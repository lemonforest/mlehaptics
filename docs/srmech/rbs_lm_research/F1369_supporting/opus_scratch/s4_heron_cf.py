"""S4 - a second two-frame instance with an EXACT index correspondence, and a record-rate check.
Heron (depth frame) vs continued-fraction convergents (Class N frame, srmech.math.rational.best_rational).
Fibonacci ratio convergence rate vs |psi| and psi^2. Fractions + integer isqrt brackets (disclosed).
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
from srmech import _native
from srmech.math.rational import best_rational
print("HAS_NATIVE", _native.HAS_NATIVE)
D = 10 ** 300
s2 = F(math.isqrt(2 * D * D), D)
conv = [(1, 1), (3, 2)]
while conv[-1][1] < 10 ** 40:
    (p1, q1), (p0, q0) = conv[-1], conv[-2]
    conv.append((2 * p1 + p0, 2 * q1 + q0))
ok = all(best_rational(s2.numerator, s2.denominator, q) == (p, q) for p, q in conv)
print("CF convergents of sqrt2 (recurrence) == srmech best_rational at each convergent denominator:", ok, "count", len(conv))
x = F(1)
for n in range(1, 7):
    x = (x + 2 / x) / 2
    idx = conv.index((x.numerator, x.denominator)) if (x.numerator, x.denominator) in conv else None
    err = x - s2
    print(f"  Heron depth {n}: {x.numerator}/{x.denominator} = convergent index {idx}   error 10^{math.log10(float(err)):.1f}")
phi = F(math.isqrt(5 * D * D) + D, 2 * D)
fib = [1, 1]
while len(fib) < 45:
    fib.append(fib[-1] + fib[-2])
errs = [F(fib[n + 1], fib[n]) - phi for n in range(len(fib) - 1)]
print("Fibonacci ratio error ratios err(n+1)/err(n): " + " ".join(f"{float(errs[n + 1] / errs[n]):.6f}" for n in (10, 20, 30, 40)))
psi = (1 - math.sqrt(5)) / 2
print(f"  |psi| = {abs(psi):.6f}   psi^2 = {psi * psi:.6f}")
