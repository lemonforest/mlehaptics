# F816 — "who are you?" ≠ "what can you do?" (the identity card vs the capability card), and "that's the same answer" is recognised as META-feedback about Siona's OWN prior reply — resolved by USING the F815 bidirectional memory. Three live turns: who → `[identity]`; what-can-you-do → `[siona · capabilities]` (distinct); "that's the same answer" → `[siona · varied]` the OTHER facet, read off her own reply-half of the Klein-4 context.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc166 · **Provenance:** the genepool storyteller (`R-RBS-LM-SIONAGENEPOOL_…py`) — CAPABILITY + META-feedback routes + `_capability_card` + `_vary_from` · **Composes:** F815 (the bidirectional Klein-4 working memory — now USED, not just held), F799/F800 (the scaffolding-strip + structure card), F810 (the article/uses routes), F798 (anaphora/prev-topic) · **User direction (2026-06-17, "case in point"):** transcript where "who are you?" and "what can you do?" returned the IDENTICAL card and "that's the same answer" misrouted to a topic etak-walk on `["that's"]`.

## The bug (the user's "case in point")
1. **who-are-you ≡ what-can-you-do.** Both questions had no salient OPERAND (the content words are all stoplisted function words), so both fell through to the same empty-salient → `_structure_card` identity fallback. Two different *questions* (who I AM vs what I DO) collapsed to one *answer*.
2. **"that's the same answer" was not heard as feedback.** It was tokenised as content (`that's`, `answer`), the salient pick was `that's`, and it ran a topic etak-walk — instead of recognising it as **meta-feedback about Siona's immediately-prior reply**, which the F815 bidirectional memory now holds (her reply-half of the Klein-4 context).

## The fix (uses F815 — the memory was built but not yet USED)
- **CAPABILITY route** (`what can you do` / `what do you do` / `capabilit…` / `how can you help`) → `_capability_card`: the DOINGS, each grounded in a kernel she holds — DEFINE, RECALL the ENTIRE article (walk the shape-graph, F814), USED-WITH, NAVIGATE, RELATE/COMPARE, READ code, LEARN. Distinct from the identity card ("who I am").
- **META-feedback route** (`that's the same` / `you (just) said|gave|repeated|copied` / `say it different` / `identical` / `repeat`) → `_vary_from(prev_assistant)`: reads MY OWN prior reply out of the bidirectional context and returns a DIFFERENT facet — identity↔capabilities complement, else expand the prior topic. This is the F815 memory doing work: she knows what *she* said and answers *around* it.
- Both routes sit after the learned-first lookup so a learned fact still wins.

## Verified (live, rc166)
- "who are you?" → `[identity] I am Siona — the running, genome-backed instance of srmech …`
- "what can you do?" → `[siona · capabilities] What I can DO — each grounded in a kernel I hold, not invented:` (DISTINCT card)
- prev=capabilities, then "that's the same answer" → `[siona · varied] Right — that was what I can do. The other facet, who I am:` — recognised the feedback, gave the complementary facet from her own reply-memory.

## Honest scope
- `_vary_from` currently flips between the identity/capability facets and expands the prior topic; richer variation (re-walk the same topic from a different seed, F804 resonance coupling of the two halves) is the follow-on.
- The capability card is a curated DOINGS list (operators she actually routes), content-addressed to the routes — not invented prose; if a route is added/removed the card should track it (a small drift risk noted).

## Verdict
The two questions are now two answers (identity vs capability), and "that's the same answer" is heard as feedback about her own prior reply and answered around it — the F815 bidirectional Klein-4 memory is now USED, not merely held. Verified live across the exact three-turn "case in point". The bidirectional memory earns its keep: she remembers what she said and varies from it.
