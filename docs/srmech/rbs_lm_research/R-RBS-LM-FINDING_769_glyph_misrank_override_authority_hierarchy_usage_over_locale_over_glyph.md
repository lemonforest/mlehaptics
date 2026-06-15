# F769 — the glyph mis-rank fix: an AUTHORITY hierarchy for Pass-1 comprehension — observed USAGE > LOCALE > glyph+edit

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F767 (the mis-rank lever it closes — "an edit-distance-ranked resolver is the precision-preserving lever"), F765 (Pass-1 comprehension / the edit-distance guard), F762 (the abstract glyph resolver, now the *lowest* authority), F759 (the running-context RBS-HDC object = the "observed usage" signal), F761 (the language kernel where the locale layer lives) · **User direction (2026-06-15):** "glyph-mis-ranks should have some sort of override in the language kernel, ie en_US vs en_GB … also if user has spelled it correct before, and in context memory, then it's maybe more likely to route correctly making localities not the authority when user input suggests another."

## The problem (from F767)
Pass-1 comprehension resolved a typo by the **glyph-top** candidate, which mis-ranks: `tomatto → tomatillo` (glyph sim 0.89) instead of `tomato` (edit-1). F767 showed the edit gate DECLINED these (no misbind) but couldn't CORRECT them. The user's fix: resolve by an **authority hierarchy**, with glyph similarity the *lowest* authority.

## What landed — `_resolve_canonical(w, context_words)`, three tiers in precedence
1. **OBSERVED USAGE (highest).** A word the user already USED (the running context, F759) or TAUGHT (the learned store), edit-close + routable, wins. The user's own spelling is the authority — *"localities are not the authority when the user's input suggests another."*
2. **LOCALE.** A known en_GB/en_US spelling-convention variant (`LOCALE_CANON` seed in the language kernel) → the store-canonical spelling. A locality authority, but overridden by (1).
3. **GLYPH + EDIT-RANK (lowest).** The abstract glyph candidates, but pick the **edit-closest** among the glyph-plausible (not the glyph-top), edit-gated (F765/F767 — no hallucinated comprehension). This is the F767 lever, realized.

The resolved `how` (`usage` / `locale` / `glyph`) shows in the `[understood: …]` line.

## Verified live (rc155 server)
```
what is a tomatto?                                   → [understood: tomatto→tomato (glyph)]   ← F767 mis-rank FIXED (was tomatillo)
[tomato establ. in prior turn] tell me about tomatto → [understood: tomatto→tomato (usage)]    ← user's usage is the authority
```
The edit-rank tier alone fixes `tomatto→tomato`; the usage tier confirms the user's established spelling overrides everything below it.

## Honest finding on the LOCALE tier — currently DORMANT (and why)
All 20 seed `LOCALE_CANON` pairs are **both-routable** on this genome: simplewiki carries BOTH spellings (`colour` AND `color`, `centre` AND `center`, `organise` AND `organize` …), so a locale variant routes directly to its own content and **never reaches the locale tier** (which only fires for an *unroutable* variant). So on a both-spelling corpus the locale-mapping is **moot for routing**. The locale layer's real value is the two cases this corpus doesn't exercise:
- **single-locale corpora/genomes** — a strictly-en_US source where en_GB variants ARE unroutable → locale maps them in;
- **output-spelling consistency** — rendering the ANSWER in the user's locale spelling even when both route (an output-layer use, not input-resolution).
The mechanism is correct and in place; this corpus just doesn't trigger it. (A genuinely-missing variant resolves correctly via `_resolve_canonical` — the tier is reachable, not dead.)

## Honest scope
- **Usage tier** uses the running-context words + learned store; it requires the user's word to be *routable* and edit-close. The deeper case the user named — honor the user's en_GB spelling as THEIR canonical even when it differs from the store key (route via store-content, keep their spelling) — is a display/routing split, not yet built (queued).
- **Locale seed is 20 pairs**, GB→US direction, hardcoded; a full bidirectional, configurable, locale-tagged inventory is the data scale-up (same class as the broad-dictionary scale-up in F766).
- **Edit-rank** lifts F767's ~46% typo-recall by re-ranking within the already-gated set (precision-preserving); the exact new recall is a follow-on re-run of the HALLUPROBE.
- srmech-native (Klein-4 similarity for glyph-plausibility); edit distance pure-Python (no `abs()`); no new genome chromosome (schema unchanged).

## Verdict
The glyph mis-rank is fixed by an **authority hierarchy** (F769): observed **USAGE** (the user's own context/learned spelling) > **LOCALE** (en_GB/en_US canonical) > **glyph+EDIT-rank** (edit-closest plausible candidate, not the glyph-top). Verified live: `tomatto→tomato` now resolves correctly via edit-rank, and via the usage tier when the user established it — "localities are not the authority when the user's input suggests another," realized. The locale tier is correct but dormant on this both-spelling corpus; it serves single-locale corpora and output-spelling. Closes the F767 mis-rank lever.
