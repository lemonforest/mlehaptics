"""0.9.0rc169 — the sub-quadratic (Lehmer) ``srmech_bigint_gcd``.

rc168 made the multiply Karatsuba and its honest measurement showed the
whole big-ℚ op had become GCD-BOUND (the plain-Euclid reduce dominated
above ~1024 bits). This rc replaces that plain Euclid with LEHMER'S
algorithm (Knuth TAOCP Vol 2 §4.5.2 Algorithm L): the two leading 30-bit
"digits" of x, y drive a single/double-word simulation that builds a 2x2
cofactor matrix, applied to the FULL bignums in ONE fused multiply-add
pass — batching ~30 bits of Euclid steps and replacing the per-step
full-precision divmod. Same O(n^2) class, a tiny constant.

The contract this file pins:

* BYTE-IDENTICAL to Euclid / ``math.gcd`` (the gcd value is unique) for
  every input — small, huge, coprime, one-divides-the-other, both-even,
  powers of two, and the Fibonacci-adjacent Euclid worst case.
* Both the Lehmer fast path (a bound-sized arena) AND the lean-Euclid
  fallback (a tight arena) return that identical value.
* ``srmech_bigint_gcd_ws_bound`` is a sane, positive, engaging bound.
* The rc167 big-ℚ dispatch (``bigq_reduce_c`` / ``bigint_gcd_c``) is
  still byte-identical AND counter-proven exercised (no silent fallback).
* The Lehmer path is measurably faster than forced lean Euclid at a
  huge size (a loose CI-noise floor; the attested table is in CHANGELOG).

⚠️ Sparse-tower guardrail: the gcd is the SCALAR bignum layer, below the
carriers. It densifies no sparse encoding (carrier ladders / CRT / theta-
sparse / Laplacian-eigenbasis are untouched by construction).

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import ctypes
import importlib.util
import math
import random
import time

import pytest

from srmech.amsc import _native

_HAS_GCD = bool(
    _native.HAS_NATIVE and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_bigint_gcd"))
_HAS_BOUND = _HAS_GCD and hasattr(_native.LIB, "srmech_bigint_gcd_ws_bound")

needs_gcd = pytest.mark.skipif(
    not _HAS_GCD, reason="srmech_bigint_gcd not loaded")
needs_bound = pytest.mark.skipif(
    not _HAS_BOUND, reason="rc169 srmech_bigint_gcd_ws_bound not loaded")


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "the rc169 tests must run on the numpy-ABSENT matrix")


# ── drive srmech_bigint_gcd directly through the limb marshal ────────────────
def _limbs(v: int) -> int:
    return max((v.bit_length() + 31) // 32, 1)


def _gcd_c(a: int, b: int, words: "int | None" = None) -> int:
    """gcd(a, b) via srmech_bigint_gcd. ``words`` None → a bound-sized arena
    (the Lehmer fast path); an explicit small ``words`` (< the engage
    threshold, >= the lean need) exercises the lean-Euclid fallback."""
    lib = _native.LIB
    an, bn = _limbs(a), _limbs(b)
    m = max(an, bn)
    a_bi, _ka = _native._bigint_from_int(a, an + 1)
    b_bi, _kb = _native._bigint_from_int(b, bn + 1)
    g_bi, _kg = _native._bigint_from_int(0, m + 2)
    if words is None:
        wl = int(lib.srmech_bigint_gcd_ws_bound(an, bn)) if _HAS_BOUND \
            else (8 * (m + 8) + 64) * 4
    else:
        wl = words * 4
    ws = (ctypes.c_uint8 * wl)()
    rc = lib.srmech_bigint_gcd(
        ctypes.byref(g_bi), ctypes.byref(a_bi), ctypes.byref(b_bi),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(wl))
    assert rc == _native.SRMECH_OK, f"gcd rc={rc}"
    return _native._bigint_to_int(g_bi)


def _both_paths(a: int, b: int) -> None:
    """Lehmer path AND lean-Euclid fallback both == math.gcd (byte-identity:
    an integer's normalised limb sequence is unique, so value equality IS
    limb equality)."""
    want = math.gcd(a, b)
    assert _gcd_c(a, b) == want, f"lehmer a_bits={a.bit_length()}"
    m = max(_limbs(a), _limbs(b))
    if m >= 3:                       # 6m+20 is < engage (6m+28), >= lean (6m+6)
        assert _gcd_c(a, b, 6 * m + 20) == want, f"lean a_bits={a.bit_length()}"


@needs_gcd
def test_gcd_byte_identical_random_balanced_and_asymmetric():
    rng = random.Random(0xC169)
    for nb in (32, 64, 128, 256, 512, 1024, 4096, 16384):
        for mb in (nb, max(nb // 2, 1), max(nb // 7, 1), 1, 200):
            a = rng.getrandbits(nb) | (1 << (nb - 1))
            b = rng.getrandbits(mb) | (1 << (mb - 1))
            _both_paths(a, b)


@needs_gcd
def test_gcd_byte_identical_structured_shapes():
    rng = random.Random(0x5EED169)
    # coprime consecutive integers
    for nb in (64, 512, 4096, 20000):
        x = rng.getrandbits(nb) | (1 << (nb - 1))
        assert _gcd_c(x, x + 1) == 1
        _both_paths(x, x + 1)
    # one divides the other: gcd(x, k*x) = x
    for nb in (64, 1024, 8000):
        x = rng.getrandbits(nb) | (1 << (nb - 1))
        k = rng.getrandbits(50) | 1
        assert _gcd_c(x, k * x) == x
        _both_paths(x, k * x)
    # both even: gcd(2x, 2y) = 2*gcd(x, y)
    for nb in (128, 4096):
        x = rng.getrandbits(nb) | (1 << (nb - 1))
        y = rng.getrandbits(nb) | (1 << (nb - 1))
        _both_paths(2 * x, 2 * y)
    # powers of two
    _both_paths(1 << 300, 1 << 180)
    _both_paths(1 << 20000, 1 << 9001)


@needs_gcd
def test_gcd_byte_identical_fibonacci_worst_case():
    """Consecutive Fibonacci numbers are the Euclid WORST case (every
    partial quotient 1); gcd == 1, and Lehmer batches the whole chain."""
    def fibpair(n: int) -> "tuple[int, int]":
        a, b = 1, 1
        for _ in range(n - 2):
            a, b = a + b, a
        return a, b
    for n in (50, 500, 3000, 15000):
        fa, fb = fibpair(n)
        assert math.gcd(fa, fb) == 1
        assert _gcd_c(fa, fb) == 1
        _both_paths(fa, fb)


@needs_gcd
def test_gcd_edge_cases_zero_and_small():
    for a, b in [(0, 0), (0, 5), (5, 0), (1, 1), (48, 18), (1071, 462),
                 (2**64 - 59, 2**64 - 83)]:
        assert _gcd_c(a, b) == math.gcd(a, b)


@needs_bound
def test_gcd_ws_bound_contract():
    bound = _native.LIB.srmech_bigint_gcd_ws_bound
    b1 = int(bound(1, 1))
    b1k = int(bound(1000, 1000))
    assert b1 > 0 and b1k > b1                       # positive, grows with m
    assert b1k < 64 * 1000 + 4096                    # stays O(m) words
    assert int(bound(1000, 4)) == int(bound(4, 1000))  # keyed on max(a_n, b_n)
    # the bound must actually ENGAGE Lehmer AND be sufficient (no overflow):
    rng = random.Random(0xB0169)
    a = rng.getrandbits(4096) | (1 << 4095)
    b = rng.getrandbits(4096) | (1 << 4095)
    assert _gcd_c(a, b) == math.gcd(a, b)            # ran clean at the bound


@needs_gcd
def test_bigq_dispatch_gcd_still_byte_identical_and_exercised():
    """The rc167 big-ℚ gcd dispatch (bigint_gcd_c / bigq_reduce_c) rides the
    new Lehmer gcd — still byte-identical, still counter-proven exercised."""
    if not _native.has_native_bigq():
        pytest.skip("bigq core not loaded")
    rng = random.Random(0xBEEF169)
    before = _native.BIGQ_DISPATCH_COUNT
    for bits in (1100, 4096, 40000):
        a = rng.getrandbits(bits) | (1 << (bits - 1))
        b = rng.getrandbits(bits) | (1 << (bits - 1))
        assert _native.bigint_gcd_c(a, b) == math.gcd(a, b)
        # a reducible fraction: reduce must strip the shared factor
        g = rng.getrandbits(bits // 2) | 1
        num, den = g * a, g * b
        got = _native.bigq_reduce_c(num, den)
        red = math.gcd(num, den)
        assert got == (num // red, den // red)
    assert _native.BIGQ_DISPATCH_COUNT > before


@needs_bound
def test_lehmer_faster_than_lean_euclid_at_huge_size():
    """The optimization is REAL: at ~2000 limbs (64k bits) the Lehmer path
    beats forced lean Euclid by well over the 1.3x floor asserted here
    (measured ~7x on WSL2 gcc -O2; the crossover table is in CHANGELOG)."""
    rng = random.Random(0xFEED169)
    nb = 2000 * 32
    a = rng.getrandbits(nb) | (1 << (nb - 1))
    b = rng.getrandbits(nb) | (1 << (nb - 1))
    m = max(_limbs(a), _limbs(b))
    assert _gcd_c(a, b) == _gcd_c(a, b, 6 * m + 20) == math.gcd(a, b)
    best_leh = best_euc = None
    for _ in range(3):
        t0 = time.perf_counter(); _gcd_c(a, b); dt = time.perf_counter() - t0
        best_leh = dt if best_leh is None or dt < best_leh else best_leh
        t0 = time.perf_counter(); _gcd_c(a, b, 6 * m + 20)
        dt = time.perf_counter() - t0
        best_euc = dt if best_euc is None or dt < best_euc else best_euc
    assert best_leh < best_euc / 1.3, (
        f"Lehmer should clearly beat lean Euclid at 2000 limbs: "
        f"lehmer={best_leh*1e3:.2f}ms euclid={best_euc*1e3:.2f}ms")
