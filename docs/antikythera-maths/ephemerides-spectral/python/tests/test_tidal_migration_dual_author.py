"""Tidal-migration dual-author diff test (v0.30.0rc7).

The same 6 parent-satellite migration rows are encoded in two places:

* **AMSC path** — ``research/attested/tidal_migration/migration.ndjson``
  consumed by the literature_curated adapter; surfaced via
  ``bridge.get_attested_dataset("tidal_migration")``.
* **Hand-coded path** — ``_research/tidal_migration_data.py``'s
  ``TIDAL_MIGRATIONS`` list (frozen @dataclass + List + SOURCES dict),
  the v0.21.6 Sol Tidal Migration catalogue's data source.

The two paths must agree on every row, every field. Divergence is the
data: a schema too thin to express the @dataclass, or one path edited
without the other. This is the attested-TOML backfill of a v0.21.x
cross-channel coupling catalogue (cf. saturn_rings + solar_rotation).

The per-row source DOIs were triality-attested (haiku/sonnet/opus +
opus reconciler vs live CrossRef, 2026-06-06) before being committed:
all six resolve and match their cited paper. The williams
``source_published_date`` is 2015 (CrossRef published year; the DOI
suffix uses the 2014 submission-ID convention) — the panel's correction.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge
from ephemerides_spectral._research.tidal_migration_data import (
    TIDAL_MIGRATIONS,
    migration_to_data_dict,
)


def _amsc_rows_indexed_by_pair() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("tidal_migration")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        pair = data["pair_name"]
        assert pair not in out, f"duplicate AMSC row: {pair!r}"
        out[pair] = data
    return out


def _hand_coded_rows_indexed_by_pair() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for m in TIDAL_MIGRATIONS:
        data = migration_to_data_dict(m)
        pair = data["pair_name"]
        assert pair not in out, f"duplicate hand-coded row: {pair!r}"
        out[pair] = data
    return out


def test_dual_author_row_count_agrees() -> None:
    amsc = _amsc_rows_indexed_by_pair()
    hand = _hand_coded_rows_indexed_by_pair()
    assert len(amsc) == len(hand) == 6, (
        f"row-count mismatch: AMSC={len(amsc)}, hand-coded={len(hand)}; "
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_pair_names_agree() -> None:
    amsc = _amsc_rows_indexed_by_pair()
    hand = _hand_coded_rows_indexed_by_pair()
    assert set(amsc) == set(hand), (
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_per_row_field_agreement() -> None:
    amsc = _amsc_rows_indexed_by_pair()
    hand = _hand_coded_rows_indexed_by_pair()
    mismatches: List[str] = []
    for pair in sorted(set(amsc) & set(hand)):
        a, h = amsc[pair], hand[pair]
        for field in sorted(set(a) | set(h)):
            av, hv = a.get(field, "<MISSING>"), h.get(field, "<MISSING>")
            if av != hv:
                mismatches.append(
                    f"  row {pair!r}, field {field!r}: "
                    f"AMSC={av!r} vs hand-coded={hv!r}"
                )
    assert not mismatches, (
        "dual-author divergence:\n" + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_pair() == _hand_coded_rows_indexed_by_pair()


def test_every_amsc_row_carries_attested_source_doi() -> None:
    """Per-row attestation discipline: every row has a non-empty
    source_doi (the literature_curated descriptor requires it)."""
    amsc = _amsc_rows_indexed_by_pair()
    for pair, data in amsc.items():
        assert data.get("source_doi"), f"{pair!r} missing source_doi"
        assert len(data["source_doi"]) >= 5, f"{pair!r} source_doi too short"


def test_williams_published_year_is_2015_not_2014() -> None:
    """The triality panel's correction: the terra-luna row's DOI suffix
    uses the 2014 submission convention, but CrossRef's published year is
    2015 — the attested source_published_date must reflect 2015."""
    amsc = _amsc_rows_indexed_by_pair()
    assert amsc["terra-luna"]["source_published_date"] == "2015"
