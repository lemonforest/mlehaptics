# F984 — the **F768 aboutness-gate = DOCUMENT-frequency, applied as a ONE-SIDED suppression** — the correct runtime de-lens (fixes F983). Two parts, both grounded. **(1) The metric:** function-ness is **document/tome frequency**, not term frequency. Measured on 40 real tomes: `the/of/in` are in **40/40** tomes (function); `april(6) / month(3) / calendars(2) / flowers(2)` are in **few** (topical) — *even though* `april` (term-freq 237) is as term-frequent as function words. **Document frequency cleanly separates function from topic where term frequency (F983) cannot.** **(2) The application:** a full `1/√df` reweight *over-corrects* (it boosted rare **noise** `kentucky`, df=1, over `month`). The fix is a **one-sided gate**: content (low df) **unchanged** (weight 1), function (df ≥ threshold) **suppressed** ∝ tome-spread. Grounded: a content-dominated read `[fourth]` is **unchanged** by the gate (no harm, no noise-boost); a function-dominated read `[is]` goes from raw `[that, the, april]` to gated **`[april, 16, bc]`** — function words suppressed, content surfaces.

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_984_*.py` · **Realizes / composes:** F768 (aboutness-gate = measured function-ness, task #221 — now built), F983 (the null: term-freq IDF too blunt — identified the need), F982 (de-lens at runtime, full memory), F782 (IDF-de-lensing — now the *correct* IDF: **document** not term, and **one-sided**), F957/F959 (de-lensing axis), §80 (the native per-atom weight should carry *this*) · **User direction (2026-07-02):** "let's go next move" (build the F768 aboutness-gate F983 said was required). · **Scope:** framework/tool; sparse Klein-4; no dense/numpy/abs.

## Grounded (rc97, 40 real tomes)
```
(metric) word     term-freq  doc-freq(/40)   verdict
         the        2750       40             FUNCTION (every tome)
         of         1385       40             FUNCTION
         in         1138       40             FUNCTION
         april       237        6             topical (few tomes)   <- term-frequent but LOW doc-freq
         month        22        3             topical
         calendars     2        2             topical
   => DOCUMENT frequency separates function (df~N) from topic (df small); TERM frequency does not (april~the)

(gate)  content read [fourth]:  raw [occurring,apple,overthrown]  GATED [occurring,apple,overthrown]  (UNCHANGED -- no harm)
        function read [is]:     raw [that,the,april] (func top)   GATED [april,16,bc]                 (function suppressed, content surfaces)
```

## The correction chain (why this is the fix)
- **F982:** de-lens at *runtime* on the *full* memory (never write-time strip). ✓ honored here.
- **F983:** raw **term**-frequency IDF is too blunt — it buries frequent *topic* words (`april`). Identified the need for measured function-ness.
- **F984 (this):** function-ness = **document** frequency (tome-spread) — the classic-IDF signal I got wrong in F982/F983 by using *term* frequency. `april` is in few tomes → high aboutness → **not** suppressed; `the` is in all tomes → function → suppressed. And apply it **one-sided** (suppress function, don't boost rare content) so it can't over-correct into rare noise.

## The gate (the deliverable)
```
docf[w]      = # tomes containing w          (document frequency = the aboutness signal)
FUNC_THRESH  = ~0.6 * N_tomes                 (in >=60% of tomes => function)
gate(w)      = 1.0                    if docf[w] <  FUNC_THRESH     (content/topic: UNCHANGED)
             = FUNC_THRESH / docf[w]   if docf[w] >= FUNC_THRESH     (function: suppressed prop. to spread, <=1)
score(w)     = klein4_similarity(probe, w) * gate(w)                 (read-time; memory untouched, F982)
```
One-sided (never > 1) → it suppresses the function-word frequency prior **without** up-weighting rare noise. Content-dominated reads are untouched (no false correction); function-dominated reads clear (content surfaces). This is the runtime de-lens the recall arc needed (F982), with the metric F983 required, and it is what the §80 native per-atom weight should carry.

## Honest scope
Grounded: doc-freq vs term-freq separation on 40 real tomes; the one-sided gate leaves a content read unchanged and surfaces content on a function-dominated read. The threshold (0.6·N) and suppression shape (`thresh/df`) are first-cut (tunable; the aboutness signal itself — high df = function — is the robust part). Demonstrated on a single-tome memory (article-0); the full recall re-run (chunked de-lensed tomes + this gate + etak-deeper) is the next integration — F984 delivers the *metric+application*, not yet the end-to-end recovery re-run. Composes F768/F983/F982/F782/§80.

## Verdict / next
**Built: the aboutness-gate = document-frequency, one-sided suppression** — the correct runtime de-lens (function-ness = tome-spread, not term frequency; suppress function words, don't boost rare noise). It fixes F983's null at the metric level: content-dominated reads unharmed, function-dominated reads surface content. **Next:** (i) wire the gate into the recall's routing + emission (read-time `sim·gate`, the §80 native weight carrying doc-freq); (ii) use the same doc-freq gate to **weight the community-tome cut edges** (F947/F957/F960 — hubs = high-doc-freq function words, so the gate de-lenses the *partition* too, one metric for both axes); (iii) re-run the full + gate + etak-deeper pipeline end-to-end (the fair F983 re-test).
