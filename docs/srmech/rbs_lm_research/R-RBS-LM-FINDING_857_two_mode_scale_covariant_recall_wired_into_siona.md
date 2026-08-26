# F857 — Two-mode + scale-covariant recall WIRED into Siona's recall surface (`siona/bridge.py`), with the F853-corrected mode boundary, tested end-to-end on live srmech 0.8.2 + the v082 instrument. `route()` (ABOUT mode: de-lensed Klein-4 content resonance → which tome) ranks the source article **#1**; `two_mode_recall()` (COARSE de-lensed route → FINE full-metric walk) **routes correctly AND reproduces exactly** (k\*=6, exact=True). Items 1 (two-mode) + 2 (scale-covariant) of the build-consequences are now in the package, corrected; items 3 (chiral cosets) + 4 (coherence-gated co-evolution) are documented as design (need the chirality-native encoder F844–F848, not in the loose store).

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` · **Provenance:** `docs/srmech/siona/siona/bridge.py` (+`route`/`two_mode_recall`/`_delens_bundle`) + `/tmp/test_twomode.py` on `simplewiki_rawbody_instrument_v082` · **Composes:** F853 + its §CORRECTION (the mode boundary), F851 (scale-covariant / coherence-DoF), F849/F850 (mass = de-lens target), F838/F805 (the walk), F848/F778 (cosets/clumps — design), [[feedback_relationship_lm_ideas_not_code_from_gen1]] · **User direction (2026-06-18):** "those new things now too please" (act on the PHYSICS §6 build-consequences).

## What was wired (items 1 + 2, F853-corrected)
- **`route(query_tokens, candidates, mass)`** — ABOUT mode: de-lens (drop the high-frequency mass + short tokens), bundle the content tokens to one Klein-4 HV, rank candidates by `klein4_similarity`. "Which tome is this about." The COARSE pass.
- **`two_mode_recall(query, candidates, instrument, index, mass)`** — SCALE-COVARIANT: de-lensed `route` (coarse, which tome) → full-metric `recall`/`walk` (fine, reproduce within). Returns `{routed_to, ranking, recall}`.
- **The mode boundary is documented in code** (F853 §CORRECTION): WALK/sequence → full metric (`walk`/`recall` AND per-context walk-position routing, incl. the F840 vote — de-lensing it HURTS, 94→69); ABOUT/meaning → de-lensed (`route` — de-lensing HELPS, 80→90). Discriminator = content/meaning query vs sequence/walk op, NOT routing-vs-generation.

## Test (live 0.8.2, v082 instrument, 8-article candidate set)
Source `Aquaculture`, query = a content-word sample (not the verbatim sequence):
- **`route` de-lensed**: `Aquaculture` **0.384** (#1) vs distractors 0.261 — clean margin; full-token also #1 (0.378) but tighter margin (de-lens sharpens, F853 direction).
- **`two_mode_recall`**: `routed_to='Aquaculture'` (correct), `recall.exact=True`, k\*=6 — coarse route lands the tome, fine walk reproduces it exactly.

## Items 3 + 4 — documented as design, not half-built (honest scope)
- **Chiral cosets + route/scope** (F848, "clump don't divide" F778): need the chirality-native encoder (F844–F848) which is NOT in the loose RBS-HDC store yet — recorded in the `bridge.py` mode-boundary block as the next encoding work, not stubbed.
- **Coherence-gated co-evolution ONLY** (F851): naive plastic recall runs away (76→42); recorded as a guardrail (any walk-reshapes-store step must gate on confidence), not a feature added now.

## Verdict / next
The corrected two-mode + scale-covariant recall is live in Siona's package surface and verified (route #1; two-mode routes+reproduces exact). Corpus-scale `route` needs a candidate pre-filter (F778 clump / inverted index) rather than scanning 271k — the next build step. Items 3/4 await the chirality-native encoder. Evaluate by groundedness; no single fixed match target (F851).
