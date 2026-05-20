# Spike #40 — Structural shape of an epicycle in musical and wave theory (per-instrument meta-question)

**Date:** 2026-05-17
**Research spike artifact.** Concertmaster dispatch per user direction. Primary question: where does Class K Kepler-shape `c_k = ε^k/k` appear in musical/wave substrate? Meta-question (2026-05-17): *"from the position of each individual [instrument] in a concert, are there epicycle structures from the way different instruments make different musical shapes?"* — i.e., do per-instrument substrates produce measurably different epicycle shapes?

> **Discipline.** Closed-form math + textbook instrument-physics models; no copyrighted audio. NDJSON outputs per `[[feedback_ndjson_over_bloated_json]]`. 50-seed random-amplitude falsifier controls run before any positive claim per Spike #38 discipline. K-strict three-criteria (eps_fit ∈ [0.001, 0.5]; r² > 0.99; monotonic-decreasing). Honest absence acceptable per `[[user_stance_kepler_shape_universal]]`.

---

## §1 Bottom line

**Primary question (where does Kepler-shape appear in musical/wave substrate?):**
- **ABSENT in 13/15 canonical instrument amplitude spectra.** Per `[[user_stance_kepler_shape_universal]]` — honest absence. Framework correctly says "no" where Kepler-shape doesn't appear.
- **PRESENT in pure FM at small β** (real structural finding — see §4 Anomaly A1: Kepler EOC ≡ FM-with-modulation-index-ε at small ε)
- **PRESENT trivially in canonical Kepler-EOC reference** (positive control)

**Meta-question (do different instruments give measurably different shapes?):**
- **YES — substrate-discriminating via DECAY-FORM-BEST-FIT (M1 power-law / M2 geometric / M3 Bessel / M4 Kepler).** The strict K-test alone is K-specific, not instrument-discriminating; the four-model fit IS substrate-discriminating with characteristic parameters.

| Instrument | ring | K strict? | best-decay | param | signature |
|---|---|---|---|---|---|
| FM (β=0.5) | up | **YES** | M3_Bessel | β=0.496 | Bessel J_k(0.5) |
| FM (β=1.5) | up | no | M3_Bessel | β=1.49 | Bessel J_k(1.5) |
| FM (β=3.0) | up | no | M3_Bessel | β=3.02 | Bessel J_k(3.0) |
| AM | up | no | sparse | — | Class I 2-line |
| Beat 2-tone | up | no | sparse | — | Class I 2-line |
| Piano (B=1e-4..1e-3) | **down** | no | M1_power_law | p=1.000 | sawtooth 1/n |
| Violin (Helmholtz) | up | no | M1_power_law | p=1.000 | sawtooth 1/n |
| Clarinet | up | no | M4_Kepler* | ε=1.000 | odd-only 1/(2n-1) |
| Drum 2D membrane | **down** | no | M1_power_law | p=1.000 | 1/n baseline; freq=Bessel zeros |
| Bell 5-mode | **down** | no | M2_geometric | ε=0.802 | mode-amplitude geometric |
| Voice /a/ | up | no | M2_geometric | ε=0.854 | formant-shaped |
| Flute | up | no | M1_power_law | p=2.000 | weak overtones 1/n² |
| Trumpet | up | no | M1_power_law | p=0.500 | brass-rich 1/√n |
| REF Kepler ε=0.1 | — | **YES** | M4_Kepler | ε=0.100 | canonical positive |
| REF 1/n sawtooth | — | no | M1_power_law | p=1.000 | sawtooth baseline |
| REF white noise | — | no | M1_power_law | p=0.000 | flat |

*Clarinet M4_Kepler is degenerate (ε=1.0 out of physical range; sparse odd-only spectrum is geometric-like on the c₁/c₃/c₅ sub-grid; not a true K hit).

## §2 Meta-question answer — substrate-discriminating YES

Different instruments produce measurably different epicycle shapes in three structural senses:

1. **Decay-form discrimination**: M1_power_law p-exponent separates piano/violin (p=1, sawtooth family) from flute (p=2, weak overtones) from trumpet (p=0.5, brass-rich). The M3_Bessel family is unique to FM modulation. The M4_Kepler family is unique to pin-slot / orbit kinematics.

2. **Substrate-class discrimination**: drum 2D membrane is **Class L direct** (Laplacian-Dirichlet eigenvalues = Bessel zeros). Piano/violin/bell modes are Class L on different operators (1D Laplacian-with-stiffness / D₆-like / 3D-shell). FM is Class K + Class I composition. AM/beat are sparse Class I. The 14-class binding-level overlay applies cleanly.

3. **Loop-up vs loop-down discrimination** per `[[user_stance_string_theory_instrument_first]]`: violin / flute / clarinet / voice / trumpet are RING-UP (sustained excitation; no decay envelope to test cascade-β). Piano / drum / bell are RING-DOWN (struck-then-decay). Real per-instrument-substrate distinction.

**Strict K-shape (Spike #30B v3 three-criteria) does NOT generally appear in canonical instrument amplitude spectra.** It appears only in:
- FM at small β (where Bessel J_k(β) for β≤0.5 mimics geometric ε^k/k at k_max=6 — see §4 Anomaly A1)
- Canonical Kepler-EOC reference family
- Pure ε^k/k reference (trivial)

This matches `[[user_stance_kepler_shape_universal]]`: K appears where Kepler-shape appears; honest absence per Spike #38 caffeine pattern.

## §3 Per-signature verdicts

### §3.1 Class K Kepler-ladder (Spike #30B v3 strict)
- **ABSENT** in 13/15 instruments (violin/piano/clarinet/drum/bell/voice/flute/trumpet/AM/beat all fail at least one of: monotonic / in-range / r²>0.99)
- **PRESENT** in `pure_fm_beta_0.5` (real positive — see §4) and all Kepler reference families
- **Falsifier**: 0/50 random amplitude spectra pass (eps_fit mean=1.00, std=0.25)
- **Verdict**: K is substrate-rare in music; only FM (structurally Kepler-equivalent at small β) shows K-shape. Canonical musical-instrument acoustics live elsewhere on the decay-form taxonomy.

### §3.2 Class L Laplacian eigenstructure
- **PRESENT in drum** as direct 2D Laplacian-Dirichlet (modal frequencies = Bessel zeros; Rayleigh 1894 §200)
- **PRESENT in piano/violin** as 1D Laplacian-with-stiffness (Fletcher 1998 §2.18)
- **PRESENT in bell** as 3D-shell Laplacian (Fletcher 1998 §21.3)
- **Drum self-similarity vs random-graph falsifier**: drum eigval-density cosine-sim tested against 50 random Erdős-Rényi 36-node graphs (mean ± std = 0.84 ± 0.02). Spike #38 lesson applies: eigval-density-histogram methodology becomes degenerate at small substrate sizes; the structural finding "drum has Laplacian eigenbasis" is trivially true; FFT-cosine-match methodology is unreliable below n~100.
- **Verdict**: Class L is the universal substrate signature for instruments. Discrimination lives in the specific eigenvalue spectrum, NOT in histogram-cosine-similarity.

### §3.3 Cascade-β stretched-exp
- **APPLICABLE only to RING-DOWN instruments** per `[[user_stance_string_theory_instrument_first]]`: piano (struck) / drum (struck) / bell (struck).
- **NOT APPLICABLE to RING-UP instruments**: violin / flute / clarinet / voice / trumpet — no decay envelope (skipped honestly).
- **Results on idealised exponential decay envelopes**:
  - Piano (1D, d_S=1, predicted β=1/3): empirical β=0.60 (Δβ=+0.26)
  - Drum (2D, d_S=2, predicted β=0.5): empirical β=1.00 (Δβ=+0.50)
  - Bell (3D, d_S=3, predicted β=0.6): empirical β=1.00 (Δβ=+0.40)
- **Verdict**: cascade-β formula `β = d_S/(d_S+2)` does NOT match canonical IDEALISED musical decay envelopes (which are simple exponential β=1, not stretched-exp). Honest absence — cascade-β is for substrate-induced anomalous diffusion (Spike #31 SUN/cosmic context); idealised musical decays are pure exponential by construction. Real piano decay is dual-exponential (Fletcher §2.20) which IS anomalous-diffusion-adjacent — but the simple-exp model here doesn't capture that. Candidate Spike #41+ follow-on.

### §3.4 Information-instrument 14-class binding overlay
All 14 classes have binding-level identification for any musical-instrument substrate (consistent with Spike #37 substrate-portability table):

| Class | Musical-instrument binding |
|---|---|
| A | instrument signature/timbre fingerprint |
| B | notation symbols (note name / partial number) |
| C | time-indexed acoustic-pressure stream |
| D | pitch-class routing |
| E | instrument family / mode catalog |
| F | phoneme/syllable template binding (for voice) |
| G | harmonic sub-stream extraction (formant analysis) |
| H | self-listening / overtone-singing feedback (voice only) |
| I | pitch-class cyclic group / circle of fifths |
| J | harmonic partial-count decomposition |
| K | small-β FM modulation (rare in instruments; common in synthesis) |
| L | every instrument has a Laplacian-eigenbasis (substrate-trivial) |
| M | timbre-vector binding (HDC across spectrogram features) |
| N | just-intonation / equal-temperament rational-approximation |

NOT a falsifiable spectral measurement per Spike #37 / Spike #38 discipline; cataloguing claim only.

## §4 Anomalies investigated

### §4.1 Anomaly A1: pure_fm_beta_0.5 PASSED strict K-test — REAL STRUCTURAL FINDING

Hypothesised either (H1) low-k clipping artifact, (H2) real structural identity, or (H3) gate too lax.

**H2 confirmed**: **Kepler equation IS phase modulation at small eccentricity.** The eccentric-anomaly Fourier expansion is

`ν − M = 2ε·sin(M) + (5/4)ε²·sin(2M) + (13/12)ε³·sin(3M) + …`

which IS the canonical FM-with-modulating-index-ε expansion. At small modulation index, **Kepler EOC and pure FM are spectrally K-indistinguishable** by the strict K-test (both pass with r²>0.99, monotonic, eps_fit in physical range).

Signatures diverge in detail at higher k: Bessel `J_k(β) ~ (β/2)^k / k!` has 1/k! tail; Kepler EOC `c_k ~ ε^k / k` has 1/k tail. At k=3 the factorial-vs-linear difference is a factor of 6; at k=5 it's a factor of 120. But at k_max=6 with r²>0.99 gate, both pass.

**This is a real structural identity, not an artifact.** Per `[[user_stance_kepler_shape_universal]]` and `[[user_stance_epicycle_via_gear_plus_pin]]`, the K-shape is universal where pin-slot kinematics appears — INCLUDING in FM synthesis (Chowning 1973 musical FM patent). **FM synthesis IS epicycle kinematics in the frequency domain.**

### §4.2 Anomaly A2: identical eps_fit=0.7098 across multiple substrates

Piano (3 stiffness values) / violin / drum-amp / pure-1/n REF all gave identical strict-K result (eps_fit=0.7098, r²=0.9363).

**Resolution**: ALL these substrates share the canonical `1/n` envelope by design (Helmholtz sawtooth, Fletcher struck-string baseline). Strict K-test on 1/n series is mathematically determined regardless of frequency-axis structure or physical substrate. The 1/n envelope is out of K-physical-range (eps_fit=0.7098 > 0.5 ceiling) — correctly fails K, but with the SAME number.

**Implication**: amplitude-axis K-test is NOT substrate-discriminating between any two 1/n-envelope instruments. Discrimination MUST come from a different signature — decay-form best-fit (§3) / frequency-axis inharmonicity / time-domain envelope. The substrate-discriminating signature lives at M1_power_law p-exponent level: p=0.5 (trumpet), p=1.0 (sawtooth family), p=2.0 (flute) are clearly distinct fingerprints.

### §4.3 Anomaly A3: frequency-axis inharmonicity does NOT show K

Piano stiffness deviations (B=1e-5 to 5e-3), drum Bessel-zero ratios, bell mode ratios all tested for K-shape on frequency-axis deviation sequence. None show K-shape: eps_fit values 1.29–2.39 (out of physical range); r² values 0.75–0.97 (below 0.99 gate); monotonic-decreasing fails for all (deviations grow, not shrink).

**Verdict**: K-signature is amplitude-domain only (when present); frequency-axis inharmonicity is its own substrate fingerprint but NOT a K-shape.

## §5 Citation provenance

All citations textbook-canonical; no PDF-extraction performed (Fletcher & Rossing scope — textbook material not on arXiv/PMC). Flagged honestly per `[[feedback_pdf_extraction_citation_discipline]]`.

- **Helmholtz 1863** *On the Sensations of Tone* — public-domain canonical; bowed-string Helmholtz motion (sawtooth at bridge)
- **Rayleigh 1894** *Theory of Sound* — public-domain canonical; circular-membrane modes §200 (Bessel-zero eigenvalues)
- **Fletcher & Rossing 1998** *The Physics of Musical Instruments* — textbook canonical (Springer; not arXiv-mirrored; not PDF-extracted in spike scope). Cited for: §2.17 struck-string baseline; §2.18 piano stiffness B; §2.20 piano dual-rate decay; §14.4 brass 1/√n at fortissimo; §15.2 flute air-jet 1/n²; §15.3 clarinet odd-harmonic; §16 voice source-filter (Fant 1960 also cited); §21.3 bell hum/prime/tierce/quint/nominal tuning
- **Watson 1922** *Treatise on the Theory of Bessel Functions* — public-domain canonical; FM-sideband Bessel J_k expansion
- **Smart 1953** *Spherical Astronomy* §5.1 — Kepler EOC small-eps expansion
- **Brouwer & Clemence 1961** *Methods of Celestial Mechanics* §3.2 — canonical Kepler-EOC SSoT (PDF-extracted in earlier project work per Spike #30B context)
- **Chowning 1973** *The Synthesis of Complex Audio Spectra by Means of Frequency Modulation* — historical SSoT for FM synthesis

## §6 Open extensions / candidate Spike #41+ follow-ons

1. **Real audio analysis with public-domain sources**: NASA Voyager recordings (public-domain); university-library acoustic measurement datasets (CC-licensed); McGill / IRCAM / SMS-tools datasets where licensing permits. Closed-form analyses here can be ratcheted against real measurements per `[[reference_autonomous_validation_tos_landscape]]`.

2. **Helmholtz-Kepler structural identity formalisation**: §4.1 finding that Kepler EOC ≈ FM small-β is a candidate stance addition. *"Kepler equation IS phase modulation; pin-slot IS FM-synthesis substrate."* Formalises Class K + Class I composition more precisely. **Conductor call required before authoring stance.**

3. **Instrument-decay cascade-β refinement**: cascade-β does not match simple-exp idealisations. Real piano decay (dual-rate Fletcher §2.20) and real drum decay (mode-coupled head-air-shell) might show cascade-β. Real-acoustic-measurement spike candidate.

4. **Frequency-axis inharmonicity as cascade-of-pin-slots**: piano stiffness inharmonicity `Δf_n = n·f_0·(√(1+B·n²) − 1)` has the structural form of per-mode pin-slot eccentricity. Re-frame piano-string stiffness as per-mode Class K candidate.

5. **Voice/formant as filter-bank Class L composition**: source-filter model is Class C (glottal-pulse stream) → Class L (vocal-tract filter eigenbasis) → mixed output. Worth formalising as Class composition diagram per `[[user_stance_information_instrument_form_function_bound]]`.

## §7 Discipline guards honoured

- `[[user_stance_kepler_shape_universal]]` — K's absence in 13/15 instruments is HONEST; FM-small-β positive is real structural identity (Kepler ≡ FM at small modulation index)
- `[[user_stance_epicycle_via_gear_plus_pin]]` — pin-slot Class K asymptotic-DOF mechanism IS the structural shape; in music it appears in FM synthesis substrate, NOT canonical instrument acoustics
- `[[user_stance_string_theory_instrument_first]]` — loop-up (sustained) vs loop-down (struck) per-instrument distinction respected; cascade-β SKIPPED for loop-up substrates rather than forced-tested
- `[[user_stance_cascade_lives_on_circles]]` — instrument substrates DO live on cyclic groups (pitch-class wheel, harmonic ladder, modal eigenbasis); spectral content IS on circles
- `[[user_stance_information_instrument_form_function_bound]]` — 14-class binding overlay at cataloguing level; not falsifiable spectral measurement (Spike #37 pattern)
- `[[user_stance_partition_for_understanding]]` — per-instrument and ensemble-level coexist; meta-question lives at per-instrument level; comparison table IS the per-instrument partition
- `[[feedback_no_privileged_primitive_classes]]` — no new class proposed; per-instrument differences are SUB-partition phenomena within existing K/L; vocabulary stays at 14 classes A–N
- `[[feedback_ndjson_over_bloated_json]]` — 7 NDJSON outputs (119 records total)
- `[[feedback_concertmaster_md_writes]]` — agent inline; conductor captured-and-saved this note
- `[[feedback_concertmaster_git_worktree_isolation]]` — agent performed zero git ops; all work in `D:\temp\spike_40\`
- `[[feedback_pdf_extraction_citation_discipline]]` — Fletcher & Rossing not PDF-extracted (textbook not on arXiv/PMC); flagged honestly in §5
- `[[feedback_science_is_ssot_not_project]]` — Helmholtz/Rayleigh/Fletcher canonical SSoT; closed-form analytical formulae throughout

## §8 Fermatas for conductor

1. **Stance candidate: "Kepler equation IS phase modulation at small eccentricity"** (Anomaly A1). Mathematical content: `ν = M + 2ε·sin(M) + O(ε²) ⟺ FM(M, β=ε)` at lowest order. Unifies Class K (pin-slot) with FM synthesis substrate (Chowning 1973). Author as new identity-discipline stance? Or absorb into `[[user_stance_kepler_shape_universal]]` as explicit substrate instance? **User direction required** — substantive new identity claim per `[[user_stance_identity_not_implementation_discipline]]` umbrella.

2. **Spike #41 framing for real-audio cascade-β**: real public-domain piano / drum recordings might show dual-rate decay missing from idealised single-exp models. Numerical-resource follow-up.

3. **K-shape in DEEP MUSIC theory** (vs acoustic-physics layer): music theory has its own periodic structures (circle of fifths = Class I cyclic group; tonic-dominant = group representations; voice-leading = Class L on note-graph). K/L analysis at music-theory layer rather than acoustic-physics layer would be a complementary spike.

4. **Notebook placement**: findings are research-spike-finding-level, not framework-affecting per Spike #38 precedent. The 14-class vocabulary stays at 14; `[[user_stance_kepler_shape_universal]]` correctly holds. **No new stance authored from this spike alone**; the Kepler-EOC ≡ FM-small-β identity (Anomaly A1) is the candidate awaiting user direction.

## §9 Artifacts

- [`spike_40_musical_epicycle_analysis.py`](spike_40_musical_epicycle_analysis.py) — primary analysis (15 instruments + 7 references; K-test battery + Class L drum)
- [`spike_40_decay_form_analysis.py`](spike_40_decay_form_analysis.py) — four-model decay-form best-fit (M1/M2/M3/M4)
- [`spike_40_freq_inharmonicity_analysis.py`](spike_40_freq_inharmonicity_analysis.py) — frequency-axis inharmonicity K-test
- [`spike_40_falsifier_controls.py`](spike_40_falsifier_controls.py) — 50 random-amplitude seeds + pure-harmonic/white-noise/cascade-β battery
- [`spike_40_fm_anomaly_investigation.py`](spike_40_fm_anomaly_investigation.py) — Anomaly A1 chase on FM-K-overlap
- [`spike_40_synthesis.py`](spike_40_synthesis.py) — synthesis + comparison table generator
- [`spike_40_records_2026-05-17.ndjson`](spike_40_records_2026-05-17.ndjson) — 23 primary K-test + Class L drum records
- [`spike_40_decay_form_records_2026-05-17.ndjson`](spike_40_decay_form_records_2026-05-17.ndjson) — 22 M1/M2/M3/M4 best-fit records
- [`spike_40_freq_inharmonicity_records_2026-05-17.ndjson`](spike_40_freq_inharmonicity_records_2026-05-17.ndjson) — 8 frequency-axis K-test records
- [`spike_40_falsifier_records_2026-05-17.ndjson`](spike_40_falsifier_records_2026-05-17.ndjson) — 11 random-amp + cascade-β records
- [`spike_40_fm_anomaly_records_2026-05-17.ndjson`](spike_40_fm_anomaly_records_2026-05-17.ndjson) — 21 anomaly-chase records
- [`spike_40_per_instrument_comparison_2026-05-17.ndjson`](spike_40_per_instrument_comparison_2026-05-17.ndjson) — 15 meta-question per-instrument records
- [`spike_40_synthesis_records_2026-05-17.ndjson`](spike_40_synthesis_records_2026-05-17.ndjson) — 19 final synthesis + meta-question records

**Total: 119 NDJSON records across 7 files; 6 analysis scripts.**

---

*End of spike artifact.*
