"""Sol Orographic Forcing Catalog — per-body topography → atmospheric
standing-wave forcing summary.

Real, sourced data for the v0.21.3 ship — the **third cross-channel
coupling surface** in the §17.4.2 sequence (after v0.21.1 topography
↔ gravity admittance and v0.21.2 magnetic-multipole-derived dynamo
constraints). See research notebook §17.4.2 for the architectural
scoping.

Physics
-------
Surface topography acts as a lower-boundary forcing on the global
atmospheric circulation. A mountain range or planetary-scale uplift
generates downstream stationary Rossby waves — planetary waves with
zero phase speed in the body-rotating frame, so they appear as fixed
structure in the time-mean atmosphere.

The dominant zonal wavenumber of the standing-wave pattern is set by
the Rossby radius of deformation `L_R = N · H / f` (where N is
Brunt-Väisälä frequency, H is scale height, f is Coriolis parameter)
— shorter L_R → higher dominant wavenumber. The forcing amplitude
scales with the product of topographic height + mean zonal wind
speed at that latitude.

Coverage notes (v0.21.3)
------------------------
This is an **emerging research area** — the published catalog of
quantitatively-modelled orographic-forcing studies is small. v0.21.3
ships the four bodies with refereed published GCM-derived stationary-
wave decompositions:

- terra (Hoskins & Karoly 1981 / Held 2002 Northern-Hemisphere
  stationary-wave review): Tibetan Plateau as dominant orographic
  forcer at zonal wavenumber 1-2; East Asian / Pacific trough
  signature.
- mars (Hollingsworth 1997 / MGS Mars Climate Database): Tharsis
  bulge (~10 km elevation, ~10000 km wide) is the dominant
  orographic forcer; generates wavenumber-2 stationary pattern that
  survives to ~50 km altitude.
- venus (Lebonnois 2010 GCM): weak orographic forcing because
  Venus has only modest elevated terrain (Maxwell Montes ~11 km
  but very localised); the planet's super-rotation dominates the
  zonal circulation, suppressing classic stationary-wave physics.
  Included for completeness as a low-precision entry.
- titan (Charnay & Lebonnois 2012 GCM with topographic forcing):
  modest topographic relief but interesting because Titan's
  super-rotation regime generates atmospheric standing waves
  similar to Venus's pattern.

Future minor versions add Pluto + Triton once their atmospheric GCMs
mature past the New Horizons / Voyager 2 single-flyby characterisation
stage.
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
class OrographicForcing:
    """Per-body topography → atmospheric standing-wave forcing summary.

    Stores the *integrated* orographic-forcing description published
    in refereed GCM literature: dominant orographic feature name,
    feature height + width, dominant zonal wavenumber of the
    stationary-wave response, qualitative forcing amplitude, the
    atmospheric layer in which the standing wave is observed, and
    whether a stationary-wave pattern has been detected at all.
    """
    body: str
    # Name of the dominant topographic feature driving the forcing.
    dominant_orographic_feature_name: str
    # Feature height in km above the body's reference geoid / 1-bar
    # level.
    feature_height_km: float
    # Feature characteristic width in km (rough horizontal extent).
    feature_width_km: float
    # Dominant zonal wavenumber of the stationary-wave response.
    dominant_zonal_wavenumber: int
    # Qualitative forcing amplitude: "strong" / "moderate" / "weak" /
    # "negligible". A normalised numeric scale would require choosing
    # a single fiducial across very different planetary regimes;
    # qualitative is more honest.
    forcing_amplitude_relative: str
    # Whether a stationary-wave pattern has been observationally
    # confirmed (vs. only modelled).
    is_stationary_wave_observed: bool
    # Atmospheric pressure layer where the standing wave is most
    # prominent (verbatim from cited paper). Typical values:
    # "300-500 mbar mid-troposphere" (terra), "0.5 mbar / ~50 km altitude"
    # (mars).
    standing_wave_layer: str = ""
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body orographic-forcing entries — §17.4.2 v0.21.3 cross-channel ship
# ---------------------------------------------------------------------------

OROGRAPHIC_FORCINGS: List[OrographicForcing] = [

    # ---- Earth — Hoskins & Karoly 1981 / Held 2002 -------------------
    # Tibetan Plateau is the dominant Northern-Hemisphere orographic
    # forcer; the Hoskins & Karoly 1981 stationary-wave equation
    # decomposition shows wavenumber-1 + wavenumber-2 response with
    # the East Asian / Pacific trough at the canonical 300-500 mbar
    # mid-troposphere.
    OrographicForcing(
        body="terra",
        dominant_orographic_feature_name="Tibetan Plateau",
        feature_height_km=4.5,
        feature_width_km=2500.0,
        dominant_zonal_wavenumber=2,         # k=1 + k=2 mix; k=2 dominant
        forcing_amplitude_relative="strong",
        is_stationary_wave_observed=True,
        standing_wave_layer="300-500 mbar mid-troposphere",
        precision_flag=PRECISION_HIGH,
        notes="Hoskins & Karoly 1981 stationary-wave decomposition + "
              "Held 2002 review. NH winter pattern is classic; SH "
              "weaker because no comparable continental orography "
              "south of 30°S.",
        source_key="held_2002",
    ),

    # ---- Mars — Hollingsworth 1997 / MCD ------------------------------
    # The headline planetary case. Tharsis bulge (Olympus Mons +
    # Tharsis Montes) is ~10 km elevation, ~10000 km wide; generates
    # a wavenumber-2 stationary pattern that survives to the
    # mesopause at ~50 km altitude in MGS Mars Climate Database
    # observations and Mars GCM simulations.
    OrographicForcing(
        body="mars",
        dominant_orographic_feature_name="Tharsis Bulge",
        feature_height_km=10.0,
        feature_width_km=10000.0,
        dominant_zonal_wavenumber=2,
        forcing_amplitude_relative="strong",
        is_stationary_wave_observed=True,
        standing_wave_layer="0.5 mbar / ~50 km altitude (mesopause)",
        precision_flag=PRECISION_HIGH,
        notes="Tharsis bulge is the dominant planetary-scale "
              "orographic feature. Wavenumber-2 stationary pattern "
              "verified in MGS / MRO observations + Mars GCM. The "
              "feature persists from the surface to the mesopause.",
        source_key="hollingsworth_1997",
    ),

    # ---- Venus — Lebonnois 2010 GCM ----------------------------------
    # Venus's super-rotation (winds reaching 100 m/s at cloud level
    # vs surface rotation 1.8 m/s) dominates the zonal circulation
    # and suppresses classic stationary-wave physics. Maxwell Montes
    # (~11 km, narrow) is the only major elevated terrain;
    # observational signature of orographic forcing in the Venus
    # cloud-tracking is weak. Lebonnois 2010 GCM finds a small
    # wavenumber-1 perturbation but the precision is LOW.
    OrographicForcing(
        body="venus",
        dominant_orographic_feature_name="Maxwell Montes",
        feature_height_km=11.0,
        feature_width_km=800.0,
        dominant_zonal_wavenumber=1,
        forcing_amplitude_relative="weak",
        is_stationary_wave_observed=False,
        standing_wave_layer="cloud-deck (60-70 km altitude)",
        precision_flag=PRECISION_LOW,
        notes="Super-rotation regime suppresses classic orographic "
              "stationary-wave physics. Lebonnois 2010 GCM finds "
              "small k=1 perturbation; observational confirmation "
              "from cloud-tracking is ambiguous. Different physics "
              "regime than terra / mars.",
        source_key="lebonnois_2010",
    ),

    # ---- Titan — Charnay & Lebonnois 2012 GCM ------------------------
    # Titan also super-rotates; Charnay & Lebonnois 2012 GCM with
    # topographic forcing shows a modest wavenumber-1 standing wave
    # in the stratosphere. The forcing comes from the equatorial
    # dune fields + the icy uplifts of Xanadu region; both modest
    # in elevation (~hundreds of metres).
    OrographicForcing(
        body="titan",
        dominant_orographic_feature_name="Xanadu uplift / equatorial dune fields",
        feature_height_km=0.5,
        feature_width_km=4500.0,
        dominant_zonal_wavenumber=1,
        forcing_amplitude_relative="moderate",
        is_stationary_wave_observed=False,
        standing_wave_layer="stratosphere (100-300 km altitude)",
        precision_flag=PRECISION_LOW,
        notes="Super-rotation regime; analogous to Venus but with "
              "modest topographic relief. Charnay & Lebonnois 2012 "
              "GCM shows k=1 standing wave; Cassini CIRS observations "
              "ambiguous on direct detection.",
        source_key="charnay_2012",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "held_2002": (
        "Held I. M. et al. (2002). Northern winter stationary waves: "
        "theory and modelling. J. Climate 15:2125-2144. "
        "DOI: 10.1175/1520-0442(2002)015<2125:NWSWTA>2.0.CO;2"
    ),
    "hollingsworth_1997": (
        "Hollingsworth J. L. et al. (1997). Topographic forcing of "
        "the Martian global atmospheric circulation. J. Geophys. Res. "
        "102(E5):11365-11383. DOI: 10.1029/97JE00321"
    ),
    "lebonnois_2010": (
        "Lebonnois S. et al. (2010). Superrotation of Venus' "
        "atmosphere analyzed with a full general circulation model. "
        "JGR 115:E06006. DOI: 10.1029/2009JE003458"
    ),
    "charnay_2012": (
        "Charnay B. & Lebonnois S. (2012). Two boundary layers in "
        "Titan's lower troposphere inferred from a climate model. "
        "Nature Geoscience 5:106-109. DOI: 10.1038/ngeo1374"
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "OROGRAPHIC_FORCINGS",
    "SOURCES",
    "OrographicForcing",
]
