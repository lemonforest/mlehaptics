"""Celestial bodies database for the DE441 Mechanism.

Contains orbital periods (sidereal days) and relative masses (Earth = 1.0)
for the construction of the Solar System Graph Laplacian.

Period precision discipline (v0.5.3+)
-------------------------------------

Sidereal periods are stored to 9+ decimal places (d) — enough that
the ``omega = 2π / P`` propagation accumulates < 1° of phase error
over the v0.5.2 200-yr DE441 sweep horizon. Earlier versions stored
periods to 3-4 decimals; that 10⁻⁴-relative truncation produced
sawtooth-shaped FFT residuals at near-DC content (FFT peak at the
sweep span = 336 yr) for the moons whose mean motions are fast
enough to accumulate visible drift over 41,000+ orbits — Io / Europa
/ Ganymede / Mimas / Enceladus / Tethys / Dione / Rhea + the Jovian
inner regulars. Sources are JPL HORIZONS sidereal periods (canonical)
and NASA fact sheets (cross-checks). See `figures/moon_residual_v053.md`.
"""

from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class Body:
    name: str
    period_days: float  # Sidereal period in days (0.0 for Sun)
    mass_earth: float   # Mass relative to Earth
    category: str       # 'star', 'planet', 'moon', 'asteroid'
    # v0.11.0: volumetric mean radius in km, used for the SPrT
    # surface gravitational time-dilation calculation. For non-spherical
    # bodies (Saturnian moons, asteroids, Mars), use the volumetric
    # mean — radius of a sphere with the same volume as the actual
    # body. Sources: NASA fact sheets / JPL HORIZONS small-body
    # database. Defaults to 0.0 for backwards compatibility; bodies
    # with 0.0 radius cannot have their SPrT GR component computed.
    surface_radius_km: float = 0.0

BODIES: Dict[str, Body] = {
    # Star — radius from NASA solar fact sheet (volumetric mean).
    "sun": Body("Sun", 0.0, 333000.0, "star",
                surface_radius_km=695700.0),

    # Planets — sidereal periods from JPL HORIZONS / NASA fact sheets;
    # radii are volumetric-mean values (sphere-of-equal-volume), since
    # the SPrT GR component is a body-averaged quantity. These match
    # NASA planetary fact sheets to the rounding shown.
    "mercury": Body("Mercury",    87.96925980, 0.0553,  "planet", surface_radius_km=2_439.7),
    "venus":   Body("Venus",     224.70079922, 0.815,   "planet", surface_radius_km=6_051.8),
    "terra":   Body("Terra",     365.25636300, 1.0,     "planet", surface_radius_km=6_371.0),
    "mars":    Body("Mars",      686.97970000, 0.107,   "planet", surface_radius_km=3_389.5),
    "jupiter": Body("Jupiter",  4332.58900000, 317.8,   "planet", surface_radius_km=69_911.0),
    "saturn":  Body("Saturn",  10759.22000000,  95.16,  "planet", surface_radius_km=58_232.0),
    "uranus":  Body("Uranus",  30688.50000000,  14.54,  "planet", surface_radius_km=25_362.0),
    "neptune": Body("Neptune", 60182.00000000,  17.15,  "planet", surface_radius_km=24_622.0),
    "pluto":   Body("Pluto",   90560.00000000,   0.00218, "planet", surface_radius_km=1_188.3),

    # ---- Terra's moon (Luna) — synodic / sidereal precision per JPL HORIZONS ----
    # `luna` is the body identity (proper noun); `"moon"` (the 4th arg) is the
    # category, generic across all natural satellites in the roster.
    "luna": Body("Luna", 27.32166156, 0.0123, "moon", surface_radius_km=1_737.4),

    # ---- Mars's moons ---- (small irregular bodies; mean radii)
    "phobos": Body("Phobos", 0.31891023, 1.7e-9,  "moon", surface_radius_km=11.1),
    "deimos": Body("Deimos", 1.26244000, 2.4e-10, "moon", surface_radius_km=6.2),

    # ---- Jovian inner regular moons ----
    "metis":    Body("Metis",    0.29478000, 6.3e-12, "moon", surface_radius_km=21.5),
    "adrastea": Body("Adrastea", 0.29826000, 3.4e-12, "moon", surface_radius_km=8.2),
    "amalthea": Body("Amalthea", 0.49817905, 3.5e-10, "moon", surface_radius_km=83.5),
    "thebe":    Body("Thebe",    0.67451400, 7.5e-11, "moon", surface_radius_km=49.3),

    # ---- Galilean moons (Laplace 4:2:1 resonance) ----
    "io":       Body("Io",        1.76913786, 0.015, "moon", surface_radius_km=1_821.6),
    "europa":   Body("Europa",    3.55118100, 0.008, "moon", surface_radius_km=1_560.8),
    "ganymede": Body("Ganymede",  7.15455296, 0.025, "moon", surface_radius_km=2_634.1),
    "callisto": Body("Callisto", 16.68901840, 0.018, "moon", surface_radius_km=2_410.3),

    # ---- Jovian irregular moons (v0.16.0) ----
    # Highly inclined orbits (~150°+ for the retrogrades, ~28° for the
    # progrades). Captured-asteroid origin is standard interpretation.
    # Encoder convention from v0.5.4 / v0.14.2: omega = +2π/P regardless
    # of orbital direction; retrograde-ness is metadata, not a sign flip.
    "himalia":   Body("Himalia",   250.5662000,  1.10e-9, "moon", surface_radius_km=85.0),
    "pasiphae":  Body("Pasiphae",  743.6300000,  5.00e-12, "moon", surface_radius_km=30.0),
    "sinope":    Body("Sinope",    758.9000000,  1.30e-12, "moon", surface_radius_km=19.0),

    # ---- Classical Saturnian moons + Janus / Epimetheus co-orbitals ----
    "mimas":      Body("Mimas",       0.94242196, 6.31e-9, "moon", surface_radius_km=198.2),
    "enceladus":  Body("Enceladus",   1.37021785, 1.81e-5, "moon", surface_radius_km=252.1),
    "tethys":     Body("Tethys",      1.88780216, 1.04e-7, "moon", surface_radius_km=531.0),
    "dione":      Body("Dione",       2.73691500, 1.83e-7, "moon", surface_radius_km=561.4),
    "rhea":       Body("Rhea",        4.51821200, 3.85e-4, "moon", surface_radius_km=763.5),
    "titan":      Body("Titan",      15.94542100, 2.25e-2, "moon", surface_radius_km=2_574.7),
    "hyperion":   Body("Hyperion",   21.27660925, 9.36e-9, "moon", surface_radius_km=135.0),
    "iapetus":    Body("Iapetus",    79.32150000, 3.02e-7, "moon", surface_radius_km=734.3),
    "phoebe":     Body("Phoebe",    550.56463600, 1.39e-9, "moon", surface_radius_km=106.5),
    "janus":      Body("Janus",       0.69458200, 3.16e-10, "moon", surface_radius_km=89.5),
    "epimetheus": Body("Epimetheus",  0.69423500, 8.97e-11, "moon", surface_radius_km=58.1),

    # ---- Saturnian Lagrange trojans (v0.16.0) ----
    # First L4/L5 entries in BODIES. Each pair shares its host moon's
    # sidereal period exactly (1:1 mean-motion lock at the L4/L5 fixed
    # points of the Saturn-host CR3BP), giving the body-graph Laplacian
    # a multiplicity-2 degeneracy at the host's frequency. This is the
    # natural intersection point with the v0.16.x resonance-graph
    # multi-leg find_itn_chains work (notebook §12).
    #
    # Telesto + Calypso ride at Tethys's L4 + L5 respectively.
    # Helene + Polydeuces ride at Dione's L4 + L5 respectively.
    "telesto":     Body("Telesto",     1.88780216, 4.0e-12,  "moon", surface_radius_km=12.4),
    "calypso":     Body("Calypso",     1.88780216, 1.2e-12,  "moon", surface_radius_km=9.6),
    "helene":      Body("Helene",      2.73691500, 1.9e-12,  "moon", surface_radius_km=17.5),
    "polydeuces":  Body("Polydeuces",  2.73691500, 4.4e-15,  "moon", surface_radius_km=1.3),

    # ---- Uranian classical moons ----
    # All five major moons discovered between 1787 and 1948. Sidereal
    # periods from JPL HORIZONS; volumetric-mean radii from NASA fact
    # sheets / Voyager 2 imagery analysis. Masses relative to Earth
    # are derived from kg estimates against Earth = 5.9722e24 kg.
    # Note: Uranus's rotation axis tilt (~98°) means these moons orbit
    # in a plane near-perpendicular to the ecliptic; the encoder
    # convention (omega = +2pi/P regardless of orbital orientation)
    # carries through unchanged from v0.5.4 Sol Uranian Time.
    "miranda": Body("Miranda",  1.41347925,  1.10e-5, "moon", surface_radius_km=235.8),
    "ariel":   Body("Ariel",    2.52037935,  2.27e-4, "moon", surface_radius_km=578.9),
    "umbriel": Body("Umbriel",  4.14417500,  2.02e-4, "moon", surface_radius_km=584.7),
    "titania": Body("Titania",  8.70586900,  5.70e-4, "moon", surface_radius_km=788.4),
    "oberon":  Body("Oberon",  13.46323907,  5.05e-4, "moon", surface_radius_km=761.4),

    # ---- Neptunian moons ----
    # Triton is the only large moon in the solar system that orbits
    # its planet retrograde -- strong evidence it's a captured Kuiper
    # Belt object. Encoder convention: positive omega; retrograde-ness
    # is metadata, not a sign flip in the time-scale primitive.
    "triton":  Body("Triton",   5.87685400,  0.00359, "moon", surface_radius_km=1_353.4),

    # Proteus is Neptune's second-largest moon (radius ~210 km,
    # near-spherical despite being below the canonical hydrostatic-
    # equilibrium threshold for icy bodies). Discovered by Voyager 2
    # in 1989. Period 1.122 d -- fills the Neptune sub-graph between
    # Triton (5.88 d) and the inner-Neptunian close-packed cluster
    # (Naiad/Thalassa/Despina/Galatea/Larissa, all <0.6 d).
    "proteus": Body("Proteus",  1.12231500,  7.40e-9, "moon", surface_radius_km=210.0),

    # Nereid has the most eccentric orbit of any major moon in the
    # solar system (e=0.749) -- discovered by Kuiper in 1949,
    # likely a captured asteroid or KBO that's been in a chaotic-
    # libration eccentricity-pumping regime since capture. Period
    # 360.13 d -- almost exactly one terrestrial year, which is a
    # spectral coincidence not a resonance.
    "nereid":  Body("Nereid",  360.13619000,  5.10e-9, "moon", surface_radius_km=170.0),

    # ---- Plutonian moon ----
    # Charon is mutually tidally locked with Pluto -- both bodies show
    # the same face to each other forever. The Pluto-Charon system is
    # closer to a binary planet than a planet+moon (Charon's mass is
    # ~12% of Pluto's). The barycentre is OUTSIDE Pluto; Pluto wobbles
    # around it. Sidereal period equals the mutual rotation period of
    # the locked pair: 6.387230 days.
    "charon":  Body("Charon",   6.38723000,  2.66e-4, "moon", surface_radius_km=606.0),

    # Asteroids — sidereal periods per JPL HORIZONS; mean radii (irregular shapes).
    "ceres":   Body("Ceres",   1681.63100000, 0.00015, "asteroid", surface_radius_km=469.7),
    "vesta":   Body("Vesta",   1325.75000000, 4.3e-5,  "asteroid", surface_radius_km=262.7),
    "pallas":  Body("Pallas",  1686.00000000, 3.4e-5,  "asteroid", surface_radius_km=256.0),
    "hygiea":  Body("Hygiea",  2031.00000000, 1.4e-5,  "asteroid", surface_radius_km=215.0),
}
