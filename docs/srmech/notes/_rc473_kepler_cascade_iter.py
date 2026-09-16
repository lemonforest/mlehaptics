"""Kepler's equation as an ITERATED cascade of one-pin stages: E_{n+1} = M + e*sin(E_n), E_0 = M.

Each stage is one epicycle: a gear at M carrying a pin of radius e whose phase is the previous
stage's output. Question measured: does depth n build Kepler's own harmonics, and how fast does
it approach Kepler's E? Reference E is srmech's kepler_solve. The stage's sin is srmech's
Class-N sin (kepler._rsin). Fourier projection = plain quadrature (disclosed as hand-rolled).

CELL, printed rather than assumed: the figures in srmech_research_notebook.md section 3.60
come from the PUBLISHED wheel srmech 0.9.0rc473 (`HAS_NATIVE True`, installed in a venv
outside this repository, numpy absent). The same run against the rc472 source tree printed
the same table. The line below prints the cell it actually got, so a re-runner can tell which
one they are reading. No `sys.path` insertion on purpose: an inserted repository path
silently measures the working tree instead of the installed version.
"""
import math
from srmech.math import kepler
from srmech import _native
print("HAS_NATIVE", _native.HAS_NATIVE, "file", kepler.__file__)

N, KMAX = 128, 4
grid = [2 * math.pi * j / N for j in range(N)]

def stage_cascade(M, e, depth):
    E = M
    for _ in range(depth):
        E = M + e * float(kepler._rsin(E))
    return E

def coeffs(vals):
    return [2.0 / N * sum(v * math.sin(k * t) for v, t in zip(vals, grid)) for k in range(1, KMAX + 1)]

for e in (0.1, 0.3, 0.7):
    ref = [kepler.kepler_solve(M, e) for M in grid]
    kc = coeffs([r - M for r, M in zip(ref, grid)])
    print(f"\ne = {e}   Kepler harmonics (k=1..4): " + "  ".join(f"{c:.6f}" for c in kc))
    print("  depth   max|E_n - E_kepler|    harmonics of the depth-n cascade (k=1..4)")
    for depth in (1, 2, 3, 5, 10, 20, 40):
        vals = [stage_cascade(M, e, depth) for M in grid]
        err = max((v - r) if v >= r else (r - v) for v, r in zip(vals, ref))
        hc = coeffs([v - M for v, M in zip(vals, grid)])
        print(f"  {depth:5d}   {err:18.3e}    " + "  ".join(f"{c:.6f}" for c in hc))
