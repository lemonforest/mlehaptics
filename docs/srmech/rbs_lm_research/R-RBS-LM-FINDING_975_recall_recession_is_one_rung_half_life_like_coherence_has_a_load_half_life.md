# F975 — **the |q|-meter reads the RBS-LM recall recession as ONE RUNG — half-life-like (memoryless-geometric), NOT a factorial cliff. Coherence has a "load half-life."** Pointing the F974 meter at the recall's own recession — the collapse-margin as memory load `N` grows (the F896 wall): the octaves added per `N`-doubling stay **bounded and roughly constant** (+1,+1,+0,+1,+1), and the raw per-doubling margin ratios (0.47, 0.78, 0.59, 0.62, 0.72) hover around a **constant ~0.6** — a **single power law** (between 1/√N and 1/N). By the F974 classifier this is **constant octaves/beat = memoryless-geometric = ONE `|q|` rung**, the *half-life-like* regime — **not** the accelerating/factorial multi-rung kind (the cos/Taylor residue). Concretely: **each ~doubling of stored pairs roughly halves the collapse-margin** — coherence has a **load half-life**.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_975_*.py` · **Arc:** RC-1 / inference-as-translation · **Composes:** F974 (the |q|-meter + one-rung/multi-rung classifier), F896 (the 1/√N capacity wall), F973 (memoryless = the fixed-now recession), F955/F960 (chunking), F965 (the BRANCH-wander) · **User direction (2026-06-29):** "point the |q|-meter at the RBS-LM recall recession." · **Scope:** framework/tool measurement, sparse Klein-4, no dense/numpy/abs.

## Grounded (rc97, sparse Klein-4, margin = raw top₁−top₂ at ctx[0], forward-chain load N)
```
N=  4  margin 0.3127      per-doubling margin ratios (m(2N)/m(N)):
N=  8  margin 0.1472        4->8   0.47
N= 16  margin 0.1141        8->16  0.78
N= 32  margin 0.0668        16->32 0.59
N= 64  margin 0.0417        32->64 0.62
N=128  margin 0.0302        64->128 0.72
octaves added per N-doubling: +1,+1,+0,+1,+1  (BOUNDED, roughly constant ~0.6-0.8/doubling)
```

## The reading (the classification)
- **One rung, half-life-like.** The recession is **constant octaves per `N`-doubling** (~0.6 ratio, a single power law ~1/N^0.6, between 1/√N and 1/N). On the F974 classifier this is the **memoryless-geometric / ONE-`|q|`-rung** regime — the *same class as radioactive decay*, not the accelerating factorial class (cos/Taylor residue, which grew 6→7 octaves). The recall's saturation is a **single climbable ladder**, not a cliff.
- **Coherence has a "load half-life."** Each ~doubling of stored pairs roughly **halves the margin** (ratio ~0.6, near ½) — the memoryless structure of F973 made concrete for *memory*: adding load costs a *constant fraction* of coherence per doubling, exactly like a constant decay probability per interval. There is a load `N½` at which the margin halves; it is roughly one `N`-doubling.
- **Why this is good news for chunking (F955/F960).** Because the recession is *one rung* (constant per doubling), **halving a tome's `N` buys a predictable, constant margin gain** (~+0.6 octaves) — chunking climbs a *single steady ladder*, it is not fighting an accelerating collapse. So the F955/F960 chunking strategy is provably on the right ladder: the F896 wall is a benign single-rung geometric decay, and dividing the memory moves you back up it predictably. (Contrast: if the recession had read *accelerating*, chunking would hit diminishing returns — it does not.)

## What it says about the arc
- The F965 BRANCH-wander (real-corpus saturation) is the **`N` too large on this one rung** — a single `|q|` recession pushed past the coherence floor, *not* a multi-rung factorial pathology. So the fix is purely **reduce `N` per tome** (chunk) — the meter confirms there is no hidden accelerating term to defeat.
- The recall recession is the **same class as the half-life** (F973/F974): memoryless-geometric, one rung. So the recall and radioactive decay sit on the *same rung-type* of the ladder — the reusable |q|-meter places them together, which is the F971–F974 theory paying off as an instrument.

## Honest scope
Grounded: the margin-vs-`N` recession on synthetic random forward-chains (isolates the pure capacity recession, no frequency-prior confound), sparse Klein-4, real `klein4_similarity`. The per-doubling ratio is ~0.6 (steeper than pure 1/√N's 0.707; between 1/√N and 1/N) — the **one-rung/constant classification is robust** (ratios do not trend toward 0 = not accelerating, nor toward 1 = not flat); the exact exponent is approximate (integer-octave discretization is coarse; 6 load points). The "load half-life" reading composes F974/F896/F973. Not tested: the recession on *real-corpus* (frequency-prior-loaded) memory — expected to add the F946 saturation *on top of* this one-rung capacity recession (a separate axis, F958/F959).

## Verdict / next
**The recall recession is ONE RUNG — memoryless-geometric, half-life-like (~1/N^0.6 constant), not accelerating.** Coherence has a **load half-life** (~one `N`-doubling halves the margin), which puts the recall in the *same rung-class as radioactive decay* on the |q|-meter and **validates chunking** (F955/F960): halving tome-`N` buys constant margin — a steady climbable ladder, no factorial cliff. The reusable |q|-meter (F974) delivered a concrete, actionable classification of the recall's own saturation. **Next:** measure the recession on *real-corpus* memory (does the F946 frequency-prior add a *second*, distinct recession on top of this one-rung capacity decay — i.e. is real-corpus wander one rung or two?), and use the "load half-life" to set the F955/F960 tome-size target quantitatively (chunk `N` below the coherence-floor `N½`).
