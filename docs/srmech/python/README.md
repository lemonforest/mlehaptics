# srmech

`srmech` (Stored-Relationship Mechanism) is a research package shipping six load-bearing surfaces:

1. **14-class primitive vocabulary** (`srmech.math.*`, with content-addressing in `srmech.amsc.format` and catalog lookup in `srmech.introspect.naming`) — content-addressing, streaming, cyclic-group, graph-Laplacian, prime-factorisation, TLV, search, dispatch, catalog, templating, rational-approximation, equation-of-centre/Kepler, hyperdimensional-computing (HDC). Each class has both a Python wrapper and a native C symbol in `libsrmech.{so,dll,dylib}`.
2. **The continuous-math cascade + the One** (`srmech.cascade.*`, `srmech.physics.qm.*`) — every "scientific" op (trig, exp, sqrt, FFT, SVD, eig, …) is a **composition of the 14**, not a separate primitive (numpy-free; the native build holds no libm). No particular math is privileged — it is all the same cascade. The same 14 are the graded blocks of **the One**, `S(σ,θ,w) = ⨁_{n=1}^{3}(ℝ·1 ⊕ σ·e^{Î_nθ}·Im 𝔸_n)`, `dim = 1+3+7+3 = 14` (`cascade.the_one(σ, θ, w)`, exact-rational + numpy-free; the bit-exact matrix peer `qm.hurwitz`) — `θ` the **epicycle** half-angle and the winding triad `w = (w_saros, w_metonic, w_callippic)` the **metacycle** grade (carrying the spinor double-cover sign `(−1)^Σw` + the divmod binary tower); the ℂ/ℍ/𝕆 Hurwitz ladder = the 28-generator `so(8)` adjoint + Spin(8) triality (`qm.{octonion, so8, triality}`; the order-3 outer automorphism `τ`, `Fix(τ) = g₂ = 14` = the A-N `1+3+7+3` partition).
3. **Runtime spectral decomposition** (`srmech.spectral`) — eigenbasis projection, HDC delta encoding, spectral prediction, prediction-error gating, sparse-truncate compression.
4. **Dual-path signal-processing surface** (`srmech.signal_processing`) — 41 closed-form algebra ops (Path A) + an RBS-HDC bound-vector instrument at D=8192 (Path B), with a cascade dispatcher routing per call.
5. **AMSC provenance framework** (`srmech.amsc.format`, `srmech.amsc.catalog`, `srmech.amsc.adapters`) — every ground-proof datum carries a mandatory attestation block (`source_doi`, `source_url`, `license`, `retrieved_at`, `response_sha256`, `parser_version`, `parser_rule_hash`, `collector_descriptor_path`, `collector_descriptor_hash`).
6. **The genome storage format** (`srmech.biology.genome`, `srmech.biology.plasmid`) — srmech's own self-describing on-disk store (wire format **v19**): O(1) append, a catalog derived from the body rather than a stored table of contents, centromere / diploid / chromatin / gene structure read back out of the bytes, and a two-stage extract-then-organize encode that makes adding a document incremental.

> **⚠️ BREAKING at v0.9.0rc287 — text is segmented into glyph clusters, not words.** `srmech.math.text.tokenize` and `DEFAULT_STOPLIST` are **removed** and replaced by `glyph_stream`. There is no shim and no compatibility flag. Every stored vocabulary, co-occurrence edge store and text-derived genome built before rc287 contains word tokens and must be **re-encoded** — the container format is unchanged, its contents are not. See [the glyph stream](#srmechmathtext--the-glyph-stream-uax-29) below before upgrading.

Implementation is JPL Power-of-Ten compliant on the C side; cibuildwheel matrix covers Linux / macOS / Windows × Python 3.10–3.14; a `py3-none-any` pure-Python wheel ships for Pyodide / WASM environments where the C surface can't load.

**Two implementations, one capability set.** srmech is a multi-implementation codebase: the **scripting-coherency** implementation (`python/srmech`) and the **compiled-coherency** implementation (`c/src`, `c/include`) are co-equal projections of the same capability into different execution regimes, related by projection rather than by rank — neither is the reference, and parity means *byte-identical results*, not similar behaviour (ADR-0009). The orchestration is compiled too, not only the compute kernels: the `srmech.bus` cross-process IPC server (req/rep **and** pub/sub broadcast, over AF_UNIX sockets / Windows named pipes, with an optional encrypted wire), the `srmech.dsl` operator-chain interpreter, the MCP server (JSON-RPC over stdio + HTTP/SSE) with in-C tool dispatch over the 655-entry tool registry, the CLI arg-parser, and the `make_class` config-driven `[class]` object model all ship as `libsrmech` symbols, so a host with **no Python present** can serve tools, run cascades, and speak the bus. The exact-algebra tail is C-native too: exact-ℚ `char_poly` / `eigvals` / `eigvec` / `eig` / `jordan_form` and integer-polynomial factoring run on srmech's own `srmech_bigint` (no Python-int oracle), and the Python-side `Q` / `Qi` exact scalars dispatch straight to it.

Coverage is **not** yet complete, and the gap is enumerated rather than asserted away — see [C-host coverage](#c-host-coverage--what-a-bare-c-host-cannot-run-today) for the ops a bare-C host cannot currently run, and the down-only ratchet that pins them.

## Companion textbook

**The Metric Field and Its Primitives** — the framework textbook accompanying this package. Lays out the substrate-vs-excitation ontology (MFO), the 14-class primitive vocabulary at substrate level, and the cascade-composition discipline that `srmech` implements computationally.

- [PDF (GitHub)](https://github.com/lemonforest/mlehaptics/blob/main/docs/srmech/metric-field-and-its-primitives.pdf) — renders inline in the GitHub viewer
- [PDF (ReadTheDocs)](https://mlehaptics.readthedocs.io/srmech/metric-field-and-its-primitives.pdf) — served as a static asset alongside the [research notebook](https://mlehaptics.readthedocs.io/srmech/srmech_research_notebook/)
- [Technical Disclosure Commons](https://www.tdcommons.org/dpubs_series/10243/) — the textbook as a timestamped defensive publication (Kirkland, 2026-05-25)
- [MFO research notebook](https://mlehaptics.readthedocs.io/antikythera-maths/mfo_spectral_research_notebook/) — working draft the textbook is consolidated from

## Install

```bash
pip install srmech                  # the whole package — no numpy, ever
pip install srmech[validation]      # adds jsonschema for strict data-block validation
pip install srmech[collectors]      # adds requests + beautifulsoup4 for fetched adapters
```

The package is **numpy-free** (the v0.7.5 carrier-removal arc, graduated in v0.8.0): there is no numpy dependency and no `[scientific]` extra. The whole surface — the 14-class cascade core *and* the `srmech.physics.qm.*` / `srmech.signal_processing` / `srmech.spectral` tiers — runs over the numpy-free `Mat` / `Vec` / `HV` carriers, which feed the native dense kernels zero-copy from `array('d')` interleaved-complex buffers. A fresh numpy-absent venv imports and runs the entire package.

**The one non-stdlib runtime dependency, stated exactly.** On **Python 3.10 only**, `pyproject.toml` declares `tomli>=2.0` (`python_version<'3.11'`) — a genuine third-party package. TOML parsing entered the stdlib as `tomllib` in 3.11, so on 3.11+ the install is stdlib-only; on 3.10 it is not. Seven modules carry the `try: import tomllib / except ImportError: import tomli` pair — `amsc/catalog.py`, `amsc/descriptor.py`, `introspect/tool_schema.py`, `dsl/_catalog.py`, `dsl/_class_catalog.py`, `dsl/_toml_chain.py`, `profile_loader.py`. This is worth naming rather than rounding off, because the C library **already ships its own TOML parser** (`c/src/srmech_toml.c`, 1,485 lines; `srmech_toml_parse` / `srmech_toml_table_get` exported, `srmech_toml_canonical` / `_type` / `_value` declared in the public header) for exactly the bare-C host ADR-0003 targets. The Python implementation does not read TOML through it. That is a self-hosting gap, not a packaging accident, and it is tracked as [#907](https://github.com/lemonforest/mlehaptics/issues/907).

### Carriers — the numpy-free array + scalar family

Every value srmech moves rides one of **six framework-owned carriers** instead of an `ndarray` / `float` / `complex`. A carrier keeps the value inside the srmech cascade (introspection, attestation, native dispatch) and refuses the idiom — `m @ v` routes the Class-L cascade, not BLAS; `float(q)` is an explicit boundary collapse, not a silent one — so an LLM consumer cannot quietly reach back for numpy.

| Carrier | Module | Shape / role | Replaces (numpy idiom) |
|---|---|---|---|
| `Mat` | `srmech/math/mat.py` | 2-D `array('d')`, row-major, interleaved-`(re,im)` for complex | `np.ndarray` (2-D); `A @ B`, `A[i]`, `A[:, j]`, `A.conj().T` |
| `Vec` | `srmech/math/vec.py` | 1-D `array('d')`, `.shape = (n,)` | `np.ndarray` (1-D); `v @ w`, `v[k]`, `v[:2]`, `v.conj` |
| `HV` | `srmech/math/hv.py` | hypervector (Class-M HDC bind/bundle/permute/similarity) | `np.ndarray` used as a `{-1,0,+1}` spatter code |
| `Q` | `srmech/math/q.py` | **exact-rational scalar** — a reduced `(num, den)` integer pair (**v0.9.0rc7 headline**) | a real `float` returned by `sin`/`cos`/`exp`/`sqrt`/`atan2`/… |
| `Complex128` | `srmech/math/complex128.py` | float-complex scalar — two `float64` `(re, im)`, 1:1 with C99 `double _Complex` | the builtin `complex` (an `e^{iθ}`, an eigenvalue, a `the_one` component) |
| `Qi` | `srmech/math/qi.py` | **exact-complex scalar** — a Gaussian rational `(re: Q, im: Q)`, the exact `numbers.Complex` over ℚ; its sign sector is a **Klein-4 quadrant** (**v0.9.0rc14**) | the builtin `complex` where the value is exactly rational |

`Mat` / `Vec` / `HV` feed the native dense kernels **zero-copy**; `Q` / `Complex128` / `Qi` are the scalar peers — `Q` exact-real, `Complex128` the float-complex display type for irrational values, `Qi` the **exact**-complex (`Qi = klein4 quadrant ⊗ |Qi|`, conjugation XOR-ing the imaginary bit).

#### The lens — ALU all the way, FPU last-mile

A cascade is integer arithmetic on the **ALU** (add / multiply / GCD / cross-multiply over big integers) right up to the edge, where a single `float()` "rotates" the held rational onto the **FPU** decimal axis. `Q` is what keeps the ALU stretch exact: `srmech.math.rational.{sin,cos,tan,atan,atan2,exp,log,sqrt,hypot}` return a `Q` (an exact `(num, den)`) instead of a bare `float`, so the value stays in the integer ALU and `float(q)` / `complex(z)` is the *one* last rotation, taken only at the display / carrier edge.

This split is load-bearing because the two halves have different reproducibility guarantees. **Integer-ALU is bit-reproducible and attestable** — the same `(num, den)` on every platform, content-addressable via `sha256_bytes`, no last-bit drift. **The FPU is where cross-platform last-bit divergence lives** (libm rounding, `-ffast-math`, x87-vs-SSE), so the framework spends as little of the cascade there as possible. The native Q61 C peers (`srmech_{sin,cos,atan,exp,log,sqrt}_q61`) carry the same exact integer-ALU result across the C boundary, byte-exact-verified against the Python `Q`. When the native library is loaded, `srmech.math.rational.{sin,cos,tan,atan,atan2,exp,log,sqrt}` **dispatch to those peers automatically** (the Python Q61 cascade computes the byte-identical value when it is not — a spy test asserts the live dispatch on every native CI cell). A **C-only host** reassembles the same exact rational from the peers plus the exported `SRMECH_Q61_ONE` / `SRMECH_Q61_LN2` / `SRMECH_Q61_HALF_PI` model constants — no Python required.

The collapse is a *genuine boundary*, not a no-op shim. Leaf physical-observable scalar ops (`srmech.physics.qm.*`, `math/kepler.py`) and the iterative FPU kernels (`math/laplacian.py` Jacobi / QR / SVD / Fiedler, `signal_processing` taper/window helpers, the Kuramoto step) collapse to `float` at their edge **because they ARE the FPU** — an iterative numeric kernel that kept exact rationals would grow `num` / `den` unboundedly per sweep. Exact cascades keep `Q`; numeric kernels rotate at the boundary.

#### Why `Q` — the stay-rational discipline (F868)

A quantity that is *exactly* rational must stay two integers the whole way and collapse to a decimal **only at the display boundary** — a `float` is just `best_rational` with `max_d ≈ 2⁵²` and the provenance thrown away, a strictly worse version of the rational already held. Holding `Q` removes the **float-arithmetic rounding** from the cascade (not the series-truncation error): a perfect-square root is exact (`sqrt(4) == Q(2,1)`, `hypot(3,4) == Q(5,1)`, `sqrt(0.25) == Q(1,2)`), the special values are exact (`sin(0)=0`, `cos(0)=1`, `exp(0)=1`, `log(1)=0`), a match-fraction `matches / D` stays an exact ratio that ranks correctly under `max()` / `sorted()` (a `Q` compares by integer cross-multiply, `a·d` vs `c·b`, never by collapsing first), and every numeric leaf that ships in an attested record is bit-reproducible rather than a platform-dependent decimal. A transcendental *value* is itself an exact rational Taylor truncation of an irrational, so an identity like `cos²θ + sin²θ` holds to that truncation precision (its `float()` rounds to `1.0`), not symbolically — `Q` keeps the arithmetic exact, it does not turn an irrational into a rational.

## Quick start

Decompose a real signal onto a graph-Laplacian eigenbasis, take an HDC delta against a reference, and recompose:

```python
from srmech import spectral
from srmech.math import laplacian

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

Under Class C chirality the cyclic-algebra-path further admits a **`14 + 14 = 28`-dim chiral-hyper-loop reading = 𝔰𝔬(8) adjoint** (per MFO §VIII.31.11): `14 𝔤₂ derivations + 14 L⊕R octonion-multiplications` = the chirality-dual pair. As of v0.5.0 this is **exposed as a callable, bit-exact-tested surface** (`srmech.physics.qm.{octonion, so8, triality}`): the τ-fixed subalgebra of `so(8)` is exactly the 14 `g₂` derivations (the `D4 →(Z3 fold) G2` theorem) — the same 14 as the A-N partition's `1 + 3 + 7 + 3`. Endianness is the byte-axis instance of the same Class C orientation primitive; the scope hierarchy is `endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality`.

Modern physics uses the first; antiquity 9 of 9 traditions canvassed (Antikythera + Pythagoreans + Plato Timaeus + Stoics + Lucretius + Apollonius + Ptolemy + Heron + Archimedes) used the second. We had been using the cyclic-algebra path in `srmech` from the beginning without ever stating why — because antiquity had, and it worked. The R30 closure provides the answer: bit-exact cross-substrate confirmation rules out projection-reading; both languages are substrate-native; the `+3 = {B, H, N}` are substrate-native language-translation operators bridging them. The k=3 fingerprint observed across substrates (planet multipole axes, codon alphabet, 3-jet QCD, 3-generation Yukawa, the antiquity meta-op triads) is the `{B, H, N}` triad showing up wherever continuous↔discrete encoding happens.

**About the A–N alphabet.** The labels A through N record the **chronological order** in which each operation was named during this framework's evolution — they are discovery-fingerprint, not substrate-ordering. Re-sorted by substrate-native role, the partition above (`{A}` + `{I, C, J}` + `{D, E, F, G, K, L, M}` + `{B, H, N}`) is the substrate-side grouping. The alphabetical table below is the lookup convenience.

Full context: [substrate-native-maths research notebook](https://mlehaptics.readthedocs.io/en/latest/substrate-native-maths/substrate_native_research_notebook/) (PR #680 SSoT).

### The same 14 in observer-frame ordering — `3 + 1 + 3 + 7`

The partition above is the **substrate / construction frame**: it builds real-first (the `{A}` anchor), then the imaginary grades, and closes the **winding** `{B, H, N}` last — the same order as the One's `S(σ,θ,w)`, `dim = 1 + 3 + 7 + 3` (which is why that construction is left unchanged). An **observer** reads the *same loop* from the other side — the operators that *make the projection* come first, and the content-anchor is the shadow the loop casts, not its origin:

| Slot | Classes | Observer role |
|---|---|---|
| **3** — projection-enablers | `{B, H, N}` | TLV-framing + self-introspection + rational-approximation — the continuous↔discrete language-translation operators; the observer's frame *begins* at the projection, not the substrate |
| **1** — time-shadow anchor | `{A}` | Content-addressing — identity/time, the 1-D real shadow (`ℝ·1`) the loop casts, read as the frame's pivot rather than its seed |
| **3** — substrate-projection triad | `{I, C, J}` | Cyclic-group + cascade-orientation + prime-period — the `Im ℍ` grade |
| **7** — cascade-detection heptad | `{D, E, F, G, K, L, M}` | Pattern-match + catalog + render + byte-search + pin-slot + Laplacian + HDC-bind — the `Im 𝕆` grade |

**Two frames of one loop — what is actually invariant.** `1 + 3 + 7 + 3` (substrate) and `3 + 1 + 3 + 7` (observer) are not two different objects; they are two places to **cut the same loop open**. Pick the cut at the real anchor and you build real-first, winding-last (substrate); pick it at the projection-enablers and you read winding-first, time-as-shadow (observer). Even `7 + 3 + 1 + 3` — cutting at the heptad — is the same loop from a third entry point. What no frame can move is the one adjacency **Cayley–Dickson nesting** forces: the **`3` (`Im ℍ`) always sits between the `1` (`ℂ/ℝ`) and the `7` (`Im 𝕆`)** — `… 1 · 3 · 7 …`. The frame is a choice of entry point; **the `3`-between-the-`1`-and-the-`7` is the fixed structure of the loop itself.**

### The 14-class primitive vocabulary — where each class lives (alphabetical lookup)

Under ADR-0010 the 14 A-N classes are homed by owning subpackage, not under one flat namespace. The **bulk is `srmech.math.*`** (`tlv`, `dispatch`, `template`, `search`, `cyclic`, `primes`, `kepler`, `laplacian`, `hdc`, `rational`); content-addressing + streaming are `srmech.amsc.format`; catalog lookup is `srmech.introspect.naming`; and self-introspection rides the native shim `srmech._native`. The **Home** column of the table below names each class's importable module (relative to `srmech.`). Both implementations realise the class; which one services a call inside a co-installed process is a **routing** decision, made once at import time. If `libsrmech` cannot be loaded (Pyodide, ABI mismatch), calls route to the Python implementation and results are unchanged.

To check which implementation is routing, call `srmech.native_status()` (top-level; equivalently `describe()['native']`) — `{has_native, dispatching, abi_version, expected_abi, native_version, load_error}`. `dispatching` is `True` iff `libsrmech` loaded **and** its ABI matched (**ABI 14** at this release — v11 removed `srmech_cd_zero_divisor_witness`, v12 gave `srmech_json_parse` / `srmech_toml_parse` a new `SRMECH_ERR_LIMIT` status, v13 gave nine exported genome entry points their caller-attestation params, v14 widened `srmech_mlse`'s `n_states` from `A^(L-1)` to `A^L` so the trellis state spans the whole tap window); otherwise `load_error` carries the reason and the Python implementation services the call. Routing status is not evidence of parity — that is what the ratchets below are for. (The native shim is `srmech._native` — the package that carries the ctypes bindings and holds `libsrmech.{so,dll,dylib}`.)

`SRMECH_ABI_VERSION` moves **13 → 14** at rc425 and is unchanged at this release, and it is worth saying why, because it is the kind of bump that is easy to mistake for bookkeeping. No signature changed shape; an existing parameter's *contract* did. `srmech_mlse`'s `n_states` meant `A^(L-1)` and now means `A^L`, because the trellis state has to span the whole tap window: `y_t = Σ_k taps[k]·s_{t−k}` reads all `L` symbols, and a state-emission Viterbi cannot express an emission that depends on a symbol its state does not hold. The older kernel held `L−1` and applied `taps[0]` and `taps[1]` to the *same* symbol, so it decoded a different channel and returned a wrong sequence **with no error signal** — measured against an exhaustive maximum-likelihood search, wrong on 4 of 9 test channels, returning a sequence of cost 13.0 where the transmitted one scored exactly 0.0. Both projections are fixed and now agree with brute force, and with each other over 60 randomly generated channels. A stale pre-rc425 `libsrmech` would still *load* into this Python, which now sizes its scratch arena for `A^L` states, so the pin is what rejects it.

```python
import srmech
srmech.native_status()
# {'has_native': True, 'dispatching': True, 'abi_version': 14,
#  'expected_abi': 14, 'native_version': '0.9.0rc428', 'load_error': None}
```

| Home (under `srmech.`) | Class | Primitive operation |
|---|---|---|
| `amsc.format`, `_native` | A | Content-addressing via SHA-256 (`sha256_bytes` -> 64-char lowercase hex digest `str`) |
| `math.tlv` | B | Byte-canonical TLV pack (`tlv_pack`) |
| `amsc.format` | C | Streaming NDJSON iterator (`read_ndjson`) |
| `math.dispatch` | D | Multi-needle byte-pattern dispatch (`match`) |
| `introspect.naming` | E | Catalog sorted-key lookup (`lookup`) |
| `math.template` | F | Template `{key}` substitution (`render`) |
| `math.search` | G | Byte-pattern search (`byte_search`) |
| `_native` | H | Self-introspection (`srmech_version`, `srmech_abi_version`) |
| `math.cyclic` | I | Modular arithmetic — `gcd`, `lcm`, `mod_add`, `mod_mul`, `mod_pow`, `mod_inv` |
| `math.primes` | J | Prime testing + factorisation + multiplicative order — `is_prime`, `factor`, `cyclic_period` |
| `math.kepler` | K | Equation-of-centre / pin-slot — `pin_slot`, `kepler_solve`, `equation_of_centre` |
| `math.laplacian` | L | Graph Laplacian — `dense_adjacency`, `dense_laplacian`, `normalized_laplacian`, `jacobi_eigvals`, `hermitian_eigendecompose`, `symmetric_eigendecompose`, `elementwise_transcendental` (pi-free Jacobi in C; n ≤ 256 native bound); relational read-outs `fiedler_vector` / `three_fold_eigvec_groups` (2- and 3-way communities), `spectral_spine` + `relational_structure` (structural centre + coherence λ₂), `magnetic_laplacian` / `signed_laplacian` (directed / signed), `cycle_holonomy` (the odd / chirality channel the Hermitian spectrum provably cannot carry); the **directed Class-L genome recovery family** (#1390) — `eulerian_path` / `eulerian_circuit` (Hierholzer walk reconstruction, `→ None` on an infeasible graph), `recover_check` (the op / operand / responsion / curvature round-trip integrity check, with `recover_check_structural` / `recover_check_spectral` for corpus scale), and `order_fingerprint` / `recover_check_order` (the octonion order faculty that catches a graph-preserving reorder); and `recursive_cut` (balanced out-of-core partition into bounded tomes) |
| `math.hdc` | M | HDC spatter codes — binary `bind`, `bundle`, `permute`, `similarity`; `polar_*` `{-1,0,+1}` and `klein4_*` `(ℤ₂)²` variants |
| `math.rational` | N | Continued-fraction convergents — `continued_fraction`, `best_rational` |

> **⚠️ Correctness advisory — `mat_eigvals` returned a wrong spectrum before v0.9.0rc285.** If you computed eigenvalues with `mat_eigvals` (or `cascade.matrix_cascades.eigvals`, which delegates to it) on any release before rc285, **recompute them**. The shifted-QR iteration ran on an unreduced matrix — the Householder reduction to Hessenberg form was **entirely absent** — and the Householder reflector divided by a `hypot` cascade whose inaccurate-nonzero returns broke the similarity property, so the iteration converged to numbers that were not the input's eigenvalues.
>
> The trigger is **vertex labelling, not hub dominance**, which is why it went unnoticed: it is not a pathological-input bug. A 4-node **path** graph relabelled `0-2-1-3` returned `[1, 1, 1, 3]` against a true spectrum of `[0, 2−√2, 2, 2+√2]`. Relabelling a graph does not change its spectrum, so any answer that moves under relabelling is wrong on its face — that invariant is now a ratchet (`tests/test_laplacian_kernel_invariant_rc285.py`, **65 tests**) applied across **all six** shipped eigensolvers (`mat_eigvals`, `jacobi_eigvals`, `hermitian_eigendecompose`, `symmetric_eigendecompose`, `mat_hermitian_eigendecompose`, `matrix_cascades.eigvals`), not only the one that was broken.

> **⚠️ Correctness advisory — `rational.hypot` (and `rational.sqrt` on a `Q` input) lost precision for small magnitudes before v0.9.0rc299.** If you computed a magnitude below roughly **1e-8** with `hypot`, with `laplacian.elementwise_hypot`, or with `sqrt` on an exact-`Q` argument, on any release before rc299, **recompute it**. The exact-rational √ floored onto a FIXED `2^-54` grid — **absolute** precision, not relative — so accuracy fell away linearly as the value shrank and vanished entirely below `2^-54 ≈ 5.55e-17`, where the result became exactly `0.0`.
>
> The exact zero is the easy half to notice. The dangerous half is **above** it, where the return value looks perfectly ordinary and is not: `hypot(1e-16, 0)` was **44% low**, `hypot(1e-13, 0)` 2.4e-4 low, `hypot(1e-8, 0)` 5.3e-10 low. Nothing in the value signals the error, which is why a "is it zero?" check was never sufficient. Since rc299 the grid is sized to the radicand and both ops are accurate to **~1 ulp at every magnitude** (verified against libm over 220 orders of magnitude). Values at or above 1 are byte-identical to previous releases, so nothing that was already correct moved.

### `srmech.physics.qm.*` — the substrate engine: the Hurwitz ladder, `so(8)` triality, and the One

The ℂ/ℍ/𝕆 division-algebra ladder and its `so(8)` / Spin(8) structure — the framework's own substrate, not a math-application layer. Modules:

- `octonion` — the MPR-attested Cayley-Dickson-from-H convention: `octonion_mult_table` (the attested `(8,8,8)` int8 structure constants), `octonion_left_mult` / `octonion_right_mult` (the `8×8` `L_a` / `R_a` binders), `octonion_conjugate`, `octonion_norm` (Class K ∘ C, never `abs()`). `octonion_table_attestation` content-addresses the table bytes via `sha256_bytes`. Cites Baez (2002), *The Octonions* (arXiv:math/0105155).
- `so8` — the 28-generator `so(8)` adjoint partitioned **14 (g₂ = Der O) + 7 (L-type) + 7 (R-type)**: `so8_adjoint_basis`, `g2_subalgebra` (the 14 derivations; deterministic rank-revealing subset over the numpy-free `Mat` carrier, no RNG), `so7_subalgebra` (the 21; the `D4 → B3` Z2 fold), and `an_embedding` — the bit-exact **su(3) ⊕ 3 ⊕ 3̄** Lie branching of the 14 g₂ generators (su(3) = the stabiliser of an imaginary octonion unit; the genuine fundamental `3` is the `+i` eigenspace of the su(3)-invariant complex structure `J`, `J² = −I`, so a real 3-span cannot carry it). The `8 + 3 + 3̄` decomposition is the op's own self-attesting bit-exact computation (Baez §4.1 cited for `g₂ = Der O` / dim 14 only, the build input); the 14 A-N class names are surfaced only as a documented `framework_an_reading` label ("framework-reading, not derived"), distinct from this su(3) partition.
- `triality` — the Spin(8) triality engine: `triality_automorphism` (the `28×28` order-3 outer automorphism `τ`, `τ³ = I`, `Fix(τ) = g₂` dim 14), `triality_swap` (the Z2 — with `τ` generates `S3 = Out(Spin(8))`), `triality_cycle` (the Class-I `8v → 8s → 8c` rep-permutation), `triality_apply`, `triality_companions`, `triality_relation_residual` (Cartan's `g_v(x·y) = g_s(x)·y + x·g_c(y)`, 0 when correct). Cites Cartan (1925) + Baez (2002).
- `hurwitz` — **the One** as a matrix (#887): the `14×14` `G(σ,θ) = ⨁_n(1 ⊕ σ R_n(θ))` — the θ-**epicycle** rotation part of the full **`the_one(σ, θ, w)`** object — is built numpy-free by `srmech.cascade.the_one(σ, θ_num, θ_den).to_matrix()` (exact-rational), with the Fano planes **derived** from `octonion_mult_table`; `srmech.physics.qm.hurwitz.hurwitz_planes()` exposes the `0 / 1 / 3` planes each ℂ / ℍ / 𝕆 block turns by θ (the octonion epicycle: 𝕆 spins three Fano-triple planes at once, eigenvalues `{1, e^{±iθ}×3}`). The **winding triad `w = (w_saros, w_metonic, w_callippic)`** (rc137; the Antikythera back-panel metacycle dials, default `(0,0,0)`) is the object's *metacycle* grade layered on that epicycle: it carries the **spinor double-cover sign `(−1)^Σw`** (`One.spinor_sign`) and the **divmod binary tower** (`One.winding_tower()`) — the winding that the flat `to_matrix()` epicycle realisation alone does not carry; a full-period-trivial winding reads back as flat. Since the v0.7.5 reframe, Hurwitz is a config-driven `[class]` over `the_one` (`srmech/cascade/catalogs/class_catalog/hurwitz.toml`) — the cascade↔class Rosetta peer, no numpy.

Further continuous-math worked-examples (single-particle / spin / relativistic / propagator / gauge / Standard-Model operators, each cited to its canonical literature) also ship under `srmech.physics.qm.*` and are discoverable via `describe()` / the tool-schema. They are compositions of the 14 like everything else — no domain is privileged or singled out.

### `srmech.spectral` — runtime spectral decomposition

Class-composition layer above `srmech.math.{laplacian, hdc}` + `srmech.amsc.format`. No new primitive class is introduced; every operation is a composition over the 14-class A–N vocabulary.

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

(the literal sentinel key is `HANDLE_ENVELOPE_KEY = "$srmech_handle"`), the caller copies it verbatim into the next tool's input, and `srmech._handles.get_handle_registry()` resolves it back to the live in-process object. The id carries a **dual grammar**: `uuid` is the position-encoded (silicon / cyclic-algebra) address, `name` is the meaning-encoded (biology / continuous-Hopf) address auto-derived from the handle's Class-A `content_sha` (`"spectral:" + content_sha[:12]`); resolution tries `uuid` then `name` — the registry is the **B/H/N continuous↔discrete translation locus**. With the grammar landed, **all 7 `srmech.spectral.*` operations are MCP-callable**.

The envelope generalises by its `kind` field, and v0.9.0rc414 uses it: `CDRegister` and `SedenionRegister` are **handle-shaped, not value-shaped** — each holds a `D`-wide hypervector store behind mutating methods (`write` / `carry` / `couple_working` / `navigate`) and inherits object identity, so what a consumer wants back is the live object, not a copy of its contents. They ride the same `$srmech_handle` id under `kind` `"cd-register"` / `"sedenion-register"`. Before rc414 both crossed as `"<...SedenionRegister object at 0x…>"` — a **non-deterministic** payload, because the class ships no `__repr__` and the default one carries a memory address, so two identical calls produced different bytes.

#### By-value carriers — the `$srmech_carrier` envelope (rc414)

The by-value peer of the same idea. An exact-algebra carrier (`Poly`, `BiPoly`, `TriPoly`, `QPoly`, `QBiPoly`, `EllMonomial`, `Theta`, `EllRatio`, `One`, `ChainSpec`, `RecoverableFold`) rides as

```json
{"$srmech_carrier": "BiPoly", "value": [[[1,1],[1,1]],[[-1,1]]]}
```

and is rebuilt structurally on the way back in. Before rc414 each of these fell through to `repr(obj)` and crossed as a metadata **string** — `"BiPoly(k_degree=1, exact-ℚ[n,k])"` — which is why `zeilberger`'s `certificate`, the entire point of that op, arrived as prose. The `value` payload is not new grammar: it is the same nested exact-ℚ shape the C carrier marshal (`SRMECH_CARRIER_POLY` / `_BIPOLY` / `_TRIPOLY` / `_QBIPOLY` / `_ELLRATIO`) has read since v0.9.0rc191, so both implementations already agree on the payload and the envelope only adds the tag that says which carrier it is.

Two consequences worth stating plainly, because both were silent-wrong-answer defects rather than missing features. A `QPoly`'s **`x_low`** (the Laurent tail offset) is now carried in both directions — the coefficient-list form dropped it, so a Laurent `QPoly` could not be expressed at all, in either direction, and came back as a different polynomial. And `the_one`'s **winding triad** now survives: rc408 made `w` a declared parameter, so from rc408 a caller could SET the winding and never READ it back, receiving a well-formed `One` at rest with no error.

### `srmech.cascade` — foundational cross-domain cascade catalog

The cascades that recur across **every / most** domains, promoted so a named cascade is the default and a math-library call the exception (*being forced to reach for a math library is the signal that a cascade is waiting to be found*). Compositions over the 14-class A–N vocabulary — **no new primitive class.** Each cascade in this catalog ships with a **dedicated C symbol** in `libsrmech.{so,dll,dylib}` AND a TOML descriptor under `srmech/cascade/catalogs/cascade_catalog/` documenting the composition declaratively (**20 descriptors**, loaded at runtime by `srmech.dsl`; this read "15" until rc364 — re-counted at the move). No `abs()`: sign is the Class K pin-slot + Class C re-orientation.

As of **v0.6.0** the catalog is a **two-tier lean-ISA split** (`#751`): `srmech.cascade.atoms` holds the irreducible primitives and `srmech.cascade.compose` holds the composites that chain them — the same surface re-exported flat from `srmech.cascade`, so existing call sites are unchanged. The catalog grew two ops this line: `parallel_sector_dispatch` (Klein-4 four-sector orchestration) and `kuramoto_step` (the native coupled-oscillator step).

- `pin_slot_at_zero(x) -> (orientation, magnitude)` — **Class K** pin-slot at zero (the cascade-honest `abs()` split). *(C peer: v0.4.5rc2)*
- `reorient(value, *, orientation)` — **Class C** orientation re-apply. *(C peer: v0.4.5rc4)*
- `magnitude(x)` — **Class K** magnitude-only convenience. *(C peer: v0.4.5rc3)*
- `best_rational_signed(x, *, max_denominator=100, fine_scale=1_000_000)` — **Class K ∘ N ∘ C** float → signed small-denominator rational (sign in the numerator). *(C peer: v0.4.5rc7 — delegates Class N stage to `srmech_best_rational`; banker's rounding via `llrint()`)*
- `cyclic_gcd(a, b)` — **Class I** (delegates to `srmech.math.cyclic.gcd`). *(C peer: v0.4.5rc6 — delegates to Class I primitive `srmech_gcd`)*
- `chiral_flip(seq)` — **Class C** orientation reversal (`seq[::-1]`). *(C peer: v0.4.5rc1)*
- `chiral_dual(op, x)` — **Class C ∘ op ∘ Class C**: run an operator in the opposite Class-C orientation. The chiral dual of an A–N operator is *same spectral shape, inverted orientation* (magnitude preserved, phase flipped — spike-verified); it reduces to the bare Class K `−1` for the sign operators and is the identity for real-symmetric ones. *(C: `srmech_cascade_chiral_dual_f64`, v0.4.5rc8; higher-order, callback ABI)*
- `net_chirality(orientations)` — **Class C** net handedness of a cascade (product of per-op orientations in `{-1,0,+1}`; `0` if any is neutral). *(C peer: v0.4.5rc5)*
- `parallel_sector_dispatch(body, x, *, n_sectors=4, verify=False)` — **Class C** (Klein-4 `γ₅± × iω₇±` four-sector orchestration). Runs one cascade `body` across its ≤4 Klein-4 chirality sectors and returns a structured self-describing result; a GIL-releasing (native / IO) body lets the ≤4 sectors genuinely overlap. Higher-order (a body-callback orchestrator, not a unary `chain().then(...)` stage). *(C peer: `srmech_cascade_parallel_sector_dispatch`, body-callback ABI, v0.6.0; `n_sectors > 4` → `ValueError` — Klein-4 has no order-4+ element, 8+ needs the order-3 triality.)*
- `kuramoto_step(theta, omega, *, coupling=1.0, dt=0.01)` — **Class I ∘ sin ∘ Σ ∘ C** one forward-Euler step of the canonical Kuramoto coupled-oscillator model (`θᵢ ← θᵢ + dt·(ωᵢ + (K/n)·Σⱼ sin(θⱼ − θᵢ))`). The O(n²) sin-coupling runs natively. *(C peer: `srmech_cascade_kuramoto_step_f64`, v0.6.0rc9; parity to the native trig-cascade tolerance — the C build holds no libm — same coupling-sum index order both sides; `n == 1` is pure drift.)*

### `srmech.signal_processing` — dual-path signal-processing surface

Two paths for the same algebra, dispatched per call:

- **Path A** — closed-form algebra over the numpy-free `Mat` / `Vec` carriers (no numpy, no scipy); one module per op under `srmech.signal_processing.closed_form_ops.*`. 41 ops (38 Phase-2 baseline + `ifft` + `pi_cascade` + `rfft`) covering frequency analysis (`fft`, `ifft`, `rfft`, `stft`, `spectrogram`, `multitaper`, `dct`, `wavelet`), digital filters (`fir`, `iir`, `allpass`, `polyphase`, `multirate`, `farrow`, `sinc_interp`), detection / estimation (`matched_filter`, `wiener`, `lmmse`, `map_ml`, `mlse`, `viterbi`, `cross_spectral`, `music`, `esprit`, `ica_jade`, `mimo_svd`), modulation (`psk_qam`, `fsk`, `ofdm`, `beamforming_fixed`), coding (`huffman`, `rle`, `lz77`, `arithmetic_coding`, `jpeg`), quantisation / compression (`sign_quantise`, `vector_quantisation`, `hdc_truncation`, `heat_kernel`, `spectral_subtraction`, `pi_cascade`).
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (`srmech.signal_processing.rbs_hdc_instrument`). Mints class-operator vectors, cascade compositions, stance fingerprints, and full LoE content encodings (Mode-B). Eight ops have full dual-path implementations: `fft`, `ifft`, `rfft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`, `pi_cascade`.

```python
from srmech.signal_processing import (
    dispatch, begin_cascade,             # cascade-aware routing (A / B / verify)
    register, lookup, has_path,          # path registry (Path A vs Path B per op)
    record_profile, cell_grid,           # per-op × per-cascade-depth × per-substrate profiling
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

**`dispatch` routes the ops that HAVE two paths — the other 33 are called by direct import.** `dispatch` is a path-*router*, not a name-resolver: `registered_ops()` returns the 13 names it can route, and asking it for a single-path op raises `UnknownOperationError`. That is the correct answer to a routing question, not a gap — but it does mean the calling convention above is not the one for most of the 41. Import those directly; each module exposes exactly one callable named `op`:

```python
from srmech.signal_processing.closed_form_ops.wavelet import op as wavelet
from srmech.signal_processing.closed_form_ops.dct import op as dct
coeffs = dct(x, dct_type=2)
```

Path A and Path B produce bit-exact-equal outputs on substrate-natural inputs (D1 algebra-content identity); substrate-fingerprint divergence at D2 is expected and documented.

> ⚠️ **`music_doa` is an acronym, not the art form.** `srmech.signal_processing.music_doa` is **MU**ltiple **SI**gnal **C**lassification — the subspace direction-of-arrival estimator — and has nothing to do with the `srmech.music` package below. Through v0.9.0rc423 it shipped as `closed_form_ops.music`, one dotted path from `srmech.music`; v0.9.0rc424 renamed it and registered it so the name carries its own disambiguation.

### `srmech.music` — acoustic spectra and pitch relations

Two lanes that never meet, kept apart on purpose.

**The acoustic lane** asks what a single sounding object *is*. `spectrum_tier` tags a spectrum's exactness — Tier 1 exact rational, Tier 2 exact algebraic irrational, Tier 3 no exact carrier (**declared**, never inferred). `commensurability_verdict` then decides `"harmonic"` / `"inharmonic"` / `"open"` by **rational rank**, not by finding a period — which is the point, because Class-I `gcd`/`lcm` structurally *cannot* return `"inharmonic"` (a finite set of rational ratios always has an lcm) and Class-N `best_rational` is worse than silent: it does not approximate an inharmonic spectrum, it **converts** it into a harmonic one. `common_period` returns a period only for a spectrum that earned the verdict, and raises otherwise — that refusal is what makes the silent conversion unreachable. Four closed-form constructors span all three tiers: `bell_partials`, `equal_temperament_partials`, `stiff_string_partials`, `membrane_partials`.

**The relational lane** (new in v0.9.0rc424) asks how two pitches stand to *one another*. It reads no spectrum.

```python
from srmech.music import just_limit, comma_of_chain, tempers_out, prime_form

just_limit((3, 2))["monzo"]                     # {'2': -1, '3': 1}  — a just fifth IS 2**-1 * 3
comma_of_chain((3, 2), 12, (2, 1))["comma"]     # '531441/524288'    — the Pythagorean comma, DERIVED
tempers_out((81, 80), 12)["tempers_out"]        # True  — why a piano has one key for D# and Eb
prime_form([0, 4, 7], "rahn")                   # (0, 3, 7)
```

The two lanes **disagree, and that is the content**. A chain of just fifths never closes in the frequency lane — `(3/2)**n == 2**m` has no solution for `n > 0`, because the prime supports `{3}` and `{2}` are disjoint — while the same chain always closes in the modular lane, because a generator coprime to the modulus generates the whole cycle. The exact non-vanishing residue between them **is** a comma, and `comma_of_chain` derives it rather than looking it up.

`prime_form` and `normal_order` **require** a `convention` argument and have no default. Forte (1973) packs normal order from the left, Rahn (1980) from the right, and they give different prime forms for exactly **6 of the 208 set classes** — 5-20, 6-Z29, 6-31, 7-Z18, 7-20, 8-26 — measured here by enumerating every set class of cardinality 2..10 rather than by copying a list. (Note 7-Z18: the count usually quoted is *five*, following Straus, which omits it.) An unnamed `prime_form` would silently pick a side in a live scholarly disagreement.

Everything in both lanes is exact ℚ or exact ℤ: no `float`, no stdlib `math`/`fractions`/`decimal`, no numpy, and no `abs()` — sign is a Class-K pin-slot with Class-C re-application.

### `srmech.math.text` — the glyph stream (UAX #29)

The front door for text: it turns a string into the units that everything downstream counts, and those units are what a co-occurrence graph, and therefore a text-derived genome, is built out of. **As of v0.9.0rc287 the unit is the extended grapheme cluster — the glyph — not the word.**

#### ⚠️ BREAKING at v0.9.0rc287 — `tokenize` is removed, `glyph_stream` replaces it

`tokenize` and `DEFAULT_STOPLIST` are gone. There is **no shim**, no `legacy_mode=`, and no parallel old path. What a reader upgrading needs, stated first:

| | Before rc287 | rc287 onward |
|---|---|---|
| Public op | `tokenize(text)` | `glyph_stream(text, *, unicode_normalize=True)` |
| Unit | word (Latin-shaped) | UAX #29 extended grapheme cluster |
| Casefold | always | never — the op does not decide case for you |
| Length floor | 2 codepoints | none |
| Stoplist | 146 English function words, by default, in every language | none |
| Stored data | — | **every** pre-rc287 vocabulary / edge store / text-built genome must be re-encoded |
| Format / ABI | — | `GENOME_FORMAT_VERSION` unchanged at **15** at that rc (later advanced 15 → 19); **ABI 6 → 7** |

The container is fine; its contents are not. `GENOME_FORMAT_VERSION` does not move because nothing about the byte layout changed — what changed is which strings went into it. ABI moves because the C surface lost an exported symbol (`srmech_text_tokenize`) and gained two (`srmech_text_glyph_stream`, `srmech_text_default_gb_table`), and a **removal always bumps**.

#### Why the word was the wrong unit

The word decision carried four Latin-shaped assumptions — a 2-codepoint length floor, a universal casefold, a 146-word English stoplist, and an apostrophe special case. Each mis-handled most of the world's writing systems, and the failure was not cosmetic: in scriptio-continua scripts it collapsed whole clauses into single "words", leaving roughly **89%** of Chinese / Japanese / Thai types as singletons (English: ~20%). A co-occurrence graph over an 89%-singleton vocabulary carries almost no association mass. It also deleted content outright — `tokenize("中 国")` returned `[]`, both single-codepoint words lost to the length floor.

A grapheme cluster is what a reader perceives as one character. It is the only unit well-defined in **every** script, which is exactly why it replaces the word here. Real output from this tree:

```python
from srmech.math.text import glyph_stream

glyph_stream("语言是人类交流的工具")
# ['语', '言', '是', '人', '类', '交', '流', '的', '工', '具']   → 10 glyphs, not 1 "word"

glyph_stream("中 国")
# ['中', ' ', '国']            # before rc287: []  — the content was deleted outright

glyph_stream("’okina")
# ['’', 'o', 'k', 'i', 'n', 'a']   # the Hawaiian okina survives; it used to vanish

len(glyph_stream("👨‍👩‍👧‍👦"))   # 1  — one family, 7 codepoints, GB11 (emoji ZWJ)
len(glyph_stream("🇻🇺"))       # 1  — one flag, 2 codepoints, GB12/13
len(glyph_stream("क्षि"))       # 1  — one Devanagari cluster, GB9c (Indic conjunct)
len(glyph_stream("1️⃣"))        # 1  — one keycap
```

Each of those last four is **one thing a human sees** and **one element of the stream**. That agreement is the whole point of the unit.

#### The break table is vendored and attested, not derived at runtime

Python's `unicodedata` does not expose the Grapheme_Cluster_Break property, so the table is vendored: **683 ranges / 6,147 bytes**, from **UCD 16.0.0**, carried as `GB_TABLE_BLOB` in `srmech/math/_unicode_gb_tables.py` with a `GB_TABLE_SHA256` content-address and an MPR attestation block (`tests/test_unicode_gb_tables_attested.py`). It is a **caller-provided input** to the C op (`srmech_text_default_gb_table` hands out the default), not a compiled-in constant. Hangul LV/LVT are deliberately absent — they are recovered by the UAX #29 §3 syllable algebra rather than stored.

| Property | Value |
|---|---|
| UCD version | 16.0.0 |
| Ranges | 683 |
| Blob size | 6,147 bytes |
| Rules implemented | GB1–GB999, incl. GB9c (Indic conjuncts, Unicode 15.1) and GB11 (emoji ZWJ) |
| Conformance | **1093/1093** on Unicode's `GraphemeBreakTest.txt`, in **both** implementations |

The 1093/1093 bar is held by the scripting-coherency body and the compiled-coherency peer independently — the C peer gets no allowance for being the fast one.

**Why the bar is the whole suite and not a sample**, which is the more interesting point: a best-effort `unicodedata`-only derivation without the vendored table scores 954/1093 (87.28%) — and that aggregate is exactly the kind of number that hides the problem. The same approximation is **perfectly correct** for Latin, Greek, Cyrillic, Arabic, Hebrew, CJK, Korean and Hawaiian, while being **19.2% wrong for Burmese, 9.2% for Bengali and 8.0% for Devanagari**. An 87% score reads as "mostly fine"; what it actually describes is a segmenter that is flawless on the scripts that barely need clustering and broken on the ones that do. A partial conformance target would conceal that the same way, so the target is the whole suite, exactly. The suite is also what found the third data dependency: omitting InCB scores 1086/1093, and those 7 cases are the only signal that GB9c exists at all.

#### What consumes the stream

`cooccurrence_edges(docs, *, window=2, vocab=None, vocab_size=None, directed=False)` and `cooccurrence_topk(docs, *, window=2, k=20, …)` build the weighted graph the Class-L Laplacian surface and the genome encoders read. They take documents that are already glyph streams, so the unit change propagates through every text-derived store — which is why re-encoding is mandatory rather than advisory.

### `srmech.biology.genome` / `srmech.biology.plasmid` — the genome storage format

srmech's own on-disk store for coupled-turn content: a **self-describing** byte format (`turns.bin` + a head-only `manifest.json`) whose structure is read back out of the bytes rather than out of a sidecar table of contents. **Wire format v19.** The vocabulary is biology's because the structures are the ones biology already names — this is form-matching, not a claim about biochemistry.

A genome is a sequence of **chromosomes**; each chromosome opens with a cap marker and carries interior caps. Every marker is one byte, distinct, and a reader that does not know a marker skips it by its self-described length — which is why v19 reads pre-v19 bodies unchanged.

| Marker | Byte | Role |
|---|---|---|
| CHROM | `0x43` | opens a plain chromosome; carries the label inline |
| diploid telomere | `0x44` | opens a **diploid** chromosome (two homologous copies) |
| kernel telomere | `0x6B` | opens a graph-kernel chromosome |
| active telomere | `0x74` | opens a chromosome carrying a division count |
| centromere | `0x58` | **interior**; the p:q arm split + the strand's global orientation |
| chromatin | `0x48` | **interior**; the epigenetic access level for a region |
| gene | `0x47` | a named gene; carries copy number in its padding |
| graded / regulatory / boolean / threshold gene | `0x64` / `0x67` / `0x62` / `0x77` | gene promoters under a cell-state gate |

#### ⚠️ BREAKING at v0.9.0rc271 — the chromosome-type vocabulary follows the field

The derived per-chromosome `cap_kind` and census type **values** were renamed to the names bacterial genomics already uses. `"diploid"` is unchanged.

| Was (srmech-coined) | Now (canonical, field-supplied) | What it is |
|---|---|---|
| `"stick"` | **`"plasmid"`** | Tier-1: mobile, append-only, no centromere |
| `"minted"` | **`"nuclear"`** | Tier-2: stable, centromere-anchored |

This changes **strings, not bytes** — `cap_kind` is derived on read, never stored, so there is **no on-disk migration and no format or ABI bump**; a pre-rc271 genome censuses identically except for those two labels. What moves is the value in `genome_catalog` / `genome_census` / `genome_registry` (including the census `types` dict **keys**) and `mint_plan`'s `shape`.

**To keep the old names, opt in to the value-alias layer** — a pure presentation transform over the canonical output. Storage, the C implementation and the format stay canonical; the alias never touches disk:

```python
from srmech.biology import genome as G
G.set_type_aliases({"plasmid": "stick", "nuclear": "minted"})   # or any vocabulary
G.clear_type_aliases()                                          # back to canonical
G.load_type_aliases_toml(path)                                  # a [genome.type_aliases] table
```

#### The tooling reads the shape

`genome()` picks each chromosome's shape from the kernel it is given, rather than being told: a plasmid-scale kernel (≤ 4 leaves) stays Tier-1, a chromosome-scale kernel (≥ 5 leaves) is minted with an interior centromere. `plasmid()` is the all-Tier-1 builder; `mint()` is an alias of `genome()`; `mint_plan()` reports the picks without building anything.

```python
import tempfile, pathlib
from srmech.biology import genome as G
from srmech.cascade.one import the_one
from srmech.math.hdc import klein4_expand, klein4_from_one

# rc290: the coupling is DERIVED from (sigma, theta, terms) — no magic seed.
coupling = klein4_from_one(the_one(1, 1, 4), 64)
lv = lambda n, b: [klein4_expand(64, b + i) for i in range(n)]

strand = G.genome({"small": lv(3, 10), "large": lv(8, 40)}, coupling)
path = pathlib.Path(tempfile.mkdtemp()) / "demo.genome"
G.genome_save(strand, path, coupling)

census = G.genome_census(path, coupling=coupling)
print(census["types"])      # {'plasmid': 1, 'nuclear': 1, 'diploid': 0}
print(census["topology"])   # nuclear-like
print([(c["label"], c["type"]) for c in census["chromosomes"]])
# [('small', 'plasmid'), ('large', 'nuclear')]
```

`genome_census(path)` rolls a genome up; `genome_registry(root)` censuses a whole directory of them (which genome is the nucleus, which is an organelle). `topology` is a structural **integer** read — `nuclear-like` / `organelle-like` / `plasmid/prokaryote-like` / `empty` — with no float anywhere.

#### The op families

| Family | Ops | What it does |
|---|---|---|
| build | `genome` · `plasmid` · `mint` · `mint_plan` · `chromosome` · `telomere` | build a strand; the tooling picks each shape |
| mint post-pack | `mint_strand` | promote an **already-packed** strand to Tier-2 by splicing a centromere at the p:q split — no re-mint from leaves |
| anchor | `centromere` · `centromere_of` | the global orientation, stored as a majority-decoded repeat array |
| redundancy | `diploid` · `recover_diploid` | two homologous copies + the centromere as which-template mark; heals an erasure on **either** homolog |
| access | `condense` · `decondense` · `chromatin_of` · `accessible` | the epigenetic gate — which regions express, **computed** per cell state |
| multiplicity | `amplify` · `copy_number_of` | a gene's copy number as an exact integer count |
| splice | `integrate` | splice a Tier-1 provirus into a host genome, with a compatibility gate |
| graph | `graph_to_kernel` · `kernel_to_graph` · `genome_partition` · `genome_from_graph` | a relational graph in and out of a genome, partitioned by its own structure |
| persist | `genome_save` · `genome_load` · `genome_append` · `genome_window` · `genome_catalog` | O(1) append; the catalog is derived, never a stored TOC |
| census | `genome_census` · `genome_registry` | roll up a genome / a directory of genomes |
| two-stage encode | `plasmid.plasmid_extract` · `plasmid.section_counts` · `plasmid.conserved_core` · `plasmid.genome_integrate_plasmids` · `plasmid.add_plasmid` | extract-then-organize, incremental |

#### The attestation of record — omitting `attestation=` PRESERVES it (v0.9.0rc418)

A genome's `manifest.json` carries a full MPR attestation block, and until v0.9.0rc418 **every mutating op re-minted srmech's default over it**. A genome saved under a real DOI and a real licence came back `10.0/srmech.genome.persistence` / `CC0` after one `genome_append` — and the false block validated as a well-formed MPR exactly as cleanly as the true one, which is why no test caught it. The same substitution ran through `genome_append_kernel`, `genome_remove`, `genome_replace`, `genome_import`, `genome_pack`, `upgrade_v15_to_v16`, a re-`genome_save`, and — worst, because it is the **distribution unit** — `genome_export`, so a chromosome exported from a `GPL-3.0-only` parent shipped as `CC0` and left the machine that way.

srmech now has the concept it was missing: **the attestation of record**.

```python
G.genome_save(strand, path, coupling, attestation={
    "source_doi": "10.5281/zenodo.1234567",
    "source_url": "https://example.org/corpus",
    "license": "GPL-3.0-only",
    "retrieved_at": "2026-08-08T00:00:00Z",
})
G.genome_append(path, "chr2", leaves, coupling)     # ← carried forward, not re-minted
```

Three rules, and the split between them is the whole design:

| | behaviour |
|---|---|
| **Four SOURCE fields** — `source_doi` · `source_url` · `license` · `retrieved_at` | **INHERIT** across every mutation. They are facts about where the corpus came from, and a mutation does not change the source. |
| **`response_sha256` + the four encoder-identity fields** | **ALWAYS re-synthesised.** `response_sha256` IS the body hash; carrying it forward would freeze a stale digest into an attested genome and every downstream re-verification would fail against bytes that are perfectly intact — a worse defect than the one being fixed. |
| **An explicit `attestation=` that DISAGREES with a non-default block on disk** | `GenomeAttestationConflict` (a `ValueError` subclass). Overwriting an attestation of record is allowed; it is never *silent*. Pass the values already on disk to confirm, or omit the argument to keep them. |

`genome_export` stamps the parent's block onto the `.chr`; `genome_import` and `genome_pack` into a **fresh** destination inherit from the bundle, because at that moment the bundle *is* the genome. `plasmid_extract(..., attestation=...)` is where provenance enters the two-stage pipeline — once, at the seed; every later section append and the stage-2 promotion are in-place and carry it forward for free.

**The compiled projection gained the same capability, not a workaround.** Ten C entry points took no attestation at all before this release, which is why `genome_save(attestation=…)` had to branch to the scripting path — an ADR-0009 capability gap. `SRMECH_ABI_VERSION` moved **12 → 13** at that release (nine existing exported signatures changed; the second ordinary-kind bump after v9). A bare-C host now saves, appends and exports with a caller attestation and gets byte-identical manifests. `GENOME_FORMAT_VERSION` stays **19** — the attestation block is free-form MPR content, gains no key, and `turns.bin` is untouched.

#### Copy number is a multiplicity, not N strands

`amplify` records **how many copies** on a gene's cap, in what was NUL padding. `n == 1` is byte-identical to a plain gene, so only `n >= 2` spends the field, and a gene written before the field existed reads back as `1`. The count is transparent to every existing reader.

```python
chrom = G.chromosome(genes=[("resA", lv(2, 10)), ("resB", lv(3, 20))],
                     coupling=coupling, label="plasmidR")
amp = G.amplify(chrom, "resA", 12)
print(G.copy_number_of(amp, "resA"), G.copy_number_of(amp, "resB"))  # 12 1
print(len(amp) == len(chrom))                                        # True
print(G.amplify(chrom, "resA", 1) == chrom)                          # True
```

#### Chromatin — accessibility is computed, not stored

A **constitutive** chromatin cap carries a static level. A **facultative** cap carries a *gate*, so the same genome under two different cell states has two different accessible open-sets. `cell_state` is an integer bitmask; the level is an exact `(num, den)` rational.

```python
XIST = 1 << 1
chrX  = G.chromosome(lv(6, 60), coupling=coupling, label="chrX")
gated = G.condense(chrX, coupling=coupling, state={"activator": XIST})  # facultative
print(G.accessible(chrX,  0))       # (1, 1)  — no cap: euchromatin by default
print(G.accessible(gated, 0))       # (0, 1)  — gate does not fire: silenced
print(G.accessible(gated, XIST))    # (1, 1)  — gate fires: open

const = G.condense(chrX, coupling=coupling, state="condensed")          # constitutive
print(G.accessible(const, 0), G.accessible(const, XIST))  # (0, 1) (0, 1)
```

A graded chromatin level composes **multiplicatively** with a graded promoter, as exact rationals. On the demand-load path a condensed region is skipped having touched only its chromatin cap — fewer bytes read, not more.

#### Progress and graceful abort (added at ABI 6)

The long encode ops were blind and un-cancellable. `progress=` is an in-process callback taking `{struct_size, phase, done, total}` — exact integers, never a float or a division. Returning truthy **cancels**, and every cancel yields a *valid* shorter result rather than a half-written one. It is available on `genome` / `mint` / `mint_strand` / `genome_partition` / `genome_from_graph`, `laplacian.recursive_cut` / `fiedler_sparse_file`, and the `plasmid.*` pipeline.

```python
seen = []
G.genome({"a": lv(3, 1), "b": lv(3, 5), "c": lv(3, 9)}, one,
         progress=lambda ev: seen.append((ev["phase"], ev["done"], ev["total"])))
print(seen)   # [(3, 0, 3), (3, 1, 3), (3, 2, 3)]     phase 3 = MINTING

partial = G.genome({"a": lv(3, 1), "b": lv(3, 5), "c": lv(3, 9)}, one,
                   progress=lambda ev: ev["done"] >= 1)
print(len(G.partition(partial, one)))   # 1 — complete chromosomes only, never a partial one
```

This is a C-native primitive, not a Python driver loop: the heartbeat is the compiled loop's own (a versioned `srmech_progress_ev_t` + a `srmech_progress_tick_cb_t` returning nonzero to cancel, plus a `SRMECH_CANCELLED` status). Adding that callback typedef is what took **ABI 5 → 6**. `progress=` is deliberately **not** an MCP wire parameter — a callable cannot cross JSON-RPC — so it adds no tool.

#### Two-stage encode — extract, then organize

Encoding a corpus as one monolithic partition does not scale. The two-stage split makes adding a document an **append plus a bounded re-mint** instead of a global re-solve.

1. **EXTRACT** — `plasmid_extract(docs, store, the_one)` turns each document into one Tier-1 plasmid section appended to a single store, and returns `section_count`, a **free** integer accumulator built during the append pass.
2. **ORGANIZE** — `conserved_core` derives the conservation threshold `k`, then `genome_integrate_plasmids` promotes the induced core to a nuclear chromosome and merges the retained sections. `add_plasmid` does the same for one document at a time; D incremental calls are byte-identical to one batch call.

`section_counts(store)` re-derives the accumulator from the sections themselves — the SSoT check, and the resume path when you did not just build the store. Pass the accumulator through on the hot path; the re-derivation is the verification path, not the default.

**The read path pays its own bill (v0.9.0rc282), and the part that does not is named.** Scanning a store used to re-open `turns.bin` once per region — about **2 opens per section** in the scripting-coherency implementation, so the cost grew with the store. Both implementations now hold **one** handle for the whole scan and thread it through: the Python side through a `_body_handle` contextmanager, the compiled side through a held `FILE*` and a new platform read-at trio. Catalog derivation also stopped slurping the whole body into RAM — it streams, bounded by **the largest single region** rather than the file, the bound being one region and not one block because the SHA-256 op has no streaming API.

Two honest limits belong with that claim. First, the ratchet that pins it (`tests/test_genome_read_io_ratchet_rc282.py`, `CEIL_BODY_OPENS_PER_SCAN = 2`, verified across a 25/50/100/200-section sweep with an independent assertion that 8× more sections must not raise the count *at all*) exercises the **scripting-coherency** implementation only — it deliberately disables native dispatch, because the compiled projection's open shape is a separate C-side concern that does not yet have an equivalent assertion. Second, the bound is on **RAM**, not on bytes read: `gene_express_plan`'s **call-level** I/O is *not* bounded the way its docstrings once advertised, and cannot be while the chromosome table is derived by scanning — ADR-0003 forbids storing it. Call-level bytes-read is **≥ the whole body**; only the per-region gate reads are bounded. The docstring now says exactly that, and closing the gap needs a format change this release does not make.

**`k` is derived or honestly declined — never manufactured.** `conserved_core` measures the antimode of the section-count histogram. On a distribution with no clean gap it reports `k_source="declined"` with an empty core rather than inventing a threshold; an explicit `k` is reported as `"policy"`, a caller's stated choice, never as measured:

```python
from srmech.biology import plasmid as P

planted = {i: 1 for i in range(20)}                # 20 periphery ids, seen once
planted.update({100 + i: 12 for i in range(4)})    #  4 core ids, seen 12×
d = P.conserved_core(planted, k="auto")
print(d["k_source"], d["k"], sorted(d["core"]))
# derived 2 [100, 101, 102, 103]

p = P.conserved_core(planted, k=8)
print(p["k_source"], p["k"])       # policy 8
```

Measured on the full simplewiki corpus, stage 1 extracted **240,881 sections in 11.1 min** where the monolithic builder ran 8+ hours without finishing. The same corpus's conservation curve is heavy-tailed with no clean gap, so `conserved_core` **declines** on it — a scale-free distribution has no characteristic scale and therefore no natural antimode. That is a reported finding, not a defect, and the decline path is tested as a first-class outcome.

### C-host coverage — what a bare-C host cannot run today

ADR-0003 commits srmech to running standalone on a C host with no Python present; ADR-0009 frames the two implementations as co-equal projections of one capability set. Neither is a claim that coverage is currently complete. It is not, and the shortfall is **enumerated in the test suite rather than described in prose**.

`tests/test_rosetta_transitive_standalone.py` ratchets the **wire-format surface** — the ops that lay out srmech's own on-disk byte structures (`srmech.biology.genome`, `srmech.biology.plasmid`, and the out-of-core `laplacian.recursive_cut`), where "a bare-C host cannot run this" is load-bearing rather than theoretical. Each such op must either name a **whole-op C entry point** — machine-checked twice over, that the symbol is declared in `c/include/srmech.h` **and** that the op actually reaches it through its dispatch glue — or sit on a documented allowlist. Reaching a C *primitive* through a private helper is deliberately **not** sufficient; that is the weaker property the ratchet exists to reject.

The allowlist is pinned by `CEIL_WIRE_GLUE_GAPS`, and it is **down-only**: a test fails if the list grows. An entry leaves it only by landing a C entry point. As of v0.9.0rc334 that count is **0** — the **enumerated genome wire-glue gap list is empty**: every wire-format `composition_of_c` op on the `srmech.biology.genome` / `srmech.biology.plasmid` surface (plus the out-of-core `laplacian.recursive_cut`) now names a machine-checked whole-op C entry point a bare-C host reaches through its dispatch glue. This is the concrete ADR-0003 "genome must exist fully in C" closure for the wire-glue surface.

The count walked steadily down as each op landed its own C entry point, never by an adjacent op landing one. **11 → 10** at v0.9.0rc284 (the out-of-core `laplacian.recursive_cut` driver earned `srmech_laplacian_recursive_cut`); **10 → 9** at rc321 and **9 → 8** at rc327 (the two graph builders `genome.genome_partition` and `genome.genome_from_graph` earned `srmech_genome_graph_partition` / `srmech_genome_from_graph` — the exact-integer participation + antimode + per-node classify + per-group `graph_to_kernel` → `mint_strand` loop + strand assembly, all in C, closing the §100 G-series ladder); **8 → 6** at rc329 (the two §2-G7 leaf ops `genome.active_telomere` and `genome.mint_plan` earned `srmech_genome_active_telomere` / `srmech_genome_mint_plan` — the op⊗operand Hayflick cap packer, factored out of the tick with no daughter-minting, and the read-only shape-plan loop, `encode_shape` + the content-address orientation per kernel); **6 → 4** at rc332 (the chromatin `genome.condense` and `genome.decondense` pair earned `srmech_genome_condense` / `srmech_genome_decondense` — the shared `label → chromatin-range` find + `region` resolution to the cap-splice insert index, and the inverse per-block keep-mask; the cap bytes were already compiled, so this lifted the Python-only `_chrom_range` + region resolution into C); **4 → 1** at rc333 (the **genes family** — `genome.genes`, `genome.genome_genes` and `genome.genome_genes_expressed` — earned `srmech_genome_genes` / `srmech_genome_genome_genes` / `srmech_genome_genes_expressed`, the per-gene `(label, leaves)` boundary-preserving read: the in-memory split, the on-disk page-region + split, and the demand-load plan-walk + region-page + `gene_express` collect, all in C); and **1 → 0** at rc334 (the last and hardest op, `plasmid.add_plasmid`, earned `srmech_genome_add_plasmid` — the incremental CONSERVE (merge the section-count accumulator + `srmech_genome_conserved_core`) + ORGANIZE (page every section off disk, decode + harvest the induced core subgraph, sum the per-`(u,v)` multiplicities in canonical order, pack it, then MINT the core + FOLD the retained plasmids), so a bare-C host runs one incremental add end-to-end). `recursive_cut` was the shared dead-end of the two graph builders, so closing it **unblocked** them without closing them — unblocking is not closing, and each still needed a C surface of its own; the ratchet is what keeps that distinction honest.

**The ratchet at 0 is a scoped claim, not a blanket one.** It is the concrete statement that the *enumerated wire-glue surface* is fully C-reachable — coverage is still **enumerated in the tests, not asserted in prose**. Two other surfaces remain legitimately projection-specific and are **not** wire-glue gaps: the `make_class` `One.flat` / `One.scalar` bignum-leaf defers are a separate (config-DSL) surface, and the `host_glue` / `dev_tooling` buckets are projection-specific by design (an MCP server or an editable-install dispatcher has no on-disk byte structure to lay out in C). The wire-glue ratchet does not speak to those, and does not claim the entire capability surface is compiled.

One further coverage fact stated plainly rather than left to be discovered: `srmech_genome_section_counts` is **caller-arena** (rc306 / #899 — the count table, region window and catalog arena are carved from a caller `ws` buffer sized by `srmech_genome_section_counts_arena_bytes`), so it carries no compiled-in corpus cap and is reentrant on disjoint `ws` buffers; a short `ws` is a clean, typed decline (the Python implementation services the call), which is never the same thing as lacking the capability.

### `srmech.amsc` — Attested Multi-Source Collector/Catalog framework

Two readings of the same abbreviation:

- At **collection time**, the adapter classes are *collecting* attested rows from upstream archives. Eight adapters cover the realistic source space:

  | adapter | class | network? |
  |---|---|---|
  | `html_scraper` | fetched | yes (BeautifulSoup) |
  | `json_api` | fetched | yes (paginated JSON) |
  | `csv_bulk` | fetched | yes (CSV/XYZ bulk) |
  | `netcdf_grid` | fetched | stub (gated behind extras) |
  | `geotiff_bbox` | fetched | stub (gated behind extras) |
  | `literature_curated` | curated | no (data-only NDJSON committed directly) |
  | `mpr_committed` | curated | no (whole MPR envelopes committed directly) |
  | `substrate_parameterization` | configured | no (parameter set, not rows) |

  The `curated` class never touches the network, and its two members split on **where the attestation lives** — a distinction v0.9.0rc418 (`#T1108`) had to introduce because getting it wrong is not cosmetic. A `literature_curated` catalog commits **data-only** rows and srmech **synthesises** the full MPR attestation at read time from each row's per-row DOI; an `mpr_committed` catalog commits **whole MPR v1 envelopes** whose attestation was minted when the upstream response was captured, and srmech reads it back **verbatim**. Synthesis is legitimate only where nothing true was committed. Pointing the synthesising reader at an envelope makes it manufacture a `response_sha256` over the row's own JSON on top of one that already hashes the real upstream response — the read-side mirror of the write-side substitution `#T1108` closes.

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
    "parser_version": "srmech 0.9.0",
    "parser_rule_hash": "<64 hex chars>",
    "collector_descriptor_path": "...",
    "collector_descriptor_hash": "<64 hex chars>"
  },
  "rendering": { "name": "...", "purpose": "...", "cite_as": "..." }
}
```

### `srmech.introspect.tool_schema` — LLM-friendly introspection

```python
from srmech.introspect.tool_schema import get_tool_schema, tool_schema_view

schema = get_tool_schema()                # ToolEntry objects, one per public callable
for tool in schema.tools:
    print(tool.name, "—", tool.summary)   # canonical-SSoT-cited one-line summaries

json_view = tool_schema_view()            # JSON-serialisable view
```

Every primitive class, every `srmech.physics.qm.*` operation (including the so(8)/triality engine), and every `srmech.spectral.*` runtime operation is discoverable here without reading the implementation. Summaries cite the canonical physics / mathematics literature directly.

### `srmech.introspect.describe()` — the package recognising its own shape

`srmech.introspect.describe()` is the self-recognition ROOT (Class H self-introspection at package scale): one call returns the package version, the native-dispatch status, and a `tools` block reporting `total` / `mcp_callable` / `handle_pending` plus a per-category breakdown — the package's own at-a-glance map.

```python
from srmech.introspect import describe

d = describe()
print(d["srmech_version"])              # e.g. "0.9.0"
print(d["tools"]["total"])              # every registered ToolEntry
print(d["tools"]["mcp_callable"])       # advertised over JSON-RPC / Anthropic
print(d["tools"]["handle_pending"])     # entries NOT advertised over MCP; each carries a reason
print(sorted(d["tools"]["by_category"]))
```

`describe()` is the source of truth for the tool count (it grows per voxel — the triality voxel added 15 entries, including the `octonion_table_attestation` self-attestation that the coverage walker requires); read it rather than hard-coding a number.

## MCP server + Claude Desktop bundle

srmech ships an **MCP (Model Context Protocol) server** so an LLM client — Claude Code, Claude Desktop, or any MCP-aware host — sees the advertised `tool_schema` surface as callable tools. The `srmech-mcp` console script serves it over **stdio** (the transport Claude Desktop spawns) or **HTTP + SSE** for remote / cross-process use:

```bash
srmech-mcp                                      # stdio (Claude Code / Claude Desktop default)
srmech-mcp --transport http-sse --port 9991     # HTTP+SSE on localhost (remote / cross-process)
srmech-mcp --filter "srmech.physics.qm.*"               # expose only a sub-tree of tools
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
