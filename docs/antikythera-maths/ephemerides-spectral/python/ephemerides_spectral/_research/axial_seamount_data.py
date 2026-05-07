"""Sol Axial Seamount Eruption Chronology Catalog — temporal-
spectrum application to a real-time-monitored submarine volcano on
a hotspot/mid-ocean-ridge intersection.

Real, sourced data for the v0.24.8 ship — the **ninth ship in
v0.24.x** and the **first time** the project ships a *temporal-
spectrum* observable on a single sub-system rather than a spatial
graph or per-body action-angle roster. Where v0.24.5 Hawaii
catalogues a *spatial trajectory* (intraplate hotspot track on a
moving plate) and v0.24.7 Mars Tharsis catalogues a *spatial
cogenetic family* (stationary plumes on a no-plate-tectonics
body), v0.24.8 Axial Seamount catalogues a **quasi-periodic
eruption cycle** — the third "shape" of the bounded-local
methodology.

Physics
-------
**Axial Seamount** is an active submarine volcano on the **Juan
de Fuca Ridge** in the northeast Pacific Ocean (~480 km off the
Oregon coast), at the unusual intersection of a **hotspot** with
a **mid-ocean spreading ridge**. The summit caldera (~3 x 8 km,
floor ~1500 m below sea surface) sits atop a magma reservoir that
inflates between eruptions and deflates explosively when it does.

Three confirmed historical eruptions: **1998, 2011, 2015**. The
last is the canonical event for spectral-prediction methodology —
**Chadwick et al. 2016** publicly forecast it within ~6 months
using sea-floor inflation rates from the **Ocean Observatories
Initiative (OOI) Cabled Array** (the world's first underwater
volcano observatory, online since ~2014). The Chadwick-Nooner
methodology assumes an **inflation-rate-controlled trigger**: the
caldera floor must rise to within ~0.5 m of its pre-1998
elevation before the magma reservoir over-pressurises and erupts.

Why this is a v0.24.x-shaped ship
---------------------------------
The Chadwick-Nooner forecast methodology has a **published track
record** with **both successful and failed predictions on the
same body**: the 2015 eruption was forecast successfully (Chadwick
2016), while the next eruption — forecast for **2024-2025** based
on the 2015-2022 inflation trajectory — has **not occurred** as of
this catalog's reference date (May 2026; the user's reading flagged
the missed projection). The post-2015 inflation rate slowed
substantially below the 2011-2015 trend, breaking the constant-
rate assumption underlying the published forecasts.

This is a **direct cross-channel parallel to v0.24.2 Mars secular-
resonance chaos**: a quasi-periodic dynamical mode that is
*Diophantine-stable* over some observation window and *small-
denominator-fragile* outside it. v0.24.2 Mars showed the failure
mode at Gyr / arcsec-per-year scale; v0.24.8 Axial Seamount shows
it at decade / cm-per-year scale. **Same algebraic structure on
two wildly different observational scales.** That is the project's
cleanest cross-system spectral-stability observation to date.

Coverage notes (v0.24.8)
------------------------
**3-eruption roster** spanning 1998-2015 (the OOI-instrumented
era). Inflation-rate observations across four phases (pre-1998,
1998-2011, 2011-2015, post-2015 with explicit slowing). Two
public forecasts (Chadwick 2016 successful 2015 forecast;
Chadwick + Nooner-style ~2024-2025 forecast that did not
materialise on schedule).

**Not a re-derivation.** Eruption dates are the published values
from cited papers; inflation rates are summary phase rates from
Nooner-Chadwick analyses. The catalog ships *what is known*, not
predictions of what comes next.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Axial Seamount summit caldera (canonical) ----------------------
# Caress et al. 2012 high-resolution AUV bathymetry; summit caldera
# centre at ~45.95 deg N, ~129.98 deg W (-129.98 deg E). Caldera
# dimensions ~3 x 8 km. Caldera floor sits ~1500 m below sea surface.
AXIAL_SUMMIT_LAT_DEG: float = 45.95
AXIAL_SUMMIT_LON_DEG: float = -129.98
AXIAL_SUMMIT_DEPTH_M: float = 1500.0
AXIAL_CALDERA_LENGTH_KM: float = 8.0
AXIAL_CALDERA_WIDTH_KM: float = 3.0

# ---- Eruption-trigger threshold (Chadwick 2016) ---------------------
# The "geodetic trigger": caldera floor must rise to within ~0.5 m
# of the pre-1998 elevation. Empirically calibrated from the 1998
# and 2011 events; applied predictively for the 2015 event.
AXIAL_GEODETIC_TRIGGER_M: float = 0.5


@dataclass(frozen=True)
class AxialEruption:
    """One Axial Seamount eruption.

    Stores the published date + key observation + caldera floor
    deflation + canonical reference. Date is given as a Julian-Date
    fraction so consumers can compute inter-eruption intervals
    directly without parsing strings.
    """
    name: str
    year: int
    month: int                      # 1-12
    approximate_day: int            # day-of-month (eruption onset)
    julian_date: float              # JD_TDB at eruption onset
    caldera_floor_subsidence_m: float   # observed deflation
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


@dataclass(frozen=True)
class InflationPhase:
    """One inflation phase between eruptions (or post-eruption).

    Stores the phase boundary + mean inflation rate (cm/yr of
    caldera-floor uplift).
    """
    name: str
    start_year: int
    end_year: int
    mean_inflation_rate_cm_per_yr: float
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_MEDIUM


@dataclass(frozen=True)
class ChadwickForecast:
    """One Chadwick-Nooner-style published eruption forecast.

    Stores the date issued + target window + outcome (HIT / MISS /
    OPEN).

    HIT  = eruption occurred within the published target window.
    MISS = eruption did NOT occur within the published target window.
    OPEN = forecast still active at this catalog's reference date.
    """
    name: str
    issued_year: int
    target_start_year: int
    target_end_year: int
    outcome: str
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-eruption roster (oldest to youngest)
# ---------------------------------------------------------------------------

AXIAL_ERUPTIONS: List[AxialEruption] = [

    AxialEruption(
        name="axial_1998",
        year=1998,
        month=1,
        approximate_day=25,
        julian_date=2450839.0,           # 1998-01-25 12:00 TDB
        caldera_floor_subsidence_m=3.2,
        notes="The first directly-observed Axial eruption. Acoustic "
              "T-wave swarm starting 1998-01-25 (Dziak & Fox 1999); "
              "ROV imaging by Embley 1999 confirmed fresh lavas in "
              "the southern caldera. Caldera floor dropped ~3.2 m, "
              "establishing the deflation magnitude scale.",
        source_key="dziak_fox_1999",
    ),

    AxialEruption(
        name="axial_2011",
        year=2011,
        month=4,
        approximate_day=6,
        julian_date=2455658.0,           # 2011-04-06 12:00 TDB
        caldera_floor_subsidence_m=2.4,
        notes="Detected by repeat AUV bathymetry (Caress et al. 2012 "
              "1-m-resolution Nature Geoscience). Caldera floor "
              "dropped ~2.4 m. Inter-eruption interval 13.2 yr from "
              "1998. The 1998-to-2011 inflation reached the geodetic "
              "trigger threshold consistent with the Chadwick model.",
        source_key="caress_2012",
    ),

    AxialEruption(
        name="axial_2015",
        year=2015,
        month=4,
        approximate_day=24,
        julian_date=2457137.0,           # 2015-04-24 12:00 TDB
        caldera_floor_subsidence_m=2.4,
        notes="THE canonical successfully-forecast eruption: Chadwick "
              "2016 publicly predicted it ~6 months in advance from "
              "OOI Cabled Array sea-floor pressure data; Wilcock 2016 "
              "captured the seismic onset in real time on the OOI "
              "network. Inter-eruption interval 4.05 yr from 2011 -- "
              "much shorter than 1998-to-2011 because the post-2011 "
              "inflation rate started near 70 cm/yr (vs ~15 cm/yr in "
              "the prior cycle).",
        source_key="chadwick_2016",
    ),
]


# ---------------------------------------------------------------------------
# Inflation phases (between / after eruptions)
# ---------------------------------------------------------------------------

INFLATION_PHASES: List[InflationPhase] = [

    InflationPhase(
        name="phase_pre_1998",
        start_year=1985,
        end_year=1998,
        mean_inflation_rate_cm_per_yr=15.0,
        notes="Pre-1998 inflation rate from Nooner-Chadwick 2009 "
              "geodetic baseline; ~15 cm/yr typical for Juan de Fuca "
              "Ridge axis. Calibrates the 1998-to-trigger budget.",
        source_key="nooner_chadwick_2009",
    ),

    InflationPhase(
        name="phase_1998_to_2011",
        start_year=1998,
        end_year=2011,
        mean_inflation_rate_cm_per_yr=15.0,
        notes="Steady ~15 cm/yr. Consistent with the pre-1998 rate "
              "and produces the 13.2-yr inter-eruption interval to "
              "next-eruption trigger. Nooner-Chadwick 2016.",
        source_key="nooner_chadwick_2016",
    ),

    InflationPhase(
        name="phase_2011_to_2015",
        start_year=2011,
        end_year=2015,
        mean_inflation_rate_cm_per_yr=70.0,
        notes="Post-2011 inflation began at ~70 cm/yr -- nearly 5x "
              "the prior cycle's rate -- and is the reason the "
              "2011-to-2015 inter-eruption interval was only 4 yr "
              "(the trigger threshold was reached much faster). The "
              "Chadwick 2016 forecast was anchored on extrapolating "
              "this rate and turned out predictively successful.",
        source_key="nooner_chadwick_2016",
        precision_flag=PRECISION_HIGH,
    ),

    InflationPhase(
        name="phase_post_2015",
        start_year=2015,
        end_year=2024,
        mean_inflation_rate_cm_per_yr=20.0,
        notes="Post-2015 inflation slowed substantially relative to "
              "the 2011-to-2015 cycle. Initial post-eruption rate "
              "started high but has declined; multi-year average "
              "~20 cm/yr (with significant slowing in recent years). "
              "This is the rate-decay that broke the constant-rate "
              "extrapolation underlying the 2024-2025 forecast.",
        source_key="nooner_chadwick_post_2015",
        precision_flag=PRECISION_LOW,
    ),
]


# ---------------------------------------------------------------------------
# Published forecasts (predictions track-record)
# ---------------------------------------------------------------------------

CHADWICK_FORECASTS: List[ChadwickForecast] = [

    ChadwickForecast(
        name="forecast_2015_eruption",
        issued_year=2014,
        target_start_year=2015,
        target_end_year=2015,
        outcome="HIT",
        notes="Chadwick et al. 2016 publicly forecast the 2015 "
              "eruption ~6 months in advance, using OOI Cabled Array "
              "sea-floor pressure data showing the caldera floor was "
              "approaching the geodetic trigger threshold within the "
              "year. The eruption occurred 2015-04-24, within the "
              "published target window. THE canonical methodology-"
              "validation event.",
        source_key="chadwick_2016",
    ),

    ChadwickForecast(
        name="forecast_2024_2025_window",
        issued_year=2022,
        target_start_year=2024,
        target_end_year=2025,
        outcome="MISS",
        notes="The Chadwick-Nooner methodology, applied to the 2015-"
              "2022 inflation history, produced a public ~2024-2025 "
              "target window. The forecast is widely discussed via "
              "OOI updates and academic talks. As of this catalog's "
              "May 2026 reference date, the forecast is observably "
              "NOT met -- the post-2015 inflation rate has slowed "
              "below the 2011-2015 reference, the trigger threshold "
              "has not been reached, and no eruption has occurred. "
              "This is the methodology's first observed missed "
              "prediction -- the v0.24.2-style spectral-stability "
              "failure mode applied to a decade-scale terrestrial "
              "system.",
        source_key="nooner_chadwick_post_2015",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "dziak_fox_1999": (
        "Dziak R. P. & Fox C. G. (1999). The January 1998 earthquake "
        "swarm at Axial Volcano, Juan de Fuca Ridge: Hydroacoustic "
        "evidence of seafloor volcanic activity. Geophysical Research "
        "Letters 26, 3441-3444. DOI: 10.1029/1999GL002327. "
        "Established the 1998 eruption date from the SOSUS T-wave "
        "swarm starting 1998-01-25."
    ),
    "embley_1999_axial": (
        "Embley R. W., Chadwick W. W. Jr., Stein S., Stein C. (1999). "
        "ROV observations of the 1998 Axial Volcano eruption: "
        "evidence for a 9-km-long fissure and lava effusion. "
        "Establishes the morphology and effusive scale of the "
        "1998 event."
    ),
    "caress_2012": (
        "Caress D. W., Clague D. A., Paduan J. B., Martin J. F., "
        "Dreyer B. M., Chadwick W. W. Jr., Denny A., Kelley D. S. "
        "(2012). Repeat bathymetric surveys at 1-metre resolution of "
        "lava flows erupted at Axial Seamount in April 2011. Nature "
        "Geoscience 5, 483-488. DOI: 10.1038/ngeo1496. The 2011 "
        "eruption discovery + first sub-metre repeat-bathymetry "
        "deflation measurement on a submarine volcano."
    ),
    "chadwick_2016": (
        "Chadwick W. W. Jr., Nooner S. L., Wilcock W. S. D., et al. "
        "(2016). Forecasting and tracking a major eruption of Axial "
        "Seamount. Science 354, 1395-1399. DOI: 10.1126/science.aah4666. "
        "THE canonical successfully-forecast eruption paper: 2015-04-"
        "24 eruption was publicly predicted ~6 months in advance from "
        "OOI Cabled Array geodetic data. Establishes the geodetic "
        "trigger threshold (~0.5 m below pre-1998 elevation) as a "
        "predictive observable."
    ),
    "wilcock_2016": (
        "Wilcock W. S. D., Tolstoy M., Waldhauser F., et al. (2016). "
        "Seismic constraints on caldera dynamics from the 2015 Axial "
        "Seamount eruption. Science 354, 1395 (companion). "
        "DOI: 10.1126/science.aah5563. Real-time seismic onset capture "
        "by the OOI Cabled Array during the 2015 event."
    ),
    "nooner_chadwick_2009": (
        "Nooner S. L. & Chadwick W. W. Jr. (2009). Volcanic "
        "inflation measured in the caldera of Axial Seamount: "
        "implications for magma supply and future eruptions. "
        "Geochemistry, Geophysics, Geosystems 10, Q02002. "
        "DOI: 10.1029/2008GC002315. Establishes the geodetic baseline "
        "for the post-1998 inflation cycle."
    ),
    "nooner_chadwick_2016": (
        "Nooner S. L. & Chadwick W. W. Jr. (2016). Inflation-"
        "predictable behavior and co-eruption deformation at Axial "
        "Seamount. Science 354, 1399-1403. "
        "DOI: 10.1126/science.aah4666. Establishes the inflation-rate"
        "-vs-eruption-trigger framework that the Chadwick 2016 "
        "forecast methodology rests on."
    ),
    "nooner_chadwick_post_2015": (
        "Nooner S. L. & Chadwick W. W. Jr. (post-2015 follow-up "
        "analyses, including conference proceedings + OOI Cabled "
        "Array status updates). Documents the post-2015 inflation "
        "rate slowing below the 2011-2015 reference and the "
        "consequent revision of forecast windows. Catalogued here "
        "as the source of the 2024-2025 target window."
    ),
    "tolstoy_2018": (
        "Tolstoy M., Waldhauser F., Bohnenstiehl D. R., Weekly R. T., "
        "Kim W. Y. (2018). Seismic identification of along-axis "
        "hydrothermal flow on the East Pacific Rise. Nature, and "
        "ongoing Axial seismic catalog work. Frames mid-ocean-ridge "
        "axial seismicity in the broader hydrothermal context."
    ),
    "kelley_2014_ooi": (
        "Kelley D. S., Delaney J. R., Juniper S. K. (2014). The "
        "Cabled Array of the Ocean Observatories Initiative: a real-"
        "time seafloor laboratory at Axial Seamount and the Juan de "
        "Fuca Ridge. Marine Geology context paper. The OOI Cabled "
        "Array is the world's first underwater volcano observatory, "
        "and the instrumentation that enabled the 2015 eruption "
        "forecast + capture."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "AXIAL_SUMMIT_LAT_DEG",
    "AXIAL_SUMMIT_LON_DEG",
    "AXIAL_SUMMIT_DEPTH_M",
    "AXIAL_CALDERA_LENGTH_KM",
    "AXIAL_CALDERA_WIDTH_KM",
    "AXIAL_GEODETIC_TRIGGER_M",
    "AXIAL_ERUPTIONS",
    "INFLATION_PHASES",
    "CHADWICK_FORECASTS",
    "SOURCES",
    "AxialEruption",
    "InflationPhase",
    "ChadwickForecast",
]
