"""Toroidal-Residual J₂ Catalogue dual-author diff test — v0.27.0 phase A.

14 per-body Chandrasekhar-sequence classification rows encoded in
two places:

* **AMSC path** — ``research/attested/toroidal_residual/row.ndjson``
* **Hand-coded path** — ``_research/toroidal_residual_data.py``
  (the v0.24.4 ship) converted via ``_toroidal_residual_amsc_helpers.py``.

Mirrors PRs #303 / #306 / #308 / #309. Single row_type catalogue.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _toroidal_residual_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("toroidal_residual")
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
        assert name not in out
        out[name] = data
    return out


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("toroidal_residual")
    assert result["ok"] is True
    assert len(result["rows"]) == 14, (
        f"expected 14 bodies; got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    assert len(_amsc_rows_indexed_by_name()) == len(_hand_coded_rows_indexed_by_name())


def test_dual_author_row_names_agree() -> None:
    assert set(_amsc_rows_indexed_by_name()) == set(_hand_coded_rows_indexed_by_name())


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
    from ephemerides_spectral._research.toroidal_residual_data import (
        TOROIDAL_RESIDUALS,
    )
    referenced = {row.source_key for row in TOROIDAL_RESIDUALS}
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
    """Toroidal-residual is single-row-type. Pin it."""
    for row in _amsc_rows_indexed_by_name().values():
        assert row["row_type"] == "toroidal_residual_classification"


def test_regime_values_are_valid() -> None:
    """Regimes must be in the Chandrasekhar-sequence enum:
    sphere / maclaurin / jacobi / bar / ring."""
    valid_regimes = {"sphere", "maclaurin", "jacobi", "bar", "ring"}
    for name, row in _amsc_rows_indexed_by_name().items():
        assert row["regime"] in valid_regimes, (
            f"row {name!r} has invalid regime {row['regime']!r}"
        )


def test_fossil_figures_match_expected_bodies() -> None:
    """Mercury and Luna are the canonical fossil-figure cases (J₂
    exceeds current-rotation prediction). Pin the labelling."""
    rows = _amsc_rows_indexed_by_name()
    fossils = {name for name, row in rows.items() if row["fossil_figure"]}
    assert fossils == {"mercury", "luna"}, (
        f"expected fossils = mercury + luna; got {fossils}"
    )


def test_saturn_is_closest_to_maclaurin_jacobi_bifurcation() -> None:
    """Headline physics ratchet: Saturn's q is the largest in the
    catalogue (closest to the q ≈ 0.187 Maclaurin-Jacobi bifurcation
    threshold) and still below the threshold (Maclaurin regime, not
    Jacobi)."""
    rows = _amsc_rows_indexed_by_name()
    saturn_q = rows["saturn"]["rotation_parameter_q"]
    assert rows["saturn"]["regime"] == "maclaurin"
    other_q_max = max(
        row["rotation_parameter_q"]
        for name, row in rows.items()
        if name != "saturn"
    )
    assert saturn_q > other_q_max, (
        f"Saturn q={saturn_q} should exceed all other bodies' q "
        f"(max other = {other_q_max})"
    )
    assert saturn_q < 0.187, (
        f"Saturn q={saturn_q} should still be below Maclaurin-Jacobi "
        f"bifurcation threshold 0.187"
    )


def test_all_rows_in_sphere_or_maclaurin_regime() -> None:
    """The v0.24.4 catalogue's 14 bodies are all in either sphere
    (Venus, q ≈ 10⁻⁷ from its 243-day rotation) or Maclaurin
    (everything else). No Jacobi triaxials, no bars, no rings — those
    would be Haumea or Saturn-rings-as-fragmented-body, not in this
    roster. Pin the split so a future regime-classifier change
    surfaces cleanly."""
    rows = _amsc_rows_indexed_by_name()
    for name, row in rows.items():
        assert row["regime"] in {"sphere", "maclaurin"}, (
            f"row {name!r} expected sphere or maclaurin regime; "
            f"got {row['regime']!r}"
        )
    # Venus is the canonical sphere case here (slowest rotator;
    # retrograde 243-day period).
    assert rows["venus"]["regime"] == "sphere", (
        f"venus expected sphere; got {rows['venus']['regime']!r}"
    )
