# Spike #144 — Substrate roster pre-registration

Date: 2026-05-18 (Tuning A)
Branch: `research/spike-144-inter-body-7dg-ball-boundary-signatures`
Parent: Spike #143 (intra-body d_geom-monotone shadow at p<0.05).

## Purpose

Pre-register the full substrate roster BEFORE running any analysis,
per Meta-lesson 1 (sample-selection-bias check). Locks the bodies /
surveys / binaries used so post-hoc curation cannot inflate
significance.

## Strict-spec d_geom

```
d_geom = 2 G M / (c^2 R)
```

where M = body mass (kg), R = boundary radius (m). For Axis 1
(heliosphere) R is the heliopause radius; for Axis 2 R is the
stellar Bondi-radius proxy; for Axis 3 R is binary semi-major axis.
This is the SAME strict spec used in Spike #143 — no metaphorical
extension. Units: dimensionless.

## Axis 1 — Heliosphere boundary

PREDICTION: The Sun's 7D_g ball boundary location is set by
d_geom_Sol on the heliopause scale. Standard model (Parker / Burlaga)
predicts heliopause from solar-wind ram-pressure balance with ISM.
Framework adds a d_geom term such that the observed heliopause
distance scales monotonically (or with weighted contribution) with
the predicted 7D_g boundary radius.

Pre-registered sample (n=2, Voyager 1+2 only; no curation):

| Body | Boundary measurement | Source |
|------|---------------------|--------|
| Sol heliopause (V1 crossing) | 121.6 AU, 2012-08-25 | Stone et al. 2013 Science 341:150 [Voyager Interstellar Mission] |
| Sol heliopause (V2 crossing) | 119.0 AU, 2018-11-05 | Stone et al. 2019 Nature Astronomy 3:1013 |

Reference for solar wind ram-pressure model: Parker 1958 ApJ 128:664;
Burlaga 2015 Heliosphere review (cite-by-ref; arXiv 1502.04960).

DOI access: arXiv versions of Stone+2013 and Stone+2019 are PMC-
deposited and within autonomous-validation TOS landscape.

## Axis 2 — Faraday rotation vs stellar density

PREDICTION: Inter-stellar magnetic field IS the superposition of
stellar 7D_g ball boundaries. Faraday rotation measure (RM in
rad/m²) should correlate with stellar density (visible matter,
proxied by Gaia DR3 stellar count per unit solid angle or by
near-IR surface brightness) MORE than with neutral H I (proxied by
Heiles & Troland H I survey) or molecular gas (proxied by CO
emission, Dame et al.).

Pre-registered sample (n=5 Galactic latitude bins, NO post-hoc
binning revisions):

| Bin name | Galactic l, b range | Stellar density proxy | RM source |
|----------|--------------------|-----------------------|------------|
| GAL_CENTER | l=350-10, b=-5..5 | Gaia DR3 G<18 count | Oppermann et al. 2012 A&A 542:A93 |
| GAL_INNER | l=300-60, b=-10..10 | Gaia DR3 G<18 count | Oppermann+2012 |
| GAL_DISK | l=60-300, b=-5..5 | Gaia DR3 G<18 count | Oppermann+2012 |
| GAL_MID_LAT | all l, b=10-30 | Gaia DR3 G<18 count | Oppermann+2012 |
| GAL_HIGH_LAT | all l, b>30 or b<-30 | Gaia DR3 G<18 count | Oppermann+2012 |

ALTERNATIVE-EXPLANATION proxies (must NOT correlate better with RM
than stellar density does, or the framework is wrong):

- H I column density: HI4PI survey (Westerhout-completed; Bekhti et al. 2016 A&A 594:A116)
- CO molecular gas: Dame, Hartmann, Thaddeus 2001 ApJ 547:792
- Free-electron density: Cordes & Lazio NE2001 model (independent of RM)

NOTE: The Oppermann et al. 2012 RM full-sky catalog is the
NVSS-derived reconstruction; published values are computed via
Wiener-filter on ~37000 extragalactic point-source RMs. This is
the de-facto standard inter-stellar RM map. arXiv: 1111.6186.

## Axis 3 — Close binary magnetic spectra

PREDICTION: Short-period close binaries with both components on the
main sequence should show inter-7D_g-ball-coupling effects in their
magnetic / activity spectra. Specifically, the framework predicts
**harmonic content tied to orbital frequency** beyond what the
canonical Skumanich rotational-spin-down + dynamo model accounts
for.

Pre-registered sample (n=5 close binaries with both
photometric/spectropolarimetric magnetic measurements AND
published orbital periods, NO post-hoc curation):

| System | Type | P_orb (d) | B-field detection | Source |
|--------|------|-----------|-------------------|--------|
| V471 Tau | WD+K2V | 0.521 | DA WD: 350 G | Kawka+2007 ApJ 654:499 |
| BY Dra | K4V+K7V | 5.98 | Both: ~kG | Strassmeier 2009 A&ARv 17:251 |
| RS CVn | F4IV+G9IV | 4.80 | Active K-component: kG | Donati+1995 A&A 300:803 |
| AR Lac | G2IV+K0IV | 1.98 | Both: kG-scale | Drake & Sarna 2003 ApJ 594:L55 |
| YY Gem | M0Ve+M0Ve | 0.814 | Both: ~kG | Hussain+2012 MNRAS 423:493 |

ALTERNATIVE EXPLANATIONS to control for:
- Skumanich rotational spin-down (P_rot vs age)
- Tidal locking (P_rot ≈ P_orb for synchronized close systems)
- Dynamo α-Ω classical model (radiative-convective boundary depth)

Note: YY Gem from Hussain+2012 is a load-bearing case because both
components are pre-main-sequence M dwarfs with strong inter-ball
coupling expected if framework is correct.

## Discipline anchors

- Meta-lesson 1: pre-register before any analysis
- Meta-lesson 2: multi-round survival required
- Strict-spec d_geom (no metaphorical extension)
- PDF-extraction citation discipline (verify authors + title + arXiv before citing)
- Trauma-informed defensive scope (defensive preparedness, not capability assessment)
- arXiv / NASA ADS for primary; cite-by-ref for paywalled Nature/Science
- NDJSON output structure (one record per body/measurement)
- 14 A-N primitive vocabulary intact; this spike adds NO new classes
- Vocabulary-impact stance candidate `magnetic_field_is_2d_boundary_of_7d_g_ball` HELD pending consolidated decision

## Exit conditions per axis

A — STRONG POSITIVE: predicted scaling holds, alternative-explanation
proxies fail comparison test (p < 0.05).

B — WEAK POSITIVE: predicted scaling holds in sign/monotonicity but
alternative explanations remain plausible.

C — NULL: scaling fails or alternative explanations win.

D — FALSIFIED: anti-prediction realised (e.g., RM anticorrelates with
stellar density at p < 0.05).

## Discipline note

The d_geom of a single body has a defined unit (dimensionless). The
INTER-body construct here ASSUMES the 7D_g balls of different bodies
can be compared on a common scale. This is a non-trivial assumption
of the framework being tested. If results are null or falsified,
this assumption is part of what falls.
