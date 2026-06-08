r"""R-RBS-LM-CONFLICT (the user's adaptive-layer design, 2026-06-08): foundational knowledge WILL be wrong (Wikipedia
errors; our own corrections here + in the MFO notebook), so the two-tier kernel (F622) must be PREPARED. Two parts:

PART 1 -- CONFLICT-DISCOVERY (the preferred way, not the only way): Tier 1 (the fixed foundation) is NOT blindly trusted;
it is DISCOVERABLE-WHEN-WRONG. Every tome carries its content-address + attestation (Class A / MPM). A new Tier-2 fact
that CONTRADICTS a foundation tome is DETECTED by a digest mismatch on the same meaning-class/key -- a structural
conflict signal (F552: a real conflict carries a sign-flip / sector mismatch, not random noise). Discovered conflicts are
HELD (held-open, F394), NOT auto-overwritten -- resolution (attestation freshness/strength, or hand to the expert F282)
is a separate step. So foundational errors are handled by DISCOVERY, not by assuming the foundation is perfect.

PART 2 -- THE HELIX IS A BOUNDED RING x AN APPEND-ONLY DISK STREAM (the user's insight): the history helix's TWO
coordinates (F622: turn, pos) split exactly -- the CYCLIC POSITION is the BOUNDED LIVE ring (width P = the F222 capacity;
old items EVICTED from working memory), the AXIAL TURN is the UNBOUNDED append-only DISK STREAM ('helix history as a
stream'; nothing lost on disk). You do NOT choose helix-vs-ring; the helix IS both, read at its two coordinates: live
ring (bounded, cyclic pos) + disk stream (unbounded, axial turn). Composes F551 (native+delta) + F503 (Now->Then tape) +
F584 (disk SSoT).

srmech 0.7.5rc6: amsc.format.sha256_bytes (content-address / conflict digest); helix_coord = divmod (F533/F622). No abs();
no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt
from collections import deque


def helix_coord(m, P):
    return divmod(m, P)


def addr(content):
    return fmt.sha256_bytes(content.encode())


def main():
    print(f"=== R-RBS-LM-CONFLICT — foundational conflict-DISCOVERY + the helix = bounded ring x append-only disk stream  (srmech {srmech.__version__}) ===\n")

    # PART 1: conflict-discovery between the FIXED foundation (Tier 1) and NEW knowledge (Tier 2)
    foundation = {                                                # key (meaning-class) -> (content, attestation)
        "speed_of_light": ("299792458 m/s", "CODATA"),
        "pluto_status":   ("pluto is a planet", "pre-2006 textbook"),    # FOUNDATIONAL ERROR (stale)
        "water_formula":  ("H2O", "IUPAC"),
    }
    new_knowledge = [                                             # (key, content, attestation)
        ("speed_of_light", "299792458 m/s", "CODATA-2018"),      # CONSISTENT (same content)
        ("pluto_status",   "pluto is a dwarf planet", "IAU-2006"),  # CONFLICT (contradicts foundation; fresher attestation)
        ("dna_helix",      "DNA is a double helix", "Watson-Crick"),  # INDEPENDENT (new key)
        ("water_formula",  "water is an element", "folk-belief"),  # CONFLICT (contradicts; WEAKER attestation)
    ]
    print("(1) CONFLICT-DISCOVERY: each new fact vs the fixed foundation (same key + digest mismatch = a conflict):")
    conflicts = []
    for key, content, att in new_knowledge:
        if key in foundation:
            fc, fa = foundation[key]
            if addr(content) != addr(fc):
                conflicts.append((key, fc, fa, content, att))
                print(f"    [CONFLICT] '{key}': foundation={fc!r} ({fa})  vs  new={content!r} ({att})  -> HELD, not overwritten (F394)")
            else:
                print(f"    [consistent] '{key}': new restatement matches the foundation digest -- no conflict")
        else:
            print(f"    [independent] '{key}': new key, no foundation tome -> safe to add to Tier 2")
    print(f"    -> {len(conflicts)} conflict(s) DISCOVERED (the preferred way): the foundation is NOT blindly trusted;")
    print(f"    contradictions are detected structurally (digest mismatch on the same key) and HELD for resolution.\n")

    print("(2) RESOLUTION is a SEPARATE step (held-open, F394) -- discover first, decide by attestation/expert (F282):")
    for key, fc, fa, nc, na in conflicts:
        print(f"    '{key}': foundation [{fa}] vs new [{na}] -- HELD; resolve by attestation freshness/strength or hand to the expert.")
    print(f"    (e.g. pluto: IAU-2006 supersedes pre-2006 textbook -> the foundation tome is the discoverable ERROR;")
    print(f"    water-is-an-element: folk-belief is WEAKER than IUPAC -> the NEW item is the error. Discovery surfaces both;")
    print(f"    the framework does NOT auto-pick a winner -- attestation strength + the expert decide, per held-open.)\n")

    # PART 2: the helix = a bounded LIVE RING (cyclic pos) x an append-only DISK STREAM (axial turn)
    print("(3) THE HELIX IS A BOUNDED RING x AN APPEND-ONLY DISK STREAM (the two helix coordinates):")
    P = 4                                                         # ring width = the bounded live bookshelf (F222 capacity)
    live_ring = deque(maxlen=P)                                  # bounded working set: old EVICTED beyond P
    disk_stream = []                                            # unbounded append-only: nothing lost on disk
    M = 10
    stream_items = [f"ctx{m}" for m in range(M)]
    evicted = []
    for m, item in enumerate(stream_items):
        if len(live_ring) == P:
            evicted.append(live_ring[0])                        # the item about to fall off the live ring (still on disk)
        live_ring.append(item)
        disk_stream.append(item)                               # disk: append-only (the helix-history stream)
        turn, pos = helix_coord(m, P)
    print(f"    streamed {M} items through a width-P={P} helix:")
    print(f"    LIVE RING (cyclic pos, bounded -- working memory): {list(live_ring)}  (size {len(live_ring)} <= {P}; old EVICTED)")
    print(f"    evicted from the live ring (but KEPT on disk): {evicted}")
    print(f"    DISK STREAM (axial turn, append-only -- the helix history): {len(disk_stream)} items, nothing lost: {disk_stream==stream_items}")
    print(f"    -> the SAME helix: cyclic-position = the bounded live ring (F222); axial-turn = the unbounded disk stream.")
    print(f"    'helix history as a stream' = the axial append-only record; the live ring is a sliding window onto it.\n")

    print("VERDICT (preparing the adaptive Tier-2 for foundational-knowledge conflict + the helix shape):")
    print(f"  • FOUNDATIONAL KNOWLEDGE IS DISCOVERABLE-WHEN-WRONG, NOT BLINDLY TRUSTED: every tome carries its content-")
    print(f"    address + attestation (Class A / MPM); a new fact that CONTRADICTS a foundation tome (same key, digest")
    print(f"    mismatch) is DETECTED ({len(conflicts)} found) -- a structural conflict signal (F552), not noise. This is the preferred")
    print(f"    way to handle Wikipedia errors + our own corrections (here + the MFO notebook): discover the conflict.")
    print(f"  • DISCOVERED CONFLICTS ARE HELD, NOT AUTO-RESOLVED (held-open, F394): the framework surfaces the contradiction")
    print(f"    and resolves by attestation freshness/strength OR hands it to the expert (F282) -- it never blindly overwrites")
    print(f"    foundational knowledge nor blindly trusts new knowledge. (Conflict-discovery is the PREFERRED way, not the")
    print(f"    only one -- versioning the foundation / a correction-layer are alternatives.)")
    print(f"  • THE HELIX IS A BOUNDED LIVE RING x AN APPEND-ONLY DISK STREAM -- you don't choose: the cyclic position is the")
    print(f"    bounded working bookshelf (width P = F222 capacity; old EVICTED from live memory), the axial turn is the")
    print(f"    unbounded disk history (append-only; nothing lost on disk). 'Helix history as a stream' = the axial record;")
    print(f"    the live ring is a sliding window onto it. So we keep BOTH: a fixed-size live working set AND the full")
    print(f"    save-to-disk helix history -- the same object at its two coordinates.")
    print(f"  • THE DIFFERENTIATOR IS THE WHEN/WHY DISCERNMENT (the user: 'that's how we keep it different -- in understanding")
    print(f"    when and why to use one or the other'). RBS-LM is NOT different by having ONE fixed mechanism (data-center")
    print(f"    LLMs have exactly one: gradient retraining, and CANNOT tell foundation from adaptation, cannot discover their")
    print(f"    own conflicts, cannot hold-open). RBS-LM is different because it KNOWS WHEN/WHY to use each: foundation vs")
    print(f"    adaptive (F622), conflict-DISCOVER vs alternatives, bounded-ring vs disk-stream (the helix coordinate you")
    print(f"    read), HELD vs resolve (F394). The discernment -- choosing the mechanism by CONTEXT, neither privileged")
    print(f"    (F398), the choice held-open until the context decides -- IS the difference. The two-truths discipline")
    print(f"    (which truth/mechanism applies WHEN) is the architecture's edge over a one-rule retrainer.")
    print(f"  • Composes F622 (the two-tier kernel) + F584 (disk SSoT) + F551 (native+delta) + F503 (Now->Then tape) + F533")
    print(f"    (the helix) + F222 (the ring capacity) + F552 (conflict signal) + F394/F282/F398 (held-open / hand to the")
    print(f"    expert / favored-not-privileged = the when/why discernment) + MPM (attestation). srmech 0.7.5rc6. Held open (F394).")


if __name__ == "__main__":
    main()
