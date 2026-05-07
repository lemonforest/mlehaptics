"""v0.24.4 — Sol Toroidal-Residual J₂ Catalog tests.

Pins the per-body shape classification on the Chandrasekhar 1969
ellipsoidal-equilibrium sequence (Sphere → Maclaurin → Jacobi →
bar → ring/torus). Codifies the "rotation makes the toroidal,
self-gravity rounds it back" insight as a per-body surface.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.toroidal_residual_catalog import (
    get_chandrasekhar_sequence_thresholds,
    get_toroidal_residual,
    list_toroidal_residuals,
)
from ephemerides_spectral._research.toroidal_residual_data import (
    PRECISION_HIGH,
    Q_JACOBI_BAR_INSTABILITY,
    Q_MACLAURIN_JACOBI_BIFURCATION,
    Q_ROCHE_FISSION,
    SOURCES,
    TOROIDAL_RESIDUALS,
    ToroidalResidual,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_roster_size_14() -> None:
    assert len(TOROIDAL_RESIDUALS) == 14


def test_canonical_roster_members() -> None:
    by = {t.body for t in TOROIDAL_RESIDUALS}
    expected = {
        "terra", "mars", "venus", "mercury", "luna",
        "jupiter", "saturn", "uranus", "neptune",
        "io", "europa", "ganymede", "callisto", "titan",
    }
    assert by == expected


def test_sources_count() -> None:
    assert len(SOURCES) == 14


# ──────────────────────────────────────────────────────────────────────
# Chandrasekhar sequence thresholds
# ──────────────────────────────────────────────────────────────────────


def test_maclaurin_jacobi_bifurcation_value() -> None:
    """Chandrasekhar 1969: q_M-J ≈ 0.187 (e ≈ 0.81267)."""
    assert Q_MACLAURIN_JACOBI_BIFURCATION == pytest.approx(0.187, abs=0.01)


def test_jacobi_bar_threshold_above_bifurcation() -> None:
    assert Q_JACOBI_BAR_INSTABILITY > Q_MACLAURIN_JACOBI_BIFURCATION


def test_roche_threshold_above_jacobi() -> None:
    assert Q_ROCHE_FISSION > Q_JACOBI_BAR_INSTABILITY


# ──────────────────────────────────────────────────────────────────────
# Headlines
# ──────────────────────────────────────────────────────────────────────


def test_saturn_closest_to_bifurcation() -> None:
    """Saturn is THE Solar-System body closest to the Maclaurin-Jacobi
    bifurcation — q ≈ 0.155 vs threshold 0.187."""
    by = {t.body: t for t in TOROIDAL_RESIDUALS}
    saturn_q = by["saturn"].rotation_parameter_q
    assert 0.13 < saturn_q < 0.18

    # Saturn must have the highest q in the catalog
    qs = [(t.body, t.rotation_parameter_q) for t in TOROIDAL_RESIDUALS]
    qs.sort(key=lambda b: b[1], reverse=True)
    assert qs[0][0] == "saturn"


def test_jupiter_second_highest_q() -> None:
    qs = [(t.body, t.rotation_parameter_q) for t in TOROIDAL_RESIDUALS]
    qs.sort(key=lambda b: b[1], reverse=True)
    assert qs[1][0] == "jupiter"


def test_earth_canonical_maclaurin() -> None:
    """Earth: q ≈ 3.46e-3, J₂ ≈ 1.08e-3, well-within Maclaurin."""
    by = {t.body: t for t in TOROIDAL_RESIDUALS}
    terra = by["terra"]
    assert terra.regime == "maclaurin"
    assert terra.fossil_figure is False
    assert terra.rotation_parameter_q == pytest.approx(3.46e-3, abs=2e-4)


def test_luna_fossil_figure() -> None:
    """Luna's J₂ exceeds rotation-equilibrium prediction by >10× —
    fossil from when Luna was closer to Earth."""
    by = {t.body: t for t in TOROIDAL_RESIDUALS}
    luna = by["luna"]
    assert luna.fossil_figure is True
    # J₂ should be much larger than q (current rotation gives tiny q)
    assert luna.J2_observed > 5 * luna.rotation_parameter_q


def test_mercury_fossil_figure() -> None:
    """Mercury's J₂ exceeds 3:2-locked rotation-equilibrium
    prediction by >10× — fossil from earlier faster-rotation epoch."""
    by = {t.body: t for t in TOROIDAL_RESIDUALS}
    mercury = by["mercury"]
    assert mercury.fossil_figure is True
    assert mercury.J2_observed > 5 * mercury.rotation_parameter_q


def test_venus_extreme_sphere_regime() -> None:
    """Venus: slow retrograde rotator. q ~ 10⁻⁷ → essentially
    spherical."""
    by = {t.body: t for t in TOROIDAL_RESIDUALS}
    venus = by["venus"]
    assert venus.regime == "sphere"
    assert venus.rotation_parameter_q < 1e-6


def test_galileans_synchronous_low_q() -> None:
    """Galileans (Io, Europa, Ganymede, Callisto) all have low q
    because synchronous rotation locks them at orbital frequencies.
    Io is fastest (1.77 d sidereal lock) and so has the highest
    q in this group (~0.0017); Callisto slowest (16.7 d) → smallest q."""
    by = {t.body: t for t in TOROIDAL_RESIDUALS}
    for moon in ("io", "europa", "ganymede", "callisto"):
        assert by[moon].rotation_parameter_q < 5e-3
    # Io has the highest q among Galileans (fastest sidereal rotation)
    galilean_qs = [
        by[m].rotation_parameter_q
        for m in ("io", "europa", "ganymede", "callisto")
    ]
    assert galilean_qs[0] == max(galilean_qs)


# ──────────────────────────────────────────────────────────────────────
# Regime classification
# ──────────────────────────────────────────────────────────────────────


def test_no_body_past_jacobi_threshold() -> None:
    """No Solar-System body sits past the Maclaurin-Jacobi
    bifurcation. (Haumea would, but is not in the v0.16.0 BODIES
    roster.)"""
    for t in TOROIDAL_RESIDUALS:
        assert t.regime in ("sphere", "maclaurin")


def test_q_maclaurin_classification_consistent() -> None:
    """Bodies in the 'maclaurin' regime must have q in the Maclaurin
    range."""
    for t in TOROIDAL_RESIDUALS:
        if t.regime == "maclaurin":
            assert 0.001 <= t.rotation_parameter_q < Q_MACLAURIN_JACOBI_BIFURCATION


def test_q_sphere_classification_consistent() -> None:
    for t in TOROIDAL_RESIDUALS:
        if t.regime == "sphere":
            assert t.rotation_parameter_q < 0.001


# ──────────────────────────────────────────────────────────────────────
# q computation invariants
# ──────────────────────────────────────────────────────────────────────


def test_q_recomputable_from_inputs() -> None:
    """Each row's q must equal ω²R³/(GM) within ppm — verifies the
    helper computed the value correctly from the inputs."""
    for t in TOROIDAL_RESIDUALS:
        period_s = abs(t.rotation_period_days) * 86400.0
        omega = 2.0 * math.pi / period_s
        R_m = t.equatorial_radius_km * 1000.0
        q_recomputed = (omega ** 2) * (R_m ** 3) / t.GM_m3_s2
        assert t.rotation_parameter_q == pytest.approx(
            q_recomputed, rel=1e-6,
        )


def test_all_q_non_negative() -> None:
    for t in TOROIDAL_RESIDUALS:
        assert t.rotation_parameter_q >= 0.0


def test_all_J2_non_negative() -> None:
    """J₂ should be positive for prograde rotators (oblate); the
    dataset only contains positive-J₂ bodies."""
    for t in TOROIDAL_RESIDUALS:
        assert t.J2_observed >= 0.0


def test_all_moment_of_inertia_factor_in_uniform_density_range() -> None:
    """C/MR² ≤ 2/5 (uniform density). Centrally-concentrated bodies
    have lower I_M."""
    for t in TOROIDAL_RESIDUALS:
        assert 0.1 < t.moment_of_inertia_factor <= 0.4 + 1e-6


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_source_key_resolves() -> None:
    for t in TOROIDAL_RESIDUALS:
        assert t.source_key in SOURCES


def test_chandrasekhar_lai_helled_sources_present() -> None:
    """Theory references must be in SOURCES even though no per-row
    cites them — they're the framework references for the threshold
    constants and moment-of-inertia model."""
    for ref in ("chandrasekhar_1969", "lai_1994", "helled_2011"):
        assert ref in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_toroidal_residual_unknown_body() -> None:
    r = get_toroidal_residual(body="krypton")
    assert r["ok"] is False


def test_get_toroidal_residual_full_roster() -> None:
    r = get_toroidal_residual()
    assert r["ok"] is True
    assert r["n_bodies"] == 14
    assert "regime_distribution" in r


def test_get_toroidal_residual_per_body_saturn() -> None:
    r = get_toroidal_residual(body="saturn")
    assert r["ok"] is True
    assert r["residual"]["regime"] == "maclaurin"
    assert r["residual"]["rotation_parameter_q"] > 0.13


def test_get_chandrasekhar_thresholds_smoke() -> None:
    r = get_chandrasekhar_sequence_thresholds()
    assert r["ok"] is True
    assert r["q_maclaurin_jacobi"] == pytest.approx(0.187, abs=0.01)
    # Should ship 5 regimes
    assert len(r["regimes"]) == 5


def test_list_toroidal_residuals_smoke() -> None:
    r = list_toroidal_residuals()
    assert r["ok"] is True
    assert r["n_bodies"] == 14
    assert r["n_sources"] == 14


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_toroidal_residual() -> None:
    r = bridge.get_toroidal_residual(body="saturn")
    assert r["ok"] is True
    assert r["residual"]["fossil_figure"] is False


def test_bridge_get_chandrasekhar_sequence_thresholds() -> None:
    r = bridge.get_chandrasekhar_sequence_thresholds()
    assert r["ok"] is True


def test_bridge_list_toroidal_residuals() -> None:
    r = bridge.list_toroidal_residuals()
    assert r["ok"] is True
    assert r["n_bodies"] == 14


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_toroidal_residual_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["toroidal-residual", "--body", "saturn"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["residual"]["regime"] == "maclaurin"


def test_cli_chandrasekhar_sequence_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["chandrasekhar-sequence"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["q_maclaurin_jacobi"] == pytest.approx(0.187, abs=0.01)


def test_cli_toroidal_residuals_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["toroidal-residuals"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 14


def test_cli_toroidal_help() -> None:
    """All v0.24.4 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("toroidal-residual",
                "chandrasekhar-sequence",
                "toroidal-residuals"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
