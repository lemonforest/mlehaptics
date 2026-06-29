# F963 — **arc opener: the recursive scale-invariant `compose`** (from F962). One operation — the position-keyed role-filler bind+bundle — is the n-gram at every scale; applied recursively it lifts `glyph → word → phrase → sentence`, and **one `recall_level` reads the next unit at any scale**. First demo runs end-to-end (sparse Klein-4 only): the **same `compose` + same `recall_level`** at the word scale gives `'april is' → 'the'` (correct), and at the phrase scale runs but mis-steps (`'april'` repeats in 4 phrases → crosstalk). **That mis-step *confirms* the arc's thesis:** scale-invariance means the *problems* recur too — so the F954/F955/F957/F961 fixes recur at every scale, as knobs on the one op.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Module:** `rbs_lm_recursive_compose.py` · **Opens from:** F962 (scale-invariant n-gram) · **Composes:** F961 (dynamic width `k`), F958 (phrase units), F955 (chunk/tomes), F957 (de-lensed routing), F959 (ASL unit-stream), F943 (collapse-margin readout) · **User direction (2026-06-26):** "let's try the recursive compose as a research arc to follow through."

## The module (`rbs_lm_recursive_compose.py`) — one op, every scale
- **`compose(cs, unit_hvs)`** — the scale-invariant n-gram: `bundle_odd([klein4_bind(pos_key(p), u) …])`. A 1-unit group is the identity.
- **`lift(cs, units, k)`** — chunk a `(hv,label)` stream into k-groups, `compose` each → next-level units. The dynamic width `k` (F961) is the only per-scale parameter.
- **`words_of(cs, text)`** — leaf: text → word units via srmech's `enc` (the byte→word role-filler bundle).
- **`recall_level(cs, units, k_ctx)`** — scale-invariant recall: one sparse Klein-4 memory `M` of (k_ctx-context → next), cleanup by integer match-count over the *distinct* units. **Same code at word / phrase / sentence.**
All sparse Klein-4 (`klein4_bind` / `bundle_odd` / `klein4_similarity`); **no dense matrix, no numpy, no abs/Counter** (honours F960 + the sparse directive).

## Grounded (rc79 demo, real-ish text)
```
WORD  scale (k_ctx=2): ctx ['april','is'] -> next = 'the'              (correct; 15 distinct word-units)
phrases (lift k=3)   : ['april is the','fourth month of','the year april','has thirty days', ...]
PHRASE scale (k_ctx=1): ctx ['april is the'] -> next phrase = 'march april comes'   (mis-step; 6 phrase-units)
```
The **same** `compose` + `recall_level` ran at both scales (scale-invariant, demonstrated). The word scale is clean; the phrase scale mis-steps because `'april'` occurs in 4 of the 6 phrases → the `compose` probe crosstalks — the F946/F958 repetition-saturation, now at the phrase scale.

## The thesis (why the mis-step is the point)
Scale-invariance cuts both ways: if the *operation* is the same at every scale, so are its *failure modes* — and so are its *fixes*. The phrase-scale crosstalk is the same wall as the word-scale frequency prior, so the same toolkit applies at every scale as **knobs on the one op**:
- **width** — dynamic `k` (F961): wider context sharpens the collapse, at any scale;
- **units** — what you feed it (words / phrases / ASL-gloss, F958/F959): drop/absorb the repeaters at the source;
- **chunk** — bound the per-scale memory under the F896 wall via sparse `recursive_cut` (F955/F960);
- **read** — the collapse-margin trichotomy / honest-stop (F943/F945), per scale.
None of these is scale-specific code; they are parameters of `compose` / `recall_level`.

## Arc roadmap (to follow through)
1. **Per-scale tuning** — apply dynamic-`k` (F961) + de-lensed units (F957/F958/F959) + sparse `recursive_cut` chunking (F955/F960) at *each* level; verify the word-scale clean recall extends to phrase + sentence.
2. **Native coherence per scale** — either feed composed HVs to a custom margin read, or extend `next_token_coherence` to accept an external unit-HV set (the §80-adjacent ask) so the trichotomy is native at every scale.
3. **Unit-stream choice** — function-word-delimited phrases (F958) and/or ASL-gloss units (F959) as the content stream; measure which recurses cleanest.
4. **Real-corpus level-by-level** — run `glyph→word→phrase→sentence` on a real text with the sparse tomes; read the live coherence trace at each scale.

## Honest scope
Grounded: the module runs; the same `compose`/`recall_level` work at word + phrase scales; word-scale recall correct; phrase-scale mis-steps (repetition crosstalk — expected, the same wall one scale up). No claim of a tuned multi-scale recall yet — this is the **arc opener**: the one operation + the scale-invariant recall + the demo + the roadmap. The fixes are known (F954/F955/F957/F961) and are scale-invariant by the F962 thesis; applying them per-scale is the arc.

## Verdict / next
**Arc open + first demo running.** One `compose` (the role-filler n-gram) + one `recall_level`, sparse, recursing `glyph→word→phrase→sentence`; word-scale recall correct; phrase-scale mis-step confirms the saturation (and the fixes) recur scale-invariantly. **Next (step 1):** per-scale dynamic-`k` + de-lensed units + sparse-`recursive_cut` chunking — make the phrase scale as clean as the word scale by turning the *same* knobs one level up.
