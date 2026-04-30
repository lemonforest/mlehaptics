"""Calendar-conversion bridge tests (§5.3).

Five methods: jd_to_gregorian, gregorian_to_jd, jd_to_julian_calendar,
jd_to_athenian, jd_to_olympiad.

Round-trips: gregorian_to_jd → jd_to_gregorian must return the same
date. Anchor checks: J2000 = 2451545.0 → 2000-01-01 12:00 TT.
"""

from __future__ import annotations

import pytest

from antikythera_spectral import bridge

# ──────────────────────────────────────────────────────────────────────
# Gregorian
# ──────────────────────────────────────────────────────────────────────

def test_j2000_to_gregorian() -> None:
    """J2000 = JD 2451545.0 = 2000-01-01 12:00 TT."""
    out = bridge.jd_to_gregorian(2451545.0)
    assert out["ok"] is True
    assert out["year"] == 2000
    assert out["month"] == 1
    assert out["day"] == 1
    assert out["hour"] == 12
    assert out["era"] == "CE"


def test_gregorian_round_trip_modern() -> None:
    a = bridge.gregorian_to_jd(2000, 1, 1, 12, 0, 0)
    assert a["ok"] is True
    assert a["jd_tdb"] == pytest.approx(2451545.0, abs=1e-6)

    b = bridge.jd_to_gregorian(a["jd_tdb"])
    assert b["year"] == 2000
    assert b["month"] == 1
    assert b["day"] == 1


def test_gregorian_round_trip_hellenistic_bce() -> None:
    """200 BCE round-trip — the era around the Antikythera mechanism."""
    a = bridge.gregorian_to_jd(200, 1, 1, 0, 0, 0, era="BCE")
    assert a["ok"] is True
    b = bridge.jd_to_gregorian(a["jd_tdb"])
    assert b["era"] == "BCE"
    assert b["year"] == 200
    assert b["month"] == 1
    assert b["day"] == 1


def test_gregorian_to_jd_rejects_invalid() -> None:
    out = bridge.gregorian_to_jd(2000, 13, 1)
    assert out["ok"] is False
    out = bridge.gregorian_to_jd(2000, 1, 32)
    assert out["ok"] is False
    out = bridge.gregorian_to_jd(2000, 1, 1, era="AD")
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Julian calendar
# ──────────────────────────────────────────────────────────────────────

def test_julian_calendar_anchor() -> None:
    """1582-10-15 Gregorian = 1582-10-05 Julian (the calendar reform skip)."""
    a = bridge.gregorian_to_jd(1582, 10, 15)
    assert a["ok"] is True
    j = bridge.jd_to_julian_calendar(a["jd_tdb"])
    assert j["ok"] is True
    assert j["year"] == 1582
    assert j["month"] == 10
    assert j["day"] == 5


# ──────────────────────────────────────────────────────────────────────
# Olympiad
# ──────────────────────────────────────────────────────────────────────

def test_olympiad_anchor() -> None:
    """JD 1438178 = Olympiad I, year 1 (776 BCE)."""
    out = bridge.jd_to_olympiad(1438178.0)
    assert out["ok"] is True
    assert out["olympiad_number"] == 1
    assert out["year_in_olympiad"] == 1


def test_olympiad_advances() -> None:
    """+ ~4 years = next Olympiad."""
    a = bridge.jd_to_olympiad(1438178.0)
    b = bridge.jd_to_olympiad(1438178.0 + 4 * 365.25)
    assert b["olympiad_number"] == a["olympiad_number"] + 1
    assert b["year_in_olympiad"] in (1, 2)  # boundary tolerance


def test_olympiad_at_reference_jd() -> None:
    """REFERENCE_JD (mechanism epoch ~102 BCE) → Olympiad ~169."""
    from antikythera_spectral.encoder import REFERENCE_JD
    out = bridge.jd_to_olympiad(REFERENCE_JD)
    assert out["ok"] is True
    # 776 - 102 = 674 yr / 4 = 168 → Olympiad 169 (ish)
    assert 165 <= out["olympiad_number"] <= 175


# ──────────────────────────────────────────────────────────────────────
# Athenian
# ──────────────────────────────────────────────────────────────────────

def test_athenian_anchor() -> None:
    """At the anchor JD, we should be near Hekatombaion 1."""
    out = bridge.jd_to_athenian(1438192.0)
    assert out["ok"] is True
    assert out["attic_month"] == "Hekatombaion"
    assert out["month_index"] == 1
    assert out["day_in_month"] == 1


def test_athenian_advances_through_months() -> None:
    """+ 30 days should advance one Attic month."""
    a = bridge.jd_to_athenian(1438192.0)
    b = bridge.jd_to_athenian(1438192.0 + 29.530588861)
    assert a["month_index"] != b["month_index"] or a["lunar_year"] != b["lunar_year"]


def test_athenian_archon_is_none_in_v01() -> None:
    """Archon name deferred to v0.2.0 per ADR 0007."""
    out = bridge.jd_to_athenian(1438192.0)
    assert out["archon"] is None
    assert "approximation_note" in out


# ──────────────────────────────────────────────────────────────────────
# Negative inputs
# ──────────────────────────────────────────────────────────────────────

def test_jd_to_gregorian_rejects_bad_jd() -> None:
    assert bridge.jd_to_gregorian("not-a-number")["ok"] is False
    assert bridge.jd_to_gregorian(float("nan"))["ok"] is False


def test_jd_to_olympiad_rejects_bad_jd() -> None:
    assert bridge.jd_to_olympiad("Olympiad I")["ok"] is False
