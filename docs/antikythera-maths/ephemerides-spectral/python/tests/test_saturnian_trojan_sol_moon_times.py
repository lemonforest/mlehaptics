"""v0.16.0 — Sol Moon Times: Saturnian Lagrange trojans (Telesto, Calypso,
Helene, Polydeuces).

First L4/L5 entries in BODIES. Each pair shares its host moon's
sidereal period EXACTLY (1:1 mean-motion lock at the L4/L5 fixed
points of the Saturn-host CR3BP). The body-graph Laplacian acquires
a multiplicity-2 degeneracy at the host's frequency — the natural
intersection point with the v0.16.x resonance-graph multi-leg
find_itn_chains work (notebook §12).

Same invariants as the v0.14.x / v0.15.0 family tests (J2000-zero,
after-one-period, inverse round-trip, NaN/Inf rejection, CLI
parsing) plus explicit cross-checks that:

  - The trojan period EXACTLY matches its host moon's period
    (this is the L4/L5 1:1 spin-orbit lock identity).
  - The first invocation of the v0.14.1 suffix-disambiguation
    policy (Telesto's SSaTeT2 vs Tethys's existing SSaTeT) works
    end-to-end.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.time_scales import (
    SOL_MOON_TIME_J2000_JD_TDB,
)
from ephemerides_spectral.cli import main as cli_main


# (body_key, abbrev, sol_time_name, host_key, jd_to_fn, to_jd_fn)
TROJANS = [
    ("telesto", "SSaTeT2", "Sol Saturn-Telesto Time", "tethys",
     bridge.jd_to_sol_saturn_telesto_time, bridge.sol_saturn_telesto_time_to_jd),
    ("calypso", "SSaCaT", "Sol Saturn-Calypso Time", "tethys",
     bridge.jd_to_sol_saturn_calypso_time, bridge.sol_saturn_calypso_time_to_jd),
    ("helene", "SSaHeT", "Sol Saturn-Helene Time", "dione",
     bridge.jd_to_sol_saturn_helene_time, bridge.sol_saturn_helene_time_to_jd),
    ("polydeuces", "SSaPoT", "Sol Saturn-Polydeuces Time", "dione",
     bridge.jd_to_sol_saturn_polydeuces_time, bridge.sol_saturn_polydeuces_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, _host, jd_to_fn, _to_jd_fn", TROJANS)
def test_trojan_bridge_at_j2000_returns_zero_count(
        body_key, abbrev, sol_time_name, _host, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "saturn"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize("body_key, _abbrev, _name, _host, jd_to_fn, _to_jd_fn", TROJANS)
def test_trojan_bridge_after_one_sidereal_period(
        body_key, _abbrev, _name, _host, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    assert abs(out["sidereal_count"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, _host, jd_to_fn, to_jd_fn", TROJANS)
def test_trojan_bridge_inverse_round_trip(
        body_key, abbrev, _name, _host, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


@pytest.mark.parametrize("body_key, _abbrev, _name, host_key, _jd_fn, _inv_fn", TROJANS)
def test_trojan_period_exactly_matches_host_period(
        body_key, _abbrev, _name, host_key, _jd_fn, _inv_fn):
    """L4/L5 trojans share their host moon's period EXACTLY (1:1 mean-
    motion lock at the L4/L5 fixed points of the Saturn-host CR3BP).
    This is the spectral content the trojan slot earns: the body-
    graph Laplacian acquires a multiplicity-2 eigenvalue at the
    host frequency.
    """
    trojan_period = float(BODIES[body_key].period_days)
    host_period   = float(BODIES[host_key].period_days)
    assert trojan_period == host_period, (
        f"trojan {body_key} period {trojan_period} != host {host_key} "
        f"period {host_period}; the L4/L5 1:1 lock should make these "
        f"byte-identical at the BODIES level."
    )


def test_telesto_suffix_disambiguates_from_tethys() -> None:
    """First invocation of the v0.14.1 suffix-disambiguation policy.
    Both Tethys and Telesto have moon-prefix `Te`. Tethys (shipped
    v0.14.1) has the canonical `SSaTeT`; Telesto (shipped v0.16.0)
    takes the suffixed `SSaTeT2`. Without the suffix policy both
    moons would collapse to `SSaTeT` — exactly the kind of intra-
    parent collision the policy was reserved for.
    """
    telesto = bridge.jd_to_sol_saturn_telesto_time(SOL_MOON_TIME_J2000_JD_TDB)
    tethys  = bridge.jd_to_sol_saturn_tethys_time(SOL_MOON_TIME_J2000_JD_TDB)
    a_telesto = telesto["epoch"]["abbreviation"]
    a_tethys  = tethys["epoch"]["abbreviation"]
    assert a_telesto == "SSaTeT2"
    assert a_tethys  == "SSaTeT"
    assert a_telesto != a_tethys
    # Both share the Te moon-prefix.
    assert a_telesto[3:5] == "Te" and a_tethys[3:5] == "Te"
    # The suffix '2' is the disambiguator.
    assert a_telesto.endswith("T2")
    assert not a_tethys.endswith("T2")


def test_trojan_abbreviations_dont_collide_with_other_families() -> None:
    """All four trojan abbreviations must be globally distinct from
    every other Sol Moon Time abbreviation across all parents."""
    galilean = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    jovian_inner = {"SJuMeT", "SJuAdT", "SJuAmT", "SJuThT"}
    jovian_irregular = {"SJuHiT", "SJuPaT", "SJuSiT"}  # v0.16.0
    saturnian = {"SSaMiT", "SSaEnT", "SSaTeT", "SSaDiT", "SSaRhT", "SSaTiT",
                 "SSaHyT", "SSaIaT", "SSaPhT", "SSaJaT", "SSaEpT"}
    martian = {"SMaPhT", "SMaDeT"}
    uranian = {"SUrMiT", "SUrArT", "SUrUmT", "SUrTiT", "SUrObT"}
    neptunian = {"SNeTrT", "SNePrT", "SNeNeT"}  # v0.16.0 adds SNePrT, SNeNeT
    plutonian = {"SPlChT"}
    trojan = {abbrev for _, abbrev, *_ in TROJANS}
    all_other = (galilean | jovian_inner | jovian_irregular | saturnian
                 | martian | uranian | neptunian | plutonian)
    assert all_other.isdisjoint(trojan), (
        f"abbreviation collision between Saturnian trojans and prior "
        f"families: {all_other & trojan}"
    )


@pytest.mark.parametrize("body_key, _abbrev, _name, _host, jd_to_fn, _to_jd_fn", TROJANS)
def test_trojan_bridge_rejects_non_finite_jd(
        body_key, _abbrev, _name, _host, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False
    out = jd_to_fn(float("-inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-saturn-{trojan}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _host, _jd_fn, _inv_fn", TROJANS)
def test_trojan_cli_jd_path(body_key, abbrev, _name, _host, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-saturn-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "saturn"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _host, _jd_fn, _inv_fn", TROJANS)
def test_trojan_cli_inverse_path(body_key, abbrev, _name, _host, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-saturn-{body_key}", "--sidereal-count", "100"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["sidereal_count"] == 100.0
    assert payload["abbreviation"] == abbrev
    expected_jd = (
        SOL_MOON_TIME_J2000_JD_TDB
        + 100.0 * float(BODIES[body_key].period_days)
    )
    assert abs(payload["jd_tdb"] - expected_jd) < 1e-6


@pytest.mark.parametrize("body_key, _abbrev, _name, _host, _jd_fn, _inv_fn", TROJANS)
def test_trojan_cli_requires_jd_or_sidereal_count(
        body_key, _abbrev, _name, _host, _jd_fn, _inv_fn):
    with pytest.raises(SystemExit):
        cli_main([f"time-saturn-{body_key}"])
