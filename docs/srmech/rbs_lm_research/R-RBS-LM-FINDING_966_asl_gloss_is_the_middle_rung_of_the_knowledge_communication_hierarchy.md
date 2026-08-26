# F966 — **ASL-gloss is the middle rung** of the knowledge→communication hierarchy (inference-as-translation step 2). On the 74 parallel English↔ASL-gloss pairs (`asl_corpus.json`), the **content-dense ASL-gloss form recalls more coherently than the English surface** — mean collapse-margin **0.009 vs 0.005** (~2×) — and does it in **41% fewer tokens** (307 vs 519 for the same 74 sentences). So the hierarchy sits in the predicted order:

```
English surface   0.005   function-word linear projection (most lossy)   [F964]
ASL-gloss         0.009   content-dense communication (the MIDDLE)       [F966]
chunked knowledge 0.077   bonded relationship-tomes (most coherent)      [F965]
```

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RC-1 / inference-as-translation · **Probe:** in `R-RBS-LM-FINDING_967_*.py` (shared run) · **Composes:** F964/F965 (the hierarchy + baselines), F959 (ASL drops function words), F609 (meaning-class ASL selects better than English), R-RBS-LM-27 (`asl_corpus.json`, 74 pairs) · **User direction (2026-06-29):** "ASL first then written last."

## Reading
ASL-gloss is the **content-dense communicated form**: it drops the articles/copula (`"I beat the eggs in the bowl"` → `[fs:I] /beat-egg/ /EGG/+ /BOWL/`), so its atoms are more distinctive → higher coherence (0.009 > 0.005) in fewer tokens (content density, F959). It sits **between** the bonded knowledge (chunked, 0.077 — most coherent) and the English surface (0.005 — the function-word projection). This is the hierarchy's middle rung *measured*: **ASL-first is genuinely more coherent than English-first** (confirming F609), and inference walking *down* knowledge → ASL → English loses coherence at each step (each adds surface).

## Honest scope
Grounded: gloss 0.009 > English 0.005 on the 74 parallel pairs, real Klein-4 + native coherence. Both are still small/BRANCH (74 sentences, unchunked) — the ASL edge is modest (~2×, consistent with F959's ~25% function-word drop = partial de-lensing), not the ~13× that *chunking* the knowledge gave (F965). So ASL is the middle rung by direction, on a small parallel set; chunking the gloss (F960) + the composed cascade (F964 step 3) remain. The gloss surface is the F282 expert's call (a Deaf source verifies the signs).

## Verdict / next
**Middle rung confirmed:** ASL-gloss (0.009) sits above the English surface (0.005) and below chunked knowledge (0.077) — the knowledge→communication hierarchy in order. **Next:** F964 step 3 (chain knowledge-tome → gloss → English as the recursive compose, F963) — and the F967 forcing/direction shape, which is what makes each rung's recall *stop* cleanly.
