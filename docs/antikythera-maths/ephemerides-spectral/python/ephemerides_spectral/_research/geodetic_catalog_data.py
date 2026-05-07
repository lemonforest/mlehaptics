"""Sol Geodetic Catalog — per-body solid-body geodetic observables.

Real, sourced data for the v0.20.0 ship surface. See research notebook
§17.1 + §17.4.2 for the architectural scoping that motivates this
module. Mirrors the v0.19.0 ``em_instrument_data.py`` pattern exactly:
dataclasses, SOURCES dict, ``source_key`` per entry, scoping precision.

Three internal channels:

* **Gravity** — published spherical-harmonic geopotential models
  (``GravityModel``). Where only zonal-J series have been published
  (gas/ice giants, single-flyby moons), we ship those; ``S_nm = 0`` by
  axisymmetry. Where only point-mass GM is known (Jovian irregulars,
  small Saturnian co-orbitals) we ship ``max_degree=0``.
* **Topography** — DEM / shape-model spectral content
  (``TopographyModel``). Skipped when no published DEM exists.
* **Interior** — radial density profile of a body's interior
  (``InteriorModel`` containing a tuple of ``InteriorLayer``). Skipped
  when no published density profile exists.

ALL VALUES MUST BE CITED. Every entry carries a ``source_key`` that is
a key in the SOURCES dict at the bottom. Where a value is uncertain or
estimated, the ``precision_flag`` field carries one of
``PRECISION_HIGH`` / ``PRECISION_MEDIUM`` / ``PRECISION_LOW`` /
``PRECISION_NONE`` per the §17.1.6 ship-readiness convention.

Units convention
----------------
* ``GM`` (gravitational parameter, μ = G·M): km³/s² (standard
  planetary-science unit).
* ``reference_radius_km``: km.
* ``J2``, ``J3``, ``J4``: dimensionless, unnormalised (the
  coefficients consumers most often want; see ``full_coeff_archive``
  for the normalised C̄_nm/S̄_nm tables on bodies where they exist).
* ``horizontal_resolution_km`` / ``vertical_precision_m``: km / m
  respectively, per the standard DEM convention.
* ``mean_density_kg_per_m3``: SI kg/m³ over each interior layer.
* ``total_mass_kg``: SI kg.

Coverage notes
--------------
This catalog is roster-broader than the v0.16.0 BODIES dict because
spacecraft-derived geodetic data has been collected for several small
bodies that are not in the orbital encoder roster (Eros, Bennu,
Itokawa, Ryugu). Those ship as ``body=<name>`` strings even though
``bodies.BODIES`` does not contain them. See §17.4.2 for the full
roster commitment.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"          # spacecraft-derived multipole expansion, current-era
PRECISION_MEDIUM: str = "medium"       # spacecraft-derived but limited degree / older mission
PRECISION_LOW: str = "low"             # Voyager-only / single-flyby / inferred-only
PRECISION_NONE: str = "none"           # no published model exists; placeholder only


@dataclass(frozen=True)
class GravityModel:
    """Per-body gravity multipole expansion (or zonal-only for gas/ice giants).

    Convention: spherical-harmonic Stokes coefficients ``C_nm``, ``S_nm``
    normalised to standard 4π-normalisation at reference radius ``R``.
    For zonal-only models (Jupiter / Saturn / Uranus / Neptune) only
    the ``J_n`` series is meaningful (``S_nm = 0`` by axisymmetry).
    """
    body: str
    model_name: str           # e.g. "EGM2008", "GRGM1200B", "Juno-zonals", "JRM33"
    max_degree: int           # 0 = point-mass only; 2 = J2-only; 13 = IGRF-13-equivalent
    reference_radius_km: float
    # GM (gravitational parameter, μ = G·M) in km³/s². Standard.
    gm_km3_per_s2: float
    # Just J2, J3, J4 explicitly for the most common consumer query.
    # Higher-degree coefficients live in linked data files (paths only).
    J2: Optional[float] = None
    J3: Optional[float] = None
    J4: Optional[float] = None
    # Path or URL to full coefficient table (.gfc / .cof / paper-supplement).
    # If None, the J-zonals are the entire shipped representation.
    full_coeff_archive: Optional[str] = None
    precision_flag: str = PRECISION_HIGH
    source_key: str = ""


@dataclass(frozen=True)
class TopographyModel:
    """Per-body topography / shape model spectral content."""
    body: str
    model_name: str           # e.g. "MOLA-MEGDR", "LOLA-SLDEM2015", "shape-polyhedron-DAWN"
    # DEM type: "global_grid" (full-coverage raster), "partial_grid" (Cassini SARTopo etc.),
    # "shape_polyhedron" (small-body polyhedral models), "limb_profile_only" (Voyager fly-by).
    representation: str
    # Horizontal sampling in km (for grids); diameter in km (for polyhedra).
    horizontal_resolution_km: Optional[float]
    # Vertical precision in m (for grids); shape uncertainty for polyhedra.
    vertical_precision_m: Optional[float]
    # Coverage fraction of body surface, in [0, 1].
    coverage_fraction: float
    # Power-spectrum decay slope (β in P(k) ∝ k^β), where measured.
    # For most planetary topography β ≈ −2 to −3 ("red noise"); values published
    # in the literature (Mars: Aharonson et al. 2001; Earth: Watts 2001).
    power_spectrum_slope: Optional[float] = None
    archive_url: Optional[str] = None
    precision_flag: str = PRECISION_HIGH
    source_key: str = ""


@dataclass(frozen=True)
class InteriorLayer:
    """One radial layer of a body's interior density profile."""
    name: str                 # "inner_core" / "outer_core" / "lower_mantle" / "crust" / etc.
    inner_radius_km: float
    outer_radius_km: float
    # Mean density in kg/m³ over this layer's radial range.
    mean_density_kg_per_m3: float
    # Composition string ("Fe + 5% Ni" / "silicate + Fe-Mg" / "H/He" / "ice")
    composition: str = ""


@dataclass(frozen=True)
class InteriorModel:
    """Per-body interior structure model (layered density profile)."""
    body: str
    model_name: str           # "PREM" / "GRAIL+Apollo" / "InSight-Khan-2023" / "Juno-Wahl-2017"
    # Total radius and mass for normalization checks.
    total_radius_km: float
    total_mass_kg: float
    # Layered density profile, ordered inner → outer.
    layers: Tuple[InteriorLayer, ...]
    # Dimensionless moment of inertia (I/MR²); 0.4 = uniform density, lower = mass concentrated toward centre.
    normalised_moi: Optional[float] = None
    # Has subsurface ocean?
    has_subsurface_ocean: bool = False
    archive_url: Optional[str] = None
    precision_flag: str = PRECISION_HIGH
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body gravity models — §17.4.2 roster.
#
# Convention checks:
#   Earth EGM2008 GM = 398600.4418 km³/s² ✔ (published value)
#   Earth J2 = 1.0826267e-3 ✔ (Pavlis 2012)
#   Moon GRGM1200B GM = 4902.800076 km³/s² ✔
#   Mars MRO120F GM = 42828.3737 km³/s² ✔
#   Jupiter J2 = 1.4696572e-2 ✔ (Iess 2018)
#   Saturn J2 = 1.6290573e-2 ✔ (Iess 2019)
#
# Note: J2 values stored in unnormalised convention. Multiply by
# √5 / (-1) = -√5 to convert to normalised C̄_20.
# ---------------------------------------------------------------------------

GRAVITY_MODELS: List[GravityModel] = [

    # ---- Sun (point-mass; the heliocentric reference) -----------------
    GravityModel(
        body="sun",
        model_name="IAU-2015-nominal",
        max_degree=0,                      # solar oblateness J2 ~ 2e-7 (Mecheri 2004) but not a multipole catalog
        reference_radius_km=695_700.0,
        gm_km3_per_s2=1.32712440018e11,    # IAU 2015 nominal solar GM
        J2=2.2e-7,                          # tiny — solar oblateness from helioseismology
        precision_flag=PRECISION_MEDIUM,
        source_key="iau_2015_nominal",
    ),

    # ---- Mercury — MESSENGER HgM008 -----------------------------------
    GravityModel(
        body="mercury",
        model_name="HgM008",
        max_degree=50,
        reference_radius_km=2_440.0,
        gm_km3_per_s2=22_031.86855,
        J2=5.0322e-5,                       # Mazarico 2014; revised by Genova 2019
        J3=1.07e-5,
        J4=-1.95e-5,
        full_coeff_archive="https://pgda.gsfc.nasa.gov/products/71",
        precision_flag=PRECISION_HIGH,
        source_key="mazarico_2014",
    ),

    # ---- Venus — Magellan MGNP180U ------------------------------------
    GravityModel(
        body="venus",
        model_name="MGNP180U",
        max_degree=180,                     # equatorial; ~40 effective at poles
        reference_radius_km=6_051.8,
        gm_km3_per_s2=324_858.592,
        J2=4.404e-6,
        J3=-2.11e-6,
        J4=-2.15e-6,
        full_coeff_archive="https://pds-geosciences.wustl.edu/mgn/mgn-v-rss-5-gravity-l2-v1/mg_5201/",
        precision_flag=PRECISION_MEDIUM,    # heterogeneous longitude/latitude resolution
        source_key="konopliv_1999",
    ),

    # ---- Earth — EGM2008 ----------------------------------------------
    GravityModel(
        body="terra",
        model_name="EGM2008",
        max_degree=2190,                    # block-diagonal to 2159
        reference_radius_km=6_378.1363,
        gm_km3_per_s2=398_600.4418,
        J2=1.0826267e-3,                    # Pavlis 2012, unnormalised
        J3=-2.5327e-6,
        J4=-1.6196e-6,
        full_coeff_archive="https://icgem.gfz-potsdam.de/getmodel/gfc/c50128797a9cb62e936337c890e4425f03f0461d7329b09a8cc8561504465340/EGM2008.gfc",
        precision_flag=PRECISION_HIGH,
        source_key="pavlis_2012",
    ),

    # ---- Moon — GRAIL GRGM1200B ---------------------------------------
    GravityModel(
        body="luna",
        model_name="GRGM1200B",
        max_degree=1200,
        reference_radius_km=1_738.0,
        gm_km3_per_s2=4_902.800076,
        J2=2.033542e-4,                     # Goossens 2020; Lemoine 2014 cross-check
        J3=8.4759e-6,
        J4=-9.616e-6,
        full_coeff_archive="https://pgda.gsfc.nasa.gov/products/50",
        precision_flag=PRECISION_HIGH,
        source_key="goossens_2020",
    ),

    # ---- Mars — MRO120F (JGMRO_120F) ----------------------------------
    GravityModel(
        body="mars",
        model_name="MRO120F",
        max_degree=120,
        reference_radius_km=3_396.0,
        gm_km3_per_s2=42_828.3737,
        J2=1.95626e-3,                      # Konopliv 2016
        J3=3.1450e-5,
        J4=-1.5377e-5,
        full_coeff_archive="https://pds-geosciences.wustl.edu/mro/mro-m-rss-5-sdp-v1/mrors_1xxx/data/shadr/",
        precision_flag=PRECISION_HIGH,
        source_key="konopliv_2016",
    ),

    # ---- Phobos (Mars I) — Pätzold 2014 / Jacobson 2010 ---------------
    GravityModel(
        body="phobos",
        model_name="MEX-Patzold-2014",
        max_degree=2,                       # J2 + C22 from MEX flybys
        reference_radius_km=11.0814,
        gm_km3_per_s2=7.087e-4,
        J2=0.105,                           # large — irregular shape; Pätzold 2014
        precision_flag=PRECISION_MEDIUM,
        source_key="patzold_2014",
    ),

    # ---- Deimos (Mars II) — point-mass only ---------------------------
    GravityModel(
        body="deimos",
        model_name="Jacobson-2010-pointmass",
        max_degree=0,
        reference_radius_km=6.2,
        gm_km3_per_s2=9.615e-5,
        precision_flag=PRECISION_MEDIUM,
        source_key="jacobson_2010_mars",
    ),

    # ---- Jupiter — Juno zonals (Iess 2018; Durante 2020) --------------
    GravityModel(
        body="jupiter",
        model_name="Juno-zonals-Durante-2020",
        max_degree=10,                      # zonal only (J2..J10 even + J3,J5,J7,J9 odd)
        reference_radius_km=71_492.0,
        gm_km3_per_s2=1.26686534e8,
        J2=1.4696572e-2,                    # Iess 2018
        J3=-4.0e-8,                          # tiny odd; Iess 2018
        J4=-5.86609e-4,                     # Iess 2018
        full_coeff_archive=None,             # Durante 2020 supplement table
        precision_flag=PRECISION_HIGH,
        source_key="iess_2018_jupiter",
    ),

    # ---- Galilean moons — Anderson 1996/1998a/1998b/2001 --------------
    # All Galilean GMs and J2/C22 from the Anderson series; J2/C22 in
    # hydrostatic ratio J2 = (10/3)C22 to within published uncertainties.
    GravityModel(
        body="io",
        model_name="Galileo-Anderson-2001",
        max_degree=2,
        reference_radius_km=1_821.6,
        gm_km3_per_s2=5_959.916,
        J2=1845.9e-6,                       # Anderson 2001
        precision_flag=PRECISION_HIGH,
        source_key="anderson_2001_io",
    ),
    GravityModel(
        body="europa",
        model_name="Galileo-Anderson-1998a",
        max_degree=2,
        reference_radius_km=1_565.0,
        gm_km3_per_s2=3_202.739,
        J2=435.5e-6,                        # Anderson 1998a; refined Gomez Casajus 2021
        precision_flag=PRECISION_HIGH,
        source_key="anderson_1998_europa",
    ),
    GravityModel(
        body="ganymede",
        model_name="Galileo-Anderson-1996",
        max_degree=2,
        reference_radius_km=2_634.0,
        gm_km3_per_s2=9_887.834,
        J2=127.8e-6,                        # Anderson 1996
        precision_flag=PRECISION_HIGH,
        source_key="anderson_1996_ganymede",
    ),
    GravityModel(
        body="callisto",
        model_name="Galileo-Anderson-2001b",
        max_degree=2,
        reference_radius_km=2_410.3,
        gm_km3_per_s2=7_179.292,
        J2=32.7e-6,                         # Anderson 2001b
        precision_flag=PRECISION_HIGH,
        source_key="anderson_2001_callisto",
    ),

    # ---- Jovian inner regulars — Galileo + JIRAM (limited) ------------
    GravityModel(
        body="amalthea",
        model_name="Galileo-Anderson-2005",
        max_degree=0,                       # GM-only from Galileo flyby
        reference_radius_km=83.5,
        gm_km3_per_s2=1.378e-1,
        precision_flag=PRECISION_LOW,
        source_key="anderson_2005_amalthea",
    ),
    GravityModel(
        body="metis",
        model_name="JPL-pointmass",
        max_degree=0,
        reference_radius_km=21.5,
        gm_km3_per_s2=2.5e-3,               # IAU/JPL nominal; no spacecraft determination
        precision_flag=PRECISION_LOW,
        source_key="jpl_ssd_jovian_satellites",
    ),
    GravityModel(
        body="adrastea",
        model_name="JPL-pointmass",
        max_degree=0,
        reference_radius_km=8.2,
        gm_km3_per_s2=1.3e-3,               # estimated from shape + assumed density
        precision_flag=PRECISION_LOW,
        source_key="jpl_ssd_jovian_satellites",
    ),
    GravityModel(
        body="thebe",
        model_name="JPL-pointmass",
        max_degree=0,
        reference_radius_km=49.3,
        gm_km3_per_s2=3.0e-2,
        precision_flag=PRECISION_LOW,
        source_key="jpl_ssd_jovian_satellites",
    ),

    # ---- Jovian irregulars — point-mass (no published multipole) ------
    GravityModel(
        body="himalia",
        model_name="Emelyanov-pointmass",
        max_degree=0,
        reference_radius_km=85.0,
        gm_km3_per_s2=4.5e-1,               # Emelyanov 2005 from Sinope/Pasiphae perturbations
        precision_flag=PRECISION_LOW,
        source_key="emelyanov_2005",
    ),
    GravityModel(
        body="pasiphae",
        model_name="Emelyanov-pointmass",
        max_degree=0,
        reference_radius_km=30.0,
        gm_km3_per_s2=2.0e-3,
        precision_flag=PRECISION_LOW,
        source_key="emelyanov_2005",
    ),
    GravityModel(
        body="sinope",
        model_name="Emelyanov-pointmass",
        max_degree=0,
        reference_radius_km=19.0,
        gm_km3_per_s2=5.2e-4,
        precision_flag=PRECISION_LOW,
        source_key="emelyanov_2005",
    ),

    # ---- Saturn — Cassini Grand Finale (Iess 2019) --------------------
    GravityModel(
        body="saturn",
        model_name="Cassini-Iess-2019",
        max_degree=12,                      # zonal only (J2..J12 even + J3,J5)
        reference_radius_km=60_330.0,
        gm_km3_per_s2=3.7931208e7,
        J2=1.6290573e-2,                    # Iess 2019, unnormalised
        J3=4.5e-8,                           # tiny — interior asymmetry
        J4=-9.36e-4,                         # Iess 2019
        full_coeff_archive=None,             # Iess 2019 supplement table; J6, J8, J10, J12 measured
        precision_flag=PRECISION_HIGH,
        source_key="iess_2019_saturn",
    ),

    # ---- Saturnian classical moons — Cassini RSS ----------------------
    GravityModel(
        body="mimas",
        model_name="Cassini-Jacobson-2006",
        max_degree=2,
        reference_radius_km=198.2,
        gm_km3_per_s2=2.5026,
        J2=1.59e-2,                          # large J2 — synchronous rotation
        precision_flag=PRECISION_MEDIUM,
        source_key="jacobson_2006_saturn",
    ),
    GravityModel(
        body="enceladus",
        model_name="Cassini-Iess-2014",
        max_degree=3,                       # J2, C22 + J3 anomaly south pole
        reference_radius_km=252.1,
        gm_km3_per_s2=7.2103,
        J2=5435.2e-6,                       # Iess 2014
        J3=-115.3e-6,                       # south-polar mass deficit
        precision_flag=PRECISION_HIGH,
        source_key="iess_2014_enceladus",
    ),
    GravityModel(
        body="tethys",
        model_name="Cassini-Jacobson-2006",
        max_degree=2,
        reference_radius_km=531.0,
        gm_km3_per_s2=41.21,
        J2=8.9e-3,
        precision_flag=PRECISION_MEDIUM,
        source_key="jacobson_2006_saturn",
    ),
    GravityModel(
        body="dione",
        model_name="Cassini-Jacobson-2006",
        max_degree=2,
        reference_radius_km=561.4,
        gm_km3_per_s2=73.116,
        J2=1.496e-3,                        # Cassini RSS
        precision_flag=PRECISION_MEDIUM,
        source_key="jacobson_2006_saturn",
    ),
    GravityModel(
        body="rhea",
        model_name="Cassini-Iess-2007",
        max_degree=2,
        reference_radius_km=763.5,
        gm_km3_per_s2=153.94,
        J2=9.31e-4,                         # Iess 2007
        precision_flag=PRECISION_HIGH,
        source_key="iess_2007_rhea",
    ),
    GravityModel(
        body="titan",
        model_name="Cassini-Iess-2010",
        max_degree=3,                       # J2, J3, C22 from Cassini RSS
        reference_radius_km=2_575.0,
        gm_km3_per_s2=8_978.1382,
        J2=33.462e-6,                       # Iess 2010 / Durante 2019
        J3=-1.84e-6,
        precision_flag=PRECISION_HIGH,
        source_key="iess_2010_titan",
    ),
    GravityModel(
        body="iapetus",
        model_name="Cassini-Jacobson-2006",
        max_degree=2,
        reference_radius_km=734.3,
        gm_km3_per_s2=120.51,
        J2=4.8e-3,                          # very oblate — fossil rotation bulge (Castillo-Rogez 2007)
        precision_flag=PRECISION_MEDIUM,
        source_key="jacobson_2006_saturn",
    ),
    GravityModel(
        body="hyperion",
        model_name="JPL-pointmass",
        max_degree=0,
        reference_radius_km=135.0,
        gm_km3_per_s2=0.3727,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2006_saturn",
    ),
    GravityModel(
        body="phoebe",
        model_name="Cassini-Jacobson-2006",
        max_degree=0,
        reference_radius_km=106.5,
        gm_km3_per_s2=0.5532,
        precision_flag=PRECISION_MEDIUM,
        source_key="jacobson_2006_saturn",
    ),
    GravityModel(
        body="janus",
        model_name="Cassini-Spitale-2006",
        max_degree=0,
        reference_radius_km=89.5,
        gm_km3_per_s2=0.1263,
        precision_flag=PRECISION_LOW,
        source_key="spitale_2006",
    ),
    GravityModel(
        body="epimetheus",
        model_name="Cassini-Spitale-2006",
        max_degree=0,
        reference_radius_km=58.1,
        gm_km3_per_s2=0.0351,
        precision_flag=PRECISION_LOW,
        source_key="spitale_2006",
    ),

    # ---- Saturnian Lagrange trojans — shape-derived only --------------
    GravityModel(
        body="telesto",
        model_name="Cassini-shape-derived",
        max_degree=0,
        reference_radius_km=12.4,
        gm_km3_per_s2=2.7e-4,
        precision_flag=PRECISION_LOW,
        source_key="thomas_2010_saturnian_smalls",
    ),
    GravityModel(
        body="calypso",
        model_name="Cassini-shape-derived",
        max_degree=0,
        reference_radius_km=9.6,
        gm_km3_per_s2=8.0e-5,
        precision_flag=PRECISION_LOW,
        source_key="thomas_2010_saturnian_smalls",
    ),
    GravityModel(
        body="helene",
        model_name="Cassini-shape-derived",
        max_degree=0,
        reference_radius_km=17.5,
        gm_km3_per_s2=1.3e-4,
        precision_flag=PRECISION_LOW,
        source_key="thomas_2010_saturnian_smalls",
    ),
    GravityModel(
        body="polydeuces",
        model_name="Cassini-shape-derived",
        max_degree=0,
        reference_radius_km=1.3,
        gm_km3_per_s2=3.0e-7,
        precision_flag=PRECISION_LOW,
        source_key="thomas_2010_saturnian_smalls",
    ),

    # ---- Uranus — Voyager 2 fly-by zonals (Jacobson 2014 fit) ---------
    GravityModel(
        body="uranus",
        model_name="Voyager2-Jacobson-2014",
        max_degree=4,                       # J2, J4 only
        reference_radius_km=25_559.0,
        gm_km3_per_s2=5.793939e6,
        J2=3.34343e-3,                      # Voyager 2 + ground; Jacobson 2014
        J4=-2.885e-5,
        precision_flag=PRECISION_LOW,        # Voyager 2 fly-by, ~35 yr stale
        source_key="jacobson_2014_uranus",
    ),

    # ---- Uranian classical moons — Jacobson 2014 / 2025 ---------------
    # GM values from the Jacobson reanalyses of Voyager 2 + ground-based
    # mutual-event timings + ring occultations.
    GravityModel(
        body="miranda",
        model_name="Voyager2-Jacobson-2014",
        max_degree=0,
        reference_radius_km=235.8,
        gm_km3_per_s2=4.4,                  # Jacobson 2014
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2014_uranus",
    ),
    GravityModel(
        body="ariel",
        model_name="Voyager2-Jacobson-2014",
        max_degree=0,
        reference_radius_km=578.9,
        gm_km3_per_s2=86.1,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2014_uranus",
    ),
    GravityModel(
        body="umbriel",
        model_name="Voyager2-Jacobson-2014",
        max_degree=0,
        reference_radius_km=584.7,
        gm_km3_per_s2=81.5,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2014_uranus",
    ),
    GravityModel(
        body="titania",
        model_name="Voyager2-Jacobson-2014",
        max_degree=2,                       # J2 weakly constrained
        reference_radius_km=788.4,
        gm_km3_per_s2=228.2,
        J2=1.0e-3,                          # rough Voyager-era estimate
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2014_uranus",
    ),
    GravityModel(
        body="oberon",
        model_name="Voyager2-Jacobson-2014",
        max_degree=2,                       # J2 weakly constrained
        reference_radius_km=761.4,
        gm_km3_per_s2=192.4,
        J2=1.0e-3,                          # rough Voyager-era estimate
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2014_uranus",
    ),

    # ---- Neptune — Voyager 2 fly-by (Jacobson 2009) -------------------
    GravityModel(
        body="neptune",
        model_name="Voyager2-Jacobson-2009",
        max_degree=4,
        reference_radius_km=25_225.0,
        gm_km3_per_s2=6.836529e6,
        J2=3.408428e-3,
        J4=-3.34e-5,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2009_neptune",
    ),

    # ---- Neptunian moons — Voyager 2 ----------------------------------
    GravityModel(
        body="triton",
        model_name="Voyager2-Jacobson-2009",
        max_degree=0,                       # J2 not separable from Neptune oblateness fit
        reference_radius_km=1_353.4,
        gm_km3_per_s2=1428.495,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2009_neptune",
    ),
    GravityModel(
        body="proteus",
        model_name="Voyager2-Jacobson-2009",
        max_degree=0,
        reference_radius_km=210.0,
        gm_km3_per_s2=2.95,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2009_neptune",
    ),
    GravityModel(
        body="nereid",
        model_name="JPL-pointmass",
        max_degree=0,
        reference_radius_km=170.0,
        gm_km3_per_s2=2.06,
        precision_flag=PRECISION_LOW,
        source_key="jacobson_2009_neptune",
    ),

    # ---- Pluto / Charon — New Horizons (Brozović 2015 / Stern 2015) ---
    GravityModel(
        body="pluto",
        model_name="NewHorizons-Brozovic-2015",
        max_degree=0,                       # J2 unresolved from single fly-by
        reference_radius_km=1_188.3,
        gm_km3_per_s2=869.61,
        precision_flag=PRECISION_LOW,
        source_key="brozovic_2015",
    ),
    GravityModel(
        body="charon",
        model_name="NewHorizons-Brozovic-2015",
        max_degree=0,
        reference_radius_km=606.0,
        gm_km3_per_s2=105.88,
        precision_flag=PRECISION_LOW,
        source_key="brozovic_2015",
    ),

    # ---- Asteroids — DAWN-derived for Vesta + Ceres -------------------
    GravityModel(
        body="ceres",
        model_name="DAWN-Park-2020",
        max_degree=18,
        reference_radius_km=470.0,
        gm_km3_per_s2=62.62736,             # Park 2018; refined Park 2020
        J2=2.6499e-2,                       # Park 2018 (264.99e-4)
        full_coeff_archive="https://sbn.psi.edu/pds/resource/dawn/dwncgravL2.html",
        precision_flag=PRECISION_HIGH,
        source_key="park_2018_ceres",
    ),
    GravityModel(
        body="vesta",
        model_name="DAWN-Konopliv-2014",
        max_degree=20,
        reference_radius_km=265.0,
        gm_km3_per_s2=17.288245,
        J2=3.1779e-2,                       # Konopliv 2014
        full_coeff_archive="https://sbn.psi.edu/pds/resource/dawn/dwnvgrav.html",
        precision_flag=PRECISION_HIGH,
        source_key="konopliv_2014_vesta",
    ),
    # Pallas + Hygiea — HST + VLT-SPHERE adaptive optics, shape-derived
    GravityModel(
        body="pallas",
        model_name="VLT-Marsset-2020",
        max_degree=0,
        reference_radius_km=256.0,
        gm_km3_per_s2=14.3,                 # mass from satellite perturbations
        precision_flag=PRECISION_MEDIUM,
        source_key="marsset_2020_pallas",
    ),
    GravityModel(
        body="hygiea",
        model_name="VLT-Vernazza-2020",
        max_degree=0,
        reference_radius_km=215.0,
        gm_km3_per_s2=5.78,
        precision_flag=PRECISION_MEDIUM,
        source_key="vernazza_2020_hygiea",
    ),

    # ---- Small-body shape-model bodies (NOT in v0.16.0 BODIES) --------
    # These ship with body-name strings even though bodies.BODIES does
    # not contain them — see §17.4.2 roster-broader commitment.
    GravityModel(
        body="eros",
        model_name="NEAR-Miller-2002",
        max_degree=15,                      # robust to ~10
        reference_radius_km=16.0,
        gm_km3_per_s2=4.463e-4,
        full_coeff_archive="https://sbn.psi.edu/pds/resource/nearbrowse.html",
        precision_flag=PRECISION_HIGH,
        source_key="miller_2002_eros",
    ),
    GravityModel(
        body="bennu",
        model_name="OSIRIS-REx-Scheeres-2020",
        max_degree=16,
        reference_radius_km=0.245,
        gm_km3_per_s2=4.892e-9,
        full_coeff_archive="https://sbn.psi.edu/pds/resource/orex/",
        precision_flag=PRECISION_HIGH,
        source_key="scheeres_2020_bennu",
    ),
    GravityModel(
        body="itokawa",
        model_name="Hayabusa-Fujiwara-2006-shape",
        max_degree=0,                       # shape-derived, uniform-density assumption
        reference_radius_km=0.165,
        gm_km3_per_s2=2.36e-9,
        precision_flag=PRECISION_MEDIUM,
        source_key="fujiwara_2006_itokawa",
    ),
    GravityModel(
        body="ryugu",
        model_name="Hayabusa2-Watanabe-2019-shape",
        max_degree=0,
        reference_radius_km=0.448,
        gm_km3_per_s2=3.0e-8,
        precision_flag=PRECISION_MEDIUM,
        source_key="watanabe_2019_ryugu",
    ),
]


# ---------------------------------------------------------------------------
# Per-body topography models — §17.4.2 roster.
#
# DEMs only where a published, accessible product exists; bodies with
# only Voyager limb profiles or no surface topography ship with a
# "limb_profile_only" representation and PRECISION_LOW.
# ---------------------------------------------------------------------------

TOPOGRAPHY_MODELS: List[TopographyModel] = [

    # ---- Earth — SRTM + ETOPO -----------------------------------------
    TopographyModel(
        body="terra",
        model_name="SRTM-30+ETOPO2022",
        representation="global_grid",
        horizontal_resolution_km=0.030,     # SRTM 30 m at 60S-60N
        vertical_precision_m=6.0,
        coverage_fraction=1.0,              # ETOPO fills polar caps
        power_spectrum_slope=-2.0,          # canonical Earth red noise
        archive_url="https://www.ncei.noaa.gov/products/etopo-global-relief-model",
        precision_flag=PRECISION_HIGH,
        source_key="amante_2009_etopo",
    ),

    # ---- Moon — LOLA + SLDEM2015 --------------------------------------
    TopographyModel(
        body="luna",
        model_name="LOLA-SLDEM2015",
        representation="global_grid",
        horizontal_resolution_km=0.118,     # 118 m global; 60 m at equator
        vertical_precision_m=3.0,
        coverage_fraction=1.0,
        power_spectrum_slope=-2.5,          # Wieczorek 2013 spherical-harmonic decay
        archive_url="https://pgda.gsfc.nasa.gov/products/54",
        precision_flag=PRECISION_HIGH,
        source_key="barker_2016_sldem",
    ),

    # ---- Mars — MOLA MEGDR --------------------------------------------
    TopographyModel(
        body="mars",
        model_name="MOLA-MEGDR",
        representation="global_grid",
        horizontal_resolution_km=0.463,     # 463 m grid
        vertical_precision_m=1.0,
        coverage_fraction=1.0,
        power_spectrum_slope=-2.0,          # Aharonson 2001 power-law slope
        archive_url="https://pds-geosciences.wustl.edu/missions/mgs/megdr.html",
        precision_flag=PRECISION_HIGH,
        source_key="smith_2001_mola",
    ),

    # ---- Mercury — MLA + MDIS-stereo USGS -----------------------------
    TopographyModel(
        body="mercury",
        model_name="USGS-Becker-2016",
        representation="global_grid",
        horizontal_resolution_km=0.222,
        vertical_precision_m=30.0,
        coverage_fraction=1.0,              # USGS global mosaic; MLA NH only
        archive_url="https://astrogeology.usgs.gov/search/map/Mercury/Topography/MESSENGER/Mercury_Messenger_USGS_DEM_Global_665m_v2",
        precision_flag=PRECISION_HIGH,
        source_key="becker_2016_mercury",
    ),

    # ---- Venus — Magellan SAR (heterogeneous) -------------------------
    TopographyModel(
        body="venus",
        model_name="Magellan-GTDR",
        representation="partial_grid",
        horizontal_resolution_km=10.0,
        vertical_precision_m=100.0,
        coverage_fraction=0.98,             # SAR coverage with gaps
        archive_url="https://pds-geosciences.wustl.edu/missions/magellan/",
        precision_flag=PRECISION_MEDIUM,
        source_key="ford_1992_magellan",
    ),

    # ---- Titan — Cassini SARTopo --------------------------------------
    TopographyModel(
        body="titan",
        model_name="Cassini-SARTopo-Lorenz-2013",
        representation="partial_grid",
        horizontal_resolution_km=10.0,
        vertical_precision_m=150.0,
        coverage_fraction=0.20,             # ~5-23% depending on grid
        archive_url="https://pds-imaging.jpl.nasa.gov/data/cassini/cassini_orbiter/CORADR_xxxx/",
        precision_flag=PRECISION_MEDIUM,
        source_key="lorenz_2013_titan",
    ),

    # ---- Pluto + Charon — New Horizons stereo -------------------------
    TopographyModel(
        body="pluto",
        model_name="NewHorizons-Schenk-2018",
        representation="partial_grid",
        horizontal_resolution_km=0.300,
        vertical_precision_m=100.0,
        coverage_fraction=0.40,             # encounter hemisphere only
        archive_url="https://pds-imaging.jpl.nasa.gov/volumes/nh.html",
        precision_flag=PRECISION_MEDIUM,
        source_key="schenk_2018_pluto",
    ),
    TopographyModel(
        body="charon",
        model_name="NewHorizons-Schenk-2018",
        representation="partial_grid",
        horizontal_resolution_km=0.300,
        vertical_precision_m=100.0,
        coverage_fraction=0.40,
        archive_url="https://pds-imaging.jpl.nasa.gov/volumes/nh.html",
        precision_flag=PRECISION_MEDIUM,
        source_key="schenk_2018_pluto",
    ),

    # ---- Asteroids/Dawn — Vesta + Ceres -------------------------------
    TopographyModel(
        body="vesta",
        model_name="DAWN-Preusker-2014",
        representation="global_grid",
        horizontal_resolution_km=0.060,
        vertical_precision_m=10.0,
        coverage_fraction=1.0,
        archive_url="https://sbnarchive.psi.edu/pds3/dawn/fc/DWNVFC2_1B/",
        precision_flag=PRECISION_HIGH,
        source_key="preusker_2014_vesta",
    ),
    TopographyModel(
        body="ceres",
        model_name="DAWN-Roatsch-2016",
        representation="global_grid",
        horizontal_resolution_km=0.100,
        vertical_precision_m=10.0,
        coverage_fraction=1.0,
        archive_url="https://sbnarchive.psi.edu/pds3/dawn/fc/DWNCFC2_1B/",
        precision_flag=PRECISION_HIGH,
        source_key="roatsch_2016_ceres",
    ),

    # ---- Small-body shape polyhedra (Bennu / Eros / Itokawa / Ryugu) --
    TopographyModel(
        body="bennu",
        model_name="OSIRIS-REx-OLA-SPC",
        representation="shape_polyhedron",
        horizontal_resolution_km=0.0002,    # 20 cm
        vertical_precision_m=1.0,
        coverage_fraction=1.0,
        archive_url="https://asteroidmission.org/updated-bennu-shape-model-3d-files/",
        precision_flag=PRECISION_HIGH,
        source_key="barnouin_2019_bennu",
    ),
    TopographyModel(
        body="eros",
        model_name="NEAR-NLR-Miller-2002",
        representation="shape_polyhedron",
        horizontal_resolution_km=0.025,
        vertical_precision_m=5.0,
        coverage_fraction=1.0,
        archive_url="https://sbn.psi.edu/pds/resource/nearbrowse.html",
        precision_flag=PRECISION_HIGH,
        source_key="miller_2002_eros",
    ),
    TopographyModel(
        body="itokawa",
        model_name="Hayabusa-Gaskell-SPC",
        representation="shape_polyhedron",
        horizontal_resolution_km=0.001,
        vertical_precision_m=1.0,
        coverage_fraction=1.0,
        archive_url="https://sbn.psi.edu/pds/resource/itokawashape.html",
        precision_flag=PRECISION_HIGH,
        source_key="gaskell_2008_itokawa",
    ),
    TopographyModel(
        body="ryugu",
        model_name="Hayabusa2-SPC-Watanabe-2019",
        representation="shape_polyhedron",
        horizontal_resolution_km=0.0005,
        vertical_precision_m=1.0,
        coverage_fraction=1.0,
        archive_url="https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/README.html",
        precision_flag=PRECISION_HIGH,
        source_key="watanabe_2019_ryugu",
    ),

    # ---- Galilean moons — Voyager + Galileo limb profiles -------------
    TopographyModel(
        body="io",
        model_name="Voyager-Galileo-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=2.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.30,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1998_galileans",
    ),
    TopographyModel(
        body="europa",
        model_name="Galileo-Nimmo-2003-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=1.0,
        vertical_precision_m=200.0,
        coverage_fraction=0.30,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="nimmo_2003_europa",
    ),
    TopographyModel(
        body="ganymede",
        model_name="Voyager-Galileo-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=1.0,
        vertical_precision_m=500.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1998_galileans",
    ),
    TopographyModel(
        body="callisto",
        model_name="Voyager-Galileo-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1998_galileans",
    ),

    # ---- Saturnian classical moons — Cassini ISS shape models ---------
    TopographyModel(
        body="mimas",
        model_name="Cassini-Thomas-2010-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="thomas_2010_saturnian_smalls",
    ),
    TopographyModel(
        body="enceladus",
        model_name="Cassini-Thomas-2016-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=0.5,
        vertical_precision_m=200.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="thomas_2016_enceladus",
    ),
    TopographyModel(
        body="tethys",
        model_name="Cassini-Thomas-2010-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="thomas_2010_saturnian_smalls",
    ),
    TopographyModel(
        body="dione",
        model_name="Cassini-Thomas-2010-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="thomas_2010_saturnian_smalls",
    ),
    TopographyModel(
        body="rhea",
        model_name="Cassini-Thomas-2010-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="thomas_2010_saturnian_smalls",
    ),
    TopographyModel(
        body="iapetus",
        model_name="Cassini-Thomas-2010-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="thomas_2010_saturnian_smalls",
    ),
    TopographyModel(
        body="phoebe",
        model_name="Cassini-Thomas-2010-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=2.0,
        vertical_precision_m=500.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="thomas_2010_saturnian_smalls",
    ),

    # ---- Phobos — MEX HRSC + Viking shape -----------------------------
    TopographyModel(
        body="phobos",
        model_name="MEX-Willner-2014-shape",
        representation="shape_polyhedron",
        horizontal_resolution_km=0.1,
        vertical_precision_m=20.0,
        coverage_fraction=1.0,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="willner_2014_phobos",
    ),

    # ---- Triton — Voyager 2 stereo limb -------------------------------
    TopographyModel(
        body="triton",
        model_name="Voyager2-Schenk-2007",
        representation="limb_profile_only",
        horizontal_resolution_km=5.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="schenk_2007_triton",
    ),

    # ---- Uranian moons — Voyager 2 -----------------------------------
    TopographyModel(
        body="miranda",
        model_name="Voyager2-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=5.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1988_uranian",
    ),
    TopographyModel(
        body="ariel",
        model_name="Voyager2-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=5.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1988_uranian",
    ),
    TopographyModel(
        body="umbriel",
        model_name="Voyager2-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=5.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.30,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1988_uranian",
    ),
    TopographyModel(
        body="titania",
        model_name="Voyager2-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=5.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1988_uranian",
    ),
    TopographyModel(
        body="oberon",
        model_name="Voyager2-limb",
        representation="limb_profile_only",
        horizontal_resolution_km=5.0,
        vertical_precision_m=1000.0,
        coverage_fraction=0.40,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="thomas_1988_uranian",
    ),
]


# ---------------------------------------------------------------------------
# Per-body interior models — §17.4.2 roster.
#
# Ordered inner → outer. Total mass is the SI-kg ground truth from
# bodies.BODIES.mass_earth × 5.9722e24, with model-specific exceptions
# noted inline. Layers are coarse-grained where the literature offers
# only a 2-3 layer fit (e.g. Voyager-bound icy moons).
# ---------------------------------------------------------------------------

INTERIOR_MODELS: List[InteriorModel] = [

    # ---- Earth — PREM (Dziewonski & Anderson 1981) --------------------
    InteriorModel(
        body="terra",
        model_name="PREM",
        total_radius_km=6_371.0,
        total_mass_kg=5.9722e24,
        layers=(
            InteriorLayer("inner_core", 0.0, 1_221.5, 12_900.0, "Fe + 5% Ni (solid)"),
            InteriorLayer("outer_core", 1_221.5, 3_480.0, 11_000.0, "Fe + 10% light elements (liquid)"),
            InteriorLayer("lower_mantle", 3_480.0, 5_701.0, 4_900.0, "Mg-perovskite + ferropericlase"),
            InteriorLayer("transition_zone", 5_701.0, 5_971.0, 3_900.0, "ringwoodite + wadsleyite"),
            InteriorLayer("upper_mantle", 5_971.0, 6_346.6, 3_400.0, "olivine + pyroxene"),
            InteriorLayer("crust", 6_346.6, 6_371.0, 2_800.0, "basalt/granite"),
        ),
        normalised_moi=0.3307,              # Earth canonical
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="dziewonski_anderson_1981",
    ),

    # ---- Moon — GRAIL + Apollo composite (Wieczorek 2013) -------------
    InteriorModel(
        body="luna",
        model_name="GRAIL-Apollo-Wieczorek-2013",
        total_radius_km=1_737.4,
        total_mass_kg=7.342e22,
        layers=(
            InteriorLayer("inner_core", 0.0, 240.0, 7_500.0, "Fe (solid)"),
            InteriorLayer("outer_core", 240.0, 330.0, 5_200.0, "Fe-S (liquid)"),
            InteriorLayer("partial_melt", 330.0, 480.0, 3_400.0, "partially molten silicate"),
            InteriorLayer("mantle", 480.0, 1_697.4, 3_300.0, "olivine + pyroxene"),
            InteriorLayer("crust", 1_697.4, 1_737.4, 2_550.0, "anorthositic feldspar (12% porosity)"),
        ),
        normalised_moi=0.3931,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="wieczorek_2013_moon",
    ),

    # ---- Mars — InSight composite (Stähler 2021 + Khan 2023) ----------
    InteriorModel(
        body="mars",
        model_name="InSight-Khan-2023",
        total_radius_km=3_389.5,
        total_mass_kg=6.4171e23,
        layers=(
            InteriorLayer("liquid_core", 0.0, 1_830.0, 6_120.0, "Fe-S-O liquid"),
            InteriorLayer("molten_silicate", 1_830.0, 1_900.0, 4_050.0, "molten silicate (Khan 2023)"),
            InteriorLayer("lower_mantle", 1_900.0, 2_700.0, 3_750.0, "ringwoodite-bearing"),
            InteriorLayer("upper_mantle", 2_700.0, 3_352.0, 3_500.0, "olivine + pyroxene"),
            InteriorLayer("crust", 3_352.0, 3_389.5, 2_900.0, "basalt"),
        ),
        normalised_moi=0.3645,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="khan_2023_mars",
    ),

    # ---- Mercury — Hauck 2013 (MESSENGER + radar libration) -----------
    InteriorModel(
        body="mercury",
        model_name="Hauck-2013",
        total_radius_km=2_439.7,
        total_mass_kg=3.3011e23,
        layers=(
            InteriorLayer("inner_core", 0.0, 1_000.0, 8_100.0, "Fe (possibly solid)"),
            InteriorLayer("outer_core", 1_000.0, 2_020.0, 6_980.0, "Fe-S (liquid)"),
            InteriorLayer("FeS_layer", 2_020.0, 2_080.0, 5_500.0, "FeS solid"),
            InteriorLayer("mantle", 2_080.0, 2_410.0, 3_380.0, "silicate"),
            InteriorLayer("crust", 2_410.0, 2_439.7, 2_900.0, "silicate"),
        ),
        normalised_moi=0.346,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="hauck_2013_mercury",
    ),

    # ---- Venus — poorly constrained (Margot 2021 spin update) ---------
    InteriorModel(
        body="venus",
        model_name="Magellan-Margot-2021",
        total_radius_km=6_051.8,
        total_mass_kg=4.8675e24,
        layers=(
            InteriorLayer("core", 0.0, 3_200.0, 11_000.0, "Fe-Ni (state unknown — possibly liquid)"),
            InteriorLayer("mantle", 3_200.0, 6_001.8, 4_500.0, "silicate"),
            InteriorLayer("crust", 6_001.8, 6_051.8, 2_900.0, "basalt (single-plate)"),
        ),
        normalised_moi=0.337,               # Margot 2021 spin/precession
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_LOW,        # no seismic data
        source_key="margot_2021_venus",
    ),

    # ---- Jupiter — Wahl 2017 + Militzer 2022 dilute core --------------
    InteriorModel(
        body="jupiter",
        model_name="Juno-Militzer-2022-dilute-core",
        total_radius_km=69_911.0,
        total_mass_kg=1.8982e27,
        layers=(
            InteriorLayer("dilute_core", 0.0, 42_000.0, 4_500.0, "H/He + ~17 Earth-mass heavy elements (dilute)"),
            InteriorLayer("metallic_H_envelope", 42_000.0, 56_000.0, 1_500.0, "metallic hydrogen + helium"),
            InteriorLayer("molecular_H_envelope", 56_000.0, 69_911.0, 350.0, "molecular H2 + He"),
        ),
        normalised_moi=0.2756,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,    # multiple competing model families
        source_key="militzer_2022_jupiter",
    ),

    # ---- Saturn — Mankovich & Fuller 2021 diffuse core ----------------
    InteriorModel(
        body="saturn",
        model_name="Cassini-Mankovich-2021-diffuse-core",
        total_radius_km=58_232.0,
        total_mass_kg=5.6834e26,
        layers=(
            InteriorLayer("diffuse_core", 0.0, 35_000.0, 5_000.0, "H/He + 17 Earth-mass ice/rock (stably stratified, ~60% R)"),
            InteriorLayer("metallic_H_envelope", 35_000.0, 47_000.0, 1_200.0, "metallic hydrogen"),
            InteriorLayer("molecular_H_envelope", 47_000.0, 58_232.0, 400.0, "molecular H2 + He"),
        ),
        normalised_moi=0.21,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="mankovich_fuller_2021",
    ),

    # ---- Uranus — Helled 2020 (Voyager-bound layered) -----------------
    InteriorModel(
        body="uranus",
        model_name="Helled-2020-layered",
        total_radius_km=25_362.0,
        total_mass_kg=8.6810e25,
        layers=(
            InteriorLayer("rocky_core", 0.0, 5_000.0, 9_000.0, "silicate + Fe (small core)"),
            InteriorLayer("ices_envelope", 5_000.0, 18_000.0, 2_500.0, "H2O + NH3 + CH4 ('ices')"),
            InteriorLayer("H_He_envelope", 18_000.0, 25_362.0, 700.0, "H2 + He"),
        ),
        normalised_moi=0.23,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="helled_2020_ice_giants",
    ),

    # ---- Neptune — Helled 2020 ---------------------------------------
    InteriorModel(
        body="neptune",
        model_name="Helled-2020-layered",
        total_radius_km=24_622.0,
        total_mass_kg=1.02413e26,
        layers=(
            InteriorLayer("rocky_core", 0.0, 5_000.0, 9_500.0, "silicate + Fe"),
            InteriorLayer("ices_envelope", 5_000.0, 18_000.0, 2_700.0, "H2O + NH3 + CH4"),
            InteriorLayer("H_He_envelope", 18_000.0, 24_622.0, 800.0, "H2 + He"),
        ),
        normalised_moi=0.23,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="helled_2020_ice_giants",
    ),

    # ---- Galilean moons — Anderson series ----------------------------
    InteriorModel(
        body="io",
        model_name="Galileo-Anderson-2001",
        total_radius_km=1_821.6,
        total_mass_kg=8.9319e22,
        layers=(
            InteriorLayer("Fe_core", 0.0, 750.0, 5_150.0, "Fe + Fe-S (partially molten)"),
            InteriorLayer("partial_melt_asthenosphere", 750.0, 1_750.0, 3_400.0, "partially molten silicate (tidal heating)"),
            InteriorLayer("crust", 1_750.0, 1_821.6, 3_000.0, "basalt + sulfur"),
        ),
        normalised_moi=0.378,
        has_subsurface_ocean=False,         # silicate magma ocean, not water
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="anderson_2001_io",
    ),
    InteriorModel(
        body="europa",
        model_name="Galileo-Anderson-1998a",
        total_radius_km=1_560.8,
        total_mass_kg=4.7998e22,
        layers=(
            InteriorLayer("Fe_core", 0.0, 600.0, 5_500.0, "Fe + Fe-S"),
            InteriorLayer("silicate_mantle", 600.0, 1_460.0, 3_300.0, "olivine + pyroxene"),
            InteriorLayer("subsurface_ocean", 1_460.0, 1_540.0, 1_020.0, "liquid H2O (salty)"),
            InteriorLayer("ice_shell", 1_540.0, 1_560.8, 920.0, "H2O ice"),
        ),
        normalised_moi=0.346,
        has_subsurface_ocean=True,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="anderson_1998_europa",
    ),
    InteriorModel(
        body="ganymede",
        model_name="Galileo-Anderson-1996",
        total_radius_km=2_634.1,
        total_mass_kg=1.4819e23,
        layers=(
            InteriorLayer("Fe_core", 0.0, 700.0, 5_500.0, "Fe + Fe-S (molten — sustains dipole)"),
            InteriorLayer("silicate_mantle", 700.0, 1_900.0, 3_500.0, "olivine + pyroxene"),
            InteriorLayer("HP_ice_layer", 1_900.0, 2_500.0, 1_300.0, "high-pressure ice (ice III/V/VI)"),
            InteriorLayer("subsurface_ocean", 2_500.0, 2_600.0, 1_050.0, "liquid H2O"),
            InteriorLayer("ice_shell", 2_600.0, 2_634.1, 920.0, "H2O ice Ih"),
        ),
        normalised_moi=0.3115,
        has_subsurface_ocean=True,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="anderson_1996_ganymede",
    ),
    InteriorModel(
        body="callisto",
        model_name="Galileo-Anderson-2001b",
        total_radius_km=2_410.3,
        total_mass_kg=1.0759e23,
        layers=(
            InteriorLayer("rock_ice_mixture", 0.0, 2_000.0, 2_300.0, "undifferentiated rock + ice"),
            InteriorLayer("subsurface_ocean", 2_000.0, 2_100.0, 1_050.0, "liquid H2O (putative)"),
            InteriorLayer("ice_shell", 2_100.0, 2_410.3, 920.0, "H2O ice"),
        ),
        normalised_moi=0.3549,              # high — incomplete differentiation
        has_subsurface_ocean=True,          # induced field response (Khurana 1998)
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="anderson_2001_callisto",
    ),

    # ---- Saturnian moons — Cassini-derived ---------------------------
    InteriorModel(
        body="enceladus",
        model_name="Cassini-Iess-2014",
        total_radius_km=252.1,
        total_mass_kg=1.08e20,
        layers=(
            InteriorLayer("rocky_core", 0.0, 190.0, 2_400.0, "hydrated silicate (porous)"),
            InteriorLayer("subsurface_ocean", 190.0, 230.0, 1_020.0, "global liquid H2O ocean"),
            InteriorLayer("ice_shell", 230.0, 252.1, 920.0, "H2O ice (thinner at south pole)"),
        ),
        normalised_moi=0.335,
        has_subsurface_ocean=True,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="iess_2014_enceladus",
    ),
    InteriorModel(
        body="titan",
        model_name="Cassini-Hemingway-2013",
        total_radius_km=2_574.7,
        total_mass_kg=1.3452e23,
        layers=(
            InteriorLayer("rocky_core", 0.0, 2_100.0, 2_600.0, "hydrated silicate"),
            InteriorLayer("HP_ice_layer", 2_100.0, 2_400.0, 1_300.0, "high-pressure ice"),
            InteriorLayer("subsurface_ocean", 2_400.0, 2_500.0, 1_100.0, "liquid H2O + NH3"),
            InteriorLayer("ice_shell", 2_500.0, 2_574.7, 920.0, "H2O ice Ih"),
        ),
        normalised_moi=0.3414,
        has_subsurface_ocean=True,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="hemingway_2013_titan",
    ),
    InteriorModel(
        body="mimas",
        model_name="Cassini-Tajeddine-2014",
        total_radius_km=198.2,
        total_mass_kg=3.7493e19,
        layers=(
            InteriorLayer("rocky_core", 0.0, 100.0, 2_400.0, "rocky (possibly elongated)"),
            InteriorLayer("ice_mantle", 100.0, 198.2, 950.0, "H2O ice"),
        ),
        normalised_moi=0.39,
        has_subsurface_ocean=False,         # libration suggests possible — disputed
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="tajeddine_2014_mimas",
    ),
    InteriorModel(
        body="rhea",
        model_name="Cassini-Iess-2007",
        total_radius_km=763.5,
        total_mass_kg=2.3065e21,
        layers=(
            InteriorLayer("rock_ice_mixture", 0.0, 763.5, 1_236.0, "undifferentiated rock + ice"),
        ),
        normalised_moi=0.394,               # near-uniform; not differentiated
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="iess_2007_rhea",
    ),
    InteriorModel(
        body="dione",
        model_name="Cassini-Hemingway-2016",
        total_radius_km=561.4,
        total_mass_kg=1.0954e21,
        layers=(
            InteriorLayer("rocky_core", 0.0, 400.0, 2_400.0, "rocky"),
            InteriorLayer("subsurface_ocean", 400.0, 460.0, 1_050.0, "liquid H2O (inferred)"),
            InteriorLayer("ice_shell", 460.0, 561.4, 920.0, "H2O ice"),
        ),
        normalised_moi=0.36,
        has_subsurface_ocean=True,          # Hemingway 2016 inference
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="hemingway_2016_dione",
    ),
    InteriorModel(
        body="iapetus",
        model_name="Cassini-Castillo-Rogez-2007",
        total_radius_km=734.3,
        total_mass_kg=1.806e21,
        layers=(
            InteriorLayer("rock_ice_mixture", 0.0, 734.3, 1_088.0, "undifferentiated; fossil rotation bulge"),
        ),
        normalised_moi=0.40,                # near-uniform (fossil bulge from fast early rotation)
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_MEDIUM,
        source_key="castillo_rogez_2007",
    ),

    # ---- Triton — Voyager-only (McKinnon 2014 composite) -------------
    InteriorModel(
        body="triton",
        model_name="Voyager2-McKinnon-2014",
        total_radius_km=1_353.4,
        total_mass_kg=2.139e22,
        layers=(
            InteriorLayer("rocky_core", 0.0, 1_000.0, 4_000.0, "silicate + Fe"),
            InteriorLayer("subsurface_ocean", 1_000.0, 1_100.0, 1_050.0, "liquid H2O + NH3 (inferred)"),
            InteriorLayer("ice_shell", 1_100.0, 1_353.4, 950.0, "H2O ice + N2 frost cap"),
        ),
        normalised_moi=None,                 # not measured
        has_subsurface_ocean=True,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="mckinnon_2014_triton",
    ),

    # ---- Pluto + Charon — McKinnon 2017 ------------------------------
    InteriorModel(
        body="pluto",
        model_name="NewHorizons-McKinnon-2017",
        total_radius_km=1_188.3,
        total_mass_kg=1.303e22,
        layers=(
            InteriorLayer("rocky_core", 0.0, 850.0, 3_500.0, "hydrated silicate"),
            InteriorLayer("subsurface_ocean", 850.0, 1_000.0, 1_050.0, "liquid H2O (inferred)"),
            InteriorLayer("ice_shell", 1_000.0, 1_188.3, 950.0, "H2O ice + N2/CO/CH4 frost"),
        ),
        normalised_moi=None,
        has_subsurface_ocean=True,
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="mckinnon_2017_pluto",
    ),
    InteriorModel(
        body="charon",
        model_name="NewHorizons-McKinnon-2017",
        total_radius_km=606.0,
        total_mass_kg=1.586e21,
        layers=(
            InteriorLayer("rocky_core", 0.0, 376.0, 3_000.0, "silicate"),
            InteriorLayer("ice_mantle", 376.0, 606.0, 1_400.0, "H2O ice (refrozen ocean candidate)"),
        ),
        normalised_moi=None,
        has_subsurface_ocean=False,         # likely refrozen by present epoch
        archive_url=None,
        precision_flag=PRECISION_LOW,
        source_key="mckinnon_2017_pluto",
    ),

    # ---- Asteroids/dwarf planets — DAWN-derived for Vesta + Ceres -----
    InteriorModel(
        body="vesta",
        model_name="DAWN-Russell-2012",
        total_radius_km=262.7,              # volumetric mean
        total_mass_kg=2.5908e20,
        layers=(
            InteriorLayer("Fe_core", 0.0, 113.0, 7_400.0, "Fe + Fe-S (differentiated; HED meteorite parent body)"),
            InteriorLayer("silicate_mantle", 113.0, 250.0, 3_200.0, "olivine"),
            InteriorLayer("basaltic_crust", 250.0, 262.7, 2_900.0, "basalt (HED-source)"),
        ),
        normalised_moi=0.36,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="russell_2012_vesta",
    ),
    InteriorModel(
        body="ceres",
        model_name="DAWN-Park-2016",
        total_radius_km=469.7,
        total_mass_kg=9.3835e20,
        layers=(
            InteriorLayer("rocky_core", 0.0, 280.0, 2_460.0, "hydrated silicate (only partially differentiated)"),
            InteriorLayer("muddy_mantle", 280.0, 440.0, 1_680.0, "ice + clay + brine"),
            InteriorLayer("ice_crust", 440.0, 469.7, 1_280.0, "ice + salt + carbonate"),
        ),
        normalised_moi=0.37,
        has_subsurface_ocean=True,          # localised brine pockets (Cerealia Facula)
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="park_2016_ceres",
    ),

    # ---- Bennu / Ryugu — rubble-pile rubble-pile ----------------------
    InteriorModel(
        body="bennu",
        model_name="OSIRIS-REx-Scheeres-2020",
        total_radius_km=0.245,
        total_mass_kg=7.329e10,
        layers=(
            InteriorLayer("under_dense_centre", 0.0, 0.150, 1_100.0, "loose rubble (~50% porosity)"),
            InteriorLayer("denser_outer", 0.150, 0.245, 1_400.0, "denser rubble + boulders"),
        ),
        normalised_moi=None,                 # heterogeneous; not a meaningful single number
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="scheeres_2020_bennu",
    ),
    InteriorModel(
        body="ryugu",
        model_name="Hayabusa2-Watanabe-2019",
        total_radius_km=0.448,
        total_mass_kg=4.5e11,
        layers=(
            InteriorLayer("rubble_pile", 0.0, 0.448, 1_190.0, "rubble (~50-60% porosity); CI/CM-like composition"),
        ),
        normalised_moi=None,
        has_subsurface_ocean=False,
        archive_url=None,
        precision_flag=PRECISION_HIGH,
        source_key="watanabe_2019_ryugu",
    ),
]


# ---------------------------------------------------------------------------
# Citations — every entry above carries a source_key pointing here.
# ---------------------------------------------------------------------------
SOURCES: Dict[str, str] = {

    "amante_2009_etopo": (
        "Amante, C., & Eakins, B. W. (2009). ETOPO1 1 Arc-Minute Global "
        "Relief Model: Procedures, Data Sources and Analysis. NOAA Tech. "
        "Memo. NESDIS NGDC-24. (Updated to ETOPO 2022.) "
        "https://www.ncei.noaa.gov/products/etopo-global-relief-model"
    ),

    "anderson_1996_ganymede": (
        "Anderson, J. D., Lau, E. L., Sjogren, W. L., Schubert, G., & "
        "Moore, W. B. (1996). Gravitational constraints on the internal "
        "structure of Ganymede. Nature, 384, 541-543. "
        "https://doi.org/10.1038/384541a0"
    ),

    "anderson_1998_europa": (
        "Anderson, J. D., Schubert, G., Jacobson, R. A., Lau, E. L., "
        "Moore, W. B., & Sjogren, W. L. (1998). Europa's differentiated "
        "internal structure: inferences from four Galileo encounters. "
        "Science, 281, 2019-2022. "
        "https://doi.org/10.1126/science.281.5385.2019"
    ),

    "anderson_2001_io": (
        "Anderson, J. D., Jacobson, R. A., Lau, E. L., Moore, W. B., & "
        "Schubert, G. (2001). Io's gravity field and interior structure. "
        "J. Geophys. Res. Planets, 106, 32963-32969. "
        "https://doi.org/10.1029/2000JE001367"
    ),

    "anderson_2001_callisto": (
        "Anderson, J. D., Jacobson, R. A., McElrath, T. P., Moore, W. B., "
        "Schubert, G., & Thomas, P. C. (2001). Shape, mean radius, gravity "
        "field, and interior structure of Callisto. Icarus, 153, 157-161. "
        "https://doi.org/10.1006/icar.2001.6664"
    ),

    "anderson_2005_amalthea": (
        "Anderson, J. D., Johnson, T. V., Schubert, G., et al. (2005). "
        "Amalthea's density is less than that of water. Science, 308, "
        "1291-1293. https://doi.org/10.1126/science.1110422"
    ),

    "barker_2016_sldem": (
        "Barker, M. K., Mazarico, E., Neumann, G. A., Zuber, M. T., "
        "Haruyama, J., & Smith, D. E. (2016). A new lunar digital elevation "
        "model from the Lunar Orbiter Laser Altimeter and SELENE Terrain "
        "Camera. Icarus, 273, 346-355. "
        "https://doi.org/10.1016/j.icarus.2015.07.039"
    ),

    "barnouin_2019_bennu": (
        "Barnouin, O. S., Daly, M. G., Palmer, E. E., et al. (2019). "
        "Shape of (101955) Bennu indicative of a rubble pile with "
        "internal stiffness. Nature Geoscience, 12, 247-252. "
        "https://doi.org/10.1038/s41561-019-0330-x"
    ),

    "becker_2016_mercury": (
        "Becker, K. J., Robinson, M. S., Becker, T. L., et al. (2016). "
        "First Global Digital Elevation Model of Mercury. LPSC 47, #2959. "
        "https://www.hou.usra.edu/meetings/lpsc2016/pdf/2959.pdf"
    ),

    "brozovic_2015": (
        "Brozović, M., Showalter, M. R., Jacobson, R. A., & Buie, M. W. "
        "(2015). The orbits and masses of satellites of Pluto. Icarus, "
        "246, 317-329. https://doi.org/10.1016/j.icarus.2014.03.015"
    ),

    "castillo_rogez_2007": (
        "Castillo-Rogez, J. C., Matson, D. L., Sotin, C., et al. (2007). "
        "Iapetus' geophysics: Rotation rate, shape, and equatorial ridge. "
        "Icarus, 190, 179-202. "
        "https://doi.org/10.1016/j.icarus.2007.02.018"
    ),

    "dziewonski_anderson_1981": (
        "Dziewonski, A. M., & Anderson, D. L. (1981). Preliminary Reference "
        "Earth Model. Phys. Earth Planet. Inter., 25, 297-356. "
        "https://doi.org/10.1016/0031-9201(81)90046-7"
    ),

    "emelyanov_2005": (
        "Emelyanov, N. V. (2005). The mass of Himalia from the perturbations "
        "on other satellites. Astronomy & Astrophysics, 438, L33-L36. "
        "https://doi.org/10.1051/0004-6361:200500142"
    ),

    "ford_1992_magellan": (
        "Ford, P. G., & Pettengill, G. H. (1992). Venus topography and "
        "kilometer-scale slopes. J. Geophys. Res., 97, 13103-13114. "
        "https://doi.org/10.1029/92JE01085"
    ),

    "fujiwara_2006_itokawa": (
        "Fujiwara, A., Kawaguchi, J., Yeomans, D. K., et al. (2006). "
        "The rubble-pile asteroid Itokawa as observed by Hayabusa. "
        "Science, 312, 1330-1334. "
        "https://doi.org/10.1126/science.1125841"
    ),

    "gaskell_2008_itokawa": (
        "Gaskell, R. W., Barnouin-Jha, O. S., Scheeres, D. J., et al. "
        "(2008). Characterizing and navigating small bodies with imaging "
        "data. Meteoritics & Planet. Sci., 43, 1049-1061. "
        "https://doi.org/10.1111/j.1945-5100.2008.tb00692.x"
    ),

    "goossens_2020": (
        "Goossens, S., Sabaka, T. J., Genova, A., Mazarico, E., "
        "Nicholas, J. B., & Neumann, G. A. (2020). High-Resolution Gravity "
        "Field Models from GRAIL Data and Implications for Models of the "
        "Density Structure of the Moon's Crust. JGR Planets, 125, "
        "e2019JE006086. https://doi.org/10.1029/2019JE006086"
    ),

    "hauck_2013_mercury": (
        "Hauck, S. A. II, Margot, J.-L., Solomon, S. C., et al. (2013). "
        "The curious case of Mercury's internal structure. JGR Planets, "
        "118, 1204-1220. https://doi.org/10.1002/jgre.20091"
    ),

    "helled_2020_ice_giants": (
        "Helled, R., Nettelmann, N., & Guillot, T. (2020). Uranus and "
        "Neptune: Origin, Evolution and Internal Structure. Space Science "
        "Reviews, 216, 38. https://doi.org/10.1007/s11214-020-00660-3"
    ),

    "hemingway_2013_titan": (
        "Hemingway, D., Nimmo, F., Zebker, H., & Iess, L. (2013). A "
        "rigid and weathered ice shell on Titan. Nature, 500, 550-552. "
        "https://doi.org/10.1038/nature12400"
    ),

    "hemingway_2016_dione": (
        "Hemingway, D. J., Iess, L., Tajeddine, R., & Tobie, G. (2016). "
        "The interior of Enceladus and Dione. AGU Fall Meeting, P21B-2125. "
        "(See also: Beuthe, M., Rivoldini, A., & Trinh, A. (2016). "
        "Enceladus's and Dione's floating ice shells supported by "
        "minimum stress isostasy. GRL, 43, 10088-10096. "
        "https://doi.org/10.1002/2016GL070650)"
    ),

    "iau_2015_nominal": (
        "Mamajek, E. E., Prsa, A., Torres, G., et al. (2015). IAU 2015 "
        "Resolution B3 on Recommended Nominal Conversion Constants for "
        "Selected Solar and Planetary Properties. arXiv:1510.07674. "
        "https://www.iau.org/static/resolutions/IAU2015_English.pdf"
    ),

    "iess_2007_rhea": (
        "Iess, L., Rappaport, N. J., Tortora, P., et al. (2007). Gravity "
        "field and interior of Rhea from Cassini data analysis. Icarus, "
        "190, 585-593. https://doi.org/10.1016/j.icarus.2007.03.027"
    ),

    "iess_2010_titan": (
        "Iess, L., Rappaport, N. J., Jacobson, R. A., et al. (2010). "
        "Gravity field, shape, and moment of inertia of Titan. Science, "
        "327, 1367-1369. https://doi.org/10.1126/science.1182583"
    ),

    "iess_2014_enceladus": (
        "Iess, L., Stevenson, D. J., Parisi, M., et al. (2014). The "
        "Gravity Field and Interior Structure of Enceladus. Science, 344, "
        "78-80. https://doi.org/10.1126/science.1250551"
    ),

    "iess_2018_jupiter": (
        "Iess, L., Folkner, W. M., Durante, D., et al. (2018). Measurement "
        "of Jupiter's asymmetric gravity field. Nature, 555, 220-222. "
        "https://doi.org/10.1038/nature25776 "
        "(Updates: Durante, D., et al. (2020). Jupiter's Gravity Field "
        "Halfway Through the Juno Mission. GRL, 47, e2019GL086572. "
        "https://doi.org/10.1029/2019GL086572)"
    ),

    "iess_2019_saturn": (
        "Iess, L., Militzer, B., Kaspi, Y., et al. (2019). Measurement "
        "and implications of Saturn's gravity field and ring mass. "
        "Science, 364, eaat2965. "
        "https://doi.org/10.1126/science.aat2965"
    ),

    "jacobson_2006_saturn": (
        "Jacobson, R. A., Antreasian, P. G., Bordi, J. J., et al. (2006). "
        "The gravity field of the Saturnian system from satellite "
        "observations and spacecraft tracking data. Astronomical Journal, "
        "132, 2520-2526. https://doi.org/10.1086/508812"
    ),

    "jacobson_2009_neptune": (
        "Jacobson, R. A. (2009). The Orbits of the Neptunian Satellites "
        "and the Orientation of the Pole of Neptune. Astronomical Journal, "
        "137, 4322-4329. https://doi.org/10.1088/0004-6256/137/5/4322"
    ),

    "jacobson_2010_mars": (
        "Jacobson, R. A. (2010). The orbits and masses of the Martian "
        "satellites and the libration of Phobos. Astronomical Journal, "
        "139, 668-679. https://doi.org/10.1088/0004-6256/139/2/668"
    ),

    "jacobson_2014_uranus": (
        "Jacobson, R. A. (2014). The orbits of the Uranian satellites and "
        "rings, the gravity field of the Uranian system, and the orientation "
        "of the pole of Uranus. Astronomical Journal, 148, 76. "
        "https://doi.org/10.1088/0004-6256/148/5/76"
    ),

    "jpl_ssd_jovian_satellites": (
        "JPL Solar System Dynamics — Planetary Satellite Physical "
        "Parameters. https://ssd.jpl.nasa.gov/sats/phys_par/ "
        "(Inner Jovian regulars: nominal masses derived from shape + "
        "assumed density; no spacecraft mass determination.)"
    ),

    "khan_2023_mars": (
        "Khan, A., Huang, D., Durán, C., Sossi, P. A., Giardini, D., & "
        "Murakami, M. (2023). Geophysical evidence for an enriched "
        "molten silicate layer above Mars's core. Nature, 622, 718-723. "
        "https://doi.org/10.1038/s41586-023-06601-8 "
        "(Composite with: Stähler, S. C., et al. (2021). Seismic detection "
        "of the martian core. Science, 373, 443-448. "
        "https://doi.org/10.1126/science.abi7730)"
    ),

    "konopliv_1999": (
        "Konopliv, A. S., Banerdt, W. B., & Sjogren, W. L. (1999). "
        "Venus Gravity: 180th Degree and Order Model. Icarus, 139, 3-18. "
        "https://doi.org/10.1006/icar.1999.6086"
    ),

    "konopliv_2014_vesta": (
        "Konopliv, A. S., Asmar, S. W., Park, R. S., et al. (2014). "
        "The Vesta gravity field, spin pole and rotation period, "
        "landmark positions, and ephemeris from the Dawn tracking and "
        "optical data. Icarus, 240, 103-117. "
        "https://doi.org/10.1016/j.icarus.2013.09.005"
    ),

    "konopliv_2016": (
        "Konopliv, A. S., Park, R. S., & Folkner, W. M. (2016). "
        "An improved JPL Mars gravity field and orientation from Mars "
        "orbiter and lander tracking data. Icarus, 274, 253-260. "
        "https://doi.org/10.1016/j.icarus.2016.02.052"
    ),

    "lorenz_2013_titan": (
        "Lorenz, R. D., Stiles, B. W., Aharonson, O., et al. (2013). "
        "A global topographic map of Titan. Icarus, 225, 367-377. "
        "https://doi.org/10.1016/j.icarus.2013.04.002"
    ),

    "mankovich_fuller_2021": (
        "Mankovich, C. R., & Fuller, J. (2021). A diffuse core in Saturn "
        "revealed by ring seismology. Nature Astronomy, 5, 1103-1109. "
        "https://doi.org/10.1038/s41550-021-01448-3"
    ),

    "margot_2021_venus": (
        "Margot, J.-L., Campbell, D. B., Giorgini, J. D., et al. (2021). "
        "Spin state and moment of inertia of Venus. Nature Astronomy, 5, "
        "676-683. https://doi.org/10.1038/s41550-021-01339-7"
    ),

    "marsset_2020_pallas": (
        "Marsset, M., Brož, M., Vernazza, P., et al. (2020). The violent "
        "collisional history of aqueously evolved (2) Pallas. Nature "
        "Astronomy, 4, 569-576. "
        "https://doi.org/10.1038/s41550-019-1007-5"
    ),

    "mazarico_2014": (
        "Mazarico, E., Genova, A., Goossens, S., et al. (2014). The "
        "gravity field, orientation, and ephemeris of Mercury from "
        "MESSENGER observations after three years in orbit. JGR Planets, "
        "119, 2417-2436. https://doi.org/10.1002/2014JE004675 "
        "(Updates: Genova, A., et al. (2019). Geodetic Evidence That "
        "Mercury Has A Solid Inner Core. GRL, 46, 3625-3633. "
        "https://doi.org/10.1029/2018GL081135)"
    ),

    "mckinnon_2014_triton": (
        "McKinnon, W. B., & Kirk, R. L. (2014). Triton. In Encyclopedia "
        "of the Solar System (3rd ed.), 861-881. Elsevier. "
        "https://doi.org/10.1016/B978-0-12-415845-0.00040-2"
    ),

    "mckinnon_2017_pluto": (
        "McKinnon, W. B., Stern, S. A., Weaver, H. A., et al. (2017). "
        "Origin of the Pluto-Charon system: Constraints from the New "
        "Horizons flyby. Icarus, 287, 2-11. "
        "https://doi.org/10.1016/j.icarus.2016.11.019"
    ),

    "militzer_2022_jupiter": (
        "Militzer, B., Hubbard, W. B., Wahl, S., et al. (2022). Juno "
        "Spacecraft Measurements of Jupiter's Gravity Imply a Dilute "
        "Core. Planetary Science Journal, 3, 185. "
        "https://doi.org/10.3847/PSJ/ac7ec8 "
        "(See also: Wahl, S. M., et al. (2017). Comparing Jupiter "
        "interior structure models to Juno gravity measurements and the "
        "role of a dilute core. GRL, 44, 4649-4659. "
        "https://doi.org/10.1002/2017GL073160)"
    ),

    "miller_2002_eros": (
        "Miller, J. K., Konopliv, A. S., Antreasian, P. G., et al. (2002). "
        "Determination of Shape, Gravity, and Rotational State of Asteroid "
        "433 Eros. Icarus, 155, 3-17. "
        "https://doi.org/10.1006/icar.2001.6753"
    ),

    "nimmo_2003_europa": (
        "Nimmo, F., Pappalardo, R. T., & Giese, B. (2003). On the origins "
        "of band topography, Europa. Icarus, 166, 21-32. "
        "https://doi.org/10.1016/j.icarus.2003.08.002"
    ),

    "park_2016_ceres": (
        "Park, R. S., Konopliv, A. S., Bills, B. G., et al. (2016). "
        "A partially differentiated interior for (1) Ceres deduced from "
        "its gravity field and shape. Nature, 537, 515-517. "
        "https://doi.org/10.1038/nature18955"
    ),

    "park_2018_ceres": (
        "Park, R. S., Konopliv, A. S., Asmar, S. W., et al. (2018). "
        "The Ceres gravity field, spin pole, rotation period and orbit "
        "from the Dawn radiometric tracking and optical data. Icarus, "
        "299, 411-429. https://doi.org/10.1016/j.icarus.2017.08.005"
    ),

    "patzold_2014": (
        "Pätzold, M., Andert, T. P., Tyler, G. L., et al. (2014). Phobos "
        "mass determination from the very close flyby of Mars Express in "
        "2010. Icarus, 229, 92-98. "
        "https://doi.org/10.1016/j.icarus.2013.10.021"
    ),

    "pavlis_2012": (
        "Pavlis, N. K., Holmes, S. A., Kenyon, S. C., & Factor, J. K. "
        "(2012). The development and evaluation of the Earth Gravitational "
        "Model 2008 (EGM2008). J. Geophys. Res., 117, B04406. "
        "https://doi.org/10.1029/2011JB008916"
    ),

    "preusker_2014_vesta": (
        "Preusker, F., Scholten, F., Matz, K.-D., et al. (2014). Global "
        "shape of (4) Vesta from Dawn FC stereo images. LPSC 45, #1416. "
        "https://www.hou.usra.edu/meetings/lpsc2014/pdf/1416.pdf"
    ),

    "roatsch_2016_ceres": (
        "Roatsch, T., Kersten, E., Matz, K.-D., et al. (2016). High-"
        "resolution Ceres High Altitude Mapping Orbit atlas derived from "
        "Dawn Framing Camera images. Planet. Space Sci., 129, 103-107. "
        "https://doi.org/10.1016/j.pss.2016.05.011"
    ),

    "russell_2012_vesta": (
        "Russell, C. T., Raymond, C. A., Coradini, A., et al. (2012). "
        "Dawn at Vesta: Testing the Protoplanetary Paradigm. Science, "
        "336, 684-686. https://doi.org/10.1126/science.1219381"
    ),

    "schenk_2007_triton": (
        "Schenk, P. M., & Zahnle, K. (2007). On the negligible surface "
        "age of Triton. Icarus, 192, 135-149. "
        "https://doi.org/10.1016/j.icarus.2007.07.004"
    ),

    "schenk_2018_pluto": (
        "Schenk, P. M., Beyer, R. A., McKinnon, W. B., et al. (2018). "
        "Basins, fractures and volcanoes: Global cartography and "
        "topography of Pluto from New Horizons. Icarus, 314, 400-433. "
        "https://doi.org/10.1016/j.icarus.2018.06.008"
    ),

    "scheeres_2020_bennu": (
        "Scheeres, D. J., French, A. S., Tricarico, P., et al. (2020). "
        "Heterogeneous mass distribution of the rubble-pile asteroid "
        "(101955) Bennu. Science Advances, 6, eabc3350. "
        "https://doi.org/10.1126/sciadv.abc3350"
    ),

    "smith_2001_mola": (
        "Smith, D. E., Zuber, M. T., Frey, H. V., et al. (2001). Mars "
        "Orbiter Laser Altimeter: Experiment summary after the first "
        "year of global mapping of Mars. JGR Planets, 106, 23689-23722. "
        "https://doi.org/10.1029/2000JE001364"
    ),

    "spitale_2006": (
        "Spitale, J. N., Jacobson, R. A., Porco, C. C., & Owen, W. M. "
        "(2006). The orbits of Saturn's small satellites derived from "
        "combined historic and Cassini imaging observations. AJ, 132, "
        "692-710. https://doi.org/10.1086/505206"
    ),

    "tajeddine_2014_mimas": (
        "Tajeddine, R., Rambaux, N., Lainey, V., et al. (2014). "
        "Constraints on Mimas' interior from Cassini ISS libration "
        "measurements. Science, 346, 322-324. "
        "https://doi.org/10.1126/science.1255299"
    ),

    "thomas_1988_uranian": (
        "Thomas, P. C. (1988). Radii, shapes, and topography of the "
        "satellites of Uranus from limb coordinates. Icarus, 73, 427-441. "
        "https://doi.org/10.1016/0019-1035(88)90054-1"
    ),

    "thomas_1998_galileans": (
        "Thomas, P. C., Davies, M. E., Colvin, T. R., et al. (1998). "
        "The shape of Io from Galileo limb measurements. Icarus, 135, "
        "175-180. https://doi.org/10.1006/icar.1998.5987"
    ),

    "thomas_2010_saturnian_smalls": (
        "Thomas, P. C. (2010). Sizes, shapes, and derived properties of "
        "the saturnian satellites after the Cassini nominal mission. "
        "Icarus, 208, 395-401. "
        "https://doi.org/10.1016/j.icarus.2010.01.025"
    ),

    "thomas_2016_enceladus": (
        "Thomas, P. C., Tajeddine, R., Tiscareno, M. S., et al. (2016). "
        "Enceladus's measured physical libration requires a global "
        "subsurface ocean. Icarus, 264, 37-47. "
        "https://doi.org/10.1016/j.icarus.2015.08.037"
    ),

    "vernazza_2020_hygiea": (
        "Vernazza, P., Jorda, L., Ševeček, P., et al. (2020). A basin-"
        "free spherical shape as an outcome of a giant impact on asteroid "
        "Hygiea. Nature Astronomy, 4, 136-141. "
        "https://doi.org/10.1038/s41550-019-0915-8"
    ),

    "watanabe_2019_ryugu": (
        "Watanabe, S., Hirabayashi, M., Hirata, N., et al. (2019). "
        "Hayabusa2 arrives at the carbonaceous asteroid 162173 Ryugu — "
        "A spinning top-shaped rubble pile. Science, 364, 268-272. "
        "https://doi.org/10.1126/science.aav8032"
    ),

    "wieczorek_2013_moon": (
        "Wieczorek, M. A., Neumann, G. A., Nimmo, F., et al. (2013). "
        "The Crust of the Moon as Seen by GRAIL. Science, 339, 671-675. "
        "https://doi.org/10.1126/science.1231530"
    ),

    "willner_2014_phobos": (
        "Willner, K., Shi, X., & Oberst, J. (2014). Phobos' shape and "
        "topography models. Planetary and Space Science, 102, 51-59. "
        "https://doi.org/10.1016/j.pss.2013.12.006"
    ),
}


__all__ = [
    "PRECISION_HIGH", "PRECISION_MEDIUM", "PRECISION_LOW", "PRECISION_NONE",
    "GravityModel", "TopographyModel", "InteriorLayer", "InteriorModel",
    "GRAVITY_MODELS", "TOPOGRAPHY_MODELS", "INTERIOR_MODELS",
    "SOURCES",
]
