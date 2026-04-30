"""Visibility windows + heliacal rising/setting computation.

The astronomical baseline behind §11.6.16 of the research notebook:
each planet has invisibility windows around solar conjunction, and
heliacal rising / setting events delimit observable periods.

Skyfield is the optional dependency that powers this module; if it
isn't installed (or no kernel is on disk), the functions return
``None`` and bridge methods report UNDETERMINED.

References
----------
Schaefer, B. E. (1985). Predicting heliacal risings and settings.
    *Sky and Telescope* 70:261.
Toomer, G. J. (1984). *Ptolemy's Almagest*. Princeton.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


# Heliacal-event thresholds in degrees of solar elongation. These are
# rough operational values (Schaefer 1985); fainter planets need wider
# elongation to be visible against twilight.
_HELIACAL_THRESHOLDS_DEG: Dict[str, float] = {
    "mercury": 18.0,
    "venus":    7.0,
    "mars":    13.0,
    "jupiter": 11.0,
    "saturn":  13.0,
    "moon":     0.5,
}

# Skyfield body-name mappings.
_SKYFIELD_NAMES: Dict[str, str] = {
    "mercury": "mercury",
    "venus":   "venus",
    "mars":    "mars",
    "jupiter": "jupiter barycenter",
    "saturn":  "saturn barycenter",
    "sun":     "sun",
    "moon":    "moon",
}

SUPPORTED_PLANETS: Tuple[str, ...] = (
    "mercury", "venus", "mars", "jupiter", "saturn",
)


def _load_skyfield_bundle(kernel: str = "de421") -> Optional[Any]:
    """Return an EphemerisBundle for the requested kernel, or None."""
    try:
        from antikythera_spectral._research.ephemeris_loader import (
            load_ephemeris,
        )
    except ImportError:
        return None
    return load_ephemeris(kernel)


def get_solar_elongation_deg(jd_tdb: float, planet: str,
                              kernel: str = "de421") -> Optional[float]:
    """Solar elongation (degrees) of `planet` at `jd_tdb`.

    Returns None if skyfield/kernel unavailable.
    """
    if planet.lower() not in SUPPORTED_PLANETS:
        return None
    bundle = _load_skyfield_bundle(kernel)
    if bundle is None:
        return None

    # Build skyfield observers + targets from the bundle's `eph` handle.
    eph = bundle.eph
    ts = bundle.ts
    earth = eph["earth"]
    sun = eph["sun"]
    target = eph[_SKYFIELD_NAMES[planet.lower()]]

    t = ts.tdb_jd(jd_tdb)
    sun_pos = earth.at(t).observe(sun).apparent()
    target_pos = earth.at(t).observe(target).apparent()
    sep = sun_pos.separation_from(target_pos)
    return float(sep.degrees)


def get_next_heliacal_rising(jd_tdb: float, planet: str,
                              kernel: str = "de421",
                              max_search_days: float = 800.0,
                              step_days: float = 1.0) -> Optional[float]:
    """Find the next JD when `planet` emerges from solar glare.

    Implementation is a coarse linear search forward from `jd_tdb` for
    the first crossing of the solar-elongation threshold from below to
    above. ``max_search_days`` caps the search.

    Returns the crossing JD, or None if no crossing within the search
    window or skyfield unavailable.
    """
    p = planet.lower()
    if p not in _HELIACAL_THRESHOLDS_DEG:
        return None
    threshold = _HELIACAL_THRESHOLDS_DEG[p]

    bundle = _load_skyfield_bundle(kernel)
    if bundle is None:
        return None

    # Walk forward, look for first crossing.
    prev_elong = get_solar_elongation_deg(jd_tdb, planet, kernel)
    if prev_elong is None:
        return None

    n_steps = int(math.ceil(max_search_days / step_days))
    for i in range(1, n_steps + 1):
        jd = jd_tdb + i * step_days
        elong = get_solar_elongation_deg(jd, planet, kernel)
        if elong is None:
            continue
        if prev_elong < threshold <= elong:
            # Linear interpolation between the two samples.
            frac = (threshold - prev_elong) / (elong - prev_elong)
            return jd_tdb + (i - 1 + frac) * step_days
        prev_elong = elong
    return None


def get_visibility_windows(jd_lo: float, jd_hi: float, planet: str,
                            kernel: str = "de421",
                            step_days: float = 5.0) -> Optional[List[Tuple[float, float]]]:
    """Sample the elongation curve and return (rise, set) JD windows.

    A window is a contiguous run where elongation > threshold. Coarse
    sampling: 5-day step by default.

    Returns
    -------
    list of tuples or None
        Each tuple is (heliacal_rising_jd, heliacal_setting_jd).
        None if skyfield/kernel unavailable.
    """
    p = planet.lower()
    if p not in _HELIACAL_THRESHOLDS_DEG:
        return None
    threshold = _HELIACAL_THRESHOLDS_DEG[p]
    bundle = _load_skyfield_bundle(kernel)
    if bundle is None:
        return None

    n_samples = int(math.ceil((jd_hi - jd_lo) / step_days))
    samples: List[Tuple[float, float]] = []
    for i in range(n_samples + 1):
        jd = jd_lo + i * step_days
        elong = get_solar_elongation_deg(jd, planet, kernel)
        if elong is not None:
            samples.append((jd, elong))

    windows: List[Tuple[float, float]] = []
    in_window = False
    win_start = 0.0
    prev_jd = 0.0
    prev_elong = 0.0
    for jd, e in samples:
        if not in_window and e > threshold:
            # Use linear-interp crossing if previous sample exists
            win_start = jd
            if prev_elong > 0 and prev_jd > 0 and prev_elong < threshold < e:
                frac = (threshold - prev_elong) / (e - prev_elong)
                win_start = prev_jd + frac * (jd - prev_jd)
            in_window = True
        elif in_window and e <= threshold:
            win_end = jd
            if prev_elong > 0 and prev_elong > threshold >= e:
                frac = (prev_elong - threshold) / (prev_elong - e)
                win_end = prev_jd + frac * (jd - prev_jd)
            windows.append((win_start, win_end))
            in_window = False
        prev_jd, prev_elong = jd, e
    if in_window:
        windows.append((win_start, jd_hi))
    return windows


__all__ = [
    "SUPPORTED_PLANETS",
    "get_solar_elongation_deg",
    "get_next_heliacal_rising",
    "get_visibility_windows",
]
