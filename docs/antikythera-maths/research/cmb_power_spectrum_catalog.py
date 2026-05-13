"""CMB Power Spectrum Catalog — query surface for the cosmology-instrument
v0.X.0 ship (Planck 2018 PR3 binned TT power spectrum; the canonical
spherical-harmonic spectral observable at cosmological scale).

AMSC-first ship: data lives only in the attested NDJSON
(`_research/attested/cmb_power_spectrum/row.ndjson`); this catalog module
reads from the NDJSON at module load via the AMSC machinery. No separate
`_data.py` since the catalog was AMSC-first (vs. v0.24.x catalogs that
backfill an existing `_data.py` into attested NDJSON).

Bridge surfaces:

* :func:`get_cmb_power_at_ell` — D_ℓ at the multipole bin containing a
  given ℓ (raw or in the ΛCDM context of acoustic-peak / damping-tail
  position).
* :func:`get_cmb_first_acoustic_peak` — THE headline observable: peak
  D_ℓ ≈ 5800 μK² at ℓ ≈ 220. One of the most-cited numerical results
  in cosmology; constrains spatial flatness + baryon density.
* :func:`list_cmb_power_spectrum` — full enumeration of all 111 binned
  bands with per-band feature classification + citations.

MFO connection: this is the IR end of the d_S(σ) flow predicted by
notebook §V (spectral dimension flow). CMB analyses give effective
d_H ≈ 4 at Mpc scales, consistent with the framework's IR limit.

Reference: research notebook §V.5 (Observational constraints) and
Part VII (Cosmological reframings).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from .attested_collector_catalog import get_attested_dataset


CATALOG_KEY = "cmb_power_spectrum"
CANONICAL_REFERENCE_DOI = "10.1051/0004-6361/201833910"
CANONICAL_REFERENCE_LABEL = (
    "Planck Collaboration 2018 VI: Aghanim et al. 2020, A&A 641:A6"
)


@lru_cache(maxsize=1)
def _rows() -> List[Dict[str, Any]]:
    """All 111 binned multipole rows from Planck 2018 PR3 TT."""
    result = get_attested_dataset(CATALOG_KEY, limit=None)
    return [r["data"] for r in result["rows"]]


def get_cmb_power_at_ell(ell: int) -> Dict[str, Any]:
    """Return the binned-band entry whose multipole window contains ``ell``.

    Each Planck PR3 band has a center ``ell_center`` and ``ell_half_width``;
    a given ℓ falls into the band whose window
    [ell_center − half_width, ell_center + half_width] covers it. Low-ℓ
    bands (ℓ ≤ 29) use half_width = 0 (unbinned commander likelihood).

    Returns ``{"ok": True, "row": ..., "feature": ..., "D_ell_muK2": ...}``
    for the matching band; ``{"ok": False, "reason": ...}`` if ``ell`` is
    outside the PR3 coverage [2, 2508] or falls in a gap between bands.
    """
    if not isinstance(ell, int):
        return {"ok": False, "reason": f"ell must be int, got {type(ell).__name__}"}
    if ell < 2:
        return {"ok": False, "reason": "ell must be >= 2 (monopole + dipole not measured)"}

    for row in _rows():
        center = row["ell_center"]
        half = row["ell_half_width"]
        lo = center - half
        hi = center + half
        if lo <= ell <= hi:
            return {
                "ok": True,
                "ell_query": ell,
                "ell_bin_label": row["ell_bin_label"],
                "ell_center": center,
                "ell_half_width": half,
                "D_ell_muK2": row["D_ell_muK2"],
                "D_ell_error_muK2": row["D_ell_error_muK2"],
                "spectrum_kind": row["spectrum_kind"],
                "feature": row["feature"],
                "precision_flag": row["precision_flag"],
                "source_doi": row["source_doi"],
            }
    return {
        "ok": False,
        "reason": f"ell={ell} not covered by PR3 bands (low-ℓ unbinned 2..29; high-ℓ binned ~47..2499)",
    }


def get_cmb_first_acoustic_peak() -> Dict[str, Any]:
    """Return the binned band closest to the first acoustic peak (ℓ ≈ 220).

    The first acoustic peak is the canonical CMB observable; peak position
    constrains spatial flatness of the universe, peak height constrains
    baryon density Ω_b h². D_ℓ ≈ 5800 μK² is one of the most-cited
    numerical results in cosmology.
    """
    peak_rows = [r for r in _rows() if r["feature"] == "first_acoustic_peak"]
    if not peak_rows:
        return {"ok": False, "reason": "no first_acoustic_peak feature in catalog"}
    peak = max(peak_rows, key=lambda r: r["D_ell_muK2"])
    return {
        "ok": True,
        "ell_center": peak["ell_center"],
        "ell_half_width": peak["ell_half_width"],
        "D_ell_muK2": peak["D_ell_muK2"],
        "D_ell_error_muK2": peak["D_ell_error_muK2"],
        "feature": "first_acoustic_peak",
        "ell_bin_label": peak["ell_bin_label"],
        "notes": peak.get("notes"),
        "source_doi": peak["source_doi"],
        "source_label": CANONICAL_REFERENCE_LABEL,
    }


def list_cmb_power_spectrum() -> Dict[str, Any]:
    """Full enumeration of all 111 Planck PR3 binned TT bands.

    Returns a dict with ``n_bands``, ``ell_range``, per-feature counts, and
    the full row list. Each row is the raw MPR ``data`` block.
    """
    rows = _rows()
    if not rows:
        return {"ok": False, "reason": "catalog empty"}

    ells = [r["ell_center"] for r in rows]
    feature_counts: Dict[str, int] = {}
    for r in rows:
        feature_counts[r["feature"]] = feature_counts.get(r["feature"], 0) + 1

    return {
        "ok": True,
        "catalog_key": CATALOG_KEY,
        "canonical_reference_doi": CANONICAL_REFERENCE_DOI,
        "canonical_reference_label": CANONICAL_REFERENCE_LABEL,
        "n_bands": len(rows),
        "ell_range": [min(ells), max(ells)],
        "spectrum_kinds": sorted({r["spectrum_kind"] for r in rows}),
        "feature_counts": feature_counts,
        "rows": rows,
    }
