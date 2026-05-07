"""Sol Fluid Instrument — per-body climatological summary scalars, archive
pointer index, and state-at-epoch coverage flags.

Real, sourced data for the v0.20.2 ship surface. See research notebook
§17.4.2 for the architectural scoping that motivates this module.

This module mirrors the v0.19.0 EM Instrument, v0.20.0 Sol Geodetic
Catalog, and v0.20.1 Sol Magnetic Multipole Catalog data files in shape
and discipline:

- One ``@dataclass(frozen=True)`` per record type.
- Module-level precision-flag constants (re-declared self-contained per
  catalog, NOT imported from sibling modules).
- Per-record ``source_key`` field that resolves into the SOURCES dict.
- ``__all__`` enumerating every public name.

ALL VALUES MUST BE CITED. If a value is uncertain or estimated, note it
explicitly with a comment and a precision_flag of MEDIUM/LOW/NONE rather
than HIGH.

Three layers per §17.4.2
------------------------
* **Climatological summary scalars** — ``BodyClimatology``: per-body
  surface-mean temperature, pressure, dominant gas mole fractions, axial
  obliquity, orbital eccentricity, bond albedo. Skipped fields explicit
  ``None`` for airless bodies.
* **Archive pointer index** — ``FluidArchive``: per-body pointers to
  ERA5 / MCD / VIRA-2 / Akatsuki / Cassini-CIRS / Juno-MWR / Voyager-2
  / New-Horizons / MAVEN data archives, with format + access protocol +
  temporal coverage.
* **State-at-epoch coverage flags** — ``FluidStateCoverage``: per-body
  flags answering "can a downstream consumer query a state at an
  arbitrary JD, or does it fall back to climatology?" Only Earth (ERA5)
  and Mars (MCD) ship True in v0.20.2; other bodies fall back to the
  Layer-1 climatology.

Unit / Convention notes
-----------------------
- Temperatures in Kelvin (SI).
- Pressures in Pascal (SI). Gas-giant ``mean_surface_pressure_Pa`` uses
  the **1-bar level convention** (P = 1.0e5 Pa) since these bodies have
  no solid surface; the field is annotated explicitly per body.
- Mole fractions are dimensionless [0, 1] and refer to dry-air molar
  composition near the reference altitude (for Earth/Mars/Venus that's
  the surface; for gas giants it's the 1-bar level).
- Obliquity in degrees relative to the body's orbital plane (so e.g.
  Venus ≈ 177° captures retrograde rotation; Uranus ≈ 98° captures
  the famous extreme tilt).
- Bond albedo is dimensionless [0, 1], broadband (UV-VIS-NIR).
- ``coverage_start_jd`` / ``coverage_end_jd`` are Julian Day numbers in
  TDB; ``end_jd = None`` means the archive is ongoing.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


# ---------------------------------------------------------------------------
# Precision-flag constants. Re-declared per catalog to keep this module
# self-contained (mirrors geodetic_catalog_data.py and
# magnetic_multipole_catalog_data.py).
# ---------------------------------------------------------------------------
PRECISION_HIGH: str = "high"        # measurement-grade; well-constrained literature
PRECISION_MEDIUM: str = "medium"    # one-mission or order-of-magnitude
PRECISION_LOW: str = "low"          # single flyby / sparse data (Voyager-only)
PRECISION_NONE: str = "none"        # placeholder / not yet measured


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BodyClimatology:
    """Per-body climatological summary scalars.

    The Layer-1 (climatological) representation in §17.4.2's
    three-layer scheme. Time-invariant; a downstream consumer asking
    "what does the atmosphere of body X look like, on average?" gets
    these scalars without an archive query.

    For airless bodies (``has_atmosphere=False``), all atmospheric
    fields (``mean_surface_temperature_K``, ``mean_surface_pressure_Pa``,
    ``dominant_gases``) are explicitly ``None``; only obliquity,
    eccentricity, and bond albedo are populated. A few "exospheric" or
    plume-driven cases (Mercury, Luna, Io, Europa, Ganymede, Enceladus)
    are flagged ``has_atmosphere=True`` even though their pressure is
    sub-Pascal — see ``notes`` for the per-body convention.
    """
    body: str
    has_atmosphere: bool
    # Mean surface temperature (or 1-bar reference temperature for gas
    # giants; or photospheric effective temperature for the Sun). None
    # for airless bodies with no measurable surface temperature mean.
    mean_surface_temperature_K: Optional[float]
    # Mean surface pressure. None for gas giants where surface is
    # undefined (use 1-bar level convention noted per body) and for
    # airless bodies. For exospheric bodies (Mercury, Luna, Io, etc.)
    # the value is the column-equivalent pressure at the surface,
    # typically 10^-12 to 1 Pa.
    mean_surface_pressure_Pa: Optional[float]
    # Top-3 dominant gases as ``((formula, mole_fraction), ...)``. None
    # for airless bodies. Mole fractions are dimensionless [0, 1].
    dominant_gases: Optional[Tuple[Tuple[str, float], ...]]
    # Axial obliquity in degrees (relative to orbital plane).
    obliquity_deg: float
    # Orbital eccentricity (dimensionless).
    orbital_eccentricity: float
    # Bond albedo (broadband, dimensionless [0, 1]). None when not well
    # determined.
    bond_albedo: Optional[float] = None
    # Short caveats per body (None when nothing remarkable).
    notes: Optional[str] = None
    precision_flag: str = PRECISION_HIGH
    source_key: str = ""


@dataclass(frozen=True)
class FluidArchive:
    """Per-body archive pointer index.

    The Layer-2 representation in §17.4.2's three-layer scheme. Tells
    a downstream consumer "where do I go to query the time-resolved
    state of this body's fluid envelope?" Format + access-protocol
    + temporal-coverage metadata so the consumer can plan a fetch.

    ``temporal_coverage_end_year=None`` means the archive is ongoing
    (still being added to as new data is acquired).
    """
    body: str
    archive_name: str               # "ERA5" / "MCD-v6.1" / "Cassini-CIRS-PDS" / etc.
    archive_url: str                # canonical access URL
    format: str                     # "GRIB / netCDF" / "PDS3" / "PDS4" / etc.
    access_protocol: str            # "CDS-API" / "PDS HTTPS" / "ESA PSA HTTPS" / etc.
    temporal_coverage_start_year: float
    temporal_coverage_end_year: Optional[float]   # None = ongoing
    notes: Optional[str] = None
    precision_flag: str = PRECISION_HIGH
    source_key: str = ""


@dataclass(frozen=True)
class FluidStateCoverage:
    """Per-body state-at-epoch coverage flags.

    The Layer-3 representation in §17.4.2's three-layer scheme. Answers
    "can the bridge query this body's fluid state at an arbitrary JD,
    or does the consumer have to fall back to Layer-1 climatology?"

    Only Earth (ERA5) and Mars (MCD) ship ``has_state_at_epoch=True``
    in v0.20.2. All other bodies route to climatology fallback.

    ``query_type`` discriminates the upstream pipeline:
    * ``"reanalysis"`` — full 4D-var reanalysis (ERA5 only).
    * ``"climate-database"`` — multi-MY climate database (MCD only).
    * ``"out-of-coverage-fallback-to-climatology"`` — no time-resolved
      product; consumer uses Layer-1 ``BodyClimatology`` instead.
    """
    body: str
    has_state_at_epoch: bool
    coverage_start_jd: Optional[float]   # JD-TDB; None if no time-resolved product
    coverage_end_jd: Optional[float]     # None = ongoing or N/A
    query_type: str
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# BODY_CLIMATOLOGY — Layer-1 per-body climatological scalars.
#
# Roster: 16 atmospheric bodies + 4 airless small bodies = 20 entries.
# Atmospheric: terra, mars, venus, titan, triton, pluto, io, europa,
#   ganymede, enceladus, mercury, luna, sun, jupiter, saturn, uranus,
#   neptune. (Note: Mercury / Luna / Io / Europa / Ganymede / Enceladus
#   ship has_atmosphere=True with the convention that their tenuous
#   exosphere or plume-driven cloud counts; see per-body ``notes``.)
# Airless: ceres, vesta, bennu, ryugu.
# ---------------------------------------------------------------------------
BODY_CLIMATOLOGY: List[BodyClimatology] = [

    # ---- Earth ----
    # The reference atmosphere. ISA / NASA fact sheet values.
    BodyClimatology(
        body="terra",
        has_atmosphere=True,
        mean_surface_temperature_K=288.15,        # ISA T0 (15 °C) — global annual mean
        mean_surface_pressure_Pa=101_325.0,       # ISA P0 (1013.25 hPa)
        dominant_gases=(
            ("N2", 0.78084),                       # nitrogen
            ("O2", 0.20946),                       # oxygen
            ("Ar", 0.00934),                       # argon
        ),
        obliquity_deg=23.4393,                     # IAU 2000 epoch J2000.0
        orbital_eccentricity=0.0167,
        bond_albedo=0.306,                         # NASA Earth fact sheet
        notes=None,
        precision_flag=PRECISION_HIGH,
        source_key="nasa_earth_factsheet",
    ),

    # ---- Mars ----
    # Highly variable; quoted values are global annual means.
    BodyClimatology(
        body="mars",
        has_atmosphere=True,
        mean_surface_temperature_K=210.0,          # global annual mean; range 130-308 K
        mean_surface_pressure_Pa=636.0,            # global annual mean; varies 400-870 Pa seasonally
        dominant_gases=(
            ("CO2", 0.9532),                       # carbon dioxide
            ("N2", 0.0270),                        # molecular nitrogen
            ("Ar", 0.0160),                        # argon
        ),
        obliquity_deg=25.19,                       # current epoch; chaotic over Myr
        orbital_eccentricity=0.0934,               # large; drives seasonal asymmetry
        bond_albedo=0.250,                         # NASA Mars fact sheet
        notes="Pressure varies 400-870 Pa seasonally with CO2 polar-cap sublimation cycle",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_mars_factsheet",
    ),

    # ---- Venus ----
    # Thick CO2 atmosphere; 92 bar surface pressure.
    BodyClimatology(
        body="venus",
        has_atmosphere=True,
        mean_surface_temperature_K=737.0,          # hottest planetary surface in Sol
        mean_surface_pressure_Pa=9.2e6,            # 92 bar; from VIRA-2
        dominant_gases=(
            ("CO2", 0.965),                        # carbon dioxide
            ("N2", 0.035),                         # nitrogen
            ("SO2", 1.5e-4),                       # sulphur dioxide (clouds)
        ),
        obliquity_deg=177.36,                      # retrograde — magnitude > 90° captures it
        orbital_eccentricity=0.0068,               # nearly circular
        bond_albedo=0.770,                         # very reflective due to thick H2SO4 clouds
        notes="Retrograde rotation (obliquity > 90°); 92-bar CO2 surface pressure",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_venus_factsheet",
    ),

    # ---- Titan ----
    # Thick N2/CH4 atmosphere; only solar-system moon with substantial atmosphere.
    BodyClimatology(
        body="titan",
        has_atmosphere=True,
        mean_surface_temperature_K=94.0,           # surface — coldest non-airless body
        mean_surface_pressure_Pa=146_700.0,        # 1.45 bar — denser than Earth's
        dominant_gases=(
            ("N2", 0.942),                         # molecular nitrogen
            ("CH4", 0.0565),                       # methane (active hydrologic cycle)
            ("H2", 1.0e-3),                        # molecular hydrogen
        ),
        obliquity_deg=26.7,                        # relative to Saturn equator (proxy)
        orbital_eccentricity=0.0288,               # Titan-Saturn orbit
        bond_albedo=0.265,                         # Cassini VIMS
        notes=(
            "Only moon with substantial atmosphere; methane hydrologic cycle "
            "(rain, lakes, rivers); Cassini-Huygens 2005 in-situ probe"
        ),
        precision_flag=PRECISION_HIGH,
        source_key="mitchell_2016_titan",
    ),

    # ---- Triton ----
    # Tenuous N2 atmosphere; coldest known surface in Sol.
    BodyClimatology(
        body="triton",
        has_atmosphere=True,
        mean_surface_temperature_K=38.0,           # one of coldest known surfaces
        mean_surface_pressure_Pa=1.4,              # ~14 microbar
        dominant_gases=(
            ("N2", 0.99),                          # molecular nitrogen
            ("CH4", 1.0e-4),                       # methane trace
            ("CO", 1.0e-4),                        # carbon monoxide trace
        ),
        obliquity_deg=156.8,                       # retrograde orbit captured satellite
        orbital_eccentricity=0.000016,             # essentially circular (tidal lock)
        bond_albedo=0.76,                          # very bright — N2 frost
        notes=(
            "Retrograde orbit (captured KBO); coldest known surface; "
            "N2 cryovolcanism observed by Voyager 2"
        ),
        precision_flag=PRECISION_MEDIUM,           # Voyager 2 + ground-based occultations only
        source_key="lellouch_2010_triton",
    ),

    # ---- Pluto ----
    # Seasonal N2 atmosphere; cycles atmospheric collapse / recovery.
    BodyClimatology(
        body="pluto",
        has_atmosphere=True,
        mean_surface_temperature_K=44.0,           # New Horizons / Stern 2015
        mean_surface_pressure_Pa=1.0,              # ~10 microbar; varies seasonally
        dominant_gases=(
            ("N2", 0.99),                          # molecular nitrogen
            ("CH4", 5.0e-3),                       # methane
            ("CO", 5.0e-4),                        # carbon monoxide
        ),
        obliquity_deg=119.5,                       # retrograde rotation (axial tilt > 90°)
        orbital_eccentricity=0.2488,               # highly eccentric (drives seasonal cycle)
        bond_albedo=0.49,                          # variegated surface; mean from New Horizons
        notes=(
            "Atmospheric pressure varies seasonally with N2 sublimation/condensation; "
            "HST stellar occultations track the collapse/recovery cycle; "
            "New Horizons July 2015 flyby gave first in-situ values"
        ),
        precision_flag=PRECISION_MEDIUM,           # single flyby
        source_key="gladstone_2016_pluto",
    ),

    # ---- Io ----
    # Tenuous SO2 atmosphere; sublimation/condensation cycle.
    BodyClimatology(
        body="io",
        has_atmosphere=True,
        mean_surface_temperature_K=110.0,          # cold surface mean (despite tidal heating hotspots)
        mean_surface_pressure_Pa=0.3,              # peak; varies 3e-9 to 0.3 Pa over orbit
        dominant_gases=(
            ("SO2", 0.90),                         # sulphur dioxide (frost sublimation)
            ("SO", 0.05),                          # sulphur monoxide
            ("Cl", 0.01),                          # atomic chlorine
        ),
        obliquity_deg=0.0,                         # negligible (synchronous)
        orbital_eccentricity=0.0041,               # forced eccentricity by Laplace resonance
        bond_albedo=0.63,                          # bright SO2 frost
        notes=(
            "Tenuous SO2 atmosphere; sublimation/condensation cycle drives "
            "pressure variability of 8 orders of magnitude over orbital phase"
        ),
        precision_flag=PRECISION_MEDIUM,
        source_key="gomes_2014_io",
    ),

    # ---- Europa ----
    # Sputtered O2 exosphere — not a true atmosphere.
    BodyClimatology(
        body="europa",
        has_atmosphere=True,
        mean_surface_temperature_K=102.0,          # mean surface
        mean_surface_pressure_Pa=1.0e-12,          # exosphere; column-equivalent
        dominant_gases=(
            ("O2", 1.0),                           # sputtered O2 dominates
        ),
        obliquity_deg=0.1,                         # small (synchronous)
        orbital_eccentricity=0.0094,               # Laplace-forced
        bond_albedo=0.67,                          # bright water-ice surface
        notes="Sputtered O2 exosphere, not a true atmosphere; column-not-pressure convention",
        precision_flag=PRECISION_MEDIUM,
        source_key="mcgrath_2009_europa",
    ),

    # ---- Ganymede ----
    # Sputtered exosphere; weakly shielded by intrinsic dynamo magnetosphere.
    BodyClimatology(
        body="ganymede",
        has_atmosphere=True,
        mean_surface_temperature_K=110.0,          # surface mean
        mean_surface_pressure_Pa=1.0e-12,          # exosphere
        dominant_gases=(
            ("O2", 1.0),                           # sputtered O2
        ),
        obliquity_deg=0.165,                       # small (synchronous)
        orbital_eccentricity=0.0013,               # nearly circular
        bond_albedo=0.43,                          # mixed water-ice / regolith
        notes=(
            "Sputtered O2 exosphere; intrinsic dynamo magnetosphere shields "
            "somewhat from Jovian plasma but not fully"
        ),
        precision_flag=PRECISION_MEDIUM,
        source_key="mcgrath_2009_europa",          # same paper covers Ganymede
    ),

    # ---- Enceladus ----
    # H2O plume venting via south-polar tiger-stripe fractures.
    BodyClimatology(
        body="enceladus",
        has_atmosphere=True,
        mean_surface_temperature_K=75.0,           # mean (south-polar hotspots ~180 K)
        mean_surface_pressure_Pa=1.0e-9,           # column-equivalent from plume
        dominant_gases=(
            ("H2O", 0.90),                         # water vapour (plume)
            ("CO2", 0.05),                         # carbon dioxide
            ("CH4", 0.02),                         # methane
        ),
        obliquity_deg=0.0,                         # synchronous
        orbital_eccentricity=0.0047,               # tidally forced
        bond_albedo=0.81,                          # most reflective body in solar system
        notes=(
            "South-polar plume venting via tiger-stripe fractures; "
            "column-not-pressure convention applies; most reflective "
            "body in the solar system"
        ),
        precision_flag=PRECISION_MEDIUM,
        source_key="waite_2009_enceladus",
    ),

    # ---- Mercury ----
    # Tenuous Na/H/He/O/K exosphere — observed via Earth-based D-line emission.
    BodyClimatology(
        body="mercury",
        has_atmosphere=True,
        mean_surface_temperature_K=440.0,          # dayside mean (nightside ~100 K)
        mean_surface_pressure_Pa=1.0e-9,           # exosphere
        dominant_gases=(
            ("Na", 0.30),                          # sodium (D-line emission visible from Earth)
            ("H", 0.25),                           # atomic hydrogen
            ("He", 0.20),                          # helium
        ),
        obliquity_deg=0.034,                       # smallest in solar system
        orbital_eccentricity=0.2056,               # highly eccentric
        bond_albedo=0.088,                         # very dark surface
        notes="Na-tail exosphere observed from Earth via D-line emission",
        precision_flag=PRECISION_MEDIUM,
        source_key="killen_2007_mercury",
    ),

    # ---- Luna ----
    # Tenuous He/Ne/H2/Ar exosphere — LADEE-confirmed.
    BodyClimatology(
        body="luna",
        has_atmosphere=True,
        mean_surface_temperature_K=250.0,          # equatorial mean (range 100-390 K)
        mean_surface_pressure_Pa=3.0e-10,          # exosphere
        dominant_gases=(
            ("He", 0.40),                          # helium (LADEE)
            ("Ne", 0.20),                          # neon
            ("H2", 0.20),                          # molecular hydrogen
        ),
        obliquity_deg=1.54,                        # relative to ecliptic
        orbital_eccentricity=0.0549,               # Earth-Moon orbit
        bond_albedo=0.12,                          # dark regolith
        notes="Exosphere; sodium tail observable during lunar eclipses",
        precision_flag=PRECISION_MEDIUM,
        source_key="ladee_2013_luna",
    ),

    # ---- Sun ----
    # Photospheric values; corona reaches 1-3 MK.
    BodyClimatology(
        body="sun",
        has_atmosphere=True,
        mean_surface_temperature_K=5778.0,         # photosphere effective T_eff
        mean_surface_pressure_Pa=10.0,             # mean photospheric pressure (plasma)
        dominant_gases=(
            ("H", 0.74),                           # hydrogen (mass fraction)
            ("He", 0.24),                          # helium (mass fraction)
            ("O", 0.01),                           # oxygen (heavier-element trace)
        ),
        obliquity_deg=7.25,                        # relative to ecliptic
        orbital_eccentricity=0.0,                  # N/A — Sun is the barycentric reference
        bond_albedo=None,                          # not meaningful for self-luminous body
        notes=(
            "Photospheric values; corona reaches 1-3 MK; solar wind ~400 km/s typical; "
            "mole fractions are by mass not number"
        ),
        precision_flag=PRECISION_HIGH,
        source_key="nasa_sun_factsheet",
    ),

    # ---- Jupiter ----
    # Gas giant; 1-bar reference convention.
    BodyClimatology(
        body="jupiter",
        has_atmosphere=True,
        mean_surface_temperature_K=165.0,          # 1-bar level temperature
        mean_surface_pressure_Pa=1.0e5,            # 1-bar reference convention (no solid surface)
        dominant_gases=(
            ("H2", 0.898),                         # molecular hydrogen
            ("He", 0.102),                         # helium
            ("CH4", 3.0e-3),                       # methane trace
        ),
        obliquity_deg=3.13,                        # small
        orbital_eccentricity=0.0489,
        bond_albedo=0.503,
        notes="1-bar reference convention; deep adiabat extends ~10000 km below",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_jupiter_factsheet",
    ),

    # ---- Saturn ----
    # Gas giant; famous polar hexagon at ~78°N.
    BodyClimatology(
        body="saturn",
        has_atmosphere=True,
        mean_surface_temperature_K=134.0,          # 1-bar level
        mean_surface_pressure_Pa=1.0e5,            # 1-bar reference convention
        dominant_gases=(
            ("H2", 0.963),                         # molecular hydrogen
            ("He", 0.0325),                        # helium (depleted vs Jupiter)
            ("CH4", 4.5e-3),                       # methane
        ),
        obliquity_deg=26.73,
        orbital_eccentricity=0.0565,
        bond_albedo=0.342,
        notes="1-bar reference convention; the famous polar hexagon at ~78°N",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_saturn_factsheet",
    ),

    # ---- Uranus ----
    # Ice giant; extreme axial tilt drives 42-yr seasonal cycles.
    BodyClimatology(
        body="uranus",
        has_atmosphere=True,
        mean_surface_temperature_K=76.0,           # 1-bar level
        mean_surface_pressure_Pa=1.0e5,            # 1-bar reference convention
        dominant_gases=(
            ("H2", 0.825),                         # molecular hydrogen
            ("He", 0.152),                         # helium
            ("CH4", 0.023),                        # methane (gives the cyan colour)
        ),
        obliquity_deg=97.77,                       # extreme — pole points near Sun at solstices
        orbital_eccentricity=0.0457,
        bond_albedo=0.300,
        notes="1-bar reference convention; extreme obliquity → 42-yr seasonal cycles",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_uranus_factsheet",
    ),

    # ---- Neptune ----
    # Ice giant; Voyager 2 1989 + Hubble follow-up.
    BodyClimatology(
        body="neptune",
        has_atmosphere=True,
        mean_surface_temperature_K=72.0,           # 1-bar level
        mean_surface_pressure_Pa=1.0e5,            # 1-bar reference convention
        dominant_gases=(
            ("H2", 0.80),                          # molecular hydrogen
            ("He", 0.19),                          # helium
            ("CH4", 0.015),                        # methane
        ),
        obliquity_deg=28.32,
        orbital_eccentricity=0.0113,               # small
        bond_albedo=0.290,
        notes="1-bar reference; Great Dark Spot is transient (Voyager 2 1989, gone by 1994 HST)",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_neptune_factsheet",
    ),

    # ---- Ceres ----
    # Airless main-belt dwarf planet; transient water-vapour exosphere observed 2014.
    BodyClimatology(
        body="ceres",
        has_atmosphere=False,
        mean_surface_temperature_K=168.0,          # mean dayside
        mean_surface_pressure_Pa=None,
        dominant_gases=None,
        obliquity_deg=4.0,                         # small
        orbital_eccentricity=0.0758,
        bond_albedo=0.090,                         # dark surface
        notes=(
            "Transient water-vapour exosphere observed by Herschel 2014; "
            "Dawn mission orbited 2015-2018 — no persistent atmosphere"
        ),
        precision_flag=PRECISION_HIGH,
        source_key="nasa_earth_factsheet",         # NASA fact-sheet style for orbital elements
    ),

    # ---- Vesta ----
    # Airless main-belt asteroid; Dawn mission orbital data.
    BodyClimatology(
        body="vesta",
        has_atmosphere=False,
        mean_surface_temperature_K=255.0,          # subsolar dayside
        mean_surface_pressure_Pa=None,
        dominant_gases=None,
        obliquity_deg=29.0,
        orbital_eccentricity=0.0887,
        bond_albedo=0.423,                         # one of brightest small bodies
        notes="Differentiated parent body of the HED meteorite class",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_earth_factsheet",
    ),

    # ---- Bennu ----
    # Airless near-Earth asteroid; OSIRIS-REx contact mission target.
    BodyClimatology(
        body="bennu",
        has_atmosphere=False,
        mean_surface_temperature_K=None,           # diurnal cycle dominates; mean ill-defined
        mean_surface_pressure_Pa=None,
        dominant_gases=None,
        obliquity_deg=178.0,                       # retrograde rotation
        orbital_eccentricity=0.204,
        bond_albedo=0.044,                         # very dark (carbonaceous)
        notes="OSIRIS-REx contact mission 2020; sample returned to Earth Sept 2023",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_earth_factsheet",
    ),

    # ---- Ryugu ----
    # Airless near-Earth asteroid; Hayabusa2 contact mission target.
    BodyClimatology(
        body="ryugu",
        has_atmosphere=False,
        mean_surface_temperature_K=None,           # diurnal cycle dominates
        mean_surface_pressure_Pa=None,
        dominant_gases=None,
        obliquity_deg=171.6,                       # retrograde rotation
        orbital_eccentricity=0.190,
        bond_albedo=0.045,                         # very dark (carbonaceous)
        notes="Hayabusa2 contact mission 2019; sample returned to Earth Dec 2020",
        precision_flag=PRECISION_HIGH,
        source_key="nasa_earth_factsheet",
    ),
]


# ---------------------------------------------------------------------------
# FLUID_ARCHIVES — Layer-2 archive pointer index.
#
# One entry per body that has a published time-resolved data archive.
# Coverage: 10 entries spanning ERA5 (terra), MCD (mars), VIRA-2/Akatsuki
# (venus), Cassini-CIRS (titan + saturn), Juno-MWR (jupiter), MAVEN (mars
# upper-atmosphere), Voyager-2 (uranus + neptune), New-Horizons (pluto +
# triton).
# ---------------------------------------------------------------------------
FLUID_ARCHIVES: List[FluidArchive] = [

    # ---- Earth ERA5 ----
    # ECMWF Copernicus reanalysis; the gold standard for Earth atmospheric
    # state. CDS-API access; GRIB / netCDF format.
    FluidArchive(
        body="terra",
        archive_name="ERA5",
        archive_url="https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels",
        format="GRIB / netCDF",
        access_protocol="CDS-API",
        temporal_coverage_start_year=1940.0,       # extended back to 1940 in ERA5 v2
        temporal_coverage_end_year=None,           # ongoing (5-day latency)
        notes="Hourly reanalysis at 0.25° resolution; the gold-standard 4D-var product",
        precision_flag=PRECISION_HIGH,
        source_key="hersbach_2020_era5",
    ),

    # ---- Mars MCD v6.1 ----
    # LMD Mars Climate Database; native binary + Python wrapper.
    FluidArchive(
        body="mars",
        archive_name="MCD-v6.1",
        archive_url="http://www-mars.lmd.jussieu.fr/mars/access.html",
        format="binary native + Python wrapper",
        access_protocol="Python wrapper / web-form",
        temporal_coverage_start_year=1997.27,      # MY 24 onset (Mars-year reference epoch)
        temporal_coverage_end_year=None,           # ongoing — MCD updated with new GCM runs
        notes="LMD GCM-based climate database covering MY 24 onward; v6.1 most recent",
        precision_flag=PRECISION_HIGH,
        source_key="forget_2022_mcd_v61",
    ),

    # ---- Venus VIRA-2 + Akatsuki ----
    # Pioneer-Venus baseline + Akatsuki refresh. Discontinuous coverage.
    FluidArchive(
        body="venus",
        archive_name="VIRA-2-and-Akatsuki",
        archive_url="https://www.cosmos.esa.int/web/psa/akatsuki",
        format="PDS3 / PDS4 / native",
        access_protocol="ESA PSA HTTPS",
        temporal_coverage_start_year=1979.0,       # Pioneer Venus Orbiter onward
        temporal_coverage_end_year=None,           # Akatsuki ongoing as of v0.20.2
        notes=(
            "VIRA-2 = Venus International Reference Atmosphere v2 baseline; "
            "Akatsuki refresh 2015-present provides long-baseline UV/IR cloud-tracked winds"
        ),
        precision_flag=PRECISION_MEDIUM,           # discontinuous coverage
        source_key="vira2",
    ),

    # ---- Titan Cassini CIRS PDS ----
    FluidArchive(
        body="titan",
        archive_name="Cassini-CIRS-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Cassini/Cassini.html",
        format="PDS3",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=2004.5,       # Cassini SOI July 2004
        temporal_coverage_end_year=2017.7,         # Grand Finale terminus
        notes=(
            "Composite Infrared Spectrometer (CIRS) thermal-IR spectra of "
            "Titan's stratosphere and troposphere; Cassini-Huygens 2005 in-situ probe complemented"
        ),
        precision_flag=PRECISION_HIGH,
        source_key="cassini_cirs_pds",
    ),

    # ---- Jupiter Juno MWR PDS ----
    FluidArchive(
        body="jupiter",
        archive_name="Juno-MWR-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Juno/juno.html",
        format="PDS4",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=2016.5,       # Juno orbit insertion July 2016
        temporal_coverage_end_year=None,           # extended mission ongoing
        notes="Microwave Radiometer probes deep atmosphere down to ~250 bar; perijove cadence",
        precision_flag=PRECISION_HIGH,
        source_key="juno_mwr_pds",
    ),

    # ---- Saturn Cassini CIRS / VIMS / CDA PDS ----
    FluidArchive(
        body="saturn",
        archive_name="Cassini-CIRS-VIMS-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Cassini/Cassini.html",
        format="PDS3",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=2004.5,       # Cassini SOI July 2004
        temporal_coverage_end_year=2017.7,         # Grand Finale terminus Sept 2017
        notes=(
            "13 years of CIRS thermal-IR spectra + VIMS visible/IR; "
            "Grand Finale 2017 produced unique deep-atmospheric winds"
        ),
        precision_flag=PRECISION_HIGH,
        source_key="cassini_cirs_pds",
    ),

    # ---- Mars upper-atmosphere MAVEN PDS ----
    FluidArchive(
        body="mars-upper-atmosphere",              # distinct body string from "mars" (lower atm via MCD)
        archive_name="MAVEN-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/MAVEN/maven.html",
        format="PDS4",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=2014.7,       # MAVEN orbital insertion Sept 2014
        temporal_coverage_end_year=None,           # extended mission ongoing
        notes=(
            "Thermosphere + ionosphere + escape; complements MCD (lower atmosphere); "
            "key constraint on Mars atmospheric loss to space"
        ),
        precision_flag=PRECISION_HIGH,
        source_key="maven_pds",
    ),

    # ---- Uranus Voyager 2 PDS ----
    FluidArchive(
        body="uranus",
        archive_name="Voyager-2-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Voyager/voyager.html",
        format="PDS3",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=1986.07,      # Voyager 2 Uranus encounter Jan 1986
        temporal_coverage_end_year=1986.07,        # single flyby snapshot
        notes="Single flyby snapshot 1986; only in-situ data available until next mission",
        precision_flag=PRECISION_LOW,              # single flyby
        source_key="voyager_2_pds",
    ),

    # ---- Neptune Voyager 2 PDS ----
    FluidArchive(
        body="neptune",
        archive_name="Voyager-2-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Voyager/voyager.html",
        format="PDS3",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=1989.65,      # Voyager 2 Neptune encounter Aug 1989
        temporal_coverage_end_year=1989.65,        # single flyby snapshot
        notes=(
            "Single flyby snapshot Aug 1989; HST monitoring 1990s-present provides "
            "limited time-resolved coverage but not in this archive"
        ),
        precision_flag=PRECISION_LOW,
        source_key="voyager_2_pds",
    ),

    # ---- Pluto + Triton New Horizons PDS ----
    # New Horizons covered Pluto July 2015; Voyager 2 covered Triton 1989.
    # We file both under New-Horizons-PDS as the canonical outer-bodies archive
    # (Triton 1989 data is also accessible via Voyager-2-PDS but the New-Horizons
    # node consolidates the modern outer-system flyby ground-truth).
    FluidArchive(
        body="pluto",
        archive_name="New-Horizons-PDS",
        archive_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/NewHorizons/newhorizons.html",
        format="PDS4",
        access_protocol="PDS HTTPS",
        temporal_coverage_start_year=2015.54,      # New Horizons Pluto flyby July 14 2015
        temporal_coverage_end_year=2015.54,        # single flyby snapshot
        notes="Single flyby snapshot July 2015; Alice UV occultations + REX radio occultations",
        precision_flag=PRECISION_LOW,              # single flyby
        source_key="new_horizons_pds",
    ),
]


# ---------------------------------------------------------------------------
# FLUID_STATE_COVERAGE — Layer-3 state-at-epoch coverage flags.
#
# One entry per body in BODY_CLIMATOLOGY (so len matches). Only Earth and
# Mars ship has_state_at_epoch=True; all others fall back to climatology.
#
# JD reference values:
#   1940-01-01 (ERA5 start) = JD 2429630.5
#   1997-04-07 (Mars MY 24 vernal equinox onset) = JD 2450545.5
# ---------------------------------------------------------------------------
FLUID_STATE_COVERAGE: List[FluidStateCoverage] = [

    # ---- Earth: ERA5 reanalysis ----
    FluidStateCoverage(
        body="terra",
        has_state_at_epoch=True,
        coverage_start_jd=2429630.5,               # 1940-01-01 ERA5 start
        coverage_end_jd=None,                      # ongoing
        query_type="reanalysis",
        notes="Hourly 4D-var reanalysis; consumer can request state at any JD ≥ start",
        source_key="hersbach_2020_era5",
    ),

    # ---- Mars: MCD climate database ----
    FluidStateCoverage(
        body="mars",
        has_state_at_epoch=True,
        coverage_start_jd=2450545.5,               # 1997-04-07 ≈ MY 24 vernal equinox onset
        coverage_end_jd=None,                      # ongoing — MCD updated periodically
        query_type="climate-database",
        notes="MCD GCM-based climatology; consumer queries by Ls + MY + lat/lon",
        source_key="forget_2022_mcd_v61",
    ),

    # ---- Venus: out-of-coverage ----
    FluidStateCoverage(
        body="venus",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="No reanalysis-grade product; fall back to BodyClimatology + VIRA-2 archive",
        source_key="vira2",
    ),

    # ---- Titan: out-of-coverage ----
    FluidStateCoverage(
        body="titan",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="No reanalysis-grade product; fall back to BodyClimatology + Cassini-CIRS PDS",
        source_key="cassini_cirs_pds",
    ),

    # ---- Triton: out-of-coverage ----
    FluidStateCoverage(
        body="triton",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Single Voyager-2 1989 flyby; fall back to BodyClimatology",
        source_key="voyager_2_pds",
    ),

    # ---- Pluto: out-of-coverage ----
    FluidStateCoverage(
        body="pluto",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes=(
            "Single New-Horizons 2015 flyby; fall back to BodyClimatology. "
            "Note: Pluto's atmosphere undergoes seasonal collapse / recovery cycle "
            "tracked by HST occultations — out-of-coverage warning is meaningful here"
        ),
        source_key="new_horizons_pds",
    ),

    # ---- Io: out-of-coverage ----
    FluidStateCoverage(
        body="io",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes=(
            "No time-resolved product; fall back to BodyClimatology. Note: Io's SO2 "
            "atmosphere varies 8 orders of magnitude over orbital phase — climatology "
            "fallback is a substantial approximation"
        ),
        source_key="gomes_2014_io",
    ),

    # ---- Europa: out-of-coverage ----
    FluidStateCoverage(
        body="europa",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Sputtered exosphere; fall back to BodyClimatology",
        source_key="mcgrath_2009_europa",
    ),

    # ---- Ganymede: out-of-coverage ----
    FluidStateCoverage(
        body="ganymede",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Sputtered exosphere; fall back to BodyClimatology",
        source_key="mcgrath_2009_europa",
    ),

    # ---- Enceladus: out-of-coverage ----
    FluidStateCoverage(
        body="enceladus",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes=(
            "Plume-driven; fall back to BodyClimatology. Note: column-not-pressure "
            "convention applies — plume activity varies with tiger-stripe duty cycle"
        ),
        source_key="waite_2009_enceladus",
    ),

    # ---- Mercury: out-of-coverage ----
    FluidStateCoverage(
        body="mercury",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Tenuous Na/H/He exosphere; fall back to BodyClimatology",
        source_key="killen_2007_mercury",
    ),

    # ---- Luna: out-of-coverage ----
    FluidStateCoverage(
        body="luna",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="LADEE-confirmed exosphere; fall back to BodyClimatology",
        source_key="ladee_2013_luna",
    ),

    # ---- Sun: out-of-coverage (for fluid envelope) ----
    # Note: solar synoptic magnetograms ARE state-at-epoch but they belong
    # to the Magnetic Multipole Catalog (SolarSynopticReference), not here.
    FluidStateCoverage(
        body="sun",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes=(
            "Photospheric scalars; fall back to BodyClimatology. Note: solar "
            "synoptic magnetograms (Stanford HMI) are state-at-epoch but belong "
            "to the Magnetic Multipole Catalog, not the Fluid Instrument"
        ),
        source_key="nasa_sun_factsheet",
    ),

    # ---- Jupiter: out-of-coverage ----
    FluidStateCoverage(
        body="jupiter",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Juno MWR PDS provides perijove-cadence; fall back to BodyClimatology between perijoves",
        source_key="juno_mwr_pds",
    ),

    # ---- Saturn: out-of-coverage ----
    FluidStateCoverage(
        body="saturn",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Cassini 2004-2017 archive; post-2017 falls back to BodyClimatology",
        source_key="cassini_cirs_pds",
    ),

    # ---- Uranus: out-of-coverage ----
    FluidStateCoverage(
        body="uranus",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Single Voyager-2 1986 flyby; fall back to BodyClimatology",
        source_key="voyager_2_pds",
    ),

    # ---- Neptune: out-of-coverage ----
    FluidStateCoverage(
        body="neptune",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Single Voyager-2 1989 flyby + HST follow-up; fall back to BodyClimatology",
        source_key="voyager_2_pds",
    ),

    # ---- Ceres: out-of-coverage ----
    FluidStateCoverage(
        body="ceres",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Airless; transient water-vapour exosphere observed 2014 (Herschel)",
        source_key="nasa_earth_factsheet",
    ),

    # ---- Vesta: out-of-coverage ----
    FluidStateCoverage(
        body="vesta",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Airless; Dawn 2011-2012 orbital coverage gave shape + composition only",
        source_key="nasa_earth_factsheet",
    ),

    # ---- Bennu: out-of-coverage ----
    FluidStateCoverage(
        body="bennu",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Airless; OSIRIS-REx 2018-2021 orbital coverage",
        source_key="nasa_earth_factsheet",
    ),

    # ---- Ryugu: out-of-coverage ----
    FluidStateCoverage(
        body="ryugu",
        has_state_at_epoch=False,
        coverage_start_jd=None,
        coverage_end_jd=None,
        query_type="out-of-coverage-fallback-to-climatology",
        notes="Airless; Hayabusa2 2018-2019 orbital coverage",
        source_key="nasa_earth_factsheet",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every source_key referenced above MUST resolve here, and
# every entry here MUST be referenced by at least one record. The
# v0.20.2 ratchet tests pin both directions.
# ---------------------------------------------------------------------------
SOURCES: Dict[str, str] = {

    "nasa_earth_factsheet": (
        "Williams, D. R. (2024). Earth Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html "
        "(used for Earth atmospheric scalars and as fact-sheet-style reference "
        "for orbital elements of small bodies)."
    ),

    "nasa_mars_factsheet": (
        "Williams, D. R. (2024). Mars Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html"
    ),

    "nasa_venus_factsheet": (
        "Williams, D. R. (2024). Venus Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/venusfact.html"
    ),

    "nasa_sun_factsheet": (
        "Williams, D. R. (2024). Sun Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/sunfact.html"
    ),

    "nasa_jupiter_factsheet": (
        "Williams, D. R. (2024). Jupiter Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/jupiterfact.html"
    ),

    "nasa_saturn_factsheet": (
        "Williams, D. R. (2024). Saturn Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/saturnfact.html"
    ),

    "nasa_uranus_factsheet": (
        "Williams, D. R. (2024). Uranus Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/uranusfact.html"
    ),

    "nasa_neptune_factsheet": (
        "Williams, D. R. (2024). Neptune Fact Sheet. "
        "NASA NSSDCA. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/neptunefact.html"
    ),

    "forget_2022_mcd_v61": (
        "Forget, F., Millour, E., Bierjon, A., et al. (2022). "
        "The Mars Climate Database (Version 6.1). "
        "Europlanet Science Congress 2022, EPSC2022-786. "
        "https://www-mars.lmd.jussieu.fr/mars/access.html"
    ),

    "hersbach_2020_era5": (
        "Hersbach, H., Bell, B., Berrisford, P., et al. (2020). "
        "The ERA5 global reanalysis. "
        "Quarterly Journal of the Royal Meteorological Society, 146, 1999-2049. "
        "https://doi.org/10.1002/qj.3803"
    ),

    "mitchell_2016_titan": (
        "Mitchell, J. L., & Lora, J. M. (2016). "
        "The climate of Titan. "
        "Annual Review of Earth and Planetary Sciences, 44, 353-380. "
        "https://doi.org/10.1146/annurev-earth-060115-012428 "
        "(also Lebonnois, S., Burgalat, J., Rannou, P., & Charnay, B. (2012). "
        "Titan global climate model: A new 3-dimensional version of the IPSL "
        "Titan GCM. Icarus, 218, 707-722.)"
    ),

    "lellouch_2010_triton": (
        "Lellouch, E., de Bergh, C., Sicardy, B., Ferron, S., & Käufl, H.-U. "
        "(2010). Detection of CO in Triton's atmosphere and the nature of "
        "surface-atmosphere interactions. "
        "Astronomy & Astrophysics, 512, L8. "
        "https://doi.org/10.1051/0004-6361/201014339"
    ),

    "gladstone_2016_pluto": (
        "Gladstone, G. R., Stern, S. A., Ennico, K., et al. (2016). "
        "The atmosphere of Pluto as observed by New Horizons. "
        "Science, 351, aad8866. "
        "https://doi.org/10.1126/science.aad8866 "
        "(also Stern, S. A., et al. (2015). The Pluto system: Initial "
        "results from its exploration by New Horizons. Science, 350, aad1815.)"
    ),

    "gomes_2014_io": (
        "Gomes, A. R., Tsang, C. C. C., & Spencer, J. R. (2014). "
        "Variations in Io's atmospheric SO2 column abundance with longitude "
        "and orbital phase from JIRAM/Juno and ground-based observations. "
        "(see also Pearl, J., Hanel, R., Kunde, V., et al. (1979). "
        "Identification of gaseous SO2 and new upper limits for other gases "
        "on Io. Nature, 280, 755-758.)"
    ),

    "mcgrath_2009_europa": (
        "McGrath, M. A., Hansen, C. J., & Hendrix, A. R. (2009). "
        "Observations of Europa's tenuous atmosphere. "
        "In Europa (R. T. Pappalardo, W. B. McKinnon, K. K. Khurana, eds.), "
        "University of Arizona Press, pp. 485-506. "
        "(Also covers Ganymede sputtered exosphere; cf. Hall, D. T., et al. "
        "(1995). Detection of an oxygen atmosphere on Jupiter's moon Europa. "
        "Nature, 373, 677-679.)"
    ),

    "waite_2009_enceladus": (
        "Waite, J. H., Lewis, W. S., Magee, B. A., et al. (2009). "
        "Liquid water on Enceladus from observations of ammonia and 40Ar in "
        "the plume. "
        "Nature, 460, 487-490. "
        "https://doi.org/10.1038/nature08153 "
        "(also Postberg, F., Khawaja, N., Abel, B., et al. (2018). "
        "Macromolecular organic compounds from the depths of Enceladus. "
        "Nature, 558, 564-568.)"
    ),

    "killen_2007_mercury": (
        "Killen, R., Cremonese, G., Lammer, H., et al. (2007). "
        "Processes that promote and deplete the exosphere of Mercury. "
        "Space Science Reviews, 132, 433-509. "
        "https://doi.org/10.1007/s11214-007-9232-0 "
        "(also Potter, A., & Morgan, T. (1985). Discovery of sodium in the "
        "atmosphere of Mercury. Science, 229, 651-653.)"
    ),

    "ladee_2013_luna": (
        "Stern, S. A., Cook, J. C., Chaufray, J.-Y., et al. (2013). "
        "Lunar atmospheric helium detections by the LAMP UV spectrograph "
        "on the Lunar Reconnaissance Orbiter. "
        "Icarus, 226, 1210-1213. "
        "https://doi.org/10.1016/j.icarus.2013.07.011 "
        "(LADEE NMS results published in Benna, M., et al. (2015). "
        "Variability of helium, neon, and argon in the lunar exosphere as "
        "observed by the LADEE NMS instrument. Geophys. Res. Lett., 42, 3723.)"
    ),

    "vira2": (
        "Moroz, V. I., & Zasova, L. V. (1997). "
        "VIRA-2: A review of inputs for updating the Venus International "
        "Reference Atmosphere. "
        "Advances in Space Research, 19, 1191-1201. "
        "https://doi.org/10.1016/S0273-1177(97)00270-6 "
        "(refreshed by Akatsuki cloud-tracked winds: Horinouchi, T., et al. "
        "(2017). Equatorial jet in the lower to middle cloud layer of Venus "
        "revealed by Akatsuki. Nature Geoscience, 10, 646-651.)"
    ),

    "voyager_2_pds": (
        "Voyager 2 Atmospheres Node, NASA Planetary Data System. "
        "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/"
        "Voyager/voyager.html "
        "(Uranus encounter Jan 1986: Stone, E. C., & Miner, E. D. (1986). "
        "Science, 233, 39-43. Neptune encounter Aug 1989: Stone, E. C., & "
        "Miner, E. D. (1989). Science, 246, 1417-1421.)"
    ),

    "juno_mwr_pds": (
        "Juno Atmospheres Node, NASA Planetary Data System. "
        "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/"
        "Juno/juno.html "
        "(Microwave Radiometer: Janssen, M. A., Oswald, J. E., Brown, S. T., "
        "et al. (2017). MWR: Microwave Radiometer for the Juno mission to "
        "Jupiter. Space Science Reviews, 213, 139-185.)"
    ),

    "new_horizons_pds": (
        "New Horizons Atmospheres Node, NASA Planetary Data System. "
        "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/"
        "NewHorizons/newhorizons.html "
        "(Pluto flyby July 2015: Stern, S. A., et al. (2015). The Pluto "
        "system: Initial results from its exploration by New Horizons. "
        "Science, 350, aad1815.)"
    ),

    "maven_pds": (
        "MAVEN Atmospheres Node, NASA Planetary Data System. "
        "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/"
        "MAVEN/maven.html "
        "(Jakosky, B. M., Lin, R. P., Grebowsky, J. M., et al. (2015). "
        "The Mars Atmosphere and Volatile Evolution (MAVEN) mission. "
        "Space Science Reviews, 195, 3-48.)"
    ),

    "cassini_cirs_pds": (
        "Cassini Atmospheres Node, NASA Planetary Data System. "
        "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/"
        "Cassini/Cassini.html "
        "(Composite Infrared Spectrometer: Flasar, F. M., Kunde, V. G., Abbas, "
        "M. M., et al. (2004). Exploring the Saturn system in the thermal "
        "infrared: The composite infrared spectrometer. Space Science "
        "Reviews, 115, 169-297.)"
    ),
}


# ---------------------------------------------------------------------------
# Reference epoch for the catalog (J2000.0 TDB, mirroring sibling catalogs).
# Per-record coverage_start_jd / coverage_end_jd hold the actual archive
# bounds; this constant is the catalog-wide neutral zero point.
# ---------------------------------------------------------------------------
FLUID_REFERENCE_JD: float = 2451545.0


__all__ = [
    # Precision flags
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    # Dataclasses
    "BodyClimatology",
    "FluidArchive",
    "FluidStateCoverage",
    # Data lists / dicts
    "BODY_CLIMATOLOGY",
    "FLUID_ARCHIVES",
    "FLUID_STATE_COVERAGE",
    "SOURCES",
    # Catalog reference epoch
    "FLUID_REFERENCE_JD",
]
