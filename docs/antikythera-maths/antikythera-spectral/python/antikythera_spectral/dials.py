"""Dial / cycle accessor facade.

The mechanism's dials and the astronomical commensurability ratios they
encode. Re-exported from ``_research.astronomical_cycles``.
"""

from __future__ import annotations

from antikythera_spectral._research.astronomical_cycles import (
    CYCLES,
    Cycle,
    prime_factor_set,
    prime_factors,
    shared_primes_among_planetary,
)
from antikythera_spectral._research.encode_ant import (
    DIAL_SPECS,
    DialSpec,
)

__all__ = [
    # Cycle data
    "CYCLES",
    "Cycle",
    # Dial specs (the per-dial Cycle + supported-D matrix)
    "DIAL_SPECS",
    "DialSpec",
    # Prime-factor helpers
    "prime_factors",
    "prime_factor_set",
    "shared_primes_among_planetary",
]
