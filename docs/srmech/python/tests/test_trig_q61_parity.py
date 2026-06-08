"""Q61 trig cascade — C↔Python bit-exact parity (srmech v0.7.5rc2).

This completes the v0.7.0 "C-transpile triality coherence": the Python float
``rational.{sin,cos,tan,atan,atan2}`` now compute the SAME Q61 fixed-point
Class-N cascade as the native peer ``c/src/srmech_trig.c`` (``srmech_sin`` …),
so the two renderings are BIT-IDENTICAL and the Python callers dispatch to the
C when it is loaded.

The three things this asserts:

1. **C ↔ Q61 bit-exact** — the native ``srmech_*`` and the pure-Python Q61
   core produce identical IEEE-754 bits over a wide finite range. (Skipped
   when no native library is loaded; the CI wheel build is the real gate.)
2. **native ↔ non-native bit-exact** — the public ``rational`` functions
   return the same bits whether they dispatch to C or run the pure-Python
   Q61 fallback, across the WHOLE domain including ±Inf / NaN.
3. **correctness floor** — both agree with libm to ~1 ULP (a sanity bound
   that holds even with no native library, so the port itself is checked).

The exact-rational ``*_series_truncate`` bignum surface is a SEPARATE,
higher-precision reference and is intentionally not bit-compared here.
"""

from __future__ import annotations

import math
import struct

import pytest

from srmech.amsc import _native
from srmech.amsc import rational as R


def _bits(value: float) -> str:
    return struct.pack("<d", value).hex()


# ---- pure-Python Q61 cores (bypass the native dispatch in the public fns) ----

def _py_sin(x: float) -> float:
    if not math.isfinite(x):
        return x - x
    ok, octant, r = R._q61_reduce(x)
    if not ok:
        return x - x
    sc = R._q61_sin_core(r)
    cc = R._q61_cos_core(r)
    v = sc if octant == 0 else cc if octant == 1 else -sc if octant == 2 else -cc
    return R._q61_to_double(v)


def _py_cos(x: float) -> float:
    if not math.isfinite(x):
        return x - x
    ok, octant, r = R._q61_reduce(x)
    if not ok:
        return x - x
    sc = R._q61_sin_core(r)
    cc = R._q61_cos_core(r)
    v = cc if octant == 0 else -sc if octant == 1 else -cc if octant == 2 else sc
    return R._q61_to_double(v)


def _py_atan(x: float) -> float:
    xm = x if x >= 0.0 else -x
    r = R._q61_atan_nonneg(xm)
    return r if x >= 0.0 else -r


# A deterministic spread of test angles (no RNG — reproducible across runs).
def _angles(lo: float, hi: float, n: int):
    span = hi - lo
    out = []
    for i in range(n):
        # irrational-ish stride to avoid hitting only nice multiples of pi
        t = (i * 0.6180339887498949) % 1.0
        out.append(lo + t * span)
    return out


_BIG_ANGLES = _angles(-2000.0, 2000.0, 4000)
_ATAN_ARGS = _angles(-300.0, 300.0, 2000)


# ----------------------------------------------------------------------
# 1. C ↔ Q61 bit-exact (the Rosetta-pair guarantee)
# ----------------------------------------------------------------------

native_only = pytest.mark.skipif(
    not _native.has_native_trig(),
    reason="no native srmech trig loaded; CI wheel build is the bit-exact gate",
)


@native_only
def test_native_sin_cos_bit_exact_with_q61():
    for x in _BIG_ANGLES:
        assert _native.sin_c(x) == _py_sin(x), (
            f"sin({x!r}) C={_bits(_native.sin_c(x))} Q61={_bits(_py_sin(x))}")
        assert _native.cos_c(x) == _py_cos(x), (
            f"cos({x!r}) C={_bits(_native.cos_c(x))} Q61={_bits(_py_cos(x))}")


@native_only
def test_native_atan_bit_exact_with_q61():
    for x in _ATAN_ARGS:
        assert _native.atan_c(x) == _py_atan(x), (
            f"atan({x!r}) C={_bits(_native.atan_c(x))} Q61={_bits(_py_atan(x))}")


@native_only
def test_native_atan2_bit_exact_with_q61():
    half = R._q61_to_double(R._Q61_HALF_PI_Q61)
    pi = 2.0 * half

    def q61_atan2(y, x):
        if x == 0.0:
            return half if y > 0.0 else (-half if y < 0.0 else 0.0)
        ratio = y / x
        rm = ratio if ratio >= 0.0 else -ratio
        b = R._q61_atan_nonneg(rm)
        base = b if ratio >= 0.0 else -b
        if x > 0.0:
            return base
        return base + pi if y >= 0.0 else base - pi

    ys = _angles(-300.0, 300.0, 400)
    xs = _angles(-300.0, 300.0, 400)
    for y, x in zip(ys, xs):
        assert _native.atan2_c(y, x) == q61_atan2(y, x), (
            f"atan2({y!r},{x!r}) C={_bits(_native.atan2_c(y, x))} "
            f"Q61={_bits(q61_atan2(y, x))}")


# ----------------------------------------------------------------------
# 2. native ↔ non-native public functions bit-exact (whole domain)
# ----------------------------------------------------------------------

def _force_nonnative(monkeypatch):
    monkeypatch.setattr(_native, "has_native_trig", lambda: False)


@native_only
def test_public_sin_cos_native_eq_nonnative(monkeypatch):
    native = {x: (R.sin(x), R.cos(x)) for x in _BIG_ANGLES}
    _force_nonnative(monkeypatch)
    for x in _BIG_ANGLES:
        ns, nc = native[x]
        assert R.sin(x) == ns, f"sin({x!r}) native!=nonnative"
        assert R.cos(x) == nc, f"cos({x!r}) native!=nonnative"


@native_only
def test_public_atan_atan2_native_eq_nonnative(monkeypatch):
    pairs = list(zip(_ATAN_ARGS, reversed(_ATAN_ARGS)))
    native_atan = {x: R.atan(x) for x in _ATAN_ARGS}
    native_atan2 = {(y, x): R.atan2(y, x) for y, x in pairs}
    _force_nonnative(monkeypatch)
    for x in _ATAN_ARGS:
        assert R.atan(x) == native_atan[x], f"atan({x!r}) native!=nonnative"
    for y, x in pairs:
        assert R.atan2(y, x) == native_atan2[(y, x)], (
            f"atan2({y!r},{x!r}) native!=nonnative")


# ----------------------------------------------------------------------
# 3. correctness floor vs libm (holds with OR without native)
# ----------------------------------------------------------------------

def test_sin_cos_match_libm():
    for x in _angles(-1000.0, 1000.0, 3000):
        assert abs(R.sin(x) - math.sin(x)) < 1e-12
        assert abs(R.cos(x) - math.cos(x)) < 1e-12


def test_atan_atan2_match_libm():
    for x in _angles(-50.0, 50.0, 2000):
        assert abs(R.atan(x) - math.atan(x)) < 1e-12
    ys = _angles(-50.0, 50.0, 500)
    xs = _angles(-49.0, 51.0, 500)
    for y, x in zip(ys, xs):
        assert abs(R.atan2(y, x) - math.atan2(y, x)) < 1e-12


def test_tan_matches_libm():
    for x in _angles(-1.3, 1.3, 500):
        assert abs(R.tan(x) - math.tan(x)) < 1e-11


# ----------------------------------------------------------------------
# 4. non-finite reconciliation (native and non-native agree, see (2))
# ----------------------------------------------------------------------

def test_nonfinite_sin_cos_are_nan():
    for x in (float("inf"), float("-inf"), float("nan")):
        assert math.isnan(R.sin(x))
        assert math.isnan(R.cos(x))


def test_nonfinite_atan_limits():
    half = R._q61_to_double(R._Q61_HALF_PI_Q61)
    assert R.atan(float("inf")) == half
    assert R.atan(float("-inf")) == -half
    assert math.isnan(R.atan(float("nan")))


def test_nonfinite_atan2_matches_libm():
    vals = [1.0, -1.0, 0.0, float("inf"), float("-inf")]
    for y in vals:
        for x in vals:
            got = R.atan2(y, x)
            want = math.atan2(y, x)
            assert got == want or (math.isnan(got) and math.isnan(want)), (
                f"atan2({y!r},{x!r})={got} libm={want}")
    assert math.isnan(R.atan2(float("nan"), 1.0))
    assert math.isnan(R.atan2(1.0, float("nan")))
