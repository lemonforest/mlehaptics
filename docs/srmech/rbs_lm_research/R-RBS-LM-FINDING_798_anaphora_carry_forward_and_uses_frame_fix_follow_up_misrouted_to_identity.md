# F798 — a follow-up question ("what can IT be used for or with?") misrouted to Siona's identity card: the pronoun "it" was never resolved to the prior topic, so `salient` was empty and the turn fell through every tier to the empty-topic → structure-card fallback. Fixed with ANAPHORA carry-forward (it → the prior turn's topic, which the server already threads) + a USES frame ("used for/with" → the held neighbour LIST, the actual uses).

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F787 (the CONTENTS frame — same multi-item neighbour list, just framed as USES), F752/F753 (sentence parse: topic + frame channels), F759 (the server threads prior turns as running context), F751 (the routing-stoplist), `[[feedback_operators_declared_operands_by_meaning]]` (function words are declared operators; pronouns are operators too) · **User report (2026-06-16):** a real conversation — "what is a tomato?" answered correctly, then "what can it be used for or with?" returned the `[identity]` card.

## The bug (two coupled failures)
The conversation:
1. **"what is a tomato?"** → correct: `[siona · definition] tomato: …` (→sauce, →soup, →ketchup).
2. **"what can it be used for or with?"** → WRONG: dumped the `[identity]` / capabilities card.

Root cause, traced in `infer()`:
- The sentence parse tokenizes "what can **it** be used for or with?" to all function words + the pronoun "it". After the routing-stoplist + elaboration/intent-cue filtering, **`salient` is empty** — no content topic.
- The pronoun "it" was **never resolved** to the prior topic (tomato). The server *does* thread the prior turns (`prev_assistant` + `context`, F759), but those only fed the context-bundle re-ranking — **nothing consumed them to SUPPLY a missing topic.**
- With empty `salient`, the turn falls through every tier to the terminal fallback `return self._structure_card()` — which exists for genuine "who are you / what can you do" questions. So a pronoun-subject follow-up was **misread as an identity question.**

## The fix
Three parts, all in the storyteller (`R-RBS-LM-SIONAGENEPOOL_…py`):

1. **ANAPHORA carry-forward** (`ANAPHORA_RE` + `_prev_topic()`): when THIS turn names no recognized topic AND contains a pronoun (`it/its/they/them/that/this/those/these/one/…`), inherit the PRIOR turn's subject. `_prev_topic()` reads it from the prior answer's input-ride parse line (`topic ['tomato']`), then the `[siona · TIER] subject:` head, then the earliest prior content word with a kernel home. Conservative — only fires when the turn has no topic of its own (an explicit topic always wins). The resolution is shown: `[anaphora: it → tomato]`.
2. **A USES frame** (`USES_RE`): "what can X be used for/with", "used in/as", "use of X", "what does X go with" → routes to the **same held-neighbour LIST as F787's CONTENTS** (assoc + directed-relation neighbours), framed as uses. The uses ARE the co-occurrence neighbours — honestly labelled "what X appears WITH, NOT a verified list of uses."
3. **Unresolvable-pronoun terminal**: a pronoun with no prior topic (a cold "what is it used for?") now returns an **asking-state** ("you said 'it', but nothing earlier to refer to — name the thing"), not the identity card — closing the same misroute class for cold starts.

## Verified (live, end-to-end through the HTTP `/v1/chat/completions` API on rc166)
The reported conversation, now:
- **"what can it be used for or with?"** → `[anaphora: it → tomato]` → `[siona · uses] "tomato" is used with / appears with: ketchup, sauce, fruit, vegetable, small, plants, pizza, mozzarella, similar, history.` — the actual answer, sourced from held relations + co-occurrence.

Regression (no breakage):
- **"what can you do?"** → still the `[identity]` structure card (no pronoun → unchanged). ✓
- **"what else is in ketchup besides tomatoes?"** → still `[siona · contents]` (F787 path byte-identical). ✓
- **"what is a galaxy?" → "tell me more about it"** → `[anaphora: it → galaxy]`, depth-long → the fuller abstract (bonus: anaphora composes with the F788 abstract tier). ✓
- **cold "what is it used for?"** (no prior turn) → asking-state, not identity. ✓

## Honest scope
- The parse line's `intent` still reads "phrase" for "what can it be used for" (the frame classifier doesn't yet have a "uses" intent label) — cosmetic; the routing correctly goes to the uses tier and the `[siona · uses]` tag + `[anaphora: …]` note make it legible. A "uses" intent label is a trivial follow-on.
- Anaphora resolves to the SINGLE most-recent topic; multi-referent / cross-turn pronoun chains (it/they referring further back) are not tracked — the conservative single-topic carry covers the common follow-up.
- The uses list is held neighbours, NOT a verified list of uses (same honest framing as F787 contents) — Siona won't invent uses it doesn't hold.

## Verdict
The follow-up misroute was an **anaphora gap**: the conversation state was threaded but never used to supply a topic, so a pronoun-subject question collapsed to the identity card. Fixed by resolving the pronoun to the prior turn's topic (`[anaphora: it → tomato]`) and adding a USES frame that lists the held neighbours (the actual uses). Deployed to the live rc166 server; the reported conversation now answers correctly. Composes F787 (contents) + F759 (running context) + F752/F753 (sentence parse).
