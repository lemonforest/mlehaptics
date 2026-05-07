"""Sol Ballistic Trajectory Catalog — per-body BC-parameterized
short-range ballistic propagation data.

Real, sourced data for the v0.22.0 ship — **Layer A** of the
trajectory + sensing surface. Provides per-body exponential-atmosphere
parameters + surface gravity + body radius for short-range projectile
propagation under optional drag.

Physics
-------
Short-range ballistic flight under flat-target gravity, optionally with
exponential atmosphere drag. Closed-form vacuum solution:

    range  = v² · sin(2θ) / g
    apex   = v² · sin²(θ) / (2g)
    T_flight = 2 v · sin(θ) / g

With drag, integrate the equations of motion under

    F_drag = -½ · ρ(h) · v² / BC · v̂
    ρ(h)   = ρ₀ · exp(-h / H)         (exponential atmosphere)
    BC     = m / (C_d · A)             (ballistic coefficient, kg/m²)

This is the textbook formulation (Vallado §8.6.2 / Curtis Ch. 12 /
Tewari for Mars/Venus/Titan body-specific atmospheres).

Coverage notes (v0.22.0)
------------------------
7 bodies — every solid-surface body in v0.20.2 ``BodyClimatology`` with
a published exponential-atmosphere fit + every airless body where the
vacuum solution is the reference. Atmosphere-bearing bodies use the
1-bar ρ₀ for terrestrial bodies, surface ρ₀ for Mars/Venus/Titan, and
the 1-bar reference level for Jupiter (gas giant convention from
v0.20.2).

**Not a re-derivation.** Atmosphere constants are the canonical
exponential-fit parameters from cited references; surface gravity and
radius are NASA Planetary Fact Sheet values.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


@dataclass(frozen=True)
class BallisticAtmosphere:
    """Per-body short-range ballistic propagation parameters.

    Stores the surface gravity + body radius + exponential-atmosphere
    fit (ρ₀, H) needed to integrate ballistic flight with optional
    drag. Airless bodies have ``rho_0_kg_m3 = 0.0``.
    """
    body: str
    # Surface gravity (m/s²). Canonical NASA Planetary Fact Sheet value;
    # for gas giants, the 1-bar reference level.
    surface_gravity_m_s2: float
    # Mean radius (km). For gas giants, 1-bar level.
    body_radius_km: float
    # Surface atmospheric density (kg/m³). For airless bodies, 0.0.
    rho_0_kg_m3: float
    # Atmospheric scale height (m). Approximate exponential-fit H;
    # 0.0 for airless bodies.
    scale_height_m: float
    # Effective top of atmosphere (km). Karman line for Earth (100 km),
    # body-specific elsewhere; 0.0 for airless bodies.
    atmosphere_top_km: float
    # Whether the body has a non-trivial atmosphere for drag purposes.
    has_atmosphere: bool
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body entries — v0.22.0 Layer A roster
# ---------------------------------------------------------------------------

BALLISTIC_ATMOSPHERES: List[BallisticAtmosphere] = [

    # ---- Terra (Earth) — sea-level US Standard Atmosphere 1976 -------
    # ρ₀ = 1.225 kg/m³ at sea level; H = 8500 m mean scale height
    # (varies 7-9 km across stratosphere); Karman line at 100 km.
    BallisticAtmosphere(
        body="terra",
        surface_gravity_m_s2=9.80665,
        body_radius_km=6378.137,
        rho_0_kg_m3=1.225,
        scale_height_m=8500.0,
        atmosphere_top_km=100.0,
        has_atmosphere=True,
        precision_flag=PRECISION_HIGH,
        notes="US Standard Atmosphere 1976 sea-level reference. "
              "Scale height varies 7-9 km in stratosphere; H=8.5 km is "
              "the textbook mean. Karman line at 100 km.",
        source_key="us_standard_atmosphere_1976",
    ),

    # ---- Mars — Tewari atmospheric fit -------------------------------
    # Surface ρ ~ 0.020 kg/m³ at 600 Pa; H ~ 11.1 km (taller than
    # Earth's because lower g and CO2-dominant). Top ~ 100 km.
    BallisticAtmosphere(
        body="mars",
        surface_gravity_m_s2=3.711,
        body_radius_km=3389.5,
        rho_0_kg_m3=0.020,
        scale_height_m=11100.0,
        atmosphere_top_km=100.0,
        has_atmosphere=True,
        precision_flag=PRECISION_HIGH,
        notes="Mars Climate Database / Tewari 2011 fit. Thin 636-Pa "
              "CO2 surface; large scale height because low g + cold T. "
              "Cross-references v0.20.2 fluid_instrument.",
        source_key="tewari_2011",
    ),

    # ---- Venus — VIRA reference atmosphere ---------------------------
    # Surface ρ = 65 kg/m³ at 92 bar (!); H = 15.9 km (warm 740 K +
    # heavy CO2). Atmosphere extends to ~250 km.
    BallisticAtmosphere(
        body="venus",
        surface_gravity_m_s2=8.87,
        body_radius_km=6051.8,
        rho_0_kg_m3=65.0,
        scale_height_m=15900.0,
        atmosphere_top_km=250.0,
        has_atmosphere=True,
        precision_flag=PRECISION_HIGH,
        notes="VIRA (Venus International Reference Atmosphere). 92-bar "
              "surface; ρ₀=65 kg/m³ is FIFTY times Earth's. Cross-"
              "references v0.20.2 fluid_instrument 92-bar atmosphere.",
        source_key="seiff_1985_vira",
    ),

    # ---- Titan — Cassini-Huygens HASI -------------------------------
    # Surface ρ = 5.43 kg/m³ at 1.467 bar; H = 20 km (cold 94 K +
    # N2-dominant). Atmosphere extends to ~600 km.
    BallisticAtmosphere(
        body="titan",
        surface_gravity_m_s2=1.352,
        body_radius_km=2574.7,
        rho_0_kg_m3=5.43,
        scale_height_m=20000.0,
        atmosphere_top_km=600.0,
        has_atmosphere=True,
        precision_flag=PRECISION_HIGH,
        notes="Cassini-Huygens HASI direct-descent measurements (Fulchignoni "
              "2005). Cold 94 K N2 atmosphere; surface ρ four times Earth's. "
              "Cross-references v0.20.2 fluid_instrument.",
        source_key="fulchignoni_2005",
    ),

    # ---- Luna (Moon) — vacuum / airless -----------------------------
    BallisticAtmosphere(
        body="luna",
        surface_gravity_m_s2=1.625,
        body_radius_km=1737.4,
        rho_0_kg_m3=0.0,
        scale_height_m=0.0,
        atmosphere_top_km=0.0,
        has_atmosphere=False,
        precision_flag=PRECISION_HIGH,
        notes="Vacuum-trajectory case. Trace exosphere (10⁻¹⁵ kg/m³) "
              "negligible for ballistic propagation.",
        source_key="nasa_planetary_factsheet",
    ),

    # ---- Mercury — vacuum / airless ----------------------------------
    BallisticAtmosphere(
        body="mercury",
        surface_gravity_m_s2=3.70,
        body_radius_km=2439.7,
        rho_0_kg_m3=0.0,
        scale_height_m=0.0,
        atmosphere_top_km=0.0,
        has_atmosphere=False,
        precision_flag=PRECISION_HIGH,
        notes="Vacuum-trajectory case. Sodium exosphere (10⁻¹² kg/m³) "
              "negligible for ballistic propagation.",
        source_key="nasa_planetary_factsheet",
    ),

    # ---- Jupiter — 1-bar reference -----------------------------------
    # 1-bar ρ ~ 0.16 kg/m³, H ~ 27 km (large because hot H2/He +
    # high g). Gas giant convention from v0.20.2.
    BallisticAtmosphere(
        body="jupiter",
        surface_gravity_m_s2=24.79,
        body_radius_km=69911.0,
        rho_0_kg_m3=0.16,
        scale_height_m=27000.0,
        atmosphere_top_km=5000.0,
        has_atmosphere=True,
        precision_flag=PRECISION_MEDIUM,
        notes="1-bar reference level (gas giant convention from "
              "v0.20.2). Ballistic trajectories on gas giants are "
              "academic; no solid surface to land on.",
        source_key="seiff_1998_galileo_probe",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "us_standard_atmosphere_1976": (
        "U.S. Standard Atmosphere 1976. NOAA / NASA / USAF, "
        "NOAA-S/T 76-1562. Sea-level reference + exponential-fit "
        "scale height through troposphere/stratosphere."
    ),
    "tewari_2011": (
        "Tewari A. (2011). Atmospheric and Space Flight Dynamics. "
        "Birkhäuser. Body-parameterized exponential-atmosphere fits "
        "for Mars / Venus / Titan ballistic propagation."
    ),
    "seiff_1985_vira": (
        "Seiff A. et al. (1985). Models of the structure of the "
        "atmosphere of Venus from the surface to 100 km. "
        "Adv. Space Res. 5, 3-58. Venus International Reference "
        "Atmosphere (VIRA)."
    ),
    "fulchignoni_2005": (
        "Fulchignoni M. et al. (2005). In situ measurements of the "
        "physical characteristics of Titan's environment. Nature 438, "
        "785-791. DOI: 10.1038/nature04314 (Cassini-Huygens HASI)."
    ),
    "nasa_planetary_factsheet": (
        "Williams D. R. NASA Planetary Fact Sheet. "
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/ "
        "(canonical g, R values for all Solar-System bodies)."
    ),
    "seiff_1998_galileo_probe": (
        "Seiff A. et al. (1998). Thermal structure of Jupiter's "
        "atmosphere near the edge of a 5-µm hot spot in the north "
        "equatorial belt. JGR 103, 22857-22889. Galileo probe direct "
        "measurements at 1-bar reference level."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "BALLISTIC_ATMOSPHERES",
    "SOURCES",
    "BallisticAtmosphere",
]
