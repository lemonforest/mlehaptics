"""Sol Yarkovsky/YORP dual-author diff test — v0.27.0 phase A.

10-asteroid roster; single row_type. Mirrors prior phase A patterns.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _yarkovsky_yorp_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("yarkovsky_yorp")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("yarkovsky_yorp")
    assert result["ok"] is True
    assert len(result["rows"]) == 10, (
        f"expected 10 asteroids; got {len(result['rows'])}"
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
    from ephemerides_spectral._research.yarkovsky_yorp_data import (
        YARKOVSKY_YORP_ENTRIES,
    )
    referenced = {e.source_key for e in YARKOVSKY_YORP_ENTRIES}
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
    """Yarkovsky/YORP is single-row-type. Pin it."""
    for row in _amsc_rows_indexed_by_name().values():
        assert row["row_type"] == "yarkovsky_yorp_entry"


def test_prograde_rotators_drift_outward_retrograde_inward() -> None:
    """Headline physics ratchet: the Yarkovsky diurnal effect's
    direction is set by rotation sense — prograde rotators drift
    outward (positive da/dt), retrograde drift inward (negative).
    Pin this on every row that has a measured Yarkovsky drift."""
    rows = _amsc_rows_indexed_by_name()
    for name, row in rows.items():
        drift = row.get("yarkovsky_drift_1e4_au_per_myr")
        if drift is None:
            continue
        if row["is_prograde"]:
            assert drift > 0, (
                f"{name!r} is prograde but Yarkovsky drift "
                f"{drift} is non-positive"
            )
        else:
            assert drift < 0, (
                f"{name!r} is retrograde but Yarkovsky drift "
                f"{drift} is non-negative"
            )


def test_bennu_is_first_directly_imaged_yarkovsky_drifter() -> None:
    """Headline ratchet: Bennu (OSIRIS-REx target) is the canonical
    retrograde inward-drifter at -19e-4 AU/Myr — the largest-magnitude
    Yarkovsky drift in this catalogue and the headline direct-imaging
    detection. Pin both the magnitude and the regime (retrograde
    inward)."""
    rows = _amsc_rows_indexed_by_name()
    bennu = rows["bennu"]
    assert bennu["is_prograde"] is False
    assert bennu["yarkovsky_drift_1e4_au_per_myr"] == -19.0
    drifts = [
        abs(row["yarkovsky_drift_1e4_au_per_myr"])
        for row in rows.values()
        if row.get("yarkovsky_drift_1e4_au_per_myr") is not None
    ]
    assert max(drifts) == 19.0, (
        f"Bennu's |drift| 19.0 should be the maximum; got max={max(drifts)}"
    )


def test_1950_da_at_rotational_fission_limit() -> None:
    """1950 DA's 2.121-h rotation period sits AT the canonical 2.2-h
    rubble-pile fission limit — pin the period as below the threshold
    (cohesive forces required to prevent disruption)."""
    from ephemerides_spectral._research.yarkovsky_yorp_data import (
        ROTATIONAL_FISSION_PERIOD_HOURS,
    )
    rows = _amsc_rows_indexed_by_name()
    asteroid_1950_da = rows["1950_da"]
    period = asteroid_1950_da["rotation_period_hours"]
    assert period < ROTATIONAL_FISSION_PERIOD_HOURS, (
        f"1950 DA period {period} h should be below fission limit "
        f"{ROTATIONAL_FISSION_PERIOD_HOURS} h"
    )
    # And it should be the closest in this catalogue to the fission
    # limit — pinning the headline-near-fission-limit observation.
    closest = min(
        (row["rotation_period_hours"], name)
        for name, row in rows.items()
        if row["rotation_period_hours"] >= 1.0  # exclude 2000 PH5
                                                # (12-minute period, already past
                                                # any rubble-pile interpretation)
    )
    assert closest[1] == "1950_da", (
        f"closest-to-fission-limit (≥ 1 h) expected 1950_da; got {closest[1]!r}"
    )
