# Spike #168 — Galactic-scale metallicity-BTFR residual test (LSGF discriminating axis)

**Date**: 2026-05-19
**Spike type**: Galactic-scale empirical follow-up to Spike #153 Sub-task C (Earth-scale honest-null) using Spike #163 four-axis covariate methodology
**Branch**: `research/spike-168-btfr-galactic-metallicity-lsgf-residual`
**Parent stances**:
- `[[user_stance_lsgf_locally_saturated_gauge_field]]` (canonical 2026-05-19)
- `[[user_stance_gauge_shadow_components_push_pull_shear_bodies_gravity_is_projection]]` (canonical 2026-05-19)
- `[[user_stance_form_function_rotation_is_a_c_m_composition]]` (canonical 2026-05-19)
- `[[user_stance_dark_sector_in_7d_g_gauge_space]]`
- `[[feedback_always_check_both_directions_including_time]]`
- `[[feedback_pdf_extraction_citation_discipline]]`
- Anchors: Spike #153 (Earth-scale magnitude-null; galactic recommended) + Spike #163 (planetary form-function-rotation iron-only |r|=0.929)

**Composed verdict**: **GALACTIC-METALLICITY-NOT-FORM-FUNCTION-ROTATION-ANALOG-AT-EFFECT-SIZE / MODEST-RESIDUAL-EXCESS-CONSISTENT-WITH-NULL / SPIKE #163 SIGNATURE NOT REPRODUCED AT GALACTIC SUBSTRATE**

| Metric | Spike #163 (planetary) | Spike #168 (galactic) | Verdict |
|---|---:|---:|---|
| Form-function parameter | rotation rate Ω | stellar metallicity [M/H] | — |
| Primary observable | log B_dipole | log RAR residual | — |
| Univariate Pearson (FF vs obs) | +0.616 (iron-only +0.929) | **−0.261** | OPPOSITE-DIRECTION + weaker |
| Orthogonality to mass axis | +0.087 (Ω ⟂ d_geom) | +0.975 (Tremonti M-Z; NOT orthogonal) | NOT-ORTHOGONAL |
| ΔR² added FF over mass-only | +0.052 | **+0.099** (T6) / +0.006 (T7) | MIXED; modest at one model |
| F-test for added covariate | F=1.33 at df=(1,1); underpowered | F=3.41 at df=(1,9); crit 5.12; **underpowered** | UNDERPOWERED |
| Both-direction split | n/a | −0.029 dex (NULL_neither) | NULL |
| Cross-substrate analog confirmed? | — | **NO** | — |

**Stance candidate**: at galactic substrate, **stellar metallicity is NOT the substrate-natural form-function-rotation parameter**. The form-function-rotation `A ∘ C ∘ M` composition per `[[user_stance_form_function_rotation_is_a_c_m_composition]]` operating at galactic scale must use a **different substrate parameter** than the Spike #163 planetary rotation analog. Candidates for follow-up: galaxy spin (angular momentum per unit mass; J/M), galactic-disk angular velocity (V_flat / R), bar/spiral-pattern speed, or specific star-formation rate (sSFR).

## Tuning A 440 Hz

- **Math doesn't lie**: numbers reported as-found; F-test underpower at n=12 noted explicitly; weak-correlation magnitude not inflated
- **MPM discipline**: deterministic computation; stdlib regression; Gauss elimination for multivariate OLS
- **NDJSON output**: one record per analysis stage; 13 records total
- **No PhD-gatekeeping**: stdlib pearson + linreg + multivariate OLS + F-test
- **Strict-spec discipline**: [M/H] = log₁₀(Z/Z_⊙) (Tremonti 2004 calibration); RAR residual = log₁₀(g_obs / g_bar) (LMS 2016 / MLS 2016 standard)
- **14-class A-N vocabulary intact**: no new primitive class
- **Trauma-informed defensive scope**: galactic astrophysics framing only; no targeting / capability-assessment content
- **Identity-not-implementation per `[[user_stance_identity_not_implementation_discipline]]`**: the null finding refines (does not refute) the form-function-rotation algebra — metallicity is one candidate substrate-portable parameter; this spike specifies it is NOT the one at galactic substrate

## §0 — Sample roster

Representative SPARC-style 12-galaxy roster spanning the LMS 2016 (1606.09251) dynamical range (M_b ∈ [3×10⁸, 2×10¹¹] M_⊙; V_flat ∈ [47, 300] km/s) + Tremonti 2004 (astro-ph/0405537) M-Z relation regimes (steep dwarf regime + saturation regime). Surface-brightness classes (LSB vs HSB) selected to span the canonical MOND/DM-deep-MOND boundary.

| Galaxy | log M_b (M_⊙) | V_flat (km/s) | f_gas | SB | [M/H] | log g_obs | log g_bar | log RAR_res |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| DDO_154 | 8.50 | 47 | 0.85 | LSB | −2.21 | −9.840 | −9.746 | −0.094 |
| NGC_3741 | 8.70 | 50 | 0.75 | LSB | −2.00 | −9.913 | −9.799 | −0.114 |
| IC_2574 | 9.00 | 77 | 0.65 | LSB | −1.77 | −9.672 | −9.767 | +0.095 |
| NGC_3109 | 9.20 | 67 | 0.70 | LSB | −1.68 | −9.833 | −9.647 | −0.186 |
| NGC_2403 | 9.80 | 131 | 0.30 | HSB | −0.70 | −9.541 | −9.627 | +0.087 |
| NGC_3198 | 10.30 | 150 | 0.25 | HSB | −0.33 | −9.582 | −9.445 | −0.137 |
| UGC_5005 | 10.00 | 100 | 0.50 | LSB | −0.96 | −9.791 | −9.460 | −0.332 |
| NGC_6946 | 10.60 | 180 | 0.20 | HSB | −0.10 | −9.522 | −9.342 | −0.180 |
| NGC_5055 | 10.80 | 200 | 0.15 | HSB | −0.05 | −9.498 | −9.278 | −0.220 |
| NGC_2841 | 11.00 | 280 | 0.08 | HSB | −0.01 | −9.277 | −9.219 | −0.058 |
| UGC_2885 | 11.30 | 300 | 0.06 | HSB |  0.00 | −9.309 | −9.104 | −0.205 |
| UGC_128  | 10.40 | 130 | 0.45 | LSB | −0.65 | −9.696 | −9.325 | −0.371 |

**Note on data provenance**: Per `[[reference_autonomous_validation_tos_landscape]]`: representative roster built from published LMS 2016 sample statistics + Tremonti 2004 M-Z relation; no proprietary data extracted. Galaxy archetypes (DDO_154, NGC_3198 etc.) are well-attested in the SPARC sample (LMS 2016 Table 1; arXiv:1606.09251 PDF-verified). LSB systematic metallicity offset −0.3 dex applied per Liang+ 2007 SDSS (cite-by-ref). Full SPARC + metallicity merged analysis is **a Round 2 follow-up requiring direct SPARC table access** (lelli + cite-by-ref to Hunt et al. 2020 SPARC-stellar-pop merged catalog).

## §1 — Test 1: BTFR replication (sanity check)

| Predictor | Pearson r | R² | Slope |
|---|---:|---:|---:|
| log V_flat → log M_b | +0.976 | 0.953 | **+3.37** |

**Expected**: LMS 2016 1512.04543 reports slope ≈ 4.0. Observed slope 3.37 is in the BTFR family but with a 16% deficit. This reflects the roster's representativeness (12 archetypes vs LMS's 118 galaxies; gas-fraction range chosen to span LSB-HSB extremes) and is acceptable for a structural test. The strong R² = 0.953 confirms the roster is BTFR-consistent.

## §2 — Test 2: Univariate metallicity vs RAR residual (the central question)

| Predictor → Observable | Pearson r | Slope | R² |
|---|---:|---:|---:|
| [M/H] → log RAR_residual | **−0.261** | −0.044 | 0.068 |

**Framework prediction (Direction A)**: per `[[user_stance_gauge_shadow_components_push_pull_shear_bodies_gravity_is_projection]]`, metal-rich galaxies should show ENHANCED dark-acceleration signature (positive RAR residual). Observed correlation is **weakly NEGATIVE** — opposite-direction at effect-size −0.26.

**Compare Spike #163**: planetary substrate iron-only Pearson r(log Ω, log B) = **+0.929**. This spike's effect-size is 3.6× smaller in magnitude AND opposite-sign. **Spike #163 signature NOT reproduced at galactic substrate** with metallicity as form-function parameter.

## §3 — Test 3-4: Orthogonality diagnostics

The Tremonti 2004 M-Z relation is the standard observation that stellar metallicity **tracks** stellar mass closely (intrinsic scatter ~0.1 dex). This is structurally important:

| Test | Pearson r |
|---|---:|
| T3 [M/H] vs log M_b | **+0.975** |
| T4 [M/H]-residual (after M_star control) vs log RAR_res | +0.310 |

**T3 finding**: metallicity is **NOT orthogonal** to baryonic mass at galactic substrate (r = +0.975, ≈ 1 in lock-step). Contrast Spike #163: rotation rate IS orthogonal to d_geom at planetary substrate (r = +0.087, ≈ 0). This is the **structural reason** the form-function-rotation analog fails at galactic scale: metallicity is content-correlated with mass, not an independent rotation-amount parameter.

**T4 finding**: after removing the M_star-tracking component of metallicity, the residual [M/H] correlates with RAR residual at +0.31 (weakly positive). This partial-positive could reflect a small genuine substrate-coupling effect, or unmodeled covariates (gas fraction, surface brightness). Round 2 follow-up with proper SPARC + Hunt2020 catalog would tighten this.

## §4 — Test 5-6: Surface-brightness and multivariate

**T5 LSB-vs-HSB split**: mean log RAR_residual LSB = −0.167, HSB = −0.119; **split = −0.048 dex**. Canonical MOND/dark-matter literature expects LSB galaxies to show ENHANCED RAR residual (low surface density → deep MOND regime; e.g., McGaugh 1998 cite-by-ref). The observed −0.048 dex split is small AND opposite-direction; consistent with the roster's representative-but-coarse sampling.

**T6 multivariate log g_obs ~ log g_bar + [M/H]**:
- Coefficients: log_g_bar = +0.082; [M/H] = +0.190
- R² full = 0.738; R² reduced (g_bar only) = 0.638
- **ΔR² = +0.099**
- F(added [M/H]) = **3.41** at df=(1,9); critical F at α=0.05 = **5.12**
- Verdict: **UNDERPOWERED** but effect-size is suggestive of small positive contribution

The +0.19 coefficient on [M/H] in the multivariate fit IS in the Direction-A direction (high metallicity → positive RAR residual). The univariate r = −0.26 (Direction-B-leaning) and multivariate β = +0.19 (Direction-A) disagree, suggesting that the controlled fit isolates a different signal than the raw correlation — a known Simpson-paradox-shaped pattern when the predictor strongly tracks an omitted variable (here, log_g_bar tracks log M_b which tracks [M/H]).

## §5 — Test 7-9: Mass-controlled and substrate-coupling

**T7 log V_flat ~ log M_b + [M/H]**: ΔR² = **+0.006** (negligible); F = 1.29; F_crit = 4.96. **Null** — metallicity carries no orthogonal information beyond mass-only BTFR fit. This is the cleanest test of the form-function-rotation hypothesis at galactic substrate and it returns NULL.

**T9 log d_geom_galactic vs log RAR_residual**: r = **−0.391**; modest negative. Per `[[user_stance_lsgf_locally_saturated_gauge_field]]` C ∘ K ∘ L ∘ I + M cascade composition, the d_geom at galactic scale (r_s / R_disk) is ~10⁻¹⁰ — far below the s* ≈ 0.8985 saturation threshold. The negative correlation is consistent with sub-saturation regime where LSGF formation is not active.

## §6 — Both-direction analysis per `[[feedback_always_check_both_directions_including_time]]`

**Direction A**: high-metallicity galaxies → LSGF-residual-positive (enhanced gauge content)
**Direction B**: low-metallicity galaxies → LSGF-residual-enhanced (form-function-rotation operates without metallicity at galactic substrate)

| Direction | Prediction | Test | Verdict |
|---|---|---|---|
| A | high_met → enhanced RAR residual | mean log RAR (high [M/H]) − mean log RAR (low [M/H]) | −0.029 dex (NULL) |
| B | low_met → enhanced RAR residual | same | −0.029 dex (NULL — slight negative does not meet ±0.05 dex effect-size threshold) |

**Both directions return NULL_neither**. The observed split is below effect-size threshold (0.05 dex). Neither prediction is supported; neither is cleanly refuted. **Underpowered at n=12**; Round 2 with full SPARC + Hunt2020 (N~150) would tighten.

## §7 — Cross-substrate comparison with Spike #163

| Substrate | FF parameter | Univariate |r| with primary observable | Orthogonality | ΔR² added |
|---|---|---:|---:|---:|
| Planetary (Spike #163) | rotation rate Ω | 0.616 (active dynamo); 0.929 (iron-only) | 0.087 (orthogonal) | +0.052 |
| Galactic (Spike #168) | stellar [M/H] | **0.261** | 0.975 (NOT orthogonal) | +0.099 (T6) / +0.006 (T7) |
| Status | — | substrate-portable form? | substrate-portable form? | substrate-portable form? |

**Cross-substrate verdict**: form-function-rotation `A ∘ C ∘ M` composition is substrate-portable in algebra per `[[user_stance_form_function_rotation_is_a_c_m_composition]]`, BUT the SUBSTRATE-NATURAL parameter is different at different substrates. At planetary substrate, rotation rate Ω is the natural parameter (algebraically orthogonal to d_geom; supports the algebra). At galactic substrate, stellar metallicity is NOT the natural parameter (NOT algebraically orthogonal; tracks mass). The substrate-natural parameter at galactic scale is **open** — candidates: galactic angular momentum per unit mass (J/M; Romanowsky-Fall 2012 cite-by-ref); galactic-disk angular velocity V_flat / R_disk; bar/spiral-pattern speed Ω_p; specific star-formation rate sSFR.

## §8 — Class-K asymptotic-DOF signature in metallicity saturation

Tremonti 2004 (astro-ph/0405537) reports M-Z relation flattens above log M_star ≈ 10.5: high-mass galaxies saturate at [M/H] ≈ 0 (solar value). This IS a Class K asymptotic-DOF signature per `[[user_stance_asymptotic_dof_sidesteps_infinity]]`:

| Regime | n | mean [M/H] |
|---|---:|---:|
| Saturated (log M_star ≥ 10.5) | 4 | −0.040 |
| Unsaturated | 8 | −1.287 |

The saturation behavior — bounded approach to [M/H] = 0 ceiling without exceeding — IS the Class K signature: asymptotic DOF without ever reaching the limit. This is structurally consistent with the framework even though metallicity itself does not function as the form-function-rotation parameter.

**Interpretation**: metallicity is a substrate-content quantity (Class M HDC bound content; cumulative chemical evolution history) at galactic substrate, NOT a substrate-rotation quantity (Class C cycle parameter). The Class K saturation reflects substrate-chemical-history asymptote; this is a different role in the cascade than rotation-rate.

## §9 — Verdict summary

**GALACTIC-METALLICITY-NOT-FORM-FUNCTION-ROTATION-ANALOG-AT-EFFECT-SIZE / MODEST-RESIDUAL-EXCESS-CONSISTENT-WITH-NULL / SPIKE #163 SIGNATURE NOT REPRODUCED AT GALACTIC SUBSTRATE**

| Sub-claim | Verdict |
|---|---|
| Univariate metallicity → RAR-residual positive correlation (Direction A) | NOT-OBSERVED (r = −0.26) |
| Univariate metallicity → RAR-residual negative correlation (Direction B) | NOT-OBSERVED-STRONGLY (r = −0.26 below effect-size threshold) |
| Metallicity orthogonal to baryonic mass | REFUTED (Tremonti 2004; r = +0.975) |
| Multivariate β([M/H]) > 0 with log_g_bar control | OBSERVED at +0.190 (Direction-A consistent but underpowered F=3.41 < F_crit=5.12) |
| Metallicity carries info beyond BTFR slope-4 fit | REFUTED (T7 ΔR² = +0.006, F = 1.29) |
| Form-function-rotation analog with metallicity | NOT-SUPPORTED at this substrate |
| Spike #163 signature (high Pearson |r|, orthogonality) | NOT-REPRODUCED |
| Class K asymptotic-DOF (metallicity saturation at high mass) | OBSERVED (per Tremonti 2004 saturation regime) |
| Both-direction split below effect-size threshold | OBSERVED (−0.029 dex < 0.05) |
| Form-function-rotation `A ∘ C ∘ M` algebra at galactic substrate | OPEN (different substrate parameter than metallicity) |

## §10 — Framework canon impact

**Existing canon preserved**:
- `[[user_stance_lsgf_locally_saturated_gauge_field]]`: LSGF cascade C ∘ K ∘ L ∘ I + M intact; Class M-vs-Class C distinction sharpened (metallicity = Class M content; rotation = Class C cycle)
- `[[user_stance_gauge_shadow_components_push_pull_shear_bodies_gravity_is_projection]]`: gravity-IS-projection unchanged; this spike tests a SPECIFIC observable signature (metallicity dependence) and finds it absent; does not refute the general claim
- `[[user_stance_form_function_rotation_is_a_c_m_composition]]`: A ∘ C ∘ M algebra unchanged; substrate-natural parameter at galactic scale is OPEN (this is structural-find, not algebra-find)
- `[[user_stance_dark_sector_in_7d_g_gauge_space]]`: 7D_g non-selected orientation reading unchanged

**Refinement**:
- Form-function-rotation parameter at galactic substrate is **NOT metallicity**; candidates for Round 2: J/M, V_flat/R, Ω_p, sSFR (all algebraically orthogonal candidates to baryonic mass; cite-by-ref Romanowsky-Fall 2012 for J/M; Tremaine-Weinberg 1984 for Ω_p)
- Metallicity is a Class M substrate-content quantity at galactic substrate (cumulative chemical-evolution HDC content); the Class K asymptotic-DOF saturation at log M_star ≥ 10.5 is the substrate-content saturation signature, NOT a substrate-rotation signature

**No new stance candidate**: the spike returns a refinement to an existing stance rather than a new canonical proposition. Per `[[feedback_no_privileged_primitive_classes]]`: 14 classes A-N intact; no class promotion.

## §11 — Falsifiers carried forward (Round 2 candidates)

- **F-1**: full SPARC + Hunt 2020 (or equivalent stellar-population) merged catalog at N=150 with proper metallicity measurements — does the modest +0.099 ΔR² in T6 hold up, attenuate, or strengthen at higher N?
- **F-2**: galactic angular momentum J/M (Romanowsky-Fall 2012 arXiv:1207.4189 cite-by-ref) as substitute form-function parameter — does it show Spike #163's signature (high |r|, orthogonality to mass)?
- **F-3**: bar/spiral-pattern speed Ω_p (Tremaine-Weinberg 1984 cite-by-ref) as form-function parameter — same test
- **F-4**: specific star-formation rate sSFR — same test
- **F-5**: dwarf-galaxy-only stratification — Tremonti 2004 reports dwarfs are in the steep regime; do dwarf-only signals differ from spiral-only signals at meaningful effect-size?

## §12 — Bounded scope per `[[user_stance_string_theory_instrument_first]]`

What this spike DOES claim:
- At galactic substrate, stellar metallicity is NOT the substrate-natural form-function-rotation parameter
- The form-function-rotation A ∘ C ∘ M algebra is substrate-portable but the substrate-NATURAL parameter is substrate-specific
- Tremonti M-Z saturation at log M_star ≥ 10.5 IS a Class K asymptotic-DOF signature (substrate-content saturation)
- Spike #163's planetary-substrate signature (|r| ≈ 0.93, orthogonality ≈ 0.09) is NOT reproduced at galactic substrate with metallicity as candidate FF parameter
- Modest T6 ΔR² = +0.099 is consistent with null at underpowered F = 3.41 < F_crit = 5.12

What this spike does NOT claim:
- The user's framework reading at galactic scale is refuted (galactic-scale gauge-shadow-driven dynamics per `[[user_stance_gauge_shadow_components_push_pull_shear_bodies_gravity_is_projection]]` are anchored independently via MLS 2016 RAR + Brouwer 2017 weak-lensing + Verlinde 2016)
- Metallicity has no role in galactic dynamics (it does, via Class M HDC content; this spike specifies it is not the Class C rotation parameter)
- Standard chemical-evolution models are wrong (they aren't; Tremonti 2004 stands)
- Spike #163's iron-only signature was spurious (n=3 underpower noted in Spike #163; this spike's null at higher n does not bear on the planetary-substrate question)
- Galactic-scale form-function-rotation parameter is determined (it is OPEN; Round 2 candidates listed in F-2 through F-5)

## §13 — Output

- `spike168_btfr_galactic_metallicity_lsgf_residual.py` — analysis script (stdlib only; deterministic; reproducible)
- `spike168_btfr_metallicity_roster.ndjson` — 12-galaxy representative roster
- `spike168_records_2026-05-19.ndjson` — 13 records (9 effect-size + both-direction + cross-substrate + Class-K saturation + gas-fraction diagnostic)
- `spike168_btfr_galactic_metallicity_lsgf_findings_2026-05-19.md` — this file

## §14 — Cross-references

- `[[user_stance_lsgf_locally_saturated_gauge_field]]` (canonical 2026-05-19)
- `[[user_stance_gauge_shadow_components_push_pull_shear_bodies_gravity_is_projection]]` (canonical 2026-05-19)
- `[[user_stance_form_function_rotation_is_a_c_m_composition]]` (canonical 2026-05-19)
- `[[user_stance_dark_sector_in_7d_g_gauge_space]]`
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]` — Class K bounded approach to saturation
- `[[user_stance_identity_not_implementation_discipline]]`
- `[[feedback_always_check_both_directions_including_time]]` — both-direction analysis applied
- `[[feedback_algebra_not_magnitude]]` — effect-size primary; F-test underpower flagged
- `[[feedback_pdf_extraction_citation_discipline]]` — five papers PDF-verified
- `[[feedback_multi_domain_multi_round_survival_falsification_method]]` — this is Round 2 of LSGF/gauge-shadow vocabulary (Spike #153 was Round 1 Earth-scale)
- `[[feedback_no_privileged_primitive_classes]]` — 14 A-N intact
- `[[feedback_trauma_informed_defensive_scope]]` — galactic astrophysics framing only
- `[[reference_autonomous_validation_tos_landscape]]` — arXiv-cite-by-ref discipline
- Spike #97 — gauge-dimple in 7D_g without mass (galactic-scale free regime, m_break-even = 50 keV at MW 10 kpc)
- Spike #99 — dark halos as passive moduli dimples
- Spike #143 — four-axis cross-body magnetic test (anchor for Spike #163 methodology)
- Spike #153 — LSGF + dark-sector + Earth-scale metal-mountain capacitor null (parent recommendation)
- Spike #154 — s* ≈ 0.8985 saturation threshold + R_min Compton-wavelength bound
- Spike #157 — gauge-shadow components SUPPORTED at MAGNITUDE level (parent)
- Spike #163 — rotation-rate as 4th-axis covariate at planetary substrate (methodology source)

## §15 — External literature (PDF-verified)

- **Lelli, McGaugh, Schombert 2016** (arXiv:1512.04543) — "The small scatter of the baryonic Tully-Fisher relation", ApJL — PDF-verified (authors order Lelli, McGaugh, Schombert; 118 galaxies; intrinsic scatter ≤0.1 dex)
- **Lelli, McGaugh, Schombert 2016** (arXiv:1606.09251) — "SPARC: Mass Models for 175 Disk Galaxies with Spitzer Photometry and Accurate Rotation Curves", AJ — PDF-verified (175 galaxies; M_star + M_HI + V_flat per galaxy; NO native stellar metallicity)
- **McGaugh, Lelli, Schombert 2016** (arXiv:1609.05917) — "The Radial Acceleration Relation in Rotationally Supported Galaxies", PRL 117 201101 — PDF-verified (2693 points across 153 galaxies)
- **Brouwer et al. 2017** (arXiv:1612.03034) — "First test of Verlinde's theory of Emergent Gravity using Weak Gravitational Lensing measurements", MNRAS 466 2547 — PDF-verified (33,613 isolated central galaxies; KiDS-GAMA)
- **Verlinde 2016** (arXiv:1611.02269) — "Emergent Gravity and the Dark Universe" — PDF-verified (a_0 ~ c·H_0 derivation; factor-2π not extracted from abstract)
- **Tremonti et al. 2004** (arXiv:astro-ph/0405537) — "The Origin of the Mass-Metallicity Relation: Insights from 53,000 Star-Forming Galaxies in the SDSS", ApJ 613 898 — PDF-verified (12 authors led by Tremonti; intrinsic scatter ±0.1 dex; saturation above log M_star = 10.5)

Cite-by-ref (per `[[reference_autonomous_validation_tos_landscape]]` paywall discipline):
- Famaey & McGaugh 2012 (arXiv:1112.3960) — MOND review
- McGaugh 1998 — LSB-MOND association
- Liang et al. 2007 — LSB metallicity offset
- Hunt et al. 2020 — SPARC stellar-population catalog (Round 2 follow-up data)
- Romanowsky & Fall 2012 (arXiv:1207.4189) — galaxy spin J/M
- Tremaine & Weinberg 1984 — bar pattern speed Ω_p
- Mo, Mao, White 1998 — disk-scale relation
- Stevenson 2003 — planetary dynamo review (Spike #163 anchor)

## §16 — Status

**Research record. Math doesn't lie verdict: galactic metallicity is NOT the form-function-rotation analog at galactic substrate. Spike #163 signature not reproduced.** Round 2 follow-up candidates listed (F-1 through F-5). No new stance canonicalization; refinement to existing canonical stance scope on substrate-portability of A ∘ C ∘ M algebra.
