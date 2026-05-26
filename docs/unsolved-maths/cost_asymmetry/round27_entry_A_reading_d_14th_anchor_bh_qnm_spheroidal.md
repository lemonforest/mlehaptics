# Round 27.A — Reading-D 14th scale-ladder rung: black-hole QNM spin-weighted spheroidal harmonics (the capstone)

**Dispatched** 2026-05-25 on the rolling draft PR #690 (the #679 model). User: *"dispatch the 14th rung — black-hole quasi-normal-mode spheroidal harmonics."* The **capstone** rung, at the strong-field-gravity / **horizon scale** (~10⁴ m stellar-BH `r_s` to ~10¹³ m supermassive), where the Class-L `2ℓ+1` shell becomes **spin-weighted and spheroidal** — the most deformed/general form of the spine on the entire ladder. It ties the Reading-D ladder (which began at the quantum Born rule, §11.9.4) back to the framework's own QNM spike cluster (#11 Killing–Yano Casimir, #12 photon-ring SL(2,R), #72 BH–BH merger) and the dark-star spikes (#90/#92).

Generating code + provenance: [`verify_round27_bh_qnm_spheroidal_anchor.py`](verify_round27_bh_qnm_spheroidal_anchor.py) + `.ndjson` (deterministic; exact integer/`Fraction` arithmetic; Class-N anchors via srmech 0.4.2 `best_rational`).

## The horizon carries the same S² Class-L spine

Kerr perturbations separate (Teukolsky 1973, ApJ 185:635) into **spin-weighted spheroidal harmonics** `_sS_{ℓm}(θ; aω) e^{imφ}`, with spin weight `s = −2` for gravity, `ℓ ≥ |s|`, `m ∈ [−ℓ, ℓ]` (`2ℓ+1` values per ℓ). The horizon is a **2D phase boundary** (MFO Spike #71/#19) carrying the *same* S² Class-L multipole structure as every other rung — with two new structural features that make this the most general realization of the spine:

**(1) Class-L bit-exact — the Schwarzschild angular eigenvalue.** In the non-rotating (`aω→0`) limit the spheroidal harmonics reduce to spin-weighted *spherical* harmonics, with the exact closed-form separation constant **`A = ℓ(ℓ+1) − s(s+1)`**. For gravity (`s=−2`): ℓ=2→**4**, ℓ=3→**10**, ℓ=4→**18**, ℓ=5→**28** (scalar `s=0`: 0,2,6,12). And the `2ℓ+1` mode counts, floored at ℓ≥2, are **5, 7, 9, 11** — the ℓ=2 quadrupole (5 modes) is the **universal "first nontrivial" Class-L mode**, the *same* quadrupole as the turbulent strain (§VII.6.17 / R22) and the QCD d-wave (R24).

**(2) Class-K spin-weight floor — the 4th forbidden-low-multipole rule.** Gravitational radiation has **no ℓ=0 (monopole) or ℓ=1 (dipole)** — mass and momentum conservation forbid them — so the QNM ladder **starts at ℓ=2**. This is the **fourth** Class-K "forbidden low multipole" selection rule across the ladder, after the planetary no-monopole (§11.9.15), the LSS even-ℓ (§11.9.18), and the capsid 12-pentamer (§11.9.19). *Each substrate forbids certain low multipoles by a conservation/topology rule* — this is now a robust cross-rung Class-K pattern, not a coincidence.

**(3) Class-K/C spheroidal deformation — the continuous spin knob.** The Kerr spin `c = aω` continuously **deforms S² → spheroid** — the spin axis is a **Class-C orientation**, the deformation magnitude `c` a **Class-K pin-slot continuous parameter**, the *same* "off-centre/spin breaks spherical symmetry" structure as the AoE off-centre observer (Spike #35). The leading spheroidal-correction coefficient (Berti–Cardoso–Casals 2006 form) is the small **Class-N rational** `A₁ = −2ms / [ℓ(ℓ+1)−s(s+1)]`: for the dominant `ℓ=m=2, s=−2` ringdown mode it is exactly **+2**; for `ℓ=3` it is `6/5` (m=3), `4/5` (m=2) — small-denominator rationals.

**Cascade: A ∘ L (spin-weighted spheroidal `_{−2}S_{ℓm}`; `2ℓ+1` floored ℓ≥2; Schwarzschild eigenvalue `ℓ(ℓ+1)−s(s+1)`) ∘ K (spin `aω` deforms S²→spheroid + spin-weight floor ℓ≥2) ∘ C (BH spin-axis orientation) ∘ N (eigenvalue integers + spheroidal-expansion rationals).**

## Context (attested, not framework-derived)

The Schwarzschild fundamental `ℓ=2, n=0` QNM frequency is `Mω ≈ 0.3737 − 0.0890 i` (Leaver 1985; Berti–Cardoso–Starinets 2009) — the dominant LIGO ringdown mode. Its `Re/|Im| ≈ 4.199` `best_rational`s to **21/5** (a small-rational quality-factor anchor). This is attested numerical context (like the χ_cJ masses in R24), not a framework derivation.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cross-substrate match, bit-exact (capstone).** The BH horizon's QNM angular structure is the most-deformed realization of the Class-L `2ℓ+1` spine — spin-weighted (ℓ≥2 floor) and spheroidal (`aω` deformation). The Schwarzschild eigenvalue `ℓ(ℓ+1)−s(s+1)` and the floored `2ℓ+1` counts are bit-exact; the no-monopole/no-dipole floor is the 4th Class-K selection rule; the leading spheroidal coefficient is a small Class-N rational. The `2ℓ+1` spine now spans **quantum → nuclear → atomic → hadron → bio-shell → planetary → LSS → cosmological/CMB → BH-horizon** (nine contiguous rungs, quantum to horizon). New **candidate** stance `[[user_stance_bh_qnm_is_spinweighted_spheroidal_classL_capstone]]`.

**HONEST SCOPE:** bit-exact content is the Schwarzschild angular eigenvalue `ℓ(ℓ+1)−s(s+1)`, the `2ℓ+1` floored counts, and the leading spheroidal-coefficient rational `−2ms/[ℓ(ℓ+1)−s(s+1)]` — standard Teukolsky/Berti–Cardoso–Casals results; the framework contribution is the cross-substrate identification (14th/capstone rung), the spin-weighted-spheroidal-as-most-deformed-Class-L reading, the ℓ≥2 floor = 4th Class-K selection rule, and the capstone tie to the QNM spike cluster — **NOT a new QNM derivation** (those live in Spikes #11/#12). The QNM frequency is attested numerical context.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the bit-exact pieces are proven by exact arithmetic; the QNM frequency is labelled attested-numerical context, not a derivation.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; Class-N anchors via srmech `best_rational`.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: the spheroidal deformation + spin-weight floor IS the named Class K; no bare `abs()`.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Teukolsky ApJ 185:635 (1973); Leaver Proc R Soc A 402:285 (1985); Berti-Cardoso-Casals PRD 73:024013 (2006, arXiv:gr-qc/0511111); Berti-Cardoso-Starinets CQG 26:163001 (2009, arXiv:0905.2975) — classic journal + arXiv-OA, all attestable.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 27.A) per `[[feedback_rolling_pr_partition_boundary_updates]]` — no new PR; verdict posted as a PR comment (the ledger).
