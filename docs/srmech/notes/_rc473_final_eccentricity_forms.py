"""rc473 final round (`#T1188`): which ratio each shipped "eccentricity" sentence means.

Two shipped spellings name an eccentricity for the same op with RECIPROCAL ratios:

* the curated ``kepler.pin_slot`` worked comment: "the ratio eps = d / i IS the
  mechanism's eccentricity", for ``pin_slot(theta, 1.0, 0.0549)`` (i = 1, d = 0.0549);
* the curated ``rational.atan2`` example input: "ε = i/d = 0.0549 (Moon
  eccentricity)", for ``pin_slot(1.0, 0.0549, 1.0)`` (i = 0.0549, d = 1).

(Corrected at the rc473 instrument round, `#T1188`. This bullet named the
``rational.sin`` / ``cos`` / ``atan2`` examples as carrying "eps = i/d = 0.0549 (Moon
eccentricity)". At ``52371629a`` all three carry ``i/d = 0.0549``, but only
``rational.atan2``'s carries "(Moon eccentricity)"; ``cos`` reads "(eps = i/d =
0.0549)" and ``sin`` "ε = i/d = 0.0549" with no eccentricity label. Measured with
``git show 52371629a:docs/srmech/python/srmech/introspect/_tool_docs_curated.py``
piped to ``grep -n -i "moon eccentricity"`` (one line, ``rational.atan2``) and to
``grep -n "i/d = 0.0549"`` (three lines: ``atan2``, ``cos``, ``sin``).)

``pin_slot(theta, i, d) = atan2(i sin theta, d + i cos theta)``. Printed here, for each
form, the first three sine harmonics of the quantity that form produces, so the
sentence can say which ratio is the first-harmonic amplitude of what:

* DEPARTURE form ``pin_slot(theta, 1.0, eps) - theta`` (eps = d / i);
* STAGE form ``pin_slot(theta, eps, 1.0)`` (eps = i / d);

plus, at the Moon's e = 0.0549, Kepler's ``E(M) - M`` harmonics for comparison, the two
single values the examples print, and the departure at ``theta = pi/2``.

Ops under test: ``srmech.math.kepler.pin_slot`` and ``kepler_solve``. The quadrature is
hand-rolled over ``srmech.math.rational.sin`` on ``theta_j = 2 pi j / 256``. No numpy, no
math module, no abs().

Usage (from docs/srmech):  python3 notes/_rc473_final_eccentricity_forms.py python
"""
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "python")
import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech.math import kepler as K  # noqa: E402
from srmech.math import rational as R  # noqa: E402

print("python", sys.version.split()[0], "srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)
PI = float(R.atan2(0.0, -1.0))
N = 256
GRID = [2 * PI * j / N for j in range(N)]
BASIS = {k: [float(R.sin(k * t)) for t in GRID] for k in (1, 2, 3)}


def harmonics(values):
    return [2.0 / N * sum(v * b for v, b in zip(values, BASIS[k])) for k in (1, 2, 3)]


def fmt(cs):
    return "  ".join("%+.12f" % c for c in cs)


E_MOON = 0.0549
print("\ngrid theta_j = 2 pi j / %d; harmonics k = 1..3" % N)
def departure(t, eps):
    """``pin_slot(t, 1.0, eps) - t`` on the principal branch.

    ``pin_slot`` answers in (-pi, pi] while ``t`` runs over [0, 2 pi), so for
    ``t > pi`` the raw difference is the departure minus 2 pi. A first run of this
    script took the raw difference and printed c1 = +3.94 at eps = 0.0549: the
    wrap, not the mechanism. The branch is restored with a Class-K comparison.
    """
    d = K.pin_slot(t, 1.0, eps) - t
    return d + 2 * PI if d < -PI else d


for eps in (E_MOON, 0.3):
    dep = harmonics([departure(t, eps) for t in GRID])
    stage = harmonics([K.pin_slot(t, eps, 1.0) for t in GRID])
    print("eps = %-6s DEPARTURE pin_slot(t, 1.0, eps) - t : %s   c1 + eps = %+.3e"
          % (eps, fmt(dep), dep[0] + eps))
    print("eps = %-6s STAGE     pin_slot(t, eps, 1.0)     : %s   c1 - eps = %+.3e"
          % (eps, fmt(stage), stage[0] - eps))
kep = harmonics([K.kepler_solve(M, E_MOON) - M for M in GRID])
print("e   = %-6s Kepler    E(M) - M                  : %s   c1 - e   = %+.3e"
      % (E_MOON, fmt(kep), kep[0] - E_MOON))
print("\nthe single values the examples print")
print("pin_slot(1.0, 0.0549, 1.0)        =", repr(K.pin_slot(1.0, 0.0549, 1.0)))
print("pin_slot(pi/2, 1.0, 0.0549) - pi/2 =", repr(K.pin_slot(PI / 2, 1.0, 0.0549) - PI / 2))
print("pin_slot(pi/2, 0.0549, 1.0)        =", repr(K.pin_slot(PI / 2, 0.0549, 1.0)))
