"""Babylonian Goal-Year overlay.

Given a (planet, jd) pair, return what an astronomer using the Goal-Year
N-year cycle for that planet would have predicted, by reading the same
phenomenon from N years prior.

For Mars the canonical cycle is 47 years (not 79; 47 yr = 22 synodic
periods to high precision). For Saturn 59 yr; Jupiter 71 yr; Venus
8 yr; Mercury 46 yr.

References: MUL.APIN, Almagest IX.3, Britton 2010 *Studies in Babylonian
Goal-Year Astronomy*. The frozen ``_data/periods.json`` carries the
specific cycle relations used.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


_GOAL_YEAR_CYCLES_DAYS: Dict[str, float] = {
    # Babylonian Goal-Year cycles in tropical days (synodic-period
    # multiples). Sources: Britton 2010 §3 Table 1; Almagest IX.3.
    "mars":    47 * 365.25,
    "venus":    8 * 365.25,
    "mercury": 46 * 365.25,
    "jupiter": 71 * 365.25,
    "saturn":  59 * 365.25,
}


def predict(planet: str, jd_tdb: float, *,
             source: str = "mulapin") -> Dict[str, Any]:
    """JD that the Goal-Year cycle would direct an astronomer to query.

    The "prediction" for ``jd_tdb`` is the same phenomenon read from
    ``jd_tdb - cycle_days`` (i.e. one full Goal-Year cycle earlier).
    """
    p = planet.lower()
    if p not in _GOAL_YEAR_CYCLES_DAYS:
        raise ValueError(f"no Goal-Year cycle known for {planet!r}")
    if source not in ("mulapin", "almagest"):
        raise ValueError(f"source must be 'mulapin' or 'almagest', got {source!r}")
    cycle_days = _GOAL_YEAR_CYCLES_DAYS[p]
    return {
        "planet": p,
        "source": source,
        "jd_query": float(jd_tdb),
        "cycle_days": float(cycle_days),
        "lookup_jd": float(jd_tdb) - cycle_days,
        "cycle_years": float(cycle_days / 365.25),
        "method_note": (
            f"Goal-Year cycle: read the same phenomenon from "
            f"{cycle_days / 365.25:.0f} years before the query date. "
            f"Britton 2010 §3."
        ),
    }


def compare(planet: str, jd_tdb: float) -> Dict[str, Any]:
    """Goal-Year prediction + encoder prediction + (skyfield) truth."""
    g = predict(planet, jd_tdb)
    out: Dict[str, Any] = dict(g)
    # Encoder prediction: just the dial residue at jd_tdb. The encoder
    # uses MODERN cycle data (CYCLES.modern_days), not Goal-Year cycles,
    # so we report it as a side-by-side reference rather than an inverse.
    try:
        from antikythera_spectral._research.encode_ant import (
            DIAL_SPECS, REFERENCE_JD,
        )
        # Find the planetary dial whose name starts with the planet
        # (e.g. "Mars_synodic_period_relation").
        planet_cap = planet.capitalize()
        spec = next(
            (s for s in DIAL_SPECS if s.name.startswith(planet_cap)),
            None,
        )
        if spec is not None and spec.cycle_period_days:
            phase = ((jd_tdb - REFERENCE_JD) / spec.cycle_period_days) % 1.0
            out["encoder_angle_deg"] = float(phase * 360.0)
            out["encoder_dial"] = spec.name
    except (ImportError, ValueError, AttributeError):
        pass
    return out


__all__ = ["predict", "compare"]
