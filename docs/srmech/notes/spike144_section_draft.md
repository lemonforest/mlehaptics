# Spike #144 — Inter-body 7D_g ball boundary signatures (section draft)

Date: 2026-05-19
Branch: `research/spike-144-inter-body-7dg-ball-boundary-signatures`
Status: COMPLETE — 3-axis inter-body extension of Spike #143; consolidated decision PENDING conductor.

## What was tested

Spike #143 surfaced an intra-body d_geom-monotone signal at p<0.05
(Axis 2 + Axis 3) in solar-system magnetic substrates. Spike #144
extends the question to INTER-body scale: if every massive body has
its own 7D_g ball, the boundary between balls should leave empirical
traces.

Three pre-registered axes (substrate roster locked before any
analysis per Meta-lesson 1):

- AXIS 1 — Heliopause distance vs Sun's 7D_g ball boundary; n=2 (Voyager 1+2)
- AXIS 2 — Galactic Faraday rotation vs stellar density; n=4 latitude bins
- AXIS 3 — Close binary magnetic spectra vs inter-component d_geom; n=5

Strict-spec d_geom = 2GM/(c²R); no metaphorical extension. NDJSON outputs.

## Findings

### Axis 1 — Heliopause distance

Observed mean R_HP = 120.3 AU (Stone+2013, +2019). Standard
ram-pressure model (Parker 1958; Burlaga 2015) predicts R_HP = 97.8 AU
under canonical solar-wind / LIC parameters; observed is 1.23× larger.
At observed R_HP, d_geom_Sol = 1.64e-10; at predicted R_HP,
d_geom_Sol = 2.02e-10. These agree to factor 1.24.

VERDICT: UNIT-CONSISTENT-WEAK-N2.

The math is sound — d_geom evaluated at the heliopause is the same
order of magnitude whether you anchor it on the observation or on
the ram-pressure prediction. But this is not a discrimination — the
standard ram-pressure model is also "consistent" at the same order
of magnitude. With n=2 and a 24% disagreement between observation
and standard model, there is no clean lever to claim the framework
predicts better.

### Axis 2 — Faraday rotation vs stellar density

Pre-registered 4 Galactic latitude bins (|b|<5, 5-10, 10-30, >30).
Pearson r(log RM, log proxy) for five proxies:

| Proxy | r |
|-------|---|
| n_e (NE2001) | 0.9998 |
| stellar density (Gaia DR3) | 0.9942 |
| n_e × H I | 0.9968 |
| H I (HI4PI) | 0.9923 |
| CO (Dame+2001) | 0.9825 |

All proxies correlate >0.98 with RM at latitude-bin scale because
they ALL track Galactic-disk concentration. The standard-model proxy
(n_e, which directly enters the RM formula) wins narrowly. Stellar
density does NOT dominate; framework prediction of
"stellar-density-led" does not discriminate.

VERDICT: DEGENERATE-LAT-SCALE-NO-DISCRIMINATION.

This is a NULL result not a falsification. Pixel-level analysis
at HEALPix Nside=64 over the Oppermann all-sky map vs Gaia DR3
stellar density at the same resolution WOULD test the framework at
sub-disk-scale-height angular scales where stellar density does
NOT track H I. That analysis is out of timebox for this spike.

### Axis 3 — Close binary magnetic spectra

Five pre-registered systems: V471 Tau (WD+K2V), BY Dra (K4V+K7V),
RS CVn (F4IV+G9IV), AR Lac (G2IV+K0IV), YY Gem (M0Ve+M0Ve).

Defined R_HE (Harmonic Enhancement) = B_observed / B_predicted_singlestar.
Framework predicts r(log d_geom_intercomponent, log R_HE) > 0 with
synchronized systems showing R_HE > 1.

ORIGINAL result: r = -0.851 (anti-prediction).
ANOMALY INVESTIGATED.

Cause: (a) V471 Tau B_obs of 350 G was the WD measurement
(Kawka+2007), not the K-dwarf companion which is the magnetically-
active member; correct K-dwarf value is ~1500 G (Hussain+2006 MNRAS
367:1699). (b) Naive Skumanich scaling underestimates B_pred for
saturated-regime fast rotators; Saar-Reiners empirical saturation
at ~3500 G for P_rot < 3.9 d is more honest.

CORRECTED result: r = -0.249. Mean R_HE_synchronized = 0.65;
mean R_HE_nonsynchronized = 0.71. The synchronized systems do NOT
exceed predicted saturation; the framework's positive-correlation
prediction is not supported.

But this corrected result is also NOT a clean falsification:
Saar-Reiners saturation mathematically forces R_HE flat over the
range 0.3-1.3 for all P_rot < 3.9 d systems, removing most of the
d_geom signal a priori. The test as constructed is underpowered.

VERDICT: NULL-AFTER-CORRECTION.

A genuine inter-ball coupling test would Fourier-decompose
photometric light curves of synchronized binaries to find spectral
content at n×P_orb beyond the fundamental, controlling for
ellipsoidal variation. Out of timebox.

## Cross-axis synthesis

Three NULL or WEAK axes. NO consolidated empirical support for the
candidate stance "magnetic_field_is_2d_boundary_of_7d_g_ball" at
inter-body scale that goes beyond intra-body Spike #143 results.

Specifically:
- Axis 1 cannot discriminate framework from ram-pressure model.
- Axis 2 is degenerate at gross spatial scale.
- Axis 3 returns null after data-quality correction; underpowered a priori.

**The intra-body Spike #143 d_geom-monotone signal is unaffected.**
That finding (Axis 2 Pearson r = 0.77, p<0.05 one-tailed, on
intra-body solar-system bodies) stands on its own. What Spike #144
shows is that the SAME framework conjecture does NOT cleanly extend
to inter-body scales using these specific tests.

## Stance candidate disposition

The pre-spike stance candidate `magnetic_field_is_2d_boundary_of_7d_g_ball`
remains HELD pending consolidated decision. Spike #144 provides
neither confirmation nor falsification. Conductor decision needed
on whether:

(a) Hold and dispatch follow-up spikes targeted at the underpowered
    aspects of axes 2 and 3 (pixel-level RM map; photometric Fourier
    binary search; magnetar QPO).
(b) Hold pending different empirical anchors (e.g. planetary nebula
    magnetic structure; pulsar wind nebula boundary; Lagrange-point
    field measurements).
(c) Reframe the stance to "intra-body-only" pending further evidence
    at inter-body scale.

This is a FERMATA — a deliberate pause-point for conductor input.
The concertmaster does not unilaterally promote, dissolve, or
reframe vocabulary-impact stances per the brief.

## Fermata items for conductor

1. Stance candidate disposition (above) — three options.
2. Whether to commission pixel-level Axis 2 follow-up spike.
3. Whether to broaden Axis 3 to magnetar QPO regime (much stronger
   framework signal expected if correct; harder substrate to
   compute against).
4. Whether the inter-body extension is itself a hypothesis that
   needs more careful pre-spike framework derivation before more
   data work.

## Discipline anchors honored

- Pre-registered roster (Meta-lesson 1)
- Math-doesn't-lie (negative Axis 3 reported as-found; investigated; corrected; null reported)
- PDF-extraction citation discipline (Stone, Oppermann, Hussain refs verified)
- 14 A-N classes intact (no vocabulary changes proposed)
- No lineage claims
- Trauma-informed defensive scope (this is fundamental physics, not weaponizable)
- NDJSON outputs throughout
- Concertmaster discipline: stance HELD; conductor decision required

## Files produced

- `spike144_substrate_roster_pre_registration.md` — pre-registered roster
- `spike144_axis1_heliopause.py` + `spike144_axis1_findings.ndjson`
- `spike144_axis2_faraday_stellar.py` + `spike144_axis2_findings.ndjson`
- `spike144_axis3_close_binaries.py` + `spike144_axis3_findings.ndjson`
- `spike144_axis3_anomaly_investigation.py` + `spike144_axis3_corrected_findings.ndjson`
- `spike144_overall_synthesis.py` + `spike144_overall_synthesis.ndjson`
- `spike144_findings_2026-05-19.ndjson` — consolidated findings (one record per axis)
- `spike144_section_draft.md` — this file
