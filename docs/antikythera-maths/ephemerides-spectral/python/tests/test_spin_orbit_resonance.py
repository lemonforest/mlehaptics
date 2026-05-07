"""v0.23.0 — Sol Spin-Orbit Resonance Catalog tests.

Pins the eleventh cross-channel coupling surface (resumed after v0.22.0
trajectory + sensing discipline pivot):

* 8-body roster (mercury, luna, io, europa, ganymede, titan, triton,
  charon).
* Headlines: Mercury 3:2 (the only non-1:1 spin-orbit resonance in the
  Solar System); Luna 1:1 + 7.9 arcsec libration (the canonical case);
  Pluto-Charon dual-synchronous (the unique solar-system case);
  Titan anomalously large libration (subsurface ocean diagnostic).
* p/q ratio invariants + period consistency invariants.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.spin_orbit_resonance_catalog import (
    compute_spin_orbit_resonance,
    get_spin_orbit_resonance,
    list_spin_orbit_resonances,
)
from ephemerides_spectral._research.spin_orbit_resonance_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    SPIN_ORBIT_RESONANCES,
    SpinOrbitResonance,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_roster_size_is_8() -> None:
    assert len(SPIN_ORBIT_RESONANCES) == 8


def test_canonical_roster_members() -> None:
    by = {s.body for s in SPIN_ORBIT_RESONANCES}
    assert by == {
        "mercury", "luna", "io", "europa", "ganymede",
        "titan", "triton", "charon",
    }


def test_sources_count() -> None:
    assert len(SOURCES) == 8


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────


def test_mercury_3to2_resonance() -> None:
    """Mercury is THE 3:2 case — the only non-1:1 spin-orbit
    resonance in the Solar System."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    mercury = by["mercury"]
    assert mercury.p_numerator == 3
    assert mercury.q_denominator == 2
    # Period ratio T_rot / T_orb ≈ 2/3
    ratio = mercury.rotation_period_days / mercury.orbital_period_days
    assert ratio == pytest.approx(2.0 / 3.0, abs=0.01)


def test_mercury_only_non_one_to_one() -> None:
    """Only Mercury has p ≠ q in the catalog."""
    non_one_to_one = [
        s for s in SPIN_ORBIT_RESONANCES
        if s.p_numerator != s.q_denominator
    ]
    assert len(non_one_to_one) == 1
    assert non_one_to_one[0].body == "mercury"


def test_mercury_libration_high_precision() -> None:
    """Margot 2007: Mercury libration amplitude ~36 arcsec."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    mercury = by["mercury"]
    assert mercury.libration_amplitude_arcsec == pytest.approx(35.8, abs=2)
    assert mercury.precision_flag == PRECISION_HIGH


def test_luna_canonical_one_to_one() -> None:
    """Williams 2014 LLR: Luna 1:1 with ~7.9 arcsec libration."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    luna = by["luna"]
    assert luna.p_numerator == 1
    assert luna.q_denominator == 1
    assert luna.libration_amplitude_arcsec == pytest.approx(7.9, abs=0.5)
    assert luna.parent == "terra"


def test_charon_pluto_dual_synchronous() -> None:
    """Pluto-Charon is the unique dual-synchronous case in the
    Solar System."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    charon = by["charon"]
    assert charon.is_dual_synchronous is True
    # Only Charon should have this flag set
    duals = [s for s in SPIN_ORBIT_RESONANCES if s.is_dual_synchronous]
    assert len(duals) == 1
    assert duals[0].body == "charon"


def test_titan_anomalous_libration() -> None:
    """Iess 2012: Titan libration ~52 arcsec (anomalously large for
    a moon its size — subsurface ocean diagnostic)."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    titan = by["titan"]
    assert titan.p_numerator == 1
    assert titan.q_denominator == 1
    # Titan libration must be substantially larger than Galileans
    # (which are sub-arcsec) — it's the subsurface-ocean signature.
    io_lib = by["io"].libration_amplitude_arcsec
    europa_lib = by["europa"].libration_amplitude_arcsec
    assert titan.libration_amplitude_arcsec > 10 * io_lib
    assert titan.libration_amplitude_arcsec > 10 * europa_lib


def test_galileans_all_one_to_one() -> None:
    """Io, Europa, Ganymede are all 1:1 tidal locks (Lainey 2009/2020)."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    for moon in ("io", "europa", "ganymede"):
        assert by[moon].p_numerator == 1
        assert by[moon].q_denominator == 1
        assert by[moon].parent == "jupiter"


def test_triton_retrograde_one_to_one() -> None:
    """Triton 1:1 retrograde tidal lock (Jacobson 2009)."""
    by = {s.body: s for s in SPIN_ORBIT_RESONANCES}
    triton = by["triton"]
    assert triton.p_numerator == 1
    assert triton.q_denominator == 1
    assert triton.parent == "neptune"


# ──────────────────────────────────────────────────────────────────────
# Period consistency invariants
# ──────────────────────────────────────────────────────────────────────


def test_one_to_one_periods_equal() -> None:
    """For 1:1 resonances, T_rot = T_orb exactly (definitionally)."""
    for s in SPIN_ORBIT_RESONANCES:
        if s.p_numerator == 1 and s.q_denominator == 1:
            assert s.rotation_period_days == pytest.approx(
                s.orbital_period_days, rel=1e-6
            )


def test_period_ratio_matches_p_over_q() -> None:
    """For every entry, T_rot / T_orb ≈ q / p (rotations per orbit
    means T_rot is q times shorter than the orbit divided by p)."""
    for s in SPIN_ORBIT_RESONANCES:
        ratio = s.rotation_period_days / s.orbital_period_days
        expected = s.q_denominator / s.p_numerator
        # ±1% tolerance for the 3:2 case (rotation period is the
        # 1965 Pettengill measurement)
        assert ratio == pytest.approx(expected, rel=0.01), (
            f"{s.body}: T_rot/T_orb = {ratio}, "
            f"expected q/p = {expected}"
        )


def test_all_ratios_low_integer() -> None:
    """All ratios should be small integers (not 17:23 etc)."""
    for s in SPIN_ORBIT_RESONANCES:
        assert 1 <= s.p_numerator <= 10
        assert 1 <= s.q_denominator <= 10


def test_all_periods_positive() -> None:
    for s in SPIN_ORBIT_RESONANCES:
        assert s.rotation_period_days > 0
        assert s.orbital_period_days > 0


def test_all_libration_non_negative() -> None:
    for s in SPIN_ORBIT_RESONANCES:
        assert s.libration_amplitude_arcsec >= 0


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_source_key_resolves() -> None:
    for s in SPIN_ORBIT_RESONANCES:
        assert s.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {s.source_key for s in SPIN_ORBIT_RESONANCES}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_compute_unknown_body() -> None:
    r = compute_spin_orbit_resonance(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_spin_orbit_resonance()
    assert r["ok"] is True
    assert r["n_bodies"] == 8


def test_compute_per_body_mercury() -> None:
    r = compute_spin_orbit_resonance(body="mercury")
    assert r["ok"] is True
    assert r["resonance"]["p_numerator"] == 3
    assert r["resonance"]["q_denominator"] == 2
    assert r["resonance"]["ratio_label"] == "3:2"


def test_get_alias_works() -> None:
    """get_spin_orbit_resonance is alias for compute_spin_orbit_resonance."""
    r1 = compute_spin_orbit_resonance(body="luna")
    r2 = get_spin_orbit_resonance(body="luna")
    assert r1 == r2


def test_list_spin_orbit_resonances_smoke() -> None:
    r = list_spin_orbit_resonances()
    assert r["ok"] is True
    assert r["n_bodies"] == 8
    assert r["n_sources"] == 8


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_spin_orbit_resonance_smoke() -> None:
    r = bridge.get_spin_orbit_resonance(body="mercury")
    assert r["ok"] is True
    assert r["resonance"]["ratio_label"] == "3:2"


def test_bridge_get_spin_orbit_resonance_full_roster() -> None:
    r = bridge.get_spin_orbit_resonance()
    assert r["ok"] is True
    assert r["n_bodies"] == 8


def test_bridge_list_spin_orbit_resonances_smoke() -> None:
    r = bridge.list_spin_orbit_resonances()
    assert r["ok"] is True


def test_bridge_get_spin_orbit_resonance_rejects_unknown() -> None:
    r = bridge.get_spin_orbit_resonance(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_spin_orbit_resonance_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["spin-orbit-resonance", "--body", "mercury"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["resonance"]["ratio_label"] == "3:2"


def test_cli_spin_orbit_resonances_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["spin-orbit-resonances"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 8


def test_cli_spin_orbit_help() -> None:
    """Both v0.23.0 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("spin-orbit-resonance", "spin-orbit-resonances"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
