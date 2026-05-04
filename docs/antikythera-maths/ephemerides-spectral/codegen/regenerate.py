"""Orchestrator for de441-spectral codegen."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

import emit_research_modules
from _paths import DATA_DIR

def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}

    print("copying research modules ...")
    research_paths = emit_research_modules.emit()
    for p in research_paths:
        written[f"_research/{p.name}"] = p

    print("writing manifest ...")
    manifest = {
        "package": "ephemerides-spectral",
        "version": "0.1.0",
        "files": {
            name: {"size_bytes": p.stat().st_size, "sha256": _sha256(p)}
            for name, p in sorted(written.items())
        },
    }
    manifest_path = DATA_DIR / "manifest.json"
    manifest_path.write_bytes((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(f"done; {len(written)} files written.")

if __name__ == "__main__":
    main()
