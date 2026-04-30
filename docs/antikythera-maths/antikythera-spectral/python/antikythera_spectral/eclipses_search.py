"""Sky-driven eclipse enumeration over JD bands.

Wraps ``_research.sky_driven_validation`` for the bridge. A "sky-driven"
search scans the JD band sample-by-sample looking for new-moon (solar
eclipse candidate) or full-moon (lunar eclipse candidate) configurations
where the moon's ecliptic latitude is small enough for actual eclipse
geometry.

Skyfield is required; returns None if unavailable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def find_eclipses_in_range(jd_lo: float, jd_hi: float, kind: str = "all",
                            kernel: str = "de421") -> Optional[List[Dict[str, Any]]]:
    """Enumerate eclipses (lunar | solar | all) in [jd_lo, jd_hi].

    Returns
    -------
    list of dicts or None
        Each dict has::

            {
                "jd_tdb": float,        # peak time
                "kind": "lunar" | "solar",
                "moon_lat_deg": float,   # ecliptic latitude (small = eclipse)
                "phase": float,          # 0=new, 0.5=full
            }

        ``None`` if skyfield/kernel unavailable.
    """
    if kind not in ("lunar", "solar", "all"):
        return None
    try:
        from antikythera_spectral._research import sky_driven_validation as sdv
    except ImportError:
        return None
    try:
        from antikythera_spectral._research.ephemeris_loader import load_ephemeris
    except ImportError:
        return None

    bundle = load_ephemeris(kernel)
    if bundle is None:
        return None

    # Use the research module's primitive: find_syzygies returns
    # (jd, kind, moon_lat) per syzygy. We re-shape into bridge JSON.
    if not hasattr(sdv, "find_syzygies"):
        return None

    raw = sdv.find_syzygies(bundle, jd_lo, jd_hi)
    out: List[Dict[str, Any]] = []
    for entry in raw:
        # `entry` is expected to be a dict-like or tuple. Tolerate both.
        if isinstance(entry, dict):
            ejd = entry.get("jd")
            ekind = entry.get("kind")
            elat = entry.get("moon_lat_deg")
            ephase = entry.get("phase", 0.0)
        else:
            ejd, ekind, elat = entry[0], entry[1], entry[2]
            ephase = entry[3] if len(entry) > 3 else 0.0
        if kind != "all" and ekind != kind:
            continue
        out.append({
            "jd_tdb": float(ejd),
            "kind": ekind,
            "moon_lat_deg": float(elat),
            "phase": float(ephase),
        })
    return out


__all__ = ["find_eclipses_in_range"]
