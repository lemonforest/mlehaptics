# F788 — finished F745's documented scale path: the FULL-COVERAGE lead-paragraph abstract tier (216,563 abstracts) is built + wired, so "tell me about / explain X" gives multi-sentence prose while "what is X" stays a crisp one-line definition

**Date:** 2026-06-16 · **srmech:** 0.7.5rc165 · **Composes / finishes:** F745 (the wiki abstract chromosome — built + proven on a **58-article cut**, with the full ingest named as "the documented scale path" — *this is that scale path, run*), F760 (the lead-sentence gloss tier — kept for crisp "what is X"), F763 (the elaboration depth signal — "tell me more" = depth long → abstract), F787 (the SAME operator-leak class — `explain`/`describe` leaked as topics, now stoplisted) · **User direction (2026-06-16):** "[richer prose] — I thought we had already done this. we did the research for it and said we were going to do it. let's check." · **Provenance:** `R-RBS-LM-WIKIABSTRACT_…py` (builder) + `R-RBS-LM-SIONAGENEPOOL_…py` (wiring)

## The trail-check verdict (the user was right)
F745 (2026-06-14) **built and proved** the multi-sentence wiki abstract chromosome — but only ran the **58-article proof cut** (fantasy creatures, for the "dragons" test); its verdict explicitly named the rest: *"the full enwiki-abstracts bulk-ingest … is the documented scale path."* The full-coverage tier shipped was the **lead-SENTENCE gloss** (216k, one sentence, F760). So the *capability* existed; the *full ingest we said we'd do* was never run — which is exactly why "what is ketchup" returned a single sentence. **Now done.**

## What was built + wired
- **`R-RBS-LM-WIKIABSTRACT`** — the lead-PARAGRAPH abstract store: `title → first ≤3 clean sentences`, same extractor + markup-understanding (F764) + MPR attestation as the gloss builder. **240,881 articles → 216,563 abstracts in 80 s → `simplewiki_abstracts.json` (63.5 MB, CC-BY-SA, outside the repo).**
- **Siona wiring (3 tiers, by question shape):**
  - **"what is X"** → the crisp **lead sentence** (gloss, F760) — a definition stays one line, by design.
  - **"tell me about / explain / describe X"** (`ABOUT_RE`) or **"tell me more"** (depth=long, F763) → the fuller **abstract** (≤3 sentences).
  - **deep-kernel terms** (MFO / srmech / dict-en) → the etak-walk still fires when the subject has **no** wiki abstract; and an open "tell me about X" whose subject **has** an abstract **skips the terse dict-en seed** (so "tell me about computer" → the wiki abstract "A computer is a machine that uses electronics to input, process, store…", not the 3-word seed "an electronic machine").
- **Operator-leak fix (F787 class):** `explain`/`describe`/`overview` were being counted as topics (they have co-occurrence entries) → "explain tomato" mis-declined. Stoplisted (they're ABOUT-frame operators, F770).

## Tested (fresh instance)
| query | tier | result |
|---|---|---|
| `what is ketchup` | gloss | 1 sentence (crisp) |
| `tell me about ketchup` | abstract | 3 sentences (…flavour to food… burgers, fries, hotdogs…) |
| `explain tomato` | abstract | 3 sentences (no decline) |
| `tell me about computer` | abstract | full abstract (not the dict seed) |
| `what is computer` | deep kernel | crisp |
| `what else is in ketchup besides tomatoes` | contents | vinegar/salt list (F787 intact) |
| `what is MFO about chirality?` | deep kernel | MFO walk preserved |

This **directly answers the "single sentence" report**: the single sentence was the *definition* tier; richer asks now get multi-sentence prose, and the deep-kernel / contents / definition tiers are all preserved.

## Honest scope
- The abstract is the **lead PARAGRAPH (≤3 sentences), not the full article body** — bounded, attested, CC-BY-SA. Deeper than a sentence, still not the whole article (storing full bodies is a much larger store; not needed for "tell me about").
- Minor extraction noise on a few articles (e.g. "volcano" caught a "Volcanoes / plural" disambiguation header) — same light thumb/px guard as the gloss extractor; most are clean.
- **Not yet redeployed:** the running server (port 8000) still has the old code + no abstract store loaded; needs a by-port restart (on direction) to serve it.
- srmech-native text extraction (markup grammar F764); no `abs`, no CAD; the 63.5 MB store lives OUTSIDE the repo (only the builder script + wiring + this finding are committed).

## Verdict
F745's "documented scale path" is **run**: a full-coverage (216,563-entry) lead-paragraph abstract tier is built + wired so Siona answers **"tell me about / explain X" with multi-sentence prose** while keeping **"what is X" a crisp one-line definition** — the deep-kernel walk, the F787 contents list, and the definition tier all preserved, and the `explain`/`describe` operator-leak fixed along the way. The user's "I thought we did this" was right: we'd proved it (58 articles) and planned the ingest; the ingest is now done. Redeploy (by-port) to serve it live.
