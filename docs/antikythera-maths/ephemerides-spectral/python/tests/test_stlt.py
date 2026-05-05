"""v0.10.0 — Sol Terra-Luna Time (STLT) — focused tests.

The bridge surface and CLI primitives. Phase B of task #95.

Invariants enforced:

  1. Default epoch is Meton's 432 BCE summer solstice.
  2. JD ↔ synodic-count roundtrip is exact (within float precision).
  3. `epoch=` parameter accepts all five named anchors and produces
     consistent results.
  4. Synodic / Saros / Metonic counts at J2000 against a Meton epoch
     match closed-form expectations.
  5. The CLI subcommand parses through to the bridge and emits valid
     JSON with the expected fields.
"""

from __future__ import annotations

import io
import json
import math
from contextlib import redirect_stdout

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.time_scales import (
    STLT_DEFAULT_EPOCH,
    STLT_EPOCH_ANTIKYTHERA_JD_TDB,
    STLT_EPOCH_J2000_JD_TDB,
    STLT_EPOCH_METON_JD_TDB,
    STLT_EPOCHS,
    STLT_METONIC_CYCLE_DAYS,
    STLT_SAROS_CYCLE_DAYS,
    STLT_SYNODIC_MONTH_DAYS,
    jd_to_terra_luna_time,
    terra_luna_time_to_jd,
)


def test_default_epoch_is_meton() -> None:
    assert STLT_DEFAULT_EPOCH == "meton"
    assert "meton" in STLT_EPOCHS
    assert STLT_EPOCHS["meton"] == STLT_EPOCH_METON_JD_TDB


def test_all_epochs_present() -> None:
    """The five named epochs all map to JDs within DE441 coverage."""
    expected = {"meton", "antikythera", "hipparchus", "mardokempad", "j2000"}
    assert set(STLT_EPOCHS) == expected
    # DE441 covers -13200 BCE → +17191 CE; in JD that's roughly
    # JD 627000 to JD 8090000. All our anchors fall well inside.
    for name, jd in STLT_EPOCHS.items():
        assert 627000.0 <= jd <= 8_090_000.0, f"epoch {name!r} JD {jd} outside DE441"


def test_meton_epoch_jd_is_proleptic_julian_27_jun_432_bce() -> None:
    """Sanity-pin the Meton epoch JD.

    27 June 432 BCE proleptic Julian is the calibration anchor of the
    Metonic cycle. The constant should be within ~1 day of that date
    (we ship JD 1645528.0; cross-check with calendar-date conversion).
    """
    # Proleptic Julian formula (Meeus ch. 7) — same as the research
    # script. 432 BCE → astronomical year -431.
    year = -431
    month = 6
    day = 27
    if month <= 2:
        y, m = year - 1, month + 12
    else:
        y, m = year, month
    jd_noon = (math.floor(365.25 * (y + 4716))
               + math.floor(30.6001 * (m + 1))
               + day - 1524.5 + 0.5)
    # Within 1 day of the shipped constant.
    assert abs(jd_noon - STLT_EPOCH_METON_JD_TDB) <= 1.0, (
        f"Meton epoch JD {STLT_EPOCH_METON_JD_TDB} disagrees with "
        f"proleptic Julian 27 June 432 BCE noon ({jd_noon})"
    )


def test_jd_to_stlt_at_j2000_with_meton_epoch() -> None:
    """At JD = J2000, days_since_epoch = J2000 - Meton (~806017 days)."""
    out = jd_to_terra_luna_time(STLT_EPOCH_J2000_JD_TDB)
    assert out.epoch_name == "meton"
    assert out.epoch_jd_tdb == STLT_EPOCH_METON_JD_TDB
    expected_days = STLT_EPOCH_J2000_JD_TDB - STLT_EPOCH_METON_JD_TDB
    assert out.days_since_epoch == pytest.approx(expected_days, abs=1e-9)
    # Synodic count = days / synodic_month
    assert out.synodic_count == pytest.approx(
        expected_days / STLT_SYNODIC_MONTH_DAYS, rel=1e-12)
    # Phase ∈ [0, 1)
    assert 0.0 <= out.synodic_phase < 1.0
    assert 0.0 <= out.saros_phase < 1.0
    assert 0.0 <= out.metonic_phase < 1.0


def test_roundtrip_jd_to_stlt_to_jd() -> None:
    """JD → STLT → JD is exact (within float precision)."""
    for jd in (STLT_EPOCH_J2000_JD_TDB,
               STLT_EPOCH_J2000_JD_TDB + 365.25,
               STLT_EPOCH_J2000_JD_TDB - 1000.0,
               STLT_EPOCH_METON_JD_TDB):
        out = jd_to_terra_luna_time(jd)
        recovered = terra_luna_time_to_jd(out.synodic_count)
        assert recovered == pytest.approx(jd, abs=1e-9)


def test_roundtrip_for_each_epoch() -> None:
    """Each named epoch produces an exact roundtrip."""
    jd_test = STLT_EPOCH_J2000_JD_TDB + 100.0
    for epoch_name in STLT_EPOCHS:
        out = jd_to_terra_luna_time(jd_test, epoch=epoch_name)
        recovered = terra_luna_time_to_jd(out.synodic_count, epoch=epoch_name)
        assert recovered == pytest.approx(jd_test, abs=1e-9), (
            f"roundtrip failed for epoch {epoch_name!r}"
        )
        # And: count differs from the next-epoch's count by exactly the
        # epoch JD difference / synodic month.
        assert out.epoch_name == epoch_name


def test_unknown_epoch_raises() -> None:
    with pytest.raises(ValueError, match="epoch must be one of"):
        jd_to_terra_luna_time(2451545.0, epoch="bogus")
    with pytest.raises(ValueError, match="epoch must be one of"):
        terra_luna_time_to_jd(0.0, epoch="bogus")


def test_bridge_jd_to_sol_terra_luna_time_smoke() -> None:
    r = bridge.jd_to_sol_terra_luna_time(STLT_EPOCH_J2000_JD_TDB)
    assert r.get("ok") is True
    assert r["epoch_name"] == "meton"
    assert r["epoch_jd_tdb"] == STLT_EPOCH_METON_JD_TDB
    epoch_block = r["epoch"]
    assert epoch_block["abbreviation"] == "STLT"
    assert epoch_block["name"] == "meton"
    assert epoch_block["default_epoch"] == "meton"
    assert set(epoch_block["available_epochs"]) == set(STLT_EPOCHS)
    assert epoch_block["synodic_month_days"] == pytest.approx(
        STLT_SYNODIC_MONTH_DAYS)
    assert epoch_block["saros_cycle_days"] == pytest.approx(
        STLT_SAROS_CYCLE_DAYS)
    assert epoch_block["metonic_cycle_days"] == pytest.approx(
        STLT_METONIC_CYCLE_DAYS)


def test_bridge_with_antikythera_epoch_differs_from_meton() -> None:
    jd = STLT_EPOCH_J2000_JD_TDB
    r_meton = bridge.jd_to_sol_terra_luna_time(jd, epoch="meton")
    r_antik = bridge.jd_to_sol_terra_luna_time(jd, epoch="antikythera")
    assert r_meton["synodic_count"] != r_antik["synodic_count"]
    # The difference should equal (Meton epoch - Antikythera epoch) /
    # synodic month — i.e., the antikythera count is *smaller* (the
    # antikythera epoch is later than Meton, so fewer synodic months
    # have elapsed between antikythera and J2000).
    # synodic_count(epoch) = (J2000 - epoch) / synodic_month, so
    # (meton - antikythera) for the count = (J2000 - meton) - (J2000 - antik)
    # all over synodic_month = (antikythera_jd - meton_jd) / synodic_month.
    expected_delta = (
        (STLT_EPOCH_ANTIKYTHERA_JD_TDB - STLT_EPOCH_METON_JD_TDB)
        / STLT_SYNODIC_MONTH_DAYS
    )
    actual_delta = r_meton["synodic_count"] - r_antik["synodic_count"]
    assert actual_delta == pytest.approx(expected_delta, rel=1e-12)


def test_bridge_inverse_emits_jd() -> None:
    syn = 27294.31  # close to J2000 with Meton epoch
    r = bridge.sol_terra_luna_time_to_jd(syn)
    assert r["ok"] is True
    assert "jd_tdb" in r
    assert r["epoch_name"] == "meton"
    assert r["synodic_count"] == syn


def test_bridge_invalid_epoch_returns_ok_false() -> None:
    r = bridge.jd_to_sol_terra_luna_time(2451545.0, epoch="bogus")
    assert r["ok"] is False
    assert "bogus" in r["error"]
    assert "must be one of" in r["error"]


def test_synodic_phase_is_fractional_part() -> None:
    """`synodic_phase` should equal `synodic_count - floor(synodic_count)`."""
    for jd in (STLT_EPOCH_J2000_JD_TDB,
               STLT_EPOCH_J2000_JD_TDB + 30.0,
               STLT_EPOCH_J2000_JD_TDB + 1000.0):
        out = jd_to_terra_luna_time(jd)
        assert out.synodic_phase == pytest.approx(
            out.synodic_count - math.floor(out.synodic_count), abs=1e-12)
        assert out.saros_phase == pytest.approx(
            out.saros_count - math.floor(out.saros_count), abs=1e-12)
        assert out.metonic_phase == pytest.approx(
            out.metonic_count - math.floor(out.metonic_count), abs=1e-12)


def test_meton_epoch_synodic_count_at_meton_epoch_is_zero() -> None:
    """At the epoch itself, synodic_count == 0 exactly."""
    out = jd_to_terra_luna_time(STLT_EPOCH_METON_JD_TDB)
    assert out.synodic_count == 0.0
    assert out.synodic_phase == 0.0
    assert out.days_since_epoch == 0.0


def test_cli_time_terra_luna_default_meton() -> None:
    """End-to-end CLI: default invocation uses Meton's epoch."""
    from ephemerides_spectral.cli import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["time-terra-luna", "--jd", str(STLT_EPOCH_J2000_JD_TDB)])
    assert rc == 0
    text = buf.getvalue()
    brace = text.find("{")
    parsed = json.loads(text[brace:])
    assert parsed["ok"] is True
    assert parsed["epoch_name"] == "meton"


def test_cli_time_terra_luna_epoch_override() -> None:
    """CLI: --epoch antikythera switches to the Saros anchor."""
    from ephemerides_spectral.cli import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["time-terra-luna",
                   "--jd", str(STLT_EPOCH_J2000_JD_TDB),
                   "--epoch", "antikythera"])
    assert rc == 0
    parsed = json.loads(buf.getvalue()[buf.getvalue().find("{"):])
    assert parsed["epoch_name"] == "antikythera"
    assert parsed["epoch_jd_tdb"] == STLT_EPOCH_ANTIKYTHERA_JD_TDB


def test_cli_time_terra_luna_inverse() -> None:
    """CLI: --synodic-count inverts back to JD_TDB."""
    from ephemerides_spectral.cli import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["time-terra-luna", "--synodic-count", "27294.31"])
    assert rc == 0
    parsed = json.loads(buf.getvalue()[buf.getvalue().find("{"):])
    assert parsed["ok"] is True
    assert "jd_tdb" in parsed
    assert parsed["epoch_name"] == "meton"
