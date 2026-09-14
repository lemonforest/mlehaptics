"""S2 - approach RATES of the two frames toward the same Kepler E(M).
Depth frame: E_(n+1) = M + e*sin(E_n), sin = srmech Class-N kepler._rsin; reference kepler_solve.
Mode frame: radii (2/k)J_k(ke) from srmech.music.bessel_j_fixed (declared 2^-256).
Comparison constants: e (Lipschitz constant of the pin stage) and rho(e) = e*exp(sqrt(1-e^2))/(1+sqrt(1-e^2))
(Bessel large-order form, CITED-NOT-FETCHED). Grid sup-norm = hand-rolled, disclosed.
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
from srmech import _native
from srmech.math import kepler
from srmech.music import bessel_j_fixed
print("HAS_NATIVE", _native.HAS_NATIVE)
N = 64
grid = [2 * math.pi * (j + 0.5) / N for j in range(N)]
for e in (F(1, 10), F(3, 10), F(7, 10)):
    ef = float(e)
    ref = [kepler.kepler_solve(M, ef) for M in grid]
    E = list(grid)
    errs = []
    for n in range(1, 61):
        E = [M + ef * float(kepler._rsin(x)) for M, x in zip(grid, E)]
        err = max((x - r) if x >= r else (r - x) for x, r in zip(E, ref))
        errs.append(err)
        if err < 1e-13:
            break
    tail = [errs[i] / errs[i - 1] for i in range(len(errs) // 2, len(errs))]
    rho = ef * math.exp(math.sqrt(1 - ef * ef)) / (1 + math.sqrt(1 - ef * ef))
    print(f"\ne = {ef}: depth frame  steps to 1e-13: {len(errs)};  per-step sup-error ratio (2nd half) "
          f"min {min(tail):.4f} max {max(tail):.4f}   [e = {ef}]")
    radii = []
    for k in range(1, 62):
        num, den = bessel_j_fixed(k, k * e.numerator, e.denominator)
        radii.append(F(2, k) * F(num, den))
    ratios = {k: float(radii[k] / radii[k - 1]) for k in (10, 20, 30, 40, 60)}
    print("  mode frame  radius ratio r_(k+1)/r_k: " + "  ".join(f"k={k}:{v:.4f}" for k, v in ratios.items())
          + f"   [rho(e) = {rho:.4f}]")
    # modes needed for 1e-13 tail bound sum_{k>K} r_k
    tailsum = F(0)
    K13 = None
    for K in range(60, 0, -1):
        tailsum += radii[K]
        if float(tailsum) > 1e-13:
            K13 = K + 1
            break
    print(f"  modes needed so that sum of omitted radii (k<=61) < 1e-13: K = {K13}")
