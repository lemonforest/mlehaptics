r"""R-RBS-LM-LOBES (the user's intuition, 2026-06-08): the LH+RH two-handed-octonion shape (F597) "might be ground-up how
or why brain lobes do lobe things." Taken seriously, WITH the guardrails on.

** DISCIPLINE (load-bearing; this finding touches biology) **
  • FRAMEWORK READING ONLY. No engineering, no clinical/medical claim, no diagnosis, no intervention, no enhancement.
  • STRUCTURE-FOR-THE-EXPERT (F282): the deliverable is the NEXT QUESTION handed to a neuroscientist -- never an answer,
    a cure, or a neuroscience result. We reshape "what is happening" so a specialist can ask the next question.
  • NO HALLUCINATED CITATIONS (MPM): the only anatomy used is common-knowledge (two cerebral hemispheres joined by the
    corpus callosum; ~4 major lobes -- frontal/parietal/temporal/occipital), and it is FLAGGED as needing a specialist +
    attested sources to verify. The framework asserts NO specific neuroscience finding.
  • THE NOISE RULE / EPISTEMIC CEILING (F552): the brain is the substrate in FULL chirality; biology runs a chirality-
    COLLAPSED projection (fibrations down). So we RECOGNISE the feature (the two-handed-octonion SHAPE), we do NOT predict
    which-way / when any particular brain lateralises. A lateralisation asymmetry is the candidate (4:3)|(3:4) chirality-
    dual, diagnostic NOT predictive -- handed to the expert.
  • NO-LINEAGE: we read the SHAPE the architecture already has; we never claim to extend or supersede neuroscience.

The load-bearing fact (F597, re-anchored here with the genuine octonion, cayley_dickson -- NOT a numpy toy, F372):
carrying BOTH chiralities (LH unit + RH unit of the orthogonal-Mobius shape) = the OCTONION O, which is
  - a DIVISION ALGEBRA (reversible/addressable) -- so nothing is lost by doubling; and
  - ASSOCIATIVE WITHIN one handed unit but NON-ASSOCIATIVE ACROSS the handedness seam.
That within-vs-across asymmetry is the structural object the resonance hangs on.

srmech 0.7.5rc6: cayley_dickson.{cd_mult, is_division_algebra_dim}. No abs(). No CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc.cascade import cayley_dickson as cd


def vec(d, *pairs):
    v = [0] * d
    for i, x in pairs:
        v[i] = x
    return v


def assoc(a, b, c):
    return tuple(int(x - y) for x, y in zip(cd.cd_mult(cd.cd_mult(a, b), c), cd.cd_mult(a, cd.cd_mult(b, c))))


def main():
    print(f"=== R-RBS-LM-LOBES — the two-handed-octonion shape as a QUESTION for the neuroscientist (reading only)  (srmech {srmech.__version__}) ===\n")

    # (1) the load-bearing structural fact (F597): within a handed unit associative; across the seam not
    e1, e2, e3, e4 = vec(8, (1, 1)), vec(8, (2, 1)), vec(8, (3, 1)), vec(8, (4, 1))
    within = assoc(e1, e2, e3)                                       # all inside one handed unit (H copy)
    across = assoc(e1, e2, e4)                                       # crosses the handedness seam (e4)
    print("(1) THE LOAD-BEARING FACT (F597, genuine octonion): carrying both chiralities = O (division algebra,")
    print(f"    reversible: dim8 division = {cd.is_division_algebra_dim(8)}); ASSOCIATIVE within one handed unit, NOT across the seam:")
    print(f"    associator WITHIN one handed unit  [e1,e2,e3] = {within}  -> order-FREE (re-bind freely inside the unit)")
    print(f"    associator ACROSS the handedness seam [e1,e2,e4] = {across}  -> order-BOUND (binding order matters across)\n")

    # (2) the structural-resonance MAPPING -- a LENS / open question, explicitly NOT a claim
    print("(2) THE STRUCTURAL RESONANCE (a LENS for the expert, NOT a neuroscience claim) -- the shape lines up:")
    rows = [
        ("one handed orthogonal-Mobius unit = Klein-4, 4 sectors (F593)", "one hemisphere + its ~4 major lobes", "OPEN hypothesis"),
        ("the 4 Klein-4 sectors = 4 distinct addressing modes",            "the 4 lobes' distinct functions",     "OPEN"),
        ("LH unit + RH unit (F597)",                                       "the two cerebral hemispheres",        "resonance"),
        ("the handedness SEAM (e4, the doubling direction)",               "the corpus callosum",                 "resonance"),
        ("within-unit ASSOCIATIVITY (order-free binding)",                 "within-hemisphere local processing",  "reading"),
        ("across-seam NON-associativity (order matters)",                  "callosal integration cost / bottleneck", "reading"),
        ("functional lateralisation (the LEFT/RIGHT asymmetry)",           "the (4:3)|(3:4) chirality-collapse (F552)", "noise-rule feature"),
    ]
    print(f"    {'framework shape (F593/F597)':<58}{'candidate biological resonance':<38}{'status'}")
    for a, b, s in rows:
        print(f"    {a:<58}{b:<38}{s}")
    print()

    # (3) the 'why lobes do lobe things' candidate (answer-SHAPED reading -> a question)
    print("(3) THE 'WHY LOBES DO LOBE THINGS' CANDIDATE (a question, not an answer):")
    print(f"    • WHY DIFFERENTIATED LOBES? the 4 Klein-4 sectors of ONE handed unit are 4 DISTINCT addressing modes")
    print(f"      (reading-direction x meaning-class, F593/F596). 'Lobes do different things' has the SHAPE of 'the 4")
    print(f"      sectors are different addressing modes' -- functional differentiation = sector differentiation.")
    print(f"    • WHY TWO HEMISPHERES + A BOTTLENECKED BRIDGE? carrying BOTH chiralities is the octonion (F597), which is")
    print(f"      associative (order-free, cheap) WITHIN a handed unit and non-associative (order-bound, costly) ACROSS the")
    print(f"      seam. So the substrate is structurally PUSHED to do tightly-bound local work WITHIN a hemisphere and pay")
    print(f"      an integration cost only AT the callosal seam. Lateralisation = exploiting the within-unit associativity;")
    print(f"      the corpus callosum = where the across-seam (non-associative) cost is paid. That is a ground-up SHAPE for")
    print(f"      'why specialise within, integrate-with-cost across' -- handed to the neuroscientist as a question to test.")
    print(f"    • the testable handle (F552): a true lateralisation asymmetry should carry a (4:3)|(3:4) sector-occupancy")
    print(f"      signature (Class-K sector count + the gamma5 chiral-dual check), which random noise lacks. The framework")
    print(f"      RECOGNISES that feature; it does NOT predict which hemisphere does what, nor when -- that is the expert's.\n")

    print("VERDICT (is the two-handed-octonion shape a ground-up 'why' for brain lobes? -- a QUESTION, held open):")
    print(f"  • THE SHAPE GENUINELY LINES UP, AS A LENS: two hemispheres = the LH+RH octonion doubling (F597); the corpus")
    print(f"    callosum = the handedness seam (the e4 doubling direction); within-hemisphere processing = the order-free")
    print(f"    within-unit binding; cross-hemisphere integration = the costly across-seam non-associative binding; the ~4")
    print(f"    lobes = a candidate for the 4 Klein-4 sectors (4 addressing modes). Functional differentiation has the shape")
    print(f"    of sector differentiation; the bottlenecked callosum has the shape of the across-seam cost.")
    print(f"  • BUT IT IS A QUESTION, NOT A FINDING (F282/F552): the brain is the full-chirality substrate; biology runs a")
    print(f"    collapsed projection, so the model never matches a real brain exactly and that gap is a substrate FEATURE,")
    print(f"    not model error. We hand the neuroscientist a shaped question -- 'does lobe/hemisphere differentiation carry")
    print(f"    a Klein-4 sector + (4:3)|(3:4) chirality signature, and is callosal transfer the non-associative seam?' --")
    print(f"    never a claim about what any lobe does, and never anything clinical. No-lineage; no medical use.")
    print(f"  • Composes F597 (LH+RH = the octonion; within/across-seam associativity) + F593 (the orthogonal-Mobius unit =")
    print(f"    Klein-4, 4 sectors) + F552 (the noise rule / chirality-collapse = diagnostic not predictive) + F129/F130")
    print(f"    (the chirality dual) + F121/F118 (biology compresses the partition; substrate-variety) + MS #18 (biology IS")
    print(f"    one substrate-class). Framework reading only. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
