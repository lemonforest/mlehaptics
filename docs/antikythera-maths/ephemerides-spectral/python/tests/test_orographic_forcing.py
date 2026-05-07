"""v0.21.3 — Sol Orographic Forcing Catalog tests.

Pins the third cross-channel coupling surface in the §17.4.2 v0.21.x
sequence:

* 4-body roster (terra, mars, venus, titan).
* Headline numerics: Mars Tharsis Bulge ~10 km / 10000 km / k=2 mode
  surviving to 50 km altitude (Hollingsworth 1997 — the headline
  planetary case); Earth Tibetan Plateau k=2 forcer (Held 2002);
  Venus + Titan super-rotation suppression (LOW precision flags;
  is_stationary_wave_observed=False).
* Citation discipline.
* Bridge + CLI surfaces.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.orographic_forcing import (
    compute_orographic_forcing,
    list_orographic_forcings,
)
from ephemerides_spectral._research.orographic_forcing_data import (
    OROGRAPHIC_FORCINGS,
    OrographicForcing,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_4() -> None:
    assert len(OROGRAPHIC_FORCINGS) == 4


def test_canonical_roster_members() -> None:
    by = {m.body for m in OROGRAPHIC_FORCINGS}
    assert by == {"terra", "mars", "venus", "titan"}


def test_sources_count() -> None:
    assert len(SOURCES) == 4


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_mars_tharsis_bulge_pinned() -> None:
    """Hollingsworth 1997: Tharsis Bulge ~10 km / ~10000 km / k=2;
    standing wave survives to ~50 km altitude (mesopause)."""
    by = {m.body: m for m in OROGRAPHIC_FORCINGS}
    mars = by["mars"]
    assert mars.dominant_orographic_feature_name == "Tharsis Bulge"
    assert mars.feature_height_km == pytest.approx(10.0, abs=2)
    assert mars.feature_width_km == pytest.approx(10000.0, abs=2000)
    assert mars.dominant_zonal_wavenumber == 2
    assert "50 km" in mars.standing_wave_layer or "mesopause" in mars.standing_wave_layer.lower()
    assert mars.is_stationary_wave_observed is True
    assert mars.precision_flag == PRECISION_HIGH


def test_terra_tibetan_plateau_pinned() -> None:
    """Held 2002 / Hoskins & Karoly 1981: Tibetan Plateau forcer."""
    by = {m.body: m for m in OROGRAPHIC_FORCINGS}
    terra = by["terra"]
    assert "Tibetan" in terra.dominant_orographic_feature_name
    assert terra.dominant_zonal_wavenumber == 2
    assert terra.is_stationary_wave_observed is True
    assert terra.precision_flag == PRECISION_HIGH


def test_venus_super_rotation_suppression() -> None:
    """Lebonnois 2010: Venus super-rotation suppresses classic
    stationary-wave physics; LOW precision; observed=False."""
    by = {m.body: m for m in OROGRAPHIC_FORCINGS}
    venus = by["venus"]
    assert venus.precision_flag == PRECISION_LOW
    assert venus.is_stationary_wave_observed is False
    assert venus.notes is not None
    assert "super-rotation" in venus.notes.lower()


def test_titan_super_rotation_suppression() -> None:
    """Charnay & Lebonnois 2012: Titan super-rotation, analogous to
    Venus; LOW precision; observed=False."""
    by = {m.body: m for m in OROGRAPHIC_FORCINGS}
    titan = by["titan"]
    assert titan.precision_flag == PRECISION_LOW
    assert titan.is_stationary_wave_observed is False


def test_observed_split() -> None:
    """terra + mars have observationally-confirmed standing waves;
    venus + titan are GCM-only."""
    by = {m.body: m for m in OROGRAPHIC_FORCINGS}
    assert by["terra"].is_stationary_wave_observed is True
    assert by["mars"].is_stationary_wave_observed is True
    assert by["venus"].is_stationary_wave_observed is False
    assert by["titan"].is_stationary_wave_observed is False


def test_forcing_amplitude_strings_valid() -> None:
    valid = {"strong", "moderate", "weak", "negligible"}
    for m in OROGRAPHIC_FORCINGS:
        assert m.forcing_amplitude_relative in valid


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in OROGRAPHIC_FORCINGS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in OROGRAPHIC_FORCINGS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_orographic_forcing(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_orographic_forcing()
    assert r["ok"] is True
    assert r["n_bodies"] == 4


def test_compute_per_body_mars() -> None:
    r = compute_orographic_forcing(body="mars")
    assert r["ok"] is True
    assert r["forcing"]["dominant_orographic_feature_name"] == "Tharsis Bulge"


def test_list_orographic_forcings_smoke() -> None:
    r = list_orographic_forcings()
    assert r["ok"] is True
    assert r["n_bodies"] == 4


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_orographic_forcing_smoke() -> None:
    r = bridge.get_orographic_forcing(body="mars")
    assert r["ok"] is True
    assert r["forcing"]["dominant_zonal_wavenumber"] == 2


def test_bridge_get_orographic_forcing_full_roster() -> None:
    r = bridge.get_orographic_forcing()
    assert r["ok"] is True
    assert r["n_bodies"] == 4


def test_bridge_list_orographic_forcings_smoke() -> None:
    r = bridge.list_orographic_forcings()
    assert r["ok"] is True


def test_bridge_get_orographic_forcing_rejects_unknown() -> None:
    r = bridge.get_orographic_forcing(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_orographic_forcing_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["orographic-forcing", "--body", "mars"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["forcing"]["dominant_orographic_feature_name"] == "Tharsis Bulge"


def test_cli_orographic_forcings_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["orographic-forcings"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 4


def test_cli_orographic_help() -> None:
    """Both v0.21.3 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("orographic-forcing", "orographic-forcings"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
