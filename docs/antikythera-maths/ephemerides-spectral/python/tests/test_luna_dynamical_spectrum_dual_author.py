"""Luna Dynamical Spectrum dual-author diff test — v0.27.0 phase A.

The same 15 Luna action-angle rows are encoded in two places:

* **AMSC path** — ``research/attested/luna_dynamical_spectrum/row.ndjson``
  consumed by the literature_curated adapter; bridge surface returns
  rows via ``get_attested_dataset("luna_dynamical_spectrum")``.
* **Hand-coded path** — ``_research/luna_dynamical_spectrum_data.py``
  (the v0.24.1 ship) — converted to AMSC shape via the helper module
  ``_luna_amsc_helpers.py``.

This test asserts the two paths agree on every row, every field.
Mirrors the Mercury (PR #303) and Saturn-rings (PR #291) patterns;
the per-catalogue helper module changes per body, the test
structure stays identical.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _luna_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("luna_dynamical_spectrum")
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
    result = bridge.get_attested_dataset("luna_dynamical_spectrum")
    assert result["ok"] is True, result
    assert isinstance(result["rows"], list)
    assert len(result["rows"]) == 15, (
        f"expected 15 rows (11 dynamical_mode + 4 saros_commensurability); "
        f"got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert len(amsc_rows) == len(hand_coded_rows), (
        f"row-count mismatch: AMSC={len(amsc_rows)}, "
        f"hand-coded={len(hand_coded_rows)}"
    )


def test_dual_author_row_names_agree() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    amsc_only = set(amsc_rows) - set(hand_coded_rows)
    hand_coded_only = set(hand_coded_rows) - set(amsc_rows)
    assert not amsc_only, f"rows in AMSC NDJSON but not hand-coded: {amsc_only}"
    assert not hand_coded_only, (
        f"rows in hand-coded module but not AMSC NDJSON: {hand_coded_only}"
    )


def test_dual_author_per_row_field_agreement() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    common_names = sorted(set(amsc_rows) & set(hand_coded_rows))
    assert common_names

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
    from ephemerides_spectral._research.luna_dynamical_spectrum_data import (
        LUNA_DYNAMICAL_MODES,
        SAROS_COMMENSURABILITY,
    )
    referenced = set()
    for mode in LUNA_DYNAMICAL_MODES:
        referenced.add(mode.source_key)
    for saros in SAROS_COMMENSURABILITY:
        referenced.add(saros.source_key)
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing, (
        f"hand-coded module references source_keys without "
        f"SOURCE_KEY_PROVENANCE entries: {sorted(missing)}. "
        f"Extend tests/_luna_amsc_helpers.py."
    )


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str), key
        assert len(entry["source_doi"]) >= 5, key
        assert iso_pattern.match(entry["source_published_date"]), (
            f"{key}: source_published_date "
            f"{entry['source_published_date']!r} doesn't match ISO 8601"
        )
        assert entry["source_version"] is None or isinstance(
            entry["source_version"], str
        ), key


def test_amsc_rows_split_evenly_between_row_types() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    by_type: Dict[str, int] = {}
    for row in amsc_rows.values():
        by_type[row["row_type"]] = by_type.get(row["row_type"], 0) + 1
    assert by_type == {
        "dynamical_mode": 11,
        "saros_commensurability": 4,
    }, f"unexpected row-type distribution: {by_type}"


def test_saros_closure_invariant_holds() -> None:
    """The four saros_commensurability rows' product_days must agree
    within 0.5 day. This is the headline closure invariant of the
    Saros cycle — 223 synodic ≈ 239 anomalistic ≈ 242 draconitic ≈
    19 eclipse-years ≈ 6585.32 days."""
    amsc_rows = _amsc_rows_indexed_by_name()
    saros_rows = [
        row for row in amsc_rows.values()
        if row["row_type"] == "saros_commensurability"
    ]
    assert len(saros_rows) == 4
    products = [row["product_days"] for row in saros_rows]
    spread = max(products) - min(products)
    assert spread < 0.5, (
        f"Saros closure invariant broken: products span {spread:.4f} d "
        f"(threshold 0.5 d). Products: {products}"
    )
