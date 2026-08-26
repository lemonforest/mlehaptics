# F765 — two passes, not one: UNDERSTAND the input into English (etak FIND / transcription) THEN derive meaning (etak RIDE / translation)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F762 (the abstract-layer form-resolver — *promoted* here from a last-resort fallback to the FIRST pass), F761 (the ni-Vanuatu abstract layer = the canonical "understood" medium any surface projects onto), F763 (answer-depth now rides on the *understood* form), the **etak find→ride** walk pattern (the foundational two-phase shape) · **User direction (2026-06-15):** "you're trying to consider two things as a single pass … first we must understand the input into english, and then we derive meaning as a different action … the follow in biology's footsteps we've done with our RBS-SNN object and genome." · **Clarification (2026-06-15):** the biology link is METHODOLOGICAL — genome, RBS-SNN, and etak navigation are all cases where we *studied the biology first, extracted the principle, then built deliberately* (not jumping in blindly). The split is that lineage; the transcription→translation phrasing below is an *illustrative* parallel, not a literal pipeline claim.

## The correction
I had been treating comprehension and meaning-derivation as ONE pass — reading intent/depth/topic directly off the raw surface. The user's correction: these are **two distinct, sequenced actions**, the same find→ride split the kernel walk already uses (and reminiscent of biology's transcribe-faithfully-*then*-express staging — used here as illustration, per the clarification above).

| | etak | biology | action | operates on | yields |
|---|---|---|---|---|---|
| **Pass 1** | **find** | **transcription** | UNDERSTAND into English | raw surface (any spelling/inflection/variant) | a canonical, *understood* rendering |
| **Pass 2** | **ride** | **translation** | DERIVE MEANING | the understood rendering | intent · depth · topic · the answer |

Form-level resolution (spelling/variant) is **Pass 1's** job; meaning is **Pass 2's**. This also dissolves the form/meaning confusion from the prior exchange (`detail ≈ retail 0.66`): that collision only happened because I was doing meaning work on un-normalized surface in one breath. **Form-similarity (the glyph layer) is the RIGHT tool for Pass 1 and the WRONG tool for Pass 2** — the split puts each where it belongs.

## What landed (in `infer()`)
- **`_understand(unroutable)` = PASS 1** — comprehend each non-routable surface token into its canonical English form via the abstract glyph layer (F762's resolver, now run FIRST). Returns `{surface: (canonical, sim)}`. The meaning tiers then ride on the canonical `salient`, so a misspelling reaches the **full** gloss + relation + depth machinery — not just the old last-ditch fallback.
- **Gated by `_routable`, not `_recognized`** — `_recognized` also counts the loose `wiki_idx` abstract index, so it was True for tokens that route to NO answer tier (e.g. `volcanoe` matched wiki_idx but is no gloss/relation/assoc key, and dead-ended). `_routable` = "resolves to an actual answer tier (deep-kernel / gloss / relation / assoc, lemma-folded)." Pass 1 comprehends the *un*-routable tokens.
- **Orthographic guard (edit distance) against hallucinated comprehension** — accept a Pass-1 resolution only if it's a plausible TYPO/VARIANT (`edit_distance ≤ max(2, len//3)`), never a coincidental glyph match to a different word. Without it, a genuinely-unknown word was force-comprehended and answered confidently (`flibbertigibbet → fleetwood (0.67)` → "Fleetwood is a town…", a hallucination). The guard sends genuine unknowns to the honest asking-state.
- **Both passes are visible** — the output shows `[understood: volcanoe→volcano (0.70)]` (Pass 1) above `[input-ride: …]` (Pass 2), so find-then-ride is legible.
- **Asking-state simplified** — the inline abstract-resolve fallback is removed; comprehension is Pass 1's job, so reaching asking-state means "genuinely not understood," the honest terminal.

## Verified live (rc155 server)
```
what is a volcanoe?              → [understood: volcanoe→volcano (0.70)] → definition + relations   (typo, 1 edit)
what is a computre?              → [understood: computre→computer (0.64)] → the dict-en answer       (typo, 2 edits)
tell me more about volcanoe …    → [understood: volcanoe→volcano] · detail long → definition + 8 directed + 12 assoc
what is a flibbertigibbet?       → asking-state (NOT force-comprehended)                              (genuine unknown)
what is music?                   → (no Pass-1 line) → deep-kernel walk                                (clean word, untouched)
```
The payoff: a variant now gets the **full** Pass-2 treatment (incl. F763 depth), and genuine unknowns are honestly declined instead of confidently misread.

## Honest scope
- **Pass 1 is token-level typo/variant comprehension** today. Phrase-level paraphrase ("flesh it out", "don't be terse") and cross-language input are the *deeper* Pass-1 build — those need a translation/intent dictionary, not glyph-similarity (glyph-sim is form, not meaning; F762/this finding).
- **The resolver's glyph-ranking can mis-pick among close candidates** (`tomatto → tomatillo` over `tomato`); the edit guard then rejects the mis-pick → honest ask rather than a wrong answer. Edit-distance-*ranked* candidate selection (prefer the edit-closest among glyph-plausible candidates) is the refinement that would resolve `tomatto → tomato`.
- **This sets up meaning-based intent (the prior exchange):** with the passes split, the depth/intent read is cleanly a **Pass-2 meaning op on the understood form**. It is still keyword-anchored today; the meaning-anchored version (definitions of intent words → concept anchor → overlap) is the next inch, and it needs an intent-word dictionary Siona doesn't yet hold.
- srmech-native (Class-M HDC similarity for the form-match; edit distance is pure Python, no `abs()`); no CAD; data outside the repo.

## Verdict
Inference is now **two passes, not one**: Pass 1 UNDERSTANDS the surface into canonical English (etak find / transcription — gated to plausible typos so it never hallucinates a comprehension), and Pass 2 DERIVES MEANING on the understood form (etak ride / translation). A misspelling now reaches the full meaning machinery; a genuine unknown is honestly declined; the form/meaning confusion is dissolved because each tool sits in its own pass. Live on the rc155 server. It belongs to the project's biology-first METHOD (study the biology, extract the principle, build deliberately — as with the genome, RBS-SNN, and etak navigation), not a literal biological pipeline.

## Open next-question (user, 2026-06-15): can we still claim "no hallucination"?
The edit-distance guard above had to be *added* to stop Siona confidently answering a genuinely-unknown word (`flibbertigibbet → fleetwood`) — which raises whether "no hallucination" is even claimable for a synaptic-NN-style (similarity / nearest-neighbour) inference. The honest distinction to test: **confabulation** (fabricating content Siona doesn't hold — eliminated by construction: retrieval-only, attested stores) vs **misbinding** (retrieving *real, attested* content but binding it to the *wrong* query — the nearest-neighbour failure mode, since NN always returns a nearest item unless an abstention threshold says "none"). The flibbertigibbet case is misbinding, not confabulation. So the refined, falsifiable claim is **"no confabulation; misbinding suppressed by calibrated abstention (route-confidence floor + the asking-state)"** — abstention is *engineered*, not an automatic property of the inference. Biology parallel: human memory error is mostly *misattribution / source-monitoring* (misbinding), not pure fabrication — so the residual mode here may be the *biological* one, consistent with the biology-first method. **To discover:** characterize Siona's abstention calibration — feed known / near-miss / genuinely-unknown inputs, sweep the floor + edit-distance thresholds, and measure the misbinding rate vs abstention vs coverage (the precision/coverage curve). That DISCOVERS where misbinding is inherent and how abstention trades against answering. (Queued; see the session exchange.)
