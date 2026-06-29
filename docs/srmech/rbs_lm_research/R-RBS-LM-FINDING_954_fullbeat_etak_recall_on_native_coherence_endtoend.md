# F954 — the full-beat etak recall now runs **end-to-end on native `next_token_coherence`** (F953/§78): the verdict drives the step — **COHERENT → emit top₁, BRANCH → sample `branch_candidates`, STOP → honest-stop** — replacing the F941–F945 recompute-from-`M` wrapper. With the **default floor** (0.34 = chance `Q(1,4)` + band `Q(9,100)`) the saturated shadow sits *above* the floor, so every step reads BRANCH and the walk *wanders*; with a **tuned floor** (0.42, separating the clean top₁ = 0.468 from its shadow top₂ = 0.395) the walk is a **clean COHERENT cyclic advance**. The principled no-tuning fix is **chunking** (F947 spreads margins to 0.74, far above any floor).

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_954_*.py` · **Composes:** F953 (native `next_token_coherence`), F940–F945 (the full-beat recall mechanism), F946 (single-M saturation → STOP), F947 (chunking spreads margins), F943 (the collapse-margin readout) · **User direction (2026-06-26):** "do next steps" (swap the wrapper to the native method; run the full-beat etak recall on native coherence end-to-end).

## The native-coherence recall step (the swap, complete)
```python
r = sub.next_token_coherence(out, noise_floor=nf)      # native §78 readout
if   r.verdict == 'STOP':   break                      # honest-stop: the now won't collapse
elif r.verdict == 'BRANCH': nxt = sample(r.branch_candidates)   # a real choice point
else:                       nxt = r.candidates_topk[0]          # COHERENT: emit the one next
```
No recompute from `sub.M`/`sub.ctx`/`sub.vocab_vecs` — the verdict, margin, raw sims, floor and branch set all come native and exact.

## Grounded (chain `a b c d e`, ctx `['a','b']`, rc79)
```
DEFAULT floor 0.34 : d~ c~ b~ e~ a~ c~ c~ a~ b~ d~ d~ a~   (BRANCH every step -> wanders)
TUNED   floor 0.42 : c  d  e  a  b  c  d  e  a  b  c  d     (clean COHERENT cyclic walk)
```
- **Default floor too low for a saturated bundle.** The 13-pair chain bundle at D=8192 is mildly saturated (top₂ = 0.395 above the 0.34 floor), so `top₂ ≥ floor ∧ margin < branch_band(0.12)` → BRANCH every step → random-sample → wander.
- **Tuned floor 0.42 separates clean-from-shadow.** `top₁=0.468 ≥ 0.42` (not STOP) and `top₂=0.395 < 0.42` (not BRANCH) → COHERENT → emit. The walk advances cleanly through the whole cycle.
- **Saturated real corpus → STOP at the tuned floor.** F946 measured the saturated single-M top₁ ≈ 0.37–0.40; with `noise_floor=0.42 > 0.40`, `top₁ < floor` → **STOP** (the honest "I don't know" at saturation), where the default 0.34 floor instead wandered.

## Two ways to get the clean walk (both native)
1. **Tune `noise_floor`** per corpus — set it between the saturated shadow and the clean signal. Quick, but corpus-specific.
2. **Chunk (F947) — the principled fix.** Source/community-tome routing drops each bundle under the F896 wall, so margins spread to ≈0.74 (top₂ far below any floor) and the **default** floor already gives clean COHERENT/STOP — no per-corpus tuning. The native method takes a single `M`, so chunking means one readout per routed tome (or per-tome substrates); combining native `next_token_coherence` with per-tome routing is the remaining integration.

## Honest scope
Grounded: the native walk runs end-to-end on `next_token_coherence` (chain default→wander, tuned→clean cyclic), real rc79. The saturated→STOP-at-tuned-floor is grounded by F946's measured saturated top₁ (< 0.42) + the classification logic (read from the rc79 source). The chunking-makes-the-default-floor-work claim rests on F947's measured 0.74 margins (not re-run here against the native method — that's the flagged integration). The wrapper→native swap is complete for the single-`M` path.

## Verdict / next
**Swap complete:** the full-beat etak recall (emit COHERENT / sample BRANCH / honest-stop STOP) runs end-to-end on native `next_token_coherence` — no recompute. A tuned `noise_floor` (or, principled, chunking) recovers the clean COHERENT cyclic walk; the saturated single-M honest-stops. The F940–F945 arc is now native, exact, trichotomy-aware. **Next:** wire **per-tome native coherence** (chunk F947 + one `next_token_coherence` per routed tome) so the **default** floor gives clean walks on a real corpus with no tuning — the last integration step.
