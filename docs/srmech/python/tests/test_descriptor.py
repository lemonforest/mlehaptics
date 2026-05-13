"""Descriptor module tests — TOML loading, template rendering, hashing.

Ported from
``docs/antikythera-maths/ephemerides-spectral/python/tests/test_attested_collector.py``
(Descriptor module section) at Phase 2 of Task #197. The original
tests reference the real EarthRef SC descriptor in ephemerides's
``_research/attested/``; srmech-isolation tests use the self-contained
``html_scraper_descriptor_path`` fixture from conftest.py instead.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from srmech.amsc.descriptor import (
    Descriptor,
    DescriptorValidationError,
    descriptor_hash,
    discover_descriptors,
    load_descriptor,
    render_template,
)


# ──────────────────────────────────────────────────────────────────────
# load_descriptor
# ──────────────────────────────────────────────────────────────────────


def test_load_descriptor_fixture(html_scraper_descriptor_path: Path) -> None:
    """The self-contained html_scraper descriptor parses cleanly."""
    descriptor = load_descriptor(html_scraper_descriptor_path)
    assert descriptor.key == "fixture_sc"
    assert descriptor.adapter_name == "html_scraper"
    assert descriptor.source["license"] == "CC-BY-4.0"


def test_load_descriptor_validates_gap_targeting(
    html_scraper_descriptor_path: Path,
) -> None:
    """Unknown regime labels are rejected when valid_regime_labels is supplied."""
    valid = {"some_other_regime": True}  # does not include 'bounded_local_laplacian_trajectory'
    with pytest.raises(DescriptorValidationError, match="unknown labels"):
        load_descriptor(
            html_scraper_descriptor_path,
            valid_regime_labels=valid,
        )


def test_load_descriptor_accepts_valid_regime_labels(
    html_scraper_descriptor_path: Path,
) -> None:
    """When the descriptor's regime labels are all in the valid set, load succeeds."""
    valid = {"bounded_local_laplacian_trajectory": True}
    descriptor = load_descriptor(
        html_scraper_descriptor_path, valid_regime_labels=valid
    )
    assert descriptor.gap_targeting["regime_labels"] == [
        "bounded_local_laplacian_trajectory"
    ]


def test_load_descriptor_missing_file() -> None:
    with pytest.raises(DescriptorValidationError, match="not found"):
        load_descriptor(Path("/nonexistent/descriptor.toml"))


def test_load_descriptor_missing_required_section(tmp_path: Path) -> None:
    """A descriptor missing a required top-level section is rejected."""
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[source]\nkey = "bad"\nhuman_readable_name = "x"\n'
        'purpose = "x"\nlicense = "x"\nhomepage = "x"\n',
        encoding="utf-8",
    )
    with pytest.raises(DescriptorValidationError, match="missing required section"):
        load_descriptor(bad)


def test_load_descriptor_rejects_unknown_adapter(tmp_path: Path) -> None:
    """A descriptor with an [fetch].adapter that's not in KNOWN_ADAPTERS is rejected."""
    bad = tmp_path / "bad.toml"
    bad.write_text(
        '[source]\nkey = "bad"\nhuman_readable_name = "x"\n'
        'purpose = "x"\nlicense = "x"\nhomepage = "x"\n'
        '[fetch]\nadapter = "definitely_not_an_adapter"\n'
        '[parse]\n[schema]\ndata_schema_id = "x.row.v1"\n'
        '[rendering]\ncite_as_template = "x"\npurpose_template = "x"\n'
        '[attestation]\n',
        encoding="utf-8",
    )
    with pytest.raises(DescriptorValidationError, match="unknown adapter"):
        load_descriptor(bad)


# ──────────────────────────────────────────────────────────────────────
# render_template
# ──────────────────────────────────────────────────────────────────────


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
        {"retrieved_at": dt.datetime(2026, 5, 13)},
    )
    assert out == "retrieved 2026-05-13"


def test_render_template_missing_key_returns_empty() -> None:
    """Missing context keys resolve to empty string (no KeyError)."""
    out = render_template("hello {missing_key}", {})
    assert out == "hello "


# ──────────────────────────────────────────────────────────────────────
# descriptor_hash
# ──────────────────────────────────────────────────────────────────────


def test_descriptor_hash_deterministic(
    html_scraper_descriptor_path: Path,
) -> None:
    """Hash is stable across repeated reads (canonical serialisation)."""
    h1 = descriptor_hash(html_scraper_descriptor_path)
    h2 = descriptor_hash(html_scraper_descriptor_path)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


# ──────────────────────────────────────────────────────────────────────
# discover_descriptors
# ──────────────────────────────────────────────────────────────────────


def test_discover_descriptors_walks_attested_root(
    attested_root_with_one_catalog: Path,
) -> None:
    """Walking an attested-root surfaces every committed descriptor."""
    found = discover_descriptors(attested_root_with_one_catalog)
    assert sorted(found.keys()) == ["fixture_sc"]


def test_discover_descriptors_handles_empty_root(tmp_path: Path) -> None:
    """An attested-root with no descriptors returns an empty dict."""
    assert discover_descriptors(tmp_path) == {}


def test_discover_descriptors_skips_non_directories(tmp_path: Path) -> None:
    """Stray files at the attested-root level are skipped."""
    (tmp_path / "stray.txt").write_text("ignore me", encoding="utf-8")
    assert discover_descriptors(tmp_path) == {}


def test_discover_descriptors_skips_subdirs_without_descriptor(
    tmp_path: Path,
) -> None:
    """A subdir without descriptor.toml is skipped (no error)."""
    (tmp_path / "empty_subdir").mkdir()
    assert discover_descriptors(tmp_path) == {}
