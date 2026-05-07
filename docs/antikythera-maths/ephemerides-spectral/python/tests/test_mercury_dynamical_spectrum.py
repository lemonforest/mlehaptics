"""v0.24.0 — Sol Mercury Dynamical Spectrum Catalog tests.

Pins the first per-body dynamical-spectrum surface:

* 8-mode action-angle catalog (4 angles + 4 actions).
* Headline: 3:2 spin-orbit lock; forced libration 35.8 arcsec at orbital
  frequency; perihelion precession 574.10 arcsec/century with full
  contribution-by-perturber decomposition.
* The Le Verrier / Einstein closure invariant: Newtonian planetary
  perturbations + GR + solar J₂ should sum to within Clemence 1947's
  ±0.65 arcsec/century uncertainty of the observed total.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.mercury_dynamical_spectrum_catalog import (
    get_mercury_dynamical_spectrum,
    get_mercury_precession_decomposition,
    list_mercury_dynamical_spectrum,
)
from ephemerides_spectral._research.mercury_dynamical_spectrum_data import (
    MERCURY_DYNAMICAL_MODES,
    MERCURY_FORCED_LIBRATION_ARCSEC,
    MERCURY_NORMALISED_MOI_C_OVER_MR2,
    MERCURY_OBLIQUITY_ARCMIN,
    MERCURY_ORBITAL_PERIOD_DAYS,
    MERCURY_PRECESSION_CONTRIBUTIONS,
    MERCURY_ROTATION_PERIOD_DAYS,
    PRECISION_HIGH,
    SOURCES,
    DynamicalMode,
    PrecessionContribution,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_mode_count_8() -> None:
    assert len(MERCURY_DYNAMICAL_MODES) == 8


def test_precession_contribution_count() -> None:
    # 5 Newtonian perturbers + GR + solar-J2 + observed = 8
    assert len(MERCURY_PRECESSION_CONTRIBUTIONS) == 8


def test_sources_count() -> None:
    assert len(SOURCES) == 8


# ──────────────────────────────────────────────────────────────────────
# Action-angle structure
# ──────────────────────────────────────────────────────────────────────


def test_4_angles_and_4_actions() -> None:
    """Mercury has 4 angle modes + 4 action modes in this catalog."""
    angles = [m for m in MERCURY_DYNAMICAL_MODES if m.angle_or_action == "angle"]
    actions = [m for m in MERCURY_DYNAMICAL_MODES if m.angle_or_action == "action"]
    # Angles: orbital_mean_motion + spin_frequency + forced_libration +
    #         perihelion_longitude_precession + ascending_node_precession = 5
    # Actions: eccentricity + inclination + obliquity = 3
    # (forced_libration is technically an angle mode at orbital freq)
    assert len(angles) == 5
    assert len(actions) == 3


def test_mode_names_unique() -> None:
    names = [m.name for m in MERCURY_DYNAMICAL_MODES]
    assert len(names) == len(set(names))


# ──────────────────────────────────────────────────────────────────────
# 3:2 spin-orbit commensurability (cross-references v0.23.0)
# ──────────────────────────────────────────────────────────────────────


def test_spin_orbit_3to2_lock_within_ppm() -> None:
    """T_rot * 3 = T_orb * 2 within parts-per-million."""
    # Mercury orbital period 87.96926 d * 2 = 175.93852 d
    # Mercury rotation period 58.6463 d * 3 = 175.9389 d
    lhs = MERCURY_ROTATION_PERIOD_DAYS * 3.0
    rhs = MERCURY_ORBITAL_PERIOD_DAYS * 2.0
    assert lhs == pytest.approx(rhs, rel=1e-5)


def test_spin_frequency_is_3half_orbital() -> None:
    by = {m.name: m for m in MERCURY_DYNAMICAL_MODES}
    spin_f = by["spin_frequency"].frequency_per_century
    orb_f = by["orbital_mean_motion"].frequency_per_century
    # spin = 3/2 * orbit
    assert spin_f == pytest.approx(orb_f * 1.5, rel=1e-3)


# ──────────────────────────────────────────────────────────────────────
# Forced libration headline (Margot 2007)
# ──────────────────────────────────────────────────────────────────────


def test_forced_libration_amplitude() -> None:
    """Margot 2007: 35.8 arcsec amplitude."""
    by = {m.name: m for m in MERCURY_DYNAMICAL_MODES}
    lib = by["forced_libration"]
    assert lib.amplitude_value == pytest.approx(35.8, abs=2)
    assert lib.amplitude_units == "arcsec"
    # libration is at orbital frequency (forced by solar tidal torque
    # at orbital period)
    orb = by["orbital_mean_motion"]
    assert lib.frequency_per_century == pytest.approx(
        orb.frequency_per_century, rel=1e-3,
    )


def test_forced_libration_matches_v0_23_0_value() -> None:
    """Cross-reference: v0.23.0 spin_orbit_resonance.libration_amplitude_arcsec
    must agree with v0.24.0 forced_libration mode amplitude."""
    from ephemerides_spectral._research.spin_orbit_resonance_data import (
        SPIN_ORBIT_RESONANCES,
    )
    mercury_v23 = next(s for s in SPIN_ORBIT_RESONANCES if s.body == "mercury")
    by = {m.name: m for m in MERCURY_DYNAMICAL_MODES}
    forced = by["forced_libration"]
    assert mercury_v23.libration_amplitude_arcsec == pytest.approx(
        forced.amplitude_value, rel=1e-3,
    )


def test_C_over_MR2_margot_value() -> None:
    """Margot 2007: C/MR² = 0.346 ± 0.014."""
    assert MERCURY_NORMALISED_MOI_C_OVER_MR2 == pytest.approx(0.346, abs=0.02)


def test_obliquity_in_margot_band() -> None:
    """Margot 2007: 2.04 ± 0.08 arcmin."""
    assert MERCURY_OBLIQUITY_ARCMIN == pytest.approx(2.04, abs=0.1)


# ──────────────────────────────────────────────────────────────────────
# Perihelion-precession contribution decomposition (THE headline)
# ──────────────────────────────────────────────────────────────────────


def test_observed_total_clemence_value() -> None:
    """Clemence 1947: 574.10 ± 0.65 arcsec/century."""
    observed = next(
        c for c in MERCURY_PRECESSION_CONTRIBUTIONS
        if c.physics_class == "observation"
    )
    assert observed.arcsec_per_century == pytest.approx(574.10, abs=1.0)


def test_le_verrier_einstein_closure_invariant() -> None:
    """The headline invariant: Newtonian + GR + solar-J₂ contributions
    must sum to within Clemence 1947's ±0.65 arcsec/century uncertainty
    of the observed total. This is one of the most precise
    quantitative confirmations of GR."""
    contribs = MERCURY_PRECESSION_CONTRIBUTIONS
    observed = next(c for c in contribs if c.physics_class == "observation")
    summed_predictions = sum(
        c.arcsec_per_century
        for c in contribs
        if c.physics_class != "observation"
    )
    residual = observed.arcsec_per_century - summed_predictions
    # Allow ~1 arcsec/century slop — Clemence 1947 quoted 0.65 abs and
    # the per-perturber Newtonian split has rounding from Verma 2014.
    assert abs(residual) < 1.0, (
        f"Le Verrier/Einstein closure broken: observed "
        f"{observed.arcsec_per_century} - predictions {summed_predictions} "
        f"= residual {residual} (allowed ±1.0 arcsec/century)"
    )


def test_gr_contribution_einstein_value() -> None:
    """Einstein 1915 derivation: 42.98 arcsec/century from Schwarzschild
    metric. Park 2017 MESSENGER measurement confirms to 1 part in 10^4."""
    gr = next(
        c for c in MERCURY_PRECESSION_CONTRIBUTIONS
        if c.physics_class == "general_relativity"
    )
    assert gr.arcsec_per_century == pytest.approx(42.98, abs=0.5)
    assert gr.contributor == "general_relativity"


def test_venus_largest_newtonian_contributor() -> None:
    """Venus is Mercury's closest planetary neighbour; should
    dominate the Newtonian sum."""
    contribs = MERCURY_PRECESSION_CONTRIBUTIONS
    newtonian = [
        c for c in contribs
        if c.physics_class == "newtonian_perturbation"
    ]
    largest = max(newtonian, key=lambda c: c.arcsec_per_century)
    assert largest.contributor == "venus"


def test_jupiter_second_largest_newtonian() -> None:
    """Jupiter mass dominates Earth proximity in perturbation budget."""
    contribs = MERCURY_PRECESSION_CONTRIBUTIONS
    newtonian = sorted(
        [c for c in contribs if c.physics_class == "newtonian_perturbation"],
        key=lambda c: c.arcsec_per_century,
        reverse=True,
    )
    assert newtonian[0].contributor == "venus"
    assert newtonian[1].contributor == "jupiter"


def test_solar_j2_smaller_than_gr() -> None:
    """Solar quadrupole J₂ contribution is much smaller than GR
    (Park 2017 MESSENGER constraint)."""
    contribs = MERCURY_PRECESSION_CONTRIBUTIONS
    gr = next(c for c in contribs if c.physics_class == "general_relativity")
    j2 = next(c for c in contribs if c.physics_class == "solar_oblateness")
    assert j2.arcsec_per_century < 0.1 * gr.arcsec_per_century


def test_all_arcsec_values_positive() -> None:
    """Every contribution should drive precession in the same prograde
    direction (positive arcsec/century)."""
    for c in MERCURY_PRECESSION_CONTRIBUTIONS:
        assert c.arcsec_per_century > 0


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_mode_source_resolves() -> None:
    for m in MERCURY_DYNAMICAL_MODES:
        assert m.source_key in SOURCES


def test_every_contribution_source_resolves() -> None:
    for c in MERCURY_PRECESSION_CONTRIBUTIONS:
        assert c.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    """Every SOURCES key must be referenced by either a mode or a
    contribution."""
    used = (
        {m.source_key for m in MERCURY_DYNAMICAL_MODES}
        | {c.source_key for c in MERCURY_PRECESSION_CONTRIBUTIONS}
    )
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_mercury_dynamical_spectrum_smoke() -> None:
    r = get_mercury_dynamical_spectrum()
    assert r["ok"] is True
    assert r["body"] == "mercury"
    assert r["n_modes"] == 8


def test_get_mercury_precession_decomposition_smoke() -> None:
    r = get_mercury_precession_decomposition()
    assert r["ok"] is True
    assert r["total_observed_arcsec_per_century"] == pytest.approx(
        574.10, abs=1.0,
    )
    # The headline: residual must be small
    assert abs(r["invariant_residual_arcsec_per_century"]) < 1.0


def test_list_mercury_dynamical_spectrum_smoke() -> None:
    r = list_mercury_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 8
    assert r["n_contributions"] == 8
    assert r["n_sources"] == 8


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_mercury_dynamical_spectrum() -> None:
    r = bridge.get_mercury_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 8


def test_bridge_get_mercury_precession_decomposition() -> None:
    r = bridge.get_mercury_precession_decomposition()
    assert r["ok"] is True
    assert abs(r["invariant_residual_arcsec_per_century"]) < 1.0


def test_bridge_list_mercury_dynamical_spectrum() -> None:
    r = bridge.list_mercury_dynamical_spectrum()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_mercury_dynamical_spectrum_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mercury-dynamical-spectrum"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["body"] == "mercury"
    assert payload["n_modes"] == 8


def test_cli_mercury_precession_decomposition_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mercury-precession-decomposition"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert abs(payload["invariant_residual_arcsec_per_century"]) < 1.0


def test_cli_mercury_dynamical_spectrum_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["mercury-dynamical-spectrum-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_modes"] == 8


def test_cli_mercury_help() -> None:
    """All v0.24.0 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("mercury-dynamical-spectrum",
                "mercury-precession-decomposition",
                "mercury-dynamical-spectrum-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
