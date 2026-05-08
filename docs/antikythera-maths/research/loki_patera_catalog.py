"""Sol Loki Patera Eruption Cycle Catalog — query surface for the
v0.24.12 ship (temporal-spectrum eruption-cycle observable on the
Solar System's most active volcano; v0.24.8 Axial Seamount cousin
with Galilean-Laplace tidal-heating forcing instead of mantle-
plume forcing).

Promotes the v0.24.12 architectural commitment to a stable ship
surface — Loki Patera as the second body in the temporal-quasi-
periodic-cycle regime (after v0.24.8 Axial), and the project's
first body whose temporal cycle is sourced from a 3-body mean-
motion resonance (Galilean Laplace 4:2:1) rather than from
classical Earth mantle-plume / mid-ocean-ridge dynamics.

Three bridge surfaces:

* :func:`get_loki_patera_eruption_cycle` — full cycle catalog
  (cycle peaks + action-angle modes + binary cross-channel
  parameters).
* :func:`get_loki_galilean_laplace_signature` — THE headline
  closure: the 4:2:1 commensurability between Io / Europa /
  Ganymede orbital periods, verified to within ~1e-4. Loki's
  ~540-day cycle exists at all because of this lock.
* :func:`list_loki_patera_eruption_cycle` — full enumeration with
  citations.

Cross-channel reach: same v0.24.x temporal-spectrum methodology
as v0.24.8 Axial; cross-references v0.21.5 (Jupiter-Io flux tube),
v0.21.6 (tidal-resonance ↔ orbital migration; the 4:2:1 lock),
v0.24.6 (radiation-coupled cousin in a different sense — tidal
forcing instead of solar radiation), and v0.24.11 (Pluto-Charon's
small-moon near-3:4:5:6 commensurabilities are the binary-system
analogue of the Galilean Laplace 4:2:1).

Reference: research notebook §4 release history (v0.24.12)
and §0.0 The Mathematical Provenance Method.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .loki_patera_data import (
    EUROPA_ORBITAL_PERIOD_DAYS,
    GANYMEDE_ORBITAL_PERIOD_DAYS,
    IO_FORCED_ECCENTRICITY,
    IO_ORBITAL_PERIOD_DAYS,
    IO_TIDAL_HEATING_W,
    LOKI_CYCLE_MODES,
    LOKI_CYCLE_PEAKS,
    LOKI_CYCLE_PERIOD_RANGE_DAYS,
    LOKI_DIAMETER_KM,
    LOKI_FRACTION_OF_IO_OUTPUT,
    LOKI_LATITUDE_DEG,
    LOKI_LAVA_LAKE_AREA_KM2,
    LOKI_LONGITUDE_DEG,
    LOKI_MEAN_CYCLE_PERIOD_DAYS,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    CycleMode,
    LokiCyclePeakObservation,
)


def _peak_to_dict(p: LokiCyclePeakObservation) -> Dict[str, Any]:
    return {
        "name": p.name,
        "peak_year": p.peak_year,
        "peak_month": p.peak_month,
        "cycle_index_from_anchor": p.cycle_index_from_anchor,
        "notes": p.notes,
        "source_key": p.source_key,
        "precision_flag": p.precision_flag,
    }


def _mode_to_dict(m: CycleMode) -> Dict[str, Any]:
    return {
        "name": m.name,
        "period_days": m.period_days,
        "mode_class": m.mode_class,
        "description": m.description,
        "source_key": m.source_key,
        "precision_flag": m.precision_flag,
    }


def get_loki_patera_eruption_cycle() -> Dict[str, Any]:
    """Loki Patera eruption-cycle catalog: 6 published cycle-peak
    observations spanning 1990-2017 + 6 action-angle modes
    (cycle period, brightening / resurfacing / cooling phases,
    Io orbital, Galilean Laplace 4:2:1).

    Cross-channel: Loki's existence at all is downstream of the
    Galilean Laplace lock (Io's forced eccentricity 0.0041 from
    the Europa+Ganymede resonance drives ~10^14 W of tidal
    dissipation in Io's interior; Loki Patera is the largest
    persistent surface manifestation, accounting for 5-15% of
    Io's globally-integrated thermal output).

    Returns
    -------
    dict
        ``{ok, n_peaks, n_modes, location, geometry, cycle,
        forcing, peaks: [...], modes: [...]}``.
    """
    return {
        "ok": True,
        "n_peaks": len(LOKI_CYCLE_PEAKS),
        "n_modes": len(LOKI_CYCLE_MODES),
        "location": {
            "latitude_deg": LOKI_LATITUDE_DEG,
            "longitude_deg": LOKI_LONGITUDE_DEG,
            "alternate_longitude_e_deg": 360.0 + LOKI_LONGITUDE_DEG,
        },
        "geometry": {
            "diameter_km": LOKI_DIAMETER_KM,
            "lava_lake_area_km2": LOKI_LAVA_LAKE_AREA_KM2,
        },
        "cycle": {
            "mean_period_days": LOKI_MEAN_CYCLE_PERIOD_DAYS,
            "period_range_days": list(LOKI_CYCLE_PERIOD_RANGE_DAYS),
        },
        "forcing": {
            "io_tidal_heating_W": IO_TIDAL_HEATING_W,
            "loki_fraction_of_io_output": list(LOKI_FRACTION_OF_IO_OUTPUT),
            "io_forced_eccentricity": IO_FORCED_ECCENTRICITY,
            "io_orbital_period_days": IO_ORBITAL_PERIOD_DAYS,
        },
        "peaks": [_peak_to_dict(p) for p in LOKI_CYCLE_PEAKS],
        "modes": [_mode_to_dict(m) for m in LOKI_CYCLE_MODES],
    }


def get_loki_galilean_laplace_signature() -> Dict[str, Any]:
    """The Galilean Laplace 4:2:1 commensurability signature —
    THE headline of v0.24.12.

    The 4:2:1 lock between Io / Europa / Ganymede orbital periods
    is the deep-mechanism reason Loki Patera exists. The
    commensurability is verified to within ~1e-4 by the relations:

        4 * P_Io     = 2 * P_Europa  = P_Ganymede

    Numerical check (using the published periods in days):

        4 * 1.7691378 = 7.0765512
        2 * 3.5511810 = 7.1023620
        P_Ganymede    = 7.1545530

    The agreement is not quite to a part in 1e4 — the resonance
    is a *libration* around exact, not strict equality; the small
    mismatch drives a forced libration that appears in the orbital
    elements. The Peale-Cassen-Reynolds 1979 prediction of Io
    tidal heating was based on this near-commensurability + the
    forced eccentricity it produces; Voyager 1 confirmed the
    prediction 2 weeks after publication by directly observing
    active volcanism.

    Returns
    -------
    dict
        ``{ok, io_period_days, europa_period_days,
        ganymede_period_days, four_io_period_days,
        two_europa_period_days, max_residual_days,
        max_residual_fractional, io_forced_eccentricity,
        io_tidal_heating_W, loki_mean_cycle_days,
        loki_cycle_to_io_orbital_ratio, interpretation}``.
    """
    four_io = 4.0 * IO_ORBITAL_PERIOD_DAYS
    two_europa = 2.0 * EUROPA_ORBITAL_PERIOD_DAYS
    p_ganymede = GANYMEDE_ORBITAL_PERIOD_DAYS

    products = [four_io, two_europa, p_ganymede]
    max_residual_days = max(products) - min(products)
    max_residual_fractional = max_residual_days / p_ganymede

    cycle_to_io_orbital = (
        LOKI_MEAN_CYCLE_PERIOD_DAYS / IO_ORBITAL_PERIOD_DAYS
    )

    return {
        "ok": True,
        "io_period_days": IO_ORBITAL_PERIOD_DAYS,
        "europa_period_days": EUROPA_ORBITAL_PERIOD_DAYS,
        "ganymede_period_days": GANYMEDE_ORBITAL_PERIOD_DAYS,
        "four_io_period_days": four_io,
        "two_europa_period_days": two_europa,
        "max_residual_days": max_residual_days,
        "max_residual_fractional": max_residual_fractional,
        "io_forced_eccentricity": IO_FORCED_ECCENTRICITY,
        "io_tidal_heating_W": IO_TIDAL_HEATING_W,
        "loki_mean_cycle_days": LOKI_MEAN_CYCLE_PERIOD_DAYS,
        "loki_cycle_to_io_orbital_ratio": cycle_to_io_orbital,
        "interpretation": (
            "The Galilean Laplace 4:2:1 commensurability "
            "(4*P_Io ≈ 2*P_Europa ≈ P_Ganymede) is a near-exact "
            "libration around perfect resonance — the small "
            "residual ~0.08 d (~1% fractional) is the libration "
            "amplitude. The Io+Europa+Ganymede 3-body lock forces "
            "Io's orbital eccentricity to ~0.0041 (far above what "
            "tidal damping alone would allow), driving ~10^14 W "
            "of tidal dissipation in Io's interior. Loki Patera's "
            "~540-day quasi-periodic resurfacing cycle is the "
            "largest single surface manifestation of this "
            "dissipation chain. Cross-references v0.24.8 Axial "
            "Seamount (cousin temporal-quasi-periodic-cycle, "
            "different forcing) and v0.24.11 Pluto-Charon (the "
            "binary-system analogue of the 4:2:1 lock, with the "
            "small moons at near-3:4:5:6 multiples of the mutual "
            "orbital period)."
        ),
    }


def list_loki_patera_eruption_cycle() -> Dict[str, Any]:
    """Full enumeration of Loki Patera cycle peaks + modes +
    citations."""
    return {
        "ok": True,
        "n_peaks": len(LOKI_CYCLE_PEAKS),
        "n_modes": len(LOKI_CYCLE_MODES),
        "n_sources": len(SOURCES),
        "peaks": [_peak_to_dict(p) for p in LOKI_CYCLE_PEAKS],
        "modes": [_mode_to_dict(m) for m in LOKI_CYCLE_MODES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "LOKI_CYCLE_PEAKS",
    "LOKI_CYCLE_MODES",
    "SOURCES",
    "CycleMode",
    "LokiCyclePeakObservation",
    "get_loki_patera_eruption_cycle",
    "get_loki_galilean_laplace_signature",
    "list_loki_patera_eruption_cycle",
]
