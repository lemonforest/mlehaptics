# F810 — two live Siona bugs fixed: (1) request-meta words (`show`/`wiki`/`article`/`page`/`list`) were being routed as TOPICS — "show" matched the TV-show noun, "wiki article" hit the phrase-decline, and that misrouted parse POISONED the running context; they are request OPERATORS (declared, F770) → stoplisted. (2) there was NO way to ask Siona for an article → added an ARTICLE route ("(wiki) article/page for/about X", "show me the article") that resolves the subject (multi-word binomial too: solanum lycopersicum → tomato, F790) and serves the fullest text held — the abstract-full LEAD — honestly flagged as the lead, not the full body.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 (live server; verified on rc169 too) · **Composes:** `[[feedback_operators_declared_operands_by_meaning]]` (request words = operators), F798 (anaphora — the stoplist fix lets it fire), F799/F801 (the context instrument + surgical graft — this removes the poisoning at the source), F790 (multi-word entity resolution), F788 (the abstract-full store = the lead), F805–F809 (the deterministic walk = the future full-body recall) · **User report (2026-06-16):** "context isn't working correctly and we don't have a way to invoke a full wiki article from siona" (with the 4-turn transcript).

## The two bugs (from the transcript)
- **Turn 3** "would you give us the wiki article for solanum lycopersicum?" → misrouted to the phrase-decline ("reads as several things (wiki, article, solanum, lycopersicum)"). `wiki`/`article` were treated as content TOPICS, so the F790 entity resolver got `['wiki','article','solanum','lycopersicum']` (phrase not in any lead) and declined. That bad parse's `topic [...]` then POISONED turn 4's context (`['tomatoes','wiki','article','solanum','lycopersicum']`).
- **Turn 4** "show me more about it" → defined the TV-show noun: `show` was routed as the topic, so the F798 anaphora guard (fires only when no recognized topic) never triggered and "it" was never resolved to tomato.

Both are the operators/operands discipline: `show`/`give`/`tell`/`wiki`/`article`/`page`/`list` are **request operators** (about the request, not the subject). `give`/`tell`/`want` were already stoplisted; `show`/`wiki`/`article`/`page`/`list`/`entry` were not.

## The fix
1. **Stoplist the request-meta operators** — added `show/shows/showed/showing/list/lists/wiki/article/articles/page/pages/entry/entries/us` to `ROUTING_STOPLIST`. Now `show` can't be a topic (anaphora fires for "show me more about it"), and `wiki`/`article` aren't topics (the entity resolver sees the real subject; no context poisoning).
2. **An ARTICLE route** (`ARTICLE_RE` → before the reasoner): "(wiki) article/page for/about X", "the full article", "show me the article" → resolve the subject and serve the fullest text held:
   - multi-word PHRASE first (F790): `solanum lycopersicum` → tomato (the binomial appears in tomato's lead), in PROMPT order so the phrase matches;
   - else the longest single salient token that is itself an article (water, solanum);
   - serve the abstract-full LEAD, with an honest note: *"this is the LEAD of the simplewiki article — the fullest text I hold; I don't store full article bodies yet."*
   - `ARTICLE_RE` also sets `want_abstract` so an article ask gets the ≤3-sentence lead, not the one-line gloss.

## Verified (live, rc166)
- "would you give us the wiki article for solanum lycopersicum?" → `[siona · article] tomato: The tomato (Solanum lycopersicum) is a vegetable/botanical fruit … very good for health.` (binomial → tomato, abstract-full lead, honest note). ✓
- "show me the wiki article about water" → `[siona · article] water: It is clear, has no taste or smell …` (single-token article). ✓
- "show me more about it" (after tomato) → `[anaphora: it → tomato]` → tomato's fuller abstract + relations + spectral-neighbourhood facet. ✓ (context no longer poisoned: the prior topics are real — tomatoes/solanum/tomato — not scaffold.)

## Honest scope
- Siona serves the **LEAD** (abstract-full, ≤3 sentences), NOT the full article body — she does not store full bodies. The route says so. The genuine full-body recall is the F805–F809 deterministic-walk path: ingest article bodies (from the cached `articles.jsonl`) → store the shape-graph → reconstruct exactly by walking (storage-by-seed, F809). That ingest + wire-in is the next step.
- `show`/`list` are occasionally content (the TV-show concept); declaring them request operators is the right default (F770) — the rare "define the word show" loses, recoverable by phrasing. `wiki`/`article`/`page` are medium-meta, safely operators.

## Verdict
Both reported bugs were the operators/operands discipline plus a missing route: request-meta words (`show`/`wiki`/`article`/`page`/`list`) were routed as topics — misrouting turn 3 (and poisoning the context) and blocking turn 4's anaphora. Stoplisting them (they are request operators) fixes the context and lets anaphora fire; a new ARTICLE route resolves the subject (binomial → tomato via F790) and serves the abstract-full LEAD, honestly flagged as the lead not the full body. Deployed live (rc166). Full-body recall remains the F805–F809 walk path (next: ingest bodies + wire the deterministic walk in).
