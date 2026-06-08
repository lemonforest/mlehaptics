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

### exp `e^x` (real) — **N ∘ K** — IMPLEMENTED rc34 (`rational.exp`); float path UNIFIED on the C Cody-Waite reduction v0.7.5rc3
`e^x = e^r · 2^n` with `x = n·ln2 + r`, `|r| ≤ ln2/2`. **K** = the additive range
reduction (asymptotic-DoF; pick the integer `n`, form `r` via the two-word
`LN2_HI + LN2_LO` Cody-Waite split — no irrational constant survives to the series,
exp is aperiodic). **N** = the Q61 integer exp-Taylor `1 + r + r²/2! + …`; the `2^n`
scale folds straight into the IEEE exponent. Verified vs `math.exp` to ~1 ULP.
This is the **bit-exact peer of `srmech_exp`** (`c/src/srmech_explog.c`) — the
float `rational.exp` dispatches to it natively. (The earlier `(e^(x/2^k))^(2^k)`
halve-and-square reduction amplified error to ~345 ULP and is retired; the exact-
rational `exp_series_truncate` remains the higher-precision REFERENCE surface.)

### log `ln(x)` (real) — **N ∘ K** — IMPLEMENTED v0.7.5rc3 (`rational.log`)
`ln(x) = e·ln2 + log(m)` with `x = m·2^e` read from the bit pattern, `m` folded into
`[1/√2, √2)`. **N** = the Q61 integer series `log(m) = 2·atanh((m−1)/(m+1))`; **K** =
the integer `m·2^e` decomposition + the band fold. Bit-exact peer of `srmech_log`
(`c/src/srmech_explog.c`); dispatches to C natively. Domain: `x < 0 → NaN`,
`x == 0 → −Inf`. The exact-rational `log1p_series_truncate` is the REFERENCE surface.

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
| QR | M ∘ C ∘ N ∘ K | **shipped rc38** (`cascade.matrix_cascades.qr`; Householder, reduced+complete) |
| SVD | L ∘ N∘K ∘ M | **shipped rc38** (`cascade.matrix_cascades.svd`; Gram-matrix `hermitian_eigendecompose`) |
| lstsq | {QR} ∘ M ∘ I | **shipped rc39** (`cascade.matrix_cascades.lstsq`; back-substitution) |
| einsum | B/D ∘ I ∘ M | **shipped rc39** (`cascade.matrix_cascades.einsum`; general index-iteration) |
| eig (non-Herm) | K ∘ L ∘ {QR} ∘ C | **shipped rc39** (`cascade.matrix_cascades.eigvals`; shifted-QR iteration) |
| `math.sqrt` scalar-site sweep | (route → `rational.sqrt`) | **shipped rc40** (12 sites: laplacian Jacobi ×5 + bell/octonion/sm/hypercomplex_dft; AST ratchet; see `notes/sqrt_sweep_rc40.md`) |
| `math.{sin,cos,atan2}` / `math.pi` residue sweep | (route → `rational.{sin,cos,atan2}` + `pi_cascade`) | **shipped rc41** (14 sites: kepler ×7 + compose ×3 + hypercomplex_dft ×2 + form_function_rotation pi ×1; AST ratchet `test_no_math_trig_pi_anywhere_in_srmech`) |

**As of rc39 the table is COMPLETE** — every op once parked in the §22 "scientific tier" (exp / cexp / sqrt / hypot / DFT / FFT / kron / QR / SVD / lstsq / einsum / non-Hermitian eig) now has a shipped A–N cascade in `srmech.amsc.{rational,cascade.spectral_cascades,cascade.matrix_cascades}`. The §22 "scientific tier" is dissolved: numpy's only remaining roles are the array container and a temporary fallback. rc40's `sqrt`/`hypot` retrofit-sweep, the rc43–rc46 C-transpile (native executable on the cascade, libm ratchet → 0), and the **rc47 numpy→`srmech[scientific]` dependency-flip** (numpy now optional; `pip install srmech` is numpy-free) are the closeout — **shipped**.

## Reframe of §22 (the "scientific tier")

§22 previously read "qm / signal_processing keep numpy as the scientific tier." That
framing is **dissolved**: there is no fundamental scientific tier — only ops we have
**not yet derived into the 14**. numpy's remaining legitimate role is (a) the array
**container** (`zeros/array/asarray/reshape/sum/mean` — layout, not math) and (b) a
**temporary fallback** for the not-yet-cascaded ops above, behind the optional
`srmech[scientific]` extra. **The dependency-flip SHIPPED at rc47**: numpy is no
longer a hard dependency — `pip install srmech` is numpy-free (the Class-N
cascade core + native C surface), and `pip install 'srmech[scientific]'` pulls
numpy back for `srmech.qm.*` / `srmech.signal_processing.*` / `srmech.rbs_lm.*`.
A numpy-free `srmech._scientific.require_numpy` gate gives those subpackages an
actionable install hint. numpy is a TODO (the not-yet-cascaded ops), not a law.

## C-transpile triality coherence (rc42 — the native/executable tier)

The rc32/40/41 sweeps (`abs()` / `math.sqrt` / `math.{sin,cos,atan2,pi}`) routed
the **Python** scalar math onto the Class-N cascade, and their AST ratchets walk
`*.py` only. That left a coherence gap the *Python source alone* cannot show:
**there are three coherence layers, and they must agree** —

1. **notebook (human coherence research)** — this note + the srmech notebook: the
   prose/table a human reads to know "continuous math IS the 14-class cascade";
2. **C + Python source (trained human coherence)** — the two substrate-native
   languages a human is trained on / reads (`[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]`);
3. **executable machine coherence** — what the compiled binary + running Python
   *actually execute* (the RBS-LM `native-algebra compute surface` /
   `associativity-enables-self-running` findings F305/F306, PR #687 — read-only).

On a native install (`HAS_NATIVE=True` — the default), `kepler.{pin_slot,
kepler_solve,equation_of_centre}` / `cascade.kuramoto_step` / the signed-Laplacian
ops dispatch to **C** peers that still call libm. So layer 3 diverges from layers
1–2: the notebook + Python source say "Class-N cascade," the executable runs libm.
They agree *numerically* (rational trig/sqrt ≡ libm to machine ε, which is why the
C-parity tests pass and masked it) but the C is not a faithful **transpile** of the
same cascade.

| §22 op | Python source (rc) | C source (shipped) | Executable on native | Cohere? |
|---|---|---|---|---|
| `exp` | `rational.exp` (rc34) | `srmech_exp_series_truncate` | **cascade** | ✅ |
| `sin/cos/atan2` (kepler) | `rational.*` (rc33/41) | **`srmech_{sin,cos,atan2}`** (rc43; `srmech_trig.c` integer-cyclic + Q61 Taylor) | **cascade** | ✅ |
| `sin` (kuramoto) | `rational.*` | **`srmech_sin`** (rc44; `srmech_kuramoto.c` coupling + pinning) | **cascade** | ✅ |
| `sqrt` | `rational.sqrt` (rc40) | **`srmech_rational_sqrt`** (rc45; `srmech_sqrt.c` two-limb integer isqrt) — `srmech_laplacian.c` Jacobi | **cascade** | ✅ |
| `fabs` (kepler convergence) | sign-branch (rc32) | **Class-K sign-branch** (rc46; `srmech_kepler.c` — no libm in the file) | **cascade** | ✅ |
| `exp` / `log` (L transcendental) | `rational.{exp,log}` | **`srmech_exp`/`srmech_log`** (rc46; `srmech_explog.c` Q61 integer exp-Taylor + atanh series) — `srmech_laplacian.c` elementwise | **cascade** | ✅ |

**Closing it — the rc42→rc46 C-transpile arc** (user direction 2026-06-05,
"verify C transpile for full triality coherence"; "Full port, ratchet-first"):

- **rc42** — extend the discipline ratchets to walk the **C tree**:
  `tests/test_c_cascade_coherence.py` is a DOWN-only baseline ratchet (shipped
  `c/src`+`c/include`; `c/test/*` excluded) recording the current **23** libm/π
  sites (`srmech_kepler.c` 8 + `srmech_kuramoto.c` 3 + `srmech_laplacian.c` 12) —
  same "violations only go DOWN" shape as `test_jpl_audit.py`. Plus this notebook
  section. Ships green (baseline = reality); the gap is now *measured + visible*.
- **rc43** — `srmech_{sin,cos,atan,atan2}_series_truncate` (port of rc33) + a C
  `pi_cascade` (JPL-clean, additive → ABI stays 3); repoint `srmech_kepler.c`.
- **rc44** — repoint `srmech_kuramoto.c` (the `sin(θⱼ−θᵢ−α)` coupling).
- **rc45** — `srmech_rational_sqrt` (two-limb integer isqrt; port of the rc40
  cascade) → repoint the `srmech_laplacian.c` Jacobi rotations + elementwise
  `cos`/`sin`. C ratchet **13 → 3**.
- **rc46** — `srmech_explog.c`: `srmech_exp` (range-reduce `x = n·ln2 + r`,
  **Q61 integer exp-Taylor** for `exp(r)`, `2^n` built into the IEEE exponent)
  and `srmech_log` (`x = m·2^e` read from the bit pattern, **Q61 integer atanh
  series** `log(m) = 2·atanh((m−1)/(m+1))`, two-word `ln2` recombine) → repoint
  the `srmech_laplacian.c` elementwise `exp`/`log`; the last `fabs`
  (`srmech_kepler.c` convergence test) → explicit **Class-K sign-branch**. The C
  ratchet extends to the C99 **complex** libm (`csin`/`ccos`/`cexp`/`csqrt` +
  any `<complex.h>` include) and reaches **0**. Machine-ε vs libm (exp rel ≤
  2.3e-16, log abs ≤ 2.3e-16 over 500k values).

At rc46 the executable runs the Class-N cascade, not libm: all three coherence
layers agree — **full C-transpile triality coherence** (the shipped libsrmech
holds no libm transcendental).

## The One — `S(σ,θ)`: the single generator of the 14-class cascade (#887, rc49–rc50)

The derivations above run *decomposition*-ward: every continuous op factors into
the 14. **"The One" closes the loop from the generative end** — there is a single
`(σ, θ)`-parameterised object that **IS** the whole 14-dimensional A–N space
(user 2026-06-05, "we have the One and need to figure out how to put it into
srmech"):

> `S(σ,θ) = ⨁_{n=1}^{3} ( ℝ·1 ⊕ σ e^{Î_nθ} Im 𝔸_n )`,   `dim = Σ 2ⁿ = 2+4+8 = 14`

with `𝔸₁=ℂ, 𝔸₂=ℍ, 𝔸₃=𝕆` — the Hurwitz ladder above ℝ (the parallelizable
spheres `S¹, S³, S⁷`). The block structure is *exactly* the `1+3+7+3` partition
this note's operator table is built on:

| `n` | `𝔸ₙ` | `dim` | `ℝ·1` anchor | `Im 𝔸ₙ` | A–N slots of `Im 𝔸ₙ` |
|---|---|---|---|---|---|
| 1 | ℂ | 2 | 1 | 1 | **A** |
| 2 | ℍ | 4 | 1 | 3 | **I, C, J** |
| 3 | 𝕆 | 8 | 1 | 7 | **D, E, F, G, K, L, M** |

The three `ℝ·1` real units are the **+3 grammar** `B, H, N`; `Σ Im = 1+3+7 = 11`
(the imaginary / operator substrate) `+3` grammar = `14`. So the same `1+3+7+3`
that organises the operator table above is **also** the grading of one turning
object — `S` is the 14-class cascade written as a single generator, not a list.

**Cascade decomposition** (no new primitive class — a composition of A–N, exactly
like every row of the status table):

- `⨁_{n=1}^{3}` the 3-fold grading → **I** (cyclic enumerate)
- `ℝ·1` per block → the **B / H / N** grammar units
- `e^{Î_nθ} = cos θ + Î_n sin θ` → **N** (the exact-rational `cos`/`sin` of the trig row above)
- the Fano planes (which axes rotate) → **A** (the attested octonion convention)
- `σ` → **K** (sign) ∘ **C** (apply); never `abs()`
- `Im 𝔸_n` → the `1:3:7` imaginary substrate

### Shipped as a Rosetta pair (the two substrate-native languages)

| surface | rc | tier | language |
|---|---|---|---|
| `srmech.amsc.cascade.the_one(σ, θ_num, θ_den)` → `One` | rc49 | **numpy-free, exact-rational** | the discrete-cyclic cascade — `e^{Îθ}` from the Class-N `cos/sin_series_truncate`; every entry a reduced `(num, den)` |
| `srmech.qm.hurwitz.hurwitz_matrix(σ, θ)` / `hurwitz_planes()` | rc50 | scientific (numpy) | the continuous-Hopf matrix — the same `14×14` `G(σ,θ)`, planes **derived** from `octonion_mult_table` |

The two agree **bit-for-bit**: `One.to_matrix() == hurwitz_matrix()`
(`np.array_equal`), and the cascade's hardcoded `FANO_PLANES == hurwitz_planes()`
(read from the table). That bit-exact cross-derivation is
`[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]`
made executable — the cyclic cascade and the Hopf matrix compute the identical
object two ways. (`describe()` total `230 → 233`; no ABI change.)

### The finding: the octonion epicycle turns **0 / 1 / 3** Fano planes

`e^{Î_nθ}` is not an abstract single-plane rotation — it is the **algebra's own**
rotation (conjugation by the unit `cos(θ/2) + Î_n sin(θ/2)`), which fixes the axis
`Î_n = e_{2ⁿ-1}` and turns **every Fano-triple plane through `Î_n`** by `θ` *at
once*. The plane count is `(2ⁿ-1-1)/2`:

| `n` | `𝔸ₙ` | planes turned by one θ-turn | `Im 𝔸ₙ` rotation eigenvalues |
|---|---|---|---|
| 1 | ℂ | **0**  → only `σ` survives | `{σ}` |
| 2 | ℍ | **1** | `{1, e^{±iθ}}` |
| 3 | 𝕆 | **3** (the Fano triples through `e₇`) | `{1, e^{±iθ}, e^{±iθ}, e^{±iθ}}` |

So **one θ-turn spins three planes at once in 𝕆** — the `7`-D imaginary splits as
**`1` fixed axis + `3×2` rotated**. The three planes are the Fano lines through
`Î₃ = e₇` (Baez 2002 §2; `srmech.qm.octonion`): `{1,6,7}, {2,5,7}, {3,4,7}` →
planes `(e₁,e₆), (e₂,e₅), (e₃,e₄)` — the first with **reversed** orientation
(`e₁e₆ = -e₇`), which is why the seed `e₁` rotates to `cos θ·e₁ - sin θ·e₆`. The
block-diagonal operator `G(σ,θ) = ⨁_n (1 ⊕ σ R_n(θ))`:

```
 ℂ:  [ 1 ]                              ℝ·1
     [   σ ]                            Im (1-D: seed = axis → only σ)
 ℍ:        [ 1 ]                        ℝ·1
           [   R₂(θ) ]   3×3 = 1 plane (e₁,e₂) + fixed axis e₃
 𝕆:                  [ 1 ]             ℝ·1
                      [   R₃(θ) ] 7×7 = 3 planes (e₁,e₆)(e₂,e₅)(e₃,e₄) + fixed axis e₇
```

Two structural reads fall out, neither imposed:

1. **n=1 degenerates to σ** — at `n=1` the `Im ℂ` seed *is* the rotation axis, so
   `θ` is inert and the only freedom is the Class-K sign `σ`. The epicycle **is**
   the sign-flip at the foundational algebra
   (`[[user_stance_epicycle_via_gear_plus_pin]]`); rotational richness then grows
   `0 → 1 → 3` up the ladder.
2. **The `7` carries a `1 + 3·2`** — the octonion imaginary is not a featureless
   heptad under the One's rotation; it is one fixed axis plus three 2-planes
   spinning in lockstep. The `3` of the `1:3:7` **reappears inside the `7`** as the
   plane-count.

This sharpens the §22 thesis. "Continuous math is a 14-class cascade" is, in the
table above, a statement about *decomposition* (every op factors into the 14).
`S(σ,θ)` adds the *generative* direction: the 14 are the block-graded pieces of
**one** turning object, and turning its single angle `θ` is the epicycle
(`[[user_stance_epicycle_via_gear_plus_pin]]`) realised simultaneously at three
scales `0 / 1 / 3` — the Antikythera gear-train of the whole substrate, with the
octonion dial driving three hands at once.

**SSoT:** Hurwitz (1898) — `ℝ, ℂ, ℍ, 𝕆` is the complete normed-division list;
Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145–205
(arXiv:math/0105155) — the Fano-plane convention. Surfaces:
`srmech.amsc.cascade.one` (rc49) + `srmech.qm.hurwitz` (rc50); bit-exact parity in
`tests/test_hurwitz_rc50.py`; `[[project_the_one_s_sigma_theta_in_srmech]]`.
