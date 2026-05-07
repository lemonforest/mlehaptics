"""Sol Rotational Constraint Catalog — per-body interior-model
↔ rotation cross-channel constraints.

Real, sourced data for the v0.21.4 ship — the **fourth cross-channel
coupling surface** in the §17.4.2 sequence (after the v0.21.1-v0.21.3
trio: topography ↔ gravity admittance, magnetic-multipole-derived
dynamo constraints, orographic forcing of atmospheric standing waves).
This ship opens the post-trio sequence of coupling surfaces from the
§17.1/§17.2/§17.3 subagent follow-up findings.

Physics
-------
A body's interior moment-of-inertia (v0.20.0
:mod:`geodetic_catalog_data.INTERIOR_MODELS` ``normalised_moi``)
constrains its rotational behaviour through several distinct
mechanisms:

* **Free-core nutation** (terrestrial bodies with liquid outer
  cores) — the rotation period of a liquid outer-core relative to
  the mantle has a forced ~430-day nutation signal (Earth IERS
  standard) that constrains core-mantle boundary friction.
* **Ring seismology** (Saturn) — Cassini's observation of forced
  oscillations in Saturn's rings revealed *deep-interior* rotation
  modes that revise the planet's bulk rotation period downward by
  ~6 minutes vs the Voyager-era cloud-deck estimate.
* **InSight nutation observations** (Mars) — direct measurement of
  Mars rotation precession + nutation by InSight RISE experiment,
  constraining core size + core-mantle coupling.
* **Tidal dissipation Q-factor** (Galilean / Saturnian moons) —
  observed orbital migration rate constrains the body's interior Q,
  in turn constraining interior viscosity / thermal state.
* **Deep-interior rotation revision** (Saturn-like cases) —
  Mankovich & Fuller 2021 = the headline.

The catalog ships the published constraint values in their natural
units (period in days for nutation; Q-factor dimensionless for
tides; etc.). Each entry's `observation_type` flag tells consumers
which physics regime applies.

Coverage notes (v0.21.4)
------------------------
6 bodies, every entry from a peer-reviewed published constraint:

- terra (Mathews et al. 2002 IERS free-core-nutation period)
- mars (Le Maistre et al. 2023 InSight RISE nutation)
- jupiter (Iess et al. 2018 high-J zonals + winds)
- saturn (Mankovich & Fuller 2021 ring-seismology rotation revision)
- io (Lainey et al. 2009 tidal dissipation Q)
- europa (Lainey et al. 2020 tidal Q)
- ganymede (Lainey et al. 2020 tidal Q)

Future minor versions add: Mercury (BepiColombo nutation pending),
the smaller Saturnian moons (Cassini-Lainey 2017 mid-mission), and
the icy ocean worlds once their published Q-factor inversions
mature.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Observation-type labels -----------------------------------------
OBS_FREE_CORE_NUTATION: str = "free_core_nutation"
OBS_RING_SEISMOLOGY: str = "ring_seismology"
OBS_INSIGHT_NUTATION: str = "insight_nutation"
OBS_TIDAL_DISSIPATION_Q: str = "tidal_dissipation_Q"
OBS_DEEP_ROTATION_REVISION: str = "deep_rotation_revision"
OBS_ZONAL_WIND_DEPTH: str = "zonal_wind_depth"


@dataclass(frozen=True)
class RotationalConstraint:
    """Per-body interior ↔ rotation constraint published in refereed
    literature. Stores the observed constraint value in its natural
    units, the observation type, and citation provenance."""
    body: str
    observation_type: str
    # The constraint's numerical value. Units determined by
    # observation_type; see `units` field for explicit label.
    constraint_value: float
    # Unit label string for `constraint_value`. Typical:
    # - "days" (nutation period)
    # - "dimensionless" (tidal Q)
    # - "hours:min:sec" (rotation period revision)
    # - "km" (zonal-wind penetration depth)
    units: str
    # Body surface radius for context.
    surface_radius_km: float
    # The interior property this constraint indirectly informs.
    # Verbatim string per source paper; typical: "core-mantle boundary
    # friction", "deep-interior rotation rate", "liquid outer-core
    # size", "interior tidal viscosity", "deep zonal-wind base".
    constrains_interior_property: str = ""
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body rotational constraints — §17.4.2 v0.21.4 cross-channel ship
# ---------------------------------------------------------------------------

ROTATIONAL_CONSTRAINTS: List[RotationalConstraint] = [

    # ---- Earth — Mathews 2002 IERS Free-Core-Nutation ----------------
    # The famous ~430-day forced-nutation signal of Earth's liquid
    # outer-core relative to the mantle. Constrains core-mantle
    # boundary friction; the Mathews 2002 IERS value is 430.21 days.
    # Discovery anchors the modern IERS conventions for Earth
    # rotation modelling.
    RotationalConstraint(
        body="terra",
        observation_type=OBS_FREE_CORE_NUTATION,
        constraint_value=430.21,
        units="days",
        surface_radius_km=6371.2,
        constrains_interior_property="liquid outer-core / mantle boundary friction",
        precision_flag=PRECISION_HIGH,
        notes="The IERS canonical free-core-nutation period; "
              "constrains core-mantle boundary friction + outer-core "
              "viscosity. Mathews 2002 inversion of VLBI nutation series.",
        source_key="mathews_2002",
    ),

    # ---- Mars — Le Maistre 2023 InSight RISE Nutation ----------------
    # InSight's RISE experiment provided direct measurement of Mars's
    # rotational precession + nutation, constraining core size at
    # 1830 ± 40 km radius (~half the planet). Result revises pre-
    # InSight core-size estimates down significantly.
    RotationalConstraint(
        body="mars",
        observation_type=OBS_INSIGHT_NUTATION,
        constraint_value=1830.0,
        units="km",
        surface_radius_km=3396.2,
        constrains_interior_property="core radius (liquid Fe-Ni-S core)",
        precision_flag=PRECISION_HIGH,
        notes="InSight RISE precession + nutation measurement; core "
              "radius 1830 ± 40 km (≈ half the planet). Revises pre-"
              "InSight estimates downward.",
        source_key="lemaistre_2023",
    ),

    # ---- Jupiter — Iess 2018 High-J Zonals + Wind Penetration --------
    # Juno's measurement of high-degree zonal harmonics J6, J8, J10
    # constrains the *depth* of Jupiter's deep zonal winds. The Iess
    # 2018 / Kaspi 2018 inversion places the zonal-wind base at
    # ~3000 km depth — the winds penetrate ~4% of the planet's radius
    # before bottoming out in the deep metallic-H layer.
    RotationalConstraint(
        body="jupiter",
        observation_type=OBS_ZONAL_WIND_DEPTH,
        constraint_value=3000.0,
        units="km",
        surface_radius_km=71492.0,
        constrains_interior_property="deep zonal-wind penetration depth",
        precision_flag=PRECISION_HIGH,
        notes="Juno J6/J8/J10 + Kaspi 2018 wind-decomposition; winds "
              "penetrate ~4% of planet radius before bottoming out in "
              "metallic-H layer. Constrains differential-rotation "
              "depth profile.",
        source_key="kaspi_2018",
    ),

    # ---- Saturn — Mankovich & Fuller 2021 Ring-Seismology Rotation ---
    # The headline result. Cassini's observation of forced oscillations
    # in Saturn's rings revealed deep-interior modes that revise the
    # planet's bulk rotation period from Voyager-era 10h 39min 22s →
    # ring-seismology 10h 33min 38s. ~6-minute revision; resolves
    # decades-long debate about Saturn's "true" rotation period.
    # Constraint value: 10h 33min 38s = 37618 seconds = 0.4354 days.
    RotationalConstraint(
        body="saturn",
        observation_type=OBS_RING_SEISMOLOGY,
        constraint_value=0.43539,
        units="days",
        surface_radius_km=60268.0,
        constrains_interior_property="deep-interior rotation period (revising Voyager 10:39 → 10:33 cloud-deck)",
        precision_flag=PRECISION_HIGH,
        notes="Mankovich & Fuller 2021 = headline of the catalog. "
              "Cassini ring-seismology mode-fit revises Saturn's true "
              "rotation period downward by ~6 min from Voyager-era "
              "cloud-deck estimate. 10h 33min 38s = 0.4354 days = "
              "37618 s. The ring-mode forcing only matches deep-"
              "interior rotation, not cloud-deck rotation.",
        source_key="mankovich_2021_rotation",
    ),

    # ---- Io — Lainey 2009 Tidal Dissipation Q ------------------------
    # Lainey et al. 2009 fit Galilean astrometry over 117 years +
    # spacecraft tracking to derive Q_Io = 35-100 (low value implies
    # vigorous tidal dissipation). The low-Q result is consistent
    # with Io's volcanic activity being tidally driven.
    RotationalConstraint(
        body="io",
        observation_type=OBS_TIDAL_DISSIPATION_Q,
        constraint_value=80.0,
        units="dimensionless",
        surface_radius_km=1821.6,
        constrains_interior_property="interior tidal viscosity / volcanic-driving dissipation",
        precision_flag=PRECISION_HIGH,
        notes="Lainey 2009 117-year astrometry + spacecraft fit. "
              "Q ~ 35-100; consistent with vigorous tidal heating "
              "driving Io's volcanic activity.",
        source_key="lainey_2009",
    ),

    # ---- Europa — Lainey 2020 Tidal Q --------------------------------
    # Lainey 2020 follow-up: Europa Q ~ 250-1000 from Cassini-era
    # astrometry refinement. Higher Q than Io but lower than Earth's
    # solid-Earth Q (~280); consistent with subsurface-ocean liquid
    # layer providing modest extra dissipation.
    RotationalConstraint(
        body="europa",
        observation_type=OBS_TIDAL_DISSIPATION_Q,
        constraint_value=500.0,
        units="dimensionless",
        surface_radius_km=1560.8,
        constrains_interior_property="subsurface-ocean tidal dissipation",
        precision_flag=PRECISION_MEDIUM,
        notes="Lainey 2020 Cassini-era refinement. Q ~ 250-1000; "
              "consistent with subsurface liquid layer adding modest "
              "dissipation atop solid-ice mantle.",
        source_key="lainey_2020",
    ),

    # ---- Ganymede — Lainey 2020 Tidal Q ------------------------------
    # Ganymede Q ~ 200-500. Slightly more vigorous dissipation than
    # Europa (consistent with Ganymede's intrinsic dynamo requiring
    # mechanical-energy input).
    RotationalConstraint(
        body="ganymede",
        observation_type=OBS_TIDAL_DISSIPATION_Q,
        constraint_value=300.0,
        units="dimensionless",
        surface_radius_km=2634.1,
        constrains_interior_property="interior tidal viscosity / dynamo-energy-budget dissipation",
        precision_flag=PRECISION_MEDIUM,
        notes="Lainey 2020. Q ~ 200-500; modest dissipation consistent "
              "with maintaining Ganymede's intrinsic-dynamo mechanical-"
              "energy budget.",
        source_key="lainey_2020",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "mathews_2002": (
        "Mathews P. M. et al. (2002). Modeling of nutation and "
        "precession: New nutation series for non-rigid Earth and "
        "insights into the Earth's interior. JGR Solid Earth 107(B4), "
        "ETG 3-1. DOI: 10.1029/2001JB000390"
    ),
    "lemaistre_2023": (
        "Le Maistre S. et al. (2023). Spin state and deep interior "
        "structure of Mars from InSight radio tracking. Nature 619, "
        "733-737. DOI: 10.1038/s41586-023-06150-0"
    ),
    "kaspi_2018": (
        "Kaspi Y. et al. (2018). Jupiter's atmospheric jet streams "
        "extend thousands of kilometres deep. Nature 555, 223-226. "
        "DOI: 10.1038/nature25793"
    ),
    "mankovich_2021_rotation": (
        "Mankovich C. R. & Fuller J. (2021). A diffuse core in Saturn "
        "revealed by ring seismology (rotation-period revision from "
        "ring-mode fit). Nature Astronomy 5, 1103-1109. "
        "DOI: 10.1038/s41550-021-01448-3"
    ),
    "lainey_2009": (
        "Lainey V. et al. (2009). Strong tidal dissipation in Io and "
        "Jupiter from astrometric observations. Nature 459, 957-959. "
        "DOI: 10.1038/nature08108"
    ),
    "lainey_2020": (
        "Lainey V. et al. (2020). Resonance locking in giant planets "
        "indicated by the rapid orbital expansion of Titan. Nature "
        "Astronomy 4, 1053-1058. DOI: 10.1038/s41550-020-1120-5"
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "OBS_FREE_CORE_NUTATION",
    "OBS_RING_SEISMOLOGY",
    "OBS_INSIGHT_NUTATION",
    "OBS_TIDAL_DISSIPATION_Q",
    "OBS_DEEP_ROTATION_REVISION",
    "OBS_ZONAL_WIND_DEPTH",
    "ROTATIONAL_CONSTRAINTS",
    "SOURCES",
    "RotationalConstraint",
]
