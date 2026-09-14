"""B3 - direction dependence of the approach in the Kepler (e-order p, harmonic k) lattice.

Five directions through one lattice c_{p,k} (coefficient of e^p sin kM in E-M), each with its
own asymptotic per-step ratio, measured:
  D-p   : along p at fixed k   (the e-order tower INSIDE one harmonic)   -> factorial decay (ratio -> 0)
  D-diag: along the diagonal p = k (leading e-order of each harmonic)    -> ratio -> e*exp(1)/2
  D-k   : along k with the tower summed (Kapteyn radius r_k, bessel_j_fixed) -> ratio -> rho(e)
  D-row : along p with harmonics summed (Lagrange a_p at M = pi/2)        -> ratio -> e/e_L
  D-step: the one-pin iteration (depth n; not a lattice direction)        -> ratio -> e
Plus: triangular support (k <= p), parity (p = k mod 2), and equal-index truncation errors.

INSTRUMENTS: srmech kepler_solve, bessel_j_fixed. HAND-ROLLED (disclosed): Fraction lattice
(validated against bessel_j_fixed in b2), float sin on the output grid, math.log/exp/sqrt.
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math import kepler
from srmech.music import bessel_j_fixed
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)

def kapteyn(p, k):
    if k < 1 or k > p or (p - k) % 2:
        return F(0)
    m = (p - k) // 2
    return F((-1) ** m * 2 * k ** (2 * m + k), k * 2 ** (2 * m + k) * math.factorial(m) * math.factorial(m + k))

P = 41
cells = [(p, k) for p in range(1, P + 1) for k in range(1, p + 1) if kapteyn(p, k) != 0]
print(f"support: nonzero cells with p<={P}: {len(cells)}; all satisfy k<=p: {all(k <= p for p, k in cells)}; all satisfy p=k mod 2: {all((p - k) % 2 == 0 for p, k in cells)}")
print(f"  cells with k > p (would be a symmetric lattice): 0 by construction; the lattice is TRIANGULAR and PARITY-GRADED")

E_L = 0.6627434193  # CITED-NOT-FETCHED, comparison column only
def rho(e):
    s = math.sqrt(1 - e * e); return e * math.exp(s) / (1 + s)

for e in (0.3, 0.7, 0.75):
    ef = F(e).limit_denominator(1000)
    print(f"\n=== e = {e} ===")
    # D-p: fixed k=1 and k=3, ratio of successive nonzero cells along p
    for k in (1, 3):
        rr = [float(abs(kapteyn(p + 2, k) * ef ** 2 / kapteyn(p, k))) for p in range(k, 31, 2)]
        print(f"  D-p   (k={k}): ratios along p: {[f'{r:.3e}' for r in rr[:3]]} ... {[f'{r:.3e}' for r in rr[-2:]]} -> 0 (factorial)")
    # D-diag
    rr = [float(abs(kapteyn(k + 1, k + 1) * ef / kapteyn(k, k))) for k in range(20, 40)]
    print(f"  D-diag        : ratio at k=39: {rr[-1]:.4f}; limit e*exp(1)/2 = {e * math.e / 2:.4f} -> {'DIVERGES' if e * math.e / 2 > 1 else 'converges'}")
    # D-k: Kapteyn radii from the shipped Bessel op
    def r(k):
        num, den = bessel_j_fixed(k, k * ef.numerator, ef.denominator)
        return F(2, k) * F(num, den)
    if e < 1:
        rk = [float(r(k + 1) / r(k)) for k in (20, 40, 60)]
        print(f"  D-k           : r_(k+1)/r_k at k=20,40,60: {[f'{v:.4f}' for v in rk]}; rho(e) = {rho(e):.4f} -> converges for e<1")
    # D-row: Lagrange a_p at M = pi/2
    a = {p: sum(kapteyn(p, k) * (1 if k % 4 == 1 else -1) for k in range(1, p + 1, 2)) for p in range(1, P + 1, 2)}
    rr = [(abs(float(a[p + 2] / a[p])) ** 0.5) * e for p in (31, 35, 39)]
    print(f"  D-row         : (|a_(p+2)/a_p|)^(1/2)*e at p=31,35,39: {[f'{v:.4f}' for v in rr]}; e/e_L = {e / E_L:.4f} -> {'DIVERGES' if e / E_L > 1 else 'converges'}")
    # D-step: one-pin iteration
    if e < 1:
        N = 256; G = [2 * math.pi * i / N for i in range(N)]
        ref = [kepler.kepler_solve(M, e) for M in G]
        En = list(G); errs = []
        for n in range(1, 31):
            En = [M + e * math.sin(x) for M, x in zip(G, En)]
            errs.append(max(abs(u - v) for u, v in zip(En, ref)))
        win = [i for i in range(len(errs) - 1) if 1e-10 < errs[i + 1] and errs[i] < 1e-3]
        print(f"  D-step        : err(n+1)/err(n) over steps {win[0]+1}..{win[-1]+1} (1e-3 > err > 1e-10): mean {sum(errs[i + 1] / errs[i] for i in win) / len(win):.4f}, last {errs[win[-1] + 1] / errs[win[-1]]:.4f} -> e = {e}")
        # equal-index truncation errors: depth n vs K = n modes
        for n in (5, 10, 20):
            K = n
            approx = [M + sum(float(r(k)) * math.sin(k * M) for k in range(1, K + 1)) for M in G]
            mode_err = max(abs(u - v) for u, v in zip(approx, ref))
            print(f"  equal index n=K={n}: depth error {errs[n - 1]:.2e}  vs  mode error {mode_err:.2e}  ratio depth/mode = {errs[n - 1] / mode_err:.3f}")

print("\nSUMMARY (per e): five directions, five limiting ratios {0, e*e^1/2, rho(e), e/e_L, e}: the approach is direction-dependent in the index lattice.")
print("radii: D-p entire (no radius); D-diag e < 2/e^1 = 0.7358; D-k e < 1; D-row e < e_L = 0.6627; D-step e < 1 (contraction).")
