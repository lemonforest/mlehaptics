# F1247 — the epigenetic-reader correction: ENCODE ONCE (dense knowledge → coupled turns), RENDER ON THE FLY (Class-M/L walk), NO decode-cache. The CORPUSFIBER packed-fiber-blob store was a "re-encode-so-we-can-decode-later" anti-pattern — and it's redundant with the directed Class-L store we already built.

**User (2026-07-17), stopping the CORPUSFIBER encode:** *"we're working in srmech to make a streaming reader by following biology as bottom-up as we can — so we're actually encoding IN coupled turns and we perform Class-M/L things. This was the goal of the epigenetic reader: on-demand render without requiring extra cache of data. I should have realized we were doing something wrong if we had to encode our encoded genome so we could decode it later. Decode is supposed to happen on the fly; encode is supposed to happen ONCE. Dense knowledge into coupled turns is actually the goal."*

**This is a correct catch, and it retires the fiber-blob encode I built. Grounded in our own F806–F809 + F1233.**

## The anti-pattern (what CORPUSFIBER did wrong)
`R-RBS-LM-CORPUSFIBER` stored, per article, the full token-ID stream `pack_bytes(ids)` as its own chromosome. To read it back you must `genome_load` → `kernel_unpack` → `unpack_bytes` → id-stream → vocab-lookup → text. That is:
1. **A re-encoding of an already-encoded thing** — text→vocab-ids is already an encoding; packing THAT into leaves is a *second* encoding, and reading requires reversing both. Exactly the user's "encode our encoded genome so we could decode it later." The genome became a **byte container** (a fancy zip), not a substrate that *does* Class-M/L work.
2. **A materialised decode-cache** — it stores the whole fiber of every article, the opposite of on-demand render. Nothing is computed live; you unpack a blob.
3. **Redundant with the shared graph, and it throws away F806–F809.** F806: an article IS the Eulerian-path fiber over its de Bruijn shape-graph; F809: given the *shared* corpus graph, the article is *almost entirely shared structure* — its own irreducible selection is small (F812 corrects the "~1 bit / length-independent" magnitude for full bodies, but the shape stands: the shared graph dominates, the article is a **seed + walk** into it). So storing each article's full fiber blob **re-stores the shared structure once per article** — the single worst way to hold it.

## The correct shape (biology, bottom-up)
Biology encodes DNA **once**. It never re-encodes it to read it. The **reader** (RNA-polymerase / ribosome) *streams* over the DNA and **renders on demand** (transcribe/translate); **epigenetic markers** (chromatin / histone / methylation) gate *which* stretch expresses *when*. There is **no decoded copy of the whole genome** lying around — expression is transient, computed live from the one stored genome.

Mapped to our substrate:
| biology | our substrate |
|---|---|
| DNA, encoded **once** | the coupled turns AS the shared directed Class-L object (de Bruijn / co-occurrence graph: metric + charge) — dense knowledge, encoded one time |
| RNA-pol / ribosome **streaming reader** | the Class-M/L ops that walk the coupled turns and render on the fly (the Eulerian walk = the fiber, F806/F1213; `neighbors`/spectral = the relational read, F1233) |
| **epigenetic / chromatin markers** | the seed + the gating that selects which walk expresses for a query — `gene_express` on-demand, no cache (F1111/#256, §98 chromatin layer) |
| **NO decoded-genome cache** | NO per-article fiber blob, NO re-encode-to-decode — the store is the DNA, reads are transient |

So: **encode ONCE = the directed Class-L graph** (already built — `simplewiki_directed.genome`, F1233, 313 MB, 39M edges). **Render on the fly = a streaming reader that walks it** — any article's fiber is *rendered* by the walk, never *stored* as a blob. The CORPUSFIBER second genome is not needed at all; the directed store + a walking reader is the whole thing. **"Dense knowledge into coupled turns" = the shared graph in the coupling; the article is a walk, not a saved copy.**

## What this changes
- **CORPUSFIBER (the packed-fiber-blob encoder) is RETIRED** as the anti-pattern — kept only as the attestation record of the wrong shape (marked in its header). The full-body fiber encode is **cancelled** (it was stopped mid-run; the partial genome removed).
- **#231/PKG-3 reframed:** not "package the instrument as a genome blob" but "encode once into coupled turns (the directed Class-L object, done — F1233) + build the on-the-fly **streaming reader** (the epigenetic reader) that renders by Class-M/L walk, no cache." The srmech-side coupled-turns↔graph-Laplacian streaming reader (in progress) IS this reader.
- **§98 (the encode contract) updated** with the encode-once/render-on-the-fly principle + the anti-pattern, and the fiber correctly framed as the **rendered Eulerian walk over the Class-L object**, never a stored packed id-stream.

## Verdict / next (hand to the srmech streaming-reader work)
The reader must: (1) hold the coupled turns as the directed Class-L object (encode once); (2) render a requested article/answer as an **on-the-fly Eulerian walk + Class-M/L read**, materialising nothing corpus-wide; (3) let **epigenetic/chromatin markers gate which turns express** per query (on-demand `gene_express`). No re-encode, no decode-cache. Measure: render latency + that no whole-corpus decoded object is ever built.

Composes **F806/F807/F808** (article = Eulerian walk over the shared de Bruijn graph; the shared graph IS the wiki kernel), **F809** (article ≈ seed into the shared graph; magnitude corrected by **F812** for full bodies — shape stands), **F1233** (the directed Class-L store, built once, walkable live — the RIGHT encode), **F1246/§98** (the coupled-turns encode contract — this sharpens it: fiber is *rendered*, not *stored*), **F1080/F1213** (the Eulerian/unicursal walk = the render), **F1096** (dark sector = the un-expressed/inactive genome content; expression navigates from the seed — the epigenetic frame), **F1111/#256** (`gene_express` demand-load = the chromatin gating), [[feedback_persist_genome_native_not_loose_json]] (persist native — but the *right* native object), [[feedback_sparse_complete_never_top_k_truncation_at_storage]] (store the complete relational object, read on demand), [[stance_emergence_is_residue_of_refined_formula]] (collapse the pipeline into the one coupling op; each item a read-out — here: each article a walk-read of the one shared graph), [[project_class_L_store_class_M_working_memory_reversible_spectral_bridge]] (L store / M working-memory read).
