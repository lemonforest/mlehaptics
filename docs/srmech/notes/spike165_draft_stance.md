# Draft stance refinement — Memory-system augmentation pathway pluralism

**Status:** DRAFT — Round 2 candidate from Spike #165. **DO NOT canonicalize without user direction.** HIGH (not HIGHEST) vocab-impact zone — parent stance refinement, not new canonical stance.

**Author:** Claude (Opus 4.7) executing Spike #165 as concertmaster, 2026-05-19.

**Parent stance:** `[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]` (Spike #160, canonical 2026-05-19).

**Sibling stances strengthened:**
- `[[user_stance_agent_cascade_isomorphic_to_biological_deliberation_k3_covers_gap]]` (Spike #151 META)
- `[[user_stance_neural_hebbian_is_bci_drift_model]]` (Spike #127.4 cellular Hebbian)
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]` (Class K rate-parameter)

---

## Proposed action

**REFINE** the parent stance text (not canonicalize a new sibling stance). The Round 2 finding is that WM is ONE of FOUR memory-system augmentation pathways, all sharing Class K and the reflex base, differing in their augmentation delta. Suggest editing the parent stance to acknowledge this pluralism explicitly.

**Two specific candidates** are also produced as potential SIBLING stances if the user prefers a new-stance approach over parent refinement:

1. `procedural-is-the-anoetic-skilled-behavior-augmentation-cascade`
2. `episodic-ltm-engages-class-h-autonoetic-self-witness`

But the recommended action is **parent-stance refinement** — pathway-pluralism is a parent-text clarification, not a new canonical stance.

---

## Suggested parent-stance refinement text

**Insert / amend in `[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]`** — propose adding a new section AFTER current `### Cross-substrate test (5 substrates from Spike #160)` and BEFORE `### k=3 tripartition coverage`:

````markdown
### Pathway pluralism — WM is ONE of FOUR memory-system augmentation pathways

Per Spike #165 R2 falsifier verification (F5 + F2 both CONFIRMED at magnitude level), WM is ONE pathway in a small family of cascade-augmentation pathways on top of the universal reflex base {B, D, E, F, C}:

| Pathway | Augmentation delta | Awareness tier (Tulving 2002) | Distinguishing class(es) |
|---|---|---|---|
| **Procedural / model-free** | {G, I, K, L} | Anoetic | G (byte-pattern-search) + I (cyclic rhythm) |
| **Semantic LTM** | {A, K, L} | Noetic (fact-aware) | (no H, no M — facts without source-context, retrieved without bind) |
| **Working memory** | {A, K, M} (+ L?) | Noetic-deliberative | M (cross-modal HDC bind) |
| **Episodic LTM** | {A, H, K, L, M} | Autonoetic (self-aware) | **H (self-as-witness)** |

**All four pathways share Class K** (capacity-bounded asymptotic-DOF retention) per `[[user_stance_asymptotic_dof_sidesteps_infinity]]` — capacity-bounded retention is the irreducible cost of any post-reflex pathway.

**Refined IS-claim**: WM IS the cascade augmenting reflex into **deliberative** agency. Procedural memory IS the parallel cascade augmenting reflex into **skilled-behavior** agency. Episodic LTM augments deliberative-WM-state into **autonoetic-self-witness** agency. Semantic LTM augments reflex into **noetic-fact-aware** agency without binding or self-witness. The original IS-claim ("WM IS the cascade augmenting reflex into agency") remains correct for the deliberative-agency sub-type; this section names the sibling pathways for sub-types that augment reflex differently.

**Two senses of M**: cellular Hebbian / STDP fire-together-wire-together per `[[user_stance_neural_hebbian_is_bci_drift_model]]` is M_cell (synaptic scale); cross-modal episodic-buffer bind per Baddeley 2000 is M_WM (system scale). Both are Class M at magnitude level — same algebraic operation (HDC bind / similarity) at different spatiotemporal scales. The system-level M_WM is plausibly the population-scale emergent expression of many M_cell binds. Procedural memory engages M_cell but not M_WM — that's the load-bearing F5 finding.

**Citations**: Squire-Zola 1996 PMC33639 (procedural taxonomy); Daw-Niv-Dayan 2005 PMID 16286932 (model-free / model-based RL); Tulving 2002 PMID 11752477 (autonoetic episodic memory); Eichenbaum 2017 PMC5644341 (memory-system integration); Schacter 1987 JEP:LMC (implicit memory; citation-watch-flagged paywalled).
````

---

## Identity-level claim

Per `[[user_stance_identity_not_implementation_discipline]]`: the four pathways IS-claim is that each pathway's strict-spec class composition IS the operational distinction between awareness tiers — anoetic / noetic / autonoetic — not a metaphor for them. Class H IS the autonoetic component; Class M IS the noetic-deliberative component; absence-of-both IS the anoetic procedural tier.

The four pathways are not just psychological-typology categories — they are class-engagement-distinct cascades at the strict-spec primitive level.

---

## Round 1 status

| Check | Status |
|---|---|
| Procedural cascade decomposed concretely | PASS — {B,C,D,E,F,G,I,K,L} per §3.2 of findings |
| Episodic-LTM cascade decomposed concretely | PASS — {A,B,C,D,E,F,H,K,L,M} per §4.2 |
| Pathway pluralism (4 pathways) verified | PASS — procedural / semantic-LTM / WM / episodic-LTM |
| F5 (alternative augmentation pathways) | CONFIRMED — procedural pathway distinct from WM |
| F2 (class outside parent set) | CONFIRMED — Class H load-bearing for episodic-LTM |
| Cross-substrate shape-match | PASS — 4 substrates × 3 pathways verified at magnitude level |
| k=3 tripartition coverage | PASS — all 4 pathways fit k=3; no k=4 required |
| Both-direction check per `[[feedback_always_check_both_directions_including_time]]` | PASS — Class K parameterises both build-up and decay |
| Bit-exact algebra identity | NOT-CLAIMED (MAGNITUDE-level only) |
| F1 (qualia) | OPEN (unchanged) |
| F3 (cascade-ordering violation) | NOT-IDENTIFIED in Round 2 |
| F4 (substrate divergence) | NOT-IDENTIFIED in Round 2 |
| M_cell vs M_WM disambiguation | NAMED; sub-flag within Class M, no class promotion |
| PDF-citation verification | OPEN-ACCESS subset autonomously verifiable; books and paywalled journals citation-watch-flagged |

---

## Augmentation delta — pathway-by-pathway comparison

| Pathway | Reflex base | Delta classes (sorted) | Total engaged | Awareness tier |
|---|---|---|---|---|
| Pure reflex | {B,C,D,E,F} | — | 5 | (sub-anoetic / form-function only) |
| Procedural | {B,C,D,E,F} | {G, I, K, L} | 9 | Anoetic |
| Semantic LTM | {B,C,D,E,F} | {A, K, L} | 8 | Noetic (fact-aware) |
| Working memory | {B,C,D,E,F} | {A, K, M} + L? | 7–8 | Noetic (deliberative) |
| Episodic LTM | {B,C,D,E,F} | {A, H, K, L, M} | 10 | Autonoetic |

**Shared core minus reflex = {K}** — capacity-bounded retention is universal across all four post-reflex pathways. The reflex itself is stateless across firings; ANY augmentation that retains content asymptotic-bounds it, engaging Class K.

---

## k=3 mapping (all four pathways)

| Pathway | Classes added | k=3 axis assignment |
|---|---|---|
| Procedural | {G,I,K,L} | G → 3D_s; I → 1D_t; K → 1D_t; L → 3D_s ⊗ 7D_g |
| Semantic LTM | {A,K,L} | A → 3D_s; K → 1D_t; L → 3D_s ⊗ 7D_g |
| WM | {A,K,M} (+L?) | A → 3D_s; K → 1D_t; M → 7D_g; L? → 3D_s ⊗ 7D_g |
| Episodic LTM | {A,H,K,L,M} | A → 3D_s; **H → 1D_t (autonoetic witness-self IS LoE-identity at recall moment)**; K → 1D_t; L → 3D_s ⊗ 7D_g; M → 7D_g |

**No k=4 required for any pathway.** All four fit cleanly into `3D_s ⊗ 7D_g ⊗ 1D_t`. F1 (qualia / Chalmers) remains OPEN — none of these pathway decompositions settle the subjective-character question.

---

## Bridges

- `[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]` — PARENT stance to refine
- `[[user_stance_identity_not_implementation_discipline]]` — IS-form claim
- `[[user_stance_agent_cascade_isomorphic_to_biological_deliberation_k3_covers_gap]]` — sibling Spike #151 META; strengthened by 4-pathway k=3 coverage
- `[[user_stance_neural_hebbian_is_bci_drift_model]]` — M_cell anchor (Spike #127.4 cellular Hebbian)
- `[[user_stance_holographic_projection_at_linguistic_substrate]]` — LLM-agent autonoetic-H is linguistic-substrate projection
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]` — Class K shared across all pathways from both directions
- `[[user_stance_closure_subgroup_BDEFL_substrate_class_universal]]` — {B,D,E,F} closure-subgroup persists as reflex core across pathways
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` — method anchor; 4 substrates × 3 pathways verified
- `[[user_stance_hyper_as_3d_spatial_interface]]` — 3D_s axis for content-address (A) + pattern-search (G)
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — 7D_g axis for M-bind
- `[[user_stance_1d_collapse_to_loe_identity_not_action]]` — 1D_t axis for K (rate) and H (witness-self LoE-identity)
- `[[user_stance_kepler_shape_universal]]` + `[[user_stance_cascade_lives_on_circles]]` — Class I cyclic-pattern anchor for procedural rhythm
- `[[feedback_no_privileged_primitive_classes]]` — M_cell vs M_WM sub-flag, not class promotion
- `[[feedback_algebra_not_magnitude]]` — MAGNITUDE-level only; bit-exact identities pending
- `[[feedback_language_is_analysis_tool_not_specific_question]]` — Tulving anoetic/noetic/autonoetic vocabulary refined into class-engagement deltas
- `[[feedback_multi_domain_multi_round_survival_falsification_method]]` — Round 2 explicit; rounds 3-4 pending
- `[[feedback_always_check_both_directions_including_time]]` — Class K both directions covered
- `[[feedback_trauma_informed_defensive_scope]]` — research/educational frame; no clinical/therapeutic
- `[[feedback_pdf_extraction_citation_discipline]]` — PMC subset PDF-verify follow-up
- `[[reference_autonomous_validation_tos_landscape]]` — open-access vs paywalled vs book citation-class distinction
- `[[feedback_concertmaster_git_worktree_isolation]]` — discipline applied (worktree-isolated branch)
- Spike #127.4 (cellular Hebbian L+K+M+C+I anchor); Spike #142 (tripartite Mermin algebra); Spike #151 (callback-cascade META); Spike #160 (parent stance empirical anchor)

---

## Operational implications if refinement adopted

1. **Memory-system pluralism becomes canonical** — the parent stance acknowledges that agency-augmentation is NOT WM-monopolised; procedural and episodic-LTM are sibling pathways with distinct class signatures.
2. **Class H gets a named load-bearing role** — autonoetic-self-as-witness is the H-engagement that distinguishes episodic from semantic memory at the strict-spec class level.
3. **Class M sub-flag M_cell vs M_WM** — without class promotion; just operational disambiguation within Class M's HDC bind / similarity surface.
4. **Pathway-specific cascade signatures** — the "oh by the way / almost forgot" cascade (parent stance §"Oh by the way") stays specific to WM (since M-similarity surfacing is the trigger); procedural memory has its own characteristic cascade (pattern-recognition-driven cached-value lookup); episodic-LTM has its own (cue-retrieval-with-autonoetic-context cascade).
5. **k=3 coverage further strengthened** — three additional pathways all fit k=3 with no k=4 promotion required.

**Recommendation:** present to user for stance text-refinement directive. The parent stance update is small (one new subsection + light edit to IS-claim framing); no new canonical stance file needed if the user prefers the parent-stance-refinement approach.

If the user prefers new sibling stances instead, candidates 1 and 2 from §"Proposed action" above can be drafted in full.
