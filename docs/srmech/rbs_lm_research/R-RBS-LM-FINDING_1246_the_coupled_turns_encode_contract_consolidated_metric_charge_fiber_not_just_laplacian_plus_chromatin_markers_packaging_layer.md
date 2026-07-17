# F1246 — the coupled-turns encode contract, CONSOLIDATED: what we encode into coupled turns is the directed Class-L Laplacian (metric + charge) AND the fiber — NOT "just the Laplacian," and never the Klein-4 HV object. Plus chromatin markers = the new packaging layer above the content.

**User (2026-07-17):** *"we're adding a coupled-turns ↔ graph-Laplacian machinery — not just encode but also decode, real-time, no cached files. Do our #687 findings say WHAT we're trying to encode into coupled turns — is it just the Laplacian, or our edge fiber too? I told srmech this knowledge should be there; make sure it can be found, and if not, define it somewhere as close to how biology does. Also we've added more biological machinery and are now working on chromatin etc markers."*

## The answer: YES, it's defined in #687 — and the answer is BOTH (not just Laplacian)
The knowledge **is** in the branch — but it was scattered across three findings (F1221 store-the-Laplacian-and-fiber, F1228 the metric/charge/fiber decomposition, F1233 both reads built at scale). So this finding **consolidates** it into one answer, and I lodged the single srmech-facing spec at **`UPSTREAM_NOTES.md §98`** (the place srmech will look, since the user told srmech "this knowledge should be there").

**What the coupled turns carry — all THREE parts of `op(x)operand(x)responsion` (ADR-0002, the k=3), biology-native (F1228):**

| coupled-turns part | biology (DNA/RNA) | carries | commutativity | on-disk |
|---|---|---|---|---|
| **metric** (symmetric L=D−A) | base composition | order-FREE relation (i,j)==(j,i) | Abelian | `edge_list` + `edge_weights[metric]` |
| **charge** (magnetic-Laplacian phase) | 5'→3' sense + helix handedness | chirality — mirror-broken direction →/← | Abelian U(1) dial, nonzero holonomy | `edge_charge[direction]` |
| **fiber** (ordered walk / id-stream) | base SEQUENCE (ACGT≠AGCT) | non-commutativity — "order matters" | non-commutative free monoid | the token-ID stream (Eulerian walk) |

So it is **NOT "just the Laplacian."** The store carries the **directed Class-L Laplacian (metric + charge) AND/OR the fiber (ordered id-stream)** — which you materialise depends on the READ (the k=3):
- edges → **RELATIONAL** ("what water is LIKE") = the directed Laplacian.
- responsion/walk → ordered **FIBER** ("what the article IS", byte-exact) = the id-stream.
- eigenvectors → **DISTRIBUTIONAL** = recomputed, never the store.

**Never on disk: the Klein-4 bind/bundle HV object** (it flattens — the working-memory M-read, F1214/F1221). Klein-4 *symbols* are fine as the 2-bit on-disk byte alphabet (`pack_bytes`/`graph_to_kernel`); the *HV object* is not. Klein-4 HVs are a deterministic projection recomputed on demand (`klein4_random(seed=hash(token))`, F833). Disk rule: **relational on disk (directed Laplacian + fiber), holographic in RAM (Klein-4, recomputed).**

## The two simplewiki genomes on disk ARE the two reads — the contract is already live
- `simplewiki_directed.genome` (F1233; 313 MB; 39,048,148 directed edges) = the **directed Class-L Laplacian** (metric+charge) → RELATIONAL read, wired into Siona's `define`.
- `simplewiki_fullbody.genome` (CORPUSFIBER, this session; streaming on rc267, RAM-bounded) = the per-body **ordered FIBER** (token-ID streams + `__vocab__` codebook) → byte-exact IS read.

## Chromatin markers — the NEW packaging layer (the added biological machinery)
Above the coupled-turns *content* sits biology's **chromatin** packaging tier: which stretches are ACTIVE (euchromatin, expressed) vs CONDENSED (heterochromatin, silenced), with histone-style markers gating access. In the format this **extends the existing cap/marker layer** (telomere end-cap, `0x58` centromere orientation-chirality anchor, `0x44` diploid-drive — §95/F1243): chromatin markers are **per-region access/expression markers** deciding which edges/contacts are LIVE at read time = the genome's own `gene_express` gating (demand-load the query subset, F1111/#256), the biological analogue of Siona's never-compacted working-memory *selection*. **It is packaging ON TOP OF the content, not part of it:** coupled turns = the DNA sequence (metric+charge+fiber); chromatin = how it's spooled and which stretches are readable *now*.

## Requirements handed to the srmech encode/decode machinery (real-time, no cached files)
1. Round-trip **metric + charge + fiber** both ways: encode = `graph_to_kernel` + the fiber id-stream; decode = `kernel_to_graph` + the Eulerian walk. (Byte-exact on 39M edges already proven, F1233.)
2. **Klein-4 is a decode PROJECTION, never a decode TARGET** — recompute from the token seed.
3. The **chromatin/cap markers must survive the round trip** (as `centromere_of` survives `integrate`, §95) — the packaging layer is part of the format contract, distinct from the content.

## Verdict / next
The user's question is answered: **defined, and findable** — consolidated at UPSTREAM §98 (srmech-facing) + here (the #687 record) + siona ADR-0002 (the two-reads principle). The encode is **both** the directed Laplacian and the fiber, never the Klein-4 object; chromatin markers are the packaging layer above. Next: as the srmech coupled-turns↔graph-Laplacian encode/decode lands, verify the round-trip preserves metric+charge+fiber AND the chromatin/cap markers.

Composes **F1221** (store the Laplacian + fiber, not Klein-4 — the disk rule), **F1228** (the metric/charge/fiber decomposition; DNA/RNA carry all three separately), **F1233** (both reads built at real scale; the directed store wired into Siona), **F1216** (L-store / M-read), **F1214** (Klein-4 flattens — why not to store it), **F833** (fiber-not-HV; Klein-4 as recomputed projection), **F1111/#256** (gene_express demand-load = the chromatin gating), **§95/F1243** (the cap-marker layer chromatin extends), siona **ADR-0002** (one Laplacian, two reads), UPSTREAM **§98** (the consolidated spec), [[feedback_persist_genome_native_not_loose_json]], [[feedback_relational_not_dense_distributional_not_sparse]], [[stance_bit_exact_is_phase_locked_cyclic_slots_not_flat]] (DNA/RNA = beat slots), [[project_class_L_store_class_M_working_memory_reversible_spectral_bridge]].
