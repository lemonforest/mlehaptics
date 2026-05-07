"""Sol Volcanic Outgassing Catalog — per-body volcanic outgassing ↔
atmospheric composition cross-channel coupling.

Real, sourced data for the v0.21.9 ship — the **ninth cross-channel
coupling surface** in the §17.4.2 v0.21.x sequence (after v0.21.8
heat flow ↔ tidal heating).

Physics
-------
Volcanic outgassing rate sets atmospheric-inventory dynamics through
steady-state mass balance:

    outgassing_rate (SOURCE) = escape_rate (SINK from v0.21.7)
                              + sequestration_rate (frost, weathering,
                                ocean dissolution)

Inventory stable iff source ≈ sink. The cross-channel observation:
**v0.21.7 escape + v0.21.9 outgassing form the supply-and-demand
sides of atmospheric mass balance**. v0.21.8 heat flow provides the
energy budget that drives outgassing in the first place.

For Io: the closure is particularly clean. v0.21.8's 100 TW tidal
heating drives volcanism → 1 ton/s SO₂ outgassing (Lellouch 2007) →
Jupiter Io plasma torus injection at ~1 ton/s of S+/O+ → v0.21.7's
1000 kg/s Jupiter pickup-ion escape. **Three observational handles
on the same Io→Jupiter mass-transfer pipeline.**

Coverage notes (v0.21.9)
------------------------
6 bodies with peer-reviewed measured volcanic outgassing rates:

- terra (Burton 2013 subaerial + Plank 2019 submarine CO₂ flux).
- mars (Halevy & Head 2014 early-Mars volcanism estimate; modern
  rate effectively zero).
- venus (Bullock & Grinspoon 2001 model + Marcq 2018 EUV-spectroscopy
  upper limits on modern flux).
- io (Lellouch 2007 / Spencer 2007 SO₂ frost-volcano-atmosphere
  steady state — the headline).
- enceladus (Hansen 2011 Cassini INMS plume H₂O flux).
- jupiter (Bagenal 2007 Io plasma torus injection — the Jovian
  "outgassing" via Io's volcanism).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Source-mechanism labels -----------------------------------------
SRC_SUBAERIAL_VOLCANISM: str = "subaerial_volcanism"     # terra
SRC_SUBMARINE_VOLCANISM: str = "submarine_volcanism"      # terra
SRC_TIDAL_VOLCANISM: str = "tidal_volcanism"              # io
SRC_PLUME_VENTING: str = "plume_venting"                  # enceladus
SRC_MAGNETOSPHERIC_INJECTION: str = "magnetospheric_injection"  # jupiter via io
SRC_DORMANT: str = "dormant"                              # mars present-day


@dataclass(frozen=True)
class VolcanicOutgassing:
    """Per-body volcanic-outgassing ↔ atmospheric-composition coupling.

    Stores the published outgassing rate in kg/s + dominant outgassed
    species + source mechanism + escape-balance flag. Cross-references
    v0.21.7 atmospheric escape (sink) and v0.21.8 heat flow (energy).
    """
    body: str
    # Outgassing rate (kg/s). For "dormant" bodies (modern Mars), the
    # value is the integrated upper limit, not zero.
    outgassing_rate_kg_per_s: float
    # Dominant outgassed species (verbatim string; "CO2" / "SO2" /
    # "H2O" / "S+/O+ via Io").
    dominant_outgassed_species: str
    # Source mechanism (one of SRC_*).
    source_mechanism: str
    # True if body has present-day active outgassing.
    is_active: bool
    # The corresponding escape rate from v0.21.7 (kg/s) for direct
    # comparison. None when not directly comparable (e.g., subsurface
    # carbonate sequestration intercepts the balance).
    balance_with_escape_kg_per_s: Optional[float] = None
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body volcanic-outgassing entries — §17.4.2 v0.21.9 cross-channel ship
# ---------------------------------------------------------------------------

VOLCANIC_OUTGASSINGS: List[VolcanicOutgassing] = [

    # ---- Earth — Burton 2013 / Plank 2019 ----------------------------
    # Subaerial volcanism: ~85 Tg CO₂/yr = 2.7 kg/s globally.
    # Submarine: ~10 Tg CO₂/yr = 0.32 kg/s. Total ~3 kg/s; tightly
    # balanced over 10⁶-yr timescales by carbonate-silicate weathering
    # + ocean dissolution NOT by atmospheric escape (which is
    # negligible at v0.21.7 3 kg/s thermal Jeans of H/He, not CO₂).
    VolcanicOutgassing(
        body="terra",
        outgassing_rate_kg_per_s=3.0,
        dominant_outgassed_species="CO2",
        source_mechanism=SRC_SUBAERIAL_VOLCANISM,
        is_active=True,
        balance_with_escape_kg_per_s=None,        # not balanced via escape
        precision_flag=PRECISION_HIGH,
        notes="Subaerial + submarine combined ~85+10 Tg CO₂/yr = "
              "~3 kg/s. Tightly balanced by carbonate-silicate "
              "weathering on geological timescales (NOT by atmospheric "
              "escape, which is negligible for CO₂). The famous "
              "long-term carbon cycle.",
        source_key="burton_2013",
    ),

    # ---- Mars — Halevy & Head 2014 / present-day dormant ----------
    # Modern Mars: effectively dormant (no active volcanism observed
    # by Mars Express + ExoMars TGO; methane spikes detected but
    # source ambiguous). Halevy 2014 estimates early-Mars volcanism
    # was substantial (~10⁻³ Earth) but stopped ~3 Gyr ago. Modern
    # upper limit ~0.001 kg/s SO₂.
    VolcanicOutgassing(
        body="mars",
        outgassing_rate_kg_per_s=0.001,
        dominant_outgassed_species="SO2 (upper limit)",
        source_mechanism=SRC_DORMANT,
        is_active=False,
        balance_with_escape_kg_per_s=2.0,         # v0.21.7 escape rate
        precision_flag=PRECISION_MEDIUM,
        notes="Modern Mars effectively dormant. Halevy 2014 estimates "
              "early-Mars volcanism was ~10⁻³ Earth; stopped ~3 Gyr "
              "ago. Atmosphere-loss decoupled from outgassing — Mars "
              "has 2 kg/s pickup-ion escape (v0.21.7) but ~0 outgassing "
              "→ atmospheric inventory shrinks. The famous Mars-as-"
              "dead-planet story.",
        source_key="halevy_2014",
    ),

    # ---- Venus — Bullock & Grinspoon 2001 / Marcq 2018 EUV ----------
    # Modern Venus active mantle hotspots (Bullock & Grinspoon model
    # + EnVision pending observations); EUV spectroscopy from Venus
    # Express limits SO₂ outgassing to ~0.1-1 kg/s. Atmospheric
    # inventory of CO₂ stable on Gyr timescales because Venus's CO₂
    # is essentially "all up there" — no carbonate weathering sink.
    VolcanicOutgassing(
        body="venus",
        outgassing_rate_kg_per_s=0.5,
        dominant_outgassed_species="SO2",
        source_mechanism=SRC_SUBAERIAL_VOLCANISM,
        is_active=True,
        balance_with_escape_kg_per_s=0.4,          # v0.21.7 escape rate
        precision_flag=PRECISION_MEDIUM,
        notes="Active mantle hotspots (Bullock & Grinspoon 2001 + "
              "Marcq 2018 EUV upper limits). Modest source. "
              "Atmospheric CO₂ stable on Gyr because no carbonate "
              "weathering sink + matching escape rate (v0.21.7 "
              "0.4 kg/s).",
        source_key="bullock_2001",
    ),

    # ---- Io — Lellouch 2007 / Spencer 2007 ---------------------------
    # The headline. Lellouch 2007 SO₂ atmospheric-cycle modelling +
    # Spencer 2007 Galileo PPR thermal mapping give Io outgassing
    # rate ~1000 kg/s (1 ton/s) of SO₂ from active volcanism. This
    # SO₂ then goes through three fates: (a) frost condensation on
    # the cold side hemisphere; (b) photo-dissociation in atmosphere;
    # (c) injection into Jupiter's Io plasma torus (S+/O+).
    VolcanicOutgassing(
        body="io",
        outgassing_rate_kg_per_s=1000.0,
        dominant_outgassed_species="SO2",
        source_mechanism=SRC_TIDAL_VOLCANISM,
        is_active=True,
        balance_with_escape_kg_per_s=1000.0,      # v0.21.7 Jupiter Io-torus escape
        precision_flag=PRECISION_HIGH,
        notes="THE HEADLINE: 1 ton/s SO₂ outgassing from tidal-driven "
              "volcanism (v0.21.8 100 TW heating). SO₂ fates: frost "
              "condensation + photo-dissociation + injection into "
              "Jupiter Io plasma torus. Cross-references v0.21.7 "
              "Jupiter 1000 kg/s pickup-ion escape (essentially the "
              "same ions, just downstream).",
        source_key="lellouch_2007",
    ),

    # ---- Enceladus — Hansen 2011 Cassini INMS ------------------------
    # Cassini INMS in-situ plume samples gave H₂O flux ~200 kg/s
    # venting from south-polar tiger-stripe fissures. The plumes
    # supply Saturn's E-ring (which would otherwise sublimate away
    # in <100 yr). Cross-references v0.21.8 Enceladus 10 GW SP heat
    # flow that drives the venting.
    VolcanicOutgassing(
        body="enceladus",
        outgassing_rate_kg_per_s=200.0,
        dominant_outgassed_species="H2O",
        source_mechanism=SRC_PLUME_VENTING,
        is_active=True,
        balance_with_escape_kg_per_s=None,         # most goes to E-ring not escape
        precision_flag=PRECISION_HIGH,
        notes="200 kg/s H₂O via south-polar tiger-stripe plume vents. "
              "Supplies Saturn's E-ring directly (which would otherwise "
              "sublimate in <100 yr). Cross-references v0.21.8 "
              "Enceladus 10 GW SP heat flow that drives the venting.",
        source_key="hansen_2011_outgassing",
    ),

    # ---- Jupiter via Io — Bagenal 2007 ------------------------------
    # Jupiter's "outgassing" is the Io plasma torus injection
    # (~1 ton/s S+/O+) that ultimately escapes via the magnetosphere.
    # Cross-references v0.21.7 Jupiter 1000 kg/s magnetospheric mass
    # loss + the Io-flux-tube physics (v0.19.0 ~10¹² W).
    VolcanicOutgassing(
        body="jupiter",
        outgassing_rate_kg_per_s=1000.0,
        dominant_outgassed_species="S+/O+ (via Io)",
        source_mechanism=SRC_MAGNETOSPHERIC_INJECTION,
        is_active=True,
        balance_with_escape_kg_per_s=1000.0,
        precision_flag=PRECISION_HIGH,
        notes="Jupiter's mass loss is dominated by Io plasma torus "
              "injection -- this is the upstream side of v0.21.7's "
              "1000 kg/s magnetospheric escape. Same number because "
              "torus is in steady state. Cross-references v0.19.0 "
              "Io flux tube + v0.20.1 JRM33 + v0.21.5 Io footprint "
              "aurora -- five ships forming a coherent Io→Jupiter "
              "mass-transfer story.",
        source_key="bagenal_2007_outgassing",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "burton_2013": (
        "Burton M. R. et al. (2013). Deep carbon emissions from "
        "volcanoes. Reviews in Mineralogy and Geochemistry 75, "
        "323-354. DOI: 10.2138/rmg.2013.75.11"
    ),
    "halevy_2014": (
        "Halevy I. & Head J. W. (2014). Episodic warming of early "
        "Mars by punctuated volcanism. Nature Geoscience 7, 865-868. "
        "DOI: 10.1038/ngeo2293"
    ),
    "bullock_2001": (
        "Bullock M. A. & Grinspoon D. H. (2001). The recent evolution "
        "of climate on Venus. Icarus 150, 19-37. "
        "DOI: 10.1006/icar.2000.6570"
    ),
    "lellouch_2007": (
        "Lellouch E. et al. (2007). Io's atmosphere and surface-"
        "atmosphere interactions. In: Io After Galileo (Springer), "
        "pp. 231-264 (SO₂ atmospheric-cycle steady-state modelling)."
    ),
    "hansen_2011_outgassing": (
        "Hansen C. J. et al. (2011). The composition and structure "
        "of the Enceladus plume. Geophys. Res. Lett. 38, L11202. "
        "DOI: 10.1029/2011GL047415"
    ),
    "bagenal_2007_outgassing": (
        "Bagenal F. et al. (2007). Io plasma torus mass-loading and "
        "transport. In: Jupiter: The Planet, Satellites and "
        "Magnetosphere (Cambridge), pp. 537-572 (chapter on torus "
        "mass-loss vs Io outgassing)."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "SRC_SUBAERIAL_VOLCANISM",
    "SRC_SUBMARINE_VOLCANISM",
    "SRC_TIDAL_VOLCANISM",
    "SRC_PLUME_VENTING",
    "SRC_MAGNETOSPHERIC_INJECTION",
    "SRC_DORMANT",
    "VOLCANIC_OUTGASSINGS",
    "SOURCES",
    "VolcanicOutgassing",
]
