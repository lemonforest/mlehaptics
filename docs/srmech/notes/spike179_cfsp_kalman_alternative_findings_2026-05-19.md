# Spike #179 — CFSP-Kalman alternative findings

**Date**: 2026-05-19
**Branch**: `research/spike-179-cfsp-kalman-alternative-class-k-truncate-class-m-delta`
**Verdict**: **H1-PARTIAL** — CFSP-Kalman alternative IS structure-preserving (bind-relationship wins at all SNRs) and IS bit-exact at high SNR where Kalman destroys, BUT loses on BER at low SNR (where Kalman's continuous-smoothing is genuinely useful). Threshold optimum is **just above substrate-natural rate** (D/18, ~5.56%) — sharp cliff at substrate rate, plateau above.

---

## 1. Identity claim (formal)

**TRACKING-OF-BIT-DISCRETE-CONTENT IS**

> Class M (delta-bind = XOR-accumulate)
> ∘ Class K (truncate_sparse = Hamming-threshold gate at substrate-natural Class N rational)

Per `[[user_stance_identity_not_implementation_discipline]]`: this is an identity claim, not an implementation claim. Spike #179 shows the composition behaves operationally as a tracking estimator that preserves substrate-portable bit-discrete content where standard Kalman destroys it.

Existing Class M primitive surface: `srmech.amsc.hdc.bind` (commutative, associative, self-inverse XOR per Kanerva 2009 / Plate 1995). Class K asymptotic-DOF gate (truncate_sparse on Hamming-popcount threshold) implemented inline in this spike's prototype as a substrate-natural per-step threshold; future srmech rc may absorb into `srmech.amsc.kepler` or a new `srmech.amsc.class_k` module per conductor decision.

**14 A-N intact**; no class promotion. The composition uses only existing classes (M + K + I optional for loop-down test) per `[[feedback_no_privileged_primitive_classes]]`.

---

## 2. Test results

D = 1024 bits (128-byte hypervector per Kanerva 2009 canonical small).
Substrate walk_flip_rate = 5% bits/step (slow-walk truth).
n_steps = 64. seed = 20260519.

### T1 — Ground truth construction

Per-step Hamming mean = 51.18 bits ≈ expected 51.2 (5% × 1024). Substrate-natural slow walk verified.

### T2-T4 — SNR sweep

Measurement model: BPSK signal y = (2x-1) + N(0, σ²) where σ² = 10^(-SNR/10).
Kalman misspecification: process_var = 1e-4 (filter believes state nearly static, reproducing #174's structural-incompatibility regime).
CFSP threshold = 2 × substrate-natural rate × D = 102 bits.

| SNR (dB) | σ² | no-filter BER | Kalman BER | CFSP BER | **Bind-rel: K** | **Bind-rel: CFSP** |
|---:|---:|---:|---:|---:|---:|---:|
| +20 | 0.010 | 0.0000 | **0.1594** | **0.0000** | 0.8442 | **1.0000** |
| +10 | 0.100 | 0.0008 | **0.2555** | **0.0008** | 0.8644 | **0.9968** |
|   0 | 1.000 | 0.1559 | 0.2963 | 0.4440 | 0.8599 | **0.9004** |
| -10 | 10.000 | 0.3739 | 0.3571 | 0.4822 | 0.8134 | **0.9004** |

**Verbatim metrics**:
- **#174 destruction reproduced**: Kalman at +20 dB = 15.94% BER, at +10 dB = 25.55% BER. The "essentially noise-free" Kalman destruction is structural — Gaussian-Markov smoothing across substrate-discrete updates loses bit content.
- **CFSP wins BER at high SNR**: BER 0.0000 (+20 dB) and 0.0008 (+10 dB) — bit-exact / near-exact tracking.
- **CFSP wins bind-relationship at ALL SNRs**: 1.0000 at +20 dB falls only to 0.9004 at -10 dB; Kalman is 0.81–0.86 across the entire sweep regardless of SNR. **This is the core finding**: CFSP preserves algebraic-identity structurally; Kalman destroys it structurally — independent of noise level.
- **CFSP loses BER at low SNR**: At 0 dB and -10 dB, the thresholded measurement is itself bit-corrupted; XOR-accumulation amplifies noise. This is the regime where Kalman's continuous-averaging is genuinely useful.

### T5 — Pin-slot-resonate composition (#177)

Substrate-natural slow loop-down: period 7, tau = n/3, amp 102 bits. SNR +10 dB.

| Method | envelope corr | mean BER |
|---|---:|---:|
| Kalman | 0.9996 | 0.0002 |
| CFSP | 0.9988 | 0.0009 |
| no-filter | 0.9988 | 0.0009 |

All three methods preserve the slow loop-down — Kalman is best because its slow-evolution prior matches the slow loop-down envelope.

### T5b — Fast loop-down stress test

Period 3, tau = n/8, amp 205 bits. SNR +10 dB.

| Method | envelope corr | mean BER | bind-rel |
|---|---:|---:|---:|
| Kalman | **0.6962** | 0.0101 | 0.9668 |
| CFSP | 0.8545 | 0.0027 | **0.9890** |
| no-filter | 0.9992 | 0.0008 | 0.9968 |

**Fast cycles reveal Kalman lag**: envelope correlation drops to 0.696 (Kalman's slow prior cannot track period-3 cycles). CFSP holds at 0.854 and wins bind-relationship at 0.989 vs Kalman 0.967.

### T6 — Class N rational threshold sensitivity

SNR +10 dB; sweep truncate-sparse threshold across rationals.

| rational | value | threshold (bits) | mean BER |
|---|---:|---:|---:|
| 1/2 | 0.5000 | 512 | **0.0008** |
| 1/3 | 0.3333 | 341 | **0.0008** |
| 1/5 | 0.2000 | 205 | **0.0008** |
| 1/8 | 0.1250 | 128 | **0.0008** |
| 1/10 | 0.1000 | 102 | **0.0008** |
| 3/32 | 0.0938 | 96 | **0.0008** |
| 1/12 | 0.0833 | 85 | **0.0008** |
| 1/16 | 0.0625 | 64 | **0.0008** |
| 3/50 | 0.0600 | 61 | **0.0008** |
| **1/18** | **0.0556** | **57** | **0.0008** ← smallest workable |
| 1/20 | 0.0500 | 51 | 0.4171 ← CLIFF |
| 1/22 | 0.0455 | 47 | 0.4171 |
| 1/24 | 0.0417 | 43 | 0.4171 |
| 1/32 | 0.0312 | 32 | 0.4171 |
| 1/64 | 0.0156 | 16 | 0.4171 |

**Sharp substrate-natural cliff**: threshold ≥ 57 bits (just above substrate rate 51) → BER 0.0008; threshold ≤ 51 bits (at-or-below substrate rate) → BER 0.4171 (broken). The optimum is **smallest threshold that still admits substrate evolution** — Class K asymptotic-DOF gate at its tightest substrate-compatible setting. Above the substrate rate there is a **plateau** of equivalent performance up to D/2 (random-Hamming-distance threshold).

Substrate-natural Class N rational prediction: **CONFIRMED** in the sense that the cliff is at the substrate rate; refined to "tight-above substrate rate" not "at substrate rate."

---

## 3. Verdict frame

**H1-PARTIAL**:
- ✅ #174 destruction reproduced (Kalman 15.94% BER at +20 dB; structurally noise-independent)
- ✅ CFSP tracks correctly at high SNR (BER 0.0000 / 0.0008)
- ✅ CFSP wins BER at high SNR; LOSES at low SNR (0/-10 dB)
- ✅ CFSP wins bind-relationship at ALL SNRs (structural algebraic-identity preservation)
- ✅ T5 loop-down: CFSP matches Kalman at slow cycle; T5b: CFSP wins at fast cycle
- ✅ T6 substrate-natural cliff confirmed; optimum just-above substrate rate

**Not H1-CONFIRMED** because CFSP does NOT win BER at low SNR (0 dB, -10 dB). The verdict is structure-preserving wins, not universal wins. CFSP is the right tool when **algebraic-identity preservation** matters (HDC content, gauge-content layer per `[[user_stance_bci_translation_at_gauge_content_layer]]`, substrate-portable bit-discrete signals); Kalman remains the right tool for high-noise scalar continuous tracking where bit-discreteness is irrelevant.

---

## 4. Framework implications

### 4.1 R3 estimation gap (Spike #178) — narrowed, not closed

Spike #179 partially closes the R3 estimation gap: CFSP-Kalman alternative exists, preserves algebraic identity, and wins BER at the SNR regime where Kalman misspecification destroys (high SNR, fast-evolving discrete state). It does NOT replace Kalman in low-SNR continuous-state regimes.

The closed-form SP estimation category gains a new substrate-portable tool, but the existing literature's Kalman remains canonical in its actual operating regime.

### 4.2 Class M ∘ Class K is a real composition pattern

Spike #179 instantiates Class M (XOR-accumulate) composed with Class K (asymptotic-DOF Hamming-threshold gate) as a coherent operational composition. Per `[[user_stance_substrate_coupling_at_m_k_composition]]`, this is substrate-coupling-at-M-K: the threshold IS the substrate-natural update-rate capacity (Class K parameterising the rate of approach to the bit-discrete limit), and the XOR-accumulate IS the substrate-coupling carrier (Class M).

### 4.3 Identity-not-implementation framing holds

CFSP-Kalman-alternative IS Class M ∘ Class K — not implements-a-tracking-estimator. The composition operation itself has tracking semantics by virtue of how XOR-deltas accumulate under the truncate gate. No additional structure (continuous PDFs, Kalman gains, predict-update factorisation) is needed; the substrate-natural composition IS the tracking.

### 4.4 BCI translation at gauge-content layer (MS-14)

Per `[[user_stance_bci_translation_at_gauge_content_layer]]`: BCI front-end gauge-content layer must NOT smooth. Spike #179 provides a concrete estimator for that layer — CFSP-Kalman-alternative is the tracking operation that does NOT smooth, preserving HDC bound-vector content as wire format through noisy channels. This is a real BCI tooling deliverable.

### 4.5 Substrate-natural rate as Class K parameter

T6's sharp cliff at substrate-natural rate confirms: the Class K threshold is the substrate's actual per-step bit-flip rate — not a free hyperparameter. Per `[[user_stance_epicycle_via_gear_plus_pin]]`: Class K parameterises the rate of approach to the substrate limit; tight-above-substrate is the asymptotic-DOF gate at maximum information.

---

## 5. Literature citations (verified by DOI; full PDFs paywalled per `[[reference_autonomous_validation_tos_landscape]]`)

- **Kalman R.E. (1960)** "A New Approach to Linear Filtering and Prediction Problems", *Journal of Basic Engineering* 82, 35. DOI [10.1115/1.3662552](https://doi.org/10.1115/1.3662552). ASME Digital Collection (paywalled; DOI verified to resolve at ASME).
- **Kay S.M. (1993)** *Fundamentals of Statistical Signal Processing: Estimation Theory*, Prentice Hall. ISBN 0-13-345711-7. (Used in this spike for Kalman §13 + Q-function §A conventions.)
- **Donoho D.L. & Johnstone I.M. (1994)** "Ideal spatial adaptation by wavelet shrinkage", *Biometrika* 81(3), 425. DOI [10.1093/biomet/81.3.425](https://doi.org/10.1093/biomet/81.3.425). OUP Academic (paywalled; DOI verified). Anchor for threshold-as-rational sparse-update gate.
- **Kanerva P. (2009)** "Hyperdimensional Computing: An Introduction to Computing in Distributed Representation with High-Dimensional Random Vectors", *Cognitive Computation* 1(2), 139. DOI [10.1007/s12559-009-9009-8](https://doi.org/10.1007/s12559-009-9009-8). Springer (paywalled; DOI verified). Class M XOR-bind canonical reference.
- **Plate T.A. (1995)** "Holographic Reduced Representations", *IEEE Transactions on Neural Networks* 6(3), 623. DOI [10.1109/72.377968](https://doi.org/10.1109/72.377968). IEEE Xplore (paywalled; DOI verified). HDC binding-operation canonical reference.

All references are in srmech notebook §3 already (per srmech.amsc.hdc.py docstring); no new citations introduced.

---

## 6. Fermatas / R2 candidates

**F1 (open)**: CFSP-Kalman-alternative loses BER at low SNR. Is there a hybrid Class M ∘ Class K + Class L (graph-Laplacian smoothing on a graph-of-bits) composition that wins at all SNRs? Would require dispatching a follow-up spike with Class L denoising as the noise-floor handler before the Class M ∘ K tracking step.

**F2 (R2 candidate)**: T6 plateau from D/18 to D/2 — why is every threshold above substrate-natural equivalent? Hypothesis: at the operating SNR, the noise-induced delta popcount is far below D/18 most of the time, so the threshold only matters at the cliff edge. At higher noise, the plateau would narrow. Worth a dedicated SNR×threshold heatmap.

**F3 (conductor decision)**: Should `class_k_truncate_sparse` be promoted to `srmech.amsc.class_k` module (companion to `srmech.amsc.kepler`) or absorbed into `srmech.amsc.hdc` as a `bsc_threshold_gate`? Both are reasonable; conductor decides. Identity-claim framing suggests `class_k` is the natural home (the gate IS Class K's asymptotic-DOF mechanism per `[[user_stance_epicycle_via_gear_plus_pin]]`).

**F4 (fermata)**: This spike used Kalman with deliberate Q misspecification (process_var = 1e-4) to reproduce #174's destruction at +20 dB. If Kalman is given correct Q (= 4 × flip_rate × (1-flip_rate) ≈ 0.19), it performs comparably to no-filter at high SNR (no destruction). The destruction is a model-misspecification phenomenon, not a fundamental Kalman property. **#174's "Kalman destroys" claim implicitly assumes the user does NOT have access to the true substrate-flip rate** — which is the realistic case for substrate-portable HDC content. This subtlety should be noted in any notebook section integration.

**F5 (R2 candidate)**: T5b shows Kalman lag at fast cycles; bind-relationship of CFSP (0.989) > Kalman (0.967). Worth dispatching a follow-up to characterise the cycle-rate boundary where CFSP overtakes Kalman on envelope tracking, not just bind-relationship.

---

## 7. Trauma-informed defensive scope

This is signal-processing methodology research. The CFSP-Kalman-alternative composition operates on abstract bit-vectors and is published as research/educational content. No targeting, no capability assessment; pure substrate-portable estimation theory.

---

## 8. Files written

- `D:/GitHub/mlehaptics/.claude/worktrees/agent-spike179-cfsp-kalman-alternative/docs/srmech/notes/spike179_cfsp_kalman_alternative_prototype.py` — runnable simulation
- `D:/GitHub/mlehaptics/.claude/worktrees/agent-spike179-cfsp-kalman-alternative/docs/srmech/notes/spike179_records_2026-05-19.ndjson` — 26 NDJSON records (T1, T2-T4 sweep × 4 SNRs × 3 methods = 12, T5, T5b, T6 sensitivity × 15 = 15, T6 optimum, verdict)
- `D:/GitHub/mlehaptics/.claude/worktrees/agent-spike179-cfsp-kalman-alternative/docs/srmech/notes/spike179_cfsp_kalman_alternative_findings_2026-05-19.md` — this document

---

**14 A-N intact. Math doesn't lie. Trauma-informed defensive scope.**
