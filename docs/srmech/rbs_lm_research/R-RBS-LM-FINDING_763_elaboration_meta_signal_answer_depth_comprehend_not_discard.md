# F763 — ELABORATION understanding: "tell me more / briefly" is a meta-signal Siona COMPREHENDS (an answer-depth control), not content to discard

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F762 (the markup-correction principle — *comprehend* a meta-signal, never strip/discard it), F760 (the definition + steer-gated relation tiers being depth-controlled), F757/F754 (the directed + assoc relational tiers), F752/F753 (the input-ride parse: TOPIC + FRAME channels), F584 (the related material is the bounded relation/assoc store) · **User direction (2026-06-15):** "Siona should understand 'tell me more / longer / more detail' as a meta-signal (like markup: comprehend it, don't discard it), controlling answer depth."

## The principle (markup, one layer up)
F762 corrected the instinct to *strip* markup: a meta-signal Siona needs is **comprehended, not discarded**. A request for a longer/shorter answer is the same kind of meta-signal — it is not the *topic*, it is an instruction *about the answer*. So Siona now **parses it, consumes it, and acts on it** (controls depth), exactly as markup should be parsed (understood) rather than deleted.

## What landed
- **`ELABORATION_RE`** — a DEPTH axis ORTHOGONAL to `intent` (the F752 frame channel = question TYPE). It classifies the raw prompt into:
  - **`long`** — "tell me more", "in detail", "elaborate", "go deeper", "expand on", "at length", "explain further", "comprehensive", …
  - **`short`** — "briefly", "in short", "tl;dr", "one line", "concise(ly)", "summarize", "the short answer", …
  - **`normal`** — no cue (the standard answer).
- **`_depth(pl)`** reads the signal; a knob map turns depth into answer-shaping parameters:

  | depth | k (directed edges) | k (assoc neighbours) | walk steps | attach extra |
  |-------|----|----|----|----|
  | short  | 3  | 4  | 2 | **no** (bare core) |
  | normal | 6  | 8  | 4 | yes |
  | long   | 12 | 12 | 6 | yes + **both** directed AND assoc |

  Threaded through every read-out tier: the definition/gloss tier, the wiki-abstract tier, the directed-relation story walk, and the assoc tier.
- **The meta-words are CONSUMED, not routed** (the markup discipline made concrete): `ELABORATION_WORDS` (detail/briefly/deeper/elaborate/…) are stripped from BOTH the TOPIC channel and the STEER channel once `_depth` has read them — so "tomato **in detail**" reads as the one topic *tomato*, never the two topics *tomato + detail*. (This was the live bug on first cut: "detail" mis-routed as a second topic and tripped the word-salad guard. Comprehend-then-consume fixed it.)
- **Siona shows she understood it**: the input-ride parse prints `· detail short` / `· detail long` (the comprehension is visible, per the user's debugging-trace preference).

## Live (the same question at three depths)
```
NORMAL  what is a tomato?
        [siona · definition] tomato: The tomato (Solanum lycopersicum) is a … berry …
          (related: →sauce, →soup, →ketchup, →based, and→onion, →dishes)            ← 6 directed

SHORT   what is a tomato, briefly?
        [input-ride: definition · detail short …]
        [siona · definition] tomato: The tomato (Solanum lycopersicum) is a … berry …  ← bare definition, no related-note

LONG    tell me more about a tomato, in detail
        [input-ride: phrase · topic ['tomato'] · detail long · steer ['about']]      ← 'detail' consumed (not a topic/steer)
        [siona · definition] tomato: …
          (related: →sauce, →soup, →ketchup, →based, and→onion, →dishes, →solanum, →paste;  ← 8 directed
                    ketchup, sauce, tomatoes, fruit, vegetable, small, plants, pizza, …)     ← + 12 assoc
```
`tell me more about volcanoes, go deeper` likewise returns the definition + 8 directed + 12 assoc.

## Honest scope
- Depth currently controls the **breadth of read-out** over the existing bounded tiers (more/fewer edges, longer/shorter walk, attach-both-or-none) — it does NOT yet add a *different kind* of knowledge for "more detail" (e.g. an examples tier, or paragraph-2 of the article). A depth-driven **tier ladder** (definition → relations → examples → full section) is the natural next rung.
- The extra material at `long` is still the bounded relation/assoc side-store (F584 capacity-sized), so "more detail" stays substrate-honest — it widens the read-out, it does not invent.
- `short`/`long` adjectives that are genuinely a *topic* (rare in Q&A, e.g. "what is depth?") are stoplisted from routing — an accepted, low-cost trade (the elaboration use dominates). Detection runs on the raw prompt, so it is unaffected by the stoplist.

## Verdict
Elaboration is now **understood, not discarded**: "tell me more / in detail" deepens the answer (more edges, longer walk, both relation tiers), "briefly / tl;dr" trims it to the core, and the meta-words are consumed from the content channels so they never mis-route — the F762 markup principle applied to answer length. Live on the rc155 server. Closes F762 queued item (C) elaboration-understanding; queued item (A) loopshelf-consolidation and (B) markup-kernel-into-genome remain.
