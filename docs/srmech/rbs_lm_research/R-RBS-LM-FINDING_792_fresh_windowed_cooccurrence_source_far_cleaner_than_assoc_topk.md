# F792 — the FRESH windowed co-occurrence source graph is dramatically cleaner than the pre-built assoc top-K (the #3 quality lever, confirmed): clean tomes (cuisine, breeds, eruptions, computing) replace the assoc tree's genus-name / extraction-artifact noise — deployed as Siona's nav source

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F789/F791 (the clump + nav — this swaps the SOURCE graph), F786 (de-lensing), F758/§50/§17 (the streaming-co-occurrence question — the full-vocab scaling fix) · **User direction (2026-06-16):** "try also with fresh windowed co-occurrence source graph." · **Provenance:** `R-RBS-LM-FRESHCLUMP_…py` → `simplewiki_tome_tree_fresh.json`.

## What changed
F789/F791 sourced the clump graph from the **pre-built assoc top-K** (word→top-K neighbours) — which carries **extraction artifacts** (`actornominated`, `bouncedecember`) and isn't a clean windowed co-occurrence, so the tomes were noisy (`tomato` → a plant-GENUS cluster; ZOOM/web full of foreign/tangential tokens). `R-RBS-LM-FRESHCLUMP` instead builds the source by a **FRESH windowed co-occurrence pass over the corpus** (srmech `text.tokenize` + `text.cooccurrence_edges`, window 6), df-selected content band, IDF-weighted + top-20 sparsified, then the same native §51 clump.

## Result — far cleaner (28k vocab / 22k articles)
| word | assoc tree (F791) | **fresh source (F792)** |
|---|---|---|
| ketchup | (usage sub-clump) | **{cuisine, tomato, salad, sauces, onions, lettuce}** · web `food~cuisine` |
| tomato | plant-genus `{cystopteris, cyrtanthus…}` | **{cuisine, salad, sauces, onions, lettuce, ketchup}** |
| dog | canid genera only | **{bred, fluffy, barking, breeder, gentle}** · web `dog~dogs` |
| volcano | + foreign tokens | **{erupts, debris, landforms, etna}** · web `mount~volcano` |
| star | + `intermediajune` junk | **{hollywood, anthology, moore's}** · web `star~wars` |
| computer | (hub-dropped) | **{execute, aided, pointer, fetch, eniac}** · web `computer~computers` |

The extraction artifacts are **gone** (clean tokenization); probes are coherent and the web bridges are meaningful (`food~cuisine`, `earth~planet`, `star~wars`, `bass~guitar`, `mount~volcano`). **The #3 hypothesis is confirmed: the source graph was the quality bottleneck, not the method.**

## Honest tradeoffs
- **RAM:** the fresh pass materialises the full raw edge list — **8.7M edges / 2.1 GB at 12k vocab; 10M / 2.4 GB at 28k.** So a **full-90k-vocab fresh** build is NOT tractable this way — it needs a **streaming / bounded co-occurrence** (return top-K per node without materialising all edges) — the same gap as §50/§17. That's the full-vocab scaling fix (an upstream ask).
- **Coverage:** the fresh tree is the common-word **core** (28k from a 22k-article sample), vs the assoc tree's full 90k. `music`/`france` are very-high-df → dropped as top-200 hubs (still answerable via abstracts; just not nav-placed). So fresh = cleaner-but-core; assoc = noisier-but-full.
- **within-fraction 7.1%** — low because MAXTOME=12 over a dense graph fragments topics into many sibling tomes (the F785 small-tome artifact); the RIDE/ZOOM are still coherent (topics live across siblings, reconnected by the tree+web). A larger MAXTOME would raise it.
- Sample (22k articles), not the full corpus; srmech-native; no abs/CAD; outside the repo.

## Deployment
Siona's nav source repointed to the **fresh** tree (`simplewiki_tome_tree_fresh.json`) — clean navigation for the common-word core; the assoc 90k tree remains as the fuller-but-noisier alternative. (Definition/abstract/contents tiers cover every word regardless of nav-band membership.)

## Verdict
The **fresh windowed co-occurrence source is dramatically cleaner** than the assoc top-K — confirming the source was the quality bottleneck. Tomes are coherent (cuisine, breeds, eruptions, computing) with meaningful web bridges, deployed as Siona's navigation source for the common-word core. The honest limits: it's a 28k-core / 22k-article-sample (full-90k fresh needs a **streaming co-occurrence** to avoid the materialised-edge-list RAM — the upstream scaling fix), and small-tome fragmentation keeps within-fraction low (MAXTOME knob). The navigable smallwiki is now clean where it's covered; full-vocab-clean is gated on streaming co-occurrence.
