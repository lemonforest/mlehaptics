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
- **rc29 (done) — the exact ℤ[ζ_N] spectrum goes public + gets its C twin.**
  `exact_dft` / `exact_idft` / `lift` are promoted to introspected ops, and the
  native-C twin **`srmech_exact_dft_i64`** (`srmech_exact_dft.c`, JPL-clean,
  caller-buffer int64) ships the integer add/subtract fast path. The Python op
  dispatches to C when `N·max|signal|` is int64-safe, else the arbitrary-precision
  bignum path. Rosetta: `exact_dft` / `exact_idft` → **`c_dispatched`** (they
  HAVE the C twin), `lift` → **`composition_of_c`** (over the Class-N `cexp`) —
  the honest "land WITH the C twin so it's not Python-only debt" the rc28 note
  flagged. 3 ToolEntries (introspect 260 → 263), 3 rosetta lines, a
  `list[tuple[list[int],list[int]]]` MCP coercer. ABI 3 (additive). Next:
  general-`N` cyclotomic (Python-only `bignum_reference`).
- **rc30 (done) — the exact DFT goes general-`N` (any length, not just pow2).**
  A pure-integer cyclotomic engine (compute `Φ_N` from `x^N-1 = Π_{d|N} Φ_d`;
  reduce each `ζ^j` to the length-`φ(N)` power basis, cached per `N`) extends
  `exact_dft`/`exact_idft` to **any** `N ≥ 2`; `lift` infers the basis degree
  from the spectrum; `dft`/`fft` route all integer signals exact (pow2 keeps the
  negacyclic / native-C route, general uses the bignum cyclotomic path). **No new
  public surface, no ratchet movement** — the general path is Python-only
  (`bignum_reference` shape; the op stays `c_dispatched` for its pow2 C fast
  path), numpy-free, ABI 3. The rc28/rc29 non-pow2 "not-supported" tests update
  to the general-`N` contract. Perf: the general path is `O(N²·φ(N))` integer —
  exactness costs the `φ(N)` factor.
- **rc31 (done) — exact-until-rotation EIGENVALUES; the ill-conditioned problem
  HAS a cascade form.** Per user insight: the Wilkinson ill-conditioning of float
  root-finding from char-poly coefficients is a float-perturbation artifact, NOT
  inherent — integer-matrix eigenvalues are ALGEBRAIC and come out well-conditioned
  if kept in exact arithmetic. Two new public ops: **`char_poly`** (exact integer
  characteristic polynomial via Faddeev–Leverrier — exact trace/det/symmetric
  functions; Class L∘M∘K) and **`eigvals_exact`** (exact real eigenvalues with
  multiplicity: char_poly → Yun square-free → **Sturm** sign-sequence isolation
  (Class C sign-count @ Class K interval boundaries) → rational **bisection**
  (Class N anchors → the algebraic asymptote), exact `Fraction` throughout, one
  FPU lift). Proven: Wilkinson `diag(1..10)` exact (err 0.0) vs float `np.roots`
  9-digit loss; irrational golden-ratio exact to 15 digits; singular values via the
  exact integer Gram `AᵀA` match numpy ~1e-9 (the svd exact substrate too). Both
  `bignum_reference` (non-debt; `Fraction`/bignum, numpy is a container). 2
  ToolEntries (introspect 263 → 265), 2 rosetta lines, ABI 3, ratchet untouched.
  Follow-up: complex-eigenvalue exact isolation. NEXT-ARC SEED (user-requested):
  an **A-N-cascade sweep/ratchet** — a down-only guard flagging math not yet
  reduced to the 14 A-N class cascades (the `math.*`/`cmath.*` float-transcendental
  residue beyond the numpy-math ratchet).
- **rc32 (done) — the A-N-cascade ratchet itself (the rc31 NEXT-ARC SEED).**
  `tests/test_an_cascade_ratchet.py` — the bare-Python-tier sibling of the
  C-transpile libm ratchet (23 → 0) and the numpy-math ratchet. **AST-based, not
  regex** (the source carries ~39 *descriptive* docstring mentions of `math.cos`
  etc. that a text grep would miscount as debt; the AST sees only genuine
  `Call`/`Attribute`/`BinOp` nodes — the same basis as the no-abs scanner). Three
  tight down-only categories pinned at the measured baseline: `transcendental` = 1
  (the lone `cmath.sqrt` Wilkinson-shift discriminant in the FLOAT `eigvals`
  complex-spectrum path — eliminated when complex-eigenvalue exact isolation lands,
  the rc31 follow-up), `math_const` = 0 (the π-cascade discipline fully holds — zero
  float `math.pi` in any compute path), `float_pow` = 0. Excluded + documented:
  integer primitives (`isqrt`/`gcd`/`factorial`/…), IEEE/sign primitives
  (`copysign`/`fabs`/`isfinite`/… — Class-K sign family; `copysign` at an IEEE ±0
  limit is the correct idiom), and the inherently-invisible string mentions. No
  module carve-out — a stray `math.sin` anywhere fails. Test-only; no public
  surface, no ToolEntry, no introspect change, ABI 3.
- **rc33 (done) — A-N ratchet CLOSED to zero.** The one rc32 `transcendental`
  site (the `cmath.sqrt` Wilkinson-shift discriminant in the float `eigvals`
  complex-spectrum path) routed through `matrix_cascades._complex_sqrt` — the
  principal complex root rebuilt from the Class-N `hypot`/`sqrt` real cascades + a
  Class-K sign-branch (principal branch `Re ≥ 0`) + a Class-K pin-slot-at-zero
  floor on each radicand (the `_norm2` idiom; tiny `<0` round-off → 0). No libm
  `cmath` (the import is removed); matches `cmath.sqrt` ~1e-13. `CEIL_TRANSCENDENTAL`
  1 → 0 — all three A-N categories now ZERO. The bare-Python tier joins the C tier
  (libm 23 → 0) at zero continuous-math residue: every continuous-math op across C,
  numpy-tier, and bare-Python is a cascade of the 14, floats only at the FPU lift.
  Test-only ceiling drop + one helper; ABI 3.
- **rc34 (done) — matmul decrement by ROUTING np.kron + np.einsum onto existing
  cascades** (no new public op — pure routing). `qm.so8`'s `ad⊗I − I⊗ad` su(3)
  superoperator (×2) + `qm.bell`'s `_kron` (×1) → `spectral_cascades.kron`
  (`np.asarray` carrier-only); `qm.triality`'s octonion-couple `np.einsum`
  (×1) → `matrix_cascades.einsum`. Value-faithful (so8/triality bit-exact 0.0;
  bell bit-exact on its Pauli operators). `CEIL_MATMUL` 55 → 51. Deferred:
  `ica_jade` 2 einsum (hot Jacobi loop), the np.outer family (needs a
  `dense_outer` cascade), the QR-internal vdot/outer/@ (shape-polymorphic pass).
  Watch the regex ratchet: an `np.kron`/`np.einsum` MENTION in a NEW code comment
  re-adds the token — write "the NumPy Kronecker product" / "the NumPy einsum"
  (no `np.`/`numpy.` prefix) in routing comments.
- **rc35 (done) — numpy-free native dispatch for `jacobi_eigvals` (UPSTREAM §38 /
  F708; ~49×).** The bound `srmech_jacobi_eigvals` C symbol is now reachable
  WITHOUT numpy: `_jacobi_eigvals_native_listmarshal` builds a flat
  `(c_double * n·n)` ctypes buffer from the `list[list[float]]` and calls the C
  symbol; the numpy-absent branch dispatches to it when `HAS_NATIVE` + `n ≤ 256`,
  else the pure-Python Jacobi cascade. Fixes the rc28 finding (numpy-free Class-L
  store ~68 s @ n=256 → ~1.4 s native). PHASE B of the numpy-carrier-removal
  north-star — the C foundation must be numpy-free-reachable before numpy can
  leave as a carrier. §38 "bind the symbols" was already done (HEAD binds
  jacobi/laplacian/hermitian/hdc/klein4); bytes-hdc already numpy-free;
  symmetric eigvec-decompose stays numpy.linalg.eigh (deliberate); klein4→C
  deferred behind W5. ABI 3; no public-surface change.
- **rc36 (done) — Laplacian tidy: numpy-free native dispatch for the Class-L
  BUILD ops + header-comment accuracy (UPSTREAM §38, completing rc35).**
  `dense_adjacency` / `dense_laplacian` / `normalized_laplacian` reach the bound
  `srmech_graph_*` C symbol on the numpy-absent install too, via
  `_build_matrix_native_listmarshal` (Python list → flat ctypes uint32/double
  buffers → reshape); fall back to the pure-Python builder only when no native
  lib / n>256 / non-OK. (O(edges)-cheap — consistency, not the perf eig.) Fixed
  the stale "wrappers fall back to numpy unconditionally" module-header note
  (eigvals dispatch numpy-free now; only the eigenVECTOR decompose stays the
  LAPACK `eigh` path, by design). PHASE B of the carrier-removal north-star.
  #962 reconciliation: the binding ask was already done at HEAD; klein4→C stays
  behind W5 (even-count now documented: strict majority, tie→0); the Klein-4
  spectral quad-stream is sequenced into the Part-2 genome-storage surface (its
  quad-turn unit). Watch the regex ratchet: a `numpy.linalg.eigh` MENTION in a
  new comment counts — write "the LAPACK `eigh` path" (no `numpy.linalg.`).
- **rc37 (done) — genome-storage surface, brick 1 (#962 Part 2; F711–F715).**
  New module `srmech.amsc.genome` (biological-structure names as cascade names):
  `encode_shape(n)` — the encode CRITERION (tome ≤256 / mobius ≤1024 / quad_strand
  >1024; `depth = ceil(log4(ceil(n/256)))` in pure integer arithmetic, no float
  log) → bucket `non_compute`; `quad_turn(turn, the_one)` — the reversible Klein-4
  the_one coupling (F713; `quad_turn∘quad_turn == id`), a pure delegation to
  `hdc.klein4_bind` → bucket `composition_of_c`. NB the delegate `klein4_bind` is
  still `c_exists_unbound` (W5-gated); `quad_turn` adds no new debt and inherits
  the eventual dispatch. 2 ToolEntries (category `genome`), tools.total 265→267,
  `np.ndarray` param-type (matches the Klein-4 family + has an MCP coercer — `HV`
  has none). No C twin yet (the quad-turn is pure-Python reversible XOR); the
  chromosome (telomere-capped strand) + genome (multi-kernel) assemble next.
- **rc38 (done) — genome-storage surface, brick 2: the chromosome (#962 Part 2).**
  `srmech.amsc.genome` gains the LAYER-1 cascade primitives: `telomere(label,
  dim)` — the non-data content-address cap (sha256_bytes → seed → Klein-4
  sentinel; Class A ∘ M) → `composition_of_c`; `chromosome(leaves, the_one,
  label=)` — pack a kernel into a telomere-capped strand of quad-turns →
  `composition_of_c`; `recall(strand, the_one, telomere)` — the exact inverse
  (cap matched by VALUE so it generalises to a multi-chromosome genome) →
  `composition_of_c`. 3 ToolEntries (category `genome`), tools.total 267→270.
  These are the ops the upcoming USER-AUTHORED class layer binds to (declarative
  `[class]` TOML → generic class-aware object via the config-driven loader; DSL /
  CLI / tool_schema lifted class-aware from the `register_catalog_dir` op-pattern;
  genome = seed worked-instance). No C twin (pure-Python reversible XOR + content
  address). klein4_bind stays `c_exists_unbound` (W5).
- **rc39 (done) — user-declared classes from `[class]` TOML (#962 Part 2).** The
  cascade-catalog config-driven pattern lifted from ops to CLASSES:
  `srmech.dsl.make_class(name)` + the generic `CatalogClass` construct a
  class-aware object from a `[class]` descriptor (fields + methods-as-cascade-
  op-refs; methods dispatch to a shipped op by dotted srmech path) — zero user
  Python. `register_class_dir` / `SRMECH_CLASS_PATH` is the bring-your-own
  surface (B-tier, no-shadow), mirroring `register_catalog_dir`. genome ships as
  the built-in seed (`_research/class_catalog/genome.toml`): `Genome` with
  `shape`/`cap`/`add_chromosome`/`recall` binding the rc37/rc38 genome ops. The
  loader lives in `srmech.dsl` (NOT `srmech.amsc`/`qm`) so it adds no tool-schema
  / rosetta entry — pure orchestration over already-classified ops. No C twin
  (config + dispatch). DSL stage / CLI / tool_schema class-awareness are rc40/rc41.
- **rc40 (done) — DSL class-awareness (#962 Part 2).** `srmech.dsl` gains the
  one-shot surface over the rc39 `CatalogClass`: `describe_class(name)` /
  `list_class_surface()` (JSON-able introspection — fields + methods + binds +
  provenance) and `run_class_method(class_name, method, fields=, args=)` (the
  stateless construct-invoke-return: `{class, method, result, fields}` with the
  post-call state, so an `appends`/`sets` mutation is visible). `fields`/`args`
  are plain dicts (MCP-grammar friendly). Lives in `srmech.dsl` (NOT amsc/qm) →
  no tool-schema / rosetta entry. CLI subcommands + tool_schema/MCP class
  registration are rc41.
- **rc41 (done) — CLI + tool_schema/introspect class-awareness; the genome
  surface closes (#962 Part 2).** `srmech class list` / `srmech class describe
  NAME` (`srmech.cli.klass`; CLI token `class`, module `klass` since `class` is
  a keyword); `introspect.describe()["classes"] = {total, names}` (the package
  recognises its own user-class surface — sibling key, `tools.total`
  unaffected); 2 ToolEntries `srmech.dsl.list_class_surface` / `describe_class`
  so the LLM tool list includes class discovery (`tools.total` 270→272; 5
  count-tests bumped). dsl ToolEntries take no rosetta line (rosetta walks
  amsc/qm live ops). Completes rc37/rc38 (genome primitives) → rc39 (`[class]`
  loader) → rc40 (DSL surface) → rc41 (CLI + tool_schema): a researcher reaches
  a TOML-declared class from Python, the shell, and an LLM. NB the local-only
  `test_introspection_version_native_matches` false-fail is the stale hand-built
  DLL (version string vs a fresh CI build), not a regression.
- **rc42 (done) — genome-storage brick 3: multi-kernel `genome` + `partition`
  (#962 Part 2).** `srmech.amsc.genome.genome(kernels, the_one)` packs many
  `{label: leaves}` kernels into ONE telomere-partitioned strand (each a
  telomere-capped `chromosome` coupled through `the_one`, concatenated); the
  inverse `partition(strand, the_one, labels)` knows ALL caps so it never
  mistakes one chromosome's cap for another's data — round-trips every kernel
  exactly. The seed `Genome` `[class]` gains `assemble`/`partition` methods.
  Closes the F715 hierarchy GENOME→CHROMOSOMES→QUAD-TURNS→LEAF≤256. 2
  ToolEntries (`genome` / `partition`; `tools.total` 272→274; 5 count-tests
  bumped); both **`composition_of_c`** (compose of `chromosome`/`recall` over the
  c_dispatched `klein4_bind`, with a content-address cap from `sha256_bytes`) —
  no debt-bucket growth. ABI 3; numpy not required.
- **rc43 (done) — text→graph stage primitives (RBS-LM UPSTREAM §17 U1; #855
  R3 U1).** `srmech.amsc.laplacian.tokenize(text, *, stopwords=, min_len=,
  pattern=)` (Class B/G text-segmentation) + `cooccurrence_edges(tokens, *,
  window=, vocab_size=) -> (n, edges, weights)` (Class-L precursor) — the only
  links between raw text and the already-shipped `dense_laplacian`. The K1
  presence-kernel is now an authorable composite end-to-end (`tokenize →
  cooccurrence_edges → dense_laplacian → eigendecompose → …`), retiring the
  hand-rolled `re.findall` + `Counter()` idiom. Both pure-Python / numpy-free;
  2 ToolEntries (`tools.total` 274→276; 5 count-tests bumped); both
  **`non_compute`** in the ledger (string segmentation + integer graph
  construction — no numeric/matrix compute, no c-dispatch → no debt-bucket
  growth). The directed sibling (`i(A−Aᵀ)` Hermitian-Laplacian builder, reusing
  the shipped `hermitian_eigendecompose`) is a separate queued Class-L
  precursor (UPSTREAM §18.1 op(b) reference F357). ABI 3; numpy not required.
- **rc44 (done) — DSL dotted-`op=` resolver + §17 U2 (`encode_loe_content`
  registered as a cascade-op).** `lookup_cascade_op` honours a dotted
  `[cascade].op` entry point (mirrors the rc39 class-catalog), so the verified
  `srmech.signal_processing.encode_loe_content` text→instrument encoder is a
  one-line DSL stage — any catalog's text rows get a one-line kernel chain.
  `list_cascade_ops` 14→15; no new `srmech.amsc.*` callable (the op already
  ships + keeps its `composition_of_c` rosetta line), so the rosetta ledger +
  `tools.total` are unchanged. ABI 3.
- **rc45 (done) — `srmech.dsl.list_ops` unified op-discovery (RBS-LM §17 U3).**
  Merges the two previously-disjoint discovery registries — `list_catalog_ops`
  (value-transform cascade ops) + `catalog.list_catalog_chains` (AMSC
  catalog-declared chains) — into ONE call with a uniform
  `{name,class,purpose,kind,provenance}` record (`kind` adds `catalog-chain`;
  `provenance` adds `catalog:<source_key>`). New `srmech.dsl.list_ops` ToolEntry
  (a DSL discovery callable — no rosetta line, per the dsl-ToolEntry convention),
  so `tools.total` 276→277 but the Rosetta op ledger is unchanged. ABI 3;
  numpy-free.
- **rc46 (done) — catalog→DSL auto-registration bridge actually routes (RBS-LM §17 U4).**
  rc45's `list_ops()` auto-discovery read the wrong source-key field
  (`source_key`/`name`) where `list_attested_sources()` returns each source under
  `key`, so the catalog-chain half was silently empty. rc46 reads `key` (with the
  alternates as fallbacks) → the 7 packaged catalog-chains (asymptotic_calculus ×5
  + cosmos_validation + pi_digits) now surface tagged `catalog:<source_key>`, and a
  freshly `register_attested_root`-ed catalog's declared chains too. Pure
  registry-read fix; no new callable, `tools.total` stays 277, Rosetta op ledger
  unchanged. ABI 3; numpy-free.
- **rc47 (done) — `hdc.klein4_project_axis`: iω₇-collapse / bipolar projection
  (RBS-LM §18 Tier-2 leaf; F350/F354).** Projects a 2-DoF Klein-4 store onto one
  chirality axis → bipolar `{-1,+1}` (the asymptotic-DoF render; drops the other
  axis + its self-EC per F354 axis-split). `axis` co-equal (`gamma5` bit 1 /
  `iomega7` bit 0; settable-chirality discipline). Class K (sign render) ∘ Class
  C (axis select); numpy-free; no `abs()`. New ToolEntry → `tools.total` 277→278.
  Rosetta bucket **`non_compute`** (a one-way bipolar render/readout OUT of the
  store — peer to the rc43 tokenize/cooccurrence_edges projections, NOT a
  reversible store-transform like the klein4 flips, whose standalone-C twin stays
  W5-gated per the do-not-mirror rule). ABI 3.
- **rc48 (done) — `laplacian.spectral_block_dispatch`: the 1024-node 4-sector
  spectral one-call (RBS-LM Ask-3; F233 4-rung).** Eigendecomposes ≤4 dense
  symmetric blocks (each n ≤ 256) on a 4-worker thread pool — the threaded-
  Klein-4-streams pattern (the same 4-way fan-out as
  `cascade.parallel_sector_dispatch`, but over DISTINCT blocks). 4 × 256 = 1024
  nodes within the native dense-eig bound; 0 cross-thread reads → parallel ==
  serial bit-for-bit. New ToolEntry → `tools.total` 278→279. Rosetta bucket
  **`composition_of_c`** (composes the `c_dispatched` `jacobi_eigvals` + a
  merge-sort reduction). Class L over the 4-rung; numpy-free. ABI 3.
- **rc49 (done) — `dsl.generate_class_descriptor`: the make_class inverse
  (RBS-LM §39).** Renders a `[class]` TOML descriptor from components (or by
  introspecting a registered class via `describe_class`) round-trippable straight
  back through `make_class` — closing the class-from-TOML loop the other
  direction. New ToolEntry → `tools.total` 279→280. A `srmech.dsl.*`
  discovery/render callable: it bumps the tool count but is **NOT** in
  `rosetta_classification.ndjson` (the rosetta surface is the `srmech.amsc.*`
  compute ops; the dsl render/introspect callables — `list_ops`,
  `describe_class`, now `generate_class_descriptor` — are out of that scope, same
  as their peers). Class E ∘ F ∘ H; numpy-free; no C twin (pure descriptor
  render). ABI 3.
- **rc50 (done) — `amsc.text.{tokenize, cooccurrence_edges}`: the §40 R3-U1
  acceptance fix (was SHIPPED-but-FAILING 3/3; F722).** The rc43 text→graph
  leaves shipped in `laplacian` but failed §40 on Unicode (ASCII `\w+` truncated
  café→caf, dropped Cyrillic/CJK) / silent `vocab_size=1000` cap (the F708
  pre-encode quantization bug as a default) / no document-boundary window reset.
  rc50 **relocates** them to a dedicated ingestion module `srmech.amsc.text`
  (laplacian stays purely spectral) and fixes all three: Unicode-aware
  (`unicodedata` L/M + casefold), full vocab by default (cap = explicit logged
  opt-in), `docs: Sequence[Sequence[str]]` so the window resets per document.
  The two `ToolEntry`s move `laplacian.* → text.*` and the two rosetta lines
  re-point (`non_compute` bucket unchanged); `tools.total` stays 280 (relocation,
  not a new op). Class B/G ∘ Class-L precursor; numpy-free; no C twin. ABI 3.
- **rc51 (done) — `laplacian.dense_outer_{complex,real}`: the np.outer → cascade
  decrement (numpy-removal PHASE A).** An outer product is the k=1 case of a
  matrix product, so `dense_outer_complex` = `dense_matmul_complex` on the
  reshaped (column, row) pair — rides the native kernel, single-multiply per
  entry, **bit-identical to numpy**. Routes the 3 genuine np.outer sites
  (qm.propagators' two real kᵘkᵛ momentum tensors → dense_outer_real,
  qm.single_particle's complex |ψ⟩⟨ψ| density matrix → dense_outer_complex) off
  numpy's contraction engine — the numpy-math ratchet's `matmul` ceiling 51→48.
  2 new ToolEntries → `tools.total` 280→**282**; both `composition_of_c` (no own
  C symbol; compose the c_dispatched dense-matmul kernel). The 2 remaining
  np.outer are the matrix_cascades QR-internal Householder updates (shape-
  polymorphic pass). Class L rank-1 contraction; numpy carriers-only. ABI 3.
- **rc52 (done) — `laplacian.elementwise_hypot`: the np.hypot |z| magnitude
  cascade OPENS the ufunc bucket (numpy-removal).** With the np.outer contraction
  surface handed off (rc51), the sweep turns to the **ufunc** ceiling (pinned at
  48 since rc13) — numpy's transcendental / magnitude engine. `np.hypot(z.real,
  z.imag)` = `|z| = √(re²+im²)`, a per-element libm `hypot`; `elementwise_hypot(a,
  b)` loops the **Class-N `rational.hypot` cascade** (isqrt-based, native
  `srmech_rational_sqrt`-dispatched, no libm) over the flattened pair, numpy
  carrying the array only. Routes all **5 DSP magnitude sites** (fsk / mlse /
  psk_qam nearest-symbol distances, ofdm channel-mag, spectral coeff-mag) off
  `np.hypot` — the numpy-math ratchet's `ufunc` ceiling **48 → 43**. Round-off-
  faithful (rational sqrt floor-projected vs IEEE round-to-nearest, ≤1-ULP; never
  flips a nearest-symbol / argmax decision) + **bit-exact** on perfect squares
  (Pythagorean-triple constellation points decode exactly). 1 new ToolEntry →
  `tools.total` 282→**283**; `composition_of_c` (no own C symbol; composes the
  c_dispatched `rational.hypot`/`srmech_rational_sqrt`). Class N magnitude over a
  Class-L array surface; numpy carriers-only. ABI 3. Next ufunc batches: the
  np.exp complex-phase sites onto `elementwise_transcendental`, then np.sqrt /
  np.sin / np.cos / np.log / np.sign.
- **rc53 (done) — the `np.exp` batch: 14 callsites routed off numpy's exponential
  ufunc (the rc52 ufunc decrement continues).** `np.exp(1j·x)` = the phase
  `e^{iθ}`; routing onto `elementwise_transcendental(·, "exp_i")` runs the real
  cos/sin through the native libm-free C cascade and assembles the complex result
  (numpy carries the array only). Array phases (9): qm.gauge `diag(e^{iλ})`,
  qm.single_particle TDSE/Heisenberg/Liouville `e^{−iλt}` (×3), fsk tone bank
  (×2), psk_qam constellation, spectral_subtraction phase re-attach, spectral
  phase-extrapolate, laplacian magnetic directed-phase. Real exp (2): heat_kernel
  decay, rbs_lm softmax → `(·, "exp")`. Scalar `e^{iδ}` (2): qm.sm CKM CP phase →
  `rational.cexp` (Euler). **numpy-math ratchet `ufunc` 43 → 27** + 2 doc/summary
  `np.exp(` mentions de-parened. Pure routing — no new op, `tools.total` stays
  283, no rosetta/ToolEntry change. The 2 remaining np.exp are
  `elementwise_transcendental`'s OWN complex-input + real no-native fallbacks
  (documented internal kernel; deferred). Round-off-faithful (~1 ULP; QM + DSP
  suites pass unchanged). ABI 3. Next: np.sqrt (12), then sin/cos/log/sign.
- **rc54 (done) — `laplacian.elementwise_sqrt`: the `np.sqrt` batch (ufunc
  decrement continues rc52 hypot → rc53 exp).** New public `elementwise_sqrt(arr)`
  computes `√arrᵢ` per element via the Class-N `rational.sqrt` cascade (isqrt-
  based, native `srmech_rational_sqrt`-dispatched, no libm) — companion to
  `elementwise_hypot`, numpy carries the array only. Routes the 2 array np.sqrt
  (spectral_subtraction PSD `√(new_psd)`, ica_jade whitening `1/√(eigvals)`) onto
  it, and the 10 SCALAR np.sqrt (qm.gauge Gell-Mann `1/√3` ×3, qm.potentials `√n`
  ladder, qm.relativistic Klein-Gordon on-shell energy, qm.so8 ×2, qm.triality,
  psk_qam `√M`, wavelet `1/√2`) onto `rational.sqrt` (7 modules gain a
  `rational as _srn` import). **numpy-math ratchet `ufunc` 27 → 15.** Round-off-
  faithful (≤1-ULP; bit-exact on perfect squares; QM ladder/dispersion + DSP
  whitening/decode pass unchanged). 1 new ToolEntry → `tools.total` 283 → **284**;
  `composition_of_c` rosetta (composes the c_dispatched `rational.sqrt`; no own C
  symbol). Class N √ over a Class-L array surface; numpy carriers-only. ABI 3.
  Next ufunc: np.sin (3) + np.cos (3) → `elementwise_transcendental`, np.log (5),
  np.sign (2); then the 2 internal exp fallbacks (deferred cascade kernel).
- **rc55 (done) — the `np.log` + `np.sign` external residue (ufunc decrement
  closeout; rc52 hypot → rc53 exp → rc54 sqrt → rc55 log/sign).** Pure routing,
  no new op. 2 scalar `np.log` (mlse uniform-prior A_log `−log(A)` / pi_log
  `−log(n_states)`) → `rational.log` (Class-N, no libm). 1 array `np.sign`
  (hdc.polar_bundle's Pyodide fallback — the C peer `srmech_polar_bundle` owns
  the native path) → Class-K comparison sign `(total>0)−(total<0)` (carrier
  comparisons, the pin-slot at zero: + / 0 / − sector; no `np.sign` ufunc, no
  abs(), bit-identical to np.sign for the real int sum). Plus 2 comment mentions
  de-parened. **numpy-math ratchet `ufunc` 15 → 10.** The remaining 10 are ALL
  `elementwise_transcendental`'s OWN internal numpy fallback (2 exp + 3 sin + 3
  cos + 2 log — the complex-input path + the no-native real path); zeroing those
  is the deferred cascade-kernel work (complex-input trig/exp/log cascades),
  tracked separately. `tools.total` stays 284; no rosetta/ToolEntry change. ABI 3.
  The external ufunc surface (hypot/exp/sqrt/log/sign) is now CLEAR — only the
  cascade's own fallback kernel + the `linalg_fft` (122) ledger remain before
  the carrier-removal North Star.
- **rc56 (done) — `elementwise_transcendental` numpy-free: the ufunc bucket
  CLOSES to ZERO.** The last 10 ufunc sites were `elementwise_transcendental`'s
  OWN internal numpy fallback (complex-input path + no-native real path). rc56
  makes both numpy-free: `_real_transcendental_loop` loops `rational.{exp,cos,
  sin,log}` (Class-N scalar cascades, bit-exact vs numpy; log domain guard kept);
  `_complex_transcendental_loop` runs `rational.complex_exp` (exp) / cosh-sinh-
  from-`rational.exp` (cos/sin) / `rational.log(hypot)+i·atan2` (log) per element
  (principal branch, rejects z=0). **numpy-math ratchet `ufunc` 10 → 0.** Across
  rc52–rc56 the ufunc bucket went **48 → 0** — every transcendental / magnitude /
  sign op (hypot/exp/sqrt/log/sin/cos/sign) now runs a libm-free srmech cascade,
  numpy only ever packing the array. `tools.total` stays 284 (numpy-free kernels,
  no new public op). ABI 3. The two remaining numpy-math ledgers are `matmul`
  (48) and `linalg_fft` (122 — np.linalg.* / np.fft.*); after those, the carrier-
  removal North Star (#564).
- **rc57 (done) — the matmul-ledger REWORD SWEEP (docs only, zero behaviour
  change).** ufunc bucket closed (rc52–rc56); turning to `matmul`, ~30 of its 48
  matches were TEXTUAL ` @ ` / np.{vdot,einsum,convolve,correlate,kron} mentions
  in docstrings / comments / ToolEntry summaries (+ a `profile_loader`
  `entry-point[…] @ …` f-string false positive) — not compute. rc57 strips them
  all (NumPy op name / `·` without the dotted-paren form, per the rc34
  convention). **numpy-math ratchet `matmul` 48 → 18.** The remaining 18 are
  genuine deferred compute: matrix_cascades QR-internals (vdot/outer/@/back-solve
  — shape-polymorphic pass), ica_jade np.einsum (hot JADE loop), fir/multirate/
  polyphase np.convolve + matched_filter np.correlate (distinct-op convolution/
  correlation cascades), laplacian Schur L_pi·X + the dense_matvec kernel-internal
  @. Pure docs — `tools.total` stays 284; no rosetta/ToolEntry change. ABI 3. Next
  matmul: the convolve/correlate cascades, then the QR shape-polymorphic pass;
  then the `linalg_fft` ledger (122 — np.linalg.* / np.fft.*).
- **rc58 (done) — the convolve/correlate cascade (matmul decrement).** A length-N
  convolution is a rank-1 accumulate (a small matrix product), so it sits on the
  matmul ledger. rc58 adds a numpy-free helper
  `signal_processing._dsp_cascades.{convolve,correlate}` — Class I shift ∘ Class M
  scaled-accumulate (`full[i:i+nb] = full[i:i+nb] + a[i]*b`; numpy a carrier only),
  full/same/valid modes; `correlate = convolve(a, conj(v)[::-1])` with NumPy's exact
  same-mode crop (floor for na>=nv, ceil for na<nv). Value-faithful across 15
  length-combos × 3 dtypes × 3 modes. Routes the 6 DSP sites (fir / multirate /
  polyphase ×2 / closed_form + path_b matched_filter). **numpy-math ratchet
  `matmul` 18 → 12.** NOT a public `srmech.amsc` op — it composes carrier
  arithmetic with no own C symbol, so a public peer would only add
  `python_only_irreducible` debt (down-only ratchet forbids it without a C twin);
  a future rc can promote it WITH a native C twin. `tools.total` stays 284; no
  rosetta/ToolEntry change. ABI 3. The remaining 12 matmul: matrix_cascades
  QR-internals (8) + ica_jade einsum (2) + laplacian Schur/dense_matvec (2). Next:
  the QR shape-polymorphic pass; then the `linalg_fft` ledger (122).
- **rc59 (done) — the QR shape-polymorphic pass (matmul decrement).** The 8
  matrix_cascades QR-internal sites route onto the EXISTING value-faithful
  dense_* kernels (no new kernel): `np.vdot(v,v)` ×2 (the _norm2/vhv Hermitian
  self-bind) → `dense_dot_complex(conj(v), v)`; `np.outer` ×2 (the Householder
  reflector v vᴴ) → `dense_outer_complex`; the `conj(v)·R` / `Q·v` reflector
  matvecs → `dense_matvec_complex`; the lstsq back-solve `Qᴴ·b` →
  `dense_matvec/matmul_complex` (branch rhs ndim) and `R[i,i+1:]·x[i+1:]` →
  `dense_dot_complex` (1-D x) / `dense_matvec_complex` (k-col x — the
  shape-polymorphic case). Kernels are value-faithful → QR/SVD/lstsq/eig
  INVARIANTS preserved (verified vs numpy, real+complex, 1-D + multi-col rhs).
  **numpy-math ratchet `matmul` 12 → 4.** `tools.total` stays 284; no public-op /
  rosetta / ToolEntry change. ABI 3. The final 4 are genuinely deferred:
  ica_jade np.einsum (hot JADE cumulant loop) + laplacian Schur `L_pi·X` + the
  `dense_matvec_complex` kernel-internal `@` fallback (a kernel can't route onto
  itself). Next: the `linalg_fft` ledger (122 — np.linalg.* / np.fft.*).
- **rc60 (done) — the dense_norm cascade (linalg_fft decrement).** Opens the
  `linalg_fft` ledger (122) at its biggest cluster: the 20 default
  `np.linalg.norm` callsites (QM self-consistency residuals + signal-processing
  taper normalisations) — the Euclidean 2-norm / Frobenius norm √(Σ|x|²). New
  public `laplacian.dense_norm(x)` = Class N (rational.sqrt) ∘ Class M
  (dense_dot_complex self-bind Σ|x|²); numpy a carrier only. Value-faithful to
  the NumPy norm (real+complex, 1-D + n-D). Routes 20 sites across qm/{so8 ×7,
  relativistic ×3, spin ×3, triality ×3, gauge, sm, pseudo_hermitian} +
  signal_processing multitaper. **numpy-math ratchet `linalg_fft` 122 → 102.**
  New public op ⟹ describe tools.total 284 → 285 (+1 ToolEntry, +1 rosetta
  composition_of_c, __all__ + LAPLACIAN_OPS). ABI 3. Next linalg_fft batches:
  the np.fft.* family (→ spectral_cascades) and np.linalg.{svd,qr,eig,solve,inv}
  (→ matrix_cascades / laplacian decompositions).
- **rc76 (done, v0.7.5rc76) — the scalar-export layer `One.to_scalar`
  (matrix/vector → scalar; EXACT (num,den) default + opt-in numpy-FREE float
  export).** Carrier-removal #564, follow-on to the rc75 Hurwitz TOML-class
  reframe (lets a TOML class chain matrix-math → scalar output). User rule:
  *return float sometimes, never receive float* — `the_one` stays integer-only
  (no float input), and `as_float=True` does the single terminal `num/den` cast
  to a plain Python float with **no numpy** (pointedly UNLIKE the numpy-tier
  `One.to_numpy`/`to_matrix` exports #564 is retiring). Three exact modes:
  `trace` = `3+3σ+8σ·cosθ` (uses the SAME `rational.cos_series_truncate` the
  trigonometry/asymptotic_calculus catalogs validate — those catalogs are the
  target test), `sqnorm` = `Σ(num/den)²` (sign-free), `component` = the i-th of
  the 14 rationals. New public callable ⟹ rosetta `bignum_reference` (exact
  oracle tier, outside the debt ceilings) + `__all__`; takes a structured `One`
  (no MCP coercer) so it is tool-schema-coverage-EXEMPT (like `the_one`),
  bindable for TOML classes by dotted path. describe tools.total stays 287,
  classes stays 2; CEIL_NUMPY_CARRIER stays 52. ABI 3; no C change. New
  `test_to_scalar_rc76.py` (15 tests).
- **rc75 (done, v0.7.5rc75) — the numpy-Rosetta-peer DISSOLUTION: delete
  `qm.hurwitz.hurwitz_matrix`; declare the Hurwitz operator as a `[class]` over
  the EXACT `the_one`; FIRST carrier-ceiling decrement CEIL_NUMPY_CARRIER
  53 → 52.** Carrier-removal #564. rc50's `hurwitz_matrix` was a numpy 14×14
  FLOAT builder (np.zeros + cos/sin float-divided) DUPLICATING `One.to_matrix` —
  both float-cast the SAME exact cascade `the_one`. There was never supposed to
  be a continuous-float peer (chained float ops SUM rounding error every op; not
  correct-for-science). The exact `One` (14 exact (num,den) rationals) is the
  correct realisation; the float 14×14 is a lossy projection, legitimate only as
  the opt-in `One.to_matrix` export. The Hurwitz operator is now declared the
  class-from-TOML way (`make_class`): new `class_catalog/hurwitz.toml` `[class]`
  whose method `generate` BINDS `op="srmech.amsc.cascade.the_one"` → returns the
  EXACT `One`, bit-for-bit `to_flat_rational()`-identical, zero Python/numpy.
  `qm/hurwitz.py` is now numpy-free at top level (no `import numpy`) ⟹
  CEIL_NUMPY_CARRIER 53 → 52 (FIRST flip of the carrier arc). `hurwitz_planes`
  survives — the GENUINE Fano-plane cross-derivation from `octonion_mult_table`
  (exact integer-tuple structure, matches `One.FANO_PLANES`; still octonion-gated
  numpy until `qm.octonion` flips). New `[class]` ⟹ describe classes.total 1 → 2
  (Hurwitz joins Genome); deleted ToolEntry + rosetta line ⟹ describe tools.total
  288 → 287 (7 count-tests). Maths ratchets at floor; ABI 3; no C change.
  `test_hurwitz_rc50.py` rewritten (class-is-the-exact-the_one + dissolution +
  surviving plane cross-derivation).
- **rc74 (done, v0.7.5rc74) — Mat bridge primitive #3 (the LAST): numpy-FREE
  Hermitian eigendecomposition (`mat_hermitian_eigendecompose`;
  CEIL_NUMPY_CARRIER stays 53; new capability, not a flip).** Completes the
  bridge family with rc72 `mat_matmul` + rc73 `mat_solve`.
  `laplacian.mat_hermitian_eigendecompose(H: Mat) -> (eigvals, eigvecs)`
  diagonalises `H = V·diag(λ)·Vᴴ`: the real/complex `Mat.buffer`
  (interleaved-(re,im) row-major) feeds the native
  `srmech_hermitian_eigendecompose(n, H_il, out_eigvals, out_eigvecs_il)`
  ZERO-COPY (complex Mat) / interleaved-(re,0) once (real Mat); `eigvals` →
  (n,1) REAL Mat ascending, `eigvecs` → (n,n) COMPLEX unitary Mat (always
  complex, mirroring `hermitian_eigendecompose`). Unconditionally numpy-free:
  no-native / n>256 / convergence-miss falls back to srmech's own cyclic Jacobi
  (`_jacobi_eig_py`, the eigenvector-accumulating sibling of
  `_jacobi_eigvals_py`) — real-symmetric directly, complex-Hermitian via the
  real 2n×2n embedding `[[A,-B],[B,A]]` with `vⱼ = topⱼ + i·botⱼ` reconstruction
  + same-eigenvalue Gram–Schmidt (unitary inside a degenerate eigenspace). No
  abs() / libm (Class-K sign-branch; Class-N rational.sqrt). SUBPROCESS-proven
  numpy-free (native + forced-embedding-fallback); reconstruction +
  unitarity-pinned (NOT element-wise — eigenvector phase / degenerate basis is
  solver-chosen); eigenvalues match `numpy.linalg.eigvalsh` ~1e-13 both paths.
  New public callable ⟹ ToolEntry + rosetta `c_dispatched` + __all__/LAPLACIAN_OPS;
  describe tools.total 287 → 288. rc72 Mat MCP coercer + sample already cover it
  (no ratchet change). Maths ratchets at floor; ABI 3; no C change. New
  `test_mat_hermitian_eig_bridge_rc74.py` (8 tests). **The Mat↔native-dense-kernel
  bridge family (matmul + solve + eig) is now COMPLETE — a `qm.*` module's full
  numpy surface has Mat-native peers; the first module flip can now decrement
  the carrier ceiling.**
- **rc73 (done, v0.7.5rc73) — Mat bridge primitive #2: numpy-FREE dense solve
  (`mat_solve`; CEIL_NUMPY_CARRIER stays 53; new capability, not a flip).** The
  peer of rc72 `mat_matmul`. `laplacian.mat_solve(A: Mat, B: Mat) -> Mat` solves
  `A·X = B`: the real `Mat.buffer`s (row-major f64) feed the native
  `srmech_dense_solve_f64(n, nrhs, A, B, out)` ZERO-COPY via
  `(c_double*n²).from_buffer(...)` (C side const → Mats not mutated), output
  `array('d')` → Mat. Unconditionally numpy-free: no-native / dim>256 / singular
  falls back to srmech's own exact-rational Gauss–Jordan (`_solve_exact`, Class-N
  Fraction) → float64. REAL-f64 only (complex = real 2n×2n block embedding,
  later rc → NotImplementedError). SUBPROCESS-proven numpy-free (native +
  forced-fallback); value-faithful vs `numpy.linalg.solve` ~1e-15. New public
  callable ⟹ ToolEntry + rosetta `c_dispatched` + __all__/LAPLACIAN_OPS; describe
  tools.total 286 → 287. rc72 Mat MCP coercer + sample already cover it (no
  ratchet change). Maths ratchets at floor; ABI 3. New
  `test_mat_solve_bridge_rc73.py` (8 tests). rc74 = `mat_hermitian_eigendecompose`
  completes the bridge family.
- **rc72 (done, v0.7.5rc72) — the Mat↔native-dense-kernel bridge: numpy-FREE
  2-D matmul (`mat_matmul`; CEIL_NUMPY_CARRIER stays 53; new capability, not a
  flip).** Carrier-removal foundation #2. rc69 built the numpy-free 2-D `Mat`
  carrier (flat array('d'), row-major, interleaved-(re,im) = C99 double
  _Complex); this rc adds `laplacian.mat_matmul(a: Mat, b: Mat) -> Mat`, the
  numpy-free `@` the 2-D qm.* matmul callsites flip onto. Because Mat.buffer IS
  already the exact layout `srmech_dense_matmul_complex` reads, a complex operand
  feeds the kernel ZERO-COPY via `(c_double*2n).from_buffer(mat.buffer)` (C side
  const); a real operand is interleaved (re,0) once; output is a fresh array('d')
  → Mat. Follows the rc#563 numpy-free ctypes-marshalling precedent
  (`_jacobi_eigvals_native_listmarshal`) — HAS_NATIVE True with numpy absent.
  Unconditionally numpy-free: no-native / dim>256 falls back to a pure-Python
  triple loop (cascade, never numpy @). SUBPROCESS-proven (numpy blocked at
  sys.meta_path): computes on native + forced-fallback + real paths numpy-free;
  native complex kernel BIT-EXACT vs numpy (max-err 0.0). New public callable ⟹
  ToolEntry + rosetta `c_dispatched` + __all__/LAPLACIAN_OPS; describe tools.total
  285 → 286. Maths ratchets at floor; ABI 3. New `test_mat_matmul_bridge_rc72.py`
  (9 tests). rc73+ flips the qm.* matmul callsites onto it (lowering the carrier
  ceiling); `mat_solve` / `mat_hermitian_eigendecompose` are the follow-on rcs.
- **rc71 (done, v0.7.5rc71) — lazy op-registration: `signal_processing` is
  IMPORT-reachable numpy-FREE (CEIL_NUMPY_CARRIER stays 53; reachability, not a
  flip).** rc70 made the FFT family's MATH numpy-free, but a fresh
  `import srmech.signal_processing` on a numpy-absent install still raised: two
  layers ABOVE the carrier ratchet. (1) the eager `_require_numpy(...)` package
  gate (rc47), and (2) eager all-op registration (`from . import path_b_ops` →
  every op imported for registry population → the numpy ops' `import numpy`
  fired transitively, even for numpy-free ops). rc71 dissolves both:
  `closed_form_ops`/`path_b_ops` swap their eager `from . import (…every op…)`
  for a PEP-562 `__getattr__` (`_scientific.make_lazy_op_getattr`) deferring each
  op-module import to first attribute access; numpy-free Path-B ops still
  eager-register, numpy Path-B ops (`matched_filter`/`sign_quantise`/`wiener`)
  register a deferred LOADER with `path_registry` so `lookup`/`has_path`/
  `dispatch` resolve them on-demand; `registered_ops()` is declarative
  (lists pending lazy ops without importing). Eager `__init__` gate removed.
  SUBPROCESS-proven: `test_signal_processing_numpy_free_reachable_rc71.py`
  blocks numpy at `sys.meta_path` before the first import (a real numpy-absent
  install — `monkeypatch` can't prove fresh-import-numpy-freedom) and asserts
  import + FFT-family run + dispatch succeed numpy-free, a numpy op raises the
  clean `[scientific]` hint, plus a down-only static guard the eager gate stays
  gone. No carrier flip (ceiling 53) / no public op (describe stays 285); maths
  ratchets at floor. ABI 3. Next: the `Mat`↔native-dense-kernel bridge (the 2-D
  qm/* foundation).
- **rc70 (done, v0.7.5rc70) — carrier-flip #1: the FFT op-family runs 1-D
  numpy-FREE (CEIL_NUMPY_CARRIER 61 → 53).** First real module flip of the
  carrier arc. `_fft_carrier`'s numpy was pure carrier-shaping (asarray /
  moveaxis / reshape / pad / output-alloc) while the transform already rode the
  numpy-free 1-D `spectral_cascades`. The common 1-D/default-axis path is now
  numpy-free (list → cascade → list; framework-native list when numpy absent,
  ndarray for parity when present); n-D/non-default-axis still uses numpy lazily.
  8 modules drop their top-level `import numpy` — leaf `_fft_carrier` +
  `closed_form_ops.{fft,ifft,rfft}` (redundant `np.asarray` removed; `_fc`
  coerces) + `closed_form_ops.spectrogram` (annotation-only import) +
  `path_b_ops.{fft,ifft,rfft}` (numpy-free length via the input's own
  `.shape`/`len`). HONEST-not-theater: `test_fft_family_numpy_absent_rc70.py`
  hides numpy and proves fft/ifft/rfft/fftfreq + n-pad/truncate still compute
  value-faithful (~1e-9). Same cascade ⟹ existing 788-test FFT suite green. No
  public-op change (describe stays 285); maths ratchets unchanged at floor.
  ABI 3. 2-D qm/* matrix modules come later behind a Mat↔native-kernel bridge.
- **rc69 (done, v0.7.5rc69) — carrier-removal arc Phase 0 (infra): numpy-free
  2-D `Mat` carrier + down-only carrier ratchet.** The numpy-MATH sweep
  (rc53–rc68) is floored; what's left is numpy-as-CARRIER — 61 submodules still
  `import numpy` at module level (lazy submodule imports; the package imports
  numpy-free). New `srmech.amsc.mat.Mat`: the 2-D peer of the `HV` carrier — a
  dense matrix over a flat `array('d')`, **row-major, interleaved `(re,im)`**
  for complex (C99 `double _Complex` layout → `.buffer` directly ctypes-castable
  to the native dense kernels, no copy/no numpy on HAS_NATIVE). numpy-free at
  import (lazy `.to_numpy()` bridge; numpy-free path is `.tolist()`/`.buffer`).
  New down-only ratchet `test_numpy_carrier_ratchet.py` (`CEIL_NUMPY_CARRIER=61`)
  + a guard that `mat.py` stays numpy-free. NO module flips this rc (ratchet
  stays 61; mat.py doesn't bump it). Unregistered handle (like `HV`) ⟹ no
  ToolEntry/introspect/rosetta gate (describe stays 285). ABI 3. rc70+ flips
  modules onto `Mat` one cluster per rc, lowering the ceiling toward 0.
- **rc68 (done, v0.7.5rc68) — real-antisymmetric eig → iS-Hermitian cascade
  route (linalg_fft decrement; the maths-engine sweep's last bulletproof step).**
  Both `np.linalg.eig` sites in `qm/so8.py` take a REAL antisymmetric matrix —
  the `J` complex-structure op (584) and `ad(H)` for a Cartan element (646),
  each with a purely-imaginary `±i·weight` spectrum. For real skew `S`, `iS` is
  Hermitian, so eigenpairs come from the shipped C-backed
  `hermitian_eigendecompose(iS)`: `λ_S = −i·μ` (μ real, ascending), SAME `V`.
  New PRIVATE `so8._eig_real_skew` routes both — no `np.linalg.eig`. Sound under
  degeneracy ONLY because so8 consumes `V` invariantly: 584 rebuilds the triplet
  from the `+i` eigenspace SPAN (projector basis-invariant, even for `J`'s mult-3
  eigenspace), 646 reads scale/phase-invariant Rayleigh-quotient weights. Both
  differential-tested vs `np.linalg.eig` on a degenerate (mult-3) real-skew
  matrix; the full so8/triality/an_embedding/quaternion/killing/semisimple suite
  (80 tests) stays green with BOTH sites routed. **numpy-math ratchet linalg_fft
  25 → 23** (2 genuine eig calls; helper docstrings `numpy.linalg.`-free).
  Private helper ⟹ no ToolEntry gate (describe stays 285). ABI 3. The 1 remaining
  `np.linalg.eig` (pseudo_hermitian:182, general `O` — NOT skew, so iS trick N/A)
  needs a general non-Hermitian eigenvector cascade that does not exist; rest of
  linalg_fft is numpy-as-accuracy or cascade-internal fallbacks. **Maths-engine
  sweep floored; next numpy removal is the carrier layer.**
- **rc67 (done, v0.7.5rc67) — real-symmetric eigh → C-backed hermitian +
  eigenvector sign-canon (linalg_fft decrement; lane 1 past the floor).**
  `laplacian.symmetric_eigendecompose`'s `np.linalg.eigh` routes onto the
  already-shipped, C-backed `hermitian_eigendecompose` (real-symmetric IS
  complex-Hermitian — native Jacobi peer when present; numpy eigh only as THAT
  op's own shared fallback). Real-symmetric eigenvectors come back real
  (imag ~0), so we take `.real` and a new PRIVATE
  `_canonicalize_eigenvector_signs` pins each column's ±1 sign (Class-K: flip
  so the largest-|·| entry is positive, magnitude via `col²` — no `abs()`, no
  float sqrt; the `re²+im²`+√ draft tripped the A-N `float_pow` ratchet).
  LAPACK's arbitrary eigenvector sign was a HIDDEN non-settable convention;
  this makes it a deterministic SETTABLE one (endianness precedent).
  Degenerate-subspace U(k) basis stays solver-chosen + reconstruction-invariant;
  sign-canon pins the per-column Z₂. Correctness via basis-INVARIANT props (ascending eigvals == eigvalsh,
  reconstruction, orthonormality) on degenerate cases (4-cycle / identity /
  block-degen), real V on both native + numpy-fallback paths. **numpy-math
  ratchet linalg_fft 28 → 25** (1 genuine call + 2 textual docstring mentions).
  Rosetta: symmetric_eigendecompose python_only_irreducible → composition_of_c
  (now composes c_dispatched hermitian), CEIL_PYTHON_ONLY_IRREDUCIBLE 108 → 107
  (debt closed). Private helper ⟹ no ToolEntry gate (describe stays 285). ABI 3.
- **rc66 (done, v0.7.5rc66) — complex inv → real 2n×2n block embedding of the
  native dense_solve (linalg_fft decrement; FIRST new-capability step past the
  carrier-swap floor).** The lone complex `np.linalg.inv` — pseudo_hermitian's
  `η = (V·Vᴴ)⁻¹` Mostafazadeh metric — routes onto a new PRIVATE Class-L helper
  `laplacian._dense_solve_complex`. `(Aᵣ+iAᵢ)(u+iv)=(bᵣ+ibᵢ)` ⟺ the real 2n×2n
  `[[Aᵣ,-Aᵢ],[Aᵢ,Aᵣ]]·[u;v]=[bᵣ;bᵢ]` (X=u+iv); EXACT embedding (concatenate /
  slice / .real / .imag — numpy a carrier only) riding the shipped NATIVE real
  dense_solve. HPD Gram `V·Vᴴ` → well-conditioned → `== numpy` inv/solve ~1e-9
  (verified incl. `M·M⁻¹=I`, general vector+matrix complex solve, η-metric
  `O†η=ηO`). Underscore-private ⟹ NO registry/ToolEntry gate (describe stays
  285). **numpy-math ratchet linalg_fft 29 → 28; np.linalg.inv → 0.** ABI 3.
  **ROUTE-SAFE FLOOR reached** — the remaining 20 genuine sites are
  numpy-as-accuracy (6 matrix_rank + 7 so8 svd nullspace), irreducible numpy
  fallbacks inside the cascade ops (dense_solve / hermitian_eigendecompose), or
  need eigenvector-sign-canonicalization (eig×3 / eigh-1062 / mimo svd) — a
  legitimate residual, not unfinished carrier work.
- **rc65 (done, v0.7.5rc65) — np.linalg.pinv → cascade SVD reconstruct
  (linalg_fft decrement).** Cashes in rc64's "value-faithful for LARGE singular
  values" on the lone genuine `np.linalg.pinv` site — the qm/so8.py
  `_killing_form` structure-constant least-squares solve. New `_pinv` helper:
  `A⁺ = V·diag(1/s)·Uᴴ` from `matrix_cascades.svd`, NumPy's `rcond=1e-15`
  cutoff. Route-safe BECAUSE (a) the pseudoinverse is UNIQUE → the per-factor
  U/V column-sign ambiguity cancels, and (b) the generator stack is
  full-column-rank (the semisimplicity certificate) → every `s` well clear of
  the cutoff (no nullspace/small-`s` accuracy exercised — the exact regime rc64
  flagged as numpy-as-accuracy for matrix_rank). Verified `_pinv == numpy.pinv`
  (~1e-7) incl. the `pinv·bracket` matvec usage + the `A·A⁺·A=A` identity;
  reconstruction uses `dense_matmul_real` (NOT `@`, matmul ledger untouched).
  23 so8/Killing/stabiliser tests pass (incl. g₂ full-rank-14 Cartan check the
  rc63b matrix_rank route had broken). 1 textual `numpy.linalg.pinv` reworded.
  **numpy-math ratchet linalg_fft 30 → 29.** No rosetta / ToolEntry change
  (describe tools.total stays 285). ABI 3. Deferred: complex inv (complex
  solve), eigh/eigvalsh (eigenvector-sign-delicate), eig/svd-direct;
  matrix_rank stays on numpy PERMANENTLY (numpy-as-accuracy).
- **rc63b (done, v0.7.5rc64) — map_ml real inv → dense_solve (linalg_fft
  decrement).** The 2 real `np.linalg.inv` covariance-inverse sites in
  signal_processing/closed_form_ops/map_ml.py route onto
  `laplacian.dense_solve(M, np.eye(n))` (the inverse IS A·X=I; unique, well-
  conditioned; == numpy ~1e-9). The so8 `np.linalg.matrix_rank` sites were
  INVESTIGATED and KEPT ON NUMPY — the cascade SVD's nullspace (small-singular-
  value) accuracy is too low for an absolute-tol rank count on a rank-deficient
  matrix (over-counted rank_with_so4 6→9); a numpy-as-ACCURACY site, deferred
  with the dense_solve numpy fallback + matmul-4 kernel-internal tail.
  **numpy-math ratchet linalg_fft 32 → 30.** No rosetta / ToolEntry change
  (describe tools.total stays 285). ABI 3. Later sub-rcs: pinv (svd-reconstruct,
  sign-invariant), complex inv (complex solve), eigh (hermitian_eigendecompose),
  eig/svd-direct.
- **rc63a (done) — np.linalg.* cluster, first sub-batch (linalg_fft
  decrement).** Route the sign/order-invariant decompositions onto the
  already-shipped value-faithful `matrix_cascades` cascades. 5
  `q, _ = np.linalg.qr(X)` (qm/so8.py) → `matrix_cascades.qr`: Q consumed only
  via `Q @ Qᵀ` projectors / column span / sum-of-squares leak (all invariant to
  QR per-column sign; verified Q@Qᵀ == numpy ~1e-9). 2 `np.linalg.eigvals(X)`
  (pseudo_hermitian max|imag|, esprit rotation set) → `.eigvals` (multiset,
  set-faithful ~1e-12). 83 op-tests pass. ~22 textual `numpy.linalg.X` mentions
  in matrix_cascades / tool_schema / triality (no genuine calls) reworded to
  "NumPy X". **numpy-math ratchet linalg_fft 61 → 32.** No rosetta / ToolEntry
  change (describe tools.total stays 285). ABI 3. rc63b/c: the delicate svd /
  matrix_rank / inv / eig / eigh / solve / lstsq / pinv (mostly qm/so8.py +
  amsc/laplacian.py), with sign/order handling per callsite.
- **rc62 (done) — DRAIN the np.fft.* family (linalg_fft decrement).** New
  `signal_processing/_fft_carrier.py` lifts the 1-D `spectral_cascades` fft/ifft
  to NumPy's ndarray + n= (zero-pad / truncate) + axis= contract (NumPy a
  carrier only: moveaxis / reshape / pad / slice), plus a real-input rfft
  (full-transform-then-slice; complex input raises TypeError mirroring NumPy)
  and an fftfreq carrier (integer bin indices / (n*d); no transcendentals). The
  8 remaining genuine np.fft.* calls route onto it — the 6 Path-A/Path-B
  fft/ifft/rfft ops (closed_form_ops + path_b_ops) + the 2 cross_spectral
  fftfreq sites — and the ~18 textual `numpy.fft.X` doc/summary mentions are
  reworded to "NumPy fft". Carriers bit-faithful to NumPy (real+complex, 1-D +
  n-D, every axis, n pad/truncate, ~1e-9); rfft is value-faithful (~1 ULP) NOT
  bit-identical to pocketfft (even np.fft.fft(real)[:n//2+1] != np.fft.rfft),
  so the rfft-vs-NumPy tests are now allclose (Path-A == Path-B cascade identity
  stays exact). **np.fft. -> 0. numpy-math ratchet linalg_fft 87 -> 61.** No
  rosetta / ToolEntry change (describe tools.total stays 285). ABI 3. Next: the
  np.linalg.{svd,qr,eig,solve,inv,...} cluster (~36 sites, mostly qm/so8.py).
- **rc61 (done) — the np.fft.* family, first batch (linalg_fft decrement).**
  The 15 one-dimensional `np.fft.fft(x)` / `np.fft.ifft(x)` callsites across
  signal_processing route onto the EXISTING value-faithful
  `cascade.spectral_cascades.fft` / `.ifft` (rc36/rc37 radix-2 Cooley–Tukey +
  dft fallback for non-power-of-2 N; exact-until-rotation). NO new public op —
  rc61 swaps only the carrier (NumPy FFT → cascade), value-for-value, wrapping
  `np.asarray(...)` so the result stays an ndarray. 15 sites:
  closed_form_ops/{cross_spectral ×4, ofdm ×2, spectral_subtraction ×2,
  multitaper ×1, stft ×2, wiener ×2} + path_b_ops/wiener ×2. Cascade verified
  == numpy (real+complex, N=2…100, ~1e-9); DSP-op invariants (coherence, Wiener
  gain, OFDM round-trip, STFT, multitaper) preserved — 447 signal_processing
  tests pass. **numpy-math ratchet `linalg_fft` 102 → 87.** No rosetta /
  ToolEntry change (describe tools.total stays 285). ABI 3. Remaining np.fft.*
  = the n=/axis= Path-A ops (fft.py/ifft.py/rfft.py + fftfreq) needing an
  array-aware (n-pad + axis) wrapper — next batch; then np.linalg.{svd,qr,eig,
  solve,inv} (~36 sites, mostly qm/so8.py).
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
