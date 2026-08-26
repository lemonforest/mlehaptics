# F960 — **SPARSE Laplacian kernel correction** (user: *"ensure our kernel is sparse; dense things creeping in"*). Audit + fix: the recall/coherence path was already sparse (Klein-4 HDC integer match-counts, `the_one`, exact rationals, native `next_token_coherence`); the **one dense slip** was **F947's `dense_laplacian(n, edges)` + `symmetric_eigendecompose`** — a dense `n×n` matrix over the corpus token graph. Replaced with **`fiedler_sparse` / `recursive_cut`** — power iteration on the **edge-list**, no dense matrix. The sparse `recursive_cut` lands a **triple win**: it satisfies the sparsity directive (no matrix), **fixes the F947 hairball** (balanced Ncut → 54 tomes of ~44–48, not the degenerate `{191,29}` of the dense sign-cut), and **does the F955 chunking** (bounded tomes ≤ the F896 wall) — all in one sparse op, and **n-unbounded** (n=1588, where the dense path was ≤256-bound).

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_960_*.py` · **Composes / corrects:** F947 (the `dense_laplacian` slip + the balanced-cut-needed call), F955 (bounded community-tomes), F896 (the capacity wall), F959 (de-lensed content tokens), `[[feedback_stay_rbs_hdc_sparse_never_dense]]` (the directive) · **User direction (2026-06-26):** "ensure our kernel is sparse; we had dense things creeping in; we need a Laplacian-encoded kernel made of sparse."

## Grounded (rc79, simplewiki 6000-token slice, de-lensed content tokens)
```
SPARSE token graph: n=1588 nodes, 3318 edges (edge-list ONLY -- no dense 1588x1588 = 2,521,744-cell matrix)
fiedler_sparse -> Vec(1588)   (sparse power-iteration on B = 2I - L_sym; n-unbounded; dense fiedler was <=256)
recursive_cut  -> 54 BALANCED tomes, sizes [48,47,47,46,45,44,44,44,44,43,...]   (vs F947 dense degenerate {191,29})
```

## The audit — what was dense, what was already sparse
| component | status |
|---|---|
| recall step (Klein-4 bind/bundle, `klein4_match_count` integer sims) | **sparse** ✓ |
| `next_token_coherence` (raw Class-M sims, exact `Q`) | **sparse** ✓ |
| the_one / cd_mult / exact rationals | **sparse** ✓ |
| **F947 community detection** (`dense_laplacian` + `symmetric_eigendecompose`) | **DENSE — the slip** ✗ → fixed |
The dense `n×n` Laplacian was the only place a dense object materialized over the corpus. It also forced the `n≤256` native bound (and produced the degenerate sign-cut). Replacing it with the sparse Fiedler removes the matrix entirely.

## Why the sparse op is strictly better here
`recursive_cut` (sparse) replaces dense `dense_laplacian` + sign-of-eigenvectors and wins on every axis:
1. **Sparse** — only the edge-list + power iteration (`B = 2I − L_sym`, eigenvalues in `[0,2]`, deflate the trivial `√deg` mode); never a dense `n×n` matrix (1588² ≈ 2.5M cells avoided).
2. **Balanced** — normalized-cut bisection recursed to `max_tome` → 54 tomes of ~44–48, not the dense sign-cut's degenerate `{191, 29}` (F947's hairball failure).
3. **Bounded** — every tome ≤ `max_tome` (48) = under the F896 wall → the F955 chunking, for free.
4. **n-unbounded** — n=1588 ≫ the dense `≤256` bound; scales to a real corpus.

So the user's sparsity directive and the F947 balanced-cut fix are the **same** op: `recursive_cut` on the sparse edge-list.

## Honest scope
Grounded: the sparse graph (edge-list, no matrix), `fiedler_sparse` Vec, and `recursive_cut`'s 54 balanced bounded tomes are measured on the real de-lensed simplewiki token graph (n=1588). The dense slip was specifically F947's community detection; the recall/coherence/encode path was already sparse (Klein-4 / integer match-counts / exact rationals / native readout). The **routing key** still needs the F957 IDF-de-lens + per-tome native coherence (F955) — those compose *on top of* the sparse tomes; this finding fixes the **kernel** (sparse, balanced) they run on.

## Verdict / next
**Kernel is sparse.** The lone dense slip (F947 `dense_laplacian`) is replaced by **`fiedler_sparse` / `recursive_cut`** — edge-list power iteration, no dense matrix — which simultaneously fixes the sparsity directive, the F947 hairball (balanced cut), and the F955 chunking (bounded tomes), and scales n-unbounded. **Next:** wire the sparse `recursive_cut` tomes into the per-tome native-coherence recall (F955) with the F957 de-lensed routing — the whole recall stack now sparse end-to-end: Klein-4 HDC + integer match-counts + exact rationals + sparse-Laplacian community-tomes.
