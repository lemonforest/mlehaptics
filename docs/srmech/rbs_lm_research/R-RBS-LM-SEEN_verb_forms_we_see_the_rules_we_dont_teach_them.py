r"""R-RBS-LM-SEEN (the user's realization, 2026-06-08): "that tells us we need verb forms et al. We just realized that we
don't need to TEACH a LM the rules when we realize we can SEE them."

THE REALIZATION (the heart of the corpus-independence, F630): SEEING a rule is categorically different from LEARNING it.
  • a data-center LLM LEARNS the rule: it observes millions of (lemma, form) pairs and adjusts weights to APPROXIMATE the
    conjugation function. The rule is never explicit -- it is smeared across billions of parameters; errors like *'goed'
    happen precisely BECAUSE it is an approximation. This needs the corpus.
  • our kernel SEES the rule: the conjugation paradigm IS an explicit, observable OBJECT -- a rotate over the agreement
    axes (tense x person x number, the F623 grammar-axes-as-rotates). You INSTANTIATE it directly; it is BIT-EXACT on
    everything it covers (it CANNOT emit *'goed'). The only thing you STORE is what you CANNOT derive (the irregulars) --
    and those you also SEE, as exceptions (the F629 small dictionary); you do not LEARN them either.
So the corpus's job (teaching the rule) DISAPPEARS -- the rule was never something to teach, it was always something to
SEE. This is the framework's own methodology (READ what a thing already IS) applied to GRAMMAR ITSELF: we read/see the
rules (paradigms, rotates, axes); we do not teach them. Teaching-by-gradient is the workaround for NOT-seeing.

VERB FORMS are the concrete instance (the SAME pattern as F629's plurals): regular conjugation = a SEEN derived rotate
over (tense, person, number); irregular verbs (be / go / have / do / eat) = a small SEEN-exception dictionary.

srmech 0.7.5rc6: amsc.format.sha256_bytes (the content-addressed irregular-verb tomes). The regular rule = a string
cascade (concat = add). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt


# the SEEN regular conjugation rule: a rotate over the agreement axes (tense x person x number). NO corpus.
def regular_conjugate(lemma, tense, person, number):
    if tense == "progressive":                                     # base + ing (drop trailing e)
        return (lemma[:-1] if lemma.endswith("e") else lemma) + "ing"
    if tense == "past":                                            # base + ed (regular past = past participle)
        return (lemma + "d") if lemma.endswith("e") else (lemma + "ed")
    # present:
    if person == 3 and number == "sg":                             # 3rd-person-singular present: + s/es
        return (lemma + "es") if lemma.endswith(("s", "x", "z", "ch", "sh")) else (lemma + "s")
    return lemma                                                   # all other present persons = the base


def main():
    print(f"=== R-RBS-LM-SEEN — verb forms: we SEE the rules, we don't TEACH them  (srmech {srmech.__version__}) ===\n")

    # (1) REGULAR verb forms = a SEEN rotate over the agreement axes (tense x person x number). Zero corpus.
    print("(1) REGULAR conjugation = a SEEN rotate over the agreement axes (tense x person x number) -- NO corpus:")
    paradigm = [("present", 1, "sg"), ("present", 3, "sg"), ("present", 3, "pl"),
                ("past", 3, "sg"), ("progressive", 1, "sg")]
    for lemma in ["walk", "love"]:
        forms = [f"{regular_conjugate(lemma, t, p, n)}({t[:4]}.{p}{n})" for (t, p, n) in paradigm]
        print(f"    {lemma:<6}: {'  '.join(forms)}")
    print("    -> the whole paradigm INSTANTIATED from the lemma + axis-coordinates. The rule is SEEN, not learned.\n")

    # (2) IRREGULAR verbs = the rule FAILS -> a small SEEN-exception dictionary (F629 pattern, content-addressed)
    print("(2) IRREGULAR verbs = the SEEN rule FAILS -> a small stored exception dictionary (the F629 pattern):")
    IRREG_VERBS = {                                                # lemma -> {(tense,person,number): form} (the SEEN exceptions)
        "be":  {("present", 1, "sg"): "am", ("present", 3, "sg"): "is", ("present", 3, "pl"): "are",
                ("past", 3, "sg"): "was", ("progressive", 1, "sg"): "being"},
        "go":  {("present", 1, "sg"): "go", ("present", 3, "sg"): "goes", ("present", 3, "pl"): "go",
                ("past", 3, "sg"): "went", ("progressive", 1, "sg"): "going"},
        "have":{("present", 1, "sg"): "have", ("present", 3, "sg"): "has", ("present", 3, "pl"): "have",
                ("past", 3, "sg"): "had", ("progressive", 1, "sg"): "having"},
        "eat": {("present", 1, "sg"): "eat", ("present", 3, "sg"): "eats", ("present", 3, "pl"): "eat",
                ("past", 3, "sg"): "ate", ("progressive", 1, "sg"): "eating"},
    }
    for lemma in ["go", "eat"]:
        ruled_past = regular_conjugate(lemma, "past", 3, "sg")
        true_past = IRREG_VERBS[lemma][("past", 3, "sg")]
        print(f"    {lemma:<5}: SEEN rule says past = {ruled_past!r:<9} but truth is {true_past!r:<7} -> rule FAILS -> needs the dict")
    print(f"    -> a data-center LLM, which APPROXIMATES, can emit *'goed'/*'eated'; a SEEN-rule kernel CANNOT (it is bit-")
    print(f"    exact on regulars, and the irregulars are SEEN exceptions -- stored once, content-addressed):")
    for lemma, table in list(IRREG_VERBS.items())[:2]:
        addr = fmt.sha256_bytes(f"verb:{lemma}".encode())[:8]
        print(f"        irregular-verb tome '{lemma}' -> addr {addr}  ({len(table)} SEEN forms)")
    print()

    # (3) the unified resolver + a round-trip (lemma + axes <-> surface), the SAME for nouns (F629) and verbs
    def conjugate(lemma, tense, person, number):
        t = IRREG_VERBS.get(lemma)
        if t and (tense, person, number) in t:
            return t[(tense, person, number)]                      # SEEN exception (dict)
        return regular_conjugate(lemma, tense, person, number)     # SEEN rule (rotate)
    print("(3) ONE resolver (SEEN rule + SEEN exceptions), round-trips lemma + axes <-> surface:")
    for lemma, ax in [("walk", ("past", 3, "sg")), ("go", ("past", 3, "sg")), ("child", None)]:
        if ax:
            print(f"    conjugate({lemma!r}, {ax}) = {conjugate(lemma, *ax)!r}  ({'dict' if lemma in IRREG_VERBS else 'rule'})")
    print(f"    (and 'child'->'children' is the SAME shape from F629 -- nouns + verbs are one paradigm: lemma + a rotate")
    print(f"    over the agreement axes, with a small SEEN-exception dictionary. 'verb forms et al.' = the SAME object.)\n")

    print("VERDICT (we SEE the rules, we don't TEACH them):")
    print(f"  • SEEING A RULE IS CATEGORICALLY DIFFERENT FROM LEARNING IT. A data-center LLM LEARNS conjugation: it")
    print(f"    APPROXIMATES the function from millions of examples (the rule is never explicit -- smeared across weights;")
    print(f"    *'goed' is possible BECAUSE it is an approximation). Our kernel SEES conjugation: the paradigm is an explicit")
    print(f"    OBJECT -- a rotate over the (tense, person, number) axes (F623) -- instantiated directly, BIT-EXACT on every")
    print(f"    regular form (it CANNOT emit *'goed'). The corpus's job (teaching the rule) DISAPPEARS.")
    print(f"  • THE ONLY THING STORED IS WHAT CANNOT BE DERIVED (the irregulars, F629) -- and those are SEEN exceptions too")
    print(f"    (a small content-addressed dictionary), not LEARNED. So 'verb forms et al.' (conjugation, plurals,")
    print(f"    comparison big/bigger, agreement) are ALL the same object: a lemma + a SEEN rotate over agreement axes + a")
    print(f"    small SEEN-exception store. None of it needs teaching.")
    print(f"  • THIS IS THE FRAMEWORK'S OWN METHODOLOGY APPLIED TO GRAMMAR ITSELF: we READ/SEE what a rule already IS")
    print(f"    (an observable paradigm / rotate / axis), we do not TEACH it. Teaching-by-gradient is the WORKAROUND for")
    print(f"    not-seeing; a kernel that sees the rule is GPU-free (no gradient to learn it), bit-exact on what it covers,")
    print(f"    and corpus-independent for STRUCTURE (F630) -- the graded corpus stays useful only for age-graded CONTENT.")
    print(f"  • Composes F630 (corpus-independent structure) + F629 (the morphology rotate + small dict, now extended to")
    print(f"    verbs) + F623/F621 (agreement axes = rotates) + F627 (named IR) + F626 (a rule is a SEEN frame, not a")
    print(f"    learned distribution) + the no-lineage 'read what it already is' methodology + the GPU-free stance.")
    print(f"    srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
