"""rc473 truth repair 1 — the curated literal edits, each required to match exactly once.

1. Three duplicate path pairs the citation rewrite left ("(p.py / p.py)").
2. T1-B1: pin_slot's WHEN clause ("the SAME shape").
3. B2:    pin_slot's example why ("to four significant figures at three ... eccentricities").
4. B1:    equation_of_centre's "to within 2.0e-15 rad for e from 0.0549 to 0.99".
Figures in 3 and 4 are the output of notes/_rc473_truth_repair1_kepler.py (pure cell).
Line endings preserved (newline='').  Usage: python r1_curated_literal.py <curated.py>
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(sys.argv[1])
text = P.open(encoding="utf-8", newline="").read()
orig = text
R = [
    ("It REUSES oct_mult via oct_bind (octonion.py / octonion.py) rather than",
     "It REUSES oct_mult via oct_bind (srmech/math/octonion.py) rather than"),
    ("and the Weyl projectors (srmech/physics/qm/relativistic.py / srmech/physics/qm/relativistic.py). clifford_res",
     "and the Weyl projectors (srmech/physics/qm/relativistic.py). clifford_res"),
    ("weyl_left_projector / weyl_right_projector (srmech/physics/qm/relativistic.py / srmech/physics/qm/relativistic.py) and charge_co",
     "weyl_left_projector / weyl_right_projector (srmech/physics/qm/relativistic.py) and charge_co"),
    # the rewrite dropped this pair's first line (``:191``, not qpoly_promote's def line)
    # and left its follow-on, which then read as the pair's only location
    ("``qpoly_promote`` / ``qpoly_project`` (``srmech/math/carrier_ladder.py`` / ``:229``)",
     "``qpoly_promote`` / ``qpoly_project`` (``srmech/math/carrier_ladder.py``)"),
    ("or demonstrating that a bronze linkage and an orbital equation are the SAME shape.",
     "or comparing a bronze linkage with Kepler's equation, which one stage matches through e**2 and departs from at e**3."),
    ("The bronze transform's departure at theta = pi/2 lands on -eps to four significant figures at three different eccentricities - agreement at first order.",
     "The bronze transform's departure at theta = pi/2 agrees with -eps to two significant figures at eps = 0.0549 and 0.0934, and to five at eps = 0.0114 - agreement at first order: measured at rc473, the departure sits 0.3316 to 0.3333 eps**3 above -eps, the eps**3/3 term of -atan(eps)."),
    ("agreed with the true anomaly nu to within 2.0e-15 rad for e from 0.0549 to 0.99.",
     "agreed with the true anomaly nu at double precision, which is not a bound: the largest difference was 1.998e-15 rad over 64 uniformly spaced E at e = 0.0549, 0.3, 0.7, 0.9 and 0.99, 2.220e-15 rad over 4096 E at e = 0.99, and 1.377e-13 rad over 1024 E at e = 0.9999."),
]
for old, new in R + [tuple(x) for x in (sys.argv[2:] and [])]:
    n = text.count(old)
    assert n == 1, (n, old[:100])
    text = text.replace(old, new)
    print("x1", old[:96])
print("chars", len(orig), "->", len(text), "CRLF", orig.count("\r\n"), "->", text.count("\r\n"))
P.open("w", encoding="utf-8", newline="").write(text)
print("WROTE", P)
