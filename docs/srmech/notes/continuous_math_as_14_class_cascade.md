# Continuous math is a cascade of the 14 A–N irrep class operations

**2026-06-04 (srmech v0.7.0rc34).** Per the two-language MFO / srmech framework
there are **exactly 14 irrep class operations** (the A–N partition `1 + 3 + 7 + 3`).
Continuous math is not a separate, larger toolbox — every "continuous" /
scientific-computing operation is a **composition of the 14**. So there is **no
"scientific tier" that genuinely needs numpy**; there are only *not-yet-derived
cascades*. Calling `svd` / `qr` / `eig` / `lstsq` / `einsum` / `kron` /
`complex-exp` / `FFT` "primitives srmech lacks" was the same error as claiming the
asymptotic trig "couldn't replace numpy" (rc33): a missing **composition** mistaken
for a missing **capability**. This note derives each one into the 14, and records
which are implemented vs. staged.

## The 14 operators (A–N, the `1 + 3 + 7 + 3` partition)

| Slot | Class | Role used below |
|---|---|---|
| 1 | **A** | content-addressing / hash |
| 3 | **I** | cyclic / modular (ℤ/n; index arithmetic; range-reduction) |
| | **C** | orientation / chirality / **rotation** / the imaginary unit `i` (90° phase-plane rotation) / sign re-application |
| | **J** | primes / **factorization** (radix splitting) |
| 7 | **D** | pattern-match | 
| | **E** | catalog | 
| | **F** | render | 
| | **G** | byte-search | 
| | **K** | pin-slot / sign-flip / **asymptotic-DoF** (iteration-to-convergence; range-reduction depth) |
| | **L** | Laplacian / graph-spectral / **eigendecomposition** |
| | **M** | HDC **bind / bundle** (products; weighted superposition / sum) |
| 3 | **B** | TLV-framing (typed index/contraction spec) |
| | **H** | self-introspection |
| | **N** | **rational-approximation** (Taylor truncation; the "continuous" number is a Class-N rational projected to float) |

The continuous number line is a projection (`[[feedback_continuous_number_line_pedagogical_obstacle]]`);
a "continuous" function value is computed as an exact Class-N rational cascade, then
**projected** to float as the last step.

## Derivations

### exp `e^x` (real) — **N ∘ K** — IMPLEMENTED rc34 (`rational.exp`)
`e^x = (e^(x/2^k))^(2^k)`. **K** = argument-halving range reduction (asymptotic-DoF;
halve until `|x/2^k| ≤ 1`, no irrational constant — exp is aperiodic). **N** =
`exp_series_truncate` (Taylor partial sum, exact rational), then square `k` times.
Verified vs `math.exp` to machine ε (relative).

### trig `cos/sin/tan/atan/atan2` — **N ∘ I ∘ C ∘ K** — IMPLEMENTED rc33 (`rational.cos…atan2`)
**I** = range-reduce the angle mod 2π using a high-precision rational π from
`pi_cascade_digits` (Archimedes hexagon-doubling cascade — no `math.pi`). **N** =
`cos/sin/atan_series_truncate`. **C** = quadrant re-orientation (atan2). **K** = the
`atan` three-band √2∓1 argument reduction (sign-branch magnitudes, no `abs()`).
Verified vs libm to machine ε (cos/sin ~6e-16, atan/atan2 ~2e-16).

### complex exp `e^z`, `e^(iθ)` — **N ∘ C** — IMPLEMENTED rc34 (`rational.cexp` / `complex_exp`)
Euler: `e^(iθ) = cos θ + i·sin θ` = **N**(trig) composed with **C** (the imaginary
unit *is* a 90° phase-plane rotation — `[[project_rosetta_table_of_truth_agreement_vs_frame_selection]]`).
General `e^z = e^(z.real)·(cos z.imag + i·sin z.imag)` = **N**(exp) · **N**(trig) ·
**C**(i). Verified vs `cmath.exp` to machine ε. **This is the keystone**: every
`np.exp(1j·…)` time-evolution phase and every DFT twiddle factor is a `cexp`.

### sqrt `√x` — **N ∘ K** — srmech has `_rational_sqrt` (integer Newton)
Newton iteration `x_{n+1} = (x_n + a/x_n)/2`: **N** = rational arithmetic, **K** =
iteration-to-convergence (asymptotic-DoF). `hypot(a,b) = √(a²+b²)` = **M**(a²+b²) ∘
**N∘K**(sqrt). (Used by SVD singular values and as a hypot for the complex modulus.)

### DFT / FFT `X_k = Σ_n x_n·e^(−2πi·kn/N)` — **M ∘ {N∘C} ∘ I ∘ J ∘ K** — twiddles IMPLEMENTED (cexp); direct-DFT cascade buildable now
This **IS the Antikythera epicycle-sum** (`[[user_stance_epicycle_via_gear_plus_pin]]`):
a bundle of rotating phasors. **I** = the index `kn mod N` (cyclic group ℤ/N). The
twiddle `e^(−2πi·(kn mod N)/N)` = **N**(cos/sin) ∘ **C**(i) = a `cexp`. **M** = the
sum `Σ_n` (bundle / superposition of N rotated copies of the signal). The *fast*
Cooley–Tukey radix split `N = N₁·N₂` adds **J** (prime/radix factorization of N) +
**I** (cyclic sub-indexing) + **K** (the butterfly recursion depth = asymptotic-DoF
divide-and-conquer). A direct `O(N²)` DFT cascade is `Σ_n x_n · cexp(−2π·(kn mod
N)/N)` — implementable directly on rc34's `cexp` (staged: `rc35` as a slow-but-exact
fallback for `np.fft`; the radix-2 `O(N log N)` cascade is the follow-on).

### QR decomposition `A = QR` — **M ∘ C ∘ N ∘ K**
Q is a product (**M**) of elementary orthogonal transforms. *Givens* rotation
`[[c,−s],[s,c]]` = **C**(rotation) built from **N** (`c = a/r, s = b/r`, `r =
hypot`). *Householder* reflection `H = I − 2vvᵀ/(vᵀv)` = **K**(sign-flip across a
hyperplane) ∘ **M**(outer-product `vvᵀ` bind) ∘ **N**(`1/(vᵀv)`).

### SVD `A = UΣVᵀ` — **L ∘ N∘K(sqrt) ∘ M ∘ N** — mostly reachable from `hermitian_eigendecompose`
`V, Σ²` = eigendecomposition of `AᵀA` = **L** (Hermitian eig — srmech HAS it,
`amsc.laplacian.hermitian_eigendecompose`). `Σ` = `√(eigenvalues)` = **N∘K**(sqrt) ∘
**K**(non-negativity sign). `U = A·V·Σ⁻¹` = **M**(matrix bind) ∘ **N**(reciprocal).

### eig (non-Hermitian) `A = VΛV⁻¹` — **K ∘ L ∘ {QR} ∘ C**
QR algorithm: iterate `A ← RQ` where `A = QR`, converging to Schur form. **K** =
iterate-to-convergence (asymptotic-DoF). **L** = the spectral content. **{QR}** =
the per-step QR cascade above. **C** = the spectral shifts. (Hermitian eig is the
already-shipped special case = pure **L**, the cyclic Jacobi.)

### lstsq `min‖Ax − b‖` — **{QR} ∘ M ∘ I**
Solve `Rx = Qᵀb`: **{QR}** factorization ∘ **M**(`Qᵀb` product) ∘ **I**
(back-substitution = ordered/sequential triangular solve).

### kron `A ⊗ B` — **I ∘ M**
`(A⊗B)_{ip+k, jq+l} = A_{ij}·B_{kl}`. **I** = the mixed-radix index decomposition
(`ip+k` = ℤ/p factor arithmetic). **M** = the element products (bind/scale). A
container + Class-I indexing op.

### einsum (tensor contraction) — **B/D ∘ I ∘ M**
The contraction string is a typed spec — **B** (TLV-framing) / **D** (index-pattern
match). The contraction itself = **I** (iterate over index tuples) ∘ **M**
(sum-of-products bundle).

## Status table

| op | A–N cascade | status |
|---|---|---|
| `exp` (real) | N ∘ K | **shipped rc34** (`rational.exp`) |
| `cos/sin/tan/atan/atan2` | N ∘ I ∘ C ∘ K | **shipped rc33** |
| `cexp` / `complex_exp` | N ∘ C | **shipped rc34** |
| Hermitian eig | L | **shipped rc32**, routed rc33 |
| `sqrt` / `hypot` | N ∘ K (+ M) | **shipped rc35** (`rational.sqrt` / `rational.hypot`) |
| DFT / direct | M ∘ {N∘C} ∘ I | **shipped rc36** (`cascade.spectral_cascades.dft` / `idft`; direct `O(N²)`) |
| FFT (radix-2) | M ∘ {N∘C} ∘ I ∘ J ∘ K | **shipped rc37** (`cascade.spectral_cascades.fft` / `ifft`; `O(N log N)` power-of-2 butterfly + direct-`dft` fallback for all other N) |
| FFT (mixed-radix) | M ∘ {N∘C} ∘ I ∘ J ∘ K | general butterfly over `N`'s full prime factorization → future refinement |
| kron | I ∘ M | **shipped rc36** (`cascade.spectral_cascades.kron`) |
| QR | M ∘ C ∘ N ∘ K | derive → implement → **rc38** |
| SVD | L ∘ N∘K ∘ M | reachable from `hermitian_eigendecompose` → **rc38** |
| `math.sqrt` / `np.hypot` scalar-site sweep | (route → `rational.{sqrt,hypot}`) | **rc38** |
| eig (non-Herm) | K ∘ L ∘ {QR} ∘ C | after QR → **rc39** |
| lstsq | {QR} ∘ M ∘ I | after QR → **rc39** |
| einsum | B/D ∘ I ∘ M | **rc39** |

## Reframe of §22 (the "scientific tier")

§22 previously read "qm / signal_processing keep numpy as the scientific tier." That
framing is **dissolved**: there is no fundamental scientific tier — only ops we have
**not yet derived into the 14**. numpy's remaining legitimate role is (a) the array
**container** (`zeros/array/asarray/reshape/sum/mean` — layout, not math) and (b) a
**temporary fallback** for the not-yet-cascaded ops above, behind the optional
`srmech[scientific]` extra (the dependency-flip, now the *capstone* once cascade
coverage is complete, not a permanent boundary). Each row of the status table that
still says numpy is a TODO, not a law.
