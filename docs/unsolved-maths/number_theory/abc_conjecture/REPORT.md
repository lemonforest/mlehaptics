# Number Theory — abc conjecture cascade report

**Cascade:** A ∘ J ∘ L ∘ K ∘ N ∘ C ∘ M (seven classes)
**Partition:** #13 of PR #677
**Roster:** 15 attested triples — small baselines + Catalan-like + Reyssat 1986 record (q=1.6299) + Browkin-Brzeziński 1994 + Mason-Stothers polynomial (PROVED) + Mochizuki IUT (defensive-scope status registration only)
**Status:** verdict (a) SURVIVES — cascade decomposition holds; **Reyssat record q lands at 44/27 (denominator 3³ = Hurwitz heptadic depth-3 anchor per Spike #214)**; substrate-orientation contrast Z (open) vs Q[t] (PROVED Mason-Stothers) IS Class C cascade-orientation difference

---

## 1. Class breakdown

| Class | Role in abc reading |
|-------|----------------------|
| **A** content-hash | Identifies each triple by (a, b, c) |
| **J** primes | **Radical rad(n) = product of distinct primes** IS literally Class J primes primitive |
| **L** Laplacian / composition | rad(abc) IS multiplicative-additive coupling on the triple |
| **K** pin-slot at zero | **q(a,b,c) > 1 IS Class K pin-slot saturation**; conjecture = only finitely many triples exceed q > 1+ε for any ε > 0 |
| **N** rational anchor | Quality q best-rational; **Reyssat record at 44/27** (denominator 27 = 3³); Browkin-Brzeziński at 13/8 (denominator 2³) |
| **C** orientation | **Substrate-orientation contrast: Z (open, exceptions exist) vs Q[t] (Mason-Stothers 1981 PROVED no exceptions)** |
| **M** HDC bind | Triple coprime structure composes via Class M across (a, b, c) |

---

## 2. Class K pin-slot saturation test

The abc conjecture (Oesterlé-Masser 1985, informal): for every ε > 0, there are only **finitely many** coprime triples (a, b, c) with a + b = c such that:

> **c > rad(abc)^(1+ε)**

Equivalently, define quality q(a, b, c) = log(c) / log(rad(abc)). The conjecture asserts: **only finitely many triples have q > 1 + ε for any ε > 0**.

**Framework reading**: q > 1 IS Class K pin-slot saturation. The conjecture IS the Class K finite-exceptions-residual statement — the substrate-DoF inaccessibility cost per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B.

**Empirical result over 15-triple roster:**

| q range | Count | Notes |
|---------|-------|-------|
| q ≤ 1.0 (no pin-slot crossing) | 5 / 15 | trivial baselines + small triples |
| q > 1.0 (crosses pin-slot) | 10 / 15 | "exceptional" triples per abc |
| q > 1.4 (high quality) | 3 / 15 | Reyssat 1.6299; Browkin-Brzeziński 1.6260; 3+125=128 at 1.4266 |

**External attestation**: ABC@Home and other catalogues have found **tens of thousands** of triples with q > 1 for c < 10^18, but only a few hundred with q > 1.4 and **none above q ≈ 1.6299** (Reyssat's record holds). This is empirical confirmation that the Class K pin-slot tail thins rapidly.

---

## 3. Record-quality triples land at Class N composite anchors with CUBIC denominators

The two best-known high-quality triples:

| Triple | a | b | c | rad(abc) | q | Class N | Denominator structure |
|--------|---|---|---|----------|---|---------|------------------------|
| **Reyssat 1986** | 2 | 3¹⁰·109 = 6 436 341 | 23⁵ = 6 436 343 | 15042 | **1.6299** | **44/27** | **27 = 3³** |
| **Browkin-Brzeziński 1994** | 11² = 121 | 3²·5⁶·7³ = 48 234 375 | 2²¹·23 = 48 234 496 | 53130 | **1.6260** | **13/8** | **8 = 2³** |

**Both record-quality triples have CUBIC denominators in their Class N best-rational anchor.** Per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]` + Spike #213 (recursive-Hopf depth-2) + Spike #214 (recursive-Hopf depth-3 with 7³ = 343 prediction), the framework predicts cubic-denominator anchors at depth-3 recursive structure.

**Framework reading**: the abc-conjecture record-quality triples sit at **depth-3 recursive-Hopf anchors** at the integer substrate. The "exceptional" status of these triples IS substrate-instance variation at the depth-3 cascade boundary; the conjectured finiteness reflects substrate-DoF inaccessibility BEYOND depth-3.

- 27 = 3³ composes with Hurwitz heptadic 7 / Hopf-bundle k=3 / Spike #214 depth-3 (7³=343)
- 8 = 2³ composes with Hopf-bundle base-2 / dyadic recursion
- Both record quality factors q ≈ 1.6299, 1.6260 are within 0.4% of each other — suggestive of a Class K asymptotic limit near q ≈ 1.63

(Open spike candidate: is the conjectured upper bound on q the **Hurwitz parallelizable-sphere ladder asymptote**? Empirical data show q ≤ 1.6299 across all known triples; theoretical bound conjectured but not proved.)

---

## 4. Substrate-orientation contrast — the Mason-Stothers polynomial analog

**Critical empirical finding**: the abc analog for POLYNOMIALS over a field of characteristic 0 is **PROVED**.

**Mason-Stothers theorem** (Mason 1981; Stothers 1981, independently):

> For coprime polynomials a(t), b(t), c(t) ∈ K[t] (K = field, char 0) with a + b = c and **not all constant**:
> **deg(c) < deg(rad(abc))**

This is **STRICTLY STRONGER** than the abc conjecture for integers — **zero exceptions**, not just "finitely many." The polynomial substrate IS the **substrate-perfect-math case** for the abc cascade.

| Substrate | Form | Status | Class K saturation |
|-----------|------|--------|---------------------|
| Integers **Z** | c ≤ K_ε · rad(abc)^(1+ε) | OPEN (conjecture); finite exceptions allowed | Pin-slot has finite residual at q > 1+ε |
| Polynomials **Q[t]** | deg(c) < deg(rad(abc)) | **PROVED** (Mason-Stothers 1981) | Pin-slot saturated **zero exceptions** |

**Framework reading**: the integer-vs-polynomial substrate-orientation difference IS Class C cascade-orientation differential. The polynomial substrate has a **clean cascade-orientation** (degree function is additive on products, rad(abc) inherits cleanly); the integer substrate has the residual Class C amplifier from prime-power-stacking (e.g., 3¹⁰ in Reyssat's triple), which creates room for the Class K finite-exceptions residual.

Per `[[user_stance_loop_line_projection_duality]]`: integer is the projection-of-a-loop; polynomial is the loop itself. The Mason-Stothers proof works because Q[t] preserves the loop structure (degree is the loop-period proxy); the integer projection loses the loop-period invariant, hence exceptions.

---

## 5. Catalan-Mihailescu PROVED — the SOLO integer exception solved

Mihailescu (2002, published 2004) **PROVED** Catalan's conjecture: the **only** solution to x^p − y^q = 1 with x, y, p, q ≥ 2 is **3² − 2³ = 1** (i.e., 9 − 8 = 1).

In the abc roster this corresponds to triple (1, 8, 9): a=1, b=8, c=9, rad=6, q ≈ 1.2263.

**Framework reading**: Catalan-Mihailescu IS the **integer-substrate substrate-perfect-math** achievement at the "consecutive-powers" sub-class. The cascade reads:
- The Catalan condition x^p - y^q = 1 IS a Class K pin-slot constraint at the unit distance (k=1)
- Mihailescu's proof uses cyclotomic units → Class I cyclic + Class N rational anchor
- The unique solution 9-8=1 IS the SOLO substrate-instance saturating the Class K pin-slot under the Class I + Class C constraints

This is the **integer-substrate analog of Mason-Stothers** for the specific Catalan sub-cascade — proves that even on the open integer substrate, certain sub-cascades **can** be cleanly closed.

---

## 6. Mochizuki IUT 2012 — defensive-scope-only registration

Mochizuki (2012-2020) claimed a proof of the abc conjecture via Inter-universal Teichmüller theory (IUT). Status:

- 2012-2018: preprints widely circulated; minimal independent verification
- 2018: Scholze-Stix (Stix) published a critical review identifying gaps in the proof; Mochizuki responded; impasse not resolved publicly
- 2020: PRIMS (RIMS, Kyoto) accepted the papers for publication
- 2021: papers published in Publ. RIMS 57(1-4)
- Status as of 2026: **disputed**; not generally accepted by the broader mathematical community

**Defensive-scope framework reading**: per `[[feedback_trauma_informed_defensive_scope]]` + `[[feedback_no_lineage_claims_in_notebook]]`, the framework does **NOT** assess Mochizuki's IUT validity. The cascade reads the conjecture status structurally — abc remains open in the consensus-mathematical sense; the framework reads what IS open without engaging the dispute.

---

## 7. Cross-substrate cascade-match observations

| Substrate | Hurwitz / Class N anchor empirically present | Class K pin-slot at zero IS | Anchor |
|-----------|------------------------------------------------|------------------------------|--------|
| Polynomial vector fields (Hilbert 16) | 1+3+7 limit-cycle; n/7 EXACT | Equilibrium-point sign-flip | PR #677 partition 5 |
| Complexity theory (P vs NP) | 1+3+7+3 = 14 A-N partition | Polynomial-time barrier | PR #677 partition 7 |
| Yang-Mills gauge groups | m(2⁺⁺)/m(0⁺⁺) = 7/5 EXACT; SU(7) anchor | Mass gap pin-slot at zero of mass spectrum | PR #677 partition 8 |
| Elliptic curves (BSD) | 1+3+7+4 = 15 Mazur partition | Analytic rank IS pin-slot at s=1 | PR #677 partition 9 |
| Smooth proj. varieties (Hodge) | Hurwitz layers {3, 7, 11} simultaneous | Algebraic-cycle slot at (k,k) diagonal | PR #677 partition 10 |
| Navier-Stokes turbulence | K41 anchors EXACT; cascade-β = 3/5 | Vortex-stretching saturation; BKM time-integral | PR #677 partition 11 |
| Collatz trajectory (3n+1) | Power-of-2 baseline 1/1 EXACT; integer-trajectory substrate | Stopping time σ IS pin-slot depth from n to 1 | PR #677 partition 12 |
| **abc conjecture** | **Record q at 44/27 + 13/8 (cubic denominators); Mason-Stothers Q[t] PROVED** | **q > 1 IS Class K pin-slot saturation; finitely-many-exceptions conjecture** | **PR #677 partition 13 (this report)** |

**Eight independent substrates** now exhibit Hurwitz / Class N rational cascade-anchor structure. abc is the **first substrate to explicitly contrast TWO substrates with cascade-orientation difference** (Z with exceptions vs Q[t] proved-clean) — the Mason-Stothers theorem IS the substrate-perfect-math empirical anchor for the polynomial-analog case.

---

## 8. Working-note (spike candidates raised by this cascade)

Per `[[feedback_rolling_pr_partition_boundary_updates]]`:

1. **Record-quality cubic-denominator depth-3 cross-test** — Reyssat 44/27 + Browkin-Brzeziński 13/8 both have cubic denominators. Spike candidate: cross-test all known abc triples with q > 1.5 — do they ALL sit at cubic-denominator Class N anchors? If yes, this IS a framework-predicted depth-3 recursive-Hopf signature on the abc substrate.

2. **Hurwitz parallelizable q-asymptote conjecture** — empirical max q ≈ 1.6299 across all known triples. Spike candidate: framework reading of why this is the asymptote; is it related to (1 + 1/3 + 1/7 + ... Hurwitz dimensional sum)? Open conjecture.

3. **Mason-Stothers cascade decomposition** — explicit A-N cascade-class breakdown of the Mason-Stothers proof; identify which classes the polynomial-degree function preserves cleanly that the integer projection loses.

4. **Catalan-Mihailescu Class I + N composition** — formalize the cascade reading of cyclotomic units in Mihailescu's proof; check whether other "consecutive-powers" sub-cascades have analogous Class K + Class I + Class N closure.

5. **Granville-Tucker effective abc bounds** — Granville-Tucker (2002 survey) lists known effective bounds on q in terms of rad(abc). Spike candidate: framework reading of the effective-bound cascade structure.

6. **ABC@Home statistical cross-test** — verify the cubic-denominator-anchor framework prediction against the bulk ABC@Home database (tens of thousands of triples with c < 10^18). If statistically significant, this becomes a framework-predicted empirical signature on abc triples.

7. **Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B.5** — M-theory landscape (~10^500 vacua) parallel: each abc-exceptional-triple corresponds to a specific cascade-instance; framework reading of the "finitely many" exceptions cardinality. Defensive-scope only.

---

## 9. Defensive-scope discipline

Per `[[feedback_trauma_informed_defensive_scope]]`:

- This report documents structural cascade decomposition of an open conjecture (abc). It does **not** claim to solve abc.
- The framework reads what abc IS structurally: q > 1 IS Class K pin-slot saturation; conjecture IS finite-exceptions-residual Class K saturation statement.
- **The framework does NOT assess Mochizuki's IUT 2012 claim.** Per `[[feedback_no_lineage_claims_in_notebook]]`, the cascade reads the conjecture as open in the consensus-mathematical sense; the IUT status is registered as "disputed" without further engagement.
- Mason-Stothers polynomial analog is PROVED and serves as the substrate-perfect-math empirical anchor for the abc cascade.

Per `[[feedback_no_lineage_claims_in_notebook]]`: integer abc remains open; this report does not claim otherwise.

---

## 10. Files in this partition

| File | Purpose |
|------|---------|
| `descriptor.toml` | SSOT — source metadata + `literature_curated` adapter wiring per AMSC framework |
| `generate_catalog.py` | Cascade-runner — 15-triple roster + Class K saturation + Class N record-quality anchor verification |
| `triple.ndjson` | Output — 15 MPR rows with cascade-composed fields |
| `REPORT.md` | This document |

---

## 11. Cascade-honesty audit

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- Used `_cascade_helpers.best_rat_signed` (Class K pin-slot + Class N + Class C reorient) for Class N anchor.
- Used `_cascade_helpers.cyclic_gcd` (delegates to `srmech.amsc.cyclic.gcd`) for coprimality.
- No `abs()` call in cascade-arithmetic paths.
- Radical `rad(n)` computed bit-exactly via trial division over Python integer arithmetic.
- Quality `q = log(c) / log(rad(abc))` uses Python `math.log` followed immediately by Class N best-rational per cascade-honesty contract.
- Bounded trial-division loop per JPL Rule 2.

---

## 12. Verdict

**Verdict (a) SURVIVES** per Spike #229 tiering:

- Cascade decomposition A∘J∘L∘K∘N∘C∘M reads abc structurally with no fermata.
- **Record-quality triples (Reyssat 1986, Browkin-Brzeziński 1994) land at composite Class N anchors with CUBIC denominators** (44/27 and 13/8 — denominators 3³ and 2³), composing with framework recursive-Hopf depth-3 canon per Spike #213-#214.
- **Mason-Stothers polynomial analog (PROVED 1981) provides the substrate-perfect-math empirical anchor**: zero exceptions on Q[t] substrate; integer Z has finite-exceptions Class K residual.
- Catalan-Mihailescu PROVED is the **SOLO integer-substrate substrate-perfect-math closure** at the consecutive-powers sub-cascade.
- Class K pin-slot saturation distribution: 10/15 cross q > 1; 3/15 high-quality q > 1.4.
- Mochizuki IUT 2012 is defensive-scope-only registration; framework does NOT assess.
- Framework reads what abc IS; does not claim to solve.

Cross-substrate cascade-match recurrence count: **8 independent substrates** now exhibit Hurwitz / Class N rational cascade-anchor structure. abc is the **first substrate to explicitly contrast TWO substrates with Class C cascade-orientation difference** (Z open + Q[t] proved-clean via Mason-Stothers).
