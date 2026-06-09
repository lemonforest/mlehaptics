"""Sol Solar Cycle Spectrum Catalog — query surface for the v0.30.0rc3
ship (the Sun's magnetic activity cycle).

The third solar-dynamics catalogue on the v0.30.0 line, after the
v0.24.3 Sun Dynamical Spectrum (p-modes) and the rc2 differential
rotation. Where those read the Sun's *fast* oscillations and rotation,
this reads its *slow* magnetic clock: the ~11-year Schwabe sunspot
cycle, the 22-year Hale polarity cycle, the ~88-year Gleissberg
amplitude modulation, and the butterfly-diagram equatorward drift.

Four query surfaces:

* :func:`get_solar_cycle_spectrum` — the three cycle periods + the
  butterfly latitudes + the recent-cycle roster.
* :func:`get_hale_polarity_closure` — THE closure invariant: the Hale
  magnetic cycle is **exactly two** Schwabe cycles, because the Sun's
  global polarity *reverses* (a sign-flip) each activity cycle. The
  integer ``2:1`` commensurability is the polarity **Class-K sign-flip**
  made literal — the same sign-flip-doubles-the-period structure as an
  epicycle (the ring `(p:q)` resonance and the differential-rotation
  closure were the rc1/rc2 analogues).
* :func:`get_butterfly_drift` — Spörer's law: sunspots emerge at
  ~30° latitude at cycle start and drift to ~8° by cycle end.
* :func:`list_solar_cycle_spectrum` — enumeration + citations.

Scope note: this catalogues the *periods and latitudes* of the cycle
(integer commensurability + a drift law), not a flux-transport dynamo
simulation. The Class-K sign-flip framing is an honest structural
reading of the polarity reversal, not a forced ``the_one`` mapping
(the cycle is a scalar period structure, not a Hurwitz rotation).

Reference: research notebook §17 (solar dynamics); Spike #49 / task
#267 (solar-surface field activity) is the deeper chaotic-field thread
this period-structure catalogue sits beneath.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .solar_cycle_data import (
    BUTTERFLY_END_LATITUDE_DEG,
    BUTTERFLY_START_LATITUDE_DEG,
    GLEISSBERG_PERIOD_YEARS,
    HALE_PERIOD_YEARS,
    HALE_TO_SCHWABE_RATIO,
    SCHWABE_PERIOD_YEARS,
    SOLAR_CYCLES,
    SOURCES,
    cycle_to_data_dict,
)


def _cycles_out() -> List[Dict[str, Any]]:
    return [cycle_to_data_dict(c) for c in SOLAR_CYCLES]


def get_solar_cycle_spectrum() -> Dict[str, Any]:
    """The Sun's magnetic activity cycle — the period structure.

    Headlines: the **Schwabe** sunspot cycle (~11 yr), the **Hale**
    magnetic-polarity cycle (22 yr = 2 Schwabe), and the **Gleissberg**
    amplitude modulation (~88 yr ≈ 8 Schwabe cycles). The butterfly
    diagram tracks sunspots drifting equatorward over each cycle.

    Returns
    -------
    dict
        ``{ok, body, periods_years, butterfly_latitude_deg, n_cycles,
        cycles}``.
    """
    return {
        "ok": True,
        "body": "sol",
        "subject": "magnetic_activity_cycle",
        "periods_years": {
            "schwabe": SCHWABE_PERIOD_YEARS,
            "hale": HALE_PERIOD_YEARS,
            "gleissberg": GLEISSBERG_PERIOD_YEARS,
        },
        "butterfly_latitude_deg": {
            "cycle_start": BUTTERFLY_START_LATITUDE_DEG,
            "cycle_end": BUTTERFLY_END_LATITUDE_DEG,
        },
        "n_cycles": len(SOLAR_CYCLES),
        "cycles": _cycles_out(),
    }


def get_hale_polarity_closure() -> Dict[str, Any]:
    """THE closure invariant — the Hale magnetic cycle is exactly two
    Schwabe cycles.

    The Sun's global magnetic polarity reverses at each sunspot maximum
    (Hale & Nicholson 1925) and returns to its original sense only after
    **two** activity cycles, so the magnetic period is exactly twice the
    sunspot period: ``Hale = 2 × Schwabe``. The integer ``2:1``
    commensurability is driven by the polarity **sign-flip** — a
    Class-K pin-slot sign re-applied once per Schwabe cycle, the same
    structure by which an epicycle's sign-flip doubles its return
    period. Small integers + a sign-flip reproduce the structure, as in
    the rc1 ring `(p:q)` resonance and the Sun's helioseismic asymptotic
    relation.

    Returns
    -------
    dict
        ``{ok, body, schwabe_period_years, hale_period_years,
        hale_to_schwabe_ratio, predicted_hale_years, residual_years,
        polarity_flips_per_hale_cycle, interpretation}``.
    """
    predicted_hale = HALE_TO_SCHWABE_RATIO * SCHWABE_PERIOD_YEARS
    return {
        "ok": True,
        "body": "sol",
        "schwabe_period_years": SCHWABE_PERIOD_YEARS,
        "hale_period_years": HALE_PERIOD_YEARS,
        "hale_to_schwabe_ratio": HALE_TO_SCHWABE_RATIO,
        "predicted_hale_years": predicted_hale,
        "residual_years": predicted_hale - HALE_PERIOD_YEARS,
        "polarity_flips_per_hale_cycle": HALE_TO_SCHWABE_RATIO,
        "interpretation": (
            "The Hale magnetic cycle is exactly two Schwabe sunspot "
            "cycles: the Sun's global polarity reverses each activity "
            "cycle (Hale & Nicholson 1925) and only returns to its "
            "original sense after two, so Hale = 2 x Schwabe. The 2:1 "
            "commensurability is the polarity sign-flip -- a Class-K "
            "pin-slot sign re-applied once per cycle -- the same "
            "sign-flip-doubles-the-period structure as an epicycle."
        ),
    }


def get_butterfly_drift() -> Dict[str, Any]:
    """Spörer's law — the butterfly-diagram equatorward drift.

    Sunspots emerge at ~30° latitude at the start of a cycle and drift
    toward the equator (~8°) by its end; plotting emergence latitude vs
    time over many cycles draws the "butterfly" wings.

    Returns
    -------
    dict
        ``{ok, body, start_latitude_deg, end_latitude_deg,
        equatorward_drift_deg}``.
    """
    return {
        "ok": True,
        "body": "sol",
        "start_latitude_deg": BUTTERFLY_START_LATITUDE_DEG,
        "end_latitude_deg": BUTTERFLY_END_LATITUDE_DEG,
        "equatorward_drift_deg": (
            BUTTERFLY_START_LATITUDE_DEG - BUTTERFLY_END_LATITUDE_DEG
        ),
    }


def list_solar_cycle_spectrum() -> Dict[str, Any]:
    """Full enumeration of solar-cycle data + citations."""
    return {
        "ok": True,
        "body": "sol",
        "n_cycles": len(SOLAR_CYCLES),
        "n_sources": len(SOURCES),
        "periods_years": {
            "schwabe": SCHWABE_PERIOD_YEARS,
            "hale": HALE_PERIOD_YEARS,
            "gleissberg": GLEISSBERG_PERIOD_YEARS,
        },
        "cycles": _cycles_out(),
    }


__all__ = [
    "get_solar_cycle_spectrum",
    "get_hale_polarity_closure",
    "get_butterfly_drift",
    "list_solar_cycle_spectrum",
]
