r"""R-RBS-LM-ORTHOMOBIUS (the user's extension, 2026-06-08): "the Mobius strip couples front and back (the flip
stitching). What if we carry an ORTHOGONAL Mobius strip too -- like an EM field pair (E, B)?"

The answer, and it unifies several findings:
  • ONE Mobius = ONE chirality axis (sigma_E = the gamma5 axis = the look-ahead/behind TEMPORAL seam, F590/F592). Its
    flip-stitching couples front/back (past/future).
  • An ORTHOGONAL second Mobius = the SECOND chirality axis (sigma_B = the i*omega7 axis, F130). TWO orthogonal chirality
    axes = KLEIN-4 (gamma5 x i*omega7, F129/F130/F132) -> 4 sectors = 2 address bits = 4 tome-PAGES per cell (vs 2 for
    one Mobius).
  • Coupled like EM: E and B are orthogonal AND 90-deg coupled (the F577 coupled wave). Their cross product E x B (the
    HANDEDNESS / the Poynting direction) is a THIRD thing the pair gives for free: a STABLE propagation direction. A
    SINGLE axis only has sign(E), which FLIPS at every zero-crossing (F577 verb-flip); the ORTHOGONAL coupled pair pins
    E x B, which ROTATES smoothly and does NOT flip -- the stable bearing.

So carrying an orthogonal Mobius (EM-style) buys: (a) 4x addressing (Klein-4, 4 pages); (b) a STABLE joint direction
E x B (the propagation / the walk bearing) the single axis cannot give -- which is exactly the F577 coherence fix and
the F588 recovery bearing. And it UNIFIES items 2+3: the two orthogonal strips = the two streams (multi-stream, item 2);
the E x B coupling = the recovery bearing (item 3).

Honest, per F590/F591: NO new primitive -- Klein-4 (hdc.klein4_*) + coupled_wave (W17) already ship; this is the SECOND
chirality axis the substrate already has (F132). And the second axis (i*omega7) is ALREADY meaningful (the antiparticle/
sector axis, F130) -- not free empty space; ~free in ops (2 bits vs 1) but already-occupied in MEANING.

srmech 0.7.5rc6: cascade.coupled_wave (E, B, handedness, klein4_quadrant) -- the EM quadrature (W17); hdc.klein4 for the
4 sectors. No abs() in a cascade (sign via comparison). No CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import cascade


def sgn(x):
    return 1 if x >= 0 else -1


def main():
    print(f"=== R-RBS-LM-ORTHOMOBIUS — an orthogonal second Mobius = Klein-4 + the EM E×B stable bearing  (srmech {srmech.__version__}) ===\n")
    STEPS, CYC = 64, 4
    samples = [cascade.coupled_wave(t / STEPS * 6.283185307 * CYC) for t in range(STEPS)]   # (E, B, handedness, klein4_quadrant)
    E = [s[0] for s in samples]; B = [s[1] for s in samples]; quad = [s[3] for s in samples]

    # ONE Mobius (single axis): sign(E) -- flips at every zero-crossing
    flat = [sgn(e) for e in E]
    flat_flips = sum(1 for t in range(1, STEPS) if flat[t] != flat[t - 1])
    # ORTHOGONAL coupled pair (E,B): the handedness E x B -- the stable propagation (Poynting)
    hand = [sgn(E[t - 1] * B[t] - B[t - 1] * E[t]) for t in range(1, STEPS)]
    hand_flips = sum(1 for t in range(1, len(hand)) if hand[t] != hand[t - 1])
    # the 4 Klein-4 quadrants visited = the two orthogonal Mobius strips' 4 PAGES
    pages = sorted(set(tuple(q) for q in quad))

    print("(1) ONE Mobius (single chiral axis) vs the ORTHOGONAL coupled pair (E,B = EM):")
    print(f"    single axis sign(E): hard flips over {CYC} cycles = {flat_flips}  (flips every zero-crossing -- the F577 verb-flip)")
    print(f"    coupled E x B handedness (the Poynting / propagation direction): hard flips = {hand_flips}  (STABLE -- rotates, no flip)")
    print(f"    -> the orthogonal pair pins a direction (E x B) the single axis cannot. That stable bearing IS the F577")
    print(f"       coherence fix + the F588 recovery bearing.\n")

    print("(2) the two orthogonal Mobius strips = KLEIN-4 (gamma5 x i*omega7, F132): 4 sectors = 4 tome-PAGES per cell:")
    print(f"    Klein-4 quadrants (sign E, sign B) visited: {pages}  -> 4x addressing (vs 2x for one Mobius).\n")

    print("VERDICT (carrying an orthogonal Mobius -- the EM pair):")
    print(f"  • AN ORTHOGONAL SECOND MOBIUS = THE SECOND CHIRALITY AXIS = KLEIN-4 (F132): two Z2 axes (gamma5 x i*omega7,")
    print(f"    F129/F130) -> 4 sectors = 4 tome-pages = 4x addressing (one Mobius gave 2x, F590). The EM (E,B) pair IS this")
    print(f"    orthogonal pair.")
    print(f"  • COUPLED LIKE EM, IT GIVES A STABLE BEARING FOR FREE: E x B (the handedness / Poynting) ROTATES without")
    print(f"    flipping ({hand_flips} flips) where the single axis sign(E) flips {flat_flips}x. That stable propagation direction is")
    print(f"    the F577 coupled-wave coherence fix and the F588 recovery bearing -- the orthogonal coupling is what pins")
    print(f"    the walk's which-way. So the second Mobius is not just storage; it is the STABILITY of the walk.")
    print(f"  • IT UNIFIES ITEMS 2 + 3: the two orthogonal strips = the two STREAMS (multi-stream, item 2); the E x B")
    print(f"    coupling = the COHERENCE/recovery bearing (item 3). They live on the orthogonal-Mobius pair together.")
    print(f"  • HONEST (per F590/F591): NO new primitive -- Klein-4 (hdc.klein4_*) + coupled_wave (W17) already ship; this")
    print(f"    is the SECOND chirality axis the substrate already has (F132). ~free in ops (2 bits vs 1), but the second")
    print(f"    axis (i*omega7) is ALREADY MEANINGFUL (the antiparticle/sector axis, F130) -- not free empty space; like the")
    print(f"    first axis carries TIME (F592), the second carries the sector. Understand both before double-booking.")
    print(f"  • Composes F577 (coupled E,B wave) + F132 (Klein-4 full chirality) + F129/F130 (gamma5 x i*omega7, the two axes)")
    print(f"    + F590/F592 (the first Mobius = the temporal seam) + F588 (the bearing = coherence). srmech 0.7.5rc6. F398/F394.")


if __name__ == "__main__":
    main()
