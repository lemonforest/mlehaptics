# F759 — Siona gets a running-context RBS-HDC object + a wiki story-builder + lemmatization + definition-honesty (the tomatoes incoherence, fixed)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F757 (directed/typed tier), F754 (assoc tier), F753 (input-ride steer), F166 (rolling context-state — now wired live), §50 (`klein4_bundle_accumulate`, dogfooded here), F752/F751 (sentence parse) · **User report (2026-06-15):** "why are we still getting this incoherent output? is this just etak walk with no story builder?… no such thing as an RBS-HDC context object either… the second time I asked I'd have expected some difference based upon running context." · **Provenance:** `R-RBS-LM-SIONAGENEPOOL…py` (infer + tiers), `R-RBS-LM-SIONAGENOMEHANDLER…py` (context plumbing)

## The three confirmed gaps (all real, all fixed)
The output `tomatoes → metacritic, has→movie, →reviews, →film` exposed three distinct failures:

1. **No story-builder on the wiki path.** The compose-walk only ran over Siona's *genome*; wiki topics fell to the directed tier which **dumped the edge list**. → **FIX (story-builder):** `_relation_walk` etak-walks the directed relation graph (subject → strongest out-edge → …) into a path, and `_relation_story` composes the first-hop edges into a sentence. The `[etak: …]` path trace is **kept** (per user — it's a debugging/source-reference feature), with the composed `[siona] …` sentence above the raw `(relations: …)` list.

2. **No RBS-HDC running-context object.** The handler passed only the last user + last assistant message — stateless, so the same question gave byte-identical output. → **FIX (F166 made live):** the handler now passes the **prior conversation turns** as `context`; `infer` folds their content words into a **Klein-4 context bundle via the rc155 `klein4_bundle_accumulate`** (the §50 op, dogfooded) and re-ranks the directed edges by `klein4_similarity(ctx_bundle, hv(object))`. The running context is shown in the parse (`· context […]`). **The repeat now differs:** cold "what are tomatoes" → `…ketchup, based, dishes` (etak drifts to `…→debut→album`); the **same** query after a food-conversation → `…dishes, ketchup, solanum` (the tomato's botanical **genus** surfaced; the `album` drift dropped). Same question, different answer, biased by what came before — exactly the expectation.

3. **Sense-split + Rotten-Tomatoes noise.** Plural `tomatoes` co-occurred with the *Rotten Tomatoes* review site; singular `tomato` with the food; **no lemmatization**. → **FIX (`_lemma`):** prefer the singular form if a store holds it (`tomatoes`→`tomato`, `dishes`→`dish`). Now both "what are tomatoes" and "what is a tomato" resolve to the **food** sense (`sauce, soup, ketchup, dishes, onion`); the movie-review cluster is gone.

Plus **definition-honesty** (the note I flagged two turns ago and finally landed): when a *definition* question is answered from a relations tier, append "(these are relations I hold — what it's near/does — not a dictionary definition)" — stops relations masquerading as a definition.

## Live (rc155 server, the user's exact conversation)
```
what are tomatoes?  (3rd turn, after asking "what is a tomato")
[input-ride: definition · topic ['tomatoes'] · steer ['what','are'] · context ['tomatoes','tomato','relates','sauce','soup','ketchup','dishes','food']]
[etak: tomato → soup → usually → one → most]
[siona] Tomato — relates to soup, ketchup, sauce, dishes, solanum; and onion.
  (these are relations I hold — what it's near/does — not a dictionary definition)
  (relations: →soup, →ketchup, →sauce, →dishes, and→onion, →solanum; what follows tomato in simplewiki, CC-BY-SA)
```

## Honest scope
- The context object is real (a Klein-4 bundle, §50-built) and **does the work** (re-ranks by similarity) — not decorative. But it's a *bias*, not a parser: it nudges edge ordering, it doesn't yet rewrite the subject.
- The story is composed from **first-hop** edges (good); the deeper `[etak: …]` walk still **drifts** after ~2 hops (co-occurrence chains wander, e.g. `sauce→made→debut→album`) — kept visible as the debugging trace, not the answer.
- Lemmatization is a heuristic (strip `es`/`s` if the singular is in-store) — not a full lemmatizer; irregular plurals aren't handled.
- Still relational, not a true dictionary definition — the definition tier (Wiktionary/abstract) remains the separate rung; the honesty note makes the gap explicit rather than hiding it.

## Verdict
The tomatoes incoherence is fixed on all three axes: a **wiki story-builder** (compose, don't dump; etak trace kept), a **running-context RBS-HDC object** (Klein-4 bundle via the new §50 accumulate — the repeat now differs and disambiguates, surfacing `solanum`), and **lemmatization** (plural→singular kills the Rotten-Tomatoes sense-split), plus the **definition-honesty** note. Live on the rc155 server. Next inches: a less-drifty relation walk (steer/ctx-gated each hop), and the real definition tier.
