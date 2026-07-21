# C-host-standalone parity audit — genome op family (rc258–rc273 + laplacian deps)

**Audited against** `origin/main` @ `6e0cbc893` (srmech v0.9.0rc273; local tree was 3 commits behind — read via `git show origin/main:…`).
**Standard:** ADR-0003 (C-host-standalone). **Method:** per-op read of the Python body, grep of `srmech_genome_*` C decls (`srmech.h`) + defs (`srmech_genome.c`) + `_native.py` dispatchers, cross-check vs `rosetta_classification.ndjson` + the two rosetta ratchets. Adversarial: labels + docstrings treated as claims to refute.

## 0. The systemic root cause (why honest-looking labels hide gaps)

Two "standalone-ready" standards disagree, and the disagreement is unenforced:

- **Rosetta `composition_of_c`** = "pure composition of c_dispatched ops" (`test_rosetta_completeness.py`). Verified by `test_rosetta_transitive_standalone.py`, which walks the callee graph but (a) treats every `composition_of_c` op as a **leaf** and stops, and (b) flags only three explicit debt buckets (`bignum_reference`/`python_only_debt`/`c_exists_unbound`). So it proves a composite *reaches* C-backed leaves — it never proves a bare-C host can run the composite's own **glue**.
- **ADR-0003 §2/§3** = every composite, *including orchestrators* (it names `mint`), "still gets its own C entry point so a C-only caller can invoke the whole operation."

The project applied ADR-0003-strict to the mature genome ops (they shipped `srmech_genome_mint/genome/chromosome/partition/recall/centromere_of/chromatin_of`). The gaps are the ops that got the **rosetta-loose** treatment instead: labeled standalone-ready while their orchestration (splice, boundary-scan, participation read, cap-rewrite, out-of-core recursion) lives only in Python. That is "a 1:1-parity gap wearing an honest-looking label."

## 1. Summary table

Verdict legend: **C-COMPLETE** (C entry exists; bare-C host does whole op — parity OK, may be under-labeled) · **GAP** (non-trivial Python-only orchestration, no C entry) · **HONEST** (trivially composable in C / native-dispatched scan + trivial read).

| Op | rosetta bucket | C peer? | Verdict |
|----|----|----|----|
| encode_shape, telomere, centromere, diploid, recover_diploid, telomere_tick, gene_express(/_levels/_plan), modulator_* | c_dispatched | yes | C-COMPLETE ✓ |
| genome / mint | composition_of_c | `srmech_genome_mint` (dispatches) | C-COMPLETE (under-labeled) |
| plasmid (kernels=) | composition_of_c | `srmech_genome_genome` (dispatches) | C-COMPLETE (under-labeled) |
| partition (strand) | composition_of_c | `srmech_genome_partition` (dispatches) | C-COMPLETE (under-labeled) |
| recall | composition_of_c | `srmech_genome_recall` (dispatches) | C-COMPLETE (under-labeled) |
| centromere_of | composition_of_c | `srmech_genome_centromere_of` (dispatches) | C-COMPLETE |
| chromatin_of | composition_of_c | `srmech_genome_chromatin_of` (scan) + inline handle | HONEST |
| quad_turn | composition_of_c | reversible bind primitive | HONEST |
| **integrate** | composition_of_c | **none** | **GAP** |
| **mint_strand** | composition_of_c | **none** (cap-writer only) | **GAP** |
| **genome_partition** (graph) | composition_of_c | **none** (name-collides w/ strand op) | **GAP** |
| **genome_from_graph** | composition_of_c | **none** | **GAP (compound)** |
| **recursive_cut** (laplacian dep) | composition_of_c | **none** (fiedler C only) | **GAP (deepest)** |
| **amplify** (rc273) | composition_of_c | **none** | **GAP** |
| **copy_number_of** (rc273) | composition_of_c | **none** | **GAP** |
| **condense** | composition_of_c | cap bytes only (`srmech_genome_chromatin`) | **GAP-lite** |
| **decondense** | composition_of_c | none (cap-filter) | GAP-minor |
| **active_telomere** | composition_of_c | none (packer) | GAP-minor |
| **genes** (in-memory) | composition_of_c | none (recall keeps split) | GAP-minor |
| **mint_plan** | composition_of_c | none (encode_shape read) | GAP-minor |
| plasmid (chromosomes=) / chromosome(genes=) | — | `srmech_genome_chromosome` is **plain-only** | GAP (secondary) |

## 2. GAPs ranked by severity, with corrections

Every signature below: `srmech_status_t`, caller-arena out buffer, byte-parity vs the Python oracle, JPL-clean (≤60 lines, ≥2 asserts, no goto/malloc, no `abs()` — sign/gate = Class-K equality read).

### G1 — recursive_cut (MOST load-bearing) — laplacian
Deepest shared dependency: `genome_partition` **and** `genome_from_graph` dead-end here, as does rc275's progress/cancel for the graph pipeline. Out-of-core recursive spectral bisection: Python `while pending` driver + on-disk tome management, calling `srmech_laplacian_fiedler_sparse_file` (c_dispatched) per bisection. The recursion + PAL tome I/O has no C entry.
**Correction:** `srmech_laplacian_recursive_cut(uint32_t n, const char *edges_path, const char *work_dir, uint32_t max_tome, uint32_t max_iters, uint32_t max_depth, uint32_t *tome_sizes_out, char *tome_paths_out, size_t paths_cap, uint32_t *n_tomes_out)` — PAL-mirrored tome read/write; loops fiedler internally. (Largest single build.)

### G2 — genome_from_graph (compound) — §100 GAP2 flagship
Transitively needs G1 + G3 + G5 plus its own Python glue (`_induced_subgraph` relabel, per-group `graph_to_kernel`→`mint_strand` loop, strand assembly, optional `genome_save`). `graph_to_kernel` IS c_dispatched (`srmech_graph_kernel_encode`); the assembly is not.
**Correction:** `srmech_genome_from_graph(...)` — lands after G1/G3/G5; composes them + `srmech_graph_kernel_encode` + `srmech_genome_save`.

### G3 — genome_partition (graph) — name-collision resolved
`srmech_genome_partition` EXISTS but is the **strand-recovery** op (inverse of `genome`) — a *different function sharing the name*, confirmed by the rc275 note §1.4. The graph `genome_partition(n, edges, …)` has NO C peer: it composes `recursive_cut` (G1) + a pure participation (O(|E|)) + antimode (O(n)) + per-node classify read, all Python. Not c_dispatched, not mislabeled — a genuine gap.
**Correction:** distinctly-named `srmech_laplacian_participation_partition(...)` (avoid the `srmech_genome_partition` collision); exact-integer participation `(num,den)` + antimode; composes G1.

### G4 — integrate — the rc262/rc273 claim refuted
Docstring: "a C-only host integrates identically by concatenating the two genomes' self-describing regions … the region byte-offsets are in the manifest." **Refuted:** `integrate` operates on an **in-memory strand (list of HV) — there is no manifest** at integrate-time; the boundary offsets must be derived by scanning caps (the same scan `partition` does), which has no C entry. The op = boundary-cap scan → `at`→locus computation → width-coherence gate (`len(host[0])==len(provirus[0])`, C-reproducible equality) → splice. The rc273 `compatible=` hook is correctly Python-only (a caller callable, like a callback — excluded from the C wire domain per the rc273 fixup). The GATE is C-reachable; the SPLICE orchestration is not.
**Correction:** `srmech_genome_integrate(const unsigned char *host, size_t host_blocks, const unsigned char *provirus, size_t prov_blocks, uint32_t leaf_dim, long at, unsigned char *out, size_t out_cap, size_t *n_blocks_out, int *integrated_out)` — `*integrated_out=0` on width-incoherence (honest-decline). ~40 lines. Self-contained (no dep on G1–G3).

### G5 — mint_strand — cap-writer C, glue Python
Every primitive exists in C (`srmech_genome_centromere` cap, `srmech_genome_recall` orientation preimage, `srmech_sha256_hex` fold) but the glue — data-turn position scan → midpoint/`centromere_at` → single-block insert — is Python-only. Docstring's "byte-identical whether the cap came from C or pure Python" covers only the cap bytes, not the whole op. Foundation for genome_from_graph + the streaming reader.
**Correction:** `srmech_genome_mint_strand(const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim, const unsigned char *coupling, long centromere_at, unsigned char orientation, int orientation_auto, uint32_t repeats, const unsigned char *handle, size_t handle_len, unsigned char *out, size_t out_cap, size_t *n_blocks_out)`. ~50 lines.

### G6 — amplify + copy_number_of (rc273 pair) — cleanest exhibit
The copy-number rides in `0x47` gene-cap NUL padding (uint64-BE after the label NUL) and is **byte-transparent to existing readers** — the rc273 C test proves `srmech_genome_gene_express` skips it and its comment concludes "no C change" needed. But transparent-to-readers ≠ C-host parity: there is NO C path to **WRITE** it (`amplify`→`_pack_gene_cap_copy_number`) or **READ its value** (`copy_number_of`→`_gene_copy_number`). A bare-C host can neither set nor get gene copy-number. Docstring "pure composition over the C-built strand (a cap rewrite)" is unbacked — the cap-rewrite has no C peer.
**Correction (pair):** `srmech_genome_amplify(strand, n_blocks, leaf_dim, label, label_len, uint64_t n, out, out_cap)` — find first `0x47` w/ label, rewrite w/ count (n==1 → plain, byte-identical; n≥2 spends the field), byte-copy rest (~35 lines); `srmech_genome_copy_number(strand, n_blocks, leaf_dim, label, label_len, uint64_t *count_out)` — read uint64-BE, all-NUL→1 (~25 lines).

### G7 — condense / decondense / active_telomere / genes / mint_plan (minor)
- **condense** GAP-lite: native cap bytes (`srmech_genome_chromatin`) but `_chrom_range`(label) + region resolution + splice are Python-only → `srmech_genome_condense(...)`.
- **decondense** minor: whole-strand form ≈ trivial `0x48` cap-filter; label-scoped form needs range-find glue.
- **active_telomere** minor: a single cap packer (`_pack_active_telomere`); the pack logic exists inside `srmech_genome_telomere_tick` (it mints daughter active caps) but is not exposed → `srmech_genome_active_telomere(...)` ~20 lines.
- **genes** minor: an in-memory recall-variant that keeps per-gene boundaries; `srmech_genome_recall` flattens, `srmech_genome_gene_express_plan` returns per-gene spans — neither returns the `(label,leaves)` split.
- **mint_plan** minor: a pure `encode_shape`-loop read (builds nothing).
- **Secondary:** `srmech_genome_chromosome` is plain-only (label+leaves, no gene boundaries) → the §44 multi-gene `chromosome(genes=)` form and `plasmid(chromosomes=)` have no C peer.

## 3. rc275 (progress/abort) dependency

rc275 wires an inline progress+cancel tick into `mint`/`genome()`, `mint_strand`, `genome_partition`, `genome_from_graph`, `recursive_cut`, `fiedler_sparse_file`. Its C-host reality splits exactly on C-reachability:

- **C-real:** `fiedler_sparse_file` (c_dispatched) + `mint`/`genome()` (`srmech_genome_mint`) — rc275 adds the `_progress` C overloads here. ✓ The rc275 note §1.4 confirms these are "the only heavy C loops in §101 scope."
- **Python-only by necessity:** `recursive_cut` (G1), `genome_partition` (G3), `genome_from_graph` (G2), `mint_strand` (G5) — rc275 hooks their **Python drivers**. A bare-C host cannot run these ops at all, so their progress/cancel cannot be C-host-real until G1–G3/G5 ship. rc275 does not *create* the gap, but its graph-pipeline progress/cancel is only as real as those C entry points.

## 4. Correction roadmap

- **Gate rc275 (or split rc275a):** ship the encode C entry points **G1 (recursive_cut) → G3 (partition_graph) → G5 (mint_strand) → G2 (from_graph)** first; then the rc275 `_progress` overloads are C-host-real across the whole pipeline. Building rc275's progress on top of Python-only orchestrators bakes a permanent C-host hole.
- **Own small parity rcs (independent of the graph pipeline):**
  - **G6 (amplify+copy_number)** — smallest, newest, cleanest; best first fix.
  - **G4 (integrate)** — self-contained.
  - **G7** — a cleanup rc (condense/decondense, active_telomere, genes, mint_plan, multi-gene chromosome).
- **Ratchet fix (systemic):** extend `test_rosetta_transitive_standalone.py` (or a new ratchet) so a `composition_of_c` compute op with non-trivial Python-only glue and no C entry point is FLAGGED, not silently accepted as a leaf. Otherwise this class recurs every rc.

## 5. Fermatas (conductor decisions)

1. Reclassify the native-dispatched genome ops (mint/genome/plasmid/partition/recall/centromere_of) from `composition_of_c` → `c_dispatched`? They dispatch to a whole-op C peer; the current label under-states their parity and muddies the gap signal.
2. Scope of the systemic ratchet fix — its own PR vs folded into the first correction rc.
3. Whether G7-minor reads (mint_plan/genes) count as "compute" owing a C mirror or as introspection exempt under everything-mirrors.
