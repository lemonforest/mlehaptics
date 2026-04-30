"""Shared path helpers for codegen scripts.

The codegen scripts run from a checkout of the monorepo, importing
the research-scaffold modules under ``docs/antikythera-maths/research/``.
This helper module:

- adds ``docs/antikythera-maths/`` to ``sys.path`` so ``import research``
  resolves; safe to call multiple times,
- exposes ``DATA_DIR`` = the package's ``_data/`` directory where
  emitters write JSON and NPZ output.

Codegen scripts call ``ensure_research_importable()`` exactly once at
their top before any ``from research import …`` line.
"""

from __future__ import annotations

import sys
from pathlib import Path

# This file lives at:
#   docs/antikythera-maths/antikythera-spectral/codegen/_paths.py
# Walk up to docs/antikythera-maths/ for the research-scaffold root.
_THIS = Path(__file__).resolve()
_RESEARCH_ROOT = _THIS.parents[2]  # docs/antikythera-maths/
_PACKAGE_ROOT = _THIS.parents[1] / "python" / "antikythera_spectral"

DATA_DIR: Path = _PACKAGE_ROOT / "_data"
"""Where emit_*.py scripts write their JSON / NPZ output."""

RESEARCH_ROOT: Path = _RESEARCH_ROOT
"""``docs/antikythera-maths/`` — root of the research-scaffold imports."""


def ensure_research_importable() -> None:
    """Add ``docs/antikythera-maths/`` to ``sys.path`` if not present."""
    p = str(RESEARCH_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)
