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
| `c_dispatched` | 78 → **85** | ✅ runs on libsrmech alone |
| `composition_of_c` | 61 → **73** | ✅ pure composition of C-dispatched ops |
| `bignum_reference` | 22 | ➖ intentional exact-rational oracle tier (not debt) |
| `non_compute` | 56 | ➖ IO / registry / schema / introspection (no kernel) |
| **`c_exists_unbound`** | 23 → **5** | ❌ **DEBT (cheap):** a C twin exists, Python doesn't dispatch |
| **`python_only_irreducible`** | **108** | ❌ **DEBT:** irreducible kernel, no C twin yet |

**Total standalone-C debt = 131 → 113** (108 irreducible + 5 unbound). The
ratchet's two ceilings start at the rc7 baseline and only move **down**:
rc8 took the first 6 off (the SHA-256 mint cluster), rc9 the next 3 (octonion
L/R-multiply + conjugate → the C-backed `hdc.loop_*` family), rc10 the next 2
(`cd_basis_product` → `srmech_cd_basis_product`; `octonion_mult_table` composes it),
rc11 the next 3 (Hamming GF(2) `encode`/`syndrome` → `srmech_hamming_*`;
`decode_correct` composes the syndrome twin), rc12 the next 3 (the polar-HDC trio
`polar_{bind,bundle,density}` → `srmech_polar_*`), rc13 the next 1 (`lmmse` routes
its solve → `dense_solve` + its matvec → `dense_matvec_complex` cascades). The
remaining **5 are the Klein-4 family, gated on W5.**

**A sibling source-level guard** lands with rc13: the **numpy-math ratchet**
(`python/tests/test_numpy_math_ratchet.py`) keeps numpy a *carrier*, not a *math
engine* — it greps the srmech source for numpy-math callsites (`np.linalg`/`np.fft`
126 · `@`/`dot`/`einsum`/`kron`/… 185 · transcendental ufuncs 48) and pins each at
a tight down-only ceiling. It is the same debt the 108 `python_only_irreducible`
cluster represents, seen at the source level: a new `np.linalg.solve` fails CI,
and each migration to a cascade decrements both ledgers. (`lmmse` was decrement #1.)

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
- **HDC Klein-4 (5):** `klein4_{bind,bundle,similarity,triality_cycle,unbind}` — twins `srmech_klein4_*` exported, Python is numpy-free pure-Python. **Gated on W5** (`klein4_bundle` even-count) per the do-not-mirror gate — the one cheap cluster still held.
- ~~**HDC polar (3):** `polar_{bind,bundle,density}`~~ — **✅ CLOSED rc12:** dispatch to `srmech_polar_*` (int8 sign-product / sticky-majority / informative-fraction). Bit-exact over 200 trials each.
- ~~**Octonion einsum (4):** `octonion_{left_mult,right_mult,conjugate,mult_table}`~~ — **✅ CLOSED rc9 (3) + rc10 (1):** L/R-mult + conjugate delegate to the C-dispatched `hdc.loop_{left_op,right_op,conj}`; `mult_table` composes the now-native `cd_basis_product` (`srmech_cd_basis_product`). Bit-exact; content-address `7f36461e…` unchanged.
- ~~**Hamming GF(2) (3):** `hamming_{encode,syndrome,decode_correct}`~~ — **✅ CLOSED rc11:** `encode`/`syndrome` dispatch to `srmech_hamming_*` (the v0.7.2rc2 C twin; the module gained its `_native` import); `decode_correct` composes the syndrome twin. Bit-exact over `n∈{2,3,4}` + every single-bit-flip.
- ~~**`lmmse` (1)** (`np.linalg.solve`)~~ — **✅ CLOSED rc13:** the framing was corrected (user direction 2026-06-08) — numpy is a *carrier*, never the math engine, so the `np.linalg.solve` was a **defect**, not a convenience, and the srmech cascade (not LAPACK) is the source of truth. Routed the solve → `dense_solve` + the estimate matvec → `dense_matvec_complex`; reclassified `c_exists_unbound → composition_of_c`. Correct to machine precision (gain residual `≈4e-16`).

Cheap-win sweep is **done** (rc8–rc13). Remaining **5** `c_exists_unbound` are the
**Klein-4 family — gated on W5** (`klein4_bundle` even-count must be confirmed
before its standalone-C sector-dispatch port per the do-not-mirror gate). Beyond
that, debt only falls by **new C kernels** for the 108 irreducible (biggest single
lever a dense complex `matmul`) — tracked at the source level by the **numpy-math
ratchet** (a stray `np.linalg`/`@`/ufunc now fails CI; each cascade migration
decrements it).

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
- **rc9 (done) — cheap-win sweep #2: octonion L/R-mult + conjugate.** The three
  `qm.octonion` einsum ops delegate to the C-dispatched `hdc.loop_*` family →
  `composition_of_c`; `c_exists_unbound` ceiling **17 → 14**.
- **rc10 (done) — cheap-win sweep #3: the Cayley-Dickson basis cocycle.**
  `cascade.cd_basis_product → srmech_cd_basis_product` (`c_dispatched`);
  `octonion_mult_table` composes it (`composition_of_c`); content-address
  `7f36461e…` unchanged; ceiling **14 → 12**.
- **rc11 (done) — cheap-win sweep #4: the Hamming GF(2) block code.**
  `cascade.hamming_{encode,syndrome} → srmech_hamming_*` (`c_dispatched`);
  `hamming_decode_correct` composes the syndrome twin (`composition_of_c`);
  bit-exact over `n∈{2,3,4}` + every single-bit-flip; ceiling **12 → 9**.
- **rc12 (done) — cheap-win sweep #5: the polar-HDC trio.**
  `hdc.polar_{bind,bundle,density} → srmech_polar_*` (`c_dispatched`); all int8,
  bit-exact over 200 trials each; ceiling **9 → 6**.
- **rc13 (done, this) — numpy-math ratchet + lmmse → cascade (decrement #1).**
  Framing correction (user direction): numpy is a *carrier*, never the math
  engine, so the `np.linalg.solve` in `lmmse` was a **defect** — the srmech
  cascade (not LAPACK) is the truth. Routed the solve → `dense_solve` + the
  estimate matvec → `dense_matvec_complex`; `lmmse` reclassifies
  `c_exists_unbound → composition_of_c`, ceiling **6 → 5**. Shipped alongside the
  new **numpy-math ratchet** (`test_numpy_math_ratchet.py`) — the source-level
  down-only guard (`np.linalg`/`np.fft` 126 · `@`/dot/einsum/… 185 · ufuncs 48)
  that keeps numpy a carrier, not a math engine. A stray `np.linalg.solve` now
  fails CI.
- **rc14 (done, this) — the new-C-kernel phase OPENS: dense complex `matmul`.**
  New additive C symbol `srmech_dense_matmul_complex` (`(m,k)·(k,n)`, interleaved,
  ≤256/dim; JPL-clean; ABI stays 3) + `laplacian.dense_matmul_complex` (native
  dispatch; no-native fallback composes `dense_matvec_complex` column-by-column —
  a cascade, never numpy `@`). Tool-schema `describe` **255 → 256**; Rosetta
  inventory **348 → 349** (`c_dispatched`). This rc ships + **proves** the kernel
  (parity + CI build); the `@`-callsite migrations against it (decrementing the
  ratchet's `matmul` 185) are the next batches.
- **rc16 (done) — matmul-kernel batch 1: `matrix_cascades` dense matmuls.** The 5
  dense complex 2-D matmuls inside `matrix_cascades.py` (`AᴴA`/`A·V`/`AAᴴ`/`Aᴴ·U`
  Gram + reconstruction products of `svd`; the `R·Q` shifted-QR step of `eigvals`
  that `qr`/`lstsq` ride) now route through `laplacian.dense_matmul_complex`
  instead of numpy `@`. **numpy-math ratchet `matmul` 185 → 180.** No Rosetta
  bucket move (`qr`/`svd`/`lstsq`/`eigvals` were already `composition_of_c` via the
  `hermitian_eigendecompose` Class-L cascade); pure Python-tier, ABI stays 3, the
  25 decomposition parity tests pass unchanged.
- **rc17 (done) — matmul-kernel batch 2: `qm.single_particle` contractions.** The
  12 dense complex contractions in `qm/single_particle.py` (`commutator` `AB−BA`;
  `heisenberg_evolve` `Uᴴ·A·U` + `liouville_evolve` `U·ρ·Uᴴ` with `U=V·diag·Vᴴ`;
  `tdse_evolve` eigenbasis change) route through `dense_matmul_complex` /
  `dense_matvec_complex`. **numpy-math ratchet `matmul` 180 → 168.** Module residual
  is only `np.outer` in `density_matrix` (rank-1, distinct op). No Rosetta move
  (already `composition_of_c` via `hermitian_eigendecompose`); ABI stays 3; the 27
  single_particle parity tests pass unchanged.
- **rc18 (done) — matmul-kernel batch 3: `qm.spin` + `qm.gauge`.** `qm.spin`'s 15
  Pauli products (Clifford anticommutator + cyclic commutator residuals) and
  `qm.gauge`'s 6 SU(N) Lie-algebra products (structure-constant commutator,
  quadratic Casimir `ΣTᵃTᵃ`, segment-holonomy `V·diag(eⁱᵠ)·Vᴴ`, Wilson-loop
  path-product) now route through `dense_matmul_complex`. **numpy-math ratchet
  `matmul` 168 → 147.** Both modules numpy-`@`-free; no Rosetta move; ABI 3; spin +
  gauge parity tests pass unchanged.
- **rc19 (done) — matmul-kernel batch 4: `qm.relativistic` + `qm.pseudo_hermitian`.**
  `qm.relativistic`'s 9 Dirac γ-matrix products (`γ_5=iγ0γ1γ2γ3`, Clifford
  `{γ^μ,γ^ν}`, `γ_5²`, `{γ_5,γ^μ}`, charge-conj `C=iγ2γ0`) + `qm.pseudo_hermitian`'s
  3 (`Oᴴη−ηO`, `η=(V·Vᴴ)⁻¹`) route through `dense_matmul_complex`. **numpy-math
  ratchet `matmul` 147 → 135.** ABI 3; parity tests unchanged. DEFERRED: the
  real-typed `eta@k` Minkowski matvec/dot + `vᴴηv` eta-sandwich vecmat-dot sites
  (need a real-matmul cascade + vecmat helper); `qm.triality` is entirely real-typed
  and awaits the same real-matmul variant.
- **rc20 (done) — matmul-kernel batch 5: complex vecmat/dot/sandwich → new
  `dense_dot_complex` bilinear helper.** The complex 2-D matmul surface was
  exhausted at rc19; rc20 adds `dense_dot_complex(a, b)` (plain bilinear
  `Σ aᵢbᵢ` = `elementwise_multiply_complex` ⊕ reduction; **`composition_of_c`**)
  and routes the genuinely-complex contraction sites onto `dense_matvec_complex`
  + `dense_dot_complex`: `qm.pseudo_hermitian`'s 3 η-sandwiches (7 `@`),
  `heat_kernel`'s 2 eigenbasis matvecs, `spectral`'s 2 decompose/recompose
  matvecs, `music`'s `Enᴴ·A` 2-D matmul. **numpy-math ratchet `matmul`
  135 → 123.** ABI 3; parity tests unchanged. DEFERRED: the real-typed
  so8/triality/octonion-DFT/Minkowski/DSP sites (real-matmul + real-matvec
  cascade) and the `matrix_cascades` QR-internal vdot/back-solves (shape-
  polymorphic pass).
- **rc21 (done) — matmul-kernel batch 6: real-linear-algebra cascade trio +
  `hypercomplex_dft`.** Introduces `dense_matmul_real` / `dense_matvec_real` /
  `dense_dot_real` (float64 peers riding the complex kernel on imag-free input,
  `.real`; **`composition_of_c`**) so the ~70 real-typed sites can leave numpy
  `@`/`.dot` without a dtype change. First use: `amsc.cascade.hypercomplex_dft`'s
  8 octonion-rep (8×8 real) matvecs in the QDFT/ODFT core + `hypercomplex_couple`
  → `dense_matvec_real` (lazy-imported, numpy-absent-safe §22; F378 bracketing
  preserved). **numpy-math ratchet `matmul` 123 → 115.** ABI 3; QDFT/ODFT +
  numpy-free tests unchanged. `dense_matmul_real`/`dense_dot_real` get first
  callsites in the next batches (so8 / triality).
- **rc22 (done) — matmul-kernel batch 7: `qm.triality` real products → real
  cascade.** First consumer of the rc21 real trio. `qm.triality`'s 7 real
  products — octonion-rep matvecs (`operator @ octonion_mul(…)`, `g_v/g_s/g_c @
  …`) onto `dense_matvec_real`; the 28×28 Spin(8) triality `tau = S_B·S_C` /
  `tau²` / `tau³` onto `dense_matmul_real` — plus 3 docstring `@`→`·` rewords.
  **numpy-math ratchet `matmul` 115 → 105.** ABI 3; triality parity unchanged
  (`tau³=I₂₈`, `Fix(tau)=g₂` dim 14). `qm.so8`'s ~17 real sites + Minkowski/DSP
  land next.
- **rc23 (done) — matmul-kernel batch 8: `qm.so8` real + complex.** The
  g₂/Spin(8) module's 17 contraction sites: 15 real (the `[X,Y]` commutator,
  su(3)/g₂ Gram products, basis-projection matvecs, structure-constant
  `pinv·bracket`, Gram-Schmidt dot) → `dense_matmul_real`/`matvec_real`/`dot_real`;
  2 COMPLEX (the su(3)-weight Rayleigh quotients `vᴴv` / `vᴴ·ad·v`, where `v` is a
  complex eigenvector of the real ad(H)) → `dense_dot_complex`/`dense_matvec_complex`.
  **numpy-math ratchet `matmul` 105 → 86.** ABI 3; so8 parity unchanged (g₂ dim 14,
  14 = 8+3+3̄ su(3) branching, su(3) weights). The 2 `np.kron` stay (distinct op).
- **rc24 (done) — matmul-kernel batch 9: the real "Minkowski + real-dot" sweep.**
  Eleven real-typed sites across `qm` + `amsc`: `qm.relativistic` (3 — `η k`
  lowering matvec, the K-G `⟨k,k⟩` dispersion dot, the `kᵀηk` bilinear),
  `qm.propagators` (1 — gauge-term `η k` matvec), `amsc.harmonics` (3 — the
  `_spectral_scores` energy/mirror/three-cycle ⟨x,·⟩ probes), `amsc.hdc` (3 — the
  Moufang norm² gates in `loop_inv`/`loop_inv_hd` + the `g2_three_form` associator
  ⟨x,y×z⟩) → `dense_matvec_real`/`dense_dot_real`. The `amsc` sites import the
  helper **function-locally** so `harmonics`/`hdc` stay numpy-absent-safe (§22).
  **numpy-math ratchet `matmul` 86 → 75.** ABI 3; values bit-preserved; the qm +
  hdc-loop + harmonic suites pass unchanged. The `np.outer` k^μk^ν sites stay
  (distinct op). DSP `closed_form_ops` + `matrix_cascades` QR-internals next.
- **rc25 (done) — matmul-kernel batch 10: the real DSP `closed_form_ops`
  cluster.** Fifteen sites: `dct` (2 — DCT-matrix `arr·Mᵀ`/`M·arr`), `map_ml`
  (6 — the `AᵀR⁻¹A` normal-equation matmuls + matvecs; `np.linalg.inv/solve`
  stay), `ica_jade` (6 — `XᵀX` covariance + whitening + Givens `V·G` rotations;
  2 `np.einsum` + `eigh` stay) → `dense_matmul_real`/`dense_matvec_real`; plus
  `fsk` (1 — the complex `tones·conj(window)` correlator bank) →
  `dense_matvec_complex`. Top-level helper import (these DSP modules hard-import
  numpy, unlike the lazy-numpy amsc modules). **numpy-math ratchet `matmul`
  75 → 60.** ABI 3; dct/map_ml/ica_jade/fsk suites unchanged. `np.convolve`/
  `correlate`/`outer`/`einsum` stay (distinct ops).
- **rc26 (done) — matmul-kernel batch 11: the genuine-code tail.** Five remaining
  genuine dense-matmul *code* sites: `vector_quantisation` (real `vec·cbᵀ`),
  `sinc_interp` (COMPLEX `K·y` — `y` is complex128 IQ → `dense_matvec_complex`),
  `farrow` (real Lagrange `C[k]·x` dot), `qm.potentials` (complex `a†·a` number
  op), `qm.sm` (complex `V·Vᴴ` CKM-unitarity) → `dense_matmul_real`/`dense_dot_real`/
  `dense_matvec_complex`/`dense_matmul_complex`. **numpy-math ratchet `matmul`
  60 → 55.** ABI 3. This reaches the **dense-matmul-migration floor**: of the
  remaining ~55, ~16 are docstring/comment/summary-string `@` *mentions* (cosmetic
  `·` reword) and ~25 are distinct ops needing own cascades (convolve / correlate /
  kron / outer / einsum). The `laplacian` Schur `L_pi·X` is deferred (in-helper,
  shape-polymorphic). Further matmul reduction = reword sweep + distinct-op
  cascades (separate work items), not more dense-matmul routing.
- **rc27 (done) — linalg/fft phase opens: the linear-solve family.** Dense-matmul
  floored, the arc pivots to `linalg_fft` (pinned at 126 since rc13). Per user
  direction (cascade + TOML for ALL maths; numpy carrier-only, carrier removed as
  the FINAL step), the cascades replace numpy math even where round-off-faithful
  not bit-exact (fft/svd/qr/eig ~1e-14; within-tolerance shift accepted). rc27:
  `map_ml`'s 2 `np.linalg.solve` → `dense_solve` (bit-exact, 1-D RHS); `triality`
  + `esprit`'s `np.linalg.lstsq` → `matrix_cascades.lstsq` (round-off, complex-safe;
  bare-ndarray return replaces numpy's 4-tuple → callsite unpack changed).
  **numpy-math ratchet `linalg_fft` 126 → 122.** ABI 3. NOT migrated: the cascade
  ops' OWN internal numpy kernels (laplacian eigh/solve — Class-L impls w/
  pure-Python fallbacks; deeper pass) + docstring/summary `numpy.linalg.*` MENTIONS
  (precise docs, not gamed). Next: np.fft (n/axis) + svd/qr/eigvals + inv/pinv.
- **rc28 (done) — the first exact-until-rotation cascade: DFT/FFT goes integer.**
  Per the sharpened user direction (*"don't use floats for bit-exact math, that's
  what ints and complex are for; floats are for FPU lift"*), the `dft`/`fft`
  cascade now routes an all-integer / Gaussian-integer **power-of-two** signal
  through an exact cyclotomic-integer engine — `ℤ[ζ_N]`, `ζ^{N/2} = -1` (a Class-K
  sign-flip) collapsing to the negacyclic integers `ℤ[x]/(x^{N/2}+1)` → **pure
  integer add/subtract**, with ONE FPU lift at the end (`ζ → e^{-2πi/N}`). This is
  *more* faithful than a float FFT (which rounds every butterfly) and sharpens
  rc27's "round-off-faithful is fine" framing for the integer case. **No ratchet
  movement, no Rosetta-bucket change**: the engine is a private module
  (`srmech.amsc.cascade.exact_dft._exact_transform` + helpers), adds no numpy and
  no public introspected callable, so all three numpy-math ceilings AND the
  `python_only_irreducible` debt count are untouched. ABI 3.
  **Follow-up C-twin candidate:** exposing the exact `ℤ[ζ_N]` spectrum as a
  *public* op (`exact_dft` / `exact_idft` / `lift`) should land **with** its
  native-C peer so it classifies `c_dispatched`, not Python-only debt — the
  ratchet's exact-equality `python_only_irreducible` ceiling is precisely what
  blocks adding it Python-only. General-`N` (non-power-of-two) cyclotomic
  reduction is also a follow-up.
- **Next batches — migrate `@`-callsites onto `dense_matmul_complex`.** The 108
  `python_only_irreducible` ARE the numpy-math ratchet's 359 callsites seen at the
  op level; the QM / `matrix_cascades` `@` matmuls now have their kernel. Each
  migration decrements BOTH the ratchet's `matmul` ceiling AND moves a Rosetta op
  `python_only_irreducible → composition_of_c`. After `matmul`: FFT/DFT,
  `eig`/`SVD`/`QR`/`lstsq`, `kron`, `einsum`. The 5 remaining `c_exists_unbound`
  stay the **Klein-4 family, gated on W5**.

**Standing tracker.** Issue [#928](https://github.com/lemonforest/mlehaptics/issues/928)
is the consolidated srmech wishlist (bugs · schema · enhancements · new ops,
W1–W18). Consult it at every rc boundary: (1) the do-not-mirror gate above
before any Python→C port, and (2) the stale-vs-missed sweep per
`[[feedback_tracker_lookback_stale_vs_missed_each_sprint]]`.
