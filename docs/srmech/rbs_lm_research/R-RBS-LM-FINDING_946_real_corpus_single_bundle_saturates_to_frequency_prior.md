# F946 (research note, real corpus) — at real scale the **single bundle saturates to the frequency prior**, and the **collapse-margin trichotomy correctly diagnoses it** (it does *not* falsely emit). Learning a simplewiki slice (2500 tokens → **818 vocab, 1500 context→next pairs in ONE bundle**), *every* context — including the nonsense `['xyzzy','qwerty']` — returns the **same high-frequency function words** (`an, on, in, of`) at sim **~0.37**, floor **~0.31**, **margin ~0.00**. The bundle is hard against the F896 1/√N wall, so it returns the **unigram frequency prior**, not the context-conditioned next. The trichotomy (F945) reads this exactly right: `top₁` only ~0.06 above the floor with margin ~0 → **STOP / not-coherent**, never a confident emit. The honest "I don't know" fires at the saturation point — which is the whole value.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RBS-LM / Siona · **Probe:** `R-RBS-LM-FINDING_946_*.py` · **Composes:** F945 (the coherence trichotomy), F943/F944 (collapse-margin readout), F896 (the 1/√N wall), F768 (aboutness-gate / function-word dominance), F778 (community-tome routing — the fix, F947) · **User direction (2026-06-26):** "let's try it on a real corpus … we might surface research notes."

## Measured (simplewiki, 2500-token slice)
```
vocab=818; learned=1500 pairs (ONE bundle)
ctx ['the','fourth']   floor 0.31  top [(an,0.39),(to,0.39),(as,0.38)]   margin 0.00  -> top1 0.08 above floor
ctx ['is','the']       floor 0.32  top [(on,0.40),(ii,0.39),(in,0.39)]   margin 0.00  -> top1 0.08 above floor
ctx ['between','march'] floor 0.31  top [(an,0.38),(on,0.37),(in,0.37)]  margin 0.01  -> top1 0.07 above floor
ctx ['xyzzy','qwerty'] floor 0.30  top [(an,0.37),(on,0.36),(in,0.36)]   margin 0.01  -> top1 0.07 above floor  (NONSENSE input, same answer)
```

## The two readings
1. **Saturation = collapse to the frequency prior.** With 1500 pairs in one bundle, the tokens that appear in the *most* edges (the function words `an/on/in/of`) carry the *most* crosstalk, so they win *every* query regardless of context — even nonsense. The single bundle has degraded from a context model to a **unigram frequency table**. This is the F896 wall at real scale, in its concrete failure shape.
2. **The trichotomy is honest at the failure point.** It does **not** confidently emit `an` — it reads `top₁` ~0.07 above floor with margin ~0 as **not-coherent** (STOP). The calibrated "I don't know" (F943) holds exactly where it matters: a saturated memory *says* it's saturated instead of hallucinating fluent function words. (This is the recall-level form of the F934 honest-`OPEN`.)

## Research note (what surfaced)
The function-word domination is **two failures, not one** — and they need different fixes:
- **capacity** (too many edges in one bundle, F896) → fixed by **chunking into community-tomes** (F778/F944/F945; tested next in F947);
- **frequency prior** (function words are frequent in *every* community, so they leak crosstalk even into small tomes) → needs the **F768 aboutness-gate** (down-weight by function-ness / IDF-style de-lensing, F782), *orthogonal* to chunking.
So chunking alone may not fully restore context at real scale — the frequency prior is a second axis. That is the concrete prediction F947 (spectral routing) tests.

## Honest scope
Measured on a 2500-token slice (real simplewiki), single bundle, real `RBSLMInferenceSubstrate` + recomputed raw-sim margin. The saturation is the expected F896 wall; the value here is that the **trichotomy diagnoses it honestly** (no false emit) and that it **separates the capacity axis from the frequency-prior axis** (F896 vs F768). Spectral community-tome routing (does chunking recover context, and does the frequency prior still leak?) = F947.

## Verdict / next
**Surfaced:** at real scale the single bundle collapses to the unigram frequency prior (function words), and the collapse-margin trichotomy correctly calls it not-coherent rather than emitting — the honest "I don't know" works at the failure point. The function-word dominance is **capacity (F896) ⊕ frequency-prior (F768)**, two axes. **Next (F947):** spectral community-tome routing — does chunking restore context-resolution, and does the frequency prior still leak through?
