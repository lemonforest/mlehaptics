"""v0.16.0 — Sol Moon Times: Jovian irregular moons (Himalia, Pasiphae, Sinope).

Three Jovian "captured asteroid"-class moons added in v0.16.0:

  - Himalia (1904, prograde, P=250.6 d) -- largest Jovian irregular
    (radius ~85 km), eponym of the Himalia group.
  - Pasiphae (1908, retrograde, P=743.6 d, inclination ~141°) --
    eponym of the Pasiphae group.
  - Sinope (1914, retrograde, P=758.9 d, inclination ~153°) --
    Pasiphae-group member, near-resonant with Pasiphae.

Pasiphae and Sinope are the second retrograde marker beyond Triton
(v0.14.2). Encoder convention from v0.5.4 / v0.14.2 / v0.15.0:
period_days is positive for ALL bodies; retrograde-ness is metadata,
not a sign flip.
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


# (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
JOVIAN_IRREGULARS = [
    ("himalia", "SJuHiT", "Sol Jupiter-Himalia Time",
     bridge.jd_to_sol_jupiter_himalia_time, bridge.sol_jupiter_himalia_time_to_jd),
    ("pasiphae", "SJuPaT", "Sol Jupiter-Pasiphae Time",
     bridge.jd_to_sol_jupiter_pasiphae_time, bridge.sol_jupiter_pasiphae_time_to_jd),
    ("sinope", "SJuSiT", "Sol Jupiter-Sinope Time",
     bridge.jd_to_sol_jupiter_sinope_time, bridge.sol_jupiter_sinope_time_to_jd),
]


@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", JOVIAN_IRREGULARS)
def test_jovian_irregular_at_j2000(body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "jupiter"
    assert out["sidereal_count"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", JOVIAN_IRREGULARS)
def test_jovian_irregular_after_one_period(body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB + period)
    assert out["ok"] is True
    assert abs(out["sidereal_count"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", JOVIAN_IRREGULARS)
def test_jovian_irregular_round_trip(body_key, abbrev, _name, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 50.0  # +50 yr (long-period bodies)
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev


def test_pasiphae_sinope_period_resonance() -> None:
    """Pasiphae and Sinope are near-resonant: their sidereal periods
    differ by ~2%. Pin both periods + the ratio so a future BODIES
    tweak can't silently drift the captured-pair signature.
    """
    p_pasiphae = float(BODIES["pasiphae"].period_days)
    p_sinope   = float(BODIES["sinope"].period_days)
    assert p_pasiphae == 743.6300000
    assert p_sinope   == 758.9000000
    ratio = p_sinope / p_pasiphae
    # ~1.0205 — the near-resonance signature
    assert 1.015 < ratio < 1.025


def test_retrograde_periods_encoded_positive() -> None:
    """Both Pasiphae (i~141°) and Sinope (i~153°) orbit retrograde,
    but BODIES stores positive period_days per the encoder convention
    established in v0.5.4 / v0.14.2 / v0.15.0. Same as Triton.
    Retrograde-ness is metadata, not a sign flip in the time-scale
    primitive.
    """
    assert float(BODIES["pasiphae"].period_days) > 0
    assert float(BODIES["sinope"].period_days) > 0
    assert float(BODIES["triton"].period_days) > 0  # the v0.14.2 precedent


def test_jovian_irregular_abbreviations_dont_collide() -> None:
    """The three Jovian-irregular abbreviations must not collide with
    any Galilean (SJu*) or Jovian-inner-regular (SJu*) abbreviation.
    """
    galilean = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    jovian_inner = {"SJuMeT", "SJuAdT", "SJuAmT", "SJuThT"}
    jovian_irreg = {abbrev for _, abbrev, *_ in JOVIAN_IRREGULARS}
    assert galilean.isdisjoint(jovian_irreg)
    assert jovian_inner.isdisjoint(jovian_irreg)


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", JOVIAN_IRREGULARS)
def test_jovian_irregular_rejects_non_finite_jd(body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    assert jd_to_fn(float("nan"))["ok"] is False
    assert jd_to_fn(float("inf"))["ok"] is False
    assert jd_to_fn(float("-inf"))["ok"] is False


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", JOVIAN_IRREGULARS)
def test_jovian_irregular_cli_jd_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-jupiter-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", JOVIAN_IRREGULARS)
def test_jovian_irregular_cli_inverse_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-jupiter-{body_key}", "--sidereal-count", "10"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["abbreviation"] == abbrev
