"""
Shared cascade helpers for the unsolved-maths/ catalogs.

ARCHITECTURAL ROLE (user direction 2026-05-23):

  > this catalog of cascade operations that replace math modules should be a
  > catalog that follows srmech, just like asymptotic calculus and trigonometry,
  > as well. I think we need to make it explicit in the srmech code base that
  > this is foundational cascade operations for a whole host of things because
  > of scale invariance that does apply to every single discipline.

This file is the PRECURSOR of a srmech foundational-cascade-operations
catalog -- a peer to:
  - srmech.asymptotic_calculus  (Spike #234)
  - srmech.trigonometry         (per [[user_stance_loe_asymptotes_are_ring_valued]])

(Both paths verified live by import 2026-09-01. They were written here as
srmech.amsc.cosmos.* -- a spelling ADR-0010 retired; `import srmech.amsc.cosmos`
raises ModuleNotFoundError today.)

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

EVERY helper defined below has now graduated into srmech, and each was measured
value-identical to its local twin on 2026-09-01 (rc463):

  class_k_pin_slot_at_zero -> srmech.cascade.atoms.pin_slot_at_zero
  class_c_reorient         -> srmech.cascade.atoms.reorient
  magnitude                -> srmech.cascade.atoms.magnitude
  best_rat_signed          -> srmech.cascade.composites.best_rational_signed
  cyclic_gcd               -> srmech.cascade.composites.cyclic_gcd

The local definitions are kept because the 61 cascade scripts that import them
call them by these names. The swap is drop-in on all but ONE signature:
srmech's `reorient(value, *, orientation)` is keyword-only and takes its
arguments in the opposite order to the local `class_c_reorient(orientation,
value)`. (This paragraph named a future `srmech.amsc.cascade.pin_slot_at_zero`
until rc463 -- a path ADR-0010 retired, describing a graduation that had
already happened.) Same for the catalog-config-driven runner:

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

from srmech.math.cyclic import gcd as _srmech_gcd
from srmech.math.rational import best_rational as _srmech_best_rational


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

    srmech.math.rational.best_rational requires (num: int >= 0, denom: int > 0,
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
    """Class I cyclic GCD. Delegates to srmech.math.cyclic.gcd."""
    return _srmech_gcd(a, b)


# ---------- Promotion ledger: what has LANDED in srmech, and what has not ----------
#
# MEASURED 2026-09-01 on this tree (srmech rc463, `#T1188`) by IMPORTING each
# path, not by reading prose. This block previously listed seven "candidate
# promotions" as uniformly pending and spelled every one of them under
# srmech.amsc.* -- a namespace ADR-0010 retired. All three module paths it
# named are gone: `srmech.amsc.trig`, `srmech.amsc.transcendentals` and
# `srmech.amsc.cascade` each raise ModuleNotFoundError today. Five of the seven
# candidates had in fact shipped, under different names, in different modules,
# with different signatures.
#
# The Python math-module operations still reached for by the 61 cascade scripts
# under docs/unsolved-maths/ that import this file (measured file counts):
#
#   math.cos(2*pi/n), math.sin(2*pi/n), math.pi  -- 1 script
#                       (hilbert/hilbert_12_kronecker_jugendtraum)
#   math.log(p)                                  -- 9 scripts
#   math.sqrt(N)                                 -- 3 scripts
#   math.ceil(x)                                 -- 1 script
#   numpy.mean(xs) / numpy.std(xs)               -- 8 scripts
#
# LANDED -- five of the seven, with their REAL homes and REAL signatures.
# The candidate NUMBERS below are the original seven's index and are kept
# stable, so candidates 1 and 2 share one entry: rc468 (`#T1188`) merged
# them into a single shipped op, which is why five landed candidates are
# now four rows.
#
#   1 + 2. srmech.math.qalg.cos_sin_2pi_k_over_n(n: int, k: int = 1)
#           -> tuple[Qalg, Qalg]                            [rc463 / rc468]
#      EXACT (cos(2*pi*k/n), sin(2*pi*k/n)), BOTH as elements of the ONE field
#      Q(zeta_N) with N = lcm(n, 4). Class J (the cyclotomic divisor lattice
#      and the lcm) o Class I (k reduced in Z_n first) o Class N (the exact
#      rational coordinates) o Class C (the zeta rotation). This block's
#      original entry promised `(n, max_d) -> (int, int)`, "exact for
#      constructible n, Class N rational approximation otherwise". BOTH halves
#      of that were wrong: the shipped op takes NO max_d and never
#      approximates, because cos and sin of a rational turn are algebraic
#      numbers for EVERY n -- there is no non-constructible fallback case to
#      have. Bounded 1 <= n <= 256 (a measured field-degree cap, not a
#      constructibility condition).
#
#      ⚠️ rc463 shipped this as TWO ops, cos_2pi_over_n over Phi_n and
#      sin_2pi_over_n over Phi_lcm(n,4), and rc468 (`#T1188`) REMOVED both:
#      with k defaulting to 1 the general constructor IS the two, so keeping
#      them was a duplicate op. They were also the worse spelling -- the
#      cosine and the sine answered in DIFFERENT fields whenever 4 does not
#      divide n, so Qalg correctly refused to add a cosine to its own sine.
#      There is no alias: cos_2pi_over_n(n) is cos_sin_2pi_k_over_n(n)[0].
#
#   3. srmech.math.rational.log(x, *, precision=None) -> Q
#      Exact-Q natural log. The old entry named a dead
#      `srmech.amsc.transcendentals.log_class_n(num, denom, max_d)`.
#
#   4. srmech.math.rational.sqrt(x, *, precision=None) -> Q
#      Exact-Q square root. Old entry: dead `...transcendentals.sqrt_class_n`.
#
#   5. srmech.cascade.composites.compensated_sum(values) -> float
#      Class M Kahan-Babuska-Neumaier compensated summation -- the reduce-sum
#      role the old `srmech.amsc.cascade.reduce_sum` entry described.
#
# DISSOLVED -- not pending, and deliberately never to be minted:
#
#   6. reduce_count(xs) -> int.  DISSOLVED per dissolve-before-promote
#      ([[feedback_no_privileged_primitive_classes]]). A finite count IS
#      `len(xs)`: it reads a length the object already carries and executes no
#      cascade step whatsoever. Minting it would add an op with zero cascade
#      content and make the vocabulary read one op wider than the algebra
#      actually is -- the precise failure the dissolve-first discipline exists
#      to prevent. So numpy.mean(xs) is `compensated_sum(xs) / len(xs)`: one
#      shipped op and a builtin, not two ops.
#
# STILL PENDING -- one of the seven:
#
#   7. A ceiling at the integer boundary. No public op ships it, but the exact
#      carrier already answers the question: srmech.math.q.Q.__ceil__ returns an
#      int from an exact Q with no float and no math module (Q(7,2) -> 4,
#      Q(-7,2) -> -3). What is missing is only a NAMED Class-K op over it.
#
# What THIS FILE does, measured: nothing transcendental at all. There are zero
# `math.*` and zero `numpy.*` calls anywhere in this module outside these
# comments, and zero `abs()` calls -- the three mentions of abs() above are
# prose saying not to use it. The paragraph that used to close this block
# described "the cascade scripts continue to use math.cos / sin / log / sqrt /
# numpy.mean as TRANSCENDENTAL SHORTCUTS ... until these land in srmech" as the
# standing practice. They have landed. For cos, sin, log and sqrt an EXACT
# srmech answer now exists, so a transcendental shortcut is no longer the
# honest first move for any of them; where a consumer script still reaches for
# math.* (counts above) that is a MIGRATION BACKLOG, not a sanctioned pattern.
# The cascade-honesty contract still binds the un-migrated remainder: a math.*
# call MUST be followed by Class N best-rational in the same cascade-step, so
# the record is finite-cyclical-algebra-honest end-to-end even where the
# intermediate float is irrational. The point is that for four of these
# operations you can now skip the float entirely.
