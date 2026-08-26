# F740 — storyteller + etak-walk wired into the genome; MFO + srmech notebooks now in Siona's genepool

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F739 (genome-backed Siona + era-dictionary), F737 (foundational language layer), F735 (SignWriting), F704 (etak = grounded walk), STORYMODULE/STORYAPI/SIONASERVER (the storyteller), §46 GENOMEPLAN Stage 3 · **User direction (2026-06-14):** wire storyteller/etak-walk into genome; put the foundational MFO + srmech research notebooks in the Siona genepool. · **Provenance:** `R-RBS-LM-SIONAGENEPOOL_storyteller_etak_walk_over_genome_with_notebooks.py` (runs on rc149)

## The era-dictionary scope, clarified (user)
Packing a `dict-en-1600` is fine — *we don't create the translation*. The deferral-to-specialists is for **items of antiquity with no clean translation**. Shipping current-gen + 1600 en dictionaries **demonstrates the mechanism and lets us test as we go** — era-context translation is a fair, bounded skill for Siona.

## Build 1 — storyteller + etak-walk wired into the genome
`SionaGenepool` is STORYMODULE's World, **genome-backed**: it **introspects** (`genome_catalog` → its own inventory), **routes** a prompt to a chromosome, **etak-walks** it (`genome_genes` pages the chromosome, then navigates to the matching section — F704 "thinking is a grounded walk"), and **renders** the MPR payload or **asks** on a gap (F661). The `SIONASERVER /v1` would import this as its World in place of the hardcoded demo shelf. Verified answers:
- *"what is MFO about chirality?"* → routes `mfo_notebook` → etak-walks to **§Part I — Framing** → renders the real text: *"All matter and force fields are harmonic excitations of a single metric field…"*
- *"explain the srmech A-N classes"* → `srmech_notebook` → **§2.6 `1+3+7+3=14`** → the real section text.
- *"1600s … define awful"* → `dict-en-1600`; *"modern … awful"* → `dict-en-2026` → "very bad"; *"qwérty"* → asking-state.

## Build 2 — the foundational notebooks are in the genepool
Siona's genepool genome now holds **6 chromosomes**: `siona_identity`, `signwriting` (7 ISWA genes), `dict-en-1600` + `dict-en-2026` (5 words each), **`mfo_notebook` (16 Part-genes)**, **`srmech_notebook` (44 §-genes)**. Each notebook section is a GENE (content-addressed); the renderable text (heading + first line) is MPR-attested payload (`genepool.ndjson`). So MFO (the ontology) and srmech (the mechanism) are Siona's foundational, introspectable self-knowledge.

## etak-walk = the genome supplies structure, etak supplies the walk
The walk is: introspect → page the chromosome (`genome_genes`) → navigate to the nearest landmark. The nearest-section here is a **legible term-overlap placeholder**; the **semantic** nearest-section is the WIKIKERNEL co-occurrence-Laplacian follow-on (F724). The genome gives the navigable sectional structure; etak gives the grounded walk over it.

## Honest scope
- Notebooks are stored as **section-gene structure + MPR payload** (heading + first line) — not deep per-paragraph encoding (that's the WIKIKERNEL pipeline). Enough for introspection + section-level rendering today.
- This is a **research-subtree scaffold** composing `genome.*` + the storyteller pattern + the etak walk; pointing the LITERAL `STORYMODULE`/`STORYAPI`/`SIONASERVER` World at it is the same wiring (`World.recall` → `genome_genes`/`genome_catalog`), the natural next commit.
- Era-dictionary text + notebook text are MPR-attested payload (AMSC content layer), not the structural sidecar §44 rejects.

## Verdict
**Done:** the storyteller is genome-backed with an etak-walk over the genepool, and the MFO + srmech notebooks are in Siona's genepool — she introspects her own store, walks to the right kernel/section, and renders real foundational content (or asks). This is GENOMEPLAN Stage 3 maturing: the foundational language layer (F737) + the framework's own notebooks, all on the one biology-faithful substrate, navigated by etak.
