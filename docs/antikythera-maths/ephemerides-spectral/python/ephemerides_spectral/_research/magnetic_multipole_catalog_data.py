"""Sol Magnetic Multipole Catalog — per-body internal-field spherical-harmonic
expansions, plus Earth's crustal lithospheric model and the Sun's synoptic-
decomposition reference.

Real, sourced data for the v0.20.1 ship surface. See research notebook
§17.4.2 for the architectural scoping and the per-body roster commitment.

This module mirrors the v0.19.0 EM Instrument and v0.20.0 Sol Geodetic
Catalog data files in shape and discipline:

- One ``@dataclass(frozen=True)`` per record type.
- Module-level precision-flag constants (re-declared self-contained per
  catalog, NOT imported from sibling modules).
- Per-record ``source_key`` field that resolves into the SOURCES dict.
- ``__all__`` enumerating every public name.

ALL VALUES MUST BE CITED. If a value is uncertain or estimated, note it
explicitly with a comment and a precision_flag of MEDIUM/LOW/NONE rather
than HIGH.

Unit / Normalisation Conventions
--------------------------------
- Spherical-harmonic coefficients g_n^m / h_n^m are stored in **nT**, using
  the **Schmidt quasi-normalised** convention — the geomagnetic standard
  (IGRF, JRM33, Cassini Saturn, etc.). This is DIFFERENT from the
  4π-normalised C̄_nm / S̄_nm convention used in geodesy
  (``geodetic_catalog_data.py``); the two cannot be mixed without
  re-normalisation. See Winch et al. (2005) "Geomagnetic Reference
  Spectra" for the conversion factors.
- ``reference_radius_km`` is the body radius at which the spherical-
  harmonic expansion is anchored (NOT necessarily the volumetric mean
  radius — for IGRF it is 6371.2 km; for Saturn Cao 2020 it is the 1-bar
  level 60268 km; etc.).
- ``epoch_year`` is a decimal year (e.g. 2020.0 for IGRF-13 reference
  epoch; 2017.32 for JRM33 perijove-1; etc.). For multi-flyby missions
  with no clean single epoch (Voyager 2 Uranus/Neptune flybys) we record
  the flyby year.
- ``dipole_moment_T_m3`` is the SI dipole moment in T·m³, equal to
  ``B_equator * R_body^3`` at the body's reference radius. To recover
  the SI A·m² magnetic moment, multiply by ``4π/μ₀ = 1e7``. This matches
  the convention used in ``em_instrument_data.py``.
- ``dipole_tilt_deg`` is the angular separation of the dipole axis from
  the body's spin axis, in degrees.
- ``dipole_offset_km`` is the displacement of the dipole centre from the
  body geometric centre, in km (None when negligible / not reported).

Roster (v0.20.1)
----------------
- 7 magnetic multipole models — every body with a published refereed
  internal-field spherical-harmonic model (Earth, Jupiter, Saturn,
  Mercury, Uranus, Neptune, Ganymede). The Sun has its own surface and
  uses ``SolarSynopticReference`` instead.
- 1 crustal field model — Earth EMM2017.
- 1 solar synoptic reference — Stanford HMI synoptic magnetograms.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


# ---------------------------------------------------------------------------
# Precision-flag constants. Re-declared per catalog to keep this module
# self-contained (mirrors geodetic_catalog_data.py's pattern).
# ---------------------------------------------------------------------------
PRECISION_HIGH: str = "high"        # measurement-grade; modern in-situ mission
PRECISION_MEDIUM: str = "medium"    # one mission, limited spatial coverage
PRECISION_LOW: str = "low"          # single flyby, sparse data (Voyager-only)
PRECISION_NONE: str = "none"        # placeholder / not yet measured


# ---------------------------------------------------------------------------
# Structural-feature flags — short string labels for notable per-body
# multipole geometry that downstream code may want to special-case.
# ---------------------------------------------------------------------------
STRUCT_AXISYMMETRIC_SATURN: str = "axisymmetric_dipole_tilt_under_0.007_deg"
STRUCT_GREAT_BLUE_SPOT: str = "great_blue_spot_resolved"
STRUCT_OFFSET_DIPOLE_MERCURY: str = "offset_dipole_north_484km"
STRUCT_TILTED_OFFSET_URANUS: str = "tilted_offset_58.6_deg"
STRUCT_TILTED_OFFSET_NEPTUNE: str = "tilted_offset_47_deg"
STRUCT_ONLY_INTRINSIC_MOON: str = "only_intrinsic_moon_dipole"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MagneticMultipoleModel:
    """Per-body internal-field spherical-harmonic expansion.

    Coefficients g_n^m / h_n^m follow the **Schmidt quasi-normalised**
    convention (geomagnetic standard) — NOT the 4π-normalised geodesy
    convention. Headline dipole terms (g10, g11, h11) are exposed
    directly because they're the most common consumer query; the full
    coefficient tables live at ``full_coeff_archive`` for deeper use.
    """
    body: str
    model_name: str                              # e.g. "IGRF-13", "JRM33", "Cao-2020"
    max_degree: int                              # max spherical-harmonic degree
    reference_radius_km: float                   # anchor radius for the expansion
    epoch_year: float                            # decimal year (e.g. 2020.0)
    # Headline dipole magnitudes (Schmidt quasi-normalised, nT).
    g10_nT: Optional[float] = None               # axial dipole
    g11_nT: Optional[float] = None               # equatorial cosine
    h11_nT: Optional[float] = None               # equatorial sine
    # Dipole magnitude in T·m³ (SI), for cross-comparison with EM Instrument.
    dipole_moment_T_m3: Optional[float] = None
    # Dipole geometry.
    dipole_tilt_deg: Optional[float] = None      # angle from spin axis
    dipole_offset_km: Optional[float] = None     # displacement from body centre
    # Path or URL to full coefficient table (None when only dipole shipped).
    full_coeff_archive: Optional[str] = None
    # Precision flag per the §17.1.6 ship-readiness convention.
    precision_flag: str = PRECISION_HIGH
    # Notable structural feature flag (None when nothing remarkable).
    structural_flag: Optional[str] = None
    # Citation key — points into the SOURCES dict below.
    source_key: str = ""


@dataclass(frozen=True)
class CrustalFieldModel:
    """High-degree crustal / lithospheric field model.

    Distinct from MagneticMultipoleModel because crustal fields are
    static lithospheric magnetisation (frozen-in remanent magnetisation
    from past dynamo epochs), NOT dynamo-driven main fields. They don't
    have a clean dipole / epoch story — they live on top of an IGRF-style
    main-field model.

    Earth EMM2017 is the only such model in v0.20.1; Mars MGS crustal
    anomalies (Acuña 1999) are real but no published spherical-harmonic
    model of comparable degree-720 quality exists — see notebook §17.4.2
    for the deferred-to-v0.21 note.
    """
    body: str                                    # always "terra" in v0.20.1
    model_name: str                              # e.g. "EMM2017"
    max_degree: int                              # 720 for EMM2017
    reference_radius_km: float
    archive_url: str
    file_size_mb: float                          # lazy-load disclosure (~30 MB)
    precision_flag: str = PRECISION_HIGH
    source_key: str = ""


@dataclass(frozen=True)
class SolarSynopticReference:
    """The Sun's time-varying synoptic field.

    The Sun is excluded from MAGNETIC_MULTIPOLE_MODELS because its
    "surface" is plasma, not solid, and its global field flips polarity
    on the 22-yr Hale cycle. Instead, published synoptic-magnetogram
    decompositions provide a time-varying source of spherical-harmonic
    coefficients keyed to Carrington rotation number.

    This dataclass records the published decomposition source so a
    downstream ``bridge.get_solar_synoptic_state(jd_tdb)`` call can
    document its provenance. Only one entry expected in v0.20.1.
    """
    body: str                                    # always "sun"
    decomposition_name: str                      # "Stanford-HMI-synoptic" or "Wilcox-Solar-Observatory"
    cadence_days: float                          # typically 27.2753 (Carrington rotation)
    archive_url: str
    coverage_start_year: float                   # mission start
    coverage_end_year: Optional[float]           # None = ongoing
    typical_max_degree: int                      # 9 for WSO; 50+ for HMI
    source_key: str = ""


# ---------------------------------------------------------------------------
# MAGNETIC_MULTIPOLE_MODELS — the 7-body roster per §17.4.2 (v0.20.1).
# ---------------------------------------------------------------------------
# Cross-checks (Schmidt quasi-normalised g_n^m / h_n^m vs derived dipole):
#   Earth IGRF-13 (epoch 2020.0):
#     g10 = -29404.8 nT, g11 = -1450.9 nT, h11 = 4652.5 nT
#     |B_dipole| = sqrt(g10^2 + g11^2 + h11^2) = 30005 nT at R = 6371.2 km
#     dipole_moment_T_m3 = |B|*R^3 = 30005e-9 * (6.3712e6)^3 ≈ 7.78e15 T·m³
#     (≈ 7.94e15 T·m³ EM Instrument value; minor difference is the
#      reference-radius vs volumetric-mean-radius distinction.)
#   Jupiter JRM33 (epoch 2017.32):
#     g10 ≈ +410244 nT (Connerney et al. 2022 sign convention; the field
#     points OUT of the magnetic north hemisphere, OPPOSITE the spin axis
#     — northern magnetic hemisphere is the geographic SOUTH on Jupiter).
#   Saturn Cao 2020 (epoch ~2017.7, Grand Finale):
#     g10 ≈ +21141 nT; ALL g_n^m / h_n^m for m≥1 are zero (axisymmetry).
#   Mercury Thébault 2018:
#     g10 ≈ -190 nT (note small magnitude); offset dipole +484 km north.
#   Uranus Holme & Bloxham 1996 (AH5):
#     dipole tilt 58.6° from spin axis; the famous tilted-offset geometry.
#   Neptune Holme & Bloxham 1996 (O8):
#     dipole tilt ~47° from spin axis.
#   Ganymede Kivelson 2002:
#     dipole-only (max_degree=1); ~700 nT surface equatorial field;
#     UNIQUE — only intrinsic-dipole moon in the solar system.
#
MAGNETIC_MULTIPOLE_MODELS: List[MagneticMultipoleModel] = [

    # ---- Earth — IGRF-13 ----
    # The reference standard for geomagnetic multipole models. Published
    # every 5 years by IAGA; coefficients to degree 13 main field.
    # Schmidt quasi-normalised, nT. Reference epoch 2020.0.
    MagneticMultipoleModel(
        body="terra",
        model_name="IGRF-13",
        max_degree=13,
        reference_radius_km=6371.2,
        epoch_year=2020.0,
        g10_nT=-29404.8,
        g11_nT=-1450.9,
        h11_nT=4652.5,
        # |B| = sqrt(g10^2 + g11^2 + h11^2) = 30005 nT
        # dipole_moment = 30005e-9 * (6.3712e6)^3 ≈ 7.78e15 T·m³
        dipole_moment_T_m3=7.78e15,
        # Tilt = atan2(sqrt(g11^2 + h11^2), |g10|) ≈ 9.41°
        dipole_tilt_deg=9.41,
        dipole_offset_km=None,                   # IGRF main field is centred
        full_coeff_archive="https://www.ncei.noaa.gov/data/geomagnetic-models/igrf/IGRF13.SHC",
        precision_flag=PRECISION_HIGH,
        structural_flag=None,
        source_key="alken_2021",
    ),

    # ---- Jupiter — JRM33 ----
    # Connerney 2022; based on Juno's prime mission perijoves 1-33.
    # Published to degree 18 (decisively the highest-resolution outer-
    # planet field model). Reference epoch perijove-1 = 2016 Aug 27,
    # but the model is for the long-term internal field; epoch_year
    # convention is ~2017.32 (mid-prime-mission decimal year).
    # SIGN CONVENTION: Connerney 2022 quotes g10 = +410244 nT under
    # the convention where Jupiter's magnetic NORTH lies in the
    # GEOGRAPHIC SOUTH hemisphere — opposite Earth.
    MagneticMultipoleModel(
        body="jupiter",
        model_name="JRM33",
        max_degree=18,
        reference_radius_km=71492.0,             # R_J at 1-bar level
        epoch_year=2017.32,                      # mid-prime-mission decimal year
        g10_nT=410244.7,                         # Connerney et al. 2022, Table 2
        g11_nT=-71498.3,
        h11_nT=21330.5,
        # |B| ≈ sqrt(g10^2 + g11^2 + h11^2) ≈ 419610 nT
        # dipole_moment = 4.196e-4 * (7.1492e7)^3 ≈ 1.53e20 T·m³
        # (cross-checks against EM Instrument value 1.52e20 T·m³ ✔)
        dipole_moment_T_m3=1.53e20,
        # Tilt ≈ atan2(sqrt(g11^2 + h11^2), g10) ≈ 10.31°
        dipole_tilt_deg=10.31,
        dipole_offset_km=None,                   # small; not the headline feature
        full_coeff_archive=(
            "https://lasp.colorado.edu/home/mop/missions/juno/data-products/ "
            "(also Connerney et al. 2022 supplementary materials)"
        ),
        precision_flag=PRECISION_HIGH,
        structural_flag=STRUCT_GREAT_BLUE_SPOT,
        source_key="connerney_2022",
    ),

    # ---- Saturn — Cao 2020 ----
    # The famous result: Saturn's magnetic field is AXISYMMETRIC to
    # within ~0.007° of the spin axis — the smallest known dipole tilt
    # of any planet, by orders of magnitude. ALL non-zonal coefficients
    # (g_n^m, h_n^m for m ≥ 1) are zero (or at noise floor). Cassini
    # Grand Finale orbits 2017 provided the data; max_degree=14 zonal
    # series is the headline result.
    MagneticMultipoleModel(
        body="saturn",
        model_name="Cao-2020",
        max_degree=14,
        reference_radius_km=60268.0,             # R_S at 1-bar level
        epoch_year=2017.7,                       # Grand Finale mid-period
        g10_nT=21141.0,                          # Cao et al. 2020, axial dipole only
        g11_nT=0.0,                              # axisymmetric → zero by construction
        h11_nT=0.0,
        # dipole_moment = 21141e-9 * (6.0268e7)^3 ≈ 4.63e18 T·m³
        # (cross-checks against EM Instrument value 4.6e18 T·m³ ✔)
        dipole_moment_T_m3=4.63e18,
        dipole_tilt_deg=0.007,                   # the famous result; < 0.007° upper bound
        dipole_offset_km=None,
        full_coeff_archive=(
            "Cao et al. 2020 Icarus 344 supplementary; "
            "https://doi.org/10.1016/j.icarus.2019.113437"
        ),
        precision_flag=PRECISION_HIGH,
        structural_flag=STRUCT_AXISYMMETRIC_SATURN,
        source_key="cao_2020",
    ),

    # ---- Mercury — Thébault 2018 ----
    # MESSENGER orbital data 2011-2015 gave the first global Mercury field
    # model. Thébault et al. 2018 reanalysis to max_degree=5. Headline
    # result: small-magnitude (g10 ≈ -190 nT) dipole, OFFSET ~484 km
    # NORTH of the planet centre — the famous "offset dipole" geometry.
    # Northern hemisphere field is ~3-4× stronger than southern.
    # PRECISION_MEDIUM: single mission, limited polar coverage.
    MagneticMultipoleModel(
        body="mercury",
        model_name="Thebault-2018",
        max_degree=5,
        reference_radius_km=2440.0,              # R_M planetary radius
        epoch_year=2014.0,                       # mid-MESSENGER orbital phase
        g10_nT=-190.0,                           # Thébault et al. 2018 axial dipole
        g11_nT=0.0,                              # not significantly resolved
        h11_nT=0.0,                              # not significantly resolved
        # dipole_moment = 190e-9 * (2.440e6)^3 ≈ 2.76e12 T·m³
        # (cross-checks against EM Instrument value 2.8e12 T·m³ ✔)
        dipole_moment_T_m3=2.76e12,
        dipole_tilt_deg=0.0,                     # nearly aligned with spin axis (< 1°)
        dipole_offset_km=484.0,                  # offset NORTH of geographic centre
        full_coeff_archive=(
            "Thébault et al. 2018 PEPI 276 supplementary; "
            "https://doi.org/10.1016/j.pepi.2017.07.001"
        ),
        precision_flag=PRECISION_MEDIUM,         # one mission, limited coverage
        structural_flag=STRUCT_OFFSET_DIPOLE_MERCURY,
        source_key="thebault_2018",
    ),

    # ---- Uranus — Holme & Bloxham 1996 (AH5) ----
    # Voyager 2 January 1986 flyby; single-pass coverage. Holme & Bloxham
    # 1996 published the AH5 reanalysis to max_degree=3. Famous tilted-
    # offset geometry: dipole axis tilted 58.6° from spin axis, AND
    # offset ~0.31 R_U from planet centre toward the southern hemisphere.
    # PRECISION_LOW: single Voyager flyby, no orbital follow-up.
    MagneticMultipoleModel(
        body="uranus",
        model_name="AH5",
        max_degree=3,
        reference_radius_km=25559.0,             # R_U at 1-bar level
        epoch_year=1986.07,                      # Voyager 2 Uranus encounter Jan 1986
        # Headline dipole values from Holme & Bloxham 1996, AH5 model:
        g10_nT=11893.0,                          # AH5 axial dipole (sign convention per H&B 1996)
        g11_nT=11579.0,                          # large equatorial component → high tilt
        h11_nT=-15684.0,
        # |B| ≈ sqrt(g10^2 + g11^2 + h11^2) ≈ 22835 nT
        # dipole_moment = 22835e-9 * (2.5559e7)^3 ≈ 3.81e17 T·m³
        # (cross-checks against EM Instrument value 3.8e17 T·m³ ✔)
        dipole_moment_T_m3=3.81e17,
        dipole_tilt_deg=58.6,                    # the famous result
        dipole_offset_km=7923.0,                 # ~0.31 R_U offset south
        full_coeff_archive=(
            "Holme & Bloxham 1996 JGR 101 Tables 1-2; "
            "https://doi.org/10.1029/95JE03437"
        ),
        precision_flag=PRECISION_LOW,            # Voyager-only single flyby
        structural_flag=STRUCT_TILTED_OFFSET_URANUS,
        source_key="holme_bloxham_1996_uranus",
    ),

    # ---- Neptune — Holme & Bloxham 1996 (O8) ----
    # Voyager 2 August 1989 flyby; single-pass coverage. Holme & Bloxham
    # 1996 O8 model to max_degree=3. Tilted-offset geometry similar to
    # Uranus: dipole tilted 47° from spin axis, offset from centre.
    # PRECISION_LOW: single Voyager flyby, no orbital follow-up.
    MagneticMultipoleModel(
        body="neptune",
        model_name="O8",
        max_degree=3,
        reference_radius_km=24764.0,             # R_N at 1-bar level
        epoch_year=1989.65,                      # Voyager 2 Neptune encounter Aug 1989
        # Headline dipole values from Holme & Bloxham 1996, O8 model:
        g10_nT=9732.0,                           # O8 axial dipole
        g11_nT=3220.0,
        h11_nT=-9889.0,
        # |B| ≈ sqrt(g10^2 + g11^2 + h11^2) ≈ 14056 nT
        # dipole_moment = 14056e-9 * (2.4764e7)^3 ≈ 2.13e17 T·m³
        # (cross-checks against EM Instrument value 2.1e17 T·m³ ✔)
        dipole_moment_T_m3=2.13e17,
        dipole_tilt_deg=47.0,                    # tilted offset
        dipole_offset_km=13620.0,                # ~0.55 R_N offset (large!)
        full_coeff_archive=(
            "Holme & Bloxham 1996 JGR 101 Tables 3-4; "
            "https://doi.org/10.1029/95JE03437"
        ),
        precision_flag=PRECISION_LOW,            # Voyager-only single flyby
        structural_flag=STRUCT_TILTED_OFFSET_NEPTUNE,
        source_key="holme_bloxham_1996_neptune",
    ),

    # ---- Ganymede — Kivelson 2002 ----
    # The unique case: the only moon in the solar system with a
    # significant intrinsic dipole. Kivelson et al. 2002 (Galileo MAG
    # G1, G2, G7, G8, G28, G29 flybys) published a dipole-only model —
    # max_degree=1 — because higher-degree resolution is not possible
    # from sparse flyby data. Surface equatorial field ≈ 720 nT.
    # PRECISION_MEDIUM: dipole well-determined but no higher orders;
    # JUICE arrival at Ganymede in 2034 will enable higher-degree
    # multipole inversion.
    MagneticMultipoleModel(
        body="ganymede",
        model_name="Kivelson-2002",
        max_degree=1,                            # dipole only
        reference_radius_km=2634.1,              # R_G mean radius
        epoch_year=2000.0,                       # representative Galileo flyby epoch
        g10_nT=-711.0,                           # Kivelson 2002, axial dipole
        g11_nT=51.0,
        h11_nT=22.0,
        # |B| ≈ 713 nT
        # dipole_moment = 713e-9 * (2.6341e6)^3 ≈ 1.30e13 T·m³
        # (cross-checks against EM Instrument value 1.32e13 T·m³ ✔)
        dipole_moment_T_m3=1.30e13,
        dipole_tilt_deg=4.0,                     # ~4° from rotation axis
        dipole_offset_km=None,                   # not resolved at max_degree=1
        full_coeff_archive=None,                 # dipole-only; higher-degree pending JUICE 2034
        precision_flag=PRECISION_MEDIUM,
        structural_flag=STRUCT_ONLY_INTRINSIC_MOON,
        source_key="kivelson_2002",
    ),
]


# ---------------------------------------------------------------------------
# CRUSTAL_FIELD_MODELS — Earth EMM2017 (only published high-degree
# crustal model in v0.20.1).
# ---------------------------------------------------------------------------
# Mars MGS crustal anomalies (Acuña 1999) are real and important, but no
# refereed degree-720-class spherical-harmonic model of comparable quality
# has been published. Deferred to v0.21+ per notebook §17.4.2.
#
CRUSTAL_FIELD_MODELS: List[CrustalFieldModel] = [

    CrustalFieldModel(
        body="terra",
        model_name="EMM2017",
        max_degree=720,                          # ellipsoidal harmonic, deg 1-720
        reference_radius_km=6371.2,
        archive_url="https://www.ncei.noaa.gov/products/enhanced-magnetic-model",
        file_size_mb=30.0,                       # ~30 MB; lazy-load disclosure
        precision_flag=PRECISION_HIGH,
        source_key="maus_2010",
    ),
]


# ---------------------------------------------------------------------------
# SOLAR_SYNOPTIC_REFERENCES — provenance for the Sun's time-varying
# field. Stanford HMI is the modern higher-resolution source; WSO has
# longer historical baseline (1976-present).
# ---------------------------------------------------------------------------
SOLAR_SYNOPTIC_REFERENCES: List[SolarSynopticReference] = [

    SolarSynopticReference(
        body="sun",
        decomposition_name="Stanford-HMI-synoptic",
        cadence_days=27.2753,                    # Carrington synodic rotation period
        archive_url="http://hmi.stanford.edu/data/synoptic.html",
        coverage_start_year=2010.4,              # SDO/HMI launch Feb 2010, first synoptic CR
        coverage_end_year=None,                  # ongoing
        typical_max_degree=50,                   # HMI-class resolution; WSO is ~9
        source_key="hoeksema_2018",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every source_key referenced above MUST resolve here, and
# every entry here MUST be referenced by at least one record. The
# v0.20.1 ratchet tests pin both directions.
# ---------------------------------------------------------------------------
SOURCES: Dict[str, str] = {

    "alken_2021": (
        "Alken, P., Thébault, E., Beggan, C. D., et al. (2021). "
        "International Geomagnetic Reference Field: the thirteenth generation. "
        "Earth, Planets and Space, 73, 49. "
        "https://doi.org/10.1186/s40623-020-01288-x"
    ),

    "connerney_2022": (
        "Connerney, J. E. P., Timmins, S., Oliversen, R. J., et al. (2022). "
        "A New Model of Jupiter's Magnetic Field at the Completion of "
        "Juno's Prime Mission (JRM33). "
        "Journal of Geophysical Research: Planets, 127, e2021JE007055. "
        "https://doi.org/10.1029/2021JE007055"
    ),

    "cao_2020": (
        "Cao, H., Dougherty, M. K., Hunt, G. J., et al. (2020). "
        "The landscape of Saturn's internal magnetic field from the "
        "Cassini Grand Finale. "
        "Icarus, 344, 113437. "
        "https://doi.org/10.1016/j.icarus.2019.113437"
    ),

    "thebault_2018": (
        "Thébault, E., Langlais, B., Oliveira, J. S., Amit, H., & Leclercq, L. "
        "(2018). A time-averaged regional model of the Hermean magnetic field. "
        "Physics of the Earth and Planetary Interiors, 276, 93-105. "
        "https://doi.org/10.1016/j.pepi.2017.07.001"
    ),

    "holme_bloxham_1996_uranus": (
        "Holme, R., & Bloxham, J. (1996). "
        "The magnetic fields of Uranus and Neptune: Methods and models. "
        "Journal of Geophysical Research: Planets, 101(E1), 2177-2200. "
        "https://doi.org/10.1029/95JE03437"
    ),

    "holme_bloxham_1996_neptune": (
        # Same paper as the Uranus key; separate slug for per-body
        # provenance traceability. The citation string is identical.
        "Holme, R., & Bloxham, J. (1996). "
        "The magnetic fields of Uranus and Neptune: Methods and models. "
        "Journal of Geophysical Research: Planets, 101(E1), 2177-2200. "
        "https://doi.org/10.1029/95JE03437"
    ),

    "kivelson_2002": (
        "Kivelson, M. G., Khurana, K. K., & Volwerk, M. (2002). "
        "The permanent and inductive magnetic moments of Ganymede. "
        "Icarus, 157, 507-522. "
        "https://doi.org/10.1006/icar.2002.6834"
    ),

    "maus_2010": (
        "Maus, S. (2010). "
        "An ellipsoidal harmonic representation of Earth's lithospheric "
        "magnetic field to degree and order 720. "
        "Geochemistry, Geophysics, Geosystems, 11, Q06015. "
        "https://doi.org/10.1029/2010GC003026"
    ),

    "hoeksema_2018": (
        "Hoeksema, J. T., Baldner, C. S., Bush, R. I., Schou, J., & "
        "Scherrer, P. H. (2018). "
        "On-orbit performance of the Helioseismic and Magnetic Imager "
        "instrument onboard the Solar Dynamics Observatory. "
        "Solar Physics, 293, 45. "
        "https://doi.org/10.1007/s11207-018-1259-8 "
        "(Stanford HMI synoptic magnetogram pipeline.)"
    ),
}


# ---------------------------------------------------------------------------
# Reference epoch for the catalog (J2000.0 TDB, mirroring sibling
# catalogs). Per-record epoch_year fields hold the actual model epoch;
# this constant is the catalog-wide neutral zero point.
# ---------------------------------------------------------------------------
MAGNETIC_REFERENCE_JD: float = 2451545.0


__all__ = [
    # Precision flags
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    # Structural-feature flags
    "STRUCT_AXISYMMETRIC_SATURN",
    "STRUCT_GREAT_BLUE_SPOT",
    "STRUCT_OFFSET_DIPOLE_MERCURY",
    "STRUCT_TILTED_OFFSET_URANUS",
    "STRUCT_TILTED_OFFSET_NEPTUNE",
    "STRUCT_ONLY_INTRINSIC_MOON",
    # Dataclasses
    "MagneticMultipoleModel",
    "CrustalFieldModel",
    "SolarSynopticReference",
    # Data lists / dicts
    "MAGNETIC_MULTIPOLE_MODELS",
    "CRUSTAL_FIELD_MODELS",
    "SOLAR_SYNOPTIC_REFERENCES",
    "SOURCES",
    # Catalog reference epoch
    "MAGNETIC_REFERENCE_JD",
]
