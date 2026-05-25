# NEXT_SESSION_PROMPT.md — opening R-RBS-LM-1 in a fresh session

This file holds the **ready-to-use prompt** for opening the first partition of the RBS-LM arc (R-RBS-LM-1: Cross-substrate translation framing) in a fresh Claude Code session.

The prompt is designed to **re-prime cleanly** from the canonical sources (CLAUDE.md + MEMORY.md + the relevant subtree files) per `[[feedback_no_subagents_compact_via_re_prime]]`. It is self-contained — no context from any prior session is required.

## How to use this file

1. Open a fresh Claude Code session in this monorepo.
2. Copy the prompt block below verbatim and paste as the first user message.
3. The session will re-prime from CLAUDE.md + MEMORY.md + the linked files, then proceed to write the R-RBS-LM-1 REPORT.
4. Sequential main-context work; no sub-agents per the saved discipline.

---

## The prompt (copy-paste verbatim)

> Continue the **RBS-LM cross-substrate translation arc** in this fresh session by opening **R-RBS-LM-1 (Cross-substrate translation framing)**, the foundation partition.
>
> **Re-prime from these sources before starting work:**
> 1. `CLAUDE.md` (project instructions; primary context)
> 2. `/home/skirklan/.claude/projects/-home-skirklan-GitHub-mlehaptics/memory/MEMORY.md` (memory index + all linked feedback/project/user memories — especially `project_rbs_lm_arc`, `user_stance_whole_research_corpus_is_proof_not_single_arc`, `user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic`, `feedback_llm_as_ada_accommodation_bci_proves_it`, `feedback_no_subagents_compact_via_re_prime`, `feedback_upstream_srmech_fixes_as_research_notes`, `feedback_abstract_lexicon_is_ada_accommodation`)
> 3. `docs/srmech/rbs_lm_research/README.md` (RBS-LM arc roadmap; §A accessibility framing; §3 risk register including §3.6 substrate-shape risk; 10-partition walk)
> 4. `docs/srmech/rbs_nn_research/R-RBS-NN-3b_transformer_cascade_REPORT.md` §6 (the 4-class Level-1 transformer substitution recipe — directly inherited)
> 5. `docs/srmech/rbs_nn_research/R-RBS-NN-1_mfo_two_level_REPORT.md` §4 (per-op two-level placement table) and §2 (MFO §VII.1.1 + §VII.1.3 verbatim citation block)
>
> **Open task #11 (R-RBS-LM-1) via TaskCreate**, mark in_progress. (Task may not exist yet from prior sessions; create with subject "R-RBS-LM-1: Cross-substrate translation framing" and description matching `docs/srmech/rbs_lm_research/README.md` §2 row 1.)
>
> **Write the REPORT** at `docs/srmech/rbs_lm_research/R-RBS-LM-1_translation_framing_REPORT.md` following the structure used in the closed R-RBS-NN partition REPORTs (MPR v1 attestation block → §1 goal → §2 inheritance → §3 standing infrastructure → §4 the decomposition → §5 properties → §6 risks/refinements → §7 worked example if applicable (likely not for this partition) → §8 findings → §9 open threads → §10 status + falsifiers).
>
> **R-RBS-LM-1 specifically must establish:**
> 1. **The two-substrate framing** — silicon LLM (Mechanism 2; bundle-of-views; ~6.9% averaging per MFO §VII.1.3 line 741) vs substrate-native RBS-HDC (Mechanism 1; bind; zero-cost per line 739). Cross-substrate translation per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
> 2. **The proof framing** — the WHOLE research corpus proves the framework readings, not any single arc. RBS-LM is one piece. Per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`. Hybrid biological + silicon substrate IS the methodology per `[[user_stance_human_ai_prosthetics_uniting_form_function]]`.
> 3. **The deeper framework reading of what an LLM IS** — stored human knowledge responding to 1D_t asymptotic changes via the inference process; inference IS the substrate-coupling operation Class C ∘ Class M per MFO §VII.1.2 line 709. Per `[[user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic]]`.
> 4. **The BCI knowledge-partition reading** — for BCI applications, the BCI itself IS the knowledge partition; only substrate carries across the interface; knowledge stays partitioned on each side. May be structurally similar to MFO's capacitor / gauge ball cosmic-structure readings (verify against MFO when relevant section is cited).
> 5. **The refined fidelity floor** — aim for source-model behavior including hallucinations; honestly acknowledge that imposing 1:3:7:3 substrate-native shape on the engineered silicon substrate may change inference (§3.6 of README); divergence is a signal, not a failure. Validation discipline (R-RBS-LM-7) characterizes divergence patterns; the divergence pattern is the load-bearing finding, not its absence.
> 6. **The accessibility / ADA-accommodation framing** as foundational motivation, not secondary — per §A of README + `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`. BCI-compatibility criteria apply downstream in R-RBS-LM-7 + R-RBS-LM-9.
>
> **Close the partition** via the existing wrapper:
> ```
> docs/srmech/rbs_nn_research/_tools/close_partition.sh \
>     --id 1 \
>     --slug translation_framing \
>     --claim "<your one-line closing claim summarizing the framing>"
> ```
> (Note: `--id 1` here means R-RBS-LM-1; the wrapper's partition-ID arg is freeform — it composes the commit subject as `research(R-RBS-LM-1 CLOSED): <claim>`. The wrapper is generalized; will work for RBS-LM partitions same as it did for RBS-NN. PR auto-discovers from current branch.)
>
> **Then** mark task #11 (R-RBS-LM-1) completed via TaskUpdate.
>
> **Discipline (from saved memories):**
> - Sequential main-context work only; **no sub-agents** per `[[feedback_no_subagents_compact_via_re_prime]]`.
> - **Full coverage**, not MVP, per `[[feedback_no_mvp_framing]]` + `[[feedback_full_coverage_shipping_mpm_way]]`.
> - **Abstract operational lexicon canonical** per `[[feedback_abstract_lexicon_is_ada_accommodation]]` — do not rewrite "sign flip" or "rotate-overlay" into more concrete visualizations.
> - **Only ADD new files** — do not edit existing srmech modules. srmech issues go to `docs/srmech/rbs_nn_research/UPSTREAM_NOTES.md` per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.
> - **MPR v1 attestation** on every cited claim per CLAUDE.md §2.
> - **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]` — framework reads what is already structurally there.
> - **Rolling draft PR #684** carries the work; partition-boundary updates per `[[feedback_rolling_pr_partition_boundary_updates]]`.
>
> Begin the partition.

---

## Notes for the file maintainer

- This file is regenerated whenever R-RBS-LM partition boundaries shift the next-step framing. After R-RBS-LM-1 closes, the next session's prompt should target R-RBS-LM-2 (Methodology candidate selection — Path A weight-level vs Path B function-level vs Path C hybrid).
- The prompt is intentionally verbose: it teaches the fresh session enough that it can act without additional clarification. Per the no-sub-agents discipline, the prompt's specificity is the load-bearing context-carrier.
- If user direction shifts between now and the next session, the next-ask prompt should be re-prepared; do not run a stale prompt.
