"""ONE carrier for a C-vs-Python comparison — the double projection.
rc479 (`#T1188`).

Not a test module (no ``test_`` prefix, no assertions). It exists because TWO
harnesses need the identical projection and a second copy would be free to
drift: ``tests/test_c_cascade_value_parity_rc450.py`` (the value gate) and
``tests/test_c_cascade_parity_ratchet_rc446.py`` (the accepted/rejected
ratchet), which the value gate cross-ties itself to — so a difference between
two copies would read as the two harnesses disagreeing, which is the exact
signal that tie exists to report.

WHY IT IS NEEDED AT ALL
-----------------------
Contract A (rc479) reads a descriptor's decimal literals as the exact
rationals they name, so a proof case's inputs AND a chain's bound literals
arrive as ``Q``. C has no exact route: a bare-C host reads the same
descriptor through ``srmech_toml_parse`` and gets ``double``, and no C value
layer in this library can hold a rational (``dv_value_t`` and
``srmech_mval_t`` both carry ``double``). So an unprojected harness does one
of two wrong things, and rc479 measured BOTH before this helper existed:

1. ``json.dumps`` has no ``default=`` for a ``Q``, so the marshal fails and
   the case is recorded "not serialisable". In the value gate that meant
   **50 of 98 proof cases silently reclassified from BYTE_IDENTICAL to
   NONFINITE_CANNOT_CROSS_WIRE** — a verdict whose NAME then said something
   false about them. In the rc446 ratchet it meant **8 of 18 chains
   reclassified from accepted to rejected**, which is the same collapse
   wearing the other harness's vocabulary.
2. Project only the INPUTS and the chain's bound literals stay exact, so C
   runs on doubles and Python on exact rationals — a DIVERGENT verdict on a
   difference that is the CARRIER rather than the kernel.

So both harnesses project the chain document AND the case inputs, once, and
compare like with like. What that scopes them to is stated rather than
implied: **the C kernel and the Python kernel agree on the same chain over
the same doubles.** Neither file covers the exact route, because C does not
have one; the exact route's own gate is
``tests/test_cascade_catalog_executable_rc420.py``, which runs the pure
projection by construction.

Integer-only: nothing here rounds except the single explicit ``float()`` at
the leaf, which is the projection this module is named for.
"""

from __future__ import annotations

from typing import Any


def double_projection(value: Any) -> Any:
    """``value`` with every exact-rational leaf replaced by its double.

    ``int`` / ``bool`` are returned untouched — they are exact on both sides
    of the wire and projecting them would introduce the very rounding this
    helper exists to keep on ONE side. A non-finite ``float`` is likewise
    untouched, so a harness that refuses to marshal it still refuses, which is
    what ``NONFINITE_CANNOT_CROSS_WIRE`` is supposed to mean.

    Raises ``OverflowError`` for a rational outside double range, which is the
    right answer: such a value genuinely cannot cross this wire, and inventing
    an infinity for it would be the silent wrong answer.
    """
    if isinstance(value, dict):
        return {k: double_projection(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(double_projection(v) for v in value)
    if isinstance(value, list):
        return [double_projection(v) for v in value]
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    num = getattr(value, "numerator", None)
    den = getattr(value, "denominator", None)
    if isinstance(num, int) and isinstance(den, int):
        return float(value)
    return value
