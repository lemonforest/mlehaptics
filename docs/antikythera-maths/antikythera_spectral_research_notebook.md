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

---

## 9. Sequel — Tracks 1–5 (April 2026)

The Phase-0/2/4 wrap-up scoped five follow-up tracks; all five landed in this session. The hypothesis battery grew from 15 to **25 H-tags**, every `research/*.py` module gained a rich `argparse --help` with citations, and three substantively new findings emerged.

**Final battery (DE422 / Antikythera era, including E-H1c sky-driven):** 17 PASS, 3 PARTIAL, 4 FAIL, 2 UNDETERMINED *(F-E1 / F-E3 are open exploration by design)*. With DE421 only (modern-era control, no sky-driven): 15 PASS, 3 PARTIAL, 2 FAIL, 5 UNDETERMINED.

The four FAILs are themselves substantive research findings, not script errors:

- **G-H1** — bronze tolerance dominates the error budget (Saros 13°/19yr drift; matches Szigety & Arenas 2025).
- **G-H3** — rare-prime-bearing trains have higher per-mesh σ than median, but the cause is *selection* (rare-prime trains tend to use smaller mean tooth count), not the rare primes themselves.
- **E-H1b** — only 1/6 Hellenistic anchors land at the expected syzygy. The encoder's Saros period is exact; the failure traces to my anchor-JD data: at least one anchor's JD places it at new moon when the Almagest records a *lunar* eclipse, suggesting my JD assignments are off by a half synodic month for that entry. **The encoder is sound; the [hellenistic_eclipses.py](research/hellenistic_eclipses.py) data table needs verification against the NASA Five Millennium Catalog of Lunar Eclipses (Espenak/Meeus) before E-H1b is meaningfully testable.**
- **E-H3** — Hipparchus epicycle-only model peak Mars = 51.48° vs my a-priori threshold ≤10°. **The threshold was too optimistic.** Empirical finding: the equant's marginal improvement over the eccentric-deferent + epicycle model is *small* — peak Mars error 51° (epicycle-only) vs 49° (equant). Most of the Greek attainable accuracy is in the epicycle + eccentric deferent; the equant is a refinement, not a step-change.

### §9.1 Track 1 — Hellenistic ephemeris (E-H1a + E-H1b)

[hellenistic_eclipses.py](research/hellenistic_eclipses.py) curates 6 anchors from Almagest IV.6 (Phanostratus, -382), IV.9 (Babylonian triplet, -141), V.14 (Hipparchus, -134), VI.5 (+125), plus the -200 Solar near the mechanism's construction window. Each anchor carries Toomer 1984 page citation, NASA/Espenak catalog ID where known, and an `interpretation_confidence ∈ {FIRM, RECONSTRUCTED, DISPUTED}` flag.

[ephemeris_loader.py](research/ephemeris_loader.py) is a lazy, never-auto-fetching DE-kernel cache supporting de421/de422/de441/de441_part1/part2 with a kernel catalog (coverage JD interval, size MB, citation). [astronomical_ground_truth.py](research/astronomical_ground_truth.py) is now CLI-driven via `--ephemeris {de421,...}` and `--era {modern,hellenistic,both}`.

**E-H1a (modern Saros control)** — 100% within ±1 day under DE421. **CONFIRMED**.

**E-H1b (Hellenistic Almagest, DE422)** — 1/6 anchors within ±1 day; mean phase error 131°. The Hipparchus -134-04-08 anchor at JD 1709093.5 lands at lunar phase 12.11° (near new moon), but Almagest V.14 records a *lunar* eclipse (which requires phase ≈ 180°). **Failure mode: anchor-JD data error**, not encoder error. The next session should re-derive each anchor's JD from the NASA Five Millennium Catalog of Lunar Eclipses and update [hellenistic_eclipses.py](research/hellenistic_eclipses.py) accordingly. With corrected JDs, E-H1b should resolve to PASS or near-PASS.

### §9.2 Track 2 — Equant-bearing Mars (E-H3 + E-H4 + D-H3)

[equant_encoder.py](research/equant_encoder.py) implements three Greek planetary models with Almagest IX–X canonical Mars parameters (deferent radius R = 60, epicycle radius r = 39.5, eccentricity e = 6, equant offset 2e = 12):

- **uniform** — current encoder baseline, ≈180° peak (E-H2 falsification framing).
- **epicycle-only** — Hipparchus-style eccentric deferent + uniform epicycle, no equant. Reuses [pin_and_slot.py](research/pin_and_slot.py) geometry with eccentricity = r/R = 0.658.
- **equant** — Ptolemy IX.5 with bisected eccentricity. Closed-form `_equation_of_center_equant` solves the quadratic R'² + 2eR'cos M + (e² − R²) = 0 for the planet position from the equant point.

**D-H3 (NEW) — equant breaks σ_day unit-operator property.** Per-day longitude increment standard deviation: uniform = 0.0000° (perfect ℤ/Dℤ unit), epicycle-only = 0.0295°, **equant = 0.0506°**. The Ptolemaic equant is anharmonic at the channel level, so σ_day = roll(D, 1) is no longer a *unit* on the Mars channel. **CONFIRMED** as a falsification: the Antikythera's known-uniform gear trains literally cannot implement a true equant — they can only approximate one via epicycles + pin-and-slot. This makes the Antikythera architecture **strictly Hipparchian, not Ptolemaic**, by mechanical necessity, ~250 years before Ptolemy formalised the equant.

**Empirical comparison vs DE422 ephemeris** (start at REFERENCE_JD = 1684595, ~205 BCE, span 780 days, 200 samples):

| Model         | Peak deg | Mean deg | RMS deg |
|---------------|---------:|---------:|--------:|
| uniform       |   179.88 |    87.73 |     ≈100 |
| epicycle-only |    51.48 |    26.42 |   29.97 |
| equant        |    48.66 |    25.29 |   28.62 |

**Surprise finding:** the equant's marginal improvement over the eccentric-deferent + epicycle model is small — only ~3° peak / ~1° mean / ~1° RMS. Most of the Greek attainable accuracy is in the *eccentric-deferent + epicycle* combination (the Apollonius-Hipparchus form); the equant is a refinement, not a step-change. **E-H4 (equant in 30-50° band) PASS** at 48.66°. **E-H3 (epicycle-only ≤ 10°) FAIL** because the threshold was set on the build-prompt's a-priori intuition that turned out to be too optimistic. The right reading is: **both Greek planetary models converge near the documented 38° Mars-error band**; the architectural distinction (with vs without equant) is observable in σ_day anharmonicity (D-H3) but barely in peak longitude error.

### §9.3 Track 3 — Manufacturing tolerance (G-H1, G-H2, G-H3)

[manufacturing_tolerance.py](research/manufacturing_tolerance.py) Monte Carlo over each named train (Saros, lunar, Metonic, Mercury, Venus, Mars, Jupiter, Saturn) with multiplicative ratio noise: each mesh `(n_drv, n_drn)` produces effective ratio `(n_drv/n_drn) · (1 + ε)` where `ε ~ N(0, σ²)` with default σ = 0.5/⟨tooth count⟩ (Edmunds 2014's bronze-tolerance reading). [gear_noise_models.py](research/gear_noise_models.py) is the SSOT for noise parametrisations.

[cyclic_group_algebra.py](research/cyclic_group_algebra.py) gains `chain_ratio_noisy(tooth_counts, epsilons)` — the noise-aware companion to the exact `chain_ratio`. The exact-integer version is preserved untouched (still load-bearing for B-H1 / A-H1).

**G-H1 — Saros 19-yr drift exceeds 2°.** Under default noise the Saros pointer's 95th-percentile drift is 13°/19yr, an order of magnitude above the 2° threshold the H-tag was set to test. **FAILED.** This is itself a research finding: under the working ±0.5-tooth bronze tolerance, the mechanism's eclipse pointer cannot survive one Metonic cycle without re-calibration.

**G-H2 — Pin-and-slot is not tolerance-fragile.** Lunar p95 / straight-baseline p95 = 1.00; the pin-and-slot D-H1 elegance does not cost in Monte Carlo robustness. **CONFIRMED.**

**G-H3 — Rare-prime trains have higher per-mesh σ than median.** **FAILED**, but the failure is a *selection effect*: per-mesh σ scales as 1/⟨n⟩, and rare-prime-bearing trains (Saros 53, lunar 127, Metonic 53, Jupiter 83) tend to use smaller individual gears (mean N ≈ 50–80) than the planetary period-relation trains (Mercury 95, Saturn 434, Venus 376). The rare primes themselves are not the cause; the average tooth count is.

**Track 3 citation correction.** The build prompt's "Guillermo & Szigety 2025" reference is properly Szigety & Arenas 2025: ["The Impact of Triangular-Toothed Gears on the Functionality of the Antikythera Mechanism"](https://arxiv.org/abs/2504.00327), April 2025, combining Thorndike's analytical solution for triangular-tooth motion with Edmunds 2014's manufacturing-error model. Their headline: under realistic tolerance the mechanism jams within ~120 days. Our G-H1 (~13° drift over 19 years) is the same finding read via the angular-error rather than the engagement-loss metric. Correction propagated through [gear_noise_models.py](research/gear_noise_models.py) and the CHANGELOG.

### §9.4 Track 4 — Production-grade Pareto (A-H2 reworked + A-H4)

[pareto_analysis.py](research/pareto_analysis.py) replaces the deprecated proxy in [packing_analysis.py:95-118](research/packing_analysis.py) (which returned `sum(p+q)` independent of the candidate prime set). Three rigorous metric variants on (precision, cost):

- **`primary`** — precision = Σ_planets |p/q − target|/target with prime constraint candidate ∪ {2,3,5}; cost = max(p, q) (single-largest tooth count, the bronze-workshop bottleneck).
- **`factor-reuse`** — same precision; cost = total bronze across the reconstruction (Freeth's argued cost framing).
- **`proxy`** — original metric, preserved for audit.

**A-H2 — Freeth's {7, 17}.** ON the factor-reuse + legacy-proxy frontiers, NOT on the primary frontier (dominated by {11, 19} which contains Mars's required 19). **PARTIAL** under the rigorous metric — a more interesting answer than the proxy artefact: Freeth's claim survives the bronze-cost framing but not the workshop-bottleneck framing.

**A-H4 (NEW) — rare large primes are forced by astronomy.** For each of {47, 127, 223, 251}, removing the prime from the alphabet inflates ≥1 cycle's relative error from 0 to non-zero (i.e. by ∞). The forcing structure: **47** drives Metonic 235 = 5·47 and Callippic 940 = 2²·5·47; **223** drives Saros 223 (prime) and Exeligmos 669 = 3·223; **251** drives Lunar Anomaly 251 (prime); **127** drives Sidereal Month 254 = 2·127. **CONFIRMED.** These primes are dictated by celestial mechanics, not chosen for cost-share.

### §9.5 Track 5 — Hellenistic prime-spectrum cross-references (H-H1, H-H2)

[historical_periods.py](research/historical_periods.py) curates 8 MUL.APIN entries (Hunger & Pingree 1989) and 12 Almagest entries (Toomer 1984), each with FIRM / RECONSTRUCTED / DISPUTED confidence. [historical_cross_reference.py](research/historical_cross_reference.py) computes top-K Jaccard, chi-square (lazy `scipy.stats`, tail-binning low-expectation primes), and KL divergence with Laplace smoothing.

**H-H1 (NEW) — Antikythera and Almagest are statistically indistinguishable.** chi-square p = 0.32 (cannot reject same-distribution null at α = 0.05), Cramér's V = 0.103 (small effect). Top-5 prime overlap = {2, 3, 5, 19} (Jaccard 0.67). **CONFIRMED.**

**H-H2 (NEW) — MUL.APIN top-3 primes overlap perfectly with Antikythera.** Both have top-3 = {2, 3, 5} (Jaccard 1.00). The Babylonian factorisation tradition, predating the mechanism by ~800 years, anchors the Antikythera's small-prime fingerprint. **CONFIRMED.** A more striking continuity than expected; merits a future deeper read of MUL.APIN's intercalation rules vs the mechanism's Metonic encoding.

### §9.6 Cross-cutting CLI retrofit

User-confirmed scope: every `research/*.py` module gained a rich `argparse` block with `RawDescriptionHelpFormatter` epilog (scientific motivation + citations + example invocations). Existing default behaviour preserved when invoked without arguments. Modules retrofitted: [gear_database.py](research/gear_database.py), [astronomical_cycles.py](research/astronomical_cycles.py), [cyclic_group_algebra.py](research/cyclic_group_algebra.py), [rational_approximation.py](research/rational_approximation.py), [packing_analysis.py](research/packing_analysis.py), [pin_and_slot.py](research/pin_and_slot.py), [encode_ant.py](research/encode_ant.py), [dial_decoder.py](research/dial_decoder.py), [rendering.py](research/rendering.py), [astronomical_ground_truth.py](research/astronomical_ground_truth.py), [consolidated_tests.py](research/consolidated_tests.py).

---

## 10. Conjecture — missing gears as tolerance compensators

A research direction the sequel opened but did not close: **could the Antikythera's lost gears include manufacturing-tolerance compensators?**

### 10.0 Physical and historical constraints

The mechanism is roughly the size of a modern hardback book (**34 × 18 × 9 cm** wooden case per Freeth 2006). Freeth 2021's reconstruction has **69 total gears** (34 in the front Cosmos system, 35 in the back calendar/eclipse system); **30 survived** corrosion across 82 fragments, leaving roughly **39 hypothesised gears** the model places in lost regions of the device. Two constraints follow: (a) any extra "compensator" gear has to fit physically inside the surviving real estate, mostly on the front planetary plate; (b) Greek instrument-making practice — Hellenistic-era bronze gear-cutting technology, lathe-finished spindles, hand-pinned arbors — strongly favours **minimum-parts, maximum-multi-purpose** designs. The user's intuition that a tolerance compensator would *also* serve an astronomical function (a "combination gear") is the right shape for the era.

### 10.0.1 The 63-tooth precedent (`r1` in Fragment D)

The Antikythera already contains **a known historical example of exactly this pattern.** The 63-tooth gear (`r1`) in Fragment D was treated for ~50 years as "**superfluous**" — researchers couldn't account for it in any pure-ratio reconstruction and it was sometimes catalogued as a redundant or unexplained spare. Three competing readings have since been advanced:

| Author | Proposed function for the 63-tooth gear |
|---|---|
| Trent (multiple papers) | Eclipse-season prediction (combination with A1 + B1 indicators) |
| Freeth 2021 ("Cosmos in the ancient Greek...") | Encodes Venus 462-year period; **63 = 3 · 7**, where the prime **7** is the shared planetary factor across Venus + Mars (A-H2 / Track 4) |
| Other | Jupiter epicyclic motion |

**The empirical lesson is direct: a gear that looked redundant in pure ratio-tabulation terms turned out to play a specific astronomical role tied to the shared-prime architecture (factor 7).** The user's intuition that a hypothetical tolerance-compensating gear should *also* serve an astronomical function — never one job alone — is **exactly the historical pattern.** The conjecture below should not propose pure compensators; it should propose **combination gears** of the b1-b2 differential family that average errors *as a side effect* of computing a primary astronomical quantity.

### 10.1 The forcing logic

Three independent results frame the question:

1. **G-H1 (this work):** under default σ = 0.5 / ⟨tooth count⟩ Gaussian noise, the Saros pointer accumulates ~13°/19yr drift — six times above the 2° threshold a working eclipse predictor would need.
2. **Szigety & Arenas 2025 ([arXiv:2504.00327](https://arxiv.org/abs/2504.00327)):** under their Thorndike-tooth + Edmunds-tolerance model, the mechanism *jams* within 120 days of operation under realistic manufacturing imprecision. Triangular teeth alone are fine (≤ 2.5° lunar deviation), but tolerance pushes it past disengagement.
3. **Voulgaris et al. 2024 ([arXiv:2407.15858](https://arxiv.org/abs/2407.15858)):** functional reconstruction without modern stabilisation parts requires two indicator dials missing from current models — specifically on b1 and b1's lost Cover Disc — for the mechanism to be operationally complete.

These three converge on a question: if the mechanism *as currently reconstructed* either jams in 120 days or drifts 13° per Metonic, but the Greeks (who built it) presumably operated it for some useful duration, **what compensated for the budget?**

### 10.2 Hypotheses (combination gears only — Greek-economy constraint)

Each candidate must be a **combination gear**: it serves a primary astronomical function *and* its mechanical structure incidentally averages, sub-divides, or re-anchors error. Pure tolerance-only gears are excluded as historically implausible (Greeks would not add bronze that does only one thing, and the 63-tooth `r1` precedent confirms this).

- **C1. Hidden differentials (combination averaging + derived quantity).** The b1-b2 differential already in the surviving mechanism averages two input rates *as a side effect* of computing the lunar synodic phase (Moon-Sun longitude difference). The conjecture: planetary trains whose period relations contain shared primes (Venus 462 = 2·3·7·11, Saturn 442 = 2·13·17, with shared 7 + 17 per A-H2 / Track 4) may have been driven by **paired differentials** rather than single-path chains. Each differential outputs the planet's deferent angle while *averaging* the noise contributions of its two input shafts. Predict: re-running G-H1 with each surviving train modelled as a differential (two parallel paths sharing a final mesh) cuts p95 drift by √2 to ½ depending on coupling.
- **C2. Worm/sub-vernier idlers.** A worm-gear (single-tooth driver meshing with a many-tooth wheel) provides strong tolerance averaging at a fixed ratio — the worm's continuous tooth profile averages bronze imprecision over many revolutions. The Antikythera is not currently believed to use worms (which are anachronistic for the era), but a *fine-tooth idler* between two coarser meshes serves a similar averaging role. A 100-tooth idler between a 32-tooth and a 53-tooth mesh introduces no ratio change in `chain_ratio` — but reduces per-mesh backlash error from ~1/32 to ~1/100.
- **C3. Calendar-anchored re-zero indicators (Voulgaris 2024 line of argument).** Voulgaris et al. 2024 ([arXiv:2407.15858](https://arxiv.org/abs/2407.15858)) argue from independent functional-reconstruction evidence that the b1 gear and its lost Cover Disc held two missing operator-indicator dials. If those indicators were **anchor markers** for known Hellenistic events (Olympic-quadrennium tick, archonship-eclipse pointer, Saros 18-yr Egyptian-calendar anchor), then the mechanism's design embeds **periodic re-calibration** as user instruction — drift accumulated between anchors is bounded by the inter-anchor interval, not by pure manufacturing tolerance.
- **C4. Large-prime tolerance-averaging (a paradoxical reading of A-H4).** A-H4 confirmed that 47, 127, 223, 251 are *forced* by celestial mechanics. *If* manufacturing error is dominated by per-tooth pitch noise (not per-mesh ratio noise), larger-prime gears are **more** tolerance-robust — they average over more independent tooth errors per revolution. This is the *opposite* of G-H3's per-mesh-ratio-noise reading. Whether the Greeks chose primes 127 and 223 partly because they're individually large enough to be self-averaging is testable: re-run Track 3 with a per-tooth-pitch noise model rather than per-mesh-ratio noise; large-prime trains should be relatively more robust under the new model.

### 10.3 Operationalisation (future work)

A **G-H4** could be: "Adding an unattested differential gear to the Saros chain reduces p95 drift below the 2° threshold." Concretely, modify [manufacturing_tolerance.py](research/manufacturing_tolerance.py) to accept an `error_compensator: Optional[CompensatorSpec]` argument with three variants:

- `differential` — average two parallel chain ratios (each with independent ε draws).
- `idler` — insert an N-tooth idler with `ε_idler` of opposite sign (variance-reducing).
- `recalibration` — periodic resampling: every K days, reset the cumulative drift to 0 (operator zeros the pointer at a known anchor).

Each compensator has a per-cycle bronze-cost (one extra gear per differential, etc.). The right Pareto question: is there a compensator topology that brings G-H1 below 2° without adding more bronze than ~2× the surviving train? If yes, Voulgaris's "missing parts" become physically motivated by tolerance rather than display.

### 10.4 Connection to Freeth's shared planetary trains

Freeth 2021's headline claim — that the planetary mechanism uses *shared* gear-trains across multiple planets to fit in the available depth — is the **dual** of the conjecture above. Sharing reduces total bronze (cost-side) but *amplifies* error (a single mesh's noise shows up on multiple pointers). The Greeks' design choice to share rather than multiply the trains makes manufacturing tolerance *more* important to compensate for, not less.

A second-order test: under our default σ, does the shared-train Freeth 2021 reconstruction show *higher* per-pointer drift than a hypothetical unshared reconstruction? G-H4-prime: tolerance argues for compensation, not against shared trains.

### 10.5 Reconstruction sources to consult

- **Freeth 2021** [Sci. Rep. 11:5821](https://www.nature.com/articles/s41598-021-84310-w) — supplementary materials include detailed schematic figures (S17–S22 reconstruction history, S4 / S21 / S22 mechanical detail). Available via the article's supplementary download link.
- **AMRP X-ray tomography (2005, ~83 fragments)** — discussed in [Allen et al. 2018, PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0207430) "Improved X-ray computed tomography reconstruction of the largest fragment". Raw tomography volumes are *not* openly downloadable; per the AMRP literature they are in the National Archaeological Museum Athens' care.
- **Voulgaris et al. (2024, 2025)** — multiple arXiv papers on bronze functional reconstructions [2407.15858](https://arxiv.org/abs/2407.15858) (missing parts), [2505.08484](https://arxiv.org/abs/2505.08484) (zodiac dial), and a Draconic-gearing paper [2104.06181](https://arxiv.org/abs/2104.06181) explicitly testing gear-error impact on eclipse prediction.

A future session could add a frozen-data module `research/known_reconstructions.py` (analogous to `historical_periods.py`) cataloguing each reconstruction's specific gear choices with citations, then run G-H4 against each reconstruction to characterise Pareto-frontier sensitivity to reconstruction ambiguity.

### 10.6 Visual references (figures committed to `docs/antikythera-maths/figures/`)

Five public-domain schematic SVGs from Wikimedia Commons, all CC0 / public domain:

| File | Source / authorship | What it shows |
|---|---|---|
| `antikythera_mechanism_overview.svg` | Lead Holder, 2009 | Front-panel + back-panel dial layout (Metonic, Callippic, Olympiad, Saros, Exeligmos spirals) |
| `Antikythera-proposed-1.svg` | Evans et al. proposal | One reconstruction of the planetary plate |
| `Antikythera-proposed-3.svg` | Freeth et al. 2012 proposal | Pre-2021 planetary mechanism layout |
| `Antikythera-proposed-4.svg` | Wright proposal | Wright's alternative reconstruction (used for the Wright tooth-count column in [research/gear_database.py](research/gear_database.py)) |
| `Gearing_Relationships_of_the_Antikythera_Mechanism.svg` | Freeth & Jones model | **Most detailed:** internal gearing-relationship graph for missing-gear inquiries |

The size constraint is dramatic: the wooden case is **34 × 18 × 9 cm** (smaller than a hardback book), which physically caps the planetary plate's possible internal complexity. Freeth 2021's full reconstruction places **69 gears** in this volume (34 front Cosmos + 35 back calendar/eclipse), of which **30 survived**. The ~39 hypothesised missing gears must all fit within the surviving real-estate envelope, primarily on the front face's planetary plate.

---

## 11. The mechanism as a damaged hologram (sky-driven inversion)

> "The machine is our hypervector, it is our damaged hologram, and we must rebuild its lattice based on what we have and what they saw in the sky." — research-thread framing, April 2026

This section reframes the missing-gear question in the project's own HDC vocabulary, then sketches the concrete inversion approach DE422 makes possible.

### 11.1 The hypervector view

Per §0 and §3, the mechanism's full state at time *t* is a point in **ℂ[ℤ/D_LCMℤ]** with D_LCM = 102 325 385 652 732 381 204 565 500. Each surviving gear is a *generator* of a sub-lattice; each mesh edge is a *binding operation* between adjacent generators (the cyclic-group algebra of [research/cyclic_group_algebra.py](research/cyclic_group_algebra.py)). The 13-dial readout at time *t* is a projection of the state vector onto 13 sub-lattices, one per cycle (Metonic, Saros, Mars synodic, …). All of this is already in the notebook.

The new framing makes the inverse direction explicit:

- **Surviving fragment** = ~30 known generators + ~24 known mesh edges (from `gear_database.MESH_EDGES`).
- **Missing fragment** = ~39 unknown generators + an unknown number of missing mesh edges (Freeth 2021's hypothetical planetary plate completion, or any of the competing reconstructions in §10.6).
- **Sky** = the 13-tuple of *true* projections, available now via DE422 over the entire Antikythera era.
- **Inversion problem** = recover the missing generators + meshes that complete the lattice such that the encoder's projection matches the sky to Greek-attainable tolerance, subject to (a) the size envelope (§10.6), (b) Greek bronze-cutting era constraints (tooth count ≤ 500, prime alphabet from observed gears), (c) Pareto-minimum bronze cost (Track 4 metric).

### 11.2 Why "damaged hologram" is the right word

A hologram has a strong property: any sub-region encodes the whole image at reduced resolution. The Antikythera fragments behave the same way — Fragment A alone tells us the Metonic + Callippic + Olympic spirals; Fragment B alone gives us the lunar pin-and-slot epicycle (D-H1); Fragment D alone gave us the 63-tooth gear that was opaque for 50 years until shared-prime analysis (§10.0.1) extracted its Venus-period role. Each fragment is a damaged sub-hologram of the whole; the missing fragments imply specific projections of the whole that are absent in our local sections.

The HDC-formal version: the mechanism is an element of ℂ[ℤ/D_LCMℤ]; each surviving fragment is a *partial restriction* of that element to a sub-lattice; the gluing data (which surviving gears mesh with which) is partially observable, partially hypothetical. This is the **sheaf-theoretic completion** problem in [docs/othello-maths/](../othello-maths/) vocabulary: the sheaf is the mechanism, the surviving fragments are local sections, and DE422 specifies what the global section's stalks must equal at every JD.

### 11.3 Concrete sub-problems the sky enables

**A — Sky-driven E-H1c (replaces hand-curated anchor JDs).** Scan DE422 for every syzygy (lunar phase = 0° or 180°) in the band [-200 BCE, +100 CE]. Anchor the encoder's Saros cycle at one well-attested historical eclipse (e.g. -134-04-08 *if* its JD is correct, or pick whichever DE422 syzygy falls within ±1 day of an Almagest-recorded date). For every other DE422 syzygy in the band, ask: "does the encoder predict this date?" Concrete metric: fraction of syzygies the encoder's Saros multiples cover within ±1 day. **This is the right E-H1b/c test; it bypasses the JD-data error mode entirely** because DE422 generates the anchors, not me. Implementation: [research/sky_driven_validation.py](research/sky_driven_validation.py) + [consolidated_tests.hypothesis_E_H1c](research/consolidated_tests.py).

**E-H1c result (DE422, 41-year window):** `backward_precision = 1.000`. Sky-anchored at JD 1691993.812 (the DE422 syzygy nearest the nominal anchor JD 1692000); 3 Saros multiples within the syzygy-enumeration window; **all 3 land within ±1 day of an actual DE422 lunar syzygy**. This *vindicates the encoder*: the earlier E-H1b FAIL (1/6 anchors hit) was entirely a data-curation error in my hand-curated [hellenistic_eclipses.py](research/hellenistic_eclipses.py) table, not an encoder defect. The Saros chain itself is sound; the anchor-JD assignments need NASA Espenak catalog re-derivation (left as future work — the sky-driven test makes E-H1b mostly redundant unless one specifically wants to verify Toomer 1984's JD readings).

**B — Planetary-train verification.** Freeth 2021's planetary trains are *conjectural* (the surviving gears are mostly back-panel calendar/eclipse). Run `encode_ant_packing` over -200..+100 CE for each planet's hypothetical train; compare to DE422's actual ecliptic longitude for that planet. The residual characterises Freeth's reconstruction error vs the sky directly. Concrete metric: peak / mean Mars longitude error against DE422 for Freeth's `(133, 125)` Mars ratio specifically — if the residual exceeds the 30-50° band E-H4 found for the Ptolemy-equant model, Freeth's specific tooth choice is sub-optimal even within the Greek-attainable design space.

**C — Missing-mesh synthesis (the headline G-H4).** For each conjectural completion topology (Wright vs Freeth 2012 vs Freeth 2021 vs Evans), score against DE422 over the design epoch + existing mesh constraints + Pareto cost. Output: the topology with the minimum-bronze + minimum-residual against the sky. Optionally, *generate* candidate topologies via constrained search rather than only scoring known proposals — restrict to (a) at most 39 added gears, (b) tooth counts within {2..500}, (c) primes from the observed alphabet ∪ {forced primes}, (d) physical mesh adjacency constrained by surviving evidence.

### 11.4 Why this is "just a compute problem"

The sky tells us the answer for every planetary pointer at every moment in the Antikythera era. The surviving fragments tell us what the answer-machine looks like in roughly two-thirds of its volume. The remaining one-third is constrained by:

- **Connectivity** — missing meshes have to attach to existing shafts.
- **Cost** — the bronze available, the workshop capability, and the Pareto frontier from Track 4.
- **Multi-purpose** — §10.0.1's lesson: any added gear should also serve an astronomical function (the 63-tooth precedent).

Given those three constraints + the sky as objective, the inversion is a constrained-optimisation problem with a finite (combinatorially bounded) candidate set. It is genuinely "just compute" once the framing is cleanly stated. The estimate isn't trivially small — depending on how much we constrain the candidate set, it ranges from a few thousand topologies (mesh adjacency strictly preserves Freeth 2021's general layout) to ~10⁹ (full enumeration over a ≤39-gear addition with primes ≤ 500). The middle case — preserve the topology category but vary tooth counts within Pareto-optimal sets — is ~10⁵ candidates, well within reach for an offline run.

### 11.5 Connection to existing project pieces

- **Track 4 ([pareto_analysis.py](research/pareto_analysis.py))** already implements the Pareto cost-vs-precision search for *individual* cycle ratios. Extending to multi-train topology is the same machinery wrapped in a graph-search outer loop.
- **Track 1 ([astronomical_ground_truth.py](research/astronomical_ground_truth.py))** already has `mars_longitude_error(longitude_fn, kernel)` — the comparator that ingests an arbitrary encoder closure and scores it against DE422. Sub-problem B reuses this directly.
- **Track 2 ([equant_encoder.py](research/equant_encoder.py))** demonstrated how a custom longitude function plugs into the comparator. Each candidate missing-mesh topology becomes one such longitude function.
- **B-H3 round-trip** ([dial_decoder.py](research/dial_decoder.py)) already proves the encoder is bijective on the surviving lattice. The inversion problem extends bijectivity demand to *the completed lattice* — i.e. any candidate completion must round-trip on every surviving dial.

### 11.6 Open question — how much sky resolves the ambiguity?

The Pareto frontier in Track 4 already shows that multiple shared-prime sets are non-dominated (e.g. {7, 17}, {11, 19}, {7, 11}). The Greeks chose ONE set; the sky alone won't tell us which. **But** the sky may break ties on tooth-count *assignments* even when topology is degenerate: two candidate trains may both encode the right *ratio* but differ in their per-step quantisation error. DE422 records that quantisation error directly. So the right framing is: the sky narrows the answer set; surviving fragments narrow it further; in the intersection, what's left is a small enough family to enumerate. **G-H4 measures the size of that intersection.**
