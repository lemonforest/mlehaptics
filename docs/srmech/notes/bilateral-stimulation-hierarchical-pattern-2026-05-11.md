# Bilateral stimulation as hierarchical multi-modal pattern — 2026-05-11

**Role:** Concertmaster (dispatched by conductor)
**Round date:** 2026-05-11
**Method:** MPM-discipline closed-form linear algebra (numpy / scipy `eigh`); deterministic seed `20260511`; reproducible 24-record NDJSON output; 33s runtime.
**Artifacts:**
- Script: [`bilateral-stimulation-hierarchical-pattern-script.py`](bilateral-stimulation-hierarchical-pattern-script.py)
- Per-level records: [`bilateral-stimulation-hierarchical-pattern-per-level-2026-05-11.ndjson`](bilateral-stimulation-hierarchical-pattern-per-level-2026-05-11.ndjson)

---

## Provisional verdict

Math-doesn't-lie verdict on the user's load-bearing question: **the srmech framework genuinely covers hierarchical multi-modal bilateral stimulation patterns, end-to-end, with no new math required.** All three load-bearing claims hold; the only framework discipline needed is choosing the segment-transition graph weighting (uniform vs inverse-duration) appropriately for variable-duration patterns. The user's "active-system" stance is documented but does not extend the framework.

Five math identities verified at machine precision (max deviation ~1e-14):

| Identity | Layer | Max deviation |
|---|---|---|
| K_2 eigenvalues exactly `{0, 2}` | §3.5 row 5 (degenerate case) | `0.0` |
| 13-segment uniform cycle = `2(1−cos(2πk/13))` | §3.5 row 5 (general graph) | `2.66e-15` |
| Fiber-bundle Cartesian sum = `λ_base + λ_fiber` | §3.5.4 (operator orthogonality) | `9.19e-15` |
| Envelope × pattern Cartesian product Laplacian | §3.5.3(F) Imrich-Klavžar | `5.30e-15` |
| Envelope × pattern strong-product adjacency: `μ_env + μ_seg + μ_env·μ_seg` | §3.5.3(F) Imrich-Klavžar | `8.88e-15` |
| Triple Cartesian product (envelope × pattern × modality) | §3.5.3(F) + §3.5.4 composition | `1.07e-14` |

---

## Three-level math summary

### Level 1 — Trivial bilateral alternation (DEGENERATE)

Two motors A, B; `K_2` adjacency; `L = [[1,−1],[−1,1]]`; eigenvalues `{0, 2}`; anti-phase eigenvector `(1,−1)/√2`. CTQW lift `U(t) = exp(−i L t)` propagates anti-phase mode at rate 2 on `T²`.

**Framework-already-covers verdict.** EMDR Phase 2 NTP-style time sync (±100μs first-pair handshake; ±30μs converged drift over 90 min stress test) IS the `T²` phase-coherence preservation primitive (srmech §3.5.1 layer b). Phase 6r drift continuation under disconnect IS the magnitude-shadow fallback (`exp(−L t)`) when fresh measurements pause but extrapolation continues. EMDRIA standard 0.5–2 Hz @ 125 ms ON / 500 ms cycle is one operating point on this 2-node graph's `T²` ambient.

Honest verdict: not a "complex object" in the project's sense. One phase relationship, one frequency. The user's framing is correct — this is the degenerate case.

### Level 2 — Multi-segment pattern (THE EMERGENCE POINT)

Test pattern (user's "emergency lights" example): `[ON-300ms × 3 with 200ms gaps] [OFF-1500ms] [ON-100ms × 5 with 50ms gaps] [OFF-3000ms]` — 13 segments, 6500 ms total cycle, segment durations vary 50ms–3000ms, intensities {0, 1}.

Three layers stack cleanly per srmech §3.5:

1. **Per-segment Euclidean-time-axis (§3.5 row 1).** Step-function segments have only the constant (λ=0) mode within each segment; sub-mode structure is trivial. Recorded as a degeneracy-check finding, not a load-bearing computation.

2. **Segment-transition graph-Laplacian (§3.5 row 5).** Cycle graph of 13 segment-nodes. Uniform-weight version matches the closed-form `2(1−cos(2πk/n))` cycle spectrum at machine precision (max deviation `2.66e-15`); inverse-duration-weighted version (edge weight `1000/d_ms` in Hz) gives a deformed spectrum where short segments contribute more to high-frequency modes. Fiedler value is the natural pattern-period proxy. Higher eigenvalues correspond to within-pattern substructure (the 3-flash vs 5-flash grouping).

3. **Modality fiber bundle (§3.5.4).** Base = 13 segments; fiber = rank-2 (vibe, light); total space = `13 × 2 = 26`-dim. Constructed via Cartesian sum `L_total = L_base ⊗ I_2 + I_n ⊗ L_fiber` (the §3.5.4 operator-orthogonality identity). Empirical eigendecomposition matches the closed-form sum-of-eigenvalues prediction `λ_total = λ_base + λ_fiber` to machine precision (`9.19e-15`).

CTQW lift on the bundle Laplacian produces eigenphase variance on `T²⁶`; documented at `t=1.0` graph units for record-keeping.

**Framework-handles-cleanly verdict.** All three layers are explicit instantiations of existing srmech rows. The framework was already there.

### Level 3 — Hierarchical pattern-of-patterns (THE RECURSION POINT)

Level-2 envelope (2-node graph, `K_2`) × level-1 pattern (segment-transition graph). Tested for two level-1 patterns:

- Envelope × emergency-light-13: Cartesian sum match `5.30e-15`; strong-product adjacency match `8.88e-15`.
- Envelope × simple-bilateral-2: Cartesian sum match `2.66e-15`; strong-product adjacency match `1.78e-15`.

Triple Cartesian product (envelope × pattern × modality, dimensions `2 × 2 × 2 = 8`): match `1.07e-14`.

**Framework-handles-cleanly verdict.** The Imrich-Klavžar product-graph universality (srmech §3.5.3(F)) gives closed-form composition at any depth. The sum-of-eigenvalues formula `λ_{ij} = λ_i(env) + λ_j(pattern)` for Cartesian product and the `μ_{ij} = μ_i + μ_j + μ_i·μ_j` formula for strong-product adjacency both verified empirically.

---

## Anomaly findings

**Anomaly 1: uniform-weight segment-transition Laplacian loses duration information.** Any two patterns with the same segment count have identical eigenspectrum under uniform weighting (the graph topology is identical). This is bounded — inverse-duration weighting or per-segment Euclidean-time-axis lifting (§3.5 row 1 with segment duration as lattice extent) recovers the information. The framework already supports both responses; the engineering discipline is choosing per use-case.

**Anomaly 2: Cartesian vs strong product produce distinguishable bundles for modality fusion.** Cartesian sum (separable channels: vibration alone or light alone gives the same eigenphase structure on different bands) vs strong product (fused channels: vibration AND light produces a NEW phase relationship). The framework supports both math-identity-cleanly; which one therapy benefits from is a clinical EMDRIA question downstream and out of scope for this spike. Documented for future clinical hypothesis-testing.

**Anomaly 3: step-function per-segment time-axis is degenerate.** All within-segment energy lives at the constant mode (λ=0); sub-mode structure trivial for piecewise-constant intensity. This is consistent with the pattern domain (intensity is binary per segment) and is not a framework gap — it's the math saying "this segment carries no sub-structure to decompose."

No catastrophic gaps surfaced. The framework's `(Transform, λ_k, g)` decomposition + product-graph universality + fiber-bundle composition fully express the hierarchical multi-modal bilateral pattern problem.

---

## Cross-domain analog instances

The hierarchical-multi-modal-active-stimulation structure has clean analogs across already-absorbed srmech domains:

| Domain | Analog | Provenance |
|---|---|---|
| **Music** | Rhythm = beat × measure × phrase × form (Tonnetz cyclic-group hierarchy) | srmech §5.2 audio absorption |
| **EEG / neural oscillations** | Theta-gamma cross-frequency coupling = `T^n` eigenphase lift between scales | srmech §3.5.1 layer (b) |
| **Cardiac PVC patterns / arrhythmias** | Multi-segment nested rhythmic structure (HRV multi-scale) | New analog (cross-pollination candidate) |
| **Morse code** | Discrete-time analog: dot × dash × character × word × sentence hierarchy | tested in script as `P_morse_V` |
| **Emergency vehicle sirens** | wail / yelp / phaser / hi-lo each have multi-segment patterns; change-of-mode = level-2 envelope | the user's load-bearing example |
| **OFDM cyclic prefix subcarrier** | telecom signal as `T^N` periodic-CP basis (srmech §3.5 row 3 + §5.4 telecom round identity) | srmech §5.4 |

Most-direct cross-pollination: **EEG theta-gamma coupling** is the cleanest published-spectral-literature analog. It is literally `T^n` eigenphase coupling between two scales of brain activity, IS the §3.5.1 layer (b) structure, and has decades of clinical EEG-coherence literature (Buzsáki, Canolty et al). A future srmech absorption round on neural oscillations would extend the cross-manifold §3.5 row 1+5 coverage with biomedical-electrophysiology evidence.

---

## Active-vs-passive stance (the "active system" observation)

User: *"what's odd here is it's an active system whose outputs can be vibration or light or both."*

Documented as a stance record, not a framework extension. The `(Transform, λ_k, g)` decomposition (srmech §3.0) applies identically to active and passive systems. The difference is direction:

- **Passive** (audio analysis, NMA, EEG): input is external; system computes the eigendecomposition; output is a structural fingerprint.
- **Active** (EMDR device, emergency-light controller, metronome, pacemaker): pattern is user-specified; system generates the field-domain excitation matching the eigenphase trajectory on `T^N` ambient.

Per MFO §VII.1.1 two-level ontology: active stimulation IS a field-domain excitation generator; the multi-modal output coupling (vibration AND light) IS the modality fiber bundle product structure. No new math needed.

---

## Ship-mode mapping — EMDR Phase 7 P7.3 PWA Pattern Designer

The EMDR firmware project's Phase 7 P7.3 (next milestone per CLAUDE.md) ships a PWA Pattern Designer. This spike maps directly:

**Pattern descriptor schema.** List of `(duration_ms, vibe_intensity, light_intensity[, audio_intensity])` tuples. TOML-shaped per project memory `feedback_ndjson_over_bloated_json.md` (descriptor-shaped data → TOML; results-style data → NDJSON).

**Spectral fingerprint.** Top-k eigenvalues from inverse-duration-weighted segment-transition graph-Laplacian. Pattern similarity via cosine-of-fingerprint-vectors. Pattern library indexable as a Path-D-style spectral index over the descriptor heavy-store (srmech §2). Pattern interpolation via eigenmode-weighted blending (future work).

**Framework layers**, in order of complexity supported:

1. §3.5 row 1 (Euclidean grid, per-segment time axis — degenerate for step functions)
2. §3.5 row 5 (general graph, segment-transition Laplacian — the load-bearing layer)
3. §3.5.4 (fiber bundle, modality × segment Cartesian sum — multi-modal layer)
4. §3.5.3(F) (product-graph, envelope × pattern composition — hierarchical layer)
5. §3.5.1 layer (b) (eigenphase `T^N` via CTQW — phase-coherent dynamics)

Phase 6r drift-continuation (CLAUDE.md) already implements §3.5.1 layer (b) magnitude-shadow fallback for the 2-node case; the multi-segment generalization follows the same drift extrapolation pattern at the segment level.

---

## Conductor decision points (fermata records)

The conductor should integrate these findings to decide:

1. **§1.5 cross-domain pollination map gains a 7th absorption round** — "Bilateral stimulation patterns (with EMDRIA as canonical citation; project-internal direct-mission fit)." This round is unusual because the domain is the project's actual mission (not a stretch test) — it deserves notebook treatment commensurate with the audio round (§5.2). My recommendation: add §5.6 as the absorption-round section, with this notes file as the detailed scoping reference.

2. **§3.5.3 gains a new motif (G)** — "Hierarchical multi-modal active stimulation as Cartesian-product-of-graph-Laplacians × fiber-bundle modality structure." The motif is empirically anchored by the six machine-precision math-identity matches in this spike; provenance pattern matches the existing motif (C) chess + MFO Phase B + finance instances.

3. **§3.5.4 fiber-bundle table gains a new row** — "EMDR bilateral pattern: segment-transition graph × (vibe, light, audio) modality fiber rank 2-3."

4. **EMDR Phase 7 P7.3 specification gains a srmech-compatible descriptor** — TOML schema + spectral-fingerprint computation + Path-D-style pattern library index. Recommended as concrete deliverable for P7.3 integration with the spectral framework.

5. **Future-work bullet for clinical EMDRIA hypothesis**: Cartesian-product (separable modalities) vs strong-product (fused modalities) bilateral multi-modal stimulation produces math-identity-different eigenspectra; downstream clinical question is which is therapeutically superior, but the framework expresses both. This is a research-direction record only; the project does not make clinical-efficacy claims.

---

## What's NOT in scope here (honest framing)

- No clinical efficacy claims. The framework expresses Cartesian-vs-strong modality fusion as math identity; whether one therapeutic configuration outperforms another is downstream of this spike.
- No HRV biofeedback adaptive control. That's a substrate primitive (state-dependent), not a closed-form `g(λ)` entry, per srmech §4.2.
- No phase-extraction-from-observation methods. This spike is forward-direction (generate pattern → eigenphase trajectory); inverse problems (extract user-physiological-phase from sensor data) are different math.
- No microtonal / non-12-EDO audio extension. Z₁₂ audio cyclic-group framing per srmech §5.2 carries through; microtonal needs different modular arithmetic and is out of scope for this spike.

---

## References

- srmech §3.5 cross-manifold table (six rows)
- srmech §3.5.1 layer (b) eigenphase torus `T^n` (CTQW lift)
- srmech §3.5.3(F) product-graph universality (Imrich-Klavžar *Product Graphs*)
- srmech §3.5.4 fiber-bundle structure (chess 2D 64×10 + 4D 4096×11 as load-bearing instances)
- srmech §5.2 audio absorption round — bilateral audio as peer modality
- CLAUDE.md Phase 2 NTP-style time sync (±30 μs drift over 90 min)
- CLAUDE.md Phase 6r drift continuation (magnitude-shadow fallback at 2-node level)
- CLAUDE.md Phase 7 P7.1 Scheduled Pattern Playback + P7.3 PWA Pattern Designer
- MFO §VII.1.1 two-level ontology (active stimulation = field-domain excitation generator)
- Memory `user_explanation_discipline.md` — Feynman compression: trust the user's compressed framing
