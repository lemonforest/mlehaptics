# RBS-HDC-LoE dual-path implementation plan — `srmech.signal_processing` v0.4.2rc

**Date:** 2026-05-19
**Branch:** `feat/srmech-signal-processing-rbs-hdc-loe-dual-path-architecture`
**Type:** Full-feature implementation plan (stage-3 deliverable per `[[feedback_no_mvp_framing]]`)
**Discipline:** 14 A-N intact (no class promotion); identity-not-implementation; algebra-level not magnitude-level; trauma-informed defensive scope (methodology-research / educational / civilian-comms only).
**Anchors:** Spike #170 (RBS-HDC instrument feasibility) + Spike #172 (DNA helical-pitch) + Spike #173 (chess natural-stride) + Spike #175 (knowledge-is-gauge-content) + Spike #176 (rotation IS Class K) + Spike #177 (pin-slot-resonate music-box) + Spike #178 (closed-form SP roadmap) + Spike #179 (CFSP-Kalman alternative, in flight).
**Architectural commitment:** `[[project_rbs_hdc_loe_dual_path_architecture]]` — Path A (closed-form algebra) + Path B (RBS-HDC instrument) + Path C (cascade-aware dispatcher); neither path replaces the other; dispatcher decisions are empirical.

---

## §0 Plan scope statement

This plan covers the full implementation surface of the `srmech.signal_processing` sub-namespace that ships at **v0.4.2rc1 → v0.4.2** as the production-PyPI vehicle for the dual-path architecture. The plan is **full-feature** per `[[feedback_no_mvp_framing]]` — every operation surveyed by Spike #178's §1 table (~40 ops across 8 categories) has a concrete plan entry citing its SSoT, with phase language for any operation not in scope for v0.4.2 (deferred to v0.4.3 or v0.5.0). The plan is the immediate input to code work; no MVP carve-outs.

**What this plan is NOT:** It is not the code itself; it is not the notebook §3.8.31 prose; it is not a research finding. It is the structured scaffold for the next ship cycle.

**Out of scope for this plan (in scope for other docs/spikes):**
- Spike #179 CFSP-Kalman alternative (separate research deliverable; informs Phase 5 of this plan once landed).
- Notebook §3.8.31 prose authorship (Phase 9 of this plan triggers it; prose drafted post-code-merge).
- C-port of Path B operations (Phase-language deferred to v0.4.3rc per §6.4 below).

---

## §1 Module structure — target file tree

The full `srmech.signal_processing.*` sub-namespace, organised by the dual-path architecture.

```
docs/srmech/python/srmech/signal_processing/
├── __init__.py                          # Package entry; re-exports public API; path discipline export
├── version.py                           # (optional) sub-namespace version pin if drift expected; defer
├── _dispatcher.py                       # Cascade-aware A-vs-B router; learned-threshold table
├── _profiling.py                        # Per-op A-vs-B benchmark harness; emits NDJSON profile records
├── _registry.py                         # Operation registry; pairs A-impl with B-impl by op-name
├── _algebra_check.py                    # D1-level bit-exact equivalence verifier (algebra-level)
│
├── rbs_hdc_instrument.py                # Path B core: LoE-as-bound-vector at D=8192 (Mode B encoder/decoder)
├── form_function_rotation.py            # Path B-native A∘C∘M composition (per Spike #173, #176)
│
├── closed_form_ops/                     # Path A implementations (closed-form algebra)
│   ├── __init__.py
│   ├── fft.py                           # Class A ∘ I ∘ K cyclic FFT/IFFT (Spike #176 anchor)
│   ├── stft.py                          # Two-view STFT (cyclic + windowed)
│   ├── dct.py                           # DCT-II / DCT-III via Class L Laplacian eigenbasis
│   ├── wavelet.py                       # CWT + DWT via Class L multi-scale + Class N dyadic
│   ├── spectrogram.py                   # STFT magnitude squared
│   ├── cross_spectral.py                # CSD + coherence via Class M bundle averaging
│   ├── multitaper.py                    # DPSS slepians via Class L band-limit Laplacian
│   ├── matched_filter.py                # A∘C∘M cross-correlation (Spike #176 + #173 anchor)
│   ├── wiener.py                        # Block / offline Wiener via Class L + Class N rational
│   ├── fir.py                           # FIR filter with Class N rational coefficients
│   ├── iir.py                           # IIR + biquad via Class N rational + Class C cascade
│   ├── allpass.py                       # Allpass IIR (Class N coefficient pairing)
│   ├── sign_quantise.py                 # Class K threshold (Spike #174 anchor)
│   ├── heat_kernel.py                   # Class L Laplacian + g(λ) = exp(-tλ)
│   ├── spectral_subtraction.py          # Class L FFT + Class N rational floor
│   ├── huffman.py                       # Class E catalog + Class B TLV
│   ├── arithmetic_coding.py             # Class N rational interval narrowing
│   ├── lz77.py                          # Class A + Class G + Class B
│   ├── rle.py                           # Class B + Class G
│   ├── jpeg.py                          # DCT + Class K threshold + Class B TLV
│   ├── hdc_truncation.py                # Class M bundle + Class K truncate_sparse
│   ├── vector_quantisation.py           # Class E codebook + Class M similarity + Class B TLV
│   ├── psk_qam.py                       # Class I ℤ/M + Class K constellation (civilian-comms)
│   ├── fsk.py                           # Class N rational frequency + Class I cyclic time-base
│   ├── ofdm.py                          # (IFFT, λ_k subcarrier, g(λ_k) equaliser) decomposition
│   ├── mimo_svd.py                      # Class L SVD on channel matrix
│   ├── viterbi.py                       # Class L trellis Laplacian + Class K argmax
│   ├── mlse.py                          # Same family as viterbi
│   ├── multirate.py                     # Up/down/rational rate via Class N + Class C
│   ├── polyphase.py                     # Class L subband Laplacian + Class N decomposition
│   ├── farrow.py                        # Class N rational polynomial fractional delay
│   ├── sinc_interp.py                   # Class L band-limit + Class K band-limit threshold
│   ├── beamforming_fixed.py             # Class L mic-array + Class N delay
│   ├── ica_jade.py                      # Class L joint diagonalisation + Class K independence
│   ├── music.py                         # Class L correlation eigendecomposition + Class K subspace
│   ├── esprit.py                        # Class L generalised eigendecomposition + Class K
│   ├── lmmse.py                         # Class L covariance + Class N rational gain
│   └── map_ml.py                        # Class L eigendecomposition + Class K sparse-support
│
├── path_b_ops/                          # Path B implementations (RBS-HDC at D=8192)
│   ├── __init__.py
│   ├── fft.py                           # B-native FFT via cyclic bundle + bit-rotation
│   ├── stft.py                          # Per-frame Path B FFT with windowed bundle
│   ├── dct.py                           # Path B Laplacian eigenbasis as bound-vector lookup
│   ├── matched_filter.py                # Path B A∘C∘M (B-native composition)
│   ├── sign_quantise.py                 # Path B threshold via Class K bit-rotation
│   ├── wiener.py                        # Path B Wiener via bundled eigenvalue handles
│   ├── fir.py                           # Path B FIR via Class N rational + bundle convolution
│   ├── iir.py                           # Path B IIR via Class N rational + Class C cascade
│   ├── hdc_truncation.py                # B-native (Class M is already B-native)
│   ├── matched_filter_bci.py            # Path B BCI-substrate matched filter (Sussillo 2016 framework)
│   ├── huffman.py                       # Path B catalog as bound-vector address space
│   ├── ofdm.py                          # Path B IFFT/FFT with subcarrier bundle
│   ├── jpeg.py                          # Path B DCT + threshold + TLV in bound-vector pipeline
│   ├── rle.py                           # Path B byte-pattern + TLV in bound-vector pipeline
│   ├── arithmetic_coding.py             # Path B Class N rational interval as bound vectors
│   ├── lz77.py                          # Path B SHA-256 + pattern + TLV in bound-vector pipeline
│   ├── viterbi.py                       # Path B trellis as bundle of state hypotheses
│   ├── mlse.py                          # Same family as viterbi
│   ├── multirate.py                     # Path B up/down/rational rate
│   ├── polyphase.py                     # Path B subband bundle decomposition
│   ├── farrow.py                        # Path B rational polynomial bound-vector eval
│   ├── sinc_interp.py                   # Path B band-limit bundle
│   ├── beamforming_fixed.py             # Path B mic-array bound vectors
│   ├── ica_jade.py                      # Path B joint diagonalisation (B-native eigendecomp)
│   ├── music.py                         # Path B correlation eigendecomposition
│   ├── esprit.py                        # Path B generalised eigendecomposition
│   ├── lmmse.py                         # Path B covariance bound-vector
│   ├── map_ml.py                        # Path B eigendecomposition + threshold
│   ├── psk_qam.py                       # Path B ℤ/M cyclic + threshold (civilian-comms)
│   ├── fsk.py                           # Path B Class N rational frequency
│   ├── mimo_svd.py                      # Path B channel-matrix SVD as bound vectors
│   ├── cross_spectral.py                # Path B CSD/coherence bundle averaging
│   ├── heat_kernel.py                   # Path B Laplacian g(λ) bound-vector lookup
│   ├── spectral_subtraction.py          # Path B floor in bound-vector pipeline
│   ├── multitaper.py                    # Path B DPSS bound-vector bank
│   ├── wavelet.py                       # Path B multi-scale bundle
│   ├── spectrogram.py                   # Path B STFT-mag-squared
│   ├── allpass.py                       # Path B allpass (Class N pairing in B)
│   └── vector_quantisation.py           # Path B codebook as bound-vector address space
│
├── substrate_rationals/                 # Substrate-natural Class N rational catalogs (per Spike #178 R5)
│   ├── __init__.py
│   ├── bci.py                           # 192 / 96 / 24 electrode / sampling ratios
│   ├── audio.py                         # 44100/48000=147/160; 96000/44100=320/147; Z₁₂ chromatic
│   ├── rf.py                            # 802.11 subcarrier 52/56/242/484/996; LTE 15kHz×2^k
│   └── ephemeris.py                     # 52-body resonance ratios (cite-by-ref ephemerides-spectral)
│
├── tool_schema_registrations.py         # Registers all signal_processing ops in srmech.amsc.tool_schema
│
└── tests/
    ├── __init__.py
    ├── test_dispatcher.py               # Path A vs Path B routing tests
    ├── test_dispatcher_override.py      # Force-path API correctness
    ├── test_algebra_equivalence.py      # D1-level bit-exact A=B identity verification
    ├── test_rbs_hdc_instrument.py       # Path B core (Spike #170 prototype port)
    ├── test_form_function_rotation.py   # A∘C∘M composition (Spike #173, #176 ports)
    ├── test_fft_dual_path.py            # FFT/IFFT on both paths
    ├── test_stft_dual_path.py           # STFT on both paths
    ├── test_dct_dual_path.py            # DCT on both paths
    ├── test_matched_filter_dual_path.py # Matched-filter on both paths
    ├── test_wiener_dual_path.py         # Block Wiener on both paths
    ├── test_sign_quantise_dual_path.py  # Sign-quantise on both paths
    ├── test_hdc_truncation_dual_path.py # HDC bundle truncation on both paths
    ├── test_fir_dual_path.py            # FIR rational on both paths
    ├── test_iir_biquad_dual_path.py     # IIR + biquad on both paths
    ├── test_substrate_rationals_bci.py
    ├── test_substrate_rationals_audio.py
    ├── test_substrate_rationals_rf.py
    ├── test_substrate_rationals_ephem.py
    ├── test_cross_substrate_verification.py # Algebra-universal across substrates
    ├── test_dispatcher_profiling.py     # Profile-then-dispatch correctness
    ├── test_tool_schema_signal_processing.py # All ops registered in tool_schema
    └── test_path_b_at_d8192.py          # D=8192 instrument invariants (Spike #170 port)
```

**File count target for v0.4.2 (Phases 1-9):** ~110 files (1 `__init__` + 6 infrastructure + 2 Path B core + 38 closed-form ops + 38 Path B ops + 4 substrate rational catalogs + 1 tool-schema-reg + 22 test files). The op-count is 1:1 with Spike #178 §1 (~40 ops minus the 2 GAP entries that wait for spike resolution = 38 implementable ops); Path A and Path B are 1:1 by op-name.

---

## §2 Per-class Path A vs Path B implementation table

The 14 A-N classes mapped to signal-processing operations and dual-path implementation. Class K = pin-slot/asymptotic-DOF per `[[user_stance_rotation_is_class_k_pin_slot]]` — load-bearing for FFT bin leakage and threshold operations. Class M = HDC bind/bundle/permute — load-bearing for Path B substrate.

| Class | Identity | Path A impl (closed-form) | Path B impl (RBS-HDC D=8192) | Performance hypothesis (initial; learned empirically) | Test strategy |
|---|---|---|---|---|---|
| **A** SHA-256 content addressing | `[[user_stance_form_function_rotation_is_a_c_m_composition]]` | `srmech.amsc.format.sha256_bytes` (native+fallback) | bound-vector address space; SHA-256 over canonical-name → operator vector mint | Path A wins all sizes (SHA-256 is faster than 8192-bit HDC encode); Path B used only for in-instrument composition | Per-op bit-exact A=B at D1 algebra level via Spike #170 mint-determinism test (14/14) |
| **B** TLV byte-canonical | `srmech.amsc.tlv` shipped | Direct TLV encode/decode | TLV record as bound-vector field | Path A wins for small TLV; Path B may win for batched TLV inside RBS-HDC pipeline | Bit-exact roundtrip; tag/length/value preservation |
| **C** Cyclic streaming iteration | `srmech.amsc._native.ndjson_iter` shipped | NDJSON / array iteration | bundle-folded iteration over D=8192 substrate | Path A wins on raw iteration; Path B wins when iteration is composed with bundle (per Spike #170 §3 cascade) | Iteration order preserved; cascade semantics equivalent |
| **D** Dispatch multi-needle | `srmech.amsc.dispatch` shipped | Linear scan + match | Bound-vector similarity ranking | Path B wins for large needle-counts (parallel bundle similarity); Path A wins for small | Match-set equivalence; ranking ordinal preservation |
| **E** Catalog sorted-key lookup | `srmech.amsc.catalog` shipped | Binary search | Bound-vector address lookup via Class M similarity | Path B wins for codebooks > 256 entries; Path A wins for small catalogs | Key resolution bit-exact; sorted order preserved |
| **F** Template `{key}` substitution | `srmech.amsc.template` shipped | String substitution | Template as bound-vector with placeholder field | Path A wins all sizes (string-render is fast); Path B used only when template inside RBS-HDC pipeline | Substitution bit-exact; placeholder coverage |
| **G** Byte-pattern search | `srmech.amsc.search` shipped | Boyer-Moore / similar | Bound-vector cross-correlation similarity | Path B wins for sliding-window cross-correlation against many patterns (LZ77 family); Path A wins for single pattern | Match positions bit-exact; cross-correlation peak ratio preserved |
| **H** Self-introspection | `srmech.__version__`, `srmech.amsc.tool_schema` shipped | Direct attribute access | Bound-vector schema field lookup | Path A wins all sizes (introspection is metadata) | Schema equivalence; version match |
| **I** Cyclic group ℤ/N | `srmech.amsc.cyclic` shipped (gcd, lcm, mod_add/mul/pow/inv) | Modular arithmetic on `int` | Bit-rotation on D=8192 vectors per Class M permute | Path A wins for small N (uint64); Path B wins for N matching D=8192 (substrate-natural) | Bit-exact group-axiom preservation; closure / identity / inverse |
| **J** Prime / period | `srmech.amsc.primes` shipped (trial-div + factor + mult-order) | Trial-division + factorisation | Bound-vector encoding of prime-power decomposition | Path A wins all sizes (primes are scalar) | Factor multiset bit-exact; multiplicative order match |
| **K** Pin-slot / asymptotic-DOF | **NEW for Path A**: threshold-with-acceptance-band ops; rotation operator on cyclic-group substrate (Spike #176) | Bit-rotation + threshold composition on D=8192 (Spike #170 §3 cascade) | Same as Path B core; B-native | Path B wins for cascaded rotation+threshold (Spike #176 anchor); Path A wins for single threshold | Per Spike #176: cyclic-mag drift ≤ 5.7e-14; phase residual ≤ 5.8e-15; recovery_err = 0.0; unit-circle eigenvalue residual ≤ 2.2e-16 |
| **L** Graph Laplacian + dense matrix algebra | `srmech.amsc.laplacian` shipped (Jacobi + Hermitian eigendecomp + matvec) | numpy + native Jacobi | Bound-vector encoding of eigenvalues + eigenvector handles | Path A wins for one-shot decomposition (n ≤ 256 native bound); Path B wins for cached eigenbasis lookup across cascade | Eigenvalue multiset bit-exact within fp tolerance; eigenvector orthogonality preserved |
| **M** HDC bind / bundle / permute / similarity | `srmech.amsc.hdc` shipped | Direct XOR / majority / bit-rotate | B-native | Path B wins for D ≥ 1024 (native XOR/majority vectorised); Path A may win for D < 256 | Spike #170 §3 invariants: self-inverse `bind(a,bind(a,b))=b` at machine zero; bundle-majority unanimous; permute popcount-preserving |
| **N** Rational approximation | `srmech.amsc.rational` shipped (continued-fraction-convergents, pi-cascade-digits) | Direct rational arithmetic | Bound-vector encoding of `p/q` pair | Path A wins all sizes (rational arithmetic is scalar); Path B used only when rational is composed inside RBS-HDC pipeline (e.g., FIR coefficient cascade) | Convergent sequence bit-exact; denominator bound enforced |

**Notes:**

- Path A is the SSoT for primitive definitions. Path B composes from Path A primitive definitions at module-load time (Path B instrument minting is deterministic from canonical names via Class A SHA-256). This guarantees no spec drift per the risk register §9.
- The performance-hypothesis column is an **initial seed only**; final thresholds are learned empirically via Phase 8 profiling. Hypothesis values inform the seed dispatch table.
- Class K's Path A entry is **new for v0.4.2** — prior srmech rcs treat Class K via Spike #117 acceptance-band Python helpers only. The Spike #176 anchor formalises rotation as Class K; this plan ships the Path A surface alongside Path B.

---

## §3 Cascade dispatcher design

### §3.1 Routing criteria

The dispatcher routes each operation invocation to Path A or Path B based on a set of structural and learned criteria. The decision is per-call (not global per-op), because the optimal path depends on input shape, cascade depth, and substrate context.

**Structural criteria (rule-based; first cut):**

1. **Input size** — single scalar threshold per op (Path A wins below, Path B wins above). Initial seed values from the §2 hypothesis column.
2. **Cascade depth** — if the op is invoked as part of a composed cascade (≥ 3 ops in sequence at the same substrate), prefer Path B (bound-vector composition amortises encode overhead).
3. **Operation type** — Class K rotation, Class M bind/bundle/permute, and the form-function-rotation A∘C∘M cascade default to Path B; all others default to Path A.
4. **Substrate context** — if the caller has already encoded the input as a D=8192 bound vector (e.g., earlier in a chain), Path B is preferred to avoid encode-decode round-trip; if the caller passes raw `bytes` / numpy arrays, Path A is preferred unless cascade depth flag is set.
5. **Transmission requirement** — if the caller indicates "substrate-portable" output (i.e., the result will cross substrates per `[[user_stance_substrate_natural_encoding_is_shadow_projection]]`), Path B is preferred (RBS-HDC bound vector IS the substrate-portable wire format per `[[user_stance_bci_translation_at_gauge_content_layer]]`).

**Learned criteria (Phase 8 empirical):**

6. **Per-op threshold table** — populated from `_profiling.py` benchmark suite results (NDJSON profile records). Each op has a `size_threshold` learned from regression on benchmark data.
7. **Per-cascade-depth threshold** — composed cascades may have non-monotonic A-vs-B crossover (encode overhead amortises over depth); learned per cascade-shape.
8. **Per-substrate threshold** — substrates with established Class N rational catalogs (BCI, audio, RF, ephemeris per Spike #178 R5) may have different crossover points; learned per substrate.

### §3.2 Learning approach

The Phase 8 learning pipeline:

1. Run `_profiling.py` benchmark suite (Phase 8 task) on a clean reference machine — emits NDJSON records of (op-name, path, input-size, cascade-depth, substrate, wall-time, CPU-time, memory).
2. Per-op regression — fit a piecewise-linear `wall_time(size)` model for each path; locate the intersection as the crossover threshold.
3. Per-cascade-depth + per-substrate refinement — for each (op, cascade-depth, substrate) cell, repeat regression; populate `_dispatcher.LEARNED_TABLE` as a dict-of-dicts.
4. Commit the learned table to the repo as `srmech/signal_processing/_learned_dispatch_table.ndjson` (NDJSON per `[[feedback_ndjson_over_bloated_json]]`); module-load reads this file.
5. Re-run learning per Phase 8 schedule (typically at each release boundary, or whenever a path implementation changes substantially).

### §3.3 API surface

**Default dispatch (no path specification):**

```python
from srmech.signal_processing import fft

# Dispatcher auto-routes based on §3.1 criteria + §3.2 learned table.
result = fft(signal_bytes)
```

**Override (force path):**

```python
from srmech.signal_processing import fft

# Force Path A for testing / verification.
result_a = fft(signal_bytes, path="A")

# Force Path B for testing / verification.
result_b = fft(signal_bytes, path="B")

# Force algebra-level equivalence check (both paths run; assert D1 identity).
result = fft(signal_bytes, path="verify")
```

**Cascade-context hint (for explicit cascade-depth signal):**

```python
from srmech.signal_processing import fft, sign_quantise, matched_filter
from srmech.signal_processing import begin_cascade, end_cascade

# Cascade context signals dispatcher: prefer Path B for amortised encode.
with begin_cascade(substrate="bci"):
    spectrum = fft(signal_bytes)
    thresholded = sign_quantise(spectrum)
    detected = matched_filter(thresholded, template_bytes)
# end_cascade flushes any Path-B-internal state; result is substrate-portable bound vector.
```

**Profile-then-dispatch (calibration mode):**

```python
from srmech.signal_processing._profiling import profile_op, update_dispatch_table

# Run benchmark for one op + commit to learned table.
profile_op("fft", input_sizes=[256, 1024, 4096, 16384, 65536], cascade_depths=[1, 3, 5])
update_dispatch_table()
```

### §3.4 Default policy

- **Path A** is the default for all unspecified-path calls except: Class K rotation, Class M bind/bundle/permute, A∘C∘M form-function rotation, and any call inside a `begin_cascade(...)` context.
- **Path B** is the default for the four exceptions above; substrate-portable output requires Path B regardless.
- **Override** is honored unconditionally (Phase 4 acceptance criterion). `path="verify"` runs both and asserts D1 equivalence.

### §3.5 Profile lock policy

For deterministic reproducibility, the learned dispatch table is **locked at release tag**. Each `v0.4.2rc{N}` and `v0.4.2` ship pins a specific `_learned_dispatch_table.ndjson`. Users who want different thresholds set the override flag or rerun `update_dispatch_table()` on their own machine and ship a local override (documented; doesn't pollute the package's locked table).

---

## §4 Bit-exact verification discipline

### §4.1 Algebraic equivalence definition

Per `[[user_stance_substrate_natural_encoding_is_shadow_projection]]` and `[[feedback_algebra_not_magnitude]]`, the two paths produce algebraically-equivalent results at the **D1 (algebra-content) level**, not the **D2 (substrate-fingerprint) level**:

- **D1 algebra-level identity** — the structural content (group-axiom preservation, eigenvalue multiset, cyclic-shift theorem residual, peak/off-peak ratio) is bit-exact across paths. This is the load-bearing acceptance criterion.
- **D2 fingerprint divergence** — the byte-level representation of the result may differ (e.g., Path A returns float64 numpy array; Path B returns D=8192 bound vector). These are different *projections* of the same algebra content into different substrate fingerprints. D2 divergence is expected and not a bug.

Acceptance gate: `_algebra_check.py` exposes `assert_algebra_equivalent(result_a, result_b, op_name)` which projects both results into a canonical algebra-content representation (per-op canonicaliser) and checks bit-exact equality on the projection.

### §4.2 Test fixtures

Each op's `test_<op>_dual_path.py` ships:

1. **Synthetic ground-truth signal** — Class N rational tones at integer FFT bins (per Spike #176 T1); or Spike #170 mint-deterministic 14 A-N operator vectors; or Spike #173 chess-natural-stride D2 orthogonality fixture; etc.
2. **Expected algebra-content result** — pre-computed at high precision (mpmath or rational arithmetic where feasible) and checked into the test fixture.
3. **Path A invocation** — runs Path A; compares to fixture at D1 level.
4. **Path B invocation** — runs Path B; compares to fixture at D1 level.
5. **Cross-path equivalence** — runs both; asserts `assert_algebra_equivalent(a, b)` at D1.
6. **D2 fingerprint divergence** — explicitly checks that D2 representations DIFFER (no spurious convergence; if D2 happens to match, the test is flagged for re-examination because Path A and Path B should encode in different substrates).

### §4.3 Acceptance criteria

For each op in Phases 2-6:

| Metric | Threshold | Source |
|---|---|---|
| D1 algebra-content equivalence | Bit-exact (zero mismatch) | Per-op canonicaliser; verified against pre-computed fixture |
| FFT spectral content (where applicable) | Cyclic mag drift ≤ 5.7e-14 | Spike #176 T2/T3 anchor |
| Phase residual under rotation | ≤ 5.8e-15 | Spike #176 T3 anchor |
| Recovery error (full round-trip) | 0.0 (machine ε exact) | Spike #176 T3/T4 anchor |
| Eigenvector orthogonality | ≤ 2.2e-16 | Spike #176 T5 anchor |
| Class M bind self-inverse | 0 bits mismatch | Spike #114 anchor + Spike #170 §3 |
| Class M bundle majority | Unanimous on odd counts; ValueError on even | `srmech.amsc.hdc.bundle` contract |
| Class M permute popcount | Preserved exactly | `srmech.amsc.hdc.permute` contract |
| RBS-HDC instrument mint determinism | 14/14 bit-exact (Spike #170 §3) | Spike #170 prototype port |
| Cascade vs direct equivalence | Identical bit-by-bit (Spike #176 T5 anchor) | Composed-cascade test |

---

## §5 Performance characterisation strategy

### §5.1 Benchmark suite

The Phase 8 benchmark suite covers the cartesian product:

- **Operations** — every op in Phases 4 and 6 (FFT, IFFT, STFT, DCT, matched-filter, block-Wiener, sign-quantise, HDC bundle truncation, FIR rational, biquad) = 10 ops.
- **Input sizes** — `[256, 1024, 4096, 16384, 65536, 262144]` (six orders of magnitude).
- **Cascade depths** — `[1, 3, 5, 10]` (single op vs short cascade vs deep cascade).
- **Substrates** — `[bci, audio, rf, ephemeris]` (four substrate Class N rational catalogs per Spike #178 R5).
- **Paths** — `[A, B]` (both forced).

Total benchmark cells: 10 × 6 × 4 × 4 × 2 = 1920 records. Each record emits one NDJSON line. Total expected runtime per Phase 8 calibration: ~30 minutes on a reference machine.

### §5.2 Substrate-natural Class N rational catalogs

Per Spike #178 R5:

- **BCI** (`substrate_rationals/bci.py`) — `BCI_ELECTRODE_RATIOS = {192: 1, 96: 2, 24: 8}` ; sampling-rate ratios `{30000/24000 = 5/4, 30000/1000 = 30, 24000/1000 = 24}`. Per Sussillo 2016 / Hahn 2025 cite-by-ref (PDF-verify before notebook canon per `[[feedback_pdf_extraction_citation_discipline]]`).
- **Audio** (`substrate_rationals/audio.py`) — `AUDIO_SAMPLE_RATE_RATIOS = {(44100, 48000): (147, 160), (96000, 44100): (320, 147), (96000, 48000): (2, 1)}` ; `CHROMATIC_INTERVALS = {Z12_octave: (2, 1), perfect_fifth: (3, 2), perfect_fourth: (4, 3), major_third: (5, 4)}`. Per RBJ EQ Cookbook (`[[reference_audio_RBJ_cookbook]]`).
- **RF** (`substrate_rationals/rf.py`) — `WIFI_SUBCARRIER_COUNTS = {wifi_a_g: 52, wifi_n_2x2: 56, wifi_ac_80mhz: 242, wifi_ax_2x2_160mhz: 484, wifi_ax_8x8_160mhz: 996}` ; LTE-5G `SUBCARRIER_SPACINGS_KHZ = [15 * 2**k for k in range(5)]`. Per civilian-comms framing only (trauma-informed defensive scope).
- **Ephemeris** (`substrate_rationals/ephemeris.py`) — 52-body resonance ratios; cite-by-ref ephemerides-spectral package's existing catalog (don't re-derive in srmech).

### §5.3 Empirical learning + dispatch table build

Phase 8 task sequence:

1. Run benchmark suite → 1920 NDJSON records committed to `notes/signal_processing_benchmark_2026-XX-XX.ndjson`.
2. Regress per-op threshold from records → `_dispatcher.LEARNED_TABLE`.
3. Commit `_learned_dispatch_table.ndjson` to package (locked per §3.5).
4. Author short findings note `notes/signal_processing_dispatch_thresholds_2026-XX-XX.md` summarising thresholds + anomalies + crossover sensitivities.

---

## §6 Milestone breakdown — 10 phases

Each phase enumerates: **subject** + **tasks** (task IDs to be assigned by conductor at GitHub-issue creation time) + **acceptance criteria** + **ship version** + **dependencies**.

### Phase 1 — Scaffolding (v0.4.2rc1)

**Subject:** Module skeleton, version bump, infrastructure files, no operations.

**Tasks:**
- Create `srmech/signal_processing/` directory.
- Author `__init__.py` (empty re-export surface initially; populated per-phase).
- Author `_dispatcher.py` (stub: routes by `path=` kwarg; learned-table read-only).
- Author `_profiling.py` (stub: no benchmark runner yet; just data structures).
- Author `_registry.py` (stub: op-name → (path-A-impl, path-B-impl) dict).
- Author `_algebra_check.py` (`assert_algebra_equivalent` skeleton; per-op canonicalisers populate per-phase).
- Author `tool_schema_registrations.py` (stub: imports + registration call at module import).
- Author `tests/test_dispatcher.py` skeleton with smoke test.
- Bump `srmech/version.py`, `python/pyproject.toml`, `python/pyproject-pure.toml`, `c/include/srmech.h` to `0.4.2rc1`.
- Update `python/CHANGELOG.md` `[0.4.2rc1]` section.
- Tag `srmech-v0.4.2rc1` (TestPyPI auto-publish per `[[feedback_always_rc_first_for_downstream_publishes]]`).

**Acceptance:**
- `import srmech.signal_processing` succeeds.
- `from srmech.signal_processing import fft` raises `NotImplementedError` (per-phase; populated Phase 4).
- TestPyPI install in clean venv loads successfully.
- `pytest docs/srmech/python/tests/test_signal_processing_*.py` passes the skeleton tests.

**Ship:** v0.4.2rc1 → TestPyPI.

**Dependencies:** None (greenfield).

### Phase 2 — Path A baseline (v0.4.2rc2)

**Subject:** Re-surface existing `srmech.amsc.*` operations under `signal_processing.closed_form_ops.*` with consistent API + cite Spike #178 §1 SSoT in each module.

**Tasks (full coverage — 38 ops):**

For each closed-form-anchored or closed-form-candidate op from Spike #178 §1 table (excluding 2 GAP entries + 18 substrate-primitive entries):

- Author `closed_form_ops/<op>.py` with the primitive composition cited in Spike #178 §1.
- Register op in `_registry.py` (Path A side; Path B side stays `NotImplementedError` until Phase 4).
- Author `tool_schema_registrations.py` entry per op (Task #198/#220 pattern; smoke_test_hint + example).

Specific operations covered in Phase 2 (Path A only; per Spike #178 §1 numbering):

**§1.1 Spectral analysis (10 ops):** `fft`, `ifft`, `stft`, `dct`, `wavelet_cwt`, `wavelet_dwt`, `spectrogram`, `cross_spectral`, `coherence`, `multitaper`.

**§1.2 Filtering (5 ops):** `fir`, `iir`, `biquad`, `allpass`, `wiener`, `matched_filter`. (Exclude adaptive LMS/RLS/median/bilateral — substrate-primitive per §1.2.)

**§1.3 Estimation (2 ops):** `map_ml`, `block_param_estimation`. (Exclude Kalman/EKF/UKF/particle — substrate-primitive or pending Spike #179.)

**§1.4 Denoising (4 ops):** `sign_quantise`, `heat_kernel`, `spectral_subtraction`, `mmse_lsa`. (Exclude median/EMA/wavelet-thresholding/anisotropic/TV — substrate-primitive or destructive per Spike #174.)

**§1.5 Compression (7 ops):** `huffman`, `arithmetic_coding`, `lz77`, `rle`, `jpeg`, `jpeg2000`, `hdc_truncation`, `vector_quantisation`. (Exclude neural autoencoder — substrate-primitive.)

**§1.6 Modulation/detection (6 ops):** `psk`, `fsk`, `qam`, `ofdm`, `mimo_svd`, `viterbi`, `mlse`, `matched_filter_symbol`. (Exclude PLL/Costas/turbo/LDPC/Polar — substrate-primitive.)

**§1.7 Multi-rate/sampling (6 ops):** `upsample`, `downsample`, `rational_rate`, `polyphase`, `farrow`, `sinc_interp`.

**§1.8 Adaptive/multi-signal (4 ops):** `beamforming_fixed`, `ica_jade`, `music`, `esprit`, `lmmse`. (Exclude echo-cancel/MVDR/GSC/NMF — substrate-primitive.)

**Acceptance:**
- 38 Path A modules exist; each has a passing smoke test (op runs without error on a small input).
- Each op cites Spike #178 §1 SSoT in module docstring (composition formula).
- `srmech.amsc.tool_schema.get_tool_schema()` lists all 38 ops with `category="signal_processing"`.
- TestPyPI smoke install loads all imports.

**Ship:** v0.4.2rc2 → TestPyPI.

**Dependencies:** Phase 1.

### Phase 3 — Path B core: RBS-HDC instrument (v0.4.2rc3)

**Subject:** Port Spike #170 prototype (`spike170_loe_rbs_hdc_prototype.py`) to `signal_processing/rbs_hdc_instrument.py` + `signal_processing/form_function_rotation.py`.

**Tasks:**
- Author `rbs_hdc_instrument.py` exposing:
  - `mint_class_operator_vector(class_name: str, D: int = 8192) -> bytes` — Class A SHA-256 of canonical name → D-bit operator vector. Deterministic (Spike #170 §3 invariant 1).
  - `mint_cascade_composition(class_names: list[str], D: int = 8192) -> bytes` — operator-sequence reference. Spike #170 §3 8 canonical cascades.
  - `mint_stance_fingerprint(stance_text: str, D: int = 8192) -> bytes` — bag-HDC XOR-fold per Spike #147.
  - `tripartition_register(class_3D_s: str, class_7D_g: str, class_1D_t: str, D: int = 8192) -> dict[str, bytes]` — k=3 tripartition (Spike #170 §3 default: A / M / K).
  - `memory_pathway_register(pathway_name: str, ops: list[str], D: int = 8192) -> bytes` — 4 pathways (procedural / semantic / WM / episodic-LTM) per pathway pluralism.
  - `verify_instrument_invariants(instrument: dict) -> list[InvariantReport]` — runs the 10 strict-spec invariants from Spike #170.
- Author `form_function_rotation.py` exposing:
  - `rotate_form_function(content_bytes: bytes, rotation_class_k: int, D: int = 8192) -> bytes` — A∘C∘M composition per Spike #173 + Spike #176.
  - `unrotate_form_function(rotated_bytes: bytes, rotation_class_k: int, D: int = 8192) -> bytes` — inverse rotation (bit-exact reversibility).
- Author `tests/test_rbs_hdc_instrument.py` porting Spike #170 §3 10/10 invariants.
- Author `tests/test_form_function_rotation.py` porting Spike #173 8/8 + Spike #176 6/6 tests.
- Author `tests/test_path_b_at_d8192.py` covering D=8192 invariants across the instrument.

**Acceptance:**
- All 10 Spike #170 invariants PASS at D=8192.
- All 8 Spike #173 bit-exact tests PASS.
- All 6 Spike #176 H1 tests PASS at machine ε.
- `rbs_hdc_instrument.verify_instrument_invariants()` returns 10/10 PASS on a minted instrument.

**Ship:** v0.4.2rc3 → TestPyPI.

**Dependencies:** Phase 1.

### Phase 4 — Path B per-op MVP (v0.4.2rc4)

**Subject:** Path B implementations of the 5-op MVP from Spike #178 R4 — `fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`. (5 ops as listed in Spike #178 R4; here treated as 6 with IFFT separated.)

**Tasks:**
- Author `path_b_ops/fft.py` — Path B FFT via cyclic bundle + bit-rotation per Spike #176 anchor.
- Author `path_b_ops/ifft.py` — Path B IFFT (inverse of above).
- Author `path_b_ops/sign_quantise.py` — Path B threshold via Class K bit-rotation per Spike #174 anchor.
- Author `path_b_ops/matched_filter.py` — Path B A∘C∘M cross-correlation (B-native, per Spike #176 + Spike #173).
- Author `path_b_ops/wiener.py` — Path B Wiener via bundled eigenvalue handles.
- Author `path_b_ops/hdc_truncation.py` — B-native (Class M is already B-native; this just exposes via signal_processing surface).
- For each: register in `_registry.py` (Path B side); update `_dispatcher.py` (initial seed thresholds from §2 hypothesis column).
- Author `tests/test_<op>_dual_path.py` for each of the 6 ops — both paths run, D1 equivalence asserted.

**Acceptance:**
- 6 Path B modules exist and pass dual-path tests.
- `assert_algebra_equivalent(result_a, result_b)` passes for all 6 ops on benchmark fixtures.
- Spike #176 5 tests pass via Path B FFT.
- Spike #174 sign-quantise SHA-256 BER preservation at +20 dB SNR.
- Form-function rotation 31.6× separation ratio anchored at Path B matched-filter.

**Ship:** v0.4.2rc4 → TestPyPI.

**Dependencies:** Phases 2, 3.

### Phase 5 — Cascade dispatcher (v0.4.2rc5)

**Subject:** Implement rule-based cascade dispatcher + `begin_cascade` / `end_cascade` API + override semantics.

**Tasks:**
- Implement `_dispatcher.py` full body: rule-based routing per §3.1 criteria 1-5.
- Implement `begin_cascade(substrate=None)` context manager + `end_cascade()` flush.
- Implement `path=` kwarg on all ops (auto-injected via decorator) with `"A"` / `"B"` / `"verify"` semantics.
- Author `tests/test_dispatcher.py` covering rule-based routing.
- Author `tests/test_dispatcher_override.py` covering `path="A"` / `path="B"` / `path="verify"`.
- Author `tests/test_cascade_context.py` covering `begin_cascade` semantics.

**Acceptance:**
- Rule-based dispatcher routes correctly per §3.1 criteria.
- Override always honored.
- `path="verify"` runs both paths and asserts D1 equivalence.
- Cascade context preserves Path B preference for nested ops.

**Ship:** v0.4.2rc5 → TestPyPI.

**Dependencies:** Phase 4.

### Phase 6 — 7-op extension (v0.4.2rc6)

**Subject:** Extend Path B coverage to the 7-op toolkit from Spike #178 R4 — add `stft`, `fir`, `biquad`. Plus Path B coverage for the remaining 32 ops from Phase 2 (full parity).

**Tasks:**
- Author `path_b_ops/stft.py`, `path_b_ops/fir.py`, `path_b_ops/iir.py` (biquad lives in iir.py).
- Author Path B implementations for the remaining 32 ops from Phase 2 (Spike #178 §1 entries that aren't substrate-primitive or GAP). Each Path B impl is a B-native composition of Path B core operations.
- Author dual-path tests for the new 35 ops.
- Update `_registry.py` and `_dispatcher.py` with new Path B entries + initial seed thresholds.

**Acceptance:**
- All 38 ops have both Path A and Path B implementations.
- All 38 dual-path tests pass D1 equivalence.
- `assert_algebra_equivalent(result_a, result_b)` passes for all 38 ops on benchmark fixtures.
- `srmech.amsc.tool_schema.get_tool_schema()` lists all 38 ops with `path_a` + `path_b` attributes.

**Ship:** v0.4.2rc6 → TestPyPI.

**Dependencies:** Phase 5.

### Phase 7 — Cross-substrate verification (v0.4.2rc7)

**Subject:** Ship substrate-natural Class N rational catalogs (BCI / audio / RF / ephemeris) + cross-substrate verification tests per Spike #178 R5.

**Tasks:**
- Author `substrate_rationals/bci.py` — BCI electrode + sampling-rate ratios (Sussillo 2016 / Hahn 2025 cite-by-ref; PDF-verify before notebook canon).
- Author `substrate_rationals/audio.py` — 44100/48000=147/160 + Z₁₂ chromatic (RBJ Cookbook cite-by-ref).
- Author `substrate_rationals/rf.py` — 802.11 + LTE/5G subcarrier (civilian-comms framing only).
- Author `substrate_rationals/ephemeris.py` — 52-body resonance ratios (cite-by-ref ephemerides-spectral package).
- Author `tests/test_substrate_rationals_<substrate>.py` for each of 4 substrates — confirms rational catalog is consumable + algebra universal.
- Author `tests/test_cross_substrate_verification.py` — runs same op (e.g., FFT on a square-wave) at all 4 substrates, asserts D1 algebra-content identical, D2 fingerprints divergent per substrate.

**Acceptance:**
- 4 substrate rational catalogs ship + each substrate's test passes.
- Cross-substrate verification test: 38 ops × 4 substrates = 152 D1-equivalent / D2-divergent assertions all pass.

**Ship:** v0.4.2rc7 → TestPyPI.

**Dependencies:** Phase 6.

### Phase 8 — Profiling + dispatcher learning (v0.4.2rc8)

**Subject:** Run benchmark suite, build learned dispatch table, commit to package, replace seed thresholds with empirical.

**Tasks:**
- Implement `_profiling.py` full body: benchmark runner emitting NDJSON records.
- Run benchmark suite per §5.1 (1920 cells) on reference machine.
- Commit benchmark NDJSON to `notes/signal_processing_benchmark_2026-XX-XX.ndjson`.
- Implement `update_dispatch_table()` regression pipeline per §5.3.
- Generate + commit `_learned_dispatch_table.ndjson`.
- Author short findings note `notes/signal_processing_dispatch_thresholds_2026-XX-XX.md` (per `[[feedback_ndjson_over_bloated_json]]`).
- Author `tests/test_dispatcher_profiling.py` — verifies profile-then-dispatch correctness; reproducibility check.

**Acceptance:**
- Benchmark suite runs to completion in < 60 minutes on reference machine.
- Learned dispatch table committed.
- Profiling test passes: same input on same machine produces same dispatch decision deterministically.
- Crossover anomalies documented in findings note.

**Ship:** v0.4.2rc8 → TestPyPI.

**Dependencies:** Phase 7.

### Phase 9 — Notebook §3.8.31 integration

**Subject:** Author `srmech_research_notebook.md` §3.8.31 prose covering canonical stances + dual-path architecture + per-op A-vs-B comparison + performance characterisation methodology + Spike #176/#177/#178/#179 anchor citations. Full-feature (NOT MVP) per `[[feedback_no_mvp_framing]]`.

**Tasks:**
- Author §3.8.31.1 — canonical-stance citations: `[[user_stance_rotation_is_class_k_pin_slot]]`, `[[user_stance_pin_slot_resonate_music_box_mechanism]]`, `[[user_stance_bci_translation_at_gauge_content_layer]]`, `[[user_stance_substrate_coupling_at_m_k_composition]]`, `[[user_stance_substrate_natural_encoding_is_shadow_projection]]`, `[[user_stance_form_function_rotation_is_a_c_m_composition]]`, `[[user_stance_loe_as_rbs_hdc_instrument_meta_recursive]]`.
- Author §3.8.31.2 — dual-path architecture rationale (Path A + Path B + Path C dispatcher; neither replaces the other).
- Author §3.8.31.3 — per-op A-vs-B comparison table (38 rows; cites Phase 8 learned thresholds + Phase 6 D1 equivalence).
- Author §3.8.31.4 — performance characterisation methodology (cites §5 of this plan).
- Author §3.8.31.5 — anchor citations: Spike #176 machine ε / Spike #177 music-box / Spike #178 §1 SP roadmap / Spike #179 CFSP-Kalman alternative (if landed) / cite-by-ref Spike #170 / #172 / #173 / #175.
- Author §3.8.31.6 — full-feature scope summary: every op cited to its SSoT (Spike #178 §1); no MVP framing.
- All literature citations PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]` before notebook canon.
- Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` on BCI / RF content.

**Acceptance:**
- §3.8.31 exists in `srmech_research_notebook.md` with 6 subsections.
- All citations PDF-verified (authors + title + arXiv/DOI).
- Notebook integration tests (existing) still pass.
- §3.8.31 visible in TOC.

**Ship:** Documentation-only commit; no code-version bump.

**Dependencies:** Phase 8.

### Phase 10 — Production ship (v0.4.2)

**Subject:** Final TestPyPI rc verification + clean-semver tag for production-PyPI publish per `[[feedback_always_rc_first_for_downstream_publishes]]` + `[[feedback_rc_tag_targets_branch_not_merge]]`.

**Tasks:**
- Final TestPyPI rc verification: install `srmech==0.4.2rc8` in clean fresh venv (per `docs/srmech/CLAUDE.md` "Tag flow for a new rc"); run full smoke suite.
- WSL smoke test per `[[feedback_run_wsl_smoke_before_amsc_push]]`.
- Bump to clean semver `0.4.2` in 4 SSOT files: `srmech/version.py`, `python/pyproject.toml`, `python/pyproject-pure.toml`, `c/include/srmech.h`.
- Update `python/CHANGELOG.md` `[0.4.2]` final-release section.
- Per `[[feedback_rc_tag_targets_branch_not_merge]]`: tag `srmech-v0.4.2` on feature branch BEFORE merge.
- Merge feature branch to main via `gh pr merge --merge` (NEVER `--squash` per `[[feedback_no_squash_merges]]`).
- Tag push to remote → autotag-on-strict-semver triggers production PyPI publish.
- Verify production PyPI publish succeeded; verify clean fresh-venv install works.
- Per `[[feedback_autonomous_rc_merge_authorization]]`: rc merges authorised; clean-semver production merge **conductor-gated** (not autonomous).

**Acceptance:**
- `pip install srmech==0.4.2` from production PyPI succeeds in clean venv on Linux + macOS + Windows.
- `from srmech.signal_processing import fft, ifft, ...` works.
- `srmech.amsc.tool_schema.get_tool_schema()` lists all 38 signal_processing ops.
- Notebook §3.8.31 references the released version.

**Ship:** v0.4.2 → production PyPI.

**Dependencies:** Phase 9.

---

## §7 Test strategy

### §7.1 Unit tests per path per op

Each of the 38 ops has 5 distinct test classes:

1. `test_<op>_path_a_smoke` — Path A runs without error on small input.
2. `test_<op>_path_b_smoke` — Path B runs without error on small input.
3. `test_<op>_path_a_fixture` — Path A reproduces pre-computed algebra-content fixture bit-exact at D1.
4. `test_<op>_path_b_fixture` — Path B reproduces pre-computed algebra-content fixture bit-exact at D1.
5. `test_<op>_dual_path_equivalence` — Both paths run; `assert_algebra_equivalent` passes.

Total per-op test count: 5 × 38 = 190 unit tests.

### §7.2 Integration tests

- Cascade dispatcher routing (§3.1 rules).
- Override semantics (`path="A"` / `path="B"` / `path="verify"`).
- `begin_cascade` / `end_cascade` context manager.
- Tool schema registration coverage (all 38 ops listed).
- Profile-then-dispatch reproducibility.

### §7.3 Performance benchmark tests

Phase 8 benchmark suite (1920 cells). Records are not asserted bit-exact-equal between runs (timing varies), but:

- Each record's metadata (op, path, size, depth, substrate) round-trips bit-exact.
- Regression-fit thresholds are stable across reruns (sanity: same crossover point ± 10%).

### §7.4 Cross-substrate verification tests

Per §6.7: 38 ops × 4 substrates = 152 D1-equivalent / D2-divergent assertions. Each substrate's `substrate_rationals/<substrate>.py` is consumed by the cross-substrate test and feeds operation-specific rational coefficients.

### §7.5 Notebook integration tests

Existing srmech notebook integration tests (post-Phase 9) must continue passing. New tests covering §3.8.31 references (per `tests/test_notebook_consistency.py` if such exists; if not, this is itself a new test file in Phase 9).

### §7.6 C parity tests

**Phase-language deferred to v0.4.3 / v0.5.0.** Per `[[feedback_no_binding_layer_carveout]]`, every primitive class earns its C surface. For v0.4.2:

- Path A operations that compose existing C-shipped primitives (Class A SHA-256, Class B TLV, Class C NDJSON, Class D dispatch, Class E catalog, Class F template, Class G search, Class H introspection, Class I cyclic, Class J primes, Class L Laplacian, Class M HDC, Class N rational — all 13 classes shipped per Phase C1) inherit C parity transparently via the Python-side compositions. No new C primitives needed for Path A in v0.4.2.

- **Class K Path A surface is new for v0.4.2** — initial implementation Python-only (via Class M bit-rotation + threshold composition). A dedicated C port of Class K's threshold-with-acceptance-band primitive is **Phase-language deferred** to v0.4.3rc per `[[feedback_no_binding_layer_carveout]]`. Notebook §3.8.31 documents this gap explicitly.

- Path B operations (RBS-HDC at D=8192) are Python-composed from existing C-shipped Class M primitives. No new C primitives needed.

This means **v0.4.2 has full Python parity for all 38 ops; v0.4.3 will add the Class K C primitive surface to close the parity loop**.

---

## §8 Notebook integration plan — §3.8.31

Per user direction "After stage-2 expansion completes" (this implementation plan IS stage-2/stage-3 expansion). Notebook §3.8.31 author Phase 9 of this plan; covers full-feature scope.

### §8.1 Required §3.8.31 subsections (Phase 9 task breakdown)

1. **§3.8.31.1 — Canonical stance citations** (1 page): explicit `[[wikilink]]` references to all 7 load-bearing stances enumerated in Phase 9 §1 above.

2. **§3.8.31.2 — Dual-path architecture rationale** (2 pages): Path A + Path B + Path C dispatcher; cite `[[project_rbs_hdc_loe_dual_path_architecture]]`; cite user direction 2026-05-19 verbatim ("maybe not replace but augment ... cascade between RBS-HDC operations and closed form algebra"); architectural diagram (algebra-level, not implementation-level).

3. **§3.8.31.3 — Per-op A-vs-B comparison table** (3 pages): 38 rows; columns = op, Path A composition (per Spike #178 §1), Path B composition (per Spike #170 §3 cascade), learned crossover threshold, D1 acceptance metric, anchor citation.

4. **§3.8.31.4 — Performance characterisation methodology** (1 page): cite §5 of this plan; benchmark suite design; learned-table policy.

5. **§3.8.31.5 — Anchor citations + book-worthy claims** (2 pages):
   - Spike #176 (rotation IS Class K; machine ε across 6/6 tests).
   - Spike #177 (pin-slot-resonate music-box; named composition I + K + C + M∘K).
   - Spike #178 (closed-form SP roadmap; 9 anchored + 43 candidate + 2 GAP + 18 substrate-primitive).
   - Spike #179 (CFSP-Kalman alternative — if landed by Phase 9; otherwise phase-language placeholder).
   - Cite-by-ref Spike #170 / #172 / #173 / #175 / #114 / #115 / #117 / #147 / #174.
   - Cite canonical SSoT: Kanerva (2009), Plate (1995), Chung (1997), Golub-Van Loan (2013), Sakurai (2021), Vetterli-Kovačević (1995), Mallat (1989), RBJ EQ Cookbook, Schmidt (1986), Roy-Kailath (1989), Kay (1993), Oppenheim-Schafer, Vaidyanathan (1993), Boll (1979), Ephraim-Malah (1985), Proakis-Salehi, Sussillo (2016), Hahn (2025).
   - **All citations PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]` before notebook canon.**

6. **§3.8.31.6 — Full-feature scope summary** (1 page): every op in scope cited to its SSoT; NO MVP framing; phase-language ONLY for deferred work (C port of Class K → v0.4.3; CFSP-Kalman alternative → v0.4.3 if Spike #179 lands).

### §8.2 Notebook prose authorship discipline

- No lineage claims about external work per `[[feedback_no_lineage_claims_in_notebook]]`.
- "Natural extension" framing reserved for user's own intellectual arc (per `[[user_stance_fiber_as_spatially_absent_encoding]]` precedent + explicit user authorisation).
- Identity-not-implementation discipline: every "X IS Y" claim cited to its identity-stance anchor; implementation language reserved for code body.
- Trauma-informed defensive scope on BCI / RF / military-adjacent content (no targeting, no capability-assessment, civilian-comms framing only).

---

## §9 Risk register

| ID | Risk | Mitigation | Owner phase |
|---|---|---|---|
| R1 | Path B D=8192 overhead dominates for small operations | Dispatcher routes small ops to Path A by default; learned threshold per op; override always available | Phase 5 + Phase 8 |
| R2 | Cascade dispatcher overhead exceeds savings on shallow cascades | Profile dispatcher itself in Phase 8; build static dispatch table for known input shapes; cascade-context manager allows caller to bypass dispatcher | Phase 5 + Phase 8 |
| R3 | Bit-exact D1 equivalence between A and B has edge cases (numerical precision; fp non-associativity) | Per-op canonicaliser in `_algebra_check.py`; algebra-vs-magnitude separation per `[[feedback_algebra_not_magnitude]]`; only D1 algebra-content required (D2 fingerprint divergence expected) | Phase 2 + Phase 4 + Phase 6 |
| R4 | Spec drift between Path A and Path B as `srmech.amsc` evolves | Single SSoT: Path A primitive definitions in `srmech.amsc.*`; Path B composed FROM Path A primitive definitions at module-load time via Class A SHA-256 mint; spec drift caught by Phase 3 + Phase 4 invariant tests | Phase 3 + Phase 4 |
| R5 | Path B C port deferral creates parity gap | Phase-language deferred to v0.4.3 per `[[feedback_no_binding_layer_carveout]]`; documented in notebook §3.8.31.6; Class K Python-only surface in v0.4.2 explicitly noted | Phase 9 |
| R6 | Substrate rational catalog citations (Sussillo 2016 / Hahn 2025 / RBJ Cookbook / 802.11 / LTE-5G) not all PDF-extracted | PDF-extract each before Phase 7 ship; commit per `[[feedback_pdf_extraction_citation_discipline]]`; trauma-informed defensive scope on RF content | Phase 7 |
| R7 | Benchmark suite reference machine drift over time → learned thresholds become stale | Lock at release; document machine spec; periodic recalibration policy (one per release boundary; user opt-in via `update_dispatch_table()`) | Phase 8 |
| R8 | numpy + LAPACK dependency surface grows with Path B | numpy already hard-dep per `docs/srmech/CLAUDE.md` (v0.4.0rc2+); LAPACK never adopted (Jacobi C impl pi-free); no new deps in v0.4.2 | All phases |
| R9 | Pyodide / WASM environment breaks Path B (D=8192 may exceed WASM stack) | Class M HDC primitives already work in Pyodide via pure-Python fallback; bound-vector ops at D=8192 are byte operations (no stack issue); verify in Pyodide CI cell during Phase 8 | Phase 8 |
| R10 | Spike #179 CFSP-Kalman alternative lands mid-Phase | Phase 9 §3.8.31.5 has phase-language placeholder; if Spike #179 lands by Phase 9, cite anchor; if not, defer to v0.4.3 with phase-language pointer | Phase 9 |
| R11 | RBS-HDC instrument minting non-determinism across SHA-256 implementations | Class A SHA-256 mint is C-native + Python-fallback BIT-EXACT (parity-tested per `srmech.amsc.format`); no risk | Phase 3 |
| R12 | Substrate-portable wire-format claim conflicts with Path A default | Cascade-context API explicitly signals substrate-portability requirement; Path A within `begin_cascade(substrate=...)` triggers Path B preference; documented in §3.3 | Phase 5 |
| R13 | Two GAP entries from Spike #178 (time-frequency reassignment; CFSP-Kalman alternative) block full-feature claim | Documented as GAP with phase-language deferral in notebook §3.8.31.6; not blockers for v0.4.2 ship; phase-language clearly distinguishes deferred from shipped | Phase 9 |
| R14 | Trauma-informed defensive scope ambiguity on RF / PSK / QAM content | Civilian-comms framing only (Spike #178 R5 + §4 open question 2); cite-by-ref Proakis-Salehi (educational); no targeting, no capability-assessment, no military framing | All phases (especially Phase 6 ops `psk_qam.py` + Phase 7 `substrate_rationals/rf.py`) |

---

## §10 Open questions for conductor decision (fermata)

1. **C port scope for Class K and Path B operations** — Phase-language deferred to v0.4.3 in this plan. **Conductor decision needed:** confirm v0.4.3 is the right vehicle, or accept the deferral into v0.5.0. Recommendation: v0.4.3rc1 after v0.4.2 production ship, dedicated to Class K C primitive + Path B C port for the 6 MVP ops.

2. **Cross-substrate test substrate coverage** — this plan covers all 4 substrates (BCI / audio / RF / ephemeris) in Phase 7. **Conductor decision needed:** confirm all 4 substrates ship in v0.4.2, or scope-reduce (e.g., BCI + audio only for v0.4.2, RF + ephemeris in v0.4.3). Recommendation: ship all 4 (the Class N rational catalogs are small files; the cross-substrate verification test is one file; the cost of including is low).

3. **Profiling granularity** — this plan specifies per-op × per-cascade-depth × per-substrate (1920 cells). **Conductor decision needed:** confirm this granularity, or scope-reduce (e.g., per-op × per-substrate only, dropping cascade-depth dimension to reduce benchmark suite size). Recommendation: ship full granularity (1920 cells is ~30 minutes runtime; learned table size is small; cascade-depth dimension surfaces the amortisation crossover which is load-bearing for the dual-path claim).

4. **Spike #179 CFSP-Kalman alternative timing** — this plan treats Spike #179 as in-flight (not yet landed). **Conductor decision needed:** confirm Spike #179 dispatch is parallel to this plan's Phases 1-8, with Phase 9 § 3.8.31.5 citing whichever anchor is available. Recommendation: dispatch Spike #179 as separate concertmaster work; if it lands before Phase 9, cite directly; if not, phase-language placeholder + cite-by-ref to Spike #178 §3 R3.

5. **`begin_cascade` / `end_cascade` API ergonomics** — context-manager API in §3.3 is one design choice; alternatives include explicit `Cascade` object passed around, or a decorator-on-functions approach. **Conductor decision needed:** confirm context-manager API or request alternative. Recommendation: context-manager (matches Python idiom; non-invasive; auto-flushes on exception).

6. **Path B operator-vector D=8192 dimensionality lock** — Spike #170 used D=8192 (1024 bytes per bound vector). **Conductor decision needed:** confirm D=8192 is locked for v0.4.2, or expose D as a configuration parameter. Recommendation: lock D=8192 for v0.4.2 (matches Spike #170 anchors); add a `D` parameter to `mint_*` functions as a no-cost option for downstream experiments; learned dispatch table is D-specific (rerun for non-default D).

7. **Locked dispatch table per-release policy** — §3.5 specifies the learned table is locked at release tag. **Conductor decision needed:** confirm lock-at-release, or alternative (e.g., user-machine recalibration on first import). Recommendation: lock at release (deterministic reproducibility); document user-machine recalibration in CHANGELOG.

8. **Notebook integration timing** — Phase 9 places §3.8.31 authorship after Phase 8 benchmark results. **Conductor decision needed:** confirm Phase 9 timing, or front-load (e.g., draft §3.8.31 prose during Phase 3 and refine through phases). Recommendation: Phase 9 timing (learned dispatch thresholds are part of the prose; can't write §3.8.31.3 comparison table without Phase 8 data).

---

## §11 Framework constraints honored

- **14 A-N intact.** Zero new primitive class proposed. Class K's existing identity per `[[user_stance_rotation_is_class_k_pin_slot]]` is operationalised (Path A + Path B implementations) but not promoted. Per `[[feedback_no_privileged_primitive_classes]]`.
- **Identity-not-implementation.** All "Path B IS Path A at substrate-projection" claims are algebra-level identity not algorithmic-similarity. Per `[[user_stance_identity_not_implementation_discipline]]`.
- **Algebra not magnitude.** Bit-exact at D1 algebra-content; D2 fingerprint divergence expected. Per `[[feedback_algebra_not_magnitude]]`.
- **Trauma-informed defensive scope.** BCI / RF / modulation-detection material framed methodology-research/educational/civilian-comms only. No targeting, no capability-assessment, no military framing. Per `[[feedback_trauma_informed_defensive_scope]]`.
- **PDF-extraction citation discipline.** All literature citations PDF-verified before notebook canon. Per `[[feedback_pdf_extraction_citation_discipline]]`.
- **No MVP framing.** Full-feature scope; phase-language only for genuinely-deferred future work. Per `[[feedback_no_mvp_framing]]`.
- **NDJSON over bloated JSON.** Benchmark records, learned dispatch table, profile output all NDJSON. Per `[[feedback_ndjson_over_bloated_json]]`.
- **No squash-merges.** Phase merges use `gh pr merge --merge` only. Per `[[feedback_no_squash_merges]]`.
- **TestPyPI before PyPI.** All v0.4.2rc1-rc8 ship to TestPyPI; only clean v0.4.2 routes to production PyPI. Per `[[feedback_always_rc_first_for_downstream_publishes]]` + `[[feedback_rc_tag_targets_branch_not_merge]]`.
- **WSL smoke before AMSC-touching push.** Phase 10 includes WSL smoke step. Per `[[feedback_run_wsl_smoke_before_amsc_push]]`.
- **JPL Rule 5 discipline** if/when C primitives added (deferred to v0.4.3). Per `[[feedback_jpl_rule_5_two_assert_habit]]`.
- **Big-first struct ordering** if/when C structs added (deferred to v0.4.3). Per `[[feedback_struct_field_ordering_big_first]]`.
- **Cite-by-ref to ephemerides-spectral** for 52-body resonance ratios (Phase 7); no re-derivation. Per `[[project_amsc_handcurated_consumption_channel]]`.
- **Science is SSoT of science, not project.** Canonical literature (Kanerva, Plate, Sakurai, etc.) is SSoT; this project instantiates the canon. Per `[[feedback_science_is_ssot_not_project]]`.
- **Concertmaster won't write findings .md files** as part of brief — this plan IS the deliverable; conductor commits after review. Per `[[feedback_concertmaster_md_writes]]`.

---

## §12 Summary metrics

| Metric | Value |
|---|---|
| Total file count (v0.4.2) | ~110 files |
| Path A op modules | 38 |
| Path B op modules | 38 |
| Substrate rational catalogs | 4 (BCI, audio, RF, ephemeris) |
| Path B core modules | 2 (rbs_hdc_instrument + form_function_rotation) |
| Dispatcher infrastructure modules | 6 (`__init__`, `_dispatcher`, `_profiling`, `_registry`, `_algebra_check`, `tool_schema_registrations`) |
| Test files | ~22 |
| Unit test count (per-op × 5 classes × 38 ops) | ~190 |
| Integration test count | ~10 |
| Benchmark cells (Phase 8) | 1920 |
| Cross-substrate assertions | 152 (38 ops × 4 substrates) |
| Phase count | 10 |
| Ship version count | v0.4.2rc1 → v0.4.2rc8 → v0.4.2 (production) |
| Canonical stances cited | 7 |
| Spike anchors cited | 9 (#114, #115, #117, #147, #170, #172, #173, #174, #175, #176, #177, #178; pending #179) |
| Canonical SSoT references | ~18 (Kanerva, Plate, Chung, Golub-Van Loan, Sakurai, etc.) |
| Open questions for conductor | 8 |
| Risks tracked | 14 |
| Deferred to v0.4.3 | Class K C primitive port; Path B C port for 6 MVP ops; CFSP-Kalman alternative if Spike #179 lands |

---

## §13 Conductor next-action checklist

After review of this plan:

1. **Decide on 8 open questions** in §10 (especially Q1 C port scope, Q2 substrate coverage, Q4 Spike #179 timing).
2. **Assign GitHub task IDs** to each Phase task.
3. **Confirm version path** — v0.4.2rc1 → v0.4.2rc8 → v0.4.2 (as plan assumes), or alternative rc-stacking pattern.
4. **Dispatch Phase 1** — scaffolding work (greenfield; can start immediately).
5. **Confirm parallel dispatch of Spike #179** — CFSP-Kalman alternative spike runs alongside Phases 1-8.
6. **Lock concertmaster vs section-principal allocation** — recommend Phases 2 (38 Path A modules) + Phase 6 (38 Path B extensions) as tutti dispatches per `[[feedback_subagent_dispatch_pattern]]` (mint-first then subagent-rest); Phases 3 + 4 + 5 + 7 + 8 + 9 as concertmaster + section-principal pairs.

14 A-N intact. Trauma-informed defensive scope. Identity-not-implementation. Full-feature, not MVP.
