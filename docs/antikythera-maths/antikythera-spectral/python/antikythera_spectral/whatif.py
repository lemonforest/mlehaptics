"""What-if encoder — re-encode a dial with arbitrary p/q gear ratio.

Bounded-input gates (per ADR 0008):

- ``p, q ∈ [1, 500]`` (Greek bronze cuttability ceiling, A-H1)
- ``gcd(p, q) == 1`` (already-reduced ratio)
- ``dial`` ∈ DIAL_SPECS allowlist
"""

from __future__ import annotations

import math
from typing import Any, Dict

import numpy as np

from antikythera_spectral._research.encode_ant import DIAL_SPECS, REFERENCE_JD


_DIAL_BY_NAME = {s.name: s for s in DIAL_SPECS}

MAX_TEETH = 500
"""Max p or q in any what-if ratio. Greek workshop ceiling per A-H1."""


def encode_with_custom_train(jd_tdb: float, dial: str, p: int, q: int) -> Dict[str, Any]:
    """Encode the residue/angle a custom p/q ratio would emit at jd_tdb.

    Returns
    -------
    dict
        ``{
            "dial": str,
            "p": int, "q": int,
            "ratio": float,
            "implied_period_days": float,
            "residue": int,
            "angle_deg": float,
        }``

    Raises ``ValueError`` if the input bounds are violated; bridge layer
    catches and converts to ``ok: false``.
    """
    if dial not in _DIAL_BY_NAME:
        raise ValueError(f"unknown dial {dial!r}")
    if not isinstance(p, int) or not isinstance(q, int):
        raise ValueError("p and q must be integers")
    if not (1 <= p <= MAX_TEETH):
        raise ValueError(f"p must be in 1..{MAX_TEETH}, got {p}")
    if not (1 <= q <= MAX_TEETH):
        raise ValueError(f"q must be in 1..{MAX_TEETH}, got {q}")
    if math.gcd(p, q) != 1:
        raise ValueError(f"p/q must be reduced (gcd != 1): {p}/{q}")

    spec = _DIAL_BY_NAME[dial]
    cycle = spec.cycle
    # If the cycle's true ratio is num/den (per modern_days), the implied
    # period under the custom (p, q) is (cycle.modern_days / cycle.numerator) * p.
    # That mirrors how the mechanism's gear train would interpret the ratio.
    if cycle.modern_days is None or cycle.modern_days <= 0:
        raise ValueError(f"dial {dial!r} has no usable modern_days")
    implied_period = (cycle.modern_days / cycle.numerator) * p
    days = float(jd_tdb) - REFERENCE_JD
    phase = (days / implied_period) % 1.0
    residue = int(phase * p) % p
    angle_deg = phase * 360.0
    return {
        "dial": dial,
        "p": p, "q": q,
        "ratio": p / q,
        "implied_period_days": float(implied_period),
        "residue": residue,
        "angle_deg": float(angle_deg),
    }


def compare_to_ground_truth(jd_tdb: float, dial: str, p: int, q: int) -> Dict[str, Any]:
    """Compare a custom ratio's residue against the canonical encoder."""
    custom = encode_with_custom_train(jd_tdb, dial, p, q)
    spec = _DIAL_BY_NAME[dial]
    canonical_residue = int(spec.integer_residue(jd_tdb))
    canonical_angle = (
        ((jd_tdb - REFERENCE_JD) / spec.cycle_period_days) % 1.0
    ) * 360.0
    return {
        "custom": custom,
        "canonical_residue": canonical_residue,
        "canonical_angle_deg": float(canonical_angle),
        "angle_residual_deg": float(custom["angle_deg"] - canonical_angle),
    }


__all__ = ["MAX_TEETH", "encode_with_custom_train", "compare_to_ground_truth"]
