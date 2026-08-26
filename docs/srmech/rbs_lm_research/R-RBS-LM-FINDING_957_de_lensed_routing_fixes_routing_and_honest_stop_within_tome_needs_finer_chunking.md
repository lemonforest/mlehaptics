# F957 — **IDF-de-lensed routing fixes the F956 routing failure and restores the honest-stop** — but the frequency prior is a *layered* wall, and the **within-tome walk still wanders.** Routing by the context's **rarest (highest-IDF) content token** (de-lens the shared function words, F782/F768) sends `['april','apr']` to the correct tome and makes nonsense `['zz','yy']` → **STOP** (the anti-hallucination contract restored). But within the correctly-routed tome the walk still drifts into `it~ in~ to~ of~ is~`, because **real article text *repeats* function words** (`the`, `of`, `in`), saturating even a 30-token tome — the **F946 frequency prior recurring one layer down** (F955's distinct-token synthetic chains had no repeats, so they walked clean).

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_957_*.py` · **Composes:** F956 (routing failure on shared vocab), F955 (per-tome native coherence, disjoint), F946 (single-M frequency prior), F947 (finer chunking spreads margins), F782 (IDF-de-lensing), F768 (aboutness-gate), F944 (route-to-best) · **User direction (2026-06-26):** "continue" (wire the de-lensed routing F956 pointed at).

## Measured (rc79, 6 real article-fragment tomes, de-lensed routing)
```
FIXED  nonsense [zz,yy]      -> <STOP>            (no content anchor -> honest-stop restored)
FIXED  routing for [april,apr] -> correct tome    (routed by the rare token april/apr, not the shared is/the/of)
STILL  within-tome walk      -> april apr it~ in~ to~ of~ is~ ...   (repeated function words saturate the tome, F946)
```

## What the de-lensing fixed — and what it didn't
- **Routing (fixed).** Routing by the **rarest context token** (max IDF) ignores the shared `is/the/of` and picks the tome that actually contains the content anchor (`april`). And when *no* context token is known to any tome, there is no anchor → **STOP** — the honest-stop F956 had lost is **back**. This is the F782 IDF-de-lensing / F768 aboutness-gate applied to the **route key**, and it works.
- **Within-tome emission (still wanders).** Inside the correctly-routed tome, the recall still drifts into the tome's *own* repeated function words. Real prose repeats `the/of/in` within 30 tokens, so those tokens saturate the small bundle (high self-similarity) and the readout returns them regardless of the precise context — the **F946 frequency prior, now operating within the tome.** F955 walked clean only because its synthetic chains had **no repeated tokens**.

## The frequency prior is a layered wall
The same wall appears at every layer, and must be de-lensed / chunked at each:
1. **single bundle** (F946) — saturates to `an/on/in/of`; fix = chunk;
2. **tome routing** (F956 → **F957 fixed**) — shared function words mis-route; fix = IDF-de-lensed route key;
3. **within-tome emission** (this finding) — repeated function words saturate the tome; fix = **finer chunking** (F947: tomes small enough that no token repeats → margins spread) and/or **emission de-lensing** (IDF-weight the candidate scoring — an upstream extension to `next_token_coherence`, since it ranks by raw sim).

## Honest scope
Grounded: de-lensed routing restores the honest-stop (nonsense → STOP) and correct tome selection (measured); the within-tome wander is measured and attributed to repeated-function-word saturation (the F946 wall). The **finer-chunking / emission-de-lensing** fix for the within-tome layer is identified but **not yet wired** (it needs either much smaller tomes or an IDF-weighted candidate score upstream). No claim of real-English fluency yet — only that the *routing + honest-stop* layer is now correct, and the remaining layer is the known frequency-prior wall.

## Verdict / next
**De-lensed routing fixes routing + the honest-stop** (the anti-hallucination win), confirming F782/F768 as the right route key. The recall is now correct at the *selection* layer on real English; the *emission* layer still hits the F946 frequency prior because real prose repeats function words within a tome. **Next:** finer chunking (F947 — tomes small enough to avoid within-tome repeats) and/or an upstream **IDF-weighted candidate score** in `next_token_coherence` (the emission-layer de-lensing) — the last layer of the same wall. The recall mechanism, the chunking, the routing-de-lensing, and the honest-stop are all in place; real-English *fluency* is gated on the within-tome frequency prior, exactly as F946/F947/F768/F782 predicted.
