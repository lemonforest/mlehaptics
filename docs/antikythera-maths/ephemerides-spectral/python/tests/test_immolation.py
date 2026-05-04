"""Immolation suite for ephemerides-spectral.

Cheap-but-load-bearing release-gate tests: every name in
``bridge.__all__`` must resolve, the version string must agree
between version.py and pyproject.toml, and the v0.3.0 time-scale +
natural-resonance surface must be wired through.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral.version import __version__


# Names exported from bridge.__all__ that are *constants* rather than
# callables. They must still resolve via getattr, but `callable()` is
# the wrong check for them.
_BRIDGE_CONSTANTS = frozenset({
    "DEFAULT_BACKEND",
    "SUPPORTED_BACKENDS",
    "SUPPORTED_BODIES",
    "ALLOWED_KERNELS",
    "LUNAR_KERNELS",
})


def test_bridge_api_contract() -> None:
    """Every name in bridge.__all__ must resolve; functions must be callable."""
    assert len(bridge.__all__) >= 3
    for name in bridge.__all__:
        attr = getattr(bridge, name)  # raises if missing
        if name in _BRIDGE_CONSTANTS:
            # Constants: not callable, but must be a non-None value.
            assert attr is not None, f"{name} is None"
        else:
            assert callable(attr), f"{name} is in __all__ but not callable"


def test_version_agreement() -> None:
    """Version in pyproject.toml must match version.py."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover — only hit on py3.10
        import tomli as tomllib  # type: ignore[no-redef]

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == __version__


def test_bridge_has_v030_surface() -> None:
    """The v0.3.0 time-scale + natural-resonance surface must be present."""
    expected = {
        "jd_to_mars_time",
        "mars_time_to_jd",
        "get_lunar_phase",
        "list_lunar_kernels",
        "get_natural_resonance_group",
    }
    missing = expected - set(bridge.__all__)
    assert not missing, f"missing v0.3.0 surface in bridge.__all__: {missing}"


def test_natural_resonance_group_returns_z30() -> None:
    """The four-resonance v0.2.0 set must yield Z_30 = Z_2 × Z_3 × Z_5."""
    out = bridge.get_natural_resonance_group()
    assert out["ok"] is True
    assert out["natural_modulus"] == 30
    assert out["prime_factors"] == [2, 3, 5]


def test_mars_time_round_trip_at_reference() -> None:
    """Allison & McEwen reference: 2000-01-06 UTC ↔ MSD ≈ 44795.99."""
    forward = bridge.jd_to_mars_time(2451549.5)
    assert forward["ok"] is True
    assert abs(forward["msd"] - 44795.999817) < 1e-4
    inverse = bridge.mars_time_to_jd(forward["msd"])
    assert inverse["ok"] is True
    assert abs(inverse["jd_utc"] - 2451549.5) < 1e-9
