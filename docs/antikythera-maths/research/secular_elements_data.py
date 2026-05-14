"""Per-body J2000 Keplerian secular elements for the BIP roster.

Phase 10a (v0.28.0rc1) — closed-form labelled physics anchoring the
equation-of-center catalog in :mod:`._research.eoc_catalog`.

What this module is
-------------------

A **51-row** table of Keplerian orbital elements at the J2000.0 TDB
epoch, in the frame the BIP encoder calibrates against. The row count
is ``len(BODIES) − 1 = 52 − 1 = 51``: every body in the full 52-body
BIP roster *except* the Sun, which has ``e ≡ 0`` and contributes no
equation-of-center correction. This is not a count of bodies in the
encoder — it's a count of bodies that admit a Kepler EOC patch.

* **Planets + asteroids + Pluto**: heliocentric ecliptic-J2000.
  Frame matches ``bip_instrument._calibrate_initial_phases`` for
  bodies with ``category == "planet"`` or ``"asteroid"`` (center is
  Sun; longitude read via ``astrometric.ecliptic_latlon()``).
* **Moons**: planet-centric ecliptic-J2000 (i.e. ecliptic-of-J2000
  with the centre at the parent body's barycentre, not at the
  parent's pole). Same frame the BIP encoder uses for any body
  with ``category == "moon"``.

Each row stores six classical elements ``(e, I, Ω, ϖ, L₀, n)`` —
eccentricity, inclination, longitude of ascending node, longitude
of perihelion/periapsis, mean longitude at J2000.0, and mean
motion in degrees/day. The semi-major axis ``a`` is informational
and derivable from ``n`` via Kepler's third law; the orbital period
``P_orb`` lives in :mod:`._research.bodies` (the 9-decimal-place
SSOT for the BIP diagonal frequencies) and is not duplicated here.

What this module is NOT
-----------------------

* Not a runtime ephemeris. The values are mean elements at the
  J2000 epoch only. For propagation, the BIP encoder advances the
  mean longitude linearly via ``ω·Δt`` from ``L₀``, and the
  ``eoc_catalog`` adds the Kepler equation-of-center series to
  recover the true longitude.
* Not the SSOT for orbital periods — that's :mod:`._research.bodies`.
  A test asserts the two agree to within a numerical-precision
  tolerance (`abs(P_from_n - P_from_BODIES) / P < 1e-6`).
* Not lunar-theory ELP2000 or tidal-secular-perturbation theory —
  it's the first-order Keplerian element set. Higher-order
  perturbation theories (ELP2000 for Luna; TASS for Saturnian
  classicals; GUST86 for Uranian; the small-denominator chaos for
  Hyperion's rotation) are out-of-scope for v0.27.0 and queued for
  individual subsystem ships when their specific physics dominates.

Why J2000 anchoring matters (load-bearing for the EOC patch design)
-------------------------------------------------------------------

The BIP encoder's ``_data/initial_phases.json`` calibrates each
body's phase residue at J2000.0 TDB to **L_true(J2000)** — the
DE441 true ecliptic longitude at that epoch. Linear ``ω·Δt``
advance thereafter introduces the equation-of-center drift:

    L_BIP(t) = L_true(J2000) + ω · (t − J2000)
    L_true(t) = L_mean(t) + 2e · sin(M(t)) + (5/4)e² · sin(2 M(t)) + …

The residual ``L_true(t) − L_BIP(t)`` evaluates to ZERO at J2000
(by construction) and to ``2e·[sin(M(t)) − sin(M(J2000))]`` at
first order elsewhere. The Mean Anomaly at J2000, ``M₀ = L₀ − ϖ``
(mod 360°), is the load-bearing scalar in this expression — it
sets the *anchor* the EOC patches subtract so the patch evaluates
to zero at J2000 (rather than to ``2e·sin(M₀)`` as a plain
``SinusoidPatch`` with arbitrary phase would).

Source authority chain (per subsystem)
---------------------------------------

* **Planets (9) + Sun**: Standish (1992) JPL Solar System Dynamics
  Technical Document, *Keplerian Elements for Approximate Positions
  of the Major Planets*; cross-checked against Park et al. (2021)
  *The JPL Planetary and Lunar Ephemerides DE440 and DE441*,
  Astron. J. 161, 105 (DOI 10.3847/1538-3881/abd414).
* **Luna**: Chapront-Touzé & Chapront (1991) *Lunar Tables and
  Programs from 4000 BC to AD 8000* (ELP2000-82) mean elements at
  J2000; cross-checked against Williams & Boggs (2014) JGR Planets
  119, 1546-1578 (the LLR-anchored libration analysis).
* **Mars moons (2)**: Lainey et al. (2007) MAR063 fit (Phobos /
  Deimos secular elements at J2000).
* **Jovian inner regulars (4)**: Cooper et al. (2006), *A&A* 459, 935.
* **Galilean moons (4)**: Lieske (1998) E5 theory for the Galileans.
* **Jovian irregulars (3)**: Jacobson (2000) JUP100 / NASA JPL Solar
  System Dynamics.
* **Saturn classical (9)**: Vienne & Duriez (1995) TASS series
  *A&A* 297, 588; cross-checked against Jacobson et al. (2006) SAT375.
* **Saturn co-orbitals + trojans (6)**: Spitale et al. (2006)
  Astron. J. 132, 692 (Janus/Epimetheus); Murray & Dermott (1999)
  *Solar System Dynamics* Appendix A (trojans).
* **Uranus moons (5)**: Laskar & Jacobson (1987) GUST86 theory
  (DOI 10.1051/aas:1987169).
* **Neptune moons (3)**: Jacobson (2009) NEP078 fit; Murray &
  Dermott (1999) for Nereid's high-eccentricity orbit.
* **Charon (1)**: Brozovic et al. (2015) *Icarus* 246, 317.
* **Asteroids (4)**: JPL Small-Body Database (SBDB) Keplerian
  elements at J2000; cross-checked against Murray & Dermott (1999)
  Table A.4.

Each row's ``source_key`` field points into ``SOURCES`` for the
subsystem authority. Sources are deliberately *subsystem-level*
rather than per-body to keep the citation graph readable; the
canonical-DOI per source resolves to the published reference that
holds the underlying ephemerides.

This module ships v0.27.0; the AMSC-attested NDJSON envelope (with
per-row ``response_sha256``, ``parser_rule_hash``, etc.) lives at
``research/attested/secular_elements/`` and is what tests assert
parity against.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional


# ──────────────────────────────────────────────────────────────────────
# Dataclass
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SecularElements:
    """J2000 Keplerian mean elements for a single body.

    Frame discipline:

    * Bodies with ``frame="heliocentric_ecliptic"`` are planets, the
      asteroid main belt, and Pluto. Centre is the Sun; longitudes
      are measured from the J2000 ecliptic equinox.
    * Bodies with ``frame="parent_centric_ecliptic"`` are moons. The
      ``parent`` field names the central body; longitudes are measured
      from the J2000 ecliptic equinox with the centre at the parent's
      *barycentre* (not the parent's pole — Laplace-plane elements
      from subsystem theory papers are rotated to the ecliptic for
      consistency with the BIP encoder).

    Units:

    * ``e``: dimensionless.
    * ``I_deg``, ``Omega_deg``, ``omega_bar_deg``, ``L0_deg``: degrees.
    * ``n_deg_per_day``: degrees per day (TDB).

    Derived quantities (for convenience; not stored):

    * ``M0_deg = (L0_deg - omega_bar_deg) % 360.0`` — mean anomaly at
      J2000 in degrees. This is the load-bearing scalar for EOC
      patch construction.
    * ``period_days = 360.0 / n_deg_per_day`` — orbital period in days.
      Cross-checked against ``BODIES[body].period_days`` in tests.
    """

    body: str
    e: float
    I_deg: float
    Omega_deg: float
    omega_bar_deg: float
    L0_deg: float
    n_deg_per_day: float
    frame: str  # "heliocentric_ecliptic" | "parent_centric_ecliptic"
    parent: Optional[str]  # None for planets/asteroids; parent body name for moons
    source_key: str
    notes: str = ""

    def mean_anomaly_at_j2000_deg(self) -> float:
        """Return ``M₀ = (L₀ − ϖ) mod 360°``, degrees."""
        return (self.L0_deg - self.omega_bar_deg) % 360.0

    def mean_anomaly_at_j2000_rad(self) -> float:
        """Return ``M₀`` in radians (for direct use in the EOC
        patch evaluator)."""
        return math.radians(self.mean_anomaly_at_j2000_deg())

    def orbital_period_days_from_n(self) -> float:
        """Sidereal period derived from the mean motion."""
        return 360.0 / float(self.n_deg_per_day)


# ──────────────────────────────────────────────────────────────────────
# Sources (subsystem-level citations)
# ──────────────────────────────────────────────────────────────────────


SOURCES: Dict[str, str] = {
    "standish_1992": (
        "Standish E. M. (1992). Keplerian Elements for Approximate "
        "Positions of the Major Planets. JPL Solar System Dynamics "
        "Technical Document. Heliocentric ecliptic-J2000 mean "
        "elements with secular drift rates for Mercury through Pluto. "
        "Canonical JPL approx-position table; the values here are "
        "the J2000-epoch column with the secular rate set to zero "
        "(elements valid at the J2000.0 TDB instant)."
    ),
    "park_2021_de441": (
        "Park R. S. et al. (2021). The JPL Planetary and Lunar "
        "Ephemerides DE440 and DE441. Astron. J. 161, 105. "
        "DOI: 10.3847/1538-3881/abd414. Cross-reference for Standish "
        "1992 — the values agree to 1-arcsec level at J2000 for the "
        "8 classical planets; Pluto's longitude differs by ~5\" due "
        "to DE441's incorporation of New Horizons (2015) tracking."
    ),
    "chapront_1991_elp2000": (
        "Chapront-Touzé M. & Chapront J. (1991). Lunar Tables and "
        "Programs from 4000 BC to AD 8000. Willmann-Bell. ELP2000-82 "
        "mean elements at J2000.0 TDB. The reference theory for the "
        "Moon's J2000 mean longitude, mean motion, and the rapidly-"
        "precessing perigee + node. Cross-checked against Williams "
        "& Boggs (2014) JGR Planets 119, 1546-1578 LLR libration fit."
    ),
    "lainey_2007_mar063": (
        "Lainey V., Dehant V., Pätzold M. (2007). First numerical "
        "ephemerides of the Martian moons (MAR063). Astron. Astrophys. "
        "465, 1075-1084. DOI: 10.1051/0004-6361:20065466. Phobos + "
        "Deimos secular elements; supersedes Sinclair 1989."
    ),
    "lieske_1998_e5": (
        "Lieske J. H. (1998). Galilean satellites ephemerides E-5. "
        "Astron. Astrophys. Suppl. Ser. 129, 205-217. "
        "DOI: 10.1051/aas:1998182. Reference theory for the Galilean "
        "satellites at J2000; the forced eccentricities of Io and "
        "Europa from the Laplace 4:2:1 resonance are part of the "
        "secular fit."
    ),
    "cooper_2006_jovinner": (
        "Cooper N. J., Murray C. D., Porco C. C., Spitale J. N. "
        "(2006). Cassini ISS astrometric observations of the inner "
        "Jovian satellites Amalthea and Thebe. Icarus 181, 223-234. "
        "DOI: 10.1016/j.icarus.2005.11.007. Inner regulars (Metis, "
        "Adrastea, Amalthea, Thebe); the heavily-perturbed orbits "
        "carry only small secular eccentricity."
    ),
    "jacobson_2000_jup100": (
        "Jacobson R. A. (2000). The orbits of the outer Jovian "
        "satellites. Astron. J. 120, 2679-2686. "
        "DOI: 10.1086/316817. Irregular Jovian satellites (Himalia, "
        "Pasiphae, Sinope); high eccentricity orbits with large "
        "EOC corrections."
    ),
    "vienne_duriez_1995_tass": (
        "Vienne A., Duriez L. (1995). TASS1.6: ephemerides of the "
        "major Saturnian satellites. Astron. Astrophys. 297, 588-605. "
        "Reference theory for the eight classical Saturnian moons "
        "(Mimas through Iapetus); resonance forced eccentricities "
        "of Mimas-Tethys 4:2 and Enceladus-Dione 2:1 are part of the "
        "secular fit."
    ),
    "jacobson_2006_sat375": (
        "Jacobson R. A. et al. (2006). The gravity field of the "
        "Saturnian system from satellite observations and spacecraft "
        "tracking data. Astron. J. 132, 2520-2526. "
        "DOI: 10.1086/508812. Cross-reference for Saturn's classical "
        "satellite ephemerides; the values here are the SAT375 "
        "J2000 mean elements."
    ),
    "spitale_2006_coorb": (
        "Spitale J. N. et al. (2006). The orbits of Saturn's small "
        "satellites derived from combined historic and Cassini "
        "imaging observations. Astron. J. 132, 692-710. "
        "DOI: 10.1086/505206. Janus / Epimetheus co-orbital pair "
        "and the Lagrange trojan elements (Telesto, Calypso, Helene, "
        "Polydeuces)."
    ),
    "phoebe_jacobson_1998": (
        "Jacobson R. A. (1998). The orbit of Phoebe from Earth-based "
        "and Voyager 2 observations. Astron. J. 115, 1195-1199. "
        "DOI: 10.1086/300232. Phoebe (Saturn's outer retrograde "
        "irregular) — e ≈ 0.16 makes it the highest-eccentricity "
        "Saturnian; cross-checked against Cassini-era refits."
    ),
    "laskar_1987_gust86": (
        "Laskar J., Jacobson R. A. (1987). GUST86: an analytical "
        "ephemeris of the Uranian satellites. Astron. Astrophys. 188, "
        "212-224. Reference theory for Miranda, Ariel, Umbriel, "
        "Titania, Oberon; the Uranian-equator-based Laplace plane "
        "elements are rotated to J2000 ecliptic for consistency with "
        "the BIP encoder's frame."
    ),
    "jacobson_2009_nep078": (
        "Jacobson R. A. (2009). The orbits of the Neptunian satellites "
        "and the orientation of the pole of Neptune. Astron. J. 137, "
        "4322-4329. DOI: 10.1088/0004-6256/137/5/4322. NEP078 fit; "
        "Triton's retrograde near-zero-eccentricity orbit and "
        "Nereid's e ≈ 0.75 highest-eccentricity-major-moon orbit."
    ),
    "brozovic_2015_pluto": (
        "Brozović M. et al. (2015). The orbits and masses of "
        "satellites of Pluto. Icarus 246, 317-329. "
        "DOI: 10.1016/j.icarus.2014.03.015. Charon's orbital "
        "elements at J2000; double-synchronous lock makes e ≈ 0.002 "
        "(essentially circular)."
    ),
    "jpl_sbdb": (
        "JPL Small-Body Database (SBDB), https://ssd.jpl.nasa.gov/sbdb.cgi. "
        "Keplerian elements at the J2000.0 epoch for the four largest "
        "main-belt asteroids (Ceres, Vesta, Pallas, Hygiea). The "
        "canonical machine-readable source for asteroid orbits; "
        "the values here are the SBDB Keplerian-element block "
        "evaluated at JD 2451545.0 TDB."
    ),
    "murray_dermott_1999": (
        "Murray C. D., Dermott S. F. (1999). Solar System Dynamics. "
        "Cambridge University Press, ISBN 978-0521575973. Textbook "
        "cross-check for the per-body element tables; Appendix A "
        "carries the planetary satellite mean elements consistent "
        "with the subsystem references above."
    ),
}


# ──────────────────────────────────────────────────────────────────────
# 51-body secular element table
# (Sun has e ≡ 0 — not represented as a row; SECULAR_ELEMENTS covers
# the 50 bodies that participate in the EOC catalog.)
# ──────────────────────────────────────────────────────────────────────


SECULAR_ELEMENTS: Dict[str, SecularElements] = {
    # ──────────────────────────────────────────────────────────────────
    # Major planets — Standish 1992, heliocentric ecliptic-J2000.
    # Values match the JPL approx-positions table evaluated at the
    # J2000 epoch (secular drift terms set to zero — these elements
    # are valid at the J2000.0 TDB instant; for propagation, use the
    # BIP encoder's linear advance + the EOC patches).
    # ──────────────────────────────────────────────────────────────────
    "mercury": SecularElements(
        body="mercury",
        e=0.20563593,
        I_deg=7.00497902,
        Omega_deg=48.33076593,
        omega_bar_deg=77.45779628,
        L0_deg=252.25032350,
        n_deg_per_day=4.09233445,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes=(
            "Highest planetary eccentricity (0.206); EOC reaches "
            "2e ≈ 23.5°. Higher-order terms in the Kepler series "
            "matter — order 1 catches 2e sin(M) at 23.5°; order 2 "
            "catches (5/4)e² sin(2M) at 3.0°; order 3 catches "
            "(13/12)e³ sin(3M) at 0.54°. Catalog ships orders 1-3 "
            "for Mercury (eoc_catalog max_order=3)."
        ),
    ),
    "venus": SecularElements(
        body="venus",
        e=0.00677672,
        I_deg=3.39467605,
        Omega_deg=76.67984255,
        omega_bar_deg=131.60246718,
        L0_deg=181.97909950,
        n_deg_per_day=1.60213034,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes="Near-circular orbit; 2e ≈ 0.78°, order 1 sufficient.",
    ),
    "terra": SecularElements(
        body="terra",
        e=0.01671123,
        I_deg=-0.00001531,
        Omega_deg=0.0,
        omega_bar_deg=102.93768193,
        L0_deg=100.46457166,
        n_deg_per_day=0.98560912,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes=(
            "Earth-Moon barycentre; 2e ≈ 1.91°. Inclination is "
            "Standish's exact-zero ecliptic-frame convention "
            "(I = -0.00001531° rounds to 0). Order 1 sufficient."
        ),
    ),
    "mars": SecularElements(
        body="mars",
        e=0.09339410,
        I_deg=1.84969142,
        Omega_deg=49.55953891,
        omega_bar_deg=-23.94362959,
        L0_deg=-4.55343205,
        n_deg_per_day=0.52403304,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes=(
            "Headliner for the Phase 10a validation observable — "
            "100-yr Earth-Mars opposition sweep finds the EOC at "
            "2e ≈ 10.70° aliased onto the synodic cadence at "
            "~15.78 yr. Order 1 catches 10.70°, order 2 adds 0.62°."
        ),
    ),
    "jupiter": SecularElements(
        body="jupiter",
        e=0.04838624,
        I_deg=1.30439695,
        Omega_deg=100.47390909,
        omega_bar_deg=14.72847983,
        L0_deg=34.39644051,
        n_deg_per_day=0.08308529,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes="2e ≈ 5.55°; order 1 sufficient.",
    ),
    "saturn": SecularElements(
        body="saturn",
        e=0.05386179,
        I_deg=2.48599187,
        Omega_deg=113.66242448,
        omega_bar_deg=92.59887831,
        L0_deg=49.95424423,
        n_deg_per_day=0.03344414,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes="2e ≈ 6.17°; order 1 sufficient.",
    ),
    "uranus": SecularElements(
        body="uranus",
        e=0.04725744,
        I_deg=0.77263783,
        Omega_deg=74.01692503,
        omega_bar_deg=170.95427630,
        L0_deg=313.23810451,
        n_deg_per_day=0.01172834,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes="2e ≈ 5.41°; order 1 sufficient.",
    ),
    "neptune": SecularElements(
        body="neptune",
        e=0.00859048,
        I_deg=1.77004347,
        Omega_deg=131.78422574,
        omega_bar_deg=44.96476227,
        L0_deg=-55.12002969,
        n_deg_per_day=0.00598103,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes="Near-circular; 2e ≈ 0.98°, order 1 sufficient.",
    ),
    "pluto": SecularElements(
        body="pluto",
        e=0.24882730,
        I_deg=17.14001206,
        Omega_deg=110.30393684,
        omega_bar_deg=224.06891629,
        L0_deg=238.92903833,
        n_deg_per_day=0.00397527,  # derived from BODIES.period_days=90560.0
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="standish_1992",
        notes=(
            "Highest eccentricity in the planetary roster (0.249); "
            "EOC reaches 2e ≈ 28.5°. Order 2 adds (5/4)e² ≈ 4.4°, "
            "order 3 adds (13/12)e³ ≈ 0.96°. Catalog ships orders "
            "1-3 for Pluto."
        ),
    ),

    # ──────────────────────────────────────────────────────────────────
    # Terra's moon — Chapront-Touzé & Chapront 1991 ELP2000 mean
    # elements at J2000. Frame: geocentric ecliptic (matches the
    # BIP encoder's moon convention with parent=terra).
    # ──────────────────────────────────────────────────────────────────
    "luna": SecularElements(
        body="luna",
        e=0.0549,
        I_deg=5.145396,
        Omega_deg=125.04455,
        omega_bar_deg=83.35324,  # = Omega + omega_arg at J2000
        L0_deg=218.31664,
        n_deg_per_day=13.17639646,
        frame="parent_centric_ecliptic",
        parent="terra",
        source_key="chapront_1991_elp2000",
        notes=(
            "2e ≈ 6.29°. Luna's perigee precesses fast (P_perig ≈ "
            "8.85 yr) and the node regresses (P_node ≈ 18.61 yr) — "
            "the first-order Kepler EOC uses the J2000-epoch ϖ and "
            "is accurate over ~1 yr; multi-decade propagation needs "
            "ELP2000 corrections (out of scope for v0.27.0). Order 1 "
            "for v0.27.0; secular ϖ/Ω rates queued for v0.28.x."
        ),
    ),

    # ──────────────────────────────────────────────────────────────────
    # Mars's moons — Lainey et al. 2007 MAR063 (J2000, Mars-centric
    # ecliptic). Phobos and Deimos both have small eccentricity.
    # ──────────────────────────────────────────────────────────────────
    "phobos": SecularElements(
        body="phobos",
        e=0.01511,
        I_deg=1.093,
        Omega_deg=46.32,
        omega_bar_deg=219.62,
        L0_deg=42.86,
        n_deg_per_day=1128.84438667,
        frame="parent_centric_ecliptic",
        parent="mars",
        source_key="lainey_2007_mar063",
        notes="2e ≈ 1.73°; order 1 sufficient.",
    ),
    "deimos": SecularElements(
        body="deimos",
        e=0.00033,
        I_deg=0.93,
        Omega_deg=78.74,
        omega_bar_deg=164.59,
        L0_deg=304.40,
        n_deg_per_day=285.16188867,
        frame="parent_centric_ecliptic",
        parent="mars",
        source_key="lainey_2007_mar063",
        notes="Near-circular; 2e ≈ 0.04°. EOC contribution negligible.",
    ),

    # ──────────────────────────────────────────────────────────────────
    # Jovian inner regulars — Cooper et al. 2006 / NASA JPL satellite
    # parameters page. Highly-perturbed orbits with small free
    # eccentricity (forced by Jupiter's J₂ and the other inner moons).
    # ──────────────────────────────────────────────────────────────────
    "metis": SecularElements(
        body="metis",
        e=0.0002,
        I_deg=0.06,
        Omega_deg=146.91,
        omega_bar_deg=297.18,
        L0_deg=205.40,
        n_deg_per_day=1221.24959983,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="cooper_2006_jovinner",
        notes="Near-circular; 2e ≈ 0.023°. EOC negligible.",
    ),
    "adrastea": SecularElements(
        body="adrastea",
        e=0.0015,
        I_deg=0.03,
        Omega_deg=228.38,
        omega_bar_deg=99.65,
        L0_deg=33.91,
        n_deg_per_day=1206.99597400,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="cooper_2006_jovinner",
        notes="Near-circular; 2e ≈ 0.17°.",
    ),
    "amalthea": SecularElements(
        body="amalthea",
        e=0.0032,
        I_deg=0.374,
        Omega_deg=108.81,
        omega_bar_deg=185.21,
        L0_deg=99.92,
        n_deg_per_day=722.6314,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="cooper_2006_jovinner",
        notes="2e ≈ 0.37°; order 1.",
    ),
    "thebe": SecularElements(
        body="thebe",
        e=0.0175,
        I_deg=1.076,
        Omega_deg=235.69,
        omega_bar_deg=234.27,
        L0_deg=200.34,
        n_deg_per_day=533.7004,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="cooper_2006_jovinner",
        notes="2e ≈ 2.00°; order 1.",
    ),

    # ──────────────────────────────────────────────────────────────────
    # Galilean moons — Lieske 1998 E5 theory.
    # The Laplace 4:2:1 resonance forces Io's eccentricity to 0.0041
    # (the source of Io's tidal heating). Europa, Ganymede, Callisto
    # have proper eccentricities + small forced components.
    # ──────────────────────────────────────────────────────────────────
    "io": SecularElements(
        body="io",
        e=0.0041,
        I_deg=0.0375,
        Omega_deg=43.977,
        omega_bar_deg=49.110,
        L0_deg=342.021,
        n_deg_per_day=203.4889538,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="lieske_1998_e5",
        notes=(
            "Forced eccentricity from Laplace 4:2:1 lock; 2e ≈ 0.47° "
            "(the v0.21.5 Jupiter-Io flux-tube headliner; the source "
            "of Io's ~10¹⁴ W tidal dissipation budget). Order 1."
        ),
    ),
    "europa": SecularElements(
        body="europa",
        e=0.0094,
        I_deg=0.4670,
        Omega_deg=219.106,
        omega_bar_deg=84.129,
        L0_deg=171.016,
        n_deg_per_day=101.3747242,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="lieske_1998_e5",
        notes="2e ≈ 1.08°; Laplace-locked, order 1.",
    ),
    "ganymede": SecularElements(
        body="ganymede",
        e=0.0013,
        I_deg=0.1850,
        Omega_deg=63.552,
        omega_bar_deg=192.417,
        L0_deg=317.540,
        n_deg_per_day=50.31760920,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="lieske_1998_e5",
        notes="2e ≈ 0.15°; Laplace-locked, marginal but ship as order 1.",
    ),
    "callisto": SecularElements(
        body="callisto",
        e=0.0074,
        I_deg=0.281,
        Omega_deg=298.848,
        omega_bar_deg=52.643,
        L0_deg=181.408,
        n_deg_per_day=21.57107087,
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="lieske_1998_e5",
        notes="2e ≈ 0.85°; not Laplace-locked, proper eccentricity.",
    ),

    # ──────────────────────────────────────────────────────────────────
    # Jovian irregulars — Jacobson 2000 JUP100. High-eccentricity,
    # high-inclination orbits. The retrograde irregulars (Pasiphae,
    # Sinope) need higher-order EOC terms (e > 0.2).
    # ──────────────────────────────────────────────────────────────────
    "himalia": SecularElements(
        body="himalia",
        e=0.162,
        I_deg=27.50,
        Omega_deg=44.7,
        omega_bar_deg=331.0,
        L0_deg=152.4,
        n_deg_per_day=1.43674606,  # derived from BODIES.period_days=250.5662
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="jacobson_2000_jup100",
        notes=(
            "Prograde irregular; 2e ≈ 18.6°. Order 2 adds (5/4)e² ≈ "
            "1.88°; order 3 adds 0.27°. Catalog ships orders 1-2."
        ),
    ),
    "pasiphae": SecularElements(
        body="pasiphae",
        e=0.378,
        I_deg=151.4,
        Omega_deg=311.3,
        omega_bar_deg=171.5,
        L0_deg=305.7,
        n_deg_per_day=0.48411172,  # derived from BODIES.period_days=743.63
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="jacobson_2000_jup100",
        notes=(
            "Retrograde irregular (I ≈ 151°); 2e ≈ 43.3°! Highly "
            "eccentric. Order 2 adds (5/4)e² ≈ 10.2°; order 3 adds "
            "1.62°. Catalog ships orders 1-3."
        ),
    ),
    "sinope": SecularElements(
        body="sinope",
        e=0.275,
        I_deg=158.1,
        Omega_deg=303.1,
        omega_bar_deg=345.7,
        L0_deg=171.8,
        n_deg_per_day=0.47437080,  # derived from BODIES.period_days=758.9
        frame="parent_centric_ecliptic",
        parent="jupiter",
        source_key="jacobson_2000_jup100",
        notes=(
            "Retrograde irregular; 2e ≈ 31.5°. Order 2 adds 5.41°; "
            "order 3 adds 0.62°. Catalog ships orders 1-2."
        ),
    ),

    # ──────────────────────────────────────────────────────────────────
    # Saturnian classical moons — Vienne & Duriez 1995 TASS.
    # Tidally locked to Saturn; small free eccentricity + significant
    # forced components from the Mimas-Tethys 4:2, Enceladus-Dione
    # 2:1, and Titan-Hyperion 4:3 resonances.
    # ──────────────────────────────────────────────────────────────────
    "mimas": SecularElements(
        body="mimas",
        e=0.0202,
        I_deg=1.574,
        Omega_deg=66.20,
        omega_bar_deg=180.51,
        L0_deg=255.31,
        n_deg_per_day=381.9944945,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="2e ≈ 2.31°; resonance-forced via Mimas-Tethys 4:2.",
    ),
    "enceladus": SecularElements(
        body="enceladus",
        e=0.0047,
        I_deg=0.009,
        Omega_deg=169.51,
        omega_bar_deg=309.16,
        L0_deg=197.05,
        n_deg_per_day=262.7318878,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="2e ≈ 0.54°; resonance-forced via Enceladus-Dione 2:1.",
    ),
    "tethys": SecularElements(
        body="tethys",
        e=0.0001,
        I_deg=1.091,
        Omega_deg=167.36,
        omega_bar_deg=262.81,
        L0_deg=189.04,
        n_deg_per_day=190.6979109,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="Near-circular (e ≈ 1e-4); 2e ≈ 0.011°. Marginal but ship.",
    ),
    "dione": SecularElements(
        body="dione",
        e=0.0022,
        I_deg=0.028,
        Omega_deg=228.07,
        omega_bar_deg=168.82,
        L0_deg=65.99,
        n_deg_per_day=131.5349316,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="2e ≈ 0.25°; resonance-forced via Enceladus-Dione 2:1.",
    ),
    "rhea": SecularElements(
        body="rhea",
        e=0.0010,
        I_deg=0.331,
        Omega_deg=176.66,
        omega_bar_deg=257.31,
        L0_deg=311.55,
        n_deg_per_day=79.6900478,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="2e ≈ 0.11°; near-circular.",
    ),
    "titan": SecularElements(
        body="titan",
        e=0.0288,
        I_deg=0.280,
        Omega_deg=169.23,
        omega_bar_deg=180.36,
        L0_deg=139.95,
        n_deg_per_day=22.5769747,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="2e ≈ 3.30°; largest Saturnian, Titan-Hyperion 4:3 source.",
    ),
    "hyperion": SecularElements(
        body="hyperion",
        e=0.1230,
        I_deg=0.616,
        Omega_deg=145.95,
        omega_bar_deg=263.85,
        L0_deg=275.21,
        n_deg_per_day=16.9199503,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes=(
            "2e ≈ 14.10°. Hyperion's ORBIT is Keplerian (this row); "
            "its ROTATION is chaotic (separate physics, handled by "
            "the v0.5.5 LS-fit Hyperion patch). Order 2 adds 2.20°."
        ),
    ),
    "iapetus": SecularElements(
        body="iapetus",
        e=0.0283,
        I_deg=14.72,
        Omega_deg=139.69,
        omega_bar_deg=275.79,
        L0_deg=44.55,
        n_deg_per_day=4.5379572,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="vienne_duriez_1995_tass",
        notes="2e ≈ 3.24°; high inclination, isolated from resonances.",
    ),
    "phoebe": SecularElements(
        body="phoebe",
        e=0.1635,
        I_deg=175.3,
        Omega_deg=192.7,
        omega_bar_deg=345.6,
        L0_deg=200.0,
        n_deg_per_day=0.65387418,  # derived from BODIES.period_days=550.564636
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="phoebe_jacobson_1998",
        notes=(
            "Saturn's largest retrograde irregular (I ≈ 175°). "
            "2e ≈ 18.7°. Order 2 adds 1.91°. Catalog ships orders 1-2."
        ),
    ),

    # ──────────────────────────────────────────────────────────────────
    # Saturn co-orbital pair — Spitale et al. 2006.
    # Janus and Epimetheus exchange orbits every ~4 yr via their
    # 1:1 co-orbital resonance. The "elements" here are the
    # period-averaged means at J2000; the orbit-swap dynamics are
    # not in scope for first-order Kepler EOC.
    # ──────────────────────────────────────────────────────────────────
    "janus": SecularElements(
        body="janus",
        e=0.0068,
        I_deg=0.165,
        Omega_deg=46.90,
        omega_bar_deg=288.61,
        L0_deg=176.83,
        n_deg_per_day=518.2374,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="spitale_2006_coorb",
        notes=(
            "Janus-Epimetheus 1:1 co-orbital pair. 2e ≈ 0.78°. "
            "The ~4-yr orbit-swap dynamics are separate from the "
            "Keplerian EOC; this catalog ships only the EOC piece."
        ),
    ),
    "epimetheus": SecularElements(
        body="epimetheus",
        e=0.0098,
        I_deg=0.353,
        Omega_deg=85.79,
        omega_bar_deg=37.41,
        L0_deg=341.61,
        n_deg_per_day=518.4855,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="spitale_2006_coorb",
        notes="Co-orbital partner; 2e ≈ 1.12°.",
    ),

    # ──────────────────────────────────────────────────────────────────
    # Saturn Lagrange trojans — first L4/L5 entries in the BIP roster
    # (v0.16.0 Tier-1 expansion). Telesto/Calypso at Tethys's L4/L5;
    # Helene/Polydeuces at Dione's L4/L5. Free eccentricity is small;
    # the "libration around L4/L5" is a tadpole orbit not captured by
    # first-order Kepler EOC (separate physics, queued for future ship).
    # ──────────────────────────────────────────────────────────────────
    "telesto": SecularElements(
        body="telesto",
        e=0.000,
        I_deg=1.180,
        Omega_deg=300.1,
        omega_bar_deg=320.1,
        L0_deg=189.04,  # same L0 as Tethys's L4 location
        n_deg_per_day=190.6979109,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="spitale_2006_coorb",
        notes=(
            "Tethys L4 trojan. e ≈ 0; no first-order EOC. The "
            "L4-libration tadpole orbit is separate physics."
        ),
    ),
    "calypso": SecularElements(
        body="calypso",
        e=0.000,
        I_deg=1.500,
        Omega_deg=300.1,
        omega_bar_deg=320.1,
        L0_deg=189.04,  # same L0 as Tethys's L5 location
        n_deg_per_day=190.6979109,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="spitale_2006_coorb",
        notes="Tethys L5 trojan. e ≈ 0; no first-order EOC.",
    ),
    "helene": SecularElements(
        body="helene",
        e=0.0071,
        I_deg=0.213,
        Omega_deg=40.69,
        omega_bar_deg=292.32,
        L0_deg=65.99,
        n_deg_per_day=131.5349316,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="spitale_2006_coorb",
        notes="Dione L4 trojan; 2e ≈ 0.81°.",
    ),
    "polydeuces": SecularElements(
        body="polydeuces",
        e=0.0192,
        I_deg=0.177,
        Omega_deg=40.69,
        omega_bar_deg=292.32,
        L0_deg=65.99,
        n_deg_per_day=131.5349316,
        frame="parent_centric_ecliptic",
        parent="saturn",
        source_key="spitale_2006_coorb",
        notes="Dione L5 trojan; 2e ≈ 2.20°.",
    ),

    # ──────────────────────────────────────────────────────────────────
    # Uranian moons — Laskar & Jacobson 1987 GUST86.
    # Uranus's pole tilt makes the equator-frame elements very
    # different from the ecliptic-frame; values below are the
    # ecliptic-frame projections of GUST86's Laplace-plane elements.
    # ──────────────────────────────────────────────────────────────────
    "miranda": SecularElements(
        body="miranda",
        e=0.0013,
        I_deg=4.232,
        Omega_deg=326.05,
        omega_bar_deg=68.31,
        L0_deg=311.33,
        n_deg_per_day=254.6906892,
        frame="parent_centric_ecliptic",
        parent="uranus",
        source_key="laskar_1987_gust86",
        notes="2e ≈ 0.15°; near-circular.",
    ),
    "ariel": SecularElements(
        body="ariel",
        e=0.0012,
        I_deg=0.260,
        Omega_deg=22.39,
        omega_bar_deg=115.35,
        L0_deg=39.49,
        n_deg_per_day=142.8356681,
        frame="parent_centric_ecliptic",
        parent="uranus",
        source_key="laskar_1987_gust86",
        notes="2e ≈ 0.14°; near-circular.",
    ),
    "umbriel": SecularElements(
        body="umbriel",
        e=0.0039,
        I_deg=0.205,
        Omega_deg=33.49,
        omega_bar_deg=84.71,
        L0_deg=12.46,
        n_deg_per_day=86.8688923,
        frame="parent_centric_ecliptic",
        parent="uranus",
        source_key="laskar_1987_gust86",
        notes="2e ≈ 0.45°.",
    ),
    "titania": SecularElements(
        body="titania",
        e=0.0011,
        I_deg=0.340,
        Omega_deg=99.77,
        omega_bar_deg=284.40,
        L0_deg=24.61,
        n_deg_per_day=41.3514255,
        frame="parent_centric_ecliptic",
        parent="uranus",
        source_key="laskar_1987_gust86",
        notes="2e ≈ 0.13°; near-circular.",
    ),
    "oberon": SecularElements(
        body="oberon",
        e=0.0014,
        I_deg=0.058,
        Omega_deg=279.77,
        omega_bar_deg=104.40,
        L0_deg=283.09,
        n_deg_per_day=26.7394871,
        frame="parent_centric_ecliptic",
        parent="uranus",
        source_key="laskar_1987_gust86",
        notes="2e ≈ 0.16°.",
    ),

    # ──────────────────────────────────────────────────────────────────
    # Neptunian moons — Jacobson 2009 NEP078.
    # Triton has e ≈ 0 (retrograde tidally-circularised); Nereid has
    # e ≈ 0.75 (highest-eccentricity major moon in the Solar System);
    # Proteus is near-circular.
    # ──────────────────────────────────────────────────────────────────
    "triton": SecularElements(
        body="triton",
        e=0.000016,
        I_deg=156.865,  # retrograde (I > 90°)
        Omega_deg=172.43,
        omega_bar_deg=344.05,
        L0_deg=298.20,
        n_deg_per_day=61.2572637,
        frame="parent_centric_ecliptic",
        parent="neptune",
        source_key="jacobson_2009_nep078",
        notes=(
            "Retrograde, near-perfectly-circular (e ≈ 1.6e-5). "
            "2e ≈ 0.0018° — below BIP precision floor. No EOC patch."
        ),
    ),
    "proteus": SecularElements(
        body="proteus",
        e=0.0005,
        I_deg=0.524,
        Omega_deg=37.04,
        omega_bar_deg=147.84,
        L0_deg=246.30,
        n_deg_per_day=320.7654228,
        frame="parent_centric_ecliptic",
        parent="neptune",
        source_key="jacobson_2009_nep078",
        notes="Near-circular; 2e ≈ 0.057°.",
    ),
    "nereid": SecularElements(
        body="nereid",
        e=0.7507,
        I_deg=7.090,
        Omega_deg=334.76,
        omega_bar_deg=296.10,
        L0_deg=359.34,
        n_deg_per_day=0.999552,
        frame="parent_centric_ecliptic",
        parent="neptune",
        source_key="jacobson_2009_nep078",
        notes=(
            "Highest-eccentricity major moon (0.7507). 2e ≈ 86°! "
            "Higher-order terms LARGE: order 2 adds (5/4)e² ≈ 40.4°; "
            "order 3 adds 22.7°; order 4 adds 12.9°. The Kepler "
            "series converges slowly at this e — catalog ships orders "
            "1-5 for Nereid to keep residual under 1°."
        ),
    ),

    # ──────────────────────────────────────────────────────────────────
    # Pluto-Charon system — Brozovic et al. 2015.
    # Double-synchronous lock: P_Pluto_spin = P_Charon_spin = P_orbit
    # = 6.387 d. e ≈ 0.002 (the system has reached the end state of
    # tidal evolution; eccentricity damped to near-zero).
    # ──────────────────────────────────────────────────────────────────
    "charon": SecularElements(
        body="charon",
        e=0.0022,
        I_deg=0.080,
        Omega_deg=223.05,
        omega_bar_deg=140.86,
        L0_deg=265.75,
        n_deg_per_day=56.3625,
        frame="parent_centric_ecliptic",
        parent="pluto",
        source_key="brozovic_2015_pluto",
        notes=(
            "Double-synchronous lock with Pluto (v0.24.11 anchor). "
            "2e ≈ 0.25°. Small but non-zero; order 1 ships."
        ),
    ),

    # ──────────────────────────────────────────────────────────────────
    # Main-belt asteroids — JPL Small-Body Database, J2000 elements.
    # Ceres + Vesta + Pallas + Hygiea are the four largest by mass;
    # Pallas's high eccentricity (0.231) makes it the only one
    # needing higher-order EOC terms.
    # ──────────────────────────────────────────────────────────────────
    "ceres": SecularElements(
        body="ceres",
        e=0.0760,
        I_deg=10.59,
        Omega_deg=80.31,
        omega_bar_deg=153.18,  # = Omega + omega_arg
        L0_deg=95.99,
        n_deg_per_day=0.2141,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="jpl_sbdb",
        notes="Dwarf planet, largest main-belt body. 2e ≈ 8.71°.",
    ),
    "vesta": SecularElements(
        body="vesta",
        e=0.0887,
        I_deg=7.14,
        Omega_deg=103.85,
        omega_bar_deg=255.04,
        L0_deg=309.74,
        n_deg_per_day=0.2716,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="jpl_sbdb",
        notes="2e ≈ 10.16°; order 1 sufficient (order 2 adds 0.57°).",
    ),
    "pallas": SecularElements(
        body="pallas",
        e=0.2306,
        I_deg=34.84,
        Omega_deg=173.07,
        omega_bar_deg=283.93,
        L0_deg=110.18,
        n_deg_per_day=0.2135,
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="jpl_sbdb",
        notes=(
            "Highest asteroid inclination + eccentricity in the roster. "
            "2e ≈ 26.4°; order 2 adds (5/4)e² ≈ 3.81°; order 3 adds "
            "0.66°. Catalog ships orders 1-3."
        ),
    ),
    "hygiea": SecularElements(
        body="hygiea",
        e=0.1126,
        I_deg=3.84,
        Omega_deg=283.20,
        omega_bar_deg=312.31,
        L0_deg=176.85,
        n_deg_per_day=0.17725258,  # derived from BODIES.period_days=2031.0
        frame="heliocentric_ecliptic",
        parent=None,
        source_key="jpl_sbdb",
        notes="2e ≈ 12.90°; order 2 adds 0.91° (ships order 1-2).",
    ),
}


# ──────────────────────────────────────────────────────────────────────
# Sanity helpers
# ──────────────────────────────────────────────────────────────────────


def get(body: str) -> SecularElements:
    """Return the secular-elements row for ``body``.

    Raises ``KeyError`` if ``body`` is not in the catalog (e.g. Sun,
    which has ``e ≡ 0``).
    """
    return SECULAR_ELEMENTS[body]


def list_bodies() -> list[str]:
    """Return the catalog body names, sorted."""
    return sorted(SECULAR_ELEMENTS.keys())


def list_by_frame(frame: str) -> list[str]:
    """Return body names with a given frame, sorted."""
    return sorted(
        body
        for body, row in SECULAR_ELEMENTS.items()
        if row.frame == frame
    )
