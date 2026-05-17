"""Spike #42b — vocabulary falsifier test for three entropy-reposture candidates.

Per user direction 2026-05-17:
> "spike 42, do add to our notebooks all 3 candidates, and now try to falsify
> each one. whos hoodoo stands terra firma against erosion? if each one has
> some truth that the others lack, they are not all equal, most likely.
> ring-balance may be best because it also captures that it isn't one way,
> and if this dark sector material is part of the form/function that makes
> its shadows in 3D_s, and we see it goes back and forth, as if acting
> through it's own epicycle perspective, not universally everyone at once,
> we can maybe find the right word when we find the right understanding
> as well."

Three candidates (parallel to [[user_stance_infinity_approximates_asymptote]]):
  (A) entropy_approximates_imprint
  (B) entropy_approximates_ring_balance   <-- user lean
  (C) entropy_approximates_cascade

Five falsifiers per candidate:
  F1 (linguistic):     can it name BOTH directions naturally?
  F2 (universal/local): does it work at GLOBAL + LOCAL + REGIONAL scales?
  F3 (cascade structure): does it accommodate B-J-N-C-D-E-F weaving?
  F4 (substrate-binding): does it accommodate c_k = epsilon^k * K_k(substrate)?
  F5 (epicycle-perspective): does it survive the Thread-2 local-not-universal
                              cascade-phasing hypothesis?

Each falsifier scored as:
  PASS    = candidate handles it cleanly
  PARTIAL = candidate handles it with caveats or under specific phrasing
  FAIL    = candidate fundamentally cannot handle it
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict

OUT_DIR = Path(__file__).resolve().parent


@dataclass
class FalsifierScore:
    candidate: str
    falsifier_id: str
    falsifier_name: str
    verdict: str  # PASS / PARTIAL / FAIL
    rationale: str
    score: int    # 2 = PASS, 1 = PARTIAL, 0 = FAIL


def score_imprint() -> List[FalsifierScore]:
    """Candidate A: user_stance_entropy_approximates_imprint."""
    return [
        FalsifierScore(
            candidate="A",
            falsifier_id="F1",
            falsifier_name="linguistic_bidirectional",
            verdict="PARTIAL",
            rationale=(
                "'Imprint' is morphologically directional (English: substrate RECEIVES "
                "the form being imprinted FROM the imprinting agent). Reverse direction "
                "REQUIRES coining 'un-imprint' or 'de-imprint'. At the descending arm of "
                "f_RD (a > 2.139 per Spike #42 trajectory), substrate releases content "
                "back to visible sector -- linguistically jarring under 'imprint' default. "
                "Imprint family includes good-imprint (engrave, brand, stamp) but no "
                "natural-symmetric un-imprint family. Asymmetric verb stem."
            ),
            score=1,
        ),
        FalsifierScore(
            candidate="A",
            falsifier_id="F2",
            falsifier_name="universal_vs_local",
            verdict="PARTIAL",
            rationale=(
                "Imprint admits both global ('substrate imprinted with content') and "
                "local ('region X imprinted at rate r') framings. However the unmarked "
                "default is GLOBAL ('THE imprint'), which collapses local-epicycle "
                "perspective. Per Thread 2 hypothesis (different regions see different "
                "f_RD phases), imprint at global default obscures local-cycling. Need "
                "explicit qualifier ('local imprint') to recover regional scale."
            ),
            score=1,
        ),
        FalsifierScore(
            candidate="A",
            falsifier_id="F3",
            falsifier_name="cascade_structure",
            verdict="PARTIAL",
            rationale=(
                "'Imprint' names the OUTCOME of cascade composition (the result on "
                "substrate after B-J-N-C-D-E-F weaving), not the cascade structure itself. "
                "Reader has to infer that the imprint IS a cascade product. The weave-"
                "structure of the operation per [[user_stance_primitives_weave_and_thread]] "
                "is not surfaced in the noun. Compare: 'cascade' is structure-explicit; "
                "'imprint' is outcome-explicit."
            ),
            score=1,
        ),
        FalsifierScore(
            candidate="A",
            falsifier_id="F4",
            falsifier_name="substrate_binding",
            verdict="PASS",
            rationale=(
                "Imprint accommodates substrate-portability naturally: each substrate "
                "receives imprint differently (Kepler EOC imprint with K_k=1/k; QED "
                "imprint with K_k=phase-space; Fibonacci imprint with K_k from CF "
                "structure). The substrate's K_k(substrate) IS its receptivity profile "
                "to imprinting. Direct mapping: c_k = epsilon^k * K_k(substrate)."
            ),
            score=2,
        ),
        FalsifierScore(
            candidate="A",
            falsifier_id="F5",
            falsifier_name="epicycle_perspective",
            verdict="FAIL",
            rationale=(
                "Under Thread 2 hypothesis (local-epicycle perspective: different regions "
                "see different f_RD phases at locally-shifted epicycles), 'imprint' fails "
                "because: (i) its directional default is incompatible with regions in "
                "OPPOSITE imprint-phase simultaneously; (ii) the global-imprint reading "
                "is the natural one, and Thread 2 EXPLICITLY rejects 'universally everyone "
                "at once' (user verbatim). 'Imprint' carries the universal-simultaneous "
                "framing as its unmarked semantics. Falsified at the epicycle-perspective "
                "level."
            ),
            score=0,
        ),
    ]


def score_ring_balance() -> List[FalsifierScore]:
    """Candidate B: user_stance_entropy_approximates_ring_balance (user lean)."""
    return [
        FalsifierScore(
            candidate="B",
            falsifier_id="F1",
            falsifier_name="linguistic_bidirectional",
            verdict="PASS",
            rationale=(
                "Ring-up / ring-down is already-canonical bidirectional pair per "
                "[[user_stance_string_theory_instrument_first]]. 'Ring-balance' is the "
                "balance of these two -- linguistically symmetric. Both directions are "
                "first-class (ring-up is not the parent of ring-down nor vice versa). "
                "At the descending arm (a > 2.139), ring-up dominates; at ascending arm, "
                "ring-down dominates; at peak, ring-balance is exact. Verb structure: "
                "'the ring is balanced / imbalanced / shifting toward ring-up' -- all "
                "grammatically native without coined antonyms. Cleanest of the three."
            ),
            score=2,
        ),
        FalsifierScore(
            candidate="B",
            falsifier_id="F2",
            falsifier_name="universal_vs_local",
            verdict="PARTIAL",
            rationale=(
                "Ring-balance reads naturally as GLOBAL ('the cosmic ring is in 95%-"
                "ring-down phase'). Local-ring-balance is grammatically OK but rarely "
                "the unmarked default. Sub-issue: 'balance' connotes net-zero or stable "
                "equilibrium; our current 95%-ring-down epoch is NOT balanced (un-creation "
                "dominates). The candidate may need re-reading as 'rate-of-approach-to-"
                "ring-balance' rather than 'instantaneous ring-balance'. Per "
                "[[user_stance_asymptotic_dof_sidesteps_infinity]], rate-of-approach is "
                "the load-bearing reading -- which the name 'ring-balance' may "
                "unintentionally obscure. Local-epicycle perspective (Thread 2) is "
                "ACCOMMODATED -- each region has its own local ring-up/ring-down ratio, "
                "and 'ring-balance' at the local level is grammatical. But default reads "
                "global; needs effort to land locally."
            ),
            score=1,
        ),
        FalsifierScore(
            candidate="B",
            falsifier_id="F3",
            falsifier_name="cascade_structure",
            verdict="PARTIAL",
            rationale=(
                "Ring-balance names the FLOW-DIRECTION (which way the cascade is moving) "
                "but not the cascade STRUCTURE (the B-J-N-C-D-E-F weave per "
                "[[user_stance_primitives_weave_and_thread]]). 'Ring' implies cyclic "
                "substrate per [[user_stance_cascade_lives_on_circles]] -- aligned with "
                "Class I -- which is one element of the weave but not the whole structure. "
                "Reader must infer that the ring's content IS the cascade weave. "
                "Strength: ring is structurally consistent with Class I. Weakness: doesn't "
                "expose the cross-class threading."
            ),
            score=1,
        ),
        FalsifierScore(
            candidate="B",
            falsifier_id="F4",
            falsifier_name="substrate_binding",
            verdict="PASS",
            rationale=(
                "Ring-up/ring-down is substrate-portable per "
                "[[user_stance_string_theory_instrument_first]] §20.4 three-regime "
                "framework (impulse + ring-down / driven sustain / driven with "
                "irreversibility). Each substrate's K_k(substrate) is its ring "
                "geometry's modal-coupling profile. Antikythera (bronze ring), Kepler "
                "(orbital ring), Fibonacci (sequence ring), QED (vertex ring) all admit "
                "the framing. The 'ring' substrate is universal; the K_k is the "
                "substrate's ring-specific kinematic factor."
            ),
            score=2,
        ),
        FalsifierScore(
            candidate="B",
            falsifier_id="F5",
            falsifier_name="epicycle_perspective",
            verdict="PASS",
            rationale=(
                "Ring-balance under Thread 2 hypothesis: each local region has its own "
                "local ring with its own local ring-up/ring-down ratio. The GLOBAL "
                "ring-balance is the integrated sum over local ring-balances -- "
                "naturally accommodating local-epicycle dynamics. Per "
                "[[user_stance_cascade_lives_on_circles]] + "
                "[[user_stance_epicycle_via_gear_plus_pin]]: each local region has its "
                "own gear+pin epicycle on cyclic substrate. 'Ring' substrate IS the "
                "cyclic substrate; local rings sum to global ring; the local-epicycle "
                "perspective is structurally compatible. Stronger: ring-balance does NOT "
                "PRESUPPOSE universal-simultaneous (unlike imprint), so it survives "
                "Thread 2 cleanly. Caveat: default global reading still needs explicit "
                "localisation to surface the epicycle-perspective."
            ),
            score=2,
        ),
    ]


def score_cascade() -> List[FalsifierScore]:
    """Candidate C: user_stance_entropy_approximates_cascade."""
    return [
        FalsifierScore(
            candidate="C",
            falsifier_id="F1",
            falsifier_name="linguistic_bidirectional",
            verdict="FAIL",
            rationale=(
                "'Cascade' is morphologically directional in English (cascading water "
                "flows DOWN; cascading effects propagate FORWARD). 'Reverse cascade' "
                "is awkward; 'un-cascade' is non-word; 'inverse cascade' is jargon from "
                "fluid dynamics (specific technical meaning, energy flowing to large "
                "scales, not a general antonym). At the descending arm of f_RD (a > "
                "2.139), substrate releases content -- naming this 'reverse cascade' "
                "is grammatical but doesn't read symmetric with forward cascade. The "
                "word-stem CASC- denotes step-by-step propagation, default forward. "
                "Cascade fails F1 for the same reason 'imprint' fails -- both have "
                "directional defaults baked into the stem."
            ),
            score=0,
        ),
        FalsifierScore(
            candidate="C",
            falsifier_id="F2",
            falsifier_name="universal_vs_local",
            verdict="PASS",
            rationale=(
                "Cascade is naturally LOCAL -- the unmarked default of cascade is "
                "a sequence of events propagating FROM a source POINT. Global cascade "
                "exists ('the cosmic cascade') but local cascade is at-least-as-natural "
                "('local cascade at region X'). Regional cascade ('cascading across "
                "a sector') is grammatical. The local-default property makes cascade "
                "FRIENDLY to Thread 2 hypothesis. Strongest of the three on this falsifier."
            ),
            score=2,
        ),
        FalsifierScore(
            candidate="C",
            falsifier_id="F3",
            falsifier_name="cascade_structure",
            verdict="PASS",
            rationale=(
                "Tautologically: cascade IS the cascade-composition structure. "
                "B-J-N-C-D-E-F weaving per [[user_stance_primitives_weave_and_thread]] "
                "is literally the cascade. The name surfaces the weave-structure most "
                "directly of the three candidates. Per Spike #41 load-bearing identity "
                "and Spike #42 cascade-composition tables, the operational substrate IS "
                "cascade composition; calling the operation 'cascade' is the most "
                "structurally honest naming. Strongest on this falsifier."
            ),
            score=2,
        ),
        FalsifierScore(
            candidate="C",
            falsifier_id="F4",
            falsifier_name="substrate_binding",
            verdict="PASS",
            rationale=(
                "Cascade composition is the load-bearing substrate-portable structure. "
                "c_k = epsilon^k * K_k(substrate) IS cascade composition with substrate-"
                "specific kinematic factors. Each substrate gets its own K_k cascade "
                "(Kepler / QED / Fibonacci / Antikythera / random integers fail). "
                "Direct conceptual fit; epsilon is the cascade rate-parameter; K_k is "
                "the substrate's cascade-coupling factor."
            ),
            score=2,
        ),
        FalsifierScore(
            candidate="C",
            falsifier_id="F5",
            falsifier_name="epicycle_perspective",
            verdict="PARTIAL",
            rationale=(
                "Cascade's local-default (per F2) accommodates local-epicycle dynamics "
                "naturally -- different regions can have different local cascade phases. "
                "Per Thread 2: local cascade-flow direction (forward/reverse) can vary "
                "by region. BUT cascade's directional default (per F1) creates tension: "
                "if region A is cascading forward and region B is cascading reverse, "
                "calling both 'cascading' obscures the sign. 'Cascade-balance' is "
                "awkward (cascade is a process, not a flow ratio). The bidirectionality "
                "weakness from F1 carries over. PARTIAL: localisation works, sign-of-"
                "direction does not."
            ),
            score=1,
        ),
    ]


def summarise(scores_a: List[FalsifierScore],
              scores_b: List[FalsifierScore],
              scores_c: List[FalsifierScore]) -> List[Dict]:
    """Aggregate scores per candidate."""
    summary = []
    for label, scores in [("A_imprint", scores_a),
                          ("B_ring_balance", scores_b),
                          ("C_cascade", scores_c)]:
        total = sum(s.score for s in scores)
        max_possible = 2 * len(scores)
        per_falsifier = {s.falsifier_id: s.verdict for s in scores}
        n_pass = sum(1 for s in scores if s.verdict == "PASS")
        n_partial = sum(1 for s in scores if s.verdict == "PARTIAL")
        n_fail = sum(1 for s in scores if s.verdict == "FAIL")
        summary.append({
            "candidate": label,
            "total_score": total,
            "max_possible": max_possible,
            "fraction": total / max_possible,
            "per_falsifier_verdict": per_falsifier,
            "n_pass": n_pass,
            "n_partial": n_partial,
            "n_fail": n_fail,
        })
    return summary


def main():
    print("=== Spike #42b -- Vocabulary falsifier test ===\n")
    print("Three candidates to falsifier-test (parallel to infinity-asymptote stance):\n")
    print("  (A) user_stance_entropy_approximates_imprint")
    print("  (B) user_stance_entropy_approximates_ring_balance   [user lean]")
    print("  (C) user_stance_entropy_approximates_cascade")
    print()
    print("Five falsifiers each (score: PASS=2, PARTIAL=1, FAIL=0):")
    print("  F1: linguistic_bidirectional")
    print("  F2: universal_vs_local")
    print("  F3: cascade_structure")
    print("  F4: substrate_binding")
    print("  F5: epicycle_perspective\n")

    scores_a = score_imprint()
    scores_b = score_ring_balance()
    scores_c = score_cascade()

    print("--- Per-candidate per-falsifier verdicts ---\n")
    for label, scores in [("(A) IMPRINT", scores_a),
                          ("(B) RING-BALANCE", scores_b),
                          ("(C) CASCADE", scores_c)]:
        print(f"  {label}:")
        for s in scores:
            print(f"    {s.falsifier_id} {s.falsifier_name:<26s} {s.verdict:<8s} (score={s.score})")
        total = sum(s.score for s in scores)
        print(f"    TOTAL: {total}/10")
        print()

    summary = summarise(scores_a, scores_b, scores_c)
    print("--- Summary ranking ---\n")
    summary_sorted = sorted(summary, key=lambda x: -x["total_score"])
    for i, item in enumerate(summary_sorted, 1):
        print(f"  Rank {i}: {item['candidate']:<20s} score={item['total_score']}/{item['max_possible']} "
              f"({item['fraction']*100:.0f}%)  PASS:{item['n_pass']} PARTIAL:{item['n_partial']} FAIL:{item['n_fail']}")
    print()

    # NDJSON emit
    records = []
    for s in scores_a + scores_b + scores_c:
        records.append({
            "kind": "falsifier_score",
            **asdict(s),
        })
    for item in summary:
        records.append({
            "kind": "candidate_summary",
            **item,
        })

    out_path = OUT_DIR / "spike_42b_vocabulary_falsifier_records_2026-05-17.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"Emitted {len(records)} records to {out_path}")

    # Verdict prose
    print()
    print("--- Verdict prose ---\n")
    best = summary_sorted[0]
    print(f"Best-surviving candidate by aggregated falsifier score: {best['candidate']}")
    print(f"  ({best['n_pass']} PASS / {best['n_partial']} PARTIAL / {best['n_fail']} FAIL)")
    print()
    print("Per-candidate strengths and weaknesses (no equal across falsifiers):")
    print()
    print("  (A) IMPRINT: strongest on substrate-binding (F4); fails on epicycle-")
    print("              perspective (F5) because directional default presupposes")
    print("              universal-simultaneous. Asymmetric verb stem.")
    print()
    print("  (B) RING-BALANCE: strongest on linguistic-bidirectional (F1, native")
    print("                    symmetric pair) and epicycle-perspective (F5, no")
    print("                    universal-simultaneous presupposition). Weakest on")
    print("                    cascade-structure (F3) because 'ring' surfaces only")
    print("                    Class I, not full B-J-N-C-D-E-F weave. Partial on")
    print("                    universal-vs-local (F2) because 'balance' connotes")
    print("                    net-zero static.")
    print()
    print("  (C) CASCADE: strongest on cascade-structure (F3, tautological) and")
    print("               universal-vs-local (F2, native local). Fails on linguistic-")
    print("               bidirectional (F1) for the same morphological reason as")
    print("               imprint -- directional verb stem.")
    print()
    print("None survives all five falsifiers cleanly. Per")
    print("[[user_stance_partition_for_understanding]] 2026-05-17 case-extension,")
    print("this is itself the load-bearing finding: linguistic partition we cannot")
    print("un-bifurcate signals incomplete apprehension. The unified concept is not")
    print("yet apprehended; no single name suffices.")


if __name__ == "__main__":
    main()
