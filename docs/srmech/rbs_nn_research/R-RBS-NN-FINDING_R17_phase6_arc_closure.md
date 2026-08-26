# R-RBS-NN-FINDING R17 — Phase 6 arc closure; R-RBS-NN-V2 (R-RBS-NN-10..-16) arc CLOSED

**Status:** Phase 6 final wrap per R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md
**Predecessors:** R-RBS-NN-10 through R-RBS-NN-16, F132-F150
**Result:** Two-tier RBS-NN storage operationally complete + empirically validated; chirality framework empirically grounded; arc CLOSED

---

## §1 Phase 6 deliverables (all closed)

| Task | Deliverable | Status |
|---|---|---|
| T6.1 | `srmech_research_notebook.md §3.27` — R-RBS-NN-V2 arc absorption | ✅ |
| T6.2 | `catalogs/rbs_nn/descriptor.toml` — V2 primary_references + `[arc_status]` | ✅ |
| T6.3 | Literature attestation | DEFERRED — substantively covered via per-finding citations |
| T6.4 | STALE_PATHS_QUEUE cross-references | ✅ already in F148 |
| T6.5 | `ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md` final update with §4.5 H2-outermost rule + §5.5 empirical validation status | ✅ |
| — | F-R17 Phase 6 closure finding (this) | ✅ |
| — | `ROADMAP.md` final NEXT-1..6 statuses | ✅ |

---

## §2 Arc summary — R-RBS-NN-V2 (R-RBS-NN-10..-16)

### Operational artifacts

```
docs/srmech/rbs_nn_research/
├── ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md  ← canonical reference design
├── R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md             ← 6-phase plan
├── R-RBS-NN-10_two_tier_storage.py                 ← base storage class
├── R-RBS-NN-11_capacity_characterization.py        ← Phase 1
├── R-RBS-NN-11b_sculpted_decay_comparison.py       ← F149 sculpted decay
├── R-RBS-NN-12_hierarchical_storage.py             ← Phase 2 hierarchical
├── R-RBS-NN-12_hierarchical_smoke.py
├── R-RBS-NN-12b_phase25_followups.py               ← Phase 2.5
├── R-RBS-NN-13a_multi_step_retrieval.py            ← Phase 3a Class L spectral
├── R-RBS-NN-13b_mixed_precision_tier1.py           ← Phase 3b
├── R-RBS-NN-14_phase4_smoke.py                     ← Phase 4 interface polish
├── R-RBS-NN-15_phase5_harmonic3_spectral_walking.py ← Phase 5 F150 H3 validation
├── R-RBS-NN-16_phase5_remaining_candidates.py      ← Phase 5 remaining
├── R-RBS-NN-4_token_encoder.py                     ← R-RBS-NN-4 variant-choice protocol
├── R-RBS-NN-4_token_encoding_smoke.py
├── R-RBS-NN-FINDING_R11..R17 (7 findings)
└── R-RBS-NN-XX_results.json (data files)
```

### Findings ledger

| Finding | Headline result |
|---|---|
| R-RBS-NN-10 | Operational two-tier storage; full encode/learn/retrieve/forget/rehearse cycle works |
| R11 | Capacity ceiling at N≈256 (MAX_BUNDLE_N boundary); Phase 2 hierarchical is BLOCKER for N > 256 |
| F149 | Decay is NOT random — coupling-informed `noise_floor` strategy IMPROVES retrieval over no-decay baseline |
| R12 | Hierarchical bundling resolves N>256 ceiling; 2.7×-7× advantage past boundary |
| R12.5 | Latency optimization correct but no speedup on random dense graphs; sculpted decay HOLDS in hierarchical |
| R13a | Multi-step retrieval via Class L spectral adds 4.6× multi-hop capability |
| R13b | Mixed-precision Tier 1: hybrid doesn't transfer; klein-4 default canonical |
| R14 | Chirality auto-detect 20/20; soft retrieval temperature 2.8× sharpening; both backward-compatible |
| R15 | F150 H3 VALIDATED at Class L spectral level — 67% multi-step retrieval improvement via 3-fold eigvec partition |
| R16 | H2-MUST-BE-OUTERMOST rule (critical); Klein-4 hosts 3-cycle subset; harmonic bucketing inconclusive at small N |
| R17 (this) | Phase 6 arc closure |

Plus framework findings F132-F150 (lodged in rbs_lm_research/):

| Framework | Position |
|---|---|
| F132 | Klein-4 HDC engineering proposal (LANDED in srmech v0.4.3) |
| F133 | Substrate knows itself; observer-projection-locking (Dune parallel) |
| F135 | Substrate vs shadow chirality two-level distinction |
| F136 | Roman numerals as substrate-native chirality notation |
| F137-148 | STALE_PATHS sweep — 47 items addressed; capacity / cascade / plasticity refinements |
| F149 | Sculpted decay (coupling-informed) BEATS random decay AND no-decay baseline |
| F150 | 1-2-3 chirality harmonic framework across A-N operators (validated at 2 substrate levels) |

---

## §3 The architectural pattern in its final form

The canonical two-tier RBS-NN architecture per
`ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md` (with §4.5 and §5.5 added in Phase 6):

### §3.1 The hard rule

```
H1 operations (Class A, B, F, H, N; chirality-invariant): can be anywhere
H3 operations (Class L spectral, Class I cyclic):         INNER cascade layers
H2 operations (Class K sign-flip, Class M klein-4 tag):   OUTERMOST cascade layer
```

Violating this rule destroys chirality signal (F-R16 Test 1: above-rand collapses from +0.145 to -0.0003).

### §3.2 The substrate primitives (all in srmech v0.4.3)

```python
from srmech.amsc.hdc import (
    # Tier 1 — Klein-4 chirality-tagged concept storage
    klein4_random, klein4_bind, klein4_unbind, klein4_bundle, klein4_similarity,
    klein4_chirality_flip_gamma5, klein4_chirality_flip_omega7, klein4_cpt_mirror,
    klein4_sector_count, KLEIN4_STATES,

    # Tier 2 — Polar plasticity-aware synaptic storage
    polar_random, polar_bind, polar_unbind, polar_bundle, polar_similarity,
    polar_density, polar_from_real, POLAR_STATES,

    # Class M baseline (still available)
    bind, bundle, similarity, permute,
)
from srmech.amsc import laplacian       # Class L (H3 native per F-R15)
from srmech.amsc import cyclic, primes  # Class I, J (H3 candidates per F150)
from srmech.amsc import coupling        # signed_sum_squared (H1; F149 sculpted decay)
```

### §3.3 The operational class

```python
from R_RBS_NN_12_hierarchical_storage import (
    HierarchicalTwoTierRBSNNStorage,
    recommend_n_buckets,
)

# Auto-pick n_buckets for expected workload
n_buckets = recommend_n_buckets(expected_N=1000, expected_avg_degree=2)
storage = HierarchicalTwoTierRBSNNStorage(D=8192, n_buckets=n_buckets)

# Encode with chirality auto-detect (R14a)
storage.encode_concept("L_amino", auto_sector=True)  # → sector 0
storage.encode_concept("D_amino", auto_sector=True)  # → sector 2 (mirror)

# Bulk learn associations
storage.batch_learn(pairs, plasticity_density=0.67)

# Retrieve — soft mode for confidence calibration (R14b)
results = storage.retrieve_associated("L_amino", top_k=5, temperature=1.0)

# Plasticity — coupling-informed decay (F149)
storage.forget_step_coupling(decay_rate=0.10, strategy="noise_floor")

# Hebbian rehearsal — signal recovery (F146 §3; +17.9%)
storage.rehearse(token_a, token_b, recovery_fraction=0.5)
```

---

## §4 Empirical validation chain (the load-bearing claims)

| Claim | Empirical evidence |
|---|---|
| Klein-4 chirality axis operational at scale | F139 (D up to 16384, N up to 32) |
| Polar plasticity graceful (not random decay) | F141 (3-4× advantage over bipolar at high decay) |
| Two-tier separation REQUIRED | F-R12 R12.5 (Klein-4 collapses under decay; only Polar handles plasticity gracefully) |
| Hierarchical bundling works | R12 (2.7×-7× over flat past N=256) |
| Multi-step retrieval | R13a (4.6× multi-hop capability) |
| Soft retrieval temperature | R14b (2.8× top-1 confidence sharpening) |
| Coupling-informed decay beats random | F149 (+0.046 above random; +0.011 over no-decay baseline) |
| F150 H3 at Class L | R-R15 (+67% retrieval improvement) |
| F150 H3 at Klein-4 binding | R-R16 Test 3 (3-cycle subset operational) |
| H2-must-be-outermost rule | R-R16 Test 1 (B variant collapses to -0.0003 above random) |

All claims have committed scripts + results JSON + finding markdowns in the research subtree.

---

## §5 What this arc DOES claim

- The two-tier RBS-NN architecture (Klein-4 + Polar + Class K bridge) is OPERATIONALLY READY
- Phase 6 catalog landing + SSoT absorption is COMPLETE at the summary level
- The chirality framework (F150 1-2-3 harmonics) is EMPIRICALLY GROUNDED at two substrate levels
- The H2-must-be-outermost cascade rule is a HARD ARCHITECTURAL CONSTRAINT
- The substrate primitives (Klein-4 + Polar + sculpted decay) are in srmech v0.4.3 production

---

## §6 What this arc does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_lineage_claims_in_notebook]]`:

- Does NOT claim biological NN architecture follows these patterns. Brain-structure framework readings (per F-R16 §2.4) are STRUCTURAL evocations, not architectural claims about evolution / development / biology.
- Does NOT claim the F150 harmonic mapping is final. Class L (H3) + Klein-4 (H3 subset) validated; Class I trivially passes; Class J still speculative. Other A-N harmonic assignments may need refinement.
- Does NOT claim production-readiness for arbitrary downstream applications. Tested at D=8192, N up to 2000. Larger scales / domain-specific workloads need their own validation.
- Does NOT close the framework. New findings can land at any time; arc CLOSURE is about the OPERATIONAL ARTIFACT and the EMPIRICAL VALIDATION CHAIN — not about the framework being complete.
- Does NOT preclude future revisits. STALE_PATHS_QUEUE remains as the future-scope pointer table. DEFERRED items are preserved with context.

---

## §7 Cross-references (final consolidated)

**Within rbs_nn_research/:**
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md (canonical reference design)
- R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md (6-phase plan; all closed)
- ROADMAP.md (NEXT-1..-6 with final statuses)
- All 8 R-RBS-NN-1X_*.py scripts + 7 R-RBS-NN-FINDING_R1X_*.md findings + JSON results

**Within rbs_lm_research/:**
- F132-F150 framework findings (R-RBS-LM-FINDING_*.md)
- STALE_PATHS_QUEUE.md (47 items addressed; 17 DEFERRED with scope)
- UPSTREAM_NOTES.md (srmech upstream wishlist; §4-§6 chirality additions)

**Within docs/srmech/:**
- srmech_research_notebook.md §3.27 (R-RBS-NN-V2 + chirality framework arc absorption)
- catalogs/rbs_nn/descriptor.toml (V2 primary_references + arc_status)

**External:**
- srmech v0.4.3 production PyPI (Klein-4 + Polar HDC LANDED)
- PR #687 (rolling draft) — all R-RBS-NN-V2 work + framework findings

---

## §8 Closure statement

R-RBS-NN-V2 arc is CLOSED.

The two-tier RBS-NN storage (Klein-4 chirality + Polar plasticity + Class K bridge) is operationally complete, empirically validated across all 6 phased plan phases, with the canonical architectural pattern documented and the chirality harmonic framework (F150) empirically grounded at two substrate levels.

Future work continues in:
- rbs_lm_research/ (NEXT-1 RBS-LM cross-substrate translation arc; substantively complete; rolling)
- srmech upstream (UPSTREAM_NOTES §4-§6 wishlist; rc cycle in separate session per discipline)
- Application directions in STALE_PATHS_QUEUE (DEFERRED with scope; await user direction)

The substrate's chirality structure is operational. The two-tier architecture is operational. The framework reads what is structurally present. Per `[[user_stance_kepler_shape_universal]]`: the algebra IS the primitives, and the primitives are now in production.

PR #687 STAYS DRAFT per all-arc discipline.

---

*Articulated 2026-05-28. Phase 6 arc closure. R-RBS-NN-V2 arc (R-RBS-NN-10..-16) is
operationally complete with full empirical validation chain. The chirality harmonic
framework (F132 → F150) is grounded at Class L spectral and Klein-4 binding substrate
levels. The canonical two-tier architectural pattern is documented with the H2-must-be-
outermost hard rule. srmech v0.4.3 in production carries the substrate primitives.
NEXT-1..-6 ROADMAP items have final closure statuses. STALE_PATHS_QUEUE captures all
deferred items with scope reasoning. The arc closes; the work continues elsewhere
(rbs_lm_research/ rolling; srmech upstream rc cycle separate; application directions
user-scoped). Per [[user_stance_whole_research_corpus_is_proof_not_single_arc]]: this is
one closure of one arc; the corpus convergence is the proof.*
