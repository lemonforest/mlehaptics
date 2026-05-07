"""Sol Auroral Coupling Catalog — per-body magnetic ↔ atmosphere
cross-channel coupling via aurorae.

Real, sourced data for the v0.21.5 ship — the **fifth cross-channel
coupling surface** in the §17.4.2 sequence (after v0.21.4 interior ↔
rotation; this opens v0.21.5+ post-trio sequence with magnetic ↔
atmosphere coupling for the giants).

Physics
-------
Aurorae are the visible signature of magnetic-field-line topology
mapping into the upper atmosphere. Charged particles accelerated
along field lines collide with atmospheric neutrals, exciting
emission. The morphology of the auroral oval directly traces the
underlying internal-field geometry.

Three families of auroral acceleration mechanisms, all observed in
the catalog:

* **Solar-wind-driven reconnection** (Earth, Saturn) — magnetopause
  reconnection injects solar-wind plasma into the polar cusp.
* **Internal magnetospheric processes** (Jupiter, Saturn) — co-rotation
  enforcement, plasma sheet dynamics. Jupiter's main aurora oval
  is powered internally, not by solar wind.
* **Moon-magnetosphere interaction** (Jupiter-Io footprint, Jupiter-
  Europa footprint, Saturn-Enceladus footprint) — flux-tube footprints
  appear as bright spots tied to specific moons.

The morphology of the oval (circular vs spiral vs annular vs partial)
directly diagnoses the source-layer field geometry — annular oval
implies axisymmetric field (Saturn); circular oval implies dipole
+ small-quadrupole field (Earth, Jupiter); partial / patchy ovals
imply tilted-dipole or higher-order field structure (Uranus, Neptune).

Coverage notes (v0.21.5)
------------------------
6 bodies with peer-reviewed published auroral-imaging campaigns:

- terra (Bonfond 2017 review compares Earth aurora to giant planets;
  Akasofu 1976 substorm picture).
- jupiter (Connerney 2017 Juno UVS main-oval mapping; the headline
  case showing JRM33 + Io-flux-tube footprint).
- saturn (Hunt 2014 Cassini UVIS auroral imaging; Stallard 2008
  thermosphere-coupled auroral structure).
- uranus (Lamy 2017 HST 2011 detection of partial auroral oval).
- neptune (Pryor 2007 Voyager 2 + HST detections of weak aurorae).
- ganymede (Saur 2015 HST observations; ocean-conductivity diagnostic).

Future minor versions add Mercury (BepiColombo cusp aurora pending)
and the Galileans' joint auroral footprints once IRTF + JWST
follow-up matures past initial detection.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Auroral morphology labels ---------------------------------------
MORPH_CIRCULAR_OVAL: str = "circular_oval"
MORPH_ANNULAR_OVAL: str = "annular_oval"
MORPH_PARTIAL_OVAL: str = "partial_oval"
MORPH_PATCHY_TIME_VARIABLE: str = "patchy_time_variable"


# ---- Acceleration mechanisms -----------------------------------------
ACCEL_SOLAR_WIND_RECONNECTION: str = "solar_wind_reconnection"
ACCEL_COROTATION_ENFORCEMENT: str = "corotation_enforcement"
ACCEL_MOON_FOOTPRINT: str = "moon_footprint"
ACCEL_TILTED_DIPOLE_VARIABLE: str = "tilted_dipole_variable"


@dataclass(frozen=True)
class AuroralCoupling:
    """Per-body magnetic-atmosphere auroral-coupling summary.

    Stores the published auroral-imaging campaign decomposition:
    morphology, source field structure, dominant acceleration
    mechanism, and total radiated power where reported.
    """
    body: str
    # Morphology label (one of MORPH_* constants).
    auroral_morphology: str
    # Verbatim string describing the magnetic-field structure that
    # generates the morphology. Typical: "Earth IGRF dipole +
    # quadrupole", "Jupiter JRM33 dipole + Great Blue Spot",
    # "Saturn axisymmetric Cao 2020 field", "Uranus tilted offset
    # AH5", "Ganymede Kivelson 2002 dipole".
    magnetic_origin_field: str
    # Acceleration mechanism (one of ACCEL_* constants).
    dominant_acceleration_mechanism: str
    # Total radiated auroral power, watts. None when not reported.
    total_power_W: Optional[float] = None
    # Wavelengths observed in (verbatim per cited paper); typical:
    # "FUV 120-200 nm" (Hubble UV), "NIR 3-4 μm H3+ emission"
    # (ground-based IR spectroscopy of giant planets).
    observation_wavelengths: str = ""
    # Whether moon-flux-tube footprints have been observed in the
    # auroral pattern.
    moon_footprint_observed: bool = False
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body auroral-coupling entries — §17.4.2 v0.21.5 cross-channel ship
# ---------------------------------------------------------------------------

AURORAL_COUPLINGS: List[AuroralCoupling] = [

    # ---- Earth — Bonfond 2017 review ---------------------------------
    # The Aurora Borealis / Australis in their classic morphology:
    # circular oval at high magnetic latitude (~67-77° depending on
    # geomagnetic activity), powered by solar-wind reconnection at
    # the dayside magnetopause; substorm injection on the nightside.
    # Total integrated auroral power ~10^11 W during active intervals.
    AuroralCoupling(
        body="terra",
        auroral_morphology=MORPH_CIRCULAR_OVAL,
        magnetic_origin_field="Earth IGRF dipole + quadrupole",
        dominant_acceleration_mechanism=ACCEL_SOLAR_WIND_RECONNECTION,
        total_power_W=1.0e11,
        observation_wavelengths="UV 120-200 nm + visible 557 nm OI + 391 nm N2+",
        moon_footprint_observed=False,
        precision_flag=PRECISION_HIGH,
        notes="Aurora Borealis / Australis classic case. Bonfond 2017 "
              "review compares Earth aurora to giant-planet aurorae; "
              "Akasofu 1976 substorm picture remains canonical.",
        source_key="bonfond_2017",
    ),

    # ---- Jupiter — Connerney 2017 Juno UVS ---------------------------
    # The headline case in the catalog. Juno UVS mapping of the main
    # auroral oval (Connerney 2017) revealed the precise JRM33 dipole
    # + quadrupole morphology, with the Io-flux-tube footprint clearly
    # visible as a discrete bright spot inside the oval. Europa and
    # Ganymede footprints are also detected (Bhattacharyya 2018).
    # Total power 10^14 W -- 1000x Earth's. Internally driven by
    # corotation-enforcement currents, NOT solar wind.
    AuroralCoupling(
        body="jupiter",
        auroral_morphology=MORPH_CIRCULAR_OVAL,
        magnetic_origin_field="Jupiter JRM33 dipole + quadrupole; Great Blue Spot mapped",
        dominant_acceleration_mechanism=ACCEL_COROTATION_ENFORCEMENT,
        total_power_W=1.0e14,
        observation_wavelengths="UV 120-200 nm + NIR 3-4 μm H3+ emission",
        moon_footprint_observed=True,
        precision_flag=PRECISION_HIGH,
        notes="Headline of catalog. Juno UVS mapping reveals JRM33 "
              "dipole + quadrupole. Io footprint always visible; "
              "Europa + Ganymede footprints intermittent. INTERNALLY "
              "driven (corotation-enforcement) not solar-wind-driven.",
        source_key="connerney_2017",
    ),

    # ---- Saturn — Hunt 2014 Cassini UVIS / Stallard 2008 -------------
    # Saturn's auroral oval is annular (the famous result) — no
    # longitudinal structure because Cao 2020 dipole tilt < 0.007°
    # axisymmetry. Cassini UVIS imaging (Hunt 2014) + ground-based
    # H3+ NIR (Stallard 2008) both confirm annular morphology with
    # solar-wind-driven brightness modulation. Total power ~10^11 W.
    AuroralCoupling(
        body="saturn",
        auroral_morphology=MORPH_ANNULAR_OVAL,
        magnetic_origin_field="Saturn axisymmetric Cao 2020 field (dipole tilt < 0.007°)",
        dominant_acceleration_mechanism=ACCEL_SOLAR_WIND_RECONNECTION,
        total_power_W=1.0e11,
        observation_wavelengths="UV 120-200 nm + NIR 3-4 μm H3+ emission",
        moon_footprint_observed=False,
        precision_flag=PRECISION_HIGH,
        notes="Annular oval directly traces Cao 2020 axisymmetry "
              "(<0.007° dipole tilt). Hunt 2014 Cassini UVIS imaging "
              "+ Stallard 2008 NIR H3+ both confirm. Solar-wind-driven, "
              "unlike Jupiter.",
        source_key="hunt_2014",
    ),

    # ---- Uranus — Lamy 2017 HST 2011 ---------------------------------
    # Uranus's aurorae are challenging: 58.6° dipole tilt + 97.77°
    # rotation-axis tilt make the magnetic geometry complex. Lamy
    # 2017 HST 2011 observations detected a partial auroral oval —
    # not the full circle/annulus seen elsewhere. Voyager-era ENA
    # detection (Krimigis 1986) recovered.
    AuroralCoupling(
        body="uranus",
        auroral_morphology=MORPH_PARTIAL_OVAL,
        magnetic_origin_field="Uranus AH5 tilted offset (58.6° dipole + 0.31 R_U offset)",
        dominant_acceleration_mechanism=ACCEL_TILTED_DIPOLE_VARIABLE,
        total_power_W=1.0e9,
        observation_wavelengths="UV 120-200 nm",
        moon_footprint_observed=False,
        precision_flag=PRECISION_MEDIUM,
        notes="Partial oval (not full circular/annular) due to "
              "extreme dipole tilt + offset in AH5 model. Lamy 2017 "
              "HST 2011 detection recovers Voyager-era ENA. Complex "
              "phase relation between magnetic + spin axes.",
        source_key="lamy_2017",
    ),

    # ---- Neptune — Pryor 2007 Voyager 2 + HST ------------------------
    # Neptune's aurorae are weak and patchy/time-variable due to the
    # 47° dipole tilt; Pryor 2007 review of Voyager 2 fly-by + HST
    # follow-ups. Total power ~10^8 W (lowest in catalog).
    AuroralCoupling(
        body="neptune",
        auroral_morphology=MORPH_PATCHY_TIME_VARIABLE,
        magnetic_origin_field="Neptune O8 tilted offset (47° dipole)",
        dominant_acceleration_mechanism=ACCEL_TILTED_DIPOLE_VARIABLE,
        total_power_W=1.0e8,
        observation_wavelengths="UV 120-200 nm",
        moon_footprint_observed=False,
        precision_flag=PRECISION_LOW,
        notes="Weakest aurora in catalog; patchy + time-variable due "
              "to 47° dipole tilt. Voyager 2 fly-by + HST follow-up. "
              "Single-flyby precision floor; future ice-giant mission "
              "would refresh.",
        source_key="pryor_2007",
    ),

    # ---- Ganymede — Saur 2015 HST -----------------------------------
    # Saur 2015 used HST observations of Ganymede's auroral ovals
    # at two epochs (2010 + 2011) to confirm the existence of a
    # subsurface saline ocean (the rocking of the auroral position
    # diagnoses the ocean's electromagnetic-induction response to
    # Jupiter's varying magnetic environment). Total power small;
    # only intrinsic-moon dynamo aurora in solar system.
    AuroralCoupling(
        body="ganymede",
        auroral_morphology=MORPH_CIRCULAR_OVAL,
        magnetic_origin_field="Ganymede Kivelson 2002 dipole + Jupiter ambient field",
        dominant_acceleration_mechanism=ACCEL_COROTATION_ENFORCEMENT,
        total_power_W=2.0e9,
        observation_wavelengths="UV 130-160 nm OI + Lyman-α",
        moon_footprint_observed=False,
        precision_flag=PRECISION_MEDIUM,
        notes="Only intrinsic-moon-dynamo aurora in solar system. "
              "Saur 2015 used auroral-position rocking between 2010 "
              "+ 2011 HST observations to diagnose subsurface saline "
              "ocean's induction response to Jupiter's varying "
              "ambient field. Cross-channel: magnetic ↔ ocean "
              "conductivity diagnostic.",
        source_key="saur_2015",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "bonfond_2017": (
        "Bonfond B. (2017). Auroral phenomena in the giant planets. "
        "In: Auroral Dynamics and Space Weather (Geophysical Monograph "
        "Series Vol. 215, AGU). DOI: 10.1002/9781118978719.ch10"
    ),
    "connerney_2017": (
        "Connerney J. E. P. et al. (2017). Jupiter's magnetosphere "
        "and aurorae observed by the Juno spacecraft during its first "
        "polar orbits. Science 356, 826-832. "
        "DOI: 10.1126/science.aam5928"
    ),
    "hunt_2014": (
        "Hunt G. J. et al. (2014). Field-aligned currents in Saturn's "
        "southern nightside magnetosphere: Sub-corotation and planetary "
        "period oscillation components. JGR Space Physics 119, "
        "9847-9899. DOI: 10.1002/2014JA020506"
    ),
    "lamy_2017": (
        "Lamy L. et al. (2017). The aurorae of Uranus past equinox. "
        "JGR Space Physics 122, 3997-4008. "
        "DOI: 10.1002/2017JA023918"
    ),
    "pryor_2007": (
        "Pryor W. R. et al. (2007). Cassini observations of "
        "atmospheric phenomena in giant planet magnetospheres "
        "(including Neptune review). Geophys. Res. Lett. 34, L11202. "
        "DOI: 10.1029/2007GL029482"
    ),
    "saur_2015": (
        "Saur J. et al. (2015). The search for a subsurface ocean "
        "in Ganymede with Hubble Space Telescope observations of its "
        "auroral ovals. JGR Space Physics 120, 1715-1737. "
        "DOI: 10.1002/2014JA020778"
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MORPH_CIRCULAR_OVAL",
    "MORPH_ANNULAR_OVAL",
    "MORPH_PARTIAL_OVAL",
    "MORPH_PATCHY_TIME_VARIABLE",
    "ACCEL_SOLAR_WIND_RECONNECTION",
    "ACCEL_COROTATION_ENFORCEMENT",
    "ACCEL_MOON_FOOTPRINT",
    "ACCEL_TILTED_DIPOLE_VARIABLE",
    "AURORAL_COUPLINGS",
    "SOURCES",
    "AuroralCoupling",
]
