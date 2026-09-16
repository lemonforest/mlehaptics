"""Kepler's equation as a HARMONIC cascade: E(M) = M + sum_k (2/k) J_k(k e) sin(k M).

Each mode is one epicycle: a gear at integer ratio k (Class I) carrying a pin of radius
(2/k) J_k(k e). Radii come from srmech.music.bessel_j_fixed (exact rational at a DECLARED
2^-256 scale; not a claim that J_k is rational). Compared against the harmonics measured from
srmech's kepler_solve, then the K-mode reconstruction against kepler_solve pointwise.

The `measured` table below is the k=1..4 harmonic magnitudes this cascade is checked against;
they are produced by `_rc473_kepler_cascade_iter.py` in the same cell and are pasted here so
this script states what it is comparing to rather than recomputing it silently.

CELL, printed rather than assumed: the figures in srmech_research_notebook.md section 3.60
come from the PUBLISHED wheel srmech 0.9.0rc473 (`HAS_NATIVE True`, installed in a venv
outside this repository, numpy absent). The same run against the rc472 source tree printed
the same table. No `sys.path` insertion on purpose: an inserted repository path silently
measures the working tree instead of the installed version.
"""
import math
from fractions import Fraction
from srmech.math import kepler
from srmech.music import bessel_j_fixed
from srmech import _native
print("HAS_NATIVE", _native.HAS_NATIVE, "file", kepler.__file__)

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
