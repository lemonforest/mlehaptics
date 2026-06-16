# F784 — clump lensing DEMONSTRATED end-to-end, and IDF de-lensing WORKS — but only once the IDF is fixed to VANISH at df=N (the naive 1/(1+deg) leaves a lensing residue; that was the "fix the IDF subtraction" lesson)

**Date:** 2026-06-16 · **srmech:** 0.7.5rc165 · **Composes / VALIDATES:** F782 (clump lensing + IDF = mass-sheet/convergence subtraction — this proves it end-to-end on the demo graph), F758/F768/F777 (the hub/stopword domination + IDF/capacity-sizing — now mechanistically explained: IDF is de-lensing), F780/F779 (same graph) · **Discipline:** the first run shipped a broken de-lensing (caught by the numbers, corrected) — `[[feedback_computational_provenance_discipline]]` · **Provenance:** `R-RBS-LM-CLUMPLENS_hub_magnification_then_idf_de_lensing.py` · **User direction (2026-06-16):** "and fix the idf substraction too."

## The demo (falsifiable: does a hub lens, and does IDF de-lens?)
Metric = the **lensed (2-step) path**: `mediated(A,B) = Σ_{d≠A,B} idf(d)·w(A,d)·w(d,B)` (light bent THROUGH the intermediary). Headline = **separation** = mean mediated(related same-topic pairs) / mean mediated(unrelated cross-topic pairs); ≫1 = true structure intact, ≈1 = washed out. A synthetic **massive hub** (weight = max real edge = 7610, to all 32 words; a stopword stand-in) is the lens.

```
baseline (no hub, no idf)      separation  7.54x   true topical structure
+ massive hub (LENSED)         separation  1.05x   structure WASHED OUT (magnification floods the field)
baseline + IDF (ref, no hub)   separation 12.43x   idf-space reference
+ hub + IDF (DE-LENSED)        separation 12.43x   BIT-IDENTICAL to ref -> hub path FULLY subtracted
```
**Magnification** (query `tomato`, top intermediaries by retrieval mass): lensed → `[__HUB__, sauce, recipe, vegetable]` (the hub dominates every query); de-lensed → `[sauce, garlic, recipe, vegetable]` (hub gone, topical retrieval restored).

So both halves of F782 are demonstrated: **(magnification)** a massive clump mediates a spurious `A→HUB→B` path for every pair, collapsing related-vs-unrelated separation 7.5×→1.05× and dominating every query — this IS the F758/F768 stopword domination; **(de-lensing)** inverse-frequency weighting subtracts that lens, and the de-lensed graph is **bit-identical to the hub-free graph** (the lens is removed *exactly*, not merely reduced).

## The "fix the IDF subtraction" lesson (load-bearing)
The first run used **idf(d)=1/(1+deg(d))** and de-lensing FAILED (separation stayed 1.06×). Why: the hub enters the 2-step path as **weight² (≈58M)**; 1/(1+N)=1/33 only shrinks it to ≈1.76M, which still swamps the real topical mass (~0.1M). **A merely-small weight does not subtract a mass-sheet — the weight must VANISH for the node that touches everything.** The fix: **idf(d)=1−df(d)/N** (linear inverse-frequency; the standard **log(N/df)** has the same df=N→0 limit). At df=N (the hub touches all): idf = 0 exactly → the hub's `weight²` term is multiplied by 0 → the lensed path is *removed*, not dented. That is why de-lensed = hub-free exactly. **General principle: de-lensing = drive the all-touching (uniform-convergence) component's weight to ZERO; any IDF that doesn't reach 0 at df=N leaves a lensing residue.**

## What this settles
- **F782 validated end-to-end:** clump lensing is real on the co-occurrence graph (a hub magnifies + distorts), and **IDF / stopword-filtering IS the mass-sheet (convergence) subtraction that de-lenses it** — a *principled* reason for the F758/F777 capacity-sizing fix, not an ad-hoc hack. The hub/stopword domination (F758/F768) is named (magnification) and its cure derived (de-lensing).
- **Bonus:** IDF lifts separation **above** the no-hub baseline (7.54×→12.43×) — de-lensing also sharpens the *native* structure (it down-weights the moderately-frequent shared words that already blur cross-topic pairs), not just the injected hub.

## Honest scope
- Synthetic single-hub stress test on the 32-word seed graph — it demonstrates the *mechanism* and the *fix*, not a production retrieval system. Real corpora have many graded hubs (a convergence *field*, not one sheet); the principle (IDF→0 at df=N) holds, but the operating point (which IDF, how much) is a sweep (F777's capacity-sizing).
- Linear `1−df/N` chosen over `log(N/df)` to stay closed-form (no transcendental / series-convergence landmine); both share the df=N→0 limit that makes de-lensing exact. Stated as illustrative, not a tuned magic number.
- srmech-native co-occurrence (Class-L `text.cooccurrence_edges`); plain graph arithmetic for the 2-step path; no numpy, no `abs()`, no CAD; data outside the repo; CC-BY-SA. "Clump lensing" — the math runs in the data, not the universe (F782).

## Verdict
Clump lensing is **demonstrated end-to-end**: a massive hub collapses the related/unrelated separation 7.5×→1.05× (magnification) and dominates every query — the F758/F768 stopword domination, named. **IDF de-lensing WORKS** — once fixed so the all-touching node's weight **vanishes** (idf=1−df/N → 0 at df=N): the de-lensed graph is **bit-identical to the hub-free graph** (the mass-sheet subtracted exactly), and it even sharpens the native structure (7.54×→12.43×). The "fix the IDF subtraction" lesson: **de-lensing requires the uniform-convergence weight to reach zero, not just shrink** — the naive 1/(1+deg) left a residue because the lens enters quadratically. F782's "IDF = mass-sheet subtraction" is now proven, giving F758/F777's capacity-sizing a principled basis. (#224 part 2 delivered.)
