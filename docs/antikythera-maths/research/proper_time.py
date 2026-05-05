"""Sol Proper Time (SPrT) primitives — v0.11.0.

Per-body proper-time-rate computation relative to TCB (barycentric
coordinate time, the IAU reference for Solar-System dynamics).

Two leading-order components are scored for every body:

    1. **Surface gravitational time dilation** — `GM/(Rc²)` at the body's
       surface. Positive — clocks tick slower in the body's gravitational
       well. The same physics as Mercury's existing 43"/century PN
       diagonal correction, applied to every body in the roster as a
       per-body diagonal "fiber."

    2. **Mean orbital kinematic time dilation** — `v_orb²/(2c²)`,
       leading-order Special Relativity time dilation due to the body's
       orbital velocity in the barycentric frame. Computed from
       Kepler's third law with sidereal period + central-body GM.

The total clock rate of a stationary surface clock relative to TCB is

    rate ≈ 1 - gr_surface - kinematic_orbital

For most users, this is exactly the correction the `--proper` CLI flag
applies to existing `time-*` commands.

What this module does NOT model (deferred to v0.12.0+):

    - Surface rotational kinematic (`ω × R` at the body's surface
      latitude). For most bodies the orbital term dominates; for the
      Sun, rotational dominates (no orbital motion to speak of).
    - J₂ oblateness corrections (~10⁻¹⁵ scale spatial variation).
      Adding `J2_oblateness` per body in `bodies.py` lets `--lat`/`--lon`
      kick in for that precision tier.
    - Frame dragging (Lense-Thirring; ~10⁻¹⁵ at Earth-Moon scale).

References
----------

- Misner, Thorne, Wheeler. *Gravitation*, ch. 38 (PPN formalism).
- Ashby, N. (2003). "Relativity in the Global Positioning System."
  *Living Rev. Relativity* 6, 1.
- Genova, A. et al. (2014). "Mars high-resolution global gravity
  field." *Geophys. Res. Lett.* 41(18). — Curiosity rover navigation
  baseline numbers.

Validated against six published values to within 0.30 % — see
`tests/test_sprt.py` for the regression discipline and
`research/proper_time_rates.py` for the Phase A audit script.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ephemerides_spectral._research.bodies import BODIES


# ──────────────────────────────────────────────────────────────────────
# Physical constants (SI, IAU 2015 conventions)
# ──────────────────────────────────────────────────────────────────────

#: Speed of light in vacuum (m/s).
C: float = 299_792_458.0

#: c² (m²/s²).
C_SQUARED: float = C * C

#: Newtonian gravitational constant (m³ / (kg · s²)).
G: float = 6.67430e-11

#: Earth's mass (kg). The mass scale used by `BODIES[*].mass_earth`.
EARTH_MASS_KG: float = 5.9722e24

#: Earth's gravitational parameter (m³ / s²) ≈ 3.986×10¹⁴.
GM_EARTH: float = G * EARTH_MASS_KG

#: Solar gravitational parameter (m³ / s²). Canonical IAU value.
GM_SUN: float = 1.32712440018e20

#: Seconds per day.
DAY_S: float = 86400.0


# ──────────────────────────────────────────────────────────────────────
# Parent-body table for moons (used by Kepler's third law)
# ──────────────────────────────────────────────────────────────────────

PARENT_OF: Dict[str, Optional[str]] = {
    "luna":       "terra",
    "phobos":     "mars",
    "deimos":     "mars",
    # Jovian
    "metis":      "jupiter",
    "adrastea":   "jupiter",
    "amalthea":   "jupiter",
    "thebe":      "jupiter",
    "io":         "jupiter",
    "europa":     "jupiter",
    "ganymede":   "jupiter",
    "callisto":   "jupiter",
    # Saturnian
    "mimas":      "saturn",
    "enceladus":  "saturn",
    "tethys":     "saturn",
    "dione":      "saturn",
    "rhea":       "saturn",
    "titan":      "saturn",
    "hyperion":   "saturn",
    "iapetus":    "saturn",
    "phoebe":     "saturn",
    "janus":      "saturn",
    "epimetheus": "saturn",
    # Uranus / Neptune
    "titania":    "uranus",
    "triton":     "neptune",
}

#: The reference time scale for SPrT rates.
DEFAULT_REFERENCE: str = "tcb"
SUPPORTED_REFERENCES: Tuple[str, ...] = ("tcb", "tdb")


# ──────────────────────────────────────────────────────────────────────
# Per-body computations
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProperTimeRate:
    """Leading-order proper-time-rate components for one body vs. TCB."""
    body: str
    reference: str
    gr_surface: float
    kinematic_orbital: float
    j2_oblateness: float
    total: float
    rate_relative_to_reference: float
    orbital_velocity_kms: float
    parent_body: Optional[str]
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body":                       self.body,
            "reference":                  self.reference,
            "rate_relative_to_reference": float(self.rate_relative_to_reference),
            "components": {
                "gr_surface":              float(self.gr_surface),
                "kinematic_orbital":       float(self.kinematic_orbital),
                "j2_oblateness":           float(self.j2_oblateness),
                "total":                   float(self.total),
            },
            "orbital_velocity_kms":       float(self.orbital_velocity_kms),
            "parent_body":                self.parent_body,
            **({"note": self.note} if self.note else {}),
        }


def _gm_for(body_key: str) -> float:
    if body_key == "sun":
        return GM_SUN
    if body_key not in BODIES:
        raise KeyError(f"unknown body {body_key!r}")
    return BODIES[body_key].mass_earth * GM_EARTH


def _gr_surface(body_key: str) -> Tuple[float, Optional[str]]:
    body = BODIES[body_key]
    if body.surface_radius_km <= 0.0:
        return (0.0, "no surface_radius_km in BODIES table")
    gm = _gm_for(body_key)
    r_m = body.surface_radius_km * 1000.0
    return (gm / (r_m * C_SQUARED), None)


def _kinematic_orbital(body_key: str) -> Tuple[float, float]:
    body = BODIES[body_key]
    if body.period_days <= 0.0:
        return (0.0, 0.0)
    parent = PARENT_OF.get(body_key)
    gm_central = GM_SUN if parent is None else _gm_for(parent)
    t_s = body.period_days * DAY_S
    a_m = (gm_central * t_s * t_s / (4.0 * math.pi * math.pi)) ** (1.0 / 3.0)
    v = 2.0 * math.pi * a_m / t_s
    return (v * v / (2.0 * C_SQUARED), v / 1000.0)


def get_proper_time_rate(
    body: str,
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    jd_tdb: Optional[float] = None,
    reference: str = DEFAULT_REFERENCE,
) -> ProperTimeRate:
    """Compute the leading-order proper-time rate for a body vs. TCB.

    `lat`/`lon`/`jd_tdb` are accepted for forward compatibility (J2
    oblateness + per-JD eccentricity deferred to v0.12.0+); v0.11.0
    ignores them and uses each body's mean orbital velocity.
    """
    if body not in BODIES:
        raise KeyError(
            f"unknown body {body!r}; valid keys: {sorted(BODIES)}"
        )
    if reference not in SUPPORTED_REFERENCES:
        raise ValueError(
            f"reference must be one of {list(SUPPORTED_REFERENCES)}, "
            f"got {reference!r}"
        )
    gr, gr_note = _gr_surface(body)
    kin, v_kms = _kinematic_orbital(body)
    j2 = 0.0
    total = gr + kin + j2
    note: Optional[str] = None
    if gr_note:
        note = gr_note
    return ProperTimeRate(
        body=body,
        reference=reference,
        gr_surface=gr,
        kinematic_orbital=kin,
        j2_oblateness=j2,
        total=total,
        rate_relative_to_reference=1.0 - total,
        orbital_velocity_kms=v_kms,
        parent_body=PARENT_OF.get(body),
        note=note,
    )


def compare_proper_times(
    body_a: str,
    body_b: str,
    *,
    reference: str = DEFAULT_REFERENCE,
) -> Dict[str, Any]:
    """Compare two bodies' proper-time rates.

    Convention: positive `seconds_per_earth_year` means body_a's
    surface clocks tick *slower* than body_b's.
    """
    a = get_proper_time_rate(body_a, reference=reference)
    b = get_proper_time_rate(body_b, reference=reference)
    delta_total = a.total - b.total
    rate_ratio = a.rate_relative_to_reference / b.rate_relative_to_reference
    return {
        "body_a":    body_a,
        "body_b":    body_b,
        "reference": reference,
        "rate_ratio_a_over_b":      rate_ratio,
        "delta_total_a_minus_b":    delta_total,
        "seconds_per_earth_year":   delta_total * 365.25 * DAY_S,
        "components_a": a.to_dict()["components"],
        "components_b": b.to_dict()["components"],
    }


__all__ = [
    "C", "G", "GM_EARTH", "GM_SUN", "DAY_S",
    "PARENT_OF",
    "DEFAULT_REFERENCE", "SUPPORTED_REFERENCES",
    "ProperTimeRate",
    "get_proper_time_rate",
    "compare_proper_times",
]
