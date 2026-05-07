"""v0.22.0 Layer C(b) — Decoy Discrimination Catalog tests.

Pins BC-differential velocity separation (the only midcourse-
surviving discriminator), discrimination-altitude search, and BC
reference class roster. Allen-Eggers closed-form physics
(NACA Report 1381, 1958); reference: Sessler/UCS *Countermeasures*
2000.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.decoy_discrimination_catalog import (
    compute_bc_differential,
    compute_discrimination_altitude,
    get_bc_reference_class,
    list_bc_reference_classes,
)
from ephemerides_spectral._research.decoy_discrimination_data import (
    BC_REFERENCE_CLASSES,
    SOURCES,
    BCReferenceClass,
)


# ──────────────────────────────────────────────────────────────────────
# BC reference class roster shape
# ──────────────────────────────────────────────────────────────────────


def test_reference_class_count() -> None:
    assert len(BC_REFERENCE_CLASSES) == 4


def test_reference_class_names() -> None:
    by = {c.class_name for c in BC_REFERENCE_CLASSES}
    assert by == {"heavy_rv", "light_rv", "replica_decoy", "chaff_decoy"}


def test_sources_count() -> None:
    assert len(SOURCES) == 4


def test_heavy_rv_above_decoy_classes() -> None:
    """Sessler 2000 Table 8.1: warhead BC ~5000-15000, decoy ~10-100."""
    by = {c.class_name: c for c in BC_REFERENCE_CLASSES}
    assert by["heavy_rv"].typical_bc_kg_m2 > by["replica_decoy"].typical_bc_kg_m2
    assert by["heavy_rv"].typical_bc_kg_m2 > by["chaff_decoy"].typical_bc_kg_m2
    assert by["heavy_rv"].typical_bc_kg_m2 / by["chaff_decoy"].typical_bc_kg_m2 >= 100.0


# ──────────────────────────────────────────────────────────────────────
# BC-differential physics (Allen-Eggers)
# ──────────────────────────────────────────────────────────────────────


def test_bc_differential_warhead_decoy_separation() -> None:
    """Heavy compact RV (BC=10000) vs balloon decoy (BC=50) at
    standard ICBM re-entry → significant Δv in 60-100 km band."""
    r = compute_bc_differential(
        bc_heavy_kg_m2=10000.0,
        bc_light_kg_m2=50.0,
    )
    assert r["ok"] is True
    # Peak Δv must exceed 500 m/s (Sessler 2000 published figures)
    assert r["peak_delta_v_m_s"] > 500.0


def test_bc_differential_at_reentry_interface_small() -> None:
    """At 100 km (re-entry interface), both objects are essentially at
    v_entry — Δv is small but nonzero (exponential atmosphere has
    finite density at the Karman line)."""
    r = compute_bc_differential(
        bc_heavy_kg_m2=10000.0,
        bc_light_kg_m2=50.0,
        entry_velocity_m_s=7000.0,
    )
    # First sample at upper band (100 km); Δv must be small relative
    # to v_entry — under 1% of 7000 m/s.
    first = r["samples"][0]
    assert first["altitude_km"] == pytest.approx(100.0, abs=0.01)
    assert abs(first["delta_v_m_s"]) < 70.0  # < 1% of 7000 m/s


def test_bc_differential_grows_downward() -> None:
    """Δv must increase monotonically as altitude decreases (heavy
    decelerates less, light decelerates more, gap grows)."""
    r = compute_bc_differential(
        bc_heavy_kg_m2=10000.0,
        bc_light_kg_m2=50.0,
    )
    samples = r["samples"]
    for prev, curr in zip(samples[:-1], samples[1:]):
        # Each successive sample is at lower altitude
        assert curr["altitude_m"] < prev["altitude_m"]
        # Δv must be non-decreasing (allow tiny float noise)
        assert curr["delta_v_m_s"] >= prev["delta_v_m_s"] - 1e-3


def test_bc_ratio_drives_discrimination() -> None:
    """Bigger BC ratio → bigger peak Δv. (10000/10) > (10000/50)."""
    r_big = compute_bc_differential(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=10.0,
    )
    r_small = compute_bc_differential(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=50.0,
    )
    assert r_big["peak_delta_v_m_s"] > r_small["peak_delta_v_m_s"]


# ──────────────────────────────────────────────────────────────────────
# Input validation
# ──────────────────────────────────────────────────────────────────────


def test_bc_heavy_must_exceed_bc_light() -> None:
    """The whole physics relies on heavy > light."""
    r = compute_bc_differential(
        bc_heavy_kg_m2=50.0, bc_light_kg_m2=10000.0,  # reversed
    )
    assert r["ok"] is False


def test_negative_bc_rejected() -> None:
    r = compute_bc_differential(
        bc_heavy_kg_m2=-1.0, bc_light_kg_m2=50.0,
    )
    assert r["ok"] is False


def test_inverted_altitude_band_rejected() -> None:
    r = compute_bc_differential(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=50.0,
        altitude_band_lower_km=100.0,
        altitude_band_upper_km=60.0,  # inverted
    )
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Discrimination altitude search
# ──────────────────────────────────────────────────────────────────────


def test_discrimination_altitude_found_for_strong_pair() -> None:
    """Heavy RV vs chaff decoy with low Δv threshold → easy
    discrimination, threshold crossed within band."""
    r = compute_discrimination_altitude(
        bc_heavy_kg_m2=10000.0,
        bc_light_kg_m2=10.0,
        delta_v_threshold_m_s=100.0,
    )
    assert r["ok"] is True
    assert r["threshold_crossed"] is True
    assert r["discrimination_altitude_m"] is not None


def test_discrimination_altitude_lower_for_higher_threshold() -> None:
    """Higher Δv threshold → discrimination altitude must be at
    LOWER altitude (more decel needed to reach the threshold)."""
    r_low = compute_discrimination_altitude(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=50.0,
        delta_v_threshold_m_s=100.0,
    )
    r_high = compute_discrimination_altitude(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=50.0,
        delta_v_threshold_m_s=500.0,
    )
    if r_low["threshold_crossed"] and r_high["threshold_crossed"]:
        assert r_high["discrimination_altitude_m"] < r_low["discrimination_altitude_m"]


def test_discrimination_threshold_too_high_not_crossed() -> None:
    """Demanding Δv threshold may not be crossed within the band."""
    r = compute_discrimination_altitude(
        bc_heavy_kg_m2=200.0,        # not very heavy
        bc_light_kg_m2=100.0,        # not very light — narrow gap
        delta_v_threshold_m_s=5000.0,  # unrealistically demanding
    )
    assert r["ok"] is True
    assert r["threshold_crossed"] is False
    assert r["discrimination_altitude_m"] is None


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_class_source_resolves() -> None:
    for c in BC_REFERENCE_CLASSES:
        assert c.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# BC class catalog API
# ──────────────────────────────────────────────────────────────────────


def test_get_bc_class_heavy_rv() -> None:
    r = get_bc_reference_class(class_name="heavy_rv")
    assert r["ok"] is True
    assert r["bc_class"]["typical_bc_kg_m2"] >= 5000.0


def test_get_bc_class_full_catalog() -> None:
    r = get_bc_reference_class()
    assert r["ok"] is True
    assert r["n_classes"] == 4


def test_list_bc_classes() -> None:
    r = list_bc_reference_classes()
    assert r["ok"] is True
    assert r["n_classes"] == 4


def test_unknown_class_rejected() -> None:
    r = get_bc_reference_class(class_name="non_existent_class")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_compute_bc_differential() -> None:
    r = bridge.compute_bc_differential(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=50.0,
    )
    assert r["ok"] is True
    assert r["peak_delta_v_m_s"] > 500.0


def test_bridge_compute_discrimination_altitude() -> None:
    r = bridge.compute_discrimination_altitude(
        bc_heavy_kg_m2=10000.0, bc_light_kg_m2=10.0,
    )
    assert r["ok"] is True


def test_bridge_bc_class_apis() -> None:
    r = bridge.get_bc_reference_class(class_name="replica_decoy")
    assert r["ok"] is True
    r2 = bridge.list_bc_reference_classes()
    assert r2["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_bc_differential_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "bc-differential",
            "--bc-heavy", "10000", "--bc-light", "50",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["peak_delta_v_m_s"] > 500.0


def test_cli_discrimination_altitude_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "discrimination-altitude",
            "--bc-heavy", "10000", "--bc-light", "10",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["threshold_crossed"] is True


def test_cli_bc_classes_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["bc-reference-classes"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_classes"] == 4


def test_cli_decoy_help() -> None:
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("bc-differential", "discrimination-altitude",
                "bc-reference-class", "bc-reference-classes"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
