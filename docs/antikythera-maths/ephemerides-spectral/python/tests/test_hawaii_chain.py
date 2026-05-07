"""v0.24.5 — Sol Hawaiian-Emperor Chain Spectral Catalog tests.

Pins the **first time** the project's graph-Laplacian eigenbasis is
applied to physical features on a single body's surface (rather than
to orbital relationships between bodies). Demonstrates the
**bounded-local-Laplacian / chess-board** insight as an explicit ship.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.hawaii_chain_catalog import (
    get_hawaii_chain,
    get_hawaii_emperor_bend_signature,
    list_hawaii_chain,
)
from ephemerides_spectral._research.hawaii_chain_data import (
    HAWAII_HOTSPOT_LAT_DEG,
    HAWAII_HOTSPOT_LON_DEG,
    HAWAIIAN_EMPEROR_BEND_AGE_MYR,
    HAWAIIAN_EMPEROR_SEAMOUNTS,
    PRECISION_HIGH,
    SOURCES,
    Seamount,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_seamount_count_18() -> None:
    assert len(HAWAIIAN_EMPEROR_SEAMOUNTS) == 18


def test_arc_distribution() -> None:
    """5 emperor + 1 bend (Daikakuji) + 12 hawaiian."""
    arcs = [s.arc for s in HAWAIIAN_EMPEROR_SEAMOUNTS]
    assert arcs.count("emperor") == 5
    assert arcs.count("bend") == 1
    assert arcs.count("hawaiian") == 12


def test_bend_age_47_5_myr() -> None:
    """Sharp & Clague 2006 canonical bend age: 47.5 ± 1.0 Myr."""
    assert HAWAIIAN_EMPEROR_BEND_AGE_MYR == pytest.approx(47.5, abs=0.5)


def test_sources_count() -> None:
    assert len(SOURCES) == 10


def test_seamount_names_unique() -> None:
    names = [s.name for s in HAWAIIAN_EMPEROR_SEAMOUNTS]
    assert len(names) == len(set(names))


def test_meiji_oldest() -> None:
    """Meiji Seamount is the oldest in the catalog (~85 Myr)."""
    oldest = max(HAWAIIAN_EMPEROR_SEAMOUNTS, key=lambda s: s.age_myr)
    assert oldest.name == "meiji"
    assert oldest.age_myr >= 80.0


def test_kilauea_youngest() -> None:
    """Kilauea is the youngest (currently active)."""
    youngest = min(HAWAIIAN_EMPEROR_SEAMOUNTS, key=lambda s: s.age_myr)
    assert youngest.name == "hawaii_kilauea"
    assert youngest.age_myr < 0.1


def test_daikakuji_at_bend_age() -> None:
    """Daikakuji is the bend marker — within ~5 Myr of bend age."""
    by = {s.name: s for s in HAWAIIAN_EMPEROR_SEAMOUNTS}
    daikakuji = by["daikakuji"]
    assert daikakuji.arc == "bend"
    assert abs(daikakuji.age_myr - HAWAIIAN_EMPEROR_BEND_AGE_MYR) < 5.0


# ──────────────────────────────────────────────────────────────────────
# Hawaii hotspot location
# ──────────────────────────────────────────────────────────────────────


def test_hotspot_at_big_island() -> None:
    """Hotspot is at Big Island latitude ~19°N, longitude ~-155°."""
    assert HAWAII_HOTSPOT_LAT_DEG == pytest.approx(19.4, abs=0.5)
    # The catalog uses east-positive 0-360 longitudes for chain
    # seamounts but stores the hotspot in -180..180. Both
    # conventions point to the same place.
    assert -158.0 < HAWAII_HOTSPOT_LON_DEG < -154.0


# ──────────────────────────────────────────────────────────────────────
# Arc-length + plate velocity
# ──────────────────────────────────────────────────────────────────────


def test_arc_length_increases_with_age() -> None:
    """Older seamounts are further from the hotspot."""
    r = get_hawaii_chain()
    smts = sorted(r["seamounts"], key=lambda s: s["age_myr"])
    for prev, curr in zip(smts[:-1], smts[1:]):
        # Arc-length must be monotonically non-decreasing as age increases
        assert curr["arc_length_km"] >= prev["arc_length_km"] - 1.0


def test_plate_velocity_in_published_range() -> None:
    """Pacific Plate velocity from age-vs-arc-length slope:
    8-10 cm/yr (Sharp 2006 / O'Connor 2013)."""
    r = get_hawaii_chain()
    v = r["plate_velocity"]["post_bend_velocity_cm_per_yr"]
    assert 7.0 < v < 11.0


# ──────────────────────────────────────────────────────────────────────
# Graph-Laplacian eigenbasis (the methodology demonstration)
# ──────────────────────────────────────────────────────────────────────


def test_fiedler_eigenvalue_positive() -> None:
    """Connected graph → λ₂ > 0."""
    r = get_hawaii_chain()
    assert r["fiedler_eigenvalue"] > 0.0


def test_eigenvalue_gap_substantial() -> None:
    """A quasi-1D chain has a clean Fiedler partition; the gap
    λ₃ - λ₂ should be at least as large as λ₂ (i.e., the partition
    is structurally crisp)."""
    r = get_hawaii_emperor_bend_signature()
    assert r["eigenvalue_gap"] >= r["fiedler_eigenvalue"]


def test_fiedler_single_zero_crossing() -> None:
    """For a quasi-1D chain, the Fiedler vector should have
    EXACTLY ONE sign change as we walk the chain age-ordered.
    This is the structural confirmation that the chain bisects
    cleanly — same property that v0.18.0 body_architecture's
    Fiedler vector has on the orbital-resonance graph."""
    r = get_hawaii_emperor_bend_signature()
    assert r["n_fiedler_sign_changes"] == 1


def test_fiedler_sign_change_in_hawaiian_arc() -> None:
    """The single sign change happens within the Hawaiian arc
    (geographic spatial gap, not the directional bend at 47.5 Myr).
    Specifically, the gap is between Midway (27.7 Myr) and
    Pearl-and-Hermes Atoll (20 Myr) — a real ~7 Myr / ~700 km gap
    in the chain."""
    r = get_hawaii_emperor_bend_signature()
    sc = r["fiedler_sign_changes"][0]
    older_age, younger_age = sc["at_age_range_myr"]
    # Sign change should be well after the bend (47.5 Myr)
    assert older_age < 40.0
    assert younger_age < older_age


def test_meiji_largest_residual() -> None:
    """The largest residual from the post-bend linear age-vs-arc-
    length fit is at the OLDEST Emperor seamount — Meiji — because
    the linear fit extrapolated ~85 Myr back from the post-bend
    Hawaiian arc misses the bend's directional kink. The bend
    surfaces in the residual structure."""
    r = get_hawaii_emperor_bend_signature()
    assert r["max_residual_seamount"]["name"] == "meiji"
    assert abs(r["max_residual_seamount"]["residual_km"]) > 500.0


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_source_key_resolves() -> None:
    for s in HAWAIIAN_EMPEROR_SEAMOUNTS:
        assert s.source_key in SOURCES


def test_canonical_papers_in_sources() -> None:
    """Sharp & Clague 2006 + Tarduno 2003 + Morgan 1971 must be
    cited — they're the canonical references for the chain's
    interpretation."""
    for ref in ("sharp_clague_2006", "tarduno_2003", "morgan_1971"):
        assert ref in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_hawaii_chain_smoke() -> None:
    r = get_hawaii_chain()
    assert r["ok"] is True
    assert r["n_seamounts"] == 18


def test_get_hawaii_emperor_bend_signature_smoke() -> None:
    r = get_hawaii_emperor_bend_signature()
    assert r["ok"] is True
    assert r["fiedler_eigenvalue"] > 0
    assert r["n_fiedler_sign_changes"] == 1


def test_list_hawaii_chain_smoke() -> None:
    r = list_hawaii_chain()
    assert r["ok"] is True
    assert r["n_seamounts"] == 18
    assert r["n_sources"] == 10


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_hawaii_chain() -> None:
    r = bridge.get_hawaii_chain()
    assert r["ok"] is True
    assert r["n_seamounts"] == 18


def test_bridge_get_hawaii_emperor_bend_signature() -> None:
    r = bridge.get_hawaii_emperor_bend_signature()
    assert r["ok"] is True
    assert r["n_fiedler_sign_changes"] == 1


def test_bridge_list_hawaii_chain() -> None:
    r = bridge.list_hawaii_chain()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_hawaii_chain_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["hawaii-chain"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_seamounts"] == 18


def test_cli_hawaii_emperor_bend_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["hawaii-emperor-bend"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_fiedler_sign_changes"] == 1


def test_cli_hawaii_chain_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["hawaii-chain-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_seamounts"] == 18


def test_cli_hawaii_help() -> None:
    """All v0.24.5 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("hawaii-chain", "hawaii-emperor-bend", "hawaii-chain-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
