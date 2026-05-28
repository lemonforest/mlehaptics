"""C/Python parity tests for srmech.amsc.cascade.pin_slot_at_zero.

v0.4.5rc2 continues the v0.4.5rc1 cascade-catalog C-parity correction
by retrofitting pin_slot_at_zero (Class K) with both a native C symbol
and a TOML descriptor. This test confirms native + Python paths produce
bit-identical outputs across the supported input types.

The reference Python impl (cascade.py) splits a real value into
``(orientation, magnitude)`` where orientation in {-1, 0, +1}; the
``else`` branch (which handles 0.0, -0.0, AND NaN) returns ``(0, 0.0)``.
The native C impl preserves that behaviour bit-identically — verified
in each test below.
"""
import math

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)


# Whether the loaded libsrmech actually exposes the pin_slot_at_zero
# symbol. Mirrors test_cascade_chiral_flip_parity.py — a stale lib
# (pre-rc2) loads fine but doesn't expose the new symbol; tests that
# need the native path skip cleanly when this is False.
_PIN_SLOT_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_pin_slot_at_zero_f64")
)

SKIP_IF_NO_PIN_SLOT_NATIVE = pytest.mark.skipif(
    not _PIN_SLOT_NATIVE,
    reason="installed libsrmech predates v0.4.5rc2 pin_slot_at_zero symbol",
)


def _py_ref(x):
    """The Python reference impl, inlined so test parity is unambiguous."""
    if x > 0.0:
        return +1, x
    if x < 0.0:
        return -1, -x
    return 0, 0.0


# ──────────────────────────────────────────────────────────────────────
# Python-path tests (int inputs — must stay on Python; magnitude must
# stay int, not be coerced to float by the native path).
# ──────────────────────────────────────────────────────────────────────


def test_python_path_int_positive():
    """Positive int stays on Python; magnitude is int (not float)."""
    orient, mag = cascade.pin_slot_at_zero(5)
    assert (orient, mag) == (1, 5)
    assert isinstance(orient, int)
    assert isinstance(mag, int)
    assert not isinstance(mag, float)


def test_python_path_int_negative():
    """Negative int stays on Python; magnitude is int (not float)."""
    orient, mag = cascade.pin_slot_at_zero(-3)
    assert (orient, mag) == (-1, 3)
    assert isinstance(orient, int)
    assert isinstance(mag, int)
    assert not isinstance(mag, float)


def test_python_path_int_zero():
    """Zero int hits the dead-band; magnitude is float 0.0 (matches ref)."""
    orient, mag = cascade.pin_slot_at_zero(0)
    assert (orient, mag) == (0, 0.0)
    # The Python ref returns 0.0 (a float) for the dead-band branch;
    # type-parity with the ref is what matters.
    assert isinstance(orient, int)


def test_python_path_bool_stays_python():
    """bool is a subclass of int — it must stay on the Python path
    so the int-in / int-magnitude-out contract holds for True/False."""
    orient, mag = cascade.pin_slot_at_zero(True)
    assert orient == 1
    # The Python ref returns ``x`` itself on the positive branch, which
    # for bool=True is True (==1). What matters is bit-identical parity
    # with the ref impl.
    assert mag == _py_ref(True)[1]


# ──────────────────────────────────────────────────────────────────────
# Native-path parity tests (float inputs).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_parity_positive_floats():
    """Native parity for a range of positive floats."""
    samples = [1.0, 3.14, 1.5, 1e-10, 1e10, 0.5, 42.42]
    for x in samples:
        native = cascade.pin_slot_at_zero(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"
        assert isinstance(native[0], int)
        assert isinstance(native[1], float)


@SKIP_IF_NO_NATIVE
def test_parity_negative_floats():
    """Native parity for a range of negative floats."""
    samples = [-1.0, -3.14, -1.5, -1e-10, -1e10, -0.5, -42.42]
    for x in samples:
        native = cascade.pin_slot_at_zero(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"
        assert isinstance(native[0], int)
        assert isinstance(native[1], float)


@SKIP_IF_NO_NATIVE
def test_parity_positive_zero():
    """+0.0 maps to the dead-band (0, 0.0)."""
    native = cascade.pin_slot_at_zero(0.0)
    python_ref = _py_ref(0.0)
    assert native == python_ref
    assert native == (0, 0.0)


@SKIP_IF_NO_NATIVE
def test_parity_negative_zero():
    """-0.0 also maps to the dead-band (0, 0.0) — both `x > 0` and
    `x < 0` evaluate False for -0.0, hitting the else branch."""
    native = cascade.pin_slot_at_zero(-0.0)
    python_ref = _py_ref(-0.0)
    assert native == python_ref
    assert native == (0, 0.0)


@SKIP_IF_NO_NATIVE
def test_parity_very_small_magnitude():
    """Native parity at the small-magnitude boundary (1e-30, 1e-300)."""
    for x in [1e-30, -1e-30, 1e-300, -1e-300]:
        native = cascade.pin_slot_at_zero(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"


@SKIP_IF_NO_NATIVE
def test_parity_very_large_magnitude():
    """Native parity at the large-magnitude boundary (1e30, 1e300)."""
    for x in [1e30, -1e30, 1e300, -1e300]:
        native = cascade.pin_slot_at_zero(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"


@SKIP_IF_NO_NATIVE
def test_parity_nan_dead_band():
    """NaN maps to the dead-band (0, 0.0) — IEEE-754 says NaN > 0 and
    NaN < 0 are both False, so both Python ref and native C land in
    the else branch with the same (0, 0.0) result."""
    native = cascade.pin_slot_at_zero(float("nan"))
    python_ref = _py_ref(float("nan"))
    # Both must equal the dead-band exactly. The magnitude is NOT NaN —
    # it's 0.0, the else-branch's explicit constant.
    assert native == python_ref
    assert native == (0, 0.0)
    assert not math.isnan(native[1])


@SKIP_IF_NO_NATIVE
def test_parity_positive_infinity():
    """+inf maps to (+1, +inf) — both branches handle it the same way
    (+inf > 0.0 is True, so the magnitude is +inf unchanged)."""
    native = cascade.pin_slot_at_zero(float("inf"))
    python_ref = _py_ref(float("inf"))
    assert native == python_ref
    assert native[0] == 1
    assert math.isinf(native[1])
    assert native[1] > 0


@SKIP_IF_NO_NATIVE
def test_parity_negative_infinity():
    """-inf maps to (-1, +inf) — `-inf < 0.0` is True, so the magnitude
    is `-(-inf)` = `+inf`."""
    native = cascade.pin_slot_at_zero(float("-inf"))
    python_ref = _py_ref(float("-inf"))
    assert native == python_ref
    assert native[0] == -1
    assert math.isinf(native[1])
    assert native[1] > 0


@SKIP_IF_NO_NATIVE
def test_parity_random_floats():
    """Native parity across a swept random sample (bit-exact)."""
    import random
    rng = random.Random(42)
    for _ in range(50):
        x = rng.uniform(-1e6, 1e6)
        native = cascade.pin_slot_at_zero(x)
        python_ref = _py_ref(x)
        # Bit-exact equality — sign-handling has no floating-point
        # rounding to worry about; the native path either returns x
        # unchanged or returns -x (a single negation), both of which
        # are exact under IEEE-754.
        assert native == python_ref, (
            f"x={x!r}: native={native}, ref={python_ref}"
        )


# ──────────────────────────────────────────────────────────────────────
# Native-symbol exposure (gated; mirrors the rc1 chiral_flip pattern).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_PIN_SLOT_NATIVE
def test_native_lib_exposes_symbol():
    """The libsrmech native library exposes the new symbol.

    Skips cleanly on a stale lib (pre-rc2) — mirrors the rc1 chiral_flip
    binding convention. Once the v0.4.5rc2 wheel is installed, this test
    confirms the symbol is present.
    """
    assert _native.LIB is not None
    assert hasattr(_native.LIB, "srmech_cascade_pin_slot_at_zero_f64")
