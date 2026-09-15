"""rc473 truth repair 1 (`#T1188`): the two Kepler figures the truth-round gate found overstated.

B2 — the curated ``pin_slot`` why said the departure at theta = pi/2 "lands on -eps to
     four significant figures at three different eccentricities". Printed here: the
     departure, -eps, -atan(eps), the significant-figure counts at which the departure
     and -eps agree as rounded ``%.{n}g`` strings, and (departure + eps) / eps**3.
B1 — ``nu - E`` as a doubled stage was shipped as "to within 2.0e-15 rad for e from
     0.0549 to 0.99". Printed here: the largest difference over uniform E grids of 64,
     256, 1024 and 4096 points ((j + 0.5) offsets, as ``_rc473_truth_kepler_family.py``
     uses) at the five e, a 47-e sweep of [0.0549, 0.99] at 1024 E, and three e above
     that range inside the op's domain.

Ops under test: ``srmech.math.kepler.pin_slot``. Reference trig and sqrt are srmech's
own (``srmech.math.rational``). No numpy, no math module; magnitudes are a Class-K branch.

Usage (from docs/srmech):  python3 notes/_rc473_truth_repair1_kepler.py python
"""
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "python")
import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech.math import kepler as K  # noqa: E402
from srmech.math import rational as R  # noqa: E402

print("python", sys.version.split()[0], "srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)
PI = float(R.atan2(0.0, -1.0))


def sin(x):
    return float(R.sin(x))


def cos(x):
    return float(R.cos(x))


def sqrt(x):
    return float(R.sqrt(x))


def mag(x):
    return x if x >= 0.0 else -x          # Class-K magnitude, reporting only


print("\n[B2] departure pin_slot(pi/2, 1.0, eps) - pi/2 against -eps")
for eps in (0.0114, 0.0549, 0.0934):
    dep = K.pin_slot(PI / 2, 1.0, eps) - PI / 2
    at = -float(R.atan2(eps, 1.0))
    agree = [n for n in range(1, 8) if f"{dep:.{n}g}" == f"{-eps:.{n}g}"]
    most = 0
    for n in range(1, 8):
        if f"{dep:.{n}g}" == f"{-eps:.{n}g}":
            most = n
        else:
            break
    print(f"  eps={eps}: departure {dep!r}  -eps {-eps!r}  -atan(eps) {at!r}  departure == -atan(eps): {dep == at}"
          f"  agree at s.f. {agree} (leading run {most})  (departure + eps) / eps^3 = {(dep + eps) / eps ** 3:+.6f}")


def worst_nu(e, grid):
    beta = e / (1.0 + sqrt(1.0 - e * e))
    w, wE = 0.0, None
    for E in grid:
        nu = 2.0 * float(R.atan2(sqrt(1.0 + e) * sin(E / 2), sqrt(1.0 - e) * cos(E / 2)))
        d = mag(E + 2.0 * K.pin_slot(PI - E, beta, 1.0) - nu)
        if d > w:
            w, wE = d, E
    return w, wE


print("\n[B1] max |E + 2 pin_slot(pi - E, beta, 1) - nu| over uniform E grids (j + 0.5 offsets)")
grids = {n: [-PI + 2 * PI * (j + 0.5) / n for j in range(n)] for n in (64, 256, 1024, 4096)}
for n, g in grids.items():
    print(f"  {n:>4} E: " + "  ".join("e=%s %.3e" % (e, worst_nu(e, g)[0]) for e in (0.0549, 0.3, 0.7, 0.9, 0.99)))
g = grids[1024]
es = [0.0549 + (0.99 - 0.0549) * k / 46 for k in range(47)]
top = max(((worst_nu(e, g)[0], e) for e in es))
print(f"  47 e evenly from 0.0549 to 0.99, 1024 E: max {top[0]:.3e} at e = {top[1]:.6f}")
for e in (0.995, 0.999, 0.9999):
    print(f"  e = {e}, 1024 E: max {worst_nu(e, g)[0]:.3e}")
