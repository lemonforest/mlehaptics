"""srmech.trigonometry — the trig subset of :mod:`srmech.asymptotic_calculus`.

A convenience re-export of the substrate-native (Class-N rational) trig
primitives. Each returns an **exact** ``(numerator, denominator)`` rational
from a Taylor-series truncation, not a float — the continuous number line is
a projection (``[[feedback_continuous_number_line_pedagogical_obstacle]]``);
"continuous" trig is computed as a Class-N rational cascade.

Implementations live in :mod:`srmech.amsc.rational`; see
:mod:`srmech.asymptotic_calculus` for the full continuous-calculus surface
(transcendentals + rational arithmetic + Class-N anchors + π).

>>> from srmech import trigonometry as trig
>>> trig.sin_series_truncate(1, 2, 8)   # sin(1/2) as an exact rational tuple
(...)
"""
from __future__ import annotations

from srmech.amsc.rational import (
    sin_series_truncate,
    cos_series_truncate,
    atan_series_truncate,
)

__all__ = [
    "sin_series_truncate",
    "cos_series_truncate",
    "atan_series_truncate",
]
