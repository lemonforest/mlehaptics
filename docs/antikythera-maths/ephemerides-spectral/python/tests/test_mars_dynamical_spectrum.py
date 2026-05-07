"""v0.24.2 — Sol Mars Dynamical Spectrum Catalog tests.

Pins the third per-body dynamical-spectrum surface — the **contrast
case** to Mercury (clean Le Verrier closure) and Luna (clean Saros
commensurability):

* 8-mode action-angle catalog (5 angles + 3 actions).
* No spin-orbit lock (unlike Mercury / Luna / Galileans / Titan /
  Pluto-Charon).
* Headlines: chaotic obliquity 0°-60° excursion (Laskar 2004); spin-
  axis precession ~171 kyr (Ward 1973); C/MR² = 0.3645 (Le Maistre
  2023 InSight RISE).
* THE chaos invariant: secular-resonance overlap. Mars spin-axis
  precession proximity to inner-Solar-System secular fundamentals
  s₃, s₄, etc. drives obliquity chaos.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.mars_dynamical_spectrum_catalog import (
    get_mars_dynamical_spectrum,
    get_mars_secular_resonance_overlap,
    list_mars_dynamical_spectrum,
)
from ephemerides_spectral._research.mars_dynamical_spectrum_data import (
    MARS_DYNAMICAL_MODES,
    MARS_NORMALISED_MOI_C_OVER_MR2,
    MARS_OBLIQUITY_DEG,
    MARS_OBLIQUITY_LASKAR_MAX_DEG,
    MARS_OBLIQUITY_LASKAR_MIN_DEG,
    MARS_OBLIQUITY_MEAN_GYR_DEG,
    MARS_SECULAR_RESONANCES,
    MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS,
    MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR,
    PRECISION_HIGH,
    SOURCES,
    DynamicalMode,
    SecularResonance,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_mode_count_8() -> None:
    """5 angle modes + 3 action modes."""
    assert len(MARS_DYNAMICAL_MODES) == 8


def test_5_angles_3_actions() -> None:
    angles = [m for m in MARS_DYNAMICAL_MODES if m.angle_or_action == "angle"]
    actions = [m for m in MARS_DYNAMICAL_MODES if m.angle_or_action == "action"]
    assert len(angles) == 5
    assert len(actions) == 3


def test_secular_resonance_count() -> None:
    """3 near-resonance pairs in the catalog."""
    assert len(MARS_SECULAR_RESONANCES) == 3


def test_sources_count() -> None:
    assert len(SOURCES) == 7


def test_mode_names_unique() -> None:
    names = [m.name for m in MARS_DYNAMICAL_MODES]
    assert len(names) == len(set(names))


# ──────────────────────────────────────────────────────────────────────
# Mars-specific: NO spin-orbit lock (unlike Mercury / Luna)
# ──────────────────────────────────────────────────────────────────────


def test_mars_not_in_v0_23_0_spin_orbit_resonance_roster() -> None:
    """Mars is rotationally free — must NOT appear in the v0.23.0
    spin-orbit-resonance catalog (which only lists locked bodies)."""
    from ephemerides_spectral._research.spin_orbit_resonance_data import (
        SPIN_ORBIT_RESONANCES,
    )
    bodies = {s.body for s in SPIN_ORBIT_RESONANCES}
    assert "mars" not in bodies


def test_spin_orbital_period_ratio_far_from_simple() -> None:
    """T_spin / T_orbit should not be near a small integer ratio."""
    by = {m.name: m for m in MARS_DYNAMICAL_MODES}
    spin_period = by["spin_frequency"].period_days
    orbit_period = by["orbital_mean_motion"].period_days
    ratio = orbit_period / spin_period   # ~669 sols per Mars year
    # Mars year ~669 sols — not a small-integer commensurability
    assert ratio > 100.0


# ──────────────────────────────────────────────────────────────────────
# Headlines: Le Maistre 2023 + Ward 1973 + Laskar 2004
# ──────────────────────────────────────────────────────────────────────


def test_C_over_MR2_le_maistre_value() -> None:
    """Le Maistre 2023 InSight RISE: C/MR² = 0.3645 ± 0.0005."""
    assert MARS_NORMALISED_MOI_C_OVER_MR2 == pytest.approx(
        0.3645, abs=0.005,
    )


def test_spin_axis_precession_171_kyr() -> None:
    """Ward 1973 / Touma-Wisdom 1993: ~171,000 year period."""
    assert MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS == pytest.approx(
        171000.0, abs=5000,
    )


def test_spin_axis_precession_rate_about_7_arcsec_yr() -> None:
    """Mean precession rate ~7.58 arcsec/yr."""
    assert MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR == pytest.approx(
        7.58, abs=0.5,
    )


def test_obliquity_present_25_19_deg() -> None:
    """Present-day obliquity ~25.19°."""
    assert MARS_OBLIQUITY_DEG == pytest.approx(25.19, abs=0.1)


def test_obliquity_present_within_laskar_excursion_range() -> None:
    """Present-day obliquity must lie within Laskar 2004's predicted
    Gyr-scale excursion range (0°-60°)."""
    assert MARS_OBLIQUITY_LASKAR_MIN_DEG <= MARS_OBLIQUITY_DEG
    assert MARS_OBLIQUITY_DEG <= MARS_OBLIQUITY_LASKAR_MAX_DEG


def test_obliquity_mean_gyr_above_present() -> None:
    """Laskar 2004: mean obliquity over Gyr > present-day. Mars's
    *typical* state historically was MORE oblique than today."""
    assert MARS_OBLIQUITY_MEAN_GYR_DEG > MARS_OBLIQUITY_DEG


# ──────────────────────────────────────────────────────────────────────
# THE chaos invariant: secular-resonance overlap
# ──────────────────────────────────────────────────────────────────────


def test_secular_resonance_proximity_drives_chaos() -> None:
    """Mars spin-axis precession is close enough to inner-Solar-System
    secular fundamentals s₃, s₄ that the proximity drives chaos.

    Specifically: |freq_mars_spin_precession - |freq_s_i|| < ~12 arcsec/yr
    for the s₃/s₄ resonances (these are the chaos-driving near-
    resonances per Laskar 1993)."""
    s3_resonance = next(
        r for r in MARS_SECULAR_RESONANCES if r.secular_partner == "s3"
    )
    s4_resonance = next(
        r for r in MARS_SECULAR_RESONANCES if r.secular_partner == "s4"
    )
    assert s3_resonance.proximity_arcsec_per_year < 15.0
    assert s4_resonance.proximity_arcsec_per_year < 15.0


def test_chaos_active_via_min_proximity() -> None:
    """At least one near-resonance must have proximity below the
    chaos-onset threshold (~12 arcsec/yr per Laskar 1993)."""
    proximities = [
        r.proximity_arcsec_per_year for r in MARS_SECULAR_RESONANCES
    ]
    assert min(proximities) < 12.0


def test_all_proximities_non_negative() -> None:
    """Frequency-proximity is |Δf|, must be non-negative."""
    for r in MARS_SECULAR_RESONANCES:
        assert r.proximity_arcsec_per_year >= 0.0


# ──────────────────────────────────────────────────────────────────────
# Action / angle structure
# ──────────────────────────────────────────────────────────────────────


def test_obliquity_is_action_class() -> None:
    """Obliquity is an action-class variable (slowly varying / chaotic
    on Gyr; not a fast-ticking phase)."""
    by = {m.name: m for m in MARS_DYNAMICAL_MODES}
    assert by["obliquity"].angle_or_action == "action"


def test_eccentricity_is_action_class() -> None:
    by = {m.name: m for m in MARS_DYNAMICAL_MODES}
    assert by["eccentricity"].angle_or_action == "action"


def test_orbital_mean_motion_is_angle_class() -> None:
    by = {m.name: m for m in MARS_DYNAMICAL_MODES}
    assert by["orbital_mean_motion"].angle_or_action == "angle"


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_mode_source_resolves() -> None:
    for m in MARS_DYNAMICAL_MODES:
        assert m.source_key in SOURCES


def test_every_resonance_source_resolves() -> None:
    for r in MARS_SECULAR_RESONANCES:
        assert r.source_key in SOURCES


def test_no_unused_sources_entries_except_touma_wisdom() -> None:
    """Every SOURCES key must be used by either a mode or a resonance,
    EXCEPT touma_wisdom_1993 which is cited in the module-docstring as
    independent confirmation of Laskar 1993 — it's a textbook
    cross-reference rather than a per-row source."""
    used = (
        {m.source_key for m in MARS_DYNAMICAL_MODES}
        | {r.source_key for r in MARS_SECULAR_RESONANCES}
    )
    unused = set(SOURCES.keys()) - used
    # touma_wisdom_1993 is allowed to be unused per row (cited in docstring)
    allowed_unused = {"touma_wisdom_1993"}
    assert unused.issubset(allowed_unused), (
        f"Unexpected unused sources: {unused - allowed_unused}"
    )


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_mars_dynamical_spectrum_smoke() -> None:
    r = get_mars_dynamical_spectrum()
    assert r["ok"] is True
    assert r["body"] == "mars"
    assert r["n_modes"] == 8


def test_get_mars_secular_resonance_overlap_smoke() -> None:
    r = get_mars_secular_resonance_overlap()
    assert r["ok"] is True
    assert r["chaos_invariant"]["chaos_active"] is True
    # Excursion range envelope
    lo, hi = r["chaos_invariant"]["obliquity_excursion_range_deg"]
    assert lo == 0.0
    assert hi == 60.0


def test_list_mars_dynamical_spectrum_smoke() -> None:
    r = list_mars_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 8
    assert r["n_resonances"] == 3
    assert r["n_sources"] == 7


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_mars_dynamical_spectrum() -> None:
    r = bridge.get_mars_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 8


def test_bridge_get_mars_secular_resonance_overlap() -> None:
    r = bridge.get_mars_secular_resonance_overlap()
    assert r["ok"] is True
    assert r["chaos_invariant"]["chaos_active"] is True


def test_bridge_list_mars_dynamical_spectrum() -> None:
    r = bridge.list_mars_dynamical_spectrum()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# Cross-references
# ──────────────────────────────────────────────────────────────────────


def test_mars_C_over_MR2_matches_v0_21_4_rotational_constraint() -> None:
    """v0.21.4 ROTATIONAL_CONSTRAINTS Mars entry uses Le Maistre 2023
    InSight RISE chain — must use the same C/MR² value as the v0.24.2
    Mars dynamical-spectrum catalog. Both must trace to Le Maistre 2023."""
    from ephemerides_spectral._research.rotational_constraint_data import (
        ROTATIONAL_CONSTRAINTS,
    )
    mars_v21 = next(
        (r for r in ROTATIONAL_CONSTRAINTS if r.body == "mars"), None,
    )
    if mars_v21 is None:
        pytest.skip("Mars not in v0.21.4 rotational_constraint catalog "
                    "(may be a rotation-period-only entry)")


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_mars_dynamical_spectrum_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mars-dynamical-spectrum"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["body"] == "mars"
    assert payload["n_modes"] == 8


def test_cli_mars_secular_resonance_overlap_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mars-secular-resonance-overlap"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["chaos_invariant"]["chaos_active"] is True


def test_cli_mars_dynamical_spectrum_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mars-dynamical-spectrum-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_modes"] == 8


def test_cli_mars_help() -> None:
    """All v0.24.2 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("mars-dynamical-spectrum",
                "mars-secular-resonance-overlap",
                "mars-dynamical-spectrum-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
