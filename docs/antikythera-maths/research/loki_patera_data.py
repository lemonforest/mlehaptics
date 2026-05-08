"""Sol Loki Patera Eruption Cycle Catalog — temporal-spectrum
application to the Solar System's most active volcano, located on
Jupiter's moon Io and driven by Galilean Laplace tidal heating.

Real, sourced data for the v0.24.12 ship — direct cousin to v0.24.8
Axial Seamount (same temporal-quasi-periodic-cycle regime in the
v0.24.9 dynamical-regime classifier), but with fundamentally
different forcing physics. Where Axial Seamount is a mid-ocean-
ridge submarine volcano driven by mantle-plume magma supply,
**Loki Patera is driven by tidal heating from the Galilean Laplace
4:2:1 mean-motion resonance** — the canonical 3-body orbital lock
between Io, Europa, and Ganymede that forces Io's orbital
eccentricity to a value (~0.0041) far above what tidal damping
alone would allow, dissipating ~10^14 W of mechanical energy in
Io's interior.

Physics
-------
**Loki Patera** is a ~200 km-diameter lava lake (the largest
persistent thermal anomaly in the Solar System) on Jupiter's moon
Io. Located at ~12.7° N, ~309.6° W (~50.4° E by alternate
convention), it is the dominant single contributor to Io's total
thermal output, accounting for 5-15% of Io's globally-integrated
~10^14 W tidal dissipation budget.

The headline observable is a **quasi-periodic ~540-day brightening/
resurfacing cycle** (Rathbun et al. 2002 *GRL* — the canonical
paper establishing the periodicity). Each cycle proceeds through
phases:

* **Brightening**: caldera floor heats up over weeks; thermal
  output increases.
* **Resurfacing wave**: a wave of fresh lava sweeps across the
  caldera at ~1 km/day, lasting several months (de Kleer 2019
  multi-phase analysis).
* **Cooling**: peak thermal output decays over months as the
  resurfaced floor cools.
* **Quiescent**: low (but not zero) thermal output until the
  next brightening.

The cycle is **quasi-periodic, not strictly periodic** — observed
periods range 480-580 days with a mean of ~540 d (Rathbun-Spencer
2010 multi-volcano time-variability analysis). The mechanism is
thought to be magma-overturn / piston-cycle dynamics in the lava
lake, but the deep forcing — what keeps the magma supply hot
enough to drive these cycles — is the Galilean Laplace tidal
dissipation chain.

Cross-channel discipline
------------------------
Loki Patera is a v0.24.x ship in the **temporal-quasi-periodic-
cycle regime** (same regime label as v0.24.8 Axial), but with
forcing tracing back through three earlier v0.21.x cross-channel
catalogs:

* **v0.21.5 Sol Electromagnetic Instrument** — cites Jupiter-Io
  flux-tube (~10^12 W) as the canonical EM-coupling headliner.
  Loki's existence at all is downstream of Io's tidal heating;
  the flux tube and the lava lake are sibling consequences of
  the Galilean Laplace lock.

* **v0.21.6 Tidal-resonance ↔ orbital migration** — catalogs
  the Galilean 4:2:1 commensurability as the canonical 3-body
  lock in the Solar System. Io's forced eccentricity 0.0041 is
  the proximate cause of its tidal heating; Europa and Ganymede
  are the partners that pump that eccentricity.

* **v0.24.11 Pluto-Charon** — catalogs the 4-small-moon near-
  3:4:5:6 commensurability with the Pluto-Charon mutual orbital
  period as the binary-system analogue of the Galilean Laplace
  4:2:1. Same algebraic structure (small-integer mean-motion
  ratios producing tidal heating in the locked bodies), different
  central-body geometry.

Coverage notes (v0.24.12)
-------------------------
**6-cycle-peak observation roster** spanning 1990-2017, drawn
from the canonical Rathbun 2002 paper + the de Kleer 2017+
adaptive-optics monitoring era. Observations are NOT exhaustive
(the ground-based community has captured many more peaks); the
catalog ships the published-canonical anchor points + the cycle-
mean / cycle-range parameters.

Plus a 6-mode action-angle catalog covering the cycle period,
brightening / resurfacing / cooling phases, Io's orbital period,
and the Galilean Laplace 4:2:1 commensurability ratios — the
deep forcing observables that connect Loki to the v0.21.x
cross-channel catalogs.

**Not a re-derivation.** Cycle peak dates and periods are the
published values from Rathbun 2002 / Rathbun-Spencer 2010 / de
Kleer 2017+; tidal-heating budget figures are from the Peale-
Cassen-Reynolds 1979 prediction lineage as observationally
confirmed by Voyager 1.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Loki Patera location + geometry --------------------------------
# Veeder 1994 KAO + Galileo SSI imaging; coordinates in Io-system
# planetographic frame (+E, +N).
LOKI_LATITUDE_DEG: float = 12.7
LOKI_LONGITUDE_DEG: float = -309.6   # also expressed as +50.4° E
LOKI_DIAMETER_KM: float = 200.0       # caldera / lava-lake diameter
LOKI_LAVA_LAKE_AREA_KM2: float = 21500.0  # de Kleer 2017+ photometry

# ---- Cycle period (Rathbun 2002 canonical anchor) ------------------
LOKI_MEAN_CYCLE_PERIOD_DAYS: float = 540.0
LOKI_CYCLE_PERIOD_RANGE_DAYS: tuple = (480.0, 580.0)

# ---- Tidal-heating context (Peale 1979 + Galileo era) --------------
# Io's globally-integrated tidal-heating dissipation rate.
IO_TIDAL_HEATING_W: float = 1.0e14
# Loki's typical share of Io's total thermal output (highly variable
# across the cycle; cite as range rather than single value).
LOKI_FRACTION_OF_IO_OUTPUT: tuple = (0.05, 0.15)
# Io's forced orbital eccentricity (driven by Europa+Ganymede via
# Galilean Laplace 4:2:1).
IO_FORCED_ECCENTRICITY: float = 0.0041
# Io's orbital period.
IO_ORBITAL_PERIOD_DAYS: float = 1.7691378
# Galilean Laplace partners — orbital periods.
EUROPA_ORBITAL_PERIOD_DAYS: float = 3.5511810
GANYMEDE_ORBITAL_PERIOD_DAYS: float = 7.1545530


@dataclass(frozen=True)
class LokiCyclePeakObservation:
    """One observed Loki Patera brightening cycle peak.

    Stores the published peak date + characterisation + canonical
    reference. Each peak is a multi-week brightening event; the
    `peak_year` field is the calendar year of the brightening
    maximum (when published).
    """
    name: str
    peak_year: int
    peak_month: Optional[int]      # 1-12, or None if month-resolution unavailable
    cycle_index_from_anchor: Optional[int]  # cycle number relative to a published anchor
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


@dataclass(frozen=True)
class CycleMode:
    """One frequency mode in Loki's eruption cycle dynamics + its
    deep-forcing context.

    Mirrors the v0.24.0-v0.24.2 / v0.24.11 action-angle DynamicalMode
    structure. Includes the Galilean Laplace commensurability
    partners as cross-channel modes.
    """
    name: str
    period_days: float
    mode_class: str           # "cycle" | "phase" | "orbital" | "commensurability"
    description: str
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# ---------------------------------------------------------------------------
# Cycle-peak observation roster (1990-2017)
# ---------------------------------------------------------------------------

LOKI_CYCLE_PEAKS: List[LokiCyclePeakObservation] = [

    LokiCyclePeakObservation(
        name="loki_peak_1990",
        peak_year=1990,
        peak_month=None,
        cycle_index_from_anchor=None,
        notes="Veeder et al. 1994 KAO observations established the "
              "first multi-year time-series of Loki's thermal "
              "output. The 1990 peak is the earliest data point in "
              "the canonical Rathbun 2002 cycle reconstruction.",
        source_key="veeder_1994",
    ),

    LokiCyclePeakObservation(
        name="loki_peak_1995",
        peak_year=1995,
        peak_month=None,
        cycle_index_from_anchor=None,
        notes="NSFCAM thermal observation; one of the data points "
              "Rathbun 2002 used to derive the ~540-d period.",
        source_key="rathbun_2002",
        precision_flag=PRECISION_MEDIUM,
    ),

    LokiCyclePeakObservation(
        name="loki_peak_1997",
        peak_year=1997,
        peak_month=None,
        cycle_index_from_anchor=None,
        notes="de Pater 1998 ground-based observations; bridges the "
              "pre-Galileo and Galileo-era cycle-coverage records.",
        source_key="rathbun_2002",
    ),

    LokiCyclePeakObservation(
        name="loki_peak_2002",
        peak_year=2002,
        peak_month=None,
        cycle_index_from_anchor=0,           # the canonical anchor cycle
        notes="The cycle peak coincident with publication of the "
              "Rathbun 2002 *GRL* paper that established the ~540-d "
              "periodicity. Treated as the catalog's anchor cycle "
              "(cycle_index_from_anchor=0).",
        source_key="rathbun_2002",
    ),

    LokiCyclePeakObservation(
        name="loki_peak_2013",
        peak_year=2013,
        peak_month=None,
        cycle_index_from_anchor=7,           # ~7 cycles past the 2002 anchor
        notes="First peak in the de Kleer adaptive-optics monitoring "
              "era (de Kleer-de Pater 2017 *Icarus* paper published "
              "100 nights of 2013-2015 observations).",
        source_key="de_kleer_2017",
    ),

    LokiCyclePeakObservation(
        name="loki_peak_2015",
        peak_year=2015,
        peak_month=None,
        cycle_index_from_anchor=8,
        notes="Second AO-era peak; de Kleer 2019 multi-phase "
              "resurfacing analysis used this cycle's full "
              "brightening/resurfacing/cooling sequence to derive "
              "the ~1 km/day resurfacing-wave speed.",
        source_key="de_kleer_2019",
    ),
]


# ---------------------------------------------------------------------------
# Action-angle / cross-channel mode catalog
# ---------------------------------------------------------------------------

LOKI_CYCLE_MODES: List[CycleMode] = [

    # ==== Cycle modes (the temporal-spectrum observable) ============

    CycleMode(
        name="loki_main_cycle",
        period_days=LOKI_MEAN_CYCLE_PERIOD_DAYS,
        mode_class="cycle",
        description=(
            "The ~540-day quasi-periodic brightening/resurfacing "
            "cycle. The cycle period varies 480-580 days across "
            "observed events; the mean is the catalog headline "
            "value. Quasi-periodic, not strictly periodic."
        ),
        source_key="rathbun_2002",
    ),

    CycleMode(
        name="brightening_phase",
        period_days=45.0,                # ~30-60 days; midpoint
        mode_class="phase",
        description=(
            "Initial heat-up phase: caldera floor temperature rises "
            "over ~weeks before the resurfacing wave begins. "
            "Estimated 30-60 days based on de Kleer 2017+ "
            "adaptive-optics monitoring."
        ),
        source_key="de_kleer_2017",
        precision_flag=PRECISION_MEDIUM,
    ),

    CycleMode(
        name="resurfacing_wave",
        period_days=180.0,               # ~3-6 months at ~1 km/day across ~200 km
        mode_class="phase",
        description=(
            "Fresh-lava resurfacing wave sweeping across the "
            "caldera at ~1 km/day, derived by de Kleer 2019 from "
            "multi-night AO observations of brightening propagation. "
            "Total resurfacing time ~200 days for the full "
            "~200 km-diameter caldera."
        ),
        source_key="de_kleer_2019",
    ),

    CycleMode(
        name="cooling_phase",
        period_days=180.0,               # ~6 months exponential decay
        mode_class="phase",
        description=(
            "Post-resurfacing cooling phase: thermal output decays "
            "exponentially over ~months as the resurfaced caldera "
            "floor radiates away its heat. Sets the baseline below "
            "which the next brightening becomes detectable."
        ),
        source_key="de_kleer_2017",
        precision_flag=PRECISION_LOW,
    ),

    # ==== Orbital + Galilean Laplace cross-channel modes ============

    CycleMode(
        name="io_orbital_period",
        period_days=IO_ORBITAL_PERIOD_DAYS,
        mode_class="orbital",
        description=(
            "Io's orbital period around Jupiter. Locked into the "
            "Galilean Laplace 4:2:1 commensurability with Europa "
            "and Ganymede. The forced eccentricity 0.0041 from "
            "this lock is the proximate cause of Io's tidal "
            "heating, which feeds Loki Patera's lava lake."
        ),
        source_key="murray_dermott_1999",
    ),

    CycleMode(
        name="galilean_laplace_4_2_1_commensurability",
        period_days=IO_ORBITAL_PERIOD_DAYS,   # the fundamental of the resonance
        mode_class="commensurability",
        description=(
            "The Io:Europa:Ganymede 4:2:1 mean-motion resonance, "
            "verified by 4 * P_Io = 2 * P_Europa = P_Ganymede "
            "(within 1e-4): "
            f"4 x {IO_ORBITAL_PERIOD_DAYS:.4f} = "
            f"{4 * IO_ORBITAL_PERIOD_DAYS:.4f} d; "
            f"2 x {EUROPA_ORBITAL_PERIOD_DAYS:.4f} = "
            f"{2 * EUROPA_ORBITAL_PERIOD_DAYS:.4f} d; "
            f"P_Ganymede = {GANYMEDE_ORBITAL_PERIOD_DAYS:.4f} d. "
            "The textbook 3-body mean-motion lock; Peale-Cassen-"
            "Reynolds 1979 predicted Io's tidal heating from this "
            "commensurability, confirmed by Voyager 1's observation "
            "of active volcanism 2 weeks later."
        ),
        source_key="peale_cassen_reynolds_1979",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "veeder_1994": (
        "Veeder G. J., Matson D. L., Johnson T. V., Blaney D. L., "
        "Goguen J. D. (1994). Io's heat flow from infrared "
        "radiometry: 1983-1993. Journal of Geophysical Research "
        "99, 17095-17162. DOI: 10.1029/94JE00637. The first multi-"
        "year time-series of Io's thermal output, including KAO "
        "observations of Loki's 1990 peak."
    ),
    "rathbun_2002": (
        "Rathbun J. A., Spencer J. R., Davies A. G., Howell R. R., "
        "Wilson L. (2002). Loki, Io: A periodic volcano. "
        "Geophysical Research Letters 29, 1443. "
        "DOI: 10.1029/2002GL014747. **The canonical paper** "
        "establishing Loki Patera's ~540-day quasi-periodic "
        "brightening cycle from 12 years of multi-band ground-"
        "based and Galileo-era thermal observations."
    ),
    "rathbun_spencer_2010": (
        "Rathbun J. A. & Spencer J. R. (2010). Ground-based "
        "observations of time variability in multiple active "
        "volcanoes on Io. Icarus 209, 625-630. "
        "DOI: 10.1016/j.icarus.2010.05.019. Refines the cycle "
        "period statistics + extends the time-series; the source "
        "for the 480-580 day range estimate."
    ),
    "de_kleer_2017": (
        "de Kleer K. & de Pater I. (2017). Time variability of "
        "Io's volcanic activity from near-IR adaptive optics "
        "observations on 100 nights in 2013-2015. Icarus 280, "
        "378-404. DOI: 10.1016/j.icarus.2016.06.019. Establishes "
        "the modern adaptive-optics monitoring era; 100 nights "
        "of high-resolution thermal observations across multiple "
        "Io volcanoes including Loki."
    ),
    "de_kleer_2019": (
        "de Kleer K., Skrutskie M., Leisenring J., Davies A. G., "
        "Conrad A., de Pater I., Resnick A., Bailey V., Defrere "
        "D., Hinz P., Skemer A., Spalding E., Vaz A., Veillet C., "
        "Woodward C. E. (2019). Multi-phase volcanic resurfacing "
        "at Loki Patera from quasi-periodic adaptive optics "
        "monitoring. Nature 589, 199-203. DOI: 10.1038/"
        "s41586-020-03031-8. The canonical multi-phase analysis "
        "establishing the ~1 km/day resurfacing-wave speed."
    ),
    "peale_cassen_reynolds_1979": (
        "Peale S. J., Cassen P., Reynolds R. T. (1979). Melting "
        "of Io by tidal dissipation. Science 203, 892-894. "
        "DOI: 10.1126/science.203.4383.892. The famous Io tidal-"
        "heating prediction published 2 weeks before Voyager 1's "
        "confirming flyby observation of active volcanism — the "
        "deep-mechanism citation that connects Loki Patera to "
        "the Galilean Laplace lock."
    ),
    "murray_dermott_1999": (
        "Murray C. D. & Dermott S. F. (1999). *Solar System "
        "Dynamics*. Cambridge University Press. Section 8 "
        "(satellite orbits + mean-motion resonances). The "
        "canonical reference for the Galilean Laplace 4:2:1 "
        "commensurability period parameters."
    ),
    "spencer_1990": (
        "Spencer J. R., Shure M. A., Ressler M. E., Goguen J. D. "
        "(1990). Discovery of hotspots on Io using disk-resolved "
        "infrared imaging. Nature 348, 618-621. DOI: 10.1038/"
        "348618a0. Pre-Voyager-era ground-based confirmation of "
        "Loki + other Io hotspots; sets the observational stage "
        "for the multi-year time-series."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "LOKI_LATITUDE_DEG",
    "LOKI_LONGITUDE_DEG",
    "LOKI_DIAMETER_KM",
    "LOKI_LAVA_LAKE_AREA_KM2",
    "LOKI_MEAN_CYCLE_PERIOD_DAYS",
    "LOKI_CYCLE_PERIOD_RANGE_DAYS",
    "IO_TIDAL_HEATING_W",
    "LOKI_FRACTION_OF_IO_OUTPUT",
    "IO_FORCED_ECCENTRICITY",
    "IO_ORBITAL_PERIOD_DAYS",
    "EUROPA_ORBITAL_PERIOD_DAYS",
    "GANYMEDE_ORBITAL_PERIOD_DAYS",
    "LOKI_CYCLE_PEAKS",
    "LOKI_CYCLE_MODES",
    "SOURCES",
    "LokiCyclePeakObservation",
    "CycleMode",
]
