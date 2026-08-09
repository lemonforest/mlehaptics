"""SPIKE `#T1114` rung 1 — the two ops ADR-0008 §2 needs and srmech does NOT
register, provided HERE (in `notes/`, outside the package) so the remaining
gap can be measured in isolation.

This is deliberately NOT a shim inside `srmech`.  Nothing in the package is
modified.  The point is to answer a narrower question than "does rung 1
pass": *if the op inventory were closed, would the linear chain be
bit-identical to the hand-rolled op?*  Whatever diverges after this module
is supplied is attributable to the SCHEMA (ADR-0008 §3.2 "no branching"),
not to a missing callable.

Both ops below are the exact stages the shipped
`best_rational_signed.toml` describes in prose but does not name as ops:

  `scale_round_half_even`  <- `[cascade.signature].operation`'s
                              "round(magnitude * fine_scale)", whose
                              banker's-rounding contract `[cascade.rounding]`
                              specifies at length.
  `pair`                   <- `[cascade.signature].output`'s
                              "tuple[int, int]", which no step can produce
                              because a chain returns only its LAST step's
                              value.

No `abs()`.  No `math` / `fractions` / `decimal` / `numpy`.
"""

from __future__ import annotations


def scale_round_half_even(*, value, scale):
    """Class N: scale a non-negative real by an integer and round
    half-to-even to an int.

    Mirrors the reference implementation's `int(round(mag * fine_scale))`
    exactly.  Python's built-in `round()` IS round-half-to-even (PEP 3141),
    which is the parity contract `[cascade.rounding]` pins the C peer to via
    `_cascade_brs_round_half_even`.
    """
    return int(round(value * scale))


def pair(*, first, second):
    """Class B (framing): assemble two prior step outputs into the 2-tuple
    the chain's declared `returns` promises.  A chain returns only its final
    step's output, so the pair must itself be a step."""
    return (first, second)


# Re-exports so a single spike module can back the K / C / N letters.
from srmech.cascade.atoms import pin_slot_at_zero, reorient  # noqa: E402,F401
from srmech.math.rational import best_rational  # noqa: E402,F401
