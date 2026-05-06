# JPL Power-of-Ten Audit — ephemerides-spectral C library

**Standard:** Holzmann, G. J. (2006). "The Power of Ten — Rules for Developing Safety Critical Code." *IEEE Computer* 39(6), 95-99.

**Audited at:** v0.11.2 baseline (the audit-only ship; no code changes yet).

**Scope:** 11 source files (~2.1k LOC) under `c/src/*.c` and `c/include/*.h`.

**Discipline:** This document is the audit record. Live counts are pinned in [`tests/test_jpl_audit.py`](../python/tests/test_jpl_audit.py) as a one-way ratchet — violation counts can only go DOWN, never UP, in PR review. Adding a new violation requires updating the pin upward AND an explicit justification in the PR description.

This is the *audit* phase. Rule-by-rule fixes ship in v0.11.3+ as separate code-quality minors; each fix lands as its own commit, drops the pin, and reduces the recorded total.

---

## Summary

| Rule | Description | v0.11.2 baseline | Current | Status |
|---|---|--:|--:|---|
| 1 | No goto / setjmp / longjmp / recursion | 5 | **0** | ✅ — fixed in v0.13.4 (caller-supplied-scratch refactor in `es_hd_state.c`) |
| 2 | Fixed loop bounds | 0 | 0 | ✅ — no `while(1)` / `for(;;)` |
| 3 | No dynamic allocation after init | 29 | **0** | ✅ — fixed in v0.13.4 (C library no longer calls `malloc`/`free` after init) |
| 4 | Functions ≤ 60 lines | 4 | **0** | ✅ — fixed in v0.13.5 (4 long functions split via 10 new private static helpers) |
| 5 | ≥ 2 assertions per function (avg) | 64 short | **0 short** | ✅ — fixed in v0.13.6 (88 assertions across 42 functions; 2.10/function avg; gated behind `<assert.h>` NDEBUG so production strips them entirely) |
| 6 | Smallest possible scope for data | manual | manual | ⚠ — defer to v0.13.8 manual audit |
| 7 | Check return values, validate parameters | manual | manual | ⚠ — partial; bridge sites validate, internal sites mixed. Queued for v0.13.8. |
| 8 | Limited preprocessor (header includes + simple macros only) | 0 | 0 | ✅ — no multi-line macros |
| 9 | Pointer dereference depth ≤ 1; no function pointers | 0 | 0 | ✅ — no function pointers found |
| 10 | Compile clean at most-pedantic warning level | unknown | **0 warnings** | ✅ — fixed in v0.13.7 (`ES_PEDANTIC=ON` CMake option + 3-cell `pedantic-build` CI matrix; Linux gcc / macOS clang / Windows MSVC; always-on, fails build on any warning) |

**Headline:** Four ships, all five mechanically-enforceable JPL rules cleared (Rules 1, 3, 4, 5, 10). v0.13.4 was the structural cleanup (caller-supplied scratch removed `malloc`/`free` and the `goto`-cleanup pattern they were guarding); v0.13.5 was the formatting cleanup (10 new private static helpers split the 4 long functions along natural algorithm seams); v0.13.6 was the documentation pass (88 assertions across 42 functions documenting pre-conditions, post-conditions, and invariants); v0.13.7 was the toolchain pass (`ES_PEDANTIC=ON` + 3-cell pedantic-build CI matrix enforces zero-warnings across gcc / clang / MSVC). Encoder math byte-identical across all four ships — parity smoke pins both backends to within float-ULP. Remaining: Rules 6+7 manual audits (v0.13.8).

**Mechanically-detectable violations: v0.11.2 baseline 102 → v0.13.7 0.** Every Rule 1-5 source-side pin satisfied; Rule 10 toolchain-side enforcement always-on in CI. The pinned ratchet test allows this number to go DOWN only; PRs that increase it fail.

---

## Rule 1 — Restrict control flow

> *"Restrict all code to very simple control flow constructs — do not use goto statements, setjmp or longjmp constructs, and direct or indirect recursion."*

### Violations: 0 *(baseline 5; fixed in v0.13.4)*

All in `c/src/es_hd_state.c`. Cleanup-on-error pattern:

```c
es_complex64_t *basis = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
es_complex64_t *rolled = (es_complex64_t *)malloc(D * sizeof(es_complex64_t));
if (!basis || !rolled) {
    free(basis); free(rolled);
    return ES_ERR_NULL_OUTPUT;
}
rc = es_channel_basis(seed, basis, D);
if (rc != ES_OK) goto out;
rc = roll_complex64(basis, rolled, phase, D);
if (rc != ES_OK) goto out;
// ...
out:
    free(basis);
    free(rolled);
    return rc;
```

| Site | Function | Pattern |
|---|---|---|
| `es_hd_state.c:186` | `es_encode_state_hd` | `goto out` for cleanup of `basis` + `rolled` |
| `es_hd_state.c:189` | `es_encode_state_hd` | (continued) |
| `es_hd_state.c:274` | `es_get_eclipse_probability` | `goto out` for cleanup of `sun_b` + `moon_b` + `node_b` + `s_op` |
| `es_hd_state.c:277` | `es_get_eclipse_probability` | (continued) |
| `es_hd_state.c:279` | `es_get_eclipse_probability` | (continued) |

### v0.13.4 fix shipped

The combined Rule 1 + Rule 3 fix made all three HD-pipeline entry points take caller-supplied scratch buffers as additional pointer parameters. The Python ctypes shim (`_native_bip.py`) allocates the scratch alongside the existing `out_state` buffer; the user-facing bridge API is unchanged.

```c
/* v0.13.4 (ABI v6) signature: */
es_status_t es_encode_state_hd(
    double delta_t_days,
    es_complex64_t *out_state,
    es_complex64_t *scratch_basis,    /* [D], caller-supplied */
    es_complex64_t *scratch_rolled,   /* [D], caller-supplied */
    size_t D
);
```

With no buffers to free, the cleanup-on-error path collapses to plain early-return. Result: zero `goto`s, zero `malloc`/`free`, both Rule 1 and Rule 3 satisfied in one refactor. Encoder math is byte-identical to ABI v5 (parity smoke verifies).

### setjmp / longjmp: 0
### Recursion: 0 (manual inspection — no function calls itself)

---

## Rule 2 — All loops must have fixed bounds

> *"All loops must have a fixed upper-bound. It must be trivially possible for a checking tool to prove statically that a preset upper-bound on the number of iterations of a loop cannot be exceeded."*

### Violations: 0

No `while(1)`, `for(;;)`, or other unbounded loop constructs. Every loop in the codebase has a static upper bound (`ES_N_BODIES`, `ES_COSINE_LUT_SIZE`, `D`, `n_bodies`, etc.) provable by inspection.

✅ **Pass.**

---

## Rule 3 — No dynamic allocation after initialization

> *"Do not use dynamic memory allocation after initialization."*

### Violations: 0 *(baseline 29; fixed in v0.13.4)*

All in `c/src/es_hd_state.c`. Each HD-pipeline entry point (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) allocates D-dimensional `es_complex64_t` buffers per call:

| Function | Per-call allocations | Lines |
|---|---|---|
| `es_encode_state_hd` | 2 (`basis`, `rolled`) | 111-127, 141-142 |
| `es_bind_observer` | 3 (`body_basis`, `coord_basis`, `coord_op`) | 176-180, 237-239 |
| `es_get_eclipse_probability` | 4 (`sun_b`, `moon_b`, `node_b`, `s_op`) | 263-268 |

Total: ~9 `malloc` calls + ~9 mirrored `free` calls + a few error-path `free`s = **29 dynamic-allocation references**.

### v0.13.4 fix shipped

The caller-supplied-scratch pattern was chosen over static buffers because D is set at runtime by the Python bridge (typically D=65536, but configurable). Static buffers sized for the worst-case D would have wasted memory on lower-D paths and forced a recompile to expand the cap; caller-supplied scratch keeps the C library D-agnostic.

The 29 `malloc`/`calloc`/`realloc`/`free` references in `es_hd_state.c` collapsed to 0; the file no longer needs `<stdlib.h>` (`malloc`/`free` were the only consumers). The Python ctypes shim allocates the scratch buffers via `(EsComplex64 * D)()` once per call alongside the existing `out_state` allocation — no observable change in heap pressure (Python was always heap-allocating the output buffer; the C library was duplicating the allocation strategy from C side).

ABI v5 → v6: the wire format of all three HD-pipeline entry points changed (extra pointer params); the encoder math is byte-identical and the parity smoke test pins both paths to within float-ULP. The pure-Python BIP encoder is unaffected.

---

## Rule 4 — Function bodies ≤ 60 lines

> *"No function should be longer than what can be printed on a single sheet of paper in a standard reference format with one line per statement and one line per declaration."*

Convention: 60 lines max (typical printable page; matches Holzmann's intent).

### Violations: 0 *(baseline 4; fixed in v0.13.5)*

| Lines (baseline) | File | Function |
|--:|---|---|
| 109 | `c/src/es_encode.c` | `es_encode_state` |
| 99 | `c/src/es_parity.c` | `es_find_syzygies` |
| 86 | `c/src/es_hd_state.c` | `es_bind_observer` |
| 71 | `c/src/es_hd_state.c` | `es_get_eclipse_probability` |

### v0.13.5 fix shipped

All four functions split into ≤60-line drivers via 10 new private static helpers along natural algorithm seams. No public API change, no ABI change (still v6), encoder math byte-identical (parity smoke green).

| Driver | Helpers extracted |
|---|---|
| `es_encode_state` | `apply_one_chunk` (chunk-loop body: diagonal evolution + breathing-couplings perturbation), `apply_subchunk_remainder` (banker's-round leftover-day step) |
| `es_find_syzygies` | `select_syzygy_targets` (kind-filter table builder), `score_syzygy_event` (per-event geometry: synodic + draconic residuals), `validate_syzygy_args` (input check helper), `emit_syzygy_event` (cap-aware emit) |
| `es_bind_observer` | `observer_coord_shift` (lat/lon → roll index), `apply_observer_bind` (complex-multiply inner loop) |
| `es_get_eclipse_probability` | `build_syzygy_operator` (sun+moon+node sum), `complex64_vdot_magnitude` (numpy-`vdot` magnitude) |

Total function count 32 → 42; `PIN_RULE_5_TOTAL_FUNCS` ratcheted UP. The Rule 5 fix in v0.13.6 needs the new inventory (84 assertions for 2/function average vs. baseline 64).

---

## Rule 5 — Average of 2+ assertions per function

> *"The assertion density of the code should average to a minimum of two assertions per function. Assertions are used to check for anomalous conditions that should never happen in real-life executions."*

### v0.13.6 fix shipped

- **Total functions:** 42 (post-v0.13.5)
- **Total `assert(...)` calls:** 88
- **Average:** 2.10 assertions / function (target ≥2.0) ✅
- **Shortfall:** **0**

| File | Assertions / Functions | Density |
|---|--:|--:|
| `es_channel_bases.c` | 2 / 1 | 2.00 |
| `es_encode.c` | 26 / 13 | 2.00 |
| `es_hd_state.c` | 25 / 11 | 2.27 |
| `es_parity.c` | 16 / 8 | 2.00 |
| `es_patches.c` | 15 / 7 | 2.14 |
| `es_prng.c` | 4 / 2 | 2.00 |
| **Total** | **88 / 42** | **2.10** |

The previously-skipped `test_rule_5_density_meets_2_per_function` ratchet test now PASSES.

### Historical baseline (v0.11.2): 64 short

The codebase has **zero** assertions. Every function is a Rule 5 violation by inspection.

**Fix path (v0.11.3+):**

Per Holzmann, assertions should check:
- Pre-conditions on parameters (caller contract) — even when already validated by `if (!ptr) return ERR;`, an `assert(ptr != NULL);` documents the contract for static analysis.
- Post-conditions on results (callee contract) — `assert(rc == ES_OK || rc < ES_MAX_STATUS);`.
- Loop invariants — `assert(i < ES_N_BODIES);` inside the body-iteration loop.
- Range invariants — `assert(D > 0 && (D & (D-1)) == 0);` (D is a power of 2).

Targeted addition pattern:
- One pre-condition + one post-condition per function = 64 assertions, hitting the 2/function avg exactly.
- For the encoder hot path, gate behind `#ifndef NDEBUG` so production builds with `-DNDEBUG` strip them — assertions are a *development* tool, not a runtime cost.

---

## Rule 6 — Smallest possible scope for data

> *"Data objects must be declared at the smallest possible level of scope."*

### Status: ⚠ Manual audit deferred to v0.11.3

This rule is not mechanically detectable without semantic analysis. Spot-check on `es_encode.c::es_encode_state`:

```c
es_status_t es_encode_state(...) {
    int64_t omega_int;
    uint32_t phase;
    int64_t step;
    // ...
    for (size_t i = 0; i < n_bodies; ++i) {
        omega_int = es_omega_diag[i];      // declared at function scope
        phase = phases_init[i];            // declared at function scope
        // ...
    }
}
```

Function-scope declarations should mostly be loop-scope. Likely 5-10 violations across `es_encode.c` + `es_parity.c`. Pinned as a **manual rule with TBD count** — the v0.11.3+ fix work scans + relocates declarations.

---

## Rule 7 — Check all return values; validate all parameters

> *"The return value of non-void functions must be checked by each calling function and the validity of parameters must be checked inside each function."*

### Status: ⚠ Partial; manual audit needed

**Bridge entry points** (`es_encode_state`, `es_find_syzygies`, etc.) validate parameters cleanly with `ES_ERR_*` returns. ✅

**Internal helpers** (`es_floor_div`, `phase_uint32_to_residue`, etc.) take pre-validated inputs and don't re-check. This is JPL-acceptable IFF the caller documents the precondition (Rule 5 assertions help here).

**Return-value checking by callers:** `bridge.py`'s ctypes shim checks every `es_status_t` return. Internal C-side calls are mostly checked but a manual audit will likely find 5-15 sites where `rc` is assigned but not checked before the next call.

**Pinned as a manual rule with TBD count.**

---

## Rule 8 — Limited preprocessor

> *"The use of the preprocessor must be limited to the inclusion of header files and simple macro definitions. Token pasting, variable argument lists (ellipses), and recursive macro calls are not permitted. All macros must expand into complete syntactic units. The use of conditional compilation directives is often also dubious, but cannot always be avoided."*

### Violations: 0

- No multi-line macros (`#define X foo \\` continuation lines).
- No token-pasting (`##`).
- No variadic macros (`__VA_ARGS__`).
- No recursive macros.
- Conditional compilation limited to `#ifndef ES_*_H` header guards + `#ifdef __cplusplus` extern-C wrappers.
- All macros are simple constants (`#define ES_N_BODIES 38u`) or simple inline expansions (`#define ES_MODULO_MASK 0xFFFFFFFFu`).

✅ **Pass.**

---

## Rule 9 — Pointer use restricted

> *"The use of pointers should be restricted. Specifically, no more than one level of dereferencing is allowed. Pointer dereference operations may not be hidden in macro definitions or inside typedef declarations. Function pointers are not permitted."*

### Violations: 0

- No function pointers anywhere in the codebase.
- No multi-level dereferencing (`**ptr`, `(*ptr)->member`) in expressions — pointers are always taken to single-element scope.
- No pointer dereferences inside macro definitions.
- No pointer dereferences hidden by typedefs (e.g. `typedef struct Foo *FooHandle` patterns).

✅ **Pass.**

---

## Rule 10 — Compile clean at most-pedantic warning level

> *"All code must be compiled, from the first day of development, with all compiler warnings enabled at the compiler's most pedantic setting. All code must compile with these settings without any warnings. All code must be checked daily with at least one, but preferably more than one, state-of-the-art static source code analyzer and should pass the analyses with zero warnings."*

### Violations: 0 *(fixed in v0.13.7)*

### v0.13.7 fix shipped

CMake gains an `ES_PEDANTIC` option (default OFF) that elevates the existing pedantic warning flags to errors:

| Toolchain | Existing flags | With `ES_PEDANTIC=ON` |
|---|---|---|
| gcc / clang | `-Wall -Wextra -Wpedantic` | + `-Werror` |
| MSVC | `/W4` | + `/WX` |

The `pedantic-build` CI job in `.github/workflows/ephemerides-spectral-ci.yml` runs a 3-cell matrix (`ubuntu-latest` gcc, `macos-14` clang, `windows-latest` MSVC) with `ES_PEDANTIC=ON`. Always-on (not gated by `wheel-check`) — Rule 10 is a permanent invariant, not a per-PR opt-in.

Local MSVC `/W4 /WX` build verified clean. The cross-platform CI matrix catches the gcc/clang-specific warnings (different toolchains warn on different patterns).

### Why CI-only and not pinned in test_jpl_audit.py

Compiler warnings are toolchain-side and toolchain-version-dependent — gcc-13 might warn on a pattern gcc-14 silently accepts. Pinning a count in a Python test file would be brittle and would couple the source tree to a specific CI runner image. The CI job IS the ratchet — drop the pin (the warning), drop the build failure.

The pinned ratchets in `test_jpl_audit.py` cover Rules 1-5 (source-side patterns); Rule 10 is enforced by the CI build itself (toolchain-side). Both ratchets are one-way: violations can only be removed, never silently accumulated.

---

## Discipline (the v0.11.2 ship)

This audit document is paired with [`tests/test_jpl_audit.py`](../python/tests/test_jpl_audit.py), which encodes the violation counts above as **pinned baselines**. Every PR runs the test as part of the regular suite:

- Counts at or below the pin → **pass**.
- Counts above the pin → **fail** (a new violation slipped in; PR must either fix it or update the pin upward with explicit justification).

Same modular discipline as the other v0.x.x freshness/parity invariants:
- `test_native_version_string_matches_package_version` — C ↔ Python version pin.
- `test_parity_smoke.py::PARITY_TARGETS` — every bridge function classified.
- `test_readme_freshness.py` — Status / banner / CLI body-name examples in the PyPI README.
- `test_jpl_audit.py` *(this ship)* — JPL Power-of-Ten violation counts.

The pattern: enumerate the truth, fail loudly on drift, reduce on improvement.

---

## Roadmap

The v0.11.3-v0.11.7 numbering originally queued at the v0.11.2 audit ship is **obsolete**. After the audit landed, the project shipped v0.12.0 (Sol Kinematics) and v0.13.0 (Sol Dynamics) ahead of the JPL rule-fix work, so the rule-fix patches are renumbered to land in the **v0.13.x** series instead. The audit document and the ratchet pins are unchanged; only the version labels move.

| Version | Focus |
|---|---|
| v0.11.2 *(shipped)* | Audit-only. Document violations; pin counts in CI as a one-way ratchet. No code changes. |
| **v0.13.4** | **Rule 1 + Rule 3 fixes** — refactor `es_hd_state.c` HD pipeline to remove `goto` + `malloc`. Combined fix using static buffers for embedded targets / caller-supplied buffers for dynamic-D library use. |
| **v0.13.5** | **Rule 4 fixes** — split the 4 long functions into JPL-compliant <60-line factors. |
| **v0.13.6** | **Rule 5 fixes** — add 64+ assertions across the 32 functions to hit the 2/function average. Gate behind `#ifndef NDEBUG`. Flips the Rule-5 density skip in `test_jpl_audit.py` to passing. |
| **v0.13.7** | **Rule 10 audit** — cross-platform pedantic-build CI matrix (`-Wall -Wextra -Wpedantic` for gcc/clang; `/W4` for MSVC); document warning counts; iterate. |
| **v0.13.8** | **Rule 6 + Rule 7 audits** — manual passes for variable scope + return-value checking. |
| v0.14.0+ | First non-audit minor after the JPL series. Likely Sol Moon Times (`#86`) or the SPICE-gap fills from `#101`. |

Each v0.13.x rule-fix ship updates this audit document AND drops the corresponding pin in `test_jpl_audit.py`. The ratchet structure means even partial progress (e.g., removing 3 of 5 `goto`s in v0.13.4) lowers the pin and is permanently locked in.

In-prose version references throughout the rest of this document still say "v0.11.3+" — those mean "the current rule-fix series, now starting at v0.13.4." Replace mentally if you're reading old captures of this file.
