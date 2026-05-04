"""Time-scale conversions for ephemerides-spectral.

Adds Mars Sol Date / Mars Coordinated Time (Allison & McEwen 2000)
and lunar synodic / sidereal phase primitives to the same package
that already speaks JD / J2000 natively.

Mars Sol Date (MSD)
-------------------

Per Allison & McEwen 2000 (Planet. Space Sci., 48, 215–235), the
Mars Sol Date is the count of mean Mars days since a reference
Mars-midnight at Airy-0 that falls on 1873-12-29 12:00 UTC. The
numerical recipe used here matches their published formula,
modulo conventional offsets:

    MSD = (JD_UTC + (TAI - UTC) / 86400 - 2405522.0025054) / 1.0274912517

where 1.0274912517 is the ratio (Mars day / Earth Julian day) and
TAI - UTC is the cumulative leap-second count (37 s as of 2017-01-01,
unchanged through 2026).

Mars Coordinated Time (MTC) is the fractional part of MSD expressed
as a 24-hour clock at the Martian prime meridian (Airy-0). One Mars
hour = (1/24) of a Mars sol = 1.0274912517 / 24 Earth days.

Lunar primitives
----------------

We provide synodic and sidereal lunar phase / age, derived from
fixed mean values:

    synodic month  = 29.530588853 days
    sidereal month = 27.321661547 days

Both are computed relative to a reference new-moon JD (TDB).
For full precision (sub-second fluctuation), a JPL DE-kernel
ephemeris call (skyfield's `astrometric` API on the moon) gives
the actual elongation; the fixed-mean primitives here are the
dial-style approximations the bronze antikythera used and are
sufficient for HDC-encoded events.

Lunar Coordinated Time (LTC) — formal definition pending across
NASA + international space agencies (target ~2026-2028 per the
April 2024 White House directive). LTE440 (Lin et al. 2025,
Astronomy & Astrophysics) ships the underlying SPICE-format
TCL/TCB/TDB conversion ephemeris. When LTC is finalised, this
module gains an ``LunarTime`` namespace mirroring ``MarsTime``.

References
----------

* Allison, M., & McEwen, M. (2000). "A post-Pathfinder evaluation
  of aerocentric solar coordinates with improved timing recipes
  for Mars seasonal/diurnal climate studies." Planet. Space Sci.,
  48, 215–235.
* Lin, X. et al. (2025). "Lunar time ephemeris LTE440: Definitions,
  algorithm, and performance." A&A 704, A76.
* JPL Mars24 Sunclock: https://www.giss.nasa.gov/tools/mars24/
* xlucn/LTE440: https://github.com/xlucn/LTE440
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


# ───────────────────────────────────────────────────────────────────
# Mars
# ───────────────────────────────────────────────────────────────────

#: Ratio of mean Mars sol to Earth Julian day (Allison & McEwen 2000).
MARS_SOL_PER_JD: float = 1.0274912517

#: MSD epoch in JD_UTC. MSD = 0 at JD 2405522.0025054 UTC, which is
#: 1873-12-29 12:03:36 UTC, the reference Mars midnight at Airy-0.
MSD_EPOCH_JD: float = 2405522.0025054

#: Default leap-second count (TAI − UTC) as of 2017-01-01, unchanged
#: through 2026. Callers in the future may need to bump this; the
#: published IERS Bulletin C is the authoritative source.
DEFAULT_LEAP_SECONDS: int = 37


@dataclass(frozen=True)
class MarsTime:
    """Mars time at a given JD_UTC.

    msd          :  Mars Sol Date (count of mean Mars sols).
    mtc_hours    :  Mars Coordinated Time, hours [0, 24).
    mtc_seconds  :  MTC expressed as seconds-since-midnight on Mars.
    sol_number   :  Integer floor(MSD); the current Mars sol.
    """
    jd_utc: float
    msd: float
    mtc_hours: float
    mtc_seconds: float
    sol_number: int

    def to_dict(self) -> dict:
        return {
            "jd_utc": float(self.jd_utc),
            "msd": float(self.msd),
            "mtc_hours": float(self.mtc_hours),
            "mtc_seconds": float(self.mtc_seconds),
            "sol_number": int(self.sol_number),
        }


def jd_to_msd(jd_utc: float, leap_seconds: int = DEFAULT_LEAP_SECONDS) -> MarsTime:
    """Convert UTC Julian Date → Mars Sol Date + Mars Coordinated Time.

    Implements Allison & McEwen 2000 §3:

        MSD = (JD_UTC + (TAI - UTC) / 86400 - MSD_EPOCH_JD) / MARS_SOL_PER_JD

    Parameters
    ----------
    jd_utc : float
        Julian Date in the UTC time scale.
    leap_seconds : int, default 37
        TAI − UTC offset in seconds. Authoritative source: IERS
        Bulletin C. Default tracks the Jan 2017 value, unchanged
        through 2026.

    Returns
    -------
    MarsTime
        ``msd`` (sols since MSD epoch), ``mtc_hours`` ∈ [0, 24),
        ``mtc_seconds`` ∈ [0, 86400 × 1.027…), ``sol_number``.
    """
    tai_utc_days = leap_seconds / 86400.0
    msd = (float(jd_utc) + tai_utc_days - MSD_EPOCH_JD) / MARS_SOL_PER_JD
    sol_number = int(math.floor(msd))
    mtc_fraction = msd - sol_number  # ∈ [0, 1)
    mtc_hours = mtc_fraction * 24.0
    mtc_seconds = mtc_fraction * 86400.0 * MARS_SOL_PER_JD
    return MarsTime(
        jd_utc=float(jd_utc),
        msd=msd,
        mtc_hours=mtc_hours,
        mtc_seconds=mtc_seconds,
        sol_number=sol_number,
    )


def msd_to_jd(msd: float, leap_seconds: int = DEFAULT_LEAP_SECONDS) -> float:
    """Inverse of :func:`jd_to_msd`. Returns ``JD_UTC``."""
    tai_utc_days = leap_seconds / 86400.0
    return MSD_EPOCH_JD + float(msd) * MARS_SOL_PER_JD - tai_utc_days


# ───────────────────────────────────────────────────────────────────
# Lunar (mean / dial-style)
# ───────────────────────────────────────────────────────────────────

#: Mean synodic month (new-moon-to-new-moon period), days. The
#: literature standard value (Naval Almanac / IERS conventions).
SYNODIC_MONTH_DAYS: float = 29.530588853

#: Mean sidereal month (period against the fixed-star background), days.
SIDEREAL_MONTH_DAYS: float = 27.321661547

#: Reference new moon: JD of new moon at J2000 epoch (TDB). Matches
#: the figure used in the bronze antikythera Saros / Metonic
#: anchors. The sub-day error is below the precision of mean-period
#: extrapolation, which is the main source of drift here anyway
#: (~few hours of drift per century).
LUNAR_REFERENCE_NEW_MOON_JD_TDB: float = 2451550.1


@dataclass(frozen=True)
class LunarTime:
    """Lunar synodic + sidereal phase / age primitives at a given JD.

    Mean values only (29.530588853 d synodic, 27.321661547 d
    sidereal). For arc-second-class accuracy, use the JPL DE
    ephemeris path (skyfield) which has the perturbation series
    baked in. These primitives are the bronze-dial approximations
    sufficient for HDC encoding and Saros-class navigation.

    synodic_age_days     :  Days since reference new moon, modular
                            into [0, SYNODIC_MONTH_DAYS).
    synodic_phase        :  Phase ∈ [0, 1). 0 = new moon, 0.5 = full.
    sidereal_age_days    :  Same shape, modulo SIDEREAL_MONTH_DAYS.
    sidereal_phase       :  Phase ∈ [0, 1) on the sidereal cycle.
    """
    jd_tdb: float
    synodic_age_days: float
    synodic_phase: float
    sidereal_age_days: float
    sidereal_phase: float

    def to_dict(self) -> dict:
        return {
            "jd_tdb": float(self.jd_tdb),
            "synodic_age_days": float(self.synodic_age_days),
            "synodic_phase": float(self.synodic_phase),
            "sidereal_age_days": float(self.sidereal_age_days),
            "sidereal_phase": float(self.sidereal_phase),
        }


def jd_to_lunar(jd_tdb: float) -> LunarTime:
    """Convert JD (TDB) → mean synodic + sidereal lunar age/phase.

    Both phases are referenced to ``LUNAR_REFERENCE_NEW_MOON_JD_TDB``
    (the J2000-anchored new moon). Sidereal phase is referenced to
    the same instant — at that JD the moon's ecliptic longitude
    coincides with its J2000 reference, by construction.

    For higher accuracy in any specific narrow window (where the
    perturbation series matters), call into the JPL DE ephemeris
    via skyfield instead.
    """
    delta_days = float(jd_tdb) - LUNAR_REFERENCE_NEW_MOON_JD_TDB

    syn_age = delta_days % SYNODIC_MONTH_DAYS
    syn_phase = syn_age / SYNODIC_MONTH_DAYS

    sid_age = delta_days % SIDEREAL_MONTH_DAYS
    sid_phase = sid_age / SIDEREAL_MONTH_DAYS

    return LunarTime(
        jd_tdb=float(jd_tdb),
        synodic_age_days=syn_age,
        synodic_phase=syn_phase,
        sidereal_age_days=sid_age,
        sidereal_phase=sid_phase,
    )


__all__ = [
    "MARS_SOL_PER_JD",
    "MSD_EPOCH_JD",
    "DEFAULT_LEAP_SECONDS",
    "SYNODIC_MONTH_DAYS",
    "SIDEREAL_MONTH_DAYS",
    "LUNAR_REFERENCE_NEW_MOON_JD_TDB",
    "MarsTime",
    "LunarTime",
    "jd_to_msd",
    "msd_to_jd",
    "jd_to_lunar",
]
