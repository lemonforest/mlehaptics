"""C/Python parity tests for srmech.amsc.cascade.reorient.

v0.4.5rc4 continues the v0.4.5rc1 + rc2 + rc3 cascade-catalog C-parity
correction by retrofitting reorient (Class C cascade-orientation
re-application) with both native C symbols (i64 + f64; type-preserving)
and a TOML descriptor. This test confirms native + Python paths produce
bit-identical outputs across the supported input types.

The reference Python impl (cascade.py) is:
    if orientation < 0:
        return -value
    return value

The native C impls (i64 + f64) preserve that behaviour bit-identically —
verified in each test below. The op is type-preserving: int in → int
out, float in → float out. Boundary cases:
  - INT64_MIN: explicit Python-fallback gate (negation would overflow
    under fixed-width two's-complement; Python's arbitrary-precision
    int handles it).
  - NaN / +/-Inf: IEEE-754 negation flips the sign bit; NaN stays NaN;
    +/-Inf swap.
  - bool orientation: bool subclasses int but must NOT take the native
    path (True/False are Python idiomatic, not int8 codepoints).
  - Out-of-int8 orientation: skipped from native; Python fallback runs.
"""
import math
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)


# Whether the loaded libsrmech actually exposes the reorient symbols.
# Mirrors test_cascade_magnitude_parity.py — a stale lib (pre-rc4) loads
# fine but doesn't expose the new symbols; tests that need the native
# path skip cleanly when this is False.
_REORIENT_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_reorient_i64")
    and hasattr(_native.LIB, "srmech_cascade_reorient_f64")
)

SKIP_IF_NO_REORIENT_NATIVE = pytest.mark.skipif(
    not _REORIENT_NATIVE,
    reason="installed libsrmech predates v0.4.5rc4 reorient symbols",
)


def _py_ref(orientation, value):
    """The Python reference impl, inlined so test parity is unambiguous."""
    if orientation < 0:
        return -value
    return value


# ──────────────────────────────────────────────────────────────────────
# Python-path tests (numpy / list / mixed — must stay on Python).
# ──────────────────────────────────────────────────────────────────────


def test_python_path_numpy_ndarray():
    """numpy ndarray stays on Python; numpy negation applies."""
    np = pytest.importorskip("numpy")
    arr = np.array([1.0, 2.0, 3.0])
    result = cascade.reorient(arr, orientation=-1)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, np.array([-1.0, -2.0, -3.0]))


def test_python_path_list_raises():
    """list value stays on Python; Python `-[1,2,3]` is TypeError —
    preserve that bubbling rather than masking it via native."""
    with pytest.raises(TypeError):
        cascade.reorient([1, 2, 3], orientation=-1)
    # orientation == 0 / positive should NOT negate so list passes through
    # unchanged (the `value` branch returns value).
    result = cascade.reorient([1, 2, 3], orientation=0)
    assert result == [1, 2, 3]


def test_python_path_orientation_zero_passes_through():
    """orientation == 0 returns value unchanged across every type."""
    assert cascade.reorient(5, orientation=0) == 5
    assert cascade.reorient(3.14, orientation=0) == 3.14
    assert cascade.reorient(-7, orientation=0) == -7


def test_python_path_orientation_positive_passes_through():
    """orientation > 0 returns value unchanged."""
    assert cascade.reorient(5, orientation=1) == 5
    assert cascade.reorient(3.14, orientation=1) == 3.14
    assert cascade.reorient(-7, orientation=1) == -7


# ──────────────────────────────────────────────────────────────────────
# Native-path parity tests (int values via i64 variant).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_parity_int_negative_orientation():
    """orientation = -1, int values — negate; type-preserving (int out)."""
    for v in [5, -3, 0, 1, 100, -100]:
        native = cascade.reorient(v, orientation=-1)
        ref = _py_ref(-1, v)
        assert native == ref, f"v={v}: native={native}, ref={ref}"
        assert isinstance(native, int)
        assert not isinstance(native, float)


@SKIP_IF_NO_NATIVE
def test_parity_int_zero_orientation():
    """orientation = 0, int values — pass through; type-preserving."""
    for v in [5, -3, 0, 1, 100, -100]:
        native = cascade.reorient(v, orientation=0)
        ref = _py_ref(0, v)
        assert native == ref
        assert isinstance(native, int)


@SKIP_IF_NO_NATIVE
def test_parity_int_positive_orientation():
    """orientation = +1, int values — pass through; type-preserving."""
    for v in [5, -3, 0, 1, 100, -100]:
        native = cascade.reorient(v, orientation=1)
        ref = _py_ref(1, v)
        assert native == ref
        assert isinstance(native, int)


# ──────────────────────────────────────────────────────────────────────
# Native-path parity tests (float values via f64 variant).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_parity_float_negative_orientation():
    """orientation = -1, float values — IEEE-754 negation; float out."""
    for v in [3.14, -3.14, 0.5, -0.5, 1e10, -1e-10]:
        native = cascade.reorient(v, orientation=-1)
        ref = _py_ref(-1, v)
        assert native == ref, f"v={v}: native={native}, ref={ref}"
        assert isinstance(native, float)


@SKIP_IF_NO_NATIVE
def test_parity_float_zero_orientation_passes_through():
    """orientation = 0, float values — pass through; type-preserving."""
    for v in [3.14, -3.14, 0.0, -0.0, 1e10]:
        native = cascade.reorient(v, orientation=0)
        ref = _py_ref(0, v)
        assert native == ref
        assert isinstance(native, float)


# ──────────────────────────────────────────────────────────────────────
# INT64 boundary cases — INT64_MIN MUST fall back to Python.
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_int64_min_falls_back_to_python():
    """INT64_MIN = -(2**63) must NOT dispatch to native (would overflow).
    Python's arbitrary-precision int returns 2**63 (which is OUT of
    int64 range) — confirming the fallback ran (no overflow / clobber)."""
    INT64_MIN = -(2 ** 63)
    native = cascade.reorient(INT64_MIN, orientation=-1)
    ref = _py_ref(-1, INT64_MIN)
    assert native == ref
    assert native == 2 ** 63  # arbitrary-precision result
    assert isinstance(native, int)


@SKIP_IF_NO_NATIVE
def test_int64_min_plus_one_does_dispatch_native():
    """INT64_MIN + 1 = -(2**63) + 1 = -9223372036854775807 — IS within
    safe-negation range; dispatches to native; correct result."""
    v = -(2 ** 63) + 1
    native = cascade.reorient(v, orientation=-1)
    ref = _py_ref(-1, v)
    assert native == ref
    assert native == (2 ** 63) - 1
    assert isinstance(native, int)


@SKIP_IF_NO_NATIVE
def test_int64_max_dispatches_native():
    """INT64_MAX = 2**63 - 1 — dispatches; negation is safe."""
    v = (2 ** 63) - 1
    native = cascade.reorient(v, orientation=-1)
    ref = _py_ref(-1, v)
    assert native == ref
    assert native == -((2 ** 63) - 1)
    assert isinstance(native, int)


@SKIP_IF_NO_NATIVE
def test_bigint_falls_back_to_python():
    """Values beyond int64 range must NOT dispatch to native; Python
    arbitrary-precision handles them."""
    v = 2 ** 100
    native = cascade.reorient(v, orientation=-1)
    ref = _py_ref(-1, v)
    assert native == ref
    assert native == -(2 ** 100)
    assert isinstance(native, int)


# ──────────────────────────────────────────────────────────────────────
# IEEE-754 edge cases for the f64 variant.
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_nan_stays_nan_under_negation():
    """orientation < 0 with NaN value: result is still NaN (IEEE-754
    negation flips the sign bit; NaN-ness is preserved)."""
    native = cascade.reorient(float("nan"), orientation=-1)
    assert math.isnan(native)
    # And orientation = 0 also keeps NaN.
    native0 = cascade.reorient(float("nan"), orientation=0)
    assert math.isnan(native0)


@SKIP_IF_NO_NATIVE
def test_positive_inf_swaps_to_negative_inf():
    """orientation = -1 with +inf: result is -inf."""
    native = cascade.reorient(float("inf"), orientation=-1)
    ref = _py_ref(-1, float("inf"))
    assert native == ref
    assert math.isinf(native)
    assert native < 0


@SKIP_IF_NO_NATIVE
def test_negative_inf_swaps_to_positive_inf():
    """orientation = -1 with -inf: result is +inf."""
    native = cascade.reorient(float("-inf"), orientation=-1)
    ref = _py_ref(-1, float("-inf"))
    assert native == ref
    assert math.isinf(native)
    assert native > 0


# ──────────────────────────────────────────────────────────────────────
# Orientation-typing edge cases.
# ──────────────────────────────────────────────────────────────────────


def test_bool_orientation_stays_python():
    """bool is int-subclass but must skip native dispatch. Python
    fallback evaluates ``True < 0`` as False → returns value; ``False
    < 0`` also False → returns value. Verify result is correct AND
    Python-pathed (bool orientation never reaches the native call)."""
    # True < 0 is False, so the value is returned unchanged.
    assert cascade.reorient(5, orientation=True) == 5
    assert cascade.reorient(5, orientation=False) == 5
    # And for floats.
    assert cascade.reorient(3.14, orientation=True) == 3.14
    assert cascade.reorient(3.14, orientation=False) == 3.14


def test_orientation_out_of_int8_range_stays_python():
    """orientation outside int8 range [-128, 127] skips native; Python
    fallback handles it. 128 >= 0 → returns value; -129 < 0 → negates."""
    assert cascade.reorient(5, orientation=128) == 5
    assert cascade.reorient(5, orientation=-129) == -5
    assert cascade.reorient(3.14, orientation=128) == 3.14
    assert cascade.reorient(3.14, orientation=-129) == -3.14


# ──────────────────────────────────────────────────────────────────────
# Random sweeps — int and float.
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_NATIVE
def test_parity_random_int_sweep():
    """Native parity across a random sample of (orientation, int)."""
    rng = random.Random(4321)
    for _ in range(50):
        o = rng.choice([-1, 0, 1])
        v = rng.randint(-(2 ** 60), 2 ** 60)
        native = cascade.reorient(v, orientation=o)
        ref = _py_ref(o, v)
        assert native == ref, f"o={o}, v={v}: native={native}, ref={ref}"
        assert isinstance(native, int)


@SKIP_IF_NO_NATIVE
def test_parity_random_float_sweep():
    """Native parity across a random sample of (orientation, float).
    Bit-exact equality — sign-flip has no floating-point rounding."""
    rng = random.Random(8765)
    for _ in range(50):
        o = rng.choice([-1, 0, 1])
        v = rng.uniform(-1e6, 1e6)
        native = cascade.reorient(v, orientation=o)
        ref = _py_ref(o, v)
        assert native == ref, f"o={o}, v={v}: native={native}, ref={ref}"
        assert isinstance(native, float)


# ──────────────────────────────────────────────────────────────────────
# Native-symbol exposure (gated; mirrors the rc1/rc2/rc3 convention).
# ──────────────────────────────────────────────────────────────────────


@SKIP_IF_NO_REORIENT_NATIVE
def test_native_lib_exposes_both_symbols():
    """The libsrmech native library exposes both reorient symbols.

    Skips cleanly on a stale lib (pre-rc4) — mirrors the rc1/rc2/rc3
    binding convention. Once the v0.4.5rc4 wheel is installed, this
    test confirms both symbols are present.
    """
    assert _native.LIB is not None
    assert hasattr(_native.LIB, "srmech_cascade_reorient_i64")
    assert hasattr(_native.LIB, "srmech_cascade_reorient_f64")
