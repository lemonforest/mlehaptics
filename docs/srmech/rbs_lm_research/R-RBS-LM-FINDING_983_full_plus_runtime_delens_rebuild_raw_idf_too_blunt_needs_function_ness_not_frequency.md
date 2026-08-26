# F983 — honest rebuild (full memory + runtime de-lens + etak-deeper): the **architecture is right (nothing dropped, de-lens at read-time, shapes intact) but raw-frequency IDF is too blunt a de-lens — it buries frequent *content* words (the topic word) along with the function words.** Rebuilding F980/F981 the F982 way — **full** bounded tome (every token kept) + **runtime** `sim·idf` de-lens + etak-deeper — the target `april` was **not recovered** (raw read `days→30`; de-lensed read `days→apart`; etak-deeper k=3 `→apart`). Diagnosis: `april` is the article's **topic word (high freq)**, so the `1/√freq` de-lens **down-weighted it** exactly as it down-weights `the/of` — raw frequency does not distinguish *frequent-because-function* from *frequent-because-topic*. The correct runtime de-lens is **measured function-ness** (F768 aboutness-gate), not raw frequency. Function words remained in the tome + recallable (the F982 discipline held).

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_983_*.py` · **Composes / depends on:** F982 (de-lens at runtime — honored), F980/F981 (the write-time-shortcut versions being corrected), F768 (aboutness-gate = *measured function-ness*, task #221 — the actual metric needed), F947/F957/F960 (de-lensed community-tome chunking — the capacity axis), F782 (IDF as *a* de-lens — shown here too blunt for topic words), `[[feedback_dont_pre_commit_spike_query_operators]]` (null counts) · **User direction (2026-06-29):** "rebuild full + runtime de-lens and re-run etak-deeper." · **Scope:** framework/tool; sparse Klein-4; no dense/numpy/abs.

## Grounded (rc97, bounded tome 180 tokens / 69 vocab, ALL kept; target `april`, 5 contexts)
```
raw FAST [days]                 -> 30       (frequency prior)
RUNTIME sim*idf FAST [days]     -> apart    correct=no   (idf down-weighted 'april' -- it's high-freq TOPIC word)
ETAK-DEEPER runtime-delens k=2  -> 245      correct=no
ETAK-DEEPER runtime-delens k=3  -> apart    correct=no
shapes intact: the/of/in/and STILL in the tome (nothing dropped)  <- the F982 discipline held
```

## The lesson (why the null is diagnostic)
1. **The architecture was correct.** Full memory (nothing dropped), de-lens at read-time, function words present and recallable — the F982 discipline is honored, no doctoring. That part is right and must stay.
2. **Raw-frequency IDF is the wrong de-lens metric.** `1/√freq` treats *all* frequent atoms alike — but frequency has two sources: **function-ness** (`the/of`, should be down-weighted) and **topicality** (`april` in an april article, should NOT). Raw IDF conflates them, so it buried the topic word. This is exactly why **F768 (task #221)** specifies **measured function-ness** (aboutness) as the de-lens metric, not raw frequency — F983 is the concrete demonstration that the distinction is load-bearing.
3. **The capacity axis still needs real chunking.** The bounded tome here was an arbitrary 180-token window; margins stayed small. The proper chunk is a **de-lensed community-tome** (F947/F957/F960 — cut on IDF/function-ness-weighted edges so hubs don't dominate the partition, tomes bounded under F896), not a raw window.

## What it hands to the arc (the real dependencies, now isolated)
The honest rebuild converges the recall arc's two remaining prerequisites, both already on the board:
- **Runtime de-lens must use function-ness (F768 / #221), not raw frequency** — so `april` (topic, high-freq) survives while `the` (function, high-freq) is down-weighted. The measured-function-ness gate is the correct read-time weight (and the §80 native per-atom weight should carry *that*, not raw idf).
- **Chunking must be de-lensed community-tomes (F947/F957/F960)**, not arbitrary windows — the capacity axis.
Only *after* both are in place does the full+runtime-de-lens+etak-deeper pipeline get a fair test. Until then this is an honest null: the correct architecture with a too-blunt de-lens metric.

## Honest scope
Grounded: the full+runtime-de-lens+etak rebuild did not recover `april`; the cause is raw-IDF down-weighting the high-freq topic word; function words remained (F982 held). Per `[[feedback_dont_pre_commit_spike_query_operators]]` I did **not** tune the target/metric until it "worked" — the null is the finding, and it cleanly identifies **F768 measured-function-ness** as the required de-lens metric (raw frequency is insufficient) and **de-lensed community-tomes** as the required chunk. No fluency claim. The etak-deeper mechanism itself is unrefuted (F979/F980/F981); what failed is the *de-lens metric* feeding it on the full memory.

## Verdict / next
**Honest null, diagnostic:** the F982 architecture (full memory + runtime de-lens + etak-deeper, nothing dropped) is correct, but **raw-frequency IDF is too blunt a de-lens** — it buries frequent *topic* words (`april`) with the function words, so recovery failed. The runtime de-lens must be **measured function-ness (F768/#221)**, and the chunk must be **de-lensed community-tomes (F947/F957/F960)**. **Next:** build the F768 aboutness-gate (measured function-ness as the read-time weight, the §80 native carrier), chunk into de-lensed community-tomes, *then* re-run the full + runtime-function-ness-de-lens + etak-deeper pipeline for the fair test.
