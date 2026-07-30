"""``srmech.music`` — the acoustic domain slice.

The ADR-0010 ``srmech.music.*`` domain namespace, opened at v0.9.0rc362. It
holds the acoustic/music surface: partial spectra, the exactness TIER TAG over
them, and a commensurability verdict that can return **"inharmonic"**.

⚠️ **"harmonic" in this package is the ACOUSTIC word.** Everywhere else in the
tree it means **chirality order** — ``harmonics.classify_harmonic`` has the
signature ``(class_letter: str) -> int`` and indexes the A–N partition. The two
senses never meet; nothing here imports, extends or shadows that surface, and
every name in this package is chosen so it cannot be read as the chirality one.

WHAT IS HERE
============
``spectrum_tier``
    The honesty layer. Tier 1 (``Q``, exact rational) / Tier 2 (``Qalg``, exact
    algebraic irrational) / Tier 3 (no exact carrier — DECLARED, never
    inferred).

``commensurability_verdict``
    The core capability: ``"harmonic"`` / ``"inharmonic"`` / ``"open"``, decided
    by RATIONAL RANK (ℚ-membership inside ℚ[x]/(m)) rather than by any period.
    Class-I gcd/lcm structurally cannot return "inharmonic" — a finite set of
    rational ratios always has an lcm — and Class-N ``best_rational`` is worse
    than silent, because it CONVERTS an inharmonic spectrum into a harmonic one.

``common_period``
    The guard that makes that conversion unreachable: a period comes back only
    for a spectrum that earned the ``"harmonic"`` verdict; otherwise it raises.

``bell_partials`` / ``equal_temperament_partials`` / ``stiff_string_partials``
/ ``membrane_partials``
    Four closed-form spectra spanning all three tiers, each DECLARING its own.

``bessel_j_fixed`` / ``bessel_zero_fixed``
    The Class-N exact-rational Bessel kernel the membrane needs, promoted from
    the Spike #40 exact primitives.

WHY IT IS NOT UNDER ``srmech.amsc``
===================================
ADR-0010 is actively DRAINING that namespace back to attestation, and the drain
is enforced by a down-only per-artifact ratchet. ``srmech.music`` is the domain
home that ADR names for this surface, so the slice lands where it belongs rather
than adding to a population being reduced.
"""

from __future__ import annotations

from ._bessel import bessel_j_fixed, bessel_zero_fixed
from ._instruments import (
    bell_partials,
    equal_temperament_partials,
    membrane_partials,
    stiff_string_partials,
)
from ._spectra import (
    TIER_ALGEBRAIC,
    TIER_OPEN,
    TIER_RATIONAL,
    commensurability_verdict,
    common_period,
    spectrum_tier,
)

__all__ = [
    "spectrum_tier",
    "commensurability_verdict",
    "common_period",
    "bell_partials",
    "equal_temperament_partials",
    "stiff_string_partials",
    "membrane_partials",
    "bessel_j_fixed",
    "bessel_zero_fixed",
]

# ``TIER_RATIONAL`` / ``TIER_ALGEBRAIC`` / ``TIER_OPEN`` are importable module
# attributes but are deliberately NOT in ``__all__``: they are ints, and the
# Rosetta ledger walk enumerates ``__all__`` expecting callables.
