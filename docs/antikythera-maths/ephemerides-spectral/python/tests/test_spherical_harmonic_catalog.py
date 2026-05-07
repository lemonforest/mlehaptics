"""v0.21.0 — Sol Spherical Harmonic Catalog (unification refactor) tests.

Pins:

* The unification surface — querying any body across {"gravity",
  "magnetic", "both"} returns the v0.20.0 / v0.20.1 records adapted
  to a unified shape with explicit `normalisation_convention`.
* Roster shape: 56 gravity bodies (from v0.20.0) + 7 magnetic bodies
  (from v0.20.1) + 7 both-channels intersection.
* No regression on v0.20.0 / v0.20.1 surfaces — those continue to
  return their original shapes.
* Schmidt ↔ 4π-Stokes conversion factor math (Winch et al. 2005).
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).

Mirrors the v0.19/v0.20 ship test patterns.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.spherical_harmonic_catalog import (
    CHANNEL_BOTH,
    CHANNEL_GRAVITY,
    CHANNEL_MAGNETIC,
    NORM_4PI_STOKES,
    NORM_SCHMIDT_QUASI,
    compute_spherical_harmonics,
    convert_normalisation,
    list_spherical_harmonic_models,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_unified_roster_size() -> None:
    """56 gravity + 7 magnetic; 7 in both (the magnetic roster is a
    strict subset of the gravity roster)."""
    r = list_spherical_harmonic_models()
    assert r["ok"] is True
    assert r["n_gravity_models"] == 56
    assert r["n_magnetic_models"] == 7
    assert r["n_both_channels_bodies"] == 7


def test_unified_bodies_union_size() -> None:
    """Union of gravity + magnetic = 56 (since magnetic ⊆ gravity)."""
    r = list_spherical_harmonic_models()
    assert r["n_bodies"] == 56


def test_both_channels_subset_canonical() -> None:
    """The 7 bodies with both channels are the v0.20.1 magnetic
    multipole roster: terra, mercury, jupiter, saturn, uranus, neptune,
    ganymede."""
    r = list_spherical_harmonic_models()
    expected = {"terra", "mercury", "jupiter", "saturn",
                "uranus", "neptune", "ganymede"}
    assert set(r["both_channels_bodies"]) == expected


def test_merged_sources_dict() -> None:
    """Merged citation dict spans both sectors. v0.20.0 has 67;
    v0.20.1 has 9; some keys may collide (rare). The merged size
    is between max(67, 9) and 67 + 9 = 76."""
    r = list_spherical_harmonic_models()
    assert 67 <= r["n_merged_sources"] <= 76


def test_normalisation_conventions_advertised() -> None:
    r = list_spherical_harmonic_models()
    conv = r["normalisation_conventions"]
    assert conv[CHANNEL_GRAVITY] == NORM_4PI_STOKES
    assert conv[CHANNEL_MAGNETIC] == NORM_SCHMIDT_QUASI


# ──────────────────────────────────────────────────────────────────────
# Per-body unified query
# ──────────────────────────────────────────────────────────────────────

def test_query_terra_both_channels() -> None:
    """Earth has both gravity (EGM2008) + magnetic (IGRF-13)."""
    r = compute_spherical_harmonics(body="terra", channel=CHANNEL_BOTH)
    assert r["ok"] is True
    assert r["channels"][CHANNEL_GRAVITY] is not None
    assert r["channels"][CHANNEL_MAGNETIC] is not None
    assert r["channels"][CHANNEL_GRAVITY]["model_name"] == "EGM2008"
    assert r["channels"][CHANNEL_MAGNETIC]["model_name"] == "IGRF-13"


def test_query_mars_gravity_only() -> None:
    """Mars has gravity but no global intrinsic dipole; magnetic = None."""
    r = compute_spherical_harmonics(body="mars", channel=CHANNEL_BOTH)
    assert r["ok"] is True
    assert r["channels"][CHANNEL_GRAVITY] is not None
    assert r["channels"][CHANNEL_MAGNETIC] is None


def test_query_jupiter_magnetic_only_request() -> None:
    """`channel="magnetic"` returns only the magnetic record (gravity
    not in response)."""
    r = compute_spherical_harmonics(body="jupiter", channel=CHANNEL_MAGNETIC)
    assert r["ok"] is True
    assert CHANNEL_MAGNETIC in r["channels"]
    assert CHANNEL_GRAVITY not in r["channels"]
    assert r["channels"][CHANNEL_MAGNETIC]["model_name"] == "JRM33"


def test_query_normalisation_convention_attached() -> None:
    """Every gravity record carries 4pi-Stokes; every magnetic
    record carries Schmidt-quasi-norm."""
    r = compute_spherical_harmonics(body="terra", channel=CHANNEL_BOTH)
    assert r["channels"][CHANNEL_GRAVITY]["normalisation_convention"] == NORM_4PI_STOKES
    assert r["channels"][CHANNEL_MAGNETIC]["normalisation_convention"] == NORM_SCHMIDT_QUASI


def test_query_unknown_body() -> None:
    r = compute_spherical_harmonics(body="krypton", channel=CHANNEL_BOTH)
    assert r["ok"] is False


def test_query_unknown_channel() -> None:
    r = compute_spherical_harmonics(body="terra", channel="nonsense")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Normalisation conversion math (Winch et al. 2005)
# ──────────────────────────────────────────────────────────────────────

def test_conversion_identity_when_same_convention() -> None:
    """Schmidt → Schmidt should return value unchanged + factor = 1."""
    r = convert_normalisation(
        coefficient_value=42.0, n=3, m=2,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_SCHMIDT_QUASI,
    )
    assert r["ok"] is True
    assert r["value"] == 42.0
    assert r["factor"] == 1.0


def test_conversion_n1_m0() -> None:
    """n=1, m=0: delta_0m=1, so factor = (2-1)(2*1+1) = 3.
    Schmidt → 4pi: divide by sqrt(3) ≈ 0.577."""
    r = convert_normalisation(
        coefficient_value=1.0, n=1, m=0,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_4PI_STOKES,
    )
    assert r["ok"] is True
    assert r["factor"] == pytest.approx(1.0 / math.sqrt(3.0), abs=1e-10)


def test_conversion_n1_m1() -> None:
    """n=1, m=1: delta_0m=0, so factor = (2)(3) = 6.
    Schmidt → 4pi: divide by sqrt(6) ≈ 0.408."""
    r = convert_normalisation(
        coefficient_value=1.0, n=1, m=1,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_4PI_STOKES,
    )
    assert r["ok"] is True
    assert r["factor"] == pytest.approx(1.0 / math.sqrt(6.0), abs=1e-10)


def test_conversion_round_trip() -> None:
    """Schmidt → 4pi → Schmidt = identity (modulo float)."""
    original = 12345.6789
    forward = convert_normalisation(
        coefficient_value=original, n=4, m=2,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_4PI_STOKES,
    )
    back = convert_normalisation(
        coefficient_value=forward["value"], n=4, m=2,
        from_convention=NORM_4PI_STOKES,
        to_convention=NORM_SCHMIDT_QUASI,
    )
    assert back["value"] == pytest.approx(original, rel=1e-12)


def test_conversion_invalid_n() -> None:
    r = convert_normalisation(
        coefficient_value=1.0, n=-1, m=0,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_4PI_STOKES,
    )
    assert r["ok"] is False


def test_conversion_m_greater_than_n() -> None:
    r = convert_normalisation(
        coefficient_value=1.0, n=1, m=5,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_4PI_STOKES,
    )
    assert r["ok"] is False


def test_conversion_non_finite() -> None:
    r = convert_normalisation(
        coefficient_value=float("nan"), n=2, m=1,
        from_convention=NORM_SCHMIDT_QUASI,
        to_convention=NORM_4PI_STOKES,
    )
    assert r["ok"] is False


def test_conversion_unknown_convention() -> None:
    r = convert_normalisation(
        coefficient_value=1.0, n=2, m=1,
        from_convention="NotARealConvention",
        to_convention=NORM_4PI_STOKES,
    )
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Back-compat: v0.20.0 + v0.20.1 surfaces unchanged
# ──────────────────────────────────────────────────────────────────────

def test_v0_20_0_geodetic_state_still_works() -> None:
    """v0.20.0 surface continues to function unchanged."""
    r = bridge.get_geodetic_state(body="terra")
    assert r["ok"] is True
    assert r["gravity"]["model_name"] == "EGM2008"


def test_v0_20_1_magnetic_multipoles_still_works() -> None:
    """v0.20.1 surface continues to function unchanged."""
    r = bridge.get_magnetic_multipoles(body="jupiter")
    assert r["ok"] is True
    assert r["main_field"]["model_name"] == "JRM33"


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_spherical_harmonics_smoke() -> None:
    r = bridge.get_spherical_harmonics(body="terra")
    assert r["ok"] is True


def test_bridge_get_spherical_harmonics_channel_filter() -> None:
    r = bridge.get_spherical_harmonics(body="jupiter", channel="magnetic")
    assert r["ok"] is True
    assert "magnetic" in r["channels"]
    assert "gravity" not in r["channels"]


def test_bridge_list_spherical_harmonic_models_smoke() -> None:
    r = bridge.list_spherical_harmonic_models()
    assert r["ok"] is True
    assert r["n_gravity_models"] == 56
    assert r["n_magnetic_models"] == 7


def test_bridge_convert_normalisation_smoke() -> None:
    r = bridge.convert_spherical_harmonic_normalisation(
        coefficient_value=1.0, n=1, m=0,
        from_convention="Schmidt-quasi-norm",
        to_convention="4pi-Stokes",
    )
    assert r["ok"] is True
    assert r["factor"] == pytest.approx(1.0 / math.sqrt(3.0), abs=1e-10)


def test_bridge_get_spherical_harmonics_rejects_unknown() -> None:
    r = bridge.get_spherical_harmonics(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_spherical_harmonics_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["spherical-harmonics", "--body", "terra"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True


def test_cli_spherical_harmonic_models_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["spherical-harmonic-models"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_gravity_models"] == 56


def test_cli_convert_normalisation_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "convert-normalisation",
            "--value", "1.0",
            "--n", "1", "--m", "0",
            "--from", "Schmidt-quasi-norm",
            "--to", "4pi-Stokes",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["factor"] == pytest.approx(1.0 / math.sqrt(3.0), abs=1e-10)


def test_cli_spherical_help() -> None:
    """All three v0.21.0 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("spherical-harmonics", "spherical-harmonic-models",
                "convert-normalisation"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
