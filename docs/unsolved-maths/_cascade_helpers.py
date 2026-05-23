"""
Shared cascade helpers for the unsolved-maths/ catalogs.

ARCHITECTURAL ROLE (user direction 2026-05-23):

  > this catalog of cascade operations that replace math modules should be a
  > catalog that follows srmech, just like asymptotic calculus and trigonometry,
  > as well. I think we need to make it explicit in the srmech code base that
  > this is foundational cascade operations for a whole host of things because
  > of scale invariance that does apply to every single discipline.

This file is the PRECURSOR of a future srmech foundational-cascade-operations
catalog -- a peer to:
  - srmech.amsc.cosmos.asymptotic_calculus  (Spike #234)
  - srmech.amsc.cosmos.trigonometry         (planned per [[user_stance_loe_asymptotes_are_ring_valued]])

The discipline that justifies this catalog: per the framework's scale-invariance
canon, the A-N class operators are substrate-universal vocabulary that applies
at every discipline + every scale per [[user_stance_cross_substrate_cascade_matching_as_research_method]].
The same Class K pin-slot at zero operates at:
  - bronze gear engagement (Antikythera)
  - atomic shell-boundary (electron sign-flip across nucleus)
  - biological membrane potential zero-crossing (action potential)
  - quantum tunneling sign-flip across barriers
  - prime-cyclic Laplacian residue exclusion (twin-prime r=23 mod 30)
  - GUE Wigner-Dyson spacing-ratio at 20/17

Same Class C cascade-orientation, same Class N rational approximation, same
Class I cyclic modulus -- across every substrate-class-instance the framework
has examined. That's the load-bearing reason these primitives belong in srmech
as foundational catalog: scale-invariance IS the math, not Python's math module.

DISCIPLINE per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:

  > all operations should be reduced to finite cyclical algebra, even when some
  > python math module does it differently. these are actually items that need
  > to live in srmech eventually, and fit inside catalog configuration text files.

When each helper here graduates into srmech (e.g. as
srmech.amsc.cascade.pin_slot_at_zero), the local import in cascade scripts
becomes a srmech import without changing call sites. Same for the future
catalog-config-driven runner:

    [cascade]
    classes = ["A", "L", "K", "N", "M"]
    operations = [
      { class = "K", op = "pin_slot_at_zero", args = {} },
      { class = "N", op = "best_rational",   args = { fine = 1000000, max_d = 20 } },
      { class = "C", op = "reorient",        args = {} },
      ...
    ]

Naming convention:
  - class_<X>_<name> : the named A-N cascade operation
  - <name>          : the convenience wrapper (composed cascade) callers reach for

All math comes from srmech primitives where one exists. Where srmech does not
yet expose the primitive, we explicitly note the ALU dependency that would be
removed by the future srmech promotion.
"""

from typing import Tuple

from srmech.amsc.cyclic import gcd as _srmech_gcd
from srmech.amsc.rational import best_rational as _srmech_best_rational


# ---------- Class K pin-slot at zero (sign-strip) ----------

def class_k_pin_slot_at_zero(x: float) -> Tuple[int, float]:
    """Class K pin-slot operation at zero. Returns (orientation, magnitude).

    Per [[user_stance_epicycle_via_gear_plus_pin]]: sign-flip IS the canonical
    Class K pin-slot phase-boundary operation -- the pin enters or exits the
    slot at the zero-crossing. Expressing this as a named cascade rather than
    Python abs() keeps the cascade-count claimed in line with the cascade-count
    actually executed.

    orientation ∈ {-1, 0, +1}; magnitude >= 0 always.
    """
    if x > 0.0:
        return +1, x
    if x < 0.0:
        return -1, -x
    return 0, 0.0


# ---------- Class C cascade-orientation reapply ----------

def class_c_reorient(orientation: int, value):
    """Class C cascade-orientation: re-apply the captured orientation."""
    if orientation < 0:
        return -value
    return value


# ---------- Composed: Class K + Class N + Class C (float -> rational) ----------

def best_rat_signed(x: float, max_d: int = 100, fine: int = 1_000_000) -> Tuple[int, int]:
    """Class K pin-slot at zero -> Class N best-rational -> Class C reorient.

    srmech.amsc.rational.best_rational requires (num: int >= 0, denom: int > 0,
    max_denominator: int) and returns the integer rational pair. This wrapper
    handles the float -> integer-pair conversion via fine-scaling, and keeps the
    sign external as a Class K + Class C composition (not Python abs()).

    Returns (signed_numerator, denominator).
    """
    orientation, magnitude = class_k_pin_slot_at_zero(x)
    if orientation == 0 or magnitude < 1e-12:
        return 0, 1
    num_pos = int(round(magnitude * fine))
    if num_pos == 0:
        return 0, 1
    nf, df = _srmech_best_rational(num_pos, fine, max_d)
    return class_c_reorient(orientation, int(nf)), int(df)


# ---------- Class K pin-slot at zero (magnitude-only convenience) ----------

def magnitude(x: float) -> float:
    """Class K pin-slot at zero, magnitude only (discards orientation).

    Use this in place of Python abs() when only the magnitude is needed
    (e.g. spectral-radius computation, eigenvalue-magnitude proxy).
    """
    return class_k_pin_slot_at_zero(x)[1]


# ---------- Class I cyclic GCD (delegates to srmech) ----------

def cyclic_gcd(a: int, b: int) -> int:
    """Class I cyclic GCD. Delegates to srmech.amsc.cyclic.gcd."""
    return _srmech_gcd(a, b)


# ---------- Notes on transcendental shortcuts that DO NOT yet have srmech replacements ----------
#
# The following Python math-module operations are used in cascade scripts:
#
#   math.cos(2*pi/n), math.sin(2*pi/n)
#   math.log(p), math.sqrt(N)
#   math.pi, math.ceil(x)
#   numpy.mean(xs), numpy.std(xs)
#
# Per the cascade-honesty discipline, these are CANDIDATE PROMOTIONS to srmech:
#
#   1. srmech.amsc.trig.cos_2pi_over_n(n: int, max_d: int) -> (int, int)
#      Exact for constructible n (cyclotomic polynomial root); Class N rational
#      approximation otherwise.
#
#   2. srmech.amsc.trig.sin_2pi_over_n(n: int, max_d: int) -> (int, int)
#      Companion to cos_2pi_over_n.
#
#   3. srmech.amsc.transcendentals.log_class_n(num: int, denom: int, max_d: int)
#      Class N best-rational approximation of log(num/denom).
#
#   4. srmech.amsc.transcendentals.sqrt_class_n(num: int, denom: int, max_d: int)
#      Class N best-rational approximation of sqrt(num/denom).
#
#   5. srmech.amsc.cascade.reduce_sum(xs: List[T]) -> T
#      Finite-sum reduction (replaces numpy.mean's sum part).
#
#   6. srmech.amsc.cascade.reduce_count(xs: List[T]) -> int
#      Finite count.
#
#   7. srmech.amsc.cascade.ceil_at_integer_boundary(x: float) -> int
#      Class K pin-slot at integer-boundary (replaces math.ceil).
#
# Until these land in srmech, the cascade scripts continue to use math.cos / sin
# / log / sqrt / numpy.mean as TRANSCENDENTAL SHORTCUTS, followed immediately by
# Class N best_rat_signed() to convert the irrational into its small-denominator
# rational anchor. The cascade-honesty contract: a math.cos / math.sin / math.log
# call MUST be followed by Class N best-rational in the same cascade-step, so
# that the cascade is finite-cyclical-algebra-honest end-to-end at the record
# level even if the intermediate floating-point value is irrational.
