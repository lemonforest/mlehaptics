# F760 — the two F759 next-inches: a real DEFINITION tier (216k lead-sentence glosses) + a STEER-GATED relation walk (no drift)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F759 (running-context + story-builder + lemma; the two open next-inches), F757/F754 (relational tiers), F584/F119 (exact + holographic two-tier), §35/F698 (wiki markup-strip discipline) · **User direction (2026-06-15):** "next inches are a steer-gated (less drifty) relation walk and a real definition tier now" · **Provenance:** `R-RBS-LM-WIKIGLOSS…py` (the gloss store), `R-RBS-LM-SIONAGENEPOOL…py` (the tier + gated walk)

## Inch 1 — the real DEFINITION tier
The lead sentence of a simplewiki article IS a definition. `R-RBS-LM-WIKIGLOSS` extracts the first **markup-free** sentence per article → `simplewiki_glosses.json` (**216,676 glosses, 26.5 MB**, 240,881 articles, 20.6 s). Wired into Siona as the `wiki·definition` side-store; `infer()` gained a **definition tier** that fires after the deep-kernel walk and **before** the relations tiers, lemmatized (`tomatoes`→`tomato`).
- **Live result (the original complaint, fixed):** both "what is a tomato?" and "what are tomatoes?" now return *"tomato: The tomato (Solanum lycopersicum) is a vegetable/botanical fruit, or specifically, a berry…"* — a real definition, not a relations dump or the Rotten-Tomatoes movie noise. `dragon` → "There are stories about dragons in Chinese culture…". The honesty-note ("not a dictionary definition") now only appears when we genuinely *lack* a gloss and fall through to relations.
- Architecture: this is the **exact definition tier** of the F584/F119 two-tier — the definition side-store + the relational side-stores (assoc/relations) + the genome (self). Definitions answer "what X IS"; relations answer "what X is near/does".

## Inch 2 — the STEER-GATED relation walk (drift fixed)
`_relation_walk` was drifting (`tomato → sauce → made → debut → album` — co-occurrence chains wander). The fix: each hop may only step to a node **within the subject's own neighbourhood ∪ the running context** (`anchor`). Result: `tomato → sauce` (stops at the topic boundary) instead of wandering to `album`. The gate trades walk-DEPTH for COHERENCE — an honest, deliberate tradeoff (the walk is now short + on-topic rather than long + drifting). The `[etak: …]` trace stays visible (debugging/source, per user).

## Honest scope
- Gloss extraction is a heuristic (first markup-free sentence) — most are clean (`tomato`/`computer`/`earth`/`music`/`dragon`); a minority carry artifacts (`volcano` → "VolcanoesThe plural of volcano…", a heading-merge). Good first cut; not a parser.
- Words in Siona's own genome (e.g. `music`) still route to the **deep kernel first** (her notebooks take precedence over the wiki definition) — defensible (self before external knowledge), occasionally tangential.
- The gated walk is now shallow by design (coherence over depth); a similarity-graded gate (allow farther hops if still context-consistent) is the next refinement.
- All side-stores (def/assoc/relations) live outside the repo; scripts + findings committed. srmech-native; no `abs()`; no CAD.

## Verdict
Both F759 next-inches landed: a **real definition tier** (216k lead-sentence glosses — "what is a tomato?" finally answers with a definition) and a **steer-gated relation walk** (no more `→ album` drift; stays in the subject's topic/context). Live on the rc155 server. The tomatoes incoherence arc (F757→F759→F760) is closed: lemmatized sense, real definition, context-aware, non-drifty, with the etak trace kept for debugging.
