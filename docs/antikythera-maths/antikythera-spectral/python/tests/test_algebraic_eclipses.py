"""Self-contained algebraic eclipse-search tests (no skyfield required).

Tests the Saros-cycle propagation in `eclipses_algebraic.py` against
expected behaviour. Per ADR 0011, the algebraic mode is the default.
"""

from __future__ import annotations

import pytest

from antikythera_spectral import bridge
from antikythera_spectral.eclipses_algebraic import find_eclipses_in_range


def test_finds_eclipses_in_hellenistic_band() -> None:
    """Asking for eclipses spanning the Hellenistic anchor era should yield several."""
    # The anchors themselves are at JD ~1684500 and ~1789000 (-200 BCE to +125 CE).
    # A 200-year band centred on -200 BCE should match multiple anchors directly.
    eclipses = find_eclipses_in_range(1620000.0, 1700000.0, kind="all")
    assert len(eclipses) >= 5, f"expected >=5 eclipses, got {len(eclipses)}"
    # Each entry has the required fields.
    for e in eclipses:
        assert "jd_tdb" in e
        assert "kind" in e
        assert e["kind"] in ("lunar", "solar")
        assert "saros_offset" in e


def test_finds_modern_eclipses() -> None:
    """A modern band should yield at least one Saros-propagated eclipse.

    With only 8 anchors and Saros cycle = 18 yr, a 5-year band can
    match at most ~8 anchors-via-offset; after dedupe, expect 1-3
    hits. We assert >=1 — the Saros pointer's job is periodic
    prediction from a known anchor, not exhaustive enumeration.
    """
    # 2020-01-01 to 2025-01-01 ≈ JD 2458849 to 2460676.
    eclipses = find_eclipses_in_range(2458849.0, 2460676.0, kind="all")
    assert len(eclipses) >= 1, (
        "expected at least one Saros-propagated eclipse in 2020-2025"
    )


def test_kind_filter_lunar() -> None:
    eclipses = find_eclipses_in_range(1620000.0, 1700000.0, kind="lunar")
    for e in eclipses:
        assert e["kind"] == "lunar"


def test_kind_filter_solar() -> None:
    eclipses = find_eclipses_in_range(1620000.0, 1700000.0, kind="solar")
    for e in eclipses:
        assert e["kind"] == "solar"


def test_invalid_kind_raises() -> None:
    with pytest.raises(ValueError):
        find_eclipses_in_range(1620000.0, 1700000.0, kind="penumbral")


def test_dedupes_near_coincident_predictions() -> None:
    """Multiple anchors sometimes resolve to the same eclipse (within ~1 day).

    The dedupe keeps the prediction with smallest |saros_offset| (closest
    anchor). Verify no two output entries are within 2 days of each other.
    """
    eclipses = find_eclipses_in_range(1620000.0, 1700000.0, kind="all")
    jds = sorted(e["jd_tdb"] for e in eclipses)
    for a, b in zip(jds[:-1], jds[1:]):
        assert b - a >= 2.0, f"two predictions at JD {a} and {b} are too close"


def test_bridge_find_eclipses_default_is_algebraic() -> None:
    """Bridge default returns mode=algebraic without skyfield."""
    out = bridge.find_eclipses(1620000.0, 1700000.0, kind="all")
    assert out["ok"] is True
    assert out["mode"] == "algebraic"
    assert out["n_eclipses"] >= 5


def test_bridge_find_eclipses_input_validation_still_works() -> None:
    """Invalid inputs still error out (don't reach algebraic path)."""
    out = bridge.find_eclipses("a", "b")
    assert out["ok"] is False
    out = bridge.find_eclipses(1620000.0, 1620000.0)  # zero-width
    assert out["ok"] is False
    out = bridge.find_eclipses(1620000.0, 1700000.0, kind="penumbral")
    assert out["ok"] is False


def test_algebraic_module_does_not_import_skyfield() -> None:
    """The algebraic module must not pull skyfield at import time."""
    import importlib
    import sys

    pre = set(sys.modules.keys())
    if "antikythera_spectral.eclipses_algebraic" in sys.modules:
        del sys.modules["antikythera_spectral.eclipses_algebraic"]
    importlib.import_module("antikythera_spectral.eclipses_algebraic")
    post = set(sys.modules.keys())

    new = post - pre
    skyfield_imports = [m for m in new if "skyfield" in m or "jplephem" in m]
    assert not skyfield_imports, (
        f"eclipses_algebraic pulled skyfield modules: {skyfield_imports}"
    )
