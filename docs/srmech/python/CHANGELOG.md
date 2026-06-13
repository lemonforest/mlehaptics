# srmech changelog

All notable changes to this package will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this package uses semantic versioning.

## [Unreleased]

_Next development line: deferred-from-v0.4.6 introspection extensions (Tier 2 mmap ring buffer for >1k events/sec + C-side `srmech_progress_cb_t` callback ABI extension + `siona status` CLI via siona pyproject `[project.scripts]` enhancement)._

<!-- pypi-readme-changelog: the markers below slice ONLY the current-minor (0.7.0) entries into the PyPI long-description (fancy-pypi-readme hook in both pyprojects). MOVE BOTH MARKERS at each minor bump: -start- before the first 0.7.x entry, -end- immediately before the prior released minor (currently [0.6.0]). -->
<!-- pypi-readme-changelog-start -->
## [0.7.5rc132] - 2026-06-13

**Carrier-spirit lockdown — the tool schema stops advertising `np.ndarray` in the PARAMETER vocabulary too (the OTHER half of every tool signature; numpy was DELETED in #564).** rc131 killed `np.ndarray` from all RETURN types and added the immolation gate; the parameter type strings still advertised `np.ndarray` ~150 times. Anywhere the API/introspection says `np.ndarray` is an INVITATION to an LLM to drop srmech and reach for numpy ("it's just a numpy array, do the math in numpy"). The carrier is the lock: advertise the srmech CARRIER (the numpy *spirit* without numpy), keep it AGNOSTIC about input (it accepts AND degrades to every form the no-math plan used — list / `array.array` / tuple / scalar / nested-list), and NEVER name numpy where a caller / LLM / introspection can see it.

- **Parameter type-string sweep (`srmech.amsc.tool_schema`):** all **152** `np.ndarray` occurrences in `P(...)` parameter type strings replaced with the carrier-spirit type by op semantics — by family: qm/laplacian matrix params (`H`/`A`/`B`/`L`/`O`/`eta`/`rho`/`laplacian`/`M`/`V`/`g_v`/`g_s`/`g_c`/`A_segments`) → `Mat`; 1-D vector / signal / state params (`psi`/`state`/`v`/`k`/`k_spatial`/`direction`/`a`/`b` dot-vectors/`A_components`) → `Vec`; HDC + genome hypervector params (klein4/polar byte vectors, octonion power-of-two vectors, `the_one`/`turn`/`telomere`/`store`) → `HV`; shape-polymorphic 2-D-or-1-D ops (`elementwise_*`, `dense_norm`, `dense_solve.B`, `lstsq.b`) → `Mat | Vec`; gauge `generators` / einsum `operands` → `tuple[Mat, ...]`; the rank-3 structure-constant tensor → `list[list[list[float]]]`; sequences → `Sequence[HV]` / `Sequence[Vec]`; `Optional[...]` per semantics. The HARD RULE now holds on BOTH sides: **no `P(` parameter type string NOR `returns=R(` type string in `tool_schema.py` contains the token `ndarray`.**
- **The carrier is AGNOSTIC about input (made real + tested):** every numpy-free op already validates a 1-D / 2-D operand by iterating it (`_as_rows` / `_as_loop` / `_as_klein4_buf` / `Vec.from_sequence`), so a `Mat`-typed param accepts a `Mat` OR list-of-lists OR tuple-of-rows; a `Vec`-typed param accepts a `Vec` OR flat list / tuple / `array.array`; an `HV`-typed param accepts an `HV` OR flat int list / `array.array` / tuple. `tests/test_immolation.py` gains a focused test asserting a representative carrier-returning op gives the SAME result whether fed the carrier or its degenerate list / tuple / array form (`dense_solve` / `dense_matvec_real` / `klein4_bind` / `loop_bind`), plus a wire-path test that each carrier coercer produces an op-accepted structure — numpy-absent.
- **The MCP coercion lexicon + synth harness + JSON-schema lexicon extended:** `srmech.mcp._coercion` gains `Vec` / `HV` / `Optional[Vec]` / `Optional[HV]` / `Mat | Vec` / `Sequence[Vec]` / `Sequence[HV]` / `tuple[Mat, ...]` / `list[list[list[float]]]` coercers — each producing the natural Python structure (flat list for `Vec`/`HV`, nested list for `Mat`) the agnostic op consumes (NO numpy ever built); the legacy `np.ndarray` keys are KEPT for the wire-form / round-trip tests. `test_mcp.py`'s `_synth_value_for_type` + `srmech.mcp._tools` `_TYPE_LEXICON` / `_ENCODING_HINT` gain matching entries so the §10.1 every-tool harness synth-invokes every op cleanly and the advertised JSON schema never degrades a carrier param to a string.
- **The immolation param-guard (`tests/test_immolation.py`):** a new permanent assertion that NO advertised PARAMETER type (across all ToolEntries) contains `ndarray`, mirroring the rc131 no-`ndarray`-in-returns guard — the lock is now on BOTH sides of every tool signature, and the numpy-hard-blocked slice asserts both halves numpy-absent.
- **Source prose scrub** — stale `numpy.ndarray` / `ndarray` mentions in the carrier accept-list docstrings (`hv.py` `HV.from_sequence`, `hdc.py` `_as_klein4_buf` / `_as_polar` / `_store_buf`) reworded to the carrier-spirit ("the carrier is agnostic about the source shape"); the historical "(was an ndarray)" flip-notes are kept (they document numpy's removal, not an invitation).
- **Schema-vocabulary-only** — no public op added or removed (`describe()["tools"]["total"]` stays **298**); ABI 3 (no C wire-format change); the native build still holds no libm. numpy-free (no `import numpy`, no `np.`, verified with numpy hard-blocked); no `abs()` in cascade source; docstrings use `·` not a literal `@` token (the numpy-math ratchet is unchanged). All 5 SSOT version locations bumped.

## [0.7.5rc131] - 2026-06-13

**Introspection HONESTY + the immolation gate — the tool schema stops advertising `np.ndarray` returns for 88 ops it can no longer produce (numpy was DELETED in #564), and 8 straggler ops flip from bare lists to the `Mat`/`Vec` carriers.** srmech's `describe()` / tool schema IS its Class-H self-recognition surface; advertising a `returns` type the package cannot make is a false self-description. Every advertised RETURN type is now the TRUE post-#564 carrier, determined by CALLING each op, and a named release gate (`test_immolation.py`) makes it permanent.

- **Return-type honesty sweep (`srmech.amsc.tool_schema`):** all **88** `returns=R("…ndarray…")` type strings corrected to the true carrier — by family: the qm matrix builders (`spin`/`relativistic`/`gauge`/`sm`/`potentials`/`propagators`/`pseudo_hermitian`/`bell`/`single_particle`/`triality`/`so8`) → `Mat` or `tuple[Mat, …]`; the klein4 HDC + `genome.{quad_turn,telomere}` ops → `HV`; the polar HDC ops → `array`; the loop-bind / octonion-vector / `triality_apply` ops → `list[float]`; the structure-constants / `octonion_mult_table` → genuine rank-3 `list[…]`; `spectral.recompose` / `single_particle.tdse_evolve` → `list[complex]`. **The prose (2nd `R()` arg) is preserved verbatim;** parameter `np.ndarray` type strings are deliberately UNTOUCHED (a separate, synth-coupled concern). The HARD RULE now holds: **no `returns=R(` type string in `tool_schema.py` contains the token `ndarray`.**
- **8 straggler carrier-flips (the carrier-format law `[[feedback_numpy_removal_must_preserve_carrier_format_mat_vec_not_lists]]`):** `laplacian.{dense_solve,schur_complement,dirichlet_to_neumann}` float path → `Mat` (2-D) / `Vec` (vector RHS), the exact path keeps `list[list[Fraction]]`; `cascade.matrix_cascades.{qr→tuple[Mat,Mat], svd→tuple[Mat,Vec,Mat] (singular values 1-D → Vec), lstsq→Vec|Mat, eigvals→Vec, einsum→Mat|Vec|scalar}` — all routed through the existing numpy-free `mat_*` engine (no math reimplemented). A bare list has no honest C representation; a `Mat`/`Vec` IS a contiguous double buffer.
- **The immolation gate — `tests/test_immolation.py` (the established sister-package release-gate name; ephemerides-spectral + antikythera-spectral each ship one):** for EVERY `mcp_callable` ToolEntry it synth-invokes and, when the op returns cleanly, asserts `type(raw)` AGREES with the advertised `returns.type` (carrier-aware union/tuple matcher in `conftest`) — the inspection the §10.1 every-tool smoke held `raw` for but never did; it asserts NO advertised return type names `ndarray` (a permanent down-only guard); and it folds in the rc130 carrier idiom-surface contract (calling real carrier-returning ops + asserting `.shape`/`m[i,j]`/`m[0]`→`Vec`/`.T`/`.conj`/`@`/…), then re-runs a representative slice with numpy hard-blocked at import. `test_carrier_contract_rc130.py` is retired into it (no coverage lost). **`test_mcp.py`'s §10.1** gains the same return-type-agreement assertion (298/298 binding+coercion+return-type clean).
- **Introspection-honesty-only** — no public op added or removed (`describe()["tools"]["total"]` stays **298**); ABI 3 (no C wire-format change); the native build still holds no libm. numpy-free (no `import numpy`, no `np.`, verified with numpy hard-blocked); no `abs()` in cascade source; the numpy-math ledger lowers `linalg_fft` 3 → 2 (the rewritten `schur_complement` docstring dropped a stale `numpy.linalg.solve` mention). All 5 SSOT version locations bumped.

## [0.7.5rc130] - 2026-06-13

**The `Mat` / `Vec` carriers gain the last two numpy idioms — single-index row `m[0]` (→ `Vec`) and the `@` matmul operator — and a carrier-contract smoke that would have CAUGHT both gaps (#564 follow-up).** rc129 restored the carrier FORMAT but left two numpy idioms unimplemented: `m[0]` raised `"Mat index must be (i, j)"` (forcing `m.row(0)`) and `@` was unsupported (forcing `laplacian.dense_matmul_*`). These were the holes a downstream numpy-idiom compat sweep surfaced. rc130 closes them and — answering "how did the smoke miss this?" — adds the behavioural net the registry-walk smoke structurally could not be.

- **`Mat.__getitem__` is now rank-polymorphic:** `m[i, j]` → a plain `float`/`complex` scalar (unchanged); **`m[i]` (a single int) → row `i` as a `Vec`** (the numpy single-index idiom — format-preserving, NOT a bare list; negative indices supported). The explicit stdlib-list accessor `m.row(i)` is unchanged.
- **`@` matmul on both carriers, routed onto the Class-L cascade (never numpy):** `Mat.__matmul__`/`__rmatmul__` — `Mat·Mat` → `Mat` (`dense_matmul_*`), `Mat·Vec` (or a flat 1-D sequence) → `Vec` (`dense_matvec_*`); `Vec.__matmul__`/`__rmatmul__` — `Vec·Vec` (or a flat sequence) → a scalar inner product (`dense_dot_*`), `Vec·Mat` (row-vector · matrix) → `Vec`. Format-preserving: real ⊗ real → real carrier, complex anywhere → complex carrier. Two shared numpy-free detectors (`_is_matrix_like` / `_carrier_is_complex`) pick matmul-vs-matvec and the real-vs-complex Class-L peer.
- **Smoke completeness — the answer to "the smoke missed these":** the registry-walk smoke (`test_registry_smoke_rc127`) only checks that each registered tool NAME *resolves* to a callable and each catalog class *describes* — a name-resolution + introspection net that never *calls* an op nor touches a returned carrier, so a carrier-method gap is invisible to it. New **`tests/test_carrier_contract_rc130.py`** is the behavioural net: it CALLS representative carrier-returning ops (`dense_laplacian` / `dense_adjacency` / `jacobi_eigvals` / `fiedler_vector` / `dense_matmul_real` / `dense_matvec_real` / `dense_outer_real`) and asserts their `Mat`/`Vec` returns expose the full documented numpy-idiom surface (`.shape`, `len`, iteration, `m[i, j]`, `m[0]`, `.T`/`.transpose()`, `.conj()`, `.tolist()`, `.tobytes()`, value-`==`, `@`) — and re-runs it numpy hard-blocked at import. A future op that returns a bare list (the rc127 regression) or a carrier that drops an idiom now fails loudly here.
- **Carrier-idiom-only** — no new public op (`describe()["tools"]["total"]` stays **298**); ABI 3 (no C wire-format change); the native build still holds no libm. numpy-free (no `import numpy`, no `np.`, verified with numpy hard-blocked); no `abs()` in cascade source; the numpy-math ledger is unchanged (the new docstrings use `·`, not a literal `@` token). All 5 SSOT version locations bumped.

## [0.7.5rc129] - 2026-06-12

**Carrier FORMAT restored — the Class-L `dense_*` / eigendecompose / graph-build / elementwise ops return `Mat` (matrices) / the new `Vec` (vectors), NOT bare Python lists (#564 correction).** rc127's numpy-removal regressed ~17 ops in `srmech.amsc.{laplacian,coupling,harmonics}` from the numpy-carrier to bare Python lists/tuples — losing `.shape`, the 2-D/1-D structure, and any honest C representation (a list **is not** something in C; a contiguous `double` / interleaved `double _Complex` buffer **is**). rc129 restores the numpy-carrier FORMAT numpy-free: the math stays the exact cascades, only the **return carrier** is fixed. **This supersedes the rc127 "now return plain Python lists" BREAKING note** — the carriers re-expose `.shape` + a native C interleaved-buffer wire form, so the downstream `.shape` / 2-D-structure / 1-D-vector consumers (e.g. ephemerides-spectral) are fixed.

- **New `Vec` carrier (`srmech/amsc/vec.py`)** — the numpy-free 1-D peer of `Mat`: a flat `array('d')` (real → `n` doubles; complex → `2n` interleaved `(re, im)` doubles, C99 `double _Complex` order), `is_complex` flag. Surface mirrors `Mat`: `.shape -> (n,)` (1-tuple, like a 1-D ndarray), `__len__`, `__getitem__(i) -> float|complex` (plain scalar), `__iter__` yields **SCALARS** (not rows), `__eq__` → scalar bool (vs `Vec`/sequence; never imports numpy), `.conj()` (Class-K imag sign-flip), `from_sequence` / `from_flat` classmethods, `tolist` / `tobytes` / `.buffer`, `__repr__`. The C wire helper is `laplacian._vec_to_interleaved_cbuf` (+ `_vec_from_interleaved_cbuf`) — the 1-D twin of the `Mat` marshallers, so a `Vec` is `ctypes`-castable to the native dense buffer exactly like a `Mat` (zero-copy for complex, `(re, 0)`-filled once for real).
- **Flipped → `Mat`** (2-D matrix returns): `dense_adjacency` / `dense_laplacian` / `normalized_laplacian` / `signed_laplacian` / `magnetic_laplacian`, `dense_matmul_complex` / `dense_matmul_real`, `dense_outer_complex` / `dense_outer_real`, the **eigenVECTORS** of `hermitian_eigendecompose` / `symmetric_eigendecompose`, and the per-band eigenvector groups of `three_fold_eigvec_groups` (the returned dict's `low`/`mid`/`high` are real `Mat`s).
- **Flipped → `Vec`** (1-D vector returns): `fiedler_vector`, `dense_matvec_complex` / `dense_matvec_real`, `jacobi_eigvals` (eigenvalues), the **eigenVALUES** of `hermitian_eigendecompose` / `symmetric_eigendecompose`, `spectral_block_dispatch` (per-block + combined spectra), and `coupling.signed_sum_squared` (the small non-negative integer scores are exact as float64 doubles — well within the 2⁵³ exact-integer range; noted in the docstring).
- **Shape-polymorphic** (preserve input rank): `elementwise_multiply_complex` / `elementwise_transcendental` / `elementwise_hypot` / `elementwise_sqrt` — a `Mat`/2-D input → `Mat` out, a `Vec`/1-D-sequence input → `Vec` out (rank read off the input). **Unchanged scalars:** `dense_dot_real -> float` / `dense_dot_complex -> complex` (already scalars, not carriers).
- **Internal chaining + MCP boundary:** `jacobi_eigvals(dense_laplacian(...))` and the `symmetric_eigendecompose`→`three_fold`/`fiedler` chains accept the carrier natively (`m[i, j]` / `v[i]`); the MCP `serialise_native` gains a `Vec` branch (flat JSON list; complex → `[re, im]` leaves) next to the existing `Mat` branch. `harmonics.classify_chirality_harmonic` accepts `Vec`/`Mat`/`Sequence` (read element-by-element).
- **Carrier-FORMAT-only** — no new public op (`describe()["tools"]["total"]` stays **298**); ABI 3 (no C wire-format change; the `Vec` marshaller is Python ctypes only); the native build still holds no libm. numpy-free verified with numpy hard-blocked at `sys.meta_path` (carrier ops import + run numpy-absent); no `abs()` in cascade source (the Class-K sign-branch is in `Mat`/`Vec.conj` + the signed-degree magnitude). New `tests/test_vec_carrier_rc129.py`; ~16 carrier-consuming test files updated to assert via the `Mat`/`Vec` API (`m[i, j]` / `v[i]` / `.tolist()` / `.shape`). All 5 SSOT version locations bumped.

## [0.7.5rc128] - 2026-06-12

**§41 genome persistence — the `Genome` catalog class learns to save/load itself to disk, attested and numpy-free (PR #687 UPSTREAM §41; #564 C/Python-1:1 arc).** A genome strand (telomere-capped, Klein-4 quad-turn-coupled leaves) now round-trips to an on-disk directory as a **provenance-attested** artefact — the FIRST half of the §41 1:1 pair (the C `srmech_json` + `srmech_genome` mirror follows in this branch).

- **Five new public ops** in `srmech.amsc.genome` (`describe()["tools"]["total"]` **293 → 298**): `genome_save(strand, path, *, the_one, labels)` / `genome_load(path, *, labels=None)` / `genome_catalog(path)` / `genome_append(path, label, leaves, *, the_one)` / `genome_window(path, label)`, plus a new `GenomeBoundingError`.
- **On-disk format** — `path/` is a directory: `manifest.json` is an **`MPRRecord`** (`attestation.response_sha256 == body_sha256`, `parser_version` = the srmech version) whose `data` carries `{format_version, leaf_dim, n_turns, the_one:{sha256,hex}, body_sha256, chromosomes:[{label, cap_sha256, leaf_count, byte_offset, byte_len}]}`; `turns.bin` is an **append-only** flat concatenation of fixed-width `leaf_dim`-byte Klein-4 (0..3) leaf blocks (turn *k* = bytes `[k·leaf_dim : (k+1)·leaf_dim]`, no length prefixes).
- **Disk-paging + bounding-as-integrity:** `genome_load(path)` streams block-by-block; `genome_window` / labelled `genome_load` seek to `byte_offset` and read only `byte_len` (RAM bounded by the largest single chromosome). Every read re-hashes via `format.sha256_bytes` against `body_sha256` (whole-genome) or the region cap vs `cap_sha256` (windowed) → `GenomeBoundingError` on mismatch. `genome_catalog` reads the manifest ONLY (never opens `turns.bin`). `genome_append` is append-only — every prior chromosome's `cap_sha256` / `byte_offset` / `leaf_count` stays byte-identical; only `n_turns` / `body_sha256` / the new entry change.
- **Catalog-class surface:** the shipped `Genome` `[class]` descriptor gains `save` / `load` / `catalog` / `append` methods (mirroring the existing `assemble` / `partition` bindings).
- **numpy-free** (no `import numpy`, no `np.`, verified passing with numpy hard-blocked at import); hashing routed through `format.sha256_bytes`; no `abs()` in cascade source. Registry checklist satisfied (5 `ToolEntry` registrations + 5 `rosetta_classification.ndjson` `non_compute` lines + the `describe` count-test bump). ABI 3; the native build still holds no libm.
- **C mirror — `srmech_json` (malloc-free JSON parser + canonical writer; `c/src/srmech_json.c`):** the keystone the genome-persistence C mirror needs. The parser builds a value tree (`srmech_json_value_t`) from a caller-supplied arena/workspace (the same `void *ws, size_t ws_len` bump allocator the TOML parser uses); the writer emits bytes **BYTE-IDENTICAL** to CPython `json.dumps(obj, sort_keys=True, ensure_ascii=False)` for any tree of null / bool / int / string / object / array — exactly what an MPR manifest / genome catalog is. Object keys sorted by UTF-8 byte order (= code-point order = Python `sorted()`); `": "` / `", "` separators; strings escape only `" \ \b \t \n \f \r` + other controls `< 0x20` as `\u00XX` (lowercase), with `ensure_ascii=False` so all bytes ≥ 0x20 (incl. multibyte UTF-8) emit verbatim. New symbols: `srmech_json_parse` / `srmech_json_write` (NULL buf ⇒ size query; too-small buf ⇒ `SRMECH_ERR_OVERFLOW`, never overflows) / `srmech_json_object_get` + a builder (`srmech_json_builder_init` / `srmech_json_new_{null,bool,int,double,string,array,object}`). **Float caveat:** `SRMECH_JSON_DOUBLE` values are written best-effort (`%.17g`); byte-parity with Python's `repr(float)` is NOT guaranteed — the parity GUARANTEE covers null/bool/int/string/object/array trees only (manifests are float-free). JPL-clean (no recursion — explicit depth-bounded stack capped at `SRMECH_JSON_MAX_DEPTH`; no malloc — caller arena; ≤60-line functions; ≥2 asserts/non-exempt-fn; `json_is_ws` / `json_is_digit` are the 2 Rule-5-exempt char classifiers). ABI stays 3 (additive symbols + a struct + macros).
- **C mirror — `srmech_genome` (the §41 persistence mirror; `c/src/srmech_genome.c`) — completes the §41 1:1 pair.** `srmech_genome_save` writes `<dir>/turns.bin` (= the body verbatim) + `<dir>/manifest.json` built via the `srmech_json` builder and serialized **BYTE-IDENTICAL** to Python `genome_save`'s manifest; all hashing routes through `srmech_sha256_hex` (the `§` in `cite_as` emitted as raw UTF-8 `0xC2 0xA7`; `parser_version` = `"srmech " SRMECH_VERSION`; `parser_rule_hash` / `collector_descriptor_hash` the sha256 of the same ASCII inputs as Python). `srmech_genome_catalog` parses the manifest only (never opens `turns.bin`); `srmech_genome_load` / `srmech_genome_window` re-hash the bytes read against `body_sha256` / `cap_sha256` and return a bounding error on mismatch; `srmech_genome_append` grows `turns.bin` + rewrites the manifest leaving prior chromosome entries byte-identical. New symbols: `srmech_genome_save` / `_catalog` / `_load` / `_window` / `_append` + `srmech_genome_chrom_t`. JPL-clean (file I/O via stdio, json tree in the caller arena; no malloc/libm/goto/recursion; ≤60-line fns; ≥2 asserts; no new Rule-5 exemptions). ABI stays 3. **Verified standalone in WSL2 (no Python):** pedantic `-Werror` build clean; C smoke 18/18; the C↔Python byte-parity harness shows `manifest.json` (1747 bytes) AND `turns.bin` (576 bytes) reproduced **byte-for-byte** over the real synthetic genome, plus the catalog/load/bounding round-trip.

## [0.7.5rc127] - 2026-06-12

**numpy is GONE — the whole package AND the whole test suite run with numpy NOT installed (`CEIL_NUMPY_CARRIER` 1 → 0, the capstone of #564).** This is the big-bang completion of the carrier-removal arc: not numpy-optional, not behind a `[scientific]` extra, not a lazy proxy, not a `.to_numpy()` export — numpy is removed, period. `pip install srmech` pulls no numpy; a fresh numpy-absent venv imports + runs the entire API and the entire pytest suite green.

- **The last top-level carrier flips numpy-free:** `mcp/_coercion.py` (MCP arg coercion) routes to `Mat` / plain lists — `_to_ndarray` → nested list, `_complex_pairs_to_ndarray` → recursive `[re, im]` → `complex` list, `serialise_native` gains a `Mat` branch and drops the ndarray/`np.generic` branches. `CEIL_NUMPY_CARRIER` reaches **0** — the carrier ratchet is now the permanent "ZERO `import numpy` anywhere in `srmech/`" guard.
- **The `[scientific]` hint machinery is DELETED:** `srmech/_scientific.py` (`require_numpy`/`_LazyNumpy`/`lazy_numpy`/`make_lazy_op_getattr`) is gone; its importers (`qm/__init__`, `signal_processing/closed_form_ops/__init__`, `signal_processing/path_b_ops/__init__`) de-wire to plain eager re-exports / `__getattr__`.
- **The export boundary is DELETED:** `One.to_numpy()` / `One.to_matrix()` (→ `Mat`), `HV.to_numpy()`, `Mat.to_numpy()` — the lossy numpy-export convenience methods are removed (they were the last "numpy-optional" survivors; #564 retires the "lossy export convenience, kept" stance entirely).
- **Remaining numpy MATH flips onto the `mat_*` engine + plain lists** (`laplacian.py` dense_*/eigendecompose/graph-build/graph-spectral, `matrix_cascades` qr/svd/lstsq/einsum/eigvals, `coupling`, `harmonics`, `atoms`, `_fft_carrier`). **BREAKING API change:** the `dense_*` / `*_eigendecompose` / graph-build / graph-spectral ops now return plain Python **lists** (matrices = list-of-lists, vectors / eigenvalues = flat list, scalars = `float`/`complex`) instead of `np.ndarray`; `schur_complement` float → `list[list[float]]`, exact → `list[list[Fraction]]`. Downstream consumers that relied on ndarray returns (e.g. ephemerides-spectral) need a numpy-free-consumption follow-up.
- **Packaging + CI:** both pyprojects drop the `scientific = ["numpy"]` extra and numpy from `tests`/`dev`; the description is "numpy-FREE"; the srmech-ci pure-wheel guard is the **numpy-ZERO capstone** (a hard `find_spec('numpy') is None` assert) and the stale `One.to_numpy()` must-raise is gone.
- **Tests:** ~72 numpy-oracle / ndarray-dispatch test files rewritten numpy-free (oracles → stdlib `cmath`/`fractions`/`struct`/`math`/`random.Random`, the srmech exact path, or reconstruction/residual invariants); the obsolete `[scientific]`-machinery / must-raise-hint test functions are deleted; `test_numpy_math_ratchet` ceilings recomputed. This rc closes the last two in-function `import numpy` test gaps (`test_introspect` describe_shape → `Mat`; `test_cascade_sedenion_register` un-skips its now-numpy-free storage + working-word tests). A new **registry-walk smoke** (`test_registry_smoke_rc127.py` + the pure-wheel CI step) walks the FULL tool registry (all 293 `tool_schema` entries resolve to a real attribute) and the FULL class registry (every shipped catalog class — `Genome`, `Hurwitz` — describes), numpy-absent — so a newly-registered tool whose module fails to import, or a shipped class that fails to describe, fails immediately instead of via a hand-picked subset. **Full suite verified numpy-genuinely-absent: 3506 passed, 2 skipped** — the only failures are the 3 stale-local-DLL version-agreement tests (they pass on CI's fresh build).
- **No new public op** (`describe()["tools"]["total"]` stays **293**); ABI 3; the native build still holds no libm. All 5 SSOT version locations bumped.

## [0.7.5rc126] - 2026-06-12

**`signal_processing/closed_form_ops/ica_jade.py` (JADE blind-source-separation / independent-component analysis) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 2 → 1) — the LAST `srmech.signal_processing` carrier, so the whole `srmech.signal_processing` subpackage is now numpy-free.** Carrier-removal #564. Per the no-bridge discipline (`grep -E "\bnp\.|import numpy|_lazy_numpy"` = 0): drops `import numpy as np` and the `dense_matmul_real` / `hermitian_eigendecompose` / `elementwise_sqrt` numpy-carrier imports.

- **Whitening eig onto the Mat carrier:** the covariance eigendecomposition routes through `mat_hermitian_eigendecompose` (the prior `hermitian_eigendecompose` / `dense_matmul_real` are numpy *carriers* that raise numpy-absent — the rc70 runnable≠loadable trap). The covariance build, PCA whitening, whitened-source projection, and the final unmixing are explicit numpy-free loops over plain `float` lists; the inverse-`√λ` whitening scales use the Class-N `rational.sqrt`.
- **Cumulants + Givens:** the fourth-order cumulant tensor is **nested Python lists** (`Mat` is 2-D only); the Givens-rotation joint diagonalisation is an explicit numpy-free sweep — the rotation angle is the Class-N `rational.atan2` and `c,s = rational.cos/sin`, the off-diagonal magnitudes are Class-K sign-branches (**no `abs()`**), and the two cumulant-axis rotations (originally `np.einsum("ai,ijlm->ajlm", G.T, …)`) become explicit first-axis contractions — preserving the original behaviour byte-for-byte incl. the inert `if False` alternate-subscript branch (carrier-swap, not a bugfix). `op` returns the sources `S` and unmixing matrix `W` as `Mat` (was an array return).
- **CI-GUARD STRUCTURAL SHIFT**: `ica_jade` was the pure-wheel must-raise `[scientific]` exemplar; now numpy-free, the exemplar MOVED to the **durable export boundary `One.to_numpy()`** — a lossy ndarray export that intrinsically needs numpy and is NOT a carrier to be flipped, so it stays the long-lived numpy-requiring exemplar past the carrier-removal capstone. The `test_signal_processing_numpy_free_reachable_rc71` clean-hint test repointed to the same surface; `ica_jade` added to the flipped-and-exercised list. `test_ica_jade_smoke` rewritten numpy-FREE (`random.Random` sources, list mixing); new `_BLOCK_NUMPY` reachability proof (incl. a full-`srmech.signal_processing`-imports-numpy-free assertion).
- **Carrier-only** — no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. The matmul math-ledger drops **4 → 2** (the 2 cumulant-rotation `np.einsum` calls gone; the `a·b` matmul docstring de-`@`-ed); `linalg_fft`/`ufunc` unchanged. All 5 SSOT version locations bumped. **Remaining 1 carrier: `mcp/_coercion` — the rc127 CAPSTONE (`CEIL_NUMPY_CARRIER` 1 → 0 + delete the must-raise clause + numpy-absent fresh-import asserts).**

## [0.7.5rc125] - 2026-06-12

**`srmech.spectral` (Spike #115 runtime spectral encode/decode surface) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 3 → 2).** Carrier-removal #564. A LEAF for its public ops — the only srmech-side importer is `mcp/_coercion.py`, which imports the `SpectralHandle` *type* (not any function); nothing in srmech calls `decompose`/`recompose`/`predict`/`truncate_sparse`. Per the no-bridge discipline (`grep -E "\bnp\.|import numpy|_lazy_numpy"` = 0): drops `import numpy as np` and the `dense_matvec_complex` / `hermitian_eigendecompose` / `elementwise_hypot` / `elementwise_transcendental` numpy-carrier imports.

- **Math onto the Mat carrier:** the Hermitian eigendecomposition routes through `mat_hermitian_eigendecompose` (the prior `hermitian_eigendecompose`/`dense_matvec_complex` are numpy *carriers* that raise numpy-absent — the rc70 runnable≠loadable trap); the projection `Vᴴ·state` (decompose) and reconstruction `V·coeffs` (recompose) are explicit numpy-free matvecs over the eigenvector `Mat`. The eigenbasis LRU cache now stores `(eigvals_list, V_Mat)`.
- **Bytes / sort / phase / magnitude:** the complex128 coefficient bytes (`np.frombuffer` / `.tobytes`) become `struct` pack/unpack of interleaved native-endian `(re, im)` float64 pairs — **byte-identical** to the prior layout, so the substrate-descriptor and content-SHA hashes are stable (verified). `np.argsort(-mag, stable)` → `sorted(range(n), key=…, reverse=True)` (stable, same tie order); the per-mode `predict` phase `e^{-iλt}` → the Class-N Euler cascade `rational.cexp`; the `truncate_sparse` magnitudes → squared-modulus `re²+im²` (monotone, no `abs()`/sqrt — used for both the top-k rank and the threshold gate via `thr²`).
- **`recompose` now returns `List[complex]`** (was `np.ndarray`); the MCP dispatch path serialises via the JSON wire (`.tolist()`-style), so the return-type change is transparent to callers. `test_spectral.py` + `test_spectral_rcn_plus_2.py` rewritten **numpy-FREE** (`struct` unpack, `max(abs(…))`, `random.Random` fixtures, list-of-lists Laplacians); new `_BLOCK_NUMPY` reachability proof.
- **CI-GUARD**: `ica_jade` **stays** the pure-wheel must-raise `[scientific]` example (spectral ≠ ica_jade) — no guard move. **Carrier-only** — no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change; math-ledger unchanged (spectral's numpy was bytes/sort coercions, not linalg/fft/matmul/ufunc). All 5 SSOT version locations bumped. Remaining **2** carriers: `mcp/_coercion` (the capstone) / `signal_processing/.../ica_jade`.

## [0.7.5rc124] - 2026-06-12

**`qm/pseudo_hermitian.py` (η-pseudo-Hermitian / PT-symmetric framework) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 4 → 3) — the LAST `srmech.qm` carrier, so the whole `srmech.qm` subpackage is now numpy-free.** Carrier-removal #564, a LEAF qm module (its only consumers are `tool_schema` metadata + the `qm/__init__` re-export). Per the no-bridge discipline (`grep -E "\bnp\.|import numpy|_lazy_numpy"` = 0): drops `import numpy as np`, the `dense_*` numpy-carrier imports (`_dense_solve_complex`/`dense_dot_complex`/`dense_matmul_complex`/`dense_matvec_complex`/`dense_norm`), and `matrix_cascades as _mc`.

- Matrices ride the framework-native `Mat`; state vectors are plain `complex` lists (`Mat` is 2-D only). `inner_product_eta` / `expectation_eta` are explicit Class-L matvec + sesquilinear-dot cascades; `is_pseudo_hermitian` is `‖O†η − ηO‖` via `mat_matmul` + `mat_norm`. The spectrum comes from the Mat-carrier `mat_eigvals` (the lone `np.linalg.eig` is gone — `linalg_fft` math-ledger 9 → 8).
- The η = (V·V†)⁻¹ construction needs the general **non-Hermitian eigenvectors** of a real-spectrum O: each is the null vector of `O − λI` computed by **deterministic Gaussian elimination** (squared-modulus pivots — a Class-K magnitude, **no `abs()`**), avoiding any ill-conditioned shifted-inverse solve. η is the inverse of the HPD Gram V·V† via the well-conditioned `mat_solve` (no rank-deficiency → no native-vs-pure-Python singular-solve divergence). The identity O†η = ηO holds for any column scaling of V, so the eigenvectors need no normalisation.
- `test_qm_pseudo_hermitian.py` rewritten numpy-FREE (fixed small `Mat` fixtures; the Hermitian-eigenstate oracle is `mat_hermitian_eigendecompose`, not numpy); new `_BLOCK_NUMPY` reachability proof (incl. a full-`srmech.qm`-imports-numpy-free assertion). The rc60/rc63/rc66 routing tests updated: rc63 `_ROUTED` now empty (pseudo_hermitian graduated, like so8/esprit); rc66 asserts the `mat_solve` route (was `_dense_solve_complex`).
- **CI-GUARD**: the pure-wheel must-raise `[scientific]` example MOVED `pseudo_hermitian` → `ica_jade` (`from srmech.signal_processing.closed_form_ops import ica_jade`, a still-numpy carrier whose import re-raises the clean hint via the `closed_form_ops` lazy package gate); `pseudo_hermitian` added to the flipped-and-exercised list. **Carrier-only** — no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. All 5 SSOT version locations bumped. Remaining **3** carriers: `mcp/_coercion` / `signal_processing/.../ica_jade` / `spectral/__init__`.

## [0.7.5rc123] - 2026-06-12

**`qm/propagators.py` (Feynman scalar / fermion / photon / massive-vector propagators) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 5 → 4).** Carrier-removal #564 — a LEAF qm module (its only consumers are `tool_schema` metadata + the `qm/__init__` re-export, so no connected-component cascade). Per the no-bridge discipline (`grep -E "\bnp\.|import numpy|_lazy_numpy"` = 0): drops `import numpy as np` and the `dense_matvec_real`/`dense_outer_real` numpy-carrier imports; the four propagators are built over the framework-native `Mat` + Python `complex`.

- The fermion-propagator numerator `i(p̸+m)` consumes `relativistic.dirac_operator_momentum_space(...)` (a `Mat`, numpy-free since rc118) DIRECTLY — the **three rc118 `.to_numpy()` bridges** propagators carried (the fermion numerator + the two `minkowski_metric()` coercions for the photon / massive-vector) are **DELETED** (consume the `Mat` directly). The `kᵘkᵛ` tensor routes through a numpy-free `_outer(u,v)` (column·row `mat_matmul`); the `k²` contraction reuses relativistic's numpy-free `four_momentum_squared` fold. Returns: matrices → `Mat`, scalar propagators → `complex` (same physics, identical signatures). No `mat_solve` (pure matmul/outer), so no native-vs-pure-Python divergence risk.
- `test_qm_propagators.py` rewritten numpy-FREE (pole structure, Clifford `(p̸+m)(p̸−m)=p²−m²`, photon transversality via `Mat`-entry/`mat_matmul`/`complex`); new `_BLOCK_NUMPY` reachability proof; the `test_dense_outer_rc51` propagators cell updated. **CI-GUARD**: the pure-wheel must-raise `[scientific]` example MOVED `propagators` → `pseudo_hermitian` (still a numpy carrier); `propagators` added to the flipped-and-exercised list. **Carrier-only** — no math-ledger change; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. All 5 SSOT version locations bumped. Remaining **4** carriers: `qm/pseudo_hermitian` / `mcp/_coercion` / `signal_processing/.../ica_jade` / `spectral/__init__`.

## [0.7.5rc122] - 2026-06-12

**The octonion connected component goes numpy-FREE in one coordinated cluster flip (`CEIL_NUMPY_CARRIER` 8 -> 5).** Carrier-removal #564, done as a single honest unit per the discipline that **numpy-free means ZERO numpy** -- no `import numpy`, no `np.` callsite, no latent `_lazy_numpy` proxy, and **no `.to_numpy()`/`np.asarray` bridge** anywhere. The gate is literal: `grep -E "\bnp\.|import numpy|_lazy_numpy"` returns **zero** for every file touched. Because the no-bridge rule forbids "wrap the still-numpy consumer," octonion could not flip alone -- the whole dependency component (`hdc` octonion-loop path -> `qm/octonion` -> `qm/so8` + `qm/triality` + `amsc/cascade/hypercomplex_dft`) is removed together, decrementing three carriers at once.

- **`amsc/hdc.py`** -- the `np = _lazy_numpy(...)` proxy is **deleted**; the octonion loop family (`loop_bind/conj/inv/associator/cross7/g2_three_form/left_op/right_op` + the `*_hd` whole-array peers + the polar/klein4 HDC family) marshals to/from the **native C dispatch** with **no numpy** (ctypes `(c_double*n)` buffers + `list[float]`/`Mat` returns; the two matrix ops return a real `Mat`); numpy-free pure-Python fallbacks operate on lists. Native dispatch is **preserved** (no Rosetta-ledger regression); numpy-present results are bit-for-bit identical (`||tau^3 - I|| = 3.22e-15`, unchanged).
- **`qm/octonion.py`** -- the (8,8,8) structure-constant tensor is a nested `list[list[list[int]]]`; `octonion_mult_table()` returns it, `octonion_left_mult`/`octonion_right_mult` return a real 8x8 `Mat`, `octonion_conjugate` a `list[float]`, `octonion_norm` a `float` (Class-K `magnitude` -> `rational.sqrt`, no `abs()`). The Class-A self-attestation `response_sha256` is **byte-identical** to the old `np.int8.tobytes()` path (`7f36461e...ab5b`, unchanged).
- **`qm/so8.py`** -- full rewrite onto `Mat` + the `mat_*` family. The **dual** numpy use is resolved exactly: matrix-RANK on exact {-1,0,+1} data -> an **exact RREF over the rationals** (`fractions.Fraction`, mathematically identical and numpy-free); nullspace **geometry** -> the numpy-free `mat_svd` float carrier (smallest-singular-value vectors by known nullity, never a tolerance -- honouring the cascade-SVD small-singular-value accuracy floor). Fixes a genuine latent defect surfaced by the flip: the eigenspace Rayleigh quotient used a vdot-style bilinear `v.v` (~0 for a complex eigenvector of a real-skew matrix); now the explicit Hermitian `sum(conj(v_i)*v_i)`.
- **`qm/triality.py`** -- `Mat`/`mat_matmul`/`mat_norm`; the order-3 companion solve moved off the over-256-bound `mat_lstsq` (pure-Python 512-wide, ~309 s) onto **sparse normal equations** `(A^T A)x = A^T rhs` via native `mat_solve` (~1.2 s), value-identical.
- **`amsc/cascade/hypercomplex_dft.py`** -- drops the function-local numpy; consumes the `Mat` octonion operators via a numpy-free `_matvec8`.
- **`qm/hurwitz.py`** (consumer, already 0-numpy) -- nested-list indexing `table[a][b][axis]` for the now-list octonion table.

Every `.to_numpy()` bridge prior rcs had parked in so8/triality is **deleted** (rewritten to `.tolist()`). The 14 cluster + loop-family test files are rewritten numpy-FREE (so8's rank tests exercise the rank-deficient regime -- `rank_with_so4` stays 6); a `_BLOCK_NUMPY` subprocess test proves all five modules import+run numpy-genuinely-absent. Also a small **test-harness robustness fix**: `test_dsl.py::_run_cli` now decodes the CLI subprocess as UTF-8 (`encoding="utf-8"`) so it is locale-robust (a cp1252-default box previously raised `UnicodeDecodeError` on the unicode op descriptions). **CI-GUARD**: octonion/so8/triality/hdc/hypercomplex added to the pure-wheel flipped-and-exercised list; must-raise example stays `propagators`. **No new public op** (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. All 5 SSOT version locations bumped. Remaining **5** carriers: `qm/propagators` / `qm/pseudo_hermitian` / `mcp/_coercion` / `signal_processing/.../ica_jade` / `spectral/__init__`.

## [0.7.5rc121] - 2026-06-12

**`qm/potentials.py` (hydrogen radial + harmonic oscillator) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 9 → 8).** Carrier-removal #564 — the breach the rc120 native-eig-bound raise was opened for. (rc120 was a foundation rc that did not decrement the ratchet, so it stayed at 9; potentials is the 9→8 flip.) `hydrogen_radial`'s real-symmetric tridiagonal Hamiltonian (n_grid up to ~600) now eigensolves on the **fast native C Jacobi** via `mat_hermitian_eigendecompose` (rc120 lifted the native bound to n≤2048), with **no compromise** — no API-default change, no slow pure-Python fallback.

- **`srmech/qm/potentials.py`** drops `import numpy as np` (and `dense_matmul_complex`/`hermitian_eigendecompose`). `hydrogen_radial` builds the tridiagonal H as a `Mat` and returns `(r: list[float], energies: list[float], eigenvectors: real Mat)` — the eigenvalues are the ascending `(n,1)` real Mat as a list, the eigenvectors the value-preserving real part (H is real-symmetric). `harmonic_oscillator_ladder` returns the lowering/raising operators as complex `Mat` (√n via the Class-N `rational.sqrt`; `a† = a.conj().T`), and `harmonic_oscillator_hamiltonian` is `ω(a†a + ½I)` via `mat_matmul`. Verified numpy-genuinely-absent.
- `test_qm_potentials.py` rewritten numpy-FREE (commutator / spectrum via `mat_matmul` + `mat_hermitian_eigendecompose`, ladder action by direct `Mat`-entry, hydrogen via list indexing + real-`Mat` `mat_matmul`, the harmonic-oscillator↔TDSE cross-check passes the `Mat` H directly to `single_particle.tdse_evolve`). Test grids tuned to n_grid=250 (≈3 s/eig on the native path) landing inside the **unchanged** accuracy bands (ground −0.496 ∈ (−0.51,−0.48), 2s −0.125, 2p −0.125). The potentials cell in `test_qm_cascade_routing_rc33.py` is numpy-free too (numpy stays in that file only as the differential oracle for the still-unflipped generic `hermitian_eigendecompose`).

**CI-GUARD**: potentials added to the pure-wheel flipped-and-exercised list (must-raise example stays `propagators`). **Carrier-only** — no math-ledger change; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change (rides the rc120 native-bound foundation). All 5 SSOT version locations bumped. Remaining **8** carriers: so8 / octonion / triality / propagators / pseudo_hermitian + `mcp/_coercion` + `spectral/__init__` + `ica_jade`.

## [0.7.5rc120] - 2026-06-12

**Native Hermitian eigendecomposition now serves n up to 2048 (was 256) — foundation for large-grid numpy-free eig (#564).** The native C `srmech_hermitian_eigendecompose` path was capped at `n ≤ 256`; above that, `mat_hermitian_eigendecompose` fell to the pure-Python cyclic Jacobi, which is impractically slow for the matrix sizes real QM operators need (e.g. `qm.potentials.hydrogen_radial` defaults to n_grid=400 and tests use 600). This rc lifts that cap **with no compromise**: it routes through the reentrant `srmech_hermitian_eigendecompose_ws` C entry (shipped since #772), which takes a **caller-supplied** workspace — Python allocates it via `ctypes` (heap, **not** a C `malloc` → JPL Rule 3 clean; **not** the stack → no overflow), so `n` is bounded only by a sanity constant, not by storage.

- **C**: added `SRMECH_HERMITIAN_WS_MAX_NODES = 2048` (srmech.h) and pointed the five hermitian-eig-path bound checks in `srmech_laplacian.c` (`off_diag_sq` / `init_identity` / `run_sweeps` / `_ws` assert + hard cap) at it. `SRMECH_LAPLACIAN_MAX_NODES` stays **256** — the graph-laplacian-build stack arrays (`degree[256]` / `d_inv_sqrt[256]`) and the non-`_ws` convenience wrapper's 1 MB static buffer are untouched (the non-`_ws` wrapper stays self-limited to 256 via its `ws_len < 2·n·n` check). The whole hermitian-eig path works **in-place** on the caller's workspace + eigenvector output — there are no O(n²) stack arrays. **ABI stays 3** (additive symbol + internal bound relax; no wire-format change). Pedantic `/W4 /WX` build clean; JPL ratchet unchanged.
- **Python**: `_native.py` binds the (guarded) `srmech_hermitian_eigendecompose_ws` symbol; `mat_hermitian_eigendecompose` prefers it with a `(2·n·n)`-double `ctypes` workspace when `n ≤ MAX_NATIVE_HERMITIAN_NODES` (new constant = 2048), falling back to the non-`_ws` entry for `n ≤ MAX_NATIVE_NODES` (256, unchanged) on older libs, then to the pure-Python Jacobi on a convergence miss. `MAX_NATIVE_NODES` (256) still gates the genuinely-256-bounded paths (`dense_solve` static buffer, `dense_matvec`/`matmul`, `jacobi_eigvals`).

Verified: 400×400 native Hermitian eig in **16.5 s** (vs ~29 min on the pure-Python fallback — 140× at n=128), eigenvalues correct to ~2e-12; n=200 + n=2 paths unchanged. **Foundation rc** — no carrier flip (`CEIL_NUMPY_CARRIER` stays **9**), no new public op (`describe()["tools"]["total"]` stays **293**); this unblocks `qm/potentials.py` flipping numpy-free with the fast native path intact at n=400/600 (next rc). All 5 SSOT version locations bumped.

## [0.7.5rc119] - 2026-06-12

**`qm/gauge.py` (Yang-Mills SU(2)/SU(3)) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 10 → 9).** Carrier-removal #564 — the gauge-theory layer (SU(2)/SU(3) generators / eight Gell-Mann matrices / structure constants / Casimirs / connection / path-segment holonomy / Wilson loop). The generator matrices are held in the framework-native `Mat`; every matrix product routes through the Class-L `mat_matmul`, residual norms through `mat_norm`, and the path-segment holonomy `exp(i g A^a T^a)` through `mat_hermitian_eigendecompose` (`V·diag(e^{iλ})·Vᴴ`, the `e^{+iλ}` phase the Class-N `rational.cexp` Euler cascade) — **no numpy**.

- **`srmech/qm/gauge.py`** drops `import numpy as np` (and the `dense_matmul_complex`/`dense_norm`/`elementwise_transcendental`/`hermitian_eigendecompose` carrier imports). The SU(2) generators consume the rc115 numpy-free `spin.pauli_matrices()` 2×2 `Mat` blocks **directly** — so the rc115 `.to_numpy()` boundary coercion that this module carried is **removed** (gauge was the last consumer of spin's Pauli producer). The eight Gell-Mann matrices are exact small-integer `Mat` (λ⁸'s `1/√3` via the Class-N `rational.sqrt`); `casimir_operator`/`gauge_connection_matrix` are explicit `Mat` folds; `casimir_eigenvalue` is `trace(C₂)/dim`; `lie_algebra_residual` reads `f[a][b][c]`. The structure constants `f^{abc}` become plain nested Python lists (rank-3; `Mat` is 2-D only). Verified runs numpy-genuinely-absent: the SU(2)/SU(3) Casimir eigenvalues are **exactly 3/4 and 4/3**, the Lie-algebra residuals ~1e-16, Wilson-loop unitarity ~1e-15.
- No srmech-side **call** consumer — `sm`/`so8` only mention gauge in comments (so8 explicitly does NOT use `su3_structure_constants`); no producer-flip boundary needed.

`test_qm_gauge.py` was **rewritten numpy-FREE** — Hermiticity / trace / normalization (`tr(T^a T^b)=½δ^{ab}`) / Casimir / unitarity by direct `Mat`-entry arithmetic + the native `mat_matmul`, a deterministic LCG for the multi-segment Wilson loop, and an analytic diagonal-λ³ `exp` oracle, no np (per `[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`). The gauge cell in `test_qm_cascade_routing_rc33.py` is numpy-free too (independent analytic oracle + native `mat_matmul` unitarity). **CI-GUARD**: the must-raise example stays `propagators` (still a numpy carrier — gauge ≠ propagators); gauge **added** to the pure-wheel flipped-and-exercised list. **Carrier-only** — no math-ledger change; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. All 5 SSOT version locations bumped. Remaining **9** carriers: potentials / so8 / octonion / triality / propagators / pseudo_hermitian qm tail + `mcp/_coercion` + `spectral/__init__` + `ica_jade`.

## [0.7.5rc118] - 2026-06-12

**`qm/relativistic.py` (Dirac γ-matrix algebra) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 11 → 10).** Carrier-removal #564 — the relativistic-QM layer (γ-matrices / γ₅ / Weyl projectors / charge conjugation / Klein-Gordon / Dirac operator). The 4×4 operators are held in the framework-native `Mat`, assembled from the numpy-free Pauli 2×2 `Mat` blocks; every matrix product routes through the Class-L `mat_matmul`, residual norms through `mat_norm`, and the Klein-Gordon dispersion through the Class-N `rational.sqrt` — **no numpy**.

- **`srmech/qm/relativistic.py`** drops `import numpy as np` (and the `dense_dot_real`/`dense_matmul_complex`/`dense_matvec_real`/`dense_norm` carrier imports). The Dirac γ-matrices are built from the rc115 numpy-free `spin.pauli_*` 2×2 `Mat` blocks via a `_block4` helper (the numpy-free `np.block` replacement) — so the rc115 `.to_numpy()` boundary coercion that this module carried is **removed**. `gamma_5` / `charge_conjugation_matrix` use `mat_matmul`; `clifford_residuals` uses `mat_matmul` + `mat_norm`; `minkowski_metric` is a real `Mat`; 4-momenta are plain float sequences (`four_momentum_squared` / `klein_gordon_dispersion` compute the bilinear / dispersion numpy-free). Verified runs numpy-genuinely-absent: the Cl(1,3) Clifford residuals `{γ^μ,γ^ν}=2η^{μν}I` are **exactly 0.0**.
- **PRODUCER-FLIP**: `propagators` (still a numpy carrier) consumes `dirac_operator_momentum_space` + `minkowski_metric`, so those 3 callsites coerce `.to_numpy()` at the boundary (the legit bridge inside a still-numpy carrier, removed when propagators flips).

`test_qm_relativistic.py` was **rewritten numpy-FREE** — Clifford-algebra / chirality-projector / charge-conjugation (`C γ C^{-1} = -γ^T` via the native `mat_solve` for `C^{-1}`) / Klein-Gordon identities, all `mat_matmul`/`mat_norm` + direct `Mat`-entry comparison, no np oracle (per `[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`). The two relativistic-producer calls in `test_qm_propagators.py` bridge `.to_numpy()` (testing the still-numpy propagators). **CI-GUARD**: rc117 named `relativistic` as the pure-wheel must-raise example — moved it to `propagators` (still numpy) and added relativistic to the flipped-and-exercised list (the recurring lesson). **Carrier-only** — no math-ledger change; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. All 5 SSOT version locations bumped. Remaining **10** carriers: gauge / potentials / so8 / octonion / triality / propagators / pseudo_hermitian qm tail + `mcp/_coercion` + `spectral/__init__` + `ica_jade`.

## [0.7.5rc117] - 2026-06-11

**`qm/single_particle.py` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 12 → 11).** Carrier-removal #564 — the design-heavy submodule split out of rc116 (TDSE/TISE/Heisenberg/commutator/density-matrix/Liouville-von-Neumann). The single-particle dynamics layer now holds its working matrices in the framework-native `Mat` carrier and composes the eigenbasis time-evolution operator `V·diag(e^{-iλt})·Vᴴ` entirely from the Class-L `mat_*` family + the Class-N `rational.cexp` Euler cascade — **no numpy, no `np.exp`**.

- **`srmech/qm/single_particle.py`** drops `import numpy as np` (and the `dense_matmul_complex`/`dense_matvec_complex`/`dense_outer_complex`/`hermitian_eigendecompose`/`elementwise_transcendental` carrier imports). Matrices (`H`, `A`, `ρ`, `V`) are `Mat`; state vectors are plain `complex` lists (`Mat` is 2-D only). Every linear-algebra step routes through `mat_matmul` (matmul, matvec-via-column-`Mat`, outer-product-via-column·row) and `mat_hermitian_eigendecompose` (the eigenbasis); the per-mode phase `e^{-iλt}` is `rational.cexp(-λt)` (Euler `cos + i·sin`, NOT `np.exp`). `tise_solve` is now a thin pass-through to `mat_hermitian_eigendecompose` (returns the `(n,1)` real eigval `Mat` + `(n,n)` complex unitary `Mat`). The only srmech-side consumer is `tool_schema` registration metadata (strings, not a call — **no boundary coercion**, unlike rc115's producer-flip).
- Verified runs numpy-**genuinely**-absent (`_BLOCK_NUMPY` meta-path): TDSE preserves norm to 1.1e-16, TISE unitarity 7.4e-16 on the native path.

Three test files rewritten numpy-FREE: **`test_qm_single_particle.py`** asserts canonical *physical identities* (norm / energy / trace / hermiticity / unitarity / purity preservation; eigenstate-phase evolution) with a deterministic numpy-free PRNG building Hermitian `Mat`s and the `rational` cascade as the only oracle — no `np`, no numpy reference (per `[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`); the two `single_particle` tests in **`test_qm_cascade_routing_rc33.py`** (reconstruction + unitarity + closed-form TDSE, all `Mat`/`rational`); and the cross-module harmonic-oscillator TDSE test in **`test_qm_potentials.py`** (potentials' still-numpy `H` bridged to `Mat` once at the flipped-op boundary, the TDSE assertion then numpy-free). **Carrier-only** — the math was already cascade-routed, so no math-ledger change; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. All 5 SSOT version locations bumped incl. the scaffolding pin. Remaining **11** carriers: the so8/octonion/triality/relativistic/propagators/pseudo_hermitian/potentials/gauge qm tail + `mcp/_coercion` + `spectral/__init__` + `ica_jade`.

## [0.7.5rc116] - 2026-06-11

**`qm/sm.py` (Standard Model) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 13 → 12).** Carrier-removal #564, the next qm-submodule consumer flip after rc115's spin/bell. The roadmap paired `single_particle` + `sm` for this rc; per the "design-heavy — don't rush, **split on wobble**" discipline, `sm` (clean) ships now and the design-heavy `single_particle` (matrix-exponential `V·diag(e^{−iEₜ})·V†` via a complex diagonal from Class-N `rational` trig) is split to its own later rc.

- **`srmech/qm/sm.py`** drops `import numpy as np` (and the `dense_matmul_complex`/`dense_norm` carrier import). Every scalar electroweak op already routed through the Class-N `rational` cascade (Higgs VEV `√(μ²/2λ)`; W/Z masses; Weinberg residual via `rational.cos`; Yukawa `y·v/√2`) — those are unchanged. The only numpy was the flavour sector: **`ckm_matrix`** now returns an exact-cascade 3×3 complex `Mat` (the mixing-angle `cos`/`sin` via `rational`, the CP phase `e^{±iδ}` via `rational.cexp`, assembled by entrywise list build); **`ckm_unitarity_residual`** computes `V·Vᴴ` via the native `mat_matmul`, the entrywise `− I` as plain `Mat`-entry subtraction, and the Frobenius norm via the rc114 Class-N `mat_norm` (no numpy). Verified numpy-absent: a unitary CKM gives residual ≈3.8e-16. `sm` is a **leaf** (no consumers — no producer-flip boundary needed, unlike rc115's relativistic/gauge).

`test_qm_sm.py` was **rewritten numpy-FREE** — no `np` oracle: unitarity via `mat_matmul` + a `_max_dev_from_identity` direct `Mat`-entry comparison (numpy is not a validation reference per `[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`). Verified by passing the file with numpy blocked at the meta-path. **Carrier-only** — the math was already cascade-routed, so the math ledger is untouched; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin. Remaining **12** carriers: `single_particle` + the so8/octonion/triality/relativistic/propagators/pseudo_hermitian/potentials/gauge qm tail + `mcp/_coercion` + `spectral/__init__` + `ica_jade`.

## [0.7.5rc115] - 2026-06-11

**First qm-submodule CONSUMER carrier-flips — `qm/spin.py` + `qm/bell.py` go numpy-FREE (`CEIL_NUMPY_CARRIER` 15 → 13).** Carrier-removal #564, the first consumers to flip on the rc114 `mat_norm`/`mat_dot_*` + the rc74 `mat_hermitian_eigendecompose` foundation. Both modules were already cascade-routed for the *math*; this removes numpy as the **carrier** so they import and run with numpy genuinely absent.

- **`srmech/qm/spin.py`** drops `import numpy as np`. `pauli_matrices()` / `pauli_identity()` return **exact** 2×2 complex `Mat` (entries in `{0, ±1, ±i}` — no float approximation); `pauli_spin_operator(direction)` accepts any 3-sequence, normalises via the rc114 `mat_norm`, and builds the 2×2 `Mat` by entrywise list arithmetic (no `abs()` — Class-K magnitude is the `mat_norm` `√(Σ|·|²)`); `pauli_clifford_residuals()` forms every Pauli product with the native `mat_matmul`, combines entrywise as flat complex lists, and measures with `mat_norm` (Clifford anticommutator + commutator residuals exactly `0.0`).
- **`srmech/qm/bell.py`** drops `import numpy as np` (incl. two stale `-> np.ndarray` annotations → `-> "Mat"`, and a docstring that cited "numpy's Jacobi floor" as the accuracy reference). `chsh_pauli_combination()` / `chsh_operator()` return `Mat` built via the numpy-free `kron` cascade + entrywise list arithmetic (the `1/√2` phase via Class-N `rational.sqrt`); `chsh_pauli_combination_norm()` uses the EXACT integer `eigvals_exact` on the {0,±1} 4×4 (Tsirelson primary identity `= 2` at residual **exactly 0**); `operator_norm()` / `chsh_operator_norm()` go through the unconditionally-numpy-free `mat_hermitian_eigendecompose` (Class-K max-`|λ|` via sign-branch, no `abs()`).
- **`srmech/qm/__init__.py`** relaxes the eager `_require_numpy("srmech.qm")` subpackage gate to LAZY per-submodule `__getattr__` (the rc71 signal_processing precedent / `[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]`): the flipped `spin`/`bell` import with numpy absent, while the not-yet-flipped qm modules still surface the actionable `[scientific]` hint (not a bare numpy `ImportError`).
- **Producer-flip boundary coercion** — `qm/relativistic.py` (Dirac γ-matrices) and `qm/gauge.py` (SU(2) generators) are STILL numpy carriers (they flip in their own later #564 rcs) that *consume* `spin.pauli_matrices()`/`pauli_identity()`. Since those now return `Mat`, the two consumers coerce the producer to ndarray at the import boundary via the lossy export bridge (`p.to_numpy()`) — the legitimate use of the bridge: a numpy module receiving a numpy-free `Mat`. The boundary disappears when each module itself goes numpy-free. (Without this, `np.block([[I2,…],[…,-I2]])` over a `Mat` raised `TypeError`.)

`test_qm_spin.py` + `test_bell_chsh.py` were **rewritten numpy-FREE** — no `np` oracle, no `.to_numpy()` (numpy is not a validation reference per `[[feedback_no_numpy_rosetta_peer_continuous_float_error_collecting]]`): eigenvalues come from `mat_hermitian_eigendecompose`, Kronecker from the `kron` cascade, and every matrix check is a direct `Mat`-entry comparison — so the numpy-absent install runs its own tests (verified by collecting + passing both files with numpy blocked at the meta-path). **Carrier-only** — the math was already cascade-routed, so the math ledger is untouched; no new public op (`describe()["tools"]["total"]` stays **293**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin. Remaining **13** carriers: the qm matrix tail (`gauge`/`octonion`/`potentials`/`propagators`/`pseudo_hermitian`/`relativistic`/`single_particle`/`sm`/`so8`/`triality`), `mcp/_coercion`, `spectral/__init__`, `ica_jade`.

## [0.7.5rc114] - 2026-06-11

**FOUNDATION for the carrier-ratchet → 0 endgame — numpy-free `mat_norm` / `mat_dot_real` / `mat_dot_complex` (`CEIL_NUMPY_CARRIER` stays 15).** Carrier-removal #564, the first of three spine foundations (with the planned exact-RREF-rank + numpy-free octonion-mult) that gate the remaining qm/so8/spectral consumer-flips. A `carrier-ratchet-to-zero` workflow ground-truthed the remaining 15 carriers against source and caught the load-bearing trap: `dense_norm` / `dense_dot_real` / `dense_dot_complex` are numpy **CARRIERS** (they call `np.ascontiguousarray` / `np.iscomplexobj` / the elementwise-multiply cascade over numpy arrays) and **RAISE** on a numpy-absent install — the rc70 *runnable ≠ loadable* trap. Nothing in the tree computed `‖x‖` or `a·b` over the numpy-free carriers, so the qm Clifford / unitarity / η-Hermiticity residuals and so8's Gram-Schmidt could not flip.

- `srmech/amsc/laplacian.py` adds three genuinely numpy-free reductions over the `Mat` / `HV` carriers (added to both `__all__` exports): **`mat_norm(x)`** = `√(Σ|xᵢ|²)` (vector 2-norm / matrix Frobenius) via a pure-Python `Σ|xᵢ|²` (complex `|z|² = z.real²+z.imag²`, **no `abs()`**, **no `math.hypot`**) then the libm-free Class-N `rational.sqrt` root — **Class N ∘ Class M**; **`mat_dot_real(a,b)`** / **`mat_dot_complex(a,b)`** = plain **bilinear** `Σ aᵢbᵢ` (matching numpy `a·b`, NOT the conjugating `vdot`) over a pure-Python reduction. A shared `_iter_mat_scalars` flattens a `Mat` (interleaved-complex aware) / `HV` / flat sequence row-major.

Value-faithful to `dense_norm` / `dense_dot_*` / the numpy peers to ~1 ULP (same float sum-of-products), verified both with numpy present AND in a **fresh subprocess with numpy blocked at the meta-path** (`test_mat_norm_dot_rc114.py` — the real fresh-import-numpy-free gate, stronger than a monkeypatch). **Foundation only** — no consumer flips, so `CEIL_NUMPY_CARRIER` stays **15**; the math ledger is untouched (these are new numpy-free ops, not numpy removals). The three are registered public `srmech.amsc.laplacian.*` callables exactly like their `dense_*` peers, so per the registry checklist each gets a `ToolEntry` + a `composition_of_c` `rosetta_classification.ndjson` line, bumping `describe()["tools"]["total"]` **290 → 293** (seven count-tests updated). ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc113] - 2026-06-11

**RBS-LM subpackage goes numpy-FREE — incidental-source RNG re-based onto our own (`CEIL_NUMPY_CARRIER` 17 → 15).** Carrier-removal #564. `srmech.rbs_lm` (the F166 inference substrate: Class A∘M Klein-4 encode + iω₇ position + Class M retrieve, temperature-sampled) carried numpy only as an **incidental deterministic source**, never a correctness oracle — so per user direction ("use our own rng … rbs_lm is ours") the three numpy-RNG sites are swapped to the framework-native stdlib stream and the values re-based ONCE:

- **`rbs_lm/substrate.py`** drops `import numpy as np`. The per-token vector seed `np.random.default_rng(token_seed(word))` → `hdc.klein4_random(D, seed=token_seed(word))` (the §22 numpy-optional stdlib `random.Random` path); the `np.full(D, sector, uint8)` sector key → a numpy-free `bytes([sector]) * D` constant (`klein4_bind` coerces it); and the encode helpers + `ContextSubstrate` now return the framework-native **`HV`** carrier end-to-end (no `.to_numpy()`). `sim_k4_batch` is the Class-M `hdc.klein4_similarity` over each HV candidate (== the old `(candidates == query).mean(axis=1)`).
- **`rbs_lm/inference.py`** drops `import numpy as np`. `_softmax` routes its per-element exp through the Class-N **`rational.exp`** cascade (NOT the numpy-carrier `elementwise_transcendental`); `vocab_vecs` is a `list[HV]` (was `np.stack`); the learn-memory subsample `rng.choice(…, replace=False)` → `random.Random(learn_seed).sample`; the infer sampler `gr.choice(…, p=p)` → `random.Random(seed).choices(weights=p)`. Distributions/probs are plain Python `list`s.
- **`rbs_lm/__init__.py`** REMOVES the eager `_require_numpy("srmech.rbs_lm")` gate (per `[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]`: both layers must fall — the whole subpackage is now numpy-free, so `import srmech.rbs_lm` succeeds with numpy genuinely absent, no `[scientific]` extra).

**Authorized one-time RNG re-base** (numpy-as-incidental-source, not numpy-as-accuracy): stdlib MT19937 ≠ numpy PCG64, so the underlying Klein-4 bytes + sampled sequences change, but every test asserts an RNG-INDEPENDENT structural property (determinism, the XOR-sector relationship `s₁ == s₀^1`, self-similarity == 1.0, bigram-legality, same-seed determinism) — no test pins a specific byte value, so the re-base needs no value oracle. `test_rbs_lm.py` migrates the ndarray assertions (`.shape` / `np.array_equal` / `np.unique`) to HV-native (`len` / `==` / `.tolist`). **Carrier-only** — the encode math was already the cascade (`hdc.klein4_*`), so the math-ratchet ledger is **untouched**; the A-N transcendental ratchet stays green (`rational.exp` IS the cascade). No new public op (`describe()["tools"]["total"]` stays **290**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin. Remaining **15** carriers: the qm matrix layer (TOML `[class]` reframe / lossy-peer delete — *not* per-module flips), `mcp/_coercion`, `spectral/__init__`, `ica_jade` (numpy-as-accuracy: `eigh`), and the so8/triality matrix-algebra tail (numpy-as-accuracy: `matrix_rank`).

## [0.7.5rc112] - 2026-06-11

**Carrier-ratchet ACCURACY fix — `the_one` was a false positive (`CEIL_NUMPY_CARRIER` 19 → 18 → 17).** Carrier-removal #564, opening the qm-layer phase. NOT a carrier removal — a correction to the ratchet's *measurement*:

- `amsc/cascade/one.py` (the exact-rational `the_one` generator) is **numpy-FREE at import** — its only numpy is a LAZY `require_numpy` inside the opt-in `One.to_numpy` / `One.to_matrix` float exports. But the ratchet's scanner used a naive `line.startswith("import numpy")` over *every* line, and a docstring that wrapped to `"import numpy lazily (the …"` at column 0 tripped it, so `the_one` was wrongly counted as a carrier.
- The scanner is hardened to a real-import regex (`_is_numpy_import`): it matches `import numpy` / `import numpy as np` / `import numpy.sub` / `from numpy[.sub] import …` (optionally trailed by a comment) and **not** `import numpy <word>…` prose. `the_one` drops out of the count; the 17 genuine carriers (all real `import numpy as np`) are unchanged. The `one.py` docstring is also reworded defensively.

Honest down-only decrement (the ratchet now reflects reality — `the_one` was never a carrier). No source op changed; `describe()["tools"]["total"]` stays **290**, `classes` **2**; ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin. The remaining **17** are the real carriers: the qm matrix layer (TOML `[class]` reframe / lossy-peer delete) + `rbs_lm` + `mcp/_coercion` + `spectral/__init__` + `ica_jade`.

## [0.7.5rc111] - 2026-06-11

**Fourteenth CONSUMER carrier-flip — `jpeg` goes numpy-FREE, the LAST clean DSP carrier flip (`CEIL_NUMPY_CARRIER` 19 → 18).** Carrier-removal #564. The block-DCT image compressor (Class L ∘ K ∘ B):

- The block transform already ran numpy-free through the rc104 `dct.op` (returns a list-of-lists); `jpeg` now carries the 2-D image as **nested Python `list`s end-to-end**. The canonical luminance quantisation table becomes a plain list-of-lists; the Wallace quality scaling is per-element (`int(...)` is exact floor for the non-negative `(luma·scale + 50)/100`); the Class-K quantise is `round(coeff / qt)` (Python `round` is round-half-to-even — bit-identical to `np.round`); and the encode/decode block loops index nested lists directly (the `_dct` `np.asarray` consumer-boundary wrapper is removed).
- Drops `import numpy as np`. **Encode** returns `(quant_blocks, shape, quant_table)` with `quant_blocks` a `list` of 8×8 integer list-of-lists and `quant_table` a list-of-lists; **decode** returns a 2-D `list` (both were ndarrays). Inputs coerce numpy-free via `tolist()`.

Value-faithful to the prior matrix path (the DCT basis is the Class-N `rational.cos` cascade, value-faithful to ~1e-9): verified by an encode→decode round-trip (RMS ≈ 0.58 at quality 75, quantisation-bounded) and a numpy-absent subprocess run. The `test_jpeg_smoke` `len(quant_blocks) == 4` assertion is unchanged. **Carrier-only** — the math was already cascade-routed, so the math-ratchet ledger is **untouched**. No new public op (`describe()["tools"]["total"]` stays **290**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

With `jpeg` flipped, the clean-DSP carrier-flip phase of #564 is complete; the remaining carriers are the qm matrix layer (resolved via the TOML `[class]` reframe / lossy-peer deletion, the rc75 Hurwitz precedent — *not* per-module flips) plus a linalg-consolidation pass to retire the duplicate `mat_*` / `matrix_cascades` SVD paths.

## [0.7.5rc110] - 2026-06-11

**Twelfth + thirteenth CONSUMER carrier-flips — the two Path B DSP duals go numpy-FREE (`CEIL_NUMPY_CARRIER` 21 → 19).** Carrier-removal #564. Both are clean leaf flips of ops whose Path A counterparts already went numpy-free (rc80 `matched_filter`, rc87 `wiener`):

- **`path_b_ops/matched_filter`** (Class A∘C∘M form-function cross-correlation) drops `import numpy as np` and delegates straight to the rc79 numpy-free `_dsp.correlate` (the FFT-convolution-theorem correlation `sum_n a[n+k]·conj(v[n])`, which coerces both inputs to 1-D lists and returns a list). The prior `np.asarray` input-coerce + return-wrap are gone; the op returns a `list` (was an ndarray).
- **`path_b_ops/wiener`** (Class L∘N cyclic-graph-Laplacian eigenbasis + rational MMSE gain) takes the rc87 closed-form list-comprehension form: `_sc.fft` returns `List[complex]` numpy-free, the per-bin power is `|X|² = X.real² + X.imag²` (no `abs()`), the `np.maximum(·, 1e-30)` eps-floors become the builtin `max`, the Class-N rational gain `S/(S+N)` and the spectral product are explicit comprehensions, `_sc.ifft` → real part. Returns a `list` of float.

Both flips are **carrier-only** — the math was already cascade-routed (`_dsp.correlate` / `_sc.fft`/`_sc.ifft`), so only the numpy carriers (`np.asarray` / `np.maximum` / `np.real`) go. The math-ratchet ledger is **untouched**. The Path A↔Path B D1-equivalence smoke (`test_signal_processing_path_b_mvp`) keeps passing (list vs list). No new public op (`describe()["tools"]["total"]` stays **290**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc109] - 2026-06-11

**Eleventh CONSUMER carrier-flip — `mimo_svd` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 22 → 21).** Carrier-removal #564. The first consumer to route onto the rc108 `mat_svd` Mat-carrier foundation:

- The MIMO channel-matrix SVD (`H = U·S·Vᴴ`, Class L) drops `import numpy as np` and `np.linalg.svd` entirely. It coerces the channel matrix numpy-free (`tolist()` covers ndarray AND `Mat`), wraps it in `Mat.from_rows(..., is_complex=True)`, calls `laplacian.mat_svd` (Gram `AᴴA` → `mat_hermitian_eigendecompose` → `√λ` + `A·v/σ` + orthonormal null completion), and returns plain Python `list`s — `U` `(n_rx, n_rx)` list-of-rows, `S` descending `list`, `Vh` `(n_tx, n_tx)` list-of-rows (were ndarrays).
- **Value-faithful, NOT bit-identical** (per `[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]`): SVD is non-unique in the per-pair phase and the degenerate / null subspace, so correctness is the reconstruction `H ≈ U·diag(S)·Vᴴ` + unitarity of `U` / `Vh` + singular-value match to NumPy. Differential-verified over 100 cases (real/complex × square/tall/wide × full/rank-deficient): 0 reconstruction failures, 0 singular-value failures.

Because the op also removes its `np.linalg.svd`, this decrements **both** ledgers: `CEIL_NUMPY_CARRIER` 22 → 21 and the math-ratchet `CEIL_LINALG_FFT` 23 → 22. The `test_mimo_svd_smoke` `.shape` checks move to `isinstance(U, list)` / `len`. The rc71 numpy-free-reachable exemplar (the still-numpy op that must raise the clean `[scientific]` hint) moves `mimo_svd → ica_jade` — `ica_jade`'s `np.linalg.eigh` is numpy-as-ACCURACY (not just a carrier), so it stays gated. No new public op (`describe()["tools"]["total"]` stays **290**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc108] - 2026-06-11

**`mat_svd` foundation — numpy-free FULL SVD over the Mat carrier (carrier-removal #564, Mat-bridge foundation #5).** The op `mimo_svd` has waited on this; it does NOT decrement `CEIL_NUMPY_CARRIER` (still 22) — it's the foundation the next consumer flip routes onto:

- `laplacian.mat_svd(A: Mat) -> (U: Mat, S: list[float], Vh: Mat)` mirrors the `svd(A, full_matrices=True)` shape contract: `U` `(m,m)` complex, `S` descending `min(m,n)`, `Vh` `(n,n)` complex, so `A = U[:, :k]·diag(S)·Vh[:k, :]`. The right vectors are eigenvectors of the Hermitian PSD Gram `AᴴA` via `mat_hermitian_eigendecompose` (reordered descending); `S = √λ` (the Class-N `rational.sqrt`, libm-free); the left vectors are `uⱼ = A·vⱼ/σⱼ` for `σⱼ` above the rank tolerance, with an orthonormal modified-Gram–Schmidt completion of the left-nullspace block. **Unconditionally numpy-free** (composes the native-backed `mat_matmul` + `mat_hermitian_eigendecompose`; pure-Python completion).
- **Value-faithful, NOT bit-identical** (per `[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]`): SVD is non-unique (a per-pair phase, and a free unitary basis inside a degenerate-σ / null subspace), so correctness is pinned by **reconstruction** (`A ≈ U·diag(S)·Vᴴ`), **unitarity** (`UᴴU ≈ I`, `Vh·Vhᴴ ≈ I`), and **singular-value match** to NumPy — verified across real/complex × square/tall/wide × full-rank/rank-deficient. The rank tolerance is `σ_max·max(m,n)·1e-6` (relative to the Gram eigen-route's ~1e-7·σ_max small-σ floor, NOT machine-eps) so a sub-floor σ routes its U column through the completion instead of letting `A·v/σ` amplify the error.

Registered as a `ToolEntry` (like its `mat_*` siblings) — `describe()["tools"]["total"]` **289 → 290** (the five count-tests bump in lockstep); `__all__` + rosetta `composition_of_c` bucket added. `CEIL_NUMPY_CARRIER` unchanged at **22**; math-ratchet ledger untouched; ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc107] - 2026-06-11

**Tenth CONSUMER carrier-flip — `mlse` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 23 → 22).** Carrier-removal #564. The Viterbi-trellis channel equaliser (Class L ∘ K), no `np.linalg`:

- The trellis tables — transition / emission / initial log-prob — become pure-Python **list-of-lists** built with the Class-N `rational.log` cascade (uniform `−log A` transition priors; uniform `−log n_states` initial). The per-branch metric is an explicit `−|obs − expected|²` multiply-add (squared distance, monotone in `|·|`, so no `sqrt` and no `abs()`).
- The **no-ISI** fast path (`memory == 0`) is a per-sample squared-distance argmin over `obs − taps[0]·alpha` (strict `<`, first-minimum tie-break matching `np.argmin`), replacing the `elementwise_hypot` carrier.
- The trellis search itself delegates to the already-numpy-free `viterbi.op` (rc83), which returns a plain `list`. Inputs coerce numpy-free via `tolist()`; the op now returns `list[int]` (was an ndarray).

Differential-verified **BIT-IDENTICAL** to the numpy reference over 180 cases (BPSK + QPSK × channel-memory {0, 1, 2} × random observations; 0 sequence mismatches). The `test_mlse_smoke` `.shape == (4,)` moves to `isinstance(syms, list) and len(syms) == 4`. `CEIL_NUMPY_CARRIER` 23 → 22 (down-only ratchet). The math-ratchet ledger is untouched (the op now uses no numpy; `mlse` only appears in math-ratchet *comments*, none enforced). `mlse`'s `rosetta_classification.ndjson` bucket is unchanged. No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc106] - 2026-06-11

**Ninth CONSUMER carrier-flip — `psk_qam` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 24 → 23).** Carrier-removal #564. The fsk-cousin constellation mapper (Class I ∘ K), no `np.linalg`:

- The **PSK** constellation points `e^{i·2π·k/M}` route through `_exp_i` (the Class-N `rational.cos` / `rational.sin` cascade over the substrate-native `_PI` = `pi_cascade_digits(30)`, native libm-free) — bit-faithful to the prior `elementwise_transcendental(·, 'exp_i')` path. The **QAM** grid is built from pure-Python Gray-coded levels (`√M` via the Class-N `rational.sqrt`), replacing `np.meshgrid(...).flatten()` with a row-major `complex(levels[col], levels[row])` comprehension (byte-faithful ordering).
- The **demod** nearest-neighbour decision is an **argmin over the squared Euclidean distance** `|received − const|²` (squared distance is monotone in `|·|`, so the decision is identical to the prior `argmin(hypot(re, im))` — and now needs no `sqrt` / no `hypot` / no `abs()`; strict `<` keeps the first-minimum index, matching the prior `np.argmin` tie-break). The top-level `import numpy as np` is **gone**; inputs coerce numpy-free via `tolist()`; modulate returns `list[complex]`, demodulate returns `list[int]` (were ndarrays).

The `test_psk_qam_smoke` `.shape == (4,)` / `np.iscomplexobj` checks move to `isinstance(points, list)` / `len` / `isinstance(z, complex)`; the rc52 demod round-trip is unchanged (decision is identical). `CEIL_NUMPY_CARRIER` 24 → 23 (down-only ratchet). The math-ratchet ledger is untouched (the op now uses no numpy at all; `psk_qam` only appears in math-ratchet *comments*, none of which are enforced counts). `psk_qam`'s `rosetta_classification.ndjson` bucket is unchanged. No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc105] - 2026-06-11

**Eighth CONSUMER carrier-flip — `vector_quantisation` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 25 → 24).** Carrier-removal #564. The cleanest remaining consumer — nearest-codebook lookup (Class E ∘ M ∘ B), no `np.linalg`:

- The nearest-neighbour query becomes a **pure-Python argmin** over the squared Euclidean distance `Σ_j (x_j − c_j)²` (the `|x|² − 2x·c + |c|²` matmul cross-term trick is unnecessary for an argmin, so `dense_matmul_real` is dropped). Inputs coerce numpy-free via `tolist()` (a single 1-D vector is accepted as one row). The top-level `import numpy as np` is **gone**; encode returns `list[int]`, decode returns a list-of-rows (were ndarrays).
- **Differential-verified**: the encode argmin is **bit-identical** to numpy's `argmin(Σ(x−c)², axis=1)` over 200 random `(n_codes, d, n_vec)` configs (0/1262 mismatches); decode round-trips.

The single `idx.shape == (10,)` smoke moves to `len(idx) == 10`. `CEIL_NUMPY_CARRIER` 25 → 24 (down-only ratchet). The math-ratchet ledger is untouched (`np.sum`/`np.argmin`/`np.asarray` + the named `dense_matmul_real` match no counted pattern — and the op now uses no numpy at all). `vector_quantisation`'s `rosetta_classification.ndjson` bucket stays `python_only_irreducible`. No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc104] - 2026-06-11

**Seventh CONSUMER carrier-flip — `dct` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 26 → 25).** Carrier-removal #564. The DCT-II / DCT-III (the JPEG / audio-codec cosine transform) flips numpy-free — the involved one of the batch, because it also has a `jpeg` consumer:

- The cosine basis matrix `_dct_matrix` is built directly as a **list-of-lists** through the Class-N `rational.cos` cascade over the substrate-native `_PI = pi_cascade_digits(30)` source (no `np.cos` / `np.pi`); value-faithful to the `np.cos` matrix to ~1e-9. The transform is a pure-Python matvec (1-D) / per-axis row|column transform (2-D, `axis` 0/1/-1 — the jpeg block case). The old `scipy.fft.dct` fast-path is **dropped** (it required numpy as a carrier); the cascade DCT-matrix path IS the substrate-native realisation.
- **DCT-III parity fix**: scipy's `norm=None` DCT-III weights the `x_0` term by **1**, not 2 (`y_k = x_0 + 2·Σ_{j≥1} M[k][j] x_j`), making it the exact inverse of DCT-II. The prior matrix-fallback's blanket `2.0·Σ` doubled it — a latent inconsistency that was masked because the op *preferred* the scipy path. The numpy-free `_transform` now matches scipy exactly for both types.
- **`jpeg` consumer**: `jpeg` calls `dct_op` for its block DCT-II encode / DCT-III decode and expects ndarrays. jpeg is still a numpy carrier (it flips in its own later rc), so it now coerces dct's list return back to ndarray at a thin `_dct(...)` boundary wrapper (`np.asarray`). Values are bit-identical to the prior matrix path.
- **Differential-verified**: dct 1-D and 2-D (both axes), DCT-II and DCT-III, all ~1e-14 vs `scipy.fft.dct(..., norm=None)`; the `jpeg` encode→decode round-trip recovers the image with RMSE 1.2 / 0.25 / 0.025 at quality 50 / 90 / 99 (clean lossy-quant behaviour). Ripples: `test_dct_smoke` / `test_dct_op_stable_and_invertible` `X.shape == (8,)` → `len`, `np.all(np.isfinite)` → `all(math.isfinite)`, `M @ x` → an explicit pure-Python matvec; the rc33 `_dct_matrix` basis tests' `cascade.shape` → `len`-based checks (`np.allclose(cascade, reference)` still coerces the list).

`CEIL_NUMPY_CARRIER` 26 → 25 (down-only ratchet; only `dct` drops its `import numpy`, `jpeg` keeps its own). The math-ratchet ledger is untouched (`rational.cos` + pure-Python; no counted linalg/fft/matmul/ufunc patterns). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc103] - 2026-06-11

**Sixth CONSUMER carrier-flip — `fsk` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 27 → 26).** Carrier-removal #564. The FSK (frequency-shift-keying) modulator/demodulator — educational civilian-comms textbook reference per the trauma-informed defensive scope — flips numpy-free:

- The per-symbol tone phases `e^{i·2π·f·t}` route off the numpy-carrier `elementwise_transcendental(·, "exp_i")` onto a per-element Class-N `_exp_i(θ) = complex(rational.cos(θ), rational.sin(θ))` over the substrate-native `_PI = pi_cascade_digits(30)` source (native libm-free, bit-faithful to the prior path). The demodulator correlator bank becomes a pure-Python complex matvec `corr_k = Σ_j tone[k][j]·conj(window[j])` whose nearest-tone decision is `argmax|corr|²` — monotone in `|corr|`, so **no `sqrt` and no `abs()`** (drops the `dense_matvec_complex` + `elementwise_hypot` carriers too). Inputs coerce numpy-free via `tolist()`. The top-level `import numpy as np` is **gone**; modulate returns `list[complex]`, demodulate returns `list[int]` (was ndarrays).
- **Differential-verified**: modulate is bit-faithful to the `e^{i2πft}` reference (max-err ~1e-16); a noiseless demod round-trip recovers the symbol stream exactly, and a 0.01-noise sweep over 300 random `(M, samples_per_symbol)` configs misclassifies <0.1% of symbols (noise-edge, not the routing). The one `waveform.shape == (4*8,)` smoke moves to `len(waveform) == 4*8`.

`CEIL_NUMPY_CARRIER` 27 → 26 (down-only ratchet). The math-ratchet ledger is untouched (fsk's `np.pi` constant / `np.conj` / `np.argmax` + the named `elementwise_*`/`dense_matvec_complex` helpers match none of the counted linalg/fft/matmul/ufunc patterns — and the op now uses no numpy at all). fsk's `rosetta_classification.ndjson` bucket stays `python_only_irreducible` (still a Python op with no C peer). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc102] - 2026-06-11

**Fifth CONSUMER carrier-flip — `map_ml` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 28 → 27).** Carrier-removal #564. The same real-solve family as `lmmse`: the linear-Gaussian MAP / ML estimator `x_hat = (Aᵀ R_v⁻¹ A + R_x⁻¹)⁻¹ (Aᵀ R_v⁻¹ y + R_x⁻¹ μ)` (Kay 1993 §7 / §11):

- The two covariance inverses (`R_v⁻¹`, and `R_x⁻¹` on the MAP branch) route off the numpy-carrier `dense_solve(M, np.eye(n))` onto the native `mat_solve(Mat, identity_Mat)` over real `Mat`s (the inverse IS the solve against the identity; rides `srmech_dense_solve_f64`). `Aᵀ R_v⁻¹` rides `mat_matmul`, the normal-equation matrix `Aᵀ R_v⁻¹ A` rides `mat_matmul`, and the `Aᵀ R_v⁻¹ y` / `R_x⁻¹ μ` matvecs + the `M + R_x⁻¹` precision add are pure-Python sums. Inputs (`y`, `A`, `R_noise`, optional `R_prior` / `mean_prior`) coerce numpy-free via `tolist()`. The top-level `import numpy as np` is **gone**; both branches return `list[float]` (was an ndarray).
- **Differential-verified** value-faithful to the numpy-present closed-form reference over 200 random `(m, n)` trials (ML max-err ~7e-12 — the normal-equations conditioning — and MAP max-err ~5e-14). The `x_hat.shape == (2,)` smoke (baseline) and `x_ml.shape`/`x_map.shape == (n,)` + `np.all(np.isfinite(...))` asserts (rc64 test) move to `len(...)` + `all(math.isfinite(v) ...)`; the rc64 residual-check `"dense_solve(" in txt` becomes `"mat_solve(" in txt`.

`CEIL_NUMPY_CARRIER` 28 → 27 (down-only ratchet). The math-ratchet ledger is untouched (`mat_solve`/`mat_matmul` + `np.asarray` analogues are not counted linalg/fft/matmul/ufunc patterns — here the op uses none of numpy at all). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc101] - 2026-06-11

**Fourth CONSUMER carrier-flip — `lmmse` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 29 → 28).** Carrier-removal #564. A different sub-shape from the eigendecomposition consumers: the real-valued linear MMSE estimator `x_hat = mean_x + R_xy·R_yy⁻¹·(y − mean_y)`:

- The Class-L gain solve routes off the numpy-carrier `dense_solve` onto the native `mat_solve` over a real `Mat` — solving `R_yyᵀ·Z = R_xyᵀ` for `Z` so `K = Zᵀ = R_xy·R_yy⁻¹` (the solve rides `srmech_dense_solve_f64`); the `K·(y − mean_y)` estimate becomes a pure-Python matvec `mx[i] + Σ_j Z[j,i]·(y_j − my_j)`. Inputs (the vector + the two covariance matrices + the optional means) coerce numpy-free via `tolist()`. The top-level `import numpy as np` is **gone**; `op` returns `list[float]` (was an ndarray).
- **Differential-verified** value-faithful to the numpy-present reference. The one `x_hat.shape == (1,)` smoke moves to `len(x_hat) == 1`.

`CEIL_NUMPY_CARRIER` 29 → 28 (down-only ratchet). The math-ratchet ledger is untouched (`dense_solve`/`dense_matvec_complex` + `np.asarray`/`np.zeros`/`np.ascontiguousarray` match none of the counted patterns). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc100] - 2026-06-11

**Third CONSUMER carrier-flip — `heat_kernel` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 30 → 29).** Carrier-removal #564. The graph heat-kernel denoiser `exp(−tL)·signal = V·diag(exp(−tλ))·Vᴴ·signal` flips numpy-free:

- The Laplacian eigendecomposition routes off the numpy-carrier `hermitian_eigendecompose` onto the native `mat_hermitian_eigendecompose`; the spectral filter `g(λ) = exp(−t·λ)` (real eigenvalues) routes off the numpy-carrier `elementwise_transcendental(…, "exp")` onto a per-bin Class-N `rational.exp(−t·λ_k)` cascade (the scalar float-returning `exp`, which dispatches to native `srmech_exp`); the project (`Vᴴ·signal`) and reconstruct (`V·(g ⊙ coeffs)`) matvecs become pure-Python nested sums over the eigenvector `Mat`. The top-level `import numpy as np` is **gone**; `op` returns `list[complex]` (was ndarray).
- **Differential-verified**: mass conservation (the graph-Laplacian null-vector preserves the sum) holds to <1e-9, the output stays real for a real Laplacian + real signal, and an impulse diffuses onto its neighbour. The `out.shape` smoke asserts move to `len(out)`, `out.real.sum()` → `sum(v.real for v in out)`, `np.max(out.imag**2)` → `max(v.imag**2 for v in out)`, `out.real[1]` → `out[1].real`.

`CEIL_NUMPY_CARRIER` 30 → 29 (down-only ratchet). The math-ratchet ledger is untouched (`dense_matvec_complex`/`elementwise_transcendental`/`np.asarray` match none of the linalg/fft/matmul/ufunc patterns). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc99] - 2026-06-11

**Second CONSUMER carrier-flip — `music` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 31 → 30).** Carrier-removal #564. The ESPRIT sibling on the completed Mat foundation: the MUSIC pseudospectrum DOA estimator flips numpy-free:

- The covariance eigendecomposition routes off the numpy-carrier `hermitian_eigendecompose` onto the native `mat_hermitian_eigendecompose` (ascending eigenvalues → the noise subspace is the smallest `M − n_sources` eigenvectors via a pure-Python `sorted`, no `np.argsort`); the noise-subspace projection `Enᴴ·A` routes off `dense_matmul_complex` onto the native `mat_matmul` (`Enᴴ` built as a fresh `Mat` over `conj(eigvecs[i, noise_col])`); the pseudospectrum `1 / Σ_s |proj[s,k]|²` is a pure-Python column loop (`|z|² = re²+im²`, no `abs()`). The top-level `import numpy as np` is **gone**; `op` returns a `list[float]` (was an ndarray).
- **Differential-verified**: the pseudospectrum peak lands at the true source spatial frequency (within one grid bin); all values positive. The `psd.shape == (...)` smoke asserts move to `len(psd) == ...`, `np.all(psd > 0)` → `all(v > 0 for v in psd)`, `np.argmax` → a pure-Python argmax. The rc71 "numpy op raises the clean `[scientific]` hint" exemplar moves from `music` to `mimo_svd` (which still needs a `mat_svd` foundation op, so it stays the long-lived numpy-requiring exemplar).

`CEIL_NUMPY_CARRIER` 31 → 30 (down-only ratchet). The math-ratchet ledger is untouched (music's numpy — `np.asarray`/`np.sum`/`np.argsort` + the named `dense_matmul_complex` — matches none of the linalg/fft/matmul/ufunc patterns). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc98] - 2026-06-11

**First CONSUMER carrier-flip on the completed Mat foundation — `esprit` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 32 → 31).** Carrier-removal #564. The Mat foundation is now complete (Hermitian rc74 + linear-system rc95/rc96 + general-eig rc97), so the matrix-heavy DSP ops can finally flip. `esprit` (the ESPRIT rotational-invariance DOA/frequency estimator) is the first:

- Its three matrix steps route off the numpy-carrier `matrix_cascades` stack onto the **native Mat trio**: the Hermitian eigendecomposition → `mat_hermitian_eigendecompose`, the signal-subspace least-squares `Phi` → `mat_lstsq`, and the rotation-extraction eigenvalues → `mat_eigvals`. The signal-subspace column-select / shifted-subarray row-slices become plain `Mat.from_rows` over `mat[i, j]`; `np.argsort` becomes a pure-Python `sorted(range, key=…, reverse=True)`. The top-level `import numpy as np` is **gone**, so esprit runs with numpy genuinely absent (a runnable flip riding the native foundation, not the load-only rc70 trap). `op` now returns a `list[complex]` (was an ndarray).
- **Differential-verified value-faithful** to the numpy-present reference: clean single-tone DOA recovery within 1e-3, and the trace/determinant invariants of the recovered rotation spectrum match. The two `eigs.shape == (1,)` smoke tests move to `len(eigs) == 1`; esprit graduates out of the rc63 "cascade-routed" check (it's now numpy-free, a strictly stronger guarantee).

`CEIL_NUMPY_CARRIER` 32 → 31 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **289**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc97] - 2026-06-11

**Mat-return foundation #3 — `mat_eigvals`, numpy-free general (non-Hermitian) eigenvalues over the Mat carrier.** Carrier-removal #564. `mat_hermitian_eigendecompose` (rc74) + `mat_solve` (rc95) + `mat_lstsq` (rc96) cover the Hermitian + linear-system cases; this closes the **general non-Hermitian** eigenproblem so esprit's general-eig route can flip off the numpy-carrier `matrix_cascades` stack. New public `amsc.laplacian.mat_eigvals(a: Mat) -> list[complex]`:

- Computes the eigenvalue **multiset** of a general square `Mat` via a **Wilkinson-shifted QR iteration** — Class K (iterate-to-convergence) ∘ Class L (the spectral content) ∘ Householder QR ∘ Class C (the complex Wilkinson shift) — running in plain `complex` lists with the `RQ` recombination routed through the **native `mat_matmul`**, so it is unconditionally numpy-free. Small sizes take a closed form (`n=1` scalar; trailing-`2×2` block via the quadratic over the Class-N `_complex_sqrt`). The iteration is complex throughout, so it converges to the complex eigenvalues of a real matrix directly (e.g. a rotation block yields `±i`).
- **Differential-verified value-faithful to NumPy `eigvals`** to machine eps (~5e-14, *multiset* / nearest-neighbour distance — eigenvalues are unique only as a set) across real-symmetric, real non-symmetric with complex-conjugate pairs, complex, upper-triangular and defective (Jordan-block) inputs. For a Hermitian `A` prefer `mat_hermitian_eigendecompose` (exact Jacobi). `mat_eigvals` matches the shipped numpy-carrier `matrix_cascades.eigvals` bit-for-bit (same Wilkinson-shifted-QR).

**New public op** → `describe()["tools"]["total"]` **288 → 289** (`classes` stays 2); ToolEntry + rosetta `composition_of_c` bucket + `__all__`/`LAPLACIAN_OPS` added; `CEIL_NUMPY_CARRIER` unchanged at **32**; ABI 3; no C change. Next: route esprit through the three `mat_*` ops (`hermitian_eigendecompose`→`mat_hermitian_eigendecompose`, `lstsq`→`mat_lstsq`, `eigvals`→`mat_eigvals`).

## [0.7.5rc96] - 2026-06-11

**Mat-return foundation #2 — `mat_lstsq`, numpy-free least-squares over the Mat carrier.** Carrier-removal #564, the second foundation op unblocking the matrix-heavy DSP carrier-flips. New public `amsc.laplacian.mat_lstsq(a: Mat, b: Mat) -> Mat`:

- Solves the overdetermined / square (`m ≥ n`, full column rank) least-squares `A·X ≈ B` as the **normal equations** `X = (Aᴴ·A)⁻¹·Aᴴ·B`, composed entirely from the native `mat_*` trio: `mat_solve(mat_matmul(Aᴴ, A), mat_matmul(Aᴴ, B))` with `Aᴴ = A.conj().T`. Fully numpy-free for **real and complex** `A` (rc95 made `mat_solve` complex-capable). The result is complex iff `A` is.
- Differential-verified value-faithful to `numpy.linalg.lstsq` to ~1e-13 (real + complex) for well-conditioned `A`; `m < n` raises `ValueError`. The normal equations square the condition number — fine for the orthonormal signal-subspace projections esprit/the matrix-heavy DSP ops feed it.
- Also corrects the `mat_solve` ToolEntry summary (it still said "Real-f64 only" after the rc95 complex support).

**New public op** → `describe()["tools"]["total"]` **287 → 288** (`classes` stays 2); ToolEntry + rosetta `composition_of_c` bucket + `__all__`/`LAPLACIAN_OPS` added; `CEIL_NUMPY_CARRIER` unchanged at **32**; ABI 3; no C change. Next: `mat_eigvals` (Mat-carrier shifted-QR), then route esprit through the three `mat_*` ops.

## [0.7.5rc95] - 2026-06-11

**Mat-return foundation — `mat_solve` now handles COMPLEX (numpy-free), unblocking the matrix-heavy DSP carrier-flips.** Carrier-removal #564. The matrix-heavy `signal_processing` ops (esprit, dct, fsk, ica_jade, lmmse, map_ml, mimo_svd, music, psk_qam, vector_quantisation) can't be flipped numpy-free as leaves because they receive numpy arrays from `hermitian_eigendecompose` / `matrix_cascades.lstsq` / `matrix_cascades.eigvals` (all numpy-carrier-internal). The genuinely numpy-free path is the **native `mat_*` bridge** (rc72–74). This rc closes the first gap:

- `amsc.laplacian.mat_solve` previously **raised** `NotImplementedError` on a complex `Mat`. It now routes complex inputs through the new private `_mat_solve_complex`, which builds the real **2n×2n block embedding** `[[Aᵣ,−Aᵢ],[Aᵢ,Aᵣ]]·[u;v] = [bᵣ;bᵢ]` from plain `Mat` indexing (no numpy) and rides the shipped **native real** `mat_solve` — so `X = u + iv` is computed with numpy genuinely absent. This is the `Mat`-carrier peer of the existing numpy-carrier `_dense_solve_complex`.
- Differential-verified **value-faithful to ~1e-16** (machine eps) vs `numpy.linalg.solve` for well-conditioned `A` (the signal-subspace projections the DSP ops feed it). The rc73 `test_mat_solve_complex_rejected` flips to `test_mat_solve_complex_via_block_embedding` (asserts the solve + residual).

No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**; `mat_solve` was already a public op — this enhances it); `CEIL_NUMPY_CARRIER` unchanged at **32** (foundation-op enhancement, not a carrier flip); ABI 3; no C change. Next: `mat_lstsq` (normal-equations via `mat_solve`∘`mat_matmul`) + `mat_eigvals` (Mat-carrier shifted-QR), then route esprit.

## [0.7.5rc94] - 2026-06-11

**Carrier-flip batch #18 — `path_b_ops/sign_quantise` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 33 → 32).** Carrier-removal #564. The Path-B sign-quantise (Class K pin-slot threshold ∘ Class M dispatch tag; Spike #174 sign-quantise BER anchor) drops its top-level `import numpy`:

- It was a **pure carrier** — `np.asarray`/`np.zeros_like`/`np.where` with no helper dependencies, and the `np.where` **is** the Class-K decision. The flip coerces the signal to a `list` of `float` and makes the decision an explicit per-element sign-branch (no `abs()`): `v >= threshold → +1 else -1`, with the optional dead-band as a three-level `+1`/`-1`/`0` branch.
- `op` now returns a `list` of `int` `{-1, 0, +1}` (was an `int8` ndarray). The Spike #174 `path_b_mvp` BER test already wraps the dispatch result in `np.asarray(..., dtype=np.int8)` before `.tobytes()`/`.astype()`, so it is robust to the list return.

**Differential-verified BIT-EXACT** (a pure sign decision; identical `{-1,0,+1}` to the old `np.where`). Full local suite green.

`CEIL_NUMPY_CARRIER` 33 → 32 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc93] - 2026-06-11

**Carrier-flip batch #17 — `sinc_interp` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 34 → 33).** Carrier-removal #564. `closed_form_ops/sinc_interp` (Class L band-limit eigenbasis ∘ Class K pin-slot threshold; Whittaker-Shannon, Oppenheim & Schafer §4.1) drops its top-level `import numpy`:

- The sinc kernel reuses the rc92 substrate-native **`_sinc(x) = sin(πx)/(πx)`** (`rational.sin` over the Class-N **`_PI`** cascade; the `x = 0` removable singularity is a **Class-K branch** returning `1.0`, no division, no `abs()`) plus a pure-Python `_median` of the consecutive sample-spacing differences (was `np.median(np.diff(...))`).
- The complex Whittaker-Shannon matvec `out[q] = Σ_s sinc((t_q−t_s)/T)·y[s]` is an **inline nested sum** over plain `list`s — **not** `dense_matvec_complex` (which is numpy-carrier **internally**, the rc70 "runnable ≠ loadable" trap; it was also a matmul-ledger site, but the math ratchet asserts `total <= ceil`, so removing it stays green).
- `op` now returns a `list` of `complex` (or a single `complex` for a scalar `target_indices`), preserving the old scalar-vs-array return shape.

**Differential-verified value-faithful to maxerr 1.1e-16** (the rational `sinc` matches libm to ≤1 ULP; the integer-grid + scalar-target paths are bit-exact 0.0) — well within the op's tolerance. The baseline smoke moves `.shape` → `isinstance`/`len`.

`CEIL_NUMPY_CARRIER` 34 → 33 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc92] - 2026-06-11

**Carrier-flip batch #16 — `multirate` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 35 → 34).** Carrier-removal #564. `closed_form_ops/multirate` (Class N rational rate-conversion `up/down` ∘ Class C cyclic streaming; Vaidyanathan 1993 §4) drops its top-level `import numpy`:

- The default windowed-sinc low-pass taps are built with a substrate-native **`_sinc(x) = sin(πx)/(πx)`** (`rational.sin` over the Class-N **`_PI`** cascade) and a numpy-free **`_ccos`** Hamming window. The `x = 0` removable singularity of `_sinc` is a **Class-K branch** (returns `1.0`, **no division**, never an `abs()`), matching `np.sinc(0) = 1`.
- `np.arange` → `range`/list-comp; `np.zeros` → `[0.0]*n`; `np.pi` → `_PI`; `np.sum` → builtin `sum`; the up-sample zero-insert is a plain index loop; `_dsp.convolve` already returns a `list` (rc79); the down-sample is a `[::down]` slice scaled by `up`. `op` now returns a `list` of `float` (was an ndarray).
- Differential-verified **value-faithful to maxerr 7.1e-15** (the rational `sinc`/`cos` cascades match libm to ≤1 ULP; the `up==down==1` identity path is bit-exact 0.0) — well within the op's tolerance. The rc33 `_ccos` Hamming test moves off ndarray-broadcast to a list-comp (`isinstance`/`len`); the baseline smoke moves `.ndim` → `isinstance(list)`.

`CEIL_NUMPY_CARRIER` 35 → 34 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc91] - 2026-06-11

**Carrier-flip batch #15 — `multitaper` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 36 → 35).** Carrier-removal #564. `closed_form_ops/multitaper` (Class L DPSS eigenbasis ∘ Class M tapered-periodogram bundle-average; Thomson 1982) drops its top-level `import numpy`:

- `scipy.signal.windows.dpss` is an **external accelerator** (it needs numpy), so it stays a **lazy** import inside the `try`. numpy-absent it raises `ImportError` and the op falls through to the fully numpy-free cosine-taper fallback — whose tapers use the **Class-N π cascade** (`_PI`) fed to `rational.sin` via `_csin`, ℓ²-normalised by the inline `rational.sqrt(Σvᵢ²)` (the old `dense_norm` helper is numpy-carrier **internally**, so it cannot be called numpy-free).
- The per-taper periodogram `|F|² = real²+imag²` (no `abs()`) and the bundle average are explicit elementwise list comprehensions; `_sc.fft` returns `List[complex]`. `op` now returns a `list` of `float` (was an ndarray).
- Differential-verified **bit-exact (maxerr 0.0)** on the scipy-dpss path (the primary path locally); the fallback path runs numpy-free returning non-negative floats. The rc60 `np.linalg.norm`-absence ratchet + rc61 routed assertion stay green; the 3 op-smoke `.shape` asserts (rc33 ×2 + baseline) move to `isinstance`/`len`.

`CEIL_NUMPY_CARRIER` 36 → 35 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc90] - 2026-06-11

**Carrier-flip batch #14 — `spectral_subtraction` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 37 → 36).** Carrier-removal #564 — the **first flip whose numpy-free output is not bit-exact-0.0** (it is value-faithful to machine eps). `closed_form_ops/spectral_subtraction` (Class L FFT-domain PSD ∘ Class N rational floor; Boll 1979) drops its top-level `import numpy`:

- The signal/noise coerce to `list`s of `float`; the `np.maximum(|X|²−αN, βN)` Class-N floor becomes the builtin **`max`** per bin; `|z|² = real²+imag²` (no `abs()`).
- `np.angle(X)` (libm `atan2`) routes through **`rational.atan2`** (bit-exact to libm here). The phasor + magnitude — previously the numpy-CARRIER helpers `elementwise_transcendental(phase, "exp_i")` + `elementwise_sqrt` (both use `np.zeros`/`reshape` **internally** — the rc70 "runnable ≠ loadable" trap) — are inlined per-bin as `rational.{sqrt,cos,sin}`, so the op runs with numpy **absent**.
- `_sc.fft`/`_sc.ifft` already return `List[complex]`. `op` now returns a `list` of `float` (was an ndarray). Differential-verified **value-faithful to maxerr 6.7e-16** (the rational cascades match libm `atan2`/`cos`/`sin` and `sqrt` to ≤1 ULP) — well within the op's `1e-9` tolerance. The baseline smoke moves `.shape` → `len`.

`CEIL_NUMPY_CARRIER` 37 → 36 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc89] - 2026-06-11

**Carrier-flip batch #13 — `stft` (+ its `spectrogram` consumer) go numpy-FREE (`CEIL_NUMPY_CARRIER` 38 → 37).** Carrier-removal #564, the seventh of the workflow-scoped batch and the second windowed follower of `cross_spectral` — reusing the rc88-codified **`_PI = float(pi_cascade_digits(30))`** (Class-N Archimedes hexagon-doubling) + `_ccos` → `rational.cos` π source. `closed_form_ops/stft` (Class C ∘ A ∘ I ∘ K windowed-frame FFT) drops its top-level `import numpy`:

- The signal coerces to a `list` of `complex` (a `hasattr(seq[0], "__len__")` guard preserves the old 1-D `ValueError`); the default Hann window `0.5·(1 − cos(2π·n/(N−1)))` is the same `_PI`-formed `_ccos` cascade; per-frame `signal·window` + `_sc.fft` build a **list-of-lists** STFT matrix (no `np.zeros` stack).
- `op` now returns a `list` of per-frame `list`s (was a complex128 ndarray). `spectrogram` (already top-level-numpy-free since rc70) consumes the list-of-lists and computes `|z|² = real²+imag²` (no `abs()`) elementwise, returning a `list` of `list`s of `float`.
- The rc33 window/op trig-routing tests + the baseline `stft`/`spectrogram` smoke tests move `.ndim`/`.shape` → `isinstance`/`len`; differential-verified bit-exact (maxerr 0.0) against the pre-change numpy path.

`CEIL_NUMPY_CARRIER` 38 → 37 (down-only ratchet; only `stft` carried a top-level import, so the count drops by one). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc88] - 2026-06-10

**Carrier-flip batch #12 — `cross_spectral` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 39 → 38).** Carrier-removal #564, the sixth of the workflow-scoped batch — and the **first sigproc carrier-flip to need π** (a *moderate* flip). `closed_form_ops/cross_spectral` (Class M HDC bundle-average ∘ Class A FFT cross-product; Welch's method) drops its top-level `import numpy`:

- The Hann window `0.5·(1 − cos(2π·n/(N−1)))` uses a module-level **`_PI = float(pi_cascade_digits(30))`** (Class-N Archimedes hexagon-doubling cascade — already the numpy-free π source in `exact_dft`/`spectral_cascades`) fed to `rational.cos`.
- The cross-product `X·conj(Y)`, the per-bin power `|z|² = real²+imag²` (no `abs()`), and the `np.maximum(..., 1e-30)` coherence floor (builtin `max`) become explicit elementwise list comprehensions. `_sc.fft` returns `List[complex]`; `_fc.fftfreq` returns a plain list numpy-absent.
- `op` now returns `(list, list)` (was two ndarrays). The baseline smoke moves `.shape` → `len`; the rc61 coherence test already wraps `coh` in `np.asarray` (resilient).

`CEIL_NUMPY_CARRIER` 39 → 38 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc87] - 2026-06-10

**Carrier-flip batch #11 — `wiener` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 40 → 39).** Carrier-removal #564, the fifth of the workflow-scoped batch and a clean leaf. `closed_form_ops/wiener` (Class L power-spectrum Laplacian eigenbasis ∘ Class N rational MMSE gain) drops its top-level `import numpy`:

- `_sc.fft`/`_sc.ifft` already return `List[complex]`; the `np.asarray`/`np.real` wraps drop. The per-bin power `|X|² = X.real² + X.imag²` (no `abs()`), the Class-N rational gain `H_W(k) = S_xx/(S_xx+S_nn)`, and the IFFT-then-real-part are explicit elementwise list comprehensions.
- The two `np.maximum(..., 1e-30)` ε-floors become the builtin **`max(x, 1e-30)`** per bin.
- `op` now returns a `list` of `float` (was float64 ndarray). The baseline + rc61 smoke tests move `.shape` → `len`; the rc61 finite/real checks pass on the list.

`CEIL_NUMPY_CARRIER` 40 → 39 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc86] - 2026-06-10

**Carrier-flip batch #10 — `beamforming_fixed` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 41 → 40).** Carrier-removal #564, the fourth of the workflow-scoped batch and a clean leaf. `closed_form_ops/beamforming_fixed` (Class L microphone-array combiner ∘ Class N rational delay coefficients; trauma-informed civilian-acoustics scope) drops its top-level `import numpy`:

- `array_signals` coerces to a `list`-of-`list` of `complex` (`np.complex128`/`np.full`/`np.zeros`/`np.int64` → `complex()`/plain lists/`int()`); a `hasattr(row, "__len__")` guard preserves the old 2-D `ValueError`.
- `max_delay = int(np.max(d))` → the builtin **`max(d)`** (Class-L reduce, no `abs()`); the per-mic delay-and-sum `out += w[m] * sig[m, delay:delay+out_len]` becomes an explicit **Class-M scale-and-accumulate** index loop `out[i] += w[m]*row[delay+i]`.
- `op` now returns a `list` of `complex` (was complex128 ndarray; empty result is `[]`). The smoke test moves `y.ndim == 1`/`y.shape[0]` → `isinstance(y, list)`/`len(y)`.

`CEIL_NUMPY_CARRIER` 41 → 40 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc85] - 2026-06-10

**Carrier-flip batch #9 — `polyphase` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 42 → 41).** Carrier-removal #564, the third of the workflow-scoped batch and a clean leaf (same shape as fir/matched_filter rc80). `closed_form_ops/polyphase` (Class L subband Laplacian ∘ Class N rational FIR decomposition) drops its top-level `import numpy`:

- Its only delegate is the already-numpy-free `_dsp.convolve` (returns `List[float]`); the `np.asarray(...)` wrap around it drops.
- The strided polyphase split `E_k[n] = h[k+n·L]` and the interpolation interleave are native list `[::L]` slices; the per-component accumulate (`out[:n] += filtered`) and the strided interleave write (`out[k::L][:m] = c`) become explicit **Class-M elementwise index loops**. `np.zeros`/`np.concatenate`/`np.array([])` → plain lists.
- `decompose` now returns a `list` of `list` (was list-of-ndarray); `op` returns a `list` (was ndarray). The smoke test moves `y.ndim == 1` → `isinstance(y, list)`.

`CEIL_NUMPY_CARRIER` 42 → 41 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc84] - 2026-06-10

**Carrier-flip batch #8 — `ofdm` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 43 → 42).** Carrier-removal #564, the second of the workflow-scoped batch. `closed_form_ops/ofdm` (Class I IFFT ∘ Class L per-subcarrier equaliser ∘ Class K cyclic-prefix) drops its top-level `import numpy`:

- The **modulate** path returns a 1-D `list`: the `np.zeros(...)` baseband buffer becomes `[complex(0)] * N`, the cyclic-prefix `np.concatenate([prefix, time_block])` becomes a `prefix + time_block` list concat, and the per-OFDM-symbol write becomes a list slice-assign. `_sc.ifft` already returns `List[complex]`.
- The **demodulate** path returns a **list-of-lists** (one row per OFDM symbol). The Class-L one-tap equaliser inlines the numpy-bound `laplacian.elementwise_hypot` via the numpy-free Class-N `rational.hypot` in a per-subcarrier comprehension, and the `np.where(|H_k| > 1e-12, H_k, 1.0)` guard becomes an explicit **Class-K pin-slot sign-branch** (`> 1e-12 → H_k else 1.0`; no `abs()`). `_sc.fft` already returns `List[complex]`.
- Smoke tests move `.shape`/`.reshape` → `len`/list-flatten at the test boundary (baseline `test_ofdm_smoke` + rc61-routing `test_ofdm_round_trip_value_faithful`). The rc61 `np.fft.` residual-callsite assertion still passes (ofdm uses `_sc.fft`/`_sc.ifft`).

`CEIL_NUMPY_CARRIER` 43 → 42 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc83] - 2026-06-10

**Carrier-flip batch #7 — `viterbi` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 44 → 43).** Carrier-removal #564, the first of the workflow-scoped batch (a `carrier-flip-scoping` multi-agent run classified the remaining signal_processing carrier files: 8 flippable-now, 16 blocked behind `dense_*`/`np.linalg`/`np.fft`). `closed_form_ops/viterbi` (Class L trellis-graph Laplacian ∘ Class K argmax pin-slot) drops its top-level `import numpy`:

- The 2-D trellis tables `delta` / `psi` become **list-of-lists** (`[[float('-inf')] * n_states for _ in range(T)]`); the branch metrics `delta[t-1] + A[:, s]` become an explicit **Class-M multiply-add list comprehension** over the transition column; and the two `np.argmax` merge points are the **Class-K pin-slot** as Python `max(range(n_states), key=lambda i: scores[i])` — first-maximal tie-break, matching `np.argmax`. Self-contained: no scipy, no helper delegation.
- `viterbi.op` now returns a `list` of `int` (was an int64 ndarray). The smoke test moves `path.shape == (5,)` → `len(path) == 5`. Value-faithful (same DP, same tie-break).

`CEIL_NUMPY_CARRIER` 44 → 43 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc82] - 2026-06-10

**Carrier-flip batch #6 — `iir` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 45 → 44).** Carrier-removal #564, the same shape as the rc77 `allpass` flip. `closed_form_ops/iir` (Class N rational `b/a` ∘ Class C recursive biquad cascade) drops its top-level `import numpy`:

- The optional **scipy accelerator stays lazy** (`scipy.signal.lfilter` / `sosfilt`); scipy needs numpy, so a numpy-absent install falls through to the pure-Python path. The scipy branch now passes the `list` inputs straight to `lfilter`/`sosfilt` (scipy coerces) and wraps the result in `list(...)` so the return type matches the fallback.
- The no-scipy path is the **direct-form-II transposed difference equation** (`_lfilter_direct`) — the Class-C recursive cascade of the Class-N `b/a` rational — now running on plain Python `list`s (explicit multiply-add accumulation of `y[i]` and the state `z`; coefficient normalisation by `a[0]` as a list comprehension). The biquad-cascade branch chains sections on lists.
- `iir.op` now returns a `list` (was ndarray). The smoke test moves `.shape == (16,)` → `len(...) == 16`. Value-faithful (same difference equation).

`CEIL_NUMPY_CARRIER` 45 → 44 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc81] - 2026-06-10

**Carrier-flip batch #5 — `wavelet` (Haar DWT) goes numpy-FREE (`CEIL_NUMPY_CARRIER` 46 → 45).** Carrier-removal #564. `closed_form_ops/wavelet` (Class L multi-scale 2-point Laplacian ∘ Class N dyadic 2^k scaling) drops its top-level `import numpy`:

- Its only numpy was `np.asarray` / `np.zeros` carriers — the `1/√2` normaliser was already the libm-free Class-N `rational.sqrt`. The op now runs on a plain Python `list`: each level is an explicit **elementwise Class-L 2-point band** (`approx = [(e+o)/√2]`, `detail = [(e-o)/√2]` over `zip(evens, odds)`) on the **Class-N dyadic decimation** (`current[0::2]` / `current[1::2]`), with a one-zero pad for odd lengths. Value-faithful (same `rational.sqrt` constant, same float64 arithmetic).
- Returns `(approx, [detail_level_k, …])` as `list`s (was ndarrays). **Zero test ripple** — the smoke test already asserts `isinstance(details, list)` + `len(details) == 2`, both unchanged.

`CEIL_NUMPY_CARRIER` 46 → 45 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc80] - 2026-06-10

**Carrier-flip batch #4 — `fir` + `matched_filter` go numpy-FREE (`CEIL_NUMPY_CARRIER` 48 → 46).** Carrier-removal #564, the follow-on rc79 unblocked: now that `_dsp_cascades` is numpy-free, the two convolution/correlation leaf ops flip trivially. Both `closed_form_ops/fir` (Class N ∘ Class C) and `closed_form_ops/matched_filter` (Class A ∘ Class C ∘ Class M) drop their top-level `import numpy`:

- Each had only one remaining numpy use — the `np.asarray(...)` return-wrap added at rc79 plus the `np.asarray` + `.ndim` input guard. Both now **delegate straight to the numpy-free `_dsp.convolve` / `_dsp.correlate`**, which coerce both inputs to 1-D lists (raising `ValueError` on a nested/2-D or empty input — same exception type as the prior `.ndim` guard) and return a `list`. No numpy anywhere in the op.
- `fir.op` / `matched_filter.op` now return a `list`. The two smoke tests move `.shape == (N,)` → `len(...) == N`. Value-faithful (same `_dsp` cascade).

`CEIL_NUMPY_CARRIER` 48 → 46 (down-only ratchet, two files). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc79] - 2026-06-10

**Carrier-flip batch #3 — the DSP convolution foundation `_dsp_cascades` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 49 → 48).** Carrier-removal #564. `signal_processing/_dsp_cascades` (the internal `convolve` / `correlate` Class I ∘ Class M cascade) was already numpy-free as a *math engine* (rc58) but still used numpy as a **carrier** (`np.ascontiguousarray` / `np.zeros` / `np.conj` / `np.result_type`). It now runs with **no numpy at all**:

- The output buffer is a plain Python `list` (`[0] * N`, which promotes int → float → complex exactly as the element arithmetic dictates — so an all-integer convolution stays integer, matching numpy's `result_type`); the Class-I shift is a list slice; the conjugate is the element's own `.conjugate()` (Python `int` / `float` / `complex` all provide it). Accumulation order (i outer, j inner) is unchanged, so floats stay **bit-faithful** to the prior numpy-carrier path (`test_dsp_convolution_cascade_rc58.py` still passes).
- `convolve` / `correlate` now return a `list`. The **5 consumer callsites** — `closed_form_ops/{fir, matched_filter, multirate, polyphase}` + `path_b_ops/matched_filter` — wrap the result in `np.asarray(...)` at their own (still numpy-importing) boundary, preserving their exact ndarray return/behaviour (e.g. `multirate`'s `filtered[::down] * up` strided-scale, `polyphase`'s `.shape` accumulate). Zero value change. This unblocks `fir` + `matched_filter` to flip in a later rc (their only remaining numpy is the `np.asarray` carrier).

`CEIL_NUMPY_CARRIER` 49 → 48 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc78] - 2026-06-10

**Carrier-flip batch #2 — `signal_processing` `farrow` goes numpy-FREE (`CEIL_NUMPY_CARRIER` 50 → 49).** Carrier-removal #564, continuing the pure carrier-flip phase. `closed_form_ops/farrow` (Class N — cubic-Lagrange fractional-delay Farrow structure) drops its top-level `import numpy`:

- The 4-tap Lagrange sub-filter `_FARROW_LAGRANGE_CUBIC` becomes a **plain-tuple constant table** of exact-rational floats (was an `np.array`), and each per-output-sample `C[k]·x` mixer term becomes an **explicit length-4 Class-M micro-reduction** (`c[0]·x[0] + … + c[3]·x[3]`, left-to-right). At rc26 this dot was *routed onto* `dense_dot_real` to retire a numpy matmul site — but `dense_dot_real` feeds numpy carriers (`np.ascontiguousarray` + `np.sum`) into the native kernel, so a farrow that called it could not run numpy-absent. Inlining the four-term dot is **bit-faithful** (same IEEE-754 multiply-adds, same order) and adds **no** numpy matmul site, so the math ratchet stays floored.
- Carriers become plain lists (`padded = [0.0] + sig + [0.0, 0.0]`; `out` accumulates by `append`); the op now returns `list[float]`. The smoke test moves from `.shape == (16,)` to `len(...) == 16`. `CEIL_NUMPY_CARRIER` 50 → 49 (down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc77] - 2026-06-10

**Carrier-flip batch #1 — `signal_processing` `allpass` + `sign_quantise` go numpy-FREE (`CEIL_NUMPY_CARRIER` 52 → 50).** Carrier-removal #564, the first of the pure carrier-flip phase (the dissolution track closed at rc76 — `hurwitz_matrix` was the only float-restatement-of-an-exact-op; a full re-review confirmed zero further dissolutions). The numpy-MATH sweep already cascade-routed these ops; what remained was numpy as a **carrier**. Both modules drop their top-level `import numpy`:

- **`closed_form_ops/sign_quantise`** (Class K) — the `np.where` sign-quantiser becomes an explicit per-element **Class-K threshold sign-branch** over a plain Python list (no `abs()`); returns `list[int]` of `{-1, 0, +1}`. Exact integer comparisons — value-identical to the numpy logic.
- **`closed_form_ops/allpass`** (Class N) — carriers become plain lists; the optional scipy `lfilter` accelerator is lazy (scipy needs numpy, so a numpy-absent install falls through) and its result is coerced to a list; the no-scipy path is the existing **direct-form-I difference-equation reference** running on lists. Returns `list[float]`.
- The two smoke tests move from `.shape == (N,)` to `len(...) == N` (the numpy-free list carrier), with `sign_quantise` pinned to its exact `{-1,0,+1}` output. `CEIL_NUMPY_CARRIER` 52 → 50 (the down-only ratchet). No new public op (`describe()["tools"]["total"]` stays **287**, `classes` **2**); ABI 3; no C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc76] - 2026-06-10

**The scalar-export layer — `One.to_scalar`: matrix/vector → scalar, EXACT by default, opt-in numpy-free float export.** Carrier-removal #564, the follow-on to the rc75 Hurwitz TOML-class reframe (so a TOML class can chain matrix-math → scalar output). The user's rule (2026-06-10): *return float sometimes, never receive float*. `One.to_scalar(mode='trace'|'sqnorm'|'component', index=None, *, as_float=False)` (plus the bindable module-level `srmech.amsc.cascade.to_scalar`) is the scalar member of the One's projection family — the scalar peer of `to_flat_rational`.

- **Never *receive* float.** Inputs stay exact integers — `the_one(σ, θ_num, θ_den)` is integer-only (float `θ` raises). There is no float-accepting lift; the exact scalar→matrix lift is already `the_one` itself.
- **Return float *sometimes*.** The default is the exact reduced `(num, den)` Class-N rational (the math path). `as_float=True` does the single terminal `num/den` cast to a **plain Python `float` — NO numpy**. Pointedly *unlike* `One.to_numpy` / `One.to_matrix` (the numpy `[scientific]`-tier exports #564 is retiring), this float export needs no numpy at all; one boundary cast ≠ error summation.
- **Three exact modes (`mode=`).** `trace` → `Tr G(σ,θ) = 3 + 3σ + 8σ·cos θ` (the rotation character, the 0/1/3-plane diagonal of `One.to_matrix`); `sqnorm` → `Σ (num/den)²` over the 14 state rationals (sign-free, no `abs`/`sqrt`); `component` → the `index`-th of the 14 exact rationals. **`trace` consumes the same Class-N `rational.cos_series_truncate` the `trigonometry` / `asymptotic_calculus` catalogs validate** — those catalogs are this scalar's *target test* (no forked trig path; their 59 tests stay green).
- New public callable ⟹ rosetta `bignum_reference` (the exact-rational oracle tier, outside the debt ceilings) + `__all__`. It takes a structured `One` (no MCP-JSON coercer) so it is **not** an MCP tool — tool-schema-coverage exemption, like `the_one` / `greedy_bipartite_alignment`; bindable for TOML classes by dotted path (`op = "srmech.amsc.cascade.to_scalar"`). `describe()["tools"]["total"]` stays **287**, `classes` stays **2**; `CEIL_NUMPY_CARRIER` stays **52**. ABI 3; no C change. New `test_to_scalar_rc76.py` (15 tests). Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc75] - 2026-06-10

**The numpy-Rosetta-peer dissolution — `qm.hurwitz.hurwitz_matrix` deleted; the Hurwitz operator is now a `[class]` over the EXACT `the_one`; FIRST carrier-ceiling decrement (`CEIL_NUMPY_CARRIER` 53 → 52).** Carrier-removal #564. rc50 shipped `qm.hurwitz.hurwitz_matrix`, a numpy `14×14` **float** builder (`np.zeros` + `cos`/`sin` float-divided) that DUPLICATED `srmech.amsc.cascade.One.to_matrix` — both float-cast the SAME exact cascade `the_one`. There was never supposed to be a continuous-float Rosetta-peer: chained float ops SUM rounding error at every operation and are not correct-for-science. The EXACT realisation (the `One` object's 14 exact `(num, den)` rationals) is the correct one; the float matrix is a lossy projection, legitimate only as an opt-in export, never as a separately-named math op.

- **The Hurwitz operator is now declared the class-from-TOML way** (`srmech.dsl.make_class`, the genome-update mechanism). New `srmech/amsc/_research/class_catalog/hurwitz.toml` declares a `Hurwitz` `[class]` whose method `generate` BINDS `op = "srmech.amsc.cascade.the_one"` — the exact, numpy-free generator. `make_class("Hurwitz")().generate(sigma=1, theta_num=1, theta_den=4, terms=24)` returns the EXACT `One`, bit-for-bit identical (`to_flat_rational()`) to `the_one(1, 1, 4, terms=24)` — zero user Python, no numpy, no error summation. "Same operation, different name" → the TOML-class way (`[[project_srmech_class_from_toml_user_targeting_model]]`).
- **`qm/hurwitz.py` is now numpy-free at the top level** (no `import numpy`; no `cos_series`/`sin_series` import) → **`CEIL_NUMPY_CARRIER` 53 → 52**, the FIRST carrier-ceiling decrement of the carrier-removal arc (rc69–rc74 built the Mat bridge; rc75 flips the first module). What survives in `qm.hurwitz` is `hurwitz_planes` — the GENUINE cross-derivation of the oriented Fano planes from `octonion_mult_table` (an exact integer-tuple structure, not a float restatement; matches `One.FANO_PLANES` bit-for-bit). Its full numpy-free reachability follows when `qm.octonion` flips (the octonion table is still numpy until then).
- New `[class]` ⟹ `describe()["classes"]["total"]` **1 → 2** (`Hurwitz` joins `Genome`). The deleted `hurwitz_matrix` ToolEntry + its rosetta `composition_of_c` line are removed ⟹ `describe()["tools"]["total"]` **288 → 287** (7 count-tests). The float `14×14` stays as the opt-in lossy `One.to_matrix` (the `[scientific]` export), never a named op. `test_hurwitz_rc50.py` rewritten: pins the class-IS-the-exact-the_one identity, the dissolution (`not hasattr(h, "hurwitz_matrix")`), and the surviving plane cross-derivation. ABI 3. No C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin.

## [0.7.5rc74] - 2026-06-10

**The Mat bridge primitive #3 (the LAST) — numpy-FREE Hermitian eigendecomposition (`mat_hermitian_eigendecompose`).** Carrier-removal #564, completing the family with rc72's `mat_matmul` and rc73's `mat_solve`. `laplacian.mat_hermitian_eigendecompose(H: Mat) -> (eigvals, eigvecs)` diagonalises `H = V·diag(λ)·Vᴴ` over the numpy-free 2-D `Mat` carrier with **NO numpy**: the real/complex `Mat.buffer` (interleaved-`(re, im)` row-major) feeds the native `srmech_hermitian_eigendecompose(n, H_il, out_eigvals, out_eigvecs_il)` **zero-copy** (a complex `Mat`) or interleaved-`(re, 0)` once (a real `Mat`); `eigvals` returns as an `(n, 1)` **real** `Mat` (ascending) and `eigvecs` as an `(n, n)` **complex** unitary `Mat` (always complex, mirroring `hermitian_eigendecompose`).

- **Unconditionally numpy-free.** With no native lib — or `n` > `MAX_NATIVE_NODES` (256), or a native convergence miss — the fallback is srmech's own pure-Python **cyclic Jacobi** (`_jacobi_eig_py`, the eigenvector-accumulating sibling of `_jacobi_eigvals_py`): a real-symmetric input diagonalises directly; a complex-Hermitian input is diagonalised through its real `2n×2n` symmetric embedding `[[A, -B], [B, A]]` (`H = A + iB`), the complex eigenvectors reconstructed `vⱼ = topⱼ + i·botⱼ` and same-eigenvalue Gram–Schmidt re-orthonormalised (pins a unitary basis inside a degenerate eigenspace). No `abs()`, no libm (off-diagonal magnitude is a sum of squares; the rotation sign is the explicit `tau ≥ 0` Class-K branch; roots via Class-N `rational.sqrt`).
- **Subprocess-proven** (numpy blocked at `sys.meta_path` before the first import): the op computes with numpy absent on both the native and the forced-embedding-fallback paths. Correctness is pinned by **eigenvalues + reconstruction (`H ≈ V·diag(λ)·Vᴴ`) + unitarity (`Vᴴ·V ≈ I`)**, NOT element-wise parity (an eigenvector is fixed only up to a phase; a degenerate eigenspace's basis is solver-chosen); eigenvalues match `numpy.linalg.eigvalsh` to ~1e-13 on both paths. New `test_mat_hermitian_eig_bridge_rc74.py` (8 tests) also pins the eigenvalue equation `H·v = λ·v`, a degenerate complex spectrum, non-square → `ValueError`, and the empty case.
- New public callable ⟹ `ToolEntry` + rosetta `c_dispatched` + `__all__`/`LAPLACIAN_OPS`; `describe()["tools"]["total"]` **287 → 288** (7 count-tests). The rc72 `Mat` MCP coercer + smoke sample already cover it (no MCP-ratchet change). All maths ratchets at floor; `CEIL_NUMPY_CARRIER` stays **53** (new numpy-free capability, not yet a module flip). ABI 3. No C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin. **The Mat↔native-dense-kernel bridge family (matmul + solve + eig) is now complete — a `qm.*` module's full numpy surface has Mat-native peers, so the first module flip can finally decrement the carrier ceiling.**

## [0.7.5rc73] - 2026-06-10

**The Mat bridge primitive #2 — numpy-FREE dense solve (`mat_solve`).** Carrier-removal #564, the peer of rc72's `mat_matmul`. `laplacian.mat_solve(A: Mat, B: Mat) -> Mat` solves `A·X = B` over the numpy-free 2-D `Mat` carrier with **NO numpy**: the real `Mat.buffer`s (row-major float64) feed the native `srmech_dense_solve_f64(n, nrhs, A, B, out)` **zero-copy** via `(c_double*n²).from_buffer(...)` (the C side takes them `const`, so the `Mat`s are not mutated), and the output `array('d')` wraps straight back into a `Mat`.

- **Unconditionally numpy-free.** With no native lib — or any dim > `MAX_NATIVE_NODES` (256), or the native path flagging singular — the fallback is srmech's own **exact-rational Gauss–Jordan** (`_solve_exact`, Class-N `Fraction` division, numpy-free) coerced to float64. `srmech_dense_solve_f64` is **real-f64 only**; a complex `Mat` raises `NotImplementedError` (the complex solve is the real `2n×2n` block embedding — a later rc).
- **Subprocess-proven** (numpy blocked at `sys.meta_path` before the first import): `mat_solve` computes with numpy absent on both the native and the forced-fallback paths; value-faithful to `numpy.linalg.solve` (~1e-15) when numpy is present. New `test_mat_solve_bridge_rc73.py` (8 tests) also pins singular → `ZeroDivisionError`, complex → `NotImplementedError`, and the `A·X = A → X = I` round-trip.
- New public callable ⟹ `ToolEntry` + rosetta `c_dispatched` + `__all__`/`LAPLACIAN_OPS`; `describe()["tools"]["total"]` **286 → 287** (7 count-tests). The rc72 `Mat` MCP coercer + smoke sample already cover it (no MCP-ratchet change). All maths ratchets at floor; `CEIL_NUMPY_CARRIER` stays **53** (new numpy-free capability, not yet a module flip). ABI 3. No C change. Version bumped at all 5 SSOT locations incl. the scaffolding pin. **rc74 = `mat_hermitian_eigendecompose` completes the bridge family; then a `qm.*` module's full numpy surface (matmul+solve+eig) has Mat-native peers and the first module flip can decrement the carrier ceiling.**

## [0.7.5rc72] - 2026-06-10

**The `Mat`↔native-dense-kernel bridge: numpy-FREE 2-D matmul (`mat_matmul`).** Carrier-removal foundation #2 (#564). rc69 built the numpy-free 2-D `Mat` carrier (flat `array('d')`, row-major, interleaved-`(re,im)` for complex = C99 `double _Complex`); rc71 made signal_processing import-reachable numpy-free. This rc adds the bridge the 2-D `qm.*` matmul callsites flip onto: `laplacian.mat_matmul(a: Mat, b: Mat) -> Mat` computes `A·B` with **NO numpy** on the dispatch path.

- **Zero-copy into the native kernel.** Because `Mat.buffer` is already the exact flat row-major interleaved-complex layout the C symbol reads, a complex operand feeds `srmech_dense_matmul_complex` **zero-copy** via `(c_double*2·n).from_buffer(mat.buffer)` (the C side treats it `const`); a real operand is interleaved `(re, 0)` once. The output is a fresh `array('d')` wrapped back into a `Mat` (complex iff either input is). This is the bridge half the rc69 `Mat` design was built for — and it follows the rc#563 numpy-free ctypes-marshalling precedent (the `srmech_jacobi_eigvals` list-marshal), so HAS_NATIVE is True with numpy genuinely absent.
- **Unconditionally numpy-free.** With no native lib — or any dim > `MAX_NATIVE_NODES` (256) — the fallback is a pure-Python triple loop over the `Mat` (a cascade, **never** numpy `@`). So `mat_matmul` is numpy-free on BOTH paths.
- **Honest, subprocess-proven.** `test_mat_matmul_bridge_rc72.py` (9 tests) pins value-correctness (the native complex kernel is **bit-exact vs numpy**, max-err 0.0) AND — in a subprocess that blocks numpy at `sys.meta_path` before the first import — that `mat_matmul` computes with numpy absent on the native path, the forced-fallback path, and the real path.
- New public callable ⟹ full registry treatment: `ToolEntry` + rosetta `c_dispatched` bucket + `__all__`/`LAPLACIAN_OPS`; `describe()["tools"]["total"]` **285 → 286**. MCP-invocable too — a `Mat` coercer (`srmech.mcp._coercion`, JSON list-of-rows → real `Mat`, mirroring `_to_ndarray`) so the every-tool-invocable ratchet stays green. All three maths ratchets at floor; `CEIL_NUMPY_CARRIER` stays **53** (the bridge is a new numpy-free capability, not yet a module flip). ABI 3. **rc73+ flips the `qm.*` matmul callsites onto `mat_matmul`, lowering the carrier ceiling; `mat_solve` / `mat_hermitian_eigendecompose` are the follow-on bridge rcs.**

## [0.7.5rc71] - 2026-06-10

**Lazy op-registration — `srmech.signal_processing` is now IMPORT-reachable numpy-FREE.** rc70 flipped the FFT op-family's *runtime math* numpy-free, but a fresh `import srmech.signal_processing` on a numpy-absent install still raised: two uncounted layers above the carrier ratchet. (1) An **eager `_require_numpy(...)` package gate** in `signal_processing/__init__` (the rc47 capstone), and (2) **eager all-op registration imports** — `from . import path_b_ops` → every op module imported for registry population → the numpy ops' `import numpy` fired transitively, even for the numpy-free FFT family. rc71 dissolves both, so the maths-engine-floored FFT family is finally **reachable**, not merely runnable, without numpy.

- **Op-registration is now LAZY.** `closed_form_ops` / `path_b_ops` replace their eager `from . import (…every op…)` with a PEP-562 module **`__getattr__`** (shared `srmech._scientific.make_lazy_op_getattr`) that defers each op-module import to first attribute access. The numpy-free Path-B ops (the FFT family — `fft`/`ifft`/`rfft`/`hdc_truncation`/`pi_cascade`) still import + self-register eagerly (numpy-free); the **numpy** Path-B ops (`matched_filter`/`sign_quantise`/`wiener`) register a deferred **loader** with the `path_registry` instead, so `lookup` / `has_path` / `dispatch` resolve them by importing-on-demand. A numpy `ModuleNotFoundError` is re-raised as the clean `[scientific]` hint at one chokepoint.
- **`path_registry.registered_ops()` is now declarative** — it lists the lazily-registrable numpy ops as *pending* (no numpy-pulling import forced) after the eagerly-loaded ops; `lookup`/`has_path` gained an `_ensure_loaded()` that runs the loader on first touch. The eager `__init__` `_require_numpy("srmech.signal_processing")` gate is **removed**.
- **Honest, subprocess-proven:** new `test_signal_processing_numpy_free_reachable_rc71.py` spawns a subprocess that blocks numpy at `sys.meta_path` *before the first import* (a real numpy-absent install, not in-process `monkeypatch` — which can't prove fresh-import-numpy-freedom because the module is already bound), then asserts `import srmech.signal_processing` succeeds, `closed_form_ops.fft.op([1,2,3,4])` + `dispatch("fft", …, path="A")` return a numpy-free list, `closed_form_ops.music` (a numpy op) raises the clean `[scientific]` hint, and `registered_ops()` lists `matched_filter`/`sign_quantise`/`wiener` declaratively. Plus a down-only static guard that the eager `_require_numpy()` gate stays gone.
- **No carrier flip ⟹ `CEIL_NUMPY_CARRIER` stays 53** (rc71 is a *reachability* fix, not a module flip — it removes the import-time numpy barrier above the already-flipped FFT family). No public-op change ⟹ `describe()["tools"]["total"]` stays **285**; all maths ratchets at floor. ABI 3. The 2-D `qm/*` matrix modules still need the `Mat`↔native-dense-kernel bridge (next foundation).

## [0.7.5rc70] - 2026-06-10

**Carrier-removal flip #1 — the FFT op-family runs 1-D numpy-FREE.** rc69 built the carrier ratchet + the `Mat` carrier; rc70 is the first real **module flip**, lowering `CEIL_NUMPY_CARRIER` **61 → 53**. `_fft_carrier`'s numpy was pure carrier-shaping (`asarray` / `moveaxis` / `reshape` / zero-pad / output-alloc) while the transform already rode the numpy-free 1-D `spectral_cascades`. Now the **common 1-D / default-axis** path is numpy-free (a stdlib list flows straight through the cascade and comes back a list — the framework-native carrier when numpy is absent, an `ndarray` for parity when present); only the **n-D / non-default-axis** case still uses numpy as a carrier, and it imports numpy **lazily**.

- **8 modules drop their top-level `import numpy`** (loadable AND 1-D-runnable numpy-free, not merely loadable): the leaf `_fft_carrier` + the pass-through wrappers `closed_form_ops.{fft,ifft,rfft}` (their redundant `np.asarray` removed — `_fc` already coerces) + `closed_form_ops.spectrogram` (its only numpy was an annotation-only import) + `path_b_ops.{fft,ifft,rfft}` (numpy-free length via the input's own `.shape`/`len`).
- **Honest, not theater:** a new `test_fft_family_numpy_absent_rc70.py` HIDES numpy (`sys.modules["numpy"]=None`) and proves `fft`/`ifft`/`rfft`/`fftfreq` + `n=` pad/truncate still compute, value-faithful (~1e-9) to the DFT oracle, returning the framework-native list. The values are identical on both paths because both ride the same `spectral_cascades` cascade — the existing bit-faithful FFT suite (788 tests) stays green.
- `CEIL_NUMPY_CARRIER` **61 → 53** (down-only carrier ratchet). No public-op change ⟹ `describe()["tools"]["total"]` stays **285**; all three maths ratchets unchanged at floor. ABI 3. The 2-D `qm/*` matrix modules come in a later rc behind a `Mat`↔native-dense-kernel bridge.

## [0.7.5rc69] - 2026-06-10

**Carrier-removal arc — Phase 0 (infra): the numpy-free 2-D `Mat` carrier + a down-only carrier ratchet.** The numpy-*math* sweep (rc53–rc68) drove the `linalg_fft` / `matmul` / `ufunc` ledgers to their floor — numpy is gone as a *math engine*. What remains is numpy as a **carrier** (array container / shaping): 61 submodules still `import numpy` at module level, so they can't load on a numpy-free install (the package itself already imports numpy-free; these are lazy submodule imports). This rc lays the foundation to delete that — **no module is flipped yet**.

- **New `srmech.amsc.mat.Mat`** — the 2-D peer of the `HV` carrier (rc29). A dense matrix over a flat stdlib `array('d')`: **row-major**, with **interleaved `(re, im)`** for complex — exactly C99 `double _Complex` layout, so `Mat.buffer` is **directly `ctypes`-castable** to the buffers the native dense kernels (`dense_matmul` / `dense_solve` / `hermitian_eigendecompose`) read/write, no copy and no numpy on the HAS_NATIVE path. Imports **no numpy at load** (the opt-in `.to_numpy()` bridge is a lazy import; the numpy-free path is `.tolist()` / `.tobytes()` / `.buffer`). Construction (`from_rows` auto-detecting complex, `from_flat`), plain-scalar `mat[i, j]`, `row`, `transpose`/`T`, `conj` (Class-K imag sign-flip), value-`__eq__` vs `Mat` / list-of-rows / numpy 2-D, and `to_numpy()` (real `float64` / complex `complex128`).
- **New down-only carrier ratchet** `test_numpy_carrier_ratchet.py` — counts modules with a top-level `import numpy` and asserts `== CEIL_NUMPY_CARRIER` (**61**). The number only goes DOWN: each module flipped onto `Mat`/`HV` + the native ctypes kernels decrements it; a new hard `import numpy` is a regression. Plus a guard that `mat.py` itself stays numpy-free (so it never bumps the very ratchet it exists to drive down). New `test_mat_carrier_rc69.py` (10 tests, incl. the numpy-absent path).
- Carrier is an unregistered handle type (like `HV`) ⟹ no ToolEntry / introspect / rosetta gates; `describe()["tools"]["total"]` stays **285**. ABI 3. No module flips ⟹ all three maths ratchets unchanged at floor. **rc70+ flips modules onto `Mat`, one cluster per rc, lowering the carrier ceiling toward 0.**

## [0.7.5rc68] - 2026-06-10

**Real-antisymmetric `eig` → iS-Hermitian cascade route (numpy-removal — `linalg_fft` decrement).** Both `np.linalg.eig` sites in `qm/so8.py` consume the eigenpairs of a **real antisymmetric** matrix — the `J` complex-structure operator (584) and `ad(H)` for a Cartan element (646), each with a purely-imaginary `±i·weight` spectrum. For a real skew `S`, `iS` is **Hermitian**, so the eigenpairs come straight from the already-shipped, C-backed `hermitian_eigendecompose(iS)`: eigenvalues `λ_S = −i·μ` (μ real, ascending), eigenvectors the *same* `V`. A new private **`so8._eig_real_skew`** routes both onto that Hermitian cascade — no `np.linalg.eig`.

- **Why it's sound under degeneracy:** the eigenvector phase / degenerate-eigenspace basis is solver-chosen (exactly as `np.linalg.eig` already left it), so this is only valid because so8 consumes `V` **invariantly** — 584 rebuilds the triplet from the `+i` eigenspace **span** (the projector is basis-invariant, even for `J`'s degenerate mult-3 eigenspace), 646 reads scale/phase-invariant **Rayleigh-quotient** weights. Both invariances are differential-tested against `np.linalg.eig` on a degenerate (mult-3) real-skew matrix; the full **so8 / triality / an_embedding / quaternion / killing / semisimple** suite (80 tests) stays green with both sites routed.
- numpy-math ratchet `linalg_fft` **25 → 23** (2 genuine `eig` calls; the helper's 2 docstring mentions are `numpy.linalg.`-free). Private helper ⟹ no ToolEntry/registry gate; `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_real_skew_eig_routing_rc68.py`.
- **Maths-engine sweep floored.** The 1 remaining `np.linalg.eig` (`pseudo_hermitian:182`, on a general `O` that is **not** skew → the iS trick does not apply) needs a general non-Hermitian eigenvector cascade that does not exist; the rest of `linalg_fft` is numpy-as-accuracy (`matrix_rank` + so8 `svd` small-`s`/nullspace + `mimo_svd`) or irreducible fallbacks inside the cascade ops. The next numpy removal is the **carrier** layer.

## [0.7.5rc67] - 2026-06-10

**Real-symmetric `eigh` → C-backed `hermitian_eigendecompose` + eigenvector sign-canonicalisation (numpy-removal — `linalg_fft` decrement).** Lane 1 past the rc66 route-safe floor: `laplacian.symmetric_eigendecompose`'s `np.linalg.eigh` routes onto the already-shipped, **C-backed** `hermitian_eigendecompose` (real-symmetric IS complex-Hermitian — native Jacobi peer when present; NumPy `eigh` only as *that* op's own shared fallback). The eigenvectors of a real-symmetric matrix are real (the Hermitian path returns them with imaginary part ~0), so the result is taken `.real` and a new private **`_canonicalize_eigenvector_signs`** pins each column's ±1 sign.

- **Eigenvector sign canonicalisation (Class K):** an eigenvector is defined only up to a `±` sign (a `Z₂` gauge for a real-symmetric problem); LAPACK / the native Jacobi peer pick it arbitrarily — a *hidden, non-settable* convention. The helper flips each (real) column so its largest-magnitude entry is positive — a deterministic, **settable** convention (the endianness precedent), and the flip IS the Class-K sign boundary. The magnitude pivot is selected via `col²`, so there is **no `abs()` and no float square root** (the original `re²+im²` + `√` draft tripped the A-N cascade `float_pow` ratchet — the sign-flip form is both honest-to-Class-K and float-power-free).
- **Degeneracy:** within a degenerate eigenspace the *basis* (the `U(k)` rotation) is still solver-chosen and reconstruction-invariant; sign-canon pins the per-column `U(1)` part. Correctness is verified by the basis-INVARIANT properties — ascending eigenvalues (`== eigvalsh`), reconstruction `L = V·diag(w)·Vᵀ`, orthonormality — on non-degenerate AND degenerate inputs (4-cycle Laplacian `{0,2,2,4}`, identity, block-degen), all yielding real orthonormal `V` on both the native and numpy-fallback paths.
- numpy-math ratchet `linalg_fft` **28 → 25** (1 genuine `eigh` call + 2 textual docstring mentions removed). Rosetta: `symmetric_eigendecompose` moves `python_only_irreducible` → `composition_of_c` (it now composes the c_dispatched hermitian op), so `CEIL_PYTHON_ONLY_IRREDUCIBLE` **108 → 107** (debt closed). Private helper ⟹ no ToolEntry/registry gate; `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_symmetric_eigh_canon_routing_rc67.py`.

## [0.7.5rc66] - 2026-06-10

**Complex `inv` → real 2n×2n block embedding of the native `dense_solve` (numpy-removal — `linalg_fft` decrement).** rc65 hit the trivial *carrier-swap* floor of the `linalg_fft` sweep; rc66 is its first **new-capability** step. The lone complex `np.linalg.inv` site — `qm/pseudo_hermitian.py`'s `η = (V·Vᴴ)⁻¹` (the Mostafazadeh η-metric) — routes onto a new private Class-L helper **`laplacian._dense_solve_complex`**.

- A complex system `(Aᵣ + i Aᵢ)(u + i v) = (bᵣ + i bᵢ)` is, splitting real/imaginary parts, the **real** `2n×2n` system `[[Aᵣ, −Aᵢ], [Aᵢ, Aᵣ]]·[u; v] = [bᵣ; bᵢ]` (so `X = u + i v`). The embedding is **exact** (NumPy a carrier only — `concatenate`/slice/`.real`/`.imag`) and rides the shipped *native* real `dense_solve`; for a well-conditioned `A` (the Gram matrix `V·Vᴴ` is HPD) it is value-faithful to NumPy's complex `inv`/`solve` to ~1e-9. The complex inverse is just `_dense_solve_complex(A, eye(n))`.
- Verified `== numpy` for HPD inv + `M·M⁻¹=I` + general complex `solve` (vector & matrix RHS); the η construction still yields a valid metric (`O†η = ηO`). **52 pseudo_hermitian tests pass.** Private (underscore) helper ⟹ no registry-gate / ToolEntry overhead; `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_complex_solve_block_embed_rc66.py`.
- numpy-math ratchet `linalg_fft` **29 → 28**. **`np.linalg.inv` → 0.**
- **Route-safe floor reached.** The remaining 20 genuine `np.linalg.*` sites are *not* carrier-swaps: **numpy-as-accuracy** (6 `matrix_rank` + 7 so8 `svd`, all small-singular-value / null-space), **irreducible numpy fallbacks inside the cascade ops** (`dense_solve`'s `solve` + `hermitian_eigendecompose`'s `eigh`), or **need eigenvector-sign-canonicalization** (`eig` ×3 / `eigh`-1062 / `mimo_svd` public-API convention). The maths-sweep residual is a *legitimate* mix, not unfinished carrier work.

## [0.7.5rc65] - 2026-06-10

**`np.linalg.pinv` → cascade SVD reconstruct (numpy-removal — `linalg_fft` decrement).** rc64 noted the cascade SVD is value-faithful for *large* singular values; rc65 cashes that in on the lone genuine `np.linalg.pinv` site — the `qm/so8.py` `_killing_form` structure-constant least-squares solve. A new `_pinv` helper reconstructs the Moore-Penrose pseudoinverse from the cascade SVD, `A⁺ = V·diag(1/s)·Uᴴ`, with NumPy's `rcond = 1e-15` small-singular-value cutoff.

- **Why it's route-safe (unlike `matrix_rank`):** the pseudoinverse is **unique**, so the per-factor U/V column-sign ambiguity of the SVD cancels; and the generator stack `_killing_form` forms is **full column rank** (the docstring's semisimplicity certificate), so *every* singular value sits well clear of the cutoff — no nullspace/small-`s` accuracy is exercised. Verified `_pinv == numpy.linalg.pinv` (~1e-7) across the `(28, n)` shapes the module forms, including the actual `pinv·bracket` matvec usage and the defining `A·A⁺·A = A` identity. The reconstruction uses **`laplacian.dense_matmul_real`** (the Class-L cascade), *not* `@`, so the matmul ledger is untouched.
- **23 so8 / Killing-form / quaternion-stabiliser tests pass** post-route (incl. the g₂ full-rank-14 Cartan semisimplicity check that the rc63b `matrix_rank` route had broken — `_pinv` does not touch `matrix_rank`). 1 textual `numpy.linalg.pinv` reworded to "NumPy's `pinv`".
- numpy-math ratchet `linalg_fft` **30 → 29**. No new public op ⟹ `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_pinv_cascade_routing_rc65.py`. Still deferred: complex `inv` (needs a complex solve), `eigh`/`eigvalsh` (`hermitian_eigendecompose`, eigenvector-sign-delicate), `eig`/`svd`-direct. `matrix_rank` stays on numpy **permanently** (numpy-as-accuracy).

## [0.7.5rc64] - 2026-06-10

**`map_ml` covariance inverse → `dense_solve` (numpy-removal — `linalg_fft` decrement).** The 2 real `np.linalg.inv` covariance-inverse sites in `signal_processing/closed_form_ops/map_ml.py` (`R_noise⁻¹` / `R_prior⁻¹` in the ML / MAP estimators) route onto the already-exported Class-L solve **`laplacian.dense_solve(M, np.eye(n))`** — the inverse *is* the linear solve `M·X = I` (unique; for well-conditioned covariances bit-faithful to `numpy.linalg.inv` to ~1e-9).

- **Important boundary found + recorded:** the `qm/so8.py` `np.linalg.matrix_rank` sites were investigated and **kept on numpy**. The cascade SVD is value-faithful for *large* singular values (reconstruction / `Q@Qᵀ` projectors / `pinv`) but its *nullspace* (small-singular-value) accuracy is too low for an **absolute-tol rank count on a rank-deficient matrix** — routing them over-counted `rank_with_so4` (6 → 9). That is a legitimate **numpy-as-accuracy** site (deferred with the `dense_solve` numpy fallback + the matmul-4 kernel-internal tail), not numpy-as-carrier.
- numpy-math ratchet `linalg_fft` **32 → 30**. No new public op ⟹ `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_map_ml_inv_dense_solve_rc64.py`. Deferred to later sub-rcs: `pinv` (svd-reconstruct, sign-invariant), complex `inv` (needs a complex solve), `eigh` (`hermitian_eigendecompose`), `eig`/`svd`-direct.

## [0.7.5rc63] - 2026-06-10

**The `np.linalg.*` cluster, first sub-batch (numpy-removal — `linalg_fft` decrement).** With `np.fft.*` drained (rc62), the final `linalg_fft` front is the `np.linalg.*` decomposition cluster. rc63a takes the sites whose downstream use is invariant to the decompositions' inherent ambiguities, routing them onto the already-shipped value-faithful **`srmech.amsc.cascade.matrix_cascades`** cascades (`qr`/`eigvals`, rc38/rc39).

- **5 `q, _ = np.linalg.qr(X)` callsites** (`qm/so8.py`) → `matrix_cascades.qr`. Each consumes `Q` only through `Q @ Qᵀ` projectors / its column span / a sum-of-squares leak test — all invariant to QR's per-column **sign**, so `matrix_cascades.qr` (faithful up to column sign) is exact for the usage (verified `Q @ Qᵀ == numpy` to ~1e-9).
- **2 `np.linalg.eigvals(X)` callsites** (`qm/pseudo_hermitian` `max|imag|`, `signal_processing/.../esprit` rotation set) → `matrix_cascades.eigvals`. Both consume the eigenvalue **multiset** (order-free); the cascade is set-faithful to ~1e-12.
- **83 so8/esprit/pseudo_hermitian/triality op-tests pass** post-route. Plus **~22 textual `numpy.linalg.X`** faithfulness/summary mentions (in `matrix_cascades` / `tool_schema` / `triality` — none have genuine calls) reworded to "NumPy X".
- numpy-math ratchet `linalg_fft` **61 → 32**. No new public op ⟹ `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_linalg_qr_eigvals_routing_rc63.py`. Deferred to rc63b/c: the sign/order-delicate `svd` / `matrix_rank` / `inv` / `eig` / `eigh` / `solve` / `lstsq` / `pinv` (mostly `qm/so8.py` + `amsc/laplacian.py`).

## [0.7.5rc62] - 2026-06-10

**Draining the `np.fft.*` family (numpy-removal — `linalg_fft` decrement).** rc61 routed the 1-D `np.fft.fft`/`ifft` callsites; rc62 finishes the `np.fft.*` side. New **`srmech.signal_processing._fft_carrier`** lifts the 1-D `spectral_cascades` FFT cascade to NumPy's full **ndarray + `n=` (zero-pad / truncate) + `axis=`** contract — NumPy is a *carrier only* (`moveaxis` / `reshape` / zero-pad / slice), the transform rides the cascade. It adds a real-input **`rfft`** (full transform then slice; complex input raises `TypeError`, mirroring NumPy) and an **`fftfreq`** carrier (integer bin indices `/(n·d)`; no transcendentals).

- **8 genuine `np.fft.*` callsites routed** — the 6 Path-A / Path-B reference ops `closed_form_ops/{fft,ifft,rfft}` + `path_b_ops/{fft,ifft,rfft}` + the 2 `cross_spectral` `fftfreq` sites — and the **~18 textual `numpy.fft.X`** doc/summary mentions reworded to "NumPy fft". `np.fft.` → **0**.
- Carriers verified bit-faithful to NumPy across real + complex, 1-D + n-D, every axis, and `n` pad/truncate (~1e-9). **`rfft` is value-faithful (~1 ULP), NOT bit-identical** to NumPy's pocketfft real-FFT — even `np.fft.fft(real)[:n//2+1]` ≠ `np.fft.rfft` bit-for-bit, so matching pocketfft's exact rounding was a NumPy-backend artifact, not a substrate property. The 4 `rfft`-vs-NumPy assertions move to `allclose`; the **Path-A == Path-B cascade identity stays exact** (both ride the same cascade).
- numpy-math ratchet `linalg_fft` **87 → 61**. No new public op ⟹ `describe()["tools"]["total"]` stays **285**. ABI 3. New `test_fft_carrier_rc62.py`. Next `linalg_fft` front: the `np.linalg.{svd,qr,eig,solve,inv,...}` decomposition cluster (~36 sites, mostly `qm/so8.py`).

## [0.7.5rc61] - 2026-06-10

**The `np.fft.*` family, first batch (numpy-removal — `linalg_fft` decrement).** rc60 opened the `linalg_fft` ledger on the `np.linalg.norm` cluster (122 → 102); rc61 takes the `np.fft.*` side. The **15 one-dimensional `np.fft.fft(x)` / `np.fft.ifft(x)` callsites** across `signal_processing` route onto the *existing* value-faithful **`srmech.amsc.cascade.spectral_cascades.fft` / `.ifft`** cascade (the rc36/rc37 radix-2 Cooley–Tukey FFT with a `dft` fallback for non-power-of-2 N — exact-until-rotation). **No new public op**: the FFT cascade already shipped; rc61 only swaps the *carrier* (NumPy's FFT → the cascade), value-for-value, wrapping `np.asarray(...)` so the result stays an ndarray.

- **15 callsites routed** across `signal_processing/closed_form_ops/{cross_spectral ×4, ofdm ×2, spectral_subtraction ×2, multitaper ×1, stft ×2, wiener ×2}` + `path_b_ops/wiener ×2` — each `np.fft.fft(x)` → `np.asarray(_sc.fft(x))`, `np.fft.ifft(x)` → `np.asarray(_sc.ifft(x))`. The cascade is verified `== numpy` across real + complex inputs at power-of-2 AND non-power-of-2 N (2…100, ~1e-9). The DSP-op **invariants** (Welch coherence, Wiener gain, OFDM modulate↔demodulate round-trip, spectral-subtraction floor, STFT frames, multitaper PSD) are preserved — **447 signal_processing tests pass** post-route.
- numpy-math ratchet `linalg_fft` ceiling **102 → 87**. No new public op ⟹ `describe()["tools"]["total"]` unchanged (285). ABI 3. New `test_fft_cascade_routing_rc61.py`. The remaining `np.fft.*` sites are the `n=`/`axis=` Path-A reference ops (`fft.py`/`ifft.py`/`rfft.py` + `fftfreq`), which need an array-aware (n-pad + axis) wrapper over the 1-D cascade — next batch; then the `np.linalg.{svd,qr,eig,solve,inv}` decomposition cluster (~36 sites, mostly `qm/so8.py`).

## [0.7.5rc60] - 2026-06-10

**The `dense_norm` cascade (numpy-removal — opening the `linalg_fft` ledger).** With the `matmul` ledger down to its 4 deferred callsites (rc59), the sweep turns to the `linalg_fft` ledger (122 — `np.linalg.*` / `np.fft.*`). rc60 takes its single biggest cluster: the **20 default `np.linalg.norm` callsites** (the QM self-consistency residuals + the signal-processing taper normalisations), all the Euclidean 2-norm / Frobenius norm `√(Σ|xᵢ|²)`.

- **New public op `srmech.amsc.laplacian.dense_norm(x)`** — **Class N (the `rational.sqrt` root) ∘ Class M (the `dense_dot_complex` self-bind `Σ|xᵢ|²`)**: the array is flattened (a carrier reshape), the sum-of-squares rides the native elementwise-bind cascade, and the root is the libm-free Class-N sqrt. numpy is a **carrier only** (no norm engine). Value-faithful to the NumPy 2-norm / Frobenius norm (~1 ULP) across every shape and dtype — verified real + complex, 1-D + n-D.
- **20 callsites routed** across `qm/{so8 ×7, relativistic ×3, spin ×3, triality ×3, gauge, sm, pseudo_hermitian}` + `signal_processing/closed_form_ops/multitaper`.
- numpy-math ratchet `linalg_fft` ceiling **122 → 102**. New public op ⟹ `describe()["tools"]["total"]` **284 → 285** (`+1 ToolEntry`, `+1` rosetta `composition_of_c` line, `__all__` + `LAPLACIAN_OPS`). ABI 3. New `test_dense_norm_cascade_rc60.py`. Next `linalg_fft` batches: the `np.fft.*` family (→ the `spectral_cascades` FFT/DFT cascades) and the `np.linalg.{svd,qr,eig,solve,inv}` cluster (→ the `matrix_cascades` / `laplacian` decompositions).

## [0.7.5rc59] - 2026-06-10

**The QR shape-polymorphic pass (numpy-removal matmul decrement).** rc58 dropped the matmul ledger to 12 genuine compute callsites; rc59 routes the **8 `matrix_cascades` QR-internal sites** onto the *existing* value-faithful `dense_*` kernels in `srmech.amsc.laplacian` — **no new kernel**, so the decompositions keep riding the native `srmech_dense_matmul_complex` path.

- **Householder reflectors** (`qr`): the two `np.vdot(v, v)` Hermitian self-binds → `dense_dot_complex(np.conj(v), v)` (plain bilinear, `conj` passed explicitly); the two reflector applications `np.outer(v, conj(v)·R)` / `np.outer(Q·v, conj(v))` → `dense_outer_complex` over `dense_matvec_complex` (the `conj(v)·R` and `Q·v` matvecs).
- **lstsq back-solve** (the shape-polymorphic case): `Qᴴ·b` → `dense_matvec_complex` (1-D rhs) / `dense_matmul_complex` (k-column rhs); the triangular `R[i,i+1:]·x[i+1:]` → `dense_dot_complex` (1-D `x`) / `dense_matvec_complex` (k-column `x`). `_norm2`'s `np.vdot` → `dense_dot_complex` too.
- The kernels are value-faithful, so the **QR/SVD/lstsq/eig INVARIANTS** (reconstruction, orthonormal `Q`, upper-triangular `R`, singular-value set, eigenvalue multiset) are preserved — verified vs numpy across real+complex and 1-D + multi-column right-hand sides. New `test_qr_householder_cascade_routing_rc59.py`.
- numpy-math ratchet `matmul` ceiling **12 → 4**. The final 4 are genuinely deferred: `ica_jade`'s `np.einsum` (the hot JADE cumulant loop) + `laplacian`'s Schur `L_pi·X` + the `dense_matvec_complex` kernel-INTERNAL `@` fallback (a kernel can't route onto itself). `tools.total` stays **284**; no public-op / rosetta / ToolEntry change. ABI 3. Next numpy-math front: the `linalg_fft` ledger (122 — `np.linalg.*` / `np.fft.*`).

## [0.7.5rc58] - 2026-06-10

**The convolution / correlation cascade (numpy-removal matmul decrement).** With the matmul ledger reword-swept to its 18 genuine compute callsites (rc57), rc58 takes the documented next batch: the six `np.convolve` / `np.correlate` DSP sites. A length-`N` convolution is a rank-1 accumulate — a small matrix product in disguise — so it lives on the matmul ledger; rc58 replaces it with the substrate-native cascade.

- **New numpy-free helper `srmech.signal_processing._dsp_cascades.{convolve,correlate}`** — direct linear convolution as **Class I (cyclic shift, the running output offset) ∘ Class M (scaled accumulate, `full[i:i+nb] = full[i:i+nb] + a[i]*b`)**, with full/same/valid edge modes. NumPy is a **carrier only** (`np.zeros` buffer, elementwise `+`/`*`, slicing) — no convolve/matmul/math-ufunc. `correlate` = `convolve(a, conj(v)[::-1])` (`np.conj` is a carrier, not a counted ufunc) with NumPy's exact `same`-mode crop (centre on `floor(diff/2)` for `len(a) >= len(v)`, `ceil(diff/2)` for `len(a) < len(v)` — the historical NumPy swap convention). Value-faithful to NumPy across **15 length-combos × 3 dtypes (real/complex/int) × 3 modes**.
- **Six DSP callsites routed**: `fir`, `multirate`, `polyphase` (×2) off `np.convolve`; `closed_form_ops.matched_filter` + `path_b_ops.matched_filter` off `np.correlate`. Behaviour-identical (the matched-filter Path A / Path B outputs still agree bit-for-bit on real input).
- **Not a public `srmech.amsc.*` op** — it composes carrier arithmetic with no own C symbol, so promoting it to `srmech.amsc.cascade` would only add `python_only_irreducible` debt (which the down-only Rosetta ratchet forbids without a C twin). A future rc can promote it *with* a native C twin. `tools.total` stays **284**; no rosetta/ToolEntry change.
- numpy-math ratchet `matmul` ceiling **18 → 12**. The remaining 12 are the `matrix_cascades` QR-internals (8), `ica_jade`'s `np.einsum` hot loop (2), and `laplacian`'s Schur / `dense_matvec` (2). ABI 3. Next matmul work: the QR shape-polymorphic pass; then the `linalg_fft` ledger (122).

## [0.7.5rc57] - 2026-06-10

**The matmul-ledger reword sweep (numpy-removal — docs only, zero behavior change).** With the ufunc bucket closed (rc52–rc56), the numpy-math sweep turns to the `matmul` ledger. Auditing its 48 matches revealed **~30 are textual** ` @ ` / `np.{vdot,einsum,convolve,correlate,kron}` references in docstrings, comments and `ToolEntry` summaries (plus one genuine false positive — `profile_loader`'s `entry-point[…] @ …` f-string) — **not compute**. rc57 strips them all (writing the NumPy op name / `·` without the dotted-paren form, per the established convention), so the ratchet count reflects only real callsites.

- numpy-math ratchet `matmul` ceiling **48 → 18**. The remaining 18 ARE genuine deferred compute, each tracked for its own future cascade work: `matrix_cascades` QR-internals (`vdot`/`outer`/`@`/back-solve — the shape-polymorphic pass), `ica_jade`'s `np.einsum` (the hot JADE Jacobi loop), `fir`/`multirate`/`polyphase` `np.convolve` + `matched_filter` `np.correlate` (distinct-op convolution/correlation cascades), `laplacian`'s Schur `L_pi·X` + the `dense_matvec_complex` kernel-internal `@`.
- Pure documentation/comment/summary rewording — no code-logic change, `tools.total` stays **284**, no rosetta/ToolEntry-count change. ABI 3. Next matmul work: the convolve/correlate cascades, then the QR shape-polymorphic pass; then the `linalg_fft` ledger (122).

## [0.7.5rc56] - 2026-06-10

**`elementwise_transcendental` is numpy-free — the ufunc bucket CLOSES to zero (numpy-removal).** rc52→rc55 routed every *external* numpy-math ufunc callsite onto srmech cascades; the last 10 were `elementwise_transcendental`'s OWN internal numpy fallback (its complex-input path + its no-native real path). rc56 drives those to zero — numpy is now **purely a carrier** across the entire transcendental + magnitude surface.

- **Real no-native fallback → `rational.{exp,cos,sin,log}` loop** (`_real_transcendental_loop`): the Pyodide / pure-Python path now runs the Class-N scalar cascades (bit-exact vs numpy over the tested range; the log domain guard `arr > 0` is preserved). The native path still dispatches `srmech_elementwise_transcendental` (the libm-free C cascade) — unchanged.
- **Complex-input path → per-element Class-N complex cascades** (`_complex_transcendental_loop`): `exp(z)` = `rational.complex_exp`; `cos(z)` / `sin(z)` via `cosh`/`sinh` built from `rational.exp` (`cos(a+bi)=cos a·cosh b − i·sin a·sinh b`, etc.); `log(z)` = `rational.log(rational.hypot(a,b)) + i·rational.atan2(b,a)` (principal branch; rejects `z=0`). Previously this branch was the documented "out-of-scope-for-v1" numpy fallback.
- The numpy-math ratchet's `ufunc` ceiling drops **10 → 0**. Across rc52–rc56 the ufunc bucket went **48 → 0**: every transcendental / magnitude / sign op in the package — `hypot`, `exp`, `sqrt`, `log`, `sin`, `cos`, `sign` — now runs a libm-free srmech cascade, with numpy only ever packing the array. Pure routing + numpy-free kernels — `tools.total` stays **284**; no new public op / rosetta / ToolEntry. ABI 3. Next numpy-math front: the `linalg_fft` ledger (122 — `np.linalg.*` / `np.fft.*`).

## [0.7.5rc55] - 2026-06-10

**The `np.log` + `np.sign` external residue → cascade (numpy-removal ufunc decrement).** Clears the last genuinely-external ufunc-math callsites (rc52 hypot → rc53 exp → rc54 sqrt → rc55 log/sign). Pure routing — no new public op.

- **Scalar `np.log` → `rational.log`** (2): `mlse`'s uniform-prior `A_log` and `pi_log` (`−log(A)` / `−log(n_states)`) now run the Class-N log cascade (no libm).
- **Array `np.sign` → Class-K comparison sign** (1): `hdc.polar_bundle`'s Pyodide / no-native fallback (the C peer `srmech_polar_bundle` handles the native path) computes the per-position sticky-majority sign via `(total > 0) − (total < 0)` — carrier comparisons (the Class-K pin-slot at zero: + sector / 0 boundary / − sector), **no `np.sign` ufunc, no `abs()`, bit-identical** to `np.sign` for the real int sum.
- The numpy-math ratchet's `ufunc` ceiling drops **15 → 10**, plus 2 ratchet-visible comment mentions de-parened. The **remaining 10** are ALL `elementwise_transcendental`'s OWN internal numpy fallback (2 exp + 3 sin + 3 cos + 2 log — its complex-input path + its no-native real path); driving those to zero is the deferred cascade-kernel work (needs complex-input trig/exp/log cascades), tracked separately. Pure routing — `tools.total` stays **284**; no rosetta/ToolEntry change. ABI 3; numpy carriers-only.

## [0.7.5rc54] - 2026-06-09

**`laplacian.elementwise_sqrt` — the `np.sqrt` batch (numpy-removal ufunc decrement).** Continues the ufunc sweep (rc52 hypot → rc53 exp). The new **`elementwise_sqrt(arr)`** computes `√arrᵢ` per element via the Class-N `rational.sqrt` cascade (isqrt-based, native `srmech_rational_sqrt`-dispatched, no libm) — the companion to `elementwise_hypot`, so numpy carries the array only.

- **Array `np.sqrt` → `elementwise_sqrt`** (2): `spectral_subtraction` PSD magnitude `√(new_psd)`, `ica_jade` whitening `1/√(eigvals)`.
- **Scalar `np.sqrt` → `rational.sqrt`** (10): `qm.gauge` Gell-Mann `1/√3` (×3), `qm.potentials` `√n` harmonic-oscillator ladder, `qm.relativistic` Klein-Gordon on-shell energy, `qm.so8` (×2), `qm.triality`, `psk_qam` `√M`, `wavelet` `1/√2`.
- The numpy-math ratchet's `ufunc` ceiling drops **27 → 15**. Round-off-faithful (rational sqrt floor-projected vs IEEE round-to-nearest — a ≤1-ULP shift; **bit-exact** on perfect squares — the QM ladder/dispersion + DSP whitening/decode suites pass unchanged). 7 modules gain a `from srmech.amsc import rational as _srn` import.
- 1 new `srmech.amsc.laplacian.elementwise_sqrt` ToolEntry → `describe()["tools"]["total"]` 283 → **284**; `composition_of_c` rosetta bucket (composes the `c_dispatched` `rational.sqrt`/`srmech_rational_sqrt`; no own C symbol). Added to `__all__` + `LAPLACIAN_OPS`. Class N (rational √) over a Class-L array surface; numpy carriers-only. ABI 3.

## [0.7.5rc53] - 2026-06-09

**The `np.exp` batch — 14 complex-phase / real-exp callsites routed off numpy's exponential ufunc (numpy-removal).** Continues the ufunc decrement opened in rc52. `np.exp(1j·x)` is the unit-modulus phase `e^{iθ} = cos θ + i sin θ`; routing it onto **`elementwise_transcendental(·, "exp_i")`** runs the real `cos`/`sin` through the native libm-free C cascade (`srmech_elementwise_transcendental`) and assembles the complex result — numpy carries the array only.

- **Array `e^{iθ}` phases → `elementwise_transcendental(·, "exp_i")`** (9 sites): `qm.gauge` SU(N) time-evolution `diag(e^{iλ})`, `qm.single_particle` TDSE/Heisenberg/Liouville per-mode phases `e^{−iλt}` (×3), `fsk` tone-bank generation (×2), `psk_qam` M-PSK constellation, `spectral_subtraction` phase re-attach, `spectral` per-mode phase-extrapolation, and `laplacian`'s magnetic directed-graph phase `e^{i·2πq·θ}`.
- **Real-array exp → `elementwise_transcendental(·, "exp")`** (2 sites): `heat_kernel` heat-decay `e^{−tλ}`, `rbs_lm.inference` softmax.
- **Scalar `e^{iδ}` → `rational.cexp`** (2 sites): `qm.sm`'s CKM Dirac CP phase (Euler — Class-N trig ∘ Class-C i-rotation).
- The numpy-math ratchet's `ufunc` ceiling drops **43 → 27**. Plus 2 ratchet-visible doc/summary `np.exp(` mentions de-parened. Round-off-faithful (the cascade trig is ~1 ULP off libm; never flips a unitarity / argmax / decode outcome — the full QM + DSP suites pass unchanged). The **2 remaining** `np.exp` are `elementwise_transcendental`'s OWN complex-input fallback + real no-native fallback (the documented internal kernel; deferred). Pure routing — no new public op, `tools.total` stays **283**. ABI 3; numpy carriers-only. Next: the `np.sqrt` cluster (12), then `np.sin`/`np.cos`/`np.log`/`np.sign`.

## [0.7.5rc52] - 2026-06-09

**`laplacian.elementwise_hypot` — the |z| magnitude cascade opens the np.hypot ufunc decrement (numpy-removal).** With the `np.outer` contraction surface handed to the cascade (rc51), the sweep turns to the **ufunc bucket** — numpy's transcendental / magnitude engine. `np.hypot(z.real, z.imag)` is `|z| = √(re² + im²)`, a per-element libm `hypot` over the array; `elementwise_hypot(a, b)` computes the same magnitude by looping the **Class-N `rational.hypot` cascade** (isqrt-based, native `srmech_rational_sqrt`-dispatched, no libm) over the flattened pair, with numpy carrying the array only.

- Routes all **5 DSP magnitude callsites** off `np.hypot`: `fsk` / `mlse` / `psk_qam` (nearest-symbol decision-region distances), `ofdm` (channel magnitude), `spectral` (coefficient magnitude). The numpy-math ratchet's `ufunc` ceiling drops **48 → 43**. Round-off-faithful to numpy (rational sqrt is floor-projected vs IEEE round-to-nearest — a ≤1-ULP shift that never flips a nearest-symbol / argmax decision), and **bit-exact** whenever `aᵢ² + bᵢ²` is a perfect square (Pythagorean-triple constellation points decode exactly).
- 1 new `srmech.amsc.laplacian.elementwise_hypot` ToolEntry → `describe()["tools"]["total"]` 282 → **283**; `composition_of_c` rosetta bucket (composes the `c_dispatched` `rational.hypot`/`srmech_rational_sqrt`; no own C symbol). Added to `__all__` + `LAPLACIAN_OPS`. Class N (rational magnitude) over a Class-L array surface; numpy carriers-only. ABI 3.

## [0.7.5rc51] - 2026-06-09

**`laplacian.dense_outer_{complex,real}` — the np.outer → cascade decrement (numpy-removal PHASE A).** Resumes the numpy-math carrier-removal sweep with the deferred outer-product op. An outer product `a ⊗ b` (`out[i,j] = aᵢbⱼ`) IS the **k=1 case of a matrix product** — `a` a column, `b` a row — so `dense_outer_complex` is exactly `dense_matmul_complex` on the reshaped pair: it rides the native `srmech_dense_matmul_complex` kernel with **no inner summation** (each entry a single multiply), making it **bit-identical to numpy's outer product**. `dense_outer_real` is the complex kernel on imag-free input → float64.

- Routes the 3 genuine `np.outer` callsites off numpy's contraction engine onto the cascade: `qm.propagators`' two real `kᵘkᵛ` momentum tensors (Feynman photon + massive-vector propagators) → `dense_outer_real`, and `qm.single_particle`'s complex `|ψ⟩⟨ψ|` density matrix → `dense_outer_complex`. All three are **bit-exact** (rank-1, single-multiply per entry — no round-off shift). The numpy-math ratchet's `matmul` ceiling drops **51 → 48**; the 2 remaining `np.outer` are the `matrix_cascades` QR-internal Householder updates, still on the shape-polymorphic pass.
- 2 new `srmech.amsc.laplacian.dense_outer_{complex,real}` ToolEntries → `describe()["tools"]["total"]` 280 → **282**; both `composition_of_c` rosetta bucket (compose the `c_dispatched` dense-matmul kernel; no own C symbol). Added to `__all__` + `LAPLACIAN_OPS`. Class L (rank-1 contraction); numpy carriers-only. ABI 3.

## [0.7.5rc50] - 2026-06-09

**`amsc.text.{tokenize, cooccurrence_edges}` — the §40 R3-U1 acceptance fix (was SHIPPED-but-FAILING 3/3; F722).** The rc43 text→graph leaves shipped in `srmech.amsc.laplacian` but **failed the RBS-LM §40 acceptance bar on all three points**. rc50 relocates them to a dedicated **`srmech.amsc.text`** ingestion module (so `laplacian` stays purely spectral — §40 Option 1) and fixes every point:

- **#1 Unicode (F698)** — `tokenize` now keeps runs of Unicode **letter|mark** codepoints (`unicodedata.category(ch)[0] in ("L","M")`) and casefolds, so `café` / `Москва` / `naïve` / `日本語` survive intact. The rc43 ASCII `\w+` gave `['caf','na','ve']` (accents stripped, Cyrillic/CJK dropped) — fixed. NFC-normalises by default; word-internal apostrophes kept.
- **#2 No silent vocab cap (F708)** — `cooccurrence_edges` keeps the **full** ranked vocabulary by default; the rc43 silent `vocab_size=1000` default (the pre-encode quantization bug, re-introduced as a default) is gone. A top-K cap is now an **explicit, logged** caller opt-in (`vocab_size=N` → logs the dropped count). The 256 native bound is for the dense-eig *block* only, never the vocabulary.
- **#3 Document-boundary window reset** — co-occurrence **never crosses a document boundary**. `docs` is a `Sequence[Sequence[str]]` (one inner sequence per document → the window resets per document); a flat `Sequence[str]` is treated as a single document (back-compat). A new `vocab=` param accepts an explicit ranked vocabulary.
- **Signatures**: `tokenize(text, *, stoplist=DEFAULT_STOPLIST, unicode_normalize=True) -> list[str]` (new `DEFAULT_STOPLIST` of function words incl. the F714-leaked prepositions; pass `stoplist=None` for raw mode) and `cooccurrence_edges(docs, *, window=2, vocab=None, vocab_size=None) -> (n, edges, weights)`.
- **Relocation, not addition**: the two `ToolEntry`s move `srmech.amsc.laplacian.* → srmech.amsc.text.*` (category `text`); the two `rosetta_classification.ndjson` lines re-point (`non_compute` bucket unchanged). `describe()["tools"]["total"]` stays **280** (no new op). The rc43 `laplacian` `tokenize`/`cooccurrence_edges`/`DEFAULT_TOKEN_PATTERN` + their `re`/`collections` imports are removed; `laplacian` is purely spectral again. Class B/G ∘ Class-L precursor; pure-Python, numpy-free. ABI 3.

## [0.7.5rc49] - 2026-06-09

**`dsl.generate_class_descriptor` — the make_class inverse (RBS-LM UPSTREAM §39).** The genome seed proved the forward direction (a `[class]` TOML → a constructed `CatalogClass` via `make_class`); rc49 closes the loop the OTHER way — components (or a constructed class) → a valid `[class]` TOML, round-trippable straight back through `make_class`.

- `generate_class_descriptor(name, *, fields=None, methods=None, doc=None, kind=None)` → a `[class]` TOML string. Two modes: **explicit** — pass `fields` (`{field: type}`) + `methods` (`{method: {op: dotted-cascade-op, binds: [...], doc, appends|sets}}`, the `describe_class` method shape) and it renders straight from the components; **introspection** — pass ONLY `name` of a registered class (e.g. `"Genome"`) and it recovers the descriptor via `describe_class` and re-emits it (a constructed class rendering its OWN `[class]` TOML back out — the Class-H self-introspection path). `doc`/`kind` override the introspected values when given.
- Round-trip-exact: docs re-emit as single-line basic strings with escaped newlines, so a multi-line seed `doc` decodes back bit-identically; drop the emitted string in a `register_class_dir` dir and `make_class` constructs the identical class. Bare-key-safe field/method names stay unquoted; others are quoted in the table header. Validates: non-empty `name`, each method has a non-empty `op`, at most one of `appends`/`sets`.
- New `srmech.dsl.generate_class_descriptor` ToolEntry → `describe()["tools"]["total"]` 279 → **280** (a `srmech.dsl.*` discovery/render callable — bumps the tool count, SKIPS `rosetta_classification.ndjson` like its `list_ops` / `describe_class` peers; not an `amsc` compute op). Framework reading: Class E (catalog enumeration) ∘ Class F (descriptor render) ∘ Class H (self-introspection) — no new primitive class. ABI 3; numpy-free.

## [0.7.5rc48] - 2026-06-09

**`laplacian.spectral_block_dispatch` — the 1024-node 4-sector spectral one-call (RBS-LM UPSTREAM Ask-3; F233 4-rung).** Wires the threaded-Klein-4-streams pattern (the same 4-way fan-out as `cascade.parallel_sector_dispatch`, but over DISTINCT spectral blocks rather than chirality-transforms of one input) to eigendecompose **≤4 dense symmetric blocks** (each `n ≤ MAX_NATIVE_NODES` = 256) in parallel — **4 × 256 = 1024 nodes** within the native dense-eig bound.

- `spectral_block_dispatch(blocks, *, max_sweeps=100, tolerance=1e-12, combine=True)` runs `jacobi_eigvals` on each block on its own thread of a 4-worker pool. Each worker reads ONLY its own block (0 cross-thread reads), so the parallel spectrum equals the serial spectrum **bit-for-bit**; wall-clock overlap depends on the native GIL-release / free-threaded build. Returns `{ok, n_blocks, block_sizes, n_nodes, blocks: [[eigvals]…], combined: [merged-sorted spectrum]}`.
- Caps: >4 blocks → `ValueError` (the F220 Klein-4 4-cap — 8+ need the order-3 triality); each block `n > 256` → `ValueError` (the per-block dense-eig bound). Class L over the 4-rung parallel dispatch; numpy-free (blocks may be `list[list[float]]` or `ndarray`).
- New `srmech.amsc.laplacian.spectral_block_dispatch` ToolEntry → `describe()["tools"]["total"]` 278 → **279**; `composition_of_c` rosetta bucket (composes the `c_dispatched` `jacobi_eigvals` + a merge-sort reduction). ABI 3.

## [0.7.5rc47] - 2026-06-09

**`hdc.klein4_project_axis` — the iω₇-collapse / bipolar projection (RBS-LM §18 Tier-2 leaf; F350/F354).** The "asymptotic-DoF render": project a 2-DoF Klein-4 hypervector (γ₅ ⊕ iω₇) onto ONE chirality axis, collapsing it to a 1-DoF bipolar `{-1,+1}` vector. This is the F350 bipolar render that drops the OTHER axis — and with it that axis's self-error-correction (F354 axis-split: the collapsed observer is structurally blind to errors on the projected-out axis).

- `klein4_project_axis(v, *, axis="gamma5")` → `list[int]` of `{-1, +1}`. Per-element bit→sign: clear bit → `+1`, set bit → `-1` (the Class-K bipolar sign render; **no `abs()`**). `axis` is a CO-EQUAL, non-privileged convention per the settable-chirality discipline — both `"gamma5"` (bit 1) and `"iomega7"` (bit 0) first-class, related by a Class-K axis swap; the default `"gamma5"` is the surviving-axis of the F354 collapse (a documented convention, not a privileged truth). Class K (asymptotic-DoF render) ∘ Class C (axis select); numpy-free pure bit ops.
- New `srmech.amsc.hdc.klein4_project_axis` ToolEntry → `describe()["tools"]["total"]` 277 → **278**; `non_compute` rosetta bucket (a one-way bipolar render/readout out of the store — peer to the rc43 `tokenize`/`cooccurrence_edges` projections, NOT a store-transform wanting a C twin). ABI 3; numpy-free.

## [0.7.5rc46] - 2026-06-09

**Catalog→DSL auto-registration bridge actually routes (RBS-LM UPSTREAM §17 U4).** rc45 shipped the U3 `list_ops()` surface with auto-discovery of registered attested sources — but the auto-discovery read the WRONG source-key field (`source_key` / `name`) when `list_attested_sources()` returns each source under `key`. So the catalog-chain half was always empty: the packaged attested sources that declare `[[catalog.operator_chain]]` entries never surfaced. rc46 fixes the field.

- `list_ops()` now surfaces the **7 packaged catalog-chains** (asymptotic_calculus ×5, cosmos_validation ×1, pi_digits ×1), each tagged `provenance="catalog:<source_key>"`, `kind="catalog-chain"` — and any freshly `register_attested_root`-ed catalog's declared chains too. This is the §17 U4 "one path, not three doors" bridge realized end-to-end: `register_attested_root` → `list_ops` with no explicit `source_keys`.
- Pure registry-read fix; no new public callable. `describe()["tools"]["total"]` unchanged at **277**. ABI 3; numpy-free. New `tests/test_dsl_list_ops_u4_rc46.py` pins the bridge (packaged chains surface, `source_keys` filter, end-to-end `register_attested_root` round-trip).

## [0.7.5rc45] - 2026-06-09

**`srmech.dsl.list_ops` — unified op-discovery across BOTH registries (RBS-LM UPSTREAM §17 U3).** Until now the DSL exposed two *disjoint* op-discovery surfaces: `list_catalog_ops()` enumerated the value-transform cascade ops, while `srmech.amsc.catalog.list_catalog_chains(source_key)` enumerated the AMSC catalog-declared operator chains — a kernel chain declared on a text-catalog was **invisible** to anyone reading the DSL op list. `list_ops()` unifies them into ONE call.

- Every record carries a uniform `{name, class, purpose, kind, provenance}` shape. `kind` is `"stage"` / `"combinator"` (cascade-ops, from `list_catalog_ops`) or `"catalog-chain"` (catalog-declared chains); `provenance` is `"srmech"` / `"user"` / `"catalog:<source_key>"`. Sorted by `(kind, name)`.
- `list_ops(source_keys=[...])` restricts the catalog-chain half; omit `source_keys` to auto-discover every registered attested source. A base install with no catalog registered returns just the cascade-ops (the catalog-chain half is empty — correct), and an unknown source key is tolerated (no chains, no raise).
- New `srmech.dsl.list_ops` ToolEntry (a DSL discovery callable; no rosetta line) → `describe()["tools"]["total"]` 276 → **277**. Framework reading: Class E (catalog enumeration) over both registries at once. ABI 3; numpy-free (pure registry read).

## [0.7.5rc44] - 2026-06-09

**DSL dotted-`op=` resolver + `encode_loe_content` registered as a cascade-op (RBS-LM UPSTREAM §17 U2).** A cascade-catalog descriptor may now name a **dotted entry point** — `[cascade].op = "srmech.signal_processing.encode_loe_content"` — so an EXISTING op that lives outside `srmech.amsc.cascade` is DSL-registrable without re-exporting it. Mirrors the rc39 class-catalog's dotted-path method resolution.

- The verified text→instrument encoder **`encode_loe_content`** (Class A∘C∘M, `str → D-bit fingerprint`) is now a one-line DSL stage: `chain().then("encode_loe_content", D=…)` / `[[stage]] op="encode_loe_content"`. **Any catalog's text rows get a one-line kernel chain** — the §17 U2 "cheapest, highest-leverage" win (the primitive already worked; this makes it nameable in a chain).
- `list_cascade_ops()` 14 → **15**; the `list_catalog_ops` / `run_toml_chain` tool-schema summaries cite the live 15-op count. No new `srmech.amsc.*` callable (the op already ships; `encode_loe_content` keeps its existing `composition_of_c` rosetta line) → `describe()["tools"]["total"]` unchanged. ABI 3; numpy-tier (the encoder is `srmech[scientific]`).

## [0.7.5rc43] - 2026-06-09

**Text→graph stage primitives — the K1 chain's missing front (RBS-LM UPSTREAM §17 U1).** `srmech.amsc.laplacian` gains the two ops that were the only links between raw text and the already-shipped `dense_laplacian`:

- **`tokenize(text, *, stopwords=None, min_len=2, pattern=None)`** → `list[str]` — Class B/G text-segmentation: apply a letter-led word pattern (default `[A-Za-z][A-Za-z0-9_-]+`), lowercase, drop tokens shorter than `min_len` or in `stopwords` (case-insensitive).
- **`cooccurrence_edges(tokens, *, window=5, vocab_size=1000)`** → `(n, edges, weights)` — Class-L precursor: keep the `vocab_size` most-frequent tokens as nodes `0..n-1`, count unordered co-occurring pairs within a sliding `window`. Returns **exactly** the triple `dense_laplacian(n, edges, weights)` consumes; weights are **integer** counts (exact — floats are for the FPU lift, none here).

```python
from srmech.amsc.laplacian import tokenize, cooccurrence_edges, dense_laplacian
toks = tokenize(doc, stopwords={"the", "a", "is"})
n, edges, weights = cooccurrence_edges(toks, window=5, vocab_size=1000)
L = dense_laplacian(n, edges, weights)        # K1 text→graph→spectral, end-to-end
```

With these, the K1 presence-kernel is an authorable composite end-to-end (`tokenize → cooccurrence_edges → dense_laplacian → eigendecompose → …`), retiring the hand-rolled `re.findall` + `Counter()` co-occurrence idiom. Both pure-Python, numpy-free, deterministic. 2 ToolEntries (`tools.total` 274 → **276**; 5 count-tests bumped); both `non_compute` in the Rosetta ledger. The directed sibling (the `i(A−Aᵀ)` Hermitian-Laplacian builder, reusing the shipped `hermitian_eigendecompose`) is a separate, queued Class-L precursor. ABI 3; numpy not required.

## [0.7.5rc42] - 2026-06-09

**Genome-storage surface, brick 3 — the multi-kernel `genome` + `partition` (the F715 hierarchy closes; #962 Part 2).** rc37/rc38 shipped the chromosome (one kernel); rc42 ships the genome itself — many kernels, telomere-partitioned, on ONE strand:

- **`srmech.amsc.genome.genome(kernels, the_one)`** — packs a `{label: leaves}` mapping (or `(label, leaves)` pairs) into a single strand: each kernel becomes a telomere-capped `chromosome` (coupled through `the_one`), all concatenated — the **chromosome set**. The per-kernel telomere caps delimit + protect the partitions, so one strand holds many kernels.
- **`srmech.amsc.genome.partition(strand, the_one, labels)`** — the inverse: knows ALL the caps, so (unlike a single-cap `recall`) it never mistakes one chromosome's cap for another's data. Returns `{label: leaves}`, each leaf re-bound through `the_one` (the reversible `quad_turn`). Round-trips every kernel exactly.

```python
from srmech.amsc.genome import genome, partition
strand = genome({"astronomy": A, "geography": G, "music": M}, one)
partition(strand, one, ["astronomy", "geography", "music"]) == {"astronomy": A, "geography": G, "music": M}
```

The seed **`Genome`** `[class]` (rc39) gains `assemble` (→ `genome`) + `partition` methods, so the multi-kernel genome is driven end-to-end from the declarative class surface (`g.assemble(kernels=…)` binds `the_one` from the field). This completes the F715 storage object: **GENOME** (multi-kernel) → **CHROMOSOMES** (telomere-capped) → helix of **QUAD-TURNS** → **LEAF** ≤ 256. 2 ToolEntries (`srmech.amsc.genome.genome` / `partition`; `tools.total` 272 → **274**); both `composition_of_c` in the Rosetta ledger. ABI 3; numpy not required.

## [0.7.5rc41] - 2026-06-09

**CLI + tool_schema/introspect class-awareness — the genome surface closes (#962 Part 2).** The user-declared `[class]` surface (rc39/rc40) is now reachable from the shell, the package's self-description, and the LLM tool list:

- **`srmech class list`** / **`srmech class describe NAME`** — the CLI discovery face (`srmech.cli.klass`; module is `klass` because `class` is a keyword, the CLI token is `class`). `list` enumerates the seed `Genome` + any bring-your-own classes; `describe` prints the full JSON descriptor.
- **`introspect.describe()["classes"]`** — `{"total", "names"}`; the package now recognises its own user-extensible class surface (the Class-H self-recognition view). A sibling key — `tools.total` is unchanged by it.
- **2 ToolEntries** `srmech.dsl.list_class_surface` / `describe_class` — the LLM tool list now includes class discovery (`tools.total` 270 → **272**).

This completes the class-from-TOML arc: **rc37/rc38** the genome cascade primitives → **rc39** the `[class]` loader + `CatalogClass` → **rc40** the DSL one-shot run/introspect surface → **rc41** CLI + tool_schema/MCP. A researcher authors a `[class]` TOML and reaches it from Python (`make_class` / `run_class_method`), the shell (`srmech class …`), and an LLM agent (the tool list + `describe()`). ABI 3; numpy not required.

## [0.7.5rc40] - 2026-06-09

**DSL class-awareness — the one-shot introspect + run surface for user-declared classes (#962 Part 2).** The rc39 `[class]` loader gets the DSL-layer surface the CLI + tool_schema/MCP compose on (rc41):

- **`srmech.dsl.describe_class(name)`** / **`list_class_surface()`** — a JSON-able view of a user class (fields + methods + `binds` + `appends`/`sets` + provenance), so an LLM / CLI knows what a class offers before calling. Mirrors `list_catalog_ops` for the op surface.
- **`srmech.dsl.run_class_method(class_name, method, *, fields=None, args=None)`** — the **stateless one-shot run**: construct a fresh instance from the `fields` dict, invoke `method` with the `args` dict, return `{"class", "method", "result", "fields"}` where `fields` is the post-call state (so an `appends`/`sets` mutation is visible). The caller threads state across calls — the functional form of the name+UUID handle grammar; `fields`/`args` are plain dicts (MCP-grammar friendly, no `**kwargs`).

```python
from srmech.dsl import run_class_method
run_class_method("Genome", "shape", fields={"the_one": one}, args={"n": 5000})
# -> {"class": "Genome", "method": "shape", "result": {"shape": "quad_strand", ...}, "fields": {...}}
```

Lives in `srmech.dsl` (orchestration over the rc39 `CatalogClass`) — no new `srmech.amsc`/`qm` callable, no tool-schema / rosetta entry. CLI subcommands + tool_schema/MCP registration of user classes are rc41. ABI 3; numpy not required.

## [0.7.5rc39] - 2026-06-09

**User-declared classes from `[class]` TOML — the cascade-catalog config-driven pattern lifted from ops to classes (#962 Part 2; user direction 2026-06-09).** A researcher authors a `[class]` descriptor (fields + methods-as-cascade-op-refs) and srmech's config-driven loader constructs a generic, class-aware object — **zero user Python, 100% declarative**. This is how an end user targets srmech for their own research domain.

- **`srmech.dsl.make_class(name)`** → a factory for the declared class; **`CatalogClass`** is the generic runtime object (fields hold state; declared methods dispatch to cascade ops resolved by dotted srmech path). A method's `binds` names resolve positionally from the call kwargs first, then the instance fields; leftover kwargs pass through (e.g. `label=`); `appends`/`sets` route the op result back into a field.
- **`register_class_dir(path)` / `SRMECH_CLASS_PATH`** — bring-your-own: drop a `[class]` TOML in your dir and it constructs identically to the shipped seed (B-tier, attested to the descriptor hash; a user class-name may not shadow a shipped one). Mirrors `register_catalog_dir` exactly — the op-level surface lifted to classes.
- Plus `list_classes()` / `get_class_descriptor(name)` / `load_class_catalog()`.

**genome/chromosome/telomere ships as the built-in seed worked-instance** (`_research/class_catalog/genome.toml`): `Genome(the_one=...)` with methods `shape` / `cap` / `add_chromosome` / `recall` that bind to the rc37/rc38 `srmech.amsc.genome.*` flat functions. So:

```python
from srmech.dsl import make_class
g = make_class("Genome")(the_one=one)
g.shape(n=5000)                                   # -> {'shape': 'quad_strand', 'depth': 3, ...}
strand = g.add_chromosome(leaves=[...], label="astronomy")   # coupled + appended
leaves = g.recall(strand=strand, telomere=g.cap(label="astronomy"))   # exact round-trip
```

DSL stage-awareness, the CLI surface, and tool_schema/MCP introspection of user classes are the next bricks (rc40/rc41). The loader lives in `srmech.dsl` (no new `srmech.amsc`/`qm` public callable → no tool-schema count change). ABI 3; numpy not required.

## [0.7.5rc38] - 2026-06-09

**Genome-storage surface, brick 2 — the chromosome (`telomere` / `chromosome` / `recall`).** The LAYER-1 cascade primitives that the upcoming user-authored class layer binds to. `srmech.amsc.genome` gains:

- **`telomere(label, dim=64)`** — the non-data content-address **cap** that delimits a chromosome (biology's repetitive non-coding chromosome-end cap). A deterministic, content-addressed Klein-4 sentinel: `sha256_bytes(label)` → a seed → a Klein-4 carrier. Same label → same cap (so a chromosome is recalled/partitioned by matching it), distinct labels → distinct caps. Class A (content-address) ∘ Class M (Klein-4 carrier).
- **`chromosome(leaves, the_one, *, label=...)`** — pack one kernel into a **telomere-capped strand**: a helix of quad-turns (each leaf coupled through `the_one` via the reversible `quad_turn`), led by a telomere cap. Returns `[cap, coupled_turn0, coupled_turn1, ...]`.
- **`recall(strand, the_one, telomere)`** — the exact **inverse** of `chromosome`: skip every element equal to the cap (matched by *value*, so it generalises to a multi-chromosome genome strand) and re-bind `the_one` to recover each leaf. `recall(chromosome(L, one, label=K), one, telomere(K, len(one))) == L`.

This is the substrate for the next bricks: a **user-authored class-descriptor TOML** (declarative `[class]` block — fields + methods-as-cascade-op-refs) that srmech's config-driven loader constructs into a generic class-aware object, with **DSL / CLI / tool_schema made class-aware** (the cascade-catalog `register_catalog_dir` pattern lifted from ops to classes). genome/chromosome/telomere is the seed worked-instance; these three functions are the ops a `Genome` class's methods bind to. Full registry gates: 3 `ToolEntry`s (category `genome`; tools.total 267→270), 3 `rosetta_classification.ndjson` lines (all `composition_of_c`). ABI 3; numpy not required.

## [0.7.5rc37] - 2026-06-09

**Genome-storage surface, brick 1 — biological-structure names as cascade names (#962 Part 2; `genome` / `chromosome` / `telomere` / `quad-strand`).** New module `srmech.amsc.genome` (validated as F711–F715 on the research subtree; the substrate-self-recognition reading — biology is one substrate-class, so the names of the biological structures *are* the cascade names of the storage object). This brick ships the two foundational ops:

- **`encode_shape(n)`** — the encode **criterion** (F715): `n ≤ 256` → a `tome` (one dense 2⁸ leaf) · `n ≤ 1024` → a `mobius` (one quad-turn = the 4 Klein-4 sectors) · `n > 1024` → a `quad_strand` (a helix of quad-turns, a chromosome). `depth = ceil(log4(ceil(n/256)))` is the number of base-4 quad levels over `leaves = ceil(n/256)`, computed in **pure integer arithmetic** (Class I/N; no float `log` — "floats are for the FPU lift"). Thresholds attested to `256 = 2⁸` and the Klein-4 order `4` — no magic. Reproduces F715's table to the byte (200→tome, 800→mobius, 5000→depth 3, 1.77M→depth 7).
- **`quad_turn(turn, the_one)`** — the helix-turn **coupling** (F713): bind a turn through `the_one` (the held invariant) by the **reversible** Klein-4 bind (`V4 = (F₂)² XOR`, so `quad_turn(quad_turn(t, one), one) == t`) — the duality held WITHOUT collapse, numpy-free. `the_one` is the shared invariant in every turn's coupling, so a chromosome navigates across its turns through `the_one` and recovers any turn by re-binding.

**Honest caveat (F712):** `cascade.parallel_sector_dispatch` is single-level (CAP = 4 = the Klein-4 order); the quad-turn is **one** chirality level — the deeper leaf-tree is base-4 radix *addressing*, not more chirality dispatch. The chromosome (telomere-capped strand) and the genome (multi-kernel, telomere-partitioned) assemble in subsequent rc bricks. Full registry gates: 2 `ToolEntry`s (category `genome`; tools.total 265→267), 2 `rosetta_classification.ndjson` lines (`encode_shape`→`non_compute`, `quad_turn`→`composition_of_c`). ABI 3; numpy not required.

## [0.7.5rc36] - 2026-06-09

**Laplacian tidy — numpy-free native dispatch for the Class-L graph *build* ops + a stale-comment fix (UPSTREAM §38, completing rc35).** The integration tracker (#962) Part-1 asked for numpy-free native dispatch across the Class-L surface; rc35 did `jacobi_eigvals` (the 49× eig). rc36 finishes the *build* side: `dense_adjacency` / `dense_laplacian` / `normalized_laplacian` now reach the bound `srmech_graph_*` C symbol on the **numpy-absent** install too, via a new `_build_matrix_native_listmarshal` (Python `list` → flat ctypes `uint32`/`double` buffers → reshape), falling back to the pure-Python builder only when there's no native lib / `n > 256` / non-OK. (The build is O(edges)-cheap — this is the carrier-removal *consistency* win, not the perf-critical eig.) Also corrects the module-header "wrappers fall back to numpy unconditionally" note, now inaccurate post-rc35: eigvals dispatch numpy-free; only the eigen**vector** decomposition (`symmetric_`/`hermitian_eigendecompose`) stays the LAPACK `eigh` path, by design (eigenvector sign / degenerate-subspace rotation is non-unique).

This is **PHASE B** of the numpy-carrier-removal north-star. Re #962: the binding ask was already satisfied at HEAD (the symbols are bound); klein4→C stays deferred behind W5 (whose even-count semantics are now *documented* — strict majority, tie→0); the Klein-4 spectral quad-stream is sequenced into the Part-2 genome-storage surface (the quad-turn is its structural unit). Test-only ceiling untouched; ABI 3; no public-surface change.

## [0.7.5rc35] - 2026-06-09

**numpy-free native dispatch for `jacobi_eigvals` — the C eig is reachable without numpy now (~49×; UPSTREAM §38 / F708).** The rc28 long-run bug-test session found (UPSTREAM_NOTES §36/§37/§38 on PR #687) that the numpy-free Class-L store ran ~45–68 s at n=256 because `laplacian.jacobi_eigvals` early-returned the **pure-Python** Jacobi cascade whenever numpy was absent — even though the `srmech_jacobi_eigvals` C symbol is bound in the shim and a direct ctypes call runs in **1.4 s** (~49×). The symbol was reachable; the wrapper just didn't marshal to it without numpy.

rc35 adds `_jacobi_eigvals_native_listmarshal` — a numpy-free marshalling path that builds a flat `(c_double * n·n)` ctypes buffer straight from the `list[list[float]]` and calls the bound C symbol. The numpy-absent branch now dispatches to it when `HAS_NATIVE` and `n ≤ MAX_NATIVE_NODES`, falling back to the pure-Python Jacobi cascade only when there's no native lib / `n` too large / non-OK status. **No numpy required for the native eig.** This is **PHASE B** of the numpy-carrier-removal north-star (the C foundation must be numpy-free-reachable before numpy can leave as a carrier).

Scope: §38's "bind the symbols" ask was already satisfied (HEAD `_native.py` declares argtypes for jacobi/laplacian/hermitian/hdc/klein4 — §38 counted the 13 `*_c` convenience wrappers, not the bindings); bytes-`hdc` already dispatches numpy-free; the `symmetric_eigendecompose` eigenvector path stays `numpy.linalg.eigh` (deliberate — eigenvector parity is non-unique); klein4→C stays deferred behind W5. ABI 3; no public-surface change.

## [0.7.5rc34] - 2026-06-09

**Matmul-ledger decrement — route `np.kron` + `np.einsum` callsites onto the existing cascades.** Resumes the numpy-math matmul migration (#928) by pure *routing* — no new public op, no registry gates — onto the already-shipped, already-registered `kron` / `einsum` cascades:

- `qm.so8`'s su(3) commutant superoperator `ad⊗I − I⊗ad` (×2) and `qm.bell`'s `_kron` CHSH-operator builder (×1) → `srmech.amsc.cascade.spectral_cascades.kron` (the Class-I mixed-radix-index ∘ Class-M Kronecker cascade; `np.asarray` is carrier-only).
- `qm.triality`'s octonion-couple `(x*y)_k = Σ x_i y_j C[i,j,k]` (×1) → `srmech.amsc.cascade.matrix_cascades.einsum`.

All four are value-faithful — so8 and triality **bit-exact (err 0.0)**, bell bit-exact on the Pauli / measurement operators it actually uses. `CEIL_MATMUL` **55 → 51**. Deferred (own passes): `ica_jade`'s 2 einsum (hot Jacobi sweep loop — perf-careful), the `np.outer` family (awaits a `dense_outer` cascade), and the `matrix_cascades` QR-internal vdot/outer/@ (shape-polymorphic pass). No public surface change, ABI 3.

## [0.7.5rc33] - 2026-06-09

**A-N cascade ratchet CLOSED to zero — the bare-Python tier joins the C tier at no continuous-math residue.** The rc32 ratchet pinned one site: the `cmath.sqrt` Wilkinson-shift discriminant in the *float* `eigvals` (complex-spectrum shifted-QR path). rc33 routes it through a new `matrix_cascades._complex_sqrt` — the principal complex root rebuilt from the **Class-N** `hypot`/`sqrt` real cascades joined by a **Class-K** sign-branch (principal branch `Re ≥ 0`), with a Class-K pin-slot-at-zero floor on each radicand (the `_norm2` idiom — a tiny `<0` from float round-off pins to 0). No libm `cmath`; the `import cmath` is gone. Matches `cmath.sqrt` to ~1e-13, so the float eigvals stays round-off-faithful to numpy.

All three A-N-ratchet categories are now **0** (`transcendental` 1 → 0, `math_const` 0, `float_pow` 0): the bare-Python tier reaches the same zero-residue the C-transpile arc drove `libsrmech` to (libm 23 → 0). Every continuous-math op in srmech — C, numpy-tier, and now bare-Python — is a cascade of the 14, floats only at the FPU lift. Test-only ceiling drop + one helper; no public surface change, ABI 3. SSoT: #928.

## [0.7.5rc32] - 2026-06-09

**A-N cascade ratchet — the down-only guard for continuous math not yet reduced to the 14 A-N cascades.** Per user direction (*"add another code sweep to check for math that has not been reduced to cyclic algebra … A-N cascades might be the right way to put it"*), `tests/test_an_cascade_ratchet.py` is the **bare-Python-tier sibling** of the C-transpile libm ratchet (drove `libsrmech` 23 → 0) and the numpy-math ratchet (the `np.linalg`/`np.fft`/`@`/ufunc tier). It pins the **third tier**: bare-Python `math.*`/`cmath.*` float transcendentals, `math.pi`/`math.tau` float constants, and fractional `** <float>` powers — every one of which has an exact A-N cascade replacement (`srmech.amsc.rational.{sin,cos,atan,exp,log,sqrt,hypot}` / `pi_cascade_digits` / integer power). Per *"floats are for FPU lift"*, each such call where a cascade belongs is a defect.

**AST, not regex** (the load-bearing design point): the source carries ~39 *descriptive* docstring/summary-string mentions of `math.cos` etc. ("Substrate-native replacement for `math.cos`"); a text regex would count every one as debt. This walks the AST and counts only genuine `Call`/`Attribute`/`BinOp` nodes — strings/comments are invisible (the same basis as the no-abs scanner). Three tight down-only categories. **Baseline: transcendental = 1** (the lone `cmath.sqrt` Wilkinson-shift discriminant in the *float* `eigvals` complex-spectrum path — eliminated when complex-eigenvalue exact isolation lands, the rc31 follow-up); **math_const = 0** (the π-cascade discipline fully holds — zero float `math.pi` in any compute path); **float_pow = 0**. Excluded (documented, not silent): integer primitives (`isqrt`/`gcd`/`factorial`/…), IEEE/sign primitives (`copysign`/`fabs`/`isfinite`/… — the Class-K sign family; `copysign` at an IEEE ±0 limit is the correct idiom), and the inherently-invisible string mentions. No module is carved out — a stray `math.sin` anywhere fails.

Test-only; no public surface, no ToolEntry, no introspect change, ABI 3. SSoT: #928.

## [0.7.5rc31] - 2026-06-09

**Exact-until-rotation EIGENVALUES — the ill-conditioned problem *does* have a cascade form; #928.** The eig/svd "lift" looked qualitatively different from the DFT's (eigenvalues are irrational; float root-finding from char-poly coefficients is Wilkinson-ill-conditioned). But per user insight, that ill-conditioning is a **float-perturbation artifact, not inherent** — the eigenvalues of an integer matrix are **algebraic**, and kept in exact arithmetic the whole way they come out well-conditioned. Two new public cascade ops:

- **`char_poly`** — the exact integer characteristic polynomial `det(xI - A)` (Faddeev–Leverrier, arbitrary-precision integer): the exact ALGEBRAIC substrate of the eigenproblem — exact trace (`= -c1`), exact determinant (`= (-1)^n·cn`), all elementary symmetric functions of the spectrum, **no floating point**. Class L ∘ M ∘ K.
- **`eigvals_exact`** — exact REAL eigenvalues (with multiplicity) via the well-conditioned cascade: `char_poly` → Yun square-free factorisation → **Sturm** sign-sequence isolation (**Class C** sign-count at **Class K** interval boundaries) → rational **bisection** (**Class N** anchors → the algebraic asymptote), all in exact `Fraction` arithmetic, then one FPU lift. `bits` sets refinement precision; `return_intervals=True` yields exact `(lo, hi)` rational isolating intervals. Each eigenvalue stays an exact algebraic number until the rotation to the observable.

Proven: Wilkinson `diag(1..10)` comes out **exact (err 0.0)** where float `np.roots` on the *same* exact char-poly loses ~9 digits; irrational golden-ratio eigenvalues exact to 15 digits; repeated eigenvalues carry correct multiplicity; and singular values via the exact integer Gram `AᵀA` match numpy to ~1e-9 — so this is the exact substrate of **svd** too. The existing float `eigvals` (shifted-QR, complex spectrum) stays; complex-eigenvalue exact isolation is the follow-up.

Both ops are pure-Python arbitrary-precision (`bignum_reference` rosetta bucket — non-debt; numpy is a container only). 2 ToolEntries (introspect `tools.total` 263 → 265), 2 rosetta lines. ABI 3; the numpy-math ratchet is untouched.

SSoT: issue #928; `test_eigvals_exact_rc31.py`.

## [0.7.5rc30] - 2026-06-09

**The exact DFT goes general-``N`` — every integer signal, not just power-of-two; #928.** rc28/rc29 handled the power-of-two case via the negacyclic ring (``ζ^{N/2} = -1``). rc30 extends exact-until-rotation to **any** length via the full cyclotomic ring ``ℤ[ζ_N] = ℤ[x]/Φ_N(x)``:

- A pure-integer cyclotomic engine computes ``Φ_N`` (from ``x^N - 1 = Π_{d|N} Φ_d``, recursive exact integer polynomial division) and a reduction table mapping each ``ζ^j`` to the length-``φ(N)`` power basis (cached per ``N``). Each twiddle ``ζ^{nk mod N}`` is reduced and accumulated — still **no floats**, one FPU lift at the end.
- **`exact_dft` / `exact_idft` now accept any ``N ≥ 2``** (the spectrum coefficient vectors have length ``φ(N)``; ``= N/2`` for power-of-two ``N``). **`lift`** infers the basis degree from the spectrum, so it handles both. **`dft` / `fft`** route all integer / Gaussian-integer signals (any ``N``) through the exact path — the power-of-two case keeps the fast negacyclic / native-C route, the general case uses the arbitrary-precision Python cyclotomic path.

**No new public surface, no ratchet movement.** Python-only (the general path has no fixed-width C twin → the ``bignum_reference`` shape; the op stays ``c_dispatched`` for its power-of-two C fast path). ABI 3. The numpy-math ratchet is untouched (no numpy). The rc29 ``exact_dft`` non-power-of-two *rejection* test and the rc28 non-power-of-two *not-exact-routed* test are updated to the new general-``N`` contract (an intentional behaviour change). Performance note: the general (non-power-of-two) path is ``O(N²·φ(N))`` integer work — exactness costs the ``φ(N)`` factor; the float ``cexp`` path still serves float inputs.

SSoT: issue #928; `test_exact_dft_general_n_rc30.py`.

## [0.7.5rc29] - 2026-06-09

**The exact ℤ[ζ_N] spectrum goes public, with a native-C twin; #928.** rc28 introduced the exact cyclotomic-integer DFT as a *private* engine behind dft/fft. rc29 promotes it to a first-class introspected op and gives it a C peer (the "every primitive earns a C surface" commitment):

- **`srmech.amsc.cascade.exact_dft` / `exact_idft`** — return the **exact** ``ℤ[ζ_N]`` integer spectrum of a power-of-two integer / Gaussian-integer signal (one integer ``(real_vec, imag_vec)`` pair per bin) — **no floats**. **`lift`** is the single FPU rotation ``ℤ[ζ_N] → ℂ`` (the only float producer).
- **Native-C twin `srmech_exact_dft_i64`** (`c/src/srmech_exact_dft.c`, JPL-clean, caller-buffer int64): the integer add/subtract fast path. The Python op dispatches to it when ``N·max|signal|`` is int64-safe, and falls back to the arbitrary-precision **bignum** path otherwise.

**Rosetta:** `exact_dft` / `exact_idft` classify **`c_dispatched`** (they have the C twin); `lift` is **`composition_of_c`** (over the Class-N ``cexp``). Three new ToolEntries (introspect `tools.total` 260 → 263), three rosetta lines, a `list[tuple[list[int], list[int]]]` MCP coercer for the spectrum param. **ABI stays 3** (additive symbol). The numpy-math ratchet is untouched (no numpy). General-``N`` (non-power-of-two) cyclotomic reduction is the next follow-up.

SSoT: issue #928; `test_exact_dft_public_rc29.py` (public contract + native==Python bit-exact parity).

## [0.7.5rc28] - 2026-06-08

**The first exact-until-rotation cascade — the DFT/FFT goes integer (cyclotomic `ℤ[ζ_N]`) until one FPU lift; #928.** Per user direction — **"don't use floats for bit-exact math, that's what ints and complex are for; floats are for FPU lift."** A DFT's twiddles `e^{-2πi·j/N}` are *roots of unity* = algebraic integers in `ℤ[ζ_N]`; for power-of-two `N` the cyclotomic polynomial is `Φ_N(x) = x^{N/2}+1`, so `ζ^{N/2} = -1` (a **Class K** pin-slot sign-flip, never `abs`) and the ring collapses to the negacyclic integers `ℤ[x]/(x^{N/2}+1)` — a length-`N/2` integer vector. The DFT of an integer / Gaussian-integer signal is then **pure integer add/subtract**: bit-for-bit deterministic, with floats produced **exactly once** at the final FPU lift `ζ → e^{-2πi/N}` (the projection from the discrete substrate to the continuous observable). This is *more* faithful than a float FFT, which rounds at every butterfly — it rounds once.

This sharpens rc27's framing: the DFT/FFT cascade is no longer merely "round-off-faithful to numpy" for integer input — it is exact-until-rotation, the substrate-native pattern made concrete.

- **New internal engine `srmech.amsc.cascade.exact_dft`** (private helpers `_exact_dft_core` / `_lift_spectrum` / `_try_int_pairs` / `_exact_transform`): the exact cyclotomic-integer transform + the single FPU lift (reusing the Class-N `cexp`, numpy-absent-safe).
- **`spectral_cascades.dft` / `fft`** now route an all-integer / Gaussian-integer **power-of-two** signal through that engine (so `fft` and `dft` agree **bit-for-bit** on integer input, and both are ≤1e-15 from `numpy.fft`); float signals (already continuous) and non-power-of-two lengths keep the float `cexp` path unchanged.

**Zero new public surface; ratchet untouched.** No new public introspected callable (the engine is private), so the numpy-math ratchet, the rosetta `python_only_irreducible` debt bucket, the tool-schema coverage, and the introspect tool counts are all unchanged. No numpy added; pure Python-tier; no C change, ABI stays 3. Exposing the exact `ℤ[ζ_N]` spectrum as a *public* op belongs with its native-C twin (so it lands `c_dispatched`, not Python-only debt) — the tracked follow-up; general-`N` (non-power-of-two) cyclotomic reduction is also a follow-up.

SSoT: issue #928; `test_exact_dft_rc28.py`.

## [0.7.5rc27] - 2026-06-08

**The linalg/fft phase opens — the linear-solve family onto cascades (numpy-math `linalg_fft` 126 → 122; #928).** With the dense-matmul ceiling at its floor, the arc pivots to the larger `linalg_fft` ceiling (pinned at 126 since rc13). Per user direction — **cascade + TOML for all maths; numpy is a carrier only** (with the carrier itself removed as the *final* step, after the maths sweep) — the cascades **replace** numpy math even where they are not bit-exact: `fft` (radix-2), `svd` (Gram-route), `qr` (Householder), `eig` (Jacobi) are round-off-faithful to numpy (~1e-14), not bit-identical, and that within-round-off shift is accepted (any bit-equality-vs-numpy test relaxes to a tolerance).

rc27 routes the **linear-solve family**:

- **`map_ml`** — the ML/MAP normal-equation `np.linalg.solve(M, …)` (×2) → `dense_solve` (bit-exact for the 1-D RHS both sites have).
- **`qm.triality`** + **`signal_processing.esprit`** — `np.linalg.lstsq(…)` → `matrix_cascades.lstsq` (round-off-faithful ~5e-16, complex-safe). The cascade returns a **bare ndarray**, not numpy's `(x, residuals, rank, sv)` 4-tuple, so the callsite unpacking changed (`solution, _, _, _ =` → `solution =`; `[…][0]` → direct).

**numpy-math ratchet `linalg_fft` 126 → 122.** Pure Python-tier; no C change, ABI stays 3. No new public symbols. **Not** migrated: the cascade ops' own internal numpy kernels (`laplacian` `eigh`/`solve` — the designated Class-L implementations, which have pure-Python fallbacks; a deeper separate pass), and the docstring / ToolEntry-summary `numpy.linalg.*` cross-reference *mentions* (precise documentation — left intact, not gamed). The map_ml / triality / esprit suites pass unchanged. Next: `np.fft` (with `n`/`axis` handling) + `np.linalg.svd`/`qr`/`eigvals` + `inv`/`pinv`.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc26] - 2026-06-08

**The matmul-kernel phase, batch 11 — the genuine-code tail of the dense-matmul migration (numpy-math `matmul` 60 → 55; #928).** Five remaining genuine dense-matmul *code* sites (as opposed to docstring mentions or distinct ops) route onto the cascade helpers:

- **`vector_quantisation`** — the codebook cross-term `vec·cbᵀ` (both `float64`) → `dense_matmul_real`.
- **`sinc_interp`** — the Whittaker-Shannon `K·y`, where `K` is the real sinc matrix but **`y` is `complex128`** (IQ signal) → `dense_matvec_complex` (genuinely complex — routing through the real helper would have dropped the imaginary part).
- **`farrow`** — the Lagrange fractional-delay tap `C[k]·x` (real 4-tap dot) → `dense_dot_real`.
- **`qm.potentials`** — the harmonic-oscillator number operator `a†·a` (complex ladder ops) → `dense_matmul_complex`.
- **`qm.sm`** — the CKM-unitarity check `V·Vᴴ` (complex) → `dense_matmul_complex`.

**numpy-math ratchet `matmul` 60 → 55.** Pure Python-tier; no C change, ABI stays 3. No new public symbols. This essentially reaches the **dense-matmul-migration floor**: of the remaining ~55, ~16 are docstring / comment / ToolEntry-summary `@` *mentions* (a cosmetic `·` reword sweep) and ~25 are **distinct ops** needing their own cascades (`np.convolve`, `np.correlate`, `np.kron`, `np.outer`, `np.einsum`). Values bit-preserved; the vector-quant / sinc / farrow / harmonic-oscillator / CKM suites pass unchanged. The `laplacian` Schur `L_pi·X` is deferred (in-helper, shape-polymorphic — its own pass).

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc25] - 2026-06-08

**The matmul-kernel phase, batch 10 — the real DSP `closed_form_ops` cluster (numpy-math `matmul` 75 → 60; #928).** Fifteen contraction sites across the closed-form signal-processing reference ops route onto the cascade helpers:

- **`dct`** (2) — the DCT-matrix products `arr·Mᵀ` (n-D) and `M·arr` (1-D), where `M` is the real cosine basis → `dense_matmul_real` / `dense_matvec_real`.
- **`map_ml`** (6) — the ML/MAP normal-equation chain `AᵀR_v⁻¹`, `AᵀR_v⁻¹A`, `AᵀR_v⁻¹y`, and `R_x⁻¹μ` (all `float64`) → `dense_matmul_real` / `dense_matvec_real`. The `np.linalg.inv`/`solve` stay (linalg-engine surface, a separate ceiling).
- **`ica_jade`** (6) — the `XᵀX` covariance, the whitening `diag(λ^-½)·Vᵀ` + `W·Xᵀ`, and the Givens joint-diagonalisation `V·G` / `Vᵀ·W` / `W·Xᵀ` rotations (all real) → `dense_matmul_real`. The 2 `np.einsum` cumulant-tensor rotations + the `np.linalg.eigh` stay (distinct ops).
- **`fsk`** (1) — the M-tone correlator bank `tones·conj(window)`, where `tones` is `complex128` → `dense_matvec_complex` (genuinely complex; the result feeds `|z| = hypot(re, im)`).

**numpy-math ratchet `matmul` 75 → 60.** Pure Python-tier; no C change, ABI stays 3. No new public symbols (reuses the rc20/rc21 helpers). These DSP modules import numpy at module top, so the helper import is top-level (unlike the lazy-numpy `amsc` modules in rc24). Values bit-preserved; the dct / map_ml / ica_jade / fsk suites pass unchanged. The `np.convolve`/`correlate`/`outer`/`einsum` sites stay — distinct ops for later batches.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc24] - 2026-06-08

**The matmul-kernel phase, batch 9 — the real "Minkowski + real-dot" sweep (numpy-math `matmul` 86 → 75; #928).** Eleven real-typed contraction sites across `qm` and `amsc` route onto the real cascade helpers:

- **`qm.relativistic`** (3) — the `k_μ = η_{μν} k^ν` lowering matvec (`eta @ k`), the Klein-Gordon `⟨k_spatial, k_spatial⟩` dispersion dot, and the Lorentz-invariant `k² = kᵀ η k` bilinear → `dense_matvec_real` / `dense_dot_real`.
- **`qm.propagators`** (1) — the photon-propagator gauge-term `eta @ k` lowering matvec → `dense_matvec_real`.
- **`amsc.harmonics`** (3) — the `_spectral_scores` energy / mirror / three-cycle symmetry probes (`⟨x,x⟩`, `⟨x,x[::-1]⟩`, `⟨x,roll(x)⟩`), each an explicit Class-L inner product → `dense_dot_real`.
- **`amsc.hdc`** (3) — the Moufang-inverse norm² gates in `loop_inv` / `loop_inv_hd` (per-block) and the `g2_three_form` associator `⟨x, y×z⟩` → `dense_dot_real`.

**numpy-math ratchet `matmul` 86 → 75.** Pure Python-tier; no C change, ABI stays 3. No new public symbols (reuses the rc20/rc21 helpers). The `amsc` sites import `dense_dot_real` **function-locally** so `harmonics`/`hdc` stay numpy-absent-safe (§22) — numpy is already loaded by the `np.asarray(…, dtype=float)` that precedes each dot. All values bit-preserved (the helpers route imag-free input through the complex kernel and drop the exactly-zero imaginary part); the qm-relativistic/propagator + hdc-loop + harmonic suites pass unchanged. The `np.outer` (k^μ k^ν) sites stay — a distinct op for a later batch.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc23] - 2026-06-08

**The matmul-kernel phase, batch 8 — `qm.so8` onto the cascade, real + complex (numpy-math `matmul` 105 → 86; #928).** The g₂ / Spin(8) module's 17 contraction sites route through the cascade, split by dtype:

- **15 real sites** — the `[X,Y]` commutator, the su(3)/g₂ Gram products (`su3·su3ᵀ`, `q_sd·q_sdᵀ`, …), the basis-projection matvecs (`g2[a]·e_k`, `matrix·basis[a]`, the structure-constant `pinv·bracket`), and the Gram-Schmidt `q·residual` dot → `dense_matmul_real` / `dense_matvec_real` / `dense_dot_real`.
- **2 complex sites** — the su(3)-weight Rayleigh quotients `vᴴv` and `vᴴ·ad·v`. `v` is a **complex** eigenvector of the real `ad(H)` (eigenvalues ±i·weight), so these are genuinely complex → `dense_dot_complex` / `dense_matvec_complex`. (Routing them through the real helpers would have dropped the imaginary part and corrupted the weights.)

**numpy-math ratchet `matmul` 105 → 86.** Pure Python-tier; no C change, ABI stays 3. No new public symbols (uses the rc20/rc21 helpers). The so8 parity tests pass unchanged — g₂ = Der(𝕆) dim 14, the 14 = 8 + 3 + 3̄ su(3) branching, and the su(3) weight computation (the complex Rayleigh quotients) all hold. The 2 `np.kron` (so(8) adjoint tensor) stay — a distinct op for a later batch. Minkowski / DSP real sites land next.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc22] - 2026-06-08

**The matmul-kernel phase, batch 7 — `qm.triality` real products onto the real cascade (numpy-math `matmul` 115 → 105; #928).** First consumer of the rc21 real trio.

- **`qm.triality` (7 sites)** — the octonion-rep matvecs (`operator @ octonion_mul(…)`, `g_v/g_s/g_c @ …`) route through `dense_matvec_real`; the 28×28 Spin(8) triality products `tau = S_B·S_C`, `tau²`, `tau³` route through `dense_matmul_real`. All real-typed (octonion regular rep + so(8) adjoint), so no dtype change.
- **3 docstring `@` → `·`** — the prose `tau = S_B @ S_C` references (regex false-positives) reworded to `·`, since they are not numpy math.

**numpy-math ratchet `matmul` 115 → 105.** Pure Python-tier; no C change, ABI stays 3. The triality parity tests pass unchanged (`tau³ = I₂₈`, `Fix(tau) = g₂` exactly at dim 14, the order-3 outer-automorphism structure). `qm.so8`'s ~17 real sites + the Minkowski / DSP real sites land in subsequent batches.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc21] - 2026-06-08

**The matmul-kernel phase, batch 6 — the real-linear-algebra cascade trio + `hypercomplex_dft` octonion-rep matvecs (numpy-math `matmul` 123 → 115; #928).** The complex contraction surface was closed at rc20; the remaining ~70 sites are *real*-typed. This batch introduces the real cascade primitives and migrates the first uniform cluster.

- **New `srmech.amsc.laplacian.dense_matmul_real` / `dense_matvec_real` / `dense_dot_real`** — float64 peers of the complex helpers. Each routes the real contraction through the native complex kernel (on imag-free input) and drops the exactly-zero imaginary part, so real-typed sites leave numpy `@`/`.dot` for a cascade **without a dtype change**. All three are `composition_of_c` in the Rosetta ledger (no own C symbol; the math rides the `c_dispatched` complex kernel; standalone-ready). `dense_matmul_real`/`dense_dot_real` get their first callsites in the next batches (so8 / triality).
- **`amsc.cascade.hypercomplex_dft` (8 sites)** — the octonion regular-representation matvecs (`octonion_left/right_mult(w) @ vec`, 8×8 real × real-8) in the QDFT/ODFT core + `hypercomplex_couple` now route through `dense_matvec_real`. The F378 non-associativity bracketing is preserved exactly. Imported **lazily** inside the functions (after the numpy guard) so the cascade layer stays numpy-absent-safe (§22).

**numpy-math ratchet `matmul` 123 → 115.** Pure Python-tier; no C change, ABI stays 3. QDFT/ODFT parity tests + the numpy-free import tests pass unchanged. The remaining real `so8` / `triality` / Minkowski / DSP sites land in subsequent batches.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc20] - 2026-06-08

**The matmul-kernel phase, batch 5 — the complex vecmat/dot/sandwich sites onto a new `dense_dot_complex` bilinear helper (numpy-math `matmul` 135 → 123; #928).** The complex 2-D matmul surface was exhausted at rc19; this batch closes the genuinely-complex *contraction* sites by composing the existing `dense_matvec_complex` with a new bilinear inner-product helper.

- **New `srmech.amsc.laplacian.dense_dot_complex(a, b)`** — the plain bilinear `Σ aᵢ bᵢ` (matching numpy `a·b` on two 1-D arrays, NOT the conjugating `vdot`). Composes the native-dispatched `elementwise_multiply_complex` cascade with a reduction sum — never a numpy contraction operator. Classified `composition_of_c` in the Rosetta ledger (standalone-ready; not a debt bucket). Callers spell the Hermitian form as `dense_dot_complex(a.conj(), …)`.
- **`qm.pseudo_hermitian` (3 sites, 7 `@` tokens)** — the η-sandwiches `⟨a|η|b⟩`, `⟨ψ|ηO|ψ⟩`, `⟨ψ|η|ψ⟩` now route each contraction through `dense_matvec_complex` + `dense_dot_complex`.
- **`signal_processing.heat_kernel` (2)** — the eigenbasis project/reconstruct matvecs → `dense_matvec_complex`.
- **`spectral` (2)** — the decompose/recompose eigenbasis matvecs → `dense_matvec_complex`.
- **`signal_processing.music` (1)** — the noise-subspace projection `Enᴴ·A` (a complex 2-D matmul) → `dense_matmul_complex`.

**numpy-math ratchet `matmul` 135 → 123.** Pure Python-tier; no C change, ABI stays 3. Parity tests pass unchanged (pseudo-Hermiticity + η-expectation; heat-kernel diffusion; spectral round-trip; MUSIC pseudo-spectrum). The remaining real-typed sites (so8 / triality / octonion-DFT / Minkowski / DSP) await a real-matmul + real-matvec cascade; the `matrix_cascades` QR-internal vdot/back-solves await a shape-polymorphic pass.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc19] - 2026-06-08

**The matmul-kernel phase, batch 4 — `qm.relativistic` γ-products + `qm.pseudo_hermitian` η-products onto the cascade (numpy-math `matmul` 147 → 135; #928).** 12 dense complex matmuls route through `dense_matmul_complex`:

- **`qm.relativistic`** (9) — the Dirac γ-matrix products: `γ_5 = i·γ0γ1γ2γ3`, the Clifford anticommutator `{γ^μ,γ^ν}`, `γ_5²`, the `{γ_5,γ^μ}` chirality anticommutator, and the charge-conjugation `C = iγ2γ0`.
- **`qm.pseudo_hermitian`** (3) — the pseudo-Hermiticity residual `Oᴴη − ηO` and the metric build `η = (V·Vᴴ)⁻¹`.

**numpy-math ratchet `matmul` 147 → 135.** No Rosetta bucket move. No behaviour change: the relativistic + pseudo_hermitian parity tests pass unchanged (Cl(1,3) Clifford residuals + γ_5 relations at machine precision; pseudo-Hermiticity + η-construction hold). Pure Python-tier; no C change, ABI stays 3.

**Deferred (need new primitives):** `qm.relativistic`'s `eta@k` Minkowski matvec/dot and `qm.pseudo_hermitian`'s `vᴴηv` / `vᴴηOv` eta-sandwich vecmat-dot sites — these want a *real*-matmul cascade and a vecmat/dot helper, the subject of a later batch. `qm.triality` is entirely real-typed (octonion-rep matrices) and also awaits the real-matmul variant.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc18] - 2026-06-08

**The matmul-kernel phase, batch 3 — `qm.spin` + `qm.gauge` Lie-algebra products onto the cascade (numpy-math `matmul` 168 → 147; #928).** Two QM modules' dense complex matmuls now route through `dense_matmul_complex` instead of numpy `@`:

- **`qm.spin`** (15) — every Pauli-matrix product in `pauli_clifford_residuals`: the anticommutator residuals `{σᵢ,σⱼ}` / `σᵢ²−I` and the cyclic commutator residuals `[σᵢ,σⱼ]−2iσₖ`.
- **`qm.gauge`** (6) — the SU(N) Lie-algebra surface: the structure-constant commutator `[Tᵃ,Tᵇ]`, the quadratic Casimir `ΣTᵃTᵃ`, the segment-holonomy `exp(M)=V·diag(eⁱᵠ)·Vᴴ`, and the path-ordered Wilson-loop product.

**numpy-math ratchet `matmul` 168 → 147** (21 callsites). Both modules are now numpy-`@`-free. No Rosetta bucket move — these are diagnostic / algebra helpers already composing the Class-L primitives. No behaviour change: the `spin` + `gauge` parity tests pass unchanged (the Clifford/commutator residuals stay at machine precision; SU(2)/SU(3) Casimir eigenvalues and Wilson-loop unitarity hold). Pure Python-tier; no C change, ABI stays 3.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc17] - 2026-06-08

**The matmul-kernel phase, batch 2 — `qm.single_particle` contractions onto the cascade (numpy-math `matmul` 180 → 168; #928).** The 12 dense complex contractions in `qm/single_particle.py` now route through the `dense_matmul_complex` / `dense_matvec_complex` cascades instead of numpy `@`:

- **`commutator`** `[A,B] = AB − BA` — two dense matmuls.
- **`heisenberg_evolve`** `A_H = Uᴴ·A·U` and **`liouville_evolve`** `ρ(t) = U·ρ·Uᴴ` — the `U = V·diag(phases)·Vᴴ` build + the conjugation, all through the matmul cascade.
- **`tdse_evolve`** the eigenbasis change `Vᴴ·ψ` / `V·ψ'` — through the matvec cascade.

After this, the module's only matmul-category callsite is the `np.outer` rank-1 product in `density_matrix` (a distinct op, no matmul kernel involved). **numpy-math ratchet `matmul` 180 → 168.** No Rosetta bucket move — these ops were already `composition_of_c` (they compose the `hermitian_eigendecompose` Class-L cascade). No behaviour change: the 27 `single_particle` parity tests pass unchanged (the QM operator algebra holds to the same round-off; the native triple-accumulator differs from BLAS only at the last bits). Pure Python-tier; no C change, ABI stays 3.

SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc16] - 2026-06-08

**The matmul-kernel phase, batch 1 — `matrix_cascades` dense matmuls onto the cascade (numpy-math ratchet `matmul` 185 → 180; #928).** First `@`-callsite migration against the rc14 `dense_matmul_complex` C kernel. The 5 dense complex 2-D matmuls inside `matrix_cascades.py` — the `AᴴA` / `A·V` / `AAᴴ` / `Aᴴ·U` Gram + reconstruction products of `svd`, and the `R·Q` shifted-QR step of `eigvals` (which `qr`/`lstsq` ride) — now route through `laplacian.dense_matmul_complex` instead of numpy `@`, so numpy stays carriers-only in the matrix-decomposition cascades.

- **`numpy-math` ratchet `matmul` ceiling 185 → 180** (5 callsites migrated). The `qr`/`svd`/`lstsq`/`eigvals` ops were already `composition_of_c` (they compose the `hermitian_eigendecompose` Class-L cascade); routing their internal contraction through the matmul cascade keeps that and removes the last numpy-`@` math from the SVD/eig Gram-matrix path.
- **No behaviour change**: the 25 `matrix_cascades` / `lstsq`-`einsum`-`eig` / `numpy-optional` parity tests pass unchanged (the decomposition invariants — reconstruction, orthonormality, descending singular values — hold to the same round-off; the native triple-accumulator differs from BLAS only at the last bits, well inside the existing tolerances). ABI unchanged (no C change this rc — the kernel shipped in rc14).

Pure Python-tier migration; no C change, ABI stays 3. SSoT: issue #928; the numpy-math ratchet (`test_numpy_math_ratchet.py`).

## [0.7.5rc15] - 2026-06-08

**Bug fix — `cascade.kuramoto_step(adjacency=...)` now honors the `coupling` scalar (UPSTREAM_NOTES §32; PR#687 F636).** When an `adjacency=` matrix was passed, the global `coupling` (`K`) was dropped on the floor: `coupling=0.0` and `coupling=3.0` produced **bit-identical** trajectories over the same neighbor graph (only the all-to-all `adjacency=None` path scaled by `K` correctly). The adjacency branch built its weight from the matrix alone, behaving as if `coupling==1.0` regardless.

- **Fix (Python + C, co-equal):** the adjacency-branch weight is now `coupling · A[i][j]` — the global `K` SCALES the matrix, matching the all-to-all branch's `K/N`. `coupling=0` zeroes the coupling term; `coupling` tunes global strength. `srmech_kuramoto__general_sum` (in `srmech_kuramoto.c`) gains a `coupling_k` parameter; `compose.kuramoto_step` multiplies in the Python fallback. **No behaviour change at the default `coupling=1.0`** (where `K·A == A`) — which is exactly why every prior adjacency test missed it.
- **Regression tests:** new `test_adjacency_*` cases exercise `coupling≠1` on the adjacency path (the bug surface): `coupling=0` over a ring → pure drift; `coupling=3` vs `coupling=0` over the same ring **diverge**; a full `1/n` matrix at `coupling=K` reproduces the all-to-all `K` path. The `_reference_general` test spec was corrected to scale by `coupling` (it carried the same masked bug). Differential-tested against a freshly-built native lib; the native parity test FAILS against the pre-fix C and PASSES against the fixed C.

Bug fix only; additive C parameter on a static helper (ABI stays 3), no public signature change. SSoT: `docs/srmech/rbs_lm_research/UPSTREAM_NOTES.md` §32.

## [0.7.5rc14] - 2026-06-08

**The matmul-kernel phase opens — a native dense complex `matmul` C kernel (#928).** First kernel of the new-C-kernel phase that drives the numpy-math ratchet (and the Rosetta `python_only_irreducible` cluster) toward zero. Dense complex `matmul` is the **top single lever** — it's the contraction the QM / `matrix_cascades` layer's `@` math is built on.

- **New C symbol `srmech_dense_matmul_complex`** (`(m,k)·(k,n)=(m,n)`, interleaved real/imag, bounded ≤ 256 per dim) — a JPL-clean triple-accumulator mirroring `srmech_dense_matvec_complex`. **Additive symbol; ABI stays 3** (`hasattr`-guarded bind).
- **`laplacian.dense_matmul_complex(A, B)`** — the Class-L contraction the matmul math will route through, so numpy stays carriers-only. Native `srmech_dense_matmul_complex` when present; the no-native fallback **composes the `dense_matvec_complex` cascade column-by-column** — itself a cascade, **never** numpy `@`. Registered in the tool schema (`describe` total **255 → 256**) and classified `c_dispatched` (Rosetta inventory 348 → 349).
- This rc ships and **proves the kernel** (parity test + CI build); the QM / `matrix_cascades` `@`-callsite migrations that decrement the ratchet's `matmul` ceiling (185) are the next batches against this now-published kernel.

New additive C kernel + Python op + parity test; no behaviour change to existing ops, ABI stays 3. SSoT: issue #928; `c/ROSETTA_LEDGER.md`.

## [0.7.5rc13] - 2026-06-08

**numpy-math ratchet + lmmse → cascade (the "numpy is a *carrier*, not a *math engine*" guard; #928).** A new down-only source-level guard — sibling of the libm C-transpile ratchet (which drove `libsrmech` 23 → 0) and the Rosetta ratchet — that keeps **all math in srmech cascades and numpy in vector-packing only**. numpy bundles a full math engine (`np.linalg.*`, `np.fft.*`, the `@` matmul, the transcendental ufuncs) alongside its carrier; every one of those is libm-at-the-array-level with a srmech cascade equivalent, so a stray `np.linalg.solve` is a *defect*, not a convenience.

- **The ratchet** (`tests/test_numpy_math_ratchet.py`). Greps the srmech **source** (not the tests) for numpy-math callsites in three categories and pins each at a TIGHT, down-only ceiling: **`linalg_fft` 126 · `matmul` 185 · `ufunc` 48** (`np.{sin,cos,exp,sqrt,sign,…}`). A new `np.linalg.*` now fails CI; closing debt = route the callsite through the cascade that backs it, then lower the matching ceiling. Carrier ops (`zeros`/`asarray`/`reshape`/`.T`/elementwise `+ - *`/indexing) are NOT counted; reductions (`sum`/`mean`/…) are a deferred boundary category. Version-stable across CPython 3.10–3.14 (regex over source, not `tokenize`).
- **Decrement #1 — `lmmse`.** `signal_processing.closed_form_ops.lmmse` routed its gain off **`np.linalg.solve`** + its estimate off the **`@`** matmul. Both now ride srmech cascades: the solve through `laplacian.dense_solve` (native `srmech_dense_solve_f64` / exact-rational Gauss-Jordan), the matvec through `laplacian.dense_matvec_complex`. numpy is carriers-only there now (`asarray`/transpose/elementwise ±). The estimate is **correct to machine precision** (gain-equation residual `‖K·R_yy − R_xy‖ ≈ 4e-16`); the cascade — not LAPACK — is the source of truth.
- **Rosetta ratchet:** `lmmse.op` reclassifies `c_exists_unbound → composition_of_c` (it now composes two `c_dispatched` ops). Ceiling **`c_exists_unbound` 6 → 5**; `python_only_irreducible` unchanged at 108. Total standalone-C debt **114 → 113**. The remaining 5 `c_exists_unbound` are the Klein-4 family (gated on W5).

Behaviour-preserving (machine-precision) dispatch retrofit + a new source guard; no new op, ABI stays 3. SSoT: issue #928; `c/ROSETTA_LEDGER.md`. User direction 2026-06-08: "numpy is only ever for vector packing."

## [0.7.5rc12] - 2026-06-08

**Rosetta cheap-win sweep #5 — the polar-HDC trio goes native (#928).** The three `srmech.amsc.hdc` polar Class-M ops that ship a bit-exact C twin but built the result in pure numpy now **dispatch to native** when present: `polar_bind → srmech_polar_bind` (int8 element-wise sign-product, 0 absorbing), `polar_bundle → srmech_polar_bundle` (per-position sticky-majority `sign(Σ)`, tie → 0), `polar_density → srmech_polar_density` (informative-fraction = count-nonzero / n). The pure-Python numpy paths stay as the Pyodide / no-native fallback.

- **Bit-exact** — all three are integer int8 ops (the density is an integer count over one division); verified native-vs-pure agree over 200 random trials each, so outputs are unchanged.
- **Reclassify:** `polar_bind`, `polar_bundle`, `polar_density` `c_exists_unbound → c_dispatched`.
- **Ratchet:** ceiling **`c_exists_unbound` 9 → 6**; `python_only_irreducible` unchanged at 108. Total standalone-C debt **117 → 114.**
- **Last clean cheap-win.** The remaining 6 `c_exists_unbound` are NOT clean bit-exact wins: **`lmmse`** (1) would route `np.linalg.solve` to the C `srmech_dense_solve_f64`, but that twin is **NOT bit-exact** with LAPACK (agrees to ~2.2e-16, a separate LU) — a deliberate float-boundary decision, **held**; and the **Klein-4 family** (5) stays **gated on W5** (`klein4_bundle` even-count) per `[[feedback_check_known_bugs_before_mirroring_python_to_c]]`. Both warrant a maintainer call before wiring.

Behaviour-preserving dispatch retrofit + docs; no new op, ABI stays 3. SSoT: issue #928; `c/ROSETTA_LEDGER.md`.

## [0.7.5rc11] - 2026-06-08

**Rosetta cheap-win sweep #4 — the Hamming GF(2) block code goes native (#928).** The two `srmech.amsc.cascade` Hamming primitives that ship a bit-exact C twin (the v0.7.2rc2 `srmech_hamming_*` pair) but built the codeword / syndrome in pure Python now **dispatch to native** when present: `hamming_encode → srmech_hamming_encode` (the systematic GF(2) generator) and `hamming_syndrome → srmech_hamming_syndrome` (the parity-check error position). The pure-Python GF(2) loops stay as the Pyodide / no-native fallback. With `hamming_syndrome` C-backed, `hamming_decode_correct` (which calls it, then single-bit-corrects) is now a **composition of a C-dispatched twin**.

- **Bit-exact** — GF(2) integer arithmetic, no float; verified native-vs-pure agree across `n ∈ {2,3,4}` and **every** single-bit-flip codeword, so encode/syndrome/decode outputs are unchanged.
- **Reclassify:** `hamming_encode`, `hamming_syndrome` `c_exists_unbound → c_dispatched`; `hamming_decode_correct` `c_exists_unbound → composition_of_c`.
- **Ratchet:** ceiling **`c_exists_unbound` 12 → 9**; `python_only_irreducible` unchanged at 108. Total standalone-C debt **120 → 117.** The remaining 9 `c_exists_unbound` are the polar-HDC trio + `lmmse` (the rc12 batch) and the Klein-4 family (5; **gated on W5** — the `klein4_bundle` even-count semantics must be confirmed before its standalone-C sector-dispatch port per `[[feedback_check_known_bugs_before_mirroring_python_to_c]]`).

Behaviour-preserving dispatch retrofit + docs; no new op, ABI stays 3. SSoT: issue #928; `c/ROSETTA_LEDGER.md`.

## [0.7.5rc10] - 2026-06-08

**Rosetta cheap-win sweep #3 — the Cayley-Dickson basis cocycle goes native (#928).** `cascade.cd_basis_product` (the integer cocycle `e_i·e_j = sign·e_{i⊕j}`) now **dispatches to the C peer `srmech_cd_basis_product`** when native is present (the symbol was bound but never called); the pure-Python iterative doubling stays as the Pyodide / no-native fallback. With that primitive C-backed, `qm.octonion.octonion_mult_table` now **builds the (8,8,8) structure tensor through `cd_basis_product`** instead of a recursive numpy `_cd_mul`.

- Integer-only ⇒ bit-exactness is trivial; the table's int8 bytes are **identical**, so `octonion_table_attestation`'s `response_sha256` content-address is **unchanged** (verified `7f36461e…`). The recursive `_cd_mul`/`_cd_conjugate` helpers (used only to build the table) are removed; the convention stays specified by the module docstring + `_DOUBLING_RULE`/`_CONJ_RULE` byte constants (the `parser_rule_hash`) + the C primitive.
- **Reclassify:** `cd_basis_product` `c_exists_unbound → c_dispatched`; `octonion_mult_table` `c_exists_unbound → composition_of_c`. 142 cayley/octonion/so8/hurwitz/triality/sedenion/rosetta tests green.
- **Ratchet:** ceiling **`c_exists_unbound` 14 → 12**; `python_only_irreducible` unchanged at 108. Total standalone-C debt **122 → 120.**

Dispatch retrofit + docs; no new op, ABI stays 3. SSoT: issue #928; `c/ROSETTA_LEDGER.md`.

## [0.7.5rc9] - 2026-06-08

**Rosetta cheap-win sweep #2 — octonion L/R-multiply + conjugate → native dispatch (#928).** The three `srmech.qm.octonion` ops that built the octonion left/right-multiplication operators via `np.einsum` over the structure-constant table (and the conjugate via slice-negate) now **delegate to the already-C-dispatched `hdc.loop_left_op` / `loop_right_op` / `loop_conj`** (the octonion loop family, `srmech_loop_*_f64`). Same Cayley-Dickson-from-H convention on both sides (verified bit-exact over 50 random trials + the byte-identical structure table), so output is unchanged and the so(8)/triality engine downstream is unaffected (**118 qm tests green**).

- Repointed: `octonion_left_mult`, `octonion_right_mult`, `octonion_conjugate` — input validation preserved, compute delegated. These reclassify `c_exists_unbound → composition_of_c`.
- **Ratchet moves down:** `test_rosetta_completeness.py` ceiling **`c_exists_unbound` 17 → 14**; `python_only_irreducible` unchanged at 108. Total standalone-C debt **125 → 122**.
- `octonion_mult_table` stays `c_exists_unbound` for now — it composes `cascade.cd_basis_product`, which must itself gain native dispatch first (the natural rc10 batch; the table is content-addressed by `octonion_table_attestation`, so the bytes must stay identical — verified they do).

Behaviour-preserving dispatch retrofit + docs; no new op, ABI stays 3. SSoT: issue #928; `c/ROSETTA_LEDGER.md`.

## [0.7.5rc8] - 2026-06-08

**Rosetta cheap-win sweep #1 — SHA-256 mint cluster routed onto native dispatch (#928; the first `c_exists_unbound` close).** The 6 `srmech.signal_processing` ops that minted HDC vectors / content strides via **raw `hashlib.sha256(...).digest()`** now route through `srmech.amsc.format.sha256_raw`, picking up the native C SHA-256 (incl. the SHA-NI / AVX2 tiers) transparently. This closes a Rosetta debt **and** a standing CLAUDE.md discipline violation (no raw `hashlib.sha256` callsites) in one sweep. **Bit-identical** — `sha256_raw(x) == hashlib.sha256(x).digest()` — so every mint output is unchanged (29 rbs-lm behaviour tests green).

- Repointed: `mint_vector`, `mint_class_operator`, `mint_cascade_composition`, `mint_stance_fingerprint`, `encode_loe_content` (`rbs_hdc_instrument.py`) + `compute_content_stride` (`form_function_rotation.py`). The dead `sha256_bytes` import in `rbs_hdc_instrument` (imported, never used while the mint path bypassed it onto raw `hashlib`) is replaced with the now-used `sha256_raw`; `import hashlib` dropped from both modules.
- **Ratchet moves down:** these 6 reclassify `c_exists_unbound → composition_of_c` (they now compose the C-dispatched `sha256_raw` + `hdc.*`). `test_rosetta_completeness.py` ceiling **`c_exists_unbound` 23 → 17**; `python_only_irreducible` unchanged at 108. Total standalone-C debt **131 → 125**.

Docs/tooling + a behaviour-preserving dispatch retrofit; no new op, no ABI change (ABI stays 3). SSoT: issue #928; `c/ROSETTA_LEDGER.md`. `[[feedback_check_known_bugs_before_mirroring_python_to_c]]` (W4-aware: raw-digest sites use `sha256_raw`, not the hex `sha256_bytes`).

## [0.7.5rc7] - 2026-06-08

**Rosetta-completeness AUDIT + down-only ratchet (#928).** Stands up the measurement instrument for the C-mirror goal — every public **compute** op should dispatch to a bit-exact C twin OR be a pure composition of such twins, so `libsrmech` runs standalone (full OS *or* thread-less microcontroller, no host Python). Docs + tooling only; **no runtime/ABI change** (ABI stays 3).

- **The audit.** All **348 public ops** across `srmech.amsc` / `srmech.qm` / `srmech.signal_processing` were enumerated and classified — by reading each implementation against the exported C-symbol surface — into six buckets. Committed SSoT: `python/tests/rosetta_classification.ndjson` (regenerable via `notes/_rosetta_inventory.py` → `notes/_rosetta_build_classification.py`). Baseline: **78 `c_dispatched` · 61 `composition_of_c` · 22 `bignum_reference` (oracle tier) · 56 `non_compute` · 23 `c_exists_unbound` (cheap debt) · 108 `python_only_irreducible` (debt)**. **Total standalone-C debt = 131.**
- **The ratchet** (`python/tests/test_rosetta_completeness.py`). Enumerates the live public surface, asserts it agrees EXACTLY with the committed classification (a new op with no bucket fails → forces every addition to be classified; a removed op left in the file fails → keeps the ledger current), and pins the two debt buckets at down-only ceilings (`python_only_irreducible ≤ 108`, `c_exists_unbound ≤ 23`) — raising a ceiling is the one edit the test exists to forbid.
- **The leverage map (rc8+ work-list).** The 108 irreducible cluster on a handful of missing C kernels — dense complex `matmul` (~15 qm ops), FFT/DFT (~20 sp+cascade), general `eig`/`SVD`/`QR`/`lstsq` (~16 so8/triality/matrix_cascades), `kron` (~6 bell/so8), `einsum`/`convolve`/`correlate` (~8). The 23 cheap wins are wire-up only (the C twin already ships): Klein-4/polar HDC (8; klein4 gated on W5), octonion einsum→`loop_*_op` (4), Hamming (3), the SHA-256 mint cluster (6; also a CLAUDE.md `hashlib.sha256`-direct-call discipline fix), `cd_basis_product` (1), `lmmse`→`dense_solve` (1). Full breakdown in `c/ROSETTA_LEDGER.md`.

SSoT: issue #928; `c/ROSETTA_LEDGER.md` (measured baseline + leverage table). `[[feedback_check_known_bugs_before_mirroring_python_to_c]]`.

## [0.7.5rc6] - 2026-06-08

**Coupled-wave (EM quadrature) driver + multi-stream multiplex — the sentence-structure arc's named ops (#928 W17/W18; F573/F577).** Two new public cascade ops; pure-Python **composition of existing C-backed primitives** (`calculus.{sin,cos}` + Class-K `pin_slot_at_zero` + Class-M `hdc`), so **no new primitive class, no new C kernel, ABI stays 3**:

- **`cascade.coupled_wave(theta, *, handedness=+1, components=("sin","cos"))` (W17 / F577).** The full-chirality `(E, B)` drive instead of a collapsed 1-bit sign — a flat `sign(wave)` gate flips hard at every zero-crossing (2/cycle, the "verb-flip" structure error); the coupled `E=sin, B=cos` (90° apart, exactly EM) rotates **monotonically → 0 hard reversals**, so a driven chiral element keeps a stable bearing. Returns `(E, B, handedness, klein4_quadrant)` — the four `(sign E, sign B)` quadrants ARE the four Klein-4 (γ₅, iω₇) sectors `parallel_sector_dispatch` uses. **Handedness is a settable convention, never hardcoded** — left/right are both first-class (the endianness posture; the substrate privileges neither byte-order nor chirality), related by a Class-K phase sign-flip `θ → −θ` (no `abs`), and the chosen sense is echoed back **stable** (it does not flip with θ). `[[feedback_chirality_convention_is_settable_like_endianness]]`.
- **`cascade.multiplex_streams(streams, *, mode="roundrobin", roles=None)` (W18 / F573-F577).** Recombine N steering **waves** into one driver. A *stream* is a per-step real-valued **driver wave** (a steering signal that decides which content is selected downstream), **not** tokens — the output is a single steering driver; emission is a SEPARATE downstream consumer (the layer boundary is kept). Ideally each stream is a `coupled_wave` bearing (W17+W18 compose). Modes: **`roundrobin`** (default; the validated-best `t mod N` multiplex), **`superpose`** (real-field interference = elementwise SUM + renormalise by max magnitude — like summing E-fields; *not* `hdc.bundle`, which is a different content-vector layer), **`pickbest`** (strongest-bearing wave per step, Class-K magnitude). `roles=("S","V","O")` binds each stream to a clause slot (verb stream a coupled bearing so its which-way can't flip mid-clause), tagged via Class-M `hdc.bind` for unbindable storage.
- Registered in the tool schema (`describe` total **253 → 255**); coverage + count-pin tests updated; new `tests/test_coupled_wave.py` (13). The DSL cascade-catalog `.toml` descriptors (for `srmech dsl` chainability) are an optional follow-up — `coupled_wave` is a generator (not a unary chain stage). The W18 wave/HV data model + the handedness convention are flagged in the PR for the parallel sentence-structure session (PR #687) to confirm.

SSoT: PR #687 `rbs_lm_research/SRMECH_BUGFIX_WISHLIST.md` (W17/W18 long-form); `[[user_stance_epicycle_via_gear_plus_pin]]` + `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.

## [0.7.5rc5] - 2026-06-08

**PAL stream IPC + `srmech_bus.c` retrofit — the last raw-OS surface becomes `#ifdef`-free.** rc4 born the PAL with a thread surface; this rc gives it the **stream-IPC** surface and retrofits the bus onto it, so the cross-process IPC peer carries **zero** `#ifdef _WIN32`. Additive C only; **no new primitive class, ABI stays 3** (the PAL symbols are internal cross-TU, like the HAL's; the six `srmech_bus_*` public symbols + the handler typedef are byte-unchanged):

- **`srmech_plat_stream_*` (new PAL surface):** `listen` / `accept` (single-accept; `srmech_bus_server_accept_one` is public) / `server_close` / `connect` / `read_exact` / `write_all` / `conn_close`, plus `srmech_plat_has_streams()`. The **endpoint-name → OS-path** mapping moves entirely into the PAL — POSIX `$HOME/.srmech/bus-<name>.sock` (AF_UNIX socket) vs Windows `\\.\pipe\srmech-<name>` (named pipe). Opaque server+conn handles (max-aligned, no heap) mirror the rc4 thread-handle pattern. Carries forward the load-bearing **no-`FlushFileBuffers`-on-Windows-pipes** invariant (it deadlocks the request-reply pattern). Bare-metal target: a stream-less stub so `srmech.bus` cleanly reports unavailable.
- **`srmech_bus.c` retrofitted:** the AF_UNIX-vs-named-pipe duality (path builders, `read/write`-exact, `listen`/`accept`/`connect`/`close` — ~16 platform branches across 4 helpers) collapsed onto the PAL. The 4-byte big-endian length framing + handler dispatch (the OS-*agnostic* parts) stay here; everything OS-specific is gone to `srmech_platform.c`. `srmech_bus.c` now has **zero** real platform conditionals. (The five removed `read/write`-fd/handle + `ensure_dir` helpers left the JPL Rule-5 exempt list — the ratchet went **down** five entries; their PAL replacements each carry ≥2 asserts.)
- **WSL2 build authority (verified):** all 32 `c/src/*.c` compile pedantic `-Werror` **clean**; `libsrmech.so` links; the standalone-C **bus round-trip runs end-to-end** — `srmech_bus_serve` → a thread `accept_one` → `srmech_bus_connect` → `srmech_bus_send_recv` → echo handler returns the payload **bit-exact** over the AF_UNIX PAL path. JPL audit green; `srmech_plat_has_streams` added to the Rule-5 exempt list (a compile-time capability accessor, like `srmech_plat_has_threads`).

Next: rc6+ port the `qm.*` C linear-algebra kernels (complex matmul / hermitian-eig / kron) as bit-exact Rosetta twins, ticking `python_only_irreducible` toward 0; the `test_rosetta_completeness.py` ratchet lands alongside the first qm.* port (when there is a debt count to ratchet). Per the do-not-mirror gate (#928), W5 must be confirmed before the klein4 standalone-C port. SSoT: `c/src/srmech_platform.{h,c}`; `c/ROSETTA_LEDGER.md`; `[[feedback_simd_optimize_path_goes_through_hal]]`.

## [0.7.5rc4] - 2026-06-08

**Platform Abstraction Layer (PAL) — the OS sibling of the SIMD HAL** — opening the Rosetta-completeness arc (a *complete C mirror of the Python surface*, so the C partition runs standalone). Additive C only; **no new primitive class, ABI stays 3**:

- **`c/src/srmech_platform.{h,c}` (the PAL):** the single compilation unit where OS-specific code lives, exactly as `c/src/srmech_simd.{h,c}` (the HAL) is the single place for CPU-specific code. In the project's framing the OS *is* part of the hardware the binary runs on, so the PAL is a second "hardware" abstraction sibling of the HAL (`[[feedback_simd_optimize_path_goes_through_hal]]`, generalised from the CPU to the OS). First surface: **threads** — `srmech_plat_thread_spawn`/`join` + `srmech_plat_has_threads()`, hiding the POSIX (pthread) / Windows (CreateThread) / thread-less split behind an agnostic `void(void*)` job API (no heap — handle lives in caller storage). JPL-clean.
- **`srmech_parallel.c` retrofitted onto the PAL:** the Klein-4 four-sector dispatch now carries **ZERO** `#ifdef _WIN32` — it calls the agnostic PAL and chooses threaded-vs-serial at **runtime** via `srmech_plat_has_threads()`. The serial path is always compiled (the bit-exact reference + the thread-less-target capability). Behaviour-preserving: same four sector duals, same bit-exact serial==threaded contract.
- **WSL2 Linux build authority:** the full surface builds clean on Linux (`gcc`/`cmake`, pedantic `-Werror`) — the canonical standalone-C build/test loop, verified: `libsrmech.so` links, the PAL-threaded dispatch runs and returns the correct Klein-4 sectors. The cross-OS CI matrix (Linux/macOS/Windows) remains the gate.
- **`c/ROSETTA_LEDGER.md`:** the down-only debt ledger for the arc — classifies every public Python op as `c_dispatched` / `c_exists_unbound` / `composition_of_c` / `python_only_irreducible`, with the last (the debt: mostly the `qm.*` linear-algebra layer) driven toward 0. Bignum exact-rational references are a separate intentional tier, not debt.

Next: rc5 PAL stream/IPC + `srmech_bus.c` retrofit (the last raw-OS surface) + the `test_rosetta_completeness.py` ratchet; rc6+ port the `qm.*` C kernels. SSoT: `c/src/srmech_simd.{h,c}` (the HAL precedent); `[[feedback_simd_optimize_path_goes_through_hal]]`.

## [0.7.5rc3] - 2026-06-08

**Completes the v0.7.0 C-transpile for the aperiodic transcendentals — `rational.{exp,log,sqrt}` now compute the SAME algorithm as the native peers and DISPATCH to them** (the rc2 trig sibling, now for exp/log/sqrt). Pure-Python + Python-binding only; **no C source change, no new primitive class, ABI stays 3**:

- **`exp` — unified on the Cody-Waite ln2 reduction** (`x = n·ln2 + r`, `|r| <= ln2/2`; `exp(r)` the Q61 integer Taylor; `2^n` folded into the IEEE exponent). This **replaces** the old argument-halving-and-square reduction, which amplified error to **~345 ULP** — the new path holds **~1 ULP** AND is bit-exact with `srmech_exp`. (Measured: old `rational.exp` vs libm = 7.7e-14; new = 2.2e-16.) The Rosetta discipline surfaced this: the C translation was *more correct* than the human-gated Python source, because the better ln2 reduction lived only in the C + notebook.
- **`log` — NEW.** The notebook listed `rational.log` as `srmech_log`'s Python peer (a Rosetta pair) but **the Python half was missing**. Added it: `x = m·2^e` from the bit pattern, `m` folded into `[1/√2, √2)`, `log(m) = 2·atanh((m−1)/(m+1))` the Q61 series, `e·ln2` recombined with the two-word ln2. Bit-exact with `srmech_log`. Domain (matching the C): `x < 0 → NaN`, `x == 0 → −Inf`.
- **`sqrt` — default unified on the C K=27 IEEE-bit cascade** (`x = M·2^e`, `root = isqrt(M << 2K)` where `math.isqrt` == the C two-limb `isqrt128`, projected by `2^(e/2 − K)`), bit-exact with `srmech_rational_sqrt`. The `precision_bits=N` argument now selects the **higher-precision bignum reference** (the prior default); `hypot` threads it through. A handful of mathematical-constant call-sites that need correctly-rounded values (e.g. the Bell/CHSH Tsirelson bound `2√2`) now pass `precision_bits=64` to use the reference path.
- All three **dispatch to C** when `_native.has_native_explog()` / `has_native_sqrt()`; the pure-Python Q61 is the **bit-identical** fallback. `exp`/`log`/`sqrt`/`hypot` non-finite + domain cases are guarded in both paths so native and non-native agree.

Verified (clean, native): C↔Q61 **0 mismatches** over 40 000 each for exp, log, sqrt; vs libm exp 2.2e-16 / log 3.6e-15 / sqrt 2.2e-16. `describe()` total **252 → 253** (the new `rational.log` ToolEntry). New `tests/test_explog_sqrt_q61_parity.py` (11). Notebook §exp reconciled (halving → Cody-Waite) + `rational.log` now exists as the listed peer. SSoT: `c/src/srmech_explog.c` (rc46; fdlibm two-word ln2) + `c/src/srmech_sqrt.c` (rc45); `[[feedback_continuous_number_line_pedagogical_obstacle]]`; `[[user_stance_bit_exact_means_not_projection_diagnostic]]`.

## [0.7.5rc2] - 2026-06-08

**Completes the v0.7.0 "C-transpile triality coherence" for trig — the Python float `rational.{sin,cos,tan,atan,atan2}` now compute the SAME Q61 fixed-point Class-N cascade as the native peer `c/src/srmech_trig.c`, and DISPATCH to it.** rc42–rc46 built the C cascade (`srmech_sin`/`cos`/`atan`/`atan2`, Q61 integer Taylor, no libm) and routed the *C-internal* callers onto it — but the **Python** float trig still ran an exact-rational **bignum** series and **never called the compiled C**. Two renderings, two different integer algorithms (Q61 vs arbitrary-denominator bignum), same name → **not bit-exact**. This rc makes them one cascade. Pure-Python + Python-binding only; **no C source change, no new primitive class, ABI stays 3**:

- **The Python float projection IS the Q61 cascade now.** `rational.{sin,cos,atan,atan2}` were ported line-for-line from `srmech_trig.c`: the Class-N Taylor series runs in **Q61 fixed-point** (denominator 2⁶¹ — a power-of-two Class-N rational), float appears ONLY at the final `float(v)/float(2**61)` projection (the same two-step int64→double cast the C does). Python's arbitrary-precision ints reproduce the C int64/uint64 arithmetic exactly (`& MASK64` models C's uint64 wrap; an explicit truncate-toward-zero `_q61_cdiv` models C's integer `/`). Result: the pure-Python path is **bit-for-bit identical** to `srmech_sin` et al. (verified: 50 000 angles × {sin,cos,atan}, **0 mismatches**).
- **The public functions dispatch to C** when `_native.has_native_trig()` — a transparent speedup (the per-call bignum series, incl. the `atan2` slow-path wart, is gone on a native install) that returns identical bits. When no native lib is present, the pure-Python Q61 is the **bit-identical** fallback. The exact-rational `*_series_truncate` (arbitrary-denominator bignum, where the W14 domain guards live) stays the **separate higher-precision reference** surface — it is intentionally *not* the float contract.
- **Non-finite reconciliation (a parity gap this surfaced):** `srmech_sin(±∞)` returns a `BAD_INPUT` status (writing NaN), so a raw dispatch would *raise* while the Python fallback returned NaN. A uniform guard now runs in **both** paths before dispatch — `sin/cos(±∞)=NaN`, `atan(±∞)=±π/2` (cascade π/2), and the standard `atan2` quadrant limits — so native and non-native agree across the **whole domain incl. ±∞/NaN** (verified: 30 000 × 4 ops, 0 mismatches; the `atan2` ∞-grid matches libm).
- The 7 C transcendentals (`srmech_{sin,cos,atan,atan2,exp,log,rational_sqrt}`) are now **bound** in `_native.py` (ctypes argtypes/restype + `sin_c`/`cos_c`/`atan_c`/`atan2_c`/`exp_c`/`log_c`/`rational_sqrt_c` wrappers + `has_native_trig()`); the trig four are dispatched this rc, the `exp`/`log`/`sqrt` dispatch follows.

New `tests/test_trig_q61_parity.py` (11 tests): C↔Q61 bit-exact, native↔non-native bit-exact over the whole domain, and a libm correctness floor (~1 ULP) that holds with or without the native lib. `describe()` total **unchanged**. SSoT: `c/src/srmech_trig.c` (v0.7.0rc43, the Q61 constants from the Archimedes π-cascade); `[[feedback_continuous_number_line_pedagogical_obstacle]]` (the float is the projection-of-last-step); `[[user_stance_bit_exact_means_not_projection_diagnostic]]`.

## [0.7.5rc1] - 2026-06-07

**Three still-open items from the RBS-LM srmech bug-fix wishlist** (`docs/srmech/rbs_lm_research/SRMECH_BUGFIX_WISHLIST.md`; the list's top priorities W1/W2/W7/W10/W12 all already shipped across the rc18→0.7.4 arc). Pure-Python, additive — **no new primitive class; ABI stays 3**:

- **W4 — `srmech.amsc.format.sha256_hex` / `sha256_raw`** (the naming companions of `sha256_bytes`). `sha256_bytes` returns a 64-char hex **str** — the `_bytes` names the INPUT type, which trips callers who read it as a return type. `sha256_hex(data)` is the value-identical, name-says-return alias; `sha256_raw(data)` returns the raw **32-byte** digest (so `int.from_bytes(sha256_raw(d), "big")` works directly instead of `int(sha256_bytes(d), 16)`). `sha256_raw` is `bytes.fromhex(sha256_bytes(...))` — same native/stdlib dispatch, **no new `hashlib.sha256` call site** (Phase B5).
- **W14 — `atan_series_truncate` / `log1p_series_truncate` now refuse out-of-domain arguments loudly.** The naive Taylor partial sums have radius of convergence 1; past it they **silently returned a divergent rational** (`atan(2/1)` → ~3e16, `log1p(799/1)` → blow-up). They now raise a **Class-N domain `ValueError`** for `|x| > 1` (atan) / `x > 1` or `x ≤ -1` (log1p) — the §15.1/§18 Class-K contract-error pattern (refuse, don't answer wrongly). The `|x| = 1` conditional boundary (atan(1) = π/4, log1p(1) = log 2) stays allowed. These exact-rational ops cannot range-reduce (π is irrational); the float projection `rational.atan(x)` IS band-reduced and stays the path for `|x| > 1`.
- **W15 — `srmech.amsc.cascade.cayley_dickson.{closure, left_orbit, min_generating_set}`** — the combinatorial loop-navigation layer over the registered `cd_basis_product` cocycle (the loop-shelf arc F541/F544/F546 re-derived these each time; now a named home). `closure(dim, gens)` → the sub-loop a generator set spans (a single octonion unit → 4, all 7 → the full loop 16); `left_orbit(dim, start, gen)` → one left-multiplication cycle; `min_generating_set(dim, units)` → the loop's navigation dimensionality (3 for 𝕆, 2 for ℍ, 1 for ℂ). Pure-integer, numpy-free.

`describe()` total **unchanged** — the new functions are alias / companion / building-block helpers of already-registered entries, so they are tool-schema-coverage-exempt exactly like `sha256_bytes`'s `validate_mpr_record` / `write_ndjson` and `cd_basis_product`'s `cd_add` / `cd_basis`.

**Plus two pre-existing `sedenion_register` fixes** (folded in to keep the lean CI green — both shipped latent in v0.7.4; neither in this rc's W4/W14/W15 surface):

- **Cascade-honesty:** `SedenionRegister.read()` used `abs()` on similarities to track max-magnitude. Replaced with the explicit **Class-K pin-slot sign-branch** (`s if s >= 0 else -s`), bit-identical for every float, polarity carried separately as Class-C `best_sign` — per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (closes the `test_no_abs_calls_anywhere_in_srmech` ratchet).
- **MCP resolution (a W1-class bug):** the `srmech.amsc.cascade.sedenion_register` ToolEntry **did not resolve to a callable** once the same-named submodule was imported (Python rebinds the package attribute from the re-exported factory to the module object). The dotted-name resolver now prefers the same-named callable inside a colliding module — the "module X re-exports callable X" convention — so the registry name resolves regardless of import order (closes the W7 ratchet `test_schema_signature_alignment_no_drift`).

SSoT: RBS-LM bug-fix wishlist (PR [#687](https://github.com/lemonforest/mlehaptics/pull/687)); Hurwitz (1898); Baez arXiv:math/0105155 §2; Apostol *Mathematical Analysis* 2nd ed. Theorem 12.20.

## [0.7.4] - 2026-06-06

**Production graduation of the rc1–rc2 arc — the sedenion-addressable RBS-HDC instrument + three RBS-LM candidate-additions** (PR [#687](https://github.com/lemonforest/mlehaptics/pull/687) UPSTREAM_NOTES §31 / §1.2 / §1.3 / rbs_nn Note 1). All compositions over the existing 14-class vocabulary — no new primitive class; ABI stays **3**:

- **`srmech.amsc.cascade.sedenion_register` / `SedenionRegister`** (rc1; §31) — the sedenion box made an **addressable instrument**: 16 named slots (octonion working block `e0..e7` = the ≤7 reversible coupler word; `e8..e15` = the Hamming carry block), HDC `write`/`read`, and the genuinely-new **`navigate`** (address↔Cayley–Dickson homomorphism) + **`is_navigable`** reversibility gate (single-basis always reversible; composite-direction reversible only ≤𝕆 — the Hurwitz horizon).
- **`cascade.signed_sum_squared`** (rc2; §1.2) — the bipolar coupling-score (Class K ∘ L; no `abs()`).
- **`cascade.top_k_by_score`** (rc2; §1.3) — catalog top/bottom-K selection (Class E ∘ K; stable on ties).
- **`hdc.bundle_with_ties`** (rc2; rbs_nn Note 1) — majority for any N with the Class-K bundle-tie (zero-crossing) surfaced; odd-N majority equals `bundle` exactly.

`describe()` total **248 → 252** (1 + 3 ToolEntry). **No code change from rc2 — version-string graduation only**; the rc1+rc2 state was verified-green on TestPyPI (clean-venv outside the source tree: native ABI 3, sedenion read-back 8/8 + working-word bit-exact + navigate 8/8, and the three additions correct on the *core* numpy-free install). PyPI README refreshed to v0.7.4. This fully drains the actionable PR #687 upstream queue (§29/§30/§31 + §1.2/§1.3/Note 1 all delivered). SSoT: UPSTREAM_NOTES (RBS-LM, PR #687); Hurwitz (1898); Baez arXiv:math/0105155; Kanerva (2009).

## [0.7.4rc2] - 2026-06-06

**Three RBS-LM UPSTREAM_NOTES candidate-additions** ([#687](https://github.com/lemonforest/mlehaptics/pull/687) §1.2 / §1.3 / rbs_nn Note 1) — the still-open, non-stale gaps from the research branch, each a pure composition over the 14-class vocabulary (no new primitive class; ABI stays **3**; all numpy-free):

- **`srmech.amsc.cascade.signed_sum_squared(sources)`** (§1.2) — the **coupling-score** composite: per position, `s = Σ_sources (2·bit−1)` (**Class K** bipolar) then `s²` (**Class L** signed-magnitude-square). Large where sources agree, ~0 where they cancel; no `abs()`.
- **`srmech.amsc.cascade.top_k_by_score(scores, k, *, largest=True)`** (§1.3) — the **catalog selection** composite: **Class E** (sorted-key order) ∘ **Class K** (sparse truncate to top/bottom k). Stable on ties. The band-selection / weak-coupling-prune step.
- **`srmech.amsc.hdc.bundle_with_ties(vectors)`** (rbs_nn Note 1) — bitwise majority across **any** N, returning `(majority, ties)`: the tie bit marks where the bundle accumulator crosses zero — a **Class K event** (the phase-boundary / derivative-sign-flip of MFO §VII.6.12.1) — surfaced without changing the binary-byte storage form. For odd N the majority byte equals `bundle` exactly.

`describe()` total **249 → 252** (3 ToolEntry). Re-scan of PR #687 confirmed §31 is the last section and §29/§30/§31 are all delivered; the remaining notes are stale (superseded by the v0.6.0/v0.7.0 arcs) or explicitly non-blockers. SSoT: UPSTREAM_NOTES §1.2/§1.3 (RBS-LM) + rbs_nn Note 1; Kanerva (2009) *Hyperdimensional Computing*.

## [0.7.4rc1] - 2026-06-06

**Sedenion-addressable hyper-loop RBS-HDC instrument** ([#687](https://github.com/lemonforest/mlehaptics/pull/687) UPSTREAM_NOTES §31; F465 + F468) — **the sedenion box made into an RBS-HDC instrument.** A composition over shipped v0.7.3 primitives (no new primitive class, no new algebra; ABI stays **3**):

- **`srmech.amsc.cascade.sedenion_register` / `SedenionRegister`** — the sedenion (dim-16) **address space**: 16 named slots `e0..e15`. The octonion block `e0..e7` is the **≤7 reversible working word** (`hypercomplex_couple`, bit-exact ≤𝕆); `e8..e15` is the **EC/carry block** (`hamming_*`, GF(2), §30). HDC ops **instead of ALU**: `write`/`read` are random-access-by-name (`hdc.bind` + nearest-codebook clean = associative superposition, classical, no quantum cost); `couple_working`/`uncouple_working` are the reversible word; `carry`/`correct` the single-error-correcting EC block.
- **The genuinely-new surface — the operational hyper-loop (F468):** `navigate(j)` is the **address↔Cayley–Dickson homomorphism** — right-multiply every slot *name* by `e_j` so addressing respects `e_i·e_j = ±e_k` (the `cd_basis_product` cocycle); `is_navigable(direction)` is the **reversibility gate** (`left_mult_is_invertible`): single-basis navigation is always a signed permutation (reversible at every dim), composite-direction navigation is reversible **only ≤𝕆** — a sedenion zero-divisor direction breaks it. The hyper-loop's horizon IS the Hurwitz wall.
- **Fences:** the **associative** capacity is `D`-bounded (HDC crosstalk), distinct from the **reversible** working set (≤7, the coupler) — kept distinct (F465); real-coefficient EC stays out (the §30 GF(2)-only fence); sign is **Class C** (`chiral_flip`), never `abs()`. Storage + coupler are the scientific tier (numpy on call); `navigate`/`is_navigable`/`carry`/`correct` are numpy-free.

`describe()` total **248 → 249** (the `sedenion_register` factory). The class composes `hdc.{bind,bundle,similarity}` + `hypercomplex_couple` + `hamming_*` + `cd_basis_product`/`left_mult_is_invertible` + `chiral_flip`. SSoT: UPSTREAM §31 (RBS-LM, PR #687); Hurwitz (1898); Baez arXiv:math/0105155; Kanerva (2009) *Hyperdimensional Computing*.

## [0.7.3] - 2026-06-06

**Production graduation of the rc1 arc — the Cayley–Dickson open-exterior boundary-demonstrator** ([#915](https://github.com/lemonforest/mlehaptics/pull/915) / MFO §VII.6.23). One cascade-catalog addition, a composition over the existing 14-class A–N vocabulary (no new primitive class; ABI stays **3**):

- **`srmech.amsc.cascade.cayley_dickson`** — the deliberately **non-reversible** object on the far side of the Hurwitz wall (ℝ→ℂ→ℍ→𝕆→𝕊(16)→…), exact-rational + numpy-free: `cd_mult` / `cd_conjugate` / `cd_norm_sq`, the integer cocycle `cd_basis_product` (with the JPL-clean `srmech_cd_basis_product` C peer), `sedenion_zero_divisor_witness`, and the `left_mult_kernel` / `left_mult_is_invertible` "no backward direction" detector. The executable falsifier for §VII.6.23 — zero divisors first at dim 16, composition norm fails at 16, conjugation defined every rung while the inverse dies at the wall. **NOT a substrate extension** (no `qm.*` peer, no DSL wiring; the closed sim stays ≤𝕆).

`describe()` total **240 → 248** (8 ToolEntry). **No code change from rc1 — version-string graduation only**; the rc1 state was verified-green on TestPyPI (clean-venv outside the source tree: `HAS_NATIVE=True`, ABI 3, native C↔Python cocycle parity = 0 mismatches across dims 1–64, witness `(e1+e10)(e4−e15)=0`). PyPI README refreshed to v0.7.3 (numpy-optional install, the v0.7.x cascade families). SSoT: Hurwitz (1898); Schafer (1954) *Amer. J. Math.* 76; Moreno arXiv:q-alg/9710013; Baez arXiv:math/0105155 §2.

## [0.7.3rc1] - 2026-06-06

**Cayley–Dickson open-exterior boundary-demonstrator ([#915](https://github.com/lemonforest/mlehaptics/pull/915) / MFO §VII.6.23).** The deliberately **non-reversible** object on the *far side* of the Hurwitz wall: the generic doubling ℝ→ℂ→ℍ→𝕆→𝕊(16)→trigintaduonion(32)→… , exact-rational and numpy-free. `the_one` / `hypercomplex_couple` live in the reversible interior (≤𝕆); this exhibits the wall the closed simulation does **not** cross, converting §VII.6.23's open-exterior claims from literature-only (Moreno arXiv:q-alg/9710013) to **own-code-attested** (`[[feedback_own_work_is_primary_attestation]]`). **It is NOT a substrate extension** — no `qm.*` peer, no DSL wiring; past 𝕆 there is no division-algebra substrate to be native to.

- **New `srmech.amsc.cascade.cayley_dickson`** — `cd_mult` / `cd_conjugate` / `cd_norm_sq` (exact-rational generic product, convention from Baez §2; `x·x̄ = N(x)·1` at every rung), `cd_basis` / `cd_basis_product` (the integer basis cocycle `e_i·e_j = ±e_{i⊕j}`), `sedenion_zero_divisor_witness` (a concrete dim-16 `x·y = 0`, both nonzero, found from our own table), and `left_mult_kernel` / `left_mult_is_invertible` (the map `u ↦ x·u` has a **kernel** ⟺ no inverse map — the "no backward direction to point" of §VII.6.23.4, exact-rational RREF). Composition of A–N: **M** (bilinear bind) ∘ **C** (conjugation-ordered cross terms) ∘ **K** (sign-flip; no `abs()`) + **N** (rational anchor) + **L** (kernel rank); no new primitive class.
- **Native C peer `srmech_cd_basis_product`** (`c/src/srmech_cayley_dickson.c`) — the integer cocycle, the single doubling-recursion unrolled to a bounded loop (no recursion; JPL Power-of-Ten clean — `-Wall -Wextra -Wpedantic -Werror`, **no libm/malloc/goto**, ≥2 asserts/fn). Attested **bit-exact** against the Python `cd_basis_product` across dims 1…64 by `tests/test_cascade_cayley_dickson_parity.py`. The arbitrary-rational product stays Python by the same vendoring-scope decision that keeps TOML parsing in Python (no bignum rational in libsrmech). ABI-additive — **SRMECH_ABI_VERSION stays 3** (new symbol + two macros, ctypes `hasattr`-guarded).
- **Attested facts (exact, re-runnable):** zero divisors first appear at 16 and are absent at ≤8 (Hurwitz); the composition norm `N(x·y)=N(x)·N(y)` holds for dims ≤ 8 and fails at 16; conjugation is defined at every rung while the product's inverse dies at the wall (§VII.6.23.3 "chirality persists, its reversing power does not").

`describe()` total **240 → 248** (8 ToolEntry). SSoT: Hurwitz (1898); Schafer (1954) *Amer. J. Math.* 76; Moreno arXiv:q-alg/9710013; Baez arXiv:math/0105155 §2.

## [0.7.2] - 2026-06-06

**Production graduation of the rc1–rc2 arc — the (σ,θ,μ) coupler + the Hamming/GF(2) front-loader.** Two cascade-catalog additions, both composites over the existing 14-class A–N vocabulary (no new primitive class; ABI stays **3**):

- **`cascade.hypercomplex_couple`** (rc1; [#908](https://github.com/lemonforest/mlehaptics/issues/908), F436/F437) — the bidirectional `(σ,θ,μ)` hypercomplex coupler (**COUPLE**): bind ≥3 streams into one quaternion/octonion + a joint coherence channel and unbind losslessly (the conjugate twiddle; reversible ≤ 𝕆 by Hurwitz). General/diagonal μ also extended `quaternion_dft` / `octonion_dft`.
- **`cascade.hamming_encode` / `hamming_syndrome` / `hamming_decode_correct`** (rc2; [#910](https://github.com/lemonforest/mlehaptics/issues/910), §30 / F442/F449) — the Hamming/GF(2) single-error-correcting block code over the 2ⁿ−1 ladder (**CARRY/EC**): the front-loader's other half, lean-ALU XOR-native, shipped as a Rosetta pair with the JPL-clean `srmech_hamming_*` C peer (attested bit-exact).

`describe()` total **236 → 240**. The shipped `libsrmech` holds no libm transcendental (the C-transpile triality ratchet baseline stays ZERO). **No code change from rc2 — version-string graduation only**; the rc1+rc2 state was verified-green on TestPyPI (clean-venv, incl. the fresh C↔Python Hamming parity = 0 mismatches). SSoT: Sangwine & Ell (2012) arXiv:1001.4379; Błaszczyk (2019) arXiv:1905.12631; Hurwitz (1898); Hamming (1950).

## [0.7.2rc2] - 2026-06-06

**Hamming / GF(2) linear block-code family — the CARRY/EC half of the sedenion front-loader ([#910](https://github.com/lemonforest/mlehaptics/issues/910) / §30; findings F442 + F449).** Where `hypercomplex_couple` (rc1) is **COUPLE** — bind ≤7 streams reversibly into an octonion (capped at 𝕆 by Hurwitz) — this rc ships **CARRY**: hold >7 data items + locate/correct an error in one structure, reversible *past* 𝕆 using the sedenion's CODE geometry (its Fano/PG structure), **not** its broken chirality. Shipped as a **Rosetta pair**: a pure-Python spec + a JPL-clean C peer, attested bit-exact.

- **New cascade ops `hamming_encode(data_bits, n)` / `hamming_syndrome(codeword)` / `hamming_decode_correct(codeword)`** over the **2ⁿ−1 ladder** (Hamming(7,4) / (15,11) / (31,26) / …). Single-error-correcting (minimum distance 3): every single-bit error in every position is located and corrected, and the payload recovers exactly. Canonical 1-indexed construction — parity bits at the power-of-two positions, the syndrome IS the flipped-bit position. A Hamming(15,11) carrier holds 11 data + 4 EC in one structure (1.57× the octonion's 7 reversible slots, F449); **Hamming(7,4) IS the octonion's own Fano plane** (F441). **Lean-ALU XOR-native** (GF(2) add = parity = XOR); no float, no libm, no `abs()`. Class **B** (structure framing) ∘ **I** (cyclic index arithmetic) ∘ **A** (content-addressed error locator).
- **Native C peer `srmech_hamming_{encode,syndrome,decode_correct}`** (`c/src/srmech_hamming.c`) — JPL Power-of-Ten clean (no goto/malloc, bounded loops, ≥2 asserts/fn, `-Wall -Wextra -Wpedantic -Werror`-clean), **no libm** (the C-transpile triality ratchet baseline stays ZERO). Attested **bit-exact** against the Python spec by `tests/test_cascade_hamming_parity.py` (encode vectors, syndrome, decode across the 2ⁿ−1 ladder). ABI-additive — **SRMECH_ABI_VERSION stays 3** (new symbols + one macro, ctypes `hasattr`-guarded).
- **Fences (F449):** the code carries the GF(2) sector/structure bits + EC; real-valued coefficients ride alongside (real-field EC = RS/BCH is a separate, larger construction). No multiplicative product — bind/couple stays `hypercomplex_couple`'s job (≤𝕆). Single-error correction per rung.

`describe()` total **237 → 240** (the three Hamming ops). SSoT: Hamming, R. W. (1950), Bell Syst. Tech. J. 29(2):147–160. Provenance: PR #687 §30 / F442 / F449.

## [0.7.2rc1] - 2026-06-06

**General/diagonal μ-axis for the QDFT/ODFT + a bidirectional `(σ,θ,μ)` hypercomplex coupler ([#908](https://github.com/lemonforest/mlehaptics/issues/908) §29; findings F436/F437).** The shipped `quaternion_dft` / `octonion_dft` exposed **named single μ-axes only** (`'i'|'j'|'k'|'ijk'`): a single axis *carries* N streams (round-trips) but does **not couple** them — perturbing the i-stream leaves the j,k spectra untouched (a complex FFT on the (1,μ) plane + an independent transform on the rest). This rc closes that gap.

- **`mu_axis` (and the ODFT `two_sided_right_axis`) now accept `'diagonal'` or a general unit pure-imaginary vector** — `'diagonal'` is the equal-weight axis of the active algebra (`(i+j+k)/√3` for ℍ, `(Σ_{n=1..7}eₙ)/√7` for 𝕆). A diagonal μ **couples** all streams: `μ·Σsₙeₙ` folds them into the real/anchor channel as a **joint coherence detector** (F436: coherent streams add ∝ n·s, incoherent cancel ∝ √n → anchor-energy ratio ≈ n; measured 3.0× at k=3, 7.0× at k=7). A general vector is normalised to unit length; e0 (and e4..e7 for the quaternion scope) must be zero. `_twiddle8` now carries all seven imaginary components (was i/j/k only), so a diagonal/general octonion μ is honoured. Existing named-axis behaviour is **bit-identical** (e4..e7=0).
- **New public op `srmech.amsc.cascade.hypercomplex_couple(streams, *, axis="diagonal", theta=π/2, sigma=1, form="left", inverse=False)`** — binds ≥3 streams into one quaternion/octonion + a joint coherence channel and **unbinds losslessly**. Bind (`sigma=+1`) applies `T=exp(σ·μ·θ)`; unbind (`sigma=-1`) applies the **conjugate** twiddle `exp(−μθ)` and recovers the input exactly via the division-algebra identity `x̄·(x·y)=‖x‖²·y` (F437) — **guaranteed reversible only up to 𝕆** (the Hurwitz boundary; sedenion zero-divisors break it) → lossless for **≤7 streams**. `form`/`inverse`/`sigma` are discrete points of the continuous `(σ,θ,μ)` family = the_one's `𝕊(σ,θ)` (F420) **plus the axis μ**. Class **M** (octonion multiply) ∘ **C** (σ/conjugation orientation) ∘ **N** (rational phase θ); **no new algebra, no abs()** — composite over the `qm.octonion` left/right-mult atoms.
- **These remain COMPOSITES** (prototype tier per #863): the 14-class A–N vocabulary is intact. Scientific tier (UPSTREAM §22): numpy is imported lazily on call, so `import srmech.amsc.cascade` stays numpy-free. `describe()` total **236 → 237** (one new tool-schema entry, `hypercomplex_couple`). **ABI unchanged** (Python-only cascade composite; no new C symbol). SSoT for the coupling math: Sangwine & Ell (2012) arXiv:1001.4379 (QDFT); Błaszczyk (2019) arXiv:1905.12631 (ODFT); the Hurwitz reversibility cap is Hurwitz (1898).

## [0.7.1] - 2026-06-05

**The Class-L Schur complement / Dirichlet-to-Neumann (DtN) map — the operator|operand FUSION op ([#897](https://github.com/lemonforest/mlehaptics/issues/897) §26).** Graduation of the rc1–rc3 arc: an op that keeps BOTH a spatial boundary and its spectrum (every other Class-L cascade only projects), integrates the bulk out, and lives on the boundary — `S = L_∂∂ − L_∂i·L_ii⁻¹·L_i∂`.

- **`srmech.amsc.laplacian.schur_complement(L, boundary_idx, *, exact=False)`** (alias `dirichlet_to_neumann`) — exact-rational `fractions.Fraction` solve (Class-N core; numpy-absent or `exact=True`) or the float `[scientific]`-tier realization; the area law is the dimensional reduction `n → |∂|`. (rc1)
- **DSL chain-contract wiring** — `schur_complement` is a first-class cascade-catalog stage; `chain().then("schur_complement", boundary_idx=[…])` / TOML chains thread `boundary_idx` + `exact` as bound stage kwargs (the 14th catalog op). (rc2)
- **Reusable native C peer `srmech_dense_solve_f64`** — the dense linear solve `A·X = B` the Schur/DtN float path composes over (the expensive interior solve IS an `A·X = B`), promoted to its own exported Class-L primitive. Gauss–Jordan with partial pivoting (Class-K magnitude sign-branch, no `fabs`/`abs()`); bounded `n,nrhs ≤ 256` thread-local workspace (no malloc, reentrant); no libm; JPL Power-of-Ten clean. New public op `srmech.amsc.laplacian.dense_solve(A, B, *, exact=False)`. (rc3)

`describe()` total **233 → 236** (schur_complement + dirichlet_to_neumann + dense_solve). **ABI stays 3** (additive symbol; the Python ctypes shim `hasattr`-guards it). Canonical SSoT: Zhang, *The Schur Complement and Its Applications* (2005) §0; Golub & Van Loan §3. Production cut of the **rc3** state already verified-green on TestPyPI (the pedantic-C / 4-cell test / pure-wheel matrix re-verifies the `0.7.1` build); no code change from rc3 — version-string graduation only.

## [0.7.1rc3] - 2026-06-05

**Native C peer for the Schur/DtN float path — a reusable `srmech_dense_solve_f64` Class-L primitive ([#897](https://github.com/lemonforest/mlehaptics/issues/897) §26).** The expensive part of the Schur complement is the interior solve `L_ii⁻¹·L_i∂`, which IS a dense linear solve `A·X = B`. rc3 ships that solve as its own exported Class-L C symbol (the "every primitive earns a C surface" path), and `schur_complement` becomes a genuine **composition** over it.

- **`c/src/srmech_dense_solve.c` → `srmech_dense_solve_f64(n, nrhs, A, B, out_X)`** — Gauss–Jordan with **partial pivoting** (the pivot magnitude is the Class-K pin-slot read — a sign *branch*, never `fabs()`/`abs()`); row-major doubles; bounded `n, nrhs ≤ 256` on a thread-local augmented workspace (the `srmech_hermitian_eigendecompose` precedent — no malloc, reentrant); a singular `A` returns `SRMECH_ERR_BAD_INPUT`. **No libm** — a solve is `+ − × ÷` only. JPL Power-of-Ten clean (no goto/malloc, ≤60-line factored helpers, ≥2 asserts each); ABI stays **3** (additive symbol, `hasattr`-guarded in the ctypes shim).
- **New public Python op `srmech.amsc.laplacian.dense_solve(A, B, *, exact=False)`** — float path dispatches to the native C peer (numpy fallback when absent / over-bound / singular); exact path is the bit-exact `fractions.Fraction` Gauss–Jordan (Class-N, promoted from rc1's `_solve_exact`). Accepts a matrix or vector RHS. One new tool-schema entry → `describe()` total **235 → 236**.
- **`schur_complement` now composes over `dense_solve`** for its interior solve (both exact and float paths) — the float interior solve runs native, the cheap boundary GEMM + subtract stay numpy. Same results: the rc1 worked instance `S = (1/3)[[1,−1],[−1,1]]` is unchanged. `tests/test_dense_solve_parity.py`: exact + numpy paths always run; native C parity (vs numpy + exact, `atol ≤ 1e-9`) runs where `libsrmech` is attached.

## [0.7.1rc2] - 2026-06-05

**Schur/DtN wired into the DSL chain contract ([#897](https://github.com/lemonforest/mlehaptics/issues/897) §26 follow-up).** The rc1 `schur_complement` op shipped only at `srmech.amsc.laplacian.schur_complement`; rc2 makes it a first-class **cascade-catalog stage** so it drives in a `chain().then(...)` / TOML chain like any other Class-L op. The chain runner resolves stage ops via `getattr(srmech.amsc.cascade, name)`, so the op is **re-exported flat** onto `srmech.amsc.cascade` (a DSL-resolution alias of the laplacian-registered op — *not* a second primitive, so it stays out of `cascade.__all__` and adds no tool-schema entry; `describe()` total holds at **235**).

- **`boundary_idx` + `exact` thread through as bound stage kwargs** — the data-first pattern (`schur_complement(L, *, boundary_idx, exact=False)`; the pipe fills `L`, the kwargs bind), exactly like `reorient`'s `orientation`. `boundary_idx` is required (no default) — a chain that omits it fails loudly with `TypeError`, never silently. A new descriptor `cascade_catalog/schur_complement.toml` (`class_composition = "L"`) makes it the **14th** catalog op (`srmech dsl ops` → `14 total`); `schur_complement` + `dirichlet_to_neumann` also join the documentary `LAPLACIAN_OPS` registry.
- **Tests** (`tests/test_schur_complement_dsl_stage.py`): `.then("schur_complement", boundary_idx=[0,3], exact=True)` and the equivalent TOML `[[stage]]` both reduce the path-4 graph Laplacian to `S = (1/3)[[1,−1],[−1,1]]` (exact `Fraction`, numpy-free); the float path is numpy-guarded. No ABI change (ABI stays **3**); the co-equal native C peer is the rc3 follow-up.

## [0.7.1rc1] - 2026-06-05

**Class-L Schur complement / Dirichlet-to-Neumann (DtN) map — the operator|operand FUSION op ([#897](https://github.com/lemonforest/mlehaptics/issues/897); UPSTREAM §26 / F412·F417·F419).** New `srmech.amsc.laplacian.schur_complement(L, boundary_idx)` (alias `dirichlet_to_neumann`) integrates the interior (bulk) out of a Laplacian and keeps the boundary effective operator

> `S = L_∂∂ − L_∂i · L_ii⁻¹ · L_i∂`

the discrete **Dirichlet-to-Neumann map** — give boundary values, it returns the boundary normal-derivative of their harmonic interior extension (*boundary data ⟹ the whole interior field*). Every other Class-L cascade only **projects** (a spatial graph → its cyclic spectrum, F417's one-way seam, dropping the spatial structure); Schur/DtN keeps **both** the spatial boundary and its spectrum — the *fusion*, not the projection. Holographic reading (F412): the bulk is integrated out, the effective theory lives on the boundary; the operator's size is `|∂|`, not `n` — the dimensional reduction `n → |∂|` **is** the area law.

- **Exact-rational core (Class-N).** With numpy absent — or `exact=True` — the interior solve `L_ii⁻¹·L_i∂` is **exact Gauss–Jordan elimination in `fractions.Fraction`** (division is exact rational, never a float reciprocal — F392; no `abs()`), and `S` is returned as `list[list[Fraction]]`. With numpy present (and `exact=False`) the float realization rides the `[scientific]` tier (`numpy.linalg.solve`) and `S` is an `ndarray`. Cascade-honesty: the inverse is Class C (conjugate) → Class K (`1/‖·‖²`); a singular interior block (an interior component disconnected from the boundary) raises `ZeroDivisionError`, not a silent NaN.
- **Area-law statement (precise).** For a pure graph Laplacian the DtN/Kron reduction inherits the all-ones null vector, so `rank(S) = |∂| − c` (`c` = connected components of the boundary-reduced graph; `= |∂| − 1` for a connected graph). The area law is the *dimensional* reduction `n → |∂|`, not a full-rank claim. Worked check: the two endpoints of a 3-edge unit-conductance path get `S = (1/3)·[[1,−1],[−1,1]]` exactly (effective conductance 1/3).
- Two new tool-schema entries → `describe()` total **233 → 235**. No ABI change (pure-Python; ABI stays 3). The DSL/compose-engine wiring and a co-equal C peer are the natural follow-up rcs (Python-first, like the loop family). Canonical SSoT: Zhang, *The Schur Complement and Its Applications* (2005) §0; Golub & Van Loan §3.2.

## [0.7.0] - 2026-06-05

**Production graduation of the v0.7.0 rc1–rc51 arc to PyPI.** The clean (non-rc) tag promotes the **rc51** state already verified-green on TestPyPI — the only delta from rc51 is this version string + entry, and the full pedantic-C (gcc/clang/MSVC) + 4-cell test matrix + pure-wheel build re-verify the `0.7.0` build before the production tag. ABI **3**; `describe()` total **233**.

**The v0.7.0 identity.** numpy is now **optional**: `pip install srmech` is numpy-free — the 14-class A–N cascade core (`srmech.amsc.*`) and the native C surface run with zero numpy; `pip install 'srmech[scientific]'` pulls numpy back in for the array-numerical tier (`srmech.qm.*` / `signal_processing.*` / `rbs_lm.*`). Every continuous-math op (trig, exp, sqrt, FFT, SVD, eig) is a **cascade of the 14**, and the shipped `libsrmech` holds **no libm transcendental** — the executable runs the Class-N cascade, not the C math library.

The arc, voxel by voxel:

- **MS #21 — the Moufang loop-bind / octonion gauge arithmetic (rc1–rc7).** `srmech.amsc.hdc` gains the octonion (Cayley–Dickson) product `loop_bind` + `loop_conj` / `loop_inv` / `loop_associator` / `loop_left_op` / `loop_right_op`; `cross7` (the 7-D cross product, `M∘C`) + the G₂ associative 3-form; the block-octonion HD tiling (`loop_bind_hd`, D=2048); compose-engine integration (the loop family resolves as `class="M"`); co-equal C peers in `c/src/srmech_loopbind.c`.
- **Perf + attestation discipline (rc8–rc20).** The Class-L circular autocorrelation primitive (Wiener–Khinchin); the N-way SIMD SHA-256 batch (AVX2 8-way / SSE2 4-way runtime cpuid dispatch, JPL-clean) routed through the new `c/src/srmech_simd.h` HAL — all platform/cpuid/target-attr bits live in the HAL, the core stays machine-agnostic; HAL constant-attestation (MPR derive-and-assert); native C peers for the HD loop family.
- **#797 ops + the §22 numpy-free cascade core (rc26–rc46).** `asymptotic_calculus` / `trigonometry` alias modules + a directed/signed-Laplacian eigen-op; the Klein-4 holographic-erasure code + the explicit order-3 triality-recursion corrector; the numpy-free HV carrier. The §22 arc makes **every** continuous-math op a cascade: QDFT/ODFT, laplacian-build + pure-Python Jacobi eigenvalues, dft/idft/kron, radix-2 Cooley–Tukey FFT, QR/SVD, lstsq/einsum/non-Hermitian eig; the `math.sqrt` + trig/π residue sweeps onto the Class-N rationals; the C-transpile coherence arc driving libsrmech's libm-transcendental count `23 → 0` (native C `srmech_sin`/`cos`/`atan`/`atan2`/`rational_sqrt`/`exp`/`log`).
- **numpy → optional (rc47–rc48).** numpy demoted from a hard dependency to the `scientific` extra, with a friendly `pip install 'srmech[scientific]'` gate at the scientific-tier import boundary; the #882 lazy-numpy fix (the Klein-4 HV-carrier path runs genuinely numpy-free on a plain install).
- **"The One" (rc49–rc50, [#887](https://github.com/lemonforest/mlehaptics/issues/887)).** `S(σ,θ) = ⨁ₙ(ℝ·1 ⊕ σ·e^{Îₙθ}·Im 𝔸ₙ)`, `dim = 2+4+8 = 14` — the single generator of the `1+3+7+3 = 14` substrate, shipped as a **Rosetta pair**: the numpy-free exact-rational `srmech.amsc.cascade.the_one` + the bit-exact `srmech.qm.hurwitz` matrix peer (`to_matrix() == hurwitz_matrix()`; `FANO_PLANES == hurwitz_planes()` derived from `octonion_mult_table`). The **0/1/3 finding**: `e^{Îₙθ}` is the algebra's own rotation → turns 0/1/3 Fano planes for ℂ/ℍ/𝕆; 𝕆 spins three planes at once (eigenvalues `{1, e^{±iθ}×3}`; the 7 = 1 fixed axis + 3×2 rotated). The ℂ/ℍ/𝕆 Hurwitz ladder = `so(8)` + Spin(8) triality (`Fix(τ) = g₂ = 14`).
- **PyPI README + description refresh (rc51).** Cut the QM/QFT/SM framing — every continuous-math op is a cascade of the 14, so no math domain is privileged or called out (the physics worked-examples still ship and stay discoverable via `describe()` / the tool-schema).

No code change from rc51; version-string graduation + this entry only.

## [0.7.0rc51] - 2026-06-05

**PyPI-facing README + project description refresh (pre-graduation).** Cuts the "canonical QM/QFT/SM operations" framing — every continuous-math op is a cascade of the 14, so no particular math domain is privileged or called out (it is all the same cascade). No code change; the physics worked-examples (`single_particle`/`spin`/`relativistic`/`propagators`/`gauge`/`sm`) still ship and remain discoverable via `describe()` / the tool-schema.

- **`[project].description`** (both `pyproject.toml` + `pyproject-pure.toml`, kept in lockstep) — rewritten to the v0.7.0 identity: *numpy-optional 14-class A-N vocabulary in native C + Python; every continuous-math op (trig/exp/sqrt/FFT/SVD/eig) is a cascade of the 14, no libm in the native build; **the One**, `S(σ,θ)`, generates the whole `1+3+7+3 = 14` substrate (the ℂ/ℍ/𝕆 Hurwitz ladder = `so(8)` + Spin(8) triality, bit-exact cascade↔matrix); AMSC (MPR v1).* ASCII-only, 438 chars (under the 480 soft cap).
- **`README.md`** — status banner refreshed `v0.6.0 → v0.7.0`; the QM/QFT/SM feature bullet replaced by **the continuous-math cascade + the One**; the `srmech.qm.*` section retitled **the substrate engine** (the ℂ/ℍ/𝕆 Hurwitz ladder, `so(8)` triality, the One) — `octonion`/`so8`/`triality` kept, **`hurwitz`** (the One's matrix peer, #887) added, the physics-ops enumeration dropped (with a domain-neutral note that they still ship, discoverable, un-privileged); stale `0.6.0` example outputs bumped to `0.7.0`.

No ABI / API change; `describe()` total unchanged at **233**.

## [0.7.0rc50] - 2026-06-05

**"The One" goes octonion-native — `S(σ,θ)`'s 𝕆 block is a 3-plane rotation, with a bit-exact qm-matrix Rosetta peer ([#887](https://github.com/lemonforest/mlehaptics/issues/887)).** rc49 used the simplest single-plane epicycle for every block; rc50 makes `e^{Î_nθ}` the **algebra's own** rotation — conjugation by the unit `cos(θ/2)+Î_n sin(θ/2)`, which turns *every Fano-triple plane through `Î_n`* by θ. The plane count is `0 / 1 / 3` for ℂ / ℍ / 𝕆: the single θ-turn spins **three planes at once in 𝕆** (eigenvalues `{1, e^{±iθ}×3}` on the imaginary part — the `1 fixed axis + 3×2 rotated` split of the 7). ℂ (σ-only) and ℍ (1-plane) are unchanged.

- **`srmech.amsc.cascade.one`** — the rotation now uses `FANO_PLANES` (the oriented Fano lines through each axis: ℍ `(1,2,+1)`; 𝕆 `(1,6,−1),(2,5,+1),(3,4,+1)` through `Î₃=e₇`), matching the fixed Cayley–Dickson-from-ℍ convention (Baez 2002 §2). `One.to_matrix()` is the full block-diagonal multi-plane operator; new `One.plane_counts` → `(0,1,3)` and `Block.rotated_planes`. The 𝕆 seed `e₁` now lands in its Fano plane `(1,6,−1)` → `cosθ·e₁ − sinθ·e₆` (the only rc49 behaviour change).
- **NEW `srmech.qm.hurwitz`** — the scientific-tier matrix peer: `hurwitz_matrix(σ, θ)` builds the same `14×14` `G(σ,θ)`, and `hurwitz_planes()` **derives** the planes straight from `octonion_mult_table` (not a hardcoded list). The cascade and the qm matrix agree **bit-for-bit** (`np.array_equal`), and the hardcoded `FANO_PLANES` equals the table-derived `hurwitz_planes()` — a genuine two-language cross-derivation (continuous-Hopf matrix vs discrete-cyclic cascade), not a restatement.
- No new primitive class (Class A planes ∘ N rational cos/sin ∘ K·C sign), no `abs()`. Two new tool-schema entries → `describe()` total **231 → 233**. No ABI change.

## [0.7.0rc49] - 2026-06-05

**"The One" — `S(σ,θ)`, the single generator of the 1+3+7+3 = 14 substrate ([#887](https://github.com/lemonforest/mlehaptics/issues/887)).** A new cascade-native surface `srmech.amsc.cascade.the_one` builds the unifying Hurwitz-ladder generator

> `S(σ,θ) = ⨁_{n=1}^{3} ( ℝ·1 ⊕ σ·e^{Î_nθ}·Im 𝔸_n )`,  `dim = Σ 2ⁿ = 2+4+8 = 14`

with `𝔸₁=ℂ, 𝔸₂=ℍ, 𝔸₃=𝕆` (the normed division algebras above ℝ). The decomposition **is** the A–N partition: the imaginary parts `Im 𝔸_n` (dims `1, 3, 7`) carry the anchor `A` / projection-triad `I,C,J` / detection-heptad `D,E,F,G,K,L,M`; the three `ℝ·1` real units are the **+3 grammar** `B, H, N`.

- **Numpy-free, exact-rational.** `e^{Î_nθ} = cos θ + Î_n sin θ` is built from the **Class-N** rational Taylor partials (`rational.{cos,sin}_series_truncate`) — every entry is a reduced `(num, den)` integer pair; no float until the opt-in `One.to_numpy()` / `One.to_matrix()` realisations (the `srmech[scientific]` tier, §22). No new primitive class — `⨁` over `n` is **Class I**, `σ` is **Class K** sign ∘ **Class C** apply (never `abs()`).
- **Structural prediction: n=1 degenerates to σ.** Fixing the rotation axis `Î_n = e_d` (the last imaginary unit) and rotating the `(e₁,e₂)` plane, at `n=1` the 1-D `Im ℂ` seed coincides with the axis → `θ` is inert and the only freedom is the chirality `σ` (the epicycle **is** the Class-K sign at the foundational algebra; richness grows `1→3→7`). Verified bit-exactly.
- **Returns a structured `One`** of three `Block`s tiling `1+3+7+3`; `.dim`, `.partition`, `.grammar_slots`, `.n1_is_sigma_only`, `.to_flat_rational()`. The qm-matrix Rosetta peer (`srmech.qm.hurwitz`) + the bit-exact cascade↔matrix parity test follow in rc50. No ABI change; `describe()` unchanged. Python-only (the C-transpile triality ratchet stays at 0).

## [0.7.0rc48] - 2026-06-05

**Fix [#882](https://github.com/lemonforest/mlehaptics/issues/882): `srmech.amsc.hdc` (Class M / Klein-4) — and three sibling `amsc` core modules — no longer crash raw on a plain (numpy-free) install.** rc47's numpy-optional capstone left four `srmech.amsc.*` modules with a top-level `import numpy as np`, so `import srmech.amsc.hdc` raised a raw `ModuleNotFoundError: No module named 'numpy'` instead of importing cleanly (the Klein-4 HV-carrier path is *designed* numpy-free) or gating like `srmech.qm`. rc47's AST ratchet used a hardcoded module list that missed them.

- **`srmech._scientific.lazy_numpy`** — a lazy numpy proxy: the holding module imports numpy-free; the **first numpy attribute access** imports numpy or raises the actionable `pip install 'srmech[scientific]'` hint. `srmech.amsc.{hdc, coupling, harmonics, cascade.matrix_cascades}` now use it.
- **Result, on a plain install:** the modules **import**; the **Klein-4 HV-carrier path** (`klein4_random` default-seed / `klein4_bind` / `klein4_bundle` / `klein4_similarity` / chirality / triality / holographic) runs **genuinely numpy-free**; the bipolar `polar_*` HDC + the loop family + the QR/SVD/lstsq/einsum/eig matrix cascades raise the clean `[scientific]` hint when called. The issue's preferred option (a).
- **Ratchet broadened** — `test_numpy_optional_rc47.py` now walks the **whole `srmech/amsc/**`** subtree for module-level numpy imports (closing rc47's hardcoded-list hole), plus a numpy-blocked behavioral test (import + Klein-4 numpy-free + the `[scientific]` hint). numpy-present behavior unchanged; no ABI change; `describe()` stays **230**.

## [0.7.0rc47] - 2026-06-05

**numpy is now an OPTIONAL dependency — the §22 capstone.** The §22 + C-transpile arcs (rc29–rc46) made the **Class-N cascade core numpy-free**: `srmech.amsc.*` (the A-N primitives, the rational/cyclic/laplacian cascades) and the native C surface run with **zero numpy**. rc47 demotes numpy from a hard dependency to the **`scientific`** extra. `pip install srmech` is now numpy-free; `pip install 'srmech[scientific]'` pulls it back in for the array-numerical scientific tier (`srmech.qm.*` / `srmech.signal_processing.*` / `srmech.rbs_lm.*`).

- **`pyproject.toml` + `pyproject-pure.toml`** — numpy moved out of `dependencies` into `optional-dependencies.scientific`. The `dev` + `tests` extras keep numpy (the full suite exercises the scientific tier). No ABI change; `describe()` stays **230**.
- **Friendly gate** — new numpy-free `srmech._scientific.require_numpy`; the scientific-tier subpackages (`qm` / `signal_processing` / `rbs_lm`) call it at import so a no-numpy install fails with `pip install 'srmech[scientific]'`, not an opaque `No module named 'numpy'`. `ImportError` (numpy's own error subclasses it), so existing handlers keep working.
- **CI guard** — the pure-wheel "Verify wheel installs + imports" job now asserts numpy is **absent** from the base install, that the cascade core works numpy-free, and that the scientific tier raises the actionable hint. New `test_numpy_optional_rc47.py` pins the pyproject contract + the gate + an AST ratchet that the cascade core never imports numpy at module top.

This is the last planned rc of the v0.7.0 line. **Graduation to production PyPI is held** for a dedicated testing pass.

## [0.7.0rc46] - 2026-06-05

**The C-transpile triality closeout — the executable runs the Class-N cascade, not libm (C ratchet → 0).** The shipped `libsrmech` now holds **no libm transcendental**: the notebook, the C+Python source, and the native executable all agree. ABI stays 3 (additive `srmech_exp`/`srmech_log`); `describe()` stays **230**.

- **New `c/src/srmech_explog.c`** → `srmech_exp` / `srmech_log`, the double→double Class-N exp/log cascades (the last two libm calls in the library):
  - `srmech_exp(x)` — range-reduce `x = n·ln2 + r` (`|r| ≤ ln2/2`, two-word Cody–Waite `ln2`), `exp(r)` via a **Q61 integer Taylor** `1 + r + r²/2! + …`, then `· 2^n` with the power-of-two built straight into the IEEE exponent field (no `ldexp`). Overflow → `+Inf`, underflow → `0`.
  - `srmech_log(x)` — read `x = m·2^e` **exactly from the bit pattern** (no `frexp`), fold `m` into `[1/√2, √2)`, `log(m) = 2·atanh((m−1)/(m+1))` via a **Q61 integer atanh series**, then the `e·ln2` recombine (two-word `ln2`). Non-positive `x` → `SRMECH_ERR_BAD_INPUT` (NaN / −Inf).
  - No libm, no `abs()` (Class-K sign-branch). Machine-ε vs libm (exp rel err ≤ 2.3e-16; log abs err ≤ 2.3e-16 over 500k values; `exp(log(x))` round-trips ≤ 2.3e-16).
- **`srmech_laplacian.c` repointed** — the elementwise `exp`/`log` → `srmech_exp`/`srmech_log`; `#include <math.h>` dropped (the file now holds no libm). **Class L composes Class N in the executable.**
- **`srmech_kepler.c`** — the last `fabs` (Newton convergence test) → an explicit **Class-K sign-branch**; `#include <math.h>` dropped (no libm in the file).
- **C ratchet `test_c_cascade_coherence.py` → 0** (`23 → 16 → 13 → 3 → 0` across rc43–rc46). The guard now also covers the C99 **complex** libm (`csin`/`ccos`/`cexp`/`csqrt`/…) and any `<complex.h>` include, so a future complex op can't silently reintroduce libm. JPL-clean; pedantic `-Werror`/`/WX` clean.

**Next (the capstone, human-gated):** the numpy→`srmech[scientific]` optional-dependency flip, then the clean `v0.7.0` graduation to production PyPI.

## [0.7.0rc45] - 2026-06-05

**Native sqrt cascade — the Jacobi eigensolver runs the Class-N integer-sqrt, not libm (C-transpile triality, arc step 3).** ABI stays 3 (additive `srmech_rational_sqrt`); `describe()` stays **230**.

- **New `c/src/srmech_sqrt.c`** → `srmech_rational_sqrt` — `sqrt(x)` (x≥0) via an **integer floor-isqrt** on a scaled radicand: `x = M·2^e` read from the bit pattern, `root = isqrt(M<<54)` via a **portable two-limb 128-bit integer square root** (restoring binary, 64 bounded iterations, no division, **no `__int128`**), projected by `(double)root·2^(e/2−27)` with the power-of-two built directly from the IEEE exponent field (no `ldexp`). No libm, no float sqrt. Machine-ε vs libm (rel err ≤ 2.2e-16 over 500k values; `1/√d` bit-exact).
- **`srmech_laplacian.c` repointed** — the **8 cyclic-Jacobi `sqrt`** (off-diagonal norm + rotation angles) → a `lap_sqrt` wrapper over the cascade; the **elementwise `cos`/`sin`** → `srmech_cos`/`srmech_sin`. **Class L now visibly composes Class N in the executable.** Jacobi spectrum vs `numpy.linalg.eigvalsh` unchanged.
- C ratchet baseline **13 → 3** (laplacian 12 → 2: only `exp` + `log` remain). JPL-clean; pedantic `-Werror`/`/WX` clean.

**Roadmap (rc46, the closeout):** a C `exp` double-wrapper over `srmech_exp_series_truncate` + a C `log` (`log1p`-series + integer exponent) → repoint the laplacian signed/magnetic phase; `fabs`→Class-K sign-branch (`srmech_kepler.c`); the complex-libm guard (`csin`/`ccos`/`cexp`/`csqrt`) → **C ratchet 0**, executable fully on the cascade. Then the numpy→`srmech[scientific]` capstone.

## [0.7.0rc44] - 2026-06-05

**Native Kuramoto step runs the trig cascade, not libm (C-transpile triality, arc step 2).** ABI stays 3; `describe()` stays **230**. `srmech_cascade_kuramoto_step_f64` / `_general_f64` now compute their coupling `sin` via the rc43 Class-N cascade.

- **`srmech_kuramoto.c` repointed** — the 3 libm `sin` sites (mean-field coupling `Σ sin(θⱼ−θᵢ)`, the generalised Sakaguchi `Σ Aᵢⱼ·sin(θⱼ−θᵢ−α)`, and the per-oscillator pinning `pᵢ·sin(ψᵢ−θᵢ)`) → `srmech_sin`; `#include <math.h>` dropped (no other libm in the file).
- **#784 / F234 non-regression confirmed** — the Kuramoto-coupled-adder differential test (`test_kuramoto_step.py`, the "tile nibbler") stays green with the native cascade-trig (18 passed). The defaults still reproduce the plain step.
- C ratchet `test_c_cascade_coherence.py` baseline **16 → 13** (kuramoto 3 → 0). JPL-clean; pedantic `-Werror`/`/WX` clean.

**Roadmap:** rc45 `srmech_rational_sqrt` (integer-Newton) → `srmech_laplacian.c` (sqrt×8 Jacobi + the cos/sin/exp phase); rc46 `fabs`→Class-K sign-branch + the complex-libm guard (`csin`/`ccos`/`cexp`/`csqrt`) → C ratchet **0**. Then the numpy→`srmech[scientific]` capstone.

## [0.7.0rc43] - 2026-06-05

**Native C trig cascade — the executable runs the Class-N cascade for trig, not libm (C-transpile triality, rc42→rc46 arc step 1).** ABI stays 3 (additive C symbols); `describe()` stays **230** (no Python tools). The first *behavioural* C port: on a native install `kepler.{pin_slot,kepler_solve,equation_of_centre}` now compute `sin`/`cos`/`atan2` via the cascade, closing the kepler row of the executable-coherence gap.

- **New `c/src/srmech_trig.c`** → `srmech_sin`/`srmech_cos`/`srmech_atan`/`srmech_atan2` (double→double, status-returning). The **cyclic range-reduction (mod π/2) is pure INTEGER** (user direction "prefer ints over float always for cyclic algebra"): the IEEE-754 input is read as an exact `M·2^E` from its bit pattern (no `frexp`), the octant `k` comes from an integer wide-multiply (portable 64×64→128, no `__int128`/`_umul128`) by a high-precision cascade `2/π`, the remainder is an exact integer fraction; the Class-N Taylor runs in **Q61 fixed-point**; **float appears only at the final `(double)sum/2^61` projection**. π from the Archimedes pi-cascade (derive-and-assert constants). No libm, no `abs()` (Class-K sign-branch). Validated vs libm to machine ε — **sin 5.3e-19, cos 8.1e-20, atan 2.2e-16, atan2 0.0 bit-exact** across 200k+ angles.
- **`srmech_kepler.c` repointed** — 7 trig sites (`cos`×2, `sin`×4, `atan2`×1) → the cascade; native `pin_slot` is bit-exact (0.0) vs libm and the Kepler residual holds at 0.0. (The `fabs` stays for rc46.)
- **C ratchet** `test_c_cascade_coherence.py` baseline **23 → 16** (kepler 8 → 1). New ctypes parity test `test_native_trig_rc43.py`. JPL Power-of-Ten clean (≤60-line fns, ≥2 asserts); pedantic `-Werror`/`/WX` clean. Kuramoto native step (#784) confirmed green pre-touch (rc44 target).

**Roadmap:** rc44 repoints `srmech_kuramoto.c` (sin×3, watching the F234 differential test); rc45 adds `srmech_rational_sqrt` → `srmech_laplacian.c`; rc46 `fabs`→sign-branch + the complex-libm guard (`csin`/`ccos`/`cexp`/`csqrt`) → C ratchet 0. Then the numpy→`srmech[scientific]` capstone.

## [0.7.0rc42] - 2026-06-05

**C-transpile triality coherence — start the native/executable-tier port, ratchet-first.** Pure tooling+docs; no new tools (`describe()` stays **230**); ABI stays 3; no C *behaviour* change yet. Opens the rc42→rc46 arc that makes the **executable** layer run the Class-N cascade, not libm.

- **The gap rc40/rc41 didn't close.** Those sweeps were Python-only (AST ratchets walk `*.py`). On a native install (`HAS_NATIVE=True` — the default) `kepler.{pin_slot,kepler_solve,equation_of_centre}` / `cascade.kuramoto_step` / signed-Laplacian dispatch to **C** peers that still call libm `sin`/`cos`/`atan2`/`sqrt`/`pow`/`fabs`. So the three coherence layers — notebook / C+Python source / executable — agree numerically (rational ≡ libm to machine ε, which masked it) but the C isn't a faithful *transpile* of the cascade. Only `exp` already coheres (`srmech_exp_series_truncate`).
- **New ratchet** `tests/test_c_cascade_coherence.py` — a **DOWN-only baseline** ratchet (same shape as `test_jpl_audit.py`) over the shipped library `c/src`+`c/include` (`c/test/*` excluded). Records the current **23** libm/π sites (`srmech_kepler.c` 8 + `srmech_kuramoto.c` 3 + `srmech_laplacian.c` 12); each file's count + the total only go DOWN, and no new C file may introduce libm transcendentals. Ships green (baseline = reality) — the gap is now measured + visible.
- **Notebook** `notes/continuous_math_as_14_class_cascade.md` — new "C-transpile triality coherence" section: the three-layer coherence model + the per-op table + the rc42→rc46 roadmap, grounded in the RBS-LM `native-algebra compute surface` findings (F305/F306, PR #687, read-only).

**Roadmap (rc43–rc46):** `srmech_{sin,cos,atan,atan2}_series_truncate` + C `pi_cascade` → repoint `srmech_kepler.c` (rc43); `srmech_kuramoto.c` (rc44); `srmech_rational_sqrt` → `srmech_laplacian.c` (rc45); `fabs` → Class-K sign-branch, C ratchet → 0 (rc46). Then the numpy→`srmech[scientific]` optional-dependency-flip capstone. New C symbols are additive (ABI stays 3).

## [0.7.0rc41] - 2026-06-05

**`math.{sin,cos,atan2}` + `math.pi` trig/π residue sweep — route continuous trig + π through the Class-N cascade, not libm.** Pure refactor; no new tools (`describe()` stays **230**); ABI stays 3. The companion to rc40's `math.sqrt` sweep, closing the §22 libm-scalar-math audit: now that `rational.{sin,cos,tan,atan,atan2}` (rc33) + the `pi_cascade` exist, every remaining libm trig / π reference in shipped srmech is routable to its exact Class-N peer.

- **14 sites routed across 4 modules** — verified machine-ε vs libm before routing (sin 7.8e-16, cos 6.7e-16, atan2 4.4e-16 across all quadrants + multiple periods; the cascade-π float is **bit-exact 0.0** vs `math.pi`):
  - `amsc/kepler.py` ×7 — `cos`/`sin`/`atan2` in the **pin-slot** transform + the **Kepler-equation** Newton solver + the equation-of-centre series → `rational.{cos,sin,atan2}`. The iterative solver is the sensitive case (trig accuracy gates Newton convergence): `pin_slot` is **bit-exact 0.0** vs libm and the Kepler residual `|E − e·sinE − M|` holds at 4.4e-16. (The Class-K Newton-step magnitude was already an explicit sign-branch, never `abs()`.)
  - `amsc/cascade/compose.py` ×3 — the `sin` in the Kuramoto-coupling DSL worked examples → `rational.sin` (`math.fsum` stays — exact numerical sum, no transcendental peer).
  - `amsc/cascade/hypercomplex_dft.py` ×2 + `math.pi` ×1 — the quaternion/octonion twiddle `exp(μθ)=cosθ + μ·sinθ` + the `2π` factor → `rational.{cos,sin}` + a cascade-π float (`pi_cascade_digits(30)` projected once at import). `import math` dropped.
  - `signal_processing/form_function_rotation.py` ×1 — the `math.pi` in the fundamental-mode eigenvalue `exp(−2πi·composed/D)` → cascade-π (its trig was already `rational.cos/sin`). `import math` dropped.
- **Ratchet** `test_no_math_trig_pi_anywhere_in_srmech` (AST) — no `math.{sin,cos,tan,asin,acos,atan,atan2,exp,pi,tau}` reference (call **or** bare constant) anywhere in shipped srmech; only goes DOWN to zero. `math.{gcd,isqrt,fsum}` (exact integer / numerical helpers — `isqrt` even powers `rational.py`'s own sqrt cascade) are deliberately NOT flagged.
- **Audit note** `notes/sqrt_sweep_rc40.md` — the rc41 residue section marked routed; the libm-scalar-math audit (26 references across 8 files) is now fully swept (12 sqrt @ rc40 + 14 trig/π @ rc41).

**With rc41 the libm-scalar-math discipline is complete** — no `math.{sqrt,hypot,sin,cos,tan,atan,atan2,exp,pi,tau}` anywhere in shipped srmech; continuous scalar math routes through the A–N cascade (`rational.*` + the `pi_cascade`), with numpy/cmath retained only for genuinely-vectorised or complex-root ops that have no scalar-cascade peer. **Roadmap:** the numpy→`srmech[scientific]` optional-dependency-flip capstone. No new C symbols.

## [0.7.0rc40] - 2026-06-05

**`math.sqrt` scalar-site retrofit sweep — route the scalar root through the Class-N cascade, not libm.** Pure refactor; no new tools (`describe()` stays **230**); ABI stays 3. The §22 discipline closeout (sibling of the rc32 `abs()`-sweep and rc33 numpy-math-sweep): now that `rational.sqrt`/`hypot` exist (rc35), every `math.sqrt` in shipped srmech is routable to its exact Class-N peer.

- **12 `math.sqrt` call sites routed → `srmech.amsc.rational.sqrt`**, across 5 modules:
  - `amsc/laplacian.py` ×5 — the cyclic-Jacobi eigensolver's off-diagonal norm + rotation angles. **Class L now visibly composes Class N** (its leaf root is the rational sqrt). Jacobi vs `numpy.linalg.eigvalsh` = 8.9e-16.
  - `qm/bell.py` ×2 (Tsirelson `2√2`, `1/√2`), `qm/octonion.py` ×1 (`octonion_norm`), `qm/sm.py` ×3 (Higgs vev / Z-mass / Yukawa), `amsc/cascade/hypercomplex_dft.py` ×1 (`1/√3`) — all bit-exact 0.0 vs libm (`rational.sqrt` is machine-ε at 64 precision bits). All 12 args are provably non-negative (guards / sums-of-squares), so `rational.sqrt`'s raise-on-negative is a safe drop-in.
- **Ratchet** `test_no_math_sqrt_hypot_anywhere_in_srmech` (AST) — `math.sqrt`/`math.hypot` calls only go DOWN to zero. `cmath.sqrt` (complex root, the rc39 eigvals shift) and `np.sqrt(array)` (bulk-array, no scalar peer) are NOT flagged.
- **Audit note** `notes/sqrt_sweep_rc40.md` — the full AST audit found 26 routable `math.*` references; the 12 sqrt are routed here, the **14 trig/pi residue** (`math.{sin,cos,atan2}` ×12 in kepler/compose/hypercomplex_dft + `math.pi` ×2) are STAGED to **rc41** (a different primitive family with its own anchor concerns + kepler's iterative solver). `rational.py`/`pi_cascade.py`/`trigonometry.py` have ZERO real libm calls — the float-trig cascades are genuinely libm-free.

**Roadmap:** rc41 = the `math.{sin,cos,atan2}`/`math.pi` trig-residue sweep onto `rational.{sin,cos,atan2}` + `pi_cascade`; then the numpy→`srmech[scientific]` dependency-flip capstone. No new C symbols.

## [0.7.0rc39] - 2026-06-05

**`lstsq` + `einsum` + non-Hermitian `eig` — the remaining linear-algebra layer as A–N cascades.** ABI stays 3; `describe()` 227 → **230** (+3 tools). numpy is the array **container** only — no `np.linalg.{lstsq,eig,eigvals}` in the call graph (AST guard).

- **New** in `srmech.amsc.cascade.matrix_cascades`:
  - **`lstsq`** — least-squares `min‖A x − b‖` = **{QR}** factorization (rc38's `qr`) ∘ **Class M** (the `Qᴴ b` product) ∘ **Class I** (back-substitution, the ordered triangular solve). Overdetermined/square `m ≥ n`; `b` a vector or a stack of RHS. Matches `numpy.linalg.lstsq(a,b)[0]` to ~1e-15.
  - **`einsum`** — the tensor contraction = **Class B/D** (the subscript string is a typed index-pattern spec) ∘ **Class I** (iterate over every free + summed index tuple) ∘ **Class M** (the sum-of-products bundle). The *general* index-iteration definition — handles any subscript string (matmul `ij,jk->ik`, trace `ii->`, transpose `ij->ji`, dot `i,i->`, outer `i,j->ij`, batched `ijk,kl->ijl`, implicit output), just unoptimised. Bit-exact / machine-ε vs `numpy.einsum`.
  - **`eigvals`** — non-Hermitian eigenvalues via the **shifted-QR iteration**: **Class K** (iterate-to-convergence asymptotic-DoF) ∘ **Class L** (the spectral content) ∘ **{QR}** (the per-step Householder factorization) ∘ **Class C** (the Wilkinson spectral shifts). Runs in complex arithmetic, so complex eigenvalues of *real* matrices fall out directly — the 2-D rotation `[[0,−1],[1,0]]` yields `±i`. The eigenvalue multiset matches `numpy.linalg.eigvals` to ~1e-12 (Hermitian inputs are the already-shipped exact special case = pure **Class L**, the cyclic Jacobi).
  - **MCP-callable** — params are `np.ndarray`/`str`/`int`/`tuple[np.ndarray,…]`, all with existing coercers.
- **Tests** `tests/test_lstsq_einsum_eig_rc39.py` (+10): lstsq overdetermined/square/multi-RHS vs numpy, einsum across 9 subscript shapes + complex, eigvals multiset-match across 20 random real+complex matrices, complex-conjugate-pair-of-real, empty/scalar/non-square edges, AST guard.

**With rc39 the `continuous_math_as_14_class_cascade` table is complete** — every op once parked in the §22 "scientific tier" (exp/cexp/sqrt/hypot/DFT/FFT/kron/QR/SVD/lstsq/einsum/eig) now has a shipped A–N cascade. **Roadmap:** rc40 = the codebase-wide `math.sqrt`/`np.hypot` scalar-site retrofit sweep onto `rational.{sqrt,hypot}` (focused discipline pass); then the numpy→`srmech[scientific]` dependency-flip capstone. No new C symbols.

## [0.7.0rc38] - 2026-06-05

**QR + SVD as A–N cascades — the matrix factorizations, built on srmech's own roots + eigendecomposition.** ABI stays 3; `describe()` 225 → **227** (+2 matrix tools). numpy is the array **container** only — there is no `np.linalg.qr`/`np.linalg.svd` anywhere in the call graph (an AST guard enforces it).

- **New** `srmech.amsc.cascade.matrix_cascades.{qr, svd}`:
  - **`qr`** — `A = Q·R` via **Householder reflections**. Q is a product (**Class M**) of elementary reflectors `H = I − β·v·vᴴ`; each reflector is **Class K** (the sign-flip across a hyperplane) ∘ **Class M** (the outer-product `v·vᴴ` bind) ∘ **Class N** (the `2/(vᴴv)` scale, the column norm a `rational.sqrt`). The phase choice `α = −phase·‖x‖` is the **Class K** pin-slot that avoids cancellation. `mode='reduced'` (default, matching `numpy.linalg.qr`) / `'complete'`. Real + complex.
  - **`svd`** — `A = U·diag(s)·Vᴴ` reached from the Hermitian eigendecomposition of the Gram matrix: **Class L** (`hermitian_eigendecompose` of `AᴴA` or `AAᴴ` — srmech's cyclic-Jacobi cascade) ∘ **Class N∘K** (`s = √eigvals` via `rational.sqrt`) ∘ **Class M** (`U = A·V·Σ⁻¹`).
  - **Verified by INVARIANTS, not by element-wise numpy match** (QR/SVD are unique only up to signs): reconstruction `Q·R = A` / `U·diag(s)·Vᴴ = A` to ~1e-15, orthonormality `Qᴴ Q = I` / `Uᴴ U = I` to ~1e-14, R upper-triangular — and the singular VALUES (which *are* unique) match `numpy.linalg.svd` to round-off. The Gram route squares the condition number, so very small singular values carry √ε-scale error (documented caveat).
  - **MCP-callable** — params are `np.ndarray`/`str`/`bool`, all with existing coercers; the every-tool smoke covers both.
- **Tests** `tests/test_matrix_cascades_rc38.py` (+8): QR/SVD invariants across real+complex and 7 shapes, complete-mode, singular-value match vs numpy, empty, AST guard (no `abs()`, no `np.linalg.{qr,svd,eig,…}`).

**Roadmap:** rc39 = `lstsq` (`{QR}∘M∘I` back-substitution) + `einsum` (`B/D∘I∘M` index-iteration) + non-Hermitian `eig` (`K∘L∘{QR}∘C`, the shifted-QR iteration); rc40 = the codebase-wide `math.sqrt`/`np.hypot` scalar-site retrofit onto `rational.{sqrt,hypot}` (a focused discipline pass, like the rc32 abs-sweep / rc33 numpy-math-sweep). The numpy→`srmech[scientific]` dependency-flip is the capstone. No new C symbols.

## [0.7.0rc37] - 2026-06-04

**The FFT butterfly = the DFT cascade + Class J + Class K.** Pure-Python; ABI stays 3; `describe()` 223 → **225** (+2 FFT tools).

- **New** `srmech.amsc.cascade.spectral_cascades.{fft, ifft}` — the **radix-2 Cooley–Tukey** butterfly. Bit-for-bit the same *mathematics* as rc36's `dft` (and value-faithful to `numpy.fft.fft`/`ifft` to ~3e-14, machine ε), but `O(N log N)` when `N` is a power of two: the decimation-in-time even/odd split `x[0::2]` / `x[1::2]` is **Class J** (the radix `N = 2·(N/2)` factorization), the recursion is **Class K** (the butterfly depth), the twiddle `e^(∓2πi·k/N)` is the same `cexp` = **Class N** ∘ **Class C**, and the butterfly `E ± t·O` is **Class M** (bundle add) ∘ **Class K** (pin-slot sign-flip). No `math.pi`/`np.pi` in the call graph (π from the cascade).
- **Full-coverage at any length** — for non-power-of-2 `N` (3, 5, 7, 13, …) `fft` falls back to rc36's direct `O(N²)` `dft`, so it is a true drop-in for `numpy.fft.fft`/`ifft` at *any* `N`, not just powers of two. (The general mixed-radix butterfly — full Class J over `N`'s prime factorization — is the follow-on refinement.)
- **MCP-callable** — `fft`/`ifft` reuse rc36's `list[complex]` coercer; no new coercion handler needed.
- **Tests** `tests/test_fft_radix2_rc37.py` (+7): fft/ifft vs numpy across power-of-2 AND non-power-of-2 lengths, fft≡dft agreement, ifft∘fft round-trip, empty, `_is_power_of_two` exhaustive 1..129, AST no-libm-π guard.

**Roadmap:** rc38 = QR (Givens/Householder) + SVD (from `hermitian_eigendecompose`) + the `math.sqrt`/`np.hypot` scalar-site sweep onto `rational.{sqrt,hypot}`; rc39 = non-Hermitian eig + lstsq + einsum; the numpy→`srmech[scientific]` dependency-flip is the capstone. No new C symbols.

## [0.7.0rc36] - 2026-06-04

**The DFT as the Antikythera epicycle-sum + Kronecker, as A–N cascades — plus a Bio-TOTP test-flake root-cause + fix.** Pure-Python; ABI stays 3; `describe()` 220 → **223** (+3 spectral cascade tools).

- **New numpy-free spectral cascades** `srmech.amsc.cascade.spectral_cascades.{dft, idft, kron}` (built on rc34's `cexp`):
  - **`dft` / `idft`** — the discrete Fourier transform IS the Antikythera epicycle-sum (`[[user_stance_epicycle_via_gear_plus_pin]]`): `X_k = Σ_n x_n · e^(∓2πi·(k·n mod N)/N)` = **Class I** (the cyclic index `k·n mod N`) ∘ **Class N** (the twiddle cos/sin) ∘ **Class C** (the imaginary-unit 90° rotation) ∘ **Class M** (the bundle/superposition sum). Direct `O(N²)`; matches `numpy.fft.fft`/`ifft` to ~3e-15 (machine ε). No `math.pi`/`np.pi` in the call graph (the twiddle angle draws π from the cascade). The radix-2 `O(N log N)` butterfly (adds Class J + Class K) is the follow-on.
  - **`kron`** — Kronecker product `A⊗B` = **Class I** (mixed-radix index) ∘ **Class M** (element products). Bit-exact vs `numpy.kron`.
  - **MCP-callable**: the new `list[complex]` / `list[list[complex]]` param types get real inbound coercers in `srmech.mcp._coercion` (each complex scalar rides as `[re, im]`), so all three tools are invocable over the MCP / Anthropic surface (the every-tool invocation smoke covers them).
- **Bug fix (test-only): Bio-TOTP flaky test root-caused.** `test_bus.py::test_bio_totp_decrypt_rejects_channel_id_mismatch` was intermittently failing with `DID NOT RAISE` (~1/8). Root cause: the test runs in **permissive** mode (`strict=False`) and used the **real wall clock**, so `encrypt`/`decrypt` could straddle a TOTP window boundary — the wrong-window decrypt yields garbage that fails the UTF-8/JSON parse, so the binding fields read as *absent* and permissive mode accepts (routing around the present-but-mismatched rejection the test exercises). **The cipher and the secure `strict=True` bus path are unaffected** (strict mode rejects garbage). Fixed by pinning `time_ns` (the same hook every deterministic sibling test already uses) on this test and the sibling replay test; verified deterministic over 80 executions.
- **Tests** `tests/test_spectral_cascades_rc36.py` (+6): dft/idft vs numpy.fft, idft∘dft round-trip, kron vs numpy.kron, AST no-libm-π guard.

**Roadmap:** rc37 routes the ~32 `math.sqrt`/`np.hypot` sites + the radix-2 FFT + QR/SVD; the numpy→`srmech[scientific]` dependency-flip is the capstone. No new C symbols.

## [0.7.0rc35] - 2026-06-04

**`sqrt`/`hypot` cascade primitives + module rename `asymptotic_calculus` → `calculus`.** Pure-Python; ABI stays 3; `describe()` 218 → **220** (+2 root tools).

- **New substrate-native roots** — `srmech.amsc.rational.{sqrt, hypot}` (re-exported from `srmech.calculus`). `sqrt(x)` (x ≥ 0) is Newton-Raphson realised as an **integer** floor-isqrt on a scaled-bignum radicand — **Class-N** rational arithmetic ∘ **Class-K** sqrt-convergence; no `math.sqrt`/`np.sqrt` in the call graph (AST-guarded); negative `x` raises a domain error. `hypot(a, b) = √(a²+b²)` = **Class-M** sum-of-squares bind ∘ the Class-N sqrt (the complex modulus `|z| = hypot(z.real, z.imag)`). Both **bit-exact** vs libm in testing.
- **Module rename `asymptotic_calculus` → `calculus`** (no-break). The continuous-calculus surface is now `srmech.calculus`; `srmech.asymptotic_calculus` remains a **back-compat re-export alias** (same function objects). The "asymptotic" qualifier was an early framing that singled out this one module while the whole framework is equally substrate-native asymptotic-rational (trig, exp, the eigen ops, the FFT-as-epicycle-sum) — the insight is framework-wide now (see `docs/srmech/notes/continuous_math_as_14_class_cascade.md`), so the module is simply `calculus`. `srmech.trigonometry` (the trig subset) is unchanged.
- **Tests** `tests/test_sqrt_rename_cascade_rc35.py` (+6): sqrt/hypot vs libm + negative-domain raise + AST no-libm-sqrt guard; `calculus` canonical surface; `asymptotic_calculus` is a true alias (identical callables + `__all__`).

**Roadmap (per the derivation note):** rc36 routes the ~32 `math.sqrt`/`np.hypot` sites onto the cascade + builds the direct-DFT (the Antikythera epicycle-sum, on `cexp`) + `kron`; rc37 QR + SVD; rc38 non-Hermitian eig + lstsq + einsum; the numpy→`srmech[scientific]` dependency-flip is the capstone. No new C symbols.

## [0.7.0rc34] - 2026-06-04

**"Continuous math is a cascade of the 14 A–N class operations" — the complex-exponential keystone, plus the derivation that dissolves the "scientific tier."** Pure-Python additions; ABI stays 3; `describe()` 215 → **218** (+3 exp tools).

- **New substrate-native exp family** — `srmech.amsc.rational.{exp, cexp, complex_exp}` (re-exported from `srmech.asymptotic_calculus`). `exp(x)` = Class-N Taylor with **K** argument-halving range reduction (`e^x = (e^(x/2^k))^(2^k)`, no irrational constant); `cexp(θ) = cos θ + i·sin θ` = **N**(rc33 trig) ∘ **C**(imaginary-unit 90° rotation, Euler); `complex_exp(z) = e^(z.real)·(cos z.imag + i·sin z.imag)`. No `math.exp`/`cmath.exp`/`np.exp` in the call graph (AST-guarded). Matches libm to machine ε (`cexp`/`complex_exp` ~3–9e-16; real `exp` ~1e-9 absolute at e¹⁵, machine-ε relative). **This is the keystone**: every `np.exp(1j·…)` time-evolution phase and every DFT twiddle factor IS a `cexp`.
- **Derivation note** `docs/srmech/notes/continuous_math_as_14_class_cascade.md` — derives the A–N cascade for **every** op previously called "scientific-tier / numpy-only": `exp` (N∘K), trig (N∘I∘C∘K), `complex-exp` (N∘C), `sqrt` (N∘K), **DFT/FFT** (M∘{N∘C}∘I∘J∘K — the Antikythera epicycle-sum), **QR** (M∘C∘N∘K), **SVD** (L∘N∘K∘M, reachable from `hermitian_eigendecompose`), **non-Hermitian eig** (K∘L∘{QR}∘C), **lstsq** ({QR}∘M∘I), **kron** (I∘M), **einsum** (B/D∘I∘M). Per the two-language MFO/srmech framework there are exactly **14** irrep class operations — so none of these is a primitive srmech lacks; each is a not-yet-derived *composition*. The §22 "scientific tier" framing is dissolved: numpy's only legitimate roles are the array **container** and a **temporary fallback** for not-yet-cascaded ops.
- **Tests** `tests/test_continuous_exp_cascade_rc34.py` (+6) — exp/cexp/complex_exp vs libm/cmath; `cexp` == Euler of srmech's own trig; AST guard against any `math/cmath/np .exp` in the call graph.

**Roadmap (per the derivation note):** rc35 promotes `sqrt`/`hypot` float wrappers + a direct-DFT cascade (on `cexp`) + `kron`; rc36 builds QR + SVD; rc37 non-Hermitian eig + lstsq + einsum; the numpy→`srmech[scientific]` dependency-flip is the capstone once cascade coverage is complete. No new C symbols.

## [0.7.0rc33] - 2026-06-04

**numpy-math → srmech-cascade routing: substrate-native trig (`cos`/`sin`/`tan`/`atan`/`atan2`) that replaces `math`/`numpy` trig at machine precision, plus Hermitian-eig routed onto srmech's own primitive across qm + signal_processing.** Pure-Python additions; ABI stays 3; `describe()` 210 → **215** (+5 trig tools).

- **New substrate-native float trig** — `srmech.amsc.rational.cos / sin / tan / atan / atan2` (also re-exported from `srmech.trigonometry` and `srmech.asymptotic_calculus`). The exact Class-N Taylor cascades were always globally convergent; what was missing was the **range-reduction wrapper** that composes them with the π-cascade. The pipeline is: range-reduce the angle into [−π, π] using a high-precision π drawn from `pi_cascade_digits` (Archimedes hexagon-doubling — **no `math.pi`/`np.pi` in the call graph**), anchor to a Class-N rational at the float64 floor, `cos`/`sin` Taylor partial sum, then project the exact rational to float. `atan` uses a three-band argument reduction (√2∓1 edges). Measured vs libm: **cos/sin ≈ 6e-16, atan/atan2 ≈ 2e-16** (machine ε). Class-K sign handling throughout (no `abs()`).
- **Trig call sites routed** — `qm.sm` (Weinberg / CKM angles), and the `signal_processing` window/basis/rotation trig (`cross_spectral`, `dct`, `multirate`, `multitaper`, `stft`, `ica_jade`, `form_function_rotation`) now compute their trig through the cascade instead of `math.cos/sin` / `np.cos/sin/arctan2`, per the directive *"never use numpy math when srmech can do it with a cascade."* Value-faithful (per-site parity tests vs the prior libm result, ≤1e-9).
- **Hermitian eigendecomposition routed** — every `np.linalg.eigh` / `eigvalsh` in `qm.{potentials, gauge, single_particle, so8}` and `signal_processing.{esprit, heat_kernel, ica_jade, music}` now goes through srmech's own **`amsc.laplacian.hermitian_eigendecompose`** (native C complex-Hermitian Jacobi when present; the eigenvalue/eigenvector math is srmech's, not LAPACK, on the native path). Real-symmetric inputs take a value-preserving `.real` on the eigenvectors; complex-Hermitian keep complex128.
- **Tests** — `test_qm_cascade_routing_rc33.py`, `test_sp_eigh_cascade_routing_rc33.py`, `test_sp_trig_cascade_routing_rc33.py` (eig parity ≤1e-9 + reconstruction, trig vs libm at machine ε, and each public op vs its pre-change output). The codebase-wide `abs()` AST ratchet stays green.

**Scope:** rc33 routes the audited qm + signal_processing numpy-math sites (`docs/srmech/notes/numpy_math_abs_audit_rc32.md`, Category B) onto srmech cascades. The genuinely scientific-tier numpy with no srmech equivalent yet (svd / qr / non-Hermitian-eig / lstsq / einsum / kron / complex-exp / FFT) stays per §22.

## [0.7.0rc32] - 2026-06-04

**numpy-optional core, step 3 — the real-symmetric Class-L Laplacian core is numpy-absent-safe (its eigenvalue math is srmech's OWN Jacobi cascade, never LAPACK), PLUS a codebase-wide `abs()` elimination (the rule: "abs() is never fine").** Pure-Python; ABI stays 3; `describe()` unchanged at 210.

- **`amsc.laplacian` real-symmetric core (`dense_adjacency` / `dense_laplacian` / `normalized_laplacian` / `jacobi_eigvals`) now runs with numpy absent** — the numpy import is guarded; numpy-absent builds return `list[list[float]]` and `jacobi_eigvals` returns `list[float]`. The native C path (primary) is unchanged.
- **`jacobi_eigvals`'s no-native fallback is now srmech's OWN pure-Python Jacobi cascade** (`_jacobi_eigvals_py`, a classical cyclic Jacobi rotation — the converged diagonal IS the spectrum), **never `numpy.linalg.eigvalsh`** (per the directive "never use numpy math when srmech can do it with a cascade"). It matches the native/numpy spectrum to Jacobi round-off (~1e-15). The complex-Hermitian / signed / magnetic ops stay scientific-tier (§22) and raise a clear `ImportError` when numpy is absent.
- **`abs()` eliminated codebase-wide (the absolute rule, value-preserving).** Every `abs()` / `np.abs()` / `math.fabs()` / `sqrt(·²)` stealth-abs in shipped srmech code is now an explicit Class-K sign-branch (`x if x >= 0 else -x` / `np.where(x>=0, x, -x)`) or real-imag composition (`|z|² = z.real²+z.imag²`, `|z| = hypot(z.real, z.imag)`) — `amsc.rational`/`kepler`/`harmonics`/`laplacian`/`hypercomplex_dft`, `qm.bell`/`sm`/`pseudo_hermitian`, `spectral`, and 13 `signal_processing` DSP files (≈40 sites). A permanent **AST ratchet** (`tests/test_laplacian_numpy_free.py::test_no_abs_calls_anywhere_in_srmech`) fails CI if any real `abs()` call reappears anywhere in `srmech/`.
- **`tests/test_laplacian_numpy_free.py`** (new, +6) — the Jacobi cascade matches the numpy/native spectrum + the P4 closed-form spectrum; the real-symmetric build→eigvals chain runs with numpy monkeypatched absent; the scientific-tier ops raise `ImportError`; and the codebase-wide abs() ratchet.

**Scope (honest staging):** rc32 does the §22 Laplacian-numpy-free voxel + the absolute abs() sweep (value-preserving, low-risk). The codebase audit (recorded in `docs/srmech/notes/numpy_math_abs_audit_rc32.md`) also found ~26 numpy-math sites where srmech has a cascade (Hermitian `np.linalg.eigh` → `hermitian_eigendecompose`; `np` trig → Class-N rational trig); routing those is **explicitly staged to rc33** (engine-swap — value-equal but a different code path needing per-site parity tests), not silently dropped. The genuinely scientific-tier numpy (svd/qr/non-Hermitian-eig/lstsq/einsum/kron/complex-exp/FFT) stays per §22. No new ops (`describe()` stays 210).

## [0.7.0rc31] - 2026-06-04

**Quaternion / octonion DFT cascade composites — `quaternion_dft` / `octonion_dft` (#863, F380). The native transform for a Klein-4 object: where a complex FFT collapses one of its two Z₂ chirality axes (the flat shadow), the QDFT's ℍ coefficient algebra resolves both.** Pure-Python composites over the `qm.octonion` atoms; ABI stays 3; `describe()` 208 → 210.

**Why it's exact, not analogical (F380):** the Klein-4 group **is** the quaternion units modulo sign — `Q₈/{±1} ≅ Z₂×Z₂`. So the coefficient algebra of each FFT-ladder rung carries a different chirality content: complex FFT → ℂ → `{±1,±i}/± = Z₂` (one axis); **quaternion FT → ℍ → `Q₈/± = Z₂×Z₂` (both axes)**. A QDFT's coefficient algebra matches the Klein-4 object's value algebra, so both axes survive.

- **`cascade.quaternion_dft(x, *, form, mu_axis, inverse)`** — `X[k] = Σ_n exp(σ·μ·2πkn/N)·x[n]`. Left/right `form` (ℍ is non-commutative → the twiddle can't be factored out as in the complex FFT; both forms round-trip). `inverse(forward(x)) == x` to float round-off, recovering **all four** components (both Z₂ axes). Composite over the `qm.octonion` left/right-mult atoms restricted to ℍ.
- **`cascade.octonion_dft(x, *, form, mu_axis, bracketing, two_sided_right_axis, inverse)`** — the (8:7) rung. Carries the F378 **non-associativity as an explicit declared `bracketing` field**: the two-sided ODFT `W_l·x·W_r` is not unique, so `(W_l·x)·W_r` vs `W_l·(x·W_r)` must be stated — these measurably differ for octonions. One-sided forms round-trip; the two-sided form is forward-only (its inverse is open under non-associativity → raises).
- **Class home** M (Clifford/HDC multiply) ∘ C (twiddle ±μ orientation) ∘ N (rational angle kn/N). No new primitive class; **no `abs()`**.
- **Scientific tier (UPSTREAM §22):** numpy is imported **lazily inside each op**, so `import srmech.amsc.cascade` stays numpy-free (the rc30 numpy-absent-safe core is intact); the transforms use numpy on call (consistent with §22 keeping the python-side qm maths numpy-ful).
- **`tests/test_hypercomplex_dft.py`** (new, +16) — QDFT left/right round-trip (each μ axis); the load-bearing **Klein-4 both-axes-preserved** round-trip + the **complex-FFT flat-shadow contrast** (the complex projection drops bit1; the QDFT keeps it); ODFT one-sided round-trip; the **two-sided bracketing is measurably non-associative**; input validation; numpy-absent ImportError.
- **`cascade_catalog/{quaternion_dft,octonion_dft}.toml`** (new) — the DSL-catalog descriptors with left/right form, the octonion bracketing convention as an **explicit attested field**, and PDF-verified OA citations (Sangwine & Ell, arXiv:1001.4379; Błaszczyk, arXiv:1905.12631; Hahn & Snopek 2011, Bull. Polish Acad. Sci. 59(2):167–181 — the paywalled IEEE TIP 2007 / Elsevier 2017 papers were **excluded** in favour of their OA arXiv equivalents per the paywalled-DOI rule).

**Tier note (the prototype/graduation split per #863):** these are the **prototype tier** — composites over existing primitives, no capability gap. A graduation to a first-class native C primitive (`srmech_quaternion_dft`, like the existing `fft`) is a **separate later voxel**, explicitly deferred — not silently capped. Also folds a doc-honesty fix: the `autocorrelation` tool_schema summary's stale "numpy FFT fallback" claim (made inaccurate by rc30) now reads numpy-free. Full suite green.

## [0.7.0rc30] - 2026-06-04

**numpy-optional core, step 2 — the `cascade` layer is numpy-absent-safe (UPSTREAM §22, Option 1). The second voxel of the "runs embedded without numpy/LAPACK" framework-identity arc.** Pure-Python; ABI stays 3; `describe()` unchanged at 208.

Introspection first (per the introspect-before-assert discipline): the four lowest-level core modules — `srmech.amsc.cyclic` (Class I), `srmech.amsc.primes` (Class J), `srmech.amsc.rational` (Class N), `srmech.amsc.format` (Classes A/B/the MPR IO) — were already **numpy-free** (zero `import numpy`). The only genuine numpy-absent crash sites in the cascade layer were two no-native fallback paths:

- **`cascade.compose.autocorrelation`** — the no-native fallback used `numpy.fft` to compute `IFFT(|FFT(x)|²)`. Replaced with the **defining direct circular-autocorrelation sum** `r[k] = Σ_n x[n]·x[(n+k) mod n]` (identical value for real `x`, no FFT / no numpy; `math.fsum` keeps each per-bin sum well-conditioned). The native C path is unchanged and still primary when `HAS_NATIVE`.
- **`cascade.atoms._try_native_chiral_dual`** — its float-list accel path did an unguarded `import numpy` (the C callback marshals via numpy views). Now guarded: numpy absent → returns `None` → the op's existing pure-Python `chiral_dual` fallback runs, rather than raising `ImportError`.

- **`tests/test_cascade_numpy_absent.py`** (new, +6) — the pure-Python autocorrelation matches both the closed-form definition and the numpy-FFT reference; a `sys.modules['numpy'] = None` simulation proves the cascade ops still run with numpy absent; and an audit-lock asserts `cyclic`/`primes`/`rational`/`format` carry no `import numpy`.

**Scope note (the arc):** numpy stays a **hard dependency** this rc — the flip to a `srmech[scientific]` extra is a later voxel (after `qm/*` + `signal_processing` get their `ImportError` guards). **Explicitly deferred, not silently capped:** the `atoms` stdlib-buffer C-boundary perf optimization (so the native `chiral_dual` accel path needs no numpy marshalling at all) is a tracked follow-up voxel — this rc only makes the path numpy-*absent-safe*, it does not yet make the native accel numpy-free. No new ops (`describe()` stays 208). No `abs()`.

## [0.7.0rc29] - 2026-06-04

**numpy-optional core, step 1 — the `HV` carrier + the Klein-4 family goes numpy-free (UPSTREAM §22 / §22b, Option 1). The first voxel of the "runs embedded without numpy/LAPACK" framework-identity arc.** Pure-Python; ABI stays 3; `describe()` unchanged at 208.

Per the RBS-LM research subtree's §22 recommendation (make numpy *optional*, for framework-identity — NOT as a reflex-fix), the **boundary-type lever**: the core A-N vocabulary returns a framework-native handle, not a raw `np.ndarray` (a numpy-typed return invites `np.dot`/`np.linalg`; a handle forces the srmech op).

- **New `srmech.amsc.hv.HV`** — a numpy-free hypervector carrier over a stdlib `array('B')` buffer. Plain-`int` `hv[i]`; scalar-`bool` `hv == other` (accepts `HV` / list / `bytes` / 1-D `np.ndarray`, so `np.array_equal(rec, v)` → `rec == v`); `hv.tolist()` / `hv.tobytes()` (stdlib) and `hv.to_numpy()` (opt-in bridge); buffer-protocol (the native C ops read/write it in place, so **HAS_NATIVE keeps HV fast** — pure-Python is only the no-native path). Imports **no numpy at load**. Distinct from `srmech.spectral.SpectralHandle`.
- **The whole Klein-4 family is now numpy-free internally + returns `HV`** — `klein4_random` (stdlib-`random` seed path; the numpy `rng=` back-compat path is unchanged), `klein4_bind` / `unbind` / `bundle` / `similarity` (the `sectors=`/`parallel=`/`mode=` flag is preserved + value-identical; only `bundle` chirality is value-meaningful), the three `chirality_flip*` / `cpt_mirror`, `klein4_triality_cycle`, `klein4_holographic_encode` / `decode` (rc27), and `klein4_triality_encode` / `correct` (rc28). `klein4_sector_count` returns a stdlib `list[int]`. No `abs()`.
- **Boundary plumbing**: the MCP result serialiser coerces `HV → list` (so MCP tool calls returning Klein-4 vectors still cross JSON-RPC); `rbs_lm.substrate` (a numpy research consumer, per §22) bridges back via the opt-in `.to_numpy()`.

**Scope note (the arc):** numpy stays a **hard dependency** this rc — the dependency only flips to a `srmech[scientific]` extra in a later voxel, once *every* core module imports without numpy. `qm/*` + `signal_processing` keep numpy throughout (§22: "leaving numpy for the python-side triality/qm maths is correct"). Chosen for the framework-identity / embedded-install reasons, **not** as an agent-reflex cure (§22 honest caveat). Breaking: consumers of the `klein4_*` return type now get `HV` (use `.tolist()` / `.to_numpy()` / `==`). Full suite green.

## [0.7.0rc28] - 2026-06-04

**Explicit order-3 triality-recursion corrector — `klein4_triality_encode` / `klein4_triality_correct` (#797 op (a1), F359 5-bar contract). The EXPLICIT k=3-CORRECT path past the order-2 4-cap (op (a2) is the measured no-Z3 substitute). Pure-Python; ABI stays 3; `describe()` 206 → 208.**

The order-2 Klein-4 store is **k=2-DETECT** natively (F294: no Z3, 3∤4) — two views detect a mismatch but cannot say which is right. k=3-CORRECT needs the **order-3 triality** (τ³=I) past the 4-cap. The store carries the order-3 triality **orbit** of the value, `[v, T(v), T²(v)]` for `T = klein4_triality_cycle`, so the third vote IS the triality orbit's third element (`T²v`) — not an external 3rd render:

- **`klein4_triality_encode(v)`** — `len(v)*3` uint8 store = `[v | T(v) | T²(v)]` (orbit-major). Class-home **M** (orbit replication bind) ∘ **I** (the order-3 cycle that generates the orbit).
- **`klein4_triality_correct(store, *, depth=1)`** — brings every orbit-block back to the common `v`-frame by **inverting the triality** (`T⁻¹` on block1, `T⁻²=T` on block2) then takes the per-position **2-of-3 majority**, correcting one error: k=3-CORRECT where the bare order-2 store is only k=2-DETECT.

The F359 5-bar contract (each falsifiable bar verified in `tests/test_klein4_triality_corrector.py`, new, +11):
1. **blind correction beats the F353 holographic 0.25 baseline** — single-error recovery is exact (measured rate 1.0);
2. **the 3rd vote is the order-3 triality orbit** of the same value (`block2 == T²v`, structurally);
3. **C/Python parity** — Python-first (co-equal); the standalone-C peer is the tracked next voxel;
4. **disable the order-3 op → degrade to k=2-DETECT** — without the inverse-to-frame step the raw orbit-blocks `{v,Tv,T²v}` disagree on every non-zero sector, so a naive majority does NOT recover `v` (correction is attributable to the triality, not to plain replication);
5. **WIDTH-step only** — one 4-cap crossing (order-2 → order-3); `depth != 1` **raises** `NotImplementedError` rather than fabricating the continuum count-recursion (open math).

Both ops registered in tool_schema (describe 206→208). No `abs()`. Built to the #797-comment / F359 contract (the canonical §20/F359 figures are not on the read-only research branch). This closes the #797 op-pair: (b) directed/signed-Laplacian (rc26), (a2) holographic substitute (rc27), (a1) explicit triality corrector (rc28).

## [0.7.0rc27] - 2026-06-04

**Klein-4 holographic-erasure code — `klein4_holographic_encode` / `klein4_holographic_decode` (#797 op (a2), F353). The measured substitute for the (a1) triality corrector: k=3-CORRECT with NO Z3. Pure-Python; ABI stays 3; `describe()` 204 → 206.**

The order-2 Klein-4 store is **k=2-DETECT** natively (F294: no Z3, 3∤4). k=3-CORRECT needs *either* the order-3 triality (op (a1), rc28) *or* this holographic-erasure route — replicate the store across `replicas` blocks so any one surviving replica-subregion (`1/replicas`) reconstructs the whole (the holographic "any subregion contains the whole" property at block granularity):

- **`klein4_holographic_encode(v, *, replicas=4)`** — `len(v)*replicas` uint8 store (replica-major).
- **`klein4_holographic_decode(store, *, replicas=4, erased=None)`** — `erased=mask` → first-surviving-replica (exact up to **(replicas-1)/replicas = 3/4** known-location erasure; raises if a position loses all replicas); `erased=None` → per-position majority (**blind**, corrects up to `floor((replicas-1)/2)` = **1/4** errors at the default). These are the F353 measured tolerances.
- **`tests/test_klein4_holographic_erasure.py`** (new, +10) — 3/4 known-erasure round-trip, any-single-block reconstruction, 1/4 blind correction, and an honest **past-capacity** test (3-of-4 corrupted → decode is *not* claimed correct — no silent over-claim). Both ops registered in tool_schema (describe 204→206).

Class-home **M** (replication bind) ∘ **C** (surviving-copy / majority selection); no `abs()`. The standalone-C peer is the tracked next voxel. Built to the #797-comment / F353 spec. op (a1) (explicit order-3 triality corrector; F359 5-bar contract) follows in rc28.

## [0.7.0rc26] - 2026-06-04

**Two surfaces: (1) the `srmech.asymptotic_calculus` / `srmech.trigonometry` continuous-calculus import path now resolves; (2) the directed/signed-Laplacian eigen-op (Class L, #797 op (b)). Pure-Python; ABI stays 3; `describe()` goes 201 → 204 (the three new Class-L ops registered).**

**(1) `srmech.asymptotic_calculus` + `srmech.trigonometry` (new modules).** The documented `srmech.asymptotic_calculus.*` import path had no module — the continuous-calculus primitives live in `srmech.amsc.rational` (Class N: `sin/cos/exp/log1p/atan_series_truncate` — exact-rational Taylor truncation, the substrate-native "continuous" trig) + the `srmech/amsc/attested/asymptotic_calculus/` catalog. These thin re-export modules make the advertised path resolve (no regression — nothing was deleted; the import surface was simply never created). `tests/test_asymptotic_calculus_alias.py` pins the re-export identity.

**(2) directed/signed-Laplacian (Class L, #797 op (b)).** The undirected combinatorial Laplacian is the F348 navigation control (Fiedler shuffle-fragile r=0.214); two generalisations from the F347–F354 research:

- **`signed_laplacian(n, edges, weights)`** — real-symmetric, PSD even with negative (frustrated) edges. The signed degree `D̄_ii = Σ_j |A_ij|` is the **Class-K magnitude** of the signed-metric (the operation Spike #24 located as "Class O", DISSOLVED into Class L). Kunegis et al. (2010).
- **`magnetic_laplacian(n, edges, weights, *, q=0.25)`** — complex **Hermitian**; direction is encoded as a phase `exp(i·2π·q·(W−Wᵀ))` so a directed graph stays Hermitian and the existing C-backed `hermitian_eigendecompose` diagonalises it — the complex eigenpair is the directed-navigation signature. `q=0` collapses to the real symmetrised Laplacian (the undirected control).
- **`fiedler_vector(matrix)`** — the λ₂ navigation embedding; dispatches real→`symmetric_eigendecompose`, complex→`hermitian_eigendecompose` (both C-backed).
- `tests/test_directed_signed_laplacian.py` pins the Hermitian/PSD/symmetry contracts + the q=0 control.

**Cadence note (honest):** the heavy eigendecomposition runs **native today** (the existing `symmetric`/`hermitian` C solvers), and the three new ops **are registered in tool_schema** (`describe()` 201 → 204; the no-carve-out coverage ratchet requires it). The only tracked next voxel is the standalone-C **builder** peers (`srmech_graph_signed_laplacian` / `…_magnetic_laplacian`) — mirroring the `loop_bind` Python-first→C-peer cadence (rc1 → rc7/rc20/rc21). Op (b) is the genuine new primitive (no substitute for directed navigation); op (a) (triality-recursion corrector / holographic-erasure substitute, #797) follows in rc27/rc28.

## [0.7.0rc25] - 2026-06-03

**CLI module docstrings refreshed to enumerate all four subcommands (`status` / `bus` / `dsl` / `mcp`) + an anti-staleness ratchet so they can't silently drift again (UPSTREAM_NOTES §13 D4). Docs only; ABI stays 3; `describe()` stays 201.**

The `srmech.cli` package + `srmech.cli.main` module docstrings had frozen at the v0.5.0rc4 *two-subcommand era* (`status` + `bus`), silently omitting `dsl` (v0.5.0rc8) and `mcp` (v0.5.0) even after the live CLI grew to four. The user-facing argparse `--help` was already correct (refreshed v0.6.0rc12) — only the module docstrings drifted.

- **`cli/main.py` + `cli/__init__.py` docstrings** — now enumerate all four subcommands with their intro versions + Usage examples for `dsl` / `mcp`.
- **`tests/test_cli_docstring_freshness.py`** (new) — reads the **live argparse subparser registry** (no hard-coded list to itself go stale) and asserts both module docstrings *and* the top-level `--help` description name every registered subcommand. A future subcommand that forgets the docstring now fails CI instead of drifting unnoticed.

This closes the last srmech-side item under the #855 "Dependency gates" list (§13 D4). It was a stale-finding cleanup: the behaviour was never wrong, only the module docs lagged.

## [0.7.0rc24] - 2026-06-03

**Class K real-axis atoms reject complex input cleanly — `cascade.magnitude` / `cascade.pin_slot_at_zero` now raise an intentional `TypeError` instead of leaking the internal `x > 0.0` comparison (UPSTREAM_NOTES §15.1, srmech-side fix (b)). Pure-Python boundary guard; ABI stays 3; `describe()` stays 201.**

`cascade.magnitude` and `cascade.pin_slot_at_zero` are **Class K pin-slot** operations — real-axis sign-splits, signature `(x: float)`. A complex argument previously fell through to `pin_slot_at_zero`'s `if x > 0.0:` and surfaced an opaque `TypeError: '>' not supported between instances of 'complex' and 'float'` — an internal comparison leaking, not a contract error.

- **`_require_real(x, op)`** — shared boundary guard. Raises `TypeError("cascade.{op} is a Class K real-axis (pin-slot) operation and does not accept complex input … use e.g. math.hypot(z.real, z.imag) for the modulus.")` before any dispatch. Catches Python `complex` **and** numpy complex scalars / 0-d arrays (`dtype.kind == 'c'`). Every real numeric (`int` / `float` / `bool` / `Decimal` / `Fraction` / numpy real scalar) is ordered against `0.0` and passes through bit-identically — no behaviour change for in-contract inputs.
- **Honest class boundary:** kept real-only (option (b), not (a)) because the complex modulus `(re**2+im**2)**0.5` is a **Euclidean-norm** op — a *different* cascade class, not a Class K pin-slot. Conflating it would muddy the cascade-class accounting.
- **No C change / no ABI bump:** the native `srmech_cascade_magnitude_f64` / `…_pin_slot_at_zero_f64` symbols take `c_double` — the C ABI has no complex entry point by design, so this is purely a Python-boundary input-validation guard, not a new operation. The Rosetta "C = transpiled Python" discipline is not engaged (there is no Python *operation* here lacking a C peer; rejecting out-of-contract input is a language-level concern).
- **`tests/test_cascade_magnitude_complex_reject.py`** (new) — both atoms raise a clean `TypeError` (with the actionable message) on Python complex and numpy complex128 / complex64; real inputs (float / int / negative / zero / NaN / ±inf) are unaffected.

With rc24 the §15.1 srmech-side gate (tracked in #855) is closed; the paired `CLAUDE.md` STOP-list doc correction lives on the parallel-session research branch (maintainer's to apply, per the upstream-as-research-notes discipline).

## [0.7.0rc23] - 2026-06-03

**`parallel_sectors` gains a body-kwarg channel — completes the §16.1 `parallel_body=` half so a kwarg-taking op can be a parallel body, symmetric with `op=`/`.then`. Pure-Python DSL; ABI stays 3; `describe()` stays 201.**

rc22 made `reorient` an `op=`/`.then`/TOML stage (data-first); the §16.1 finding also named `parallel_body=`. `Chain.parallel_sectors(body, *, n_sectors, combine)` had no way to pass the body op's keyword-only options, so a required-kwarg op couldn't be a `parallel_body`:

- **`Chain.parallel_sectors(body, *, n_sectors=4, combine="bundle", **body_kwargs)`** — `functools.partial`-binds `**body_kwargs` onto the body op before fan-out, so the bound body stays a unary `value → value` callable and the per-sector dispatch is unchanged. e.g. `chain.parallel_sectors("reorient", orientation=-1)` / `parallel_sectors("best_rational_signed", max_denominator=100)`.
- **TOML** — the parallel branch forwards non-reserved stage keys (`[[stage]] parallel_body="reorient"` + `orientation=-1`), mirroring the `op=` → `then(**kwargs)` path.
- **`tests/test_reorient_dsl_stage.py`** — extends with the kwarg-channel proof (bound orientation reaches the body) via Python + TOML.

**Honest scope (no silent cap):** the channel is the generic fix. `reorient` is a **scalar** op, so it's a valid `parallel_body` only at **`n_sectors=1`** (the identity sector); at `n_sectors≥2` the iω₇/γ₅ chirality stream-transforms iterate the stream per-element, which a scalar op can't consume (a category error, not a kwarg-channel failure). So the **practical** drivability for `reorient` remains the `op=` path (rc22); the channel benefits future kwarg-taking *sequence* bodies. With rc22 + rc23 the §16.1 dependency gate (tracked in #855) is closed.

## [0.7.0rc22] - 2026-06-03

**`reorient` is now data-first — `reorient(value, *, orientation)` — so it drives as a DSL chain stage (UPSTREAM_NOTES §16.1 fix (a)). BREAKING Python signature** (the data arg moved first; orientation is keyword-only). C ABI unchanged (stays 3); `describe()` stays 201.**

`reorient(orientation, value)` was the one cascade-op whose data argument was **second** — every other stage-op is data-first. The DSL chain runner pipes the stream into arg 0, so `op="reorient"` bound the stream to `orientation` and dropped `value` (`TypeError`), and a stage `orientation=` kwarg collided on position 0. It was therefore **un-invokable as an `op=` / `.then()` / TOML stage**, though the catalog listed it `kind="stage"`. Per the §16.1 "cleanest" resolution:

- **`srmech.amsc.cascade.atoms.reorient(value, *, orientation)`** — `value` positional (the piped data), `orientation` keyword-only. Now drives exactly like `best_rational_signed(x, *, max_denominator=…)`: `chain.then("reorient", orientation=-1)` in Python, or a TOML `[[stage]] op="reorient"` + `orientation = -1` (the non-reserved key is forwarded as the bound kwarg). C dispatch + Python fallback unchanged internally; the C ABI (`srmech_cascade_reorient_{i64,f64}`) is untouched.
- **Call sites updated** (the order flip is breaking): `cascade.atoms` (`net_chirality`), `cascade.compose` (`best_rational_signed`), `cascade.parallel` (`_reorient_each` / iω₇ axis), the `reorient` `tool_schema` ToolEntry (params reordered), `reorient.toml` signature, and the cascade test suite.
- **`tests/test_reorient_dsl_stage.py`** (new) — pins the fix: reorient drives via `.then("reorient", orientation=-1)`, composes after `magnitude`, and runs from a TOML chain; the old positional second-arg now raises (keyword-only).

**Migration:** `reorient(o, v)` → `reorient(v, orientation=o)`.

**Scope note (no silent cap):** this fixes the `op=` / `.then` / TOML drivability (the primary finding). `parallel_body="reorient"` with a bound orientation is **not** yet supported — `Chain.parallel_sectors(body, *, n_sectors, combine)` has no body-kwarg channel, so any required-kwarg op (reorient's `orientation`) can't be a `parallel_body`; that body-kwarg forward is a separate follow-up. `parallel_body` ops whose kwargs all default (e.g. `best_rational_signed`) already work.

## [0.7.0rc21] - 2026-06-03

**Native C peers for the last three loop-bind ops computing via pure-Python — `loop_associator` / `loop_left_op` / `loop_right_op`. Closes a parity gap the rc20 #814 close glossed: those three (all named in #814's op spec) still ran the pure-Python Cayley-Dickson recursion (`_loop_bind_raw`) while `cross7`/`g2_three_form` already had dedicated C symbols. Now every op in the loop-bind spec is at native C/Python parity. Additive C symbols → ABI stays 3; `describe()` stays 201; every dispatch arm bit-exact with its Python fallback.**

The "C = transpiled Python" Rosetta discipline (notebook §3.29.4–§3.29.5) admits no Python-only carve-out: a composition-op gets a C rendering exactly as `cross7 = Im(bind)` and `g2 = ⟨x, cross7⟩` did (rc7). The associator (the Class-K residue, the genuinely-new k=7 arithmetic surfaced in #797/F271) and the L/R multiplication-operator matrices were the remaining pure-Python composites:

- **`srmech_loop_associator_f64`** (`c/src/srmech_loopbind.c`) — `(a·b)·c − a·(b·c)`, two fixed triple-products via the static octonion product (no recursion); 8 doubles out.
- **`srmech_loop_left_op_f64` / `srmech_loop_right_op_f64`** — the L_a (col k = a·e_k) / R_a (col k = e_k·a) operator matrices, n·n doubles row-major, byte-matching numpy `column_stack` of the per-basis binds.
- **`srmech.amsc.hdc`** — `loop_associator` / `loop_left_op` / `loop_right_op` dispatch to the peers for the dim-8 octonion when `HAS_NATIVE`, pure-Python recursion kept as the Pyodide/WASM (and non-dim-8) fallback.
- **`tests/test_loop_operator_native_parity.py`** (new) — native peer vs the pure-Python recursion (the Rosetta agreement-attestation), plus the associator's known structure (zero on associative/Fano triples, antisymmetry).

With rc7 (per-block) + rc11/rc17 (HD bind SIMD) + rc20 (HD conj/inv/unbind/runbind) + rc21 (associator + L/R operators), the **entire** `srmech.amsc.hdc` loop-bind / Moufang surface is native at both single-octonion and HD-block scale — no op is Python-only. JPL Power-of-Ten clean (≤60-line, ≥2 asserts, no goto/malloc/recursion); warning-clean under `-Wall -Wextra -Wpedantic -Werror` / `/W4 /WX`.

## [0.7.0rc20] - 2026-06-03

**Native C peers for the rest of the HD loop family — completes "C = transpiled Python" (the Rosetta discipline, notebook §3.29.4–§3.29.5: one SSoT rendered as meaning : Python AND C source : Compiled C). The HD block conjugate / Moufang inverse / left-unbind / right-unbind were Python-only per-block loops; now each has a whole-array C transpile, so NO HD loop op is Python-only. Additive C symbols → ABI stays 3; `describe()` stays 201; every dispatch arm bit-exact with its Python fallback.**

`srmech_loop_bind_hd_f64` (rc11/rc17, the F292 #2 graft) gave the HD BIND its native peer; the companions (`loop_conj_hd` / `loop_inv_hd` / `loop_unbind_hd` / `loop_runbind_hd`) kept looping over 8-blocks in Python — a Rosetta with a glyph present in one script (Python) but missing from the other (C source), so those ops had no machine-code tier. This rc renders them in C too:

- **`c/src/srmech_loophd_family.c`** (new) — `srmech_loop_{conj,inv,unbind,runbind}_hd_f64`, the SHIPPED per-block symbol (`srmech_loop_conj_f64` / `srmech_loop_inv_f64` / `srmech_loop_bind_f64`) applied over NB independent dim-8 blocks (the block-diagonal ⊕, #811/F289). The faithful transpile of the Python wrappers — same per-block ops, same order — collapsing the per-block Python loop into ONE native call (bit-exact with the fallback by construction). `loop_inv_hd` propagates `SRMECH_ERR_BAD_INPUT` from a zero block (→ the Python fallback raises, contract preserved). Scalar — no N-way SIMD here (the bind owns that, `srmech_loopbind_hd.c`); the heavy step where present (the product) is already native per-block.
- **`srmech.amsc.hdc`** — `loop_conj_hd` / `loop_inv_hd` / `loop_unbind_hd` / `loop_runbind_hd` dispatch to the new peers when `HAS_NATIVE`, with the per-8-block pure-Python recursion kept as the Pyodide / WASM fallback (`hasattr`-guarded ctypes, stale-`.dll`-safe).
- **`c/include/srmech.h`** — 4 new prototypes; the stale "the HD variants need NO C peer of their own" note is retired (it predated `loop_bind_hd`'s peer and contradicted the Rosetta discipline).
- **`tests/test_loop_hd_native_parity.py`** (new) — asserts the whole-array native peer agrees with the pure-Python Cayley-Dickson recursion (`_loop_bind_raw` / `_loop_conj_raw`) — the literal Rosetta agreement-attestation — plus the round-trip identities. The existing `test_loop_hd_division.py` suite now exercises the native path for free.

Closes the C/Python-parity ask in **#814** (loop-bind op spec — "Parity-tested against the Python fallback", now true across the HD surface too) on the realization established in **#811**/**#812** (the dim-8 → high-dim block-octonion ⊕). Each function is ≤60 lines, ≥2 asserts, no goto/malloc/recursion, single-line macros only, warning-clean under `-Wall -Wextra -Wpedantic` / `/W4 /WX` (JPL Power-of-Ten).

## [0.7.0rc19] - 2026-06-03

**HAL constant-attestation discipline — MPM (Mathematical Provenance Method) applied to CODE CONSTANTS, retroactive. Externally-sourced magic that srmech does NOT derive from its own framework (and historically transcribed by hand) is now attested in a per-target header MPR block AND, where derivable, regenerated-and-asserted by a test. Pure provenance/hardening: no behaviour change → ABI stays 3; `describe()` stays 201; every dispatch arm byte-identical.**

Motivated by the rc18 SHA-NI K-table typo (`0x8CC70808` where FIPS K[59] is `0x8CC70208`) — a transcribe-from-memory error invisible on a host without the SHA feature, caught only on SHA-NI CI. The fix generalises: magic constants get attested + derived-and-asserted so the next such typo fails locally, on any host, at unit-test time.

- **`c/src/srmech_sha256_constants.h`** (new) — the SINGLE attested home for FIPS K[64] + H0[8] (MPR block → FIPS 180-4 §4.2.2/§5.3.3). The three SHA-256 TUs (`srmech_sha256.c` / `_batch.c` / `_shani.c`) now `#include` it instead of each carrying a hand-copied duplicate (that duplication was the same risk surface as the rc18 bug).
- **`c/src/srmech_sha256_shani.h`** (new) — the packed SHA-NI `KP[16][2]` + an MPR block attesting BOTH the constants (FIPS) and the rnds2/msg1/msg2 instruction **sequence** (Intel SDM Vol 2 + Intel SHA Extensions whitepaper as primary; noloader/Walton as a working-impl pointer, NOT a drifting byte-hash; correctness pinned by `test_sha256_shani.py` on SHA-NI CI).
- **`c/src/srmech_simd.h`** — MPR block for the cpuid leaf/bit numbers (Intel SDM Vol 2A CPUID: leaf-1 ECX bit 27/28 OSXSAVE/AVX; leaf-7 EBX bit 5/29 AVX2/SHA; XGETBV XCR0 gate) + the GCC/Clang target-attribute feature strings (GCC x86 Function Attributes).
- **`tests/test_fips_constants_attested.py`** (new) — derive-and-assert: regenerates K from **exact integer cube-roots** of the first 64 primes (`icbrt(p<<96)`) and H0 from square-roots (`isqrt(p<<64)`) — no float, no ULP risk — and asserts byte-for-byte against the committed `srmech_sha256_constants.h` tables **and** the decoded packed `KP`. This is the gate that would have failed rc18's typo at unit-test time. (Self-check: asserts the derivation itself yields K[59]=`0x8CC70208`.)

The discipline going forward: a HAL/target magic constant ships with (a) an MPR attestation block in its `.h`, and (b) a regenerate-and-assert test where the value is derivable; a hand edit the test doesn't bless is a defect by construction.

## [0.7.0rc18] - 2026-06-02

**SHA-NI single-stream SHA-256 (F292 graft #3) — performance-engineering of srmech's OWN content-addressing hash for the common single-message case (`sha256_bytes`, every AMSC attestation). Built in CI so a SHA-NI-capable runner exercises the kernel, not parked because the dev CPU lacks the feature. New C symbol → ABI stays 3; `describe()` stays 201; JPL ratchet unchanged.**

Graft #1 (rc10 `sha256_batch`) accelerates "hash N independent messages" by filling SIMD lanes; the single-message case it can't help is exactly the hot path (one response-bytes blob fingerprinted per attestation). The Intel SHA Extensions (SHA-NI) accelerate ONE message — `_mm_sha256rnds2_epu32` runs two rounds per instruction, `_mm_sha256msg1/msg2_epu32` drive the schedule — so one 64-byte block compresses in a handful of instructions.

- **`srmech_sha256_shani`** (new `c/src/srmech_sha256_shani.c`) — FIPS-pads a block at a time, runs each block through the SHA-NI compress (state kept packed in the Intel ABEF/CDGH layout), and writes the raw 32-byte digest. The 64 rounds are factored into JPL-clean ≤60-line helpers (load warm-up + a cyclic steady-state group driven by a rotating message-register index + a final group) that are bit-identical to the canonical interleaving. A self-contained scalar duplicate (byte-for-byte the `srmech_sha256.c` compress, NIST-KAT-pinned) is the oracle AND the fallback.
- **HAL** (`srmech_simd.{h,c}`, rc11) gains `srmech_simd_has_shani()` (leaf7 EBX bit29 — no OSXSAVE gate; XMM state is always OS-saved) + `SRMECH_SIMD_TARGET_SHANI` (`target("sha,sse4.1,ssse3")` on gcc/clang; empty on MSVC). Target-attribute-guarded compilation means the kernel **builds on any host** (incl. the SHA-NI-less dev CPU); runtime cpuid-dispatch enters it only where the feature is present.
- **Dispatch safety:** the kernel is NEVER entered unless cpuid confirms SHA-NI, so the `SRMECH_SHANI_FORCE_TIER` test hook ({0,1}) can only select scalar-or-(SHA-NI-if-present) — it can never SIGILL. `srmech.amsc.format.sha256_bytes` prefers the SHA-NI peer when the rc18 symbol is bound (transparent hot-path accel; every arm bit-exact).
- **Honest coverage:** `tests/test_sha256_shani.py` pins the scalar oracle on every host (force tier 0) AND the auto path (kernel on SHA-NI runners, scalar elsewhere); the "kernel actually ran" assertion is **exercise-if-present / skip-with-log** keyed on `_native.has_shani()` (so a non-SHA-NI runner skips with a clear log rather than passing a scalar run off as kernel coverage). A CI **cpuid-dump** step records which matrix cells carry the feature. `_native.has_shani()` surfaces the host capability (tri-state True/False/None).

Each function is pi-free, ≥2 asserts (the cpuid probe + the 1-line rotate are the documented Rule-5 exemptions), ≤60 lines, no goto/malloc/recursion, single-line macros only, warning-clean under `-Wall -Wextra -Wpedantic` / `/W4 /WX`.

## [0.7.0rc17] - 2026-06-02

**C-transpile of the last two rc12 chiral primitives (Class E + L) — closes the C/Python-parity gap so NO rc12 primitive op is Python-only (full-C-parity commitment per `[[feedback_no_binding_layer_carveout]]`). Additive C symbols → ABI stays 3; `describe()` stays 201; JPL ratchet unchanged.**

rc16 transpiled the Class-I/D/G chiral ops; rc16's two "deferred" ops were a soft-MVP carve-out the project rejects — both have clean integer kernels and now have native C peers, dispatched-to when `HAS_NATIVE` (byte-exact Python fallback unchanged):

- **`srmech_reverse_order`** (Class E → `srmech_catalog.c`) — the reversed index permutation `out[i] = n-1-i` (the chiral mirror of a sorted catalog; the wrapper applies the permutation to the `(key, value)` pairs); wired into `srmech.amsc.naming.reverse_order`.
- **`srmech_three_fold_bands`** (Class L → `srmech_laplacian.c`) — the harmonic-3 three-fold band split (`low/mid/high` from `n/3` + remainder to the later bands so `|low| ≤ |mid| ≤ |high|`); wired into `srmech.amsc.laplacian.three_fold_eigvec_groups` (the band-size computation gains a C path; the eigvec solve composes the existing Class-L spectral machinery).

Each is pi-free integer arithmetic, 2 asserts, ≤60 lines, no goto/malloc/recursion, warning-clean (`-Wall -Wextra -Wpedantic`). `hasattr`-guarded ctypes bindings (stale-`.dll`-safe). 4 new native-vs-Python parity tests (`test_chiral_EL_c_parity.py`) force both paths.

With rc16+rc17, **every rc12 primitive op (D/E/G/I/L) now has a native C surface.** (`classify_harmonic` is a static partition-constant lookup and `classify_chirality_harmonic` is a composite spectral reading — classifiers, not bare per-class primitives — so they compose rather than each get a C symbol, consistent with the primitive-vs-composite line the architecture already draws.)

## [0.7.0rc16] - 2026-06-02

**C-transpile of the rc12 chiral primitives — native C peers for the F150 Class-I/D/G chiral ops, byte-exact with their Python fallbacks. Additive C symbols → ABI stays 3; `describe()` stays 201 (no new public callable — the ops already shipped in rc12); JPL ratchet unchanged.**

The three rc12 chiral ops with a clean integer/byte kernel now have a native C surface, dispatched-to when `HAS_NATIVE` (pure-Python fallback unchanged, byte-exact):

- **`srmech_three_cycle`** (Class I → `srmech_cyclic.c`) — the Z/3 generator `(value+1)%3`, computed overflow-safe as `((value%3)+1)%3`; wired into `srmech.amsc.cyclic.three_cycle` (uint64-range values dispatch to C, larger fall back to Python).
- **`srmech_mirror_pattern`** (Class D → `srmech_dispatch.c`) — the byte-reversed needle; wired into `srmech.amsc.dispatch.mirror_pattern`.
- **`srmech_byte_search_backward`** (Class G → `srmech_search.c`) — the last-occurrence search (rfind; empty needle → `len`, absent → `UINT32_MAX`/`None`); wired into `srmech.amsc.search.byte_search_backward`.

Each is pi-free integer/byte arithmetic, ≥2 asserts, ≤60 lines, no goto/malloc/recursion, warning-clean under `-Wall -Wextra -Wpedantic` (JPL Power-of-Ten). 9 new native-vs-Python parity tests (`test_chiral_c_parity.py`) force both paths and assert byte-exact agreement across boundaries / random sweeps / period-3 / involution / empty-absent-multi-occurrence. ctypes bindings are `hasattr`-guarded so a stale `.dll` falls back to Python rather than failing to load.

**Deferred rungs (no-silent-caps):** Class E `reverse_order` (list-of-pairs reversal — a Python data-structure op, not a numeric/byte kernel; intentionally Python-only) and Class L `three_fold_eigvec_groups` (eigendecompose-adjacent band split) remain Python-only for now; the rbs_lm Klein-4 encode helpers compose the already-C-backed `klein4_*` primitives.

## [0.7.0rc15] - 2026-06-02

**DSL surface audit — corrects stale op-counts in the LLM-facing cascade-DSL tool descriptions + adds an anti-drift guard. Descriptions only; no new ToolEntry → `describe()` stays 201; ABI stays 3; no C change.**

The cascade-DSL tool descriptions had drifted behind the runner: the
`srmech.dsl.list_catalog_ops` ToolEntry summary enumerated only "8 ops"
(omitting the v0.7.0rc8 `autocorrelation` AND the v0.6.0 `kuramoto_step` /
`parallel_sector_dispatch`), and `run_toml_chain` referenced a "10-op cascade
catalog" — so an LLM driving the DSL via MCP would believe fewer ops exist than
the **11** that actually ship. The CLI (`srmech dsl ops`) was already correct
(it reads the catalog live).

- **Corrected** every stale count/list across the DSL surface: the two
  `_register_dsl_tools` ToolEntry summaries (`run_toml_chain` /
  `list_catalog_ops`), the `srmech.dsl.__init__` + `srmech.dsl._tool_surface`
  module docstrings — all now cite **11** ops and `list_catalog_ops` names all
  eleven (`autocorrelation`, `best_rational_signed`, `chiral_dual`,
  `chiral_flip`, `cyclic_gcd`, `kuramoto_step`, `magnitude`, `net_chirality`,
  `parallel_sector_dispatch`, `pin_slot_at_zero`, `reorient`).
- **Anti-drift guard** (`test_dsl_tool_surface_descriptions.py`): the DSL
  ToolEntry summaries are now locked to the LIVE `list_cascade_ops()` set —
  every live op name must appear in the `list_catalog_ops` summary and both
  summaries must cite the current op count, so a future op forces the
  descriptions to be updated (or CI fails) rather than silently falling stale.

## [0.7.0rc14] - 2026-06-02

**RBS-LM upstream wishlist — the `srmech.rbs_lm` inference substrate (UPSTREAM_NOTES §9; F166 walk). A NEW top-level module, pure-Python; outside the `amsc.*`/`qm.*` tool-schema enumeration → `describe()` stays 201; ABI stays 3; no C change.**

Ports the F166 bit-exact, catalog-instantiable inference substrate from the research subtree into the package — inference built UP from the 28-D Klein-4 coordinate, not distilled DOWN from float weights. The typed substrate config of rc13 (`substrate_parameterization`) gets its first consumer.

- **`srmech.rbs_lm.ContextSubstrate`** — the rolling-context encoder: per-token Klein-4 vectors (SHA-256 seed → fixed vector, sector arithmetic), `iω₇` position keys, odd-bundle of the last-k tokens → ONE Klein-4 state (Class A∘M encode + position). Plus the numpy-level encode helpers (`token_seed`, `encode_word_k4`, `encode_bigram_l1`, `encode_skeleton_l2`, `encode_sentence_l3`, `sim_k4_batch`) — the same Klein-4 sector cascade as `srmech.amsc.hdc.klein4_*`, at numpy-array granularity for the inference loop.
- **`srmech.rbs_lm.RBSLMInferenceSubstrate`** — the inference object: `from_catalog(toml)` / `from_params(dict)` build it; `learn(stream)` loads the bigram candidate structure + a context→next associative memory (F154-bounded, `klein4_bind` over windows, odd-bundle); `next_token_distribution(ctx, temperature)` retrieves over bigram-legal candidates (Class M) + temperature-softmax; `infer(prompt, …, seed)` is the deterministic autoregressive loop; `attestation()` returns the MPR block (descriptor_hash + srmech_version + abi + provenance) so any generated sequence is re-derivable.

**Determinism:** same corpus + params + srmech_version + seed → bit-exact identical output (SHA-256 token seeds, exact XOR bind, seeded sampling). Faithful (bit-exact) port of the research artifact; composes the existing `srmech.amsc.hdc.klein4_*` primitives + `srmech.amsc.load_descriptor`/`descriptor_hash` (no new `hashlib.sha256` — routes through `srmech.amsc.format.sha256_bytes` via `token_seed`).

**SCOPE / deferred rungs (no-silent-caps):** rc14 ships the two classes. The `srmech.rbs_lm` **tool_schema surface** (LLM-as-tool inference) + the **`siona.profile("rbs_lm").infer()` binding** (§8+§9 join) + the **hierarchical-memory scale-up** (`CanonicalHierarchicalMemory`, F162 — past the single-memory F154 4× ceiling, for corpus-scale inference) remain open for follow-up rcs. `[[feedback_no_mvp_framing]]`.

## [0.7.0rc13] - 2026-06-02

**RBS-LM upstream wishlist — the `substrate_parameterization` adapter + typed Descriptor sub-dataclasses (UPSTREAM_NOTES §7). Pure-Python, additive; no new ToolEntry → `describe()` stays 201; ABI stays 3; no C change.**

A seventh AMSC adapter (`html_scraper` / `json_api` / `csv_bulk` / `netcdf_grid` / `geotiff_bbox` / `literature_curated` → + `substrate_parameterization`). Where the first six answer *"where do the ground-proof rows come from?"*, this one answers *"how is a parameterized substrate configured?"* — every former module-level magic number of a substrate characterization run (the RBS-LM variable-length Klein-4 chirality-level sentence substrate is the canonical consumer) lives in attested `[fetch.substrate_parameterization.*]` sub-tables rather than script-embedded MVP magic (`[[feedback_no_mvp_framing]]` + user direction 2026-05-28).

- **Typed sub-dataclasses** (in `srmech.amsc.adapters.substrate_parameterization`): `SubstrateParams`, `EncodingParams`, `GenerationParams`, `HierarchicalParams`, `CorpusParams` (required) + `GrammarParams`, `PlausibilityParams`, `MeasurementParams` (optional), composed into a frozen `SubstrateConfig`. First-class typed access (`cfg.substrate.D`) replaces dict-navigation (`desc.fetch["literature_curated"]["substrate"]["D"]`).
- **`parse_substrate_config(params)`** — validates the called-out invariants: `D > 0` (and every count); `cycle_policy ∈ {forbid, allow, count_limited}`; `corpus.source` / `corpus.tokenizer` / `grammar.mode` enums; `default_strategy ∈ allowed_strategies`; `0 ≤ plausibility weight ≤ 1`; `eps_smoothing > 0`. Booleans are rejected where ints are required.
- **`config_for(descriptor)`** — typed accessor that locates the substrate sub-table inside `descriptor.fetch` (the `substrate_parameterization` key when migrated, else the legacy `literature_curated` key, else `[fetch]` directly), so it works for a migrated descriptor AND one still riding the interim adapter.
- **`fetch` / `parse`** — the AMSC adapter protocol: `fetch` reads the committed `[fetch].ndjson_path` (the characterization measurement output); `parse` decodes it line-by-line. These rows are *computed* outputs attested by the descriptor + `parser_rule_hash`, so (unlike `literature_curated`) no per-row `source_doi` is required.

**SCOPE:** the typed config layer only. The `run_substrate_characterization` operation that *consumes* a `SubstrateConfig` + corpus + phase set and *produces* the measurement NDJSON is the substrate-module port (UPSTREAM_NOTES §9), landing in a follow-up rc. The adapter module lives under the coverage-exempt `srmech.amsc.adapters.*` prefix (like its six siblings), so no tool-schema churn. `[[feedback_no_mvp_framing]]`.

## [0.7.0rc12] - 2026-06-02

**RBS-LM upstream wishlist — F150 chiral A–N harmonics (UPSTREAM_NOTES §6) + §2.2 cross-substrate alignment. 7 new ToolEntries → `describe()` 194→201 (+1 coverage-exempt utility); pure-Python, no C change (this rc), ABI stays 3.**

Lands the research-side F150 framework move: the 14 A–N operators carry a **per-operator chirality-harmonic order** (1/2/3) that partitions the existing classes — H1 (chirality-invariant) = A B F H N, H2 (chiral inverse / mirror) = C D E G K M, H3 (chiral rotation / 3-cycle) = I J L. Variants land **next to their base Class op** (no privileged namespace, per `[[feedback_no_privileged_primitive_classes]]`; `siona` is a co-name alias, so these are `srmech.amsc.*`).

- **`srmech.amsc.harmonics`** (new) — `classify_harmonic(letter) -> 1|2|3` (the static F150 partition) + `classify_chirality_harmonic(hv) -> 1|2|3` (spectral classifier: DC-dominant→H1, else zero-mean mirror vs 3-fold self-agreement→H2/H3; energy / inner-product ratios, no abs() on the substrate). `HARMONIC_PARTITION` + `HARMONIC_LADDER_OPEN_RUNGS` constants.
- **Harmonic-2 mirror ops** (period-2 involutions): `dispatch.mirror_pattern` (D — byte-reversed needle), `naming.reverse_order` (E — order-reversed sorted catalog), `search.byte_search_backward` (G — last-occurrence search).
- **Harmonic-3 three-cycle ops** (period-3): `cyclic.three_cycle` (I — Z/3 generator; any non-negative int read mod 3, so the generic MCP int-synth is always in-domain), `laplacian.three_fold_eigvec_groups` (L — low/mid/high eigenvector bands).
- **`compose.greedy_bipartite_alignment`** (§2.2) — greedy cross-substrate kernel matcher (caller `similarity_fn`); the Rosetta-layer utility. It takes a Python callable that cannot cross JSON-RPC, so it is **not** an MCP tool — it is coverage-exempt in `tests/test_tool_schema_coverage.py::_EXEMPT_FUNCTION_NAMES` on the callable-arg rationale (public + tested, surfaced via `srmech.amsc.compose`).
- **tool_schema:** the **7** primitive ops are all registered and **fully MCP-callable** (`mcp_callable=True`) — no handle-pending entries (the rc16 zero-handle-pending invariant holds): `classify_harmonic` (str), `classify_chirality_harmonic` (np.ndarray, JSON-list-coerced + flattened), `mirror_pattern` (bytes), `reverse_order` (list[tuple[bytes,bytes]]), `byte_search_backward` (bytes×2), `three_cycle` (int), `three_fold_eigvec_groups` (np.ndarray). → `describe()` 194→**201**.

**Ladder is staged, not capped** (no-silent-caps): `HARMONIC_LADDER_OPEN_RUNGS = {2: ("C","K"), 3: ("J",)}` — Class M's H2 already ships as `hdc.klein4_*` (F132); C/K explicit mirror variants + J's speculative `three_cycle_factor` (F150 §6.3) remain open for a later rung.

**SCOPE:** framework-composition surfaces over the existing A–N primitives; most of UPSTREAM_NOTES §1/§2 (`rfft`, `signed_sum_squared`, `symmetric_eigendecompose`) was already shipped in prior rcs. `[[feedback_no_privileged_primitive_classes]]`.

## [0.7.0rc11] - 2026-06-02

**F292 graft #2 — N-way SIMD block-octonion HD bind (`srmech.amsc.hdc.loop_bind_hd`), on a new SIMD optimize-path HAL (`c/src/srmech_simd.h`). NO new public callable → `describe()` stays 194; a NEW C symbol → ABI stays 3 (additive).**

The on-theme F292 graft: `loop_bind_hd` is the block-diagonal direct sum ⊕ of NB **independent** dim-8 octonion products (F289 verified err 0.0) — exactly the data-parallel shape cpuminer's N-way-SIMD mindset exploits. It was a **Python loop** over the NB 8-blocks (one ctypes call per block); this collapses it to **one native call** that advances W blocks per SIMD pass.

- **`srmech_loop_bind_hd_f64(x, y, nb, out)`** (`c/src/srmech_loopbind_hd.c`, new) — binds all NB blocks in one call via a runtime **AVX (256-bit double, W=4)** / **SSE2 (W=2)** / scalar dispatch. The SIMD kernels mirror the rc7 `mul2/mul4/mul8` Cayley-Dickson op-DAG with `double` → a vector holding W blocks of one component; the scalar tier (remainder / non-x86 / Pyodide) reuses the shipped `srmech_loop_bind_f64`, so it is bit-exact with the single-block product by construction. `loop_bind_hd` dispatches to it (whole NB-block array crosses once — no per-element Python loop); the per-block fallback is unchanged. NOTE the 256-bit **double** ops are AVX, not AVX2.
- **HAL — `c/src/srmech_simd.h` + `srmech_simd.c` (new):** ALL machine-specific bits other than the kernels now live in ONE place — the `SRMECH_SIMD_X86` platform macro, the arch intrinsic includes, the `SRMECH_SIMD_TARGET_*` per-function attributes, and the cpuid/xgetbv feature probes (`srmech_simd_has_avx2/_avx/_sse2`) + env-tier clamp (`srmech_simd_tier`). The portable core (`srmech_sha256.c`, `srmech_loopbind.c`) and the public header (`c/include/srmech.h`) stay 100% machine-agnostic. **rc10's `srmech_sha256_batch.c` is retrofitted onto the HAL** — its own platform/target/cpuid copies deleted (byte-identical SHA output, every tier; net FEWER Rule-5-exempt functions). New optimize-path ops include the HAL and write only their kernels.
- **Bit-exact, every tier:** scalar / SSE2 / AVX all match the pure-Python `_loop_bind_raw` per block (**maxerr 0.00e+00**, including the canonical HD width 2048 = 256·8) — the F292 "parity-trivial" prediction confirmed. `tests/test_loop_bind_hd.py`. SHA-256 batch regression: still byte-identical to `hashlib` + NIST KATs at every tier.
- **JPL-clean:** intrinsics (NOT asm); no `goto`/recursion/malloc; ≤60-line functions; single-line vector macros (Rule 8); kernels self-isolate via `__attribute__((target("avx"|"sse2")))` so the library compiles at baseline ISA (no global `-mavx`); ≥2 asserts per non-exempt function (the cpuid probes are the documented exempt entries). gcc/clang/MSVC `-Werror`/`/WX`.

**SCOPE (load-bearing):** energy/perf-engineering of srmech's OWN Class-M HD bind (octonion algebra — not hashing, not mining). The HAL is the architectural answer to "no machine-specific bits in the core; abstract the optimize path behind a header." `[[feedback_trauma_informed_defensive_scope]]`.

**`describe()` stays 194** (internal acceleration of an existing surface, no new ToolEntry); **ABI stays 3** (new symbol, additive). Anchor: F292 (`R-RBS-LM-FINDING_292_cpu_optimization_reference_graft_handdown`).

## [0.7.0rc10] - 2026-06-02

**F292 graft #1 — N-way SIMD SHA-256 BATCH (`srmech.amsc.format.sha256_batch`), folding the F292 CPU-optimization hand-down into v0.7.0. +1 ToolEntry → `describe()` 194; a NEW symbol → ABI stays 3 (additive).**

The first "apple-tree" graft from F292: take cpuminer's battle-tested **N-way SIMD SHA-256 technique** (`sha256d_ms_4way/8way`) and re-implement it JPL-clean in srmech's own hash, for the bulk-attestation common case (fingerprinting a whole catalog of upstream response bytes at once).

- **`srmech.amsc.format.sha256_batch(datas) -> list[str]`** — one 64-char lowercase hex digest per message, each **byte-identical** to `sha256_bytes(d)` / `hashlib.sha256(d).hexdigest()`. A throughput surface, NOT a new content-address shape. Dispatches to the native peer when present, else a `hashlib` loop.
- **`srmech_sha256_batch`** (`c/src/srmech_sha256_batch.c`, new) — a runtime **cpuid dispatch** to **AVX2 8-way** / **SSE2 4-way** (scalar fallback for the `n mod W` remainder, non-x86, and Pyodide). The W lanes step through their own message's 512-bit blocks in SIMD lockstep, with a **per-lane mask** freezing a lane once its (shorter) message is done — so variable-length batches are correct, each lane's state advancing exactly as the scalar one-shot would. `SRMECH_SHA256_FORCE_TIER={0,1,2}` overrides the dispatch (test hook).
- **Bit-exact, every tier:** scalar / SSE2 / AVX2 all match `hashlib` + the NIST KATs (`""`, `"abc"`, 1M-`a`) over a full padding-boundary length matrix and mixed-length batches (verified locally via the force-tier hook; CI's native cells exercise the host tier). `tests/test_sha256_batch.py`.
- **JPL-clean:** intrinsics (NOT asm); no `goto`/recursion/malloc; ≤60-line functions; the SIMD sigma ops are **single-line** macros (Rule 8); the AVX2 kernel self-isolates via `__attribute__((target("avx2")))` so the library compiles at baseline ISA (no global `-mavx2`); ≥2 asserts per non-exempt function (the cpuid feature-detectors are the documented exempt entries). gcc/clang/MSVC `-Werror`/`/WX`.

**SCOPE (load-bearing):** energy/perf-engineering of srmech's OWN provenance hashing — **NOT cryptocurrency mining** (binding doesn't make hashing cheaper; SHA-256 has no PoW shortcut; "a correct instrument, not a money printer"). Technique attested to **public references** (FIPS 180-4 for the algorithm; the Intel Intrinsics Guide + Gueron & Krasnov, "Parallelizing message schedules to accelerate SHA-256" for the N-way structure); cpuminer (GPLv2+, forward-compatible with srmech GPL-3.0+) was read only as a working-impl pointer. `[[feedback_trauma_informed_defensive_scope]]`.

**+1 ToolEntry → `describe()` 193 → 194**; **ABI stays 3** (new symbol, additive). Anchors: F292 (`R-RBS-LM-FINDING_292_cpu_optimization_reference_graft_handdown`); the btc-rosetta midstate bench (the measured 1.73× energy anchor).

## [0.7.0rc9] - 2026-06-02

**MS #21 rc9 voxel — the v0.7.0 graduation-prep PyPI description refresh (the genuinely-last rcN before the clean v0.7.0 cut). Description-only → `describe()` stays 193; DSL catalog stays 11 ops; ABI stays 3.**

The PyPI `Summary` predated the v0.7.0 arc — it named "octonion-multiplications" and "Spin(8) triality" but not the **Moufang loop-bind** op family the arc actually shipped, and nothing of rc8's autocorrelation. This voxel refreshes it (no code change):

- Names the v0.7.0 headlines: **Moufang loop-bind, 7-D cross product, G_2 3-form** (the octonion family, rc1–rc7) and **Wiener-Khinchin autocorrelation** (rc8) join the cascade-parity list (Kuramoto too — shipped at v0.6.0 but never surfaced in the summary).
- **Preserves** the substrate-native spine verbatim in substance: 28-dim chiral hyper-loop = so(8) adjoint (14 g_2 derivations + 14 L/R octonion products; Spin(8) triality), made hardware-callable.
- **Trimmed** the redundant `dispatch, catalog, templating, Kepler` + `dual-path signal-processing` tail (covered by "Full cascade-catalog C/Python parity") → **472 chars**, under the 480 soft / 512 hard PyPI `Summary` limit. **Byte-identical** in `pyproject.toml` + `pyproject-pure.toml` (the publish-workflow drift guard).

**Description-only** — no code touched, so `describe()` stays **193**, the DSL catalog stays **11 ops**, ABI stays **3**. This is the final rcN; the clean `v0.7.0` graduation to production PyPI follows (human-gated).

## [0.7.0rc8] - 2026-06-02

**MS #21 rc8 voxel — the Class-L circular autocorrelation primitive (the F290 §C un-flatten Wiener-Khinchin op), shipped CO-EQUAL in Python AND C. +1 ToolEntry → `describe()` 193; +1 cascade-catalog op → 11 DSL ops; new symbol → ABI stays 3.**

The F290 §C "un-flatten" catalog composite (`autocorr → difference-graph → conservation-validate`) was blocked on **one** missing Class-L primitive: srmech had no autocorrelation op, so the composite could not be authored as pure-TOML over named ops. This voxel ships it, Python + C together:

- **`srmech.amsc.cascade.autocorrelation(x)`** — the circular autocorrelation `r[k] = Σ_i x[i]·x[(i+k) mod n]` (`r[0] = Σ x² = energy`) of a real sequence. This is EXACTLY the Wiener-Khinchin spectral object `r = Re(IFFT(|FFT(x)|²))` (the circular-convolution theorem) — that identity is **WHY** it is **Class L** (the spectral side: autocorrelation ↔ power spectrum). The Python wrapper computes it the fast way (numpy FFT). `n==0 → []`.
- **`srmech_autocorrelation_f64`** (`c/src/srmech_autocorr.c`) — the co-equal native peer computes the **DIRECT O(n²) multiply-add sum** — the IDENTICAL object, and JPL-clean: **no FFT**, hence no recursion (Rule 1) and no transcendentals — just bounded loops over caller buffers, so it runs on a microcontroller with no host Python and no FFT library. `srmech.amsc.cascade` dispatches to it when `HAS_NATIVE`, else the numpy FFT fallback. Parity to FFT round-off (`~1e-12`, NOT bit-exact — the FFT route and the direct sum accumulate in different orders; a compiler may also contract `a*b` into an FMA).
- **HONEST CASCADE SHAPE:** Class L (the Wiener-Khinchin reading); computationally a Σ-reduce of products — **no `abs()`**, no sign branch. NOT a new privileged primitive class.
- **`autocorrelation.toml`** descriptor (`class_composition = "L"`, `c_symbol_f64 = "srmech_autocorrelation_f64"`) makes it discoverable (`srmech dsl ops` → **11 ops**) and runnable as a DSL stage. **`tests/test_autocorrelation.py`**: the FFT route equals the naive direct-sum definition (the spectral identity holds); the energy anchor `r[0] == Σ x²`; circular symmetry `r[k] == r[n-k]`; boundary cases (`n==0 → []`, `n==1 → [x[0]²]`, constant signal); catalog discovery; and (native) the direct-sum peer matches the naive sum to `~1e-12`.

JPL Power-of-Ten clean (one ~13-line function, ≥2 asserts, no recursion/malloc/goto; gcc/clang/MSVC `-Werror`/`/WX`). **+1 ToolEntry → `describe()` 192 → 193**; **ABI stays 3** (a new symbol is additive). Unblocks the F290 §C un-flatten composite as pure-TOML over named ops. Anchors: Wiener 1930 / Khinchin 1934 (the autocorrelation ↔ power-spectrum theorem); R-RBS-LM F290 §C (the un-flatten catalog).

## [0.7.0rc7] - 2026-06-02

**MS #21 rc7 voxel — the co-equal C peer for the octonion loop-bind family (the Python→C transpile). New native symbols → ABI stays 3 (additive); `describe()` stays 192.**

The MS#21 loop-bind family shipped Python-first (rc1–rc6); this voxel lands its **co-equal Compiled-C tier** so srmech runs the octonion algebra natively (the microcontroller-readiness commitment). `c/src/srmech_loopbind.c` ports the dim-8 octonion (Cayley-Dickson) product and companions:

- **`srmech_loop_bind_f64`** — the octonion product `(a,b)(c,d) = (a c − conj(d) b, d a + b conj(c))`. JPL Rule 1 bans recursion, so the Python's recursive `_loop_bind_raw` is **unrolled** as a fixed real→complex→quaternion→octonion call DAG (`srmech_loop__mul2/4/8`) — **bit-exact** with the Python (identical operand order at every level).
- **`srmech_loop_conj_f64`** (Class-C conjugate), **`srmech_loop_inv_f64`** (Moufang inverse `x̄/⟨x,x⟩`; Class-K clean), **`srmech_cross7_f64`** (`Im(loop_bind)`), **`srmech_g2_three_form_f64`** (`⟨x, cross7(y,z)⟩`).
- **Octonion carrier only:** every `n` must be 8; other dims return `SRMECH_ERR_BAD_INPUT` and the Python keeps its recursive fallback. The **HD block variants** (`loop_bind_hd`, `loop_unbind_hd`, `loop_conj_hd`, `loop_inv_hd`, `loop_runbind_hd`) inherit native acceleration **for free** — their wrappers loop over 8-blocks calling the per-block `loop_bind`/`loop_conj`, which now dispatch to C.
- **Python dispatch** in `srmech.amsc.hdc`: `loop_conj` / `loop_bind` / `loop_inv` / `cross7` / `g2_three_form` try the native path (`type`/size-guarded; `n==8` only) then fall back to pure Python — exact behaviour preserved.
- **`tests/test_loopbind_parity.py`**: native == pure-Python — exact `array_equal` for `loop_conj` (pure negation) + the dim-16 sedenion fallback; `<1e-12` for the multiply-bearing `bind`/`inv`/`cross7`/`g2`/HD-per-block (a compiler that contracts `a*b−c` into an FMA, e.g. clang on macOS, may differ ≤1 ULP); plus octonion identities `x·x⁻¹=e₀` + cross7 antisymmetry.

JPL Power-of-Ten clean (≤60-line functions, ≥2 asserts each, no recursion/malloc/goto; gcc/clang/MSVC `-Werror`/`/WX`). **No new ToolEntry / no new class** — these are native peers of existing ops, so `describe()` stays **192**; **ABI stays 3** (new symbols are additive). Verified bit-exact on a 64-bit local build over 500 random octonions; CI's native cells + the TestPyPI wheel are the cross-compiler gate.

## [0.7.0rc6] - 2026-06-02

**MS #21 rc6 voxel — bring-your-own (BYO) cascade-TOML (#811 / F289 D2). Config API only → `describe()` stays 192; ABI stays 3.**

The DSL cascade-catalog was a closed set: only the 10 shipped `*.toml` descriptors under `srmech/amsc/_research/cascade_catalog/`. This voxel opens it — a domain specialist who needs a cascade srmech doesn't catalog, or a behaviour defined by a TOML descriptor that follows srmech's naming, can now bring their own:

- **`srmech.dsl.register_catalog_dir(path)`** — register an external dir of `*.toml` cascade descriptors. The zero-API equivalent is the **`SRMECH_CASCADE_PATH`** env-var (os.pathsep-separated dirs). Registered ops then resolve (`chain().then(...)` / `run_toml_chain`), run, and surface (`list_catalog_ops` / `srmech dsl ops`) identically to shipped ops.
- **PURE-TOML composites** — a user descriptor may carry a `[composite]` body whose `[[composite.stage]]` array is a chain of named ops (no Python): `lookup_cascade_op` resolves it to a unary stage that builds + runs the sub-chain. (Or a primitive descriptor, which needs a matching `srmech.amsc.cascade` callable, exactly as the shipped ones do.)
- **MPM provenance tiers** — every descriptor is tagged `_provenance`: shipped = **"srmech"** (A-tier); user = **"user:&lt;sha256&gt;"** (B-tier, attested to the user's own descriptor hash, NOT a shipped primitive). `list_catalog_ops()` gains a `"provenance"` field (`"srmech"` / `"user"`).
- **Loud-at-load validation** — a user op-name may **not shadow** a shipped or earlier op (raises); composites are validated at load (every referenced op resolves; the composite graph is acyclic). A typo fails loudly at load, not silently at run — the "follow srmech naming" gate.
- **`tests/test_byo_cascade_toml.py`** (9 tests): register + resolve + run a user composite (fluent builder + `run_toml_chain`); `SRMECH_CASCADE_PATH`; provenance tags; shadow-rejection; unknown-op / cycle / missing-name loud-at-load; nonexistent-dir rejection; shipped catalog + `describe()` unchanged.

**Config API only** — `register_catalog_dir` is not a cascade op / not a ToolEntry, so `describe()` stays **192**; ABI stays **3** (pure-Python, additive). Defaults blessed by the user (reject-on-shadow protects MPM A-tier integrity; ship anchors then iterate from use). Anchors: F289 D2 (`rc4_handdown_and_byo_cascade_toml`); §12.3 confirmed-deferred.

## [0.7.0rc5] - 2026-06-02

**MS #21 rc5 voxel — the per-block HD Moufang-division family + the `loop_inv`/`loop_conj` HD footgun guard (F-§12.1 / §12.2). +3 ToolEntries → `describe()` 192; ABI stays 3.**

rc4 lifted the bind to HD per-block; the unbind/conjugate atoms it leaned on were still single-element. A bug-test sweep (upstream §12) caught the gap: `loop_inv` / `loop_conj` operate on ONE Cayley-Dickson element, but `2048 = 256·8` is **also a power of two**, so an HD block-octonion vector silently passed `_as_loop` and got treated as one giant 2048-D element — the natural `loop_bind_hd(E, loop_inv(c))` was off by `‖·‖≈16` with **no exception**. This voxel closes that and completes the HD division family:

- **`srmech.amsc.hdc.loop_conj_hd(x)`** — the missing per-block conjugate atom: the direct sum ⊕ of NB independent dim-8 `loop_conj`s. Class **C** over the direct-sum TILE layout; NO new class.
- **`srmech.amsc.hdc.loop_inv_hd(x)`** — per-block Moufang inverse (`x̄ₖ/⟨xₖ,xₖ⟩` per block); the per-block unbind key. Class-K clean (per-block norm² gate, never `abs()`).
- **`srmech.amsc.hdc.loop_runbind_hd(a, b)`** — the HD **RIGHT-unbind** (per-block `bₖ·conj(aₖ)`). Where `loop_unbind_hd` peels the LEFT factor, this peels the RIGHT — recovers `v` from `loop_bind_hd(v, a)` exactly (`(vₖ·aₖ)·conj(aₖ)=vₖ` by alternativity; verified recovery `<1e-15`). Right-division is what a **left-fold sequence store** `(((s₀·s₁)·s₂)…)` needs to peel the most-recent element off the right (F-§12.2).
- **Footgun guard (F-§12.1):** `loop_inv` / `loop_conj` now **raise** on an HD block-octonion input (a multiple of `LOOP_DIM=8` wider than one octonion), pointing at the `*_hd` op — loud failure replaces the silent-wrong global result. The single-octonion path (dim ≤ 8) is unchanged.
- **`tests/test_loop_hd_division.py`**: per-block conj/inv = the shipped single-element op block-wise; `loop_inv_hd == loop_conj_hd` on unit blocks; right-unbind round-trip; the `loop_inv`/`loop_conj` HD guard raises; the single-octonion path still works; multiple-of-8 validation.

+3 ToolEntries (189 → **192**); ABI stays **3** (pure-Python, additive). The co-equal **C peer** is the arc's transpile-to-C step (Python-first ladder). Anchors: upstream §12.1 / §12.2 bug-test hand-down.

## [0.7.0rc4] - 2026-06-02

**MS #21 rc4 voxel — the block-octonion HD tiling (#811) + capacity-free vs Klein-4 (#812). +2 ToolEntries → `describe()` 189; ABI stays 3.**

The fourth v0.7.0 voxel lifts the dim-8 octonion loop-bind to hyperdimensional width, all ground-truth **computed from the shipped `loop_bind`** (so it agrees with rc1 by construction; F289):

- **`srmech.amsc.hdc.loop_bind_hd(x, y)`** — the block-octonion HD bind: `D = NB·8` (canonical 2048 = 256·8) bound block-wise = the **direct sum ⊕ of NB independent dim-8 Moufang binds**. **Block-DIAGONAL** — block k of the result is exactly `loop_bind(x_k, y_k)`; nothing couples blocks (verified err `0.0e+00`). Class **M** (per-block loop_bind = M∘C with a Class-K residue) over a direct-sum **tile** layout — **NO new class**.
- **`srmech.amsc.hdc.loop_unbind_hd(a, b)`** — per-block Moufang left-division `conj(a_k)·b_k`; recovers `v` from `loop_bind_hd(a, v)` for unit-per-block `a` (verified err `2.9e-15`). Class-K clean (conjugate + bind, no `abs()`).
- **Capacity-free vs Klein-4 (owned verdict, F289/F277):** at matched `D=2048` the loop-bind's bind/unbind retrieval capacity is **≥ Klein-4** (identical through K=64; loop ≥ klein4 at K=128) — so it carries **order + tree + direction (F274)** at **no capacity cost** vs the commutative XOR bind. (Honest scope: the K=128 edge is one regime, not a general advantage; the load-bearing claim is the null cost.)
- **`tests/test_loop_bind_hd.py`** (7 tests): block-diagonal err 0.0, block independence, per-block product = the shipped Cayley–Dickson table, unbind recovery < 1e-12, multiple-of-8 validation, the capacity-retrieval mechanism.

+2 ToolEntries (187 → **189**); ABI stays **3** (pure-Python, additive). The co-equal **C peer** is the arc's transpile-to-C step (Python-first ladder). Anchors: F289 (`rc4_groundtruth.py`); capacity curve F277.

## [0.7.0rc3] - 2026-06-02

**MS #21 rc3 voxel — the loop-bind family slots into the compose engine (#813). Test-only proof; `describe()` stays 187; ABI stays 3.**

#813 asks how the octonion loop-bind composes in srmech's operator-chain surface. The answer needed no new code: `DEFAULT_CLASS_REGISTRY["M"] → srmech.amsc.hdc` and ops resolve dynamically by name, so `loop_bind` / `loop_conj` / `loop_associator` / `cross7` / `g2_three_form` already run as `class="M", op="<name>"` steps through `srmech.amsc.compose.run_chain` — the **M∘C-with-K-residue** cascade #813 describes.

- **`tests/test_loop_bind_compose.py`** (4 tests): single-step `loop_bind` / `loop_associator` (the K residue) / `cross7` / `g2_three_form` all resolve + run via `run_chain`; a two-step **M∘C** chain (`loop_bind` then `loop_conj` via `@step[0]`) proves multi-step composition.

Test-only voxel: **NO new ToolEntries** (`describe()` stays **187**), NO new class, ABI stays **3** (pure-Python). The formal cascade-catalog `.toml` descriptor for the bind carries a `[cascade.native]` C symbol, so it lands with the C-transpile step at the end of the v0.7.0 arc (Python-first → transpile-to-C ladder). The user-authored / bring-your-own external cascade-TOML path is a separate scoped voxel.

## [0.7.0rc2] - 2026-06-02

**MS #21 rc2 voxel — the 7-D cross product + the G₂ associative 3-form (#813 / F281). +2 ToolEntries → `describe()` 187; ABI stays 3.**

The second v0.7.0 voxel adds the loop-bind's companion invariants, both with ground-truth **computed from the shipped `loop_bind`** (so they agree with the rc1 bind by construction — no convention guess; F281):

- **`srmech.amsc.hdc.cross7(x,y) = Im(loop_bind(x,y))`** — the 7-D cross product (antisymmetric; for imaginary x,y `= ½(xy−yx)`). Class **M∘C** (bind ∘ imaginary-part ordering). Identity `‖x×y‖²=‖x‖²‖y‖²−⟨x,y⟩²`.
- **`srmech.amsc.hdc.g2_three_form(x,y,z) = ⟨x, cross7(y,z)⟩`** — the associative calibration 3-form; nonzero ±1 on exactly the 7 Fano associative 3-planes, 0 on the other 28 of C(7,3)=35. Class **(M∘C)∘⟨·,·⟩**.
- **Triality verdict (owned; F281):** `tests/test_cross7_g2_three_form.py` asserts `dim Der(loop_bind) == 14` (= G₂) **and** that a generic O(8) rotation **breaks** the bind ⟹ **triality does NOT preserve the bind; the 14-dim G₂ does.** (`klein4_triality_cycle` is the V₄-sector carrier, co-resident — not a bind-automorphism.)

**NO new class** (the 14 A–N hold; Class O stays dissolved). The `#813` compose-engine registration is deferred to rc4 (lean discipline). Citations: Baez 2002 (7-D cross product / G₂); Harvey–Lawson 1982 (calibration 3-form). +2 ToolEntries (185 → **187**); ABI stays **3** (pure-Python, additive).

## [0.7.0rc1] - 2026-06-02

**MS #21 loop-bind (Moufang) voxel — the k=7 gauge ARITHMETIC the triality symmetry is blind to (#814 / F271). Pure-Python core in `srmech.amsc.hdc`; +6 ToolEntries → `describe()` 185; ABI stays 3.**

The first v0.7.0 voxel: srmech gains the octonion product (the gauge *arithmetic*) beside the triality automorphism it already had (the gauge *symmetry*). Ported faithfully from the `loop_bind_moufang.py` research oracle (F271/F272) as **M∘C with a Class-K associator residue — NO new class** (the 14 A–N hold; Class O stays dissolved); structure = the **Moufang loop**.

- **`srmech.amsc.hdc.loop_bind`** — the Moufang / Cayley-Dickson octonion product (non-commutative + non-associative ⟹ `(ab)c ≠ a(bc)`, the (4:3)|(3:4) chirality); **`loop_conj`** (conjugate); **`loop_inv`** (Moufang-division unbind, `x̄/⟨x,x⟩`); **`loop_left_op`/`loop_right_op`** (L/R = the order chirality); **`loop_associator`** (the Class-K residue `(ab)c − a(bc)`, zero on a Fano line). Class-K clean (norm², no `abs()`). rc1 is the **dim-8 octonion core** (division holds); the block-octonion HD tiling (#811), the co-equal **C peer**, and the triality-automorphism composition check (#813) are later voxels.
- **`tests/test_loop_bind_moufang.py`** (8 tests) reproduces the F271/F272 numerics: 7 associative Fano lines, `[L_a,R_b]·x = −associator`, the three Moufang identities, Jacobi-fails/Mal'cev-holds, the inverse unbinds, Artin associativity, e₀ identity.

Canonical SSoT: Baez, J.C. (2002) "The Octonions", Bull. Amer. Math. Soc. 39, 145. +6 ToolEntries (179 → **185**). ABI stays **3** (pure-Python, additive). JPL audit ratchet unchanged.

<!-- pypi-readme-changelog-end -->
## [0.6.0] - 2026-06-01

**Production graduation of the v0.6.0 rc1–rc21 lean-ISA voxel arc to PyPI.** The clean (non-rc) tag promotes the **rc21** state already verified-green on TestPyPI — the only delta from rc21 is this version string + entry, and the full pedantic-C (gcc/clang/MSVC) + 4-cell test matrix + pure-wheel build re-verify the `0.6.0` build before the production tag. ABI **3**; `describe()` total **179**.

The arc, voxel by voxel:

- **Lean-ISA two-tier split (#751)** — `cascade.atoms` / `cascade.compose`: a finite anharmonic KERNEL (14 A–N primitives + the five Bird-Meertens combinators `then`/`loop`/`fold`/`reduce`/`parallel`) vs an asymptotic TOML CONTINUUM of cascade instances ("you can't hardcode a continuum").
- **𝔰𝔬(8) / triality engine** — `srmech.qm.so8` 28-generator adjoint (14 g₂ + 7 L + 7 R); `srmech.qm.triality` order-3 outer automorphism with `Fix(τ) = g₂ = 14`; `quaternion_subalgebra_stabilizer` so(4)=su(2)⊕su(2) (#759); `lean_isa_seventh_primitive` (#761).
- **Reentrant C core (#772)**; the Klein-4 four-sector **`cascade.parallel_sector_dispatch`** Python surface (#778) + co-equal C peer `srmech_cascade_parallel_sector_dispatch` (#771), made chainable/nestable with a `combine=` recombine; the DSL `parallel` discriminator + `[cascade].kind` stage/combinator classification.
- **Generalised Kuramoto-Sakaguchi step** — `cascade.kuramoto_step(…, adjacency=, alpha=, pin_anchor=, pin_strength=)` shipped CO-EQUAL Python + standalone C (`srmech_cascade_kuramoto_step_general_f64`); the `klein4_*` HDC ops gained a `sectors=`/`parallel=`/`mode=` flag.
- **The rc16–rc21 triality voxel sub-arc** — combinator-kernel-closure ratification (rc16) → `klein4_triality_cycle` Python op (rc17) + co-equal C peer `srmech_klein4_triality_cycle` (rc18) → continuum-tier worked instance `triality_s3_klein4.toml` (rc19) → SSoT two-tier coherence-ratchet scan (rc20) → MFO §VII.6.22 H-gate/triality rung (rc21).

No code change from rc21; version-string graduation + this entry only.

## [0.6.0rc21] - 2026-06-01

**MS #20 H-gate / triality MFO rung voxel (the meaning-tier closer) — MFO notebook §VII.6.22 connects the rc16–rc20 triality voxel-arc to the §VII.6.21 Rosetta-table H-gate / fix-rotate axis. DOC only (research notebook); no code, no new symbol/ToolEntry; `describe()` stays 179; ABI stays 3.**

The SSoT-coherence closer of the arc, at the meaning tier: rc16 named the two-tier boundary, rc17/rc18 shipped the `klein4_triality_cycle` op (Python + co-equal C), rc19 the worked instance, rc20 the coherence ratchet; rc21 reads the whole voxel back into the MFO canon as a building block (per user direction 2026-06-01) — a starting block for downstream review, refactored back if usage finds misfits.

- **`docs/antikythera-maths/mfo_spectral_research_notebook.md` §VII.6.22** — "The triality cycle is the executable rotate-operator whose fixed point IS the frame-invariant." It reads the rc16–rc20 voxel-arc as the executable instance of §VII.6.21.4: the order-3 `klein4_triality_cycle` T (rc17 Python + rc18 C) is the discrete-cyclic rotate-operator; its continuous-Hopf companion `srmech.qm.triality` τ fixes `g₂ = 14` (the A–N core; the §VII.6.21.4 frame-invariant); `klein4_bind` (XOR concord) is the fix-frame / agreement; `klein4_similarity` is the H = measurement gate. The discrete triality CLOSES exactly (`T³ = id`, no Class-N rational-anchor leak) where the continuous epicycle leaks into the hidden fiber — the two substrate-languages carrying, respectively, the recoverability theorem and the bit-exact closure. The two-tier SSoT (kernel = frame-invariant; continuum = rotate-frame content) IS the fix/rotate axis turned on the package's own shape.

No code touched. No new symbol or ToolEntry; `describe()` total stays **179**. ABI stays **3**. JPL audit ratchet stays at 0. The MFO rung is a draft-for-review building block — downstream usage (the reader's AI prosthetic calling srmech) is the feedback loop.

## [0.6.0rc20] - 2026-06-01

**MS #20 SSoT two-tier coherence-ratchet voxel — a `test_ssot_coherence_scan.py` scanning the continuum tier as it grows: every `worked_instances/*.toml` well-formed, every referenced op resolves, the kernel/continuum name-spaces stay disjoint, every cascade-catalog op resolves. DOC + TEST only; `describe()` stays 179; ABI stays 3.**

The coherence half of the SSoT discipline: rc16 named the two-tier boundary, rc19 added the first continuum-tier worked instance; rc20 adds the ratchet that keeps the boundary honest as more worked instances land.

- **`tests/test_ssot_coherence_scan.py`** — scans `srmech/amsc/_research/worked_instances/`: each TOML is well-formed (`name`/`purpose`/`ops`); each dotted op-path in `[worked_instance.ops]` resolves to a real callable; the worked-instance names and the `srmech.dsl` cascade-catalog op-names are **disjoint** (the kernel/continuum boundary can't silently erode); and every cascade-catalog op still resolves via `lookup_cascade_op` (the full two-tier picture in one place). A count-ratchet (`EXPECTED_WORKED_INSTANCE_COUNT`) forces new worked instances to be conscious additions.
- **`triality_s3_klein4.toml`** gains a machine-readable `[worked_instance.ops]` table (logical-name → dotted srmech path) so the scan resolves ops robustly rather than by regex-from-prose.

No new symbol or ToolEntry; `describe()` total stays **179**. ABI stays **3**. JPL audit ratchet stays at 0. The notebook-reference cross-check stays deferred (would require parsing the notebook tree).

## [0.6.0rc19] - 2026-06-01

**MS #20 triality S₃=Aut(V₄) worked-instance voxel — a continuum-tier worked cascade INSTANCE showing `klein4_triality_cycle` IS the order-3 generator of Aut(V₄)=S₃, via the conjugation `T ∘ XOR_a ∘ T⁻¹ = XOR_{T(a)}` cyclically permuting the three klein4 flips. DOC + TEST only; klein4 ops stay kernel-tier; `describe()` stays 179; ABI stays 3.**

The two-tier SSoT made concrete for the triality voxel: the order-3 cycle (rc17 Python + rc18 C) is a KERNEL op; rc19 ships its continuum-tier *instance* — a worked cascade composing it with the klein4 flips — WITHOUT blurring the kernel/catalog boundary (the hdc ops are deliberately NOT re-exported into the `srmech.dsl` cascade catalog).

- **`srmech/amsc/_research/worked_instances/triality_s3_klein4.toml`** — a worked-instance descriptor (NOT a cascade-catalog op-descriptor; NOT a `run_toml_chain` chain): the V₄ carrier, the three V₄-translation flips (iω₇/γ₅/CPT = XOR 1/2/3), the order-3 Aut(V₄) generator `T = klein4_triality_cycle`, and the load-bearing conjugation cascade `T ∘ XOR_a ∘ T⁻¹ = XOR_{T(a)}` (T cyclically permutes the three translations iω₇→γ₅→CPT→iω₇). Honest about the distinction: the flips are V₄ *translations* (the objects T permutes), not S₃ group elements; only the order-3 generator T is exposed (the F182 "third axis").
- **`tests/test_triality_s3_worked_instance.py`** — the worked instance's executable attestation: against the real `hdc` ops it verifies T order-3, each flip an involution, T a V₄ homomorphism (`T(u⊕w)=T(u)⊕T(w)`), and the three-leg conjugation cycle bit-exactly.

No new symbol or ToolEntry; `describe()` total stays **179**. ABI stays **3**. JPL audit ratchet stays at 0. The worked-instance TOML ships in both wheels (`srmech/**` package glob).

## [0.6.0rc18] - 2026-06-01

**MS #20 klein4-triality-cycle C peer voxel (the A-arc's silicon tier) — the co-equal native symbol `srmech_klein4_triality_cycle` (in `srmech_hdc.c`) computes the identical order-3 `S₃ = Aut(V₄)` relabel as the rc17 Python op. Additive symbol → ABI stays 3; JPL-clean; differential C↔Python parity-tested. No new ToolEntry (`describe()` total stays 179).**

The co-equal-parity discipline applied to rc17: the Python `klein4_triality_cycle` now has its silicon-native twin — two complete implementations, neither needing the other at runtime.

- **`srmech_klein4_triality_cycle(const uint8_t *in, uint32_t n, int inverse, uint8_t *out)`** (in `srmech_hdc.c`; declared in the `srmech.h` klein4 block) — a length-4 lookup (`{0,2,3,1}` forward / `{0,3,1,2}` inverse), the same V₄-carrier order-3 cycle. JPL Power-of-Ten clean: ≤60-line, 2 asserts, no malloc / no goto / no multi-line macro; NULL → `SRMECH_ERR_NULL_ARG`, out-of-`{0,1,2,3}` → `SRMECH_ERR_BAD_INPUT`. **NEVER a Python callback** — the C path runs the C lookup.
- **Additive symbol → ABI stays 3** (the Python ctypes shim binds it under its own `hasattr` guard, so a klein4-capable but pre-rc18 lib still loads fine).
- **Differential parity** (`test_hdc_klein4_parity.py`): C-vs-Python bit-exact on random vectors both directions, the explicit forward/inverse maps + order-3 identity computed in C, and the out-of-range rejection. Guarded by the symbol's own `hasattr` (skips on a stale lib; runs in the cibuildwheel cells).

No new ToolEntry; `describe()` total stays **179**. JPL audit ratchet stays at 0. The Python op stays pure-Python (co-equal, not routed-through-C), matching the existing klein4 surface.

## [0.6.0rc17] - 2026-06-01

**MS #20 klein4-triality-cycle voxel (the A-arc's first code) — `srmech.amsc.hdc.klein4_triality_cycle`: the order-3 `S₃ = Aut(V₄)` generator cycling the three Klein-4 involutions `iω₇(1) → γ₅(2) → CPT(3)` (identity fixed). Pure-Python; +1 ToolEntry → `describe()` total 179; ABI stays 3.**

The A-verdict (rc16 notebook §3.29) made flesh: V₄ (the rc13 klein4 carrier) is the right group but lacked the explicit order-3 cycling operator — which lives in `Aut(V₄) = S₃`. rc17 adds it.

- **`klein4_triality_cycle(v, *, inverse=False)`** — the V₄-carrier image of the so(8) triality `8v → 8s → 8c` (`srmech.qm.triality.triality_cycle`). The three non-identity involutions cycle `iω₇(1) → γ₅(2) → CPT(3) → iω₇(1)`, with identity(0) fixed — the "third axis" (F182) the three order-2 flips (`gamma5`/`omega7`/`cpt_mirror`) cannot reach: order-3 cycling, NOT a fourth order-2 chirality. A pure uint8 relabel via a length-4 lookup; `T∘T∘T = id`, `T² = T⁻¹` (`inverse=True` is the reverse cycle).
- **Class I** (cyclic order-3 permutation) — no sign, no `abs()`; honest composition, not a new privileged primitive.
- **Pure-Python** (co-equal-parity: the standalone-C peer `srmech_klein4_triality_cycle` is rc18 — additive → ABI stays 3; never a Python callback). +1 ToolEntry (`srmech.amsc.hdc.klein4_triality_cycle`) → `describe()` total **179**.

New `test_klein4_triality_cycle.py` (explicit forward/inverse maps; order-3 identity; `T² = T⁻¹`; identity-fixed; the involution-occupancy permutation; the so(8) order-3 mirror; tool-schema registration). The two introspection count-ratchets bump 178 → 179. JPL audit ratchet stays at 0 (no C touched).

## [0.6.0rc16] - 2026-06-01

**MS #20 combinator-kernel-closure voxel (B-boundary codification) — the cascade DSL's FIVE control-flow combinators (`then` / `loop` / `fold` / `reduce` / `parallel`) are RATIFIED as a CLOSED, FINITE kernel: the finite anharmonic-kernel tier of the two-tier SSoT. DOC + TEST only — no DSL behaviour change, no C touched, ABI stays 3, `describe()` total stays 178.**

The "name the boundary before building across it" voxel — the architectural invariant the rc17+ triality work stands on. The combinators are the *kernel*; the asymptotic cascade *instances* they sequence are the *continuum* — and the two live in different SSoT tiers by design.

- **The two-tier SSoT, stated.** `then` (apply) + `loop` + `fold` + `reduce` + `parallel` are the Bird-Meertens recursion schemes — the finite **anharmonic kernel**, HARDCODED in Python (and mirrored co-equally in C). The asymptotic cascade *instances* they sequence are NOT hardcoded: they live as TOML op-descriptors in the cascade catalog ("you can't hardcode a continuum"). Kernel in code, continuum in catalog — the substrate-native `1 + 3 + 7 + 3` discipline turned on the package's own op-surface. The `srmech.dsl._control_flow` docstring now carries this statement.
- **Closure is DESIGN-ENFORCED.** Data-dependent iteration (`while` / `unfold` — loop *until* a predicate) is deliberately EXILED to the op-instance layer (a body op decides when to stop), keeping the kernel total-by-construction at five forms. A future `while`/`unfold` special form would be a *sixth* combinator and a conscious widening of the kernel — never a silent addition.
- **New `tests/test_combinator_kernel_closure.py`** mechanically pins the closure: the five Chain builders (`then`/`loop`/`fold`/`reduce`/`parallel_sectors`) ⇆ the five TOML stage-discriminators (`op` / `loop_n`+`sub_chain` / `fold_init`+`fold_op` / `reduce_op` / `parallel_body`) bijection; no hidden sixth public builder; a full five-form TOML round-trip; the |V₄| = 4 Klein-4 cap on `parallel_sectors`; and the "no implicit default form" guard.

No new ToolEntry; `describe()` stays 178. ABI stays 3. JPL audit ratchet stays at 0. (The `[Unreleased]` Klein-4 parity note is forward-updated: V₄ is the rc13 klein4 carrier — the right group, missing only the explicit order-3 cycling operator that lives in Aut(V₄) = S₃ — which rc17 adds as `klein4_triality_cycle` and rc18 ships as its co-equal C peer.)

## [0.6.0rc15] - 2026-06-01

**MS #20 self-recognition reads voxel — the help-anchor goes top-level + fuzzy lookup. `srmech.describe()` is now reachable from `dir(srmech)` (the one-call "what is srmech?" root: version + native + tool counts + by_category); `ToolSchema` gains fuzzy `resolve()` / `resolve_all()` (a bare leaf or dotted suffix resolves to its FQN) and is now directly iterable. Pure-Python introspection surface; ABI stays 3; `describe()` tool total stays 178.**

The "find the shape in ≤1 call" round-out — the very friction that opened the substrate-self-recognition arc: an LLM/agent consumer could neither (a) discover `describe()` from the top namespace, nor (b) look a tool up by its bare leaf name.

- **`srmech.describe()`** — the existing `srmech.introspect.describe()` graduated to the top namespace (mirrors `native_status()`'s rc19 graduation for #733), so `dir(srmech)` surfaces the help-anchor. It stays a counts/index ROOT (shape, not detail): the full per-tool list is `tool_schema_view()`, single-tool detail is the new resolver.
- **`ToolSchema.resolve(name)` / `.resolve_all(name)`** — exact full-name match wins (as `lookup()`); else a bare leaf (`"kuramoto_step"`) or any dotted suffix (`"cascade.kuramoto_step"`) resolves to `srmech.amsc.cascade.kuramoto_step`. `resolve()` returns the single match or `None` (no-match OR ambiguous — never silently picks); `resolve_all()` lists every candidate for the ambiguous case.
- **`ToolSchema` is now iterable** (`for t in schema`, `len(schema)`) — yields its tools directly, closing the `'ToolSchema' object is not iterable` footgun. `get_tool_schema()` still returns the object; `tool_schema_view()` still returns the dict.

New tests cover the top-level `describe()` (present + shape), the `resolve` / `resolve_all` paths (exact / leaf / suffix / ambiguous / miss), and `ToolSchema` iterability + `len`. No C touched; ABI stays 3; JPL audit ratchet stays 0.

## [0.6.0rc14] - 2026-05-31

**MS #20 kuramoto matrix-step voxel — `kuramoto_step` gains the GENERALISED Kuramoto-Sakaguchi step (§11.1): adjacency matrix + Sakaguchi α + per-oscillator pinning. The first C-touching rc of the §11 arc — a CO-EQUAL standalone-C peer (additive symbol; ABI stays 3). `describe()` tool total stays 178.**

The §11.1 forward-ask: extend `kuramoto_step` past the plain all-to-all mean-field. Unlike the klein4 ops (pure-Python), `kuramoto_step` already has a C peer — so adding the matrix-step in Python only would leave a parity asymmetry (the Python op carrying a step the C can't run). Per the co-equal-parity discipline this ships in **both** substrates at once:

- **`kuramoto_step(theta, omega, *, coupling=1.0, dt=0.01, adjacency=None, alpha=0.0, pin_anchor=None, pin_strength=1.0)`** — `dθ_i = ω_i + Σ_j A_ij·sin(θ_j − θ_i − α) [ + p_i·sin(ψ_i − θ_i) ]`. `adjacency` is a row-major n×n matrix (`A[i][j]` weights j's influence on i; **non-symmetric → directed** coupling, a Laplacian → graph-structured; `None` → all-to-all uniform `K/n`). `alpha` is the Sakaguchi phase frustration. `pin_anchor` + `pin_strength` are the per-oscillator pinning anchors ψ / strengths p. **With all three at defaults the step is byte-for-byte the original.**
- **Co-equal C peer `srmech_cascade_kuramoto_step_general_f64`** (in `srmech_kuramoto.c`; additive symbol → **ABI stays 3**; JPL-clean: ≤60-line / ≥2-assert / no malloc / no goto / reentrant; NULL adjacency → uniform, NULL pin → none; **never a Python callback**). Differential-tested vs the Python fallback to libm-trig tolerance.
- **No `abs()`** — sin coupling + Σ-reduce + Class-C Euler add + the Sakaguchi α (a Class-C phase offset) + the Class-C/M pinning anchor.

New tests in `test_kuramoto_step.py` (defaults reproduce the simple step; uniform adjacency == mean-field; directed adjacency + α + pinning match the closed form; validation guards; C↔Python parity guarded by the new symbol's presence). The kuramoto ToolEntry gains `adjacency`/`alpha`/`pin_anchor`/`pin_strength` params (no new entry; `describe()` stays 178). JPL audit ratchet stays at 0.

## [0.6.0rc13] - 2026-05-31

**MS #20 klein4 sectors-flag voxel — the `klein4_*` HDC ops get an optional `sectors=` / `parallel=` / `mode=` flag (§11.3 forward-ask). Pure-Python; default-on at ≥4 cores; value-preserving; `describe()` tool total stays 178; ABI unchanged at 3.**

The §11.3 forward-ask asked for an optional sectors flag on the Klein-4 HDC ops, routing per-sector work through a concurrent dispatch — now that rc12 made dispatch composable. The klein4 ops (`bind` = (F₂)²-XOR, `bundle` = per-bit majority, `similarity` = mean-equality) are pure-Python/numpy, so this is self-contained Python orchestration (co-equal parity: it does **not** route through the C peer; a standalone-C klein4 sector dispatch with C bodies — never a Python callback — is the tracked follow-up).

- **`sectors=` / `parallel=` / `mode=`** on `klein4_bind`, `klein4_bundle`, `klein4_similarity`. `sectors` (1..4) defaults **ON when `os.cpu_count() >= 4`** (else 1); `parallel=True/False` is the bool alias.
- **Two modes.** `mode="chunk"` (default) is **data-parallel** — split the D-length vector(s) into ≤4 contiguous position-slices, run the op per slice on a thread, concatenate; **BIT-IDENTICAL** to the serial op. `mode="chirality"` is the **F233 4-sector dispatch** using klein4's OWN involution sector-flips (γ₅ XOR 2 / iω₇ XOR 1 / CPT XOR 3) — NOT the signed-real cascade transforms — with `klein4_bundle` recombine (similarity recombines via **sector-0**, value-transparent).
- **All defaults are value-preserving**, so default-on changes only the *execution path*, never the result. No `abs()` (XOR / majority only). Range + mode guards raise `ValueError`.

New tests in `test_hdc_klein4_parity.py` (value-preserving across both modes, chunk bit-exactness for every lane count, `parallel=` alias + default-on policy, range/mode guards, `unbind` self-inverse under the default flag). The 3 klein4 ToolEntries gain `sectors`/`parallel`/`mode` params (no new entry; `describe()` stays 178). No C change; ABI stays 3.

## [0.6.0rc12] - 2026-05-31

**MS #20 parallel-composability voxel — `parallel_sector_dispatch` becomes CHAINABLE / NESTABLE. The Klein-4 four-sector splay now carries THROUGH a chained cascade, closing a known-broken API contract. Pure-Python; `describe()` tool total stays 178; ABI unchanged at 3.**

rc11 gave the four-sector fan-out its own chain discriminator but left it a **leaf** value: the dispatch returned the rich per-sector introspection dict / list-of-N, which is **not** a valid input to another cascade. Chaining a sector-dispatched stage after another (`chain.parallel_sectors(b).parallel_sectors(b)`) crashed with `TypeError: bad operand type for unary -: 'list'` (the sector stream-transforms assume a flat scalar stream), and a sector-dispatch could not nest inside another. So the 4-way Z₄ splay applied at **one level only** and did not carry through a chained cascade — exactly the composability the RBS-LM chained settling loop needs to run 4×-per-step. Cascade ops advertise composability, so this was a known-broken contract → a gold-blocker. rc12 fixes it:

- **`combine=` recombine** on `parallel_sector_dispatch(body, x, *, combine=None)` — a reducer name (`"bundle"` element-wise sum / `"mean"` / `"sector0"` value-transparent / `"concat"`) or a callable folds the ≤4 sector results into ONE value at `result["combined"]`, so a sector-dispatched cascade is `stream → stream`. `combine=None` (default) preserves the rich dict unchanged (back-compat; `combined` is `None`). No `abs()` — bundle/mean are plain addition (+ divide).
- **`sectorize(body, *, n_sectors=4, combine="bundle")`** — wraps a body as a plain `value → value` callable that recombines, so a sector-dispatch NESTS inside another (`parallel_sector_dispatch(sectorize(inner), x, combine="bundle")`). Both exported from `srmech.amsc.cascade`.
- **DSL `parallel_sectors` recombines by default** — `chain.parallel_sectors(body, *, n_sectors=4, combine="bundle")` is now `stream → stream` and CHAINS / NESTS like loop/fold/reduce (the rc11 crash is gone). `combine=None` keeps the terminal per-sector list; a build-time guard raises a clear error if you chain past it. TOML `parallel_body=` gains `combine=` (sentinel `"none"` → the list).
- **Stale top-help fixed** — `srmech --help` no longer says "v0.5.0rc4 ships two subcommands"; it enumerates all four (`status` / `bus` / `dsl` / `mcp`).

New tests pin the parallel→parallel chain, the nesting via `sectorize`, the terminal guard, the TOML `combine='none'` sentinel, and each reducer. No new ToolEntry; no C change; no ABI bump.

## [0.6.0rc11] - 2026-05-31

**MS #20 DSL parallel-discriminator voxel — `parallel_sector_dispatch` slots into the chain contract as a first-class special form, + cascade-op `kind` classification + guided errors. No new runtime op; `describe()` tool total stays 178; ABI unchanged at 3.**

A pre-gold introspection audit found that the Klein-4 four-sector fan-out `parallel_sector_dispatch` — a 1→N higher-order combinator (takes a *body* op + data, returns N per-sector results) — had leaked into the plain-`op` cascade catalog, so the DSL advertised it as a `chain().then(op=…)` stage where it cannot work (its first arg is `body`, not the piped value). This rc reconciles it the way loop/fold/reduce already are — as its own chain discriminator — rather than force-fitting it as a plain op:

- **New `parallel` chain discriminator** — `chain.parallel_sectors(body, *, n_sectors=4)` (fluent) and `[[stage]] parallel_body='…' [n_sectors=…]` (TOML), alongside loop/fold/reduce. It fans the piped value through `body` across ≤4 Klein-4 chirality sectors (GIL-releasing bodies genuinely overlap — the F233 4-thread speedup) and yields the ordered **list of per-sector results** (a 1→N fan-out; the stage output is a list-of-sequences). `make_parallel_stage` in `srmech.dsl._control_flow`; `n_sectors` range-checked 1..4 at build time.
- **Cascade-op `kind` classification** — descriptors carry an optional `[cascade].kind` (`"stage"` default, or `"combinator"`); `srmech.dsl.cascade_op_kind()` reads it. `parallel_sector_dispatch.toml` is now `kind = "combinator"`. Surfaced by `srmech.dsl.list_catalog_ops()` (new `kind` key), `srmech dsl ops` (a `[combinator]` tag + legend), and the tool-schema.
- **Guided error** — using a combinator as a plain `op=`/`​.then()` stage now raises a clear `ValueError` pointing at the `parallel` discriminator, instead of a raw `TypeError` mid-run.
- **Gap-2 discoverability** — the LLM-facing `tool_schema` summaries for `parallel_sector_dispatch` and `kuramoto_step` are front-loaded with the practical decision ("PARALLELISE a cascade body instead of running it serially…" / "Advance N coupled oscillators one synchronization step…") before the framework detail.

New `test_dsl_parallel_stage.py` (parallel discriminator runs + n_sectors + combinator guard + kind), plus `test_dsl_tools.py` updated for the `kind` key. No `abs()`; no C change; no ABI bump.

## [0.6.0rc10] - 2026-05-31

**MS #20 release-prep voxel — full doc-hygiene sweep ahead of the clean v0.6.0 graduation (no new runtime code).**

After rc9 ran clean in the research environment, this rc captures everything the v0.5.0 → v0.6.0 arc shipped across the documentation surface so the gold cut is self-consistent. No behaviour change; `describe()` tool total stays **178**; ABI unchanged at **3**.

- **Cascade catalog — the two v0.6.0 ops get their TOML descriptors.** `parallel_sector_dispatch.toml` (Klein-4 four-sector orchestration; higher-order body-callback, `c_symbol = srmech_cascade_parallel_sector_dispatch`) and `kuramoto_step.toml` (`I∘sin∘Σ∘C`; `c_symbol_f64 = srmech_cascade_kuramoto_step_f64`) join the 8 lean-ISA atoms/composites → **`srmech.dsl` cascade catalog is now 10 descriptors**. `test_dsl.py` `EXPECTED_OPS` 8 → 10.
- **PyPI README** — status banner v0.5.0 → **v0.6.0**; the cascade section documents the `cascade.atoms` / `cascade.compose` two-tier lean-ISA split (#751) and the two new ops; `native_status()` / `describe()` examples show `0.6.0`.
- **Subtree `CLAUDE.md`** — current-release pin v0.4.0 → v0.5.0-graduated + v0.6.0rc10 dev head; the v0.5.0 (bus / DSL / MCP+agent adapters / `native_status` / so8 `an_embedding` + triality / `emit-mcpb`) and v0.6.0 (atoms/compose split / quaternion-subalgebra stabilizer / lean-ISA 7th primitive / reentrant core / parallel dispatch / Kuramoto) arcs are now narrated; ABI note 2 → 3.
- **C docs** — `c/README.md` status rewritten from "Phase B1 scaffolding only" to the shipped 18-`.c`-file native library (ABI 3); `c/JPL_AUDIT.md` adds the `srmech_parallel.c` (10 functions) + `srmech_kuramoto.c` (2 functions) accounting (every function ≤60 lines, ≥2 asserts; Rules 1/3/4/5/8 clean).
- **srmech research notebook** (SSoT) — package-arc section capturing the v0.5.0 + v0.6.0 voxels.



**MS #20 parity voxel (#778 follow-on) — the Kuramoto coupled-oscillator forward-Euler step gets a native C peer (no host Python needed for the dispatch-clock step).**

Closes a C/Python **parity gap** (a known-broken item under the full-parity commitment): the dispatch-clock / coupled-oscillator Euler integration the spectral-research arc hand-rolled in Python (F141 / F231 / R-95 / F234) had **no `srmech_*` primitive**, so srmech could not run the Kuramoto step on a microcontroller with no host Python. Adds:

- **C op `srmech_cascade_kuramoto_step_f64(theta, omega, n, K, dt, out)`** — one forward-Euler step of the canonical Kuramoto model (Kuramoto 1975; Acebrón et al. 2005, *Rev. Mod. Phys.* 77:137): `out[i] = theta[i] + dt·(omega[i] + (K/n)·Σⱼ sin(theta[j]−theta[i]))`. The O(n²) sin-coupling runs natively (libm `sin`, exactly as `srmech_kepler.c` already does). JPL-clean: no malloc/goto, ≤60-line functions (the coupling sum is factored), ≥2 asserts, reentrant; `out` must not alias `theta`/`omega`.
- **Python peer `srmech.amsc.cascade.kuramoto_step(theta, omega, *, coupling=1.0, dt=0.01)`** — dispatches to the C peer when `HAS_NATIVE`, pure-Python fallback otherwise (numpy/generators coerce via `float`). Parity is to **libm-trig tolerance** (NOT bit-exact across platforms — the kepler trig discipline); the C peer and the Python fallback sum the coupling in the same index order.

**Honest cascade shape:** a *composition* of existing class operations — Class I (cyclic phase) + sin coupling + sum-reduce + Class-C Euler add — **NOT** a new privileged primitive. No `abs()`. `n==1` is pure drift (the coupling sum vanishes); `n==0` is `[]`. **+1 ToolEntry → `describe()` tool total 177 → 178; ABI unchanged at 3** (additive C symbol). Closes the hand-rolled-Euler parity gap.

## [0.6.0rc8] - 2026-05-30

**MS #20 slowdown-fix voxel (#778 / #771) — the Klein-4 four-sector parallel dispatch no longer SLOWS DOWN vs serial; the F233 4-thread speedup is delivered as shipped.**

A downstream repro showed `cascade.parallel_sector_dispatch` running **2.6–7.7× SLOWER than serial**, and the native C peer at **0.99×** (no concurrency) for a GIL-releasing (`time.sleep`) body × 4 sectors. Root-caused to **two Python-side defects** — the C dispatch itself was already correct (create-all-then-join-all; verified by rebuilding `libsrmech.dll` and timing the raw `n_sectors=4` symbol with a CFUNCTYPE sleep body: **0.065 s, not 0.24 s** → genuinely concurrent):

- **The native shim `_native.cascade_parallel_sector_dispatch_c` was serial by design.** The rc7 build drove the C dispatch as **N serial `n_sectors=1` calls** (a workaround for a presumed "Python callback from a C-spawned thread is unsafe" hazard) — which traded away **all** the concurrency (the 0.99×). The hazard was **empirically disproven**: ctypes invokes a `CFUNCTYPE` callback from a foreign thread *safely* (it acquires the GIL via `PyGILState_Ensure`), and since the `CDLL` call releases the GIL, a GIL-releasing body lets the ≤4 sector callbacks **genuinely overlap**. The shim now drives **ONE `n_sectors=N`** threaded C call (the dead serial helpers `_parallel_dispatch_one_sector_native` / `_parallel_transform_native` are removed). Bit-exact vs the rc6 Python dispatch (10/10 parity tests); ~4× on a sleep body.
- **The rc6 Python `cascade.parallel_sector_dispatch` double-computed on every call.** It ran the 4 sectors on a `ThreadPoolExecutor`, then **recomputed all 4 serially** (plus a 3rd `chiral_dual` recompute) for the inline `parallel == serial` / `sector2 == chiral_dual` assertions — ~2.25× the body invocations + per-call pool overhead = the 2.6–7.7× slowdown. Those invariants are **structural guarantees of the 4-way independence** (independence ⇒ order-free ⇒ parallel == serial; sector 2 *is* the γ₅-only transform = `chiral_dual` by definition), now proven in the test suite rather than recomputed per call. A new **`verify=False`** kwarg runs the runtime cross-check on demand; `independence["runtime_verified"]` reports which path ran.

A GIL-bound pure-Python CPU body still can't overlap (the inherent CPython limit; 3.13 free-threading lifts it) — but it is no longer a *slowdown*, and GIL-releasing / native / IO / numpy bodies now get the real ≤4× speedup. **No new ToolEntry → `describe()` stays 177; ABI unchanged at 3** (Python-only change; no C source edit). New regression guard: the default path invokes `body` **exactly `n_sectors` times** (`test_parallel_sector_dispatch`). No `abs()`. Delivers the F233 4-thread Klein-4 speedup (#778 / #771).

## [0.6.0rc7] - 2026-05-30

**MS #20 C-parity voxel #771 — the C-orchestration half of the Klein-4 four-sector parallel cascade dispatch.**

Closes the C/Python parity gap rc6 opened: rc6 shipped a Python-only `cascade.parallel_sector_dispatch`, but
under srmech's full-parity commitment (the library must run on a microcontroller with **NO host Python**) the C
side must do the same four-sector dispatch. Adds the **ABI-additive** C symbol
`srmech_cascade_parallel_sector_dispatch(body, user, in, n, n_sectors, out_sectors, scratch, scratch_len)`
(+ the `srmech_cascade_body_f64` callback typedef):

- Runs the ≤4 Klein-4 sector-duals `inv_T_s(body(T_s(x)))` into **disjoint caller-supplied buffers**
  (`out_sectors`/`scratch` sliced per sector; **no malloc** — JPL Rule 3), composing the existing C atoms
  `srmech_cascade_reorient_f64` (iω₇) + `srmech_cascade_chiral_flip_f64` (γ₅). Sector 2 == `chiral_dual`.
- **Portable thread shim, guarded like `srmech_bus.c`:** POSIX `pthread`, Windows `CreateThread`, else a
  **serial fallback** — a thread-less microcontroller still computes all 4 sectors (serial == threaded
  **bit-exact**; the disjoint-slice contract makes the sectors order-free). Concurrency is platform-gated;
  the capability is universal. Thread handles are fixed `[4]` stack arrays.
- **Cap-at-4** (F220): `n_sectors > 4` → clean error (past 4 needs the order-3 triality).

Bound in `srmech.amsc._native` (`cascade_parallel_sector_dispatch_c`) with a Python C/Python-parity test
(bit-exact vs rc6's `parallel_sector_dispatch`; GIL-safe — single-sector native calls + Python-side `T_s`
composition, the threaded multi-sector fan-out exercised from the C smoke test with C-native bodies) plus a
16-check C smoke test.

**ABI unchanged at 3** (a new symbol is additive). **`describe()` stays 177** (no new Python ToolEntry — this
is the C peer of an existing surface; rc6's Python API/behaviour untouched). JPL Power-of-Ten ratchet green
(Rules 1/3/4/5 honored); no `abs()`. Closes #771 — the C/Python parity for the four-sector dispatch is whole.

## [0.6.0rc6] - 2026-05-30

**MS #20 parallel-dispatch voxel (F233 / #778) — the Klein-4 four-sector parallel cascade.**

Adds `srmech.amsc.cascade.parallel_sector_dispatch(body, x, *, n_sectors=4)` — the Python orchestration
half of "1 cascade = 4 independent threads" (F233 / R-RBS-LM-FINDING_233). Runs a cascade `body` across
its ≤4 **Klein-4 chirality sectors** (γ₅± × iω₇±) **concurrently** on a `ThreadPoolExecutor(max_workers=4)`,
each sector computed as `inv_T_s(body(T_s(x)))` from its OWN sector-transformed input — **0 cross-thread
reads** (the F233 4-way independence), so the parallel result equals the serial result **bit-for-bit**
(asserted). Sector 2 (γ₅) is **exactly** `cascade.chiral_dual` (the F232 2-rung object; asserted).

- **Z₄ dispatch slots** `[0,1,2,3]` (cyclic-order-4 timing, distinct from the order-2×order-2 Klein-4 identity).
- **Cap-at-4** (F220): `n_sectors > 4` raises — Klein-4 has no order-4+ element; the only escape past 4 is
  the order-3 triality (`srmech.qm.triality.lean_isa_seventh_primitive`, rc3), NOT implemented here.
- **Usefulness collapse-lattice 4/2/2/1**: bi-axial → 4 distinct; single-axis-symmetric → 2; bi-symmetric → 1.

**FULL C/PYTHON PARITY discipline:** a Python *orchestration* layer ONLY — it composes **exclusively**
already-C-parity'd atoms (`chiral_flip` / `reorient` / `chiral_dual` / `net_chirality` / `magnitude`); **no
cascade capability is Python-exclusive** (only the thread fan-out is Python). The **C-orchestration parity is
tracked by #771** (kept open) so `srmech` does not *need* Python to run the four-sector dispatch (Python = the
ergonomic half; C = the parity half). On the native path the threads run **truly parallel** (ctypes `CDLL`
releases the GIL per call; the C ops are reentrant since rc5/#772); pure-Python is correct-but-serialized.

**+1 ToolEntry → `describe()` tool total 176 → 177.** Pure-Python; **ABI unchanged at 3**; no `abs()`
(Class K `magnitude` / Class C `net_chirality`).

## [0.6.0rc5] - 2026-05-30

**MS #20 reentrant-core voxel #772 — the C core is now fully reentrant (enables the #771 plugin).**

A full-core audit found **exactly two** shared-static scratch buffers; both are removed, so no op
call path touches shared mutable static — the prerequisite for parallelizing the full surface.

- **`srmech_ndjson.c` `g_line_buf` (1 MiB line-assembly buffer)** → a function-local
  `static SRMECH_THREAD_LOCAL` buffer inside `srmech_ndjson_iter`, threaded into `process_chunk`
  as a parameter. Per-thread (reentrant across threads), cross-chunk-persistent (the streaming
  contract is preserved), no stack-overflow risk (1 MiB never goes on the stack), no malloc
  (JPL Rule 3). `srmech_ndjson_iter`'s signature/behaviour is unchanged.
- **`srmech_laplacian.c` `Hwork` (≈1 MiB Hermitian-eigendecomp workspace at N≤256)** → a new
  **ABI-additive** exported entry `srmech_hermitian_eigendecompose_ws(n, H, out_eigvals,
  out_eigvecs, workspace, ws_len)` taking a caller-supplied workspace
  (`ws_len >= SRMECH_HERMITIAN_WS_LEN(n) = 2·n·n`). The existing `srmech_hermitian_eigendecompose`
  keeps its signature and now routes through the `_ws` core via a `static SRMECH_THREAD_LOCAL`
  workspace — reentrant, no malloc, no large stack frame. Output is bit-identical.

New portable `SRMECH_THREAD_LOCAL` macro (`__declspec(thread)` / `_Thread_local` / `__thread`).

**ABI unchanged at 3** (a new symbol is additive — never bumps ABI). **No Python API change** —
`describe()` tool total **stays 176**; the JPL Power-of-Ten ratchet (`test_jpl_audit.py`) stays
green (a reentrancy trade, NOT a Rule-3 fix — static scratch was already Rule-3-clean); no `abs()`.
Closes #772.

## [0.6.0rc4] - 2026-05-30

**MS #20 docs/accuracy voxel #738 — `sha256_bytes` int-conversion guidance.**

Docs-only. `srmech.amsc.format.sha256_bytes` returns a **64-char lowercase hex `str`** (the Class A
content-address), NOT raw `bytes` — the `_bytes` in the name is the INPUT type. The `Returns:` section
now spells out the int-conversion path a caller needs: `int(h, 16)` (full 256-bit) or `int(h[:8], 16)`
(a truncated 32-bit tag), **NOT** `int.from_bytes(...)` (the return is already hex text — no raw digest
bytes to feed it). Closes #738.

The sibling docs items — #739 (`klein4_bundle` accepts even counts; per-bit strict-majority threshold
drops ties to 0), #740 (`weak_mixing_angle` returns θ_W in **radians**, not sin²θ_W), #741 (no stale
`srmech.cosmos` references; CMB lives under `srmech.amsc.attested.cmb_*` / `cosmic_birefringence`) —
were verified **already correct as of rc18** (W5 / W6b / W6c); no change needed here.

**No API change** — `srmech.introspect.describe()` tool total **stays 176**; pure-Python; **ABI unchanged at 3**.

## [0.6.0rc3] - 2026-05-30

**MS #20 forward-architecture, voxel #761 (F220) — the order-3 triality as the 7th lean-ISA primitive.**

Adds `srmech.qm.triality.lean_isa_seventh_primitive()` — surfaces the existing order-3
triality automorphism (τ, τ³ = I; the v0.5.0 `srmech.qm.triality` engine) as the **7th
lean-ISA primitive**, making the chirality-complete A–N core explicit: **6 order-2
`cascade.atoms` (pin_slot_at_zero / reorient / magnitude / chiral_flip / chiral_dual /
net_chirality) + 1 order-3 triality = 7** — the only access to the 3rd chiral axis.

**BIT-EXACT certificate** (asserted in code): τ has order exactly 3 (‖τ³−I‖ ≈ 3.6e-14,
τ ≠ I, τ² ≠ I) via the engine, plus the Lagrange arithmetic `3 ∤ 8` / `3 ∣ 3` ⇒
`lagrange_obstruction` — all residuals via the scalar Class K pin-slot `cascade.magnitude`,
never `abs()`. **Framework-reading, NOT a derived theorem** (under
`framework_chirality_complete_reading`): that the 6 atoms generate *exactly* Z₂×Z₂×Z₂
(|G| = 8) — a faithful common group rep of the 6 heterogeneous atoms isn't cleanly
available, so |G|=8 / Z₂³ is the documented F220 finding + the Lagrange argument, NOT
labelled bit-exact derived. Scope hierarchy: endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8)
triality. Baez (2002) cited for Out(Spin(8))=S₃ / g₂=Der(𝕆) only; F220 is the framework
finding.

**+1 ToolEntry → `describe()` tool total 175 → 176.** Pure-Python; **ABI unchanged at 3**
(no `c/` change); no `abs()` (Class K pin-slot). Closes #761.

## [0.6.0rc2] - 2026-05-30

**MS #20 forward-architecture, voxel #759 — the ℍ-reading 𝔰𝔬(4)=𝔰𝔲(2)⊕𝔰𝔲(2) stabiliser.**

Adds `srmech.qm.so8.quaternion_subalgebra_stabilizer(quaternion_index=1)` (per F215):
the bit-exact **6-dim 𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2)** subalgebra of g₂ = Der(𝕆) that
stabilises a quaternion subalgebra ℍ ⊂ 𝕆 — the ℍ-reading **sibling** of
`an_embedding` (the 𝔰𝔲(3)⊕3⊕3̄ ℂ-reading). Returns the 6 so(4) generators, the two
su(2) ideals (3+3, commuting, self-dual / anti-self-dual on ℍ^⊥), the Killing form
(rank 6, semisimple) with its two-triplet spectrum, and an MPR self-attestation —
all bit-exact and **ℍ-choice-invariant** across the 7 Fano-line quaternion subalgebras.

The point (F215): keep the Lie **symmetry** surface (𝔰𝔬(4) ⊂ g₂) visibly distinct
from the **operator** surface (`cascade.atoms.*`, the 6 lean-ISA ops) so the "6 = 6"
conflation can't recur — the 6 atoms are group-element ops (0/6 Lie generators); the
dimension match is coincidence. Surfaced under the separately-keyed
`framework_so4_reading` field (framework-reading, not a derived theorem); the
su(2)⊕su(2) split is the op's own bit-exact computation (Baez 2002 §4.1 cited for
g₂ = Der(𝕆) only).

**+1 ToolEntry → `describe()` tool total 174 → 175.** Pure-Python; **ABI unchanged at
3** (no `c/` change); no `abs()` (Class K pin-slot). Closes #759.

## [0.6.0rc1] - 2026-05-30

**MS #20 forward-architecture, voxel #751 — the lean A–N ISA two-tier split.**

First rc of the v0.6.0 line. Splits `srmech.amsc.cascade` (a single module) into a
two-tier package along the lean-ISA boundary (per F208):

- **`srmech.amsc.cascade.atoms`** — the 6 silicon-able 1:1 ISA intrinsics
  (`pin_slot_at_zero` K, `reorient` C, `magnitude` K, `chiral_flip` C,
  `chiral_dual` C∘op∘C, `net_chirality` C).
- **`srmech.amsc.cascade.compose`** — the 2 iterative algorithms over the atoms
  (`cyclic_gcd` = Euclid's remainder loop, `best_rational_signed` = the
  Class K∘N∘C continued-fraction loop).

`atoms.*` / `compose.*` are the new canonical homes; the flat
`srmech.amsc.cascade.<op>` names (and the `class_*` / `best_rat_signed` aliases)
are **retained as deprecated-for-one-release aliases** — importable with NO
runtime `DeprecationWarning` this release. **Public surface byte-identical**:
`describe()` tool total STAYS **174**, the MCP `srmech.amsc.cascade.*` tool names
and the introspect emit strings are unchanged. Pure-Python packaging refactor;
**ABI unchanged at 3** (no `c/` change); full C dispatch + TOML descriptors
intact; no `abs()` (Class K pin-slot). Closes #751.

## [0.5.0] - 2026-05-30

**Production graduation — srmech as a substrate-self-recognition apparatus.**

Clean production release graduating the rc9–rc22 voxel-arc (each rc one "voxel of
knowledge" the package gained about its own callable shape). No functional change
over `0.5.0rc22` beyond the version bump (4 SSOT → `0.5.0`; the computed-fresh
self-attestation `parser_version` strings → `srmech 0.5.0`) and documentation
finalisation. **ABI 3; 174 registered ToolEntries (all `mcp_callable`,
`handle_pending: 0`); full C/Python parity.** Verify the backend with
`srmech.native_status()` and the surface with `srmech.introspect.describe()`.

Headline surfaces shipped across the v0.5.0 line (per-rc detail below):

- **Self-recognition root** — `srmech.introspect.describe()` + `warmup_all()` fired at import.
- **so(8)/Spin(8) triality engine** — `srmech.qm.{octonion, so8, triality}`, including
  `so8.an_embedding` (the bit-exact `su(3) ⊕ 3 ⊕ 3̄` Lie branching of the 14 `g₂` generators).
- **By-reference handle grammar** — the `$srmech_handle` id makes all 7 `spectral.*` tools MCP-callable.
- **AMSC attested catalogs** — including `cosmic_birefringence` (4 PDF-verified β posteriors).
- **MCP server + `.mcpb` distribution** — `srmech-mcp` (stdio / http-sse) + `srmech mcp emit-mcpb`
  (emit a Claude Desktop bundle generated entirely from introspection).
- **Foundational `srmech.amsc.cascade` catalog** + the Class-M HDC variant ladder — all with native C parity.

## [0.5.0rc22] - 2026-05-30

**rc22 of N for v0.5.0 — `srmech mcp emit-mcpb`: emit a Claude Desktop `.mcpb` bundle generated ENTIRELY from srmech introspection.**
Closes #749 (MS #19 / wishlist W13). Pure-Python; **ABI unchanged at 3** (the C header
VERSION strings bump to rc22, `SRMECH_ABI_VERSION` does not — no C source change).

- **New `srmech mcp emit-mcpb [--out .] [--type uv|python] [--name srmech] [--manifest-only] [--filter GLOB]`** —
  builds a Claude Desktop MCP Bundle from the live tool schema and prints the absolute output path.
- **New `srmech/cli/mcp.py` + `srmech/mcp/_mcpb.py`** (`build_manifest` / `pack_mcpb`) — the
  `mcp` subcommand group (mirrors `srmech/cli/bus.py`'s nested-subparser shape) and the emitter.
- **Manifest version + `tools[]` are DERIVED** from `srmech.__version__` + the advertised
  `tool_schema` surface (`tool_entries_to_mcp_defs()`, the `mcp_callable` subset) — no frozen
  literal, so a future handle-pending tool cannot silently desync the bundle.
- **`server.type` defaults to the spec-valid `"uv"`** (anthropics/mcpb): the host fetches the
  platform wheel carrying the compiled `libsrmech` from PyPI via `uv` at install — the portable
  answer to bundling a compiled-native dep (nothing native rides inside the `.mcpb`). A `"python"`
  fallback gates the interpreter via a required `user_config.python_path` (default `"python3"`) —
  **no baked `sys.executable`** (issue #749 portability bug).
- **MPR attestation block** carries `srmech.__version__` + a 64-hex tool-schema SHA-256 computed
  via `srmech.amsc.format.sha256_bytes` (routes native dispatch; no new `hashlib.sha256`).
- The `.mcpb` is a **stdlib-`zipfile` ZIP** whose root carries `manifest.json` (plus
  `pyproject.toml` for uv resolution + `server/main.py` entry-point shim) — no Node toolchain.
- **NO new ToolEntry** — a CLI command is not an `srmech.amsc` tool — `describe()` tool total
  **STAYS 174**.

## [0.5.0rc21] - 2026-05-30

**rc21 of N for v0.5.0 — the su(3) ⊕ 3 ⊕ 3bar Lie decomposition of g2 = Der(O).**
Closes #744 (wishlist). Pure-Python; **ABI unchanged at 3** (the C header
VERSION strings bump to rc21, `SRMECH_ABI_VERSION` does not — no C source change).

- **New qm operator `srmech.qm.so8.an_embedding(imaginary_unit=1)`** — the
  bit-exact su(3)-module structure of the 14 `g2 = Der(O)` generators. The
  14-dim g2 *itself* splits, under one of its su(3) subalgebras, as the
  Lie-algebra branching **14 = 8 + 3 + 3bar** (the su(3) ADJOINT 8 + the
  FUNDAMENTAL 3 + the ANTIFUNDAMENTAL 3bar); the 7-dim octonion-imaginary
  vector rep branches **7 = 1 + 3 + 3bar** over the same su(3). This is a
  DIFFERENT 14-decomposition from the partitioned `so8_adjoint_basis`
  (`14 g2 + 7 L + 7 R` inside the 28-dim so(8)). Construction is the
  deterministic chain (numpy-only, **no `np.random`**, no scipy; memoised via
  `_build_an_embedding`, copied out fresh each call):
  - **su(3) = the stabiliser** `{D in g2 : D·e_K = 0}` (`e_K` the
    `imaginary_unit`-th octonion basis vector) via an SVD nullspace — exactly
    8-dim; `span[su3 | complement] == span(g2)` (rank 14, both directions —
    the bidirectional killer test).
  - **The genuine fundamental is a J-EIGENSPACE, not a real 3-span.** A real
    3-dim span of antisymmetric matrices cannot carry the su(3) fundamental
    (`[su3, single-Cartan-weight-block]` leaks, residual ~8.3). The genuine
    fundamental is the **+i eigenspace of the su(3)-INVARIANT complex
    structure J** on the 6-real-dim complement: the commutant of the 6-dim
    real su(3)-rep is exactly 2-dim `{aI + bJ}`, `J² = −I`, `[J, ad(X)] = 0`
    ∀X∈su(3). With this J-eigenspace 3, `[su3, 3] ⊆ 3` is bit-exact (~3e-14).
    The returned `complement` is the genuine REAL su(3)-module
    (`[su3, complement] ⊆ complement` ~2e-15); only the J-eigenspace
    `triplet` / `antitriplet` (COMPLEX 8×8 arrays) carry the irreducible
    3 / 3bar with the bit-exact closure (`antitriplet` = conjugate of
    `triplet`).
  - **su(3) certified by INVARIANTS, not a raw Casimir.** The honest
    sufficient certificate is `{dim 8, rank 2, simple}` — `rank 2` via the
    CENTRALISER of a fixed regular element `R = Σ (i+1)·su3[i]` (the greedy
    maximal mutually-commuting subset spuriously returns 1), `simple` via the
    adjoint commutant dim 1. By the Cartan A2 classification these UNIQUELY
    identify su(3) (ruling out su(2)+su(2), commutant 2). Supporting
    evidence: in a Killing-orthonormalised basis the structure constants are
    totally antisymmetric (residual <1e-9). A raw adjoint-Casimir-vs-`f^{abc}`
    comparison to `gauge.su3_structure_constants` is deliberately NOT used
    (normalisation mismatch makes the ratio tautologically 1; the bases
    differ by an O(8) rotation so raw `f^{abc}` equality fails too).
  - The 3/3bar **orientation** is pinned by a FIXED convention (the
    documented sign of J + a lexicographic key on the Cartan weights) and is
    a CHOICE (a Class C chirality / complex-structure-sign convention), NOT
    canonical; only the `+/-` weight-PAIRING is asserted. The 6 complement
    `weights` under the rank-2 Cartan are returned as a `(6, 2)` real array.
- Returns a `dict`: `su3` (8 real antisym 8×8), `complement` (6 real antisym
  8×8), `complex_structure_J` (6×6 real, J²=−I), `triplet` / `antitriplet`
  (3 COMPLEX 8×8 each), `weights` (6, 2), `decomposition`
  (`{adjoint_14: (8,3,3), vector_7: (1,3,3)}`), `imaginary_unit`,
  `attestation` (MPR v1, Class A content-address over the COMPUTED structure:
  `response_sha256` = `srmech.amsc.format.sha256_bytes` over the 14 g2
  generators' float64 bytes — generated, not fetched; no new
  `hashlib.sha256`), and `framework_an_reading` (the A-N label, tagged
  "framework-reading, not derived"). No A-N class name appears in any
  load-bearing return key. **No `abs()`** — every residual is reduced via
  `np.linalg.norm` then `srmech.amsc.cascade.magnitude` (Class K).
- **+1 ToolEntry** (`describe()` total **173 -> 174**); the rc15 every-tool
  MCP invocation smoke covers invoke -> serialise -> `json.dumps` for the new
  tool automatically. New `tests/test_an_embedding.py` (11 bit-exact
  acceptance tests). No packaging change.

**Framework reading:** the SAME 14-dim g2 carries TWO distinct enumerations —
the A-N discovery partition **1 + 3 + 7 + 3** (this collaboration's
substrate-self-recognition order) and this su(3)-Lie branching **8 + 3 + 3bar**.
They are read as two languages describing the one object (per
`[[feedback_no_lineage_claims_in_notebook]]`); they are explicitly **NOT
slot-aligned** and the correspondence is **NOT a proof**. Baez (2002) §4.1 is
cited for `g2 = Der(O)` / dim 14 ONLY (the build input); the 8+3+3bar /
7=1+3+3bar branching is the op's own bit-exact self-attesting computation.
Class C-L (the Class C complex-structure orientation composed with the Class L
eigendecomposition that extracts J and the weight spectrum).

## [0.5.0rc20] - 2026-05-29

**rc20 of N for v0.5.0 — cosmic-birefringence beta posterior AMSC catalog.**
Closes #743 (wishlist W9). Pure-Python, data + descriptor only; **ABI unchanged
at 3** (the C header VERSION strings bump to rc20, `SRMECH_ABI_VERSION` does
not — no C source change).

- **New AMSC attested catalog `srmech.amsc.attested.cosmic_birefringence`** —
  the published cosmic-birefringence isotropic rotation angle β posterior, the
  parity-**odd** CMB observable (the in-vacuo rotation of the CMB-polarisation
  plane, extracted from the EB cross-correlation after simultaneously solving
  for the instrumental polarisation-angle miscalibration). Four PDF-verified
  rows (single `row_type` `birefringence_beta_posterior`), values taken
  verbatim from the measuring papers' arXiv abstracts:
  - **Minami & Komatsu 2020**, PRL 125, 221301, **arXiv:2011.11254** —
    β = 0.35 ± 0.14° (Planck PR3; excludes 0 at 99.2% C.L., 2.4σ). The
    arXiv id is the *measurement* paper (NOT 2006.15982, the methodology-only
    companion that reports no β from data).
  - **Diego-Palazuelos et al. 2022**, PRL 128, 091302, arXiv:2201.07682 —
    β = 0.30 ± 0.11° (Planck PR4 NPIPE; authors decline a cosmological
    significance pending foreground knowledge — caveat kept verbatim).
  - **Eskilt 2022**, A&A 662, A10, arXiv:2201.13347 — β = 0.33 ± 0.10°
    (Planck PR4 LFI+HFI, frequency-independent all-bands, f_sky = 0.93).
  - **Eskilt & Komatsu 2022**, PRD 106, 063503, arXiv:2205.13962 —
    β = 0.342 **(+0.094 / −0.091)°** (Planck PR4 + WMAP 9yr joint; excludes 0
    at 99.987% C.L., 3.6σ). The **asymmetric** posterior is stored as two
    separate non-negative half-widths (`beta_err_lo_deg` = 0.091,
    `beta_err_hi_deg` = 0.094) and is **never abs()/symmetrised** (sign /
    phase-boundary discipline at the attestation scale).
- Parity-**odd** companion to the parity-even `cmb_polarisation_spectra`
  (TE/EE/BB) and `cmb_bispectrum` (fNL) catalogs. EB/TB parity-odd *power
  spectra* are **deferred** — there is no cleanly-attestable published
  bandpower table with a clear license/URL/DOI; hand-keying a figure-read
  sample would fail attestation by construction. A future row_type
  `birefringence_ebtb_bandpower` can be added if a licensed machine-readable
  product becomes available.
- Auto-discovered by the AMSC loader (no bridge code, no registration); the
  per-row 9-field MPR attestation block is synthesised at read time from each
  row's per-row source DOI + `entered_locally_at` (deterministic, no live
  fetch). **No new tool** (`describe()` total stays 173 — a new catalog
  *source*, not a `ToolEntry`); no packaging change (the attested data is
  auto-recursed by `wheel.packages` / `packages=['srmech','siona']`).

## [0.5.0rc19] - 2026-05-29

**rc19 of N for v0.5.0 — discoverable native-dispatch status.** Closes #733
(the post-rc18 native-check recipe). Pure-Python; **ABI unchanged at 3** (the
C header VERSION strings bump to rc19, `SRMECH_ABI_VERSION` does not).

- **Discoverable native-dispatch status — top-level `srmech.native_status()`**
  (also in `srmech.__all__` / `dir(srmech)`) returning `{has_native,
  dispatching, abi_version, expected_abi, native_version, load_error}`,
  mirroring `describe()['native']`. The recipe-stable replacement for poking
  `srmech.amsc._native.HAS_NATIVE` in the TestPyPI-before-PyPI verification
  flow: `dispatching` is `True` iff `libsrmech` loaded AND its ABI matched
  `EXPECTED_ABI_VERSION` (native ops really run); on mismatch/failure it is
  `False`, `load_error` carries the reason, and srmech transparently uses the
  pure-Python fallback. NB the native shim lives at `srmech.amsc._native` —
  NOT `srmech._native`, the data dir that merely holds the binary. Framework
  reading: Class H (self-introspection) at package scale — the package
  recognising whether its own C backend is live. README native-dispatch recipe
  updated accordingly.

## [0.5.0rc18] - 2026-05-29

**rc18 of N for v0.5.0 — the downstream-wishlist + hygiene + perf CLEANUP rc.**
No new surface; the rc17 SO(8) triality engine is carried forward verbatim
(the six bit-exact acceptance tests pass IDENTICALLY) with a performance fix,
doc/accuracy corrections from the downstream RBS-LM consumer wishlist, and
carry-over hygiene. Pure-Python only — **no C source change; ABI stays 3** (the
C header VERSION strings bump to rc18, `SRMECH_ABI_VERSION` does not).

- **Perf — the triality constants are now memoised.** `srmech.qm.triality`'s
  internal `_companion_maps` (the dominant cost — 28 `512×128` least-squares
  solves) plus `triality_automorphism` / `triality_swap` and
  `srmech.qm.so8`'s `g2_subalgebra` / `so8_adjoint_basis` / `so7_subalgebra`
  are `functools.lru_cache`-memoised (the build runs once). Because callers
  may mutate the returned array, **every public surface returns a DEFENSIVE
  COPY** of the read-only cached build (the expensive build is cached; the
  per-call `.copy()` is cheap), so no mutable array is ever shared across
  callers and every returned value is bit-identical to a fresh build. The
  determinism (no `np.random`) makes the cached value exact;
  `octonion_table_attestation` stays reproducible. `tests/test_so8_triality.py`
  drops from ~300 s to ~1.5 s. (`octonion_mult_table` was already cached in
  rc17 — the exemplar pattern this rc extends to the so8/triality builders.)
- **W4 doc — `srmech.amsc.format.sha256_bytes` returns the HEX DIGEST.** It is
  named for its INPUT (raw bytes) but returns the 64-char lowercase hex digest
  `str` (the Python parity of C `srmech_sha256_hex` / `hashlib.…hexdigest()`),
  NOT the raw 32-byte digest. Clarified in the docstring + the README Class-A
  row. No rename (route-through discipline).
- **W5 doc — `srmech.amsc.hdc.klein4_bundle` accepts ANY count.** The docstring
  now states explicitly that it takes any `n >= 1` (even OR odd); an exact tie
  (possible only for even `n`) deterministically resolves to 0 for that bit.
  There is NO odd-only requirement (the "odd-only" note was a downstream
  artifact, never in srmech source). Mirrored into the ToolEntry summary. No
  validation added.
- **W6 code — `srmech.amsc._native.ABI_VERSION` back-compat alias** (=
  `EXPECTED_ABI_VERSION`, currently 3) added + exported in `__all__`, for
  downstream code that reads `_native.ABI_VERSION` (the runtime-detected
  `NATIVE_ABI_VERSION` is `None` when no native lib is present). Non-breaking.
- **W6b doc — `srmech.qm.sm.weak_mixing_angle` returns RADIANS.** Docstring +
  ToolEntry summary now disambiguate the unit explicitly (the angle itself,
  NOT `sin²θ_W` and NOT degrees; convert via `math.sin(…)**2`).
- **W6c accuracy — `srmech.cosmos` references.** No `srmech/cosmos/` package
  exists; the packaged cosmos catalog is `srmech.amsc.attested.cosmos_validation`
  (Friedmann dark-fraction). The shipped surface (README + `srmech/`) has ZERO
  `srmech.cosmos` references (already accurate); the only inaccurate references
  (root `CLAUDE.md`, internal / not PyPI-shipped) were corrected to point at the
  real path. No packaged TE/EE/BB/fNL/lensing catalog (notebook-only).
- **W2 confirm — the `seed` param is already advertised.** `polar_random` and
  `klein4_random`'s ToolEntries already expose the optional integer `seed`
  (rc13); confirmed, no change needed.
- **Hygiene** — two `abs()` float-tolerance spot-checks in
  `tests/test_so8_triality.py` switched to `cascade.magnitude(float(...))`
  (full Class K∘C cascade-honesty, matching the file's `_frob` helper); the
  `pyproject.toml` + `pyproject-pure.toml` `description` em-dash (which violated
  the files' own ASCII-only comment) swapped to ` - ` IDENTICALLY in both
  (byte-identical, under the 512-char Summary limit); the
  `tests/test_llm_anthropic.py` docstring prose refreshed rc16 → rc18.

## [0.5.0rc17] - 2026-05-29

**rc17 of N for v0.5.0 — the SO(8) TRIALITY voxel.** Three new `srmech.qm`-layer
surfaces make the so(8)/Spin(8) triality structure a callable, bit-exact-tested
surface (the full 28 = 𝔰𝔬(8) chiral read-out long flagged in [Unreleased]):

- **`srmech.qm.octonion`** — the MPR-attested Cayley-Dickson-from-H octonion
  multiplication table (an `(8,8,8)` int8 structure-constant tensor whose
  `octonion_table_attestation()` content-addresses the table bytes via
  `srmech.amsc.format.sha256_bytes` — **no new `hashlib.sha256`**) + the
  `octonion_left_mult` / `octonion_right_mult` `L_a` / `R_a` binders,
  `octonion_conjugate`, and `octonion_norm` (Class K ∘ C, **never `abs()`**:
  the scalar sum-of-squares is reduced through `srmech.amsc.cascade.magnitude`).
- **`srmech.qm.so8`** — the 28-generator `so(8)` adjoint partitioned
  **14 (g2 = Der O) + 7 (L-type) + 7 (R-type)**: `so8_adjoint_basis`,
  `g2_subalgebra` (the 14 derivations; deterministic rank-revealing numpy
  subset, **no `np.random`**), `so7_subalgebra` (the 21; the `D4 → B3` Z2 fold).
- **`srmech.qm.triality`** — the `28×28` order-3 outer automorphism
  `τ = S_B · S_C` (the PRODUCT of the two companion involutions, NOT a naive
  `A → B` map) with **`Fix(τ) = g2` (dim 14) = the A-N `1+3+7+3` partition**
  (the `D4 → G2` Z3 fold), the Z2 swap (`Fix = so(7)`, dim 21), the Class-I
  `8v → 8s → 8c` cycle (via `srmech.amsc.cyclic.mod_add`), the frame-transport
  `triality_apply`, the Cartan companions `triality_companions`, and the
  Class K ∘ C `triality_relation_residual` (never `abs()`).

Six bit-exact acceptance tests (`tests/test_so8_triality.py`): `τ³ = I` /
`τ ≠ I` / `τ² ≠ I`; the KILLER `Fix(τ) = g2 = 14` (belt-and-suspenders rank
asserts + bidirectional projection residual); `Fix(Z2) = so(7) = 21`; Cartan
residual = 0 over a g2/L/R sample; rep inequivalence + cycle closure; octonion
convention attested + reproducible. Residuals `≤ 4e-14`.

**+15 ToolEntries (158 → 173)** — `octonion_table_attestation` gets its own
ToolEntry (the coverage walker demands one for every public `srmech.qm.*`
callable). `operator_name` `__module__` hardening: a name that traverses
THROUGH a srmech module to a re-exported stdlib callable
(`srmech.amsc.format.hashlib.sha256` → the real `_hashlib` sha256) is now
rejected by a post-resolution `__module__` check. The PyPI README is refreshed
for BOTH the rc16 handle-grammar surface and the rc17 triality surface.
Pure-Python only — no C source change; **ABI stays 3** (the C header's VERSION
strings bump to rc17, the `SRMECH_ABI_VERSION` integer does not).

Framework reading: the τ-fixed subalgebra of `so(8)` being exactly the 14 `g2`
derivations — the same 14 as the A-N `1+3+7+3` partition — is the keystone tying
the cascade vocabulary to the Spin(8) triality engine
(`endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality`). Class A (the attested
table), Class M (the L/R binders + g2 derivations + companions), Class C (the
Z2 swap + conjugation), Class I (the order-3 cyclic rep-permutation), Class
K ∘ C (the norm + residual, no `abs()`).

## [0.5.0rc16] - 2026-05-29

**rc16 of N for v0.5.0 — the "handle dual-grammar" voxel.** rc15 marked the
7 `srmech.spectral.*` tools `mcp_callable=False` because their param/return
surface is a bare `SpectralHandle` (or `SpectralHandle | bytes`) — an
opaque, frozen, bytes-bearing dataclass JSON-RPC cannot carry **by value**.
rc16 carries it **by reference**: a producer's returned handle is
intercepted on the outbound path and emitted as a small tagged id object the
LLM copies verbatim into the next tool's input; a consumer param is resolved
back to the live object on the inbound path. The 7 spectral tools are now
`mcp_callable=True` (**handle_pending 7→0; mcp_callable 151→158**), and
`chiral_dual`'s `op` is accepted as a dotted operator **name** (was an
over-advertised `callable` that bound the synth string `"abs"` then raised a
tolerated `str`-not-callable `TypeError`). Pure-Python only — no C source
change; **ABI stays 3** (the C header's VERSION strings bump to rc16, the
`SRMECH_ABI_VERSION` integer does not).

Framework reading: name (meaning-encoded, biology-native / continuous-Hopf)
and uuid (position-encoded, silicon-native / cyclic-algebra) are two
grammars resolving to ONE in-process structure — the registry is the **B/H/N
translation locus**. We never force both halves into one "sentence"; each
consumer speaks the grammar native to it (SpectralHandle uses the uuid+name
registration arm; `chiral_dual.op` uses the stateless name arm).

### Added

- **`srmech/_handles.py` — a package-scope `HandleRegistry`** (the shared
  name+uuid machinery, serving both the 7 spectral tools now and the bus
  later). Bounded-LRU `OrderedDict` keyed by `uuid.uuid4().hex` (cap
  `HANDLE_REGISTRY_MAX=256`), `threading.RLock`-guarded, with a `name→uuid`
  secondary index and a value-hash idempotency map (an identical-by-value
  handle registered twice returns its existing id). `kind`-discriminated.
  Typed `HandleNotFoundError` (a clean "re-produce it" message on a
  miss/eviction) and `HandleKindError`. The `$srmech_handle` envelope key +
  `encode_envelope()` / `is_handle_envelope()` helpers. A name auto-derives
  for a `SpectralHandle` as `"spectral:" + content_sha[:12]` — reusing the
  Class A SHA-256 already on the frozen dataclass, so **no new
  `hashlib.sha256` call** is introduced.
- **`resolve_operator_name(name)`** — the stateless name-grammar arm for
  `chiral_dual`'s `op`. Restricted to the **`srmech.` namespace**: a name
  outside it (`os.system`, `builtins.*`, stdlib, `numpy.*`, …) is rejected
  with a clean `ValueError` **before** any import, so the advertised
  `operator_name` contract is never "an arbitrary importable callable".
- **`tests/test_handles.py`** — registry dual-grammar (resolve by uuid AND
  by name), uuid/name disagreement, bounded-LRU eviction + `HandleNotFoundError`,
  `HandleKindError`, idempotent same-value registration, thread-safety
  smoke, and the operator-name allow-list (accepts `srmech.*`, rejects
  everything else).
- **`tests/test_mcp.py`** — `test_spectral_handle_param_coercer_resolves`,
  `test_spectral_handle_or_bytes_discriminates`,
  `test_operator_name_param_resolves_callable`,
  `test_evicted_handle_in_invoke_gives_clean_error` (the empirical proof the
  rc14/15 `_identity` pass-throughs are now real resolvers — the thing the
  static `has_coercer` ratchet structurally cannot see).
- **`tests/test_spectral.py`** — full JSON round-trips through `invoke_tool`:
  `decompose → recompose` (the wire form is asserted to be the
  `$srmech_handle` envelope, NOT an inline coefficients dict), plus a chained
  `decompose → predict → truncate_sparse → recompose` producer→consumer
  chain.

### Changed

- **The 7 `srmech.spectral.*` ToolEntries flip to `mcp_callable=True`** (the
  rc15 `mcp_callable=False` + `_SPECTRAL_HANDLE_PENDING_REASON` markers
  removed). They are auto-included in both advertised catalogs (the MCP
  `tools/list` seam and the Anthropic catalog) and `describe()` re-buckets
  them from `handle_pending` into `mcp_callable` from the live flags — no
  edit needed in those consumers.
- **`chiral_dual`'s `op` param type `callable` → `operator_name`** (a new
  declared type). `srmech.mcp._coercion` gains real coercers
  (`_resolve_spectral_handle`, `_resolve_spectral_handle_or_bytes`,
  `_resolve_operator_name`); `serialise_native` gains one `SpectralHandle`
  branch (register + emit envelope) ahead of its dict/tuple fall-through.
  `_TYPE_LEXICON` / `_ENCODING_HINT` teach the LLM the `$srmech_handle`
  envelope (handle params) and the dotted operator-name string. The
  `callable` coercer key is RETAINED (other tools / the DSL / direct callers
  still pass a live callable; the exhaustiveness ratchet needs the key).
  `chiral_dual`'s Python signature is unchanged — resolution is at the
  coercion layer, so the DSL + direct callers are unaffected.
- **The rc15 catalog-EXCLUSION ratchets are INVERTED to catalog-INCLUSION**
  in BOTH `tests/test_mcp.py` (`test_handle_pending_absent_from_advertised_catalogs`)
  AND `tests/test_llm_anthropic.py`
  (`test_handle_pending_tools_excluded_from_anthropic_catalog` +
  `test_tool_catalog_includes_every_advertised_tool`'s `expected + 7` → `+ 0`):
  zero handle-pending tools remain; all 7 spectral names are PRESENT in both
  advertised surfaces. The every-tool invocation smoke
  (`_synth_value_for_type`) now synths `operator_name` →
  `srmech.amsc.cascade.chiral_flip` (a genuine unary seq→seq op) and
  `SpectralHandle` → a freshly-minted registered `$srmech_handle` envelope,
  so the smoke exercises a REAL round-trip rather than a tolerated domain
  failure.

### Unchanged

- **C source + ABI.** No file under `c/` other than the header's VERSION
  strings is touched; `SRMECH_ABI_VERSION` stays **3** and the Python shim's
  `EXPECTED_ABI_VERSION` stays **3**. The JPL Power-of-Ten ratchet is
  unaffected. The whole voxel is a Python tool-schema / registry / MCP-surface
  change. TestPyPI rc verification before any production PyPI tag.

## [0.5.0rc15] - 2026-05-29

**rc15 of N for v0.5.0 — the "every-tool invocation smoke + honest
`mcp_callable` marking" voxel (upstream §10.1).** rc14 made every declared
param TYPE JSON-coercible and shipped the static `has_coercer` ratchet —
but `has_coercer` could not tell a REAL coercer from the `_identity`
pass-through. The 7 `srmech.spectral.*` tools whose surface is a bare
`SpectralHandle` / `SpectralHandle | bytes` went **statically-green yet
were not actually invocable** across the JSON boundary (an opaque
in-process dataclass handle cannot ride JSON by value). rc15 closes that
gap empirically and marks those 7 honestly. Pure-Python only — no C
change, ABI stays 3.

Framework reading: the package declaring its own callable shape (which
tools are advertisable vs. handle-pending) IS **Class H
(self-introspection)** at package scale — the apparatus thesis. No new
primitive class is introduced.

### Added

- **THE EVERY-TOOL INVOCATION SMOKE (§10.1) —
  `test_every_advertised_tool_invocable` in `tests/test_mcp.py`.** For
  EVERY `mcp_callable=True` `ToolEntry`, it synthesises a minimal valid
  args dict from the tool's schema (using the rc14 coercion encodings per
  declared type — `int`→1, `float`→1.0, `bytes`→base64(b"abcd"),
  `np.ndarray`→2×2 identity, `complex`→`[1.0, 0.0]`, containers→minimal
  valid shapes), then actually CALLS the tool via `invoke_tool`. It
  asserts NO binding error (`TypeError` unexpected/missing kwarg) and NO
  coercion error; it TOLERATES domain errors (`ValueError` / non-square
  matrix / length mismatch / op-internal `TypeError`) — those prove the
  tool was reached with bindable + coercible args (callability, not domain
  validity). Result: **151/151 advertised tools invocable**. This is the
  EMPIRICAL complement to rc14's static `has_coercer` ratchet — it closes
  the `has_coercer`-vs-actually-callable gap that left the SpectralHandle
  `_identity` pass-through green.
- **`ToolEntry.mcp_callable: bool` (default `True`, back-compat) +
  `ToolEntry.mcp_unavailable_reason: str | None`.** The 7 handle-pending
  `srmech.spectral.*` tools (`decompose` / `delta` / `recompose` /
  `similarity` / `predict` / `prediction_error` / `truncate_sparse`) are
  marked `mcp_callable=False` with the reason "handle-pending:
  by-reference SpectralHandle id arrives in the bus handle-grammar (rc16);
  use the srmech package directly until then." `to_jsonable()` emits both
  new fields.
- **`test_handle_pending_absent_from_advertised_catalogs` +
  `test_handle_pending_tools_excluded_from_anthropic_catalog`.** Assert
  the 7 handle-pending tools are absent from BOTH advertised catalogs (MCP
  `tools/list` + Anthropic `_build_tool_catalog`) while remaining in the
  registry for introspection.

### Changed

- **Advertised-surface exclusion of `mcp_callable=False` entries at BOTH
  seams.** `srmech.mcp._tools.tool_entries_to_mcp_defs` (the MCP
  `tools/list` source) and `AnthropicAgent._build_tool_catalog` (the
  Anthropic seam) now skip `mcp_callable=False` entries, so an LLM is
  never offered a tool it cannot call. The advertised surface drops from
  158 → **151**; the registry (`get_tool_schema().tools`) keeps all 158
  for introspection.
- **`srmech.introspect.describe()` reports the split.** The `tools` block
  now carries `mcp_callable` + `handle_pending` counts alongside `total` +
  `by_category`, and a top-level `handle_pending` lists the 7 names. The
  `describe` ToolEntry's documented return-shape is updated to match.
- **Schema-accuracy fix surfaced by the smoke:**
  `srmech.amsc.laplacian.dense_laplacian` + `normalized_laplacian` now
  declare `edges` as `list[tuple[int, int]]` (matching the shipped
  `(n, edges: Iterable[Tuple[int, int]])` signature + the sibling
  `dense_adjacency` entry); the earlier bare `list` type advertised an
  edge-list shape too loose for an LLM to populate. Signature unchanged.

### Deferred

- **SpectralHandle by-reference invocation → rc16** (per user decision).
  The bus handle-grammar (a `SpectralHandle` id arriving by reference)
  lets the 7 spectral tools become `mcp_callable=True` then; until then the
  `srmech` package (`import srmech.spectral`) is the path for spectral
  work.

## [0.5.0rc14] - 2026-05-29

**rc14 of N for v0.5.0 — the "full JSON↔native MCP coercion" voxel.** A
live probe of the rc13 catalog proved **65 of 158 tools (41%) were
advertised to MCP / Anthropic but UNCALLABLE** — their parameters are
`bytes` / `np.ndarray` / `complex`, types JSON-RPC cannot express. rc14
makes **all 158 tools MCP-callable** via full **bidirectional** coercion:
a tool that accepts JSON but returns an un-serialisable ndarray is equally
unusable, so the fix covers params-in AND results-out. Pure-Python only —
no C change, ABI stays 3.

Framework reading: bidirectional coercion is **Class H
(self-introspection)** at the package's tool-surface — the package making
its own A–N callables' types JSON-expressible across the JSON-RPC /
Anthropic boundary. The base64 / `[re, im]` encodings are **Class B
(TLV-framing)** — encoding-boundary translation between continuous native
types and the discrete JSON wire. No new primitive class is introduced.

### Added

- **Bidirectional JSON↔native coercion (`srmech.mcp._coercion`).** A clean
  type→coercer dispatch keyed on each `ToolParameter.type` string, plus a
  structural outbound serialiser:
  - `bytes` ↔ base64 `str` (user decision — binary-safe + unambiguous;
    replaces the rc13 hex convention). Malformed base64 raises a clear
    `ValueError` naming the param.
  - `np.ndarray` ↔ nested JSON list (row-major `.tolist()`); complex
    arrays serialise each element as `[re, im]`.
  - `complex` ↔ `[re, im]` (a bare JSON number decodes to `complex(n, 0)`).
  - numpy scalars (`np.int64` / `np.float64` / `np.uint8` / …) → Python
    `int` / `float` / `bool` on the outbound path.
  - container types recurse element-wise: `Sequence[bytes]`,
    `Sequence[np.ndarray]`, `tuple[np.ndarray, ...]`,
    `Mapping[bytes, bytes]` (`template.render`),
    `list[tuple[bytes, int]]` (`dispatch.match` rules),
    `list[tuple[bytes, bytes]]` (`naming.lookup` pairs).
- **Schema encoding hints.** Each non-JSON native type's schema property
  carries a JSON-encoding hint in its `description` (`bytes` → string +
  "base64-encoded bytes"; `np.ndarray` → array + "nested JSON array,
  row-major; complex elements as [re, im]"; `complex` → array +
  "[real, imaginary]"; containers → the element hint), so an MCP /
  Anthropic consumer learns the wire form up front. `complex` now renders
  as a JSON-schema `array` (was `string`). The rc13 property-key grammar +
  rc10 name discipline are untouched (the hint lives in the value's
  description, never the key).
- **THE TYPE-COERCIBILITY RATCHET — `test_all_param_types_json_coercible`
  in `tests/test_mcp.py`.** For EVERY `ToolEntry` param across
  `get_tool_schema().tools`, it asserts the coercion dispatch HAS an
  explicit handler for the declared type. This guarantees no future tool
  can advertise an uncallable param type unnoticed (complements the rc13
  schema/signature name-drift ratchet). Running it over all 158 tools
  surfaced 33 distinct param types, all now handled.

### Changed

- `srmech.mcp._tools._coerce_arguments` now routes every inbound argument
  through `_coercion.coerce_param` (was a small inline hex/path matcher).
- `srmech.mcp._tools.serialise_result` now walks the result through
  `_coercion.serialise_native` before `json.dumps`, so bytes → base64,
  ndarray → nested list (complex as `[re, im]`), complex → `[re, im]`,
  numpy scalars → Python scalars, tuples/sets → lists — round-trippable
  with the inbound path.

### Tests

- `test_coercion_roundtrips_scalar_leaf_types` — `coerce_param(serialise_
  native(x)) == x` for bytes / complex / real-ndarray (exact); complex
  arrays via the explicit `complex_pairs_to_ndarray` builder.
- `test_serialise_native_emits_json_serialisable` — `json.dumps`
  succeeds for bytes / complex / real+complex ndarray / numpy scalars /
  nested tuples / dict-with-bytes-key.
- `test_invoke_*` live-path round-trips through `invoke_tool` (the shared
  MCP + Anthropic entry): `naming.lookup` (base64 key + pairs),
  `template.render` (base64 mapping), `hdc.bind` (base64 ↔ bytes
  round-trip), `laplacian.jacobi_eigvals` (nested-list matrix → eigenvalue
  list), `qm.sm.higgs_potential` (phi=`[re, im]`), `dispatch.match` (base64
  rules) — each asserts the result is JSON-serialisable.
- `test_invoke_klein4_random_seed_reproducible_rc14_path` — rc13 seed
  reproducibility holds through the rc14 ndarray-result coercion.
- `test_schema_renders_encoding_hints` +
  `test_encoding_hints_preserve_property_key_grammar` — STEP 3 schema-hint
  coverage; property-key grammar still clean.
- The two rc13 hex-based tests (`*_sha256_bytes_*`, `serialise_result_
  handles_bytes_*`) are updated to base64 (the rc14 wire form).
- Version-gate test renamed `test_version_is_0_5_0rc13` →
  `test_version_is_0_5_0rc14`; `test_version_module_matches` stays
  literal-free.

> **NOTE — arrays over JSON are payload-heavy.** Arrays are now
> MCP-callable, but a large ndarray serialised as a nested JSON list is
> expensive over the JSON-RPC wire. The bus **handle-API** (a later voxel)
> remains the by-reference path for bulk array work — per the
> package-for-bulk / MCP-for-interactive design boundary. Use MCP coercion
> for interactive / small-payload calls; use the bus handle for bulk
> spectral arrays.

## [0.5.0rc13] - 2026-05-29

**rc13 of N for v0.5.0 — MCP surface-correctness bug-fix voxel.** Two
real bugs surfaced by upstream MCP usage, plus the would-have-caught-it
ratchet. Both bugs affected BOTH the MCP path and the Anthropic adapter
(shared `srmech.mcp._tools.invoke_tool` dispatch). Pure-Python only — no
C change, ABI stays 3.

Framework reading: the fixes are **Class H (self-introspection)** at the
package's tool-surface — the schema recognising its own callables' shape.
The integer `seed` is **Class N (rational / deterministic anchor)** made
JSON-expressible so the bit-exact / attestation discipline survives the
JSON-RPC / Anthropic boundary. No new primitive class is introduced.

### Fixed

- **`hdc.klein4_random` / `hdc.polar_random` are now seedable over
  JSON-RPC (BUG A — found via upstream MCP usage).** They were seedable
  only via `rng: numpy.random.Generator`, which cannot cross JSON-RPC nor
  be expressed in an Anthropic tool schema — so MCP / Anthropic callers
  could not obtain a DETERMINISTIC Klein-4 / polar vector, breaking
  srmech's bit-exact / attestation discipline. Both ops gain an integer
  `seed: int | None = None` param: when given (and `rng` is not), the
  generator is built internally as `np.random.default_rng(seed)`. The
  in-process `rng=` path is preserved for back-compat; **precedence** —
  an explicit `rng` wins over `seed` if both are supplied. Each op's
  `ToolEntry` now advertises the JSON-friendly `seed: int` and DROPS the
  un-serialisable `rng` Generator (a Generator has no valid JSON-Schema
  type and should never have been in the MCP-facing schema). Acceptance:
  `klein4_random(seed=42)` is bit-identical twice directly AND twice
  through `invoke_tool`.
- **`srmech.amsc.naming.lookup` is callable again via MCP / Anthropic
  (BUG B — found via upstream MCP usage).** Its `ToolEntry` declared a
  param `entries` that the shipped `lookup(key, pairs)` does not accept,
  so every MCP / Anthropic invocation raised
  `TypeError: lookup() got an unexpected keyword argument 'entries'` —
  the tool was uncallable. Fixed the SCHEMA to match the shipped
  signature (`entries` → `pairs`), least-surprise (the function is the
  SSoT).
- **`srmech.amsc.template.render` schema/signature drift (surfaced by
  the new ratchet).** Its `ToolEntry` declared `substitutions` while the
  shipped `render(template_bytes, mapping)` accepts `mapping` — same
  uncallable-tool failure mode as BUG B. Aligned the schema
  (`substitutions` → `mapping`).

### Added

- **THE RATCHET — schema/signature alignment test
  (`test_schema_signature_alignment_no_drift` in `tests/test_mcp.py`).**
  For EVERY `ToolEntry` in `get_tool_schema().tools`, it resolves the
  dotted callable and asserts each declared parameter is BINDABLE to the
  callable's signature (tolerating `**kwargs` and the rc10 `*args`
  clean-name convention). This catches the whole class of bug behind
  BUG B before it ships. Running it surfaced exactly two drifts across
  all 158 tools — `naming.lookup` (`entries`) and `template.render`
  (`substitutions`) — both now fixed; the ratchet passes clean.

### Tests

- `test_klein4_random_seed_reproducible` + `test_polar_random_seed_
  reproducible` — same `seed` ⇒ bit-identical vectors directly and via
  `invoke_tool`; a different seed differs (seed is load-bearing).
- `test_random_ops_rng_takes_precedence_over_seed` — `rng` wins over
  `seed`; the legacy `rng=` path stays back-compat.
- `test_random_ops_schema_drops_unserialisable_rng` — the `*_random`
  ToolEntries advertise `seed` and NOT `rng`.
- `test_naming_lookup_callable_via_invoke_tool` +
  `test_template_render_callable_via_invoke_tool` — both return a real
  result through `invoke_tool` (no TypeError).
- De-brittled version-gate test carries forward — `test_version_is_0_5_
  0rc13` (renamed) is the single deliberate human-literal gate;
  `test_version_module_matches` stays literal-free.

## [0.5.0rc12] - 2026-05-29

**rc12 of N for v0.5.0 — the "DSL surface" voxel.** Exposes the rc8
cascade-composition DSL (`srmech.dsl.*`) as declarative MCP / Anthropic
`ToolEntry`s, so an LLM composes AND runs a cascade in a single tool
call. The fluent `chain().then(...).loop(...)` builder is not
tool-callable (a tool call can't chain methods); the declarative surface
does real work in ONE call. Pure-Python only — no C change, ABI stays 3.

Framework reading: the DSL composes **Class M (cross-class bind)** over
the cascade catalog — each chain stage is one A–N primitive-class
instance, the chain is the composition. `list_catalog_ops` is **Class E
(catalog enumeration) ∘ Class F (descriptor render)**. No new primitive
class is introduced; this voxel makes the rc8 composer callable in one
shot from an LLM tool surface.

### Added

- **`srmech.dsl.run_toml_chain(spec, input_value)` — compose + run a
  cascade in ONE call.** Author an inline TOML chain spec (a `[chain]`
  table + `[[stage]]` array; each stage carries one discriminator —
  `op` / `loop_n`+`sub_chain` / `fold_init`+`fold_op` / `reduce_op`),
  feed an input value, get the chain result. The declarative, one-shot
  face of the rc8 DSL. Registered as a `ToolEntry` (owner `srmech`,
  category `dsl`) with plain keyword params (`spec` / `input_value`), so
  the rc10 property-key grammar holds and `invoke_tool`'s `fn(**coerced)`
  calls it directly (no VAR_POSITIONAL unpack).
- **`srmech.dsl.list_catalog_ops()` — enumerate the cascade-catalog
  ops.** Returns one record per op (`{name, class, purpose}`) sourced
  from the on-disk cascade-catalog TOML descriptors (the SSoT), so an
  LLM can pick valid `op` / `fold_op` / `reduce_op` names + read each
  op's A–N class before authoring a spec. 8 ops: `best_rational_signed`,
  `chiral_dual`, `chiral_flip`, `cyclic_gcd`, `magnitude`,
  `net_chirality`, `pin_slot_at_zero`, `reorient`. Registered as a
  no-param `ToolEntry`.
- **`srmech.dsl.build_chain_from_toml_str(spec)` — the string
  counterpart of `build_chain_from_toml`.** Builds a `Chain` from an
  in-memory TOML chain-spec string (rather than a path), so a chain can
  be authored inline and materialised without writing a file first. The
  load-bearing primitive `run_toml_chain` is built on.

### Changed

- **`srmech.amsc.tool_schema.warmup_all()` now imports `srmech.dsl`.**
  Appended to the warmup import list so the dsl `ToolEntry`s register no
  matter the entry-path and the manifest stays complete. The
  registration itself fires from `_register_dsl_tools()` at
  `tool_schema` import (declarative data only — it does NOT import
  `srmech.dsl`, so there is no import cycle; the dotted-name targets are
  resolved by `srmech.mcp._tools` at invoke time). The `warmup_all()`
  import is independently verified cycle-free: neither `srmech.dsl` nor
  `srmech.introspect` imports `srmech.amsc.tool_schema` at module load.
- **De-brittled version-gate test** carries forward — `test_version_is_0
  _5_0rc12` (renamed) is the single deliberate human-literal gate;
  `test_version_module_matches` stays literal-free (sources-agree +
  PEP 440 shape only).

### Tests

- Test determinism: pinned `time_ns` on all bio-totp round-trip tests so
  they no longer depend on wall-clock window alignment (eliminates a
  CI-load timing flake; no production change).

## [0.5.0rc11] - 2026-05-29

**rc11 of N for v0.5.0 — the "Self-recognition root" voxel.** The
keystone of the v0.5.0 substrate-self-recognition arc: the package
gains a single canonical surface to populate AND recognise its own
tool-schema shape. Pure-Python only — no C change, ABI stays 3.

Framework reading: `describe()` IS **Class H (self-introspection)** at
package scale — the package recognising and rendering the SHAPE of its
own A–N tool surface. `warmup_all()` is the Class A (content-addressed
callable identifier) ∘ Class E (catalog) population step that
GUARANTEES the Class H view is complete regardless of entry-path.

### Added

- **`srmech.amsc.tool_schema.warmup_all()` — THE single registration
  entry-point.** Imports every submodule that registers `ToolEntry`s
  (`srmech.bus` / `srmech.introspect`) so the registry is fully
  populated no matter how srmech was entered (library / CLI / MCP /
  Anthropic adapter). Idempotent. Fires from `srmech.__init__` (per
  user direction 2026-05-29 — substrate-coherent: every consumer sees
  the complete tool-schema from t=0). **Permanently closes the
  orphan-registration bug class** — the rc9 miss where `srmech.bus`
  tools were silently absent from the LLM-facing catalog because no
  entry-path imported the bus. THE single place future voxels add their
  registration import. Re-exported as `srmech.warmup_all`.
- **`srmech.introspect.describe()` — the self-recognition ROOT
  surface.** The "what is srmech?" root: a structured, at-a-glance map
  of the package's own shape — package version, tool-schema version,
  native-dispatch status (`has_native` / `abi_version` /
  `native_version`), total registered tool count + per-category
  breakdown, and the sorted list of category names. Calls
  `warmup_all()` first so the counts are complete. Registered as a
  `ToolEntry` (`srmech.introspect.describe`, no params) so MCP /
  Anthropic consumers can ask "what is srmech / what can it do?". A
  ROOT / INDEX — it surfaces the SHAPE; per-tool JSON schemas, env, and
  error-type detail come from later voxels (rc15 / rc16).

### Changed

- **`srmech.mcp._tools` now warms up via the canonical entry-point.**
  The rc9 scattered side-effect imports (`from .. import bus` /
  `introspect`) are replaced by a single `warmup_all()` call. Behaviour
  is identical (registry fully populated before `get_tool_schema()`),
  but the warmup list is now maintained in ONE place.
- **De-brittled the version-gate test** (`tests/test_signal_processing
  _scaffolding.py`). `test_version_is_0_5_0rcN` (renamed to `…rc11`) is
  now the SINGLE deliberate human-literal gate — the conscious per-rc
  bump point. `test_version_module_matches` no longer hardcodes a
  literal; it only asserts the SSoT sources AGREE plus a PEP 440 sanity
  shape, so it survives version bumps (this gate bit us 3× in rc10).

## [0.5.0rc10] - 2026-05-29

**rc10 of N for v0.5.0 — two shared-dispatch bug-fixes found by a LIVE
Anthropic API test of the rc9 adapter (the mocks could not catch them).**

Both bugs lived in the **shared** tool-schema / dispatch surface that
**both** the MCP adapter (rc6, `srmech-mcp`) and the Anthropic SDK
adapter (rc9, `srmech-agent`) route through, so each affected both
transports at once. Pure-Python only — no C change, ABI stays 3.

### Fixed (load-bearing, both adapters)

- **Illegal tool-schema property key blocked the ENTIRE Anthropic
  catalog (live 400).** `srmech.amsc.hdc.polar_bundle` and
  `srmech.amsc.hdc.klein4_bundle` were registered with the param name
  `*vectors` — the Python varargs sigil leaked into the `ToolParameter`
  NAME, so the generated `input_schema.properties` carried a key
  `*vectors`. Anthropic rejects it with `400 — input_schema.properties:
  Property keys should match pattern '^[a-zA-Z0-9_.-]{1,64}$'`, which
  fails the whole `messages.create` call (every tool, not just the two
  bundles). The unit-test mocks never sent the catalog to a real
  validator, so they passed; only a live API call surfaced it. Fix:
  rename the param `*vectors` → `vectors` in both registrations, typed
  `Sequence[np.ndarray]` to match the sibling `srmech.amsc.hdc.bundle`
  convention (variadic — "one or more vectors of equal length").
- **Varargs dispatch (`fn(**coerced)` cannot call a `*args` function).**
  `srmech.mcp._tools.invoke_tool` ended with `return fn(**coerced)`
  (keyword-args only). For a variadic callable like
  `polar_bundle(*vectors)`, `fn(vectors=[...])` raises `TypeError:
  polar_bundle() got an unexpected keyword argument 'vectors'`. Both
  adapters call this `invoke_tool`, so invoking either bundle tool was
  broken on BOTH paths even after the property-key rename. Fix: detect a
  `VAR_POSITIONAL` parameter via `inspect.signature(fn)` and unpack the
  supplied sequence positionally (`fn(*seq, **coerced)`); the historical
  sigil-prefixed key (`*vectors`) is still tolerated so no in-flight
  caller breaks.

### Added — defence-in-depth + regression ratchets

- **Property-key sanitiser in the MCP/Anthropic converter.**
  `tool_entry_to_mcp_def` now strips any leaked Python sigil (leading
  `*` / `**`) and clamps every `inputSchema.properties` key to
  `^[a-zA-Z0-9_.-]{1,64}$` (the `required` list is sanitised in lockstep
  so it still references real properties). The rename above is the SSoT
  fix; this guards BOTH adapters against a future sloppy varargs/kwargs
  registration (mirrors the rc9 belt-and-braces lesson).
- **Two would-have-caught-it test ratchets** in `tests/test_mcp.py`:
  (a) for every registered tool, assert every
  `tool_entry_to_mcp_def(entry)["inputSchema"]["properties"]` key
  matches the Anthropic grammar and contains no `*` (caught BUG 1 — it
  FAILS on the pre-fix `tool_schema`, PASSES after the rename; guards
  all 155 tools on both transports forever); (b) invoke
  `srmech.amsc.hdc.polar_bundle` AND `srmech.amsc.hdc.klein4_bundle`
  through `invoke_tool` with a small valid list of vectors and assert a
  real bundled result (not a `TypeError` / `MCPToolError`) (caught BUG
  2).

For Claude Code users on the rc6 MCP path, this rc fixes the two bundle
tools (they were uncallable / catalog-blocking there too); no other
behaviour changes.

## [0.5.0rc9] - 2026-05-28

**rc9 of N for v0.5.0 — Anthropic SDK secondary adapter (optional) +
POSIX bus-discovery fix.**

### Fixed (load-bearing, since v0.5.0rc1)

- **POSIX bus discovery silently returned empty.** `_iter_candidate_files`
  filtered the `~/.srmech/` directory with `Path.is_file()`, which returns
  `False` for AF_UNIX socket files (they're `S_IFSOCK`, not `S_IFREG`).
  Effect: `by_name()` / `list_endpoints()` reported no live endpoints on
  POSIX even though the socket existed and was connectable, so every test
  using the `_wait_for_endpoint` helper hit a 5 s timeout on every POSIX
  CI cell across the rc1–rc9 series (40+ failing tests per cell, masked
  by the prior 3 POSIX cells going red the whole time). Windows passed
  throughout because its `.txt` registry file IS a regular file. Fix:
  invert the filter (skip directories; accept regular files + sockets).
  New regression test `test_discovery_iterates_uds_socket_files`.
- **`Endpoint.stop()` left accepted-client sockets open.** The listen
  socket was closed but each per-connection worker held its own accepted
  socket — workers would keep serving requests that arrived AFTER
  `stop()` returned, defeating the "stopped server cannot reply"
  contract verified by `test_send_after_server_stop_raises`. Surfaced
  on POSIX once the discovery bug above was fixed (was previously
  masked by the pre-`_wait_for_endpoint` timeout). Fix: track each
  accepted `Connection` on a per-endpoint list and close them all in
  `stop()` before joining worker threads.

### Added — Anthropic SDK adapter

Optional companion to rc6 MCP (primary path for Claude Code users). This
adapter targets users who script Claude API directly outside Claude Code
(FastAPI servers, Jupyter notebooks, CI pipelines using the `anthropic`
Python SDK).

- Added: `srmech.llm.anthropic_agent.AnthropicAgent` — builds the tool
  catalog from `srmech.amsc.tool_schema` ToolEntries, hands to Anthropic
  SDK, runs the tool_use message-loop, returns final assistant message
  with per-tool-call MPR attestation transcript.
- Added: `srmech-agent` console-script entry. `pip install srmech[anthropic]`
  installs the optional dep + the `srmech-agent` command.
- Optional dep: `anthropic>=0.40.0`. Default install does NOT add it
  (zero impact on users who don't need it).
- The Anthropic tool-name grammar (`^[a-zA-Z0-9_-]{1,64}$`) doesn't admit
  the dots in srmech dotted names; the adapter swaps `.` ↔ `_` round-trip
  and keeps a per-instance reverse map so any future tool with an
  underscore in its name still round-trips unambiguously.
- Re-uses `srmech.mcp._server.build_attestation` so the MPR envelope
  per tool call is byte-identical to what the MCP adapter emits for the
  same (tool, result) pair — same response_sha256 across transports.

For Claude Code users, this rc adds nothing — rc6 `srmech-mcp` is still
the right path. This rc exists for the user community: anyone scripting
Claude API outside Claude Code can now use srmech as a tool source with
the same MPR attestation discipline.

Pure-Python; ABI unchanged at 3. ~20 new tests using mocked
Anthropic client (no real API calls).

**This completes the v0.5.0 rc walk** (rc1-rc9 all shipped). Awaiting
user load-test signal before cutting clean v0.5.0 → production PyPI.

### Fixed — MCP tool-schema discoverability gap

- **MCP tool-schema discoverability fix**: `srmech.introspect.list`,
  `srmech.introspect.by_pid`, `srmech.bus.list_endpoints`, `srmech.bus.by_name`,
  and `srmech.bus.decode_splice` are now visible to MCP / Claude Code consumers.
  Root cause: `srmech.mcp._tools` only imported `srmech.amsc.tool_schema` and
  never triggered the side-effect imports of `srmech.bus._tool_schema` or
  `srmech.introspect`, so the "status" introspection surface and the bus
  discovery surfaces were silently missing from the LLM-facing catalog. Fix
  adds explicit `from .. import bus as _bus` / `from .. import introspect as
  _introspect` warmup at the top of `mcp/_tools.py` plus two new ToolEntry
  registrations on each module (introspect: `list`, `by_pid`; bus:
  `list_endpoints`, `by_name`). Total registered tool count goes from 150 to
  155 (decode_splice was registered all along — it just wasn't visible
  through the MCP wrapper because the side-effect import was missing).
  Six new regression tests in `tests/test_mcp.py` lock the fix in by
  asserting each tool appears in `get_tool_schema()` after importing
  `srmech.mcp._tools` (the exact path Claude Code / MCP clients take).

## [0.5.0rc8] - 2026-05-28

**rc8 of N for v0.5.0 — Cascade DSL runner (task #235).**

Fluent `chain()` API + TOML-driven runner + loop/fold/reduce control flow.

- Added: `srmech.dsl` module — `chain(name).then(op).loop(n, sub).fold(init,
  op).reduce(op).run(input)` fluent composition over the 8 cascade-catalog
  ops shipped in v0.4.5.
- Added: TOML cascade-catalog runtime loader — reads the 8 descriptors
  from `srmech/amsc/_research/cascade_catalog/` and resolves op names to
  Python entry points (which route to C peers when `HAS_NATIVE`).
- Added: `srmech dsl run / ops / visualize` CLI subcommands. The `run`
  subcommand loads a TOML chain spec (`[chain]` + `[[stage]]` array
  with `op` / `loop_n`+`sub_chain` / `fold_init`+`fold_op` / `reduce_op`
  discriminators), executes against `--input` (inline JSON) or
  `--input-file` (JSON / NDJSON), emits to stdout or `--output-file`.
- DSL stages emit `dsl.<chain_name>.stage.<N>` events (and a closing
  `dsl.<chain_name>.complete` event) when introspection publish is
  active; observable via `srmech status` or `srmech bus tap`.
- Each builder method (`then` / `loop` / `fold` / `reduce`) validates
  the op name against the on-disk catalog at chain-construction time
  (unknown ops raise `ValueError` immediately, not at `run()` time).
- No new primitive class — loop / fold / reduce are compositions of
  the existing 14-class A–N vocabulary (loop = Class I cyclic
  repetition; fold / reduce = Class M accumulator bind).

Completes ADR-0002 Phase 2-v2 (loop/fold/reduce in chain DSL; task #235).

Pure-Python; ABI unchanged at 3. ~30 new tests; full suite ~1644 passing.

Remaining: optional rc9 Anthropic SDK adapter (defer if you don't need
non-Claude-Code LLM integration).

## [0.5.0rc7] - 2026-05-28

**rc7 of N for v0.5.0 — UTLP Bio-TOTP cipher alignment + tool-schema opt-in
discoverability.**

Two related fixes per user direction 2026-05-28:

1. **UTLP Bio-TOTP cipher alignment** (Claim 255). rc3 shipped a SHA-256
   chained-cipher that was structurally related but DIFFERENT from the
   actual UTLP Bio-TOTP pattern in `examples/utlp/utlp_hal_security.h`.
   rc7 replaces rc3's `_chain.py` with `_bio_totp.py` implementing the
   real UTLP construction: key derivation rolls with a 250 ms time bucket
   (`Key = SHA256(DNA || QuantizedTime)[0:16]`); receiver tolerates ±1
   window for clock skew; nonce constructed from sender_id + channel_id +
   packet_seq ("Exon fields"); same code path for unencrypted (ZERO_DNA)
   and encrypted channels (herd-immunity); kwarg renamed `seed` → `dna`
   for naming alignment (`seed` still accepted with DeprecationWarning).
   Default cipher uses stdlib HMAC-SHA-256 keystream (zero new deps);
   `pip install srmech[crypto]` opts into UTLP-exact AES-128-CTR via
   the `cryptography` library.

2. **Tool-schema opt-in discoverability**: every emitting op's ToolEntry
   now mentions inline: "Events emitted only when wrapped in
   `srmech.introspect.publish()` or `SRMECH_PUBLISH_STATUS=1` env-var
   set; otherwise silent." Plus new top-level
   `srmech.introspect.publish` ToolEntry documenting the opt-in.
   Discoverable via the MCP adapter (rc6) — LLMs in Claude Code see the
   opt-in path inline when reading the tool catalog.

OUT OF SCOPE per user direction: UTLP's mesh / multi-arbor / Loom /
Genesis-election / time-sync layer is embedded-specific and is NOT
brought over to srmech.bus. srmech.bus is local-IPC only.

Pure-Python; ABI unchanged at 3. ~30 new tests; full suite ~1614 passing.

Remaining v0.5.0 rcs: rc8 DSL runner (task #235), optional rc9 Anthropic
SDK secondary adapter.

## [0.5.0rc6] - 2026-05-28

**rc6 of N for v0.5.0 — MCP server adapter (Claude Code integration).**

**LOAD-BEARING for the LLM tool-schema endpoint goal** per user direction
2026-05-28. User is on Claude Code Max plan (no Anthropic API/SDK tier);
MCP (Model Context Protocol) is the primary LLM integration path.

- Added: `srmech.mcp` module — MCP server exposing `srmech.amsc.tool_schema`
  ToolEntries (~150) as MCP tools. JSON-RPC 2.0 over stdio (subprocess mode)
  or HTTP+SSE (cross-process mode).
- Added: `srmech-mcp` console-script entry. `pip install srmech` now
  installs both `srmech` and `srmech-mcp` on PATH.
- Three Claude Code usage modes supported by SAME adapter:
  1. Pure local stdio subprocess (Claude Code default)
  2. Cross-terminal observability (long-running sweep + LLM in another
     terminal connects via `srmech-mcp --bus-endpoint sweep-NAME`)
  3. Subagent-orchestrated research (subagent runs srmech-mcp; reports
     back via Claude Code subagent return)
- Each MCP tool-call response carries MPR attestation (response_sha256 +
  parser_version + tool_name + timestamp).
- Inherits rc3 state-chained wire format when proxying via bus
  (`--bus-endpoint` mode): LLM connections are forward-secure by
  construction.

Pure-Python; ABI unchanged at 3. ~31 new tests; full suite ~1584 passing.

Composes with: rc4 CLI (`srmech bus tap NAME` can be used to observe
what tools the LLM is calling); rc5 async wrapper (`srmech-mcp` HTTP+SSE
uses async).

Remaining v0.5.0 rcs: rc7 DSL runner (task #235), rc8 optional Anthropic
SDK secondary adapter.

## [0.5.0rc5] - 2026-05-28

**rc5 of N for v0.5.0 — async wrapper for the bus.**

Thin asyncio shim over the sync API via `asyncio.to_thread()`. Covers
FastAPI/aiohttp/asyncio-native callers without doubling C-peer complexity.
Sync API remains the SSOT; async is a courtesy wrapper.

- Added: `srmech.bus.aio` module — `AsyncChannel`, `AsyncEndpoint`,
  `AsyncPipeHandle`, async `connect`, async `serve`, async `list`
  (alias for `list_endpoints`), async `list_endpoints`, async `pipe`.
- Handler can be sync OR async; async handlers awaited via
  `asyncio.run_coroutine_threadsafe` from the sync server's worker thread
  (handler runs back on the caller's event loop, not in the worker thread).
- `aio.connect` / `aio.serve` are async context managers (`async with ...`).
- `subscribe()` returns an async generator (per-`__anext__` worker hop).
- All encryption/seed/discovery semantics inherited unchanged from sync API.

Pure-Python; ABI unchanged at 3. No native asyncio plumbing in v1 (real
asyncio-native path via `asyncio.open_unix_connection` can come in v0.5.x
if a workload demands).

~25 new tests using `asyncio.run(...)` inside sync test functions (no
`pytest-asyncio` dep added — keeps the test surface light).

## [0.5.0rc4] - 2026-05-28

**rc4 of N for v0.5.0 — `srmech bus` CLI subcommands.**

Adds `list / tap / pipe / send / serve` subcommands to the `srmech`
console-script entry that was introduced in v0.4.6. Operates the
v0.5.0 bus from the shell: enumerate endpoints, tail live event
streams, chain endpoints, one-shot send, test-serve.

- Added: `srmech bus list [--json] [--all]` — active endpoints,
  ownership-filtered.
- Added: `srmech bus tap NAME [--seed HEX] [--format json|pretty]
  [--filter TYPE] [--limit N]` — stream events.
- Added: `srmech bus pipe SRC DST [--seed-src HEX] [--seed-dst HEX]
  [--transform PY_EXPR]` — daemon pipe.
- Added: `srmech bus send NAME EVENT_JSON [--seed HEX] [--timeout S]
  [--stdin]` — one-shot request.
- Added: `srmech bus serve NAME [--echo] [--seed HEX] [--seed-mint]
  [--handler-module PYMOD:func]` — test server.

Pure-Python; ABI unchanged at 3.

~30 new tests via subprocess invocation of the entry point.

## [0.5.0rc3] - 2026-05-28

**rc3 of N for v0.5.0 — state-chained wire format ("biological TOTP-like").**

Per user direction 2026-05-28: same-user-defensive forward-secrecy for bus
channels. Each frame N's encoding depends on state_{N-1}; receiver must walk
the chain to decrypt. Pure-Python cipher (SHA-256 keystream + HMAC-SHA256
integrity); ABI unchanged at 3 (no new C symbols this rc).

Framework reading: Class A + Class I + Class K composed at the wire layer;
substrate-self-recognition extended to the frame chain.

- Added: `srmech.bus._chain` — `ChainState` (per-direction cipher state),
  `derive_state`, `decode_splice` (pure-function decoder for tool-schema /
  LLM introspection). Cipher: `state_0 = sha256(seed || ":" || channel_id
  || ":" || direction)`; `keystream_N = sha256(state_N || "ks" ||
  counter_be8 || block_be4)`; `ciphertext_N = plaintext XOR keystream`;
  `state_{N+1} = sha256(state_N || "st" || ciphertext_N)`; `mac_N =
  hmac_sha256(state_N || "mac", ciphertext || counter_be8)[:16]`. Domain-
  separation tags (`"ks"` / `"st"` / `"mac"`) defend against
  keystream / state-advance / MAC-key cross-contamination.
- Added: `srmech.bus._tool_schema` — registers `srmech.bus.decode_splice`
  as a `ToolEntry` for LLM consumption (load-bearing for rc5 MCP adapter;
  LLMs can introspect the cipher).
- Added: `srmech.bus._seed` — seed-resolution cascade module
  (`resolve_client_seed` / `resolve_server_seed` / `mint_and_write_seed` /
  `discard_seed_file`). Three sources, in priority order: explicit kwarg
  → `SRMECH_BUS_SEED` env var → `~/.srmech/bus-{name}.seed` 0o600 file.
- Changed: `connect(name, seed=...)` and `serve(name, seed=...,
  handler=...)` accept an optional pre-shared seed. When seed is set (via
  any of the three sources), the wire is encrypted; when None, the wire
  is unencrypted (full rc2 back-compat). The server auto-writes the
  resolved seed to the discovery file so subsequent clients on the same
  machine can find it (suppressible via `_seed.resolve_server_seed(...,
  write_discovery_file=False)`).
- Added: per-direction `ChainState` discipline — each connected `Channel`
  (client) and each accepted worker (server) carries TWO independent
  chain states (send + recv), keyed with direction tags `"out"` / `"in"`
  so the two halves of the duplex never share a keystream. Concurrent
  client connections each get their own chain pair derived at accept
  time — no shared mutable state across simultaneous clients.
- Added: per-frame envelope on the wire body — `[16-byte mac][8-byte
  counter_be][ciphertext]`. Tampered frame raises `MacMismatchError`
  (constant-time `hmac.compare_digest` verification); replayed or
  reordered frame raises `CounterReplayError`. Short body raises
  `ChainFormatError`.
- Added: `Channel.encrypted` / `Endpoint.encrypted` properties — query
  whether a particular bus surface is running the cipher.
- Tests: ~30 new tests under `tests/test_bus.py` covering chain
  encrypt/decrypt round-trip, MAC mismatch detection, counter replay
  rejection, seed-mismatch behaviour at the channel layer, unencrypted
  back-compat preserved, tool-schema `decode_splice` introspection,
  end-to-end via `serve()+connect()` with seed, seed-file priority
  cascade, direction-tag keystream disjointness.

Threat model: defensive against same-user processes that didn't initiate
the channel. NOT designed for active local attackers (would need DH key
establishment + AEAD; deferred to v0.5.x or v0.6.0 if needed). Honest
scope: a co-resident process that can read the discovery file at rest
(no kernel-isolation; 0o600 is only file-perm-level) can decrypt; the
defence is structural ("you weren't part of the chain since state_0").

## [0.5.0rc2] - 2026-05-28

**rc2 of N for v0.5.0 — C peer + real Windows named pipe + envelope fixes.**

Per user direction 2026-05-28 (continuation of the rc1 dispatch): three
changes folded into one rc — the bus C peer for sub-µs native dispatch
(when both ends opt in), real Windows named pipes via Win32 ctypes
(no `pywin32` dependency), and two envelope bugs from the rc1 cross-
process smoke that silently dropped handler-returned keys and
over-restricted client `payload` schema.

- Added: `srmech_bus_*` C symbols — `srmech_bus_serve`,
  `srmech_bus_server_accept_one`, `srmech_bus_server_stop`,
  `srmech_bus_connect`, `srmech_bus_send_recv`,
  `srmech_bus_client_close` — plus the function-pointer typedef
  `srmech_bus_handler_callback_t`. JPL-clean POSIX (AF_UNIX) +
  Windows (CreateNamedPipe via Win32, no pywin32 dep). Workspace
  allocated once per server at `srmech_bus_serve`; reused across
  every accepted connection (no allocation in the hot path; JPL
  Rule 3 honored via cold-path-only allocation allowance). **ABI
  bump 2 → 3** (the new function-pointer typedef carries a wire-
  format implication for the Python ctypes CFUNCTYPE construction).
- Added: Python ctypes binding `srmech.amsc._native.BUS_HANDLER_CALLBACK`
  + bindings for all six new C symbols (hasattr-guarded so a stale
  rc1 lib falls through cleanly to the Python-only path).
- Added: `srmech.bus._transport.NamedPipeTransport` + the
  `_SafeNamedPipeServerTransport` wrapper that auto-falls-back to
  TCP-loopback on `CreateNamedPipeW` failure (rare; for sandboxed
  test environments). Default Windows transport remains TCP-loopback
  for rc2; opt-in to the named-pipe path via
  `SRMECH_BUS_USE_NAMED_PIPE=1`. (The named-pipe accept loop on
  Windows 10 / Python 3.14 exhibited a Connect/accept-ordering
  regression under `multiprocessing.spawn` — the first
  `ConnectNamedPipe` completed without a corresponding client
  `CreateFileW`, leaving the worker reading from a phantom
  connection; the rc2 commit message documents the investigation;
  not yet root-caused. The C peer + Python ctypes infrastructure
  are in place for a later rcN to flip the default once the
  Connect/accept race is understood.)
- Added: discovery registry token now accepts `pipe \\.\pipe\srmech-{name}`
  (rc2 named-pipe servers) in addition to `tcp 127.0.0.1 <port>`
  (rc1 fallback / locked-down environments).
  `_endpoint_alive_named_pipe` probes via `WaitNamedPipeW` (which
  does not consume a pipe instance per Microsoft docs).
- Fixed: handler return-shape now correctly passes the full handler
  dict through as the response Event's `payload` (rc1 was silently
  aliasing `payload` to `handler_result.get("payload")` and dropping
  every other key). A handler returning
  `{"type": "pong", "echo": ..., "server_pid": ...}` now delivers
  all three keys to the client end-to-end. The `type` discriminator
  is also retained inside the payload for client-side inspection.
  Handler contract documented in `_server.py:_normalise_response`.
- Fixed: client `Channel.send()` no longer requires `payload` to be
  a dict. Any JSON-serialisable value is accepted (string, list,
  number, bool, `None`, dict). `json.dumps` raises at the canonical
  serialisation boundary on truly non-serialisable inputs. Matches
  standard JSON conventions; supports e.g. `{"type": "ping",
  "payload": "echo-me"}` and `{"type": "metrics", "payload": [1, 2, 3]}`.
- Fixed: handlers receive `payload` of the original JSON type
  (string / list / number / dict / None), not coerced. Server's
  `_event_to_dict` no longer wraps non-dict payloads as
  `{"value": ...}`.
- Changed: handlers without a `type` key in their return dict now
  default to discriminator `"ok"` (rc1 defaulted to `"_response"`;
  the rc2 default matches the spec's "type=ok default" idiom).
- Changed: handler exceptions yield `{"type": "_error", "reason": ...,
  "traceback": ...}` (rc1 nested these inside `payload` which the
  Bug-1 fix obviated; the rc2 error envelope is flat and the full
  dict still passes through as the response payload per the new
  contract).
- Tests: ~13 new tests covering Bug-1 (handler full-dict pass-through),
  Bug-2 (any-JSON-payload), ABI v3 verification, native C-peer
  symbol presence, BUS_HANDLER_CALLBACK CFUNCTYPE constructibility.
  Total bus test count 49 → 62; full suite 1453 → 1457 passing.
- JPL audit: `srmech_bus.c` opted into `RULE_3_COLD_PATH_FILES`
  (cold-path-only allocation; no malloc in accept loop or per-
  request worker). Seven small bus low-level helpers added to
  `RULE_5_EXEMPT_FUNCTIONS` per the established static-internal-
  trivial-wrapper pattern. Rule 4 / Rule 8 / Rule 1 all clean
  without exemption.

Remaining v0.5.0 rcs: rc3 state-chained wire format (per user
direction 2026-05-28 — TOTP-like rolling cipher with srmech-provided
`decode_splice` via tool-schema; same-user-defensive forward
secrecy), rc4 CLI, rc5 async wrapper, rc6 MCP adapter (Claude Code
integration), rc7 DSL runner, rc8 optional Anthropic SDK adapter.

## [0.5.0rc1] - 2026-05-28

**rc1 of N for v0.5.0 — `srmech.bus` Python skeleton.**

Per user direction 2026-05-28: a cross-process bus over Unix-domain-sockets
(POSIX) and Windows-named-pipes / TCP-loopback fallback (Windows), TLV-framed,
MPR-NDJSON payloads, bidirectional req/rep + pub/sub. End-goal: srmech/siona
processes (and Claude Code via MCP, rc5) compose across process boundaries.

Framework reading: Class M ∘ Class B ∘ Class A extended to the OS-process-class
boundary. Class H introspection (v0.4.6) is the unidirectional read-only special
case of the bus.

- Added: `srmech.bus` module — `serve()`, `connect()`, `list()`, `pipe()`,
  `Endpoint`, `Channel`, `Event`. Sync API. Pure Python (no C peer yet —
  that's rc2; ABI unchanged at 2).
- Transport: POSIX Unix domain sockets at `~/.srmech/bus-{name}.sock`
  (permissions `0o600`) + Windows TCP-loopback fallback with a registry
  file at `~/.srmech/bus-{name}.txt` recording the kernel-assigned port.
  Real named-pipes via ctypes is the rc2 target; the rc1 fallback keeps
  the wire protocol identical so the rc2 swap is transport-only.
- Framing: 4-byte length-prefix TLV; payload is JSON-encoded MPR-shaped
  `Event` (mpr_version + type + payload + attestation + correlation_id).
- Discovery: `~/.srmech/bus-{name}.sock` (POSIX) / `~/.srmech/bus-{name}.txt`
  registry (Windows). Same ownership-filter as introspect — no `top` /
  `ps` / `Get-Process` needed.
- Req/rep: client `send()` issues a fresh UUID correlation-id and blocks
  for the matching reply; server handler returns a dict (response) or
  `None` (fire-and-forget).
- Pub/sub: server `Endpoint.broadcast()` fans out to every connected
  subscriber; client `Channel.subscribe()` yields broadcast events.
  Drop-newest / drop-oldest backpressure policies (server / client).
- Daemon pipe: `pipe(source, sink, transform=...)` composes two endpoints.
- Off by default; importing `srmech.bus` binds nothing.
- ~30-40 new parity tests; full suite passes.

Remaining v0.5.0 rcs queued: rc2 (C peer + ctypes Windows-named-pipe),
rc3 (CLI), rc4 (async wrapper), rc5 (MCP server adapter for Claude Code),
rc6 (DSL runner consuming bus), rc7 (optional Anthropic SDK adapter).

## [0.4.6] - 2026-05-28

**Clean ship — two-arc v0.4.6 closed (PyPI description SO(8) refresh + out-of-band introspection).**

PyPI metadata refresh leads with substrate-native 28-dim chiral hyper-loop = 𝔰𝔬(8) adjoint framing (per user 2026-05-28 *"strip MVP false things"*). NEW public surface: srmech is now installable as a **console-script binary** — `pip install srmech` puts `srmech` on PATH for the first time, with one subcommand `srmech status` providing out-of-band introspection of running srmech sweeps.

**rc1 (TestPyPI verified)**: PyPI `description` field rewritten. 502 chars; both pyproject + pyproject-pure identical. Leads with 28D = 𝔰𝔬(8) adjoint framing.

**rc2 (TestPyPI verified incl. CLI on PATH + live publish/status/auto-cleanup)**:
- Added: `srmech.introspect` module — `publish()` context manager; `list()` enumerates active runs (filters by file ownership; no `top`/`ps`/`Get-Process` needed); `by_pid(N).follow()` streams events; frozen `Run` + `Event` dataclasses (MPR-shaped; attestable).
- Added: `srmech status [--pid N] [-f]` CLI subcommand + `pip install srmech` → `srmech` console-script on PATH (NEW public surface).
- Added: `SRMECH_PUBLISH_STATUS=1` env var auto-activates publish process-wide.
- File backend: `~/.srmech/run-{pid}-{start_time_ns}.ndjson` (start_time_ns defeats PID recycling).
- Off by default; off-path emit check ≈174ns; on-path emit ≈76µs (json+file write+flush).
- Cross-platform Linux/macOS/Windows (POSIX `os.kill(pid, 0)`; Windows ctypes `OpenProcess` — no pywin32 dep). Pyodide degrades cleanly.
- 35 new tests in `test_introspect.py`; full suite 1392 passing.

**Framework reading**: introspection IS Class H (self-introspection) extended across the OS-process boundary; the running process IS the spatial manifold, the introspection API IS its algebraic projection. The "srmech calls itself" extension composes with Spike #219 / MFO §VII.6.11 substrate-self-recognition cascade.

**ABI**: unchanged at 2 (no C changes; pure Python module).

## [0.4.6rc2] - 2026-05-28

**Out-of-band introspection — talk-to-running-PID API.** Per user
direction 2026-05-28: srmech now exposes its internal current state
over a file-based API. Long-running sweeps (30 min to hours) become
observable from a second process without monkey-patching, GDB attach,
or `top` / `ps` polling. Substrate-self-recognition extended across
the OS-process boundary (the framework reading: Class H at PID level).

- Added: `srmech.introspect` module — `publish()` context manager;
  `list()` enumerates active runs (filters by file ownership; no `top`
  needed); `by_pid(N).follow()` streams events; `Run` + `Event` frozen
  dataclasses.
- Added: `srmech status [--pid N] [-f]` CLI subcommand. Also wired
  `python -m srmech status ...` via `srmech/__main__.py` and the
  `[project.scripts]` console-script `srmech = "srmech.cli:main"` in
  both pyprojects.
- Added: `SRMECH_PUBLISH_STATUS=1` env var auto-activates publish.
- File backend: `~/.srmech/run-{pid}-{start_time_ns}.ndjson`
  (start_time_ns defeats PID recycling). MPR-shaped events (re-uses
  srmech.amsc.format envelope — introspection is itself attestable).
- Off by default; zero cost when not used. Emit hooks at cascade-op
  (all 8 ops in `srmech.amsc.cascade`) + AMSC-fetch (`adapters._base.run`)
  + signal-processing (`cascade_dispatcher.dispatch` + RBS-HDC
  encode/decode/similarity boundaries) are no-ops without publish.
- Auto-cleanup: `list()` checks `os.kill(pid, 0)` (POSIX) / Win32
  `OpenProcess` (Windows); removes orphan files; reports dead PIDs as
  "died" with the last event's data preserved in the returned Run.
- ~30 new parity tests (`tests/test_introspect.py`). Tier 1
  (status-file) ships; Tier 2 (mmap ring buffer for >1k events/sec)
  deferred until an op proves it needs it.
- Cross-platform: Linux/macOS/Windows. Pyodide degrades cleanly.

ABI unchanged at 2 (no C changes; pure Python module).

## [0.4.6rc1] - 2026-05-28

**PyPI metadata refresh — leads with SO(8) 28D framing.** Description-only
change; no code, no test, no ABI delta. Reason: the prior v0.4.5 PyPI
description listed the 14-class primitive vocabulary without ever
mentioning that the substrate the vocabulary instantiates is the 28-dim
chiral hyper-loop = 𝔰𝔬(8) adjoint (14 𝔤₂ derivations + 14 L⊕R
octonion-multiplications; Spin(8) triality) — out of step with the
docs/RTD MFO/substrate-native blocks updated in PR #698 + the v0.4.5
cascade-catalog C-parity arc that made the 28D substrate hardware-
callable. Per user 2026-05-28 ("strip MVP false things"), refreshed.

- Changed: `pyproject.toml` + `pyproject-pure.toml` `description` field —
  leads with "substrate-native 28-dim chiral hyper-loop = so(8) adjoint
  (14 g_2 derivations + 14 L+R octonion-multiplications; Spin(8) triality)
  made hardware-callable"; keeps the 14-class vocabulary enumeration for
  PyPI search; mentions cascade-catalog C/Python parity (v0.4.5 arc).
  502 chars, both files identical.
- Version: 0.4.5 → 0.4.6rc1 across 5 SSOTs + version-pin test rename.

rc1 → TestPyPI; clean v0.4.6 follows after verify on the project page.

## [0.4.5] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — ARC CLOSED.**
Clean ship after rc1-rc8 sequence. All 8 cascade catalog ops now have
full C/Python parity (10 C symbol families total) plus declarative TOML
descriptors under `srmech/amsc/_research/cascade_catalog/`. Corrects the
v0.4.3rc6 + v0.4.4rc1 carve-out that shipped cascade ops Python-only.

**Cascade C peers added (one per rc):**
- rc1 `srmech_cascade_chiral_flip_i64` + `_f64` — Class C orientation reversal (sequence in/out; in-place safe).
- rc2 `srmech_cascade_pin_slot_at_zero_f64` — Class K pin-slot (scalar in / orientation+magnitude out via output pointers; NaN→dead-band).
- rc3 `srmech_cascade_magnitude_f64` — Class K magnitude-only (scalar in/out; explicit 3-branch impl preserving NaN→0.0 parity).
- rc4 `srmech_cascade_reorient_i64` + `_f64` — Class C re-application (two-arg shape; type-preserving; INT64_MIN guarded).
- rc5 `srmech_cascade_net_chirality_i8` — Class C net handedness (sequence in / scalar out; empty→+1; first zero short-circuits to 0).
- rc6 `srmech_cascade_cyclic_gcd_u64` — Class I cascade-namespace wrapper (delegates to existing `srmech_gcd` primitive).
- rc7 `srmech_cascade_best_rational_signed_f64` — multi-class K∘N∘C cascade (delegates Class N to `srmech_best_rational`; banker's rounding via llrint() for Python parity).
- rc8 `srmech_cascade_chiral_dual_f64` — HIGHER-ORDER (callback ABI via `srmech_cascade_op_callback_f64_t` typedef; caller-allocated workspace per JPL Rule 3; delegates inner+outer chiral_flip to rc1 native peer).

**Added:**
- 8 TOML cascade-catalog entries under `srmech/amsc/_research/cascade_catalog/` documenting each cascade's class composition, native symbol, attestation, and (where applicable) `[cascade.delegates_to]` / `[cascade.composes]` / `[cascade.higher_order]` / `[cascade.callback_marshaling]` / `[cascade.rounding]` / `[cascade.boundary_cases]` sections.
- New public C typedef `srmech_cascade_op_callback_f64_t` for higher-order callback ABI.
- ~150 new parity tests across all 8 ops (covering int / float / numpy / NaN / Inf / dead-band / banker's-rounding boundary / callback exception propagation / etc).

**Changed:**
- `srmech.amsc.cascade` module docstring: removed "no dedicated C symbol" carve-out clause; added "Full C/Python parity" discipline statement.
- README.md cascade-catalog section: stripped "no dedicated C symbol" carve-out per user directive 2026-05-28 ("strip MVP false things from our presence"); added "Each cascade ships with a dedicated C symbol in libsrmech (full C/Python parity per project discipline)" statement; per-op annotations updated with C-peer rc references.
- All 8 cascade Python entry points now dispatch through native when input shape matches the typed C variant; Python fallback retained for shapes the C ABI doesn't cover (strings, mixed types, out-of-int64 bigints, generators, etc).

**Discipline preserved:**
- ABI unchanged at 2 throughout (all rcs were additive symbols + one additive typedef).
- JPL Power-of-Ten 6/6 audit clean across the entire arc (≥2 asserts per non-exempt function, ≤60-line functions, no malloc inside libsrmech, no goto, bounded loops).
- No `abs()` in cascade Python (sign-handling via canonical Class K pin-slot + Class C re-orientation cascade).
- No new `hashlib.sha256(...)` direct calls (route through `format.sha256_bytes`).
- 1360 test suite all passing.

## [0.4.5rc8] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — chiral_dual**
(rc8 of 8; HIGHER-ORDER callback ABI; **CLOSES THE ARC**). After this
ship all 8 cascade catalog ops have full C/Python parity + TOML
descriptors. The carve-out corrections begun in v0.4.5rc1 are complete.

`chiral_dual` is the ONLY higher-order cascade op in the catalog — it
takes a callable `op` as input and conjugates it with Class C
orientation reversal: `chiral_flip(op(chiral_flip(x)))`. The C peer
uses a function-pointer callback ABI (Option A) rather than a
Class-ID enum dispatch (Option B); Option B would have restricted
`chiral_dual` to known A-N srmech ops, breaking the cascade-catalog
public API contract that `op` can be any callable.

- Added: `srmech_cascade_chiral_dual_f64` C symbol (higher-order;
  callback ABI via `srmech_cascade_op_callback_f64_t` typedef;
  caller-allocated workspace per JPL Rule 3; delegates the Class C
  inner+outer chiral_flip to the rc1 native peer). ABI unchanged at 2.
- Added: `srmech_cascade_op_callback_f64_t` public typedef in
  `srmech.h` (callback signature for higher-order cascade ops).
- Added: `_research/cascade_catalog/chiral_dual.toml` — eighth and
  final TOML cascade-catalog entry with `[cascade.higher_order]` +
  `[cascade.callback_marshaling]` + `[cascade.design_choice]`
  sections documenting the callback ABI + the Option A vs Option B
  design decision.
- Added: `tests/test_cascade_chiral_dual_parity.py` — parity across
  identity / negation / non-trivial / ndarray / empty / singleton /
  random sweep / Python exception propagation / wrong-length-output
  guard / mixed-type fallback / string fallback / non-callable op
  fallback.
- Added: `CASCADE_OP_CALLBACK_F64` ctypes CFUNCTYPE exposed at
  `srmech.amsc._native` module scope (mirrors the C typedef
  `srmech_cascade_op_callback_f64_t`) so the Python dispatch can
  construct callback instances without reaching into the library-
  binding closure.
- Changed: `srmech.amsc.cascade.chiral_dual` dispatches through native
  for homogeneous float64 sequences (list / tuple / 1-D ndarray);
  Python fallback retained for strings, mixed-type sequences, non-
  callable ops, multi-arg ops, etc. Python exceptions raised by the
  op callback propagate correctly through the trampoline (never
  silently swallowed).

Cascade-catalog C-parity + TOML retrofit arc CLOSED at rc8. All 10
cascade C symbol families exported (chiral_flip i64+f64,
pin_slot_at_zero f64, magnitude f64, reorient i64+f64, net_chirality
i8, cyclic_gcd u64, best_rational_signed f64, chiral_dual f64). Ready
for clean v0.4.5 ship to production PyPI.

## [0.4.5rc7] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — best_rational_signed**
(rc7 of N; multi-class K∘N∘C cascade with delegation to existing Class N
primitive). PLUS: README full-feature update strips residual "no
dedicated C symbol" carve-out language per user directive 2026-05-28
(*"strip MVP false things from our presence"*).

best_rational_signed is the SECOND of the delegating cascade ops in
this arc (after cyclic_gcd / rc6). The C peer composes three A–N stages:
Class K pin-slot (sign-strip) inlined + Class N best-rational anchor
delegated to the existing `srmech_best_rational` primitive + Class C
re-orientation (sign re-apply on the numerator) inlined. The multi-
stage delegation pattern generalises rc6's single-class delegation
pattern to the multi-stage case.

Banker's-rounding parity (load-bearing): Python's built-in round() uses
round-half-to-even (banker's rounding); C99 round() uses round-half-
AWAY-from-zero. The C peer uses `llrint()` under the default IEEE-754
FE_TONEAREST mode (= round-half-to-even) for bit-exact parity with
Python's round() at the .5 boundary.

- Added: `srmech_cascade_best_rational_signed_f64` C symbol (JPL-clean;
  multi-stage K∘N∘C cascade; Class K + Class C stages inlined; Class N
  delegated to existing `srmech_best_rational` primitive; banker's
  rounding via `llrint()` for Python parity). ABI unchanged at 2
  (additive symbol).
- Added: `srmech/amsc/_research/cascade_catalog/best_rational_signed.toml`
  — seventh TOML cascade-catalog entry with `[cascade.composes]` /
  `[cascade.delegates_to]` / `[cascade.rounding]` sections documenting
  the multi-stage composition + the IEEE-754 rounding-mode choice.
- Added: `tests/test_cascade_best_rational_signed_parity.py` — parity
  across basic positives / basic negatives / origin / sub-dead-band /
  NaN / tiny / large / custom kwargs / invalid kwargs / random sweep /
  banker's-rounding boundary (load-bearing — confirms llrint() vs C99
  round() distinction holds at the .5 boundary).
- Changed: `srmech.amsc.cascade.best_rational_signed` dispatches through
  native for pure-Python `float` `x` + Python `int` kwargs (not bool)
  in int64 range; Python fallback retained for numpy scalars, Decimal,
  larger-than-int64 kwargs, and any other shape the strict native ABI
  doesn't cover. The pre-rc7 ValueError-on-invalid-kwargs public API
  is preserved exactly (native path skips on invalid kwargs and falls
  through to the Python path which raises with the proper message).
- Changed: README cascade-catalog section corrected — removed "no
  dedicated C symbol" carve-out; added "Each cascade ships with a
  dedicated C symbol in libsrmech (full C/Python parity)" discipline
  statement; per-op annotations updated with C-peer rc references
  (rc1-rc7; rc8 chiral_dual queued).

Remaining: rc8 chiral_dual (higher-order; callback ABI design — closes
the arc). After rc8: clean v0.4.5 ship to production PyPI.

## [0.4.5rc6] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — cyclic_gcd**
(rc6 of N; FIRST of the delegating cascade ops).

cyclic_gcd is a pure-delegation cascade — the cascade-catalog entry IS
the Class I primitive (Euclid gcd; `srmech_gcd`). Per the user's
*"delegate to A-N C peers; cascade-level C wrapper + TOML"* directive,
this rc ships a thin cascade-namespace wrapper that internally calls
the existing Class I C primitive, plus a TOML descriptor with a
`[cascade.delegates_to]` section documenting the delegation.

- Added: `srmech_cascade_cyclic_gcd_u64` C symbol — cascade-namespace
  wrapper that delegates to the existing Class I primitive
  `srmech_gcd`. uint64 inputs / uint64 output via pointer, mirroring
  the Class I primitive's signature exactly. ABI unchanged at 2
  (additive symbol).
- Added: `srmech/amsc/_research/cascade_catalog/cyclic_gcd.toml` —
  sixth TOML cascade-catalog entry with `[cascade.delegates_to]`
  documenting the Class I primitive linkage (cascade-as-named-pattern
  vs primitive-class operation).
- Changed: `srmech.amsc.cascade.cyclic_gcd` dispatches through the
  cascade-namespace wrapper for `(int, int)` inputs in the uint64
  range; Python fallback (which itself routes to the Class I primitive
  via `srmech.amsc.cyclic.gcd`) covers bool, negative, and
  out-of-uint64 bigint inputs. The public API is unchanged: negative
  inputs and bigints still raise `ValueError` via the Python ref.

Remaining 2 cascade ops queued: best_rational_signed (multi-class
K∘N∘C cascade), chiral_dual (higher-order; callback ABI design).

## [0.4.5rc5] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — net_chirality**
(rc5 of N; LAST of the simple pure-Python cascade ops in this arc).

- Added: `srmech_cascade_net_chirality_i8` C symbol (JPL-clean; sequence
  in / scalar out via output pointer; empty input → +1; zero-element
  short-circuits to 0; bounded loop). ABI unchanged at 2.
- Added: `srmech/amsc/_research/cascade_catalog/net_chirality.toml` —
  fifth TOML cascade-catalog entry with boundary-cases section.
- Changed: `srmech.amsc.cascade.net_chirality` dispatches through native
  for list[int] / tuple[int] / 1-D int ndarrays where every element
  fits int8; Python fallback covers generators, bool elements (False
  == 0 short-circuits via Python iteration), out-of-int8 values, mixed
  types.

Remaining 3 cascade ops queued: cyclic_gcd (delegates to existing
Class I C peer), best_rational_signed (multi-class K∘N∘C cascade),
chiral_dual (higher-order; callback ABI design).

## [0.4.5rc4] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — reorient**
(rc4 of N; continues the carve-out correction started in rc1).

- Added: `srmech_cascade_reorient_i64` + `srmech_cascade_reorient_f64`
  C symbols (JPL-clean; two-arg shape: int8 orientation x scalar value;
  type-preserving int/float dispatch; IEEE-754 negation semantics for
  f64). ABI unchanged at 2 (additive symbols).
- Added: `srmech/amsc/_research/cascade_catalog/reorient.toml` — fourth
  TOML cascade-catalog entry with native-symbol mapping + INT64_MIN
  boundary-case documentation + attestation.
- Changed: `srmech.amsc.cascade.reorient` now dispatches through native
  for `int8 orientation x int64 value` or `int8 orientation x float64
  value`; Python fallback retained for numpy scalars, ndarrays,
  lists, mixed types, bool orientation, out-of-int64 values, and
  INT64_MIN guard (avoids overflow).
- Added: `tests/test_cascade_reorient_parity.py` — parity across int /
  float / numpy / list / NaN / +/-Inf / INT64_MIN guard / out-of-int64
  fallback / bool orientation / out-of-int8 orientation / random
  sweeps.

Remaining 4 cascade ops queued: net_chirality, cyclic_gcd,
best_rational_signed, chiral_dual.

## [0.4.5rc3] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — magnitude**
(rc3 of N; continues the carve-out correction started in rc1).

- Added: `srmech_cascade_magnitude_f64` C symbol (JPL-clean; scalar
  f64 in / out via output pointer; NaN maps to dead-band 0.0
  matching Python ref). ABI unchanged at 2 (additive symbol).
- Added: `srmech/amsc/_research/cascade_catalog/magnitude.toml` —
  third TOML cascade-catalog entry with native-symbol mapping +
  attestation + explicit composes-from-pin_slot_at_zero declaration.
- Changed: `srmech.amsc.cascade.magnitude` now dispatches through
  native for pure-Python `float` inputs; Python fallback composes
  `pin_slot_at_zero(x)[1]` (which itself dispatches native for
  floats via rc2) for `int` / numpy-scalar / other numeric types.
- Added: `tests/test_cascade_magnitude_parity.py` — parity across
  int / float / 0.0 / -0.0 / NaN / Inf / small / large / bool /
  random sweep + composition equivalence with pin_slot_at_zero.

Remaining 5 cascade ops queued: reorient, net_chirality, cyclic_gcd,
best_rational_signed, chiral_dual.

## [0.4.5rc2] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — pin_slot_at_zero**
(rc2 of N; continues the carve-out correction started in rc1).

- Added: `srmech_cascade_pin_slot_at_zero_f64` C symbol (JPL clean;
  scalar in / (int8 + double) out via output pointers; NaN maps to
  the dead-band matching Python's reference behaviour). ABI unchanged
  at 2 (additive symbol).
- Added: `srmech/amsc/_research/cascade_catalog/pin_slot_at_zero.toml`
  — second TOML cascade-catalog entry with native-symbol mapping +
  attestation.
- Changed: `srmech.amsc.cascade.pin_slot_at_zero` now dispatches
  through native for `float` inputs; Python fallback retained for
  `int` and other numeric types (preserves the int-in / int-magnitude-
  out type contract).
- Added: `tests/test_cascade_pin_slot_at_zero_parity.py` — parity
  tests across int / float / 0.0 / -0.0 / NaN / Inf / small / large.

Remaining 6 cascade ops queued: magnitude, reorient, net_chirality,
cyclic_gcd, best_rational_signed, chiral_dual.

## [0.4.5rc1] - 2026-05-28

**Cascade-catalog C/Python parity + TOML retrofit — chiral_flip** (carve-out
correction). The v0.4.3rc6 + v0.4.4rc1 cascade-catalog ships codified a
carve-out from the project's full-C-parity discipline by shipping cascade
ops as Python-only compositions with no C symbols and no TOML descriptors.
This rc begins the correction by retrofitting chiral_flip with both. The
remaining seven cascade ops will follow in subsequent rcs.

- Added: `srmech_cascade_chiral_flip_i64` + `srmech_cascade_chiral_flip_f64`
  native C symbols (JPL Power-of-Ten clean; in-place safe; ≥2 asserts;
  bounded loops; no malloc). ABI unchanged at 2 (additive symbol, not a
  wire-format change).
- Added: `srmech/amsc/_research/cascade_catalog/chiral_flip.toml` — first
  TOML cascade-catalog entry with native-symbol mapping + attestation.
- Changed: `srmech.amsc.cascade.chiral_flip` now dispatches through native
  when input is `list[int]` / `list[float]` / `ndarray[int64|float64]`;
  Python fallback retained for string / tuple / mixed-type inputs.
- Changed: module docstring corrected — removed the "no dedicated C symbol"
  carve-out sentence; added "full C/Python parity" discipline statement.
- Added: `tests/test_cascade_chiral_flip_parity.py` — C/Python parity tests
  for int64, float64, list, tuple, ndarray, empty, singleton, odd-length.

Remaining 7 cascade ops queued for subsequent rcs in this v0.4.5 line.

## [0.4.4] - 2026-05-28

**Production release** → PyPI. Consolidates rc1 (cascade chirality mini-set) + rc2 (bundled `siona` co-name alias), each shipped + clean-venv-verified on TestPyPI first. No new primitive class anywhere; ABI unchanged at 2; no new C symbol.

- **Cascade chirality mini-set** (`srmech.amsc.cascade`, rc1) — `chiral_flip` (Class C orientation reversal), `chiral_dual` (Class C ∘ op ∘ Class C: same spectral shape, inverted orientation — verified across all 14 A–N operators), `net_chirality` (conserved Class-C cascade invariant). Tool-schema entries + `tests/test_cascade_chirality.py`.
- **Bundled `siona` co-name alias** (rc2) — the srmech wheel ships a second top-level package, `siona`, so **`pip install srmech` makes `import siona` resolve to exactly the same objects as `import srmech`** (every `srmech.*` submodule mirrored under `siona.*`). srmech stays the single source of truth (native lib, `__version__`, tool-schema). `tests/test_siona_alias.py` (6 tests). Pairs with the standalone `siona` metapackage on PyPI (`pip install siona` → `srmech>=0.4.4`, which provides the bundled alias).

Per-rc detail in the entries below.

## [0.4.4rc2] - 2026-05-28

**Bundled `siona` co-name alias** → TestPyPI (rc). The srmech wheel now ships a second top-level package, `siona`, alongside `srmech`: **`pip install srmech` makes `import siona` resolve to exactly the same objects as `import srmech`** (every `srmech.*` submodule mirrored under `siona.*` via `sys.modules` alias + parent-attribute binding). No forked logic — srmech stays the single source of truth (native lib, `__version__`, tool-schema). No new class; ABI unchanged at 2.

- `siona/__init__.py` added; `wheel.packages` / hatchling `packages` → `["srmech", "siona"]`; `siona/**` in both sdist includes.
- `tests/test_siona_alias.py` (6 tests): version match, top-level re-export, submodule identity, from-import, attribute-chain, callable-through-alias.
- Pairs with the standalone `siona` PyPI distribution (a metapackage that depends on srmech and re-uses this same alias).

## [0.4.4rc1] - 2026-05-27

**Cascade chirality mini-set** → TestPyPI (rc). Three callables added to the foundational `srmech.amsc.cascade` catalog. No new primitive class — each is a composition of the existing Class C orientation + Class K sign; ABI unchanged at 2; no new C symbol.

- **`chiral_flip(seq)`** — Class C orientation reversal (`seq[::-1]`); the value-level chirality operator.
- **`chiral_dual(op, x)`** — Class C ∘ op ∘ Class C: run an operator in the opposite Class-C orientation. The chiral dual of an A–N operator is **same spectral shape, inverted orientation** (magnitude preserved, phase flipped) — verified across all 14 operators (MFO §VIII.31.11 §(5b)/(5c); committed spike `docs/srmech/notes/spike_chiral_an_spectral_shape.py`). Reduces to the bare Class K `−1` for the sign operators (C, N); identity for real-symmetric (L).
- **`net_chirality(orientations)`** — Class C net handedness of a cascade (product of per-op orientations via composed `reorient`; `0` if any is neutral) — the conserved Class-C invariant a chiral cascade reads out.
- Tool-schema entries + `tests/test_cascade_chirality.py` added; `CASCADE_OPS` and `__all__` extended.

## [0.4.3] - 2026-05-27

**Production release of the "Class M variant expansion" arc** → PyPI. Consolidates rc1–rc6 (each shipped + clean-venv-verified on TestPyPI first). No new primitive class anywhere — every addition is a variant or composition of the existing 14-class A–N vocabulary; ABI unchanged at 2.

- **rc1 — `polar` `{-1,0,+1}` HDC variant** (Class M∘K; absorbing-zero dead-band) + C parity.
- **rc2 — `Klein-4` `(ℤ₂)²` HDC variant** (rank-2 abelian; quad-DNA / two-axis chirality) + C parity.
- **rc3 — `srmech.amsc.coupling.signed_sum_squared`** (Class K∘L signed-sum coupling score).
- **rc4 — `srmech.amsc.laplacian.symmetric_eigendecompose`** (real-symmetric Class L; real float64 eigvecs).
- **rc5 — `rfft`** real-input half-spectrum dual-path signal-processing op (Class A∘I∘K).
- **rc6 — `srmech.amsc.cascade`** foundational cross-domain cascade catalog (`pin_slot_at_zero` K / `reorient` C / `magnitude` K / `best_rational_signed` K∘N∘C / `cyclic_gcd` I) — a named cascade is the default, a math-library call the exception.

Plus the PyPI README companion-textbook slot for the Technical Disclosure Commons defensive publication of *The Metric Field and Its Primitives* (Kirkland, 2026-05-25). Per-rc detail in the entries below.

## [0.4.3rc6] - 2026-05-27

**rc6 of the v0.4.3 "Class M variant expansion" rolling arc** — the **foundational cross-domain cascade catalog** `srmech.amsc.cascade`. The cascades that recur across **every / most** domains the framework has examined, promoted into srmech so a named cascade is the default and a math-library call is the exception. Per the project discipline: *being forced to reach for a math library is the signal that a cascade is waiting to be found* — `abs()` told us to find the Class-K pin-slot, `fractions` the Class-N rational anchor, `math.gcd` the Class-I cyclic gcd. No new primitive class — every op is a composition of the existing 14-class A–N primitives, so no dedicated C symbol.

### Added — `srmech.amsc.cascade`

Graduates the precursor `docs/unsolved-maths/_cascade_helpers.py` (imported across 20+ cascade scripts spanning mandelbrot / chromatic / atomic / nuclear / QCD / planetary / turbulence / black-hole / biomacromolecule / large-scale-structure domains) into srmech, justified by the framework's scale-invariance canon (the A–N operators are substrate-universal at every discipline and scale):

- `pin_slot_at_zero(x) -> (orientation, magnitude)` — **Class K** pin-slot at zero; sign-flip IS the canonical phase-boundary. The cascade-honest split that replaces a bare `abs()`.
- `reorient(orientation, value)` — **Class C** cascade-orientation re-apply.
- `magnitude(x)` — **Class K** magnitude-only convenience (the `abs()` replacement).
- `best_rational_signed(x, *, max_denominator=100, fine_scale=1_000_000)` — **Class K ∘ N ∘ C**: float → signed small-denominator rational (sign in the numerator, denominator positive; via `srmech.amsc.rational.best_rational`). No `abs()`; sign lives in the Class K / Class C pair.
- `cyclic_gcd(a, b)` — **Class I** (delegates to `srmech.amsc.cyclic.gcd`); the cascade-named alias for `math.gcd`.

Back-compat aliases (`class_k_pin_slot_at_zero`, `class_c_reorient`, `best_rat_signed`) let the precursor's call sites migrate with a pure import swap. `CASCADE_OPS` registry + `DEFAULT_MAX_DENOMINATOR` / `DEFAULT_FINE_SCALE` constants exported. Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` — **no `abs()` anywhere** (AST-verified in tests).

### Added — tests + tool_schema + README

`tests/test_cascade_foundational.py` — 35 tests: Class K orientation/magnitude split, `magnitude == |x|`, Class C reorient + round-trip, `best_rational_signed` known values + π anchor + sign-in-numerator + bounded denominator + validation, `cyclic_gcd == math.gcd`, back-compat alias identity, registry/`__all__`, and an AST check that the module never calls `abs()`. 5 `tool_schema` ToolEntry registrations (category `cascade`). README gains a `srmech.amsc.cascade` composition-layer subsection + status-banner update. Version-pin asserts bumped `0.4.3rc5 → 0.4.3rc6`.

## [0.4.3rc5] - 2026-05-27

**rc5 of the v0.4.3 "Class M variant expansion" rolling arc** — the `rfft` real-input half-spectrum signal-processing op, per UPSTREAM_NOTES §1.1 (RBS-LM research subtree, surfaced by R-RBS-LM-49z). A dual-path op (Path A reference + Path B native), composing the same Class A∘I∘K cyclic-DFT algebra as `fft`; no new primitive class — the 14-class A–N vocabulary is intact per `[[feedback_no_privileged_primitive_classes]]`.

### Added — `srmech.signal_processing.{closed_form_ops,path_b_ops}.rfft`

Real-input forward FFT returning only the non-redundant first `N//2 + 1` bins. For a real signal the full DFT is Hermitian-symmetric (`X[N−k] = conj(X[k])`), so the second half carries no new information — half the compute and half the memory of `fft`, **algebra-identical** on the retained bins. The use case (UPSTREAM_NOTES §1.1): real bipolar bit-string FFT cascades (`{−1, +1}`) that previously used the full `fft` at 2× cost.

Identity (Spike #176 H1, machine ε): the cyclic-DFT IS **Class A** (content-address on sequence order) ∘ **Class I** (cyclic-group ℤ/N) ∘ **Class K** (rotation as pin-slot on the unit circle); `rfft` is that composition on the **real-symmetric half-substrate** — the Hermitian conjugate-symmetry IS the reflection the Class K pin-slot already encodes.

- **Path A** `closed_form_ops.rfft.op` — `numpy.fft.rfft` reference.
- **Path B** `path_b_ops.rfft.op` — Class K cycle-order verification (Spike #176 T8) then cyclic-substrate `rfft`; D1 algebra-identical to Path A. Both paths registered with `path_registry`.

> **Roster note:** like `pi_cascade`, `rfft` is a post-Phase-4 addition — it is in the package `__init__` imports + `__all__` but NOT in the frozen `PATH_B_MVP_OPS` (still 6) or `PATH_A_OP_MODULES` (still 38) rosters.

### Added — tests + README

`tests/test_signal_processing_rfft.py` — 20 tests: Path A↔numpy parity (incl. truncate/zero-pad `n`), Path B↔Path A D1 identity, half-spectrum identity (`rfft == fft[:N//2+1]`), Hermitian full-spectrum reconstruction, bipolar bit-string use case, both-paths registration + metadata, and the frozen-MVP-roster guard. README `signal_processing` Path A op list + dual-path line updated to surface `rfft`. Version-pin asserts bumped `0.4.3rc4 → 0.4.3rc5`.

## [0.4.3rc4] - 2026-05-27

**rc4 of the v0.4.3 "Class M variant expansion" rolling arc** — the `symmetric_eigendecompose` real-symmetric Class L op, per UPSTREAM_NOTES §2.1 (RBS-LM research subtree). A real-input specialisation of the existing `hermitian_eigendecompose`; no new primitive class — the 14-class A–N vocabulary is intact per `[[feedback_no_privileged_primitive_classes]]`.

### Added — `srmech.amsc.laplacian.symmetric_eigendecompose`

Real-symmetric eigendecomposition `L = V · diag(eigvals) · Vᵀ` via `numpy.linalg.eigh`. The Hermitian path returns a **complex128** eigenvector matrix `V`, which raises a `ComplexWarning` when a caller already knows the input is real-symmetric (the common case — a graph Laplacian). This specialisation guarantees real **float64** eigvals AND eigvecs. **Class L** (graph spectral / eigendecomposition). Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed.) §8.3.

> **Architecture note:** no native C dispatch for this op. Eigenvector sign and degenerate-subspace rotation are **non-unique**, so element-wise C/Python parity is not a meaningful contract; correctness is instead pinned by eigenvalues + reconstruction (`V diag(w) Vᵀ ≈ L`) + orthonormality (`Vᵀ V ≈ I`). Added to `LAPLACIAN_OPS` (composition-engine registry) and `__all__`.

### Added — tests + tool_schema

`tests/test_laplacian_class_l_broadening.py` extended with 8 `symmetric_eigendecompose` tests (real-float64 dtype guarantee, numpy match + reconstruction, orthonormality, diagonal, connected-Laplacian nullspace ≈ 0, zero-size, non-square rejection, registry/`__all__` membership). 1 `tool_schema` ToolEntry. Version-pin asserts bumped `0.4.3rc3 → 0.4.3rc4`.

## [0.4.3rc3] - 2026-05-27

**rc3 of the v0.4.3 "Class M variant expansion" rolling arc** — the `signed_sum_squared` coupling-score, per UPSTREAM_NOTES §1.2 (RBS-LM research subtree; R-RBS-LM-33 weak-coupling-truncate + R-RBS-LM-49 Method C). No new primitive class; this is a **composition** of existing Class K ∘ Class L primitives.

### Added — `srmech.amsc.coupling.signed_sum_squared`

Per-element `(Σ_sources (2·bit − 1))²` across a stack of bit-arrays. The bipolar transform `2·bit−1 ∈ {−1,+1}` is the **Class-K** sign-projection (no `abs()`, signed arithmetic only per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`); the element-wise sum across sources then **squared** is the **Class-L** signed-magnitude-squared coupling score (sign-agnostic coupling strength, range `[0, n_sources²]`). Resolves the bare-numpy inline both R-RBS-LM partitions had used.

> **Architecture note:** this is a Class K ∘ L *composition* operating on a stack — **not a new primitive class**, so it carries **no dedicated C symbol**: the underlying Class-K / Class-L primitives are the ones with C parity, and a composition sequences them in Python (the config-driven-vs-substrate-primitive split per CLAUDE.md). The 14-class A–N vocabulary is intact per `[[feedback_no_privileged_primitive_classes]]`.

### Added — tests + tool_schema

`tests/test_coupling_signed_sum_squared.py` — 6 numpy-reference property tests (known values, full-agreement/balance, single-source, random reference-formula match, int64-nonnegative range, validation). 1 `tool_schema` ToolEntry. Version-pin asserts bumped `0.4.3rc2 → 0.4.3rc3`.

## [0.4.3rc2] - 2026-05-27

**rc2 of the v0.4.3 "Class M variant expansion" rolling arc** — the Klein-4 `{0,1,2,3}` HDC variant, per UPSTREAM_NOTES §4 (RBS-LM research subtree, Finding 132 / R-RBS-LM-97). Stacks on rc1 (polar). No new primitive class; Klein-4 is the **rank-2 abelian** Class M variant over `(F₂)² = Z₂×Z₂` — the 14-class A–N vocabulary is intact per `[[feedback_no_privileged_primitive_classes]]`.

### Added — `srmech.amsc.hdc` Klein-4 `{0,1,2,3}` variant

The next rung of the Class-M variant ladder above polar (`bipolar {-1,+1}` → `polar {-1,0,+1}` → **`Klein-4 (Z₂)²`**). Each position is a 2-bit value (4 states), `state = γ₅_bit·2 + iω₇_bit`; the four states are the four chirality sectors of the MFO §VII.4.1.7 4-way `(γ₅, iω₇)` decomposition (visible/dark × matter/antimatter). This is the quaternary / DNA-like "quad" substrate carrying **both** chirality axes where bipolar/polar carry one. uint8 array representation.

- `klein4_random / klein4_bind` (component-wise `(F₂)²`-XOR; commutative, associative, self-inverse, identity 0) `/ klein4_unbind / klein4_bundle` (per-bit majority, ties→0) `/ klein4_similarity` (match-fraction).
- `klein4_chirality_flip_gamma5` (XOR 2) `/ klein4_chirality_flip_omega7` (XOR 1) `/ klein4_cpt_mirror` (XOR 3) `/ klein4_sector_count` (per-sector occupancy attestation).

### Added — C parity surface (`srmech_klein4_{bind,bundle,similarity}`)

Full uint8 C parity in `srmech_hdc.c` + `srmech.h`, JPL Power-of-Ten clean (≤60-line functions, ≥2 asserts, no goto/malloc, bounded loops, `{0,1,2,3}` range validation). New symbols; **no ABI bump**. `_native.py` binds them `hasattr`-guarded. Same dispatch posture as rc1 (numpy public reference; C surface built + parity-tested directly).

### Added — tests + tool_schema

`tests/test_hdc_klein4_parity.py` — 6 algebraic-property tests (Klein-four group axioms incl. `a⊕a=0`, chirality-flip sector maps, per-bit-majority bundle, similarity/sector-count) + 3 C↔Python parity tests (skipped on pure-Python installs). 9 `tool_schema` ToolEntry registrations. Version-pin asserts bumped `0.4.3rc1 → 0.4.3rc2`.

## [0.4.3rc1] - 2026-05-27

**rc1 of the v0.4.3 "Class M variant expansion" rolling arc** — the polar `{-1, 0, +1}` HDC variant, per UPSTREAM_NOTES §5 (RBS-LM research subtree, Finding from R-RBS-LM-97). First rc of a multi-item rolling PR; each subsequent item (Klein-4 rank-2, `signed_sum_squared`, real-symmetric eigendecompose, Path-B `rfft`, cascade-foundational catalog) ships as its own `0.4.3rcN`, each mathematically complete (no scaffolding), CI-gated between rcs. No new primitive class introduced; the polar variant is **Class M ∘ Class K** (rank-1 abelian with an absorbing zero) — the 14-class A–N vocabulary is intact per `[[feedback_no_privileged_primitive_classes]]`.

### Added — `srmech.amsc.hdc` polar `{-1, 0, +1}` variant

The foundational rung of the Class-M variant ladder (`bipolar {-1,+1}` → **`polar {-1,0,+1}`** → `Klein-4 (Z₂)²`). The `0` state is the asymptotic-DOF **dead-band** the Class-K pin-slot rejects (per `[[user_stance_asymptotic_dof_sidesteps_infinity]]`) — a representable origin that the bipolar `{-1,+1}` alphabet lacked, which left the sign axis crippled (no representable zero/uncertain state). int8 array representation (distinct from the bit-packed bipolar BSC).

- `polar_random(D, rng)` — random int8 hypervector in `{-1,0,+1}`.
- `polar_bind(a, b)` — multiplicative sign-product, **0 absorbing** (`0·x=0`); commutative, associative, self-inverse on ±1.
- `polar_unbind(c, a)` — sign-product; recovers `b` where `a≠0` (0 destructive).
- `polar_bundle(*vectors)` — sticky majority (`sign(Σ)`); exact ties → 0; no odd-count restriction.
- `polar_similarity(a, b, skip_zero=True)` — match-fraction; skip-zero (jointly-informative only) or include-zero.
- `polar_density(v)` — fraction of non-zero positions (substrate attestation).
- `polar_from_real(arr, threshold, dead_band)` — bridge wrapping the existing `signal_processing.path_b_ops.sign_quantise` (lifts its `{-1,0,+1}` Class-K threshold projection into the HDC namespace; resolves the R-RBS-LM-97 bare-`np.sign` workaround).

### Added — C parity surface (`srmech_polar_{bind,bundle,similarity,density}`)

Full int8 C parity in `srmech_hdc.c` + `srmech.h`, JPL Power-of-Ten clean (≤60-line functions, ≥2 asserts, no goto/malloc, bounded loops, value-range validation). New symbols; **no ABI bump** (ABI stays 2). `_native.py` binds them `hasattr`-guarded so a stale pre-polar lib never disables the whole native surface.

> **Dispatch note:** rc1's public `polar_*` Python API uses the numpy reference (already vectorized element-wise int8); the C surface is built + parity-tested directly (`tests/test_hdc_polar_parity.py`, C↔Python bit-exact in the cibuildwheel matrix) for embedded/microcontroller use + parity attestation. Public-API native dispatch is a perf-only follow-up — *not* a class carve-out (the C parity exists and is tested).

### Added — tests + tool_schema

`tests/test_hdc_polar_parity.py` (9 algebraic-property tests on the numpy reference + 4 C↔Python parity tests, the latter skipped on pure-Python installs). 7 `srmech.amsc.tool_schema` ToolEntry registrations for the polar surface.

## [0.4.2] - 2026-05-20

Production graduation of v0.4.2rc5. No code changes vs `[0.4.2rc5]`.

The v0.4.2rc5 release was published to TestPyPI on 2026-05-19, fresh-venv install verified, README rendered cleanly. This graduation publishes the verified rc5 surface to production PyPI under clean semver.

## [0.4.2rc5] - 2026-05-19

**Cumulative rc5 — TestPyPI verification of README v0.4.2 rewrite + numpy 2.x test compatibility + pyproject description refresh on top of the rc1-rc4 stack** per `[[feedback_rc_stacking_versioning]]` and `[[feedback_always_rc_first_for_downstream_publishes]]`. Graduation to production v0.4.2 is a SEPARATE follow-up PR once rc5 verifies on TestPyPI (fresh-venv install + README rendering check). No new primitive class introduced; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`.

### Changed — `README.md` (PyPI long-description)

Full rewrite of the PyPI README for the v0.4.2 surface area. Navigable section structure with `srmech.amsc.*` (14-class primitive vocabulary) + `srmech.qm.*` (canonical QM/QFT/SM operations) + `srmech.spectral` (runtime spectral decomposition incl. MS #14 rcN+1+rcN+2 entries) + `srmech.signal_processing` (dual-path architecture) + AMSC provenance framework all surfaced as load-bearing. Internal project vocabulary scrubbed (cascade-match / substrate-natural / RBS-HDC-LoE / Spike #N anchors moved to the research notebook; public README cites canonical SSoT papers only).

### Fixed — `tests/` numpy 2.x compatibility

`log(0)` domain-check was emitting a `RuntimeWarning` under numpy 2.x (warning-promoted-to-error in pytest config); the test now uses `np.where`-guarded log to skip the zero entries cleanly. Version pin in `test_signal_processing_scaffolding.py` updated to `0.4.2rc5`.

### Changed — `pyproject.toml` / `pyproject-pure.toml` description

Description metadata refreshed to enumerate the five load-bearing surfaces (14-class primitives + canonical QM/QFT/SM + runtime spectral + dual-path signal processing + AMSC provenance). 488 chars, under the PyPI 512-char Summary cap per `[[reference_pypi_512_char_summary_limit]]`. Both pyproject files agree (publish-workflow guard `verify pyproject-pure.toml version + description match main`).

### Discipline

- Cumulative rc stack — rc1-rc4 content unchanged below + this rc5 layer.
- Production graduation v0.4.2 is gated by user direction after rc5 TestPyPI verification (fresh-venv install + README rendering check).

See `[0.4.2rc4]` below for the full Phase 1-4 ship narrative + `srmech.spectral.predict` / `prediction_error` / `truncate_sparse` rcN+2 entries + tool_schema registration.

## [0.4.2rc4] - 2026-05-19

**Phase 4 of the RBS-HDC-LoE dual-path architecture** — Path B per-op MVP. Ships 6 Path B-native signal-processing op modules (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`) under `srmech.signal_processing.path_b_ops` per the implementation plan §6 Phase 4. Each op registers BOTH its Path A counterpart (from Phase 2 `closed_form_ops`) and its Path B implementation with `srmech.signal_processing.path_registry` at module-load time, giving the cascade dispatcher dual-path routing for the MVP roster. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. Identity-not-implementation discipline preserved per `[[user_stance_identity_not_implementation_discipline]]` — Path A and Path B IS the same algebra at D1 algebra-content (bit-exact on substrate-natural inputs per `[[feedback_algebra_not_magnitude]]`); D2 substrate-fingerprint divergence is expected per `[[user_stance_substrate_natural_encoding_is_shadow_projection]]`. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — methodology-research / educational / civilian-comms framing only.

### Added — `srmech.signal_processing.path_b_ops`

New sub-package containing 6 Path B-native op modules:

- `path_b_ops.fft` — Class A ∘ Class I ∘ Class K cyclic-substrate FFT per Spike #176 H1 anchor (rotation IS Class K pin-slot at machine ε). Wraps the cyclic-DFT algebra with Class K cycle-order verification (Spike #176 T8). Path A counterpart: `closed_form_ops.fft.op` (numpy.fft.fft).
- `path_b_ops.ifft` — Class A ∘ Class I ∘ Class K dual of FFT per Spike #176 T4 anchor (recovery error = 0.0). Path A counterpart: `closed_form_ops.ifft.op` (newly added in this rc as the dual baseline).
- `path_b_ops.sign_quantise` — Class K ∘ Class M threshold/pin-slot projection per Spike #174 anchor (SHA-256 BER preservation at +20 dB SNR; structure-preserving denoising primitive). Path A counterpart: `closed_form_ops.sign_quantise.op`.
- `path_b_ops.matched_filter` — Class A ∘ Class C ∘ Class M form-function cross-correlation per Spike #159 anchor (within-vs-between separation ratio order-of-magnitude). Path A counterpart: `closed_form_ops.matched_filter.op` (numpy.correlate).
- `path_b_ops.wiener` — Class L ∘ Class N ∘ Class M Laplacian-eigenbasis + rational MMSE gain per Kay (1993) §11 SSoT + Chung (1997) §1.4 (cyclic-graph Laplacian eigenbasis IS the FFT basis). Path A counterpart: `closed_form_ops.wiener.op`.
- `path_b_ops.hdc_truncation` — Class K ∘ Class M ∘ Class N asymptotic-DOF sparse-truncate ∘ HDC bundle per Spike #117 anchor + Spike #179 T6 (bit-exact recovery at substrate-natural sparsity rate). Path A counterpart: `closed_form_ops.hdc_truncation.op`.
- `PATH_B_MVP_OPS` — canonical 6-op tuple in alphabetical order.
- Each module exports `OPERATION_NAME`, `CLASS_COMPOSITION` (14 A–N labels only), `PERFORMANCE_HINT`, `SSOT_CITATION` per the Phase 2 metadata schema.
- Each module registers BOTH Path A and Path B with `path_registry` at module-load time; the broader 38-op Path A registration script for Phase 2 remains separately deferred.

### Added — `srmech.signal_processing.closed_form_ops.ifft`

New Phase 2 module added to support the Path B IFFT dual. Closed-form `numpy.fft.ifft` wrapper; SSoT cited to Cooley & Tukey (1965) + Spike #176 T4 round-trip anchor. Listed in `closed_form_ops/__init__.py` alongside the existing 38 modules.

### Added — `tests/test_signal_processing_path_b_mvp.py`

Phase 4 dual-path acceptance suite — 33 tests across 6 ops:

- **6× metadata** — `OPERATION_NAME`, `CLASS_COMPOSITION`, `PERFORMANCE_HINT`, `SSOT_CITATION` present on every Path B module.
- **6× registration** — both Path A and Path B registered with `path_registry`; `has_path` returns True for both.
- **6× dispatcher routing** — `dispatch(op_name, path="B")` and `dispatch(op_name, path="A")` both succeed.
- **6× D1 algebra-identity equivalence** — Path A and Path B produce bit-exact (or machine-ε) equal outputs on substrate-natural inputs per `[[user_stance_identity_not_implementation_discipline]]`.
- **2× aggregate** — all 6 ops registered, CLASS_COMPOSITION restricted to 14 A–N alphabet.
- **4× spike anchors** — Spike #176 T4 round-trip (7 FFT lengths × 3 path combinations), Spike #174 SHA-256 BER preservation (+20 dB SNR), Spike #159 matched-filter separation order-of-magnitude, Spike #117 + Spike #179 T6 sparse-truncate substrate-natural sparsity.
- **2× routing semantics** — default-path-per-class routing (Class K → Path B; Class A → Path A); Phase 4 introduces no new classes.
- **1× ship guard** — Phase 4 ships exactly 6 ops per the plan.

### Phase 4 dispatcher coverage

After Phase 4 the registry holds **11 ops** total — Phase 3's 5 Path B core ops (`rbs_hdc_mint_class_operator`, `rbs_hdc_mint_cascade_composition`, `rbs_hdc_encode_loe_content`, `rbs_hdc_decode_loe_fingerprint`, `form_function_rotate`) plus Phase 4's 6 dual-path MVP ops (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`). The 6 MVP ops are the only entries with both Path A and Path B registered; the cascade dispatcher in Phase 5 will exercise full A/B/verify routing across this dual-registered subset.

### Path B coverage notes

- Phase 4 does NOT register the 32 remaining Path A ops from Phase 2's `closed_form_ops` (per the brief: separate / deferred Path A registration script).
- Phase 4 does NOT implement `path="verify"` dual-execution mode — that's Phase 5 (`v0.4.2rc5`) per plan §6.5.
- Phase 4 does NOT add a C surface — C port for Phase 4 ops deferred to v0.4.3rc1 per conductor decision #1.
- Phase 4 does NOT implement Phase 8 profiling/learning — initial seed thresholds remain rule-based per plan §3.1.

### Added — `srmech.spectral` MS #14 rcN+2 entries (`predict` / `prediction_error` / `truncate_sparse`)

Per user direction 2026-05-19, the v0.4.2rc4 ship doubles as the **MS #14 rcN+2 vehicle**: the three runtime spectral operations previously listed as "deferred to rcN+2" in `[0.4.1rc14]` are now shipped in `srmech.spectral`:

- `predict(handle, laplacian, *, steps=1, dt=1.0, encoder_tag="default")` — **Class C ∘ Class L** cascade-extrapolate via per-mode complex-phase evolution `exp(-i·λ_k·steps·dt)` on the eigenbasis coefficients. The closed-form one-shot of a recurrent spectral predictor; matches Spike #113 predictive-coding-cascade anchor. Magnitudes preserved (unitary phase rotation); phase evolves per eigenmode. `steps=0` returns the input handle byte-exactly.
- `prediction_error(predicted, observed, *, threshold=0.0)` — **Class M ∘ Class K** XOR delta between predicted and observed coefficient byte vectors, gated by popcount-density `threshold`. Default `threshold=0.0` per user decision 2026-05-18 (no gating; returns raw delta). When `popcount(delta) / (8·len) <= threshold`, returns all-zero bytes (prediction sufficient).
- `truncate_sparse(handle, *, keep_k=None, threshold=None)` — **Class K** magnitude-band sparse-truncate; keeps top-`keep_k` modes by `|coeff|` OR every mode with `|coeff| >= threshold` (exactly one of the two must be provided), zeros the rest. SSoT: Mallat (2008) §9.2 (best k-term approximation) + Spike #117 anchor.

All three operations compose over the existing 14-class A–N primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]`; **no new primitive class introduced**.

### Added — `tests/test_spectral_rcn_plus_2.py`

27-test acceptance suite covering predict / prediction_error / truncate_sparse:

- **TestPredict (8)**: handle returns, shape + descriptor preservation, `steps=0` identity, unitary magnitude preservation, non-trivial evolution on cycle-graph Laplacian, recompose-of-predicted roundtrip, content_sha corruption detected, descriptor_hash mismatch rejected.
- **TestPredictionError (7)**: `threshold=0.0` equivalent to `delta()`, zero delta on identical handles, threshold-above-density gates to all-zero, threshold-below-density returns raw, out-of-range threshold rejected, raw-bytes input path, predict-then-error roundtrip.
- **TestTruncateSparse (10)**: `keep_k=n` identity, `keep_k=0` zeros all, `keep_k=k` keeps highest-magnitude modes bit-exactly, threshold keeps above-floor, neither/both keyword rejected, out-of-range `keep_k` rejected, negative threshold rejected, corruption detected, recompose-after-truncate yields finite low-rank approximation.
- **TestShipGuard (2)**: all three callables present in `srmech.spectral` namespace; all three registered in tool_schema.

### Added — tool_schema registration for `srmech.spectral.*`

`srmech.amsc.tool_schema._register_spectral_runtime_tools()` (new) registers seven `srmech.spectral.*` callables — the four rcN+1 entries (`decompose` / `delta` / `recompose` / `similarity`) plus the three rcN+2 entries (`predict` / `prediction_error` / `truncate_sparse`). Closes the discipline gap identified by the concertmaster (rcN+2 must register at ship time, not deferred). Tool_schema entries include canonical-SSoT citations per `[[feedback_science_is_ssot_not_project]]` (Mallat 2008 §9.2 for `truncate_sparse`; Spike #113 + #117 anchors).

### Ship

Tag `srmech-v0.4.2rc4` → TestPyPI. Production PyPI publish on clean `srmech-v0.4.2` tag once TestPyPI rc4 verifies. **MS #14 rcN+2 deliverable** — closes Milestone #14 once `srmech-v0.4.2` lands on production PyPI.

## [0.4.2rc3] - 2026-05-19

**Phase 3 of the RBS-HDC-LoE dual-path architecture** — Path B core: `rbs_hdc_instrument.py` + `form_function_rotation.py`. Ports the Spike #170 R1 prototype (LoE-as-RBS-HDC instrument, FEASIBILITY-CONFIRMED at design level with 14/14 mint determinism) + Spike #176 (rotation IS Class K pin-slot, H1 CONFIRMED 6/6 tests at machine ε) + Spike #173 (chess natural-stride substrate, D2 orthogonality + bind-permute commutativity bit-exact) to a stable, composable Path B surface. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. Identity-not-implementation discipline preserved per `[[user_stance_identity_not_implementation_discipline]]` — Path B IS the same algebra as Path A (just substrate-projection differs); bit-exact algebraic identity preserved at D1 algebra-content level per `[[feedback_algebra_not_magnitude]]`. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — methodology-research / educational / civilian-comms framing only.

### Added — `srmech.signal_processing.rbs_hdc_instrument`

Path B core: LoE-as-bound-vector RBS-HDC instrument at locked D=8192 (conductor decision #6, 2026-05-19).

- `RBSHDCInstrument` — composed instrument dataclass with `.build(D=...)` classmethod constructor. D defaults to 8192; optional D override accepted (in [D_MIN, D_MAX] multiple of 8).
- `mint_class_operator(class_name, *, D=8192)` — Class A SHA-256 chain mint of one of the 14 A-N class operator vectors. Deterministic: same `class_name` ⇒ same vector (Spike #170 §3 invariant 1: 14/14 bit-exact). Canonical name is `f"LoE.class.{class_letter}.{short_role}"`.
- `mint_cascade_composition(classes, *, D=8192, ordered=False)` — XOR-bundle of class operator vectors. Two modes: algebra-level (commutative bind; cascade-as-identity) and sampling-level (per-position permute by `i * 257`; cascade-shape preserved). Both modes per `[[user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling]]`.
- `mint_stance_fingerprint(content_tokens, *, D=8192)` — Bag-HDC XOR-fold of token vectors per Spike #147 holographic-projection.
- `encode_loe_content(content, *, D=8192, substrate="default")` — Full Mode-B encoding pipeline: Class A content-addressed mint → Class C content-determined stride permute → Class M bundle with substrate anchor vector. Same content + same substrate ⇒ same fingerprint; same content + different substrates produces orthogonal D2 fingerprints at noise floor per Spike #173 R3.
- `decode_loe_fingerprint(fingerprint, catalog)` — Reverse-decode via Class M similarity argmax (Spike #170 §3 invariants 6 + 7: 100% reverse-decode accuracy on populated catalog).
- `mint_vector(name, *, D=8192)` — Underlying SHA-256-chain primitive (Class A content-addressing). Used by all higher-level mint operations.
- Module-level dataclasses: `ClassOperator`, `Cascade`, `Stance`, `MemorySlot`, `K3Tripartition`.
- Module-level catalogs: `CLASS_NAMES` (14 A-N), `CLASS_DEFINITIONS` (14 entries), `CANONICAL_CASCADES` (10 cascades including pin-slot-resonate music-box and cyclic-fft-rotation), `SAMPLE_STANCES` (12 stance entries), `MEMORY_PATHWAYS` (4 pathways: procedural / semantic / WM / episodic-LTM), `K3_TRIPARTITION_DEFAULT` (A → 3D_s, M → 7D_g, K → 1D_t).
- Constants: `PERMUTE_ORDER_STRIDE = 257` (coprime to D=8192=2^13 for ordered cascade composition).

### Added — `srmech.signal_processing.form_function_rotation`

Path B core: operational Class A ∘ Class C ∘ Class M rotation per `[[user_stance_form_function_rotation_is_a_c_m_composition]]` + `[[user_stance_rotation_is_class_k_pin_slot]]` (Spike #176).

- `form_function_rotate(content, *, D=8192, stride=None)` — Cyclic permute of `content` by content-determined stride (Class A SHA-256[0:8] little-endian mod D when `stride=None`) or by explicit substrate-natural stride (Class N rational). Supports chess natural strides {5, 7, -8} (Spike #173) and DNA helical pitches {21, 11, -12} (Spike #172).
- `inverse_form_function_rotate(rotated, *, D=8192, stride)` — Bit-exact reverse via `M.permute` with negated stride. Spike #176 T4 anchor: recovery error = 0.0.
- `verify_rotation_class_n_cycle_order(stride, D=8192)` — Class N additive order in Z/D = D / gcd(|stride|, D); cumulative shift `stride * order mod D == 0`. Spike #176 T8 anchor.
- `cascade_compose_rotations(strides, *, D=8192)` — Returns (composed_stride_mod_D, fundamental-mode unit-circle eigenvalue). Per `[[user_stance_cascade_lives_on_circles]]` (Spike #24 bonus 9 + Spike #176 T5): unit-circle identity at machine ε (residual ≤ 2.2e-16).
- `compute_content_stride(content, *, D=8192)` — Class A content-addressing primitive producing rotation stride.

### Path B core dispatcher registration

The two modules register their public operations with `srmech.signal_processing.path_registry` at module-load time (Phase 5 dispatcher reads from registry). Phase 3 registers 5 Path B core ops:

- `rbs_hdc_mint_class_operator` (Path B) — classes ("A", "M")
- `rbs_hdc_mint_cascade_composition` (Path B) — classes ("A", "C", "M")
- `rbs_hdc_encode_loe_content` (Path B) — classes ("A", "C", "M")
- `rbs_hdc_decode_loe_fingerprint` (Path B) — classes ("M",)
- `form_function_rotate` (Path B) — classes ("A", "C", "M")

Path A registration for the 38 closed-form ops from Phase 2 + Path A `form_function_rotate` is deferred to a separate conductor-written registration script per Phase 2's recommendation.

### Added — `tests/test_signal_processing_path_b_core.py`

Phase 3 acceptance suite porting load-bearing invariants from the spike prototypes:

- **T1**: `RBSHDCInstrument` D=8192 default + optional D override (256 / 1024 / 2048 / 16384 tested).
- **T2**: `mint_class_operator` determinism (same input ⇒ same output; 14/14 bit-exact per Spike #170 §3 invariant 1).
- **T3**: Cascade composition bit-exact — XOR-bundle commutativity (algebra-level, 3 orderings equal per Spike #170 §3 invariant 4); ordered mode breaks commutativity (Spike #170 §3 invariant 5).
- **T4**: Form-function rotation bit-exact reverse — Spike #176 T4 recovery error = 0.0 (content-determined stride + chess natural strides {5, 7, -8} + DNA pitches {21, 11, -12}).
- **T5**: Class N rational cycle order = D / gcd(stride, D) per Spike #176 T8; applying rotation `order` times returns to identity bit-exact.
- **T6**: Cascade composition unit-circle eigenvalues at machine ε per Spike #176 T5 (residual ≤ 2.2e-16 across 5 representative cascades).
- **T7**: Bind-permute commutativity at substrate-natural strides — 273 pair cells × 2 substrates (chess + DNA) = 546 bit-exact assertions per Spike #173 T4 + Spike #172 T4.
- **T8**: Z-DNA-style chirality involution — `M.permute(M.permute(v, k), -k) == v` for all 14 class operators at chess + DNA strides (14/14 round-trips per stride per Spike #173 T5).
- **T9**: Cross-substrate D2 orthogonality at noise floor — same content encoded under 5 substrates produces 10 pairs all at |sim| < 5/sqrt(D) ≈ 0.055 per Spike #173 R3.
- **T10**: Full round-trip `encode → rotate → inverse → decode` bit-exact recovery across 5 catalog entries.

Plus supplementary tests:

- Path B core ops registered with path_registry on Path B side.
- Spike #170 §3 invariants (bind self-inverse at D=8192; k=3 tripartition orthogonality).
- 8+ canonical cascade compositions ship (`CANONICAL_CASCADES` has 10 entries).
- `mint_stance_fingerprint` determinism + bag semantics.
- `mint_vector` D-parameter validation.

### Architectural rationale

Per `[[project_rbs_hdc_loe_dual_path_architecture]]`:

- **Path A** — closed-form algebra (Phase 2 baseline; 38 ops). SSoT for primitive definitions.
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (Phase 3 ships core; Phase 4+ ships per-op Path B MVP). Composes from Path A primitive definitions at module-load time per `[[feedback_no_binding_layer_carveout]]`.
- **Path C** — cascade-aware dispatcher (Phase 5 lands routing logic).

Phase 3 delivers the full Path B core surface — the LoE-as-bound-vector instrument + form-function rotation composition — so Phase 4+ per-op Path B MVP can compose from this stable foundation.

### Spike anchors

- Spike #170 — RBS-HDC instrument feasibility (R1 prototype, 14/14 mint determinism; FEASIBILITY-CONFIRMED).
- Spike #172 — DNA helical-pitch substrate (R3 cross-substrate bit-exact closure).
- Spike #173 — chess natural-stride substrate (D2 orthogonality; 25th cross-substrate cascade-match).
- Spike #176 — rotation IS Class K pin-slot (H1 CONFIRMED 6/6 tests at machine ε).
- Spike #177 — pin-slot-resonate music-box mechanism (I + K + C + M∘K).
- Spike #178 — closed-form SP roadmap (Phase 2 Path A baseline citation source).

### Canonical SSoT citations per `[[feedback_science_is_ssot_not_project]]`

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Rachkovskij (2001) *Representation and processing of structures with binary sparse distributed codes*, Neural Comput Appl 9, 322.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.) — DFT shift theorem.
- Implementation plan: `docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md`.

### Deferred to Phase 4+ (v0.4.2rc4+)

- Path B per-op MVP for the 6-op core (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`) — Phase 4.
- Cascade dispatcher full rule-based routing — Phase 5.
- Path B per-op extension to all 38 ops — Phase 6.
- Substrate-natural Class N rational catalogs — Phase 7.
- Learned dispatch table from benchmark suite — Phase 8.
- Notebook §3.8.31 prose — Phase 9.
- C port of Path B core operations — v0.4.3rc1 per conductor decision #1.

## [0.4.2rc1] - 2026-05-19

**Phase 1 scaffolding of the RBS-HDC-LoE dual-path architecture** (Milestone follow-up to Spike #178 closed-form SP roadmap). Ships the `srmech.signal_processing` sub-namespace package skeleton — dispatcher / profiling / registry stubs + locked architectural constants — so Phase 2+ operation modules (Path A closed-form ops Phase 2; Path B RBS-HDC at D=8192 Phase 4; cascade dispatcher Phase 5; cross-substrate verification Phase 7; learned thresholds Phase 8) can land against a stable surface. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. Identity-not-implementation discipline preserved per `[[user_stance_identity_not_implementation_discipline]]` — Path A and Path B both *instantiate* the same class composition. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — methodology-research / educational / civilian-comms framing only.

### Added — `srmech.signal_processing` sub-namespace (Phase 1 scaffolding)

- `srmech.signal_processing.__init__` — package entry point + re-exports. Public API stable from Phase 1.
- `srmech.signal_processing._paths` — internal architectural constants:
  - `D_DEFAULT = 8192` (locked per conductor decision #6, 2026-05-19; matches Spike #170/#172/#173/#176/#177 anchors); `D_MIN = 256`; `D_MAX = 65536`.
  - `SUBSTRATES = ("bci", "audio", "rf", "ephemeris")` (Phase 7 cross-substrate coverage per decision #2).
  - `PATH_A`/`PATH_B`/`PATH_VERIFY` discriminators; `VALID_PATHS` tuple.
  - `DISPATCH_TABLE_LOCK_POLICY = "lock-at-release"` (decision #7 — reproducibility).
  - `LEARNED_DISPATCH_TABLE_PATH` — locked NDJSON path (Phase 8 populates).
  - `PROFILING_INPUT_SIZES_DEFAULT` (6) + `PROFILING_CASCADE_DEPTHS_DEFAULT` (4) + `CASCADE_DEPTH_THRESHOLD_FOR_PATH_B = 3` — supports 1920-cell benchmark grid per decision #3.
- `srmech.signal_processing.cascade_dispatcher` — routing API:
  - `begin_cascade(substrate=None, *, D=8192)` — **context-manager** API per decision #5; auto-flush on exception; thread-local stack; nested cascades supported.
  - `end_cascade(ctx=None)` — imperative-form flush for callers who can't structure around `with`.
  - `current_cascade()` — return innermost active `CascadeContext`.
  - `resolve_path(op_name, *, explicit_path=None, input_size=None, substrate=None)` — Phase 1 rule-based routing (override → cascade-hint Path B → class-default → Path A fallback).
  - `dispatch(op_name, *args, path=None, D=8192, **kwargs)` — Phase 1 stub; raises `DispatchError` for ops without registered implementations.
  - `is_dispatch_table_locked()` / `lock_dispatch_table()` / `unlock_dispatch_table()` — lock-state tracking per decision #7.
  - `DEFAULT_PATH_PER_CLASS` — 14 A-N → default path table (Class K/M default Path B; all others default Path A per plan §3.4).
- `srmech.signal_processing.path_registry` — op-name → (Path-A-impl, Path-B-impl) pairing:
  - `register(op_name, *, path, impl, ssot_citation="", classes=())` — idempotent re-registration; `DuplicateRegistrationError` on differing-callable collision.
  - `lookup(op_name) -> OperationEntry` — raises `UnknownOperationError` for unregistered ops.
  - `has_path(op_name, path)` / `registered_ops()` / `clear_registry()`.
  - `OperationEntry` frozen dataclass with `op_name` / `path_a` / `path_b` / `ssot_citation` / `classes` (14 A–N labels).
- `srmech.signal_processing.profiling` — Phase 8 hook API + data structures:
  - `ProfileCellKey` — Cartesian key (op_name, path, input_size, cascade_depth, substrate) supporting decision #3 full granularity.
  - `ProfileRecord` — NDJSON-serialisable timing record (wall + CPU + memory + n_repeats + notes + extra dict).
  - `cell_grid(*, op_names, ...)` — enumerate the full 1920-cell benchmark sweep grid.
  - `record_profile()` / `iter_records()` / `clear_records()` — in-memory record buffer.
  - `profile_op()` / `update_dispatch_table()` — Phase 8 hooks; Phase 1 raises `ProfilingNotImplementedError`.

### Architectural rationale

Per `[[project_rbs_hdc_loe_dual_path_architecture]]`:

- **Path A** — closed-form algebra (composes existing `srmech.amsc.*` 14-class primitive vocabulary). SSoT for primitive definitions.
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (per Spike #170 anchor). Composes from Path A primitive definitions at module-load time per `[[feedback_no_binding_layer_carveout]]`; no duplicate primitive implementations.
- **Path C** — cascade-aware dispatcher (`cascade_dispatcher`); chooses A or B per call based on rule-based (Phase 5) + empirical (Phase 8) routing. Neither path replaces the other.

The 8 accepted conductor decisions (2026-05-19) framing Phase 1:

1. C port deferred to v0.4.3rc1 (no C surface in Phase 1).
2. Cross-substrate coverage stub-level for all 4 substrates.
3. Profiling granularity full per-op × per-cascade-depth × per-substrate (1920 cells).
4. Spike #179 F4 caveat integrates at Phase 9 §3.8.31.
5. `begin_cascade` API as context-manager (Pythonic; auto-flush on exception).
6. D=8192 lock for v0.4.2 baseline; optional `D` param accepted.
7. Dispatch table lock policy: lock-at-release (reproducibility).
8. Notebook §3.8.31 timing: Phase 9 (after Phase 8 learned thresholds).

### Added — `tests/test_signal_processing_scaffolding.py`

Phase 1 scaffolding verification:

- Imports succeed: `from srmech.signal_processing import begin_cascade, dispatch, register, lookup, ...`.
- D=8192 locked default; optional `D` parameter forwarded by dispatcher.
- `begin_cascade(substrate="bci")` context-manager opens/closes cascade; thread-local stack supports nesting; auto-flush on exception.
- `path_registry.register(...)` / `lookup(...)` / `has_path(...)` round-trip; duplicate-registration with differing callable raises `DuplicateRegistrationError`.
- `profiling.cell_grid(...)` enumerates the 1920-cell benchmark grid for a 10-op suite at default sweeps.
- `profile_op()` + `update_dispatch_table()` raise `ProfilingNotImplementedError` (Phase 8 lands runner).
- `dispatch(op_name, path="verify")` raises `DispatcherNotImplementedError` in Phase 1 (verify-mode lands Phase 5).
- Version is `0.4.2rc1` across `srmech.__version__` + `pyproject.toml` + `pyproject-pure.toml` + `c/include/srmech.h`.

### Canonical SSoT citations per `[[feedback_science_is_ssot_not_project]]`

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.).
- Implementation plan: `docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md` (committed on this branch).

### Spike anchors

- Spike #170 — RBS-HDC instrument feasibility (14/14 mint determinism at D=8192).
- Spike #172 — DNA helical-pitch substrate.
- Spike #173 — chess natural-stride (D2 orthogonality).
- Spike #175 — knowledge-is-gauge-content.
- Spike #176 — rotation IS Class K (machine ε).
- Spike #177 — pin-slot-resonate music-box mechanism.
- Spike #178 — closed-form SP roadmap (§1 surveys ~40 ops across 8 categories).
- Spike #179 — CFSP-Kalman alternative (in flight; Phase 9 integration per decision #4).

### Not added (deferred to Phase 2+)

- Path A closed-form ops (`closed_form_ops/*`) — Phase 2 (v0.4.2rc2) ships 38 ops re-surfacing `srmech.amsc.*` primitives.
- Path B core (`rbs_hdc_instrument.py`, `form_function_rotation.py`) — Phase 3 (v0.4.2rc3) ports Spike #170 prototype.
- Path B per-op MVP — Phase 4 (v0.4.2rc4).
- Full rule-based cascade dispatcher + `path="verify"` semantics — Phase 5 (v0.4.2rc5).
- 7-op extension + remaining 32 Path B ops — Phase 6 (v0.4.2rc6).
- Substrate-natural Class N rational catalogs + cross-substrate verification — Phase 7 (v0.4.2rc7).
- Benchmark suite + learned dispatch table — Phase 8 (v0.4.2rc8).
- Notebook §3.8.31 prose — Phase 9 (documentation-only commit).
- Production tag v0.4.2 → PyPI — Phase 10.
- C port of Path B operations — v0.4.3rc1 (per conductor decision #1).

## [0.4.1rc14] - 2026-05-18

**rcN+1 of the runtime spectral decomposition surface** (Milestone #13). Ships entries 1/2/3/7 of the 7-entry `srmech.spectral.*` namespace per Spike `#115` two-rc strategy (PR #518): `decompose` (Class L+A), `delta` (Class M; Option B per Spike `#114`), `recompose` (Class L+M), `similarity` (Class M). All composition layer; sub-ops route to existing `srmech.amsc.{laplacian, hdc, format}` C primitives. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. rcN+2 (TBD) ships entries 4/5/6 (`predict` / `prediction_error` / `truncate_sparse`) after Spike `#113` + `#117` C primitive landings.

### Added — `srmech.spectral` runtime namespace

- `srmech.spectral.SpectralHandle` — frozen dataclass pairing `substrate_descriptor_hash` (SHA-256 of Laplacian + encoder tag; `laplacian_kind` folds into the hash per Spike `#115` design 2026-05-18) with `coefficients_bytes`, `content_sha`, `n_modes`.
- `srmech.spectral.decompose(state, laplacian, *, encoder_tag="default") -> SpectralHandle` — Class L Hermitian eigendecomposition (via `srmech.amsc.laplacian.hermitian_eigendecompose`) ∘ Class A SHA-256 content addressing. Projects `state` onto eigenbasis, packs to bytes, returns handle. Eigenbasis cached in module-level LRU (`N_MAX_EIGENBASES=8`).
- `srmech.spectral.delta(ref, current) -> bytes` — Class M (HDC bind / XOR self-inverse) per Spike `#114` Option B (direct on already-encoded coefficient bytes; 1.22× faster than wrapper). Accepts `SpectralHandle` or raw `bytes`. Raises if substrate descriptor hashes mismatch between handles.
- `srmech.spectral.recompose(handle, laplacian, *, encoder_tag="default") -> np.ndarray` — inverse eigendecomposition `V @ coeffs` with `content_sha` integrity check on the handle. Bit-exact roundtrip with `decompose` at machine ε (tested at < 10⁻¹²).
- `srmech.spectral.similarity(a, b) -> float` — Class M HDC similarity `1 − 2·hamming(a,b)/D` ∈ `[−1, 1]`. Accepts `SpectralHandle` or raw `bytes`.
- `srmech.spectral.clear_eigenbasis_cache()` — test-isolation utility.
- `srmech.spectral.N_MAX_EIGENBASES` — module-level LRU bound (8).

### Added — `tests/test_spectral.py` (22 tests, all passing)

Bit-exact verification of:
- `decompose` returns valid `SpectralHandle` with stable descriptor hash (independent of state); shape-rejection paths.
- `delta` self-inverse identity `bind(a, bind(a, b)) = b` per Plate 1995 / Kanerva 2009 BSC algebra; commutativity; handle-substrate mismatch rejection.
- `recompose` roundtrip at machine ε (< 10⁻¹²); content_sha + descriptor_hash mismatch rejection.
- `similarity` self-similarity = +1.0; random near-orthogonal in `[−0.2, +0.2]`.
- Cache LRU bounded at `N_MAX_EIGENBASES`; cleared on `clear_eigenbasis_cache()`.
- End-to-end: `state_b coefficients = bind(h_a.coeffs, bind(h_a.coeffs, h_b.coeffs))` bit-exact byte-equal.

### Canonical SSoT citations per `[[feedback_science_is_ssot_not_project]]`

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Golub & Van Loan (2013) *Matrix Computations* (4th ed.), §8.5.

### Spike anchors

- Spike `#112` (PR `#513`) — scoping doc + 7-entry follow-up list.
- Spike `#114` (PR `#514`) — HDC bind delta-encoding identity bit-exact 4/4 substrates; Option B API.
- Spike `#115` (PR `#518`) — 7-entry tool-schema surface design + two-rc strategy.
- Spike `#116` (PR `#516`) — cross-substrate rank-k delta template 3/3 non-chess bit-exact.
- Spike `#117` (PR `#517`) — Class K compression by β band-membership (rcN+2 prereq).
- Spike `#113` (PR `#515`) — predictive-coding cascade Class C∘L (rcN+2 prereq).

### Not added (deferred to rcN+2 — **SHIPPED in v0.4.2rc4**)

The following three operations were originally listed as deferred from rcN+1:

- `srmech.spectral.predict` (Spike `#113` Class C cascade-extrapolate)
- `srmech.spectral.prediction_error` (Class M+K composition; `threshold=0.0` default per user decision 2026-05-18)
- `srmech.spectral.truncate_sparse` (Spike `#117` Class K sparse-truncate + gate-by-threshold)

**Ship status**: All three now shipped in `[0.4.2rc4]` (this document, above) as the MS #14 rcN+2 deliverable per user direction 2026-05-19. Tool-schema entries register at rcN+2 ship time per the original discipline. Implementation is Python-only at v0.4.2rc4; native C ports follow in a later rc per the per-class build-out roadmap.

## [0.4.1rc13] - 2026-05-17

**Task #248 — `pi_cascade_digits` cap expansion (engineering follow-on to PR #468 benchmark).** Per user direction 2026-05-17 ("now I'm curious to know and think we should include in our notes, wall time to return 350 digit pi cascade, partly because it's a weird number on purpose"). The benchmark note in [`docs/srmech/notes/pi_cascade_digits_benchmark_2026-05-17.md`](../notes/pi_cascade_digits_benchmark_2026-05-17.md) surfaced the rc12 hard cap (num_digits ≤ 50 by validation, not by mathematics); rc13 closes that gap with auto-scaled cascade parameters + a 1000-digit ceiling.

### Changed — `pi_cascade_digits` cap raised from 50 to 1000

- `srmech.amsc.rational._PI_CASCADE_MAX_DIGITS`: 50 → 1000.
- `srmech.amsc.rational._PI_CASCADE_MAX_DEPTH`: 90 → 2000.
- New constant `_PI_CASCADE_MAX_PRECISION_BITS = 32768` (was hard-coded 8192 ceiling).
- `pi_cascade_digits(num_digits, *, max_cascade_depth=None, precision_bits=None)` — kwargs default to `None`. When `None`, the function auto-scales via the new `_pi_cascade_auto_params` helper. Existing rc12 callers (no kwargs / explicit defaults of 90 / 512) continue to work unchanged.
- New helper `srmech.amsc.rational._pi_cascade_auto_params(num_digits) -> (depth, precision_bits)` — linear scaling formula derived from the rc12 validated point: `depth = max(90, ceil(num_digits * 90 / 50))`, `precision_bits = max(512, ceil(num_digits * 512 / 50))`. Bit-exact pure-integer arithmetic, AST-clean (no math.pi access).

### Changed — `_integer_sqrt` switched to `math.isqrt` (huge speedup)

- The rc12 implementation used a naive Newton iteration in pure Python. `math.isqrt` (CPython 3.10+) implements an asymptotically-optimal Karatsuba-style integer-floor square root in C; at 20480-bit inputs (D=1000 cascade scale) the speedup is ~2500x.
- `math.isqrt` is NOT a transcendental constant access — the AST gate (which flags `math.pi`, `math.tau`, `numpy.pi`, `np.pi`, `sympy.pi`, `scipy.pi`) is unchanged and still passes. `math.isqrt` is pure-integer arithmetic, fully compatible with `[[user_stance_pi_spectral_shape_scalar_invariant]]` substrate-invariance discipline.
- Without this optimization, num_digits=1000 would take ~24 minutes (extrapolated from naive Newton scaling). With `math.isqrt`, num_digits=1000 takes ~0.7 seconds.

### Added — 6 new rows in `pi_digits/row.ndjson` (12 total)

rc12's catalog at num_digits ∈ {5, 10, 15, 20, 25, 50} extended with rc13 cap-expansion rows at num_digits ∈ {100, 200, 350, 500, 750, 1000}. Each row cross-validated bit-exact against mpmath canonical π reference (the de-facto Python arbitrary-precision π implementation, via Borwein-Borwein 4th-order convergent algorithm). The 350-digit row is the user's "weird number on purpose" probe from PR #468.

Row schema's `num_digits` max widened: 50 → 1000.

### Added — 8 new tests in `tests/test_pi_cascade_primitives.py`

- `test_pi_cascade_digits_350_weird_number_on_purpose` — the deliberate probe value
- `test_pi_cascade_digits_scaling_rc13[num_digits]` — parametrised over {100, 200, 350, 500, 750, 1000}
- `test_pi_cascade_digits_1000_rc13_ceiling` — the new cap ceiling
- `test_pi_cascade_digits_over_rc13_cap_raises` — cap validation
- `test_pi_cascade_digits_auto_params_helper` — pins the auto-scaling formula
- `test_pi_cascade_digits_explicit_kwargs_override_auto` — caller can override
- `test_pi_cascade_digits_ast_no_math_pi_across_rc13_scale` — AST gate survives cap expansion
- Plus `_pi_cascade_auto_params` added to the AST-gate walk in `test_pi_cascade_digits_call_graph_ast_no_math_pi`

New canonical reference `CANONICAL_PI_1000` in both test files (1000 decimal digits, cross-validated against mpmath).

### Added — 3 new tests in `tests/test_pi_digits_catalog.py`

- `test_pi_digits_has_12_rows_rc13` — pins row count at 12 (rc12's 6 + rc13's 6)
- `test_pi_350_digits_canonical_weird_number_probe` — regression-pinned 350-digit row
- `test_pi_1000_digits_canonical_rc13_ceiling` — regression-pinned 1000-digit row
- Existing tests extended: `test_pi_digits_canonical_num_digits_values` widened to all 12 levels, `test_pi_cascade_digits_chain_falsification_all_rows` ratchet bumped from 5 → 12, `test_all_rows_share_canonical_pi_prefix` reference widened from 50 → 1000 digits.

### Wall time (Windows / Python 3.14.4 / fresh-venv)

| num_digits | depth (auto) | prec_bits (auto) | wall time |
|---:|---:|---:|---:|
| 50  | 90   | 512   | ~1 ms   |
| 100 | 180  | 1024  | ~2 ms   |
| 200 | 360  | 2048  | ~10 ms  |
| 350 | 630  | 3584  | **~40 ms** (the user's question) |
| 500 | 900  | 5120  | ~100 ms |
| 750 | 1350 | 7680  | ~310 ms |
| 1000 | 1800 | 10240 | ~700 ms |

The benchmark note's "seconds-range" projection for D=350 was based on the rc12 naive `_integer_sqrt`; the `math.isqrt` switch in rc13 collapses the projection from seconds to milliseconds.

### Test count

- 535 → 549+ passed (full srmech suite; +14 new pi-related tests)
- tool_schema `pi_cascade_digits` ToolEntry summary updated with rc13 cap-expansion note
- JPL Rule 5 audit: no regression (no new C functions; the Python-only cap-expansion + math.isqrt swap don't touch the C surface)
- AST-verification gate: zero `math.pi` invocations across the full call graph including the new `_pi_cascade_auto_params` helper

### C parity

`pi_cascade_digits` stays Python-only per rc12's honest scope decision ([[feedback_no_binding_layer_carveout]]) — the cascade requires bignum integer arithmetic for precision_bits up to 32768 + the long-division step. rc13's expansion of the cap doesn't change that decision; if anything it reinforces it (the precision_bits requirements scale linearly with num_digits, and at 10240 bits the u64 envelope is comfortably exceeded). The Python wrapper around `math.isqrt` IS the C path here — CPython's `math.isqrt` is a C implementation in the interpreter itself.

`continued_fraction_convergents` (the companion Class N primitive shipped in rc12) retains its `srmech_cf_convergents_int64` C surface unchanged.

### Anchored in

- `[[user_stance_pi_spectral_shape_scalar_invariant]]` — the convergent ladder IS π's substrate identity; the decimal expansion is downstream readout. rc13 cap-expansion makes more of the projection visible at the same substrate.
- `[[user_stance_pi_as_projection]]` — π is generated by the cascade-substrate operation
- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises
- `[[feedback_no_binding_layer_carveout]]` — Python-only by honest scope (bignum-required); not a binding-layer carve-out
- Task #248 (this rc) — engineering follow-on to PR #468 benchmark
- PR #468 benchmark note (2026-05-17) — the engineering finding (rc12 caps at 50 by validation) + the scaling projection
- Spike #32 (PR #460) — empirical confirmation across 3 substrates

## [0.4.1rc12] - 2026-05-16

**Task #245 Milestone #4 — π geometric-cascade primitives (cascade output, no `math.pi`).** Per user direction 2026-05-16 — operationalises `[[user_stance_pi_spectral_shape_scalar_invariant]]` (the convergent ladder IS π's substrate identity; the decimal expansion 3.14159... is downstream readout) via two new Class N primitives + a new chain-falsifiable `pi_digits` AMSC catalog. Confirms Spike #32 / PR #460 substrate-invariance result as on-disk falsification infrastructure (second instance of `[[feedback_every_doc_edit_faces_falsification]]` after `asymptotic_calculus`).

### Added — 2 new Class N π geometric-cascade primitives (Python)

- `srmech.amsc.rational.continued_fraction_convergents(coef_list) -> list[tuple[int, int]]` — produces the convergent ladder `[(h_0, k_0), (h_1, k_1), ...]` from a continued-fraction coefficient list via the standard CF recurrence (`h_k = a_k * h_{k-1} + h_{k-2}`). Canonical π CF `[3; 7, 15, 1, 292, 1, ...]` yields canonical convergents `(3, 1), (22, 7), (333, 106), (355, 113), (103993, 33102), ...` per Hardy & Wright §10.6. Pure-Python bignum-capable; C-standalone for int64-fit ladders via `srmech_cf_convergents_int64`.
- `srmech.amsc.rational.pi_cascade_digits(num_digits) -> str` — streams decimal-digit expansion of π via Archimedes hexagon-doubling cascade. Uses integer Newton-Raphson rational √ at fixed `precision_bits` (default 512) over `max_cascade_depth` doublings (default 90). Produces `"3.14159..."` as string. **AST-verified zero `math.pi` invocations** anywhere in the call graph (discipline gate per `[[user_stance_pi_spectral_shape_scalar_invariant]]`).

Bounded caps: 256 CF coefficients (continued_fraction_convergents); 50 digits / depth 90 / 8192 bits (pi_cascade_digits). Substantially larger than any practical use case; both primitives are pure integer arithmetic throughout the call graph.

### Added — C parity for `continued_fraction_convergents`

- `srmech_cf_convergents_int64(coefs, n, out_nums, out_dens)` in `c/src/srmech_rational.c` + header decl in `srmech.h`. ABI v2 pure-addition (no ABI bump). int64-bound n ≤ 256. Returns `SRMECH_ERR_OVERFLOW` when any convergent exceeds int64; Python wrapper falls through to bignum. Two helper functions (`cf_conv_sadd_i64`, `cf_conv_step`) split per JPL Rule 4 (≤60 LOC) with ≥2 asserts per non-exempt function (Rule 5).

`pi_cascade_digits` stays Python-only — the cascade requires bignum integer arithmetic for `precision_bits` ≥ 512 + the long-division step, neither of which fits the JPL-clean u64 envelope of the C primitive surface. Honest scope decision per `[[feedback_no_binding_layer_carveout]]`: every primitive class earns a C surface; bignum-required cases stay Python.

### Added — `srmech.amsc.attested.pi_digits/` chain-falsifiable catalog

First chain-falsifiable π substrate-invariance catalog. Operationalises Spike #32 / PR #460 result (substrate-invariance across triangle / square / hexagon cascades with AST-verified zero math.pi invocations).

- `descriptor.toml` — single-step `pi_cascade_digits` chain calling the Class N primitive.
- `row.ndjson` — 6 self-validating rows at canonical precision levels: num_digits ∈ {5, 10, 15, 20, 25, 50}. Each row's `expected_pi_string` is the bit-exact canonical decimal expansion of π verifiable against Khinchin *Continued Fractions* §10.
- `row.schema.json` — JSON schema for the row data (enforces `expected_pi_string` starts with `"3."`).

Mathematical anchor: π's substrate identity is the cascade-emergent CF convergent ladder per `[[user_stance_pi_spectral_shape_scalar_invariant]]`; the decimal expansion is a downstream readout under continuous-length-metric projection. Catalog rows are the readable artifact backed by the cascade primitive's substrate computation. Source citations: Khinchin *Continued Fractions* §10 (canonical π CF); Hardy & Wright *Theory of Numbers* §10.6 (best-rational convergent property); Archimedes *Measurement of a Circle* c. 250 BCE (hexagon-doubling cascade algorithm).

### Added — `tests/test_pi_cascade_primitives.py` (27 tests, all green)

- Continued-fraction convergents: canonical π convergents (first 6 + full 16), canonical e convergents cross-check, simple-CF edge cases, bignum ladder, input validation
- pi_cascade_digits: 0/5/10/15/20/25/50 digit canonical values, prefix consistency check, input validation, low-depth divergence behavior, default-kwargs consistency
- **AST-verification gate**: three discipline tests confirming zero `math.pi` / `numpy.pi` / `math.tau` (or equivalent) attribute accesses across `pi_cascade_digits`, its private helpers (`_integer_sqrt`, `_scaled_integer_sqrt`), and `continued_fraction_convergents`
- Substrate-readout consistency: 355/113 convergent agrees with `pi_cascade_digits(6)` first 6 digits

### Added — `tests/test_pi_digits_catalog.py` (9 tests, all green)

- Catalog presence + ≥5 rows
- Canonical num_digits coverage (5, 10, 15, 20, 25, 50)
- Chain falsification (bit-exact comparison row-by-row)
- Canonical regression-pinned values (15-digit IEEE-754 boundary, 50-digit bignum-deep)
- All rows are prefixes of canonical π (substrate-invariance documentation)
- Attestation field presence per descriptor's `[attestation]` block

### Test count

- 499 → 535 passed (full srmech suite; +36 new tests)
- tool_schema ToolEntry coverage bumps by 2 (one per new Class N primitive)
- JPL Rule 5 audit: no regression (new C helpers cf_conv_sadd_i64 + cf_conv_step + srmech_cf_convergents_int64 each have ≥ 2 asserts)
- JPL Rule 4: every new C function ≤ 60 lines (cf_conv_step is 16 LOC; srmech_cf_convergents_int64 is 28 LOC)

### Numbering note

rc12 is Milestone #4 closing Task #245 — the π substrate-output primitive shipping. Predecessor rc11 (Milestone #2 Phase 3B) closed transcendental-Taylor inventory. Following rcs continue Task #234 §11 (forward_difference / riemann_sum), Task #218 Phase C2 work, or new milestones per user direction.

### Anchored in

- `[[user_stance_pi_spectral_shape_scalar_invariant]]` — the convergent ladder IS π's substrate identity (this catalog operationalises this stance)
- `[[user_stance_pi_as_projection]]` — older form; ladder vs. decimal is the projection-shadow boundary
- `[[user_stance_identity_not_implementation_discipline]]` — umbrella discipline (π IS the ladder at substrate level; π HAS a decimal expansion at notation level)
- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises (second concrete instance)
- `[[feedback_no_binding_layer_carveout]]` — C surface for continued_fraction_convergents (int64 path); Python-only for pi_cascade_digits (bignum required) is honest scope, not binding-layer carve-out
- Spike #32 (PR #460) — empirical confirmation across 3 substrates with AST-verified zero math.pi

## [0.4.1rc11] - 2026-05-16

**Task #234 Phase 3B — trig + log Taylor primitives (Milestone #2 second ship).** Per user direction 2026-05-16 ("number 2 and 3 in the same milestone, do sequentially and test with testpypi first"). Phase 3A shipped `cosmos_validation` catalog as rc10; Phase 3B adds 4 trig/log Taylor partial-sum primitives + chain specs + rows to the `asymptotic_calculus` catalog. Closes Task #234 §11 inventory's transcendental row.

### Added — 4 new Class N Taylor-series primitives (Python)

- `srmech.amsc.rational.sin_series_truncate(num, den, num_terms) -> (out_num, out_den)` — sin(p/q) = Σ (-1)^k (p/q)^(2k+1) / (2k+1)!
- `srmech.amsc.rational.cos_series_truncate(num, den, num_terms) -> (out_num, out_den)` — cos(p/q) = Σ (-1)^k (p/q)^(2k) / (2k)!
- `srmech.amsc.rational.log1p_series_truncate(num, den, num_terms) -> (out_num, out_den)` — log(1+p/q) = Σ_{k=1} (-1)^(k+1) (p/q)^k / k (caller responsibility: |p/q| < 1 for convergence)
- `srmech.amsc.rational.atan_series_truncate(num, den, num_terms) -> (out_num, out_den)` — atan(p/q) = Σ (-1)^k (p/q)^(2k+1) / (2k+1) (caller responsibility: |p/q| ≤ 1)

Pure Python bignum-capable; uses common-denominator integer accumulation with periodic gcd reduction. Bounded `num_terms` (50 for trig; 64 for log/atan) so the per-row time stays acceptable.

### Deferred — C parity for trig primitives (rc12 candidate)

Per `[[feedback_no_binding_layer_carveout]]` every Class N op earns a C surface. rc11 ships Python-only because the 4 trig primitives use bignum-accumulating Taylor series whose intermediates exceed u64 for typical (x, N) inputs; the C path would need either (a) tight num_terms bounds and OVERFLOW returns on most catalog rows, or (b) multi-precision integer infrastructure in C. Honest scope decision: ship Python-only at rc11; add C parity in rc12 with a documented narrow-bound case (matching what `srmech_exp_series_truncate` already does at u64 limits). Tracked as a follow-on task. The rc8 exp_series_truncate C surface remains the canonical example of C-standalone discipline; rc11 adds 4 surfaces to the same C parity work queue.

### Added — `asymptotic_calculus/descriptor.toml` — 4 new chain specs

- `sin_series_truncate` chain — single Class N step
- `cos_series_truncate` chain
- `log1p_series_truncate` chain
- `atan_series_truncate` chain

Each chain takes `(@row.x_num, @row.x_den, @row.num_terms)` and returns `(out_num, out_den)` exact rational. Row schema's `kind` enum widened from `["exp"]` to `["exp", "sin", "cos", "log1p", "atan"]`.

### Added — 16 new self-validating rows in row.ndjson

Per-op rows covering canonical inputs:
- sin: x=0, 1/6 (~30°), 1/4 (~14°), 1 rad
- cos: x=0, 1/6, 1/4, 1 rad
- log1p: x=0, 1/10, 1/4, -1/4
- atan: x=0, 1/4, 1/2, 1 (~π/4)

Each row's `(expected_num, expected_den)` computed bit-exactly by running the new Python op at catalog-author time.

### Test count

- 482 → 484 passed (full srmech suite); `tests/test_asymptotic_calculus_catalog.py::test_exp_series_truncate_chain_falsification_all_rows` expanded to dispatch by `kind` and bit-exact-compare each row across all 5 chain types
- tool_schema ToolEntry coverage ratchet bumps by 4

### Numbering note

This is the second rc in Milestone #2. Phase 3A (cosmos_validation catalog, rc10) shipped first per user direction "do sequentially". rc11 closes the trig-primitive portion of Task #234 §11. Future rc12 ships C parity for the 4 trig primitives + adds calculus operators (forward_difference, riemann_sum) per Task #234 §11 inventory.

### Anchored in

- `[[feedback_every_doc_edit_faces_falsification]]` — discipline
- Task #234 §11 inventory — scope (sin / cos / tan / log / atan / sinh / cosh / Bessel / Γ / ζ / forward_difference / riemann_sum)
- User direction 2026-05-16 Milestone #2 — "do sequentially and test with testpypi first"

## [0.4.1rc10] - 2026-05-16

**Task #234 Phase 3A — `cosmos_validation` catalog ship (Spike #27 / PR #437 Q6.1 falsification infrastructure).** Per user direction 2026-05-16 (Milestone #2: "Task #234 — asymptotic_calculus expansion: cosmos_validation + trig primitives"). First instance of the milestone's pattern: a chain-falsifiable cosmology catalog using only existing Class N rational primitives plus 4 new rational arithmetic ops with Python + C parity.

### Added — Class N rational arithmetic primitives (4 new ops with full C/Python parity)

- `srmech.amsc.rational.rational_add(a, b) -> (num, den)` — add two rationals, reduced.
- `srmech.amsc.rational.rational_mul(a, b) -> (num, den)` — multiply two rationals, reduced.
- `srmech.amsc.rational.rational_div(a, b) -> (num, den)` — divide two rationals, reduced; raises ZeroDivisionError on b_num=0.
- `srmech.amsc.rational.rational_pow_uint(base, exp) -> (num, den)` — raise rational to non-negative integer exponent; exp ≤ 64.

All four take tuple inputs `(p, q)` for clean chain composition via Phase 2 v1 list-resolution in `compose._resolve_args`. C surfaces: `srmech_rational_add` / `srmech_rational_mul` / `srmech_rational_div` / `srmech_rational_pow_uint` in `c/src/srmech_rational.c` + header decls in `srmech.h` + ctypes bindings in `_native.py`. Each Python wrapper dispatches to C when inputs fit u64; falls through to bignum on OVERFLOW or missing-symbol. Per `[[feedback_no_binding_layer_carveout]]` the C library is usable standalone for u64-fit inputs. JPL Power-of-Ten clean: helpers split per Rule 4 (≤60 LOC), ≥2 asserts per function (Rule 5).

### Added — `srmech.amsc.attested.cosmos_validation/` catalog

First chain-falsifiable cosmology catalog. Operationalises Spike #27 / PR #437 Q6.1 dark-sector monotonicity claim (concertmaster's PR #437 audit recommendation 1).

- `descriptor.toml` — 9-step `friedmann_dark_fraction` chain composing rational_pow_uint (1) + rational_mul (3) + rational_add (4) + rational_div (1).
- `row.ndjson` — 11 self-validating rows: Planck-canonical Ω values (Ω_b = 49/1000, Ω_c = 265/1000, Ω_Λ = 685/1000, Ω_r = 1/10000) + scale-factor a across z ∈ [-0.9, ~10⁵]. Each row stores expected `f_dark(a)` rational; CI runs the chain and bit-exact-compares.
- `row.schema.json` — JSON schema for the row data.

Mathematical claim: `f_dark(a) = (Ω_c·a + Ω_Λ·a⁴) / (Ω_b·a + Ω_c·a + Ω_Λ·a⁴ + Ω_r)`. Q6.1 monotonicity: f_dark(a) strictly increases in a — verified bit-exact across the 11 rows (0.026 at a=1/100000 → 0.951 at a=1 → 0.99993 at a=10). Source: Planck Collaboration 2018 VI (Aghanim et al. 2020, A&A 641:A6, doi:10.1051/0004-6361/201833910, arXiv:1807.06209) per `[[feedback_pdf_extraction_citation_discipline]]`.

### Added — `tests/test_cosmos_validation_catalog.py` (9 tests, all green)

- Catalog presence + row count
- Chain bit-exact falsification (all 11 rows)
- **Q6.1 monotonicity test**: sorts rows by a, asserts strict-increase across all consecutive pairs
- Unit tests for each new rational op
- Canonical pin: f_dark(a=1) = 9500/9991

### Added — tool_schema entries for the 4 new rational ops

Coverage ratchet bumps; each op cites Class N's rational-approximation primitive role.

### Numbering note

This rc10 builds on the rc1-rc9 sprint that shipped in `0.4.1rc9` (merged to main via PR #447). It is the first rc in Milestone #2 (Task #234 — asymptotic_calculus expansion). Subsequent rc11 will add sin/cos/log/atan trig primitives (Phase 3B per user direction "do sequentially and test with TestPyPI first").

### Anchored in

- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises
- `[[feedback_no_binding_layer_carveout]]` — every new Class N op gets a C surface
- `[[user_stance_pi_as_projection]]` + `[[user_stance_kepler_shape_universal]]` + `[[user_stance_asymptotic_dof_sidesteps_infinity]]` + `[[user_stance_epicycle_via_gear_plus_pin]]` — the stance family
- Spike #27 / PR #437 Q6.1 monotonicity claim (concertmaster audit reproduced 9999/9999 positive slopes; this catalog ships the analytic proof as 11 bit-exact rows)

## [0.4.1rc9] - 2026-05-16

**Hotfix: asymptotic_calculus row attestation field.** The rc8 fresh-venv TestPyPI smoke surfaced that `catalog.get_attested_dataset("asymptotic_calculus")` failed at row-parse time because the literature_curated adapter requires every row to carry a `source_published_date` field for per-row attestation. The rc8 row.ndjson had `source_apostol` + `source_bishop` references but not the explicit publication date.

### Fixed
- All 12 rows in `srmech.amsc.attested.asymptotic_calculus/row.ndjson` now carry `source_published_date = "1974-01-01"` (Apostol *Mathematical Analysis* 2nd ed. publication; the citation pinned for the convergence claim per Theorem 12.20).
- `srmech.amsc.attested.asymptotic_calculus/row.schema.json` adds `source_published_date` to its required-fields list + properties (ISO 8601 date format).

### Behaviour impact
- `bridge.get_attested_dataset("asymptotic_calculus", limit=N)` returns rows cleanly.
- `bridge.attestation_audit("asymptotic_calculus")` resolves per-row attestation hashes.
- Python `srmech.amsc.rational.exp_series_truncate(...)` and the C path `srmech_exp_series_truncate(...)` unchanged from rc8.

This is a 12-row + 1-schema-line patch; no C code or Python primitive changes.

## [0.4.1rc8] - 2026-05-16

**Spike #28 ship — asymptotic_calculus catalog + Class N `exp_series_truncate` with C parity (re-versioned from rc6).** Originally drafted as rc6 on PR #447's branch; renumbered to rc8 after PR #439's rc7 chain-spec hotfix merged to main between the two PRs. The underlying ship is identical (asymptotic_calculus catalog, `exp_series_truncate` op, math addendum + chain-spec form + scope inventory) plus the **C parity surface** that was deferred at rc6 ship and now lands on top per `[[feedback_no_binding_layer_carveout]]` — the C library is usable standalone, no Python required.

### Added — Class N op `exp_series_truncate` with full C/Python parity

- **Python** `srmech.amsc.rational.exp_series_truncate(numerator, denominator, num_terms) -> (out_num, out_den)` — computes the exp Taylor partial sum `S_N(p/q) = sum_{k=0..N} (p/q)^k / k!` as an exact rational in lowest terms. Composes:
  - **Class N** rational-approximation: numerator/denominator tracking + gcd reduction
  - **Class J** integer factorial: `k!` as running integer product
  - **Class I** integer arithmetic: power accumulators `p^k`, `q^k`
  - Pure integer arithmetic at every step; arbitrary-precision via Python int for N ≤ 512.
- **C** `srmech_exp_series_truncate(int64_t x_num, uint64_t x_den, uint32_t num_terms, int64_t *out_num, uint64_t *out_den) -> srmech_status_t` — same op as the Python surface, bounded to `num_terms ≤ 20` (factorial fits u64); returns `SRMECH_ERR_OVERFLOW` when intermediate computation would exceed u64 range. The Python wrapper dispatches to C when inputs fit safe bounds, falls back to bignum Python when they don't. **The C library compiles and runs standalone — no Python interpreter required for the catalog-row-shaped inputs (x ∈ {0, ±1/2, ±1, ±2}, N ∈ {5, 10, 15} all fit u64 comfortably).**
- Canonical SSoT: Apostol *Mathematical Analysis* 2nd ed. Theorem 12.20 (Lagrange remainder); Bishop *Foundations of Constructive Analysis* §2 (asymptotic-rate framing). Both cited per `[[feedback_pdf_extraction_citation_discipline]]`.

### Added — `srmech.amsc.attested.asymptotic_calculus/` catalog

First concrete instance of the doc-claim falsification infrastructure (per `[[feedback_every_doc_edit_faces_falsification]]`):

- `descriptor.toml` — single-step Phase 2 v1 chain spec `exp_series_truncate` calling Class N `exp_series_truncate` op with `@row.x_num`, `@row.x_den`, `@row.num_terms` inputs.
- `row.ndjson` — 12 self-validating rows: x in {0, ±1/2, ±1, ±2} at N in {5, 10, 15}; each row carries (x_num, x_den, num_terms) input plus (expected_num, expected_den) bit-exact ground-truth output.
- `row.schema.json` — JSON schema for the row data.

Future rcs (Task #234) expand the catalog to cover sin, cos, tan, log, atan, Bessel, Γ, ζ partial sums + calculus operations (forward-difference, Riemann sum, continued-fraction convergent). Each new operation lands as a new Class N op (Python + C surface) + new chain spec + new row data.

### Added — `tests/test_asymptotic_calculus_catalog.py` (7 tests, all green)

The falsification test runs the chain for every catalog row and bit-exact compares the produced output to the row's stored expected output. Any drift in Class N + Class J primitives surfaces as immediate row-by-row test failure. Includes regression-pinned canonical exemplars: `S_10(1) = 9864101/3628800` (Spike #28 §9 V4 canonical exemplar) + `S_N(0) = 1/1` (trivial-input pin). Plus C/Python parity test (new at rc8): C path matches Python path bit-exact for `num_terms ≤ 20` inputs.

### Added — tool_schema coverage for `exp_series_truncate`

ToolEntry registered in `srmech.amsc.tool_schema` under `category="rational"`; coverage ratchet bumps from previous floor.

### Numbering note

- rc6 — drafted on PR #447's branch (commit `8887368` historical); renumbered to rc8 at rebase time. Not tagged on TestPyPI.
- rc7 — PR #439's chain-spec hotfix (merged to main). Tagged + published; removes 4 Phase 1 worked-example chains from cosmos catalogs (see rc7 entry below).
- rc8 — this rebase carries PR #447's content forward + adds C parity for `exp_series_truncate` per `[[feedback_no_binding_layer_carveout]]`.

### Anchored in

- Spike #28 working note: [`docs/antikythera-maths/research-mfo/asymptotic_vs_infinity_history_2026-05-16.md`](../../../antikythera-maths/research-mfo/asymptotic_vs_infinity_history_2026-05-16.md) — §9 falsification math (V1-V4), §10 canonical chain-spec form, §11 catalog scope inventory
- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises
- `[[feedback_no_binding_layer_carveout]]` — C-standalone contract honoured by rc8's C surface
- `[[user_stance_pi_as_projection]]` + `[[user_stance_kepler_shape_universal]]` + `[[user_stance_asymptotic_dof_sidesteps_infinity]]` + `[[user_stance_epicycle_via_gear_plus_pin]]` — the upstream stance family this catalog instantiates operationally

## [0.4.1rc7] - 2026-05-16

**Spike #28 ship — falsification-discipline pre-merge hotfix.** Removes the four Phase 1 worked-example chain specs from the cosmos catalogs because they reference primitives that don't yet exist (their chains list cleanly but fail at activate-time when actually run). Per `[[feedback_every_doc_edit_faces_falsification]]` (user direction 2026-05-16: *"our model has not lied to us yet, so I believe the math still"*) we do not ship chain specs whose underlying primitives can't run — chains that cannot execute are claims that cannot falsify. Surfaced via the rc5 fresh-venv TestPyPI smoke (Class D `match_filter`, Class E `sorted_lookup_extract` + `sorted_lookup_batch`, Class L `spherical_harmonic_decompose` + `extract_preferred_axis`, Class I `angular_separation_axes` all missing). Each chain re-lands as its underlying primitive ships — `spherical_harmonic_decompose` is Spike #26 Phase 2 scope (Task #227); `angular_separation_axes` is Task #234 §11 inventory (`cmb_angular_geometry` sister catalog with rc7+ sin/cos). The DSL design pattern lives in `docs/srmech/adr/0002-phase-1-operator-chain-schema.md` for reference.

### Changed — cosmos catalog chain specs removed

- `srmech/amsc/attested/cmb_low_ell_maps/descriptor.toml`: removed `multipole_vector_axis` (LLDA) and `t_vs_e_axis_differential` (LLLLI) chain specs.
- `srmech/amsc/attested/cmb_polarisation_spectra/descriptor.toml`: removed `acoustic_peak_locations` (CDE) chain spec.
- `srmech/amsc/attested/cmb_bispectrum/descriptor.toml`: removed `f_NL_template_combination` (ENA) chain spec.
- All three descriptors retain `[catalog].chain_schema_version = 1` so re-adding chains later does not require reintroducing the `[catalog]` section. Inline deprecation comments document what was removed and which Task # tracks the re-add.

### Behaviour impact

- `srmech.amsc.catalog.list_catalog_chains(<cosmos_catalog>)` now returns `{"ok": True, "source_key": ..., "n_chains": 0, "chains": []}` for each of the three affected catalogs. Pre-rc7 it returned `n_chains=1` or `n_chains=2` but `run_catalog_chain` would then raise `ChainSpecError` at activate time. The rc7 behaviour is strictly more honest: empty chain list reflects empty executable surface.
- All other rc5 functionality intact: cosmos catalog data rows + chain schema infrastructure + composition engine + Class L broadening + tool_schema coverage.
- `cmb_lensing` catalog never had chain specs and is unaffected.

### Test

`test_compose.test_parse_catalog_chains_cosmos_descriptors_have_no_executable_chains` pins `n_chains == 0` across all 3 cosmos catalogs at rc7.

## [0.4.1rc5] - 2026-05-16

**ADR-0002 Phase 2 — Class L broadening + composition engine + notebook updates.** Implements the Phase 1 spike's dissolve-into-Class-L proposal per `[[feedback_no_privileged_primitive_classes]]`. Class L's identity broadens from "graph Laplacian" to "dense-matrix linear algebra including eigendecomposition + matrix-vector multiplication + elementwise operations"; the graph-Laplacian-specific ops become specialisations. Adds the operator-chain composition engine (`srmech.amsc.compose`) implementing schema v1 from the Phase 1 ADR doc, with linear pipeline execution + 4-namespace reference DSL (`@row.* / @input.* / @step[N].output / @catalog.*`) + chain-level and per-step error policy. Engine integration with the catalog bridge: `list_catalog_chains(source_key)` and `run_catalog_chain(source_key, chain_name, row_index, inputs)`. **Vocabulary stays at 14 classes A–N; no Class P promoted.**

### Added — Class L broadening (4 new ops, full C + Python parity)

Each new op cites canonical physics literature per `[[feedback_science_is_ssot_not_project]]`:

- `srmech.amsc.laplacian.hermitian_eigendecompose(H) -> (eigvals, V)` — complex Hermitian generalisation of `jacobi_eigvals`. Returns ascending eigenvalues + unitary eigenvectors. Native C path via `srmech_hermitian_eigendecompose` (complex-Jacobi rotations with algebraic phase factor `e^(iφ) = γ/|γ|`; pi-free, atan2-free, n ≤ 256). Numpy fallback via `np.linalg.eigh`. Canonical SSoT: Golub & Van Loan *Matrix Computations* (4th ed., 2013) §8.5.
- `srmech.amsc.laplacian.dense_matvec_complex(M, v) -> M @ v` — general complex matrix-vector multiplication. Native C path via `srmech_dense_matvec_complex`; numpy fallback. Canonical SSoT: Golub & Van Loan §1.1.
- `srmech.amsc.laplacian.elementwise_multiply_complex(a, b) -> a * b` — vectorised pointwise complex multiply with broadcasting. Native C path; numpy fallback.
- `srmech.amsc.laplacian.elementwise_transcendental(arr, op_name)` for `op_name ∈ {"exp", "cos", "sin", "log", "exp_i"}`. Array-vectorised transcendentals over real input; `exp_i(x) = exp(1j * x)` (TDSE-relevant complex exponential) realised in Python as `cos + i*sin` over the real argument via two C calls. Canonical SSoT: ANSI C99 §7.12 libm.

The `LAPLACIAN_OPS` module-level constant exposes all 8 op names (4 original + 4 new) for the composition-engine registry.

### Added — composition engine (`srmech.amsc.compose`)

- `ChainSpec` dataclass mirroring the TOML `[[catalog.operator_chain]]` schema.
- `StepSpec` dataclass mirroring `[[catalog.operator_chain.steps]]` entries.
- `parse_chain_spec(chain_dict)` — schema-v1 validation; rejects malformed reference syntax, unknown class identifiers, out-of-bounds `@step[N]` references, illegal `on_error` values, empty step lists.
- `parse_catalog_chains(toml_dict)` — parses all chains in a descriptor TOML; requires `[catalog].chain_schema_version = 1`.
- `resolve_chain(spec, registry)` — binds each step's `class.op` against `DEFAULT_CLASS_REGISTRY` (covers all 14 classes A–N); raises `ChainSpecError` on missing op at activation time.
- `run_chain(spec, *, row, inputs, registry)` — top-level executor; linear pipeline; error policy (raise / warn_return_none / skip-NYI-for-single-call).
- 4-namespace reference DSL resolution at runtime: `@row.<path>`, `@input.<name>`, `@step[N].output[.<path>]`, `@catalog.<row_key>.<col>`.

### Added — catalog bridge integration

- `srmech.amsc.catalog.list_catalog_chains(source_key)` returns `{ok, source_key, n_chains, chains}` where each chain has `{name, summary, returns, on_error, n_steps, classes}`. ADR-0002 Phase 2 bridge surface.
- `srmech.amsc.catalog.run_catalog_chain(source_key, chain_name, *, row_index, inputs)` executes the named chain with optional row binding. Phase 1's 4 worked-example chains across 3 cosmos catalogs are now invocable via this bridge.

### Added — C surface

- `srmech_hermitian_eigendecompose(n, H_il, eigvals, V_il)` — complex Hermitian eigendecomposition via complex-Jacobi rotations. Pi-free, atan2-free; complex numbers travel as interleaved-double pairs (re, im, re, im) on the FFI boundary. Bounded by `SRMECH_LAPLACIAN_MAX_NODES` = 256.
- `srmech_dense_matvec_complex(rows, cols, M_il, v_il, out_il)` — complex matvec.
- `srmech_elementwise_multiply_complex(n, a_il, b_il, out_il)` — pointwise complex multiply.
- `srmech_elementwise_transcendental(n, arr, op_id, out)` — real transcendental dispatcher; op_id enum `SRMECH_TRANS_{EXP,COS,SIN,LOG}` in `srmech.h`.

**ABI version stays at v2** — additive symbol additions don't break the wire contract. JPL Power-of-Ten audit clean: each new function ≤ 60 lines, ≥ 2 assertions, no goto, no malloc, no unbounded loops.

### Added — tool-schema entries (10 new entries)

- `srmech.amsc.laplacian.{hermitian_eigendecompose, dense_matvec_complex, elementwise_multiply_complex, elementwise_transcendental}` — Class L broadening.
- `srmech.amsc.catalog.{list_catalog_chains, run_catalog_chain}` — bridge surfaces.
- `srmech.amsc.compose.{parse_chain_spec, parse_catalog_chains, resolve_chain, run_chain}` — engine surfaces.

Tool-schema coverage ratchet (`tests/test_tool_schema_coverage.py`) continues green.

### Added — tests (39 new test cases)

- `tests/test_laplacian_class_l_broadening.py` (18 tests): parity with numpy for all 4 new ops; Hermitian eigendecomposition convergence + unitarity + 2×2 Pauli-Y reference; `LAPLACIAN_OPS` registry coverage; **end-to-end TDSE composition test** (`hermitian_eigendecompose` → `dense_matvec_complex` → `elementwise_transcendental("exp_i")` → `elementwise_multiply_complex` → `dense_matvec_complex`) verified against reference path to 1e-10 with norm preservation.
- `tests/test_compose.py` (21 tests): schema validation; reference DSL namespace resolution; linear pipeline threading; error policy; catalog-level chain parsing including the 4 real Phase 1 cosmos chains end-to-end.

Full suite: **547 passed** (508 pre-Phase-2 + 39 new).

### Documentation

- `docs/srmech/srmech_research_notebook.md` §3.8.3 added — Class L broadening rationale, the 4 new ops with canonical SSoT citations, dissolve-vs-promote framing per `[[feedback_no_privileged_primitive_classes]]`. Cross-references to ADR-0002 Phase 1 schema doc and Phase 1 report.
- `docs/antikythera-maths/mfo_spectral_research_notebook.md` §VIII.6.1 — added "Closure-validation observation #2 — ADR-0002 Phase 1 TDSE spike" paragraph noting the second affirmative closure-validation (after Phase C1's QM/QFT/SM ops layer landing without new primitives). The closure conjecture (14 primitives suffice) now stands at two independent positive verifications.
- `docs/srmech/python/CHANGELOG.md` — this entry.

### Notes

- Per `[[feedback_no_binding_layer_carveout]]`: Class L's broadening earns its full C surface (4 new symbols + ctypes bindings), not Python-only.
- Per `[[feedback_no_mvp_framing]]`: rc5 covers the full Phase 2 surface (Class L broadening + composition engine + catalog integration + tests + notebook updates), not a Phase-2a-then-Phase-2b carve-out.
- Per `[[feedback_rc_stacking_versioning]]`: rc5 stacks on the active 0.4.1 cosmos-catalog sprint on `feat/srmech-cosmos-catalog`; clean 0.4.1 ships when sprint concludes.
- Phase 2 open questions (branching / chain-level iteration / cross-source reduction / auto-derived tool-schema parameter types / versioned op evolution) remain Phase 2-v2 scope per Phase 1 §11.

## [0.4.1rc4] - 2026-05-16

**ADR-0002 Phase 1 — operator-chain DSL design + worked-example specs + spike.** Formalises the descriptor TOML operator-chain DSL sketched in ADR-0002 §3. Schema v1 candidate lands as a new ADR Phase 1 document; four worked-example chains land across three of the four cosmos catalogs (`cmb_low_ell_maps` × 2, `cmb_polarisation_spectra` × 1, `cmb_bispectrum` × 1); the spike — closed-form TDSE evolution from `srmech.qm.single_particle.tdse_evolve` — surfaces a Class L scope-broadening question with a clean dissolve-into-existing-class proposal per `[[feedback_no_privileged_primitive_classes]]`. The vocabulary stays at 14 classes A–N; no new primitive class promoted.

### Added — schema v1 documentation

- `docs/srmech/adr/0002-phase-1-operator-chain-schema.md` (~330 lines): formalised schema specification resolving 7 design concerns from the conductor's Phase 1 brief.
  - Step shape: `class` + `op` + `args` (+ optional per-step `on_error`). Closed shape.
  - Data flow: linear pipeline with explicit `@step[N].output` references. No implicit threading. No DAG / branching in v1.
  - Input binding: reference DSL with four namespaces (`@row.X`, `@input.X`, `@step[N].output`, `@catalog.<key>.<col>`).
  - Return shape: typed string `"<type>  # <comment>"` parseable via `typing` utilities.
  - Error policy: default `raise`; opt-in `warn_return_none` / `skip`.
  - Versioning: required `[catalog].chain_schema_version = 1` when chains declared.
  - Reference DSL grammar formalised; engine validates at chain activation.
- Includes a JSON Schema (`srmech.amsc.operator_chain.v1`) for descriptor validation pipelines.

### Added — four worked-example chains

| Catalog | Chain | Classes | Steps | Purpose |
|---|---|---|---|---|
| `cmb_low_ell_maps` | `multipole_vector_axis` | L + L + D + A | 4 | de Oliveira-Costa 2004 §III axis extraction at fixed ℓ |
| `cmb_low_ell_maps` | `t_vs_e_axis_differential` | L + L + L + L + I | 5 | §VII.6.3.1 falsifiable Δθ_TE prediction (predicted 1.0°–2.0°; threshold < 0.1°) |
| `cmb_polarisation_spectra` | `acoustic_peak_locations` | C + D + E | 3 | TT/TE/EE peak enumeration via NDJSON stream + multi-needle dispatch + sorted extract |
| `cmb_bispectrum` | `f_NL_template_combination` | E + N + A | 3 | Joint rational-form bound across the 3 primordial bispectrum templates |

All four chains parse cleanly via `python -m tomllib`; canonical SSoT citations per chain (Planck 2018 IV / V / IX) all PDF-extraction-verified per `[[feedback_pdf_extraction_citation_discipline]]`.

**TOML-syntax note:** the original ADR-0002 §3 sketch used multi-line inline-table arrays (`steps = [ { ... }, { ... } ]`) which the TOML spec forbids. The Phase 1 canonical form lifts each step to its own `[[catalog.operator_chain.steps]]` array-of-tables entry; same semantic content, valid TOML, tomllib-round-tripped. The schema doc §2 documents the correction.

### Spike — closed-form TDSE evolution surfaces Class L scope question

The spike calculation `srmech.qm.single_particle.tdse_evolve(H, ψ, t) = V·diag(exp(-iλt))·V^H·ψ` (Sakurai §2.1.5 eq 2.1.40) decomposes to 5 conceptual steps: Hermitian eigendecompose + change-of-basis ψ→eigenbasis + elementwise `exp(-iλt)` + elementwise multiply + change-of-basis back. Step 0 fits Class L (with complex-Hermitian generalisation of existing real-symmetric `jacobi_eigvals`); steps 1, 3, 4 (complex matvec, elementwise multiply) and step 2 (elementwise transcendental over complex array) do NOT cleanly fit any existing A–N class op.

**Proposed Phase 2 refinement** (per `[[feedback_no_privileged_primitive_classes]]` dissolve-before-promote):
broaden Class L's identity from "graph Laplacian" to "dense-matrix linear algebra including eigendecomposition + matvec + elementwise operations". New Class L ops in Phase 2:
- `hermitian_eigendecompose(H)` — complex-Hermitian generalisation
- `dense_matvec_complex(M, v)` — general complex matvec
- `elementwise_multiply_complex(a, b)` — vectorised pointwise
- `elementwise_transcendental(arr, op_name)` — array-vectorised `exp`/`cos`/`sin`/etc.

Class L's existing graph-Laplacian-specific ops (`dense_laplacian`, `normalized_laplacian`) become specialisations of the broader dense-matrix scope. No new primitive class promoted; vocabulary stays at 14 classes A–N.

### Added — Phase 1 report

- `docs/srmech/notes/adr_0002_phase_1_dsl_design_2026-05-16.md` (~290 lines): consolidated design decisions + worked-example overview + spike write-up + open questions for Phase 2.

### No code change; no C ABI change; no Python API change

- C ABI v2 unchanged.
- No new C symbols. No JPL audit pin changes.
- No `srmech.amsc.<class>` Python surface changes.
- No `srmech.qm.*` operation changes.
- Schema is data-only addition to descriptor.toml; no Python composition-engine code yet (Phase 2 scope).

### Versioning

`0.4.1rc3` → `0.4.1rc4`. Sprint-level rc-stacking per `[[feedback_rc_stacking_versioning]]`, not a separate ship. Cumulative cosmos catalog sprint accumulates: rc1 (3-catalog data layer + framework precedent) + rc2 (`read_ndjson` framework fix) + rc3 (cmb_low_ell_maps catalog #4) + rc4 (this — ADR-0002 Phase 1 schema + 4 chains + spike). Clean `0.4.1` ships when sprint accumulates everything the cosmos catalog research thread + ADR-0002 Phase 1 implementation prep needs.

## [0.4.1rc3] - 2026-05-16

**Cosmos catalog extension — Spike #26 Phase 1 data layer folded into the 0.4.1 sprint.** Adds the fourth srmech-primary cosmos catalog source, `cmb_low_ell_maps`, providing metadata for Planck PR3 component-separated full-sky CMB maps (Commander / NILC / SEVEM / SMICA) + common-mask products. Phase 2 (the analysis script) will fetch the FITS bytes via the catalog URLs and compute T-mode + E-mode a_ℓm coefficients for multipole-vector AoE-direction extraction; the framework prediction Δθ_TE ≈ 1°–2° from §VII.6.3.1's 138°/unit-f_RD bundle-projection-reconfiguration rate × Δf_RD across the T-vs-E recombination visibility window will be tested against observation.

### Added — `cmb_low_ell_maps` attested source

7 rows of provenance metadata (4 sky-map FITS + 3 mask products) at `srmech/amsc/attested/cmb_low_ell_maps/`. FITS bytes are not committed (each map is ~168 MB; 672 MB total exceeds git's reasonable storage envelope); Phase 2 fetches via the per-row `source_url` field from PLA's HTTP CDN (`pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=...`) which serves Planck data per ESA's Open Access policy without authentication.

**Canonical citations** (PDF-extraction verified per `[[feedback_pdf_extraction_citation_discipline]]`):
- Planck 2018 IV (diffuse component separation): [arXiv:1807.06208](https://arxiv.org/abs/1807.06208), A&A 641 A4
- Planck 2018 VII (isotropy + statistics): [arXiv:1906.02552](https://arxiv.org/abs/1906.02552), A&A 641 A7

### Placement decision (rc3 only — not a framework change)

Per user directive on the MFO/AoE research line — *"MFO and srmech ship as one, because it demonstrates every class operator"* — the new `cmb_low_ell_maps` catalog is placed in **srmech** (`srmech/amsc/attested/`), matching the rc1 cosmos catalog precedent (`cmb_polarisation_spectra` + `cmb_bispectrum` + `cmb_lensing`). The Spike #26 Phase 1 concertmaster initially placed the catalog in ephemerides-spectral for cmb-family co-location; reworked here to align with rc1's placement and the user's "MFO + srmech ship as one" directive. Future migration of all cosmos catalogs to ephemerides-spectral remains the eventual plan once MFO matures and earns its own scope.

### Companion research note (separate path)

Phase 2 scope artifact at `docs/antikythera-maths/research-mfo/vii_6_3_1_prediction_verification_scope_2026-05-16.md` (171 lines): multipole-vector extraction algorithm (de Oliveira-Costa 2004), visibility-function modelling for T-vs-E recombination Δz, predicted differential trajectory across Δz ∈ [10, 50] (range 0.67° → 3.4°; central 1.0°–2.0°), falsifier threshold Δθ_TE < 0.1°. Lives in `research-mfo/` alongside the dark-sector + AoE working notes.

### No code change; no ABI change; no Python API change

- C ABI v2 unchanged.
- No new C symbols, no new Python catalog modules, no new tool_schema entries.
- Data-only addition + research-note artifact + version bump (4 SSOT files + CHANGELOG).

### Versioning

`0.4.1rc2` → `0.4.1rc3`. Cumulative rc-stack on the 0.4.1 cosmos catalog sprint per `[[feedback_rc_stacking_versioning]]`. Sprint accumulates: rc1 (cosmos catalog data layer + framework precedent for srmech-primary catalogs) + rc2 (`read_ndjson` skips `#` comments framework fix) + rc3 (this — fourth catalog source). Clean `0.4.1` ships to production once the sprint accumulates everything the cosmos-catalog research thread needs.

## [0.4.1rc2] - 2026-05-16

**Framework bug fix — `read_ndjson` now skips `#` comment-header lines.** Found during the rc1 TestPyPI smoke verify when `catalog.attestation_audit` failed on the new `cmb_polarisation_spectra/row.ndjson`. Investigation confirmed the bug **pre-exists in production srmech 0.4.0** and affects every `#`-comment-prefixed NDJSON across the spectral-research portfolio — including ephemerides-spectral 0.29.x's already-shipped `cmb_anomalies` + `cmb_power_spectrum` catalogs. `catalog.get_attested_dataset` was comment-aware via a different code path; `catalog.attestation_audit` calls `read_ndjson` directly and was choking on the leading `# CMB ... catalogue` header.

### Fixed — `format.read_ndjson` skips `#` lines + empty lines uniformly

- **Pure-Python path** (`format.py:286–296`) now skips lines that match `not line or line.startswith("#")` after stripping whitespace.
- **Native path** (`format.py:266–283`) now decodes each line, lstrips whitespace, and skips empty + `#`-prefixed lines before calling `MPRRecord.from_json_line`. Indented comments (leading whitespace before `#`) are also tolerated.
- New ratchet test `test_format.test_ndjson_skips_hash_comment_lines` pins the behaviour across both paths.

This restores `attestation_audit` parity with `get_attested_dataset` for all `#`-comment-prefixed NDJSON catalogs.

### Versioning

`0.4.1rc1` → `0.4.1rc2`. Patch bump on the cosmos catalog sprint. Cumulative rc-stack per `[[feedback_rc_stacking_versioning]]`; clean `0.4.1` ships to production after rc2 TestPyPI verify covers both the cosmos catalog content (rc1) and the framework fix (rc2).

## [0.4.1rc1] - 2026-05-16

**Cosmos catalog ship rc1.** Seeds three new srmech-primary attested AMSC sources covering the Planck 2018 PR3 CMB observables that downstream MFO research needs as ground-proof anchors. Per user directive on the AoE/dark-sector research line (PR #437 + the four-turn dialog landed in MFO §VII.6.2/.6.3): cosmos catalog lives in srmech for now (MFO + srmech ship as one demonstrates every primitive class operator); future migration to ephemerides-spectral is later scope.

### Added — three attested catalogs under `srmech/amsc/attested/`

| Source | Rows | Primary reference | Canonical content |
|---|---|---|---|
| `cmb_polarisation_spectra` | 45 | Planck 2018 V (Aghanim et al., A&A 641 A5; [arXiv:1907.12875](https://arxiv.org/abs/1907.12875)) | Binned TE/EE bandpowers (PR3/R3.02) + low-ℓ BB upper limits (R3.01); TE acoustic peak ℓ=315 D_ℓ=119.4±2.5 μK²; EE 3rd peak ℓ≈1005 D_ℓ=42.4±1.3 μK²; BB Planck-range noise-dominated |
| `cmb_bispectrum` | 36 | Planck 2018 IX (Akrami et al., A&A 641 A9; [arXiv:1905.05697](https://arxiv.org/abs/1905.05697)) | f_NL constraints (local / equilateral / orthogonal × KSW / binned / modal methods); SMICA T+E KSW lensing-subtracted: f_NL^local = -0.9 ± 5.1, f_NL^equilateral = -18 ± 47, f_NL^orthogonal = -37 ± 23 — all consistent with Gaussianity |
| `cmb_lensing` | 37 | Planck 2018 VIII (Aghanim et al., A&A 641 A8; [arXiv:1807.06210](https://arxiv.org/abs/1807.06210)) | Lensing reconstruction Cℓ^{ϕϕ} bandpowers + MV amplitude; Â^{φ,MV}_{8→400} = 1.011 ± 0.028 (conservative); 40σ MV detection |

All 118 rows authored via PDF extraction per `[[feedback_pdf_extraction_citation_discipline]]` — three primary arXiv IDs verified clean at first-page extraction (no citation drift). PLA non-blocking; arXiv served all three PDFs.

### Architectural note — srmech-primary catalogs

This is the first time srmech itself hosts attested catalogs (hitherto srmech was the AMSC *framework* provider, with catalogs hosted in consumer packages like ephemerides-spectral). The new sources sit at `srmech/amsc/attested/<source>/` where `_attested_root()` finds them automatically — no `register_attested_root()` call needed. Existing ephemerides-spectral catalogs continue to register their own root via the cross-package bootstrap (Phase 2 of Task #197).

### No code change; no ABI change

- C ABI v2 unchanged. No new C symbols. No JPL audit pin changes.
- No `srmech.amsc.<class>` Python surface changes.
- No `srmech.qm.*` operation changes.
- Data-only ship: descriptors + NDJSON + schemas under `srmech/amsc/attested/`.
- C version macros bump `SRMECH_VERSION_PATCH` 0 → 1 and `SRMECH_VERSION_PRE` "" → "rc1".

### Versioning

`0.4.0` → `0.4.1rc1`. Patch bump (data addition; no API or ABI change). rc1 routes to TestPyPI per the existing publish-workflow regex; the clean `v0.4.1` ships to production PyPI after rc verify.

## [0.4.0] - 2026-05-15

**Phase C1 close — production ship.** Ships the cumulative Phase C1 scope (rc1 → rc12) to production PyPI. Per `[[feedback_rc_stacking_versioning]]`, the rc-stack accumulated during the sprint; this clean-semver tag promotes the verified rc12 state to live.

### Phase C1 cumulative scope (per `[[feedback_no_mvp_framing]]` full-coverage shipping)

**Primitive vocabulary — 14 of 14 classes with C surfaces.** Closes Task #217 Phase C1 / the per-class C parity build-out per `[[feedback_no_binding_layer_carveout]]`:

- **Class A** — content-addressing via SHA-256 (rc-baseline)
- **Class B** — tagged-tuple TLV byte-canonical form (rc4)
- **Class C** — streaming iteration via NDJSON tokenisation (rc-baseline)
- **Class D** — late-binding multi-needle pattern dispatch (rc5)
- **Class E** — catalog sorted-key binary-search lookup (rc5)
- **Class F** — substitution / `{key}` template render (rc5)
- **Class G** — byte-pattern search (rc4)
- **Class H** — self-introspection (rc4 acknowledgment of existing version / ABI accessors)
- **Class I** — cyclic-group / modular arithmetic (rc1)
- **Class J** — prime-factorisation / period (rc3)
- **Class K** — equation-of-centre / pin-slot (rc7) — Kepler (1609); Smith (1979); Brouwer-Clemence (1961); Freeth (2021) Supp S9
- **Class L** — graph Laplacian; pi-free Jacobi eigvals (rc2)
- **Class M** — HDC binary spatter codes — bind/bundle/permute/similarity (rc8) — Kanerva (2009); Plate (1995); Rachkovskij (2001)
- **Class N** — rational-approximation; continued-fraction convergents (rc6)

**Canonical QM/QFT/SM operations layer (`srmech.qm.*`).** Sourced from canonical physics literature per `[[feedback_science_is_ssot_not_project]]`:

- **`single_particle`** (rc9) — TDSE / TISE / Heisenberg evolution / [x̂,p̂] / lattice momentum / density matrix / Liouville-vN. Schrödinger (1926); Heisenberg (1925); Sakurai §§1.4, 1.6, 2.1-2.3, 3.4; von Neumann (1932); Wilson (1974)
- **`spin`** (rc9) — Pauli matrices σ_x/σ_y/σ_z, Clifford Cl(0,3) residual verification, arbitrary-axis spin-½ operator. Pauli (1927); Sakurai §3.2
- **`potentials`** (rc9) — hydrogen radial Schrödinger, harmonic oscillator ladder operators. Bohr (1913); Heisenberg (1925); Born-Heisenberg-Jordan (1926); Sakurai §§2.3, 3.7
- **`relativistic`** (rc10) — Dirac γ-matrices (Cl(1,3)), γ_5, Weyl projectors, charge conjugation (Majorana), Dirac operator, Klein-Gordon dispersion. Dirac (1928); Klein/Gordon (1926); Weyl (1929); Majorana (1937); Peskin-Schroeder §§3.2-3.4
- **`propagators`** (rc10) — Feynman scalar / fermion / photon / massive-vector. Feynman (1949); Dyson (1949); Peskin-Schroeder §§4.2, 4.7-4.8, 20.1; Weinberg Vol II §21.1
- **`pseudo_hermitian`** (rc10) — η-deformed inner product, expectation, η-pseudo-Hermiticity test, η construction, real-spectrum theorem. Closes chess-spectral ADR-005 framework gap. Bender & Boettcher (1998); Mostafazadeh (2002, 2010)
- **`gauge`** (rc11) — SU(2) / SU(3) Gell-Mann generators, structure constants, Lie algebra residuals, Casimirs (3/4 for SU(2) fund, 4/3 for SU(3) fund), gauge connection, Wilson loop. Yang-Mills (1954); Gell-Mann (1962); Wilson (1974); Peskin-Schroeder §§15-17
- **`sm`** (rc11) — Higgs potential / vev, weak mixing angle, W/Z boson masses, Weinberg relation, fermion mass from Yukawa, CKM matrix (Chau-Keung parameterization). Glashow (1961); Weinberg (1967); Salam (1968); Higgs (1964); Cabibbo (1963); Kobayashi-Maskawa (1973); Peskin-Schroeder Chs 20-21

**Ontology refinement (notebook ship, rc7-rc10 cumulative).**

- MFO **§VII.1.2** — *1D_t as the Laws of Everything — compressed-cascade content* — per user direction 2026-05-15, with user's canonical compressions preserved verbatim (`memory/user_stance_1d_t_as_storage_extraction.md` operation-level + `memory/user_stance_1d_collapse_to_loe_identity_not_action.md` identity-level refinement).
- **Identity-not-implementation discipline** named as umbrella pattern unifying the shadow-stance family (`memory/user_stance_identity_not_implementation_discipline.md`).
- Plurality of "Laws of Everything" canonical (`memory/reference_loe_plural_canonical.md`).
- Two concertmaster artifacts in `docs/srmech/notes/`: `1d_t_as_storage_extraction_2026-05-15.md` + `1d_collapse_to_loe_identity_2026-05-15.md`.
- Plus `task_218_phase_c2_chess_spectral_qm_audit_2026-05-15.md` — QM stack coverage audit (informed Phase C2 → folded into Phase C1 per `[[feedback_science_is_ssot_not_project]]`).

**Tool-schema audit (rc12) closes the sprint** — `srmech.amsc.tool_schema` extended with **~87 entries** covering all 14-class primitives + the full `srmech.qm.*` operations layer. Coverage ratchet test (`tests/test_tool_schema_coverage.py`, 8 cases) walks every public callable in `srmech.amsc.*` and `srmech.qm.*` via `pkgutil` + `inspect` and asserts each has a registered ToolEntry. Closes Tasks #219 + #220.

### Test plan summary

- **CI**: 8/8 pass at every rc (rc7-rc12), all three OS cells (Ubuntu / macOS / Windows) × Python 3.10-3.14 × pedantic C build (gcc / clang / MSVC) + pure-wheel build + sdist.
- **Cumulative test count growth**: ~290 cases across the 12-rc sprint covering Class K parity, Class M parity, QM single-particle / spin / potentials / relativistic / propagators / pseudo-Hermitian / gauge / sm operations layer canonical identities, and tool-schema coverage.
- **TestPyPI verification**: `srmech-v0.4.0rc12` published + smoke-verified prior to this clean-semver ship.

### Discipline honoured

`[[feedback_no_mvp_framing]]`, `[[feedback_science_is_ssot_not_project]]`, `[[feedback_no_privileged_primitive_classes]]`, `[[feedback_no_binding_layer_carveout]]`, `[[feedback_jpl_rule_5_two_assert_habit]]`, `[[feedback_rc_stacking_versioning]]`, `[[feedback_no_squash_merges]]`, `[[feedback_pdf_extraction_citation_discipline]]`, `[[user_stance_kepler_shape_universal]]`, `[[user_stance_1d_collapse_to_loe_identity_not_action]]`, `[[user_stance_identity_not_implementation_discipline]]`.

### Changed

- **ABI stays v2** — cumulative across rc7-rc12 (pure additions per Phase B4 convention).

## [0.4.0rc12] - 2026-05-15

### Added

**Task #217 Phase C1 — end-of-sprint tool-schema audit (Tasks #219 + #220).**

Twelfth and final canonical rc in Phase C1's rc-stacked build-out. Closes the **end-of-sprint hygiene** scope per user direction (*"check tool-schema and help arg that every command is shown how to be used"*) before 0.4.0 ships to PyPI.

#### `srmech.amsc.tool_schema` — extension to cover the full operations layer

Adds **two new registration functions** to `srmech.amsc.tool_schema`:

- `_register_primitive_class_tools()` — **27 entries** covering the 14-class Spike #24 primitive vocabulary (Classes A and C were already registered; this adds B, D, E, F, G, I, J, K, L, M, N — every primitive operation exposed via `srmech.amsc.*`).
- `_register_qm_tools()` — **54 entries** covering the canonical QM/QFT/SM operations layer in `srmech.qm.*` (single_particle, spin, potentials, relativistic, propagators, pseudo_hermitian, gauge, sm).

Both functions are called at `tool_schema` module import time alongside the original `_register_amsc_tools()`. Total registered: **~87 tool-schema entries**, each with name + owner + category + summary + parameters + returns. Summaries cite canonical SSoT per `[[feedback_science_is_ssot_not_project]]`.

#### Coverage ratchet — `tests/test_tool_schema_coverage.py`

New test file with 8 cases enforcing the audit at CI time:

1. **`test_amsc_public_callables_have_tool_entries`** — walks `srmech.amsc.*` via `pkgutil` + `inspect`; every public function (minus a small exempt allowlist of bridge helpers + adapters + profile-loader internals) must have a registered entry.
2. **`test_qm_public_callables_have_tool_entries`** — same for `srmech.qm.*`. No exemptions — every public callable must be registered.
3. **`test_tool_schema_entries_have_required_fields`** — non-empty name / owner / summary; parameters tuple well-typed.
4. **`test_tool_schema_owner_is_srmech_for_builtins`** — owner = "srmech" for builtin entries.
5. **`test_tool_schema_view_is_jsonable`** — JSON round-trip clean.
6. **`test_tool_schema_total_count_meets_floor`** — ratchet at ≥ 80 entries (only ever grows).
7. **`test_no_duplicate_tool_names`** — each dotted name unique.
8. **`test_tool_schema_categories_match_module_structure`** — category sanity-check.

#### Discipline notes

- **No CLI surface** to audit — srmech is a library, not a command-line tool. The user's *"every command is shown how to be used"* direction was interpreted as: every callable has a proper docstring (already enforced through rc7-rc11 ToolEntry / docstring discipline) **and** every callable surfaces via the tool-schema introspection API (this rc).
- **Per-operation canonical SSoT preserved**: every new ToolEntry's summary cites the canonical physics literature (Schrödinger / Heisenberg / Dirac / Yang-Mills / Gell-Mann / Wilson / Glashow-Weinberg-Salam / Cabibbo / Kobayashi-Maskawa / Higgs / Mostafazadeh / Bender-Boettcher) per `[[feedback_science_is_ssot_not_project]]`.
- **No new C symbols**; ABI stays v2.

### Changed

- **`srmech.amsc.tool_schema`**: +2 registration functions, +81 new ToolEntry registrations (cumulative).

### Roadmap

**Phase C1 close → 0.4.0 final**:

- 14 of 14 primitive classes with C surfaces ✅
- Canonical single-particle QM (rc9) ✅
- Relativistic QM + Feynman propagators + η-pseudo-Hermitian (rc10) ✅
- Gauge theory + Standard Model surface (rc11) ✅
- End-of-sprint tool-schema audit (rc12, this rc) ✅

**Next**: drop the `rc12` suffix → tag `srmech-v0.4.0` → autotag dispatches production PyPI publish per the existing publish workflow (Task #196).

## [0.4.0rc11] - 2026-05-15

### Added

**Task #217 Phase C1 — Gauge theory + Standard Model surface (final canonical-physics rc).**

Eleventh rc in Phase C1's rc-stacked build-out. **Closes the canonical-physics scope** of PR #432: 14/14 primitive classes + canonical single-particle QM (rc9) + relativistic QM / propagators / η-pseudo-Hermitian (rc10) + **gauge theory + SM surface (rc11)**.

Per `[[feedback_science_is_ssot_not_project]]`: each operation cites canonical gauge-theory / SM literature. Numerical experimental values (M_W, M_Z, fermion masses, CKM elements) are NOT hardcoded — this rc ships the algebraic primitives that map (gauge couplings, Higgs vev, Yukawa couplings, mixing angles) to observable masses.

Per `[[user_stance_1d_collapse_to_loe_identity_not_action]]`: substrate-coupling operations on internal-symmetry representation spaces. Each dissolves into the 14-class primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]` — no new classes.

#### `srmech.qm.gauge`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `su2_generators() → (T¹, T², T³)` | Peskin-Schroeder §15.1 eq 15.5-6 | Class M (Lie-algebra binding, Pauli-half generators) |
| `su2_structure_constants() → εᵃᵇᶜ` | Peskin-Schroeder §15.1 eq 15.4 | — |
| `su3_gell_mann_matrices() → (λ¹...λ⁸)` | Gell-Mann (1962) PR 125, 1067; Peskin-Schroeder eq 17.32 | Class M (SU(3) Lie-algebra binding) |
| `su3_generators() → (T¹...T⁸)` | Peskin-Schroeder eq 17.33 | Class M |
| `su3_structure_constants() → fᵃᵇᶜ` | Peskin-Schroeder eq 17.34; Schwartz Table 25.1 | — |
| `lie_algebra_residual(gens, f)` | Peskin-Schroeder §15.1 eq 15.4 | (verification: `[Tᵃ, Tᵇ] = i fᵃᵇᶜ Tᶜ`) |
| `casimir_operator(gens) → C₂` | Peskin-Schroeder §15.4 eq 15.93 | Class L (sum of generator squares) |
| `casimir_eigenvalue(gens)` | Peskin-Schroeder §15.4 | Class L (trace / dim) |
| `gauge_connection_matrix(A, gens) → Aᵃ Tᵃ` | Peskin-Schroeder §15.1 eq 15.2 | Class M |
| `gauge_path_segment(A, gens, g) → exp(i g Aᵃ Tᵃ)` | Wilson (1974) PRD 10, 2445; Peskin-Schroeder §15.3 eq 15.55 | Class L (Hermitian matrix exponential via eigendecomp) |
| `wilson_loop_from_segments(A_segs, gens, g) → ∏ exp(...)` | Wilson (1974) eq 2.3 | Class C ∘ Class L (path-ordered iteration over segments) |

#### `srmech.qm.sm`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `higgs_potential(φ, μ², λ)` | Higgs (1964); Peskin-Schroeder §20.1 eq 20.6 | Class K (continuous projection) |
| `higgs_vev(μ², λ) → v` | Peskin-Schroeder §20.1 eq 20.7 | Class K |
| `weak_mixing_angle(g, g')` | Weinberg (1967) eq 8; Peskin-Schroeder §20.2 eq 20.31 | Class K (atan2) |
| `w_boson_mass(g, v)` | Peskin-Schroeder §20.2 eq 20.30 | Class K |
| `z_boson_mass(g, g', v)` | Peskin-Schroeder §20.2 eq 20.32 | Class K |
| `weinberg_relation_residual(g, g', v)` | Peskin-Schroeder §20.2 eq 20.33 | (verification: `M_W = M_Z cos θ_W`) |
| `electroweak_summary(g, g', v) → dict` | Composite §20.2 | — |
| `fermion_mass_from_yukawa(y, v)` | Peskin-Schroeder §20.2 eq 20.27; Schwartz §29.1 eq 29.18 | Class K |
| `ckm_matrix(θ₁₂, θ₁₃, θ₂₃, δ_CP)` | Cabibbo (1963); Kobayashi-Maskawa (1973); Chau-Keung (1984); PDG §12.1 | Class M (unitary mixing-binding) |
| `ckm_unitarity_residual(V)` | PDG §12.1 | (verification) |

Foundation literature:
- Glashow (1961) *Nucl. Phys.* 22, 579-588.
- Weinberg (1967) *Phys. Rev. Lett.* 19, 1264-1266.
- Salam (1968) *Elementary Particle Theory*.
- Higgs (1964); Englert-Brout (1964); Guralnik-Hagen-Kibble (1964).
- Cabibbo (1963); Kobayashi-Maskawa (1973).
- Yang & Mills (1954) *Phys. Rev.* 96, 191-195.
- Gell-Mann (1962) *Phys. Rev.* 125, 1067-1084.
- Wilson (1974) *Phys. Rev. D* 10, 2445-2459.
- Peskin & Schroeder (1995) *Intro QFT*, Chs 15-17, 20-21.
- Weinberg (1996) *QToF* Vol II §15, §21.
- Schwartz (2014) *QFT and the SM*, Chs 25-29.

#### Tests (2 files, ~40 cases)

- `test_qm_gauge.py` — SU(2)/SU(3) generators Hermitian + traceless; canonical normalization `tr(TᵃTᵇ) = δᵃᵇ/2`; structure-constant total antisymmetry; **Lie algebra closure `[Tᵃ, Tᵇ] = i fᵃᵇᶜ Tᶜ` at machine precision** for both SU(2) and SU(3); Casimir eigenvalue 3/4 for SU(2) fundamental, 4/3 for SU(3) fundamental; Casimir proportional to identity (Schur); path-segment unitarity; multi-segment Wilson-loop unitarity.
- `test_qm_sm.py` — Higgs vev formula; potential minimum at vev; `V(v) = -μ⁴/(4λ)`; Weinberg relation `M_W = M_Z cos θ_W` at machine precision across multiple coupling regimes; fermion mass `m = y v / √2`; CKM unitarity `V V† = I` for arbitrary mixing angles + CP phase; CKM reduces to 2×2 Cabibbo rotation when θ₁₃ = θ₂₃ = 0.

### Changed

- **ABI stays v2** — operations layer is pure Python (numpy-based; gauge matrix exponentials via Hermitian eigendecomp, no scipy dependency).
- **srmech.qm** imports updated for the two new submodules (`gauge`, `sm`).

### Roadmap

Phase C1 **canonical-physics scope complete**:
- 14 of 14 primitive classes with C surfaces.
- Canonical single-particle QM (rc9).
- Relativistic QM + Feynman propagators + η-pseudo-Hermitian (rc10).
- Gauge theory + Standard Model surface (rc11, this rc).

Remaining for Phase C1 close → 0.4.0 final (folding all into PR #432):
- **End-of-sprint hygiene** per user direction:
  - **Task #219**: Per-class CLI `--help` audit — every command shows how to be used.
  - **Task #220**: Tool-schema extension — every operation surfaces via `srmech.amsc.tool_schema`.
- **0.4.0 final**: clean ship to PyPI at PR merge.

## [0.4.0rc10] - 2026-05-15

### Added

**Task #217 Phase C1 — Relativistic QM + Feynman propagators + η-pseudo-Hermitian primitive.**

Tenth rc in Phase C1's rc-stacked build-out. **Folds the relativistic-QM / QFT propagator layer into PR #432** with canonical literature SSoT per `[[feedback_science_is_ssot_not_project]]`.

Per `[[user_stance_1d_collapse_to_loe_identity_not_action]]`: these are substrate-coupling operations on relativistic-QM and QFT Hilbert spaces. Each dissolves into the 14-class primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]`. **No new primitive classes**.

**Metric convention**: mostly-minus `η^{μν} = diag(+1, -1, -1, -1)` (Peskin-Schroeder convention). γ-matrix representation: Dirac (standard) basis.

#### `srmech.qm.relativistic`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `minkowski_metric()` | Peskin-Schroeder §3.1 eq 3.4 | — |
| `gamma_matrices() → (γ^0, γ^1, γ^2, γ^3)` | Dirac (1928); Peskin-Schroeder §3.2 eq 3.25 + A.6 | Class M (Cl(1,3) Clifford binding) |
| `gamma_5()` | Peskin-Schroeder §3.4 eq 3.72 | Class M |
| `clifford_residuals()` | Peskin-Schroeder §3.2 eq 3.21, §3.4 eq 3.72 | (verification) |
| `weyl_left_projector()`, `weyl_right_projector()` | Weyl (1929); Peskin-Schroeder §3.4 eq 3.71 | Class M |
| `charge_conjugation_matrix()` | Majorana (1937); Peskin-Schroeder eq A.27 | Class M |
| `dirac_operator_momentum_space(k, m)` | Dirac (1928); Peskin-Schroeder §3.2 eq 3.45-3.46 | Class L (linear operator on spinor space) |
| `klein_gordon_dispersion(k, m)` | Klein (1926); Gordon (1926); Peskin-Schroeder §2.3 eq 2.39 | Class L |
| `four_momentum_squared(k)` | Peskin-Schroeder §3.1 eq 3.4 | — |

#### `srmech.qm.propagators`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `feynman_scalar_propagator(k², m, ε)` | Feynman (1949); Dyson (1949); Peskin-Schroeder §4.2 eq 4.42 | Class K (continuous projection-shadow of integer-cyclic upstream per the lattice scalar propagator G(k) = 1/(m² + k̂²)) |
| `feynman_fermion_propagator(k, m, ε)` | Peskin-Schroeder §4.7 eq 4.107 + 4.111 | Class K + Class M |
| `feynman_photon_propagator(k², ξ, ε, k)` | Peskin-Schroeder §4.8 eq 4.118-4.121 | Class K (covariant gauge + Feynman gauge specializations) |
| `feynman_massive_vector_propagator(k, m, ε)` | Peskin-Schroeder §20.1 eq 20.13; Weinberg Vol II §21.1.21 | Class K |

#### `srmech.qm.pseudo_hermitian`

**Closes the η-metric primitive gap in chess-spectral ADR-005** per `docs/srmech/notes/task_218_phase_c2_chess_spectral_qm_audit_2026-05-15.md`. Chess-spectral becomes a substrate-consumer of these primitives when ADR-005 is finished.

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `inner_product_eta(a, b, η)` | Mostafazadeh (2002) JMP 43, 205, eq 2.6 | Class L (η-deformed inner product) |
| `expectation_eta(O, ψ, η)` | Mostafazadeh (2002) eq 3.6 | Class L |
| `is_pseudo_hermitian(O, η)` | Mostafazadeh (2002) eq 2.4 | (verification) |
| `construct_eta_from_eigendecomposition(O)` | Mostafazadeh (2002) eq 2.7-2.10 | Class L (eigendecomp + inverse) |
| `pseudo_hermitian_eigenvalues_real(O, η)` | Bender & Boettcher (1998) PRL 80, 5243; Mostafazadeh (2002, 2010) | (verification) |

Foundation literature:
- Bender, C.M. & Boettcher, S. (1998) *Phys. Rev. Lett.* 80, 5243-5246.
- Mostafazadeh, A. (2002) *J. Math. Phys.* 43, 205-214; 2814-2816; 3944.
- Mostafazadeh, A. (2010) *Int. J. Geom. Methods Mod. Phys.* 7, 1191-1306.

#### Tests (3 files, ~40 cases)

- `test_qm_relativistic.py` — Cl(1,3) algebra at machine precision; Weyl projector identities (P_L + P_R = I, P² = P, P_L P_R = 0); charge conjugation `C γ^μ C^{-1} = -(γ^μ)^T`; Klein-Gordon dispersion `E² = |k|² + m²`; Dirac operator on-shell zero-eigenvalues at rest; positive-energy spinor annihilation.
- `test_qm_propagators.py` — scalar / fermion propagator inverses; `S_F^{-1}(k) = -i(γ·k - m)/(k²-m²)` verified via `(γ·k - m) S_F = i I_4`; on-shell pole-prescription handling; photon Feynman-gauge shape; massive-vector k^μ k^ν / m² term verification.
- `test_qm_pseudo_hermitian.py` — η = I reduction to standard inner product; constructed η makes operator η-pseudo-Hermitian; Mostafazadeh real-spectrum theorem; complex-spectrum rejection.

### Changed

- **ABI stays v2** — operations layer is pure Python (numpy-based for complex matrices).
- **srmech.qm**: imports updated for the three new submodules (`relativistic`, `propagators`, `pseudo_hermitian`).

### Roadmap

Phase C1 progress: **14 of 14 primitive classes + canonical single-particle QM + relativistic QM + Feynman propagators + η-pseudo-Hermitian shipped**.

Remaining for Phase C1 close → 0.4.0 final (folding all into PR #432):
- **rc11**: Gauge theory (U(1) / SU(2) / SU(3) Yang-Mills, Wilson loops, gauge connections, Casimir per irrep) + SM surface (electroweak unification, Higgs, Yukawa).
- **End-of-sprint**: Task #219 (per-class CLI `--help` audit) + Task #220 (tool-schema extension for every operation).
- **0.4.0 final**: clean ship to PyPI at PR merge.

## [0.4.0rc9] - 2026-05-15

### Added

**Task #217 Phase C1 — Canonical single-particle QM operations layer (first ship from `srmech.qm`).**

Ninth rc in Phase C1's rc-stacked build-out. **First substantive operations layer on top of the 14-class C parity roster** — opens `srmech.qm.*` as the canonical QM/QFT/SM operations namespace, with each operation sourced from canonical physics literature per `[[feedback_science_is_ssot_not_project]]` (Sakurai / Cohen-Tannoudji / Griffiths / Pauli / Schrödinger / Heisenberg / Bohr / von Neumann).

Per `[[user_stance_1d_collapse_to_loe_identity_not_action]]` (MFO §VII.1.2): these operations are **substrate-coupling operations** that uncompress LoE-content (1D_t Laws) into event-stream. Each dissolves into the 14-class primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]` — no new classes added.

#### `srmech.qm.single_particle`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `tdse_evolve(H, psi, t)` | Schrödinger (1926); Sakurai §2.1.5 | Class L (spectral evolution `V·diag(exp(-iλt))·V^H`) |
| `tise_solve(H)` | Schrödinger (1926); Sakurai §2.1.3 | Class L (Hermitian eigendecomp) |
| `commutator(A, B) = AB - BA` | Sakurai §1.4 eq 1.4.6 | Class L (operator algebra) |
| `heisenberg_evolve(A, H, t)` | Heisenberg (1925); Sakurai §2.2 eq 2.2.15 | Class L (eigenbasis-diagonal `U†AU`) |
| `lattice_momentum(n, dx)` | Sakurai §1.6; Wilson (1974) | Class C (lattice gradient as anti-Hermitian central difference) |
| `density_matrix(psi)` | von Neumann (1932); Sakurai §3.4 eq 3.4.7 | (pure-state outer product) |
| `liouville_evolve(rho, H, t)` | von Neumann (1932); Sakurai §3.4.2 eq 3.4.28 | Class L (commutator-flow) |

#### `srmech.qm.spin`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `pauli_matrices() → (σ_x, σ_y, σ_z)` | Pauli (1927) ZfP 43, 601; Sakurai §3.2 | Class M (Clifford Cl(0,3) binding generators) |
| `pauli_clifford_residuals()` | Sakurai §3.2 eq 3.2.2-3 | (verification: `{σ_i, σ_j} = 2δ_{ij} I`, `[σ_i, σ_j] = 2i ε_{ijk} σ_k`) |
| `pauli_spin_operator(direction)` | Sakurai §3.2 eq 3.2.51 | Class M (Clifford projection along arbitrary axis) |

#### `srmech.qm.potentials`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `hydrogen_radial(n_grid, r_max, l_quantum)` | Bohr (1913); Schrödinger (1926); Sakurai §3.7 | Class L (3-point-stencil radial-Laplacian eigendecomp) |
| `harmonic_oscillator_ladder(n_dim, omega)` | Heisenberg (1925); Born-Heisenberg-Jordan (1926); Sakurai §2.3 | Class M (Fock-space binding for `a`, `a†`) |
| `harmonic_oscillator_hamiltonian(n_dim, omega)` | Sakurai §2.3 eq 2.3.16 | Class L + Class M composition (`H = ω(a†a + 1/2)`) |

#### Tests (3 files, ~50 cases)

- `tests/test_qm_single_particle.py` — TDSE norm/energy preservation, eigenstate phase evolution; TISE orthonormality + eigen-relation; commutator self-zero + antisymmetry; Heisenberg self-conservation; lattice momentum Hermiticity; density matrix idempotency for pure states; Liouville trace + purity preservation.
- `tests/test_qm_spin.py` — Pauli Hermiticity / tracelessness / eigenvalues ±1 / Clifford algebra residuals at machine precision; arbitrary-axis spin-½ operator.
- `tests/test_qm_potentials.py` — Harmonic oscillator analytical spectrum (`E_n = ω(n + 1/2)`); ladder action `a|n⟩ = √n |n-1⟩`; hydrogen ground state ≈ −0.5 Rydberg; 2s state ≈ −0.125; l=1 centrifugal exclusion; TDSE-on-oscillator-eigenstate phase consistency.

### Changed

- **ABI stays v2** — no new C symbols (operations layer is Python-side, building on Classes A-N C primitives + numpy for complex-Hermitian operations).

### Roadmap

Phase C1 progress: **14 of 14 primitive classes + single-particle QM operations layer landed**.

Remaining for the Phase C1 close → 0.4.0 final (folding all into PR #432):
- **rc10**: Relativistic QM (Klein-Gordon, Dirac, Weyl, Majorana, Bargmann-Wigner) + Feynman propagators (scalar / fermion / photon / vector) + η-pseudo-Hermitian (closes ADR-005 in chess-spectral).
- **rc11**: Gauge theory (U(1) / SU(2) / SU(3) Yang-Mills, Wilson loops, gauge connections, Casimir per irrep) + Standard Model surface (electroweak unification, Higgs, Yukawa couplings).
- **End-of-sprint hygiene**: Task #219 (per-class CLI `--help` audit — every command shows how to be used) + Task #220 (tool-schema extension — every operation surfaces via `srmech.amsc.tool_schema`).
- **0.4.0 final**: clean ship to PyPI at PR merge.

## [0.4.0rc8] - 2026-05-15

### Added

**Task #217 Phase C1 — Class M (HDC binary spatter codes) C port. Closes the 14-class C parity roster.**

Eighth rc in Phase C1's rc-stacked build-out. Class M is **the binding operation that uncompresses LoE-content along its compression axis** per `[[user_stance_1d_collapse_to_loe_identity_not_action]]` — substrate-coupling operation, NOT the LoE-content itself (1D_t is the content per MFO §VII.1.2). Class C ∘ Class M composes the full LoE-uncompression kernel: Class C iteration drives Class M binding to produce event-stream from compressed-cascade laws-content.

Four BSC operations on byte-buffer hyperdimensional vectors (D bits = 8 * n_bytes; canonical default 128 bytes = 1024 bits):

| C symbol | Python wrapper | Operation | Canonical SSoT |
|---|---|---|---|
| `srmech_hdc_bind(a, b, n_bytes, *out)` | `srmech.amsc.hdc.bind(a, b)` | Component-wise XOR; commutative, associative, self-inverse. | Kanerva (2009) Cognitive Computation 1, 139-159 |
| `srmech_hdc_bundle(vectors, n_vectors, n_bytes, *out)` | `srmech.amsc.hdc.bundle(vectors)` | Bitwise majority across odd `n_vectors` ≤ 257. Even counts rejected (caller can pad with tie-breaker). | Plate (1995) IEEE TNN 6, 623-641 |
| `srmech_hdc_permute(a, n_bytes, rotate_bits, *out)` | `srmech.amsc.hdc.permute(a, rotate_bits)` | Cyclic bit-rotation; preserves popcount; `permute(permute(a, k), -k) == a`. | Rachkovskij (2001) Neural Comput Appl 9, 322 |
| `srmech_hdc_similarity(a, b, n_bytes, *out)` | `srmech.amsc.hdc.similarity(a, b)` | `1 - 2 * hamming(a, b) / D` in [-1, 1]; +1 identical, 0 orthogonal, -1 complementary. | Kanerva (2009) |

**SSoT discipline per `[[feedback_science_is_ssot_not_project]]`.** Each operation cites canonical HDC literature — Kanerva / Plate / Rachkovskij — not any project instantiation. Chess-spectral's encoder (the 640-dim bundle that gets cast to ψ via `state_to_psi`) becomes one substrate-consumer of these primitives.

JPL Power-of-Ten compliant: bounded loops (bundle ≤ MAX_BUNDLE_N=257 vectors; permute ≤ D bits), 256-entry popcount lookup table for portability (no `__builtin_popcount` dependency).

### Changed

- **ABI stays v2** — four new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_hdc.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **14 of 14 classes shipped with C surfaces** ✅ (A + C from Phase B; I + L + J + B + G + H + D + E + F + N + K + M from rc1–rc8). 14-class C parity roster CLOSED.

Next layers in PR #432 (Phase C1 close — folding all):
- **Canonical single-particle QM** (TDSE / TISE / Heisenberg / [x̂,p̂] / Liouville-vN / Pauli / hydrogen-radial / harmonic-oscillator) — Sakurai / Cohen-Tannoudji / Griffiths.
- **Relativistic QM + Feynman propagators + η-pseudo-Hermitian** — Peskin & Schroeder Chs 3-4; Bender & Boettcher (1998); Mostafazadeh (2002, 2010).
- **Gauge theory + SM** — Peskin & Schroeder Chs 15, 20-21; Weinberg Vol II.
- **0.4.0 final** — clean ship to PyPI at PR merge.

## [0.4.0rc7] - 2026-05-15

### Added

**Task #217 Phase C1 — Class K (equation-of-centre / pin-slot) C port.**

Seventh rc in Phase C1's rc-stacked build-out. Class K is the **continuous-projection layer** of Kepler-shape primitive composition — per `[[user_stance_kepler_shape_universal]]` + PR #416 F2/F15/F17, Kepler-equation algebra IS pin-slot composition. The bronze Antikythera instantiates Class K natively; the universe instantiates the same algebra via gravitational dynamics (see `[[user_stance_1d_t_as_storage_extraction]]` + `docs/srmech/notes/1d_t_as_storage_extraction_2026-05-15.md` — same Kepler-shape cascade at different dimensional reaches).

Three continuous operations on double-precision floats (uses libm: `sin` / `cos` / `atan2` / `fabs`):

| C symbol | Python wrapper | Operation | Canonical SSoT |
|---|---|---|---|
| `srmech_pin_slot(theta, i, d, *phi)` | `srmech.amsc.kepler.pin_slot(theta, i, d)` | Era-appropriate Antikythera pin-and-slot transform: `phi = atan2(i*sin(theta), d + i*cos(theta))`. | Freeth (2021) *Nature Sci Rep*, Supp S9 |
| `srmech_kepler_solve(M, e, tol, max_iter, *E)` | `srmech.amsc.kepler.kepler_solve(M, e)` | Newton-Raphson on Kepler's equation `M = E - e*sin(E)` with Smith (1979) initial-guess starter `E_0 = M + e*sin(M)`. Converges in 4-6 iter for `e < 0.5`. | Kepler (1609) *Astronomia Nova*; Smith (1979) Celestial Mech 19, 163 |
| `srmech_equation_of_centre(M, e, n_terms, *delta)` | `srmech.amsc.kepler.equation_of_centre(M, e, n_terms)` | Fourier-series principal-term-per-harmonic `nu - M = sum_{k=1..n} c_k * e^k * sin(k*M)` with `c_k = [2, 5/4, 13/12, 103/96, 1097/960, 1223/960]` for `k = 1..6`. | Brouwer & Clemence (1961) §3.2; Murray & Dermott (1999) §2.5 eq 2.84-2.88 |

**SSoT discipline per `[[feedback_science_is_ssot_not_project]]`.** Each operation cites the canonical physics literature — Kepler / Brouwer & Clemence / Murray & Dermott / Smith / Freeth — not any project instantiation. Antikythera-spectral / ephemerides-spectral / chess-spectral are *substrate-consumers* of these primitives, not their authors.

### Changed

- **ABI stays v2** — three new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_kepler.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **13 of 14 classes shipped with C surfaces** (A + C from Phase B; I + L + J + B + G + H + D + E + F + N + K from rc1–rc7). Remaining: **M** (HDC bind/bundle/permute — distributed-representation, rc8).

Per `[[feedback_science_is_ssot_not_project]]` reframe: the canonical QM/QFT/SM operations layer is being woven into the Phase C1 close rather than deferred to a separate Phase C2 absorption-from-projects pass. Class M rc8 acquires its operational anchor as **the binding operation that uncompresses LoE-content along its compression axis** per `[[user_stance_1d_collapse_to_loe_identity_not_action]]` (refined from the prior storage/extraction framing — 1D_t IS the Laws of Everything content, identity; Class M is the substrate-coupling operation, not the dimension itself; see `docs/srmech/notes/1d_collapse_to_loe_identity_2026-05-15.md`). Canonical single-particle QM operations (TDSE / TISE / Heisenberg / [x̂,p̂] / Liouville-vN / Pauli / hydrogen-radial / harmonic-oscillator) targeted for rc7 follow-up commits or rc8 alongside Class M; sourced from Sakurai / Cohen-Tannoudji / Griffiths.

## [0.4.0rc6] - 2026-05-16

### Added

**Task #217 Phase C1 — Class N (rational-approximation) C port.**

Sixth rc in Phase C1's rc-stacked build-out. Class N is the third pure-integer primitive (after I — modular arithmetic, J — prime factorisation / period). Two operations, both `uint64_t`, both JPL-clean, both pi-free.

| C symbol | Python wrapper | Operation |
|---|---|---|
| `srmech_continued_fraction(p, q, terms[], max_terms, *out_count)` | `srmech.amsc.rational.continued_fraction(p, q)` | Simple continued-fraction expansion of `p/q` as `[a_0, a_1, ...]` via the Euclidean recurrence. |
| `srmech_best_rational(p, q, max_denom, *out_p, *out_q)` | `srmech.amsc.rational.best_rational(p, q, max_denom)` | Best rational `p'/q'` with `q' ≤ max_denom` approximating `p/q` via continued-fraction convergents (Stern-Brocot path through the mediant tree). Overflow-guarded on the convergent recurrence. |

Loop bound `SRMECH_RATIONAL_EUCLID_CAP = 128` covers Fibonacci-worst-case for uint64 (~91 iterations). Same constant Class I uses for its Euclidean GCD.

### Changed

- **ABI stays v2** — two new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_rational.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **12 of 14 classes shipped with C surfaces** (A + C from Phase B; I + L + J + B + G + H + D + E + F + N from rc1–rc6). Remaining: **K + M**.

- **rc7**: K (equation-of-centre / pin-slot — orbital arithmetic)
- **rc8**: M (HDC bind/bundle/permute — distributed-representation)
- **0.4.0 final**: clean ship at Phase C1 close

## [0.4.0rc5] - 2026-05-16

### Added

**Task #217 Phase C1 — Classes D + E + F C ports (real surfaces, not acknowledgment).**

Fifth rc in Phase C1's rc-stacked build-out. Three new C primitive operations, one per class, each parity-tested against a pure-Python fallback. Step 1 of C/Python parity per the architectural commitment: every primitive class earns its C surface.

| Class | C symbol | Python wrapper | Primitive operation |
|---|---|---|---|
| **D** (dispatch) | `srmech_dispatch_match` | `srmech.amsc.dispatch.match` | Given input bytes + ordered (pattern, tag) rules, return tag of first rule whose pattern occurs in input. Multi-needle pattern dispatcher; builds on Class G's `srmech_byte_search` internally. |
| **E** (catalog / naming) | `srmech_catalog_lookup` | `srmech.amsc.naming.lookup` | Binary search over sorted (key, value) catalog. Lex-comparison with length tiebreak. O(log n) lookup, ≤64 iterations cap. |
| **F** (template render) | `srmech_template_render` | `srmech.amsc.template.render` | Render template with `{key}` placeholders, substituting via key→value catalog (uses Class E's `srmech_catalog_lookup` internally). |

Naming note: the new Python primitives are `srmech.amsc.dispatch` / `srmech.amsc.naming` / `srmech.amsc.template` to avoid collision with the existing application-layer modules (`amsc.catalog` is Class E *applied to attested-source registries*, `amsc.descriptor.render_template` is Class F *applied to descriptor cite/purpose templates*). Application modules can later rebuild on the primitive surface for hot-path optimisation.

### Changed

**`CLAUDE.md` operational-scope-clarification rewritten** to remove the "binding-layer concern" framing. Per `[[feedback_no_binding_layer_carveout]]`: every primitive class earns a C surface; "binding-layer" is not a legitimate skip-class directive. Specific scope-bounded helpers (e.g., TOML parsing stays Python per the Phase B5 *vendoring-scope* decision) are framed as their own scope concerns, not as class-skipping carve-outs.

ABI stays v2 — three new symbols are pure additions per the Phase B4 convention. CMake picks up `srmech_dispatch.c` / `srmech_catalog.c` / `srmech_template.c` automatically via `file(GLOB)`.

### Roadmap

Phase C1 progress: **11 of 14 classes shipped with C surfaces** (A + C from Phase B; I + L + J + B + G + H + D + E + F from rc1–rc5). Remaining: **K + M + N**.

- **rc6**: N (rational-approximation — Stern-Brocot continued fractions; pure integer)
- **rc7**: K (equation-of-centre / pin-slot)
- **rc8**: M (HDC bind/bundle/permute)
- **0.4.0 final**: clean ship at Phase C1 close

## [0.4.0rc4] - 2026-05-16

### Added

**Task #217 Phase C1 — Classes B + G + H (the lightweight trio).**

Fourth rc in Phase C1's rc-stacked build-out. Bundles three lightweight classes whose primitive operations each fit a small C surface, freeing up rc cadence for the heavier classes (M, K) later.

- **Class B (tagged-tuple)** — `srmech_tlv_pack(tag, value, value_len, out, capacity, *written)` produces deterministic `[u8 tag][u32 length BE][value]` byte sequences for hashing / fingerprinting typed records. Format is wire-spec ordered (tag-first per the layout); documented as the exception to `[[feedback_struct_field_ordering_big_first]]`. JSON-record parsing stays Python-side per srmech CLAUDE.md operational-scope-clarification.
- **Class G (discovery/search)** — `srmech_byte_search(haystack, h_len, needle, n_len, *out_offset)` finds first occurrence of a byte pattern via naive O(n*m) (fast for srmech's small-haystack cases — descriptor lookups, fingerprint matching). Empty needle matches at offset 0 (matches Python's `bytes.find(b'')`). Catalog dictionary lookups stay Python-side.
- **Class H (self-introspection)** — *already shipped* via `srmech_meta.c`'s `srmech_version()` and `srmech_abi_version()` (Phase B2 baseline). This rc explicitly acknowledges H's mapping to those existing primitives for the cross-substrate-audit roster; no new C symbols added for H.

Public Python surfaces at `srmech.amsc.tlv` and `srmech.amsc.search` with native/fallback dispatch. Parity tests at `tests/test_lightweight_parity.py` cover reference values + Python-equivalence + native↔fallback sweep.

### Changed

- **Class O dissolution** (resolution 2026-05-16). The signed-metric / Wick-rotation operation located by Spike #24 bonus 8 and narrowed by bonus 9 was **dissolved into Class L as a signed-Laplacian-variant sub-operation** per user direction *"nothing else so far has been privileged."* Vocabulary stays at 14 classes A–N; no Class O added. Future Class L rcs will add the signed-Laplacian op when Phase C2 cascade-composition work calls for it. New memory entry `[[feedback_no_privileged_primitive_classes]]` records the design principle: dissolution into existing classes is the default disposition for candidate primitives; promotion requires structural irreducibility. Bonus 11d (Class P sign-rule reduced to existing) is the precedent.
- **ABI stays v2** — two new symbols (tlv_pack, byte_search) are pure additions per the Phase B4 convention.
- **CMake**: `srmech_tlv.c` and `srmech_search.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **8 of 14 classes shipped** (A + C from Phase B; I + L + J + B + G + H from Phase C1 rc1–rc4). Remaining: D / E / F / K / M / N. Class D and Class F are likely Python-only-by-design per srmech CLAUDE.md operational-scope-clarification (binding-layer concerns). Heavier classes (M = HDC bind/bundle, K = equation-of-centre/pin-slot) come later as dedicated rcs.

## [0.4.0rc3] - 2026-05-15

### Added

**Task #217 Phase C1 — Class J (prime-factorisation / period) C parity.**

Third per-class C port in Phase C1's rc-stacked build-out. Class J ("J prime-factorisation/period" in Spike #24's cumulative cross-substrate audit) complements Class I (modular arithmetic) with the non-modular integer-structure operations.

Three new C symbols (all `uint64_t`, JPL Power-of-Ten clean, no malloc, pi-free):

- `srmech_is_prime(n, *out)` — trial-division primality test (false for `n < 2`, true for 2 / 3, then test odd `d ≤ sqrt(n)`).
- `srmech_factor(n, primes[], exponents[], max_count, *out_count)` — trial-division prime factorisation returning sorted distinct primes + exponents. Caller-allocated fixed-size buffers; `SRMECH_ERR_OVERFLOW` if distinct-prime count exceeds `max_count`.
- `srmech_cyclic_period(a, n, max_k, *out_period)` — multiplicative order of `a` in `(Z/nZ)*` via trial-period (smallest `k > 0` with `a^k ≡ 1 mod n`). Bounded by `max_k`; `SRMECH_ERR_OVERFLOW` if period exceeds the bound. Requires `gcd(a mod n, n) == 1` (validated by detecting `a mod n == 0`).

Public Python surface at `srmech.amsc.primes` with native/fallback dispatch. Returns ordinary Python types (`bool`, `list[(int, int)]`, `int`) — no numpy dependency at this module level. Parity tests at `tests/test_primes_parity.py` cover reference values + Python-equivalence on random sweeps + native↔fallback parity.

Foundation for Task #218 Phase C2's cascade-period operations (Class J × Class I composition for cyclic-cascade orbital periods).

### Changed

- **ABI stays v2** — three new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_primes.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

## [0.4.0rc2] - 2026-05-15

### Added

**Task #217 Phase C1 — Class L (graph Laplacian) C parity.**

Second per-class C port in Phase C1's rc-stacked build-out. Class L is Spike #24's structural workhorse (instantiated at six of six bonus substrates per the cumulative cross-substrate audit) and the spectral substrate underpinning cascade-composition mass-spectrum reproduction.

Four new C symbols (all `uint32`/`double`, JPL Power-of-Ten clean, pi-free per `[[user_stance_pi_as_projection]]`):

- `srmech_graph_dense_adjacency` — `A` matrix from undirected edge list (self-loops add `2*w` to diagonal per standard convention).
- `srmech_graph_dense_laplacian` — `L = D − A` (combinatorial Laplacian).
- `srmech_graph_normalized_laplacian` — `L_sym = I − D^(−1/2) A D^(−1/2)` (isolated vertices get diagonal 0, not 1).
- `srmech_jacobi_eigvals` — symmetric Jacobi eigendecomposition with algebraic `c, s` computation (no trig calls). In-place on caller-owned matrix.

`N` bound: `SRMECH_LAPLACIAN_MAX_NODES = 256` caps the stack-allocated degree / row-scaling buffers (~2 KB) for embedded-safe execution. Larger graphs return `SRMECH_ERR_OVERFLOW` and the Python wrapper falls back to `numpy.linalg.eigvalsh`.

Public Python surface at `srmech.amsc.laplacian` (`dense_adjacency`, `dense_laplacian`, `normalized_laplacian`, `jacobi_eigvals`) with native/fallback dispatch. Parity tests at `tests/test_laplacian_parity.py` cover reference values, spectral-property invariants (PSD, row-sum=0, normalised eigvals in [0, 2]), and a native↔fallback random sweep.

Pi-free decision: cyclic-graph closed-form spectra (the pi-bearing `2(1−cos(2πk/n))` shortcut) are NOT shipped on the C surface — those are downstream projections of Class I's integer-cyclic upstream. Users computing cyclic-graph spectra compose Class I (modular arithmetic) with Class L's dense build + Jacobi, or use numpy at the Python layer.

### Changed

- **numpy is now a hard runtime dependency** (added to `[project.dependencies]`). Class L (graph Laplacian) and the upcoming Class M (HDC bind/bundle) are fundamentally array-numerical; numpy provides the ergonomic Python surface + fallback path. Pyodide environments install numpy via micropip. `srmech.amsc.cyclic` (Class I, integer-only) does not import numpy.
- **ABI stays v2** — four new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_laplacian.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)` — no CMakeLists edits required. Existing libm linkage covers the `sqrt` calls.

### Roadmap

Phase C1 continues — remaining classes (B/D/E/F/G/H/J/K/M/N + Class O if accepted) ratchet as further rc-stacked additions under `0.4.0rcN`. Class D and Class F likely Python-only-by-design per srmech CLAUDE.md operational-scope-clarification. Phase C1 closes at clean `0.4.0`.

## [0.4.0rc1] - 2026-05-15

### Added

**Task #217 Phase C1 — Class I (cyclic-group / modular arithmetic) C parity.**

First per-class C port in the post-v0.2.0 Phase C1 build-out (Task #217 follows Task #201 Phase B's ratchet). Class I appears in Spike #24's cumulative cross-substrate audit at five of six bonus substrates (tactical / SHA-256 / MFO 3+7+1 / RNG / cascade composition) and is the foundation primitive for Task #218 Phase C2's cascade-composition operations.

Six new C symbols (all uint64_t, JPL Power-of-Ten clean, no malloc, fixed-bound loops, ≥2 asserts per function):

- `srmech_gcd(a, b, *out)` — Euclidean GCD (`gcd(0, 0) = 0`).
- `srmech_lcm(a, b, *out)` — LCM via GCD with `UINT64_MAX` overflow guard.
- `srmech_mod_add(a, b, n, *out)` — `(a + b) mod n`, overflow-safe.
- `srmech_mod_mul(a, b, n, *out)` — `(a * b) mod n` via russian-peasant doubling (portable; no `__int128` / `_umul128`).
- `srmech_mod_pow(a, k, n, *out)` — `a^k mod n` via square-and-multiply.
- `srmech_mod_inv(a, n, *out)` — modular inverse via extended Euclidean (requires `n ≤ INT64_MAX` for int64 intermediate coefficients).

Public Python surface at `srmech.amsc.cyclic` with native/fallback dispatch (parity tests in `tests/test_cyclic_parity.py`).

### Changed

- **ABI stays v2.** Six new symbols are pure additions per the Phase B4 convention; existing ABI-tied wire formats unchanged.
- **CMake**: `srmech_cyclic.c` is picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)` — no CMakeLists.txt edits required.
- **JPL audit**: `srmech_cyclic.c` participates in the pytest ratchet at `tests/test_jpl_audit.py` (Rules 1/3/4/5/8 mechanically detected).

### Roadmap context

This release is the start of Task #217 Phase C1's per-class C-parity build-out. Phase C1 ratchets remaining primitive classes (B/D/E/F/G/H/J/K/L/M/N + Class O if accepted) as rc-stacked additions under `0.4.0rcN` per `[[feedback_rc_stacking_versioning]]`, with the clean `0.4.0` ship at Phase C1 close. Class D and Class F are likely Python-only-by-design (binding-layer per srmech CLAUDE.md operational-scope-clarification); each class gets a per-port decision recorded in CLAUDE.md.

Phases C2 (Task #218 — MFO/SM/QM operations layer), C3 (Task #219 — per-class CLI help-arg discipline), and C4 (Task #220 — tool-schema extension for catalog files) build on Phase C1's foundation.

## [0.3.1] - 2026-05-14

### Production cut bundling rc1 + rc2 (no code change from 0.3.1rc2)

The 0.3.1rc2 → 0.3.1 transition contains only version-string bumps in
the four SSOT locations plus this CHANGELOG header. Bundles both POC
findings from the chess-spectral simple-profile migration ([Task #211](../...)):

- **rc1**: entry-point Form-1 (package-only) support — every
  real-world Python plugin discovery system uses
  `"package_name"` rather than `"package:CONST"`.
- **rc2**: `[profile.tool_schema].extension_file` was parsed at
  validation time but never loaded at activation time, so profile
  tool entries silently went missing from the registry.

Both fixes are backward-compatible additions to the loader; no
v0.3.0 API breakage.

End-to-end verification (Windows / Python 3.14, clean venv, TestPyPI
0.3.1rc2 + chess-spectral 1.19.0 pre-release wheel):

```
srmech version: 0.3.1rc2
=== chess profile activation ===
Profile: chess v1.19.0
=== tool_schema integration ===
chess tools registered: 8
 - chess.encode_2d : Spectral 2D chess encoder...
 - chess.encode_4d : Spectral 4D chess encoder...
 - chess.fen_to_pos : Parse a FEN string into the 2D position dict...
 - chess.channel_energies : Compute per-channel L² energy...
 - chess.encode_2d_pure_phase : Integer-arithmetic 2D chess encoder...
 - chess.phase_only_pseudo_legal_moves : Pure-phase pseudo-legal...
 - chess.encode_2d_bip_hybrid : BIP-hybrid sign × magnitude...
 - chess.decode_2d_bip_hybrid : Inverse of encode_2d_bip_hybrid...
=== bridge call still works ===
encode_2d shape: (640,)
```

Profile pattern (ADR-0001) is now exercised by a real third-party-style
package. ADR §7 Step 1 (chess POC) drives ADR §7 Step 2 (ephemerides
plugin-profile) next.

See [0.3.1rc2] + [0.3.1rc1] below for the full bug + fix narratives.

## [0.3.1rc2] - 2026-05-14

### Fixed — `[profile.tool_schema]` extension file loading

Second issue surfaced by the chess-spectral simple-profile POC (Task #211).
v0.3.0–v0.3.1rc1: the profile loader's `_validate_descriptor` accepted
`[profile.tool_schema]` blocks at parse time, but `Profile.__init__`
never actually loaded the referenced extension TOML at activation
time. Profiles declaring tool-schema extensions activated cleanly but
contributed zero `ToolEntry` records to `srmech.amsc.tool_schema`.

Repro (v0.3.1rc1 against chess-spectral 1.19.0):

```python
>>> import srmech
>>> p = srmech.profile("chess")  # activates cleanly
>>> from srmech.amsc.tool_schema import get_tool_schema
>>> get_tool_schema().by_owner("chess")
[]   # ← should have been 8 entries from chess-spectral's
     # _srmech_tool_schema.toml
```

Fix in `Profile.__init__`: new `_load_tool_schema_extension()` step.
After bridge resolution + catalog registration + native plugin
loading, if `[profile.tool_schema].extension_file` is declared, the
loader resolves it inside the package directory and registers every
`[[tools]]` block via `srmech.amsc.tool_schema.register_profile_tools()`
with `owner = profile.name`.

Verified against chess-spectral's 8-tool extension file
(`_srmech_tool_schema.toml`):

```
chess tools registered: 8
 - chess.encode_2d : Spectral 2D chess encoder...
 - chess.encode_4d : Spectral 4D chess encoder...
 - chess.fen_to_pos : Parse a FEN string into the 2D position dict...
 ...
```

Backward-compatible: profiles without a `[profile.tool_schema]` block
take the no-op path. Profiles with malformed extension files raise
`InvalidProfileError` at activation time, before any bridge surface
is bound — fail-loud-at-boot per ADR-0001 §5.5.

## [0.3.1rc1] - 2026-05-14

### Fixed — entry-point Form-1 (package-only) support for profile loader

v0.3.0's `_resolve_entry_point_toml` only handled `"package:CONST"`
attribute-style entry-point declarations (Form 2). Every real-world
Python plugin discovery system (pytest, flake8, setuptools_scm) uses
the simpler `"package_name"` form — and that's what surfaced
immediately during the **chess-spectral simple-profile POC migration**
([Task #211](https://github.com/lemonforest/mlehaptics/...),
[ADR-0001](../adr/0001-profile-pattern.md) §7 Step 1).

Symptom (v0.3.0 against chess-spectral 1.19.0's declaration):

```python
>>> import srmech
>>> srmech.list_profiles()
{'chess': ProfileStatus(name='chess', ..., status='invalid',
   diagnostic="entry-point 'chess' ('chess_spectral') resolved to
   module; expected Path or str pointing at srmech_profile.toml")}
```

Fix in `srmech/profile_loader.py`:
`_resolve_entry_point_toml` now handles **three** entry-point value
forms:

1. **Package only** (recommended, boilerplate-free):
   `chess = "chess_spectral"`. Loader uses
   `importlib.resources.files(package) / "srmech_profile.toml"`.
2. **Path/str attribute** (explicit, v0.3.0 form):
   `chess = "chess_spectral:_SRMECH_PROFILE_PATH"`. Unchanged.
3. **Callable returning a Path/str** (for descriptors generated at
   import time): `chess = "chess_spectral:_get_path"`. Unchanged in
   intent — was always documented as supported but never wired.

Backward-compatible: every v0.3.0 caller continues to work; Form 1
is purely additive.

ADR-0001 §7 Step 1 explicitly anticipated this kind of finding:
> "Lessons learned go back into the ADR + the §3 schema if needed."

The schema doesn't change; only the loader implementation. The
authoring guide (Task #214) will recommend Form 1 as canonical.

### Tests

- New: `test_entry_point_form_1_package_only` (synthesised package
  on tmp_path; verifies `importlib.resources.files()` resolution).
- New: `test_entry_point_form_2_path_constant` (Form 2 regression).
- New: `test_entry_point_form_2_string_constant` (Form 2 regression).
- New: `test_entry_point_form_3_callable_returning_path`.
- New: `test_entry_point_unknown_type_rejected` (negative case).

### Why a patch bump (not minor)

The fix is purely additive to the loader's accepted inputs.
v0.3.0's documented behaviour (Form 2) continues to work identically.
No new public surface, no API breakage. SemVer patch is correct.

## [0.3.0] - 2026-05-14

### Production cut of the v0.3.0 ship (no code change from 0.3.0rc1)

The 0.3.0rc1 → 0.3.0 transition contains only version-string bumps
in the four SSOT locations (`pyproject.toml`, `pyproject-pure.toml`,
`srmech/version.py`, `c/include/srmech.h`) plus this CHANGELOG header.

TestPyPI verification (clean venv, Windows / Python 3.14):

```
version: 0.3.0rc1
HAS_NATIVE: True ABI: 2
tool_schema_version: 1.0
builtin tools: 6
list_profiles: {}
ProfileNotFoundError works: no profile named 'nonexistent'; enumerated profiles: []
All profile loader exports present: True
```

Native dispatch healthy, builtin AMSC tools self-register at amsc
import time, profile loader API complete. No issues surfaced through
the rc cycle; cutting straight to production.

See [0.3.0rc1] below for the full feature description.

## [0.3.0rc1] - 2026-05-14

### Added — Task #198 (`srmech.amsc.tool_schema`) + Task #199 (profile loader)

First implementation of the **profile pattern** specified in
[ADR-0001](../adr/0001-profile-pattern.md). Ships as v0.3.0rc1 to
TestPyPI for verification before the production v0.3.0 cut.

#### `srmech.amsc.tool_schema` — LLM-friendly introspection (Task #198)

New module that produces a single structured view of every callable
srmech exposes (and, post-profile-pattern, every profile-contributed
callable). API:

- **`get_tool_schema()`** — returns a `ToolSchema` dataclass with
  every registered `ToolEntry`. JSON-serialisable via `.to_jsonable()`.
- **`tool_schema_view()`** — convenience wrapper returning the same
  as a dict.
- **`register_tool(entry)`** — imperative registration; idempotent
  on identical re-registration; raises `ToolSchemaConflictError`
  on name collision with different content.
- **`register_profile_tools(profile_name, entries)`** — batch path
  used by the profile loader; enforces `entry.owner == profile_name`
  so profile-attribution can't drift.
- **`unregister_profile_tools(profile_name)`** — removes every entry
  owned by the named profile (used on profile deactivation).
- **`load_extension_file(path, owner)`** — parses a profile's
  TOML extension file into a list of `ToolEntry` ready for batch
  registration.

srmech's own AMSC functions (sha256_bytes, read_ndjson,
descriptor_hash, list_attested_sources, get_attested_dataset,
register_attested_root) are registered at AMSC import time with
their parameter signatures, return shapes, and smoke-test hints.

#### `srmech.profile_loader` — profile activation API (Task #199)

New module implementing ADR-0001's profile pattern:

- **`srmech.list_profiles()`** — enumerates every installed profile
  via `importlib.metadata.entry_points(group="srmech.profiles")`.
  **Eager at first call** per ADR §5.5 (JPL Rule 2 analog); cached
  for process lifetime.
- **`srmech.profile(name)`** — activation API. Returns a `Profile`
  object exposing bridge surfaces as attributes. On first call for
  a given profile-version:
  - Validates the descriptor against the v1.0 schema (strict).
  - Checks smoke-test cache at
    `~/.cache/srmech/profile_smoke_tests/<name>-<version>.toml`.
  - Cache miss / version bump → re-runs smoke test (bridge surfaces
    importable + callable; catalog roots exist).
  - On smoke-test pass: registers catalog roots into srmech's
    universal bridge; loads native plugin via ctypes if
    `[profile.native]` declared, performs ABI handshake; caches
    result; returns `Profile`.
  - On smoke-test fail: raises `SmokeTestFailedError`; profile not
    activated; cache records the failure (re-runs on next process).
- **`Profile.<bridge_surface>(args)`** — invoke a profile-declared
  bridge function.
- **`Profile.native`** — bound ctypes library (plugin tier only).

Error hierarchy:
`ProfileError` ⊂ `Exception`
  - `ProfileNotFoundError` — unknown profile name
  - `InvalidProfileError` — descriptor failed validation
    - `ProfileSchemaVersionError` — descriptor against unknown schema version
  - `SmokeTestFailedError` — smoke test failed (cache may record)
  - `AbiMismatchError` — plugin's `abi_version()` mismatch

#### JSON Schema for `srmech_profile.toml`

[`docs/srmech/adr/0001-profile-pattern.schema.json`](../adr/0001-profile-pattern.schema.json)
renders ADR §3 into a machine-checkable shape. The loader uses a
pure-Python minimal validator that covers the load-bearing
constraints (required fields, name/version patterns, schema-version
match); the full JSON Schema is the documented source-of-truth for
profile authors and for third-party validation tools.

#### `[profile.interpreted]` is reserved (ADR §5.6)

Profiles declaring an `[profile.interpreted]` block (Julia / R / Lua /
subprocess runtimes) parse cleanly but emit a `FutureWarning` and
the block is ignored. The namespace is reserved in v1.0 of the
schema so adding interpreted-runtime adapters later (a follow-up
ADR) won't be a breaking change.

#### Tests

- **`tests/test_tool_schema.py`** *(NEW)* — 11 tests covering
  imperative + extension-file registration, idempotency, conflict
  detection, owner-tag enforcement, by_owner filter, lookup,
  serialisation round-trip.
- **`tests/test_profile_loader.py`** *(NEW)* — 14 tests covering
  schema validation paths (minimal valid; missing fields; bad
  patterns; full plugin-tier `[profile.native]`; reserved
  `[profile.interpreted]` block warns), public API surface, and
  error-class exports.

All v0.2.0 tests (sha256 parity, NDJSON parity, JPL audit ratchet,
etc.) continue to pass unchanged.

#### Version

This is a **minor bump** (0.2.0 → 0.3.0). Adds new APIs; no breaking
changes to v0.2.0's public surface. C ABI still 2.

## [0.2.0] - 2026-05-14

### Task #201 Phase B7 — production cut to PyPI

First **production PyPI** release of native-C-accelerated srmech.
Content is functionally identical to **`0.2.0rc2`** on TestPyPI;
only the version string changes (rc-suffix stripped) and the
docs lose the rc-cycle commentary. The tag-routing claim in
`srmech-publish.yml` directs a non-rc tag to the production PyPI
trusted-publisher environment.

#### What v0.2.0 ships, headline

The Task #201 build-out (rc3 → rc9 + rc1 → rc2 = 11 TestPyPI
rcs across phases B1 through B7) turned srmech from a pure-Python
AMSC framework (the v0.1.0 ship) into a native-C-accelerated
multi-platform package at peer quality with ephemerides-spectral:

- **Native C library** (`srmech_sha256_hex`, `srmech_ndjson_iter`,
  + version / ABI accessors) shipped under `srmech/_native/`
  inside platform-tagged wheels.
- **15-cell cibuildwheel matrix** — Linux (manylinux_2_28) × macOS
  × Windows × py3.10 / 3.11 / 3.12 / 3.13 / 3.14. Each cell runs
  `test_native_sha256.py` + `test_format.py` to verify the wheel's
  native dispatch + sha256 parity post-build.
- **scikit-build-core + CMake** build backend (Phase B2). Pure-
  Python fallback for Pyodide / WASM lives in `pyproject-pure.toml`
  (hatchling backend, swapped in for the `build-pure-wheel` CI
  job).
- **All `hashlib.sha256` callsites** in `srmech.amsc` route through
  `format.sha256_bytes()` → native dispatch when available;
  hashlib fallback otherwise.
- **JPL Power-of-Ten audit** complete (Phase B6). 10/10 rules
  satisfied modulo one documented Rule 9 callback deviation; ratchet
  enforced by `tests/test_jpl_audit.py` (6 mechanical tests, pinned
  exemption list) + `pedantic-build` CI job (3-cell:
  Linux gcc / macOS clang / Windows MSVC × `-DSRMECH_PEDANTIC=ON`
  → `-Werror` / `/WX`).
- **Description-match guard** between `pyproject.toml` and
  `pyproject-pure.toml` (rc9 post-mortem). Both descriptions
  carry the same 450-char Summary: "*Stored-Relationship
  Mechanism research package: home of the Attested Multi-Source
  Collector/Catalog (AMSC) framework — ...*".
- **AMSC dual-name framing** (rc2). Both *Collector* (at fetch
  time) and *Catalog* (at read time) work; same abbreviation;
  pick whichever fits the lifecycle stage.
- **Development Status classifier** bumped `3 - Alpha` → `4 - Beta`
  (rc9).

#### Cross-package readiness

ephemerides-spectral 0.26.1rc1 (the parallel-session ship) pins
`srmech>=0.1.1rc9` with a TestPyPI `PIP_EXTRA_INDEX_URL` override
to exercise the cibuildwheel matrix against the TestPyPI srmech
rcs. With v0.2.0 now on production PyPI, the next
ephemerides-spectral release will bump that floor to
`srmech>=0.2.0` and drop the TestPyPI override.

#### v0.1.0 status

Still on PyPI as the historical release. `pip install srmech`
without any version constraint now resolves to v0.2.0; users on
older Python paths can still pin `srmech==0.1.0` for the
pure-Python wheel.

#### History

See the rc-by-rc entries below for the full per-phase record:

- `0.2.0rc2` — AMSC "Collector/Catalog" dual-name wording
- `0.2.0rc1` — Phase B7 final TestPyPI gate (no-op version bump
  from rc9)
- `0.1.1rc9` — Metadata drift sweep ("Pure Python." → "Native C
  dispatch"; Dev Status 3-Alpha → 4-Beta; description-match guard)
- `0.1.1rc8` — Phase B6 JPL Power-of-Ten audit + ratchet
- `0.1.1rc7` — Phase B5 sha256 callsites routed through native
- `0.1.1rc6` — Phase B4 NDJSON streaming reader C port
- `0.1.1rc5` — Phase B3 SHA-256 C port + cibuildwheel matrix
- `0.1.1rc4` — Phase B2 scikit-build-core + pyproject-pure
- `0.1.1rc3` — Phase B1 C tree scaffolding
- `0.1.1rc1` / `rc2` — Earlier infrastructure cycles
- `0.1.0` — Initial AMSC-to-srmech refactor (pure-Python)

## [0.2.0rc2] - 2026-05-14

### Added — Task #201 Phase B7: AMSC dual-name wording ("Collector / Catalog")

Documents the dual reading of the **AMSC** abbreviation across
srmech's user-facing surface. **No code, no API, no ABI change**
— pure documentation polish discovered while reviewing the
0.2.0rc1 TestPyPI metadata.

#### The framing

**AMSC** abbreviates both:

- **Attested Multi-Source Collector** — at collection time
  (T1 fetch / T3 live query / re-bake lifecycle stages), the
  framework's adapter classes are *collecting* attested rows
  from upstream archives.
- **Attested Multi-Source Catalog** — after collection, the
  committed NDJSON SSOTs constitute a *catalog* of attested
  data that downstream packages register and query through the
  universal bridge.

Both names are correct; both abbreviate to AMSC; pick whichever
fits the lifecycle stage you're describing. One framework wearing
two hats.

#### Surfaces updated

- **`pyproject.toml` + `pyproject-pure.toml`** `[project].description`
  — "Attested Multi-Source Collector (AMSC)" →
  "Attested Multi-Source Collector/Catalog (AMSC)". 442 chars →
  450 chars (still under both the 480 soft cap and PyPI's 512
  hard cap).
- **`python/README.md`** — package-intro paragraph updated;
  new "Why 'Collector/Catalog'?" subsection explains the dual
  reading with the T1/T3-fetch vs read-time-query lifecycle
  framing.
- **`python/srmech/__init__.py`** docstring — package-level
  framing now leads with the dual name and gives a paragraph on
  the lifecycle-stage interpretation.
- **`python/srmech/amsc/__init__.py`** docstring — same dual-
  name framing at the AMSC subpackage level.
- **`docs/srmech/srmech_research_notebook.md` §0** — three-layer
  architecture's L1 paragraph gains a "Naming aside" note
  introducing both readings, with explicit lifecycle-stage
  cross-references (`list_attested_sources` etc.).
- **`docs/srmech/CLAUDE.md`** state snapshot bumped to reflect
  the rc2 ship.

#### Why TestPyPI rc rather than land-as-unreleased

Initial intent (per maintainer's "leave this as an unreleased
update" guidance) was to land the doc change on `main` without a
new rc; but per the project's TestPyPI-before-PyPI discipline,
any text that goes to production PyPI's Summary metadata should
have been visible on TestPyPI first. PyPI Summary drift (the
"Pure Python." bug at rc8 → rc9) was the specific failure mode
that motivated the description-match guard; landing the dual-name
wording without a TestPyPI round-trip would re-open the same
exposure. So we ship rc2 to TestPyPI and verify there, then v0.2.0
(no rc suffix) cuts to production PyPI carrying the rc2 text.

#### No code change

C ABI still **2**. Python public API surface unchanged. Wheel
content identical to rc1 modulo the description string +
docstrings. Pytest matrix unaffected (the
`test_native_version_and_abi` rc9-bump fix from rc1 keeps working).

## [0.2.0rc1] - 2026-05-13

### Task #201 Phase B7 — final TestPyPI rc before v0.2.0 production cut

No code changes from `0.1.1rc9`. This release exists to validate
the **v0.2.0** version string itself through one more TestPyPI
round-trip before the clean `srmech-v0.2.0` tag goes to
**production PyPI**. Discipline: TestPyPI before PyPI, always —
the rc-suffix auto-routing in `srmech-publish.yml` means a clean
non-rc tag IS the production gate; we want one last sanity
verification on the version string + metadata immediately before
the gate-passing tag.

#### Why a minor bump (0.1.1 → 0.2.0)

The rc3 → rc9 series turned srmech from a pure-Python AMSC
framework into a native-C-accelerated package with cibuildwheel
matrix + JPL Power-of-Ten audit + per-platform parity tests
covering 3 OS × 5 Python versions. That's a real capability
boundary, large enough that consumers of `srmech==0.1.0`
upgrading via `pip install -U srmech` are going on a substantive
ride. Minor bump signals that.

#### Cross-package readiness (parallel session shipped this)

While the srmech rc series was iterating, a parallel Claude
Code session verified srmech rc9 against the sister package
**ephemerides-spectral** (which depends on srmech as its AMSC
substrate per Task #197). The verification result lives at
[`docs/antikythera-maths/ephemerides-spectral/CHANGELOG.md`](../../antikythera-maths/ephemerides-spectral/python/CHANGELOG.md)
under `ephemerides-spectral 0.26.1rc1`. That rc shipped to
TestPyPI with `srmech>=0.1.1rc9` pinned + a
`PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/` test-env
override (Option B from the verification prompt), confirming
the cibuildwheel test matrix actually exercises against the
TestPyPI srmech rc rather than silently falling back to PyPI's
`srmech==0.1.0`. Cross-package integration confirmed green.

After srmech v0.2.0 ships to production PyPI, ephemerides-spectral
will bump its srmech floor `>=0.1.1rc9` → `>=0.2.0` and drop the
TestPyPI test-env override in its own follow-up release. That's
ephemerides-spectral's ship to plan, not srmech's.

#### Path forward

1. **This rc1** auto-ships to TestPyPI via the rc-suffix routing.
2. Maintainer verifies wheel install + native dispatch + sha256
   parity + ndjson parity end-to-end from a clean venv outside
   the repo tree.
3. If clean, maintainer bumps `0.2.0rc1` → `0.2.0` (drop the
   `rcN` suffix in all four SSOT files), merges that bump, and
   tags `srmech-v0.2.0`. That clean tag auto-routes to
   **production PyPI** via the workflow's environment-name claim.
4. After v0.2.0 lands on PyPI, ephemerides-spectral can bump
   its srmech floor; downstream consumers can upgrade via
   `pip install -U srmech`.

#### No ABI / API / behaviour change

C ABI version unchanged (still 2). Python public surface
unchanged. Wheel content identical to rc9 modulo the version
string. The `SRMECH_VERSION` macro updates in lockstep
(`0.1.1rc9` → `0.2.0rc1`) and the Python `_native.py` reads it
back through `srmech_version()` at load time.

## [0.1.1rc9] - 2026-05-13

### Fixed — PyPI metadata drift after Phase B3 (native code) landed

User-spotted drift on the TestPyPI project page: the Summary still
read "...Pure Python." even though Phase B3 (rc5) shipped native C
dispatch and Phase B4 (rc6) added the second native symbol. Both
`pyproject.toml` and `pyproject-pure.toml` had the stale claim
verbatim because the description text was copy-pasted between them
without revisiting the trailing sentence after each phase.

#### Fixed

- **`pyproject.toml` + `pyproject-pure.toml` `[project].description`**
  — replaced "Pure Python." with "Native C dispatch (SHA-256 +
  NDJSON line reader) with pure-Python fallback for Pyodide / WASM."
  Both files now carry identical 442-char descriptions (well under
  the 480-char soft cap; well under PyPI's 512-char hard limit).
- **`README.md` Status line** — refreshed to reflect the rc3→rc8
  arc and the impending v0.2.0 cut. Adds a one-liner clarifying
  the native-C + pure-Python-fallback architecture in the package
  intro paragraph.
- **`Development Status` classifier** — bumped from
  `3 - Alpha` → `4 - Beta` on both pyproject files. After 6 rc
  iterations including cibuildwheel matrix, JPL Power-of-Ten audit,
  Python/C parity tests, and pedantic-build CI on three platforms,
  "Beta" is the honest label. Same status ephemerides-spectral
  carries.

#### Added — description-match guard (defensive ratchet)

The publish workflow (`srmech-publish.yml`) and CI workflow
(`srmech-ci.yml`) already enforce **version-match** between
`pyproject.toml` and `pyproject-pure.toml`. The same guard pattern
now also asserts **description-match**: any drift between the two
descriptions fails CI with a clear error message including both
char counts. This catches future copy-paste drift before it can
reach a TestPyPI / PyPI upload.

PyPI's Summary metadata is per-project-version (not per-wheel), so
both wheels uploaded under the same version must carry the same
Summary text. The match guard formalises that invariant.

#### Audit scope

Reviewed every user-facing PyPI metadata surface for similar drift:

- ✅ `description` — fixed (both files).
- ✅ `Development Status` classifier — bumped.
- ✅ README Status line — refreshed.
- ✅ `keywords` — accurate (stored-relationship, mechanism, attested,
  provenance, ndjson, ground-proof, research). No change.
- ✅ `Topic :: Scientific/Engineering` classifier — accurate.
- ✅ `Programming Language ::` classifiers — match `requires-python`.
- ✅ `[project.urls]` — Homepage, Repository, Issues, Changelog,
  Notebook. Stable, no drift.
- ✅ Docstrings in `_native.py` / `format.py` / `c/README.md` that
  mention "pure-Python" — all referring to the fallback path
  correctly; no drift.

#### No ABI change

C surface unchanged from rc8. `SRMECH_ABI_VERSION` stays at 2.

## [0.1.1rc8] - 2026-05-13

### Added — Task #201 Phase B6: JPL Power-of-Ten audit

Formal audit of srmech's native C library against
[Holzmann's JPL Power-of-Ten rules](https://web.eecs.umich.edu/~imarkov/10rules.pdf).
Mirrors the pattern ephemerides-spectral applied via Tasks
#105–#110. **All ten rules satisfied** for srmech's C surface,
modulo one documented Rule 9 deviation (callback-based iterator).

#### Audit deliverables (`docs/srmech/c/JPL_AUDIT.md`)

- **Rule-by-rule compliance review** across all 3 C source files
  (`srmech_meta.c`, `srmech_sha256.c`, `srmech_ndjson.c`) + the
  public header `srmech.h`. ~500 LOC total.
- **Per-function line + assertion counts** with explicit exemption
  policy for trivial accessors (`srmech_version`,
  `srmech_abi_version`) and `static inline` arithmetic primitives
  (sha256 bit-rotation helpers).
- **Rule 9 deviation rationale** documented: the `srmech_ndjson_iter`
  callback is the smallest API surface satisfying Rules 3 + 4 simultaneously.

#### Code fix shipped in this audit pass

- **`srmech_ndjson_iter`** at rc6 was **76 lines** (Rule 4 violation:
  > 60 lines). The chunk-byte-loop body extracted into a new
  `static srmech_ndjson_process_chunk` helper along its natural
  state-update seam. Post-refactor: 51-line `iter` + 43-line
  `process_chunk`. Byte semantics identical; 18 ndjson parity
  tests re-ran clean.

#### Tests + CI ratchet

- **`tests/test_jpl_audit.py`** *(NEW)* — 6 mechanically-detectable
  ratchet tests:
  - Rule 1: no `goto` / `setjmp` / `longjmp` anywhere.
  - Rule 3: no `malloc` / `calloc` / `realloc` / `free` / `alloca`.
  - Rule 4: every function ≤ 60 lines (line-count regex + brace-
    depth scanner).
  - Rule 5: every non-exempt function has ≥ 2 assertions.
    Exempt list pinned (8 entries: 2 trivial accessors, 6 inline
    helpers); adding to the exempt list requires documenting
    rationale in JPL_AUDIT.md AND updating the test.
  - Rule 8: no multi-line macros / token-paste / `__VA_ARGS__`.
  - Audit doc present-and-mentions-all-rules sanity check.
- **`.github/workflows/srmech-ci.yml`** gains a **`pedantic-build`
  job** (3-cell matrix: Linux gcc / macOS clang / Windows MSVC)
  that runs `cmake -DSRMECH_PEDANTIC=ON` → builds with `-Werror`
  (POSIX) or `/WX` (MSVC). Any new warning fails CI. Rule 10
  toolchain-side enforcement.
- All 100 existing tests still pass; pytest collects 106 tests +
  the JPL ratchet's 6 = 112 total Python tests.

#### Verification (local)

- ``gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -O2`` builds all
  3 C files clean.
- `pytest tests/test_jpl_audit.py` → 6/6 pass.
- Full pytest suite (rc8 wheel install) → 106 passed + 1 skipped
  (1 native-dispatch skip when run from source tree).

#### Phase plan progress

| B1 | C tree scaffolding (rc3)                          | ✅ |
| B2 | scikit-build-core + pyproject-pure (rc4)          | ✅ |
| B3 | SHA-256 + cibuildwheel matrix (rc5)               | ✅ |
| B4 | NDJSON streaming reader (rc6)                     | ✅ |
| B5 | Route remaining sha256 callsites (rc7)            | ✅ |
| B6 | JPL Power-of-Ten audit (rc8)                      | this ship |
| B7 | v0.2.0rc1 final TestPyPI verify → v0.2.0 to PyPI  | next |

## [0.1.1rc7] - 2026-05-13

### Changed — Task #201 Phase B5: route remaining sha256 callsites through native dispatch

Phase B5's nominal title was "TOML canonical-serialization C port".
The shipped scope is narrower and better-fit: the actual hot work
(SHA-256 over canonicalised bytes) already has a native C path
from Phase B3. **B5 routes the four remaining ``hashlib.sha256``
callsites in srmech through ``sha256_bytes``** so every per-row
attestation hash benefits from the native dispatch.

Vendoring a TOML parser in C — the original phase plan's
implication — was rejected. CPython's ``tomllib`` + ``json.dumps``
canonicalisation is small, fast, and well-tested; replicating it
in C would 3× srmech's native-code surface area for no measurable
gain on the inputs srmech actually processes.

#### Wired callsites

- **`descriptor.descriptor_hash`** — the load-bearing one. Used by
  every adapter's ``attest()`` step to compute
  ``collector_descriptor_hash`` per row.
- **`catalog._file_sha256`** — hashes overlay NDJSON files for T2
  user-runtime-kernel attestation. Small files (< few MB), so
  slurp-and-hash via ``sha256_bytes`` is fine; streaming hashlib
  (which we'd need for huge files) would require a separate
  C-side multi-update API not yet ported.
- **`catalog._kernel_cache_hash`** — cache-key hash over the
  registered T2 overlay summary.
- **`adapters._base.parser_rule_hash`** — per-row attestation field
  documenting the parse-section rules.

#### What stays in Python

- TOML parsing (``tomllib.loads``) — stdlib, already C-accelerated.
- Canonical JSON serialisation (``json.dumps(sort_keys=True, ...)``) —
  stdlib, already C-accelerated.
- Streaming hashlib for the (currently unused) very-large-file case.

#### Tests

- **`tests/test_native_descriptor_hash.py`** *(NEW)* — 7 parity
  tests:
  - 3 descriptor-shape fixtures (minimal, comments + odd-spacing,
    deeply-nested keys) comparing native-routed ``descriptor_hash``
    to a pure-Python hashlib reference computation.
  - ``catalog._file_sha256`` parity vs streaming hashlib.
  - ``adapters._base.parser_rule_hash`` parity vs hashlib.
  - Defensive ratchet asserting all four wired callsites resolve to
    the same native path (catches accidental re-introduction of
    direct ``hashlib.sha256`` calls).
- Full pytest suite (100 tests + 1 skip) all green under native
  wheel install on Windows MSVC + Python 3.14.

#### No ABI change

C surface area unchanged from rc6. SRMECH_ABI_VERSION stays at 2.

## [0.1.1rc6] - 2026-05-13

### Added — Task #201 Phase B4: NDJSON streaming reader C port

Second C/Python parity surface. Native ``srmech_ndjson_iter`` does
file-IO + line tokenisation in C; JSON parsing stays in Python.
Byte-exact line-set agreement pinned by the new pytest parity
suite in ``tests/test_native_ndjson.py`` (18 tests including
chunk-boundary span + max-line-overflow + CRLF / mixed-EOL fixtures).

#### C side (`docs/srmech/c/`)

- **`src/srmech_ndjson.c`** *(NEW)* — streaming line reader.
  Reads 64 KiB chunks via ``fread``; assembles partial lines into a
  static 1 MiB buffer (single-thread contract); invokes the caller's
  callback with ``(line, line_len, lineno, user)`` per non-empty
  line. Empty lines are silently skipped but ``lineno`` still
  advances, so callback-side error messages line up byte-exactly
  with the file (verified by ``test_read_ndjson_malformed_line_lineno_correct``).
  CR-stripping at line boundaries matches Python's
  ``raw.rstrip("\r\n")``.
- **`include/srmech.h`** — callback typedef gains ``size_t lineno``
  parameter; ``SRMECH_ABI_VERSION`` bumped to **2**.
- **`src/srmech_meta.c`** — ``srmech_abi_version()`` now returns the
  macro indirectly so a missed manual bump can't silently lie.

#### Python side (`docs/srmech/python/srmech/amsc/`)

- **`_native.py`** —
  - ``EXPECTED_ABI_VERSION = 2`` (matches C-side bump).
  - ``_NDJSON_LINE_CB`` — ctypes ``CFUNCTYPE`` mirroring the
    4-argument C callback typedef.
  - ``ndjson_lines_c(path) -> list[(lineno, bytes)]`` — Python
    wrapper that runs the native iterator under a ctypes callback
    and collects ``(lineno, line_bytes)`` tuples.
  - ``NativeNDJsonError`` — distinct from ``MPRValidationError``
    because the failure is upstream of JSON parsing (file IO or
    overflow). Translated to ``OSError`` at the ``format.read_ndjson``
    boundary so callers see consistent semantics.
- **`format.py`** — ``read_ndjson()`` dispatches via the native
  iterator when ``HAS_NATIVE`` is True; pure-Python streaming path
  remains unchanged. JSON parsing (``json.loads`` +
  ``MPRRecord.from_json_line``) stays in Python on both paths.

#### Tests

- **`tests/test_native_ndjson.py`** *(NEW)* — 18 parity tests:
  12 fixture inputs (empty file, no-trailing-newline, CRLF / mixed-EOL,
  blank-line patterns, long lines, 100-record stress, etc.) + the
  ``format.read_ndjson`` dispatch test + lineno-fidelity test +
  missing-file ``OSError`` test + 1000-record stress + chunk-
  boundary span test + ``SRMECH_ERR_OVERFLOW`` test (1.25 MiB line
  rejection).
- All 59 existing tests still pass; all 18 native-sha256 tests
  still pass (ABI v2 lift didn't break the v1 surface).

#### Notes on design

- **No JSON parsing in C.** srmech's hot path is the file-IO + line
  tokenisation overhead (Python's text-mode line iteration has
  per-line allocator pressure that adds up across thousand-row
  catalogs). Doing the JSON parse in C would need a vendored JSON
  parser; bytes returned to Python and parsed via
  ``MPRRecord.from_json_line`` is byte-equivalent and avoids that
  surface-area expansion.
- **Static 1 MiB line buffer.** Trade-off: ``srmech_ndjson_iter`` is
  not thread-safe. The two callsites today (Python
  ``format.read_ndjson`` and any future C-side parity test) are
  serial. Phase B6 audit may revisit, but for srmech's data-pipeline
  workload — read a catalog file once, iterate — single-thread is
  the correct model.
- **Eager line collection.** The native path returns a list rather
  than a generator. For the catalog files srmech actually reads
  (small, few KB to a few MB), the eager materialisation is fine.
  If a future use case wants a true generator, the callback can be
  wired to a ``queue.Queue`` + worker thread, but we're not paying
  that complexity until a real need surfaces.

## [0.1.1rc5] - 2026-05-13

### Added — Task #201 Phase B3: SHA-256 C port (first native symbol)

First C/Python parity surface in srmech. Native ``srmech_sha256_hex``
replaces ``hashlib.sha256`` on the hot path used by every adapter's
``attest()`` step. Byte-exact agreement pinned by the new pytest
parity suite in ``tests/test_native_sha256.py`` (18 tests) plus the
C-side smoke tests in ``c/test/test_srmech_sha256.c`` (12 assertions
against FIPS 180-4 fixtures + padding-boundary edge cases).

#### C side (`docs/srmech/c/src/`)

- **`srmech_sha256.c`** — self-contained SHA-256 (FIPS 180-4). No
  OpenSSL / libcrypto dependency. ~200 lines, JPL-Power-of-Ten-
  compatible (bounded loops, no malloc, no goto, ≥2 asserts/fn).
  Public entry: ``srmech_sha256_hex(data, data_len, out_hex)``.
- **`srmech_meta.c`** — ``srmech_version()`` + ``srmech_abi_version()``
  metadata accessors. Called by the Python ctypes shim at load time
  to verify ABI agreement before binding.

The header (`docs/srmech/c/include/srmech.h`) grows
``SRMECH_ABI_VERSION = 1`` and declarations for the three new
symbols.

#### Python side (`docs/srmech/python/srmech/amsc/`)

- **`_native.py`** *(NEW)* — ctypes wrapper mirroring
  ``ephemerides_spectral/_native_bip.py``:
  - ``HAS_NATIVE`` boolean — guards every callsite.
  - ABI-version check at load time; mismatch falls back to Python
    silently (LOAD_ERROR is populated).
  - Three-strategy library discovery: ``srmech.__path__`` walk,
    relative-to-module-file, ``importlib.metadata.files()`` fallback.
    The third strategy is load-bearing for scikit-build-core editable
    installs where the .py files live in the source tree but the
    CMake-installed .so/.dll/.dylib lives in site-packages.
  - ``sha256_hex_c(data) -> str`` — native entry. Handles empty
    bytes correctly (mirrors hashlib.sha256(b"") semantics).
- **`format.py`** — ``sha256_bytes()`` now dispatches to native
  when available, falls back to ``hashlib`` otherwise. The
  user-facing API is unchanged; the implementation is one
  branch deeper.

#### Tests

- **`tests/test_native_sha256.py`** *(NEW)* — 18 parity tests:
  15 fixture inputs (empty, FIPS B.2, B.3, padding boundaries at
  55/56/63/64/65/119/128 bytes, 1 KiB, 64 KiB, 256 KiB),
  ``format.sha256_bytes`` dispatch test, version/ABI lock test,
  200-input randomised parity test. Auto-skipped when
  ``HAS_NATIVE`` is False (pure-Python wheel / Pyodide install).
- **`c/test/test_srmech_sha256.c`** *(NEW)* — 12 C-side asserts
  against FIPS 180-4 vectors + padding edge cases. Exits 0 on
  all-pass.

#### Build

- **`pyproject.toml`** — Phase B2's ``wheel.py-api = "py3"`` +
  ``wheel.platlib = false`` overrides REMOVED. The wheel is now
  legitimately platform-tagged (e.g.
  ``srmech-0.1.1rc5-cp312-cp312-linux_x86_64.whl``) and contains
  ``srmech/_native/libsrmech.{so,dll,dylib}``.
- **`.github/workflows/srmech-publish.yml`** —
  ``build-wheel`` sanity check inverted: rejects py3-none-any
  output (would indicate CMake short-circuited and the .so is
  missing), requires ``srmech/_native/`` to contain a .so / .dll /
  .dylib in the wheel.

#### Phase B7 follow-up

The ``build-wheel`` job still runs on a single Ubuntu cell, so only
the Linux wheel is published at rc5. Mac / Windows users on TestPyPI
get the pure-Python wheel (built by ``build-pure-wheel``) and the
pure-Python ``hashlib`` fallback. Phase B7 adds the cibuildwheel
matrix that produces wheels for all platform/Python combinations.

## [0.1.1rc4] - 2026-05-13

### Infrastructure — Task #201 Phase B2: scikit-build-core + pyproject-pure swap

Switches srmech's build backend from hatchling to **scikit-build-core +
CMake**, mirroring ephemerides-spectral. Adds the
`pyproject-pure.toml` hatchling-fallback file for the Pyodide / WASM
build path. Rewrites `srmech-publish.yml` with the three-job shape
(scikit-build-core wheel + sdist + pure-Python wheel) that mirrors
`ephemerides-spectral-publish.yml`.

**Phase B2 still ships py3-none-any wheels** — until Phase B3 lands
real C code in `docs/srmech/c/src/`, the CMake step short-circuits
to "no library" and the wheel is tagged py3-none-any via the
`wheel.py-api = "py3"` + `wheel.platlib = false` overrides in
pyproject.toml. Both overrides come back OUT at Phase B3 so the
wheel becomes legitimately platform-tagged once the native binary
is real.

#### Added — `pyproject-pure.toml`

Parallel pyproject mirroring `docs/antikythera-maths/ephemerides-spectral/python/pyproject-pure.toml`:

- Uses `hatchling` backend instead of `scikit-build-core`.
- Same `[project]` block (name, version, deps, classifiers, urls) so
  the pure wheel and the platform wheel are interchangeable at
  install time.
- Excludes `srmech/_native/*` from both wheel + sdist so accidental
  rebuild artifacts can't leak in.
- Version-locked to `pyproject.toml`'s version by a workflow guard
  (see "Verify pyproject-pure.toml version matches main" step).

#### Changed — `pyproject.toml`: hatchling → scikit-build-core

- `build-system.requires = ["scikit-build-core>=0.10", "cmake>=3.23"]`
- `build-system.build-backend = "scikit_build_core.build"`
- New `[tool.scikit-build]` block:
  - `cmake.source-dir = ".."` points at `docs/srmech/CMakeLists.txt`
  - `wheel.packages = ["srmech"]`
  - `wheel.py-api = "py3"` + `wheel.platlib = false` — Phase B2 only,
    keeps the wheel py3-none-any while CMake validates the
    infrastructure. Removed at Phase B3.
  - `sdist.include` adds the C tree one directory up (the same
    pattern ephemerides-spectral uses for its CMakeLists.txt + c/).
- `[project.optional-dependencies].dev` gains `scikit-build-core>=0.10`
  and `cmake>=3.23`; retains `hatchling` for the pyproject-pure swap
  build path.

#### Changed — `.github/workflows/srmech-publish.yml`

Replaced the single-`build` job with a three-job pattern mirroring
`ephemerides-spectral-publish.yml`:

- **`build-wheel`** — scikit-build-core wheel via `python -m build
  --wheel` (the `--wheel` flag skips the sdist→wheel detour that
  trips scikit-build-core's `cmake.source-dir=".."` indirection when
  the sdist is unpacked).
- **`build-sdist`** — `python -m build --sdist`, twine-strict-check.
- **`build-pure-wheel`** — swaps in `pyproject-pure.toml` over
  `pyproject.toml` (saved as `.platform`), runs hatchling build,
  restores. Includes the version-match guard + PyPI 512-char
  description guard, copied wholesale from ephemerides-spectral's
  workflow.
- **`publish`** — `needs: [build-wheel, build-sdist, build-pure-wheel]`.
  Same rc-routing logic; `cp -n` dedupe in the artefact-collection
  step handles the case where build-wheel and build-pure-wheel produce
  identically-named wheels at Phase B2 (will not happen at Phase B3+
  when build-wheel becomes platform-tagged).

#### Phase B7 follow-up

`build-wheel` at Phase B7 graduates from a single Ubuntu cell to a
cibuildwheel matrix (Linux / macOS / Windows × py3.10–3.14). The
trigger for that promotion: C/Python parity tests passing in CI
across all three platforms (Phase B5 complete).

## [0.1.1rc3] - 2026-05-13

### Infrastructure — Task #201 Phase B1: srmech C scaffolding

First phase of the **srmech build-out to peer-quality with
ephemerides-spectral** (Task #201). Ships the C tree scaffolding so
Phase B2 can wire scikit-build-core in next. **Pure-Python wheel
contents are byte-identical to rc2** — this release adds files outside
the wheel, no API changes, no behaviour changes.

#### Added — C tree scaffolding (`docs/srmech/c/` + `docs/srmech/CMakeLists.txt`)

Mirrors `docs/antikythera-maths/ephemerides-spectral/c/` layout:

- `c/include/srmech.h` — public C API header. Status enum
  (`srmech_status_t`), version macros, and forward declarations
  for the three planned symbols (`srmech_sha256_hex`,
  `srmech_ndjson_iter`, `srmech_toml_canonical_hash`). No
  definitions yet — those land in Phases B3–B5.
- `c/src/.gitkeep` — empty source directory placeholder.
- `c/test/.gitkeep` — empty test directory placeholder.
- `c/Makefile` — local build/test/parity flow mirroring
  ephemerides-spectral's Makefile. Phase B1 targets noop
  gracefully (no .c files → no .a archive); Phase B3 onward they
  do real work.
- `c/README.md` — phase plan, layout, build instructions.
- `c/JPL_AUDIT.md` — JPL Power-of-Ten audit log placeholder
  (populated in Phase B6).
- `c/.gitignore` — `build/`.
- `c/.pages` — mkdocs nav stub.
- `CMakeLists.txt` (at `docs/srmech/`) — top-level CMake driver,
  mirrors `docs/antikythera-maths/ephemerides-spectral/CMakeLists.txt`.
  At Phase B1 it short-circuits library creation when `c/src/*.c`
  is empty; Phase B2 wires it into pyproject.toml via
  scikit-build-core's `cmake.source-dir = ".."`.

#### Why Phase B1 stops here

The scaffolding is intentionally **inert at rc3**: no .c files means
no library is built, the existing hatchling pyproject.toml backend is
unchanged, and the wheel content is byte-identical to rc2. This
verifies the scaffolding doesn't disturb the existing build before
Phase B2 starts moving the build backend.

#### Phase plan (Task #201 B1–B7)

| Phase | Deliverable                                    | Version    |
| ----- | ---------------------------------------------- | ---------- |
| B1    | C tree scaffolding (this release)              | `0.1.1rc3` |
| B2    | scikit-build-core + CMake + pyproject-pure     | `0.1.1rc4` |
| B3    | `srmech_sha256_hex` — first symbol + parity test | `0.1.1rc5` |
| B4    | `srmech_ndjson_iter` — streaming NDJSON reader | `0.1.1rc6` |
| B5    | `srmech_toml_canonical_hash` — descriptor hash | `0.1.1rc7` |
| B6    | JPL Power-of-Ten audit + JPL_AUDIT.md          | `0.1.1rc8` |
| B7    | cibuildwheel matrix + production v0.2.0 cut    | `0.2.0`    |

Each rc auto-routes to TestPyPI via `srmech-publish.yml`'s rc-suffix
gate; the non-rc `0.2.0` tag is the human-in-loop gate for
production PyPI.

## [0.1.1rc2] - 2026-05-13

### Fixed — hallucination in shipped metadata

- **`pyproject.toml` description, `README.md`, `srmech/__init__.py` docstring**: corrected the package's expanded name from the hallucinated "spectral-resonance mechanism" to the correct **Stored-Relationship Mechanism** (per the srmech research notebook title `# Stored-Relationship Mechanism (srmech) — Research Notebook` and the project memory `project_stored_relationship_mechanism_spike.md`). The error was caught in the TestPyPI verification of v0.1.1rc1 — the wrong text shipped to TestPyPI as srmech-0.1.1rc1's PyPI Summary metadata; rc2 corrects it.
- **`pyproject.toml` keywords**: `"spectral-resonance"` → `"stored-relationship"`.
- **`README.md` Status line** updated to reflect current state (v0.1.0 on PyPI, v0.1.1rcN iterating on TestPyPI toward Task #201 peer-quality cut).

No behaviour or API changes. Wheel + sdist content identical to rc1 except for metadata fields.

## [0.1.1rc1] - 2026-05-13

### Infrastructure — Task #200 Phase A: revert cibuildwheel + add rc-routing

This release reverts the premature cibuildwheel adoption from PR #383
and introduces **rc-suffix auto-routing** in the publish workflow.

#### Reverted (the cibuildwheel mis-application)

- **`.github/workflows/srmech-publish.yml`** restored to the
  single-build-job shape (``python -m build`` produces sdist +
  py3-none-any wheel). cibuildwheel v3.x rejects pure-Python builds
  by design ("Build failed because a pure Python wheel was
  generated") — the matrix that PR #383 introduced was structurally
  incompatible with srmech's current pure-Python state. The
  ``ephemerides-spectral-publish.yml`` template adopted there
  legitimately uses cibuildwheel because that package ships a
  native C library; srmech does not (yet).
- **`docs/srmech/python/pyproject.toml`** ``[tool.cibuildwheel]``
  configuration block removed. Replaced with an explanatory comment
  documenting that cibuildwheel returns once srmech grows the
  C/Python parity surface (Task #201 Phase B).
- The failed ``srmech-v0.1.1`` tag was deleted before any artifact
  reached TestPyPI or PyPI; ``v0.1.0`` remains the current TestPyPI
  release.

#### Added — rc-suffix auto-routing (`srmech-publish.yml`)

- Tag ``srmech-vX.Y.ZrcN`` → publishes to **TestPyPI** (testpypi
  environment) automatically. No manual workflow_dispatch needed.
- Tag ``srmech-vX.Y.Z`` (no rc suffix) → publishes to **PyPI**
  (pypi environment). The act of tagging a non-rc version IS the
  human-in-loop gate for production releases.
- ``workflow_dispatch`` with ``target ∈ {testpypi, pypi}`` retained
  as a manual override path.
- Tag-version regex extended to accept rcN suffix:
  ``r"srmech-v(\d+\.\d+\.\d+(?:rc\d+)?)"``. The version-match
  check now also logs the routing decision so the run page makes
  TestPyPI-vs-PyPI obvious.
- Same rc-routing pattern simultaneously added to
  ``ephemerides-spectral-publish.yml`` for sibling consistency.

#### Version-discipline policy (going forward)

- **Every srmech release between now and peer-quality with
  ephemerides-spectral** ships as an rc on TestPyPI:
  ``0.1.1rc1``, ``0.1.1rc2``, ``0.1.2rc1``, …
- **No non-rc tag pushed** until srmech has Python/C parity, JPL
  Power-of-Ten C standard discipline, scikit-build-core build,
  and cibuildwheel matrix legitimately producing platform wheels.
- Each rc-tagged release is auto-shipped to TestPyPI; the next rc
  iteration is the response to whatever the prior rc-test surfaced.

#### Tests + parity

- All 59 srmech tests pass post-revert (no test changes).
- ephemerides-spectral tests still pass with this srmech version
  (the `srmech>=0.1.0` floor in ephemerides-spectral's
  `pyproject.toml` is satisfied by `0.1.1rc1`; pre-release versions
  resolve normally as PEP 440 allows).

#### History link

Task #200 Phase 1 cibuildwheel adoption (PR #383, merged) → Phase A
revert (this release). The premature cibuildwheel adoption was
caught by the publish workflow's own pure-Python-wheel sanity check
failing under cibuildwheel v3.x's defensive build-time error.

### Notes — Task #197 Phase 4 cleanup (2026-05-13)

Phase 4 is the **final phase** of the AMSC-to-srmech refactor (Task #197). It does
not change the srmech package itself; it cleans up the upstream duplicate copies in
ephemerides-spectral now that Phase 3's import-swap has settled:

- ephemerides-spectral deletes 12 vendored AMSC framework modules (4 top-level +
  8 adapters) from its `_research/` mirror and its `docs/antikythera-maths/research/`
  SSOT. ephemerides-spectral's codegen `_INCLUDED_MODULES` / `_INCLUDED_SUBDIRS`
  are updated to no longer mirror the deleted framework into the wheel.
- ephemerides-spectral's wheel shrinks by ~37 KB (~4.7 %) and its codegen
  `manifest.json` n_files drops from 154 to 142.
- All 5 Phase 1 parity gates remain green at the Phase 4 boundary; srmech
  in-isolation 59/59 tests pass (unchanged from Phase 3); ephemerides-spectral
  pytest is byte-identical to the Phase 3 baseline (2128 passed + 42 skipped
  = 2170 collected).
- `srmech v0.1.0` is now ready for the **first TestPyPI release**. See
  `TESTPYPI_RELEASE_NOTES_v0.1.0.md` in this directory for the release
  procedure (autonomous TestPyPI publish via the `srmech-v0.1.0` tag through
  `.github/workflows/srmech-publish.yml`; PyPI release remains human-in-loop).

## [0.1.0] - 2026-05-13

### Added

- **Initial extract of the AMSC framework from `ephemerides-spectral`** as part of Task #197 (AMSC-to-srmech refactor, Phase 2). The framework lives under `srmech.amsc.*`:
  - `srmech.amsc.format` — Mathematical Provenance Record (MPR) v1 format: `MPRRecord` dataclass, NDJSON streaming IO (`read_ndjson` / `write_ndjson`), `validate_mpr_record`, `sha256_bytes`, schema-version + mandatory-field constants.
  - `srmech.amsc.descriptor` — descriptor TOML loader: `Descriptor`, `load_descriptor`, `discover_descriptors`, `render_template` (deliberately minimal name-substitution + Python format-spec; no Jinja), `descriptor_hash` (canonical-serialised), `DescriptorValidationError`.
  - `srmech.amsc.catalog` — universal bridge surface: `list_attested_sources` (with `adapter_class` filter), `get_attested_dataset` (paginated, T0+T1+T2+T3 tiered), `get_attested_descriptor`, `attestation_audit`, `iter_attested_dataset`, T2 local-kernel overlay (`use_local_kernel` / `clear_local_kernel` / `get_local_kernel_state`).
  - `srmech.amsc.gap_suggester` — schema-gap-driven trigger (`suggest_gap_collections`); the lazy-imported classifier + probe sources are ephemerides-specific and remain in ephemerides-spectral.
  - `srmech.amsc.adapters` — six adapter modules: `html_scraper`, `json_api`, `csv_bulk`, `netcdf_grid` (stub), `geotiff_bbox` (stub), `literature_curated`; plus `_base.py` (`ADAPTERS` registry, `attest`, `parser_rule_hash`, `run` composer).
- **`register_attested_root(path, *, source)`** — the load-bearing cross-package API added in `srmech.amsc.catalog`. Downstream packages whose catalog SSOTs live outside `srmech/amsc/attested/` push their roots at package-import time; subsequent `_descriptors()` calls enumerate the union of srmech's own root + all registered roots in registration order. Conflict policy: first-registered wins with a warning.
- **`list_registered_roots()`** — introspection of currently-registered roots (srmech's own + every external). Used by tests and diagnostic output.
- **`srmech/amsc/attested/`** — empty SSOT subtree reserved for future srmech-primary catalogs (e.g. the `citations_curated` catalog planned for Spike #23).
- **CI workflows** under `.github/workflows/`:
  - `srmech-ci.yml` — pytest on push/PR against `docs/srmech/python/**`, 4-cell matrix (Ubuntu/macOS/Windows × Py3.12 + Ubuntu × Py3.10 floor).
  - `srmech-publish.yml` — build sdist + py3-none-any wheel on `srmech-v*` tag, publish to PyPI via trusted OIDC; manual workflow_dispatch can target TestPyPI.
  - `srmech-autotag.yml` — autotag on `pyproject.toml` version bump.

### Notes

- **Phase 2 is purely additive.** No ephemerides-spectral files are touched. Phase 3 (separate PR, not yet open) will rewire ephemerides-spectral's bridge to import from `srmech.amsc.*`; the byte-identical-wheel parity gate from the Phase 1 scope document applies there, not here.
- **Cross-package gap_suggester deviation.** `srmech.amsc.gap_suggester.suggest_gap_collections()` lazy-imports `.dynamical_regime_catalog` and `.dynamical_regime_probes_data`, which are ephemerides-specific and not shipped by srmech. Calling the function from a context where those modules aren't reachable (e.g. srmech in isolation, no ephemerides installed) will raise `ImportError` at call time. The Phase 1 scope did not flag this; ephemerides-spectral consumers (the only known caller) are unaffected because the relative imports resolve inside ephemerides's `_research/` mirror until Phase 3, then via Phase 3's import-swap.
- **`parser_version` stamp.** Changed from `"ephemerides-spectral X.Y.Z"` to `"srmech X.Y.Z"` in T3 live-fetch attestation blocks: srmech is now the parser. Committed NDJSON files retain whatever `parser_version` was stamped at collection time; only future T3 runs differ. No effect on the Phase 3 wheel parity gate (T3 is runtime, not committed bytes).
