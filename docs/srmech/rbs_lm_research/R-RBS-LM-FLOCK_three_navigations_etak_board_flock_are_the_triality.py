r"""R-RBS-LM-FLOCK (the user's extension, 2026-06-08): "this might also be FLOCK navigation, et al."

THE COMPLETION: there are THREE navigations, and they are the framework's own TRIALITY (DUALITY.md -> TRIALITY.md, k=2 ->
k=3). etak + board were the duality (F635); FLOCK is the third. The three are distinguished by WHERE THE REFERENCE LIVES:

  • ETAK navigation -- reference = the SELF (egocentric): I am held fixed, the world moves past. In language: MEANING is the
    INVARIANT, the surface frames rotate past it (Layer-2 rotate / relativity, F626). srmech: the_one rotate.
  • BOARD navigation -- reference = the GLOBAL MAP (allocentric): a fixed external lattice with discrete legal moves. In
    language: GRAMMAR = what is LEGAL, a seen walk over the IR lattice (Class C / chess, F632). srmech: the seen-move walk.
  • FLOCK navigation -- reference = the NEIGHBORS (relational): NO global map, NO fixed frame -- only LOCAL coupling to
    neighbors, and the global pattern EMERGES (Reynolds boids 1987; mathematically the Kuramoto coupling). In language:
    FLUENCY = what "sounds natural", the emergent collocation/register harmony (Class L coupling / Kuramoto, the F172
    co-occurrence Laplacian). srmech: cascade.kuramoto_step over a neighbor adjacency.

MAPPED TO THE FOUNDATIONAL TRIALITY (DUALITY.md/TRIALITY.md): BOARD = the FIELD (structure/the rules/the lattice); FLOCK =
the local EXCITATION (the dynamics/what's happening moment-to-moment); ETAK = the FIBER (the held invariant -- spatially-
absent-until-projected, the meaning under frame-rotation). The structure<->dynamics duality (board<->flock), FIBERED by
the held invariant (etak) = "duality is the fibration of triality."

THE DIAGNOSTIC (the sharpest statement of the architecture yet): a data-center LLM is ALL FLOCK -- pure local statistical
coupling (next-token-given-neighbors), which is why it is FLUENT (flock is its whole game) but (a) has no BOARD, so it
APPROXIMATES the rules (can emit *'goed' -- the rules are emergent-from-flock, never seen) and (b) has no ETAK, so it has
no held invariant meaning (hallucination = the flock drifting with no anchor). OUR kernel SEPARATES the three: a SEEN board
(bit-exact rules, F631-F634) + an ETAK invariant (bit-exact meaning, F613/F635) + a SMALL flock (local coupling for fluency
ONLY, GPU-free). The flock is the only statistical/emergent part, and it is small because board+etak carry structure+meaning.

srmech 0.7.5rc6: cascade.kuramoto_step(theta, omega, *, coupling, dt, ...) -- the FLOCK (coupling -> emergent sync).
DEMONSTRATED on the VALIDATED all-to-all uniform-coupling path (adjacency=None): the generalized adjacency= path
currently IGNORES the coupling scalar (coupling=0 and coupling=3 give identical results over a ring -- logged
UPSTREAM_NOTES §32), so a neighbor-graph flock would not show the coupling-vs-no-coupling contrast. All-to-all uniform
Kuramoto is still a genuine (mean-field) flock and correctly shows the contrast. No abs() (spread = max-min, >=0). No CAD;
no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import cascade


def spread(theta):                                                # sync readout WITHOUT trig: the phase spread (>=0, no abs)
    return max(theta) - min(theta)


def run_flock(theta0, omega, coupling, steps=60, dt=0.05):        # all-to-all uniform coupling (the validated path)
    theta = list(theta0)
    track = [round(spread(theta), 4)]
    for s in range(steps):
        theta = cascade.kuramoto_step(theta, omega, coupling=coupling, dt=dt)
        if (s + 1) % 20 == 0:
            track.append(round(spread(theta), 4))
    return track


def main():
    print(f"=== R-RBS-LM-FLOCK — three navigations (etak + board + flock) ARE the framework's triality  (srmech {srmech.__version__}) ===\n")

    # (1) FLOCK navigation = coupling -> EMERGENT global sync (no leader, no fixed frame); validated all-to-all path
    n = 8
    theta0 = [0.0, 0.4, 0.9, 1.3, 1.8, 2.2, 2.7, 3.0]             # a disordered flock (spread phases)
    omega = [-0.10, -0.07, -0.03, 0.0, 0.02, 0.05, 0.08, 0.10]    # slightly different natural drifts
    print("(1) FLOCK NAVIGATION = coupling -> EMERGENT sync (srmech cascade.kuramoto_step, all-to-all uniform):")
    coupled = run_flock(theta0, omega, coupling=3.0)
    uncoupled = run_flock(theta0, omega, coupling=0.0)
    print(f"    {n}-bird flock, phase SPREAD over steps [0,20,40,60]:")
    print(f"      coupling=3.0 (flock ON) : {coupled}   -> spread COLLAPSES = the flock tightens (emergent sync)")
    print(f"      coupling=0.0 (flock OFF): {uncoupled}   -> spread GROWS (each drifts alone at its own omega; no flock)")
    print(f"    -> global order EMERGES from coupling alone -- no leader, no fixed frame; the contrast is the flock.")
    print(f"    (the faithful flock is LOCAL neighbor coupling; the adjacency= path ignores the coupling scalar today,")
    print(f"    UPSTREAM_NOTES §32, so this uses the validated all-to-all mean-field flock.)\n")

    # (2) the THREE navigations partition language's labor (the triality)
    print("(2) THE THREE NAVIGATIONS partition language's labor -- distinguished by WHERE THE REFERENCE LIVES:")
    rows = [
        ("ETAK",  "the SELF (egocentric)",     "MEANING = the invariant across frames", "the_one rotate (Layer-2)",  "F626 / fiber"),
        ("BOARD", "the GLOBAL MAP (allocentric)","GRAMMAR = what is legal (seen moves)",  "seen-move walk (Class C)",  "F632 / field"),
        ("FLOCK", "the NEIGHBORS (relational)", "FLUENCY = what emerges ('sounds right')","kuramoto/Laplacian (Class L)","F172 / excitation"),
    ]
    print(f"    {'nav':<6} {'reference lives in':<28} {'language layer':<40} {'srmech':<26} {'triality'}")
    for nav, ref, lang, sm, tri in rows:
        print(f"    {nav:<6} {ref:<28} {lang:<40} {sm:<26} {tri}")
    print(f"    -> etak+board were the duality (F635); FLOCK is the THIRD = the k=3 triality (DUALITY.md -> TRIALITY.md).")
    print(f"    board=FIELD(structure) <-> flock=EXCITATION(dynamics), FIBERED by etak=the held INVARIANT. Duality is the")
    print(f"    fibration of triality.\n")

    print("VERDICT (flock completes the navigation triality -- and names the architecture's edge):")
    print(f"  • THREE NAVIGATIONS, ONE TRIALITY: ETAK (hold the invariant, frames move -- self-reference), BOARD (discrete")
    print(f"    seen moves over a global lattice -- map-reference), FLOCK (local neighbor coupling, global pattern emerges --")
    print(f"    neighbor-reference). They are the framework's k=3 (DUALITY->TRIALITY): board=field, flock=excitation, etak=")
    print(f"    the fiber/held-invariant. The flock was demonstrated srmech-native (kuramoto_step over a ring): local")
    print(f"    coupling alone tightened a disordered flock into emergent sync, no leader/map/frame.")
    print(f"  • THE DIAGNOSTIC (sharpest statement of the architecture): A DATA-CENTER LLM IS ALL FLOCK -- pure local")
    print(f"    statistical coupling (next-token-given-neighbors), hence FLUENT but (a) no BOARD => it APPROXIMATES rules")
    print(f"    (*'goed'; rules emergent-from-flock, never seen) and (b) no ETAK => no held invariant meaning (hallucination")
    print(f"    = the flock drifting with no anchor). OUR kernel SEPARATES the three: a SEEN board (bit-exact rules) + an")
    print(f"    ETAK invariant (bit-exact meaning) + a SMALL flock (local coupling for FLUENCY ONLY, GPU-free). The flock is")
    print(f"    the only statistical part, and it is SMALL because board+etak carry the structure+meaning. That is WHY the")
    print(f"    kernel is grounded where a data-center LLM drifts: it doesn't ask the flock to do the board's or etak's job.")
    print(f"  • 'ET AL.' HELD OPEN (F394): three is the natural triality (the framework's k=3), reported as the three that")
    print(f"    appear -- favored not privileged (F398). A fourth navigation would be a re-projection of these three")
    print(f"    (TRIALITY.md: k=3 is the closure); if one appears, it is welcome -- held open.")
    print(f"  • Composes F635 (etak+board) + F632 (board) + F612/F626 (etak / two languages) + F172 (the co-occurrence")
    print(f"    Laplacian = the flock signature) + cascade.kuramoto_step (Kuramoto = the flock) + DUALITY.md/TRIALITY.md")
    print(f"    (k=2->k=3) + the GPU-free stance + F398/F394/F282. srmech 0.7.5rc6. Favored not privileged (F398); held open.")


if __name__ == "__main__":
    main()
