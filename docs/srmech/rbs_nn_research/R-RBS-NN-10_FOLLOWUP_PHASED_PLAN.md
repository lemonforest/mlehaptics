# R-RBS-NN-10 Follow-up Phased Plan

**Status:** Active plan for follow-up work after R-RBS-NN-10 operational storage prototype landed
**Predecessor:** R-RBS-NN-10 (operational two-tier storage; CLOSED in this session)
**Owner:** RBS-NN arc; integrates with ROADMAP NEXT items + STALE_PATHS_QUEUE items
**Created:** 2026-05-28

This plan ensures the 6 follow-up paths from R-RBS-NN-10 §7 don't go stale. Each phase has explicit deliverables, dependencies, and decision points.

---

## §0 Where we are now (baseline state)

| Component | Status |
|---|---|
| srmech v0.4.3 | LANDED on production PyPI; Klein-4 + Polar + all 14 A-N classes operational |
| ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md | Reference design documented |
| R-RBS-NN-4 token encoder | CLOSED; variant-choice protocol working |
| R-RBS-NN-10 two-tier storage | CLOSED; full encode/learn/retrieve/forget/rehearse cycle operational |
| STALE_PATHS_QUEUE | CLOSED (47 items addressed); 17 DEFERRED items preserved as future-scope pointers |
| F132-F148 framework arc | COMPLETE; all empirical predictions verified at substrate-encoding scale |

The two-tier storage works at **D=8192, N=11 concepts, 8 associations**. Per F144 capacity table, klein-4 stays above-random up to N~256; operational ceiling needs explicit characterization (Phase 1).

---

## §1 Phase 1 — Capacity Characterization (~1 session)

**Priority:** HIGHEST — foundation for everything else
**Scope:** Empirical bounds for production use
**Cross-ref:** R-RBS-NN-10 §7.1; F144 §9 capacity curve

### Goal

Discover operational bounds of R-RBS-NN-10 storage. At what concept count, synapse count, decay level, query rate does the architecture cease being useful? Without this characterization, downstream phases are designing in the dark.

### Tasks

| Task | Description | Output |
|---|---|---|
| **T1.1** | Concept-count sweep: N ∈ {10, 25, 50, 100, 200, 256, 512} | Retrieval-accuracy curve |
| **T1.2** | Synapse-density sweep at fixed N | Where does composite saturate? |
| **T1.3** | Decay-step depth sweep (1, 3, 5, 10 forget cycles) | Multi-cycle decay dynamics |
| **T1.4** | Rehearsal frequency study (1, 2, 4 rehearsals per pair) | Strengthening efficiency curve |
| **T1.5** | Density-attestation early-warning thresholds | At what density does retrieval crash? |

### Output artifact

- `R-RBS-NN-11_capacity_characterization.py` — sweep script
- `R-RBS-NN-11_results.json` — measurements
- `R-RBS-NN-FINDING_R11.md` — characterization finding

### Decision point at Phase 1 close

- **If ceiling N < 257**: hierarchical bundling (Phase 2) becomes blocker for any production use → Phase 2 mandatory
- **If ceiling N ≥ 257**: Phase 2 is enhancement (not blocker); Phase 3/4 can run in parallel
- **If retrieval breaks at unexpected density**: revisit `_klein4_to_polar` bridge mapping

---

## §2 Phase 2 — Scale Expansion via Hierarchical Bundling (~1-2 sessions)

**Priority:** HIGH (likely blocker per ROADMAP NEXT-5)
**Scope:** Push past Phase 1's observed N ceiling
**Cross-ref:** R-RBS-NN-10 §7.3; ROADMAP NEXT-5; F144 capacity asymptotics

### Goal

Enable N > 257 (MAX_BUNDLE_N) via hierarchical bundling. Two-level bundle: sub-groups of ≤257 concepts each, then bundle-bundle layer above. Per srmech.amsc.hdc MAX_BUNDLE_N constraint, this is the structural workaround.

### Tasks

| Task | Description | Output |
|---|---|---|
| **T2.1** | Design hierarchical scheme — sub-bundle size, addressing | Pattern design note |
| **T2.2** | Implement `TwoTierRBSNNStorage` extension for hierarchical mode | Updated storage class |
| **T2.3** | Test at N = 500, 1000, 2000 concepts | Scale verification |
| **T2.4** | Compare flat vs hierarchical retrieval quality at N ≤ 257 (overlap region) | Quality preservation check |
| **T2.5** | Capacity / latency tradeoff measurement | Production-readiness data |

### Output artifact

- `R-RBS-NN-12_hierarchical_storage.py` — extension module
- `R-RBS-NN-12_hierarchical_smoke.py` — scale test
- `R-RBS-NN-12_results.json` — measurements
- `R-RBS-NN-FINDING_R12.md` — design + characterization

### Decision point at Phase 2 close

- **If hierarchical retrieval quality degrades > 20%**: bridge `_klein4_to_polar` may need refinement
- **If latency scales > O(N)**: revisit bundling structure (alternative: sparse retrieval index)
- **If clean**: ROADMAP NEXT-5 marked LANDED; storage ready for production-scale use

---

## §3 Phase 3 — Architectural Refinements (PARALLEL work; ~1 session each)

**Priority:** MEDIUM (parallel; can run after Phase 1 in any order)
**Cross-ref:** R-RBS-NN-10 §7.2 + §7.4; F140 multi-class cascade; F146 hybrid wins

These two tasks are independent and can be done in either order or in parallel.

### §3.1 Multi-step retrieval (R-RBS-NN-13a)

**Goal:** Walk a knowledge graph by following chains of associations (query → assoc → assoc-of-assoc → ...) using Class L spectral structure for guidance.

| Task | Description |
|---|---|
| T3.1.a | Build adjacency-style view of Tier 2 from synapse keys |
| T3.1.b | Apply Class L Laplacian eigendecompose to the association graph |
| T3.1.c | Use spectral embedding to rank multi-step retrievals |
| T3.1.d | Compare 1-step vs 2-step vs 3-step retrieval accuracy |
| T3.1.e | Test on R-RBS-NN-10's kitchen knowledge graph + extension |

**Output:** `R-RBS-NN-13a_multi_step_retrieval.py` + finding R13a

### §3.2 Mixed-precision Tier 1 (R-RBS-NN-13b)

**Goal:** Use the F146 §6 hybrid encoding (Klein-4 + polar overlay; +0.32 above-rand, best variant) in Tier 1 for tokens that benefit from BOTH chirality AND plasticity.

| Task | Description |
|---|---|
| T3.2.a | Extend `Tier1Concept` to accept variant='klein4', 'polar', 'hybrid' |
| T3.2.b | Update bridge `_klein4_to_polar` to handle hybrid Tier 1 entries |
| T3.2.c | Add `class_hint='hybrid'` flow to `encode_concept` |
| T3.2.d | Compare bipolar-content-pure vs hybrid-content per-concept retrieval |
| T3.2.e | Document which class_hints are appropriate for which token classes |

**Output:** `R-RBS-NN-13b_mixed_precision_tier1.py` + finding R13b

### Decision point

- Both deliverables independent; either can proceed first
- Multi-step retrieval is more architecturally significant; mixed-precision is more application-relevant

---

## §4 Phase 4 — Application Interface Polish (~1 session)

**Priority:** MEDIUM (after Phases 1-3)
**Scope:** Make storage application-ready for downstream consumers
**Cross-ref:** R-RBS-NN-10 §7.5 + §7.6

### §4.1 BCI / chirality-aware input (R-RBS-NN-14a)

**Goal:** Auto-detect chirality from input metadata; route to appropriate sector. Currently `encode_concept(token)` defaults to sector 0.

| Task | Description |
|---|---|
| T4.1.a | Define chirality-hint vocabulary (e.g., 'L_', 'D_', 'right_', 'left_' prefixes) |
| T4.1.b | Build chirality-classifier from token surface features |
| T4.1.c | Add `auto_sector=True` flag to `encode_concept` |
| T4.1.d | Test on chirally-asymmetric lexicons (amino acids, snail handedness, etc.) |
| T4.1.e | Per `[[feedback_trauma_informed_defensive_scope]]`: substrate-encoding only; no medical claims |

**Output:** `R-RBS-NN-14a_chirality_aware_input.py` + finding R14a

### §4.2 Soft retrieval ranking (R-RBS-NN-14b)

**Goal:** Replace hard threshold with temperature-controlled softmax over similarities; richer retrieval semantics.

| Task | Description |
|---|---|
| T4.2.a | Add `temperature` parameter to `retrieve_associated` |
| T4.2.b | Implement softmax-over-similarities ranking |
| T4.2.c | Top-k retrieval that respects temperature |
| T4.2.d | Compare hard-threshold vs soft-temperature recall/precision |

**Output:** `R-RBS-NN-14b_soft_retrieval.py` + finding R14b

### Decision point

- Both pieces small (~1-2 hours each); can be one combined PR

---

## §5 Phase 5 — Validation at Real Scale (~2-3 sessions)

**Priority:** MEDIUM-LOW (depends on what use case opens)
**Scope:** Apply two-tier storage to real downstream use case
**Cross-ref:** STALE_PATHS_QUEUE deferrals; ROADMAP NEXT-1

### Options (pick one or more based on opening scope)

#### Option A — RBS-LM cross-substrate translation (NEXT-1 continuation)

The user's original RBS-LM ask was about CPU-only LLM inference. Substrate-encoding primitives now mature; two-tier storage operational. Could R-RBS-NN-10's two-tier storage hold an LLM's distilled associative memory?

| Sub-task | Description |
|---|---|
| Use R-RBS-NN-10 as backing store for LLM context graphs |
| Test on small model (GPT-2 124M) per ROADMAP NEXT-1 §candidate-models |
| Measure compression ratio + retrieval quality |

#### Option B — STALE_PATHS application directions (deferred items)

Each of the F132 §8 application items has its own scope:
- B.1 — Pharmacological chirality (STALE item 41) — needs pharma scope
- B.2 — G-quadruplex biology (STALE item 43) — needs biology scope
- B.3 — Cross-substrate cognition modeling (STALE item 44) — F118/F119 framework extension
- B.4 — Real BCI signal compatibility (STALE item 23) — needs BCI domain

Per `[[feedback_trauma_informed_defensive_scope]]`: any pickup needs explicit user scope direction; not autonomous.

#### Option C — Cross-natural chirality datasets (STALE items 25, 26)

Apply two-tier storage to F135 cross-natural chirality observations (snail handedness, beak laterality, etc.). Needs MPR-attested data per `[[feedback_pdf_extraction_citation_discipline]]`.

### Decision point

- Phase 5 is open-ended; whichever option opens via user direction
- All options validated by Phases 1-4 prerequisite work

---

## §6 Phase 6 — Catalog Landing + SSoT Absorption (~1 session)

**Priority:** LOW-MEDIUM (post-validation)
**Cross-ref:** ROADMAP NEXT-2; R-RBS-NN-4 §8 catalog landing prep; R-RBS-NN-9 pattern

### Goal

Land the R-RBS-NN-10 → R-RBS-NN-14 work into:
- `docs/srmech/srmech_research_notebook.md` §RBS-NN section (per ROADMAP NEXT-2)
- `docs/srmech/catalogs/rbs_nn/` catalog (per R-RBS-NN-9 pattern)
- Literature attestation for any new external citations (per ROADMAP NEXT-3)

### Tasks

| Task | Description |
|---|---|
| T6.1 | Update srmech_research_notebook.md §RBS-NN with R-RBS-NN-10..14 results |
| T6.2 | Populate `catalogs/rbs_nn/` slots opened by R-RBS-NN-10..14 work |
| T6.3 | Update R-RBS-NN-4 literature attestation list with any new refs |
| T6.4 | Cross-reference STALE_PATHS_QUEUE deferrals that should stay deferred |
| T6.5 | ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md final update with operational characterization |

### Output

Multiple catalog files; updated notebook section; updated pattern doc.

### Decision point

Marks formal close of the RBS-NN-V2 arc (R-RBS-NN-10..14 successor to original R-RBS-NN-1..9 arc).

---

## §7 Sequencing summary

```
Phase 1 (foundation)
   ↓
Phase 2 (scale; likely blocker)
   ↓
Phase 3a (multi-step) ─┐
                       │  parallel ok
Phase 3b (hybrid Tier 1)
                       │
Phase 4a (chirality auto-detect) ─┐
                                  │  small; combine
Phase 4b (soft retrieval)
                                  ↓
                           Phase 5 (validation; user scope)
                                  ↓
                           Phase 6 (catalog / SSoT)
```

| Phase | Estimated scope | Priority | Sequence |
|---|---|---|---|
| 1 | ~1 session | HIGHEST | first |
| 2 | ~1-2 sessions | HIGH (likely blocker) | after 1 |
| 3a | ~1 session | MEDIUM | parallel with 3b |
| 3b | ~1 session | MEDIUM | parallel with 3a |
| 4a + 4b | ~1 session combined | MEDIUM | after 3 |
| 5 | ~2-3 sessions per option | MEDIUM-LOW | after 1-4; needs user scope |
| 6 | ~1 session | LOW-MEDIUM | last |

**Total estimated scope:** 6-8 sessions for Phases 1-4; Phase 5 is open-ended; Phase 6 wraps up.

---

## §8 Cross-references with existing planning artifacts

### Existing ROADMAP.md NEXT items

| ROADMAP item | Relationship to this plan |
|---|---|
| NEXT-1 RBS-LM cross-substrate translation | Phase 5 Option A |
| NEXT-2 SSoT absorption | Phase 6 |
| NEXT-3 R-RBS-NN-4 literature attestation | Phase 6 sub-task |
| NEXT-4 Bipolar bundle variant | ✅ LANDED in v0.4.3 (was polar HDC) |
| NEXT-5 Hierarchical bundling for n > 257 | Phase 2 (now formal) |
| NEXT-6 Empty catalog slots | Phase 6 |

### STALE_PATHS_QUEUE deferred items (17 total)

The 17 DEFERRED items in `STALE_PATHS_QUEUE.md` fall into categories that map to this plan:

- Application-direction deferrals (F132 §8 items 1-5) → Phase 5 options
- srmech upstream wishlist (D₄ alternative) → not in this plan; future srmech session
- Real-LLM-scale work (R-RBS-LM-47a) → Phase 5 Option A
- Methodology open (R-RBS-LM-46c, R-RBS-LM-55) → consideration in Phase 3a multi-step work
- Linguistic/biological/cross-natural data → Phase 5 Option B/C

This plan does NOT pull the deferred items into active work; they remain DEFERRED with scope-decision rationale. They become available IF Phase 5 opens that scope.

### `ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md`

This pattern document gets updated in Phase 6 (T6.5) with the empirical characterization from Phases 1-4. The pattern is the reference; this plan is the path to making it robust and production-ready.

---

## §9 Naming convention for follow-up artifacts

All Phase 1-6 work uses the **R-RBS-NN-11 through R-RBS-NN-19** numbering, continuing the original R-RBS-NN-1..9 + R-RBS-NN-10 sequence:

| Number | Phase | Component |
|---|---|---|
| R-RBS-NN-11 | Phase 1 | Capacity characterization |
| R-RBS-NN-12 | Phase 2 | Hierarchical bundling |
| R-RBS-NN-13a | Phase 3.1 | Multi-step retrieval |
| R-RBS-NN-13b | Phase 3.2 | Mixed-precision Tier 1 |
| R-RBS-NN-14a | Phase 4.1 | Chirality-aware input |
| R-RBS-NN-14b | Phase 4.2 | Soft retrieval ranking |
| R-RBS-NN-15 | Phase 5 | Validation at scale (Option-tagged) |
| R-RBS-NN-16 | Phase 6 | Catalog landing + SSoT |

Findings under each get `R-RBS-NN-FINDING_R11.md`, `_R12.md`, etc., matching the pattern.

---

## §10 What this plan does NOT lock in

- Scope decisions for Phase 5 options (B, C subdirections) require user direction
- Phase 6 is conditional on user closing the RBS-NN-V2 arc; may not happen if exploration continues
- New stale items that arise during Phases 1-6 get logged in a fresh STALE_PATHS_QUEUE appendix section (not in the closed master table)
- This plan is REVISABLE — each phase's decision point may pivot the next phase

Per `[[feedback_no_mvp_framing]]`: each phase ships as full coverage of its own concern, not as MVP.

Per `[[feedback_full_coverage_shipping_mpm_way]]`: ships when the empirical work closes, not on artificial sprint deadlines.

---

## §11 First action (when work resumes)

When ready to start Phase 1, the concrete first step is:

```python
# R-RBS-NN-11 capacity characterization smoke
# Sweep N ∈ {10, 25, 50, 100, 200, 256, 512}
# Measure retrieval accuracy per N + synapse count
# Output JSON + finding markdown
```

The R-RBS-NN-10 storage class is the substrate. The capacity sweep extends its `learn_association` + `retrieve_associated` calls to larger lexicons and synapse counts, measuring degradation curve.

---

## §12 Cross-references

- `R-RBS-NN-10_two_tier_storage_REPORT.md` (§7 follow-up paths source)
- `ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md` (reference design)
- `docs/srmech/rbs_nn_research/ROADMAP.md` (existing NEXT items)
- `docs/srmech/rbs_lm_research/STALE_PATHS_QUEUE.md` (17 DEFERRED items)
- F132-F148 framework arc (theoretical foundation)
- R-RBS-NN-1..9 (RBS-NN partition arc; precedes this plan)

---

*Created 2026-05-28 per user direction "assemble us a phased plan to capture these follow
up paths". Organizes R-RBS-NN-10 §7's 6 follow-up paths plus relevant ROADMAP NEXT items
plus appropriate STALE_PATHS deferrals into 6 sequenced phases. Phase 1 is the foundation
(capacity characterization); Phase 2 is the likely blocker (hierarchical bundling); Phases
3-4 are architectural refinements + interface polish; Phase 5 is validation at real scale
(user-scoped); Phase 6 wraps with catalog landing + SSoT absorption. Naming convention:
R-RBS-NN-11 through R-RBS-NN-19 continues the R-RBS-NN sequence. Plan is REVISABLE per
phase decision points; first action is the capacity characterization sweep.*
