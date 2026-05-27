"""Foundational cross-domain cascade catalog.

The cascades that recur across **every / most** domains the framework has
examined — promoted into srmech so a named cascade is the default and a
math-library call is the exception. Per the project discipline: *being
forced to reach for a math library is the signal that a cascade is waiting
to be found.* `abs()` told us to find the Class-K pin-slot; `fractions`
told us to find the Class-N rational anchor; `math.gcd` told us to find the
Class-I cyclic gcd. This module is where those answers live.

Scale-invariance is the load-bearing reason these belong in srmech: the
A–N class operators are substrate-universal vocabulary that applies at
every discipline and every scale (per
``[[user_stance_cross_substrate_cascade_matching_as_research_method]]``).
The same **Class K pin-slot at zero** operates at bronze-gear engagement
(Antikythera), atomic shell-boundary sign-flip, biological membrane
zero-crossing, quantum tunnelling, and prime-cyclic Laplacian residue
exclusion. The same **Class N** rational anchor lands the GUE spacing-ratio
at 20/17, the Balmer line-ratios, the CMB peak spacing. This catalog is the
explicit home of that recurrence — the precursor
``docs/unsolved-maths/_cascade_helpers.py`` (imported across 20+ cascade
scripts spanning mandelbrot / chromatic / atomic / nuclear / QCD /
planetary / turbulence / black-hole / biomacromolecule / large-scale-
structure domains) graduates here.

**No new primitive class** — every callable is a *composition* of the
existing 14-class A–N primitives (the vocabulary is intact per
``[[feedback_no_privileged_primitive_classes]]``), so the module carries
**no dedicated C symbol**: Class I (``srmech.amsc.cyclic.gcd``) and Class N
(``srmech.amsc.rational.best_rational``) are the ones with C parity, and
the cascades sequence them in Python with inline Class K / Class C signed
arithmetic. **No ``abs()``** anywhere — sign is handled as the canonical
Class K pin-slot + Class C re-orientation per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

Naming: the clean public names (``pin_slot_at_zero``, ``reorient``,
``magnitude``, ``best_rational_signed``, ``cyclic_gcd``) are canonical; the
precursor's ``class_<X>_<name>`` call-site names are kept as back-compat
aliases so existing cascade scripts migrate with a pure import swap.

Canonical SSoT:
- ``[[user_stance_epicycle_via_gear_plus_pin]]`` — sign-flip IS the Class K
  pin-slot phase-boundary.
- Khinchin (1964), *Continued Fractions* — the Class N best-rational anchor
  (via ``srmech.amsc.rational.best_rational``).
- Euclid, *Elements* VII.1–2 — the Class I gcd (via ``srmech.amsc.cyclic.gcd``).
"""

from __future__ import annotations

from typing import Tuple

from srmech.amsc.cyclic import gcd as _cyclic_gcd
from srmech.amsc.rational import best_rational as _best_rational

#: Default small-denominator ceiling for ``best_rational_signed`` (the
#: Class N rational anchor). Matches the precursor cascade-helper default.
DEFAULT_MAX_DENOMINATOR = 100

#: Default fine-scaling factor turning a float magnitude into the integer
#: pair ``srmech.amsc.rational.best_rational`` consumes.
DEFAULT_FINE_SCALE = 1_000_000

#: A magnitude below this is treated as the Class K dead-band (origin).
_ZERO_BAND = 1e-12


def pin_slot_at_zero(x: float) -> Tuple[int, float]:
    """Class K pin-slot at zero: split ``x`` into (orientation, magnitude).

    The pin enters or exits the slot at the zero-crossing — sign-flip IS the
    canonical Class K phase-boundary per
    ``[[user_stance_epicycle_via_gear_plus_pin]]``. Expressing this as a
    named cascade (rather than Python ``abs()``) keeps the cascade-count
    claimed in line with the cascade-count executed.

    Args:
        x: A real value.

    Returns:
        ``(orientation, magnitude)`` where ``orientation ∈ {-1, 0, +1}`` and
        ``magnitude >= 0``. The origin maps to ``(0, 0.0)``.
    """
    if x > 0.0:
        return +1, x
    if x < 0.0:
        return -1, -x
    return 0, 0.0


def reorient(orientation: int, value):
    """Class C cascade-orientation: re-apply a captured orientation.

    Args:
        orientation: An orientation in ``{-1, 0, +1}`` (typically the first
            element of a :func:`pin_slot_at_zero` result).
        value: The magnitude (or magnitude-derived quantity) to re-sign.

    Returns:
        ``-value`` when ``orientation < 0``, otherwise ``value`` unchanged.
    """
    if orientation < 0:
        return -value
    return value


def magnitude(x: float) -> float:
    """Class K pin-slot at zero, magnitude only (orientation discarded).

    The cascade-honest replacement for Python ``abs()`` when only the
    magnitude is needed (spectral radius, eigenvalue-magnitude proxy, …).

    Args:
        x: A real value.

    Returns:
        ``|x|`` as the Class K pin-slot magnitude (always ``>= 0``).
    """
    return pin_slot_at_zero(x)[1]


def best_rational_signed(
    x: float,
    *,
    max_denominator: int = DEFAULT_MAX_DENOMINATOR,
    fine_scale: int = DEFAULT_FINE_SCALE,
) -> Tuple[int, int]:
    """Class K ∘ Class N ∘ Class C: float → signed small-denominator rational.

    The full cross-domain anchor cascade: strip the sign at the Class K
    pin-slot, find the Class N best-rational of the non-negative magnitude
    (via ``srmech.amsc.rational.best_rational``, which takes an integer pair),
    then re-apply the sign as Class C. No ``abs()``; the sign lives in the
    Class K / Class C pair end-to-end.

    Args:
        x: A real value (the irrational/float to anchor).
        max_denominator: Class N small-denominator ceiling.
        fine_scale: Integer scale turning the float magnitude into the
            ``(numerator, denominator)`` pair ``best_rational`` consumes.

    Returns:
        ``(signed_numerator, denominator)`` — the Class N convergent of
        ``x`` with the Class C sign re-applied. The origin and sub-dead-band
        magnitudes map to ``(0, 1)``.

    Raises:
        ValueError: if ``max_denominator < 1`` or ``fine_scale < 1``.
    """
    if max_denominator < 1:
        raise ValueError(
            f"cascade.best_rational_signed: max_denominator must be >= 1; "
            f"got {max_denominator}"
        )
    if fine_scale < 1:
        raise ValueError(
            f"cascade.best_rational_signed: fine_scale must be >= 1; "
            f"got {fine_scale}"
        )
    # Class K — pin-slot at zero (sign-strip).
    orientation, mag = pin_slot_at_zero(x)
    if orientation == 0 or mag < _ZERO_BAND:
        return 0, 1
    num_pos = int(round(mag * fine_scale))
    if num_pos == 0:
        return 0, 1
    # Class N — best-rational anchor of the non-negative magnitude.
    nf, df = _best_rational(num_pos, fine_scale, max_denominator)
    # Class C — re-apply the captured orientation.
    return reorient(orientation, int(nf)), int(df)


def cyclic_gcd(a: int, b: int) -> int:
    """Class I cyclic gcd. Delegates to ``srmech.amsc.cyclic.gcd``.

    A cascade-named alias so number-theoretic cascades reach for the Class I
    primitive by its cascade name rather than ``math.gcd``.
    """
    return _cyclic_gcd(a, b)


# ── Back-compat aliases (the precursor's call-site names) ──────────────
# Existing cascade scripts in docs/unsolved-maths/ import these names from
# the local _cascade_helpers; the alias lets them migrate to
# ``from srmech.amsc.cascade import ...`` without changing call sites.
class_k_pin_slot_at_zero = pin_slot_at_zero
class_c_reorient = reorient
best_rat_signed = best_rational_signed

#: Registry of the foundational cascade op names (documentary; consumers
#: iterate by name). Each maps to its A–N class composition in the docs.
CASCADE_OPS: Tuple[str, ...] = (
    "pin_slot_at_zero",        # Class K
    "reorient",                # Class C
    "magnitude",               # Class K (magnitude-only)
    "best_rational_signed",    # Class K ∘ N ∘ C
    "cyclic_gcd",              # Class I
)

__all__ = [
    "DEFAULT_MAX_DENOMINATOR",
    "DEFAULT_FINE_SCALE",
    "CASCADE_OPS",
    "pin_slot_at_zero",
    "reorient",
    "magnitude",
    "best_rational_signed",
    "cyclic_gcd",
    # back-compat aliases
    "class_k_pin_slot_at_zero",
    "class_c_reorient",
    "best_rat_signed",
]
