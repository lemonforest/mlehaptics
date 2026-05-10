"""Axial Seamount Eruption Chronology dual-author diff test —
v0.27.0 phase A.

Multi-row-type catalogue (eruption / inflation_phase / forecast,
9 rows total). Mirrors prior phase A patterns; row name is unique
across all three row_types in the hand-coded module.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _axial_seamount_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("axial_seamount")
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
        out[data["name"]] = data
    return out


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("axial_seamount")
    assert result["ok"] is True
    assert len(result["rows"]) == 9, (
        f"expected 9 rows; got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    assert len(_amsc_rows_indexed_by_name()) == len(_hand_coded_rows_indexed_by_name())


def test_dual_author_row_names_agree() -> None:
    assert set(_amsc_rows_indexed_by_name()) == set(_hand_coded_rows_indexed_by_name())


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


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_name() == _hand_coded_rows_indexed_by_name()


def test_every_source_key_in_provenance_table() -> None:
    from ephemerides_spectral._research.axial_seamount_data import (
        AXIAL_ERUPTIONS,
        INFLATION_PHASES,
        CHADWICK_FORECASTS,
    )
    referenced = (
        {e.source_key for e in AXIAL_ERUPTIONS}
        | {p.source_key for p in INFLATION_PHASES}
        | {f.source_key for f in CHADWICK_FORECASTS}
    )
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str)
        assert len(entry["source_doi"]) >= 5
        assert iso_pattern.match(entry["source_published_date"])


def test_row_type_distribution() -> None:
    """The 9 rows split as: 3 eruption + 4 inflation_phase + 2
    forecast. Pin it."""
    rows = _amsc_rows_indexed_by_name()
    by_type: Dict[str, int] = {}
    for row in rows.values():
        by_type[row["row_type"]] = by_type.get(row["row_type"], 0) + 1
    assert by_type == {
        "eruption": 3,
        "inflation_phase": 4,
        "forecast": 2,
    }, f"unexpected row_type distribution: {by_type}"


def test_eruption_chronology_in_order() -> None:
    """The three confirmed Axial eruptions are 1998 / 2011 / 2015 —
    pin the chronological order via Julian date."""
    rows = _amsc_rows_indexed_by_name()
    eruptions = sorted(
        ((row["julian_date"], name)
         for name, row in rows.items() if row["row_type"] == "eruption"),
    )
    assert [name for _, name in eruptions] == [
        "axial_1998", "axial_2011", "axial_2015",
    ], f"unexpected eruption order: {[name for _, name in eruptions]}"


def test_forecast_outcomes() -> None:
    """Headline ratchet: there are exactly 2 published Chadwick-Nooner
    forecasts in this catalogue — one HIT (2015 eruption, the canonical
    methodology-validation event) and one MISS (2024-2025 window, the
    methodology's first observed missed prediction). Pin both."""
    rows = _amsc_rows_indexed_by_name()
    forecasts = {
        name: row for name, row in rows.items()
        if row["row_type"] == "forecast"
    }
    assert len(forecasts) == 2
    outcomes = {row["outcome"] for row in forecasts.values()}
    assert outcomes == {"HIT", "MISS"}, (
        f"expected {{HIT, MISS}} forecast outcomes; got {outcomes}"
    )
    hit_forecasts = [
        name for name, row in forecasts.items() if row["outcome"] == "HIT"
    ]
    assert hit_forecasts == ["forecast_2015_eruption"], (
        f"HIT forecast expected forecast_2015_eruption; got {hit_forecasts}"
    )


def test_post_2015_inflation_rate_slowed() -> None:
    """Headline physics ratchet: the post-2015 mean inflation rate
    (~20 cm/yr) is below the 2011-to-2015 reference rate (~70 cm/yr) —
    the rate-decay observation that broke the constant-rate
    extrapolation underlying the 2024-2025 forecast MISS. Pin the
    sign of the comparison."""
    rows = _amsc_rows_indexed_by_name()
    cycle_2011_2015 = rows["phase_2011_to_2015"]["mean_inflation_rate_cm_per_yr"]
    cycle_post_2015 = rows["phase_post_2015"]["mean_inflation_rate_cm_per_yr"]
    assert cycle_post_2015 < cycle_2011_2015, (
        f"post-2015 rate {cycle_post_2015} cm/yr should be below "
        f"2011-to-2015 reference {cycle_2011_2015} cm/yr"
    )


def test_inflation_phases_chronologically_chained() -> None:
    """The 4 inflation phases must form a chronological chain (each
    phase's start_year >= the previous phase's start_year). Pin the
    pre_1998 → 1998_to_2011 → 2011_to_2015 → post_2015 ordering."""
    rows = _amsc_rows_indexed_by_name()
    phases = sorted(
        ((row["start_year"], name)
         for name, row in rows.items() if row["row_type"] == "inflation_phase"),
    )
    assert [name for _, name in phases] == [
        "phase_pre_1998",
        "phase_1998_to_2011",
        "phase_2011_to_2015",
        "phase_post_2015",
    ], f"unexpected inflation-phase order: {[name for _, name in phases]}"


def test_nodoi_prefix_only_for_non_crossref_sources() -> None:
    """The post-2015 follow-up analyses are non-Crossref (conference
    proceedings + OOI Cabled Array status updates). Pin that they're
    the only `nodoi:`-prefixed source in this catalogue."""
    nodoi_keys = [
        key for key, entry in SOURCE_KEY_PROVENANCE.items()
        if entry["source_doi"].startswith("nodoi:")
    ]
    assert nodoi_keys == ["nooner_chadwick_post_2015"], (
        f"expected only nooner_chadwick_post_2015 as nodoi:; got {nodoi_keys}"
    )
