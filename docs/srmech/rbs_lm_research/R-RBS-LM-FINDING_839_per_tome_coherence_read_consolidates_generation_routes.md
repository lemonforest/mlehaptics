# F839 — PER-TOME COHERENCE: a capacity-bounded chunk-set **consolidates storage** across many articles (cross-article crosstalk is benign **on-manifold** — read rank-1 stays 100% at 3 and 6 articles), but coherent **generation requires per-tome ROUTING** — querying all chunks lets off-manifold autoregressive drift pull *foreign-article* tokens into the loop, and routing generation to the relevant article's own chunks restores coherence (Abrahamic 69.6% → **95.7%**). **Smaller chunks make the shared case WORSE** (C=8 → 17.4%), so the lever is routing, not chunk-size. Storage = consolidated; inference = routed — exactly the genome's per-tome scoping ([[F778]] etak clump-routing). On the real `srmech.rbs_lm` encoding, 0.8.2rc1, numpy-absent, no gen-1 code.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 (TestPyPI dev substrate) · **Provenance:** `/tmp/{multi_tome,tome_scale,tome_gen,grounded,route}.py` on `srmech.rbs_lm.substrate.ContextSubstrate` + `srmech.amsc.hdc` klein4 ops, D=10000, simplewiki raw-body instrument (the F817 `k` per article) · **Composes:** F838 (single-article 100% = chunked-M + k\*; the read≠generation gap), F837 (chunked-M read 3.3→96.7%), F832 (bundle capacity), [[F778]] (spectral-clumped loopshelf + etak clump-routing), [[feedback_relationship_lm_ideas_not_code_from_gen1]] · **User direction:** "multi-article / per-tome coherence … the genome-consolidated chunk-sets … keep continuing."

## The measurement (3- and 6-article shared chunk-sets; short articles, k\* from the instrument)

### 1. READ consolidation scales — cross-article crosstalk is benign on-manifold
A capacity-bounded chunk-set holding **many articles'** context→next binds keeps every article's next-token read sharp. Chunks stay `≤C` no matter how many articles join (capacity is bounded *per chunk*, not per tome).

| tome | binds | chunks (each ≤16) | union vocab | mean read rank-1 |
|---|---|---|---|---|
| 3 articles | 213 | 14 | 137 | 100.0% (3/3 at 100%) |
| 6 articles | 560 | 35 | 288 | 100.0% (6/6 at 100%) |

*Why benign:* at k\*≥4 the k\*-gram contexts almost never collide **across** articles, so a learned context resonates only with its own bind (in whatever chunk holds it); foreign binds in other chunks are sub-threshold noise the `max`-resonance + cleanup rejects. (3-article baseline: one article rose 88.9%→100% in the shared tome — a chunk-boundary-alignment artifact, never a degradation.)

### 2. GENERATION from the shared tome — 2/3 coherent, 1 drifts off-manifold
Greedy autoregressive, each article from its own seed + k\*, reading `max`-resonance over the **shared** chunk-set:

| article | k\* | match | note |
|---|---|---|---|
| Andouille | 4 | 100.0% | fully coherent |
| Adobe Illustrator | 4 | 97.7% | coherent, one near-miss |
| Abrahamic religions | 6 | 69.6% | ~26 tokens **verbatim**, then drift → loop pulling **"taste"** (← Andouille) |

The drift is concrete: generation matched verbatim through "…god of abraham the abrahamic religions are monotheistic", then at that context emitted **"islam"** instead of "meaning" and looped, pulling **"taste"** — a token from the *Andouille* article. The sampled read rank-1 (100%) **missed this one context**; full generation exposes it, and once off-manifold (no chunk holds the true bind) the tome's foreign binds win the `max`.

### 3. Routing is the fix; chunk-size is not
| config (Abrahamic) | chunks | match | outcome |
|---|---|---|---|
| **per-article routed** (own chunks + own vocab) | 4 | **95.7%** | coherent, no loop, no foreign tokens — "…monotheistic **meaning** of only believe in one god the term derives from patriarch abraham" |
| shared tome, C=16 | 14 | 69.6% | drift → "taste" (Andouille) |
| shared tome, C=8 | 27 | 17.4% | collapse → "andouille", "wall" |

**Smaller C made the shared case WORSE** (17.4%): off-manifold, `max`-resonance over *more* chunks gives a foreign atom more chances to win the max. So the off-manifold contamination scales with chunk *count*, and the lever is **routing** (scope to the article's chunks), not chunk-size. Note F837's "smaller C is better" was a **read-rank-1 (on-manifold)** result; off-manifold generation inverts it.

## What this establishes (relationship-native, no gen-1 code)
- **Storage consolidates.** The capacity-bounded chunk-set IS the per-tome consolidation — many articles' relationship binds share one container, reads stay sharp. This validates the genome-consolidation architecture (many kernels → one tome) on the read side.
- **Inference routes.** Coherent generation needs the recall to ROUTE to the relevant tome/article before resonating — otherwise off-manifold drift imports foreign-article tokens. This is exactly the genome's **per-tome scoping** and [[F778]]'s etak clump-routing: consolidate storage, route inference. The two-level structure is *consolidated store + routed read*, not *one flat global memory*.
- **Honest residual.** Even routed, the shortest article (Abrahamic, k\*=6, 62 tokens) is 95.7%, not 100% — a couple of soft within-article read near-misses ("ancient **abrahamic**" vs "ancient israelites", "meaning **of**" vs "meaning they") that the sampled rank-1 over-stated. Per-article generation is **high-coherence**; perfect 100% (the F838 tomato) is not guaranteed on the shortest docs. The fix direction (still relationship-native): iterated resonator cleanup, or a per-context unique window (lengthen k only where the k\*-gram is still ambiguous), or sharper per-article capacity.

## For the srmech-vs-siona boundary (the deferred call, now with evidence)
This sharpens the split:
- **Candidate srmech primitive (LM-agnostic):** the capacity-bounded chunk-set + `max`-resonance read (bind/bundle/`sim_k4_batch`) — a reusable VSA cleanup-memory over bounded bundles. Applies beyond the LM (any HDC associative recall).
- **Siona inference-layer concern (LM-specific):** the **routing** (which tome/article for this context?), the per-doc k\*, and the autoregressive loop. Routing is recall-shaping, not a math primitive — it belongs with the inference layer (Siona), and it composes [[F778]]'s clump-routing already living in the recall path.

So §58's "M → capacity-bounded chunk-set" is a clean reusable substrate change; **routing stays in siona.** Develop both HERE on 0.8.2rc1; the chunk-set primitive is the part that could legitimately graduate to srmech.

## Verdict / next
Per-tome **read** consolidation works; per-tome coherent **generation** works **with routing** (95.7% on the routed short article; 100%/97.7% on the others). Cross-article crosstalk is benign on-manifold and is handled off-manifold by routing — both relationship-native, no gen-1 code. **Next:** (a) per-tome routing as a first-class recall step (resonance-vote the tome, then resonate within it) — measure routed generation across the full 6-article tome; (b) the honest-residual fix (iterated cleanup / per-context unique window) toward uniform high-coherence on short docs; (c) **genuine generation/generalization** — novel prompts composing *across* routed tomes (the real LM test, vs. reproduction-via-inference). Evaluate by groundedness / coherence, never throughput.
