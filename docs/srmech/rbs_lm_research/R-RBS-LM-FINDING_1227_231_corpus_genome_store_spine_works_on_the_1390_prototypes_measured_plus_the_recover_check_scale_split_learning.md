# F1227 — #231 STARTED: the genome-native directed Class-L corpus store WORKS end-to-end on the #1390 prototype spine (measured: 3.4–4.3× smaller than loose JSON, byte-exact, integrity-checkable) — and it surfaced the #1390 scale learnings the maintainer should have

**User (2026-07-14):** *"start #231 on rc241 using these prototypes as the spine. srmech dispatched to #1390 soon — flag anything we learn that needs it updated."* Started; spine works; two concrete #1390 refinements flagged.

## The store (`R-RBS-LM-SIONA231_…py`) — built entirely on the five #1390 prototypes
`text → tokenize → cooccurrence_edges(directed=True) [item 1] → magnetic_laplacian [shipped] + graph_to_kernel [item 2] → genome (2 chromosomes: directed graph + vocab string table) → kernel_to_graph → recover_check [item 4]`, with the relational read-out (`neighbors`) and the Eulerian read-out (item 3) on the same object. Proven on the **tier0 findings corpus** (1103 docs, real, dogfood):

| store | vocab | edges | genome | loose JSON | ratio | notes |
|---|---|---|---|---|---|---|
| (A) bounded | 200 | 17,535 | 89 KB | 311 KB | **3.48×** | full 4-faculty `recover_check` PASS (curvature nonzero); 2-chromosome round-trip byte-exact |
| (B) full-vocab | 18,822 | 666,821 | 3.86 MB | 13.06 MB | **3.38×** | built 18.4 s; `recover_check_structural` (sparse) PASS in **0.14 s** |
| (C) simplewiki *projection* | 831,139 | 39,048,148 | ~226 MB | 960 MB | **~4.3×** | @ 5.8 B/edge; the real #231 body-instrument target |

The relational read-out is meaningful: `neighbors('reading')` → framework ←, form ←, substrate →, structural ←, structure →, srmech → (the `←/→` is the charge/direction). So the store is **one content-addressed genome carrying the directed Laplacian + vocab, byte-exact, integrity-checkable, with a working relational read** — exactly the #231 deliverable ("one native genome, not loose NDJSON+index"), storing the **Laplacian not Klein-4** (F1221). The raw-text-source NDJSON role (byte-offset seek + quote) stays separate (F1221); this replaces the *relational* store.

## The #1390 scale learnings to flag (srmech is dispatched to #1390 soon)
1. **item 4 `recover_check` does NOT scale as written.** Its op + responsion faculties do a **DENSE n×n eigendecompose** — measured: `dense_laplacian(n=18822)` took **178.6 s just to BUILD** (before any eig; native Jacobi is n≤256, and it's O(n²) memory / O(n³) time). At corpus vocab this is infeasible. The **sparse faculties scale**: `recover_check_structural` (operand + a sampled-curvature read, O(edges)) ran in **0.14 s** at 667k edges. **Ask:** SPLIT recover_check into `recover_check_structural` (sparse, any-scale — prototyped here) vs `recover_check_spectral` (op+responsion on a **bounded principal submatrix / top-k Lanczos**, not the full dense L).
2. **item 2 `graph_to_kernel` — the codec's int-width cap.** Measured 5.8 B/edge (linear, tiny). But the 2-symbol length header caps each int at **15 base-4 digits = 30 bits**. Fine for simplewiki (831k vocab < 2²⁰; weights well under 2³⁰), but a huge corpus (enwiki, or a co-occurrence weight > 2³⁰) needs a wider header. **Ask:** document the cap (and/or a wide-int mode).
3. **the vocab STRING TABLE.** A self-contained genome needs token→string too — here a **2nd chromosome via `genome_append_kernel(path, label, raw_klein4_syms)`** worked (note: it wants raw symbols, not a packed strand). **Optional:** `graph_to_kernel` could accept/emit the string table so a corpus store is one call.

## Verdict / next
#231 is off the ground and validated at real (667k-edge) scale, projecting to a **4.3× win** on the full simplewiki body instrument. The spine is the five #1390 ops; the only gaps are the two flagged refinements (recover_check split; codec int-cap doc) — both are *corpus-scale hardening of the exact signatures the maintainer is about to implement*, so they matter now. Next: the real simplewiki build (stream the 916 MB kernel → genome) once recover_check_spectral has a bounded mode, and wire the store into Siona's `_k_load`/grounder (F1219's read-path fix).

Composes **F1226** (the item-1 front + end-to-end pipeline), **F1223/F1224/F1225** (items 2/3/4), **F1221/F1222** (store the Laplacian not Klein-4; the op family → #1390), **F1216** (L-store), **F1219** (the read-path this store will feed), #231/PKG-3, [[feedback_computational_provenance_discipline]] (measured + committed), [[feedback_store_sparse_complete_never_top_k_truncation_at_storage]] (uncapped store).
