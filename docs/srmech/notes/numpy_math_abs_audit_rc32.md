# srmech codebase audit — `abs()` + numpy-math residue (rc32)

**Done 2026-06-04** via three parallel sub-agent sweeps (amsc / qm+signal_processing+spectral / dsl+bus+cli+mcp+introspect+rbs_lm) at the user's direction, after three standing directives:

1. **"abs() is never fine"** — magnitude/sign is an explicit Class-K sign-branch
   (`x if x >= 0 else -x` / `np.where(x>=0, x, -x)` / real-imag composition),
   never an ALU `abs()` / `np.abs()` / `math.fabs()` / `sqrt(·²)` stealth-abs.
2. **"never use numpy math when srmech can do it with a cascade"** — when srmech
   ships the primitive (a C op or a Python cascade), use it; don't delegate the
   *math* to numpy. (Container/layout ops — `np.zeros/array/asarray/reshape/
   tolist/copy/astype/sum/mean` — are NOT "math" and are fine.)
3. **"audit entire codebase for numpy math residue in this rcN."**

## Category A — `abs()` residue: FIXED codebase-wide in rc32 (value-preserving)

Every site below was replaced with a value-identical explicit Class-K form and
is now guarded by a permanent **AST ratchet** test
(`tests/test_laplacian_numpy_free.py::test_no_abs_calls_anywhere_in_srmech` —
fails CI if any real `abs()`/`np.abs()`/`math.fabs()` CALL reappears anywhere in
`srmech/`; docstring mentions don't trip it).

- `amsc/rational.py` ×2 (`abs()` → sign-branch feeding `math.gcd`)
- `amsc/kepler.py` (Newton-step convergence `abs(delta)` → sign-branch)
- `amsc/harmonics.py` ×5 (`sqrt(x*x)` / `sqrt(·²)` stealth-abs → `np.where` /
  sign-branch; the docstring's false "no abs()" claim corrected)
- `amsc/laplacian.py` (`signed_laplacian` `np.abs(A_off)` → `np.where`)
- `amsc/cascade/hypercomplex_dft.py` (my rc31 ℍ-closure guard `np.abs(v[4:]).sum()`
  → `np.any(v[4:] != 0.0)` — a presence test needs no magnitude at all)
- `qm/bell.py` ×3, `qm/sm.py` ×2, `qm/pseudo_hermitian.py` ×3
  (`np.abs(real)` → `np.where`; `abs(scalar)` → sign-branch; `abs(phi)**2` →
  `phi.real**2 + phi.imag**2`)
- `spectral/__init__.py` (`np.abs(complex)` → `np.hypot(real, imag)`)
- `signal_processing/`: 21 sites across 13 files — complex `np.abs(X)**2` →
  `X.real**2 + X.imag**2`; complex `np.abs(z)` → `np.hypot(z.real, z.imag)`;
  scalar `abs()` → sign-branch (`form_function_rotation.py`, `ica_jade.py`, and
  the `closed_form_ops/` DSP family: cross_spectral, mlse, multitaper, music,
  spectral_subtraction, spectrogram, wiener, fsk, ofdm, psk_qam + `path_b_ops/wiener`).

**Verified clean (already abs-free):** `qm/octonion.py` (`octonion_norm` routes
through the Class-K cascade `_magnitude`, not abs — the documented claim holds),
`qm/triality.py`, `qm/so8.py`, and all of `dsl/`, `bus/`, `cli/`, `mcp/`,
`introspect/`, `rbs_lm/`, `llm/`, `adapters/`.

## Category B — numpy math where srmech HAS a cascade: PARTIALLY done; rest STAGED to rc33

**Done in rc32 (the §22-core Class-L spectral op):**
- `amsc/laplacian.py` `jacobi_eigvals` no-native fallback: `np.linalg.eigvalsh`
  → **srmech's own pure-Python Jacobi cascade** (`_jacobi_eigvals_py`). The
  Class-L eigenvalue math is now srmech's, never LAPACK. Native C stays primary.
- The real Laplacian builds use srmech's pure-Python builder (not numpy
  elementwise) in the no-native path.

**STAGED to rc33** (engine-routing — behavioural, needs per-site parity tests;
NOT silently dropped):
- ~11 `np.linalg.eigh`/`eigvalsh` on Hermitian/symmetric matrices (qm/gauge,
  qm/potentials, qm/single_particle ×4, qm/so8 Killing form, signal_processing
  esprit/heat_kernel/ica_jade/music) → route through `laplacian.hermitian_eigendecompose`
  (srmech's Class-L primitive).
- ~15 `np.cos/np.sin/np.arctan2/math.cos/math.sin` (windows, DCT bases,
  CKM/Weinberg angles, rotation eigenvalues) → `srmech.amsc.rational` /
  `asymptotic_calculus` Class-N exact-rational trig.

**Keep numpy (genuinely scientific-tier, no srmech equivalent — §22):**
`np.linalg.{svd,qr,eig(non-Hermitian),lstsq,inv,solve,pinv,matrix_rank,norm}`,
`np.einsum`, `np.kron`, `np.outer`, `np.trace`, `np.convolve/correlate`,
complex `np.exp` time-evolution phases. **`np.fft.*`** is architectural — both
the Path-A and Path-B `signal_processing` FFT ops delegate to numpy (there is no
hand-rolled srmech FFT); building a native srmech FFT cascade is its own future
voxel, not a residue fix.

## Why staged, not all-in-rc32

rc32 = §22 laplacian-numpy-free + the **absolute** `abs()` sweep (value-preserving,
low-risk). The Category-B *engine-routing* swaps WHICH solver computes a result
(numpy LAPACK → srmech primitive) — value-equal to round-off but a different code
path that needs per-site parity verification, and §22 itself keeps the heavy qm
linear algebra numpy-backed. Bundling 26 engine swaps into the same rc as the
16-file abs sweep would make one un-reviewable, regression-prone rc. rc33 does the
routing as a focused, separately-verified voxel.

## rc33 CLOSURE (2026-06-04) — Category B routed

Done in **v0.7.0rc33**. The premise that "full trig routing needs new infrastructure"
was WRONG (user-corrected): the Class-N Taylor cascades (`sin/cos/atan_series_truncate`)
were always globally convergent and `pi_cascade_digits` always shipped — the only gap
was a **float-returning, range-reduced wrapper** composing them. That wrapper now exists:
`srmech.amsc.rational.{cos,sin,tan,atan,atan2}` (π-cascade range reduction → Class-N
anchor → Taylor → project to float; `atan` three-band √2∓1 reduction). Measured vs libm:
cos/sin ≈6e-16, atan/atan2 ≈2e-16 (machine ε). +5 tool-schema entries (`describe` 210→215).

- **Trig sites routed** — `qm.sm` CKM/Weinberg angles + `signal_processing`
  window/basis/rotation trig (cross_spectral, dct, multirate, multitaper, stft,
  ica_jade, form_function_rotation). The amsc-internal solver trig (kepler Newton,
  kuramoto coupling, hypercomplex_dft twiddle, laplacian magnetic-phase) was NOT in
  this audit's "~15" and stays as its own future consideration (those are inside
  iterative solvers / DFT twiddles where the substitution is a separate fidelity Q).
- **Hermitian eig routed** — the 11 `np.linalg.eigh`/`eigvalsh` sites in
  qm.{potentials,gauge,single_particle,so8} + sp.{esprit,heat_kernel,ica_jade,music}
  → `amsc.laplacian.hermitian_eigendecompose` (native C complex-Hermitian Jacobi on
  the native path). Real-symmetric inputs `.real` the eigenvectors; complex-Hermitian
  keep complex128. Per-site parity tests (eigvals ≤1e-9 + reconstruction).
- **Still scientific-tier per §22** (no srmech cascade yet): svd / qr / non-Hermitian
  eig / lstsq / einsum / kron / complex-exp / FFT.
