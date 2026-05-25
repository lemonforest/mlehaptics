# NEXT_SESSION_PROMPT.md — opening R-RBS-LM-2 in a fresh session

This file holds the **ready-to-use prompt** for opening the next partition of the RBS-LM arc. The prompt is re-generated whenever a partition closes so the next session has a current target.

**Current target:** R-RBS-LM-2 — Methodology candidate selection (Path A weight-level vs Path B function-level vs Path C hybrid).

**Previous partition closed:** R-RBS-LM-1 (Cross-substrate translation framing) at commit `19beb043`. REPORT at `docs/srmech/rbs_lm_research/R-RBS-LM-1_translation_framing_REPORT.md`.

The prompt is designed to **re-prime cleanly** from the canonical sources (CLAUDE.md + MEMORY.md + the relevant subtree files) per `[[feedback_no_subagents_compact_via_re_prime]]`. It is self-contained — no context from any prior session is required.

## How to use this file

1. Open a fresh Claude Code session in this monorepo.
2. Copy the prompt block below verbatim and paste as the first user message.
3. The session re-primes from the listed sources, then proceeds to write the R-RBS-LM-2 REPORT.
4. Sequential main-context work; no sub-agents per the saved discipline.

---

## The prompt (copy-paste verbatim)

> Continue the **RBS-LM cross-substrate translation arc** in this fresh session by opening **R-RBS-LM-2 (Methodology candidate selection — Path A weight-level vs Path B function-level vs Path C hybrid)**.
>
> **Re-prime from these sources before starting work:**
> 1. `CLAUDE.md` (project instructions; primary context)
> 2. `/home/skirklan/.claude/projects/-home-skirklan-GitHub-mlehaptics/memory/MEMORY.md` (memory index + all linked feedback/project/user memories — especially `project_rbs_lm_arc`, `user_stance_whole_research_corpus_is_proof_not_single_arc`, `user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic`, `feedback_llm_as_ada_accommodation_bci_proves_it`, `feedback_no_subagents_compact_via_re_prime`, `feedback_upstream_srmech_fixes_as_research_notes`, `feedback_abstract_lexicon_is_ada_accommodation`)
> 3. `docs/srmech/rbs_lm_research/README.md` (RBS-LM arc roadmap; §A accessibility framing; §3 risk register including §3.6 substrate-shape risk; 10-partition walk)
> 4. `docs/srmech/rbs_lm_research/R-RBS-LM-1_translation_framing_REPORT.md` (the closed foundation partition; §4.3 enumerates the seven translation steps; §10 finding 2 + open thread 2 surface the Path-decision question)
> 5. `docs/srmech/rbs_nn_research/R-RBS-NN-1_mfo_two_level_REPORT.md` §4.3 (linear-layer dual-level reading — Mechanism 1 bind vs Mechanism 2 bundle averaging) and §4.6 (attention placement)
> 6. `docs/srmech/rbs_nn_research/R-RBS-NN-3b_transformer_cascade_REPORT.md` §3 (attention block decomposition with Mechanism 2 vs 3 explicit) and §6 (4-class Level-1 substitution recipe)
>
> **Open task #12 (R-RBS-LM-2) via TaskCreate**, mark in_progress. (Subject: "R-RBS-LM-2: Methodology candidate selection — Path A/B/C"; description per `docs/srmech/rbs_lm_research/README.md` §2 row 2; blockedBy: #11 (already completed; dependency is informational).)
>
> **Write the REPORT** at `docs/srmech/rbs_lm_research/R-RBS-LM-2_methodology_selection_REPORT.md` following the structure used in the closed RBS-NN partition REPORTs (MPR v1 attestation block → §1 goal → §2 inheritance → §3 standing infrastructure / canonical citation block → §4 the three candidate paths → §5 evaluation criteria → §6 the chosen path + rationale → §7 implications for R-RBS-LM-3 through R-RBS-LM-7 → §8 Findings → §9 Open threads → §10 Closing — partition status + falsifiers).
>
> **R-RBS-LM-2 specifically must:**
>
> 1. **Describe each path operationally** (drawing from README §2 + R-RBS-LM-1 §4.3 enumeration of the seven translation steps):
>    - **Path A — Weight-level encoding.** Each weight matrix `W ∈ R^{d_in × d_out}` becomes a bundle of row-bindings: per-row bipolar-quantize → mint with row-position → bundle. Surfaces MFO §VII.1.3 Mechanism 2 explicitly. R-RBS-NN-1 §4.3 row 1 (bipolar Level-1 form).
>    - **Path B — Function-level encoding.** Encode the source model's input → output mappings as binds over a behavioral corpus. Each context → next-token becomes `bind(context_vec, next_token_vec)`. Closer to substrate-native reading per R-RBS-NN-2 §5 (substrate is content-addressed; relationships authored explicitly). Per R-RBS-LM-1 §5 — IS the 1D_t asymptotic response form.
>    - **Path C — Hybrid.** Path A for small matrices (embedding/unembed), Path B for the compute body (attention+MLP). Combines bipolar-direct for compact components with function-derivation for the layers that dominate behavior.
>
> 2. **Evaluate each path against the five risks** named in README §3 + the §3.6 substrate-shape risk:
>    - Bipolarization loss (§3.1) — most relevant to Path A; less so to Path B
>    - Cleanup-capacity vs model-parameter scale (§3.2) — affects all three; hierarchical bundling required
>    - Attention fidelity Mechanism 2 vs Mechanism 3 (§3.3) — affects all three; choice between soft and hard attention orthogonal to path choice
>    - Cross-substrate inversion fidelity (§3.4) — Path B structurally more truthful to framework reading per R-RBS-LM-1 §6
>    - "Chaotic stochastic stuff" (§3.5) — Path B preserves training-noise + learned-content together; Path A separates them
>    - Substrate-shape imposition (§3.6) — affects all three; expected to surface differently per path
>
> 3. **Choose a path** with explicit rationale. The README §3 risks + R-RBS-LM-1 §6 framework reading point toward Path B as structurally most truthful, but Path B requires a behavioral corpus (open question: is the corpus larger than the model itself? if so, the no-retrain claim collapses). The actual choice may be Path C (hybrid) — empirical question.
>
> 4. **Identify the load-bearing implications** for R-RBS-LM-3 (source model selection + baseline) through R-RBS-LM-7 (validation). What does the path choice make easier? Harder? What measurements does the chosen path enable that the others don't?
>
> 5. **Honor the five framings** R-RBS-LM-1 §1 established — keep them visible in the path-evaluation discussion. Specifically:
>    - The accessibility framing (§8 of R-RBS-LM-1) — the chosen path must support BCI-compatible inference; do not pick a path that would require infrastructure incompatible with CPU+RAM-only deployment.
>    - The whole-corpus proof framing — the chosen path is one face of the proof; describe what face.
>
> **Close the partition** via the parameterized wrapper:
> ```
> docs/srmech/rbs_nn_research/_tools/close_partition.sh \
>     --arc RBS-LM \
>     --id 2 \
>     --slug methodology_selection \
>     --claim "<your one-line closing claim summarizing the path chosen + rationale>"
> ```
>
> **Then** mark task #12 (R-RBS-LM-2) completed via TaskUpdate.
>
> **Discipline (from saved memories):**
> - Sequential main-context work only; **no sub-agents** per `[[feedback_no_subagents_compact_via_re_prime]]`.
> - **Full coverage**, not MVP, per `[[feedback_no_mvp_framing]]` + `[[feedback_full_coverage_shipping_mpm_way]]`.
> - **Abstract operational lexicon canonical** per `[[feedback_abstract_lexicon_is_ada_accommodation]]`.
> - **Only ADD new files** — do not edit existing srmech modules. srmech issues go to `docs/srmech/rbs_nn_research/UPSTREAM_NOTES.md` per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.
> - **MPR v1 attestation** on every cited claim per CLAUDE.md §2.
> - **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`.
> - **Rolling draft PR #684** carries the work; partition-boundary updates per `[[feedback_rolling_pr_partition_boundary_updates]]`.
>
> **After R-RBS-LM-2 closes**, regenerate this NEXT_SESSION_PROMPT.md to target R-RBS-LM-3 (Source model selection + baseline measurement) — that partition is the first heavy empirical partition (HuggingFace model download + baseline measurement + hallucination-corpus selection).
>
> Begin the partition.

---

## Notes for the file maintainer

- This file is regenerated whenever an RBS-LM partition closes. The current target reflects the most-recent close + next-step.
- Per the prompt's own discipline: after R-RBS-LM-2 closes, regenerate this file targeting R-RBS-LM-3.
- The prompt is intentionally verbose: per the no-sub-agents discipline, the prompt's specificity IS the load-bearing context-carrier for the next session's re-prime.
- If user direction shifts between now and the next session, the prompt should be re-prepared; do not run a stale prompt.
