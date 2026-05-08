"""Sol Pluto-Charon Dynamical Spectrum — per-body action-angle
decomposition data for the v0.24.11 ship.

Real, sourced data for the **fourth per-body dynamical-spectrum
surface** in the v0.24.x sequence and the project's first
**binary mutual-tidal-lock** entry. Pluto-Charon is the Solar
System's *only* known double-synchronous binary planet — both
bodies tidally locked to each other simultaneously, with a mutual
orbital period of 6.387 days that *equals* both Pluto's spin
period AND Charon's spin period.

Why Pluto-Charon was chosen for v0.24.11
----------------------------------------
This ship is the Path-B response to the v0.24.10 OOS-probe
catalog's identification of a **feature-schema gap**: bodies with
commensurabilities but no Saros-style multi-millennium prediction
record (Pluto-Charon, Enceladus, Io) all collapsed onto Mercury-
stable in the v0.24.9 classifier because the schema couldn't
distinguish them. The project's discipline says: when the eigen-
basis honestly can't see a distinction, **populate the regime with
a real labelled training example** rather than engineer features.

Pluto-Charon is the cleanest single body to populate that regime
with: it's the unambiguous, paradigmatic mutual tidal lock of the
Solar System. Adding it as a v0.24.11 ship + regime training
example creates a new label, ``rigid_body_action_angle_mutual_lock``,
that the v0.24.10 probe re-run can then test against.

This is not an SGD-style retraining. It's a deterministic
addition: one new training row, one new regime label, the eigenbasis
recomputes via the same closed-form ``np.linalg.eigh`` call. No
random init, no validation split.

Action-angle framing
--------------------
Pluto-Charon's dynamical state factors into action-angle variables
on a **T^n × R^m phase space**, with the unusual property that
**three angle modes are identically locked** (Pluto spin + Charon
spin + mutual orbital sidereal motion):

* Angle variables (live on tori — periodic, modulo 2π):
  - **Mutual orbital sidereal motion** Λ_orb (Pluto-Charon
    binary orbital phase) — period 6.387230 d (Brozovic 2015).
  - **Pluto spin frequency** = mutual orbital frequency
    (1:1 tidal lock; same period).
  - **Charon spin frequency** = mutual orbital frequency
    (1:1 tidal lock; same period).
  - **Apsidal precession** (slow; ~3.2 Myr libration timescale
    per Showalter & Hamilton 2015 stability analysis of small
    moons).
  - **Nodal precession** (relative to Pluto's heliocentric
    orbit).

* Action variables (live on real intervals — slowly varying):
  - **Eccentricity** e ≈ 0.00005 (Brozovic 2015) —
    *roughly 1100x smaller than Luna's 0.0549*. The tidal
    evolution of Pluto-Charon has gone to completion: eccentricity
    has been almost fully damped by mutual tidal dissipation.
  - **Inclination of mutual orbit to Pluto's heliocentric plane**
    ≈ 119.6° (retrograde tilt; Stern 2015 New Horizons).
  - **Mutual obliquity** ≈ 0.0006° (also essentially zero —
    the spin axes are aligned with the mutual orbit normal).
  - **Mass ratio** Charon/Pluto ≈ 0.1218 (Brozovic 2015) —
    the *largest binary mass ratio in the Solar System*; Earth-
    Luna is 0.0123 (~10x smaller). The barycenter sits ~2128 km
    from Pluto's center, **outside** Pluto's surface (which has
    radius 1188 km).

The headline payload — TRIPLE lock + small-moon commensurabilities
------------------------------------------------------------------
Pluto-Charon ships **two** headline observables:

**(1) Triple synchronous lock** (mutual spin-orbit-spin):
::

    P_orb(Pluto-Charon) = P_spin(Pluto) = P_spin(Charon)
                        = 6.387230 days

This is the *end state* of dyadic tidal evolution — once both
bodies are tidally locked and the mutual orbit is circularised,
no further evolution is possible (modulo perturbations from the
4 small moons + the Sun). Earth-Luna is *en route* to this state
(Earth's rotation is currently spinning down via tidal recession
at +3.83 cm/yr per Williams 2014 LLR, cross-references v0.21.6);
Pluto-Charon has *arrived*. The Solar System provides exactly one
arrived-at-end-state example, and v0.24.11 catalogs it.

**(2) Small-moon near-3:4:5:6 commensurability** with the mutual
orbital period:
::

    P(Styx)     ≈ 3 × P_orb(P-C)  (3 × 6.387 = 19.16 d; observed 20.16 d)
    P(Nix)      ≈ 4 × P_orb(P-C)  (4 × 6.387 = 25.55 d; observed 24.85 d)
    P(Kerberos) ≈ 5 × P_orb(P-C)  (5 × 6.387 = 31.94 d; observed 32.17 d)
    P(Hydra)    ≈ 6 × P_orb(P-C)  (6 × 6.387 = 38.32 d; observed 38.20 d)

The four small moons orbit the *barycenter* (not Pluto), at
integer multiples of the Pluto-Charon orbital period — within
~0.3% to ~5% of perfect resonance, with Hydra and Kerberos closer
than Styx and Nix. **This is a mini-Galilean-Laplace-style
structure built on top of a mutual binary lock** — a structure
the Solar System exhibits precisely once. Showalter & Hamilton
2015 *Nature* analysed the stability and found the system is
chaotic in libration on Myr timescales.

**Cross-channel observation**: Styx-Nix-Kerberos-Hydra near-3:4:5:6
is structurally analogous to the **Galilean Laplace 4:2:1**
(v0.21.6 tidal-resonance catalog ships the Io-Europa-Ganymede
chain), but with a *binary* central body rather than a single
planet. Same algebraic discipline, more central-body structure.

**Not a re-derivation.** Values are the published high-precision
parameters from Brozovic et al. 2015 (post-New Horizons orbit
fit) + Stern et al. 2015 *Science* (New Horizons flyby summary)
+ Tholen-Buie 1990 (the original 1978 Charon-discovery
photographic-plate analysis; mutual-events 1985-1990) +
Showalter-Hamilton 2015 (small-moon dynamics).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Pluto-Charon mutual-orbit reference constants (Brozovic 2015) ---
PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS: float = 6.3872304
PLUTO_CHARON_SEMI_MAJOR_AXIS_KM: float = 19591.4
PLUTO_CHARON_ECCENTRICITY: float = 0.00005
PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG: float = 0.0006
PLUTO_HELIO_PLANE_INCLINATION_DEG: float = 119.59  # retrograde tilt

# ---- Mass-ratio + barycenter geometry (Brozovic 2015) ---------------
PLUTO_MASS_KG: float = 1.303e22
CHARON_MASS_KG: float = 1.586e21
CHARON_TO_PLUTO_MASS_RATIO: float = 0.1218
# Barycenter distance from Pluto's center (= a * M_C / (M_P + M_C))
PLUTO_BARYCENTER_OFFSET_KM: float = 2128.0
PLUTO_RADIUS_KM: float = 1188.3
CHARON_RADIUS_KM: float = 606.0
# The headline geometric fact: barycenter sits ABOVE Pluto's surface.
PLUTO_BARYCENTER_ABOVE_SURFACE_KM: float = (
    PLUTO_BARYCENTER_OFFSET_KM - PLUTO_RADIUS_KM
)  # ~940 km above Pluto's surface

# ---- Small-moon orbital periods (Brozovic 2015 / Showalter 2015) ----
STYX_ORBITAL_PERIOD_DAYS: float = 20.16155
NIX_ORBITAL_PERIOD_DAYS: float = 24.85463
KERBEROS_ORBITAL_PERIOD_DAYS: float = 32.16756
HYDRA_ORBITAL_PERIOD_DAYS: float = 38.20177


# ---------------------------------------------------------------------------
# Action-angle mode catalog
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DynamicalMode:
    """One frequency mode in Pluto-Charon's dynamical state.

    Mirrors the v0.24.0 Mercury / v0.24.1 Luna / v0.24.2 Mars
    catalog structure.
    """
    name: str
    frequency_per_century: float    # cycles/century
    period_days: float
    amplitude_value: float
    amplitude_units: str
    angle_or_action: str            # "angle" or "action"
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


_DAYS_PER_CENTURY: float = 36525.0
_TWO_PI: float = 6.283185307179586


PLUTO_CHARON_DYNAMICAL_MODES: List[DynamicalMode] = [

    # ==== Angle modes (TRIPLE-locked at 6.387 d) ====================

    DynamicalMode(
        name="mutual_orbital_sidereal",
        frequency_per_century=(
            _DAYS_PER_CENTURY / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
        ),
        period_days=PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
        amplitude_value=_TWO_PI,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Pluto-Charon binary orbital phase relative to fixed "
              "stars. The mutual orbital period 6.3872304 d is the "
              "fundamental clock of the whole system: BOTH spin "
              "frequencies are locked to it, and all four small "
              "moons (Styx/Nix/Kerberos/Hydra) sit at near-integer "
              "multiples of it.",
        source_key="brozovic_2015",
    ),

    DynamicalMode(
        name="pluto_spin_frequency",
        frequency_per_century=(
            _DAYS_PER_CENTURY / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
        ),
        period_days=PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
        amplitude_value=_TWO_PI,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Pluto's spin phase, locked 1:1 with the mutual "
              "orbital motion. Synchronous rotation; Pluto always "
              "shows the same face to Charon. Cross-references "
              "v0.23.0 spin_orbit_resonance.",
        source_key="brozovic_2015",
    ),

    DynamicalMode(
        name="charon_spin_frequency",
        frequency_per_century=(
            _DAYS_PER_CENTURY / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
        ),
        period_days=PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
        amplitude_value=_TWO_PI,
        amplitude_units="rad",
        angle_or_action="angle",
        notes="Charon's spin phase, ALSO locked 1:1 with the mutual "
              "orbital motion. THE HEADLINE: Pluto and Charon are "
              "BOTH tidally locked to each other simultaneously. "
              "This 'double-synchronous' state is the END state of "
              "dyadic tidal evolution; the Solar System provides "
              "exactly one example, and this is it.",
        source_key="stern_1992",
    ),

    # ==== Slow precession modes =====================================

    DynamicalMode(
        name="apsidal_precession_libration",
        frequency_per_century=_DAYS_PER_CENTURY / (3.2e6 * 365.25),
        period_days=3.2e6 * 365.25,
        amplitude_value=PLUTO_CHARON_ECCENTRICITY,
        amplitude_units="dimensionless",
        angle_or_action="angle",
        notes="Apsidal libration of the (already nearly-circular) "
              "mutual orbit. Showalter-Hamilton 2015 stability "
              "analysis of the small-moon system on ~3.2 Myr "
              "timescales. The eccentricity is so small (~5e-5) "
              "that the apsidal motion is largely a mathematical "
              "construct rather than a physically dominant mode.",
        source_key="showalter_hamilton_2015",
        precision_flag=PRECISION_LOW,
    ),

    # ==== Action modes (the slowly-varying parameters) ==============

    DynamicalMode(
        name="eccentricity_action",
        frequency_per_century=0.0,
        period_days=float("inf"),
        amplitude_value=PLUTO_CHARON_ECCENTRICITY,
        amplitude_units="dimensionless",
        angle_or_action="action",
        notes="Mutual orbital eccentricity ~5e-5 (Brozovic 2015) — "
              "approximately 1100x smaller than Luna's 0.0549. "
              "The tidal evolution of Pluto-Charon has gone to "
              "completion; mutual tidal dissipation has damped "
              "eccentricity to essentially zero. **The cleanest "
              "circular orbit in the Solar System.**",
        source_key="brozovic_2015",
    ),

    DynamicalMode(
        name="mutual_obliquity_action",
        frequency_per_century=0.0,
        period_days=float("inf"),
        amplitude_value=PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG,
        amplitude_units="deg",
        angle_or_action="action",
        notes="Mutual obliquity (spin-axis tilt to mutual orbit "
              "normal) ~0.0006° — essentially zero. Companion to "
              "the near-zero eccentricity: tidal evolution has "
              "aligned both spin axes with the mutual orbit normal.",
        source_key="stern_2015",
    ),

    DynamicalMode(
        name="charon_mass_ratio_action",
        frequency_per_century=0.0,
        period_days=float("inf"),
        amplitude_value=CHARON_TO_PLUTO_MASS_RATIO,
        amplitude_units="dimensionless",
        angle_or_action="action",
        notes="Mass ratio Charon/Pluto ≈ 0.1218 — the LARGEST "
              "binary mass ratio in the Solar System (Earth-Luna "
              "is 0.0123, ~10x smaller). The geometric consequence: "
              "the Pluto-Charon barycenter sits at ~2128 km from "
              "Pluto's center, **outside** Pluto's surface (radius "
              "1188 km), ~940 km above it. Pluto and Charon both "
              "orbit a point in empty space.",
        source_key="brozovic_2015",
    ),

    DynamicalMode(
        name="heliocentric_inclination_action",
        frequency_per_century=0.0,
        period_days=float("inf"),
        amplitude_value=PLUTO_HELIO_PLANE_INCLINATION_DEG,
        amplitude_units="deg",
        angle_or_action="action",
        notes="Inclination of the Pluto-Charon mutual orbit plane "
              "to Pluto's heliocentric orbital plane ~119.6° — a "
              "retrograde tilt. The whole binary system is tipped "
              "almost on its side relative to its orbit around the "
              "Sun.",
        source_key="stern_2015",
    ),

    # ==== Cross-channel: small-moon near-3:4:5:6 commensurabilities

    DynamicalMode(
        name="styx_near_3_to_1_with_pc_orbit",
        frequency_per_century=_DAYS_PER_CENTURY / STYX_ORBITAL_PERIOD_DAYS,
        period_days=STYX_ORBITAL_PERIOD_DAYS,
        amplitude_value=20.16155 / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
        amplitude_units="ratio",
        angle_or_action="angle",
        notes="Styx orbital period 20.162 d ÷ Pluto-Charon mutual "
              "period 6.387 d = 3.157 — close to but NOT exactly "
              "3:1 (5% off). Showalter-Hamilton 2015 finds the "
              "small-moon system is CHAOTIC on Myr libration "
              "timescales precisely because the resonances are not "
              "exact. Cross-channel: the proximity to small-integer "
              "ratios is exactly what the project's BIP cyclic-"
              "group encoder is built to detect.",
        source_key="showalter_2015_nature",
        precision_flag=PRECISION_MEDIUM,
    ),

    DynamicalMode(
        name="nix_near_4_to_1_with_pc_orbit",
        frequency_per_century=_DAYS_PER_CENTURY / NIX_ORBITAL_PERIOD_DAYS,
        period_days=NIX_ORBITAL_PERIOD_DAYS,
        amplitude_value=24.85463 / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
        amplitude_units="ratio",
        angle_or_action="angle",
        notes="Nix orbital period 24.855 d ÷ 6.387 d = 3.890 — "
              "close to 4:1 (3% off, lower side).",
        source_key="brozovic_2015",
    ),

    DynamicalMode(
        name="kerberos_near_5_to_1_with_pc_orbit",
        frequency_per_century=(
            _DAYS_PER_CENTURY / KERBEROS_ORBITAL_PERIOD_DAYS
        ),
        period_days=KERBEROS_ORBITAL_PERIOD_DAYS,
        amplitude_value=(
            32.16756 / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
        ),
        amplitude_units="ratio",
        angle_or_action="angle",
        notes="Kerberos orbital period 32.168 d ÷ 6.387 d = 5.038 "
              "— close to 5:1 (0.7% off; Kerberos discovered 2011 "
              "in HST imaging searches motivated by the New "
              "Horizons mission planning).",
        source_key="showalter_2015_nature",
    ),

    DynamicalMode(
        name="hydra_near_6_to_1_with_pc_orbit",
        frequency_per_century=(
            _DAYS_PER_CENTURY / HYDRA_ORBITAL_PERIOD_DAYS
        ),
        period_days=HYDRA_ORBITAL_PERIOD_DAYS,
        amplitude_value=(
            38.20177 / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
        ),
        amplitude_units="ratio",
        angle_or_action="angle",
        notes="Hydra orbital period 38.202 d ÷ 6.387 d = 5.981 — "
              "close to 6:1 (0.3% off — the closest of the four to "
              "perfect commensurability).",
        source_key="brozovic_2015",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "stern_1992": (
        "Stern S. A. (1992). The Pluto-Charon system. Annual Review "
        "of Astronomy and Astrophysics 30, 185-233. "
        "DOI: 10.1146/annurev.aa.30.090192.001153. The canonical "
        "pre-New-Horizons review of the binary's dynamical state + "
        "mutual tidal lock."
    ),
    "tholen_buie_1990": (
        "Tholen D. J. & Buie M. W. (1990). Further analysis of the "
        "Pluto-Charon mutual events: 1985-1990. The original "
        "photographic-plate analysis that confirmed the mutual "
        "tidal lock from the 1985-1990 mutual-occultation season "
        "(only one occurs every ~120 years, when Pluto-Charon's "
        "mutual orbit plane is edge-on from Earth)."
    ),
    "brozovic_2015": (
        "Brozovic M., Showalter M. R., Jacobson R. A., Buie M. W. "
        "(2015). The orbits and masses of satellites of Pluto. "
        "Icarus 246, 317-329. "
        "DOI: 10.1016/j.icarus.2014.03.015. **The post-New-Horizons "
        "definitive orbital fit** for Pluto-Charon + the four small "
        "moons. Source for mass ratio (0.1218), eccentricity "
        "(0.00005), all four small-moon periods + the near-"
        "commensurability ratios."
    ),
    "stern_2015": (
        "Stern S. A. et al. (2015). The Pluto system: Initial "
        "results from its exploration by New Horizons. Science 350, "
        "aad1815. DOI: 10.1126/science.aad1815. The canonical New "
        "Horizons flyby summary; source for radii, mutual obliquity, "
        "heliocentric inclination."
    ),
    "showalter_hamilton_2015": (
        "Showalter M. R. & Hamilton D. P. (2015). Resonant "
        "interactions and chaotic rotation of Pluto's small moons. "
        "Nature 522, 45-49. DOI: 10.1038/nature14469. **The chaos "
        "of the small-moon system**: near-3:4:5:6 with Pluto-Charon "
        "produces chaotic libration on Myr timescales — a v0.24.2-"
        "Mars-style spectral-stability failure mode applied to the "
        "binary's small-moon shepherd network."
    ),
    "showalter_2015_nature": (
        "Showalter M. R. et al. (2015). New satellite of (134340) "
        "Pluto: Kerberos. International Astronomical Union "
        "Circular 9221 (discovery announcement); + the Showalter-"
        "Hamilton 2015 *Nature* dynamics paper for orbital "
        "characterisation. Kerberos's 5:1 near-resonance is the "
        "closest of the four to integer."
    ),
    "weaver_2016": (
        "Weaver H. A. et al. (2016). The small satellites of Pluto "
        "as observed by New Horizons. Science 351, aae0030. "
        "DOI: 10.1126/science.aae0030. Direct New Horizons imaging "
        "of Styx, Nix, Kerberos, Hydra; size estimates that pin "
        "the small-moon physical properties used in the dynamical "
        "spectrum."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS",
    "PLUTO_CHARON_SEMI_MAJOR_AXIS_KM",
    "PLUTO_CHARON_ECCENTRICITY",
    "PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG",
    "PLUTO_HELIO_PLANE_INCLINATION_DEG",
    "PLUTO_MASS_KG",
    "CHARON_MASS_KG",
    "CHARON_TO_PLUTO_MASS_RATIO",
    "PLUTO_BARYCENTER_OFFSET_KM",
    "PLUTO_RADIUS_KM",
    "CHARON_RADIUS_KM",
    "PLUTO_BARYCENTER_ABOVE_SURFACE_KM",
    "STYX_ORBITAL_PERIOD_DAYS",
    "NIX_ORBITAL_PERIOD_DAYS",
    "KERBEROS_ORBITAL_PERIOD_DAYS",
    "HYDRA_ORBITAL_PERIOD_DAYS",
    "PLUTO_CHARON_DYNAMICAL_MODES",
    "SOURCES",
    "DynamicalMode",
]
