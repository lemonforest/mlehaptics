"""Saturn rings dual-author diff test — Phase 3 of the Saturn ring
exercise.

The same 12 ring-feature rows are encoded in two places:

* **AMSC path** — ``research/attested/saturn_rings/ring_feature.ndjson``
  consumed by the literature_curated adapter; bridge surface returns
  rows via ``get_attested_dataset("saturn_rings")``.
* **Hand-coded path** — ``_research/saturn_rings_data.py``'s
  ``SATURN_RING_FEATURES`` list, encoded in the v0.24.x discipline
  (frozen @dataclass + List + SOURCES dict).

This test asserts the two paths agree on every row, every field. If
they diverge, the divergence is the data:

  - "AMSC path has X but hand-coded doesn't" → the descriptor schema
    isn't rich enough at this row granularity, or the hand-coded
    path's @dataclass needs a new field. Either is a real finding
    that the pre-v1.0 backfill review (PR #284 ROADMAP entry) hinges
    on.
  - "Hand-coded value differs from NDJSON value" → one of the two
    was edited without updating the other. The test ratchets the
    discipline that they stay in sync until the v0.27.x or later
    backfill review picks one to retire.

Why this is the load-bearing test for the Phase 3 ship
------------------------------------------------------
The pre-v1.0 architectural review (PR #284 ROADMAP entry) asks whether
to migrate every v0.24.x ``_data.py`` module to AMSC-backed NDJSON
before declaring v1.0 stable. The MPM-screened answer depends on
empirical evidence about whether AMSC's descriptor + JSON schema can
express what the hand-coded modules express. Saturn rings is the
first dual-author exercise; agreement here is one row of evidence
(rich-enough schema for at least this catalogue's density). Future
dual-author exercises across other v0.24.x catalogues (Mercury,
Luna, Mars, Sun, etc.) would build the full evidence base.

References
----------
* PR #284 — pre-v1.0 backfill review.
* PR #286 — Phase 1 (AMSC literature_curated adapter + 12-row NDJSON).
* PR #289 — Phase 2 (per-row date/version + SSOT-driven validation).
* PR #290 — adapter_class filter on bridge surfaces (Step 2).
* This file — Phase 3 (parallel hand-coded module + diff test).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge
from ephemerides_spectral._research.saturn_rings_data import (
    SATURN_RING_FEATURES,
    feature_to_data_dict,
)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    """Load saturn_rings rows via the AMSC bridge surface and index
    by feature name for deterministic lookup."""
    result = bridge.get_attested_dataset("saturn_rings")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        name = data["name"]
        assert name not in out, f"duplicate AMSC row: {name!r}"
        out[name] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    """Convert hand-coded SATURN_RING_FEATURES to AMSC-shape dicts,
    indexed by feature name."""
    out: Dict[str, Dict[str, Any]] = {}
    for feature in SATURN_RING_FEATURES:
        data = feature_to_data_dict(feature)
        name = data["name"]
        assert name not in out, f"duplicate hand-coded row: {name!r}"
        out[name] = data
    return out


# ─────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────


def test_dual_author_row_count_agrees() -> None:
    """The two paths must encode the same number of rows. If one path
    has more rows, the other path was forgotten when a row was added.
    """
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert len(amsc_rows) == len(hand_coded_rows), (
        f"row-count mismatch: AMSC={len(amsc_rows)}, "
        f"hand-coded={len(hand_coded_rows)}. "
        f"AMSC-only: {set(amsc_rows) - set(hand_coded_rows)}; "
        f"hand-coded-only: {set(hand_coded_rows) - set(amsc_rows)}"
    )


def test_dual_author_row_names_agree() -> None:
    """The set of row names must match exactly between the two paths.
    Surfaces typos and forgotten-add cases at row granularity."""
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    amsc_only = set(amsc_rows) - set(hand_coded_rows)
    hand_coded_only = set(hand_coded_rows) - set(amsc_rows)
    assert not amsc_only, f"rows in AMSC NDJSON but not hand-coded: {amsc_only}"
    assert not hand_coded_only, (
        f"rows in hand-coded module but not AMSC NDJSON: {hand_coded_only}"
    )


def test_dual_author_per_row_field_agreement() -> None:
    """For every row that exists in both paths, every field must
    agree. This is the load-bearing assertion for Phase 3.

    Iterates over every (name, field) pair and asserts equality.
    Errors include both values + the field name + the row name for
    fast diagnosis when a path drifts.
    """
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    common_names = sorted(set(amsc_rows) & set(hand_coded_rows))
    assert common_names, "no rows in common — earlier ratchets should have caught this"

    mismatches: List[str] = []
    for name in common_names:
        amsc = amsc_rows[name]
        hc = hand_coded_rows[name]
        # Compare on the union of fields so neither path can hide a
        # field by omitting it.
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
        "dual-author divergence — AMSC NDJSON and hand-coded "
        f"SATURN_RING_FEATURES disagree on {len(mismatches)} "
        f"row/field pair(s):\n" + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    """As a final ratchet, assert the two indexed dicts are equal
    when canonicalised. This is the strict byte-stable agreement
    test; the per-field test above gives nicer diagnostics, but
    this catches anything the per-field iteration might miss
    (e.g. ordering issues in nested structures, types of nulls).
    """
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert amsc_rows == hand_coded_rows, (
        "dual-author dict-equality failure (see "
        "test_dual_author_per_row_field_agreement for per-field "
        "diagnostics)"
    )
