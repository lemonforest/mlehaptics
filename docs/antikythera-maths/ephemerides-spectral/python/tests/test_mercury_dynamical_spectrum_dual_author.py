"""Mercury Dynamical Spectrum dual-author diff test — v0.27.0 phase A.

The same 16 Mercury action-angle decomposition rows are encoded in
two places:

* **AMSC path** — ``research/attested/mercury_dynamical_spectrum/mercury_dynamical_spectrum.ndjson``
  consumed by the literature_curated adapter; bridge surface returns
  rows via ``get_attested_dataset("mercury_dynamical_spectrum")``.
* **Hand-coded path** — ``_research/mercury_dynamical_spectrum_data.py``
  (the v0.24.0 ship) — converted to AMSC shape via the helper module
  ``_mercury_amsc_helpers.py``, which fills attestation fields from a
  static SOURCE_KEY_PROVENANCE mapping.

This test asserts the two paths agree on every row, every field. If
they diverge, the divergence is the data:

  - "AMSC has X but hand-coded doesn't" → the descriptor schema isn't
    rich enough at this row granularity, or the helper's converter is
    missing a field.
  - "Hand-coded value differs from NDJSON value" → one of the two was
    edited without updating the other. The test ratchets the
    discipline that they stay in sync until the v0.27.x backfill
    review picks one to retire (currently both are kept; the AMSC
    NDJSON is the attestation envelope).

Why this matters for v0.27.0
-----------------------------
This is the second dual-author exercise (Saturn rings PR #291 was
the first). The pre-v1.0 architectural review in the ROADMAP asks
whether to migrate every v0.24.x ``_data.py`` module to AMSC-backed
NDJSON before declaring v1.0 stable. The MPM-screened answer
depends on empirical evidence about whether AMSC's descriptor +
JSON schema can express what the hand-coded modules express.
Mercury is the second per-body catalogue exercised; agreement here
is one row of evidence (rich-enough schema for action-angle row
density). Future v0.27.x phase A PRs build the full evidence base
across the remaining v0.24.x catalogues.

References
----------
* PR #291 — Saturn rings dual-author exercise (the precedent pattern).
* PR #297 — v0.27.0 ROADMAP entry; phase A is the literature_curated
  backfill of every v0.24.x catalogue.
* Notebook §22.9 — what v0.27.0 ships.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _mercury_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    """Load mercury_dynamical_spectrum rows via the AMSC bridge surface
    and index by row name for deterministic lookup. Names are unique
    by construction (mode names + contribution contributor names
    don't collide; OBSERVED_TOTAL is a contribution row only)."""
    result = bridge.get_attested_dataset("mercury_dynamical_spectrum")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        name = data["name"]
        assert name not in out, f"duplicate AMSC row: {name!r}"
        out[name] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    """Convert hand-coded rows to AMSC shape via the helper, index by
    name."""
    out: Dict[str, Dict[str, Any]] = {}
    for data in hand_coded_rows_in_amsc_shape():
        name = data["name"]
        assert name not in out, f"duplicate hand-coded row: {name!r}"
        out[name] = data
    return out


# ─────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────


def test_amsc_dataset_loads() -> None:
    """The AMSC bridge surface returns ``ok=True`` and a non-empty
    rows list. Sanity gate before the dual-author comparison runs."""
    result = bridge.get_attested_dataset("mercury_dynamical_spectrum")
    assert result["ok"] is True, result
    assert isinstance(result["rows"], list)
    assert len(result["rows"]) == 16, (
        f"expected 16 rows (8 modes + 8 contributions); got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    """The two paths must encode the same number of rows. If one path
    has more rows, the other was forgotten when a row was added."""
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
    agree. This is the load-bearing assertion for phase A.

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
        f"mercury_dynamical_spectrum_data disagree on {len(mismatches)} "
        f"row/field pair(s):\n" + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    """As a final ratchet, assert the two indexed dicts are equal
    when canonicalised. This is the strict byte-stable agreement
    test; the per-field test above gives nicer diagnostics, but
    this catches anything the per-field iteration might miss
    (e.g. ordering issues, type-of-null differences)."""
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    assert amsc_rows == hand_coded_rows, (
        "dual-author dict-equality failure (see "
        "test_dual_author_per_row_field_agreement for per-field "
        "diagnostics)"
    )


# ─────────────────────────────────────────────────────────────────────
# Schema-rule ratchets — the helper's static mappings are SSOT for
# phase A. If a future contributor adds a row to the hand-coded
# module with a NEW source_key, they must also extend
# SOURCE_KEY_PROVENANCE; otherwise the converter raises KeyError.
# These tests pin the schema/data-shape rules.
# ─────────────────────────────────────────────────────────────────────


def test_every_source_key_in_provenance_table() -> None:
    """Every source_key referenced by the hand-coded module's rows
    must have a corresponding SOURCE_KEY_PROVENANCE entry. Adding
    a new source_key without extending the table is the failure
    mode this test catches."""
    from ephemerides_spectral._research.mercury_dynamical_spectrum_data import (
        MERCURY_DYNAMICAL_MODES,
        MERCURY_PRECESSION_CONTRIBUTIONS,
    )
    referenced = set()
    for mode in MERCURY_DYNAMICAL_MODES:
        referenced.add(mode.source_key)
    for contrib in MERCURY_PRECESSION_CONTRIBUTIONS:
        referenced.add(contrib.source_key)
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing, (
        f"hand-coded module references source_keys without "
        f"SOURCE_KEY_PROVENANCE entries: {sorted(missing)}. "
        f"Extend tests/_mercury_amsc_helpers.py."
    )


def test_provenance_entries_have_required_fields() -> None:
    """Every SOURCE_KEY_PROVENANCE entry must populate
    source_doi (>=5 chars per schema), source_published_date (matches
    ISO 8601 partial-date pattern), and source_version (string or
    None)."""
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert "source_doi" in entry, key
        assert isinstance(entry["source_doi"], str), key
        assert len(entry["source_doi"]) >= 5, (
            f"{key}: source_doi too short for schema minLength=5"
        )
        assert iso_pattern.match(entry["source_published_date"]), (
            f"{key}: source_published_date {entry['source_published_date']!r} "
            f"doesn't match ISO 8601 partial-date pattern"
        )
        assert entry["source_version"] is None or isinstance(
            entry["source_version"], str
        ), key


def test_entered_locally_at_is_iso_date() -> None:
    """The entered_locally_at constant must be a valid ISO date."""
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", ENTERED_LOCALLY_AT), (
        f"ENTERED_LOCALLY_AT {ENTERED_LOCALLY_AT!r} is not ISO YYYY-MM-DD"
    )


def test_amsc_rows_all_carry_required_attestation_fields() -> None:
    """Every AMSC row must populate name, row_type, source_doi,
    source_published_date, entered_locally_at — the fields marked
    `required` in the schema. Non-required fields may be null."""
    amsc_rows = _amsc_rows_indexed_by_name()
    required = ["name", "row_type", "source_doi",
                "source_published_date", "entered_locally_at"]
    for name, row in amsc_rows.items():
        for field in required:
            assert field in row, f"row {name!r} missing required field {field!r}"
            assert row[field] is not None, (
                f"row {name!r} field {field!r} is null but the schema "
                f"requires a non-null value"
            )


def test_amsc_rows_split_evenly_between_row_types() -> None:
    """The catalogue ships exactly 8 dynamical_mode rows + 8
    precession_contribution rows. Anchored to the v0.24.0 module's
    contents; future row additions update this expected count
    deliberately."""
    amsc_rows = _amsc_rows_indexed_by_name()
    by_type: Dict[str, int] = {}
    for row in amsc_rows.values():
        by_type[row["row_type"]] = by_type.get(row["row_type"], 0) + 1
    assert by_type == {
        "dynamical_mode": 8,
        "precession_contribution": 8,
    }, (
        f"unexpected row-type distribution: {by_type}. "
        f"Expected 8 dynamical_mode + 8 precession_contribution."
    )
