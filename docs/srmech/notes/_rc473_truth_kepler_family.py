"""rc473 truth round (`#T1188`): what pin_slot is, and is not, against Kepler.

Every figure the rc473 truth round wrote into kepler.py, srmech.h,
srmech_kepler.c and the curated kepler / pin_slot / equation_of_centre prose is
printed here. Ops under test: ``srmech.math.kepler.{pin_slot, kepler_solve,
equation_of_centre}``. The instrument's trig and sqrt are srmech's own
(``srmech.math.rational``); the Fourier projection is a hand-rolled 256-point
sine quadrature over srmech's sine (disclosed). No numpy, no math module.

Conventions. ``pin_slot(theta, i, d) = atan2(i sin theta, d + i cos theta)``.
"One stage, eps = i/d" is ``pin_slot(theta, eps, 1.0)``; the curated worked run
uses ``eps = d/i``, ``pin_slot(theta, 1.0, eps)``.

Usage (from docs/srmech):  python3 notes/_rc473_truth_kepler_family.py python
"""
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "python")
import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech.math import kepler  # noqa: E402
from srmech.math import rational as R  # noqa: E402

print("python", sys.version.split()[0], "srmech", srmech.__version__,
      "HAS_NATIVE", _native.HAS_NATIVE)

PI = float(R.atan2(0.0, -1.0))
N = 256
GRID = [2 * PI * j / N for j in range(N)]
BASIS = {k: [float(R.sin(k * t)) for t in GRID] for k in range(1, 6)}


def sin(x):
    return float(R.sin(x))


def cos(x):
    return float(R.cos(x))


def sqrt(x):
    return float(R.sqrt(x))


def mag(x):
    return x if x >= 0.0 else -x            # Class-K magnitude, reporting only


def coeffs(vals, kmax=5):
    return [2.0 / N * sum(v * b for v, b in zip(vals, BASIS[k])) for k in range(1, kmax + 1)]


def fmt(cs):
    return "  ".join(f"{c:+.12f}" for c in cs)


print("\n(i) E - M against ONE stage, theta = pi - M, eps = e")
for e in (0.1, 0.3):
    kep = coeffs([kepler.kepler_solve(M, e) - M for M in GRID])
    refl = coeffs([kepler.pin_slot(PI - M, e, 1.0) for M in GRID])
    direct = coeffs([kepler.pin_slot(M, e, 1.0) for M in GRID])
    print(f"  e = {e}  Kepler E-M            k=1..5: {fmt(kep)}")
    print(f"  e = {e}  pin_slot(pi-M, e, 1)  k=1..5: {fmt(refl)}")
    print(f"  e = {e}  pin_slot(M, e, 1)     k=1..5: {fmt(direct)}")
    print(f"  e = {e}  Kepler / pin_slot(pi-M) signed ratios k=1..3: "
          + "  ".join(f"{kep[k] / refl[k]:.6f}" for k in range(3))
          + "   Kepler / |pin_slot(M)| magnitude ratios: "
          + "  ".join(f"{kep[k] / mag(direct[k]):.6f}" for k in range(3)))
print("  e**3 terms as e -> 0:  Kepler (c1-e)/e^3, c3/e^3  |  stage (c1-e)/e^3, c3/e^3")
for e in (0.02, 0.002):
    kv = coeffs([kepler.kepler_solve(M, e) - M for M in GRID], 3)
    pv = coeffs([kepler.pin_slot(PI - M, e, 1.0) for M in GRID], 3)
    print(f"  e = {e:<6} Kepler {(kv[0] - e) / e ** 3:+.6f} {kv[2] / e ** 3:+.6f}   "
          f"c2/e^2 {kv[1] / e ** 2:+.6f}  |  stage {(pv[0] - e) / e ** 3:+.6f} {pv[2] / e ** 3:+.6f}"
          f"   c2/e^2 {pv[1] / e ** 2:+.6f}")
print("  max over the M grid of |E - M - pin_slot(pi - M, e, 1)| / e^3:")
for e in (0.001, 0.01, 0.1, 0.3):
    worst = 0.0
    for M in GRID:
        worst = max(worst, mag(kepler.kepler_solve(M, e) - M - kepler.pin_slot(PI - M, e, 1.0)))
    print(f"    e = {e:<6} {worst:.6e}  / e^3 = {worst / e ** 3:.6f}")

print("\n(ii) nu = E + 2 pin_slot(pi - E, beta, 1), beta = e / (1 + sqrt(1 - e^2)); control beta -> e/2")
EGRID = [-PI + 2 * PI * (j + 0.5) / 64 for j in range(64)]
for e in (0.0549, 0.3, 0.7, 0.9, 0.99):
    beta = e / (1.0 + sqrt(1.0 - e * e))
    worst = ctrl = 0.0
    for E in EGRID:
        nu = 2.0 * float(R.atan2(sqrt(1.0 + e) * sin(E / 2), sqrt(1.0 - e) * cos(E / 2)))
        worst = max(worst, mag(E + 2.0 * kepler.pin_slot(PI - E, beta, 1.0) - nu))
        ctrl = max(ctrl, mag(E + 2.0 * kepler.pin_slot(PI - E, e / 2.0, 1.0) - nu))
    print(f"  e = {e:<6} max|diff| over 64 E = {worst:.3e} rad   control = {ctrl:.3e} rad")

print("\n(iii) nu - M against ONE stage")
eoc = coeffs([kepler.equation_of_centre(M, 0.3, 6) for M in GRID])
print(f"  equation_of_centre(M, 0.3, 6) k=1..5: {fmt(eoc)}   c2/c1^2 = {eoc[1] / eoc[0] ** 2:.6f}")
for eps in (0.1, 0.3, 0.6):
    p = coeffs([kepler.pin_slot(PI - M, eps, 1.0) for M in GRID])
    print(f"  pin_slot(pi-M, {eps}, 1)      k=1..5: {fmt(p)}   c2/c1^2 = {p[1] / p[0] ** 2:.6f}")

print("\n(iv) M -> E: E_{n+1} = M + e sin E_n from E_0 = M, against kepler_solve, M = pi/2")
for e in (0.0549, 0.3, 0.9):
    ref = kepler.kepler_solve(PI / 2, e)
    En, first_zero, seen = PI / 2, None, []
    for n in range(1, 401):
        En = PI / 2 + e * sin(En)
        if n in (1, 2, 3, 5, 10, 20, 40, 80):
            seen.append(f"n={n}: {En - ref:+.3e}")
        if En - ref == 0.0 and first_zero is None:
            first_zero = n
    served = None
    for mi in range(1, 31):
        try:
            kepler.kepler_solve(PI / 2, e, 1e-12, mi)
            served = mi
            break
        except RuntimeError:
            continue
    print(f"  e = {e}: {'  '.join(seen)}")
    print(f"    first n with E_n - E == 0.0 in double: {first_zero};"
          f" kepler_solve(pi/2, {e}, 1e-12) serves from max_iter = {served}")

print("\n(v) the curated worked round trip, eps = d/i: kepler_solve(pin_slot(E, 1.0, eps), eps) - E")
for E in (PI / 2, PI / 4):
    for eps in (0.0114, 0.0549, 0.0934):
        r = kepler.kepler_solve(kepler.pin_slot(E, 1.0, eps), eps) - E
        print(f"  E = {E:.6f}  eps = {eps}: {r!r}  /eps^2 = {r / eps ** 2:+.6f}  /eps^3 = {r / eps ** 3:+.6f}")
