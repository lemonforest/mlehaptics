"""Sol Dynamical-Regime Classifier — labelled training examples and
feature schema for the v0.24.9 ship (eigenbasis-projection version
of the v0.24.x if/else chain).

Real, sourced data for the v0.24.9 ship — the **tenth and capstone
ship in v0.24.x** and the **first time** the project ships an
explicit *consumer* of the v0.24.x methodology arc rather than
another generative catalog. Each v0.24.x ship (v0.24.0 through
v0.24.8) becomes a **labelled training example** in a 7-dimensional
feature space. The eigenbasis of the resulting 9 x 7 feature
matrix is the project's **dynamical-regime classifier**: given an
arbitrary feature vector for a body or sub-system, project it into
the eigenbasis and the nearest-neighbour regime label tells you
which v0.24.x methodology to apply.

Origin context
--------------
The user's original framing in the v0.24.x conversation: there is
an *if/else chain* that selects which dynamical-spectrum
methodology to apply to a given body — Mercury / Luna get rigid-
body action-angle (v0.24.0 / v0.24.1), Mars gets KAM small-
denominator failure (v0.24.2), Sun gets continuum normal-modes
(v0.24.3), and so on. The chain works but is hand-coded and
brittle. v0.24.9 replaces it with a learned eigenbasis projection:
the v0.24.x catalogs themselves are the training labels.

Feature schema (7 features)
---------------------------
Each training example is a 7-tuple:

    (time_scale_log_s, spatial_scale_log_km, stability_index,
     has_commensurability, prediction_track_signal,
     dimensionality, forcing_class_index)

* ``time_scale_log_s`` — log10 of the body/sub-system's natural
  period in seconds. Mercury orbital ~6.9; Sun p-modes ~2.5;
  Hawaii hotspot track ~15.4.

* ``spatial_scale_log_km`` — log10 of the natural length scale in
  km. Sun radius ~5.8; Mars radius ~3.5; sub-km asteroid ~-0.5.

* ``stability_index`` — heuristic 0..1 indicator of Diophantine
  stability. 1.0 = stable rigid-body action-angle (Mercury); 0.0
  = chaotic / KAM-broken (Mars obliquity); 0.5 = intermediate /
  drift-dominated.

* ``has_commensurability`` — 1 if the system carries an observable
  small-integer commensurability (Mercury 3:2 spin-orbit;
  Saros 223:239:242), 0 otherwise.

* ``prediction_track_signal`` — +1 if the system has a published
  prediction methodology with HIT-only track record (Saros);
  -1 if a published methodology has been observed to MISS on
  this body (Axial Seamount 2024-2025); 0 if no published
  prediction methodology.

* ``dimensionality`` — 0 (point dynamics, e.g., orbital), 1 (1D
  chain feature, e.g., Hawaii hotspot track), 2 (2D surface family,
  e.g., Mars Tharsis), 3 (3D volume / continuum, e.g., Sun /
  toroidal-residual interior).

* ``forcing_class_index`` — categorical index for the dominant
  forcing physics: 0 = gravitational, 1 = stellar-oscillation,
  2 = radiation-coupled, 3 = tectonic / plate motion, 4 =
  volcanic / mantle plume.

Why this feature set
--------------------
Hand-curated to span the six orders of magnitude of timescale
(seconds to Gyr), six orders of magnitude of length scale (m to
1e6 km), and the three Diophantine-stability classes (stable /
commensurate / chaotic) covered by the v0.24.x ships. With 9
training examples and 7 features, the principal-component
decomposition has at most 7 non-trivial eigenmodes; the top 2-3
account for nearly all the variance because the features are
strongly correlated (large bodies tend to have long timescales,
chaotic systems tend to have low stability, etc.).

**Not a re-derivation.** Feature values are hand-set from each
v0.24.x ship's catalog data and the published references already
cited in those ships. No new physical claim is made — the
classifier is a *consumer* of the v0.24.x catalogs.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"

# ---- Feature-vector cardinality (pinned for ABI / test stability) ----
N_FEATURES: int = 7


# ---- Forcing-class enum (categorical feature 7) ---------------------
FORCING_CLASS_GRAVITATIONAL: int = 0
FORCING_CLASS_STELLAR_OSCILLATION: int = 1
FORCING_CLASS_RADIATION: int = 2
FORCING_CLASS_TECTONIC: int = 3
FORCING_CLASS_VOLCANIC: int = 4

FORCING_CLASS_NAMES: Dict[int, str] = {
    FORCING_CLASS_GRAVITATIONAL: "gravitational",
    FORCING_CLASS_STELLAR_OSCILLATION: "stellar_oscillation",
    FORCING_CLASS_RADIATION: "radiation",
    FORCING_CLASS_TECTONIC: "tectonic",
    FORCING_CLASS_VOLCANIC: "volcanic",
}


@dataclass(frozen=True)
class RegimeExample:
    """One labelled training example (one v0.24.x ship).

    The 7 numeric features are stored alongside the regime label
    and a short description that tells you what catalog to look at
    if the classifier returns this regime.
    """
    name: str
    ship_version: str
    regime_label: str
    description: str
    catalog_module: str

    # 7-feature signature vector (see module docstring for schema)
    time_scale_log_s: float
    spatial_scale_log_km: float
    stability_index: float
    has_commensurability: int
    prediction_track_signal: int
    dimensionality: int
    forcing_class_index: int

    notes: str = ""
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH

    def feature_vector(self) -> Tuple[float, ...]:
        """Return the 7-feature vector as an ordered tuple."""
        return (
            self.time_scale_log_s,
            self.spatial_scale_log_km,
            self.stability_index,
            float(self.has_commensurability),
            float(self.prediction_track_signal),
            float(self.dimensionality),
            float(self.forcing_class_index),
        )


# ---------------------------------------------------------------------------
# Per-regime training roster (one per v0.24.x ship)
# ---------------------------------------------------------------------------

REGIME_EXAMPLES: List[RegimeExample] = [

    # ==== v0.24.0 — Mercury Dynamical Spectrum ========================

    RegimeExample(
        name="mercury_dynamical_spectrum",
        ship_version="0.24.0",
        regime_label="rigid_body_action_angle_stable",
        description=(
            "Stable rigid-body action-angle dynamics with Diophantine-"
            "robust integer-commensurability (Mercury 3:2 spin-orbit "
            "lock; Le Verrier/Einstein perihelion-precession closure)."
        ),
        catalog_module="mercury_dynamical_spectrum_catalog",
        # Mercury orbital period 88 days = 7.6e6 s
        time_scale_log_s=6.88,
        # Mercury radius 2440 km
        spatial_scale_log_km=3.39,
        stability_index=1.0,
        has_commensurability=1,
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=FORCING_CLASS_GRAVITATIONAL,
        notes="The cleanest Diophantine-stable rigid-body case in "
              "the catalog: Le Verrier/Einstein perihelion closure "
              "to within 1 arcsec/century.",
        source_key="v024_0",
    ),

    # ==== v0.24.1 — Luna Dynamical Spectrum ===========================

    RegimeExample(
        name="luna_dynamical_spectrum",
        ship_version="0.24.1",
        regime_label="rigid_body_action_angle_commensurate",
        description=(
            "Tidal-locked rigid-body action-angle with Saros "
            "integer-commensurability (223:239:242). Cassini state 2 "
            "spin axis. The textbook small-denominator case where "
            "the commensurability is empirically robust enough to "
            "underpin a 4500-year-old eclipse-prediction discipline."
        ),
        catalog_module="luna_dynamical_spectrum_catalog",
        # Sidereal month 27.3 days = 2.36e6 s
        time_scale_log_s=6.37,
        # Luna radius 1737 km
        spatial_scale_log_km=3.24,
        stability_index=1.0,
        has_commensurability=1,
        prediction_track_signal=1,
        dimensionality=0,
        forcing_class_index=FORCING_CLASS_GRAVITATIONAL,
        notes="The Saros-on-Antikythera cross-strand observation: "
              "the same (223, 239, 242) commensurability is in both "
              "ancient bronze and modern LLR data.",
        source_key="v024_1",
    ),

    # ==== v0.24.2 — Mars Dynamical Spectrum ===========================

    RegimeExample(
        name="mars_dynamical_spectrum",
        ship_version="0.24.2",
        regime_label="rigid_body_chaotic_obliquity",
        description=(
            "KAM small-denominator failure: Mars's spin-axis "
            "precession frequency (~7.6 arcsec/yr) approaches the "
            "magnitude of inner-Solar-System secular fundamentals "
            "s3 / s4, breaking the Diophantine stability condition. "
            "Result: chaotic obliquity wandering on Gyr timescales."
        ),
        catalog_module="mars_dynamical_spectrum_catalog",
        # Mars orbital period 686.97 days = 5.93e7 s
        time_scale_log_s=7.78,
        # Mars radius 3389.5 km
        spatial_scale_log_km=3.53,
        stability_index=0.0,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=FORCING_CLASS_GRAVITATIONAL,
        notes="The contrast case to Mercury / Luna. Mars is the "
              "canonical observable signature in our Solar System "
              "of KAM-theory small-denominator failure.",
        source_key="v024_2",
    ),

    # ==== v0.24.3 — Sun Dynamical Spectrum ============================

    RegimeExample(
        name="sun_dynamical_spectrum",
        ship_version="0.24.3",
        regime_label="continuum_normal_modes",
        description=(
            "Continuum normal-mode oscillation spectrum: ~10^7 "
            "discrete (n, l, m) modes obeying the Tassoul 1980 "
            "asymptotic relation. Three constants (Delta_nu, "
            "delta_nu, epsilon) predict the entire mode spectrum "
            "via a closure analogous to v0.24.1 Saros."
        ),
        catalog_module="sun_dynamical_spectrum_catalog",
        # Solar p-mode period ~5 min = 300 s
        time_scale_log_s=2.48,
        # Sun radius 696000 km
        spatial_scale_log_km=5.84,
        stability_index=1.0,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=3,
        forcing_class_index=FORCING_CLASS_STELLAR_OSCILLATION,
        notes="The first stellar entry; methodology extension from "
              "rigid-body action-angle to continuum normal-mode "
              "spectrum.",
        source_key="v024_3",
    ),

    # ==== v0.24.4 — Toroidal Residual J2 ==============================

    RegimeExample(
        name="toroidal_residual_j2",
        ship_version="0.24.4",
        regime_label="shape_residual_chandrasekhar",
        description=(
            "Per-body shape position on the Chandrasekhar 1969 "
            "ellipsoidal-equilibrium sequence: Sphere -> Maclaurin "
            "(q < 0.187) -> Jacobi -> bar (q > 0.27) -> ring/torus "
            "fission (q > 0.36). J2 quantifies the leftover toroidal "
            "residual. Saturn closest to bifurcation at q ~= 0.158."
        ),
        catalog_module="toroidal_residual_catalog",
        # Mid-range rotation period (~1 day = 86400 s)
        time_scale_log_s=4.94,
        # Mid-range body radius (~10000 km, mix of terrestrials + giants)
        spatial_scale_log_km=4.0,
        stability_index=0.5,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=3,
        forcing_class_index=FORCING_CLASS_GRAVITATIONAL,
        notes="The shape-side counterpart to v0.24.0-v0.24.3 "
              "dynamical-spectrum surfaces. 14-body roster.",
        source_key="v024_4",
    ),

    # ==== v0.24.5 — Hawaii Chain ======================================

    RegimeExample(
        name="hawaii_chain",
        ship_version="0.24.5",
        regime_label="bounded_local_laplacian_trajectory",
        description=(
            "Bounded-local graph-Laplacian on a hotspot track on a "
            "body WITH plate tectonics. 18-seamount roster spanning "
            "~85 Myr; Fiedler-eigenvector partition + age-vs-arc-"
            "length residuals decompose the chain into spatial-"
            "trajectory + directional-bend signatures."
        ),
        catalog_module="hawaii_chain_catalog",
        # Chain timespan ~85 Myr = 2.7e15 s
        time_scale_log_s=15.43,
        # Chain length ~6500 km along Pacific Plate
        spatial_scale_log_km=3.81,
        stability_index=0.7,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=1,
        forcing_class_index=FORCING_CLASS_TECTONIC,
        notes="The first non-orbital eigenbasis application. Pacific "
              "Plate motion as the trajectory-driver.",
        source_key="v024_5",
    ),

    # ==== v0.24.6 — Yarkovsky/YORP ====================================

    RegimeExample(
        name="yarkovsky_yorp",
        ship_version="0.24.6",
        regime_label="radiation_coupled_drift",
        description=(
            "Small-body anisotropic-thermal-emission drift: "
            "Yarkovsky semi-major-axis drift ~1e-4 AU/Myr (prograde "
            "outward, retrograde inward) + YORP spin-state evolution "
            "to fission-limit / obliquity attractors. The radiation-"
            "coupled analogue of v0.24.2 Mars's gravitational chaos."
        ),
        catalog_module="yarkovsky_yorp_catalog",
        # Yarkovsky drift timescale ~Myr = 3.15e13 s
        time_scale_log_s=13.5,
        # Sub-km typical asteroid (~0.3-1 km)
        spatial_scale_log_km=-0.5,
        stability_index=0.5,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=FORCING_CLASS_RADIATION,
        notes="Spin-FREE counterpart to v0.23.0's spin-orbit-LOCKED "
              "roster.",
        source_key="v024_6",
    ),

    # ==== v0.24.7 — Mars Tharsis ======================================

    RegimeExample(
        name="mars_tharsis",
        ship_version="0.24.7",
        regime_label="bounded_local_laplacian_family",
        description=(
            "Bounded-local graph-Laplacian on volcanic features on a "
            "body WITHOUT plate tectonics. 5-volcano roster (Olympus "
            "Mons + Tharsis Montes ridge + Alba Mons). Same "
            "eigendecomposition machinery as v0.24.5 Hawaii; "
            "stationary-plumes regime surfaces a *cogenetic family* "
            "structure rather than a chronological trajectory."
        ),
        catalog_module="mars_tharsis_catalog",
        # Youngest surface flows ~150 Myr = 4.7e15 s
        time_scale_log_s=15.67,
        # Tharsis system spans ~3000 km
        spatial_scale_log_km=3.48,
        stability_index=0.6,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=2,
        forcing_class_index=FORCING_CLASS_VOLCANIC,
        notes="No-plate-tectonics counterpart to v0.24.5 Hawaii. "
              "Olympus Mons super-volcano is the direct consequence "
              "of stationary plumes + unbroken lithosphere.",
        source_key="v024_7",
    ),

    # ==== v0.24.8 — Axial Seamount ====================================

    RegimeExample(
        name="axial_seamount",
        ship_version="0.24.8",
        regime_label="temporal_quasi_periodic_cycle",
        description=(
            "Temporal-spectrum eruption-cycle observable on a real-"
            "time-monitored submarine volcano. 3-eruption roster "
            "(1998 / 2011 / 2015) + Chadwick-Nooner forecast track-"
            "record (1 HIT, 1 MISS as of 2026). Decade-scale "
            "Diophantine-stability-vs-window cousin of v0.24.2 Mars."
        ),
        catalog_module="axial_seamount_catalog",
        # Mean inter-eruption interval ~8.6 yr = 2.7e8 s
        time_scale_log_s=8.61,
        # Caldera ~3-8 km
        spatial_scale_log_km=0.90,
        stability_index=0.5,
        has_commensurability=0,
        prediction_track_signal=-1,
        dimensionality=0,
        forcing_class_index=FORCING_CLASS_VOLCANIC,
        notes="The first explicit prediction-reliability ship: same "
              "methodology, same body, one HIT and one MISS.",
        source_key="v024_8",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — pointers back to the v0.24.x ships that defined each label
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "v024_0": (
        "ephemerides-spectral v0.24.0 (Mercury Dynamical Spectrum). "
        "Margot 2007 Mercury 3:2 spin-orbit lock; Le Verrier 1859 / "
        "Einstein 1916 perihelion-precession closure. See "
        "ephemerides_spectral_research_notebook.md release-history "
        "v0.24.0 entry + research/mercury_dynamical_spectrum_data.py."
    ),
    "v024_1": (
        "ephemerides-spectral v0.24.1 (Luna Dynamical Spectrum, "
        "LLR-anchored). Williams & Boggs 2014; Saros 223:239:242 "
        "integer-commensurability closure. See research/"
        "luna_dynamical_spectrum_data.py."
    ),
    "v024_2": (
        "ephemerides-spectral v0.24.2 (Mars Dynamical Spectrum, "
        "chaotic obliquity). Laskar-Robutel 1993; Touma-Wisdom 1993; "
        "Le Maistre 2023 InSight RISE. See research/"
        "mars_dynamical_spectrum_data.py."
    ),
    "v024_3": (
        "ephemerides-spectral v0.24.3 (Sun Dynamical Spectrum, "
        "helioseismic p-modes). Tassoul 1980 asymptotic relation; "
        "BiSON / SOI-MDI / SDO-HMI data. See research/"
        "sun_dynamical_spectrum_data.py."
    ),
    "v024_4": (
        "ephemerides-spectral v0.24.4 (Toroidal-Residual J2 Catalog). "
        "Chandrasekhar 1969 Ellipsoidal Figures of Equilibrium; "
        "Mankovich-Fuller 2021 Saturn rotation. See research/"
        "toroidal_residual_data.py."
    ),
    "v024_5": (
        "ephemerides-spectral v0.24.5 (Hawaiian-Emperor Chain "
        "Spectral Catalog). Sharp & Clague 2006 bend age; Tarduno "
        "2003 paleomagnetic. See research/hawaii_chain_data.py."
    ),
    "v024_6": (
        "ephemerides-spectral v0.24.6 (Small-body Yarkovsky/YORP "
        "Catalog). Farnocchia 2013 Bennu; Lowry 2007 first YORP "
        "detection; Vokrouhlicky-Capek 2002 obliquity attractors. "
        "See research/yarkovsky_yorp_data.py."
    ),
    "v024_7": (
        "ephemerides-spectral v0.24.7 (Mars Tharsis Volcanic Chain "
        "Catalog). Hartmann & Neukum 2001 Mars crater chronology; "
        "Werner 2009; Plescia 2004; Smith 2001 MGS MOLA. See "
        "research/mars_tharsis_data.py."
    ),
    "v024_8": (
        "ephemerides-spectral v0.24.8 (Axial Seamount Eruption "
        "Chronology Catalog). Chadwick 2016 forecast HIT; "
        "Nooner-Chadwick 2016 inflation-trigger framework; "
        "post-2015 follow-ups for 2024-2025 MISS context. See "
        "research/axial_seamount_data.py."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "N_FEATURES",
    "FORCING_CLASS_GRAVITATIONAL",
    "FORCING_CLASS_STELLAR_OSCILLATION",
    "FORCING_CLASS_RADIATION",
    "FORCING_CLASS_TECTONIC",
    "FORCING_CLASS_VOLCANIC",
    "FORCING_CLASS_NAMES",
    "REGIME_EXAMPLES",
    "SOURCES",
    "RegimeExample",
]
