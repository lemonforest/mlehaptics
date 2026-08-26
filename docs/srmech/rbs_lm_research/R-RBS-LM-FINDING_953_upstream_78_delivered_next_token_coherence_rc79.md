# F953 — UPSTREAM §78 **DELIVERED + VERIFIED** (srmech rc79): `next_token_coherence` ships the raw collapse-margin + the F945 trichotomy. srmech landed our §78 ask as a new method **`RBSLMInferenceSubstrate.next_token_coherence(context, *, branch_band, noise_band, noise_floor, top_k) -> CoherenceReadout`**, reusing the same probe as `next_token_distribution` but exposing the **raw Class-M sims as exact rationals before the softmax** — so the collapse-margin is not flattened. The docstring cites **§78 / F944 / F945** by name.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 (TestPyPI) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_953_*.py` · **Verifies:** UPSTREAM §78 (the ask), F943/F944/F945 (the readout + trichotomy + the softmax-flattening bug) · **User direction (2026-06-26):** "check latest test.pypi.org srmech for upstream deliverable request and update upstream notes md if it's been delivered, after testing."

## Tested (rc79, chain `a b c d e`, ctx `['a','b']`)
```
verdict           : BRANCH
collapse_margin   : 0.0724   (RAW pre-softmax = the §78 ask; vs the softmax-flattened 0.006 — F944 confirmed)
noise_floor       : 0.3400   (matches the F947 empirical floor 0.34)
top1_floor_gap    : 0.1277
candidates_topk   : ['c','d','a','e','b']
raw_sims_topk     : [0.468, 0.395, 0.316, 0.316, 0.253]   (raw Class-M sims exposed before softmax)
branch_candidates : ['c','d']            margin type: Q (exact rational, not float)
nonsense ctx      : STOP  (correct)
```

`CoherenceReadout` fields delivered = **exactly the §78 ask**: `verdict` (COHERENT/BRANCH/STOP trichotomy), `collapse_margin` (raw), `top1_floor_gap`, `noise_floor`, `candidates_topk`, `raw_sims_topk`, `branch_candidates`. Two independent convergences confirm it is *our* ask: the raw margin (0.0724) ≠ the softmax-flattened prob-margin (0.006, **F944**), and the default `noise_floor` (0.34) **matches the F947 empirical floor**.

## Status / next
**§78 CLOSED** (UPSTREAM_NOTES §79). The F941–F945 recall wrapper can drop its recompute-from-`sub.M`/`sub.ctx`/`sub.vocab_vecs` and call `next_token_coherence` directly — the recall-level honest-`OPEN` / coherence readout is now native, exact, and trichotomy-aware. **Next:** swap the wrapper to the native method; then the full-beat etak recall (F940–F945) runs on native coherence end-to-end.
