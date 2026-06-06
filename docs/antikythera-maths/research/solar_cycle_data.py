"""Solar activity cycle — hand-coded data module (v0.30.0rc3 ship).

The Sun's **magnetic activity cycle**: the ~11-year Schwabe sunspot
cycle, the 22-year Hale magnetic-polarity cycle, the ~88-year
Gleissberg amplitude modulation, and the butterfly-diagram equatorward
drift (Spörer's law). The third solar-dynamics catalogue on the
v0.30.0 line (after the Sun Dynamical Spectrum's p-modes and the
differential-rotation profile).

The closure: **the Hale cycle is exactly two Schwabe cycles.** The
Sun's global magnetic polarity *reverses* at each sunspot maximum and
returns to its original sense only after two activity cycles, so the
full magnetic period is `2 × 11 ≈ 22` years. The doubling is a
polarity **sign-flip** — the Class-K pin-slot sign of
``[[user_stance_epicycle_via_gear_plus_pin]]`` made literal in a
physical magnetic cycle (the same sign-flip-doubles-the-period
structure as an epicycle).

Sources
-------
* **Schwabe 1844** *Astron. Nachr.* 21:233. The discovery of the
  ~10-year (now ~11-year) sunspot periodicity. Cited for: the
  Schwabe period.
* **Hale & Nicholson 1925** *ApJ* 62:270. DOI 10.1086/142933. The
  law of sunspot polarity — magnetic polarity reverses each cycle, so
  the magnetic period is 22 years (Hale's law). Cited for: the Hale
  period + the polarity sign-flip.
* **Hathaway 2015** *Living Rev. Solar Phys.* 12:4.
  DOI 10.1007/lrsp-2015-4. "The Solar Cycle" review — mean cycle
  length, Gleissberg modulation, butterfly diagram / Spörer's law.
  Cited for: the Gleissberg period + butterfly latitudes + cycle
  lengths.
* **Clette 2014** *Space Sci. Rev.* 186:35-103.
  DOI 10.1007/s11214-014-0074-2. "Revisiting the Sunspot Number"
  (the SILSO recalibration). Cited for: the sunspot-number record
  underpinning the cycle roster.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Cycle periods (years)
# ---------------------------------------------------------------------------

#: Schwabe sunspot-cycle period (years) — mean (Hathaway 2015).
SCHWABE_PERIOD_YEARS: float = 11.0

#: Hale magnetic-polarity-cycle period (years) = 2 x Schwabe (Hale's law).
HALE_PERIOD_YEARS: float = 22.0

#: The integer Hale:Schwabe commensurability — the polarity-flip doubling.
HALE_TO_SCHWABE_RATIO: int = 2

#: Gleissberg amplitude-modulation period (years) — ~7-8 Schwabe cycles.
GLEISSBERG_PERIOD_YEARS: float = 88.0


# ---------------------------------------------------------------------------
# Butterfly diagram (Spörer's law) — sunspot emergence latitude
# ---------------------------------------------------------------------------

#: Mean sunspot emergence latitude at cycle START (deg) — high-latitude.
BUTTERFLY_START_LATITUDE_DEG: float = 30.0

#: Mean sunspot emergence latitude at cycle END (deg) — near-equatorial.
BUTTERFLY_END_LATITUDE_DEG: float = 8.0


# ---------------------------------------------------------------------------
# Recent solar-cycle roster (SILSO minima; Hathaway 2015 / Clette 2014)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SolarCycle:
    """One numbered solar activity (Schwabe) cycle.

    ``length_years`` is None for the ongoing cycle. ``start_year`` is
    the cycle-minimum epoch (decimal year).

    Per-row provenance (``source_doi`` / ``source_published_date`` /
    ``entered_locally_at`` / ``source_version``) mirrors the
    ``solar_cycle.solar_cycle.v1`` JSON Schema so this hand-coded path
    and the AMSC literature_curated path at
    ``research/attested/solar_cycle/`` dual-author the same rows (the
    v0.30.0rc4 dual-author exercise). The DOIs + dates are
    triality-attested (haiku/sonnet/opus vs ADS/arXiv); dates are
    written at year granularity (the value all three externally
    confirmed — the panel declined to over-claim publisher month/day).
    """

    number: int
    start_year: float
    length_years: Optional[float]
    source_key: str
    source_doi: str
    source_published_date: str
    entered_locally_at: str
    notes: str
    source_version: Optional[str] = None


#: The most recent solar cycles (cycle-minimum to cycle-minimum).
SOLAR_CYCLES: List[SolarCycle] = [
    SolarCycle(
        number=23,
        start_year=1996.4,
        length_years=12.3,
        source_key="hathaway_2015",
        source_doi="10.1007/lrsp-2015-4",
        source_published_date="2015",
        entered_locally_at="2026-06-06",
        notes="Minimum 1996.4 to 2008.96; a long cycle (~12.3 yr), the deep 2008-2009 minimum.",
    ),
    SolarCycle(
        number=24,
        start_year=2008.96,
        length_years=11.0,
        source_key="hathaway_2015",
        source_doi="10.1007/lrsp-2015-4",
        source_published_date="2015",
        entered_locally_at="2026-06-06",
        notes="Minimum 2008.96 to 2019.96; a weak cycle (lowest peak amplitude in a century).",
    ),
    SolarCycle(
        number=25,
        start_year=2019.96,
        length_years=None,
        source_key="clette_2014",
        source_doi="10.1007/s11214-014-0074-2",
        source_published_date="2014",
        entered_locally_at="2026-06-06",
        notes="Ongoing from the 2019.96 minimum; SILSO-tracked sunspot number.",
    ),
]


SOURCES: Dict[str, str] = {
    "schwabe_1844": (
        "Schwabe H. (1844). Sonnenbeobachtungen im Jahre 1843. "
        "*Astron. Nachr.* 21:233. Discovery of the ~10-year (now "
        "~11-year) sunspot periodicity."
    ),
    "hale_nicholson_1925": (
        "Hale G.E., Nicholson S.B. (1925). The law of sun-spot "
        "polarity. *ApJ* 62:270. DOI: 10.1086/142933. Magnetic "
        "polarity reverses each cycle (the 22-year Hale cycle)."
    ),
    "hathaway_2015": (
        "Hathaway D.H. (2015). The Solar Cycle. *Living Rev. Solar "
        "Phys.* 12:4. DOI: 10.1007/lrsp-2015-4. Mean cycle length, "
        "Gleissberg modulation, butterfly diagram / Spörer's law."
    ),
    "clette_2014": (
        "Clette F., Svalgaard L., Vaquero J.M., Cliver E.W. (2014). "
        "Revisiting the Sunspot Number. *Space Sci. Rev.* "
        "186:35-103. DOI: 10.1007/s11214-014-0074-2. The SILSO "
        "sunspot-number recalibration."
    ),
}


def cycle_to_data_dict(cycle: SolarCycle) -> Dict[str, object]:
    """Convert a SolarCycle to the same dict shape that
    ``bridge.get_attested_dataset('solar_cycle')`` returns in each row's
    ``data`` block (key order matches the ``solar_cycle.solar_cycle.v1``
    JSON Schema). Used by the dual-author diff test to normalise the two
    paths before comparison.
    """
    return {
        "number": cycle.number,
        "start_year": cycle.start_year,
        "length_years": cycle.length_years,
        "source_key": cycle.source_key,
        "source_doi": cycle.source_doi,
        "source_published_date": cycle.source_published_date,
        "entered_locally_at": cycle.entered_locally_at,
        "source_version": cycle.source_version,
        "notes": cycle.notes,
    }


__all__ = [
    "SCHWABE_PERIOD_YEARS",
    "HALE_PERIOD_YEARS",
    "HALE_TO_SCHWABE_RATIO",
    "GLEISSBERG_PERIOD_YEARS",
    "BUTTERFLY_START_LATITUDE_DEG",
    "BUTTERFLY_END_LATITUDE_DEG",
    "SolarCycle",
    "SOLAR_CYCLES",
    "SOURCES",
    "cycle_to_data_dict",
]
