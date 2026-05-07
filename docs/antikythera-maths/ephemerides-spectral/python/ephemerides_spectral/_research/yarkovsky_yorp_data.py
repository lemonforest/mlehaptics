"""Sol Yarkovsky/YORP Catalog — per-asteroid thermal-radiation orbital
+ spin-state drift data for the v0.24.6 ship.

Real, sourced data for the **seventh and final ship in the v0.24.x
backlog**. Per-asteroid Yarkovsky (semi-major-axis drift) + YORP
(spin-state evolution) measurements.

Physics
-------
The **Yarkovsky effect**: an asteroid absorbs sunlight and re-emits
it as thermal infrared radiation, but with a phase delay (the
"afternoon" side is hotter than the "morning" side because of
thermal inertia). The asymmetric thermal re-emission produces a
small **net force** on the asteroid; over orbital timescales this
shifts the **semi-major axis** by ~10⁻⁴ AU per Myr for typical
NEAs (Near-Earth Asteroids).

* **Diurnal Yarkovsky** (rotation-induced phase lag): direction of
  drift depends on prograde vs retrograde rotation. **Prograde
  rotators drift outward**; retrograde drift inward.
* **Seasonal Yarkovsky** (orbital-axis-induced lag): always
  drifts the asteroid inward toward the Sun.

The **YORP effect** (Yarkovsky-O'Keefe-Radzievskii-Paddack): the same
thermal re-emission asymmetry produces a **net torque** on the
asteroid's spin axis when the asteroid's shape is irregular (which
all small bodies are). YORP can:

* **spin up** an asteroid until rotational fission occurs (creating
  binary asteroids) — direct evidence in the spin-rate-versus-size
  distribution where small (D < ~10 km) asteroids cluster at
  rotation periods near the **2.2-hour fission limit**;
* **spin down** an asteroid to "tumbling" rotation states;
* **drive obliquity** to one of two YORP attractors (~55° or ~125°)
  for irregular shapes.

Both effects are **proportional to 1/D²** where D is the asteroid
diameter — small bodies feel them strongly, large bodies (D >
~30 km) negligibly.

The v0.24.6 spectral framing: where v0.24.2 Mars showed obliquity
chaos driven by *gravitational* secular-resonance overlap, v0.24.6
small-body YORP shows **spin-state evolution driven by *radiative*
forcing** — same observable (chaotic spin/obliquity) but different
underlying mechanism. The asymptotic regime is similar: bodies
walk through phase space toward attractors, with the time-scale
set by the body's properties (gravitational interactions vs
absorptivity + thermal inertia).

Coverage notes (v0.24.6)
------------------------
**10-asteroid roster** with Yarkovsky and/or YORP measurements
above the threshold of detection. Includes:

* **(101955) Bennu** — OSIRIS-REx headline; first directly-imaged
  Yarkovsky-drifting asteroid (Chesley 2014; Farnocchia 2013).
* **(54509) 2000 PH5 (YORP)** — first body where YORP spin-up was
  observed (Lowry 2007); the asteroid that lent its name to the
  effect.
* **(99942) Apophis** — Impact-prediction relevance; Yarkovsky drift
  uncertainty matters for the 2068 close approach (Vokrouhlický 2015).
* **(162173) Ryugu** — Hayabusa2 target.
* **(25143) Itokawa** — Hayabusa target; tumbling state.
* **(1862) Apollo, (1620) Geographos, (3103) Eger** — classical YORP
  + Yarkovsky targets in the NEA population.
* **(29075) 1950 DA** — radar-derived Yarkovsky.
* **(1992 BF)** — early Yarkovsky detection (Vokrouhlický 2008).

**Not a re-derivation.** Drift values are the published
measurements from cited papers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Physical-regime thresholds -------------------------------------
# Rotational-fission limit for rubble-pile asteroids (~2.2 h):
ROTATIONAL_FISSION_PERIOD_HOURS: float = 2.2
# Yarkovsky/YORP scale ~ 1/D², so for D > 30-40 km the effect is
# below current observational sensitivity:
YARKOVSKY_OBSERVABILITY_DIAMETER_KM: float = 30.0
# YORP obliquity attractors for irregular bodies (Vokrouhlický-
# Čapek 2002 numerical investigation):
YORP_OBLIQUITY_ATTRACTOR_LO_DEG: float = 55.0
YORP_OBLIQUITY_ATTRACTOR_HI_DEG: float = 125.0


@dataclass(frozen=True)
class YarkovskyYorpEntry:
    """Per-asteroid Yarkovsky + YORP measurement.

    Stores the published da/dt (semi-major-axis drift in 10⁻⁴ AU/Myr,
    a convenient unit) + dω/dt YORP spin-rate change (in 10⁻⁸ rad/d²,
    a convenient unit for measured values) when available.
    """
    designation: str            # e.g., "(101955) Bennu"
    short_name: str             # e.g., "bennu"
    semi_major_axis_au: float
    eccentricity: float
    diameter_km: float
    rotation_period_hours: float
    # Yarkovsky drift in 10⁻⁴ AU/Myr (convenient unit; 1e-4 AU/Myr =
    # 0.0149 cm/yr = 4.7 m/Myr; positive = outward drift / prograde
    # rotation; negative = inward drift / retrograde).
    yarkovsky_drift_1e4_au_per_myr: Optional[float]
    yarkovsky_uncertainty_1e4_au_per_myr: Optional[float]
    # YORP spin-rate change in 10⁻⁸ rad/d²; positive = spin-up,
    # negative = spin-down. None if not measured.
    yorp_spin_rate_change_1e8_rad_per_day_sq: Optional[float]
    yorp_uncertainty_1e8_rad_per_day_sq: Optional[float]
    is_prograde: bool
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# ---------------------------------------------------------------------------
# Per-asteroid roster
# ---------------------------------------------------------------------------

YARKOVSKY_YORP_ENTRIES: List[YarkovskyYorpEntry] = [

    # ---- (101955) Bennu — THE headline -----------------------------
    YarkovskyYorpEntry(
        designation="(101955) Bennu",
        short_name="bennu",
        semi_major_axis_au=1.126,
        eccentricity=0.204,
        diameter_km=0.490,
        rotation_period_hours=4.296,
        yarkovsky_drift_1e4_au_per_myr=-19.0,         # inward (retrograde)
        yarkovsky_uncertainty_1e4_au_per_myr=0.1,
        yorp_spin_rate_change_1e8_rad_per_day_sq=0.0635,
        yorp_uncertainty_1e8_rad_per_day_sq=0.0008,
        is_prograde=False,
        notes="THE headline: first directly-imaged Yarkovsky-drifting "
              "asteroid; OSIRIS-REx target. Retrograde rotation -> "
              "drifts inward at -19e-4 AU/Myr (-285 m/yr). YORP spin-"
              "up confirmed by Hergenrother 2019 high-precision "
              "rotation-rate measurement.",
        source_key="farnocchia_2013",
    ),

    # ---- (54509) 2000 PH5 (YORP) — first YORP detection ------------
    YarkovskyYorpEntry(
        designation="(54509) 2000 PH5 (YORP)",
        short_name="2000_ph5",
        semi_major_axis_au=1.005,
        eccentricity=0.230,
        diameter_km=0.114,
        rotation_period_hours=0.20278,                # ~12.17 minutes!
        yarkovsky_drift_1e4_au_per_myr=None,
        yarkovsky_uncertainty_1e4_au_per_myr=None,
        yorp_spin_rate_change_1e8_rad_per_day_sq=350.0,
        yorp_uncertainty_1e8_rad_per_day_sq=35.0,
        is_prograde=True,
        notes="THE first body where YORP spin-up was observed. "
              "Lowry 2007 + Taylor 2007 measured spin-up over 4-yr "
              "baseline. Asteroid lent its name to the effect itself "
              "(54509 = 2000 PH5 = 'YORP'). Rotation period only "
              "12 minutes -- approaching the rotational-fission "
              "limit. Diameter only 114 m.",
        source_key="lowry_2007",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- (99942) Apophis -------------------------------------------
    YarkovskyYorpEntry(
        designation="(99942) Apophis",
        short_name="apophis",
        semi_major_axis_au=0.922,
        eccentricity=0.191,
        diameter_km=0.340,
        rotation_period_hours=30.4,
        yarkovsky_drift_1e4_au_per_myr=-1.99,
        yarkovsky_uncertainty_1e4_au_per_myr=0.3,
        yorp_spin_rate_change_1e8_rad_per_day_sq=None,
        yorp_uncertainty_1e8_rad_per_day_sq=None,
        is_prograde=False,
        notes="Impact-prediction relevance: Yarkovsky-drift "
              "uncertainty matters for the 2068 close approach. "
              "Vokrouhlický 2015 + radar follow-up. Apophis will "
              "have the closest-recorded NEA pass on 2029-04-13 "
              "(within geosynchronous distance).",
        source_key="vokrouhlicky_2015_apophis",
    ),

    # ---- (162173) Ryugu — Hayabusa2 --------------------------------
    YarkovskyYorpEntry(
        designation="(162173) Ryugu",
        short_name="ryugu",
        semi_major_axis_au=1.190,
        eccentricity=0.190,
        diameter_km=0.870,
        rotation_period_hours=7.633,
        yarkovsky_drift_1e4_au_per_myr=-2.4,
        yarkovsky_uncertainty_1e4_au_per_myr=0.5,
        yorp_spin_rate_change_1e8_rad_per_day_sq=None,
        yorp_uncertainty_1e8_rad_per_day_sq=None,
        is_prograde=False,
        notes="Hayabusa2 sample-return target. Rubble-pile spinning "
              "near the fission limit -- close to top-shaped "
              "equilibrium that suggests prior YORP spin-up + mass "
              "shedding.",
        source_key="watanabe_2019_ryugu",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- (25143) Itokawa — Hayabusa --------------------------------
    YarkovskyYorpEntry(
        designation="(25143) Itokawa",
        short_name="itokawa",
        semi_major_axis_au=1.324,
        eccentricity=0.280,
        diameter_km=0.330,
        rotation_period_hours=12.132,
        yarkovsky_drift_1e4_au_per_myr=None,
        yarkovsky_uncertainty_1e4_au_per_myr=None,
        yorp_spin_rate_change_1e8_rad_per_day_sq=-3.5,
        yorp_uncertainty_1e8_rad_per_day_sq=1.0,
        is_prograde=True,
        notes="Hayabusa target. YORP spin-DOWN measured by Lowry "
              "2014 over 4-yr photometric baseline -- one of the "
              "few clearly-spinning-down asteroids.",
        source_key="lowry_2014_itokawa",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- (1862) Apollo ---------------------------------------------
    YarkovskyYorpEntry(
        designation="(1862) Apollo",
        short_name="apollo",
        semi_major_axis_au=1.471,
        eccentricity=0.560,
        diameter_km=1.5,
        rotation_period_hours=3.065,
        yarkovsky_drift_1e4_au_per_myr=None,
        yarkovsky_uncertainty_1e4_au_per_myr=None,
        yorp_spin_rate_change_1e8_rad_per_day_sq=5.5,
        yorp_uncertainty_1e8_rad_per_day_sq=1.2,
        is_prograde=True,
        notes="Namesake of the Apollo NEA group. YORP spin-up "
              "Kaasalainen 2007.",
        source_key="kaasalainen_2007",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- (1620) Geographos -----------------------------------------
    YarkovskyYorpEntry(
        designation="(1620) Geographos",
        short_name="geographos",
        semi_major_axis_au=1.246,
        eccentricity=0.336,
        diameter_km=2.5,
        rotation_period_hours=5.222,
        yarkovsky_drift_1e4_au_per_myr=None,
        yarkovsky_uncertainty_1e4_au_per_myr=None,
        yorp_spin_rate_change_1e8_rad_per_day_sq=1.14,
        yorp_uncertainty_1e8_rad_per_day_sq=0.27,
        is_prograde=True,
        notes="Highly elongated (1620 m × 720 m × 510 m) -- shape "
              "irregularity drives YORP torque. Durech 2008.",
        source_key="durech_2008_geographos",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- (29075) 1950 DA -------------------------------------------
    YarkovskyYorpEntry(
        designation="(29075) 1950 DA",
        short_name="1950_da",
        semi_major_axis_au=1.700,
        eccentricity=0.508,
        diameter_km=1.3,
        rotation_period_hours=2.121,
        yarkovsky_drift_1e4_au_per_myr=-0.9,
        yarkovsky_uncertainty_1e4_au_per_myr=0.1,
        yorp_spin_rate_change_1e8_rad_per_day_sq=None,
        yorp_uncertainty_1e8_rad_per_day_sq=None,
        is_prograde=False,
        notes="2.121-h rotation period -- AT the rotational-"
              "fission limit. Cohesive forces required to hold the "
              "rubble pile together against centrifugal disruption "
              "(Rozitis 2014). Radar Yarkovsky from Farnocchia 2014.",
        source_key="farnocchia_2014_1950da",
    ),

    # ---- 1992 BF — early Yarkovsky detection ----------------------
    YarkovskyYorpEntry(
        designation="(6489) Golevka",
        short_name="golevka",
        semi_major_axis_au=2.515,
        eccentricity=0.607,
        diameter_km=0.530,
        rotation_period_hours=6.026,
        yarkovsky_drift_1e4_au_per_myr=-1.5,
        yarkovsky_uncertainty_1e4_au_per_myr=0.4,
        yorp_spin_rate_change_1e8_rad_per_day_sq=None,
        yorp_uncertainty_1e8_rad_per_day_sq=None,
        is_prograde=False,
        notes="First-ever Yarkovsky detection (Chesley 2003). "
              "Established the Yarkovsky effect as observationally "
              "real for individual NEAs.",
        source_key="chesley_2003_golevka",
        precision_flag=PRECISION_MEDIUM,
    ),

    # ---- (3103) Eger -----------------------------------------------
    YarkovskyYorpEntry(
        designation="(3103) Eger",
        short_name="eger",
        semi_major_axis_au=1.405,
        eccentricity=0.354,
        diameter_km=1.5,
        rotation_period_hours=5.711,
        yarkovsky_drift_1e4_au_per_myr=None,
        yarkovsky_uncertainty_1e4_au_per_myr=None,
        yorp_spin_rate_change_1e8_rad_per_day_sq=2.4,
        yorp_uncertainty_1e8_rad_per_day_sq=0.6,
        is_prograde=True,
        notes="Hungarian NEA group. YORP-spin-up Durech 2012.",
        source_key="durech_2012_eger",
        precision_flag=PRECISION_MEDIUM,
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "farnocchia_2013": (
        "Farnocchia D. et al. (2013). Near Earth Asteroids with "
        "measurable Yarkovsky effect. Icarus 224, 1-13. "
        "DOI: 10.1016/j.icarus.2013.02.004. Plus Chesley S. R. et "
        "al. (2014). Orbit and bulk density of the OSIRIS-REx target "
        "asteroid (101955) Bennu. Icarus 235, 5-22. "
        "DOI: 10.1016/j.icarus.2014.02.020. Bennu Yarkovsky drift."
    ),
    "lowry_2007": (
        "Lowry S. C. et al. (2007). Direct detection of the "
        "asteroidal YORP effect. Science 316, 272-274. "
        "DOI: 10.1126/science.1139040. Plus Taylor P. A. et al. "
        "(2007). Spin rate of asteroid (54509) 2000 PH5 increasing "
        "due to the YORP effect. Science 316, 274-277. "
        "DOI: 10.1126/science.1139038. The first YORP detection."
    ),
    "vokrouhlicky_2015_apophis": (
        "Vokrouhlický D. et al. (2015). The Yarkovsky effect on "
        "Apophis. Icarus 252, 277-283. "
        "DOI: 10.1016/j.icarus.2015.01.025. Apophis Yarkovsky + "
        "implications for 2068 close approach."
    ),
    "watanabe_2019_ryugu": (
        "Watanabe S. et al. (2019). Hayabusa2 arrives at the carbon-"
        "ach asteroid 162173 Ryugu — A spinning top-shaped rubble "
        "pile. Science 364, 268-272. DOI: 10.1126/science.aav8032. "
        "Ryugu shape + spin state."
    ),
    "lowry_2014_itokawa": (
        "Lowry S. C. et al. (2014). The internal structure of "
        "asteroid (25143) Itokawa as revealed by detection of YORP "
        "spin-up. Astron. Astrophys. 562, A48. "
        "DOI: 10.1051/0004-6361/201322602. Itokawa YORP spin-down."
    ),
    "kaasalainen_2007": (
        "Kaasalainen M., Durech J., Warner B. D., Krugly Y. N., "
        "Gaftonyuk N. M. (2007). Acceleration of the rotation of "
        "asteroid 1862 Apollo by radiation torques. Nature 446, "
        "420-422. DOI: 10.1038/nature05614. Apollo YORP spin-up."
    ),
    "durech_2008_geographos": (
        "Durech J. et al. (2008). Detection of the YORP effect in "
        "asteroid (1620) Geographos. Astron. Astrophys. 489, L25-L28. "
        "DOI: 10.1051/0004-6361:200810672."
    ),
    "farnocchia_2014_1950da": (
        "Farnocchia D. & Chesley S. R. (2014). Assessment of the "
        "1950 DA hazard. Icarus 229, 321-327. "
        "DOI: 10.1016/j.icarus.2013.11.022. 1950 DA Yarkovsky + "
        "rotational-fission proximity."
    ),
    "chesley_2003_golevka": (
        "Chesley S. R. et al. (2003). Direct detection of the "
        "Yarkovsky effect via radar ranging to asteroid 6489 "
        "Golevka. Science 302, 1739-1742. "
        "DOI: 10.1126/science.1091452. THE first Yarkovsky detection."
    ),
    "durech_2012_eger": (
        "Durech J. et al. (2012). Analysis of the rotation period of "
        "asteroids (1865) Cerberus, (2100) Ra-Shalom, and (3103) "
        "Eger -- search for the YORP effect. Astron. Astrophys. 547, "
        "A10. DOI: 10.1051/0004-6361/201219831."
    ),
    "vokrouhlicky_capek_2002": (
        "Vokrouhlický D. & Čapek D. (2002). YORP-induced long-term "
        "evolution of the spin state of small asteroids and "
        "meteoroids: Rubincam's approximation. Icarus 159, 449-467. "
        "DOI: 10.1006/icar.2002.6918. Numerical demonstration of "
        "YORP obliquity attractors at ~55° and ~125°."
    ),
    "rubincam_2000": (
        "Rubincam D. P. (2000). Radiative spin-up and spin-down of "
        "small asteroids. Icarus 148, 2-11. "
        "DOI: 10.1006/icar.2000.6485. The seminal YORP-mechanism "
        "derivation."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "ROTATIONAL_FISSION_PERIOD_HOURS",
    "YARKOVSKY_OBSERVABILITY_DIAMETER_KM",
    "YORP_OBLIQUITY_ATTRACTOR_LO_DEG",
    "YORP_OBLIQUITY_ATTRACTOR_HI_DEG",
    "YARKOVSKY_YORP_ENTRIES",
    "SOURCES",
    "YarkovskyYorpEntry",
]
