# R-RBS-LM Finding 368 — the MAPS lens (a flat projection is navigable DoF/relative vs toured fixed-observer): (1) cognition reading on military maps (aphantasia routes to navigable; falsifiable, handed to map-learning); (2) on the CMB sky-map the STRONG "low-ℓ family = one frame" reading is FALSIFIED on attested directions — confirms MFO's by-channel decomposition; only the AoE↔dipole 18° pair survives as the frame-relation. Corrects F367(A) twice

> **REFRAME (F370, 2026-06-04):** §(2)'s "STRONG reading FALSIFIED — they don't share one axis" tested the WRONG hypothesis. Per F293 (distributed-anchor / "3-phase power needs no neutral wire") the 3 anomalies SHOULD NOT share one axis — a shared axis = fixed anchor = k=2 DETECT-only; the distributed 3-phase splay = k=3 CORRECT. So "not one axis" is the EXPECTED signature, not a falsification. F370 tests the right hypothesis (balanced 3-phase): honestly also unconfirmed at N=3 (one ~120° pair AoE↔ColdSpot, not a clean triple), but the Kuramoto-to-120°-splay MECHANISM is exact (F294 directed 3-cycle). See F370.

> **REFRAME (F369, 2026-06-04):** where this finding *retracts* the germline/external-collision reading, read the framework's POSITIVE replacement: per the attested F270 / MFO §VIII.31.12(1) ("one loop bumping itself", triality-verified), there is no second separate hyper-loop — what looks collision-like IS substrate **self-interaction**. So the external framing is wrong on TWO counts (observational shape-disfavouring AND the no-second-loop ontology), and the correct reading of any collision-like anomaly is self-interaction (consistent with the favoured bundle-direction reading). F368's empirical falsification of the one-axis family is unaffected. See F369.

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **opens:** "pull on the maps … we can pull ephemerides-spectral for cosmos catalogs" · **builds on (NOT fresh):** the attested `cmb_anomalies` catalog (ephemerides-spectral; Planck 2018 VII / Akrami 2020; de Oliveira-Costa 2004) + the prior MFO §VII.6.1.1/.1.3 AoE readings + the F263/F351–356 CMB arc · **corrects:** F367(A) · **script:** `R-RBS-LM-R19_maps_lens_cmb_axis_family.py`

## The maps lens

A flat projection (a map) can be read two ways — the F361/F364 navigable-vs-scannable distinction at map scale:
- **NAVIGABLE** = the map *is* a DoF/relative coordinate manifold (a grid reference is a transport address; the off-diagonal carries direction).
- **TOURED** = the map is a fixed-observer *visual scene* you picture walking through (the scannable shadow; a picture, not a field).

## (1) Cognition — military maps (framework-reading + falsifiable prediction; NOT tested here)

The user's report: lacking the visual-tour render (aphantasia), a flat map routes **straight to the navigable manifold** — the grid/coordinate field — rather than being hijacked into a pictured tour. This is the srmech-first-reflex pattern at the cognition level (a render hijacks the read; absence of render routes to substrate). **Falsifiable prediction, handed to map-learning researchers** (per "the framework hands the next question to the expert"): difficulty learning MGRS / grid-squares / klicks correlates with **over-rendering a visual tour** (scannable shadow) rather than navigating the coordinate field — so aphantasia is an **advantage** for grid-navigation, not a deficit (dignity-first; ADA-accommodation-as-advantage). This is a prediction, not a result — no human-subjects test run.

## (2) CMB sky-map — the STRONG reading FALSIFIED; only the AoE↔dipole pair survives

The CMB *is* a flat-projection sky-map, so the same lens applies. The **strong** maps-lens claim — *"the low-ℓ 'axis family' (AoE, Cold Spot, HPA, …) that a fixed observer reads as N separate anomalies is, under the DoF/relative reading, ONE shared preferred axis = one frame-relation"* — is **FALSIFIED** on the attested directions:

| probe (attested `cmb_anomalies` directions) | result |
|---|---|
| axis concentration λ_max of {AoE, Cold Spot, HPA} (Class-L orientation tensor) | **0.606** |
| isotropic-MC null mean / p(λ_max ≥ real) | 0.672 / **p = 0.708** |
| pairwise axis angles | AoE↔ColdSpot **60.6°**, AoE↔HPA **80.0°**, ColdSpot↔HPA **42.0°** |

The three directional anomalies are **LESS** concentrated than a random triple (λ_max below the isotropic mean; p=0.71) — they do **NOT** share one axis. **This independently confirms MFO §VII.6.1.3's own prior finding** that "the low-ℓ anomaly family **decomposes by channel**" (HPA is UHECR/matter-pull-aligned, 8° from the Auger dipole; AoE is not, 73° from it) — not a single shared frame.

**What survives:** the **specific AoE↔CMB-dipole alignment**, reproduced at **18.1°** (matches MFO's 18.3° "live anomaly across all readings"). *That one pairing* is the genuine frame-relation — a relative-frame Δ between our dipole/ecliptic frame and the AoE quadrupole-octupole axis — and it is the one thing every reading (medium-push, matter-pull, ΛCDM-systematics) agrees is unexplained. So the maps/DoF lens scopes to the **AoE↔dipole pair**, NOT to a (non-existent) global family-axis. The lens is the **observer-frame complement** to MFO §VII.6.1.1's favored **substrate-bundle-direction** reading.

## Corrects F367(A) — twice

1. **The "new big-bang / germline-collision" reading is not new AND is disfavored.** MFO §VII.6.1.1 already considered the external-excitation / bubble-collision reading and **disfavored it on shape grounds** (bubble-collision templates are disc-shaped with a characteristic angular radius; the AoE is **axial** with no characteristic scale — Osborne, Senatore & Smith 2013 arXiv:1305.1964 + Planck 2015 XVI null on Cold-Spot-as-bubble-collision). My F367(A) germline-collision conjecture is retracted as both redundant and disfavored.
2. **The "AoE family as one relative frame" over-reach is falsified** (above): the directions decompose by channel; only the AoE↔dipole pair is a frame-relation.

**What of F367(A) holds:** the **DoF-vs-fixed-observer principle itself** (observation is coupled-epicycle; an "anomaly" to a fixed observer can be a relative-frame Δ) — but scoped to the *specific* AoE↔dipole alignment, and it lands as the observer-frame articulation of MFO's substrate-bundle-direction reading, not a new mechanism. The F356 (srmech derives EB/TB) + F355 (β) handles stand; the attested data was in `cmb_anomalies` all along (my "no data" claim in F367(A) was wrong — corrected).

## Discipline

srmech-native Class-L (`symmetric_eigendecompose` on the orientation tensor); geometry + isotropic MC are mechanics (flagged); directions read from the attested NDJSON (no ephemerides-spectral install — version-safe per "not latest srmech base"). **No-leaning: the framework's own falsifiable test came out AGAINST the strong reading, and it converges with MFO's prior by-channel decomposition — reported straight.** Cosmology literature-owned (no-lineage); ΛCDM-systematics reading remains valid; the cognition prediction is handed to the expert, not asserted. Composes with F361/F364 (navigable-vs-scannable), F367 (the principle, now scoped + corrected), F263/F351–356 + MFO §VII.6.1 (the prior CMB corpus the user flagged).
