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
   8×8 octonion matrix (:mod:`srmech.physics.qm.octonion`).
2. The hypercomplex twiddle ``exp(μθ) = cos θ·1 + sin θ·μ̂`` for a UNIT pure
   imaginary ``μ̂`` (the quaternion Euler formula), shaped so the QDFT twiddle
   factors ``exp(μ·2πjk/N)`` fall out naturally (:func:`quaternion_twiddle`).

FIXED CONVENTION — the SAME Cayley-Dickson doubling that fixes
:mod:`srmech.physics.qm.octonion` (``ℝ → ℂ → ℍ → 𝕆``):

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
  :func:`srmech.cascade.hypercomplex_exp` (``k_axes=3`` = ℍ) is the Q61
  equal-weight-axis twiddle; this module does not duplicate it.
- **float64 boundary** — :func:`quaternion_exp` / :func:`quaternion_twiddle`
  return ``list[float]`` and the mult operators return a float64
  :class:`~srmech.math.mat.Mat`, the SAME boundary every ``qm.*`` op uses
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
  ``srmech.cascade.magnitude``; **never** Python ``abs()``).
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

from srmech import _native
from srmech.cascade import cd_conjugate as _cd_conjugate
from srmech.cascade import cd_norm_sq as _cd_norm_sq
from srmech.cascade import left_mult_matrix as _left_mult_matrix
from srmech.cascade import magnitude as _magnitude
from srmech.cascade import right_mult_matrix as _right_mult_matrix
# rc465 (`#T1188`): the exact-operand ADMISSION predicate is IMPORTED from its
# single definition (rc463 wrote it for einsum). Only the dim-4 ARITY wrapper is
# local — the same shape `qm.octonion` carries at dim 8. Sharing the judgement
# and keeping the arity local is deliberate: this module must not acquire a
# dependency on the rung ABOVE it just to read its own operand.
from srmech.math.q import exact_vector as _exact_vector  # rc466 (`#T1188`): the ONE exact reader
from srmech.math.q import exact_scalar as _exact_scalar  # rc466: quaternion_log's exact route
from srmech.math.q import Q  # rc465: the exact-ℚ scalar carrier
from srmech.math.qmat import QMat  # rc465: the exact-ℚ 4×4 L_q / R_q carrier
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.math.mat import Mat
from srmech.math.rational import atan as _ratan
from srmech.math.rational import atan2 as _ratan2
from srmech.math.rational import cos as _rcos
from srmech.math.rational import cos_series_truncate as _cos_series
from srmech.math.rational import sin as _rsin
from srmech.math.rational import sin_series_truncate as _sin_series
from srmech.math.rational import sqrt as _rsqrt
from srmech.math import rational as _rational

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
    :func:`srmech.cascade.cd_basis_product` at ``dim=4`` — the SAME
    generative call the octonion table uses at ``dim=8``, so the quaternion
    table IS the octonion table restricted to ``{e0..e3}`` by construction
    (the octonion-consistency gate re-verifies it). Memoised as an immutable
    nested tuple; :func:`quaternion_mult_table` hands out mutable copies.
    """
    from srmech.cascade import cd_basis_product as _cd_basis_product
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
    """C-order int8 serialization of the (4,4,4) tensor.

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
    :func:`srmech.physics.qm.octonion.octonion_table_attestation` — ℍ needs no new
    external source (Baez (2002) §1 covers the quaternions and the ladder).

    Returns:
        A plain ``dict`` with ``mpr_version``, ``data``, ``data_schema_id``,
        ``attestation`` and ``rendering`` keys.
    """
    response_sha256 = _sha256_bytes(_table_int8_bytes())
    parser_rule_hash = _sha256_bytes(_DOUBLING_RULE + b"\n" + _CONJ_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/physics/qm/quaternion.py::cayley_dickson_from_C"
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
            "collector_descriptor_path": "srmech/physics/qm/quaternion.py",
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
    """Coerce ``v`` to a plain ``list[float]`` of length 4.

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


def _operand_leaves(v, op: str):
    """Materialise a 1-D operand ONCE so the exactness read cannot consume it,
    and REFUSE a ``Mat`` here.

    ⚠️ **A pass-through IS an admission** (rc465-fix, `#T1188`). As first
    shipped this returned a ``Mat`` untouched and left the rejection to
    :func:`_as_quaternion`; the behaviour was identical, but
    ``tests/coercion_boundary.py`` reads an ``isinstance`` guard whose body
    does not raise as an ACCEPTANCE, so the four ℍ ops (and, transitively
    through :func:`quaternion_conjugate`, :func:`quaternion_slerp`) measured as
    accepting ``Mat`` while declaring only ``HV``. See the octonion peer
    :func:`srmech.physics.qm.octonion._operand_leaves` for the full account.

    :func:`_as_quaternion` KEEPS its own ``Mat`` refusal: it is still called
    directly by :func:`quaternion_log`, :func:`quaternion_slerp` and
    :func:`quaternion_cycle_holonomy`, which do not pass through here, so that
    guard is live rather than dead.
    """
    if isinstance(v, Mat):
        raise ValueError(f"{op}: q must be a 4-vector; got a Mat {v.shape}")
    try:
        return list(v)
    except TypeError:
        return v


def _exact_quaternion(v):
    """The EXACT-ℚ reading of a 4-vector operand as ``list[Q]``, or ``None`` —
    the dim-4 call of :func:`srmech.math.q.exact_vector`, the ONE reader every
    carrier-admission site imports since rc466 (`#T1188`; rc465 wrote a copy of
    it here and a second in :mod:`srmech.physics.qm.octonion`). ONE float
    component anywhere returns ``None`` (whole-operand admission: the call takes
    the float route entire); a wrong-length operand returns ``None`` too, so
    :func:`_as_quaternion`'s ``ValueError`` fires on EITHER carrier.
    """
    return _exact_vector(v, n=_DIM)


def _resolve_mu4(mu, op: str) -> List[float]:
    """Resolve ``mu`` to a UNIT pure-imaginary 4-vector ``μ̂`` (``μ̂[0] == 0``,
    ``‖μ̂‖ = 1`` ⟹ ``μ̂² = −1``) — resolved exactly ONCE per public call so the
    native and pure paths consume the identical floats (parity contract).

    Accepts a named axis ``'i'``/``'j'``/``'k'``/``'ijk'`` (exact table
    values) or a 4-sequence pure-imaginary vector, normalised via the Class-N
    :func:`srmech.math.rational.sqrt` cascade (never libm)."""
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
    """True iff the native lib is loaded AND exports ``symbol``."""
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


def quaternion_left_mult(q: Sequence[int | Q | Tuple[int, int] | float]) -> Mat | QMat:
    """Left-multiplication matrix ``L_q`` (``x → q·x``) as a ``4×4`` real ``Mat``.

    Column ``j`` is ``q * e_j``; ``L_q[k, j] = sum_i q_i C[i][j][k]``. For an
    imaginary unit ``e_i`` (``i ≥ 1``) the matrix ``L_{e_i}`` is antisymmetric
    (∈ so(4)). ``L`` is a HOMOMORPHISM — ``L(pq) = L(p)L(q)`` — and commutes
    with every right multiplication (``L(p)R(q) = R(q)L(p)``, the
    associativity witness ℍ has and 𝕆 lacks). The SIGN STRUCTURE of the
    basis columns is the F380 bridge: the unique nonzero of column ``j`` in
    ``L_{e_i}`` sits at row ``i ⊕ j`` (``Q₈/{±1}`` = the Klein-4 XOR table).

    Class M (Clifford / HDC binding).

    **THE CARRIER IS THE OPERAND'S, NOT THE OP'S** (rc465, `#T1188`) — the same
    rule :func:`srmech.physics.qm.octonion.octonion_left_mult` carries at rung 8,
    and this op had the identical defect: ``_as_quaternion`` coerced with
    ``[float(c) for c in v]`` at the entry, so
    ``quaternion_left_mult([2**53+1, 0, 0, 0])[0, 0]`` returned
    ``9007199254740992.0``. An exact operand (``int`` / ``Q`` /
    ``(num, den)``) now returns an exact-ℚ ``QMat`` through
    :func:`srmech.cascade.left_mult_matrix`; one float component anywhere routes
    the whole call to the C peer below; ``QMat.to_mat()`` projects on demand.
    Measured equal on both routes over the 4 basis vectors and 12 random integer
    4-vectors.

    The FLOAT route dispatches to the same-rc C peer
    ``srmech_quaternion_left_mult`` (byte-exact table fallback otherwise) and is
    **accurate to round-off** — every component is truncated to a 53-bit
    significand on entry.

    Args:
        q: A 4-vector quaternion (components ``(q_0, q_1, q_2, q_3)``); exact
            (``int`` / ``Q`` / ``(num, den)``) or ``float``.

    Returns:
        ``4×4`` exact-ℚ ``QMat`` ``L_q`` for an exact operand; ``4×4`` real
        ``Mat`` for a float one.

    Raises:
        ValueError: if ``q`` is not a 4-vector (on EITHER carrier).
    """
    q = _operand_leaves(q, "quaternion_left_mult")
    exact = _exact_quaternion(q)
    if exact is not None:
        return QMat.from_rows(_left_mult_matrix(exact))
    q = _as_quaternion(q, "quaternion_left_mult")
    native = _try_native_mult("srmech_quaternion_left_mult", q)
    if native is not None:
        return Mat.from_rows(native, is_complex=False)
    table = _build_mult_table()
    rows = [[sum(q[i] * table[i][j][k] for i in range(_DIM)) for j in range(_DIM)]
            for k in range(_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def quaternion_right_mult(q: Sequence[int | Q | Tuple[int, int] | float]) -> Mat | QMat:
    """Right-multiplication matrix ``R_q`` (``x → x·q``) as a ``4×4`` real ``Mat``.

    Column ``j`` is ``e_j * q``; ``R_q[k, j] = sum_i q_i C[j][i][k]``. Right
    multiplication is an ANTI-homomorphism — ``R(pq) = R(q)R(p)`` (ℍ is
    non-commutative, so ``L_q ≠ R_q`` for a generic ``q``; the genuinely
    distinct left/right QDFT forms stand on exactly this).

    Class M (Clifford / HDC binding).

    **THE CARRIER IS THE OPERAND'S, NOT THE OP'S** (rc465, `#T1188`) — the
    :func:`quaternion_left_mult` rule verbatim. An exact operand returns an
    exact-ℚ ``QMat`` via :func:`srmech.cascade.right_mult_matrix`; one float
    component anywhere routes the whole call to the C peer below;
    ``QMat.to_mat()`` projects on demand.

    The FLOAT route dispatches to the same-rc C peer
    ``srmech_quaternion_right_mult`` (byte-exact table fallback otherwise) and
    is **accurate to round-off** — every component is truncated to a 53-bit
    significand on entry.

    Args:
        q: A 4-vector quaternion; exact (``int`` / ``Q`` / ``(num, den)``) or
            ``float``.

    Returns:
        ``4×4`` exact-ℚ ``QMat`` ``R_q`` for an exact operand; ``4×4`` real
        ``Mat`` for a float one.

    Raises:
        ValueError: if ``q`` is not a 4-vector (on EITHER carrier).
    """
    q = _operand_leaves(q, "quaternion_right_mult")
    exact = _exact_quaternion(q)
    if exact is not None:
        return QMat.from_rows(_right_mult_matrix(exact))
    q = _as_quaternion(q, "quaternion_right_mult")
    native = _try_native_mult("srmech_quaternion_right_mult", q)
    if native is not None:
        return Mat.from_rows(native, is_complex=False)
    table = _build_mult_table()
    rows = [[sum(q[i] * table[j][i][k] for i in range(_DIM)) for j in range(_DIM)]
            for k in range(_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def _try_native_conjugate(x: List[float]) -> List[float]:
    """Dispatch ``conj(x)`` to ``srmech_quaternion_conjugate`` (the rc309 C
    peer), returning the 4-vector ``list[float]`` — or ``None`` for the pure
    path. ctypes-only (no numpy)."""
    if not _native_ready("srmech_quaternion_conjugate"):
        return None
    Arr = ctypes.c_double * _DIM
    c_x = Arr(*(float(v) for v in x))
    c_out = Arr()
    rc = _native.LIB.srmech_quaternion_conjugate(
        ctypes.cast(c_x, _DBLP), ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [float(c_out[i]) for i in range(_DIM)]


def quaternion_conjugate(x: Sequence[int | Q | Tuple[int, int] | float]) -> List[float] | List[Q]:
    """Quaternion conjugate ``conj(x) = (x_0, -x_1, -x_2, -x_3)``.

    Flips the sign of the three imaginary axes (the scalar axis is fixed).
    For a UNIT twiddle it is the inverse: ``conj(exp(μθ)) = exp(−μθ)`` — the
    inverse-QDFT twiddle. Class C (chirality / orientation); a plain sign
    flip (no ``abs()``), mirroring :func:`srmech.physics.qm.octonion.octonion_conjugate`.
    Dispatches to the same-rc C peer ``srmech_quaternion_conjugate`` (byte-exact
    pure fallback otherwise).

    **THE CARRIER IS THE OPERAND'S, NOT THE OP'S** (rc465, `#T1188`). An exact
    operand returns ``list[Q]`` through :func:`srmech.cascade.cd_conjugate` (the
    exact-ℚ C peer ``srmech_cd_qconjugate``); a float operand keeps the C peer
    below and is **accurate to round-off**. Through rc464 this sign flip — an
    op that performs no arithmetic at all — returned ``9007199254740992.0`` for
    ``[2**53+1, 0, 0, 0]``.

    Args:
        x: A 4-vector quaternion; exact (``int`` / ``Q`` / ``(num, den)``) or
            ``float``.

    Returns:
        The 4-vector conjugate: ``list[Q]`` for an exact operand,
        ``list[float]`` for a float one.

    Raises:
        ValueError: if ``x`` is not a 4-vector (on EITHER carrier).
    """
    x = _operand_leaves(x, "quaternion_conjugate")
    exact = _exact_quaternion(x)
    if exact is not None:
        return list(_cd_conjugate(exact))
    x = _as_quaternion(x, "quaternion_conjugate")
    native = _try_native_conjugate(x)
    if native is not None:
        return native
    return [x[0]] + [-x[i] for i in range(1, _DIM)]


def quaternion_norm(x: Sequence[int | Q | Tuple[int, int] | float]) -> float | Q:
    """Quaternion norm ``sqrt(sum x_i²)`` (Class K + Class C; never ``abs()``).

    The norm form of the composition algebra (``N(x) = x·conj(x)``).

    **SCOPE — this is the DEFINITE ℍ** (named rc352, `#T1001`). ``Σ xᵢ²``
    equals ``Re(x·x̄)`` because this module's product is
    :func:`quaternion_mult_table`'s, whose three imaginary units all square to
    ``−1``. On **split-ℍ** two square to ``+1``, the norm form is the
    indefinite ``(2, 2)`` one, and this function would report a positive number
    for a genuine null vector. Not a latent bug here — this module cannot
    construct a split algebra — but for a twist use
    ``cd_norm_sq(x, gammas=…)``. Peer of
    :func:`srmech.physics.qm.octonion.octonion_norm`, same scope.

    The sum-of-squares is reduced to a scalar float, passed through the Class K
    pin-slot magnitude (:func:`srmech.cascade.magnitude` — the
    cascade-honest ``abs()`` replacement), then the Class-N
    :func:`srmech.math.rational.sqrt`. Mirrors
    :func:`srmech.physics.qm.octonion.octonion_norm` at dim 4.

    **THE CARRIER IS THE OPERAND'S, NOT THE OP'S** (rc465, `#T1188`) — and as at
    rung 8, this op is an exact ROUTE rather than an exact CARRIER, because a
    square root is not a rational function. An exact operand takes ``Σ xᵢ²``
    through :func:`srmech.cascade.cd_norm_sq` (the C peer
    ``srmech_cd_qnorm_sq``), the Class-K pin-slot magnitude, then the Class-N
    :func:`srmech.math.rational.sqrt`, and returns a ``Q``: EXACT when the root
    lands on the Class-N DYADIC grid — an integer root, or one whose reduced
    denominator is a power of two — and **accurate to** ``2**-54`` relative
    otherwise. A rational root with an odd denominator does NOT land on the
    nose (measured: ``sqrt(Q(25, 49))`` is not ``5/7``), so this is a narrower
    claim than "exact whenever the root is rational", which is what rc465 first
    shipped here and in the sibling at rung 8. A float operand keeps the float
    route and its terminal float lift, **accurate to round-off**.

    Args:
        x: A 4-vector quaternion; exact (``int`` / ``Q`` / ``(num, den)``) or
            ``float``.

    Returns:
        The non-negative Euclidean norm: an exact-ℚ ``Q`` for an exact operand
        (exact on the Class-N dyadic grid — an integer root or a power-of-two
        denominator; otherwise that root to ``2**-54`` relative), a ``float``
        for a float one.

    Raises:
        ValueError: if ``x`` is not a 4-vector (on EITHER carrier).
    """
    x = _operand_leaves(x, "quaternion_norm")
    exact = _exact_quaternion(x)
    if exact is not None:
        # The SAME cascade as the float route, on the exact carrier: Class-K
        # pin-slot (magnitude is type-preserving over Q since rc362) then the
        # Class-N root. Never abs().
        return _rsqrt(_magnitude(_cd_norm_sq(exact)))
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
    axis; ``conj(exp(μθ)) = exp(−μθ)``; and ``exp(μ·2π/N)^N = 1`` **to a
    stated float tolerance, not exactly** (the N-th-roots closure the DFT
    needs — see :func:`quaternion_twiddle`, which carries the exactness note
    in full).

    Exactness convention (module docstring): trig is the Q61 Class-N cascade
    (``rational.{cos,sin}``; native ``srmech_{cos,sin}_q61``) projected to
    float ONCE; the exact-rational tier is
    :func:`quaternion_exp_series_truncate`; the exact-Q61 equal-weight-axis
    tier is :func:`srmech.cascade.hypercomplex_exp` (``k_axes=3``).
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


# =====================================================================
# rc385 (#T1048) — the ℍ log/slerp pair: the INVERSE of the exp twiddle
# (quaternion_log) and the exp/log geodesic interpolation (quaternion_slerp).
# The clean continuation of the hypercomplex arc (rc308 quaternion_laplacian,
# rc384 octonion_frame_read). Both carry byte-exact same-rc C peers.
# =====================================================================


def _try_native_log(q: List[float]) -> List[float]:
    """Dispatch ``log(q)`` to ``srmech_quaternion_log`` (the rc385 C peer),
    returning the 4-vector ``list[float]`` — or ``None`` for the pure path.
    ctypes-only (no numpy)."""
    if not _native_ready("srmech_quaternion_log"):
        return None
    Arr = ctypes.c_double * _DIM
    c_q = Arr(*(float(v) for v in q))
    c_out = Arr()
    rc = _native.LIB.srmech_quaternion_log(
        ctypes.cast(c_q, _DBLP), ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [float(c_out[i]) for i in range(_DIM)]


def quaternion_log(q: Sequence[int | Q | Tuple[int, int] | float]) -> List[float] | List[Q]:
    """The INVERSE of :func:`quaternion_exp` — the unit-quaternion log map.

    For a UNIT quaternion ``q = [w, v]`` (``v`` the 3-vector imaginary part)
    returns the tangent-space element ``[0, θ·v̂]`` where ``‖v‖`` is the Class-K
    magnitude of ``v``, ``θ = atan2(‖v‖, w) ∈ [0, π]`` and ``v̂ = v/‖v‖``. This
    is the pure-imaginary log the :func:`quaternion_slerp` geodesic rides:
    ``exp(quaternion_log(q)) == q`` for a unit ``q``. The pure-real branch
    (``‖v‖ == 0``, i.e. ``q = ±1``) is the **Class-K pin-slot at zero**: the
    zero tangent ``[0, 0, 0, 0]`` (the ‖v‖→0 limit — no preferred axis, taken
    as the zero-imaginary limit).

    ``‖v‖`` is the Class-N :func:`srmech.math.rational.sqrt` of a manifest
    sum-of-squares (Class-K magnitude via :func:`srmech.cascade.magnitude`;
    never ``abs()``); ``θ`` is the Class-N :func:`srmech.math.rational.atan2`
    (the Q61 atan cascade with the quadrant handled in exact rational space,
    projected to float ONCE — no libm ``atan2``). Dispatches to the same-rc C
    peer ``srmech_quaternion_log`` (byte-exact pure fallback otherwise). Class K
    (‖v‖ + the pin-slot) ∘ Class N (sqrt + atan2) ∘ Class C (the v̂ orientation).

    **THE CARRIER IS THE OPERAND'S, NOT THE OP'S** (rc466, `#T1188`) — an exact
    ROUTE, the ``quaternion_norm`` shape one cascade longer. For an exact
    operand (``int`` / ``Q`` / ``(num, den)`` components — the pair spelling
    raised "must be a 4-vector" through rc465): ``‖v‖²`` is the exact ``Q``
    sum of squares; ``‖v‖`` is the Class-N :func:`srmech.math.rational.sqrt`
    of it — EXACT on the Class-N dyadic grid (an integer root, or a
    power-of-two denominator), **accurate to** ``2**-54`` relative otherwise;
    ``θ`` is the Class-N Q61 :func:`srmech.math.rational.atan2` cascade **on a
    ratio rounded to round-off** (``atan2`` casts its two arguments to float64
    before the cascade, so ``θ`` is accurate to ~1 ULP of that ratio plus the
    ``2**-61`` grid); and ``v̂ = v/‖v‖`` and ``θ·v̂`` are exact ``Q`` products.
    The result is ``list[Q]`` — the DIRECTION is carried exactly (through
    rc465 the float route perturbed it: ``quaternion_log([1, 2**53+1, 0, 0])``
    and ``[1, 2**53, 0, 0]`` gave the same ``θ·v̂₁`` and ``2**53+2`` a different
    one, on an axis that is exactly ``(1, 0, 0)`` for all three), and the
    pin-slot at zero returns the exact zero tangent. A float component
    anywhere keeps the float route — the C peer ``srmech_quaternion_log`` —
    **accurate to round-off**.

    Args:
        q: A 4-vector quaternion (typically unit); exact or ``float``.

    Returns:
        The pure-imaginary log ``[0, θ·v̂₁, θ·v̂₂, θ·v̂₃]`` — ``list[Q]`` for an
        exact operand, ``list[float]`` for a float one.

    Raises:
        ValueError: if ``q`` is not a 4-vector (on EITHER carrier).
    """
    q = _operand_leaves(q, "quaternion_log")
    exact = _exact_quaternion(q)
    if exact is not None:
        w, v1, v2, v3 = exact
        norm_sq = v1 * v1 + v2 * v2 + v3 * v3
        if norm_sq == 0:                            # Class-K pin-slot at zero
            return [Q(0, 1), Q(0, 1), Q(0, 1), Q(0, 1)]
        nv = _rsqrt(_magnitude(norm_sq))             # Class-K magnitude ∘ Class-N sqrt (Q)
        theta = _ratan2(nv, w)                       # Class-N atan2 (Q61 Q; float-cast args)
        return [Q(0, 1), theta * v1 / nv, theta * v2 / nv, theta * v3 / nv]
    q = _as_quaternion(q, "quaternion_log")
    native = _try_native_log(q)
    if native is not None:
        return native
    w = q[0]
    # ‖v‖² is a sum of squares — manifestly ≥ 0, so the Class-K pin-slot at zero
    # is a plain ``== 0.0`` compare, never an ``abs()``.
    norm_sq = q[1] * q[1] + q[2] * q[2] + q[3] * q[3]
    if norm_sq == 0.0:                              # Class-K pin-slot at zero
        return [0.0, 0.0, 0.0, 0.0]
    nv = float(_rsqrt(_magnitude(norm_sq)))         # Class-K magnitude ∘ Class-N sqrt
    theta = float(_ratan2(nv, w))                   # Class-N atan2 (Q61 quadrant)
    return [0.0, theta * q[1] / nv, theta * q[2] / nv, theta * q[3] / nv]


def _quat_mul_cd(x: List[float], y: List[float]) -> List[float]:
    """Hamilton product ``x · y`` byte-exact with the C ``srmech_quat__mul4`` —
    the Cayley-Dickson complex-pair formula ``(a, b)(c, d) = (a c − conj(d) b,
    d a + b conj(c))`` replicating the native float-op ORDER limb-for-limb
    (Class M bind ∘ Class C orientation via the CD conjugates; no ``abs()``).

    Distinct from :func:`_quat_mul` (the ``L_a``-table row-dot the holonomy path
    uses, which is byte-exact with a DIFFERENT C helper). A GENERAL product sums
    four signed terms, so the association order is load-bearing: the slerp
    cascade dispatches to ``srmech_quat__mul4``, so its pure mirror must reduce
    in that same order."""
    def _mul2(p0, p1, q0, q1):                       # srmech_quat__mul2
        return (p0 * q0 - q1 * p1, q1 * p0 + p1 * q0)
    dconj0, dconj1 = y[2], -y[3]
    cconj0, cconj1 = y[0], -y[1]
    ac0, ac1 = _mul2(x[0], x[1], y[0], y[1])         # a c
    db0, db1 = _mul2(dconj0, dconj1, x[2], x[3])     # conj(d) b
    da0, da1 = _mul2(y[2], y[3], x[0], x[1])         # d a
    bc0, bc1 = _mul2(x[2], x[3], cconj0, cconj1)     # b conj(c)
    return [ac0 - db0, ac1 - db1, da0 + bc0, da1 + bc1]


def _exp_pure_imag(tw: List[float]) -> List[float]:
    """``exp([0, v])`` for a PURE-imaginary quaternion ``tw = [0, v₁, v₂, v₃]``
    — angle ``‖v‖`` (Class-N sqrt of the Class-K sum of squares), axis ``v/‖v‖``
    resolved inside :func:`quaternion_exp`; the ``‖v‖ → 0`` pin-slot is
    ``exp(0) =`` identity. Byte-exact with the C ``srmech_quat__exp_pure``
    mirror (same float-op order)."""
    tn_sq = tw[1] * tw[1] + tw[2] * tw[2] + tw[3] * tw[3]
    if tn_sq == 0.0:                                # Class-K pin-slot: exp(0)=1
        return [1.0, 0.0, 0.0, 0.0]
    tnorm = float(_rsqrt(_magnitude(tn_sq)))        # ‖v‖  (Class K ∘ N)
    return quaternion_exp(tnorm, [0.0, tw[1], tw[2], tw[3]])


def _try_native_slerp(q0: List[float], q1: List[float], t: float) -> List[float]:
    """Dispatch ``slerp(q0, q1, t)`` to ``srmech_quaternion_slerp`` (the rc385
    C peer), returning the 4-vector ``list[float]`` — or ``None`` for the pure
    path. ctypes-only (no numpy)."""
    if not _native_ready("srmech_quaternion_slerp"):
        return None
    Arr = ctypes.c_double * _DIM
    c_q0 = Arr(*(float(v) for v in q0))
    c_q1 = Arr(*(float(v) for v in q1))
    c_out = Arr()
    rc = _native.LIB.srmech_quaternion_slerp(
        ctypes.cast(c_q0, _DBLP), ctypes.cast(c_q1, _DBLP), ctypes.c_double(t),
        ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [float(c_out[i]) for i in range(_DIM)]


def quaternion_slerp(q0: Sequence[int | Q | Tuple[int, int] | float], q1: Sequence[int | Q | Tuple[int, int] | float],
                     t: float) -> List[float]:
    """Shortest-arc geodesic interpolation on the unit-quaternion S³ —
    ``slerp(q0, q1, t) = q0 · exp(t · log(conj(q0)·q1))``.

    The exp/log SO(3)-geodesic form: ``r = conj(q0)·q1`` is the relative
    rotation, ``log(r) = θ·μ̂`` its tangent (axis μ̂, angle θ), ``t·log(r)``
    walks a fraction ``t`` along it, and the left-multiply by ``q0`` carries the
    walk back to base. Endpoints: ``slerp(q0, q1, 0) = q0`` and, for UNIT
    ``q0``/``q1``, ``slerp(q0, q1, 1) = q1``. The degenerate ``log(r) = 0``
    branch (``q1 = ±q0``, a pure-real ``r``) is the Class-K pin-slot ``exp(0) =
    1`` and returns ``q0``.

    A pure composition of the shipped ℍ ops: :func:`quaternion_conjugate`
    (Class C) ∘ the Cayley-Dickson Hamilton product (Class M, byte-exact with
    ``srmech_quat__mul4``) ∘ :func:`quaternion_log` (rc385, Class K∘N) ∘
    :func:`quaternion_exp` (Class N∘C). Dispatches to the same-rc C peer
    ``srmech_quaternion_slerp`` (byte-exact pure fallback); no ``abs()``, no libm.

    Args:
        q0: The start quaternion (typically unit).
        q1: The end quaternion (typically unit).
        t: The interpolation parameter (``0 → q0``, ``1 → q1``); any finite
            float (``t`` outside ``[0, 1]`` extrapolates along the geodesic).

    Returns:
        The interpolated quaternion as a ``list[float]``.

    Raises:
        ValueError: if ``q0`` or ``q1`` is not a 4-vector.
    """
    q0 = _as_quaternion(q0, "quaternion_slerp")
    q1 = _as_quaternion(q1, "quaternion_slerp")
    t = float(t)
    native = _try_native_slerp(q0, q1, t)
    if native is not None:
        return native
    c0 = quaternion_conjugate(q0)                    # Class C
    r = _quat_mul_cd(c0, q1)                          # Class M (CD Hamilton product)
    lg = quaternion_log(r)                            # [0, θ·μ̂]
    tw = [0.0, t * lg[1], t * lg[2], t * lg[3]]       # t · log(r)
    e = _exp_pure_imag(tw)                            # exp(t · log(r))
    return _quat_mul_cd(q0, e)                        # q0 · exp(...)


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
    :func:`srmech.math.rational.cos_series_truncate` /
    :func:`srmech.math.rational.sin_series_truncate` (Taylor partial sums to
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
    EXACT identity, and ``exp(μ·2π/N)^N = 1`` **to a float tolerance, not
    exactly** — gated at ``|residual| ≤ 1e-9·N`` by
    ``tests/test_qm_quaternion_rc109.py``
    ``test_twiddle_nth_roots_of_unity_closure``.

    ⚠️ **Exactness gap (0.9.0rc467, `#T1188`) — recorded, not closed.** The
    target IS a root of unity, an exact algebraic integer; this carrier is
    float64 and does NOT satisfy the closure exactly (MEASURED on the sibling
    exact-Q61 tier: :func:`srmech.cascade.hypercomplex_exp` at ``2π/8`` raised
    to the 8th is a ratio of 147-digit integers, not ``1``). An EXACT route
    for the same object ships one module over —
    :func:`srmech.math.qalg.cos_2pi_over_n` /
    :func:`~srmech.math.qalg.sin_2pi_over_n`, on which
    ``(2·cos_2pi_over_n(8))² == 2``, ``cos² + sin² == 1`` and ``ζ₈⁸ == 1``
    all hold EXACTLY — and this op deliberately does NOT take it. Swapping
    the carrier is a DFT-path change with its own blast radius, scoped to a
    later rc; until then the identity above is a TOLERANCE and is written
    here as one.

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


# =====================================================================
# rc309 (#944 follow-on) — quaternion_cycle_holonomy: the k=2 discrete
# holonomy channel over the quaternion units Q8 (the ℍ "which-way" /
# Lk-analog reader). The NON-ABELIAN generalization of the abelian
# srmech.math.laplacian.cycle_holonomy (Zaslavsky signed-graph switching)
# to a non-commutative gain group.
# =====================================================================

#: Scalar-part bucket radius for the SU(2) conjugacy-class read (matches
#: SRMECH_QHOLO_TOL in the C peer). Q8-derived holonomies land on scalar
#: {+1, 0, -1} exactly; a continuous re-gauge perturbs by ~1e-15 << tol.
_QHOLO_TOL = 1e-9


def _quat_mul(a: List[float], b: List[float]) -> List[float]:
    """``a · b`` (Hamilton product), byte-exact with the C ``qholo_mul``.

    Builds the left-multiplication matrix ``L_a`` from the Cayley-Dickson
    structure table (columns are exact ``±a_i`` signed permutations — no
    rounding, identical to ``srmech_quaternion_left_mult``), then the row-dot
    ``(L_a · b)_i = Σ_k L_a[i,k]·b[k]`` accumulated left-to-right — the SAME
    float-op order the native peer uses, so native == pure to the bit."""
    table = _build_mult_table()
    out = [0.0, 0.0, 0.0, 0.0]
    for i in range(_DIM):
        t = 0.0
        for k in range(_DIM):
            la_ik = 0.0
            for j in range(_DIM):
                la_ik += a[j] * table[j][k][i]     # (a·e_k)_i = Σ_j a_j C[j][k][i]
            t += la_ik * b[k]
        out[i] = t
    return out


def _quat_class(h: List[float]) -> Tuple[int, int]:
    """Classify a unit-quaternion holonomy ``h`` by its SU(2) conjugacy class.

    The class is a level set of the scalar part ``w = h[0]`` (a conjugation
    invariant: ``Re(s·h·conj(s)) = Re(h)``). For a Q8-derived connection
    ``w ∈ {+1, 0, −1}``: ``w ≈ +1 → (0, +1)`` = ``{1}``; ``w ≈ −1 → (1, −1)`` =
    ``{−1}`` (the spinor / Lk half-twist); ``w ≈ 0 → (2, 0)`` = the
    pure-imaginary class ``{±i, ±j, ±k}``. ``|·|`` via a signed branch (Class-K
    pin-slot; never ``abs()``). A scalar far from ``{−1, 0, 1}`` means the gains
    were not Q8/unit-consistent → ``ValueError``."""
    w = h[0]
    dp = w - 1.0
    dm = w + 1.0
    adp = dp if dp >= 0.0 else -dp
    adm = dm if dm >= 0.0 else -dm
    aw = w if w >= 0.0 else -w
    if adp < _QHOLO_TOL:
        return 0, 1
    if adm < _QHOLO_TOL:
        return 1, -1
    if aw < _QHOLO_TOL:
        return 2, 0
    raise ValueError(
        f"quaternion_cycle_holonomy: holonomy scalar {w!r} is not Q8-consistent "
        f"(expected near −1, 0 or +1); gains must be unit quaternions drawn "
        f"from Q8 (or a continuous re-gauge of it)"
    )


def _quaternion_cycle_holonomy_py(n, edge_list, gains):
    """Pure-Python complete alternative for :func:`quaternion_cycle_holonomy`.

    Spanning forest by union-find (first-encountered edge = tree edge), then
    ``pot[i]`` = the ordered quaternion product along the UNIQUE tree path
    ``root → i`` (root = the smallest node index per component — the SAME seed
    order the C peer's BFS uses, so the raw holonomy is byte-identical, not just
    conjugate). Per co-tree edge ``H = pot[u] · g_uv · conj(pot[v])``, classified
    by scalar part. ``gains`` is a list of resolved 4-vectors parallel to
    ``edge_list`` (or ``None`` = identity everywhere)."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    ident = [1.0, 0.0, 0.0, 0.0]

    def gain_at(e: int) -> List[float]:
        return list(ident) if gains is None else list(gains[e])

    tree: List[Tuple[int, int, List[float]]] = []
    cotree: List[Tuple[int, int, List[float]]] = []
    for e, (u, v) in enumerate(edge_list):
        ru, rv = find(u), find(v)
        g = gain_at(e)
        if ru != rv:
            parent[rv] = ru
            tree.append((u, v, g))
        else:
            cotree.append((u, v, g))
    pot: List = [None] * n
    adj: List[List[Tuple[int, List[float]]]] = [[] for _ in range(n)]
    for (u, v, g) in tree:
        adj[u].append((v, g))                              # u → v : +g
        adj[v].append((u, quaternion_conjugate(g)))        # v → u : conj(g)
    for s in range(n):
        if pot[s] is not None:
            continue
        pot[s] = list(ident)
        stack = [s]
        while stack:
            x = stack.pop()
            for (y, g) in adj[x]:
                if pot[y] is None:
                    pot[y] = _quat_mul(pot[x], g)           # pot[x] · g
                    stack.append(y)
    class_index: List[int] = []
    center_parity: List[int] = []
    cycle_edges: List[Tuple[int, int]] = []
    holonomies: List[List[float]] = []
    for (u, v, g) in cotree:
        t1 = _quat_mul(pot[u], g)
        h = _quat_mul(t1, quaternion_conjugate(pot[v]))    # pot[u]·g·conj(pot[v])
        cls, par = _quat_class(h)
        class_index.append(cls)
        center_parity.append(par)
        cycle_edges.append((u, v))
        holonomies.append(h)
    return class_index, center_parity, cycle_edges, holonomies


def _quaternion_cycle_holonomy_native(n, edge_list, gain_flat):
    """numpy-free native dispatch for :func:`quaternion_cycle_holonomy` — marshals
    the edge endpoints (uint32) + the flat per-edge quaternion gains (4·n_edges
    doubles, or ``None`` = identity) into ctypes buffers and calls
    ``srmech_quaternion_cycle_holonomy`` with a caller arena sized from
    ``srmech_quaternion_cycle_holonomy_arena_bytes``. Returns
    ``(class_index, center_parity, cycle_edges, holonomies)`` or ``None`` on a
    missing symbol / non-OK status (caller then runs the pure-Python path)."""
    if not _native.has_native_quaternion_cycle_holonomy():
        return None
    n_edges = len(edge_list)
    eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in edge_list))
    ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in edge_list))
    gp = None if gain_flat is None else \
        (ctypes.c_double * (_DIM * n_edges))(*gain_flat)
    ocls = (ctypes.c_uint32 * max(n_edges, 1))()
    opar = (ctypes.c_int32 * max(n_edges, 1))()
    ocu = (ctypes.c_uint32 * max(n_edges, 1))()
    ocv = (ctypes.c_uint32 * max(n_edges, 1))()
    ohol = (ctypes.c_double * (_DIM * max(n_edges, 1)))()
    ncyc = ctypes.c_uint32(0)
    ws_bytes = int(_native.LIB.srmech_quaternion_cycle_holonomy_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges)))
    ws = (ctypes.c_char * ws_bytes)()
    rc = _native.LIB.srmech_quaternion_cycle_holonomy(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, gp,
        ocls, opar, ocu, ocv, ohol, ctypes.byref(ncyc),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_bytes),
    )
    if rc != _native.SRMECH_OK:
        return None
    m = ncyc.value
    class_index = [int(ocls[i]) for i in range(m)]
    center_parity = [int(opar[i]) for i in range(m)]
    cycle_edges = [(int(ocu[i]), int(ocv[i])) for i in range(m)]
    holonomies = [[float(ohol[_DIM * i + t]) for t in range(_DIM)]
                  for i in range(m)]
    return class_index, center_parity, cycle_edges, holonomies


def quaternion_cycle_holonomy(
    edges: "Sequence[Tuple[int, int]]",
    gains=None,
    *,
    n: "int | None" = None,
) -> dict:
    """The NON-ABELIAN cycle holonomies of a quaternion gain graph — the k=2
    discrete which-way / Lk-analog channel (rc309, #944 follow-on).

    The associative sibling of the abelian
    :func:`srmech.math.laplacian.cycle_holonomy`. Each edge carries a UNIT
    quaternion gain (drawn from ``Q₈ = {±1, ±i, ±j, ±k}`` or a continuous
    re-gauge of it). For each fundamental cycle the holonomy is the **ordered
    quaternion product** walked around it,

        ``H = P_u · g_uv · conj(P_v)``,

    where ``P_x`` is the ordered product of edge gains along the tree path
    ``root → x`` (a reversed edge contributes ``conj(gain)`` = its inverse). A
    node-wise re-gauge ``g_uv → s_u · g_uv · conj(s_v)`` telescopes to
    ``H → s_root · H · conj(s_root)`` — the holonomy is **conjugated** by the
    base-point gauge, so its **conjugacy class is gauge-invariant** (Zaslavsky's
    switching theory, non-abelian form).

    The gauge-invariant read — for unit quaternions (SU(2)) the conjugacy class
    is a level set of the **scalar part** ``w = Re(H)`` (a conjugation invariant:
    ``Re(s·H·conj(s)) = Re(H)`` exactly). For a Q₈-derived connection
    ``w ∈ {+1, 0, −1}``, giving three frame-free classes:

    ==============  ===========  =============  ===============================
    ``class_index``  conj. class  ``center_parity``  meaning
    ==============  ===========  =============  ===============================
    ``0``            ``{1}``      ``+1``         trivial (balanced) holonomy
    ``1``            ``{−1}``     ``−1``         the spinor / Lk central half-twist
    ``2``            ``{±i,±j,±k}`` ``0``        pure-imaginary (quarter-turn)
    ==============  ===========  =============  ===============================

    MEASURED, not assumed (the rc309 proof gate): the finer 5-class Q₈ split
    ``{±i}``/``{±j}``/``{±k}`` is invariant only under **discrete Q₈** re-gauge;
    under **continuous** unit-quaternion re-gauge SU(2) merges the three
    imaginary axes (``i`` and ``j`` are SU(2)-conjugate), so **only the
    scalar-part class above is frame-free**. That is the sound keystone this op
    ships; ``center_parity`` (the ``{1}``-vs-``{−1}`` central sign) is a class
    function, hence also invariant. The raw ``holonomies`` quaternions genuinely
    MOVE under re-gauge while the class holds — see
    ``test_quaternion_cycle_holonomy_rc309.py`` for the committed measurement.

    Dispatches to the standalone-C ``srmech_quaternion_cycle_holonomy`` (caller
    arena) when ``HAS_NATIVE``; else srmech's own quaternion cascade (the
    complete alternative, byte-exact). No ``abs()`` (sign is
    Class K ∘ Class C). Class M (quaternion bind) ∘ Class L (graph) ∘ Class C
    (orientation).

    Args:
        edges: The graph edges ``(u, v)``. A parallel edge closes a digon; a
            self-loop is a 1-cycle carrying its own gain.
        gains: Per-edge UNIT quaternion gain (a 4-sequence) parallel to
            ``edges``; ``(u, v, g) ≡ (v, u, conj(g))``. ``None`` → identity
            everywhere (a trivially balanced graph).
        n: Node count (keyword-only); inferred as one past the largest endpoint
            when ``None``.

    Returns:
        ``dict`` with ``n_cycles`` (int), ``class_index`` (list[int], the SU(2)
        class per cycle), ``center_parity`` (list[int], +1/−1/0), ``cycle_edges``
        (list[(u, v)] — the co-tree edge per cycle), ``holonomies`` (list of the
        raw ℍ 4-vectors), and ``balanced`` (bool — all ``class_index == 0``).

    Raises:
        ValueError: an out-of-range endpoint; a ``gains`` length mismatch; or a
            holonomy scalar not Q₈-consistent (gains not unit / not Q₈-derived).
    """
    edge_list = [tuple(e) for e in edges]
    n_edges = len(edge_list)
    if n is None:
        nn = 0
        for (u, v) in edge_list:
            nn = max(nn, int(u) + 1, int(v) + 1)
    else:
        nn = int(n)
    for k, (u, v) in enumerate(edge_list):
        if not (0 <= u < nn and 0 <= v < nn):
            raise ValueError(
                f"quaternion_cycle_holonomy: edge {k} = ({u}, {v}) outside "
                f"node range [0, {nn})"
            )
    if gains is None:
        gain_resolved = None
        gain_flat = None
    else:
        gain_resolved = [_as_quaternion(g, "quaternion_cycle_holonomy")
                         for g in gains]
        if len(gain_resolved) != n_edges:
            raise ValueError(
                f"quaternion_cycle_holonomy: gains length {len(gain_resolved)} "
                f"!= n_edges {n_edges}"
            )
        gain_flat = [c for g in gain_resolved for c in g]
    if nn == 0:
        return {"n_cycles": 0, "class_index": [], "center_parity": [],
                "cycle_edges": [], "holonomies": [], "balanced": True}
    res = _quaternion_cycle_holonomy_native(nn, edge_list, gain_flat)
    if res is None:
        res = _quaternion_cycle_holonomy_py(nn, edge_list, gain_resolved)
    class_index, center_parity, cycle_edges, holonomies = res
    balanced = all(c == 0 for c in class_index)
    return {
        "n_cycles": len(class_index),
        "class_index": class_index,
        "center_parity": center_parity,
        "cycle_edges": cycle_edges,
        "holonomies": holonomies,
        "balanced": balanced,
    }


__all__ = [
    "quaternion_conjugate",
    "quaternion_cycle_holonomy",
    "quaternion_exp",
    "quaternion_exp_series_truncate",
    "quaternion_left_mult",
    "quaternion_log",
    "quaternion_mult_table",
    "quaternion_norm",
    "quaternion_right_mult",
    "quaternion_slerp",
    "quaternion_table_attestation",
    "quaternion_twiddle",
]
