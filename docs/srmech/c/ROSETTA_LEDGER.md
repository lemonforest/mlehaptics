# srmech Rosetta-completeness ledger

**Goal.** A *complete C mirror of the Python surface* — every public Python op
has a C twin that is **bit-exact** and **dispatched to**, OR is a composition of
such twins. Then the C partition (`libsrmech`) runs **standalone**: on a full OS
*or* on a thread-less, OS-less microcontroller, with no host Python. C:Python
parity is the program's *form*, not a means to embedded — there are **no
exemptions**.

This file is the down-only **debt ledger** for that goal (like the C-transpile
libm ratchet that went 23 → 0): the `python_only_irreducible` count only ever
decreases. Each rc drives it down; a clean `v0.7.5` graduation waits until the
debt is closed.

---

## Two hardware abstractions make a complete mirror possible

The C core stays **machine- and OS-agnostic**; everything platform-specific
lives behind one of two sibling abstraction layers. In the project's framing the
OS *is* part of the hardware the binary runs on, so both "qualify as hardware":

| Layer | Abstracts | The one place its `#ifdef`s live | Consumers |
|-------|-----------|----------------------------------|-----------|
| **HAL** — `c/src/srmech_simd.{h,c}` | the **CPU** (SIMD tiers, cpuid, target-attrs) | `srmech_simd.c` | `srmech_sha256_batch.c`, `srmech_loopbind_hd.c` |
| **PAL** — `c/src/srmech_platform.{h,c}` (rc4) | the **OS** (threads now; stream IPC next) | `srmech_platform.c` | `srmech_parallel.c` (rc4); `srmech_bus.c` (next) |

Per `[[feedback_simd_optimize_path_goes_through_hal]]`, generalised from the CPU
to the OS: *machine-specific bits go behind another `*.h`; the core stays
agnostic.* A functional core (`srmech_parallel.c`, the cascade kernels, …)
carries **zero** `#ifdef _WIN32`.

**Build authority.** The full surface builds clean on Linux via **WSL2**
(`gcc`/`cmake`), pedantic `-Werror`; this is the canonical standalone-C build/test
loop. CI's cross-OS matrix (Linux gcc / macOS clang / Windows MSVC) is the gate.

---

## The classification (every public Python op falls in one bucket)

1. **`c_dispatched`** — has a `srmech_*` C twin, bound in `_native.py`, and the
   Python op dispatches to it. *(sha256, ndjson, cyclic, primes, laplacian,
   dispatch/catalog/template, hdc loop family, cascade atoms, Schur/DtN,
   Cayley–Dickson cocycle, the_one/hurwitz, trig (rc2), exp/log/sqrt (rc3), …)*
2. **`c_exists_unbound`** — a C twin exists but Python doesn't yet bind/dispatch
   it. *Cheap debt: bind it.*
3. **`composition_of_c`** — no single C twin, but the op is a pure composition
   of bucket-1 C kernels (e.g. a `qm.*` operator that is matmul ∘ eig ∘ kron).
   Closing it = expressing the composition in C (no new irreducible kernel).
4. **`python_only_irreducible`** — **the debt.** An irreducible compute kernel
   with no C twin and not yet a composition of C kernels (the bulk: the
   `qm.*` dense-linear-algebra layer + a few bignum-in-C gaps). **Drive to 0.**

> A *separate, intentional* tier sits outside the debt: the exact-rational
> **bignum reference** surfaces (`*_series_truncate`, the `precision_bits` sqrt).
> They are arbitrary-precision oracles the C-bit-exact cascades are checked
> against — like a higher-precision reference instrument, not a parity gap.

---

## Roadmap (rolling; each rc drives the debt down)

- **rc4 (this) — PAL born + parallel.c retrofit + WSL2 Linux build authority.**
  Establishes the OS-abstraction layer (threads) so the OS-touching C becomes
  portable; the architecture for a complete standalone mirror is now in place.
- **rc5 — PAL stream/IPC + `srmech_bus.c` retrofit.** The bus's AF_UNIX-socket /
  named-pipe duality moves behind `srmech_plat_stream_*`; `srmech_bus.c` becomes
  `#ifdef`-free — the last raw-OS surface closed.
- **rc6+ — `qm.*` C kernels.** Port the irreducible linear-algebra kernels
  (complex matmul / hermitian-eig / kron / …) to C as bit-exact Rosetta twins,
  then express the `qm.*` operators as C compositions. Each lands a chunk of
  `python_only_irreducible → composition_of_c`, the debt ticking toward 0.

The exhaustive per-op cross-reference table + a `test_rosetta_completeness.py`
ratchet (asserting `python_only_irreducible` is monotone-decreasing) lands in
rc5 alongside the bus retrofit, once the second consumer proves the PAL shape.
