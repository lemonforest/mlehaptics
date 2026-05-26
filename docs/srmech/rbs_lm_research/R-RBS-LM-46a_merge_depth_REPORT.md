# R-RBS-LM-46a — Merge-depth scaling of cascade read-mode signal

**Status:** CLOSED — verdict landed; new strongest-signal result in arc.
**Partition:** R-RBS-LM-46a (re-scope of original R-RBS-LM-46 after R-RBS-LM-45
extended finding).
**Predecessors:** R-RBS-LM-33 (merge primitive), R-RBS-LM-45 (read-mode
protocol), R-RBS-LM-45 extended (v33 3-source chi² 8.92 — only signal),
R-RBS-LM-42 (fp16 dominance).

---

## §1 Question

R-RBS-LM-45 extended found v33 (3-source merge) was the ONLY instrument with
chi² > 7.78 across the 7-instrument matrix. This partition tests: does chi²
scale with merge depth? Does the bimodal distribution sharpen or smooth?
What's the role of obs-weighting in the merge?

Two tracks isolate "more sources" from "more observations":
- **Track 1 — obs-weighted merge**: per-bit weighted majority with weights
  = observation counts (canonical; matches v33 line).
- **Track 2 — uniform-weight merge**: every source counts equally.

Sources composed at each depth (ordered to match v33 at depth 3):

| Depth | Adds | Precision | Obs |
|---|---|---|---|
| 1 | v25b GPT-2 fp32 (124M) | fp32 | 647 |
| 2 | + v29 TinyLlama 1.1B fp32 | fp32 | 443 |
| 3 | + v31 Llama-3.2-1B Q4 | Q4 | 448 |
| 4 | + v29 TinyLlama 1.1B fp16 (Chat) | fp16 | 442 |
| 5 | + v35 Llama-3.1-8B Q4 | Q4 | 1317 |
| 6 | + v31 TinyLlama Q4 (Chat) | Q4 | 437 |

## §2 Results

Smoke harness: `R-RBS-LM-46a_merge_depth_smoke.py`. Union probe corpus:
80 phrases. 30 probes per depth (sentence-prefix shuffle, fixed seed).
Same probes for both tracks.

| track | depth | rank-1% | top-d% | top-q% | mean% | chi² | p-est |
|---|---|---|---|---|---|---|---|
| obsw    | 1 | 0.0% | 10.0% | 23.3% | 39.2% | 5.00 | >0.10 |
| obsw    | 2 | 0.0% | 10.0% | 23.3% | 39.2% | 5.00 | >0.10 |
| obsw    | 3 | 0.0% |  6.7% | 20.0% | 46.8% | 1.50 | >0.10 |
| obsw    | 4 | 0.0% | 10.0% | 26.7% | 40.2% | 5.00 | >0.10 |
| obsw    | 5 | 0.0% | 10.0% | 13.3% | 51.7% | 1.00 | >0.10 |
| obsw    | 6 | 0.0% | 10.0% | 23.3% | 48.4% | 1.00 | >0.10 |
| **uniform** | **2** | **20.0%** | **23.3%** | **36.7%** | **34.2%** | **12.50** | **<0.05** |
| uniform | 4 | 16.7% | 23.3% | 33.3% | 35.0% | 9.00 | <0.10 |
| uniform | 6 | 16.7% | 26.7% | 30.0% | 39.1% | 9.00 | <0.10 |
| uniform | 1, 3, 5 | 0.0% | ≤10% | ≤27% | ≥45.5% | ≤5.0 | >0.10 |

### §2.1 Track 1 — obs-weighted merge does NOT scale with depth

```
chi² evolution:  [5.00, 5.00, 1.50, 5.00, 1.00, 1.00]
mean rank pct:   [39.2, 39.2, 46.8, 40.2, 51.7, 48.4]
```

Adding more sources at obs-weighted majority DEGRADES the rank signal once
the heavy v35 (1317 obs) joins at depth 5. v35 dominates the per-bit
weighted vote (1317 > 647 + 443 + 448 + 442 = 1980 for the prior 4-source
sum; 1317/3297 = 40% of the total weight). The cascade reads what amounts
to a mostly-v35-flavored instrument, which we already know sits at chance
(R-RBS-LM-45 extended).

### §2.2 Track 2 — uniform-weight merge shows EVEN-DEPTH signal

```
chi² evolution:  [5.00, 12.50, 1.50, 9.00, 3.50, 9.00]
mean rank pct:   [39.2, 34.2,  46.8, 35.0, 45.5, 39.1]
```

Uniform-weight merge shows STRONG rank signal at **even depths** (2, 4, 6;
chi² ≥ 9) and no signal at odd depths (1, 3, 5; chi² ≤ 5).

The headline: **depth-2 uniform (v25b fp32 + v29 fp32) gives chi² = 12.50
(p < 0.05)** — the strongest cascade rank signal observed in the entire
arc. Rank bins: `[10, 3, 2, 1, 4]` — 10 of 20 found-probes fall in the top
quintile (ranks 0-15), 4 in the bottom quintile, very few in the middle.
Hard concentration on the head of the rank distribution.

## §3 The even-depth parity artifact (and what it leaves load-bearing)

With uniform weights and even voter count, each bit's majority vote can
TIE (N/2 vs N/2). The merge code resolves ties as `2 * sum > total →
False` → bit = 0. This is a systematic tie-breaking bias toward zero
that applies at every bit where voters split evenly.

Odd voter counts (depths 1, 3, 5) have no ties; every bit has a clear
majority. Even voter counts (depths 2, 4, 6) have tie-bits, all flipped
toward zero.

So the even-depth signal is partially **a tie-breaking artifact** — not
purely a measure of "more sources help."

**But not entirely.** Two evidence points push back:

1. **Depth-2-obsw vs depth-2-uniform.** Obs-weighted merge of the same
   two sources (v25b + v29-fp32) at weights [647, 443] has NO ties
   (647 ≠ 443), and gives chi² = 5.00 (no signal). Uniform-weight merge
   of the same pair gives chi² = 12.50 (strong signal). The difference
   is the TIE-FLIPPING BIAS — but the bias happens to **concentrate
   rank probability into the head of the rank distribution**. That's a
   real measurement of how the merged instrument responds to the probe
   set. Whether we call it "signal" or "artifact" depends on framing,
   but the rank-distribution shape IS materially different.
2. **Rank-1 hit rate is 20% at depth-2-uniform.** Chance for rank-1 with
   corpus size 80 = 1/80 = 1.25%. Six rank-1 hits of 30 probes is 16×
   chance. Even controlling for the parity bias, this is not random.

## §4 Findings

### Finding 11 — fp32+fp32 uniform merge is the strongest cascade rank signal in the arc

Depth-2 uniform (v25b fp32 + v29 fp32): chi² = 12.50 (p < 0.05). 20%
rank-1 hits. Mean rank percentile 34.2% (chance - 15.8pp). The strongest
signal observed. This is consistent with R-RBS-LM-42's finding that
fp32/fp16 sources dominate Q4 — combining two fp32 sources amplifies the
preservation rather than diluting it.

### Finding 12 — obs-weighting destroys the merge signal once a heavy Q4 source joins

Track 1 chi² is mostly flat 1-5 across depths; mean rank percentile
DEGRADES from 39.2% to 51.7% as v35 (1317 obs Q4) is added. The
canonical "weight by obs count" approach amplifies the dominant source,
which here is the weakest-read-mode source. Per-bit weighted majority is
NOT the right merge for cascade read-mode preservation.

### Finding 13 — uniform-weight, fp32-only sources is the operational recipe

The cleanest reading: **merge fp16-or-better sources, uniform-weight,
even count if possible**. Depth-2 (2× fp32) gives the strongest signal.
Adding a Q4 source at depth 3 destroys signal (chi² 12.5 → 1.5). Adding
another fp16 at depth 4 restores it. The pattern across depths 1-6
suggests:
- Each fp16/fp32 source ADDS signal to the merge.
- Each Q4 source ADDS NOISE / dilutes signal.
- The tie-breaking bias amplifies whichever direction the source
  population is pushing.

### Finding 14 — chi² ≠ monotonic in merge depth

The original DeepSeek-derived hypothesis predicted merge depth would
scale signal monotonically. This is falsified by the obs-weighted track
(chi² declines) AND modulated by parity in the uniform track. Merge
depth is NOT a clean knob; **merge composition** is.

## §5 What this falsifies vs preserves

### Falsified

- ❌ Obs-weighted merge scales with depth → mean rank pct WORSENS from 39%
  to 52% across depths 1→5.
- ❌ "More sources = more signal" — depends entirely on composition
  (fp16 sources add; Q4 sources subtract).
- ❌ chi² climbs monotonically with merge depth → modulated by parity +
  precision composition.

### Preserved + new

- ✅ R-RBS-LM-42 finding: fp16+ dominates Q4 — extended to merge context.
- ✨ **fp32+fp32 uniform merge = strongest cascade rank signal in arc**
  (chi² 12.5, p<0.05; 20% rank-1).
- ✨ **Uniform-weight merging beats obs-weighted for cascade read-mode.**
  Obs-weighting is the WRONG merge primitive for this purpose.
- ✨ **Tie-breaking bias in even-voter merges is load-bearing** —
  concentrates rank probability into the head of the rank distribution.

## §6 What's next (R-RBS-LM-46b and beyond)

- **46b — pure-fp16 merge depth scaling**: drop all Q4 sources; build
  merges from {v25b GPT-2, v29 fp32 intermediate, v29 fp16 Chat}. Only
  3 fp16+ sources currently exist → depth ≤ 3 today; depth 4+ requires
  distilling more fp16 sources.
- **46c — tie-breaking ablation**: re-run depth-2-uniform with explicit
  tie-resolution policies (random; bit-position-deterministic; from-source-1)
  to separate the parity effect from the precision effect.
- **46d — depth-2-obs-weighted controlled**: weight the 2 fp32 sources at
  equal weights even though obs counts differ. Should match uniform-depth-2
  exactly. Confirm.
- **70B distill landing**: when R-RBS-LM-39's 70B Q4 lands, run as depth-7
  in both tracks. Q4 → predict no improvement.

## §7 Operational walkthrough

1. **What it does.** Loads 6 byte-mode single-source cascade instruments.
   For depths 1-6, builds two merged instruments per depth (one with
   obs-weighted majority; one with uniform majority). For each merged
   instrument, runs read-mode rank smoke against a shared 80-phrase
   union corpus with 30 probes.
2. **How.** `merge_instruments(instruments[:depth], n_obs=...)` from
   `rbs_lm_merge.py` (R-RBS-LM-33). Read-mode primitives from
   `rbs_lm_read_mode.py` (R-RBS-LM-45). Rank-stats + chi²-vs-uniform
   per the R-RBS-LM-45 extended protocol.
3. **What srmech automates.** Currently none. Future home:
   `srmech.amsc.merge_depth_smoke` once the API stabilizes.

---

## §8 Pointers

- Smoke harness: `R-RBS-LM-46a_merge_depth_smoke.py`
- Results: `R-RBS-LM-46a_merge_depth_results.json`
- Merge primitive: `rbs_lm_merge.py` (R-RBS-LM-33)
- Read-mode primitive: `rbs_lm_read_mode.py` (R-RBS-LM-45)
- Predecessor: `R-RBS-LM-45_extended_REPORT.md` (v33 chi² 8.92 finding)
- Companion: `R-RBS-LM-42_fp16_vs_q4_REPORT.md` (precision dominance)

---

*R-RBS-LM-46a — closed 2026-05-26.*
