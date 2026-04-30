"""Orchestrator — run all codegen emitters, write provenance manifest.

Usage::

    python codegen/regenerate.py

Side effects:

- runs every ``emit_*.py`` script in this directory,
- writes ``_data/manifest.json`` carrying:
    - the package version (parsed from ``../python/pyproject.toml``),
    - the source-commit hash (from ``git rev-parse HEAD``; falls back
      to ``"unknown"`` if git is unavailable),
    - per-file SHA-256 sums of every output, so a downstream consumer
      can verify the wheel's data hasn't been tampered with,
- prints a one-line summary per emitter,
- exits non-zero if any emitter fails.

The orchestrator is deterministic: re-running it on the same source
state must produce byte-identical output. ``test_data_freshness.py``
asserts this by re-running the orchestrator into a temp directory and
comparing.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Dict

from _paths import DATA_DIR

import emit_anchors
import emit_basis_vectors
import emit_cycles
import emit_fragment_inventory
import emit_gears
import emit_periods
import emit_research_modules


def _git_commit() -> str:
    """Return the current HEAD commit hash, or ``'unknown'`` on failure.

    Wrapped in try/except because:

    - some CI runners do shallow checkouts where ``git`` works but
      certain rev-parses fail,
    - someone might run codegen from a release tarball with no .git.
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        return out or "unknown"
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return "unknown"


def _package_version() -> str:
    """Read the package version from pyproject.toml.

    Single source of truth for ``manifest.version``.
    """
    pyproject = Path(__file__).resolve().parents[1] / "python" / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return str(data["project"]["version"])


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("--- antikythera-spectral codegen ---")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    written: Dict[str, Path] = {}

    # Manifest keys are paths relative to the package root
    # (antikythera_spectral/), so callers can resolve them as
    # `PKG_ROOT / key` regardless of subdir.
    print("emitting cycles ...")
    written["_data/cycles.json"] = emit_cycles.emit()

    print("emitting gears ...")
    written["_data/gears.json"] = emit_gears.emit()

    print("emitting anchors ...")
    written["_data/anchors.json"] = emit_anchors.emit()

    print("emitting periods ...")
    written["_data/periods.json"] = emit_periods.emit()

    print("emitting fragments ...")
    written["_data/fragments.json"] = emit_fragment_inventory.emit()

    print("emitting basis vectors ...")
    basis_paths = emit_basis_vectors.emit()
    for D, p in basis_paths.items():
        # Manifest keys use paths relative to the package root so the test
        # can resolve them uniformly with PKG_ROOT / key.
        written[f"_data/{p.name}"] = p

    print("copying research modules into _research/ ...")
    research_paths = emit_research_modules.emit()
    for p in research_paths:
        written[f"_research/{p.name}"] = p

    print("writing manifest ...")
    manifest = {
        "schema_version": 2,
        "package": "antikythera-spectral",
        "version": _package_version(),
        "source_commit": _git_commit(),
        "files": {
            name: {
                "size_bytes": p.stat().st_size,
                "sha256": _sha256(p),
            }
            for name, p in sorted(written.items())
        },
    }
    manifest_path = DATA_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"--- done; {len(written)} files + manifest in {DATA_DIR} ---")
    print(f"package version: {manifest['version']}")
    print(f"source commit:   {manifest['source_commit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
