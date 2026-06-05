"""§15.1 contract test — Class K real-axis atoms reject complex cleanly.

v0.7.0rc24 (UPSTREAM_NOTES §15.1, srmech-side fix (b)). ``cascade.magnitude``
and ``cascade.pin_slot_at_zero`` are **Class K pin-slot** operations —
real-axis sign-splits, signature ``(x: float)``. Before rc24 a complex
argument fell through to ``pin_slot_at_zero``'s ``if x > 0.0:`` and surfaced
an opaque ``TypeError: '>' not supported between instances of 'complex' and
'float'`` — an internal comparison leaking, not a contract error.

rc24 adds a ``_require_real`` boundary guard that raises an intentional,
actionable ``TypeError`` *before* any dispatch. This test pins:

1. both atoms reject Python ``complex`` and numpy complex scalars with a
   clean message that names the op + points at the Euclidean-norm
   alternative;
2. every real numeric (float / int / negative / zero / NaN / ±inf) is
   unaffected — no behaviour change for in-contract inputs.

The complex modulus ``(re**2 + im**2) ** 0.5`` is a **Euclidean-norm** op —
a *different* cascade class, not a Class K pin-slot — so it is deliberately
out of scope (option (b), not (a)).
"""
import math

import numpy as np
import pytest

from srmech.amsc import cascade
from srmech.amsc.cascade import atoms


# ──────────────────────────────────────────────────────────────────────
# Rejection: complex input → clean, actionable TypeError (not a leaked >)
# ──────────────────────────────────────────────────────────────────────

_COMPLEX_INPUTS = [
    complex(3, 4),
    complex(0, 1),
    complex(-2, -5),
    np.complex128(3 + 4j),
    np.complex64(1 - 2j),
    np.array(3 + 4j),  # 0-d complex ndarray (dtype.kind == 'c')
]


@pytest.mark.parametrize("z", _COMPLEX_INPUTS)
def test_magnitude_rejects_complex(z):
    """``magnitude`` raises a clean, actionable TypeError on complex."""
    with pytest.raises(TypeError) as exc:
        cascade.magnitude(z)
    msg = str(exc.value)
    # The message must name the op and NOT be the leaked ``'>' not
    # supported`` internal-comparison error.
    assert "magnitude" in msg
    assert "complex" in msg
    assert "'>' not supported" not in msg
    # Points at the right tool (Euclidean modulus, a different class).
    assert "hypot" in msg or "Euclidean" in msg


@pytest.mark.parametrize("z", _COMPLEX_INPUTS)
def test_pin_slot_at_zero_rejects_complex(z):
    """``pin_slot_at_zero`` raises a clean, actionable TypeError on complex."""
    with pytest.raises(TypeError) as exc:
        cascade.pin_slot_at_zero(z)
    msg = str(exc.value)
    assert "pin_slot_at_zero" in msg
    assert "complex" in msg
    assert "'>' not supported" not in msg


def test_magnitude_complex_message_is_not_the_leaked_comparison():
    """Regression pin: the old leak was the raw comparison TypeError.

    Confirms the boundary guard fires *before* the internal ``x > 0.0`` —
    i.e. the error text is the intentional contract message, never the
    Python comparison leak the §15.1 finding reported.
    """
    with pytest.raises(TypeError) as exc:
        atoms.magnitude(complex(3, 4))
    assert "Class K real-axis" in str(exc.value)


# ──────────────────────────────────────────────────────────────────────
# Real inputs are unaffected — no behaviour change for in-contract values
# ──────────────────────────────────────────────────────────────────────


def test_magnitude_real_floats_unchanged():
    assert cascade.magnitude(-5.0) == 5.0
    assert cascade.magnitude(5.0) == 5.0
    assert cascade.magnitude(0.0) == 0.0


def test_magnitude_int_stays_int():
    """The int-in / int-out contract (Python fallback path) is preserved."""
    out = cascade.magnitude(25)
    assert out == 25
    assert isinstance(out, int)
    neg = cascade.magnitude(-7)
    assert neg == 7
    assert isinstance(neg, int)


def test_magnitude_nan_maps_to_zero_deadband():
    """NaN → the Class K dead-band 0.0 in both paths (unchanged)."""
    assert cascade.magnitude(float("nan")) == 0.0


def test_magnitude_infinities_unchanged():
    assert cascade.magnitude(float("inf")) == float("inf")
    assert cascade.magnitude(float("-inf")) == float("inf")


def test_pin_slot_at_zero_real_unchanged():
    assert cascade.pin_slot_at_zero(2.0) == (+1, 2.0)
    assert cascade.pin_slot_at_zero(-2.0) == (-1, 2.0)
    assert cascade.pin_slot_at_zero(0.0) == (0, 0.0)


def test_numpy_real_scalars_pass_through():
    """Real numpy scalars are ordered against 0.0 → not rejected."""
    assert cascade.magnitude(np.float64(-3.0)) == 3.0
    # int64 stays on the Python path; magnitude is the |x| value.
    assert cascade.magnitude(np.int64(-4)) == 4
