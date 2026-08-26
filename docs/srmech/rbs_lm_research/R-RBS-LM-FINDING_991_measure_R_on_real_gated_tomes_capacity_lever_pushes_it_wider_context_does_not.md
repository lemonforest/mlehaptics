# F991 — **R measured on real gated tomes ≈ 0.85–1.4 (short); it CAN be pushed further, but by the CAPACITY lever (tome size), NOT by context width — and the landmark payoff is honest-small because base per-step accuracy, not drift, is the wall.** Answering F990's next step. On real simplewiki gated tomes: the free-run coherence-reach **R ≈ 1.37** (max_tome 60) — recall derails after ~1.4 autoregressive steps, so landmark spacing 2R ≈ 2.7 tokens. **Can R be pushed further?** (a) **Wider context (F962 recursive-compose): NULL** — k_ctx 1/2/3 all give R≈1.37 (+0%); context width is not the lever. (b) **Smaller tomes (the capacity axis): YES** — R = **3.89** (max_tome 15, 181 tomes) vs **2.42** (30) vs **0.85** (60); chunking finer ~4.5× the reach (landmark spacing 2R = 7.8 vs 1.7). **The landmark payoff itself is small** (free-run 34% → landmarks-every-2R 36% → landmarks-every-step 39%): re-anchoring fixes *drift*, but on a saturated real corpus the limiter is **base per-step accuracy (~39% ceiling)**, not drift.

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probes:** `R-RBS-LM-FINDING_991_*.py` (+ `_kctx_probe.py`) · **Grounds:** F990 (the coherence-reach R = |q| half-life; landmark spacing 2R), F962/RC-1 (recursive-compose k_ctx — tested null here), F985/F984 (gated tomes), F975/F896 (capacity wall), F934 (honest-STOP) · **User direction (2026-07-02):** "measure R on the real gated tomes and set landmark spacing 2R and find out if it can be pushed further." · **Scope:** framework/tool; sparse Klein-4 + gated `recursive_cut`; no dense/numpy/abs.

## Grounded (rc97, real simplewiki gated tomes)
```
R vs CONTEXT WIDTH (F962 recursive-compose; arts[:6], 75 tomes):
  k_ctx=1 : R = 1.37   k_ctx=2 : R = 1.37   k_ctx=3 : R = 1.33     -> wider context does NOT push R (+0%)

R vs TOME SIZE (the CAPACITY lever; arts[:3], n=1566 vocab):
  max_tome=15 (181 tomes): R = 3.89  -> landmark spacing 2R = 7.8
  max_tome=30 ( 93 tomes): R = 2.42  -> 2R = 4.8
  max_tome=60 ( 48 tomes): R = 0.85  -> 2R = 1.7            -> SMALLER tomes ~4.5x the reach

LANDMARK PAYOFF (max_tome=30; re-anchor to truth every L):
  free-run (no landmarks) : 34%
  landmarks every 2R=5    : 36%      (+2pp -- drift is NOT the bottleneck here)
  landmarks every 1       : 39%      (upper bound = base per-step accuracy with perfect context)
```

## The reading (three honest answers)
1. **R is short on real corpus (~1.4 at large tomes)** — the |q| half-life of a recall front (F990) is barely one beat when the tome carries real saturated load (F975/F896 wall). Landmark spacing 2R ≈ 2–3 tokens: on a saturated tome you must re-anchor almost every content word.
2. **R CAN be pushed — by the capacity lever, not context width.** Wider context (F962) is *null* (the derail isn't a context-starvation problem — it's crosstalk). **Smaller tomes push R ~4.5×** (0.85 → 3.89): less load per tome → each front reaches further → sparser landmarks (2R 1.7 → 7.8). The trade is explicit: **finer chunking buys reach at the cost of more tomes (routing overhead)** — the capacity/routing Pareto the whole recall arc has circled (F896/F975).
3. **The landmark payoff is honest-small (34→36→39%) because base accuracy, not drift, is the wall here.** Re-anchoring every 2R lifts only +2pp, and even *perfect* context every step caps at 39%. On a saturated real corpus the limiter is the **base per-step recall accuracy** (the F896 crosstalk floor), which landmarks cannot fix — landmarks fix *compounding drift*, and drift only dominates when free-runs are long and base accuracy is high. So the F990 landmark architecture is real but **conditional**: it pays off where drift dominates (long coherent runs), not on saturated short tomes where base accuracy is the ceiling.

## What pushes R vs what pushes accuracy (the clean separation)
- **Push R (reach):** the **capacity lever** — smaller tomes (more de-lensing / finer `recursive_cut`). Grounded ~4.5×.
- **Push accuracy (the 39% ceiling):** NOT landmarks, NOT context width — it's the **gate + de-lensing** (F984/F985, ~2× content recall) and the **reach modes** (etak-deeper F986, deconvolution F988) applied per hard target. Landmarks and reach are *orthogonal* levers: landmarks stop drift, the gate+reach raise the per-step floor.

## Honest scope
Grounded: R≈1.37 at mt=60; R vs tome-size 3.89/2.42/0.85; wider-context null; landmark payoff 34/36/39%. Two corpus slices (arts[:6] for k_ctx, arts[:3] for the tome-size sweep — the absolute R differs slightly with slice, but the *trends* (context-null, tome-size-positive, payoff-small) are the robust results). Free-run autoregressive reach (feeds the recalled token); the 39% "every-step" upper bound is the base per-step accuracy with perfect context. Composes F990/F962/F985/F984/F975. No fluency claim — this measures the reach/accuracy structure, honestly. `/tmp` was reset mid-run (venv survived); re-ran from durable storage.

## Verdict / next
**R ≈ 1.4 on real gated tomes (short); pushable ~4.5× by the CAPACITY lever (smaller tomes), NOT by context width (null); landmark re-anchoring gives only +2pp because base per-step accuracy (~39%), not drift, is the wall.** The clean separation: **capacity/tome-size pushes reach R; the gate + etak/deconvolution reach-modes push the per-step accuracy floor; landmarks stop drift (only where drift dominates).** These are three orthogonal levers, now each measured. **Next:** (i) the capacity/routing Pareto — plot R and tome-count vs max_tome to pick the operating point where 2R landmark-spacing meets acceptable routing overhead; (ii) since base accuracy is the wall, stack the gate + reach-modes (F984/F986/F988) at each step and re-measure the 39% ceiling; (iii) test the landmark architecture on a LOW-load regime (long coherent runs) where drift *should* dominate and landmarks *should* pay off — the honest falsification of F990's landmark claim.
