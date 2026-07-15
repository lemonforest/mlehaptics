# F1241 — Siona now says what water IS (not only what it's like): `define` reads the FULL-BODY encode for the definition. Answer to "why wasn't it reading this already?" — the definitions were ALREADY encoded (the #227 full-body RBS-HDC instrument); `load_corpus` just attached only the co-occurrence genome, so we weren't reading all the stores. Also fixes the "in detail, what is X" routing miss.

**User:** *"it never says what water is, only what it's like."* + *"help us understand why loading the smallwiki entire encoded genome wasn't reading this already, or … we weren't reading all the things we can yet, and still aren't?"* + *"in detail, what is water?" → "(no substrate content yet)"*.

## The answer to "why wasn't it reading this"
Siona has MULTIPLE simplewiki representations on disk, and `load_corpus` attached only ONE:
- **`simplewiki_directed.genome`** — the #231 DIRECTED CO-OCCURRENCE genome. **Relational by construction** (meaning = edges, F1132): it stores which words appear NEAR a token, so it can only ever say what a thing is *LIKE* (its neighbourhood). This is the only store `load_corpus` wired.
- **`simplewiki_fullbody_instrument.ndjson`** (384 MB) + `_index.json` (240,823 titles) — the #227 FULL-BODY RBS-HDC encode: the **actual article text** (`s` = the body tokens), recallable via `bridge.recall` (the de Bruijn fiber walk, F805/F818). This is where "what water *IS*" lives — but `define` never read it.
- (Plus `abstracts`/`glosses`/`rawbody` stores — same story.)

So: **the definitions were already encoded; we simply weren't reading that store.** "We weren't reading all we can" — exactly right.

## The fix (read the EXISTING encode, don't rebuild)
- `corpus_store._attach_bodies` auto-discovers the sibling `*fullbody_instrument.ndjson` (+ `_index.json`) next to the genome (env `SIONA_BODIES` overrides) and attaches it to the handle. Additive — no bodies means the relational read only.
- `corpus_store.body_lead(token)` recalls the article body via **`bridge.recall`** and **pivots to the first `<token> is/are/…`** — the definitional copula — so the leading `thumb|…` image-caption markup is skipped and the definition comes through clean; a trailing dangling connector is trimmed (the encode stripped punctuation, so a fixed span can end mid-clause).
- `infer._corpus_reply` now LEADS with the definition ("what it IS"), then the co-occurrence relations ("It is also related to …"), cited to the attested genome. Live:
  - *what is water* → **"Water is a simple chemical compound made of two hydrogen atoms and one oxygen atom it is clear has no taste or smell and is almost colorless all living things. It is also related to bodies, turning, soil, and pool. (Simple English Wikipedia, CC BY-SA 4.0)"**
  - *planet* → "A planet is a large object such as venus or earth that orbits a star…" · *science* → "Science is what we do to find out about the natural world…" · *music* → "Music is a form of art that uses sound organised in time…"

## The routing miss (F1240)
"in detail, what is water?" returned "(no substrate content yet)" — the `continue`/substrate branch. The router matched the define frame only utterance-INITIAL, so the "in detail," prefix pushed it off position 0 → fell through to WH-in-situ → grounded to `continue`. Fixed: `route` now strips leading VERBOSITY operators (the same set the context-shaper uses) before matching the frame, so "in detail, / briefly, …" still routes to define. **This band-aid is itself the argument for the next step** (below).

## Honest notes + the standing next step
- The definition span has no sentence boundaries (the encode stripped punctuation), so it can read slightly run-on; the pivot + dangle-trim make it a clean sentence in the common case. A punctuation-preserving body encode would sharpen it (a re-encode, deferred).
- **The router should be knowledge-kernel-grounded** (the user's Q: "why a router when the knowledge+language kernel describes intent?"). It doesn't need to be positional: the language board already declares the operators, the knowledge kernel already describes each intent (`define` = "Define a concept…"). Each hand-coded frame fix (like F1240's "in detail") is evidence. User chose "both, definition first" — the definition (this finding) is done; the grounded-intent refactor is the standing next step.

Composes **F1239** (the sentence render this leads with the definition into), **F1237/F1238** (the tome-tree relations = 'what it's like'), **#227/F805/F818** (the full-body instrument + de Bruijn recall — the definition source), **F1132** (relational vs the body text), **F1010 / [[feedback_operators_declared_operands_by_meaning]]** (the router discipline the grounded-intent step revisits), the AMSC/MPR cite. #231/PKG-3. Commits `8d43b02e` (routing) · `8a0b90e9` (definition read).
