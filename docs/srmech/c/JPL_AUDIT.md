# srmech C — JPL Power-of-Ten Audit

Mirrors `docs/antikythera-maths/ephemerides-spectral/c/JPL_AUDIT.md`
in structure. Tracks compliance with Holzmann's
[JPL Power-of-Ten](https://web.eecs.umich.edu/~imarkov/10rules.pdf)
rules for safety-critical C.

## Phase B1 — scaffolding only

This file is reserved. No `.c` files exist in `src/` yet, so there
is nothing to audit. The audit is populated phase-by-phase as code
lands:

| Phase | Audit content                                          |
| ----- | ------------------------------------------------------ |
| B3    | Rule survey for `srmech_sha256.c`                      |
| B4    | Rule survey for `srmech_ndjson.c`                      |
| B5    | Rule survey for `srmech_toml_canonical.c`              |
| B6    | **Full audit pass** — Rules 1–10 enumerated, per-function assertion counts, cross-platform pedantic-build CI matrix configured |

## Rules under audit (from Phase B6 onward)

| # | Rule                                                       | Strategy                                                    |
| - | ---------------------------------------------------------- | ----------------------------------------------------------- |
| 1 | No goto, setjmp/longjmp, recursion                         | Linter pass; manual review per file                         |
| 2 | All loops have fixed upper bounds                          | Each loop annotated with explicit bound macro               |
| 3 | No dynamic allocation after init                           | Bounded buffers; caller-supplied output                     |
| 4 | Functions ≤ 60 lines                                       | Mechanical: line-count CI ratchet                           |
| 5 | ≥ 2 assertions per function                                | `assert()` ratchet enforced by audit-counter test           |
| 6 | Smallest possible scope                                    | Manual review per file                                      |
| 7 | Return values checked                                      | `-Wunused-result` + manual audit                            |
| 8 | No preprocessor abuse                                      | Only `#include`, `#define` (constants), `#ifdef` (platform) |
| 9 | Restrict pointer use; single dereference per expression    | Manual review per file                                      |
| 10 | Compile with all warnings as errors                       | `ES_PEDANTIC=ON` equivalent (`SRMECH_PEDANTIC=ON`) + CI     |

## Historical context

Tasks #105–#110 brought ephemerides-spectral's C library to JPL
compliance in v0.13.x. Phase B6 of Task #201 applies the same
audit pattern to srmech. The ephemerides-spectral audit doc is the
template for the eventual srmech audit:
[ephemerides-spectral JPL_AUDIT.md](../../antikythera-maths/ephemerides-spectral/c/JPL_AUDIT.md).
