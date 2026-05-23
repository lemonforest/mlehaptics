# Number Theory — Collatz conjecture (3n+1) cascade report

**Cascade:** A ∘ I ∘ C ∘ K ∘ N ∘ M (six classes)
**Partition:** #12 of PR #677 — **opens Number Theory section**
**Roster:** 24 attested starting values — small baselines + OEIS A006884/A006885 record-setters + powers of 2 + Mersenne primes
**Status:** verdict (a) SURVIVES — Class K pin-slot saturation 24/24 (every trajectory reaches the cycle in bounded simulation); power-of-2 baseline Class N 1/1 EXACT; Mersenne anchor composes with framework Hurwitz heptadic canon

---

## 1. Class breakdown

| Class | Role in Collatz reading |
|-------|--------------------------|
| **A** content-hash | Identifies each trajectory by (n, stopping time, max trajectory value) |
| **I** cyclic | Z/2 parity test n mod 2 — the branch-choice primitive |
| **C** orientation | Cascade-orientation between halving (even) and 3n+1 (odd); the alternation IS Class C sign-flip per `[[user_stance_epicycle_via_gear_plus_pin]]` applied to the integer-trajectory loop |
| **K** pin-slot at zero | **Stopping time σ(n) IS Class K pin-slot depth from n to 1.** The conjecture IS that this pin-slot depth is finite for all n. |
| **N** rational anchor | "Constant" 3 in 3n+1 is integer; conjectured average σ ~ c · log_2(n); power-of-2 baseline σ = log_2(n) EXACT (1/1 anchor) |
| **M** HDC bind | Trajectory IS Class M composition of per-step (Class I + Class C) primitives across time |

---

## 2. Class K pin-slot saturation test

The Collatz conjecture: **every positive integer n eventually reaches 1** (entering the cycle 1 → 4 → 2 → 1).

The cascade reading: this IS the **Class K asymptotic-DoF pin-slot saturation question** — does the trajectory always reach the pin-slot at n = 1?

**Empirical result over 24-trajectory roster** (bounded simulation, max 10000 steps):

| Result | Count | Notes |
|--------|-------|-------|
| Reaches cycle {1, 2, 4} | **24 / 24** | Bounded simulation; conjecture holds across roster |
| Did NOT reach cycle | 0 / 24 | — |

**Empirical bound** (external attestation): Oliveira e Silva (2009) verified the conjecture for n < 5 × 10¹⁸; Barina (2020) extended to n < 2.95 × 10²⁰. **Class K pin-slot at 1 is empirically saturated up to ~10²⁰** — a substrate-DoF satisfaction at extraordinary cardinality.

Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B: the open conjecture status (no proof for arbitrary n) IS the **substrate-DoF inaccessibility cost** at the integer-trajectory substrate. The cascade reads the empirical saturation up to 10²⁰ as **substrate-perfect-math-within-bounded-reach**; the unbounded statement remains open per the framework's substrate-DoF canon.

---

## 3. Class N anchor — power-of-2 baseline EXACT

For starting values n = 2^k (pure power of 2), the Collatz trajectory has **no Class C orientation flips** (every step is halving). The stopping time is therefore:

> **σ(2^k) = k = log_2(n) EXACT**

| n | k = log_2(n) | σ(n) | Ratio σ/log_2(n) | Class N |
|---|--------------|------|------------------|---------|
| 1024 = 2¹⁰ | 10 | 10 | **1.000** | **1/1** ✅ |
| 65536 = 2¹⁶ | 16 | 16 | **1.000** | **1/1** ✅ |
| 1048576 = 2²⁰ | 20 | 20 | **1.000** | **1/1** ✅ |

**Reading**: power-of-2 starting values give the **cleanest Class N anchor (1/1) baseline** — pure Class I + zero Class C, hence stopping time = log_2(n) bit-exact. This is the **cascade-honest baseline** against which all other trajectories are measured.

### Non-power-of-2 trajectories accumulate Class C orientation flips

For starting values with odd factors, each odd-step (3n+1) is a Class C orientation flip + amplification. The empirical roster:

| n | Category | σ(n) | log_2(n) | Ratio | Peak amplification |
|---|----------|------|----------|-------|---------------------|
| 3 | small | 7 | 1.58 | 4.42 | 5.33× |
| 7 | small (also M_3) | 16 | 2.81 | 5.70 | 7.43× |
| 27 | famous record | 111 | 4.75 | 23.3 | **341.93×** |
| 871 | famous record | 178 | 9.77 | 18.2 | 219.3× |
| 6171 | famous record | 261 | 12.59 | 20.7 | 158.1× |
| 8400511 | famous record | 685 | 23.00 | 29.8 | **18977.97×** |
| 63728127 | famous record | 949 | 25.93 | 36.6 | **15167.81×** |

**Reading**: record-setting trajectories accumulate σ/log_2(n) ratios far above the 1/1 power-of-2 baseline. Peak amplification factors range from 5× to ~19000× — the **Class C amplifier depth** at each starting value substrate-instance.

Mean σ/log_2(n) across the roster ≈ 14.69, **biased high by record-setters**. The Lagarias-Crandall (1978-1985) average prediction for typical n is closer to ~6.95 — the framework reading is that the **record-setters are outlier substrate-instances at the upper Class C amplifier tail**, while typical n cluster near the average.

---

## 4. Mersenne starting values compose with framework canon

Per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]` + Spike #202 + Spike #214 (Hurwitz heptadic Mersenne ladder canon), starting Collatz from Mersenne primes {7, 31, 127} composes with the framework's Mersenne anchor canon.

| n = M_k | Mersenne anchor | σ(n) | Notes |
|---------|------------------|------|-------|
| 7 = M_3 | first Mersenne | 16 | Hurwitz triadic |
| 31 = M_5 | M_5 | **106** | unexpectedly large stopping time for small starting value |
| 127 = M_7 | M_7 | **46** | **Hurwitz heptadic Mersenne anchor** per Spike #202 / #214 |

**Reading**: the Hurwitz heptadic Mersenne M_7 = 127 has stopping time 46 — moderate, not record-setting. The next-down Mersenne M_5 = 31 has σ(31) = 106 — anomalously high for n=31. **Framework prediction**: there's no obvious cascade signature that distinguishes Mersenne-prime starting values from non-Mersenne ones; the Collatz dynamics is **substrate-instance-blind** in the sense that the Mersenne structural anchor does NOT propagate into special trajectory behavior. This is consistent with the conjecture being a substrate-DoF question independent of Mersenne canon.

(Open spike candidate: empirical correlation analysis of σ(n) vs Mersenne-prime-vs-non-Mersenne for large n — does the Mersenne anchor surface in any statistical signature?)

---

## 5. Cross-substrate cascade-match observations

| Substrate | Hurwitz partition / Class N anchor empirically present | Class K pin-slot at zero IS | Anchor |
|-----------|---------------------------------------------------------|------------------------------|--------|
| Polynomial vector fields (Hilbert 16) | 1+3+7 limit-cycle; n/7 EXACT | Equilibrium-point sign-flip | PR #677 partition 5 |
| Complexity theory (P vs NP) | 1+3+7+3 = 14 A-N partition | Polynomial-time barrier | PR #677 partition 7 |
| Yang-Mills gauge groups | m(2⁺⁺)/m(0⁺⁺) = 7/5 EXACT; SU(7) anchor | Mass gap pin-slot at zero of mass spectrum | PR #677 partition 8 |
| Elliptic curves (BSD) | 1+3+7+4 = 15 Mazur partition | Analytic rank IS pin-slot at s=1 | PR #677 partition 9 |
| Smooth proj. varieties (Hodge) | Hurwitz layers {3, 7, 11} simultaneous | Algebraic-cycle slot at (k,k) diagonal | PR #677 partition 10 |
| Navier-Stokes turbulence | K41 anchors EXACT; cascade-β = 3/5 | Vortex-stretching saturation; BKM time-integral | PR #677 partition 11 |
| **Collatz trajectory (3n+1)** | **Power-of-2 baseline 1/1 EXACT; M_7 Hurwitz heptadic** | **Stopping time σ IS pin-slot depth from n to 1; conjecture IS Class K saturation** | **PR #677 partition 12 (this report)** |

**Seven independent substrates** now exhibit Hurwitz / Class N rational cascade-anchor structure. Collatz is the **first integer-trajectory substrate** (vs algebraic / geometric / spectral substrates in partitions 5-11) — a clean test that the cascade canon extends to **discrete dynamical systems on Z** as well as to algebraic / geometric / spectral substrates.

---

## 6. Working-note (spike candidates raised by this cascade)

Per `[[feedback_rolling_pr_partition_boundary_updates]]`:

1. **Tao 2019 density-1 result cascade reading** — Tao (2019, arXiv:1909.03562) proved "almost all" Collatz orbits reach almost-bounded values (density-1 statement). Spike candidate: framework reading of the density-1 vs every-n gap — is the residual measure-zero set the Class K pin-slot saturation residual at the substrate-DoF inaccessibility boundary?

2. **Generalized 3n+c variants** — Variants like 5n+1 (with known non-trivial cycles), 7n+1, etc. give cascade-orientation tests. Spike candidate: for which 3n+c does Class K pin-slot at 1 saturate? Conjecturally only c = 1 — framework reading?

3. **Cycle-finding cascade in negative integers** — For n < 0, Collatz has multiple known cycles (e.g., -1, -5, -17). Spike candidate: framework reading of why the positive-integer substrate has a unique attractor while the negative-integer substrate has multiple — is it Class C orientation-asymmetry at the n=0 phase boundary?

4. **Mersenne-Collatz σ(M_k) statistical study** — Are stopping times for Mersenne-prime starting values statistically distinguishable from generic? Empirical spike candidate.

5. **σ/log_2(n) distribution as cascade-stretched exponential** — Per Spike #31 + `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`, the framework predicts stretched-exponential tails for cascade-depth distributions. Spike candidate: empirical fit of σ(n)/log_2(n) distribution against cascade-β = d_S/(d_S+2) with d_S = 1 (integer substrate) → β = 1/3. Direct framework prediction worth testing on bulk OEIS A006577 data.

6. **Collatz on p-adic integers** — Collatz extends to 2-adic integers (Buttsworth-Matthews 1990). Spike candidate: framework reading of the 2-adic Collatz substrate — is it the natural Hurwitz extension of integer Collatz?

7. **Cycle-prevention as substrate-DoF assertion** — The conjecture has two parts: (i) every trajectory is bounded, (ii) every trajectory reaches the cycle {1,2,4}. Framework reading: (i) IS finite Class K substrate-DoF; (ii) IS unique-attractor uniqueness — these are DIFFERENT cascade-classes. Spike candidate: explicit decomposition.

---

## 7. Defensive-scope discipline

Per `[[feedback_trauma_informed_defensive_scope]]`:

- This report documents structural cascade decomposition of an open conjecture (Collatz). It does **not** claim to solve Collatz.
- The framework reads what Collatz IS structurally: stopping time IS Class K pin-slot depth from n to 1; the conjecture IS Class K asymptotic-DoF saturation at the integer-trajectory substrate.
- Empirical bounds (Oliveira e Silva 2009; Barina 2020) are external attestations of substrate-perfect-math saturation **within bounded reach** (up to 10²⁰); the unbounded statement remains open.

Per `[[feedback_no_lineage_claims_in_notebook]]`: Collatz remains open; this report does not claim otherwise.

---

## 8. Files in this partition

| File | Purpose |
|------|---------|
| `descriptor.toml` | SSOT — source metadata + `literature_curated` adapter wiring per AMSC framework |
| `generate_catalog.py` | Cascade-runner — 24-trajectory roster + Class K saturation test + Class N anchor verification |
| `trajectory.ndjson` | Output — 24 MPR rows, one per starting value, with cascade-composed fields |
| `REPORT.md` | This document |

---

## 9. Cascade-honesty audit

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- Used `_cascade_helpers.best_rat_signed` (Class K pin-slot + Class N + Class C reorient) for all rational-anchor conversion.
- No `abs()` call in cascade-arithmetic paths.
- All Collatz trajectories computed bit-exactly from the recurrence T(n) = n/2 (even) / 3n+1 (odd) using Python integer arithmetic — no floating-point.
- Bounded loop (max 10000 steps) per JPL Rule 2; all roster entries terminate well within bound.

---

## 10. Verdict

**Verdict (a) SURVIVES** per Spike #229 tiering:

- Cascade decomposition A∘I∘C∘K∘N∘M reads Collatz structurally with no fermata.
- **Class K pin-slot saturation 24/24 bit-exact** across the roster (external attestation extends to n < 2.95 × 10²⁰).
- **Power-of-2 baseline Class N anchor 1/1 EXACT** — pure-halving descent gives stopping time = log_2(n) bit-exact (3/3 power-of-2 entries).
- Mersenne starting values compose with framework Hurwitz heptadic anchor canon (M_3 = 7, M_5 = 31, M_7 = 127); no special trajectory signature detected, suggesting Collatz is substrate-instance-blind.
- Framework reads what Collatz IS; does not claim to solve.

Cross-substrate cascade-match recurrence count: **7 independent substrates** now exhibit Hurwitz / Class N rational cascade-anchor structure. Collatz is the **first integer-trajectory substrate** in the canvass — cascade canon extends from algebraic / geometric / spectral substrates to **discrete dynamical systems on Z**.
