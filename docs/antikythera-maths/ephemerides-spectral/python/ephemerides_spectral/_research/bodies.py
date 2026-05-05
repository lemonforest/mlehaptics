"""Celestial bodies database for the DE441 Mechanism.

Contains orbital periods (sidereal days) and relative masses (Earth = 1.0)
for the construction of the Solar System Graph Laplacian.
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
    
    # Planets
    "mercury": Body("Mercury", 87.969, 0.0553, "planet"),
    "venus": Body("Venus", 224.701, 0.815, "planet"),
    "earth": Body("Earth", 365.256, 1.0, "planet"),
    "mars": Body("Mars", 686.980, 0.107, "planet"),
    "jupiter": Body("Jupiter", 4332.59, 317.8, "planet"),
    "saturn": Body("Saturn", 10759.22, 95.16, "planet"),
    "uranus": Body("Uranus", 30688.5, 14.54, "planet"),
    "neptune": Body("Neptune", 60182.0, 17.15, "planet"),
    "pluto": Body("Pluto", 90560.0, 0.00218, "planet"),
    
    # ---- Earth's moon ----
    "moon": Body("Moon", 27.321, 0.0123, "moon"),

    # ---- Mars's moons (Phobos has the shortest period in the system) ----
    "phobos": Body("Phobos", 0.3189, 1.7e-9, "moon"),
    "deimos": Body("Deimos", 1.263, 2.4e-10, "moon"),

    # ---- Jovian inner regular moons (v0.5.0 expansion) ----
    "metis": Body("Metis", 0.2948, 6.3e-12, "moon"),
    "adrastea": Body("Adrastea", 0.2983, 3.4e-12, "moon"),
    "amalthea": Body("Amalthea", 0.4982, 3.5e-10, "moon"),
    "thebe": Body("Thebe", 0.6745, 7.5e-11, "moon"),

    # ---- Galilean moons (Laplace 4:2:1 resonance) ----
    "io": Body("Io", 1.769, 0.015, "moon"),
    "europa": Body("Europa", 3.551, 0.008, "moon"),
    "ganymede": Body("Ganymede", 7.155, 0.025, "moon"),
    "callisto": Body("Callisto", 16.689, 0.018, "moon"),

    # ---- Classical Saturnian moons (v0.5.0 expansion: 6 new) ----
    # Mimas through Phoebe — the canonical 9 + Janus/Epimetheus
    # co-orbitals. Many drive named resonances:
    #   * Mimas–Tethys 4:2 (Cassini Division)
    #   * Enceladus–Dione 2:1 (powers Enceladus's tidal heating)
    #   * Titan–Hyperion 4:3 (Hyperion's chaotic rotation)
    "mimas": Body("Mimas", 0.9424, 6.31e-9, "moon"),
    "enceladus": Body("Enceladus", 1.370, 1.81e-5, "moon"),
    "tethys": Body("Tethys", 1.888, 1.04e-7, "moon"),
    "dione": Body("Dione", 2.737, 1.83e-7, "moon"),
    "rhea": Body("Rhea", 4.518, 3.85e-4, "moon"),
    "titan": Body("Titan", 15.945, 2.25e-2, "moon"),
    "hyperion": Body("Hyperion", 21.276, 9.36e-9, "moon"),
    "iapetus": Body("Iapetus", 79.331, 3.02e-7, "moon"),
    "phoebe": Body("Phoebe", 550.31, 1.39e-9, "moon"),

    # ---- Saturn co-orbitals (share an orbit, swap places every 4 yr) ----
    "janus": Body("Janus", 0.6945, 3.16e-10, "moon"),
    "epimetheus": Body("Epimetheus", 0.6943, 8.97e-11, "moon"),

    # ---- Uranus / Neptune (one each; still placeholders for a fuller expansion) ----
    "titania": Body("Titania", 8.706, 5.7e-4, "moon"),
    "triton": Body("Triton", 5.877, 0.00359, "moon"),
    
    # Asteroids
    "ceres": Body("Ceres", 1681.63, 0.00015, "asteroid"),
    "vesta": Body("Vesta", 1325.75, 4.3e-5, "asteroid"),
    "pallas": Body("Pallas", 1686.0, 3.4e-5, "asteroid"),
    "hygiea": Body("Hygiea", 2031.0, 1.4e-5, "asteroid"),
}
