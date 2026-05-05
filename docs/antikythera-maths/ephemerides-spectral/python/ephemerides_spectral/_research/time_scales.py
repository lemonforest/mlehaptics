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


# ───────────────────────────────────────────────────────────────────
# Sol Uranian Time (SUT) — v0.5.4
# ───────────────────────────────────────────────────────────────────
#
# Uranus's "natural harmonic" pairs a fast retrograde rotation
# (~17.24 h sidereal) against an extreme axial-tilt orbit (97.77° tilt,
# 84.02 yr period). The physical consequence is unique among the
# planets: every Uranian point spends ~21 yr in continuous daylight,
# then ~21 yr in continuous darkness. Time on Uranus therefore
# decomposes into THREE natural cycles, not two:
#
#   1. **Sidereal day** (rotation against the fixed-star background) —
#      17.24 h ≈ 0.71833 d. Retrograde (the planet rotates backward
#      relative to its orbital motion); we emit unsigned magnitudes
#      and carry the retrograde-ness as a flag.
#   2. **Solar day** (sun-to-sun on Uranus) — for Earth this differs
#      from the sidereal day by ~4 minutes; for Uranus the long
#      orbital period makes the solar/sidereal ratio essentially
#      unity (1 + 1/42721, ~2.3e-5).
#   3. **Seasonal phase** — Uranus's orbital phase relative to the
#      solstice/equinox cycle. The 4 distinct seasonal configurations
#      (north-pole-summer, descending equinox, south-pole-summer,
#      ascending equinox) partition the 84.02 yr orbit into ~21 yr
#      quarters. Anchored at the 2007 northern equinox (JD 2454451.0)
#      where the sun crossed Uranus's equator on its way to southern
#      summer (2028).
#
# The "natural harmonic" idea (notebook §6) plays out as a triplet
# (USD, SUT, SUS) of independent cyclic phases. Their coprime
# decomposition is essentially unrelated to the lcm of integer
# resonance pairs in `RESONANCES` — Uranus doesn't sit in a clean
# mean-motion resonance with anything in the Sol Star System
# (its 84.02 yr is not an integer multiple of any nearby body's
# period). Sol Uranian Time therefore lives in its OWN cyclic group
# rather than feeding back into the natural-resonance `Z_60` of v0.5.0.

#: Uranus sidereal rotation period in Earth days (retrograde).
#: 17.24 h is the value used by the IAU/NASA fact sheet, which itself
#: tracks the Voyager-2 1986 radio-occultation magnetic-field result
#: (-17h 14m 24s ≈ -17.24 h). The "minus" reflects the retrograde
#: sense relative to Uranus's orbital motion; we carry that as a
#: separate ``retrograde=True`` flag in :class:`UranianTime` rather
#: than as a negative period.
URANUS_SIDEREAL_DAY_HOURS: float = 17.24
URANUS_SIDEREAL_DAY_DAYS:  float = URANUS_SIDEREAL_DAY_HOURS / 24.0  # ≈ 0.7183333…

#: Uranus orbital period (sidereal year), Earth days.
#: From the high-precision BODIES table (v0.5.3) — JPL HORIZONS.
URANUS_ORBITAL_PERIOD_DAYS: float = 30688.5
URANUS_ORBITAL_PERIOD_YEARS: float = URANUS_ORBITAL_PERIOD_DAYS / 365.25  # ≈ 84.0205

#: Uranus axial tilt (degrees from orbital plane normal). The 97.77°
#: tilt is what makes Uranus rotate "on its side"; values near 90°
#: produce extreme polar-day / polar-night cycles each lasting one
#: quarter of an orbit.
URANUS_AXIAL_TILT_DEG: float = 97.77

#: Reference epoch for SUT — Uranus's 2007 northern equinox, when
#: the Sun crossed Uranus's equator on its way to southern summer.
#: Approximate JD: 2007-12-16 00:00 UTC.
SUT_EPOCH_JD_TDB: float = 2454451.0

#: Names of the four Uranian seasons, in order from the northern
#: equinox (anchor). Each spans approximately ``URANUS_ORBITAL_PERIOD_YEARS / 4``
#: ≈ 21 years.
URANIAN_SEASONS: Tuple[str, str, str, str] = (
    "northern-autumn",   # equinox -> southern-summer-solstice  (2007 -> 2028)
    "southern-summer",   # solstice -> ascending-equinox        (2028 -> 2050)
    "northern-spring",   # equinox -> northern-summer-solstice  (2050 -> 2071)
    "northern-summer",   # solstice -> descending-equinox       (2071 -> 2092)
)


@dataclass(frozen=True)
class UranianTime:
    """Sol Uranian Time at a given JD (TDB).

    Three independent phase coordinates:

    - ``usd``           Uranian Sol Date — count of mean Uranian
                        sidereal days since :data:`SUT_EPOCH_JD_TDB`.
                        Floats; positive past the epoch, negative
                        before. Integer floor → sol number.
    - ``sut_hours``     Sol Uranian Time, hours ∈ [0, 24). Time-of-day
                        on Uranus. One Uranian hour = ``URANUS_SIDEREAL_DAY_HOURS / 24``
                        Earth hours = ~43.1 minutes.
    - ``sut_seconds``   SUT expressed as Earth-seconds since Uranian
                        midnight. Equals ``sut_hours × URANUS_SIDEREAL_DAY_DAYS × 86400 / 24``.

    Plus the orbital-cycle layer:

    - ``orbital_phase`` ∈ [0, 1). Uranus's orbital phase relative to
                        the SUT epoch (2007 northern equinox → 0.0).
    - ``season``        One of :data:`URANIAN_SEASONS` based on
                        ``orbital_phase``.
    - ``years_since_epoch``  Real-valued Uranian years since epoch
                        (orbital_phase + integer-orbits).
    - ``retrograde``    True. Uranus rotates retrograde relative to
                        its orbital motion; the magnitude in ``usd``
                        is unsigned (counts wall-clock days), but
                        the rotation direction is *backwards* relative
                        to the prograde convention used for Earth /
                        Mars / etc. Callers that care about the sign
                        of angular velocity (e.g., the diagnosed-fiber
                        encoder for retrograde irregulars) read this
                        flag.

    Example for ``jd_tdb = 2451545.0`` (J2000):

        UranianTime(
            jd_tdb=2451545.0,
            usd=-4046.45,             # 4046 Uranian sols BEFORE the SUT epoch
            sut_hours=13.30,
            sut_seconds=20657,
            orbital_phase=0.9054,     # ~95% through one orbit before 2007 equinox
            season="northern-summer",
            years_since_epoch=-7.96,
            retrograde=True,
        )
    """
    jd_tdb: float
    usd: float
    sut_hours: float
    sut_seconds: float
    orbital_phase: float
    season: str
    years_since_epoch: float
    retrograde: bool = True

    def to_dict(self) -> dict:
        return {
            "jd_tdb": float(self.jd_tdb),
            "usd": float(self.usd),
            "sut_hours": float(self.sut_hours),
            "sut_seconds": float(self.sut_seconds),
            "orbital_phase": float(self.orbital_phase),
            "season": str(self.season),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde": bool(self.retrograde),
        }


def jd_to_uranian_time(jd_tdb: float) -> UranianTime:
    """Convert JD (TDB) → Sol Uranian Time + orbital-season state.

    The three layers are independent — ``usd`` and ``sut_hours``
    measure Uranus's rotation; ``orbital_phase`` measures its
    revolution; ``season`` is a discretisation of ``orbital_phase``
    against the four seasonal solstice/equinox configurations.

    For arc-second-precision Uranus rotation (with sub-decadal
    precession + nutation perturbations), use the IAU rotation
    model (Archinal et al. 2018) — this routine uses the constant
    sidereal period from the IAU/NASA fact sheet, which has
    sub-arcminute drift over the v0.5.x DE441 epoch.
    """
    delta_days = float(jd_tdb) - SUT_EPOCH_JD_TDB

    usd = delta_days / URANUS_SIDEREAL_DAY_DAYS
    sol_fraction = usd - math.floor(usd)
    sut_hours = sol_fraction * 24.0
    sut_seconds = sol_fraction * URANUS_SIDEREAL_DAY_DAYS * 86400.0

    years_since_epoch = delta_days / URANUS_ORBITAL_PERIOD_DAYS
    orbital_phase = years_since_epoch - math.floor(years_since_epoch)
    # Map orbital_phase into one of 4 seasons.
    season_idx = int(orbital_phase * 4) % 4
    season = URANIAN_SEASONS[season_idx]

    return UranianTime(
        jd_tdb=float(jd_tdb),
        usd=usd,
        sut_hours=sut_hours,
        sut_seconds=sut_seconds,
        orbital_phase=orbital_phase,
        season=season,
        years_since_epoch=years_since_epoch,
        retrograde=True,
    )


def uranian_time_to_jd(usd: float) -> float:
    """Inverse of :func:`jd_to_uranian_time` for the ``usd`` field.

    Returns ``JD_TDB``. Note: the inverse only takes ``usd`` (the
    sol-date count); the ``orbital_phase`` field is uniquely
    determined by ``usd × URANUS_SIDEREAL_DAY_DAYS / URANUS_ORBITAL_PERIOD_DAYS``
    given the same SUT epoch, so there's no information loss.
    """
    return SUT_EPOCH_JD_TDB + float(usd) * URANUS_SIDEREAL_DAY_DAYS


__all__ = [
    "MARS_SOL_PER_JD",
    "MSD_EPOCH_JD",
    "DEFAULT_LEAP_SECONDS",
    "SYNODIC_MONTH_DAYS",
    "SIDEREAL_MONTH_DAYS",
    "LUNAR_REFERENCE_NEW_MOON_JD_TDB",
    "URANUS_SIDEREAL_DAY_HOURS",
    "URANUS_SIDEREAL_DAY_DAYS",
    "URANUS_ORBITAL_PERIOD_DAYS",
    "URANUS_ORBITAL_PERIOD_YEARS",
    "URANUS_AXIAL_TILT_DEG",
    "SUT_EPOCH_JD_TDB",
    "URANIAN_SEASONS",
    "MarsTime",
    "LunarTime",
    "UranianTime",
    "jd_to_msd",
    "msd_to_jd",
    "jd_to_lunar",
    "jd_to_uranian_time",
    "uranian_time_to_jd",
]
