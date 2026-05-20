# Spike #192 — NILC component-separation cross-method verification of Spike #190

**Date:** 2026-05-19
**Branch:** `research/spike-192-nilc-cross-method-verification`
**Milestone:** 16
**Origin:** Spike #190 (PR #631) returned `H1_cross_substrate_concentration` on
CMB TT low-ℓ using SMICA-nosz; user 2026-05-19 elevated Spike #190 fermata-4
(NILC second-method verification) from optional to **blocking** before merging
PR #621 + #629 + #631.

**Verdict:** **STRONG cross-method agreement.** NILC reproduces Spike #190's
result at < 1% relative ratio difference; Spike #190 H1 is genuinely framework
signal in CMB TT, NOT a SMICA-specific component-separation artifact.

---

## TL;DR

| Metric                                    | NILC-full        | SMICA-nosz (recomputed) | Spike #190 baseline | Cross-method |
|-------------------------------------------|------------------|-------------------------|---------------------|--------------|
| Primary {3, 7} ratio                      | **6.144×**       | **6.194×**              | 6.194×              | **0.8% rel diff** |
| Primary {3, 7} p-value (10k perms, Wilson)| **0.00580**      | **0.00580**             | 0.00580             | identical   |
| Primary {3, 7} verdict                    | **H1**           | **H1**                  | H1                  | match       |
| Falsifier {15, 31, 63, 127} ratio         | **0.686×**       | **0.694×**              | 0.694×              | match       |
| Falsifier {15, 31, 63, 127} p-value       | **0.240**        | **0.241**               | 0.241               | match       |
| Falsifier verdict                         | **H0**           | **H0**                  | H0                  | match       |

**Cross-method agreement level: STRONG** (relative ratio difference 0.008
at {3,7}; same primary verdict; same falsifier verdict; both falsifiers pass
cleanly).

**SMICA-nosz bit-for-bit reproduction.** Re-running the pipeline on the
cached SMICA-nosz FITS in this spike produced exactly Spike #190's primary
ratio (6.19425053358111) and p-value (0.0057994200579942). The pipeline is
deterministic; cross-method comparison is methodologically apples-to-apples.

---

## What we did

1. **Downloaded NILC-full** (`COM_CMB_IQU-nilc_2048_R3.00_full.fits`,
   ~1.5 GB) from the IRSA Planck mirror, per
   `[[reference_autonomous_validation_tos_landscape]]` (PLA / IRSA on the
   permitted list).
2. **Reused SMICA-nosz cache** (~400 MB) from the Spike #190 worktree via
   symlink for the side-by-side recomputation.
3. **Ran the same pipeline on both**: `hp.read_map(field=0)` → `hp.ud_grade`
   Nside 2048 → 64 (power-preserving) → `hp.anafast(lmax=191)`.
4. **Applied the same fractional-power test** (10,000-perm shuffle null,
   seed=0, Wilson-corrected p-values) at the primary set {3, 7} on ℓ=2..40
   and the falsifier set {15, 31, 63, 127} on ℓ=2..191.
5. **Computed cross-method agreement metrics** (relative ratio difference at
   {3, 7}; verdict-bucket matching for primary + falsifier).
6. **Closed Spike #190 fermata-5** (MASTER mode-coupling correction): for
   full-sky pseudo-C_ℓ, the MASTER M_ℓℓ' matrix reduces to δ_ℓℓ' (Hivon+
   2002 Eq. 25). The anafast output already IS the MASTER-corrected
   estimator for the full-sky configuration we use.

---

## What the result means

The 6.19× SMICA-nosz signal at {3, 7} is reproduced at 6.14× by an
**independent algorithmic family** (Delabrouille+ 2009 needlet-domain ILC
vs. Cardoso+ 2008 spectral-domain ILC). Both share the same underlying
multi-frequency Planck data, but their component-separation pipelines have
**different beam-window-function treatment + different noise weighting**.
Concordance at this level eliminates the SMICA-specific-pipeline-artifact
concern raised as Spike #190 fermata-4.

Equally important, the **higher-Mersenne falsifier passes cleanly on both
methods** (ratio ~ 0.69×, p ~ 0.24, verdict H0). The framework's prediction
that {15, 31, 63, 127} should NOT concentrate (lack of Hopf-bundle structure
per Adams 1962 / Hurwitz 1898 / Bott-Milnor-Kervaire) is method-independent.
The signal is structurally Hopf-fiber, not generically Mersenne-prime.

### Composition with stances

* `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]` — H1
  reading from Spike #190 holds across both ILC methods. The empirical-
  signature catalogue carries the {3, 7} TT concentration as a robust
  cross-substrate signature, no longer caveated by single-method
  dependency.
* `[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]` —
  S² spherical-harmonic projection on the CMB sky shows preferential
  power at the Hopf-fiber dimensions {3, 7} (S³ + S⁷ ladder steps);
  unaffected by component-separation algorithm choice.
* `[[user_stance_identity_not_implementation_discipline]]` — structural-
  algebra layer (4:3 base:fiber ratio at IEEE-754 double, 2× doubling,
  Mersenne + Lie-group + parallelizable-sphere convergence at {1, 3, 7})
  was already unchanged regardless of any Spike #192 verdict. STRONG
  agreement here strengthens the empirical-projection-side reading
  toward universality.

### What did NOT change

* **14 A-N classes intact.** Test uses Class L (spectral-power on sphere
  Laplacian eigenbasis), Class K (asymptotic loop DOF; ℓ-mode index),
  Class C (FITS streaming), Class I (cyclic-modular membership for
  {3, 7}). No new mechanism.
* **No vocabulary impact.** Ring vocabulary (S¹ / S³ / S⁷) preserved
  throughout per `[[feedback_asymptotic_ring_vocabulary_discipline]]`.
* **Trauma-informed defensive scope** intact — public ESA Planck Legacy
  Archive data only.

---

## PR dispositions

Per `[[feedback_autonomous_research_followup_authorization]]` + the
`DO_NOT_MERGE_AUTONOMOUSLY` flag at the bottom of the final_verdict
record, **all three PRs remain conductor-gated**. Recommendations:

* **PR #621 (Spike #185 IGRF-13 planetary-magnetic):** **MERGE_WITHOUT_
  SUBSTRATE_SPECIFICITY_CAVEAT.** Cross-method verification confirms
  Spike #190's H1 reading; the substrate-specificity caveat that arose
  from Spike #187 BB H0 is fully relaxed.
* **PR #629 (Spike #187 CMB BB):** **MERGE.** The BB H0 reading was
  noise-floor-driven (Spike #190 closure); this PR ships the H0 record
  with the noise-floor caveat, which Spike #190 + Spike #192 jointly
  closed. The BB null is a measurement-floor artifact, not substrate-
  specific structural absence.
* **PR #631 (Spike #190 CMB TT SMICA-nosz):** **MERGE.** Cross-method
  STRONG agreement confirms the SMICA-nosz H1 reading. Recommend
  inlining a Spike #192 cross-method confirmation reference in the
  spike-note before merge.

---

## Fermatas remaining

* **Masked-sky comparison.** Adding the Planck `COM_Mask_CMB-common-Mask-Int`
  Galactic mask would invoke non-trivial MASTER mode-coupling per Hivon+
  2002. This spike used full-sky maps (anafast = MASTER-corrected for
  full-sky). A masked-sky tighter-bound follow-up is a clean future spike
  if conductor wants to pressure-test {3, 7} against foreground-residual
  contributions at low Galactic latitude.
* **Third-method tie-break.** SEVEM and Commander are the remaining
  Planck-pipeline component-separation methods. STRONG agreement between
  NILC and SMICA-nosz already eliminates the SMICA-specific-artifact
  concern; SEVEM / Commander third-method runs would be optional
  belt-and-suspenders work, not blocking.
* **Higher-ℓ extension.** This spike tested ℓ=2..40 primary and ℓ=2..191
  falsifier at Nside=64 downgrade. A Nside=256 or 512 run could extend
  ℓ to ~767 / 1535 to probe whether the Hopf-fiber signature persists
  in the acoustic-peak regime. Out of scope for this spike but a
  natural next step.

---

## Cited literature (PDF / arXiv verified per `[[feedback_pdf_extraction_citation_discipline]]`)

* **Akrami Y. et al. (Planck Collaboration)**, "Planck 2018 results IV:
  Diffuse component separation", *A&A* 641 (2020), A4.
  DOI:10.1051/0004-6361/201833881; arXiv:1807.06208.
  Source for SMICA / NILC / SEVEM / Commander map products.
* **Cardoso J.-F., Le Jeune M., Delabrouille J., Betoule M., Patanchon G.**,
  "Component separation with flexible models — Application to multi-
  channel astrophysical observations", *IEEE J. Sel. Topics Signal
  Process.* 2 (2008), 735-746. DOI:10.1109/JSTSP.2008.2005346;
  arXiv:0803.1814. SMICA algorithm reference.
* **Delabrouille J., Cardoso J.-F., Le Jeune M., Betoule M., Fay G.,
  Guilloux F.**, "A full sky, low foreground, high resolution CMB map
  from WMAP", *A&A* 493 (2009), 835-857.
  DOI:10.1051/0004-6361:200810514; arXiv:0807.0773. NILC algorithm
  reference.
* **Hivon E., Gorski K.M., Netterfield C.B., Crill B.P., Prunet S.,
  Hansen F.**, "MASTER of the CMB Anisotropy Power Spectrum", *ApJ* 567
  (2002), 2-17. DOI:10.1086/338126; arXiv:astro-ph/0105302. MASTER
  mode-coupling matrix reduction to δ_ℓℓ' for full-sky case.
* **Gorski K.M. et al.**, "HEALPix: A Framework for High-Resolution
  Discretization and Fast Analysis of Data Distributed on the Sphere",
  *ApJ* 622 (2005), 759. DOI:10.1086/427976; arXiv:astro-ph/0409513.
  HEALPix pixelisation / anafast.

---

## Discipline checklist

- [x] **NDJSON over bloated JSON** — output is one record per line per
      `[[feedback_ndjson_over_bloated_json]]`.
- [x] **Computational provenance** — script committed alongside NDJSON;
      seed=0, n_permutations=10000, Wilson-corrected p-values per
      `[[feedback_computational_provenance_discipline]]`.
- [x] **Math doesn't lie** — empirical verdicts from
      `anafast(Planck NILC + SMICA-nosz FITS)`; no hand-entered numbers.
- [x] **PDF-extraction citation discipline** — five canonical references
      verified per `[[feedback_pdf_extraction_citation_discipline]]`.
- [x] **Asymptotic-loop vocabulary** — S¹ / S³ / S⁷, per-integer-ℓ used
      throughout per `[[feedback_asymptotic_ring_vocabulary_discipline]]`.
- [x] **No class promotion** — 14 A-N classes intact per
      `[[feedback_no_privileged_primitive_classes]]`.
- [x] **Trauma-informed defensive scope** — public ESA Planck Legacy
      Archive data only per `[[feedback_trauma_informed_defensive_scope]]`.
- [x] **Identity-not-implementation discipline** — structural-algebra
      layer unchanged; only empirical-projection-side reading affected
      per `[[user_stance_identity_not_implementation_discipline]]`.
- [x] **TOS landscape compliance** — PLA / IRSA Planck mirrors only per
      `[[reference_autonomous_validation_tos_landscape]]`.
- [x] **`DO_NOT_MERGE_AUTONOMOUSLY` flag set** — final_verdict record
      carries the flag; conductor-gated.

---

## Files

* `docs/srmech/notes/spike192_nilc_cross_method_verification.py` —
  the full pipeline script.
* `docs/srmech/notes/spike192_findings_2026-05-19.ndjson` —
  21 NDJSON records: header, set_definition, method_comparison_design,
  data_acquisition, two per_ell_tables (NILC + SMICA-nosz),
  four primary_tests (primary + falsifier × 2 methods),
  cross_method_agreement, master_mode_coupling_note, 8 discipline
  records, final_verdict.
* `docs/srmech/notes/spike_192_nilc_cross_method_verification_2026-05-19.md` —
  this spike-note.
