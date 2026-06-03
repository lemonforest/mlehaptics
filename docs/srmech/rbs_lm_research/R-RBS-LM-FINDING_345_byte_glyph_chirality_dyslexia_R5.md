# R-RBS-LM Finding 345 — #855 R5: byte-BAG catches transpositions + Class-C glyph-chirality catches b/d mirrors (CONFIRMED); but the position-bound SEQUENCE is a cliff, not graceful (FALSIFIES my earlier claim) — typo-robustness is bag-only; phonetic out of scope

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 · **#855 block:** R5 (byte-level + glyph-chirality; depends on R1's γ₅ axis) · **extends:** R-RBS-LM-25 (byte-level) · **script:** `R-RBS-LM-R5_byte_glyph_chirality_dyslexia.py`

## What R5 tested

The dyslexia/typo-robustness claims from the earlier exchange, srmech-native (`mint_vector` byte/glyph atoms; `bundle` bag; `bind`+`permute` sequence; `similarity`), three encoders × four error types:
- **byte_bag** — permutation-invariant bag of byte-atoms.
- **byte_seq** — position-bound `bind`∘`permute` over bytes (order-sensitive).
- **glyph_bag** — Class-C glyph-chirality: fold horizontal-mirror pairs (b↔d, p↔q) to a shared **shape-class** atom (the γ₅ relation made explicit at the glyph level).

## Result (means per error type)

| error type | byte_bag | byte_seq | glyph_bag |
|---|---|---|---|
| transposition (the/teh, form/from, …) | **1.000** | **0.011** | 1.000 |
| omit/insert (hello/helo, …) | 0.707 | 0.001 | 0.711 |
| mirror b/d,p/q (bad/dad, bpdq/dqbp, …) | **0.503** | −0.001 | **1.000** |
| phonetic (enough/enuff, phone/fone) | 0.339 | 0.007 | 0.346 |

## Verdict — 3 confirmed, 1 FALSIFIED (reported straight)

1. **CONFIRMED — bag catches transpositions perfectly (1.000).** A transposition leaves the byte *multiset* unchanged, so the permutation-invariant bag is exactly invariant. This is the "read by letter-set, not strict order" effect, made literal.
2. **FALSIFIED — the position-bound SEQUENCE does NOT degrade gracefully.** byte_seq scores **0.011** on transpositions (and ~0 on every single-edit typo) — **near-orthogonal, a cliff**, not graceful. My earlier conversational claim that "K3 degrades gracefully (no BPE cliff)" is **wrong for this encoder**: position-bound `bind∘permute` is *more* brittle to reordering than BPE, because one swap shifts the positional binding of every subsequent byte. **Honest correction: typo-robustness is bag-only; the sequence encoder gives order-discrimination at the cost of being a reordering cliff.**
3. **CONFIRMED — glyph-chirality catches the b/d, p/q mirror that byte-identity misses.** byte_bag scores **0.503** on mirror-swaps (it sees b and d as unrelated bytes, only the shared letters overlap); glyph_bag scores **1.000** (b,d → one shape-class → identical). This is the concrete payoff of the R1 dependency: **a chirality error (b↔d mirror) is invisible to byte-identity and visible only to an encoding that carries the glyph-chirality axis** — exactly "you can't catch a chirality error if the chirality axis doesn't exist in the representation."
4. **CONFIRMED (honest negative) — phonetic is out of scope.** enough/enuff, phone/fone score ~0.25–0.35 under every byte/glyph encoder — they are *sound*-level relations, not graphemic, and need a phonetic render (a different rosetta layer). Flagged, not papered over.

## Implication for the instrument (ties R5 → R1/R2)

The **input-robust** encoder for dyslexia/typos is **bag (presence) + glyph-chirality (shape-class)** — NOT the position-bound sequence. There is a real tradeoff:
- **bag** = transposition-robust + (with glyph-chirality) mirror-robust, but **order-blind**.
- **sequence** = order-discriminating, but a **reordering cliff** (no typo-robustness).

So the R1 K1+K3 smoothie must **weight toward the bag (K1)** for input-robustness, using the sequence (K3) only where order genuinely carries meaning. And the glyph-chirality layer = the **γ₅ shape-class** axis (R1/R2's store-rung chirality) applied at the glyph level. The bag is the order-2 *presence* (store rung); the mirror-catch is the Class-C *chirality* (the iω₇/γ₅ axis that R1 proved the store must carry). R5 is the accessibility-mission instance of the same Klein-4-native conclusion.

## Honest caveat on glyph_bag

glyph_bag folds b/d (and p/q) to **one** shape-class — so it scores 1.000 on a mirror-swap by *fully collapsing* the distinction. That is the right behavior for *robust recovery* (snap a b/d confusion to the shared word) but it **loses the b-vs-d distinction** when you need it. Recovering the distinction needs the **γ₅ orientation as a kept fiber** (R1/R2 "keep both": shape-class base + orientation fiber) — i.e., glyph_bag for recovery, the orientation tag for disambiguation. Not built here; flagged as the clean next step.

## Discipline

srmech-native (`mint_vector`/`bundle`/`bind`/`permute`/`similarity`); **falsified my own prior claim** (sequence-graceful) and reported it straight per no-leaning; phonetic negative kept visible; ADA-accessibility mission (the foundational motivation). Composes with R1 (Klein-4-native γ₅ axis), R2 (the chirality rung), and R-RBS-LM-25 (byte-level English-privilege strip).
