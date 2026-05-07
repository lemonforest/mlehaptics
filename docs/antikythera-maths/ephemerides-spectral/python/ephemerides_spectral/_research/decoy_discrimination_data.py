"""Decoy Discrimination Catalog — BC-differential physics constants
for the v0.22.0 ship.

Real, sourced data for **Layer C(b)** of the trajectory + sensing
surface — the only midcourse-surviving discriminator: the
**ballistic-coefficient differential** in the upper atmospheric drag
tail.

Physics
-------
A ballistic missile defense engagement has three discrimination
phases:

* **Boost** (~0-5 min): rocket plume IR; heavy with countermeasures;
  exo-atmospheric debris/decoy not yet deployed.
* **Midcourse** (~5-30 min): vacuum environment; warhead and decoys
  are **indistinguishable** by trajectory alone — heavy compact RV
  and lightweight balloon decoy follow identical Kepler ellipses
  in vacuum. Visual / radar discrimination is highly defeatable.
* **Re-entry** (~30 min onwards, below ~100 km): atmospheric
  re-entry. The ballistic coefficient (BC = m/(C_d·A)) drives
  deceleration. Heavy compact RV (BC ~5000-15000 kg/m²)
  decelerates **slowly** in the upper atmosphere; light decoys
  (BC ~10-50 kg/m²) decelerate **rapidly** in the same upper
  atmospheric tail.

This separation in the 60-100 km altitude band is the **only
publishable physics-based midcourse-surviving discrimination
mechanism** (Sessler/UCS *Countermeasures* 2000). Below ~60 km, the
decoys have effectively decelerated to terminal velocity (~50 m/s)
while the warhead is still at ~5-7 km/s — they're separated by
megameters of trajectory by then.

The Allen-Eggers ballistic re-entry solution gives the closed-form
velocity-vs-altitude relation. Differentiating between two BCs
yields the **discrimination altitude** — the altitude at which the
velocity gap opens up enough to be measurable.

Coverage notes (v0.22.0)
------------------------
4 reference BC classes from open-literature missile-defense physics:

* **Heavy_RV** — compact warhead, BC ~10000 kg/m².
* **Light_RV** — older / lighter warhead, BC ~3000 kg/m².
* **Replica_decoy** — anti-simulant balloon decoy, BC ~50 kg/m².
* **Chaff_decoy** — lightweight reflector strip, BC ~10 kg/m².

These are textbook open-literature class baselines from Sessler/UCS
2000. **No specific weapon-system BCs, no specific decoy designs, no
operational discrimination algorithm parameters.** Publishable physics
only.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Earth atmospheric reference (matches Layer A for consistency) ----
DEFAULT_RHO_0_KG_M3: float = 1.225
DEFAULT_SCALE_HEIGHT_M: float = 8500.0
DEFAULT_DISCRIMINATION_BAND_LOWER_KM: float = 60.0
DEFAULT_DISCRIMINATION_BAND_UPPER_KM: float = 100.0


@dataclass(frozen=True)
class BCReferenceClass:
    """Open-literature reference ballistic-coefficient class.

    Stores a textbook reference BC for a class of midcourse object
    (heavy RV / light RV / replica decoy / chaff). NOT specific
    weapon-system parameters — these are the open-literature class
    baselines used as sanity-check fixtures for the BC-differential
    discrimination physics.
    """
    class_name: str
    typical_bc_kg_m2: float
    typical_mass_kg: float       # Reference mass (kg)
    typical_diameter_m: float    # Reference diameter (m)
    drag_coefficient: float      # C_d for the canonical shape
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Reference BC classes (open literature, NOT specific systems)
# ---------------------------------------------------------------------------

BC_REFERENCE_CLASSES: List[BCReferenceClass] = [

    # ---- Heavy compact RV --------------------------------------------
    BCReferenceClass(
        class_name="heavy_rv",
        typical_bc_kg_m2=10000.0,
        typical_mass_kg=200.0,
        typical_diameter_m=0.45,
        drag_coefficient=0.10,
        precision_flag=PRECISION_MEDIUM,
        notes="Heavy compact re-entry vehicle class. Open-literature "
              "BC ~5000-15000 kg/m² (Sessler/UCS 2000 Table 8.1). "
              "Designed for steep re-entry with minimal upper-"
              "atmospheric deceleration.",
        source_key="sessler_ucs_2000",
    ),

    # ---- Light / older RV --------------------------------------------
    BCReferenceClass(
        class_name="light_rv",
        typical_bc_kg_m2=3000.0,
        typical_mass_kg=200.0,
        typical_diameter_m=0.6,
        drag_coefficient=0.20,
        precision_flag=PRECISION_MEDIUM,
        notes="Lighter or older RV class. BC ~2000-4000 kg/m². Higher "
              "drag at peak deceleration but still warhead-class for "
              "discrimination purposes.",
        source_key="sessler_ucs_2000",
    ),

    # ---- Replica decoy (anti-simulant balloon) ----------------------
    BCReferenceClass(
        class_name="replica_decoy",
        typical_bc_kg_m2=50.0,
        typical_mass_kg=10.0,
        typical_diameter_m=1.0,
        drag_coefficient=1.0,
        precision_flag=PRECISION_LOW,
        notes="Anti-simulant balloon decoy class. BC ~10-100 kg/m² "
              "depending on inflation + skin material. Mimics warhead "
              "in vacuum (mid-course), decelerates rapidly on entry.",
        source_key="sessler_ucs_2000",
    ),

    # ---- Chaff / light reflector ------------------------------------
    BCReferenceClass(
        class_name="chaff_decoy",
        typical_bc_kg_m2=10.0,
        typical_mass_kg=0.05,
        typical_diameter_m=0.1,
        drag_coefficient=2.0,
        precision_flag=PRECISION_LOW,
        notes="Lightweight chaff strip / metallised film. BC ~5-20 "
              "kg/m². Decelerates immediately on encountering "
              "atmosphere; first to drop out of decoy cloud.",
        source_key="sessler_ucs_2000",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "sessler_ucs_2000": (
        "Sessler A. M., Cornwall J. M., Dietz B., Fetter S., Frankel S., "
        "et al. (2000). Countermeasures: A Technical Evaluation of the "
        "Operational Effectiveness of the Planned US National Missile "
        "Defense System. Union of Concerned Scientists / MIT Security "
        "Studies Program. The canonical decoy-discrimination physics "
        "reference; Table 8.1 BC class ranges."
    ),
    "allen_eggers_1958": (
        "Allen H. J., Eggers A. J. (1958). A study of the motion and "
        "aerodynamic heating of ballistic missiles entering the "
        "Earth's atmosphere at high supersonic speeds. NACA Report "
        "1381. Closed-form ballistic re-entry velocity-vs-altitude."
    ),
    "wilkening_2000": (
        "Wilkening D. A. (2000). A Simple Model for Calculating "
        "Ballistic Missile Defense Effectiveness. Science & Global "
        "Security 8, 183-215."
    ),
    "postol_1991": (
        "Postol T. A. (1991/92). Lessons of the Gulf War Experience "
        "with Patriot. International Security 16:3. Foundational paper "
        "on the limits of midcourse discrimination."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "DEFAULT_RHO_0_KG_M3",
    "DEFAULT_SCALE_HEIGHT_M",
    "DEFAULT_DISCRIMINATION_BAND_LOWER_KM",
    "DEFAULT_DISCRIMINATION_BAND_UPPER_KM",
    "BC_REFERENCE_CLASSES",
    "SOURCES",
    "BCReferenceClass",
]
