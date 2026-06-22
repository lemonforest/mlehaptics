"""srmech.asymptotic_calculus — back-compat alias for :mod:`srmech.calculus`.

The continuous-calculus surface was renamed ``asymptotic_calculus`` →
``calculus`` (the "asymptotic" qualifier singled out this one module while the
whole framework is equally substrate-native asymptotic-rational; the insight
is framework-wide now — see
``docs/srmech/notes/continuous_math_as_14_class_cascade.md``). This module
remains a **no-break re-export** so existing ``srmech.asymptotic_calculus.*``
imports keep working; new code should prefer :mod:`srmech.calculus`.
"""
from __future__ import annotations

from srmech.calculus import (  # noqa: F401  (re-exported for back-compat)
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
    log,
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
from srmech.calculus import __all__ as __all__
