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

BODIES: Dict[str, Body] = {
    # Star
    "sun": Body("Sun", 0.0, 333000.0, "star"),

    # Planets — sidereal periods from JPL HORIZONS / NASA fact sheets
    "mercury": Body("Mercury",    87.96925980, 0.0553, "planet"),
    "venus":   Body("Venus",     224.70079922, 0.815,  "planet"),
    "terra":   Body("Terra",     365.25636300, 1.0,    "planet"),
    "mars":    Body("Mars",      686.97970000, 0.107,  "planet"),
    "jupiter": Body("Jupiter",  4332.58900000, 317.8,  "planet"),
    "saturn":  Body("Saturn",  10759.22000000, 95.16,  "planet"),
    "uranus":  Body("Uranus",  30688.50000000, 14.54,  "planet"),
    "neptune": Body("Neptune", 60182.00000000, 17.15,  "planet"),
    "pluto":   Body("Pluto",   90560.00000000, 0.00218, "planet"),

    # ---- Terra's moon (Luna) — synodic / sidereal precision per JPL HORIZONS ----
    # `luna` is the body identity (proper noun); `"moon"` (the 4th arg) is the
    # category, generic across all natural satellites in the roster.
    "luna": Body("Luna", 27.32166156, 0.0123, "moon"),

    # ---- Mars's moons ----
    "phobos": Body("Phobos", 0.31891023, 1.7e-9,  "moon"),
    "deimos": Body("Deimos", 1.26244000, 2.4e-10, "moon"),

    # ---- Jovian inner regular moons ----
    "metis":    Body("Metis",    0.29478000, 6.3e-12, "moon"),
    "adrastea": Body("Adrastea", 0.29826000, 3.4e-12, "moon"),
    "amalthea": Body("Amalthea", 0.49817905, 3.5e-10, "moon"),
    "thebe":    Body("Thebe",    0.67451400, 7.5e-11, "moon"),

    # ---- Galilean moons (Laplace 4:2:1 resonance) ----
    "io":       Body("Io",        1.76913786,  0.015, "moon"),
    "europa":   Body("Europa",    3.55118100,  0.008, "moon"),
    "ganymede": Body("Ganymede",  7.15455296,  0.025, "moon"),
    "callisto": Body("Callisto", 16.68901840,  0.018, "moon"),

    # ---- Classical Saturnian moons + Janus / Epimetheus co-orbitals ----
    "mimas":      Body("Mimas",       0.94242196, 6.31e-9, "moon"),
    "enceladus":  Body("Enceladus",   1.37021785, 1.81e-5, "moon"),
    "tethys":     Body("Tethys",      1.88780216, 1.04e-7, "moon"),
    "dione":      Body("Dione",       2.73691500, 1.83e-7, "moon"),
    "rhea":       Body("Rhea",        4.51821200, 3.85e-4, "moon"),
    "titan":      Body("Titan",      15.94542100, 2.25e-2, "moon"),
    "hyperion":   Body("Hyperion",   21.27660925, 9.36e-9, "moon"),
    "iapetus":    Body("Iapetus",    79.32150000, 3.02e-7, "moon"),
    "phoebe":     Body("Phoebe",    550.56463600, 1.39e-9, "moon"),
    "janus":      Body("Janus",       0.69458200, 3.16e-10, "moon"),
    "epimetheus": Body("Epimetheus",  0.69423500, 8.97e-11, "moon"),

    # ---- Uranus / Neptune (one each; placeholders for a fuller expansion) ----
    "titania": Body("Titania", 8.70586900, 5.7e-4,  "moon"),
    "triton":  Body("Triton",  5.87685400, 0.00359, "moon"),

    # Asteroids — sidereal periods per JPL HORIZONS
    "ceres":   Body("Ceres",   1681.63100000, 0.00015, "asteroid"),
    "vesta":   Body("Vesta",   1325.75000000, 4.3e-5,  "asteroid"),
    "pallas":  Body("Pallas",  1686.00000000, 3.4e-5,  "asteroid"),
    "hygiea":  Body("Hygiea",  2031.00000000, 1.4e-5,  "asteroid"),
}
