# F947 (research note, spectral routing) — **the chunking *principle* holds (source-routing = 100%, margin 0.115), but the spectral *partition* fails on word co-occurrence — it's a hairball.** On the real-corpus token graph (220 tokens, 699 co-occurrence edges, 717 directed relationships), the **sign-of-eigenvector** spectral partition is **degenerate**: 4 communities come out `{2: 191, 3: 29}` (two empty), so the "community-tomes" barely chunk and match the single bundle (**58%** true-next accuracy, margin **~0.004**). **De-lensing** (drop the 18 function-word hubs before partitioning, F782) lifts accuracy to **82%** — but the content subgraph *still* collapses to one community (`{-1: 18, 7: 202}`), so the margin stays **~0.005** (the 202-token content tome is still saturated). Meanwhile **source-routing** (the fine-grained limit) gives **100%** at margin **0.115** — proving the chunking principle is right; the *partition method* is the failure.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RBS-LM / Siona · **Probe:** `R-RBS-LM-FINDING_947_*.py` · **Composes:** F946 (the frequency-prior saturation), F944/F945 (chunk + trichotomy), F778 (community-tome routing), F781/F782 (cosmic-web hub-lensing / IDF-de-lensing), F768 (aboutness-gate) · **User direction (2026-06-26):** "then with full spectral routing … we might surface research notes."

## Measured (real simplewiki, 220-token graph, Class-L Laplacian)
| routing | true-next acc | mean margin | top₁ above floor |
|---|---|---|---|
| **single bundle** | 58% | 0.004 | 0.022 |
| **spectral 4-comm** (sign-of-eigvec) | 58% | 0.005 | 0.023 |
| **de-lensed spectral 8-comm** (drop 18 hubs) | **82%** | 0.005 | 0.024 |
| **source-routed** (fine-grained limit) | **100%** | **0.115** | **0.341** |

Spectral community sizes: raw `{2:191, 3:29}`; de-lensed `{hubs:18, 7:202}` — **both degenerate** (one giant community).

## The research note (what surfaced)
1. **Word co-occurrence is a hairball — sign-of-eigenvector partitioning can't split it.** Function words connect *everything* (the F782 hub-lensing), so the Fiedler sign-cut puts ~all tokens in one community. Even after **dropping** the 18 hubs, the *content* subgraph still collapses to one octant — the remaining content tokens are still densely cross-linked. So **naive F778 spectral routing does not chunk** a word-bigram graph.
2. **The chunking principle is sound — the partition is the bug.** Source-routing (each prev its own tome) gives **100%** accuracy at margin **0.115** and top₁ **0.34** above floor — fully resolved, confident. So bounded tomes *do* recover context (F944); the open problem is *producing* bounded, balanced tomes from the graph.
3. **De-lensing helps the relationships, not the partition.** Routing the hub-prev relationships to their own tome lifts accuracy 58→82% (less function-word crosstalk in the content tome), but the content tome is still one big saturated bundle (margin ~0) — the partition never split it. So **de-lensing (F782) and balanced-partitioning are two separate needs**, and we only got the first.

## The fix (next-question, handed forward)
To make spectral community-tomes actually chunk a word graph:
- **Use a balanced k-way cut, not sign-of-eigenvectors.** srmech ships `laplacian.normalized_cut_bisect` / `recursive_cut` / `three_fold_eigvec_groups` — these target *balanced* cuts (Ncut), which the degenerate sign-partition does not. Recurse until each tome is under the F896 capacity (≈ the source-routing granularity that already hits 100%).
- **De-lens the edge *weights* (IDF), not just drop nodes (F782).** Weight each co-occurrence edge by `1/√(f_a·f_b)` so hub edges stop dominating the spectrum, *then* cut — so the communities reflect topical structure, not raw degree.
- **Target tome size, not community count.** The signal that matters is the per-step margin (F943); recurse the cut until margins clear the floor. Source-routing proves the target exists.

## Honest scope
Measured on a 220-token real-corpus graph; real Class-L Laplacian (`dense_laplacian` + `symmetric_eigendecompose`) + real Klein-4 recall. The degenerate partition is the sign-of-eigvec method on a hairball graph — **not** a refutation of community-tome routing (source-routing = 100% proves the principle); it's a finding that the *partition method* must be balanced-Ncut + IDF-de-lensed. The balanced-cut fix is the next build (srmech has the ops); handed forward.

## Verdict / next
**Surfaced:** full spectral routing via sign-of-eigenvectors **fails on word co-occurrence** (hairball → one giant community, no chunking, no margin recovery), even after hub-de-lensing; but **source-routing = 100% at real margin** proves the chunking principle and the existence of the target. The two real needs are **balanced k-way cut** (`normalized_cut_bisect`/`recursive_cut`, not sign-cut) **+ IDF edge de-lensing** (F782) — and they are *separate* from each other. **Next:** redo the partition with `recursive_cut` over IDF-weighted edges, recursing until each tome clears the F896 margin floor (the source-routing granularity is the proof it converges).
