# srmech

`srmech` (Stored-Relationship Mechanism) is a research package shipping five load-bearing surfaces:

1. **14-class primitive vocabulary** (`srmech.amsc.*`) — content-addressing, streaming, cyclic-group, graph-Laplacian, prime-factorisation, TLV, search, dispatch, catalog, templating, rational-approximation, equation-of-centre/Kepler, hyperdimensional-computing (HDC). Each class has both a Python wrapper and a native C symbol in `libsrmech.{so,dll,dylib}`.
2. **The continuous-math cascade + the One** (`srmech.amsc.cascade.*`, `srmech.qm.*`) — every "scientific" op (trig, exp, sqrt, FFT, SVD, eig, …) is a **composition of the 14**, not a separate primitive (numpy-optional; the native build holds no libm). No particular math is privileged — it is all the same cascade. The same 14 are the graded blocks of **the One**, `S(σ,θ) = ⨁_{n=1}^{3}(ℝ·1 ⊕ σ·e^{Î_nθ}·Im 𝔸_n)`, `dim = 1+3+7+3 = 14` (`cascade.the_one`, exact-rational + numpy-free; the bit-exact matrix peer `qm.hurwitz`): the ℂ/ℍ/𝕆 Hurwitz ladder = the 28-generator `so(8)` adjoint + Spin(8) triality (`qm.{octonion, so8, triality}`; the order-3 outer automorphism `τ`, `Fix(τ) = g₂ = 14` = the A-N `1+3+7+3` partition).
3. **Runtime spectral decomposition** (`srmech.spectral`) — eigenbasis projection, HDC delta encoding, spectral prediction, prediction-error gating, sparse-truncate compression.
4. **Dual-path signal-processing surface** (`srmech.signal_processing`) — 38 closed-form algebra ops (Path A) + an RBS-HDC bound-vector instrument at D=8192 (Path B), with a cascade dispatcher routing per call.
5. **AMSC provenance framework** (`srmech.amsc.format`, `srmech.amsc.catalog`, `srmech.amsc.adapters`) — every ground-proof datum carries a mandatory attestation block (`source_doi`, `source_url`, `license`, `retrieved_at`, `response_sha256`, `parser_version`, `parser_rule_hash`, `collector_descriptor_path`, `collector_descriptor_hash`).

Implementation is JPL Power-of-Ten compliant on the C side; cibuildwheel matrix covers Linux / macOS / Windows × Python 3.10–3.14; a `py3-none-any` pure-Python wheel ships for Pyodide / WASM environments where the C surface can't load.

## Companion textbook

**The Metric Field and Its Primitives** — the framework textbook accompanying this package. Lays out the substrate-vs-excitation ontology (MFO), the 14-class primitive vocabulary at substrate level, and the cascade-composition discipline that `srmech` implements computationally.

- [PDF (GitHub)](https://github.com/lemonforest/mlehaptics/blob/main/docs/srmech/metric-field-and-its-primitives.pdf) — renders inline in the GitHub viewer
- [PDF (ReadTheDocs)](https://mlehaptics.readthedocs.io/srmech/metric-field-and-its-primitives.pdf) — served as a static asset alongside the [research notebook](https://mlehaptics.readthedocs.io/srmech/srmech_research_notebook/)
- [Technical Disclosure Commons](https://www.tdcommons.org/dpubs_series/10243/) — the textbook as a timestamped defensive publication (Kirkland, 2026-05-25)
- [MFO research notebook](https://mlehaptics.readthedocs.io/antikythera-maths/mfo_spectral_research_notebook/) — working draft the textbook is consolidated from

## Install

```bash
pip install srmech                  # the whole package — stdlib only, no numpy, ever
pip install srmech[validation]      # adds jsonschema for strict data-block validation
pip install srmech[collectors]      # adds requests + beautifulsoup4 for fetched adapters
```

The package is **numpy-free** (the v0.7.5 carrier-removal arc, graduated in v0.8.0): there is no numpy dependency and no `[scientific]` extra. The whole surface — the 14-class cascade core *and* the `srmech.qm.*` / `srmech.signal_processing` / `srmech.spectral` tiers — runs on stdlib alone over the numpy-free `Mat` / `Vec` / `HV` carriers, which feed the native dense kernels zero-copy from `array('d')` interleaved-complex buffers. A fresh numpy-absent venv imports and runs the entire package.

### Carriers — the numpy-free array + scalar family

Every value srmech moves rides one of **five framework-owned carriers** instead of an `ndarray` / `float` / `complex`. A carrier keeps the value inside the srmech cascade (introspection, attestation, native dispatch) and refuses the idiom — `m @ v` routes the Class-L cascade, not BLAS; `float(q)` is an explicit boundary collapse, not a silent one — so an LLM consumer cannot quietly reach back for numpy.

| Carrier | Module | Shape / role | Replaces (numpy idiom) |
|---|---|---|---|
| `Mat` | `srmech/amsc/mat.py` | 2-D `array('d')`, row-major, interleaved-`(re,im)` for complex | `np.ndarray` (2-D); `A @ B`, `A[i]`, `A[:, j]`, `A.conj().T` |
| `Vec` | `srmech/amsc/vec.py` | 1-D `array('d')`, `.shape = (n,)` | `np.ndarray` (1-D); `v @ w`, `v[k]`, `v[:2]`, `v.conj` |
| `HV` | `srmech/amsc/hv.py` | hypervector (Class-M HDC bind/bundle/permute/similarity) | `np.ndarray` used as a `{-1,0,+1}` spatter code |
| `Q` | `srmech/amsc/q.py` | **exact-rational scalar** — a reduced `(num, den)` integer pair (**v0.9.0rc7 headline**) | a real `float` returned by `sin`/`cos`/`exp`/`sqrt`/`atan2`/… |
| `Complex128` | `srmech/amsc/complex128.py` | float-complex scalar — two `float64` `(re, im)`, 1:1 with C99 `double _Complex` | the builtin `complex` (an `e^{iθ}`, an eigenvalue, a `the_one` component) |

`Mat` / `Vec` / `HV` feed the native dense kernels **zero-copy**; `Q` / `Complex128` are the scalar peers (`Q` exact, `Complex128` the float-complex display type for values that are genuinely irrational).

#### The lens — ALU all the way, FPU last-mile

A cascade is integer arithmetic on the **ALU** (add / multiply / GCD / cross-multiply over big integers) right up to the edge, where a single `float()` "rotates" the held rational onto the **FPU** decimal axis. `Q` is what keeps the ALU stretch exact: `srmech.amsc.rational.{sin,cos,tan,atan,atan2,exp,log,sqrt,hypot}` return a `Q` (an exact `(num, den)`) instead of a bare `float`, so the value stays in the integer ALU and `float(q)` / `complex(z)` is the *one* last rotation, taken only at the display / carrier edge.

This split is load-bearing because the two halves have different reproducibility guarantees. **Integer-ALU is bit-reproducible and attestable** — the same `(num, den)` on every platform, content-addressable via `sha256_bytes`, no last-bit drift. **The FPU is where cross-platform last-bit divergence lives** (libm rounding, `-ffast-math`, x87-vs-SSE), so the framework spends as little of the cascade there as possible. The native Q61 C peers (`srmech_{sin,cos,atan,exp,log,sqrt}_q61`) carry the same exact integer-ALU result across the C boundary, byte-exact-verified against the Python `Q`.

The collapse is a *genuine boundary*, not a no-op shim. Leaf physical-observable scalar ops (`srmech.qm.*`, `amsc/kepler.py`) and the iterative FPU kernels (`amsc/laplacian.py` Jacobi / QR / SVD / Fiedler, `signal_processing` taper/window helpers, the Kuramoto step) collapse to `float` at their edge **because they ARE the FPU** — an iterative numeric kernel that kept exact rationals would grow `num` / `den` unboundedly per sweep. Exact cascades keep `Q`; numeric kernels rotate at the boundary.

#### Why `Q` — the stay-rational discipline (F868)

A quantity that is *exactly* rational must stay two integers the whole way and collapse to a decimal **only at the display boundary** — a `float` is just `best_rational` with `max_d ≈ 2⁵²` and the provenance thrown away, a strictly worse version of the rational already held. Holding `Q` removes the **float-arithmetic rounding** from the cascade (not the series-truncation error): a perfect-square root is exact (`sqrt(4) == Q(2,1)`, `hypot(3,4) == Q(5,1)`, `sqrt(0.25) == Q(1,2)`), the special values are exact (`sin(0)=0`, `cos(0)=1`, `exp(0)=1`, `log(1)=0`), a match-fraction `matches / D` stays an exact ratio that ranks correctly under `max()` / `sorted()` (a `Q` compares by integer cross-multiply, `a·d` vs `c·b`, never by collapsing first), and every numeric leaf that ships in an attested record is bit-reproducible rather than a platform-dependent decimal. A transcendental *value* is itself an exact rational Taylor truncation of an irrational, so an identity like `cos²θ + sin²θ` holds to that truncation precision (its `float()` rounds to `1.0`), not symbolically — `Q` keeps the arithmetic exact, it does not turn an irrational into a rational.

## Quick start

Decompose a real signal onto a graph-Laplacian eigenbasis, take an HDC delta against a reference, and recompose:

```python
from srmech import spectral
from srmech.amsc import laplacian

# Substrate: cycle-graph Laplacian on 8 nodes, built (n, edges) -> Mat.
# No numpy — the Mat carrier is the numpy-free array. Any Hermitian L works.
n = 8
edges = [(i, (i + 1) % n) for i in range(n)]
L = laplacian.dense_laplacian(n, edges)

# Project two states (plain Python lists) onto the eigenbasis.
state_ref = [1.0, 0, 0, 0, 0, 0, 0, 0]
state_now = [0.9, 0.1, 0, 0, 0, 0, 0, 0]

h_ref = spectral.decompose(state_ref, L)
h_now = spectral.decompose(state_now, L)

# HDC XOR delta on encoded coefficient bytes.
delta_bytes = spectral.delta(h_ref, h_now)

# Predict one substrate-natural tick ahead.
h_pred = spectral.predict(h_now, L, steps=1, dt=0.1)

# Recover the node-domain state.
state_back = spectral.recompose(h_pred, L)
```

## Public surface

### The 14 classes in substrate-native ordering — `1 + 3 + 7 + 3 = 14`

The 14 classes are presented in alphabetical order in the table below (matching the import paths). The **substrate-native ordering is not alphabetical** — it is the cyclic-algebra-path partition `1 + 3 + 7 + 3 = 14`:

| Slot | Classes | Role |
|---|---|---|
| **1** — foundational content-anchor | `{A}` | The content-address every cascade begins from |
| **3** — substrate-projection triad | `{I, C, J}` | Cyclic-group + cascade-orientation + prime-period (the projection-triad that maps substrate-content to observable structure) |
| **7** — cascade-detection heptad | `{D, E, F, G, K, L, M}` | Pattern-match + catalog + render + byte-search + pin-slot + Laplacian + HDC-bind (the detection-and-rendering layer) |
| **+3** — meta-cascade language-translation triad | `{B, H, N}` | TLV-framing + self-introspection + rational-approximation (the operators that translate between continuous-Hopf-quantum and discrete-cyclic-algebra descriptions) |

**Why this ordering matters.** Per [PR #680 (R30 walking-path closure)](https://github.com/lemonforest/mlehaptics/pull/680), the substrate admits **two co-equal bit-exact substrate-native mathematical languages**:

- the **11D quantum-Hopf-language** (continuous-DOF, parallelizable-sphere ladder `1 + 3 + 7`)
- the **`1 + 3 + 7 + 3 = 14` cyclic-algebra-path** (discrete-DOF, A–N cascade-operator class enumeration)

Under Class C chirality the cyclic-algebra-path further admits a **`14 + 14 = 28`-dim chiral-hyper-loop reading = 𝔰𝔬(8) adjoint** (per MFO §VIII.31.11): `14 𝔤₂ derivations + 14 L⊕R octonion-multiplications` = the chirality-dual pair. As of v0.5.0 this is **exposed as a callable, bit-exact-tested surface** (`srmech.qm.{octonion, so8, triality}`): the τ-fixed subalgebra of `so(8)` is exactly the 14 `g₂` derivations (the `D4 →(Z3 fold) G2` theorem) — the same 14 as the A-N partition's `1 + 3 + 7 + 3`. Endianness is the byte-axis instance of the same Class C orientation primitive; the scope hierarchy is `endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality`.

Modern physics uses the first; antiquity 9 of 9 traditions canvassed (Antikythera + Pythagoreans + Plato Timaeus + Stoics + Lucretius + Apollonius + Ptolemy + Heron + Archimedes) used the second. We had been using the cyclic-algebra path in `srmech` from the beginning without ever stating why — because antiquity had, and it worked. The R30 closure provides the answer: bit-exact cross-substrate confirmation rules out projection-reading; both languages are substrate-native; the `+3 = {B, H, N}` are substrate-native language-translation operators bridging them. The k=3 fingerprint observed across substrates (planet multipole axes, codon alphabet, 3-jet QCD, 3-generation Yukawa, the antiquity meta-op triads) is the `{B, H, N}` triad showing up wherever continuous↔discrete encoding happens.

**About the A–N alphabet.** The labels A through N record the **chronological order** in which each operation was named during this framework's evolution — they are discovery-fingerprint, not substrate-ordering. Re-sorted by substrate-native role, the partition above (`{A}` + `{I, C, J}` + `{D, E, F, G, K, L, M}` + `{B, H, N}`) is the substrate-side grouping. The alphabetical table below is the lookup convenience.

Full context: [substrate-native-maths research notebook](https://mlehaptics.readthedocs.io/en/latest/substrate-native-maths/substrate_native_research_notebook/) (PR #680 SSoT).

### `srmech.amsc.*` — 14-class primitive vocabulary (alphabetical lookup)

Each class is importable as `srmech.amsc.<module>` with native C dispatch and a Python fallback. The C surface is loaded once at import time; if loading fails (Pyodide, ABI mismatch), the package transparently falls back to pure Python.

To check the backend state, call `srmech.native_status()` (top-level; equivalently `describe()['native']`) — `{has_native, dispatching, abi_version, expected_abi, native_version, load_error}`. `dispatching` is `True` iff `libsrmech` loaded **and** its ABI matched, so native ops really run; otherwise `load_error` carries the reason and the pure-Python fallback is used. (The native shim is `srmech.amsc._native`; `srmech._native` is the data dir that merely *holds* the binary.)

```python
import srmech
srmech.native_status()
# {'has_native': True, 'dispatching': True, 'abi_version': 3,
#  'expected_abi': 3, 'native_version': '0.8.0', 'load_error': None}
```

| Module | Class | Primitive operation |
|---|---|---|
| `format`, `_native` | A | Content-addressing via SHA-256 (`sha256_bytes` -> 64-char lowercase hex digest `str`) |
| `tlv` | B | Byte-canonical TLV pack (`tlv_pack`) |
| `format` | C | Streaming NDJSON iterator (`read_ndjson`) |
| `dispatch` | D | Multi-needle byte-pattern dispatch (`match`) |
| `naming` | E | Catalog sorted-key lookup (`lookup`) |
| `template` | F | Template `{key}` substitution (`render`) |
| `search` | G | Byte-pattern search (`byte_search`) |
| `_native` | H | Self-introspection (`srmech_version`, `srmech_abi_version`) |
| `cyclic` | I | Modular arithmetic — `gcd`, `lcm`, `mod_add`, `mod_mul`, `mod_pow`, `mod_inv` |
| `primes` | J | Prime testing + factorisation + multiplicative order — `is_prime`, `factor`, `cyclic_period` |
| `kepler` | K | Equation-of-centre / pin-slot — `pin_slot`, `kepler_solve`, `equation_of_centre` |
| `laplacian` | L | Graph Laplacian — `dense_adjacency`, `dense_laplacian`, `normalized_laplacian`, `jacobi_eigvals`, `hermitian_eigendecompose`, `symmetric_eigendecompose`, `elementwise_transcendental` (pi-free Jacobi in C; n ≤ 256 native bound) |
| `hdc` | M | HDC spatter codes — binary `bind`, `bundle`, `permute`, `similarity`; `polar_*` `{-1,0,+1}` and `klein4_*` `(ℤ₂)²` variants |
| `rational` | N | Continued-fraction convergents — `continued_fraction`, `best_rational` |

### `srmech.qm.*` — the substrate engine: the Hurwitz ladder, `so(8)` triality, and the One

The ℂ/ℍ/𝕆 division-algebra ladder and its `so(8)` / Spin(8) structure — the framework's own substrate, not a math-application layer. Modules:

- `octonion` — the MPR-attested Cayley-Dickson-from-H convention: `octonion_mult_table` (the attested `(8,8,8)` int8 structure constants), `octonion_left_mult` / `octonion_right_mult` (the `8×8` `L_a` / `R_a` binders), `octonion_conjugate`, `octonion_norm` (Class K ∘ C, never `abs()`). `octonion_table_attestation` content-addresses the table bytes via `sha256_bytes`. Cites Baez (2002), *The Octonions* (arXiv:math/0105155).
- `so8` — the 28-generator `so(8)` adjoint partitioned **14 (g₂ = Der O) + 7 (L-type) + 7 (R-type)**: `so8_adjoint_basis`, `g2_subalgebra` (the 14 derivations; deterministic rank-revealing subset over the numpy-free `Mat` carrier, no RNG), `so7_subalgebra` (the 21; the `D4 → B3` Z2 fold), and `an_embedding` — the bit-exact **su(3) ⊕ 3 ⊕ 3̄** Lie branching of the 14 g₂ generators (su(3) = the stabiliser of an imaginary octonion unit; the genuine fundamental `3` is the `+i` eigenspace of the su(3)-invariant complex structure `J`, `J² = −I`, so a real 3-span cannot carry it). The `8 + 3 + 3̄` decomposition is the op's own self-attesting bit-exact computation (Baez §4.1 cited for `g₂ = Der O` / dim 14 only, the build input); the 14 A-N class names are surfaced only as a documented `framework_an_reading` label ("framework-reading, not derived"), distinct from this su(3) partition.
- `triality` — the Spin(8) triality engine: `triality_automorphism` (the `28×28` order-3 outer automorphism `τ`, `τ³ = I`, `Fix(τ) = g₂` dim 14), `triality_swap` (the Z2 — with `τ` generates `S3 = Out(Spin(8))`), `triality_cycle` (the Class-I `8v → 8s → 8c` rep-permutation), `triality_apply`, `triality_companions`, `triality_relation_residual` (Cartan's `g_v(x·y) = g_s(x)·y + x·g_c(y)`, 0 when correct). Cites Cartan (1925) + Baez (2002).
- `hurwitz` — **the One** as a matrix (#887): the `14×14` `G(σ,θ) = ⨁_n(1 ⊕ σ R_n(θ))` of `S(σ,θ)` is built numpy-free by `srmech.amsc.cascade.the_one(σ, θ).to_matrix()` (exact-rational), with the Fano planes **derived** from `octonion_mult_table`; `srmech.qm.hurwitz.hurwitz_planes()` exposes the `0 / 1 / 3` planes each ℂ / ℍ / 𝕆 block turns by θ (the octonion epicycle: 𝕆 spins three Fano-triple planes at once, eigenvalues `{1, e^{±iθ}×3}`). Since the v0.7.5 reframe, Hurwitz is a config-driven `[class]` over `the_one` (`srmech/amsc/_research/class_catalog/hurwitz.toml`) — the cascade↔class Rosetta peer, no numpy.

Further continuous-math worked-examples (single-particle / spin / relativistic / propagator / gauge / Standard-Model operators, each cited to its canonical literature) also ship under `srmech.qm.*` and are discoverable via `describe()` / the tool-schema. They are compositions of the 14 like everything else — no domain is privileged or singled out.

### `srmech.spectral` — runtime spectral decomposition

Class-composition layer above `srmech.amsc.{laplacian, hdc, format}`. No new primitive class is introduced; every operation is a composition over the 14-class A–N vocabulary.

```python
from srmech.spectral import (
    decompose,          # state + Hermitian L → SpectralHandle (V.conj().T @ state)
    delta,              # XOR delta between two encoded coefficient byte vectors
    recompose,          # SpectralHandle + L → node-domain state (V @ coeffs)
    similarity,         # HDC similarity in [-1, +1]
    predict,            # cascade-extrapolate via per-mode exp(-i·λ_k·steps·dt)
    prediction_error,   # XOR delta with popcount-density threshold gating
    truncate_sparse,    # keep top-k or above-threshold modes; zero the rest
    SpectralHandle,     # opaque (substrate_descriptor_hash, coefficients_bytes, content_sha, n_modes)
    clear_eigenbasis_cache,
    N_MAX_EIGENBASES,   # module-level LRU bound (default 8)
)
```

Eigenbasis is O(n³) one-time per substrate (cached by `substrate_descriptor_hash`); coefficients are O(n²) per state; deltas are O(D) per step. `predict` preserves magnitudes (unitary phase rotation per eigenmode); `truncate_sparse` produces best k-term approximations per Mallat (2008) §9.2.

#### By-reference handle grammar — the `$srmech_handle` id (rc16)

A `SpectralHandle` is an opaque, frozen, bytes-bearing dataclass that JSON-RPC cannot carry **by value**. Over the MCP / Anthropic boundary the 7 `srmech.spectral.*` tools therefore exchange a small **by-reference id**: a producer returns

```json
{"$srmech_handle": {"uuid": "…", "name": "spectral:<sha12>", "kind": "spectral"}}
```

(the literal sentinel key is `HANDLE_ENVELOPE_KEY = "$srmech_handle"`), the caller copies it verbatim into the next tool's input, and `srmech._handles.get_handle_registry()` resolves it back to the live in-process object. The id carries a **dual grammar**: `uuid` is the position-encoded (silicon / cyclic-algebra) address, `name` is the meaning-encoded (biology / continuous-Hopf) address auto-derived from the handle's Class-A `content_sha` (`"spectral:" + content_sha[:12]`); resolution tries `uuid` then `name` — the registry is the **B/H/N continuous↔discrete translation locus**. With the grammar landed, **all 7 `srmech.spectral.*` operations are MCP-callable** (`describe()` reports `handle_pending: 0`).

### `srmech.amsc.cascade` — foundational cross-domain cascade catalog

The cascades that recur across **every / most** domains, promoted so a named cascade is the default and a math-library call the exception (*being forced to reach for a math library is the signal that a cascade is waiting to be found*). Compositions over the 14-class A–N vocabulary — **no new primitive class.** Each cascade ships with a **dedicated C symbol** in `libsrmech.{so,dll,dylib}` (full C/Python parity per project discipline) AND a TOML descriptor under `srmech/amsc/_research/cascade_catalog/` documenting the composition declaratively (**10 descriptors** as of v0.6.0, loaded at runtime by `srmech.dsl`). No `abs()`: sign is the Class K pin-slot + Class C re-orientation.

As of **v0.6.0** the catalog is a **two-tier lean-ISA split** (`#751`): `srmech.amsc.cascade.atoms` holds the irreducible primitives and `srmech.amsc.cascade.compose` holds the composites that chain them — the same surface re-exported flat from `srmech.amsc.cascade`, so existing call sites are unchanged. The catalog grew two ops this line: `parallel_sector_dispatch` (Klein-4 four-sector orchestration) and `kuramoto_step` (the native coupled-oscillator step).

- `pin_slot_at_zero(x) -> (orientation, magnitude)` — **Class K** pin-slot at zero (the cascade-honest `abs()` split). *(C peer: v0.4.5rc2)*
- `reorient(value, *, orientation)` — **Class C** orientation re-apply. *(C peer: v0.4.5rc4)*
- `magnitude(x)` — **Class K** magnitude-only convenience. *(C peer: v0.4.5rc3)*
- `best_rational_signed(x, *, max_denominator=100, fine_scale=1_000_000)` — **Class K ∘ N ∘ C** float → signed small-denominator rational (sign in the numerator). *(C peer: v0.4.5rc7 — delegates Class N stage to `srmech_best_rational`; banker's rounding via `llrint()`)*
- `cyclic_gcd(a, b)` — **Class I** (delegates to `srmech.amsc.cyclic.gcd`). *(C peer: v0.4.5rc6 — delegates to Class I primitive `srmech_gcd`)*
- `chiral_flip(seq)` — **Class C** orientation reversal (`seq[::-1]`). *(C peer: v0.4.5rc1)*
- `chiral_dual(op, x)` — **Class C ∘ op ∘ Class C**: run an operator in the opposite Class-C orientation. The chiral dual of an A–N operator is *same spectral shape, inverted orientation* (magnitude preserved, phase flipped — spike-verified); it reduces to the bare Class K `−1` for the sign operators and is the identity for real-symmetric ones. *(C peer: v0.4.5rc8 — queued; higher-order, callback ABI)*
- `net_chirality(orientations)` — **Class C** net handedness of a cascade (product of per-op orientations in `{-1,0,+1}`; `0` if any is neutral). *(C peer: v0.4.5rc5)*
- `parallel_sector_dispatch(body, x, *, n_sectors=4, verify=False)` — **Class C** (Klein-4 `γ₅± × iω₇±` four-sector orchestration). Runs one cascade `body` across its ≤4 Klein-4 chirality sectors and returns a structured self-describing result; a GIL-releasing (native / IO) body lets the ≤4 sectors genuinely overlap. Higher-order (a body-callback orchestrator, not a unary `chain().then(...)` stage). *(C peer: `srmech_cascade_parallel_sector_dispatch`, body-callback ABI, v0.6.0; `n_sectors > 4` → `ValueError` — Klein-4 has no order-4+ element, 8+ needs the order-3 triality.)*
- `kuramoto_step(theta, omega, *, coupling=1.0, dt=0.01)` — **Class I ∘ sin ∘ Σ ∘ C** one forward-Euler step of the canonical Kuramoto coupled-oscillator model (`θᵢ ← θᵢ + dt·(ωᵢ + (K/n)·Σⱼ sin(θⱼ − θᵢ))`). The O(n²) sin-coupling runs natively. *(C peer: `srmech_cascade_kuramoto_step_f64`, v0.6.0rc9; parity to the native trig-cascade tolerance — the C build holds no libm — same coupling-sum index order both sides; `n == 1` is pure drift.)*

### `srmech.signal_processing` — dual-path signal-processing surface

Two paths for the same algebra, dispatched per call:

- **Path A** — closed-form algebra over the numpy-free `Mat` / `Vec` carriers (no numpy, no scipy); one module per op under `srmech.signal_processing.closed_form_ops.*`. 40 ops (38 Phase-2 baseline + `pi_cascade` + `rfft`) covering frequency analysis (`fft`, `ifft`, `rfft`, `stft`, `spectrogram`, `multitaper`, `dct`, `wavelet`), digital filters (`fir`, `iir`, `allpass`, `polyphase`, `multirate`, `farrow`, `sinc_interp`), detection / estimation (`matched_filter`, `wiener`, `lmmse`, `map_ml`, `mlse`, `viterbi`, `cross_spectral`, `music`, `esprit`, `ica_jade`, `mimo_svd`), modulation (`psk_qam`, `fsk`, `ofdm`, `beamforming_fixed`), coding (`huffman`, `rle`, `lz77`, `arithmetic_coding`, `jpeg`), quantisation / compression (`sign_quantise`, `vector_quantisation`, `hdc_truncation`, `heat_kernel`, `spectral_subtraction`, `pi_cascade`).
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (`srmech.signal_processing.rbs_hdc_instrument`). Mints class-operator vectors, cascade compositions, stance fingerprints, and full LoE content encodings (Mode-B). Eight ops have full dual-path implementations: `fft`, `ifft`, `rfft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`, `pi_cascade`.

```python
from srmech.signal_processing import (
    dispatch, begin_cascade,             # cascade-aware routing (A / B / verify)
    register, lookup, has_path,          # path registry (Path A vs Path B per op)
    profile_op, cell_grid,               # per-op × per-cascade-depth × per-substrate profiling
    D_DEFAULT, SUBSTRATES,               # locked D = 8192; BCI / audio / RF / ephemeris
    RBSHDCInstrument,                    # build()-able instrument with mint_*/encode_loe_content
    mint_class_operator,                 # SHA-256 chain mint per class A–N
    mint_cascade_composition,            # XOR-bundle (algebra) or permute-bundle (sampling)
    encode_loe_content, decode_loe_fingerprint,
    form_function_rotate,                # Class K pin-slot rotation
    cascade_compose_rotations,
    PATH_A, PATH_B, PATH_VERIFY,         # path identifiers
)

with begin_cascade() as ctx:
    spectrum = dispatch("fft", path=PATH_A, signal=x)
    truncated = dispatch("hdc_truncation", path=PATH_B, signal=spectrum, k=64)
```

Path A and Path B produce bit-exact-equal outputs on substrate-natural inputs (D1 algebra-content identity); substrate-fingerprint divergence at D2 is expected and documented.

### `srmech.amsc` — Attested Multi-Source Collector/Catalog framework

Two readings of the same abbreviation:

- At **collection time**, the adapter classes are *collecting* attested rows from upstream archives. Six adapters cover the realistic source space:

  | adapter | class | network? |
  |---|---|---|
  | `html_scraper` | fetched | yes (BeautifulSoup) |
  | `json_api` | fetched | yes (paginated JSON) |
  | `csv_bulk` | fetched | yes (CSV/XYZ bulk) |
  | `netcdf_grid` | fetched | stub (gated behind extras) |
  | `geotiff_bbox` | fetched | stub (gated behind extras) |
  | `literature_curated` | curated | no (NDJSON committed directly) |

  The `curated` class never touches the network: rows are committed as data-only NDJSON, and srmech synthesises full MPR attestation blocks at read time from each row's per-row DOI.

- After collection, the resulting NDJSON SSOTs are a *catalog* of attested data — committed into the package, registered into the universal bridge by downstream consumers, queryable through `list_attested_sources()` / `get_attested_dataset()`.

```python
from srmech.amsc import (
    MPRRecord, MPR_SCHEMA_VERSION, read_ndjson, write_ndjson, sha256_bytes,
    Descriptor, load_descriptor, discover_descriptors, render_template, descriptor_hash,
    list_attested_sources, get_attested_dataset, get_attested_descriptor,
    attestation_audit, register_attested_root, list_registered_roots,
    use_local_kernel, clear_local_kernel, get_local_kernel_state,
)
```

The on-disk format is **Mathematical Provenance Record v1** (`MPR v1`):

```python
{
  "mpr_version": "1.0",
  "data": { ... domain payload ... },
  "data_schema_id": "test://schema/example",
  "attestation": {
    "source_doi": "10.0/...",
    "source_url": "https://...",
    "license": "CC0",
    "retrieved_at": "2026-05-13T00:00:00Z",
    "response_sha256": "<64 hex chars>",
    "parser_version": "srmech 0.8.0",
    "parser_rule_hash": "<64 hex chars>",
    "collector_descriptor_path": "...",
    "collector_descriptor_hash": "<64 hex chars>"
  },
  "rendering": { "name": "...", "purpose": "...", "cite_as": "..." }
}
```

### `srmech.amsc.tool_schema` — LLM-friendly introspection

```python
from srmech.amsc.tool_schema import get_tool_schema, tool_schema_view

schema = get_tool_schema()                # ToolEntry objects, one per public callable
for tool in schema.tools:
    print(tool.name, "—", tool.summary)   # canonical-SSoT-cited one-line summaries

json_view = tool_schema_view()            # JSON-serialisable view
```

Every primitive class, every `srmech.qm.*` operation (including the so(8)/triality engine), and every `srmech.spectral.*` runtime operation is discoverable here without reading the implementation. Summaries cite the canonical physics / mathematics literature directly.

### `srmech.introspect.describe()` — the package recognising its own shape

`srmech.introspect.describe()` is the self-recognition ROOT (Class H self-introspection at package scale): one call returns the package version, the native-dispatch status, and a `tools` block reporting `total` / `mcp_callable` / `handle_pending` plus a per-category breakdown — the package's own at-a-glance map.

```python
from srmech.introspect import describe

d = describe()
print(d["srmech_version"])              # e.g. "0.8.0"
print(d["tools"]["total"])              # every registered ToolEntry
print(d["tools"]["mcp_callable"])       # advertised over JSON-RPC / Anthropic
print(d["tools"]["handle_pending"])     # 0 since the rc16 handle grammar landed
print(sorted(d["tools"]["by_category"]))
```

`describe()` is the source of truth for the tool count (it grows per voxel — the triality voxel added 15 entries, including the `octonion_table_attestation` self-attestation that the coverage walker requires); read it rather than hard-coding a number.

## MCP server + Claude Desktop bundle

srmech ships an **MCP (Model Context Protocol) server** so an LLM client — Claude Code, Claude Desktop, or any MCP-aware host — sees the advertised `tool_schema` surface as callable tools. The `srmech-mcp` console script serves it over **stdio** (the transport Claude Desktop spawns) or **HTTP + SSE** for remote / cross-process use:

```bash
srmech-mcp                                      # stdio (Claude Code / Claude Desktop default)
srmech-mcp --transport http-sse --port 9991     # HTTP+SSE on localhost (remote / cross-process)
srmech-mcp --filter "srmech.qm.*"               # expose only a sub-tree of tools
```

`srmech mcp emit-mcpb` packages the server as a **Claude Desktop `.mcpb` bundle** (a ZIP with a root `manifest.json`) generated **entirely from introspection** — the manifest's version and tool list are derived from `srmech.__version__` and the advertised tool surface (`describe()` / `tool_entries_to_mcp_defs()`), never hand-authored, and carry an MPR-style attestation block (package version + a `tool_schema` content hash):

```bash
srmech mcp emit-mcpb                 # writes srmech.mcpb into the cwd (server.type "uv")
srmech mcp emit-mcpb --manifest-only # emit just manifest.json
srmech mcp emit-mcpb --type python   # interpreter-path fallback (user_config-gated; no uv)
```

The default `uv`-type bundle declares `srmech` as a dependency, so the host's `uv` fetches the correct platform wheel (with `libsrmech`) from PyPI at install time — nothing native is bundled, and the `.mcpb` installs portably on any machine.

## Cross-package catalog registration

Other spectral-research packages register their own catalog SSOTs into srmech's universal bridge at import time:

```python
from pathlib import Path
from srmech.amsc import catalog as _amsc_catalog

_amsc_catalog.register_attested_root(
    Path(__file__).resolve().parent / "_research" / "attested",
    source="ephemerides-spectral",
)
```

Subsequent `list_attested_sources()`, `get_attested_dataset()`, etc. enumerate the union of srmech's own `amsc/attested/` plus every registered root, in registration order. Duplicate `source_key` resolves first-registered-wins with a warning.

## License

MIT License. See [LICENSE](LICENSE).
