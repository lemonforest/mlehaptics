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
ctypes shim (`srmech._native`) and falls back to a complete
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

C ABI version is **25** (`SRMECH_ABI_VERSION 25` in
`c/include/srmech.h`). The v25 bump is rc464's (`#T1188`) and it is the fourth of the REMOVAL kind (v7 / v8 / v11 before it), the plainest shape there is. Three exported symbols go — `srmech_sedenion_navmap`, `srmech_sedenion_navigate` and `srmech_sed_slots` — with the 16-slot `SedenionRegister` they were the Rosetta peer of. They are SUBSUMED, not dropped: `srmech_cd_navmap` / `srmech_cd_navigate` take the rung as a parameter and this header has documented them as bit-identical at dim 16 since rc298, and `srmech_sed_slots` was a validate-and-copy its one caller now does inline. A removed export produces no symptom other than a version mismatch, so by standing policy it always bumps. The `SRMECH_SEDENION_NUM_SLOTS` macro goes with them and contributes nothing — macros are not exported symbols. `srmech_sedenion_is_navigable` STAYS: it is the general DENSE kernel for every rung up to `SRMECH_CD_DENSE_MAX_DIM`, dispatched live by `left_mult_is_invertible`, and only its NAME was ever sedenion-specific. rc464 also changes what one existing function returns — `srmech_make_class_run_arena_bytes` now budgets the TOML parser's own stated bound instead of a hand-rolled `32 * toml_len` heuristic, so the envelope is LARGER — which is the v10 / v12 / v23 / v24 wire-sizing shape and would have bumped on its own; it rides this one. `SRMECH_GENOME_FORMAT_VERSION` stays 20.

The v24 bump before it is rc455's, and it is the SECOND instance of
a shape this header already recorded one function over. `srmech_dsl_chain_run`'s
writer reserve was derived from the INPUT length while it bounds the OUTPUT
tree, so `srmech_dsl_chain_run_arena_bytes` now returns a **smaller** envelope —
by exactly `32768 + 16*(chain_len + input_len)` — with the json builder, the
emit scratch and the write scratch carved forward from the value actually
produced instead. No signature changed and no symbol was added or removed; what
moved is what an existing function returns, which is the v10/v12 wire-sizing
shape. rc452's v23 note in `srmech.h` covers exactly that move on the SIBLING
`srmech_chain_run_arena_bytes` and says it "rides this bump rather than going
unrecorded", so declining here would leave the second instance of a recorded
shape unrecorded. Neither mixed-version pairing computes a wrong value: an old
(larger) cached figure over-provisions a v24 library, and a new (smaller) figure
handed to a v23 library gets a correct `SRMECH_ERR_OVERFLOW`.

*(⚠️ The narrative under this heading has lagged the integer even while the
integer was gated. At rc454 this paragraph still explained the **v20** bump —
rc451's `{"k":"t"}` TUPLE kind — beside a correct **23**, three bumps behind,
because `test_abi_prose_currency_rc449.py` asserts one decidable thing per file
(the integer equals the macro) and deliberately does not read the surrounding
rationale. That is the right scope for that gate and it is also the residual: a
number that cannot go stale above a story that can. rc455 rewrote the story with
the number.)*

*(This line read **3** from the v0.5.0 era until rc442 —
fourteen bumps stale, and wrong long before that release touched it. It then went
stale AGAIN five rcs later: rc447 bumped 17 → 18 and rc448 shipped over it, so by
rc449 it was two behind. The note that used to sit here said "no gate covers
`c/README.md` at all, which is exactly why it drifted the furthest" — and then it
drifted again, which is the whole argument. rc449 (`#T1158`) closed that:
`tests/test_abi_prose_currency_rc449.py` now reads this line and
`docs/srmech/CLAUDE.md`'s "ABI compatibility" section against the macro. The SSoT
is still the macro; the narrative SSoT is still that CLAUDE.md section.)* Bump it in lockstep only when the wire
format of an existing exported function changes; adding a new
symbol does not bump the ABI.

### JPL Power-of-Ten

The C library is clean on **eight** of the ten Power-of-Ten rules;
**Rule 1 (recursion half) and Rule 9 (function-pointer half) are
PARTIAL**, each under a seeded down-only ratchet — see
[JPL_AUDIT.md](JPL_AUDIT.md) for the rule-by-rule audit and the
measured Rule 9 census. *(This line said "JPL Power-of-Ten clean"
until rc452.)*
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
