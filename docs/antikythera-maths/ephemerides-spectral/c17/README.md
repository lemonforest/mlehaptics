# ephemerides-spectral — ANSI C17 BIP encoder

Embedded-friendly C kernel for the integer-only Phase 9 `encode_state`
path. Direct port of `EphemerisBIPInstrument._encode_state_impl` from the
Python `ephemerides-spectral` package; **byte-exact parity** with the
Python reference encoder over the +20 yr smoke-test horizon.

## Why C17

The Python BIP encoder is already integer-only — `(φ₁ + φ₂) mod 2³²`
hits `uint32` overflow directly with no FPU calls. Porting that path to
ANSI C17 makes it directly drop-in for embedded targets that don't ship
a Python runtime: ESP32, Cortex-M, RISC-V, FPGA softcores. **No libm
inside the chunk loop**, no malloc, no Skyfield, no Python at runtime.
The single float touchpoint is `delta_t_days`, consumed once at the
top of `es_encode_state`.

## Layout

```
c17/
├── include/ephemerides_spectral.h   # public C API
├── src/
│   ├── es_encode.c                  # encode_state, hand-written
│   ├── es_bodies.c                  # codegen — 26-body roster
│   ├── es_laplacian.c               # codegen — omega_diag, initial_phases, couplings
│   └── es_cosine_lut.c              # codegen — 1024-entry int32 LUT (Q1.14)
├── test/
│   ├── test_es_encode.c             # 9 C unit tests + parity payload emission
│   └── test_parity_python.py        # builds C, runs both, byte-compares phases
├── codegen/
│   └── emit_c_tables.py             # SSOT codegen from Python research modules
├── manifest.json                    # SHA-256s of the codegen-emitted C files
├── Makefile                         # build / test / parity / codegen / clean
└── README.md                        # this file
```

## Build & test

```bash
cd c17

# Build the static library + smoke test binary
make

# Run the C smoke tests (9 assertions)
make test

# Run the cross-language parity test
# (requires Python with the research/ tree importable)
make parity

# Re-emit the C tables from the Python research modules
# (run after any change to research/{bodies,laplacian,bip_instrument}.py)
make codegen
```

The Makefile defaults to `gcc -std=c17 -Wall -Wextra -Wpedantic -O2`.
Override `CC` and `STD` for cross-compilation:

```bash
make CC=arm-none-eabi-gcc STD=c11 CFLAGS="-mthumb -mcpu=cortex-m7 -O2"
```

## Embedded usage

The encoder is reentrant and allocates nothing on the heap. Stack
footprint: `2 * ES_N_BODIES * sizeof(uint64_t) + ES_N_BODIES *
sizeof(int64_t)` ≈ 624 bytes for D=26 bodies. The const tables
(`es_bodies`, `es_omega_diag`, `es_initial_phases`, `es_couplings`,
`es_cosine_lut`) total ~6 KB and live in `.rodata`.

```c
#include "ephemerides_spectral.h"

uint32_t phases[ES_N_BODIES];
es_status_t st = es_encode_state(20.0 * 365.25, phases);
if (st != ES_OK) { /* handle */ }

/* phases[i] is body i's phase in Z_{2^32}.
 * For Earth (idx = es_body_index("earth")):
 *   double rad = es_residue_to_radians(phases[idx]);
 *   double deg = rad * 180.0 / M_PI;
 */
```

## Codegen + manifest discipline

`codegen/emit_c_tables.py` reads the canonical Python research
modules (`research/bodies.py`, `research/laplacian.py`,
`research/bip_instrument.py`) and emits the three C source files
plus a `manifest.json` carrying SHA-256 sums. Same Python research
code → same C tables → same SHAs.

The Python wheel ships its own `_data/manifest.json` — sibling to
this `manifest.json` — so a consumer who installs both can verify
they came from the same research-tree commit.

## Cross-language parity

`make parity` runs the C smoke-test binary, parses the
`PARITY_PAYLOAD` JSON line it emits, encodes the same JD with the
Python `EphemerisBIPInstrument`, and asserts byte-for-byte agreement
on all 26 phases. Floor-division semantics (`Python a // b` vs
`C a / b`) are reconciled by the `es_floor_div` helper in
`src/es_encode.c` so negative numerators round identically.

## Status

* **v0.1.0** (2026-05-04) — initial C17 port. 9 smoke tests pass; 26
  bodies match the Python reference byte-for-byte at +20 yr from
  J2000. Phase 9 breathing-coupling table currently wires only the
  Jupiter-Saturn 5:2 entry (matches Python v0.1.0).
* **Roadmap:** see [`../ROADMAP.md`](../ROADMAP.md). Phase 9 coverage
  extension (Neptune-Pluto 3:2, Io-Europa 1:2, Earth-Moon precession,
  Jovian Trojans) lands in the C tables automatically when the Python
  research adds them — `make codegen` re-syncs.

## License

GPL-3.0-or-later (parent project: mlehaptics).
