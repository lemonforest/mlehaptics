"""v0.11.0 — Sol Proper Time (SPrT) — focused tests.

Same six validation cases that Phase A's `research/proper_time_rates.py`
verifies, pinned against the canonical `_research.proper_time` primitive
that ships in v0.11.0. Two independent implementations agreeing on the
same published numbers — if either one drifts, the discipline catches it.

Plus end-to-end CLI exercises for `time-proper` and the `--proper` flag.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.proper_time import (
    C, DAY_S, GM_EARTH, GM_SUN,
    DEFAULT_REFERENCE,
    SUPPORTED_REFERENCES,
    compare_proper_times,
    get_proper_time_rate,
)


# ──────────────────────────────────────────────────────────────────────
# Validation pins (identical to Phase A research script)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body,expected,rel_tol,label", [
    ("terra", 6.95e-10, 0.02, "Terra surface GR (Ashby 2003 / GPS)"),
    ("sun",   2.12e-6,  0.02, "Sun surface GR"),
    ("mars",  1.40e-10, 0.05, "Mars surface GR (Genova 2014 / Curiosity)"),
    ("pluto", 8.15e-12, 0.05, "Pluto surface GR (smallest in the roster)"),
])
def test_surface_gr_matches_published(body: str, expected: float,
                                      rel_tol: float, label: str) -> None:
    out = get_proper_time_rate(body)
    rel_err = abs(out.gr_surface - expected) / expected
    assert rel_err <= rel_tol, (
        f"{label}: computed {out.gr_surface:.4e} vs. expected "
        f"{expected:.4e} (rel err {rel_err:.2%} > {rel_tol:.0%})"
    )


def test_terra_orbital_kinematic_matches_published() -> None:
    """Terra's orbital kinematic dilation ≈ 4.95×10⁻⁹."""
    expected = 4.95e-9
    out = get_proper_time_rate("terra")
    rel_err = abs(out.kinematic_orbital - expected) / expected
    assert rel_err <= 0.02, (
        f"Terra orbital kinematic: computed {out.kinematic_orbital:.4e} "
        f"vs. expected {expected:.4e} (rel err {rel_err:.2%})"
    )
    # Sanity: orbital velocity should be ~29.78 km/s.
    assert 29.0 < out.orbital_velocity_kms < 30.5


def test_mars_minus_terra_gr_difference_matches_published() -> None:
    """The famous 0.0175 s/Earth-year Mars-Terra clock-rate difference (GR-only).

    Cited in Curiosity rover navigation papers (Genova et al. 2014).
    Pure gravitational-potential-difference effect; orbital kinematic
    excluded.
    """
    terra = get_proper_time_rate("terra")
    mars = get_proper_time_rate("mars")
    gr_delta = terra.gr_surface - mars.gr_surface
    sec_per_yr = gr_delta * 365.25 * DAY_S
    assert abs(sec_per_yr - 0.01755) < 0.001, (
        f"Mars-Terra GR-only clock difference: {sec_per_yr:.4f} s/yr "
        f"(expected ~0.0175)"
    )


# ──────────────────────────────────────────────────────────────────────
# Primitive surface
# ──────────────────────────────────────────────────────────────────────

def test_rate_relative_to_reference_is_one_minus_total() -> None:
    out = get_proper_time_rate("mars")
    assert out.rate_relative_to_reference == pytest.approx(1.0 - out.total)


def test_default_reference_is_tcb() -> None:
    assert DEFAULT_REFERENCE == "tcb"
    assert "tcb" in SUPPORTED_REFERENCES
    assert "tdb" in SUPPORTED_REFERENCES


def test_unknown_body_raises() -> None:
    with pytest.raises(KeyError, match="unknown body"):
        get_proper_time_rate("fictitious")


def test_unknown_reference_raises() -> None:
    with pytest.raises(ValueError, match="reference must be"):
        get_proper_time_rate("terra", reference="utc")


def test_lat_lon_jd_args_accepted_for_forward_compat() -> None:
    """v0.11.0 ignores --lat/--lon/--jd_tdb but accepts them cleanly."""
    out = get_proper_time_rate("terra", lat=51.5, lon=-0.1, jd_tdb=2451545.0)
    assert out.body == "terra"
    # j2_oblateness is a placeholder in v0.11.0
    assert out.j2_oblateness == 0.0


def test_compare_proper_times_basic() -> None:
    cmp_result = compare_proper_times("mars", "terra")
    # body_a (mars) ticks faster than body_b (terra), so total_a < total_b
    # and seconds_per_earth_year is NEGATIVE (per the convention "more
    # dilation = lower rate").
    assert cmp_result["delta_total_a_minus_b"] < 0
    assert cmp_result["seconds_per_earth_year"] < 0
    # Rate ratio > 1 means body_a ticks faster. Mars > Terra.
    assert cmp_result["rate_ratio_a_over_b"] > 1.0


def test_orbital_velocity_for_sun_is_zero() -> None:
    """Sun has period_days = 0 → no orbital kinematic from Kepler."""
    out = get_proper_time_rate("sun")
    assert out.kinematic_orbital == 0.0
    assert out.orbital_velocity_kms == 0.0


def test_every_body_in_roster_has_a_rate() -> None:
    """Sanity: every body in BODIES yields a clean rate computation."""
    for body_key in BODIES:
        out = get_proper_time_rate(body_key)
        assert out.body == body_key
        # All v0.11.0 bodies have radii — no `note` should be set.
        assert out.note is None, (
            f"{body_key} returned note {out.note!r}; "
            f"missing surface_radius_km in BODIES?"
        )


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_proper_time_rate_smoke() -> None:
    r = bridge.get_proper_time_rate("mars")
    assert r["ok"] is True
    assert r["body"] == "mars"
    assert r["abbreviation"] == "SPrT"
    assert r["reference"] == "tcb"
    assert "components" in r
    assert "gr_surface" in r["components"]
    assert "kinematic_orbital" in r["components"]
    assert "j2_oblateness" in r["components"]


def test_bridge_unknown_body_returns_ok_false() -> None:
    r = bridge.get_proper_time_rate("fictitious")
    assert r["ok"] is False
    assert "must be one of" in r["error"]


def test_bridge_compare_proper_times_smoke() -> None:
    r = bridge.compare_proper_times("mars", "terra")
    assert r["ok"] is True
    assert r["body_a"] == "mars"
    assert r["body_b"] == "terra"
    assert "rate_ratio_a_over_b" in r
    assert "seconds_per_earth_year" in r


def test_bridge_apply_proper_correction_augments_count() -> None:
    """`apply_proper_correction` adds <field>_proper siblings + a block."""
    mars_time = bridge.jd_to_mars_time(2451545.0)
    augmented = bridge.apply_proper_correction(mars_time, "time-mars")
    assert "msd" in augmented
    assert "msd_proper" in augmented
    assert "proper_time" in augmented
    assert augmented["proper_time"]["applied"] is True
    assert augmented["proper_time"]["body"] == "mars"
    # The proper count should be smaller than the coordinate-time count
    # (Mars total dilation is positive → rate < 1).
    rate = augmented["proper_time"]["rate_relative_to_reference"]
    assert rate < 1.0
    assert augmented["msd_proper"] == pytest.approx(augmented["msd"] * rate)


def test_bridge_apply_proper_no_op_for_unknown_subcommand() -> None:
    """Unknown subcommand → return the result unchanged."""
    mars_time = bridge.jd_to_mars_time(2451545.0)
    augmented = bridge.apply_proper_correction(mars_time, "time-bogus")
    assert "msd_proper" not in augmented
    assert "proper_time" not in augmented


def test_bridge_apply_proper_no_op_on_error_response() -> None:
    err = {"ok": False, "error": "something"}
    out = bridge.apply_proper_correction(err, "time-mars")
    assert out is err  # unchanged


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────

def _run_cli_json(*argv: str) -> dict:
    from ephemerides_spectral.cli import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(list(argv))
    text = buf.getvalue()
    brace = text.find("{")
    assert brace >= 0, f"no JSON in stdout: {text!r}"
    parsed = json.loads(text[brace:])
    return {"_rc": rc, **parsed}


def test_cli_time_proper_basic() -> None:
    r = _run_cli_json("time-proper", "--body", "mars")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert r["body"] == "mars"
    assert r["abbreviation"] == "SPrT"


def test_cli_time_proper_compare() -> None:
    r = _run_cli_json("time-proper", "--body", "mars", "--compare-to", "terra")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert r["body_a"] == "mars"
    assert r["body_b"] == "terra"
    assert "rate_ratio_a_over_b" in r


def test_cli_proper_flag_on_time_mars() -> None:
    """--proper on time-mars augments the result with msd_proper + block."""
    r = _run_cli_json("time-mars", "--jd", "2451545.0", "--proper")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "msd" in r
    assert "msd_proper" in r
    assert "proper_time" in r
    assert r["proper_time"]["applied"] is True
    assert r["proper_time"]["body"] == "mars"


def test_cli_proper_flag_on_time_terra_luna() -> None:
    """--proper on STLT applies Terra's dilation to synodic_count etc."""
    r = _run_cli_json("time-terra-luna", "--jd", "2451545.0", "--proper")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "synodic_count" in r
    assert "synodic_count_proper" in r
    assert r["proper_time"]["body"] == "terra"


def test_cli_no_proper_flag_means_no_correction() -> None:
    """Default (no --proper) → output unchanged from previous releases."""
    r = _run_cli_json("time-mars", "--jd", "2451545.0")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "msd" in r
    assert "msd_proper" not in r
    assert "proper_time" not in r
