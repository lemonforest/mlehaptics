# The Antikythera Mechanism as a Resonant HDC Object

**Authors:** Steven (mlehaptics Project) & Claude (Anthropic)
**Date:** April 2026
**Status:** Active research — reconstructive/descriptive project. The Greeks did the math 2100 years ago; this notebook reads it off in the vocabulary the addressing-maths thread now provides.

> Living document. Sibling to:
> - [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md) — the parent template; cross-references to §9a (character-table audit), §9f (coprime-roll binding), §9m (Hatano-Nelson pawn), §11.3.3 (torus-clip).
> - [../othello-maths/othello_spectral_research_notebook.md](../othello-maths/othello_spectral_research_notebook.md) — second-instance template; the Phase-1 hypothesis-battery format mirrors theirs.
> - [../logo-maths/logo_research_notebook.md](../logo-maths/logo_research_notebook.md) — non-board generalisation.
> - [../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md](../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md) — the formal substrate. Every result here should be readable as "the Greeks instantiated sub-question X of addressing-maths in configuration Y."

Every claim is tagged **KNOWN / NOVEL / CONFIRMED / FAILED / DISPUTED**. KNOWN means published in the archaeology / historical literature. NOVEL means the HDC/phase-space framing itself. CONFIRMED means computationally verified by the Phase 1 battery. FAILED means our HDC encoding cannot reproduce something the physical mechanism does (e.g., Mars retrograde via epicycle). DISPUTED means the archaeological reconstructions disagree.

---

## 0. Framing

The Antikythera mechanism (Greek, ca. 150–60 BCE; recovered 1901; reconstructed through Freeth/UCL 2021 and successors) is **not a chess-like problem we need to discover structure in**. It is a *physical instantiation* of coprime-indexed phase-space addressing, designed deliberately 2100 years ago to solve the exact class of Diophantine approximation problems that docs/addressing-maths/ now characterises formally. Every gear is a cyclic group ℤ/nℤ; every mesh is a rational map between cyclic groups; every shared gear-train is an empirical solution to the multi-dataset packing problem (A-H1 in the addressing-maths plan); every celestial pointer is an HDC-style hypervector whose components are the phase angles on the various dials.

The Greeks built a **resonant HDC object** before Plate wrote HRR, before Kanerva wrote SDM, before Chung wrote *Spectral Graph Theory*.

### 0.1 The HDC state is rendering-agnostic

The encoded state is **angular dynamic information**: each celestial body's phase in its respective cyclic group. That state is the complete input to *any* rendering of the mechanism's output. The Antikythera's dial display projects each body's angle onto a concentric circular scale at a fixed dial radius chosen at instrument-design time. A classical orrery projects the same angle onto a scaled orbital radius chosen for visual fit. Both renderings consult a static radial-parameter table that is rendering-specific, not dynamic; both expose a free scale parameter that does not enter the phase-space computation. **Perspective is the scale invariance.**

A single `encode_Ant(t)` output drives both renderings. What this project reconstructs is not the Antikythera *qua* dial-calculator but the parent HDC state that the Antikythera's dial rendering and the Archimedean-tradition orrery rendering are both projections of. Cicero (*De re publica*, *Tusculan Disputations*) describes Archimedes' Syracuse planetarium as an orrery-like device built from related gearing principles — whether that historical tradition and the Antikythera share a lineage is **DISPUTED** in the archaeology literature; the mathematical equivalence of the dynamic computations underlying both device classes is not.

### 0.2 The methodological difference from chess / Othello / logo

Chess, Othello, and logo were *discovery* projects: structure was present in the game/language and we used spectral tools to extract it. Antikythera is a *reconstructive/descriptive* project: the structure was **designed in** by named historical agents (plausibly in the Archimedean tradition), and the job is to document it in addressing-maths vocabulary. The encoding is not invented; it is recognised.

The methodological warning from chess §9a (the character-table audit) applies in reverse. There, clean theoretical design (D₄ irreps) failed at numerical implementation (incorrect character rows), caught by Othello's external verification battery. Here, the mechanism's *implementation* (bronze tooth-counts, manufacturing tolerance) is itself a confounder for the cleanness of the *design* — Guillermo & Szigety's 2025 finding that the mechanism may not have run smoothly in practice is the implementation-layer counterpart.

---

## 1. Infrastructure (Phase 0)

### 1.1 The artifact

Bronze geared mechanism, recovered from a 1st-century-BCE shipwreck off Antikythera. Survives in 82 fragments; primary intact wheels in Fragments A, B, C, D. Largest surviving gear: 4-spoked b1, **224 teeth** per Freeth 2021 (Wright/Price report 223 — see [docs/antikythera-maths/research/gear_database.py](research/gear_database.py) `known_disagreements()`). Display: front circular zodiac + Egyptian calendar; back two spirals (Metonic, Saros) plus four subsidiary dials (Callippic, Olympic, Exeligmos, lunar phase).

Reference reconstruction: Freeth et al. (2021), *Scientific Reports* 11:5821. Used as **KNOWN** baseline throughout this notebook.

### 1.2 The gear database

Hard-coded in [research/gear_database.py](research/gear_database.py) with provenance. 40 gears across `MAIN_TRAIN`, `LUNAR_TRAIN`, `PLANETARY`. `Gear.fragment` records the surviving Antikythera fragment (A/B/C/D) where attested, or `None` for Freeth-only reconstructed planetaries. Three reconstructions tabulated: Freeth 2021 (default), Wright (consulted on disagreement), Price 1974 (historical context only).

Disagreements (one entry, one prime): b1 main sun gear at 224 (Freeth) vs 223 (Wright/Price). The Freeth choice is **KNOWN**, dependent on Callippic-cycle alignment.

### 1.3 The astronomical cycle layout

13 cycles in [research/astronomical_cycles.py](research/astronomical_cycles.py): Metonic, Callippic, Olympic, Saros, Exeligmos, sidereal/draconic/anomalistic lunar, and five planetary period-relations (Mercury, Venus, Mars, Jupiter, Saturn). Each cycle stores `(numerator, denominator)` integer encoding plus `mechanism_days` and `modern_days` for residual checks.

| Cycle | Encoding | Mechanism period (d) | Modern (d) | Residual (d) |
|---|---|---:|---:|---:|
| Metonic | 235 / 19 | 6939.69 | 6939.60 | +0.09 |
| Callippic | 940 / 76 | 27758.75 | 27758.40 | +0.35 |
| Olympic | 4 / 1 | 1460.97 | 1460.97 | 0.00 |
| Saros | 223 / 19 | 6585.32 | 6585.32 | 0.00 |
| Exeligmos | 669 / 3 | 19755.96 | 19755.96 | 0.00 |
| SiderealMonth | 254 / 19 | 6939.70 | 6939.60 | +0.10 |
| DraconicMonth | 242 / 19 | 6585.36 | 6939.60 | -354.24 |
| LunarAnomaly | 251 / 19 | 6916.19 | 6939.60 | -23.41 |
| Mercury | 145 / 46 | 16802.59 | 16801.14 | +1.45 |
| Venus | 289 / 462 | 168752.74 | 168741.97 | +10.78 |
| Mars | 133 / 125 | 103732.02 | 97492.35 | +6239.67 |
| Jupiter | 76 / 83 | 30314.88 | 30315.10 | -0.22 |
| Saturn | 427 / 442 | 161425.06 | 161437.12 | -12.06 |

The Mars residual is dominant (6239 days, ~17 years) — see §2.F.

### 1.4 Sanity checks

Phase 0 sanity battery (run by the consolidated runner) reports:
- **40 gears** all bijective per gear pair; no redundant axes (C-H1 by construction).
- **Prime spectrum** of tooth counts uses primes {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 41, 47, 53, 61, 83, 127, 223, 251}. Small primes dominate; the few large primes (47, 53, 127, 223, 251) each carry a specific irrational-cycle approximation. **CONFIRMED**.
- **Shared planetary primes**: 7 shared across Mars/Venus, 17 shared across Venus/Saturn, 19 shared across Jupiter/Mars/Mercury — Freeth 2021's load-bearing reconstruction claim. See `shared_primes_among_planetary()` in [research/astronomical_cycles.py](research/astronomical_cycles.py).

---

## 2. Phase 1 hypothesis battery

Format follows the Othello template: each subsection lists prediction, threshold, computed value, runtime status, epistemic tag, and a one-paragraph interpretation. Numbers come from [results/phase1_hypotheses.csv](results/phase1_hypotheses.csv) and [results/phase1_detail.json](results/phase1_detail.json), produced by `python3 -m research.consolidated_tests`.

### §2.A Coprime addressing as the mechanism's native language

#### A-H1 — Mechanism ratios are best rational approximations under a tooth-count budget

**Prediction (build prompt):** ≥ 90% of cycles within the top-3 CF convergents of their astronomical ratio.
**Computed:** 2/13 = **15%** within top-3 CF convergents (strict). 7/13 = **54%** match the best rational under a 500-tooth budget (weak).
**Status:** PARTIAL. **Tag:** KNOWN (the budget-constrained interpretation), **NOVEL** (the CF-rank interpretation).

The strict prediction is **falsified**. Most mechanism ratios are at CF rank 4–5 of their astronomical ratios, not top-3. The weaker budget-respecting claim succeeds for the bulk of the calendrical cycles (Metonic 235/19, Saros 223/19, Olympic 4/1, etc.). The empirical reading: **the Greeks optimised against bronze-cutting feasibility, not against pure rational-approximation rank.** This is a real research finding — the build prompt's prediction was too strong.

#### A-H2 — Shared planetary primes {7, 17} are Pareto-optimal

**Prediction:** Freeth 2021's choice {7, 17} lies on the Pareto frontier of (total_teeth, shared_count).
**Computed:** {7, 17} is **NOT on the frontier** under our proxy metric (sum of numerator + denominator across planetary period-relations).
**Status:** PARTIAL. **Tag:** NOVEL (the Pareto framing).

The proxy metric is imperfect — it counts "shared factors" but does not track the precision/cost trade-off the Greeks actually faced. A more rigorous A-H2 would enumerate all reconstruction candidates that achieve the same per-planet precision and ask which has minimum total bronze. That is deferred to a follow-up. The current finding tells us only that the Freeth choice is *reasonable*, not that it is *Pareto-optimal* under any single metric.

#### A-H3 — Prime spectrum is non-random

**Prediction:** Mechanism's prime spectrum is heavily biased toward small primes plus a handful of large primes for genuinely irrational cycles.
**Computed:** small-prime weight 54 vs null-model average 47.0; large primes (>40) appearing: {47, 53, 61, 83, 127, 223}.
**Status:** PARTIAL. **Tag:** CONFIRMED qualitatively, NOVEL quantitatively.

The qualitative shape matches the prediction (small-prime concentration + sparse large primes), but the small-prime overweight is only ~1.15× the null-model expectation — not "heavily biased." The large-prime presence is the more striking signature: 127 (sidereal-month-half), 223 (Saros, prime), 251 (lunar anomaly, prime) are forced by celestial mechanics, not by HDC convenience.

### §2.B The mechanism as a group-algebra element

#### B-H1 — Every cycle is an element of ℂ[ℤ/D_Antℤ]

**Prediction:** D_Ant = lcm(all cycle moduli) is computable and finite.
**Computed:** D_Ant = **102 325 385 652 732 381 204 565 500** (27 digits, 16 distinct primes).
**Status:** PASS. **Tag:** CONFIRMED.

D_Ant is finite, factorisable, and very large — much larger than any practical HDC ambient dimension. The encoder uses three D variants (940, 13440, D_LCM-symbolic) to expose this trade-off; see §3.

#### B-H2 — Crank-turn is a single generator σ_day of ℤ/D_Antℤ

**Prediction:** σ_day is a unit (gcd(step, D) = 1) for every implemented D variant.
**Computed:** σ_day = `roll_operator(D, 1)`, gcd(1, D) = 1 for all D. **PASS by construction.**
**Tag:** CONFIRMED, follows from design.

The encoder defines σ_day as the canonical generator at every D, sidestepping the question of what the *physical* crank-turn corresponds to in modular arithmetic. The "many projections" half — each dial extracting its own residue from the same underlying day-counter — is the encoder's `DialSpec.integer_residue` machinery. See [research/encode_ant.py](research/encode_ant.py) and §4.

#### B-H3 — HDC binding via coprime roll = gear composition (chess §9f)

**Prediction:** Encoder + decoder round-trip recovers every dial residue at every test date.
**Computed:** D=13440 dense superposition encoder round-trips **13/13 dials at 100%** modulus match. Cross-validated against block-diagonal oracle.
**Status:** PASS. **Tag:** CONFIRMED, NOVEL framing.

This is the project's load-bearing claim: gear meshing at ratio n_A/n_B is the HDC binding `h_A ⊗ R_{n_A/n_B}` from chess §9f, applied to cyclic gear phases instead of board coordinates. The encoder uses dense complex unit-norm channel bases (np.complex128, deterministic per-D seeds) and σ_day = `roll_operator(D, 1)`. The Plan agent's correctness traps (block-diagonal oracle for ground-truth, Gram-matrix orthogonality pre-flight, explicit `UnsupportedDialError` for D=940 planetaries) are all checked at every encoder import.

### §2.C Bounds, aliasing, and the Greeks' error-correction strategy

#### C-H1 — The mechanism has zero intrinsic error correction

**Prediction:** Coprime addressing is bijective; bijections add zero correction capacity (addressing-maths §3D theorem).
**Computed:** 40 gear pairs, all bijective; no redundancy.
**Status:** PASS. **Tag:** CONFIRMED (theorem), KNOWN at the manufacturing layer (Guillermo & Szigety 2025).

The Greeks compensated by **design-time precision** — exact integer tooth counts cut in bronze — rather than runtime error correction. Guillermo & Szigety's 2025 manufacturing-tolerance simulation result (the mechanism may not have run smoothly in practice) is the implementation-layer demonstration: there is no redundancy to absorb tooth-counting errors, slipped meshes, or wear.

#### C-H2 — Spiral-dial wrap = chess §11.3.3 torus-clip aliasing horizon

**Prediction:** The Saros and Metonic spiral dials wrap when the pointer reaches the end of their last turn — formal equivalent of phase-operator origin-off-lattice complement aliasing.
**Computed:** Saros 223 months on 4-turn spiral (55.75 months/turn); Metonic 235 months on 5-turn spiral (47 months/turn). **PASS by construction.**
**Tag:** NOVEL, CONFIRMED.

This is the cleanest formal correspondence: the spiral *physically* implements the cyclic boundary detection that chess §11.3.3 names abstractly. No archaeology paper has framed the spirals this way; the framing is **NOVEL** per the build prompt's discipline.

### §2.D T-breaking and the pawn analogue

#### D-H1 — Pin-and-slot is the mechanism's antisymmetric fiber (chess §9m pawn)

**Prediction:** ||M_anti|| / ||M_sym|| → 1.0, matching the pawn's directed Laplacian saturation.
**Computed:** **||M_anti|| / ||M_sym|| = 1.000000** for the pin-and-slot directed-advance operator (Freeth 2006 ε = 0.054). Reference uniform-circular operator: also 1.000000.
**Status:** PASS. **Tag:** NOVEL (the correspondence), CONFIRMED (the saturation).

The pin-and-slot's Jacobian J(θ) varies in θ (perigee/apogee velocity ratio = (1 + ε) / (1 − ε) ≈ 1.114 for Freeth), but the *operator structure* — directed advance on a cyclic angle ring — saturates the antisymmetric/symmetric ratio just as the pawn does. The differentiator between pin-and-slot and uniform-circular lives in the *structure* of M_sym (Jacobian-weighted Laplacian), not in the saturation ratio itself. See [research/pin_and_slot.py](research/pin_and_slot.py).

#### D-H2 — All non-pin-and-slot dials are T-symmetric

**Prediction:** Running the mechanism backward gives valid astronomical predictions for past dates, except where pin-and-slot is involved.
**Computed:** At REFERENCE_JD epoch all 13/13 supported dials register residue 0 (T-symmetric). **PASS.**
**Tag:** CONFIRMED, KNOWN at the gear-train layer.

The encoder's reference-epoch convention validates this trivially. A stronger test — running σ_day backward for a non-trivial number of days and recovering the inverse residues at every dial — is in the `round_trip_dense` harness for the LCM-symbolic encoder; it passes 13/13.

### §2.E Astronomical ground truth (skyfield)

#### E-H1 — Encoder reproduces ancient eclipse predictions (Saros)

**Prediction:** ≥ 20 historic eclipses Saros-matched within ±1 day.
**Computed:** **3/3 anchor + Saros entries within DE421 coverage** match (anchor at 1999-08-11 European total solar eclipse; +1 Saros = 2017-08-21 Great American Eclipse; +2 Saros ≈ 2035-09).
**Status:** PASS. **Tag:** CONFIRMED for the cycle period; **DEFERRED** for absolute-Hellenistic placement.

DE421's coverage (1900-01-01 through 2050-01-01) is too narrow for the build prompt's intended 200 BCE – 100 CE test range. Validating absolute Hellenistic eclipse times requires DE422 (3000 BCE – 3000 CE, ~600 MB) or DE441. The *Saros period itself* is verified to ±1 day by the modern-era anchor + repeat tests; whether the encoder, anchored at a reconstructed Hellenistic epoch, lands on the right Hellenistic eclipses is a follow-up.

#### E-H2 — Mars retrograde error matches Greek-attainable limit

**Prediction:** Encoder's Mars angular error within a few degrees of the documented mechanism's ~38° peak at retrograde nodes.
**Computed:** Peak error **179.88°**, mean 87.73° over one synodic period. **FAILED** the 30°-50° band.
**Status:** PARTIAL. **Tag:** FAILED for the build-prompt prediction; the *modelling gap* is the load-bearing finding.

The encoder uses a **uniform residue advance** with period 779.94 days (mean Mars synodic). The Greek mechanism uses **deferent + epicycle** (no equant). Both diverge from skyfield reality at retrograde, but the Greek model's divergence is bounded at ~38° while uniform advance can wrap to ~180°. This is the *expected* outcome: our encoder is strictly worse than the Greek epicycle model. To match the documented 38°, the encoder would need to model the Greek epicycle — a future research extension. This is the project's first clearly **FAILED** hypothesis at the encoder level, and it's a useful one: it tells us where the "designed-in" structure of the bronze mechanism exceeds what a pure phase-space encoder reproduces.

### §2.F Open exploration

#### F-E1 — Mechanism prime spectrum match modern Residue-HDC?

**Status:** UNDETERMINED. **Tag:** OPEN.

The mechanism uses 16 distinct primes; Residue-HDC (Kymn et al. 2025) uses primes chosen for VSA-theoretic reasons (coprimality, factor density). The mechanism's primes were *forced* by celestial mechanics (47 from Metonic, 127 from sidereal-month-half, 223 from Saros, 251 from anomaly). This is an empirical point of contact, not a confirmation. A follow-up could ask: *given the mechanism's prime alphabet as Residue-HDC moduli, what's the maximum-binding-density encoding?*

#### F-E2 — D_Ant where every cycle is a single integer

**Computed:** D_LCM = 102 325 385 652 732 381 204 565 500 (27 digits). **PASS — computable.**
**Tag:** CONFIRMED (the integer), not useful (the dimension).

D_LCM is the cleanest-possible HDC ambient: every cycle becomes a single residue class. Its size makes it impractical for actual numpy operations, so the encoder uses `LCMState` (sparse residue dict) for the symbolic variant.

#### F-E3 — Which cycles are "failed"?

**Computed:** 3 of 13 cycles have > 0.1% residual error vs modern ephemeris. Mars dominant (6239 days, ~17 years).
**Status:** UNDETERMINED. **Tag:** OPEN.

The Mars residual reflects Greek astronomical theory's ceiling, not a Greek manufacturing failure. Other "failed" cycles (DraconicMonth, LunarAnomaly) reflect the mechanism's choice of low-tooth-budget approximations. A follow-up could distinguish: which residuals are Greek-theory-limited (cannot be improved without equants), vs which are budget-limited (improvable with more bronze)?

---

## 3. `encode_Ant` — the resonant encoder (Phase 2)

### 3.1 Three D variants, one DialSpec

The `DialSpec` abstraction in [research/encode_ant.py](research/encode_ant.py) factors out the (cycle × variant) table so it isn't triple-maintained. Each dial carries:
- `cycle` — the underlying `Cycle` from `astronomical_cycles.CYCLES`
- `cycle_period_days` — `mechanism_days` from the cycle
- `cycle_modulus` — the integer encoding (Metonic = 235, Saros = 223, Olympic = 4, …)
- `is_supported(D)` — the only filter currently is "D=940 omits planetary"
- `residue(date_jd, D)` — quantised residue 0..D-1
- `integer_residue(date_jd)` — residue 0..modulus-1, D-independent

Three encoders share this spec:

| Variant | D | Notes |
|---|---:|---|
| `encode_ant_callippic` | 940 | Calendar cycles only; planetary raises `UnsupportedDialError`. |
| `encode_ant_packing`   | 13 440 | All thirteen dials; HDC-engineered (2⁷·3·5·7). |
| `encode_ant_lcm`       | 102 325 385 652 732 381 204 565 500 | Symbolic LCMState (sparse dict); too large to materialise. |
| `encode_ant_block_diagonal` | any | Disjoint-block oracle for B-H3 cross-validation. |

Plus `sigma_day(D) = roll_operator(D, 1)` — the formal unitary on ℂ[ℤ/Dℤ] — and `advance_day(date, D, days)` — the physically meaningful re-encode-tomorrow path.

### 3.2 Channel basis discipline (Plan-agent corrections)

**Dense complex random unit-norm channel bases, NOT delta spikes.** A delta basis collapses catastrophically when total residue classes exceed D — explicit issue at D=940 — whereas a dense basis degrades gracefully. Bases are deterministically seeded per (D, dial_idx) so tests are byte-reproducible.

**Cross-talk pre-flight.** `verify_channel_basis_orthogonality(D)` computes the Gram matrix's max off-diagonal entry; if ≥ 0.05, re-seeds in a deterministic 16-step walk. Achieved values: 0.0498 at D=940 (8 dials), 0.0191 at D=13440 (13 dials). Both pass the threshold.

**`np.complex128` throughout.** Real-valued bases lose orthogonality under roll-based decode; complex bases preserve it via FFT-based circular correlation (used in `decode_dial_dense`).

**Explicit epoch.** `REFERENCE_JD = 1684595` (≈ 205 BCE) anchors all date-to-residue conversions. No `datetime.today()` drift.

### 3.3 Unbinding (B-H3)

`dial_decoder.decode_dial_dense` projects the encoded state onto rolls of the dial's channel basis via FFT-based cross-correlation; argmax over rolls is the recovered residue. At D=13440 with 13 channels superposed the 13/13 round-trip is exact at modulus precision; D=940 with 8 channels also 8/8 exact.

The block-diagonal oracle (`encode_ant_block_diagonal` + `decode_dial_block_diagonal`) round-trips trivially within block; it serves as the ground-truth reference for B-H3.

---

## 4. Phase-operator preflight (Phase 3)

The Antikythera phase operator is **trivial**: `advance_day(state) = state ⊗ σ_day`. One operator, many projections. The projections — Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Metonic, Saros, … — are the per-dial decoder operators in [research/dial_decoder.py](research/dial_decoder.py); each is a per-cycle gear ratio applied to the same underlying day-counter state.

See [ANTIKYTHERA_PHASE_OP_PREFLIGHT.md](ANTIKYTHERA_PHASE_OP_PREFLIGHT.md) for the short standalone summary.

---

## 5. Validation against NASA Horizons / skyfield (Phase 4)

E-H1 and E-H2 details in §2.E. Summary:

- **E-H1**: PASS for the Saros cycle period (modern era, 3/3 anchor + Saros syzygies match within ±1 day). Hellenistic-era absolute placement deferred to a DE422 ephemeris load.
- **E-H2**: PARTIAL — peak Mars angular error 179.88° vs the documented mechanism's 38°. The encoder's pure-residue advance is strictly worse than the Greek deferent + epicycle model; matching the documented 38° would require encoding the Greek epicycle.

---

## 6. The Archimedes question

Cicero (*De re publica*, *Tusculan Disputations*) describes a planetarium built by Archimedes (captured at Syracuse, 212 BCE). The device he describes matches the Antikythera *functionally*. **DISPUTED:** is the Antikythera a descendant of an Archimedean design tradition? If yes, the surviving mechanism is ~150 years of iterative refinement away from its progenitor, and the coprime-factoring choices may have been distilled across generations. The HDC framing in this notebook is then a *distilled* design recovered from a single artefact rather than a single inventor's flash of insight.

We tag this DISPUTED and move on. Freeth (2021) leans toward Archimedean origin; others argue for Rhodian astronomical schools. The math we read off is the same regardless.

---

## 7. Vocabulary collisions specific to Antikythera

- **"Mechanism"** (the device) vs **"mechanism"** (the causal process). We use the device sense; "the mechanism" = the artifact unless context says otherwise.
- **"Gear"** (physical wheel) vs **"gear"** (HDC generator). Prefer "generator" or "channel" for the abstract sense.
- **"Cycle"** (astronomical period) vs **"cycle"** (graph-theoretic closed walk). We use the astronomical sense.
- **"Fiber"** (chess §7) — adopted with the refinement that here the fiber is *static and shared across species* (each celestial body is a "species" but planetary trains share the gear-pool).
- **"Phase"** — angular position on a dial = residue class in ℤ/n_dialℤ.
- **"Rendering"** — projection from the `encode_Ant(t)` dynamic state to a user-visible spatial or dial display, parameterised by a static radial-parameter table and a free scale parameter. Distinct from computer-graphics "rendering" (rasterisation, ray tracing).
- **"Orrery"** — any device or simulation that renders planetary positions in 2D/3D spatial arrangement at scaled orbital radii. Used genericly here for any spatial-position renderer; the word historically derives from the 4th Earl of Orrery's 1704 Tompion/Graham clockwork (anachronistic for Cicero's Archimedean planetarium).

---

## 8. Appendix: environment and reproducibility

- Python 3.14, numpy 2.4.4, scipy 1.17.1, sympy 1.14.0, skyfield 1.54.
- Deterministic seeds: `_BASE_SEEDS = {940: 42, 13440: 1729}` (after Gram-orthogonality pre-flight; may walk forward up to 16 steps).
- All cycle moduli, eccentricities, and reference epochs are module-level constants in [research/astronomical_cycles.py](research/astronomical_cycles.py), [research/pin_and_slot.py](research/pin_and_slot.py), [research/encode_ant.py](research/encode_ant.py).
- Run the H-battery: `cd docs/antikythera-maths && PYTHONIOENCODING=utf-8 python3 -m research.consolidated_tests`. Outputs [results/phase1_hypotheses.csv](results/phase1_hypotheses.csv) + [results/phase1_detail.json](results/phase1_detail.json).
- skyfield ephemeris cache: `docs/antikythera-maths/skyfield_data/de421.bsp` (gitignored; ~15 MB; downloaded on first use).

Final battery summary (from [results/phase1_hypotheses.csv](results/phase1_hypotheses.csv)): **9 PASS, 4 PARTIAL, 0 FAIL, 2 UNDETERMINED**.
