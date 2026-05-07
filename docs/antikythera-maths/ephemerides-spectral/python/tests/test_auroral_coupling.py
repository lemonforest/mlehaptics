"""v0.21.5 — Sol Auroral Coupling Catalog tests.

Pins the fifth cross-channel coupling surface:

* 6-body roster (terra, jupiter, saturn, uranus, neptune, ganymede).
* Headline numerics: Jupiter 10^14 W (1000× Earth; the headline);
  Saturn annular oval traces Cao 2020 axisymmetry; Ganymede
  only-intrinsic-moon-dynamo aurora.
* Morphology / acceleration-mechanism vocabulary checks.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.auroral_coupling_catalog import (
    compute_auroral_coupling,
    list_auroral_couplings,
)
from ephemerides_spectral._research.auroral_coupling_data import (
    ACCEL_COROTATION_ENFORCEMENT,
    ACCEL_SOLAR_WIND_RECONNECTION,
    ACCEL_TILTED_DIPOLE_VARIABLE,
    AURORAL_COUPLINGS,
    AuroralCoupling,
    MORPH_ANNULAR_OVAL,
    MORPH_CIRCULAR_OVAL,
    MORPH_PARTIAL_OVAL,
    MORPH_PATCHY_TIME_VARIABLE,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_6() -> None:
    assert len(AURORAL_COUPLINGS) == 6


def test_canonical_roster_members() -> None:
    by = {m.body for m in AURORAL_COUPLINGS}
    assert by == {"terra", "jupiter", "saturn",
                  "uranus", "neptune", "ganymede"}


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_jupiter_aurora_power_pinned() -> None:
    """Connerney 2017 Juno UVS: Jupiter total auroral power ~10^14 W
    (1000× Earth; the headline of the catalog)."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    jupiter = by["jupiter"]
    assert jupiter.total_power_W == pytest.approx(1.0e14, rel=0.5)
    assert jupiter.dominant_acceleration_mechanism == ACCEL_COROTATION_ENFORCEMENT
    assert jupiter.moon_footprint_observed is True
    assert "JRM33" in jupiter.magnetic_origin_field


def test_saturn_annular_oval_traces_axisymmetry() -> None:
    """Hunt 2014: Saturn annular oval directly traces Cao 2020
    axisymmetry (dipole tilt < 0.007°)."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    saturn = by["saturn"]
    assert saturn.auroral_morphology == MORPH_ANNULAR_OVAL
    assert "Cao 2020" in saturn.magnetic_origin_field
    assert "axisymmetric" in saturn.magnetic_origin_field.lower()


def test_terra_aurora_power_pinned() -> None:
    """Bonfond 2017 review: Earth auroral power ~10^11 W."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    terra = by["terra"]
    assert terra.total_power_W == pytest.approx(1.0e11, rel=0.5)
    assert terra.dominant_acceleration_mechanism == ACCEL_SOLAR_WIND_RECONNECTION


def test_jupiter_1000x_earth_aurora_power() -> None:
    """Jupiter aurora is ~1000× Earth's — the famous comparison."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    ratio = by["jupiter"].total_power_W / by["terra"].total_power_W
    assert ratio >= 100  # at least 100x; headline says ~1000x


def test_uranus_partial_oval_pinned() -> None:
    """Lamy 2017 HST: Uranus partial oval (not full); 58.6° dipole tilt."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    uranus = by["uranus"]
    assert uranus.auroral_morphology == MORPH_PARTIAL_OVAL
    assert uranus.dominant_acceleration_mechanism == ACCEL_TILTED_DIPOLE_VARIABLE


def test_neptune_weakest_aurora() -> None:
    """Neptune has the weakest aurora in catalog (~10^8 W)."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    neptune = by["neptune"]
    other_powers = [
        m.total_power_W for m in AURORAL_COUPLINGS
        if m.body != "neptune" and m.total_power_W is not None
    ]
    assert neptune.total_power_W < min(other_powers)
    assert neptune.precision_flag == PRECISION_LOW


def test_ganymede_only_intrinsic_moon_aurora() -> None:
    """Saur 2015: Ganymede is the only intrinsic-moon-dynamo aurora;
    notes call out subsurface-ocean diagnostic."""
    by = {m.body: m for m in AURORAL_COUPLINGS}
    ganymede = by["ganymede"]
    assert ganymede.notes is not None
    assert "ocean" in ganymede.notes.lower()
    assert "Kivelson 2002" in ganymede.magnetic_origin_field


def test_morphology_vocabulary() -> None:
    """All morphology values come from the constant set."""
    valid = {MORPH_CIRCULAR_OVAL, MORPH_ANNULAR_OVAL,
             MORPH_PARTIAL_OVAL, MORPH_PATCHY_TIME_VARIABLE}
    for m in AURORAL_COUPLINGS:
        assert m.auroral_morphology in valid


def test_acceleration_mechanism_vocabulary() -> None:
    """All mechanism values come from the constant set."""
    valid = {ACCEL_SOLAR_WIND_RECONNECTION, ACCEL_COROTATION_ENFORCEMENT,
             ACCEL_TILTED_DIPOLE_VARIABLE}
    for m in AURORAL_COUPLINGS:
        # Note: ACCEL_MOON_FOOTPRINT exists but not used in v0.21.5
        # (since Io footprint is tracked via moon_footprint_observed
        # flag rather than as the dominant mechanism).
        assert m.dominant_acceleration_mechanism in valid


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in AURORAL_COUPLINGS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in AURORAL_COUPLINGS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_auroral_coupling(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_auroral_coupling()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_compute_per_body_jupiter() -> None:
    r = compute_auroral_coupling(body="jupiter")
    assert r["ok"] is True
    assert r["coupling"]["moon_footprint_observed"] is True


def test_list_auroral_couplings_smoke() -> None:
    r = list_auroral_couplings()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_auroral_coupling_smoke() -> None:
    r = bridge.get_auroral_coupling(body="saturn")
    assert r["ok"] is True
    assert r["coupling"]["auroral_morphology"] == MORPH_ANNULAR_OVAL


def test_bridge_get_auroral_coupling_full_roster() -> None:
    r = bridge.get_auroral_coupling()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_bridge_list_auroral_couplings_smoke() -> None:
    r = bridge.list_auroral_couplings()
    assert r["ok"] is True


def test_bridge_get_auroral_coupling_rejects_unknown() -> None:
    r = bridge.get_auroral_coupling(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_auroral_coupling_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["auroral-coupling", "--body", "jupiter"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["coupling"]["moon_footprint_observed"] is True


def test_cli_auroral_couplings_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["auroral-couplings"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 6


def test_cli_auroral_help() -> None:
    """Both v0.21.5 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("auroral-coupling", "auroral-couplings"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
