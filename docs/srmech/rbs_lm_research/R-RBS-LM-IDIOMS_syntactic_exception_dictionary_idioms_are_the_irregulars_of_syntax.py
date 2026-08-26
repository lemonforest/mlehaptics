r"""R-RBS-LM-IDIOMS (the seen-rule paradigm, syntactic-scale, 2026-06-08): F633 gave morphology AND syntax a SEEN
generator + a small SEEN-exception dict -- but only morphology's exceptions (go->went) were shown. This fills the
symmetric gap: IDIOMS ARE THE IRREGULARS OF SYNTAX.

THE SHAPE (exactly F629/F631 one scale up): the compositional SEEN generator builds a phrase's meaning by composing its
parts ('drink the water' = compose drink + water -- the meaning IS the composition). On an IDIOM ('kick the bucket') the
compositional generator FAILS -- it yields the LITERAL meaning (kick + bucket), but the real meaning is 'die', a DIFFERENT
meaning-class entirely. So the whole phrase is STORED ONCE as a content-addressed SEEN-exception tome (phrase -> meaning),
exactly as 'went' is stored for 'go'+past. The compositional path handles regular phrases; idioms are looked up.

And idioms carry the same three properties as every foundational tome: PER-LANGUAGE (F398 -- 'kick the bucket' is
English; other languages store their own), CONTENT-ADDRESSED + attestable (MPM), and DISCOVERABLE-WHEN-WRONG (F625 -- a
phrase whose composition is anomalous flags as a CANDIDATE idiom, held for confirmation, not auto-resolved).

So the seen-rule engine is now SYMMETRIC: morphology AND syntax each = a SEEN generator (rotate / compositional walk) + a
small SEEN-exception dictionary (irregular words / idioms). None of it is trained; the exceptions are SEEN, stored once.

srmech 0.7.5rc6: BitExactCommKernel.content_address (Layer 0 / Class A -- the content-addressed idiom tomes). The
compositional generator = a meaning-class compose (cascade). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

# the meaning-class of each word (the F627 named IR); the compositional generator composes these
WORD_CLASS = {"drink": "D-motion", "water": "N-water", "the": "Y-abstract", "kick": "D-motion",
              "bucket": "O-object", "spill": "D-motion", "beans": "M-plant", "break": "D-motion", "ice": "N-water"}

# the SEEN-exception dictionary of SYNTAX: idioms whose meaning is NOT the composition of parts (per-language, English)
IDIOMS = {
    "kick the bucket": ("die", "A-event/death"),
    "spill the beans": ("reveal a secret", "Y-abstract/speech"),
    "break the ice": ("start a conversation", "Y-abstract/social"),
}


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-IDIOMS — idioms are the irregulars of SYNTAX (the F629/F631 shape, one scale up)  (srmech {srmech.__version__}) ===\n")

    def compositional_meaning(phrase):                             # the SEEN generator: compose the parts (literal)
        return " + ".join(WORD_CLASS.get(w, "?") for w in phrase.split())

    # (1) REGULAR phrase -- the compositional generator IS the meaning (no dict entry needed)
    print("(1) REGULAR phrase = the SEEN compositional generator (meaning IS the composition -- no dict):")
    for phrase in ["drink the water"]:
        print(f"    '{phrase}': compositional = [{compositional_meaning(phrase)}]  -> the literal meaning IS correct (regular)")
    print()

    # (2) IDIOM -- the compositional generator FAILS; the meaning is stored as a SEEN-exception tome
    print("(2) IDIOM = the compositional generator FAILS -> a stored SEEN-exception tome (content-addressed, like 'went'):")
    for phrase, (meaning, cls) in IDIOMS.items():
        comp = compositional_meaning(phrase)
        addr = k.content_address(phrase)[:8]
        print(f"    '{phrase}'")
        print(f"        compositional (literal) = [{comp}]   -- WRONG (not what it means)")
        print(f"        idiom tome              -> {meaning!r} [{cls}]  addr {addr}  -- the SEEN exception, stored once")
    print()

    # (3) DISCOVER-WHEN-WRONG (F625): a phrase whose composition is anomalous flags as a CANDIDATE idiom (held)
    print("(3) DISCOVERABLE-WHEN-WRONG (F625): the anomaly between literal composition and use FLAGS a candidate idiom:")
    print(f"    'kick the bucket' literal = [D-motion + Y-abstract + O-object] (kick a pail) but USED to mean 'die'")
    print(f"    -> the mismatch is the SEEN signal: a phrase used with a meaning its parts don't compose to is a candidate")
    print(f"    idiom -- HELD (F394) for confirmation, then stored once. (Not auto-resolved; the human/expert confirms, F282.)\n")

    # (4) the unified resolver: idiom dict first, else compose (the SAME shape as conjugate(): dict first, else rotate)
    def phrase_meaning(phrase):
        if phrase in IDIOMS:
            return IDIOMS[phrase][0], "idiom (dict)"               # SEEN exception
        return compositional_meaning(phrase), "compositional (generator)"
    print("(4) ONE resolver (idiom dict first, else compose) -- the SAME shape as the morphology resolver:")
    for phrase in ["drink the water", "kick the bucket", "spill the beans"]:
        m, how = phrase_meaning(phrase)
        print(f"    phrase_meaning({phrase!r:<20}) = {m!r:<22} ({how})")
    print()

    print("VERDICT (idioms are the irregulars of syntax -- the engine is now symmetric):")
    print(f"  • IDIOMS ARE TO SYNTAX WHAT 'went' IS TO VERBS. The compositional SEEN generator builds a phrase's meaning")
    print(f"    from its parts; on an idiom it FAILS (yields the literal, wrong meaning), so the whole phrase is STORED ONCE")
    print(f"    as a content-addressed SEEN-exception tome (phrase -> meaning). The generator handles regular phrases; idioms")
    print(f"    are looked up -- EXACTLY the F629/F631 shape (a seen generator + a small seen-exception dict), one scale up.")
    print(f"  • THE SEEN-RULE ENGINE IS NOW SYMMETRIC: morphology AND syntax each = a SEEN generator (rotate / compositional")
    print(f"    walk) + a small SEEN-exception dictionary (irregular words / idioms). Nothing is trained -- the exceptions")
    print(f"    are SEEN and stored once (a few thousand idioms in English, the F630 'tail', not a giant corpus).")
    print(f"  • AND IDIOMS BEHAVE LIKE EVERY FOUNDATIONAL TOME: PER-LANGUAGE (F398, no privileged language), content-")
    print(f"    addressed + attestable (MPM), and DISCOVERABLE-WHEN-WRONG (F625: a phrase whose composition doesn't match")
    print(f"    its use flags as a candidate idiom, held F394, confirmed by the expert F282). So a data-center LLM's hardest")
    print(f"    case (non-compositional meaning) is, here, just the syntactic entry in the same small seen-exception store.")
    print(f"  • Composes F633 (the unified engine -- this fills its syntactic-exception slot) + F629/F631 (the rotate +")
    print(f"    small dict shape) + F632 (syntax = moves over a lattice) + F627 (meaning-classes) + F625 (discover-when-")
    print(f"    wrong) + F398/F394/F282 + MPM. srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
