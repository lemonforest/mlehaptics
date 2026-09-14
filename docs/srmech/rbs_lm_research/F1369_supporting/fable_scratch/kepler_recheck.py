"""Recheck of the May-2026 'c_k = eps^k/k IS Kepler' chain, on srmech's own ops (main checkout).

Instruments (disclosed): the Fourier sine-projection is a plain N-point quadrature (hand-rolled);
nu(E) uses math.atan2/sqrt (hand-rolled, float, output-side only). Everything Kepler-side is
srmech: kepler.kepler_solve (E from M), kepler.pin_slot (rocker angle), music.bessel_j_fixed
(declared 2^-256 rational). numpy is NOT imported anywhere here.
"""
import math, sys
from fractions import Fraction
sys.path.insert(0, r"D:/GitHub/mlehaptics/docs/srmech/python")
try:
    import numpy  # noqa
    NUMPY = "IMPORTABLE (not used)"
except Exception:
    NUMPY = "ABSENT"
import srmech
from srmech.math import kepler
from srmech.music import bessel_j_fixed
from srmech import _native
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE, "numpy", NUMPY, "file", kepler.__file__)

N = 512
grid = [2 * math.pi * j / N for j in range(N)]

def sine_coeffs(vals, kmax):
    return [2.0 / N * sum(v * math.sin(k * t) for v, t in zip(vals, grid)) for k in range(1, kmax + 1)]

def kepler_E(e):
    return [kepler.kepler_solve(M, e) for M in grid]

def nu_from_E(E, e):
    return 2.0 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))

def bessel_radius(k, e_frac):
    num, den = bessel_j_fixed(k, k * e_frac.numerator, e_frac.denominator)
    return float(Fraction(2, k) * Fraction(num, den))

def unwrap_diff(a, b):
    d = a - b
    while d > math.pi: d -= 2 * math.pi
    while d < -math.pi: d += 2 * math.pi
    return d

def r2_loglin(cs):
    """Strict-K-style fit: log(c_k * k) ~ a + b*k  (unbiased variant of Spike #41 §5.2). Returns (r2, exp(b))."""
    ks = list(range(1, len(cs) + 1))
    ys = [math.log(abs(c) * k) for c, k in zip(cs, ks)]
    n = len(ks); mx = sum(ks) / n; my = sum(ys) / n
    sxy = sum((k - mx) * (y - my) for k, y in zip(ks, ys)); sxx = sum((k - mx) ** 2 for k in ks)
    b = sxy / sxx; a = my - b * mx
    ss_res = sum((y - (a + b * k)) ** 2 for k, y in zip(ks, ys)); ss_tot = sum((y - my) ** 2 for y in ys)
    return 1 - ss_res / ss_tot, math.exp(b)

print("\n=== A. E(M)-M harmonics of Kepler's equation vs eps^k/k vs (2/k)J_k(ke) ===")
for e_frac in (Fraction(167, 10000), Fraction(1, 10), Fraction(3, 10), Fraction(618, 1000)):
    e = float(e_frac)
    E = kepler_E(e)
    ck = sine_coeffs([x - M for x, M in zip(E, grid)], 6)
    print(f"e={e}")
    print("  k   Kepler(E-M)      eps^k/k         (2/k)J_k(ke)     Kepler/(eps^k/k)   Kepler/Bessel")
    for k in range(1, 7):
        c = ck[k - 1]; ca = e ** k / k; cb = bessel_radius(k, e_frac)
        print(f"  {k}   {c: .9f}   {ca: .9f}   {cb: .9f}   {c/ca: .6f}          {c/cb: .9f}")

print("\n=== B. Earth e=0.0167: TRUE-anomaly equation of centre nu-M vs Spike #30B numbers vs (2e)^k/k ===")
e_frac = Fraction(167, 10000); e = float(e_frac)
E = kepler_E(e)
nu = [nu_from_E(x, e) for x in E]
ck_nu = sine_coeffs([unwrap_diff(v, M) for v, M in zip(nu, grid)], 4)
closed = [2 * e, 1.25 * e ** 2, (13 / 12) * e ** 3, (103 / 96) * e ** 4]
print("  k   measured nu-M    closed-form (2e,5/4e^2,13/12e^3,103/96e^4)   (2e)^k/k     Spike#30B recorded")
rec = [0.03340, 3.486e-4, 5.045e-6, None]
for k in range(1, 5):
    g = (2 * e) ** k / k
    print(f"  {k}   {ck_nu[k-1]: .6e}    {closed[k-1]: .6e}                              {g: .6e}   {rec[k-1]}")
print(f"  ratio measured/(2e)^k/k at k=2: {ck_nu[1]/((2*e)**2/2):.4f}   (5/4)/2 = {1.25/2:.4f}")

print("\n=== C. The strict-K fit does NOT discriminate: r2 of log(c_k k) ~ a + b k on TRUE Kepler coefficients ===")
for e_frac in (Fraction(167, 10000), Fraction(3, 10), Fraction(618, 1000)):
    e = float(e_frac); E = kepler_E(e)
    ck = sine_coeffs([x - M for x, M in zip(E, grid)], 6)
    r2, ef = r2_loglin(ck)
    r2b, efb = r2_loglin([bessel_radius(k, e_frac) for k in range(1, 7)])
    print(f"  e={e}: TRUE Kepler E-M k=1..6  r2={r2:.5f} eps_fit={ef:.4f} | Bessel closed form r2={r2b:.5f} eps_fit={efb:.4f} | eps^k/k would give r2=1.0000 eps_fit={e}")

print("\n=== D. Pin-slot atan2(sin M, cos M - eps) IS exactly eps^k/k (eccentric-circle equation of centre), not Kepler ===")
for eps in (0.1146, 0.3):
    vals = [math.atan2(math.sin(M), math.cos(M) - eps) for M in grid]
    ck = sine_coeffs([unwrap_diff(v, M) for v, M in zip(vals, grid)], 5)
    print(f"  eps={eps}: ratio to eps^k/k k=1..5:", " ".join(f"{ck[k-1]/(eps**k/k):.9f}" for k in range(1, 6)))
# srmech's own pin_slot (rocker angle) for comparison, magnitude eps^k/k with alternating sign
eps = 0.3
vals = [kepler.pin_slot(th, eps, 1.0) for th in grid]
ck = sine_coeffs(vals, 5)
print(f"  srmech kepler.pin_slot(th,0.3,1.0) coeffs k=1..5:", " ".join(f"{c:+.6f}" for c in ck), " | eps^k/k:", " ".join(f"{eps**k/k:.6f}" for k in range(1,6)))

print("\n=== E. Spike #41 'Fibonacci psi-decay IS Kepler EOC at e=|psi|': |psi|^k/k vs TRUE Kepler harmonics at e=0.618 ===")
psi = (1 - math.sqrt(5)) / 2
e_frac = Fraction(618, 1000); e = float(e_frac); E = kepler_E(e)
ck = sine_coeffs([x - M for x, M in zip(E, grid)], 6)
print("  k   |psi|^k/k      Kepler E-M at e=0.618   ratio")
for k in range(1, 7):
    print(f"  {k}   {abs(psi)**k/k: .6f}     {ck[k-1]: .6f}              {abs(psi)**k/k/ck[k-1]: .4f}")

print("\n=== F. Cross-truncation: depth-n one-pin cascade vs K-mode harmonic truncation — related by an exact correspondence, or only by the limit? ===")
def stage_cascade(M, e, depth):
    x = M
    for _ in range(depth):
        x = M + e * float(kepler._rsin(x))
    return x
print("  F1. depth-n cascade harmonic error c_k^(n)(e) - c_k^Kepler(e), and its scaling exponent in e (log-ratio e=0.1 vs 0.2)")
for depth in (1, 2, 3, 4):
    errs = {}
    for e in (0.1, 0.2):
        E = kepler_E(e); ck = sine_coeffs([x - M for x, M in zip(E, grid)], 6)
        vals = [stage_cascade(M, e, depth) for M in grid]; cn = sine_coeffs([v - M for v, M in zip(vals, grid)], 6)
        errs[e] = [cn[k] - ck[k] for k in range(6)]
    exps = []
    for k in range(6):
        a, b = abs(errs[0.1][k]), abs(errs[0.2][k])
        exps.append(math.log(b / a) / math.log(2) if a > 1e-15 and b > 1e-15 else float('nan'))
    print(f"    depth {depth}: |err| at e=0.2 k=1..6 = " + " ".join(f"{abs(x):.2e}" for x in errs[0.2]) + "  | exponent = " + " ".join(f"{x:.2f}" for x in exps))
print("  F2. harmonic support of the depth-n cascade (which k are nonzero at e=0.3)")
for depth in (1, 2, 3):
    vals = [stage_cascade(M, 0.3, depth) for M in grid]; cn = sine_coeffs([v - M for v, M in zip(vals, grid)], 8)
    print(f"    depth {depth}: c_k k=1..8 = " + " ".join(f"{c:.2e}" for c in cn))
print("  F3. pointwise error of the two truncation frames at e=0.7 (beyond the Laplace limit 0.6627 of the POWER series in e)")
e_frac = Fraction(7, 10); e = 0.7
ref = kepler_E(e)
radii = [bessel_radius(k, e_frac) for k in range(1, 61)]
for n in (1, 2, 4, 8, 16, 32):
    vals = [stage_cascade(M, e, n) for M in grid]
    err_d = max(abs(v - r) for v, r in zip(vals, ref))
    err_k = max(abs(M + sum(radii[k] * math.sin((k + 1) * M) for k in range(n)) - r) for M, r in zip(grid, ref))
    print(f"    n={n:2d}: depth-n cascade max err {err_d:.3e}   |   n-mode harmonic max err {err_k:.3e}")
lap = 0.6627434
rho = lambda e: e * math.exp(math.sqrt(1 - e * e)) / (1 + math.sqrt(1 - e * e))
print(f"  F4. per-step contraction of the iteration is e (=0.7); per-mode decay of the Bessel series ~ rho(e)={rho(0.7):.4f} (at e=0.3: rho={rho(0.3):.4f}); Laplace limit {lap} is where rho(e)=1: rho({lap})={rho(lap):.6f}")
