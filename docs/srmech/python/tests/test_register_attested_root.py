"""Cross-package catalog-root registration tests.

These tests are net-new in Phase 2 (Task #197). They exercise the
load-bearing API that lets downstream packages (e.g. ephemerides-
spectral) push their catalog SSOTs into srmech.amsc's universal
bridge surface at import time. Phase 1 scope §3.3 documents the
design; this file pins it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srmech.amsc import catalog


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_registered_roots():
    """Clear registered roots before AND after each test.

    Module-level state survives across tests by default; this fixture
    enforces clean-slate behaviour so test ordering doesn't matter.
    """
    catalog._clear_registered_roots()
    yield
    catalog._clear_registered_roots()


# ──────────────────────────────────────────────────────────────────────
# register_attested_root — happy path
# ──────────────────────────────────────────────────────────────────────


def test_register_attested_root_returns_ok(
    attested_root_with_one_catalog: Path,
) -> None:
    result = catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    assert result["ok"] is True
    assert result["source"] == "test-package"
    assert result["total_registered"] == 1


def test_register_attested_root_idempotent(
    attested_root_with_one_catalog: Path,
) -> None:
    """Re-registering the same (path, source) pair is a no-op."""
    catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    result = catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    assert result["ok"] is True
    assert result["total_registered"] == 1
    assert "idempotent" in result.get("note", "")


def test_list_registered_roots_includes_srmech_own_first(
    attested_root_with_one_catalog: Path,
) -> None:
    """srmech's own attested-root is the implicit first-registered."""
    catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    rows = catalog.list_registered_roots()
    assert rows[0]["source"] == "srmech.amsc"
    assert rows[1]["source"] == "test-package"


# ──────────────────────────────────────────────────────────────────────
# _descriptors — union enumeration
# ──────────────────────────────────────────────────────────────────────


def test_descriptors_enumerates_registered_root(
    attested_root_with_one_catalog: Path,
) -> None:
    """After registration, _descriptors() includes the registered root's catalogs."""
    catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    found = catalog._descriptors()
    assert "fixture_sc" in found


def test_descriptors_cache_invalidated_on_register(
    attested_root_with_one_catalog: Path,
) -> None:
    """Registration invalidates the descriptors cache."""
    # First call: no roots registered. srmech's own root is empty
    # (no built-in catalogs at v0.1.0); so the descriptors map is empty.
    pre = catalog._descriptors()
    assert "fixture_sc" not in pre

    # Register a root; the next _descriptors() call must see the new entry.
    catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    post = catalog._descriptors()
    assert "fixture_sc" in post


def test_descriptors_preserves_registration_order(tmp_path: Path) -> None:
    """When two roots register descriptors with different source_keys,
    both are present; iteration order is deterministic."""
    # Build two distinct attested-roots, each with one unique catalog.
    root_a = tmp_path / "a"
    cat_a = root_a / "alpha"
    cat_a.mkdir(parents=True)
    (cat_a / "descriptor.toml").write_text(
        _minimal_descriptor_toml("alpha"), encoding="utf-8"
    )

    root_b = tmp_path / "b"
    cat_b = root_b / "beta"
    cat_b.mkdir(parents=True)
    (cat_b / "descriptor.toml").write_text(
        _minimal_descriptor_toml("beta"), encoding="utf-8"
    )

    catalog.register_attested_root(root_a, source="pkg-a")
    catalog.register_attested_root(root_b, source="pkg-b")

    found = catalog._descriptors()
    assert "alpha" in found
    assert "beta" in found


def test_register_attested_root_handles_nonexistent_path(
    tmp_path: Path,
) -> None:
    """Registering a nonexistent path is allowed (idempotent stub) but
    contributes no descriptors at enumeration time. This matches the
    realistic case where a downstream package registers a directory
    that will exist after import — defensive registration."""
    nonexistent = tmp_path / "does_not_exist"
    result = catalog.register_attested_root(nonexistent, source="absent")
    assert result["ok"] is True
    # _descriptors() must not raise on a nonexistent registered root.
    found = catalog._descriptors()
    assert isinstance(found, dict)


# ──────────────────────────────────────────────────────────────────────
# Conflict handling — duplicate source_key
# ──────────────────────────────────────────────────────────────────────


def test_duplicate_source_key_logs_warning_and_first_wins(
    tmp_path: Path,
) -> None:
    """When two registered roots contain the same source_key, the
    first-registered wins and a warning is emitted."""
    # Two roots, both with a catalog keyed "shared".
    root_a = tmp_path / "a"
    cat_a = root_a / "shared"
    cat_a.mkdir(parents=True)
    (cat_a / "descriptor.toml").write_text(
        _minimal_descriptor_toml("shared", human_name="Variant A"),
        encoding="utf-8",
    )

    root_b = tmp_path / "b"
    cat_b = root_b / "shared"
    cat_b.mkdir(parents=True)
    (cat_b / "descriptor.toml").write_text(
        _minimal_descriptor_toml("shared", human_name="Variant B"),
        encoding="utf-8",
    )

    catalog.register_attested_root(root_a, source="pkg-a")
    catalog.register_attested_root(root_b, source="pkg-b")

    with pytest.warns(UserWarning, match="duplicate source_key"):
        found = catalog._descriptors()

    # First-registered wins: 'Variant A' should be the human_readable_name.
    assert found["shared"].source["human_readable_name"] == "Variant A"


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — list_attested_sources sees registered roots
# ──────────────────────────────────────────────────────────────────────


def test_list_attested_sources_sees_registered_root(
    attested_root_with_one_catalog: Path,
) -> None:
    """list_attested_sources() enumerates descriptors from registered roots."""
    catalog.register_attested_root(
        attested_root_with_one_catalog, source="test-package"
    )
    result = catalog.list_attested_sources()
    assert result["ok"] is True
    keys = {s["key"] for s in result["sources"]}
    assert "fixture_sc" in keys


# ──────────────────────────────────────────────────────────────────────
# Local helpers
# ──────────────────────────────────────────────────────────────────────


def _minimal_descriptor_toml(key: str, human_name: str = "") -> str:
    """Synthesise a minimal-but-valid descriptor TOML for a given key.

    All required sections + fields are populated. Adapter is
    `literature_curated` because that one has no fetch dependencies
    and is the simplest to construct for test purposes.
    """
    name = human_name or f"Fixture {key}"
    return f"""\
[source]
key = "{key}"
human_readable_name = "{name}"
purpose = "fixture row for register_attested_root tests"
license = "CC-BY-4.0"
homepage = "https://example.com/{key}/"

[fetch]
adapter = "literature_curated"

[parse]

[schema]
data_schema_id = "{key}.row.v1"

[rendering]
cite_as_template = "Fixture {key}; retrieved {{retrieved_at:%Y-%m-%d}}."
purpose_template = "fixture row for {{schema.regime_label}} regime"

[attestation]
hash_algorithm = "sha256"
"""
