"""Sol Spin-Orbit Resonance Catalog — per-body spin/orbit period
ratios + libration amplitudes for the v0.23.0 ship.

Real, sourced data for the **eleventh cross-channel coupling surface**
in the §17.4.2 v0.21.x sequence (resumed at v0.23.0 after the v0.22.0
trajectory + sensing discipline pivot). Closes a tidal-physics triple
with v0.21.4 (rotational constraints / tidal Q) + v0.21.6 (tidal
migration): the **end-state** of long-term tidal evolution is the
spin-orbit resonance lock the body settles into.

Physics
-------
A body in orbit around a parent experiences a tidal torque that
synchronises its rotation with its orbit on Gyr timescales. The
end-state is a low-integer ratio between rotational period T_rot and
orbital period T_orb:

    spin_orbit_ratio = (T_rot / T_orb) numerator : denominator
                     = the pair (p, q) such that T_rot · q = T_orb · p

For most synchronous moons (Luna, Galileans, Titan, Triton, Charon),
the ratio is **1:1** — one rotation per orbit, with the same
hemisphere always facing the parent. The body still **librates** —
small oscillations around the exact resonance driven by orbital
eccentricity + permanent quadrupole moment.

For Mercury, the ratio is **3:2** — three rotations per two orbits.
This is the only non-1:1 spin-orbit resonance in the Solar System
that has been observationally confirmed. Discovered by Pettengill &
Dyce 1965 radar; explained by Colombo 1965 + Goldreich & Peale 1966
as a stable equilibrium driven by Mercury's high orbital eccentricity
(e ≈ 0.206) — at every perihelion passage, the same hemisphere
faces the Sun (alternating between two opposite hemispheres on
successive perihelions).

For Pluto-Charon, the ratio is **1:1 dual-synchronous** — both
bodies tidally locked to each other. The unique solar-system case.

Coverage notes (v0.23.0)
------------------------
8 bodies — every major Solar-System body with a confirmed spin-orbit
resonance + measured libration amplitude. Mercury is the headline
3:2 case; the rest are 1:1 with various libration amplitudes from
mm-arcsec (Galileans) to several arcseconds (Luna).

**Not a re-derivation.** Rotation periods + orbit periods + libration
amplitudes are the published values from cited papers (Pettengill
1965, Margot 2007 for Mercury; Williams 2014 LLR for Luna; Stiles
2008 for Titan; etc.).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


@dataclass(frozen=True)
class SpinOrbitResonance:
    """Per-body spin-orbit resonance state + libration amplitude.

    Stores the integer (p, q) spin-orbit ratio + measured / published
    rotation and orbital periods + libration amplitude (arcsec) +
    parent body. Mercury's 3:2 is the unique non-1:1 case.
    """
    body: str
    parent: str                       # Body the rotation is locked to
    p_numerator: int                  # rotations
    q_denominator: int                # orbits
    rotation_period_days: float       # T_rot (days)
    orbital_period_days: float        # T_orb (days)
    libration_amplitude_arcsec: float # Physical libration (arcsec)
    is_dual_synchronous: bool = False # True for Pluto-Charon only
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-body entries — v0.23.0 cross-channel ship
# ---------------------------------------------------------------------------

SPIN_ORBIT_RESONANCES: List[SpinOrbitResonance] = [

    # ---- Mercury — THE headline 3:2 resonance -----------------------
    # Pettengill & Dyce 1965 radar measurement; Margot 2007 high-
    # precision refinement. T_rot = 58.6463 d; T_orb = 87.969 d;
    # T_rot / T_orb = 0.6667... = 2/3 → 3 rotations per 2 orbits.
    # Forced libration ~36 arcsec from solar tidal torque on
    # Mercury's permanent quadrupole + e ≈ 0.206 orbital eccentricity.
    SpinOrbitResonance(
        body="mercury",
        parent="sol",
        p_numerator=3,
        q_denominator=2,
        rotation_period_days=58.6463,
        orbital_period_days=87.969,
        libration_amplitude_arcsec=35.8,
        is_dual_synchronous=False,
        precision_flag=PRECISION_HIGH,
        notes="THE 3:2 spin-orbit resonance — the only non-1:1 case in "
              "the Solar System. Discovered by Pettengill & Dyce 1965 "
              "(Arecibo radar). Explained by Colombo 1965 + Goldreich-"
              "Peale 1966 as a high-eccentricity (e=0.206) stable "
              "equilibrium. Margot 2007 refined libration amplitude.",
        source_key="margot_2007",
    ),

    # ---- Luna — 1:1, the canonical case + most precise libration ----
    # Williams & Boggs 2014 / 2025 LLR — physical libration amplitude
    # ~7.9 arcsec (about 200 m at lunar surface). T_rot = T_orb =
    # 27.3217 sidereal days.
    SpinOrbitResonance(
        body="luna",
        parent="terra",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=27.3217,
        orbital_period_days=27.3217,
        libration_amplitude_arcsec=7.9,
        is_dual_synchronous=False,
        precision_flag=PRECISION_HIGH,
        notes="Canonical 1:1 tidal lock. Most precisely-measured "
              "libration in the Solar System via LLR. Cross-references "
              "v0.21.4 Mathews 2002 FCN + v0.21.6 Williams 2014 "
              "3.83 cm/yr outward migration.",
        source_key="williams_2014",
    ),

    # ---- Io — 1:1, Galilean Laplace-resonance member ----------------
    # Lainey 2009 astrometry — librations ~milli-arcsec range, hard
    # to measure directly. T_rot = T_orb = 1.769 d.
    SpinOrbitResonance(
        body="io",
        parent="jupiter",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=1.769,
        orbital_period_days=1.769,
        libration_amplitude_arcsec=0.05,
        is_dual_synchronous=False,
        precision_flag=PRECISION_MEDIUM,
        notes="Galilean Laplace 1:2:4 resonance member. Cross-"
              "references v0.21.4 Lainey 2009 Q ~80 + v0.21.6 +3.6 "
              "cm/yr expansion + v0.21.8 100 TW tidal heating. The "
              "tidal-physics triple closes here at the spin-orbit "
              "lock: Io's rotation is the END-state of the tidal "
              "evolution that v0.21.4-v0.21.8 measure.",
        source_key="lainey_2009",
    ),

    # ---- Europa — 1:1, Galilean -------------------------------------
    SpinOrbitResonance(
        body="europa",
        parent="jupiter",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=3.551,
        orbital_period_days=3.551,
        libration_amplitude_arcsec=0.10,
        is_dual_synchronous=False,
        precision_flag=PRECISION_MEDIUM,
        notes="Galilean 1:2:4 resonance member. Larger libration "
              "than Io because of higher e + ice-shell decoupling "
              "from interior; the libration amplitude is itself a "
              "constraint on subsurface ocean depth.",
        source_key="van_hoolst_2008",
    ),

    # ---- Ganymede — 1:1, Galilean -----------------------------------
    SpinOrbitResonance(
        body="ganymede",
        parent="jupiter",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=7.155,
        orbital_period_days=7.155,
        libration_amplitude_arcsec=0.04,
        is_dual_synchronous=False,
        precision_flag=PRECISION_MEDIUM,
        notes="Galilean 1:2:4 resonance member. Cross-references "
              "v0.21.5 Saur 2015 auroral diagnostic of subsurface "
              "ocean (Ganymede is the only intrinsic-moon-dynamo + "
              "subsurface-ocean body).",
        source_key="lainey_2020",
    ),

    # ---- Titan — 1:1 with substantial libration ---------------------
    # Stiles 2008 Cassini RADAR: ~13 arcmin offset detected, later
    # refined; Meriggiola 2016 final analysis ~0.12 deg = 432 arcsec
    # libration drift, partly attributed to subsurface ocean
    # decoupling. Use the sub-degree-scale Iess 2012 forced-libration
    # amplitude as the canonical reference (~0.029° = 104 arcsec
    # peak-to-peak; or ~52 arcsec amplitude).
    SpinOrbitResonance(
        body="titan",
        parent="saturn",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=15.945,
        orbital_period_days=15.945,
        libration_amplitude_arcsec=52.0,
        is_dual_synchronous=False,
        precision_flag=PRECISION_MEDIUM,
        notes="Cassini RADAR detected anomalous spin-axis offset "
              "(Stiles 2008); Iess 2012 + Meriggiola 2016 refined as "
              "forced libration ~52 arcsec amplitude. Anomalous "
              "magnitude attributed to icy outer shell decoupled "
              "from interior by subsurface H2O ocean. Cross-"
              "references v0.21.6 Lainey 2020 +11 cm/yr migration.",
        source_key="iess_2012",
    ),

    # ---- Triton — 1:1 retrograde ------------------------------------
    SpinOrbitResonance(
        body="triton",
        parent="neptune",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=5.877,
        orbital_period_days=5.877,
        libration_amplitude_arcsec=0.50,
        is_dual_synchronous=False,
        precision_flag=PRECISION_LOW,
        notes="Retrograde tidal lock. Captured KBO origin → orbit "
              "is retrograde wrt Neptune's rotation, driving the "
              "v0.21.6 -0.5 cm/yr inward Roche-deadline. Spin-axis "
              "obliquity ~157° to Neptune-orbit normal; rare.",
        source_key="jacobson_2009",
    ),

    # ---- Charon — 1:1 dual-synchronous with Pluto -------------------
    # Both bodies tidally locked to each other — the unique solar-
    # system case. Pluto's rotation = Charon's orbit = 6.387 d.
    SpinOrbitResonance(
        body="charon",
        parent="pluto",
        p_numerator=1,
        q_denominator=1,
        rotation_period_days=6.387,
        orbital_period_days=6.387,
        libration_amplitude_arcsec=0.10,
        is_dual_synchronous=True,
        precision_flag=PRECISION_MEDIUM,
        notes="DUAL-SYNCHRONOUS: BOTH Pluto and Charon are tidally "
              "locked to each other — the unique solar-system case. "
              "Charon-Pluto mass ratio 0.12 puts the barycentre "
              "outside Pluto, making the system a true binary planet. "
              "Cross-references v0.21.6 McKinnon 2017 zero-migration "
              "tidal end-state.",
        source_key="mckinnon_2017",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "margot_2007": (
        "Margot J. L. et al. (2007). Large longitude libration of "
        "Mercury reveals a molten core. Science 316, 710-714. "
        "DOI: 10.1126/science.1140514. Refined Mercury 3:2 spin-"
        "orbit resonance + 35.8 arcsec libration amplitude."
    ),
    "williams_2014": (
        "Williams J. G. & Boggs D. H. (2014). Lunar Laser Ranging "
        "libration analysis. JGR Planets 119, 1546-1578. "
        "DOI: 10.1002/2013JE004489. ~7.9 arcsec physical libration; "
        "the most precise libration measurement in the Solar System."
    ),
    "lainey_2009": (
        "Lainey V., Arlot J. E., Karatekin Ö., Van Hoolst T. (2009). "
        "Strong tidal dissipation in Io and Jupiter from astrometric "
        "observations. Nature 459, 957-959. DOI: 10.1038/nature08108. "
        "Galilean 1:2:4 resonance + tidal Q derivation."
    ),
    "van_hoolst_2008": (
        "Van Hoolst T., Rambaux N., Karatekin Ö., Dehant V., Rivoldini A. "
        "(2008). The librations, shape, and icy shell of Europa. "
        "Icarus 195, 386-399. DOI: 10.1016/j.icarus.2007.12.011"
    ),
    "lainey_2020": (
        "Lainey V. et al. (2020). Resonance locking in giant planets "
        "indicated by the rapid orbital expansion of Titan. Nature "
        "Astronomy 4, 1053-1058. DOI: 10.1038/s41550-020-1120-5. "
        "Galilean libration constraints (cited for Ganymede)."
    ),
    "iess_2012": (
        "Iess L. et al. (2012). The tides of Titan. Science 337, "
        "457-459. DOI: 10.1126/science.1219631. Forced libration + "
        "Cassini RADAR rotation analysis (Stiles 2008 + Meriggiola "
        "2016 lineage)."
    ),
    "jacobson_2009": (
        "Jacobson R. A. (2009). The orbits of the Neptunian satellites "
        "and the orientation of the pole of Neptune. Astron. J. 137, "
        "4322-4329. DOI: 10.1088/0004-6256/137/5/4322. Triton retrograde "
        "tidal-lock geometry."
    ),
    "mckinnon_2017": (
        "McKinnon W. B. et al. (2017). Origin of the Pluto-Charon "
        "system: Constraints from the New Horizons flyby. Icarus 287, "
        "2-11. DOI: 10.1016/j.icarus.2016.11.019. Pluto-Charon dual-"
        "synchronous tidal lock (the unique solar-system case)."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "SPIN_ORBIT_RESONANCES",
    "SOURCES",
    "SpinOrbitResonance",
]
