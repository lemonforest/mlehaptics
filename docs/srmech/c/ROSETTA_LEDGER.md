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
| **PAL** — `c/src/srmech_platform.{h,c}` (rc4–rc5) | the **OS** (threads rc4; stream IPC rc5) | `srmech_platform.c` | `srmech_parallel.c` (rc4); `srmech_bus.c` (rc5) |

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

## Do-not-mirror gate — known Python bugs (issue [#928](https://github.com/lemonforest/mlehaptics/issues/928))

The Rosetta law is a **bit-exact** C twin. That cuts both ways: bit-exact
mirroring of a *buggy* Python op enshrines the bug in **two** places instead of
one. So before any op crosses Python → C, check it against the open-bug list in
the consolidated wishlist tracker (issue #928 / `rbs_lm_research/SRMECH_BUGFIX_WISHLIST.md`).
**A known-defective Python op is resolved on the Python side FIRST, then its
corrected behaviour is what the C twin mirrors.** Never port a `🔴 OPEN` /
`CONFIRM` row to C.

Open rows that intersect this arc (as of 2026-06-08):

| # | Bug | Intersection | Gate |
|---|-----|--------------|------|
| **W5** | `klein4_bundle` even-count behaviour vs prior "odd-only" note (CONFIRM) | rc13 shipped the klein4 `sectors=` splay **pure-Python**, with "standalone-C sector dispatch is the tracked follow-up". | **Resolve/confirm W5 BEFORE the klein4 standalone-C port** — otherwise the ambiguous even-count semantics freeze into C. Highest-risk row. |
| **W4** | `sha256_bytes` returns a hex *string*, not `bytes` | sha256 is already `c_dispatched` (`srmech_sha256_hex` → hex); the contested return-type is a Python API contract the C twin already matches. | Don't enshrine further; re-decide the return-type at the next sha256 touch, then align C. |

MCP-layer rows (W1 `naming_lookup` kwarg-drift, W3 non-JSON schema leak) are
wrapper-surface, not compute kernels — outside the C-mirror surface entirely.

---

## The measured baseline (rc7 audit; issue [#928](https://github.com/lemonforest/mlehaptics/issues/928))

The rc7 audit enumerated the **348 public compute-or-not ops** across
`srmech.amsc` / `srmech.qm` / `srmech.signal_processing` and classified every
one by reading its implementation against the exported C-symbol surface. The
result is the committed SSoT `python/tests/rosetta_classification.ndjson`, pinned
by the `python/tests/test_rosetta_completeness.py` ratchet (regenerate via
`notes/_rosetta_inventory.py` → `notes/_rosetta_build_classification.py`):

| Bucket | Count | Standalone-C? |
|--------|------:|---------------|
| `c_dispatched` | 78 → **79** | ✅ runs on libsrmech alone |
| `composition_of_c` | 61 → **71** | ✅ pure composition of C-dispatched ops |
| `bignum_reference` | 22 | ➖ intentional exact-rational oracle tier (not debt) |
| `non_compute` | 56 | ➖ IO / registry / schema / introspection (no kernel) |
| **`c_exists_unbound`** | 23 → **12** | ❌ **DEBT (cheap):** a C twin exists, Python doesn't dispatch |
| **`python_only_irreducible`** | **108** | ❌ **DEBT:** irreducible kernel, no C twin yet |

**Total standalone-C debt = 131 → 120** (108 irreducible + 12 unbound). The
ratchet's two ceilings start at the rc7 baseline and only move **down**:
rc8 took the first 6 off (the SHA-256 mint cluster), rc9 the next 3 (octonion
L/R-multiply + conjugate → the C-backed `hdc.loop_*` family), rc10 the next 2
(`cd_basis_product` → `srmech_cd_basis_product`; `octonion_mult_table` composes it).

### What collapses the most debt (the rc8+ work-list, by leverage)

The 108 irreducible are not 108 distinct problems — they cluster on a **handful
of missing C kernels**. One kernel each clears a column:

| Missing C kernel | Clears (approx) | Where |
|------------------|-----------------|-------|
| **dense complex `matmul`** (matrix×matrix) | ~15 | qm: `commutator`, `gamma_5`, `casimir_*`, `clifford_residuals`, `wilson_loop`, `heisenberg/liouville_evolve`, `harmonic_oscillator_hamiltonian`, … (matvec twin already exists; matmul is the gap) |
| **FFT/DFT** (radix-2 + Bluestein) | ~20 | sp: `fft/ifft/rfft/stft/spectrogram/cross_spectral/multitaper/wiener/spectral_subtraction/ofdm` (Path A+B) + cascade `dft/fft/idft/ifft` |
| **general dense `eig`/`SVD`/`QR`/`lstsq`** | ~16 | qm `so8.*` + `triality.*` (svd/lstsq/qr/pinv/rank), cascade `matrix_cascades.{qr,svd,lstsq,eigvals}`, sp `esprit/mimo_svd/map_ml` |
| **`kron`** (tensor product) | ~6 | qm `bell.*` CHSH family + `so8` binders |
| **`einsum` / `convolve` / `correlate`** | ~8 | sp `ica_jade/fir/multirate/polyphase/matched_filter`, cascade `einsum` |

The remaining irreducible are pure-Python DP/codec loops (Viterbi, Huffman,
LZ77, RLE, arithmetic-coding, wavelet, JPEG, PSK/QAM/FSK) + the numpy-`eigh`
Laplacian pair + the Klein-4/polar relabel ops — each its own small port.

### The cheap wins (`c_exists_unbound` — wire-up only); 23 → 17 after rc8

A bit-exact C twin **already ships**; the Python just never calls it:

- ~~**SHA-256 mint cluster (6):** `mint_*` / `encode_loe_content` / `compute_content_stride` call **raw `hashlib.sha256`** instead of the C SHA-256~~ — **✅ CLOSED rc8:** routed through `format.sha256_raw` (native dispatch; bit-identical raw-32 digest), reclassified → `composition_of_c`. Also cleared the CLAUDE.md raw-`hashlib` discipline violation. *(W4-aware: these are `.digest()` raw-byte sites, so `sha256_raw` — not the hex `sha256_bytes` — is the correct twin.)*
- **HDC Klein-4 / polar (8):** `klein4_{bind,bundle,similarity,triality_cycle,unbind}` + `polar_{bind,bundle,density}` — twins `srmech_klein4_*` / `srmech_polar_*` exported, Python is numpy-free pure-Python. **`klein4_*` gated on W5** (`klein4_bundle` even-count) per the do-not-mirror gate.
- **Octonion einsum (4):** `octonion_{left_mult,right_mult,conjugate,mult_table}` — twins `srmech_loop_{left_op,right_op,conj_hd}_f64` + `srmech_cd_basis_product`.
- **Hamming GF(2) (3):** `hamming_{encode,syndrome,decode_correct}` — twins `srmech_hamming_*` exported, module has **no `_native` import at all**.
- **`cd_basis_product` (1)** + **`lmmse` (1)** (`np.linalg.solve` → `srmech_dense_solve_f64`).

Remaining cheap wins after rc8: **17** (the four bullets above). The natural
next sweeps are the **octonion einsum (4)** and **Hamming (3)** — both have
exported twins and no W5 gate — then the W5-cleared klein4 family.

## Roadmap (rolling; each rc drives the debt down)

- **rc4 (done) — PAL born + parallel.c retrofit + WSL2 Linux build authority.**
- **rc5 (done) — PAL stream/IPC + `srmech_bus.c` retrofit** (last raw-OS surface closed).
- **rc6 (done) — W17 `coupled_wave` + W18 `multiplex_streams`** (active-arc named ops; `composition_of_c`, no new C debt).
- **rc7 (done) — the Rosetta-completeness AUDIT + ratchet.** 348 ops
  classified; `test_rosetta_completeness.py` pins `python_only_irreducible ≤ 108`
  and `c_exists_unbound ≤ 23`, both monotone-down, plus a live↔classified
  exact-match guard so every new op must be bucketed.
- **rc8 (done, this) — cheap-win sweep #1: the SHA-256 mint cluster.** The 6
  `signal_processing` mint/stride ops routed off raw `hashlib.sha256` onto
  `format.sha256_raw` (native dispatch, bit-identical) → `composition_of_c`;
  `c_exists_unbound` ceiling **23 → 17**. Closes the CLAUDE.md raw-`hashlib`
  discipline gap in the same move.
- **rc9+ — keep closing debt by the leverage tables above.** Each kernel port +
  dispatch-wire moves ops `python_only_irreducible`/`c_exists_unbound →
  `c_dispatched`/`composition_of_c`, **lowering the ceiling in lockstep**. Next
  cheap sweeps: octonion einsum (4) + Hamming (3) (no gate), then the
  W5-cleared klein4 family; biggest single lever is a dense complex `matmul`.

**Standing tracker.** Issue [#928](https://github.com/lemonforest/mlehaptics/issues/928)
is the consolidated srmech wishlist (bugs · schema · enhancements · new ops,
W1–W18). Consult it at every rc boundary: (1) the do-not-mirror gate above
before any Python→C port, and (2) the stale-vs-missed sweep per
`[[feedback_tracker_lookback_stale_vs_missed_each_sprint]]`.
