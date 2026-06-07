"""Sol Heat Flow Catalog — per-body surface heat flow ↔ tidal-heating
cross-channel coupling.

Real, sourced data for the v0.21.8 ship — the **eighth cross-channel
coupling surface** in the §17.4.2 v0.21.x sequence (after v0.21.7
atmospheric escape ↔ magnetic-field shielding).

Physics
-------
Internal heat flow connects to tidal-Q dissipation (v0.21.4
``RotationalConstraint``) through energy-budget conservation: a body
dissipating mechanical tidal energy must radiate that heat through
its surface as observable thermal flux. The total surface heat flow
decomposes into three contributions:

* **Tidal** — mechanical-energy dissipation from parent-body tidal
  forcing; rate connects to v0.21.4 Q-factor + v0.21.6 orbital
  migration through angular-momentum conservation.
* **Radiogenic** — radioactive decay of long-lived isotopes
  (Earth-like ²³⁸U, ²³²Th, ⁴⁰K).
* **Primordial cooling** — gravitational potential energy released
  during accretion + core formation (Earth-like).

The cross-channel observation: v0.21.4 + v0.21.6 + v0.21.8 close the
**tidal-energy-budget loop**. For Io, the v0.21.4 Q ≈ 80 + v0.21.6
+3.6 cm/yr outward migration imply tidal dissipation power → must
match v0.21.8 observed surface heat flow ~100 TW. For Saturn-Titan,
the v0.21.6 11 cm/yr outward migration + Mankovich-Fuller 2021
ring-seismology imply Saturn-interior dissipation that should
manifest in Saturn's heat balance.

Coverage notes (v0.21.8)
------------------------
6 bodies with peer-reviewed measured surface heat flow:

- terra (Davies 2010 / Lay 2008 review).
- mars (Frizzell 2023 InSight + GRS-geochemistry crustal heat-flow
  synthesis).
- io (McEwen 2004 / Veeder 2012 Galileo PPR + ground-based IR
  total-power measurement; the headline).
- europa (Vance 2018 icy-shell + ocean energy budget).
- enceladus (Howett 2011 Cassini CIRS south-polar terrain power).
- titan (Tobie 2005 coupled thermal-orbital internal-structure model).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


@dataclass(frozen=True)
class HeatFlow:
    """Per-body surface heat-flow ↔ tidal-heating decomposition.

    Stores the published total heat flow in TW + fractional
    decomposition into tidal / radiogenic / primordial-cooling
    contributions, per the cited paper's energy-budget analysis.
    """
    body: str
    # Total surface heat flow in TW (10^12 W).
    total_heat_flow_TW: float
    # Fraction from tidal dissipation (0-1; sum of the three fractions
    # should be ~1).
    tidal_fraction: float
    # Fraction from radiogenic decay.
    radiogenic_fraction: float
    # Fraction from primordial cooling / accretion energy.
    primordial_fraction: float
    # Verbatim string describing the observation / inference method.
    observation_method: str = ""
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""
    # ---- dual-author provenance (v0.30.0rc10 attested-TOML backfill) ----
    # Per-row citation provenance, mirrored byte-stably into the AMSC
    # literature_curated path at research/attested/heat_flow/. All six
    # source DOIs CrossRef-verified (the 3 rc9 repairs + the 3 pre-existing
    # davies/vance/howett, 2026-06-07).
    source_doi: str = ""
    source_published_date: str = ""
    entered_locally_at: str = ""
    source_version: Optional[str] = None


# ---------------------------------------------------------------------------
# Per-body heat-flow entries — §17.4.2 v0.21.8 cross-channel ship
# ---------------------------------------------------------------------------

HEAT_FLOWS: List[HeatFlow] = [

    # ---- Earth — Davies 2010 / Lay 2008 ------------------------------
    # 47 TW total; ~50-80% radiogenic (²³⁸U + ²³²Th + ⁴⁰K), ~20-50%
    # primordial cooling, ~0% tidal. The canonical case.
    HeatFlow(
        body="terra",
        total_heat_flow_TW=47.0,
        tidal_fraction=0.001,
        radiogenic_fraction=0.66,
        primordial_fraction=0.34,
        observation_method="surface heat-flow probes + seismic core flux",
        precision_flag=PRECISION_HIGH,
        notes="Canonical case. Davies 2010 / Lay 2008 review. "
              "Radiogenic-dominated with significant primordial-"
              "cooling tail. Tidal contribution negligible (Earth's "
              "tidal Q ≈ 280 dissipates almost entirely in oceans).",
        source_key="davies_2010",
        source_doi="10.5194/se-1-5-2010",
        source_published_date="2010",
        entered_locally_at="2026-06-07",
    ),

    # ---- Mars — Khan 2023 InSight ------------------------------------
    # InSight RISE + seismometer data inversion gives Mars basal heat
    # flow ~25-30 mW/m^2 globally averaged → ~0.1 TW total.
    # Radiogenic-dominated with smaller cooling component than Earth
    # (Mars cooled faster).
    HeatFlow(
        body="mars",
        total_heat_flow_TW=1.5,
        tidal_fraction=0.001,
        radiogenic_fraction=0.85,
        primordial_fraction=0.15,
        observation_method="InSight crustal-thickness + GRS regional-geochemistry heat-production synthesis",
        precision_flag=PRECISION_MEDIUM,
        notes="Frizzell 2023 InSight + GRS synthesis: crustal heat flow "
              "~3-14 mW/m^2 (endmember crustal-thickness models); ~1.5 TW "
              "globally at the upper end. Radiogenic-dominated; cooled "
              "faster than Earth.",
        source_key="frizzell_2023",
        source_doi="10.1016/j.icarus.2023.115700",
        source_published_date="2023",
        entered_locally_at="2026-06-07",
    ),

    # ---- Io — McEwen 2004 / Veeder 2012 ------------------------------
    # The headline. ~100 TW (twice Earth's despite Io being 4× smaller
    # in radius!) measured by Galileo PPR + ground-based IR. Almost
    # entirely tidal heating from Jupiter — cross-references v0.21.4
    # Q ≈ 80 + v0.21.6 outward migration. Drives Io's volcanism.
    HeatFlow(
        body="io",
        total_heat_flow_TW=100.0,
        tidal_fraction=0.99,
        radiogenic_fraction=0.005,
        primordial_fraction=0.005,
        observation_method="Galileo PPR thermal mapping + ground-based IR total-power",
        precision_flag=PRECISION_HIGH,
        notes="THE HEADLINE: Io is most volcanically active body in "
              "solar system at ~100 TW (2× Earth despite 4× smaller "
              "radius). Almost entirely tidal heating from Jupiter. "
              "Cross-references v0.21.4 Q~80 + v0.21.6 +3.6 cm/yr "
              "outward migration -- the three ships close the Io "
              "tidal-energy-budget loop.",
        source_key="veeder_2012",
        source_doi="10.1016/j.icarus.2012.04.004",
        source_published_date="2012",
        entered_locally_at="2026-06-07",
    ),

    # ---- Europa — Vance 2018 -----------------------------------------
    # 0.1-1 TW total; tidal heating in icy shell + ocean dominates;
    # maintains the subsurface saline ocean against freezing. Uncertain
    # because tidal dissipation depends on poorly-constrained ice-shell
    # rheology.
    HeatFlow(
        body="europa",
        total_heat_flow_TW=0.5,
        tidal_fraction=0.85,
        radiogenic_fraction=0.13,
        primordial_fraction=0.02,
        observation_method="Galileo magnetic + Vance 2018 icy-shell + ocean energy budget model",
        precision_flag=PRECISION_MEDIUM,
        notes="Maintains subsurface saline ocean against freezing. "
              "Tidal-dominated but uncertain (ice-shell rheology not "
              "well constrained). Vance 2018 budget model. Cross-"
              "references v0.21.5 Saur 2015 ocean diagnostic.",
        source_key="vance_2018",
        source_doi="10.1002/2017JE005341",
        source_published_date="2018",
        entered_locally_at="2026-06-07",
    ),

    # ---- Enceladus — Howett 2011 -------------------------------------
    # 4-15 GW south-polar plumes (NOT TW; Enceladus is small). Howett
    # 2011 Cassini CIRS imaging of "tiger stripe" SPT terrain found
    # dissipation rate ≈ tidal heating prediction. Drives the plume
    # geyser system.
    HeatFlow(
        body="enceladus",
        total_heat_flow_TW=0.01,                  # 10 GW = 0.01 TW
        tidal_fraction=0.95,
        radiogenic_fraction=0.04,
        primordial_fraction=0.01,
        observation_method="Cassini CIRS south-polar terrain thermal imaging",
        precision_flag=PRECISION_HIGH,
        notes="South-polar plumes: 4-15 GW dissipation in 'tiger "
              "stripe' SPT terrain matches tidal heating prediction. "
              "Drives plume geyser system; H2O/CO2/CH4/N2/H2 "
              "venting. Cross-references v0.20.2 fluid-envelope plume "
              "column convention.",
        source_key="howett_2011",
        source_doi="10.1029/2010JE003718",
        source_published_date="2011",
        entered_locally_at="2026-06-07",
    ),

    # ---- Titan — Tobie 2005 ------------------------------------------
    # ~1-3 TW; uncertain because of weak observational constraint.
    # Tobie 2005 coupled thermal-orbital model gives substantial tidal
    # heating from Saturn's gravitational pull, particularly in the
    # icy outer mantle.
    HeatFlow(
        body="titan",
        total_heat_flow_TW=2.0,
        tidal_fraction=0.55,
        radiogenic_fraction=0.45,
        primordial_fraction=0.0,
        observation_method="Tobie 2005 coupled thermal-orbital internal-structure + tidal-heating model; Iess 2010 gravity",
        precision_flag=PRECISION_LOW,
        notes="Modest tidal heating in icy outer mantle from Saturn. "
              "Cross-references v0.21.6 Lainey 2020 Saturn-Titan +11 "
              "cm/yr outward migration: Saturn loses angular momentum "
              "→ Titan gains orbital energy → some fraction dissipates "
              "as Titan tidal heat.",
        source_key="tobie_2005",
        source_doi="10.1016/j.icarus.2004.12.007",
        source_published_date="2005",
        entered_locally_at="2026-06-07",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "davies_2010": (
        "Davies J. H. & Davies D. R. (2010). Earth's surface heat "
        "flux. Solid Earth 1, 5-24. DOI: 10.5194/se-1-5-2010"
    ),
    "frizzell_2023": (
        "Frizzell K. R., Ojha L. & Karunatillake S. (2023). Bounding "
        "the unknowns of martian crustal heat flow from a synthesis of "
        "regional geochemistry and InSight mission data. Icarus 405, "
        "115700. DOI: 10.1016/j.icarus.2023.115700"
    ),
    "veeder_2012": (
        "Veeder G. J., Davies A. G., Matson D. L., Johnson T. V., "
        "Williams D. A. & Radebaugh J. (2012). Io: Volcanic thermal "
        "sources and global heat flow. Icarus 219, 701-722. "
        "DOI: 10.1016/j.icarus.2012.04.004"
    ),
    "vance_2018": (
        "Vance S. D. et al. (2018). Geophysical investigations of "
        "habitability in ice-covered ocean worlds. JGR Planets 123, "
        "180-205. DOI: 10.1002/2017JE005341"
    ),
    "howett_2011": (
        "Howett C. J. A. et al. (2011). High heat flow from "
        "Enceladus' south polar region measured using 10-600 cm⁻¹ "
        "Cassini/CIRS data. JGR Planets 116, E03003. "
        "DOI: 10.1029/2010JE003718"
    ),
    "tobie_2005": (
        "Tobie G., Grasset O., Lunine J. I., Mocquet A. & Sotin C. "
        "(2005). Titan's internal structure inferred from a coupled "
        "thermal-orbital model. Icarus 175, 496-502. "
        "DOI: 10.1016/j.icarus.2004.12.007"
    ),
}


# ---------------------------------------------------------------------------
# Dual-author bridge (v0.30.0rc10 attested-TOML backfill)
# ---------------------------------------------------------------------------

def heatflow_to_data_dict(hf: "HeatFlow") -> Dict[str, object]:
    """Project a ``HeatFlow`` row to the flat dict shape carried by the
    AMSC literature_curated NDJSON at
    ``research/attested/heat_flow/heat_flow.ndjson``.

    ``tests/test_heat_flow_dual_author.py`` asserts byte-stable equality
    between this hand-coded projection and the AMSC-path ``data`` block
    surfaced by ``bridge.get_attested_dataset("heat_flow")`` — the
    evidence the descriptor schema expresses what the @dataclass expresses
    (the saturn_rings + solar_rotation + tidal_migration pattern).
    """
    return {
        "body": hf.body,
        "total_heat_flow_TW": hf.total_heat_flow_TW,
        "tidal_fraction": hf.tidal_fraction,
        "radiogenic_fraction": hf.radiogenic_fraction,
        "primordial_fraction": hf.primordial_fraction,
        "observation_method": hf.observation_method,
        "precision_flag": hf.precision_flag,
        "source_key": hf.source_key,
        "source_doi": hf.source_doi,
        "source_published_date": hf.source_published_date,
        "entered_locally_at": hf.entered_locally_at,
        "source_version": hf.source_version,
        "notes": hf.notes,
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "HEAT_FLOWS",
    "SOURCES",
    "HeatFlow",
    "heatflow_to_data_dict",
]
