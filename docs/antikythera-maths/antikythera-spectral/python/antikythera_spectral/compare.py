"""DE-kernel comparator + Greek-model comparator.

Two comparators:

- ``compare_ephemerides_at_jd``: load two JPL kernels (e.g. DE441 vs
  DE422), query both for the same body's barycentric position at the
  same JD, return the delta in arcseconds, kilometers, AU.
- ``compare_models_at_jd``: uniform vs Hipparchus epicycle vs Ptolemy
  equant residuals against ephemeris truth.

Skyfield required.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional


_BODY_NAMES = {
    "mercury": "mercury",
    "venus":   "venus",
    "mars":    "mars",
    "jupiter": "jupiter barycenter",
    "saturn":  "saturn barycenter",
    "sun":     "sun",
    "moon":    "moon",
}


def compare_ephemerides_at_jd(jd_tdb: float, body: str,
                               kernel_a: str, kernel_b: str) -> Optional[Dict[str, float]]:
    """Position delta between two kernels for the same body/JD."""
    if body.lower() not in _BODY_NAMES:
        return None
    try:
        from antikythera_spectral._research.ephemeris_loader import load_ephemeris
    except ImportError:
        return None
    bundle_a = load_ephemeris(kernel_a)
    bundle_b = load_ephemeris(kernel_b)
    if bundle_a is None or bundle_b is None:
        return None

    target_name = _BODY_NAMES[body.lower()]

    def _vec(bundle):
        ts = bundle.ts
        eph = bundle.eph
        earth = eph["earth"]
        target = eph[target_name]
        t = ts.tdb_jd(jd_tdb)
        astrometric = earth.at(t).observe(target)
        return astrometric

    a = _vec(bundle_a)
    b = _vec(bundle_b)
    sep = a.separation_from(b)
    # Distance delta (km).
    pos_a_au = a.position.au
    pos_b_au = b.position.au
    dx = (pos_a_au[0] - pos_b_au[0]) ** 2
    dy = (pos_a_au[1] - pos_b_au[1]) ** 2
    dz = (pos_a_au[2] - pos_b_au[2]) ** 2
    dist_au = math.sqrt(dx + dy + dz)
    # 1 AU ≈ 149_597_870.7 km
    return {
        "delta_arcsec": float(sep.arcseconds()),
        "delta_au": float(dist_au),
        "delta_km": float(dist_au * 149_597_870.7),
    }


_VALID_MODEL_NAMES = ("uniform", "epicycle", "equant", "bronze")
"""Public model name aliases accepted by compare_models_at_jd.  Note
'epicycle' here aliases to mars_longitude_epicycle_only in the
research module; 'bronze' is the algebra/eigenbasis-projected
companion (see ADR 0012)."""


def compare_models_at_jd(jd_tdb: float, body: str,
                          model_a: str, model_b: str,
                          kernel: str = "de421",
                          params: str = "ptolemy") -> Optional[Dict[str, Any]]:
    """Per-Greek-model longitude-error comparison against ephemeris truth.

    Parameters
    ----------
    jd_tdb : float
        Julian Date (TDB) at which to query both models and the
        ephemeris truth.
    body : str
        Currently supports ``"mars"`` only (the only body with all
        Greek models implemented in research.equant_encoder).
    model_a, model_b : str
        Choices: ``"uniform" | "epicycle" | "equant" | "bronze"``.  See
        ``antikythera_spectral.mars_models`` for the model semantics.
        ``"bronze"`` is the algebra/eigenbasis projection of the
        gear-ratio cyclic-group representation; numerically agrees with
        ``"epicycle"`` to ~1e-13 deg (different derivation pathway,
        same transform — see ADR 0012).
    kernel : str
        JPL DE-kernel name (default ``"de421"``).
    params : str
        Mars param-set name; one of ``"ptolemy"`` (Almagest IX-X
        canonical, e=6, equant_offset=12), ``"freeth_2012"`` (F&J 2012
        bare deferent + epicycle, e=0, no equant), or ``"freeth_2021"``
        (Freeth 2021 reconstruction, same kinematic class as 2012).
        Default ``"ptolemy"`` keeps the v0.2.x behaviour.

    Returns
    -------
    dict or None
        ``None`` if body unsupported, model name unknown, params
        unknown, or skyfield/kernel unavailable.  Otherwise a dict
        with model_a / model_b longitudes, residuals vs truth, and
        their pairwise difference.
    """
    if body.lower() != "mars":
        return None
    if model_a not in _VALID_MODEL_NAMES or model_b not in _VALID_MODEL_NAMES:
        return None
    try:
        from antikythera_spectral import mars_models
    except ImportError:
        return None
    try:
        from antikythera_spectral._research import equant_encoder as eq
    except ImportError:
        return None
    try:
        from antikythera_spectral._research.ephemeris_loader import load_ephemeris
    except ImportError:
        return None

    try:
        param_obj = mars_models.get_params(params)
    except ValueError:
        return None

    bundle = load_ephemeris(kernel)
    if bundle is None:
        return None

    # Ground-truth longitude
    eph = bundle.eph
    ts = bundle.ts
    earth = eph["earth"]
    mars = eph["mars"]
    t = ts.tdb_jd(jd_tdb)
    astrometric = earth.at(t).observe(mars).apparent()
    truth_lon = float(astrometric.ecliptic_latlon()[1].degrees)

    def _model_lon(name):
        if name == "uniform":
            return float(eq.mars_longitude_uniform(jd_tdb, param_obj))
        if name == "epicycle":
            return float(eq.mars_longitude_epicycle_only(jd_tdb, param_obj))
        if name == "equant":
            return float(eq.mars_longitude_equant(jd_tdb, param_obj))
        if name == "bronze":
            return float(eq.mars_longitude_bronze(jd_tdb, param_obj))
        return None

    lon_a = _model_lon(model_a)
    lon_b = _model_lon(model_b)
    if lon_a is None or lon_b is None:
        return None

    def _wrap_180(x):
        return ((x + 180.0) % 360.0) - 180.0

    return {
        "model_a": model_a,
        "model_b": model_b,
        "params": params,
        "truth_lon_deg": truth_lon,
        "model_a_lon_deg": lon_a,
        "model_b_lon_deg": lon_b,
        "model_a_residual_deg": _wrap_180(lon_a - truth_lon),
        "model_b_residual_deg": _wrap_180(lon_b - truth_lon),
        "ab_difference_deg": _wrap_180(lon_a - lon_b),
    }


def compare_reconstructions_at_jd(jd_tdb: float,
                                    dials: str = "all") -> Dict[str, Any]:
    """Side-by-side dial readings across Freeth/Wright/Price reconstructions.

    Currently the encoder uses Freeth 2021 tooth counts; cross-
    reconstruction comparison only changes when reconstructions
    disagree on a tooth count. We report the disagreements, with each
    reconstruction's tooth-count expressed as a per-dial ratio impact.
    """
    from antikythera_spectral._research.gear_database import (
        ALL_GEARS, FREETH_2021, WRIGHT, PRICE_1974,
    )
    disagreements = []
    for g in ALL_GEARS:
        teeth = g.teeth
        counts = sorted(set(teeth.values()))
        if len(counts) > 1:
            disagreements.append({
                "gear": g.name,
                "role": g.role,
                "freeth_2021": teeth.get(FREETH_2021),
                "wright":      teeth.get(WRIGHT),
                "price_1974":  teeth.get(PRICE_1974),
            })
    return {
        "jd_tdb": float(jd_tdb),
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
    }


__all__ = [
    "compare_ephemerides_at_jd",
    "compare_models_at_jd",
    "compare_reconstructions_at_jd",
]
