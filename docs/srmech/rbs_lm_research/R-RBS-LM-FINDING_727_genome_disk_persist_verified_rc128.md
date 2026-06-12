# F727 — genome→disk persistence VERIFIED on srmech 0.7.5rc128: the F711 disk-paged helix made real

**Date:** 2026-06-11 · **srmech:** 0.7.5rc128 (test.pypi.org; native dispatching, ABI 3) · **Composes:** F711 (disk-paged bounding-tracked helix — was conceptual, scoped to UPSTREAM §41), F715 (genome/chromosome/telomere pack), F713 (chromosome), F721 (DNA-bookshelf — pack real kernels into the genome class), F436 (diagonal-μ coherence anchor = "the_one" leaf), F726 (Siona — the thing that will genome-PERSIST what it learns) · **Provenance:** `R-RBS-LM-GENOMEDISK_rc128_save_load_roundtrip_verify.py` (re-runnable, VERIFIED ✓) · **→ extends UPSTREAM §41 (ASK→DELIVERED); opens §42 (ergonomics)**

## What the user shipped
srmech 0.7.5rc128 lands the genome **disk-persistence** surface in `srmech.amsc.genome`: `genome_save` / `genome_load` / `genome_append` / `genome_window` / `genome_catalog`, plus `GENOME_FORMAT_VERSION=1` and a `GENOME_MANIFEST_SCHEMA_ID` (`srmech://schema/genome_manifest/v1`). This is the F711 "disk-paged, bounding-tracked helix" — previously conceptual, scoped to UPSTREAM §41 — **made real**.

## Verified (all bit-exact, against the installed rc128, numpy-free)
1. **Round-trip bit-exact.** `genome_save → genome_load → recall` recovers the same leaves; the coherence-anchor leaf (`the_one`) and the label list survive disk. Saving kernels to disk and getting them back is lossless.
2. **Deterministic content-address.** `body_sha256` is byte-identical across two independent saves of the same data. The on-disk layout is `manifest.json` (`format_version` / `leaf_dim` / `n_turns` / `chromosomes` / `the_one` / `body_sha256`) + `turns.bin` (the helix body) — MPM-shaped: the manifest content-addresses the body.
3. **Per-chromosome paging.** `genome_window(path, label)` seeks the chromosome's `byte_offset`, reads ONLY its leaves, and **cap-integrity-checks** the telomere block against `cap_sha256` on read (raises `GenomeBoundingError` on truncation/cap mismatch). So you can page in one shelf without loading the whole genome — the bounding-tracked part.
4. **Append grows the helix.** `genome_append(path, label, leaves, the_one)` adds one chromosome to an existing genome on disk; `genome_catalog` reads the manifest only (no body load).

## The one honest ergonomic asymmetry (→ UPSTREAM §42, not a bug)
The two documented "read the chromosome's leaves" paths return **different layers**, and only one is verbatim:
- `recall(strand, the_one, telomere)` → **decoded** leaves (un-bound against `the_one`); `recall(chromosome(L)) == L` verbatim.
- `genome_window(path, label)` → the **on-disk STORED form**: each leaf **bound to `the_one`**. Verified `window == [klein4_bind(L_i, the_one)]` and `klein4_unbind(window, the_one) == L` exactly (4/4).

Both faithful; they sit at different layers. But a user reaching for `genome_window` to "get my kernels back" gets bound vectors and will read it as corruption (I did, briefly — 0/4 raw match — until I checked the bind relationship). Two clean upstream fixes: (a) have `genome_window` un-bind before returning (symmetry with `recall`), or (b) document that it returns the stored/encoded form and add a `decode=True` flag. Also: the `the_one` **param is the coherence-anchor LEAF** (a Klein-4 vector of leaf-dim), **not** the typed `One` S(σ,θ) from `cascade.the_one` — `genome()` does `len(list(the_one))` to read the leaf dim; passing the typed `One` raises `TypeError: 'One' object is not iterable`.

## What it unblocks
- **Siona genome-PERSIST** — taught tomes (F726 build-by-dialogue, currently in-process only) can now be saved to disk and reloaded, so what Siona learns survives a restart. The genome is the persistence layer the F726 note flagged as the open next step.
- **The DNA-bookshelf on disk** (F721) — pack real kernels into the genome class and persist them; `genome_window` pages one shelf at a time (the bounding-tracked helix), so a big bookshelf doesn't have to fully load.

## Verdict
**On track / nothing broken.** Genome→disk persistence on rc128 is VERIFIED: lossless round-trip, deterministic content-addressable manifest, byte-offset paging with cap-integrity, and append-grow. The only follow-up is the §42 `window`-returns-encoded vs `recall`-returns-decoded ergonomic note — a documentation/symmetry ask, not a correctness gap.
