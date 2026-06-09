# Finding 699 — the dictionary is the WORD-level grounding map (the user's "like the unicode map")

**Script:** `R-RBS-LM-WORDMEANING_dictionary_is_the_word_level_grounding_map.py`
**Status:** VERIFIED (srmech 0.6.0rc8 runtime)
**User direction:** *"dictionary like unicode map maybe? — for english words to know what they mean?"*

## The insight — a three-rung grounding ladder, and the Unicode map is the bottom rung

The seen-rule layer needs a **lookup map at each resolution**, and they are the *same shape* one rung up:

| layer | the map | grounds… | finding |
|---|---|---|---|
| **char** | the Unicode map (`unicodedata`: codepoint → category/name) | what a character **is** | F696/F698 |
| **word** | **a dictionary** (word → definition) | what a word **means** | **F699 (this)** |
| **relation** | the big-wiki kernel (word → associations) | what a word is **seen with** | F690/F697 |

The user's intuition is exact: **`unicodedata` *is* the char-level dictionary** (codepoint → {category, name}); a word
dictionary is the same shape one rung up (word → {meaning, part-of-speech}); the big-wiki kernel (F690) is a third map
(word → co-occurrence neighbours). **One discipline, three resolutions.** All three are attested lookup tables; all three
fail an unknown key to the **asking-state** (F661); none invents.

## Crucial honesty — meaning is DETECTED via an attested source, not DECREED (F640/F688/F573)

A "dictionary" here is **not me writing definitions** (that would be the exact hallucination the chord forbids). It is a
**class-B attested map** — each entry a valid `MPRRecord` whose gloss traces to a real source:

- **Framework vocabulary** (`the_one`, `chirality`, `cascade`) → attested **class-A** to *our own* MFO + A-N notebooks
  (we own these meanings).
- **General-English words** (`galaxy`, `spiral`) → ship the **shape + the real Wiktionary pointer** (`source_url`,
  `license: CC-BY-SA-4.0`) with the gloss text marked **`[DEV-SESSION-FILL]`** — the reference does **not** fabricate the
  English gloss; the dev session loads the attested Wiktionary/WordNet dump.

> *MPR note:* Wiktionary and internal notebooks have **no DOI** — a living wiki / an internal doc are URL/path-located,
> not DOI-located. The MPR mandates a non-empty `source_doi`, so we lodge the honest **source locator** there (the wiki URL
> / notebook anchor), never a fabricated DOI. That is class-A/B attestation, not class-C (F640).

**Verified:** `the_one`/`chirality` → class-A attested glosses (notebook-sourced); `galaxy` → shape + Wiktionary pointer
(dev-fill); `assoc('galaxy')` → `[spiral, turns, coils]`; **`dragon`** → unknown to **all three** maps (no name-less char
issue, no word entry, not in kernel vocab) → the **asking-state** ("What is 'dragon'? I have no attested meaning and no
attested association") — detected-absent (F688), never invented.

## Lands in the bone

A `storyteller_bone/wordmeaning/` sibling to `wordassoc/` (the relation map) + a `word_meaning.descriptor.toml`; the dev
session loads the attested Wiktionary/WordNet dump and srmech wires `word_meaning()` alongside `assoc()` in
`storyteller.infer`'s gap-fill.

**Composes:** F698 (the char/Unicode map) · F690/F697 (the association map) · F640/F688 (detect-not-decree) · F573 (no
fabricated glosses) · F661 (the asking-state) · F669 (the MPR attestation) · F695 (the bone). Extends F698.

*Held open (F394). Reference scaffold; not a package edit.*
