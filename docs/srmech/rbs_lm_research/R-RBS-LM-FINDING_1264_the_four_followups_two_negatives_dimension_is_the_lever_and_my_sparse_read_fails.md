# F1264 — F1263's four follow-ups, run: **(2) storage is ~5.5× the bundle, not 4×, and the compressible axis is the VALUE RANGE not occupancy. (3) my margin-based sparse read FAILS — the O(N·dim) probe cost is not reducible that way. (1) the count structure's horizon is a function of N/dim, not an absolute N. (4) DIMENSION is the working lever — recall 0.200 → 0.800 across an 8× dim sweep at fixed N.** Two positives, two negatives, and one of the negatives invalidated my own first attempt at (4).

**User (2026-07-20):** *"let's do next 4"* — the follow-ups F1263 queued. Harness `R-RBS-LM-COUNTHORIZON_…py`, srmech **0.9.0rc288**.

## (2) SPARSITY — the 4× estimate was wrong in both directions
| N (dim=1024) | occupied cells |
|---|---|
| 256 | 4096 / 4096 (100 %) |
| 2000 | 4096 / 4096 (100 %) |
| 4000 | 4096 / 4096 (100 %) |

**The matrix is 100 % DENSE in cells** — all four sectors fill once N ≫ 4, so there is no occupancy sparsity to exploit. My "likely compressible — most coordinates concentrate" guess in F1263 was wrong.

**But the compressible axis is the VALUE RANGE.** Max cell value at N=4000 is **1100**, so **11 bits/cell suffices**, not 32 or 64. Storage is `dim × 4 × ceil(log2 N)` bits:

- bundle: 1024 B
- counts at N=4000: **5.5 KB** (vs **32 KB** if stored as naive 64-bit ints)

So the honest figure is **~5.5× the bundle and growing as log N** — worse than my 4× claim, far better than the naive-int 32×.

## (3) THE SPARSE READ FAILS — my own idea, refuted
Design was: keep the full store, read only the *decisive* coordinates (`margin[i] = top count − second count`), i.e. top-K as a READ never a storage cut. Validated against the full read at N=512, dim=1024:

| top-M | recall | **agreement with full read** |
|---|---|---|
| 1024 (all) | 0.333 | 1.000 |
| 512 | 0.333 | **0.429** |
| 256 | 0.048 | 0.143 |
| 128 | 0.095 | 0.095 |
| 64 | 0.000 | 0.000 |

At M=512 the recall coincidentally matches while **disagreeing with the full read 57 % of the time** — it is not the same computation. Below that it collapses outright.

**Why, and this is the transferable part:** with N items over 4 sectors, each coordinate sees ≈N/4 votes per sector with fluctuation ≈√(N/4). **Every coordinate's margin is the same random fluctuation** — the ranking is noise. There is no globally-decisive subset to find, *because the near-tiedness IS the collision loss*. A per-query index (coordinates where the *target* stands out) might work, but a global margin index provably cannot. **The O(N·dim) probe cost stands.**

## (1) THE HORIZON IS A RATIO, NOT AN N
At dim=1024 (sparse read, so read as a lower bound):
| N | bundle | counts |
|---|---|---|
| 512 | 0.143 | 0.333 |
| 1000 | 0.000 | 0.050 |
| 2000 | 0.000 | 0.000 |

Compare F1263 at dim=4096: counts held **0.962 at N=512** and **0.440 at N=1200**. Same N, four times the dimension, radically different outcome. **So "the count structure's horizon" is not an absolute item count — it is a function of N/dim.** F1263's 11×-at-N=1200 headline is a *dim=4096* statement and should always be quoted with its dimension.

## (4) DIMENSION IS THE LEVER — and my first measurement of it was void
**First attempt was invalid**: I measured the dimension sweep using the margin-sparse read that (3) had just shown to be broken, and got a non-monotonic mess (0.000 / 0.100 / 0.050 / 0.350). Re-run with the **full** read, N=1000:

| dim | counts recall |
|---|---|
| 1024 | 0.200 |
| 2048 | 0.300 |
| 4096 | 0.500 |
| **8192** | **0.800** |

Clean and monotonic — recall roughly scales with dimension across an 8× sweep at fixed N.

**So the collision term responds strongly to dimension.** That reframes F1259: the designed-family question is **secondary, not blocking**. Dimension is linear in storage, trivially available, and delivers 4× recall over an 8× sweep; a designed family is hard (two constructions already lost to the RNG) and would buy a constant factor on the sidelobe. **Spend dimension first.**

## Net
| # | result |
|---|---|
| 1 | horizon is **N/dim**, not an N — F1263's headline is dim-conditional |
| 2 | storage **~5.5× and log N**; dense in cells, compressible in value range |
| 3 | **sparse read refuted** — margin ranking is noise; O(N·dim) stands |
| 4 | **dimension is the working lever** — 0.200 → 0.800 over 8× dim |

**NEXT:** (a) a *per-query* index — coordinates where the target's contribution stands out — since the global one provably fails; (b) bit-pack the counts at `ceil(log2 N)` to realise the 5.5× rather than paying 32×; (c) push dim to 32768–65536 to find where the dimension lever itself saturates; (d) F1259's designed-family question stays open but **de-prioritised** behind (c).

Composes **F1263** (the count structure; its 4× storage guess and sparse-read hope both corrected here), **F1259** (designed families — now de-prioritised, with a measured reason), **F1216**, **F1205/#263**, `[[feedback_sparse_complete_never_top_k_truncation_at_storage]]` (the read-side application, which failed on this object), `[[feedback_read_independent_structure_check_first]]`, #231/PKG-3.
