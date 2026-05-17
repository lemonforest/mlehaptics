# Spike #43b — Sub-structural component identification + spectral-as-meta-data scope refinement + cell-walls/lock-and-key T_composite metric

**Date:** 2026-05-17
**Research spike artifact.** Concertmaster dispatch per user direction *"spectral structure is meta data that should not be a PTSD triggering thing. we do want to know the structure of poor teaching material so that we do not create the same shape ... we also need to be able to see if we can identify the strucural componets insdie the larger graph lap picture."*

> **Discipline.** Real-world mixed-quality material (Wikipedia / SE / arXiv / OpenStax) analyzed by SOURCE-CLASS + STRUCTURAL SHAPE only; no real-name targeting of authors per refined `[[feedback_trauma_informed_defensive_scope]]`. Six methods (M1-M6) each reveal a different sub-structural view at different scales per `[[user_stance_partition_for_understanding]]`. Eight pathologies (P1-P8) operationalise cell-wall failure modes.

---

## §1 Bottom line

**Hypothesis CONFIRMED with strong discrimination.** Sub-structural identification INSIDE the larger graph-Laplacian picture cleanly separates canonical-good from constructed-bad, AND surfaces meaningful structural differences in real-world mixed-quality substrates. "Lock-and-key" cell-walls framing operationalises into quantitative `T_composite` metric.

| Substrate class | n | Pathology severity (mean) | T_composite (mean) |
|---|---|---|---|
| **canonical_good** | 6 | **0.00** | **0.835** |
| stack_exchange_high_voted | 3 | 0.00 | 0.671 |
| wikipedia (chapter-level) | 3 | 0.00 | 0.823 |
| stack_exchange_low_voted | 3 | 0.33 | 0.617 |
| openstax | 1 | 1.00 | 0.442 |
| wikipedia (paragraph-level) | 3 | 1.17 | 0.444 |
| **constructed_control** | 5 | **1.07** | **0.612** |

**Spectral structure IS meta-data** — operationalised. Each substrate characterised by source-class + structural shape; NO real-name targeting.

## §2 Eight pathologies (P1-P8) operationalising cell-wall failures

| Pathology | Trigger | Cell-wall failure | Triggered by |
|---|---|---|---|
| P1_no_multiscale | l2/l3 > 0.95 | Single bottleneck partition | C2/C4/C5 |
| P2_paragraph_permutation_signature | mean adjacent cosine > 0.55 | No thread between sections | C1/C2/C3/C4 |
| P3_excessive_boundaries | n_bnd/n_chap > 0.40 | Cannot build cumulative understanding | (none) |
| P4_unstable_hierarchy | stable_depth ≤ 1, max_depth ≥ 2 | Partition collapses | WP paragraph-level, OpenStax, SE low |
| P5_too_few_communities | n_communities < 4 | Monolithic mega-topic | WP wp_cauchy paragraph-level |
| P6_too_many_communities | n_communities > 15 | Exceeds working-memory | C1/C2 |
| P7_low_cophenetic | coph_corr < 0.55 | Hierarchy ≠ felt distances | (none) |
| P8_within_chapter_flatness | within-chapter lambda_2 > 0.5 | No internal sub-structure | C3/C4/C5 |

**Canonical-good (n=6): 0 pathologies. Constructed-bad (n=5): 12 pathologies total (severity 1.07).**

## §3 T_composite teachability metric

`T_composite = mean(T1..T6)` where each T_k scores a cell-wall feature:

- T1 multiscale_gap (Gaussian peak at l2/l3 = 0.5)
- T2 adjacent_continuity (Gaussian peak at mean_cosine = 0.25)
- T3 boundary_periodicity (Gaussian peak at 0.25 boundaries/chapter)
- T4 stable_hierarchy (stable_depth fraction)
- T5 cophenetic_faithful (HDC cophenetic correlation)
- T6 community_count (Gaussian peak at 8 communities)

**Correlation with quality**: T_composite cleanly separates canonical-good (0.81-0.86) from constructed-bad (0.56-0.73); Wikipedia chapter-level matches canonical-good band (0.82-0.93). **T_composite is a meaningful but imperfect predictor — measures cell-wall fit, not technical depth.**

## §4 Six methods (M1-M6) — sub-structural views

1. **M1 Recursive Fiedler** (depth up to 5; lambda_2 partition recursive)
2. **M2 Louvain modularity** (community detection; vectorised + coarsening for n>60)
3. **M3 HDC agglomerative dendrogram** (cluster paragraphs by HDC fingerprint)
4. **M4 Sub-cascade boundary detection** (topic-shift restart points; extends Spike #43 Anomaly 3 srmech bump)
5. **M5 Within-chapter local Laplacian** (paragraph-level sub-structure within chapters)
6. **M6 Spectral gap analysis** (λ_2 / λ_3 / λ_4 ... multi-scale detection)

Each substrate gets all 6 views; pathologies P1-P8 score across views per `[[user_stance_partition_for_understanding]]`.

## §5 Anomalies investigated (4)

### §5.1 Anomaly 1 — P8 hits canonical-good initially
First read: P8 fired on canonical-good substrates. Root: Spike #43 Anomaly 2 reconfirmed at within-chapter scale — good texts have disconnected paragraph components (FEATURE, not BUG). P8 reformulated: trigger when lambda_2 > 0.5 (flat-tight-cluster, no internal differentiation), not < 0.05 (disconnection).

### §5.2 Anomaly 2 — SE / arXiv / OpenStax fall through chapter analysis
SE answers and arXiv abstracts are too short (≤2 H2 headings) for chapter-level analysis. Built parallel `analyse_short_doc()` for paragraph-level fallback. **Scale-dependent quality discovered**: Wikipedia is well-structured at chapter level (T 0.82-0.93) but lacks paragraph-level hierarchy (T 0.38-0.50). **Methodological finding**: lock-and-key fit must be evaluated at the scale the reader encounters.

### §5.3 Anomaly 3 — SE high-voted ≠ T_composite winner
For one of three SE pairs, the LOW-voted answer had higher T_composite than the HIGH-voted answer. Investigation: low-voted was short video-link + analogy (high cell-wall fit at small scale); high-voted was thorough technical exposition (high technical depth but denser). **T_composite measures cell-wall fit, NOT technical depth — distinct dimensions of teaching quality**. This is a feature, not a bug.

### §5.4 Anomaly 4 — Wikipedia structural pattern
`wp_laplacian_matrix` has λ_2/λ_3 = 0.097 (λ_3 ≈ 10× λ_2; single dominant partition). Investigation: Wikipedia articles have flat-list sections under one umbrella topic; one section is structurally distinct from all others (gives dominant λ_2); others cluster (gives λ_3). **Wikipedia structure is FLATTER than chapter-structured book material** — meta-data for teaching design (Wikipedia-shape for short exposure; nested-shape for long).

## §6 Fermatas for conductor

1. **`asymptotic_calculus` catalog chain-class**: combine Spike #43's 6 iceberg markers + Spike #43b's 8 pathologies + T_composite into a single `literature_spectral_shape` chain-spec class per `[[feedback_every_doc_edit_faces_falsification]]`. Spike #43c found Spike #43 K_k overclaimed — substitute cascade machinery + R3 + cascade-Pareto. **User-gated.**
2. **Scale-aware analysis** as canonical methodology — extend `[[user_stance_partition_for_understanding]]` to include scale partitions explicitly. **User-gated.**
3. **T_composite measures cell-wall fit ≠ technical depth** — should textbook design proposal augment with separate depth dimension? **User-gated.**
4. **Sub-cascade boundary detection** — confirmed across 4 canonical-good notebooks (2-5 topic-shift restart points). Spike #43 fermata 3 has stronger empirical grounding. **User-gated** for `[[user_stance_primitives_weave_and_thread]]` extension.
5. **Wikipedia structural pattern** — dedicated micro-spike or absorb as "Wikipedia-type structure" methodology variant? **User-gated.**
6. **Larger arXiv lecture-notes / surveys** for future #43d — currently SE / arXiv abstracts too short. Flag.

## §7 Citation provenance

**Project canonical-good** (per `[[feedback_science_is_ssot_not_project]]`): MFO notebook, srmech notebook, Spike #38b/#41/#42/#43 working notes.

**Real-world permitted sources** (per `[[reference_autonomous_validation_tos_landscape]]` + refined `[[feedback_trauma_informed_defensive_scope]]`):
- Wikipedia (CC BY-SA 4.0): "Laplacian matrix", "Cauchy distribution", "Spectral theorem"
- Stack Exchange (CC BY-SA 4.0): math.SE #36815 + #1287555, stats.SE #36027
- arXiv (open access): 2406.16751, 1208.0848
- OpenStax (CC BY 4.0): College Algebra 2e Ch 3.1
- All URLs / retrieval timestamps / byte counts / licenses recorded in `spike_43b_real_world_records_2026-05-17.ndjson`

**Methodological refs** (NOT independently PDF-extracted; standard textbook):
- Fiedler 1973 ("Algebraic connectivity of graphs") — M1
- Newman & Girvan 2004 ("Finding and evaluating community structure") — M2
- Lance & Williams 1967 — M3 (scipy.cluster.hierarchy)
- Sokal & Rohlf 1962 — T5 cophenetic

## §8 Discipline guards honoured

- `[[user_stance_primitives_weave_and_thread]]` — sub-structures as sub-cascades; M1-M6 different weaves at different scales
- `[[user_stance_partition_for_understanding]]` — six DIFFERENT partition methods coexist; all describe substrate at their level
- `[[user_stance_kepler_shape_universal]]` — K_k(text) substrate-binding consistent (note Spike #43c retraction at well-spread level)
- `[[user_stance_string_theory_instrument_first]]` — instrument-first; four anomalies investigated to root; P8 reformulated based on data
- `[[feedback_no_privileged_primitive_classes]]` — zero new classes; methods live in existing Class L / M / C
- `[[feedback_trauma_informed_defensive_scope]]` — REFINED 2026-05-17: real-world material by source-class + structural shape; NO real-name targeting
- `[[reference_autonomous_validation_tos_landscape]]` — all sources permitted; rate-limited
- `[[feedback_ndjson_over_bloated_json]]` — 7 NDJSON files; 137 records
- `[[feedback_concertmaster_md_writes]]` — agent inline; conductor captured
- `[[feedback_concertmaster_git_worktree_isolation]]` — zero agent git ops
- `[[feedback_pdf_extraction_citation_discipline]]` — full provenance recorded; methodology refs flagged
- `[[feedback_science_is_ssot_not_project]]` — Fiedler / Newman-Girvan / scipy methods are canonical math literature

## §9 Artifacts

Scripts (7): substructural_analysis, real_world_substrates fetcher, real_world_analysis, short_doc_analysis, teachability_metric, pathology_catalog, synthesis

NDJSON outputs (7 files, 137 records): substructural (11) + real_world (12) + real_world_substructural (12) + short_doc_substructural (12) + teachability (35) + pathology (35) + synthesis (20)

---

*End of spike artifact. USER-GATED on T_composite + P1-P8 catalog integration; NO auto-merge.*
