"""Sun Dynamical Spectrum dual-author diff test — v0.27.0 phase A.

20 helioseismic p-mode rows encoded in two places:

* **AMSC path** — ``research/attested/sun_dynamical_spectrum/row.ndjson``
* **Hand-coded path** — ``_research/sun_dynamical_spectrum_data.py``
  (the v0.24.3 ship) converted via ``_sun_amsc_helpers.py``.

Mirrors PRs #303 / #306 / #308 (Mercury / Luna / Mars). Single
row_type catalogue.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _sun_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("sun_dynamical_spectrum")
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
    result = bridge.get_attested_dataset("sun_dynamical_spectrum")
    assert result["ok"] is True
    assert len(result["rows"]) == 20, (
        f"expected 20 rows; got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    assert len(_amsc_rows_indexed_by_name()) == len(_hand_coded_rows_indexed_by_name())


def test_dual_author_row_names_agree() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert set(amsc_rows) == set(hand_coded_rows)


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
    assert _amsc_rows_indexed_by_name() == _hand_coded_rows_indexed_by_name()


def test_every_source_key_in_provenance_table() -> None:
    from ephemerides_spectral._research.sun_dynamical_spectrum_data import (
        HELIOSEISMIC_MODES,
    )
    referenced = {mode.source_key for mode in HELIOSEISMIC_MODES}
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str)
        assert len(entry["source_doi"]) >= 5
        assert iso_pattern.match(entry["source_published_date"])


def test_all_rows_share_helioseismic_mode_row_type() -> None:
    """Sun catalogue is single-row-type. Pin it."""
    amsc_rows = _amsc_rows_indexed_by_name()
    for name, row in amsc_rows.items():
        assert row["row_type"] == "helioseismic_mode", (
            f"row {name!r} has row_type {row['row_type']!r}; expected 'helioseismic_mode'"
        )


def test_all_rows_are_p_modes() -> None:
    """The current catalogue ships only p-modes (Tassoul-1980 asymptotic-
    relation reference). Future g/f/mixed-mode rows would relax this
    assertion deliberately."""
    amsc_rows = _amsc_rows_indexed_by_name()
    for name, row in amsc_rows.items():
        assert row["mode_class"] == "p", (
            f"row {name!r} has mode_class {row['mode_class']!r}; expected 'p'"
        )


def test_n_l_grid_coverage() -> None:
    """The v0.24.3 catalogue ships n=18-25 at l=0 (8 rows), n=18-23 at
    l=1 (6 rows), n=18-23 at l=2 (6 rows). Pin the grid against
    silent regression."""
    amsc_rows = _amsc_rows_indexed_by_name()
    by_l: Dict[int, set] = {}
    for row in amsc_rows.values():
        by_l.setdefault(row["l"], set()).add(row["n"])
    assert by_l[0] == set(range(18, 26)), f"l=0 n-coverage: {sorted(by_l[0])}"
    assert by_l[1] == set(range(18, 24)), f"l=1 n-coverage: {sorted(by_l[1])}"
    assert by_l[2] == set(range(18, 24)), f"l=2 n-coverage: {sorted(by_l[2])}"


def test_frequencies_increase_with_n_at_fixed_l() -> None:
    """Tassoul asymptotic relation: ν_{n,l} ≈ Δν(n + l/2 + ε) - small.
    At fixed l, frequency increases monotonically with n. Pin this
    against silent data corruption."""
    amsc_rows = _amsc_rows_indexed_by_name()
    by_l: Dict[int, List[tuple]] = {}
    for row in amsc_rows.values():
        by_l.setdefault(row["l"], []).append((row["n"], row["frequency_uhz"]))
    for l, points in by_l.items():
        points.sort()
        for i in range(1, len(points)):
            assert points[i][1] > points[i - 1][1], (
                f"l={l}: frequency must increase with n; "
                f"got n={points[i-1][0]} ν={points[i-1][1]} → "
                f"n={points[i][0]} ν={points[i][1]}"
            )
