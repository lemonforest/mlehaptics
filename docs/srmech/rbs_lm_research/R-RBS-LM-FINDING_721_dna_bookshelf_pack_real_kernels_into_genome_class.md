# Finding 721 — the DNA bookshelf: packing our loose kernels into the Genome class; the rc42 chromosomal storage surface, exercised end-to-end

**Script:** `R-RBS-LM-DNABOOKSHELF_pack_real_kernels_into_the_genome_class.py`
**Status:** VERIFIED (srmech 0.7.5rc42, numpy-free)
**User direction:** *"see how our genome class works and test our chromosomal storage surface … create our DNA
bookshelf. this part will just be a matter of packing our loose kernels into a structured class, right? and we
also get to test the new surface."*

## Yes — packing is structured shelving (confirmed)

The Genome class is a **storage container**, so building the bookshelf is exactly a packing exercise: each loose
kernel → **content-addressed Klein-4 leaves** (one tome per concept, Class A → Class M) → a **telomere-capped
chromosome**, all coupled through `the_one`. It does **not** recompute the kernels; it shelves them. We packed
**five real kernels from this session** — `etak`, `cortana`, `siona`, `genome_model`, `an_vocab` (the 14 A-N
classes) — into one genome strand: **48 elements = 43 quad-turns + 5 telomere caps**, content-address bounded.

## The surface, exercised three ways (all pass)

| layer | what was tested | result |
|---|---|---|
| **(A) flat** `srmech.amsc.genome` | `genome()` assemble → `partition()` back | round-trip **reversible** through the_one ✓ |
| **(B) class** `make_class("Genome")` | `add_chromosome` ×5 → `assemble` / `recall` / `shape` / `cap` | class `assemble()` **== flat** `genome()`; `recall('siona')` exact ✓ |
| **(C) bring-your-own** `register_class_dir` | a `Codex` "school" (folio/colophon/shelve) over the **same** ops | **identical** strand; `provenance: 'user'` ✓ |

(C) is the F716 "class names for your school of choice" made concrete: **Codex** is a librarian's vocabulary
(`shelve` = `genome`, `colophon` = `telomere`) binding to the *same* `srmech.amsc.genome` ops — and it produces the
**byte-identical strand** the biology-named `Genome` does, attested `provenance: 'user'`, with the shipped name
un-shadowed. Same substrate ops, a different school's names — exactly the projection-vs-invariant reading.

## Granularity note (honest)

`encode_shape(n)` reports the **block-packed minimum**: n ≤ 256 → `tome` (1 leaf), because up to 256 items fit one
dense ≤256 block. The bookshelf here is packed **concept-granular** instead — **one leaf per concept** — so each
concept is an *individually recallable* quad-turn (a 14-concept kernel → 14 turns, not 1 block). **Both are valid
and the surface supports either**: dense-pack a small kernel into one tome (matches `encode_shape`), or shelve it
concept-granular for per-item recall (what we did). The choice is a recall-granularity decision, not a correctness
one — flagged so the manifest's "1 tome" and the strand's "43 turns" aren't read as a mismatch.

## What this confirms about the new surface

- The **chromosomal storage surface is real and lossless**: assemble → partition/recall recovers every kernel's
  leaves exactly, by telomere label, through the reversible `the_one` coupling — never quantized (F49/F50),
  content-address bounded (the whole-shelf fingerprint is the bounding).
- The **flat and class surfaces are consistent** (`assemble()` == `genome()`), so a researcher can script either
  the low-level ops or the declarative class with the same result.
- **Bring-your-own classes work** end-to-end (register → make_class → run → attested provenance), so the storage
  structure travels under whatever discipline's vocabulary the user brings.

**Next (optional):** shelve a *large* kernel (the F708 uncapped wiki vocab) so a chromosome is a genuine
`quad_strand` (depth ≥ 2) rather than five `tome`-scale books — that exercises the paging/depth path the small
session kernels don't reach.

**Composes:** F716 (genome surface + class-from-TOML + school-of-choice) · F715/F713 (chromosome/telomere/the_one) ·
F708/F712 (encode criterion, no-magic 256/1024) · F718–F720 (the kernels shelved here) · F49/F50 (no quantization).
srmech 0.7.5rc42. Held open (F394).
