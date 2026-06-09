"""Solar-cycle dual-author diff test (v0.30.0rc4).

The same 3 solar-cycle rows are encoded in two places:

* **AMSC path** — ``research/attested/solar_cycle/solar_cycle.ndjson``
  consumed by the literature_curated adapter; surfaced via
  ``bridge.get_attested_dataset("solar_cycle")``.
* **Hand-coded path** — ``_research/solar_cycle_data.py``'s
  ``SOLAR_CYCLES`` list, the rc3 Sol Solar Cycle Spectrum catalogue's
  data source.

The two paths must agree on every row, every field. Per-row source
DOIs + dates triality-attested (haiku/sonnet/opus vs ADS/arXiv/ROB)
before commit; dates at year granularity (the value all three tiers
externally confirmed).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge
from ephemerides_spectral._research.solar_cycle_data import (
    SOLAR_CYCLES,
    cycle_to_data_dict,
)


def _amsc_rows_indexed_by_number() -> Dict[int, Dict[str, Any]]:
    result = bridge.get_attested_dataset("solar_cycle")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[int, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        number = data["number"]
        assert number not in out, f"duplicate AMSC row: {number!r}"
        out[number] = data
    return out


def _hand_coded_rows_indexed_by_number() -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    for cycle in SOLAR_CYCLES:
        data = cycle_to_data_dict(cycle)
        number = data["number"]
        assert number not in out, f"duplicate hand-coded row: {number!r}"
        out[number] = data
    return out


def test_dual_author_row_count_agrees() -> None:
    amsc = _amsc_rows_indexed_by_number()
    hand = _hand_coded_rows_indexed_by_number()
    assert len(amsc) == len(hand) == 3, (
        f"row-count mismatch: AMSC={len(amsc)}, hand-coded={len(hand)}; "
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_numbers_agree() -> None:
    amsc = _amsc_rows_indexed_by_number()
    hand = _hand_coded_rows_indexed_by_number()
    assert set(amsc) == set(hand), (
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_per_row_field_agreement() -> None:
    amsc = _amsc_rows_indexed_by_number()
    hand = _hand_coded_rows_indexed_by_number()
    mismatches: List[str] = []
    for number in sorted(set(amsc) & set(hand)):
        a, h = amsc[number], hand[number]
        for field in sorted(set(a) | set(h)):
            av, hv = a.get(field, "<MISSING>"), h.get(field, "<MISSING>")
            if av != hv:
                mismatches.append(
                    f"  cycle {number!r}, field {field!r}: "
                    f"AMSC={av!r} vs hand-coded={hv!r}"
                )
    assert not mismatches, (
        "dual-author divergence:\n" + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_number() == _hand_coded_rows_indexed_by_number()


def test_every_amsc_row_carries_attested_source_doi() -> None:
    amsc = _amsc_rows_indexed_by_number()
    for number, data in amsc.items():
        assert data.get("source_doi"), f"cycle {number!r} missing source_doi"
        assert len(data["source_doi"]) >= 5, f"cycle {number!r} source_doi too short"
