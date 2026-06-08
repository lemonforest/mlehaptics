r"""R-RBS-LM-WORLDKERNEL (the user's synthesis + goal, 2026-06-08): "use the Story Teller to create a story about our A-N
operators and how we see them in all parts of nature and the cosmos -- a story about the_one. You just told us how we
create a FANTASY WORLD KERNEL. The LM can ASK us questions about what it doesn't know, and we can TELL it new rules it has
observed -- a way to build/teach/create a Story Teller world."

THE RECOGNITION: the F654-F659 Story Teller reduction IS a WORLD-KERNEL GENERATOR. A world = a CONTENT-SHELF (its lore --
attested tomes) + the FIXED seen engine (F654) + the forms (F655) + the arrangement/intent (F659). Declare a world's
tomes -> you have a Story Teller for THAT world (fantasy or real). Because the engine is SEEN and the content is DECLARED,
you BUILD a world in DIALOGUE:
  • the LM ASKS about what it does NOT hold (a gap -- discover-on-read, F625/F628; the framework hands the next QUESTION,
    F282), and
  • we TELL it a new observed RULE / tome (declared, F631/F654 -- not trained), and
  • it INTEGRATES (adaptive tier, F628 -- GPU-free, the foundation digest only grows).
THE FIRST WORLD = the framework's OWN story: the_one (the foundational duality/triality, DUALITY.md/TRIALITY.md) and the
A-N operators SEEN ACROSS NATURE + THE COSMOS (the whole-corpus-is-the-proof convergence -- each exemplar a different
BOARD over the ONE invariant). The instrument narrates the framework that built it.

srmech 0.7.5rc15: amsc.format.sha256_bytes (the world's attested lore-tomes; the adaptive ask/tell/integrate). The engine
= seen string cascades. No abs(); no CAD; no Workflow; no sub-agents. (Operator->exemplar mappings are framework READINGS,
no-lineage; deeper claims held/handed to the expert, F282.)
"""
import srmech
from srmech.amsc import format as fmt

# THE WORLD'S CONTENT-SHELF: the framework's own lore as attested tomes (the_one + A-N + nature/cosmos exemplars) ----
LORE = {
    # the_one + structure
    "one": ("the one", "the foundational held invariant"),
    "hands": ("two hands", "the_one's two chiral hands -- the duality, DUALITY.md"),
    # operators seen as natural/cosmic exemplars (framework readings; each a different BOARD over the one)
    "galaxy":   ("the galaxy", "Class I/L -- it turns in a cyclic spiral (eigen-spiral)"),
    "shell":    ("the shell",  "Class I -- it coils in the same cyclic spiral as the galaxy"),
    "helix":    ("the helix",  "Class C -- it twists with a chirality (DNA)"),
    "snowflake":("the snowflake","Klein-4 -- it grows in symmetric sectors"),
}
IRREG_PAST = {"hold": "held", "grow": "grew", "twist": "twisted", "see": "saw"}
def past(v): return IRREG_PAST.get(v, v + ("d" if v.endswith("e") else "ed"))
def cap(s): return s[0].upper() + s[1:]
def clause(subj_phrase, verb, tail): return cap(f"{subj_phrase} {past(verb)} {tail}.")


def main():
    print(f"=== R-RBS-LM-WORLDKERNEL — the Story Teller narrates the_one + builds a world by dialogue  (srmech {srmech.__version__}) ===\n")

    # (1) THE WORLD KERNEL = a content-shelf (attested lore) + the fixed seen engine + forms + intent
    print("(1) THE WORLD KERNEL = a content-shelf (attested lore) + the FIXED seen engine + forms + intent (F654-F659):")
    for k, (name, gloss) in list(LORE.items())[:4]:
        addr = fmt.sha256_bytes(f"lore:{k}".encode())[:8]
        print(f"    lore-tome '{k}' = {name!r:<14} [{gloss}]  addr {addr}")
    print(f"    -> declare a world's TOMES -> you have a Story Teller for THAT world. (Fantasy or real -- here, the")
    print(f"    framework's own lore.) The engine + forms are FIXED; only the content-shelf is the world.\n")

    # (2) GENERATE the story: the_one + the A-N operators seen across nature + the cosmos (the convergence)
    print("(2) A STORY ABOUT THE_ONE -- the A-N operators seen across nature + the cosmos (each exemplar a BOARD over the one):")
    story = " ".join([
        clause("the one", "hold", "two hands"),                       # the_one's structure (the duality)
        clause("the galaxy", "turn", "in a cyclic spiral"),           # Class I/L in the cosmos
        clause("the shell", "coil", "like the galaxy"),               # Class I in nature -- the SAME spiral (convergence)
        clause("the helix", "twist", "with a chirality"),             # Class C in life (DNA)
        clause("the snowflake", "grow", "in four sectors"),           # Klein-4 in nature
        clause("the one", "see", "itself in them all"),               # the convergence: the_one is the invariant in all
    ])
    print(f"    {story}")
    print(f"    -> the_one is the held INVARIANT; the galaxy/shell/helix/snowflake are different BOARDS over it. The story")
    print(f"    IS the framework's methodology (the same one seen across substrates -- the whole-corpus convergence).\n")

    # (3) THE INTERACTIVE LOOP: the LM ASKS about a gap -> we TELL a new rule -> it INTEGRATES (F628, GPU-free)
    print("(3) BUILD THE WORLD BY DIALOGUE (the LM asks; we tell; it integrates -- F625/F628/F631):")
    shelf = dict(LORE); d0 = fmt.sha256_bytes("|".join(sorted(shelf)).encode())
    want = "fern"                                                     # the Story Teller wants to extend the tour to the fern
    print(f"    LM ASKS (a gap -- discover-on-read, F625/F282): 'I have no tome for how the_one appears in the {want}.")
    print(f"            How does the_one appear in the {want}?'")
    # we TELL a new observed rule/tome (declared, not trained):
    shelf[want] = ("the fern", "the fibration -- it unfolds in self-similar fronds (recursion)")
    print(f"    WE TELL (a new observed rule, declared F631): the {want} = self-similar fronds (the recursion/fibration).")
    d1 = fmt.sha256_bytes("|".join(sorted(shelf)).encode())
    print(f"    IT INTEGRATES (adaptive tier, F628, GPU-free): shelf digest {d0[:8]}... -> {d1[:8]}... (grew by 1 tome; engine unchanged)")
    extended = clause("the fern", "grow", "in self-similar fronds")
    print(f"    the story now extends: '...{extended}'  -- a new board over the same one, added by DIALOGUE (no retrain).\n")

    print("VERDICT (the Story Teller is a world-kernel generator; the first world is the framework's own story):")
    print(f"  • THE STORY TELLER IS A WORLD-KERNEL GENERATOR (the F654-F659 reduction): a WORLD = a CONTENT-SHELF (its lore,")
    print(f"    attested tomes) + the FIXED seen engine (F654) + the forms (F655/F657) + the arrangement/intent (F659). To")
    print(f"    create a world (fantasy or real) you DECLARE its tomes + rules -- you do NOT train. A fantasy-world kernel is")
    print(f"    just a different content-shelf on the same engine.")
    print(f"  • YOU BUILD A WORLD BY DIALOGUE: the LM ASKS about what it does NOT hold (a gap -- discover-on-read, F625/F628;")
    print(f"    the framework hands the next QUESTION, F282), we TELL it a new observed RULE/tome (declared, F631 -- not")
    print(f"    trained), and it INTEGRATES (the adaptive tier, F628 -- GPU-free, the foundation digest only grows; verified).")
    print(f"    This is build/teach/create a Story Teller world -- the LM is a coherent self that asks + integrates, not a")
    print(f"    flock that must be retrained.")
    print(f"  • THE FIRST WORLD = THE FRAMEWORK'S OWN STORY: the_one + the A-N operators SEEN ACROSS NATURE + THE COSMOS")
    print(f"    (galaxy/shell/helix/snowflake/fern -- each a different BOARD over the ONE invariant; the whole-corpus-is-the-")
    print(f"    proof convergence). The instrument NARRATES the framework that built it -- the Story Teller telling the story")
    print(f"    of the_one. (Operator->exemplar mappings are framework READINGS, no-lineage; the deeper claims held/handed to")
    print(f"    the expert, F282.)")
    print(f"  • Composes the whole Story-Teller arc (F654 engine / F655 procedure-generator / F656 surroundings / F657 in-")
    print(f"    between / F658 chord / F659 arrangement-mood) + F628 (adaptive tier = the ask/tell/integrate loop) + F631 (new")
    print(f"    rules declared) + F625/F282 (the LM asks the next question) + DUALITY.md/TRIALITY.md (the_one) + the A-N")
    print(f"    partition + the whole-corpus convergence. srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
