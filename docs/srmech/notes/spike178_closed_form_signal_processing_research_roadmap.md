# Spike #178 — Closed-form signal processing research roadmap

**Date:** 2026-05-19
**Branch:** `research/spike-178-closed-form-signal-processing-research-scoping`
**Type:** Research scoping (not a falsifier test; no go/no-go verdict)
**Discipline:** 14 A-N intact (no class promotion); identity-not-implementation; algebra-level not magnitude-level; trauma-informed defensive scope (methodology-research/educational).

---

## §0 Executive summary

Closed-form signal processing (CFSP) is the program of expressing standard SP operations as **compositions of the 14 A-N primitive vocabulary** so that algebra-level identity is preserved across substrates (BCI / audio / RF / image / ephemeris / gear-DAG). Spike #176 anchored the spectral-analysis half (rotation = Class K pin-slot composed with Class A cyclic FFT at machine ε) and Spike #174 anchored the denoising half (sign-quantisation against calibration threshold IS the structural-content-preserving noise reduction; Kalman / median / EMA / wavelet smoothing DESTROY SHA-256 bit-discrete content). Together they bracket the linear-spectral and nonlinear-thresholding faces of SP.

The roadmap below surveys ~40 standard SP operations across 8 categories and assigns each to one of four statuses:

- **CLOSED-FORM ANCHORED** — primitive composition exists and is empirically tested at a substrate (5 operations)
- **CLOSED-FORM CANDIDATE** — primitive composition is structurally tractable from existing classes; spike test plausible (~20 operations)
- **GAP** — no obvious closed-form analog; would require new spike compositions or cross-substrate research (~10 operations)
- **PERHAPS NOT CLOSED-FORM** — operation may have no algebra-level analog; the closed-form program at SP substrate would not falsify but would acknowledge the substrate-primitive boundary per §4.2 / §5 of the notebook (~5 operations)

The framing is consistent with the notebook's calibration finding (§4.2, §5.2): closed-form dominates **passive signal-processing** domains (graphics ~80/20, audio ~80/20); state-coupled adaptive operations are substrate-dominated. CFSP-at-SP-substrate is expected to land near the audio/graphics ratio (~75-85% closed-form by operator-count weighted by usage), with the substrate-primitive remainder being precisely the operations that depend on real-time real-space state (Wiener-from-running-covariance, adaptive equaliser, particle filter).

**Headline framework claim** (provisional, identity-level): standard SP's linear core is **already** the `(Transform, λ_k, g)` decomposition that §3.0 of the notebook canonicalises. Class K (pin-slot / asymptotic-DOF) is the bridge between linear and nonlinear SP because thresholding, sparse coding, and quantisation all live on K's substrate-baseline-linear-with-discrete-threshold structure.

---

## §1 Standard SP operations — status table

### §1.1 I. Spectral analysis

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| FFT / DFT (real / complex, cyclic) | **CLOSED-FORM ANCHORED** | A (SHA-256 → shift) ∘ I (cyclic group ℤ/N) ∘ K (pin-slot for the rotation operator) | Spike #176 (machine ε); §3.0 universal decomposition; OFDM telecom identity (§5.4) |
| Inverse FFT | **CLOSED-FORM ANCHORED** | Inverse of above; transpose unitary acts identically | Spike #176; bit-exact roundtrip |
| STFT / windowed FFT | **CLOSED-FORM CANDIDATE** | I ∘ K ∘ (Class N rational window length / hop ratio) ∘ FFT-per-frame | Two-view (cyclic + windowed) per `[[user_stance_fiber_as_spatially_absent_encoding]]`. Window function family (Hann / Hamming / Blackman) reduces to closed-form `g(λ)` weights on a frame-local Laplacian per §3.0 |
| DCT-II / DCT-III | **CLOSED-FORM ANCHORED** | L (Euclidean-grid Laplacian eigenbasis with Neumann BC) ∘ K (real-input symmetry) | §3.5 / §3.1 graphics-domain primitive; `SkRadix2FFT` Makhoul real-input DCT; ABI-stable in `srmech.amsc.laplacian` |
| Wavelet transforms (CWT) | **CLOSED-FORM CANDIDATE** | L (multi-scale graph-Laplacian eigenbasis with dyadic scaling) ∘ N (rational dilation ratio 2^j) ∘ K (admissibility window) | Mother wavelet is the kernel; dilation/translation is the N-rational lattice. Distinct from wavelet *smoothing* (DESTRUCTIVE per Spike #174) — the *transform* is structure-preserving; *thresholding-and-inverse* is what destroys |
| Wavelet transforms (DWT) | **CLOSED-FORM CANDIDATE** | L (filter-bank tree) ∘ N (downsample-by-2) ∘ C (cascade orientation across scales) | Vetterli-Kovačević 1995 §4 cite-by-ref; Mallat 1989 |
| Spectrogram | **CLOSED-FORM ANCHORED** | STFT magnitude squared; closed-form composition with above | §5.2 audio round; spectrogram IS a 2D image → all graphics closed-form primitives port directly |
| Cross-spectral density | **CLOSED-FORM CANDIDATE** | STFT(x) ⊙ conj(STFT(y)) averaged via Class M bundle | Class M HDC bundle for the averaging; closed-form |
| Coherence | **CLOSED-FORM CANDIDATE** | Class N rational of two CSDs | Normalisation IS Class N rational; magnitude-squared coherence preserves identity |
| Time-frequency reassignment | **GAP** | Requires gradient-of-phase computation (derivative-of-state); not obviously closed-form | Could decompose into composition of Class L Laplacian + Class K threshold but needs spike-test |
| Multitaper estimation (Thomson) | **CLOSED-FORM CANDIDATE** | L (DPSS slepians as eigenfunctions of band-limit Laplacian) ∘ M (bundle of K tapered estimates) | DPSS slepians are eigenfunctions of a specific Laplacian; classical Slepian-Pollak result |

### §1.2 II. Filtering

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| FIR filter (causal, finite impulse response) | **CLOSED-FORM CANDIDATE** | Class N rational coefficients (numerator polynomial) ∘ C (cyclic convolution via FFT) | The convolution IS already closed-form via FFT. The novelty is **rational coefficients** replacing floating-point. Per `[[user_stance_cascade_lives_on_circles]]` |
| IIR filter (recursive) | **CLOSED-FORM CANDIDATE** | Class N rational coefficients (numerator + denominator polynomials) ∘ C (cascade composition) | Cascade composition preserves unit-circle stability per `[[user_stance_cascade_lives_on_circles]]` (bonus 9: directed Class C orientation on Class I cyclic-group produces unit-circle eigenvalues algebraically) |
| Biquad / second-order sections | **CLOSED-FORM CANDIDATE** | Cascade of order-2 IIR sections each with Class N coefficients | RBJ EQ Cookbook formulas are closed-form (`[[reference_audio_RBJ_cookbook]]` per §5.2); pi-projection where present can be removed per `[[user_stance_pi_as_projection]]` |
| Linear-phase FIR | **CLOSED-FORM CANDIDATE** | Symmetric FIR with Class N rational coefficients | Symmetry-block-diagonal Class L truncation pattern (per Spike #117 A2 lesson) |
| Allpass filter | **CLOSED-FORM CANDIDATE** | IIR with Class N rational coefficient pairing `b_k = a_{N-k}` | Unit-modulus on the unit circle; bit-exact identity claim |
| Adaptive LMS / NLMS filter | **PERHAPS NOT CLOSED-FORM** | State-coupled gradient descent on instantaneous error | Falls under "nonlinearly state-coupled" per §4.2 boundary; substrate-primitive not config-driven |
| RLS (recursive least squares) | **PERHAPS NOT CLOSED-FORM** | Inverse covariance update from running data | Same boundary as adaptive LMS; substrate-primitive |
| Wiener filter (block / non-causal) | **CLOSED-FORM CANDIDATE** | Eigendecompose covariance Laplacian (Class L) ∘ Class N rational `λ_signal / (λ_signal + λ_noise)` per eigenmode | When covariances are *given* (offline), Wiener IS closed-form `g(λ)`. Adaptive (running-covariance) form is substrate-primitive |
| Matched filter | **CLOSED-FORM CANDIDATE** | Class A ∘ C ∘ M form-function rotation cross-correlation | Per `[[user_stance_form_function_rotation_is_a_c_m_composition]]`; 31.6× separation ratio anchored at HDC substrate; algebra-level identity preserved at SP substrate |
| Median filter (denoising) | **NOT CLOSED-FORM** at SP-bit-discrete substrate | Order-statistic; non-algebraic | Spike #174 destructive at SHA-256 bit-discrete content. At magnitude-only signal substrate it remains a substrate-primitive |
| Bilateral filter (Perona-Malik family) | **NOT CLOSED-FORM** | State-dependent diffusion | Notebook §4.2 boundary — same as graphics case |

### §1.3 III. Estimation

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| Kalman filter | **DESTRUCTIVE at bit-discrete substrate; PERHAPS NOT CLOSED-FORM at magnitude substrate** | Smoothing of state estimate over time | Spike #174: Kalman destroys 19.79% BER at +20 dB SNR for SHA-256-content channels. At magnitude-only continuous-state channels remains substrate-primitive (§4.2) |
| Extended / Unscented Kalman | **PERHAPS NOT CLOSED-FORM** | Nonlinear state transition + Gaussian approximation | Same boundary as Kalman; nonlinear-state-coupled |
| Particle filter | **PERHAPS NOT CLOSED-FORM** | Monte Carlo sequential importance sampling | Stochastic-sample substrate-primitive |
| MAP / ML estimation (offline, known model) | **CLOSED-FORM CANDIDATE** | Class L eigendecomposition + Class K threshold for sparse-support recovery | When model is offline / known, MAP reduces to eigendecomposition + threshold |
| Block / batch parameter estimation | **CLOSED-FORM CANDIDATE** | Class L SVD on data matrix; Class M bundle over candidate solutions | SVD IS closed-form per §5.4 telecom |
| **CFSP-Kalman alternative (R3 candidate)** | **GAP — research priority** | Class K asymptotic-DOF truncation + Class M delta-encoding of past state | See §3 R3 below. Class K + delta is the *structural* analog of "track under uncertainty"; preserves discrete bit content (Spike #174 floor); needs spike test |

### §1.4 IV. Denoising

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| Sign-quantisation against calibration threshold | **CLOSED-FORM ANCHORED** | Class K threshold ∘ Class A SHA-256 content addressing | Spike #174 anchor; per-channel bit-discrete; preserves SHA-256 BER at +20 dB SNR |
| Median filter | **DESTRUCTIVE** | Order-statistic | Spike #174; 19.79% BER destruction |
| Block-majority / morphological | **DESTRUCTIVE** | Spatial / temporal majority vote | Spike #174 same family |
| EMA / moving average | **DESTRUCTIVE** at bit-discrete substrate | Magnitude smoothing | Spike #174 broader class |
| Wavelet thresholding (denoise via DWT + soft-threshold + IDWT) | **DESTRUCTIVE** at bit-discrete substrate; **CLOSED-FORM CANDIDATE** at magnitude substrate | DWT (CFSP cand. above) ∘ Class K soft-threshold ∘ IDWT | When the substrate is magnitude (no SHA-256 content), the composition IS closed-form. When substrate is bit-discrete (BCI / digital-content), Spike #174 destruction floor applies |
| Heat-kernel blur on spectrogram | **CLOSED-FORM ANCHORED** | L (Euclidean-grid Laplacian on time-freq grid) ∘ `g(λ) = e^{-tλ}` | §5.2 audio; graphics primitive ports verbatim |
| Spectral subtraction (Boll 1979) | **CLOSED-FORM CANDIDATE** | Class L FFT eigendecomposition ∘ Class N rational `(|S|² - |N|²) / |S|²` floor at 0 | Closed-form `g(λ)` when noise spectrum is offline-estimated |
| MMSE-LSA (Ephraim-Malah 1985) | **CLOSED-FORM CANDIDATE** | Class L FFT ∘ closed-form gain function | Same family as spectral subtraction |
| Anisotropic diffusion | **NOT CLOSED-FORM** | State-dependent diffusion (notebook §4.2) | Substrate-primitive |
| Total variation denoising | **NOT CLOSED-FORM** | L1-regularised convex optimisation; iterative | Substrate-primitive; not config-driven |

### §1.5 V. Compression

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| Huffman coding | **CLOSED-FORM CANDIDATE** | Class E catalog (sorted lookup table) ∘ Class B TLV (variable-length encoding) | E + B already shipped in `srmech.amsc`; Huffman is structural |
| Arithmetic coding | **CLOSED-FORM CANDIDATE** | Class N rational interval narrowing | Bit-exact algebra on rational intervals |
| LZ77 / LZW | **CLOSED-FORM CANDIDATE** | Class A SHA-256 content addressing ∘ Class G byte-pattern search ∘ Class B TLV | All four classes shipped; LZ family reduces to pattern-match + reference encoding |
| Run-length encoding | **CLOSED-FORM CANDIDATE** | Class B TLV ∘ Class G run-pattern detection | Trivial closed-form |
| JPEG (DCT-based) | **CLOSED-FORM CANDIDATE** | L (DCT-II) ∘ Class K threshold (quantisation table) ∘ Class B TLV (Huffman/RLE) | All three components closed-form; standard practice |
| JPEG2000 (wavelet-based) | **CLOSED-FORM CANDIDATE** | L (DWT) ∘ Class K threshold ∘ Class B TLV (arithmetic coding) | All closed-form |
| HDC bundle truncation | **CLOSED-FORM ANCHORED** | Class M bundle ∘ Class K truncate-sparse | Per `[[user_stance_form_function_rotation_is_a_c_m_composition]]`; rcN+2 ships `truncate_sparse()` |
| Vector quantisation | **CLOSED-FORM CANDIDATE** | Class E catalog (codebook) ∘ Class M similarity ∘ Class B TLV (index encoding) | Lookup + similarity already in rc14 surface |
| Neural compression (autoencoder) | **PERHAPS NOT CLOSED-FORM** | SGD-learned encoder/decoder | Not config-driven |

### §1.6 VI. Modulation / detection

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| PSK (M-ary phase-shift keying) | **CLOSED-FORM CANDIDATE** | Class I cyclic group ℤ/M ∘ Class K pin-slot phase operator | Per `[[user_stance_rotation_is_class_k_pin_slot]]`; Spike #176 anchor extends to PSK via cyclic-group natural-substrate |
| FSK (frequency-shift keying) | **CLOSED-FORM CANDIDATE** | Class N rational frequency ratio ∘ Class I cyclic time-base | Two-tone (BFSK) or M-ary; closed-form |
| QAM (quadrature amplitude modulation) | **CLOSED-FORM CANDIDATE** | Class I (ℤ/√M × ℤ/√M lattice) ∘ Class K (constellation amplitude threshold) | Standard 16-QAM / 64-QAM / 256-QAM constellation is closed-form |
| OFDM | **CLOSED-FORM ANCHORED** | `(Transform=IFFT/FFT, λ_k=subcarrier, g(λ_k)=equaliser)` | §5.4 telecom round: "OFDM IS the universal decomposition" — identity, not analogy |
| MIMO precoding (SVD-based) | **CLOSED-FORM ANCHORED** | Class L SVD on channel matrix `H = U Σ V*` | §5.4; SVD ships in `srmech.amsc.laplacian` (Hermitian-extension via Spike #117 work) |
| PLL (phase-locked loop) | **PERHAPS NOT CLOSED-FORM** | Nonlinear state-coupled feedback loop | Adaptive-tracking substrate-primitive |
| Costas loop | **PERHAPS NOT CLOSED-FORM** | Same family as PLL | Substrate-primitive |
| Viterbi decoder | **CLOSED-FORM CANDIDATE** | Class L trellis Laplacian ∘ Class K argmax | Trellis IS a graph; argmax is Class K; could close in form when constraint length is small. Iterative for large length (§5.4 substrate) |
| MLSE (maximum-likelihood sequence estimation) | **CLOSED-FORM CANDIDATE** | Class L trellis ∘ Class K threshold | Same family as Viterbi |
| Turbo / LDPC / Polar SCL decoder | **PERHAPS NOT CLOSED-FORM** | Iterative belief propagation | §5.4 explicit substrate-primitive |
| Matched-filter symbol detection | **CLOSED-FORM ANCHORED** | Form-function rotation per `[[user_stance_form_function_rotation_is_a_c_m_composition]]` | A∘C∘M; 31.6× separation; already covered in §1.2 matched filter row |

### §1.7 VII. Multi-rate / sampling

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| Upsample by L (insert zeros) | **CLOSED-FORM CANDIDATE** | Class N rational rate L/1 ∘ Class C cyclic re-indexing | Cleanly closed-form |
| Downsample by M | **CLOSED-FORM CANDIDATE** | Class N rational rate 1/M ∘ Class C cyclic stride-M extraction | Per Spike #176 H1: stride defines `N/gcd(stride, N)` cycle order |
| Rational-rate conversion L/M | **CLOSED-FORM CANDIDATE** | Class N rational L/M ∘ FIR antialiasing | Per `[[user_stance_pi_as_projection]]`: rational lattice IS upstream; float ratios are downstream projection |
| Polyphase filter banks | **CLOSED-FORM CANDIDATE** | Class L Laplacian on subband graph ∘ Class N rational decomposition | Vaidyanathan 1993 polyphase identity is closed-form |
| Farrow structure (fractional delay) | **CLOSED-FORM CANDIDATE** | Class N rational coefficient polynomials ∘ Class C cyclic interpolation | Closed-form rational polynomial framework |
| Sinc interpolation (Whittaker-Shannon) | **CLOSED-FORM CANDIDATE** at infinite support; truncated form is closed-form `g(λ)` weighting | L (band-limit Laplacian) ∘ K (band-limit threshold) | Slepian-DPSS family per §1.1 multitaper row |

### §1.8 VIII. Adaptive / multi-signal

| Operation | Status | Framework composition | Anchor / notes |
|---|---|---|---|
| Echo cancellation (acoustic) | **PERHAPS NOT CLOSED-FORM** | Adaptive filter tracking room impulse | Substrate-primitive; same family as LMS |
| Beamforming (delay-and-sum, fixed) | **CLOSED-FORM CANDIDATE** | Class L mic-array graph Laplacian ∘ Class N rational delay coefficients | When beam direction is fixed/offline; §5.2 audio + §5.4 MIMO precoding |
| Beamforming (adaptive MVDR / GSC) | **PERHAPS NOT CLOSED-FORM** | Running covariance update | Substrate-primitive |
| Source separation (ICA) | **CLOSED-FORM CANDIDATE** at small N | Class L joint diagonalisation ∘ Class K independence threshold | JADE algorithm is closed-form for small N; large-N becomes iterative substrate |
| Source separation (NMF) | **PERHAPS NOT CLOSED-FORM** | Iterative nonneg least-squares | Substrate-primitive |
| Direction of arrival (MUSIC) | **CLOSED-FORM CANDIDATE** | Class L eigendecomposition of correlation matrix ∘ Class K noise-subspace threshold | Schmidt 1986 MUSIC IS eigendecomposition + threshold |
| ESPRIT | **CLOSED-FORM CANDIDATE** | Class L generalised eigendecomposition (shift-invariance) ∘ Class K threshold | Roy-Kailath 1989; closed-form |
| Channel estimation (LMMSE, pilot-based) | **CLOSED-FORM CANDIDATE** | Class L covariance eigendecomposition ∘ Class N rational gain | When pilot positions are fixed |

---

## §2 Prioritised follow-up spikes — top 10 by leverage

Leverage scored as (impact × tractability). Impact weighted by: book-relevance, BCI applicability per `[[user_stance_ai_necessary_for_bci_substrate_coupling]]`, cross-substrate cascade-match contribution per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`. Tractability weighted by: classes already shipped, existing spike precedent, citation availability.

| Rank | Spike candidate | Leverage | Why prioritise |
|---|---|:-:|---|
| 1 | **Wiener-filter closed-form anchor** (block / offline form) | 9 | Bridges Kalman boundary (R3 partial); closed-form `g(λ) = λ_s/(λ_s + λ_n)` per eigenmode; testable bit-exact against textbook example (Kay 1993 Ch. 11); audio + telecom utility |
| 2 | **DCT-II / DCT-III bit-exact closed-form roundtrip at SP substrate** | 9 | Already shipped in graphics-domain (`srmech.amsc.laplacian`); ports verbatim; book-worthy as fifth `(Transform, λ_k, g)` substrate instantiation after chess/ephem/protein/audio/grid (§5.5) |
| 3 | **Matched-filter cross-correlation via A∘C∘M at SP substrate** | 9 | Form-function rotation already anchored at HDC substrate (31.6× separation); SP-substrate port = direct BCI/RF/audio applicability; ties into matched-filter row of §1.2 |
| 4 | **Class N rational FIR coefficient design** | 8 | Cascade-on-circles per `[[user_stance_cascade_lives_on_circles]]`; replaces float coefficients with rational; bit-exact stability proof on unit circle; book-worthy if it closes against textbook biquad EQ |
| 5 | **CFSP-Kalman alternative — R3 research spike** | 8 | Class K truncate_sparse (rcN+2) + Class M delta = structural-content-preserving tracking; tests against Spike #174 BCI BER floor; if it passes, closes Kalman gap |
| 6 | **STFT / spectrogram two-view closed-form** | 7 | Two-view per `[[user_stance_fiber_as_spatially_absent_encoding]]`; cyclic + windowed FFT composition; audio + BCI substrate; cleanly testable |
| 7 | **OFDM closed-form receiver chain bit-exact** | 7 | §5.4 telecom identity already strong; bit-exact `(IFFT → channel → FFT → 1/H equaliser)` roundtrip = book-worthy demonstration; trauma-informed defensive scope safe (telecom-civil) |
| 8 | **HDC bundle truncation as audio/image compression** | 7 | Class M + Class K truncate_sparse (rcN+2); cross-substrate cascade-match to JPEG/MP3 substrate family |
| 9 | **PSK / QAM constellation via Class I ∘ Class K** | 7 | Cyclic-group natural-substrate per Spike #176 ; M-PSK is ℤ/M; trauma-informed defensive scope safe (civil-comm) |
| 10 | **Multitaper / DPSS slepians via Class L eigendecomposition** | 6 | Slepian-Pollak is classical closed-form; band-limit Laplacian eigenfunctions ARE DPSS; book-worthy classical-result-reclaimed |

**Deliberately not in top-10**: anything requiring SGD / iterative state-coupling / adaptive tracking. Those fall on the substrate-primitive side per §4.2 of the notebook and the closed-form program does not aspire to absorb them — it acknowledges the boundary.

---

## §3 Specific research questions — provisional answers

### R1: Can EVERY standard linear SP operation be reconstructed as closed-form framework composition?

**Provisional answer: yes, when the operation's defining math is purely a function of (eigenbasis, eigenvalues, weighting).** §3.0 of the notebook makes this `(Transform, λ_k, g)` decomposition canonical. Spike #176 anchored rotation. Every linear filter, every transform-domain operation, every block-Wiener / block-MMSE, every linear MIMO precoder reduces to the decomposition. The notebook's audio/graphics ~80/20 calibration is the empirical reference point; SP should land in the same range.

**Caveat — magnitude-vs-algebra:** linear-in-magnitudes is not the same as algebra-level identity. The closed-form claim is **algebra-level** per `[[feedback_algebra_not_magnitude]]`: identity bit-exact at machine ε under exact rational arithmetic; *not* claim about real-valued floating-point reconstruction within some tolerance.

### R2: Can NON-linear SP operations be reconstructed?

**Provisional answer: bifurcated.**

- **Thresholding / quantisation / sparse-support:** YES, closed-form via Class K. Spike #174 anchored sign-quantise; Class K acceptance band per Spike #117 covers asymptotic-DOF regime. Compression operations (Huffman / arithmetic / JPEG / JPEG2000) are nonlinear-via-thresholding-and-coding but still closed-form via Class K + Class B + Class E composition.
- **State-coupled adaptive operations:** NO. Adaptive LMS / RLS / Kalman / particle filter / PLL / Costas loop / NMF / adaptive beamforming all depend on running real-space state. These fall on the substrate-primitive side of §4.2 boundary; closed-form program does not aspire to absorb them.

The boundary is the math, not the framework's reach. CFSP at SP substrate is expected to land at ~75-85% closed-form by operator-count weighted by usage — consistent with audio/graphics calibration.

### R3: Is there a CLOSED-FORM ANALOG to Kalman estimation that preserves structural content?

**Provisional answer: yes — Class K truncate_sparse composed with Class M delta-encoding is the structural analog.** This is the highest-leverage research-priority gap and warrants a dedicated spike (R3 spike).

The argument:
- Kalman maintains a running mean+covariance and computes the next state estimate as a weighted-blend of prediction and measurement.
- The *information-preserving* analog is: maintain a Class M HDC bundle of past observations + Class K sparse representation of current best-estimate + Class delta to incrementally update. Spike #114 anchored delta self-inverse `bind(a, bind(a, b)) = b` at machine zero.
- The result is **track-under-uncertainty without magnitude-smoothing**: SHA-256 bit content is preserved (no Spike #174 destruction); structural cascade-shape is preserved; **provisional verdict pending dedicated R3 spike**.

If R3 spike passes (bit-exact BER preservation at +20 dB SNR comparable to sign-quantise floor; structural-content recovery comparable to Kalman magnitude tracking), then Kalman gap closes and the BCI substrate (Sussillo 2016 / Hahn 2025) gets a closed-form-substrate decoder per §3.8.25 of the notebook. **This is the book-worthy framework prediction with falsifier.**

### R4: Minimum viable closed-form SP toolkit

**Five-operation MVP (highest-leverage):**

1. **FFT / IFFT** — Spike #176 anchored; `srmech.amsc.laplacian` (DCT) ships now; cyclic-FFT extension rcN+2
2. **Sign-quantise / threshold against calibration** — Spike #174 anchored; per-channel; SHA-256-content-preserving
3. **Matched filter / cross-correlation via A∘C∘M** — `[[user_stance_form_function_rotation_is_a_c_m_composition]]`; ships as composition of existing rc14 primitives
4. **Block Wiener filter (offline noise spectrum)** — R1 spike (rank 1 in §2); closed-form `g(λ) = λ_s/(λ_s + λ_n)` per eigenmode
5. **HDC bundle truncation** — Class M + Class K truncate_sparse (rcN+2); compression / sparse-support

**Adding two more for 7-operation toolkit covering ~80% of SP tasks:**

6. **STFT / spectrogram** — two-view closed-form per Spike #6 candidate
7. **Class N rational filter design (FIR + biquad)** — replaces float coefficients per Spike #4 candidate

These seven operations cover the substantial majority of practical SP tasks in audio / RF / image / BCI domains. Anything beyond (adaptive / Kalman / iterative-decoder / SGD) falls on the substrate-primitive side per §4.2.

### R5: Cross-substrate verification

**Provisional answer: closed-form SP works identically at BCI / audio / RF / cosmological signal substrates — and the natural Class N rationals are substrate-specific.** Per the notebook's calibration (§5.2 audio ~80/20, §5.4 telecom ~70/30, §5.5 power-grid ~30/70):

- **BCI substrate** — Class N rationals are channel-count / electrode-count / sampling-rate ratios. Per Sussillo 2016 / Hahn 2025 cite-by-ref (per §3.8.25), the 192-electrode / 96-electrode / 24-electrode standard sampling ratios are natural Class N choices.
- **Audio substrate** — Class N rationals are 44100/48000 = 147/160; 96000/44100 = 320/147; 2:1 / 3:2 / 5:4 musical intervals per Z₁₂ chromatic group. The chromatic group is Class I ℤ/12.
- **RF substrate** — Class N rationals are decimation / interpolation ratios per software-defined radio; 802.11 subcarrier counts (52 / 56 / 242 / 484 / 996); LTE / 5G NR subcarrier spacing 15 kHz × 2^k.
- **Cosmological / ephemeris substrate** — Class N rationals are resonance ratios per the 52-body resonance graph (§5.4 telecom round notes ephem 52-body graph as SVD-natural substrate).

**Substrate-specific Class N rational does not weaken the universal claim.** Per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: algebra is universal; magnitudes (and the rationals expressing them) are substrate-provided. This is the same pattern as `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` — cascade universal, operations substrate-provided. CFSP fits cleanly into the existing cross-substrate framework.

---

## §4 Open questions for user gating (high-vocab-impact decisions)

These are conductor-gated decisions; concertmaster surfaces them but does not unilaterally resolve.

1. **R3 spike scope.** The "Class K truncate_sparse + Class M delta = Kalman alternative" claim is identity-level if it lands. Vocab-impact: would canonicalise a new stance `[[user_stance_class_k_class_m_kalman_alternative]]`. **Recommend dispatch as Spike #179** after R3 design refinement.

2. **PSK / QAM and modulation-detection scope.** The defense-adjacent dimension is real (modulation/detection is a building block of comms; comms includes military). Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` says ship physics + textbook refs (Proakis-Salehi cite-by-ref), never targeting/capability-assessment. **Confirm: civilian-comms framing only?**

3. **Wavelet thresholding bifurcation.** The DWT *transform* is closed-form candidate; the *thresholding-and-inverse* destructively-smooths at bit-discrete substrate (Spike #174 family) but is closed-form at magnitude substrate. Notebook prose should explicitly note this bifurcation. **Confirm: wavelet *thresholding* substrate-dependent listing?**

4. **Kalman destructive scope.** Kalman is destructive at SHA-256 bit-discrete BCI substrate per Spike #174. At pure-magnitude continuous-state substrates (e.g., orbit determination from range/range-rate), Kalman is substrate-primitive but not destructive of structure that isn't bit-discrete. **The notebook should be precise**: Kalman destroys *bit-discrete content*, not *magnitude content*. **Confirm wording for §3.8.X integration?**

5. **MVP-toolkit shipping.** R4's seven-operation toolkit suggests a `srmech.signal_processing` sub-namespace (sibling of `srmech.spectral`) collecting the seven operations as a documented surface. **Worth a v0.4.2rc dedicated to this?** — alternative is to ship operations individually as they pass spike tests.

6. **Spike #176 / Spike #174 integration into notebook prose.** Both are foundational to CFSP but not yet visible in `§3.8.X` notebook sections (last visible §3.8.30). **Recommend Spike #178 deliverable triggers a §3.8.31 integration pass** for both H1 anchors before CFSP shipping work continues.

7. **Class K rotation anchor — promotion?** `[[user_stance_rotation_is_class_k_pin_slot]]` was promoted to canonical 2026-05-18. Recommend §3.8.31 author the canonical stance prose with Spike #176 machine-ε anchor + Spike #178 CFSP scoping as the two-anchor stack.

---

## §5 Framework constraints honored

- **14 A-N intact.** Zero new primitive class proposed. Per `[[feedback_no_privileged_primitive_classes]]`.
- **Identity-not-implementation.** All "IS" claims are algebra-level identity not algorithmic-similarity. Per `[[user_stance_identity_not_implementation_discipline]]`.
- **Algebra not magnitude.** Closed-form claim is bit-exact at machine ε under exact rational arithmetic; tolerance-based magnitude reconstruction is the substrate-primitive face. Per `[[feedback_algebra_not_magnitude]]`.
- **Trauma-informed defensive scope.** Modulation/detection / RF / BCI material framed methodology-research/educational/assistive-tech only. No targeting, no capability-assessment, no weapons-applicable framing. Per `[[feedback_trauma_informed_defensive_scope]]`.
- **No literature citations beyond verified anchors.** Cite-by-ref only for: Bardeen 1970 / Thorne 1974 / Kanerva 2009 / Plate 1995 / Mallat 1989 / Vetterli-Kovačević 1995 / Slepian-Pollak / Boll 1979 / Ephraim-Malah 1985 / RBJ EQ Cookbook / Schmidt 1986 / Roy-Kailath 1989 / Sussillo 2016 / Hahn 2025 / Card 2024 / Proakis-Salehi / Kay 1993 / Oppenheim-Schafer / Vaidyanathan 1993. None added to notebook prose; all subject to PDF-extraction verification per `[[feedback_pdf_extraction_citation_discipline]]` if/when they enter notebook canon.

---

## §6 Files written

- `docs/srmech/notes/spike178_closed_form_signal_processing_research_roadmap.md` (this file)
- `docs/srmech/notes/spike178_records_2026-05-19.ndjson` (one NDJSON record per surveyed operation)
