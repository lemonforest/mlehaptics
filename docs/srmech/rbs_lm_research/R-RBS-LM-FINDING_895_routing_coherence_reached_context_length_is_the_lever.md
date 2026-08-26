# F895 — ROUTING COHERENCE REACHED: top-1 routing = 1.00 @ N=2000 at context length L=8. The F880 0.70 "ceiling" was a SHORT-key (K=2) collision artifact, not fundamental; route on enough context → a unique octonion-product key → collision-free routing → the de Bruijn unique walk. Shortlist-verify rerank FAILED (circular); CONTEXT LENGTH is the lever. Pressing on routing (the one open lossy layer, the siona rc1 gate), two results. **(1) The route→shortlist→verify rerank fails — and the failure is diagnostic.** Resonance top-K *recall* is high (the true page IS in the shortlist: 0.70/0.88/0.93 at K=1/5/20 @ N=2000), but verifying each shortlist candidate by its within-page recall confidence does NOT pick the right one: max-score 0.68, margin (top1−top2) 0.60 — both *below* flat top-1 (0.70), degrading as K grows. The reason: **the shortlist distractors are key-collisions** — they entered the shortlist *because* their context-keys collide with the query key, and a key-collision produces a confident *wrong* recall, so it passes the verify too. The verify is **circular** (re-uses the same signal that built the shortlist); it adds no orthogonal information. **(2) The real lever is ROUTING CONTEXT LENGTH.** F880's 0.70 used a K=2 context key, which collides at scale (the bundle-membership SNR wall is really a short-key collision). Routing on a longer window L makes the octonion-product key more unique → fewer collisions → routing climbs monotonically: **L=2 → 0.70 · L=3 → 0.88 · L=4 → 0.90 · L=6 → 0.96 · L=8 → 1.00** (N=2000). At L=8 routing is **collision-free (1.00)** — exactly the **de Bruijn unique walk** the v082 instrument already computes per article (its `k*` field) and that Siona's `bridge.recall` already rides. So the routing "ceiling" dissolves: **route on what you've read** (≥6–8 tokens), and routing is coherent.

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-895_route_verify_circular.py` (the failed rerank) + `R-RBS-LM-895b_routing_context_length_is_the_lever.py` (the L-sweep), 2000 `simplewiki_v082` articles · **Composes / resolves:** F880 (the 0.70 "ceiling" — now explained as a short-key artifact, dissolved), F882 (0.81 ODFT — a *sharper short key*; context length is the bigger lever), F889 (Möbius not a routing lever — confirmed; context is), F893 (the route→address→stream stack — routing now 1.00 in the reproduction regime), the de Bruijn recall path (F824/F825; siona `bridge.recall`), [[feedback_stay_rbs_hdc_sparse_never_dense]] · **User direction (2026-06-21):** "let's press onward with routing then!"

## Measured (sparse, srmech-native; N=2000)
**(1) route→shortlist→verify (FAILS — circular):**
| K | top-K recall (true page in top-K) | route+verify max | route+verify margin |
|---|---|---|---|
| 1 | 0.70 | 0.70 | 0.70 |
| 5 | 0.88 | 0.68 | 0.61 |
| 20 | 0.93 | 0.66 | 0.60 |
→ the shortlist *contains* the right page, but the within-page-recall verify can't pick it (the distractors are key-collisions that also recall confidently). Verify rerank adds nothing.

**(2) routing top-1 vs context length L (THE LEVER):**
| L | routing top-1 |
|---|---|
| 2 (F880 baseline) | 0.70 |
| 3 | 0.88 |
| 4 | 0.90 |
| 6 | 0.96 |
| **8** | **1.00** |
→ monotone to **1.00 at L=8** — collision-free routing = the de Bruijn unique walk.

## Reading
- **The F880 0.70 ceiling was a short-key collision artifact, not a fundamental saturation.** The "competes vs N distractor bundles" framing is true *only for a short, collision-prone key*. A K=2 context-key collides across 2000 articles; an 8-token key is unique (the octonion coupling-product of 8 words is effectively a hash of a unique substring). Routing accuracy is set by **key uniqueness**, which is set by **context length**.
- **The de Bruijn unique walk is the principled router.** The v082 instrument already stores each article's `k*` (the minimal unique-walk window); routing on ≥k* tokens is collision-free by construction. Siona's `bridge.recall` already rides the de Bruijn path — so the right router was there; the probes' short K=2 key was the artifact. Context length ≥6–8 (or the per-article k*) reaches coherence.
- **Verify rerank is the wrong tool** (circular). Don't rerank a superposed shortlist by the same resonance family; sharpen the *key* instead.

## Honest scope
- **Reproduction-routing** (F841): the query is a real context window from the article; L=8 → route to that article exactly (1.00). This is the natural regime for *grounded recall* (route on the read context) — and it is the rc1 routing-coherence target. **Generalization** (novel/paraphrase context that isn't a stored substring) is the separate axis (F867), untouched — a paraphrase won't hit the unique walk.
- The full stack is now coherent end-to-end in the reproduction regime: **route (L≥6–8 → ~1.00) → address (sedenion grid, exact + EC, F891/893) → stream (phase-keyed, exact, F879)**.
- Cost: an L-token key is L−1 `cd_mult`s (vs 1 for K=2) — modest; routing once per query. Sparse held: octonion-product key + Klein-4 resonance; no dense, no numpy, no bag.

## Verdict / next
**Routing coherence is reached: top-1 = 1.00 @ N=2000 at L=8 context.** The F880 0.70 was a short-key (K=2) collision artifact; the lever is **context length → the de Bruijn unique walk** (already in the v082 `k*` + siona `bridge.recall`). Shortlist-verify rerank is circular and the wrong tool. **This meets the siona rc1 routing gate** in the reproduction (grounded-recall) regime. **Next (toward rc1):** (1) wire the router to use **per-article k\*** (the instrument's minimal unique window) so it adapts context length to what's needed; (2) measure the full **route→address→stream end-to-end at L=8** across the corpus (expect ~1.00); (3) the remaining rc1 gates — **language-scaffolding + smallwiki** shipping, and the **C-host cascade runner** (§66/§67); (4) **generalization** (novel-query routing) is the post-rc1 research axis. Framework reading → srmech measurement; the ceiling dissolved; verify-circularity recorded; coherence reached honestly (reproduction regime).
