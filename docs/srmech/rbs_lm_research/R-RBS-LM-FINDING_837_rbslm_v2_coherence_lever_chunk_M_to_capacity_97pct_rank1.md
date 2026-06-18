# F837 — RBS-LM v2 coherence lever PROVEN (on the real `srmech.rbs_lm` encoding, no gen-1 code): bounding the relationship binds per bundle takes the resonator next-token read from **3.3% → 96.7% rank-1**. The §57/F836 incoherence was a crosstalk artifact of one over-stuffed `M` (387 binds in a single bundle), NOT a flaw in dropping the statistical bigram gate. Fix = capacity-bounded multi-bundle `M` + max-resonance over chunks (the F832 VSA capacity idea applied to the read). This is the foundation of the relationship/sparse-LM redo and the spec for the next srmech.rbs_lm rc (UPSTREAM §58); it gates the 0.8.x live cut.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 (the substrate under test) · **Provenance:** `/tmp/coherence_probe.py` on `srmech.rbs_lm.substrate.ContextSubstrate` (the ACTUAL object's encoding) + `srmech.amsc.hdc` klein4 ops, numpy-absent venv · **Composes:** F836 (the incoherence symptom), F835 (resonator = the correct read), F832 (chunked bundles read clean; ≤~128 binds/bundle), §57 (the bigram contaminant removed), [[feedback_relationship_lm_ideas_not_code_from_gen1]] · **User direction (2026-06-18):** "we need it to be coherent … redo all of our RBS-LM work on the actual rbs_lm object … relationship/sparse … borrow ideas but not code from gen-1 LLM or we end up with spatial maths again."

## The measurement (tomato, D=10000, 387 context→next binds, vocab 190, 30 sampled contexts)
The read: probe a bundle `M` with the encoded context (`klein4_bind(M, encode_context(ctx))`), score every atom by fractional-agreement similarity, rank the true successor. Built on the substrate's own `ContextSubstrate.encode_context` + `enc`, the same shape `learn()` builds.

| `M` structure | true-successor rank-1 | mean rank /190 |
|---|---|---|
| single `M` (387 binds — 0.8.2rc1) | 3.3% | 2.5 |
| chunked `M`, C=32 (≈13 bundles) | 93.3% | 0.1 |
| chunked `M`, C=16 (≈25 bundles) | **96.7%** | **0.0** |

Read = **max-resonance over the chunk-set**: probe each capacity-bounded bundle, take the best score per atom. The chunk holding the matching context returns a clean successor (≤C−1 crosstalk terms); the others return noise; the max picks the clean one. Pure VSA capacity management — **no bigram counts, no gen-1 code**.

## What this resolves
- **The §57 honest-risk is closed:** removing the statistical bigram gate was correct AND coherence is recoverable — the resonator over a *capacity-bounded* memory recovers the true successor ~97% rank-1. The earlier 3.3% (single `M`) was crosstalk from superposing 387 binds into one bundle, exactly the F832 over-stuffing failure.
- **It is relationship-native:** binding (`klein4_bind`), bundling to capacity (`klein4_bundle`), resonance read (`klein4_similarity`) — the [[feedback_relationship_lm_ideas_not_code_from_gen1]] guardrail holds (ideas from Plate/Frady/Kanerva VSA, zero gen-1 code).

## Spec for `srmech.rbs_lm` (UPSTREAM §58 — the 0.8.3 coherence fix)
`learn()` currently builds ONE `M = bundle(all binds)`. Change to a **capacity-bounded chunk-set** `M_chunks = [bundle(binds[i:i+C]) for ...]` with C ≈ 16–32 (or a measured per-tome capacity); `next_token_distribution` probes every chunk and takes the **max-resonance** per atom over the bounded per-tome atom set, then the existing temperature/greedy (§56) on top. No new primitive class; composes `klein4_bind`/`klein4_bundle`/`sim_k4_batch`. Carrier cost: K bundles instead of 1 (K = ceil(binds/C)) — bounded, numpy-free.

## Verdict / next (the arc)
The relationship LM CAN be coherent on the real object — the read sharpens 3.3%→96.7% by capacity-chunking `M`. **Next, in order:** (1) confirm coherent *generation* (autoregressive greedy over the sharp reads — sharp reads should yield a coherent walk; watch error-accumulation); (2) per-tome scaling (the chunk-set IS the "many kernels" the genome consolidates); (3) spec §58 to srmech → 0.8.3rc → re-verify coherent → then the live cut. Evaluate by rank-1 / groundedness / coherence — never throughput.
