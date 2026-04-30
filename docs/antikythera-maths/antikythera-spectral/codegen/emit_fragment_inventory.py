"""Emit ``_data/fragments.json`` — gears keyed by Antikythera fragment.

The wreck-recovered fragments A, B, C, D each contain a subset of the
device's gears; gears reconstructed by Freeth 2021 but not present in
any fragment carry ``fragment=None``.

This emitter groups ``research.gear_database.ALL_GEARS`` by the
``fragment`` field and emits a per-fragment list of (gear_name, role,
attested_in_reconstruction) triples — enough to drive the
``archaeology`` bridge methods.

Run::

    python codegen/emit_fragment_inventory.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from _paths import DATA_DIR, ensure_research_importable

ensure_research_importable()
from research.gear_database import ALL_GEARS  # noqa: E402


def emit() -> Path:
    out_path = DATA_DIR / "fragments.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    by_fragment: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for g in ALL_GEARS:
        key = g.fragment if g.fragment is not None else "reconstructed"
        by_fragment[key].append({
            "name": g.name,
            "role": g.role,
            "teeth": dict(g.teeth),
            "notes": g.notes,
        })

    # Stable sort within each fragment by gear name.
    for entries in by_fragment.values():
        entries.sort(key=lambda d: d["name"])

    fragments_known = sorted([k for k in by_fragment if k != "reconstructed"])
    payload = {
        "schema_version": 1,
        "source_module": "research.gear_database",
        "fragments_attested": fragments_known,
        "n_total": len(ALL_GEARS),
        "n_attested": sum(len(by_fragment[k]) for k in fragments_known),
        "n_reconstructed": len(by_fragment.get("reconstructed", [])),
        "fragments": dict(by_fragment),
    }

    out_path.write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return out_path


if __name__ == "__main__":
    p = emit()
    print(f"wrote {p} ({p.stat().st_size} bytes)")
