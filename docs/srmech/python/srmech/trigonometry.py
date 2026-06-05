"""srmech.trigonometry — the trig subset of :mod:`srmech.asymptotic_calculus`.

A convenience re-export of the substrate-native (Class-N rational) trig
primitives. Each returns an **exact** ``(numerator, denominator)`` rational
from a Taylor-series truncation, not a float — the continuous number line is
a projection (``[[feedback_continuous_number_line_pedagogical_obstacle]]``);
"continuous" trig is computed as a Class-N rational cascade.

Implementations live in :mod:`srmech.amsc.rational`; see
:mod:`srmech.calculus` (formerly ``srmech.asymptotic_calculus``, still a
back-compat alias) for the full continuous-calculus surface (transcendentals
+ exp/roots + rational arithmetic + Class-N anchors + π).

Two layers:

- the exact ``*_series_truncate`` Taylor cascades (return ``(num, den)``);
- the **float-projection** ``cos`` / ``sin`` / ``tan`` / ``atan`` / ``atan2``
  wrappers — substrate-native, drop-in replacements for ``math``/``numpy``
  trig. They range-reduce against the π-cascade and project the exact
  rational result to float (no ``math.cos`` / ``np.cos`` in the call graph).

>>> from srmech import trigonometry as trig
>>> trig.sin_series_truncate(1, 2, 8)   # sin(1/2) as an exact rational tuple
(...)
>>> trig.cos(0.5)                        # float projection; matches math.cos
0.8775825618903728
"""
from __future__ import annotations

from srmech.amsc.rational import (
    sin_series_truncate,
    cos_series_truncate,
    atan_series_truncate,
    cos,
    sin,
    tan,
    atan,
    atan2,
)

__all__ = [
    "sin_series_truncate",
    "cos_series_truncate",
    "atan_series_truncate",
    "cos",
    "sin",
    "tan",
    "atan",
    "atan2",
]
