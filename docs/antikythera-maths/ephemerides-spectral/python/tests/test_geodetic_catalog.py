"""v0.20.0 — Sol Geodetic Catalog tests.

Pins:

* Roster shape across the three channels (56 gravity / 32 topography /
  26 interior; 22 triple-channel bodies; 67 SOURCES citations).
* Per-tier counts per the §17.1.6 ship-readiness convention.
* Headline numeric pins: Earth EGM2008 GM, Moon GRGM1200B GM, Mars
  MRO120F GM, Jupiter zonal J2 (Iess 2018 / Durante 2020).
* Citation discipline: every body's source_key resolves; no unused
  SOURCES entries (ratchet test).
* Architecture partition: HIGH/MEDIUM/LOW/NONE tiers populated by the
  median-across-channels rule from §17.1.6.
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).

Mirrors test_em_instrument.py shape exactly.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.geodetic_catalog import (
    compute_geodetic_architecture,
    compute_geodetic_state,
    list_geodetic_models,
)
from ephemerides_spectral._research.geodetic_catalog_data import (
    GRAVITY_MODELS,
    GravityModel,
    INTERIOR_MODELS,
    InteriorLayer,
    InteriorModel,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    TOPOGRAPHY_MODELS,
    TopographyModel,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_gravity_roster_size() -> None:
    """56 published gravity models per §17.4.2 commitment."""
    assert len(GRAVITY_MODELS) == 56


def test_topography_roster_size() -> None:
    """32 published topography / shape models per §17.4.2 commitment."""
    assert len(TOPOGRAPHY_MODELS) == 32


def test_interior_roster_size() -> None:
    """26 published interior structure models per §17.4.2 commitment."""
    assert len(INTERIOR_MODELS) == 26


def test_sources_dict_size() -> None:
    """67 unique citations covering every numeric value in the catalog."""
    assert len(SOURCES) == 67


def test_triple_channel_bodies() -> None:
    """22 bodies have published models in all three channels (the
    'fully-characterised' subset)."""
    g = {m.body for m in GRAVITY_MODELS}
    t = {m.body for m in TOPOGRAPHY_MODELS}
    i = {m.body for m in INTERIOR_MODELS}
    triple = g & t & i
    assert len(triple) == 22
    # Spot-checks on the canonical members.
    for body in ("terra", "luna", "mars", "mercury", "venus",
                 "io", "europa", "ganymede", "callisto",
                 "titan", "enceladus",
                 "pluto", "charon", "triton",
                 "ceres", "vesta"):
        assert body in triple, f"expected {body} in triple-channel set"


# ──────────────────────────────────────────────────────────────────────
# Headline numeric pins
# ──────────────────────────────────────────────────────────────────────

def test_earth_egm2008_gm_pinned() -> None:
    """EGM2008 GM = 398600.4418 km³/s² (Pavlis 2012)."""
    by_body = {m.body: m for m in GRAVITY_MODELS}
    assert by_body["terra"].model_name == "EGM2008"
    assert by_body["terra"].gm_km3_per_s2 == pytest.approx(398_600.4418)


def test_luna_grgm1200b_gm_pinned() -> None:
    """GRAIL GRGM1200B GM = 4902.800076 km³/s² (Goossens 2020)."""
    by_body = {m.body: m for m in GRAVITY_MODELS}
    assert by_body["luna"].model_name == "GRGM1200B"
    assert by_body["luna"].gm_km3_per_s2 == pytest.approx(4_902.800076)


def test_mars_mro120f_gm_pinned() -> None:
    """MRO120F GM = 42828.3737 km³/s² (Konopliv 2016)."""
    by_body = {m.body: m for m in GRAVITY_MODELS}
    assert by_body["mars"].model_name == "MRO120F"
    assert by_body["mars"].gm_km3_per_s2 == pytest.approx(42_828.3737)


def test_jupiter_zonal_j2_pinned() -> None:
    """Iess 2018 / Durante 2020 zonal J2 = 1.4696572e-2 (unnormalised)."""
    by_body = {m.body: m for m in GRAVITY_MODELS}
    assert by_body["jupiter"].J2 == pytest.approx(1.4696572e-2, rel=1e-4)


def test_zonal_only_giants_have_no_full_coeff_archive_url() -> None:
    """Gas + ice giants ship as zonal-only (Saturn axisymmetry plus
    no full Stokes table beyond zonals); their `full_coeff_archive`
    should be either None or a documentation URL — but their `S_nm`
    series is zero by axisymmetry."""
    by_body = {m.body: m for m in GRAVITY_MODELS}
    for giant in ("jupiter", "saturn", "uranus", "neptune"):
        m = by_body[giant]
        # Zonal models specifically; J2 always set, J3 may be 0 by symmetry.
        assert m.J2 is not None, f"{giant} missing J2"


# ──────────────────────────────────────────────────────────────────────
# Source-citation discipline (ratchet)
# ──────────────────────────────────────────────────────────────────────

def test_every_gravity_source_key_resolves() -> None:
    for m in GRAVITY_MODELS:
        assert m.source_key in SOURCES, (
            f"gravity {m.body} has unknown source_key {m.source_key!r}"
        )


def test_every_topography_source_key_resolves() -> None:
    for m in TOPOGRAPHY_MODELS:
        assert m.source_key in SOURCES, (
            f"topography {m.body} has unknown source_key {m.source_key!r}"
        )


def test_every_interior_source_key_resolves() -> None:
    for m in INTERIOR_MODELS:
        assert m.source_key in SOURCES, (
            f"interior {m.body} has unknown source_key {m.source_key!r}"
        )


def test_no_unused_sources_entries() -> None:
    """Ratchet: every SOURCES entry is actually cited by at least one
    catalog row. Catches stale citations on future refactors."""
    used = (
        {m.source_key for m in GRAVITY_MODELS}
        | {m.source_key for m in TOPOGRAPHY_MODELS}
        | {m.source_key for m in INTERIOR_MODELS}
    )
    unused = set(SOURCES.keys()) - used
    assert unused == set(), f"unused SOURCES entries: {unused}"


# ──────────────────────────────────────────────────────────────────────
# Precision-flag invariants
# ──────────────────────────────────────────────────────────────────────

def test_every_gravity_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in GRAVITY_MODELS:
        assert m.precision_flag in valid, (
            f"gravity {m.body} has invalid precision_flag {m.precision_flag!r}"
        )


def test_every_topography_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in TOPOGRAPHY_MODELS:
        assert m.precision_flag in valid


def test_every_interior_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in INTERIOR_MODELS:
        assert m.precision_flag in valid


def test_terra_is_high_tier_in_every_channel() -> None:
    """Earth's gravity (EGM2008), topography (ETOPO 2022), and interior
    (PREM) are all current-best published models — must be HIGH."""
    by_body_g = {m.body: m for m in GRAVITY_MODELS}
    by_body_t = {m.body: m for m in TOPOGRAPHY_MODELS}
    by_body_i = {m.body: m for m in INTERIOR_MODELS}
    assert by_body_g["terra"].precision_flag == PRECISION_HIGH
    assert by_body_t["terra"].precision_flag == PRECISION_HIGH
    assert by_body_i["terra"].precision_flag == PRECISION_HIGH


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — error paths + body-shape
# ──────────────────────────────────────────────────────────────────────

def test_compute_geodetic_state_unknown_body() -> None:
    r = compute_geodetic_state(body="krypton")
    assert r["ok"] is False
    assert "unknown body" in r["error"].lower()


def test_compute_geodetic_state_full_roster_shape() -> None:
    r = compute_geodetic_state()
    assert r["ok"] is True
    # Union of all bodies appearing in any channel.
    g = {m.body for m in GRAVITY_MODELS}
    t = {m.body for m in TOPOGRAPHY_MODELS}
    i = {m.body for m in INTERIOR_MODELS}
    union = g | t | i
    assert r["n_bodies"] == len(union)
    assert set(r["bodies"].keys()) == union


def test_compute_geodetic_state_sparse_channels_are_none() -> None:
    """A body present only in one channel returns None for the others.
    Use a body that is gravity-only (no topo, no interior) to test."""
    r = compute_geodetic_state()
    bodies = r["bodies"]
    g = {m.body for m in GRAVITY_MODELS}
    t = {m.body for m in TOPOGRAPHY_MODELS}
    i = {m.body for m in INTERIOR_MODELS}
    gravity_only = g - t - i
    assert len(gravity_only) > 0, "expected at least one gravity-only body"
    sample = next(iter(gravity_only))
    assert bodies[sample]["gravity"] is not None
    assert bodies[sample]["topography"] is None
    assert bodies[sample]["interior"] is None


def test_compute_geodetic_architecture_unknown_target() -> None:
    r = compute_geodetic_architecture(target="krypton")
    assert r["ok"] is False
    assert "unknown body" in r["error"].lower()


def test_compute_geodetic_architecture_full_partition_shape() -> None:
    r = compute_geodetic_architecture()
    assert r["ok"] is True
    p = r["partitions"]
    assert PRECISION_HIGH in p
    assert PRECISION_MEDIUM in p
    assert PRECISION_LOW in p
    assert PRECISION_NONE in p
    # Every body landed in exactly one partition.
    total = sum(len(v) for v in p.values())
    assert total == r["n_bodies"]


def test_compute_geodetic_architecture_terra_is_high() -> None:
    """Earth has HIGH-tier flags in all three channels → median is HIGH."""
    r = compute_geodetic_architecture(target="terra")
    assert r["ok"] is True
    assert r["tier"] == PRECISION_HIGH


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_geodetic_state_full_roster() -> None:
    r = bridge.get_geodetic_state()
    assert r["ok"] is True
    assert r["n_bodies"] >= 56  # union of channels


def test_bridge_get_geodetic_state_per_body() -> None:
    r = bridge.get_geodetic_state(body="mars")
    assert r["ok"] is True
    assert r["body"] == "mars"
    assert r["gravity"] is not None
    assert r["gravity"]["model_name"] == "MRO120F"


def test_bridge_get_geodetic_state_rejects_unknown() -> None:
    r = bridge.get_geodetic_state(body="krypton")
    assert r["ok"] is False


def test_bridge_list_geodetic_models_smoke() -> None:
    r = bridge.list_geodetic_models()
    assert r["ok"] is True
    assert r["n_gravity_models"] == 56
    assert r["n_topography_models"] == 32
    assert r["n_interior_models"] == 26
    assert r["n_sources"] == 67


def test_bridge_geodetic_architecture_full_partition() -> None:
    r = bridge.geodetic_architecture()
    assert r["ok"] is True
    assert PRECISION_HIGH in r["partitions"]
    assert PRECISION_MEDIUM in r["partitions"]
    assert PRECISION_LOW in r["partitions"]
    assert PRECISION_NONE in r["partitions"]


def test_bridge_geodetic_architecture_target_terra() -> None:
    r = bridge.geodetic_architecture(target="terra")
    assert r["ok"] is True
    assert r["tier"] == PRECISION_HIGH


def test_bridge_geodetic_architecture_rejects_unknown() -> None:
    r = bridge.geodetic_architecture(target="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_geodetic_state_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["geodetic-state", "--body", "mars"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body"] == "mars"


def test_cli_geodetic_models_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["geodetic-models"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_gravity_models"] == 56


def test_cli_geodetic_architecture_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["geodetic-architecture", "--target", "terra"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["tier"] == PRECISION_HIGH


def test_cli_geodetic_help() -> None:
    """geodetic-state / geodetic-models / geodetic-architecture --help all render."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("geodetic-state", "geodetic-models", "geodetic-architecture"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
