"""S3 - what the eps^k/k series IS, and what the May-2026 records' numbers ARE.
Harmonic projection = N-point quadrature (hand-rolled, disclosed). Kepler E via srmech kepler_solve.
True anomaly nu from E via nu = 2 atan2(sqrt(1+e) sin(E/2), sqrt(1-e) cos(E/2)) using math (float instrument,
disclosed). Bessel radii via srmech.music.bessel_j_fixed. EOC table via srmech kepler.equation_of_centre coefficients.
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
from srmech import _native
from srmech.math import kepler
from srmech.music import bessel_j_fixed
print("HAS_NATIVE", _native.HAS_NATIVE, "EOC table", kepler._EOC_COEFFS)
N, KM = 512, 7
th = [2 * math.pi * j / N for j in range(N)]
def sine_coeffs(vals):
    return [2.0 / N * sum(v * math.sin(k * t) for v, t in zip(vals, th)) for k in range(1, KM + 1)]
def kap(k, e):
    num, den = bessel_j_fixed(k, k * e.numerator, e.denominator)
    return float(F(2, k) * F(num, den))
def nu_of_E(E, e):
    return 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))

print("\n(A) Spike #29 eps = 0.1146: eps^k/k vs Kepler E-M harmonics (2/k)J_k(k eps)")
e = F(573, 5000)
for k in range(1, KM + 1):
    c = float(e) ** k / k
    kk = kap(k, e)
    print(f"  k={k}  eps^k/k={c:.6e}  (2/k)J_k={kk:.6e}  ratio={c / kk:.4f}")

for e in (F(167, 10000), F(253, 5000), F(3, 10)):
    ef = float(e)
    E = [kepler.kepler_solve(M, ef) for M in th]
    nu = [nu_of_E(x, ef) for x in E]
    eoc = sine_coeffs([(n - M + math.pi) % (2 * math.pi) - math.pi for n, M in zip(nu, th)])
    eml = sine_coeffs([x - M for x, M in zip(E, th)])
    print(f"\n(B) e = {ef}:  k | nu-M measured | EOC table c_k e^k | E-M measured | e^k/k")
    for k in range(1, 5):
        tab = kepler._EOC_COEFFS[k - 1] * ef ** k
        print(f"   {k} | {eoc[k-1]: .6e} | {tab: .6e} | {eml[k-1]: .6e} | {ef ** k / k: .6e}")

print("\n(C) the eps^k/k series in Kepler motion: (nu - E)(E) harmonics vs 2 beta^k / k, beta = e/(1+sqrt(1-e^2))")
for ef in (0.3, 0.7):
    beta = ef / (1 + math.sqrt(1 - ef * ef))
    d = sine_coeffs([(nu_of_E(E, ef) - E + math.pi) % (2 * math.pi) - math.pi for E in th])
    print(f"  e={ef} beta={beta:.6f}: " + "  ".join(f"k{k}: {d[k-1]:.8f}/{2 * beta ** k / k:.8f}" for k in range(1, 5)))

print("\n(D) FM sidebands |J_k(beta)| vs Kepler Kapteyn radii (2/k)J_k(k beta)")
for b in (F(3, 10), F(1, 2)):
    fm = []
    for k in range(1, 6):
        num, den = bessel_j_fixed(k, b.numerator, b.denominator)
        fm.append(float(F(num, den)))
    print(f"  beta={float(b)}  FM: " + " ".join(f"{x:.3e}" for x in fm)
          + "   Kepler: " + " ".join(f"{kap(k, b):.3e}" for k in range(1, 6)))

print("\n(E) Hopf 'per-mode gap' check (integers): S3 unit l(l+2); S2 unit l(l+1); Hopf base S2 radius 1/2: 4j(j+1), l = 2j")
for l in range(0, 9):
    s3, s2 = l * (l + 2), l * (l + 1)
    base = 4 * (l // 2) * (l // 2 + 1) if l % 2 == 0 else None
    print(f"  l={l}: S3={s3:3d}  S2(r=1)={s2:3d}  gap={s3 - s2}  S2(r=1/2) at j=l/2: {base}  equal-to-S3: {base == s3 if base is not None else '-'}")
