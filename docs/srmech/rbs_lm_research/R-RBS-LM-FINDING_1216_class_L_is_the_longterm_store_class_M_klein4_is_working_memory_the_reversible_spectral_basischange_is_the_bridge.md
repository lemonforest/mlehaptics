# F1216 — Class-L is the long-term relational STORE, Class-M (Klein-4/HDC) is WORKING MEMORY; the reversible spectral basis-change (eigen / Walsh-Hadamard, laddered by the fractal tower) is the bridge. Reversibility lives in the change-of-basis; loss lives in the compression

**User (2026-07-14), synthesizing F1207/F1214/F1215:** *"do our fractal math towers give a reversible way to change between class-L and class-M? Klein-4 might be the right shape for context / active working memory (a cost-comparison thing) — or is it just 'use both because they flatten differently'?"* All three intuitions are right and fold into one architecture.

## Reversibility lives in the CHANGE OF BASIS; loss lives in the COMPRESSION
Two distinct operations we had been conflating:
- **Change of basis** — eigendecomposition on L, **Walsh-Hadamard** on M — is a *lossless re-coordinate* (same info, different lens). MEASURED exact both sides: WHT `inverse(fwd(x)) == x` (pure ±1 add/subtract); graph↔eigenbasis `L = V diag(λ) Vᵀ` reconstruct max|err| 1.5e-14. This IS the F1207 "one object → many reads" (edges ↔ eigenvectors ↔ eigenvalues = the same graph in different coordinates).
- **Compression** — superposition/`bundle`, top-k truncation, dimension projection — is where information is *spent* for a fixed size. The Klein-4 **bundle** is exactly this.

**So graph ↔ its full distributional (eigenvector) face is REVERSIBLE; the Klein-4 bundle is a LOSSY sketch of that face (bundle→graph is not reversible).** The fractal tower (Cayley-Dickson ℝ→ℂ→ℍ→𝕆 / winding, F1072/F963/RC-1) is the **multi-scale ladder of the reversible basis-changes** — lossless re-coordinate at every rung; the loss only enters at a bundling/truncation step, which is a **choice about compactness, not forced.** (WHT is the octonion's own FT because its sector group is (Z₂)³, F422/F423/F444 — reversibility attested + re-measured here.)

## Klein-4 IS the working-memory shape
The exact properties that make Klein-4 WRONG for the exact store (F1214/F1215) make it RIGHT for active context:
- **fixed cost** — one D-vector, cost independent of how much is crammed in (the D-independent capacity, F871);
- **cheap compose** — one `bundle` op, O(D);
- **fuzzy match** — similarity = resonance = "what's salient now" (approximate is FINE for context);
- **graceful decay** — the ~24-bind capacity wall IS a working-memory *span*; old items fade as it fills.
Its capacity wall **is literally a working-memory-cost metric** (how much context fits before recall degrades) — the "cost-comparison thing." Klein-4 = the RAM / attention object.

## The architecture — division of labor by memory ROLE, bridged reversibly
| role | representation | properties |
|---|---|---|
| **long-term store** | **Class-L Laplacian** (directed/magnetic) | exact, addressed, directional, reconstructible, GROWS with knowledge (the genome/disk) |
| **working memory / active context** | **Class-M Klein-4 bundle** | fuzzy, composable, BOUNDED, decays (the RAM/attention) |
| **bridge** | reversible spectral basis-change (eigen/WHT, laddered by the tower) | `gene_express` (F1111 demand-load) the query-relevant subgraph out of L → project into the M bundle for the turn → commit back to L for anything exact/permanent |

**The invariant that keeps it consistent with the canon:** the distributional (Klein-4 / eigenvector) form is always a **transient READ of the relational store, never the store itself** (F1132 "stay relational, never distributional-as-store"; F1207 "distributional = a read-out") — like the melange coupling op that is computed, used, and discarded (`[[project_genome_melange_coexpress_separate_class_l_genomes]]`). Stay relational on disk; go holographic in RAM; the reversible transform is the bus between them.

## Consequences
- **Not "use both because they flatten differently"** — it is "use both" **sharpened into a role split**: L = store, M = working context, reversible spectral bridge between.
- **This is exactly why #231 is the right next move:** make the *word* a Laplacian object (the exact directional store, F1213), while Klein-4 stays the working-context bundle riding on top — the user's gut-check confirmed.
- **The two "not-flatten" strategies are a ladder** (F1214): dense float embedding (most flattened, rejected) → Klein-4 bundle (discrete chirality-native but superposed/fuzzy — the working read) → Laplacian graph (least flattened, exact/directional — the store).

Composes **F1207** (one relational object → three reads; the eigenbasis is the bridge), **F1214/F1215** (why Klein-4 is the coarse/fuzzy face; the bag is in the abelian combine + coarse read), **F1132** (relational store, distributional read — never the reverse), **F1111** (gene_express demand-load = the L→M projection), **F422/F423/F444** (WHT = the octonion FT, reversible), **F1072/F963** (the fractal winding/CD tower = the multi-scale reversible ladder), **F871** (D-independent capacity = the working-memory budget), [[project_genome_melange_coexpress_separate_class_l_genomes]] (couple op computed-then-discarded), [[feedback_relational_not_dense_distributional_not_sparse]].
