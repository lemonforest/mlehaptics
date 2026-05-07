"""v0.21.4 — Sol Rotational Constraint Catalog tests.

Pins the fourth cross-channel coupling surface:

* 7-body roster (terra, mars, jupiter, saturn, io, europa, ganymede).
* Headline numerics: Mathews 2002 Earth FCN 430.21 days; Mankovich
  2021 Saturn rotation 0.43539 days = 10h 33min 38s (the headline);
  Le Maistre 2023 Mars core radius 1830 km; Lainey 2009 Io Q ~80.
* 6 sources (Lainey 2020 covers both Europa + Ganymede).
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.rotational_constraint_catalog import (
    compute_rotational_constraint,
    list_rotational_constraints,
)
from ephemerides_spectral._research.rotational_constraint_data import (
    OBS_FREE_CORE_NUTATION,
    OBS_INSIGHT_NUTATION,
    OBS_RING_SEISMOLOGY,
    OBS_TIDAL_DISSIPATION_Q,
    OBS_ZONAL_WIND_DEPTH,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    ROTATIONAL_CONSTRAINTS,
    RotationalConstraint,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_7() -> None:
    assert len(ROTATIONAL_CONSTRAINTS) == 7


def test_canonical_roster_members() -> None:
    by = {m.body for m in ROTATIONAL_CONSTRAINTS}
    expected = {"terra", "mars", "jupiter", "saturn",
                "io", "europa", "ganymede"}
    assert by == expected


def test_sources_count() -> None:
    """6 sources — Lainey 2020 covers both Europa and Ganymede."""
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_earth_free_core_nutation_pinned() -> None:
    """Mathews 2002 IERS standard: FCN period = 430.21 days."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    terra = by["terra"]
    assert terra.observation_type == OBS_FREE_CORE_NUTATION
    assert terra.constraint_value == pytest.approx(430.21, abs=0.5)
    assert terra.units == "days"


def test_saturn_ring_seismology_rotation_pinned() -> None:
    """The headline. Mankovich & Fuller 2021: ring-seismology revises
    Saturn rotation from Voyager 10:39 → 10:33 = 0.43539 days."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    saturn = by["saturn"]
    assert saturn.observation_type == OBS_RING_SEISMOLOGY
    assert saturn.constraint_value == pytest.approx(0.43539, abs=0.001)
    assert saturn.units == "days"
    assert saturn.precision_flag == PRECISION_HIGH


def test_mars_insight_core_radius_pinned() -> None:
    """Le Maistre 2023 InSight RISE: core radius 1830 ± 40 km."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    mars = by["mars"]
    assert mars.observation_type == OBS_INSIGHT_NUTATION
    assert mars.constraint_value == pytest.approx(1830.0, abs=50)
    assert mars.units == "km"


def test_jupiter_zonal_wind_depth_pinned() -> None:
    """Kaspi 2018 from Juno J6/J8/J10: wind base ~3000 km depth."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    jupiter = by["jupiter"]
    assert jupiter.observation_type == OBS_ZONAL_WIND_DEPTH
    assert jupiter.constraint_value == pytest.approx(3000.0, abs=500)
    assert jupiter.units == "km"


def test_io_tidal_q_pinned() -> None:
    """Lainey 2009: Io Q ≈ 35-100; vigorous tidal dissipation
    consistent with volcanic activity."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    io = by["io"]
    assert io.observation_type == OBS_TIDAL_DISSIPATION_Q
    assert 30 <= io.constraint_value <= 110


def test_europa_ganymede_higher_q_than_io() -> None:
    """Galileans Q ordering: Io << Europa, Ganymede (much less
    dissipative because no volcanic forcing)."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    assert by["europa"].constraint_value > by["io"].constraint_value
    assert by["ganymede"].constraint_value > by["io"].constraint_value


def test_observation_types_diverse() -> None:
    """Catalog spans 5 distinct observation types."""
    types = {m.observation_type for m in ROTATIONAL_CONSTRAINTS}
    assert len(types) >= 5


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in ROTATIONAL_CONSTRAINTS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in ROTATIONAL_CONSTRAINTS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


def test_lainey_2020_shared_by_europa_ganymede() -> None:
    """Lainey 2020 is the shared citation for both Europa and Ganymede
    Q-factors — explains why we have 6 sources for 7 bodies."""
    by = {m.body: m for m in ROTATIONAL_CONSTRAINTS}
    assert by["europa"].source_key == "lainey_2020"
    assert by["ganymede"].source_key == "lainey_2020"


# ──────────────────────────────────────────────────────────────────────
# Precision-flag invariants
# ──────────────────────────────────────────────────────────────────────

def test_every_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in ROTATIONAL_CONSTRAINTS:
        assert m.precision_flag in valid


def test_high_tier_members() -> None:
    """Multi-mission high-confidence: terra, mars, jupiter, saturn, io."""
    by = {m.body: m.precision_flag for m in ROTATIONAL_CONSTRAINTS}
    assert by["terra"] == PRECISION_HIGH
    assert by["saturn"] == PRECISION_HIGH


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_rotational_constraint(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_rotational_constraint()
    assert r["ok"] is True
    assert r["n_bodies"] == 7


def test_compute_per_body_saturn() -> None:
    r = compute_rotational_constraint(body="saturn")
    assert r["ok"] is True
    assert r["constraint"]["observation_type"] == OBS_RING_SEISMOLOGY


def test_list_rotational_constraints_smoke() -> None:
    r = list_rotational_constraints()
    assert r["ok"] is True
    assert r["n_bodies"] == 7


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_rotational_constraint_smoke() -> None:
    r = bridge.get_rotational_constraint(body="saturn")
    assert r["ok"] is True
    assert r["constraint"]["constraint_value"] == pytest.approx(0.43539, abs=0.001)


def test_bridge_get_rotational_constraint_full_roster() -> None:
    r = bridge.get_rotational_constraint()
    assert r["ok"] is True
    assert r["n_bodies"] == 7


def test_bridge_list_rotational_constraints_smoke() -> None:
    r = bridge.list_rotational_constraints()
    assert r["ok"] is True


def test_bridge_get_rotational_constraint_rejects_unknown() -> None:
    r = bridge.get_rotational_constraint(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_rotational_constraint_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["rotational-constraint", "--body", "saturn"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["constraint"]["observation_type"] == OBS_RING_SEISMOLOGY


def test_cli_rotational_constraints_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["rotational-constraints"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 7


def test_cli_rotational_help() -> None:
    """Both v0.21.4 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("rotational-constraint", "rotational-constraints"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
