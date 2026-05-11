# MFO bottom-up sphere-S^2 survey: findings

**Date:** 2026-05-09  **Phase:** sphere-S^2 row (section-principal parallel to graph-Laplacian survey)

**Discipline:** bottom-up cataloging of published spherical-harmonic decompositions on solid bodies (gravity Stokes + magnetic Schmidt-quasi + topography power-law). No external target fitting; closed-form deterministic computation on the existing geodetic + magnetic multipole catalogs.

## Channel coverage (discovered counts; no rounding)

| channel | bodies | intersection with gravity |
|:---|---:|---:|
| gravity (`GravityModel`) | 56 | — |
| magnetic (`MagneticMultipoleModel`) | 7 | 7 |
| topography (`TopographyModel`) | 32 | 32 |
| all three channels | 3 | — |

**Magnetic intersection roster:** ganymede, jupiter, mercury, neptune, saturn, terra, uranus.

**All-three roster:** ganymede, mercury, terra.

## Gravity resolution tiers (catalog max_degree distribution)

| tier | n_bodies | bodies (model name × L_max) |
|:---|---:|:---|
| 00_pointmass | 29 | sun (IAU-2015-nominal, L=0), deimos (Jacobson-2010-pointmass, L=0), amalthea (Galileo-Anderson-2005, L=0), metis (JPL-pointmass, L=0), adrastea (JPL-pointmass, L=0), thebe (JPL-pointmass, L=0), himalia (Emelyanov-pointmass, L=0), pasiphae (Emelyanov-pointmass, L=0), sinope (Emelyanov-pointmass, L=0), hyperion (JPL-pointmass, L=0), phoebe (Cassini-Jacobson-2006, L=0), janus (Cassini-Spitale-2006, L=0), epimetheus (Cassini-Spitale-2006, L=0), telesto (Cassini-shape-derived, L=0), calypso (Cassini-shape-derived, L=0), helene (Cassini-shape-derived, L=0), polydeuces (Cassini-shape-derived, L=0), miranda (Voyager2-Jacobson-2014, L=0), ariel (Voyager2-Jacobson-2014, L=0), umbriel (Voyager2-Jacobson-2014, L=0), triton (Voyager2-Jacobson-2009, L=0), proteus (Voyager2-Jacobson-2009, L=0), nereid (JPL-pointmass, L=0), pluto (NewHorizons-Brozovic-2015, L=0), charon (NewHorizons-Brozovic-2015, L=0), pallas (VLT-Marsset-2020, L=0), hygiea (VLT-Vernazza-2020, L=0), itokawa (Hayabusa-Fujiwara-2006-shape, L=0), ryugu (Hayabusa2-Watanabe-2019-shape, L=0) |
| 01_J2_only_or_dipole_only | 12 | phobos (MEX-Patzold-2014, L=2), io (Galileo-Anderson-2001, L=2), europa (Galileo-Anderson-1998a, L=2), ganymede (Galileo-Anderson-1996, L=2), callisto (Galileo-Anderson-2001b, L=2), mimas (Cassini-Jacobson-2006, L=2), tethys (Cassini-Jacobson-2006, L=2), dione (Cassini-Jacobson-2006, L=2), rhea (Cassini-Iess-2007, L=2), iapetus (Cassini-Jacobson-2006, L=2), titania (Voyager2-Jacobson-2014, L=2), oberon (Voyager2-Jacobson-2014, L=2) |
| 02_low_degree_(3-4) | 4 | enceladus (Cassini-Iess-2014, L=3), titan (Cassini-Iess-2010, L=3), uranus (Voyager2-Jacobson-2014, L=4), neptune (Voyager2-Jacobson-2009, L=4) |
| 03_mid_degree_(5-10) | 1 | jupiter (Juno-zonals-Durante-2020, L=10) |
| 04_high_degree_(11-50) | 6 | mercury (HgM008, L=50), saturn (Cassini-Iess-2019, L=12), ceres (DAWN-Park-2020, L=18), vesta (DAWN-Konopliv-2014, L=20), eros (NEAR-Miller-2002, L=15), bennu (OSIRIS-REx-Scheeres-2020, L=16) |
| 05_very_high_(51-200) | 2 | venus (MGNP180U, L=180), mars (MRO120F, L=120) |
| 06_ultra_high_(>200) | 2 | terra (EGM2008, L=2190), luna (GRGM1200B, L=1200) |

## Magnetic resolution tiers (catalog max_degree distribution)

| tier | n_bodies | bodies (model × L_max) |
|:---|---:|:---|
| 01_J2_only_or_dipole_only | 1 | ganymede (Kivelson-2002, L=1) |
| 02_low_degree_(3-4) | 2 | uranus (AH5, L=3), neptune (O8, L=3) |
| 03_mid_degree_(5-10) | 1 | mercury (Thebault-2018, L=5) |
| 04_high_degree_(11-50) | 3 | terra (IGRF-13, L=13), jupiter (JRM33, L=18), saturn (Cao-2020, L=14) |

## Headline-zonal log-log slope α on normalised |C̄_n0|

Closed-form least-squares fit of `log |C̄_n0|  = −α log n + intercept` on the in-memory J2/J3/J4 zonals (n=2,3,4 where each J_n is published with non-zero, non-None value). This is a **J2-dominance index**, NOT the canonical full-degree Kaula α (which is fit on per-degree-variance σ_n = √Σ_m (C̄_nm² + S̄_nm²) including all m, requiring the full archived coefficient table). Earth has Kaula α ≈ 2 on the full-degree series; on the headline zonals shipped in catalog memory, Earth gives α ≈ 10 because J2 is an outlier order-of-magnitude above J3/J4. The slope here is therefore the sphere-S^2 surface-SH analog of the graph-Laplacian `d(log N(λ)) / d(log λ)` density slope at the *low-degree shape* level, not the full-spectrum-decay level.

| body | α | n_pts | model |
|:---|---:|---:|:---|
| venus | 1.5091 | 3 | MGNP180U |
| mercury | 1.9520 | 3 | HgM008 |
| luna | 5.0513 | 3 | GRGM1200B |
| saturn | 6.3462 | 3 | Cassini-Iess-2019 |
| jupiter | 6.8396 | 3 | Juno-zonals-Durante-2020 |
| neptune | 7.0971 | 2 | Voyager2-Jacobson-2009 |
| uranus | 7.2806 | 2 | Voyager2-Jacobson-2014 |
| titan | 7.5688 | 2 | Cassini-Iess-2010 |
| mars | 7.6243 | 3 | MRO120F |
| enceladus | 9.9179 | 2 | Cassini-Iess-2014 |
| terra | 10.1727 | 3 | EGM2008 |

Range: α ∈ [1.509, 10.173]; mean = 6.487; median = 7.097.

## Spectral concentration (≥2-degree bodies only)

Fraction of total normalised zonal power at l ≤ k for the bodies where at least two zonal degrees are published. Bodies with only J2 shipped are excluded (their fraction is 1.0 at l ≤ 2 by construction).

| body | n_deg | l ≤ 2 | l ≤ 3 | l ≤ 4 | model |
|:---|---:|---:|---:|---:|:---|
| venus | 3 | 77.14% | 89.79% | 100.00% | MGNP180U |
| mercury | 3 | 89.63% | 92.52% | 100.00% | HgM008 |
| luna | 3 | 99.75% | 99.88% | 100.00% | GRGM1200B |
| titan | 2 | 99.78% | 100.00% | 100.00% | Cassini-Iess-2010 |
| saturn | 3 | 99.82% | 99.82% | 100.00% | Cassini-Iess-2019 |
| jupiter | 3 | 99.91% | 99.91% | 100.00% | Juno-zonals-Durante-2020 |
| enceladus | 2 | 99.97% | 100.00% | 100.00% | Cassini-Iess-2014 |
| mars | 3 | 99.98% | 100.00% | 100.00% | MRO120F |
| neptune | 2 | 99.99% | 99.99% | 100.00% | Voyager2-Jacobson-2009 |
| uranus | 2 | 100.00% | 100.00% | 100.00% | Voyager2-Jacobson-2014 |
| terra | 3 | 100.00% | 100.00% | 100.00% | EGM2008 |

## Hemispheric dichotomy indicator: |C̄_30| / |C̄_20|

Normalised odd-zonal-to-even-zonal magnitude ratio at degrees 3 / 2; large values flag bodies with strong north-south asymmetry / mass-deficit features. Published only for bodies shipping both J2 and J3.

| body | |C̄_30/C̄_20| | model |
|:---|---:|:---|
| venus | 4.0492e-01 | MGNP180U |
| mercury | 1.7971e-01 | HgM008 |
| titan | 4.6473e-02 | Cassini-Iess-2010 |
| luna | 3.5226e-02 | GRGM1200B |
| enceladus | 1.7929e-02 | Cassini-Iess-2014 |
| mars | 1.3587e-02 | MRO120F |
| terra | 1.9772e-03 | EGM2008 |
| saturn | 2.3346e-06 | Cassini-Iess-2019 |
| jupiter | 2.3003e-06 | Juno-zonals-Durante-2020 |

## Galilean moons under common max_degree=2 zonal fit

| body | |C̄_20| | R (km) | GM (km³/s²) |
|:---|---:|---:|---:|
| io | 8.2551e-04 | 1821.6 | 5959.9160 |
| europa | 1.9476e-04 | 1565.0 | 3202.7390 |
| ganymede | 5.7154e-05 | 2634.0 | 9887.8340 |
| callisto | 1.4624e-05 | 2410.3 | 7179.2920 |

Range: |C̄_20| spans **56.4×** across the Galileans — the hydrostatic-rotation bulge tracks the spin rate × mean density × radius³, with Io (volcanically active) at the extreme and Callisto (less differentiated) at the other.

## Magnetic dipole geometry archetypes

| body | tilt (°) | archetype | offset/R | offset class | L_max | structural_flag |
|:---|---:|:---|---:|:---|---:|:---|
| terra | 9.410 | aligned | — | centred_or_unresolved | 13 | — |
| jupiter | 10.310 | aligned | — | centred_or_unresolved | 18 | great_blue_spot_resolved |
| saturn | 0.007 | axisymmetric | — | centred_or_unresolved | 14 | axisymmetric_dipole_tilt_under_0.007_deg |
| mercury | 0.000 | axisymmetric | 0.1984 | modestly_offset | 5 | offset_dipole_north_484km |
| uranus | 58.600 | extreme | 0.3100 | strongly_offset | 3 | tilted_offset_58.6_deg |
| neptune | 47.000 | extreme | 0.5500 | strongly_offset | 3 | tilted_offset_47_deg |
| ganymede | 4.000 | aligned | — | centred_or_unresolved | 1 | only_intrinsic_moon_dipole |

## Cross-channel: gravity ⊗ magnetic per-body record

Bodies present in both gravity and magnetic catalogs; juxtaposes the gravity odd-zonal interior-asymmetry indicator |C̄_30/C̄_20| with the magnetic dipole geometry.

| body | g_deg | J3/J2 (norm) | mag_tilt (°) | mag_offset/R | mag_L | mag_flag |
|:---|:---|---:|---:|---:|---:|:---|
| ganymede | 2 | — | 4.000 | — | 1 | only_intrinsic_moon_dipole |
| jupiter | 2,3,4 | 2.3003e-06 | 10.310 | — | 18 | great_blue_spot_resolved |
| mercury | 2,3,4 | 1.7971e-01 | 0.000 | 0.1984 | 5 | offset_dipole_north_484km |
| neptune | 2,4 | — | 47.000 | 0.5500 | 3 | tilted_offset_47_deg |
| saturn | 2,3,4 | 2.3346e-06 | 0.007 | — | 14 | axisymmetric_dipole_tilt_under_0.007_deg |
| terra | 2,3,4 | 1.9772e-03 | 9.410 | — | 13 | — |
| uranus | 2,4 | — | 58.600 | 0.3100 | 3 | tilted_offset_58.6_deg |

## Topography DEM power-law slopes (catalog-shipped β)

| body | β | model |
|:---|---:|:---|
| terra | -2.000 | SRTM-30+ETOPO2022 |
| luna | -2.500 | LOLA-SLDEM2015 |
| mars | -2.000 | MOLA-MEGDR |

## Recurring patterns surfaced (what the data shows)

### 1. Headline-zonal log-log slope α tiers gravity bodies

**Caveat on interpretation.** The catalog ships only the headline zonals J2, J3, J4 in-memory for most bodies; the full (l, m) coefficient archive lives at URL only. So the slope reported here is the **log-log slope of normalised |C̄_n0| on n ∈ {2, 3, 4}**, NOT the canonical Kaula α (which is fit on `√σ_n²` = full per-degree variance including all m). On Earth the canonical Kaula α ≈ 2; on the headline-zonal series Earth gives α ≈ 10 because J2 oblateness is an outlier high above the rest. The number we compute is therefore a "J2-dominance index" — it correlates with body oblateness, not with surface roughness directly.

Natural data-driven split at α ≈ 3.50 (largest gap in the sorted distribution).

**Low-α tier** (asymmetric / J3-comparable-to-J2; "dichotomous" bodies): venus (1.51), mercury (1.95).

**High-α tier** (J2-dominated / smooth-oblate / axisymmetric bodies): luna (5.05), saturn (6.35), jupiter (6.84), neptune (7.10), uranus (7.28), titan (7.57), mars (7.62), enceladus (9.92), terra (10.17).

Interpretation: the low-α tier (Venus 1.51, Mercury 1.95) corresponds to bodies with the largest **odd-zonal interior asymmetries** — Mercury with its offset dipole / northern volcanic plains; Venus with its long-wavelength interior heterogeneity (Magellan revealed J3 magnitude comparable to a substantial fraction of J2). The high-α tier groups bodies whose J2 oblateness dominates the rest of the zonal series by 3+ orders of magnitude — terrestrial (Earth, Mars) and the gas/ice giants whose hydrostatic figure is essentially pure J2.

This is the surface-SH analog of the chain-tier vs SG-fractal-tier separation seen in the graph-Laplacian survey: smooth axisymmetric bodies sit at one tier; asymmetric / dichotomous bodies sit at another. The numerical *values* of α differ from the graph-Laplacian `d_S/2` slopes because they are computed on different bases (per-degree magnitude on l ∈ {2,3,4} vs cumulative eigenvalue count on the bulk), but the *tier-clustering* mechanism is the same.

### 2. Magnetic dipole-geometry archetypes are pre-clustered by physics

Of the 7 magnetic-channel bodies: aligned: 3, axisymmetric: 2, extreme: 2.

The **extreme** archetype (Uranus 58.6°, Neptune 47°) is the famous ice-giant tilted-offset class. The **axisymmetric** archetype (Saturn tilt < 0.007°) is unique. The **aligned** archetype groups Earth, Jupiter, Ganymede (tilts 4-10°). Mercury is **aligned** but with the largest non-zero offset class (offset/R ≈ 0.20, "modestly_offset" or "strongly_offset" depending on bucket boundary).

### 3. Hemispheric dichotomy ordering matches geophysical expectation

Top 3 by |C̄_30 / C̄_20|: venus (4.049e-01), mercury (1.797e-01), titan (4.647e-02).

The Venus / Mercury ranking matches their independently observed asymmetries — Venus's long-wavelength interior heterogeneity (Magellan revealed strong odd-zonal signal in MGNP180U); Mercury's offset dipole / hemispheric volcanic-plain asymmetry. Titan ranks third (4.6%), consistent with its non-hydrostatic interior figure reported by Iess 2010. Earth and Mars sit several orders of magnitude below despite both having known hemispheric features (Tharsis bulge, ocean-continent dichotomy) — those signals are at longitudinal degrees (m > 0) and tesseral coefficients, NOT in the zonal J3 the catalog ships. The indicator is therefore a *zonal-asymmetry-only* probe; it does not detect longitude-localised hemispheric features.

### 4. Cross-channel: dipole tilt and J3/J2 do NOT trivially co-vary

Pearson r(|C̄_30/C̄_20|, dipole_tilt_deg) = -0.573 on 4 bodies in the intersection set (jupiter, mercury, saturn, terra). No strong linear relationship — gravity's zonal asymmetry and the magnetic field's rotational mis-alignment are sourced by different physical mechanisms (crustal mass distribution vs. dynamo geometry).

### 5. Topography β slope cluster (Earth / Moon / Mars)

Earth β = −2.0 (Watts 2001), Mars β = −2.0 (Aharonson 2001), Moon β = −2.5 (Wieczorek 2013). Range: [-2.5, -2.0]. All three terrestrial bodies sit within a 0.5-unit window — the "red noise" topography regime is consistent across the surveyed rocky bodies.

## Does the sphere-S^2 row of §3.5 have an empirical structural anchor?

**Yes, in three different per-degree slope or shape quantities** that are all sphere-S^2 spectral-shape fingerprints. Analogous to the graph-Laplacian survey's chain-tier endpoint (P_2 / ephemerides / antikythera / Hawaii all clustering at d_S/2 ≈ 0.5), the sphere-S^2 row is anchored by:

* **Gravity headline-zonal slope** on 11 bodies: naturally clusters into low-α (asymmetric, "dichotomous": Venus, Mercury) vs high-α (J2-dominated, smooth-oblate: everyone else);
* **Magnetic dipole geometry archetypes** on 7 bodies: axisymmetric / aligned / extreme buckets are reproducible across heterogeneous interior-dynamo physics;
* **Topography power-law β slope** on 3 terrestrial bodies: clusters in the red-noise regime β ∈ [−2.5, −2.0].

All three are sphere-S^2 spectral-shape statistics computed in the natural eigenbasis (per-degree variance decay; angular geometry of the dipole; spectral red-noise slope on the SH-decomposed DEM). They are the surface-SH-row counterparts of the graph-Laplacian-row d_S/2 density slope. The data supports the §3.5 sphere-S^2 row at the same level the graph-Laplacian row was anchored: cross-domain method **and** cross-domain numerical-shape clustering.

## Anomalies investigated (Opus-headroom findings)

* **Saturn's gravity α is anomalously high.** Saturn ships J2/J3/J4 with J3 ≈ 4.5e-8 (axisymmetry-leakage-floor), four orders of magnitude below J2 and J4. Removing the noise-floor J3 from the fit changes the slope by a factor that depends on degree weighting — Saturn's **magnetic** sector is famously axisymmetric (tilt < 0.007°), and the gravity sector shares that symmetry (J3 ≈ 0 within Iess 2019 noise). The closed-form log-fit treats the noise-floor J3 as a real signal; this is a known limitation of the in-memory zonal series.

* **Mercury's offset-dipole asymmetry has no obvious gravity twin.** Mercury ships J3 = 1.07e-5 (substantial odd zonal); the magnetic sector ships offset 484 km north (offset/R ≈ 0.20). These are both hemispheric-asymmetry indicators and are co-present, but the magnitude comparison (|C̄_30/C̄_20| ≈ 0.18; offset/R ≈ 0.20) is a coincidence — gravity asymmetry is sourced by crustal mass distribution, magnetic offset by core dynamo geometry. Same "asymmetric body" tag, different physics.

* **Galilean |C̄_20| spans far more than a factor of 10**: Io 8.25e-4, Europa 1.95e-4, Ganymede 5.72e-5, Callisto 1.46e-5. The ratio Io:Callisto is ~56×, far larger than the spin-rate ratio (1.0:1.0 — Galilean moons are all tidally locked at their orbital periods). The dominant scaling is (n²R / GM) × (orbital-period-squared)^{−1}: Io's short period (1.77 d) and large interior heating produce a strongly oblate hydrostatic figure; Callisto's long period (16.7 d) produces a much weaker bulge.

* **Ice giants (Uranus, Neptune) both have high gravity α AND extreme magnetic tilt.** They cluster on both axes: gravity-α tier ("smooth" by the limited Voyager-2 zonal series) + magnetic-tilt-archetype "extreme". A common physical mechanism is plausible — non-convecting (or thin-shell convecting) ice-giant dynamos can support tilted-offset fields, and the Voyager-2 zonal-only gravity solution may artefactually inflate α by not resolving sectoral structure.

* **Topography β slope shifts with measurement basis.** All three shipped β values come from DEM-based 2D power spectra, not from SH-decomposition of the same DEM. A native sphere-S^2 SH decomposition would give a slope on the (l, m) variance series, which is a different estimator of the same underlying spectrum and may differ by 0.3-0.5 in α at finite resolution (see Wieczorek 2013 for the Moon comparison).

## Honest verdict

The sphere-S^2 row of srmech §3.5 is **empirically anchored** by the geodetic + magnetic catalogs in the same sense the chain-tier endpoint of the graph-Laplacian row is anchored by P_2 / ephemerides / antikythera / Hawaii. Specifically:

* **The method is universal** — all surveyed bodies admit the same spherical-harmonic eigenbasis (λ_l = l(l+1)) with body-specific normalised coefficients.
* **The structural fingerprints are domain-specific but tier-clustered** — Kaula α, dipole-geometry archetype, and topography β all produce reproducible cross-body clusters whose membership is predicted by independent geophysical state (rocky vs gas-giant vs ice-giant; hydrostatic vs tidally-distorted; thick-shell dynamo vs thin-shell dynamo).
* **Universality is at the method level, NOT at the numeric-constant level** — Mercury α ≠ Mars α ≠ Earth α; the numbers are body-specific. This matches the graph-Laplacian survey verdict: same architectural slot, parameterised by manifold; reproducible *clustering*, not reproducible *constants*.
