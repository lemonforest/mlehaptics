"""Sol Dynamical-Regime OOS Probe Roster dual-author diff test —
v0.27.0 phase A.

10-probe roster; single row_type ('regime_probe'). Mirrors prior
phase A patterns. Companion to dynamical_regime training roster.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _dynamical_regime_probes_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("dynamical_regime_probes")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("dynamical_regime_probes")
    assert result["ok"] is True
    assert len(result["rows"]) == 10, (
        f"expected 10 probes; got {len(result['rows'])}"
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
    from ephemerides_spectral._research.dynamical_regime_probes_data import (
        REGIME_PROBES,
    )
    referenced = {p.source_key for p in REGIME_PROBES}
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
    """Probe roster is single-row-type. Pin it."""
    for row in _amsc_rows_indexed_by_name().values():
        assert row["row_type"] == "regime_probe"


def test_ood_expected_probe_distribution() -> None:
    """Headline ratchet: exactly one probe carries ood_expected=True
    (Ceres) — the genuinely-out-of-distribution case in the v0.24.10
    roster. The rest (including Vesta + magnetar despite their
    surprising classification behaviour) carry ood_expected=False
    because the schema-gap is documented as let-classifier-surprise-us
    rather than a-priori OOD-flagged."""
    rows = _amsc_rows_indexed_by_name()
    ood_probes = sorted([
        name for name, row in rows.items() if row["ood_expected"]
    ])
    assert ood_probes == ["ceres"], (
        f"ood_expected=True probes expected [ceres]; got {ood_probes}"
    )


def test_let_classifier_surprise_us_probes() -> None:
    """The let-classifier-surprise-us bucket (expected_regime=None +
    ood_expected=False) pins probes whose classifier behaviour is
    documented as ground-truth without a-priori expectation. Phobos
    + Vesta land here."""
    rows = _amsc_rows_indexed_by_name()
    surprise_probes = sorted([
        name for name, row in rows.items()
        if row["expected_regime"] is None and not row["ood_expected"]
    ])
    assert surprise_probes == ["phobos", "vesta"], (
        f"let-classifier-surprise-us probes expected [phobos, vesta]; "
        f"got {surprise_probes}"
    )


def test_pluto_charon_probe_targets_v024_11_label() -> None:
    """The Pluto-Charon probe was the v0.24.10 schema-gap surfacer and
    now self-classifies to the v0.24.11-introduced
    `rigid_body_action_angle_mutual_lock` regime. Pin the expected
    label as ground truth for the v0.24.11 closure."""
    rows = _amsc_rows_indexed_by_name()
    pc = rows["pluto_charon"]
    assert pc["expected_regime"] == "rigid_body_action_angle_mutual_lock"
    assert pc["has_commensurability"] == 1  # 1:1 mutual lock
    assert pc["ood_expected"] is False


def test_isbn_prefix_only_for_textbook_source() -> None:
    """Murray-Dermott 1999 *Solar System Dynamics* is a textbook;
    pin that it's the only `isbn:`-prefixed source in this
    catalogue."""
    isbn_keys = [
        key for key, entry in SOURCE_KEY_PROVENANCE.items()
        if entry["source_doi"].startswith("isbn:")
    ]
    assert isbn_keys == ["murray_dermott_1999"], (
        f"expected only murray_dermott_1999 as isbn:; got {isbn_keys}"
    )
