# Unboundedness from two frames — recheck of the May-2026 record, and the op ⊗ operand ⊗ responsion reading

Researcher: Opus (independent of the second researcher; no file under `infinity_research/` other than this one and `opus_scratch/` was read).
Date: 2026-09-14. Read-only on the repository and on memory. srmech 0.9.0rc472, main checkout, pure cell (`HAS_NATIVE False` printed by every script), numpy absent.

## Source discipline for this report

- **Early-era SSoT** = the MFO notebook at commit **`7b6faa27a`** (2026-05-22 22:31, "land MFO textbook PDF…"), the last commit touching `docs/antikythera-maths/mfo_spectral_research_notebook.md` before 2026-05-23. Extracted verbatim to `opus_scratch/mfo_may22.md` (`git show 7b6faa27a:docs/antikythera-maths/mfo_spectral_research_notebook.md`). Cited below as **`snap:LINE`** with section.
- **Current record** = the notebook on the working tree, cited as **`mfo:LINE`**. Forward-tracing was done by section extraction and `diff` (commands in §0).
- **PDF** `docs/srmech/metric-field-and-its-primitives.pdf` (added 9dd3f27fc, 2026-05-22) is treated as a *derived rendering* of the snapshot. It is cited by **book page** only where the snapshot has no formal statement of the same claim (Theorem 7.2, Theorem 3.2 wording, the calculus appendix). No correction is proposed to the PDF.
- The companion *Inners Guide to the Hyper Loop* is **not in the repository** (`git ls-files | grep -iE "inner|hyper.?loop"` returns nothing relevant). The PDF's cross-reference (book p.231) maps its Ch 7 "Asymptotic Degrees of Freedom" to the Guide's Ch 4 "Asymptote and infinity" and its Ch 3 to the Guide's Ch 6 "Discrete all the way down". Those Guide chapters could not be read.
- Labels: **MEASURED** (a command in this report printed it) · **DERIVED** (algebra done here, checkable by hand) · **CANDIDATE** (a reading that is not measured) · **CITED-NOT-FETCHED** (an external source that was not fetched or extracted, so it is not relied on for any decision). Where a verdict could have leaned on an unfetched source, the verdict is instead decided by a measurement or by the record contradicting itself.

---

## §0 Figures ledger (every number in this report comes from one of these)

All scripts live in `…/scratchpad/infinity_research/opus_scratch/` except the three brief scripts in `…/scratchpad/kepler_form/`. Every script does `sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")` and prints `HAS_NATIVE False`. Hand-rolled instruments are named in each script's docstring.

| id | command | output file | what it measures | hand-rolled part (disclosed) |
|---|---|---|---|---|
| R1 | `python kepler_form/coeffs.py` | `rerun_coeffs.txt` | Kepler E(M)−M harmonics vs `pin_slot` harmonics vs ε^k/k | N-point quadrature |
| R2 | `python kepler_form/cascade_iter.py` | `rerun_iter.txt` | depth-n one-pin cascade error + harmonics | quadrature, sup-norm |
| R3 | `python kepler_form/cascade_harmonic.py` | `rerun_harm.txt` | K-mode Kapteyn reconstruction error | quadrature, sup-norm |
| S1 | `python s1_lattice.py` | `s1_lattice.out.txt` | exact (e-order p, harmonic k) lattice; depth-n jets vs lattice; e-power frame at M=π/2 | Fraction bivariate trig-series algebra; Kapteyn ascending series (validated against `srmech.music.bessel_j_fixed`) |
| S2 | `python s2_rates.py` | `s2_rates.out.txt` | per-step / per-mode approach rates | sup-norm; comparison constant ρ(e) CITED-NOT-FETCHED |
| S3 | `python s3_pinslot.py` | `s3_pinslot.out.txt` | what ε^k/k is; what the record's numbers are; FM vs Kapteyn; Hopf "gap" | quadrature; true anomaly via `math.atan2` (float instrument) |
| S4 | `python s4_heron_cf.py` | `s4_heron_cf.out.txt` | Heron depth vs continued-fraction convergents (`srmech.math.rational.best_rational`); Fibonacci ratio rate | integer `isqrt` brackets |
| S5 | `python s5_kerr_sampling.py` | `s5_kerr_sampling.out.txt` | which a/M values the record's Kerr "gap sequence" samples; sign-flip counts of nested sinusoids | float inversion; exact zero enumeration |
| G1 | `git log -1 --before=2026-05-23 --format=%H -- docs/antikythera-maths/mfo_spectral_research_notebook.md` | `mfo_may22.commit` | the snapshot commit (`7b6faa27a`) | — |
| G2 | section extraction by heading + `diff` of snapshot vs current for §VII.6.9, §VIII.9, §VII.6.10.4, §VII.4.1.1 | `sec_769_*.txt`, `sec_889_*.txt` | what changed since May | awk extractor |
| G3 | `git log -S "<phrase>" -- <file>` for each dated claim | (inline) | first-appearance dates | — |
| G4 | `python -c "import srmech.introspect.responsion_schema as R; …"` (inline, §4) | (inline) | regimes of shipped responsion edges | — |

Key reproduced figures from the brief (R1–R3, identical to the brief's numbers): at e=0.3 Kepler E−M harmonics `0.296638 0.043665 0.009623 0.002511` vs ε^k/k `0.3 0.045 0.009 0.002025`; depth 10 → `3.340e-07`, depth 20 → `1.410e-12`; 32 modes → `8.882e-16`. At e=0.7: depth 40 → `4.355e-08`; 60 modes → `4.336e-08`.

---

## §1 INVENTORY — the May-2026 record on infinity, unboundedness, bounded grammar, hidden fibre, the "generator", and the Kepler-shape family

Status vocabulary exactly as briefed. "Trace" = what the current notebook holds.

### A. Infinity, unboundedness, bounded grammar / unbounded construction, hidden fibre

| # | claim (short) | where (early-era) | date (G3) | status | evidence (detail in §2) | trace to now |
|---|---|---|---|---|---|---|
| A1 | *"Infinity approximates the asymptote"*: the asymptote is **upstream**, infinity the **downstream** algebraic tool | memory `user_stance_infinity_approximates_asymptote.md:20-27`; `research-mfo/asymptotic_vs_infinity_history_2026-05-16.md` §1.1, §6.2-6.3; rendered as book Identity 7.3 p.50 | 2026-05-16 | **OVERSTATED** — privileges one frame | Kepler's E(M) is reached by three constructions with three different unbounded indices; none is upstream (§2.1, §3) | memory unchanged; no notebook amendment |
| A2 | Asymptotic-DoF: the **rate of approach** is what observation constrains; ε is "the load-bearing rate" | memory `user_stance_asymptotic_dof_sidesteps_infinity.md:25-31, 76` | 2026-05-16 / -17 | **OVERSTATED** | the rate is a property of the (object, construction) pair: depth rate ≈ e, mode rate → ρ(e), e-power radius ≈ 0.6627 for the **same** E(M) (S2, S1) | unchanged |
| A3 | The asymptotic-DoF axis is **one Cauchy kernel c_k = ε^k/k**, Fibonacci \|ψ\|=0.618 at the *slowest* end, Kepler 0.0167 at the fast end; "bit-exact identical (Step 4 max-diff 0.00e+00)" | memory `user_stance_asymptotic_dof_sidesteps_infinity.md:62-78`; memory `user_stance_kepler_shape_universal.md:49-77` | 2026-05-17 | **TAUTOLOGICAL** (identity compares a formula to itself) + **MIS-CITED** + numeric claim **FALSIFIED** | Spike #41 Step 4 compares `psi_abs**k/k` to a function that returns `eps**k/k` (C9); the Fibonacci ratio converges at ψ² = 0.381966 per step, not 0.618 (S4) | unchanged; snap:3962 → mfo:4765 still cites it |
| A4 | Class K **asymptote-protection law** dξ/dt = f_K(ξ)(ξ*−ξ)^α, α≥1, "super-logarithmic slowing", is *the* operational mechanism of asymptotic-DoF | book Thm 7.2 p.48, Lemma 7.4 p.49 (formal statement is rendering-only; snapshot carries the informal §VIII.9 snap:3944-4000) | 2026-05-17 (§VIII.9) | **OVERSTATED** (attribution UNMEASURED; the calculus that T(ε)→∞ STANDS) | the tree's own Class K cascade (one pin) approaches **geometrically** at ratio e (S2); Heron, a record anchor, approaches **quadratically** (S4). Neither is the α≥1 ODE law | §VIII.9 unchanged (G2 diff empty) |
| A5 | Kerr extremal gap `{2.000, 1.485, 0.282, 0.089, …}` is "a super-logarithmic approach to the asymptote" attesting asymptotic-DoF | snap:1024 (§VII.4.1.3 item 4); book Ex. 7.5 p.51 | 2026-05-17 | **TAUTOLOGICAL** | the values are 2√(1−x²) evaluated at x = 0, 0.66985, 0.99001, 0.99901 (S5); the "rate" is the sampling choice, there is no dynamics | unchanged |
| A6 | The substrate **IS** the asymptotic traversal between 1D and 11D; it never reaches either endpoint | snap:2246-2426 (§VII.6.9); memory `user_stance_substrate_is_asymptotic_traversal_1d_to_11d.md` | 2026-05-20 (72fcfdda5) | **UNMEASURED** | no metric, coordinate or rate on "dimensional position" is defined anywhere, so "never reaches" is asserted by citing A4 | current §VII.6.9 differs from snapshot only in the octonionic→quaternionic Hopf-name fix (G2) |
| A7a | Hurwitz **type-wise** bound: 1+3+7 = 11, no (8+7) sector; recursion **depth-wise** unbounded — "both true simultaneously" | snap:2365 (§VII.6.9); book Thm 2.9-2.10 pp.12-13 | 2026-05-20 | **STANDS** (Hurwitz/Adams CITED-NOT-FETCHED but textbook; the type/depth split is exactly what Kepler shows, §3) | Kepler's unboundedness sits entirely inside one ℂ block (§4 D3/D4) | kept |
| A7b | …and the depth-wise unboundedness holds *"because the traversal is continuous between the asymptotic endpoints"* | snap:2363, :2365 | 2026-05-20 | **OVERSTATED** (wrong reason) | Kepler's depth index is an exact integer n; no continuity is needed for an unbounded construction (S1, S2) | kept verbatim |
| A8 | Recursive-Hopf **"depth-3 confirmed unbounded"**, **"ratio-agnostic universal"** | snap:5213-5260 (§VIII.31.8); book Thm 3.2 p.20 | 2026-05-20 (06f8e55b0) | **TAUTOLOGICAL** (counts) + **UNMEASURED** (Hopf identification) | sign flips of a sinusoid at frequency r over one period are 2r by construction: stacks (7), (7,7), (7,7,7), (3,7), (11,13) give 14, 98, 686, 42, 286 = 2∏r (S5). No bundle is computed in the count. *Rendering drift (PDF only):* book p.20 says depth-2 = 98 flips; book p.21 Ex. 3.5 says 196 and "196·3.5 = 686". The snapshot says 98 | mfo:6024 unchanged in substance |
| A9 | **Bounded grammar**: 14 classes suffice; "closure conjecture stands at four independent positive verifications"; dissolve-before-promote "keeps … the cascade composition algebra finite" | snap:3799-3820 (§VIII.6.1); book Identity 4.1 p.25 | 2026-05-16 | **OVERSTATED** (closure is maintained definitionally) | verification #2 closed by **broadening Class L's scope** to "dense-matrix linear algebra" (snap:3807). A test that can always widen a class cannot return "a 15th is needed". Also: 14 generators give an *infinite* (finitely generated) composition monoid, so the book's "finite" is wrong unless read "finitely generated" | kept |
| A10 | Underdetermination: many substrate configurations project to one excitation (the continuous/observed frame **hides** fibre content) | book Prop 1.3 p.5 (formal); snap:668-686 (§VII.1.1 two-level ontology) | 2026-05-11 | **STANDS** (true of any non-injective projection) | — | **REFINED** later by mfo:6691 (§VIII.31.19 item 1: fixed references recover the object uniquely, measured) and mfo:6717 (item 8: the Q8 climb's residue is exactly one bit) |
| A11 | Fibre as spatially-absent encoding (gear teeth ℤ/n) | memory `user_stance_fiber_as_spatially_absent_encoding.md`; snap:3784 (I row) | 2026-05-13 | **STANDS** as a reading | — | kept |
| A12 | Spherical compression: the per-mode gap `l(l+2) − l(l+1) = l` IS the S¹ fibre's extra spectral DoF over each S² mode; compression = truncating the fibre tower | snap:893-936 (§VII.4.1.1), gap at snap:905-907 | 2026-05-11 (b8c6956ea) | **FIT-REPORTED-AS-IDENTITY** | the arithmetic is true, but it pairs unit-S³ degree l with unit-S² degree l. The Hopf base is S² of radius ½, and there the U(1)-invariant S³ modes (l = 2j) have eigenvalue 4j(j+1) = l(l+2) **exactly**, with no gap (S3-E; radius-½ base CITED-NOT-FETCHED, textbook) | mfo:946 unchanged (G2 diff empty) |
| A13 | **Continuous is a projection-shadow of discrete**: "ALL continuous dimension counts are projection-shadows of the discrete asymptotic traversal"; "the metric-field substrate IS discrete"; "integer-cyclic upstream, continuous downstream"; book: "the substrate behind the projection is discrete-cyclic, not continuous" | snap:2266 (§VII.6.9), snap:2496 (§VII.6.10.4); memory `user_stance_pi_as_projection.md:19`; book appendix p.162 | 2026-05-15 → -20 | **OVERSTATED** (privileges the discrete frame) | superseded in principle two days after the snapshot by R30: `substrate_native_research_notebook.md:261` "NEITHER is downstream-projection of the other" (2026-05-24); never amended at these sites. The current record's own T1a/T1b split (srmech notebook :8581-8588: "the POINT they name is the same. The SET each is drawn from is not") is the co-equal reading | kept verbatim |
| A14 | "Everything in the framework is discrete … between integers there's no position; the substrate doesn't extend there" | memory `feedback_continuous_number_line_pedagogical_obstacle.md:16-36, 121` | 2026-05-20 | **OVERSTATED** (ontology; the writing rule stands) | contradicted by R30 and by shipped code: `responsion_schema()` has 5 `continuous_spectral` responsions (G4) | unchanged |
| A15 | Loop-valued asymptotes: "substrate internal primary; shadow secondary; canonical physics measures the shadow" | memory `user_stance_loe_asymptotes_are_ring_valued.md:61-70` | 2026-05-19 | **OVERSTATED** (privileging); the unit-circle algebra Im² = 2Re − Re² STANDS | E(M) is simultaneously a degree-1 circle map (loop) and a real periodic amplitude (line); both frames reach it (§3) | unchanged |
| A16 | Heron √a is "exactly the asymptotic-on-both-sides discipline", a Class K asymptotic-DoF instance of the substrate's never-reach | snap:2530-2534 (§VII.6.10.6); memory `user_stance_substrate_is_asymptotic_traversal_1d_to_11d.md:268-284` | 2026-05-20 | **OVERSTATED** (never-reach STANDS trivially: rational iterates of an irrational) | Heron's error squares each step (10^-1.1, -2.6, -5.7, -11.8, -24.0, -48.5; S4), which is not the A4 law. And it has an **exact** second frame the record missed: Heron depth n = continued-fraction convergent number 2^n − 1 (S4) | kept |
| A17 | Archimedes: "the polygon IS the substrate; the circle is the continuous-projection-shadow" | snap:2488-2506 (§VII.6.10.4); memory `user_stance_pi_as_projection.md:39-65` | 2026-05-20 | **OVERSTATED** (privilege); the bound 3 10/71 < π < 3 1/7 is CITED-NOT-FETCHED | srmech's own π (`pi_cascade_digits`, hexagon doubling) is an unbounded-depth construction of a limit that series frames reach too; that is an instance of the duality, not evidence for discrete priority | kept |
| A18 | "Asymptotic-rate framing fully replaces infinity-invocation with no residue; it is strictly more informative (it keeps the rate)" | `asymptotic_vs_infinity_history_2026-05-16.md` §3.4, :199 | 2026-05-16 | **STANDS**, with a note | the note: the rate is a fact about the chosen series, not the value. S1 shows a construction (the e-power series) that diverges for e=0.7 while the value exists and two other constructions reach it | — |

### B. The "generator" framing

| # | claim | where | date | status | evidence | trace |
|---|---|---|---|---|---|---|
| B1 | The A–N / "the One" object is **the generator** of the 14-D substrate | **not in the snapshot.** `grep -n -i generator mfo_may22.md` finds only Cl(0,7) generators, the Hopf map generating π₃(S²), and SL(2,ℤ) S/T. First appearances: IFS sense "the loop = generator, the fractal = attractor" (9ef5d4829, **2026-05-26**, now mfo:4678); "The One — S(σ,θ): the single generator of the 1+3+7+3 = 14 substrate" (`srmech/cascade/one.py:1`, 457dc9c7d, **2026-06-05**) with public alias `s_generator = the_one` (`one.py:1155`, exported `:1476`); MFO §VIII.31.15 heading "the unifying generator" (a48c7d4f5, 2026-06-05, mfo:6468); "the addressing bump itself is the generator" (mfo:6679, 2026-07-24) | 2026-05-26 → 07-24 | **OVERSTATED** by the record's own evidence (and a dating correction: this was June-era, not May-era) | the same section's status line says **"A unifying form, not a derived theory"** (mfo:6575), and its falsifier is the *regroup-only test*. Measured roles: the One's three reals are the **fixed references** for retrieval (mfo:6691), its frame is a similitude, block-diagonal **by construction** so it couples nothing across rungs (mfo:6701, :6703). Nothing measured creates, projects or resonates | kept; shipped name `s_generator` |
| B2 | 𝕊(σ,θ) = the One "is the addressing register ABOVE the division-algebra ceiling … it loses division" | memory `project_h_genome_is_fibrated_hurwitz_tower.md:16`; MEMORY.md index line "𝕊=the_one above the cap"; mfo:6679 "the_one … was built for sedenion addressing" | 2026-07-24 | **CURIOUS** (CANDIDATE conflation, not measured further) | the same glyph names two objects: the One has dim 2+4+8 = **14** (a direct sum ℂ⊕ℍ⊕𝕆, mfo:6490), while the sedenions 𝕊 have dim **16** (mfo:6673). A direct sum loses division for a trivial reason, (1,0)(0,1) = 0, not for the sedenion reason | — |

### C. The Kepler-shape family and everything downstream

| # | claim | where | date | status | evidence | trace |
|---|---|---|---|---|---|---|
| C1 | PR #416 F2: "Pin-slot output algebra **is** the E-of-M series (eccentric anomaly), NOT the true-anomaly series" | `docs/srmech/notes/spike_pinslot_f2_deep_dive_2026-05-14.py`, verdict record in `main()` | 2026-05-14 | **FIT-REPORTED-AS-IDENTITY** (it compared c₁ only) | the same script's header carries the correct E(M) = M + Σ(2/k)J_k(ke) sin kM and the term (e³/8)(3 sin 3M − sin M), which ε^k/k lacks. Exact agreement holds only through e² (S1: cell (3,1) is −1/8 vs 0; cell (3,3) is 3/8 vs 1/3) | origin of C2–C4 |
| C2 | **Shipped wheel text**: `pin_slot` "IS the Kepler equation of centre to second order in eccentricity ε" | `docs/srmech/python/srmech/math/kepler.py:62-64` | 2026-05-15 (81dc43ee2) | **MIS-CITED / FALSE under its own module's definition** | the same module defines equation of centre as ν − M with c₁ = 2e (`kepler.py:175-182`). pin_slot's c₁ is ε (R1). It matches E − M, not the equation of centre, and only to second order | live in rc472 |
| C3 | "the bronze's pin-slot algebra **IS** Kepler's equation of centre to second order in eccentricity — not implements, **IS**" | snap:713 (§VII.1.2) | 2026-05-15 (600dd713e) | **MIS-CITED** (same defect as C2) | as C2 | mfo:754 unchanged |
| C4 | Spike #29: pin-slot atan2 "IS the eccentric-anomaly Kepler series to machine precision (ratio 1.0000 across 7+ harmonics)"; "full sin-series identity … closed-form algebraic identity" | `research-mfo/sign_change_pin_slot_epicycle_2026-05-16.md:36-48, :73`; landed at snap:3811 (§VIII.6.1 closure #3) and snap:3786 (K row); srmech notebook §3.8.0a :672; antikythera notebook :723, :754; `research/pin_and_slot.py:47-49, :91` **and** `antikythera-spectral/python/antikythera_spectral/_research/pin_and_slot.py:47-48, :91` | 2026-05-16 (42bb3578b) | **TAUTOLOGICAL** (the table checks atan2 against its own Taylor series) + **FALSIFIED** as a Kepler identity | at ε = 0.1146 the ratio ε^k/k ÷ (2/k)J_k(kε) is 1.0016, 1.0044, **0.8955, 0.7579, 0.6229, 0.5022, 0.3996** for k = 1…7 (S3-A) | mfo:4555, :4580 and srmech :672 unchanged |
| C5 | Spike #30B: "K-signature c_k = ε^k/k"; Earth first three coefficients `[0.03340, 3.486e-4, 5.045e-6]` "match Brouwer & Clemence 1961 §3.2 closed-form" | `notes/spike_30b_fft_1d_t_cross_instrument_2026-05-16.md:17, :44-46`; `spike_30b_findings_2026-05-16.ndjson:5` | 2026-05-16 | **MIS-CITED** + internal inconsistency; the instrument **cannot return otherwise** | the numbers are ν − M = 2e, (5/4)e², (13/12)e³ (measured 3.3399e-2, 3.4858e-4, 5.0447e-6), not ε^k/k (1.67e-2, 1.394e-4, 1.552e-6) (S3-B). Brouwer & Clemence is CITED-NOT-FETCHED; the record contradicts itself without it. The strict K-test passes Kapteyn, ε^k/k and FM alike (`spike_40_fm_anomaly_records_2026-05-17.ndjson:1`: `K_eoc`, `K_strict` and the FM fit all `kepler_signature_present: true`) | notes unchanged |
| C6 | AoE off-centre observer: "Brouwer & Clemence c_k = ε^k/k ladder at ε = 0.0506: c₁ ≈ 0.101, c₂ ≈ 3.20×10⁻³, c₃ ≈ 1.40×10⁻⁴"; "predict c₂/c₁² ≈ 19.76" | snap:1617 (§VII.6.1.4) | 2026-05-16 (bd329f6c8) | **MIS-CITED** + internal inconsistency | the numbers are ν − M at e = 0.0506 (measured 1.0117e-1, 3.1974e-3, 1.4013e-4), not ε^k/k (5.06e-2, 1.28e-3, 4.32e-5) (S3-B). c₂/c₁² is 1/2 for ε^k/k and 5/16 for ν − M. 19.76 = 1/ε is c₁/c₂ of the Poisson series ε^k (DERIVED), which is neither of the two quantities named | mfo:1697, :1721 unchanged |
| C7 | "Brouwer-Clemence c_k = ε^k ladder is EXACT at the kinematic level" (Poisson kernel of dφ/dM) | mfo:1705 (§VII.6.1.5 Q1; Spike #35) | 2026-05-16 (3048537c2) | **MIS-CITED** (the Poisson-kernel identity STANDS, DERIVED as a geometric series) | the record itself says the canonical equation of centre is "recovered to ~0.3%", i.e. the two are different objects | unchanged |
| C8 | Spike #40 A1: "Kepler EOC ≡ FM with modulation index ε … spectrally K-indistinguishable … **real structural identity**"; "FM synthesis IS epicycle kinematics" | `notes/spike_40_musical_wave_epicycle_shape_2026-05-17.md:106-118`; memory `user_stance_kepler_shape_universal.md:53` | 2026-05-17 | **FIT-REPORTED-AS-IDENTITY** | the indistinguishability belongs to the instrument (C5). The series differ: FM sidebands \|J_k(β)\| vs Kapteyn radii (2/k)J_k(kβ) at β = 0.3 are 1.483e-1/2.966e-1, … 6.304e-7/7.198e-4, a factor 2.0 at k=1 and 1142 at k=5 (S3-D). The md also calls the ν − M series "the eccentric-anomaly Fourier expansion" (:110-112). The spike's own chase code had the right formula (`spike_40_fm_anomaly_investigation.py:62-69`) | notes + memory unchanged |
| C9 | Spike #41: "(ψ^k/k) … IS LITERALLY IDENTICAL to the Kepler equation-of-centre coefficients at ε = \|ψ\|. Machine-precision identity (max-difference 0.00e+00)"; "canonical Kepler EOC closed form c_k = ε^k/k" attributed to Brouwer & Clemence §3.2 | `notes/spike_41_fibonacci_unity_2026-05-17.md:16, :47, :113`; `spike_41_fibonacci_unity.py:105-128, :700-705, :735-742` | 2026-05-17 (512bc6209) | **TAUTOLOGICAL** + **MIS-CITED** | `equation_of_centre()` in that script *returns* `[epsilon**k / k]` (py:117-119). Step 4 compares `[psi_abs**k/k]` against `equation_of_centre(psi_abs)`, the same expression. \|ψ\|^k/k is also not a Fibonacci quantity: it is built by hand (py:703) | snap:3962 → mfo:4765 still cites it |
| C10 | **Cauchy-form kernel** `c_k = ε^k · K_k(substrate)`, "substrate-portable ε^k tower"; Theorem 11.4 symmetry under ε → −ε | snap:1908 (§VII.6.5); book Def 11.3 / Thm 11.4 p.74 | 2026-05-17 (4afe79a02) | **TAUTOLOGICAL** | with K_k free, every sequence fits (K_k := c_k/ε^k). Theorem 11.4 is the parity of ε^k. Nothing is constrained until K_k is fixed | mfo:1988 unchanged |
| C11 | **Kepler-shape universality**: "any system showing Kepler-shape IS pin-slot-gear composition"; 2026-05-17 sharpening: "the Cauchy-form kernel c_k = ε^k/k is the SINGLE algebraic shape carried by every substrate showing Kepler-shape behaviour" | memory `user_stance_kepler_shape_universal.md`; snap:3786; book Thm 8.2 p.54 ("Argument … by Definition 7.1's characterisation … therefore Class K-instantiating") | 2026-05-15 / -17 | universality **TAUTOLOGICAL** (definitional); the sharpening **FALSIFIED** | Kepler's own E(M) is not ε^k/k beyond e² (S1, S3-A), and neither is ν − M (S3-B). Where ε^k/k does occur exactly in Kepler motion is measured in §2.2 | memory unchanged |
| C12 | Saturation threshold **s\* = 1 − √(ε_kepler · ε_fib)** = 1 − √(0.0167·0.618) ≈ 0.8985 | snap:5003 (§VIII.28); `notes/spike154_saturation_threshold_calc_findings_2026-05-19.md:69, :158` | 2026-05-19 | **UNMEASURED** derivation that inherits C9 and A3 | ε_fib = 0.618 is \|ψ\|, which is not a measured Fibonacci rate (the ratio's rate is 0.382, S4). The pairing "Kepler ↔ Fibonacci as two ends of one kernel" rests on C9. The threshold's own derivation was not rechecked | mfo:5814 unchanged |
| C13 | Kepler's equation, Newton-Raphson, and the equation-of-centre coefficients [2, 5/4, 13/12, …] | `kepler.py:103-240`; book Ch 8 §8.5 pp.56-57 | 2026-05-15 | **STANDS** | the table matches measured ν − M at e = 0.0167 to 4 digits (S3-B) | — |
| C14 | The pin-slot series itself is exactly Σ ε^k/k sin kM | Spike #29 §2 | 2026-05-16 | **STANDS** (DERIVED: arg(1 − εe^{−iM}) = Σ ε^k sin kM / k; R1 measures `pin_slot` magnitudes ε^k/k with alternating sign) | the defect is only the Kepler label (C4) | — |

**Suspect-item count** (every row whose status is not STANDS): A1, A2, A3, A4, A5, A6, A7b, A8, A9, A12, A13, A14, A15, A16, A17 (15); B1, B2 (2); C1–C12 (12). **Total 29.**

---

## §2 RECHECK — the measurements and derivations that decide the non-STANDS rows

### §2.1 The Kepler cascade pair, exactly (S1, S2, R1–R3)

**(i) The lattice is validated against srmech.** Take the Kapteyn ascending series (2/k)J_k(ke) = Σ_m (−1)^m k^{2m+k} e^{2m+k} / (k·2^{2m+k−1}·m!(m+k)!) as a lattice c_{p,k} with p = 2m+k. Its column sums at e = 3/10 (p ≤ 120) agree with `srmech.music.bessel_j_fixed` to |diff| ≤ 4.2e-77 for k = 1…6. MEASURED (S1 part 0).

**(ii) Depth n equals e-order n, exactly and only.** The depth-n one-pin cascade E_{n+1} = M + e sin E_n was expanded in exact Fraction arithmetic to e⁹ (S1 part 1):

```
depth 1: all lattice cells with p <= 1 EXACT; first mismatches (2,2): 0 vs 1/2, (3,1): 0 vs -1/8, (3,3): 0 vs 3/8
depth 2: all lattice cells with p <= 2 EXACT; first mismatches (3,1): -3/8 vs -1/8, (3,3): 1/8 vs 3/8
depth 3: all lattice cells with p <= 3 EXACT; first mismatches (4,2): -5/12 vs -1/6 ...
 ...
depth 8: all lattice cells with p <= 8 EXACT; first mismatches at p = 9
cos-terms: 0 at every depth; harmonics present at orders > n: all k (1..9) for n = 2..7
```

- MEASURED: depth n reproduces **every** lattice cell with p ≤ n (every harmonic k ≤ p), and **none** reliably at p = n+1.
- The truncation in modes, E_K = M + Σ_{k≤K} r_k sin kM, is by construction every cell with k ≤ K, at all orders p.
- **So the two truncations are row and column projections of one triangular lattice** {(p,k): 1 ≤ k ≤ p, p ≡ k mod 2}. They share the cells with p ≤ n and k ≤ K. **No bijection** between depth-n and K-mode truncations exists at the level of coefficients. The correspondence that does exist is exact, and it runs between the **depth** frame and the **e-power (Lagrange jet)** frame, not the harmonic frame. MEASURED.
- The depth frame's inexact remainder at orders > n is spread over **all** harmonics (last output field above), so a finite depth never looks like a finite mode sum. MEASURED.

**(iii) Each frame shows the index the other hides.** Each harmonic radius r_k = Σ_m c_{2m+k,k} e^{2m+k} carries an unbounded e-order tower inside one mode. The harmonic frame therefore shows k and sums out p. The depth frame shows p (rows) and smears k. MEASURED for Kepler (i and ii); the general statement is CANDIDATE (§3).

**(iv) Rates are frame-relative (S2).**

| e | depth frame: per-step sup-error ratio (2nd half) | steps to 1e-13 | mode frame: r_{k+1}/r_k at k = 10 / 20 / 40 / 60 | ρ(e) | modes to 1e-13 |
|---|---|---|---|---|---|
| 0.1 | 0.0928 – 0.0990 | 12 | 0.1176 / 0.1260 / 0.1307 / 0.1323 | 0.1356 | 13 |
| 0.3 | 0.2871 – 0.2940 | 23 | 0.3458 / 0.3705 / 0.3841 / 0.3888 | 0.3986 | 27 |
| 0.7 | 0.6908 – 0.6927 | 60 | 0.7248 / 0.7758 / 0.8039 / 0.8137 | 0.8341 | 61 |

MEASURED. The depth rate tends to e (the Lipschitz constant of the pin stage, DERIVED). The mode ratio approaches ρ(e) = e·exp(√(1−e²))/(1+√(1−e²)); that closed form is CITED-NOT-FETCHED and used only as a comparison, not as evidence. **The same object has at least two different "rates of approach".**

**(v) A third frame fails where the other two succeed: the Laplace radius (S1 part 2).** At M = π/2 the e-power coefficients a_p give a root test |a_p|^{−1/p} = 0.8329 (p=21), 0.7634 (41), 0.7212 (81), **0.7047 (121)**, falling steadily. Partial sums against `kepler_solve`:

```
e=0.60  error  P=25: +2.23e-04  P=51: -5.97e-06  P=81: +1.53e-07  P=121: +1.58e-09   (converges)
e=0.65  error  P=25: +1.80e-03  P=51: -3.86e-04  P=81: +1.09e-04  P=121: +2.77e-05   (converges slowly)
e=0.70  error  P=25: +1.24e-02  P=51: -1.82e-02  P=81: +4.75e-02  P=121: +2.34e-01   (DIVERGES)
```

MEASURED. The radius at M = π/2 therefore lies in (0.65, 0.70). The root of the Laplace-limit equation x·exp(√(1+x²))/(1+√(1+x²)) = 1 is 0.6627434193 (formula CITED-NOT-FETCHED, used only as a consistency check). At e = 0.7 the depth frame (60 steps) and the mode frame (61 modes) both reach 1e-13 (S2), and R2/R3 give 4.355e-08 at depth 40 and 4.336e-08 at 60 modes.

**Consequence.** The depth frame agrees **termwise** with the e-power frame at every finite depth (ii), yet the e-power frame diverges where the depth frame converges. **An exact finite-stage correspondence does not carry convergence.** Frames reach the same limit where each one converges. They are not interchangeable as constructions.

### §2.2 What ε^k/k is, and what the record's numbers are (S3, R1)

- **(A) Spike #29 / C4.** At ε = 0.1146 the ratio ε^k/k ÷ (2/k)J_k(kε) is 1.0016, 1.0044, 0.8955, 0.7579, 0.6229, 0.5022, 0.3996 for k = 1…7. The "ratio 1.0000 across 7+ harmonics" in `sign_change_pin_slot_epicycle_2026-05-16.md:38-46` compared the atan2 FFT with its own Taylor series. MEASURED.
- **(B) Spike #30B / AoE / C5, C6.** At e = 0.0167 the measured ν − M is 3.339884e-2, 3.485769e-4, 5.044712e-6; the `kepler._EOC_COEFFS` table gives 3.340000e-2, 3.486125e-4, 5.045585e-6; E − M gives 1.669942e-2, 1.394320e-4, 1.746275e-6; ε^k/k gives 1.67e-2, 1.394450e-4, 1.552488e-6. At e = 0.0506: ν − M 1.011676e-1, 3.197447e-3, 1.401277e-4; ε^k/k 5.06e-2, 1.28018e-3, 4.318474e-5. MEASURED. **The record's numbers are ν − M; its label is ε^k/k.**
- **(C) The exact home of ε^k/k in Kepler motion.** As a function of E, (ν − E) has harmonics 2β^k/k with β = e/(1+√(1−e²)). At e = 0.3 (β = 0.153536): 0.30707199/0.30707199, 0.02357330/0.02357330, 0.00241290/0.00241290, 0.00027785/0.00027785. At e = 0.7 (β = 0.408367): 0.81673473/0.81673473 … 0.01390510/0.01390510. MEASURED to 8 digits. So the pin-slot series is Kepler's **ν ↔ E** relation, halved, at the reduced parameter β and in the eccentric-anomaly variable. It is not E(M) and not ν(M). The Hipparchan eccentric-circle reading in `pin_and_slot.py:49-51` (ε ≈ 2e matches ν − M at first order: ε = 2e gives 2e sin M + 2e² sin 2M against 2e sin M + (5/4)e² sin 2M) is DERIVED from these two series and is consistent with it.
- **(D) FM ≠ Kepler / C8.** At β = 0.3: FM 1.483e-1, 1.117e-2, 5.593e-4, 2.100e-5, 6.304e-7; Kapteyn 2.966e-1, 4.367e-2, 9.623e-3, 2.511e-3, 7.198e-4. MEASURED. FM uses a fixed Bessel argument (Jacobi–Anger); Kepler's argument grows with k (Kapteyn). They are different series.
- **(E) Hopf "gap" / A12.** For l = 0…8: S³ gives l(l+2) = 0, 3, 8, 15, 24, 35, 48, 63, 80; unit S² gives l(l+1); the radius-½ base gives 4j(j+1) at l = 2j = 0, 8, 24, 48, 80, equal to the S³ value in every case. MEASURED (integer arithmetic). The "gap l" comes from comparing different radii and labels. Fibre content lives in the U(1)-charge ≠ 0 sectors (standard, CITED-NOT-FETCHED; not needed for the verdict).

### §2.3 Heron and Fibonacci (S4)

- srmech `best_rational` reproduces all 106 CF convergents of √2 (recurrence p_n = 2p_{n−1} + p_{n−2}): `True`. Heron from x₀ = 1 gives depth n = convergent **index 2^n − 1** exactly (1, 3, 7, 15, 31, 63), with errors 10^−1.1, −2.6, −5.7, −11.8, −24.0, −48.5. MEASURED. This is a two-frame instance with an **exact index map** (a subsequence), the strong end of the correspondence spectrum. Kepler depth ↔ modes sits at the weak end (shared limit, disjoint row/column projections).
- Fibonacci ratio error ratios err(n+1)/err(n) at n = 10, 20, 30, 40: −0.381979, −0.381966, −0.381966, −0.381966. \|ψ\| = 0.618034, ψ² = 0.381966. MEASURED. A3 and C12 carry the wrong constant: the CF-convergent approach to φ (the "slowest" CF, which is what Hardy & Wright is cited for, CITED-NOT-FETCHED) runs at ψ², not \|ψ\|.

### §2.4 Tautologies decided without numerics

- **A5 (S5).** Inverting 2√(1−x²) gives a/M = 0.00000, 0.66985, 0.99001, 0.99901. The "super-logarithmic" sequence is four hand-picked evaluations of a closed form.
- **A8 (S5).** For a sinusoid at integer frequency r, the zeros on [0, 2π) are kπ/r, k = 0…2r−1, so a closed period has 2r sign changes: 14, 98, 686, 42, 286 for the stacks tested in Spikes #212–#215. The verdicts "DEPTH-3-CONFIRMED-UNBOUNDED" and "ASYMMETRIC-RATIO-INVARIANCE-UNIVERSAL" restate multiplication of frequencies. DERIVED + MEASURED.
- **C9.** `spike_41_fibonacci_unity.py:117-119` (`return [epsilon ** k / k …]`) and `:735-742` (`kepler_at_psi = equation_of_centre(psi_abs, 20)` vs `[psi_abs ** k / k]`). Source-read.
- **C10.** K_k := c_k/ε^k fits any sequence. DERIVED.
- **A9.** snap:3807 records closure verification #2 as Class L's identity "broadens from graph Laplacian to dense-matrix linear algebra". A closure test that can widen a class's scope has no failing outcome. Source-read.

### §2.5 What did NOT change since May (G2)

- §VII.6.9: current vs snapshot differ in exactly three lines, all the octonionic→quaternionic Hopf-name correction.
- §VIII.9, §VII.6.10.4 and §VII.4.1.1: `diff` is empty.
- The ε^k/k-as-Kepler sentence still stands at mfo:754, :1697, :1705, :1721, :1988, :4555, :4580, :4765, :5814, srmech notebook :672, antikythera notebook :723/:754, the two `pin_and_slot.py` copies, and **shipped** `kepler.py:62-64`.
- `git grep -i kapteyn -- docs` finds only `spike_40_fm_anomaly_investigation_exact.py:48` and `spike_pinslot_f2_deep_dive_2026-05-14.py:45`. **No correction exists yet anywhere in the tree.**

### §2.6 Failure pattern (the thing to look for elsewhere)

1. A **correct earlier record** (F2, 2026-05-14, which printed the Kapteyn formula and separated E from ν) is compressed into a shorter slogan on a leading-order match.
2. The slogan is then **checked against itself** (Spike #29, Spike #41).
3. It is **certified by an instrument that cannot discriminate** (strict K-test).
4. It is **attributed to a canonical source** that was never extracted (Brouwer & Clemence).
5. It propagates into stances, which later records cite as settled.

Signatures to grep for: "machine precision" / "0.00e+00" beside a formula defined in the same script; "K-indistinguishable"; "IS … to second order"; a source cited "project-verified per Spike #N".

---

## §3 THE DUALITY OF UNBOUNDEDNESS

### §3.1 What the maintainer's reading claims, stated precisely

- **(D1)** The discrete/cyclic frame and the continuous frame are co-equal descriptions of one object.
- **(D2)** The unboundedness each frame shows (unbounded construction in the discrete frame; hidden fibre content in the continuous frame) is **one thing seen from two perspectives**.
- **(D3)** The A–N grammar is an 11/14-D chunk of a larger hypercomplex object. It neither creates, projects nor resonates.
- **(D4)** What separates the two descriptions is a duality that carries fibre content.
- **(D5)** Insisting on one true description is the modern-era problem.

### §3.2 What supports it

- **R30 (2026-05-24)**, two days after the snapshot: `substrate_native_research_notebook.md:261` "NEITHER is downstream-projection of the other" (supports D1).
- **The Kepler pair, now exact** (supports D1, D2):
  - The limit E(M) is frame-free: it is reached to 8.9e-16 by depth 40 and by 32 modes at e=0.3 (R2, R3).
  - Both frames carry an **exact, unbounded integer index**: depth n in one, harmonic k in the other.
  - Both carry **inexact per-stage content**: each stage's sin is a truncated Class-N series; each radius r_k is a transcendental J_k at declared scale 2⁻²⁵⁶.
  - **What the harmonic frame hides inside each mode (the e-order tower m) is exactly what the depth frame exposes as its index (rows p ≤ n)** (§2.1 ii–iii). This is D2 made concrete for one object, with "hidden fibre content" = the summed-out grading. MEASURED for Kepler.
- **Heron ↔ continued fractions**: an exact index map between a depth frame and a Class-N frame (S4). A second instance.
- **The current record already holds the co-equal reading at the level of data.** srmech notebook §3.59.5 (:8581-8588): "1/7 is an element of ℤ/7; 2π/7 is a real number. The POINT they name is the same. The SET each is drawn from is not." Also MFO §VIII.31.21 (:6784-6815): two independent facts, both corners measured.
- **Hidden content is recoverable.** mfo:6691 (§VIII.31.19 item 1): fixed references recover the object uniquely; residue exactly one bit (item 8). The early "continuous frame hides fibre content" (A10) is therefore right and incomplete: *hidden* means *not in this frame's index*, not *lost* (supports D4).
- **The shipped introspection contract already treats the frame as an attribute of the responsion.** Each `responsion_schema` record has `regime ∈ {continuous_spectral, discrete_algebraic}` (`responsion_schema.py:46-59`) (supports D4, see §4 D2).

### §3.3 What contradicts or limits it

1. **"Same thing" holds at the limit and at integer invariants, not at the rate.** The depth rate is ≈ e and the mode rate is → ρ(e) (S2). A reading that makes the *rate* the substance (A2) is frame-bound.
2. **Correspondence strength varies by object.** Heron has an exact subsequence map; Kepler depth ↔ e-order has exact jet agreement; Kepler depth ↔ modes has only the shared limit (row vs column projections). "Two perspectives on one thing" is therefore always true of the **limit**, and true of **finite stages** only when one construction is a regrading or subsequence of the other. MEASURED for three pairs.
3. **Frames are not interchangeable as constructions.** The e-power frame diverges for e = 0.70 while depth and modes converge (§2.1 v). The frames are co-equal as *descriptions of a limit where both converge*, not co-equal as algorithms.
4. **D3's "11/14-D chunk" and "unbounded construction" sit on orthogonal axes.** All of Kepler's unboundedness lives in **one** imaginary direction (the ℂ block, powers e^{ikM}, k ∈ ℤ). The Hurwitz bound limits the **number of anticommuting directions** (type), not iteration or powers. This is the snapshot's own type-wise/depth-wise split (snap:2365, A7a) and the order discriminant of srmech §3.59.0 (rows 2 and 5: exact but unbounded iff the group has infinite order, e.g. the integer winding T5). DERIVED. So "the grammar is bounded at 14" is not in tension with "construction is unbounded". They describe different axes of the object, and D3 should say which axis it bounds.
5. **D4's "duality with fibre content" is measured here only as a summed-out grading (Kepler) and a subsequence (Heron).** Whether every discrete/continuous pair has such a hidden grading is **CANDIDATE**.

### §3.4 What remains CANDIDATE

- **(CAND-1)** Two constructions of one limit object are two summation orders, or two regradings, of one multi-graded object. Each frame's unbounded index is the other frame's hidden fibre. (Measured for Kepler; Heron fits as a degenerate one-index case.)
- **(CAND-2)** The frame-free data of an unbounded construction are its **limit** and its **integer invariants**. For Kepler: winding number 1 (E(M+2π) = E(M) + 2π at every truncation in both frames, DERIVED), triangular lattice support k ≤ p, and parity p ≡ k mod 2 (MEASURED S1).
- **(CAND-3)** B/H/N as translation operators (R30) would be the maps between gradings. In Kepler that map is the Kapteyn resummation, which is neither B, H nor N as shipped. **Not established.**

### §3.5 How the existing stances would have to change

- **`user_stance_infinity_approximates_asymptote`.** Keep "asymptote is not cardinal infinity" and the generous historical reposture. **Withdraw the direction** "asymptote upstream, infinity downstream". Replace with: *the limit object is frame-free; "infinity" names the unbounded index of a chosen construction (depth, mode count, series order); the indices of different constructions are co-equal and may be related exactly, partially, or only through the limit.* It privileged the discrete/asymptotic frame. Its sister stances did so explicitly: `pi_as_projection` "integer-cyclic upstream"; `continuous_number_line` "between integers there's no position"; `loe_asymptotes` "substrate primary, shadow secondary"; book appendix p.162.
- **`user_stance_asymptotic_dof_sidesteps_infinity`.** Keep "count at the limit-approach, not the limit itself". Change "the rate is what observation constrains" to "**a rate belongs to a construction**; name it". **Withdraw the 2026-05-17 sharpening** entirely: it rests on C9 (tautology), C5 (mis-citation) and A3 (wrong Fibonacci constant).
- **"Generator" (B1).** Its history: no such use at the May-22 snapshot. From 2026-05-26 it was an IFS generator (a Hutchinson map whose attractor is a fractal). From 2026-06-05 the One was "the single generator of the 14 substrate", shipped as docstring + `s_generator`. From 2026-07-24 the Cayley–Dickson addressing bump was "the generator". **Word the record's own evidence supports: FORM**, specifically **reference form / reference frame**:
  - "A unifying form, not a derived theory" (mfo:6575).
  - Partitions are "regroupings of the same 𝕊" (mfo:6450).
  - Its reals are the fixed **references** of retrieval (measured, mfo:6691).
  - It is block-diagonal by construction, so it binds nothing across rungs (mfo:6701).
  - Its falsifier is the regroup-only test (mfo:6575).

  Each of these is a property of a form that is **read**, not of something that generates. This fits the maintainer's own exclusion (not create, not project, not resonate). CANDIDATE vocabulary; the measured roles are MEASURED in the record.

---

## §4 OP ⊗ OPERAND ⊗ RESPONSION — per dictionary, with Kepler worked through

### §4.0 Census verified

srmech notebook §3.59 opening (:8248-8261) tabulates three different counts:
- **FOUR placements** of the turn, already in the tree.
- **SIX dictionaries** D1–D6 (§3.59.3, :8430-8440): four adopted (D1 spectral, D2 verb/noun, D3 carrier parts, D4 rung), D5 topological (candidate, self-fenced), D6 field/excitation/curvature (candidate, open in all three slots).
- **SIX turn-objects** T1a–T5 (§3.59.5).

Root CLAUDE.md's "four placements of the TURN" is correct (placements). **`docs/antikythera-maths/CLAUDE.md:9` is stale**: it says "§3.59.3 names the four different dictionaries", but the census has six (a correction is listed in §5b).

### §4.1 Kepler through each dictionary

"Bounded grammar" = the finite rule set. "Unbounded construction" = the unbounded index. "Hidden fibre" = what the continuous (harmonic) frame sums out.

| dict | slot 1 | slot 2 | slot 3 | bounded grammar sits… | unbounded construction sits… | hidden fibre sits… | status |
|---|---|---|---|---|---|---|---|
| **D1 spectral** (read only on the **linearisation** at the fixed point and on the **jet**; the full map is nonlinear) | eigenvectors = sin(kM), eigenmodes of the cyclic shift on the M-circle: the **harmonic frame's alphabet** | edges = the single pin coupling e·sin(·); under n-fold repetition its exact reach in the lattice is rows p ≤ n (the §3.59.1 authority table's "1-hop → n-hop") | eigenvalue = contraction factor e·cos E; λⁿ governs the depth-frame error | **slot 2** (one edge rule) | **slot 3** exponent n (depth); **slot 1** count K (modes) | inside each slot-1 coefficient (the e-order tower of r_k) | slot 2 reach **MEASURED** (S1); slot 3 λ → e **MEASURED** (S2; §3.59.0 row 3, \|λ\| < 1 ⇒ bounded error); slot 1 **CANDIDATE** (standard eigenbasis fact); full nonlinear object **DOES-NOT-MAP** (remainder spreads over all k, S1) |
| **D2 verb / noun / (op, carrier) edge** | A–N verbs used: gear (I), pin (K), Class-N sin, `bessel_j_fixed` | carriers: float, Fraction/Q | the (op, carrier) responsion edge, carrying `regime ∈ {continuous_spectral, discrete_algebraic}` (`responsion_schema.py:46-59`) | **slot 1** (finite verb set) | **DOES-NOT-MAP** (a chain's depth is a path through the introspection graph, not a node or edge) | **DOES-NOT-MAP** as a slot; the **frame itself** is an attribute of slot 3 | regime field source-read. G4 **MEASURED**: 23 edges, 25 responsions, 20 `discrete_algebraic` / 5 `continuous_spectral` (all `laplacian.*|Mat`: responsion propagator+resolvent, propagate, heat_trace, ground_state_flux_response), **0 edges carry both regimes**, no Kepler or Bessel edge registered. **CANDIDATE**: D2's native place for the duality is **one (op, carrier) edge carrying two responsions of opposite regime** (the schema is list-valued, so this is allowed and never exercised). `kepler_solve|float` with a depth responsion and a Kapteyn responsion would be the first |
| **D3 carrier parts** (rotation / real / resonance) | rotation = e^{iM} and its powers e^{ikM} | real = the displayed offset E − M, real radii r_k | resonance / the_one | **number of imaginary directions used = 1** (the ℂ block) | **integer powers k of one rotation**: exact index, infinite order, the T5 shape (§3.59.0 row 5) | the amplitude r_k: T1a-like, transcendental, exact only at declared scale | slots 1-2 **DERIVED**; unbounded-at-infinite-order **DERIVED** via §3.59.0; slot 3 **DOES-NOT-MAP** (the One is block-diagonal and binds no harmonics, mfo:6701) |
| **D4 rung** (ℂ / ℍ / 𝕆) | ℂ | ℍ (unused) | 𝕆 (unused) | the Hurwitz type bound | not on this axis | not on this axis | **DOES-NOT-MAP** beyond ℂ. The DERIVED finding is that Kepler's unboundedness is orthogonal to the rung axis (§3.3 point 4). D4 is self-fenced |
| **D5 topological** (Tw / Wr / Lk) | Tw-like: uniform winding carried by M (the gear) | Wr-like: periodic remainder with zero net winding (the pin) | Lk-like: degree 1 of E as a circle map | — | — | — | Lk = 1 preserved exactly by every depth-n and K-mode truncation: **DERIVED** (shadow-free integer invariant, CAND-2). Tw/Wr split: **CANDIDATE** (D5 is itself a candidate dictionary) |
| **D6 field / excitation / curvature** | — | — | — | — | — | — | **DOES-NOT-MAP**: open in all three slots (§3.59.3 :8461-8470); placing Kepler would be the cross-dictionary transport §3.59.4 forbids |

### §4.2 Reading across the table

- **D1 (linearised) and D3 both place the two frames' unbounded indices in different slots:**
  - D1: depth in the responsion exponent, modes in the eigenvector count.
  - D3: modes as integer powers of the one rotation; depth is not a D3 object.
- **D2 is the only dictionary with an explicit field for "which frame".** It puts the frame on the responsion, not on the op or the operand. CANDIDATE: that is the structural home of D4 in the maintainer's reading ("the duality … with some fibre content").
- The dictionary where "hidden fibre" means something measurable for Kepler is **D1**: the coefficient tower inside a slot-1 mode, validated to 1e-77 (S1 part 0).
- Placing it in D6's curvature slot is not supported.

---

## §5 DRAFT TEXT — not applied

### §5a Proposed amendment to the infinity stance

Append to `user_stance_infinity_approximates_asymptote.md`; mirror the second and fourth paragraphs in `user_stance_asymptotic_dof_sidesteps_infinity.md`.

> ## Amendment 2026-09-14 — unboundedness is frame-indexed; the limit is frame-free (MEASURED on Kepler's equation, srmech 0.9.0rc472 pure)
>
> **Kept.** No cardinal infinity is asserted of anything the framework computes. "Asymptote" and "limit" language stays, and so does the historical reposture (infinity was the best tool 17th-century algebra had).
>
> **Withdrawn: the direction.** "Asymptote upstream, infinity downstream" and "integer-cyclic upstream, continuous downstream" are withdrawn *as ontology*. They privileged one construction. R30 (2026-05-24) already said neither language is a projection of the other; this stance did not follow it.
>
> **What replaces it.** One object can be reached by several constructions, and each construction carries its own unbounded index. Kepler's E(M) is the worked case:
> - **depth n**: one pin rule iterated, E_{n+1} = M + e sin E_n;
> - **mode count K**: one rotation raised to integer powers, radii (2/k)J_k(ke);
> - **e-order p**: the Lagrange power series.
>
> All three are exact integer indices. Depth n reproduces every e-order-≤n coefficient exactly and nothing above it; mode count K reproduces every harmonic-≤K coefficient at all orders. Depth and modes are row and column projections of one triangular lattice. **What the harmonic frame hides inside each mode (the e-order tower) is exactly what the depth frame exposes as its index.** (`opus_scratch/s1_lattice.py`.)
>
> **Rates belong to constructions, not to objects.** The same E(M) approaches at ratio ≈ e per depth step and ≈ ρ(e) per mode (0.29 vs 0.39 at e = 0.3). The e-power construction *diverges* at e = 0.70 while the other two converge (`s1_lattice.py`, `s2_rates.py`). When writing "asymptotic-DoF" or "rate of approach", **name the construction the rate belongs to.** The frame-free data are the limit and the integer invariants: winding number 1, lattice support k ≤ p, parity p ≡ k (mod 2).
>
> **The 2026-05-17 sharpening (Cauchy kernel ε^k/k = Kepler; Fibonacci 0.618 as the slowest end) is withdrawn.**
> - Step 4 of Spike #41 compared ε^k/k with itself.
> - ε^k/k is not Kepler's E(M) beyond e² and not ν(M) at all. It is exactly (ν − E)/2 in the E variable at β = e/(1+√(1−e²)) (`s3_pinslot.py`).
> - The Fibonacci ratio converges at ψ² = 0.382, not \|ψ\| = 0.618 (`s4_heron_cf.py`).
>
> **CANDIDATE, not measured beyond Kepler and Heron.** Two constructions of one limit are two summation orders or regradings of one multi-graded object, and each frame's unbounded index is the other's hidden fibre. Correspondence strength varies: exact subsequence (Heron depth n = CF convergent 2ⁿ−1), exact jet agreement (Kepler depth ↔ e-order), or the shared limit only (Kepler depth ↔ modes).

### §5b Record corrections owed

Each correction is an **APPEND** (a dated note placed after the cited text; the dated text is never rewritten). The evidence column names the command.

| # | target (current) | append text (short form) | evidence to cite |
|---|---|---|---|
| 1 | MFO §VII.1.2, after mfo:754 | "Correction 2026-09-14: the pin-slot atan2 algebra is not Kepler's equation of centre (ν − M, c₁ = 2e); its c₁ is ε. It agrees with the eccentric anomaly E − M only through e², and is exactly (ν − E)/2 in E at β = e/(1+√(1−e²))." | S3-A, S3-C; S1 cells (3,1), (3,3) |
| 2 | MFO §VIII.6.1 K row mfo:4555 and closure-validation #3 mfo:4580 | "Correction 2026-09-14: the Spike #29 'machine-precision identity across 7+ harmonics' checked the atan2 series against its own Taylor series. Against Kepler's E(M) the ratio at ε = 0.1146 is 1.0016, 1.0044, 0.8955, 0.7579, 0.6229, 0.5022, 0.3996 (k=1…7). The Class-K-vs-Class-L non-dissolution verdict is unaffected." | S3-A |
| 3 | MFO §VII.6.1.4, after mfo:1697 and :1721 | "Correction 2026-09-14: the listed values c₁ ≈ 0.101, c₂ ≈ 3.20e-3, c₃ ≈ 1.40e-4 are the true-anomaly equation of centre at e = 0.0506 (2e, (5/4)e², (13/12)e³), not ε^k/k (5.06e-2, 1.28e-3, 4.32e-5). The predicted c₂/c₁² ≈ 19.76 matches neither: c₂/c₁² is 1/2 (ε^k/k) or 5/16 (ν − M); 19.76 = 1/ε. Brouwer & Clemence is cited-not-fetched; the inconsistency is internal." | S3-B |
| 4 | MFO §VII.6.1.5 Q1, after mfo:1705 | "Note 2026-09-14: the Poisson-kernel identity stands; the label 'Brouwer-Clemence c_k = ε^k ladder' does not. The equation of centre is a different series, as the '~0.3%' already shows." | S3-B |
| 5 | MFO §VII.6.5, after mfo:1988 | "Note 2026-09-14: c_k = ε^k·K_k(substrate) constrains nothing while K_k is free (K_k := c_k/ε^k fits every sequence). Theorem-level claims need a stated K_k." | §2.4 |
| 6 | MFO §VIII.9, after mfo:4765 | "Correction 2026-09-14: Spike #41's 'Cauchy form unity' rests on a self-comparison (spike_41_fibonacci_unity.py:117-119, :735-742). Support for (P1)/(C3) from Spike #41 is withdrawn." | §2.4, S4 |
| 7 | MFO §VIII.28, after mfo:5814 | "Note 2026-09-14: s* uses ε_fib = \|ψ\| = 0.618; the measured Fibonacci convergence rate is ψ² = 0.382. The Kepler↔Fibonacci pairing rests on the withdrawn Spike #41 identity. s* is an unmeasured fit until re-derived." | S4 |
| 8 | MFO §VII.4.1.1, after mfo:946 | "Correction 2026-09-14: l(l+2) − l(l+1) = l compares a unit S³ with a unit S². The Hopf base is S² of radius ½, on which U(1)-invariant S³ modes (l = 2j) have eigenvalue 4j(j+1) = l(l+2): no per-mode gap. Fibre content lives in the charge ≠ 0 sectors. The information-channel reading needs restating on those sectors." | S3-E |
| 9 | MFO §VII.4.1.3 item 4 (current position of snap:1024) | "Note 2026-09-14: the gap sequence {2.000, 1.485, 0.282, 0.089} samples 2√(1−x²) at a/M = 0, 0.670, 0.990, 0.999. It is not a dynamical approach rate." | S5 |
| 10 | MFO §VIII.31.8, after mfo:6024 area | "Note 2026-09-14: the sign-flip counts 2∏r follow from frequency multiplication for any nested sinusoid, so the depth-1/2/3 and ratio-agnostic verdicts cannot fail. They do not measure a Hopf bundle. 'Unbounded' is true of the construction trivially; the Hopf identification is unmeasured." | S5 |
| 11 | MFO §VII.6.9 (current position of snap:2365) | "Note 2026-09-14: 'bounded type-wise, unbounded depth-wise' stands. The reason 'because the traversal is continuous' is withdrawn: Kepler's unbounded depth is an exact integer index inside a single ℂ block." Plus, at snap:2266's current position: "'ALL continuous dimension counts are projection-shadows of the discrete traversal' is superseded by R30 (2026-05-24): neither language is a projection of the other." | S1, S2; substrate-native nb :261 |
| 12 | MFO §VII.6.10.4 and §VII.6.10.6 | "Note 2026-09-14: 'the polygon IS the substrate, the circle its shadow' is superseded by R30. Heron converges quadratically (error 10^−1.1 → 10^−48.5 in six steps) and has an exact second frame: depth n = CF convergent 2ⁿ−1. It is a two-frame instance, not a Class-K super-logarithmic one." | S4 |
| 13 | MFO §VIII.6.1 closure paragraph (current of snap:3820) | "Note 2026-09-14: closure verification #2 was closed by broadening Class L's scope. A closure test that can widen a class has no failing outcome, so the 'four independent positive verifications' are rulings, not measurements." | snap:3807 |
| 14 | MFO §VIII.31.15, after mfo:6575 | "Vocabulary note 2026-09-14: the heading's 'unifying generator' (added 2026-06-05) is not May-era vocabulary and is not supported by this section's own evidence. The section is a unifying **form** (its status line), whose reals are measured **references** (§VIII.31.19 item 1) and which is block-diagonal by construction (item 6). Prefer 'reference form'. The shipped docstring and `s_generator` alias (`one.py:1, :653, :1155`) are a maintainer decision (public API)." | §1 B1 |
| 15 | srmech notebook §3.8.0a, after :672 | Same content as #2. | S3-A |
| 16 | `docs/antikythera-maths/CLAUDE.md:9` (orientation file; a correction, not a dated append) | "§3.59.3 names **six** dictionaries (four adopted, D5 and D6 candidates) and **four** placements." | srmech nb :8255 |
| 17 | memory `user_stance_kepler_shape_universal.md` | Append: withdraw the 2026-05-17 sharpening (FM identity, Cauchy kernel as THE shape, Fibonacci identity). Record the measured home of ε^k/k (S3-C). Keep the burden-flip only as a methodological stance, marked definitional. | S1, S3, S4, C5 record |
| 18 | memory `user_stance_asymptotic_dof_sidesteps_infinity.md` | Append §5a paragraphs 4-5. | S1, S2, S4 |
| 19 | memory `user_stance_epicycle_via_gear_plus_pin.md` | Append: "Cauchy-form ε^k/k is exactly the pin-slot's own series (true), not Kepler's; the 'pin-slot = asymptotic DOF' operational identity does not carry a rate law (the one-pin cascade converges geometrically at ratio e)." | S2, S3 |
| 20 | memory `user_stance_pi_as_projection.md`, `feedback_continuous_number_line_pedagogical_obstacle.md`, `user_stance_loe_asymptotes_are_ring_valued.md` | Append: "Ontological 'upstream/downstream' / 'substrate primary, shadow secondary' superseded by R30. The writing rules (do not interpolate discrete data; name the frame) stand. Same point, different set (srmech §3.59.5)." | substrate-native nb :261; srmech nb :8581-8588; G4 (5 shipped continuous responsions) |
| 21 | memory `user_stance_substrate_is_asymptotic_traversal_1d_to_11d.md` | Append: "Heron anchor: quadratic convergence and an exact CF second frame. Depth-wise unboundedness needs no continuity." | S4 |
| 22 | memory `project_h_genome_is_fibrated_hurwitz_tower.md` + MEMORY.md index line | Append: "𝕊 names two objects: the One (dim 14 = ℂ⊕ℍ⊕𝕆) and the sedenions (dim 16). 'the_one loses division' holds for any direct sum and says nothing about sedenions." | mfo:6490, :6673 |

**Owed on other surfaces** (flagged, not drafted in full; latency by surface):
- **Shipped wheel text** `docs/srmech/python/srmech/math/kepler.py:62-64` (the `pin_slot` docstring), in the current rc.
- `docs/antikythera-maths/antikythera-spectral/python/antikythera_spectral/_research/pin_and_slot.py:47-48, :91` and its research twin `research/pin_and_slot.py:47-49, :91`: replace "E(M) = M + Σ(ε^k/k) sin kM" with the E−M-to-O(e²) statement.
- Antikythera notebook :723, :754.
- Spike notes 29, 30B, 40, 41, and Spike #154's findings: append errata; the dated notes stay.

---

## §6 What I could not measure, and what would change these conclusions

**Not measured or not fetched**
- Brouwer & Clemence (1961) §3.2, Murray & Dermott, Hardy & Wright Thm 154, the Laplace-limit formula, the large-order Bessel form ρ(e), the Hopf base radius ½ and its charge-sector decomposition, Hurwitz/Adams. None was fetched. No verdict above depends on them: each was decided by the record contradicting itself or by a measurement, and they appear only as consistency checks.
- The *Inners Guide to the Hyper Loop* is not in the repository. If its Ch 4 "Asymptote and infinity" or Ch 6 "Discrete all the way down" uses "generator" or "bounded grammar / unbounded construction" in May 2026, the B1 dating correction changes; the vocabulary finding (the record's evidence supports "form") does not.
- The e-power root test at M = π/2 was carried to p = 121 (0.7047 and falling). The radius is bracketed in (0.65, 0.70) by partial sums, not pinned. Other M were not scanned.
- Only coefficient-level correspondences between depth-n and K-mode truncations were tested. A nonlinear resummation map between them is not excluded.
- CAND-1 (every frame pair is a regrading of one multi-graded object) was tested on two objects (Kepler, Heron), not on the MFO physics claims.
- Spike #154's s\* derivation was not re-derived; only its inputs were rechecked.
- The D1 mapping is valid only for the linearisation and the jet. The full nonlinear map does not map (measured).
- D6 cannot be tested while its slots are open.

**What would change the conclusions**
- If Brouwer & Clemence §3.2 prints c_k = ε^k/k *for some named quantity* (for example the eccentric-circle direction), C5, C6 and C9 downgrade from MIS-CITED to MIS-APPLIED. The measured facts (ε^k/k ≠ E(M) beyond e², ≠ ν(M)) stand.
- If a closure-verification procedure is shown that could have returned "a 15th class is required" without scope-broadening, A9 moves toward STANDS.
- If a dynamical Class-K instance with the (ξ*−ξ)^α, α ≥ 1 law is measured on shipped ops, A4 narrows to "one Class-K rate law among several".
- If a construction pair is found whose frames reach one limit but share **no** integer invariant, CAND-2 fails.
- If a construction pair is found whose finite stages cannot be related by any regrading, CAND-1 fails, and the duality stays true only "at the limit".
