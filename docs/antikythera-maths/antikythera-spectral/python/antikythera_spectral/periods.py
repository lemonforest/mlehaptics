"""Historical period-relation accessor facade.

MUL.APIN (~1000 BCE) and Almagest (~150 CE) period relations with
FIRM / RECONSTRUCTED / DISPUTED confidence tags. Default consumers
should filter to FIRM + RECONSTRUCTED unless their analysis specifically
calls for the disputed interpretations.

Re-exported from ``_research.historical_periods``.
"""

from __future__ import annotations

from antikythera_spectral._research.historical_periods import (
    ALMAGEST_PERIODS,
    MULAPIN_PERIODS,
    PeriodRelation,
    filter_by_confidence,
    periods_by_source,
    prime_spectrum_of_periods,
)

__all__ = [
    "ALMAGEST_PERIODS",
    "MULAPIN_PERIODS",
    "PeriodRelation",
    "filter_by_confidence",
    "periods_by_source",
    "prime_spectrum_of_periods",
]
