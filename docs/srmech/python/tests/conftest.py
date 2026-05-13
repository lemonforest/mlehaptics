"""Shared pytest fixtures for srmech tests.

Each fixture builds a minimal self-contained descriptor.toml so the
tests don't depend on any external catalog SSOT (ephemerides-spectral
or otherwise). The shape mirrors the real EarthRef SC descriptor so
the html_scraper parse test exercises the same field-map structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Mirror of EarthRef SC's html_scraper descriptor — self-contained,
# usable from tmp_path without touching any external catalog.
_HTML_SCRAPER_DESCRIPTOR_TOML = """\
[source]
key = "fixture_sc"
human_readable_name = "Fixture Seamount Catalog"
purpose = "fixture ground-proof rows for srmech tests"
license = "CC-BY-4.0"
homepage = "https://example.com/SC/"
canonical_doi = "10.1029/test"

[fetch]
adapter = "html_scraper"
endpoint = "https://example.com/SC/catalog?page={page}"
rate_limit_rps = 0.5
robots_txt_compliant = true

[fetch.pagination]
type = "page_query"
start = 1
end_detected_by = "empty_page"

[parse]
table_selector = "table.sc_main"
row_selector = "tr.sc_row"
field_map = [
    { canonical = "name",          selector = "td.name",  type = "string" },
    { canonical = "latitude_deg",  selector = "td.lat",   type = "float"  },
    { canonical = "longitude_deg", selector = "td.lon",   type = "float"  },
    { canonical = "summit_depth_m", selector = "td.depth", type = "float" },
    { canonical = "summit_height_m", selector = "td.height", type = "float" },
]

[schema]
data_schema_id = "fixture_sc.seamount.v1"
data_schema_path = "seamount.schema.json"

[rendering]
cite_as_template = "Fixture Catalog; retrieved {retrieved_at:%Y-%m-%d}."
purpose_template = "fixture ground-proof row for {schema.regime_label} regime"

[attestation]
hash_response = true
hash_algorithm = "sha256"
required_fields = [
    "source_doi",
    "source_url",
    "license",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "parser_rule_hash",
    "collector_descriptor_path",
    "collector_descriptor_hash",
]

[gap_targeting]
regime_labels = ["bounded_local_laplacian_trajectory"]
"""


@pytest.fixture
def html_scraper_descriptor_path(tmp_path: Path) -> Path:
    """A self-contained html_scraper descriptor at
    ``tmp_path / "fixture_sc" / "descriptor.toml"``.

    Mirrors EarthRef SC's shape so the html_scraper parse test
    exercises the same five-field-map structure as in production.
    """
    catalog_dir = tmp_path / "fixture_sc"
    catalog_dir.mkdir()
    desc_path = catalog_dir / "descriptor.toml"
    desc_path.write_text(_HTML_SCRAPER_DESCRIPTOR_TOML, encoding="utf-8")
    return desc_path


@pytest.fixture
def attested_root_with_one_catalog(tmp_path: Path) -> Path:
    """A complete attested-root directory with one descriptor in it,
    suitable for `register_attested_root` tests.
    """
    catalog_dir = tmp_path / "fixture_sc"
    catalog_dir.mkdir()
    desc_path = catalog_dir / "descriptor.toml"
    desc_path.write_text(_HTML_SCRAPER_DESCRIPTOR_TOML, encoding="utf-8")
    return tmp_path
