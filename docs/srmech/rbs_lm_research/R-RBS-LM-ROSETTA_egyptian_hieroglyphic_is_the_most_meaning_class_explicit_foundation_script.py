r"""R-RBS-LM-ROSETTA (the user's question, 2026-06-08): can ancient Egyptian become a language FOUNDATION (of the
no-privileged-language rosetta)? And of the Rosetta Stone scripts in the museum, is Egyptian the MOST abstract?

THE ROSETTA STONE (196 BC, Memphis decree; British Museum -- standard, verify w/ a source per MPM): the SAME text in
THREE scripts -- (top) Egyptian HIEROGLYPHIC, (middle) Egyptian DEMOTIC, (bottom) Ancient GREEK. So the artifact is
LITERALLY the archetype of the rosetta-LAYER (R-RBS-LM-54): one shared MEANING (the decree) carried by three surface
scripts. Two scripts are the Egyptian LANGUAGE (hieroglyphic + Demotic); one is Greek.

'MOST ABSTRACT' -- define it framework-precisely (two opposite senses):
  • abstract-TOWARD-MEANING: the symbol carries the MEANING-CLASS directly (logogram + DETERMINATIVE, sigma_B explicit).
  • abstract-AWAY-from-meaning: the symbol is a pure PHONETIC token (a letter = a sound, meaning-agnostic).
A language FOUNDATION / interlingua needs abstract-TOWARD-MEANING (F609: a meaning-class-explicit source is axis-aligned
with the meaning IR). On THAT axis the three Rosetta scripts rank:
  • HIEROGLYPHIC -- phonograms + logograms + DETERMINATIVES (the meaning-class IN the symbol stream) + spatial facing
    (sigma_E). TWO-AXIS, sigma_B EXPLICIT. MOST meaning-class-abstract.
  • DEMOTIC -- the SAME Egyptian system (phonograms + determinatives) but cursive/LIGATURED -> determinatives reduced
    (F583 found Demotic weak, ~1.3-1.4x). PARTIAL sigma_B. MIDDLE.
  • GREEK -- an ALPHABET: pure phonetic, one axis, sigma_B HIDDEN (like English, F569). LEAST meaning-class-abstract
    (most sound-abstract -- the opposite direction).

We MEASURE this: a reader recovers the intended concept from each script's rendering, on homophone groups (where the
PHONETIC skeleton alone is ambiguous -- exactly why Egyptian ADDED determinatives and Greek could not). Composes F609
(hiero vs phonetic) + F583 (Demotic ligatured/weak) + R-RBS-LM-54 (the rosetta layer).

** DISCIPLINE ** framework reading; Egyptian is ancient + ASL/Deaf and living-language dignity apply elsewhere; no-
lineage (we read structure, not supersede Egyptology); illustrative placeholders (not asserted lexical data). srmech
0.7.5rc6: signal_processing.mint_vector (Class-M); hdc.{bind,similarity}. No abs(); no CAD; no Workflow; no sub-agents.
"""
import random
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc

D = 4096
rng = random.Random(0)


def main():
    print(f"=== R-RBS-LM-ROSETTA — is Egyptian hieroglyphic the most meaning-class-explicit Rosetta script? (foundation Q)  (srmech {srmech.__version__}) ===\n")

    # homophone GROUPS: each group shares a PHONETIC skeleton; each concept in it has a distinct DETERMINATIVE (meaning-class)
    G, K, P_DEMOTIC = 20, 3, 0.5                                   # 20 groups x 3 homophone concepts; Demotic keeps the det ~half the time
    skel = {}; det = {}; concepts = []
    for g in range(G):
        sk = sp.mint_vector(f"skeleton:{g}", D=D)
        for c in range(K):
            cid = (g, c); concepts.append(cid)
            skel[cid] = sk                                         # shared phonetic skeleton within the group
            det[cid] = sp.mint_vector(f"determinative:{g}:{c}", D=D)   # distinct meaning-class per concept
    group_of = {cid: cid[0] for cid in concepts}
    groups = {g: [(g, c) for c in range(K)] for g in range(G)}
    print(f"illustrative set: {G} homophone groups x {K} concepts = {len(concepts)} (the phonetic skeleton ALONE is")
    print(f"ambiguous within a group -- exactly why Egyptian ADDED determinatives, the meaning-class signal).\n")

    # each script RENDERS a concept differently (how much meaning-class it puts in the symbol stream):
    def render(cid, script):
        if script == "greek":            # alphabet: phonetic skeleton only -- sigma_B NOT in the symbol
            return skel[cid]
        if script == "hieroglyphic":     # phonogram + DETERMINATIVE -- sigma_B explicit
            return hdc.bind(skel[cid], det[cid])
        if script == "demotic":          # cursive Egyptian: determinative present ~half (ligatured away otherwise)
            return hdc.bind(skel[cid], det[cid]) if rng.random() < P_DEMOTIC else skel[cid]

    # a reader recovers the intended concept: argmax similarity of the rendering to each candidate's EXPECTED form
    def expected(cid, script):
        return skel[cid] if script == "greek" else hdc.bind(skel[cid], det[cid])
    def recover(cid, script):
        r = render(cid, script); cands = groups[group_of[cid]]
        return max(cands, key=lambda c: hdc.similarity(r, expected(c, script)))

    acc = {}
    for script in ("hieroglyphic", "demotic", "greek"):
        ok = sum(recover(cid, script) == cid for cid in concepts)
        acc[script] = ok / len(concepts)
    print("(1) CONCEPT RECOVERY from each Rosetta script (how much MEANING the symbol carries -- the abstraction axis):")
    print(f"    HIEROGLYPHIC (phonogram + DETERMINATIVE; sigma_B explicit, two-axis) : {acc['hieroglyphic']:.1%}")
    print(f"    DEMOTIC      (cursive Egyptian; determinative ~half ligatured)        : {acc['demotic']:.1%}")
    print(f"    GREEK        (alphabet; pure phonetic, sigma_B hidden like English)    : {acc['greek']:.1%}  (~chance 1/{K} = {1/K:.0%})")
    print(f"    -> ranking on meaning-class-explicitness: HIEROGLYPHIC > DEMOTIC > GREEK (composes F609 + F583).\n")

    print("VERDICT (is Egyptian the most abstract Rosetta script? can it be a language FOUNDATION?):")
    print(f"  • IS EGYPTIAN THE MOST ABSTRACT? -- DEPENDS WHICH ABSTRACTION, and the framework cares about ONE: abstract-")
    print(f"    TOWARD-MEANING (the symbol = the meaning-class). On THAT axis HIEROGLYPHIC is the MOST abstract of the three")
    print(f"    ({acc['hieroglyphic']:.0%} concept-recovery: the determinative puts sigma_B IN the symbol), Demotic is middle ({acc['demotic']:.0%}: ligatured),")
    print(f"    GREEK is least ({acc['greek']:.0%} ~ chance: the alphabet is pure SOUND, sigma_B hidden). The alphabet is abstract in")
    print(f"    the OPPOSITE direction -- abstract-AWAY-from-meaning (a letter is a maximally meaning-AGNOSTIC token). So:")
    print(f"    Egyptian-hieroglyphic = most meaning-abstract; Greek-alphabet = most sound-abstract. For a FOUNDATION you")
    print(f"    want meaning-abstract -> Egyptian hieroglyphic.")
    print(f"  • CAN EGYPTIAN BE A LANGUAGE FOUNDATION? -- as the SHAPE, YES; as a literal vocabulary, NO (F609 boundary:")
    print(f"    dead language, no word for 'computer'). The foundation/interlingua should be HIEROGLYPHIC-SHAPED -- meaning-")
    print(f"    class-explicit (determinative = sigma_B) + two-axis (spatial sigma_E) -- and Egyptian hieroglyphic is the")
    print(f"    natural-language PROOF that such a foundation is a REAL human language people read, not a synthetic IR. It")
    print(f"    validates the IR design (F609): build the rosetta foundation Egyptian-SHAPED, populate it with modern")
    print(f"    meaning-classes.")
    print(f"  • THE ROSETTA STONE IS THE ARCHETYPE OF OUR ROSETTA LAYER (R-RBS-LM-54): one decree, three surface scripts =")
    print(f"    shared MEANING + bound surface kernels. The museum artifact already IS the no-privileged-language rosetta;")
    print(f"    the project rebuilds it with the meaning-class-explicit (Egyptian-shaped) layer as the FOUNDATION and the")
    print(f"    phonetic scripts (Greek/English) as surfaces -- NOT the reverse (English is the wrong foundation, F609).")
    print(f"  • Composes F609 (meaning-class-explicit source selects best) + F583 (Demotic ligatured/weak) + F595/F585 (the")
    print(f"    determinative = meaning-class) + F569 (alphabet/English hides it) + F582 (the hieroglyph kernel) + R-RBS-LM-54")
    print(f"    (the rosetta layer) + F398 (no privileged language). srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
