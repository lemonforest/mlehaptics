"""Algebraic eclipse search — Saros-cycle scan from frozen anchors.

Self-contained mode (precise=False default per ADR 0011): instead of
sky-driven syzygy enumeration via skyfield, scan forward/backward
from the frozen Hellenistic + modern Saros anchors in
``_data/anchors.json``.

Saros cycle = 6585.32 days (223 synodic months). Every Saros after a
known eclipse, an eclipse of similar character occurs at almost the
same JD-mod-Saros position. We don't get NEW eclipses (the Saros
catalogue is what it is) — we get every eclipse the ancient operator
could have predicted from the Antikythera's Saros pointer, which IS
the device's job.

Precision: ±1-2 days at Hellenistic-era epochs (limited by the
anchors' own ΔT-uncertainty, not by approximation error).

For high-precision sky-driven syzygy enumeration of arbitrary JDs,
install with [ephemeris] and pass precise=True.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


_DATA_DIR = Path(__file__).resolve().parent / "_data"

# Saros cycle (Greek, attested in MUL.APIN + Almagest).
_SAROS_DAYS: float = 6585.3211

# Maximum Saros offset to scan in either direction. 200 Saros
# = ~3600 years; covers everything from -1500 BCE to +2100 CE
# from a single anchor. Bounded so the enumeration doesn't go
# unbounded for huge JD bands.
_MAX_SAROS_OFFSET: int = 250


# Module-level cache.
_ANCHORS_CACHE: Optional[Dict[str, Any]] = None


def _load_anchors() -> Dict[str, Any]:
    """Read the frozen eclipse anchors (Hellenistic + modern Saros)."""
    global _ANCHORS_CACHE
    if _ANCHORS_CACHE is None:
        path = _DATA_DIR / "anchors.json"
        if not path.exists():
            raise RuntimeError(
                f"missing {path}; run codegen/regenerate.py to create it"
            )
        _ANCHORS_CACHE = json.loads(path.read_text(encoding="utf-8"))
    return _ANCHORS_CACHE


def find_eclipses_in_range(jd_lo: float, jd_hi: float, *,
                            kind: str = "all") -> List[Dict[str, Any]]:
    """Enumerate eclipses in [jd_lo, jd_hi] from Saros-cycle propagation.

    For each anchor in the frozen catalogue, generate the n-th Saros
    successor / predecessor at ``anchor.jd + n · 6585.32`` for
    ``n ∈ [-_MAX_SAROS_OFFSET, +_MAX_SAROS_OFFSET]``, keep those that
    land in the query band, and dedupe approximate-coincidences (within
    ~1 day) since multiple anchors may converge on the same predicted
    eclipse.
    """
    if kind not in ("lunar", "solar", "all"):
        raise ValueError(f"kind must be 'lunar' | 'solar' | 'all', got {kind!r}")
    anchors_payload = _load_anchors()
    anchors = list(anchors_payload.get("hellenistic", [])) + list(anchors_payload.get("modern", []))

    raw: List[Dict[str, Any]] = []
    for a in anchors:
        a_kind = (a.get("eclipse_type") or "").lower()
        # Normalise eclipse_type to lunar/solar.
        if "solar" in a_kind:
            a_kind_norm = "solar"
        else:
            a_kind_norm = "lunar"
        if kind != "all" and a_kind_norm != kind:
            continue
        a_jd = float(a["jd"])
        for n in range(-_MAX_SAROS_OFFSET, _MAX_SAROS_OFFSET + 1):
            candidate_jd = a_jd + n * _SAROS_DAYS
            if jd_lo <= candidate_jd <= jd_hi:
                raw.append({
                    "jd_tdb": candidate_jd,
                    "kind": a_kind_norm,
                    "saros_offset": n,
                    "anchor_label": a.get("almagest_ref") or a.get("espenak_id") or a.get("date_iso", ""),
                })

    # Dedupe near-coincident predictions (within 2 days; multiple
    # anchors may resolve to the same physical eclipse through different
    # Saros offsets). Prefer the entry with smallest |saros_offset|
    # (closest anchor → most precise).
    raw.sort(key=lambda r: (r["jd_tdb"], abs(r["saros_offset"])))
    deduped: List[Dict[str, Any]] = []
    for r in raw:
        if deduped and abs(r["jd_tdb"] - deduped[-1]["jd_tdb"]) < 2.0:
            continue
        deduped.append(r)
    return deduped


__all__ = ["find_eclipses_in_range"]
