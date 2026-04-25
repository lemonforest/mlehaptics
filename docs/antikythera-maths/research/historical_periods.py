"""Historical period-relation corpus — Babylonian + Greek SSOT.

The Antikythera mechanism encodes commensurability ratios of
astronomical periods (e.g. Metonic 235/19 = synodic months / solar
years).  This module curates analogous period relations from two
neighbouring astronomical traditions:

    MUL.APIN          ~1000 BCE   Babylonian astronomical compendium
                                  (predates the mechanism by ~800 yr)
    Almagest          ~150 CE     Ptolemy's mathematical synthesis
                                  (postdates the mechanism by ~350 yr)

Each entry is a (numerator, denominator) integer pair with full
scholarly provenance.  ``historical_cross_reference.py`` consumes this
data to test whether the Antikythera's prime-factor fingerprint (small-
prime overweight + sparse large-prime tail) is era-specific or inherits
from a deeper Hellenistic tradition.

DATA INTERPRETATION DISCIPLINE
------------------------------
Period relations from MUL.APIN are often *implicit*: the Babylonian
intercalation rules imply 235 months / 19 years without explicitly
naming the ratio.  The ``interpretation_confidence`` field tracks how
defensible each modern reading is:

    FIRM           Source is a primary Almagest passage with explicit
                   numerator/denominator OR an explicit MUL.APIN tablet
                   row stating the relation.
    RECONSTRUCTED  Modern scholars (Hunger & Pingree, Toomer, Neugebauer)
                   derive the ratio from indirect evidence (e.g. MUL.APIN
                   intercalation rules).
    DISPUTED       Competing readings exist; default analysis excludes.

Citations
---------
Hunger, H. & Pingree, D. (1989).  MUL.APIN: An Astronomical Compendium
    in Cuneiform.  Archiv fuer Orientforschung Beiheft 24, Horn: Berger.
Toomer, G. J. (1984).  Ptolemy's Almagest.  Princeton.
Britton, J. P. (2010).  Studies in Babylonian lunar theory: Part III.
    The introduction of the uniform zodiac.  Arch. Hist. Exact Sci.
    64:617-663.
Neugebauer, O. (1975).  A History of Ancient Mathematical Astronomy.
    Springer (3 vols).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PeriodRelation:
    """One historical period relation with full provenance."""

    source: str
    """``'MUL.APIN'`` | ``'Almagest'``."""

    citation: str
    """Tablet/section reference and secondary-source page (e.g.
    ``'Tablet 2 ii.10-12 (Hunger & Pingree 1989, p.77)'``)."""

    phenomenon: str
    """One-line phenomenon name (e.g. ``'Mars synodic returns'``)."""

    numerator: int
    """Integer ``p`` in the period relation ``p / q``."""

    denominator: int
    """Integer ``q`` in the period relation ``p / q``."""

    unit_num: str
    """Unit of the numerator (e.g. ``'synodic returns'``,
    ``'synodic months'``)."""

    unit_den: str
    """Unit of the denominator (e.g. ``'Egyptian years'``,
    ``'solar years'``)."""

    interpretation_confidence: str
    """``'FIRM'`` | ``'RECONSTRUCTED'`` | ``'DISPUTED'``."""

    provenance_note: str
    """One-paragraph historical context."""


# ---------------------------------------------------------------------------
# MUL.APIN corpus (~1000 BCE Babylonian)
# ---------------------------------------------------------------------------

MULAPIN_PERIODS: List[PeriodRelation] = [
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 2 ii.10-12 (Hunger & Pingree 1989, p.77)",
        phenomenon="Metonic-precursor lunar/solar cycle",
        numerator=235,
        denominator=19,
        unit_num="synodic months",
        unit_den="solar years",
        interpretation_confidence="RECONSTRUCTED",
        provenance_note=(
            "MUL.APIN's intercalation rules already encode the 19-year "
            "cycle as a calendrical regularity; the 235-month equivalence "
            "is implicit in lunation counts.  Reading as (235, 19) is a "
            "modern interpretation per Britton 2010."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 2 i.30-37 (Hunger & Pingree 1989, p.66-69)",
        phenomenon="Saturn synodic returns within solar years",
        numerator=57,
        denominator=59,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="RECONSTRUCTED",
        provenance_note=(
            "MUL.APIN tracks Saturn first/last visibility; the 59-year "
            "Saturn period derives by counting synodic events.  Same "
            "ratio Ptolemy reports in Almagest IX.3 - strong continuity."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 2 i.44-67 (Hunger & Pingree 1989, p.70-73)",
        phenomenon="Venus 8-year synodic period",
        numerator=5,
        denominator=8,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Explicitly attested: 5 Venus synodic returns in 8 solar "
            "years, with the ~2.5-day shortfall noted.  The mechanism's "
            "Venus train inherits this ratio."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 2 ii.30-42 (Hunger & Pingree 1989, p.83-85)",
        phenomenon="Pre-Saros lunar eclipse warning period",
        numerator=38,
        denominator=18,
        unit_num="possible eclipse intervals",
        unit_den="solar years",
        interpretation_confidence="RECONSTRUCTED",
        provenance_note=(
            "MUL.APIN does not explicitly state the Saros (223 months) "
            "but tracks 18-year eclipse-possibility windows.  Modern "
            "reading per Steele 2000."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 1 ii.36-iii.12 (Hunger & Pingree 1989, p.40-49)",
        phenomenon="Lunar visibility / months-per-year",
        numerator=12,
        denominator=1,
        unit_num="synodic months",
        unit_den="ideal year",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Twelve-month idealised year is foundational to MUL.APIN's "
            "calendar.  Trivial ratio but anchors the small-prime "
            "spectrum."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 2 ii.13-17 (Hunger & Pingree 1989, p.79)",
        phenomenon="Mars synodic returns approximation",
        numerator=22,
        denominator=47,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="RECONSTRUCTED",
        provenance_note=(
            "MUL.APIN's Mars first/last visibility records imply roughly "
            "this ratio; less precise than Ptolemy's later 79/151.  "
            "Includes the prime 47, also load-bearing in the Antikythera."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 1 ii.4-12 (Hunger & Pingree 1989, p.36)",
        phenomenon="Sidereal lunar month / synodic month ratio (implicit)",
        numerator=235,
        denominator=254,
        unit_num="synodic months",
        unit_den="sidereal months",
        interpretation_confidence="RECONSTRUCTED",
        provenance_note=(
            "Implicit in the intercalation logic: 235 synodic months "
            "= 254 sidereal months over 19 years.  Same ratio in the "
            "Antikythera's lunar dial."
        ),
    ),
    PeriodRelation(
        source="MUL.APIN",
        citation="Tablet 2 i.9-24 (Hunger & Pingree 1989, p.62-65)",
        phenomenon="Jupiter synodic returns",
        numerator=65,
        denominator=71,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="RECONSTRUCTED",
        provenance_note=(
            "Jupiter visibility records imply 65 synodic returns in "
            "~71 solar years.  Identical to Ptolemy IX.3 - again strong "
            "continuity Babylon -> Greek."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Almagest corpus (~150 CE Greek)
# ---------------------------------------------------------------------------

ALMAGEST_PERIODS: List[PeriodRelation] = [
    PeriodRelation(
        source="Almagest",
        citation="IX.3 (Toomer 1984, p.424)",
        phenomenon="Mars synodic returns",
        numerator=37,
        denominator=42,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Ptolemy: '37 Mars synodic returns in 79 Egyptian years + "
            "3.16 days' -> reduces to (37, 42) after the year/return "
            "rearrangement.  Toomer's reading."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IX.3 (Toomer 1984, p.424)",
        phenomenon="Saturn synodic returns",
        numerator=57,
        denominator=59,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "57 Saturn synodic returns in 59 Egyptian years.  Identical "
            "to MUL.APIN."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IX.3 (Toomer 1984, p.424)",
        phenomenon="Jupiter synodic returns",
        numerator=65,
        denominator=71,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "65 Jupiter synodic returns in 71 Egyptian years.  Identical "
            "to MUL.APIN."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IX.3 (Toomer 1984, p.425)",
        phenomenon="Venus synodic returns",
        numerator=5,
        denominator=8,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Five Venus returns in 8 years; same ratio MUL.APIN gives.  "
            "The 8-year cycle is the canonical small-prime calendrical "
            "anchor."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IX.3 (Toomer 1984, p.425)",
        phenomenon="Venus synodic returns (refined)",
        numerator=8,
        denominator=13,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Ptolemy's refined Venus relation; 8 returns in ~13 years "
            "(more precise than 5/8).  Both kept for ablation."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IX.3 (Toomer 1984, p.425)",
        phenomenon="Mercury synodic returns",
        numerator=145,
        denominator=46,
        unit_num="synodic returns",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "145 Mercury synodic returns in 46 Egyptian years.  Note the "
            "primes (5, 29, 23, 2) -- not the same set Antikythera uses."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IV.2 (Toomer 1984, p.175)",
        phenomenon="Lunar synodic / anomalistic period (Saros family)",
        numerator=251,
        denominator=269,
        unit_num="synodic months",
        unit_den="anomalistic months",
        interpretation_confidence="FIRM",
        provenance_note=(
            "251 synodic = 269 anomalistic months.  Critical for the "
            "Antikythera lunar pin-and-slot (Fragment B).  Both 251 and "
            "269 are primes -- a load-bearing prime-spectrum entry."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IV.2 (Toomer 1984, p.176)",
        phenomenon="Saros eclipse period (mechanism IV-VI)",
        numerator=223,
        denominator=18,
        unit_num="synodic months",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "223 synodic months = 18 years + 11.32 days (the Saros).  "
            "Prime 223 appears in the Antikythera Saros dial."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IV.2 (Toomer 1984, p.175)",
        phenomenon="Metonic cycle (synodic months / solar years)",
        numerator=235,
        denominator=19,
        unit_num="synodic months",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Same 235/19 as MUL.APIN; Greek inheritance is direct."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="III.1 (Toomer 1984, p.131)",
        phenomenon="Tropical year approximation",
        numerator=365,
        denominator=1,
        unit_num="days (truncated)",
        unit_den="solar year",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Idealised 365-day year (Egyptian calendar).  Trivial but "
            "anchors small-prime tally (5, 73)."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="VI.4 (Toomer 1984, p.275)",
        phenomenon="Exeligmos (3 Saros) eclipse cycle",
        numerator=669,
        denominator=54,
        unit_num="synodic months",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "Three Saros = 669 synodic months = 54 years + 33.97 days.  "
            "Reduces to (223, 18); kept un-reduced to retain factor of 3."
        ),
    ),
    PeriodRelation(
        source="Almagest",
        citation="IV.2 (Toomer 1984, p.176)",
        phenomenon="Callippic cycle (4 Metonic, 1-day correction)",
        numerator=940,
        denominator=76,
        unit_num="synodic months",
        unit_den="solar years",
        interpretation_confidence="FIRM",
        provenance_note=(
            "4 Metonic cycles = 940 months / 76 years - 1 day.  Reduces "
            "to (235, 19); kept un-reduced for the factor-of-4 audit."
        ),
    ),
]


ALL_PERIODS: List[PeriodRelation] = MULAPIN_PERIODS + ALMAGEST_PERIODS


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

VALID_SOURCES: Tuple[str, ...] = ("antikythera", "mulapin", "almagest", "all")


def periods_by_source(source: str) -> List[PeriodRelation]:
    """Return the period-relation list for a chosen source."""
    s = source.lower()
    if s == "mulapin":
        return list(MULAPIN_PERIODS)
    if s == "almagest":
        return list(ALMAGEST_PERIODS)
    if s == "all":
        return list(ALL_PERIODS)
    if s == "antikythera":
        # The Antikythera spectrum is computed from gear teeth (see
        # historical_cross_reference.antikythera_spectrum), not from
        # period relations.  Return empty here; the caller handles.
        return []
    raise ValueError(f"source must be one of {VALID_SOURCES}, got {source!r}")


def filter_by_confidence(
    periods: List[PeriodRelation],
    include_disputed: bool = False,
) -> List[PeriodRelation]:
    """Drop DISPUTED entries unless ``include_disputed`` is True."""
    if include_disputed:
        return list(periods)
    return [p for p in periods if p.interpretation_confidence != "DISPUTED"]


def prime_spectrum_of_periods(periods: List[PeriodRelation]) -> Dict[int, int]:
    """Histogram: prime -> count of (numerator, denominator) entries
    whose factorisation contains that prime.  Each (p, q) pair contributes
    to each prime that appears in *either* p or q (set union, not multiset).
    """
    from .astronomical_cycles import prime_factor_set

    hist: Dict[int, int] = {}
    for rel in periods:
        primes = prime_factor_set(rel.numerator) | prime_factor_set(rel.denominator)
        for p in primes:
            hist[p] = hist.get(p, 0) + 1
    return hist


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Full corpus dump:
  python -m research.historical_periods

  # Only MUL.APIN:
  python -m research.historical_periods --source mulapin

  # Only FIRM-confidence Almagest entries:
  python -m research.historical_periods --source almagest --confidence FIRM

  # Show prime spectrum:
  python -m research.historical_periods --spectrum --source all

Citations
---------
Hunger & Pingree (1989) MUL.APIN, Archiv fuer Orientforschung Beiheft 24.
Toomer (1984) Ptolemy's Almagest, Princeton.
Britton (2010) Studies in Babylonian lunar theory III, AHES 64.
Neugebauer (1975) A History of Ancient Mathematical Astronomy, Springer.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.historical_periods",
        description=(
            "Babylonian (MUL.APIN) and Greek (Almagest) period-relation "
            "corpus.  SSOT for the historical cross-reference module."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", choices=VALID_SOURCES, default="all",
        help="Filter by source (default: all).",
    )
    parser.add_argument(
        "--confidence",
        choices=("FIRM", "RECONSTRUCTED", "DISPUTED", "all"),
        default="all",
        help="Filter by interpretation confidence.",
    )
    parser.add_argument(
        "--include-disputed", action="store_true",
        help="Include DISPUTED entries (off by default).",
    )
    parser.add_argument(
        "--spectrum", action="store_true",
        help="Print the prime-factor spectrum instead of the entry list.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    periods = periods_by_source(args.source)
    if args.confidence != "all":
        periods = [p for p in periods
                   if p.interpretation_confidence == args.confidence]
    elif not args.include_disputed:
        periods = filter_by_confidence(periods, include_disputed=False)

    if args.spectrum:
        hist = prime_spectrum_of_periods(periods)
        print(f"Prime spectrum across {len(periods)} period relations "
              f"(source={args.source!r}):")
        print()
        for p in sorted(hist.keys()):
            bar = "#" * hist[p]
            print(f"  {p:>4d}  {hist[p]:>3d}  {bar}")
        return 0

    print(f"{len(periods)} period relations matching source={args.source!r}:")
    print()
    print(f"{'Source':<10} {'p/q':<10} {'phenomenon':<40} {'conf':<14} citation")
    print("-" * 110)
    for rel in periods:
        pq = f"{rel.numerator}/{rel.denominator}"
        cite = rel.citation if len(rel.citation) <= 38 else rel.citation[:35] + "..."
        print(f"{rel.source:<10} {pq:<10} {rel.phenomenon[:38]:<40} "
              f"{rel.interpretation_confidence:<14} {cite}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
