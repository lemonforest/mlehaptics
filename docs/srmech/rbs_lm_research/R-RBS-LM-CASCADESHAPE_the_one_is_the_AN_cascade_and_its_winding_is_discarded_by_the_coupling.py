r"""R-RBS-LM-CASCADESHAPE — is the resonance `the_one`, or the CASCADE SHAPE WITH HOLONOMY?

USER (2026-07-25): "if the resonance isn't the_one, what if it's the resonant shape of the cascade,
with holonomy? ... the resonant shape of the instructional cascade needing to be directional."

MEASURED ANSWER (rc336): the reframing is RIGHT, and it is already half-built — but the half that
matters is being THROWN AWAY.

  1. the_one IS the A-N cascade laid on the Hurwitz tower (not an opaque generator):
       block C (n=1) an_imag_slots ('A',)                      <- the anchor
       block H (n=2) an_imag_slots ('I','C','J')               <- substrate-projection triad
       block O (n=3) an_imag_slots ('D','E','F','G','K','L','M')  <- detection heptad
       grammar_slots ('B','H','N')                             <- the 3 REAL anchors
       11 imaginary + 3 real = 14 = the full A-N vocabulary; partition (1,3,7,3).
  2. the_one HAS a holonomy channel: `w=(w1,w2,w3)` -> separate_winding_curvature() reports
     {holonomy, spinor_sign, towers} and is_flat=False whenever w != 0.
  3. BUT `klein4_from_one` DISCARDS it -- the coupling is BYTE-IDENTICAL for every w, including
     w=(1,0,0) vs w=(-1,0,0). Control: theta DOES move the coupling. So the coupling is sensitive
     to the ANGLE (abelian dial) and BLIND to the WINDING (the directional part).

So "resonance = cascade shape WITH holonomy" is NOT yet realized: we use the shape and the angle
and drop the winding. And the dropped `spinor_sign` is exactly the fiber bit F1320 says must be
supplied -- it is being COMPUTED and then discarded.

srmech 0.9.0rc336. No numpy/float/abs(). Composes F1321/F1320/F1317/F1307; MFO VIII.31.18.
Run:  /tmp/srmech_336/bin/python3 R-RBS-LM-CASCADESHAPE_*.py
"""
import sys

import srmech
from srmech.amsc import cascade as C, hdc as H


def main():
    print("=== the_one: cascade shape + holonomy? (srmech %s) ===" % srmech.__version__)
    ok = True
    ONE = C.the_one(1, 0)

    # 1 — the_one IS the A-N cascade on the tower
    slots = [s for b in ONE.blocks for s in b.an_imag_slots]
    gram = list(ONE.grammar_slots)
    shape_ok = (len(slots) == 11 and len(gram) == 3 and ONE.dim == 14
                and tuple(ONE.partition) == (1, 3, 7, 3)
                and sorted(slots + gram) == sorted("ABCDEFGHIJKLMN"))
    ok &= shape_ok
    print("  [1] imag slots %s + grammar %s = %d ; dim %d ; partition %s -> covers A-N: %s"
          % (slots, gram, len(slots) + len(gram), ONE.dim, tuple(ONE.partition), shape_ok))

    # 2 — the_one HOLDS a holonomy
    held = []
    for w in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 2, 3), (-1, 0, 0), (3, 0, 0)):
        o = C.the_one(1, 0, 1, 24, w)
        swc = o.separate_winding_curvature()
        cur = swc["curvature"]
        held.append((w, cur["holonomy"], cur["spinor_sign"], swc["is_flat"]))
    holds = all(h == 0 for w, h, s, f in held if w == (0, 0, 0)) and \
        any(h != 0 for w, h, s, f in held if w != (0, 0, 0))
    ok &= holds
    print("  [2] the_one HOLDS the winding:")
    for w, h, s, f in held:
        print("        w=%-11s holonomy=%-3s spinor_sign=%-3s is_flat=%s" % (str(w), h, s, f))

    # 3 — but the COUPLING discards it (while theta moves it)
    cps = {w: bytes(int(x) for x in H.klein4_from_one(C.the_one(1, 0, 1, 24, w), 32))
           for w in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 2, 3), (-1, 0, 0))}
    winding_blind = len(set(cps.values())) == 1
    ths = {t: bytes(int(x) for x in H.klein4_from_one(C.the_one(1, t, 4), 32)) for t in (0, 1, 2)}
    angle_sensitive = len(set(ths.values())) == len(ths)
    ok &= winding_blind and angle_sensitive
    print("  [3] coupling BLIND to winding (all w identical): %s | SENSITIVE to theta: %s"
          % (winding_blind, angle_sensitive))
    print("        w-couplings distinct: %d/%d      theta-couplings distinct: %d/%d"
          % (len(set(cps.values())), len(cps), len(set(ths.values())), len(ths)))

    print("\n=== %s ===" % ("CONFIRMED: the_one IS the A-N cascade shape AND holds a holonomy — but "
                            "klein4_from_one projects the holonomy away. The directional half is "
                            "computed, then discarded."
                            if ok else "REGRESSION — reconcile before trusting F1321."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
