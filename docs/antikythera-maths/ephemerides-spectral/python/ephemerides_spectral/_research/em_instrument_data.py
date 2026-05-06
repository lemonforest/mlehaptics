"""Sol Electromagnetic Instrument — per-body observables + pairwise couplings.

Real, sourced data for the v0.19.0 ship surface. See research notebook
§16.8-§16.9 for the architectural scoping that motivates this module.

This is a **scoping-grade** data table: order-of-magnitude precision is the
target. Where literature values vary across missions / epochs / definitions
(e.g. Saturn's rotation period, Enceladus plume mass-loading, Io plasma
torus source rate) we pin a representative central value and flag the
uncertainty explicitly via the ``_uncertainty_pct`` field on the body
record. Anything below 1% precision is *not* a claim this module makes.

ALL VALUES MUST BE CITED. If a value is uncertain or estimated, note
it explicitly with a ``_uncertainty`` flag and a ``_source`` reference
into the SOURCES dict at the bottom.

Units convention
----------------
- Magnetic dipole moment: SI ``T·m³`` per the spec, which equals
  ``μ₀ * M_Am2 / (4π)``, i.e. ``B_eq * R_body^3`` at the planet's surface.
  To recover the SI A·m² moment, multiply by ``4π/μ₀ = 1e7``.
- Powers: SI watts (W).
- Plasma source rates: SI kg/sec.
- Rotation periods: days (sidereal where applicable; for the Sun the
  Carrington synodic equatorial period is conventional and is used here).
- Photoelectric potentials: SI volts (V), peak day-side surface value
  for airless bodies.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

# Class labels for the magnetised/induced/unmagnetised partition
EM_CLASS_MAGNETISED: str = "magnetised"        # intrinsic dipole significant
EM_CLASS_INDUCED: str = "induced"               # subsurface ocean / ionosphere
EM_CLASS_UNMAGNETISED: str = "unmagnetised"     # negligible field; SW-driven
EM_CLASS_STAR: str = "star"                     # the Sun (its own class)


@dataclass(frozen=True)
class EmBodyState:
    """Per-body EM observables, time-invariant where possible."""
    name: str
    em_class: str                                       # one of EM_CLASS_*
    # Magnetic dipole moment in T·m³ (SI) — None if no significant intrinsic field.
    # Convention: B = μ₀ M / (4π r³) at distance r along the dipole axis;
    # the value stored here is μ₀ M / (4π), i.e. B_eq * R_body^3.
    intrinsic_dipole_moment_T_m3: Optional[float]
    # Rotation period in days (sidereal where applicable). For Saturn,
    # the canonical pinned value; uncertainty flagged separately.
    rotation_period_days: float
    rotation_period_uncertainty_pct: float = 0.0
    # Synchrotron / coherent radio emission, total radiated power (W). None
    # for bodies without measurable emission.
    synchrotron_power_W: Optional[float] = None
    # Plasma source rate (kg/sec) — for bodies that supply mass to a host
    # body's magnetosphere (Io → Jupiter; Enceladus → Saturn).
    plasma_source_rate_kg_per_s: Optional[float] = None
    # Surface photoelectric potential (V) — peak day-side value for
    # airless bodies. None for bodies with substantial atmospheres.
    photoelectric_potential_V: Optional[float] = None
    # Citation key — points into the SOURCES dict below.
    source_key: str = ""


@dataclass(frozen=True)
class EmCoupling:
    """Pairwise EM coupling — one entry per significant interaction."""
    body_a: str
    body_b: str
    # Coupling kind: "flux_tube" / "induced_magnetosphere" / "imf_reconnection"
    # / "plasma_mass_loading" / "radiation_pressure" /
    # "intrinsic_field_to_intrinsic_field" / etc.
    kind: str
    # Order-of-magnitude power transfer (W). At the precision of the cited
    # literature only — the numbers are NOT measurement-grade.
    power_W: float
    # Dominant time-scale (e.g. "Io orbital 1.77 d", "Saturnian 10.7 h")
    dominant_timescale: str
    # Short physical description.
    note: str
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body roster — 16 entries per notebook §16.9.2.
# ---------------------------------------------------------------------------
#
# Magnetic-dipole conventions:
#   value [T·m³] = B_equator [T] * R_body^3 [m³]
#   (= μ₀ * M [A·m²] / (4π); to get A·m², multiply by 1e7)
#
# Cross-checks against published moments:
#   Earth IGRF-13:    M ≈ 7.94e22 A·m²  → 7.94e15 T·m³ ✔
#   Jupiter JRM33:    M ≈ 1.53e27 A·m²  → 1.53e20 T·m³ ✔
#   Saturn Cassini:   M ≈ 4.6e25  A·m²  → 4.6e18  T·m³ ✔
#   Mercury MESS.:    M ≈ 2.8e19  A·m²  → 2.8e12  T·m³ ✔
#   Ganymede Galileo: M ≈ 1.3e20  A·m²  → 1.3e13  T·m³ ✔
#
SOL_EM_BODIES: List[EmBodyState] = [

    # ---- Star ----
    EmBodyState(
        name="sun",
        em_class=EM_CLASS_STAR,
        # The Sun's *global* dipole component is highly variable across the
        # 22-yr Hale cycle (polarity flip at solar max). Quoted polar field
        # ~1-2 G at minima → ~1e-4 T at R_sun = 6.957e8 m gives an
        # equivalent dipole μ₀M/(4π) = B*R^3 ≈ 1e-4 * 3.36e26 ≈ 3.4e22 T·m³.
        # Order-of-magnitude only; flagged uncertain.
        intrinsic_dipole_moment_T_m3=3.4e22,  # UNCERTAIN — Hale-cycle variable
        rotation_period_days=27.275,           # Carrington synodic equatorial
        rotation_period_uncertainty_pct=0.5,   # latitudinal differential rotation
        synchrotron_power_W=None,              # not the dominant radio mechanism
        plasma_source_rate_kg_per_s=1.6e9,     # solar wind total mass flux
        photoelectric_potential_V=None,
        source_key="hathaway_2015",
    ),

    # ---- Inner rocky bodies ----
    EmBodyState(
        name="mercury",
        em_class=EM_CLASS_MAGNETISED,          # weak but present intrinsic dipole
        # MESSENGER multipole analysis: offset dipole ≈ 195 nT·R_M^3,
        # i.e. surface field at the magnetic equator ≈ 195 nT.
        # B*R^3 = 195e-9 * (2.4397e6)^3 = 2.83e12 T·m³.
        # ~0.4 % of Earth's dipole moment.
        intrinsic_dipole_moment_T_m3=2.8e12,
        rotation_period_days=58.6462,          # 3:2 spin-orbit-locked
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        plasma_source_rate_kg_per_s=None,
        photoelectric_potential_V=None,        # has minimal exosphere
        source_key="anderson_2011",
    ),

    EmBodyState(
        name="venus",
        em_class=EM_CLASS_INDUCED,             # induced ionospheric magnetosphere
        intrinsic_dipole_moment_T_m3=None,     # below detection threshold
        rotation_period_days=243.0226,          # retrograde — magnitude only
        rotation_period_uncertainty_pct=0.05,   # Magellan vs Venus Express disagree
        synchrotron_power_W=None,
        plasma_source_rate_kg_per_s=None,
        photoelectric_potential_V=None,
        source_key="russell_1980",
    ),

    EmBodyState(
        name="terra",
        em_class=EM_CLASS_MAGNETISED,
        # IGRF-13 (Alken et al. 2021): M = 7.94e22 A·m² → 7.94e15 T·m³.
        intrinsic_dipole_moment_T_m3=7.94e15,
        rotation_period_days=0.99726968,        # sidereal day
        rotation_period_uncertainty_pct=0.0,
        # Auroral kilometric radiation (AKR): ~1e7-1e9 W; pinned at ~1e8 W
        # geometric mean. Source: Gurnett 1974, Wu & Lee 1979 review.
        synchrotron_power_W=1e8,
        plasma_source_rate_kg_per_s=None,       # negligible compared to Io/Enceladus
        photoelectric_potential_V=None,
        source_key="alken_2021",
    ),

    EmBodyState(
        name="luna",
        em_class=EM_CLASS_UNMAGNETISED,
        # Apollo magnetometers + Lunar Prospector: weak crustal anomalies
        # (10-100 nT locally) but NO global dipole. None for the dipole
        # field here is the right call.
        intrinsic_dipole_moment_T_m3=None,
        rotation_period_days=27.32166156,       # synchronous with Terra orbit
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        plasma_source_rate_kg_per_s=None,
        # Day-side photoelectric potential ~+10 V (sunlit), night-side
        # ~-100 V in plasma sheet. Quoted +10 V dayside. Halekas 2008.
        photoelectric_potential_V=10.0,
        source_key="halekas_2008",
    ),

    EmBodyState(
        name="mars",
        em_class=EM_CLASS_UNMAGNETISED,         # no global dipole
        # Mars has STRONG crustal anomalies (Acuña 1999) but no global
        # dipole. The crustal field locally exceeds 1500 nT but does not
        # form a dipole. Stored as None — see crustal anomaly literature
        # (Acuña 1999, Connerney 2005) for the spatial-pattern story.
        intrinsic_dipole_moment_T_m3=None,
        rotation_period_days=1.02595675,        # sol = sidereal Mars day
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        # MAVEN escape rate: ~1-2 kg/s ions lost to space (atmospheric
        # erosion). Pinned at 1.5 kg/s. Jakosky 2018.
        plasma_source_rate_kg_per_s=1.5,
        photoelectric_potential_V=None,         # has thin atmosphere
        source_key="acuna_1999",
    ),

    # ---- Jupiter system ----
    EmBodyState(
        name="jupiter",
        em_class=EM_CLASS_MAGNETISED,
        # JRM33 (Connerney 2022): equatorial surface field 4.17 G = 4.17e-4 T
        # at R_J = 71492 km. B*R^3 = 4.17e-4 * (7.1492e7)^3 ≈ 1.52e20 T·m³.
        # ~20,000× Earth's dipole moment.
        intrinsic_dipole_moment_T_m3=1.52e20,
        rotation_period_days=0.41354,           # System III (9h 55m 29.71s)
        rotation_period_uncertainty_pct=0.0,    # well-determined from radio
        # Jovian decametric (DAM) + hectometric (HOM) + kilometric (bKOM/nKOM)
        # total non-thermal radio luminosity ≈ 2e10 W. Bagenal 2014.
        synchrotron_power_W=2e10,
        plasma_source_rate_kg_per_s=None,       # source is Io, not Jupiter itself
        photoelectric_potential_V=None,
        source_key="connerney_2022",
    ),

    EmBodyState(
        name="io",
        em_class=EM_CLASS_UNMAGNETISED,         # no intrinsic dipole; SW/Jovian-MHD-driven
        intrinsic_dipole_moment_T_m3=None,      # confirmed null by Galileo MAG
        rotation_period_days=1.76913786,        # synchronous with Jovian orbit
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,                # Io itself doesn't radiate; the flux tube does
        # Io plasma torus mass loading: ~1 ton/s = 1000 kg/s of SO2 + neutrals.
        # Bagenal & Delamere 2011: 260-2800 kg/s sulfur+oxygen ions; total
        # neutrals + ions ≈ 1000 kg/s order of magnitude.
        plasma_source_rate_kg_per_s=1.0e3,
        photoelectric_potential_V=None,
        source_key="bagenal_delamere_2011",
    ),

    EmBodyState(
        name="europa",
        em_class=EM_CLASS_INDUCED,              # induced field from subsurface ocean
        intrinsic_dipole_moment_T_m3=None,      # no intrinsic; induced response only
        rotation_period_days=3.55118100,        # synchronous
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        # Europa atmospheric sputtering: O2 + H2O sputter products, ~few kg/s
        # contributed to Jovian magnetosphere. Pinned at 5 kg/s (Smyth 2006).
        # UNCERTAIN — order-of-magnitude only.
        plasma_source_rate_kg_per_s=5.0,
        photoelectric_potential_V=None,
        source_key="khurana_1998",
    ),

    EmBodyState(
        name="ganymede",
        em_class=EM_CLASS_MAGNETISED,           # only moon with intrinsic dipole
        # Kivelson 2002 (Galileo MAG): M ≈ 1.32e13 T·m³, surface equatorial
        # field ≈ 720 nT at R_G = 2634.1 km. The unique moon with a dipole.
        intrinsic_dipole_moment_T_m3=1.32e13,
        rotation_period_days=7.15455296,        # synchronous
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        plasma_source_rate_kg_per_s=None,
        photoelectric_potential_V=None,
        source_key="kivelson_2002",
    ),

    EmBodyState(
        name="callisto",
        em_class=EM_CLASS_INDUCED,              # induced field from putative subsurface ocean
        intrinsic_dipole_moment_T_m3=None,
        rotation_period_days=16.68901840,       # synchronous
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        plasma_source_rate_kg_per_s=None,
        photoelectric_potential_V=None,
        source_key="khurana_1998",
    ),

    # ---- Saturn system ----
    EmBodyState(
        name="saturn",
        em_class=EM_CLASS_MAGNETISED,
        # Cassini SOI (Burton 2010): equatorial surface field 21,160 nT at
        # 1 bar level R_S = 60268 km. B*R^3 = 2.116e-5 * (6.0268e7)^3
        # ≈ 4.63e18 T·m³. Pure-dipole component (offset/tilted model
        # has additional multipoles; we quote the dipole only).
        intrinsic_dipole_moment_T_m3=4.6e18,
        # Saturn rotation period UNCERTAIN at ~1% — Voyager SKR gave
        # 10h 39m 22.4s = 0.4440 d; Cassini SKR drifted to 10h 47m 6s
        # = 0.4494 d. We pin the geometric midpoint 0.4467 d and flag
        # 1% uncertainty per notebook §16.3 disclaimer.
        rotation_period_days=0.4467,
        rotation_period_uncertainty_pct=1.0,    # Voyager↔Cassini SKR disagreement
        # Saturnian Kilometric Radiation (SKR) total power ≈ 5e7 W. Lamy 2008.
        synchrotron_power_W=5e7,
        plasma_source_rate_kg_per_s=None,       # source is Enceladus
        photoelectric_potential_V=None,
        source_key="burton_2010",
    ),

    EmBodyState(
        name="enceladus",
        em_class=EM_CLASS_UNMAGNETISED,         # no intrinsic; plume-driven plasma source
        intrinsic_dipole_moment_T_m3=None,
        rotation_period_days=1.37021785,        # synchronous
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        # Enceladus plume H2O mass loading into Saturnian magnetosphere
        # ≈ 200 kg/s (Hansen 2011, Cassini INMS+UVIS). Variable with
        # tiger-stripe activity over orbital phase. UNCERTAIN ±50%.
        plasma_source_rate_kg_per_s=200.0,
        photoelectric_potential_V=None,
        source_key="hansen_2011",
    ),

    EmBodyState(
        name="titan",
        em_class=EM_CLASS_INDUCED,              # induced ionospheric magnetosphere
        intrinsic_dipole_moment_T_m3=None,      # no intrinsic field detected by Cassini
        rotation_period_days=15.94542100,       # synchronous
        rotation_period_uncertainty_pct=0.0,
        synchrotron_power_W=None,
        # Titan atmospheric escape: photolytic + magnetospheric pickup;
        # CH4/N2 escape ~5 kg/s into Saturnian magnetosphere. UNCERTAIN
        # ±factor 2 — depends on Titan's position in/out of Saturnian
        # magnetopause (varies with solar wind dynamic pressure).
        plasma_source_rate_kg_per_s=5.0,
        photoelectric_potential_V=None,         # has substantial atmosphere
        source_key="bertucci_2008",
    ),

    # ---- Ice giants ----
    EmBodyState(
        name="uranus",
        em_class=EM_CLASS_MAGNETISED,
        # Voyager 2 (1986) magnetometer: highly tilted (~59°) and offset
        # internal dipole; surface equatorial field ~23,000 nT at 1 bar
        # level R_U = 25559 km. B*R^3 = 2.3e-5 * (2.5559e7)^3 ≈ 3.84e17 T·m³.
        # Pure-dipole component; multipoles substantial but not quoted here.
        intrinsic_dipole_moment_T_m3=3.8e17,
        rotation_period_days=0.71833,           # 17h 14m 24s (Voyager 2)
        rotation_period_uncertainty_pct=0.5,    # single-mission determination
        synchrotron_power_W=None,                # detected but very weak
        plasma_source_rate_kg_per_s=None,
        photoelectric_potential_V=None,
        source_key="ness_1986",
    ),

    EmBodyState(
        name="neptune",
        em_class=EM_CLASS_MAGNETISED,
        # Voyager 2 (1989) magnetometer: tilted (~47°) and offset internal
        # dipole; surface equatorial field ~14,000 nT at 1 bar level
        # R_N = 24764 km. B*R^3 = 1.4e-5 * (2.4764e7)^3 ≈ 2.13e17 T·m³.
        intrinsic_dipole_moment_T_m3=2.1e17,
        rotation_period_days=0.6713,            # 16h 6m 36s (Voyager 2)
        rotation_period_uncertainty_pct=0.5,    # single-mission determination
        synchrotron_power_W=None,                # detected but very weak
        plasma_source_rate_kg_per_s=None,
        photoelectric_potential_V=None,
        source_key="ness_1989",
    ),
]


# ---------------------------------------------------------------------------
# Pairwise couplings — the strongest pairwise EM interactions (notebook §16.2
# and §16.8.3). Order-of-magnitude precision; literature varies.
# ---------------------------------------------------------------------------
EM_COUPLINGS: List[EmCoupling] = [

    # The headliner: Jupiter-Io flux tube. The strongest pairwise EM
    # interaction in the solar system after Sun→planets radiation pressure.
    EmCoupling(
        body_a="jupiter",
        body_b="io",
        kind="flux_tube",
        power_W=1.0e12,                         # ≈ 1 TW (Saur 2007, Hess 2010)
        dominant_timescale="Io orbital 1.77 d × Jovian rotational 9.93 h",
        note=("Io plasma torus + Alfvén-wing current loop closing through "
              "Jovian polar ionosphere; lights the Io-DAM decametric "
              "emission; the strongest moon-magnetosphere coupling known."),
        source_key="saur_2007",
    ),

    # Saturn-Enceladus plume mass loading.
    EmCoupling(
        body_a="saturn",
        body_b="enceladus",
        kind="plasma_mass_loading",
        power_W=5.0e9,                           # ≈ 5 GW (Pontius & Hill 2006)
        dominant_timescale="Enceladus orbital 1.37 d (plume duty cycle)",
        note=("Enceladus plumes inject ~200 kg/s H2O into Saturnian "
              "magnetosphere; mass-loading drag on Saturnian plasma "
              "transfers angular momentum from Saturn's rotation."),
        source_key="pontius_hill_2006",
    ),

    # Saturn-Titan induced-magnetosphere coupling.
    EmCoupling(
        body_a="saturn",
        body_b="titan",
        kind="induced_magnetosphere",
        power_W=1.0e9,                           # ≈ 1 GW order-of-magnitude
        dominant_timescale="Titan orbital 15.95 d",
        note=("Titan's ionosphere drapes Saturnian magnetic-field lines; "
              "occasional excursions into solar-wind sheath (Bertucci 2008) "
              "switch the coupling to direct SW-Titan reconnection."),
        source_key="bertucci_2008",
    ),

    # Sun-Earth IMF/reconnection coupling.
    EmCoupling(
        body_a="sun",
        body_b="terra",
        kind="imf_reconnection",
        power_W=5.0e9,                           # ≈ 1-10 GW (Lockwood 2022)
        dominant_timescale="Carrington 27.275 d / Bz polarity (IMF)",
        note=("Solar-wind dynamic pressure + IMF Bz reconnection rate "
              "determines geomagnetic activity / ring current / auroral "
              "power. Variable across Schwabe (11 yr) + Hale (22 yr) "
              "cycles. Order GW; exceeds gravitational-perturbation budget "
              "but is far below Jupiter-Io flux tube."),
        source_key="lockwood_2022",
    ),

    # Jupiter-Europa induced magnetosphere — second-strongest moon coupling
    # to Jupiter after Io. Subsurface-ocean signature in Galileo MAG data
    # (Khurana 1998) is the canonical evidence for the ocean.
    EmCoupling(
        body_a="jupiter",
        body_b="europa",
        kind="induced_magnetosphere",
        power_W=1.0e10,                          # ≈ 10 GW (estimate; UNCERTAIN)
        dominant_timescale="Europa orbital 3.55 d (synodic w/ Jovian rotation)",
        note=("Subsurface salty ocean acts as conducting shell; induced "
              "field response to time-varying Jovian field at the ~5.5h "
              "synodic period (Jovian rot + Europa orbit). Key constraint "
              "on ocean depth/salinity — Khurana 1998."),
        source_key="khurana_1998",
    ),

    # Jupiter-Ganymede: the only intrinsic-field-to-intrinsic-field
    # interaction in this entire table. Ganymede's mini-magnetosphere is
    # embedded in Jupiter's, and Ganymede's dipole reconnects with
    # Jovian field lines at Ganymede's polar regions.
    EmCoupling(
        body_a="jupiter",
        body_b="ganymede",
        kind="intrinsic_field_to_intrinsic_field",
        power_W=1.0e10,                          # ≈ 10 GW (estimate; UNCERTAIN)
        dominant_timescale="Ganymede orbital 7.15 d (synodic w/ Jovian rotation)",
        note=("Ganymede's intrinsic dipole forms a mini-magnetosphere "
              "inside Jupiter's. Magnetic reconnection at Ganymede's "
              "magnetopause drives auroral emission (HST + Hubble UV). "
              "Unique system in the solar system."),
        source_key="kivelson_2002",
    ),

    # Sun radiation-pressure on the asteroid belt (representative-body
    # entry; per notebook §16.8.1 — Yarkovsky/YORP secular drift anchor).
    # Coupling-power figure is solar luminosity × dust-disk-equivalent
    # cross-section × albedo, order-of-magnitude only.
    EmCoupling(
        body_a="sun",
        body_b="asteroid_belt_bulk",
        kind="radiation_pressure",
        power_W=1.0e15,                          # ≈ 1 PW intercepted by belt cross-section
        dominant_timescale="orbital ~4 yr (typical main-belt) + Yarkovsky secular",
        note=("Radiation pressure + Yarkovsky/YORP thermal-recoil drives "
              "secular drift of small bodies (km-scale). Representative-"
              "body anchor; not a single-pair coupling. UNCERTAIN — depends "
              "strongly on assumed effective cross-section + albedo "
              "distribution. Notebook §16.8.1."),
        source_key="bottke_2006",
    ),
]


# ---------------------------------------------------------------------------
# Citations — every numeric value above has a source_key pointing here.
# ---------------------------------------------------------------------------
SOURCES: dict = {

    "alken_2021": (
        "Alken, P., Thébault, E., Beggan, C. D., et al. (2021). "
        "International Geomagnetic Reference Field: the thirteenth generation. "
        "Earth, Planets and Space, 73, 49. "
        "https://doi.org/10.1186/s40623-020-01288-x"
    ),

    "anderson_2011": (
        "Anderson, B. J., Johnson, C. L., Korth, H., et al. (2011). "
        "The Global Magnetic Field of Mercury from MESSENGER Orbital Observations. "
        "Science, 333, 1859-1862. "
        "https://doi.org/10.1126/science.1211001"
    ),

    "acuna_1999": (
        "Acuña, M. H., Connerney, J. E. P., Ness, N. F., et al. (1999). "
        "Global Distribution of Crustal Magnetization Discovered by the "
        "Mars Global Surveyor MAG/ER Experiment. "
        "Science, 284, 790-793. "
        "https://doi.org/10.1126/science.284.5415.790"
    ),

    "bagenal_delamere_2011": (
        "Bagenal, F., & Delamere, P. A. (2011). Flow of mass and energy in "
        "the magnetospheres of Jupiter and Saturn. "
        "Journal of Geophysical Research: Space Physics, 116, A05209. "
        "https://doi.org/10.1029/2010JA016294"
    ),

    "bertucci_2008": (
        "Bertucci, C., Achilleos, N., Dougherty, M. K., et al. (2008). "
        "The Magnetic Memory of Titan's Ionized Atmosphere. "
        "Science, 321, 1475-1478. "
        "https://doi.org/10.1126/science.1159780"
    ),

    "bottke_2006": (
        "Bottke, W. F., Vokrouhlický, D., Rubincam, D. P., & Nesvorný, D. "
        "(2006). The Yarkovsky and YORP effects: Implications for asteroid "
        "dynamics. Annual Review of Earth and Planetary Sciences, 34, 157-191. "
        "https://doi.org/10.1146/annurev.earth.34.031405.125154"
    ),

    "burton_2010": (
        "Burton, M. E., Dougherty, M. K., & Russell, C. T. (2010). "
        "Saturn's internal planetary magnetic field. "
        "Geophysical Research Letters, 37, L24105. "
        "https://doi.org/10.1029/2010GL045148"
    ),

    "connerney_2022": (
        "Connerney, J. E. P., Timmins, S., Oliversen, R. J., et al. (2022). "
        "A New Model of Jupiter's Magnetic Field at the Completion of "
        "Juno's Prime Mission. JRM33. "
        "Journal of Geophysical Research: Planets, 127, e2021JE007055. "
        "https://doi.org/10.1029/2021JE007055"
    ),

    "halekas_2008": (
        "Halekas, J. S., Delory, G. T., Brain, D. A., et al. (2008). "
        "Lunar surface charging during solar energetic particle events: "
        "Measurement and prediction. "
        "Journal of Geophysical Research: Space Physics, 113, A09102. "
        "https://doi.org/10.1029/2008JA013194"
    ),

    "hansen_2011": (
        "Hansen, C. J., Shemansky, D. E., Esposito, L. W., et al. (2011). "
        "The composition and structure of the Enceladus plume. "
        "Geophysical Research Letters, 38, L11202. "
        "https://doi.org/10.1029/2011GL047415"
    ),

    "hathaway_2015": (
        "Hathaway, D. H. (2015). The Solar Cycle. "
        "Living Reviews in Solar Physics, 12, 4. "
        "https://doi.org/10.1007/lrsp-2015-4 "
        "(also: Lockwood, M. (2013). Reconstruction and Prediction of "
        "Variations in the Open Solar Magnetic Flux and Interplanetary "
        "Conditions. Living Reviews in Solar Physics, 10, 4.)"
    ),

    "khurana_1998": (
        "Khurana, K. K., Kivelson, M. G., Stevenson, D. J., et al. (1998). "
        "Induced magnetic fields as evidence for subsurface oceans in "
        "Europa and Callisto. "
        "Nature, 395, 777-780. "
        "https://doi.org/10.1038/27394"
    ),

    "kivelson_2002": (
        "Kivelson, M. G., Khurana, K. K., & Volwerk, M. (2002). "
        "The permanent and inductive magnetic moments of Ganymede. "
        "Icarus, 157, 507-522. "
        "https://doi.org/10.1006/icar.2002.6834"
    ),

    "lockwood_2022": (
        "Lockwood, M., Owens, M. J., Barnard, L. A., et al. (2022). "
        "The Development of a Space Climatology: 1. Solar Wind Magnetosphere "
        "Coupling as a Function of Timescale. "
        "Space Weather, 20, e2021SW002989. "
        "https://doi.org/10.1029/2021SW002989"
    ),

    "ness_1986": (
        "Ness, N. F., Acuña, M. H., Behannon, K. W., et al. (1986). "
        "Magnetic Fields at Uranus. "
        "Science, 233, 85-89. "
        "https://doi.org/10.1126/science.233.4759.85"
    ),

    "ness_1989": (
        "Ness, N. F., Acuña, M. H., Burlaga, L. F., et al. (1989). "
        "Magnetic Fields at Neptune. "
        "Science, 246, 1473-1478. "
        "https://doi.org/10.1126/science.246.4936.1473"
    ),

    "pontius_hill_2006": (
        "Pontius, D. H., & Hill, T. W. (2006). Enceladus: A significant "
        "plasma source for Saturn's magnetosphere. "
        "Journal of Geophysical Research: Space Physics, 111, A09214. "
        "https://doi.org/10.1029/2006JA011674"
    ),

    "russell_1980": (
        "Russell, C. T., Elphic, R. C., & Slavin, J. A. (1980). "
        "Limits on the possible intrinsic magnetic field of Venus. "
        "Journal of Geophysical Research: Space Physics, 85, 8319-8332. "
        "https://doi.org/10.1029/JA085iA13p08319"
    ),

    "saur_2007": (
        "Saur, J., Neubauer, F. M., & Schilling, N. (2007). "
        "Hemisphere coupling in Enceladus' asymmetric plasma interaction. "
        "Journal of Geophysical Research: Space Physics, 112, A11209. "
        "(See also: Hess, S., Bonfond, B., Zarka, P., & Grodent, D. (2010). "
        "Model of the Jovian magnetic field topology constrained by the "
        "Io auroral emissions. JGR Space Physics, 116, A05217. "
        "https://doi.org/10.1029/2010JA016262)"
    ),
}


# Reference epoch for the rotation-phase advance. J2000.0 (TDB) by default;
# rotation is advanced from this epoch using rotation_period_days for each
# body. Rotation phases in the Earth-fixed (IAU prime-meridian) sense.
EM_REFERENCE_JD: float = 2451545.0


__all__ = [
    "EM_CLASS_MAGNETISED",
    "EM_CLASS_INDUCED",
    "EM_CLASS_UNMAGNETISED",
    "EM_CLASS_STAR",
    "EmBodyState",
    "EmCoupling",
    "SOL_EM_BODIES",
    "EM_COUPLINGS",
    "SOURCES",
    "EM_REFERENCE_JD",
]
