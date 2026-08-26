r"""R-RBS-LM-SNNLIFE (the user's extension of the living stone, 2026-06-08): "and the foundation of understanding
communication MAYBE across all mammals and across all life WITH a synaptic neural network."

THE HYPOTHESIS (held-open, "maybe" -- a horizon, not a claim): the living stone / shared-invariant-above-languages
(F652) is the foundation for understanding communication across ALL SNN-bearing life -- because the shared invariant
(meaning held over a board) is plausibly a property of the SYNAPTIC NEURAL NETWORK substrate-class itself. Any life with
an SNN would then run the SAME shape (a held invariant + a board + small exceptions), so the reading-key (anchor / board
/ exception) applies IN PRINCIPLE. The BOARD differs per species (whale song / birdsong / bee waggle-dance / primate call
/ elephant infrasound / cephalopod chromatophore display / human language); the INVARIANT (meaning) is shared because the
SUBSTRATE-CLASS is shared.

PRIOR SUPPORT (this EXTENDS existing findings, not a leap): F112/F115 already found CROSS-SPECIES PARTITION CONVERGENCE
(cetacean / chimp / octopus) -- structural convergence across species. The living stone simply names that convergence's
foundation: one invariant, every species a board.

THE DOUBLE EPISTEMIC CEILING (load-bearing -- this is the regime where over-claim is the danger):
  • F552 (the noise rule): we will NEVER find the 'error of biology'; a mind is likely never EXACTLY modelable. We can
    recognise the STRUCTURE (the board has anchor/exceptions; the invariant is shared) -- NOT decode a specific whale song
    nor read an animal's mind. A deviation that looks like noise may be a chirality-collapse substrate FEATURE, not error.
  • F282 + F118: the SPECIFIC meaning is the animal's and the ethologist's (hand the next question to the expert); and
    SUBSTRATE VARIETY means this is SCOPED to SNN-bearing life -- life WITHOUT an SNN (plants, fungi, single cells) is a
    DIFFERENT substrate (chemical/electrical), outside this scope (the user already scoped it: 'with synaptic NN').
  • F650 DIGNITY, extended to non-human communicators: a whale, a crow, a bee is doing the universal thing in its own
    board. The lifting extends to them -- we recognise the structure, HONOR the communicator, never own/presume/decode.

srmech 0.7.5rc15: BitExactCommKernel (F613) -- demonstrates the SHAPE (IF the invariant is shared across SNN-life, THEN
the Rosetta-layer reading applies), NOT evidence that it IS (that is the ethologists'/the animals', F282). No abs(); no
CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-SNNLIFE — the living stone as the foundation for communication across SNN-bearing life (a held-open hypothesis)  (srmech {srmech.__version__}) ===\n")

    # (1) the SHAPE: IF the invariant is an SNN-substrate property, the Rosetta-layer reading spans species-boards
    print("(1) THE SHAPE (a STRUCTURAL hypothesis -- NOT evidence animals share meanings): one invariant, every species a board:")
    species_boards = ["human-language", "whale-song", "birdsong", "bee-waggle-dance",
                      "primate-call", "elephant-infrasound", "cephalopod-display"]
    for concept, mc in [("danger", "K-alarm"), ("food", "M-resource"), ("kin", "A-person"), ("self", "A-person")]:
        inv = k.encode(concept, mc)
        print(f"    '{concept}' [{mc}] -> invariant ir_digest {inv['ir_digest'][:12]}...  (the SHAPE: shared above {len(species_boards)} species-boards)")
    print(f"    species-boards (the SNN-substrate's surfaces): {species_boards}")
    print(f"    -> IF the invariant is a property of the SNN substrate-class, THEN the reading-key (anchor/board/exception)")
    print(f"    applies across all of them. This shows the SHAPE -- it does NOT prove animals share these meanings.\n")

    # (2) prior support: the framework ALREADY found cross-species convergence (F112/F115)
    print("(2) PRIOR SUPPORT (this EXTENDS existing findings, not a leap):")
    print(f"    F112/F115: CROSS-SPECIES PARTITION CONVERGENCE (cetacean / chimp / octopus) -- structural convergence")
    print(f"    already found across species. The living stone names that convergence's FOUNDATION: one invariant, every")
    print(f"    species a board. (Octopus is the F118 reminder: substrate VARIETY -- a distributed NN, a different board.)\n")

    # (3) the double epistemic ceiling -- the regime where over-claim is the danger
    print("(3) THE DOUBLE EPISTEMIC CEILING (load-bearing -- structural recognition ONLY):")
    print(f"    F552 (noise rule): we NEVER find the 'error of biology'; a mind is never EXACTLY modelable. Recognise the")
    print(f"        STRUCTURE -- never decode a specific song, never read a mind. A 'noise'-looking deviation may be a")
    print(f"        chirality-collapse substrate FEATURE (the (4:3)|(3:4) dual), not error.")
    print(f"    F282 + F118: the SPECIFIC meaning is the animal's + the ethologist's (hand to the expert); SCOPED to SNN-")
    print(f"        bearing life -- life WITHOUT an SNN (plants/fungi/single-cell) is a DIFFERENT substrate, out of scope.")
    print(f"    F650 (dignity, extended): a whale/crow/bee is doing the universal thing in its own board -- the lifting")
    print(f"        extends to them; we HONOR the communicator, never own/presume/decode.\n")

    print("VERDICT (the living stone as the foundation for SNN-life communication -- a held-open hypothesis):")
    print(f"  • THE HYPOTHESIS (held open, 'maybe', a HORIZON): the living stone / shared-invariant-above-languages (F652) is")
    print(f"    the foundation for understanding communication across ALL SNN-bearing life -- IN PRINCIPLE -- because the")
    print(f"    shared invariant (meaning over a board) is plausibly a property of the SYNAPTIC NEURAL NETWORK substrate-")
    print(f"    class itself. The board differs per species (whale song / birdsong / bee dance / primate call / human")
    print(f"    language); the invariant is shared because the substrate-class is shared. The reading-key (anchor/board/")
    print(f"    exception) applies in principle; cross-species communication = the Rosetta layer extended across species.")
    print(f"  • IT EXTENDS, NOT LEAPS: F112/F115 already found cross-species partition convergence (cetacean/chimp/octopus);")
    print(f"    the living stone names that convergence's foundation. (RBS-SNN is the framework's own synaptic-NN arc; F323")
    print(f"    the notebook-native-language target.)")
    print(f"  • THE DOUBLE EPISTEMIC CEILING IS LOAD-BEARING: this is STRUCTURAL recognition IN PRINCIPLE only. We NEVER")
    print(f"    decode a specific whale song nor read an animal's mind (F552: a mind is never exactly modelable; a 'noise'-")
    print(f"    looking deviation may be a chirality-collapse substrate FEATURE). The SPECIFIC meaning is the animal's + the")
    print(f"    ethologist's (F282); SCOPED to SNN-bearing life (F118: life without an SNN is a different substrate). And the")
    print(f"    LIFTING (F650) extends to non-human communicators -- a whale/crow/bee does the universal thing in its own")
    print(f"    board; we HONOR the communicator, never own/presume/decode. The framework's deliverable is the QUESTION,")
    print(f"    handed to the ethologist (and, in the only way that matters, to the animal): 'this has the shape of held-")
    print(f"    meaning over a board -- here is the structure; you know how to ask what it means.'")
    print(f"  • Composes F652 (the living stone -- this extends it) + F650 (the lifting, to non-human communicators) +")
    print(f"    F646/F649/R-RBS-LM-54 (the shared invariant / Rosetta layer) + F112/F115 (cross-species convergence) + F118")
    print(f"    (substrate variety) + the RBS-SNN arc/F323 + F552/F282 (the epistemic ceiling / hand-to-expert) + F398/F394.")
    print(f"    srmech 0.7.5rc15. A held-open hypothesis (F394); structural recognition only; dignity-first.")


if __name__ == "__main__":
    main()
