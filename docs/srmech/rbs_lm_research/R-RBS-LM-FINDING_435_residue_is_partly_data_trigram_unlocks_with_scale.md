# R-RBS-LM Finding 435 (data-scaling) — F434's prediction CONFIRMED: the 2-word-context saturation was DATA-bound, not a law. On a 759k-token corpus, the trigram's gain over the bigram climbs MONOTONICALLY with training data — from −7.5% (hurts, at 36k tokens) through break-even (~108k) to **+31.8% at 721k, still climbing**. So the transparency residue is *partly* the LLM's trillions-of-tokens data advantage (quantified); the irreducible part is the *representation* residue (long-range/compositional coherence no n-gram order can hold)

**Date:** 2026-06-06
**Arc:** RBS-LM / the end-to-end RBS-LM stage (F434 → **F435**); **measurement**
**Provenance:** `R-RBS-LM-END2_data_scaling_residue.py` (committed; seed 20260606; findings + 4 research notebooks)
**Composes:** **F434** (the end-to-end stage; *its pre-stated data-scaling prediction is what this tests*) · **F433** (the residue = DATA + REPRESENTATION — *the data half is now confirmed*) · **F172** (storage signature) · **F168** (perplexity from memory-depth) · standard n-gram / Witten-Bell smoothing (attested). Defensive / no-lineage.
**→ confirms F434's prediction; resolves the *data* half of F433's transparency residue; isolates the irreducible *representation* residue.**

---

## The prediction (F434, pre-stated)
F434 found the trigram saturated at 400k findings-only tokens (the 2-word context added nothing) and pre-stated: *"the saturation is DATA-bound, not a law — on a far larger corpus the trigram would help."* This tests it directly: a **fixed held-out set**, training on **increasing data** (findings + 4 big research notebooks = 758,762 tokens), tracking the trigram's gain over the bigram as the past grows.

## The result — the trigram unlocks with data (clean, monotonic)
| train tokens | bigram PPL | trigram PPL | trigram gain over bigram |
|---|---|---|---|
| 36k | 886 | 953 | **−7.5%** (data-starved — hurts) |
| 108k | 644 | 644 | +0.1% (break-even) |
| 288k | 461 | 396 | **+14.1%** |
| 505k | 382 | 289 | **+24.2%** |
| 721k | 337 | 230 | **+31.8%** (still climbing) |

**Monotonic.** The 2-word context goes from *hurting* (too sparse to estimate at 36k) to a **+31.8% perplexity win at 721k tokens, and the curve has not plateaued.** F434's prediction is confirmed: the saturation was **data-bound, not a law.**

## What it settles
- **The transparency residue is *partly* DATA — now quantified.** The LLM's advantage of seeing *trillions* of tokens is real and measurable: more past → longer transparent context helps progressively more. A legible n-gram model, given more data, recovers more of the coherence the black box holds. The residue is **not** "the black box does something inexplicable" — for the local/medium range it does something **data-hungry but legible.**
- **The irreducible part is the *representation* residue.** What no amount of data fixes is the n-gram's *structural* inability to hold **long-range / compositional** coherence (agreement across clauses, discourse structure, reference). That is the genuine LLM edge — and the genuine open problem (a *legible* long-range mechanism, not just more n-gram data). The two halves of F433's residue are now **separated**: data (closable, confirmed) vs representation (the real frontier).

## Methodology note (a confound I caught + corrected)
The first run held out the **tail** of the combined corpus (chess-notebook prose) while training prefixes started with findings — a **train/test domain mismatch** that made the trigram look bad at *every* data size (−15% to −24%, non-monotonic), conflating domain-shift with data-scale. Corrected with a **shuffled same-distribution split** (sentences shuffled, fixed held-out from the same mix). The corrected curve is the clean monotonic result above. *(Logged per the honest-correction discipline — the confounded run would have falsely read as "data doesn't help.")*

## Falsifiable form (pre-stated; not leaning — F394)
- **Still-climbing ≠ unbounded:** the +31.8% at 721k is on an unplateaued curve; it will keep rising with data but must eventually hit the *representation* ceiling (n-grams cannot encode unbounded context). The claim is "data unlocks medium-range context," not "n-grams reach the LLM."
- **Mixed-register corpus:** the combined corpus spans findings + 4 notebooks (heterogeneous technical prose); the absolute PPL and the exact slope are corpus-specific. The *monotonic-unlock-with-data* shape is the robust claim.
- **No 4-gram / no LLM number:** tested to trigram (2-word context); 4-gram+ would extend the curve. The residue-vs-LLM gap is bounded by *shape*, not a measured LLM PPL (no model run). Honest gaps, flagged.
- **Scope:** coherence *mechanism* + its data-scaling, not understanding (F43/F408 ceilings). Defensive / no-lineage.

## Verdict
**F434's prediction is confirmed:** the 2-word-context saturation was **data-bound, not a law.** On 759k tokens, the trigram's gain over the bigram climbs **monotonically with data — −7.5% (36k) → +31.8% (721k), still climbing.** This resolves the **data** half of F433's transparency residue (the LLM's trillions-of-tokens advantage is real, legible, and recoverable with more data) and isolates the irreducible **representation** half (long-range/compositional coherence beyond any n-gram order) as the genuine frontier — the *legible long-range mechanism* now the clear next seek. (A tail-held-out confound was caught and corrected to a shuffled split.) Favored, not privileged (F398); the unplateaued curve, mixed register, and missing 4-gram/LLM numbers are the honest fences.
