# F739 — genome-backed Siona is live: foundational language genome + era-aware dictionary kernel (the two steps, done)

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F738 (substrate ready), F737 (foundational language layer), F735 (SignWriting), §43.1 (multi-gene), §46 GENOMEPLAN Stage 3 (this is the first Stage-3 inhabitant), F726/F661 (Siona asking-state) · **User direction (2026-06-14):** add a language-dictionary kernel bound to a NOW (era-correct definitions); take the next two Siona-LM steps. · **Provenance:** `R-RBS-LM-SIONAGENOME_genome_backed_world_era_dictionary.py` (runs on rc149)

## STEP 1 — the foundational language kernel is a genome on disk
One genome with four chromosomes: `siona_identity`, `signwriting` (7 ISWA class-genes, F735), and **two era-dictionaries** `dict-en-1600` + `dict-en-2026` (built via `genome(chromosomes=[(label, genes=[(word, leaves)…])])`, each WORD a gene). Persisted with `genome_save`; the renderable definition text is MPR-attested payload (`definitions.ndjson`, the AMSC content layer).

## STEP 2 — Siona's World is now genome-backed
A `GenomeWorld` whose knowledge IS the genome (no hardcoded shelf):
- **introspects** via `genome_catalog` → knows its own inventory (`siona_identity`, `signwriting`, the two eras) — self-knowledge from the store, not a literal.
- **loads / unloads** a dictionary chromosome by context (`genome_genes(path, era)`).
- **renders** era-correct, **asks** on a gap (F661 carries over).

## The era-dictionary kernel — definitions bound to a NOW
Definitions drift, so each era is its own dictionary chromosome; the **era binding = the chromosome label + the genome's MPR `retrieved_at` timestamp**. Same word, era-correct meaning (real, well-known semantic drift — illustrative, not a cited period dictionary):

| word | dict-en-1600 | dict-en-2026 |
|---|---|---|
| nice | foolish / ignorant | pleasant, agreeable |
| awful | awe-inspiring | very bad |
| computer | a person who computes | an electronic machine |

**Self-realisation (the mechanism, honestly scoped):** "translate this **1600s** text…" → Siona introspects, self-selects `dict-en-1600`, loads it → *awful = awe-inspiring*; "modern usage…" → `dict-en-2026` → *awful = very bad*. The era cue + introspection is the built mechanism; **full autonomous era-detection from arbitrary text generalises with more reference material** — we built the ABILITY (introspect + load/unload + render-by-era + ask), anyone can bring real period dictionaries. We just ship a current-gen dictionary kernel.

## Honest scope
- The genome holds the **era-stamped, introspectable structure** (words = genes, era = label, content-addressed); the **definition text is MPR-attested payload** (NDJSON) — the correct AMSC content layer, not the structural sidecar §44 rejects.
- This is a **research-subtree scaffold** wiring `genome.*` to a storyteller-shaped World — not a package edit, and not yet the full `STORYMODULE` chain (that's the natural follow-on: point the real storyteller's World at `genome_load`/`genome_genes`).
- The two illustrative semantic drifts are well-known etymology; a production era-dictionary uses real period sources (OED historical, Johnson 1755, …).

## Verdict
**The two steps are done: Siona's knowledge is genome-backed, and it carries an era-aware dictionary kernel.** Siona introspects the genome to know what it holds, pages the era-correct dictionary by context, renders the era-correct definition, and asks when it lacks one — definitions bound to a NOW via the chromosome label + MPR timestamp. This is GENOMEPLAN Stage 3's first inhabitant on the rc149 substrate, and the concrete start of Siona LM progress.
