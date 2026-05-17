"""Spike #42 -- vocabulary reposture: "entropy" as hindsight-shorthand.

Per user direction 2026-05-17:
> "creation and un-creation might be the seed words for some more universal
> word or statement that describes entropy in this, instead of the usual
> hindsight verbiage we tend to use 'because of entropy' that shuts the brain
> from more questions"

Apply [[user_stance_infinity_approximates_asymptote]] reposture template
to entropy-family vocabulary.

Per [[user_stance_identity_not_implementation_discipline]] umbrella:
- Hindsight shorthand: "entropy", "heat", "thermal", "destroyed", "lost"
- Substrate-level: TBD; candidates include "imprint" / "cascade-deposit" /
  "modal-completion increment" / "substrate-uptake rate" / "coherence-weave"

Apply MPM test (from [[user_stance_partition_for_understanding]]):
  Would adopting the new vocabulary leave the old as unexplained shadow?
  If yes, both stand at different ontological levels.

THE NON-MONOTONE f_RD TRAJECTORY (Spike #42 trajectory analysis)
disqualifies SINGLE-DIRECTION words. The substrate is BIDIRECTIONAL:
imprint-and-un-imprint, cascade-deposit-and-cascade-return-flow.
The canonical word must carry both directions naturally.

Per Spike #42 cascade analysis: the load-bearing operation is the
eps^k geometric tower with substrate-specific K_k kinematic factor.
The "entropy" shorthand collapses this operational structure into a
single coarse-grained scalar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

OUT_DIR = Path(__file__).resolve().parent


def mpm_test(new_word: str, old_words: List[str], leaves_shadow: bool, notes: str) -> Dict:
    """MPM test: does the new vocabulary leave the old as unexplained shadow?

    If yes, both stand at different ontological levels.
    If no, the old vocabulary is dispensable; the new is canonical at its level.
    """
    return {
        "new_word": new_word,
        "old_words_repostured": old_words,
        "leaves_old_as_shadow": leaves_shadow,
        "verdict": "BOTH STAND" if leaves_shadow else "NEW IS SUBSTRATE-LEVEL",
        "notes": notes,
    }


def main():
    print("=== Spike #42 -- Vocabulary reposture ===\n")
    print("Hindsight-shorthand catalog (the 'because of entropy' family):\n")
    hindsight_words = [
        ("entropy", "Boltzmann/Clausius proxy for many-distinct-state-counting"),
        ("heat", "energy in random motion -- coarse readout"),
        ("thermal", "equilibrium of fast-equilibrating DOFs"),
        ("destroyed", "loss of accessible information"),
        ("lost", "decoupled from observable structure"),
        ("created", "visible-sector materialization"),
        ("un-created", "visible-sector de-materialization"),
        ("disorder", "statistical-mechanics-proxy for log(microstates)"),
        ("dissipation", "energy flow into many DOFs"),
    ]
    for w, gloss in hindsight_words:
        print(f"  {w:>15}: {gloss}")
    print()

    print("Each is 'because of entropy' shorthand that shuts down further questioning.")
    print()
    print("PARALLEL to [[user_stance_infinity_approximates_asymptote]]:")
    print("  Just as 'infinity is fundamental' shut down asymptote-recognition for")
    print("  centuries (per Spike #28 calculus-history finding), 'because of entropy'")
    print("  shuts down cascade-structure-recognition.")
    print()
    print("  Per [[feedback_every_doc_edit_faces_falsification]]: the burden is to")
    print("  state the substrate-level operation, not invoke the coarse-grained proxy.")
    print()

    print("=== Substrate-level candidates ===\n")
    print("Candidates with operational-precision definitions:\n")

    candidates = [
        {
            "word": "imprint",
            "definition": (
                "the cascade-deposit operation: substrate accumulates cascade content "
                "from one mode-sector to another. Bidirectional under thawing-CPL "
                "(forward: imprint INTO dark; reverse: imprint INTO visible)."
            ),
            "captures_directionality": "PARTIAL -- 'imprint' is naturally forward; un-imprint must be named separately",
            "captures_cascade_structure": "YES -- imprinting is the cascade-deposit per K-step",
            "alignment_with_existing_stances": (
                "User already used 'imprinting' phrasing ('dark sector imprinting "
                "attractors'). [[user_stance_dark_sector_ring_down_age]] family."
            ),
        },
        {
            "word": "cascade-deposit",
            "definition": (
                "per-mode-k advancement of f_RD; the substrate's accumulated "
                "modal-completion increment at index k of the eps^k tower."
            ),
            "captures_directionality": "DEPOSIT is forward; need 'cascade-withdrawal' for reverse",
            "captures_cascade_structure": "YES -- explicit cascade-naming",
            "alignment_with_existing_stances": (
                "Direct extension of [[user_stance_primitives_weave_and_thread]] -- "
                "the cascade's per-mode deposit IS the operational increment."
            ),
        },
        {
            "word": "modal-completion increment",
            "definition": (
                "df_RD increment from one mode-k completion. Per Spike #41 sharpening, "
                "this is the eps^k geometric step on Class K asymptotic-DOF axis."
            ),
            "captures_directionality": "SIGNED -- df_RD/dt sign captures direction",
            "captures_cascade_structure": "YES -- modal-completion is the cascade's atomic step",
            "alignment_with_existing_stances": (
                "[[user_stance_asymptotic_dof_sidesteps_infinity]] -- modal-completion "
                "increments parameterize the rate-of-approach without commiting to "
                "infinite-vs-finite cardinality."
            ),
        },
        {
            "word": "coherence-weave",
            "definition": (
                "the rate-of-coherence-shift across all 14 classes simultaneously. "
                "Per [[user_stance_primitives_weave_and_thread]], the weaving IS "
                "the operation."
            ),
            "captures_directionality": "WEAVING has direction; un-weaving is natural symmetric",
            "captures_cascade_structure": "YES -- explicit cross-class structure",
            "alignment_with_existing_stances": (
                "Maximum alignment with [[user_stance_primitives_weave_and_thread]] -- "
                "names the weaving directly."
            ),
        },
        {
            "word": "substrate-uptake / return-flow",
            "definition": (
                "what the substrate absorbs (uptake) or releases (return-flow) per "
                "unit cosmic time. Captures bidirectionality NATURALLY."
            ),
            "captures_directionality": "EXPLICIT bidirectional pair",
            "captures_cascade_structure": "PARTIAL -- describes net flow, not eps^k tower",
            "alignment_with_existing_stances": (
                "Aligns with non-monotone f_RD finding (Spike #42 trajectory): "
                "uptake dominates before peak; return-flow dominates after."
            ),
        },
        {
            "word": "ring-up / ring-down",
            "definition": (
                "Per [[user_stance_string_theory_instrument_first]]: ring-up = "
                "substrate excitation; ring-down = cascade-decay return-flow. "
                "Bidirectional natively."
            ),
            "captures_directionality": "EXPLICIT bidirectional pair (already-canonical)",
            "captures_cascade_structure": "YES -- ring-down IS the cascade structure",
            "alignment_with_existing_stances": (
                "MAXIMUM -- already canonical project vocabulary. The 'entropy' "
                "shorthand is a coarse readout of ring-up vs ring-down balance."
            ),
        },
    ]
    for c in candidates:
        print(f"  {c['word']}:")
        print(f"    definition: {c['definition']}")
        print(f"    directionality: {c['captures_directionality']}")
        print(f"    cascade structure: {c['captures_cascade_structure']}")
        print(f"    alignment: {c['alignment_with_existing_stances']}")
        print()

    print("=== MPM-test verdicts ===\n")
    print("Does adopting the new vocabulary leave 'entropy' as unexplained shadow?\n")

    tests = [
        mpm_test(
            "imprint / un-imprint pair",
            ["entropy", "heat", "destroyed", "created"],
            leaves_shadow=False,
            notes=(
                "Imprint is operational-precise (cascade-deposit per K-step); "
                "entropy is a coarse Boltzmann readout of imprint accumulation. "
                "'Heat' becomes one dimensional-kind manifestation (3D_s + thermal "
                "= imprint accumulation in 3D_s modes). 'Entropy' becomes secondary."
            ),
        ),
        mpm_test(
            "ring-up / ring-down (already-canonical)",
            ["entropy", "heat", "thermal", "destroyed", "lost", "dissipation"],
            leaves_shadow=False,
            notes=(
                "Ring-up/ring-down already named per [[user_stance_string_theory_instrument_first]]. "
                "Entropy becomes a coarse net-readout of ring-down imbalance. "
                "Thermal becomes ring-down equilibrium across one mode-class. "
                "Dissipation becomes ring-down flow across mode-coupling boundaries."
            ),
        ),
        mpm_test(
            "modal-completion increment",
            ["entropy", "heat", "thermal", "destroyed"],
            leaves_shadow=True,
            notes=(
                "Modal-completion increment is the operational PER-STEP measure. "
                "Entropy IS the integrated counting of modal-completion steps. "
                "Both stand: modal-completion at operational level; entropy at "
                "integrated/coarse-grained level. Per "
                "[[user_stance_partition_for_understanding]], both partitions "
                "coexist at different ontological levels."
            ),
        ),
        mpm_test(
            "coherence-weave",
            ["entropy", "thermal"],
            leaves_shadow=True,
            notes=(
                "Coherence-weave is the cross-class operational structure. "
                "Entropy is the projection onto a single mode-class. Both stand: "
                "weave at substrate level; entropy at projection-to-one-class level."
            ),
        ),
    ]
    for t in tests:
        print(f"  {t['new_word']}:")
        print(f"    repostures: {t['old_words_repostured']}")
        print(f"    leaves old as shadow: {t['leaves_old_as_shadow']}")
        print(f"    verdict: {t['verdict']}")
        print(f"    notes: {t['notes']}")
        print()

    print("=== Candidate stance proposal ===\n")
    print("CANDIDATE: user_stance_entropy_approximates_imprint")
    print()
    print("Form: same shape as [[user_stance_infinity_approximates_asymptote]]")
    print()
    print("Claim: 'entropy' is the algebraic shorthand thermodynamics reached for to")
    print("       describe the cascade-imprint operation. Imprint is upstream;")
    print("       cardinal entropy is downstream approximation.")
    print()
    print("Three operational senses (parallel to infinity-asymptote stance):")
    print("  1. No ontological denial of entropy. Boltzmann/Clausius/Shannon entropy")
    print("     remain legitimate mathematical structures.")
    print("  2. Locates entropy as approximation. Imprint -> entropy (substrate ->")
    print("     algebraic tool), not entropy -> imprint.")
    print("  3. Honours the historical record. Clausius/Boltzmann/Gibbs were reaching")
    print("     for the cascade-imprint object without 14-class vocabulary yet.")
    print()
    print("REFINEMENT FROM SPIKE #42: Imprint is BIDIRECTIONAL under non-monotone f_RD.")
    print("So the more careful framing is:")
    print("  'entropy approximates the imprint-and-un-imprint cascade balance'")
    print("OR equivalently, with already-canonical project vocabulary:")
    print("  'entropy approximates the ring-up/ring-down cascade balance'")
    print()
    print("CONCERTMASTER LEAN (per existing-stance dissolve-before-promote)")
    print("[[feedback_no_privileged_primitive_classes]]:")
    print("  RING-UP/RING-DOWN is ALREADY CANONICAL.")
    print("  Per [[user_stance_string_theory_instrument_first]], project already")
    print("  has the bidirectional vocabulary. The new stance candidate sharpens")
    print("  the connection: entropy IS the coarse readout of ring-down accumulation")
    print("  minus ring-up replenishment.")
    print()
    print("FERMATA: which name? Three options:")
    print("  (A) 'entropy approximates the imprint' (parallels infinity-stance)")
    print("  (B) 'entropy approximates the ring-up/ring-down balance' (most")
    print("       project-aligned; uses existing canonical vocabulary)")
    print("  (C) 'entropy approximates the cascade-imprint operation' (most")
    print("       cascade-explicit)")
    print()
    print("All three pass the MPM test (entropy stands at integrated-counting level;")
    print("substrate-cascade stands at operational level). User-gated choice.")
    print()
    print("PER USER DIRECTION TO 'NOT RESTRICT TO JUST HUMAN TERMS':")
    print("  'imprint' and 'ring-up/ring-down' are accessible.")
    print("  'cascade-imprint' is operationally most precise; the human-language")
    print("  word for it might be unfamiliar.")
    print("  Per [[user_stance_partition_for_understanding]] -- multiple ")
    print("  levels can coexist; the substrate-level word is allowed to be")
    print("  non-human even if a human-accessible word also coexists at the")
    print("  pedagogical level.")
    print()

    # Emit NDJSON
    records = []
    for w, gloss in hindsight_words:
        records.append({
            "kind": "hindsight_word",
            "word": w,
            "gloss": gloss,
        })
    for c in candidates:
        records.append({
            "kind": "candidate_substrate_word",
            **c,
        })
    for t in tests:
        records.append({
            "kind": "mpm_test_outcome",
            **t,
        })
    records.append({
        "kind": "candidate_stance_proposal",
        "stance_name": "user_stance_entropy_approximates_imprint",
        "shape": "same as [[user_stance_infinity_approximates_asymptote]]",
        "claim_three_phrasings": [
            "entropy approximates the imprint",
            "entropy approximates the ring-up/ring-down balance",
            "entropy approximates the cascade-imprint operation",
        ],
        "concertmaster_lean": (
            "Ring-up/ring-down is already canonical per "
            "[[user_stance_string_theory_instrument_first]]. The new stance "
            "candidate sharpens the entropy connection; uses existing vocabulary. "
            "Per dissolve-before-promote, prefer ring-up/ring-down phrasing."
        ),
        "non_monotone_refinement": (
            "Spike #42 trajectory analysis shows imprint is bidirectional. "
            "Single-direction 'imprint' alone is incomplete; pair with "
            "'un-imprint' or use 'ring-up/ring-down' which is natively "
            "bidirectional."
        ),
        "user_gated": True,
        "fermata_options": [
            "(A) 'entropy approximates the imprint' (parallels infinity-stance)",
            "(B) 'entropy approximates the ring-up/ring-down balance' (most project-aligned)",
            "(C) 'entropy approximates the cascade-imprint operation' (most cascade-explicit)",
        ],
    })

    out_path = OUT_DIR / "spike_42_vocabulary_records.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"\nEmitted {len(records)} vocabulary records to {out_path}")


if __name__ == "__main__":
    main()
