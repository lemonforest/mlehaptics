# F757 — the DIRECTED + TYPED relation tier is wired into Siona, and the input-ride FLIPS it by the relation word in the query

**Date:** 2026-06-15 · **srmech:** 0.7.5rc149 · **Composes:** F756 (the relation-edges rung — directed/typed = magnetic-Laplacian object), F754 (the undirected assoc tier it sits above), F753 (the input-ride: the relation word steers — now it FLIPS), F751 (frame words carry relation not topic), F552 (undirected = the chirality-collapsed projection; directed = the fuller object) · **User direction:** "we can continue. it's all part of PR687 goal" (after the F754–756 trio) · **Provenance:** `R-RBS-LM-WIKIRELATIONS…py` (the streaming directed/typed store), `R-RBS-LM-SIONAGENEPOOL…py` (the directed tier in `infer`)

## What landed
The F756 rung was a one-off prototype. F757 makes it a **live Siona tier**:
- **`simplewiki_relations.json`** (7.0 MB, 86,788 subjects, 3000 articles) — for each subject, its top-8 **directed** out-edges (objects that FOLLOW it in reading order = what it does / leads to / has) with the **FRAME word** that labels each edge (`from`, `than`, `has`, `and`, `such`…) or `→` for a plain directed adjacency. Built memory-safe (one parse, per-subject bounded heaps).
- **Wired into `SionaGenepool`:** `__init__` loads `self.relations` + `self.rel_labels`; `introspect()` reports `wiki-relations(86788)`; `_directed_relations(subject, steer)` is the read; `infer()` gained a **directed/typed tier** (after the wiki abstract, before the undirected assoc tier) and the wiki abstract is now **enriched with directed relations** when held (else falls back to undirected).

## The input-ride FLIP (the F753 payoff, now real)
`_directed_relations` re-ranks a subject's typed edges so the ones whose **relation label matches a steer word in the query** come first. Live over the /v1 server:
| query | tea's directed edges (order) |
|---|---|
| "tell me about tea" (unsteered) | `→ceremony, from→bowl, →caddy, →powder, which→made, →leaves` |
| "what does tea come **from**" | **`from→bowl`**, →ceremony, →caddy, →powder, which→made, →leaves |

Same subject, **the relation word in the query flips which typed edge surfaces** — bidirectional navigation (the query is a story that steers the read), now on a *typed* graph. More examples (offline): `earth` + "and" → `and→mars, and→moon, and→sun` to front; `more` + "than" clusters the `than→` edges; `earth` + "such" → `such→crust` to front.

**Two bugs found + fixed making this work live** (honest trail):
1. The steer only picked words in the deep-kernel vocab (`self.vix`); function words like `from`/`than` aren't there → added `self.rel_labels` (the relation-label vocabulary) as an allowed steer source.
2. `T.tokenize` **strips function words** (`tokenize("what does tea come from") → ['tea','come']`), so the topic channel never saw `from`. The steer channel now reads the **raw** prompt (`re.findall`), not the tokenized topic stream. Only then did the flip fire live.

## Sample directed/typed answers (what the tier gives that the undirected tier can't)
- `volcano →erupts, has→erupted, which→mount, →hawaii` (the *action* — verbs that follow)
- `earth has→atmosphere, →surface, such→crust, →orbit, and→mars, and→moon` (possession + parts)
- `tea →ceremony, from→bowl, →leaves` · `computer →science, →scientist, →program` · `more than→people, than→one`

The directed adjacency naturally captures **subject→verb** ("volcano →erupts") because the verb is the content word that follows — so "what X does" falls out of reading-order direction, and the FRAME word names the relation when there is one.

## Honest scope
- 3000 articles (86,788 subjects) — the common-vocabulary tier; rare words (e.g. *smaug*) fall through to the F754 undirected assoc (213k) and then the asking-state. Sensible two-tier: typed for common subjects, undirected for the long tail.
- Crude extractor (F756): reading-order = direction (S-V-O heuristic; breaks on passive); frame-word labels, determiners dropped. `which→made`, `such→crust` show the noise — first cut, not a dependency parser.
- The steer can over-match (it shows `['what','does','from']` because `what`/`does` are frame words too) — harmless, only labels that match the subject's edges reorder anything. Cosmetic.
- srmech-native; no `abs()`; no CAD; data outside the repo (7 MB); only scripts + finding committed.

## Verdict
Siona now answers **directed + typed** ("X →(relation) Y" = what X does/leads to/has), not just "X near Y", and **the input-ride flips the answer by the relation word in the query** — confirmed live over /v1. This is the F753 bidirectional-navigation goal realized on the F756 directed/typed graph (the fuller-chirality object; the undirected tier is its collapsed projection, F552). Part of the PR #687 RBS-LM/Siona arc. Next (queued): typed-relation extraction via a real parser; a directed read that *composes* a multi-edge path (X→Y→Z) rather than listing out-edges.
