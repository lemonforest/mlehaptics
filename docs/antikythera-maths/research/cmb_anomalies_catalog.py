"""CMB Anomalies Catalog — query surface for the cosmology-instrument
v0.X.0+1 ship (six canonical large-scale CMB anomalies; companion to
cmb_power_spectrum).

AMSC-first ship: data lives only in the attested NDJSON
(`_research/attested/cmb_anomalies/row.ndjson`); this catalog module
reads from the NDJSON at module load via the AMSC machinery.

Bridge surfaces:

* :func:`get_cmb_anomaly` — single anomaly by stable id.
* :func:`list_cmb_anomalies` — full enumeration of all 6 canonical
  anomalies + summary statistics by anomaly_kind.

Where cmb_power_spectrum indexes the CMB by multipole bin (assumes
statistical isotropy), this catalog indexes it by structural anomaly
(deviations from isotropy + Gaussianity at typically 2σ-3σ levels).

This is DATA, not interpretation. Theoretical interpretations of
specific anomalies (bubble-collision, EM-medium-pressure, axion /
cosmic-string explanations) are research-scope and not part of the
catalog.

Reference: research notebook §V.5 (Observational constraints).
Companion to :mod:`cmb_power_spectrum_catalog`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from srmech.amsc.catalog import get_attested_dataset


CATALOG_KEY = "cmb_anomalies"
CANONICAL_REFERENCE_DOI = "10.1051/0004-6361/201833881"
CANONICAL_REFERENCE_LABEL = (
    "Planck Collaboration 2018 VII: Akrami et al. 2020, A&A 641:A7"
)


@lru_cache(maxsize=1)
def _rows() -> List[Dict[str, Any]]:
    """All 6 canonical anomaly rows."""
    result = get_attested_dataset(CATALOG_KEY, limit=None)
    return [r["data"] for r in result["rows"]]


def get_cmb_anomaly(anomaly_id: str) -> Dict[str, Any]:
    """Return the single anomaly with the given stable id.

    Known anomaly_ids:

    - ``axis-of-evil-l2-l3-alignment`` — Quadrupole-octupole alignment.
    - ``cold-spot`` — Vielva et al. 2004 localized cold region.
    - ``hemispherical-power-asymmetry`` — Eriksen et al. 2004 dipolar
      modulation.
    - ``low-quadrupole`` — Observed C₂ deficit vs. ΛCDM.
    - ``parity-asymmetry-low-ell`` — Land & Magueijo 2005 odd-vs-even.
    - ``missing-large-angle-correlation`` — S 1/2 anomaly; suppressed
      two-point correlation at θ > 60°.

    Returns ``{"ok": True, ...full row...}`` or ``{"ok": False, "reason": ...}``.
    """
    if not isinstance(anomaly_id, str):
        return {"ok": False, "reason": f"anomaly_id must be str, got {type(anomaly_id).__name__}"}

    for row in _rows():
        if row["anomaly_id"] == anomaly_id:
            return {"ok": True, **row}

    known = sorted(r["anomaly_id"] for r in _rows())
    return {
        "ok": False,
        "reason": f"unknown anomaly_id '{anomaly_id}'; known ids: {known}",
    }


def list_cmb_anomalies() -> Dict[str, Any]:
    """Full enumeration of all 6 canonical CMB anomalies.

    Returns a dict with ``n_anomalies``, per-kind counts, and the full
    row list. Each row is the raw MPR ``data`` block.
    """
    rows = _rows()
    if not rows:
        return {"ok": False, "reason": "catalog empty"}

    kind_counts: Dict[str, int] = {}
    for r in rows:
        kind_counts[r["anomaly_kind"]] = kind_counts.get(r["anomaly_kind"], 0) + 1

    return {
        "ok": True,
        "catalog_key": CATALOG_KEY,
        "canonical_reference_doi": CANONICAL_REFERENCE_DOI,
        "canonical_reference_label": CANONICAL_REFERENCE_LABEL,
        "n_anomalies": len(rows),
        "anomaly_kind_counts": kind_counts,
        "anomaly_ids": sorted(r["anomaly_id"] for r in rows),
        "rows": rows,
    }
