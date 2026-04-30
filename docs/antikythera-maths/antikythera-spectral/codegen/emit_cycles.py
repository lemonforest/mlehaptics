"""Emit ``_data/cycles.json`` from ``research.astronomical_cycles.CYCLES``.

The Cycle dataclass carries (name, numerator, denominator, modern_days,
mechanism_days, notes, tag) plus computed prime-factor lists. We
serialize the dataclass fields verbatim and add the prime factors so
downstream consumers don't need to re-import sympy or the research
module.

Run::

    python codegen/emit_cycles.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from _paths import DATA_DIR, ensure_research_importable

ensure_research_importable()
from research.astronomical_cycles import CYCLES  # noqa: E402


def cycle_to_dict(c: Any) -> Dict[str, Any]:
    """Serialize one ``Cycle`` to a JSON-compatible dict.

    Includes the @property-derived prime factors so JSON consumers
    don't need to re-import the ``research`` module's prime helpers.
    """
    d = asdict(c)
    d["num_factors"] = list(c.num_factors)
    d["den_factors"] = list(c.den_factors)
    return d


def emit() -> Path:
    out_path = DATA_DIR / "cycles.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "source_module": "research.astronomical_cycles",
        "source_symbol": "CYCLES",
        "n_cycles": len(CYCLES),
        "cycles": [cycle_to_dict(c) for c in CYCLES],
    }

    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path


if __name__ == "__main__":
    p = emit()
    print(f"wrote {p} ({p.stat().st_size} bytes, {len(CYCLES)} cycles)")
