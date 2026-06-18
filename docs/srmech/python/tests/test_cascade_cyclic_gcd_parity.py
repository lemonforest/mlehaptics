"""C/Python parity tests for srmech.amsc.cascade.cyclic_gcd.

v0.4.5rc6 continues the v0.4.5rc1..rc5 cascade-catalog C-parity
correction by retrofitting cyclic_gcd (Class I cyclic-group gcd) with a
cascade-namespace C wrapper and a TOML descriptor. This is the FIRST of
the delegating cascade ops in the arc: the cascade-catalog entry IS
the Class I primitive (Euclid gcd; srmech_gcd), and the cascade wrapper
(srmech_cascade_cyclic_gcd_u64) is a pure-delegation alias that exists
to maintain the srmech_cascade_* namespace invariant.

This test confirms native + Python paths produce bit-identical outputs
across the supported input types, and that BOTH the cascade-namespace
wrapper symbol AND the underlying Class I primitive symbol are exposed
(so application code can choose which surface to call).

The reference Python impl (cascade.py) falls through to
srmech.amsc.cyclic.gcd which is itself C-backed via srmech_gcd. The
native cascade-wrapper path (rc6) routes through
srmech_cascade_cyclic_gcd_u64 which internally calls srmech_gcd. Both
paths must produce bit-identical results.

Boundary cases:
  - gcd(0, 0) = 0; gcd(a, 0) = a; gcd(0, b) = b (gcd identity).
  - Negative input: Python fallback raises ValueError (matches
    srmech.amsc.cyclic.gcd uint64 surface).
  - Out-of-uint64: UNCAPPED (v0.9.0) — big-int Euclid (native serves uint64).
  - Bool input: Python fallback accepts (isinstance(True, int) is True);
    native rejects via `type(x) is int` (bool subclass check).
"""
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)

# Whether the loaded libsrmech actually exposes the cyclic_gcd cascade
# wrapper symbol. A stale lib (pre-rc6) loads fine but doesn't expose
# the new symbol; tests that need the native cascade path skip cleanly
# when this is False. The Class I primitive (srmech_gcd) has been
# present since rc1 of the original Phase C1 build-out, so it's
# expected to always be available when HAS_NATIVE — but we check it
# too so the symbol-exposure test reports both surfaces.
_CYCLIC_GCD_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_cyclic_gcd_u64")
)

SKIP_IF_NO_CYCLIC_GCD_NATIVE = pytest.mark.skipif(
    not _CYCLIC_GCD_NATIVE,
    reason="installed libsrmech predates v0.4.5rc6 cyclic_gcd cascade symbol",
)


def _python_ref(a, b):
    """Bit-identical Euclidean gcd mirror (no srmech imports)."""
    while b != 0:
        a, b = b, a % b
    return a


# ──────────────────────────────────────────────────────────────────────
# Basic correctness (cascade ref vs Python ref bit-identical)
# ──────────────────────────────────────────────────────────────────────

def test_basic_gcd_12_8_is_4():
    assert cascade.cyclic_gcd(12, 8) == 4


def test_basic_gcd_17_5_is_1_coprime():
    """Coprime inputs return 1."""
    assert cascade.cyclic_gcd(17, 5) == 1


def test_gcd_identity_zero_zero_is_zero():
    """gcd(0, 0) = 0 by convention (matches srmech_gcd)."""
    assert cascade.cyclic_gcd(0, 0) == 0


def test_gcd_identity_zero_seven_is_seven():
    """gcd(0, b) = b — left identity."""
    assert cascade.cyclic_gcd(0, 7) == 7


def test_gcd_identity_seven_zero_is_seven():
    """gcd(a, 0) = a — right identity."""
    assert cascade.cyclic_gcd(7, 0) == 7


def test_gcd_equal_inputs_returns_input():
    assert cascade.cyclic_gcd(42, 42) == 42


def test_gcd_one_with_anything_is_one():
    assert cascade.cyclic_gcd(1, 1_000_000) == 1


# ──────────────────────────────────────────────────────────────────────
# Large values within uint64
# ──────────────────────────────────────────────────────────────────────

def test_gcd_large_pair_near_2_62():
    """A pair near 2**62 — well within uint64, hits the native path."""
    a = 2 ** 62
    b = (2 ** 62) - 2  # gcd = 2 (both even, differ by 2)
    assert cascade.cyclic_gcd(a, b) == _python_ref(a, b)


def test_gcd_large_coprime_pair():
    """Two large Mersenne-ish primes — coprime, gcd = 1."""
    a = (2 ** 61) - 1  # Mersenne prime M_61
    b = (2 ** 31) - 1  # Mersenne prime M_31
    assert cascade.cyclic_gcd(a, b) == 1


# ──────────────────────────────────────────────────────────────────────
# Boundary inputs — Python fallback paths (negative / bigint / bool)
# ──────────────────────────────────────────────────────────────────────

def test_negative_a_falls_back_python_raises():
    """Negative inputs: native dispatch falls through; Python ref raises."""
    with pytest.raises(ValueError, match="must be non-negative"):
        cascade.cyclic_gcd(-12, 8)


def test_negative_b_falls_back_python_raises():
    with pytest.raises(ValueError, match="must be non-negative"):
        cascade.cyclic_gcd(12, -8)


def test_both_negative_falls_back_python_raises():
    with pytest.raises(ValueError, match="must be non-negative"):
        cascade.cyclic_gcd(-12, -8)


def test_out_of_uint64_a_is_bigint_uncapped():
    """v0.9.0: cyclic.gcd is UNCAPPED — bigint > 2**64-1 takes the big-int
    Euclid (native serves its uint64 domain; standalone-honor "no compiled-in
    caps"). gcd(2**100, 2**99) == 2**99."""
    assert cascade.cyclic_gcd(2 ** 100, 2 ** 99) == 2 ** 99


def test_bool_true_input_via_python_fallback():
    """Bool: native rejects (type(True) is not int); Python ref accepts
    (isinstance(True, int) is True, value 1). gcd(1, 8) == 1.
    """
    # Both bool reach the Python fallback path; result matches the int
    # equivalent gcd(1, 8) == 1.
    assert cascade.cyclic_gcd(True, 8) == 1


def test_bool_false_input_via_python_fallback():
    """gcd(False, 8) == gcd(0, 8) == 8."""
    assert cascade.cyclic_gcd(False, 8) == 8


# ──────────────────────────────────────────────────────────────────────
# Native + Python ref bit-identical sweep
# ──────────────────────────────────────────────────────────────────────

@SKIP_IF_NO_CYCLIC_GCD_NATIVE
def test_native_vs_python_ref_30_pair_random_sweep():
    """30-pair random sweep within uint64 range; native dispatch through
    the cascade-namespace wrapper must equal the Python Euclidean ref
    bit-exactly.
    """
    rng = random.Random(20260528)  # deterministic seed
    UINT64_MAX = (2 ** 64) - 1
    for _ in range(30):
        a = rng.randint(0, UINT64_MAX)
        b = rng.randint(0, UINT64_MAX)
        cascade_result = cascade.cyclic_gcd(a, b)
        ref_result = _python_ref(a, b)
        assert cascade_result == ref_result, (
            f"native cascade dispatch diverged from Python Euclidean ref "
            f"for gcd({a}, {b}): cascade={cascade_result}, ref={ref_result}"
        )


@SKIP_IF_NO_CYCLIC_GCD_NATIVE
def test_native_known_gcd_pairs_bit_exact():
    """Well-known gcd pairs through the native cascade path."""
    cases = [
        (48, 18, 6),
        (100, 75, 25),
        (1_071, 462, 21),  # Knuth's classic Euclidean example
        (1_000_000, 1, 1),
        (12345, 67890, 15),
    ]
    for a, b, expected in cases:
        assert cascade.cyclic_gcd(a, b) == expected, (
            f"gcd({a}, {b}) expected {expected}"
        )
        # Symmetry: gcd is commutative
        assert cascade.cyclic_gcd(b, a) == expected


# ──────────────────────────────────────────────────────────────────────
# Symbol exposure — both cascade wrapper AND Class I primitive present
# ──────────────────────────────────────────────────────────────────────

@SKIP_IF_NO_NATIVE
def test_cascade_wrapper_symbol_is_exposed():
    """rc6 ships srmech_cascade_cyclic_gcd_u64 as the cascade-catalog
    naming-uniform entry-point.
    """
    assert hasattr(_native.LIB, "srmech_cascade_cyclic_gcd_u64"), (
        "rc6 cascade-namespace wrapper srmech_cascade_cyclic_gcd_u64 "
        "should be exposed in libsrmech"
    )


@SKIP_IF_NO_NATIVE
def test_class_i_primitive_symbol_still_exposed():
    """The Class I primitive srmech_gcd (from Phase C1 rc1) must remain
    exposed alongside the cascade wrapper — both surfaces coexist.
    """
    assert hasattr(_native.LIB, "srmech_gcd"), (
        "the Class I primitive srmech_gcd should remain exposed in "
        "libsrmech (cascade wrapper is an alias, not a replacement)"
    )


@SKIP_IF_NO_CYCLIC_GCD_NATIVE
def test_cascade_wrapper_and_primitive_agree_bit_exact():
    """The cascade-namespace wrapper and the Class I primitive are two
    entry-points to the same Euclidean iteration; calling each directly
    must produce bit-identical results.
    """
    import ctypes
    pairs = [(12, 8), (1_071, 462), (0, 0), (1, 1), (2 ** 50, 2 ** 49)]
    for a, b in pairs:
        # Through cascade wrapper
        out_w = ctypes.c_uint64(0)
        rc_w = _native.LIB.srmech_cascade_cyclic_gcd_u64(
            ctypes.c_uint64(a), ctypes.c_uint64(b), ctypes.byref(out_w),
        )
        # Direct to primitive
        out_p = ctypes.c_uint64(0)
        rc_p = _native.LIB.srmech_gcd(
            ctypes.c_uint64(a), ctypes.c_uint64(b), ctypes.byref(out_p),
        )
        assert rc_w == _native.SRMECH_OK
        assert rc_p == _native.SRMECH_OK
        assert int(out_w.value) == int(out_p.value), (
            f"cascade wrapper / Class I primitive diverged at gcd({a}, {b}): "
            f"wrapper={out_w.value}, primitive={out_p.value}"
        )
