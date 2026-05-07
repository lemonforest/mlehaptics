"""v0.24.6 — Sol Yarkovsky/YORP Catalog tests.

Pins the seventh and final ship in the v0.24.x backlog —
per-asteroid thermal-radiation orbital + spin-state drift.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.yarkovsky_yorp_catalog import (
    get_yarkovsky_yorp,
    get_yorp_attractor_thresholds,
    list_yarkovsky_yorp,
)
from ephemerides_spectral._research.yarkovsky_yorp_data import (
    PRECISION_HIGH,
    ROTATIONAL_FISSION_PERIOD_HOURS,
    SOURCES,
    YARKOVSKY_OBSERVABILITY_DIAMETER_KM,
    YARKOVSKY_YORP_ENTRIES,
    YORP_OBLIQUITY_ATTRACTOR_HI_DEG,
    YORP_OBLIQUITY_ATTRACTOR_LO_DEG,
    YarkovskyYorpEntry,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_roster_size_10() -> None:
    assert len(YARKOVSKY_YORP_ENTRIES) == 10


def test_canonical_targets_present() -> None:
    """Bennu / 2000 PH5 / Apophis / Itokawa / Ryugu must all be in
    the catalog (the canonical Yarkovsky/YORP reference targets)."""
    by = {e.short_name for e in YARKOVSKY_YORP_ENTRIES}
    for required in (
        "bennu", "2000_ph5", "apophis", "itokawa", "ryugu",
        "apollo", "geographos", "1950_da", "golevka", "eger",
    ):
        assert required in by


def test_sources_count() -> None:
    """10 per-row citations + Vokrouhlický-Čapek 2002 framework +
    Rubincam 2000 mechanism = 12 sources."""
    assert len(SOURCES) == 12


def test_short_names_unique() -> None:
    names = [e.short_name for e in YARKOVSKY_YORP_ENTRIES]
    assert len(names) == len(set(names))


# ──────────────────────────────────────────────────────────────────────
# Headlines
# ──────────────────────────────────────────────────────────────────────


def test_bennu_yarkovsky_drift() -> None:
    """Chesley 2014 / Farnocchia 2013: Bennu drifts at -19e-4 AU/Myr
    (retrograde -> inward)."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    bennu = by["bennu"]
    assert bennu.yarkovsky_drift_1e4_au_per_myr == pytest.approx(-19.0, abs=1.0)
    assert bennu.is_prograde is False


def test_2000_ph5_huge_yorp_spin_up() -> None:
    """(54509) 2000 PH5 (YORP itself) -- the first YORP detection
    (Lowry 2007). Very small body (~114 m), so very large spin-up
    rate."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    yorp = by["2000_ph5"]
    assert yorp.yorp_spin_rate_change_1e8_rad_per_day_sq is not None
    assert yorp.yorp_spin_rate_change_1e8_rad_per_day_sq > 100.0


def test_2000_ph5_near_fission_limit() -> None:
    """2000 PH5 has 12-minute rotation period — order-of-magnitude
    near the rotational-fission limit at ~2.2 h. 12 min = 0.2 h
    is well below 2.2 h fission limit (already spun up past it,
    held together by strength rather than self-gravity)."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    yorp = by["2000_ph5"]
    assert yorp.rotation_period_hours < 1.0


def test_itokawa_spin_down_negative_yorp() -> None:
    """Itokawa is one of few measured spin-DOWN cases (Lowry 2014)."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    itokawa = by["itokawa"]
    assert itokawa.yorp_spin_rate_change_1e8_rad_per_day_sq is not None
    assert itokawa.yorp_spin_rate_change_1e8_rad_per_day_sq < 0


def test_1950_da_at_fission_limit() -> None:
    """(29075) 1950 DA: 2.121-h rotation -- AT the rotational-
    fission limit. Cohesive forces required to hold the rubble pile
    together."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    da = by["1950_da"]
    assert da.rotation_period_hours == pytest.approx(
        ROTATIONAL_FISSION_PERIOD_HOURS, abs=0.2,
    )


def test_apophis_yarkovsky_present() -> None:
    """Apophis Yarkovsky drift must be measured (relevant for 2068
    impact-prediction)."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    apophis = by["apophis"]
    assert apophis.yarkovsky_drift_1e4_au_per_myr is not None
    assert abs(apophis.yarkovsky_drift_1e4_au_per_myr) > 0


def test_golevka_first_yarkovsky_detection() -> None:
    """(6489) Golevka — Chesley 2003 first-ever Yarkovsky detection."""
    by = {e.short_name: e for e in YARKOVSKY_YORP_ENTRIES}
    golevka = by["golevka"]
    assert golevka.yarkovsky_drift_1e4_au_per_myr is not None


# ──────────────────────────────────────────────────────────────────────
# Direction-sign convention (prograde outward / retrograde inward)
# ──────────────────────────────────────────────────────────────────────


def test_retrograde_drift_inward() -> None:
    """Diurnal-Yarkovsky direction signature: retrograde rotators
    must drift INWARD (negative da/dt)."""
    for e in YARKOVSKY_YORP_ENTRIES:
        if (
            not e.is_prograde
            and e.yarkovsky_drift_1e4_au_per_myr is not None
        ):
            assert e.yarkovsky_drift_1e4_au_per_myr < 0, (
                f"{e.short_name} is retrograde but has "
                f"da/dt = {e.yarkovsky_drift_1e4_au_per_myr}"
            )


# ──────────────────────────────────────────────────────────────────────
# Threshold constants
# ──────────────────────────────────────────────────────────────────────


def test_rotational_fission_limit_2_2_hours() -> None:
    """Rubble-pile rotational-fission limit ~2.2 h."""
    assert ROTATIONAL_FISSION_PERIOD_HOURS == pytest.approx(2.2, abs=0.1)


def test_yorp_obliquity_attractors() -> None:
    """Vokrouhlický-Čapek 2002: ~55° and ~125° attractors for
    irregular bodies."""
    assert YORP_OBLIQUITY_ATTRACTOR_LO_DEG == pytest.approx(55.0, abs=10)
    assert YORP_OBLIQUITY_ATTRACTOR_HI_DEG == pytest.approx(125.0, abs=10)


def test_observability_diameter_threshold() -> None:
    """Yarkovsky/YORP scales as 1/D² → bodies > ~30 km below
    detection."""
    assert YARKOVSKY_OBSERVABILITY_DIAMETER_KM == pytest.approx(30.0, abs=10)


def test_all_catalog_bodies_below_observability_threshold() -> None:
    """Every body in the catalog must be below the ~30 km observability
    threshold (or the catalog wouldn't include them)."""
    for e in YARKOVSKY_YORP_ENTRIES:
        assert e.diameter_km < YARKOVSKY_OBSERVABILITY_DIAMETER_KM


# ──────────────────────────────────────────────────────────────────────
# Physical-quantity invariants
# ──────────────────────────────────────────────────────────────────────


def test_all_periods_positive() -> None:
    for e in YARKOVSKY_YORP_ENTRIES:
        assert e.rotation_period_hours > 0


def test_all_diameters_positive() -> None:
    for e in YARKOVSKY_YORP_ENTRIES:
        assert e.diameter_km > 0


def test_all_eccentricities_in_valid_range() -> None:
    for e in YARKOVSKY_YORP_ENTRIES:
        assert 0.0 <= e.eccentricity < 1.0


def test_all_semi_major_axes_in_inner_solar_system() -> None:
    """All entries are NEAs / inner-solar-system bodies — a < 3 AU."""
    for e in YARKOVSKY_YORP_ENTRIES:
        assert 0.5 < e.semi_major_axis_au < 3.0


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_entry_source_resolves() -> None:
    for e in YARKOVSKY_YORP_ENTRIES:
        assert e.source_key in SOURCES


def test_framework_references_in_sources() -> None:
    """Vokrouhlický-Čapek 2002 + Rubincam 2000 are framework
    references — must be in SOURCES even if not cited per-row
    (theory references for the threshold constants and the
    YORP mechanism itself)."""
    for ref in ("vokrouhlicky_capek_2002", "rubincam_2000"):
        assert ref in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_yarkovsky_yorp_unknown_body() -> None:
    r = get_yarkovsky_yorp(body="krypton")
    assert r["ok"] is False


def test_get_yarkovsky_yorp_full_roster() -> None:
    r = get_yarkovsky_yorp()
    assert r["ok"] is True
    assert r["n_asteroids"] == 10


def test_get_yarkovsky_yorp_per_body_bennu() -> None:
    r = get_yarkovsky_yorp(body="bennu")
    assert r["ok"] is True
    assert r["entry"]["yarkovsky_drift_1e4_au_per_myr"] < 0


def test_get_yorp_attractor_thresholds_smoke() -> None:
    r = get_yorp_attractor_thresholds()
    assert r["ok"] is True
    assert r["rotational_fission_period_hours"] == pytest.approx(2.2, abs=0.1)


def test_list_yarkovsky_yorp_smoke() -> None:
    r = list_yarkovsky_yorp()
    assert r["ok"] is True
    assert r["n_asteroids"] == 10
    assert r["n_sources"] == 12


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_yarkovsky_yorp() -> None:
    r = bridge.get_yarkovsky_yorp(body="apophis")
    assert r["ok"] is True


def test_bridge_get_yorp_attractor_thresholds() -> None:
    r = bridge.get_yorp_attractor_thresholds()
    assert r["ok"] is True


def test_bridge_list_yarkovsky_yorp() -> None:
    r = bridge.list_yarkovsky_yorp()
    assert r["ok"] is True
    assert r["n_asteroids"] == 10


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_yarkovsky_yorp_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["yarkovsky-yorp", "--body", "bennu"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["entry"]["short_name"] == "bennu"


def test_cli_yorp_attractor_thresholds_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["yorp-attractor-thresholds"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["rotational_fission_period_hours"] == pytest.approx(2.2, abs=0.1)


def test_cli_yarkovsky_yorps_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["yarkovsky-yorps"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_asteroids"] == 10


def test_cli_yarkovsky_help() -> None:
    """All v0.24.6 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("yarkovsky-yorp", "yorp-attractor-thresholds",
                "yarkovsky-yorps"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
