# F766 — depth by MEANING, not keywords: an intent-word dictionary + definition-overlap anchors (Pass-2 op on the understood form)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F763 (the keyword depth read — now the crisp FAST-PATH), F765 (the two-pass split: this is the Pass-2 meaning op on the *understood* form, its natural home), F761/F764 (genome language-layer chromosomes — `dict-intent` is a new one), F119/F529 (two-tier: exact + general), the prior exchange ("use language definitions of words to know when to be more descript instead of keyword-like things" + "form-similarity is the wrong tool for meaning") · **User direction (2026-06-15):** "ready for this one now."

## What it does
The F763 elaboration read was a **keyword regex** — a "keyword-like thing." F766 makes the depth decision come from **meaning**:
- **An intent-word DICTIONARY** (`INTENT_DICT`, ~28 words → one-line definitions), stored in the genome as a **`dict-intent` chromosome** (same shape as `dict-en`; introspectable, genome-native).
- **Concept ANCHORS built from a few SEED definitions** — `long` = a Klein-4 bundle of the content-word leaves across {elaborate, detail, thorough, comprehensive} definitions; `short` = {brief, concise, short, summary}. (Uses `_leaf` per content word = **meaning** overlap, NOT the glyph `_word_hv` = form — the placement the prior exchange settled: form-similarity is right for Pass-1 comprehension, wrong for meaning.)
- **Every other dictionary entry SELF-CLASSIFIES** by definition-overlap to the anchors — so a synonym *we never hand-listed* resolves by meaning. Adding `word + definition` auto-places it; no hand-tagged long/short. This is the substrate-native difference from a keyword list.

It runs as a **two-tier read** (F119/F529): (1) the F763 **keyword fast-path** (crisp, phrase-aware — "tell me more", "in detail"); (2) the **meaning anchor** over any prompt word in the dictionary. A frame-channel **negation flip** is in both tiers ("do not be brief" → long).

## Verified (offline classification + live)
Per-word anchor affinity (Δ = long_sim − short_sim), **none of these are in the keyword regex** — they self-classify by definition meaning:
```
exhaustive Δ+0.141 → long    succinct Δ−0.234 → short    terse Δ−0.438 → short
extensive  Δ+0.094 → long    overview Δ−0.141 → short    simple Δ−0.156 → short
elaborate  Δ+0.156 → long(seed)   brief Δ−0.312 → short(seed)
```
Live on the rc155 server:
```
give an exhaustive answer about a tomato   → detail long (meaning:exhaustive)  → definition + 8 directed + 12 assoc
a succinct answer: what is a tomato        → detail short (meaning:succinct)    → bare definition
tell me more about a tomato                → detail long (keyword)              → full treatment
what is a tomato? do not be brief          → detail long (keyword(neg))         → full treatment
```
The `how` (`keyword` / `keyword(neg)` / `meaning:<word>`) is shown in the input-ride parse, so the path is legible.

## Honest scope
- **The dictionary is finite (28 words).** Open-vocabulary intent (ANY synonym, not just dictionary entries) needs a broad word→definition dictionary (WordNet / Wiktionary / GCIDE) as a side-store — the real scale-up. The mechanism is proven; the coverage scales with the dictionary.
- **A few genuinely-ambiguous definitions land `normal`** rather than mis-classify (`verbose` Δ−0.016: "more words" pulls short, "detail" pulls long; `deepen` Δ+0.031; `condense` Δ+0.016). Honest abstention beats a wrong vote; tightening those defs (or seeds) is a refinement.
- **`dict-intent` definition words become walkable genome surface** — a query whose content words coincide with definition words (e.g. "answer") could mis-walk into the chromosome. Mitigated by stoplisting scaffolding words (answer/question/response/reply); a cleaner fix is to exclude `dict-intent` from the *content* walk graph (it's a meta dictionary, not a content kernel) — queued.
- **Negation is shallow** (a negator within 3 tokens flips polarity) — handles "do not be brief" / "not too detailed", not nested/scoped negation.
- srmech-native (Class-M `klein4_bundle_accumulate`/`similarity`; no `abs()`, no `Counter`); DEPTH_MARGIN is a type-B calibration floor (measured separation gap), not a magic number.

## Verdict
The depth read now decides by **meaning**: an intent-word dictionary (genome-native `dict-intent`) + definition-overlap anchors, so synonyms we never enumerated (`exhaustive`, `succinct`, `terse`) self-classify — "use definitions, not keyword-like things," realized. It sits cleanly as a **Pass-2 op on the understood form** (F765), hybrid with the F763 keyword fast-path, with frame-channel negation. Live on the rc155 server. The open-vocabulary scale-up (a broad dictionary) is the next inch; the mechanism is proven on the seed dictionary.
