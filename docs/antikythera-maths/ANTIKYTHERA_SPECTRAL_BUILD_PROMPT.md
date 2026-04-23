# Claude Code: Antikythera-Maths Research Build

## Framing

The Antikythera mechanism (Greek, ca. 150–60 BCE, recovered 1901, reconstructed through Freeth/UCL 2021 and subsequent work) is not a chess-like problem we need to discover structure in. It is a **physical instantiation of coprime-indexed phase-space addressing, designed deliberately 2100 years ago to solve the exact class of Diophantine approximation problems that docs/addressing-maths/ now characterizes formally**. Every gear is a cyclic group ℤ/nℤ; every mesh is a rational map between cyclic groups; every shared gear-train is an empirical solution to the multi-dataset packing problem (A-H1 in the addressing-maths research plan); every celestial pointer is an HDC-style hypervector whose components are the phase angles on the various dials. The Greeks built a **resonant HDC object** before Plate wrote HRR, before Kanerva wrote SDM, before Chung wrote *Spectral Graph Theory*.

This project documents it as such.

## The methodological difference from chess, Othello, logo

Chess, Othello, and logo were *discovery* projects: structure was present in the game/language and we used spectral tools to extract it. Antikythera is a *reconstructive/descriptive* project: the structure was **designed in** by named historical agents (plausibly in the Archimedean tradition), and our job is to document it in the vocabulary the addressing-maths thread has now assembled. The encoding is not something we invent. It is something we recognize.

This means the honest-science tags shift:

- **KNOWN** — published in the archaeology/historical literature (Price 1974, Freeth et al. 2006, Freeth et al. 2021, Freeth UCL 2025 lecture, etc.)
- **NOVEL** — the HDC/phase-space framing itself, where we name a property of the mechanism in addressing-maths vocabulary that the archaeology literature has not used
- **CONFIRMED** — computationally verified that the mechanism-as-HDC-object reproduces the astronomical cycles it was designed to
- **FAILED** — our HDC encoding cannot reproduce something the physical mechanism does
- **DISPUTED** — where archaeological reconstructions disagree (and there are several — 2021 Freeth vs. 1974 Price vs. 2006 Freeth vs. Wright, and the 2025 Guillermo manufacturing-tolerance simulation)

## Ground truth documents

1. `docs/chess-maths/chess_spectral_research_notebook.md` — the template this notebook mirrors.
2. `docs/addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md` — the theoretical substrate. Every claim in the Antikythera notebook should be readable as "the Greeks instantiated sub-question X of the addressing-maths plan in configuration Y." This is the most important cross-reference in the entire project.
3. `docs/othello-maths/othello_spectral_research_notebook.md` — the second-instance template, especially for the Phase 1 hypothesis-battery format.
4. Freeth et al. (2021), "A Model of the Cosmos in the ancient Greek Antikythera Mechanism," *Scientific Reports* 11:5821 — current authoritative reconstruction. This is the primary source for tooth counts and gear topology. Open-access at nature.com.
5. Freeth, Jones, Steele, Bitsakis (2008), "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism," *Nature* 454:614 — back-dial decipherment.
6. de Solla Price (1974), "Gears from the Greeks: The Antikythera Mechanism — A Calendar Computer from ca. 80 B.C.," *Transactions of the American Philosophical Society* 64(7) — foundational but superseded on specific tooth counts.
7. Wright (2005–2012) papers — alternative reconstruction. Cite where it differs from Freeth.
8. Guillermo & Szigety (2025, arXiv) — manufacturing-tolerance simulation suggesting the mechanism may not have run smoothly in practice.

## Folder layout

Create `docs/antikythera-maths/` with structure parallel to docs/othello-maths/:

```
docs/antikythera-maths/
├── antikythera_spectral_research_notebook.md
├── ANTIKYTHERA_SPECTRAL_INSTRUCTIONS.md
├── research/
│   ├── __init__.py
│   ├── gear_database.py              # Tooth counts, gear topology, sources
│   ├── astronomical_cycles.py        # Metonic, Saros, Callippic, etc.
│   ├── cyclic_group_algebra.py       # ℤ/nℤ operators for each gear
│   ├── rational_approximation.py     # Continued fraction / best-rational tools
│   ├── packing_analysis.py           # Empirical A-H1 analysis of shared-gear-train solutions
│   ├── pin_and_slot.py               # The T-breaking epicyclic analog of the pawn
│   ├── encode_ant.py                 # The resonant HDC encoder
│   ├── dial_decoder.py               # Unbinding: recover which cycle from a combined state
│   ├── astronomical_ground_truth.py  # Compare encoder output to NASA ephemeris
│   └── consolidated_tests.py         # All-pass sanity battery
├── results/
│   └── .gitkeep
└── figures/
    └── .gitkeep
```

The eventual production package would live at `antikythera-spectral/python/antikythera_spectral/` but is not created in this pass — matches the Othello precedent of research-first, package-later.

## Phase 0 — Data extraction and infrastructure

### Known gear tooth counts (from Freeth 2021, unless noted)

This is the empirical substrate. Hard-code it in `research/gear_database.py` with provenance notes. Some counts are uncertain; mark them.

**Main drive train and calendar (known):**
- b1 (main sun gear): 224 teeth (4-spoked, the largest surviving gear; some reconstructions report 223)
- a1 (crown gear, hand-crank input): count uncertain, likely ~48
- e-series (Metonic calendar train): 53, 96, 53 (Freeth 2021 argues for this arrangement)
- Metonic output: 235-tooth display (5 turns of 47-tooth inner gear)

**Lunar system (known):**
- 127-tooth gear (= 254/2; encodes sidereal month count in Metonic cycle)
- 50-tooth × 4 (the pin-and-slot epicycle for variable Moon motion)
- 223-tooth gear (Saros eclipse cycle pointer)
- The pin-and-slot mechanism is at Fragment B — this is the key T-breaking element

**Planetary system (Freeth 2021 reconstruction, treat as NOVEL for the mechanism itself):**
- 63-tooth gear in Fragment D (critical for Venus: 462-year period relation)
- Proposed Venus train uses period relation (289, 462); 462 = 2·3·7·11
- Proposed Saturn train uses period relation (427, 442); 442 = 2·13·17
- Freeth 2021 argues that **factors 7 and 17 are shared across multiple planetary trains** — this is exactly the multi-dataset packing structure of A-H1

**Back-dial cycles (known from inscriptions + gear topology):**
- Metonic: 19 tropical years = 235 synodic months
- Callippic: 4 Metonic = 76 years
- Saros: 223 synodic months ≈ 18 years 11 days (eclipse cycle)
- Exeligmos: 3 Saros = 54 years (eclipse-triple cycle, aligns eclipses to same time of day)
- Olympic: 4 years (Panhellenic games)
- Lunar anomalistic period encoded in the pin-and-slot epicycle: ≈8.85 years (apsidal precession)

### `research/astronomical_cycles.py` — the "channel" layout

The mechanism's dial set is the analog of chess's 10-channel 640-dim encoding. Each dial is one channel:

| Dial | Cycle | Integer encoding | Prime factors |
|---|---|---|---|
| Front zodiac | 360° / year | 365 days ≈ 1 tropical year | — |
| Front calendar | Egyptian civil year | 365 | 5 · 73 |
| Metonic spiral | 235 synodic months / 19 years | 235 = 5 · 47 | 5, 47 |
| Callippic | 4 Metonic | 940 = 4 · 235 | 2², 5, 47 |
| Olympic | 4 years | 4 | 2² |
| Saros spiral | 223 synodic months | 223 (prime) | 223 |
| Exeligmos | 3 Saros | 669 = 3 · 223 | 3, 223 |
| Lunar anomaly | 8.85 years | fractional; epicyclic | — |
| Lunar nodes | 18.6 years (nodal regression) | — | — |
| Sun pointer | 1 year | 365 or year-fraction | — |
| Moon pointer | variable (elliptical) | — | — |
| Mercury pointer | synodic 116 days | — | — |
| Venus pointer | synodic 584 days; period relation (289, 462) | 462 = 2·3·7·11 | 2, 3, 7, 11 |
| Mars pointer | synodic 780 days | — | — |
| Jupiter pointer | synodic 399 days | — | — |
| Saturn pointer | synodic 378 days; period relation (427, 442) | 442 = 2·13·17 | 2, 13, 17 |

**Observe the shared-prime-factor structure**: 7 and 17 appear in multiple planetary trains per Freeth 2021, exactly the shared-generator pattern the addressing-maths plan names in A-H1.

### Sanity checks Phase 0 must pass

Put these in `research/consolidated_tests.py`:

1. **Tooth-count consistency.** For every gear pair, the ratio encodes a known cycle to within Greek-attainable precision (≤1/1000). E.g., Metonic: 19 years ↔ 235 lunar months is reproduced by the e-series train to machine precision.
2. **Prime-factor catalog.** All gear tooth counts factorize into known primes; list the prime spectrum the mechanism actually uses. This is the "alphabet" of the HDC encoding.
3. **Gear-topology graph.** Build the gear-composition DAG. Leaves are dial pointers; root is the crank. Each internal node carries its tooth count and the cycle it encodes.
4. **Astronomical cycle residuals.** For each cycle (Metonic, Saros, Callippic, …), compute the cycle length produced by the gear train and compare against the modern astronomical value. Report the error per cycle. Expected: <0.1% for the Greek-solved cycles, larger for Mars (the Greeks didn't have equants).

## Phase 1 — Hypothesis battery

Same format as Othello Phase 1: each hypothesis is a concrete computation with prediction, threshold, prior art, status. Emit `results/phase1_hypotheses.csv` and `results/phase1_detail.json`.

### A. Coprime addressing is the mechanism's native language

**A-H1: Every gear ratio is a best rational approximation under a tooth-count budget.** For each astronomical cycle, compute the best rational approximation p/q with max(p, q) ≤ some budget (say 500, reflecting the physical feasibility of cutting >500 teeth in bronze). Compare to the ratio the mechanism actually uses. **Prediction:** the mechanism's ratios are within the top-3 convergents of the continued-fraction expansion for every cycle. **Prior art:** Freeth 2021 supplementary material does this informally; we do it systematically. **Threshold:** ≥90% of cycles within top-3 convergents.

**A-H2: Shared prime factors across planetary trains are Pareto-optimal.** Freeth 2021 claims 7 and 17 are shared. Enumerate all prime factors ≤ 50 and compute, for each set of candidate shared factors, the total tooth budget required to achieve the stated per-planet precision. **Prediction:** the Freeth 2021 choice of shared primes is Pareto-optimal on the (precision, total-tooth-count) frontier. **Threshold:** no candidate factoring achieves lower total tooth count at equal or better precision. **Status:** NOVEL — this reframes the Freeth reconstruction as an optimization result.

**A-H3: The prime spectrum of the mechanism is non-random.** Compute the histogram of primes appearing in the gear tooth counts. Compare to a null model (random tooth counts drawn from [10, 300]). **Prediction:** the observed spectrum is heavily biased toward small primes (2, 3, 5, 7) plus a handful of large primes needed for specific irrationals (47, 53, 127, 223). **Prior art:** Freeth 2008 notes the 223-prime is "strange"; we contextualize it as the signature of a genuinely irrational cycle requiring a prime denominator.

### B. The mechanism as a group-algebra element

**B-H1: Every cycle is an element of ℂ[ℤ/D_Antℤ] for some D_Ant.** Compute D_Ant = lcm of all gear tooth counts (and their compositions). Each dial pointer corresponds to a specific residue class. **Prediction:** D_Ant is factorizable and of moderate size (expected: under 10¹⁰ but significantly structured). **Threshold:** compute D_Ant and its prime factorization explicitly.

**B-H2: Crank-turn = single generator of the phase-space.** One turn of the hand-crank advances the full system by one day. In the phase-space ℤ/D_Antℤ, this is a single generator σ_day. Every astronomical prediction is a power of σ_day projected onto a specific dial. **Prediction:** σ_day is a unit in ℤ/D_Antℤ (coprime to D_Ant). **Status:** likely CONFIRMED — follows from design.

**B-H3: The HDC binding operation = gear composition.** If piece A has hypervector h_A encoding its phase on ℤ/n_Aℤ, and piece B has h_B on ℤ/n_Bℤ, then meshing gear A with gear B at ratio n_A/n_B corresponds to the HDC bind h_A ⊗ R_{n_A/n_B}, where R is a roll/rotation operator. **Prediction:** the chess §9f coprime roll binding is exactly the Antikythera gear-meshing operation transposed to an abstract HDC space. **Novel:** this is the structural claim the project most wants to establish.

### C. Bounds, aliasing, and the Greeks' error-correction strategy (they had none)

**C-H1: The mechanism has zero intrinsic error correction.** Apply the addressing-maths §3D theorem: coprime addressing is a bijection; bijections add zero correction capacity. **Prediction:** any mis-counting of teeth or single-gear-slip propagates with no correction. **Implication:** the Greeks knew this — they compensated by using exact integer tooth counts with astronomical *precision at design time* rather than error-correction at runtime. The Guillermo & Szigety 2025 simulation result — that the mechanism may not have run smoothly — is a direct empirical demonstration of this theorem at the manufacturing level.

**C-H2: Aliasing horizon as the spiral-dial return-to-start.** The Metonic and Saros dials are **physical spirals** rather than circles because the cycles are longer than the visible spiral-arc length. The dial wraps after a full spiral traversal. This is the **physical instantiation of the §11.3.3 torus-clip**: when the pointer reaches the end of the spiral, it re-enters at the start, signaling a cycle boundary. **Prediction:** this is formally identical to the "phase-op shifts that carry an origin off the lattice land in the off-image complement" mechanism of chess §11. **Novel:** no one has framed the spiral dial as an aliasing-horizon detector before. **Status:** likely CONFIRMED by construction — the spiral is the physical mechanism for boundary detection.

### D. T-breaking and the pawn-analog

**D-H1: The pin-and-slot mechanism is the Antikythera's antisymmetric fiber.** In chess, the pawn's directed Laplacian breaks Z₂ time-symmetry (§9m, Hatano-Nelson t_L = 0). In Antikythera, the pin-and-slot epicycle *breaks time-symmetry of the lunar motion* — it approximates Kepler's second law, so the Moon moves faster at perigee and slower at apogee. The pin-and-slot is mechanical T-breaking: a component that does not commute with the time-reversal operator. **Prediction:** the ratio ||pin_and_slot_asymmetric|| / ||pin_and_slot_symmetric|| approaches 1.0 in the relevant decomposition, matching the chess pawn ratio ||A_anti|| / ||A_sym|| = 1.0. **Status:** NOVEL — the pawn/pin-and-slot correspondence has not been drawn in the literature.

**D-H2: All other gear trains are T-symmetric.** Running the mechanism backward (turning the crank the other way) gives valid astronomical predictions for past dates, except where the pin-and-slot is involved. **Prediction:** the Sun dial, the Metonic, the Saros, and the outer planets (Jupiter, Saturn) all run cleanly in reverse. The Moon dial and (to a lesser extent) the inner planets (Mercury, Venus) carry T-breaking in their epicyclic approximations.

### E. Ground-truth validation

**E-H1: The encoder reproduces ancient eclipse predictions.** Pick a known Hellenistic-era eclipse (e.g., the 120 BCE lunar eclipse). Run the encoded mechanism forward from a known reference date. Compare the Saros dial output against NASA historical ephemeris. **Prediction:** within ~1 day for the Greek-solved cycles, within ~1 month for Mars. **Threshold:** Saros match to ±1 day across any 20 eclipses in 200 BCE – 100 CE.

**E-H2: Planetary-position errors match the documented Greek-astronomy limits.** The Mars pointer is up to 38° wrong at retrograde nodes (Wikipedia; Freeth 2021) because Greek astronomy lacked equants. Reproduce this error exactly: our encoder should be wrong *in the same way* the mechanism was wrong. **Prediction:** the encoder's error at Mars-retrograde is within a few degrees of the mechanism's. **Status:** this is a fidelity test, not a correctness test — we want to match the historical device, not modern astronomy.

### F. Open exploration

**F-E1: Does the mechanism's prime spectrum match any modern VSA/HDC encoding?** Compare to Residue-HDC (Kymn et al. 2025), which explicitly uses CRT moduli. **Prediction:** the Antikythera is a 1st-century-BCE Residue-HDC instance with moduli chosen from astronomy rather than number theory.

**F-E2: Is there a natural `D_Ant` at which every cycle the mechanism supports becomes a single integer?** If yes, this is the mechanism's "640-dim" — the natural ambient modulus for an encode_Ant function.

**F-E3: What are the "failed" cycles?** Cycles the mechanism attempted to approximate but got wrong. Mars is the canonical example. **Open:** are these failures attributable to specific approximation-precision tradeoffs the Greeks made, or to genuine limits of their astronomical theory?

## Phase 2 — `encode_Ant`: the resonant HDC encoder

Build `research/encode_ant.py` to produce a hypervector for any date (or ℝ-valued "time" variable) that encodes the full mechanism state.

### Architecture

The encoding has one channel per dial, matching the mechanism's physical structure. Dimension is determined by the largest gear tooth count (or its lcm composition, depending on H2/H3 outcomes). Candidate dimensions:

- **D = 940** (Callippic cycle × 4 for safety) — encodes annual + multi-year cycles cleanly but may not fit planets.
- **D = lcm(all cycles)** — exact and natural, but possibly huge.
- **D = chess-style ambient (e.g. 2⁷ × 3 × 5 × 7 = 13440)** — engineered for packing. Probably best for HDC operations.

Commit to one primary and one ablation, like Othello's D=768 + rank-8 ablation.

### Fiber structure

The Antikythera's "fiber" is the shared gear-train structure (H-A2). Unlike chess's piece Laplacians (static) or Othello's ray Laplacians (dynamic with flanking), the Antikythera fiber is **static but shared across species**. Each celestial body has its own dial (species), but the internal gearing draws from a shared pool of generators (7, 17, and a few others). This is the cleanest "fiber bundle" in the project so far — completely static, empirically verified by Freeth 2021.

### Unbinding

The Phase 2 deliverable must include `research/dial_decoder.py`: given a full-mechanism hypervector, recover which dial is pointing where. This is the chess-style unbinding test. Given the hypervector is constructed from shared generators, unbinding across multiple planetary dials should work cleanly (if the Greeks got the packing right — which A-H2 tests).

## Phase 3 — Phase-operator preflight

Minimal. The Antikythera's phase operator is **trivial**: it's the single σ_day = crank-turn operator. All predictions are powers of σ_day projected onto specific dials. There are no distinct "pieces" with different movement rules; there is one universal operator (time advance) and many projections.

This is a feature, not a bug. The Antikythera is the **simplest possible phase-operator system** in the project's triad-plus:
- Chess: 6 piece types × 8 D₄ orbits = rich operator set
- Othello: 1 piece type × 8 ray directions × dynamic gating = rich but different
- Logo: command set + grammar = structured but different again
- Antikythera: **1 operator, multiple projections** = minimal

Write `OTHELLO_PHASE_OP_PREFLIGHT.md` equivalent as `ANTIKYTHERA_PHASE_OP_PREFLIGHT.md`. Short. Argue that the phase-operator build for this domain is ~20 lines of code: `advance_day(state) = state ⊗ σ_day`.

## Phase 4 — Historical validation (WTHOR equivalent)

The Antikythera's WTHOR is the **NASA JPL Horizons ephemeris**, computed backward to the Hellenistic era. Horizons is free and covers 15 BCE – present; several historical eclipse catalogs extend it further back.

Tests:
1. Compare encoder-produced Sun positions to Horizons' Sun positions over 100 BCE – 100 CE.
2. Compare encoder-produced Moon positions to Horizons' Moon positions over the same range.
3. Compare encoder-produced eclipse times to known Hellenistic eclipse records (Ptolemy's *Almagest* lists several).
4. Reproduce the Mars-retrograde error pattern.

Ground-truth availability is much better for this domain than for chess or Othello. The research-budget question is just whether to run modern astronomy against Phase 2 encoder, or whether to stop at validating against Freeth 2021's own astronomical validation (which already exists).

Recommendation: do it. NASA Horizons has a Python API (`astroquery.jplhorizons`); the marginal cost is low.

## Research notebook scaffold

Create `docs/antikythera-maths/antikythera_spectral_research_notebook.md` with this skeleton. Fill in §1, §2, §3 from Phase 0–4 as they complete.

```
# The Antikythera Mechanism as a Resonant HDC Object

**Authors:** Steven (mlehaptics Project) & Claude (Anthropic)
**Date:** April 2026
**Status:** Active research — reconstructive/descriptive project; the Greeks did the math, we're reading it off.

> Living document. Sibling to:
> - [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md) — the template this notebook mirrors.
> - [../othello-maths/othello_spectral_research_notebook.md](../othello-maths/othello_spectral_research_notebook.md) — the second-instance template, Phase 1 battery format.
> - [../logo-maths/logo_research_notebook.md](../logo-maths/logo_research_notebook.md) — the non-board generalization.
> - [../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md](../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md) — the formal substrate. Every result in this notebook should be readable as "the Greeks instantiated X of the addressing-maths framework in configuration Y."

Every claim is tagged **KNOWN / NOVEL / CONFIRMED / FAILED / DISPUTED** (see Framing for DISPUTED tag definition specific to this domain).

---

## 0. Framing

The Antikythera mechanism is coprime-indexed phase-space addressing executed in bronze, designed 2100 years ago. This notebook documents it as such. The math is already in the artifact; our job is to name it in the vocabulary the addressing-maths thread has now assembled. This is the first mlehaptics project where the encoding is *descriptive*, not *prescriptive* — we are not inventing an encoder, we are recognizing one.

## 1. Infrastructure (Phase 0)

### 1.1 The artifact
Brief physical description. Size, date, recovery, fragment count. Reference to Freeth 2021 as the canonical reconstruction.

### 1.2 The gear database
Hard-coded tooth counts with provenance. Freeth 2021 as primary, Wright where it differs, de Solla Price for historical context.

### 1.3 The astronomical cycle layout
Metonic, Saros, Callippic, Exeligmos, Olympic, lunar anomaly, lunar nodes, 7 planets. Each as a row in a table with integer encoding and prime factorization.

### 1.4 Sanity checks
Tooth-count consistency; prime spectrum; gear-topology graph; per-cycle astronomical residuals.

## 2. Phase 1 battery

§2.A, §2.B, §2.C, §2.D, §2.E, §2.F matching Phase 1 above. Each subsection: prediction, experiment, measured numbers, status tag, interpretation, lesson.

## 3. `encode_Ant` — the resonant encoder (Phase 2)

Architecture decision log: which D, which fiber structure, which unbinding test suite passes.

## 4. Phase-operator preflight (Phase 3)

Short. `advance_day` is the entire operator set for this domain.

## 5. Validation against NASA Horizons (Phase 4)

Eclipse comparison, planetary-position comparison, Mars-retrograde error reproduction.

## 6. The Archimedes question

Cicero, in *De re publica* and *Tusculan Disputations*, describes a planetarium built by Archimedes (captured by Marcellus at Syracuse, 212 BCE). The device he describes matches the Antikythera functionally. **Open:** is the Antikythera a descendant of an Archimedean design tradition? If yes, the mechanism we have is ~150 years of iterative design away from its progenitor, and the coprime-factoring choices may have been refined over generations by an unbroken tradition of craftsmen. The HDC encoding we extract is thus a **distilled** design, not a single inventor's flash of insight. This framing is DISPUTED in the literature; Freeth (2021) leans toward Archimedean origin, others argue for Rhodian astronomical schools.

## 7. Vocabulary collisions specific to Antikythera

- "Mechanism" (the device) vs "mechanism" (the causal process).
- "Gear" (physical wheel) vs "gear" (HDC generator — we use "generator" or "channel" where possible).
- "Cycle" (astronomical period) vs "cycle" (graph-theoretic closed walk) — we commit to the astronomical usage in this notebook.
- "Fiber" — adopted from chess §7 with the refinement that here the fiber is static *and* shared across species, unlike Othello's dynamic fiber.
- "Phase" — adopted from chess/addressing-maths. In this notebook "phase" means angular position on a dial (equivalently: residue class in ℤ/n_dialℤ).

## 8. Appendix: Environment and reproducibility

Python 3.12, NumPy, SciPy, `astroquery.jplhorizons` for Phase 4. All seeds explicit. All gear tooth counts hard-coded with provenance notes.
```

---

## Reporting discipline (same as Othello)

At end of session:
1. `results/phase1_hypotheses.csv` — structured per-hypothesis status table.
2. `results/phase1_detail.json` — per-hypothesis numeric detail.
3. `results/session_summary.md` — ~1 page narrative.
4. Notebook sections §1–§3 filled in.
5. `ANTIKYTHERA_PHASE_OP_PREFLIGHT.md` — short handoff.

## Common pitfalls anticipated

1. **Tooth-count disputes.** Freeth 2021 vs Wright vs Price disagree on specific counts. Document all three where they differ; run the hypothesis battery primarily against Freeth 2021 as the most recent authoritative reconstruction; note sensitivity to the disputed counts.

2. **Don't overstate the HDC framing.** The Greeks did not think of this as HDC. They thought of it as gear ratios chosen to approximate astronomical cycles. The HDC recognition is *our* framing. Keep the language clean: "the gear ratios, when expressed in modern vocabulary, constitute an HDC encoding" — not "the Greeks built an HDC encoder."

3. **The 2025 manufacturing-tolerance result is real.** Guillermo & Szigety's arXiv finding that the mechanism may not have run smoothly matters methodologically. It's the domain's equivalent of the chess §9a character-table bug: the *design* was clean, the *implementation* was tolerance-limited. Don't treat design cleanness as implementation success.

4. **Mars is intentionally wrong.** The Greeks didn't have equants. The mechanism is doing the best it could with epicycles-on-deferents, which is why Mars is up to 38° off at retrograde nodes. This is not a "bug" — it's the ceiling of Greek astronomical theory, faithfully encoded. Our encoder should *reproduce* the error, not correct it.

5. **The Archimedes attribution is DISPUTED.** Tag it DISPUTED and move on. Don't overclaim, don't dismiss.

6. **NASA Horizons before 15 BCE.** The API doesn't cover pre-15 BCE cleanly. Use historical eclipse catalogs (e.g., NASA's own pre-computed eclipse catalog, which extends to 2000 BCE) for validation of the Hellenistic-era test cases. `skyfield` with JPL DE441 is the standard Python tool.

7. **Integer vs modular arithmetic.** Every gear ratio is a rational number p/q. The cyclic-group structure comes from *taking the ratio mod 1* (i.e., keeping only the fractional part). Be explicit: the HDC encoding lives in ℝ/ℤ (or ℤ/Dℤ after discretization), not ℤ itself.

## How this fits the Rosetta Stone

| Project | Structure type | Encoding type | Phase operator complexity |
|---|---|---|---|
| chess-maths | discovered | prescriptive | rich (6 piece types × 8 orbits) |
| othello-maths | discovered | prescriptive | rich but different (1 piece, 8 rays, dynamic) |
| logo-maths | discovered | prescriptive | command set + grammar |
| addressing-maths | formalized foundation | — | — (the substrate itself) |
| **antikythera-maths** | **recognized/documented** | **descriptive** | **trivial (1 operator, many projections)** |

Antikythera is the first project where:
- The structure was deliberately designed into the artifact.
- The encoding is recognized, not invented.
- The phase operator is minimal.
- Ground truth is external (actual astronomy) rather than internal (game rules).

These four simplifications make Antikythera the **best pedagogical entry point** for the framework. A reader coming to mlehaptics fresh may find Antikythera easier to enter than chess because every claim has an external grounding — one can check "is this really how the 127-tooth gear works?" against the physical mechanism, rather than against our construction of piece Laplacians.

**Consequence for the framework narrative.** When the addressing-maths paper is eventually written, the Antikythera example is probably the best motivating vignette — it gives a concrete, visual, historically documented instance of every concept the paper introduces. Consider writing the mlehaptics framework paper with Antikythera as §1 introduction, addressing-maths as §2 formal substrate, and chess/Othello/logo as §3 empirical case studies.

## What this prompt is not

- Not a claim that the Greeks "invented HDC." They invented a specific geared astronomical calculator. The HDC recognition is our framing, valid as a description but not as an anachronistic attribution.
- Not a commitment to reconstructing the mechanism in hardware. The deliverable is computational/descriptive.
- Not a commitment to one reconstruction as ground truth. Where Freeth 2021, Wright, and Price disagree, all three are documented and the sensitivity is reported.
- Not a replacement for the excellent archaeology literature on the mechanism. We cite and build on it; we do not supplant it.
- Not a commitment to the Archimedes attribution. DISPUTED tag, stays DISPUTED.

## Definition of done

- `docs/antikythera-maths/` exists with the file layout above.
- Gear database, astronomical cycle database, and cyclic-group algebra utilities pass sanity checks.
- Phase 1 battery run (A-H1 through E-H2 + F-E1–F-E3) with numbers.
- Phase 2 `encode_Ant` produces hypervectors that reproduce the mechanism's astronomical predictions to within Greek-attainable precision.
- Phase 3 preflight is short and argues for the trivial phase operator.
- Phase 4 validation against NASA Horizons (or `skyfield`) completes on a test set of 20+ eclipses in 200 BCE – 100 CE.
- Research notebook §1–§3 prose + numbers matching the CSV.
- Session summary ~1 page.
- `ANTIKYTHERA_PHASE_OP_PREFLIGHT.md` drafted.

Extra credit! All protoplanet named celestial bodies in our solar system:
- Reproduce the Mars retrograde error to within a few degrees of the mechanism's documented 38° error.
- Cross-check the Freeth 2021 shared-prime-factor claim (7, 17) is Pareto-optimal per A-H2.
- Identify whether any ancient astronomical table (Babylonian MUL.APIN, Ptolemy's *Almagest* tables) shows evidence of the same prime-factorization choices the mechanism makes.
- How many more gears? Find out first if it's practically feasible to build a physical Antikythera with the tooth counts we document. If not, how many more gears would be needed to achieve the same astronomical precision?
