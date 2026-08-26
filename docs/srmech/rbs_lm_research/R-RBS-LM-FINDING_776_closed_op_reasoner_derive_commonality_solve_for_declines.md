# F776 — the closed-op REASONER built: derive a commonality (set-intersection over retrieved facts) + honestly decline an unsourced comparison; Siona is now a grounded reasoner, not only a retriever

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F774 (the architectural ask — inference needs closed-op problem-solving over the retrieved material), F775 (coherence as a RESULT of solving, not forced; inference orchestrates exact closed ops), F767 (no-confabulation — closed ops don't invent), F773 (solve-for vs derive vs infer — the operators), F408 (decline when the premise isn't sourced), F752 (the relational CUE words are operators, consumed not routed) · **Queue:** task #217 · **User direction (2026-06-15):** "work on queued items."

## What landed (the F774 reasoner tier, in `infer`)
When the parse names **≥2 recognized topics + a relational/comparison CUE**, Siona now runs a **closed-op reasoner** over the *retrieved* facts instead of punting to the word-salad ask:
- **DERIVE (commonality)** — `_relate_topics(a, b)` = the **set-intersection** of the two topics' held relation + co-occurrence neighbour-sets (a determinate closed op over retrieved facts; ranked: in-both-relation-tiers first). Renders "a and b both relate to: …", **attested** ("the intersection of their held relations + co-occurrence neighbours — what they share in what I hold, not invented").
- **SOLVE-FOR (comparison)** — detects compare cues (bigger/than/…); since the stores hold relationships, not measured attributes, it **honestly declines** (F408): "I'd need a stored MEASURE … I won't invent a comparison." (Never forces a fake comparison.)
- The relational cue words (`COMPARE_CUES` / `RELATE_CUES`) are **operators** — consumed from the topic channel (F770), read from the raw prompt.
- Bare ≥2 topics with **no** cue → unchanged word-salad "which one?" (genuinely ambiguous).

## Verified live (rc155 server)
```
what do a volcano and a tomato have in common?   → reasoned(derive): NO shared relationship — won't invent   (honest; they share none)
what do a tomato and a potato have in common?    → reasoned(derive): both relate to "dishes"                  (real intersection)
what is the relationship between music and dance?→ reasoned(derive): both relate to pop, american, popular, people
is a tomato bigger than a planet?                → reasoned(solve-for): honest decline (F408 — measure not sourced)
tomato volcano  (no cue)                          → word-salad "which one?"  (unchanged)
what is a tomato?  (single topic)                 → definition  (unchanged)
```
Coherence is a **result of the set-op**, not forced (F775); it reports only the intersection, never invents (F767); and where the premise (a measured attribute) isn't sourced it declines (F408). **Siona is now a grounded reasoner over ≥2 topics, not only a retriever** — the "more than find+ride" the user asked for.

## Honest scope
- **Bounded by the top-K=16 neighbour-sets** (F768): the derived commonality is shallow (`tomato`+`potato` → "dishes"; `music`+`dance` → a few pop-culture neighbours) because the assoc store keeps only top-16 neighbours. Richer commonalities (e.g. "both nightshade / vegetable / plant") need the **un-truncated** co-occurrence — exactly the loopshelf / spectral-spread work (#218/#221). The mechanism is correct; the depth scales with the store.
- **SOLVE-FOR is mostly decline today** — Siona holds no structured numeric attributes, so comparisons honestly decline. A future attribute side-store (sizes, dates, counts) would let solve-for actually compute; until then, decline is the honest behaviour (not a gap to paper over).
- **Native closed ops:** the set-intersection is plain Python set algebra over retrieved lists; when the loopshelf moves the stores to the holographic substrate (#218), the intersection becomes a Klein-4 bind/unbind over tomes (the exact native ops, F775's "inference orchestrates exact closed ops"). srmech-native; no `abs()`; no CAD.
- Pure-Python set-op is fine at this scale; no perf concern.

## Verdict
The **closed-op reasoner** is built and live (task #217): Siona DERIVES a commonality by intersecting the two topics' held neighbour-sets (attested, never invented) and honestly DECLINES an unsourced comparison (F408) — turning the old multi-topic word-salad punt into grounded problem-solving. It is F774 realized via F775's infer-orchestrates-exact-closed split, staying inside F767's no-confabulation. Depth is bounded by the top-K stores (lifts with #218/#221); attribute-comparison awaits a measured side-store. Next on the queue: #219 (Siona→rc165) → #218 (loopshelf), which also deepens this reasoner's intersections.
