# F733 — the genome diverged from biology: "fixed-width" (dev) and "no sidecar manifest" (user) are the SAME ask

**Date:** 2026-06-14 · **srmech:** 0.7.5rc141 (test.pypi.org) · **Composes:** §43/§43.1 (the TLV gene-frame — root of the divergence), F730/F732 (genes), F715 (telomere), CLAUDE §0 (biology is a wire-format) · **Provenance:** rc141 apidiff + genome layout inspection + the `genome(chromosomes=)` `TypeError` repro · **→ UPSTREAM §44**

## The diagnosis
The srmech dev wants **fixed-width**; the user wants **no sidecar manifest** ("follow biology"). These are **one requirement**: biology has no offset table — structure is found by **scanning the strand for fixed-width inline markers** (TTAGGG telomere repeats, ATG/stop codons), and **fixed-width is precisely what makes an offset-sidecar unnecessary** (fixed-width records + inline fixed-width caps ⇒ random-access by `index × width` + boundary-by-scan ⇒ no byte-offset index needed).

## Where it diverged (root cause, owned)
My **§43 scoping recommended TLV (Class B) for the gene-frame — which is VARIABLE-length** (length prefix). Variable-length *forces* a sidecar offset table. So rc141 responded by adding a **`genome_save(..., gene_index=)` sidecar** + `genome_genes(path,label)` (sidecar-paged), and `genome(chromosomes=…)` is **half-wired and BROKEN** (`TypeError: int() … not 'HV'` in `_split_into_chromosomes`). Today `turns.bin` is fixed-width and telomere caps are inline, **but the label↔chromosome map + byte-offsets live only in `manifest.json`** — the un-biological part. (Flat path stays green: regression 49/0, genome→disk VERIFIED, carrier 17/17.)

## The fix (UPSTREAM §44 — replaces the TLV approach)
1. **Gene boundary = fixed-width inline GENE-CAP leaf** (telomere-analog), scanned for — not a TLV length-prefix.
2. **Label inline** (fixed-width leaves), not sidecar-only — the strand self-describes.
3. **`window`/`genes`/`genome_genes`/`catalog` SCAN the fixed-width strand**, not seek via offsets.
4. **`manifest.json` → optional DERIVED index** (a `.fai`/faidx analog, rebuildable by scanning) — the strand is the SSoT. (FASTA is inline self-describing; `.fai` is an optional cache.)
5. **Fix the rc141 `genome(chromosomes=)`/`genome_save` breakage the fixed-width way**, not by extending `gene_index`.

## Verdict
Not "go fix the package" (research-subtree discipline — we scope, srmech builds): the redesign is lodged as **§44**. Net target: one fixed-width, inline, self-describing strand per chromosome — scannable, arithmetic-seekable, tarball-able as a unit (the §43 goal) **without a sidecar**. This is biology's own wire-format: nested fixed-width inline framing (telomere = chromosome cap, gene-cap = gene cap), Class B done the biological way.
