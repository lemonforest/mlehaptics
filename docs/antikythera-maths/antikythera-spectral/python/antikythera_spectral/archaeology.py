"""Fragment-keyed gear inventory — archaeological mode."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


_DATA_DIR = Path(__file__).resolve().parent / "_data"


def get_fragment_inventory(fragment: str = "all") -> Dict[str, Any]:
    """Gears grouped by Antikythera fragment (A, B, C, D, or 'all').

    Reads the codegen-emitted ``_data/fragments.json`` rather than the
    live ``_research`` module so the wheel can serve this from frozen
    data without touching the gear-database module's imports.
    """
    p = _DATA_DIR / "fragments.json"
    if not p.exists():
        return {"error": "fragments.json missing — run codegen/regenerate.py"}
    payload = json.loads(p.read_text(encoding="utf-8"))
    by_frag: Dict[str, List[Dict[str, Any]]] = payload.get("fragments", {})
    if fragment == "all":
        return {
            "n_total": payload.get("n_total"),
            "fragments_attested": payload.get("fragments_attested"),
            "n_attested": payload.get("n_attested"),
            "n_reconstructed": payload.get("n_reconstructed"),
            "by_fragment": by_frag,
        }
    if fragment not in by_frag and fragment != "reconstructed":
        return {"error": f"unknown fragment {fragment!r}; "
                          f"valid: {payload.get('fragments_attested')}"}
    return {
        "fragment": fragment,
        "n_gears": len(by_frag[fragment]),
        "gears": list(by_frag[fragment]),
    }


__all__ = ["get_fragment_inventory"]
