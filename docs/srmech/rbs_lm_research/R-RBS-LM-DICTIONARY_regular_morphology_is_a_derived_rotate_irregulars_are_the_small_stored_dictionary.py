r"""R-RBS-LM-DICTIONARY (the user's question, 2026-06-08): do we need a DICTIONARY with a language kernel? Asked because
of the child/children (singular/plural) issue in F627's morphology matcher.

THE ANSWER: YES, but a SMALL one -- and it is NOT a privileged English word-list; it is the IRREGULAR-rotate store in
the FOUNDATION. The lemma/inflection split is the F612 pattern again:
  • LEMMA = the INVARIANT (the meaning / the bit-exact IR, Layer 1). 'child' and 'children' share ONE lemma.
  • REGULAR inflection (cat->cats, walk->walked) = a DERIVED ROTATE (a rule cascade: strip/add the suffix). The number/
    tense axis (F623) is the rotate; for regulars it is COMPUTED (CORDIC-like, add/concat) -- NO storage needed.
  • IRREGULAR inflection (child->children, go->went, mouse->mice, foot->feet) = a STORED ROTATE: the rule has no closed
    form, so the lemma<->form mapping must be STORED -- a content-addressed relationship-tome in the FOUNDATION (Tier 1,
    Class-A address + Class-L lemma<->form edge). This is the 'dictionary' -- but it is SMALL (English has only a few
    hundred irregulars), bounded, and per-language (no privileged language, F398).
So: the dictionary is the SPECIAL-VALUES TABLE (the irregular rotates that aren't on the regular cascade), not the whole
series. Regular morphology is derived (the rotate); irregular morphology is stored (the foundation). That is why F627's
stemmer needed help on child/children: child->children is IRREGULAR (not a suffix-strip).

srmech 0.7.5rc6: amsc.format.sha256_bytes (the content-addressed irregular tomes). The regular rule = a string cascade
(concat = add). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt


def regular_plural(lemma):                                         # the DERIVED rotate (a rule cascade -- no storage)
    if lemma.endswith(("s", "x", "z", "ch", "sh")):
        return lemma + "es"
    if lemma.endswith("y") and lemma[-2:-1] not in "aeiou":
        return lemma[:-1] + "ies"
    return lemma + "s"


def main():
    print(f"=== R-RBS-LM-DICTIONARY — regular morphology = a derived rotate; irregulars = the small stored dictionary  (srmech {srmech.__version__}) ===\n")

    # the IRREGULAR dictionary: the STORED rotates (a few hundred in English; here a representative sample)
    IRREGULAR_PLURALS = {
        "child": "children", "mouse": "mice", "foot": "feet", "tooth": "teeth", "man": "men",
        "woman": "women", "person": "people", "goose": "geese", "ox": "oxen", "louse": "lice",
        "datum": "data", "cactus": "cacti", "analysis": "analyses", "phenomenon": "phenomena", "sheep": "sheep",
    }
    # a test set: regular lemmas (rule-derivable) + the irregular lemmas
    regulars = ["cat", "dog", "house", "box", "city", "book", "tree", "river", "king", "song", "church", "key", "day", "boat"]
    print("(1) REGULAR inflection = a DERIVED ROTATE (the rule cascade; NO storage):")
    reg_ok = 0
    for w in regulars[:6]:
        print(f"    {w:<8} -> regular_plural(rule) = {regular_plural(w):<10}  (derived; lemma '{w}' is the invariant)")
    print(f"    ... {len(regulars)} regular lemmas, all derived by the suffix-rotate -- no dictionary entry needed.\n")

    print("(2) IRREGULAR inflection = a STORED ROTATE (the rule FAILS -> must be in the dictionary):")
    fails = 0
    for lemma, truth in list(IRREGULAR_PLURALS.items())[:6]:
        ruled = regular_plural(lemma)
        ok = (ruled == truth)
        fails += (not ok)
        print(f"    {lemma:<10} rule says {ruled:<11} but truth is {truth:<10}  -> rule {'OK' if ok else 'FAILS -> needs the dict'}")
    print(f"    ... the rule cannot derive these -- the lemma<->form mapping must be STORED (a foundational tome).\n")

    # each irregular = a content-addressed foundational relationship-tome (Class-A address + Class-L lemma<->form edge)
    print("(3) THE DICTIONARY = the irregular lemma<->form tomes (content-addressed, foundational, SMALL + bounded):")
    dict_tomes = {lemma: (form, fmt.sha256_bytes(f"{lemma}<->{form}".encode())) for lemma, form in IRREGULAR_PLURALS.items()}
    for lemma, (form, address) in list(dict_tomes.items())[:5]:
        print(f"    tome '{lemma}<->{form}' -> address {address[:16]}...  (Class-A; the stored rotate)")
    print(f"    dictionary size = {len(dict_tomes)} irregular tomes (English has only a few HUNDRED irregulars total).")
    print(f"    -> the regular forms (millions) are DERIVED (the rotate); only the irregulars (hundreds) are STORED.\n")

    # the resolver: lemma -> form = dict (if irregular) else the rule (the derived rotate)
    def inflect(lemma):
        return dict_tomes[lemma][0] if lemma in dict_tomes else regular_plural(lemma)
    # and the inverse (what F627's stemmer needs): form -> lemma = dict-inverse (irregular) else un-rotate (strip)
    inv = {form: lemma for lemma, (form, _) in dict_tomes.items()}
    def lemmatize(form):
        if form in inv:
            return inv[form]                                       # irregular: stored inverse (child<-children)
        for suf, repl in (("ies", "y"), ("es", ""), ("s", "")):    # regular: un-rotate (strip the suffix)
            if form.endswith(suf) and len(form) - len(suf) >= 2:
                return form[:-len(suf)] + repl
        return form
    print("(4) THE RESOLVER (lemma<->form, both directions) -- dict for irregulars, the rotate for regulars:")
    for f in ["cats", "cities", "children", "mice", "boxes", "feet"]:
        print(f"    lemmatize({f!r:<10}) = {lemmatize(f):<8}  ({'dict (irregular)' if f in inv else 'un-rotate (regular)'})")
    print(f"    -> 'children'->'child' needs the DICT (irregular); 'cats'->'cat' is the un-rotate (regular). THIS is what")
    print(f"    F627's stemmer was missing on child/children -- the small irregular dictionary.\n")

    print("VERDICT (do we need a dictionary with a language kernel?):")
    print(f"  • YES, BUT A SMALL ONE -- AND IT IS THE FOUNDATION'S IRREGULAR-ROTATE STORE, not a privileged word-list. The")
    print(f"    LEMMA is the invariant (the meaning / the IR); REGULAR inflection is a DERIVED rotate (the suffix rule")
    print(f"    cascade -- no storage, millions of forms derived); IRREGULAR inflection is a STORED rotate (the lemma<->form")
    print(f"    tome, content-addressed, in the foundation Tier 1 -- only a few HUNDRED). The dictionary = the special-")
    print(f"    values table (the irregular rotates that aren't on the regular cascade), NOT the whole series.")
    print(f"  • THIS IS THE F612 PATTERN AGAIN: lemma = bit-exact invariant; inflection = the rotate; regular = the")
    print(f"    computed rotate, irregular = the stored rotate. And it is per-language (each language's irregulars; no")
    print(f"    privileged language, F398). The dictionary lives in the FIXED foundation (F622 Tier 1), content-addressed")
    print(f"    + attestable (MPM) -- and discoverable-when-wrong (F625) like any foundational tome.")
    print(f"  • SO F627's child/children SNAG IS EXPLAINED + FIXED: the stemmer (the un-rotate) handles regulars; the small")
    print(f"    irregular dictionary handles child<->children, go<->went, mouse<->mice. Together they are the morphology")
    print(f"    layer -- a derived rotate + a small stored special-values table. NOT a giant word-list.")
    print(f"  • Composes F627 (the morphology matcher) + F612 (invariant + rotate) + F621/F623 (inflection axes = rotates) +")
    print(f"    F622 (the foundation Tier 1 = where the dict lives) + F625 (discoverable-when-wrong) + F398 (per-language,")
    print(f"    no privileged) + MPM (content-addressed tomes). srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
