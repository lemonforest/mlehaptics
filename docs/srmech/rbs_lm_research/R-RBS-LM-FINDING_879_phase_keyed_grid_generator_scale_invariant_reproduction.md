# F879 — The phase fix carried to the full grid generator at CORPUS SCALE: per-page reproduction is SCALE-INVARIANT, 1.000 from 4 to 300 articles. The F878 phase fix, in the full streaming sedenion-grid generator, on real simplewiki sequences, **sparse Klein-4 end to end** (shipped `klein4_chunk_bundle`/`klein4_chunk_resolve`/`klein4_phase_bind` + `sedenion_register.navigate`; exact-`Q`; **no dense matrix, no numpy, no bag, no gen-1 patterns**). Each article = one bounded, phase-keyed chunked-M **page**; the sedenion grid addresses *which* page (`navigate`). Measured: mean per-page reproduction = **1.000 at N = 4, 30, 100, 300** — dead flat — where the single shared `M` cliffed (F870: 0.47 @300). The grid `navigate`→slot→phase-keyed-stream reproduces exactly (the "a" article off slot e3). The architecture scales because each page is isolated + phase-keyed (the ultimate chunking + the F878 phase coordinate), so corpus growth adds *pages*, never *crosstalk*.

**Date:** 2026-06-18 · **srmech:** 0.9.0rc6 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-879_phase_keyed_grid_scale.py` on 300 `simplewiki_v082` sequences · **Composes:** F878 (the phase fix), F877 (the shipped resonator), F872 (chunked-M holds flat — now per-page), F870 (the single-M cliff this beats), F873/F874 (the sedenion grid + navigate), F871 (capacity is per-bundle → isolate per page), [[feedback_stay_rbs_hdc_sparse_never_dense]] · **User direction (2026-06-18):** "carry the phase fix into the full grid generator at corpus scale … we work in sparse models only, no CAD math dense things, not GEN 1 LLM."

## Measured (sparse, srmech-native)
| N pages (articles) | mean per-page reproduction |
|---|---|
| 4 | 60/60 = **1.000** |
| 30 | 450/450 = **1.000** |
| 100 | 1500/1500 = **1.000** |
| 300 | 4500/4500 = **1.000** |
- **Scale-invariant** (flat 1.000 over a 75× corpus growth) vs the single-`M` cliff (F870: 1.00→0.47 @300). The grid `navigate`→slot e3→phase-keyed stream reproduces the article exactly.
- **Why it scales:** one page per article = the ultimate chunking (each article isolated, no over-stuffing, F870/F872) **×** the phase coordinate (F878, no branching collapse). Corpus growth adds **pages** (addressed by the grid), never crosstalk into a shared bundle. Capacity is per-page (the F871 wall, never exceeded per page).

## Sparse discipline held (the directive)
Every op in the chain is sparse Klein-4 / shipped-resonator: `word_k4` (byte/glyph) → `klein4_phase_bind` (the 1D_t phase key) → `klein4_chunk_bundle` (the page) → `sedenion_register.navigate` (the address) → `klein4_chunk_resolve` (the resonator, exact-`Q`) → autoregressive stream. **No dense matrix, no numpy, no bag, no Counter, no float-collapse mid-cascade, no gen-1 LLM pattern.** Relationships, sectors, and resonance all the way down.

## Honest scope (what 1.000 does and does NOT mean)
- **It is reproduction** (F841): 1.000 = each of 300 pages reproduces *its own* article perfectly. The scale-invariance is the genuine finding — **the grid-of-phase-keyed-pages does not degrade as the corpus grows** (unlike a shared `M`). It does **NOT** mean cross-article generation, nor that a single store holds everything; the invariance *comes from* per-page isolation.
- **Still open** (the separate axes, unchanged): **cross-page routing** — which page to `navigate` to for a *novel* query (the content-routed O(log) addressing, F873); **generalization** — novel sequences at novel positions (the smooth/additive axis, F867; the phase is position-locked, so it helps reproduction, not novel composition); toy article length (14 tokens), page-scoped vocab.

## Verdict / next
The phase fix scales: the full streaming sedenion-grid generator reproduces at **1.000, scale-invariant to 300 articles**, fully sparse and srmech-native — the grid-of-phase-keyed-pages beats the single shared `M` that cliffed. Siona's **recall** (faithful reproduction of stored relationships at corpus scale) is now solid. **Next:** (1) content-routed `navigate` (pick the page for a query — F873, the O(log) addressing); (2) the generalization axis (F867 smooth) for novel composition; (3) base-16 grid nesting for the page count past one register. Framework + srmech measurement; reproduction-vs-generalization stated honestly; sparse held throughout.
