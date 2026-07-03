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

**GRADUATION SPLIT (0.9.0rc110; #1234 Item 1b, re-raise of #863):**

- :func:`quaternion_dft` is **GRADUATED** — a first-class op over the rc109
  ``srmech.qm.quaternion`` foundation (the 4×4 ``L_q``/``R_q`` operators +
  ``quaternion_twiddle``, no longer the sliced 8×8 octonion embedding) with
  the whole-transform C peer ``srmech_quaternion_dft`` (byte-exact composed
  fallback).
- :func:`octonion_dft` / :func:`hypercomplex_couple` remain the composite
  tier over the ``srmech.qm.octonion`` left/right-multiply atoms; the ODFT's
  own graduation is a separate later voxel.

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


def _twiddle8(theta: float, mu: Sequence[float]) -> List[float]:
    """``exp(μθ) = cos θ·1 + sin θ·μ`` as an 8-vector (μ a unit pure-imaginary
    octonion). All seven imaginary components are carried — a quaternion axis
    has ``e4..e7 == 0`` so the result is unchanged from the ℍ-only form, but a
    general / diagonal octonion ``μ`` (e.g. ``(Σeₙ)/√7``) is now honoured.
    rc125 (numpy-free): a plain ``list[float]``."""
    c = _rcos(theta)
    s = _rsin(theta)
    return [c] + [s * mu[i] for i in range(1, 8)]


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


def _matvec8(op, v: Sequence[float]) -> List[float]:
    """The octonion-rep matvec ``op · v`` — ``op`` an ``8×8`` :class:`Mat`
    (``octonion_left_mult`` / ``octonion_right_mult``), ``v`` an 8-vector list.
    rc125 (numpy-free): a pure-Python matvec over the ``Mat`` rows (never numpy
    ``@`` / ``dense_matvec_real``; the rc117 single_particle pattern)."""
    rows = op.tolist()
    return [sum(rows[i][j] * v[j] for j in range(8)) for i in range(8)]


def _dft_core(x, *, form, mu_axis, inverse, two_sided_right, bracketing):
    """The ODFT engine. Composes the qm.octonion left/right-mult atoms.

    X[k] = scale · Σ_n  T( W(σ·2πkn/N) ) · x[n]

    where ``W`` is the twiddle, ``σ = +1`` for the inverse (else −1), ``scale``
    = 1/N for the inverse (else 1), and ``T`` is left- or right-multiplication
    by the twiddle (``octonion_left_mult`` / ``octonion_right_mult``) — the
    non-commutative choice that distinguishes the left/right forms.

    rc125 (numpy-free): the operators are the :class:`Mat` ``octonion_*_mult``
    now returns; the matvec is :func:`_matvec8` (pure Python); the accumulator
    is a ``list[float]``. rc110: the QUATERNION path graduated out of this
    engine onto the rc109 qm.quaternion foundation (:func:`_qdft_composed` +
    the ``srmech_quaternion_dft`` C peer); this core now serves the ODFT only.
    """
    from srmech.qm.octonion import octonion_left_mult, octonion_right_mult

    mu = _resolve_mu(mu_axis, octonion=True)
    # Resolve the two-sided right axis once (defaults to the left axis).
    mu_r = _resolve_mu(two_sided_right or mu_axis, octonion=True)

    xs = [_as8(v) for v in x]
    n_pts = len(xs)
    if n_pts == 0:
        return []

    sigma = 1.0 if inverse else -1.0
    scale = (1.0 / n_pts) if inverse else 1.0
    two_pi = 2.0 * _PI

    mult_left = form == "left"
    out: List = []
    for k in range(n_pts):
        acc = [0.0] * 8
        for n in range(n_pts):
            theta = sigma * two_pi * k * n / n_pts
            w = _twiddle8(theta, mu)
            if form == "two_sided":
                # Octonion two-sided: W_l · x · W_r — the bracketing of the
                # 3-factor product is meaningful (𝕆 is NON-associative, F378).
                wl = octonion_left_mult(w)
                w_r = _twiddle8(theta, mu_r)
                if bracketing == "left_associated":
                    # (W_l · x) · W_r
                    inner = _matvec8(wl, xs[n])
                    term = _matvec8(octonion_right_mult(w_r), inner)
                else:
                    # W_l · (x · W_r)
                    inner = _matvec8(octonion_right_mult(w_r), xs[n])
                    term = _matvec8(wl, inner)
            elif mult_left:
                term = _matvec8(octonion_left_mult(w), xs[n])   # W·x (left)
            else:
                term = _matvec8(octonion_right_mult(w), xs[n])  # x·W (right)
            acc = [acc[i] + term[i] for i in range(8)]
        acc = [a * scale for a in acc]
        out.append(list(acc))
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
    """Octonion discrete Fourier transform (ODFT) — composite over qm.octonion.

    Carries the F378 **non-associativity** as an *explicit declared field*: the
    ODFT is **not unique** for the two-sided form, so the bracketing/association
    convention must be stated, not assumed.

    Parameters
    ----------
    x : sequence of octonions
        Each sample is an 8-component ``[e0..e7]``. ``N = len(x)``.
    form : {"left", "right", "two_sided"}
        ``W·x`` / ``x·W`` / ``W_l·x·W_r``. The two-sided form is where octonion
        non-associativity bites.
    mu_axis : {"i", "j", "k", "ijk", "diagonal"} or unit pure-imaginary vector
        The left (or single) transform axis ``μ`` (``μ²=−1``). ``'diagonal'``
        (= ``(Σ_{n=1..7} eₙ)/√7`` for octonions) **couples** all seven imaginary
        streams into the real/anchor coherence channel (F436); a single named
        axis only carries them. A general unit pure-imaginary octonion vector is
        also accepted (#908). See :func:`_resolve_mu`.
    bracketing : {"left_associated", "right_associated"}
        **Only meaningful for** ``form="two_sided"``: ``(W_l·x)·W_r`` vs
        ``W_l·(x·W_r)``. These **differ** for octonions (F378) — the field is
        the concrete crystallisation of "the ODFT must declare its association
        order". Recorded (trivially) for the one-sided forms.
    two_sided_right_axis : {"i", "j", "k", "ijk", "diagonal"} or unit vector
        The right twiddle axis ``μ_r`` for the two-sided form (same resolution
        as ``mu_axis``: named / ``'diagonal'`` / general unit pure-imaginary).
    inverse : bool
        Inverse ODFT (one-sided forms round-trip; the two-sided form is
        forward-only here — its inverse is open under non-associativity).

    Returns
    -------
    list[list[float]]
        ``N`` octonions (8-component lists).

    Class home: **M** (octonion multiply) ∘ **C** (twiddle orientation) ∘ **N**
    (rational angle). Błaszczyk (2019), arXiv:1905.12631; origin Hahn & Snopek
    (2011), Bull. Polish Acad. Sci. 59(2):167–181.
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
    return _dft_core(
        x, form=form, mu_axis=mu_axis, inverse=inverse,
        two_sided_right=two_sided_right_axis, bracketing=bracketing,
    )


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
