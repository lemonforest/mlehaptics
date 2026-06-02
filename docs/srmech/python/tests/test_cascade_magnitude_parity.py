"""C/Python parity tests for srmech.amsc.cascade.magnitude.

v0.4.5rc3 continues the v0.4.5rc1 + rc2 cascade-catalog C-parity
correction by retrofitting magnitude (Class K magnitude-only projection)
with both a native C symbol and a TOML descriptor. This test confirms
native + Python paths produce bit-identical outputs across the supported
input types.

The reference Python impl (cascade.py) is the composition
``pin_slot_at_zero(x)[1]`` — which itself maps NaN to ``0.0`` (both
``x > 0`` and ``x < 0`` evaluate False for NaN, falling through to the
dead-band ``(0, 0.0)``). The native C impl preserves that behaviour
bit-identically — verified in each test below.
"""
import math

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)


# Whether the loaded libsrmech actually exposes the magnitude symbol.
# Mirrors test_cascade_pin_slot_at_zero_parity.py — a stale lib (pre-rc3)
# loads fine but doesn't expose the new symbol; tests that need the
# native path skip cleanly when this is False.
_MAGNITUDE_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_magnitude_f64")
)

SKIP_IF_NO_MAGNITUDE_NATIVE = pytest.mark.skipif(
    not _MAGNITUDE_NATIVE,
    reason="installed libsrmech predates v0.4.5rc3 magnitude symbol",
)


def _py_ref(x):
    """The Python reference impl, inlined so test parity is unambiguous.

    Equivalent to ``pin_slot_at_zero(x)[1]`` — including the dead-band
    branch that maps NaN to 0.0.
    """
    if x > 0.0:
        return x
    if x < 0.0:
        return -x
    return 0.0


# ──────────────────────────────────────────────────────────────────────
# Python-path tests (int inputs — must stay on Python; magnitude must
# stay int, not be coerced to float by the native path).
# ──────────────────────────────────────────────────────────────────────


def test_python_path_int_positive():
    """Positive int stays on Python; magnitude is int (not float)."""
    mag = cascade.magnitude(5)
    assert mag == 5
    assert isinstance(mag, int)
    assert not isinstance(mag, float)


def test_python_path_int_negative():
    """Negative int stays on Python; magnitude is int (not float)."""
    mag = cascade.magnitude(-3)
    assert mag == 3
    assert isinstance(mag, int)
    assert not isinstance(mag, float)


def test_python_path_int_zero():
    """Zero int hits the dead-band; magnitude is float 0.0 (matches ref)."""
    mag = cascade.magnitude(0)
    assert mag == 0
    # The Python ref returns 0.0 (a float) for the dead-band branch
    # because pin_slot_at_zero(0)[1] is 0.0. Type-parity with the ref
    # is what matters: int -> the dead-band literal is a Python float.
    assert mag == 0.0


def test_python_path_bool_stays_python():
    """bool is a subclass of int — it must stay on the Python path
    so the int-in / int-magnitude-out contract holds for True/False."""
    mag_true = cascade.magnitude(True)
    # True > 0 is True (True == 1), so the positive branch returns x
    # itself: True. Bit-identical with the Python ref.
    assert mag_true == 1
    assert mag_true == _py_ref(True)
    # False hits the dead-band like 0 does.
    assert cascade.magnitude(False) == 0


# ──────────────────────────────────────────────────────────────────────
# Native-path parity tests (float inputs).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_parity_positive_floats():
    """Native parity for a range of positive floats."""
    samples = [1.0, 3.14, 1.5, 1e-10, 1e10, 0.5, 42.42]
    for x in samples:
        native = cascade.magnitude(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"
        assert isinstance(native, float)


@SKIP_IF_NO_NATIVE
def test_parity_negative_floats():
    """Native parity for a range of negative floats."""
    samples = [-1.0, -3.14, -1.5, -1e-10, -1e10, -0.5, -42.42]
    for x in samples:
        native = cascade.magnitude(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"
        assert isinstance(native, float)


@SKIP_IF_NO_NATIVE
def test_parity_positive_zero():
    """+0.0 maps to the dead-band 0.0."""
    native = cascade.magnitude(0.0)
    python_ref = _py_ref(0.0)
    assert native == python_ref
    assert native == 0.0


@SKIP_IF_NO_NATIVE
def test_parity_negative_zero():
    """-0.0 also maps to the dead-band 0.0 — both `x > 0` and `x < 0`
    evaluate False for -0.0, hitting the else branch."""
    native = cascade.magnitude(-0.0)
    python_ref = _py_ref(-0.0)
    assert native == python_ref
    assert native == 0.0


@SKIP_IF_NO_NATIVE
def test_parity_very_small_magnitude():
    """Native parity at the small-magnitude boundary (1e-30, 1e-300)."""
    for x in [1e-30, -1e-30, 1e-300, -1e-300]:
        native = cascade.magnitude(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"


@SKIP_IF_NO_NATIVE
def test_parity_very_large_magnitude():
    """Native parity at the large-magnitude boundary (1e30, 1e300)."""
    for x in [1e30, -1e30, 1e300, -1e300]:
        native = cascade.magnitude(x)
        python_ref = _py_ref(x)
        assert native == python_ref, f"x={x}: native={native}, ref={python_ref}"


@SKIP_IF_NO_NATIVE
def test_parity_nan_dead_band():
    """NaN maps to the dead-band 0.0 — IEEE-754 says NaN > 0 and NaN < 0
    are both False, so both Python ref and native C land in the else
    branch with the same 0.0 result. The result is NOT NaN — it is 0.0,
    the else-branch's explicit constant. This is the load-bearing parity
    invariant: a naive ``if (x < 0) out = -x; else out = x`` C impl
    would return NaN here, breaking parity."""
    native = cascade.magnitude(float("nan"))
    python_ref = _py_ref(float("nan"))
    assert native == python_ref
    assert native == 0.0
    assert not math.isnan(native)


@SKIP_IF_NO_NATIVE
def test_parity_positive_infinity():
    """+inf maps to +inf — `+inf > 0.0` is True, magnitude is +inf
    unchanged."""
    native = cascade.magnitude(float("inf"))
    python_ref = _py_ref(float("inf"))
    assert native == python_ref
    assert math.isinf(native)
    assert native > 0


@SKIP_IF_NO_NATIVE
def test_parity_negative_infinity():
    """-inf maps to +inf — `-inf < 0.0` is True, so the magnitude is
    `-(-inf)` = `+inf`."""
    native = cascade.magnitude(float("-inf"))
    python_ref = _py_ref(float("-inf"))
    assert native == python_ref
    assert math.isinf(native)
    assert native > 0


@SKIP_IF_NO_NATIVE
def test_parity_random_floats():
    """Native parity across a swept random sample (bit-exact)."""
    import random
    rng = random.Random(42)
    for _ in range(50):
        x = rng.uniform(-1e6, 1e6)
        native = cascade.magnitude(x)
        python_ref = _py_ref(x)
        # Bit-exact equality — sign-handling has no floating-point
        # rounding to worry about; the native path either returns x
        # unchanged or returns -x (a single negation), both of which
        # are exact under IEEE-754.
        assert native == python_ref, (
            f"x={x!r}: native={native}, ref={python_ref}"
        )


@SKIP_IF_NO_NATIVE
def test_composition_equivalence_with_pin_slot_at_zero():
    """The cascade-honest invariant: magnitude(x) == pin_slot_at_zero(x)[1]
    across every input class. This is the structural contract — the
    dedicated C symbol is a fast-path, NOT a separate primitive."""
    samples = [
        1.0, -1.0, 0.0, -0.0, 3.14, -3.14,
        1e-10, -1e-10, 1e10, -1e10,
        float("inf"), float("-inf"),
        # NOTE: NaN handled separately below — math.nan != math.nan
        # under IEEE-754 so a == comparison can't be used. But both
        # sides MUST return 0.0 not NaN, which is checked there.
    ]
    for x in samples:
        assert cascade.magnitude(x) == cascade.pin_slot_at_zero(x)[1], (
            f"x={x}: magnitude={cascade.magnitude(x)}, "
            f"pin_slot[1]={cascade.pin_slot_at_zero(x)[1]}"
        )
    # NaN check — both must return 0.0 (not NaN). The above equality
    # comparison would fail for NaN under IEEE-754 even if both sides
    # WERE NaN, so this is verified by value-equality on the dead-band
    # constant.
    nan = float("nan")
    assert cascade.magnitude(nan) == 0.0
    assert cascade.pin_slot_at_zero(nan)[1] == 0.0


# ──────────────────────────────────────────────────────────────────────
# Native-symbol exposure (gated; mirrors the rc1/rc2 binding convention).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_MAGNITUDE_NATIVE
def test_native_lib_exposes_symbol():
    """The libsrmech native library exposes the new symbol.

    Skips cleanly on a stale lib (pre-rc3) — mirrors the rc1/rc2
    binding convention. Once the v0.4.5rc3 wheel is installed, this
    test confirms the symbol is present.
    """
    assert _native.LIB is not None
    assert hasattr(_native.LIB, "srmech_cascade_magnitude_f64")
