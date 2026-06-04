"""srmech.calculus — the continuous-calculus surface (Class N).

**This is the public, discoverable home of srmech's "continuous" calculus /
trig / transcendental primitives.** They are the substrate-native
*integer/rational* renderings: an exact ``(numerator, denominator)`` Taylor
truncation, or a float **projection** of that exact rational — because the
framework holds that the continuous number line is a pedagogical projection,
so a "continuous" function is computed as a Class-N rational cascade, not a
float (``[[feedback_continuous_number_line_pedagogical_obstacle]]``).

Renamed from ``srmech.asymptotic_calculus`` (which remains as a no-break
back-compat alias). The "asymptotic" qualifier was an early framing — it
singled out *this* module while the rest of the framework (trig, exp, the
eigen ops, the FFT-as-epicycle-sum) is equally substrate-native asymptotic-
rational. The insight is framework-wide now, so the module is simply
``calculus`` (see ``docs/srmech/notes/continuous_math_as_14_class_cascade.md``:
every continuous op is a composition of the 14 A–N class operations).

The implementations live in :mod:`srmech.amsc.rational` (Class N — the
rational-anchor / best-rational home, native-C-accelerated). This module is
a thin, stable re-export so the documented ``srmech.calculus.*`` import path
resolves directly; the attested catalog of worked instances ships at
``srmech/amsc/attested/asymptotic_calculus/`` (descriptor + NDJSON rows +
JSON schema).

Surface
-------
* **transcendental Taylor truncations** (each ``(num, den, num_terms) ->
  (num, den)``): :func:`exp_series_truncate`, :func:`sin_series_truncate`,
  :func:`cos_series_truncate`, :func:`log1p_series_truncate`,
  :func:`atan_series_truncate`;
* **float-projection trig** (substrate-native drop-ins for ``math``/``numpy``
  trig — range-reduce against the π-cascade, then project the exact rational
  to float): :func:`cos`, :func:`sin`, :func:`tan`, :func:`atan`,
  :func:`atan2`;
* **float-projection exp / complex-exp** (Euler ``e^(iθ)`` = Class-N trig ∘
  Class-C i-rotation): :func:`exp`, :func:`cexp`, :func:`complex_exp`;
* **float-projection roots** (integer-Newton scaled-bignum sqrt, Class-N∘K):
  :func:`sqrt`, :func:`hypot`;
* **rational arithmetic**: :func:`rational_add`, :func:`rational_mul`,
  :func:`rational_div`, :func:`rational_pow_uint`;
* **Class-N anchors**: :func:`best_rational`, :func:`continued_fraction`,
  :func:`continued_fraction_convergents`;
* **π as a cascade**: :func:`pi_cascade_digits`.

Example
-------
>>> from srmech import calculus
>>> calculus.sin_series_truncate(1, 2, 8)     # sin(1/2) as an exact rational
(...)
>>> calculus.cos(0.5)                          # float projection; matches math.cos
0.8775825618903728
>>> from srmech import trigonometry as trig    # the trig-only subset
"""
from __future__ import annotations

from srmech.amsc.rational import (
    best_rational,
    continued_fraction,
    continued_fraction_convergents,
    exp_series_truncate,
    sin_series_truncate,
    cos_series_truncate,
    log1p_series_truncate,
    atan_series_truncate,
    cos,
    sin,
    tan,
    atan,
    atan2,
    exp,
    cexp,
    complex_exp,
    sqrt,
    hypot,
    rational_add,
    rational_mul,
    rational_div,
    rational_pow_uint,
    pi_cascade_digits,
)

__all__ = [
    "exp_series_truncate",
    "sin_series_truncate",
    "cos_series_truncate",
    "log1p_series_truncate",
    "atan_series_truncate",
    "cos",
    "sin",
    "tan",
    "atan",
    "atan2",
    "exp",
    "cexp",
    "complex_exp",
    "sqrt",
    "hypot",
    "rational_add",
    "rational_mul",
    "rational_div",
    "rational_pow_uint",
    "best_rational",
    "continued_fraction",
    "continued_fraction_convergents",
    "pi_cascade_digits",
]
