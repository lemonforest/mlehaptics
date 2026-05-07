"""Sol Atmospheric Escape Catalog — per-body atmospheric escape ↔
magnetic-field shielding cross-channel coupling.

Real, sourced data for the v0.21.7 ship — the **seventh cross-channel
coupling surface** in the §17.4.2 v0.21.x sequence (after v0.21.6
tidal ↔ orbital migration).

Physics
-------
Atmospheric escape rates depend critically on magnetic-field shielding.
A planet with a strong intrinsic dipole (Earth IGRF; Jupiter JRM33)
deflects solar wind at the magnetopause, preventing direct ion-pickup
escape and limiting losses to thermal Jeans escape of light species
(H, He). A planet without intrinsic field (Mars, Venus) is exposed
to direct solar-wind interaction, allowing pickup-ion escape that
preferentially removes heavy species (O+, CO₂+) over Gyr timescales.

The cross-channel observation: **the v0.20.2 atmospheric inventory
diverges by Gyr from the v0.20.1 magnetic-multipole inventory**.
Earth + Jupiter + Saturn retain their primordial atmospheres; Mars +
Venus diverge from terrestrial inventory because they cannot retain
escape against solar-wind erosion.

Coverage notes (v0.21.7)
------------------------
6 bodies with peer-reviewed measured atmospheric-escape rates:

- terra (Bauer 2014 thermal escape; Lammer 2018 review).
- mars (Jakosky 2018 MAVEN integrated atmospheric loss — the
  headline; Mars lost ~50% of its primordial atmosphere over 4 Gyr).
- venus (Persson 2020 / Lundin 2008 ASPERA-4 ion measurements).
- mercury (Killen 2007 review; MESSENGER replenishment-rate
  inferences).
- titan (Strobel 2008 hydrodynamic-escape modelling; Sittler 2010
  Cassini observations).
- jupiter (Bagenal 2007 magnetospheric mass-loss; Mauk 2017
  Juno-era refinement).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Escape mechanism labels ------------------------------------------
ESC_THERMAL_JEANS: str = "thermal_jeans"           # Maxwell-Boltzmann tail of H/He
ESC_HYDRODYNAMIC: str = "hydrodynamic"             # bulk-flow blowoff
ESC_PICKUP_ION: str = "pickup_ion"                 # solar-wind direct interaction
ESC_PHOTOCHEMICAL: str = "photochemical"            # photo-dissociation + Jeans
ESC_SPUTTERING: str = "sputtering"                 # solar-wind sputtering of regolith


@dataclass(frozen=True)
class AtmosphericEscape:
    """Per-body atmospheric escape ↔ magnetic-shielding constraint.

    Stores the published total escape rate in kg/s + the dominant
    escape mechanism + the magnetic-shielding state + the dominant
    escaping species + integrated Gyr atmospheric loss where reported.
    """
    body: str
    # Total atmospheric escape rate (kg/s). Combined across all
    # mechanisms / species; dominant species reported in
    # `dominant_escaping_species`.
    escape_rate_kg_per_s: float
    # Dominant escape mechanism (one of ESC_*).
    dominant_escape_mechanism: str
    # True if body has a strong intrinsic dipole field that deflects
    # solar wind at a global magnetopause. False for unmagnetised
    # bodies (Mars, Venus).
    magnetic_shielding_present: bool
    # Dominant escaping species (verbatim string; "H" / "H2" /
    # "O+" / "CO2+" / "Na" etc.).
    dominant_escaping_species: str
    # Integrated atmospheric mass loss over 4 Gyr (kg). None when not
    # reported in cited literature. For Mars: ~10^17-10^18 kg = ~50%
    # of original CO2 atmosphere.
    integrated_loss_4Gyr_kg: Optional[float] = None
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body atmospheric escape entries — §17.4.2 v0.21.7 cross-channel ship
# ---------------------------------------------------------------------------

ATMOSPHERIC_ESCAPES: List[AtmosphericEscape] = [

    # ---- Earth — Bauer 2014 / Lammer 2018 ----------------------------
    # Earth's IGRF dipole deflects solar wind at magnetopause ~10 R_E
    # → only thermal Jeans escape of H + He at exobase. Total escape
    # ~3 kg/s, dominated by H. Negligible integrated loss over 4 Gyr
    # (terrestrial atmosphere is "geologically forever" given current
    # rates).
    AtmosphericEscape(
        body="terra",
        escape_rate_kg_per_s=3.0,
        dominant_escape_mechanism=ESC_THERMAL_JEANS,
        magnetic_shielding_present=True,
        dominant_escaping_species="H",
        integrated_loss_4Gyr_kg=4.0e14,
        precision_flag=PRECISION_HIGH,
        notes="IGRF dipole protects against solar-wind pickup; only "
              "thermal Jeans escape of H/He. Atmosphere stable on "
              "Gyr timescales given current rates. Cross-references "
              "v0.20.1 IGRF + v0.20.2 ERA5 climatology.",
        source_key="lammer_2018",
    ),

    # ---- Mars — Jakosky 2018 MAVEN -----------------------------------
    # The headline. MAVEN's integrated 4-year measurement of pickup-
    # ion escape gives ~2 kg/s present-day rate; back-extrapolating
    # over 4 Gyr accounting for early Mars's stronger XUV environment
    # gives total atmospheric loss of ~10^18 kg = ~50% of primordial
    # CO2 atmosphere. The famous "Mars lost its atmosphere because
    # it lost its dynamo" story.
    AtmosphericEscape(
        body="mars",
        escape_rate_kg_per_s=2.0,
        dominant_escape_mechanism=ESC_PICKUP_ION,
        magnetic_shielding_present=False,
        dominant_escaping_species="O+",
        integrated_loss_4Gyr_kg=1.0e18,
        precision_flag=PRECISION_HIGH,
        notes="THE HEADLINE: Jakosky 2018 MAVEN integrated escape. "
              "Mars lost ~50% of primordial CO2 atmosphere over 4 Gyr "
              "because it lacks magnetic shielding. Cross-references "
              "v0.20.1 (no Mars magnetic multipole entry) + v0.20.2 "
              "(thin Mars atmosphere). The famous dynamo-loss / "
              "atmosphere-loss correlation.",
        source_key="jakosky_2018",
    ),

    # ---- Venus — Persson 2020 / Lundin 2008 ASPERA-4 -----------------
    # Venus has NO intrinsic dipole but retains its thick CO2
    # atmosphere because of induced magnetosphere from solar-wind
    # interaction with ionosphere. Modest escape rate ~0.4 kg/s
    # (lower than Mars despite no shielding) because Venus's stronger
    # gravity holds heavier ions.
    AtmosphericEscape(
        body="venus",
        escape_rate_kg_per_s=0.4,
        dominant_escape_mechanism=ESC_PICKUP_ION,
        magnetic_shielding_present=False,
        dominant_escaping_species="O+",
        integrated_loss_4Gyr_kg=5.0e16,
        precision_flag=PRECISION_HIGH,
        notes="No intrinsic dipole but thick atmosphere retained "
              "because Venus's stronger gravity holds heavier ions "
              "+ induced magnetosphere from solar-wind/ionosphere "
              "interaction. Persson 2020 + Lundin 2008 ASPERA-4 "
              "Venus Express measurements.",
        source_key="persson_2020",
    ),

    # ---- Mercury — Killen 2007 review --------------------------------
    # Mercury's weak field provides minimal solar-wind deflection;
    # surface-bound exosphere of Na/K/H/He is constantly replenished
    # by impact vaporisation + sputtering. Net loss rate ~10 g/s
    # (4 orders below Venus); Na tail observable from Earth as
    # downstream extension.
    AtmosphericEscape(
        body="mercury",
        escape_rate_kg_per_s=0.01,
        dominant_escape_mechanism=ESC_SPUTTERING,
        magnetic_shielding_present=True,            # weak shielding
        dominant_escaping_species="Na",
        integrated_loss_4Gyr_kg=1.0e15,
        precision_flag=PRECISION_MEDIUM,
        notes="Weak field provides partial deflection; surface-bound "
              "exosphere replenished by impact + sputtering at rate "
              "matched to escape. Na tail observable from Earth via "
              "D-line emission; classic exospheric system.",
        source_key="killen_2007",
    ),

    # ---- Titan — Strobel 2008 ----------------------------------------
    # Titan's thick N2 atmosphere undergoes hydrodynamic blowoff at
    # the exobase; Strobel 2008 gives ~30 kg/s present rate (highest
    # in the catalog despite Titan's small size). Saturn's
    # magnetosphere provides partial shielding; Titan inside
    # magnetosphere most of the time but exposed during occasional
    # solar-wind compressions.
    AtmosphericEscape(
        body="titan",
        escape_rate_kg_per_s=30.0,
        dominant_escape_mechanism=ESC_HYDRODYNAMIC,
        magnetic_shielding_present=True,           # via Saturn's magnetosphere
        dominant_escaping_species="H2",
        integrated_loss_4Gyr_kg=4.0e18,
        precision_flag=PRECISION_HIGH,
        notes="Highest absolute escape rate in catalog despite small "
              "size. Hydrodynamic blowoff at exobase; Saturn's "
              "magnetosphere provides partial shielding. Cross-"
              "references v0.20.2 Titan thick atmosphere + v0.20.1 "
              "(Saturn axisymmetric field).",
        source_key="strobel_2008",
    ),

    # ---- Jupiter — Bagenal 2007 / Mauk 2017 --------------------------
    # Jupiter's massive magnetosphere (extends to ~5 AU on dayside
    # under solar-wind compression) prevents direct atmospheric
    # interaction with solar wind. Mass loss is dominated by Io
    # plasma torus (~1 ton/s of S+, O+ injected by Io volcanism)
    # routed through the magnetosphere rather than direct escape.
    AtmosphericEscape(
        body="jupiter",
        escape_rate_kg_per_s=1000.0,
        dominant_escape_mechanism=ESC_PICKUP_ION,
        magnetic_shielding_present=True,
        dominant_escaping_species="S+/O+ (Io torus)",
        integrated_loss_4Gyr_kg=1.0e20,
        precision_flag=PRECISION_HIGH,
        notes="Dominant mass loss is Io plasma torus injection (S+/O+ "
              "from Io volcanism) routed through magnetosphere, not "
              "Jupiter atmospheric escape per se. Cross-references "
              "v0.19.0 (Jupiter-Io flux tube ~10^12 W) + v0.20.1 "
              "(JRM33 magnetosphere) + v0.21.5 (Io footprint aurora).",
        source_key="bagenal_2007",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "lammer_2018": (
        "Lammer H. et al. (2018). Origin and evolution of the "
        "atmospheres of early Venus, Earth and Mars. Astron. "
        "Astrophys. Rev. 26, 2. DOI: 10.1007/s00159-018-0108-y"
    ),
    "jakosky_2018": (
        "Jakosky B. M. et al. (2018). Loss of the Martian atmosphere "
        "to space: Present-day loss rates determined from MAVEN "
        "observations and integrated loss through time. Icarus 315, "
        "146-157. DOI: 10.1016/j.icarus.2018.05.030"
    ),
    "persson_2020": (
        "Persson M. et al. (2020). The Venusian atmospheric oxygen "
        "ion escape: Extrapolation to the early solar system. JGR "
        "Planets 125, e2019JE006336. DOI: 10.1029/2019JE006336"
    ),
    "killen_2007": (
        "Killen R. M. et al. (2007). Processes that promote and "
        "deplete the exosphere of Mercury. Space Sci. Rev. 132, "
        "433-509. DOI: 10.1007/s11214-007-9232-0"
    ),
    "strobel_2008": (
        "Strobel D. F. (2008). Titan's hydrodynamically escaping "
        "atmosphere. Icarus 193, 588-594. "
        "DOI: 10.1016/j.icarus.2007.08.014"
    ),
    "bagenal_2007": (
        "Bagenal F. et al. (2007). Jupiter: The Planet, Satellites "
        "and Magnetosphere. Cambridge University Press (escape "
        "chapter): plasma-source rates from Io torus."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "ESC_THERMAL_JEANS",
    "ESC_HYDRODYNAMIC",
    "ESC_PICKUP_ION",
    "ESC_PHOTOCHEMICAL",
    "ESC_SPUTTERING",
    "ATMOSPHERIC_ESCAPES",
    "SOURCES",
    "AtmosphericEscape",
]
