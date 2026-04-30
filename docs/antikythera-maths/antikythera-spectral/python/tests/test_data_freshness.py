"""Committed ``_data/`` and ``_research/`` must match what codegen would produce.

Re-runs the codegen orchestrator and asserts byte-identical output
against the committed package state. Catches drift between
``research/*.py`` source and the package's frozen-data exports + the
copied research-module tree.

Run with::

    pytest python/tests/test_data_freshness.py -q
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

# Bring codegen scripts onto the path. They live at:
#   docs/antikythera-maths/antikythera-spectral/codegen/
# This test file is at:
#   docs/antikythera-maths/antikythera-spectral/python/tests/
_HERE = Path(__file__).resolve()
_PKG_DIR = _HERE.parents[1]
_PROJECT_ROOT = _PKG_DIR.parent
_CODEGEN = _PROJECT_ROOT / "codegen"
_PKG_ROOT = _PKG_DIR / "antikythera_spectral"
_DATA_DIR = _PKG_ROOT / "_data"
_RESEARCH_DIR = _PKG_ROOT / "_research"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the committed manifest (skips if missing)."""
    p = _DATA_DIR / "manifest.json"
    if not p.exists():
        pytest.skip(
            f"_data/manifest.json missing -- run "
            f"`python {_CODEGEN / 'regenerate.py'}` first."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def test_manifest_lists_every_committed_file(manifest: dict) -> None:
    """Every codegen-managed file must appear in the manifest."""
    expected: set[str] = set()
    # _data/*.json (excluding the manifest itself).
    for p in _DATA_DIR.iterdir():
        if p.suffix == ".json" and p.name != "manifest.json":
            expected.add(f"_data/{p.name}")
    # _research/*.py + README.md (codegen-emitted copies).
    if _RESEARCH_DIR.exists():
        for p in _RESEARCH_DIR.iterdir():
            if p.is_file():
                expected.add(f"_research/{p.name}")
    listed = set(manifest["files"].keys())
    missing = expected - listed
    extra = listed - expected
    assert not missing, f"committed files not in manifest: {missing}"
    assert not extra, f"manifest lists files that don't exist: {extra}"


def test_manifest_sha_matches_committed_files(manifest: dict) -> None:
    """SHA-256 of every committed file must match the manifest's record."""
    for rel_path, entry in manifest["files"].items():
        p = _PKG_ROOT / rel_path
        assert p.exists(), f"manifest references {rel_path}, but file is missing"
        assert entry["size_bytes"] == p.stat().st_size, (
            f"{rel_path}: manifest size {entry['size_bytes']} != "
            f"actual {p.stat().st_size}"
        )
        assert entry["sha256"] == _sha256(p), (
            f"{rel_path}: manifest SHA does not match committed file. "
            "Re-run `python codegen/regenerate.py` to refresh."
        )


def test_codegen_is_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-running codegen reproduces every committed file byte-identically.

    Skipped if the research-scaffold imports aren't available (which can
    happen in a wheel-only test environment without the monorepo).
    """
    if str(_CODEGEN) not in sys.path:
        sys.path.insert(0, str(_CODEGEN))
    import _paths  # noqa: WPS433 - codegen-internal helper

    _paths.ensure_research_importable()
    pytest.importorskip("research.astronomical_cycles")

    # Codegen writes to two roots: _DATA_DIR and _RESEARCH_DIR. To run a
    # clean re-emission we patch both, point them at tmp_path subtrees,
    # and then byte-compare against the committed copies.
    tmp_data = tmp_path / "_data"
    tmp_research = tmp_path / "_research"
    tmp_data.mkdir()
    tmp_research.mkdir()

    monkeypatch.setattr(_paths, "DATA_DIR", tmp_data)

    # Force a re-import of the emitters with the patched DATA_DIR.
    for mod_name in [
        "emit_cycles", "emit_gears", "emit_anchors",
        "emit_periods", "emit_fragment_inventory",
        "emit_research_modules", "emit_visibility_anchors",
    ]:
        sys.modules.pop(mod_name, None)

    import emit_anchors                 # noqa: E402
    import emit_cycles                  # noqa: E402
    import emit_fragment_inventory      # noqa: E402
    import emit_gears                   # noqa: E402
    import emit_periods                 # noqa: E402
    import emit_research_modules        # noqa: E402
    import emit_visibility_anchors      # noqa: E402

    # Patch _research_modules destination to the temp dir.
    monkeypatch.setattr(emit_research_modules, "_RESEARCH_DST", tmp_research)

    emit_cycles.emit()
    emit_gears.emit()
    emit_anchors.emit()
    emit_periods.emit()
    emit_fragment_inventory.emit()
    emit_visibility_anchors.emit()
    emit_research_modules.emit()

    for name in ("cycles.json", "gears.json", "anchors.json",
                 "periods.json", "fragments.json",
                 "visibility_anchors.json"):
        regenerated = (tmp_data / name).read_bytes()
        committed = (_DATA_DIR / name).read_bytes()
        assert regenerated == committed, (
            f"_data/{name}: codegen output does not match committed file."
        )

    if _RESEARCH_DIR.exists():
        for committed_path in _RESEARCH_DIR.iterdir():
            if not committed_path.is_file():
                continue
            regen_path = tmp_research / committed_path.name
            assert regen_path.exists(), (
                f"_research/{committed_path.name}: codegen failed to emit"
            )
            assert regen_path.read_bytes() == committed_path.read_bytes(), (
                f"_research/{committed_path.name}: codegen output does not match"
            )
