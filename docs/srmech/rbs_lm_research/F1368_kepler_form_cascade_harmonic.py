"""Kepler's equation as a HARMONIC cascade: E(M) = M + sum_k (2/k) J_k(k e) sin(k M).

Each mode is one epicycle: a gear at integer ratio k (Class I) carrying a pin of radius
(2/k) J_k(k e). Radii come from srmech.music.bessel_j_fixed (exact rational at a DECLARED
2^-256 scale; not a claim that J_k is rational). Compared against the harmonics measured from
srmech's kepler_solve, then the K-mode reconstruction against kepler_solve pointwise.
"""
import math, sys
from fractions import Fraction
sys.path.insert(0, r"D:/GitHub/mlehaptics/docs/srmech/python")
from srmech.math import kepler
from srmech.music import bessel_j_fixed
from srmech import _native
print("HAS_NATIVE", _native.HAS_NATIVE, "(pure cell)")

measured = {Fraction(3, 10): [0.296638, 0.043665, 0.009623, 0.002511],
            Fraction(7, 10): [0.657991, 0.207356, 0.096851, 0.053334]}
N = 128
grid = [2 * math.pi * j / N for j in range(N)]
for e, meas in measured.items():
    radii = []
    for k in range(1, 61):
        num, den = bessel_j_fixed(k, k * e.numerator, e.denominator)
        radii.append(Fraction(2, k) * Fraction(num, den))
    print(f"\ne = {float(e)}   k   (2/k)J_k(ke) [declared 2^-256]   measured from kepler_solve")
    for k in range(4):
        print(f"            {k+1}   {float(radii[k]): .6f}                      {meas[k]: .6f}")
    ref = [kepler.kepler_solve(M, float(e)) for M in grid]
    sines = [[math.sin((k + 1) * M) for M in grid] for k in range(60)]
    print("   modes   max|E_K - E_kepler|")
    for K in (1, 2, 4, 8, 16, 32, 60):
        err = 0.0
        for j, M in enumerate(grid):
            EK = M + sum(float(radii[k]) * sines[k][j] for k in range(K))
            d = EK - ref[j]
            err = max(err, d if d >= 0 else -d)
        print(f"   {K:5d}   {err:.3e}")
