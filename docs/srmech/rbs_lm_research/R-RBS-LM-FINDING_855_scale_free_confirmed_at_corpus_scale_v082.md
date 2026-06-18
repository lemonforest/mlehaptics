# F855 — Scale-free/fractal signature CONFIRMED at corpus scale on the clean 0.8.2 instrument (F854 v082). 8,000 articles (4.68M tokens, 140,392 nodes, 2.92M edges): power-law degree exponent γ converges to **2.00** at the deep tail (1.74 k≥10 → 1.78 k≥20 → 1.89 k≥50 → **2.00 k≥100**), max/median degree **9018×** (vs 1375× at the 400-article scale, F852) — the heavy tail sharpens with scale, no characteristic scale. The fractal/scale-free structure is not a small-sample artifact; it holds and intensifies at 20× scale on the fresh, attested instrument. live srmech 0.8.2.

**Date:** 2026-06-18 (autonomous) · **srmech:** 0.8.2 (live) · **Provenance:** `/tmp/fractal_v082.py` on `simplewiki_rawbody_instrument_v082.ndjson` (F854), 8,000-article window-co-occurrence + Clauset tail-MLE · **Composes:** F852 (scale-free at 400 articles), F854 (the clean instrument), F849/F850 (hubs=mass), [[user_stance_no_information_without_value]].

## Measurement (8,000 articles, v082)
| tail k_min | γ (Clauset MLE) |
|---|---|
| 10 | 1.74 |
| 20 | 1.78 |
| 50 | 1.89 |
| 100 | **2.00** |
- top degrees `[45091, 38910, 33596, …]`, median **5**, **max/median = 9018×**.
- γ→2.0 is the canonical hub-dominated scale-free regime; the deeper the tail, the cleaner the power law (finite-size convergence) — consistent with F852's γ→~2 and *sharper* at scale.

## What it confirms
- "Scale not fixed" / fractal (F852) is a **stable corpus-scale property**, not a 400-article fluke — it strengthens with scale (1375×→9018× max/median).
- The Cayley–Dickson-generator self-similarity reading (F852) stands: the structure is scale-invariant across a 20× zoom.
- The hubs (the power-law tail) are the gravitational masses / function-word background (F849/F850) and the de-lensing target for routing (F853).

## Verdict
The clean v082 instrument exhibits the same scale-free/fractal signature as F852, sharper at scale (γ→2.00, 9018× spread). The physics-of-the-knowledge-metric picture (F849–F853) rests on a corpus-scale-confirmed foundation. Full 271k run deferred (8k is decisive + bounded-memory; full-corpus needs streaming-degree to avoid the neighbor-set blowup). Framework reading + Class-L measurement; the spectral fractal-dimension number goes to the expert.
