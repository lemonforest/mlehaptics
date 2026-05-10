"""Sol Dynamical-Regime Classifier Training Roster dual-author diff
test — v0.27.0 phase A.

11 ship-row roster (one per v0.24.x ship); single row_type
('regime_example'). Mirrors prior phase A patterns.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _dynamical_regime_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("dynamical_regime")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("dynamical_regime")
    assert result["ok"] is True
    assert len(result["rows"]) == 11, (
        f"expected 11 rows; got {len(result['rows'])}"
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
    from ephemerides_spectral._research.dynamical_regime_data import (
        REGIME_EXAMPLES,
    )
    referenced = {ex.source_key for ex in REGIME_EXAMPLES}
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
    """Dynamical-regime training roster is single-row-type. Pin it."""
    for row in _amsc_rows_indexed_by_name().values():
        assert row["row_type"] == "regime_example"


def test_regime_label_distribution_pins_v024_taxonomy() -> None:
    """Headline ratchet: the regime-label distribution pins the
    v0.24.0-v0.24.12 ship taxonomy. Two ships share the
    `temporal_quasi_periodic_cycle` label (v0.24.8 Axial + v0.24.12
    Loki Patera); every other label is unique. Pin it."""
    rows = _amsc_rows_indexed_by_name()
    by_label: Dict[str, int] = {}
    for row in rows.values():
        by_label[row["regime_label"]] = by_label.get(row["regime_label"], 0) + 1
    assert by_label == {
        "rigid_body_action_angle_stable": 1,           # v0.24.0 Mercury
        "rigid_body_action_angle_commensurate": 1,     # v0.24.1 Luna
        "rigid_body_chaotic_obliquity": 1,             # v0.24.2 Mars
        "continuum_normal_modes": 1,                   # v0.24.3 Sun
        "shape_residual_chandrasekhar": 1,             # v0.24.4 Toroidal
        "bounded_local_laplacian_trajectory": 1,       # v0.24.5 Hawaii
        "radiation_coupled_drift": 1,                  # v0.24.6 Yarkovsky/YORP
        "bounded_local_laplacian_family": 1,           # v0.24.7 Mars Tharsis
        "temporal_quasi_periodic_cycle": 2,            # v0.24.8 Axial + v0.24.12 Loki
        "rigid_body_action_angle_mutual_lock": 1,      # v0.24.11 Pluto-Charon
    }, f"unexpected regime-label distribution: {by_label}"


def test_pluto_charon_only_mutual_lock_row() -> None:
    """v0.24.11 Pluto-Charon defines the
    `rigid_body_action_angle_mutual_lock` label — the only training
    row in this regime. Pin it as the v0.24.10 schema-gap closure."""
    rows = _amsc_rows_indexed_by_name()
    mutual_lock_rows = [
        name for name, row in rows.items()
        if row["regime_label"] == "rigid_body_action_angle_mutual_lock"
    ]
    assert mutual_lock_rows == ["pluto_charon_dynamical_spectrum"], (
        f"mutual_lock training row should be Pluto-Charon only; "
        f"got {mutual_lock_rows}"
    )


def test_axial_seamount_is_only_negative_prediction_track() -> None:
    """Headline ratchet: v0.24.8 Axial Seamount is the only training
    row with prediction_track_signal = -1 (the canonical published-
    forecast-MISS case). Pin it as the methodology's first observed
    spectral-stability failure mode at decade scale."""
    rows = _amsc_rows_indexed_by_name()
    miss_rows = [
        name for name, row in rows.items()
        if row["prediction_track_signal"] == -1
    ]
    assert miss_rows == ["axial_seamount"], (
        f"prediction_track_signal=-1 training row should be Axial only; "
        f"got {miss_rows}"
    )


def test_v024_source_keys_map_to_real_dois() -> None:
    """All `v024_N` source_keys map to real Crossref-indexed DOIs (no
    nodoi: / historical: / isbn: prefixes for this catalogue — the
    v0.24.x ship taxonomy is built on the modern Crossref-era
    literature)."""
    for source_key, prov in SOURCE_KEY_PROVENANCE.items():
        assert source_key.startswith("v024_"), (
            f"unexpected source_key {source_key!r}; expected v024_N format"
        )
        doi = prov["source_doi"]
        assert not doi.startswith(("nodoi:", "historical:", "isbn:", "ads:")), (
            f"v024_N source_keys should map to real DOIs; "
            f"{source_key!r} maps to {doi!r}"
        )
