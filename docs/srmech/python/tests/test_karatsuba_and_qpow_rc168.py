"""0.9.0rc168 — the bignum-layer optimization + a Q.__pow__ correctness fix.

PART 1 (#765 optimization): ``srmech_bigint_mul`` is now KARATSUBA above a
measured limb crossover (schoolbook below), with the split running as an
ITERATIVE explicit frame machine (JPL Rule 1: no recursion) over either a
caller scratch arena (the new ``srmech_bigint_mul_ws`` +
``srmech_bigint_mul_ws_bound`` symbols) or the plain entry's bounded
internal arena. The contract this file pins: the product is BYTE-IDENTICAL
to schoolbook (and to CPython int, the oracle) for every input — the arena
tunes speed, never the result — and the arena path is measurably faster at
huge sizes (the rc167 multiply gap vs CPython is closed: parity ~2048
limbs, a win above; the composite big-Q ops stay gcd-bound cost-parity —
the honest whole-op verdict lives in CHANGELOG rc168).

PART 2 (correctness, pre-existing — NOT an rc167 regression):
``Q(-3, 4) ** -2`` raised ``ValueError("denominator must be positive")``
because ``Q.__pow__`` routed the reciprocal ``(den, num)`` with a NEGATIVE
num into ``rational_pow_uint``'s positive-denominator contract. Fixed by
normalising the reciprocal's sign onto the numerator
(``b/a == (-b)/(-a)``); byte-identical to ``fractions.Fraction``.

⚠️ Sparse-tower guardrail: Karatsuba changes HOW two scalar bignums
multiply — the layer BELOW every carrier. No carrier structure is touched.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import ctypes
import importlib.util
import random
import time
from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc.q import Q

_HAS_KARA = bool(
    _native.HAS_NATIVE and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_bigint_mul_ws")
    and hasattr(_native.LIB, "srmech_bigint_mul_ws_bound"))

needs_kara = pytest.mark.skipif(
    not _HAS_KARA, reason="rc168 srmech_bigint_mul_ws symbols not loaded")


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "the rc168 tests must run on the numpy-ABSENT matrix")


# ── PART 1 helpers: drive the C multiply directly via the limb marshal ──────
def _c_mul(a: int, b: int, mode: str) -> int:
    """a·b through the C bigint multiply. mode: 'plain' (bounded internal
    arena), 'ws' (full-bound caller arena → complete Karatsuba split),
    'null' (ws=NULL → schoolbook forced), 'small' (1 KiB arena → partial
    split levels). All four must return the SAME integer."""
    lib = _native.LIB
    mag_a = a if a >= 0 else -a          # Class-K sign branch, never abs()
    mag_b = b if b >= 0 else -b
    an = max((mag_a.bit_length() + 31) // 32, 1)
    bn = max((mag_b.bit_length() + 31) // 32, 1)
    a_bi, _ka = _native._bigint_from_int(a, an + 1)
    b_bi, _kb = _native._bigint_from_int(b, bn + 1)
    o_bi, _ko = _native._bigint_from_int(0, an + bn + 2)
    if mode == "plain":
        rc = lib.srmech_bigint_mul(
            ctypes.byref(o_bi), ctypes.byref(a_bi), ctypes.byref(b_bi))
    else:
        if mode == "ws":
            wl = int(lib.srmech_bigint_mul_ws_bound(a_bi.n, b_bi.n))
            ws = (ctypes.c_uint64 * (wl // 8 + 1))() if wl else None
        elif mode == "small":
            ws = (ctypes.c_uint64 * 128)()
            wl = 1024
        else:
            ws, wl = None, 0
        rc = lib.srmech_bigint_mul_ws(
            ctypes.byref(o_bi), ctypes.byref(a_bi), ctypes.byref(b_bi),
            ws, wl)
    assert rc == _native.SRMECH_OK, f"mul rc={rc} mode={mode}"
    return _native._bigint_to_int(o_bi)


@needs_kara
def test_karatsuba_byte_identical_to_schoolbook_and_cpython():
    """The wide sweep: random + structured operands across small / mid /
    huge / asymmetric / signed shapes — all four multiply paths equal the
    CPython product (byte-identity: the limb sequence of an integer is
    unique after normalisation, so value equality IS limb equality)."""
    rng = random.Random(0xC168)
    cases = []
    for n_limbs in (1, 2, 3, 10, 23, 24, 25, 26, 30, 48, 100, 500, 2000):
        for m_limbs in (n_limbs, max(n_limbs // 2, 1),
                        max(n_limbs // 7, 1), 1, 25):
            a = rng.getrandbits(n_limbs * 32) | (1 << (n_limbs * 32 - 1))
            b = rng.getrandbits(m_limbs * 32) | (1 << (m_limbs * 32 - 1))
            cases.append((a, b))
    for n_limbs in (24, 25, 48, 500):    # structured worst-carry shapes
        p2 = 1 << (n_limbs * 32 - 1)
        ones = (1 << (n_limbs * 32)) - 1
        cases += [(p2, p2), (ones, ones), (ones, p2), (p2 + 1, ones - 1)]
    big = rng.getrandbits(48 * 32)
    cases += [(big, -big), (-big, -big), (-big, big), (big, 0), (0, 0),
              (1, big), (-1, big), (7, -13)]
    for a, b in cases:
        want = a * b
        for mode in ("plain", "ws", "null", "small"):
            assert _c_mul(a, b, mode) == want, (
                f"mode={mode} a_bits={a.bit_length()} b_bits={b.bit_length()}")


@needs_kara
def test_mul_ws_bound_contract():
    """0 below the crossover (schoolbook needs no scratch); positive and
    sane above it; asymmetric pairs keyed on the smaller operand."""
    bound = _native.LIB.srmech_bigint_mul_ws_bound
    assert int(bound(1, 1)) == 0
    assert int(bound(23, 23)) == 0          # below the measured crossover
    assert int(bound(1000, 4)) == 0         # smaller operand rules
    b24 = int(bound(24, 24))
    b1k = int(bound(1000, 1000))
    assert b24 > 0 and b1k > b24
    # linear-ish scaling: the deepest-path sum is ~4m words + frames
    assert b1k < 64 * 1000 + 8192, "bound should stay O(m) words"


@needs_kara
def test_bigq_mul_dispatch_still_byte_identical_and_exercised():
    """The rc167 Q-dispatch multiply now rides the full-arena Karatsuba
    entry — still byte-identical to Fraction, and the dispatch counter
    still proves the native path runs (no silent fallback)."""
    if not _native.has_native_bigq():
        pytest.skip("bigq core not loaded")
    rng = random.Random(0xBEEF168)
    before = _native.BIGQ_DISPATCH_COUNT
    for bits in (1024, 4096, 40000):
        a_n = rng.getrandbits(bits) | (1 << (bits - 1))
        a_d = rng.getrandbits(bits) | (1 << (bits - 1))
        b_n = rng.getrandbits(bits) | (1 << (bits - 1))
        b_d = rng.getrandbits(bits) | (1 << (bits - 1))
        got = _native.bigq_mul_c(a_n, a_d, b_n, b_d)
        assert got is not None
        want = Fraction(a_n, a_d) * Fraction(b_n, b_d)
        assert got == (want.numerator, want.denominator)
    assert _native.BIGQ_DISPATCH_COUNT > before


@needs_kara
def test_karatsuba_speedup_measured_at_huge_size():
    """The optimization is REAL: at ~2000 limbs (64k bits) the full-arena
    Karatsuba beats forced schoolbook by well over the 1.2x floor asserted
    here (measured ~4-5x on WSL2 gcc -O2; the floor is loose only for CI
    noise — the crossover/speedup table is attested in CHANGELOG rc168)."""
    rng = random.Random(0xFEED168)
    n_bits = 2000 * 32
    a = rng.getrandbits(n_bits) | (1 << (n_bits - 1))
    b = rng.getrandbits(n_bits) | (1 << (n_bits - 1))
    assert _c_mul(a, b, "ws") == _c_mul(a, b, "null") == a * b
    best_school = None
    best_kara = None
    for _trial in range(3):
        t0 = time.perf_counter()
        _c_mul(a, b, "null")
        dt = time.perf_counter() - t0
        best_school = dt if best_school is None or dt < best_school else best_school
        t0 = time.perf_counter()
        _c_mul(a, b, "ws")
        dt = time.perf_counter() - t0
        best_kara = dt if best_kara is None or dt < best_kara else best_kara
    assert best_kara < best_school / 1.2, (
        f"Karatsuba should clearly beat schoolbook at 2000 limbs: "
        f"kara={best_kara*1e3:.2f}ms school={best_school*1e3:.2f}ms")


# ── PART 2: the Q.__pow__ negative-base/negative-exponent fix ───────────────
def test_qpow_negative_base_negative_exponent_bug_case():
    """The exact reported shape: Q(-3, 4) ** -2 must be 16/9 (it raised
    ValueError pre-rc168)."""
    got = Q(-3, 4) ** -2
    assert (got.numerator, got.denominator) == (16, 9)
    want = Fraction(-3, 4) ** -2
    assert got == Q(want.numerator, want.denominator)


def test_qpow_matches_fraction_across_sign_and_exponent_sweep():
    """Byte-identical to Fraction across negative/positive/zero exponents
    x negative/positive bases (both parities of the exponent)."""
    for num in (-7, -3, -2, -1, 1, 2, 3, 9):
        for den in (1, 2, 3, 4, 9):
            for k in range(-6, 7):
                want = Fraction(num, den) ** k
                got = Q(num, den) ** k
                assert (got.numerator, got.denominator) == (
                    want.numerator, want.denominator), (num, den, k)


def test_qpow_integer_valued_rational_exponent_negative_base():
    """An integer-valued rational exponent (Q(-2, 1)) takes the same fixed
    path as a plain int."""
    got = Q(-3, 4) ** Q(-2, 1)
    assert (got.numerator, got.denominator) == (16, 9)
    got = Q(-3, 4) ** Q(-3, 1)
    assert (got.numerator, got.denominator) == (-64, 27)


def test_qpow_zero_base_negative_exponent_still_raises():
    with pytest.raises(ZeroDivisionError):
        Q(0, 1) ** -1


def test_qpow_huge_negative_base_negative_exponent_dispatch_path():
    """The fix holds on the big-operand dispatch path too (>= 1024-bit
    components ride the srmech_bigint composites when native is loaded;
    byte-identical either way)."""
    rng = random.Random(0xD00D168)
    n = -(rng.getrandbits(1200) | (1 << 1199))
    d = rng.getrandbits(1200) | (1 << 1199)
    got = Q(n, d) ** -3
    want = Fraction(n, d) ** -3
    assert (got.numerator, got.denominator) == (
        want.numerator, want.denominator)


def test_qpow_rpow_negative_base_negative_exponent():
    """__rpow__ routes int ** Q(neg, 1) through the fixed __pow__."""
    got = (-2) ** Q(-3, 1)
    assert (got.numerator, got.denominator) == (-1, 8)
    want = Fraction(-2) ** -3
    assert got == Q(want.numerator, want.denominator)
