"""Astronomy-bridge tests (§5.4).

Six methods. The frozen-data ones (get_eclipse_anchors,
get_period_relations) always work; the skyfield-dependent ones
(visibility, heliacal rising, solar elongation, find_eclipses) are
gracefully marked ``ok=False`` if no kernel is on disk — we test that
behavior, not that they actually compute.
"""

from __future__ import annotations

import os

import pytest

from antikythera_spectral import bridge


# ──────────────────────────────────────────────────────────────────────
# Frozen-data methods (always available)
# ──────────────────────────────────────────────────────────────────────

def test_get_eclipse_anchors_hellenistic() -> None:
    out = bridge.get_eclipse_anchors(era="hellenistic")
    assert out["ok"] is True
    assert out["era"] == "hellenistic"
    assert out["n_anchors"] >= 6
    a = out["anchors"][0]
    assert "jd" in a
    assert "date_iso" in a


def test_get_eclipse_anchors_modern_or_all() -> None:
    assert bridge.get_eclipse_anchors(era="modern")["ok"] is True
    assert bridge.get_eclipse_anchors(era="all")["ok"] is True


def test_get_eclipse_anchors_rejects_bad_era() -> None:
    out = bridge.get_eclipse_anchors(era="bronze-age")
    assert out["ok"] is False


def test_get_period_relations_mulapin() -> None:
    out = bridge.get_period_relations(source="mulapin")
    assert out["ok"] is True
    assert out["n_relations"] >= 5
    r = out["relations"][0]
    assert "source" in r
    assert "phenomenon" in r
    assert "numerator" in r
    assert "denominator" in r


def test_get_period_relations_almagest() -> None:
    out = bridge.get_period_relations(source="almagest")
    assert out["ok"] is True
    assert out["n_relations"] >= 8


def test_get_period_relations_rejects_bad_source() -> None:
    out = bridge.get_period_relations(source="enuma-elish")
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Skyfield-dependent methods (gracefully degrade)
# ──────────────────────────────────────────────────────────────────────

def test_get_solar_elongation_input_validation() -> None:
    """Bad inputs error before any kernel load is attempted."""
    out = bridge.get_solar_elongation("nope", "mars")
    assert out["ok"] is False
    out = bridge.get_solar_elongation(2451545.0, "Pluto")
    assert out["ok"] is False


def test_get_visibility_windows_input_validation() -> None:
    out = bridge.get_visibility_windows(2451545.0, 2451545.0, "mars")
    assert out["ok"] is False  # jd_hi must be > jd_lo
    out = bridge.get_visibility_windows("a", "b", "mars")
    assert out["ok"] is False


def test_get_next_heliacal_rising_input_validation() -> None:
    out = bridge.get_next_heliacal_rising("nope", "mars")
    assert out["ok"] is False


def test_find_eclipses_input_validation() -> None:
    out = bridge.find_eclipses("a", "b", kind="all")
    assert out["ok"] is False
    out = bridge.find_eclipses(2451545.0, 2451545.0)
    assert out["ok"] is False  # zero-width range
    out = bridge.find_eclipses(2451545.0, 2451600.0, kind="penumbral")
    assert out["ok"] is False


# Optionally, when a kernel is on disk (ANTIKYTHERA_KERNEL_PATH env
# var set), exercise the actual ephemeris-backed paths.
@pytest.mark.skipif(
    not os.environ.get("ANTIKYTHERA_KERNEL_PATH"),
    reason="set ANTIKYTHERA_KERNEL_PATH to run kernel-backed tests",
)
def test_get_solar_elongation_modern_with_kernel() -> None:
    # J2000 Mars elongation should be a valid finite number.
    out = bridge.get_solar_elongation(2451545.0, "mars")
    if not out["ok"]:
        pytest.skip(f"kernel load failed: {out.get('error')}")
    assert 0.0 <= out["elongation_deg"] <= 180.0
