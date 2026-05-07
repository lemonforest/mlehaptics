"""ICBM Trajectory Catalog — three-regime exo-atmospheric ballistic
data for the v0.22.0 ship.

Real, sourced data for **Layer B** of the trajectory + sensing
surface. Earth-only canonical reference values — the publishable
piece is the textbook **3-regime decomposition** (boost ↔ midcourse ↔
re-entry), not a vehicle-specific propagator.

Physics (Earth-centric reference)
---------------------------------
A ballistic missile trajectory has three classical regimes, each
governed by a different physical balance:

* **Boost** (0 ≤ t ≤ ~3-5 min, surface → ~200 km): thrust + gravity +
  atmospheric drag. Vehicle-specific (Isp, thrust profile, gravity
  turn). The publishable boundary is the **burnout state** (v_burnout,
  γ_burnout, h_burnout) — that's the Layer B input, not boost
  modelling.
* **Midcourse** (~3-5 min ≤ t ≤ ~25-28 min, ~200 km → apex → ~100 km):
  pure ballistic Kepler ellipse in vacuum. Apex 1000-1500 km for
  intercontinental range; apex 200-400 km for theatre range.
  Closed-form via vis-viva + flight-path-angle formula
  (Bate-Mueller-White Ch. 6).
* **Re-entry** (t > ~28 min, 100 km → ground): Allen-Eggers ballistic
  re-entry (Allen & Eggers 1958). Velocity decays as
  ``v(h) = v_e · exp[-ρ₀H/(2 BC sin γ_e) · exp(-h/H)]``
  — closed-form, fully publishable.

The ballistic coefficient ``BC = m / (C_d · A)`` parameterizes
re-entry. Heavy compact RVs have BC ~5000-15000 kg/m²; light decoys
(balloons, chaff, light replicas) have BC ~10-50 kg/m². The
**differential ballistic coefficient** is the only midcourse-
surviving discriminator (Sessler/UCS *Countermeasures* 2000).

Coverage notes (v0.22.0)
------------------------
Earth-only Layer B. Other-body ballistic propagation lives in Layer A
(short-range, surface-to-surface). Mars/Venus/Titan have no operational
ICBM context; the math generalises trivially via swap-in of body
gravity + atmosphere.

**Not a re-derivation.** Earth gravitational parameter μ + radius
from canonical NASA values; phase-boundary conventions from Vallado
§9.6. Allen-Eggers solution + BC-differential physics from cited
references. **No specific RV signatures, no specific sensor
sensitivities, no specific kill-vehicle parameters.** Publishable
textbook physics only.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Earth-centric ICBM reference constants --------------------------
# Earth gravitational parameter (μ = G·M_earth), m³/s²
EARTH_MU_M3_S2: float = 3.986004418e14

# Earth equatorial radius (m)
EARTH_RADIUS_M: float = 6378137.0

# Phase-boundary altitudes (m). Conventional cuts; not operational
# parameters — these are the textbook regime cuts in Vallado §9.6.
BOOST_BURNOUT_ALTITUDE_DEFAULT_M: float = 200_000.0  # ~200 km
REENTRY_INTERFACE_ALTITUDE_M: float = 100_000.0       # Karman line

# Reference exponential atmosphere for re-entry (sea-level
# US Standard 1976; cross-references ballistic_trajectory_data.py).
REENTRY_RHO_0_KG_M3: float = 1.225
REENTRY_SCALE_HEIGHT_M: float = 8500.0

# Standard sea-level g for surface-impact velocity reporting.
EARTH_SURFACE_G_M_S2: float = 9.80665


@dataclass(frozen=True)
class ICBMReferenceProfile:
    """Reference 3-regime trajectory profile (Earth-centric).

    These are textbook-published reference profiles for the **three
    canonical range classes** of ballistic missile, used as
    sanity-check fixtures for the propagator. Values are from open-
    literature missile-defense physics texts (Wilkening 2000, Sessler
    et al. 2000); not specific weapon-system parameters.
    """
    profile_name: str
    range_km: float                    # Ground range (km)
    burnout_velocity_m_s: float        # Speed at end of boost
    burnout_flight_path_angle_deg: float  # Burnout flight-path angle
    midcourse_apex_km: float           # Apex altitude (km)
    midcourse_duration_s: float        # Approximate midcourse duration
    reentry_velocity_m_s: float        # Speed at re-entry interface (~100 km)
    typical_warhead_bc_kg_m2: float    # Heavy-RV ballistic coefficient
    typical_decoy_bc_kg_m2: float      # Light-decoy ballistic coefficient
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Reference profiles (textbook open-literature, NOT operational parameters)
# ---------------------------------------------------------------------------

ICBM_REFERENCE_PROFILES: List[ICBMReferenceProfile] = [

    # ---- Short-range ballistic (SRBM-class, ~300 km) -----------------
    ICBMReferenceProfile(
        profile_name="srbm_300km",
        range_km=300.0,
        burnout_velocity_m_s=1700.0,
        burnout_flight_path_angle_deg=42.0,
        midcourse_apex_km=80.0,
        midcourse_duration_s=300.0,
        reentry_velocity_m_s=1700.0,
        typical_warhead_bc_kg_m2=3000.0,
        typical_decoy_bc_kg_m2=30.0,
        precision_flag=PRECISION_MEDIUM,
        notes="Theatre / short-range ballistic class. Stays largely "
              "in atmosphere; midcourse Kepler approximation is an "
              "imperfect fit. Wilkening 2000 reference profile.",
        source_key="wilkening_2000",
    ),

    # ---- Medium-range ballistic (MRBM-class, ~1500 km) ---------------
    ICBMReferenceProfile(
        profile_name="mrbm_1500km",
        range_km=1500.0,
        burnout_velocity_m_s=4000.0,
        burnout_flight_path_angle_deg=37.0,
        midcourse_apex_km=400.0,
        midcourse_duration_s=750.0,
        reentry_velocity_m_s=3900.0,
        typical_warhead_bc_kg_m2=5000.0,
        typical_decoy_bc_kg_m2=30.0,
        precision_flag=PRECISION_MEDIUM,
        notes="Medium-range ballistic. Apex above Karman line; "
              "midcourse is exo-atmospheric Kepler.",
        source_key="wilkening_2000",
    ),

    # ---- Intercontinental ballistic (ICBM-class, ~10000 km) ----------
    ICBMReferenceProfile(
        profile_name="icbm_10000km",
        range_km=10000.0,
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        midcourse_apex_km=1200.0,
        midcourse_duration_s=1500.0,
        reentry_velocity_m_s=7000.0,
        typical_warhead_bc_kg_m2=10000.0,
        typical_decoy_bc_kg_m2=50.0,
        precision_flag=PRECISION_MEDIUM,
        notes="Intercontinental ballistic class. Long midcourse "
              "(~25 min) above 100 km — the regime where decoys + "
              "warheads are indistinguishable except by BC differential. "
              "Sessler/UCS Countermeasures 2000 reference.",
        source_key="sessler_ucs_2000",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "wilkening_2000": (
        "Wilkening D. A. (2000). A Simple Model for Calculating "
        "Ballistic Missile Defense Effectiveness. Science & Global "
        "Security 8, 183-215. Analytic SSPK framework + reference "
        "trajectory profiles."
    ),
    "sessler_ucs_2000": (
        "Sessler A. M., Cornwall J. M., Dietz B., Fetter S., Frankel S., "
        "et al. (2000). Countermeasures: A Technical Evaluation of the "
        "Operational Effectiveness of the Planned US National Missile "
        "Defense System. Union of Concerned Scientists / MIT Security "
        "Studies Program. Canonical decoy-discrimination physics."
    ),
    "vallado_2013": (
        "Vallado D. A. (2013). Fundamentals of Astrodynamics and "
        "Applications, 4th ed. Microcosm Press. §9.6 (ballistic missile "
        "trajectories) + Ch. 8 (re-entry)."
    ),
    "bate_mueller_white_1971": (
        "Bate R. R., Mueller D. D., White J. E. (1971). Fundamentals "
        "of Astrodynamics. Dover. Ch. 6 (ballistic missile midcourse "
        "Kepler-ellipse derivation)."
    ),
    "allen_eggers_1958": (
        "Allen H. J., Eggers A. J. (1958). A study of the motion and "
        "aerodynamic heating of ballistic missiles entering the "
        "Earth's atmosphere at high supersonic speeds. NACA Report "
        "1381. The closed-form ballistic re-entry solution."
    ),
    "regan_anandakrishnan_1993": (
        "Regan F. J., Anandakrishnan S. M. (1993). Dynamics of "
        "Atmospheric Re-Entry. AIAA Education Series. Standard text "
        "for Layer C terminal phase + Allen-Eggers extensions."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "EARTH_MU_M3_S2",
    "EARTH_RADIUS_M",
    "BOOST_BURNOUT_ALTITUDE_DEFAULT_M",
    "REENTRY_INTERFACE_ALTITUDE_M",
    "REENTRY_RHO_0_KG_M3",
    "REENTRY_SCALE_HEIGHT_M",
    "EARTH_SURFACE_G_M_S2",
    "ICBM_REFERENCE_PROFILES",
    "SOURCES",
    "ICBMReferenceProfile",
]
