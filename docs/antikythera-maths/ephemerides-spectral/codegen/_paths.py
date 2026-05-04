"""Shared path helpers for de441-spectral codegen scripts."""

from __future__ import annotations

import sys
from pathlib import Path

# This file lives at:
#   docs/antikythera-maths/de441-spectral/codegen/_paths.py
_THIS = Path(__file__).resolve()
_RESEARCH_ROOT = _THIS.parents[2]  # docs/antikythera-maths/
_PACKAGE_ROOT = _THIS.parents[1] / "python" / "ephemerides_spectral"

DATA_DIR: Path = _PACKAGE_ROOT / "_data"
RESEARCH_ROOT: Path = _RESEARCH_ROOT

def ensure_research_importable() -> None:
    """Add research-scaffold root to sys.path."""
    p = str(RESEARCH_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)
