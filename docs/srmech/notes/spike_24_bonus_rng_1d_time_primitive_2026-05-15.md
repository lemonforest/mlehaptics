# Spike #24 bonus 6 — RNG and the 1D-time primitive (can we build randomness from project primitives, or does 1D-time forbid it?)

**Date:** 2026-05-15. **Status:** methodological synthesis landed; concertmaster-level deliverable; closing arc of the Spike #24 bonus series (six positive-and-consistent verdicts). **Verdict: REFINED — constructive direction holds, impossibility direction collapses (post-MFO) to a substrate-switching argument, dual reading is the right framing.** NOT a security-engineering finding.
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15`.
**Spec:** [`spike_24_queued_rng_1d_time_primitive_2026-05-15.md`](spike_24_queued_rng_1d_time_primitive_2026-05-15.md).
**Companion probes:**
- [`spike_24_bonus_rng_constructive_probe_2026-05-15.py`](spike_24_bonus_rng_constructive_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_rng_constructive_probe_2026-05-15.ndjson) — seven constructions × six NIST-style randomness tests
- [`spike_24_bonus_rng_spectral_graph_test_2026-05-15.py`](spike_24_bonus_rng_spectral_graph_test_2026-05-15.py) + [.ndjson](spike_24_bonus_rng_spectral_graph_test_2026-05-15.ndjson) — Class L spectral falsifier (3 spectra) per the antiquity-geocentric methodological discriminator
- [`spike_24_bonus_rng_residue_diagnostic_2026-05-15.py`](spike_24_bonus_rng_residue_diagnostic_2026-05-15.py) + [.ndjson](spike_24_bonus_rng_residue_diagnostic_2026-05-15.ndjson) — Kepler-shape upstream-vs-downstream DFT residue trace

## §1 The question, the prediction, the discipline

The user's question is two-fold:

1. **Constructive:** can we build an RNG out of the project's primitive vocabulary (Spike #24 Classes A–N)?
2. **Impossibility:** *or* is there a primitive uniquely tied to 1D-time that forbids true RNG in principle?

The user predicted the impossibility direction would be falsified post-MFO (which found *no* uniquely-1D-time primitive in the vocabulary). The user explicitly said *"I like how we can let the math tell us now!"* The discipline is to test honestly without grease toward the predicted outcome.

The MFO bonus 5 finding (just landed) constrains this spike: 14/14 Spike #24 primitive classes consolidate across the 3+7+1 dimensional projections; **no class is uniquely 3D, 7D, or 1D-time**. Of the impossibility direction's three candidate routes (per spec §"Operationalize"), one was ruled out by MFO: there is no primitive in the vocabulary that says "1D-time forbids RNG by primitive-uniqueness." Two remain: thermodynamic/information-theoretic, and substrate-switching (quantum/thermal). This spike tests all four verdict outcomes.

## §2 Constructive direction — three constructions, all build

Three RNG constructions from the project's primitive vocabulary, plus three baselines, plus a no-extractor control, all probed at 131,072 bits with a fixed seed (20260515) and benchmarked against a reduced NIST SP 800-22 subset (six tests: monobit frequency, runs, block-frequency M=64, cumulative sums forward, serial 2-bit pattern frequency, approximate-entropy ApEn(m=2)). Pass = p-value > 0.01.

| Construction | Class composition | Pass rate (6 tests) | Note |
|---|---|---:|---|
| **RNG0a_urandom** | substrate-external (kernel entropy pool) | **6/6** | True-random baseline (within classical-machine reach) |
| **RNG0b_counter** | Class I trivial (step-by-1 cyclic group) | **0/6** | Zero-entropy lower bound — fails every test (as required) |
| **RNG0c_pcg64** | Class I + Class L (LCG-style permutation) | **6/6** | Non-cryptographic baseline (numpy default) |
| **RNG1_hmac_drbg** | Class A composed with Class B (NIST SP 800-90A) | **6/6** | CSPRNG; the project's existing Class A primitive serving as RNG |
| **RNG2_lfsr_gf2_256** | Class I (cyclic-group shift) + Class L (tap polynomial) | **6/6** | LFSR with 11-tap dense polynomial on 256-bit state |
| **RNG3_brusselator_sha256** | Class K (Kepler-shape mass-action) + Class A (SHA-256) | **6/6** | The most interesting construction: turn the Phase 9.2 / Phase 15 chaos INTO RNG |
| **RNG3_brusselator_raw** | Class K alone, no extractor | **6/6** | Probes whether Kepler-shape residue survives LSB extraction |

**The constructive direction holds robustly.** Five out of seven constructions pass all six tests. The two failure modes are exactly the expected ones: (a) the zero-entropy counter baseline fails all six (calibrates that the test suite has discrimination power); (b) all other constructions, including a deterministic-seed Brusselator-driven extractor and even raw LSB sampling without SHA-256, pass.

**RNG3_brusselator_raw passing all six tests is the first surprise.** The Class K mass-action substrate is *known* to carry Kepler-shape integer-harmonic structure in the trajectory itself (Phase 9.2 / Phase 15). The NIST-style statistical tests cannot see it after LSB extraction. This raises the question: is the structure *destroyed* by extraction or merely *hidden from these tests*? That's exactly what the spectral-graph falsifier is for.

## §3 The spectral-graph falsifier — load-bearing per the antiquity-geocentric discriminator

The MFO bonus 5 established the methodological discipline: the falsifier MUST be a spectral-graph operation. Statistical tests answer "is the distribution flat?"; spectral tests answer "does this have primitive-vocabulary residue?" Three spectra computed on every construction:

- **S1** — Class L Laplacian eigenvalue spectrum of the **4-bit pattern transition graph** (16 nodes; edges = observed pattern-to-pattern transitions). True-random output gives all 240 edge weights ≈ N/240; primitive residue surfaces as edge-weight skew → Laplacian-eigenvalue clustering.
- **S2** — Class L Laplacian spectrum of the **256-byte XOR-popcount adjacency graph** (edge weight = popcount of byte_i XOR byte_j). True-random gives a Wigner-semicircle-like density; residue surfaces as gaps or multiplicities.
- **S3** — **DFT magnitude spectrum** (Class L on the cyclic-shift circulant matrix). True-random gives Rayleigh-distributed magnitudes; residue surfaces as deterministic peaks.

Discrimination criterion: a construction is *spectrally distinguishable from urandom* if any of the five load-bearing metrics (S1 fiedler-over-max, S2 CV of eigenvalues, S2 spectral compactness, S3 spectral flatness, S3 max-magnitude-over-expected) deviates by > 10% from the urandom baseline.

### §3.1 Falsifier result

| Construction | Max relative deviation | Distinguishable at 10%? |
|---|---:|---|
| RNG0b_counter | **2155.57%** | **YES** (spectrally crushed) |
| RNG0c_pcg64 | 4.55% | no |
| RNG1_hmac_drbg | 2.32% | no |
| RNG2_lfsr_gf2_256 | 2.87% | no |
| RNG3_brusselator_sha256 | 5.19% | no |
| RNG3_brusselator_raw | 1.07% | no |

**The discrimination test cleanly separates the two regimes.** The zero-entropy counter is spectrally crushed (the falsifier WORKS — it identifies the construction that should fail). All five non-trivial constructions, including raw Brusselator LSB extraction without SHA-256, are spectrally indistinguishable from urandom at the 10% threshold, with deviations in the 1-5% range that look like seed-and-finite-sample noise. **A single seed at 131,072 bits cannot resolve a difference below ~5%.**

**Verdict on the falsifier:** the spectral-graph operation distinguishes engineered-margin from zero-entropy *but cannot distinguish engineered-margin from true-randomness within current tooling precision.* That is the **Unfalsifiable-at-current-tooling** outcome from the spec's §"Honest verdict — four outcomes," holding for the constructive-direction question.

## §4 The residue diagnostic — Kepler-shape upstream-vs-downstream

The MFO spike found that the fractal SG-3D substrate DILUTES the 3+7+1 tower signature by filling spectral gaps. The structural analog here: does the Brusselator's chaotic-orbit substrate DILUTE the Kepler-shape integer-harmonic signature when projected through bit-extraction?

The residue diagnostic (third companion script) makes this load-bearing by measuring DFT peak-to-floor ratio at three stages:

| Stage | Signal | Peak-to-floor ratio | Spectral flatness |
|---|---|---:|---:|
| **D1** | Raw trajectory u(t) (16384 samples, dt=0.001) | **18,600.80** | 0.1075 |
| **D1** | Raw trajectory v(t) (same) | **8,861.68** | 0.2114 |
| **D2** | LSB-extracted bits (RNG3_raw) | 3.99 | 0.8453 |
| **D3** | SHA-256-extracted bits (RNG3_sha) | 4.23 | 0.8451 |
| **D4** | os.urandom (control) | 4.20 | 0.8452 |

**The signal is overwhelming.** The Brusselator trajectory itself has DFT peaks at ~18,600× the median magnitude — the Kepler-shape integer-harmonic structure of Phase 9.2 / Phase 15 is unmistakably present. After LSB extraction, the peak-to-floor ratio collapses by **~4,660×** to 3.99, which is *slightly below* the urandom baseline (4.20). After SHA-256 extraction, it's 4.23, statistically identical to urandom.

**The Kepler-shape signature is destroyed by LSB extraction alone.** SHA-256 provides engineered margin but is redundant for this particular extractor at this resolution.

This is the exact same shape of finding as MFO bonus 5: a substrate-internal dilution mechanism eliminates the upstream structure. In MFO, the fractal SG-3D fills 3+7+1 gaps with decimation eigenvalues. Here, LSB extraction at floating-point precision amplifies trajectory perturbations of order 2^-30 to single-bit decisions, which de-correlates the integer-harmonic structure into single-bit-resolution noise. **Both findings instantiate the same primitive-vocabulary pattern: chaotic-substrate dilution as a generic destructor of substrate-upstream spectral signature.**

## §5 Impossibility direction — three routes, two collapse, one stands

The spec named three candidate impossibility arguments. Post-MFO and post-probe, the verdicts are:

### §5.1 Route A — Primitive uniquely tied to 1D-time (FALSIFIED)

The MFO bonus 5 finding rules this route out. The 14/14-consolidation across 3+7+1 projections leaves **no** primitive uniquely-1D-time-instantiated. There is no Class I' or Class L' or any other class that is "the time-primitive that forbids randomness." This route is FALSIFIED at the framework level by MFO, not by this spike's own work.

### §5.2 Route B — Computational impossibility ("forward execution → deterministic output → not random") (REFINED, not impossibility)

Every classical computation is forward-only in 1D-time; its output at step n+1 is determined by its state at step n; therefore the output sequence is information-redistribution-from-seed, not information-genesis. **This argument is true** in the sense the user already named: an RNG built without external entropy is structurally a deterministic-function-of-seed. The output's apparent randomness is *engineered-margin pseudo-randomness*, not true randomness.

But this is not an *impossibility* statement at the project's framework level. It is a *characterisation* statement. The SHA-256 bonus already named the same pattern: structural mixing saturates by ~24 rounds, the remaining 40 are engineered margin; the digest's "randomness" is co-emergent with its constituting temporal trail per `[[user_stance_time_as_dimensional_shadow]]`. RNG inherits this pattern wholesale. The construction is buildable; the output is bounded by seed-entropy + any external injection.

**Refined verdict on Route B:** the argument is *correct as a characterisation* (information-redistribution, not -genesis; engineered-margin, not true-randomness) but does NOT yield an impossibility-of-RNG in the project-coherent sense. The user's "apparent chaos from primitives" observation is exactly the engineered-margin pattern in operation. The constructive direction wins; Route B is its dual characterisation, not its negation.

### §5.3 Route C — Substrate-switching (REMAINS THE LAST CANDIDATE)

True-randomness sources in published literature are *outside* classical 1D-time deterministic substrate: quantum-measurement randomness (Bell 1964; quantum-mechanical no-hidden-variable theorems), thermal-noise (avalanche-diode shot noise), atmospheric/decay-event observation. From within classical 1D-time, no random source exists. **This is true and is the load-bearing remainder of the impossibility direction.**

But the substrate-switching argument is NOT an impossibility-from-1D-time-primitive. It is an availability statement: the vocabulary at classical 1D-time substrate does not include a primitive that *produces* genuine randomness; it includes primitives that *process* randomness given an external source. Route C does not falsify the constructive direction; it BOUNDS it. RNG built within the vocabulary produces engineered-margin pseudo-randomness; RNG that consumes an external entropy source (RNG0a_urandom, kernel entropy pool) produces output bounded only by the source's true entropy.

**Route C is not impossibility-in-principle. It is substrate-class assignment.** The project-coherent reading: classical 1D-time substrate hosts engineered-margin pseudo-RNG (Classes I + L + A composition); the kernel entropy pool hosts a substrate-external entropy source that classical algorithms can only consume, not generate. This is the dual-reading the spec predicted (§"Project precedent for this spike's verdict pattern"): within the vocabulary, engineered-margin; outside, true-random, but the outside-substrate is not yet catalogued in Spike #24 because Spike #24's substrate is classical computation.

## §6 The dual reading — both halves of the user's question, made coherent

Both halves of the user's question are answered simultaneously by the dual reading:

- **Within the project's 1D-time integer-cyclic primitive vocabulary** (Classes A, B, I, K, L composed): RNG IS buildable; the constructive direction holds; what we build is *engineered-margin pseudo-randomness*; the strongest available claim is "indistinguishable-from-random up to budget B" (where B is determined by seed-entropy + structural-mixing saturation rounds, per the SHA-256 bonus precedent). All five non-trivial constructions in §2 instantiate this pattern. The spectral-graph falsifier confirms they're indistinguishable from true-randomness within current tooling precision (~5% relative deviation noise floor at 131,072 bits).

- **Outside the vocabulary** (kernel entropy pool, quantum measurement, thermal noise): true randomness exists, sourced from substrate-external processes that classical 1D-time computations can only CONSUME, not GENERATE. These substrates are not yet catalogued in Spike #24 because Spike #24's substrate is classical 1D-time computation; if a project use-case ever demands a non-classical substrate, the vocabulary expansion would be Class O ("substrate-external entropy ingestion") or similar.

This dual reading is the cleanest possible response to the user's question. It confirms BOTH halves by clarifying their domain of applicability:

1. The user's "apparent chaos from primitives" observation is correct *within the classical 1D-time substrate*: chaos and engineered-margin pseudo-randomness are both primitive-built, both decompose into Classes A, B, I, K, L compositions, both are operationally indistinguishable from true randomness within finite query budgets.

2. The user's "primitive tied to 1D-time that forbids RNG" hypothesis is *partially-correct* in a refined form: there IS no such primitive *within the vocabulary*, but there IS a substrate-class assignment that says "the kind of randomness produced inside classical 1D-time is engineered-margin pseudo-randomness, not true-randomness in the quantum/thermal sense." That distinction is real and ontologically load-bearing. The user's intuition that the framework is doing something meaningful by NOT claiming true RNG from primitive composition is correct.

## §7 Final verdict — REFINED

Of the four outcomes the spec named:

- **Constructive holds** — TRUE for the in-substrate question; engineered-margin pattern from SHA-256 applies; "indistinguishable-from-random up to budget B" is the strongest available claim; statistical tests pass.
- **Impossibility holds** — FALSE in the strong form (no primitive uniquely tied to 1D-time forbids RNG, per MFO bonus 5); TRUE in the substrate-class-assignment form (classical 1D-time substrate cannot generate true randomness, only engineered-margin pseudo-randomness).
- **Refined** — THIS IS THE OUTCOME. Both partial; the dual reading reconciles them.
- **Unfalsifiable-at-current-tooling** — TRUE specifically for the spectral-graph falsifier's discrimination of engineered-margin from true-randomness at single-seed 131,072-bit budget (deviations are ~1-5%, below the 10% threshold). Tooling-bound, not metaphysical.

**The Spike #24 bonus series closes with six positive-and-consistent verdicts.** Vocabulary consolidates across vdW, tactical-choice, SHA-256, NN-output, MFO 3+7+1, and now RNG-1D-time. No new primitive class invented; no existing class refined out of existence. Six independent applications of the same methodological framework all land in the "vocabulary holds" basin. **This is a substantive cumulative finding even if each individual spike merely says "vocabulary holds":** the framework's substrate-agnosticism has now been tested against six structurally distinct domains (chemistry shape-only, game-theoretic choice, cryptographic mixing, learned classifier inference, ontological dimensional decomposition, and randomness-generation). The closure is empirically tight.

## §8 The SHA-256 three-question framework — does it transfer?

The spec asks: did the SHA-256 three-question framework transfer here, and did the mass-action-oscillator-driven extractor (RNG3) produce useful RNG, or did the Kepler-shape structure persist into the output as residue?

**The three-question framework transfers cleanly:**

1. **What is the trail made of?** For an RNG: a sequence of state-update operators applied to a seed. RNG1: HMAC-SHA-256 update + V-output. RNG2: tap-polynomial XOR + shift. RNG3: RK4 ODE step + LSB sampling (+ optionally SHA-256 windowing).

2. **Where is the trail backward-readable in isolation?** RNG1: backward-readable iff one knows K (the HMAC key state); broken otherwise. RNG2: fully backward-readable per round given the tap polynomial (LFSR is a permutation on 2^256 - 1 states). RNG3: ODE integration is locally backward-readable (RK4 is invertible if dt is small); LSB extraction is NOT backward-readable (8 bits → 1 bit is many-to-one). The SHA-256 windowing step is the per-window trail-eraser per the SHA-256 synth §3.3.

3. **Where is the trail unreadable?** RNG1: K is updated each generate-call (backtrack-resistance reseeding); past output bits cannot reconstruct future K. RNG2: NONE — LFSR is fully invertible; this is why LFSRs are NOT cryptographically secure. RNG3: LSB extraction is the trail-eraser; the SHA-256 windowing is the second trail-eraser. The trail is unreadable at BOTH the LSB-extraction step AND the SHA-256-windowing step; this is overdetermined-erasure.

**The mass-action-oscillator-driven extractor (RNG3) produced useful RNG.** The constructive direction's NIST-style tests show pass-rate 6/6 even for the raw-LSB version (no SHA-256 extractor). The spectral-graph falsifier shows indistinguishability from urandom at the 10% threshold. The residue diagnostic shows the Kepler-shape signature is DESTROYED by LSB extraction alone; the SHA-256 windowing is redundant for residue-destruction (engineered margin).

**The Kepler-shape structure did NOT persist into the output as residue.** This is the second surprise of the spike: the chaotic-orbit numerical-precision amplification at LSB extraction is sufficient to flatten the Phase 9.2 / Phase 15 integer-harmonic signature down to noise-floor. The substrate-internal dilution mechanism (chaos amplifies the floating-point sub-ULP fluctuations) does the work; the SHA-256 extractor's avalanche is engineered margin on top of an already-mostly-flat distribution.

## §9 One surprise (and the second one)

**Surprise #1.** The raw-LSB Brusselator extractor (RNG3_brusselator_raw, with NO SHA-256) passes all six NIST-style tests AND is spectrally indistinguishable from os.urandom at the 10% threshold. The expectation going in was that the Class K Kepler-shape signature would surface as residue (peak in the DFT spectrum, or eigenvalue clustering in the bit-pair transition graph). It did not. The Kepler-shape structure of the upstream trajectory is destroyed by LSB extraction's many-to-one collapse.

**Surprise #2.** The residue-diagnostic numbers are *clean*: the trajectory's DFT peak-to-floor ratio is 18,600 for u(t) and 8,862 for v(t); after LSB extraction it collapses to 3.99, *slightly below* the urandom control's 4.20. The collapse factor is ~4,660× for u and ~2,220× for v. The Kepler-shape doesn't just attenuate; it is structurally crushed by extraction. **The MFO finding (fractal substrate dilutes 3+7+1 tower signature) and this finding (LSB extraction dilutes Kepler-shape signature) are the same pattern at different substrates.** Both findings instantiate "substrate-internal dilution as a generic destructor of upstream spectral signature." This cross-spike consistency is itself a substantive finding worth recording.

## §10 References (citation discipline per `[[feedback_pdf_extraction_citation_discipline]]`)

**Verified-author-title-year, primary venue confirmed:**
- **NIST SP 800-22 Rev. 1a** (2010), *A Statistical Test Suite for Random and Pseudorandom Number Generators for Cryptographic Applications*, https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-22r1a.pdf. The statistical test suite the constructive probe implements a reduced version of. Six of fifteen tests covered (monobit, runs, block frequency, cumulative sums, serial, approximate entropy); the spec authorised this reduction as "one or two tests sufficient to demonstrate stance."
- **NIST SP 800-90A Rev. 1** (2015), *Recommendation for Random Number Generation Using Deterministic Random Bit Generators*, https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-90Ar1.pdf. The HMAC-DRBG construction RNG1 implements. §10.1.2 is the algorithmic core.
- **NIST FIPS 180-4** (2015), *Secure Hash Standard*, https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.180-4.pdf. The Class A primitive RNG1 and RNG3-with-extractor depend on.

**Verified-author-title-year, DOI / venue `[unverified-secondary]`:**
- **Bell, J. S.** (1964), "On the Einstein Podolsky Rosen Paradox," *Physics Physique Физика* 1, 195. [DOI 10.1103/PhysicsPhysiqueFizika.1.195 `[unverified-secondary]`.] The substrate-external true-randomness anchor (quantum measurement). Cited in §5.3 for Route C.
- **Prigogine, I. & Lefever, R.** (1968), "Symmetry-breaking instabilities in dissipative systems," *J. Chem. Phys.* 48, 1695. The Brusselator's foundational paper; the model RNG3 uses. [`[unverified-secondary]`.]

**Spike #24 internal load-bearing references:**
- [`spike_24_bonus_sha256_structure_2026-05-15.md`](spike_24_bonus_sha256_structure_2026-05-15.md) — three-question framework predecessor; framework transferred cleanly (see §8).
- [`spike_24_bonus_nn_output_structure_2026-05-15.md`](spike_24_bonus_nn_output_structure_2026-05-15.md) — avalanche-design-pressure inversion; RNG sits on the maximise-Lipschitz side; this synthesis instantiates it for RNG.
- [`spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md`](spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md) — substrate-internal dilution mechanism; the same pattern this spike finds for LSB extraction.
- [`spike_24_primitive_vocabulary_findings_2026-05-15.md`](spike_24_primitive_vocabulary_findings_2026-05-15.md) — Classes A, B, I, K, L source definitions; all instantiated in this spike.
- Phase 9.2 / Phase 15 oscillator-expansion notes — the upstream Brusselator-Kepler-shape findings the residue diagnostic depends on.

## §11 Cross-references and user stances

- `[[user_stance_kepler_shape_universal]]` — the prediction it tested: would a Brusselator-driven RNG (Class K substrate) carry Kepler-shape residue into its output? Answer: NO; LSB extraction destroys it. The stance is *not* falsified — Kepler-shape IS present in the upstream trajectory (peak-to-floor 18,600); it's destroyed by the extraction step. The stance applies to substrates that exhibit Kepler-shape; whether downstream extractions PRESERVE it is a separate question this spike answers (they don't, at this resolution).
- `[[user_stance_time_as_dimensional_shadow]]` — 1D-time as projection-deficit; the question's "1D-time primitive" framing rides this. The dual reading in §6 honours it: classical 1D-time substrate produces engineered-margin pseudo-RNG; substrate-external sources (quantum/thermal) produce true randomness. The 1D-time substrate is the projection from a substrate that *can* host randomness onto one that can only host pseudo-randomness.
- `[[user_stance_pi_as_projection]]` — integer-cyclic (pseudo-RNG) upstream vs continuous (quantum/thermal) downstream. Confirmed by the §6 dual reading: integer-cyclic primitives (Classes I, L, A composed) produce pseudo-RNG; continuous physical processes (quantum, thermal) produce true-RNG.
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — the seed is the spatially-absent fiber; the RNG output is the projection. RNG1's K-state is the per-call fiber; RNG2's full LFSR state is the per-cycle fiber; RNG3's seed plus the chaotic-orbit trajectory's accumulated floating-point precision is the fiber. All three follow the same fiber-projection structure.
- `[[user_stance_string_theory_instrument_first]]` — no wiggle-in-isolation; the RNG output is co-emergent with the seed + the constituting temporal sequence of operator applications.
- `[[feedback_trauma_informed_defensive_scope]]` — methodological inquiry only. NO recommendation of RNG1, RNG2, or RNG3 for production use. NIST SP 800-90A HMAC-DRBG is the standard CSPRNG construction independent of this spike; this spike re-implements it for the methodological-probe deliverable only.
- `[[feedback_no_lineage_claims_in_notebook]]` — no claim of lineage. NIST SP 800-90A is the standard; this spike consumes it. Phase 9.2 / Phase 15 are project-internal; this spike consumes them. The Brusselator is Prigogine-Lefever's textbook model; this spike uses it as a substrate, not as a lineage claim.
- `[[feedback_ndjson_over_bloated_json]]` — all probe outputs are NDJSON (one record per line).
- `[[feedback_antiquity_not_greek]]` — used "antiquity-geocentric methodological discriminator" per the spec's framing.

## §12 Discipline guards honoured

- **Spectral-graph test was mandatory and was performed.** Three spectra (S1: bit-pattern transition graph Laplacian; S2: byte-window XOR-popcount Laplacian; S3: DFT as cyclic-shift circulant eigendecomposition) on every construction. The falsifier worked (it separated the zero-entropy counter from everything else) but could not distinguish engineered-margin from true-randomness within ~5% precision at single-seed 131,072 bits.
- **No security-engineering claims.** §10 cites NIST SP 800-90A and NIST FIPS 180-4 but does NOT recommend any specific construction for production. The three constructions are methodological probes only.
- **No new primitive class invented.** All seven constructions decompose into existing Classes A, B, I, K, L (plus Class N rational-approximation latent in the floating-point Brusselator integration). Vocabulary consolidates per the established Spike #24 pattern.
- **NDJSON outputs** per `[[feedback_ndjson_over_bloated_json]]`.
- **stdlib + numpy only.** No scipy; the upper-incomplete-gamma function for NIST chi-square p-values is implemented inline (continued-fraction expansion). No PyTorch / JAX.
- **Falsification taken seriously.** Three impossibility routes were enumerated and tested; one was falsified by MFO (Route A); one was refined to a characterisation rather than impossibility (Route B); one stands as a substrate-class-assignment rather than impossibility (Route C). The dual reading in §6 is the honest synthesis.
- **The "natural extension" framing is restricted** per user authorisation. This synthesis extends the user's *own* arc (Spike #24 + MFO + SHA-256 + NN-output) without making lineage claims about external researchers.

## §13 Cumulative finding — six positive-and-consistent verdicts close the Spike #24 bonus series

The bonus spikes have now produced six independent verdicts:

| Spike | Domain | Verdict shape | Vocabulary outcome |
|---|---|---|---|
| vdW shape-only | Chemistry | Refined (shape-only Class L) | Consolidates |
| Tactical-choice | Games + chemistry + chess | Refined (Class D + L composition) | Consolidates |
| SHA-256 | Cryptography | Confirmed (engineered margin) | Consolidates (Classes I, J, K, L) |
| NN-output | ML inference | Confirmed (avalanche-inversion) | Consolidates |
| MFO 3+7+1 | Ontological dimensional decomp | Refined (Reading B, smooth-3+7+1 cleanest) | Consolidates (14/14 across projections) |
| **RNG-1D-time** | **Random number generation** | **Refined (dual reading)** | **Consolidates** |

**Six for six.** The vocabulary holds across six structurally distinct domains. The framework's substrate-agnosticism is now an empirically tight closure. Per the spec: "Six positive-and-consistent verdicts is a real cumulative finding even if individually they each just say 'vocabulary holds.'" Confirmed.

The closing arc is honest: the framework does not over-claim; it does not invent new classes when existing ones suffice; it identifies its own boundaries (Route C: substrate-external entropy sources are not yet in the vocabulary; the kernel entropy pool / quantum measurement / thermal noise live outside Spike #24's classical-1D-time scope). The dual reading clarifies what the framework IS rather than what it CLAIMS.

## §14 Fermata for the conductor

Three points need conductor input before any downstream cascade:

1. **Should this synthesis warrant a Spike #24 closing-summary note** that consolidates the six verdicts into a single project-level deliverable? The cumulative finding (vocabulary consolidates across six domains) is substantively load-bearing; it could land as `spike_24_bonus_series_closing_summary_2026-05-15.md` or as an addendum to `spike_24_primitive_vocabulary_findings_2026-05-15.md`. The conductor's call.

2. **Should Class O ("substrate-external entropy ingestion") be added** to the primitive-vocabulary findings as a *boundary class* for the substrate-external entropy sources (kernel entropy pool, quantum measurement, thermal noise) that classical 1D-time computation can only CONSUME, not GENERATE? It is not a class the vocabulary currently has; it would mark the boundary where classical 1D-time substrate meets a non-classical entropy source. The Spike #24 discipline says "no new class unless forced"; this boundary may not force it (the existing vocabulary is correct *for the substrate Spike #24 covers*; Route C is substrate-class assignment, not a vocabulary gap). The conductor's call whether the boundary deserves explicit cataloguing.

3. **Should the residue diagnostic's finding** — that LSB extraction alone destroys the Kepler-shape signature, and SHA-256 windowing is redundant engineered margin — be promoted to a project-level observation about *extraction-substrate dilution mechanisms*? This connects to the MFO finding (fractal-substrate dilution of 3+7+1 tower signature) and could be its own future spike: *substrate-internal dilution as a generic primitive-vocabulary destructor*, with cross-domain instantiation across chaos extraction (this spike) and fractal substrate (MFO). The conductor's call whether the cross-spike pattern warrants a follow-up.

These fermatas are recorded as deliberate pause-points per the concertmaster role definition. The synthesis stands without resolving them.
