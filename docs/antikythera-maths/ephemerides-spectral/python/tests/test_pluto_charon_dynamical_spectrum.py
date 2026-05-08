"""v0.24.11 — Sol Pluto-Charon Dynamical Spectrum tests.

Pins the **fourth per-body dynamical-spectrum surface** (after
v0.24.0 Mercury / v0.24.1 Luna / v0.24.2 Mars) and the project's
first **binary mutual-tidal-lock** entry. Pluto-Charon is the
Solar System's only known double-synchronous binary planet:
mutual orbital period = both spin periods = 6.387 days.

Path-B response to the v0.24.10 OOS-probe-roster's identification
of a feature-schema gap (commensurabilities-without-Saros-track
were collapsing onto Mercury-stable in v0.24.9). v0.24.11 ships
Pluto-Charon as a ground-proof row in the regime classifier with
a NEW regime label `rigid_body_action_angle_mutual_lock`,
populating the gap rather than engineering a feature to force
discrimination.

The classifier is **not machine learning in the SGD sense** —
adding the v0.24.11 ground-proof row is a deterministic schema
extension; the eigenbasis recomputes via `np.linalg.eigh` (closed
form), byte-identical across runs, no training loop.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.pluto_charon_dynamical_spectrum_catalog import (
    get_double_synchronous_signature,
    get_pluto_charon_dynamical_spectrum,
    list_pluto_charon_dynamical_spectrum,
)
from ephemerides_spectral._research.pluto_charon_dynamical_spectrum_data import (
    CHARON_RADIUS_KM,
    CHARON_TO_PLUTO_MASS_RATIO,
    HYDRA_ORBITAL_PERIOD_DAYS,
    KERBEROS_ORBITAL_PERIOD_DAYS,
    NIX_ORBITAL_PERIOD_DAYS,
    PLUTO_BARYCENTER_ABOVE_SURFACE_KM,
    PLUTO_BARYCENTER_OFFSET_KM,
    PLUTO_CHARON_DYNAMICAL_MODES,
    PLUTO_CHARON_ECCENTRICITY,
    PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG,
    PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
    PLUTO_RADIUS_KM,
    PRECISION_HIGH,
    SOURCES,
    STYX_ORBITAL_PERIOD_DAYS,
    DynamicalMode,
)


# ──────────────────────────────────────────────────────────────────────
# Catalog shape
# ──────────────────────────────────────────────────────────────────────


def test_mode_count_12() -> None:
    """3 angle-locked + 1 apsidal libration + 4 actions + 4 small-moon
    near-commensurabilities = 12 modes."""
    assert len(PLUTO_CHARON_DYNAMICAL_MODES) == 12


def test_mode_names_unique() -> None:
    names = [m.name for m in PLUTO_CHARON_DYNAMICAL_MODES]
    assert len(names) == len(set(names))


def test_sources_count_6() -> None:
    """Stern 1992 + Tholen-Buie 1990 + Brozovic 2015 + Stern 2015 +
    Showalter-Hamilton 2015 + Showalter 2015 Kerberos discovery +
    Weaver 2016 = 7."""
    assert len(SOURCES) == 7


def test_every_mode_source_key_resolves() -> None:
    for m in PLUTO_CHARON_DYNAMICAL_MODES:
        assert m.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Triple-lock (the headline)
# ──────────────────────────────────────────────────────────────────────


def test_triple_lock_invariant() -> None:
    """Pluto spin period = Charon spin period = mutual orbital period
    = 6.387 d (Brozovic 2015). The closure of double-synchronous
    tidal evolution."""
    sig = get_double_synchronous_signature()
    assert sig["pluto_spin_period_days"] == sig["mutual_orbital_period_days"]
    assert sig["charon_spin_period_days"] == sig["mutual_orbital_period_days"]
    assert sig["triple_lock_max_residual_seconds"] == 0.0


def test_mutual_orbital_period_published_value() -> None:
    """Brozovic 2015: 6.3872304 d."""
    assert PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS == pytest.approx(
        6.3872304, abs=1e-6
    )


def test_eccentricity_essentially_zero() -> None:
    """The double-synchronous lock confirmation: e ~ 5e-5,
    ~1100x smaller than Luna's 0.0549."""
    assert PLUTO_CHARON_ECCENTRICITY < 1e-3
    assert PLUTO_CHARON_ECCENTRICITY > 0


def test_mutual_obliquity_essentially_zero() -> None:
    """Both spin axes aligned with mutual orbit normal; the second
    confirmation that tidal evolution has gone to completion."""
    assert PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG < 0.01


# ──────────────────────────────────────────────────────────────────────
# Mass ratio + barycenter geometry
# ──────────────────────────────────────────────────────────────────────


def test_mass_ratio_largest_in_solar_system() -> None:
    """Brozovic 2015: 0.1218 -- the largest binary mass ratio in
    the Solar System (Earth-Luna ~0.0123, ~10x smaller)."""
    assert CHARON_TO_PLUTO_MASS_RATIO == pytest.approx(0.1218, abs=0.001)
    # Sanity: must exceed Earth-Luna's 0.0123 ratio.
    assert CHARON_TO_PLUTO_MASS_RATIO > 0.05


def test_barycenter_outside_pluto_surface() -> None:
    """Pluto radius 1188 km; barycenter offset 2128 km from Pluto
    center → barycenter sits ~940 km ABOVE Pluto's surface. Both
    bodies orbit a point in empty space. The Solar System's only
    such configuration."""
    assert PLUTO_BARYCENTER_OFFSET_KM > PLUTO_RADIUS_KM
    assert PLUTO_BARYCENTER_ABOVE_SURFACE_KM > 500.0


# ──────────────────────────────────────────────────────────────────────
# Small-moon near-3:4:5:6 commensurabilities
# ──────────────────────────────────────────────────────────────────────


def test_small_moon_styx_near_3_to_1() -> None:
    """Styx period / mutual orbital period ≈ 3 (within 6%)."""
    ratio = STYX_ORBITAL_PERIOD_DAYS / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
    assert abs(ratio - 3) / 3 < 0.06


def test_small_moon_nix_near_4_to_1() -> None:
    """Nix period / mutual orbital period ≈ 4 (within 4%)."""
    ratio = NIX_ORBITAL_PERIOD_DAYS / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
    assert abs(ratio - 4) / 4 < 0.04


def test_small_moon_kerberos_near_5_to_1() -> None:
    """Kerberos period / mutual orbital period ≈ 5 (within 1%)."""
    ratio = (
        KERBEROS_ORBITAL_PERIOD_DAYS / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
    )
    assert abs(ratio - 5) / 5 < 0.01


def test_small_moon_hydra_near_6_to_1() -> None:
    """Hydra period / mutual orbital period ≈ 6 (within 0.5% — the
    closest of the four small moons to perfect commensurability)."""
    ratio = (
        HYDRA_ORBITAL_PERIOD_DAYS / PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
    )
    assert abs(ratio - 6) / 6 < 0.005


def test_small_moon_signature_in_double_synchronous_payload() -> None:
    """The double-synchronous signature includes per-small-moon
    near-integer ratios + fractional offsets."""
    sig = get_double_synchronous_signature()
    moons = sig["small_moon_ratios"]
    assert len(moons) == 4
    moon_names = {m["moon"] for m in moons}
    assert moon_names == {"styx", "nix", "kerberos", "hydra"}


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_canonical_papers_in_sources() -> None:
    """Brozovic 2015 + Stern 2015 + Stern 1992 + Showalter-Hamilton
    2015 must be present — the canonical references."""
    for ref in (
        "brozovic_2015", "stern_2015", "stern_1992",
        "showalter_hamilton_2015",
    ):
        assert ref in SOURCES


# ──────────────────────────────────────────────────────────────────────
# v0.24.9 regime classifier integration (the Path-B test)
# ──────────────────────────────────────────────────────────────────────


def test_pluto_charon_present_in_regime_classifier() -> None:
    """v0.24.11 ships Pluto-Charon as a ground-proof row in the
    v0.24.9 dynamical-regime classifier with new label
    `rigid_body_action_angle_mutual_lock`. The Path-B response to
    the v0.24.10 schema-gap (which had Pluto-Charon collapsing onto
    Mercury-stable)."""
    from ephemerides_spectral._research.dynamical_regime_data import (
        REGIME_EXAMPLES,
    )
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert "0.24.11" in by
    assert by["0.24.11"].regime_label == "rigid_body_action_angle_mutual_lock"
    assert by["0.24.11"].catalog_module == (
        "pluto_charon_dynamical_spectrum_catalog"
    )


def test_mutual_lock_regime_label_unique() -> None:
    """The new regime label must not collide with existing labels."""
    from ephemerides_spectral._research.dynamical_regime_data import (
        REGIME_EXAMPLES,
    )
    labels = [e.regime_label for e in REGIME_EXAMPLES]
    assert labels.count("rigid_body_action_angle_mutual_lock") == 1


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_pluto_charon_dynamical_spectrum_smoke() -> None:
    r = get_pluto_charon_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 12
    assert "binary_geometry" in r
    assert "small_moon_periods_days" in r


def test_get_double_synchronous_signature_smoke() -> None:
    r = get_double_synchronous_signature()
    assert r["ok"] is True
    assert "triple_lock_max_residual_seconds" in r
    assert "small_moon_ratios" in r


def test_list_pluto_charon_dynamical_spectrum_smoke() -> None:
    r = list_pluto_charon_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 12
    assert r["n_sources"] == 7


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_pluto_charon_dynamical_spectrum() -> None:
    r = bridge.get_pluto_charon_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 12


def test_bridge_get_double_synchronous_signature() -> None:
    r = bridge.get_double_synchronous_signature()
    assert r["ok"] is True


def test_bridge_list_pluto_charon_dynamical_spectrum() -> None:
    r = bridge.list_pluto_charon_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 12


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_pluto_charon_dynamical_spectrum_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["pluto-charon-dynamical-spectrum"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_modes"] == 12


def test_cli_double_synchronous_signature_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["double-synchronous-signature"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["pluto_spin_period_days"] == (
        payload["mutual_orbital_period_days"]
    )


def test_cli_pluto_charon_dynamical_spectrum_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["pluto-charon-dynamical-spectrum-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_modes"] == 12


def test_cli_pluto_charon_help() -> None:
    """All v0.24.11 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in (
        "pluto-charon-dynamical-spectrum",
        "double-synchronous-signature",
        "pluto-charon-dynamical-spectrum-full",
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
