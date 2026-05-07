"""v0.24.7 — Sol Mars Tharsis Volcanic Chain Spectral Catalog tests.

Pins the **second time** the project's graph-Laplacian eigenbasis is
applied to physical features on a single body's surface (rather than
to orbital relationships between bodies), and the **first time** on
a body **without** plate tectonics. Demonstrates the
**bounded-local-Laplacian** methodology cross-body: Hawaii (v0.24.5)
extracts a *trajectory*; Mars Tharsis extracts a *cogenetic family*.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.mars_tharsis_catalog import (
    get_mars_tharsis_chain,
    get_tharsis_fiedler_signature,
    list_mars_tharsis_chain,
)
from ephemerides_spectral._research.mars_tharsis_data import (
    MARS_RADIUS_KM,
    MARS_THARSIS_VOLCANOES,
    PRECISION_HIGH,
    SOURCES,
    THARSIS_CENTRE_LAT_DEG,
    THARSIS_CENTRE_LON_DEG,
    THARSIS_MONTES_RIDGE_AZIMUTH_DEG,
    TharsisVolcano,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_volcano_count_5() -> None:
    assert len(MARS_THARSIS_VOLCANOES) == 5


def test_role_distribution() -> None:
    """3 tharsis_montes + 1 olympus_outlier + 1 alba_outlier."""
    roles = [v.role for v in MARS_THARSIS_VOLCANOES]
    assert roles.count("tharsis_montes") == 3
    assert roles.count("olympus_outlier") == 1
    assert roles.count("alba_outlier") == 1


def test_volcano_names_unique() -> None:
    names = [v.name for v in MARS_THARSIS_VOLCANOES]
    assert len(names) == len(set(names))


def test_sources_count() -> None:
    """7 Mars-specific citations + Morgan 1971 cross-reference."""
    assert len(SOURCES) == 8


def test_olympus_mons_present() -> None:
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    assert "olympus_mons" in by
    assert by["olympus_mons"].role == "olympus_outlier"


def test_three_tharsis_montes_present() -> None:
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    for name in ("arsia_mons", "pavonis_mons", "ascraeus_mons"):
        assert name in by
        assert by[name].role == "tharsis_montes"


def test_alba_mons_present() -> None:
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    assert "alba_mons" in by
    assert by["alba_mons"].role == "alba_outlier"


# ──────────────────────────────────────────────────────────────────────
# Headline magnitudes (no-plate-tectonics super-volcano regime)
# ──────────────────────────────────────────────────────────────────────


def test_olympus_mons_largest_volcano() -> None:
    """Olympus Mons summit elevation ~21 km above MOLA datum, 600 km
    base diameter — the canonical super-volcano consequence of
    stationary-plume-without-plate-motion."""
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    olympus = by["olympus_mons"]
    assert olympus.summit_elevation_m > 20000.0
    assert olympus.edifice_diameter_km >= 500.0


def test_olympus_mons_taller_than_tharsis_montes() -> None:
    """Olympus Mons is the tallest edifice in the Tharsis system."""
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    olympus_h = by["olympus_mons"].summit_elevation_m
    montes_h = max(
        by[n].summit_elevation_m
        for n in ("arsia_mons", "pavonis_mons", "ascraeus_mons")
    )
    assert olympus_h > montes_h


def test_alba_mons_widest_shortest() -> None:
    """Alba Mons is the broadest (~1500 km) but much shorter
    (~6.8 km) than the Tharsis Montes — distinct morphology that
    reflects its earlier (Hesperian) phase of Tharsis volcanism."""
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    alba = by["alba_mons"]
    assert alba.edifice_diameter_km >= 1000.0
    assert alba.summit_elevation_m < 10000.0


def test_alba_mons_oldest() -> None:
    """Alba is the only volcano with surface age > 1 Gyr."""
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    alba = by["alba_mons"]
    assert alba.age_myr >= 1000.0
    others = [
        v for v in MARS_THARSIS_VOLCANOES
        if v.name != "alba_mons"
    ]
    assert all(v.age_myr < 1000.0 for v in others)


def test_tharsis_montes_recent_activity() -> None:
    """The three Tharsis Montes have young surface flows (<200 Myr).
    Werner 2009 + Hartmann & Neukum 2001 crater-count chronologies."""
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    for name in ("arsia_mons", "pavonis_mons", "ascraeus_mons"):
        assert by[name].age_myr < 200.0


# ──────────────────────────────────────────────────────────────────────
# Mars geometry
# ──────────────────────────────────────────────────────────────────────


def test_mars_radius_value() -> None:
    """Mars mean radius from MOLA / IAU."""
    assert MARS_RADIUS_KM == pytest.approx(3389.5, abs=1.0)


def test_tharsis_centre_at_equator() -> None:
    """Tharsis bulge centre is at ~0°N (Anderson 2001)."""
    assert abs(THARSIS_CENTRE_LAT_DEG) < 5.0
    assert 250.0 < THARSIS_CENTRE_LON_DEG < 280.0


def test_ridge_azimuth_NE_SW() -> None:
    """Tharsis Montes ridge runs NE-SW (~040 deg)."""
    assert 30.0 < THARSIS_MONTES_RIDGE_AZIMUTH_DEG < 50.0


def test_pavonis_at_equator() -> None:
    """Pavonis Mons sits within ~5° of the Mars equator."""
    by = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    assert abs(by["pavonis_mons"].latitude_deg) < 5.0


# ──────────────────────────────────────────────────────────────────────
# Graph-Laplacian eigenbasis (the methodology demonstration)
# ──────────────────────────────────────────────────────────────────────


def test_fiedler_eigenvalue_positive() -> None:
    """Connected graph -> lambda_2 > 0."""
    r = get_mars_tharsis_chain()
    assert r["fiedler_eigenvalue"] > 0.0


def test_eigenvalue_gap_substantial() -> None:
    """Cogenetic-family structure -> the Fiedler partition is crisp;
    the gap lambda_3 - lambda_2 should be a meaningful fraction of
    lambda_2 itself."""
    r = get_tharsis_fiedler_signature()
    assert r["eigenvalue_gap"] > 0.3 * r["fiedler_eigenvalue"]


def test_alba_isolated_in_fiedler_partition() -> None:
    """The Fiedler partition isolates Alba Mons (the geographically
    distant N outlier) from the four young Tharsis-region volcanoes.
    This is the structural confirmation that the bounded-local
    Laplacian surfaces the cogenetic-family structure rather than
    chronological trajectory."""
    r = get_tharsis_fiedler_signature()
    neg = [e["name"] for e in r["fiedler_clusters"]["negative_cluster"]]
    pos = [e["name"] for e in r["fiedler_clusters"]["positive_cluster"]]
    assert "alba_mons" in neg
    assert "alba_mons" not in pos


def test_three_tharsis_montes_clustered() -> None:
    """Arsia / Pavonis / Ascraeus all sit in the same Fiedler-sign
    cluster — the NE-SW ridge is the bounded-local proximity
    cluster in this 5-volcano roster."""
    r = get_tharsis_fiedler_signature()
    neg = {e["name"] for e in r["fiedler_clusters"]["negative_cluster"]}
    pos = {e["name"] for e in r["fiedler_clusters"]["positive_cluster"]}
    montes = {"arsia_mons", "pavonis_mons", "ascraeus_mons"}
    # All three on same side
    assert montes.issubset(neg) or montes.issubset(pos)


def test_olympus_residual_substantial() -> None:
    """Olympus Mons sits >500 km off the Tharsis Montes ridge axis —
    a clear structural outlier from the deep-mantle ridge that
    produced the three aligned Montes."""
    r = get_tharsis_fiedler_signature()
    assert r["olympus_residual_km"] > 500.0


def test_alba_residual_substantial() -> None:
    """Alba Mons also sits far off the Tharsis Montes ridge axis."""
    r = get_tharsis_fiedler_signature()
    assert r["alba_residual_km"] > 500.0


def test_no_directional_bend_on_no_plate_tectonics() -> None:
    """Cross-channel observation: the Mars Tharsis system has NO
    directional bend (no plate motion -> no bend record). The
    interpretation field must say so."""
    r = get_tharsis_fiedler_signature()
    interp = r["interpretation"].lower()
    assert "plate" in interp
    assert "no" in interp or "without" in interp


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_source_key_resolves() -> None:
    for v in MARS_THARSIS_VOLCANOES:
        assert v.source_key in SOURCES


def test_canonical_papers_in_sources() -> None:
    """Hartmann + Werner + Plescia + Smith MOLA + Anderson must all
    be cited — they're the canonical Mars-volcano references."""
    for ref in (
        "hartmann_neukum_2001", "hartmann_2005", "werner_2009",
        "plescia_2004", "smith_2001_mola", "anderson_2001",
    ):
        assert ref in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_mars_tharsis_chain_smoke() -> None:
    r = get_mars_tharsis_chain()
    assert r["ok"] is True
    assert r["n_volcanoes"] == 5
    assert r["mars_radius_km"] == pytest.approx(3389.5, abs=1.0)


def test_get_tharsis_fiedler_signature_smoke() -> None:
    r = get_tharsis_fiedler_signature()
    assert r["ok"] is True
    assert r["fiedler_eigenvalue"] > 0
    assert r["fiedler_clusters"]["n_negative"] >= 1
    assert r["fiedler_clusters"]["n_positive"] >= 1


def test_list_mars_tharsis_chain_smoke() -> None:
    r = list_mars_tharsis_chain()
    assert r["ok"] is True
    assert r["n_volcanoes"] == 5
    assert r["n_sources"] == 8


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_mars_tharsis_chain() -> None:
    r = bridge.get_mars_tharsis_chain()
    assert r["ok"] is True
    assert r["n_volcanoes"] == 5


def test_bridge_get_tharsis_fiedler_signature() -> None:
    r = bridge.get_tharsis_fiedler_signature()
    assert r["ok"] is True
    assert r["fiedler_eigenvalue"] > 0


def test_bridge_list_mars_tharsis_chain() -> None:
    r = bridge.list_mars_tharsis_chain()
    assert r["ok"] is True
    assert r["n_volcanoes"] == 5


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_mars_tharsis_chain_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mars-tharsis-chain"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_volcanoes"] == 5


def test_cli_tharsis_fiedler_signature_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["tharsis-fiedler-signature"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["fiedler_eigenvalue"] > 0


def test_cli_mars_tharsis_chain_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mars-tharsis-chain-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_volcanoes"] == 5


def test_cli_mars_tharsis_help() -> None:
    """All v0.24.7 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in (
        "mars-tharsis-chain",
        "tharsis-fiedler-signature",
        "mars-tharsis-chain-full",
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
