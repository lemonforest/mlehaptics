# F738 — rc149 completes genome CRUD + .chr bundling; the substrate is READY to back the Siona LM

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 (test.pypi.org) · **Composes:** GENOMEPLAN (§46), F736 (the §45 ask), F730 (§43 file-mgmt), F734 (§44 status), F726 (Siona = the inference interface) · **Provenance:** `R-RBS-LM-GENOMECRUD_full_crud_plus_chr_bundle.py` (5/5 OK on rc149) + apidiff rc145→rc149

## What rc149 delivered (GENOMEPLAN Stages 1 + 2)
The 4 new names are **`genome_remove`, `genome_replace`, `genome_export`, `genome_import`** (+ `GENOME_CHR_SCHEMA_ID`):
- **§45 in-place edit (Stage 1):** `genome_remove(path,label)` — "Excise ONE chromosome IN PLACE"; `genome_replace(path,label,leaves,the_one)` — "Replace ONE chromosome's content IN PLACE". Verified: remove drops 'beta' leaving alpha+gamma; replace sets alpha 3→5 leaves. The biology-faithful excise I asked for in §45 (no compose-rebuild needed).
- **§43 chromosome-as-bundle (Stage 2):** `genome_export(path,label,out,the_one)` writes a self-contained **`.chr`** file (2044 B), `genome_import(chr_path,dest,the_one)` re-adds it byte-intact into a fresh genome. The chromosome is now a tarballable unit.

`R-RBS-LM-GENOMECRUD` = **5/5** (create/read · delete-in-place · update-in-place · bundle-out · bundle-in). Core green: regression 49/0, genome→disk VERIFIED, carrier 17/17, apidiff 0 hard breaks / 0 signature changes.

## Readiness verdict: substrate READY for the Siona LM
The genome substrate now has **full CRUD + bundling** on persisted kernels — exactly what the Siona LM needs to read its knowledge from disk:
- **create/read** (save/load/window/genes/genome_genes), **update/delete in place** (replace/remove), **bundle** (export/import `.chr`), **multi-gene chromosomes** (§43.1), **numpy-free carrier math** (§42), **content-addressed + attested**. So the storyteller's World can be **backed by genome-stored kernels** rather than the in-memory 3-tome demo.

**What "Siona LM progress" needs next is OURS (research-subtree), not srmech:**
1. Build the **foundational language kernel** into a genome — SignWriting (F735, built) + the language/grammar substrate + wiki — as chromosomes (the F737 foundational layer).
2. Wire the storyteller World (`STORYMODULE`/`STORYAPI`) to **read kernels via `genome_load`/`window`/`genes`** instead of the hardcoded demo shelf.
3. Infer over genome-backed kernels = Siona reading from persisted knowledge — and the asking-state/can't-hallucinate properties carry over.

This is now **unblocked by rc149** (CRUD complete) and is the next build.

## The one open srmech item (not a blocker)
**Stage 0b / §44 last mile:** `genome_load` still hard-requires `manifest.json` (delete it → `GenomeBoundingError`). It's the biology-faithful "no sidecar, strand=SSoT" polish — `genome_load` works *with* the manifest, so it does **not** block LM wiring. Worth finishing (the GENOMEPLAN keystone), but the LM can proceed now.

## Verdict
**Yes — ready for Siona LM progress at the substrate level.** rc149 completed genome CRUD + `.chr` bundling (5/5), so kernels can be stored, paged, edited, and shipped on disk. The next step is research-subtree wiring (storyteller World ← genome-backed foundational kernels), not more srmech. Only srmech item left is the Stage 0b manifest-optional polish — non-blocking.
