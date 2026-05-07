"""Sol Luna Dynamical Spectrum — per-body action-angle decomposition
data for the v0.24.1 ship.

Real, sourced data for the **second per-body dynamical-spectrum
surface** in the v0.24.x sequence. Luna chosen as the natural complement
to v0.24.0 Mercury:

* Same "simple body, rich data" pattern: no atmosphere, no ocean.
* The canonical **Earth-tidal** case (Mercury was the canonical
  Sol-perturbation case).
* **Lunar Laser Ranging (LLR)** is the most precise libration
  measurement programme in the Solar System: 50+ years of millimetre-
  precision ranging from McDonald (1969), Apache Point (2006), OCA
  Grasse, and Matera observatories — providing the cleanest
  observational constraint on a planetary body's full dynamical
  spectrum.

Action-angle framing
--------------------
Luna's dynamical state factors into action-angle variables on a
**T^n × R^m phase space**:

* Angle variables (live on tori — periodic, modulo 2π):
  - **Sidereal mean motion** L_sid (orbital phase relative to fixed
    stars) — period 27.32166 d.
  - **Synodic mean motion** L_syn (orbital phase relative to Sun) —
    period 29.53059 d. The "month" of folk calendars; the STLT
    epoch's Metonic cycle is built on this.
  - **Anomalistic mean motion** L_an (orbital phase relative to
    perigee) — period 27.55455 d.
  - **Draconitic mean motion** L_dr (orbital phase relative to
    ascending node) — period 27.21222 d. Important for eclipses
    because the Sun must be at a node for a syzygy to produce one.
  - **Spin frequency** = sidereal mean motion (1:1 tidal lock).
  - **Forced libration in longitude**, ~7.9 arcsec amplitude
    (Williams 2014 LLR — most precise libration in the Solar
    System; cross-references v0.23.0 spin_orbit_resonance).
  - **Apsidal precession** (perigee advance) — period 8.8504 yr,
    forward (prograde).
  - **Nodal precession** (regression of nodes) — period 18.6134 yr,
    backward (retrograde). The famous "Saros precession".
* Action variables (live on real intervals — slowly varying):
  - **Eccentricity** e ≈ 0.0549 (varies 0.026-0.077 over decades).
  - **Inclination** to ecliptic ≈ 5.145°.
  - **Obliquity** of spin axis to orbital plane ≈ 6.687° (Cassini
    state 2 — the spin axis is tilted, with the spin axis
    precessing in lockstep with the regressing node).
  - **Normalised moment of inertia** C/MR² ≈ 0.3932 (Williams 2014).

The headline cross-channel observation
--------------------------------------
The **Saros cycle** (the famous 18.03-year eclipse-recurrence
period) emerges from a **small-integer commensurability of three
distinct lunar months**:

  223 synodic   × 29.53059   d = 6585.32   d
  239 anomalistic × 27.55455 d = 6585.54   d
  242 draconitic × 27.21222 d = 6585.36   d
  19  eclipse-years × 346.62 d = 6585.78   d

These four products agree to within ~0.5 day each — a textbook
small-denominator phenomenon. The integer triple (223, 239, 242)
is exactly the kind of structure the project's BIP encoder is
built to detect: three irrational-looking frequency ratios that
*do* happen to share a near-rational commensurability.

This is also the v0.24.1 spectral-fingerprint analogue of v0.24.0's
Le Verrier/Einstein perihelion-precession decomposition: the
catalog ships the Saros commensurability as a closure invariant —
the four 6585.x-day products must agree within ~0.5 day, pinned
in tests.

**Not a re-derivation.** Values are the published high-precision
ephemeris periods (Allen's Astrophysical Quantities; JPL DE441;
Williams 2014 LLR analysis; Newhall & Williams 1997).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Luna physical / orbital reference constants (J2000) ------------
# Allen's Astrophysical Quantities (4th ed.) + JPL DE441.
LUNA_SEMI_MAJOR_AXIS_KM: float = 384399.0           # Mean Earth-Moon distance
LUNA_ECCENTRICITY: float = 0.0549                    # Mean (varies 0.026-0.077)
LUNA_INCLINATION_TO_ECLIPTIC_DEG: float = 5.145      # Mean
LUNA_OBLIQUITY_TO_ORBIT_DEG: float = 6.687           # Spin axis tilt (Cassini state 2)
# Four classical lunar "months" — high precision (Allen's + DE441)
LUNA_SIDEREAL_MONTH_DAYS: float = 27.32166156
LUNA_SYNODIC_MONTH_DAYS: float = 29.53058886
LUNA_ANOMALISTIC_MONTH_DAYS: float = 27.55454988
LUNA_DRACONITIC_MONTH_DAYS: float = 27.21222082
LUNA_TROPICAL_MONTH_DAYS: float = 27.32158213        # ~sidereal (precessing equinox)
# Eclipse year (the year measured from one Sun-at-ascending-node to
# the next — used in Saros bookkeeping)
ECLIPSE_YEAR_DAYS: float = 346.620075

# ---- Williams 2014 LLR parameters -----------------------------------
# Williams J. G. & Boggs D. H. (2014). Lunar Laser Ranging libration
# analysis. JGR Planets 119, 1546-1578.
LUNA_FORCED_LIBRATION_LONGITUDE_ARCSEC: float = 7.9   # cross-references v0.23.0
LUNA_NORMALISED_MOI_C_OVER_MR2: float = 0.3932        # ± 0.0002
# 3.83 cm/yr secular drift cross-references v0.21.6 tidal_migration.

# ---- Precession periods --------------------------------------------
# Apsidal precession (perigee advance), prograde:
LUNA_APSIDAL_PRECESSION_YEARS: float = 8.8504
# Nodal precession (regression of nodes), retrograde:
LUNA_NODAL_PRECESSION_YEARS: float = 18.6134


# ---------------------------------------------------------------------------
# Action-angle mode catalog
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DynamicalMode:
    """One frequency mode in Luna's dynamical state.

    Mirrors the v0.24.0 Mercury catalog structure.
    """
    name: str
    frequency_per_century: float    # cycles/century
    period_days: float
    amplitude_value: float
    amplitude_units: str            # "arcsec" / "deg" / "dimensionless" / "km" / "yr"
    angle_or_action: str            # "angle" or "action"
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# ---- century in days, for cycles/century ----------------------------
_DAYS_PER_CENTURY: float = 36525.0


LUNA_DYNAMICAL_MODES: List[DynamicalMode] = [

    # ---- Sidereal mean motion --------------------------------------
    DynamicalMode(
        name="sidereal_mean_motion",
        frequency_per_century=_DAYS_PER_CENTURY / LUNA_SIDEREAL_MONTH_DAYS,
        period_days=LUNA_SIDEREAL_MONTH_DAYS,
        amplitude_value=2 * 3.141592653589793,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Orbital phase relative to fixed stars. The 'true' "
              "lunar month from a celestial-mechanics standpoint. "
              "Spin frequency is locked 1:1 with this mode.",
        source_key="allens_astrophysical_quantities",
    ),

    # ---- Synodic mean motion ---------------------------------------
    DynamicalMode(
        name="synodic_mean_motion",
        frequency_per_century=_DAYS_PER_CENTURY / LUNA_SYNODIC_MONTH_DAYS,
        period_days=LUNA_SYNODIC_MONTH_DAYS,
        amplitude_value=2 * 3.141592653589793,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Orbital phase relative to Sun (Sun-Earth-Moon "
              "geometry). The 'month' of folk calendars. The STLT "
              "Metonic cycle (v0.10.0 STLT_METONIC_CYCLE_DAYS) is "
              "235 of these; the Saros cycle is 223 of these.",
        source_key="allens_astrophysical_quantities",
    ),

    # ---- Anomalistic mean motion -----------------------------------
    DynamicalMode(
        name="anomalistic_mean_motion",
        frequency_per_century=_DAYS_PER_CENTURY / LUNA_ANOMALISTIC_MONTH_DAYS,
        period_days=LUNA_ANOMALISTIC_MONTH_DAYS,
        amplitude_value=2 * 3.141592653589793,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Orbital phase relative to perigee. Differs from "
              "sidereal because perigee precesses (apsidal "
              "precession 8.85 yr). The Saros cycle is 239 of "
              "these; the integer commensurability with synodic "
              "(223) sets the eclipse-recurrence pattern.",
        source_key="allens_astrophysical_quantities",
    ),

    # ---- Draconitic mean motion ------------------------------------
    DynamicalMode(
        name="draconitic_mean_motion",
        frequency_per_century=_DAYS_PER_CENTURY / LUNA_DRACONITIC_MONTH_DAYS,
        period_days=LUNA_DRACONITIC_MONTH_DAYS,
        amplitude_value=2 * 3.141592653589793,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Orbital phase relative to ascending node. Differs "
              "from sidereal because nodes regress (nodal "
              "precession 18.61 yr). The Saros cycle is 242 of "
              "these. Eclipses require Sun-at-node, so this period "
              "controls the eclipse-season cycle.",
        source_key="allens_astrophysical_quantities",
    ),

    # ---- Spin frequency (1:1 tidal lock) ---------------------------
    DynamicalMode(
        name="spin_frequency",
        frequency_per_century=_DAYS_PER_CENTURY / LUNA_SIDEREAL_MONTH_DAYS,
        period_days=LUNA_SIDEREAL_MONTH_DAYS,
        amplitude_value=2 * 3.141592653589793,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Spin phase, locked 1:1 with sidereal orbital motion "
              "(synchronous rotation; cross-references v0.23.0 "
              "spin_orbit_resonance). Tiny libration superposed.",
        source_key="williams_2014",
    ),

    # ---- Forced libration in longitude (Williams 2014 headline) ----
    DynamicalMode(
        name="forced_libration_longitude",
        frequency_per_century=_DAYS_PER_CENTURY / LUNA_SIDEREAL_MONTH_DAYS,
        period_days=LUNA_SIDEREAL_MONTH_DAYS,
        amplitude_value=LUNA_FORCED_LIBRATION_LONGITUDE_ARCSEC,
        amplitude_units="arcsec",
        angle_or_action="angle",
        notes="Physical libration in longitude — Williams 2014 LLR. "
              "MOST PRECISELY-MEASURED LIBRATION IN THE SOLAR SYSTEM "
              "via 50+ years of Lunar Laser Ranging. The "
              "measurement that constrains C/MR² = 0.3932 ± 0.0002. "
              "Cross-references v0.23.0 spin_orbit_resonance Luna "
              "entry (must agree at 7.9 arcsec).",
        source_key="williams_2014",
    ),

    # ---- Apsidal precession (perigee advance) ---------------------
    DynamicalMode(
        name="apsidal_precession",
        frequency_per_century=100.0 / LUNA_APSIDAL_PRECESSION_YEARS,
        period_days=LUNA_APSIDAL_PRECESSION_YEARS * 365.25,
        amplitude_value=LUNA_APSIDAL_PRECESSION_YEARS,
        amplitude_units="yr",
        angle_or_action="angle",
        notes="Perigee precesses prograde with 8.85-year period. "
              "Driven primarily by Sun's gravitational perturbation "
              "(dominant term) plus Earth-J₂ + GR Schwarzschild + "
              "tidal corrections. Anomalistic ≠ sidereal because of "
              "this precession.",
        source_key="murray_dermott_1999",
    ),

    # ---- Nodal precession (Saros precession; regression of nodes) -
    DynamicalMode(
        name="nodal_precession",
        frequency_per_century=-100.0 / LUNA_NODAL_PRECESSION_YEARS,
        period_days=LUNA_NODAL_PRECESSION_YEARS * 365.25,
        amplitude_value=LUNA_NODAL_PRECESSION_YEARS,
        amplitude_units="yr",
        angle_or_action="angle",
        notes="Nodes regress (retrograde) with 18.61-year period. "
              "Drives the famous 18.6-yr 'lunar standstill' cycle "
              "in observed lunar declination range; controls "
              "eclipse-season geometry (with synodic + anomalistic "
              "produces the 18.03-yr Saros cycle).",
        source_key="murray_dermott_1999",
    ),

    # ---- Eccentricity (action-class) ------------------------------
    DynamicalMode(
        name="eccentricity",
        frequency_per_century=0.0,
        period_days=0.0,
        amplitude_value=LUNA_ECCENTRICITY,
        amplitude_units="dimensionless",
        angle_or_action="action",
        notes="Mean orbital eccentricity (action-class variable). "
              "Varies 0.026-0.077 over decades because of solar "
              "perturbation; mean value 0.0549.",
        source_key="jpl_de441",
    ),

    # ---- Inclination (action-class) -------------------------------
    DynamicalMode(
        name="inclination_to_ecliptic",
        frequency_per_century=0.0,
        period_days=0.0,
        amplitude_value=LUNA_INCLINATION_TO_ECLIPTIC_DEG,
        amplitude_units="deg",
        angle_or_action="action",
        notes="Inclination of orbital plane to ecliptic. Mean value; "
              "varies ±9 arcmin over the 18.61-yr nodal-regression "
              "cycle.",
        source_key="jpl_de441",
    ),

    # ---- Obliquity (action-class — Cassini state 2) ---------------
    DynamicalMode(
        name="obliquity_to_orbit",
        frequency_per_century=0.0,
        period_days=0.0,
        amplitude_value=LUNA_OBLIQUITY_TO_ORBIT_DEG,
        amplitude_units="deg",
        angle_or_action="action",
        notes="Spin-axis obliquity to orbital plane. Luna occupies "
              "Cassini state 2 — spin axis precesses in lockstep "
              "with the regressing nodal axis (period 18.61 yr). "
              "Larger than Mercury's Cassini-state-1 obliquity "
              "(2 arcmin); reflects different equilibrium branch.",
        source_key="cassini_1693",
    ),
]


# ---------------------------------------------------------------------------
# The Saros commensurability — THE headline closure invariant
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SarosCommensurability:
    """One row in the Saros integer-commensurability invariant.

    The Saros cycle (~18.03 yr eclipse-recurrence period) emerges
    from the integer commensurability of synodic, anomalistic, and
    draconitic months + the eclipse year. Each row is one of the
    four products; the closure invariant is that all four products
    agree within ~0.5 day.
    """
    name: str
    integer_count: int
    unit_period_days: float
    product_days: float
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# Compute products eagerly so consumers can inspect raw values:
_SAROS_223_SYNODIC: float = 223 * LUNA_SYNODIC_MONTH_DAYS
_SAROS_239_ANOMALISTIC: float = 239 * LUNA_ANOMALISTIC_MONTH_DAYS
_SAROS_242_DRACONITIC: float = 242 * LUNA_DRACONITIC_MONTH_DAYS
_SAROS_19_ECLIPSE_YEAR: float = 19 * ECLIPSE_YEAR_DAYS


SAROS_COMMENSURABILITY: List[SarosCommensurability] = [
    SarosCommensurability(
        name="223_synodic_months",
        integer_count=223,
        unit_period_days=LUNA_SYNODIC_MONTH_DAYS,
        product_days=_SAROS_223_SYNODIC,
        notes="223 lunations (Sun-Earth-Moon configuration repeats).",
        source_key="meeus_1991",
    ),
    SarosCommensurability(
        name="239_anomalistic_months",
        integer_count=239,
        unit_period_days=LUNA_ANOMALISTIC_MONTH_DAYS,
        product_days=_SAROS_239_ANOMALISTIC,
        notes="239 anomalistic months (Earth-Moon distance / "
              "perigee phase repeats — preserves apparent lunar "
              "diameter and tidal-bulge amplitude).",
        source_key="meeus_1991",
    ),
    SarosCommensurability(
        name="242_draconitic_months",
        integer_count=242,
        unit_period_days=LUNA_DRACONITIC_MONTH_DAYS,
        product_days=_SAROS_242_DRACONITIC,
        notes="242 draconitic months (Sun-at-node geometry repeats — "
              "necessary for an eclipse to occur).",
        source_key="meeus_1991",
    ),
    SarosCommensurability(
        name="19_eclipse_years",
        integer_count=19,
        unit_period_days=ECLIPSE_YEAR_DAYS,
        product_days=_SAROS_19_ECLIPSE_YEAR,
        notes="19 eclipse years (consistency check — eclipses "
              "drift through the calendar at the eclipse-year cadence).",
        source_key="meeus_1991",
        precision_flag=PRECISION_MEDIUM,
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "allens_astrophysical_quantities": (
        "Cox A. N. (ed., 2000). Allen's Astrophysical Quantities, "
        "4th ed. Springer. Canonical lunar months (sidereal, "
        "synodic, anomalistic, draconitic) at high precision."
    ),
    "jpl_de441": (
        "Park R. S. et al. (2021). The JPL Planetary and Lunar "
        "Ephemerides DE440 and DE441. Astron. J. 161, 105. "
        "DOI: 10.3847/1538-3881/abd414. Lunar orbital elements + "
        "secular eccentricity / inclination evolution."
    ),
    "williams_2014": (
        "Williams J. G. & Boggs D. H. (2014). Lunar Laser Ranging "
        "libration analysis. JGR Planets 119, 1546-1578. "
        "DOI: 10.1002/2013JE004489. The 7.9-arcsec forced libration "
        "amplitude + C/MR² = 0.3932 ± 0.0002 normalised moment of "
        "inertia. THE most precise libration measurement in the "
        "Solar System."
    ),
    "murray_dermott_1999": (
        "Murray C. D. & Dermott S. F. (1999). Solar System "
        "Dynamics. Cambridge University Press. Standard reference "
        "for lunar apsidal + nodal precession rates."
    ),
    "cassini_1693": (
        "Cassini G. D. (1693). Three laws of lunar rotation, "
        "stated in his treatise on the Moon's libration. The "
        "first identification of synchronous rotation + the "
        "spin/node-precession lock that defines Cassini state 2. "
        "(Modern formal restatement: Colombo 1966; Peale 1969.)"
    ),
    "meeus_1991": (
        "Meeus J. (1991). Astronomical Algorithms. Willmann-Bell. "
        "Saros cycle integer commensurability + 18.0-year eclipse-"
        "recurrence derivation."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "LUNA_SEMI_MAJOR_AXIS_KM",
    "LUNA_ECCENTRICITY",
    "LUNA_INCLINATION_TO_ECLIPTIC_DEG",
    "LUNA_OBLIQUITY_TO_ORBIT_DEG",
    "LUNA_SIDEREAL_MONTH_DAYS",
    "LUNA_SYNODIC_MONTH_DAYS",
    "LUNA_ANOMALISTIC_MONTH_DAYS",
    "LUNA_DRACONITIC_MONTH_DAYS",
    "LUNA_TROPICAL_MONTH_DAYS",
    "ECLIPSE_YEAR_DAYS",
    "LUNA_FORCED_LIBRATION_LONGITUDE_ARCSEC",
    "LUNA_NORMALISED_MOI_C_OVER_MR2",
    "LUNA_APSIDAL_PRECESSION_YEARS",
    "LUNA_NODAL_PRECESSION_YEARS",
    "LUNA_DYNAMICAL_MODES",
    "SAROS_COMMENSURABILITY",
    "SOURCES",
    "DynamicalMode",
    "SarosCommensurability",
]
