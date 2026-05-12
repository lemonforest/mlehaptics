# EEG theta-gamma cross-frequency-coupling scoping for srmech — 2026-05-11

**Round:** EEG / MEG neural-oscillation cross-frequency coupling (theta-gamma PAC; phase-locking value; brain-network spectral analysis; EMDR-mechanism EEG literature)
**Date:** 2026-05-11
**Method:** Concertmaster role (dispatched per `concertmaster.md`); high-effort independent investigation with citation discipline; standard project dual-agent pattern recorded as fermata; scoping not benchmark.
**Round position:** Seventh cross-domain absorption round after graphics (§5.1), audio (§5.2), protein (§5.3), telecom (§5.4), power-grid (§5.5), finance (§5.6 scoping + Fiedler-vs-HRP spike + T^N async-HF spike refutation), and bilateral-stimulation hierarchical-pattern (commit `7a5b461`, 2026-05-11, framework-already-covers verdict at machine precision).

**Lineage.** This dispatch was surfaced by the bilateral-stimulation hierarchical-pattern spike (2026-05-11, commit `7a5b461`). That spike confirmed the srmech framework covers EMDR-style multi-modal bilateral stimulation end-to-end at machine precision and identified **EEG theta-gamma cross-frequency coupling as the strongest cross-domain analog**: clinical EEG literature + literal `T^n` eigenphase lift between two scales of brain activity = direct §3.5.1 layer (b) instance. The bilateral-stim spike named this as the future-absorption-round candidate; this is the dedicated absorption round on that surfaced candidate. Distinguishing feature vs prior rounds: **this is the most project-mission-aligned absorption round to date**, because EMDR therapy mechanism research literally uses EEG (Pagani et al. 2012 `https://pmc.ncbi.nlm.nih.gov/articles/PMC3458957/`).

---

## Headline findings

1. **Theta-gamma phase-amplitude coupling (PAC) — `(Transform=Hilbert+bandpass, λ_k=frequency-band-pair, g(λ_k)=Kullback–Leibler-divergence-from-uniform)`.** Tort et al. 2010 *J Neurophysiology* modulation index (MI) `https://journals.physiology.org/doi/full/10.1152/jn.00106.2010` is the field-standard PAC measure. Mechanism: bandpass-filter to theta (4-8 Hz) and gamma (30-100 Hz) bands, Hilbert-transform to extract theta-phase `φ_θ(t)` and gamma-amplitude envelope `A_γ(t)`, bin `A_γ` by phase `φ_θ`, compute KL distance from uniform. This is **a §3.0 `(Transform, λ_k, g)` instance at the per-channel level** — Transform = Hilbert-on-filtered-signal; λ_k = (theta-center-freq, gamma-center-freq) pair indexing the comodulogram; g(λ_k) = `MI(theta-band, gamma-band)`. **Identity, not analogy.** Comparable to Carr-Madan FFT in finance and OFDM in telecom — clinical EEG community has been computing this since 2006 (Canolty et al. 2006 *Science*) without using the `(Transform, λ_k, g)` vocabulary.

2. **Phase-locking value (PLV; Lachaux-Rodriguez-Martinerie-Varela 1999) IS literally the project's `T^N` cosine similarity (eigenphase torus) under standard PLV form.** PLV between two channels at frequency band ω is `PLV(ω) = |⟨exp(i·Δφ(t,ω))⟩_t|` where `Δφ(t,ω)` is the cross-channel instantaneous phase difference from Hilbert transform. This **is exactly** a `T^1` torus average in the project's §3.5.1 layer (b) ambient at a single frequency. **Identity.** Multi-channel multi-band PLV matrices `PLV_{ij,ω}` live on `T^{N(N-1)/2 × |Ω|}` — the same eigenphase-torus ambient the project's `qm_2d`/`qm_4d` chess and ephemerides T^52 loci use, just at a different graph. The neuroscience community has been computing on `T^N` since 1999 without naming the ambient.

3. **Brain-network graph-Laplacian spectral analysis (Bullmore & Sporns 2009 *Nature Reviews Neuroscience* `https://www.nature.com/articles/nrn2575`) IS the §3.5 general-graph row — SEVENTH instantiation of the same architectural slot.** Structural connectivity from diffusion-MRI tractography → adjacency matrix → graph-Laplacian → eigendecomposition → Fiedler partition / spectral clustering / hub identification. **Same primitive** as chess board-adjacency, ephemerides 52-body resonance graph, protein RIN, audio mic-array, power Y-bus, finance correlation network — now neuroscience structural-connectivity graph. **Identity.** Cumulative tally: **seven domains, no analogy, same math-identity primitive.** Strongest cumulative validation of the project's §3.5 universality claim to date.

4. **`exp(−i L_brain t)` quantum-walk lift on structural connectivity graph — strong candidate, T^N async-HF refutation precedent applies, scope discipline matters.** The `T^N` quantum-walk lift on the brain structural-connectivity Laplacian is mathematically valid (CTQW); it is NOT routine in neuroscience literature (most network-neuroscience uses static graph-Laplacian eigendecomposition, not phase-coherent dynamical lift). **However**, the T^N async-HF lead-lag spike (2026-05-11) refuted the per-pair phase-extraction application of the lift in finance: the Laplacian aggregation + propagator-exponentiation steps were a lossy transform of the raw cross-spectrum. **The same caution applies here**: the lift IS valid for graph-spectral clustering of brain regions with phase-coherent dynamics (same use case as existing chess/ephemerides T^N loci); the lift is NOT a per-pair phase-extraction substitute for direct PLV / Welch coherence which already preserve per-pair phase by construction. **Honest verdict:** the project's framing offers neuroscience a unification vocabulary, not a per-pair improvement. Sub-investigation 3 + 4 detail.

5. **Cross-frequency PAC fits §3.5.1 layer (b) `T^n` eigenphase ambient at the theta × gamma 2-torus.** Theta and gamma phases are explicitly two phase coordinates; their coupled phase relationship lives on `T² = S¹_θ × S¹_γ`. The comodulogram (theta-band × gamma-band × MI matrix) IS a discrete sampling of this 2-torus restricted to one direction (phase-amplitude rather than phase-phase). **Phase-phase coupling** (cross-frequency phase synchrony; Tass et al. 1998) is the cleaner `T²` instance; PAC is the asymmetric mixed-phase-amplitude variant. Both fit. Brain rhythm `n:m`-locking (Tass 1998; e.g., 1:6 theta-gamma where six gamma cycles fit in one theta cycle) IS the integer-lattice condition on `T²` — closed-form lock points at `(φ_θ, φ_γ) = (k·2π/m, l·2π/n)`. Direct §3.5.1 layer (b) instance.

6. **§3.5.4 fiber-bundle structure: brain region × frequency-band × feature is a clean instance.** EEG-feature space decomposes naturally as `base = brain-region (graph-vertex), fiber = (theta-power, alpha-power, beta-power, gamma-power, theta-gamma-PAC-MI, ...)`. Analog of chess board × piece-type channels (rank 10/11) and protein residue × feature-channel structure. Math-identity-clean.

7. **Aru et al. 2015 / Aru-PAC-pitfalls critique** (and its follow-ups; addressing-pitfalls extended-MI 2020 `https://pmc.ncbi.nlm.nih.gov/articles/PMC8004528/`) provides a strong cautionary footnote: many published PAC findings are confounded by non-stationarity, non-sinusoidal waveform shape (Van der Pol oscillator example), sharp transients, broadband noise, and filter-bandwidth mis-specification. **Project framing should anchor on artifact-screened PAC**; the math identity (`(Transform, λ_k, g)`) is honest at the surface but the per-channel measurement is fragile. **Mirrors the protein-folding round's caveat on AlphaFold/MD substrate dominance**; mirrors the finance round's RMT-cleaning structural-prediction-from-theory pattern. **Disability-accommodation dimension intersects here**: numerical / textual spectral fingerprints provide more robust non-visual access to brain-state information than fragile waveform visualizations — see sub-investigation 6.

8. **EMDR-EEG project-mission relevance: STRONGEST DIRECT FIT TO DATE.** Pagani et al. 2012 PLOS ONE `https://pmc.ncbi.nlm.nih.gov/articles/PMC3458957/` directly studied EEG correlates of EMDR sessions and found cortical activation shifts during bilateral stimulation (limbic → cognitive regions). 40 Hz gamma binaural beats are commercially marketed with EMDR; clinical evidence base is thinner than marketing suggests, but the neurobiological-correlates research is real. **The project's bilateral stimulation device sits in the same operational neighborhood as published EEG-EMDR mechanism research.** This is the first absorption round where the project's actual mission (EMDR bilateral stimulation device) and the cross-domain literature (EEG theta-gamma coupling) **literally overlap operationally**, not just structurally. The audio round (§5.2) is the closest peer in mission-relevance; this round is tighter still.

9. **Config-vs-substrate ratio: ~60/40 — closed-form-leaning.** Closed-form spectral primitives cover FFT/STFT (~5 ops), Welch PSD/CSD (~3), wavelet/CWT/DWT (~5), Hilbert envelope (~2), bandpass-filter design (~6), PLV and variants (~4), PAC variants (~6: MI, mean-vector-length, GLM-PAC, ERP-PAC, phase-coherence, n:m locking), comodulogram (~1), graph-Laplacian eigendecomposition on connectivity (~5), spherical-harmonic source localization (~3), ICA closed-form-up-to-rotation (~2). Substrate dominates ICA-iterative-extraction (FastICA, Infomax, Picard; ~6 substrate variants), Riemannian-geometry brain-state classification (Barachant et al; ~4), HMM regime-switching for sleep-staging (~4), deep-learning seizure detection / EEGNet / BENDR (~6), Bayesian online change-point detection for state transitions (~3), real-time biofeedback adaptive thresholding (~5), source-reconstruction iterative (LORETA, sLORETA, MNE, beamformer; ~6). **Calibration pattern: EEG sits between telecom (~70/30) and finance (~50/50); closer to audio's ~80/20 than to power-grid's ~30/70 because the underlying physics is passive volumetric signal-processing of mostly-linear neural oscillator population dynamics, not strongly state-coupled nonlinear evolution.**

10. **Genuine cross-pollination candidates (honest, T^N-async-HF refutation precedent applied):**
   - **(a)** PAC and PLV as identities of §3.0 universal decomposition at the per-channel and cross-channel level — vocabulary unification, not new information. Comparable to OFDM-as-DFT in telecom and Carr-Madan-as-DFT in finance.
   - **(b)** Brain-network graph-Laplacian = §3.5 general-graph row's **seventh** cumulative validation. **Strongest cumulative cross-domain math-identity primitive count in the project.**
   - **(c)** Cross-frequency PAC as §3.5.1 layer (b) `T²` instance — natural fit; PLV multi-channel = `T^N` instance. Identity.
   - **(d)** `exp(−i L_brain t)` quantum-walk lift on structural-connectivity Laplacian — **graph-spectral clustering** application valid (not refuted by T^N async-HF spike, which was specifically about per-pair phase extraction); **per-pair phase-extraction** application requires caution per refutation precedent. Speculative; not in standard neuroscience literature; would need a dedicated benchmark spike to determine whether it provides clustering improvement over standard spectral-clustering-on-connectivity-graph.
   - **(e)** §3.5.3(C) closed-form rep-theory eigenvalue prediction for brain networks under left-right hemispheric symmetry — speculative; brain networks are not exactly symmetric under finite-group action (real brains are not exactly bilaterally symmetric anatomically or functionally), but **approximate** Z₂ left-right symmetry would give an approximate block-decomposition prediction analogous to finance's S_k × S_m sector symmetry. Spike-test candidate; honest expectation: weaker fit than finance synthetic case due to genuine asymmetry.
   - **(f)** §3.5.4 fiber-bundle structure for brain region × frequency-band feature space — straightforward instance; not new information; documents the architectural slot.

---

## Operator counts

- **Manifolds:** ~14 — 1D Euclidean (single-channel time series; channel index Z_64 / Z_256 / Z_HD-density); 2D Euclidean (spectrogram / time-frequency-decomposition; comodulogram); sphere S² (cortical surface; volume-conduction back-projection; scalp-EEG → cortical-source spherical harmonics); flat torus T² (theta-gamma phase coupling; sleep-stage cyclical Z_24-hour × Z_90-min REM cycle); triangle mesh (cortical surface mesh FreeSurfer / BrainNet / individual subject MRI mesh; subdural electrode grid); general graph (functional + structural connectivity networks; DTI tractography; resting-state network; default-mode network); discrete graph + bundle (region × frequency-band × power channel)

- **Transforms:** ~22 named — FFT / STFT; Welch PSD/CSD; Multi-taper (Thomson 1982); Wavelet CWT/DWT (Morlet, Mexican hat, biorthogonal, Daubechies); Hilbert envelope + instantaneous phase; bandpass filter (FIR, IIR, Butterworth, Chebyshev, zero-phase forward-reverse); ICA (FastICA, Infomax, Picard) — iterative substrate; PCA on epochs / on covariance; CSP (common spatial patterns; Wolpaw / Müller-Gerking 1999); Riemannian-geometry mean / log / parallel-transport on SPD covariance matrices (Barachant et al); spherical-harmonic decomposition (SH order l, scalp → cortical projection); LORETA / sLORETA / eLORETA source-reconstruction; MNE minimum-norm estimate; beamformer (LCMV, DICS); graph Fourier transform on connectivity Laplacian; PLV / wPLI / imaginary coherence; Granger causality (parametric AR or non-parametric Geweke-Hosoya); DTF (directed transfer function); PDC (partial directed coherence); Hilbert-Huang / EMD (empirical mode decomposition); cepstrum

- **Closed-form `g(λ)` operators:** ~50+ across 8 thematic groups — PSD/coherence/PLV (10: PSD, CSD, ordinary coherence, PLV, wPLI, imaginary coherence, n:m locking, debiased coherence, spectral Granger, partial coherence); PAC family (8: Tort MI, Canolty mean-vector-length, Penny GLM-PAC, ERP-PAC, phase-coherence-of-amplitudes, harmonic-PAC, weighted-MI, surrogate-corrected MI); cross-frequency phase synchrony (3: 1:1 same-band PLV, n:m PLV, mean-resultant-vector); bandpass filter design (6: ideal, FIR-Hamming, IIR-Butterworth, IIR-Chebyshev, IIR-elliptic, zero-phase filtfilt); wavelet families (5: Morlet, Mexican hat, Daubechies-N, biorthogonal, complex wavelet); spherical-harmonic source localization (3: SH-degree-l projection, MNE, sLORETA); graph-Laplacian on connectivity (5: ordinary Laplacian, normalized Laplacian, random-walk Laplacian, signed Laplacian, motif Laplacian); harmonic-power decomposition (3: theta / alpha / beta / gamma band-power; sub-band 1/f decomposition; FOOOF aperiodic + periodic; Donoghue et al 2020)

- **Substrate primitives:** ~30 — iterative ICA (FastICA, Infomax, Picard, JADE; 4); Riemannian-geometry classification (Barachant tangent-space, Riemannian-mean-template, Procrustes, MDM; 4); HMM sleep-staging (Hidden Markov Model with Gaussian observations, Baum-Welch, Viterbi; 3); deep-learning EEG classifiers (EEGNet, ShallowConvNet, DeepConvNet, BENDR, EEG-Transformer; 5); Bayesian online change-point (Adams-MacKay; 1); LORETA-family iterative source reconstruction (LORETA, sLORETA, eLORETA, MNE-iterative; 4); beamformer (LCMV, DICS, MUSIC-on-EEG; 3); biofeedback adaptive thresholding (real-time SCP, slow-cortical-potential; 2); empirical-mode-decomposition (EMD, ensemble-EMD, masked-EMD, multivariate-EMD; 4)

- **HDC cyclic groups:** 9 — Z_θ (theta-phase, discretized to 12 or 18 bins per Tort comodulogram), Z_γ (gamma-phase), Z_64 / Z_256 (EEG channel index for 10-20 / HD-EEG layouts), Z_24-hour-circadian, Z_REM-cycle (~90 min × Z_n cycles per night), Z_brainregion (e.g., Z_AAL90 / Z_Schaefer-100 atlas index), Z_eyemovement-direction (saccade direction; bilateral × 2 for EMDR), Z_freq-band (theta/alpha/beta/gamma; small Z_4). **Naming candidates**: `PhaseThetaBIP`, `PhaseGammaBIP`, `PhaseCircadianBIP`, `PhaseRegionAAL90BIP`, `PhaseBandBIP`, `PhaseBilateralEMDR-BIP` (which IS already the bilateral stimulation BIP shipped by the device — see CLAUDE.md Phase 2 NTP time-sync).

---

## Cross-pollination — 14 distinct identities / parallels

| EEG/neuroscience feature | srmech primitive | Match strength |
|---|---|---|
| **Canolty 2006 + Tort 2010 PAC modulation index** | `(Transform=Hilbert+bandpass, λ_k=(θ-freq, γ-freq), g=KL-divergence-from-uniform)` | **Identity** (textbook math) — same architectural slot as Carr-Madan / OFDM identity |
| **Lachaux 1999 PLV** | `T^1` torus average; cross-channel = `T^N` average; identical to §3.5.1 layer (b) for `n=1` | **Identity** (math) — neuroscience has been computing on `T^N` since 1999 |
| **wPLI / imaginary coherence (Stam 2007; Nolte 2004)** | PLV variants that suppress zero-lag volume-conduction artifacts; same `T^N` ambient with phase-quadrant filter | **Identity** (math) — variants of the same identity |
| **Bullmore-Sporns 2009 brain-network graph-Laplacian** | §3.5 row 5 general-graph; same primitive as chess/ephem/protein/audio/power/finance | **Identity** — **seventh** cumulative instantiation; strongest cross-domain math-identity primitive count |
| **Theta-gamma phase-phase n:m locking (Tass 1998)** | §3.5.1 layer (b) `T²` integer-lattice lock-points | **Identity** — closed-form `T²` lattice |
| **Comodulogram (theta-band × gamma-band heatmap)** | 2D discrete sampling of `T²` PAC structure | **Direct cousin** |
| **Spherical-harmonic scalp-to-cortical projection** | §3.5 row 2 sphere S² (l(l+1) eigenvalues); shares architecture with HRTF / globular protein surface | **Identity** — fourth instantiation row 2 (ephem gravity + protein surface + HRTF + cortical EEG) |
| **Ramachandran-like (θ-phase, γ-phase) torus** | §3.5 row 3 flat torus T²; same architecture as protein backbone (φ, ψ) Ramachandran | **Identity** — fourth instantiation row 3 (protein Ramachandran + audio loop + magnetospheric L-shell + theta-gamma) |
| **Cortical surface mesh (FreeSurfer)** | §3.5 row 4 triangle mesh; same architecture as protein solvent-accessible-surface | **Identity** — second instantiation row 4 |
| **Multi-taper spectral estimation (Thomson 1982)** | Welch-CSD-family closed-form spectral; same as finance / audio / telecom usage | **Identity** |
| **Hilbert envelope** | Standard analytic-signal phase + amplitude extraction; identical to telecom envelope detection | **Identity** |
| **ICA (FastICA, Infomax, Picard)** | Substrate primitive — iterative unmixing; same primitive class as protein-folding MD / power-grid Newton-Raphson | **Substrate** (substrate-primitive matching) |
| **Riemannian-geometry brain-state classification (Barachant et al)** | Substrate primitive; SPD manifold; same primitive class as power-grid + finance Riemannian usage | **Substrate** (substrate-primitive matching) |
| **EMDR EEG correlates (Pagani 2012)** | **First-ever direct project-mission overlap** with cross-domain literature; bilateral stimulation generator (project) measured via cross-frequency-coupling spectral methods (literature) | **Operational adjacency** — first absorption round where project + literature literally overlap in mission |

---

## EMDR-project-specific assessment

**Direct connection: STRONGEST OF ALL ABSORPTION ROUNDS.** Unlike protein / power-grid / finance (cross-domain stretch tests), and even more direct than telecom (project's infrastructure substrate) and audio (peer modality), neuroscience theta-gamma research is **literally about the therapeutic mechanism the project's EMDR device is engaging**.

**Genuine cross-pollination wins (real, not stretches):**

1. **Pagani et al. 2012 EEG-EMDR cortical-shift study** is the canonical project-mission anchor. The device's bilateral stimulation triggers the cortical-firing shifts that Pagani et al. measured via EEG. **The project ships the stimulation generator; the EEG literature documents the response.** No cross-claim of clinical efficacy; just operational adjacency between project hardware and clinical EEG mechanism research.

2. **40 Hz gamma + theta phase coupling as a candidate mechanistic basis for bilateral stimulation efficacy** has been hypothesized in the EMDR-mechanism literature. The project's bilateral stimulation device's 0.5-2 Hz alternation rate (CLAUDE.md EMDRIA standard) sits within the **theta-adjacent slow-oscillation band** that nests gamma activity per Lisman-Jensen 2013. The Phase 7 P7.1 pattern playback can in principle generate stimuli at the EEG-coupling-relevant frequencies. **The framework's hierarchical-pattern bilateral-stim spike (commit `7a5b461`) already documents Cartesian-product vs strong-product modality fusion as math-identity-distinct; whether theta-gamma-coupling-aligned bilateral stimulation produces measurably different EEG responses is a clinical research question downstream of this scoping round.**

3. **Disability-accommodation dimension is concrete here.** EEG analysis is heavily visualization-dependent (topomaps, spectrograms, comodulograms — visual heatmaps). Aphantasia / dyslexia / executive-function differences benefit from numerical / textual spectral-fingerprint outputs — exactly what the project's framework produces. See sub-investigation 6.

4. **`exp(−i L_brain t)` quantum-walk lift on structural connectivity → graph-spectral clustering of brain regions with phase-coherent dynamics** is the cleanest project → neuroscience pollination candidate. NOT a per-pair-phase-extraction substitute for direct PLV (which preserves per-pair phase by construction); IS a candidate for spectral-clustering of brain-region groupings. Speculative — would need a dedicated benchmark spike. Honest expectation per T^N async-HF refutation precedent: speculative, likely competitive in a graph-spectral-clustering benchmark, NOT competitive against PLV for per-pair phase extraction.

5. **Concrete falsifiable spike-test candidates queued (Fermata 4):**
   - **(a)** PAC computed via project's `(Transform=Hilbert+bandpass, λ_k, g)` pipeline vs Tort 2010 MI gold standard on a public EEG dataset (HCP, OpenNeuro). Success: ρ ≈ 1.0 with reference MI; spike confirms identity.
   - **(b)** Fiedler partition on structural-connectivity Laplacian (HCP DTI) vs functional-network module decomposition (Power-Petersen, Yeo-Schaefer-7, AAL-90). Matthews φ + Spearman ρ comparison to ephemerides §13 / power-grid IEEE-39-bus / finance Fiedler-vs-HRP-vs-GICS. Eighth quantitative cross-domain datapoint candidate.
   - **(c)** `exp(−i L_brain t)` quantum-walk lift on HCP structural-connectivity Laplacian: cluster-recovery benchmark vs spectral-clustering / Louvain modularity / Newman modularity. Honest expectation: comparable, not dominant; spike confirms-or-refutes whether the project's framing offers a measurable clustering improvement.
   - **(d)** Approximate Z₂ left-right hemispheric symmetry on HCP structural-connectivity: closed-form approximate block-decomposition prediction vs empirical eigendecomposition. §3.5.3(C) candidate. Honest expectation: weaker fit than finance synthetic case due to genuine left-right asymmetry of real brains (handedness, language lateralization).

**Tenuous-but-honest stretches (don't force):**
- Closed-form prediction of theta-gamma-coupling clinical efficacy outcomes from EMDR therapy — no causal claim; the framework expresses mechanism math, not therapeutic prediction.
- Real-time biofeedback during EMDR sessions using project hardware — substrate primitive, state-dependent, out of scope for closed-form `g(λ)`.

---

## Disability-accommodation dimension (per memory)

EEG analysis has **strong, concrete** disability-accommodation dimensions — stronger than finance / power-grid / telecom because the visualization-dependence is acute:

- **Aphantasia (user has it)**: EEG/MEG workflows are saturated with topomaps, spectrograms, comodulograms, source-localization 3D-cortex visualizations — all visual heatmaps. Spectral fingerprints (numerical PAC-MI values, PLV matrices, graph-Laplacian eigenvalue vectors, HDC `PhaseThetaBIP` / `PhaseGammaBIP` cosine similarities) provide non-visual access. **The project's framework is intrinsically aphantasia-friendly.**
- **Dyslexia**: spectrogram visual-pattern-matching is hard for dyslexic readers; numerical/categorical spectral fingerprints (HDC labels; phase-bin-string regression) are easier than chart-reading.
- **ADHD / executive function**: complex multi-step PAC analysis pipelines (Aru 2015 pitfalls — multiple filter-bandwidth choices, surrogate corrections, statistical tests) are hard to manage. Closed-form `(Transform, λ_k, g)` config-entry pipelines (per srmech §3.0) are simpler and reproducible — one config, one parameter set.
- **Motor disability**: BCI (brain-computer interface) applications of EEG are explicitly disability-accommodation (locked-in syndrome, ALS, etc.). The project's framework supports closed-form motor-imagery classification primitives (CSP + LDA + Riemannian-MDM) directly.
- **Trauma-informed dimension**: EEG biomarkers for PTSD / EMDR therapy outcome research is explicitly trauma-informed. **Per `feedback_trauma_informed_defensive_scope.md`: ship the spectral analysis primitives + clinical-literature references + defensive-monitoring framing; do NOT ship offensive-marketing / capability-assessment claims about clinical efficacy.** The framework expresses the math; therapeutic outcomes remain clinical research questions downstream.

EMDR mission relevance: **STRONG**. The bilateral stimulation device serves trauma survivors; the EEG mechanism research is operationally adjacent; the disability-accommodation dimension (especially aphantasia) is concrete and immediate.

---

## Trauma-informed defensive scope (per memory)

Per `feedback_trauma_informed_defensive_scope.md`, the boundary for EEG/EMDR:

- **Ship:** spectral analysis primitives (PAC, PLV, graph-Laplacian on connectivity, source-localization); literature refs (Canolty 2006, Tort 2010, Lachaux 1999, Lisman-Jensen 2013, Buzsáki 2002, Bullmore-Sporns 2009, Pagani 2012, Aru 2015 critique); defensive-monitoring framing (EEG biomarkers for therapy outcome research); disability-accommodation alignment (aphantasia-friendly numerical outputs).
- **Do not ship:** clinical efficacy claims (the framework expresses math, not therapeutic prediction); marketing claims about 40Hz binaural beats curing PTSD (the evidence base is thin; commercial marketing exceeds the science); offensive-application research (BCI thought-decoding for surveillance / lie-detection / interrogation — explicitly out of scope).
- **Ship:** anomaly detection in EEG (defensive — abuse-detection blind to attribution); resilience-scoring of brain-network connectivity (defensive — biomarker space).

The math is dual-use; the project ships physics + textbook math + standard neuroscience literature, never offensive clinical or surveillance application.

---

## Sub-investigation 1 — Existing spectral work in neuroscience

Comprehensive citation-anchored survey. Neuroscience has the **richest spectral history** of any absorption-round domain (older than telecom OFDM, older than finance Carr-Madan, older than protein NMA in the form used).

**Cross-frequency phase-amplitude coupling (PAC)** (foundational EEG/MEG mechanism research):
- **Canolty et al. 2006** *Science* 313:1626-1628 `https://www.science.org/doi/10.1126/science.1128115` — first demonstration of robust theta-gamma PAC in human neocortex; gamma power phase-locked to theta phase. ECoG electrocorticogram data. **Foundational paper that opened the PAC research field.** Cited >5000 times.
- **Tort et al. 2010** *J Neurophysiology* 104:1195-1210 `https://journals.physiology.org/doi/full/10.1152/jn.00106.2010` — modulation index (MI) via Kullback-Leibler distance from uniform; **the field-standard PAC measure**. Defines comodulogram methodology.
- **Penny et al. 2008** *J Neurosci Methods* 174:50-61 — GLM-PAC; statistical inference for PAC effects via generalized linear models.
- **Aru et al. 2015** *Curr Opin Neurobiol* 31:51-61 — **critical methodological review**: many published PAC findings are confounded by non-stationarity, sharp transients, non-sinusoidal waveforms (Van der Pol example), filter-bandwidth mis-specification. **Cautionary anchor for any project usage.**
- **Cohen 2014** textbook *Analyzing Neural Time Series Data* — comprehensive textbook covering PAC, PLV, wavelet, ICA, source localization. MIT Press; field-standard reference.
- **Addressing Pitfalls in PAC Analysis with Extended MI Toolbox 2020** `https://pmc.ncbi.nlm.nih.gov/articles/PMC8004528/` — follow-up to Aru 2015; explicit code + corrections.

**Theta-gamma coupling specifically** (most-studied cross-frequency pair):
- **Lisman & Jensen 2013** *Neuron* 77:1002-1016 `https://www.cell.com/neuron/fulltext/S0896-6273(13)00231-6` — *The Theta-Gamma Neural Code*; comprehensive review. Hypothesizes theta-gamma coupling encodes ordered item-sequences (memory, navigation, perception). **Most-cited theta-gamma review.**
- **Buzsáki 2002** *Neuron* 33:325-340 `https://www.sciencedirect.com/science/article/pii/S089662730200586X` — *Theta Oscillations in the Hippocampus*; foundational review of theta dynamics.
- **Bragin et al. 1995** *J Neurosci* 15:47-60 — hippocampus gamma sub-bands.
- **Belluscio et al. 2012** *J Neurosci* 32:423-435 — slow vs fast gamma cross-frequency coupling.
- **Colgin 2015** *Curr Opin Neurobiol* 31:45-50 — theta-gamma coupling review.
- **O'Keefe & Recce 1993** *Hippocampus* 3:317-330 — hippocampal theta phase precession.

**Phase synchronization / PLV** (cross-channel phase coupling):
- **Lachaux et al. 1999** *Hum Brain Mapp* 8:194-208 — original PLV definition; cross-trial brain-dynamics measurement. **Foundational paper for `T^N` phase-coherence measurement** (in the project's vocabulary).
- **Tass et al. 1998** *Phys Rev Lett* 81:3291 — phase-synchronization analysis of brain signals; introduces n:m locking.
- **Stam et al. 2007** *Hum Brain Mapp* 28:1178-1193 — weighted PLI (wPLI); suppresses zero-lag volume-conduction artifacts.
- **Nolte et al. 2004** *Clin Neurophysiol* 115:2292-2307 — imaginary coherence; same purpose.
- **Bullock & Achimowicz 1994** *Brain Topogr* 6:295-302 — Hilbert-transform phase analysis (early adoption in EEG).

**Brain-network spectral analysis** (graph-theoretic):
- **Bullmore & Sporns 2009** *Nat Rev Neurosci* 10:186-198 `https://www.nature.com/articles/nrn2575` — **foundational review of graph-theoretic brain network analysis**. Structural connectivity (DTI) + functional connectivity (resting-state fMRI / EEG). Cited >10000 times.
- **Bassett & Sporns 2017** *Nat Neurosci* 20:353-364 — network neuroscience review.
- **van den Heuvel & Sporns 2011** *J Neurosci* 31:15775-15786 — rich-club hub identification via graph-Laplacian eigendecomposition.
- **Power-Petersen 2014** *Annu Rev Neurosci* — Power-Petersen 264-node parcellation for functional-network analysis.
- **Yeo-Schaefer 2018** — Schaefer-100/200/400 atlas; widely-used for graph-Laplacian on brain networks.
- **Foundational identity:** brain-network graph-Laplacian is the **seventh** instantiation of the same architectural slot as chess / ephemerides / protein RIN / audio mic-array / power Y-bus / finance correlation network.

**Source localization on sphere S²** (cortical EEG):
- **Pascual-Marqui 1994 / 1999** — LORETA (low-resolution electromagnetic tomography); sLORETA standardization.
- **Hämäläinen & Ilmoniemi 1994** — MNE (minimum-norm estimate).
- **Van Veen et al. 1997** — LCMV beamforming.
- **Vrba & Robinson 2001** — DICS beamforming.
- **Spherical-harmonic decomposition for scalp-to-cortical projection** is the §3.5 row 2 instance.

**ICA and source separation** (substrate-primitive, mostly):
- **Bell & Sejnowski 1995** *Neural Comput* — Infomax ICA on EEG.
- **Hyvärinen 1999** — FastICA.
- **Cardoso 1999** — JADE.
- **Ablin et al. 2018** — Picard (preconditioned ICA for efficient EEG).
- **Substrate primitive** — iterative; doesn't close under `(Transform, λ_k, g)`. Same primitive class as MD in proteins, Newton-Raphson in power-grid.

**EMDR-EEG mechanism literature** (project-mission direct):
- **Pagani et al. 2012** *PLOS ONE* 7:e45753 `https://pmc.ncbi.nlm.nih.gov/articles/PMC3458957/` — *Neurobiological Correlates of EMDR Monitoring — An EEG Study*. **First whole-session EEG monitoring of EMDR therapy.** Cortical firing shifts from limbic to cognitive regions during successful sessions. **Project-mission anchor.**
- **Harper, M. L., Rasolkhani-Kalhorn, T., & Drozd, J. F. 2009** *Traumatology* — proposes 40 Hz gamma frequency hypothesis for EMDR mechanism (note: clinical evidence base for 40 Hz gamma specifically is thin per Aurora-Frewen-Lanius reviews; cite the hypothesis, not the efficacy claim).
- **Calancie et al. 2018** — EMDR-induced EEG changes review.
- **van den Hout & Engelhard 2012** — *How does EMDR work?* `https://journals.sagepub.com/doi/pdf/10.5127/jep.028212` — working-memory taxation hypothesis (alternative non-EEG mechanism).
- **De Voogd et al. 2019** *ScienceDirect* `https://www.sciencedirect.com/science/article/pii/S0005791619300394` — working-memory taxation EEG correlates.
- **Pagani et al. 2017** *Front Psychology* `https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.01935/full` — *EMDR and Slow Wave Sleep: A Putative Mechanism of Action*. Theta-band link.
- **Note**: 40Hz gamma + binaural-beats commercial marketing exists `https://www.meditationlifeskillspodcast.com/blog/40hz-gamma-binaural-beats/` but the clinical evidence base is much thinner than marketing suggests. **Project framing should cite the mechanism hypothesis, not the marketing claim.** (Per memory `feedback_trauma_informed_defensive_scope.md`.)

**Wavelet methods** (academic adoption):
- **Daubechies 1992** *Ten Lectures on Wavelets* — foundational wavelet textbook.
- **Mallat 1989** *IEEE Trans PAMI* — wavelet multiresolution decomposition.
- **Tallon-Baudry & Bertrand 1999** *Trends Cogn Sci* — Morlet wavelet on event-related EEG; introduces time-frequency decomposition standard.

**EMD / Hilbert-Huang** (newer adoption):
- **Huang et al. 1998** *Proc Royal Soc A* — empirical mode decomposition.
- **Rilling-Flandrin 2008** — multivariate EMD.

**Verdict:** Neuroscience has the **richest spectral history** of any absorption-round domain. The `(Transform, λ_k, g)` decomposition is implicitly present in Canolty PAC, Tort MI, Lachaux PLV, Bullmore-Sporns network spectral analysis, LORETA spherical-harmonic source-localization, Tallon-Baudry wavelet time-frequency. **Neuroscience was doing srmech-style work since at least 1995 (Bragin) — the project's contribution is unification framing + cross-domain `T^N` ambient naming, not the methods.**

---

## Sub-investigation 2 — Map neuroscience onto the §3.5 manifold rows

| §3.5 row | Neuroscience instantiation | Strength |
|---|---|---|
| **Euclidean grid + Neumann BC** | **Strong:** single-channel EEG time series (1D Z_N grid; FFT/STFT); spectrogram (2D channel × time; comodulogram theta-band × gamma-band); multi-channel × time (Z_channels × Z_time grid); fMRI 3D voxel grid; sub-second time-frequency decomposition | **Strong** (textbook math) |
| **Sphere S²** | **Strong:** cortical surface for source-localization (scalp-EEG → cortical-source projection via spherical-harmonic decomposition; LORETA / sLORETA / MNE); volume-conduction back-projection; sphere-approximated head model | **Strong** — fourth instantiation (ephemerides gravity + protein surface + HRTF + cortical source-localization) |
| **Flat torus T²** | **STRONGEST:** theta-phase × gamma-phase coupling (the LITERAL §3.5.1 layer (b) instance); sleep-stage circadian × REM-cycle (Z_24h × Z_90min); n:m phase locking (integer-lattice on T²) | **Strong — identity** — fourth instantiation (protein Ramachandran + audio loop + magnetospheric L-shell + theta-gamma) |
| **Triangle mesh** | **Moderate:** cortical surface mesh (FreeSurfer per-subject MRI); subdural electrode grid; 3D head model mesh for source localization | **Moderate** — second instantiation (protein solvent-accessible-surface + cortical mesh) |
| **General graph** | **STRONGEST:** Bullmore-Sporns brain-network graph-Laplacian (structural + functional + dynamic); DTI tractography; resting-state network; default-mode network; functional connectivity; effective connectivity (Granger / DTF / PDC) | **Strong — identity** — **seventh** cumulative instantiation; strongest math-identity primitive count in project |
| **Discrete graph + bundle (sheaf-Laplacian)** | **Moderate:** brain region × frequency-band × power feature bundle; sheaf-Laplacian on brain networks (Hansen-Ghrist 2019 work); multi-channel multi-feature analysis | **Moderate** — research opportunity; sheaf-Laplacian on brain networks is recent academic work |

**Verdict:** **EEG/neuroscience instantiates ALL SIX §3.5 rows.** Comparable only to **audio (§5.2)** which also instantiated all rows strongly. **The strongest §3.5-row-coverage absorption round to date — tied with audio.** This is the second domain (after audio) to instantiate every row of the table. Neuroscience and audio are sibling-modalities both directly project-mission-relevant (audio as peer modality; EEG as mechanism-measurement layer).

---

## Sub-investigation 3 — Identity hits vs cross-pollination candidates

Following the financial-scoping template, classify each substantive neuroscience method:

| Neuroscience tool | Spatial / phase status | Phase-lift verdict |
|---|---|---|
| **PSD / Welch periodogram** | Time-domain magnitude-only | **No useful lift.** Magnitude-PSD discards phase; phase-lift on single-channel scalar PSD is degenerate. |
| **PAC / Tort MI** | Phase-amplitude coupling; already phase-preserving by design | **Identity, not lift.** PAC IS the project's `(Transform, λ_k, g)` at the per-channel level. No new information; vocabulary unification. |
| **PLV / wPLI** | Cross-channel phase-coherence; already `T^N` average by design | **Identity, not lift.** PLV IS the project's `T^N` cosine-similarity at single-frequency band. No new information; vocabulary unification. |
| **Multi-channel PLV matrix** | `T^{N×N}` cross-channel phase ambient | **Identity** — the multi-channel PLV matrix lives on `T^{N(N-1)/2}`; same `T^N` ambient as project's `qm_2d`/`qm_4d` chess and ephemerides T^52 loci. |
| **Brain-network graph-Laplacian** | Static eigendecomposition; spatial | **Useful lift candidate** — `exp(−i L_brain t)` on structural connectivity is NOT in standard neuroscience literature; the project's `T^N` quantum-walk lift would offer phase-coherent dynamical evolution on the connectome. **Per T^N async-HF refutation precedent**: graph-spectral-clustering application is valid; per-pair phase-extraction application is suspect (direct PLV is already gold-standard for per-pair). |
| **ICA (FastICA, Picard)** | Iterative substrate; component-extraction | **No useful lift.** ICA is real-valued unmixing; not phase-preserving in the eigenphase sense. |
| **Riemannian-geometry brain-state classification (Barachant)** | SPD covariance-matrix manifold; substrate | **Indirect** — the SPD manifold has its own geometry; not §3.5.1 layer (b) eigenphase ambient. Different math, different vocabulary. |
| **LORETA / sLORETA / MNE source localization** | Cortical-surface S² + minimum-norm; iterative substrate | **Indirect** — sphere-S² spherical-harmonic decomposition is identity; iterative source-reconstruction is substrate. Sphere instance is row 2 identity. |
| **Granger causality / DTF / PDC** | Directed connectivity; AR-model parametric or non-parametric | **No useful lift** at the lift-on-Laplacian level; the directed-graph version of `T^N` lift is `exp(−i M t)` where M is non-symmetric — opens different math (non-Hermitian quantum walk). Speculative. |
| **Spectral Granger** | Frequency-domain directed coherence | **Indirect** — closed-form frequency-domain directed-connectivity primitive; lives in §3.5 row 1 (2D channel × frequency) plus directed-graph layer. |
| **EMD / Hilbert-Huang** | Data-driven decomposition (substrate) | **No useful lift.** EMD is data-adaptive; not closed-form spectral. |

**Verdict:** For per-channel and per-pair neuroscience analysis, the `T^N` lift offers NO new information — PLV and PAC are already phase-preserving by construction. For **brain-region clustering on structural-connectivity Laplacian**, the lift IS a candidate, but per T^N async-HF refutation precedent, the framing should be careful: **graph-spectral clustering with phase-coherent dynamics** (where the lift IS valid) vs **per-pair phase extraction** (where it is suspect and PLV / Welch coherence already dominate). The honest cross-pollination candidate is graph-spectral clustering of brain regions, not per-pair phase extraction.

---

## Sub-investigation 4 — Test specific candidate findings

This is a **scoping round, not a benchmark spike**. Per dispatch instruction, candidates surfaced here would warrant dedicated numerical spikes in follow-up.

**Candidate 1: §3.5.3(C) closed-form rep-theory eigenvalue prediction for brain networks under approximate Z₂ left-right symmetry.**

Real brains are **approximately** Z₂ symmetric (left vs right hemisphere) — not exactly, due to handedness, language lateralization, anatomical asymmetry. Approximate-symmetry rep theory: if the connectivity matrix `C` had exact Z₂ symmetry, the eigenbasis would decompose as symmetric (+) and antisymmetric (-) subspaces of equal dimension. Empirical brain-connectivity matrices would show **approximate** dimension-N/2 symmetric + N/2 antisymmetric sub-blocks, with deviation parameter measuring lateralization strength. **Falsifiable spike candidate.** Honest expectation per T^N async-HF refutation precedent + per finance Fiedler-vs-HRP spike: this is weaker than finance synthetic-block case because real brains have genuine asymmetry. Spike-test would measure: (i) how close to exact symmetric/antisymmetric decomposition the empirical eigenvectors come; (ii) whether the deviation parameter correlates with handedness/language-lateralization metrics. Could be **first MPM-discipline cross-domain anatomical-lateralization metric** if it pans out.

**Candidate 2: Fiedler partition on HCP structural-connectivity Laplacian vs Power-Petersen 264-node modular decomposition vs Yeo-Schaefer-7 atlas.**

Direct parallel to ephemerides §13 (Fiedler partition + Spearman ρ vs empirical Δv) and finance Fiedler-vs-HRP-vs-GICS spike (2026-05-11; Fiedler 20/20 wins over HRP in moderate SNR). Eighth quantitative cross-domain datapoint candidate. Honest expectation per six prior rounds: Fiedler should be **competitive** with Power-Petersen modular decomposition (which uses Newman modularity, conceptually related to spectral clustering) and **dominant** over chance partitions. Matthews φ and Spearman ρ comparison to ephemerides + power-grid + finance benchmarks.

**Candidate 3: `exp(−i L_brain t)` quantum-walk lift on HCP structural-connectivity for graph-spectral clustering vs standard spectral-clustering / Louvain / Newman modularity.**

Per T^N async-HF refutation precedent: lift is valid for graph-spectral clustering (NOT for per-pair phase extraction). Spike-test would benchmark cluster-recovery on HCP ground-truth Power-Petersen or Yeo-Schaefer-7 atlas labels. Honest expectation: **comparable** to standard spectral clustering, NOT dominant. If the lift offered measurable cluster-recovery improvement, that would be the first project → external-domain pollination win in graph-spectral clustering applications — would warrant elevation to first-class srmech offering. If it offered no improvement, that would be a clean negative result and the lift stays as a vocabulary-unification claim only (math identity stands; not a competitive clustering instrument).

**Candidate 4: §3.5.4 fiber-bundle structure for brain-region × frequency-band × feature space.**

Brain-region (`base`, graph-vertex, dim N_regions per atlas) × frequency-band (`fiber`, rank 4-8 for theta/alpha/beta1/beta2/gamma1/gamma2 + aperiodic) × feature-channel (power, PAC-MI, PLV-coupling-to-other-regions). Total dim N_regions × k_features. **Direct §3.5.4 instance — math-identity-clean.** Same architectural slot as chess 64 × 10 = 640 and 4096 × 11 = 45056, and protein N_residues × k_channels. Not a falsifiable spike test; just documentation of the architectural slot.

**Candidate 5: Theta-gamma `T²` `n:m` locking integer-lattice prediction.**

Theta (4-8 Hz) and gamma (30-100 Hz) frequencies suggest typical `n:m` locking of `1:6` to `1:13` (gamma cycles per theta cycle). On `T²`, the closed-form lock-point lattice is `(φ_θ, φ_γ) = (2πk/m, 2πl/n)`. Empirical comodulogram peaks should align to these lattice points under exact `n:m` locking. **Falsifiable spike candidate.** Honest expectation: empirical brain rhythms have phase drift and frequency variability, so exact lock-points are rare; an approximate-locking spike would measure the deviation from exact lattice points. Could establish **first MPM-discipline cross-domain integer-lock-point fingerprint** if the brain rhythms approximately respect `n:m` locking at the population level.

**Honest verdict:** four falsifiable spike candidates queued. None as load-bearing as the finance Fiedler-vs-HRP spike's `20/20 wins` (the strongest cross-domain MPM-discipline win to date); all weaker than the bilateral-stim hierarchical-pattern's six machine-precision math-identity matches (because real brain data has biological variability + measurement noise that synthetic spikes don't). Per T^N async-HF refutation precedent, **don't oversell cross-pollination candidates** before the dedicated benchmark.

---

## Sub-investigation 5 — Anomalies + boundary cases

**Anomaly 1: PAC measurement controversies (Aru 2015).** Many published PAC findings are confounded by:
- **Non-stationarity** of brain rhythms across trials and time.
- **Non-sinusoidal waveform shape** (Van der Pol oscillator example): a single non-sinusoidal oscillator at theta-frequency contains harmonics at gamma-frequency, producing **spurious PAC** without real cross-frequency coupling.
- **Sharp transients** (event-related potentials, eye-blinks, electrode pops) produce broadband artifact that mimics PAC.
- **Filter-bandwidth mis-specification**: bandwidth of bandpass filter for amplitude-frequency must be wide enough to capture center frequency ± modulating-phase frequency.
- **Suboptimal analysis** (insufficient surrogate corrections, statistical multiple-comparison).

**Honest verdict:** The `(Transform, λ_k, g)` decomposition IS the math identity; per-channel measurement IS fragile. Project framing should **anchor on artifact-screened PAC** (ICA pre-processing + surrogate-corrected MI + non-sinusoidal-aware methods like Wasserstein-distance MI). Mirrors finance microstructure-noise caveat and protein RIN-cleaning caveat. Document, don't paper-over.

**Anomaly 2: Volume-conduction confound in scalp EEG.** Scalp EEG signals are linear mixtures of cortical sources via the volume-conduction head model — cross-electrode coherence is artificially inflated. **wPLI / imaginary coherence are designed exactly to suppress zero-lag volume-conduction artifacts** (Nolte 2004, Stam 2007). Project framing should default to volume-conduction-aware coherence measures, NOT raw PLV / coherence on scalp signals. **Mirrors telecom round's encryption-breaks-spectral-analysis caveat.**

**Anomaly 3: Non-stationarity of brain rhythms across regimes (resting / task / sleep).** EEG eigendecomposition is regime-dependent — resting-state default-mode network ≠ task-related connectivity ≠ sleep-stage connectivity. **Mirrors finance non-stationary-across-regimes anomaly and protein non-stationary-during-folding anomaly.** Common to all spectral-network methods on real-world data; not unique to EEG.

**Anomaly 4: 40 Hz gamma commercial-marketing claims vs clinical-evidence base.** 40 Hz binaural-beats + EMDR are commercially marketed `https://www.meditationlifeskillspodcast.com/blog/40hz-gamma-binaural-beats/`; the clinical evidence base is **much thinner** than marketing claims. **Project framing must cite mechanism hypothesis (Harper-Rasolkhani-Drozd 2009 *Traumatology*), not efficacy claim.** Per `feedback_trauma_informed_defensive_scope.md`: ship the math + cite the hypothesis; do NOT ship marketing claims about therapeutic efficacy. **The MIT BEACON40 gamma-light + Alzheimer's research (Tsai lab; Iaccarino-Singer-Martorell 2016 *Nature*) is a more rigorous evidence base for 40 Hz, but applies to dementia not PTSD/EMDR; cite carefully.**

**Anomaly 5: Source-localization ambiguity (inverse problem).** EEG source-localization is mathematically ill-posed; multiple cortical source distributions can produce identical scalp recordings. LORETA / sLORETA / MNE / beamformer all impose different regularization assumptions, producing different solutions. **Project framing should distinguish forward-model `(Transform, λ_k, g)` (well-defined) from inverse-model substrate iteration (regularization-dependent).**

**Anomaly 6: SGD / deep-learning dominates state-of-the-art EEG classification.** EEGNet, BENDR, EEG-Transformer are dominant on motor-imagery / seizure-detection / sleep-staging benchmarks. Same boundary as finance / power-grid round: **project framing offers interpretability + reproducibility wins, not predictive-accuracy wins against deep-learning.** Documentary, not competitive against transformers.

**Anomaly 7: Brain symmetry is approximate, not exact.** Per Sub-investigation 4 candidate 1: real brain networks have genuine left-right asymmetry (handedness, language lateralization, anatomical asymmetry). Approximate-Z₂-symmetry rep theory works as a deviation metric, not as exact-decomposition. **Honest expectation per finance Fiedler-vs-HRP synthetic-only caveat: weaker fit than synthetic block-correlation case.**

---

## Sub-investigation 6 — Disability-accommodation dimension + project mission

Per memory `feedback_disability_accommodation_dimension.md`, naming explicit accessibility dimensions for the brain-monitoring sub-domain:

**Aphantasia (user has it)**: This is the **most acute disability-accommodation case in the project's research landscape**. EEG/MEG analysis workflows are saturated with:
- Topomaps (scalp heatmaps).
- Spectrograms (time-frequency heatmaps).
- Comodulograms (theta-band × gamma-band PAC heatmaps).
- Source-localization 3D-cortex visualizations.
- Connectivity matrices rendered as graphs.

**Every standard EEG analysis output is a visual chart.** Aphantasia + dyslexia + ADHD users are systematically excluded from EEG-literacy.

**Project framework's value proposition for accessibility:**
- Numerical PAC-MI values (single float per channel-pair per frequency-band-pair) — readable as a table.
- PLV matrices (numerical) — readable as a sparse pairwise listing.
- Graph-Laplacian eigenvalue vectors — readable as a sorted numerical sequence.
- HDC `PhaseThetaBIP` / `PhaseGammaBIP` cosine similarities — readable as labeled cosine-distance metrics.
- Spectral fingerprints (top-k eigenvalues + Fiedler vector signs) — readable as a structured text record.

**The project's `(Transform, λ_k, g)` decomposition is intrinsically aphantasia-friendly**: it expresses spectral effects as transform + eigenvalue + decay-function tuples, not as visual heatmaps. **This is a unique structural alignment between the project's MPM discipline and disability-accommodation principles.** Strongest accessibility-fit absorption round to date.

**ADHD / executive function**: Aru 2015 PAC pipelines have **many parameter choices** (filter bandwidths, surrogate corrections, multiple-comparison thresholds, statistical tests). Closed-form `(Transform, λ_k, g)` config-entry pipelines reduce this to a single named config — one configuration captures the entire analysis recipe, reproducible without re-discovering parameter combinations.

**Trauma-informed**: EEG biomarker research for PTSD / EMDR therapy outcome is explicitly trauma-informed. **Defensive-monitoring scope** (per `feedback_trauma_informed_defensive_scope.md`): ship spectral primitives + clinical-literature references; do NOT ship clinical-efficacy claims or surveillance-applications (BCI thought-decoding for interrogation / lie-detection is explicitly out of scope).

**Motor disability (BCI)**: brain-computer interface applications for ALS / locked-in syndrome are explicitly disability-accommodation. The project's closed-form motor-imagery classification primitives (CSP + LDA + Riemannian-MDM) are directly applicable. **Concrete project-mission extension candidate**: the EMDR device's bilateral stimulation API could be extended to receive BCI motor-imagery commands for users with motor disabilities.

**Mission relevance: EMDR therapy serves trauma survivors → disability-accommodation dimension is intrinsic, not added.** This round is the strongest fit between the project's accessibility commitments and its cross-domain literature foundation.

---

## Sub-investigation 7 — Config-vs-substrate ratio

Per the calibration pattern (graphics ~80/20, audio ~80/20, telecom ~70/30, finance ~50/50, power-grid ~30/70, protein ~20/80, bilateral-stim hierarchical pattern ~80/20 = framework-already-covers), estimate where EEG / neuroscience sits.

**Closed-form `g(λ)` operators dominate** (~50+ across 8 thematic groups; see Operator counts above):
- PSD / coherence / PLV / wPLI / imaginary-coherence: closed-form Welch-CSD-family.
- PAC family (Tort MI, Canolty MVL, Penny GLM-PAC, etc.): closed-form bandpass + Hilbert + KL-divergence.
- Bandpass filter design: closed-form FIR / IIR.
- Wavelet families: closed-form per-wavelet basis.
- Spherical-harmonic source-localization (LORETA forward-model): closed-form SH-degree-l projection.
- Graph-Laplacian on connectivity (Bullmore-Sporns): closed-form eigendecomposition.
- Multi-taper PSD (Thomson 1982): closed-form Slepian-sequence basis.

**Substrate primitives** (~30; see Operator counts):
- ICA (FastICA, Picard, Infomax, JADE): iterative substrate.
- Riemannian-geometry brain-state classification (Barachant): substrate.
- HMM sleep-staging: substrate.
- Deep-learning EEG classifiers (EEGNet, BENDR): substrate.
- LORETA-iterative source reconstruction (inverse problem): substrate.
- Real-time biofeedback adaptive thresholding: substrate.
- EMD / Hilbert-Huang: substrate.

**Estimated ratio: ~60/40** — closed-form-leaning, between telecom (~70/30) and finance (~50/50). Mostly-linear passive volumetric signal-processing of neural oscillator population dynamics; substrate dominates only at inverse-problem source-reconstruction and at deep-learning state-of-the-art classification.

**Pattern confirmed across seven rounds + spike**: substrate dominates where physics is **nonlinearly state-coupled** (proteins ~20/80, power-grid ~30/70); closed-form dominates in **passive signal-processing** (graphics ~80/20, audio ~80/20, bilateral-stim ~80/20); intermediate where both apply (telecom ~70/30, finance ~50/50, **EEG ~60/40**). EEG sits with telecom/finance in the intermediate zone — closer to telecom for the closed-form-rich spectral measurement layer, closer to finance for the substrate-heavy classification / source-reconstruction layer.

---

## AMSC ingestion paths

### `literature_curated`

Standard EEG / MEG / neuroscience canon: Berger 1929 (first human EEG) · Walter 1953 contingent-negative-variation · Cooper-Osselton 1980 (EEG methodology textbook) · Niedermeyer-da Silva 2005 (EEG textbook, 5th ed) · Daubechies 1992 wavelets · Mallat 1989 multiresolution · Tallon-Baudry-Bertrand 1999 Morlet wavelet on event-related EEG · Bullock-Achimowicz 1994 Hilbert phase analysis · Lachaux-Rodriguez-Martinerie-Varela 1999 PLV · Tass et al 1998 phase synchronization · Stam et al 2007 wPLI · Nolte et al 2004 imaginary coherence · Bragin et al 1995 hippocampus gamma · O'Keefe-Recce 1993 phase precession · Buzsáki 2002 theta review `https://www.sciencedirect.com/science/article/pii/S089662730200586X` · Canolty et al 2006 PAC `https://www.science.org/doi/10.1126/science.1128115` · Tort et al 2010 MI `https://journals.physiology.org/doi/full/10.1152/jn.00106.2010` · Penny et al 2008 GLM-PAC · Lisman-Jensen 2013 theta-gamma neural code `https://www.cell.com/neuron/fulltext/S0896-6273(13)00231-6` · Aru et al 2015 PAC pitfalls · Belluscio et al 2012 slow-vs-fast gamma · Colgin 2015 theta-gamma review · Bullmore-Sporns 2009 brain networks `https://www.nature.com/articles/nrn2575` · Bassett-Sporns 2017 network neuroscience · van den Heuvel-Sporns 2011 rich club · Power-Petersen 2014 264-node parcellation · Yeo-Schaefer 2018 atlas · Pascual-Marqui 1994/1999 LORETA · Hämäläinen-Ilmoniemi 1994 MNE · Van Veen et al 1997 LCMV beamformer · Vrba-Robinson 2001 DICS · Bell-Sejnowski 1995 Infomax ICA · Hyvärinen 1999 FastICA · Cardoso 1999 JADE · Ablin et al 2018 Picard · Barachant et al 2012 Riemannian-MDM classification · Cohen 2014 textbook *Analyzing Neural Time Series Data* (MIT Press) · Donoghue et al 2020 FOOOF aperiodic+periodic decomposition · Pagani et al 2012 EEG-EMDR `https://pmc.ncbi.nlm.nih.gov/articles/PMC3458957/` · Harper-Rasolkhani-Drozd 2009 40Hz gamma EMDR hypothesis · Pagani et al 2017 EMDR slow-wave-sleep `https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.01935/full` · de Voogd et al 2019 working-memory taxation EEG · van den Hout-Engelhard 2012 EMDR mechanism review · Iaccarino-Singer-Martorell-Tsai 2016 *Nature* 40Hz gamma-stim Alzheimer (note: dementia, not PTSD).

**Standards corpus:** International 10-20 / 10-10 / 10-5 EEG electrode placement (Jasper 1958; Oostenveld-Praamstra 2001) · IFCN minimum recording standards · IEEE 11073 personal-health-device standards · DICOM-MEG / DICOM-EEG storage · BIDS-EEG (Brain Imaging Data Structure for EEG) · OpenNeuro repository standards · ANSI/AAMI ES60601-1 electrical-safety standards for EEG devices · FDA 510(k) clearance pathway for clinical EEG devices.

### `binary_archive`

OpenNeuro repository (~5000+ EEG/MEG datasets; BIDS-formatted; ~10 TB cumulative) · HCP (Human Connectome Project) MEG + EEG + DTI structural connectivity (~5 TB) · Cam-CAN (Cambridge Centre for Ageing and Neuroscience) ~700 subjects EEG+MEG+MRI · ABIDE (Autism Brain Imaging Data Exchange) ~1000 subjects · ADNI (Alzheimer's Disease Neuroimaging Initiative) ~10 TB · UK Biobank brain imaging (~100000 subjects MRI+DTI; opt-in EEG subset) · TUSZ (Temple University Seizure Corpus) ~2 TB · ChildMind Healthy Brain Network ~10000 subjects · CHB-MIT scalp EEG (pediatric seizure) · BCI Competition III/IV datasets · DEAP emotion-EEG dataset.

**Same scaling forcing function as protein AlphaFold DB and power-grid PMU archives.** Multi-TB streaming-download / partial-fetch / content-addressed dedup design.

### `csv_bulk` / `json_api`

OpenNeuro REST API · Neurosynth meta-analysis API · ConnectomeDB · PhysioNet · UK Biobank API (gated) · NWB (Neurodata Without Borders) format ingestion · MNE-Python / FieldTrip / EEGLAB compatible BIDS-EEG sidecars.

---

## Comparison: Concertmaster vs standard dual-agent pattern (Fermata 1)

This round was dispatched as concertmaster role (per `concertmaster.md`) rather than as standard dual-agent main + sub. The dispatch explicitly assigned anomaly-chase authority and "high effort, broad scope." I executed independent breadth + citation-discipline + memory-application + framework-edge cautions in a single agent, with parallel web-search for citation specificity.

**Fermata 1:** Should this round be redone as standard dual-agent (main + sub) pattern? **Established practice across the audio / protein / telecom / power-grid rounds was dual-agent**; the recent financial-scoping round (`financial-scoping-2026-05-11.md`) was concertmaster-as-solo and accepted by the conductor. **My recommendation:** accept concertmaster-as-solo for this round per the precedent set by the financial round; flag dual-agent as default for future rounds at conductor discretion.

**Convergent-check honesty:** if I were a sub-agent reading the srmech notebook fresh, I would likely converge on the load-bearing claims 1-10 above. Sub-agent unique catches that I may have missed: (i) more specific BIDS-EEG standard references; (ii) MEG-specific spectral methods (CTF/Elekta scanner-specific signal-space-separation) beyond EEG focus; (iii) developmental-EEG age-dependent spectral fingerprints (Donoghue FOOOF aperiodic 1/f exponent changes with age — recent strong evidence base); (iv) seizure-detection EEG-specific spectral biomarkers (sharp-transients, spike-wave complexes) which are clinically critical but separate from cognitive EEG.

---

## Takeaways for landing in master srmech notebook

- **§3.5 cross-manifold table:** **EEG/neuroscience instantiates ALL SIX rows**. Tied with audio as **strongest §3.5-row coverage absorption round to date**. Specifically:
  - **Row 1 (Euclidean grid + Neumann BC):** single-channel EEG; spectrogram; comodulogram. **Strong** identity.
  - **Row 2 (Sphere S²):** cortical surface for source-localization (LORETA / sLORETA / MNE / beamformer). **Fourth instantiation** (ephem + protein + HRTF + EEG).
  - **Row 3 (Flat torus T²):** theta-phase × gamma-phase coupling (literal §3.5.1 layer (b) instance). **Fourth instantiation** (protein Ramachandran + audio loop + magnetospheric L-shell + theta-gamma).
  - **Row 4 (Triangle mesh):** cortical surface mesh (FreeSurfer). **Second instantiation** (protein surface + cortical mesh).
  - **Row 5 (General graph):** brain-network graph-Laplacian (Bullmore-Sporns). **SEVENTH instantiation** — strongest cumulative cross-domain math-identity primitive count in project.
  - **Row 6 (Discrete graph + bundle):** brain-region × frequency-band × feature bundle. Moderate.

- **§4.2 calibration:** EEG profile is **~60/40, intermediate**. Closed-form covers PSD/PAC/PLV/wavelet/spherical-harmonic/graph-Laplacian. Substrate dominates ICA / Riemannian / HMM / deep-learning / inverse-source-reconstruction.

- **§5.7 absorption-round subsection (next):** headline findings + link to this file. **Seventh-instantiation framing** + **strongest project-mission-relevance to date** + **all-six-§3.5-rows instantiation tied with audio** is the load-bearing contribution.

- **§1.5 future-notebook candidates:** EEG row added (status: scoped; seventh-instantiation cross-domain validation; strongest project-mission-relevance via Pagani 2012 EEG-EMDR operational adjacency; all-six-§3.5-rows instantiation; strongest aphantasia-accessibility fit).

- **§3.5.1 layer (b) eigenphase torus:** add **PAC and PLV as identity-instances** at the per-channel and cross-channel level. Per T^N async-HF refutation precedent: clarify that the lift IS valid here (PAC and PLV are already phase-preserving by design — these are identity-instances of the `T^N` ambient, not lift-applications).

- **§3.5.3(C) closed-form group-theoretic eigenvalue prediction:** add **approximate Z₂ left-right brain-network symmetry** as candidate fourth instance (after MFO SG D₃, finance block-correlation S_k × S_m, chess D₄/B₄). Honest expectation: weaker fit than synthetic cases due to genuine biological asymmetry. Falsifiable spike candidate queued (Fermata 4 candidate 1).

- **§3.5.4 fiber-bundle structure:** add **brain-region × frequency-band × feature** as new row alongside chess 64×10 / 4096×11 and protein N_residues × k.

---

## Anomaly log

1. **PAC measurement controversies (Aru 2015).** Non-stationarity + non-sinusoidal waveform shape + sharp transients + filter-bandwidth mis-specification produce spurious PAC. Project framing should anchor on artifact-screened PAC; document, don't paper-over.
2. **Volume-conduction confound in scalp EEG.** Use wPLI / imaginary coherence to suppress zero-lag volume-conduction artifacts; default to volume-conduction-aware coherence measures.
3. **Non-stationarity across regimes** (resting / task / sleep). Common to all spectral-network methods on real-world data; not unique to EEG.
4. **40 Hz gamma commercial-marketing vs clinical-evidence base.** Ship mechanism hypothesis (Harper-Rasolkhani-Drozd 2009), NOT efficacy claim. Iaccarino-Tsai 2016 40Hz gamma-stim Alzheimer evidence applies to dementia, not PTSD/EMDR; cite carefully.
5. **Source-localization inverse-problem ambiguity.** Forward-model `(Transform, λ_k, g)` (well-defined) vs inverse-model substrate iteration (regularization-dependent). Distinguish explicitly.
6. **SGD / deep-learning dominates state-of-the-art classification.** Same boundary as finance / power-grid: project offers interpretability + reproducibility wins, not predictive-accuracy wins.
7. **Brain symmetry is approximate, not exact.** Real brains have genuine left-right asymmetry; rep-theory predictions are approximate-decomposition with deviation parameter, not exact.

---

## Fermata records

**Fermata 1: dual-agent pattern vs concertmaster-as-solo.** This round was dispatched as concertmaster role; financial round precedent (also concertmaster-as-solo) was accepted. **My recommendation:** accept concertmaster-as-solo for this round; flag dual-agent as default for future rounds at conductor discretion.

**Fermata 2: §1.5 future-notebook table should add EEG/neuroscience row.** Status: scoped; seventh-instantiation cross-domain validation; strongest project-mission-relevance to date; all-six-§3.5-rows instantiation tied with audio; strongest aphantasia-accessibility fit. **Conductor decision:** accept as §5.7 absorption-round subsection.

**Fermata 3: `exp(−i L_brain t)` quantum-walk lift on structural-connectivity Laplacian — graph-spectral-clustering candidate.** Per T^N async-HF refutation precedent: graph-spectral-clustering application IS valid (same use case as chess/ephemerides T^N loci); per-pair phase-extraction application is suspect (PLV already gold-standard). **Conductor decision:** Pursue as concrete dedicated benchmark spike (queue alongside finance Fiedler-vs-HRP and protein Fiedler-vs-coevolution as another quantitative cross-domain datapoint), or stay descriptive only?

**Fermata 4: falsifiable spike-test candidates queued.**
- **(a)** PAC computed via project's `(Transform=Hilbert+bandpass, λ_k, g)` pipeline vs Tort 2010 MI gold standard on public EEG (OpenNeuro). Success: ρ ≈ 1.0 with reference MI; confirms identity. Low cost, high pedagogical value.
- **(b)** Fiedler partition on HCP structural-connectivity Laplacian vs Power-Petersen / Yeo-Schaefer-7 modular decomposition. Matthews φ + Spearman ρ comparison to ephemerides §13 + power-grid IEEE-39-bus + finance Fiedler-vs-HRP-vs-GICS spike. Eighth quantitative cross-domain datapoint candidate.
- **(c)** `exp(−i L_brain t)` quantum-walk lift on HCP structural-connectivity for graph-spectral clustering vs standard spectral-clustering / Louvain / Newman modularity. Tests project framing's clustering value-add per T^N async-HF refutation-precedent scope.
- **(d)** §3.5.3(C) approximate Z₂ left-right hemispheric symmetry: closed-form approximate block-decomposition prediction vs empirical eigendecomposition on HCP structural-connectivity. Fourth §3.5.3(C) instance candidate; honest expectation: weaker fit than synthetic finance case.

**My recommendation:** (a) first (low cost, confirms identity, sanity-checks pipeline); (b) second (highest pedagogical value, eighth quantitative cross-domain datapoint, parallel to other Fiedler spikes); (c) third (tests T^N lift candidacy, would resolve graph-spectral-clustering applicability question); (d) fourth (most speculative; weakest expected fit).

**Fermata 5: Disability-accommodation dimension is structurally aligned with project mission for this round.** Aphantasia-friendly numerical spectral fingerprints + reproducible config pipelines + trauma-informed defensive scope all align with the project's existing commitments. **My recommendation:** EEG sub-domain should get explicit notebook documentation of disability-accommodation dimension; the alignment is sufficient to warrant first-class treatment, not just a memory-callback footnote.

---

## Recommended next actions

1. **§1.5 update:** add EEG/neuroscience row to future-notebook candidates table. Status: "scoped; seventh-instantiation cross-domain validation; strongest project-mission-relevance to date via Pagani 2012 EEG-EMDR operational adjacency; all-six-§3.5-rows instantiation tied with audio; strongest aphantasia-accessibility fit."
2. **§3.5 cross-manifold table:** add EEG/neuroscience column with strong instantiation on all six rows. **Tied with audio as strongest §3.5-row coverage absorption round to date.**
3. **§3.5.1 layer (b) update:** clarify PAC + PLV are **identity-instances** of `T^N` ambient (not lift-applications). Per T^N async-HF refutation precedent: list neuroscience as third valid use-case for the lift (after chess/ephemerides existing loci) at the graph-spectral-clustering level; flag that per-pair phase extraction is suspect (PLV already gold-standard).
4. **§3.5.3(C) update:** add **approximate Z₂ left-right brain-network symmetry** as candidate fourth instance. Honest expectation: weaker fit than synthetic cases due to biological asymmetry; falsifiable spike candidate queued (Fermata 4 candidate d).
5. **§3.5.4 update:** add **brain-region × frequency-band × feature** fiber-bundle row alongside chess and protein.
6. **§4.2 calibration update:** add EEG ~60/40 ratio; confirm pattern (substrate dominates state-coupled physics; closed-form dominates passive signal-processing; EEG sits in intermediate zone with telecom/finance).
7. **§5.7 absorption-round subsection:** create as next round in sequence after §5.6 financial-scoping. Headline framings: **seventh-instantiation** + **strongest project-mission-relevance** + **all-six-rows-tied-with-audio** + **strongest aphantasia-accessibility fit**.
8. **Fermata-3 follow-up:** conductor decision on `exp(−i L_brain t)` lift as benchmark-spike candidate (parallel to finance Fiedler-vs-HRP) or descriptive observation.
9. **Fermata-4 follow-up:** queue spike-tests (a) and (b) as concrete experiments; success criteria parallel ephemerides §13 / finance Fiedler-vs-HRP-vs-GICS / power-grid IEEE-39-bus benchmark patterns.
10. **NDJSON records** at `notes/eeg-theta-gamma-scoping-per-locus-2026-05-11.ndjson` (one record per neuroscience method surveyed).
11. **MFO MPM notes** completion record (single line) — to be added with `surfaced_from: bilateral_stim_spike_2026-05-11` lineage marker.
12. **Disability-accommodation dimension documentation:** consider explicit notebook documentation for the brain-monitoring sub-domain per Fermata 5.

---

## References (consolidated)

**Cross-frequency coupling / theta-gamma:**
- Canolty et al. 2006 *Science* 313:1626-1628 `https://www.science.org/doi/10.1126/science.1128115`
- Tort et al. 2010 *J Neurophysiology* 104:1195-1210 `https://journals.physiology.org/doi/full/10.1152/jn.00106.2010`
- Lisman & Jensen 2013 *Neuron* 77:1002-1016 `https://www.cell.com/neuron/fulltext/S0896-6273(13)00231-6`
- Buzsáki 2002 *Neuron* 33:325-340 `https://www.sciencedirect.com/science/article/pii/S089662730200586X`
- Aru et al. 2015 *Curr Opin Neurobiol* 31:51-61
- Penny et al. 2008 *J Neurosci Methods* 174:50-61
- Bragin et al. 1995 *J Neurosci* 15:47-60
- Belluscio et al. 2012 *J Neurosci* 32:423-435
- Colgin 2015 *Curr Opin Neurobiol* 31:45-50
- O'Keefe & Recce 1993 *Hippocampus* 3:317-330

**Phase synchronization / PLV:**
- Lachaux et al. 1999 *Hum Brain Mapp* 8:194-208
- Tass et al. 1998 *Phys Rev Lett* 81:3291
- Stam et al. 2007 *Hum Brain Mapp* 28:1178-1193
- Nolte et al. 2004 *Clin Neurophysiol* 115:2292-2307

**Brain-network spectral analysis:**
- Bullmore & Sporns 2009 *Nat Rev Neurosci* 10:186-198 `https://www.nature.com/articles/nrn2575`
- Bassett & Sporns 2017 *Nat Neurosci* 20:353-364
- van den Heuvel & Sporns 2011 *J Neurosci* 31:15775-15786

**Source localization:**
- Pascual-Marqui 1994/1999 — LORETA / sLORETA
- Hämäläinen & Ilmoniemi 1994 — MNE
- Van Veen et al. 1997 — LCMV beamformer
- Vrba & Robinson 2001 — DICS beamformer

**ICA / source separation:**
- Bell & Sejnowski 1995 *Neural Comput* — Infomax
- Hyvärinen 1999 — FastICA
- Ablin et al. 2018 — Picard

**EMDR-EEG mechanism research (project-mission):**
- Pagani et al. 2012 *PLOS ONE* 7:e45753 `https://pmc.ncbi.nlm.nih.gov/articles/PMC3458957/`
- Pagani et al. 2017 *Front Psychology* `https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.01935/full`
- Harper-Rasolkhani-Drozd 2009 *Traumatology* (40Hz gamma EMDR mechanism hypothesis; clinical evidence base is thin per subsequent reviews — cite hypothesis only)
- van den Hout & Engelhard 2012 *J Exp Psychopathology* `https://journals.sagepub.com/doi/pdf/10.5127/jep.028212` (working-memory taxation mechanism)
- Iaccarino-Singer-Martorell-Tsai 2016 *Nature* — 40Hz gamma-stim Alzheimer (note: dementia, not PTSD; cite carefully)

**Textbooks / foundational:**
- Cohen 2014 *Analyzing Neural Time Series Data* (MIT Press)
- Niedermeyer & da Silva 2005 *Electroencephalography: Basic Principles, Clinical Applications, and Related Fields*
- Donoghue et al. 2020 *Nat Neurosci* — FOOOF aperiodic+periodic spectral decomposition

**Project memory + lineage:**
- `bilateral-stimulation-hierarchical-pattern-2026-05-11.md` — round surfacing this candidate (commit `7a5b461`)
- `financial-scoping-2026-05-11.md` — structural template
- `t-n-async-hf-lead-lag-spike-2026-05-11.md` — refutation precedent for T^N per-pair phase extraction
- `feedback_disability_accommodation_dimension.md` — disability-accommodation discipline
- `feedback_trauma_informed_defensive_scope.md` — defensive-monitoring scope
- `user_explanation_discipline.md` — Feynman-compression discipline
- CLAUDE.md Phase 2 NTP-style time sync (±30 μs drift over 90 min); Phase 6r drift continuation; Phase 7 P7.1 Lightbar Mode + P7.3 PWA Pattern Designer (mission-mode targets)
- MFO §VII.1.1 two-level ontology (active stimulation = field-domain excitation generator; brain rhythms = field-domain excitations)
