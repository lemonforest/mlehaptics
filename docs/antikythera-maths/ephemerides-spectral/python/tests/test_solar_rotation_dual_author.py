"""Solar-rotation dual-author diff test (v0.30.0rc4).

The same 4 rotation-anchor rows are encoded in two places:

* **AMSC path** — ``research/attested/solar_rotation/rotation_anchor.ndjson``
  consumed by the literature_curated adapter; surfaced via
  ``bridge.get_attested_dataset("solar_rotation")``.
* **Hand-coded path** — ``_research/solar_rotation_data.py``'s
  ``ROTATION_ANCHORS`` list (frozen @dataclass + List + SOURCES dict),
  the rc2 Sol Solar Rotation catalogue's data source.

The two paths must agree on every row, every field. Divergence is the
data: a schema too thin to express the @dataclass, or one path edited
without the other. This is the second dual-author exercise after
saturn_rings (the v0.27.x backfill-review evidence base).

The per-row source DOIs + dates were triality-attested
(haiku/sonnet/opus vs ADS/IOPscience/arXiv) before being committed;
the dates are written at the granularity all three tiers externally
confirmed (month for Snodgrass-Ulrich, year for Schou).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge
from ephemerides_spectral._research.solar_rotation_data import (
    ROTATION_ANCHORS,
    anchor_to_data_dict,
)


def _amsc_rows_indexed_by_region() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("solar_rotation")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        region = data["region"]
        assert region not in out, f"duplicate AMSC row: {region!r}"
        out[region] = data
    return out


def _hand_coded_rows_indexed_by_region() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for anchor in ROTATION_ANCHORS:
        data = anchor_to_data_dict(anchor)
        region = data["region"]
        assert region not in out, f"duplicate hand-coded row: {region!r}"
        out[region] = data
    return out


def test_dual_author_row_count_agrees() -> None:
    amsc = _amsc_rows_indexed_by_region()
    hand = _hand_coded_rows_indexed_by_region()
    assert len(amsc) == len(hand) == 4, (
        f"row-count mismatch: AMSC={len(amsc)}, hand-coded={len(hand)}; "
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_region_names_agree() -> None:
    amsc = _amsc_rows_indexed_by_region()
    hand = _hand_coded_rows_indexed_by_region()
    assert set(amsc) == set(hand), (
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_per_row_field_agreement() -> None:
    amsc = _amsc_rows_indexed_by_region()
    hand = _hand_coded_rows_indexed_by_region()
    mismatches: List[str] = []
    for region in sorted(set(amsc) & set(hand)):
        a, h = amsc[region], hand[region]
        for field in sorted(set(a) | set(h)):
            av, hv = a.get(field, "<MISSING>"), h.get(field, "<MISSING>")
            if av != hv:
                mismatches.append(
                    f"  row {region!r}, field {field!r}: "
                    f"AMSC={av!r} vs hand-coded={hv!r}"
                )
    assert not mismatches, (
        "dual-author divergence:\n" + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_region() == _hand_coded_rows_indexed_by_region()


def test_every_amsc_row_carries_attested_source_doi() -> None:
    """Per-row attestation discipline: every row has a non-empty
    source_doi (the literature_curated descriptor requires it)."""
    amsc = _amsc_rows_indexed_by_region()
    for region, data in amsc.items():
        assert data.get("source_doi"), f"{region!r} missing source_doi"
        assert len(data["source_doi"]) >= 5, f"{region!r} source_doi too short"
