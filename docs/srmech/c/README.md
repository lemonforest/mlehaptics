# srmech — C library

Native-C parity surface for the [`srmech`](../python/) Python package's
Attested Multi-Source Collector (AMSC) framework. Ports the three
load-bearing AMSC primitives to portable C so srmech meets the same
**Python/C parity discipline** that
[`ephemerides-spectral`](../../antikythera-maths/ephemerides-spectral/c/)
uses. Same monorepo, same quality bar.

## Status — full 14-class native C parity shipped

The full **14-class A–N C-parity primitive vocabulary** is implemented
in native C and ships in every platform wheel as
`libsrmech.{so,dll,dylib}`. The Python package binds it through a
ctypes shim (`srmech.amsc._native`) and falls back to a complete
pure-Python implementation of every API surface when no native
library is present (Pyodide / WASM, or any environment where the
shared library can't load). srmech is at **v0.6.0rc9**; this is no
longer scaffolding.

### Source files (`c/src/`)

| File | Surface |
| ---- | ------- |
| `srmech_sha256.c`   | Class A — FIPS 180-4 SHA-256 content-addressing |
| `srmech_ndjson.c`   | Class C — streaming NDJSON line reader |
| `srmech_cyclic.c`   | Class I — cyclic-group / modular arithmetic |
| `srmech_laplacian.c`| Class L — dense graph Laplacian + Jacobi eigvals |
| `srmech_primes.c`   | Class J — primality / factorisation / order |
| `srmech_tlv.c`      | Class B — TLV byte-canonical framing |
| `srmech_search.c`   | Class G — byte-pattern search |
| `srmech_meta.c`     | Class H — version + ABI self-introspection |
| `srmech_dispatch.c` | Class D — multi-needle pattern dispatch |
| `srmech_catalog.c`  | Class E — sorted-key catalog lookup |
| `srmech_template.c` | Class F — template `{key}` substitution |
| `srmech_hdc.c`      | Class M — HDC bind / bundle / permute / similarity |
| `srmech_rational.c` | Class N — rational approximation (best-rational) |
| `srmech_kepler.c`   | equation-of-centre / Kepler algebra (libm) |
| `srmech_cascade.c`  | cascade-composition primitives |
| `srmech_bus.c`      | bus / handle-registry surface |
| `srmech_parallel.c` | Klein-4 four-sector parallel dispatch |
| `srmech_kuramoto.c` | native Kuramoto coupled-oscillator step |

The two newest v0.6.0 C files:

- **`srmech_parallel.c`** — the Klein-4 four-sector parallel dispatch
  (#771 / #778), with a portable thread shim that selects pthreads,
  Win32 `CreateThread`, or a serial fallback at build time so the
  same source compiles cleanly across the CI matrix.
- **`srmech_kuramoto.c`** — the native Kuramoto coupled-oscillator
  forward-Euler step (rc9), using libm `sin` exactly as
  `srmech_kepler.c` does.

### ABI

C ABI version is **3** (`SRMECH_ABI_VERSION 3` in
`c/include/srmech.h`). Bump it in lockstep only when the wire
format of an existing exported function changes; adding a new
symbol does not bump the ABI.

### JPL Power-of-Ten

The C library is **JPL Power-of-Ten clean** — see
[JPL_AUDIT.md](JPL_AUDIT.md) for the rule-by-rule audit.
Enforcement is mechanical: `tests/test_jpl_audit.py` is a ratchet
(violations only ever go down) and the pedantic-build CI matrix
(`-Werror` / `-Wpedantic`, `/WX` on MSVC) runs on
Linux gcc / macOS clang / Windows MSVC, so any new warning fails CI.

Each rc auto-routes to TestPyPI via the rc-suffix gate in
`srmech-publish.yml`. A non-rc tag is the human-in-loop gate for
the production PyPI ship.

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

MIT (parent project: mlehaptics).
