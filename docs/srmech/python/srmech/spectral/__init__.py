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
- :func:`recompose` — Class L (inverse eigendecomposition via V @ coeffs)
  ∘ Class M (handle integrity check).
- :func:`similarity` — Class M (HDC similarity = 1 − 2·hamming(a,b)/D in
  [−1, 1]).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``:

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Golub & Van Loan (2013) *Matrix Computations* (4th ed.), §8.5.

Cache strategy: module-level LRU bounded ``N_MAX_EIGENBASES=8`` keyed by
``substrate_descriptor_hash`` (laplacian_kind folds into the descriptor
hash per Spike #115 design decision 2026-05-18). Eigenbasis is O(n³)
one-time per substrate; coefficients are O(n²) per state; deltas are
O(D) per step.

Spike #115 (PR #518) carries the full design spec. This module ships
entries 1/2/3/7 (``decompose`` / ``delta`` / ``recompose`` / ``similarity``);
rcN+2 ships entries 4/5/6 (``predict`` / ``prediction_error`` /
``truncate_sparse``) after Spike #113 + #117 C primitives land.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..amsc.hdc import bind as _hdc_bind
from ..amsc.hdc import similarity as _hdc_similarity
from ..amsc.laplacian import hermitian_eigendecompose

__all__ = [
    "SpectralHandle",
    "N_MAX_EIGENBASES",
    "clear_eigenbasis_cache",
    "decompose",
    "delta",
    "recompose",
    "similarity",
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
        ``V.T @ state`` projected onto eigenbasis, packed to bytes. For
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
        With ``coefficients_bytes = (V.conj().T @ state).tobytes()``.

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
    coeffs = (V.conj().T @ state_arr).astype(np.complex128)
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

    Class chain: Class L (inverse eigendecomposition ``state = V @ coeffs``)
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
    return V @ coeffs


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
