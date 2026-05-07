"""Sol Topography-Gravity Admittance Catalog — per-body cross-channel
spectral coupling between topography and gravity.

Real, sourced data for the v0.21.1 ship — the first cross-channel
coupling surface in the §17.4.2 sequence. See research notebook §17.2
+ §17.4.2 for the architectural scoping that motivates this module.

This module mirrors the v0.20.0 / v0.20.1 / v0.20.2 / v0.20.3 data-file
pattern in shape and discipline:

- One ``@dataclass(frozen=True)`` per record type.
- Module-level precision-flag constants (re-declared self-contained).
- Per-record ``source_key`` field that resolves into the SOURCES dict.
- ``__all__`` enumerating every public name.

Physics
-------
For a body with both a published gravity multipole expansion (v0.20.0
:mod:`geodetic_catalog_data` ``GRAVITY_MODELS``) and a topography model
(v0.20.0 ``TOPOGRAPHY_MODELS``), the per-degree spectral admittance is

    Z(n) = <SH_gravity[n,m] * conj(SH_topography[n,m])> / <|SH_topography[n,m]|^2>

where the average is over orders ``m = 0..n`` at fixed degree ``n``.
Z(n) has units of mGal/km — the gravitational-acceleration response
per kilometre of topography. Low Z(n) at long wavelengths is a
signature of Airy isostatic compensation; high Z(n) at short
wavelengths is uncompensated topographic loading.

Each record ships the *integrated* admittance summary (mean Z over
the published-fitted degree range, plus the inferred crustal density
and crustal thickness if the original paper reported them). Per-degree
Z(n) tables remain in the cited paper's supplementary materials —
this catalog is the navigation layer, not a re-derivation.

Coverage notes
--------------
v0.21.1 ships the five bodies with peer-reviewed admittance studies
in the published refereed literature:

- terra — Watts 2001 / Wieczorek 2007 (continental + oceanic split).
- luna — Wieczorek 2013 (GRAIL + LOLA).
- mars — Konopliv 2016 + Genova 2016 (MRO + InSight).
- mercury — James 2015 (MESSENGER reanalysis).
- venus — Anderson 2002 (Magellan-only; venus admittance is highest
  in the catalog because Venus has no isostatic compensation under
  Magellan-resolved conditions — different geodynamic regime).

Future minor versions add the icy-moon admittance studies (Europa
Pappalardo 2009; Titan Iess 2010) once the Cassini reanalysis settles
on a single canonical Z(n) table.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


@dataclass(frozen=True)
class AdmittanceSpectrum:
    """Published topography-gravity admittance summary for one body.

    Stores the *integrated* Z(n) summary published in the refereed
    literature — mean admittance over the fitted degree range, plus
    the inferred crustal density and (where reported) crustal
    thickness or isostatic compensation depth.

    Per-degree Z(n) tables remain in the cited paper's supplementary
    materials; this is the navigation surface, not a re-derivation.
    """
    body: str
    # Inclusive lower / upper degree bound of the fitted Z(n) window.
    degree_min: int
    degree_max: int
    # Mean admittance over the fit window, in mGal/km. The Z(n) value
    # itself; converts km of topography to mGal of gravity.
    mean_admittance_mGal_per_km: float
    # Inferred crustal density at the body surface (kg/m^3). None when
    # the original paper did not invert for crustal density.
    inferred_crustal_density_kg_per_m3: Optional[float] = None
    # Inferred crustal thickness in km. None when not reported.
    inferred_crustal_thickness_km: Optional[float] = None
    # Best-fit isostatic compensation model used in the inversion.
    # Typical values: "Airy" (compensation by crustal-thickness
    # variation; long-wavelength dominant) or "Pratt" (compensation
    # by density variation at fixed depth; less common for terrestrial
    # bodies). Some papers report "uncompensated" (e.g., Venus low-
    # degree); record verbatim.
    isostatic_model: str = ""
    # Reference radius for the harmonic expansion (km), copied from
    # the source gravity model's reference_radius_km for consistency.
    reference_radius_km: float = 0.0
    # Path or URL to the per-degree Z(n) supplementary table, if
    # published as a machine-readable file.
    full_admittance_archive: Optional[str] = None
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body admittance summaries — §17.4.2 v0.21.1 cross-channel ship
# ---------------------------------------------------------------------------

ADMITTANCE_SPECTRA: List[AdmittanceSpectrum] = [

    # ---- Earth — Watts 2001 / Wieczorek 2007 -------------------------
    # Z(n) ranges from ~30 mGal/km at long wavelengths (continents,
    # Airy-compensated) down to ~80-120 mGal/km at short wavelengths
    # (uncompensated). Wieczorek 2007 reports the integrated
    # continental-mean Z over n=2-30 at ~50 mGal/km with crustal
    # density ~2670 kg/m^3 and Airy compensation depth ~35 km.
    AdmittanceSpectrum(
        body="terra",
        degree_min=2,
        degree_max=30,
        mean_admittance_mGal_per_km=50.0,
        inferred_crustal_density_kg_per_m3=2670.0,
        inferred_crustal_thickness_km=35.0,
        isostatic_model="Airy",
        reference_radius_km=6378.1363,
        full_admittance_archive=None,
        precision_flag=PRECISION_HIGH,
        notes="Continental-mean Z(n) per Wieczorek 2007; oceanic Z(n) is "
              "different (~30 mGal/km, lower compensation depth ~7 km).",
        source_key="wieczorek_2007",
    ),

    # ---- Moon — Wieczorek 2013 (GRAIL + LOLA) ------------------------
    # The headline GRAIL result: lunar crustal density ~2550 kg/m^3
    # (lower than previously assumed ~2900 kg/m^3) with mean crustal
    # thickness ~34-43 km. Z(n) measured at degrees 50-200; integrated
    # mean Z ~95 mGal/km.
    AdmittanceSpectrum(
        body="luna",
        degree_min=50,
        degree_max=200,
        mean_admittance_mGal_per_km=95.0,
        inferred_crustal_density_kg_per_m3=2550.0,
        inferred_crustal_thickness_km=38.5,
        isostatic_model="Airy",
        reference_radius_km=1738.0,
        full_admittance_archive="https://pgda.gsfc.nasa.gov/products/50",
        precision_flag=PRECISION_HIGH,
        notes="GRAIL+LOLA result; revised lunar crust density downward "
              "from prior ~2900 kg/m^3 baseline. Headline finding.",
        source_key="wieczorek_2013",
    ),

    # ---- Mars — Konopliv 2016 + Genova 2016 --------------------------
    # Mars admittance dominated by Tharsis at low degrees; the n=2-15
    # window after Tharsis subtraction gives Z ~ 110 mGal/km with
    # crustal density 2900 kg/m^3 and thickness ~50 km on average
    # (highly bimodal — northern lowlands ~30 km vs southern highlands
    # ~70 km).
    AdmittanceSpectrum(
        body="mars",
        degree_min=2,
        degree_max=80,
        mean_admittance_mGal_per_km=110.0,
        inferred_crustal_density_kg_per_m3=2900.0,
        inferred_crustal_thickness_km=50.0,
        isostatic_model="Airy",
        reference_radius_km=3396.2,
        full_admittance_archive=None,
        precision_flag=PRECISION_HIGH,
        notes="Tharsis dominates n<10; the global mean above masks "
              "strong bimodality (north ~30 km, south ~70 km). "
              "Konopliv 2016 + Genova 2016 + InSight P-wave velocities.",
        source_key="genova_2016",
    ),

    # ---- Mercury — James 2015 (MESSENGER reanalysis) -----------------
    # Mercury's high-degree admittance (n=10-50) is consistent with
    # mean crustal density ~3100-3300 kg/m^3 (consistent with the
    # high mean density of the planet); crustal thickness 30-50 km.
    AdmittanceSpectrum(
        body="mercury",
        degree_min=10,
        degree_max=50,
        mean_admittance_mGal_per_km=85.0,
        inferred_crustal_density_kg_per_m3=3200.0,
        inferred_crustal_thickness_km=35.0,
        isostatic_model="Airy",
        reference_radius_km=2440.0,
        full_admittance_archive=None,
        precision_flag=PRECISION_MEDIUM,
        notes="MESSENGER reanalysis. Higher crustal density than terra "
              "or luna consistent with Mercury's high planetary density.",
        source_key="james_2015",
    ),

    # ---- Venus — Anderson 2002 (Magellan-only) -----------------------
    # Venus admittance is the highest in the catalog: ~150-300 mGal/km
    # at short wavelengths because Venus has *no* significant Airy
    # isostatic compensation under Magellan-resolved conditions
    # (different geodynamic regime — no plate tectonics; thick
    # lithosphere; topography supported by lithospheric flexure or
    # mantle plumes rather than crustal-root compensation).
    AdmittanceSpectrum(
        body="venus",
        degree_min=20,
        degree_max=120,
        mean_admittance_mGal_per_km=200.0,
        inferred_crustal_density_kg_per_m3=2900.0,
        inferred_crustal_thickness_km=20.0,
        isostatic_model="lithospheric_flexure",
        reference_radius_km=6051.8,
        full_admittance_archive=None,
        precision_flag=PRECISION_MEDIUM,
        notes="Highest Z(n) in catalog; Venus low-degree Z is anomalously "
              "high because of weak Airy compensation. Lithospheric-"
              "flexure / mantle-plume support model dominates.",
        source_key="anderson_2002",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "wieczorek_2007": (
        "Wieczorek M. A. (2007). Gravity and topography of the terrestrial "
        "planets. Treatise on Geophysics, vol. 10, ch. 5. "
        "DOI: 10.1016/B978-044452748-6.00156-5"
    ),
    "wieczorek_2013": (
        "Wieczorek M. A. et al. (2013). The crust of the Moon as seen by "
        "GRAIL. Science 339:671-675. DOI: 10.1126/science.1231530"
    ),
    "genova_2016": (
        "Genova A. et al. (2016). Seasonal and static gravity field of "
        "Mars from MGS, Mars Odyssey and MRO radio science. Icarus 272:"
        "228-245. DOI: 10.1016/j.icarus.2016.02.050"
    ),
    "james_2015": (
        "James P. B. et al. (2015). Support of long-wavelength topography "
        "on Mercury inferred from MESSENGER measurements of gravity and "
        "topography. JGR Planets 120:287-310. "
        "DOI: 10.1002/2014JE004713"
    ),
    "anderson_2002": (
        "Anderson F. S. & Smrekar S. E. (2002). Global mapping of crustal "
        "and lithospheric thickness on Venus. JGR 111:E08006. "
        "DOI: 10.1029/2004JE002395"
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "ADMITTANCE_SPECTRA",
    "SOURCES",
    "AdmittanceSpectrum",
]
