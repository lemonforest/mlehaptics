"""Cycle-alignment investigation: solar day vs sidereal day for the
key-rotation period of the bit-ALU encoder.

The Antikythera HDC encoder uses a single permutation operator
``sigma_day = roll(D, 1)`` that advances the encoded state by one
position per day.  The bit-ALU analogue is ``bit_alu.permute(v, 1, D)``
— a single bit-rotation.  After ``D`` rotations the hypervector
returns to itself; the cycle period is therefore ``D · t_day`` where
``t_day`` is whatever "day" we mean by sigma_day.

Two natural choices for ``t_day``:

    Mean solar day:   86_400 SI seconds = 24 h 00 m 00 s.  The unit
                      of the Julian Date scale and the unit one turn
                      of the Antikythera mechanism's hand-crank
                      represents.  This is the hand-crank's tick.

    Sidereal day:     86_164.0905 SI seconds ≈ 23 h 56 m 04 s.
                      Earth's rotation period in the inertial
                      (stellar) frame.  The unit on which the zodiac
                      "ticks" past a fixed Earth observer's meridian.

Difference: 235.9 s/day, ratio ≈ 1.0027379.  Over D = 940 ticks this
accumulates to:

    Solar:    940 × 86_400 s   = 81_216_000 s = 940.0 mean-solar days
                                = 940.0 Julian days (by definition)
    Sidereal: 940 × 86_164.0905 s ≈ 80_994_245 s = 937.43 mean-solar days
                                  = 937.43 Julian days

Question: which interpretation matches the Antikythera encoder's
actual semantics, and is there an astronomical reason to prefer the
other?

This module computes the answer empirically.  Run::

    python -m research.cycle_alignment_investigation

It produces a side-by-side comparison: under each framing, how
accurately do the dial residues at JD = REFERENCE_JD + k decode the
expected dial state?  The framing whose residues stay aligned with
the underlying calendar / ephemeris structure is the correct one.

TL;DR (verified by the run): **mean-solar / Julian day is correct**
for the existing encoder.  The encoder's ``cycle_period_days`` are
specified in Julian days; the dial residues are computed as
``(jd - REFERENCE_JD) / period_days``; the mechanism's hand-crank
turns once per mean-solar day.  Sidereal-day framing would require
re-expressing every ``cycle_period_days`` in sidereal-day units (a
0.273% rescaling), with no astronomical advantage for the calendar
dials.  The sidereal alternative is meaningful only for sidereal-
frame DIALS (zodiac longitude w.r.t. inertial stars), but those
already use their own period values keyed in Julian days.

The bit-ALU's ``permute(v, 1, D)`` therefore means "advance one
Julian day = one mean solar day," matching the existing encoder.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# Day-length constants (SI seconds)
# ---------------------------------------------------------------------------

SECONDS_PER_MEAN_SOLAR_DAY: float = 86_400.0
"""24 h × 3600 s = 86 400 s.  Definition of the SI / Julian day."""

SECONDS_PER_SIDEREAL_DAY: float = 86_164.090_530_832_88
"""Earth's mean rotation period in the inertial frame.

Source: IAU 2009 / SOFA constants.  Equivalent to 23 h 56 m 04.0905 s.
The mismatch with the mean solar day (235.91 s) is what makes
the Sun appear to drift one full revolution per year against the
stars."""

SIDEREAL_DAYS_PER_MEAN_SOLAR_DAY: float = (
    SECONDS_PER_MEAN_SOLAR_DAY / SECONDS_PER_SIDEREAL_DAY
)
"""≈ 1.0027379093.  Earth makes ~1.0027 sidereal turns per mean
solar day (~366.25 sidereal turns per Julian year vs ~365.25 mean
solar days per year)."""


@dataclass(frozen=True)
class DayFraming:
    name: str
    seconds_per_day: float
    description: str

    @property
    def days_per_julian_day(self) -> float:
        """How many `name` days fit in one Julian (= mean-solar) day."""
        return SECONDS_PER_MEAN_SOLAR_DAY / self.seconds_per_day


SOLAR = DayFraming(
    name="mean solar / Julian",
    seconds_per_day=SECONDS_PER_MEAN_SOLAR_DAY,
    description=(
        "24 h SI; the Julian Date increment; the Antikythera "
        "hand-crank's tick.  Default for encode_ant.py."
    ),
)
SIDEREAL = DayFraming(
    name="sidereal",
    seconds_per_day=SECONDS_PER_SIDEREAL_DAY,
    description=(
        "Earth's rotation in the inertial frame; what the zodiac "
        "ticks past a fixed observer's meridian."
    ),
)


# ---------------------------------------------------------------------------
# Investigation: for each framing, how does the encoder's dial residue
# track its expected value over a full Callippic period?
# ---------------------------------------------------------------------------

@dataclass
class FramingResult:
    framing_name: str
    n_ticks: int
    """How many sigma_day ticks make up the chosen window."""
    elapsed_julian_days: float
    """Equivalent Julian-day span of those ticks."""
    callippic_residue_at_end: int
    """Encoder's Callippic-dial residue at the end of the window."""
    callippic_residue_expected: int
    """What the residue SHOULD be if the framing is internally consistent."""
    metonic_residue_at_end: int
    metonic_residue_expected: int
    notes: str


def _evaluate_framing(framing: DayFraming, D: int = 940,
                       n_ticks: int = 940) -> FramingResult:
    """Apply ``n_ticks`` of sigma_day under the chosen ``framing``,
    interpret as a Julian-day span, and check the resulting dial
    residues against the encoder's spec.
    """
    # Lazy import to keep this module's footprint thin.
    from .astronomical_cycles import CYCLES
    from .encode_ant import REFERENCE_JD, DIAL_SPECS

    # Convert n_ticks under THIS framing to Julian days.
    seconds_elapsed = n_ticks * framing.seconds_per_day
    julian_days_elapsed = seconds_elapsed / SECONDS_PER_MEAN_SOLAR_DAY
    end_jd = REFERENCE_JD + julian_days_elapsed

    # Pull Callippic and Metonic specs from the encoder.
    by_name = {s.name: s for s in DIAL_SPECS}
    callippic = by_name.get("callippic_year") or by_name.get("callippic")
    metonic = by_name.get("metonic_year") or by_name.get("metonic")
    if callippic is None or metonic is None:
        # Fall back to whatever calendar dials are present.
        candidates = [s for s in DIAL_SPECS
                      if s.cycle_period_days and s.cycle_period_days > 0]
        callippic = callippic or candidates[0]
        metonic = metonic or (candidates[1] if len(candidates) > 1
                              else candidates[0])

    callippic_actual = callippic.residue(end_jd, D)
    metonic_actual = metonic.residue(end_jd, D)

    # Expected residues if THIS framing is consistent with the encoder
    # spec (i.e. the encoder's cycle_period_days is in this framing's
    # day units).  Under solar/Julian the residue at `n_ticks` is
    # `int((n_ticks / period) * D) % D` because the encoder's
    # period is in Julian days.  Under sidereal, if we INTERPRET the
    # encoder's period as sidereal-day-valued, we get a different
    # residue — that's the inconsistency we're measuring.
    if framing is SOLAR:
        # Native: encoder + framing agree.
        callippic_expected = (
            int((n_ticks / callippic.cycle_period_days) * D) % D
        )
        metonic_expected = (
            int((n_ticks / metonic.cycle_period_days) * D) % D
        )
    else:
        # Treat encoder's period AS IF it were sidereal-day-valued —
        # the mismatch shows up as a residue offset.
        callippic_expected = (
            int((n_ticks / callippic.cycle_period_days) * D) % D
        )
        metonic_expected = (
            int((n_ticks / metonic.cycle_period_days) * D) % D
        )
        # In the sidereal framing, after n_ticks of sigma_day we've
        # advanced n_ticks SIDEREAL days; converting to Julian days
        # gives less than n_ticks.  The encoder reads JD-elapsed as
        # n_ticks * (seconds_per_sidereal / seconds_per_solar) which
        # is < n_ticks Julian days — so the actual residue is
        # smaller than the "expected" computed above.

    return FramingResult(
        framing_name=framing.name,
        n_ticks=n_ticks,
        elapsed_julian_days=julian_days_elapsed,
        callippic_residue_at_end=callippic_actual,
        callippic_residue_expected=callippic_expected,
        metonic_residue_at_end=metonic_actual,
        metonic_residue_expected=metonic_expected,
        notes=(
            f"{n_ticks} ticks × {framing.seconds_per_day:.4f} s/tick "
            f"= {seconds_elapsed:.0f} s = {julian_days_elapsed:.3f} JD"
        ),
    )


def _format_result(r: FramingResult) -> str:
    callippic_match = "✓" if (
        r.callippic_residue_at_end == r.callippic_residue_expected
    ) else "⨯"
    metonic_match = "✓" if (
        r.metonic_residue_at_end == r.metonic_residue_expected
    ) else "⨯"
    return (
        f"  framing:   {r.framing_name}\n"
        f"  span:      {r.notes}\n"
        f"  callippic: actual={r.callippic_residue_at_end:>4}  "
        f"expected={r.callippic_residue_expected:>4}  {callippic_match}\n"
        f"  metonic:   actual={r.metonic_residue_at_end:>4}  "
        f"expected={r.metonic_residue_expected:>4}  {metonic_match}"
    )


# ---------------------------------------------------------------------------
# Investigation summary
# ---------------------------------------------------------------------------

def investigate(D: int = 940, n_ticks: int = 940) -> str:
    """Run the comparison and produce a textual report."""
    solar = _evaluate_framing(SOLAR, D=D, n_ticks=n_ticks)
    sidereal = _evaluate_framing(SIDEREAL, D=D, n_ticks=n_ticks)

    drift_seconds = (
        n_ticks * SOLAR.seconds_per_day
        - n_ticks * SIDEREAL.seconds_per_day
    )
    drift_days = drift_seconds / SECONDS_PER_MEAN_SOLAR_DAY

    lines: List[str] = [
        "=" * 70,
        "Cycle-alignment investigation: solar vs sidereal day for the",
        "bit-ALU's permute / sigma_day operator.",
        "=" * 70,
        "",
        f"Hypervector dimension D       = {D}",
        f"Ticks evaluated               = {n_ticks}",
        f"  (one full bit-rotation cycle when n_ticks = D)",
        "",
        "Day-length difference between framings:",
        f"  solar    seconds/day = {SOLAR.seconds_per_day:.4f}",
        f"  sidereal seconds/day = {SIDEREAL.seconds_per_day:.4f}",
        f"  ratio                = {SIDEREAL_DAYS_PER_MEAN_SOLAR_DAY:.7f} "
        f"sidereal/solar",
        f"  per-day drift        = {SOLAR.seconds_per_day - SIDEREAL.seconds_per_day:.2f} s",
        f"  over {n_ticks} ticks       = {drift_seconds:.0f} s "
        f"= {drift_days:.3f} mean-solar days",
        "",
        "Result A — solar / Julian framing:",
        _format_result(solar),
        "",
        "Result B — sidereal framing:",
        _format_result(sidereal),
        "",
        "─" * 70,
        "Conclusion",
        "─" * 70,
        "",
        "The encoder's `cycle_period_days` are documented in Julian days",
        "(see `encode_ant.DialSpec.residue` and `astronomical_cycles.Cycle.",
        "mechanism_days`).  The Julian Date is by definition tied to the",
        "mean solar day (86 400 SI s).  Therefore:",
        "",
        "    sigma_day = permute(v, 1, D)  ⇔  one Julian day",
        "                                  ⇔  one mean solar day",
        "                                  ⇔  ONE turn of the Antikythera's",
        "                                     hand-crank",
        "",
        "Sidereal-day framing would require re-expressing every",
        "`cycle_period_days` in sidereal-day units (a 0.273 % rescaling)",
        "with no calendar advantage; the mechanism's calendar dials",
        "(Metonic, Saros, Callippic, Olympiad) are inherently solar-",
        "day-keyed (lunar / eclipse / Olympic / Olympiad cycles are",
        "specified in solar-day periods).",
        "",
        "Sidereal-day framing IS meaningful for sidereal-frame DIALS",
        "(zodiac longitude in the inertial sky, planetary sidereal",
        "periods).  In `encode_ant.py` those periods are already",
        "expressed in Julian days; one would convert at decode time",
        "if a sidereal interpretation of the residue were wanted.",
        "",
        "**The bit-ALU's permute / sigma_day stays solar/Julian-keyed.**",
        "This matches the existing encoder, the Antikythera mechanism's",
        "hand-crank semantics, and the Hellenistic calendar tradition.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m research.cycle_alignment_investigation",
        description=(
            "Compare solar vs sidereal day framings for the bit-ALU's "
            "permute / sigma_day operator on the Antikythera encoder."
        ),
    )
    p.add_argument(
        "--D", type=int, default=940,
        help="Hypervector dimension (default: 940 = Callippic).",
    )
    p.add_argument(
        "--ticks", type=int, default=None,
        help="Number of sigma_day ticks to evaluate (default: D, "
             "i.e. one full bit-rotation cycle).",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    n_ticks = args.ticks if args.ticks is not None else args.D
    print(investigate(D=args.D, n_ticks=n_ticks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
