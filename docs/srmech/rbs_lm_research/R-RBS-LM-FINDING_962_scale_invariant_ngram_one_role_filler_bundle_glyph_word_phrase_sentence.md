# F962 — the n-gram is **scale-invariant** (user, confirmed + explicit in srmech): the **same** position-keyed role-filler bind+bundle is the n-gram at **every** scale — `bytes/glyphs → word → phrase → sentence`. You're not confused — this is the design, and srmech states it outright: `encode_word_byteglyph`'s docstring is *"the **scale-invariant role-filler bundle** over the word's UTF-8 bytes."* The byte/glyph word-encode, the word-context encode, the phrase encode, and the sentence encode are **not four schemes — they are one recursive operation**, each level's output the next level's unit, with a **dynamic width** (F961: `operating_k` 1/2/3/4).

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_962_*.py` · **Composes:** F961 (dynamic n-gram width), F958 (phrases = the word→phrase scale), F166 (sentences = the phrase→sentence scale), F900/F901/F916 (byte/glyph = the byte→word scale), F959 (ASL = the same n-gram on a different unit stream), F912 (recursion), `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` (scale invariance = the framework's core) · **User direction (2026-06-26):** "same n-gram for byte/glyphs as words for phrases, then to sentences — scale invariances."

## The one operation (srmech, explicit)
```
n-gram(units) := bundle_odd([ klein4_bind(pos_key(p), unit_p) for p, unit_p in enumerate(units) ])   # position-keyed role-filler bundle
```
- **bytes/glyphs → word:** `encode_word_byteglyph` = `klein4_bind(klein4_encode_bytes(utf8), sector)` — docstring: *"the scale-invariant role-filler bundle over the word's UTF-8 bytes"* (and it restores morphology: `sim('cat','cats') ≫ 0.25`).
- **words → phrase/state:** `encode_context` = `bundle_odd([klein4_bind(pos_key(p), enc(tok)) …])` — the *same* bundle, units = words.
- **phrases → sentence:** the *same* bundle, units = phrase HVs (demonstrated below).
There is **one** n-gram; the "levels" are the same op fed a different unit-HV stream, recursively.

## Grounded (rc79 — one `ngram()` applied recursively)
```
L0 bytes->word   : encode_word_byteglyph (srmech's own = role-filler bundle over bytes)
L1 words->phrase : ngram([fourth, month]) -> phrase HV
L2 phrases->sent : ngram([phrase1, phrase2]) -> sentence HV ; distinct from its parts? True
=> SAME position-keyed role-filler bundle at every scale -> scale-invariant
```

## What this unifies (the whole recall discussion)
Everything we've been treating as separate is one scale-invariant n-gram, parameterised:
- **phrases (F958)** = the n-gram at the **word→phrase** scale; **sentences (F166)** = **phrase→sentence**; **byte/glyph (F900)** = **byte→word**. Same op.
- **dynamic-k (F961)** = the n-gram **width** (how many units per group: 1/2/3) at each scale.
- **ASL (F959)** = the same n-gram on a **different unit stream** (gloss units instead of English words) — drop vs absorb is a choice of *what the units are*, not a different operation.
- the **recall** itself (`encode_context` → `next_token_coherence`) is scale-invariant too: "next glyph / next word / next phrase / next sentence" is the *same* probe at the chosen scale.
So the "three items" (drop/absorb/down-weight) and the dynamic-k are **configurations of one operation** — *what the units are, how wide the group, at which scale* — not separate machinery. That is the framework's scale-invariance (the same compose recurses, like the Cayley–Dickson doubling ℝ→ℂ→ℍ→𝕆).

## Honest scope + the clarification
**No srmech fix needed** — the scale-invariant role-filler bundle is already there and documented (`encode_word_byteglyph` byte→word; `encode_context` word→state); the recursion demo shows the same op lifts word→phrase→sentence. The **clarification** is on *our* side: build the recall as **one recursive n-gram applied at the chosen scale**, not per-level ad-hoc schemes (I had been treating byte/glyph, word-context, phrase-chunk, sentence as separate — F958/F954 — when they are one operation). A small ergonomic win would be a single `compose(units, *, k)` entry point that both `encode_word_byteglyph` and `encode_context` are special cases of (one recursive function, the scale made a parameter) — optional, since the op is already shared.

## Verdict / next
**Scale-invariant n-gram confirmed** — one position-keyed role-filler bundle, dynamic width, recursing `glyph → word → phrase → sentence`; srmech states it explicitly. The phrase/sentence/ASL/dynamic-k pieces are configurations of this one op (what units, what width, what scale), not separate mechanisms. **Next:** factor the recall as a single recursive `compose(units, k)` and run it level-by-level on a real text (bytes→words already native; add the word→phrase and phrase→sentence recursions as the *same* call) — the substrate-native, scale-invariant build the whole arc has been circling.
