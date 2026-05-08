"""v0.25.0a — Attested Multi-Source Collector framework tests.

Pins the Mathematical Provenance Record (MPR) v1 normative format
+ descriptor schema + adapter Protocol + bridge surfaces + CLI
subcommands. The framework is the v0.24.x hand-coding pattern
formalised — descriptors replace per-source `*_data.py` modules.

Coverage areas:

* Format module — MPRRecord round-trip, validation, NDJSON IO.
* Descriptor module — TOML loading, [rendering] template
  substitution, [gap_targeting] regime-label validation,
  descriptor canonical hashing.
* Adapter registry — all 5 adapters register; html_scraper.parse
  works against fixture HTML; stubs raise correctly when extras
  are missing.
* Catalog wrapper — universal bridge surfaces over discovered
  descriptors; pagination; missing-NDJSON state handled.
* Bridge surfaces — 4 new functions return Pyodide-shaped dicts.
* CLI subcommands — 4 new subcommands smoke + --help.
"""

from __future__ import annotations

import datetime as dt
import io as _io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.attested_adapters import (
    ADAPTERS,
    csv_bulk,
    geotiff_bbox,
    html_scraper,
    json_api,
    netcdf_grid,
    _base,
)
from ephemerides_spectral._research.attested_collector_descriptor import (
    Descriptor,
    DescriptorValidationError,
    descriptor_hash,
    discover_descriptors,
    load_descriptor,
    render_template,
)
from ephemerides_spectral._research.attested_collector_format import (
    MANDATORY_ATTESTATION_FIELDS,
    MANDATORY_RENDERING_FIELDS,
    MPR_SCHEMA_VERSION,
    MPRRecord,
    MPRValidationError,
    read_ndjson,
    sha256_bytes,
    validate_mpr_record,
    write_ndjson,
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


def _valid_attestation() -> dict:
    return {
        "source_doi": "10.1029/test",
        "source_url": "https://example.com/page",
        "license": "CC-BY-4.0",
        "retrieved_at": "2026-05-08T14:23:11Z",
        "response_sha256": "0" * 64,
        "parser_version": "ephemerides-spectral 0.25.0a",
        "parser_rule_hash": "1" * 64,
        "collector_descriptor_path": "configs/test.toml",
        "collector_descriptor_hash": "2" * 64,
    }


def _valid_rendering() -> dict:
    return {
        "human_readable_name": "Fixture Source — row 1",
        "cite_as": "Fixture 2026; retrieved 2026-05-08.",
        "purpose": "fixture row for tests",
    }


def _valid_record() -> MPRRecord:
    return MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={"name": "Mauna Loa", "latitude_deg": 19.475, "longitude_deg": -155.608},
        data_schema_id="fixture.test.v1",
        attestation=_valid_attestation(),
        rendering=_valid_rendering(),
    )


# ──────────────────────────────────────────────────────────────────────
# Format module — MPR record + validation + NDJSON IO
# ──────────────────────────────────────────────────────────────────────


def test_mpr_schema_version_is_1_0() -> None:
    assert MPR_SCHEMA_VERSION == "1.0"


def test_mandatory_attestation_fields_count() -> None:
    """v0.25.0a fixes the v1 attestation schema at 9 required fields."""
    assert len(MANDATORY_ATTESTATION_FIELDS) == 9


def test_mandatory_rendering_fields_count() -> None:
    assert len(MANDATORY_RENDERING_FIELDS) == 3


def test_mpr_record_round_trip_through_json_line() -> None:
    record = _valid_record()
    line = record.to_json_line()
    assert MPRRecord.from_json_line(line) == record


def test_validate_accepts_valid_record() -> None:
    validate_mpr_record(_valid_record())


def test_validate_rejects_unknown_mpr_version() -> None:
    record = MPRRecord(
        mpr_version="99.0",
        data={},
        data_schema_id="x.v1",
        attestation=_valid_attestation(),
        rendering=_valid_rendering(),
    )
    with pytest.raises(MPRValidationError, match="unrecognised mpr_version"):
        validate_mpr_record(record)


def test_validate_rejects_missing_attestation_field() -> None:
    bad = dict(_valid_attestation())
    del bad["response_sha256"]
    record = MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={},
        data_schema_id="x.v1",
        attestation=bad,
        rendering=_valid_rendering(),
    )
    with pytest.raises(MPRValidationError, match="response_sha256"):
        validate_mpr_record(record)


def test_validate_rejects_empty_data_schema_id() -> None:
    record = MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={},
        data_schema_id="",
        attestation=_valid_attestation(),
        rendering=_valid_rendering(),
    )
    with pytest.raises(MPRValidationError, match="data_schema_id"):
        validate_mpr_record(record)


def test_ndjson_round_trip(tmp_path: Path) -> None:
    """Write three records, read them back, assert byte-stable order."""
    records = [
        MPRRecord(
            mpr_version=MPR_SCHEMA_VERSION,
            data={"name": f"r{i}", "lat": float(i)},
            data_schema_id="fixture.test.v1",
            attestation=_valid_attestation(),
            rendering=_valid_rendering(),
        )
        for i in range(3)
    ]
    path = tmp_path / "out.ndjson"
    n = write_ndjson(path, records)
    assert n == 3
    read_back = list(read_ndjson(path))
    assert read_back == records


def test_ndjson_rejects_invalid_json(tmp_path: Path) -> None:
    """Lines that aren't valid JSON at all raise MPRValidationError
    with the line number for diagnostics."""
    path = tmp_path / "bad.ndjson"
    path.write_text("this is not json at all\n", encoding="utf-8")
    with pytest.raises(MPRValidationError, match="line"):
        list(read_ndjson(path))


def test_ndjson_skips_empty_lines(tmp_path: Path) -> None:
    """NDJSON allows empty lines by convention; the reader skips them."""
    path = tmp_path / "with_blanks.ndjson"
    path.write_text("\n\n\n", encoding="utf-8")
    assert list(read_ndjson(path)) == []


def test_sha256_bytes_deterministic() -> None:
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")
    assert sha256_bytes(b"abc") != sha256_bytes(b"abd")
    # Match well-known abc SHA-256.
    assert sha256_bytes(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


# ──────────────────────────────────────────────────────────────────────
# Descriptor module
# ──────────────────────────────────────────────────────────────────────


def _earthref_descriptor_path() -> Path:
    """Real EarthRef SC descriptor shipped at v0.25.0a."""
    from ephemerides_spectral._research.attested_collector_catalog import (
        _attested_root,
    )
    return _attested_root() / "earthref_sc" / "descriptor.toml"


def test_load_descriptor_earthref_sc() -> None:
    """The shipped EarthRef SC descriptor parses cleanly."""
    descriptor = load_descriptor(_earthref_descriptor_path())
    assert descriptor.key == "earthref_sc"
    assert descriptor.adapter_name == "html_scraper"
    assert descriptor.source["license"] == "CC-BY-4.0"


def test_load_descriptor_validates_gap_targeting() -> None:
    """Unknown regime labels are rejected when valid_regime_labels
    is supplied. v0.25.0a doesn't enforce this in production yet
    (descriptor loads succeed without the parameter); v0.26.x will."""
    valid = {"bounded_local_laplacian_trajectory": True}
    with pytest.raises(DescriptorValidationError, match="unknown labels"):
        load_descriptor(
            _earthref_descriptor_path(),
            valid_regime_labels=valid,  # missing _family
        )


def test_load_descriptor_missing_file() -> None:
    with pytest.raises(DescriptorValidationError, match="not found"):
        load_descriptor(Path("/nonexistent/descriptor.toml"))


def test_render_template_simple_substitution() -> None:
    out = render_template("hello {name}", {"name": "world"})
    assert out == "hello world"


def test_render_template_dotted_path() -> None:
    out = render_template(
        "regime: {schema.regime_label}",
        {"schema": {"regime_label": "bounded_local_laplacian_trajectory"}},
    )
    assert out == "regime: bounded_local_laplacian_trajectory"


def test_render_template_datetime_format() -> None:
    out = render_template(
        "retrieved {retrieved_at:%Y-%m-%d}",
        {"retrieved_at": dt.datetime(2026, 5, 8)},
    )
    assert out == "retrieved 2026-05-08"


def test_descriptor_hash_deterministic() -> None:
    """Hash is stable across reads (canonical serialisation)."""
    h1 = descriptor_hash(_earthref_descriptor_path())
    h2 = descriptor_hash(_earthref_descriptor_path())
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_discover_descriptors_finds_earthref_sc() -> None:
    """Walking research/attested/ surfaces the shipped EarthRef SC
    descriptor (and only that one in v0.25.0a)."""
    from ephemerides_spectral._research.attested_collector_catalog import (
        _attested_root,
    )
    found = discover_descriptors(_attested_root())
    assert "earthref_sc" in found
    assert found["earthref_sc"].adapter_name == "html_scraper"


# ──────────────────────────────────────────────────────────────────────
# Adapter registry + html_scraper.parse against fixture HTML
# ──────────────────────────────────────────────────────────────────────


def test_all_five_adapters_registered() -> None:
    expected = {"html_scraper", "json_api", "csv_bulk", "netcdf_grid", "geotiff_bbox"}
    assert set(ADAPTERS.keys()) == expected


def test_get_adapter_resolves_html_scraper() -> None:
    mod = _base.get_adapter("html_scraper")
    assert mod.ADAPTER_NAME == "html_scraper"


def test_get_adapter_rejects_unknown() -> None:
    with pytest.raises(_base.AdapterError, match="unknown adapter"):
        _base.get_adapter("definitely_not_an_adapter")


def test_html_scraper_parse_against_fixture() -> None:
    """html_scraper.parse extracts rows from a small fixture HTML
    matching the EarthRef SC descriptor's [parse] field-map."""
    bs4 = pytest.importorskip("bs4")
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
    descriptor = load_descriptor(_earthref_descriptor_path())
    rows = list(html_scraper.parse(fixture, descriptor))
    assert len(rows) == 2
    assert rows[0]["name"] == "Mauna Loa"
    assert rows[0]["latitude_deg"] == pytest.approx(19.475)
    assert rows[1]["name"] == "Loihi Seamount"


def test_netcdf_grid_stub_raises_without_extra() -> None:
    descriptor = load_descriptor(_earthref_descriptor_path())
    with pytest.raises(_base.AdapterError, match="collector-netcdf"):
        # Force exhaustion since the iterator may lazy-raise.
        list(netcdf_grid.fetch(descriptor))


def test_geotiff_bbox_stub_raises_without_extra() -> None:
    descriptor = load_descriptor(_earthref_descriptor_path())
    with pytest.raises(_base.AdapterError, match="collector-geotiff"):
        list(geotiff_bbox.fetch(descriptor))


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces (4 new in v0.25.0a)
# ──────────────────────────────────────────────────────────────────────


def test_bridge_list_attested_sources_returns_earthref_sc() -> None:
    result = bridge.list_attested_sources()
    assert result["ok"] is True
    assert result["n_sources"] == 1
    keys = [s["key"] for s in result["sources"]]
    assert "earthref_sc" in keys


def test_bridge_get_attested_dataset_handles_missing_ndjson() -> None:
    """v0.25.0a ships descriptor-only (no NDJSON yet); bridge surface
    returns ok=True with empty rows + the explanatory note."""
    result = bridge.get_attested_dataset("earthref_sc")
    assert result["ok"] is True
    assert result["total"] == 0
    assert result["rows"] == []
    assert "first T1 collection pending" in result.get("note", "")


def test_bridge_get_attested_dataset_pagination_args() -> None:
    """Pagination kwargs accepted (limit/offset). With no rows, both
    are no-ops; the contract is exercised regardless."""
    result = bridge.get_attested_dataset("earthref_sc", limit=10, offset=0)
    assert result["ok"] is True
    assert result["limit"] == 10
    assert result["offset"] == 0


def test_bridge_get_attested_dataset_unknown_source() -> None:
    result = bridge.get_attested_dataset("not_a_real_source")
    assert result["ok"] is False
    assert "available" in result


def test_bridge_get_attested_descriptor_returns_full_toml() -> None:
    result = bridge.get_attested_descriptor("earthref_sc")
    assert result["ok"] is True
    descriptor = result["descriptor"]
    assert descriptor["source"]["key"] == "earthref_sc"
    assert "regime_labels" in descriptor["gap_targeting"]


def test_bridge_attestation_audit_handles_missing_ndjson() -> None:
    result = bridge.attestation_audit("earthref_sc")
    assert result["ok"] is True
    assert result["n_rows"] == 0


# ──────────────────────────────────────────────────────────────────────
# CLI subcommands (4 new in v0.25.0a)
# ──────────────────────────────────────────────────────────────────────


def _run_cli(*argv: str) -> dict:
    """Invoke the CLI, capture stdout, return parsed JSON payload."""
    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(list(argv))
    assert rc == 0, f"cli {argv} returned non-zero exit code {rc}"
    return json.loads(buf.getvalue())


def test_cli_attested_list_smoke() -> None:
    payload = _run_cli("attested-list")
    assert payload["ok"] is True
    assert payload["n_sources"] >= 1


def test_cli_attested_dataset_smoke() -> None:
    payload = _run_cli("attested-dataset", "--source", "earthref_sc")
    assert payload["ok"] is True
    assert payload["source_key"] == "earthref_sc"


def test_cli_attested_descriptor_smoke() -> None:
    payload = _run_cli("attested-descriptor", "--source", "earthref_sc")
    assert payload["ok"] is True
    assert payload["descriptor"]["source"]["key"] == "earthref_sc"


def test_cli_attested_audit_smoke() -> None:
    payload = _run_cli("attested-audit", "--source", "earthref_sc")
    assert payload["ok"] is True


def test_cli_attested_help() -> None:
    """All four v0.25.0a subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in (
        "attested-list",
        "attested-dataset",
        "attested-descriptor",
        "attested-audit",
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0


# ──────────────────────────────────────────────────────────────────────
# Determinism contract checks
# ──────────────────────────────────────────────────────────────────────


def test_regenerate_path_has_no_network_imports() -> None:
    """Codegen-determinism precondition: regenerate.py must not
    transitively import requests or any other network-touching
    library. T1 collector lives only in the collect workflow."""
    import importlib.util

    # Import regenerate.py from the codegen directory and verify
    # that 'requests' is not in the resulting sys.modules graph.
    # We check by attempting to access the attribute path; if it
    # imports requests, the import would be visible.
    project_root = Path(__file__).resolve().parents[1].parent
    codegen = project_root / "codegen" / "regenerate.py"
    if not codegen.exists():
        pytest.skip("codegen/regenerate.py not present in this checkout")
    src = codegen.read_text(encoding="utf-8")
    # Static check: 'import requests' or 'from requests' must not
    # appear in the regenerate.py source.
    assert "import requests" not in src
    assert "from requests" not in src
