"""Emit ``_data/periods.json`` from ``research.historical_periods``.

Two SSOT lists with FIRM / RECONSTRUCTED / DISPUTED confidence tags:

- ``MULAPIN_PERIODS`` — Babylonian period relations (~1000 BCE).
- ``ALMAGEST_PERIODS`` — Ptolemaic period relations (~150 CE).

Default consumers should filter to FIRM + RECONSTRUCTED unless the
``--include-disputed`` flag is set in the bridge call.

Run::

    python codegen/emit_periods.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from _paths import DATA_DIR, ensure_research_importable

ensure_research_importable()
from research.historical_periods import (  # noqa: E402
    ALMAGEST_PERIODS,
    MULAPIN_PERIODS,
)


def period_to_dict(p: Any) -> Dict[str, Any]:
    """Serialize one ``PeriodRelation`` to a JSON-compatible dict."""
    return asdict(p)


def emit() -> Path:
    out_path = DATA_DIR / "periods.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "source_module": "research.historical_periods",
        "confidence_levels": ["FIRM", "RECONSTRUCTED", "DISPUTED"],
        "n_mulapin": len(MULAPIN_PERIODS),
        "n_almagest": len(ALMAGEST_PERIODS),
        "mulapin": [period_to_dict(p) for p in MULAPIN_PERIODS],
        "almagest": [period_to_dict(p) for p in ALMAGEST_PERIODS],
    }

    out_path.write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return out_path


if __name__ == "__main__":
    p = emit()
    print(
        f"wrote {p} ({p.stat().st_size} bytes; "
        f"{len(MULAPIN_PERIODS)} mulapin + {len(ALMAGEST_PERIODS)} almagest periods)"
    )
