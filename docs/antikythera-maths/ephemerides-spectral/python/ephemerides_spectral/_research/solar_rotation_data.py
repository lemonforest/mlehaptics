"""Solar rotation — hand-coded data module (v0.30.0 ship).

The Sun's **surface differential rotation** + **internal rotation**
(helioseismic inversion + tachocline), the first solar-dynamics
extension beyond the v0.24.3 Sun Dynamical Spectrum (helioseismic
p-modes). Rotation-as-a-spectral-profile is explicitly in scope per
``docs/antikythera-maths/CLAUDE.md`` ("rotation as a spectral
profile").

Surface differential rotation
-----------------------------
The Sun does not rotate as a rigid body: the equator laps the poles.
The standard latitude law (Snodgrass & Ulrich 1990, from Doppler
features) is

    Omega(lat) = A + B sin^2(lat) + C sin^4(lat)   [deg/day, sidereal]

with the accepted average coefficients

    A = 14.713 +/- 0.0491   (equatorial rate)
    B = -2.396 +/- 0.188    (mid-latitude shear)
    C = -1.787 +/- 0.253    (high-latitude shear)

Internal rotation
-----------------
Helioseismic inversion (Schou 1998 SOI/MDI; Howe 2009 review) shows:
the **convection zone** (r > 0.7 R_sun) rotates differentially like the
surface; the **radiative interior** (r < 0.7 R_sun) rotates nearly
*rigidly*; the transition is the thin **tachocline** shear layer at
~0.70 R_sun — the seat of the solar dynamo.

Sources
-------
* **Snodgrass & Ulrich 1990** *ApJ* 351:309-316.
  DOI 10.1086/168467. The Doppler-feature surface differential
  rotation law A, B, C. Cited for: the A/B/C coefficients.
* **Carrington 1863** *Observations of the Spots on the Sun*. The
  1850s low-latitude-sunspot determination of the 25.38-day sidereal
  rotation period — the canonical "Carrington rotation" reference the
  package's Sol Carrington Time (``time_scales``) adopts. Cited for:
  the 25.38-day Carrington sidereal period.
* **Schou 1998** *ApJ* 505:390-417. DOI 10.1086/306146. SOI/MDI
  helioseismic inversion of the internal rotation. Cited for: the
  radiative-interior near-rigid rate + the tachocline.
* **Howe 2009** *Living Rev. Solar Phys.* 6:1. DOI 10.12942/lrsp-2009-1.
  Review of solar interior rotation + its variation. Cited for: the
  convection-zone / tachocline / radiative-interior structure.

Cross-references
----------------
* v0.24.3 Sun Dynamical Spectrum — the helioseismic p-mode comb (the
  same SOI/MDI / BiSON instrument family that resolves the internal
  rotation).
* Sol Carrington Time (``time_scales``) — adopts the 25.38-day
  Carrington sidereal period this module's closure reproduces from
  the Snodgrass-Ulrich law.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Surface differential-rotation law (Snodgrass & Ulrich 1990, sidereal)
# ---------------------------------------------------------------------------

#: Equatorial sidereal rotation rate A (deg/day).
SU_A_DEG_PER_DAY: float = 14.713
#: Mid-latitude shear coefficient B (deg/day).
SU_B_DEG_PER_DAY: float = -2.396
#: High-latitude shear coefficient C (deg/day).
SU_C_DEG_PER_DAY: float = -1.787

#: 1-sigma uncertainties on (A, B, C), deg/day (Snodgrass & Ulrich 1990).
SU_A_SIGMA: float = 0.0491
SU_B_SIGMA: float = 0.188
SU_C_SIGMA: float = 0.253


# ---------------------------------------------------------------------------
# Reference constants
# ---------------------------------------------------------------------------

#: Carrington sidereal rotation period (days) — Carrington 1863, the
#: canonical low-latitude reference; matches Sol Carrington Time.
CARRINGTON_SIDEREAL_PERIOD_DAYS: float = 25.38

#: Earth's mean orbital (sidereal) rate, deg/day — for the
#: sidereal -> synodic rotation-period conversion (synodic rate =
#: sidereal rate - Earth's orbital rate).
EARTH_ORBITAL_RATE_DEG_PER_DAY: float = 360.0 / 365.25636

#: Tachocline radius (fraction of R_sun) — the convection-zone /
#: radiative-interior shear boundary (Schou 1998; Howe 2009).
TACHOCLINE_RADIUS_R_SUN: float = 0.70


# ---------------------------------------------------------------------------
# Internal-rotation anchors (helioseismic; Schou 1998 / Howe 2009)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RotationAnchor:
    """One internal/surface rotation anchor.

    ``radius_r_sun`` is the fractional radius (None for a surface-only
    latitude anchor). ``sidereal_period_days`` is the local sidereal
    rotation period; ``regime`` names the dynamical regime.

    Per-row provenance (``source_doi`` / ``source_published_date`` /
    ``entered_locally_at`` / ``source_version``) mirrors the
    ``solar_rotation.rotation_anchor.v1`` JSON Schema so this hand-coded
    path and the AMSC literature_curated path at
    ``research/attested/solar_rotation/`` dual-author the same rows
    (the v0.30.0rc4 dual-author exercise; cf. saturn_rings). The DOIs +
    dates are triality-attested (haiku/sonnet/opus vs ADS/IOP/arXiv);
    dates are written at the granularity all three externally confirmed
    (month where unanimous, else year).
    """

    region: str
    radius_r_sun: Optional[float]
    latitude_deg: Optional[float]
    sidereal_period_days: float
    regime: str
    source_key: str
    source_doi: str
    source_published_date: str
    entered_locally_at: str
    notes: str
    source_version: Optional[str] = None


#: Internal + surface rotation anchors. The two convection-zone surface
#: anchors are the Snodgrass-Ulrich law evaluated at the equator / pole;
#: the radiative-interior anchor is the Schou 1998 near-rigid rate.
ROTATION_ANCHORS: List[RotationAnchor] = [
    RotationAnchor(
        region="convection_zone_equator_surface",
        radius_r_sun=1.0,
        latitude_deg=0.0,
        sidereal_period_days=24.47,
        regime="differential_convection_zone",
        source_key="snodgrass_ulrich_1990",
        source_doi="10.1086/168467",
        source_published_date="1990-03",
        entered_locally_at="2026-06-06",
        notes="Equatorial surface sidereal period 360/A = 360/14.713 = 24.47 d (fastest).",
    ),
    RotationAnchor(
        region="convection_zone_pole_surface",
        radius_r_sun=1.0,
        latitude_deg=90.0,
        sidereal_period_days=34.19,
        regime="differential_convection_zone",
        source_key="snodgrass_ulrich_1990",
        source_doi="10.1086/168467",
        source_published_date="1990-03",
        entered_locally_at="2026-06-06",
        notes="Polar surface sidereal period 360/(A+B+C) = 360/10.530 = 34.19 d (slowest).",
    ),
    RotationAnchor(
        region="tachocline",
        radius_r_sun=0.70,
        latitude_deg=None,
        sidereal_period_days=27.0,
        regime="shear_boundary",
        source_key="schou_1998",
        source_doi="10.1086/306146",
        source_published_date="1998",
        entered_locally_at="2026-06-06",
        notes="The thin shear layer between the differential convection zone and the rigid radiative interior; the dynamo seat. Mean rate ~27 d.",
    ),
    RotationAnchor(
        region="radiative_interior",
        radius_r_sun=0.40,
        latitude_deg=None,
        sidereal_period_days=26.9,
        regime="rigid_body",
        source_key="schou_1998",
        source_doi="10.1086/306146",
        source_published_date="1998",
        entered_locally_at="2026-06-06",
        notes="Below the tachocline the interior rotates nearly rigidly at ~432 nHz (~26.9 d sidereal), independent of latitude (Schou 1998; Howe 2009).",
    ),
]


SOURCES: Dict[str, str] = {
    "snodgrass_ulrich_1990": (
        "Snodgrass H.B., Ulrich R.K. (1990). Rotation of Doppler "
        "features in the solar photosphere. *ApJ* 351:309-316. "
        "DOI: 10.1086/168467. Surface differential-rotation law "
        "Omega(lat) = A + B sin^2(lat) + C sin^4(lat)."
    ),
    "carrington_1863": (
        "Carrington R.C. (1863). *Observations of the Spots on the Sun "
        "from November 9, 1853, to March 24, 1861*. The low-latitude "
        "sunspot determination of the 25.38-day sidereal rotation "
        "period (the canonical Carrington-rotation reference)."
    ),
    "schou_1998": (
        "Schou J. et al. (1998). Helioseismic studies of differential "
        "rotation in the solar envelope by the Solar Oscillations "
        "Investigation using the Michelson Doppler Imager. *ApJ* "
        "505:390-417. DOI: 10.1086/306146. Internal-rotation inversion."
    ),
    "howe_2009": (
        "Howe R. (2009). Solar interior rotation and its variation. "
        "*Living Rev. Solar Phys.* 6:1. DOI: 10.12942/lrsp-2009-1. "
        "Review of the convection-zone / tachocline / radiative-interior "
        "rotation structure."
    ),
}


def anchor_to_data_dict(anchor: RotationAnchor) -> Dict[str, object]:
    """Convert a RotationAnchor to the same dict shape that
    ``bridge.get_attested_dataset('solar_rotation')`` returns in each
    row's ``data`` block (key order matches the
    ``solar_rotation.rotation_anchor.v1`` JSON Schema). Used by the
    dual-author diff test to normalise the two paths before comparison.
    """
    return {
        "region": anchor.region,
        "radius_r_sun": anchor.radius_r_sun,
        "latitude_deg": anchor.latitude_deg,
        "sidereal_period_days": anchor.sidereal_period_days,
        "regime": anchor.regime,
        "source_key": anchor.source_key,
        "source_doi": anchor.source_doi,
        "source_published_date": anchor.source_published_date,
        "entered_locally_at": anchor.entered_locally_at,
        "source_version": anchor.source_version,
        "notes": anchor.notes,
    }


__all__ = [
    "SU_A_DEG_PER_DAY",
    "SU_B_DEG_PER_DAY",
    "SU_C_DEG_PER_DAY",
    "SU_A_SIGMA",
    "SU_B_SIGMA",
    "SU_C_SIGMA",
    "CARRINGTON_SIDEREAL_PERIOD_DAYS",
    "EARTH_ORBITAL_RATE_DEG_PER_DAY",
    "TACHOCLINE_RADIUS_R_SUN",
    "RotationAnchor",
    "ROTATION_ANCHORS",
    "SOURCES",
    "anchor_to_data_dict",
]
