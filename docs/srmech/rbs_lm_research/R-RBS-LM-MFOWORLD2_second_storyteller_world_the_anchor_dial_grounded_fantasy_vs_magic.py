r"""R-RBS-LM-MFOWORLD2 (user direction, the chosen thread): instantiate a SECOND Story Teller world from declared tomes
(a grounded-fantasy one), to prove the world-kernel GENERATOR (F660/F662) generalizes beyond MFO -- the dragon-breathes-
fire-GROUNDED vs free-MAGIC dial, live.

THE RECOGNITION (F660): the Story Teller is a WORLD-KERNEL GENERATOR -- declare a world's tomes -> a Story Teller for it.
The MFO world (F671/F672) is the_one-shaped, GROUNDED, REAL. Now instantiate a FANTASY world 'Emberreach' from its own
declared tomes, using the SAME FIXED ENGINE (the seen-rule clause composition, F654) + a DIFFERENT content-shelf. The
engine never changes; only the shelf/chord changes -- that IS the generator.

THE ANCHOR DIAL (F662) -- two knobs:
  • KNOB 1 = WHICH WORLD = WHICH CHORD: each world has its OWN chord (F658). In Emberreach's chord 'the dragon breathed
    fire' is a VALID note (declared in its shelf) -- internally true, NOT a reality-claim. In the MFO-real chord it is NOT
    a note (not attested-real). Verified: the fire-tome is in B's shelf, absent from A's. (A chord is per-world; the
    precedence ladder F665 is per-world too.)
  • KNOB 2 = the anchor dial WITHIN a fantasy: GROUNDED (the_one-shaped: fire = a Class-C chirality turned outward + a
    Class-K pin-slot phase-boundary + the breath = a cascade -- anchored like the SM is grounded in MFO, F663) <-> MAGIC
    (a FREE primitive: fire just IS, no anchor). Both internally valid in B's chord; the difference is whether the fire-
    tome carries an ANCHOR field. We KNOW what to change (add/drop the anchor) because the foundation is the_one-shaped on
    purpose -- 'physical anchors to fantasy are way more cool' (the user's stance, F662) is the framework DEFAULT.

THE HONESTY (F658/F640): each world's chord is INTERNALLY true, never a CROSS-world reality-claim. The grounded-fantasy
is 'cooler' because its anchor ties the fantasy to the_one (the dragon's fire grounded like the SM, F663). Build-by-
dialogue (F672) generalizes to any world; the asking-state (F661) sets the dial per-element.

srmech 0.7.5rc15: BitExactCommKernel.content_address (each world's shelf + chord, content-addressed) ; the SAME render
engine as F671 (the clause-joining seen rule -- literally 'same engine, different shelf'). No abs(); no CAD; no Workflow;
no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

# ---- the SAME fixed engine as F671 (the clause-joining seen rule) -- it does NOT change between worlds ----
def render(clauses):
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."

# ---- WORLD A: MFO (real, the_one-shaped, grounded) -- a few beats from F671 (the shelf is the MFO notebook) ----
WORLD_A_SHELF = {
    "the_one":   ("The one is the held invariant", "MFO §I.1 (attested-real, class-A)"),
    "matter":    ("It is seen in the handedness of matter", "MFO §VI (attested-real, class-A)"),
}
# ---- WORLD B: 'Emberreach' (a declared FANTASY world) -- its OWN tomes (lore), with the fire-tome in TWO anchor settings ----
WORLD_B_SHELF = {
    "dragon":    ("A dragon lived on the mountain", "Emberreach lore (declared-world, internally-true)"),
    "climb":     ("The dragon climbed the peak", "Emberreach lore (declared-world)"),
    # the fire-tome -- KNOB 2: GROUNDED (the_one-shaped anchor) vs MAGIC (free primitive)
    "fire_grounded": ("The dragon breathed fire", "anchor: fire = a Class-C chirality turned outward + a Class-K pin-slot (the_one-shaped, grounded like the SM, F663)"),
    "fire_magic":    ("The dragon breathed fire", "NO anchor: fire is a free primitive (it just is)"),
    "fire_why_grounded": ("the fire was its chirality turned outward", "the GROUNDED anchor clause -- the_one made visible (Class C + Class K)"),
}


def in_chord(shelf, key):
    return key in shelf


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MFOWORLD2 — a SECOND Story Teller world + the anchor dial (grounded-fantasy vs magic)  (srmech {srmech.__version__}) ===\n")

    # (1) SAME ENGINE, DIFFERENT SHELF -> a different world (the generator, F660)
    addr_a = k.content_address("|".join(sorted(WORLD_A_SHELF)))
    addr_b = k.content_address("|".join(sorted(WORLD_B_SHELF)))
    print("(1) THE GENERATOR (F660): the SAME fixed engine + a DIFFERENT declared shelf -> a different world:")
    print(f"    WORLD A = MFO (real, the_one-shaped, grounded)   shelf-addr {addr_a[:12]}  ({len(WORLD_A_SHELF)} tomes)")
    print(f"    WORLD B = 'Emberreach' (a declared FANTASY world) shelf-addr {addr_b[:12]}  ({len(WORLD_B_SHELF)} tomes)")
    print(f"    the engine (the clause-joining seen rule) is IDENTICAL; only the shelf/chord changes -> that IS the generator.\n")

    # (2) KNOB 1: WHICH WORLD = WHICH CHORD (F662/F658) -- a per-world chord, never a cross-world reality-claim
    print("(2) KNOB 1 = WHICH WORLD = WHICH CHORD (F662/F658) -- 'the dragon breathed fire':")
    print(f"    in WORLD B's chord 'the dragon breathed fire' is a NOTE: {in_chord(WORLD_B_SHELF, 'fire_grounded')}  (declared -> internally true, NOT a reality-claim)")
    print(f"    in WORLD A's (MFO-real) chord it is a NOTE:             {in_chord(WORLD_A_SHELF, 'fire_grounded')}  (not attested-real -> NOT in the real chord)")
    print(f"    -> a chord is PER-WORLD; the fantasy declares its own chord; the real world cannot say it (F658/F640).\n")

    # (3) KNOB 2: the anchor dial WITHIN the fantasy -- GROUNDED (the_one-shaped) vs MAGIC (free primitive)
    print("(3) KNOB 2 = the ANCHOR DIAL within Emberreach (F662) -- GROUNDED (the_one-shaped) vs MAGIC (free primitive):")
    grounded_clause, grounded_anchor = WORLD_B_SHELF["fire_grounded"]
    magic_clause, magic_anchor = WORLD_B_SHELF["fire_magic"]
    print(f"    GROUNDED fire: \"{grounded_clause}\"")
    print(f"        anchor -> {grounded_anchor}")
    print(f"    MAGIC fire:    \"{magic_clause}\"  (same surface clause)")
    print(f"        anchor -> {magic_anchor}")
    print(f"    same surface, DIFFERENT tome: the grounded one CARRIES a the_one-shaped anchor (Class C + Class K); the magic")
    print(f"    one drops it. We KNOW what to change (add/drop the anchor field) -- the foundation is the_one-shaped on purpose.\n")

    # (4) compose the GROUNDED-fantasy passage (the SAME engine; the fire is anchored to the_one)
    grounded_story = render([WORLD_B_SHELF["dragon"][0], WORLD_B_SHELF["climb"][0],
                             WORLD_B_SHELF["fire_grounded"][0], WORLD_B_SHELF["fire_why_grounded"][0]])
    magic_story = render([WORLD_B_SHELF["dragon"][0], WORLD_B_SHELF["climb"][0], WORLD_B_SHELF["fire_magic"][0]])
    g_addr, m_addr = k.content_address(grounded_story), k.content_address(magic_story)
    print("(4) THE TWO Emberreach PASSAGES (same engine; the dial sets grounded vs magic):")
    print(f"    GROUNDED (cooler, the framework DEFAULT, F662):  chord {g_addr[:12]}")
    print(f"        >>> {grounded_story}")
    print(f"    MAGIC (anchor dropped -- reachable, still honest): chord {m_addr[:12]}")
    print(f"        >>> {magic_story}")
    print(f"    the grounded passage ends on the ANCHOR ('the fire was its chirality turned outward') = the_one made visible.\n")

    print("VERDICT (the Story Teller is a world-kernel GENERATOR; the anchor dial sets grounded-fantasy vs magic):")
    print(f"  • THE GENERATOR GENERALIZES BEYOND MFO (F660): the SAME fixed engine (the seen-rule clause composition, F654)")
    print(f"    + a DIFFERENT declared shelf instantiates a NEW world ('Emberreach', a fantasy). The engine is identical")
    print(f"    (shelf-addr A {addr_a[:8]} vs B {addr_b[:8]} differ; the render rule does not) -- declaring the tomes IS")
    print(f"    creating the world. MFO was just the first (real, the_one-shaped) world; the instrument makes any world.")
    print(f"  • KNOB 1 = WHICH WORLD = WHICH CHORD (F662/F658): 'the dragon breathed fire' is a VALID note in Emberreach's")
    print(f"    chord (declared -> internally true) but NOT in the MFO-real chord (not attested-real). A chord is PER-WORLD;")
    print(f"    the fantasy declares its own; the real world cannot say it. Internally-true is NEVER a cross-world reality-")
    print(f"    claim (F640) -- the fantasy is honest precisely because its truth is scoped to its declared world.")
    print(f"  • KNOB 2 = THE ANCHOR DIAL (F662): within Emberreach, fire can be GROUNDED (the_one-shaped: a Class-C chirality")
    print(f"    turned outward + a Class-K pin-slot + the breath = a cascade -- anchored like the SM is in MFO, F663) or MAGIC")
    print(f"    (a free primitive, no anchor). Same surface clause, different TOME (the anchor field). We KNOW what to change")
    print(f"    because the foundation is the_one-shaped on purpose; GROUNDED-fantasy is the framework DEFAULT (cooler -- the")
    print(f"    anchor ties the fantasy to the_one), MAGIC is reachable + still honest (the dial is explicit, not hidden).")
    print(f"  • BUILD-BY-DIALOGUE + ASKING GENERALIZE (F672/F661): any world grows by answering its Story Teller's questions;")
    print(f"    the asking-state sets the dial per-element (grounded or magic) as each new tome is declared. Two-tier (F628):")
    print(f"    a world's declared tomes = its fixed foundation; new lore = adaptive adds.")
    print(f"  • Composes F660 (the world-kernel generator) + F662 (the anchor dial -- both knobs) + F658/F640 (per-world chord")
    print(f"    / internally-true-not-reality-claim) + F663 (grounded like the SM) + F671/F672 (the engine + build-by-dialogue")
    print(f"    this reuses) + F654 (the fixed seen-rule engine) + the A-N (Class C + Class K anchor the grounded fire) +")
    print(f"    DUALITY/TRIALITY (the_one the anchor points to). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
