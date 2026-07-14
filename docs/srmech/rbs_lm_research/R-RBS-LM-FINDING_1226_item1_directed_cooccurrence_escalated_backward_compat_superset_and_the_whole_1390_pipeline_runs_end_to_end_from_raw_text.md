# F1226 — item 1 (`cooccurrence_edges(directed=True)`) ESCALATED to a working reference impl: a backward-compatible SUPERSET (metric == today's weights) that adds the charge axis — and with it the WHOLE #1390 op family composes into ONE runnable pipeline from raw text

**User (2026-07-14):** *"escalate item 1 while we're already forming prototypes the way we use the data."* Done — item 1 is now a demonstrated reference impl, and it closes the loop with items 2/3/4 end-to-end.

## `cooccurrence_edges(docs, *, window, vocab, directed=False)` — the reference impl (PASS)
`R-RBS-LM-DIRCOOCCUR_…py`. The shipped `text.cooccurrence_edges` folds direction (canonical i<j) → `(n, edges, weights)`. The ask (F1210, already filed UPSTREAM §) is now a concrete, tested reference:
- **(A) backward-compatible drop-in.** `directed=False` reproduces the shipped op **byte-for-byte**: `(4, [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)], [3,2,1,3,1,1])` — identical. Adding `directed=` breaks nothing.
- **(B) `directed=True` = a strict SUPERSET.** Returns `(n, edges, metric, charge)` where **metric == today's weights** (`[3,2,1,3,1,1]`, verified equal) and **charge = w_fwd − w_bwd** is the new axis (`[1,0,1,1,1,−1]`, nonzero). Reversing the corpus **flips the charge exactly** (`[−1,0,−1,−1,−1,1] == −charge`) with the metric unchanged — the direction the fold discarded, recovered. This is F1211's word==reverse blindness fixed at the TOKEN scale (as NIVDIRECTED fixed it at the glyph scale — F1210's "one directed-edge object at every scale").

## The whole #1390 pipeline now runs END-TO-END from raw text
The point of escalating item 1 *while forming the prototypes* is that it is the FRONT of the pipeline whose back we already built — and they compose into ONE runnable chain (measured, PASS):

    text → tokenize → **cooccurrence_edges(directed=True)** [item 1] → (n, edges, metric, charge)
         → **magnetic_laplacian**(n, edges, metric, charges=charge)   [shipped — the directed Hermitian L]
         → **graph_to_kernel** → genome_save/load → **kernel_to_graph**  [item 2 — codec-exact]
         → **recover_check** → ok=True, curvature = "carries-direction + curvature (nonzero holonomy)"  [item 4]

So the corpus directed Class-L store is a **complete, demonstrated pipeline** from raw text to a content-addressed genome that verifiably recovers all four faculties — exactly the #231/PKG-3 spine, built from the five upstream ops (item 3's Eulerian walk is the reconstruction read-out on the same object). Nothing in the chain is hand-waved; every stage is a shipped op or a tested prototype.

## #1390 — all live items now prototyped + composed; ready for the maintainer
| item | op | status |
|---|---|---|
| 1 | `cooccurrence_edges(directed=True)` | **ESCALATED — reference impl, drop-in + superset, end-to-end** (this finding) |
| 2 | `graph_to_kernel` / `kernel_to_graph` | prototyped 8/8 (F1223) |
| 3 | `eulerian_path` / `eulerian_circuit` | prototyped 11/11 + 6/6 (F1224) |
| 4 | `recover_check` | prototyped 5/5 + round-trip + 3/3 (F1225) |
| 5 | `klein4_permute` | withdrawn (phase_bind, F1223) |

Proposed API: add `directed=False` to `text.cooccurrence_edges`; `directed=True` → `(n, edges, metric, charge)`. Additive, backward-compatible, and — because it lands in `srmech.amsc.text` (which has a C-native peer, UPSTREAM §) — it earns the C mirror. The maintainer now has a runnable, verified reference for the entire directed-genome-storage op family plus a working end-to-end integration test.

Composes **F1210** (the directed-cooccurrence ask + magnetic Laplacian; one directed object at every scale), **F1211** (word==reverse blindness, now fixed at token scale), **F1223/F1224/F1225** (items 2/3/4 — the back of this pipeline), **F1222** (the op family → #1390), **F1216** (the L-store this builds), #231/PKG-3, [[feedback_computational_provenance_discipline]], [[feedback_store_sparse_complete_never_top_k_truncation_at_storage]] (metric is uncapped; directed=True adds, never truncates).
