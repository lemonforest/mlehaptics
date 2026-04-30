"""Emit ``_data/gears.json`` from ``research.gear_database``.

Includes:

- ``ALL_GEARS`` — the union of MAIN_TRAIN + LUNAR_TRAIN + PLANETARY,
  each Gear serialized with its tooth-count dict (Freeth/Wright/Price),
  role, fragment, and notes.
- ``MESH_EDGES`` — the (gear_a, gear_b, axle_label?) DAG edges used by
  the periphery-rule analysis in research.gear_topology.
- The three reconstruction names as constants, so downstream code
  doesn't have to hard-code the strings.

Run::

    python codegen/emit_gears.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from _paths import DATA_DIR, ensure_research_importable

ensure_research_importable()
from research.gear_database import (  # noqa: E402
    ALL_GEARS,
    FREETH_2021,
    LUNAR_TRAIN,
    MAIN_TRAIN,
    MESH_EDGES,
    PLANETARY,
    PRICE_1974,
    WRIGHT,
)


def gear_to_dict(g: Any) -> Dict[str, Any]:
    """Serialize one ``Gear`` to a JSON-compatible dict."""
    return asdict(g)


def mesh_to_dict(edge: Any) -> Dict[str, Any]:
    """Serialize one MESH_EDGES entry (a 3-tuple) to a dict."""
    a, b, axle = edge
    return {"gear_a": a, "gear_b": b, "axle": axle}


def emit() -> Path:
    out_path = DATA_DIR / "gears.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "source_module": "research.gear_database",
        "reconstructions": [FREETH_2021, WRIGHT, PRICE_1974],
        "groups": {
            "main_train": [g.name for g in MAIN_TRAIN],
            "lunar_train": [g.name for g in LUNAR_TRAIN],
            "planetary": [g.name for g in PLANETARY],
        },
        "n_gears": len(ALL_GEARS),
        "n_mesh_edges": len(MESH_EDGES),
        "gears": [gear_to_dict(g) for g in ALL_GEARS],
        "mesh_edges": [mesh_to_dict(e) for e in MESH_EDGES],
    }

    out_path.write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return out_path


if __name__ == "__main__":
    p = emit()
    print(f"wrote {p} ({p.stat().st_size} bytes, {len(ALL_GEARS)} gears, {len(MESH_EDGES)} mesh edges)")
