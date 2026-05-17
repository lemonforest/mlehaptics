"""Spike #42b -- final synthesis.

Combines:
  - Vocabulary falsifier scores (3 candidates x 5 falsifiers)
  - Epicycle-perspective hypothesis verdict (v1 multiplicative model + v2 time-shift model)

Per user direction:
> "whos hoodoo stands terra firma against erosion? if each one has some truth
> that the others lack, they are not all equal, most likely. ring-balance
> may be best because it also captures that it isn't one way"

Per [[user_stance_partition_for_understanding]] 2026-05-17 case-extension:
> "we've hit a language partition that we cannot figure how to un-bifurcate
> into one thing. that means that each of these must be partially true but
> partially missing fiber content to satisify all reasoning. It also says
> that we probably don't know enough to name it yet."

Concertmaster lean per stance-discipline: vocabulary continues user-gated;
even with best survivor (B ring-balance), F3 (cascade structure) is partial
and F2 (universal-vs-local) is partial. The other two candidates each have
strengths the survivor lacks. Per case-extension, holding the partition
itself is the load-bearing finding.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent


def main():
    print("=" * 78)
    print("Spike #42b -- final synthesis")
    print("=" * 78)
    print()
    print("THREAD 1 (vocabulary falsifier test):")
    print()
    print("  Five falsifiers per candidate; PASS=2 / PARTIAL=1 / FAIL=0:")
    print()
    print("    Candidate          F1   F2   F3   F4   F5   TOTAL")
    print("    --------------------------------------------------")
    print("    (A) imprint        P    P    P    PASS FAIL  5/10 (50%)")
    print("    (B) ring-balance   PASS P    P    PASS PASS  8/10 (80%)  <-- user lean confirmed")
    print("    (C) cascade        FAIL PASS PASS PASS P     7/10 (70%)")
    print()
    print("  RANKING by falsifier survival: B > C > A")
    print()
    print("  User-lean confirmed empirically: ring-balance has the FEWEST and")
    print("  WEAKEST weaknesses. No FAIL verdicts. Strongest on:")
    print("    F1 (linguistic bidirectional): native symmetric pair")
    print("    F4 (substrate binding): substrate-portable per §20.4 three-regime")
    print("    F5 (epicycle perspective): no universal-simultaneous presupposition")
    print()
    print("  But B has REAL weaknesses on:")
    print("    F3 (cascade structure): 'ring' surfaces only Class I, not full")
    print("                            B-J-N-C-D-E-F weave per primitives-weave-and-")
    print("                            thread stance")
    print("    F2 (universal vs local): 'balance' connotes net-zero static; current")
    print("                              95%-ring-down epoch is NOT balanced")
    print()
    print("  Candidate C (cascade) has IDENTITY strength on F3 (it IS the structure)")
    print("  but FAILS F1 due to directional verb stem. Candidate A (imprint) has only")
    print("  F4 as full PASS and FAILS F5.")
    print()
    print("  EACH CANDIDATE HAS TRUTH THE OTHERS LACK -- confirms user's prior:")
    print("    'if each one has some truth that the others lack, they are not all")
    print("     equal, most likely.'")
    print()
    print("  Even the best survivor (B) has known structural weakness (F3 cascade")
    print("  structure invisible in 'ring' noun). Per [[user_stance_partition_for_")
    print("  understanding]] 2026-05-17 case-extension, this is itself the load-")
    print("  bearing finding: no single name suffices.")
    print()
    print("-" * 78)
    print()
    print("THREAD 2 (epicycle-perspective hypothesis):")
    print()
    print("  V1 MODEL (multiplicative): f_local = f_global * (1 + modulation)")
    print("    - DEGENERATE: sign(df_local) = sign(df_global) always")
    print("    - Spatial amplitude ~10% at present epoch")
    print("    - No sign-flip across directions (model defect, not hypothesis defect)")
    print()
    print("  V2 MODEL (time-shift): f_local = f_global(a_local(theta))")
    print("    where t_local = t_global + (EOC_phase_shift / 2pi) * char_time")
    print("    - PHYSICALLY CORRECT: each direction sees substrate at shifted time")
    print("    - Max time shift across sky: 1.44 Gyr (0.81% of 178 Gyr ring-down period)")
    print("    - Sign-flip at NOW: NOT observed (global ring-down too dominant)")
    print("    - Sign-flip at NEAR-PEAK (a~2.14): OBSERVED -- 2 vs 35 directions opposite sign")
    print("    - VERDICT: hypothesis CONFIRMED at near-peak regime; structural property")
    print("              valid; quantitatively subtle at canonical eps_AoE at present.")
    print()
    print("  KEY FINDING (from anomaly investigation): v1 model was multiplicatively")
    print("  degenerate by construction. Math-doesn't-lie discipline drove v2 fix.")
    print("  v2 (time-shift) produces the predicted local-not-universal pattern in")
    print("  the regime where global rate is small (near peak).")
    print()
    print("  CONSEQUENCE for vocabulary: the epicycle-perspective hypothesis is")
    print("  structurally real but quantitatively subtle at present epoch. It")
    print("  correctly WEAKENS 'universal' framings (imprint default) without")
    print("  MANDATING that local sign-flips are currently observable. Names")
    print("  that don't presuppose universal-simultaneous (ring-balance) or")
    print("  default-local (cascade) are preferred over names that default-global")
    print("  (imprint).")
    print()
    print("-" * 78)
    print()
    print("CONVERGENCE OF BOTH THREADS:")
    print()
    print("  Thread 1 (falsifier scores) and Thread 2 (epicycle hypothesis) BOTH")
    print("  weaken candidate A (imprint) most. Thread 1 ranks B > C > A; Thread 2")
    print("  weakens A's universal-simultaneous default. CONVERGENT signal.")
    print()
    print("  Thread 1 ranks B (ring-balance) ahead of C (cascade) by linguistic-")
    print("  bidirectional advantage. Thread 2 favours B over C by structural-not-")
    print("  presupposing-universal advantage. CONVERGENT signal.")
    print()
    print("  Combined ranking: B (ring-balance) > C (cascade) > A (imprint)")
    print()
    print("=" * 78)
    print("RECOMMENDATION")
    print("=" * 78)
    print()
    print("Concertmaster lean: USER-GATED CONTINUES; B (ring-balance) is the BEST")
    print("survivor but NOT a clean winner. Per stance-discipline:")
    print()
    print("  1. Best survivor: candidate B (ring-balance) -- 8/10 falsifier score,")
    print("     zero FAIL verdicts, user-lean confirmed empirically.")
    print()
    print("  2. Each candidate carries unique truth (per user's prior framing):")
    print("       A captures: substrate RECEIVES content (deposit framing)")
    print("       B captures: bidirectional flow + already-canonical vocabulary")
    print("       C captures: cascade STRUCTURE (B-J-N-C-D-E-F weave) directly")
    print()
    print("  3. Per [[user_stance_partition_for_understanding]] case-extension:")
    print("     the linguistic partition we cannot un-bifurcate is itself the")
    print("     load-bearing finding. The unified concept is not yet apprehended.")
    print()
    print("  4. Mathematical structure (c_k = eps^k * K_k(substrate) per Spike #42")
    print("     finding; local-time-shift via EOC per Spike #42b v2) STANDS regardless")
    print("     of which noun is chosen.")
    print()
    print("CONCRETE NEXT STEP (if user commits a single name):")
    print()
    print("  - Commit B (ring-balance) as the canonical stance, but record explicit")
    print("    sister-clauses for what A and C respectively capture:")
    print()
    print("      Canonical: 'entropy approximates the ring-up / ring-down balance'")
    print("      (per [[user_stance_string_theory_instrument_first]] vocabulary)")
    print()
    print("      Sister-clause from A (deposit): the substrate's accumulated content")
    print("      (cascade-deposit per K-step) IS what ring-balance is balancing.")
    print()
    print("      Sister-clause from C (cascade structure): the operation balanced")
    print("      across the ring is the B-J-N-C-D-E-F cascade weave per")
    print("      [[user_stance_primitives_weave_and_thread]].")
    print()
    print("CONCRETE NEXT STEP (if user holds the partition):")
    print()
    print("  - Record Spike #42b finding as: 'three candidates surfaced; B preferred")
    print("    on falsifier survival but no single name suffices; unified concept not")
    print("    yet apprehended.' Continue follow-up research per case-extension.")
    print()
    print("=" * 78)
    print("DISCIPLINE GUARDS HONOURED")
    print("=" * 78)
    print()
    print("  [[user_stance_partition_for_understanding]] case-extension -- LOAD-BEARING")
    print("  [[user_stance_primitives_weave_and_thread]] -- cascade composition is structure")
    print("  [[user_stance_kepler_shape_universal]] -- c_k = eps^k * K_k(substrate)")
    print("  [[user_stance_dark_sector_ring_down_rate_is_cascade_stretched]] -- non-monotone")
    print("  [[user_stance_aoe_observer_frame_offset]] -- eps_AoE = 0.0506 canonical")
    print("  [[user_stance_cascade_lives_on_circles]] -- cyclic substrate for v2 model")
    print("  [[user_stance_epicycle_via_gear_plus_pin]] -- gear+pin per region")
    print("  [[user_stance_string_theory_instrument_first]] -- math-doesn't-lie drove v2 fix")
    print("  [[user_stance_identity_not_implementation_discipline]] -- identity-level claim")
    print("  [[user_stance_fractal_shadow]] -- 3D_s shadows of cascade projection")
    print("  [[feedback_every_doc_edit_faces_falsification]] -- each candidate falsifier-tested")
    print("  [[feedback_no_privileged_primitive_classes]] -- dissolve-before-promote default")
    print("  [[feedback_ndjson_over_bloated_json]] -- all outputs NDJSON")
    print("  [[feedback_concertmaster_md_writes]] -- agent inline; no .md file")
    print("  [[feedback_concertmaster_git_worktree_isolation]] -- zero git operations")
    print()
    print("=" * 78)

    # Final synthesis NDJSON
    records = []
    records.append({
        "kind": "synthesis_ranking",
        "candidates": [
            {"rank": 1, "candidate": "B_ring_balance", "score_pct": 80, "fails": 0},
            {"rank": 2, "candidate": "C_cascade", "score_pct": 70, "fails": 1},
            {"rank": 3, "candidate": "A_imprint", "score_pct": 50, "fails": 1},
        ],
        "user_lean_confirmed": True,
        "convergence_with_thread_2": True,
    })
    records.append({
        "kind": "thread_2_hypothesis_verdict",
        "v1_model": "multiplicative; degenerate by construction; cannot produce sign-flip",
        "v2_model": "local-time-shift via EOC phase shift; physically correct",
        "v2_sign_flip_at_now": False,
        "v2_sign_flip_at_near_peak": True,
        "verdict": "PARTIAL_CONFIRMATION_NEAR_PEAK",
        "interpretation": (
            "Local-epicycle perspective is structurally real and mathematically "
            "coherent. At canonical eps_AoE = 0.0506, max time-shift across sky "
            "is ~1.44 Gyr (~0.81% of ring-down period). Sign-flip across "
            "directions occurs at near-peak (a~2.14) when global rate is small."
        ),
    })
    records.append({
        "kind": "load_bearing_finding",
        "finding": (
            "Three candidate names each carry unique truth the others lack. "
            "Best falsifier survivor (B ring-balance, 8/10) still has known "
            "structural weakness (F3: cascade structure invisible in 'ring' noun)."
        ),
        "implication": (
            "Per [[user_stance_partition_for_understanding]] 2026-05-17 case-"
            "extension: linguistic partition we cannot un-bifurcate signals "
            "incomplete apprehension. Unified concept not yet apprehended. "
            "No single name suffices."
        ),
        "user_options": [
            ("commit_B_with_sister_clauses",
             "Commit B as canonical; record sister-clauses for A and C respectively"),
            ("hold_partition_continue_research",
             "Record three-candidate finding; continue follow-up; no single name yet"),
        ],
    })
    records.append({
        "kind": "thread_2_anomaly_investigation",
        "anomaly": "v1 multiplicative model could not produce sign-flip across directions",
        "investigation": (
            "v1 form f_local = f_global(a) * (1 + modulation(theta)) has "
            "df_local/dt = df_global/dt * (1 + modulation). Since modulation amplitude "
            "is small and positive, sign is locked to sign of df_global/dt."
        ),
        "verdict": (
            "Model defect, not hypothesis defect. Per [[user_stance_string_theory_"
            "instrument_first]] math-doesn't-lie: v2 time-shift model produces "
            "expected local-not-universal pattern at near-peak regime."
        ),
        "next": "v2 model adopted as canonical; v1 archived in records.",
    })
    records.append({
        "kind": "synthesis_final_recommendation",
        "concertmaster_lean": (
            "User-gated continues; B (ring-balance) is BEST SURVIVOR but NOT clean winner. "
            "Each candidate carries unique truth. Per case-extension, holding the partition "
            "is itself load-bearing."
        ),
        "fermata_for_conductor": [
            "Option 1: commit B with sister-clauses (A captures deposit; C captures structure)",
            "Option 2: hold partition; continue research; no single name yet",
        ],
        "math_structure_stands": (
            "c_k = eps^k * K_k(substrate) per Spike #42 finding + local-time-shift "
            "via EOC per Spike #42b v2 stand REGARDLESS of which noun is chosen."
        ),
    })

    out_path = OUT_DIR / "spike_42b_synthesis_records_2026-05-17.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"Emitted {len(records)} synthesis records to {out_path}")


if __name__ == "__main__":
    main()
