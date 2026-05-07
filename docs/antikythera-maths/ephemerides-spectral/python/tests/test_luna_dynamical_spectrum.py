"""v0.24.1 — Sol Luna Dynamical Spectrum Catalog tests.

Pins the second per-body dynamical-spectrum surface:

* 11-mode action-angle catalog (8 angles + 3 actions).
* Headlines: 1:1 tidal lock; forced libration 7.9 arcsec at orbital
  frequency (Williams 2014 LLR — most precise libration in solar
  system); apsidal precession 8.85 yr; nodal precession 18.61 yr.
* THE headline closure invariant: **Saros integer commensurability**
  — 223 synodic, 239 anomalistic, 242 draconitic months, 19 eclipse
  years all agree within ~0.5 day at 6585.5 d ≈ 18.03 yr.
* Cross-references v0.23.0 (luna 1:1 + 7.9 arcsec libration must
  agree) and v0.21.6 (Williams 2014 +3.83 cm/yr migration uses the
  same paper as the libration analysis).
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.luna_dynamical_spectrum_catalog import (
    get_luna_dynamical_spectrum,
    get_luna_saros_commensurability,
    list_luna_dynamical_spectrum,
)
from ephemerides_spectral._research.luna_dynamical_spectrum_data import (
    ECLIPSE_YEAR_DAYS,
    LUNA_ANOMALISTIC_MONTH_DAYS,
    LUNA_APSIDAL_PRECESSION_YEARS,
    LUNA_DRACONITIC_MONTH_DAYS,
    LUNA_DYNAMICAL_MODES,
    LUNA_FORCED_LIBRATION_LONGITUDE_ARCSEC,
    LUNA_NODAL_PRECESSION_YEARS,
    LUNA_NORMALISED_MOI_C_OVER_MR2,
    LUNA_SIDEREAL_MONTH_DAYS,
    LUNA_SYNODIC_MONTH_DAYS,
    PRECISION_HIGH,
    SAROS_COMMENSURABILITY,
    SOURCES,
    DynamicalMode,
    SarosCommensurability,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_mode_count_11() -> None:
    """8 angle modes + 3 action modes."""
    assert len(LUNA_DYNAMICAL_MODES) == 11


def test_8_angles_3_actions() -> None:
    angles = [m for m in LUNA_DYNAMICAL_MODES if m.angle_or_action == "angle"]
    actions = [m for m in LUNA_DYNAMICAL_MODES if m.angle_or_action == "action"]
    assert len(angles) == 8
    assert len(actions) == 3


def test_saros_4_products() -> None:
    assert len(SAROS_COMMENSURABILITY) == 4


def test_sources_count() -> None:
    assert len(SOURCES) == 6


def test_mode_names_unique() -> None:
    names = [m.name for m in LUNA_DYNAMICAL_MODES]
    assert len(names) == len(set(names))


# ──────────────────────────────────────────────────────────────────────
# Lunar months — high-precision invariants (Allen's / DE441)
# ──────────────────────────────────────────────────────────────────────


def test_synodic_month_value() -> None:
    """29.53058886 d — most-cited high-precision value."""
    assert LUNA_SYNODIC_MONTH_DAYS == pytest.approx(29.53059, abs=1e-4)


def test_sidereal_month_value() -> None:
    """27.32166156 d."""
    assert LUNA_SIDEREAL_MONTH_DAYS == pytest.approx(27.32166, abs=1e-4)


def test_synodic_longer_than_sidereal() -> None:
    """Synodic > sidereal because Earth's orbital motion adds ~2 d."""
    assert LUNA_SYNODIC_MONTH_DAYS > LUNA_SIDEREAL_MONTH_DAYS


def test_anomalistic_longer_than_sidereal() -> None:
    """Anomalistic > sidereal because perigee precesses prograde."""
    assert LUNA_ANOMALISTIC_MONTH_DAYS > LUNA_SIDEREAL_MONTH_DAYS


def test_draconitic_shorter_than_sidereal() -> None:
    """Draconitic < sidereal because nodes regress (retrograde)."""
    assert LUNA_DRACONITIC_MONTH_DAYS < LUNA_SIDEREAL_MONTH_DAYS


# ──────────────────────────────────────────────────────────────────────
# 1:1 tidal lock + forced libration (cross-references v0.23.0)
# ──────────────────────────────────────────────────────────────────────


def test_spin_locked_to_sidereal() -> None:
    by = {m.name: m for m in LUNA_DYNAMICAL_MODES}
    spin_period = by["spin_frequency"].period_days
    sidereal_period = by["sidereal_mean_motion"].period_days
    assert spin_period == pytest.approx(sidereal_period, rel=1e-9)


def test_forced_libration_amplitude() -> None:
    """Williams 2014 LLR: 7.9 arcsec amplitude."""
    by = {m.name: m for m in LUNA_DYNAMICAL_MODES}
    lib = by["forced_libration_longitude"]
    assert lib.amplitude_value == pytest.approx(7.9, abs=0.5)


def test_forced_libration_matches_v0_23_0_value() -> None:
    """Cross-reference v0.23.0 spin_orbit_resonance Luna entry."""
    from ephemerides_spectral._research.spin_orbit_resonance_data import (
        SPIN_ORBIT_RESONANCES,
    )
    luna_v23 = next(s for s in SPIN_ORBIT_RESONANCES if s.body == "luna")
    by = {m.name: m for m in LUNA_DYNAMICAL_MODES}
    forced = by["forced_libration_longitude"]
    assert luna_v23.libration_amplitude_arcsec == pytest.approx(
        forced.amplitude_value, rel=1e-3,
    )


def test_C_over_MR2_williams_value() -> None:
    """Williams 2014: C/MR² = 0.3932 ± 0.0002."""
    assert LUNA_NORMALISED_MOI_C_OVER_MR2 == pytest.approx(
        0.3932, abs=0.005,
    )


# ──────────────────────────────────────────────────────────────────────
# Precession periods
# ──────────────────────────────────────────────────────────────────────


def test_apsidal_precession_8_85_years() -> None:
    """Perigee advances with 8.85-year period (prograde)."""
    assert LUNA_APSIDAL_PRECESSION_YEARS == pytest.approx(8.85, abs=0.05)


def test_nodal_precession_18_61_years() -> None:
    """Nodes regress with 18.61-year period (retrograde)."""
    assert LUNA_NODAL_PRECESSION_YEARS == pytest.approx(18.61, abs=0.05)


def test_apsidal_mode_prograde() -> None:
    by = {m.name: m for m in LUNA_DYNAMICAL_MODES}
    assert by["apsidal_precession"].frequency_per_century > 0


def test_nodal_mode_retrograde() -> None:
    by = {m.name: m for m in LUNA_DYNAMICAL_MODES}
    assert by["nodal_precession"].frequency_per_century < 0


# ──────────────────────────────────────────────────────────────────────
# THE Saros commensurability closure invariant
# ──────────────────────────────────────────────────────────────────────


def test_saros_223_synodic_value() -> None:
    """223 × synodic ≈ 6585.32 d."""
    p = next(s for s in SAROS_COMMENSURABILITY if s.integer_count == 223)
    assert p.product_days == pytest.approx(6585.32, abs=0.5)


def test_saros_239_anomalistic_value() -> None:
    """239 × anomalistic ≈ 6585.54 d."""
    p = next(s for s in SAROS_COMMENSURABILITY if s.integer_count == 239)
    assert p.product_days == pytest.approx(6585.54, abs=0.5)


def test_saros_242_draconitic_value() -> None:
    """242 × draconitic ≈ 6585.36 d."""
    p = next(s for s in SAROS_COMMENSURABILITY if s.integer_count == 242)
    assert p.product_days == pytest.approx(6585.36, abs=0.5)


def test_saros_closure_invariant() -> None:
    """THE headline invariant: max spread across the 4 products
    must be < 1 day. This is the small-denominator commensurability
    that produces the 18.03-yr Saros eclipse-recurrence cycle."""
    products = [s.product_days for s in SAROS_COMMENSURABILITY]
    spread = max(products) - min(products)
    assert spread < 1.0, (
        f"Saros closure broken: 4 products span {spread} days "
        f"(expected < 1.0). Products: {products}"
    )


def test_saros_period_is_18_03_years() -> None:
    """Mean Saros period ≈ 18.03 years."""
    products = [s.product_days for s in SAROS_COMMENSURABILITY]
    mean_d = sum(products) / len(products)
    mean_yr = mean_d / 365.25
    assert mean_yr == pytest.approx(18.03, abs=0.02)


def test_saros_integers_lowest_terms() -> None:
    """The Saros (223, 239, 242) triple is in lowest terms — they
    must share no common factor with each other (ensures the
    closure is a maximal commensurability, not a multiple of a
    smaller one)."""
    from math import gcd
    integers = [
        s.integer_count for s in SAROS_COMMENSURABILITY
        if s.integer_count in (223, 239, 242)
    ]
    g = integers[0]
    for n in integers[1:]:
        g = gcd(g, n)
    assert g == 1


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_mode_source_resolves() -> None:
    for m in LUNA_DYNAMICAL_MODES:
        assert m.source_key in SOURCES


def test_every_saros_source_resolves() -> None:
    for s in SAROS_COMMENSURABILITY:
        assert s.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = (
        {m.source_key for m in LUNA_DYNAMICAL_MODES}
        | {s.source_key for s in SAROS_COMMENSURABILITY}
    )
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_luna_dynamical_spectrum_smoke() -> None:
    r = get_luna_dynamical_spectrum()
    assert r["ok"] is True
    assert r["body"] == "luna"
    assert r["n_modes"] == 11


def test_get_luna_saros_commensurability_smoke() -> None:
    r = get_luna_saros_commensurability()
    assert r["ok"] is True
    assert r["max_spread_days"] < 1.0
    assert r["mean_period_years"] == pytest.approx(18.03, abs=0.02)


def test_list_luna_dynamical_spectrum_smoke() -> None:
    r = list_luna_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 11
    assert r["n_saros_products"] == 4
    assert r["n_sources"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_luna_dynamical_spectrum() -> None:
    r = bridge.get_luna_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 11


def test_bridge_get_luna_saros_commensurability() -> None:
    r = bridge.get_luna_saros_commensurability()
    assert r["ok"] is True
    assert r["max_spread_days"] < 1.0


def test_bridge_list_luna_dynamical_spectrum() -> None:
    r = bridge.list_luna_dynamical_spectrum()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_luna_dynamical_spectrum_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["luna-dynamical-spectrum"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["body"] == "luna"
    assert payload["n_modes"] == 11


def test_cli_luna_saros_commensurability_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["luna-saros-commensurability"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["max_spread_days"] < 1.0


def test_cli_luna_dynamical_spectrum_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["luna-dynamical-spectrum-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_modes"] == 11


def test_cli_luna_help() -> None:
    """All v0.24.1 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("luna-dynamical-spectrum",
                "luna-saros-commensurability",
                "luna-dynamical-spectrum-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
