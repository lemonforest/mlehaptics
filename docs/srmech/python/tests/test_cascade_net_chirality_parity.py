"""C/Python parity tests for srmech.amsc.cascade.net_chirality.

v0.4.5rc5 continues the v0.4.5rc1 + rc2 + rc3 + rc4 cascade-catalog
C-parity correction by retrofitting net_chirality (Class C net handedness
invariant) with a native C symbol and a TOML descriptor. This test
confirms native + Python paths produce bit-identical outputs across the
supported input types.

The reference Python impl (cascade.py) is:

    net = 1
    for o in orientations:
        if o == 0:
            return 0
        net = reorient(net, orientation=o)
    return net

The native C impl (srmech_cascade_net_chirality_i8) preserves that
behaviour bit-identically — verified in each test below. ABI shape:
const int8_t *orientations + size_t n -> int8_t out via output pointer.
Boundary cases:
  - Empty: returns +1 (multiplicative identity; loop doesn't execute).
  - Any 0: short-circuits to 0 (a zero-crossing collapses net handedness).
  - Out-of-int8 values: Python fallback (the native ABI is int8).
  - Bool elements: Python fallback (Python iteration handles False == 0).
  - Generators: Python fallback (no len(); can't pre-size the C buffer).
  - Mixed types (int + float): Python fallback.

numpy-free: inputs are plain Python lists/tuples/generators; the random
sweep uses ``random.Random``; the reference oracle is the hand-written
product-of-signs ``_python_ref``. The old ndarray-dtype dispatch cases
(``np.int8``…``np.uint32`` sweeps + empty/out-of-int8 ndarray) were deleted
— they only exercised numpy ndarray inputs that no longer reach srmech now
that numpy is out; the equivalent list-input fallbacks are retained.
"""
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)

# Whether the loaded libsrmech actually exposes the net_chirality symbol.
# Mirrors the test_cascade_reorient_parity.py / chiral_flip pattern — a
# stale lib (pre-rc5) loads fine but doesn't expose the new symbol;
# tests that need the native path skip cleanly when this is False.
_NET_CHIRALITY_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_net_chirality_i8")
)

SKIP_IF_NO_NET_CHIRALITY_NATIVE = pytest.mark.skipif(
    not _NET_CHIRALITY_NATIVE,
    reason="installed libsrmech predates v0.4.5rc5 net_chirality symbol",
)


def _python_ref(orientations):
    """Bit-identical mirror of the Python fallback in cascade.net_chirality."""
    net = 1
    for o in orientations:
        if o == 0:
            return 0
        if o < 0:
            net = -net
        # o > 0: net unchanged
    return net


# ──────────────────────────────────────────────────────────────────────
# Empty / singleton / multi (basic correctness)
# ──────────────────────────────────────────────────────────────────────

def test_empty_list_returns_one():
    """Empty input returns +1 (multiplicative identity)."""
    assert cascade.net_chirality([]) == 1


def test_empty_tuple_returns_one():
    assert cascade.net_chirality(()) == 1


def test_single_positive():
    assert cascade.net_chirality([+1]) == 1


def test_single_negative():
    assert cascade.net_chirality([-1]) == -1


def test_single_zero():
    assert cascade.net_chirality([0]) == 0


def test_three_positives():
    assert cascade.net_chirality([+1, +1, +1]) == 1


def test_two_negatives_cancel():
    assert cascade.net_chirality([-1, -1]) == 1


def test_three_mixed_two_neg():
    assert cascade.net_chirality([-1, +1, -1]) == 1


def test_three_negatives():
    assert cascade.net_chirality([-1, -1, -1]) == -1


# ──────────────────────────────────────────────────────────────────────
# Short-circuit on zero
# ──────────────────────────────────────────────────────────────────────

def test_short_circuit_middle_zero():
    assert cascade.net_chirality([1, 1, 0, -1]) == 0


def test_short_circuit_leading_zero():
    assert cascade.net_chirality([0, -1, +1]) == 0


def test_tuple_input_parity_with_list():
    """Tuple input shape — same result as list."""
    assert cascade.net_chirality((-1, +1, -1)) == cascade.net_chirality([-1, +1, -1])
    assert cascade.net_chirality((+1, +1)) == cascade.net_chirality([+1, +1])
    assert cascade.net_chirality(()) == cascade.net_chirality([])


# ──────────────────────────────────────────────────────────────────────
# Python-fallback paths (generator / bool / out-of-int8 / mixed types)
# ──────────────────────────────────────────────────────────────────────

def test_generator_falls_back_to_python():
    """Generators have no len(); must fall back to the Python loop."""
    gen = (o for o in [-1, 1])
    assert cascade.net_chirality(gen) == -1


def test_bool_list_falls_back_python_path():
    """Bool list: type(True) is bool not int via `type(o) is not int` check
    -> Python fallback. False == 0 in Python iteration short-circuits to 0."""
    # [True, False]: native path rejects (bool is not exactly int);
    # Python path: True passes (True != 0), False short-circuits to 0.
    assert cascade.net_chirality([True, False]) == 0


def test_bool_list_all_true():
    """[True, True]: Python iteration; True != 0; True < 0 is False;
    so net stays at 1 throughout."""
    assert cascade.net_chirality([True, True]) == 1


def test_out_of_int8_list_falls_back():
    """[200]: 200 > 127 -> Python fallback. reorient(1, orientation=200) returns 1
    (orientation < 0 is False)."""
    assert cascade.net_chirality([200]) == 1


def test_out_of_int8_negative_list_falls_back():
    """[-200]: -200 < -128 -> Python fallback. reorient(1, orientation=-200) returns -1
    (orientation < 0 is True; -1 * 1 = -1)."""
    assert cascade.net_chirality([-200]) == -1


def test_mixed_int_float_falls_back_python():
    """[1, 1.0]: float is not int -> Python fallback. 1.0 != 0 and 1.0 < 0
    is False, so net stays at 1."""
    assert cascade.net_chirality([1, 1.0]) == 1


def test_mixed_with_zero_float():
    """[1, 0.0]: float is not int -> Python fallback. 0.0 == 0 -> short-circuit."""
    assert cascade.net_chirality([1, 0.0]) == 0


# ──────────────────────────────────────────────────────────────────────
# Random parity sweep (op result vs Python ref)
# ──────────────────────────────────────────────────────────────────────

@SKIP_IF_NO_NATIVE
def test_random_sweep_parity():
    """50-sample random sweep: the op and Python-ref agree everywhere."""
    rng = random.Random(20260528)
    for _ in range(50):
        n = rng.randint(0, 11)
        orientations = [rng.choice([-1, 0, +1]) for _ in range(n)]
        op_result = cascade.net_chirality(orientations)
        ref_result = _python_ref(orientations)
        assert op_result == ref_result, (
            f"net_chirality({orientations!r}) -> op={op_result}, "
            f"ref={ref_result}"
        )


# ──────────────────────────────────────────────────────────────────────
# Symbol-exposure check (gated)
# ──────────────────────────────────────────────────────────────────────

@SKIP_IF_NO_NET_CHIRALITY_NATIVE
def test_native_symbol_exposed():
    """Sanity check: the rc5 native symbol is reachable on this lib."""
    assert hasattr(_native.LIB, "srmech_cascade_net_chirality_i8")
