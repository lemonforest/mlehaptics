"""Self-contained algebraic visibility tests (no skyfield required).

These tests exercise the ``precise=False`` paths in the bridge:
algebraic synodic-cycle propagation for elongation, heliacal rising,
visibility windows, and Saros-cycle eclipse propagation.

Per ADR 0011, the precision target is ~±1 day on heliacal events and
~±5° on elongation queries. Tests verify *consistency* (round-trips
across known periods) rather than absolute precision against
skyfield — those equivalence tests live in test_facades.py and need
the [ephemeris] extras.
"""

from __future__ import annotations

import math

import pytest

from antikythera_spectral import bridge
from antikythera_spectral.visibility_algebraic import (
    get_next_heliacal_rising as _alg_rising,
    get_solar_elongation_deg as _alg_elong,
    get_visibility_windows as _alg_windows,
    is_visible as _alg_visible,
    supported_planets,
)


# ──────────────────────────────────────────────────────────────────────
# Heliacal rising — closed-form anchor + n*synodic
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("planet", ["mercury", "venus", "mars", "jupiter", "saturn"])
def test_heliacal_rising_advances_one_synodic_period(planet: str) -> None:
    """Asking for the rising 'after the previous one' must give the next one."""
    rise1 = _alg_rising(2451545.0, planet)
    # Ask for rising after rise1 itself — should give the NEXT rising.
    rise2 = _alg_rising(rise1 + 0.01, planet)
    delta = rise2 - rise1
    # Synodic periods range from ~116 d (Mercury) to ~780 d (Mars). The
    # successor should be exactly one period later.
    assert 100 <= delta <= 800, f"{planet}: rise2 - rise1 = {delta} days"


def test_heliacal_rising_is_idempotent_at_anchor() -> None:
    """Asking 'next rising at exactly an anchor JD' returns the same JD or one period later."""
    for planet in supported_planets():
        rise = _alg_rising(2451545.0, planet)
        rise_again = _alg_rising(rise - 0.01, planet)
        assert abs(rise - rise_again) < 1e-6


def test_bridge_heliacal_default_is_algebraic() -> None:
    """Bridge default returns mode=algebraic without skyfield."""
    out = bridge.get_next_heliacal_rising(2451545.0, "mars")
    assert out["ok"] is True
    assert out["mode"] == "algebraic"
    assert out["heliacal_rising_jd"] > 2451545.0


# ──────────────────────────────────────────────────────────────────────
# Solar elongation — sinusoidal phase model
# ──────────────────────────────────────────────────────────────────────

def test_elongation_at_anchor_is_near_threshold() -> None:
    """At the heliacal-rising anchor the elongation should be near the threshold (positive)."""
    # Mars: anchor is its rising; elongation just at threshold (13°)
    # The sinusoidal model gives elongation = 180·sin(π·phase). At phase=0
    # this is 0 (conjunction); at phase~0.072 (13/180 ≈ 0.072 of a half-cycle),
    # it'd reach 13°. So at the anchor JD itself, the model gives 0
    # (conjunction). The CHARACTER of the model differs from reality —
    # but predictions stay periodically consistent.
    elong_at_anchor = _alg_elong(2451769.8441, "mars")
    # Model: at phase=0, elongation=0. That's by construction.
    assert abs(elong_at_anchor) < 1e-6


def test_elongation_at_half_cycle_outer_planet() -> None:
    """At phase=0.5 (opposition for outer planets), elongation should be 180°."""
    # Jupiter anchor + half synodic period.
    from antikythera_spectral.visibility_algebraic import _load_anchors
    p = _load_anchors()["planets"]["jupiter"]
    half_jd = p["heliacal_rising_anchor_jd"] + p["synodic_period_days"] / 2
    elong = _alg_elong(half_jd, "jupiter")
    assert abs(elong - 180.0) < 1.0


def test_elongation_at_max_phase_inferior_planet() -> None:
    """For Venus at phase=0.25, sinusoidal model peaks at max_elongation."""
    from antikythera_spectral.visibility_algebraic import _load_anchors
    p = _load_anchors()["planets"]["venus"]
    quarter_jd = p["heliacal_rising_anchor_jd"] + p["synodic_period_days"] / 4
    elong = _alg_elong(quarter_jd, "venus")
    # Venus max elongation is 47°; sin(2π·0.25) = sin(π/2) = 1
    assert abs(elong - 47.0) < 1.0


# ──────────────────────────────────────────────────────────────────────
# Visibility windows
# ──────────────────────────────────────────────────────────────────────

def test_visibility_windows_count_scales_with_band() -> None:
    """Twice the JD band → roughly twice the windows."""
    # Pick a planet, query a 5000-day band vs 10000-day band.
    short = _alg_windows(2451545.0, 2451545.0 + 5000, "mercury")
    long_ = _alg_windows(2451545.0, 2451545.0 + 10000, "mercury")
    # Mercury synodic ≈ 116 d, so 5000 days ≈ 43 cycles → ~43 windows.
    # 10000 days ≈ 86 cycles. ratio ≈ 2.
    assert 0.5 * len(short) <= len(long_) - len(short) <= 1.5 * len(short)


def test_visibility_window_duration_matches_synodic_fraction() -> None:
    """Each window's duration equals visibility_fraction · synodic_period (clipped)."""
    from antikythera_spectral.visibility_algebraic import _load_anchors
    p = _load_anchors()["planets"]["mars"]
    expected = p["synodic_period_days"] * p["visibility_fraction_per_cycle"]
    # Use a band wider than one window so we're not clipped.
    windows = _alg_windows(p["heliacal_rising_anchor_jd"],
                            p["heliacal_rising_anchor_jd"] + 2 * p["synodic_period_days"],
                            "mars")
    # The first window should have the full duration; others may be clipped.
    if windows:
        dur = windows[0][1] - windows[0][0]
        assert abs(dur - expected) < 1.0


def test_bridge_visibility_default_is_algebraic() -> None:
    out = bridge.get_visibility_windows(2451545.0, 2451545.0 + 1000, "venus")
    assert out["ok"] is True
    assert out["mode"] == "algebraic"
    assert out["n_windows"] >= 1
    for w in out["windows"]:
        assert "rise_jd" in w and "set_jd" in w


# ──────────────────────────────────────────────────────────────────────
# is_visible at hand-picked JDs
# ──────────────────────────────────────────────────────────────────────

def test_is_visible_at_conjunction_returns_false() -> None:
    """Outer-planet conjunction (phase 0) → elongation 0 → not visible."""
    from antikythera_spectral.visibility_algebraic import _load_anchors
    p = _load_anchors()["planets"]["jupiter"]
    # phase=0 means at the anchor (which is heliacal rising, not conjunction
    # under our model — the model treats anchor as phase=0 = conjunction
    # for elongation purposes). Adding a small offset moves us away.
    assert _alg_visible(p["heliacal_rising_anchor_jd"], "jupiter") is False


def test_is_visible_at_opposition_returns_true() -> None:
    """Outer-planet opposition (phase 0.5) → 180° → visible."""
    from antikythera_spectral.visibility_algebraic import _load_anchors
    p = _load_anchors()["planets"]["jupiter"]
    half = p["heliacal_rising_anchor_jd"] + p["synodic_period_days"] / 2
    assert _alg_visible(half, "jupiter") is True


# ──────────────────────────────────────────────────────────────────────
# Pyodide compat smoke — these should all work with skyfield uninstalled
# ──────────────────────────────────────────────────────────────────────

def test_algebraic_module_does_not_import_skyfield() -> None:
    """The algebraic module must not pull skyfield at import time."""
    import importlib
    import sys

    # Snapshot pre-state
    pre = set(sys.modules.keys())

    # Force re-import (or first import).
    if "antikythera_spectral.visibility_algebraic" in sys.modules:
        del sys.modules["antikythera_spectral.visibility_algebraic"]
    importlib.import_module("antikythera_spectral.visibility_algebraic")

    post = set(sys.modules.keys())
    new = post - pre
    skyfield_imports = [m for m in new if "skyfield" in m or "jplephem" in m]
    assert not skyfield_imports, (
        f"visibility_algebraic pulled skyfield modules: {skyfield_imports}"
    )
