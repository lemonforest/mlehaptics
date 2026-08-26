# F1253 — §102 STAGE 1 BUILT at full scale: 240,881 plasmid sections in **11.1 minutes** (2.8 ms/doc, 336 MB, checkpointed, visible, cancellable) — versus the monolithic `genome_from_graph` that ran **8+ hours without finishing** and was lost whole to a power outage. ≥45× faster and it actually completes. Plus the measured CONSERVATION CURVE (the stage-2 promote input) — heavy-tailed with a minority conserved core, the F1251 core/accessory SHAPE, though the exact ratio is k-dependent.

**Context:** the F1252/§102 two-stage encode, stage 1 delivered in srmech rc278 (`srmech.amsc.plasmid.plasmid_extract`). Run on the full simplewiki `articles.jsonl` (240,881 documents) with srmech **0.9.0rc278**, using the rc275 §101 progress tick. Harness: `R-RBS-LM-PLASMIDEXTRACT`.

## The measurement — the architecture change is the whole story
| | monolithic `genome_from_graph` (rc272) | **sectional `plasmid_extract` (rc278)** |
|---|---|---|
| runtime | **8+ h, NEVER FINISHED** (killed by power outage) | **11.1 min** (2.8 ms/doc) |
| recovery on interruption | **total loss** — writes only at completion, no checkpoint | **per-section** — each section is a complete chromosome on landing |
| visibility | blind (no progress) | live heartbeat (120 → 472 docs/s, ETA shown) |
| cancellable | no | yes (nonzero tick return, clean section boundary) |
| peak RAM | 18.5 GB and climbing | ~6.7 GB, flat |
| output | none (lost) | **336 MB store, 240,882 chromosomes, status=ok** |

`census` = `{plasmid: 240882, nuclear: 0, diploid: 0}`, topology `plasmid/prokaryote-like` — **correct for stage 1** (all Tier-1 plasmid sections + the vocab karyotype chromosome; nothing is minted until stage 2). Vocab: **1,100,189** global ids. The 336 MB store **retires the loose 916 MB `simplewiki_directed_sparse_kernel.json`** at the graph-L layer (2.7× smaller, and genome-native rather than a monolithic JSON re-extracted every encode).

**The rate CLIMBED through the run** (120 → 472 docs/s) — the append is O(1) per section (v12 head-only manifest) and the global vocab stabilises, so later sections cost less. The opposite of the monolith's behaviour.

## The conservation curve — stage 2's input, measured
`plasmid_extract` returns `section_count {global_id: n_sections}` as a FREE streamed integer accumulator (no scan). Measured over 1,100,189 global ids:

| appears in ≥ k sections | count | fraction of vocab |
|---|---|---|
| 1 (singleton) | 710,938 | **64.6 %** |
| ≥ 2 | 389,251 | 35.4 % |
| ≥ 5 | 159,618 | **14.5 %** |
| ≥ 10 | 92,137 | 8.4 % |
| ≥ 25 | 47,746 | 4.3 % |
| ≥ 50 | 29,783 | 2.7 % |
| ≥ 100 | 18,718 | 1.7 % |

**The SHAPE matches F1251's attested biology** — a heavy-tailed distribution with a **minority conserved core** and a large singleton/accessory majority, exactly the core-vs-accessory partition Shropshire et al. measured in *K. pneumoniae* (16 % core / 84 % accessory). **Honest caveat (no forcing):** the correspondence of `k≥5 → 14.5 %` to the attested 16 % is **threshold-dependent** — `k` is a free parameter, and picking it to match would be post-hoc. What is genuinely measured is the *shape* (minority conserved core, heavy accessory tail); the *ratio* only becomes meaningful once stage 2 (rc279) fixes `k` on its own criterion. The curve is the honest deliverable; the ratio is stage 2's to determine.

## Why stage 2 will be cheap (the 8-hour problem, dissolved)
`section_counts`' docstring states the promote rule: *"a node CONSERVED iff its section-occurrence count >= k (a plain integer accumulator, no spectral solve)."* So the nuclear/plasmid partition that cost **8+ hours of blind `recursive_cut`** becomes an **integer comparison over a dict we already have for free**. That is F1251's attested biology supplying the algorithm: the core genome is defined by *conservation across isolates*, not by a spectral cut — so counting conservation IS the biology-native partition, and it is O(vocab) instead of O(spectral).

## Measured srmech follow-up (§102)
`section_counts()` — the SSoT **re-derivation** (scan every section, decode its `node_ids`) — measured at **0.33 s/section → ~22 h at 240,881 sections**. It is a verification re-read, not the required path (the streamed accumulator is free and the changelog asserts they are byte-for-byte equal), so the harness makes it opt-in (`--verify-counts`). Worth a srmech look: the re-derivation should page only the `node_ids` table, not decode each section's full graph.

## Verdict / next
**§102 stage 1 is BUILT and validated at full corpus scale**, and it vindicates the architecture: extract-once + append-only is ~45× faster than the monolithic partition (which never completed), survives interruption per-section, and is visible + cancellable via §101. The conservation curve — the stage-2 promote input — is measured and heavy-tailed with a minority core. **NEXT:** when rc279 lands stage 2 (promote conserved → NUCLEAR by integer section-count), run it on this store to get the correct nuclear+plasmid genome, then answer the F1248 A–D layout/read questions on the correct shape, and settle F1250's bimodality question with the conservation criterion rather than a spectral one.

Composes **F1252/§102** (the two-stage design — this is stage 1 measured), **F1251** (core=conserved / accessory=variable — the biology that supplies both the shape and the cheap algorithm), **F1247** (encode once, render on the fly — one layer up), **§101** (the progress/cancel that made this visible; rc275), **F1248** (the A–D questions waiting on the correct genome), **F1250** (the bimodality question, to be re-answered by conservation not spectra), [[feedback_persist_genome_native_not_loose_json]] (the 916 MB JSON retired), [[feedback_encode_once_render_on_the_fly_epigenetic_reader]], #231/PKG-3.
