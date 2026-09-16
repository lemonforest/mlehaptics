"""rc474 repair P4 (`#T1188`) — the DYADIC cos/sin candidate, MEASURED.

Standalone. Implements the candidate route — evaluate the already-shipped Q61
sin/cos cores on a dyadic grid, widened from their fixed K=61 to K = P + 24 —
WITHOUT editing the package, and measures it against an INDEPENDENT ``decimal``
oracle carrying ~930 bits of working precision. Three questions decide adoption:

  1. is ``|result - true| < 2**-P`` at every P? That is the shipped CONTRACT,
     and it is an ERROR BOUND: nothing in the tree promises correct rounding or
     a bit-identical value on the ``precision=P`` path.
  2. do the two EXTRA invariants ``_g2_check`` asserts in
     ``tests/test_classn_precision_wave2_rc320.py`` still hold — error strictly
     shrinking across P in (40, 80, 160), ``den_bits[160] > 150``, and
     ``den_bits[40] < den_bits[160]``?
  3. how fast is it, against the shipped exact route and the float route?

WHY THE ARGUMENTS ARE ENTERED AS FLOATS. ``_g2_check`` calls
``FN[op](*args, precision=P)`` with float args, so the reduction receives
``float.as_integer_ratio()`` — denominator ``2**52``. Probing small rationals
like ``3/10`` would measure a case the gate never takes, which is the
wrong-instrument shape this arc keeps finding. ``tan`` is included because G2
covers it and because its candidate value is a QUOTIENT of two dyadics — the
one shape whose denominator could fall under the 150-bit floor.

No ``abs()``: every magnitude below is an explicit Class-K pin-slot branch with
a Class-C re-orientation. ⚠️ Stated precisely, because the first draft of this
line was too broad and the file contradicted itself one screen down: the
INDEPENDENT ``decimal`` oracle calls ``Decimal.copy_abs``, which is the
reference carrier's own method and not the cascade ALU this rule governs.
Read-only. NDJSON on stdout.
"""
from __future__ import annotations

import decimal
import json
import math
import time
from fractions import Fraction

import srmech
import srmech.math.rational as R
from srmech import _native as NB


def emit(**rec):
    print(json.dumps(rec, sort_keys=True), flush=True)


emit(rec="banner", version=srmech.__version__,
     HAS_NATIVE=getattr(NB, "HAS_NATIVE", None),
     NATIVE_ABI=getattr(NB, "NATIVE_ABI_VERSION", None),
     EXPECTED_ABI=getattr(NB, "EXPECTED_ABI_VERSION", None),
     f_rational=R.__file__)

GUARD = 24


def _qk_fxmul(a: int, b: int, k: int) -> int:
    neg = (a < 0) != (b < 0)
    ua = a if a >= 0 else -a                 # Class-K magnitude, never abs()
    ub = b if b >= 0 else -b
    mag = (ua * ub) >> k
    return -mag if neg else mag              # Class-C re-orientation


def _qk_cdiv(a: int, b: int) -> int:
    ua = a if a >= 0 else -a                 # Class-K magnitude
    ub = b if b >= 0 else -b
    q = ua // ub
    return -q if (a < 0) != (b < 0) else q   # Class-C re-orientation


def _terms_for(k: int) -> int:
    """Terms so the Leibniz tail is < 2**-k at |r| <= pi/4 < 785/1000."""
    return R._num_terms_for(785, 1000, k, "sin")


def _sin_core(r: int, k: int, n: int) -> int:
    r2 = _qk_fxmul(r, r, k)
    term = r
    s = r
    for i in range(1, n + 1):
        term = _qk_fxmul(term, r2, k)
        term = _qk_cdiv(term, (2 * i) * (2 * i + 1))
        s = s - term if (i & 1) else s + term
    return s


def _cos_core(r: int, k: int, n: int) -> int:
    one = 1 << k
    r2 = _qk_fxmul(r, r, k)
    term = one
    s = one
    for i in range(1, n + 1):
        term = _qk_fxmul(term, r2, k)
        term = _qk_cdiv(term, (2 * i - 1) * (2 * i))
        s = s - term if (i & 1) else s + term
    return s


def candidate(xn: int, xd: int, P: int, want: str) -> Fraction:
    K = P + GUARD
    pin0, pid0 = R._pi_exact(64)
    n = R._round_div(2 * xn * pid0, xd * pin0)     # round(x / (pi/2))
    nbits = n if n >= 0 else -n                    # Class-K magnitude
    pin, pid = R._pi_exact(K + nbits.bit_length() + 8)
    rn = xn * (2 * pid) - n * pin * xd             # r = x - n*(pi/2), exact
    rd = xd * (2 * pid)
    r_q = R._round_div(rn << K, rd)                # r onto the K-bit dyadic grid
    nt = _terms_for(K)
    octant = n % 4
    if want == "cos":
        use_cos = octant in (0, 2)
        neg = octant in (1, 2)
    else:
        use_cos = octant in (1, 3)
        neg = octant in (2, 3)
    v = _cos_core(r_q, K, nt) if use_cos else _sin_core(r_q, K, nt)
    if neg:
        v = -v                                     # Class-K flip o Class-C
    return Fraction(v, 1 << K)


def candidate_tan(xn: int, xd: int, P: int) -> Fraction:
    c = candidate(xn, xd, P, "cos")
    if c == 0:
        raise ValueError("tan undefined: cos(x) == 0")
    return candidate(xn, xd, P, "sin") / c


# ── the INDEPENDENT oracle ─────────────────────────────────────────────────
# pi to 280 digits, literal and independent of srmech (its leading digits are
# self-checked against math.pi below).
_PI_STR = (
    "3.14159265358979323846264338327950288419716939937510582097494459230781"
    "64062862089986280348253421170679821480865132823066470938446095505822317"
    "25359408128481117450284102701938521105559644622948954930381964428810975"
    "66593344612847564823378678316527120190914564856692346034861045432664821"
    "339360726024914127372458700660631558817488152092096282925409171536436")
DIGITS = 240


def _dsin(r, D):
    term = r
    s = r
    k = 1
    x2 = r * r
    while term.copy_abs() > D(2) ** (-900):
        term = -term * x2 / (D(2 * k) * D(2 * k + 1))
        s += term
        k += 1
    return s


def _dcos(r, D):
    term = D(1)
    s = D(1)
    k = 1
    x2 = r * r
    while term.copy_abs() > D(2) ** (-900):
        term = -term * x2 / (D(2 * k - 1) * D(2 * k))
        s += term
        k += 1
    return s


def oracle(xn: int, xd: int, want: str) -> Fraction:
    with decimal.localcontext(decimal.Context(prec=DIGITS + 40)):
        D = decimal.Decimal
        pi = D(_PI_STR)
        x = D(xn) / D(xd)
        n = int((x / (pi / 2)).to_integral_value(
            rounding=decimal.ROUND_HALF_EVEN))
        r = x - n * (pi / 2)
        o = n % 4
        cr, sr = _dcos(r, D), _dsin(r, D)
        c_v = (cr, -sr, -cr, sr)[o]
        s_v = (sr, cr, -sr, -cr)[o]
        if want == "tan":
            return Fraction(s_v / c_v)
        return Fraction(c_v if want == "cos" else s_v)


_pi_gap = float(_PI_STR) - math.pi
_pi_gap = _pi_gap if _pi_gap >= 0.0 else -_pi_gap      # Class-K magnitude
emit(rec="oracle_selfcheck", decimal_digits=DIGITS + 40,
     working_bits=round((DIGITS + 40) * 3.3219),
     pi_leading_matches_math_pi=(_pi_gap < 1e-14))

# the G2 grid, entered as FLOATS exactly as _g2_check enters it
G2 = {
    "cos": [0.3, 2.0, -1.2, 3.0],
    "sin": [0.3, 2.0, -1.2, 3.0],
    "tan": [0.3, 0.7, -0.5, 1.0],
}
PS = (24, 40, 53, 61, 80, 128, 160)
worst_ratio = 0.0
all_ok = True
g2_all_ok = True
for want, xs in G2.items():
    for x in xs:
        xn, xd = float(x).as_integer_ratio()
        orc = oracle(xn, xd, want)
        rows, dens = [], {}
        for P in PS:
            got = (candidate_tan(xn, xd, P) if want == "tan"
                   else candidate(xn, xd, P, want))
            e = got - orc
            e = e if e >= 0 else -e              # Class-K magnitude
            ok = e < Fraction(1, 2 ** P)
            all_ok = all_ok and ok
            rows.append((P, float(e), ok))
            dens[P] = got.denominator.bit_length()
            worst_ratio = max(worst_ratio, float(e) * (2 ** P))
        g2e = [e for (P, e, _o) in rows if P in (40, 80, 160)]
        g2d = [dens[P] for P in (40, 80, 160)]
        inv = ((g2e[0] > g2e[1] > g2e[2]), g2d[2] > 150, g2d[0] < g2d[2])
        g2_all_ok = g2_all_ok and all(inv)
        emit(rec="contract", op=want, x=repr(x),
             within_bound_all_P=all(o for (_P, _e, o) in rows),
             errs=[(P, "%.3e" % e) for (P, e, _o) in rows],
             den_bits=[(P, dens[P]) for P in PS],
             g2_err_strictly_shrinks=inv[0],
             g2_den160_gt_150=inv[1],
             g2_den40_lt_den160=inv[2])

emit(rec="verdict", every_row_within_2powminusP=all_ok,
     g2_extra_invariants_hold=g2_all_ok,
     worst_err_over_bound=worst_ratio,
     margin_bits_at_worst=(None if worst_ratio == 0
                           else round(-math.log2(worst_ratio), 2)))

# L6: the exact values at zero must stay exact
emit(rec="L6", cos0=str(candidate(0, 1, 61, "cos")),
     sin0=str(candidate(0, 1, 61, "sin")))


def bench(fn, n):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


f_float = bench(lambda: R.cos(0.7), 2000)
f_ship = bench(lambda: R.cos(1), 20)
f_cand = bench(lambda: candidate(1, 1, 61, "cos"), 200)
emit(rec="cost", op="cos(1) exact route",
     float_route_us=round(f_float * 1e6, 3),
     shipped_exact_us=round(f_ship * 1e6, 1),
     candidate_us=round(f_cand * 1e6, 1),
     shipped_over_float=round(f_ship / f_float, 1),
     candidate_over_float=round(f_cand / f_float, 2),
     candidate_speedup_vs_shipped=round(f_ship / f_cand, 1))
