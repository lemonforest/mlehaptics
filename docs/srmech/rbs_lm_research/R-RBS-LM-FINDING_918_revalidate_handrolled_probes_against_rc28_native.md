# F918 — REVALIDATION: our hand-rolled F879–F912 probes ARE the rc28 native surface (exact match), and the L1/L2/L3 ladder F900/F901 said to rebuild on C1 IS rebuilt. `klein4_compose` reproduces F901's C1 band (0.745=0.745), `encode_word_byteglyph` reproduces F908's byte/glyph morphology (cat/cot 0.560, walk/walked 0.707), `encode_bigram_l1` is now graceful (0.562, C1) instead of the old chained-bind collapse (~0.25), and `scale_signature` ships the F900/F901 coherence introspection. The arc's findings are now the shipped, attested ops — the hand-rolls can be dropped (don't-hand-roll discipline).

**Date:** 2026-06-22 · **srmech:** 0.9.0rc28 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_918_revalidate_handrolled_probes_against_rc28_native.py` · **Composes / closes:** F901 (C1 compose → `klein4_compose`), F899/F900/F908 (byte/glyph word → `encode_word_byteglyph`), F900/F901 (the ladder + scale_signature), F917 (the rc spec), §70/§71 · **User direction (2026-06-22):** "do we have any probes that need revalidated or that we can revalidate with our new native code?"

## What rc28 shipped (all F917-spec ops present)
`hdc.klein4_compose(parts)`, `substrate.encode_word_byteglyph(word, *, D, sector)`, `substrate.scale_signature(parts)`, and the rebuilt `encode_bigram_l1`/`encode_skeleton_l2`/`encode_sentence_l3`.

## Revalidation (rc28 native vs our hand-rolled)
| native op | measured (rc28) | hand-rolled (ours) | match |
|---|---|---|---|
| `klein4_compose` 1-part-change band (byte→word, n=8) | **0.745** | F901 = 0.745 | ✅ exact (it IS our C1 compose) |
| `encode_word_byteglyph` morphology | cat/cot **0.560**, walk/walked **0.707**, cat/dog 0.252 | F908 = 0.56/0.71/~0.25 | ✅ exact (it IS our word_k4) |
| `encode_bigram_l1` 1-part-change | **0.562** (graceful) | F901: chained-bind collapsed ~0.25 | ✅ **REBUILT on C1** |
| `scale_signature` | shipped `(parts)` | F900/F901 coherence metric | ✅ native |

## What this means for our probes
- **Reproduced + supersedable by native:** F901 (C1) → `klein4_compose`; F899/F900/F908 (byte/glyph word) → `encode_word_byteglyph`; F900/F901 (scale_signature) → `scale_signature`; F900/F901 (the ladder) → `encode_bigram_l1`/`skeleton_l2`/`sentence_l3` (now C1, graded). The hand-rolls can be dropped — call the attested ops.
- **Superseded by the default flip:** F899 ("the packaged RBS-LM is word-hash") is now historical — rc28's `enc_mode='byteglyph'` default closes that gap; F900's byteglyph injection is now the native default (redundant).
- **Unaffected (already native, enc-independent):** the chunked-M route/stream (F879/F895/F896/F898 use `klein4_chunk_*` + hand-rolled byte_k4 = byte/glyph already), the octonion (`cd_mult`) chemistry probes (F903–F916), and the sedenion address / Siona `page_grid` (addressing doesn't touch `enc`). All consistent with rc28 — verified surfaces intact (§71).

## Verdict
The whole arc (F899–F916) is now **the shipped native surface**: `klein4_compose` = C1, `encode_word_byteglyph` = the byte/glyph word, `scale_signature` = the coherence metric, the L1/L2/L3 ladder rebuilt on C1 (the F900/F901 core ask, **confirmed landed**). Our hand-rolled probes reproduce the native numbers exactly (0.745, 0.560, 0.707), so they revalidate clean and can now use the attested ops. The one residual (the `sim_k4_batch`→float hot-path, §71) is the only un-native piece. **Next:** optionally refactor the F901/F908 probes to call `klein4_compose`/`encode_word_byteglyph`/`scale_signature` directly (drop the hand-rolls) — a tidy-up, not a correctness need; the findings stand as-verified.
