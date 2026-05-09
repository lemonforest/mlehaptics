"""Mars Dynamical Spectrum dual-author diff test — v0.27.0 phase A.

11 Mars action-angle rows encoded in two places:

* **AMSC path** — ``research/attested/mars_dynamical_spectrum/row.ndjson``
* **Hand-coded path** — ``_research/mars_dynamical_spectrum_data.py``
  (the v0.24.2 ship) converted via ``_mars_amsc_helpers.py``.

Mirrors PR #303 (Mercury) and PR #306 (Luna).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _mars_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("mars_dynamical_spectrum")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        name = data["name"]
        assert name not in out, f"duplicate AMSC row: {name!r}"
        out[name] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for data in hand_coded_rows_in_amsc_shape():
        name = data["name"]
        assert name not in out, f"duplicate hand-coded row: {name!r}"
        out[name] = data
    return out


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("mars_dynamical_spectrum")
    assert result["ok"] is True, result
    assert len(result["rows"]) == 11, (
        f"expected 11 rows (8 dynamical_mode + 3 secular_resonance); "
        f"got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert len(amsc_rows) == len(hand_coded_rows)


def test_dual_author_row_names_agree() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    amsc_only = set(amsc_rows) - set(hand_coded_rows)
    hand_coded_only = set(hand_coded_rows) - set(amsc_rows)
    assert not amsc_only, f"AMSC-only: {amsc_only}"
    assert not hand_coded_only, f"hand-coded-only: {hand_coded_only}"


def test_dual_author_per_row_field_agreement() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    common_names = sorted(set(amsc_rows) & set(hand_coded_rows))
    mismatches: List[str] = []
    for name in common_names:
        amsc = amsc_rows[name]
        hc = hand_coded_rows[name]
        all_fields = sorted(set(amsc) | set(hc))
        for field in all_fields:
            amsc_val = amsc.get(field, "<MISSING>")
            hc_val = hc.get(field, "<MISSING>")
            if amsc_val != hc_val:
                mismatches.append(
                    f"  row {name!r}, field {field!r}: "
                    f"AMSC={amsc_val!r} vs hand-coded={hc_val!r}"
                )
    assert not mismatches, (
        f"dual-author divergence — {len(mismatches)} mismatch(es):\n"
        + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert amsc_rows == hand_coded_rows


def test_every_source_key_in_provenance_table() -> None:
    from ephemerides_spectral._research.mars_dynamical_spectrum_data import (
        MARS_DYNAMICAL_MODES,
        MARS_SECULAR_RESONANCES,
    )
    referenced = set()
    for mode in MARS_DYNAMICAL_MODES:
        referenced.add(mode.source_key)
    for res in MARS_SECULAR_RESONANCES:
        referenced.add(res.source_key)
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing, (
        f"hand-coded module references source_keys without "
        f"SOURCE_KEY_PROVENANCE entries: {sorted(missing)}"
    )


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str), key
        assert len(entry["source_doi"]) >= 5, key
        assert iso_pattern.match(entry["source_published_date"]), (
            f"{key}: source_published_date doesn't match ISO 8601"
        )
        assert entry["source_version"] is None or isinstance(
            entry["source_version"], str
        ), key


def test_amsc_rows_split_by_row_type() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    by_type: Dict[str, int] = {}
    for row in amsc_rows.values():
        by_type[row["row_type"]] = by_type.get(row["row_type"], 0) + 1
    assert by_type == {
        "dynamical_mode": 8,
        "secular_resonance": 3,
    }, f"unexpected row-type distribution: {by_type}"


def test_secular_resonance_rows_carry_proximity() -> None:
    """Every secular_resonance row must have a non-null
    proximity_arcsec_per_year (it's the headline quantity that
    measures how close the Mars-mode and secular-partner
    frequencies are; null would defeat the row's purpose)."""
    amsc_rows = _amsc_rows_indexed_by_name()
    res_rows = [
        row for row in amsc_rows.values()
        if row["row_type"] == "secular_resonance"
    ]
    assert len(res_rows) == 3
    for row in res_rows:
        assert row["proximity_arcsec_per_year"] is not None, (
            f"secular_resonance row {row['name']!r} missing proximity"
        )
        assert row["proximity_arcsec_per_year"] >= 0.0, (
            f"row {row['name']!r}: proximity must be non-negative"
        )
