"""Sol Toroidal-Residual J₂ Catalog — per-body classification on the
Chandrasekhar 1969 rotating-fluid equilibrium sequence.

Real, sourced data for the v0.24.4 ship — the **fifth ship in v0.24.x**
and the explicit codification of the user-named insight: **rotation
makes the body toroidal, self-gravity rounds it back toward spherical**.
The leftover "torus residual" — the deviation of a body's actual shape
from a perfect sphere — is captured quantitatively by the J₂
gravitational quadrupole coefficient.

Physics
-------
A rotating self-gravitating fluid in hydrostatic equilibrium settles
into a sequence of equilibrium figures parameterised by the
**dimensionless rotation parameter**:

    q = ω² R³ / (GM)

(equivalently 2T/|W| where T is rotational kinetic energy, W is
gravitational binding energy). The Chandrasekhar 1969 textbook
*Ellipsoidal Figures of Equilibrium* establishes the sequence:

* **Sphere** (q → 0): perfectly spherical
* **Maclaurin spheroid** (0 < q < q_M): axially-symmetric oblate;
  centrifugal force makes the equator bulge while gravity pulls
  the poles in. Earth, Mars, Mercury, Luna, Venus all sit here at
  small q (< 5%); the giants sit here at large q.
* **Maclaurin → Jacobi bifurcation** at **q ≈ 0.187**: the
  Maclaurin sequence becomes secularly unstable to triaxial
  perturbations.
* **Jacobi triaxial ellipsoid** (q > q_M): genuinely three-axis
  (a ≠ b ≠ c). Haumea is the famous Solar-System example —
  visibly cigar-shaped.
* **Bar instability** at q ≈ 0.270: the Jacobi sequence becomes
  dynamically unstable; the body elongates into a bar.
* **Roche limit** at q ≈ 0.36 (radial-disruption threshold): the
  body literally fissions; matter at the equator is no longer
  bound and a ring/torus forms. Saturn's rings are inside the
  Roche limit; the same matter on a single self-gravitating body
  could not have remained a sphere.

So as rotation increases relative to self-gravity, the body's
shape walks along this sequence:

    Sphere → Maclaurin → Jacobi → bar → ring/torus

The user's insight in plain language: rotation forces the body
toward toroidal; self-gravity restores it toward spherical;
J₂ (the leading rotation-induced gravitational distortion) is
the quantitative measure of where in the sequence the body sits.

The Darwin-Radau approximation links J₂ to q + the moment-of-
inertia factor I_M = C/(MR²):

    J₂ ≈ (5/2) · q · (1 - 3/2 · I_M)  /  (5 - 3 I_M)

For uniform density (I_M = 2/5): J₂ ≈ q/2.
For Earth (I_M ≈ 0.33): J₂ ≈ q/3.
For gas giants (centrally concentrated; I_M ≈ 0.25): J₂ ≈ 2q/5.

Special cases
-------------
- **Luna's J₂ exceeds the rotation-equilibrium prediction by ~3×**
  because Luna's figure was **frozen in** when it rotated faster
  (closer to Earth, before tidal recession to 384,000 km). Luna
  is therefore a **fossil-J₂** case — the body's shape is a
  diagnostic of historical rotation, not present rotation.
- **Mercury's J₂ exceeds prediction by 50×** for the same reason —
  the 3:2 spin-orbit lock has rotation slow today, but Mercury's
  shape was set when it spun faster + experienced solar tidal
  forcing.
- **Saturn's q ≈ 0.15** puts it dangerously close to the
  Maclaurin-Jacobi bifurcation at q = 0.187 — Saturn is the
  closest Solar-System body to that threshold and has the
  largest oblateness (~10% flattening).

Coverage notes (v0.24.4)
------------------------
14 bodies — all Solar-System bodies with reliable measured J₂ +
rotation-period + mass. Cross-references v0.20.0 geodetic catalog
for J₂ values and v0.16.0 BODIES table for periods + masses.

**Not a re-derivation.** J₂ values are from cited gravity-field
papers; rotation periods + masses are NASA Planetary Fact Sheet /
JPL DE441; q is computed from ω, R, M.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Chandrasekhar 1969 sequence-bifurcation thresholds -------------
# The threshold values in dimensionless rotation parameter q.
# Numerical values from Chandrasekhar 1969 + Lai 1994 review.
Q_MACLAURIN_JACOBI_BIFURCATION: float = 0.18712   # q at e ≈ 0.81267
Q_JACOBI_BAR_INSTABILITY: float = 0.27            # secular bar-mode onset
Q_ROCHE_FISSION: float = 0.36                     # equatorial unbinding


@dataclass(frozen=True)
class ToroidalResidual:
    """Per-body classification on the Chandrasekhar equilibrium sequence.

    Each body's quantitative position on the sequence:

      q = ω²R³/(GM)  → dimensionless rotation parameter
      J₂_observed   → measured gravitational quadrupole (v0.20.0)
      J₂_predicted  → Darwin-Radau prediction from q + I_M
      regime        → Sphere / Maclaurin / Jacobi / Bar / Ring

    Bodies whose observed J₂ exceeds the prediction by more than
    a small factor are "fossil" cases — their shape was set by
    historical rotation, not current rotation (Luna, Mercury).
    """
    body: str
    rotation_period_days: float       # T_rot (positive; sign of ω implicit)
    equatorial_radius_km: float       # R (km)
    GM_m3_s2: float                    # G·M (m³/s²)
    rotation_parameter_q: float        # q = ω²R³/(GM)
    J2_observed: float                 # measured gravitational quadrupole
    moment_of_inertia_factor: float    # I_M = C/(MR²); 2/5 if uniform
    regime: str                        # "sphere"/"maclaurin"/"jacobi"/"bar"/"ring"
    fossil_figure: bool                # True if J₂ >> q · prediction
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


def _compute_q(rotation_period_days: float, R_km: float,
               GM: float) -> float:
    """Compute dimensionless rotation parameter q = ω²R³/(GM).

    For retrograde rotators (Venus, Uranus), the *magnitude* of ω
    is what matters for the figure-of-equilibrium calculation.
    """
    period_s = abs(rotation_period_days) * 86400.0
    omega = 2.0 * math.pi / period_s
    R_m = R_km * 1000.0
    return (omega ** 2) * (R_m ** 3) / GM


def _classify_regime(q: float) -> str:
    """Classify a body's regime from its dimensionless rotation
    parameter q on the Chandrasekhar sequence."""
    if q < 0.001:
        return "sphere"
    elif q < Q_MACLAURIN_JACOBI_BIFURCATION:
        return "maclaurin"
    elif q < Q_JACOBI_BAR_INSTABILITY:
        return "jacobi"
    elif q < Q_ROCHE_FISSION:
        return "bar"
    else:
        return "ring"


# ---------------------------------------------------------------------------
# Per-body roster
# ---------------------------------------------------------------------------

# Helper: build the entries with q computed from inputs.

def _build_entry(
    body: str,
    rotation_period_days: float,
    R_km: float,
    GM_m3_s2: float,
    J2_observed: float,
    moment_of_inertia_factor: float,
    fossil_figure: bool,
    source_key: str,
    notes: Optional[str] = None,
    precision_flag: str = PRECISION_HIGH,
) -> ToroidalResidual:
    q = _compute_q(rotation_period_days, R_km, GM_m3_s2)
    regime = _classify_regime(q)
    return ToroidalResidual(
        body=body,
        rotation_period_days=rotation_period_days,
        equatorial_radius_km=R_km,
        GM_m3_s2=GM_m3_s2,
        rotation_parameter_q=q,
        J2_observed=J2_observed,
        moment_of_inertia_factor=moment_of_inertia_factor,
        regime=regime,
        fossil_figure=fossil_figure,
        notes=notes,
        source_key=source_key,
        precision_flag=precision_flag,
    )


TOROIDAL_RESIDUALS: List[ToroidalResidual] = [

    # ---- Terra (Earth) — canonical Maclaurin reference -------------
    _build_entry(
        body="terra",
        rotation_period_days=0.99726968,            # sidereal day
        R_km=6378.137,
        GM_m3_s2=3.986004418e14,
        J2_observed=1.08263e-3,                      # GGM05 / EGM2008
        moment_of_inertia_factor=0.3307,
        fossil_figure=False,
        notes="Canonical Maclaurin reference: q ≈ 3.46e-3, J₂ ≈ "
              "1.08e-3 ≈ q/3. Earth is well within Maclaurin "
              "regime; q << q_bifurcation = 0.187.",
        source_key="egm2008",
    ),

    # ---- Mars — Maclaurin (slightly more rotation per gravity) -----
    _build_entry(
        body="mars",
        rotation_period_days=1.02595675,
        R_km=3389.5,
        GM_m3_s2=4.282837e13,
        J2_observed=1.9555e-3,
        moment_of_inertia_factor=0.3645,             # Le Maistre 2023
        fossil_figure=False,
        notes="Slightly more rotation-per-gravity than Earth (lower "
              "GM, similar period). Cross-references v0.24.2 + "
              "v0.21.4 Mars C/MR² = 0.3645.",
        source_key="genova_2016",
    ),

    # ---- Venus — slowest rotator + retrograde; tiny q --------------
    _build_entry(
        body="venus",
        rotation_period_days=243.0226,               # retrograde
        R_km=6051.8,
        GM_m3_s2=3.24859e14,
        J2_observed=4.458e-6,                         # Anderson 2002
        moment_of_inertia_factor=0.337,
        fossil_figure=False,
        notes="Slowest planetary rotator. Retrograde; magnitude of ω "
              "is what matters for figure equilibrium. q ~ 10⁻⁷, "
              "essentially spherical.",
        source_key="anderson_2002_venus",
    ),

    # ---- Mercury — fossil 3:2 lock figure --------------------------
    _build_entry(
        body="mercury",
        rotation_period_days=58.6463,
        R_km=2439.7,
        GM_m3_s2=2.20329e13,
        J2_observed=5.03e-5,                          # MESSENGER (Smith 2012)
        moment_of_inertia_factor=0.346,               # Margot 2007
        fossil_figure=True,
        notes="FOSSIL figure: 3:2 spin-orbit lock makes present-day q "
              "tiny, but observed J₂ ≈ 50× rotation-equilibrium "
              "prediction. Mercury's shape was set during faster "
              "early rotation + solar tidal forcing.",
        source_key="smith_2012_messenger",
    ),

    # ---- Luna — fossil figure (frozen at faster rotation) ----------
    _build_entry(
        body="luna",
        rotation_period_days=27.3217,                 # synchronous with orbit
        R_km=1737.4,
        GM_m3_s2=4.9048695e12,
        J2_observed=2.0321e-4,                        # GRAIL (Konopliv 2013)
        moment_of_inertia_factor=0.3932,              # Williams 2014
        fossil_figure=True,
        notes="FOSSIL figure: J₂ ≈ 25× current-rotation prediction. "
              "Luna's shape was frozen in when Luna was much closer "
              "to Earth (faster rotation + larger Earth tidal "
              "distortion). Cross-references v0.21.6 +3.83 cm/yr "
              "tidal recession.",
        source_key="konopliv_2013_grail",
    ),

    # ---- Jupiter — moderate Maclaurin (large q for a planet) ------
    _build_entry(
        body="jupiter",
        rotation_period_days=0.41354,                 # 9h 55m 30s
        R_km=71492.0,                                  # 1-bar equator
        GM_m3_s2=1.26687e17,
        J2_observed=0.014697,                          # Iess 2018 Juno
        moment_of_inertia_factor=0.2538,               # Helled 2011
        fossil_figure=False,
        notes="Solid-body Jupiter classification skirts the regime "
              "boundary. q ≈ 0.089 — half-way to the Maclaurin-"
              "Jacobi bifurcation. Visibly oblate (1/15 flattening). "
              "J₂ ≈ q/6 (lower because central density concentration).",
        source_key="iess_2018_juno",
    ),

    # ---- Saturn — closest to Maclaurin-Jacobi bifurcation ---------
    _build_entry(
        body="saturn",
        rotation_period_days=0.43958,                 # Mankovich-Fuller 2021 ring seismology: 10:33
        R_km=60268.0,                                  # 1-bar equator
        GM_m3_s2=3.79313e16,
        J2_observed=0.016291,                          # Iess 2019 Cassini
        moment_of_inertia_factor=0.220,               # Helled 2011
        fossil_figure=False,
        notes="THE EXTREME CASE. q ≈ 0.155, dangerously close to "
              "Maclaurin-Jacobi bifurcation at q=0.187. Most oblate "
              "Solar-System body: 1/10 flattening. Cross-references "
              "v0.21.4 Mankovich-Fuller 2021 ring-seismology rotation-"
              "period revision (10:39 → 10:33).",
        source_key="iess_2019_cassini",
    ),

    # ---- Uranus — Maclaurin --------------------------------------
    _build_entry(
        body="uranus",
        rotation_period_days=0.71833,
        R_km=25559.0,
        GM_m3_s2=5.794e15,
        J2_observed=0.003510,                          # Voyager + occultations
        moment_of_inertia_factor=0.230,
        fossil_figure=False,
        notes="Modest q (~0.029) puts Uranus deep in the Maclaurin "
              "regime. J₂ ~ q/8 (centrally concentrated).",
        source_key="jacobson_2014_uranus",
    ),

    # ---- Neptune — Maclaurin --------------------------------------
    _build_entry(
        body="neptune",
        rotation_period_days=0.67125,
        R_km=24764.0,
        GM_m3_s2=6.836e15,
        J2_observed=0.003411,
        moment_of_inertia_factor=0.240,
        fossil_figure=False,
        notes="Similar to Uranus: q ~ 0.026, deep Maclaurin.",
        source_key="jacobson_2009_neptune",
    ),

    # ---- Io — fossil + tidal ---------------------------------------
    _build_entry(
        body="io",
        rotation_period_days=1.769138,
        R_km=1821.6,
        GM_m3_s2=5.96e12,
        J2_observed=1.846e-3,                          # Anderson 2001 Galileo
        moment_of_inertia_factor=0.378,
        fossil_figure=False,
        notes="Tidally-locked rotation. Anderson 2001 Galileo gravity "
              "measurement; consistent with Maclaurin equilibrium "
              "for the synchronous rotation rate + Jupiter tidal "
              "deformation.",
        source_key="anderson_2001_galilean_gravity",
    ),

    # ---- Europa — Maclaurin (synchronous) -------------------------
    _build_entry(
        body="europa",
        rotation_period_days=3.551181,
        R_km=1560.8,
        GM_m3_s2=3.20e12,
        J2_observed=4.36e-4,
        moment_of_inertia_factor=0.346,
        fossil_figure=False,
        source_key="anderson_2001_galilean_gravity",
    ),

    # ---- Ganymede — Maclaurin (synchronous) ----------------------
    _build_entry(
        body="ganymede",
        rotation_period_days=7.155,
        R_km=2634.1,
        GM_m3_s2=9.887e12,
        J2_observed=1.276e-4,
        moment_of_inertia_factor=0.3115,
        fossil_figure=False,
        source_key="anderson_2001_galilean_gravity",
    ),

    # ---- Callisto — Maclaurin -----------------------------------
    _build_entry(
        body="callisto",
        rotation_period_days=16.689,
        R_km=2410.3,
        GM_m3_s2=7.179e12,
        J2_observed=3.27e-5,                          # Less differentiated
        moment_of_inertia_factor=0.355,
        fossil_figure=False,
        notes="Less differentiated than other Galileans (Anderson "
              "2001); higher I_M reflects more uniform density.",
        source_key="anderson_2001_galilean_gravity",
    ),

    # ---- Titan — Maclaurin (synchronous; thick atmosphere) -------
    _build_entry(
        body="titan",
        rotation_period_days=15.945,
        R_km=2574.7,
        GM_m3_s2=8.978e12,
        J2_observed=3.34e-5,                          # Iess 2010 Cassini
        moment_of_inertia_factor=0.342,
        fossil_figure=False,
        source_key="iess_2010_titan",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "egm2008": (
        "Pavlis N. K. et al. (2012). The development and evaluation of "
        "the Earth Gravitational Model 2008 (EGM2008). JGR Solid Earth "
        "117, B04406. DOI: 10.1029/2011JB008916. Earth gravity field + "
        "J₂ canonical reference."
    ),
    "genova_2016": (
        "Genova A. et al. (2016). Seasonal and static gravity field of "
        "Mars from MGS, Mars Odyssey and MRO radio science. Icarus 272, "
        "228-245. DOI: 10.1016/j.icarus.2016.02.050. MRO99B Mars gravity "
        "model + J₂."
    ),
    "anderson_2002_venus": (
        "Anderson J. D. & Smith J. C. (2002). The gravity field of "
        "Venus -- A reanalysis of Magellan radio tracking. Icarus 159, "
        "517-528. DOI: 10.1006/icar.2002.6936. Venus gravity field."
    ),
    "smith_2012_messenger": (
        "Smith D. E. et al. (2012). Gravity field and internal structure "
        "of Mercury from MESSENGER. Science 336, 214-217. "
        "DOI: 10.1126/science.1218809. Mercury MESSENGER gravity model."
    ),
    "konopliv_2013_grail": (
        "Konopliv A. S. et al. (2013). The JPL lunar gravity field to "
        "spherical harmonic degree 660 from the GRAIL Primary Mission. "
        "JGR Planets 118, 1415-1434. DOI: 10.1002/jgre.20097. The GRAIL "
        "lunar gravity catalog."
    ),
    "iess_2018_juno": (
        "Iess L. et al. (2018). Measurement of Jupiter's asymmetric "
        "gravity field. Nature 555, 220-222. DOI: 10.1038/nature25776. "
        "Juno-era J₂ + odd zonal harmonics."
    ),
    "iess_2019_cassini": (
        "Iess L. et al. (2019). Measurement and implications of Saturn's "
        "gravity field and ring mass. Science 364, eaat2965. "
        "DOI: 10.1126/science.aat2965. Cassini Grand Finale gravity "
        "measurements."
    ),
    "jacobson_2014_uranus": (
        "Jacobson R. A. (2014). The orbits of the Uranian satellites "
        "and rings, the gravity field of the Uranian system, and the "
        "orientation of the pole of Uranus. AJ 148, 76. "
        "DOI: 10.1088/0004-6256/148/5/76."
    ),
    "jacobson_2009_neptune": (
        "Jacobson R. A. (2009). The orbits of the Neptunian satellites "
        "and the orientation of the pole of Neptune. AJ 137, 4322-4329. "
        "DOI: 10.1088/0004-6256/137/5/4322."
    ),
    "anderson_2001_galilean_gravity": (
        "Anderson J. D., Jacobson R. A., Lau E. L., Moore W. B., "
        "Schubert G. (2001). Io's gravity field and interior structure. "
        "JGR Planets 106, 32963-32969. DOI: 10.1029/2000JE001367. Plus "
        "companion papers Anderson et al. 1996/1998 for Europa, "
        "Ganymede, Callisto. Galileo radio-science gravity coefficients."
    ),
    "iess_2010_titan": (
        "Iess L. et al. (2010). Gravity field, shape, and moment of "
        "inertia of Titan. Science 327, 1367-1369. "
        "DOI: 10.1126/science.1182583. Cassini-era Titan gravity."
    ),
    "chandrasekhar_1969": (
        "Chandrasekhar S. (1969). Ellipsoidal Figures of Equilibrium. "
        "Yale University Press. The textbook reference for the rotating-"
        "fluid equilibrium-figure sequence: Sphere -> Maclaurin -> "
        "Jacobi -> bar -> ring/torus, with the q ≈ 0.187 Maclaurin-"
        "Jacobi bifurcation."
    ),
    "lai_1994": (
        "Lai D., Rasio F. A., Shapiro S. L. (1994). Ellipsoidal "
        "figures of equilibrium: Compressible models. ApJS 88, 205-252. "
        "DOI: 10.1086/191822. Modern review of bifurcation thresholds + "
        "stability analysis."
    ),
    "helled_2011": (
        "Helled R., Schubert G., Anderson J. D. (2011). Jupiter and "
        "Saturn rotation periods. Planet. Space Sci. 59, 17-24. "
        "DOI: 10.1016/j.pss.2010.10.005. Moment-of-inertia factor "
        "estimates for the gas giants."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "Q_MACLAURIN_JACOBI_BIFURCATION",
    "Q_JACOBI_BAR_INSTABILITY",
    "Q_ROCHE_FISSION",
    "TOROIDAL_RESIDUALS",
    "SOURCES",
    "ToroidalResidual",
]
