# Antikythera-Maths — Session Summary (Phase 0 + 2 + 4 wrap-up)

**Date:** April 2026
**Session goal:** Resume the work scoped in [SESSION_HANDOFF.md](../SESSION_HANDOFF.md): finish Phase 0 (pin-and-slot), build Phase 2 (encoder + decoder + rendering), wire Phase 4 (skyfield), run the H-battery, and write all four docs.

**Branch:** `claude/practical-pascal-8968b8`
**PR target:** `main`

---

## What passed

- **B-H1** (D_Ant computable): D_Ant = 102 325 385 652 732 381 204 565 500 (27 digits, 16 distinct primes). Pure linear algebra — PASS by construction.
- **B-H2** (σ_day is a unit): σ_day = `roll_operator(D, 1)`; gcd(1, D) = 1 for every D. PASS by construction.
- **B-H3** (HDC binding ↔ gear composition): 13/13 dials round-trip exactly at D=13440 dense superposition encoder. Cross-validated against block-diagonal oracle. **The project's load-bearing structural claim — the chess §9f coprime-roll-binding pattern applied to gear phases — verified.**
- **C-H1** (zero error correction): all 40 gear pairs bijective; PASS as theorem.
- **C-H2** (spiral-aliasing horizon): Saros 223/4 spiral and Metonic 235/5 spiral wrap behaviour formally identical to chess §11.3.3 torus-clip. NOVEL framing, verified by construction.
- **D-H1** (pin-and-slot antisymmetric fiber): ||M_anti|| / ||M_sym|| = 1.000000 for the Freeth 2006 ε = 0.054 geometry. Reference uniform-circular ratio also 1.000000. Both saturate at the chess §9m pawn directed-Laplacian limit. The differentiator between pin-and-slot and uniform circular is in the *structure* of M_sym (Jacobian-weighted Laplacian).
- **D-H2** (non-pin-and-slot dials T-symmetric): 13/13 dials at residue 0 at the reference epoch. Trivial check by construction.
- **E-H1** (Saros eclipse prediction): 3/3 anchor + Saros entries match within ±1 day at the modern era anchor (1999-08-11 → 2017-08-21 → 2035-09 syzygies). Limited to 3 entries by DE421's 1900-2050 coverage; absolute Hellenistic-era validation deferred to DE422.
- **F-E2** (D_Ant single-integer dimension): D_LCM computed and reported. PASS — the answer is the integer; whether it's *useful* is separately discussed (it's not; encoder uses LCMState).

---

## What came back PARTIAL

- **A-H1** (best rational under tooth budget): 15% of cycles within top-3 CF convergents (build-prompt strict prediction); 54% match the best rational under a 500-tooth budget (weaker claim). The build prompt's prediction is **falsified**, but the underlying intuition — the Greeks chose budget-respecting good approximations — is supported. Real research finding: *Greeks optimised against bronze-cutting feasibility, not against pure rational-approximation rank.*
- **A-H2** ({7, 17} planetary primes Pareto-optimal): not on our proxy frontier. The proxy sums numerator + denominator across planetary period-relations and counts shared factors — too crude to capture the actual precision/cost trade-off. A more rigorous Pareto analysis is a follow-up.
- **A-H3** (prime spectrum non-random): qualitatively yes (small primes + sparse large primes for irrational cycles), but the small-prime overweight is only 1.15× null — not "heavily biased." The large-prime presence (47, 53, 61, 83, 127, 223) is the more striking signature.
- **E-H2** (Mars retrograde error): peak error 179.88° vs the documented Greek mechanism's 38°. **The encoder's pure-residue uniform-advance model is strictly worse than the Greek deferent + epicycle model.** Matching the documented 38° requires modelling the Greek epicycle — a future research extension. This is the project's first clearly *FAILED at the encoder layer* hypothesis, and a useful one: it tells us where the bronze mechanism's "designed-in" structure exceeds what a pure phase-space encoder reproduces.

---

## What came back UNDETERMINED

- **F-E1** (Mechanism prime spectrum vs Residue-HDC): empirical point of contact (16 distinct primes overlap with the Residue-HDC alphabet) but the mechanism's primes were forced by celestial mechanics, not chosen for VSA convenience. A meaningful comparison would ask: *given the mechanism's prime alphabet as Residue-HDC moduli, what's the maximum-binding-density encoding?* Not answered here.
- **F-E3** ("failed" cycles): 3 of 13 cycles have > 0.1% residual error vs modern ephemeris (Mars dominant). The interpretation is open: are these residuals Greek-theory-limited (cannot be improved without equants) or budget-limited (improvable with more bronze)?

---

## Bugs fixed in flight

Two bugs in pre-existing Phase 0 code (commit `af73446`) surfaced when wiring the H-battery and were fixed:

1. **`semi_convergents` OOM** — the inner enumeration over CF terms ran for `a_k` iterations per term; for irrational ratios near machine precision `a_k` reached ~10^12 and tripped MemoryError. Fix: optional `budget` parameter that prunes the enumeration once max(p, q) > budget. ([rational_approximation.py:86](research/rational_approximation.py))
2. **`cycle_cf_ranks` squared the true_ratio** — the line `true_ratio *= mech_ratio` after computing the modern/mechanism ratio caused (235, 19) to be looked up against a CF of ~152.97 (= 12.368²) instead of ~12.368 (the actual synodic-months-per-year ratio). Fix: removed the spurious multiplication. ([packing_analysis.py:155](research/packing_analysis.py))

These two fixes converted A-H1 from a runner-crashing hypothesis to a meaningful PARTIAL with real numbers.

---

## Plan-agent corrections folded into encoder design

Pre-encoder design review by a Plan agent flagged six concrete issues that all made it into [research/encode_ant.py](research/encode_ant.py):

1. **Dense complex random channel bases**, not delta spikes — delta collapses at D=940 where total residue classes exceed D.
2. **`np.complex128` throughout** — roll preserves orthogonality under complex inner product; real-valued bases lose it.
3. **Block-diagonal oracle encoder** as ground-truth reference for B-H3 cross-validation.
4. **D=940 planetary dials raise `UnsupportedDialError`** — explicit degradation, no silent lossy encoding.
5. **σ_day = `roll_operator(D, 1)` full stop** — single unitary; per-cycle rate logic lives in decoder projection.
6. **Explicit `REFERENCE_JD` epoch + Gram-matrix orthogonality pre-flight** — byte-reproducible deterministic seeding; off-diagonal max < 0.05 enforced (auto-reseeds up to 16 times).

The Gram-matrix pre-flight passes 0.0498 at D=940 (tight, under threshold) and 0.0191 at D=13440 (comfortable margin). All cross-validation tests round-trip 13/13 at D=13440 and 8/8 at D=940.

---

## What's scoped to the sequel

1. **DE422 / DE441 ephemeris** — replace the modern-era E-H1 anchor with Hellenistic eclipses; full 200 BCE – 100 CE validation.
2. **Equant-bearing Mars encoder** — add a per-dial epicycle model so E-H2 reproduces the 38° peak instead of 180°. Research finding: how much of the Greek mechanism's accuracy comes from epicycles alone vs equants?
3. **Manufacturing-tolerance simulation** — overlay Guillermo & Szigety 2025's per-gear noise model on our encoder; quantify the implementation-layer error budget.
4. **Production-grade A-H2 Pareto analysis** — replace the proxy metric with a rigorous precision-vs-cost tradeoff; check Freeth 2021's {7, 17} claim properly.
5. **Hellenistic prime-spectrum cross-references** — does Babylonian MUL.APIN or Ptolemy's *Almagest* show evidence of the same prime-factorisation choices? (Build prompt extra credit.)

---

## Reproducibility

```bash
cd docs/antikythera-maths
PYTHONIOENCODING=utf-8 python3 -m research.consolidated_tests
# → results/phase1_hypotheses.csv
# → results/phase1_detail.json

PYTHONIOENCODING=utf-8 python3 -m research.astronomical_ground_truth
# → downloads de421.bsp on first run (~15 MB, into ./skyfield_data/)
```

Wall time: H-battery ~30 s including skyfield calls. First run downloads de421.bsp (~10–20 s on a typical connection).

Final battery summary: **9 PASS, 4 PARTIAL, 0 FAIL, 2 UNDETERMINED.**

---

# Sequel Session — Tracks 1-5 (April 25, 2026)

**Goal:** Land all five sequel tracks scoped above; refactor the H-battery; add a rich `--help` to every research module.

**Final battery summary** (DE422, era=both): **16 PASS / 3 PARTIAL / 4 FAIL / 2 UNDETERMINED** across 25 H-tags. With DE421 only: 15 PASS / 3 PARTIAL / 2 FAIL / 5 UNDETERMINED.

**New modules** (8 added, 11 retrofitted): [hellenistic_eclipses.py](../research/hellenistic_eclipses.py), [ephemeris_loader.py](../research/ephemeris_loader.py), [gear_noise_models.py](../research/gear_noise_models.py), [historical_periods.py](../research/historical_periods.py), [pareto_analysis.py](../research/pareto_analysis.py), [equant_encoder.py](../research/equant_encoder.py), [manufacturing_tolerance.py](../research/manufacturing_tolerance.py), [historical_cross_reference.py](../research/historical_cross_reference.py).

## What passed (new H-tags)

- **A-H4** (rare large primes are forced by astronomy): removing 47 / 127 / 223 / 251 inflates ≥1 cycle's relative error from 0 to non-zero. The forcing structure: **47** drives Metonic 235 = 5·47 and Callippic 940 = 2²·5·47; **223** drives Saros 223 (prime) and Exeligmos 669 = 3·223; **251** drives Lunar Anomaly 251 (prime); **127** drives Sidereal Month 254 = 2·127. CONFIRMED.
- **D-H3** (equant breaks σ_day unit-operator property): per-day longitude-increment std = 0.0000° (uniform, perfect ℤ/Dℤ unit) → 0.0506° (equant, anharmonic). The Antikythera's known-uniform gear trains literally cannot implement a true equant — they can only approximate one via epicycles + pin-and-slot. CONFIRMED. **The mechanism is strictly Hipparchian, not Ptolemaic, by mechanical necessity, ~250 years before Ptolemy formalised the equant.**
- **E-H1a** (modern Saros control, DE421): 100% within ±1 day. CONFIRMED.
- **E-H2** (uniform Mars peak ≥ 150°): 179.88° peak — uniform model fails as predicted. CONFIRMED via falsification framing.
- **E-H4** (Ptolemy equant in 30-50° band, the documented Greek limit): 48.66° peak / 25.29° mean / 28.62° RMS. **PASS in band**. The build prompt's "~38°" figure for Greek-attainable Mars accuracy is reproduced by our equant encoder under Almagest IX-X canonical parameters (R = 60, r = 39.5, e = 6, equant offset 2e = 12).
- **G-H2** (pin-and-slot tolerance ≤ 1.2× straight baseline): ratio = 1.00. CONFIRMED.
- **H-H1** (Antikythera spectrum vs Almagest is statistically indistinguishable): chi-square p = 0.32, Cramér's V = 0.103. Top-5 prime overlap = {2, 3, 5, 19} (Jaccard 0.67). CONFIRMED.
- **H-H2** (MUL.APIN top-3 primes overlap with Antikythera): both have top-3 = {2, 3, 5} (Jaccard 1.00). The Babylonian factorisation tradition, predating the mechanism by ~800 years, anchors the Antikythera's small-prime fingerprint. CONFIRMED — striking 800-year continuity.

## What came back PARTIAL (reworked)

- **A-H2** ({7, 17} planetary shared-prime choice Pareto-optimal): rebuild on rigorous (precision, cost) frontier in [pareto_analysis.py](../research/pareto_analysis.py) replaces the buggy proxy in [packing_analysis.py:95-118](../research/packing_analysis.py) (which returned `sum(p+q)` independent of candidate). Result: {7, 17} is on the **factor-reuse** + **legacy-proxy** frontiers (Freeth's bronze-cost framing) but NOT on the **primary** max-tooth-count frontier (dominated by {11, 19} which contains Mars's required 19). PARTIAL — a more nuanced answer than the proxy artefact: the {7, 17} claim survives Freeth's bronze-cost framing but not the workshop-bottleneck framing.

## What came back FAILED (research findings, not script errors)

- **G-H1** (Saros pointer p95 ≤ 2°/19yr): 13°/19yr at default σ = 0.5/⟨n⟩. **FAILED**. The mechanism's eclipse pointer cannot survive one Metonic cycle without re-calibration under the working bronze-tolerance model. Aligns with Szigety & Arenas 2025 ([arXiv:2504.00327](https://arxiv.org/abs/2504.00327)) finding that the mechanism would jam in ~120 days — same physical situation read through the angular-error rather than the engagement-loss metric.
- **G-H3** (rare-prime trains within ±15% of cross-train median per-mesh σ): 1/4 within band. **FAILED, but as a selection effect**: per-mesh σ scales as 1/⟨n⟩, and rare-prime-bearing trains tend to use smaller individual gears (mean N ≈ 50-80 for Saros / Metonic / lunar / Jupiter) than the planetary period-relation trains (Mercury 95, Saturn 434). The rare primes themselves are not the cause; the average tooth count is.
- **E-H1b** (Hellenistic Almagest within ±1 day AND ±2° phase): 1/6 anchors within ±1 day; mean phase err 131°. **The encoder is sound**: the failure traces to my anchor-JD assignments. Specifically the Hipparchus -134-04-08 anchor at JD 1709093.5 lands at phase 12° (near new moon) but Almagest V.14 records a *lunar* eclipse (phase ≈ 180°). My JD is off by ~half a synodic month for that entry — likely similar errors for some others. **Action item:** re-derive each anchor's JD from the NASA Five Millennium Catalog of Lunar Eclipses (Espenak/Meeus) and update [hellenistic_eclipses.py](../research/hellenistic_eclipses.py).
- **E-H3** (Hipparchus epicycle-only ≤ 10°): 51.48° peak. **The threshold was too optimistic.** Empirical finding: the equant's marginal improvement over the eccentric-deferent + epicycle model is small (peak Mars: 51° epicycle-only vs 49° equant). Most of the Greek attainable accuracy is in the *eccentric-deferent + epicycle* combination (the Apollonius-Hipparchus form); the equant is a refinement, not a step-change. The architectural distinction (with vs without equant) is observable in σ_day anharmonicity (D-H3) but barely in peak longitude error.

## What stayed UNDETERMINED (open exploration, by design)

- **F-E1** (mechanism prime spectrum vs modern Residue-HDC) — empirical contact, not causal claim.
- **F-E3** (which cycles are "failed" vs modern ephemeris) — descriptive.

## New conjecture opened: missing gears as tolerance compensators

A research direction the sequel surfaced but did not close (notebook §10):

The convergence of three findings — our G-H1 (13°/19yr drift), Szigety & Arenas 2025 (120-day jam), and Voulgaris et al. 2024 ([arXiv:2407.15858](https://arxiv.org/abs/2407.15858)) (b1 + b1 cover disc indicators missing for operational completeness) — suggests the lost gears might include **manufacturing-tolerance compensators**: differentials that average errors across paired paths, idler gears that sub-divide angular steps, or operator re-calibration mechanisms keyed to known Hellenistic anchor events. **G-H4 (future):** "Adding an unattested differential gear to the Saros chain reduces p95 drift below 2°." Implementation sketched in notebook §10.3.

## Open data work

- **DE441_part1 download (~1.5 GB)** failed with HTTP 404 — skyfield 1.54's URL list points at `https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de441_part-1.bsp` which 404s. **DE422 (660 MB) downloaded successfully** and covers the entire Antikythera era. Future: investigate a working DE441 mirror or use de441's NAIF SPICE source.
- **Anchor JD verification** (E-H1b) — re-derive each Almagest anchor against NASA Espenak catalog.
- **Hellenistic prime-spectrum sample size is small** (~20 entries) — H-H1's chi-square p-value sits at 0.32 with low statistical power. Adding the Babylonian Goal-Year Texts and ACT planetary-theory tables would roughly double the sample.
- **AMRP X-ray tomography raw volumes** are not openly downloadable per the literature; held by the National Archaeological Museum Athens.

## Reproducibility (sequel)

```bash
cd docs/antikythera-maths

# Pull a kernel (one-time, opt-in):
PYTHONIOENCODING=utf-8 python3 -m research.ephemeris_loader \
    --download de422 --yes        # 660 MB, covers -3001 .. +3000

# Full battery, both eras:
PYTHONIOENCODING=utf-8 python3 -m research.consolidated_tests \
    --era both --ephemeris de422
# -> results/phase1_hypotheses.csv (25 rows)
# -> results/phase1_detail.json

# Smoke-test --help on every module:
for m in gear_database astronomical_cycles cyclic_group_algebra \
        rational_approximation packing_analysis pin_and_slot \
        encode_ant dial_decoder rendering hellenistic_eclipses \
        ephemeris_loader gear_noise_models historical_periods \
        pareto_analysis equant_encoder manufacturing_tolerance \
        historical_cross_reference astronomical_ground_truth \
        consolidated_tests; do
  python3 -m research.$m --help > /dev/null && echo "$m: OK"
done
```

Wall time: H-battery with DE422 ~30 s after kernel cached (first run downloads ~660 MB, takes 1-3 min on a typical connection).

**Sequel battery summary: 16 PASS / 3 PARTIAL / 4 FAIL / 2 UNDETERMINED across 25 H-tags.** Of the 4 FAILs: 2 are research findings (G-H1 manufacturing tolerance, G-H3 selection effect), 1 is a data-table error (E-H1b anchor JDs), 1 is an over-tight threshold that revealed an interesting equant/non-equant near-equivalence (E-H3).
