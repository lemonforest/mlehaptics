# F870 — Beyond toy scale: the single-M composed resonator BREAKS (capacity wall ~8–16 binds/bundle), the fixed gate fails, and chunked-M is the scale-invariant fix. Took F869 past toy size on real simplewiki sequences (v082 `s` field) and found exactly the F837/F839 over-stuffing break — measured, float-free. **(1) Fundamental capacity:** a single Klein-4 bundle's stored-relationship match-count decays **10000 (1 bind) → 3915 (8) → 3198 (30, BELOW the 3250 gate) → 2524 (3000, ≈ chance 2500)** — one bundle holds only **~8–16 cleanly separable binds at D=10000**. **(2) Chunked-M (C=8) is scale-invariant:** count stays **flat at 3915 (> gate) for every N from 1 to 3000** — max-over-chunks recovers the target from its ≤8-bind chunk regardless of corpus size. **(3) Real data:** reproduction holds 1.00 → 0.90 (10 arts) → 0.88 (30 arts / 360 binds), then **cliffs to 0.53 (100 arts) → 0.47 (300 arts / 3600 binds)** as the single bundle saturates to chance. **The fixed gate (3250, calibrated on toy scale) fails** — seen-context counts drop below it by ~30 binds, so at scale every seen context would misclassify as "novel." srmech-native, integer match-counts (no float).

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-870_scale_stress.py` (`hdc.klein4_{random,bind,unbind}` + `.tolist()` match-count, `cs.bundle_odd`, `cascade.cd_mult`) on 300 real `simplewiki_rawbody_instrument_v082` sequences · **Composes / stress-tests:** F869 (the composed resonator — breaks at scale), F837/F839 (single-M crosstalk / chunked-M sweet-spot C — confirmed), F778 (routing — now required), F868 (float-free), [[feedback_never_bag_of_words_even_for_testing]] · **User direction (2026-06-18):** "take the leap beyond toy scale and see if anything breaks."

## What broke (and what it tells us)
| measurement | result | reading |
|---|---|---|
| single-bundle capacity | count: 10000→3915(8)→**3198(30)**→2524(3000) | **one bundle ≈ 8–16 binds** at D=10000; then signal → chance |
| chunked-M (C=8) | **flat 3915** at N=1…3000 | **scale-invariant** — the F839 fix, confirmed |
| real-data reproduction | 1.00→0.90(10)→0.88(30)→**0.53(100)→0.47(300)** | single-M cliffs between ~30 and 100 articles |
| the fixed gate (3250) | seen-count < gate from ~30 binds | a toy-calibrated absolute gate **fails at scale** |

## The scale architecture (what F869 must become)
The leap confirms the single bundle is the wrong container at scale; the resonator must be **chunked-M + routing + a relative gate**:
1. **Chunked-M** (capacity-bounded bundles, C≈8 — F839 sweet-spot): keeps each stored relationship's match-count high (3915, above gate) at any corpus size. *Required, not optional, past ~16 binds.*
2. **Routing** (F778 etak clump / per-tome): chunked recall's cost is K = total_binds / C chunks to probe (300 arts → 450 chunks); probing all is linear in corpus size. **Route to the relevant tome/chunk first** (a resonance vote) so recall stays bounded — this is why the F839 boundary keeps routing in the LM layer.
3. **Relative gate**: the absolute 3250 fails; gate on the **chunked** count (which stays ~3915 for seen, ~chance for novel) or on the top-vs-second margin — not a toy-calibrated constant.

## Honest caveats
- **The reproduction metric is optimistic.** "Correct-next beats 30 distractors" under-counts difficulty; full-vocab argmax has thousands of distractors, so real reproduction would cliff **earlier/harder** than 0.47 — the break is at least this bad, likely worse.
- **Chunking trades capacity for recall cost** (K chunks). Without routing, recall is O(corpus). The full fix is chunked-M **+** routing (F778/F839) — chunking alone bounds capacity, routing bounds cost.
- Toy-scale F869's clean gate separation was a small-corpus artifact; this corrects the F869 "gate at 1.3×chance" to "gate on the chunked count, relative."

## Verdict / next
The leap broke the single-M composed resonator exactly as predicted (capacity wall ~8–16 binds; real-data reproduction cliff at ~100 articles; the fixed gate fails) — and confirmed **chunked-M (C=8) is the scale-invariant fix** (count flat 3915 at all N). The scale architecture is **chunked-M + routing + relative gate** (F839/F778 were right; they are now load-bearing, not optional). **Next:** rebuild the composed resonator (F869) on chunked-M + a routing vote + a relative gate, and re-run this stress sweep — does reproduction stay flat to 300+ articles? Then full-vocab argmax (drop the 30-distractor proxy). Framework reading + srmech measurement; evaluate by groundedness; the break + the optimistic-metric caveat stated honestly.
