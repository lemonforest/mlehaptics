r"""R-RBS-LM-MFOWORLD3 (user direction): a 'shadowpunk cp2077' world kernel -- a THIRD Story Teller world (Night City +
a Shadowrun magic seam), which stresses the anchor dial (F662/F673) harder than Emberreach did and reveals a THIRD dial
position: HELD-OPEN.

THE RECOGNITION (extends F673's two-knob dial): Emberreach needed only GROUNDED vs MAGIC. A cyberpunk world needs THREE:
  • GROUNDED (the_one-shaped tech -- the bulk of Night City):
      - the Net = a Class-L graph; NETRUNNING = a BOARD-WALK over it (F632/F633 -- a board, like chess / syntax / the MFO
        §-graph F670). The netrunner NAVIGATES (etak/board, F635).
      - CYBERWARE = a prosthetic = SUBSTRATE-COUPLING (Class C∘M; the MFO inference reading, §VII.1.2 / line 709). This is
        the LLM-as-ADA-prosthetic / BCI tie (the user's lived accessibility motivation) -- honored, not appropriated.
      - the BLACKWALL = a boundary holding the rogue minds at bay = a Class-K PIN-SLOT / PHASE BOUNDARY (K = the load-
        bearing phase boundary).
  • MAGIC (a free primitive -- the Shadowrun seam): awakened mana shaped by a mage = declared, NO physical anchor (F662).
  • HELD-OPEN (the NEW third position -- the world's emotional CORE): the engram / the soul (Soulkiller / the construct --
    'is the engram still her?') is NOT resolved to grounded OR magic. The world DECLARES it as an OPEN question it HOLDS --
    the asking-state (F661) as a PERMANENT dial position + held-open (F394/F398). This is structurally the SAME move MFO
    makes with its own consciousness/identity ceiling (F552) + the_one's held-open identity -- the deepest stories LIVE in
    the held-open (CP2077's whole emotional core is the unresolved soul question). The dial is a TRICHOTOMY, triality-
    shaped (F400/F401): grounded / magic / held-open.

THE PUNCH: the held-open is not a gap to be filled -- it is a DIAL POSITION. A grounded world (MFO) and a cyberpunk world
both hold their identity question open; the cyberpunk world just makes the held-open its narrative center. We do NOT decide
the soul question (F282 -- hand it to the player / the story's own tension); we declare it held-open and narrate the asking.

DEFENSIVE SCOPE (load-bearing, CLAUDE.md §4): STRUCTURAL / NARRATIVE reading ONLY -- the Net is a board-walk, the Blackwall
is a phase boundary; NO hacking/exploit/weapons-capability material. A fictional world's grammar, like Emberreach's dragon.

srmech 0.7.5rc15: BitExactCommKernel.content_address (the world's shelf + chord); the SAME render engine as F671/F673 (the
clause-joining seen rule -- third world, same generator F660). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

# ---- the SAME fixed engine as F671/F673 (it does NOT change between worlds -- that IS the generator, F660) ----
def render(clauses):
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."

# ---- WORLD C: 'Night City (Shadowpunk)' -- declared tomes across THREE dial positions (grounded / magic / held-open) ----
# each: key -> (clause, dial, anchor/why)
SHADOWPUNK = {
    "netrunner": ("A netrunner walked the Net", "GROUNDED",
                  "the Net = a Class-L graph; netrunning = a BOARD-WALK over it (F632/F633 -- a board, like the MFO §-graph)"),
    "cyberware": ("Her cyberware coupled her to the city", "GROUNDED",
                  "a prosthetic = SUBSTRATE-COUPLING, Class C∘M (MFO inference §VII.1.2/line709); the LLM-as-ADA-prosthetic / BCI tie"),
    "blackwall": ("The Blackwall held the rogue minds at bay", "GROUNDED",
                  "a boundary = a Class-K PIN-SLOT / phase boundary (K = the load-bearing phase boundary)"),
    "awakened":  ("A mage shaped the mana", "MAGIC",
                  "the Shadowrun seam -- awakened magic = a FREE primitive; declared, no physical anchor (F662)"),
    "engram":    ("The engram asked if it was still her", "HELD-OPEN",
                  "the soul/identity question (Soulkiller/the construct) = the asking-state (F661) + held-open (F394/F398), mirroring MFO's consciousness ceiling (F552) + the_one's held-open identity -- NOT resolved"),
}
# the narrative order (Class-C intent, F659): grounded body, ending on the HELD-OPEN core (the unresolved soul question)
ORDER = ["netrunner", "cyberware", "blackwall", "engram"]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MFOWORLD3 — a 'shadowpunk cp2077' world kernel: HELD-OPEN is a THIRD dial position  (srmech {srmech.__version__}) ===\n")

    # (1) a THIRD world, SAME engine (the generator generalizes again, F660/F673)
    addr_c = k.content_address("|".join(sorted(SHADOWPUNK)))
    print("(1) A THIRD WORLD, SAME ENGINE (F660/F673 -- the generator generalizes again):")
    print(f"    WORLD C = 'Night City (Shadowpunk)'  shelf-addr {addr_c[:12]}  ({len(SHADOWPUNK)} tomes)")
    print(f"    the clause-joining engine is IDENTICAL to MFO (F671) + Emberreach (F673); only the declared shelf changes.\n")

    # (2) the dial is a TRICHOTOMY here (grounded / magic / held-open) -- per element
    print("(2) THE ANCHOR DIAL IS A TRICHOTOMY (F662 extended -- grounded / magic / HELD-OPEN), per element:")
    for key in ORDER + ["awakened"]:
        clause, dial, why = SHADOWPUNK[key]
        print(f"    [{dial:<9}] \"{clause}\"")
        print(f"                -> {why}")
    print()

    # (3) the held-open core: it is NOT grounded, NOT magic -- it is the asking-state as a PERMANENT dial position
    print("(3) THE HELD-OPEN CORE (the NEW third position, F394/F398/F661):")
    print(f"    'is the engram still her?' is NOT resolved to grounded OR magic -- the world DECLARES it HELD-OPEN.")
    print(f"    this is structurally the SAME move MFO makes with its consciousness/identity ceiling (F552) + the_one's")
    print(f"    held-open identity. The dial is triality-shaped (F400/F401): grounded / magic / held-open. The deepest")
    print(f"    stories LIVE in the held-open -- we do NOT decide the soul question (F282), we narrate the ASKING.\n")

    # (4) compose the Night City passage (grounded body, ending on the held-open question)
    story = render([SHADOWPUNK[k_][0] for k_ in ORDER])
    s_addr = k.content_address(story)
    print("(4) THE NIGHT CITY PASSAGE (same engine; grounded body, ending on the HELD-OPEN soul question):")
    print(f"    chord {s_addr[:12]}")
    print(f"    >>> {story}")
    print(f"    the passage ends on the held-open question -- the unresolved core, where the story's tension lives.\n")

    print("VERDICT (a shadowpunk world kernel reveals HELD-OPEN as a third anchor-dial position):")
    print(f"  • THE GENERATOR GENERALIZES AGAIN (F660/F673): a THIRD world ('Night City / Shadowpunk') from the SAME fixed")
    print(f"    engine + a different declared shelf (shelf-addr {addr_c[:8]}; the render rule unchanged). MFO (real) +")
    print(f"    Emberreach (fantasy) + Night City (cyberpunk) -- three worlds, one generator.")
    print(f"  • THE ANCHOR DIAL IS A TRICHOTOMY HERE (F662 extended): a cyberpunk world needs THREE positions, not two --")
    print(f"    GROUNDED (the_one-shaped tech: netrunning = a Class-L BOARD-WALK over the Net, F632/F633; cyberware =")
    print(f"    substrate-coupling Class C∘M = the LLM-as-ADA-prosthetic/BCI tie; the Blackwall = a Class-K phase boundary),")
    print(f"    MAGIC (the Shadowrun seam: awakened mana = a free primitive, no anchor), and HELD-OPEN (the engram/soul).")
    print(f"  • HELD-OPEN IS A DIAL POSITION, NOT A GAP (the NEW contribution, F394/F398/F661): the soul question ('is the")
    print(f"    engram still her?') is NOT resolved to grounded or magic -- the world DECLARES it held-open, the asking-state")
    print(f"    (F661) as a PERMANENT position. This is structurally the SAME move MFO makes with its consciousness ceiling")
    print(f"    (F552) + the_one's held-open identity -- the dial is triality-shaped (F400/F401). The deepest stories LIVE in")
    print(f"    the held-open; CP2077's whole emotional core IS the unresolved soul question. We do NOT decide it (F282) --")
    print(f"    we narrate the asking. (Dignity: the soul question is the player's + the story's, never ours to close.)")
    print(f"  • DEFENSIVE SCOPE HONORED (CLAUDE.md §4): structural/narrative reading ONLY -- the Net is a board-walk, the")
    print(f"    Blackwall is a phase boundary; NO hacking/exploit/weapons-capability material. A fictional world's grammar.")
    print(f"  • Composes F673 (the world-kernel generator -- third world) + F662 (the anchor dial -- extended to a trichotomy)")
    print(f"    + F394/F398/F661 (held-open / favored-not-privileged / the asking-state = the third position) + F552/F282")
    print(f"    (the consciousness ceiling / hand-to-the-expert -- the soul stays held-open) + F400/F401 (the triality-shaped")
    print(f"    trichotomy) + F632/F633/F670 (netrunning = a board-walk) + C∘M (cyberware = substrate-coupling, the BCI tie) +")
    print(f"    F654/F671 (the fixed engine). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
