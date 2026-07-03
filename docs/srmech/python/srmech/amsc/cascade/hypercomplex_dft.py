"""Quaternion / octonion discrete Fourier transforms — the native transform
for a Klein-4 object (#863, F380).

A **Klein-4 object** (the 4-state-per-coordinate HDC object srmech ships as
``hdc.klein4_*`` — the two chirality axes γ₅ and iω₇, ``Z₂×Z₂``) has two
``Z₂`` axes. The only Fourier op otherwise shipped is the **complex**
``signal_processing.closed_form_ops.fft`` (the ``k=1`` / ``S¹`` rung).
Fourier-analysing a Klein-4 object with a *complex* FFT first projects it to
``ℂ``, which collapses one of its two ``Z₂`` axes — we see only **the flat
shadow**.

The fix is exact, not analogical (F380):

    The Klein-4 group IS the quaternion units modulo sign.
    Q₈ = {±1,±i,±j,±k}, centre {±1}, and  Q₈/{±1} ≅ Z₂×Z₂ = Klein-4.

So the coefficient algebra of each FFT-ladder rung carries a different
chirality content (F379, "n things with n−1 couplings"):

    transform       coeff. algebra   units mod sign        chirality resolved
    complex FFT      ℂ                {±1,±i}/± = Z₂        one axis (flat shadow)
    quaternion FT    ℍ                Q₈/± = Z₂×Z₂          BOTH axes (γ₅ & iω₇)
    octonion FT      𝕆                the (8:7) rung        + F378 non-associativity

A quaternion FT's coefficient algebra **matches** the Klein-4 object's value
algebra, so both chirality axes survive — exactly what an RBS-SNN Klein-4
object needs and what the complex FFT cannot give.

**These compose existing atoms — no new primitive class** (the
non-commutativity of ``ℍ`` / ``𝕆`` is load-bearing: there are genuinely
**left- / right- / two-sided** forms; the twiddle cannot be factored out the
way the complex FFT does). The 14-class A–N vocabulary is intact
(``[[feedback_no_privileged_primitive_classes]]``). No ``abs()`` — the
norm/conjugate route through Class K+C, never an ALU absolute value.

**GRADUATION (0.9.0rc110 + rc111; #1234 Items 1b/1c, re-raise of #863):**

- :func:`quaternion_dft` **GRADUATED at rc110** — a first-class op over the
  rc109 ``srmech.qm.quaternion`` foundation (the 4×4 ``L_q``/``R_q``
  operators + ``quaternion_twiddle``, no longer the sliced 8×8 octonion
  embedding) with the whole-transform C peer ``srmech_quaternion_dft``
  (byte-exact composed fallback).
- :func:`octonion_dft` **GRADUATED at rc111** — first-class over the
  ``srmech.qm.octonion`` foundation (the 8×8 ``L_a``/``R_a`` operators +
  the rc111 ``octonion_twiddle``) with the whole-transform C peer
  ``srmech_octonion_dft`` covering ALL THREE forms (left / right /
  two_sided; byte-exact composed fallback). The 𝕆 non-associativity makes
  the BRACKETING an EXPLICIT ATTESTED FIELD — see the op docstring + the
  ``octonion_dft.toml`` ``[cascade.bracketing]`` attestation block.
- :func:`hypercomplex_couple` remains the composite tier over the
  exact-Q61 octonion couple.

**Numpy-free (rc125, #564).** The whole module runs with **zero numpy** —
the octonion samples / twiddles / accumulators are plain ``list[float]`` of
length 8, the ``octonion_{left,right}_mult`` operators are consumed as the
numpy-free :class:`srmech.amsc.mat.Mat` they now return, and the per-term
matvec rides a numpy-free :class:`Mat`-column ``mat_matmul`` (the pattern
``qm.single_particle`` used in rc117) — never numpy ``@`` / ``dense_matvec``.
``import srmech.amsc.cascade`` and every transform import + run numpy-absent.

Citations (verified PDFs —
``docs/srmech/notes/qdft_odft_citation_verification_863.md``; the QDFT anchor
RE-verified first-hand at rc110 by PDF text extraction — title + authors +
arXiv ID + the exponential-placement / one-sided-vs-two-sided convention
discussion, §7):
- QDFT: Sangwine, S. J. & Ell, T. A. (2012). *Complex and Hypercomplex
  Discrete Fourier Transforms Based on Matrix Exponential Form of Euler's
  Formula.* Appl. Math. Comput. 219(2):644–655. arXiv:1001.4379.
- ODFT: Błaszczyk, Ł. (2019). *A Generalization of the Octonion Fourier
  Transform to 3-D Octonion-Valued Signals.* arXiv:1905.12631. Origin:
  Hahn, S. L. & Snopek, K. M. (2011). *The unified theory of n-dimensional
  complex and hypercomplex analytic signals.* Bull. Polish Acad. Sci. Tech.
  Sci. 59(2):167–181.
"""
from __future__ import annotations

import ctypes
from typing import List, Sequence, Tuple

# §22: scalar root + trig via the Class-N rational cascade, not libm; π from the
# Archimedes pi_cascade (`[[feedback_continuous_number_line_pedagogical_obstacle]]`).
from srmech.amsc import _native
from srmech.amsc.mat import Mat as _Mat
from srmech.amsc import rational as _rational
from srmech.amsc.q import Q as _Q
from srmech.amsc.rational import cos as _rcos
from srmech.amsc.rational import pi_cascade_digits as _pi_cascade_digits
from srmech.amsc.rational import sin as _rsin
from srmech.amsc.rational import sqrt as _rsqrt

# 0.9.0rc10 (F882, srmech #205) — the LITERAL exp(μθ) twiddle in EXACT Q61.
_Q61_ONE = _rational._Q61_ONE                          # 1.0 in Q61 (= 2**61)
_HC_AXES = (1, 3, 7)                                   # ℂ / ℍ / 𝕆 imaginary dims
# unit 1/√k as a Q61 int = isqrt(2^122 / k): the substrate-native integer-sqrt
# (``rational._integer_sqrt`` → native ``srmech_isqrt``); k=1 → 2**61.
_HC_INV_Q61 = {k: _rational._integer_sqrt((_Q61_ONE * _Q61_ONE) // k) for k in _HC_AXES}


def _q61_int(qv: "_Q") -> int:
    """Recover the raw Q61 integer ``v`` from a ``Q == v / 2**61`` (the reduced
    denominator always divides ``2**61``)."""
    n, d = qv.as_pair()
    return n * (_Q61_ONE // d)

# Cascade-π as a float: the high-precision rational digit-string projected to
# float once at import (no `math.pi`).
_PI_IP, _, _PI_FP = _pi_cascade_digits(30).partition(".")
_PI = int(_PI_IP + _PI_FP) / (10 ** len(_PI_FP))

# Unit pure-imaginary quaternion axes (μ² = −1). The twiddle lives in the
# commutative subalgebra ℝ[μ] ≅ ℂ, which is WHY the one-sided transform is
# invertible: Σ_k exp(μ·2πk(n−n')/N) = N·δ_{n,n'} (geometric series in ℝ[μ]).
_MU_AXES = {
    "i": (0.0, 1.0, 0.0, 0.0),
    "j": (0.0, 0.0, 1.0, 0.0),
    "k": (0.0, 0.0, 0.0, 1.0),
}
# The body-diagonal unit axis (i+j+k)/√3 — the order-3 (triality-adjacent)
# pure-quaternion direction; still μ²=−1.
_S3 = 1.0 / float(_rsqrt(3.0))
_MU_AXES["ijk"] = (0.0, _S3, _S3, _S3)

_FORMS = ("left", "right")
_OCTONION_FORMS = ("left", "right", "two_sided")
_BRACKETINGS = ("left_associated", "right_associated")


# (rc111: the float `_twiddle8` helper GRADUATED into
# ``srmech.qm.octonion.octonion_exp`` / ``octonion_twiddle`` — the ODFT
# twiddle now rides the Q61-cascade qm.octonion foundation, not a local
# float helper.)


# 0.9.0rc16 — the EXACT-Q61 (σ,θ,μ) coupler core: the C-host-parity rewrite of
# `hypercomplex_couple`. The float `Mat` octonion-matvec is replaced by an EXACT
# fixed-width Q61 octonion multiply (the Cayley–Dickson structure constants
# `cd_basis_product` + the Q61 fixed-point multiply), so the coupler is
# byte-exact reproducible by a C-only host (`srmech_hypercomplex_couple_q61`) —
# no float boundary except the final projection. Closes the rc12
# sed_couple/sed_uncouple transitive-ratchet allowlist.
from fractions import Fraction as _Fraction
from srmech.amsc.rational import _q61_fxmul               # Q61 fixed-point multiply
from srmech.amsc.cascade.cayley_dickson import cd_basis_product as _cd_basis
# (`_q61_int` is the module-local Q-int projector defined above.)


def _to_q61(x: float) -> int:
    """Project a float to its nearest Q61 fixed-point int — the deliberate
    float→exact-rational boundary (Python-side only; the C peer receives ints)."""
    return round(_Fraction(float(x)) * _Q61_ONE)


def _octo_mult_q61(a: Sequence[int], b: Sequence[int]) -> List[int]:
    """Exact octonion product ``a·b`` over Q61 — Class-M bilinear bind via the
    Cayley–Dickson structure constants (``cd_basis_product``, the same the C peer
    uses) ∘ Class-C sign orientation ∘ the Q61 fixed-point multiply. Integer
    accumulation is order-independent, so the skip-zero shortcut is exact. No
    float, no ``abs()``."""
    out = [0] * 8
    for i in range(8):
        ai = a[i]
        if ai == 0:
            continue
        for j in range(8):
            bj = b[j]
            if bj == 0:
                continue
            k, s = _cd_basis(8, i, j)
            p = _q61_fxmul(ai, bj)
            out[k] += p if s > 0 else -p          # Class-C orientation; no abs()
    return out


def _q61_couple_fits_native(streams_q61: Sequence[int]) -> bool:
    """True iff every Q61 stream limb is unit-bounded (``|x| ≤ 1``, i.e.
    ``|limb| ≤ 2**61``) — the native int64 Q61 octonion couple's domain ceiling.
    Within it neither the limbs nor the norm-preserving output (``|q| ≤ √8 < 4``)
    overflow int64. Larger magnitudes have no Q61-int64 representation (no bignum
    in C), so they take the pure (bignum-exact) Python path — the documented
    native ceiling, like ``rational._try_c_two_rationals``. Class-K magnitude
    test (no ``abs()``)."""
    for v in streams_q61:
        if v > _Q61_ONE or v < -_Q61_ONE:
            return False
    return True


def _couple_q61(streams_q61: Sequence[int], mu_q61: Sequence[int],
                eff: float, *, form: str) -> List[int]:
    """The exact-Q61 coupler core: ``T ⊗ q`` with the twiddle ``T = exp(eff·μ) =
    cos eff·1 + sin eff·μ`` (Q61) and ``⊗`` the left/right octonion multiply.
    Returns the 8 Q61 ints — byte-exact with ``srmech_hypercomplex_couple_q61``
    when native AND the streams are unit-bounded (the int64 Q61 domain); larger
    magnitudes take the pure bignum-exact path (the Q61 trig cascade +
    cd_basis_product + fxmul are all bit-identical C↔Python in the shared
    domain)."""
    if _native.has_native_hypercomplex_couple() and _q61_couple_fits_native(streams_q61):
        out = _native.hypercomplex_couple_q61_c(     # the whole couple in C
            streams_q61, mu_q61, eff, form == "left")
        if out is not None:                          # None = native int64 ceiling
            return out
    if _native.has_native_trans_q61():
        cos = _native.cos_q61_c(eff)
        sin = _native.sin_q61_c(eff)
    else:
        cos = _q61_int(_rcos(eff))
        sin = _q61_int(_rsin(eff))
    tw = [cos] + [_q61_fxmul(sin, mu_q61[i]) for i in range(1, 8)]
    if form == "left":
        return _octo_mult_q61(tw, streams_q61)    # T·q
    return _octo_mult_q61(streams_q61, tw)        # q·T


def hypercomplex_exp(theta: float, k_axes: int) -> Tuple["_Q", ...]:
    """The unit hypercomplex exponential ``exp(μθ) = cos θ + μ·sin θ`` as an
    8-tuple of EXACT :class:`~srmech.amsc.q.Q` (Q61, denominator ``2**61``).

    ``μ`` is the EQUAL-WEIGHT UNIT pure-imaginary over the first ``k_axes``
    octonion imaginary axes — ``k_axes ∈ {1, 3, 7}`` selecting ``ℂ`` / ``ℍ`` /
    ``𝕆`` (the F882 *literal* QDFT / ODFT twiddle). The eight components are
    ``q[0] = cos θ``, ``q[1..k] = sin θ / √k`` (so ``|q| = 1``), ``q[k+1..7] =
    0``. Feed them into :func:`~srmech.amsc.cascade.cd_mult` to rotate a
    hypercomplex value **in the algebra** (then project once) — the "do the
    transform in ℍ/𝕆, then read out" that beats composing scalar ``phase_bind``
    ops on the projected carrier (F882: ℂ 0.78 = the spirit's ℍ rung; 𝕆/ODFT
    0.81, a new routing high).

    Substrate-native fixed-width Q61 cascade (``rational.{cos,sin}`` + the
    integer-sqrt unit norm — no bignum, no libm), **byte-exact** with the native
    peer ``srmech_hypercomplex_exp_q61`` when present. ``k_axes`` outside
    ``{1, 3, 7}`` or a non-finite ``theta`` raises ``ValueError`` (``Q`` is the
    finite-rational carrier)."""
    if k_axes not in _HC_INV_Q61:
        raise ValueError(
            f"hypercomplex_exp: k_axes must be 1, 3 or 7 (ℂ/ℍ/𝕆); got {k_axes!r}")
    th = float(theta)
    if not _rational._is_finite(th):
        raise ValueError("hypercomplex_exp: theta must be finite (Q is the finite-rational carrier)")
    if _native.has_native_hypercomplex_exp():
        ints = _native.hypercomplex_exp_q61_c(th, k_axes)      # 8 Q61 ints, byte-exact
    else:                                                       # pure Q61 cascade
        c = _q61_int(_rcos(th))
        s = _q61_int(_rsin(th))
        scaled = _rational._q61_fxmul(s, _HC_INV_Q61[k_axes])   # sin θ / √k (Class K·C)
        ints = [c] + [scaled if a < k_axes else 0 for a in range(7)]
    return tuple(_Q(v, _Q61_ONE) for v in ints)


def _as8(vec) -> List[float]:
    """Coerce a 4- or 8-component quaternion/octonion sample to an 8-vector
    ``list[float]`` (numpy-free)."""
    a = [float(x) for x in vec]
    n = len(a)
    if n == 4:
        return a + [0.0, 0.0, 0.0, 0.0]
    if n == 8:
        return list(a)
    raise ValueError(
        f"hypercomplex sample must have 4 (quaternion) or 8 (octonion) "
        f"components; got {n}"
    )


def _resolve_mu(mu_axis, *, octonion) -> List[float]:
    """Resolve ``mu_axis`` to a **unit pure-imaginary** 8-vector ``μ`` (``e0==0``,
    ``‖μ‖=1`` ⟹ ``μ²=−1``) — the transform/coupling axis (#908, §29).

    Accepts:

    * a **named axis** ``'i'`` / ``'j'`` / ``'k'`` / ``'ijk'`` (the shipped set);
    * ``'diagonal'`` — the equal-weight pure-imaginary axis of the active
      algebra: ``(i+j+k)/√3`` for a quaternion transform, ``(Σ_{n=1..7} eₙ)/√7``
      for an octonion one. This is the axis that **couples** all streams (F436):
      ``μ·Σ sₙeₙ`` folds them into the real/anchor coherence channel;
    * a **sequence** (4- or 8-component) — a general unit pure-imaginary axis;
      it is normalised to unit length, and ``e0`` (and, for a quaternion
      transform, ``e4..e7``) must be zero.

    rc125 (numpy-free): a plain ``list[float]``.
    """
    if isinstance(mu_axis, str):
        if mu_axis in _MU_AXES:
            return _as8(_MU_AXES[mu_axis])
        if mu_axis == "diagonal":
            hi = 8 if octonion else 4
            inv = 1.0 / float(_rsqrt(float(hi - 1)))
            return [0.0] + [inv if 1 <= i < hi else 0.0 for i in range(1, 8)]
        raise ValueError(
            f"mu_axis must be one of {sorted(_MU_AXES) + ['diagonal']}, or a unit "
            f"pure-imaginary vector; got {mu_axis!r}"
        )
    # General axis: a 4- or 8-component pure-imaginary vector.
    v = _as8(mu_axis)
    if v[0] != 0.0:
        raise ValueError("a general mu_axis must be pure-imaginary (e0 == 0)")
    if not octonion and any(v[i] != 0.0 for i in range(4, 8)):
        raise ValueError(
            "a quaternion mu_axis must lie in ℍ (components e4..e7 == 0); use "
            "octonion_dft / a quaternion-scope coupler for an octonion axis"
        )
    norm = float(_rsqrt(float(sum(c * c for c in v[1:]))))
    if norm == 0.0:
        raise ValueError("mu_axis must be a non-zero pure-imaginary vector")
    inv = 1.0 / norm
    return [x * inv for x in v]


def _pack_streams(streams) -> "tuple":
    """Coerce a coupler input to an (8-vector carrier, octonion?) pair.

    A length-≤3 (resp. 4–7) real sequence is **packed as streams** into the
    pure-imaginary slots of a quaternion (resp. octonion) carrier (real/anchor
    = 0); a length-4 or length-8 sequence is taken as a **literal** quaternion
    / octonion carrier (so a bound result round-trips back through the coupler).
    rc125 (numpy-free): a plain ``list[float]``.
    """
    a = [float(x) for x in streams]
    n = len(a)
    if n == 4:
        return _as8(a), False
    if n == 8:
        return list(a), True
    if 1 <= n <= 3:
        q = [0.0] * 8
        q[1:1 + n] = a
        return q, False
    if 5 <= n <= 7:
        q = [0.0] * 8
        q[1:1 + n] = a
        return q, True
    raise ValueError(
        "streams must be ≤7 real coefficients (packed into the imaginary slots) "
        "or a 4-/8-component literal quaternion/octonion carrier; got length "
        f"{n}"
    )


# ────────────────────────────────────────────────────────────────────────
# The GRADUATED octonion DFT (0.9.0rc111; #1234 Item 1c, re-raise of
# #863) — first-class over the qm.octonion foundation (the 8×8 L_a/R_a
# operators + the rc111 ``octonion_twiddle``), with the whole-transform
# C peer ``srmech_octonion_dft`` (ALL THREE forms) and a byte-exact
# composed fallback. The rc31 composite ``_dft_core`` retired here.
# ────────────────────────────────────────────────────────────────────────

#: The octonion carrier dimension (𝕆).
_ODIM = 8

#: The native uint32 length bound (the srmech_octonion_twiddle contract).
_ODFT_N_MAX = 2 ** 32

#: The srmech_octonion_dft wire codes (form / bracketing enums).
_ODFT_FORM_CODE = {"left": 0, "right": 1, "two_sided": 2}
_ODFT_BRACKETING_CODE = {"left_associated": 0, "right_associated": 1}


def _odft_matvec8(rows: List[List[float]], v: Sequence[float]) -> List[float]:
    """The 8×8 operator matvec with the row-dot accumulated LEFT-TO-RIGHT in a
    scalar ``t`` — the exact float-op order of the C peer's
    ``srmech_oct__matvec8`` (the byte-exact parity contract, not a
    tolerance)."""
    out = [0.0] * _ODIM
    for i in range(_ODIM):
        t = 0.0
        for c in range(_ODIM):
            t += rows[i][c] * v[c]
        out[i] = t
    return out


def _odft_native_ready() -> bool:
    """True iff the native lib is loaded AND exports ``srmech_octonion_dft``
    (hasattr-guarded for stale ABI-3 libs; numpy-free)."""
    return bool(
        _native.HAS_NATIVE and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_octonion_dft")
    )


def _try_native_odft(xs: List[List[float]], form: str, bracketing: str,
                     inverse: bool, mu_hat: List[float],
                     mu_r_hat: List[float]):
    """Dispatch the WHOLE transform to the C peer ``srmech_octonion_dft``
    (one ctypes call; μ̂/μ̂_r already unit) — or ``None`` to signal the
    composed fallback. Byte-exact with :func:`_odft_composed` (tested)."""
    n_pts = len(xs)
    if not _odft_native_ready() or n_pts >= _ODFT_N_MAX:
        return None
    In = ctypes.c_double * (n_pts * _ODIM)
    Mu = ctypes.c_double * _ODIM
    c_x = In(*(c for v in xs for c in v))
    c_mu = Mu(*(float(c) for c in mu_hat))
    c_mu_r = Mu(*(float(c) for c in mu_r_hat))
    c_out = In()
    rc = _native.LIB.srmech_octonion_dft(
        ctypes.cast(c_x, _C_DBLP), ctypes.c_uint32(n_pts),
        ctypes.c_int32(_ODFT_FORM_CODE[form]),
        ctypes.c_int32(_ODFT_BRACKETING_CODE[bracketing]),
        ctypes.c_int32(1 if inverse else 0),
        ctypes.cast(c_mu, _C_DBLP), ctypes.cast(c_mu_r, _C_DBLP),
        ctypes.c_size_t(_ODIM), ctypes.cast(c_out, _C_DBLP),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [[float(c_out[i * _ODIM + c]) for c in range(_ODIM)]
            for i in range(n_pts)]


def _odft_composed(xs: List[List[float]], form: str, bracketing: str,
                   inverse: bool, mu_hat: List[float],
                   mu_r_hat: List[float]) -> List[List[float]]:
    """The composed ODFT path over the qm.octonion foundation — the rc111
    ``_twiddle_resolved`` core (via the resolved-μ̂ one-resolution parity
    contract) + the 8×8 ``octonion_left_mult``/``octonion_right_mult``
    operator matvec.

    Float-op order MIRRORS the C peer exactly (twiddle → operator matrix →
    row-dot left-to-right → per-summand term → accumulate over m → one final
    scale; the two-sided form applies the DECLARED bracketing order), so the
    two paths are byte-exact — the parity contract, not a tolerance."""
    from srmech.qm.octonion import (
        _twiddle_resolved,
        octonion_left_mult,
        octonion_right_mult,
    )
    n_pts = len(xs)
    sigma = 1 if inverse else -1
    scale = (1.0 / float(n_pts)) if inverse else 1.0
    two_sided = form == "two_sided"
    left = form == "left"
    left_assoc = bracketing == "left_associated"
    out: List[List[float]] = []
    for k in range(n_pts):
        acc = [0.0] * _ODIM
        for m in range(n_pts):
            w = _twiddle_resolved(k, m, n_pts, sigma, mu_hat)
            if two_sided:
                # The DECLARED bracketing (the attested field, F378): the
                # 3-factor product W_l · x · W_r needs an association order.
                w_r = _twiddle_resolved(k, m, n_pts, sigma, mu_r_hat)
                if left_assoc:                     # (W_l · x) · W_r
                    inner = _odft_matvec8(octonion_left_mult(w).tolist(),
                                          xs[m])
                    term = _odft_matvec8(octonion_right_mult(w_r).tolist(),
                                         inner)
                else:                              # W_l · (x · W_r)
                    inner = _odft_matvec8(octonion_right_mult(w_r).tolist(),
                                          xs[m])
                    term = _odft_matvec8(octonion_left_mult(w).tolist(),
                                         inner)
            elif left:                             # W · x  (one product)
                term = _odft_matvec8(octonion_left_mult(w).tolist(), xs[m])
            else:                                  # x · W  (one product)
                term = _odft_matvec8(octonion_right_mult(w).tolist(), xs[m])
            for i in range(_ODIM):
                acc[i] += term[i]
        out.append([acc[i] * scale for i in range(_ODIM)])
    return out


# ────────────────────────────────────────────────────────────────────────
# The GRADUATED quaternion DFT (0.9.0rc110; #1234 Item 1b, re-raise of
# #863) — first-class over the rc109 qm.quaternion foundation (the 4×4
# L_q/R_q operators + the exp(μθ) twiddle), with the whole-transform C
# peer ``srmech_quaternion_dft`` and a byte-exact composed fallback.
# ────────────────────────────────────────────────────────────────────────

#: The quaternion carrier dimension (ℍ).
_QDIM = 4

#: ctypes double-pointer alias for the native QDFT marshalling (numpy-free).
_C_DBLP = ctypes.POINTER(ctypes.c_double)

#: The native uint32 length bound (the srmech_quaternion_twiddle contract).
_QDFT_N_MAX = 2 ** 32


def _as_quat4(v) -> List[float]:
    """Coerce one QDFT sample to a plain 4-list (numpy-free).

    Accepts a 4-component quaternion or the rc31 octonion-embedded 8-vector
    form with ``e4..e7 == 0`` (a nonzero tail would silently leak ℍ, so it
    raises — the same guard the composite tier enforced)."""
    a = [float(c) for c in v]
    n = len(a)
    if n == 4:
        return a
    if n == 8:
        # presence test (any nonzero tail) — no magnitude / no abs() needed.
        if any(a[i] != 0.0 for i in range(4, 8)):
            raise ValueError(
                "quaternion_dft requires quaternion samples (components "
                "e4..e7 must be zero); use octonion_dft for full octonions"
            )
        return a[:4]
    raise ValueError(
        f"hypercomplex sample must have 4 (quaternion) or 8 (octonion) "
        f"components; got {n}"
    )


def _resolve_mu4_qdft(mu_axis) -> List[float]:
    """Resolve the QDFT axis to a UNIT pure-imaginary 4-list ``μ̂`` — ONCE per
    public call, so the native and composed paths consume the identical floats
    (the rc109 one-resolution parity contract).

    Keeps the full rc31/rc1 axis contract: named ``'i'``/``'j'``/``'k'``/
    ``'ijk'``/``'diagonal'`` (for ℍ, ``'diagonal'`` IS ``'ijk'`` — the
    equal-weight ``(i+j+k)/√3`` coupling axis, F436), a 4-sequence
    pure-imaginary vector (normalised via the Class-N sqrt cascade), or an
    ℍ-valued 8-sequence (``e4..e7 == 0``)."""
    from srmech.qm import quaternion as _quat
    if isinstance(mu_axis, str):
        name = "ijk" if mu_axis == "diagonal" else mu_axis
        if name in _quat._MU_AXES:
            return list(_quat._MU_AXES[name])
        raise ValueError(
            f"mu_axis must be one of {sorted(_MU_AXES) + ['diagonal']}, or a "
            f"unit pure-imaginary vector; got {mu_axis!r}"
        )
    v = [float(c) for c in mu_axis]
    if len(v) == 8:
        if any(v[i] != 0.0 for i in range(4, 8)):
            raise ValueError(
                "a quaternion mu_axis must lie in ℍ (components e4..e7 == 0); "
                "use octonion_dft / a quaternion-scope coupler for an "
                "octonion axis"
            )
        v = v[:4]
    if len(v) != 4:
        raise ValueError(
            f"a general quaternion mu_axis must have 4 (or ℍ-valued 8) "
            f"components; got {len(v)}"
        )
    if v[0] != 0.0:
        raise ValueError("a general mu_axis must be pure-imaginary (e0 == 0)")
    if v[1] == 0.0 and v[2] == 0.0 and v[3] == 0.0:
        raise ValueError("mu_axis must be a non-zero pure-imaginary vector")
    return _quat._resolve_mu4(v, "quaternion_dft")


def _qdft_native_ready() -> bool:
    """True iff the native lib is loaded AND exports ``srmech_quaternion_dft``
    (hasattr-guarded for stale ABI-3 libs; numpy-free)."""
    return bool(
        _native.HAS_NATIVE and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_quaternion_dft")
    )


def _try_native_qdft(xs: List[List[float]], left: bool, inverse: bool,
                     mu_hat: List[float]):
    """Dispatch the WHOLE transform to the C peer ``srmech_quaternion_dft``
    (one ctypes call; μ̂ already unit) — or ``None`` to signal the composed
    fallback. Byte-exact with :func:`_qdft_composed` (tested)."""
    n_pts = len(xs)
    if not _qdft_native_ready() or n_pts >= _QDFT_N_MAX:
        return None
    In = ctypes.c_double * (n_pts * _QDIM)
    Mu = ctypes.c_double * _QDIM
    c_x = In(*(c for v in xs for c in v))
    c_mu = Mu(*(float(c) for c in mu_hat))
    c_out = In()
    rc = _native.LIB.srmech_quaternion_dft(
        ctypes.cast(c_x, _C_DBLP), ctypes.c_uint32(n_pts),
        ctypes.c_int32(1 if left else 0), ctypes.c_int32(1 if inverse else 0),
        ctypes.cast(c_mu, _C_DBLP), ctypes.c_size_t(_QDIM),
        ctypes.cast(c_out, _C_DBLP),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [[float(c_out[i * _QDIM + c]) for c in range(_QDIM)]
            for i in range(n_pts)]


def _qdft_composed(xs: List[List[float]], left: bool, inverse: bool,
                   mu_hat: List[float]) -> List[List[float]]:
    """The composed QDFT path over the rc109 qm.quaternion foundation —
    ``quaternion_twiddle`` (via the resolved-μ̂ core) + the 4×4
    ``quaternion_left_mult``/``quaternion_right_mult`` operator matvec.

    Float-op order MIRRORS the C peer exactly (twiddle → operator matrix →
    row-dot left-to-right → accumulate over n → one final scale), so the two
    paths are byte-exact — the parity contract, not a tolerance."""
    from srmech.qm.quaternion import (
        _twiddle_resolved,
        quaternion_left_mult,
        quaternion_right_mult,
    )
    n_pts = len(xs)
    sigma = 1 if inverse else -1
    scale = (1.0 / float(n_pts)) if inverse else 1.0
    out: List[List[float]] = []
    for k in range(n_pts):
        acc = [0.0, 0.0, 0.0, 0.0]
        for m in range(n_pts):
            w = _twiddle_resolved(k, m, n_pts, sigma, mu_hat)
            op = quaternion_left_mult(w) if left else quaternion_right_mult(w)
            rows = op.tolist()
            xm = xs[m]
            for i in range(_QDIM):
                t = 0.0
                for c in range(_QDIM):
                    t += rows[i][c] * xm[c]
                acc[i] += t
        out.append([acc[i] * scale for i in range(_QDIM)])
    return out


def quaternion_dft(
    x: Sequence,
    *,
    form: str = "left",
    mu_axis: str = "i",
    inverse: bool = False,
) -> List[List[float]]:
    """Quaternion discrete Fourier transform (QDFT) — the native transform for
    a Klein-4 object, GRADUATED first-class (0.9.0rc110; #1234 Item 1b / #863).

    A Klein-4 object has TWO ``Z₂`` chirality axes (Klein-4 = ``Q₈/{±1} ≅
    Z₂×Z₂``, F380 / the in-repo R21 proof); the complex FFT first projects it
    to ``ℂ``, collapsing one axis (the flat shadow). The QDFT's ``ℍ``
    coefficient algebra MATCHES the object's value algebra, so BOTH axes
    survive the round-trip.

    **THE CONVENTION (the in-repo SSOT — rc109 ``qm.quaternion`` + R21).**
    With ``W(θ) = exp(μθ) = cos θ·1 + sin θ·μ̂`` (``μ̂`` a unit pure imaginary,
    ``μ̂² = −1``) and the FORWARD sign ``σ = −1``:

        left  form:  X[k] = Σ_{n=0}^{N−1}  W(σ·2πkn/N) · x[n]   (twiddle LEFT)
        right form:  X[k] = Σ_{n=0}^{N−1}  x[n] · W(σ·2πkn/N)   (twiddle RIGHT)

    The INVERSE flips the sign (``σ = +1``) and scales by ``1/N``, keeping the
    twiddle on the SAME side — each form is the exact inverse of its own
    inverse-transform (the twiddle lives in the commutative ``ℝ[μ̂] ≅ ℂ``
    subalgebra, so ``Σ_k W(μ·2πk(n−n′)/N) = N·δ``). The two forms are
    GENUINELY different transforms (``ℍ`` non-commutative); they coincide
    exactly when every sample lies in ``ℝ[μ̂]`` (the classic degeneracy).
    Parseval (this convention, forward unscaled): ``Σ_k ‖X[k]‖² =
    N·Σ_n ‖x[n]‖²`` for both one-sided forms. The left form is a RIGHT
    ℍ-module map (``QDFT_left(x·q) = QDFT_left(x)·q``) and ℝ-linear; the
    right form is the mirror (a LEFT ℍ-module map).

    **API SPLIT (F1000→F1001; #1234 Item 1).** This FULL transform is the
    SPREAD-SPECTRUM ENCODING / analysis surface — it computes the whole
    length-``N`` spectrum. The READ path is deliberately a SEPARATE
    lightweight op (``phase_coherent_peak`` — the next rc, 1-d): do NOT run
    the full QDFT just to read one phase-coherent peak back out.

    Composes the rc109 foundation: ``qm.quaternion.quaternion_twiddle``
    (Class I ∘ N ∘ C — exact ``kn mod N``, π as the ``4·atan(1)`` cascade,
    Q61 trig) + ``quaternion_left_mult`` / ``quaternion_right_mult`` (Class M).
    Dispatches the whole transform to the same-rc C peer
    ``srmech_quaternion_dft`` (O(N²) exact reference; an FFT factorisation is
    honestly future work) — byte-exact composed fallback otherwise.

    Parameters
    ----------
    x : sequence of quaternions, or a real ``(N, 4)`` ``Mat``
        Each sample is a 4-component ``[q0, q1, q2, q3]`` (or an 8-component
        octonion with ``e4..e7 == 0``). ``N = len(x)`` (any N ≥ 0, power of
        two NOT required).
    form : {"left", "right"}
        Which side the twiddle multiplies on (see THE CONVENTION above).
    mu_axis : {"i", "j", "k", "ijk", "diagonal"} or unit pure-imaginary vector
        The transform axis ``μ`` (``μ²=−1``). ``'diagonal'`` (= ``(i+j+k)/√3``
        here) **couples** all three axes into the real/anchor channel (F436); a
        single named axis only **carries** them. A general unit pure-imaginary
        quaternion vector is also accepted (#908).
    inverse : bool
        Inverse QDFT (``σ = +1`` twiddle + ``1/N`` scale, same side).
        ``inverse(forward(x))`` recovers ``x`` exactly (to float round-off),
        including **all four** components — i.e. both ``Z₂`` axes.

    Returns
    -------
    list[list[float]]
        ``N`` quaternions (4-component lists).

    Class home: **M** (Clifford/HDC quaternion multiply) ∘ **C** (the
    orientation of the twiddle's ``±μ`` phase) ∘ **N** (the rational twiddle
    angle ``kn/N``) ∘ **I** (the cyclic ``kn mod N`` reduction). Sangwine &
    Ell (2012), arXiv:1001.4379 (PDF-verified: the matrix-exponential
    ``exp(μθ)`` Euler-form hypercomplex DFT framework + the
    exponential-placement / one-sided-vs-two-sided distinction).
    """
    if form not in _FORMS:
        raise ValueError(f"form must be one of {_FORMS}; got {form!r}")
    if isinstance(x, _Mat):
        if x.is_complex:
            raise ValueError(
                "quaternion_dft takes REAL quaternion components; got a "
                "complex Mat"
            )
        x = x.tolist()
    xs = [_as_quat4(v) for v in x]
    mu_hat = _resolve_mu4_qdft(mu_axis)
    if not xs:
        return []
    left = form == "left"
    native = _try_native_qdft(xs, left, bool(inverse), mu_hat)
    if native is not None:
        return native
    return _qdft_composed(xs, left, bool(inverse), mu_hat)


def octonion_dft(
    x: Sequence,
    *,
    form: str = "left",
    mu_axis: str = "i",
    bracketing: str = "left_associated",
    two_sided_right_axis: str = "j",
    inverse: bool = False,
) -> List[List[float]]:
    """Octonion discrete Fourier transform (ODFT) — the (8:7) rung above the
    QDFT, GRADUATED first-class (0.9.0rc111; #1234 Item 1c / #863).

    Because ``𝕆`` is **NON-ASSOCIATIVE** (F378), "the ODFT" is NOT unique
    until its **bracketing convention is DECLARED** — a different bracketing
    is a different (also-declarable) transform. The convention here is an
    explicit **ATTESTED field** (this docstring + the ``octonion_dft.toml``
    ``[cascade.bracketing]`` attestation block), never a silent assumption.

    **THE DECLARED CONVENTION (the attested field, verbatim in the TOML):**
    *per-summand-single-product; the inverse applies the conjugate twiddle
    (σ flip) on the SAME declared side; the two-sided form's 3-factor
    association order is the explicit ``bracketing`` parameter.* With
    ``W(θ) = exp(μθ)`` and the FORWARD sign ``σ = −1``:

        left      form:  X[k] = Σ_m  W(σ·2πkm/N) · x[m]          (ONE product)
        right     form:  X[k] = Σ_m  x[m] · W(σ·2πkm/N)          (ONE product)
        two_sided form:  X[k] = Σ_m  bracket(W_l, x[m], W_r)     (THREE factors)

    with ``bracket`` = ``(W_l·x)·W_r`` (``bracketing="left_associated"``) or
    ``W_l·(x·W_r)`` (``"right_associated"``). The INVERSE (one-sided forms)
    flips ``σ`` to +1 and scales by ``1/N``, twiddle on the SAME side.

    **WHERE NON-ASSOCIATIVITY ACTUALLY BITES (the alternativity finding —
    verified empirically, rc111 tests).** ``𝕆`` is ALTERNATIVE (``a(ax) =
    (aa)x``, ``(xa)a = x(aa)``), and by **Artin's theorem** every subalgebra
    generated by TWO elements is associative. Each one-sided summand is ONE
    product ``W·x[m]`` (no association ambiguity), and the whole one-sided
    round-trip composes twiddles on a SINGLE axis ``μ`` against one sample —
    everything lives in the two-generator subalgebra ``⟨μ, x[m]⟩``, so
    ``W̄·(W·x) = (W̄·W)·x = x`` holds EXACTLY and the round-trip is exact
    (same guarantee ℍ gives the QDFT, despite 𝕆's non-associativity).
    Non-associativity bites only at **≥ 3 independent generators**:

    * the TWO-SIDED form with distinct axes (``⟨μ_l, μ_r, x⟩``): the two
      bracketings measurably DIFFER — the ``bracketing`` field is
      load-bearing, not decorative (tested: a deliberate re-bracketing
      changes the spectrum);
    * a twiddle associated through a PRODUCT of two samples
      (``W·(x·y) ≠ (W·x)·y`` — ``⟨μ, x, y⟩``; tested);
    * with ``μ_l = μ_r`` the two-sided bracketings COINCIDE (mathematically
      — ``⟨μ, x⟩`` again; float round-off differs, tested at tolerance):
      the Artin boundary demonstrated from both sides.

    The two-sided form is FORWARD-ONLY (its inverse is open under
    non-associativity → ``inverse=True`` raises).

    Composes the qm.octonion foundation: ``octonion_twiddle`` (rc111 —
    Class I ∘ N ∘ C: exact ``km mod N``, π as the ``4·atan(1)`` cascade,
    Q61 trig) + ``octonion_left_mult`` / ``octonion_right_mult`` (Class M).
    Dispatches the whole transform (ALL THREE forms) to the same-rc C peer
    ``srmech_octonion_dft`` (O(N²) exact reference; an FFT factorisation is
    honestly future work) — byte-exact composed fallback otherwise.

    Parameters
    ----------
    x : sequence of octonions, or a real ``(N, 8)`` ``Mat``
        Each sample is an 8-component ``[e0..e7]`` (a 4-component quaternion
        is accepted and zero-extended into ``ℍ ⊂ 𝕆``). ``N = len(x)`` (any
        N ≥ 0; power of two NOT required).
    form : {"left", "right", "two_sided"}
        ``W·x`` / ``x·W`` / ``W_l·x·W_r``. The two-sided form is where
        octonion non-associativity bites (see above).
    mu_axis : named axis or unit pure-imaginary vector
        The left (or single) transform axis ``μ`` (``μ²=−1``). Named:
        ``'i'``/``'j'``/``'k'`` (= ``'e1'``/``'e2'``/``'e3'``),
        ``'e4'``..``'e7'`` (the extra octonion axes), ``'ijk'``
        (``(e1+e2+e3)/√3``), ``'diagonal'`` (``(Σ_{a=1..7} e_a)/√7`` —
        **couples** all seven imaginary streams into the real/anchor
        coherence channel, F436). A general unit pure-imaginary 4-/8-vector
        is also accepted (#908).
    bracketing : {"left_associated", "right_associated"}
        The DECLARED association order for ``form="two_sided"``:
        ``(W_l·x)·W_r`` vs ``W_l·(x·W_r)`` — these DIFFER for octonions
        (F378). Recorded (trivially) for the one-sided forms, whose
        per-summand single product has no association ambiguity.
    two_sided_right_axis : named axis or unit vector
        The right twiddle axis ``μ_r`` for the two-sided form (same
        resolution as ``mu_axis``).
    inverse : bool
        Inverse ODFT (``σ = +1`` twiddle + ``1/N`` scale, same side).
        One-sided forms round-trip exactly (the alternativity finding);
        the two-sided form is forward-only (raises).

    Returns
    -------
    list[list[float]]
        ``N`` octonions (8-component lists).

    Class home: **M** (octonion multiply) ∘ **C** (twiddle orientation) ∘
    **N** (rational angle) ∘ **I** (the cyclic ``km mod N`` reduction).
    Błaszczyk (2019), arXiv:1905.12631 (PDF re-verified at rc111); origin
    Hahn & Snopek (2011), Bull. Polish Acad. Sci. 59(2):167–181. The
    bracketing/alternativity statements are the IN-REPO SSOT (the
    qm.octonion attested table + the rc111 empirical verification), not an
    external attribution.
    """
    if form not in _OCTONION_FORMS:
        raise ValueError(f"form must be one of {_OCTONION_FORMS}; got {form!r}")
    if bracketing not in _BRACKETINGS:
        raise ValueError(f"bracketing must be one of {_BRACKETINGS}; got {bracketing!r}")
    if form == "two_sided" and inverse:
        raise NotImplementedError(
            "two-sided octonion_dft inverse is open under non-associativity "
            "(F378); only the one-sided forms round-trip"
        )
    from srmech.qm import octonion as _oct
    if isinstance(x, _Mat):
        if x.is_complex:
            raise ValueError(
                "octonion_dft takes REAL octonion components; got a "
                "complex Mat"
            )
        x = x.tolist()
    xs = [_as8(v) for v in x]
    # One-resolution parity contract: μ̂ (and μ̂_r for the two-sided form) are
    # resolved exactly ONCE so the native and composed paths consume the
    # identical floats. The one-sided forms pass μ̂ twice (μ_r ignored).
    mu_hat = _oct._resolve_mu8(mu_axis, "octonion_dft")
    if form == "two_sided":
        mu_r_hat = _oct._resolve_mu8(two_sided_right_axis, "octonion_dft")
    else:
        mu_r_hat = mu_hat
    if not xs:
        return []
    native = _try_native_odft(xs, form, bracketing, bool(inverse),
                              mu_hat, mu_r_hat)
    if native is not None:
        return native
    return _odft_composed(xs, form, bracketing, bool(inverse),
                          mu_hat, mu_r_hat)


def hypercomplex_couple(
    streams: Sequence,
    *,
    axis="diagonal",
    theta: float = _PI / 2.0,
    sigma: int = 1,
    form: str = "left",
    inverse: bool = False,
) -> List[float]:
    """Bidirectional ``(σ, θ, μ)`` hypercomplex coupler — bind ≥3 streams into
    one quaternion/octonion + a joint coherence channel, and unbind losslessly.

    This is the first-class coupler asked for in **#908 / §29** (findings
    **F436** + **F437**). Where ``quaternion_dft`` / ``octonion_dft`` *carry* N
    streams along named single axes, this **couples** them: it packs ``streams``
    into the pure-imaginary slots of a carrier ``q`` and applies the twiddle
    ``T = exp(σ_eff · μ · θ)`` (``σ_eff = σ·(−1 if inverse else +1)``):

    * **Bind** (``sigma=+1``) with a **diagonal** ``μ`` folds the streams — the
      result's **real/anchor** channel becomes a joint *coherence detector*
      (F436: coherent streams add, incoherent cancel; ``μ·Σsₙeₙ`` collects
      ``−Σsₙ``). The imaginaries carry the pairwise relations.
    * **Unbind** (``sigma=-1``, or ``inverse=True``) is the **conjugate**
      twiddle ``exp(−μθ)``; ``couple(couple(q, σ=+1), σ=-1)`` recovers ``q``
      exactly — the division-algebra identity ``T̄·(T·q)=‖T‖²·q`` (F437). This
      is **guaranteed reversible only up to 𝕆** (the Hurwitz boundary; the
      sedenion's zero divisors break it) → lossless for **≤ 7 streams**.

    ``form="left"``/``"right"`` and ``inverse`` are special discrete points of
    the same continuous ``(σ, θ, μ)`` family — exactly ``the_one``'s ``𝕊(σ,θ)``
    (F420) **plus the axis μ**. This exposes the axis + sign of the existing
    ``exp(μθ)`` twiddle; **no new algebra** (composite over ``qm.octonion``).

    Parameters
    ----------
    streams : sequence
        ≤3 real coefficients → packed into a quaternion ``(0, s₀, s₁, s₂)``;
        4–7 → packed into an octonion ``(0, s₀, …)``; a length-4 / length-8
        sequence is taken as a **literal** quaternion / octonion carrier (so a
        bound result feeds straight back in to unbind).
    axis : str or sequence
        The coupling axis ``μ`` (``'diagonal'`` default; also ``'i'``/``'j'``/
        ``'k'``/``'ijk'`` or a unit pure-imaginary vector). See
        :func:`_resolve_mu`. A single named axis does **not** couple across
        axes (it only carries) — use ``'diagonal'`` for true coupling (F436).
    theta : float
        The continuous coupling phase (default ``π/2`` — the F436 quarter-turn
        fold where the diagonal axis sends the streams into the anchor).
    sigma : {+1, -1}
        Conjugation / chirality: ``+1`` binds (forward fold), ``−1`` unbinds
        (the conjugate twiddle; F437).
    form : {"left", "right"}
        ``T·q`` or ``q·T`` (``ℍ``/``𝕆`` are non-commutative).
    inverse : bool
        Flips the effective sign (equivalently toggles ``sigma``); provided for
        symmetry with the DFT surface.

    Returns
    -------
    list[float]
        The coupled value — a 4-component quaternion (≤3 streams / literal
        quaternion) or 8-component octonion (otherwise).

    Class home: **M** (octonion multiply) ∘ **C** (the ``σ``/conjugation
    orientation) ∘ **N** (the rational phase ``θ``). F436 / F437; §29.
    """
    if sigma not in (1, -1, 1.0, -1.0):
        raise ValueError(f"sigma must be +1 or -1; got {sigma!r}")
    if form not in _FORMS:
        raise ValueError(f"form must be one of {_FORMS}; got {form!r}")

    q, octonion = _pack_streams(streams)
    mu = _resolve_mu(axis, octonion=octonion)
    eff = float(sigma) * (-1.0 if inverse else 1.0) * float(theta)
    # rc16 (C-host parity): the float `Mat` octonion-matvec is replaced by the
    # EXACT-Q61 octonion couple `_couple_q61` (cd_basis_product structure
    # constants + Q61 fxmul) — byte-exact reproducible in C
    # (`srmech_hypercomplex_couple_q61`), the stay-rational NORTH STAR with no
    # float boundary except this final projection.
    out_q61 = _couple_q61([_to_q61(v) for v in q], [_to_q61(v) for v in mu],
                          eff, form=form)
    out = [v / float(_Q61_ONE) for v in out_q61]
    return list(out) if octonion else out[:4]
