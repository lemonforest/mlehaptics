"""v0.24.3 — Sol Sun Dynamical Spectrum Catalog tests.

Pins the fourth per-body dynamical-spectrum surface — the **first
stellar entry** + **methodology extension** from rigid-body
action-angle (Mercury / Luna / Mars) to stellar-oscillation continuum
normal-mode spectrum (helioseismology).

* 20-mode sample p-mode catalog (n=18-25 at l=0-2).
* Headlines: Δν = 135.1 μHz, δν = 9.0 μHz, ν_max = 3090 μHz.
* THE closure invariant: Tassoul 1980 asymptotic relation predicts
  the entire mode comb from three constants. Catalog is asymptotic-
  consistent (residual < 0.01 μHz from float roundoff); real data
  has ~0.1-1 μHz residuals from interior-structure glitches.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.sun_dynamical_spectrum_catalog import (
    get_helioseismic_asymptotic_relation,
    get_sun_dynamical_spectrum,
    list_sun_dynamical_spectrum,
)
from ephemerides_spectral._research.sun_dynamical_spectrum_data import (
    HELIOSEISMIC_MODES,
    PRECISION_HIGH,
    SOURCES,
    SUN_ASYMPTOTIC_PHASE_OFFSET,
    SUN_EFFECTIVE_TEMPERATURE_K,
    SUN_LARGE_FREQUENCY_SEPARATION_UHZ,
    SUN_LUMINOSITY_W,
    SUN_MASS_KG,
    SUN_NU_MAX_UHZ,
    SUN_PMODE_FREQUENCY_CYCLE_SHIFT_UHZ,
    SUN_RADIUS_M,
    SUN_SMALL_FREQUENCY_SEPARATION_UHZ,
    SUN_SURFACE_GRAVITY_M_S2,
    HelioseismicMode,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_mode_count_20() -> None:
    """20 modes total: 8 (l=0, n=18-25) + 6 (l=1, n=18-23) + 6 (l=2, n=18-23)."""
    assert len(HELIOSEISMIC_MODES) == 20


def test_l_values_0_1_2() -> None:
    """Catalog spans l=0,1,2 only (the canonical low-degree comb)."""
    by_l = {m.l for m in HELIOSEISMIC_MODES}
    assert by_l == {0, 1, 2}


def test_n_range_18_to_25() -> None:
    """Catalog spans n=18 to n=25 (high-SNR p-mode comb near ν_max)."""
    by_n = {m.n for m in HELIOSEISMIC_MODES}
    assert min(by_n) == 18
    assert max(by_n) == 25


def test_sources_count() -> None:
    assert len(SOURCES) == 8


def test_all_modes_are_p_class() -> None:
    """Catalog ships only p-modes (g-modes deferred to future ship)."""
    for m in HELIOSEISMIC_MODES:
        assert m.mode_class == "p"


# ──────────────────────────────────────────────────────────────────────
# Solar standard-model constants
# ──────────────────────────────────────────────────────────────────────


def test_sun_mass_value() -> None:
    """IAU 2015 nominal: 1.98892e30 kg."""
    assert SUN_MASS_KG == pytest.approx(1.98892e30, rel=1e-4)


def test_sun_radius_iau_2015() -> None:
    """IAU 2015 nominal R_sun: 695700 km."""
    assert SUN_RADIUS_M == pytest.approx(695700e3, rel=1e-9)


def test_sun_T_eff_iau_2015() -> None:
    """IAU 2015 nominal effective temperature: 5772 K."""
    assert SUN_EFFECTIVE_TEMPERATURE_K == pytest.approx(5772.0, abs=1.0)


def test_sun_luminosity_iau_2015() -> None:
    assert SUN_LUMINOSITY_W == pytest.approx(3.828e26, rel=1e-3)


# ──────────────────────────────────────────────────────────────────────
# Asymptotic-relation constants
# ──────────────────────────────────────────────────────────────────────


def test_large_separation_135_1_uHz() -> None:
    """BiSON / Davies 2014: Δν = 135.1 ± 0.1 μHz."""
    assert SUN_LARGE_FREQUENCY_SEPARATION_UHZ == pytest.approx(
        135.1, abs=0.5,
    )


def test_small_separation_9_uHz() -> None:
    """δν₀₂ ≈ 9 μHz — sensitive to helium-core gradient."""
    assert SUN_SMALL_FREQUENCY_SEPARATION_UHZ == pytest.approx(9.0, abs=1.0)


def test_nu_max_3090_uHz() -> None:
    """ν_max ≈ 3090 μHz — peak amplitude (Brown 1991 g/√T_eff scaling)."""
    assert SUN_NU_MAX_UHZ == pytest.approx(3090.0, abs=50)


# ──────────────────────────────────────────────────────────────────────
# THE closure invariant: asymptotic relation
# ──────────────────────────────────────────────────────────────────────


def test_asymptotic_relation_closure_invariant() -> None:
    """THE headline: max residual between catalog frequencies and
    Tassoul 1980 asymptotic-relation predictions must be small.

    Catalog ships asymptotic-consistent reference values, so this
    closure test verifies internal consistency of the relation +
    constants. Real BiSON data has ~0.1-1 μHz residuals from
    interior-structure glitches; the catalog's near-zero residual
    is by-design demonstration."""
    r = get_helioseismic_asymptotic_relation()
    assert r["max_residual_uhz"] < 0.5


def test_asymptotic_relation_rms_invariant() -> None:
    """RMS residual across the catalog also small (asymptotic-
    consistent reference values)."""
    r = get_helioseismic_asymptotic_relation()
    assert r["rms_residual_uhz"] < 0.5


def test_radial_modes_separated_by_delta_nu() -> None:
    """Radial l=0 modes consecutive in n must be separated by ~Δν.

    ν(n+1, 0) - ν(n, 0) ≈ Δν = 135.1 μHz."""
    by = {(m.n, m.l): m for m in HELIOSEISMIC_MODES}
    for n in range(18, 25):
        if (n, 0) in by and (n + 1, 0) in by:
            sep = by[(n + 1, 0)].frequency_uhz - by[(n, 0)].frequency_uhz
            assert sep == pytest.approx(
                SUN_LARGE_FREQUENCY_SEPARATION_UHZ, abs=0.1,
            ), f"Δν between n={n} and n={n+1} = {sep}"


def test_dipole_modes_offset_by_half_delta_nu() -> None:
    """Dipole l=1 modes at fixed n offset from radial l=0 modes by
    ~Δν/2."""
    by = {(m.n, m.l): m for m in HELIOSEISMIC_MODES}
    half_dnu = SUN_LARGE_FREQUENCY_SEPARATION_UHZ / 2.0
    for n in range(18, 24):
        if (n, 0) in by and (n, 1) in by:
            offset = by[(n, 1)].frequency_uhz - by[(n, 0)].frequency_uhz
            # Should be ≈ Δν/2 (= 67.55 μHz) — the dipole offset
            assert offset == pytest.approx(half_dnu, abs=2.0)


# ──────────────────────────────────────────────────────────────────────
# Frequency invariants
# ──────────────────────────────────────────────────────────────────────


def test_all_frequencies_positive() -> None:
    for m in HELIOSEISMIC_MODES:
        assert m.frequency_uhz > 0


def test_all_frequencies_in_p_mode_band() -> None:
    """All catalog modes within the high-SNR p-mode band 2 < ν < 5 mHz."""
    for m in HELIOSEISMIC_MODES:
        assert 2000.0 < m.frequency_uhz < 5000.0


def test_frequencies_monotone_in_n_at_fixed_l() -> None:
    """At fixed l, ν increases monotonically with n."""
    for l in (0, 1, 2):
        modes_at_l = sorted(
            (m for m in HELIOSEISMIC_MODES if m.l == l),
            key=lambda m: m.n,
        )
        for prev, curr in zip(modes_at_l[:-1], modes_at_l[1:]):
            assert curr.frequency_uhz > prev.frequency_uhz


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_mode_source_resolves() -> None:
    for m in HELIOSEISMIC_MODES:
        assert m.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_sun_dynamical_spectrum_smoke() -> None:
    r = get_sun_dynamical_spectrum()
    assert r["ok"] is True
    assert r["body"] == "sol"
    assert r["n_modes"] == 20


def test_get_helioseismic_asymptotic_relation_smoke() -> None:
    r = get_helioseismic_asymptotic_relation()
    assert r["ok"] is True
    assert r["max_residual_uhz"] < 0.5


def test_list_sun_dynamical_spectrum_smoke() -> None:
    r = list_sun_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 20
    assert r["n_sources"] == 8


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_sun_dynamical_spectrum() -> None:
    r = bridge.get_sun_dynamical_spectrum()
    assert r["ok"] is True
    assert r["n_modes"] == 20


def test_bridge_get_helioseismic_asymptotic_relation() -> None:
    r = bridge.get_helioseismic_asymptotic_relation()
    assert r["ok"] is True
    assert r["max_residual_uhz"] < 0.5


def test_bridge_list_sun_dynamical_spectrum() -> None:
    r = bridge.list_sun_dynamical_spectrum()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_sun_dynamical_spectrum_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["sun-dynamical-spectrum"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["body"] == "sol"
    assert payload["n_modes"] == 20


def test_cli_helioseismic_asymptotic_relation_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["helioseismic-asymptotic-relation"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["max_residual_uhz"] < 0.5


def test_cli_sun_dynamical_spectrum_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["sun-dynamical-spectrum-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_modes"] == 20


def test_cli_sun_help() -> None:
    """All v0.24.3 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("sun-dynamical-spectrum",
                "helioseismic-asymptotic-relation",
                "sun-dynamical-spectrum-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
