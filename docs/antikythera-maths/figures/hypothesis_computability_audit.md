# Hypothesis Computability Audit

**Date:** April 25, 2026
**Scope:** All 33 hypotheses articulated in this thread — the original 25-row H-battery (commits up through `52b385b`) plus the 8 architectural-mode hypotheses (§10–§11.6.15, commits `9425706`–`38744a3`).

---

## Status legend

- **DONE** — Computed and recorded; result is in `results/phase1_hypotheses.csv` or notebook.
- **CODE-READY** — Algorithm defined, data available; can be computed today with existing code or a small extension (≤ 50 LOC).
- **SCOPED** — Hypothesis is formal and falsifiable; computation requires moderate code (50–300 LOC) but no new data.
- **DATA-BLOCKED** — Requires offline data we don't have (AMRP X-ray volumes, fragment photographs, paywalled papers).
- **ANALYTIC-RESOLVED** — Worked through analytically; no computation needed.
- **ARCHITECTURAL** — Open conjecture; not directly testable without committing to one specific implementation.

---

## Phase 1 H-battery (25 hypotheses)

All landed and tested under the [consolidated_tests.py](../research/consolidated_tests.py) battery. Final summary (DE422 + intermittent allowed): **17 PASS / 3 PARTIAL / 4 FAIL / 2 UNDETERMINED across 26 H-tags** (E-H1c added in `52b385b`).

### A-series — Coprime addressing

| ID | Statement | Result | Computability |
|---|---|---|---|
| A-H1 | Mechanism ratios are best rational approximations under tooth-count budget | PARTIAL (top-3 CF: 15%; best-under-budget-500: 54%) | **DONE** |
| A-H2 | {7,17} planetary shared-prime choice is Pareto-optimal | PARTIAL (on factor-reuse + proxy frontiers, NOT primary) | **DONE** |
| A-H3 | Prime spectrum non-random | PARTIAL (small-prime overweight 1.15× null; sparse large primes 47/53/61/83/127/223 distinctive) | **DONE** |
| A-H4 | Rare large primes (47, 127, 223, 251) are forced by astronomy | PASS (∞× inflation when removing each) | **DONE** |

### B-series — Algebraic structure

| ID | Statement | Result | Computability |
|---|---|---|---|
| B-H1 | Every cycle is element of ℂ[ℤ/D_LCMℤ] | PASS (D_LCM = 27-digit composite with 16 distinct primes) | **DONE** |
| B-H2 | σ_day = roll(D, 1) is unit | PASS (gcd(1, D) = 1) | **DONE** |
| B-H3 | HDC binding via coprime roll = gear composition | PASS (13/13 dials at D=13440 round-trip exact) | **DONE** |

### C-series — Bounds and aliasing

| ID | Statement | Result | Computability |
|---|---|---|---|
| C-H1 | Zero intrinsic error correction | PASS (40 gear pairs all bijective) | **DONE** |
| C-H2 | Spiral-dial wrap = chess §11.3.3 torus-clip | PASS (Saros 223/4=55.75 m/turn; Metonic 235/5=47.0) | **DONE** |

### D-series — T-breaking

| ID | Statement | Result | Computability |
|---|---|---|---|
| D-H1 | Pin-and-slot is antisymmetric fiber | PASS (||M_anti||/||M_sym|| = 1.0 saturates pawn directed-Laplacian) | **DONE** |
| D-H2 | Non-pin-and-slot dials are T-symmetric | PASS (13/13 at residue 0 at epoch) | **DONE** |
| D-H3 | σ_day fails as unit on equant-encoded channel | PASS (uniform std 0.0000° → equant std 0.0506° per day; ∞× ratio) | **DONE** |

### E-series — Astronomical ground truth

| ID | Statement | Result | Computability |
|---|---|---|---|
| E-H1a | Modern Saros syzygies (1999, 2017) within ±1 day | PASS (3/3 anchors via DE421) | **DONE** |
| E-H1b | Almagest Hellenistic anchors (-382 to +125) within ±1 day AND ±2° | FAIL (1/6; anchor JD data error in [hellenistic_eclipses.py](../research/hellenistic_eclipses.py)) | **DONE** but FAILed due to data-curation, not encoder; DATA-BLOCKED for proper test (requires NASA Espenak catalog re-derivation of JDs) |
| E-H1c | Sky-driven Saros chain: encoder anchored on DE422 syzygy reliably marks others within ±1 day | PASS (backward_precision = 1.000) | **DONE** |
| E-H2 | Uniform Mars peak error ≥ 150° (uniform model insufficient) | PASS (179.88° peak) | **DONE** |
| E-H3 | Hipparchus epicycle-only Mars peak ≤ 10° | FAIL (51.48° peak; threshold was too optimistic — epicycle-only ≈ equant in peak error) | **DONE** but threshold needs widening per §9.2 finding |
| E-H4 | Ptolemy equant Mars peak in 30–50° band | PASS (48.66° peak) | **DONE** |

### F-series — Open exploration (intentionally non-PASS/FAIL)

| ID | Statement | Result | Computability |
|---|---|---|---|
| F-E1 | Mechanism prime spectrum matches modern Residue-HDC? | UNDETERMINED | **ARCHITECTURAL** (no clean operationalisation; intentionally open) |
| F-E2 | D_LCM where every cycle is single integer | PASS (D_LCM exists; LCMState symbolic) | **DONE** |
| F-E3 | Which cycles are "failed" (>0.1% residual)? | UNDETERMINED (3 of 13 fail) | **DONE** descriptively |

### G-series — Manufacturing tolerance

| ID | Statement | Result | Computability |
|---|---|---|---|
| G-H1 | Saros pointer p95 ≤ 2°/19yr under default σ | FAIL (continuous: 13.2°) → PASS (intermittent: 0.000°). G-H1's status is REGIME-DEPENDENT — flip captured in §11.6.10.8. | **DONE** (both regimes) |
| G-H2 | Pin-and-slot tolerance ≤ 1.2× straight baseline | PASS (ratio 1.00) | **DONE** |
| G-H3 | Rare-prime trains within ±15% of cross-train median per-mesh σ | FAIL (1/4; selection effect with mean tooth count) | **DONE** |

### H-series — Historical cross-references

| ID | Statement | Result | Computability |
|---|---|---|---|
| H-H1 | Antikythera spectrum vs Almagest indistinguishable (chi² p > 0.05) | PASS (p = 0.32, Cramér's V = 0.103, top-5 Jaccard 0.67) | **DONE** |
| H-H2 | MUL.APIN top-3 prime overlap with Antikythera ≥ 2/3 Jaccard | PASS (Jaccard 1.00 — perfect {2,3,5}) | **DONE** |

---

## Architectural-mode hypotheses (§10–§11.6.15)

These are the *new* hypotheses about how the mechanism is *operationally configured*, articulated in the recent thread. None are in the H-battery yet because they require either (a) extending the gear DAG model with mode-state, or (b) archaeological evidence beyond computational reach.

### §10 — Missing gears as tolerance compensators

| Aspect | Status |
|---|---|
| Hypothesis | The ~39 missing gears include compensator elements that absorb manufacturing-tolerance drift |
| Probability estimate | LOW (≤15%) under §11.6.10.8's intermittent G-H1 PASS (eliminates the compensator necessity) |
| Computability | **WEAKENED**. Original premise (compensators are needed) is computationally refuted by §11.6.10.8's empirical G-H1 flip. Specific compensator topologies could still be enumerated and scored, but §10's *necessity* is gone. |
| Next compute step | Re-examine §10 conditional on continuous-operation assumption being relaxed; revisit only if §11.6.10 (clutch) is independently refuted. |

### §11.6.10 — Crank-as-clutch (global clutch hypothesis)

| Aspect | Status |
|---|---|
| Hypothesis | Inserting the crank key axially depresses a release element; mechanism only ticks during active operation |
| Probability estimate | 30–50% |
| Computability | **PARTIALLY DONE**. (a) Numerical: Track C (`f193781`) flips G-H1 PASS under intermittent operation — done. (b) Categorical: Track A (`f193781`) catalogues 4 candidate release elements with verdicts — done. (c) Archaeological: Track B (`8395311`) compiles literature dossier; falsification path identified but **DATA-BLOCKED** (requires AMRP X-ray re-examination of Fragment A around a1/b1). |
| Next compute step | Already maximally computed within available data. Further progress requires offline archaeological work. |

### §11.6.11 — Reverse-cranking for drift cancellation

| Aspect | Status |
|---|---|
| Hypothesis | Operator cranks backwards to cancel accumulated drift |
| Probability estimate | Mechanism is valid; superseded by anchor recalibration as the better strategy |
| Computability | **ANALYTIC-RESOLVED**. Worked through in §11.6.11.2/3/4: systematic + eccentricity errors cancel; backlash + random tooth-pitch noise + pin-and-slot anharmonicity do not. Anchor recalibration is strictly cheaper AND strictly more accurate. No further computation needed. |
| Next compute step | None — analytically resolved. |

### §11.6.12 — Selective lock per-subsystem (G-H6 sketch)

| Aspect | Status |
|---|---|
| Hypothesis | Per-cluster selective engagement: each subsystem has its own clutch, allowing operator to set one subsystem at a time |
| Probability estimate | Composes naturally with G-H8; treat as part of the same architecture rather than a separate hypothesis |
| Computability | **SCOPED**. Requires (a) defining a per-subsystem clutch model in `gear_topology.py` (~50 LOC); (b) for each subsystem, identifying the lock-attachment point; (c) scoring the periphery-rule consistency. |
| Next compute step | Implement `SubsystemClutch` dataclass + `clutch_attachment_evaluator()` in [gear_topology.py](../research/gear_topology.py). Score each existing subsystem (lunar, Saros, Metonic, planetary) for "where would the lock attach?" + verdict. ~75 LOC. Then add G-H6 row to consolidated_tests.py. |

### §11.6.14 — Carrier-gear hypothesis (G-H7)

| Aspect | Status |
|---|---|
| Hypothesis | Some "missing gears" are PORTABLE bronze carriers inserted by the operator through side ports to bridge gaps in the gear train |
| Probability estimate | 10–25% |
| Computability | **SCOPED but speculative**. (a) Side-port observation: through-shafts documented (consistent). (b) Carrier insertion consistency: doable — for each candidate carrier, check whether it can geometrically connect two existing surviving sub-axles. ~100 LOC. (c) Archaeological: requires unaccounted-for bronze in wreck site; **DATA-BLOCKED**. |
| Next compute step | Define a `CarrierGearElement` class + `carrier_insertion_geometry_check()` that takes (sub-axle A, sub-axle B, carrier tooth count) and computes whether axial insertion is mechanically possible given the case dimensions. Then enumerate plausible carrier topologies for each of the 5 planets under Freeth 2021. ~150 LOC. Result: a Pareto frontier of carrier topologies vs DE422 fit. **Doable today.** |

### §11.6.15 — Setting-mode gears (G-H8) — **the most testable**

| Aspect | Status |
|---|---|
| Hypothesis | Some gears are permanently mounted but kinematically active / functionally inert during normal operation, becoming load-bearing only during setting (clock-style). Specifically: synchronised-input differentials in the missing planetary plate. |
| Probability estimate | 30–50% — highest of the architectural readings |
| Computability | **WELL-SCOPED**. The headline prediction is concrete: "paired chains computing the same quantity for at least some planets, converging on a differential whose output reads zero under normal operation." This is directly testable. |
| Next compute step | (1) For each planet, enumerate alternative rational approximations to the same target ratio using `pareto_analysis.best_pq_constrained()`. Each alternative chain is a candidate "second chain" in the synchronised-input pair. (2) Score the (chain_A, chain_B) pair: do the rational approximations agree (synchronised) under normal operation? Is the differential output identically zero or near-zero? (3) Result: per-planet table of "what would a synchronised-input differential pair look like for this planet?" Compare against Freeth 2021's single-chain reconstruction. ~120 LOC. **Doable today.** |

---

## Computability summary

| Status | Count | Hypotheses |
|---|---|---|
| **DONE** | 25 of 33 | All 25 H-battery rows (A-H1..A-H4, B-H1..B-H3, C-H1..C-H2, D-H1..D-H3, E-H1a/b/c, E-H2..E-H4, F-E1..F-E3, G-H1..G-H3, H-H1..H-H2) — fully computed in `results/phase1_hypotheses.csv` |
| **PARTIALLY DONE** | 1 | §11.6.10 crank-as-clutch (numerical part done; archaeological part DATA-BLOCKED) |
| **ANALYTIC-RESOLVED** | 1 | §11.6.11 reverse-cranking (resolved without computation) |
| **CODE-READY / SCOPED** | 3 | §11.6.12 G-H6, §11.6.14 G-H7, §11.6.15 G-H8 |
| **WEAKENED** | 1 | §10 (compensator necessity refuted by §11.6.10.8's intermittent G-H1 PASS) |
| **DATA-BLOCKED** (offline archaeology) | aspects of §11.6.10, §11.6.14 | Requires AMRP X-ray re-exam, fragment surveys |

---

## Recommended next computational steps (priority order)

### Priority 1 — G-H8 paired-chain enumeration (most testable, highest probability)

For each of the 5 planets in `astronomical_cycles.CYCLES`:
1. Take the target ratio (numerator / denominator).
2. Use `pareto_analysis.best_pq_constrained()` (Track 4) to enumerate alternative rational approximations within the same prime-constraint family.
3. For each alternative, score the synchronisation residual: `|target_ratio − alt_ratio|` over the design epoch.
4. Output: per-planet table of "candidate synchronised-input differential pairs" with synchronisation residual, total bronze cost (sum of teeth), and prime-spectrum overlap with Freeth 2021's single chain.
5. **Falsification target:** if no plausible alternative chain exists for any planet within Greek bronze-cutting tolerance, G-H8's specific prediction (paired chains in missing plate) is weakened. If multiple plausible alternatives exist, G-H8 is supported.

**Estimated work: ~120 LOC, ~30 min compute. Doable today.** Result: a clear empirical signature for whether the missing-gear inventory could plausibly include paired-chain differentials.

### Priority 2 — G-H7 carrier insertion geometry

For each side-port through-shaft termination + each candidate carrier tooth count + each plausible target sub-axle:
1. Compute whether axial insertion is mechanically possible (case-depth constraint, sub-axle alignment).
2. Score against Freeth 2021's planetary-plate axle map.
3. Output: feasibility table.

**Estimated work: ~150 LOC. Doable today.** Result: shows whether G-H7's carrier reading is geometrically possible at all (could rule it out outright).

### Priority 3 — G-H6 selective-lock attachment

For each surviving subsystem (lunar, Saros, Metonic, plus hypothetical planetary):
1. Define lock-attachment-point evaluator.
2. Score each subsystem's natural lock attachment under the periphery rule.
3. Output: per-subsystem lock-design table.

**Estimated work: ~75 LOC. Quickest of the three.** Result: completes the G-H6/G-H8 composition and adds a row to the consolidated battery.

### Priority 4 — Update consolidated_tests.py with the three new G-tags

Once Priorities 1–3 land, add G-H6 / G-H7 / G-H8 evaluator functions to [consolidated_tests.py](../research/consolidated_tests.py) so they emit rows to the canonical CSV. The H-battery would grow from 26 → 29 rows.

---

## What's NOT computable from where we sit

These require offline archaeology / data acquisition:

- **§11.6.10 archaeological confirmation**: AMRP X-ray volume re-examination of Fragment A around a1/b1 for non-gear bronze release elements. Held by National Archaeological Museum Athens.
- **E-H1b proper anchor JDs**: NASA Espenak catalog re-derivation of the 6 Almagest-attributed eclipse JDs. Open data exists but requires manual cross-referencing with Toomer 1984.
- **Voulgaris 2024 paywalled paper**: would clarify what the "two missing mechanical structures on b1" actually look like.
- **Keyway depth measurement**: never published. Requires either a high-resolution Fragment A photograph or museum measurement.
- **Wreck-site bronze inventory**: complete catalogue of all bronze artefacts recovered, with classification beyond "gear" / "case-piece" — would directly test G-H7 (carrier gears).

These are real research blockers that no amount of computation can resolve. They are listed in [clutch_evidence_dossier.md](clutch_evidence_dossier.md) as "Actionable Next Steps" with URLs and museum contacts.

---

## Bottom line

**~76% of the hypotheses are fully computed** (25 of 33). Of the remaining 8:
- 1 is partially computed with the rest archaeology-dependent (§11.6.10)
- 1 is analytically resolved (§11.6.11)
- 3 are code-ready and could be computed today (G-H6, G-H7, G-H8)
- 1 is weakened to subsumed status (§10)
- The remaining 2 (§11.6.13 SVG caveat, F-series) are open or descriptive

**The single most valuable next compute step is G-H8 paired-chain enumeration** (Priority 1). It's well-scoped, has clear pass/fail criteria, and would directly test the leading architectural hypothesis from this thread. Estimated ~120 LOC, ~30 minutes compute. Result either supports or weakens G-H8 with concrete numbers.

If pursued, the H-battery grows from 26 to 29 rows (G-H6, G-H7, G-H8 added) and the architectural-mode hypotheses move from "scoped" to "tested."
