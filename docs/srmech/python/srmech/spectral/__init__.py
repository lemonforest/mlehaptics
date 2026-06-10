"""Runtime spectral decomposition + delta-encoding (rcN+1 = v0.4.1rc14).

Composition layer above ``srmech.amsc.{laplacian, hdc, format}``. Provides
the runtime/tool-schema-callable spectral-decomposition + delta-encoding
surface for substrates that already have Laplacian + HDC primitives in
the AMSC layer.

This module **does not** introduce a new primitive class — every operation
is class-operator composition over the existing 14-class A–N vocabulary
per ``[[feedback_no_privileged_primitive_classes]]``:

- :func:`decompose` — Class L (Hermitian Laplacian eigendecomposition)
  ∘ Class A (SHA-256 content addressing for cache + handle integrity).
- :func:`delta` — Class M (HDC bind / XOR self-inverse) per Spike #114
  Option B (direct bind on already-encoded coefficient bytes; 1.22× faster
  than wrapper variant).
- :func:`recompose` — Class L (inverse eigendecomposition via V·coeffs)
  ∘ Class M (handle integrity check).
- :func:`similarity` — Class M (HDC similarity = 1 − 2·hamming(a,b)/D in
  [−1, 1]).
- :func:`predict` — Class C (cascade-extrapolate via spectral phase
  evolution on the eigenbasis) ∘ Class L (Hermitian Laplacian
  eigenstructure). One-step or n-step substrate-natural evolution per
  Spike #113 anchor + MS #14 rcN+2 ship.
- :func:`prediction_error` — Class M (XOR delta between predicted and
  observed encoded coefficients) ∘ Class K (gate-by-threshold projection
  on the resulting popcount-density). ``threshold=0.0`` default per user
  decision 2026-05-18 (return raw delta when no gating requested).
- :func:`truncate_sparse` — Class K (magnitude-band sparse-truncate on
  spectral coefficients; keep top-k modes by |coefficient|, zero the
  rest) per Spike #117 anchor + MS #14 rcN+2 ship.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``:

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Golub & Van Loan (2013) *Matrix Computations* (4th ed.), §8.5.
- Mallat (2008) *A Wavelet Tour of Signal Processing* (3rd ed.), §9.2
  (best k-term approximation / sparse-truncate).
- Kay (1993) *Fundamentals of Statistical Signal Processing: Estimation
  Theory*, §11 (prediction-error formulation).

Cache strategy: module-level LRU bounded ``N_MAX_EIGENBASES=8`` keyed by
``substrate_descriptor_hash`` (laplacian_kind folds into the descriptor
hash per Spike #115 design decision 2026-05-18). Eigenbasis is O(n³)
one-time per substrate; coefficients are O(n²) per state; deltas are
O(D) per step.

Spike #115 (PR #518) carries the full design spec for entries 1/2/3/7
(``decompose`` / ``delta`` / ``recompose`` / ``similarity``); MS #14
rcN+2 (v0.4.2rc4) ships entries 4/5/6 (``predict`` / ``prediction_error``
/ ``truncate_sparse``) per user direction 2026-05-19. The three new
operations are class-composition over the existing 14-class A–N
vocabulary per ``[[feedback_no_privileged_primitive_classes]]``; no new
primitive class is introduced.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

import numpy as np

from srmech.amsc.laplacian import elementwise_hypot, elementwise_transcendental

from ..amsc.hdc import bind as _hdc_bind
from ..amsc.hdc import similarity as _hdc_similarity
from ..amsc.laplacian import dense_matvec_complex, hermitian_eigendecompose

__all__ = [
    "SpectralHandle",
    "N_MAX_EIGENBASES",
    "clear_eigenbasis_cache",
    "decompose",
    "delta",
    "recompose",
    "similarity",
    "predict",
    "prediction_error",
    "truncate_sparse",
]


N_MAX_EIGENBASES: int = 8
"""Maximum number of eigenbases kept in the module-level LRU cache.

Per Spike #115 design: bounded LRU; persistent on-disk cache deferred.
"""


@dataclass(frozen=True)
class SpectralHandle:
    """Opaque handle pairing substrate descriptor with encoded coefficients.

    Per Spike #115 design (PR #518) + user decision 2026-05-18 (laplacian
    kind folds into substrate descriptor hash):

    Attributes
    ----------
    substrate_descriptor_hash:
        SHA-256 hex of the substrate descriptor (Laplacian topology +
        encoder identity + any hyperparameters). Eigenbasis cache key.
    coefficients_bytes:
        Per-state encoded coefficients. For numeric substrates: typically
        ``V.T·state`` projected onto eigenbasis, packed to bytes. For
        binary HDC substrates: BSC vector bytes directly.
    content_sha:
        SHA-256 hex of ``coefficients_bytes``; integrity check on
        :func:`recompose` and substrate-match check on :func:`delta`.
    n_modes:
        Number of eigenbasis modes (``len(eigvals)``). For raw-HDC
        substrates with no spectral projection, set to ``len(bytes) * 8``
        as the BSC bit-dimension D.
    """

    substrate_descriptor_hash: str
    coefficients_bytes: bytes
    content_sha: str
    n_modes: int


# Module-level LRU cache. Keyed by substrate_descriptor_hash; value is
# (eigvals, V) tuple. Bounded to N_MAX_EIGENBASES entries; oldest evicted.
_EIGENBASIS_CACHE: "OrderedDict[str, tuple]" = OrderedDict()


def clear_eigenbasis_cache() -> None:
    """Drop all cached eigenbases. Test isolation utility."""
    _EIGENBASIS_CACHE.clear()


def _cache_eigenbasis(
    descriptor_hash: str, eigvals: np.ndarray, V: np.ndarray
) -> None:
    """Insert ``(eigvals, V)`` for ``descriptor_hash`` into the LRU cache."""
    if descriptor_hash in _EIGENBASIS_CACHE:
        _EIGENBASIS_CACHE.move_to_end(descriptor_hash)
    _EIGENBASIS_CACHE[descriptor_hash] = (eigvals, V)
    while len(_EIGENBASIS_CACHE) > N_MAX_EIGENBASES:
        _EIGENBASIS_CACHE.popitem(last=False)


def _get_cached_eigenbasis(
    descriptor_hash: str,
) -> Optional[tuple]:
    """Return ``(eigvals, V)`` for ``descriptor_hash`` if cached, else None."""
    if descriptor_hash in _EIGENBASIS_CACHE:
        _EIGENBASIS_CACHE.move_to_end(descriptor_hash)
        return _EIGENBASIS_CACHE[descriptor_hash]
    return None


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _descriptor_hash(
    laplacian: np.ndarray, encoder_tag: str = "default"
) -> str:
    """SHA-256 of canonicalised substrate descriptor.

    Per Spike #115 design decision (2026-05-18 user choice): laplacian_kind
    folds into the substrate_descriptor_hash; not a separate cache-key.
    Canonical bytes = laplacian.tobytes() + b"|" + encoder_tag.encode().
    """
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(laplacian, dtype=np.complex128).tobytes())
    h.update(b"|")
    h.update(encoder_tag.encode("utf-8"))
    return h.hexdigest()


def decompose(
    state: np.ndarray,
    laplacian: np.ndarray,
    *,
    encoder_tag: str = "default",
) -> SpectralHandle:
    """Project ``state`` onto eigenbasis of ``laplacian``; return handle.

    Class chain: L (Hermitian eigendecomposition) ∘ A (SHA-256 content
    addressing). No new primitive class.

    Parameters
    ----------
    state:
        ``(n,)`` array of substrate-state coefficients in the node-domain
        basis. Real or complex; cast to complex128 internally.
    laplacian:
        ``(n, n)`` Hermitian substrate Laplacian. Eigendecomposition is
        cached by ``descriptor_hash(laplacian, encoder_tag)`` per
        :data:`N_MAX_EIGENBASES`.
    encoder_tag:
        Tag distinguishing different encoders over the same Laplacian
        (e.g., ``"raw"`` vs ``"quantized"``); folds into descriptor hash.

    Returns
    -------
    SpectralHandle
        With ``coefficients_bytes = (V.conj().T·state).tobytes()``.

    Raises
    ------
    ValueError
        If shapes mismatch or laplacian is not square.
    """
    state_arr = np.ascontiguousarray(state, dtype=np.complex128)
    if state_arr.ndim != 1:
        raise ValueError(f"state must be 1-D; got shape {state_arr.shape}")
    L_arr = np.ascontiguousarray(laplacian, dtype=np.complex128)
    if L_arr.ndim != 2 or L_arr.shape[0] != L_arr.shape[1]:
        raise ValueError(f"laplacian must be square 2-D; got {L_arr.shape}")
    n = L_arr.shape[0]
    if state_arr.shape[0] != n:
        raise ValueError(
            f"state length {state_arr.shape[0]} != laplacian size {n}"
        )
    desc_hash = _descriptor_hash(L_arr, encoder_tag=encoder_tag)
    cached = _get_cached_eigenbasis(desc_hash)
    if cached is None:
        eigvals, V = hermitian_eigendecompose(L_arr)
        _cache_eigenbasis(desc_hash, eigvals, V)
    else:
        eigvals, V = cached
    coeffs = dense_matvec_complex(V.conj().T, state_arr)
    coeffs_bytes = coeffs.tobytes()
    return SpectralHandle(
        substrate_descriptor_hash=desc_hash,
        coefficients_bytes=coeffs_bytes,
        content_sha=_sha256_hex(coeffs_bytes),
        n_modes=int(n),
    )


def delta(ref: SpectralHandle | bytes, current: SpectralHandle | bytes) -> bytes:
    """Bit-exact XOR delta of two coefficient byte vectors.

    Class chain: Class M (HDC bind / XOR self-inverse) per Spike #114
    Option B (direct on encoded coefficient bytes; 1.22× faster than the
    Option-A encoder-handling wrapper).

    Identity guarantees per Plate 1995 / Kanerva 2009 BSC algebra:
    ``delta(ref, current) = bind(ref, current)``;
    ``bind(ref, delta) = current`` (recovery via second bind);
    ``bind(delta, current) = ref`` (commutativity);
    ``bind(a, bind(a, b)) = b`` (self-inverse).

    Parameters
    ----------
    ref, current:
        Either ``SpectralHandle`` (uses ``.coefficients_bytes``) or raw
        ``bytes``. Lengths must match.

    Returns
    -------
    bytes
        XOR delta; same length as inputs.

    Raises
    ------
    ValueError
        If inputs are different lengths, or if both are SpectralHandle
        with mismatched ``substrate_descriptor_hash``.
    """
    ref_bytes = ref.coefficients_bytes if isinstance(ref, SpectralHandle) else ref
    cur_bytes = (
        current.coefficients_bytes if isinstance(current, SpectralHandle) else current
    )
    if (
        isinstance(ref, SpectralHandle)
        and isinstance(current, SpectralHandle)
        and ref.substrate_descriptor_hash != current.substrate_descriptor_hash
    ):
        raise ValueError(
            "spectral.delta: substrate_descriptor_hash mismatch between handles"
        )
    return _hdc_bind(ref_bytes, cur_bytes)


def recompose(
    handle: SpectralHandle, laplacian: np.ndarray, *, encoder_tag: str = "default"
) -> np.ndarray:
    """Reconstruct node-domain state from ``handle`` via inverse projection.

    Class chain: Class L (inverse eigendecomposition ``state = V·coeffs``)
    ∘ Class M (SHA-256 content integrity check on handle).

    Parameters
    ----------
    handle:
        ``SpectralHandle`` produced by :func:`decompose` on the same
        Laplacian + encoder_tag.
    laplacian:
        Same Laplacian used to produce ``handle``. Cached eigenbasis is
        reused via descriptor-hash match.
    encoder_tag:
        Same encoder tag as used in :func:`decompose`.

    Returns
    -------
    np.ndarray
        ``(n_modes,)`` complex128 array; real states have negligible
        imaginary part by Hermitian eigenbasis algebra.

    Raises
    ------
    ValueError
        If handle's content_sha doesn't match its coefficients_bytes
        (corruption) or if descriptor_hash doesn't match the supplied
        laplacian.
    """
    if _sha256_hex(handle.coefficients_bytes) != handle.content_sha:
        raise ValueError(
            "spectral.recompose: handle content_sha mismatch (corruption?)"
        )
    L_arr = np.ascontiguousarray(laplacian, dtype=np.complex128)
    desc_hash = _descriptor_hash(L_arr, encoder_tag=encoder_tag)
    if desc_hash != handle.substrate_descriptor_hash:
        raise ValueError(
            "spectral.recompose: laplacian descriptor_hash mismatch with handle"
        )
    cached = _get_cached_eigenbasis(desc_hash)
    if cached is None:
        eigvals, V = hermitian_eigendecompose(L_arr)
        _cache_eigenbasis(desc_hash, eigvals, V)
    else:
        eigvals, V = cached
    n = handle.n_modes
    coeffs = np.frombuffer(handle.coefficients_bytes, dtype=np.complex128).reshape(n)
    return dense_matvec_complex(V, coeffs)


def similarity(
    a: SpectralHandle | bytes, b: SpectralHandle | bytes
) -> float:
    """HDC similarity ``1 − 2·hamming(a, b) / D`` in ``[−1, 1]``.

    Class chain: Class M (HDC similarity per Kanerva 2009 §3.2). Direct on
    coefficient bytes per Spike #115 design / Spike #114 Option B.

    Parameters
    ----------
    a, b:
        Either ``SpectralHandle`` (uses ``.coefficients_bytes``) or raw
        ``bytes``. Lengths must match.

    Returns
    -------
    float
        Similarity in ``[−1, +1]``; +1 = identical, 0 = orthogonal,
        −1 = anti-correlated.

    Raises
    ------
    ValueError
        If inputs have different byte-lengths.
    """
    a_bytes = a.coefficients_bytes if isinstance(a, SpectralHandle) else a
    b_bytes = b.coefficients_bytes if isinstance(b, SpectralHandle) else b
    return _hdc_similarity(a_bytes, b_bytes)


# ---------------------------------------------------------------------------
# MS #14 rcN+2 (v0.4.2rc4) — predict / prediction_error / truncate_sparse
# ---------------------------------------------------------------------------
# These three runtime operations close out Spike #113 (predictive-coding
# cascade Class C ∘ L) + Spike #117 (Class K sparse-truncate / gate-by-
# threshold) per user direction 2026-05-19. They compose over the existing
# 14-class A-N primitive vocabulary; no new primitive class is introduced
# per [[feedback_no_privileged_primitive_classes]].
# ---------------------------------------------------------------------------


def predict(
    handle: SpectralHandle,
    laplacian: np.ndarray,
    *,
    steps: int = 1,
    dt: float = 1.0,
    encoder_tag: str = "default",
) -> SpectralHandle:
    """Cascade-extrapolate ``handle`` ``steps`` forward in spectral time.

    Class chain: Class C (cascade-extrapolate via per-mode complex-phase
    evolution ``exp(-i·λ_k·steps·dt)`` on the eigenbasis coefficients)
    ∘ Class L (Hermitian Laplacian eigenstructure providing λ_k).

    The mathematical statement: a substrate state encoded onto the
    Laplacian eigenbasis evolves under the natural cyclic-rotation per
    eigenmode at angular rate ``λ_k``; the predicted coefficients after
    ``steps · dt`` "ticks" are ``coeffs_pred[k] = coeffs[k] · exp(-i·λ_k·
    steps · dt)``. This is the closed-form one-shot of a recurrent
    spectral predictor and matches the Spike #113 anchor for
    predictive-coding cascades on attested substrates.

    Parameters
    ----------
    handle:
        ``SpectralHandle`` from :func:`decompose` over the same Laplacian.
    laplacian:
        Hermitian Laplacian; the eigenbasis (already cached by hash) is
        re-used for the phase rotation.
    steps:
        Integer number of substrate-natural ticks forward. Default ``1``.
    dt:
        Time-step magnitude per tick (substrate-natural units). Default
        ``1.0``.
    encoder_tag:
        Same encoder tag as used in :func:`decompose`.

    Returns
    -------
    SpectralHandle
        Predicted-state handle. Same ``substrate_descriptor_hash`` and
        ``n_modes`` as the input; new ``coefficients_bytes`` /
        ``content_sha`` reflect the phase-evolved coefficients.

    Raises
    ------
    ValueError
        If ``handle.content_sha`` doesn't match its coefficients
        (corruption) or the Laplacian descriptor doesn't match the
        handle.
    """
    if _sha256_hex(handle.coefficients_bytes) != handle.content_sha:
        raise ValueError(
            "spectral.predict: handle content_sha mismatch (corruption?)"
        )
    L_arr = np.ascontiguousarray(laplacian, dtype=np.complex128)
    desc_hash = _descriptor_hash(L_arr, encoder_tag=encoder_tag)
    if desc_hash != handle.substrate_descriptor_hash:
        raise ValueError(
            "spectral.predict: laplacian descriptor_hash mismatch with handle"
        )
    cached = _get_cached_eigenbasis(desc_hash)
    if cached is None:
        eigvals, V = hermitian_eigendecompose(L_arr)
        _cache_eigenbasis(desc_hash, eigvals, V)
    else:
        eigvals, V = cached
    n = handle.n_modes
    coeffs = np.frombuffer(
        handle.coefficients_bytes, dtype=np.complex128
    ).reshape(n)
    # Class C cascade-extrapolate: per-mode phase evolution.
    phase = elementwise_transcendental(
        -(np.asarray(eigvals, dtype=np.float64) * steps * dt), "exp_i")
    coeffs_pred = (coeffs * phase).astype(np.complex128)
    coeffs_bytes = coeffs_pred.tobytes()
    return SpectralHandle(
        substrate_descriptor_hash=desc_hash,
        coefficients_bytes=coeffs_bytes,
        content_sha=_sha256_hex(coeffs_bytes),
        n_modes=int(n),
    )


def prediction_error(
    predicted: SpectralHandle | bytes,
    observed: SpectralHandle | bytes,
    *,
    threshold: float = 0.0,
) -> bytes:
    """XOR delta between predicted and observed; gate-by-threshold.

    Class chain: Class M (HDC bind / XOR self-inverse delta on encoded
    coefficient bytes) ∘ Class K (gate-by-threshold projection: when the
    delta's normalised popcount-density exceeds ``threshold``, the full
    delta is returned; otherwise an all-zero byte sequence of the same
    length is returned, signalling "below-threshold; prediction
    sufficient").

    Identity guarantees (inherited from :func:`delta`):
    ``prediction_error(p, o, threshold=0.0) == delta(p, o)``;
    when ``threshold > 0`` the gating step can suppress small-magnitude
    errors. ``threshold=0.0`` is the default per user decision 2026-05-18
    (return raw XOR delta when no gating requested).

    Parameters
    ----------
    predicted, observed:
        Either ``SpectralHandle`` (uses ``.coefficients_bytes``) or raw
        ``bytes``. Lengths must match. If both are SpectralHandles their
        substrate descriptor hashes must agree.
    threshold:
        Class K gate threshold in ``[0.0, 1.0]``. Interpreted as a
        popcount-density floor: when ``popcount(xor_delta) / (8·len)``
        is at or below this threshold, the returned delta is zeroed.
        Default ``0.0`` (no gating; raw XOR delta).

    Returns
    -------
    bytes
        XOR prediction-error delta; same byte length as the inputs.
        All-zero when the delta is below the gating threshold.

    Raises
    ------
    ValueError
        If inputs are different lengths, both handles disagree on
        substrate_descriptor_hash, or ``threshold`` is outside
        ``[0.0, 1.0]``.
    """
    if not (0.0 <= float(threshold) <= 1.0):
        raise ValueError(
            "spectral.prediction_error: threshold must be in [0.0, 1.0]; "
            f"got {threshold!r}"
        )
    # Class M side: reuse the XOR-bind delta with substrate-hash guard.
    raw_delta = delta(predicted, observed)
    if threshold == 0.0:
        return raw_delta
    # Class K side: gate-by-threshold on popcount density.
    total_bits = len(raw_delta) * 8
    if total_bits == 0:
        return raw_delta
    density = sum(bin(byte).count("1") for byte in raw_delta) / total_bits
    if density <= threshold:
        return b"\x00" * len(raw_delta)
    return raw_delta


def truncate_sparse(
    handle: SpectralHandle,
    *,
    keep_k: Optional[int] = None,
    threshold: Optional[float] = None,
) -> SpectralHandle:
    """Sparse-truncate ``handle``'s coefficients; keep only the top modes.

    Class chain: Class K (magnitude-band sparse-truncate / threshold-gate
    on spectral coefficients). The operation keeps either the top
    ``keep_k`` modes by ``|coeff|`` (zeros the rest), or every mode whose
    ``|coeff|`` is at or above ``threshold``, depending on which keyword
    is supplied. Anchored on Spike #117 (Class K compression by β
    band-membership; "best k-term approximation" per Mallat (2008) §9.2).

    Parameters
    ----------
    handle:
        ``SpectralHandle`` from :func:`decompose`.
    keep_k:
        Number of highest-magnitude modes to keep (``0 ≤ keep_k ≤
        n_modes``). Exactly one of ``keep_k`` or ``threshold`` must be
        provided.
    threshold:
        Magnitude floor; modes with ``|coeff| >= threshold`` are kept.
        Exactly one of ``keep_k`` or ``threshold`` must be provided.

    Returns
    -------
    SpectralHandle
        Truncated handle. Same ``substrate_descriptor_hash`` and
        ``n_modes`` as input; new ``coefficients_bytes`` /
        ``content_sha`` reflect the zeroed-out coefficients.

    Raises
    ------
    ValueError
        If neither or both of ``keep_k`` / ``threshold`` are supplied, if
        ``keep_k`` is negative or exceeds ``handle.n_modes``, if
        ``threshold`` is negative, or if the handle's ``content_sha``
        doesn't match its coefficients (corruption).
    """
    if (keep_k is None) == (threshold is None):
        raise ValueError(
            "spectral.truncate_sparse: exactly one of keep_k or threshold "
            "must be provided"
        )
    if _sha256_hex(handle.coefficients_bytes) != handle.content_sha:
        raise ValueError(
            "spectral.truncate_sparse: handle content_sha mismatch (corruption?)"
        )
    n = handle.n_modes
    coeffs = np.frombuffer(
        handle.coefficients_bytes, dtype=np.complex128
    ).reshape(n).copy()
    # |z| = hypot(real, imag) (no abs()); coeffs are complex spectral coefficients.
    magnitudes = elementwise_hypot(coeffs.real, coeffs.imag)
    if keep_k is not None:
        k = int(keep_k)
        if k < 0 or k > n:
            raise ValueError(
                "spectral.truncate_sparse: keep_k must be in [0, n_modes]; "
                f"got keep_k={k}, n_modes={n}"
            )
        if k == 0:
            coeffs[:] = 0
        elif k < n:
            # argpartition keeps top-k by magnitude; zero everything else.
            # Stable secondary sort by index for determinism on ties.
            order = np.argsort(-magnitudes, kind="stable")
            keep_indices = set(int(i) for i in order[:k])
            for i in range(n):
                if i not in keep_indices:
                    coeffs[i] = 0
        # k == n: keep all; no zeroing
    else:
        thr = float(threshold)  # type: ignore[arg-type]
        if thr < 0.0:
            raise ValueError(
                "spectral.truncate_sparse: threshold must be >= 0.0; "
                f"got {thr!r}"
            )
        mask = magnitudes < thr
        coeffs[mask] = 0
    coeffs_bytes = coeffs.astype(np.complex128).tobytes()
    return SpectralHandle(
        substrate_descriptor_hash=handle.substrate_descriptor_hash,
        coefficients_bytes=coeffs_bytes,
        content_sha=_sha256_hex(coeffs_bytes),
        n_modes=int(n),
    )
