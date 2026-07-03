"""Quaternion algebra: the 4×4 left/right multiplication operators + the
hypercomplex ``exp(μθ)`` twiddle — the QDFT/ODFT foundation (0.9.0rc109;
issue #1234 Item 1a, re-raise of #863 BX-5/6/7).

WHY THIS MODULE EXISTS (F380 / the in-repo R21 proof): a Klein-4 object
(``hdc.klein4_*`` — the γ₅ & iω₇ ``Z₂×Z₂`` chirality axes) has NO shipped
transform respecting both axes; the complex ``fft`` projects to ``ℂ`` and
collapses one ``Z₂``. The exact fix is that the Klein-4 group IS the
quaternion units modulo sign — ``Q₈/{±1} ≅ Z₂×Z₂`` — so a QUATERNION FT's
coefficient algebra (``ℍ``) matches the object's value algebra. This module
ships the two foundation pieces the QDFT/ODFT cascades stand on:

1. First-class ``quaternion_left_mult`` / ``quaternion_right_mult`` — the
   4×4 real matrix representations ``L_q`` (``x → q·x``) and ``R_q``
   (``x → x·q``) — so the QDFT needn't slice the top-left 4×4 block of the
   8×8 octonion matrix (:mod:`srmech.qm.octonion`).
2. The hypercomplex twiddle ``exp(μθ) = cos θ·1 + sin θ·μ̂`` for a UNIT pure
   imaginary ``μ̂`` (the quaternion Euler formula), shaped so the QDFT twiddle
   factors ``exp(μ·2πjk/N)`` fall out naturally (:func:`quaternion_twiddle`).

FIXED CONVENTION — the SAME Cayley-Dickson doubling that fixes
:mod:`srmech.qm.octonion` (``ℝ → ℂ → ℍ → 𝕆``):

- doubling rule:  ``(a, b) * (c, d) = (a*c - conj(d)*b, d*a + b*conj(c))``
- conjugation:    ``conj((a, b)) = (conj(a), -b)``; ``conj(scalar) = scalar``

``ℍ`` is the dim-4 rung of that ladder, so by construction the quaternion
structure constants ARE the octonion table restricted to ``{e0, e1, e2, e3}``
(tested — the octonion-consistency gate), and the signed basis units close
into ``Q₈`` with ``Q₈/{±e0} ≅`` the ``hdc.klein4`` XOR table (tested — the
Klein-4 bridge gate; the R21 proof re-run against this module).

EXACTNESS CONVENTION (the three tiers, stated once for the transforms):

- **exact / arbitrary precision** — :func:`quaternion_exp_series_truncate`
  composes the Class-N calculus series (``cos_series_truncate`` /
  ``sin_series_truncate``: exact rational ``(num, den)`` pairs) for a RATIONAL
  angle ``θ = p/q`` and an exactly-representable basis axis ``μ̂ = e_axis``.
  π is NOT rational, so the exact tier never sees a literal ``2πjk/N`` — the
  caller either supplies a rational approximant of the angle (e.g. via
  ``best_rational`` over the π cascade) or crosses to the float tier below.
- **exact / fixed-width Q61** — the already-shipped
  :func:`srmech.amsc.cascade.hypercomplex_exp` (``k_axes=3`` = ℍ) is the Q61
  equal-weight-axis twiddle; this module does not duplicate it.
- **float64 boundary** — :func:`quaternion_exp` / :func:`quaternion_twiddle`
  return ``list[float]`` and the mult operators return a float64
  :class:`~srmech.amsc.mat.Mat`, the SAME boundary every ``qm.*`` op uses
  (trig via the Q61 cascade — ``rational.{cos,sin}`` / the native
  ``srmech_{cos,sin}_q61`` — projected to float ONCE; π enters as the
  Class-N ``4·atan(1)`` cascade, never ``math.pi``).

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``quaternion_mult_table`` / ``quaternion_table_attestation`` — **Class A**
  (content-addressing: the convention IS the provenance).
- ``quaternion_left_mult`` / ``quaternion_right_mult`` — **Class M**
  (Clifford / HDC binding; ``L_{e_i}``/``R_{e_i}`` are antisymmetric).
- ``quaternion_conjugate`` — **Class C** (chirality / orientation).
- ``quaternion_norm`` — **Class K + Class C** (pin-slot magnitude via
  ``srmech.amsc.cascade.magnitude``; **never** Python ``abs()``).
- ``quaternion_exp`` / ``quaternion_twiddle`` — **Class N** (Q61 cos/sin
  cascade) ∘ **Class C** (the ±μ orientation) ∘ **Class I** (the cyclic
  ``jk mod N`` twiddle index reduction).
- ``quaternion_exp_series_truncate`` — **Class N** (the exact rational
  series-truncate pair).

Same-rc C peers (everything-mirrors): ``srmech_quaternion_left_mult`` /
``srmech_quaternion_right_mult`` / ``srmech_quaternion_exp`` /
``srmech_quaternion_twiddle`` — byte-exact with the pure paths here.

Canonical SSoT: the in-repo convention is the octonion module's (Baez, J.C.
(2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205,
arXiv:math/0105155 — §1 covers ``ℍ`` and the Cayley-Dickson ladder); the
Klein-4 bridge is the in-repo R21 proof
(``docs/srmech/rbs_lm_research/R-RBS-LM-R21_klein4_is_quaternion_units_mod_sign.py``).
"""

from __future__ import annotations

import ctypes
import functools
from typing import List, Sequence, Tuple

from srmech.amsc import _native
from srmech.amsc.cascade import magnitude as _magnitude
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.amsc.mat import Mat
from srmech.amsc.rational import atan as _ratan
from srmech.amsc.rational import cos as _rcos
from srmech.amsc.rational import cos_series_truncate as _cos_series
from srmech.amsc.rational import sin as _rsin
from srmech.amsc.rational import sin_series_truncate as _sin_series
from srmech.amsc.rational import sqrt as _rsqrt
from srmech.amsc import rational as _rational

#: Quaternion dimension (the real normed division algebra ``ℍ``).
_DIM = 4

#: ctypes pointer alias for the native dim-4 marshalling (numpy-free).
_DBLP = ctypes.POINTER(ctypes.c_double)

#: The two generative rules that fix THE convention (identical to
#: qm.octonion's — ℍ is the dim-4 rung of the same Cayley-Dickson ladder).
_DOUBLING_RULE = b"(a,b)*(c,d)=(a*c - conj(d)*b, d*a + b*conj(c))"
_CONJ_RULE = b"conj((a,b))=(conj(a),-b); conj(scalar)=scalar"

#: A FIXED ISO timestamp for the self-attestation (deterministic on purpose —
#: the attestation of a GENERATED constant must not change between calls).
_RETRIEVED_AT = "2026-07-03T00:00:00Z"

#: Cascade-π at the float64 boundary — the SAME Class-N derivation the
#: laplacian module uses (``4·atan(1)`` via the Q61 atan cascade, projected
#: once at import; the ×4 is an exact power of two). NO ``math.pi``.
_PI = 4.0 * float(_ratan(1.0))

#: 1/√3 for the body-diagonal axis, via the Class-N rational sqrt cascade.
_S3 = 1.0 / float(_rsqrt(3.0))

#: Named unit pure-imaginary quaternion axes (``μ̂² = −1``). ``'ijk'`` is the
#: equal-weight body diagonal ``(i+j+k)/√3`` (the coupling axis, F436).
_MU_AXES = {
    "i": (0.0, 1.0, 0.0, 0.0),
    "j": (0.0, 0.0, 1.0, 0.0),
    "k": (0.0, 0.0, 0.0, 1.0),
    "ijk": (0.0, _S3, _S3, _S3),
}

#: The native uint32 twiddle-index bound (documented parity contract: the
#: pure path enforces the same ceiling so native == pure everywhere).
_TWIDDLE_N_MAX = 2 ** 32


@functools.lru_cache(maxsize=1)
def _build_mult_table() -> Tuple[Tuple[Tuple[int, ...], ...], ...]:
    """Generate the ``(4, 4, 4)`` int8 structure-constant tensor (cached).

    Built from the Cayley-Dickson basis cocycle ``e_i·e_j = sign·e_{i⊕j}`` via
    :func:`srmech.amsc.cascade.cd_basis_product` at ``dim=4`` — the SAME
    generative call the octonion table uses at ``dim=8``, so the quaternion
    table IS the octonion table restricted to ``{e0..e3}`` by construction
    (the octonion-consistency gate re-verifies it). Memoised as an immutable
    nested tuple; :func:`quaternion_mult_table` hands out mutable copies.
    """
    from srmech.amsc.cascade import cd_basis_product as _cd_basis_product
    table = [[[0] * _DIM for _ in range(_DIM)] for _ in range(_DIM)]
    for i in range(_DIM):
        for j in range(_DIM):
            idx, sign = _cd_basis_product(_DIM, i, j)
            table[i][j][idx] = int(sign)
    return tuple(tuple(tuple(row) for row in plane) for plane in table)


def quaternion_mult_table() -> List[List[List[int]]]:
    """The ``(4, 4, 4)`` int8 structure-constant tensor ``C`` of ``ℍ``.

    ``e_i * e_j = sum_k C[i][j][k] e_k`` under the fixed Cayley-Dickson
    convention (module docstring). ``e_0`` is the identity;
    ``e_1² = e_2² = e_3² = −e_0``; the imaginary products anticommute and
    close on ``e_1·e_2 = e_3`` (the single oriented triple — ℍ's "Fano line").
    The signed basis units form ``Q₈`` (order 8) and ``Q₈/{±e0}`` is the
    Klein-4 XOR group (the F380 bridge; index is always ``i ⊕ j``).

    Class A (content-addressing): the table is the constant
    :func:`quaternion_table_attestation` content-addresses.

    Returns:
        ``4×4×4`` nested ``list[list[list[int]]]``; ``C[i][j][k]`` is the
        ``e_k`` coefficient of ``e_i * e_j`` (entries in ``{-1, 0, +1}``).
    """
    return [[list(row) for row in plane] for plane in _build_mult_table()]


def _table_int8_bytes() -> bytes:
    """C-order int8 serialization of the (4,4,4) tensor (numpy-free).

    64 bytes, one signed two's-complement byte per entry in row-major
    (i, j, k) order (``-1 → 0xFF``, ``0 → 0x00``, ``+1 → 0x01``) — the same
    wire form the octonion attestation content-addresses at dim 8.
    """
    table = _build_mult_table()
    out = bytearray(_DIM * _DIM * _DIM)
    pos = 0
    for i in range(_DIM):
        for j in range(_DIM):
            row = table[i][j]
            for k in range(_DIM):
                out[pos] = row[k] & 0xFF  # two's-complement byte; no abs()
                pos += 1
    return bytes(out)


def quaternion_table_attestation() -> dict:
    """MPR v1 self-attestation dict for the ℍ structure-constant table.

    A self-attestation for a GENERATED constant (NOT a fetched datum): the
    convention IS the provenance, so ``response_sha256`` content-addresses
    the table's 64 int8 bytes via :func:`srmech.amsc.format.sha256_bytes`
    (Class A; no new ``hashlib.sha256``). Same shape and citation chain as
    :func:`srmech.qm.octonion.octonion_table_attestation` — ℍ needs no new
    external source (Baez (2002) §1 covers the quaternions and the ladder).

    Returns:
        A plain ``dict`` with ``mpr_version``, ``data``, ``data_schema_id``,
        ``attestation`` and ``rendering`` keys.
    """
    response_sha256 = _sha256_bytes(_table_int8_bytes())
    parser_rule_hash = _sha256_bytes(_DOUBLING_RULE + b"\n" + _CONJ_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/qm/quaternion.py::cayley_dickson_from_C"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "convention": "cayley_dickson_from_C",
            "basis_order": "e0..e3",
            "oriented_triples": [[1, 2, 3]],
            "klein4_bridge": "Q8/{+-1} ~= Z2xZ2 (index = i XOR j; F380/R21)",
        },
        "data_schema_id": "srmech://schema/quaternion_structure_constants",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — so no source_doi.
            "source_doi": None,
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.9.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/quaternion.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "Quaternion multiplication table (Cayley-Dickson from C)",
            "purpose": "Fixed sign convention for the QDFT/ODFT foundation "
                       "(Q8/{±1} ≅ Klein-4, F380)",
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155), §1"
            ),
        },
    }


def _as_quaternion(v: Sequence[float], op: str) -> List[float]:
    """Coerce ``v`` to a plain ``list[float]`` of length 4 (numpy-free).

    Accepts any 1-D sequence; a wrong-length / non-sequence input raises the
    same ``ValueError`` shape the octonion module's coercer produces.
    ``Mat`` is rejected (these ops take a vector, not a matrix)."""
    if isinstance(v, Mat):
        raise ValueError(f"{op}: q must be a 4-vector; got a Mat {v.shape}")
    try:
        out = [float(c) for c in v]
    except TypeError as exc:  # 0-D scalar / non-iterable
        raise ValueError(f"{op}: q must be a 4-vector; got {v!r}") from exc
    if len(out) != _DIM:
        raise ValueError(f"{op}: q must be a 4-vector; got length {len(out)}")
    return out


def _resolve_mu4(mu, op: str) -> List[float]:
    """Resolve ``mu`` to a UNIT pure-imaginary 4-vector ``μ̂`` (``μ̂[0] == 0``,
    ``‖μ̂‖ = 1`` ⟹ ``μ̂² = −1``) — resolved exactly ONCE per public call so the
    native and pure paths consume the identical floats (parity contract).

    Accepts a named axis ``'i'``/``'j'``/``'k'``/``'ijk'`` (exact table
    values) or a 4-sequence pure-imaginary vector, normalised via the Class-N
    :func:`srmech.amsc.rational.sqrt` cascade (never libm)."""
    if isinstance(mu, str):
        if mu in _MU_AXES:
            return list(_MU_AXES[mu])
        raise ValueError(
            f"{op}: mu must be one of {sorted(_MU_AXES)} or a unit "
            f"pure-imaginary 4-vector; got {mu!r}"
        )
    v = _as_quaternion(mu, op)
    if v[0] != 0.0:
        raise ValueError(f"{op}: a general mu must be pure-imaginary (e0 == 0)")
    norm_sq = v[1] * v[1] + v[2] * v[2] + v[3] * v[3]
    if norm_sq == 0.0:
        raise ValueError(f"{op}: mu must be a non-zero pure-imaginary vector")
    inv = 1.0 / float(_rsqrt(norm_sq))
    return [0.0, v[1] * inv, v[2] * inv, v[3] * inv]


def _native_ready(symbol: str) -> bool:
    """True iff the native lib is loaded AND exports ``symbol`` (numpy-free)."""
    return bool(
        _native.HAS_NATIVE and _native.LIB is not None
        and hasattr(_native.LIB, symbol)
    )


def _try_native_mult(symbol: str, q: List[float]) -> List[List[float]]:
    """Dispatch a dim-4 multiplication operator (``srmech_quaternion_{left,
    right}_mult``) to the C peer, returning the ``4×4`` result as a nested
    ``list`` — or ``None`` to signal the table fallback. ctypes-only (no
    numpy); the native flat output is row-major ``out[i*4 + k] = M[i][k]``."""
    if not _native_ready(symbol):
        return None
    Arr = ctypes.c_double * _DIM
    MatC = ctypes.c_double * (_DIM * _DIM)
    c_q = Arr(*(float(v) for v in q))
    c_out = MatC()
    rc = getattr(_native.LIB, symbol)(
        ctypes.cast(c_q, _DBLP), ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [[float(c_out[i * _DIM + k]) for k in range(_DIM)] for i in range(_DIM)]


def quaternion_left_mult(q: Sequence[float]) -> Mat:
    """Left-multiplication matrix ``L_q`` (``x → q·x``) as a ``4×4`` real ``Mat``.

    Column ``j`` is ``q * e_j``; ``L_q[k, j] = sum_i q_i C[i][j][k]``. For an
    imaginary unit ``e_i`` (``i ≥ 1``) the matrix ``L_{e_i}`` is antisymmetric
    (∈ so(4)). ``L`` is a HOMOMORPHISM — ``L(pq) = L(p)L(q)`` — and commutes
    with every right multiplication (``L(p)R(q) = R(q)L(p)``, the
    associativity witness ℍ has and 𝕆 lacks). The SIGN STRUCTURE of the
    basis columns is the F380 bridge: the unique nonzero of column ``j`` in
    ``L_{e_i}`` sits at row ``i ⊕ j`` (``Q₈/{±1}`` = the Klein-4 XOR table).

    Class M (Clifford / HDC binding). Dispatches to the same-rc C peer
    ``srmech_quaternion_left_mult`` (byte-exact table fallback otherwise).

    Args:
        q: A 4-vector quaternion (real components ``(q_0, q_1, q_2, q_3)``).

    Returns:
        ``4×4`` real ``Mat`` ``L_q``.

    Raises:
        ValueError: if ``q`` is not a 4-vector.
    """
    q = _as_quaternion(q, "quaternion_left_mult")
    native = _try_native_mult("srmech_quaternion_left_mult", q)
    if native is not None:
        return Mat.from_rows(native, is_complex=False)
    table = _build_mult_table()
    rows = [[sum(q[i] * table[i][j][k] for i in range(_DIM)) for j in range(_DIM)]
            for k in range(_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def quaternion_right_mult(q: Sequence[float]) -> Mat:
    """Right-multiplication matrix ``R_q`` (``x → x·q``) as a ``4×4`` real ``Mat``.

    Column ``j`` is ``e_j * q``; ``R_q[k, j] = sum_i q_i C[j][i][k]``. Right
    multiplication is an ANTI-homomorphism — ``R(pq) = R(q)R(p)`` (ℍ is
    non-commutative, so ``L_q ≠ R_q`` for a generic ``q``; the genuinely
    distinct left/right QDFT forms stand on exactly this).

    Class M (Clifford / HDC binding). Dispatches to the same-rc C peer
    ``srmech_quaternion_right_mult`` (byte-exact table fallback otherwise).

    Args:
        q: A 4-vector quaternion.

    Returns:
        ``4×4`` real ``Mat`` ``R_q``.

    Raises:
        ValueError: if ``q`` is not a 4-vector.
    """
    q = _as_quaternion(q, "quaternion_right_mult")
    native = _try_native_mult("srmech_quaternion_right_mult", q)
    if native is not None:
        return Mat.from_rows(native, is_complex=False)
    table = _build_mult_table()
    rows = [[sum(q[i] * table[j][i][k] for i in range(_DIM)) for j in range(_DIM)]
            for k in range(_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def quaternion_conjugate(x: Sequence[float]) -> List[float]:
    """Quaternion conjugate ``conj(x) = (x_0, -x_1, -x_2, -x_3)``.

    Flips the sign of the three imaginary axes (the scalar axis is fixed).
    For a UNIT twiddle it is the inverse: ``conj(exp(μθ)) = exp(−μθ)`` — the
    inverse-QDFT twiddle. Class C (chirality / orientation); a plain sign
    flip (no ``abs()``), mirroring :func:`srmech.qm.octonion.octonion_conjugate`.

    Args:
        x: A 4-vector quaternion.

    Returns:
        The 4-vector conjugate as a ``list[float]``.

    Raises:
        ValueError: if ``x`` is not a 4-vector.
    """
    x = _as_quaternion(x, "quaternion_conjugate")
    return [x[0]] + [-x[i] for i in range(1, _DIM)]


def quaternion_norm(x: Sequence[float]) -> float:
    """Quaternion norm ``sqrt(sum x_i²)`` (Class K + Class C; never ``abs()``).

    The norm form of the composition algebra (``N(x) = x·conj(x)``). The
    sum-of-squares is reduced to a scalar float, passed through the Class K
    pin-slot magnitude (:func:`srmech.amsc.cascade.magnitude` — the
    cascade-honest ``abs()`` replacement), then the Class-N
    :func:`srmech.amsc.rational.sqrt`. Mirrors
    :func:`srmech.qm.octonion.octonion_norm` at dim 4.

    Args:
        x: A 4-vector quaternion.

    Returns:
        The non-negative Euclidean norm.

    Raises:
        ValueError: if ``x`` is not a 4-vector.
    """
    x = _as_quaternion(x, "quaternion_norm")
    sum_sq = sum(xi * xi for xi in x)
    return float(_rsqrt(_magnitude(sum_sq)))


def _try_native_exp(theta: float, mu: List[float]) -> List[float]:
    """Dispatch ``exp(μθ)`` to ``srmech_quaternion_exp`` (``μ`` already unit),
    returning the 4-vector ``list[float]`` — or ``None`` for the pure path."""
    if not _native_ready("srmech_quaternion_exp"):
        return None
    Arr = ctypes.c_double * _DIM
    c_mu = Arr(*(float(v) for v in mu))
    c_out = Arr()
    rc = _native.LIB.srmech_quaternion_exp(
        ctypes.c_double(theta), ctypes.cast(c_mu, _DBLP),
        ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [float(c_out[i]) for i in range(_DIM)]


def _exp_resolved(theta: float, mu: List[float]) -> List[float]:
    """The exp core over an ALREADY-RESOLVED unit ``μ̂`` (never re-normalises —
    the one-resolution parity contract): native ``srmech_quaternion_exp`` when
    present, else the pure Q61 cascade (``rational.{cos,sin}`` projected to
    float once, then the axis scaling) — byte-exact either way."""
    native = _try_native_exp(theta, mu)
    if native is not None:
        return native
    c = float(_rcos(theta))
    s = float(_rsin(theta))
    return [c, s * mu[1], s * mu[2], s * mu[3]]


def quaternion_exp(theta: float, mu="i") -> List[float]:
    """The quaternion Euler formula ``exp(μθ) = cos θ·1 + sin θ·μ̂`` — the
    QDFT twiddle at the float64 boundary.

    ``μ̂`` is a UNIT pure imaginary (``μ̂² = −1``), so ``exp(μθ)`` is a UNIT
    quaternion living in the commutative subalgebra ``ℝ[μ̂] ≅ ℂ`` — which is
    exactly why the one-sided QDFT is invertible (the geometric-series
    orthogonality runs inside ``ℝ[μ̂]``). Properties (tested):
    ``‖exp(μθ)‖ = 1``; ``exp(μθ₁)·exp(μθ₂) = exp(μ(θ₁+θ₂))`` for the SAME
    axis; ``conj(exp(μθ)) = exp(−μθ)``; ``exp(μ·2π/N)^N = 1`` (the N-th
    roots of unity the DFT needs — see :func:`quaternion_twiddle`).

    Exactness convention (module docstring): trig is the Q61 Class-N cascade
    (``rational.{cos,sin}``; native ``srmech_{cos,sin}_q61``) projected to
    float ONCE; the exact-rational tier is
    :func:`quaternion_exp_series_truncate`; the exact-Q61 equal-weight-axis
    tier is :func:`srmech.amsc.cascade.hypercomplex_exp` (``k_axes=3``).
    Dispatches to the same-rc C peer ``srmech_quaternion_exp`` (byte-exact
    pure fallback).

    Class N (Q61 cos/sin) ∘ Class C (the ±μ orientation) ∘ Class M (the axis
    scaling); no ``abs()``, no libm.

    Args:
        theta: The rotation angle θ (radians), finite.
        mu: The axis ``μ̂`` — ``'i'``/``'j'``/``'k'``/``'ijk'`` (named, exact)
            or a pure-imaginary 4-sequence (normalised via the Class-N sqrt
            cascade). Default ``'i'``.

    Returns:
        The unit quaternion ``[cos θ, sin θ·μ̂₁, sin θ·μ̂₂, sin θ·μ̂₃]`` as a
        ``list[float]``.

    Raises:
        ValueError: non-finite ``theta``; ``mu`` not a valid axis.
    """
    th = float(theta)
    if not _rational._is_finite(th):
        raise ValueError("quaternion_exp: theta must be finite")
    mu_hat = _resolve_mu4(mu, "quaternion_exp")
    return _exp_resolved(th, mu_hat)


def quaternion_exp_series_truncate(
    theta_num: int,
    theta_den: int,
    num_terms: int,
    axis: int = 1,
) -> Tuple[Tuple[int, int], ...]:
    """EXACT-rational ``exp(e_axis·θ)`` for a RATIONAL angle ``θ = p/q`` — the
    series-truncate tier of the twiddle (the exact form of the exactness
    convention).

    Composes the Class-N calculus series
    :func:`srmech.amsc.rational.cos_series_truncate` /
    :func:`srmech.amsc.rational.sin_series_truncate` (Taylor partial sums to
    ``num_terms``, exact bignum ``(num, den)`` rationals) with an
    exactly-representable basis axis ``μ̂ = e_axis`` (``axis ∈ {1, 2, 3}`` =
    i/j/k — the only unit axes with exact rational components). Returns the
    4 exact pairs ``(cos at slot 0, ±0, sin at slot axis, ±0)``. The unit
    property ``cos² + sin² = 1`` holds in the ``num_terms → ∞`` limit (the
    truncation residue is the caller's precision dial).

    π is NOT rational — a ``2πjk/N`` twiddle angle enters this tier only as
    a caller-chosen rational approximant (e.g. ``best_rational`` over the π
    cascade digits); the float64 projection of that boundary is
    :func:`quaternion_twiddle`.

    Class N (rational series-truncate). Pure exact-bignum (the
    ``bignum_reference`` tier — the arbitrary-precision oracle of the Q61 /
    float paths).

    Args:
        theta_num: Angle numerator ``p`` (radians as ``p/q``).
        theta_den: Angle denominator ``q`` (nonzero).
        num_terms: Taylor terms ``N`` (see the series-truncate contracts).
        axis: The basis axis ``e_axis``, 1 (i), 2 (j) or 3 (k). Default 1.

    Returns:
        A 4-tuple of exact ``(num, den)`` pairs: slot 0 = truncated cos,
        slot ``axis`` = truncated sin, the other two slots ``(0, 1)``.

    Raises:
        ValueError: ``axis`` not in {1, 2, 3}; series-contract violations
            propagate from the underlying truncates.
    """
    if axis not in (1, 2, 3):
        raise ValueError(
            f"quaternion_exp_series_truncate: axis must be 1 (i), 2 (j) or "
            f"3 (k); got {axis!r}"
        )
    c_pair = _cos_series(theta_num, theta_den, num_terms)
    s_pair = _sin_series(theta_num, theta_den, num_terms)
    out: List[Tuple[int, int]] = [tuple(c_pair), (0, 1), (0, 1), (0, 1)]
    out[axis] = tuple(s_pair)
    return tuple(out)


def _try_native_twiddle(j: int, k: int, n_points: int, sigma: int,
                        mu: List[float]) -> List[float]:
    """Dispatch the whole twiddle to ``srmech_quaternion_twiddle`` (``μ``
    already unit; ``j``/``k`` already reduced mod ``n_points``) — or ``None``
    to signal the pure mirror."""
    if not _native_ready("srmech_quaternion_twiddle"):
        return None
    Arr = ctypes.c_double * _DIM
    c_mu = Arr(*(float(v) for v in mu))
    c_out = Arr()
    rc = _native.LIB.srmech_quaternion_twiddle(
        ctypes.c_uint32(j), ctypes.c_uint32(k), ctypes.c_uint32(n_points),
        ctypes.c_int32(sigma), ctypes.cast(c_mu, _DBLP),
        ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [float(c_out[i]) for i in range(_DIM)]


def _twiddle_resolved(j_red: int, k_red: int, n_points: int, sigma: int,
                      mu_hat: List[float]) -> List[float]:
    """The twiddle core over an ALREADY-RESOLVED unit ``μ̂`` and ALREADY-REDUCED
    indices (``j_red``/``k_red`` < ``n_points``) — never re-normalises μ̂ (the
    one-resolution parity contract). Shared by :func:`quaternion_twiddle` and
    the rc110 ``cascade.quaternion_dft`` composed path so both consume the
    identical floats the C peers see. Native ``srmech_quaternion_twiddle`` when
    present; the pure mirror follows the C float-op order exactly."""
    native = _try_native_twiddle(j_red, k_red, n_points, sigma, mu_hat)
    if native is not None:
        return native
    # Pure mirror of the C peer — identical float-op order (parity contract).
    r = (j_red * k_red) % n_points
    two_pi = 2.0 * _PI
    frac = float(r) / float(n_points)
    theta = float(sigma) * two_pi * frac
    return _exp_resolved(theta, mu_hat)


def quaternion_twiddle(j: int, k: int, n_points: int, *,
                       mu="i", sigma: int = -1) -> List[float]:
    """The QDFT twiddle factor ``exp(σ·μ·2πjk/N)`` — the DFT-facing form of
    :func:`quaternion_exp`, with π and the index reduction handled natively.

    The angle is ``σ·2π·((j·k) mod N)/N``: the index product is reduced in
    the cyclic group Z_N FIRST (Class I — exact, and the reduction keeps the
    projected angle in one period), then π enters ONCE as the Class-N
    ``4·atan(1)`` cascade at the float64 boundary (never ``math.pi``).
    ``σ = −1`` (default) is the forward-DFT orientation (matching
    ``cascade.quaternion_dft``); ``σ = +1`` the inverse. Twiddle closure
    (tested): ``quaternion_twiddle(j, k, N)`` for ``jk ≡ 0 (mod N)`` is the
    identity, and ``exp(μ·2π/N)^N = 1``.

    Dispatches to the same-rc C peer ``srmech_quaternion_twiddle`` (byte-exact
    pure mirror otherwise). Class I (cyclic index) ∘ N (π cascade + Q61
    trig) ∘ C (σ orientation) ∘ M (axis scaling).

    Args:
        j: Frequency index (non-negative int).
        k: Sample index (non-negative int).
        n_points: The DFT length ``N`` (``1 ≤ N < 2³²`` — the native uint32
            parity bound, enforced identically on the pure path).
        mu: The axis ``μ̂`` (same forms as :func:`quaternion_exp`). Default ``'i'``.
        sigma: ``−1`` forward (default) or ``+1`` inverse.

    Returns:
        The unit-quaternion twiddle as a ``list[float]`` (4 components).

    Raises:
        ValueError: bad ``j``/``k``/``n_points``/``sigma``/``mu``.
    """
    j = int(j)
    k = int(k)
    n_points = int(n_points)
    if j < 0 or k < 0:
        raise ValueError(
            f"quaternion_twiddle: j and k must be non-negative; got {j}, {k}")
    if not (1 <= n_points < _TWIDDLE_N_MAX):
        raise ValueError(
            f"quaternion_twiddle: n_points must be in [1, 2**32); got {n_points}")
    if sigma not in (1, -1):
        raise ValueError(
            f"quaternion_twiddle: sigma must be +1 or -1; got {sigma!r}")
    mu_hat = _resolve_mu4(mu, "quaternion_twiddle")
    j_red = j % n_points
    k_red = k % n_points
    return _twiddle_resolved(j_red, k_red, n_points, sigma, mu_hat)


__all__ = [
    "quaternion_conjugate",
    "quaternion_exp",
    "quaternion_exp_series_truncate",
    "quaternion_left_mult",
    "quaternion_mult_table",
    "quaternion_norm",
    "quaternion_right_mult",
    "quaternion_table_attestation",
    "quaternion_twiddle",
]
