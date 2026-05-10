"""Mars Tharsis Volcanic Chain dual-author diff test — v0.27.0 phase A.

5-volcano roster; single row_type. Mirrors prior phase A patterns.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _mars_tharsis_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("mars_tharsis")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("mars_tharsis")
    assert result["ok"] is True
    assert len(result["rows"]) == 5, (
        f"expected 5 volcanoes; got {len(result['rows'])}"
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
    from ephemerides_spectral._research.mars_tharsis_data import (
        MARS_THARSIS_VOLCANOES,
    )
    referenced = {v.source_key for v in MARS_THARSIS_VOLCANOES}
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str)
        assert len(entry["source_doi"]) >= 5
        assert iso_pattern.match(entry["source_published_date"])


def test_all_rows_share_single_row_type() -> None:
    """Mars Tharsis is single-row-type. Pin it."""
    for row in _amsc_rows_indexed_by_name().values():
        assert row["row_type"] == "tharsis_volcano"


def test_role_distribution() -> None:
    """The 5 volcanoes split as: 3 tharsis_montes (Arsia/Pavonis/
    Ascraeus on the NE-SW ridge) + 1 olympus_outlier (Olympus Mons,
    NW super-volcano) + 1 alba_outlier (Alba Mons, older N shield)."""
    rows = _amsc_rows_indexed_by_name()
    by_role: Dict[str, int] = {}
    for row in rows.values():
        by_role[row["role"]] = by_role.get(row["role"], 0) + 1
    assert by_role == {
        "tharsis_montes": 3,
        "olympus_outlier": 1,
        "alba_outlier": 1,
    }, f"unexpected role distribution: {by_role}"


def test_olympus_mons_is_largest_summit_elevation() -> None:
    """Headline physics ratchet: Olympus Mons has the largest summit
    elevation in the catalogue (~21.2 km above MOLA datum) — the
    direct consequence of stationary plumes + no plate tectonics
    that the v0.24.5 Hawaii vs v0.24.7 Mars Tharsis pair
    demonstrates. Pin it."""
    rows = _amsc_rows_indexed_by_name()
    olympus = rows["olympus_mons"]
    assert olympus["role"] == "olympus_outlier"
    other_max = max(
        row["summit_elevation_m"]
        for name, row in rows.items()
        if name != "olympus_mons"
    )
    assert olympus["summit_elevation_m"] > other_max, (
        f"Olympus Mons summit {olympus['summit_elevation_m']} m "
        f"should exceed all other Tharsis edifices "
        f"(max other = {other_max} m)"
    )


def test_alba_mons_is_largest_edifice_diameter() -> None:
    """Headline physics ratchet: Alba Mons has the largest base
    diameter in the catalogue (~1500 km) — the broader / shorter /
    older signature of the earlier-phase Tharsis volcanism. Pin it."""
    rows = _amsc_rows_indexed_by_name()
    alba = rows["alba_mons"]
    assert alba["role"] == "alba_outlier"
    other_max = max(
        row["edifice_diameter_km"]
        for name, row in rows.items()
        if name != "alba_mons"
    )
    assert alba["edifice_diameter_km"] > other_max, (
        f"Alba Mons base {alba['edifice_diameter_km']} km "
        f"should exceed all other Tharsis edifices "
        f"(max other = {other_max} km)"
    )


def test_alba_mons_oldest_in_roster() -> None:
    """Alba Mons (mid-Hesperian, ~1.5 Gyr) is the oldest edifice in
    the catalogue — representing an earlier phase of Tharsis
    volcanism than the younger Tharsis Montes ridge / Olympus Mons
    summit flows."""
    rows = _amsc_rows_indexed_by_name()
    ages = sorted(((row["age_myr"], name) for name, row in rows.items()))
    assert ages[-1][1] == "alba_mons", (
        f"oldest expected alba_mons; got {ages[-1][1]!r}"
    )
