# F896 — The full Siona recall stack is COHERENT END-TO-END: route → address → stream = 1.00 @ N=500 (EC-protected), with the per-article k* wired in. Caught + fixed a real corpus-scale limit (the single Hamming(7,4) carry tops out at 256 pages → widen it), and corrected the k* framing (intra-article unique walk ≠ cross-article routing length). Wired the de Bruijn unique-walk routing (F895) through the whole stack and measured it end to end: **ROUTE (L=8 context → page index) 63/63 = 1.00 · ADDRESS (sedenion navigate+carry fetch) 63/63 = 1.00 · ADDRESS under a 1-bit address fault (Hamming EC) 63/63 = 1.00 · END-TO-END (route+address+fault+stream) 63/63 = 1.00.** Every sampled article is routed, addressed (even with a flipped carry bit), and reproduced exactly. **A real bug caught:** the first run cliffed to 0.51 — a single **Hamming(7,4)** carry holds only 4 data bits, so it addresses just 16 base-slots × 16 = **256 pages**; at N=500 every index ≥256 overflowed. Fixed with **Hamming(15,11)** (`carry(…, n=4)`, 11 data bits → 16×2048 = **32,768 pages**); full simplewiki (271k) needs **n=5** (Hamming(31,26) → 67M). **The k* framing, corrected:** the instrument's `k*` (median 7) is the **intra-article** de Bruijn unique walk (minimal window unique *within an article*); the **cross-article** routing length (the context to disambiguate among N articles) is a *different* quantity that **scales with corpus size** — minimal-routing-L mean 2.2 @ N=500 vs ~8 @ N=2000 (F895b) — converging toward ~k* near full-corpus scale. So "route on enough context" means **cross-article** context, set by N.

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-896_end_to_end_stack_kstar.py`, 500 `simplewiki_v082` articles + their `k*` field · **Composes:** F895 (routing coherence / context-length lever), F893 (the route→address→stream wiring), F891 (the sedenion carry — its 256-page limit now fixed by a wider Hamming), F879 (the stream), F894 (`SionaPageGrid` — the package address layer to widen) · **User direction (2026-06-21):** "wire k* into the router + an end-to-end route→address→stream measurement at L=8."

## Measured (sparse, srmech-native; N=500)
| stage | result |
|---|---|
| ROUTE (L=8 unique-walk context → page index) | 63/63 = **1.00** |
| ADDRESS (sedenion fetch, clean) | 63/63 = **1.00** |
| ADDRESS (sedenion fetch, 1-bit address-carry fault) | 63/63 = **1.00** (EC-recovered) |
| END-TO-END (route + address + fault + stream) | 63/63 = **1.00** |
- The **whole stack reproduces every sampled article exactly**, even with a flipped bit in each address carry. Reproduction regime; the rc1 routing-coherence gate demonstrated through the full pipeline.

## The carry-width fix (a real corpus-scale correctness item)
- **Bug:** `carry(bits, n=3)` = Hamming(7,4) = **4 data bits** → addresses 16 base-slots × 2⁴ = **256 pages**. The first N=500 run cliffed to **0.51** (every index ≥256 overflowed the carry → wrong address). This is exactly the ">256 pages" limit F891 flagged.
- **Fix:** Hamming(15,11) (`n=4`, **11 data bits**) → 16 × 2¹¹ = **32,768 pages** → N=500 fixed to 1.00. **Full simplewiki (271,174)** needs **n=5** (Hamming(31,26) → 16 × 2²⁶ ≈ 1.07e9 pages), single-error-correcting in one codeword.
- **Package follow-up (siona):** `SionaPageGrid` (`page_grid.py` / `page_grid_ops.py` / the TOML) hard-codes 4 data bits → **parametrize the Hamming order `n`** (or auto-size from the page count): default n=4 (32,768) for tome/smallwiki-chunk scale; n=5 for full-corpus.

## The k* clarification (intra vs cross-article)
- **k\*** (v082 `k`, median 7, max 16): the **intra-article** minimal unique walk (the de Bruijn unique window *within one article's* token graph). 98% of articles have one.
- **Routing-L**: the **cross-article** minimal context to disambiguate among **N** articles — scales with N (≈ log_V N collisions): ~2–4 @ N=500, ~8 @ N=2000. They are different lengths that **converge near full-corpus scale** (where N ≈ the full simplewiki and routing needs ~k* tokens). The router must adapt L to **N**, not just to a single article's k*.

## Honest scope
- **Reproduction regime** (F841): query = a real context window from the article → route+address+stream reproduces it. The natural grounded-recall regime and the rc1 gate; **generalization** (novel/paraphrase context) is the separate post-rc1 axis.
- N=500 (full pages tractable); routing already 1.00 at L=8 there (cross-article L needed is only ~2–4, so L=8 is comfortably above). The carry-width and routing-L both **scale with corpus** — parametrized, not fixed.
- Sparse held: octonion-product route-key + Klein-4 resonance + sedenion EC address + phase-keyed stream; no dense, no numpy, no bag.

## Verdict / next
The **full Siona recall stack is coherent end-to-end at 1.00** (route → address → stream, EC-protected) in the reproduction regime — the rc1 routing-coherence gate met through the whole pipeline. Two real scale items surfaced and were resolved/clarified: the **carry width must scale with corpus** (Hamming n: 256 → 32k → 67M pages; parametrize `SionaPageGrid`), and **routing context length is cross-article and scales with N** (distinct from intra-article k*). **Next (toward rc1):** (1) **parametrize `SionaPageGrid`'s Hamming order** (the package fix, siona branch); (2) the remaining rc1 gates — **language-scaffolding + smallwiki** shipping, the **C-host cascade runner** (§66/§67); (3) **generalization** (novel-query routing) post-rc1. Framework reading → srmech measurement; bug caught and fixed; k* framing corrected; end-to-end coherence demonstrated honestly.
