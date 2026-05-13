"""Adapter registry + adapter-specific tests.

Ported from
``docs/antikythera-maths/ephemerides-spectral/python/tests/test_attested_collector.py``
(Adapter section) at Phase 2 of Task #197. The original tests
reference ephemerides's real EarthRef SC descriptor; srmech-isolation
tests use the self-contained fixture from conftest.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srmech.amsc.adapters import (
    ADAPTERS,
    _base,
    csv_bulk,
    geotiff_bbox,
    html_scraper,
    json_api,
    literature_curated,
    netcdf_grid,
)
from srmech.amsc.descriptor import load_descriptor


# ──────────────────────────────────────────────────────────────────────
# Adapter registry
# ──────────────────────────────────────────────────────────────────────


def test_all_known_adapters_registered() -> None:
    """All six adapter modules register themselves at import time."""
    expected = {
        "html_scraper",
        "json_api",
        "csv_bulk",
        "netcdf_grid",
        "geotiff_bbox",
        "literature_curated",
    }
    assert set(ADAPTERS.keys()) == expected


def test_get_adapter_resolves_html_scraper() -> None:
    mod = _base.get_adapter("html_scraper")
    assert mod.ADAPTER_NAME == "html_scraper"


def test_get_adapter_resolves_literature_curated() -> None:
    mod = _base.get_adapter("literature_curated")
    assert mod.ADAPTER_NAME == "literature_curated"


def test_get_adapter_rejects_unknown() -> None:
    with pytest.raises(_base.AdapterError, match="unknown adapter"):
        _base.get_adapter("definitely_not_an_adapter")


# ──────────────────────────────────────────────────────────────────────
# html_scraper — fixture parse
# ──────────────────────────────────────────────────────────────────────


def test_html_scraper_parse_against_fixture(
    html_scraper_descriptor_path: Path,
) -> None:
    """html_scraper.parse extracts rows from a small fixture HTML
    matching the fixture descriptor's [parse] field-map."""
    pytest.importorskip("bs4")
    fixture = b"""<html><body>
        <table class="sc_main">
        <tr class="sc_row">
            <td class="name">Mauna Loa</td>
            <td class="lat">19.475</td>
            <td class="lon">-155.608</td>
            <td class="depth">0.0</td>
            <td class="height">9170.0</td>
        </tr>
        <tr class="sc_row">
            <td class="name">Loihi Seamount</td>
            <td class="lat">18.92</td>
            <td class="lon">-155.27</td>
            <td class="depth">975.0</td>
            <td class="height">3000.0</td>
        </tr>
        </table>
    </body></html>"""
    descriptor = load_descriptor(html_scraper_descriptor_path)
    rows = list(html_scraper.parse(fixture, descriptor))
    assert len(rows) == 2
    assert rows[0]["name"] == "Mauna Loa"
    assert rows[0]["latitude_deg"] == pytest.approx(19.475)
    assert rows[1]["name"] == "Loihi Seamount"


# ──────────────────────────────────────────────────────────────────────
# Stub adapters (netcdf_grid / geotiff_bbox)
# ──────────────────────────────────────────────────────────────────────


def test_netcdf_grid_stub_raises_without_extra(
    html_scraper_descriptor_path: Path,
) -> None:
    """netcdf_grid is a stub in v0.1.0; fetching raises AdapterError."""
    descriptor = load_descriptor(html_scraper_descriptor_path)
    with pytest.raises(_base.AdapterError, match="collector-netcdf"):
        # Force exhaustion since the iterator may lazy-raise.
        list(netcdf_grid.fetch(descriptor))


def test_geotiff_bbox_stub_raises_without_extra(
    html_scraper_descriptor_path: Path,
) -> None:
    """geotiff_bbox is a stub in v0.1.0; fetching raises AdapterError."""
    descriptor = load_descriptor(html_scraper_descriptor_path)
    with pytest.raises(_base.AdapterError, match="collector-geotiff"):
        list(geotiff_bbox.fetch(descriptor))


# ──────────────────────────────────────────────────────────────────────
# _base.attest — shared attestation block
# ──────────────────────────────────────────────────────────────────────


def test_attest_produces_all_required_fields(
    html_scraper_descriptor_path: Path,
) -> None:
    """The attest() composer produces every MANDATORY_ATTESTATION_FIELDS key."""
    import datetime as dt

    from srmech.amsc.format import MANDATORY_ATTESTATION_FIELDS

    descriptor = load_descriptor(html_scraper_descriptor_path)
    rule_hash = _base.parser_rule_hash(descriptor.parse)
    attestation = _base.attest(
        b"<html/>",
        descriptor,
        parser_version="srmech-test",
        parser_rule_hash=rule_hash,
        retrieved_at=dt.datetime(2026, 5, 13, 14, 23, 11, tzinfo=dt.timezone.utc),
    )
    for required in MANDATORY_ATTESTATION_FIELDS:
        assert required in attestation, f"missing {required}"
        assert attestation[required], f"empty {required}"


def test_parser_rule_hash_deterministic(
    html_scraper_descriptor_path: Path,
) -> None:
    """parser_rule_hash is stable across repeated calls on the same input."""
    descriptor = load_descriptor(html_scraper_descriptor_path)
    h1 = _base.parser_rule_hash(descriptor.parse)
    h2 = _base.parser_rule_hash(descriptor.parse)
    assert h1 == h2
    assert len(h1) == 64
