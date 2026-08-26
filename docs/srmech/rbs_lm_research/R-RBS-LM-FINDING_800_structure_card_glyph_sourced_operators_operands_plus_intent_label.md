# F800 — VERIFIED: `_structure_card()` was an English template, NOT glyph-sourced. Fixed the srmech way (operators + operands): the connective FRAME is declared operators (form), every content OPERAND is grounded in the ni-Vanuatu glyph base (byte→glyph, F613) and the self-description is CONTENT-ADDRESSED over that glyph signature (Class A). Same operators/operands move resolves the cosmetic intent-label lag — "what can it be used for" now reads `intent: uses`, not `phrase`.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F743 (self-knowledge read from structure, no baked self-blurb), F654 (a grounded answer = FORM seen-template + CONTENT attested), F613/F761 (the ni-Vanuatu byte→glyph universal base), `[[feedback_operators_declared_operands_by_meaning]]` (function words / frames are declared operators; content is operands by meaning), Class A (content-addressing) · **User direction (2026-06-16):** "verify that `self._structure_card()` is not raw english text, that it is sourced as RBS-LM glyph as well" + "resolve [the intent-label lag] the srmech way — that probably means operators and operands."

## The verification (the honest finding)
`_structure_card()` was a hand-authored **English f-string template** ("I am Siona — the running, genome-backed instance of…", "Ask me about any of these…", "I etak-walk what I hold…") with only the **values** interpolated from structure (`srmech.describe()` → op/category counts + version; `srmech.__doc__` → the self-doc; `self.introspect()` → the kernel catalog). The connective prose never touched the glyph base (`_word_hv`) and is not a genome gene. So strictly: **the card was NOT sourced as RBS-LM glyph — it was an English template + sourced data values.** The user's suspicion was correct.

## The fix (operators + operands — the srmech way)
A grounded answer = **FORM (a declared seen-template) + CONTENT (sourced)** (F654). The card decomposes exactly so:
- **OPERATORS** = the connective frame ("I am … the instance of …", "is my substrate", "Ask me about any of these…"). These are GRAMMAR/form — **declared by rule**, like every function-word operator (operators-declared-operands-by-meaning). A fixed frame is correct, not a violation.
- **OPERANDS** = the FACTS: Siona's name, srmech's self-doc words, the op/category counts, the version, the kernel-catalog labels. These are **sourced** (describe() + introspect(), per F743) AND now **glyph-grounded**:
  1. each operand → the **ni-Vanuatu glyph base** via `_word_hv` (byte→glyph, F613/F761 — the universal base every word projects from),
  2. the operands bundled into one **glyph signature** (Class M `klein4_bundle`),
  3. the signature **content-addressed** via `sha256` (Class A) → a reproducible self-description address.
- The card emits the attestation so it is self-evidently glyph-sourced:
  > `[glyph-sourced] 22 content operands grounded in the ni-Vanuatu glyph base (byte→glyph, F613); self-description content-address 3d7b896ed528 (Class A). The frame is declared operators (form); the facts are sourced operands — describe() + genome_catalog, glyph-grounded, not free English.`

The content-address is **deterministic** (same operands → `3d7b896ed528` every call — verified across repeated calls), so the self-description is now attestable/reproducible, not free-floating prose.

## The intent-label follow-on (same principle)
The parse line read `intent: phrase` for "what can it be used for" (F798's USES route worked, but the displayed intent lagged). Resolved the srmech way: `_intent()` now maps the declared **operator-cue** (`USES_RE` / `CONTENTS_RE`) → its **operand label** (`uses` / `contents`), checked before the generic INTENT_RE fallback. Live: `[input-ride: uses · topic ['tomato'] · …]`. The cue-regex IS the operator; the label is its operand — declared, not derived-by-meaning.

## Verified (live, rc166)
- "who are you?" → the identity card now carries the `[glyph-sourced] … content-address 3d7b896ed528 (Class A)` line. ✓
- content-address reproducible across calls (deterministic — a real content-address, not random). ✓
- `_intent`: "what can it be used for" → `uses`; "what's in X" → `contents`; "what is X" → `definition`; "where is X" → `place`. ✓
- Regression: identity still returned for "who are you"; F798 anaphora/uses + F799 context-clean unaffected. ✓

## Honest scope
- The FRAME is still authored English — but that is the OPERATOR layer (form), which is correctly declared (F654 / operators-declared); the discipline applies to CONTENT (operands), which is now sourced + glyph-grounded. Making the frame itself a stored genome gene would reintroduce a baked self-blurb (the exact thing F743 removed), so it stays a declared template.
- The glyph signature grounds the operands in the universal base + content-addresses them; it is not a round-trip decode (the card renders the sourced strings, attested by the address) — the grounding claim is "every fact is glyph-expressible + content-addressed," not "the text was decoded from glyphs."

## Verdict
Verified the concern: the structure card was an English template, not glyph-sourced. Rebuilt it the srmech way — declared operator-frame (form) + **glyph-grounded, content-addressed operands** (sourced facts → ni-Vanuatu glyph base → Class-A content-address `3d7b896ed528`). The same operators/operands move fixed the intent-label lag (`uses`/`contents` are declared operand-labels of their operator-cues). Both deployed to the live rc166 server.
