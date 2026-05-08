"""Orchestrator for ephemerides-spectral codegen.

Reads the package version from ``../python/pyproject.toml`` (the single
source of truth) and emits the frozen-data manifest with the per-file
SHA-256 sums of every research module shipped in the wheel.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore

import emit_attested_collections
import emit_research_modules
import emit_initial_phases
from _paths import ATTESTED_DST, DATA_DIR, PACKAGE_ROOT

_PYPROJECT: Path = Path(__file__).resolve().parents[1] / "python" / "pyproject.toml"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _package_version() -> str:
    """SSOT for the package version.

    Reads ``[project].version`` from pyproject.toml so the manifest,
    the wheel metadata, and ``ephemerides_spectral.version.__version__``
    can never disagree.
    """
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}

    print("copying research modules ...")
    research_paths = emit_research_modules.emit()
    for p in research_paths:
        # Manifest keys are paths relative to the package root, so
        # nested subdirectories (v0.25.0+ attested_adapters/) get
        # stable per-file keys regardless of depth.
        rel = p.relative_to(PACKAGE_ROOT).as_posix()
        written[rel] = p

    print("copying attested-data subtree ...")
    attested_paths = emit_attested_collections.emit()
    for p in attested_paths:
        rel = p.relative_to(PACKAGE_ROOT).as_posix()
        written[rel] = p

    print("emitting initial-phases JSON (SPICE-free BIP fallback) ...")
    init_phases_path = emit_initial_phases.emit()
    written[f"_data/{init_phases_path.name}"] = init_phases_path

    print("writing manifest ...")
    manifest = {
        "package": "ephemerides-spectral",
        "version": _package_version(),
        "files": {
            name: {"size_bytes": p.stat().st_size, "sha256": _sha256(p)}
            for name, p in sorted(written.items())
        },
    }
    manifest_path = DATA_DIR / "manifest.json"
    manifest_path.write_bytes(
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(f"done; {len(written)} files written.")
    print(f"package version: {manifest['version']}")


if __name__ == "__main__":
    main()
