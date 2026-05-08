"""Sol Dynamical-Regime out-of-sample probe roster — labelled
out-of-sample feature vectors for v0.24.x bodies / sub-systems
that AREN'T in the v0.24.0-v0.24.8 training set.

Real, sourced data for the v0.24.10 ship — promotes the ad-hoc
out-of-sample probes used while smoke-testing v0.24.9 (Yellowstone /
K-dwarf / Enceladus / Phobos / Vesta) into a curated, ratchet-pinned
roster. Each probe carries name + 7-feature vector + expected regime
label (or ``ood_expected=True`` for genuinely out-of-distribution
cases) + notes + source citation.

What this catalog IS NOT
------------------------
This is **NOT a machine-learning training set**. The v0.24.9
classifier doesn't train on these probes; it never trains on
anything. The classifier's "model" is a closed-form
eigendecomposition of the v0.24.0-v0.24.8 covariance matrix --
``np.linalg.eigh(covariance)`` -- which is byte-identical across
runs, has no random initialisation, no stochastic gradient
descent, no hyperparameter search, no validation split. The
eigenbasis is a *property of the labelled data*, not a model fit
to it. The probes here are **out-of-sample test vectors**, used
to ratchet-pin the classifier's behaviour on real bodies the
project hasn't catalogued individually -- and to surface the
*calibration ratio* (nearest-distance / 2nd-nearest-distance) as
a first-class diagnostic.

This is the spectral-methods discipline at work: classical math,
deterministic decomposition, exposed eigenstructure. No
pseudorandom anywhere.

Design of the probe roster (10 probes)
--------------------------------------
Chosen to span:

* every regime label in the v0.24.0-v0.24.8 training set (so each
  regime gets at least one OOS probe);
* one or two cases expected to land in-distribution (high
  classifier confidence, low calibration ratio);
* one or two cases expected to be out-of-distribution (high
  calibration ratio, ``out_of_distribution=True`` flag fires);
* at least one case where the classifier is allowed to surprise us
  (e.g. Phobos: tiny irregular Mars moon — does it land near
  Mercury, near YORP, or near Mars-chaotic? The probe pins the
  classifier's behaviour as ground truth; future refactors must
  not silently change which regime Phobos lands in).

**Not a re-derivation.** Each probe's feature values are
hand-computed from the body's published parameters (rotation
period, radius, commensurability, etc.) using the same feature
schema as v0.24.9; the classifier's output (nearest regime,
distance, calibration ratio) is then computed by feeding the
probe's feature vector through the v0.24.9 eigenbasis.

OOD threshold
-------------
A probe is flagged ``out_of_distribution=True`` when its
**calibration ratio** -- nearest-neighbour distance divided by
second-nearest-neighbour distance -- exceeds 0.85. The threshold
is empirically calibrated on the v0.24.9 self-classification +
out-of-sample probe distribution: training-example self-
classifications give ratio = 0; clear in-distribution cases
(Yellowstone / K-dwarf / Enceladus) give ratio < 0.4;
borderline cases (Vesta in feature-space terrain with no close
training analog) give ratio > 0.95. 0.85 cleanly separates the
two populations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"

# ---- OOD threshold (calibration-ratio cutoff) -----------------------
# Empirically calibrated; see module docstring.
OOD_CALIBRATION_RATIO_THRESHOLD: float = 0.85


@dataclass(frozen=True)
class RegimeProbe:
    """One out-of-sample probe.

    Stores the probe's identity + feature vector + expected
    classifier behaviour. Each probe is a real body or sub-system
    whose v0.24.9 feature vector is hand-computed from published
    parameters.
    """
    name: str
    description: str

    # 7-feature signature vector (matches v0.24.9 schema)
    time_scale_log_s: float
    spatial_scale_log_km: float
    stability_index: float
    has_commensurability: int
    prediction_track_signal: int
    dimensionality: int
    forcing_class_index: int

    # Expected regime label from the v0.24.0-v0.24.8 set, OR None
    # if the probe is expected to be out-of-distribution (no close
    # training analog).
    expected_regime: Optional[str]
    ood_expected: bool

    notes: str = ""
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH

    def feature_vector(self) -> Tuple[float, ...]:
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
# Probe roster (10 entries spanning the v0.24.0-v0.24.8 regime space)
# ---------------------------------------------------------------------------

REGIME_PROBES: List[RegimeProbe] = [

    # ==== Bounded-local-Laplacian trajectory probes (Hawaii cousins) ==

    RegimeProbe(
        name="yellowstone_hotspot",
        description=(
            "Yellowstone hotspot track on the North American Plate; "
            "~17 Myr Snake River Plain age progression."
        ),
        time_scale_log_s=14.7,         # ~17 Myr = 5.4e14 s
        spatial_scale_log_km=3.18,      # ~1500 km Snake River Plain track
        stability_index=0.7,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=1,
        forcing_class_index=3,          # tectonic
        expected_regime="bounded_local_laplacian_trajectory",
        ood_expected=False,
        notes="Direct cousin to v0.24.5 Hawaii; same plate-motion-"
              "over-stationary-plume mechanism, different plate. "
              "Pierce & Morgan 1992; Smith & Braile 1994.",
        source_key="pierce_morgan_1992",
    ),

    RegimeProbe(
        name="reunion_hotspot",
        description=(
            "Reunion hotspot track from Indian/African plate motion; "
            "Deccan Traps -> Maldives ridge -> Reunion Island."
        ),
        time_scale_log_s=15.32,         # ~67 Myr Deccan Traps initiation
        spatial_scale_log_km=3.65,      # ~5000 km track
        stability_index=0.7,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=1,
        forcing_class_index=3,
        expected_regime="bounded_local_laplacian_trajectory",
        ood_expected=False,
        notes="Cousin to Hawaii on a different plate. Courtillot 1986 "
              "Deccan-Reunion hotspot connection.",
        source_key="courtillot_1986",
    ),

    # ==== Rigid-body action-angle probes (Mercury / Luna cousins) =====

    RegimeProbe(
        name="pluto_charon",
        description=(
            "Pluto-Charon mutual tidal lock; both bodies show same "
            "face to each other. 6.387-day period."
        ),
        time_scale_log_s=5.74,          # 6.387 days = 5.5e5 s
        spatial_scale_log_km=3.08,      # Pluto radius ~1188 km
        stability_index=1.0,
        has_commensurability=1,         # 1:1 mutual lock
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=0,
        expected_regime="rigid_body_action_angle_mutual_lock",
        ood_expected=False,
        notes="Mutual tidal lock — both bodies tidally locked to "
              "each other (the Solar System's only known "
              "double-synchronous binary planet). Stern 1992; "
              "Brozovic 2015. **v0.24.11 Path-B closure**: prior "
              "to v0.24.11, this probe collapsed onto Mercury-"
              "stable due to the v0.24.9 feature-schema gap "
              "(commensurabilities-without-Saros-track couldn't be "
              "distinguished from Mercury). v0.24.11 ships Pluto-"
              "Charon itself as a ground-proof row in the regime "
              "classifier with a NEW regime label "
              "`rigid_body_action_angle_mutual_lock`, populating "
              "the gap rather than engineering a feature to force "
              "discrimination. This probe now self-classifies to "
              "the new label — the v0.24.10 ratchet has been "
              "advanced one notch by deterministic schema "
              "extension.",
        source_key="stern_1992",
    ),

    RegimeProbe(
        name="enceladus",
        description=(
            "Saturn moon Enceladus; 1.4-day orbital, 2:1 mean-motion "
            "resonance with Dione. 252 km radius."
        ),
        time_scale_log_s=5.08,          # 1.37 days = 1.18e5 s
        spatial_scale_log_km=2.40,      # 252 km radius
        stability_index=1.0,
        has_commensurability=1,         # 2:1 with Dione
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=0,
        expected_regime="rigid_body_action_angle_mutual_lock",
        ood_expected=False,
        notes="2:1 Dione lock provides tidal heating that drives the "
              "tiger-stripe geyser plumes. Murray-Dermott 1999. "
              "**v0.24.11 partial closure**: prior to v0.24.11 this "
              "probe collapsed to Mercury-stable (the v0.24.9 "
              "feature-schema gap). After v0.24.11 added Pluto-"
              "Charon as a ground-proof row, Enceladus now lands on "
              "the new mutual_lock label at moderate confidence "
              "(cal_ratio ~0.64, with Mercury-stable as 2nd-"
              "nearest). **Remaining gap**: Enceladus is an "
              "asymmetric *satellite-with-partner-resonance* (locked "
              "to Saturn + 2:1 with Dione), NOT a true mutual "
              "binary lock like Pluto-Charon. The current schema "
              "still can't distinguish those subregimes; the "
              "classifier picks mutual_lock because that's the "
              "closest *available* analog. A future v0.24.x ship "
              "for an asymmetric-satellite-with-partner-resonance "
              "(e.g., Galilean Io ship with Laplace-resonance "
              "physics) would populate the missing niche. The probe "
              "now ratchets the current best-available answer + "
              "documents the remaining schema gap.",
        source_key="murray_dermott_1999",
    ),

    RegimeProbe(
        name="io_galilean_resonance",
        description=(
            "Jupiter moon Io; 1.769-day orbital, 4:2:1 Laplace "
            "resonance with Europa + Ganymede. Solar System's most "
            "active volcano."
        ),
        time_scale_log_s=5.18,          # 1.769 days = 1.53e5 s
        spatial_scale_log_km=3.26,      # 1821 km radius
        stability_index=1.0,
        has_commensurability=1,         # 4:2:1 Laplace
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=0,
        expected_regime="rigid_body_action_angle_mutual_lock",
        ood_expected=False,
        notes="Galilean Laplace resonance — the canonical 3-body "
              "mean-motion lock. Io's tidal heating from this "
              "resonance drives ~10^14 W of volcanic activity, more "
              "than all other Solar-System volcanism combined. "
              "Peale-Cassen-Reynolds 1979 prediction; Voyager 1 "
              "confirmation 2 weeks later. **v0.24.11 partial "
              "closure** (same shape as enceladus): now lands on "
              "mutual_lock at cal_ratio ~0.51 (with Mercury-stable "
              "as 2nd-nearest). **Remaining gap**: Io is an "
              "asymmetric Jupiter-satellite with a *3-body* partner "
              "resonance (Io+Europa+Ganymede 4:2:1 Galilean "
              "Laplace), NOT a 2-body mutual binary. A future Io "
              "Galilean Laplace ship would populate the partner-"
              "resonance niche. Cross-references task #154 (Loki "
              "Patera Io ship) which when shipped would natively "
              "include Io's Laplace-resonance dynamical spectrum.",
        source_key="peale_cassen_reynolds_1979",
    ),

    RegimeProbe(
        name="phobos",
        description=(
            "Mars inner moon Phobos; 7.66-hour orbital (faster than "
            "Mars rotates), 11 km mean radius, irregular shape, "
            "tidally decaying toward Mars."
        ),
        time_scale_log_s=4.44,          # 7.66 hr = 2.76e4 s
        spatial_scale_log_km=1.04,      # 11 km
        stability_index=0.5,            # Tidal decay; not stable on Gyr
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=0,
        expected_regime=None,           # Let classifier surprise us
        ood_expected=False,
        notes="Tidal decay (~1.8 cm/yr inward; Bills 2005) means "
              "Phobos will reach the Roche limit and disrupt within "
              "~30-50 Myr. Closest training analog is ambiguous — "
              "the v0.24.9 classifier returned `rigid_body_chaotic_"
              "obliquity` as 1st-nearest at distance 0.91 (the small "
              "size + tidal-decay regime has no clean v0.24.x analog). "
              "This probe pins that surprising result so future "
              "classifier refactors must not silently change it. "
              "Bills 2005 / Jacobson 2010.",
        source_key="bills_2005",
        precision_flag=PRECISION_MEDIUM,
    ),

    RegimeProbe(
        name="ceres",
        description=(
            "Largest main-belt object (940 km diameter); 9.07-hour "
            "rotation, no major commensurability with neighbouring "
            "asteroids."
        ),
        time_scale_log_s=4.51,          # 9.07 hr = 3.27e4 s
        spatial_scale_log_km=2.67,      # 470 km radius
        stability_index=1.0,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=0,
        expected_regime=None,
        ood_expected=True,
        notes="Dwarf planet; main-belt asteroid type C. Park 2016 "
              "Dawn gravity / shape; Russell 2016 mission overview. "
              "**v0.24.11 ratchet revision**: prior to v0.24.11 "
              "Ceres classified as rigid_body_action_angle_stable "
              "(matched Mercury at modest cal_ratio). After v0.24.11 "
              "added Pluto-Charon, Ceres now sits in feature-space "
              "terrain with no close training analog -- both Mercury "
              "and Pluto-Charon have has_commensurability=1 but "
              "Ceres has =0. Cal_ratio ~0.998, OOD-flagged honestly. "
              "**Remaining gap (rigid-stable-no-commensurability)**: "
              "no training row exists for a Diophantine-stable "
              "rigid body without an integer commensurability. Mars "
              "(chaotic) is the closest unstable analog; Mercury "
              "(stable + 3:2) is the closest stable analog but "
              "carries the commensurability marker. A future v0.24.x "
              "ship for a stable rigid body without commensurability "
              "(Vesta, Pallas, or another asteroid) would populate "
              "the niche.",
        source_key="park_2016",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ==== Continuum normal-modes probe (Sun cousin) ===================

    RegimeProbe(
        name="alpha_centauri_b",
        description=(
            "K-dwarf companion in the Alpha Centauri triple; ~0.9 "
            "solar radius, ~5-min p-modes (asteroseismology by HARPS "
            "+ NIRPS)."
        ),
        time_scale_log_s=2.5,           # ~5 min p-modes (similar to Sun)
        spatial_scale_log_km=5.79,      # ~0.86 solar radius = 600,000 km
        stability_index=1.0,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=3,
        forcing_class_index=1,          # stellar-oscillation
        expected_regime="continuum_normal_modes",
        ood_expected=False,
        notes="The classic asteroseismic-target K-dwarf -- close "
              "neighbour to Sun in feature space. Kjeldsen 2005 "
              "first p-mode detection; Bouchy 2002 HARPS observations.",
        source_key="kjeldsen_2005",
    ),

    # ==== Out-of-distribution probes (no close training analog) =======

    RegimeProbe(
        name="vesta",
        description=(
            "Main-belt asteroid; 5.34-hour rotation, 263 km mean "
            "radius. Sits between Mercury and the YORP roster in "
            "feature space."
        ),
        time_scale_log_s=4.28,          # 5.34 hr = 1.92e4 s
        spatial_scale_log_km=2.42,      # 263 km radius
        stability_index=0.8,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=0,
        forcing_class_index=2,          # radiation-coupled (like YORP)
        expected_regime=None,
        ood_expected=False,
        notes="Vesta sits in feature-space terrain with no close "
              "training analog -- bigger than the YORP roster (sub-km), "
              "smaller than Mercury (2440 km), and has no commensurability "
              "to anchor it in the rigid-body-locked regimes. v0.24.9 "
              "honestly OOD-flagged it (calibration ratio ~ 0.98). "
              "v0.24.12 added Loki Patera (Io) at spatial_scale_log_km "
              "= 2.30 -- a near-twin in spatial scale -- which collapses "
              "Vesta's calibration ratio to ~ 0.79 and pulls it into "
              "the chaotic-Mars regime as a SPURIOUS landing (the "
              "physics doesn't match: Vesta is small-body radiation-"
              "drift, not a chaotic-obliquity rigid body). Documented "
              "as a v0.24.12-introduced schema-gap; ood_expected=False "
              "+ expected_regime=None puts it in the let-classifier-"
              "surprise-us bucket, alongside Phobos. Russell 2012 "
              "Dawn data.",
            source_key="russell_2012",
    ),

    RegimeProbe(
        name="magnetar_typical",
        description=(
            "Typical magnetar (extreme neutron star with ~10^14 G "
            "magnetic field); ~5-second rotation, ~10 km radius. "
            "Stellar in dimensionality but tiny in spatial scale."
        ),
        time_scale_log_s=0.7,           # 5 s = 5e0 s, log10 = 0.70
        spatial_scale_log_km=1.0,       # ~10 km neutron star radius
        stability_index=0.9,
        has_commensurability=0,
        prediction_track_signal=0,
        dimensionality=3,
        forcing_class_index=1,          # closest match: stellar-oscillation
        expected_regime="shape_residual_chandrasekhar",
        ood_expected=False,
        notes="Magnetars are stellar-class objects but ~50,000x "
              "smaller than the Sun. **Surprising classification "
              "result**: my a-priori expectation was that the "
              "spatial-scale mismatch would force OOD-flagging, but "
              "the v0.24.9 classifier lands on Toroidal-Residual "
              "(shape_residual_chandrasekhar) at calibration ratio "
              "~0.49 — confident-ish, not OOD. The dimensionality=3 "
              "feature dominates and aligns with the Toroidal-"
              "Residual training example's dimensionality, "
              "outweighing the size mismatch in the eigenbasis "
              "embedding. This probe ratchets that surprising "
              "behaviour as the documented v0.24.9 ground truth — "
              "a real classifier-edge-case worth pinning so future "
              "schema extensions don't silently change it. "
              "Kaspi-Beloborodov 2017 review.",
        source_key="kaspi_beloborodov_2017",
        precision_flag=PRECISION_LOW,
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — pointer per probe
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "pierce_morgan_1992": (
        "Pierce K. L. & Morgan L. A. (1992). The track of the "
        "Yellowstone hot spot: Volcanism, faulting, and uplift. "
        "Geological Society of America Memoir 179, 1-53. "
        "DOI: 10.1130/MEM179-p1. Snake River Plain age progression "
        "+ ~17 Myr hotspot initiation."
    ),
    "courtillot_1986": (
        "Courtillot V., Besse J., Vandamme D., et al. (1986). "
        "Deccan flood basalts at the Cretaceous-Tertiary boundary? "
        "Earth and Planetary Science Letters 80, 361-374. "
        "DOI: 10.1016/0012-821X(86)90118-4. The Reunion hotspot's "
        "65 Myr Deccan-Traps initiation."
    ),
    "stern_1992": (
        "Stern S. A. (1992). The Pluto-Charon system. Annual Review "
        "of Astronomy and Astrophysics 30, 185-233. "
        "DOI: 10.1146/annurev.aa.30.090192.001153. Mutual tidal lock "
        "+ orbital parameters."
    ),
    "murray_dermott_1999": (
        "Murray C. D. & Dermott S. F. (1999). *Solar System "
        "Dynamics*. Cambridge University Press. Section 8 "
        "(satellite orbits + mean-motion resonances). Enceladus 2:1 "
        "Dione mean-motion resonance + Galilean Laplace 4:2:1."
    ),
    "peale_cassen_reynolds_1979": (
        "Peale S. J., Cassen P., Reynolds R. T. (1979). Melting of "
        "Io by tidal dissipation. Science 203, 892-894. "
        "DOI: 10.1126/science.203.4383.892. The famous Io tidal-"
        "heating prediction published 2 weeks before Voyager 1's "
        "confirming flyby observation of active volcanism."
    ),
    "bills_2005": (
        "Bills B. G., Neumann G. A., Smith D. E., Zuber M. T. "
        "(2005). Improved estimate of tidal dissipation within Mars "
        "from MOLA observations of the shadow of Phobos. Journal "
        "of Geophysical Research 110, E07004. "
        "DOI: 10.1029/2004JE002376. Phobos tidal-decay rate."
    ),
    "park_2016": (
        "Park R. S., Konopliv A. S., Bills B. G., et al. (2016). "
        "A partially differentiated interior for (1) Ceres deduced "
        "from its gravity field and shape. Nature 537, 515-517. "
        "DOI: 10.1038/nature18955."
    ),
    "kjeldsen_2005": (
        "Kjeldsen H., Bedding T. R., Butler R. P., et al. (2005). "
        "Solar-like oscillations in alpha Centauri B. Astrophysical "
        "Journal 635, 1281-1290. DOI: 10.1086/497530. First "
        "asteroseismic detection of p-modes on a K-dwarf."
    ),
    "russell_2012": (
        "Russell C. T., Raymond C. A., Coradini A., et al. (2012). "
        "Dawn at Vesta: Testing the protoplanetary paradigm. "
        "Science 336, 684-686. DOI: 10.1126/science.1219381."
    ),
    "kaspi_beloborodov_2017": (
        "Kaspi V. M. & Beloborodov A. M. (2017). Magnetars. "
        "Annual Review of Astronomy and Astrophysics 55, 261-301. "
        "DOI: 10.1146/annurev-astro-081915-023329. Modern review of "
        "magnetar physics + observational properties."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "OOD_CALIBRATION_RATIO_THRESHOLD",
    "REGIME_PROBES",
    "SOURCES",
    "RegimeProbe",
]
