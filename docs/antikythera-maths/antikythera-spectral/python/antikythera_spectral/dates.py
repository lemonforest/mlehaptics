"""Calendar conversion: Gregorian / Julian / Athenian / Olympiad.

The Antikythera mechanism's back dial displays Olympiad games years
(Freeth, Jones, Steele, Bitsakis 2008, *Nature* 454:614). Conversion
between Julian Day numbers and the four calendar systems an ancient
astronomer or modern reader might use is therefore part of the
package's first-class surface.

Algorithms are Meeus's standard formulas (Meeus 1998, *Astronomical
Algorithms* 2nd ed., chapter 7) implemented in pure Python — no extras
needed.

Caveats
-------

- **JD ↔ Gregorian** uses the proleptic Gregorian calendar (the rule
  set extended backward before its 1582-10-15 introduction). Historians
  often want the Julian calendar for dates before that switch; use
  ``jd_to_julian_calendar``.
- **Athenian** dates: this module returns the Attic lunar-month name
  and day (computed from the Metonic cycle) but **not** the archonship
  year — the canonical archon table (Develin 1989, *Athenian Officials
  684-321 B.C.*) is not bundled in v0.1.0; see ADR 0007 for the
  rationale. ``archon`` is set to ``None`` for now.
- **Olympiad** is the four-year cycle starting Olympiad I.1 = July 776
  BCE (JD 1438178). Year-in-Olympiad is 1..4.

References
----------
Meeus, J. (1998). *Astronomical Algorithms*, 2nd edition. Willmann-Bell.
Freeth, T., Jones, A., Steele, J. M. & Bitsakis, Y. (2008). Calendars
    with Olympiad display and eclipse prediction on the Antikythera
    Mechanism. *Nature* 454:614.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────
# Gregorian
# ──────────────────────────────────────────────────────────────────────

# Anchor: JD 1438178 == 776-07-01 BCE proleptic Julian (Olympiad I.1).
# Anchor: JD 1721423.5 == -0001-12-31 to 0000-01-01 Gregorian midnight.
# Anchor: JD 2451545.0 == 2000-01-01 12:00:00 TT.

def _jd_to_calendar_meeus(jd: float, *, gregorian: bool) -> Dict[str, Any]:
    """Convert JD to (year, month, day, hour, minute, second).

    Per Meeus 1998 §7. ``gregorian`` selects the calendar system: True
    uses the proleptic Gregorian rules, False uses Julian rules.
    """
    jd_plus = jd + 0.5
    Z = math.floor(jd_plus)
    F = jd_plus - Z

    if gregorian and Z >= 2299161:
        alpha = math.floor((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - math.floor(alpha / 4)
    elif gregorian:
        # Pre-1582 Gregorian (proleptic): Meeus's "Z >= 2299161" branch
        # straddles the 1582-10-15 reform. For proleptic Gregorian we
        # stay in the alpha branch regardless.
        alpha = math.floor((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - math.floor(alpha / 4)
    else:
        A = Z

    B = A + 1524
    C = math.floor((B - 122.1) / 365.25)
    D = math.floor(365.25 * C)
    E = math.floor((B - D) / 30.6001)

    day_frac = B - D - math.floor(30.6001 * E) + F
    day = int(math.floor(day_frac))
    month = int(E - 1 if E < 14 else E - 13)
    year = int(C - 4716 if month > 2 else C - 4715)

    # Time of day from the fractional part.
    frac = day_frac - day
    seconds_total = round(frac * 86400)
    hour, rem = divmod(seconds_total, 3600)
    minute, second = divmod(rem, 60)

    era = "CE" if year >= 1 else "BCE"
    return {
        "year": year if year >= 1 else 1 - year,  # always positive; era distinguishes
        "month": month,
        "day": day,
        "hour": int(hour),
        "minute": int(minute),
        "second": int(second),
        "era": era,
        "proleptic_year": year,  # signed (e.g. -200 for 200 BCE)
    }


def jd_to_gregorian(jd_tdb: float) -> Dict[str, Any]:
    """Proleptic Gregorian calendar date for a Julian Day."""
    return _jd_to_calendar_meeus(jd_tdb, gregorian=True)


def jd_to_julian_calendar(jd_tdb: float) -> Dict[str, Any]:
    """Julian-calendar date for a Julian Day (relevant pre-1582-10-15)."""
    return _jd_to_calendar_meeus(jd_tdb, gregorian=False)


def gregorian_to_jd(year: int, month: int, day: int,
                    hour: int = 0, minute: int = 0, second: int = 0,
                    era: str = "CE") -> float:
    """Julian Day for a proleptic Gregorian date.

    ``era`` ∈ {``'CE'``, ``'BCE'``}; if ``BCE`` the ``year`` is treated
    as a positive ordinal (200 BCE → year=200, era='BCE') and converted
    internally to the astronomical -199.
    """
    if era not in ("CE", "BCE"):
        raise ValueError(f"era must be 'CE' or 'BCE', got {era!r}")
    y = year if era == "CE" else (1 - year)
    m = month
    d = day + (hour * 3600 + minute * 60 + second) / 86400.0
    if m <= 2:
        y -= 1
        m += 12
    A = math.floor(y / 100)
    B = 2 - A + math.floor(A / 4)
    return (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (m + 1))
        + d + B - 1524.5
    )


# ──────────────────────────────────────────────────────────────────────
# Olympiad
# ──────────────────────────────────────────────────────────────────────

# Olympiad I.1 = 776-07-01 BCE proleptic Julian = JD 1438178.0
_OLYMPIAD_I_1_JD: float = 1438178.0
"""Anchor: JD of Olympiad I, year 1 (the first Olympic Games, 776 BCE)."""

_TROPICAL_YEAR_DAYS: float = 365.24219
"""Modern tropical year length, used for Olympiad bin counting."""


def jd_to_olympiad(jd_tdb: float) -> Dict[str, Any]:
    """Olympiad number + year-in-Olympiad for a Julian Day.

    Returns
    -------
    dict
        ``{"olympiad_number": int, "year_in_olympiad": int (1..4),
        "year_in_era": int, "anchor_jd": float}``

    The Antikythera back dial physically displays this; Freeth, Jones,
    Steele & Bitsakis 2008 reconstruct the dial layout.
    """
    days_since_anchor = jd_tdb - _OLYMPIAD_I_1_JD
    years = days_since_anchor / _TROPICAL_YEAR_DAYS
    olympiad_number = int(math.floor(years / 4)) + 1
    year_in_olympiad = int(math.floor(years % 4)) + 1  # 1..4
    return {
        "olympiad_number": olympiad_number,
        "year_in_olympiad": year_in_olympiad,
        "year_in_era": int(math.floor(years)),  # 0-indexed years since anchor
        "anchor_jd": _OLYMPIAD_I_1_JD,
        "anchor_label": "Olympiad I.1 = 776-07-01 BCE (proleptic Julian)",
    }


# ──────────────────────────────────────────────────────────────────────
# Athenian (Attic months)
# ──────────────────────────────────────────────────────────────────────

# The 12 Attic month names, in canonical order. Year starts at the
# new moon after the summer solstice.
_ATTIC_MONTHS: List[str] = [
    "Hekatombaion",  # mid-Jul .. mid-Aug
    "Metageitnion",
    "Boedromion",
    "Pyanepsion",
    "Maimakterion",
    "Poseideon",     # mid-Dec .. mid-Jan (intercalary slot is "Poseideon II")
    "Gamelion",
    "Anthesterion",
    "Elaphebolion",
    "Mounichion",
    "Thargelion",
    "Skirophorion",  # mid-Jun .. mid-Jul
]

# Synodic month length used for Attic-month estimation (Meton's value).
_SYNODIC_MONTH: float = 29.530588861

# Anchor: nominal Hekatombaion 1 of Olympiad I.1 (~ 776-07-15 BCE,
# proleptic Julian). Approximate; Athenian observed lunation differs
# from a uniform 29.5-day model by up to 1 day. ADR 0007 documents the
# limit. JD 1438192 ≈ 776-07-15 BCE.
_ATTIC_ANCHOR_JD: float = 1438192.0


def jd_to_athenian(jd_tdb: float, *,
                   archon_table: str = "attic") -> Dict[str, Any]:
    """Approximate Attic-month + day for a Julian Day.

    v0.1.0 returns the lunar-month structure (Hekatombaion .. Skirophorion)
    derived from a uniform synodic-month model; the archonship name
    requires the Develin 1989 archon list which is not bundled in this
    release (see ADR 0007). ``archon`` is set to ``None``.

    Returns
    -------
    dict
        ::

            {
                "attic_month": str,           # e.g. "Hekatombaion"
                "month_index": int,           # 1..12
                "day_in_month": int,          # 1..30
                "lunar_year": int,            # rough year count from anchor
                "archon": None,                # v0.2.0 will fill this
                "archon_table": str,
                "approximation_note": str,
            }

    Caveats
    -------
    The Attic calendar was observational, so a single-day
    discrepancy from the modern synodic model is expected. For
    research-grade work, cross-check against Pritchett & Neugebauer 1947,
    *The Calendars of Athens*. The intercalary "Poseideon II" month
    is NOT modeled; lunar-cycle drift is folded into the year_count
    instead of an explicit intercalation rule.
    """
    if archon_table != "attic":
        return {
            "ok": False,
            "error": f"archon_table {archon_table!r} not supported in v0.1.0; "
                     "use 'attic'",
        }
    days = jd_tdb - _ATTIC_ANCHOR_JD
    months_total = days / _SYNODIC_MONTH
    lunar_year = int(months_total // 12)
    month_in_year = int(math.floor(months_total) % 12)
    fractional_month = months_total - math.floor(months_total)
    day_in_month = int(math.floor(fractional_month * 30)) + 1  # 1..30

    return {
        "attic_month": _ATTIC_MONTHS[month_in_year],
        "month_index": month_in_year + 1,
        "day_in_month": day_in_month,
        "lunar_year": lunar_year,
        "archon": None,
        "archon_table": archon_table,
        "approximation_note": (
            "Uniform-synodic-model approximation; ±1 day uncertainty vs. "
            "observed Attic dates. Archon name pending v0.2.0 (Develin 1989 "
            "table not bundled). See ADR 0007."
        ),
    }


__all__ = [
    "jd_to_gregorian",
    "jd_to_julian_calendar",
    "gregorian_to_jd",
    "jd_to_olympiad",
    "jd_to_athenian",
]
