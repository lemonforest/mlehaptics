# F958 — methodology correction (user): **yes byte/glyph, no I was word-level — and phrases dissolve the frequency prior at the source.** I *am* encoding through the **byte/glyph language-agnostic kernel** (`ContextSubstrate.enc` defaults to `byteglyph` / `encode_word_byteglyph` — the "vanuatu" / strip-English-privilege C1 object, R-RBS-LM-25). But I was working at the **word level** (k=2 *words*), **not phrases** — and that is why F946→F957 kept hitting the frequency prior. Measured: **word atoms have a few dominators** (`april` 230, `the` 180) while **3-word phrase atoms have none** (max 6) — ~38× flatter. At the phrase level the recall gets **real content**: `'april apr is' → 'the fourth month'` (the actual next phrase, function words *absorbed* into the phrase) where the word level wandered into `it~ in~ to~ of~`. The frequency-prior wall was a **word-level artifact**; phrases dissolve it structurally.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_958_*.py` · **Composes / corrects:** F957 (word-level routing/emission wander), F946 (the frequency prior), F921 (encode senses — byte/glyph = sense #2), R-RBS-LM-25 (byte/glyph strip-English-privilege), F166/F168 (the sentence layer — phrases are the missing intermediate), UPSTREAM §80 (now reframed) · **User direction (2026-06-26):** "are you abstracting first from the byte/glyph vanuatu language kernel? working in phrases before sentences?"

## Grounded (rc79, simplewiki 3000-token slice)
```
byte/glyph kernel: ContextSubstrate.enc default = 'byteglyph' (encode_word_byteglyph) -> YES, language-agnostic
WORD atoms : 938 distinct, top = april(230), the(180), day(106), of(105), in(93)   -> a few dominate
PHRASE atoms (3-word): 941 distinct, top = "same day of"(6), "the week as"(6)       -> none dominate
max-freq atom: word=230 vs phrase=6  (~38x flatter -> the frequency prior dissolves)
phrase recall: 'april apr is' -> 'the fourth month'  (the ACTUAL next phrase; vs word-level it~/in~/of~ wander)
```

## What you caught
- **Right kernel, wrong granularity.** The encoding *is* byte/glyph (sense #2 of F921, language-agnostic), so that layer is correct. But the **recall unit was the word**, and at the word level a handful of function words carry almost all the frequency mass (`april` 230, `the` 180) → they dominate the raw-sim candidate ranking regardless of context → the F946/F957 wander.
- **Phrases absorb the function words.** A 3-word phrase (`"the fourth month"`, `"of the year"`) binds `the`/`of` *into* a distinctive content atom that occurs ~once. So no atom dominates (max freq 6), and the recall ranks by *content*, not frequency — it returns `'the fourth month'`, the real next phrase.
- **The frequency prior was a word-level artifact.** F946 (single-M → `an/on/in/of`), F956/F957 (routing + within-tome wander) were all the same wall — and it exists **because the atom was the word**. Move the atom up to the phrase and the wall is largely gone *before* any de-lensing.

## The missing layer in the hierarchy
The substrate-native build is **bytes/glyphs → words → phrases → sentences**, and I had skipped straight from words to sentence-generation (F166/F168). **"Phrases before sentences" is the right bottom-up order** — and it is not just linguistically right, it is *what makes the recall work*: phrases are the granularity at which content out-weighs frequency.

## Reframing UPSTREAM §80
§80 (emission-layer IDF de-lensing of the candidate score) is the **word-level patch** — down-weight the function words *after* they dominate. The **phrase abstraction is the structural fix** — work at the granularity where they don't dominate in the first place. Both are valid; phrases are cleaner (no per-atom weighting needed). §80 stays useful for any residual word-level use; the primary path forward is **phrase atoms**.

## Honest scope
Grounded: byte/glyph is the active encoder; word-vs-phrase atom frequency (230 vs 6); phrase recall returns the actual next phrase on step 1. **Residual:** the phrase walk still oscillates after step 1 (the 12-phrase bundle is mildly saturated + default-floor BRANCH) — the *same* F954/F955 chunk/floor tuning, now operating on **contentful** atoms (a much better starting point than function-word wander). Phrase *segmentation* here is a fixed 3-gram (a crude proxy); real phrase boundaries (noun/verb phrases, or function-word-delimited chunks) are the refinement.

## Verdict / next
**You're right:** byte/glyph yes, but the recall must be **phrase-level, not word-level** — phrases dissolve the frequency prior at the source (max atom freq 6 vs 230) and recall real content (`'the fourth month'`) where words wandered. The hierarchy is **glyph → word → phrase → sentence**, and phrases are the missing layer; §80 was a word-level patch for a problem the phrase layer removes. **Next:** redo the recall on **phrase atoms** (better segmentation than fixed 3-grams — function-word-delimited or noun/verb-phrase chunks), then chunk/floor-tune (F954/F955) on those contentful atoms — *then* build sentences from phrases.
