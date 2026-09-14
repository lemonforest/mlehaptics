"""B3 - three constructions of pi (P6, P7) and the bounded 2^-44 register (P10).

srmech ops: math.rational.atan_series_truncate (exact Q), math.rational.pi_chudnovsky_digits (reference),
math.rational.pi_cascade_digits, calculus.sqrt (Class-N rational sqrt at declared precision),
music.commensurability_verdict, math.laplacian._eph_seam_fold (the pure winding_fold path; private, read-only).
HAND-ROLLED (disclosed): the Pfaff two-mean recurrence exactly as pi_cascade_digits' docstring states it,
but carried in exact rationals with srmech's sqrt at 3000 bits so each STAGE can be read (the shipped op
exposes only digits); ratio estimators.
"""
import sys, math, inspect
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math.q import Q
from srmech.math import rational as R
from srmech import calculus as C
from srmech.music import commensurability_verdict

print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)


def qf(x):
    return F(x.numerator, x.denominator)


ps = R.pi_chudnovsky_digits(700)
PI = F(int(ps.replace('.', '')), 10 ** len(ps.split('.')[1]))

print("\n(P6/P7) error ratios per step")
mach, eul = [], []
for Nt in range(1, 41):
    m = 16 * qf(R.atan_series_truncate(1, 5, Nt)) - 4 * qf(R.atan_series_truncate(1, 239, Nt))
    u = 4 * (qf(R.atan_series_truncate(1, 2, Nt)) + qf(R.atan_series_truncate(1, 3, Nt)))
    mach.append(m - PI)
    eul.append(u - PI)
for i in (10, 20, 30):
    print(f"  N={i}: Machin err ratio {float(mach[i] / mach[i - 1]):+.8f}   Euler err ratio {float(eul[i] / eul[i - 1]):+.8f}")

sq = lambda z: qf(C.sqrt(Q(z.numerator, z.denominator), precision=3000))
a, b = sq(F(12)), F(3)
pf = [(a, b)]
for n in range(1, 60):
    a = 2 * a * b / (a + b)
    b = sq(a * b)
    pf.append((a, b))
berr = [PI - bb for _, bb in pf]
aerr = [aa - PI for aa, _ in pf]
for n in (10, 20, 30, 45):
    print(f"  Pfaff depth {n}: inscribed err ratio {float(berr[n] / berr[n - 1]):.8f}  circumscribed {float(aerr[n] / aerr[n - 1]):.8f}  (bracket holds: {pf[n][1] < PI < pf[n][0]})")
print("  instrument floor: 3000-bit sqrt, errors used only while > 1e-600")

print("\n  shipped pi_cascade_digits at limited depth (digits vs Chudnovsky):")
for d in (5, 10, 20, 30):
    try:
        s = R.pi_cascade_digits(40, max_cascade_depth=d)
        good = next((i for i, (x, y) in enumerate(zip(s, ps)) if x != y), len(s))
        print(f"    max_cascade_depth={d}: first differing character index {good}")
    except Exception as ex:
        print(f"    max_cascade_depth={d}: raised {type(ex).__name__}: {str(ex)[:120]}")

print("\n  stage equality checks (exact): any Machin/Euler partial sum (N<=40) equal to Pfaff b_0 = 3 or a_0?",
      any(m + PI == 3 for m in mach) or any(u + PI == 3 for u in eul))

print("\n  shipped commensurability instrument on the step RATES read as values:")
for lab, parts in (("Pfaff 1/4 vs Machin 1/25 (fundamental = 1/4)", [Q(1, 1), Q(4, 25)]),
                   ("Pfaff 1/4 vs Euler 1/4", [Q(1, 1), Q(1, 1)])):
    v = commensurability_verdict(parts)
    print(f"    {lab}: verdict={v.get('verdict')} integer_series={v.get('integer_series')} rational_rank={v.get('rational_rank')}")
print("  step-count sense: log(1/4)/log(1/25) =", math.log(4) / math.log(25), "= log2/log5 (irrational: 2^a = 5^b has no solution in positive integers)")

print("\n(P10) the pure winding_fold 2pi constant vs Machin partial sums")
from srmech.math import laplacian as L
src = inspect.getsource(L._eph_seam_fold)
print("  _eph_seam_fold source head:\n    " + "\n    ".join(src.splitlines()[:40]))
