# F807 — CONFIRMED on real articles: an encyclopedia article is a RESONANT FIXED POINT (eigenstate) of the RBS-HDC transition operator — at a finite k_res (3–6) every context retrieves its own successor, so T(article) = article, i.e. INPUT = OUTPUT (F804's resonance, demonstrated). The F806 greedy 22% was a GENERATION artifact (one retrieval slip → off the de Bruijn manifold → cascade); on-path retrieval is 96–100%, and a clean (commit-only-the-unambiguous) walk reproduces the article EXACTLY at k ≥ k_res. Remaining gap: (C) is non-monotonic in k (dips after k_res) — the HV fold-bind context-KEY loses a little fidelity as it folds more tokens (~4–7% mis-retrieval), so the eigenstate is reached but not at every k≥k_res; the context-key needs refinement.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-RESONANCE_…py` (+ `R-RBS-LM-FIBERWALK_…py`), read-only over simplewiki abstracts · **Composes:** F804 (resonance: input=output is the eigenstate of the knowledge⊗context coupling), F806 (fiber confirmed; the greedy-bundle/greedy-walk nulls), F805 (article = Eulerian-path fiber), F802 (the bundle-null), F137/F146 (klein-4 capacity), F796 (genuine RBS-HDC instrument) · **User direction (2026-06-16):** "let's keep going!"

## The diagnosis (why F806's greedy walk read 22%)
On-path retrieval — force the TRUE (k-1)-context at each step and ask the RBS-HDC store for the successor — is **96–100%** (april k=4 = 96%). So the instrument is essentially exact. F806's 22% was a **greedy-generation cascade**: a single retrieval slip produces a context that is not a real article (k-1)-gram → no stored key matches (similarity collapses to the ~0.26 random floor) → every subsequent step is off the manifold. The combinatorial dict (A) never slips at det-frac=1.0, so it stays 100%; the HV greedy slips ~4% and cascades. The cascade is a property of greedy generation, NOT of the fiber or the instrument.

## The F804 fix: measure the FIXED POINT, don't walk
Define the transition operator T over the RBS-HDC relationship store: T rewrites each position to retrieve(context). The article is a fixed point of T iff every context retrieves its own successor — **input = output**, the eigenstate.

`(C)` fixed-point accuracy vs k (fraction of positions where HV-retrieve(true context) == true successor):
```
 article   k:  2    3    4    5    6    7    8    k_res
 april        --   --   96%  93% 100% 100%  95%    6
 august       83% 100%  96%  93% 100% 100%  96%    3
 art          93%  96%  96% 100%  96%  96% 100%    5
 a            74%  88%  92%  92% 100% 100%  81%    6
 air          89%  93% 100% 100% 100%  91% 100%    4
```
At `k_res` (3–6), **(C) = 100% → T(article) = article → input = output**: the article IS the resonant eigenstate (F804), demonstrated on real simplewiki articles. And the **clean walk** (commit only the unambiguous single-winner successor; stop at a branch) reproduces the article **exactly (100%)** at every k where (C)=100% — deterministic encyclopedia output on the RBS-HDC substrate, GPU-free, simplewiki-only, no translation.

## What we learned
1. **Input = output is real and reachable.** The article is an exact fixed point of the RBS-HDC transition operator at a finite k_res — the F804 resonance is not just a reading, it holds on real data.
2. **Deterministic generation works** at k ≥ k_res via the clean (unambiguous-commit) walk — the F806 cascade was a greedy artifact, now removed.
3. **The remaining gap is context-key fidelity, not the fiber.** (C) is NON-monotonic in k (hits 100%, then dips, e.g. april 100%@k6 → 95%@k8). Combinatorially impossible (more context ⇒ more determinism), so the dips are HV fold-bind mis-retrievals: folding more (token,pos) binds slowly erodes key separation, costing ~4–7% at some k. The eigenstate is reached, just not at EVERY k≥k_res.

## Next (the context-key refinement — carries #227)
Make (C) = 100% monotonically at k ≥ k_res by sharpening the context key: (a) permute-based positional binding (canonical VSA sequence encoding) instead of pos-role bind; (b) a cleanup/resonance iteration (project the retrieved estimate back onto a clean token and re-resonate — the F804 power-iteration/Kuramoto-lock) so a near-tie phase-locks instead of argmax-guessing; (c) higher D. Any of these should remove the dips and give a dependable deterministic walk at all k ≥ k_res.

## Honest scope
- Short abstracts (28–49 tokens), 5 articles — first confirmation. Longer articles raise k_res and need the markup form-kernels (#225) + a streaming graph.
- (C) is the clean instrument metric (no greedy cascade); the deterministic GENERATOR is the clean walk, exact at k≥k_res but currently dependent on (C)=100% there (hence the key-refinement).
- Minted per-token vectors; the glyph-grounded `_word_hv` variant (F805) is a separate measurement (adds collision noise).

## Verdict
The encyclopedia article is a RESONANT FIXED POINT of the RBS-HDC transition operator — at finite k_res every context retrieves its own successor, so T(article)=article: input = output, the eigenstate (F804 confirmed on real articles). A clean walk reproduces it exactly at k ≥ k_res — deterministic encyclopedia output on RBS-HDC, GPU-free, simplewiki-only, no translation (F805). F806's greedy 22% was a generation cascade, not the instrument (on-path retrieval 96–100%). The one remaining gap is context-key fidelity (non-monotonic dips after k_res, ~4–7% HV mis-retrieval), addressed by a sharper positional key + a cleanup/resonance iteration — the next build (#227).
