# srmech — C library

Native-C parity surface for the [`srmech`](../python/) Python package's
Attested Multi-Source Collector (AMSC) framework. Ports the three
load-bearing AMSC primitives to portable C so srmech meets the same
**Python/C parity discipline** that
[`ephemerides-spectral`](../../antikythera-maths/ephemerides-spectral/c/)
uses. Same monorepo, same quality bar.

## Status — Phase B1 scaffolding only

This directory currently ships **scaffolding only**: header, Makefile,
CMakeLists wiring (one level up), JPL audit doc, .gitignore, .pages.
No `.c` file exists yet. The library compiles to an empty archive
and the Python package falls back to its pure-Python implementations
of every API surface. Phase B3 onward replaces the stubs with real
code.

| Phase | Deliverable                                    | Version    |
| ----- | ---------------------------------------------- | ---------- |
| B1    | C tree scaffolding (this directory)            | `0.1.1rc3` |
| B2    | scikit-build-core + CMake + pyproject-pure     | `0.1.1rc4` |
| B3    | `srmech_sha256_hex` — first symbol, first parity test | `0.1.1rc5` |
| B4    | `srmech_ndjson_iter` — streaming NDJSON reader | `0.1.1rc6` |
| B5    | `srmech_toml_canonical_hash` — descriptor hash | `0.1.1rc7` |
| B6    | JPL Power-of-Ten audit + JPL_AUDIT.md          | `0.1.1rc8` |
| B7    | cibuildwheel matrix + production v0.2.0 cut    | `0.2.0`    |

Each rc auto-routes to TestPyPI via the rc-suffix gate in
`srmech-publish.yml`. The non-rc `0.2.0` tag is the human-in-loop
gate for the production PyPI ship.

## Why C

srmech is **data-pipeline tooling, not embedded firmware** — but C
buys us three things ephemerides-spectral has already validated:

1. **Performance on hot paths.** Every catalog read walks NDJSON;
   every descriptor edit recomputes the canonical-TOML hash;
   SHA-256 attestation is per-row at codegen time. The Python paths
   stay correct; C is the fast path runtime can opt into.
2. **Parity discipline as quality ratchet.** The byte-exact Python/C
   parity tests catch any drift in either implementation. The C
   side is harder to get right; passing parity is evidence the
   Python side is also correct.
3. **JPL Power-of-Ten discipline** (Phase B6). The same rules
   ephemerides-spectral's C library passes — Rule 1 (no goto),
   Rule 3 (no malloc), Rule 4 (<60-line functions), Rule 5
   (≥2 assertions per function), Rule 6+7 (scope + return-value
   checks), Rule 10 (cross-platform pedantic-build CI matrix).

## Layout

```
c/
├── include/srmech.h                # public API (Phase B1)
├── src/                            # implementation .c files (B3–B5)
│   └── .gitkeep                    # placeholder; empty at B1
├── test/                           # C smoke + cross-language parity
│   └── .gitkeep                    # placeholder; empty at B1
├── Makefile                        # local build/test/parity flow
├── JPL_AUDIT.md                    # JPL Power-of-Ten compliance log
├── .gitignore                      # build/
├── .pages                          # mkdocs nav
└── README.md                       # this file
```

The top-level CMakeLists.txt lives one directory up at
`docs/srmech/CMakeLists.txt`, mirroring ephemerides-spectral's
`docs/antikythera-maths/ephemerides-spectral/CMakeLists.txt`.
scikit-build-core (wired in Phase B2) drives it via
`cmake.source-dir = ".."` from `python/pyproject.toml`.

## Build & test (post-B3)

```bash
cd c

# Build the static library
make lib

# Build + run the C smoke tests
make test

# Build + run the cross-language parity test
make parity

# Clean
make clean
```

`make` defaults to `cc -std=c17 -Wall -Wextra -Wpedantic -O2 -fPIC`.
Override `CC` and `STD` for cross-compilation; the source compiles
cleanly under C11.

### Windows note

The `feedback_run_wsl_smoke_before_amsc_push` memory applies once
real C code lands. WSL2 catches libm last-bit divergence that
Windows-local pytest doesn't. Run `scripts/smoke_local.sh` (or the
equivalent) under WSL before pushing any branch that touches C
source.

## License

GPL-3.0-or-later (parent project: mlehaptics).
