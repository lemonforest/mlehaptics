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


# ──────────────────────────────────────────────────────────────────────
# Sol Venusian Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# Venus is famously slow + retrograde. Its sidereal day is 243.02 Earth-
# days — *longer than its 224.7-day year* — so an observer standing on
# Venus sees the Sun rise in the west, take 116.75 Earth-days to cross
# the sky, and set in the east. The sidereal day and solar day are
# both useful, depending on whether you want "how long does Venus take
# to spin once relative to the stars" (sidereal) or "how long between
# successive sunrises" (solar).
#
# Anchor: J2000.0 (JD 2451545.0). No IAU-blessed VSD convention exists;
# we mirror the Mars Sol Date convention (count of sols since epoch)
# so callers get a uniform interface across the Sol Time family.

VENUS_SIDEREAL_DAY_DAYS:    float = 243.0226   # Earth days, retrograde
VENUS_SOLAR_DAY_DAYS:       float = 116.7500   # Earth days (synodic)
VENUS_ORBITAL_PERIOD_DAYS:  float = 224.701
VENUS_ORBITAL_PERIOD_YEARS: float = VENUS_ORBITAL_PERIOD_DAYS / 365.25
VENUS_AXIAL_TILT_DEG:       float = 177.36     # tilt > 90° → retrograde
VST_EPOCH_JD_TDB:           float = 2451545.0  # J2000.0


@dataclass(frozen=True)
class VenusTime:
    """Sol Venusian Time at a given JD (TDB)."""
    jd_tdb: float
    vsd_sidereal: float       # Venus sidereal-day count since J2000
    vsd_solar:    float       # Venus solar-day count since J2000
    vst_hours:    float       # solar-day time-of-day, [0, 24) Venus-hours
    orbital_phase: float
    years_since_epoch: float
    retrograde: bool = True

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "vsd_sidereal":      float(self.vsd_sidereal),
            "vsd_solar":         float(self.vsd_solar),
            "vst_hours":         float(self.vst_hours),
            "orbital_phase":     float(self.orbital_phase),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde":        bool(self.retrograde),
        }


def jd_to_venus_time(jd_tdb: float) -> VenusTime:
    """JD (TDB) → Sol Venusian Time."""
    delta = float(jd_tdb) - VST_EPOCH_JD_TDB
    vsd_sid = delta / VENUS_SIDEREAL_DAY_DAYS
    vsd_sol = delta / VENUS_SOLAR_DAY_DAYS
    sol_frac = vsd_sol - math.floor(vsd_sol)
    years = delta / VENUS_ORBITAL_PERIOD_DAYS
    return VenusTime(
        jd_tdb=float(jd_tdb),
        vsd_sidereal=vsd_sid,
        vsd_solar=vsd_sol,
        vst_hours=sol_frac * 24.0,
        orbital_phase=years - math.floor(years),
        years_since_epoch=years,
        retrograde=True,
    )


def venus_time_to_jd(vsd_solar: float) -> float:
    """Inverse on the Venus solar-day count."""
    return VST_EPOCH_JD_TDB + float(vsd_solar) * VENUS_SOLAR_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Mercurian Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# Mercury is in 3:2 spin-orbit resonance: it rotates exactly 3 times
# every 2 orbits. Consequence: the *solar* day on Mercury is exactly
# 2 Mercury years long — **a Mercury day is two Mercury years**.
#
# Three independent cycles all need to be exposed:
#
#   sidereal_day = 58.6462 Earth days   one rotation rel. to stars
#   solar_day    = 175.9842 Earth days  one rotation rel. to Sun
#                                        = 2 × Mercury year
#   year         = 87.9691 Earth days   one orbit
#
# The natural "what time is it on Mercury" answer uses solar-day
# coordinates (because that's what an observer experiences). The
# sidereal field is the spin-physics primitive.
#
# Anchor: J2000.0 with the IAU-defined prime meridian at the Hun Kal
# crater (W=20° at J2000).

MERCURY_SIDEREAL_DAY_DAYS:    float = 58.6462
MERCURY_SOLAR_DAY_DAYS:       float = 175.9842   # = 2 × MERCURY_ORBITAL_PERIOD_DAYS
MERCURY_ORBITAL_PERIOD_DAYS:  float = 87.9691
MERCURY_ORBITAL_PERIOD_YEARS: float = MERCURY_ORBITAL_PERIOD_DAYS / 365.25
MERCURY_AXIAL_TILT_DEG:       float = 0.034
MERT_EPOCH_JD_TDB:            float = 2451545.0  # J2000.0


@dataclass(frozen=True)
class MercuryTime:
    """Sol Mercurian Time at a given JD (TDB).

    Carries both sidereal-day and solar-day phase coordinates because
    Mercury's 3:2 spin-orbit resonance makes neither alone tell the
    full story.
    """
    jd_tdb: float
    mer_sd_sidereal: float    # sidereal-day count since J2000
    mer_sd_solar:    float    # solar-day count since J2000 (= 2 × year count)
    mer_t_hours:     float    # solar-day time-of-day, [0, 24) Mercury-hours
    orbital_phase:   float    # year fraction, [0, 1)
    mercury_years_since_epoch: float
    retrograde: bool = False

    def to_dict(self) -> dict:
        return {
            "jd_tdb":           float(self.jd_tdb),
            "mer_sd_sidereal":  float(self.mer_sd_sidereal),
            "mer_sd_solar":     float(self.mer_sd_solar),
            "mer_t_hours":      float(self.mer_t_hours),
            "orbital_phase":    float(self.orbital_phase),
            "mercury_years_since_epoch": float(self.mercury_years_since_epoch),
            "retrograde":       bool(self.retrograde),
        }


def jd_to_mercury_time(jd_tdb: float) -> MercuryTime:
    """JD (TDB) → Sol Mercurian Time."""
    delta = float(jd_tdb) - MERT_EPOCH_JD_TDB
    sid = delta / MERCURY_SIDEREAL_DAY_DAYS
    sol = delta / MERCURY_SOLAR_DAY_DAYS
    sol_frac = sol - math.floor(sol)
    years = delta / MERCURY_ORBITAL_PERIOD_DAYS
    return MercuryTime(
        jd_tdb=float(jd_tdb),
        mer_sd_sidereal=sid,
        mer_sd_solar=sol,
        mer_t_hours=sol_frac * 24.0,
        orbital_phase=years - math.floor(years),
        mercury_years_since_epoch=years,
        retrograde=False,
    )


def mercury_time_to_jd(mer_sd_solar: float) -> float:
    """Inverse on the Mercury solar-day count."""
    return MERT_EPOCH_JD_TDB + float(mer_sd_solar) * MERCURY_SOLAR_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Plutonian Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# Pluto's sidereal day is 6.3872 Earth-days. The Pluto-Charon system
# is mutually tidally locked — Charon's orbital period equals Pluto's
# rotation period exactly. The IAU-2015 prime-meridian convention
# anchors at the sub-Charon point.
#
# Pluto's tilt of 122.53° is similar to Uranus's 97.77° — extreme
# enough to give Pluto Uranian-style seasons each ~62 Earth-years
# long. We expose `orbital_phase` and `years_since_epoch` but skip
# the season-name discretisation for now (TODO: a future version can
# add it once the IAU/JPL season-naming convention is settled).
#
# Anchor: 2015-07-14 (New Horizons closest approach, JD 2457217.0).

PLUTO_SIDEREAL_DAY_DAYS:    float = 6.3872
PLUTO_ORBITAL_PERIOD_DAYS:  float = 90560.0
PLUTO_ORBITAL_PERIOD_YEARS: float = PLUTO_ORBITAL_PERIOD_DAYS / 365.25
PLUTO_AXIAL_TILT_DEG:       float = 122.53
PST_EPOCH_JD_TDB:           float = 2457217.0


@dataclass(frozen=True)
class PlutoTime:
    """Sol Plutonian Time at a given JD (TDB)."""
    jd_tdb: float
    psd:    float
    pst_hours: float
    pst_seconds: float
    orbital_phase: float
    years_since_epoch: float
    retrograde: bool = True

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "psd":               float(self.psd),
            "pst_hours":         float(self.pst_hours),
            "pst_seconds":       float(self.pst_seconds),
            "orbital_phase":     float(self.orbital_phase),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde":        bool(self.retrograde),
        }


def jd_to_pluto_time(jd_tdb: float) -> PlutoTime:
    """JD (TDB) → Sol Plutonian Time."""
    delta = float(jd_tdb) - PST_EPOCH_JD_TDB
    psd = delta / PLUTO_SIDEREAL_DAY_DAYS
    sol_frac = psd - math.floor(psd)
    years = delta / PLUTO_ORBITAL_PERIOD_DAYS
    return PlutoTime(
        jd_tdb=float(jd_tdb),
        psd=psd,
        pst_hours=sol_frac * 24.0,
        pst_seconds=sol_frac * PLUTO_SIDEREAL_DAY_DAYS * 86400.0,
        orbital_phase=years - math.floor(years),
        years_since_epoch=years,
        retrograde=True,
    )


def pluto_time_to_jd(psd: float) -> float:
    """Inverse on the Pluto sol-date count."""
    return PST_EPOCH_JD_TDB + float(psd) * PLUTO_SIDEREAL_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Sol Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# The Sun's own time. The Sun has no solid surface — it's a plasma
# ball with differential rotation (equator ~24.47 d, mid-latitudes
# ~25.38 d, poles ~38 d). We use the **Carrington rotation period**
# (25.38 d at 16° latitude) as the conventional reference, matching
# all of solar-physics literature. The "Carrington Rotation Number"
# (CRN) is an integer counter that started at CRN 1 on 1853-11-09
# and increments every 25.38 Earth-days.
#
# Galactic orbital period (~225 Myr) is included for completeness
# but is too slow for any practical phase calculation.
#
# Anchor: Carrington Rotation 1 epoch (1853-11-09, JD 2398167.4).

SOL_CARRINGTON_DAY_DAYS:    float = 25.38       # Carrington rotation period
SOL_GALACTIC_PERIOD_DAYS:   float = 8.0e10      # ~219 million years
SOL_AXIAL_TILT_DEG:         float = 7.25
SOL_T_EPOCH_JD_TDB:         float = 2398167.4   # CRN 1 start


@dataclass(frozen=True)
class SolSolTime:
    """Sol Sol Time at a given JD (TDB).

    Carrington-system time. The Sun has no IAU prime meridian (no
    solid surface), so the Carrington system anchored at CRN 1 is
    the conventional reference. The differential rotation means that
    sunspots near the equator drift forward relative to CRN, and
    sunspots near the poles drift backward — the 25.38-day period
    matches the rotation at ~16° latitude only.
    """
    jd_tdb: float
    crn: float                # Carrington Rotation Number (integer.fraction)
    crn_integer: int          # floor of CRN
    rotation_phase: float     # [0, 1) within the current rotation
    rotation_hours: float     # [0, 24) Sol-hours within the current rotation
    galactic_phase: float     # [0, 1) of one ~219 Myr galactic orbit; informational
    years_since_galactic_epoch: float

    def to_dict(self) -> dict:
        return {
            "jd_tdb":          float(self.jd_tdb),
            "crn":             float(self.crn),
            "crn_integer":     int(self.crn_integer),
            "rotation_phase":  float(self.rotation_phase),
            "rotation_hours":  float(self.rotation_hours),
            "galactic_phase":  float(self.galactic_phase),
            "years_since_galactic_epoch": float(self.years_since_galactic_epoch),
        }


def jd_to_sol_sol_time(jd_tdb: float) -> SolSolTime:
    """JD (TDB) → Sol Sol Time (Carrington system)."""
    delta = float(jd_tdb) - SOL_T_EPOCH_JD_TDB
    crn = 1.0 + delta / SOL_CARRINGTON_DAY_DAYS
    crn_int = int(math.floor(crn))
    rot_frac = crn - math.floor(crn)
    galactic_years = delta / SOL_GALACTIC_PERIOD_DAYS * (
        SOL_GALACTIC_PERIOD_DAYS / 365.25
    )
    return SolSolTime(
        jd_tdb=float(jd_tdb),
        crn=crn,
        crn_integer=crn_int,
        rotation_phase=rot_frac,
        rotation_hours=rot_frac * 24.0,
        galactic_phase=(delta / SOL_GALACTIC_PERIOD_DAYS) - math.floor(
            delta / SOL_GALACTIC_PERIOD_DAYS
        ),
        years_since_galactic_epoch=galactic_years,
    )


def sol_sol_time_to_jd(crn: float) -> float:
    """Inverse on the Carrington Rotation Number."""
    return SOL_T_EPOCH_JD_TDB + (float(crn) - 1.0) * SOL_CARRINGTON_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Jovian Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# Jupiter has differential rotation just like the Sun. Three reference
# systems exist:
#
#   System I    9h 50m 30s  cloud features at the equator (±10° lat)
#   System II   9h 55m 41s  cloud features at higher latitudes
#   System III  9h 55m 30s  magnetic field axis (the "official" rate
#                            per IAU; what's used in solar-system
#                            geodesy)
#
# We use System III, matching IAU practice. Jupiter has no moon
# dependency — System III rotation is observed via decametric radio
# emission tied to the magnetic field, which is intrinsic to Jupiter.
# Its moons orbit Jupiter but contribute nothing to its rotation rate.
#
# Anchor: System III 1965.0 reference epoch (JD 2444000.5, ~1979).

JUPITER_SYS_III_DAY_DAYS:    float = 0.41354    # 9h 55m 29.71s
JUPITER_ORBITAL_PERIOD_DAYS: float = 4332.589
JUPITER_ORBITAL_PERIOD_YEARS: float = JUPITER_ORBITAL_PERIOD_DAYS / 365.25
JUPITER_AXIAL_TILT_DEG:      float = 3.13
JOVT_EPOCH_JD_TDB:           float = 2444000.5  # System III 1965.0


@dataclass(frozen=True)
class JovianTime:
    """Sol Jovian Time at a given JD (TDB) — System III."""
    jd_tdb: float
    jsd: float
    jst_hours: float
    jst_seconds: float
    orbital_phase: float
    years_since_epoch: float
    retrograde: bool = False
    rotation_system: str = "III"

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "jsd":               float(self.jsd),
            "jst_hours":         float(self.jst_hours),
            "jst_seconds":       float(self.jst_seconds),
            "orbital_phase":     float(self.orbital_phase),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde":        bool(self.retrograde),
            "rotation_system":   str(self.rotation_system),
        }


def jd_to_jovian_time(jd_tdb: float) -> JovianTime:
    """JD (TDB) → Sol Jovian Time (System III)."""
    delta = float(jd_tdb) - JOVT_EPOCH_JD_TDB
    jsd = delta / JUPITER_SYS_III_DAY_DAYS
    sol_frac = jsd - math.floor(jsd)
    years = delta / JUPITER_ORBITAL_PERIOD_DAYS
    return JovianTime(
        jd_tdb=float(jd_tdb),
        jsd=jsd,
        jst_hours=sol_frac * 24.0,
        jst_seconds=sol_frac * JUPITER_SYS_III_DAY_DAYS * 86400.0,
        orbital_phase=years - math.floor(years),
        years_since_epoch=years,
        retrograde=False,
        rotation_system="III",
    )


def jovian_time_to_jd(jsd: float) -> float:
    """Inverse on the Jupiter sol-date count."""
    return JOVT_EPOCH_JD_TDB + float(jsd) * JUPITER_SYS_III_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Saturnian Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# Saturn's System III rotation period was historically 10h 39m 22.4s
# (Voyager 1980 magnetic-field tilt-tracking). Mankovich et al. (2019,
# ApJ 871:1) revised this to 10h 32m 35s ± 13s using Cassini ring
# seismology — the rings act as a giant seismometer for Saturn's
# interior modes. We use the Cassini-revised value.
#
# Saturn has no moon dependency for its rotation either; ring
# seismology yields the rotation rate from interior gravity-mode
# eigenfrequencies, which depend only on Saturn's interior structure.
#
# Anchor: J2000.0.

SATURN_SYS_III_DAY_DAYS:    float = 0.43932     # 10h 32m 35s (Cassini-revised)
SATURN_ORBITAL_PERIOD_DAYS: float = 10759.22
SATURN_ORBITAL_PERIOD_YEARS: float = SATURN_ORBITAL_PERIOD_DAYS / 365.25
SATURN_AXIAL_TILT_DEG:      float = 26.73
SATT_EPOCH_JD_TDB:          float = 2451545.0   # J2000.0


@dataclass(frozen=True)
class SaturnianTime:
    """Sol Saturnian Time at a given JD (TDB) — System III (Cassini-revised)."""
    jd_tdb: float
    ssd: float
    sst_hours: float
    sst_seconds: float
    orbital_phase: float
    years_since_epoch: float
    retrograde: bool = False
    rotation_system: str = "III-Cassini"

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "ssd":               float(self.ssd),
            "sst_hours":         float(self.sst_hours),
            "sst_seconds":       float(self.sst_seconds),
            "orbital_phase":     float(self.orbital_phase),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde":        bool(self.retrograde),
            "rotation_system":   str(self.rotation_system),
        }


def jd_to_saturnian_time(jd_tdb: float) -> SaturnianTime:
    """JD (TDB) → Sol Saturnian Time (System III, Cassini-revised)."""
    delta = float(jd_tdb) - SATT_EPOCH_JD_TDB
    ssd = delta / SATURN_SYS_III_DAY_DAYS
    sol_frac = ssd - math.floor(ssd)
    years = delta / SATURN_ORBITAL_PERIOD_DAYS
    return SaturnianTime(
        jd_tdb=float(jd_tdb),
        ssd=ssd,
        sst_hours=sol_frac * 24.0,
        sst_seconds=sol_frac * SATURN_SYS_III_DAY_DAYS * 86400.0,
        orbital_phase=years - math.floor(years),
        years_since_epoch=years,
        retrograde=False,
        rotation_system="III-Cassini",
    )


def saturnian_time_to_jd(ssd: float) -> float:
    """Inverse on the Saturn sol-date count."""
    return SATT_EPOCH_JD_TDB + float(ssd) * SATURN_SYS_III_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Neptunian Time (v0.8.0)
# ──────────────────────────────────────────────────────────────────────
#
# Neptune's sidereal day is 16h 6m 36s = 0.67125 Earth-days, defined
# by the magnetic-field rotation (System III since Voyager 2 1989).
# Prograde rotation, mid-range axial tilt (28.32°). Year is 164.79
# Earth-years.
#
# Anchor: J2000.0. No obvious natural epoch like Uranus's 2007
# northern equinox; J2000 mirrors Saturn's choice.

NEPTUNE_SIDEREAL_DAY_DAYS:    float = 0.67125
NEPTUNE_ORBITAL_PERIOD_DAYS:  float = 60182.0
NEPTUNE_ORBITAL_PERIOD_YEARS: float = NEPTUNE_ORBITAL_PERIOD_DAYS / 365.25
NEPTUNE_AXIAL_TILT_DEG:       float = 28.32
NEPT_EPOCH_JD_TDB:            float = 2451545.0  # J2000.0


@dataclass(frozen=True)
class NeptunianTime:
    """Sol Neptunian Time at a given JD (TDB).

    Voyager-2 measured Neptune's System III rotation period as
    16h 6m 36s ± 3s in 1989. Subsequent observations have not
    materially revised the value (no Cassini-equivalent ring
    seismology mission to Neptune yet — when one happens, this
    constant may need a Mankovich-style update).
    """
    jd_tdb: float
    nsd: float
    nst_hours: float
    nst_seconds: float
    orbital_phase: float
    years_since_epoch: float
    retrograde: bool = False
    rotation_system: str = "III"

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "nsd":               float(self.nsd),
            "nst_hours":         float(self.nst_hours),
            "nst_seconds":       float(self.nst_seconds),
            "orbital_phase":     float(self.orbital_phase),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde":        bool(self.retrograde),
            "rotation_system":   str(self.rotation_system),
        }


def jd_to_neptunian_time(jd_tdb: float) -> NeptunianTime:
    """JD (TDB) → Sol Neptunian Time."""
    delta = float(jd_tdb) - NEPT_EPOCH_JD_TDB
    nsd = delta / NEPTUNE_SIDEREAL_DAY_DAYS
    sol_frac = nsd - math.floor(nsd)
    years = delta / NEPTUNE_ORBITAL_PERIOD_DAYS
    return NeptunianTime(
        jd_tdb=float(jd_tdb),
        nsd=nsd,
        nst_hours=sol_frac * 24.0,
        nst_seconds=sol_frac * NEPTUNE_SIDEREAL_DAY_DAYS * 86400.0,
        orbital_phase=years - math.floor(years),
        years_since_epoch=years,
        retrograde=False,
        rotation_system="III",
    )


def neptunian_time_to_jd(nsd: float) -> float:
    """Inverse on the Neptune sol-date count."""
    return NEPT_EPOCH_JD_TDB + float(nsd) * NEPTUNE_SIDEREAL_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Terra Time (v0.9.1) — STT
# ──────────────────────────────────────────────────────────────────────
#
# Earth's own surface clock, anchored at J2000.0 with prime meridian
# at Greenwich. Notable distinctions:
#   sidereal day = 23h 56m 4s = 0.99726957 Earth-days  (rotation rel. to stars)
#   solar day    = 24h         = 1.0 Earth-day         (rotation rel. to Sun)
#   year         = 365.25636300 Earth-days             (sidereal year)
#
# The 3m 56s/day difference between sidereal and solar arises because
# Terra moves ~1° around its orbit per day, so it rotates ~361° between
# successive solar noons but only 360° between successive star transits.

TERRA_SIDEREAL_DAY_DAYS:    float = 0.99726957
TERRA_SOLAR_DAY_DAYS:       float = 1.0
TERRA_ORBITAL_PERIOD_DAYS:  float = 365.256363
TERRA_ORBITAL_PERIOD_YEARS: float = TERRA_ORBITAL_PERIOD_DAYS / 365.25
TERRA_AXIAL_TILT_DEG:       float = 23.4393
TERRAT_EPOCH_JD_TDB:        float = 2451545.0  # J2000.0


@dataclass(frozen=True)
class TerraTime:
    """Sol Terra Time (STT) at a given JD (TDB)."""
    jd_tdb: float
    tsd_sidereal: float       # Terra sidereal-day count since J2000
    tsd_solar:    float       # Terra solar-day count since J2000 (= JD - epoch)
    stt_hours:    float       # solar-day time-of-day, [0, 24) Terra-hours
    orbital_phase: float
    years_since_epoch: float
    retrograde: bool = False

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "tsd_sidereal":      float(self.tsd_sidereal),
            "tsd_solar":         float(self.tsd_solar),
            "stt_hours":         float(self.stt_hours),
            "orbital_phase":     float(self.orbital_phase),
            "years_since_epoch": float(self.years_since_epoch),
            "retrograde":        bool(self.retrograde),
        }


def jd_to_terra_time(jd_tdb: float) -> TerraTime:
    """JD (TDB) → Sol Terra Time (STT)."""
    delta = float(jd_tdb) - TERRAT_EPOCH_JD_TDB
    tsd_sid = delta / TERRA_SIDEREAL_DAY_DAYS
    tsd_sol = delta / TERRA_SOLAR_DAY_DAYS
    sol_frac = tsd_sol - math.floor(tsd_sol)
    years = delta / TERRA_ORBITAL_PERIOD_DAYS
    return TerraTime(
        jd_tdb=float(jd_tdb),
        tsd_sidereal=tsd_sid,
        tsd_solar=tsd_sol,
        stt_hours=sol_frac * 24.0,
        orbital_phase=years - math.floor(years),
        years_since_epoch=years,
        retrograde=False,
    )


def terra_time_to_jd(tsd_solar: float) -> float:
    """Inverse on the Terra solar-day count."""
    return TERRAT_EPOCH_JD_TDB + float(tsd_solar) * TERRA_SOLAR_DAY_DAYS


# ──────────────────────────────────────────────────────────────────────
# Sol Luna Time (v0.9.1) — SLT
# ──────────────────────────────────────────────────────────────────────
#
# Luna's surface clock. Tidally locked to Terra, so:
#   sidereal day = orbital period = 27.32166156 Earth-days
#   solar day    = synodic month = 29.530588853 Earth-days
#                  (one Luna sunrise to next; longer than sidereal because
#                  Terra-Luna system also moves around Sol during the cycle)
#
# DISTINCT FROM Sol Lunar Time (jd_to_lunar): that returns Luna's
# synodic + sidereal phase as observed from Terra (lunar age, etc.).
# Sol Luna Time is the local clock on Luna's surface — different
# semantic.
#
# Anchor: J2000.0 with the IAU 2015 prime meridian at the sub-Terra
# point (Luna is tidally locked, so the same hemisphere always faces
# Terra; the prime meridian is the longitude where Terra is overhead).

LUNA_SIDEREAL_DAY_DAYS:    float = 27.32166156
LUNA_SOLAR_DAY_DAYS:       float = 29.530588853   # synodic month
LUNA_ORBITAL_PERIOD_DAYS:  float = 27.32166156    # = sidereal day (tidally locked)
LUNA_AXIAL_TILT_DEG:       float = 6.687          # w.r.t. ecliptic
LUNAT_EPOCH_JD_TDB:        float = 2451545.0      # J2000.0


@dataclass(frozen=True)
class LunaTime:
    """Sol Luna Time (SLT) at a given JD (TDB).

    Distinct from Sol Lunar Time (`jd_to_lunar`), which returns Luna's
    synodic + sidereal phase as observed from Terra. SLT is the local
    surface clock on Luna.
    """
    jd_tdb: float
    lsd_sidereal: float       # Luna sidereal-day count since J2000
    lsd_solar:    float       # Luna solar (synodic) day count since J2000
    slt_hours:    float       # solar-day time-of-day, [0, 24) Luna-hours
    orbital_phase: float      # phase around Terra, [0, 1)
    luna_orbits_since_epoch: float
    retrograde: bool = False

    def to_dict(self) -> dict:
        return {
            "jd_tdb":            float(self.jd_tdb),
            "lsd_sidereal":      float(self.lsd_sidereal),
            "lsd_solar":         float(self.lsd_solar),
            "slt_hours":         float(self.slt_hours),
            "orbital_phase":     float(self.orbital_phase),
            "luna_orbits_since_epoch": float(self.luna_orbits_since_epoch),
            "retrograde":        bool(self.retrograde),
        }


def jd_to_luna_time(jd_tdb: float) -> LunaTime:
    """JD (TDB) → Sol Luna Time (SLT)."""
    delta = float(jd_tdb) - LUNAT_EPOCH_JD_TDB
    lsd_sid = delta / LUNA_SIDEREAL_DAY_DAYS
    lsd_sol = delta / LUNA_SOLAR_DAY_DAYS
    sol_frac = lsd_sol - math.floor(lsd_sol)
    orbits = delta / LUNA_ORBITAL_PERIOD_DAYS
    return LunaTime(
        jd_tdb=float(jd_tdb),
        lsd_sidereal=lsd_sid,
        lsd_solar=lsd_sol,
        slt_hours=sol_frac * 24.0,
        orbital_phase=orbits - math.floor(orbits),
        luna_orbits_since_epoch=orbits,
        retrograde=False,
    )


def luna_time_to_jd(lsd_solar: float) -> float:
    """Inverse on the Luna solar (synodic) day count."""
    return LUNAT_EPOCH_JD_TDB + float(lsd_solar) * LUNA_SOLAR_DAY_DAYS


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
    # v0.8.0 Sol Symphony Times: Venus, Mercury, Pluto, Sol, Jupiter, Saturn.
    "VENUS_SIDEREAL_DAY_DAYS",
    "VENUS_SOLAR_DAY_DAYS",
    "VENUS_ORBITAL_PERIOD_DAYS",
    "VENUS_ORBITAL_PERIOD_YEARS",
    "VENUS_AXIAL_TILT_DEG",
    "VST_EPOCH_JD_TDB",
    "MERCURY_SIDEREAL_DAY_DAYS",
    "MERCURY_SOLAR_DAY_DAYS",
    "MERCURY_ORBITAL_PERIOD_DAYS",
    "MERCURY_ORBITAL_PERIOD_YEARS",
    "MERCURY_AXIAL_TILT_DEG",
    "MERT_EPOCH_JD_TDB",
    "PLUTO_SIDEREAL_DAY_DAYS",
    "PLUTO_ORBITAL_PERIOD_DAYS",
    "PLUTO_ORBITAL_PERIOD_YEARS",
    "PLUTO_AXIAL_TILT_DEG",
    "PST_EPOCH_JD_TDB",
    "SOL_CARRINGTON_DAY_DAYS",
    "SOL_GALACTIC_PERIOD_DAYS",
    "SOL_AXIAL_TILT_DEG",
    "SOL_T_EPOCH_JD_TDB",
    "JUPITER_SYS_III_DAY_DAYS",
    "JUPITER_ORBITAL_PERIOD_DAYS",
    "JUPITER_ORBITAL_PERIOD_YEARS",
    "JUPITER_AXIAL_TILT_DEG",
    "JOVT_EPOCH_JD_TDB",
    "SATURN_SYS_III_DAY_DAYS",
    "SATURN_ORBITAL_PERIOD_DAYS",
    "SATURN_ORBITAL_PERIOD_YEARS",
    "SATURN_AXIAL_TILT_DEG",
    "SATT_EPOCH_JD_TDB",
    "NEPTUNE_SIDEREAL_DAY_DAYS",
    "NEPTUNE_ORBITAL_PERIOD_DAYS",
    "NEPTUNE_ORBITAL_PERIOD_YEARS",
    "NEPTUNE_AXIAL_TILT_DEG",
    "NEPT_EPOCH_JD_TDB",
    "MarsTime",
    "LunarTime",
    "UranianTime",
    "VenusTime",
    "MercuryTime",
    "PlutoTime",
    "SolSolTime",
    "JovianTime",
    "SaturnianTime",
    "NeptunianTime",
    "jd_to_msd",
    "msd_to_jd",
    "jd_to_lunar",
    "jd_to_uranian_time",
    "uranian_time_to_jd",
    "jd_to_venus_time",
    "venus_time_to_jd",
    "jd_to_mercury_time",
    "mercury_time_to_jd",
    "jd_to_pluto_time",
    "pluto_time_to_jd",
    "jd_to_sol_sol_time",
    "sol_sol_time_to_jd",
    "jd_to_jovian_time",
    "jovian_time_to_jd",
    "jd_to_saturnian_time",
    "saturnian_time_to_jd",
    "jd_to_neptunian_time",
    "neptunian_time_to_jd",
]
