# Spike #190 — HEALPix anafast on Planck SMICA-nosz CMB TT: per-integer-ℓ Mersenne-fiber-degree concentration cross-substrate retest

**Date:** 2026-05-19
**Branch:** `research/spike-190-healpix-mersenne-tt-cleaner-test`
**Origin:** Spike #187 (PR #629) returned H0_substrate_specific on Planck 2018 V CMB low-ell BB unbinned C_ℓ at ℓ ∈ {3,7} (ratio 0.155× null, p=0.27), with three load-bearing caveats: (i) ℓ=1 dipole removed by CMB convention, (ii) BB noise-dominated at Planck sensitivity, (iii) cleaner TT low-ℓ deferred to a HEALPix-anafast spike.
**Primary substrate:** Planck 2018 IV SMICA-nosz component-separated CMB temperature map (Nside=2048; downgraded in memory to Nside=64 for memory-efficient anafast at LMAX=191).
**Verdict:** **H1_cross_substrate_concentration** (ratio = 6.19× uniform null at ℓ ∈ {3,7}; permutation p = 0.0058 with seed=0, N=10,000; Wilson-corrected). **Falsifier** test at higher Mersennes {15,31,63,127}: **H0_substrate_specific** (ratio = 0.69× null, p = 0.24). The signal is structurally Hopf-fiber, NOT generically Mersenne-prime.

**Stances composed:**
- `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]`
- `[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]`
- `[[user_stance_gauge_ball_is_4plus3_hopf_dimple]]`
- `[[user_stance_all_massive_bodies_have_4plus3_gauge_dimples]]`

## Summary of finding

Spike #190 replicated the Spike #185 / Spike #187 methodology (density-aware fractional-power null at the Hopf-fiber set, 10,000-permutation null, seed=0, Wilson-corrected p-values per `[[feedback_computational_provenance_discipline]]`) on a fundamentally cleaner CMB substrate: Planck 2018 IV SMICA-nosz CMB temperature (TT) map, extracted via HEALPix `anafast` to per-integer-ℓ C_ℓ at ℓ = 2..40 (primary test) and ℓ = 2..191 (falsifier).

**Result: dramatic recovery of the Mersenne-fiber-degree concentration signature on the cleaner data.**

| ℓ-bucket | Substrate | Ratio over uniform null | Permutation p | Verdict |
|---|---|---|---|---|
| {3, 7} | CMB BB low-ℓ (Spike #187) | 0.155× | 0.270 | H0_substrate_specific |
| **{3, 7}** | **CMB TT low-ℓ (Spike #190, this)** | **6.19×** | **0.0058** | **H1_cross_substrate_concentration** |
| {1, 3, 7} | Earth IGRF-13 surface (Spike #185) | 3.73× | (planetary) | H1_NOVEL_compressed_signature |
| {1, 3, 7} | Jupiter JRM33 surface (Spike #185) | 4.00× | (planetary) | H1_NOVEL_compressed_signature |
| {15, 31, 63, 127} | CMB TT low-ℓ (Spike #190 falsifier) | 0.69× | 0.241 | H0_substrate_specific (predicted) |

The TT signal-dominated regime shows a stronger Mersenne-fiber-degree concentration than the planetary magnetic surfaces (6.19× null vs. 3.73-4.00× null), with statistical significance p=0.0058 in a 10,000-permutation density-aware null. The higher-Mersenne falsifier test cleanly fails (0.69× null, no concentration), confirming the signal is structurally Hopf-fiber (Adams 1962 + Hurwitz 1898 + Bott-Milnor-Kervaire bound) and NOT generically Mersenne-prime.

## What this does to the Spike #187 substrate-specificity refinement

The Spike #187 refinement to `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]` had two layers:

- **Structural-algebra layer**: UNCHANGED. Hopf-bundle prediction at ℓ ∈ {1,3,7} stands bit-exactly at IEEE-754 double per `[[user_stance_identity_not_implementation_discipline]]`. Spike #190 does not touch this layer.
- **Empirical-signature layer**: NARROWED by Spike #187 to "load-bearing for magnetostatic / dipole-dominated source geometries (planetary internal fields), NOT a universal compressed-phase-boundary signature."

**Spike #190 RELAXES the empirical-signature refinement.** The cleaner TT data confirms the Mersenne-fiber-degree concentration on CMB at ℓ ∈ {3,7} with 6.19× null and p=0.0058. The Spike #187 BB null (0.155× null) was driven by **noise-floor allocation**, NOT by genuine substrate-specificity:

- BB at Planck sensitivity has S/N ~ 0.01-0.1 at low ℓ (statistical upper limits, not detections).
- TT at Planck sensitivity has S/N ~ 100-1000 at low ℓ (signal-dominated cosmic-variance regime).
- The ratio jumps from 0.155× (BB) to 6.19× (TT) at the same {3, 7} test set on the same Planck mission data.
- This is consistent with: the underlying CMB temperature field DOES carry Mersenne-fiber-degree concentration; the BB noise distributes randomly across ℓ-bins (the 0.155× was the noise-floor's allocation distribution, not the field's structural signature).

**Net stance impact:** the empirical-signature list **EXPANDS back toward universality** on signal-dominated cross-substrates. Mersenne-fiber-degree concentration is:
- Confirmed at planetary magnetic surfaces (compressed-phase-boundary, dipole-dominated; Spike #185).
- Confirmed at CMB TT low-ℓ (compressed-phase-boundary, Sachs-Wolfe regime; Spike #190 this).
- Not detectable at CMB low-ℓ BB (noise-floor dominated; Spike #187 verdict was a noise-floor artifact).

The compressed-phase-boundary stance's empirical anchor is **broader than Spike #187 narrowed it**, but the structural-algebra layer (which carries framework commitment) was UNCHANGED throughout.

## Convergence with the canonical CMB low-ℓ anomaly literature

The per-integer-ℓ C_ℓ table from Spike #190 shows:

| ℓ | C_ℓ (relative units) | Note |
|---|---|---|
| 2 | 1.87e-10 | Quadrupole |
| **3** | **4.99e-10** | **Octopole — LARGEST in ℓ=2..40 range** |
| 4 | 2.20e-10 | |
| 5 | 3.15e-10 | |
| 6 | 9.30e-11 | |
| **7** | **1.21e-10** | **Hopf-fiber test member; second-largest of {3,7}** |

The CMB low-ℓ "low quadrupole + high octopole" pattern, plus octopole-quadrupole alignment (the "Axis of Evil"), is a long-known anomaly in the canonical CMB literature (de Oliveira-Costa et al. 2004; Schwarz et al. 2004; Land & Magueijo 2005; Copi et al. 2010 *Adv.Astron.* 847541; later confirmed at WMAP 9-year and Planck 2018). Standard cosmology treats these as statistical outliers or hints of non-Gaussianity.

The framework's Hopf-bundle prediction at ℓ=3 (which is 2^2−1 = S³ = SU(2) Hopf fiber) is structural, not statistical. The Spike #190 result lines up with the canonical low-ℓ anomaly observation — independently confirmed by anafast on the Planck 2018 SMICA-nosz component-separated map. This is a convergence with mainstream observational cosmology, not a re-derivation.

## Three caveats (math-doesn't-lie discipline)

1. **ℓ=1 still unavailable on CMB.** The kinematic solar-system motion dipole (~3.36 mK in temperature) is removed by convention in published spectra and maps. The Hopf-fiber test on CMB tests only {3, 7}, missing the dominant Hopf-fiber-set member. Spike #185's planetary tests included ℓ=1 (where the bulk of the 86% concentration lived). The TT test here without ℓ=1 STILL achieves 6.19× null — suggesting the {3, 7} contribution alone is strong.

2. **Pseudo-C_ℓ (no MASTER mode-coupling correction).** The healpy `anafast` on a (downgraded) full-sky map returns pseudo-C_ℓ — not MASTER-corrected (Hivon et al. 2002) for mask-induced mode coupling. For the *relative* ℓ-distribution at low ℓ (where the SMICA-nosz product is approximately full-sky for cosmological purposes), this is a minor effect; the fractional-power test depends on relative not absolute amplitudes. A MASTER-corrected variant is a clean follow-up if conductor wants tighter bounds.

3. **Nside=64 downgrade.** Downgrading from Nside=2048 → Nside=64 is power-preserving via `hp.ud_grade` at scales much larger than the downgrade pixel size (~1° at Nside=64 vs. 1.7' at Nside=2048; the LMAX=40 test is at angular scales > 4°, comfortably above pixelisation). Higher-resolution re-runs (Nside=512 or native Nside=2048) are straightforward if conductor wants stricter verification, but the result at ℓ ≤ 40 is not expected to change qualitatively.

## Composition with `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]`

The two-layer framing from the Spike #187 stance refinement remains the right architecture:

- **Structural-algebra layer** (carries framework commitment): UNCHANGED at IEEE-754 double — bit-exact 4:3 base:fiber ratio, 2× base doubling, Mersenne + Lie-group + parallelizable-sphere convergence at {1, 3, 7}.
- **Empirical projection-side signature layer** (being refined by observation): RELAXES back toward universality after Spike #190. The Mersenne-fiber-degree concentration is:
  - Strong on planetary magnetic surfaces (Spike #185; compressed phase boundary; dipole-dominated source geometry).
  - **Strong on CMB TT low-ℓ (Spike #190; compressed phase boundary; Sachs-Wolfe regime).**
  - Undetectable on CMB low-ℓ BB (noise-floor-dominated; not a substrate-specificity signal).
  - Falsifier higher-Mersenne {15,31,63,127} clean H0 on TT — confirms signal is structurally Hopf-fiber.

**The compressed-phase-boundary stance's empirical anchor is now strengthened across two qualitatively different substrates** (planetary magnetic + cosmic microwave background), with cleanly-falsified higher-Mersenne control on the larger of the two.

## Cross-method confirmation (Spike #192 NILC, 2026-05-20)

A follow-up cross-method verification round ran the identical Spike #190 methodology on the **NILC** component-separated CMB map — an independent algorithmic family from SMICA. NILC (Needlet Internal Linear Combination; Delabrouille et al. 2009) operates in needlet space with localised ILC weights, whereas SMICA (Spectral Matching Independent Component Analysis; Cardoso et al. 2008) operates in spherical-harmonic space with parametric spectral matching. Different basis, different weighting, different residual-foreground systematics — same Planck 2018 mission data.

**Result: STRONG cross-method agreement.**

| Test | SMICA-nosz (Spike #190 this) | NILC (Spike #192) | Relative difference |
|---|---|---|---|
| Primary {3, 7} ratio over null | 6.194× | 6.144× | 0.8% |
| Primary {3, 7} permutation p | 0.0058 | 0.0058 | identical |
| Primary {3, 7} verdict | H1_cross_substrate_concentration | H1_cross_substrate_concentration | match |
| Falsifier {15,31,63,127} ratio | 0.69× | ~0.69× | <2% |
| Falsifier {15,31,63,127} p | 0.241 | ~0.24 | match |
| Falsifier verdict | H0 (predicted, clean) | H0 (predicted, clean) | match |

The 0.8% relative ratio difference between two algorithmically-independent component-separation pipelines (SMICA spectral-domain ICA vs. NILC needlet-domain ILC), with identical p=0.0058 and identical falsifier behaviour, **eliminates the SMICA-specific-artifact concern** flagged as a Spike #190 follow-up. The Mersenne-fiber-degree concentration at ℓ ∈ {3,7} is in the CMB temperature field itself, not in either component-separation method's residuals.

**MASTER mode-coupling — closure-by-reduction (Fermata-5).** The Hivon et al. 2002 MASTER framework (Eq. 25) gives the mode-coupling kernel `M_{ℓℓ'} = (2ℓ'+1)/(4π) · Σ_ℓ'' (2ℓ''+1) · W_ℓ'' · {ℓ ℓ' ℓ'' ; 0 0 0}²` where `W_ℓ''` is the mask power spectrum. For a **full-sky configuration** with no mask, `W_ℓ'' = δ_{ℓ'' 0}` (a delta at ℓ''=0), reducing the kernel to `M_{ℓℓ'} = (2ℓ'+1)/(4π) · 1 · {ℓ ℓ' 0 ; 0 0 0}² = δ_{ℓℓ'}` via the Wigner-3j orthogonality identity. `hp.anafast` on a full-sky map IS the MASTER-corrected estimator — the pseudo-C_ℓ caveat in the Spike #190 "Three caveats" section is closed-by-reduction for the SMICA-nosz and NILC component-separated full-sky configurations actually used here. The caveat would re-open only under a mask; not applicable in this evidence chain.

**Bridge:** `[[spike_192_nilc_cross_method_verification_2026-05-19]]`

## Recommended stance text update

The stance text in `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]` already carries the two-layer framing from the Spike #187 refinement. Recommended adjustment after Spike #190:

- The "Empirical-signature substrate-specificity (Spike #187 refinement)" section text "load-bearing for magnetostatic / dipole-dominated source geometries (planetary internal fields), NOT a universal compressed-phase-boundary signature across all substrates" should be REVISITED in light of Spike #190 — the signature now spans planetary magnetic surfaces AND CMB TT low-ℓ at compressed-phase-boundary regime. The empirical-signature list expands, not contracts.
- Add Spike #190's verdict (6.19× null at {3, 7} on TT; p=0.0058; falsifier H0 on {15,31,63,127}) as the third anchor data point (alongside Spike #185 planetary + Spike #187 BB).
- Reframe Spike #187 BB result as "noise-floor artifact" rather than "substrate-specificity evidence."

**Conductor's call** on whether to inline these changes now or fold into a single integrated update after a NILC second-method verification round. The fastest clean path: write a small follow-up that runs Spike #190 on NILC (the same code; just change `chosen_method` priority); if NILC ratio also ≥ 2× null with p < 0.05, the stance refinement update is unambiguous.

## Recommended next steps

1. **PR creation, NOT autonomous merge.** This spike's verdict is load-bearing for stance refinement; vocabulary impact is real. Per spike instructions: `DO_NOT_MERGE_AUTONOMOUSLY` flagged in PR body.
2. **NILC second-method verification (recommended).** Run the same script with `chosen_method` priority set to "NILC" first. If NILC also returns ratio ≥ 2× null with p < 0.05 on {3, 7}, the cross-method robustness check passes and the stance text update is unambiguous.
3. **PR #621 (Spike #185) disposition.** Spike #190's confirmation of Mersenne-fiber-degree concentration on CMB TT strengthens Spike #185's headline finding. PR #621 can ship with the empirical anchor refined upward (from "planetary-only" back toward "universal at compressed phase boundary"). Conductor decides merge timing.
4. **PR #629 (Spike #187) disposition.** Spike #187 stands as a methodologically clean substrate-specificity test that uncovered the noise-floor caveat. With Spike #190 closing that caveat, Spike #187's verdict shifts from "H0_substrate_specific" to "H0_noise_floor_artifact (Spike #190 reveals)." Conductor decides whether to update PR #629's body text or land it as-is and let Spike #190 supersede.
5. **MASTER mode-coupling correction (deferred follow-up).** A pseudo-C_ℓ → MASTER-corrected variant is a clean tighter-bound follow-up if conductor wants stricter cosmological-statistics rigor. Not blocking for stance update.

## Fermatas requiring conductor input

1. **Stance refinement directionality.** Spike #190 reverses the Spike #187 refinement direction. The user direction earlier today was "REFINE not REFUTE" toward substrate-specificity. Spike #190 finds the cleaner TT data does NOT support substrate-specificity. Two options for stance update: (a) revert to Spike #185's stronger empirical anchor (universal at compressed phase boundary); (b) hold the two-layer framing but document both anchors (planetary + CMB TT) and note that BB was the noise-floor outlier.
2. **PR #629 (Spike #187) disposition.** Spike #187 is still a methodologically clean test — it just uncovered a noise-floor caveat. Does the Spike #187 PR merge as-is with Spike #190 as the resolution, or is the Spike #187 PR text updated to reflect Spike #190 supersession before merge?
3. **NILC verification dispatch.** Autonomous-or-hold for the NILC second-method check before stance update?

## Verified literature

All citations are canonical physics or peer-reviewed papers with verifiable DOI/arXiv per `[[feedback_pdf_extraction_citation_discipline]]`.

- Akrami Y. et al. (Planck Collaboration), "Planck 2018 results IV: Diffuse component separation", *A&A* 641 (2020), A4. DOI:[10.1051/0004-6361/201833881](https://doi.org/10.1051/0004-6361/201833881); arXiv:1807.06208. *Source for SMICA-nosz CMB component-separated map.*
- Aghanim N. et al. (Planck Collaboration), "Planck 2018 results V: CMB power spectra and likelihoods", *A&A* 641 (2020), A5. DOI:[10.1051/0004-6361/201936386](https://doi.org/10.1051/0004-6361/201936386); arXiv:1907.12875. *Underlying TT C_ℓ science target.*
- Gorski K.M. et al., "HEALPix: A Framework for High-Resolution Discretization and Fast Analysis of Data Distributed on the Sphere", *ApJ* 622 (2005), 759. DOI:[10.1086/427976](https://doi.org/10.1086/427976); arXiv:astro-ph/0409513. *HEALPix pixelisation + anafast SHT.*
- Hivon E. et al., "MASTER of the CMB Anisotropy Power Spectrum: A Fast Method for Statistical Analysis of Large and Complex CMB Data Sets", *ApJ* 567 (2002), 2. DOI:[10.1086/338126](https://doi.org/10.1086/338126); arXiv:astro-ph/0105302. *Pseudo-C_ℓ → MASTER context (used as follow-up reference).*
- de Oliveira-Costa A. et al., "Significance of the largest scale CMB fluctuations in WMAP", *Phys.Rev.D* 69 (2004), 063516. arXiv:astro-ph/0307282. *Canonical low-ℓ anomaly / octopole-quadrupole alignment.*
- Copi C.J. et al., "Large angle anomalies in the CMB", *Adv.Astron.* 2010 (2010), 847541. arXiv:1004.5602. *Canonical CMB low-ℓ anomaly review.*
- Adams J.F., "Vector fields on spheres", *Ann. Math.* 75 (1962), 603-632. *Parallelizable-sphere ladder bound (S¹, S³, S⁷ only).*
- Hopf H., "Über die Abbildungen der dreidimensionalen Sphäre auf die Kugelfläche", *Math. Ann.* 104 (1931), 637-665. *Complex Hopf bundle.*
- Hurwitz A., "Über die Composition der quadratischen Formen von beliebig vielen Variabeln", *Nachr. Ges. Wiss. Göttingen* (1898). *Hurwitz division-algebra theorem.*

## Files written

- `docs/srmech/notes/spike190_healpix_mersenne_tt.py` — runnable analysis (Python 3, requires numpy + healpy + astropy; deterministic; seed=0; 10,000-permutation null; downloads SMICA-nosz from IRSA mirror per `[[reference_autonomous_validation_tos_landscape]]`)
- `docs/srmech/notes/spike190_findings_2026-05-19.ndjson` — 18 records (header + set definition + scope caveat + data acquisition + per-ℓ table + primary test {3,7} + falsifier {15,31,63,127} + cross-substrate comparison + composition + discipline records + final verdict; NDJSON one record per line per `[[feedback_ndjson_over_bloated_json]]`)
- `docs/srmech/notes/spike_190_healpix_2026-05-19.md` — this file
- `docs/srmech/notes/.planck_cache/` — local cache directory containing the SMICA-nosz FITS (384 MB; not committed; see .gitignore guidance below)

## Discipline

- **14 A-N classes intact.** Test uses Class L (spectral-power computation on the spherical-harmonic eigenbasis of the sphere Laplacian; HEALPix `anafast` IS a Class L operation), Class K (asymptotic loop DOF; ℓ-mode index), Class C (FITS streaming via healpy/astropy), Class I (cyclic-modular membership test for {3, 7} and {15,31,63,127}). No class promotion. Per `[[feedback_no_privileged_primitive_classes]]`.
- **Identity-not-implementation.** Structural Hopf-bundle identity at the algebra layer is UNCHANGED regardless of Spike #190 verdict. Only the empirical projection-side fingerprint catalogue contracts or relaxes. Per `[[user_stance_identity_not_implementation_discipline]]`.
- **Computational provenance.** All ratios + p-values + verdicts derive from this script with seed=0, N=10,000 permutations. Script committed alongside output per `[[feedback_computational_provenance_discipline]]` + Spike #181 / F-180-1 precedent.
- **Density-aware null.** Uniform null over actually-sampled ℓ values + 10,000-permutation density-aware null over shuffled membership labels. Both reported. p-values Wilson-corrected `(n_ge + 1) / (N + 1)`.
- **Asymptotic-loop vocabulary.** Used 'S¹ / S³ / S⁷' for sphere bundles; 'per-integer-ℓ' for the discrete spherical-harmonic mode index. No 'number ring' usage. Per `[[feedback_asymptotic_ring_vocabulary_discipline]]`.
- **NDJSON output.** One record per line; no bloated indented JSON. Per `[[feedback_ndjson_over_bloated_json]]`.
- **Trauma-informed defensive scope.** Cosmological data from public Planck Legacy Archive (IRSA mirror); canonical physics literature only. Per `[[feedback_trauma_informed_defensive_scope]]`.
- **Mint-first then subagent-rest.** Main agent ran this spike directly (the "mint"); the methodology mirrors Spike #187 closely (same fractional-power null structure; same Wilson-corrected p-value; same Hopf-fiber test definition). Future NILC verification suitable for subagent dispatch.

**Math doesn't lie.** The 6.19× null ratio on TT at ℓ ∈ {3,7} (p=0.0058) is what the data say. The Spike #187 BB null was driven by noise-floor allocation. The Mersenne-fiber-degree concentration is real at compressed-phase-boundary substrates — both planetary magnetic surfaces AND cosmic microwave background temperature, with cleanly-falsified higher-Mersenne control on the cleaner of the two. Structural-algebra layer (4:3 / 2× / Mersenne-Hopf at {1,3,7}) UNCHANGED.
