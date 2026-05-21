# Spike #144 — Substrate Pre-Registration

**Date**: 2026-05-18
**Spike type**: Empirical inter-body 7D_g ball boundary signatures
**Branch**: `worktree-agent-aa6355b78705b7fce` (to be aligned with `research/spike-144-inter-body-7dg-ball-boundary-signatures` by conductor)
**Parent stances**: `[[user_stance_dark_sector_in_7d_g_gauge_space]]`, `[[user_stance_substrate_identity_partition_coexistence_canonical]]`, `[[user_stance_universal_precession_at_substrate_level]]`, `[[user_stance_saturation_overpressure_quartet_canonical]]`, `[[user_stance_mismatched_plates_capacitor_structure]]`, `[[project_space_gauge_time_framework]]`, `[[feedback_multi_domain_multi_round_survival_falsification_method]]`

## Tuning A 440 Hz

- Math doesn't lie; report as found
- MPM discipline; cite-by-ref for paywalled
- NDJSON output; one record per finding/body
- Strict spec: d_geom = 2GM/(c²R) only (Meta-lesson 2)
- Sample-selection-bias check before claiming universality (Meta-lesson 1)
- 14-class A-N vocabulary intact
- No lineage claims about external researchers
- Trauma-informed defensive scope (astrophysics, planetary, stellar)
- Cite-by-ref TOS landscape

## Stance candidate under test (HELD pending consolidated decision)

Working candidate name (per brief): `magnetic_field_is_2d_boundary_of_7d_g_ball`.
Claim: **magnetic field structure at INTER-body scale IS the 2D boundary between adjacent 7D_g balls**. Composes with intra-body Spike #143 d_geom-driver (boundary RADIUS dependence on d_geom of source body) and with `[[user_stance_dark_sector_in_7d_g_gauge_space]]` (non-selected Class C orientations carry dark sector — the ball-interior content is gauge-fiber).

## Pre-registered substrate selection criteria

### AXIS 1 — Heliosphere boundary location
**Selection criterion**: NASA/ESA primary heliospheric probes that crossed the heliopause OR provided in-situ termination-shock / heliopause distance measurements.
- Voyager 1 (TS 94 AU, HP 121.6 AU)
- Voyager 2 (TS 84 AU, HP 119 AU)
- New Horizons (in-flight; pickup ion observations)
- IBEX ENA map (Energetic Neutral Atom imaging)
- Cassini ENA observations
- Pioneer 10/11 (no HP crossing, but plasma envelope data)

**Why principled**: every spacecraft that has provided HP-distance data in the literature is included. No selection FOR or AGAINST the framework prediction. Pre-spike list.

**Framework prediction (strict-spec)**: HP_distance ≈ k × √(d_geom_Sol) × (some scaling); test whether observed HP distance is consistent with d_geom-driven 7D_g ball boundary radius for the Sun.

**Standard model**: HP location set by ram pressure balance between solar wind dynamic pressure and ISM total pressure (Parker 1961). HP ~ √(P_SW/P_ISM) which scales as √(M_dot × v_SW / P_ISM).

### AXIS 2 — Galactic Faraday rotation
**Selection criterion**: published all-sky Faraday rotation measure catalogs with stellar density / neutral hydrogen / molecular cloud cross-correlations.
- NVSS RM catalog (Taylor, Stil, Sunstrum 2009) — primary
- LOFAR RM catalogs (Van Eck et al.)
- Planck Galactic foreground RM (cite-by-ref)
- Oppermann et al. 2012 Galactic Faraday sky reconstruction

**Cross-correlation tracers**:
- Stellar density: Gaia DR3 source density (open) per visible-matter proxy
- Neutral hydrogen: HI4PI all-sky 21cm survey (Bekhti et al. 2016) — open
- Molecular clouds: CO survey of Dame, Hartmann, Thaddeus 2001 — cite-by-ref

**Why principled**: standard Galactic magnetic field models (Jaffe et al. 2010; Jansson-Farrar 2012) explicitly treat magnetic field as warm-ionised-medium + cold-neutral-medium superposition, with stellar density entering only via cosmic-ray-driven dynamo arguments. Framework predicts stellar density should be DIRECTLY correlated with |RM| structure (NOT via cosmic ray mediation), MORE than HI / CO tracers.

**Framework prediction**: |RM| correlates more strongly with log(stellar density) than with log(HI column) or log(CO intensity). This is a stronger prediction than standard model (which predicts HI/CO domination).

### AXIS 3 — Close binary magnetic spectra
**Selection criterion**: short-period (P_orb < 10 days) stellar binaries with documented magnetic field spectra, prioritising those with X-ray + radio observations enabling spectral structure determination.

Candidate roster (pre-spike, principled):
- RS CVn systems (canonical magnetically-active binaries)
- Algol-type eclipsing binaries
- CVs (cataclysmic variables; magnetic CVs especially: polars / intermediate polars)
- BY Dra-type stars (rotation-modulated activity, not binaries strictly but related)
- HR 1099 (V711 Tau) — well-studied RS CVn
- AR Lac — well-studied RS CVn
- AM Her, V1500 Cyg — magnetic CV references
- RW Lac, σ² CrB — eclipsing magnetic binaries

**Why principled**: every magnetically-active binary class in canonical stellar-activity literature has at least one representative. Selection NOT based on whether harmonic structure is unusual.

**Framework prediction**: inter-ball-boundary coupling should produce magnetic spectral features at integer harmonics of orbital frequency f_orb that exceed standard rotational-modulation single-fundamental prediction. Specifically: power at 2 f_orb, 3 f_orb, 4 f_orb above single-modulation prediction. This is a specific signature beyond Lorentzian noise + single rotational fundamental.

**Standard model**: rotational modulation produces fundamental f_rot + possibly weak 2 f_rot due to active region spatial pattern. Inter-ball-coupling adds higher harmonics that are NOT explained by rotational geometry alone.

## Method

Per-axis NDJSON output:
- `spike144_axis1_heliosphere_findings.ndjson`
- `spike144_axis2_faraday_findings.ndjson`
- `spike144_axis3_binary_findings.ndjson`
- `spike144_overall_synthesis.ndjson`

Per-axis scripts in `spike144_axis{1,2,3}_*.py` (Python; deterministic; no SGD).

Anti-stall pattern: each axis emits findings incrementally (no end-of-script-only dump); small batch sizes; no long-blocking computations expected.

## Disciplines

- 14-class A-N vocabulary stays intact; no new primitive class
- PDF extraction verification only where claimed-by-reference can be doubted
- Cite-by-ref for paywalled (most heliospheric probe data summary papers; many Faraday catalogs)
- Identity-not-implementation: framework claims at substrate-relation level
- No squash merges
- Worktree isolation verified
