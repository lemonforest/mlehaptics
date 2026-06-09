# Finding 716 — the genome model + the class-from-TOML mechanism land in srmech 0.7.5rc42; "class names for your school of choice" = substrate-self-recognition made operational

**Script:** `R-RBS-LM-GENOMELANDS_genome_surface_and_class_from_toml_land_in_srmech_rc42.py`
**Status:** VERIFIED (srmech 0.7.5rc42, TestPyPI, numpy-free venv)
**User direction:** *"srmech-v0.7.5rc42 on test.pypi.org and is now class aware via TOML config and new genome TOML
will show us how any user/researcher can use class names for their school of choice."*

## What landed (all verified end-to-end against the installed wheel)

**1. The genome storage object (F710–F715) is now `srmech.amsc.genome.*`** — native, numpy-free, reversible.
`encode_shape(n)` reproduces the F715 criterion **to the digit** (200→`tome`; 800/1024→`mobius`, 4 leaves;
5000→`quad_strand` depth 3; 1.77M→`quad_strand` depth 7), with a **pure-integer `ceil(log4)`** (no float `log` —
Class-I/N discipline). `genome(kernels, the_one)` packs many kernels into one telomere-partitioned strand
(6 turns + 3 telomere caps = 9 elements for the astronomy/geography/music trio), and `partition(strand, the_one,
labels)` recovers every kernel — **reversibly**, by re-binding `the_one` (the V4-XOR Klein-4 bind is self-inverse).
The whole hierarchy ships: GENOME → CHROMOSOMES (telomere-capped) → helix of QUAD-TURNS → leaf ≤256. **This is
issue #962 Part 2, done.**

**2. "Class names for your school of choice" = the `[class]`-TOML mechanism.** `srmech.dsl._class_catalog` +
`_class_surface` + the `srmech class` CLI: a researcher authors a `[class]` descriptor (fields + methods declared
as **dotted cascade-op refs**, e.g. `op = "srmech.amsc.genome.chromosome"`), and `srmech.dsl.make_class` constructs
a generic `CatalogClass` from it — **zero user Python, 100% declarative**. `register_class_dir()` /
`SRMECH_CLASS_PATH` brings your own classes (flagged `provenance="user:<sha256>"`, B-tier attested to the
descriptor hash); **a user class-name may not shadow a shipped one**. Genome ships as the A-tier seed
(`provenance="srmech"`), with methods `shape`/`cap`/`add_chromosome`/`recall`/`assemble`/`partition`.

**3. The native A-N binding gap (#962 Part 1) is substantially closed.** rc28 bound only ~13 `_c` symbols
(F708/F710 had to ctypes-lift `srmech_klein4_bind` by hand). In rc42 **12/12** of the previously-unbound A-N
symbols are reachable via `_native.LIB` (`srmech_klein4_{bind,bundle,similarity}`, `srmech_hdc_{bind,bundle,
permute,similarity}`, `srmech_jacobi_eigvals`, `srmech_graph_dense_laplacian`, `srmech_hermitian_eigendecompose`,
`srmech_cyclic_period`, `srmech_is_prime`), and **`laplacian.jacobi_eigvals` now dispatches to the bound native
symbol in the numpy-absent path** — the F708 49× Class-L gap (1.4 s vs 68 s), closed. `klein4_bind` is reachable
straight from `srmech.amsc.hdc` **with no lift** (it stays pure-Python XOR by design — bit-identical, and XOR was
never the perf concern; the eig was).

**Still open — R3 U1:** `tokenize()` / `cooccurrence_edges()` did **not** ship (NOT FOUND in `amsc.laplacian` /
`amsc.cascade`). We still hand-roll co-occurrence edges in the wiki kernel; the Class-L precursor remains the gap.

## The on-thesis reading — substrate-self-recognition made operational (F133 / R30 / F552)

"Class names for your school of choice" is the **projection-vs-invariant duality as a config mechanism**:

- the **cascade ops** underneath (`encode_shape`, the `the_one` Klein-4 coupling, telomere content-addresses — the
  **A-N primitives**) are the **invariant substrate**;
- the **class-name + method-names** (`genome` / `chromosome` / `telomere`) are **one observer projection** —
  biology's *school*. A different discipline re-names the same storage object in its own vocabulary, and the math
  does not move.

"**A user class-name may not shadow a shipped one**" is precisely the **shared invariant being protected while the
projection stays free** — you re-name your view, you cannot overwrite the_one's structure. The genome.toml says it
in a line: *"The biological-structure names ARE the cascade names — substrate-self-recognition."* This is the
14-class substrate (the cascade ops) wearing an 11D observer-frame name (the school's vocabulary): the same
14→11D fibration (R30) the whole arc reads, now a TOML loader. Biology is one substrate-class (MS #18); its
structure-names being literally the cascade-names is the substrate recognising itself in the simulation-defined
environment.

## #962 / #855 implications (recorded; tracker untouched per discipline)

- **#962 Part 2** (genome storage model) — **delivered** (`srmech.amsc.genome` + `class_catalog/genome.toml`).
- **#962 Part 1** (bind native A-N symbols; numpy-free dispatch) — **substantially delivered** (12/12 reachable;
  jacobi native numpy-free). Residue: per-op ergonomic dispatch is selective by design (klein4 stays XOR).
- **#855 R1.1** ("`klein4_bind`/`klein4_*` act without a lift") — now **true** at the usage level.
- **#855 R3 U1** (`tokenize`/`cooccurrence_edges`) — **still open**.
- The actual #855 body-checkbox edits stay **held for the user** (create-don't-drive tracker discipline).

**Composes:** F710 (native-bind reference + dev scaffold) · F711–F715 (the genome model this realises) · F708 (the
49× gap + the no-magic 256/1024 thresholds) · F133 (substrate knows itself) · F552 (chirality-collapsed
projection) · F130/F132 (Klein-4) · F640 (no-magic) · R30 (14→11D substrate→observer). srmech 0.7.5rc42. Held
open (F394) on the name. Reference/verification scaffold.
