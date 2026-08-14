"""``srmech.music`` — the acoustic domain slice.

The ADR-0010 ``srmech.music.*`` domain namespace, opened at v0.9.0rc362. It
holds the acoustic/music surface: partial spectra, the exactness TIER TAG over
them, and a commensurability verdict that can return **"inharmonic"**.

⚠️ **"harmonic" in THIS ``__init__``'s public surface is the ACOUSTIC word** —
partials, overtones, frequency ratios. The OTHER sense, **chirality order**, now
also lives in this package: ADR-0010 (v0.9.0rc366) relocated ``harmonics.py``
here from ``srmech.amsc`` (a slice moves the parent, keeps the leaf), so
``srmech.music.harmonics.classify_harmonic`` — signature
``(class_letter: str) -> int``, indexing the A–N ``HARMONIC_PARTITION`` — sits as
a SIBLING submodule. The two senses still never meet: ``harmonics`` is a distinct
module, it is deliberately NOT imported or re-exported here, and every name in
THIS ``__init__`` is acoustic, so nothing below can be read as the chirality one.
(`` set(__all__) & set(harmonics.__all__) == set() `` is pinned by
``test_music_commensurability_rc362``.)

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

``just_limit`` / ``comma_of_chain`` / ``tempers_out`` / ``interval_vector`` /
``normal_order`` / ``prime_form``
    **The RELATIONAL lane (rc424).** Everything above answers *what does this
    object sound like?*; these six answer *how do two pitches stand to one
    another?*. They read no spectrum and carry no partials. Full statement in
    :mod:`srmech.music.relations` — including why the frequency lane (ℚ⁺ under
    multiplication, where a chain of fifths provably CANNOT close) and the
    modular lane (ℤ/12 under addition, where it always does) disagree, and why
    the exact residue between them IS a comma.

⚠️ **A THIRD HOMOGRAPH, now disarmed.** Besides the two senses of "harmonic"
above, "MUSIC" is also an ACRONYM — **MU**ltiple **SI**gnal **C**lassification,
the subspace direction-of-arrival estimator — which has nothing to do with this
package. Through rc423 it shipped as ``srmech.signal_processing.closed_form_ops
.music``, one dotted path away from here. rc424 renamed it
``srmech.signal_processing.music_doa`` and registered it, so the name now
carries its own disambiguation instead of relying on a reader noticing which
package it lives in.

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
from .relations import (
    comma_of_chain,
    interval_vector,
    just_limit,
    normal_order,
    prime_form,
    tempers_out,
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
    # rc424 (`#T1113`) — the RELATIONAL lane (see the module docstring above).
    "just_limit",
    "comma_of_chain",
    "tempers_out",
    "interval_vector",
    "normal_order",
    "prime_form",
]

# ``TIER_RATIONAL`` / ``TIER_ALGEBRAIC`` / ``TIER_OPEN`` are importable module
# attributes but are deliberately NOT in ``__all__``: they are ints, and the
# Rosetta ledger walk enumerates ``__all__`` expecting callables.
