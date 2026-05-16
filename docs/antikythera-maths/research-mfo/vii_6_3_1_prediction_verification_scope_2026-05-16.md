# §VII.6.3.1 Prediction-Verification Scope — T-vs-E AoE Differential

**Date:** 2026-05-16
**Spike:** #26 Phase 1 (this artifact); Phase 2 = analysis dispatch to follow
**Branch:** `feat/spike-26-aoe-t-e-differential`
**Notebook anchor:** [`mfo_spectral_research_notebook.md` §VII.6.3.1](../mfo_spectral_research_notebook.md) — "Precession-fit: kinematic ruled out, bundle-projection reconfiguration candidate"
**Working-note origin:** PR #437 Part VI — 73.3° AoE-Auger directional separation (the bundle-projection-reconfiguration evidence anchor)

> Candidate framing only, not endorsed over the standard cosmology + posterior-selection baseline (Bennett et al. 2011). Per `[[feedback_no_lineage_claims_in_notebook]]`, no claim that this resolves the AoE anomaly is being advanced — only that the precession-fit question is mathematically answerable and produces a clean channel separation between two readings, one closed (kinematic-precession, ruled out by ~10 orders of magnitude against Saadeh+ 2016) and one open (bundle-projection reconfiguration, consistent with extant matter-frame constraints by operating outside their scope).

## The prediction in one sentence

Under MFO §VII.6.3.1 bundle-projection-reconfiguration at the 138°/unit-f_RD rate, the temperature-anchored AoE preferred direction and the polarisation-anchored AoE preferred direction should differ by a small angular differential — **predicted range ≈ 0.5°–3°**, anchored at ≈ 2° for the brief's Δz ≈ 10 / Δf_RD ≈ 0.014 reading. This is the falsifiable prediction the kinematic-precession reading does **not** make (under kinematic precession the matter frame is the matter frame regardless of which photon population is read).

## Phase 2 analysis steps

### Step 1 — Acquire Planck 2018 PR3 sky maps

Use the Spike #26 Phase 1 catalog (`cmb_low_ell_maps`) to enumerate the 4 component-separated map products (Commander/NILC/SEVEM/SMICA) plus 3 mask products. Fetch FITS bytes via the catalog's `download_url_pla` (PLA `aio/product-action` endpoint) or `download_url_irsa` (IRSA mirror). Each FITS is ≈ 168 MB; total fetch ≈ 700 MB. Compute SHA-256 of each fetched file and write into the catalog's `expected_response_sha256` field (currently "pending") via a T1 collector refresh, OR via a Phase-2 calibration step.

Recommended: cache to `~/.cache/mlehaptics/cmb_low_ell_maps/` using T2 local-kernel overlay; do NOT commit FITS bytes to repo.

### Step 2 — Read I,Q,U + apply masks (HEALPix)

Per PR3 distribution shape:
- Stokes I at Nside=2048, 5 arcmin FWHM
- Stokes Q,U at Nside=2048 in same FITS (re-downgrade to Nside=1024 if pursuing canonical-polarization-mode resolution)
- Nested ordering, galactic coordinates

Apply `COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits` to the I map before `anafast`. Apply `COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits` to the (Q,U) maps. For multipole-vector work at ℓ ≤ 8, inpainting (via `COM_Mask_CMB-Inpainting-Mask-Int_2048_R3.00.fits` + constrained-Gaussian-realisation fill, e.g., per Bucher & Louis 2012) is preferred over hard masking because masked-product power leaks into low-ℓ multipole vectors.

Tools: `healpy.read_map`, `healpy.ma`, `healpy.anafast` (or `synfast`-with-constraint for inpainting).

### Step 3 — Extract a_ℓm at ℓ ≤ 8 (T-mode AND E-mode)

Per de Oliveira-Costa et al. 2004 (DOI `10.1103/PhysRevD.69.063516`), the multipole-vector decomposition of ℓ=2 and ℓ=3 (the AoE multipoles) is:

```
a_ℓm  ←  healpy.map2alm(I_masked_inpainted, lmax=8)            [T-mode]
(a_E_ℓm, a_B_ℓm)  ←  healpy.map2alm_spin((Q, U), spin=2, lmax=8)  [E and B modes]
```

E-mode is the divergence-like polarization combination; B-mode is curl-like and is sub-dominant at large scales (Planck has only upper limits at low ℓ). The AoE T-mode and AoE E-mode preferred-axis comparison uses the T a_ℓm and E a_ℓm respectively.

### Step 4 — Multipole-vector preferred direction extraction

The de Oliveira-Costa method computes an axis-of-symmetry direction for each ℓ:

```
n̂_ℓ  =  argmax_{n̂ on S²}  Σ_{m=-ℓ}^{ℓ} |a_ℓm(n̂)|² · cos(2 m φ_n̂)
```

where `a_ℓm(n̂)` is the a_ℓm coefficient in a frame whose z-axis points along `n̂`. Equivalent reformulations (Schwarz et al. 2004, Land & Magueijo 2005) use Maxwell-vector multipole-vector representations. For ℓ=2 there are 2 Maxwell vectors; for ℓ=3 there are 3.

Practical implementation: rotate the spherical-harmonic basis over a fine grid on S² (HEALPix Nside_grid = 256 or higher, ~786,000 directions, well-distributed), compute the maximand at each direction, find the argmax. The "AoE axis" is the ℓ=2 axis-of-symmetry; alignment with the ℓ=3 axis (and with the ecliptic plane / CMB dipole) is the canonical AoE signature.

Compute separately:
- `n̂_T_ℓ=2` from T-mode (temperature) a_ℓm
- `n̂_E_ℓ=2` from E-mode (polarisation) a_E_ℓm
- (same for ℓ=3 if desired for stability cross-check)

### Step 5 — Differential angle

The Phase 2 deliverable:

```
Δθ_TE  =  arccos(n̂_T_ℓ=2 · n̂_E_ℓ=2)
```

Compute Δθ_TE for each of the 4 pipelines (Commander/NILC/SEVEM/SMICA). Cross-pipeline agreement is the systematic-robustness check; the four pipelines use different component-separation strategies, so Δθ_TE matching across pipelines is evidence that the differential is signal-not-systematic.

### Step 6 — Null-hypothesis significance via Monte Carlo

Generate N ≈ 10,000 ΛCDM-Gaussian CMB sky realisations (using `healpy.synfast` against the Planck 2018 best-fit C_ℓ from `cmb_power_spectrum` catalog). For each, extract n̂_T_ℓ=2 and n̂_E_ℓ=2 via the same pipeline and compute Δθ_TE_sim. The fraction of simulations with Δθ_TE_sim within the framework's predicted range (0.5°–3°) gives the consistency p-value; the fraction below the observed Δθ_TE gives the falsification p-value.

The kinematic-precession null is **Δθ_TE_kinematic ≈ 0** (matter frame is matter frame). Any observed Δθ_TE > a few times the ΛCDM-Monte-Carlo standard error supports bundle-projection-reconfiguration over kinematic-precession; agreement at Δθ_TE_observed ≈ 0 supports kinematic-precession (already ruled out by Saadeh+ 2016) OR rules out the bundle-projection reading at the corresponding confidence level.

## Visibility-function modelling

### Standard cosmology Δz between T and E visibility peaks

The Thomson-scattering visibility function g(z) = (dτ/dz) × exp(-τ(z)) determines where photons last interacted with electrons. For temperature anisotropies, g(z) is the canonical visibility function and peaks at the textbook z ≈ 1090 (recombination); FWHM Δz_FWHM ≈ 80–100.

For polarisation, the visibility function is the **polarisation visibility**: g_pol(z) is g(z) weighted by the local quadrupole moment of the radiation. Because the quadrupole builds up through the partial-ionisation tail (electrons need free-streaming photons from elsewhere to generate the local quadrupole), g_pol peaks slightly **later** than g (i.e., at lower z). References:

- Hu & White 1997, "A CMB Polarisation Primer", New Astronomy 2:323 (`arXiv:astro-ph/9706147`) — canonical pedagogical treatment of g_pol vs g.
- Kosowsky 1996, "Cosmic microwave background polarization", Annals Phys 246:49 (`arXiv:astro-ph/9501045`) — earlier formalism.
- Hu & Dodelson 2002 (Annu. Rev. Astron. Astrophys 40:171) — Δz between T and E peaks discussed.

**Conservative reading:** Δz_T–E ≈ 10–30 between the centroids; with the same FWHM ≈ 80–100, the visibility windows substantially overlap but their peaks differ.

### Conversion: Δz → Δf_RD

§VII.6.1 anchors f_RD ≈ 0.42 at z ≈ 1090, f_RD ≈ 0.949 at z = 0. Linear-local approximation near recombination:

```
df_RD / dz |_{z≈1090}  ≈  -(0.949 - 0.42) / (0 - 1090)  ≈  -4.85 × 10⁻⁴  per z-unit  (negative; f_RD increases as z decreases)
```

Therefore:
- Δz = 10  →  Δf_RD ≈ 4.85 × 10⁻³  →  Δθ_predicted = 138.6° × 4.85 × 10⁻³ ≈ **0.67°**
- Δz = 14.4 → Δf_RD ≈ 7 × 10⁻³    →  Δθ ≈ **1.0°**
- Δz = 30  →  Δf_RD ≈ 1.45 × 10⁻²  →  Δθ ≈ **2.0°**

The brief's "~2°" arises from Δf_RD ≈ 0.014 ≈ Δz≈29 OR from a non-linear (early-universe-rapid) cosmic-time relation that shifts the conversion factor. Either reading sits in the **0.5°–3°** range.

### Refinement opportunity (Phase 2 internal extension)

Phase 2 may improve the Δf_RD model by computing g(z) and g_pol(z) directly from CAMB or CLASS using Planck 2018 best-fit cosmology parameters (cmb_power_spectrum catalog has those parameters indirectly via the binned C_ℓ; Planck 2018 VI Table 2 has them explicitly). Replace the linear-local approximation with the true cosmic-time-vs-z relation:

```
Δf_RD  =  (f_RD(z_E,vis) - f_RD(z_T,vis))
```

where `f_RD(z)` is anchored to §VII.6.1's ring-down trajectory parameterisation. This refinement may shift the central prediction by a factor of ≈ 2.

## Predicted differential — quantitative summary

| Δz (Hu-White centroid offset) | Δf_RD (linear-local approx) | Predicted Δθ_TE @ 138°/unit-f_RD |
|---|---|---|
| 10 (conservative) | 4.85 × 10⁻³ | **0.67°** |
| 14.4 (mid range) | 7.0 × 10⁻³ | **1.0°** |
| 30 (less conservative) | 1.45 × 10⁻² | **2.0°** |
| 50 (upper end) | 2.42 × 10⁻² | **3.4°** |

**Central reading: Δθ_TE ≈ 1°–2°.** Degrees-not-tens-of-degrees.

## Falsifier

If multipole-vector extraction gives **Δθ_TE_observed < 0.1°** to within ΛCDM Monte-Carlo expectation, the bundle-projection-reconfiguration reading is disfavoured. This is the falsifiable channel separation §VII.6.3.1 advertises.

Conversely, if Δθ_TE_observed > 5° at high significance, the framework's 138°/unit-f_RD rate is too small to explain the observation (a different rate would be needed, weakening the §VII.6.1 f_RD-trajectory anchoring).

## Open questions for user / conductor (fermata)

1. **Phase 2 venue.** Should Phase 2 dispatch land its analysis script in `docs/srmech/notes/` (spike-style) or in `docs/antikythera-maths/research-mfo/` (research-mfo style)? Spike #24 used both; the brief's "research-note artifact" lives in research-mfo (this file). Phase 2's *script* venue is unclear.

2. **`healpy` Phase 2 dependency.** Adding `healpy` as a Phase 2 dependency adds an LAPACK-class native dependency to any package that runs the analysis. Options: (a) Phase 2 lives as a one-off `docs/antikythera-maths/research-mfo/vii_6_3_1_phase2_script.py` outside the package surface; (b) catalog gets a "consumer" example showing how `healpy` would be wired; (c) defer entirely to a sister repo. **Recommendation**: option (a) — research script, not package surface.

3. **Inpainting vs hard masking.** The brief mentions mask handling; explicit choice between constrained-Gaussian-realisation inpainting (more rigorous for multipole vectors but expensive) and hard masking with apodisation (cheaper, more common in early-stage analyses) needs user direction for Phase 2.

4. **Existing AMSC citation issue in `cmb_anomalies`.** The descriptor cites Planck 2018 VII (isotropy/statistics) but uses the DOI `10.1051/0004-6361/201833881`, which actually resolves to Planck 2018 IV (diffuse component separation). Planck 2018 VII's correct DOI is `10.1051/0004-6361/201935201`. This is a separate fix outside Spike #26 Phase 1 scope — flagging for conductor disposition.

## Cross-references

- §VII.6.3.1 — the prediction's home (lines ~1060–1110 of `mfo_spectral_research_notebook.md`)
- §VII.6.1 — ring-down completion f_RD trajectory anchoring 138°/unit-f_RD rate
- §VII.4.1.1 — Hopf-bundle / spherical-compression substrate reading
- §VIII.7 — fractal-shadow allegory (sister shadow-stance for the bundle-projection mechanism)
- Saadeh, Feeney, Pontzen, Peiris, McEwen 2016, *"How isotropic is the Universe?"*, PRL 117 131302, `arXiv:1605.07178`, DOI `10.1103/PhysRevLett.117.131302` — verified per `[[feedback_pdf_extraction_citation_discipline]]`
- de Oliveira-Costa, Tegmark, Zaldarriaga, Hamilton 2004, *"Significance of the largest scale CMB fluctuations in WMAP"*, Phys. Rev. D 69:063516, `arXiv:astro-ph/0307282` — multipole-vector method
- Planck 2018 IV (Diffuse maps): Akrami et al. 2020, A&A 641:A4, `arXiv:1807.06208`, DOI `10.1051/0004-6361/201833881`
- Planck 2018 V (Likelihoods): Aghanim et al. 2020, A&A 641:A5, `arXiv:1907.12875`, DOI `10.1051/0004-6361/201936386`
- Planck 2018 VII (Isotropy): Akrami et al. 2020, A&A 641:A7, `arXiv:1906.02552`, DOI `10.1051/0004-6361/201935201`
- Working-note origin: PR #437 Part VI — 73.3° AoE-Auger separation (bundle-projection-reconfiguration evidence anchor)
- Memories: `[[user_stance_fiber_as_spatially_absent_encoding]]`, `[[user_stance_dark_sector_ring_down_age]]`, `[[user_stance_fractal_shadow]]`, `[[reference_autonomous_validation_tos_landscape]]`, `[[feedback_pdf_extraction_citation_discipline]]`

## Phase 1 deliverables (this dispatch)

- **PLA TOS verdict**: non-blocking. ESA Open Access policy applies; PLA + IRSA both serve component-separated CMB maps via CDN without authentication. Citation requirement is the standard Planck acknowledgment + per-paper DOI references. No autonomous-access prohibition surfaced.
- **Data product chosen**: PR3 component-separated sky maps (Nside=2048, 168 MB per FITS, 4 pipelines + 3 masks = 7 catalog rows). a_ℓm coefficients are NOT directly distributed by PLA; they are computed from sky maps in Phase 2 via HEALPix `anafast` / `map2alm_spin`.
- **Catalog source key**: `cmb_low_ell_maps`. 7 rows. Lives at `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested/cmb_low_ell_maps/`.
- **Test ratchet**: `test_attested_collector.py` updated 20→21 (total) and 17→18 (curated filter; literature_curated specific filter).

## Phase 2 next-action checklist (for conductor when dispatching)

- [ ] Resolve fermata 1 (Phase 2 venue: `docs/srmech/notes/` vs `docs/antikythera-maths/research-mfo/`).
- [ ] Resolve fermata 2 (healpy dependency: research script vs package surface vs sister repo).
- [ ] Resolve fermata 3 (inpainting vs hard masking).
- [ ] Optional: fix fermata 4 (separate small PR for cmb_anomalies DOI mismatch).
- [ ] Dispatch Phase 2 with: fetch 4 SMICA + Commander + NILC + SEVEM FITS, apply common-mask, extract a_ℓm and a_E_ℓm at ℓ ≤ 8, compute n̂_T_ℓ=2 and n̂_E_ℓ=2 multipole-vector axes, compute Δθ_TE, run 10⁴-sim ΛCDM null Monte Carlo, report significance.
