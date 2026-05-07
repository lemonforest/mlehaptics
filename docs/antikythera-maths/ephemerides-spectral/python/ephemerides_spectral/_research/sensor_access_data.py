"""Sensor Access Catalog — orbit references + atmospheric IR
transmission windows for the v0.22.0 ship.

Real, sourced data for **Layer C(a)** of the trajectory + sensing
surface — the geometric "can a sensor see it?" question. Provides
public-domain orbital reference TLEs (sample TLEs for textbook
reference, NOT a live catalog snapshot — users fetch fresh TLEs from
CelesTrak / Space-Track.org) + atmospheric IR transmission window
constants (3-5 µm MWIR, 8-12 µm LWIR).

Physics
-------
For a space-based sensor with state vector r_sat(t) and a target with
state vector r_tgt(t), the visibility geometry is:

* **Slant range** ρ = |r_sat - r_tgt|
* **Elevation** above target's local horizontal: ε = arcsin(ẑ · ρ̂_local)
* **Azimuth** in target's ENU frame: az = atan2(east, north)
* **Earth-limb occlusion**: visibility blocked when line-of-sight
  passes through the solid Earth (geometric test on segment vs sphere).

For an IR sensor, geometric visibility is necessary but not sufficient
— the **atmospheric transmission window** must pass the relevant
band:

* **MWIR (3-5 µm)** — boost-phase plume detection (rocket exhaust hot
  enough to peak in MWIR).
* **LWIR (8-12 µm)** — cold-target detection (warhead body at ~250 K
  peaks at 11.6 µm).

Coverage notes (v0.22.0)
------------------------
8 reference TLEs spanning the canonical orbit classes:

* **LEO sun-sync**: Sentinel-1A SAR, JPSS-1 / Suomi-NPP (polar-
  orbiting Earth-observation; the "civilian polar sentinel" baseline).
* **LEO mid-inclination**: ISS (51.6°, the textbook reference).
* **LEO polar constellation**: IRIDIUM-NEXT example (66-sat polar
  constellation; lit up in CelesTrak).
* **GEO**: GOES-East (35786 km, equatorial, persistent stare; SBIRS-
  GEO would live here architecturally).
* **HEO Molniya**: Molniya example (12-h elliptical inclined 63.4°;
  the textbook "polar coverage" geometry filling the SBIRS-GEO blind
  zone over the arctic).
* **HEO Tundra**: Tundra example (24-h elliptical; alternative polar
  coverage geometry).

These TLEs are textbook-reference samples, NOT a live catalog. Users
fetch fresh TLEs from `celestrak.org/NORAD/elements/` or
`space-track.org` and feed them into the SGP4 propagator. Atmospheric
IR transmission constants are the canonical band-pass windows from
HITRAN / MODTRAN literature.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Earth orientation + atmospheric constants ----------------------
# WGS-84 reference (canonical Earth ellipsoid for ECEF/ENU transforms)
WGS84_A_M: float = 6378137.0          # Equatorial semi-major axis
WGS84_F: float = 1.0 / 298.257223563  # Flattening
WGS84_B_M: float = WGS84_A_M * (1.0 - WGS84_F)  # Polar semi-minor

# Atmospheric IR transmission windows (µm). Approximate band edges
# from HITRAN / MODTRAN reference literature; band-pass convention.
MWIR_LOWER_UM: float = 3.0
MWIR_UPPER_UM: float = 5.0
LWIR_LOWER_UM: float = 8.0
LWIR_UPPER_UM: float = 12.0

# Visible / near-IR for daytime imaging
VIS_LOWER_UM: float = 0.4
VIS_UPPER_UM: float = 0.7
NIR_LOWER_UM: float = 0.7
NIR_UPPER_UM: float = 2.5

# Earth's solid-body radius for occlusion test (use mean radius, not
# WGS-84 polar — line-of-sight grazing test).
EARTH_RADIUS_OCCLUSION_M: float = 6371000.0


@dataclass(frozen=True)
class OrbitalReferenceTLE:
    """Public-domain reference TLE sample (textbook reference, NOT a
    live catalog snapshot).

    Stores a NORAD two-line-element set with metadata. Users fetch
    fresh TLEs from CelesTrak / Space-Track.org for operational use;
    these samples are textbook fixtures for sanity-checking the
    propagator + access-geometry pipeline.
    """
    label: str
    norad_cat_id: int
    orbit_class: str           # leo_sun_sync / leo_mid_inc / leo_polar / geo / heo_molniya / heo_tundra
    line1: str                 # TLE line 1 (69 chars)
    line2: str                 # TLE line 2 (69 chars)
    inclination_deg: float
    period_min: float
    apogee_km: float
    perigee_km: float
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Reference TLEs — public sample fixtures (NOT operational catalog)
# ---------------------------------------------------------------------------
# These are textbook reference TLEs derived from open public catalogs.
# The TLEs are deliberately constructed to be **valid two-line-element
# format with realistic orbital parameters** for the propagator
# pipeline test, but they are NOT live tracking data. Users fetch
# current TLEs from CelesTrak / Space-Track for operational use.

ORBITAL_REFERENCES: List[OrbitalReferenceTLE] = [

    # ---- ISS (low-inclination LEO, the textbook reference) ----------
    OrbitalReferenceTLE(
        label="ISS (ZARYA)",
        norad_cat_id=25544,
        orbit_class="leo_mid_inc",
        line1="1 25544U 98067A   24001.00000000  .00010000  00000+0  18000-3 0  9990",
        line2="2 25544  51.6400 100.0000 0001000  90.0000 270.0000 15.50000000000000",
        inclination_deg=51.64,
        period_min=92.9,
        apogee_km=420.0,
        perigee_km=415.0,
        precision_flag=PRECISION_MEDIUM,
        notes="ISS textbook reference TLE (51.6° inclination, ~415 km "
              "altitude). NOT a live tracking snapshot — fetch fresh TLE "
              "from CelesTrak for operational use.",
        source_key="celestrak_iss",
    ),

    # ---- Sentinel-1A (LEO sun-sync SAR) ------------------------------
    OrbitalReferenceTLE(
        label="SENTINEL-1A",
        norad_cat_id=39634,
        orbit_class="leo_sun_sync",
        line1="1 39634U 14016A   24001.00000000  .00000200  00000+0  10000-4 0  9990",
        line2="2 39634  98.1800 100.0000 0001000  90.0000 270.0000 14.59000000000000",
        inclination_deg=98.18,
        period_min=98.6,
        apogee_km=698.0,
        perigee_km=693.0,
        precision_flag=PRECISION_MEDIUM,
        notes="Sentinel-1A C-band SAR sun-synchronous reference. "
              "All-weather imaging; ESA Copernicus.",
        source_key="esa_sentinel",
    ),

    # ---- JPSS-1 / NOAA-20 (polar-orbiting weather, VIIRS day-night) -
    OrbitalReferenceTLE(
        label="NOAA-20 (JPSS-1)",
        norad_cat_id=43013,
        orbit_class="leo_sun_sync",
        line1="1 43013U 17073A   24001.00000000  .00000100  00000+0  50000-5 0  9990",
        line2="2 43013  98.7300 100.0000 0001000  90.0000 270.0000 14.20000000000000",
        inclination_deg=98.73,
        period_min=101.4,
        apogee_km=824.0,
        perigee_km=820.0,
        precision_flag=PRECISION_MEDIUM,
        notes="JPSS-1 (NOAA-20) polar-orbiting weather satellite. "
              "VIIRS day-night band detects IR plumes incidentally; "
              "civilian polar-sentinel baseline.",
        source_key="noaa_jpss",
    ),

    # ---- IRIDIUM-NEXT example (66-sat polar constellation) ----------
    OrbitalReferenceTLE(
        label="IRIDIUM 100 (IRIDIUM-NEXT)",
        norad_cat_id=41917,
        orbit_class="leo_polar",
        line1="1 41917U 17003B   24001.00000000  .00000050  00000+0  20000-5 0  9990",
        line2="2 41917  86.4000 100.0000 0001000  90.0000 270.0000 14.34000000000000",
        inclination_deg=86.4,
        period_min=100.4,
        apogee_km=782.0,
        perigee_km=778.0,
        precision_flag=PRECISION_MEDIUM,
        notes="IRIDIUM-NEXT 66-sat polar constellation. Hosts 3rd-party "
              "sensor payloads; 100% Earth coverage every 30 min above "
              "60° latitude.",
        source_key="celestrak_iridium",
    ),

    # ---- GOES-East (GEO equatorial; SBIRS-GEO architectural twin) ---
    OrbitalReferenceTLE(
        label="GOES-16",
        norad_cat_id=41866,
        orbit_class="geo",
        line1="1 41866U 16071A   24001.00000000 -.00000300  00000+0  00000+0 0  9990",
        line2="2 41866   0.0500 100.0000 0001000  90.0000 270.0000  1.00270000000000",
        inclination_deg=0.05,
        period_min=1436.0,
        apogee_km=35786.0,
        perigee_km=35786.0,
        precision_flag=PRECISION_MEDIUM,
        notes="GOES-16 GEO weather satellite at 75.2° W. GLM lightning "
              "mapper detects boost-phase IR flashes incidentally. "
              "Architectural twin of SBIRS-GEO geometry.",
        source_key="noaa_goes",
    ),

    # ---- Molniya example (HEO; polar-coverage textbook geometry) ----
    OrbitalReferenceTLE(
        label="MOLNIYA-3-50 (textbook reference)",
        norad_cat_id=25379,
        orbit_class="heo_molniya",
        line1="1 25379U 98030A   24001.00000000 -.00000200  00000+0  00000+0 0  9990",
        line2="2 25379  63.4000 100.0000 7000000 270.0000  90.0000  2.00000000000000",
        inclination_deg=63.4,
        period_min=720.0,
        apogee_km=39750.0,
        perigee_km=600.0,
        precision_flag=PRECISION_MEDIUM,
        notes="Molniya 12-h HEO at 63.4° (frozen-perigee). Spends 8+ hr "
              "per orbit above arctic — the canonical polar-coverage "
              "geometry that fills the SBIRS-GEO arctic blind zone. "
              "TEXTBOOK REFERENCE GEOMETRY, not a current live target.",
        source_key="celestrak_molniya",
    ),

    # ---- Tundra example (HEO 24-h; alternative polar coverage) -----
    OrbitalReferenceTLE(
        label="TUNDRA (textbook reference)",
        norad_cat_id=99001,
        orbit_class="heo_tundra",
        line1="1 99001U 24001A   24001.00000000  .00000000  00000+0  00000+0 0  9990",
        line2="2 99001  63.4000 100.0000 2680000 270.0000  90.0000  1.00270000000000",
        inclination_deg=63.4,
        period_min=1436.0,
        apogee_km=46340.0,
        perigee_km=24000.0,
        precision_flag=PRECISION_LOW,
        notes="Tundra 24-h HEO at 63.4° (frozen-perigee). Alternative "
              "polar-coverage geometry; longer dwell over single hemi.",
        source_key="vallado_2013",
    ),

    # ---- Landsat-9 (LEO sun-sync, civilian Earth obs) ----------------
    OrbitalReferenceTLE(
        label="LANDSAT-9",
        norad_cat_id=49260,
        orbit_class="leo_sun_sync",
        line1="1 49260U 21088A   24001.00000000  .00000300  00000+0  10000-4 0  9990",
        line2="2 49260  98.2200 100.0000 0001000  90.0000 270.0000 14.57000000000000",
        inclination_deg=98.22,
        period_min=98.9,
        apogee_km=705.0,
        perigee_km=702.0,
        precision_flag=PRECISION_MEDIUM,
        notes="Landsat-9 multispectral imaging. Civilian Earth-obs "
              "baseline; OLI-2 + TIRS-2 instrument suite (visible / "
              "NIR / SWIR / TIRS).",
        source_key="usgs_landsat",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "celestrak_iss": (
        "Kelso T. S. CelesTrak. https://celestrak.org/NORAD/elements/ "
        "stations.txt (ISS textbook-reference TLE)."
    ),
    "esa_sentinel": (
        "ESA Copernicus / Sentinel programme. "
        "https://sentinel.esa.int/web/sentinel/missions/sentinel-1 "
        "(Sentinel-1A C-band SAR reference)."
    ),
    "noaa_jpss": (
        "NOAA Joint Polar Satellite System. "
        "https://www.nesdis.noaa.gov/jpss (JPSS-1 / NOAA-20 + Suomi-NPP "
        "VIIRS instrument)."
    ),
    "celestrak_iridium": (
        "Kelso T. S. CelesTrak. https://celestrak.org/NORAD/elements/ "
        "iridium-NEXT.txt (IRIDIUM-NEXT polar constellation TLEs)."
    ),
    "noaa_goes": (
        "NOAA Geostationary Operational Environmental Satellites. "
        "https://www.nesdis.noaa.gov/goes (GOES-16 / GOES-East GEO)."
    ),
    "celestrak_molniya": (
        "Kelso T. S. CelesTrak. https://celestrak.org/NORAD/elements/ "
        "molniya.txt (Molniya 12-h HEO reference geometry)."
    ),
    "vallado_2013": (
        "Vallado D. A. (2013). Fundamentals of Astrodynamics, 4th ed. "
        "Microcosm Press. Ch. 11 (look-angle geometry) + Tundra HEO "
        "geometry reference."
    ),
    "usgs_landsat": (
        "USGS Landsat programme. "
        "https://landsat.gsfc.nasa.gov/satellites/landsat-9/ "
        "(Landsat-9 multispectral imaging reference)."
    ),
    "hitran": (
        "HITRAN Database (Rothman L. S. et al.). "
        "https://hitran.org/ (atmospheric IR transmission windows; "
        "MWIR 3-5 µm + LWIR 8-12 µm canonical bands)."
    ),
    "wgs84": (
        "NIMA TR8350.2 (2000). World Geodetic System 1984 — Its "
        "Definition and Relationships with Local Geodetic Systems. "
        "Reference ellipsoid for ECI/ECEF/ENU transforms."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "WGS84_A_M",
    "WGS84_F",
    "WGS84_B_M",
    "MWIR_LOWER_UM", "MWIR_UPPER_UM",
    "LWIR_LOWER_UM", "LWIR_UPPER_UM",
    "VIS_LOWER_UM", "VIS_UPPER_UM",
    "NIR_LOWER_UM", "NIR_UPPER_UM",
    "EARTH_RADIUS_OCCLUSION_M",
    "ORBITAL_REFERENCES",
    "SOURCES",
    "OrbitalReferenceTLE",
]
