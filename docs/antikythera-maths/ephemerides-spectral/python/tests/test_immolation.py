"""Immolation suite for de441-spectral."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest
from ephemerides_spectral import bridge
from ephemerides_spectral.version import __version__

def test_bridge_api_contract() -> None:
    """Ensure bridge.__all__ is documented and callable."""
    assert len(bridge.__all__) >= 3
    for name in bridge.__all__:
        assert callable(getattr(bridge, name))

def test_version_agreement() -> None:
    """Ensure version in pyproject.toml matches version.py."""
    import tomllib
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == __version__
