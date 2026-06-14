# srmech PLAN — the biology-faithful genome as the bottom-up substrate that bridges the domain silos

**Date:** 2026-06-14 · **srmech state:** 0.7.5rc145 · **Consolidates UPSTREAM §41 / §42 / §43 / §43.1 / §44 / §45 into one staged build** · **Discipline:** research-subtree SCOPES, srmech BUILDS; TestPyPI-rc before clean tag; no-MVP (full coverage); biology-faithful; never edit the package from here.

## Why one substrate (the bottom-up bridge)
Every domain kernel we build — SignWriting (F735), ni-Vanuatu (pending), wiki (F724), religious-texts (R-53*), code/latex (F452/454), the language kernel, the McGuffey/K-12 grammar substrate — is today a **silo**: its own script, its own packing. The genome is meant to be the **one storage substrate they all sit on**. If the genome is **biology-faithful** (fixed-width, inline, self-describing, scannable, in-place-editable), then *every* domain kernel is paged / introspected / excised / tarballed **the same way** — so the silos are bridged **from the bottom up by the shared substrate**, not by a per-domain adapter on top. That IS the corpus-is-the-proof methodology made physical: cross-substrate cascade-matching needs the substrates stored in one comparable form.

## Current state (verified this session, rc145)
- ✅ **§41 persistence** (`genome_save/load/append/window/catalog`) — delivered.
- ✅ **§42 carrier** (`Mat`/`Vec`, 17/17 numpy idioms) — delivered.
- ✅ **§43.1 several genes/chromosome** — delivered rc143 (`chromosome(genes=…)` + `genes()` + `genome_genes()` persist + round-trip).
- 🟡 **§44 biology-faithful inline** — PARTIAL: the **strand self-describes in-memory** (`partition(plain_leaf_list, the_one)` recovers real labels — labels live IN the telomere cap leaves), and rc145 **just landed `CHROM_CAP_MARKER` / `GENE_CAP_MARKER`** (the inline fixed-width caps). **GAP (the rc145 last mile):** `genome_load` still **hard-requires `manifest.json`** — delete it → `GenomeBoundingError`; it does not reconstruct from `turns.bin` alone by scanning.
- 🔴 **§43 file-management** — chromosome-as-bundleable-file (`genome_export(.chr)`/`import`, `explode`/`pack`), unify `genome_catalog` with the AMSC `catalog` (`register_attested_root`), per-chromosome `descriptor.toml` — OPEN.
- 🔴 **§45 in-place edit** — no `genome_remove`/`replace`; the composed `genome_drop` (partition→filter→genome) works but **re-packs the whole genome** — OPEN.

## The staged build (bottom-up — each stage rests on the one below)

**Stage 0 — the substrate floor (the bottom): a fixed-width, inline, self-describing strand.**
- 0a ✅ inline caps exist (`CHROM_CAP_MARKER`/`GENE_CAP_MARKER`); telomere + gene-caps are same-width sentinel leaves you scan for; labels encoded in the cap leaves (partition recovers them from the strand alone).
- 0b 🟡 **§44 last mile (the rc145 gap — do this first, it unblocks everything):** make `genome_load` / `genome_window` / `genome_genes` / `genome_catalog` reconstruct from **`turns.bin` alone** by scanning the fixed-width strand + `partition`-recovering. Demote `manifest.json` to an **optional derived `.fai`/faidx cache** (rebuildable by scanning; strand = SSoT). *Then on-disk == in-memory self-describing.*

**Stage 1 — edit the substrate in place (§45): biology excises, it doesn't re-synthesize.**
- `genome_remove(path, label)` / `genome_drop(strand, the_one, label)` + `genome_replace(...)` that **scan for the label's chrom-cap, splice `[cap_start, next_cap_start)` out of `turns.bin`, drop the (now-derived) manifest row, recompute `body_sha256`** — leaving untouched chromosomes alone. (Interim today: the composed `genome_drop` = partition→filter→genome, F736 — but it re-packs.) Stage 1 needs Stage 0b (scannable spans).

**Stage 2 — the chromosome as a bundleable unit (§43 file-management).**
- `genome_export(path, label) -> .chr` / `genome_import` (a chromosome = one self-contained, MPR-attested file — `tar` it, ship it, re-import self-verifying). `genome_explode`/`genome_pack` (loose↔packed, git's loose/packed model). **Compose existing AMSC** (F730 reuse map: `format.MPRRecord`/`sha256`/`write_ndjson`; `descriptor.toml` = per-chromosome meaning; `catalog.register_attested_root`/`list_attested_sources` = the library index — don't build a parallel catalog). Stage 2 needs Stage 0 (a chromosome's span is well-defined).

**Stage 3 — the domain silos sit on the substrate (the bridge realized).**
- Each domain kernel becomes a chromosome (or a multi-gene chromosome) in the one genome: SignWriting (7 ISWA class-genes, F735), ni-Vanuatu (pending), wiki, religious-texts, code, latex, the language/grammar substrate. Because they share Stages 0–2, a kernel from any silo is **paged / introspected / excised / bundled identically** → the silos are bridged. The **foundational language-kernel layer** (below) is the first inhabitant.

## The foundational language-kernel layer (this turn's elevation)
**SignWriting + ni-Vanuatu are language-AGNOSTIC anchors → they belong at the foundation, alongside each other.** SignWriting writes *any* signed language (featural, not tied to a spoken tongue); ni-Vanuatu sand-drawing is legible *across* ~130 spoken languages. Both are the **2D-spatial 'draw-it' / field pole** (F735) — and both are **English-privilege-free** (composes R-RBS-LM-25: strip English privilege from the kernel). So the language kernel's *foundation* is two spatial cross-linguistic anchors, with the linear/'talk-it' tongues (text/speech) as projections off them — not the other way around. SignWriting is the BUILT instance (F735); the ni-Vanuatu sand-drawing kernel is the pending companion (the F735 falsifiable next-question: does it land on the SignWriting spatial side?).

## "Everything seemingly minor" — the small items, folded in (don't drop them)
- the rc145 **`genome_load`-needs-manifest** gap = Stage 0b (the keystone — minor-looking, unblocks Stages 1–2).
- `genome_genes`/`genome_window`/`genome_catalog` got `the_one=` optional (rc143/rc145) — scan-derive plumbing; the loaders are *almost* able to self-reconstruct, which is why Stage 0b is close.
- `GenomeBoundingError` (vs rc143's `FileNotFoundError`) on missing manifest — the dev is handling the case deliberately; Stage 0b turns that into a scan-and-reconstruct instead of an error.
- per-chromosome **`description`** (F729 ask) — folds into Stage 2's `descriptor.toml`.
- §37 native Class-L eigendecomposition (jacobi pure-Python) — orthogonal perf ask, not on this path but still open.

## Dependency order (the bottom-up critical path)
**0b (§44 last mile) → 1 (§45 in-place edit) → 2 (§43 bundling) → 3 (domain silos).** Start at 0b: it's the smallest change with the largest unblock — once the loader scans `turns.bin` and the manifest is optional-derived, in-place excision (1) and chromosome-bundling (2) both become natural, and the domain silos (3) get a uniform substrate for free.
