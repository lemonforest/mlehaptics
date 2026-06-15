# JPL Power-of-Ten Audit — srmech C library

**Standard:** Holzmann, G. J. (2006). "The Power of Ten — Rules for Developing Safety Critical Code." *IEEE Computer* 39(6), 95-99.

**Audited at:** v0.1.1rc8 (Task #201 Phase B6); reentrancy delta
re-audited at v0.6.0rc5 (#772).

**Scope:** the source files under `c/src/*.c` and the public header
`c/include/srmech.h`. The original Phase B6 audit covered the three
baseline files below; the per-class C surfaces added since
(`srmech_cyclic.c`, `srmech_laplacian.c`, `srmech_primes.c`,
`srmech_rational.c`, `srmech_kepler.c`, `srmech_hdc.c`,
`srmech_dispatch.c`, `srmech_catalog.c`, `srmech_template.c`,
`srmech_tlv.c`, `srmech_search.c`, `srmech_cascade.c`,
`srmech_bus.c`, `srmech_parallel.c`, `srmech_kuramoto.c`,
`srmech_platform.c`, `srmech_json.c`, `srmech_genome.c` — the PAL, rc4,
the OS sibling of the `srmech_simd.c` HAL, plus the §41 genome-persistence
JSON mirror and the §41 genome-persistence disk surface itself)
are held to the same rules by the mechanical ratchet
`tests/test_jpl_audit.py`.

- `c/src/srmech_meta.c` — version + ABI accessors (Phase B3).
- `c/src/srmech_sha256.c` — FIPS 180-4 SHA-256 (Phase B3).
- `c/src/srmech_ndjson.c` — streaming NDJSON line reader (Phase B4).

**Discipline:** Same pattern as ephemerides-spectral's
[JPL_AUDIT.md](../../antikythera-maths/ephemerides-spectral/c/JPL_AUDIT.md).
This document is the audit record. The `SRMECH_PEDANTIC=ON` CMake
build (Rule 10) runs in CI as an always-on ratchet. The Python-side
test `tests/test_jpl_audit.py` (Phase B6 ship) pins the
mechanically-detectable counts as one-way ratchets — they can go
DOWN but not UP.

---

## Summary

| Rule | Description                                       | Baseline | Status |
| :--: | ------------------------------------------------- | -------- | ------ |
|   1  | No goto / setjmp / longjmp / recursion            | 0        | ✅ pass |
|   2  | All loops have fixed upper bounds                 | 0        | ✅ pass |
|   3  | No dynamic allocation after init                  | 0        | ✅ pass |
|   4  | Functions ≤ 60 lines                              | 0        | ✅ pass *(was 1; fixed in this ship by extracting `srmech_ndjson_process_chunk`)* |
|   5  | ≥ 2 assertions per non-trivial function           | 0        | ✅ pass *(trivial accessors exempt per documented rationale; inline arithmetic helpers exempt)* |
|   6  | Smallest possible scope for data                  | 0        | ✅ pass |
|   7  | Return values checked / parameters validated      | 0        | ✅ pass |
|   8  | Limited preprocessor (no multiline macros)        | 0        | ✅ pass |
|   9  | Pointer dereference depth ≤ 1; no function ptrs* | n/a      | partial — see note |
|  10  | Compile clean at most-pedantic warning level      | 0        | ✅ pass (`SRMECH_PEDANTIC=ON` CMake + CI matrix) |

\* Rule 9 partial: `srmech_ndjson_iter` accepts a function pointer
(`srmech_ndjson_line_cb`). This is a deliberate trade-off, see
Rule 9 section below.

**Headline:** All ten JPL Power-of-Ten rules satisfied for srmech's
C surface, modulo one deliberate Rule 9 deviation (callback-based
iterator). Phase B6 fixed the one mechanical violation surfaced by
the audit (Rule 4 / function-length).

---

## Rule 1 — Restrict control flow

> *"Restrict all code to very simple control flow constructs — do not use goto statements, setjmp or longjmp constructs, and direct or indirect recursion."*

### Violations: 0

- `grep -n "goto" c/src/*.c` → no matches.
- `grep -n "setjmp\|longjmp" c/src/*.c c/include/srmech.h` → no matches.
- Manual review: no function in srmech calls itself directly or
  indirectly. All control flow is straight-line, single-return
  per function (modulo early-return-on-error which is loop-free
  and allowed by the spirit of the rule).

✅ **Pass.**

---

## Rule 2 — All loops must have fixed bounds

> *"All loops must have a fixed upper-bound. It must be trivially possible for a checking tool to prove statically that a preset upper-bound on the number of iterations of a loop cannot be exceeded."*

### Violations: 0

Every loop in srmech's C has either a compile-time constant bound
or a caller-supplied size_t bound:

| Loop                                              | Bound          | Source                                |
| ------------------------------------------------- | -------------- | ------------------------------------- |
| sha256 schedule prep `for (i = 0; i < 16; i++)`   | 16             | FIPS 180-4 block size                 |
| sha256 schedule extend `for (i = 16; i < 64; i++)`| 64             | FIPS 180-4 round count                |
| sha256 rounds `for (i = 0; i < 64; i++)`          | 64             | FIPS 180-4 round count                |
| sha256 state→hex `for (i = 0; i < 8; i++)`        | 8              | SHA-256 produces 8 words              |
| sha256 hex inner-`out[base+0..7]`                 | 8 unrolled     | hex chars per word                    |
| sha256 hash full blocks                           | `data_len / 64`| caller's `size_t data_len`            |
| ndjson chunk-by-chunk `while (!eof_reached)`      | file size      | bounded by `fread` returning 0 at EOF |
| ndjson byte loop `for (i = 0; i < n_read; i++)`   | `n_read` ≤ 64 KiB | `SRMECH_NDJSON_CHUNK_BYTES`        |

The `while (!eof_reached)` deserves note: the explicit `eof_reached`
flag + `break` on zero-read makes the termination condition
mechanically obvious. We never use `while(1)` or `for(;;)`.

✅ **Pass.**

---

## Rule 3 — No dynamic allocation after init

> *"Do not use dynamic memory allocation after initialization."*

### Violations: 0

- `grep -n "malloc\|calloc\|realloc\|free" c/src/*.c` → no matches.
- `grep -n "alloca\|vla\|variable.length.array" c/src/*.c` → no matches.
- All buffers are either:
  - Stack-allocated, compile-time-constant-sized (e.g.
    `uint8_t chunk[SRMECH_NDJSON_CHUNK_BYTES]`).
  - **Thread-local static**, compile-time-constant-sized (e.g.
    the 1 MiB NDJSON line-assembly buffer in `srmech_ndjson_iter`
    and the ~1 MiB Hermitian-eigendecomp working matrix `Hwork` in
    `srmech_hermitian_eigendecompose` — both `static
    SRMECH_THREAD_LOCAL`).
  - Caller-supplied (e.g. `char *out_hex` to `srmech_sha256_hex`;
    `double *workspace` to `srmech_hermitian_eigendecompose_ws`).

**Static-scope scratch is itself a legitimate Rule-3 method** — the
buffer has static storage duration, never touches the allocator, and
is sized at compile time. The #772 conversion of the two former
**shared-static** scratch buffers (`srmech_ndjson.c`'s `g_line_buf`
and `srmech_laplacian.c`'s `Hwork`) was therefore **a reentrancy
trade, NOT a Rule-3 fix**: they were already Rule-3-clean. The change
adds the `SRMECH_THREAD_LOCAL` qualifier (and, for the eigendecomp, a
new `srmech_hermitian_eigendecompose_ws` entry taking a caller-
supplied workspace) so the buffers are per-thread / caller-owned
rather than process-wide-shared. This makes the entire op surface
safe to drive concurrently (the #771 multi-threaded plugin) while
keeping the large (~1 MiB) buffers OFF the stack — `_Thread_local` /
`__declspec(thread)` static storage is both Rule-3-clean and
reentrant-across-threads. No malloc was introduced.

✅ **Pass.**

---

## Rule 4 — Functions ≤ 60 lines

> *"No function should be longer than what can be printed on a single sheet of paper in a standard format with one line per statement and one line per declaration. Typically, this means no more than about 60 lines of code per function."*

### Violations: 0 *(was 1 — fixed in Phase B6)*

Per-function line counts (definition lines, body brace to body
brace; counted by awk script in `tests/test_jpl_audit.py`):

| Function                       | Lines | Status |
| ------------------------------ | ----- | ------ |
| `srmech_version`                |   4   | ✅      |
| `srmech_abi_version`            |   9   | ✅      |
| sha256 inline helpers (ror, ch, maj, sigmas) | 4-7 each | ✅ |
| `srmech_sha256_compress`        |  54   | ✅      |
| `srmech_sha256_state_to_hex`    |  20   | ✅      |
| `srmech_sha256_hex`             |  57   | ✅      |
| `srmech_ndjson_emit`            |  20   | ✅      |
| `srmech_ndjson_process_chunk`   |  46   | ✅ *(gained `char *line_buf` param in #772)* |
| `srmech_ndjson_iter`            |  55   | ✅ *(thread-local `line_buf` added in #772; still < 60)* |
| `srmech_hermitian_run_sweeps`   |  27   | ✅ *(extracted from eigendecompose in #772)* |
| `srmech_hermitian_eigendecompose_ws` | 44 | ✅ *(#772 reentrant caller-workspace entry)* |
| `srmech_hermitian_eigendecompose`     | 19 | ✅ *(#772 thin thread-local-workspace wrapper)* |
| `srmech_parallel__stream_transform`   | 20 | ✅ *(rc6 Klein-4 T_s involution; #771/#778)* |
| `srmech_parallel__run_sector`         | 22 | ✅ *(rc6 per-sector worker, disjoint slices)* |
| `srmech_parallel__validate`           | 25 | ✅ *(rc6 arg-validation + post-validation invariants)* |
| `srmech_parallel__serial`             | 13 | ✅ *(rc6 thread-less serial fallback)* |
| `srmech_parallel__job_run`            |  7 | ✅ *(rc6 threaded-job shim)* |
| `srmech_parallel__thread_posix`       |  7 | ✅ *(rc6 pthread entry trampoline)* |
| `srmech_parallel__threaded` (POSIX)   | 31 | ✅ *(rc6 pthread spawn-join, [4] stack handles)* |
| `srmech_parallel__thread_win`         |  7 | ✅ *(rc6 CreateThread entry trampoline)* |
| `srmech_parallel__threaded` (Win)     | 33 | ✅ *(rc6 CreateThread spawn / WaitForMultipleObjects)* |
| `srmech_cascade_parallel_sector_dispatch` | 19 | ✅ *(rc6 public four-sector entry)* |
| `srmech_kuramoto__coupling_sum`       |  9 | ✅ *(rc9 O(n²) coupling sum factored out; #778)* |
| `srmech_cascade_kuramoto_step_f64`    | 17 | ✅ *(rc9 public Kuramoto forward-Euler step)* |
| `srmech_kuramoto__general_sum`        | 12 | ✅ *(rc14 generalised Σ_j A_ij·sin(θ_j−θ_i−α); §11.1)* |
| `srmech_cascade_kuramoto_step_general_f64` | 22 | ✅ *(rc14 public Kuramoto-Sakaguchi step: adjacency + α + pinning)* |
| `srmech_loop__mul2`                   |  7 | ✅ *(rc7 complex dim-2 Cayley-Dickson product)* |
| `srmech_loop__mul4`                   | 17 | ✅ *(rc7 quaternion dim-4 product via two mul2 levels)* |
| `srmech_loop__mul8`                   | 18 | ✅ *(rc7 octonion dim-8 product via two mul4 levels)* |
| `srmech_loop_bind_f64`                | 12 | ✅ *(rc7 public octonion loop_bind; n==8)* |
| `srmech_loop_conj_f64`                | 14 | ✅ *(rc7 public octonion conjugate)* |
| `srmech_loop_inv_f64`                 | 21 | ✅ *(rc7 public Moufang inverse x̄/⟨x,x⟩)* |
| `srmech_cross7_f64`                   | 13 | ✅ *(rc7 public 7-D cross product Im(loop_bind))* |
| `srmech_g2_three_form_f64`            | 20 | ✅ *(rc7 public G2 calibration 3-form scalar)* |
| `srmech_autocorrelation_f64`          | 13 | ✅ *(rc8 Class-L circular autocorrelation; direct O(n²) sum)* |
| `srmech_sha256_batch` + `srmech_sha256_batch.c` internals | ≤45 | ✅ *(rc10 F292 N-way SIMD SHA-256: fill_block / load_words / compress1 / digest1 / compress4 / hash4 / compress8 / hash8 / batch — each ≤45 lines; SIMD sigma ops are SINGLE-line macros per Rule 8)* |
| `srmech_simd.c` HAL (`srmech_simd_has_avx2` / `_avx` / `_sse2` / `_shani` / `srmech_simd_tier`) | ≤22 | ✅ *(rc11 SIMD optimize-path HAL — cpuid/xgetbv probes + env-tier clamp; the ONE home of the machine-specific detection bits; rc18 adds the `_shani` leaf7-bit29 probe)* |
| `srmech_sha256_shani` + `srmech_sha256_shani.c` internals | ≤55 | ✅ *(rc18 F292 SHA-NI single-stream: fill_block / store_digest / scalar ror/load_words/compress1/digest / pack / unpack / rounds_0_15 / group_full / group_final / compress_block / digest_shani / public entry — each ≤55 lines; the 64 SHA-NI rounds factored via a cyclic message-register group; SHA-NI ops are SINGLE-line macros per Rule 8)* |
| `srmech_loop_bind_hd_f64` + `srmech_loopbind_hd.c` internals | ≤45 | ✅ *(rc11 F292 N-way SIMD block-octonion HD bind: vmul2/4/8 a-/s- kernels + avx/sse2 group loops + public entry — each ≤45 lines; SIMD ops are SINGLE-line macros per Rule 8)* |

### Fix shipped in this audit pass

`srmech_ndjson_iter` at rc6 was 76 lines (Rule 4 violation). The
chunk-byte-loop body was extracted into a new static helper
`srmech_ndjson_process_chunk` along its natural seam (per-chunk
state update). Behaviour byte-identical pre/post; the 18 pytest
parity tests in `tests/test_native_ndjson.py` re-ran clean against
the refactored code.

✅ **Pass.**

---

## Rule 5 — ≥ 2 assertions per function

> *"The assertion density of the code should average to a minimum of two assertions per function. Assertions are used to check for anomalous conditions that should never happen in real-life executions. Assertions must always be side-effect free."*

### Violations: 0 *(with documented exemptions)*

Per-function assertion counts:

| Function                       | Asserts | Notes                                              |
| ------------------------------ | :-----: | -------------------------------------------------- |
| `srmech_version`                |    0    | **EXEMPT** — trivial accessor returning a constant string. No preconditions to assert. |
| `srmech_abi_version`            |    0    | **EXEMPT** — trivial accessor returning a constant integer. No preconditions to assert. |
| `srmech_plat_has_threads`       |    0    | **EXEMPT** — PAL (`srmech_platform.c`, rc4) trivial accessor: returns a compile-time `1`/`0` (is a threading backend present?). No state/preconditions to assert. The other PAL fns (`srmech_plat_thread_spawn`/`join`) carry ≥2 asserts. |
| sha256 inline helpers           |    0    | **EXEMPT** — `static inline` arithmetic primitives (ror32, ch, maj, big/small sigma). Per the rule's spirit (anomalous conditions in real-life), 4-line bit-rotation helpers have no real-world failure mode worth asserting; the FIPS 180-4 algorithm is the only caller, and its preconditions on these helpers are validated at the `srmech_sha256_compress` entry. |
| `srmech_sha256_compress`        |    2    | ✅                                                  |
| `srmech_sha256_state_to_hex`    |    2    | ✅                                                  |
| `srmech_sha256_hex`             |    3    | ✅                                                  |
| `srmech_ndjson_emit`            |    2    | ✅                                                  |
| `srmech_ndjson_process_chunk`   |    5    | ✅ *(gained `line_buf != NULL` assert in #772)*     |
| `srmech_ndjson_iter`            |    2    | ✅                                                  |
| `srmech_hermitian_run_sweeps`   |    3    | ✅ *(Hwork / V non-NULL + n ≤ MAX_NODES)*           |
| `srmech_hermitian_eigendecompose_ws` |  4  | ✅ *(out ptrs + n bound + `ws_len ≥ total`)*        |
| `srmech_hermitian_eigendecompose`     |  2  | ✅ *(thin wrapper; out-ptr asserts)*                |
| `srmech_parallel__stream_transform`   |    2    | ✅ *(`label != NULL`; `buf != NULL \|\| n == 0`)*   |
| `srmech_parallel__run_sector`         |    4    | ✅ *(body / out / scratch non-NULL + `sector < CAP`)* |
| `srmech_parallel__validate`           |    2    | ✅ *(post-validation: n_sectors bound + scratch_len)* |
| `srmech_parallel__serial`             |    2    | ✅ *(body non-NULL + n_sectors bound)*              |
| `srmech_parallel__job_run`            |    2    | ✅ *(job + job->body non-NULL)*                     |
| `srmech_parallel__thread_posix`       |    2    | ✅ *(arg + job->body non-NULL)*                     |
| `srmech_parallel__threaded` (POSIX)   |    2    | ✅ *(body non-NULL + n_sectors bound)*              |
| `srmech_parallel__thread_win`         |    2    | ✅ *(arg + job->body non-NULL)*                     |
| `srmech_parallel__threaded` (Win)     |    2    | ✅ *(body non-NULL + n_sectors bound)*              |
| `srmech_cascade_parallel_sector_dispatch` | 2  | ✅ *(post-validation: body + out/scratch non-NULL)* |
| `srmech_kuramoto__coupling_sum`       |    2    | ✅ *(`theta != NULL`; `i < n`)*                     |
| `srmech_cascade_kuramoto_step_f64`    |    2    | ✅ *(out non-NULL + theta/omega-vs-n aliasing pre)* |
| `srmech_kuramoto__general_sum`        |    2    | ✅ *(`theta != NULL`; `i < n`)*                     |
| `srmech_cascade_kuramoto_step_general_f64` | 2  | ✅ *(out non-NULL + theta/omega-vs-n aliasing pre)* |
| `srmech_loop__mul2` / `__mul4` / `__mul8` | 2 each | ✅ *(rc7 inputs + out non-NULL)* |
| `srmech_loop_bind_f64`                | 2  | ✅ *(rc7 x/y/out non-NULL + n==8)*                  |
| `srmech_loop_conj_f64`                | 2  | ✅ *(rc7 x/out non-NULL + n==8)*                    |
| `srmech_loop_inv_f64`                 | 2  | ✅ *(rc7 x/out non-NULL + n==8)*                    |
| `srmech_cross7_f64`                   | 2  | ✅ *(rc7 x/y/out non-NULL + n==8)*                  |
| `srmech_g2_three_form_f64`            | 2  | ✅ *(rc7 x/y/z/out non-NULL + n==8)*                |
| `srmech_autocorrelation_f64`          | 2  | ✅ *(rc8 x/out non-NULL when n>0 + out-vs-x aliasing pre)* |
| `srmech_sha256_batch`                 | 2  | ✅ *(rc10 msgs/lens/out non-NULL when n>0 + tier∈{0,1,2})* |
| `srmech_sha256_batch.c` block/compress/hash internals | 2 each | ✅ *(rc10 fill_block/load_words/compress1/digest1/compress4/hash4/compress8/hash8 — pointer + buffer pre-conditions)* |
| `srmech_loop_bind_hd_f64`             | 2  | ✅ *(rc11 x/y/out non-NULL when nb>0 + tier∈{0,1,2})* |
| `srmech_loopbind_hd.c` vmul/group internals | 2 each | ✅ *(rc11 vmul2a/4a/8a + vmul2s/4s/8s + avx/sse2 group loops — x/y/out non-NULL)* |
| `srmech_simd_tier` (HAL)              | 2  | ✅ *(rc11 env_var != NULL + max_tier >= 0)* |
| `srmech_sha256_shani`                 | 2  | ✅ *(rc18 out_digest non-NULL + data non-NULL when len>0; tier∈{0,1})* |
| `srmech_sha256_shani.c` pad/scalar/SHA-NI internals | 2 each | ✅ *(rc18 fill_block/store_digest/load_words/compress1/digest_scalar + pack/unpack/rounds_0_15/group_full/group_final/compress_block/digest_shani — pointer + cur<4 pre-conditions)* |

**Rule 5 EXEMPT:** `srmech_sha256b__ror` (rc10) + `srmech_sha256ni__ror` (rc18)
— 1-line rotates, like the exempt scalar `srmech_ror32`. `srmech_simd_has_avx2`
/ `srmech_simd_has_avx` / `srmech_simd_has_sse2` / `srmech_simd_has_shani`
(rc11/rc18 SIMD optimize-path HAL — pure cpuid CPU-feature detectors returning
0/1, no pointer/bounds invariant to assert; the rc11 trio REPLACED the per-file
`srmech_sha256b__avx2_supported`/`__tier` copies, so the HAL nets FEWER exempt
functions, and `srmech_simd_tier` is NOT exempt; rc18 adds the `_shani`
leaf7-bit29 probe). The `SRMECH_{SHA256,LOOP_HD,SHANI}_FORCE_TIER` env overrides
+ bounded-tier clamp live in the non-exempt `srmech_simd_tier`. Mirrored in
`tests/test_jpl_audit.py::RULE_5_EXEMPT_FUNCTIONS`.

**Rule 5 EXEMPT:** `toml_is_ws` + `toml_is_bare_key_char` (`srmech_toml.c`)
— pure `char -> bool` predicates over a single value argument (is the char
ASCII whitespace / a bare-key char). No pointer, no bounds, no state; every
`char` is a valid input, so there is no anomalous condition to assert and a
tautology assert would be cargo-cult per the exemption policy below. Same
shape as the exempt sha256 `ch`/`maj` inline primitives. Every OTHER function
in `srmech_toml.c` (the arena allocator, the lexer skips, the value/array/
table parsers, the builder-tree allocators, the finaliser recursion, and the
public `srmech_toml_parse` / `srmech_toml_table_get` entries) carries ≥ 2
asserts (an entry-pointer/contract assert + a structural-invariant assert).

**Rule 5 EXEMPT (srmech_json.c, §41 genome-persistence JSON mirror):**
`json_is_ws` + `json_is_digit` — 4-line char classifiers returning 0/1 over a
single `char`, no pointer/bounds invariant to assert (the same exemption class
as the TOML parser's `toml_is_ws`). Every other function in `srmech_json.c` —
the arena bump allocator, the explicit-stack parser/emitter, the string
escape/decode helpers, the canonical writer, the builder constructors — carries
≥ 2 asserts. The parser + writer are NON-recursive (Rule 1): both walk the value
tree with an explicit depth-bounded stack capped at `SRMECH_JSON_MAX_DEPTH`.
Mirrored in `tests/test_jpl_audit.py::RULE_5_EXEMPT_FUNCTIONS`.

**Rule 5 — `srmech_genome.c` (§41 genome-persistence disk surface) adds NO
new exemptions.** Every function in `srmech_genome.c` — the path/file stdio
helpers (`genome_join` / `genome_write_file` / `genome_read_file` /
`genome_read_region`), the manifest builders (`genome_build_the_one` /
`_chrom` / `_data` / `_attest` / `_render` / `_manifest` / `_manifest_tree`), the
§44 inline-cap body scan (`genome_decode_label` / `genome_scan_chroms`) + the
string-block fill (`genome_fill_strings`, `genome_hex`), the §44 manifest-optional
acquirer (`genome_obtain_manifest` — parse if present, else rebuild by scan), the
catalog/load/window/append entries + their accessors (`genome_data_get` /
`genome_str_eq` / `genome_find_chrom` / `genome_check_new_label` /
`genome_read_bound_body` / `genome_grow_body` / `genome_save_validate`), the §45
in-place edits (`srmech_genome_remove` / `srmech_genome_replace` — splice a
chromosome's byte span out of / into the body, then re-save), the §43
file-management surface (`srmech_genome_export` / `srmech_genome_import` — bundle a
chromosome as a self-contained MPR-attested `.chr`, re-import it self-verifying,
with the `.chr` builders `genome_jstr` / `genome_find_chrom_obj` / `genome_chr_subobj`
/ `_build_data` / `_build_attest` / `_build_render` / `_build_file` / `genome_chr_meta`
/ `genome_chr_consts`, and the import helpers `genome_unhex` / `genome_chr_decode_verify`
/ `genome_chr_verify_extract` / `genome_body_exists` / `genome_chr_append`), and the
§43 loose↔packed surface (`srmech_genome_explode` / `srmech_genome_pack` — git's
object model: explode a packed genome to a dir of `<label>.chr` loose bundles,
pack a `*.chr` dir back into one genome in canonical sorted-label order, with the
helpers `genome_label_filename_safe` / `genome_collect_labels` / `genome_chr_name_ok`
/ `genome_list_chr` / `genome_chr_peek_label` / `genome_sort_by_label`) — carries ≥ 2 asserts and is ≤ 60 lines. No
recursion (the JSON tree is built/walked by the non-recursive
`srmech_json` builder/parser/writer); every loop is bounded by
`n_chroms` (a caller-arena-allocated count — no compiled-in cap; the
genome C carves ALL scratch from the caller `ws` arena) or a caller `size_t`
(the file-read loop carries an explicit `pass <= cap` over-bound, Rule 2;
the §43 `genome_list_chr` directory scan carries an explicit `guard < 65536`
over-bound on top of the `≤ max_n` collected-`.chr` cap, Rule 2). File I/O
is stdio (Rule 3 bans malloc, not files) — the §43 pack's `*.chr` directory
enumeration is the one platform-specific touch (POSIX `dirent` / Win32
`FindFirstFile`, ifdef'd like `srmech_platform.c`; no malloc); the caller
arena is for the JSON tree only; path strings + digests live in fixed
stack/static buffers.

The Hermitian-eigendecomp `_ws` entry additionally validates the new
workspace parameters at runtime (`workspace != NULL` →
`SRMECH_ERR_NULL_ARG`; `ws_len < 2*n*n` → `SRMECH_ERR_OVERFLOW`) in
addition to the debug-build asserts, per Rule 7.

**Total: 18 assertions across the NDJSON + Hermitian-reentrancy
functions; every non-exempt function stays ≥ 2.** Exceeds the 2.0
floor. (The repo-wide ratchet `tests/test_jpl_audit.py` enforces this
mechanically across all `c/src/*.c`.)

### Exemption policy

The two exempt categories above (trivial accessors, inline
arithmetic primitives) follow the same exemption policy
ephemerides-spectral applies. The rule's intent is "anomalous
conditions in real-life executions"; functions that take no inputs
and return a compile-time constant have no anomalous conditions to
check, and asserting a tautology (`assert(true)`) would be cargo-
cult compliance rather than substantive code quality.

✅ **Pass.**

---

## Rule 6 — Smallest possible scope for data

> *"Data objects must be declared at the smallest possible level of scope."*

### Violations: 0

Manual review of every variable declaration:

- Loop indices declared inside the `for (size_t i = 0u; ...)` head
  — minimal possible scope, C99/C11 idiom.
- Local intermediates (e.g. `const uint32_t t1`, `t2` in sha256
  rounds) declared `const` and at the inner loop body scope where
  they're used.
- Working state buffers (`uint32_t w[64]` in sha256 compress;
  `uint8_t chunk[]` in ndjson_iter) declared at the function
  entry — minimal-scope wouldn't help; they're used throughout the
  function body.
- The NDJSON line-assembly buffer must persist across
  `srmech_ndjson_process_chunk` invocations *during one*
  `srmech_ndjson_iter` call (a line can straddle chunk boundaries).
  As of #772 it is a **function-local `static SRMECH_THREAD_LOCAL`**
  buffer inside `srmech_ndjson_iter` (no longer a file-scope
  `g_line_buf` global), threaded into `process_chunk` / `emit` as a
  `char *line_buf` parameter so no helper references a file-scope
  global. At 1 MiB it stays static-duration (too large to stack
  safely per call) but is now per-thread → reentrant across threads.
  The `srmech_hermitian_eigendecompose` working matrix `Hwork` got
  the same treatment (function-local `static SRMECH_THREAD_LOCAL`),
  and additionally exposes `srmech_hermitian_eigendecompose_ws` with
  a caller-supplied workspace for callers that want to own the
  buffer. The earlier single-thread contract for these two buffers
  is thereby retired.

✅ **Pass.**

---

## Rule 7 — Check return values, validate parameters

> *"The return value of non-void functions must be checked by each calling function, and the validity of parameters must be checked inside each function."*

### Violations: 0

Parameter validation at every public entry point:

| Function              | Parameter validation                                          |
| --------------------- | ------------------------------------------------------------- |
| `srmech_sha256_hex`   | `out_hex == NULL` → `SRMECH_ERR_NULL_ARG`. `data == NULL` with `data_len != 0` → same. |
| `srmech_ndjson_iter`  | `path == NULL` or `cb == NULL` → `SRMECH_ERR_NULL_ARG`.       |
| `srmech_version`      | No parameters.                                                 |
| `srmech_abi_version`  | No parameters.                                                 |

Return-value checks at every internal-callsite:

- Every `fopen` checked for NULL → `SRMECH_ERR_IO`.
- Every `fread` checked for `n_read == 0` + `ferror(fp)`.
- Every callback invocation's return propagated immediately on
  non-`SRMECH_OK`.
- `srmech_ndjson_process_chunk`'s return checked at the call site
  in `srmech_ndjson_iter`.
- `srmech_sha256_compress` returns `void` (state mutation only) —
  exempt.
- `memcpy` / `memset` returns ignored per standard-library
  convention.

✅ **Pass.**

---

## Rule 8 — Limited preprocessor

> *"The use of the preprocessor must be limited to the inclusion of header files and simple macro definitions. Token pasting, variable argument lists (ellipses), and recursive macro calls are not allowed."*

### Violations: 0

- `grep -n "##\|__VA_ARGS__\|\.\.\." c/src/*.c c/include/srmech.h` → no matches.
- All `#define` directives are simple constants (`SRMECH_VERSION_*`,
  `SRMECH_NDJSON_CHUNK_BYTES`, `SRMECH_NDJSON_MAX_LINE_BYTES`,
  `SRMECH_ABI_VERSION`, `SRMECH_THREAD_LOCAL`) or include guards
  (`#ifndef SRMECH_H`).
- `SRMECH_THREAD_LOCAL` (#772) is a single-token object-like macro
  selecting the platform TLS keyword (`_Thread_local` /
  `__declspec(thread)` / `__thread`) via `#if`; no token-paste, no
  varargs, no line continuation.
- One **function-like** macro exists: `SRMECH_HERMITIAN_WS_LEN(n)`
  (#772), a single-line pure-arithmetic constant helper
  (`((size_t)(n) * (size_t)(n) * 2u)`) that lets a caller size the
  Hermitian-eigendecomp workspace. It is side-effect-free, expands on
  one line, and uses neither token-paste nor varargs — within the
  spirit of Rule 8 (which prohibits multi-line / recursive / token-
  pasting macros, not all parameterised constants). `SRMECH_HERMITIAN_WS_MAX`
  is its object-like `n = MAX_NODES` specialisation, also single-line.
- No multi-line macros. No recursive / token-pasting macros.
- `srmech_json.c` (§41 JSON mirror) adds `SRMECH_JSON_MAX_CHILDREN`,
  `SRMECH_JSON_MAX_DEPTH` (object-like int constants) and the four
  structural-byte constants `JSON_LBRACE` / `JSON_RBRACE` / `JSON_LBRACK`
  / `JSON_RBRACK` (single-token ASCII-code object-like macros, `0x7B` /
  `0x7D` / `0x5B` / `0x5D`). They exist so no brace/bracket char literal
  (`'{'` `'}'` `'['` `']'`) appears in a function body — keeping
  brace-balance unambiguous for tooling and readers. All single-line, no
  token-paste, no varargs.
- `#ifdef __cplusplus` only for `extern "C"` block — standard.

✅ **Pass.**

---

## Rule 9 — Pointer dereference depth ≤ 1; no function pointers

> *"The use of pointers should be restricted. Specifically, no more than one level of dereferencing should be used. Pointer dereference operations may not be hidden in macro definitions or inside typedef declarations. Function pointers are not permitted."*

### Status: **Partial — one deliberate deviation**

#### Dereference depth: 0 violations

No `**ptr` syntax appears anywhere; all pointer indirection is
single-level. The `size_t *line_len_inout, size_t *lineno_inout`
parameters to `srmech_ndjson_process_chunk` are single-level —
the caller passes addresses of local stack variables.

#### Function pointers: 1 deliberate deviation

`srmech_ndjson_iter` takes a `srmech_ndjson_line_cb` callback
function pointer.

**Rationale for deviation:** The callback enables the Python ctypes
binding to receive lines without copying through an intermediate
C-side dynamic structure (which would violate Rule 3). The Python
side wraps the callback in a `CFUNCTYPE` and collects lines into a
list. Removing the callback would require either:

1. A pre-allocated caller-supplied output array of structs *and*
   length, which the C code populates — but this requires the
   caller to know the line count in advance (impossible without
   a first pass over the file), OR to pass a maximum count + indicate
   truncation;
2. Or batched IO with the caller passing buffers per-batch and
   draining them — equivalent to a callback but with extra book-
   keeping.

The callback shape is the smallest API surface that lets srmech
satisfy Rules 3 + 4 without imposing Pyrrhic constraints on the
caller. It is functionally equivalent to a coroutine and behaves
the same at every callsite (single Python target, single C-side
parity test).

This is the same trade-off ephemerides-spectral makes in several
places for similar reasons.

✅ **Pass with documented Rule 9b deviation.**

---

## Rule 10 — Compile clean at most-pedantic warning level

> *"All code must compile, from the first day of development, with all compiler warnings enabled at the compiler's most pedantic setting. All code must compile with these settings without any warnings."*

### Violations: 0

Implementation:

- `CMakeLists.txt` `SRMECH_PEDANTIC` option (default OFF for casual
  local builds, ON for CI). When ON, gcc/clang add `-Werror` and
  MSVC adds `/WX`.
- Default flags: `-Wall -Wextra -Wpedantic -O2` (gcc/clang) or
  `/W4 /O2` (MSVC).
- CI matrix runs `SRMECH_PEDANTIC=ON` on Linux gcc + macOS clang +
  Windows MSVC. Any new warning fails the build.

Phase B6 ship: the CI workflow gains a dedicated `pedantic-build`
job alongside the existing `build-wheels` matrix. The pedantic
build runs cmake directly with `-DSRMECH_PEDANTIC=ON` and only
asserts the build succeeds — it doesn't ship a wheel, it's purely
the toolchain-level Rule-10 ratchet.

✅ **Pass.**

---

## Implementation history

- **Phase B3 (rc5)** — first native code shipped (sha256). The
  Power-of-Ten audit was already partially compliant in the code
  comments but unverified.
- **Phase B4 (rc6)** — ndjson reader. Same comment-level discipline.
- **Phase B5 (rc7)** — no new C code; only Python wiring. No audit
  delta.
- **Phase B6 (rc8, this ship)** — formal audit. Surfaced one
  mechanical Rule 4 violation (`srmech_ndjson_iter` at 76 lines)
  and zero substantive issues elsewhere. Fixed Rule 4 by
  extracting `srmech_ndjson_process_chunk`. Documented the Rule 9
  callback deviation. Wrote this document. Added CI pedantic-build
  job (Rule 10 ratchet).
- **v0.6.0rc5 (#772) — full-core reentrancy.** A full-core audit for
  shared mutable static data (`grep` over `c/src/*.c`) found exactly
  two process-wide-shared scratch buffers: `srmech_ndjson.c`'s
  `g_line_buf` and `srmech_laplacian.c`'s `Hwork`. Both were already
  Rule-3-clean (static-duration, no malloc) — the change is a
  **reentrancy trade, not a Rule-3 fix**. `g_line_buf` became a
  function-local `static SRMECH_THREAD_LOCAL` buffer threaded into
  `process_chunk`/`emit` as a parameter (no API/ABI change). `Hwork`
  became per-thread the same way, and a new ABI-additive exported
  symbol `srmech_hermitian_eigendecompose_ws` exposes a caller-
  supplied workspace (validated: non-NULL + `ws_len ≥ 2*n*n`); the
  original `srmech_hermitian_eigendecompose` now routes through that
  core via a thread-local workspace. The sweep loop was extracted
  into `srmech_hermitian_run_sweeps` to keep all three functions
  under Rule 4's 60-line limit. New portable TLS macro
  `SRMECH_THREAD_LOCAL` (`_Thread_local` / `__declspec(thread)` /
  `__thread`). `SRMECH_ABI_VERSION` unchanged at 3 (adding a symbol
  never bumps ABI). No new mechanical violations; ratchet stays at 0.
- **v0.6.0rc6 (#771/#778) — `srmech_parallel.c` Klein-4 four-sector
  dispatch.** The C peer for
  `srmech.amsc.cascade.parallel.parallel_sector_dispatch`: runs ONE
  caller-supplied cascade `body` across its ≤4 Klein-4 (Z₂ × Z₂)
  chirality sectors and writes the four sector duals. Adds 10 functions
  (the public `srmech_cascade_parallel_sector_dispatch` + 9 static
  helpers, including platform-conditional POSIX/Windows `__threaded`
  variants). A **portable threading shim** mirrors `srmech_bus.c`:
  `pthread_create`/`pthread_join` on POSIX, `CreateThread`/
  `WaitForMultipleObjects` on Windows, and a **serial fallback** that
  preserves the full four-sector capability bit-for-bit on a
  thread-less microcontroller. Thread handles + jobs live in fixed
  `[SRMECH_PARALLEL_SECTOR_CAP]` (`[4]`) **stack arrays** — no malloc
  (Rule 3). Sectors write only their own disjoint output + scratch
  slices (the F233 independence that makes serial == threaded). Longest
  function 33 lines (Windows `__threaded`); every function ≥ 2 asserts.
  `SRMECH_ABI_VERSION` unchanged at 3 (new symbol only). No new
  mechanical violations; ratchet stays at 0.
- **v0.6.0rc9 (#778) — `srmech_kuramoto.c` native Kuramoto step.**
  One forward-Euler step of the canonical Kuramoto coupled-oscillator
  model (Kuramoto 1975; Acebrón et al. 2005, Rev. Mod. Phys. 77:137):
  `θ_i(t+dt) = θ_i + dt·[ω_i + (K/N) Σ_j sin(θ_j − θ_i)]`. Closes a
  C/Python parity gap so the dispatch-clock / coupled-oscillator step
  runs natively (libm `sin`, as `srmech_kepler.c` already does). 2
  functions: the public `srmech_cascade_kuramoto_step_f64` (17 lines)
  plus the static `srmech_kuramoto__coupling_sum` helper (9 lines) into
  which the O(n²) inner coupling sum was **factored to keep the public
  step ≤ 60 lines** (Rule 4). Pure function over caller buffers (`out`
  must not alias θ/ω) — no malloc, reentrant, no shared static state;
  both functions carry 2 asserts. `SRMECH_ABI_VERSION` unchanged at 3
  (new symbol only). No new mechanical violations; ratchet stays at 0.

- **v0.6.0rc14 (§11.1) — generalised Kuramoto-Sakaguchi step.**
  `dθ_i/dt = ω_i + Σ_j A_ij·sin(θ_j − θ_i − α) [ + p_i·sin(ψ_i − θ_i) ]`
  added to `srmech_kuramoto.c`: a row-major `adjacency` matrix (NULL →
  uniform `K/N`; non-symmetric → directed coupling), a Sakaguchi
  frustration `α`, and optional per-oscillator pinning. 2 new functions:
  the public `srmech_cascade_kuramoto_step_general_f64` (22 lines) plus the
  static `srmech_kuramoto__general_sum` helper (12 lines, into which the
  O(n²) weighted coupling sum is factored to keep the public step ≤ 60).
  Pure functions over caller buffers (`out` must not alias θ/ω/adjacency/
  pin arrays) — no malloc, reentrant, no shared static state; both carry 2
  asserts; **NO Python callback** (co-equal parity — the C path runs C, the
  Python path runs Python). `SRMECH_ABI_VERSION` unchanged at 3 (new symbol
  only). No new mechanical violations; ratchet stays at 0.

- **§41 genome-persistence JSON mirror — `srmech_json.c`.** A malloc-free
  JSON parser + canonical writer: the parser builds a value tree from a
  caller-supplied arena/workspace (the same `void *ws, size_t ws_len` bump
  allocator the TOML parser uses); the writer emits bytes BYTE-IDENTICAL to
  CPython `json.dumps(obj, sort_keys=True, ensure_ascii=False)` for null /
  bool / int / string / object / array trees (exactly what an MPR manifest /
  genome catalog is — they are float-free). DOUBLE values are best-effort
  (`%.17g`, normalised to carry a `.`); float byte-parity with Python's
  `repr(float)` is explicitly NOT guaranteed (out of scope; manifests are
  float-free). Both the parser and the writer are NON-recursive (Rule 1):
  each walks the tree with an explicit stack of frames bounded by
  `SRMECH_JSON_MAX_DEPTH` (64), allocated off the call stack (parser frames
  in the arena; the writer's emit-frame stack a `static SRMECH_THREAD_LOCAL`
  array — Rule-3-clean static storage, per-thread reentrant). Per-node
  children capped at `SRMECH_JSON_MAX_CHILDREN` (256). Every loop has a fixed
  bound (Rule 2): the container loops are bounded by the input length / the
  child cap. No malloc (Rule 3 — caller arena), no libm, no `<complex.h>`.
  Two char classifiers (`json_is_ws` / `json_is_digit`) are Rule-5 exempt
  (see the Rule 5 section); every other function carries ≥ 2 asserts and is
  ≤ 60 lines. `SRMECH_ABI_VERSION` unchanged at 3 (new symbols + a struct +
  macros only). No new mechanical violations; ratchet stays at 0.

- **§41 genome-persistence disk surface — `srmech_genome.c`.** The C mirror
  of `srmech.amsc.genome`'s disk `save` / `load` / `catalog` / `append` /
  `window`. A genome directory holds `manifest.json` (an MPRRecord, MPR v1,
  built with the `srmech_json` BUILDER + serialised with `srmech_json_write`,
  BYTE-IDENTICAL to the Python `genome_save` manifest's
  `json.dumps(payload, sort_keys=True, ensure_ascii=False)`) and `turns.bin`
  (the append-only flat body — every strand element a FIXED-WIDTH
  `leaf_dim`-byte block, verbatim). Bounding == integrity: every read
  re-hashes the bytes it touched (via `srmech_sha256_hex`, Class A) and
  compares the lowercase-hex digest against the manifest's stored hex
  (whole-body `body_sha256`, a windowed chromosome's `cap_sha256`); a
  mismatch is `SRMECH_ERR_BAD_INPUT` — the `GenomeBoundingError` analogue.
  No abs(), no float, no libm. The §41 attestation / rendering constants
  (`source_doi` / `source_url` / `license` / `retrieved_at` /
  `collector_descriptor_path` + `human_readable_name` / `cite_as` /
  `purpose`) are copied VERBATIM from `genome.py` `_manifest_record`; the
  `cite_as` carries the U+00A7 `§` as the 2-byte UTF-8 sequence
  `0xC2 0xA7` (`ensure_ascii=False`). The `parser_rule_hash` is
  `sha256("genome_persistence/v1")` and `collector_descriptor_hash` is
  `sha256("srmech://schema/genome_manifest/v1")`. File I/O is stdio
  (Rule 3 bans malloc, not file I/O); the caller arena `ws` is for the JSON
  tree only; path strings + digests + the manifest-write buffer + the
  append body scratch live in fixed stack / `static SRMECH_THREAD_LOCAL`
  buffers (Rule-3-clean static storage; per-thread reentrant). No
  recursion (the JSON tree is built/walked by the non-recursive
  `srmech_json` builder/parser/writer); every loop bounded (Rule 2 — the
  file-read loop carries an explicit `pass <= cap` over-bound). Every
  function carries ≥ 2 asserts and is ≤ 60 lines — NO new Rule-5 exemptions.
  `SRMECH_ABI_VERSION` unchanged at 3 (new symbols + a struct + macros
  only). No new mechanical violations; ratchet stays at 0.

Both `srmech_parallel.c` (rc6) and `srmech_kuramoto.c` (rc9 + rc14) pass the
`tests/test_jpl_audit.py` mechanical ratchet (Rules 1 / 3 / 4 / 5 / 8)
and the 3-cell pedantic `-Werror` / `-Wpedantic` build (Linux gcc /
macOS clang / Windows MSVC), verified green in CI. `srmech_json.c` and
`srmech_genome.c` are held to the same ratchet + pedantic build.

**Total mechanically-detectable violations: 1 → 0 (held at 0 through
v0.6.0rc14).**

The pin test `tests/test_jpl_audit.py` enforces the zero count
going forward — PRs that introduce a new function > 60 lines or
remove an assertion from a function below the 2-assert floor will
fail CI.
