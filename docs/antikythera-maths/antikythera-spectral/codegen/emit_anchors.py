"""Emit ``_data/anchors.json`` from ``research.hellenistic_eclipses``.

Two SSOT lists:

- ``HELLENISTIC_ANCHORS`` — six well-attested Almagest IV-VI anchors
  (-382 .. +125 CE), used by E-H1b.
- ``MODERN_SAROS_ANCHORS`` — modern controls used by E-H1a.

Each anchor is an ``EclipseAnchor`` dataclass with full citations.

Run::

    python codegen/emit_anchors.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from _paths import DATA_DIR, ensure_research_importable

ensure_research_importable()
from research.hellenistic_eclipses import (  # noqa: E402
    HELLENISTIC_ANCHORS,
    MODERN_SAROS_ANCHORS,
)


def anchor_to_dict(a: Any) -> Dict[str, Any]:
    """Serialize one ``EclipseAnchor`` to a JSON-compatible dict."""
    return asdict(a)


def emit() -> Path:
    out_path = DATA_DIR / "anchors.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "source_module": "research.hellenistic_eclipses",
        "n_hellenistic": len(HELLENISTIC_ANCHORS),
        "n_modern": len(MODERN_SAROS_ANCHORS),
        "hellenistic": [anchor_to_dict(a) for a in HELLENISTIC_ANCHORS],
        "modern": [anchor_to_dict(a) for a in MODERN_SAROS_ANCHORS],
    }

    out_path.write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return out_path


if __name__ == "__main__":
    p = emit()
    print(
        f"wrote {p} ({p.stat().st_size} bytes; "
        f"{len(HELLENISTIC_ANCHORS)} hellenistic + {len(MODERN_SAROS_ANCHORS)} modern anchors)"
    )
