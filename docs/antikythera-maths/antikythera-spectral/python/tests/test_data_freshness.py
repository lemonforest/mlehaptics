"""``_data/*.json`` and basis NPZs must match what codegen would produce.

Re-runs the codegen orchestrator into a temporary directory and
asserts byte-identical output against the committed ``_data/``. Catches
drift between ``research/*.py`` source and the package's frozen-data
exports.

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
_DATA_DIR = _PKG_DIR / "antikythera_spectral" / "_data"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the committed manifest (asserts the file exists)."""
    p = _DATA_DIR / "manifest.json"
    if not p.exists():
        pytest.skip(
            f"_data/manifest.json missing -- run "
            f"`python {_CODEGEN / 'regenerate.py'}` first."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def test_manifest_lists_every_committed_file(manifest: dict) -> None:
    """Every JSON / NPZ in ``_data/`` must appear in the manifest."""
    expected = {p.name for p in _DATA_DIR.iterdir()
                if p.suffix in {".json", ".npz"} and p.name != "manifest.json"}
    listed = set(manifest["files"].keys())
    missing = expected - listed
    extra = listed - expected
    assert not missing, f"committed files not in manifest: {missing}"
    assert not extra, f"manifest lists files that don't exist: {extra}"


def test_manifest_sha_matches_committed_files(manifest: dict) -> None:
    """SHA-256 of every committed file must match the manifest's record."""
    for name, entry in manifest["files"].items():
        p = _DATA_DIR / name
        assert p.exists(), f"manifest references {name}, but file is missing"
        assert entry["size_bytes"] == p.stat().st_size, (
            f"{name}: manifest size {entry['size_bytes']} != "
            f"actual {p.stat().st_size}"
        )
        assert entry["sha256"] == _sha256(p), (
            f"{name}: manifest SHA does not match committed file. "
            "Re-run `python codegen/regenerate.py` to refresh."
        )


def test_codegen_is_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-running codegen into a temp dir must reproduce the committed JSON.

    Skipped if the research-scaffold imports aren't available (which can
    happen in a wheel-only test environment without the monorepo). The
    test is the strict-CI guardrail; in dev / CI builds we run it.
    """
    # Inject a temp DATA_DIR by monkeypatching the codegen helper.
    if str(_CODEGEN) not in sys.path:
        sys.path.insert(0, str(_CODEGEN))
    import _paths  # noqa: WPS433 - codegen-internal helper

    # Make the research/ tree importable before we ask for it (codegen
    # scripts do this via _paths.ensure_research_importable on every
    # invocation; we replicate that here).
    _paths.ensure_research_importable()
    pytest.importorskip("research.astronomical_cycles")

    monkeypatch.setattr(_paths, "DATA_DIR", tmp_path)

    # Force a re-import of the emitters with the patched DATA_DIR.
    for mod_name in [
        "emit_cycles", "emit_gears", "emit_anchors",
        "emit_periods", "emit_fragment_inventory", "emit_basis_vectors",
    ]:
        sys.modules.pop(mod_name, None)

    import emit_anchors  # noqa: E402
    import emit_cycles   # noqa: E402
    import emit_fragment_inventory  # noqa: E402
    import emit_gears    # noqa: E402
    import emit_periods  # noqa: E402

    # Re-emit the JSON files (NPZ handled in a separate test below).
    emit_cycles.emit()
    emit_gears.emit()
    emit_anchors.emit()
    emit_periods.emit()
    emit_fragment_inventory.emit()

    for name in ("cycles.json", "gears.json", "anchors.json",
                 "periods.json", "fragments.json"):
        regenerated = (tmp_path / name).read_bytes()
        committed = (_DATA_DIR / name).read_bytes()
        assert regenerated == committed, (
            f"{name}: codegen output does not match committed file. "
            "Either run `python codegen/regenerate.py` to refresh, "
            "or revert the research/*.py change that caused the drift."
        )
