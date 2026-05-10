# Audio scoping for srmech — 2026-05-09 cross-domain absorption round

**Round:** Audio (DSP / music / speech / spatial / EMDR-bilateral)
**Date:** 2026-05-09
**Method:** Dual-agent research pattern (`feedback_dual_agent_research_pattern.md`)

## Headline findings

1. **Audio instantiates every row of §3.5 cross-manifold table.** Euclidean grid → spectrogram (STFT); sphere S² → HRTF / ambisonics; flat torus T² → periodic loops; triangle mesh → 3D acoustic-cavity meshes; general graph → microphone-array beamforming + Tonnetz key-relationship graph. Strongest evidence to date that the cross-manifold framing is load-bearing.
2. **Spectrogram is a 2D image** → all graphics-domain primitives (heat-kernel blur, Perona-Malik bilateral, DoG, Varadhan SDF, anisotropic, Helmholtz wave, power-spectrum noise, reaction-diffusion) port directly with only an `eigenvalues:` field swap. Heat-kernel blur on spectrogram = noise reduction; Perona-Malik on spectrogram = harmonic-percussive separation; DoG on spectrogram = onset detection.
3. **Music theory IS cyclic-group theory.** Z₁₂ chromatic scale = direct sibling of chess Z_640 / ephemerides Z_{2³²}. D₁₂ key-and-transposition = direct sibling of chess D₄ board symmetry. Tonnetz key-relationship graph = direct sibling of ephemerides 52-body resonance graph. **`AudioPhase12BIP` is the audio-domain `SkPhase9BIP` cousin** — same architecture, different alphabet.
4. **Bilateral audio is directly load-bearing for the EMDR project's mission.** Audio as a peer modality alongside motor + LED, under the same UTLP-coordinated catalogue + bilateral-coordination machinery. Operators required (alternating tones, binaural beats, isochronic tones, music-driven panning, cardiac-coherence pacing at 0.1 Hz) are all closed-form `g(λ)` catalogue entries. Hardware cost: ~$2–5 BOM (PCM5102 / MAX98357 / UDA1334 I²S DAC). **Potentially the shortest-path proof-of-concept for srmech on the project's actual mission.**
5. **AMSC `literature_curated` already covers DSP knowledge.** RBJ EQ Cookbook → literature_curated. ISO 226 equal-loudness, ERB / Bark / A-weighting curves, Moore-Glasberg masking, MPEG psychoacoustic model, codec specifications (MP3 / AAC / Opus tables) — all standard literature_curated fits. HRTF / RIR archives, speech corpora (TIMIT / LibriSpeech / VCTK / Common Voice), music corpora (FMA / MAESTRO / MUSDB) → binary_archive. **No new ingestion machinery needed.**
6. **Config-vs-substrate ratio: ~80/20.** Most audio DSP is closed-form `g(λ)` — EQ, denoising (Wiener, spectral subtraction, MMSE-LSA), reverb, pitch-shift, ambisonic encoding. Substrate primitives are state-dependent or coupled (compressors / limiters, auto-tune, neural vocoders, source separation, AEC, ANC).

## Operator counts

- **Audio manifolds:** 13 (main agent) / 24 (sub-agent) — sub-agent broader enumeration; both cover the load-bearing core
- **Transforms:** ~25 (main) / 27 (sub) — DFT/FFT, MDCT, STFT, CQT, NSGT, wavelets, gammatone, Mel/Bark, modulation spectrogram, cepstrum, MFCC, chroma, spherical harmonics, KLT, etc.
- **Closed-form `g(λ)` operators:** 50+ (main) / 75+ (sub) across 8–11 thematic groups: EQ family, denoising family, reverb / convolution family, pitch / time family (phase vocoder), Hilbert / analytic-signal family, spatial / spherical-harmonic family, modulation / synthesis family, coding / quantisation family, fingerprinting / chroma family
- **Substrate primitives:** 25 (main) / 26 (sub) — compressor / limiter / expander, auto-tune, adaptive filtering (LMS / NLMS / RLS / Kalman), AEC, ANC, RNNoise / DeepNoise, onset / beat detection, pitch detection, source separation (NMF / ICA / RPCA / Demucs / Spleeter), Karplus-Strong, waveguide synthesis, modal synthesis with feedback, WaveNet / SampleRNN / diffusion-on-spectrogram, Griffin-Lim, MSM / DTW, etc.
- **HDC cyclic groups:** 9 (main) / 12 (sub) — Z₁₂ chromatic, Z₂₄ quartertones, Z₇ diatonic, Z₃ circle-of-fifths (Camelot wheel), Z_b beat cycles, Z₁₂ × Z_b chroma×beat, Tonnetz Z₁₂×Z₁₂ torus, Z₁₃₂ keyboard span, vocal-tract phoneme cycle, Shazam-style Z_n × Z_n peak-pair fingerprint, room-mode index (l,m,n)

## Cross-pollination with already-absorbed srmech primitives

The §3.5 cross-manifold table extends — audio instantiation column:

| Manifold | Audio instantiation |
|---|---|
| Euclidean grid + Neumann BC | Spectrogram (2D STFT) |
| Sphere S² | HRTF / ambisonics — Y_l^m basis with l(l+1) eigenvalues |
| Flat torus T² | Periodic-loop sample; periodic-rhythm pattern |
| Triangle mesh | 3D acoustic-wave simulation on irregular geometry |
| General graph | Microphone array; Tonnetz; key-relationship graph |

Direct primitive ports (graphics → spectrogram):

- Heat-kernel blur on spectrogram → noise reduction / envelope estimation (anisotropic σ_t and σ_f independent)
- Perona-Malik on spectrogram → harmonic-percussive separation (Fitzgerald 2010)
- DoG on spectrogram → onset detection
- Sharpen / Laplacian on spectrogram → transient enhancement
- Anisotropic-tensor diffusion on spectrogram → smoothing along harmonic ridges (vocal-formant tracking)
- Helmholtz wave on spectrogram → procedural texture generator
- Power-spectrum noise (audio variant) → 1/f pink, 1/f² brown, blue, violet, log-normal, log-banded — direct sibling of graphics §3.1 power-spectrum noise; same `P ∈ {1, 1/√λ, 1/λ, √λ}` menu

## EMDR-project-specific opportunities (strong direct connection)

Bilateral audio as a peer modality alongside motor + LED:

- **Alternating tones** (250 Hz–1 kHz, hard-pan L/R, 0.5–2 Hz alternation matching motor frequency range) — closed-form `(Transform = trivial, λ = bilateral_phase, g = pan(t))`
- **Alternating clicks / pulses** — sharper attention than tones for some clients
- **Pink-noise burst alternation** — spectrally rich, less fatiguing over 20-min sessions
- **Music-driven bilateral panning** — energy-preserving rotation `g_L(t) = cos²(π f_alt t)`, `g_R(t) = sin²(π f_alt t)`
- **Binaural beats** (carrier f_L = 200 Hz, f_R = 204 Hz → 4 Hz beat via frequency-following response)
- **Isochronic tones** — `(1 + cos(2π f_pulse t)) · cos(2π f_tone t)`; mono-speaker compatible
- **Cardiac-coherence pacing tones** — 0.1 Hz amplitude-modulated soft pink noise (`EMDR_Slow_BLS_Research_Frontier.md` sub-0.5 Hz frontier)
- **Coherent multi-modal stimuli** — single phase signal drives motors + audio + LED; polyrhythm via Z₂ × Z₃ × Z₆ = Z₁₂ LCM cycle
- **HRV biofeedback tones** — adaptive (substrate primitive); pace adjusts to user's RMSSD

**Disability-accommodation dimension** (per `feedback_disability_accommodation_dimension.md`, sub-agent caught this):

- Aphantasia: bilateral audio gives non-visual cue (user can't visualise moving spot but *hears* alternation) — direct accommodation
- Visual impairment / blindness: audio becomes primary modality; motor + audio is inclusive design
- Hearing impairment: motor primary, audio adds redundancy; bone-conduction transducers a future-direction accommodation
- Photosensitivity / migraine: audio + motor with no visual flicker
- Cognitive load (ADHD / executive-function differences): audio coordination removes visual-attention demand of tracking moving spot

**Trauma-informed audio environment design** (per `feedback_trauma_informed_defensive_scope.md`):

- Soft-onset / soft-offset envelopes (avoid startle response)
- Bandwidth-limited (no aggressive high-frequency content)
- Sub-A-weighted-loudness limits (perceptually safe per IEC 61672)
- No abrupt panning (smooth bilateral alternation, not L/R discrete)
- Post-session quiet ramp

## First-principles cautions (framework-edge)

- **Phase matters in audio.** `g(λ)` must often be complex-valued (delays, all-pass, comb filters). The (Transform, λ_k, g) decomposition extends naturally — g maps to ℂ rather than ℝ — but substrate must support this.
- **Time-varying `g(ω, t)`** for chorus / flanger / phaser. Framework extends but is not yet articulated in §3.0 sketch.
- **Real-time vs offline.** Offline FFT-of-whole-signal fits config; real-time block-by-block needs substrate-primitive scheduling (overlap-add / overlap-save / sliding-DFT).
- **Sample-rate dependence.** Physical-frequency `g(λ)` parameters re-bind per sample-rate.
- **Perceptual vs physical eigenbasis.** Audio's "right" basis is often perceptual (Mel / Bark / ERB / cochlear) rather than linear. Cross-manifold framing handles this; choosing per task is design.
- **EMDR sub-100ms latency budget.** Most operators work in 10ms blocks; some don't (CQT reassignment).
- **Z₁₂ / D₁₂ caveat for non-12-EDO music.** Microtonal (24-EDO, 31-EDO, just intonation) needs different modular arithmetic. Non-pitched percussion lives in rhythm-graph world.

## Comparison: main-agent vs sub-agent

| Dimension | Main-agent (with conversation context) | Sub-agent (independent fresh-read) |
|---|---|---|
| Manifold count | 13 | 24 (broader; added cepstral / wavelet plane / pitch helix / spherical shell / loudspeaker line / non-rectangular plate / auditory-nerve graph / score graph / Q-factor / beam-pattern manifolds) |
| Filter family | Bundled (low-pass / high-pass / band-pass / shelving / peaking) | Explicit (Butterworth Nth, Chebyshev I/II, elliptic / Cauer, Bessel, Linkwitz-Riley) |
| Closed-form ops | 50+ | 75+ |
| Substrate ops | 25 | 26 (added Griffin-Lim explicit, neural vocoder HiFi-GAN / Vocos, Weighted Prediction Error WPE, self-organizing maps, voice conversion) |
| HDC groups | 9 | 12 (added Z₂₄ quartertones, Z₃ Camelot, Z_n×Z_n fingerprint, Z₁₃₂ keyboard, vocal-tract phoneme, room-mode index) |
| Citation discipline | Loose | Strong (RBJ Audio EQ Cookbook 2003 by name) |
| Hardware specifics | "needs care for latency" | I²S DACs (PCM5102 / MAX98357 / UDA1334), ~$2–5 BOM, 512-sample real-time DCT on ESP32-C6 |
| **Disability-accommodation memory** | **Missed** | **Applied** |
| **Trauma-informed memory** | **Missed** | **Applied** |
| Phase-mattering caveat | **Caught** | Implicit only |
| Time-varying `g(ω, t)` framework extension | **Caught** | Listed but not articulated as gap |
| Real-time vs offline scheduling | **Caught** | Light treatment |
| Sample-rate re-binding | **Caught** | Not surfaced |
| Z₁₂ caveat for non-12-EDO | **Caught** | Mentioned but not flagged |
| `AudioPhase12BIP` naming | Implied | **Named explicitly** |
| AMSC mode taxonomy | Flat list | **Structured 7 mode classes** |

**Convergent core (both reached independently):** all 6 headline findings above. The differences are at the margin of enumeration breadth and citation specificity vs framework-edge cautions.

## Takeaways landed in master srmech notebook

- §3.5 cross-manifold table: audio instantiation column added
- §4.2 calibration: audio profile is ~80/20 (similar to graphics)
- §5.2 absorption-round subsection: headline findings + link to this file
- §1.5 future-notebook candidates: audio row added (project-mission relevance — direct EMDR fit)
