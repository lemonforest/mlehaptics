# F801 — a hand-authored English reply is a "hidden magic number" (unattested prose typed into the code). VERIFIED the user's hypothesis: encode a reply's English into the ni-Vanuatu LANGUAGE ABSTRACT and INFER it back through Siona's own vocabulary and you do NOT get the exact input — the non-exactness IS the inference signature, and the words that drift ARE the ungrounded magic numbers (round-trip exactness = groundedness). Plus: replaced the F799 brute-force context scrub with a SURGICAL graft (working memory = the declared operands, not scrubbed prose).

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** the no-magic-numbers discipline (a number is magic iff UNATTESTED — CLAUDE.md §4; this extends it from constants to PROSE), F800 (operators/operands; glyph-sourced operands), F762 (`_abstract_resolve` — inference through the glyph abstract), F613/F761 (the ni-Vanuatu byte→glyph universal base), F774 (infer = open/fallible), F552 (the model↔ideal gap is a substrate FEATURE, not error), F799 (the context fix this supersedes the brute-force half of) · **User direction (2026-06-16):** "search for other hand authored replies — this is hidden magic numbers" · "that should not have gotten in" · "we can encode the english content into language abstract … if this works correctly, we won't get the exact value that we provide as an output, based upon inference" · "we can surgically graft working context memory, don't brute force it."

## 1. The audit — hand-authored replies ARE magic numbers
A "magic number" in this project is **anything unattested** — no traceable source of truth (CLAUDE.md §4). A hand-authored English reply is the **prose form of exactly that**: a literal typed into the code, sourced from nowhere in the substrate. The storyteller has **40 such reply returns** (`return (f"[siona · …] …")`). F800 attested the structure-card's *operands* but left its English *frame* — which is the very thing that "should not have gotten in." The frame, the provenance card, the asking-state prose, the honest-note clauses: all unattested prose = hidden magic numbers.

## 2. The experiment — encode → language-abstract → infer ≠ exact (hypothesis CONFIRMED)
`R-RBS-LM-ENCODEINFER_…py`: for a reply's content words, encode each into the ni-Vanuatu glyph abstract (`_word_hv`, byte→glyph) and INFER the nearest grounded word back (Klein-4 similarity over Siona's 216,695-word vocabulary — the F762 mechanism). Result:

| reply | content words | round-trip EXACT | drifted |
|---|---|---|---|
| structure-card frame (hand-authored) | 25 | 10 (40%) | 15 |
| provenance-card (hand-authored) | 26 | 11 (42%) | 15 |
| a SOURCED definition body (wiki content) | 13 | 9 (69%) | 4 |
| **overall** | **64** | **30 (47%)** | **34** |

**The inferred output is NOT the exact input (47% exact) — the hypothesis holds.** The drift is the **inference signature** (F774/F552): `backed→backpack`, `instance→incense`, `stored→stord`, `package→page`, `levels→levens`, `locatable→lou barletta`. And it is **diagnostic**: round-trip exactness MEASURES groundedness — the **sourced wiki content round-trips far better (69%) than the hand-authored cards (40–42%)**, because its words have grounded homes and the cards' framework-jargon does not. The words that drift ARE the magic numbers.

**Why this matters (the direction):** a genuinely substrate-grounded reply, composed by inference over the abstract, will naturally vary from any literal we would hand-type — so the variation is the *proof* the reply was inferred, not echoed. The path to de-magic-numbering Siona's voice is to compose replies by inference over the abstract + genome content, not to type English. (Full rollout — every reply inferred — is the next arc; this finding validates the mechanism and the metric.)

## 3. The surgical context graft (don't brute force)
F799 fixed the context-pollution by **regex-scrubbing** Siona's rendered prose — brute force. Replaced with a **surgical graft** (`graft_context`, role-aware, in the handler): a USER turn contributes its own words (clean); an ASSISTANT turn contributes ONLY the operands Siona DECLARED (her `topic [...]` markers), never her prose. The working memory is the conversation's operands *by construction* — no scrubbing. Live: a 3rd turn now shows `context ['tomato']` (the prior turn's declared topic-operand), clean. (`_context_content` stays as a defensive net for direct callers, but the live path is the surgical graft.)

## Honest scope
- The ENCODEINFER decode is bucketed by 2-glyph prefix over the gloss vocab; some drift targets are proper-noun article titles (`nazr mohammed`, `lou barletta`) — noisy, but the verdict (output ≠ input; sourced > hand-authored) is robust to the noise.
- This finding **validates the mechanism + metric**; it does NOT yet rewire Siona's replies to be inference-composed. That rollout (compose each reply by inference over the abstract, accept non-exactness) is the next arc — queued, not done here.
- The OPERATOR frame (grammar/form) is legitimately declared (F654/F800); the magic-number concern is the unattested CONTENT prose. The rollout must preserve the operator/operand split while sourcing the content.

## Verdict
Confirmed: hand-authored replies are hidden magic numbers (unattested prose), and encoding a reply's English into the language-abstract then inferring it back does **not** reproduce the exact input — the non-exactness is the inference signature, and the drift pinpoints the ungrounded words (round-trip exactness = groundedness; sourced wiki content 69% vs hand-authored cards 40–42%). Separately, the running-context working memory is now **surgically grafted** from the declared operands, not brute-force-scrubbed. Deployed to the live rc166 server; the experiment is read-only.
