"""Emit ``_data/visibility_anchors.json`` — per-planet algebraic anchors.

The values are curated (computed once at v0.2.0 design time via skyfield
+ DE421 forward-search from J2000); we re-emit them byte-identically on
each codegen run so the manifest's SHA-256 stays stable.

This is a curated emitter, distinct from the SSOT-derived emitters
(emit_cycles.py reads research.astronomical_cycles, etc.). The anchors
here aren't derivable from the research scaffold's pure-Python data;
they require skyfield. Re-deriving with a different kernel or epoch
should produce equivalent results to within ~1 day; do that
intentionally if you bump v0.3.0.

Run::

    python codegen/emit_visibility_anchors.py
"""

from __future__ import annotations

import json
from pathlib import Path

from _paths import DATA_DIR


# Curated anchors. Computed once via:
#
#   from antikythera_spectral.visibility import (
#       SUPPORTED_PLANETS, get_next_heliacal_rising,
#   )
#   for p in SUPPORTED_PLANETS:
#       print(p, get_next_heliacal_rising(2451545.0, p, kernel="de421"))
#
# Re-running the above should reproduce these JDs to within 1 day for
# any kernel that covers J2000.
_ANCHORS = {
    "schema_version": 1,
    "doc": (
        "Per-planet anchors for self-contained algebraic visibility / "
        "heliacal-rising mode (precise=False default in v0.2.0). Each "
        "planet has one observed heliacal-rising JD (computed once via "
        "skyfield + DE421 near J2000) plus a synodic period; algebraic "
        "propagation gives any other event as anchor + n*synodic, "
        "accurate to within ~1 day at Hellenistic-era epochs (limited "
        "by ΔT, not by approximation error). For sub-arcsec precision, "
        "install with [ephemeris] and pass precise=True. ADR 0011 "
        "documents the algebraic-default discipline."
    ),
    "planets": {
        "mercury": {
            "synodic_period_days": 115.8775,
            "heliacal_rising_anchor_jd": 2451587.9489,
            "heliacal_threshold_deg": 18.0,
            "max_solar_elongation_deg": 27.8,
            "is_inferior": True,
            "visibility_fraction_per_cycle": 0.40,
            "anchor_provenance": (
                "computed via skyfield + DE421 near J2000 "
                "(linear search forward from JD 2451545.0)"
            ),
        },
        "venus": {
            "synodic_period_days": 583.9214,
            "heliacal_rising_anchor_jd": 2451732.1571,
            "heliacal_threshold_deg": 7.0,
            "max_solar_elongation_deg": 47.0,
            "is_inferior": True,
            "visibility_fraction_per_cycle": 0.95,
            "anchor_provenance": "computed via skyfield + DE421 near J2000",
        },
        "mars": {
            "synodic_period_days": 779.9361,
            "heliacal_rising_anchor_jd": 2451769.8441,
            "heliacal_threshold_deg": 13.0,
            "max_solar_elongation_deg": 180.0,
            "is_inferior": False,
            "visibility_fraction_per_cycle": 0.95,
            "anchor_provenance": "computed via skyfield + DE421 near J2000",
        },
        "jupiter": {
            "synodic_period_days": 398.8840,
            "heliacal_rising_anchor_jd": 2451687.7617,
            "heliacal_threshold_deg": 11.0,
            "max_solar_elongation_deg": 180.0,
            "is_inferior": False,
            "visibility_fraction_per_cycle": 0.93,
            "anchor_provenance": "computed via skyfield + DE421 near J2000",
        },
        "saturn": {
            "synodic_period_days": 378.0917,
            "heliacal_rising_anchor_jd": 2451690.7173,
            "heliacal_threshold_deg": 13.0,
            "max_solar_elongation_deg": 180.0,
            "is_inferior": False,
            "visibility_fraction_per_cycle": 0.93,
            "anchor_provenance": "computed via skyfield + DE421 near J2000",
        },
    },
}


def emit() -> Path:
    out_path = DATA_DIR / "visibility_anchors.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(
        (json.dumps(_ANCHORS, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return out_path


if __name__ == "__main__":
    p = emit()
    print(f"wrote {p} ({p.stat().st_size} bytes; "
           f"{len(_ANCHORS['planets'])} planets)")
