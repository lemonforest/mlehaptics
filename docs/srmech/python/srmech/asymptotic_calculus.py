"""srmech.asymptotic_calculus — the continuous-calculus surface (Class N).

**This is the public, discoverable home of srmech's "continuous" calculus /
trig / transcendental primitives.** They are the substrate-native
*integer/rational* renderings — a Taylor-series truncation that returns an
exact rational ``(numerator, denominator)`` tuple — because the framework
holds that the continuous number line is a pedagogical projection, so a
"continuous" function is computed as a Class-N rational cascade, not a float
(``[[feedback_continuous_number_line_pedagogical_obstacle]]``).

The implementations live in :mod:`srmech.amsc.rational` (Class N — the
rational-anchor / best-rational home, native-C-accelerated). This module is
a thin, stable re-export so the documented ``srmech.asymptotic_calculus.*``
import path resolves directly; the attested catalog of worked instances
ships at ``srmech/amsc/attested/asymptotic_calculus/`` (descriptor + NDJSON
rows + JSON schema).

Surface
-------
* **transcendental Taylor truncations** (each ``(num, den, num_terms) ->
  (num, den)``): :func:`exp_series_truncate`, :func:`sin_series_truncate`,
  :func:`cos_series_truncate`, :func:`log1p_series_truncate`,
  :func:`atan_series_truncate`;
* **rational arithmetic**: :func:`rational_add`, :func:`rational_mul`,
  :func:`rational_div`, :func:`rational_pow_uint`;
* **Class-N anchors**: :func:`best_rational`, :func:`continued_fraction`,
  :func:`continued_fraction_convergents`;
* **π as a cascade**: :func:`pi_cascade_digits`.

Example
-------
>>> from srmech import asymptotic_calculus as ac
>>> ac.sin_series_truncate(1, 2, 8)          # sin(1/2) as an exact rational
(...)
>>> from srmech import trigonometry as trig   # the trig-only subset
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
    "rational_add",
    "rational_mul",
    "rational_div",
    "rational_pow_uint",
    "best_rational",
    "continued_fraction",
    "continued_fraction_convergents",
    "pi_cascade_digits",
]
