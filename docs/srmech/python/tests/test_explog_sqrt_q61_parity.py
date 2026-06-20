"""Q61 exp/log/sqrt cascade — C↔Python bit-exact parity (srmech v0.7.5rc3).

Completes the v0.7.0 C-transpile for the *aperiodic* transcendentals. The
Python float ``rational.{exp,log,sqrt}`` now compute the SAME algorithm as the
native peers ``c/src/srmech_explog.c`` (``srmech_exp``/``srmech_log``, Cody-Waite
ln2 reduction + Q61 series) and ``c/src/srmech_sqrt.c``
(``srmech_rational_sqrt``, IEEE-bit ``M·2^e`` + ``isqrt(M<<2K)``, K=27), so the
two renderings are BIT-IDENTICAL and the Python callers dispatch to C.

Notes captured by this rc:
- ``rational.log`` is NEW — the notebook listed it as ``srmech_log``'s Python
  peer (a Rosetta pair) but the Python half was missing.
- ``rational.exp`` was REPLACED: the old argument-halving + square-k-times
  reduction amplified error to ~345 ULP; the Cody-Waite ln2 reduction (what
  the C + notebook specify) holds ~1 ULP. This test pins the ~1 ULP floor.

Asserts: (1) C↔Q61 bit-exact, (2) native↔non-native bit-exact, (3) libm
correctness floor (holds with or without the native lib). The exact-rational
``exp_series_truncate`` / ``log1p_series_truncate`` and the ``precision_bits``
sqrt path are the separate higher-precision REFERENCE surfaces (not bit-compared).
"""

from __future__ import annotations

import math
import struct

import pytest

from srmech.amsc import _native
from srmech.amsc import rational as R


def _bits(value: float) -> str:
    return struct.pack("<d", value).hex()


def _vals(lo: float, hi: float, n: int):
    span = hi - lo
    return [lo + ((i * 0.6180339887498949) % 1.0) * span for i in range(n)]


_EXP_ARGS = _vals(-300.0, 300.0, 4000)
_POS_ARGS = [10.0 ** e for e in _vals(-9.0, 9.0, 4000)]   # log/sqrt domain, wide


native_explog = pytest.mark.skipif(
    not _native.has_native_explog(),
    reason="no native srmech exp/log loaded; CI wheel build is the bit-exact gate",
)
native_sqrt = pytest.mark.skipif(
    not _native.has_native_sqrt(),
    reason="no native srmech sqrt loaded; CI wheel build is the bit-exact gate",
)


# ---- 1. C ↔ Q61 bit-exact (forcing the pure-Python path via monkeypatch) ----

# rc7: ``R.{exp,log,sqrt}`` return an exact ``Q``; the native ``*_c`` helpers
# return a ``float``. The C↔Q61 "bit-exact" claim is about the FLOAT PROJECTION
# of the exact Q being byte-identical to the native double, so collapse the Q
# with ``float()`` at the comparison (``Q == <native float>`` is an exact
# cross-multiply and the exact rational != the rounded double by design).

@native_explog
def test_exp_native_bit_exact_with_q61(monkeypatch):
    native = {x: _native.exp_c(x) for x in _EXP_ARGS}
    monkeypatch.setattr(_native, "has_native_explog", lambda: False)
    for x in _EXP_ARGS:
        assert float(R.exp(x)) == native[x], (
            f"exp({x!r}) C={_bits(native[x])} Q61={_bits(R.exp(x))}")


@native_explog
def test_log_native_bit_exact_with_q61(monkeypatch):
    # rc7 changed log's ``e·ln2`` recombine from the legacy two-word-FLOAT ln2
    # (which the old native float ``log_c`` still uses) to an EXACT Q61-INTEGER
    # ln2 (``_Q61_LN2``). For inputs with ``e != 0`` the two valid algorithms
    # round the last mantissa bit differently, so the Q61 float projection sits
    # within **1 ULP** of legacy ``log_c`` (both within 1 ULP of libm; exp/sqrt
    # stay byte-exact because their 2^n recombine is an exact power-of-two, no
    # irrational ln2 multiply). The byte-exact peer for the Q61 log is the rc7
    # ``srmech_log_q61`` (see test_native_q61_parity_rc7.py); legacy ``log_c`` is
    # the ≤1-ULP reference here.
    native = {x: _native.log_c(x) for x in _POS_ARGS}
    monkeypatch.setattr(_native, "has_native_explog", lambda: False)
    for x in _POS_ARGS:
        got = float(R.log(x))
        assert abs(got - native[x]) <= math.ulp(native[x]), (
            f"log({x!r}) >1ULP: C={_bits(native[x])} Q61={_bits(got)}")


@native_sqrt
def test_sqrt_native_bit_exact_with_q61(monkeypatch):
    native = {x: _native.rational_sqrt_c(x) for x in _POS_ARGS}
    monkeypatch.setattr(_native, "has_native_sqrt", lambda: False)
    for x in _POS_ARGS:
        assert float(R.sqrt(x)) == native[x], (
            f"sqrt({x!r}) C={_bits(native[x])} Q61={_bits(R.sqrt(x))}")


# ---- 2. correctness floor vs libm (holds with OR without native) ----

def test_exp_matches_libm():
    for x in _vals(-300.0, 300.0, 3000):
        want = math.exp(x)
        assert abs(R.exp(x) - want) <= 4e-16 * (want or 1.0)


def test_log_matches_libm():
    for x in _POS_ARGS[:3000]:
        assert abs(R.log(x) - math.log(x)) <= 6e-15


def test_sqrt_matches_libm():
    for x in _POS_ARGS[:3000]:
        want = math.sqrt(x)
        assert abs(R.sqrt(x) - want) <= 4e-16 * want


def test_exp_log_round_trip():
    for x in _vals(-50.0, 50.0, 1000):
        assert abs(R.log(R.exp(x)) - x) <= 3e-13 * (abs(x) or 1.0)


# ---- 3. edge cases (native and non-native agree, all guarded before dispatch) ----

def test_exp_edges():
    assert R.exp(0.0) == 1.0
    # rc7 stay-rational: a non-finite x raises (Q is the finite-rational carrier).
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            R.exp(bad)
    # No DBL_MAX overflow/underflow gate (that was a float artefact): a finite x
    # gives the EXACT (huge / tiny) finite rational, never inf / 0. Check the
    # exact (num, den) directly so no float() projection overflows.
    big_n, big_d = R.exp(1000.0).as_pair()
    assert big_n > big_d > 0                        # exp(1000) > 1, exact rational
    tiny_n, tiny_d = R.exp(-1000.0).as_pair()
    assert 0 < tiny_n and tiny_d > tiny_n           # 0 < exp(-1000) < 1, exact rational


def test_log_edges():
    assert R.log(1.0) == 0.0
    # rc7: x <= 0 and non-finite raise (none of -inf / nan is a rational).
    for bad in (float("nan"), -1.0, 0.0, float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            R.log(bad)


def test_sqrt_edges():
    assert R.sqrt(0.0) == 0.0
    assert R.sqrt(4.0) == 2.0
    # rc7: negative AND non-finite raise (Q is the finite-rational carrier).
    for bad in (-1.0, float("inf"), float("-inf"), float("nan")):
        with pytest.raises(ValueError):
            R.sqrt(bad)


def test_sqrt_precision_bits_reference_is_separate():
    # The default cascade is the C-bit-exact K=27 path; precision_bits selects
    # the higher-precision bignum reference (may differ in the last ULP).
    ref = R.sqrt(2.0, precision_bits=64)
    assert abs(ref - math.sqrt(2.0)) <= 1e-15
    assert R.hypot(3.0, 4.0) == 5.0
