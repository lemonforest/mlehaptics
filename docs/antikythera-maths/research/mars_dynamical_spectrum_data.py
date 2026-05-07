"""Sol Mars Dynamical Spectrum — per-body action-angle decomposition
data for the v0.24.2 ship.

Real, sourced data for the **third per-body dynamical-spectrum
surface** in the v0.24.x sequence. Mars is the **contrast case** to
v0.24.0 Mercury (stable simple system) and v0.24.1 Luna (clean tidal
lock): the canonical **chaotic dynamics** case in the Solar System.

Why Mars matters for the dynamical-spectrum methodology
-------------------------------------------------------
Where Mercury and Luna admit clean spectral fingerprints — Mercury's
3:2 lock + Le Verrier/Einstein closure, Luna's 1:1 lock + Saros
commensurability — Mars exhibits **secular chaos**: long-term (Myr-Gyr)
wandering of orbital + spin parameters driven by **secular-resonance
overlap**.

The KAM theorem says small enough perturbations preserve quasi-periodic
torus structure in phase space; large enough perturbations destroy it.
Mars sits *near* the boundary. Its obliquity has wandered over a wide
range across Gyr-scale time (Laskar 1989 / Laskar et al. 2004
showed extended obliquity excursions are statistically expected;
Laskar 2008 showed ~1% chance Mercury's eccentricity destabilises
within 5 Gyr — driven by the same secular-chaos mechanism). The
*spectrum itself* — the way Mars's secular angle frequencies overlap
with the rest of the Solar System's secular spectrum — is what drives
the chaos.

This is the **action-angle ↔ KAM-theory connection** in its most
directly observable form, and it's why Mars is the right contrast
case for v0.24.x.

Action-angle framing
--------------------
Mars's dynamical state has the standard layout:

* Angle variables (live on tori):
  - Orbital mean motion (period 686.971 d sidereal)
  - Spin frequency (period 1.025957 d — sol)
  - Apsidal precession (perihelion advance via secular interaction
    with Jupiter + Saturn — fundamental frequency g₄)
  - Nodal precession (regression of orbital ascending node — s₄)
  - Spin-axis precession (~171 kyr period — Ward 1973;
    Touma & Wisdom 1993)
* Action variables (live on real intervals):
  - Eccentricity 0.0934 (varies 0.005-0.119 across secular cycle)
  - Inclination to ecliptic 1.85° (varies 0°-8°)
  - Obliquity ~25.19° present-day; varies ~0°-60° on Gyr timescales
    via secular chaos
  - Normalised moment of inertia C/MR² ≈ 0.3645 (Konopliv 2016 +
    Le Maistre 2023 InSight refinement)

The headline cross-channel observation
--------------------------------------
The **Laskar secular-resonance overlap signature** — the cross-
channel observation specific to Mars — is the proximity of Mars's
spin-axis precession frequency to several secular orbital
frequencies (s₃, s₄, s₅) of the inner Solar System. When the
spin-precession frequency *crosses* one of these secular orbital
frequencies, the obliquity undergoes large excursions; the crossing
itself is what makes Mars's obliquity chaotic on Gyr timescales.

Specifically:
  - Mars spin-axis precession rate: ~7.6 arcsec/yr (Ward 1973)
  - Inner-system secular frequency s₃ (Earth-related): ~−18 arcsec/yr
  - Inner-system secular frequency s₄ (Mars-related): ~−18 arcsec/yr

These near-coincidences of frequency drive secular-resonance
overlap. The catalog ships these frequencies + the chaos-driving
near-resonance pairs.

**Not a re-derivation.** Values are from the published Laskar
secular-integration papers + InSight RISE measurement (Le Maistre
2023) + Konopliv 2016 ephemeris fits.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Mars physical / orbital reference constants (J2000) ------------
# JPL DE441 + NASA Planetary Fact Sheet.
MARS_SEMI_MAJOR_AXIS_AU: float = 1.52371034
MARS_ECCENTRICITY: float = 0.09339410
MARS_INCLINATION_TO_ECLIPTIC_DEG: float = 1.84969142
MARS_ORBITAL_PERIOD_DAYS: float = 686.97096
MARS_SIDEREAL_DAY_HOURS: float = 24.6229                # Sol = 24:39:35
MARS_SIDEREAL_DAY_DAYS: float = MARS_SIDEREAL_DAY_HOURS / 24.0
MARS_OBLIQUITY_DEG: float = 25.19                        # Present-day epoch

# ---- Le Maistre 2023 InSight RISE measurement -----------------------
# Le Maistre S. et al. (2023). Spin state and deep interior structure
# of Mars from InSight radio tracking. Nature 619, 733-737.
MARS_NORMALISED_MOI_C_OVER_MR2: float = 0.3645          # ± 0.0005

# ---- Spin-axis precession (Ward 1973; Touma-Wisdom 1993) ------------
# Period ~171,000 years; rate ~7.58 arcsec/yr (mean).
MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS: float = 171000.0
MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR: float = 7.58

# ---- Laskar obliquity-chaos bounds (Laskar et al. 2004) -------------
# Probable historical excursion range over Gyr timescales.
MARS_OBLIQUITY_LASKAR_MIN_DEG: float = 0.0
MARS_OBLIQUITY_LASKAR_MAX_DEG: float = 60.0
MARS_OBLIQUITY_MEAN_GYR_DEG: float = 37.62               # Laskar 2004 mean


# ---------------------------------------------------------------------------
# Action-angle mode catalog
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DynamicalMode:
    """One frequency mode in Mars's dynamical state.

    Mirrors the v0.24.0 / v0.24.1 catalog structure.
    """
    name: str
    frequency_per_century: float    # cycles/century (or rad/century)
    period_days: float              # 0 if mode is action-class (no period)
    amplitude_value: float
    amplitude_units: str
    angle_or_action: str            # "angle" or "action"
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


_DAYS_PER_CENTURY: float = 36525.0
_PI: float = 3.141592653589793


MARS_DYNAMICAL_MODES: List[DynamicalMode] = [

    # ---- Orbital mean motion ---------------------------------------
    DynamicalMode(
        name="orbital_mean_motion",
        frequency_per_century=_DAYS_PER_CENTURY / MARS_ORBITAL_PERIOD_DAYS,
        period_days=MARS_ORBITAL_PERIOD_DAYS,
        amplitude_value=2 * _PI,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Sidereal orbital phase. ~53 orbits per century. The "
              "fastest mode in Mars's dynamical state.",
        source_key="jpl_de441",
    ),

    # ---- Spin frequency --------------------------------------------
    DynamicalMode(
        name="spin_frequency",
        frequency_per_century=_DAYS_PER_CENTURY / MARS_SIDEREAL_DAY_DAYS,
        period_days=MARS_SIDEREAL_DAY_DAYS,
        amplitude_value=2 * _PI,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Sidereal rotation. The 'sol' (Mars day) is the "
              "synodic-rotation-relative-to-Sun period (24h 39m "
              "35.244s). NOT in spin-orbit resonance with orbit "
              "(unlike Mercury / Luna / Galileans).",
        source_key="le_maistre_2023",
    ),

    # ---- Spin-axis precession (~171 kyr; Ward 1973) ----------------
    DynamicalMode(
        name="spin_axis_precession",
        frequency_per_century=100.0 / (MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS / 1000.0),
        period_days=MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS * 365.25,
        amplitude_value=MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR,
        amplitude_units="arcsec/yr",
        angle_or_action="angle",
        notes="Spin-axis precession (~171 kyr). The mode whose "
              "frequency CROSSES the secular orbital frequencies "
              "s₃ + s₄ + s₅ of the inner Solar System -- the secular "
              "resonance overlap that drives Mars obliquity chaos "
              "(Laskar 1993; Touma-Wisdom 1993). The KAM-theory "
              "small-denominator failure mode in observable form.",
        source_key="ward_1973",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- Apsidal precession (perihelion advance, fundamental g₄) --
    DynamicalMode(
        name="apsidal_precession_g4",
        frequency_per_century=100.0 / 71600.0,    # 71.6 kyr period
        period_days=71600.0 * 365.25,
        amplitude_value=17.92,                     # arcsec/yr (Laskar)
        amplitude_units="arcsec/yr",
        angle_or_action="angle",
        notes="Mars secular fundamental g₄ — apsidal (perihelion) "
              "precession. Driven primarily by Jupiter + Saturn "
              "perturbations. Period ~71 kyr; rate ~17.92 arcsec/yr "
              "(Laskar secular ephemeris).",
        source_key="laskar_2004",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- Nodal precession (s₄ secular fundamental) ----------------
    DynamicalMode(
        name="nodal_precession_s4",
        frequency_per_century=-100.0 / 70000.0,   # ~70 kyr retrograde
        period_days=70000.0 * 365.25,
        amplitude_value=-17.74,                    # arcsec/yr retrograde
        amplitude_units="arcsec/yr",
        angle_or_action="angle",
        notes="Mars secular fundamental s₄ — nodal regression. "
              "Driven primarily by Jupiter + Saturn secular "
              "interaction. The s₃-s₄ resonance is one of the chaos-"
              "driving near-resonances in the inner Solar System.",
        source_key="laskar_2004",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- Eccentricity (action) -------------------------------------
    DynamicalMode(
        name="eccentricity",
        frequency_per_century=0.0,
        period_days=0.0,
        amplitude_value=MARS_ECCENTRICITY,
        amplitude_units="dimensionless",
        angle_or_action="action",
        notes="Present-day eccentricity 0.0934. Varies 0.005-0.119 "
              "across the secular eccentricity cycle (~95 kyr) — "
              "Milankovitch-style oscillation contributing to "
              "long-term Martian climate variation. Cross-references "
              "the Mars climate-orbit coupling literature.",
        source_key="jpl_de441",
    ),

    # ---- Inclination (action) -------------------------------------
    DynamicalMode(
        name="inclination_to_ecliptic",
        frequency_per_century=0.0,
        period_days=0.0,
        amplitude_value=MARS_INCLINATION_TO_ECLIPTIC_DEG,
        amplitude_units="deg",
        angle_or_action="action",
        notes="Present-day inclination 1.85°. Varies 0°-8° on Myr "
              "timescales (Laskar 2004 secular evolution).",
        source_key="jpl_de441",
    ),

    # ---- Obliquity (action; chaotic on Gyr timescales) -------------
    DynamicalMode(
        name="obliquity",
        frequency_per_century=0.0,
        period_days=0.0,
        amplitude_value=MARS_OBLIQUITY_DEG,
        amplitude_units="deg",
        angle_or_action="action",
        notes="THE HEADLINE: present-day obliquity 25.19°, but the "
              "Gyr-scale historical excursion range is ~0°-60°  "
              "(Laskar et al. 2004) with mean ~37.6°. Mars's "
              "obliquity is CHAOTIC -- secular-resonance overlap "
              "between spin-axis precession and the inner-Solar-"
              "System fundamental frequencies s₃, s₄, s₅ drives the "
              "wandering. Without Earth's stabilising Moon, Mars "
              "didn't escape its chaotic-obliquity zone. THE direct "
              "observable signature of KAM-theory small-denominator "
              "failure in our solar system.",
        source_key="laskar_2004",
        precision_flag=PRECISION_MEDIUM,
    ),
]


# ---------------------------------------------------------------------------
# Secular-resonance overlap catalog (the chaos driver)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SecularResonance:
    """One near-resonance in Mars's secular dynamics.

    The overlap of Mars spin-axis precession with the inner-Solar-
    System secular orbital frequencies is what drives Mars obliquity
    chaos. Each entry pairs Mars spin-precession with one secular
    fundamental + records the frequency proximity.
    """
    mars_mode: str           # "spin_axis_precession" or other
    secular_partner: str     # "s3" / "s4" / "s5" / "g4-g3" / etc.
    partner_description: str
    proximity_arcsec_per_year: float  # |freq_mars - freq_partner|
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# Inner-Solar-System secular fundamental frequencies (Laskar 1990 /
# 2004; arcsec/yr, retrograde sign for s_i):
_FREQ_S3_ARCSEC_YR: float = -18.86      # Earth-related secular
_FREQ_S4_ARCSEC_YR: float = -17.74      # Mars-related secular
_FREQ_S5_ARCSEC_YR: float = 0.00         # Jupiter (~0 for invariant plane)
_FREQ_G4_ARCSEC_YR: float = 17.92        # Mars apsidal


MARS_SECULAR_RESONANCES: List[SecularResonance] = [

    SecularResonance(
        mars_mode="spin_axis_precession",
        secular_partner="s3",
        partner_description="Earth-related secular orbital fundamental "
                            "(s₃ ≈ -18.86 arcsec/yr)",
        proximity_arcsec_per_year=abs(
            MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR
            - abs(_FREQ_S3_ARCSEC_YR)
        ),
        notes="The s₃ resonance crossing -- Mars spin-axis precession "
              "(~7.58 arcsec/yr forward) approaches the magnitude of "
              "Earth's secular orbital frequency s₃. The overlap "
              "drives Mars obliquity excursions to large values. "
              "Without the Moon stabilising Earth's obliquity, Earth "
              "would be subject to similar chaos.",
        source_key="laskar_1993",
        precision_flag=PRECISION_MEDIUM,
    ),

    SecularResonance(
        mars_mode="spin_axis_precession",
        secular_partner="s4",
        partner_description="Mars-related secular orbital fundamental "
                            "(s₄ ≈ -17.74 arcsec/yr)",
        proximity_arcsec_per_year=abs(
            MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR
            - abs(_FREQ_S4_ARCSEC_YR)
        ),
        notes="The s₄ resonance crossing -- frequency proximity drives "
              "obliquity-eccentricity coupling on long timescales.",
        source_key="laskar_1993",
        precision_flag=PRECISION_MEDIUM,
    ),

    SecularResonance(
        mars_mode="apsidal_precession_g4",
        secular_partner="g3-s3",
        partner_description="Earth secular eccentricity-precession "
                            "combination",
        proximity_arcsec_per_year=2.5,    # Approximate from Laskar 2008
        notes="The Mars-Earth secular combination contributing to the "
              "near-resonance overlap producing Mercury eccentricity "
              "instability (~1% chance of destabilisation in 5 Gyr; "
              "Laskar 2008/2009).",
        source_key="laskar_2008",
        precision_flag=PRECISION_LOW,
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "jpl_de441": (
        "Park R. S. et al. (2021). The JPL Planetary and Lunar "
        "Ephemerides DE440 and DE441. Astron. J. 161, 105. "
        "DOI: 10.3847/1538-3881/abd414. Mars orbital elements at "
        "high precision."
    ),
    "le_maistre_2023": (
        "Le Maistre S. et al. (2023). Spin state and deep interior "
        "structure of Mars from InSight radio tracking. Nature 619, "
        "733-737. DOI: 10.1038/s41586-023-06150-0. C/MR² = 0.3645 ± "
        "0.0005 + Mars rotation period refinement from InSight RISE."
    ),
    "ward_1973": (
        "Ward W. R. (1973). Large-scale variations in the obliquity "
        "of Mars. Science 181, 260-262. DOI: 10.1126/science.181.4096.260. "
        "First identification of Mars spin-axis precession + "
        "obliquity-secular-resonance coupling."
    ),
    "laskar_1993": (
        "Laskar J. & Robutel P. (1993). The chaotic obliquity of "
        "the planets. Nature 361, 608-612. DOI: 10.1038/361608a0. "
        "Established Mars obliquity chaos via secular-resonance "
        "overlap with s₃/s₄ inner-Solar-System fundamentals."
    ),
    "laskar_2004": (
        "Laskar J., Correia A. C. M., Gastineau M., Joutel F., "
        "Levrard B., Robutel P. (2004). Long term evolution and "
        "chaotic diffusion of the insolation quantities of Mars. "
        "Icarus 170, 343-364. DOI: 10.1016/j.icarus.2004.04.005. "
        "The definitive ~0°-60° obliquity-excursion range + Gyr-"
        "scale chaotic-diffusion analysis."
    ),
    "laskar_2008": (
        "Laskar J. & Gastineau M. (2008). Existence of collisional "
        "trajectories of Mercury, Mars and Venus with the Earth. "
        "Nature 459, 817-819. DOI: 10.1038/nature08096. "
        "Inner-Solar-System secular-chaos quantification — ~1% "
        "chance Mercury orbit destabilises within 5 Gyr."
    ),
    "touma_wisdom_1993": (
        "Touma J. & Wisdom J. (1993). The chaotic obliquity of "
        "Mars. Science 259, 1294-1297. "
        "DOI: 10.1126/science.259.5099.1294. Independent "
        "confirmation of Laskar 1993 chaos finding via direct "
        "numerical integration."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MARS_SEMI_MAJOR_AXIS_AU",
    "MARS_ECCENTRICITY",
    "MARS_INCLINATION_TO_ECLIPTIC_DEG",
    "MARS_ORBITAL_PERIOD_DAYS",
    "MARS_SIDEREAL_DAY_HOURS",
    "MARS_SIDEREAL_DAY_DAYS",
    "MARS_OBLIQUITY_DEG",
    "MARS_NORMALISED_MOI_C_OVER_MR2",
    "MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS",
    "MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR",
    "MARS_OBLIQUITY_LASKAR_MIN_DEG",
    "MARS_OBLIQUITY_LASKAR_MAX_DEG",
    "MARS_OBLIQUITY_MEAN_GYR_DEG",
    "MARS_DYNAMICAL_MODES",
    "MARS_SECULAR_RESONANCES",
    "SOURCES",
    "DynamicalMode",
    "SecularResonance",
]
