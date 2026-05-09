"""Hawaiian-Emperor Chain dual-author diff test — v0.27.0 phase A.

18 seamount rows; single row_type. Mirrors prior phase A patterns.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _hawaii_chain_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("hawaii_chain")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("hawaii_chain")
    assert result["ok"] is True
    assert len(result["rows"]) == 18, (
        f"expected 18 seamounts; got {len(result['rows'])}"
    )


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_name() == _hand_coded_rows_indexed_by_name()


def test_dual_author_per_row_field_agreement() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    common = sorted(set(amsc_rows) & set(hand_coded_rows))
    mismatches: List[str] = []
    for name in common:
        amsc = amsc_rows[name]
        hc = hand_coded_rows[name]
        for field in sorted(set(amsc) | set(hc)):
            if amsc.get(field, "<MISSING>") != hc.get(field, "<MISSING>"):
                mismatches.append(
                    f"  {name!r}.{field!r}: AMSC={amsc.get(field)!r} "
                    f"vs hand-coded={hc.get(field)!r}"
                )
    assert not mismatches, "\n".join(mismatches)


def test_every_source_key_in_provenance_table() -> None:
    from ephemerides_spectral._research.hawaii_chain_data import (
        HAWAIIAN_EMPEROR_SEAMOUNTS,
    )
    referenced = {s.source_key for s in HAWAIIAN_EMPEROR_SEAMOUNTS}
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str)
        assert len(entry["source_doi"]) >= 5
        assert iso_pattern.match(entry["source_published_date"])


def test_arc_distribution() -> None:
    """The 18 seamounts split as: 5 emperor (oldest arc), 1 bend
    (Daikakuji marker), 12 hawaiian (younger arc through Kilauea)."""
    rows = _amsc_rows_indexed_by_name()
    by_arc: Dict[str, int] = {}
    for row in rows.values():
        by_arc[row["arc"]] = by_arc.get(row["arc"], 0) + 1
    assert by_arc == {"emperor": 5, "bend": 1, "hawaiian": 12}, (
        f"unexpected arc distribution: {by_arc}"
    )


def test_meiji_oldest_kilauea_youngest() -> None:
    """Meiji is the oldest dated seamount in the chain (~85 Myr);
    Kilauea is the active end (age 0)."""
    rows = _amsc_rows_indexed_by_name()
    ages = sorted(((row["age_myr"], name) for name, row in rows.items()))
    assert ages[0][1] == "hawaii_kilauea", (
        f"youngest expected hawaii_kilauea; got {ages[0][1]!r}"
    )
    assert ages[-1][1] == "meiji", (
        f"oldest expected meiji; got {ages[-1][1]!r}"
    )


def test_bend_age_consistency() -> None:
    """The Hawaiian-Emperor bend marker (Daikakuji) age must lie
    within the canonical 47.5 ± 1.0 Myr window per Sharp & Clague
    2006."""
    rows = _amsc_rows_indexed_by_name()
    daikakuji = rows["daikakuji"]
    assert daikakuji["arc"] == "bend"
    age = daikakuji["age_myr"]
    assert 46.0 <= age <= 49.0, (
        f"daikakuji age {age} outside 47.5 ± 1.5 Myr canonical window"
    )
