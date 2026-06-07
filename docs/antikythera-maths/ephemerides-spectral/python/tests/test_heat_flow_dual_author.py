"""Heat-flow dual-author diff test (v0.30.0rc10).

The same 6 per-body heat-flow rows are encoded in two places:

* **AMSC path** — ``research/attested/heat_flow/heat_flow.ndjson``
  consumed by the literature_curated adapter; surfaced via
  ``bridge.get_attested_dataset("heat_flow")``.
* **Hand-coded path** — ``_research/heat_flow_data.py``'s ``HEAT_FLOWS``
  list (frozen @dataclass + List + SOURCES dict), the v0.21.8 Sol Heat
  Flow catalogue's data source.

The two paths must agree on every row, every field. Divergence is the
data: a schema too thin to express the @dataclass, or one path edited
without the other. This is the attested-TOML backfill of a v0.21.x
cross-channel coupling catalogue (cf. saturn_rings + solar_rotation +
tidal_migration).

This backfill follows the v0.30.0rc9 CITATION REPAIR: the rc7 triality
panel caught three broken citations in heat_flow's shipped data
(``khan_2023`` -> wrong DOI/lunar paper, ``tobie_2008`` -> the Enceladus
paper cited for Titan, ``veeder_2012`` -> a paraphrased title), so
heat_flow was held back from the rc7 batch backfill until those citations
were corrected (rc9). All six per-row DOIs are now CrossRef-verified.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge
from ephemerides_spectral._research.heat_flow_data import (
    HEAT_FLOWS,
    heatflow_to_data_dict,
)


def _amsc_rows_indexed_by_body() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("heat_flow")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        body = data["body"]
        assert body not in out, f"duplicate AMSC row: {body!r}"
        out[body] = data
    return out


def _hand_coded_rows_indexed_by_body() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for hf in HEAT_FLOWS:
        data = heatflow_to_data_dict(hf)
        body = data["body"]
        assert body not in out, f"duplicate hand-coded row: {body!r}"
        out[body] = data
    return out


def test_dual_author_row_count_agrees() -> None:
    amsc = _amsc_rows_indexed_by_body()
    hand = _hand_coded_rows_indexed_by_body()
    assert len(amsc) == len(hand) == 6, (
        f"row-count mismatch: AMSC={len(amsc)}, hand-coded={len(hand)}; "
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_body_names_agree() -> None:
    amsc = _amsc_rows_indexed_by_body()
    hand = _hand_coded_rows_indexed_by_body()
    assert set(amsc) == set(hand), (
        f"AMSC-only={set(amsc) - set(hand)}; hand-only={set(hand) - set(amsc)}"
    )


def test_dual_author_per_row_field_agreement() -> None:
    amsc = _amsc_rows_indexed_by_body()
    hand = _hand_coded_rows_indexed_by_body()
    mismatches: List[str] = []
    for body in sorted(set(amsc) & set(hand)):
        a, h = amsc[body], hand[body]
        for field in sorted(set(a) | set(h)):
            av, hv = a.get(field, "<MISSING>"), h.get(field, "<MISSING>")
            if av != hv:
                mismatches.append(
                    f"  row {body!r}, field {field!r}: "
                    f"AMSC={av!r} vs hand-coded={hv!r}"
                )
    assert not mismatches, (
        "dual-author divergence:\n" + "\n".join(mismatches)
    )


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_body() == _hand_coded_rows_indexed_by_body()


def test_every_amsc_row_carries_attested_source_doi() -> None:
    """Per-row attestation discipline: every row has a non-empty
    source_doi (the literature_curated descriptor requires it)."""
    amsc = _amsc_rows_indexed_by_body()
    for body, data in amsc.items():
        assert data.get("source_doi"), f"{body!r} missing source_doi"
        assert len(data["source_doi"]) >= 5, f"{body!r} source_doi too short"


def test_repaired_citations_are_the_corrected_ones() -> None:
    """The rc9 citation-repair must be reflected in the attested NDJSON:
    mars cites Frizzell 2023, titan cites Tobie 2005, io cites the 2012
    Veeder DOI — and none of the retired keys/DOIs survive."""
    amsc = _amsc_rows_indexed_by_body()
    assert amsc["mars"]["source_doi"] == "10.1016/j.icarus.2023.115700"
    assert amsc["mars"]["source_key"] == "frizzell_2023"
    assert amsc["titan"]["source_doi"] == "10.1016/j.icarus.2004.12.007"
    assert amsc["titan"]["source_key"] == "tobie_2005"
    assert amsc["io"]["source_doi"] == "10.1016/j.icarus.2012.04.004"
    all_dois = {d["source_doi"] for d in amsc.values()}
    assert "10.1038/s41586-023-06289-w" not in all_dois  # the retired khan DOI
    assert "10.1016/j.icarus.2008.03.008" not in all_dois  # the Enceladus mis-cite
