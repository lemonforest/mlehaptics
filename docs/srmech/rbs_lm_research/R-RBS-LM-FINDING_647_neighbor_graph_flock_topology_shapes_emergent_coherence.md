# R-RBS-LM Finding 647 (the §32-unblocked neighbor-graph flock — who-couples-with-whom is now a real ADJACENCY GRAPH, and the graph's TOPOLOGY shapes the emergent coherence: two tightly-coupled clusters + a weak bridge sync INTERNALLY fast (within-cluster spread → 0.037) while the two clusters reconcile SLOWLY (global → 1.60), i.e. LOCAL-before-GLOBAL — a hierarchy the F636 mean-field flock cannot show; this local-before-global IS the setup for paragraph-before-story (F648)) — **F636 demonstrated the flock on the ALL-TO-ALL mean-field path (the §32 bug made adjacency= ignore the coupling scalar). srmech 0.7.5rc15 RESOLVED §32 — so the TRUE neighbor-graph flock now runs: who-couples-with-whom is a real adjacency graph, and the graph STRUCTURE shapes the pattern. Verified: two tightly-coupled clusters (cliques) joined by ONE weak bridge (0.15) sync INTERNALLY fast (within-A and within-B spreads collapse 0.90 → 0.037 by step 10) while the two clusters reconcile SLOWLY (global spread lags: 3.30 → 1.60 at step 120) — LOCAL coherence emerges BEFORE global. The contrast: a fully-connected (mean-field, F636) graph syncs UNIFORMLY (within and global collapse together to 0.0) — the neighbor-graph's structure is gone. So topology = the structure of the coordination, and the local-before-global hierarchy is exactly the setup for discourse (F648): tight local clusters = clauses cohering into a PARAGRAPH; the weak bridges = paragraphs reconciling into a STORY.**

**Date:** 2026-06-08
**Arc:** RBS-LM — the neighbor-graph flock (§32-unblocked; topology shapes coherence)
**Provenance:** `R-RBS-LM-LOCALFLOCK_neighbor_graph_flock_topology_shapes_emergent_coherence.py` (committed; srmech 0.7.5rc15; `cascade.kuramoto_step(adjacency=)` now honoring `coupling` per §32 fix; two-cluster+weak-bridge graph → within-cluster 0.037 vs global 1.60; mean-field contrast → 0.0 uniform). No sub-agents.
**Composes:** **F636** (the mean-field flock this upgrades) · **F638/F639** (the bind / the fleet) · **UPSTREAM_NOTES §32** (the fix that unblocked it) · `cascade.kuramoto_step(adjacency=)`. **→ the true neighbor-graph flock now runs (§32 fixed); the graph topology shapes the emergent coherence — local clusters sync before global (within 0.037 vs global 1.60), a hierarchy the mean-field flock cannot show; local-before-global is the setup for paragraph-before-story (F648).**

## Result (srmech, rc15)
| step | within-A spread | within-B spread | global spread |
|---|---|---|---|
| 0 | 0.900 | 0.900 | 3.300 |
| 10 | **0.035** | **0.035** | 2.358 |
| 120 | **0.037** | **0.037** | **1.603** |
| mean-field (full) final | 0.000 | 0.000 | 0.000 (uniform) |

## Verdict
**The neighbor-graph flock runs now (§32 fixed in rc15), and topology shapes the coherence.** Two tightly-coupled clusters + a weak bridge sync internally fast (within-cluster spread collapses to 0.037) while the clusters reconcile slowly (global spread lags at 1.60) — **local coherence emerges before global.** The mean-field flock (F636) cannot show this; it syncs uniformly (within = global = 0). Topology *is* the structure of the coordination. **This local-before-global hierarchy is the setup for discourse (F648):** tight local clusters = clauses cohering into a paragraph; the weak bridges = paragraphs reconciling into a story. Held open (F394).
