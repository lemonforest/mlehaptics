# F1254 — the §102 TWO-STAGE ENCODE IS COMPLETE at full scale: the correct eukaryotic genome (1 minted nuclear core + 240,881 plasmid sections, 323.7 MB) built in **35.4 minutes** with `recursive_cut` never called — versus the monolith that ran 8+ hours and never finished. AND the honest headline: the **data-derived `k` = 10,714 gives a core of 170 / 1,100,189 ids (0.015 %)** — so F1251's ~16/84 core/accessory ratio **does NOT reproduce** on the word corpus. Independent confirmation of F1250's substrate-specificity, via a completely different method.

**Context:** chained `plasmid_extract` (stage 1, rc278) → `genome_integrate_plasmids` (stage 2, rc279–281) over all 240,881 simplewiki articles, srmech **0.9.0rc281**, handing the free streamed `section_count` straight through. Harness: `R-RBS-LM-TWOSTAGE`. This finally answers the F1248 A–D questions on the CORRECT genome shape.

## The build (D — re-layout cost, measured)
| | monolithic `genome_from_graph` | **two-stage `extract → organize`** |
|---|---|---|
| stage 1 extract | — | **10.8 min** (240,881 sections, 2.7 ms/doc, rate climbed to 481/s) |
| stage 2 organize | — | **24.3 min** (conserve + promote + merge) |
| **total** | **8+ h, NEVER FINISHED** (lost whole to a power outage) | **35.4 min, status=ok** |
| method | blind monolithic spectral `recursive_cut` | **`recursive_cut` NEVER CALLED**; integer conservation + mint + merge |
| interruption | total loss | per-section checkpoint |

**D is answered:** the re-layout is ~35 min *and* it is now incremental — `add_plasmid` makes adding a document an append + count-bump + small-core re-mint, so this is the last full rebuild, not a recurring cost.

## A — the layout of the correct-shape genome
```
path            ~/corpora/wikipedia/simplewiki_organized.genome     323.7 MB
format_version  15        leaf_dim 64        n_turns 18,376,459
chromosomes     240,882  = 1 NUCLEAR + 240,881 PLASMID
  core   cap_kind=nuclear   8,347 leaves     (minted, 0x58 centromere)
  sec0…  cap_kind=plasmid   103–801 leaves   (one per document)
census          types={diploid:0, nuclear:1, plasmid:240881}   topology=nuclear-like
```
So the eukaryotic shape we could not reach through the monolith exists: **one minted nuclear core chromosome carrying the conserved content, plus one Tier-1 plasmid chromosome per document.** Addressing is by global node-id (the section `node_ids` tables map local→global; the vocab chromosome is the karyotype index).

## The honest headline — `k` was DERIVED, and ~16/84 does NOT reproduce
`conserved_core(section_count, k="auto")` measures the **antimode of the section-count histogram**; its contract states *"`k` IS DERIVED OR DECLINED — NEVER MANUFACTURED"*, and its docstring says to *"expect the ASYMMETRIC minority core (~16/84 — F1251)."* Measured:

```
k = 10714        k_source = derived        bimodal = True    gap = 250
n_core      =        170        (0.015 %)
n_accessory =  1,100,019        (99.985 %)
```

**This is not 16/84. It is 0.015 / 99.985.** A word must appear in ≥10,714 of 240,881 documents (≥4.4 % of the corpus) to be conserved-core, and only **170 tokens** clear that bar.

Two things are true at once, and both matter:
1. **A genuine bimodal split EXISTS** (`bimodal=True`, `gap=250`, `one_dna_type=False`) — the antimode found a real gap. So the word corpus *does* have a conserved core; it is not one undifferentiated mass at this read.
2. **The RATIO is nothing like biology's.** F1251's attested *K. pneumoniae* 16 % core / 84 % accessory does **not** transfer. This is **independent confirmation of F1250** — which reached "the nuclear/organelle split is substrate-specific" by a completely different route (degree-normalised participation + spectral communities). Two orthogonal methods, same verdict: **the partition is real but substrate-specific; the ratio is not a law.**

And critically — **I did not get to choose `k`.** F1253 flagged that picking `k≥5` to land near 16 % would have been post-hoc curve-fitting. The derived answer came back two orders of magnitude away from the biology, which is exactly why deriving beats fitting. The ~16/84 correspondence F1253 noted at `k≥5` was indeed an artefact of threshold choice, and is now retired.

**What the 170 are (structural read, to be confirmed):** at ≥4.4 % document frequency these are almost certainly the ultra-high-df function-word spine — the tokens the tome-tree already drops as hubs (`H_DROP=250`, F1250). The biological role-analog is the **housekeeping gene** (expressed in essentially every cell), not the 16 % core-genome fraction. So the ROLE maps (always-present spine) while the RATIO does not — plausibly because word frequency is Zipfian and gene presence/absence across strains is not, which would put the antimode far out in the tail. **NEXT (cheap):** dump the 170 core tokens and confirm they are the function-word spine.

## B — bytes-touched on the correct shape: the read is still not a SEEK
Measured against the organized genome:

| read | bytes needed | time | note |
|---|---|---|---|
| `genome_catalog(store)` | manifest | **9.9 s** | 240,882 chromosome entries |
| `genome_load(labels=["core"])` | **0.14 MB = 0.04 %** of the 323.7 MB store | **91.0 s** | the nuclear core alone |
| `genome_load(labels=["sec0"])` | one document's 802 leaves | **88.4 s** | one plasmid section |

**A targeted single-chromosome read takes ~90 s to deliver 0.04 % of the bytes.** The catalog already carries each chromosome's `byte_offset` + `byte_len`, so this *should* be a seek — but the cost is flat across `core` (first chromosome) and `sec0`, and scales with the store, which says `genome_load(labels=…)` is **walking the strand rather than seeking to the catalogued offset**. At 240,882 chromosomes that is the difference between ~90 s and ~milliseconds.

So F1248's B-verdict **survives the re-shaping, one level up**: the old flat store had no per-NODE seek (every neighbour read hit the `adj.bin` cache); the organized store now has no per-CHROMOSOME seek. The demand-load the streaming render reader needs — "page only the walked subset" — is still not reachable from the genome alone. **This is the single highest-value srmech follow-up**: make `genome_load(labels=…)` seek via the catalog `byte_offset`, and the chromatin-gated demand-load (rc269 `gene_express_plan`) becomes real at corpus scale.

**Also found:** the organized genome has **no vocab chromosome** (`has vocab? False`) — the karyotype index stayed in the sections store. So the organized genome is not self-contained: global node-ids cannot be resolved to tokens from it alone. Either stage 2 should carry the vocab through, or the two stores are formally one unit.

## A design question this surfaces
**240,882 chromosomes is biologically strange** — no organism carries 240k chromosomes. One-chromosome-per-document is the natural granularity for the melange/book reading (each document its own store, co-expressed not merged), but it means "chromosome" is doing double duty as "document." Worth deciding whether sections should coarsen into fewer, larger chromosomes (a karyotype), or whether the per-document chromosome IS the right object and the biological odd-numberness is simply not a constraint we should honour.

## Verdict / next
The two-stage encode is **validated end-to-end at full corpus scale** and the correct eukaryotic genome exists. **D answered** (35.4 min, now incremental). **A answered** (layout above). **The 16/84 hypothesis is falsified for this substrate by a derived, non-post-hoc threshold** — F1250's substrate-specificity now has two independent confirmations. **Remaining:** (1) identify the 170 core tokens; (2) re-measure **B** (bytes-touched per read mode) against the new shape — the old `corpus_store` read path targets the retired flat store, so the genome-native demand-load (`genome_load(core)` / per-section paging) is the thing to measure now; (3) the F1248 **C** render family is unchanged (findings-level).

Composes **F1253** (stage 1 — and this retires its `k≥5 → 14.5 %` correspondence as threshold-dependent, exactly as flagged), **F1252/§102** (the two-stage design, now fully delivered), **F1251** (the attested 16/84 that does NOT transfer — the biology supplied the *algorithm* (conservation) even though the *ratio* is substrate-specific), **F1250** (substrate-specificity — independently confirmed here), **F1248** (A–D; A and D now answered on the correct shape), **F1249/§100** (the eukaryotic builder), **§101** (progress/cancel made the run visible), #231/PKG-3.
