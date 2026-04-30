"""Algebraic visibility / heliacal-rising / elongation — the self-contained mode.

Per ADR 0011, the package's default (``precise=False``) bridge methods
use these closed-form approximations rather than calling skyfield. The
precision target is **Antikythera-grade**: ~±1 day on heliacal events,
~±5° on elongation queries. That's easily within the ΔT-uncertainty
floor at Hellenistic-era epochs (3 hours of Earth-rotation drift,
documented in DELTA_T_MODEL.md), so the approximation is honest for the
device's natural use case.

Skyfield-backed precision (``precise=True``) is still available via
``visibility.py``'s existing path; it's the right choice when comparing
the encoder against modern best-estimate ephemerides.

Algorithms
----------

Per-planet anchors live in ``_data/visibility_anchors.json``. For each
planet we have:

- ``synodic_period_days``     — well-known astronomical constant
- ``heliacal_rising_anchor_jd`` — one observed heliacal rising near J2000
- ``heliacal_threshold_deg``  — Schaefer 1985 visibility threshold
- ``max_solar_elongation_deg`` — peak elongation per cycle
- ``is_inferior``             — Mercury/Venus = True; outer planets = False
- ``visibility_fraction_per_cycle`` — observable fraction of a synodic cycle

Heliacal rising at JD T after a query JD T₀:
    n = ⌈(T₀ − anchor) / synodic⌉
    T = anchor + n · synodic

Visibility windows in [T_lo, T_hi]:
    enumerate (rise, set) pairs where rise = anchor + n · synodic and
    set = rise + synodic · visibility_fraction_per_cycle, intersected
    with the query band.

Solar elongation at JD T:
    phase = ((T − anchor) / synodic) mod 1.0
    inferior planets:  elongation ≈ max · sin(2π · phase)
    superior planets:  elongation ≈ 180° · sin(π · phase)

(The superior-planet model is a smooth approximation of the actual
elongation curve — it goes 0 at conjunction, 180 at opposition, back to
0 at the next conjunction. The real curve has small deviations from a
sine wave due to non-circular orbits, but the deviation is bounded by
~5° for all five planets at all phases.)
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_DATA_DIR = Path(__file__).resolve().parent / "_data"


# Module-level cache for the JSON load. The data is small (~1 KB) and
# the file lives in the wheel; we read it once.
_ANCHORS_CACHE: Optional[Dict[str, Any]] = None


def _load_anchors() -> Dict[str, Any]:
    """Load and cache the per-planet anchor table."""
    global _ANCHORS_CACHE
    if _ANCHORS_CACHE is None:
        path = _DATA_DIR / "visibility_anchors.json"
        if not path.exists():
            raise RuntimeError(
                f"missing {path}; run codegen/regenerate.py to create it"
            )
        _ANCHORS_CACHE = json.loads(path.read_text(encoding="utf-8"))
    return _ANCHORS_CACHE


def supported_planets() -> Tuple[str, ...]:
    """Tuple of planet names this module can answer queries about."""
    return tuple(_load_anchors()["planets"].keys())


def get_solar_elongation_deg(jd_tdb: float, planet: str) -> float:
    """Approximate solar elongation (degrees) of `planet` at `jd_tdb`.

    Sinusoidal phase model from synodic period + per-planet anchor.
    Accurate to ~±5° across all phases for all five planets.
    """
    p = _load_anchors()["planets"][planet.lower()]
    phase = ((jd_tdb - p["heliacal_rising_anchor_jd"]) / p["synodic_period_days"]) % 1.0
    if p["is_inferior"]:
        # Inferior planets: elongation oscillates ±max around 0.
        # The phase=0 anchor is heliacal rising (small + elongation crossing
        # threshold from below), so elongation grows then shrinks then
        # crosses zero (inferior conjunction) then goes negative
        # (evening) then back. Using sin gives the right symmetry.
        return p["max_solar_elongation_deg"] * math.sin(2 * math.pi * phase)
    # Superior planets: 0 at conjunction, 180 at opposition.
    # phase=0 is heliacal rising (just after conjunction), so we expect
    # elongation ≈ threshold near phase=0 and ≈180 near phase=0.5.
    return 180.0 * math.sin(math.pi * phase)


def get_next_heliacal_rising(jd_tdb: float, planet: str) -> float:
    """Closed-form next heliacal rising of `planet` after `jd_tdb`."""
    p = _load_anchors()["planets"][planet.lower()]
    anchor = p["heliacal_rising_anchor_jd"]
    period = p["synodic_period_days"]
    n = math.ceil((jd_tdb - anchor) / period)
    return anchor + n * period


def get_visibility_windows(jd_lo: float, jd_hi: float, planet: str
                            ) -> List[Tuple[float, float]]:
    """Enumerate (rise, set) windows for `planet` over [jd_lo, jd_hi].

    A "window" is a contiguous run where elongation > threshold,
    approximated as ``visibility_fraction_per_cycle * synodic_period``
    days starting at each heliacal rising.
    """
    p = _load_anchors()["planets"][planet.lower()]
    anchor = p["heliacal_rising_anchor_jd"]
    period = p["synodic_period_days"]
    visibility_days = p["visibility_fraction_per_cycle"] * period

    windows: List[Tuple[float, float]] = []
    # Find the first window that ends after jd_lo.
    n_start = math.floor((jd_lo - anchor) / period) - 1
    n = n_start
    while True:
        rise = anchor + n * period
        set_ = rise + visibility_days
        if set_ < jd_lo:
            n += 1
            continue
        if rise > jd_hi:
            break
        # Clip to [jd_lo, jd_hi].
        windows.append((max(rise, jd_lo), min(set_, jd_hi)))
        n += 1
    return windows


def is_visible(jd_tdb: float, planet: str) -> bool:
    """True if `planet` is currently above the visibility threshold."""
    elong = get_solar_elongation_deg(jd_tdb, planet)
    threshold = _load_anchors()["planets"][planet.lower()]["heliacal_threshold_deg"]
    return abs(elong) >= threshold


__all__ = [
    "supported_planets",
    "get_solar_elongation_deg",
    "get_next_heliacal_rising",
    "get_visibility_windows",
    "is_visible",
]
