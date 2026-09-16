"""Is the pin-slot harmonic series IDENTICAL to Kepler's equation, or equal only to low order?

Objects measured are srmech's own ops: kepler.kepler_solve gives E(M) for Kepler's equation
M = E - e sin E; kepler.pin_slot gives the rocker angle atan2(eps sin th, 1 + eps cos th),
whose harmonic magnitudes the stance records as eps^k/k. The Fourier projection (the
instrument) is a plain N-point quadrature, exact to rounding for these smooth periodic
functions; it is disclosed as hand-rolled.

CELL, and it is printed rather than assumed: run against whatever srmech is importable.
The figures in srmech_research_notebook.md section 3.60 come from the PUBLISHED wheel
srmech 0.9.0rc473 (`HAS_NATIVE True`, installed in a venv outside this repository, numpy
absent). The same run against the rc472 source tree printed the same coefficients, so the
result is not sensitive to the cell -- but the cell is printed so a re-runner can see which
one they got. No `sys.path` insertion here on purpose: an inserted repository path silently
measures the working tree instead of the version you think you are testing.
"""
import math, time
import srmech
from srmech.math import kepler
from srmech import _native
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE, "file", kepler.__file__)

N, KMAX = 256, 5
def sine_coeffs(f):
    th = [2 * math.pi * j / N for j in range(N)]
    vals = [f(t) for t in th]
    return [2.0 / N * sum(v * math.sin(k * t) for v, t in zip(vals, th)) for k in range(1, KMAX + 1)]

for e in (0.1, 0.3):
    t0 = time.time()
    kep = sine_coeffs(lambda M: kepler.kepler_solve(M, e) - M)          # E(M) - M
    pin = sine_coeffs(lambda th: kepler.pin_slot(th, e, 1.0))           # rocker angle
    cauchy = [e ** k / k for k in range(1, KMAX + 1)]
    print(f"\ne = {e}   ({time.time() - t0:.1f}s)")
    print("  k   Kepler E(M)-M coeff   pin_slot coeff        eps^k/k             Kepler/cauchy")
    for k in range(KMAX):
        print(f"  {k+1}   {kep[k]: .15f}   {pin[k]: .15f}   {cauchy[k]: .15f}   {kep[k]/cauchy[k]: .6f}")
