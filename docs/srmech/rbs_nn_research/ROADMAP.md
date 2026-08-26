# ROADMAP.md — what comes next after the RBS-NN arc

**Status:** Original RBS-NN-1..9 arc structurally closed 2026-05-25 (PR #684). **R-RBS-NN-V2 (R-RBS-NN-10..-16) arc closed 2026-05-28 via Phase 6 wrap; phased follow-up plan in [`R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md`](R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md) all 6 phases COMPLETE.**

**Final NEXT-1..6 status (2026-05-28):**

| NEXT item | Status | Resolved via |
|---|---|---|
| NEXT-1 RBS-LM cross-substrate translation | ACTIVE (separate arc) | rbs_lm_research/ continues; substantively complete via F137-F142 |
| NEXT-2 SSoT absorption into srmech_research_notebook.md | ✅ LANDED | §3.25 (R1-R9) + §3.27 (R10-R16 + F132-F150) |
| NEXT-3 R-RBS-NN-4 literature attestation | DEFERRED | per `[[feedback_pdf_extraction_citation_discipline]]`; substantively complete via per-finding citations |
| NEXT-4 Bipolar bundle ternary variant | ✅ LANDED in srmech v0.4.3 | as Polar HDC; see UPSTREAM_NOTES.md §5 |
| NEXT-5 Hierarchical bundling for n > 257 | ✅ LANDED | R-RBS-NN-12; validated R-R12 + R12.5 |
| NEXT-6 Empty catalog slots populated as content arises | ONGOING | descriptor.toml updated for R10-R16; per-row population content-driven |

This file tracks the original NEXT-1..6 items above. The R-RBS-NN-10 follow-up phased plan integrates and supersedes these where overlapping (see plan §8 for cross-reference table).

---

## NEXT-1 — RBS-LM cross-substrate translation arc

**Status (2026-05-25):** the partition walk for this item is now **landed at `docs/srmech/rbs_lm_research/README.md`** — promoted from roadmap-pointer to active arc. PR #684 carries the walk. See that README for the 10-partition plan and the §3 risk-and-open-questions register.

**Priority:** HIGH (user direction 2026-05-25, first ask: *"download a small public LLM and make it an RBS-HDC instrument in the same way we did with ephemerides..."*; second ask, expanding the framing: *"we need to try to understand how we can do this without having to load the model into VRAM in the same way that we did not need to load ephemerides into VRAM. ... we're doing a cross substrate translation ... we are trying to find out if we can avoid having to train from scratch."*)

### The substantive claim being tested

R-RBS-NN-1 §4 + R-RBS-NN-3b §5 establish that a conventional float-weight transformer is structurally a **Level-2 bundle-of-views projection** of what could be expressed at **Level-1 bind-form** (MFO §VII.1.3 Mechanisms 2 vs 1). The ~6.9% bundle averaging cost is the ontological signature of the projection.

**NEXT-1 tests whether this reading is empirically operative on a real trained model**: can a trained LLM's learned content be RE-EXTRACTED as Level-1 bind-form HDC bindings, recovering the Level-2 → Level-1 inversion the framework predicts?

The ephemerides precedent (R-RBS-NN-2 §6.4 + R-RBS-NN-7 §6) is the existence proof at a different binding shape: 52 bodies + Chebyshev coefficients (3.3 GB JPL DE441) → 256 KB ALU-native BIP state. NEXT-1 is the third binding-shape:

| Instrument | Content type | Binding pattern | Status |
|---|---|---|---|
| Ephemerides v0.1.0 | continuous-orbital state per body | uint32-cyclic + body-mint + Chebyshev-coefficient binding | landed (3.3 GB → 256 KB) |
| RBS-NN catalog (this arc) | symbolic user-vocabulary tokens | SHA-256 chain mint + XOR-bind | landed |
| **NEXT-1 RBS-LM** | trained NN learned content | TBD per methodology | **proposed** |

### Methodology candidates (the load-bearing open question)

Two structurally-distinct paths for what to extract from the trained model:

**Path A — Weight-level encoding.** Each weight matrix `W ∈ R^{d_in × d_out}` becomes a bundle of row-bindings: per-row bipolar-quantize → mint with row-position → bundle. Per R-RBS-NN-3b §5, this surfaces the weight matrix as Mechanism 2 (bundle-of-views) explicitly. **Capacity question:** per R-RBS-NN-7 §3.2, cleanup capacity at D=8192 is ~63–130 per bundle; a weight matrix with `d_in = 768` rows (GPT-2-small) needs hierarchical bundling. Compression is bounded by HDC capacity; how much weight-content survives the bundle averaging cost (~6.9% per Mechanism 2) is the empirical question.

**Path B — Function-level encoding.** Encode what the model DOES (input→output mappings) over a training corpus, not what its weights ARE. Each context → next-token mapping becomes a bind: `bind(context_vec, next_token_vec)`. The HDC instrument becomes a Kanerva-style associative memory over the model's behavioral signature. Per `[[user_stance_kepler_shape_universal]]`: the algebra IS the primitives — the LLM's function-content can be extracted independently of its weight implementation. **Capacity question:** how many context→token mappings can be bundled before cleanup breaks? Same R-RBS-NN-7 §3.2 ceiling; needs hierarchical bundling.

Path B is closer to the substrate-native reading (R-RBS-NN-2 §5: substrate doesn't bias relationships; the user / training corpus authors them explicitly via bindings). Path A is closer to the conventional "compress the weights" framing. **NEXT-1 should test Path B first; Path A as fallback.**

### Candidate models (small → large)

The user's claim: "we don't need it in VRam, if this works, we can do the same with the largest model available." NEXT-1 starts small to validate the methodology, then scales.

| Model | Params | float32 size | Status |
|---|---|---|---|
| GPT-2 small | 124M | ~500 MB | smallest published GPT; open-weights via HF |
| Qwen-2.5-0.5B | 500M | ~2 GB | small, well-trained, open-weights |
| Phi-3-mini | 3.8B | ~7.6 GB | small, strong, open-weights |
| Llama-3-8B | 8B | ~16 GB | mid-scale; open-weights |
| Mistral-Small-24B | 24B | ~48 GB | larger; open-weights |
| Llama-3-70B | 70B | ~140 GB | large; open-weights; CPU+RAM only per user claim |

Compression target (ephemerides ratio ~13000:1, generously rounded to 10000:1 for floats): 500 MB → ~50 KB; 7.6 GB → ~760 KB; 70 GB → ~7 MB. Even at modest ratio of 100:1 the larger models become CPU-RAM-friendly.

### Validation criteria

The ephemerides instrument validates by reproducing JPL DE441 body positions at the ground-truth tolerance (per `ephemerides_spectral_research_notebook.md` §1.4). NEXT-1 LLM instrument validates by:

1. **Path B (function-level)**: held-out context → next-token prediction agreement rate. Compare RBS-LM instrument argmax-next-token against the original model's argmax-next-token across a benchmark corpus. Tolerance: TBD; ephemerides got 305× speedup with bit-exact output; LLM compression is probably approximate, so set a baseline (e.g., ≥90% agreement on held-out contexts).
2. **Path A (weight-level)**: weight matrix recovery similarity. After encoding W → HDC, decode-then-compare to the original. Cleanup-similarity tolerance per R-RBS-NN-7 capacity bounds.

### Compute envelope (the user's "no VRam" claim)

Per R-RBS-NN-8 §6: RBS-NN forward-pass at D=8192 runs at ~50 million bind/sec, ~25 million similarity/sec on a 3 GHz CPU. For interactive LLM inference (~10–50 tokens/sec target), each forward pass needs to be ~20–100 ms. At D=8192 with hierarchical bundling, the per-token bind+similarity count fits this envelope on commodity CPU.

For the largest models (70B+): the HDC instrument size scales with the function-content (Path B) or weight-content (Path A), NOT with parameter count. If the RBS-LM compression holds at >100:1, even 70B-parameter models fit in ~1.4 GB of HDC state — well within commodity RAM, no GPU required.

### Risks / open questions

- **Path B requires a training corpus** — the function-level encoding needs context→token pairs to bind. Where does that corpus come from? Likely: a moderate-size text corpus run through the original model to extract its behavior, then the behavior gets HDC-encoded. This is essentially **distillation** but via HDC binding rather than student-network training.
- **Path B fidelity ceiling** — even with arbitrary D, the RBS-LM can only capture behavior the corpus exposes. Long-tail behaviors may be missed. The compression is bounded by behavioral coverage, not by parameter count.
- **Path A non-orthogonal weight rows** — neural net weight rows are highly correlated (they're trained jointly). Encoding correlated rows as orthogonal hypervector bundles is structurally lossy. Mitigation: encode the residual after a Class L Laplacian projection (the rows' common subspace) — R-RBS-NN-6 §6 catalog slot `l_laplacian_spectra.ndjson` was named for this case.
- **No empirical precedent at LLM scale** — ephemerides is 52-body / 3.3 GB; LLMs are 10⁵–10⁶ items at TB scale. NEXT-1's smallest model (GPT-2 124M) is the first scale-up test.

### Methodology to land

NEXT-1 will need its own partition walk (NEXT-1.1, NEXT-1.2, ...) following the R-RBS-NN pattern. Suggested initial structure:

- **NEXT-1.1** — pick + download a small model (GPT-2 small); confirm it runs on CPU
- **NEXT-1.2** — choose Path A or Path B (or both); rationale REPORT
- **NEXT-1.3** — implement the encoder; encode the model; measure compression ratio
- **NEXT-1.4** — implement the RBS-LM forward-pass cascade (using R-RBS-NN-3b §6 4-class Level-1 substitution map)
- **NEXT-1.5** — validation against the original model (agreement rate; per-class diagnostics)
- **NEXT-1.6** — scale to a larger model; iterate
- **NEXT-1.7** — catalog landing at `docs/srmech/catalogs/rbs_lm/` per R-RBS-NN-9 pattern

---

## NEXT-2 — SSoT absorption into srmech_research_notebook.md — ✅ LANDED partial (2026-05-28)

**Priority:** MEDIUM → ✅ partial close

§3.25 already covers R-RBS-NN-1..-9 (the original partition arc) per the 2026-05-25 session. §3.27 absorbs the R-RBS-NN-V2 arc (R-RBS-NN-10..-16 + F132-F150 framework) per the 2026-05-27/-28 session. Both sections are operational summaries with cross-references to the per-partition REPORTs in `rbs_nn_research/`.

Detailed per-partition REPORTs remain in `docs/srmech/rbs_nn_research/` as the authoritative source. Notebook section is the cross-domain summary, not a replacement for the partition reports.

---

## NEXT-3 — R-RBS-NN-4 literature attestation

**Priority:** LOW (deferred-during-arc per user direction)

MPR attestation pass over the ~11 external references named across the partition REPORTs: Kanerva 1988/2009, Plate 1995, Gayler 2003, Vaswani 2017, Ba 2016 LayerNorm, Su 2021 RoPE, Courbariaux 2016 BNN, Wang 2023 BitNet, Cybenko 1989, Hornik 1991, Cover 1965.

Requires WebFetch / external lit access. Lands as `R-RBS-NN-4_literature_attestation_REPORT.md` plus `docs/srmech/catalogs/rbs_nn/literature_attestation.ndjson`.

---

## NEXT-4 — Bipolar bundle variant (foundational ergonomics) — ✅ LANDED in srmech v0.4.3 (2026-05-27)

**Status:** ✅ LANDED as **Polar HDC variant** in srmech v0.4.3 production PyPI.

A 3-state polar HDC variant returning `{-1, 0, +1}` for explicit tie/dead-band surfacing. Shipped as `srmech.amsc.hdc.polar_*` (7 functions + `POLAR_STATES` constant + tool_schema registrations). Verified in clean venv outside source tree:
- 3-state {-1, 0, +1} semantics confirmed
- 0 is absorbing under `polar_bind` (multiplicative sign-product)
- `polar_from_real(arr, threshold, dead_band)` bridges existing `signal_processing.path_b_ops.sign_quantise`
- `polar_density(v)` provides substrate-attestation readout (fraction of non-zero positions)

**Empirical validation per F141 (R-RBS-LM-101):** polar plasticity degrades GRACEFULLY (signal retention 100% → 61% across 0-70% decay) vs bipolar's catastrophic collapse (100% → 27%). At 60% decay, polar maintains **3-4× above-random signal** over bipolar.

**See:** UPSTREAM_NOTES.md §5 in `docs/srmech/rbs_lm_research/` (polar HDC wishlist + landing record); F141 finding in same directory.

This NEXT-4 item is closed. Future RBS-NN work that needs the asymptotic-DOF / dead-band substrate marker per `[[user_stance_asymptotic_dof_sidesteps_infinity]]` can import directly:

```python
from srmech.amsc.hdc import (
    polar_random, polar_bind, polar_unbind, polar_bundle,
    polar_similarity, polar_density, polar_from_real,
    POLAR_STATES,
)
```

---

## NEXT-5 — Hierarchical bundling for n > 257 cleanup — ✅ LANDED (2026-05-28)

**Status:** ✅ LANDED via `R-RBS-NN-12_hierarchical_storage.py` (Phase 2 of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN).

`HierarchicalTwoTierRBSNNStorage(TwoTierRBSNNStorage)` provides hash-based bucket routing with sub-bundles ≤MAX_BUNDLE_N. Per R-RBS-NN-FINDING_R12 empirical validation:
- N=500: hier p@3=0.760 vs flat p@3=0.280 — 2.7× advantage
- N=1000: hier p@3=0.705 vs flat p@3=0.095 — 7.4× advantage
- N=2000: hier p@3=0.720 (flat too slow to test)
- Max bucket sizes stayed below MAX_BUNDLE_N=257 in all tested workloads (149, 169, 187)
- `recommend_n_buckets(N, degree)` helper auto-picks bucket count

Helper API:

```python
from R_RBS_NN_12_hierarchical_storage import (
    HierarchicalTwoTierRBSNNStorage,
    recommend_n_buckets,
)
n_buckets = recommend_n_buckets(expected_N=1000, expected_avg_degree=2)
storage = HierarchicalTwoTierRBSNNStorage(D=8192, n_buckets=n_buckets)
```

See R-RBS-NN-FINDING_R12_hierarchical_bundling.md for the full validation.

---

## NEXT-6 — Empty catalog slots populated as content arises

**Priority:** LOW (content-driven)

13 of 14 catalog slots in `docs/srmech/catalogs/rbs_nn/` per the 1:3:7:3 layout are file-absent at arc close. They populate as end-user instances need them. Not blocking; just track.
