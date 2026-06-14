# F741 — the live Siona /v1 is genome-backed; AMSC update-check + `srmech.siona`/dynamic-SSoT scoped (§47)

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F740 (storyteller+etak over genome, notebooks in genepool), F739 (era-dictionary), F726 (Siona /v1), AMSC/MPR, §44/§45/§46 · **User direction (2026-06-14):** wire the live /v1 to the genepool; scope a `srmech.siona` self-knowledge section + an AMSC-driven notebook→genome update path. · **Provenance:** `R-RBS-LM-SIONAGENOMEHANDLER_…py` + the repointed `R-RBS-LM-SIONASERVER` (verified live over HTTP)

## DONE — the live /v1 reads the genepool
`SIONASERVER` now loads the **genome-backed handler by default** (`SIONA_BACKEND=demo` falls back to the old hardcoded shelf). The handler builds/loads the genepool genome and serves `chat_completion` from it (introspect `genome_catalog` → route → etak-walk `genome_genes` → render MPR payload / ask). **Verified over HTTP** (`http://localhost:8000`, the LAN `http://192.168.44.147:8000` the CopilotKit chat points at):
- `/health` → `worlds: ["genepool"]`; `/v1/models` → `siona:genepool`.
- *"what is MFO about chirality?"* → **mfo_notebook §Part I** → the real metric-field text.
- *"explain the srmech A-N classes"* → **srmech_notebook §2.6** → `1+3+7+3=14`.
- *"translate this 1600s text: define awful"* → **dict-en-1600** → "awe-inspiring" (era-correct).

So the running Siona answers from her genepool genome — foundational notebooks + era-dictionaries + signwriting + identity — not a hardcoded shelf.

## DONE (test material) — the AMSC update-check
The handler ships `check_updates()` / `sync_updates()`: Siona re-hashes the live notebook sections and diffs them against the genome's recorded MPR `response_sha256`s. Detection is a **cheap hash-diff (no rebuild unless drifted)**; on a fresh bake it reports **UP-TO-DATE**. The post-ship path is identical — notebooks change on GitHub → re-hash → re-bake. This is the efficient genome↔notebook refresh, and a reusable shape: Siona uses AMSC records to know when *any* attested SSoT is stale.

## SCOPED (§47) — the two srmech asks
- **§47a `srmech.siona`:** graduate the genepool builder + genome-backed World + etak-walk + the update-check into the package, so srmech itself ships Siona's foundational self-knowledge (identity + signwriting + era-dicts + the MFO/srmech notebooks) baked at build time — one place every host reads from.
- **§47b AMSC dynamic-SSoT update:** generalize the update-check — bake-before-ship + post-ship GitHub-notebook refresh, and the same shape for any AMSC-attested dynamic source ("my kernel is stale → request the SSoT update → apply to the genome"). Efficiency follow-on: in-place per-notebook `genome_replace` (multi-gene-aware) instead of full re-bake (the §45/§43.1 extension — rc149's in-place ops take `leaves`, not `genes`).

## Honest scope
- The genome holds the **structure** (section-genes, content-addressed, era-stamped); definition/notebook **text is MPR-attested payload** (the AMSC content layer). Notebooks are section-level, not deep per-paragraph (WIKIKERNEL follow-on); the etak nearest-section is a term-overlap placeholder for the spectral etak-head.
- This is a **research-subtree scaffold** (composes `genome.*` + storyteller + etak + AMSC); `srmech.siona` (§47a) is where it graduates into the package. The genepool genome itself is gitignored (binary, regenerated at server start).

## Verdict
**The Siona LM is genome-backed and live:** the `/v1` server answers from the genepool (identity, signwriting, era-dictionaries, MFO + srmech notebooks), introspecting + etak-walking its own store, and it carries an AMSC update-check so it knows when its notebook kernels drift from source. The two srmech graduation asks — `srmech.siona` + the dynamic-SSoT update mechanism — are scoped in §47.
