# F961 — the n-gram **is** dynamic (no srmech fix needed) — and **more context sharpens the collapse**. `operating_k = 1, 2, 3, 4` all work in `RBSLMInferenceSubstrate`; the user's concern ("3 was supposed to work too") is resolved — k=3 works fine. The striking part: the **collapse-margin rises with k** — k=2 → 0.072 (BRANCH), **k=3 → 0.205 (COHERENT)**, k=4 → 0.277 (COHERENT). So the BRANCH-wander of F954/F957 was partly a **low-k artifact** (I defaulted to k=2). The "dynamic n-gram" the user described — *typically 1–2, escalate to 3 when needed* — is a real **resolution mechanism**: when the now branches (low margin at k=2), escalate the context window to k=3 → more context disambiguates → COHERENT. This is **orthogonal** to the function-word handlings (drop/absorb/down-weight, F959).

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_961_*.py` · **Composes:** F954/F957 (the BRANCH-wander — partly low-k), F943 (collapse-margin), F959 (the three function-word handlings), R-RBS-LM-112/117 (variable-length support) · **User direction (2026-06-26):** "n-gram was supposed to be dynamic — typically 1 or 2, but 3 should work too; if not, fix/clarify for srmech."

## Grounded (rc79, chain `a b c d e`)
```
operating_k=1 -> top=a margin=0.001 verdict=BRANCH    (too little context -> ambiguous)
operating_k=2 -> top=c margin=0.072 verdict=BRANCH
operating_k=3 -> top=d margin=0.205 verdict=COHERENT  <- 3 works AND resolves the branch
operating_k=4 -> top=e margin=0.277 verdict=COHERENT
=> margin RISES monotonically with k: more context = sharper collapse
```

## Two distinct "n-grams" (clarification for srmech)
- **context n-gram** = `operating_k` (how many prior tokens condition the next). **Dynamic, verified 1–4.** This is the one that sharpens the collapse.
- **atom n-gram** = the phrase-chunking granularity (F958 — 1/2/3-word *units* as the token stream). Also free to vary (it's just how you build the token list). Both senses support dynamic n; **no srmech change required for either** — `operating_k` is a per-instrument parameter and the atom stream is the caller's.

## The resolution it adds
**Escalate-k**: run k=2 by default; when `next_token_coherence` returns a low margin / BRANCH, **re-query at k=3** (more context). The margin monotonicity (0.072 → 0.205 → 0.277) means a deeper context disambiguates the now — a context-depth resolution that is **orthogonal** to the function-word-prior handlings (you can escalate-k *and* drop/absorb/down-weight the function words). It is also cheap (just a larger window on the same M).

## Honest scope
Grounded on the clean chain (margin monotonic in k). On real English the function-word prior still applies at every k (escalate-k disambiguates *content* ambiguity, not the function-word saturation — that needs F958/F959/§80). So escalate-k is one of several composable resolutions, not a replacement. The atom-n-gram (phrase) sense is the F958 chunking choice (segmentation), separate from `operating_k`.

## Verdict
**n-gram is dynamic — no srmech fix needed** (`operating_k` 1–4 verified), and **more context sharpens the collapse** (margin rises with k), so escalate-k (k=2→3 when the now branches) is a real, orthogonal resolution. The F954/F957 BRANCH-wander was partly my k=2 default. **Composes with** the function-word handlings (drop/absorb/down-weight) — they address different axes (function-word saturation vs content-ambiguity context-depth).
