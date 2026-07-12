"""rc35 — the BIGNUM-EXACT Class-N transcendental Taylor truncations in C.

The exact-rational series in ``srmech.amsc.rational``
(``{exp,sin,cos,log1p,atan}_series_truncate`` + ``rational_pow_uint``) are
exact-rational-IN → exact-rational-OUT with NO magnitude ceiling (CPython
arbitrary-precision ``int``). The original int64/Q61 C peers
(``srmech_exp_series_truncate`` etc.) cap at int64 and return
``SRMECH_ERR_OVERFLOW`` past it, so a C-only host hit a ceiling the Python
path does not — a 1:1-parity VIOLATION.

The rc35 ``*_big`` variants (``srmech_*_series_truncate_big`` /
``srmech_rational_pow_uint_big``) compute the SAME exact rational over the
caller-arena ``srmech_bigint`` (no malloc, no GMP), reduced to lowest terms
with positive denominator — byte-identical to the Python ``(num, den)`` at
ANY magnitude. This test pins that byte-parity, with KEYSTONE cases whose
exact ``(num, den)`` exceeds ``2**64`` in numerator or denominator (proving
the ceiling is gone). The pure-Python bignum body is the parity oracle.

numpy-free + skipped cleanly when the native lib (or the rc35 symbols) is
absent — but it MUST run + pass when the native lib is loaded.
"""

from __future__ import annotations

from srmech.amsc import _native
from srmech.amsc import rational

import pytest


_INT64_CEIL = 1 << 64


def _exceeds_int64(num: int, den: int) -> bool:
    """True iff the exact (num, den) escapes the old int64/u64 C ceiling."""
    return abs(num) > _INT64_CEIL or den > _INT64_CEIL


pytestmark = pytest.mark.skipif(
    not _native.has_native_bigexp(),
    reason=(
        "native srmech bignum-exact transcendentals (rc35 *_big symbols) not "
        "loaded; the pure-Python bignum path in srmech.amsc.rational is the "
        "only path (and is itself the parity oracle this test would check "
        "against). Skipped — never xfailed."
    ),
)


# ──────────────────────────────────────────────────────────────────────
# Per-op (input, expected-keystone) parameter tables. Each row is
# (p, q, N). The Python op is the oracle; the C *_big result must equal
# it byte-for-byte. The KEYSTONE rows (marked below) overflow int64.
# ──────────────────────────────────────────────────────────────────────

_EXP_CASES = [
    (1, 1, 10), (1, 2, 5), (0, 1, 5),
    (7, 3, 30),       # KEYSTONE: ~148-bit numerator
    (-5, 2, 25),      # KEYSTONE: negative base, >int64
    (355, 113, 40),   # KEYSTONE: ~409-bit numerator
    (13, 7, 80),      # KEYSTONE: ~600-bit numerator
    (1, 1, 100),      # KEYSTONE
    (-1, 1, 3),
]

_SIN_CASES = [
    (1, 1, 5), (0, 1, 5),
    (1, 2, 10),       # KEYSTONE
    (7, 3, 40),       # KEYSTONE: ~496-bit
    (-5, 4, 30),      # KEYSTONE
]

_COS_CASES = [
    (1, 1, 5), (0, 1, 5),
    (1, 2, 10),       # KEYSTONE
    (7, 3, 40),       # KEYSTONE: ~488-bit
    (-5, 4, 30),      # KEYSTONE
]

# log1p domain: -1 < p/q ≤ 1.
_LOG1P_CASES = [
    (0, 1, 10),
    (1, 2, 40),       # KEYSTONE
    (1, 1, 60),       # KEYSTONE: boundary x = 1 (log 2)
    (-1, 2, 50),      # KEYSTONE
    (3, 7, 64),       # KEYSTONE: ~258-bit, max N
]

# atan domain: |p/q| ≤ 1.
_ATAN_CASES = [
    (0, 1, 10),
    (1, 1, 40),       # KEYSTONE: boundary x = 1 (π/4)
    (1, 2, 50),       # KEYSTONE
    (-1, 1, 60),      # KEYSTONE
    (355, 452, 64),   # KEYSTONE: ~1294-bit numerator, max N
]

_POW_CASES = [
    (2, 3, 10), (5, 1, 1), (7, 3, 0),
    (7, 5, 40),       # KEYSTONE: ~113-bit
    (-3, 4, 33),      # KEYSTONE: negative base
    (10, 9, 100),     # KEYSTONE: ~333-bit
]


def _assert_parity(symbol, py_result, p, q, N):
    c = _native._bigexp_call(symbol, p, q, N)
    assert c is not None, (
        f"has_native_bigexp() True but {symbol} returned None"
    )
    assert c == py_result, (
        f"{symbol}({p}/{q}, N={N}): C {c} != Python oracle {py_result}"
    )
    # Reduced-form invariants the C must honour (matches Python).
    out_num, out_den = c
    assert out_den > 0, f"{symbol}: denominator must be positive, got {out_den}"
    if out_num == 0:
        assert out_den == 1, f"{symbol}: 0 must reduce to 0/1, got 0/{out_den}"


@pytest.mark.parametrize("p,q,N", _EXP_CASES)
def test_exp_series_truncate_big_parity(p, q, N):
    _assert_parity("srmech_exp_series_truncate_big",
                   rational.exp_series_truncate(p, q, N), p, q, N)


@pytest.mark.parametrize("p,q,N", _SIN_CASES)
def test_sin_series_truncate_big_parity(p, q, N):
    _assert_parity("srmech_sin_series_truncate_big",
                   rational.sin_series_truncate(p, q, N), p, q, N)


@pytest.mark.parametrize("p,q,N", _COS_CASES)
def test_cos_series_truncate_big_parity(p, q, N):
    _assert_parity("srmech_cos_series_truncate_big",
                   rational.cos_series_truncate(p, q, N), p, q, N)


@pytest.mark.parametrize("p,q,N", _LOG1P_CASES)
def test_log1p_series_truncate_big_parity(p, q, N):
    _assert_parity("srmech_log1p_series_truncate_big",
                   rational.log1p_series_truncate(p, q, N), p, q, N)


@pytest.mark.parametrize("p,q,N", _ATAN_CASES)
def test_atan_series_truncate_big_parity(p, q, N):
    _assert_parity("srmech_atan_series_truncate_big",
                   rational.atan_series_truncate(p, q, N), p, q, N)


@pytest.mark.parametrize("p,q,e", _POW_CASES)
def test_rational_pow_uint_big_parity(p, q, e):
    _assert_parity("srmech_rational_pow_uint_big",
                   rational.rational_pow_uint((p, q), e), p, q, e)


# ──────────────────────────────────────────────────────────────────────
# The keystone: at least one case PER OP whose exact (num, den) exceeds
# 2**64, proving the C bignum path has no int64 ceiling.
# ──────────────────────────────────────────────────────────────────────

def test_keystone_exp_exceeds_int64():
    """exp(355/113, N=40): the exact numerator is ~409 bits (> 2**64), and the
    C bignum result equals the Python (num, den) EXACTLY — no ceiling."""
    py = rational.exp_series_truncate(355, 113, 40)
    assert _exceeds_int64(*py), "test case must exceed int64 to be a keystone"
    c = _native._bigexp_call("srmech_exp_series_truncate_big", 355, 113, 40)
    assert c == py


def test_keystone_every_op_has_an_over_int64_case():
    """Each of the six ops has at least one parametrised case whose Python
    oracle output exceeds int64 — the structural guarantee that this suite
    actually exercises the bignum (no-ceiling) regime per op."""
    checks = [
        (rational.exp_series_truncate, _EXP_CASES),
        (rational.sin_series_truncate, _SIN_CASES),
        (rational.cos_series_truncate, _COS_CASES),
        (rational.log1p_series_truncate, _LOG1P_CASES),
        (rational.atan_series_truncate, _ATAN_CASES),
    ]
    for fn, cases in checks:
        assert any(_exceeds_int64(*fn(p, q, N)) for (p, q, N) in cases), (
            f"{fn.__name__}: no parametrised case exceeds int64"
        )
    assert any(
        _exceeds_int64(*rational.rational_pow_uint((p, q), e))
        for (p, q, e) in _POW_CASES
    ), "rational_pow_uint: no parametrised case exceeds int64"


def test_native_bignum_matches_python_negative_and_zero():
    """Sign + zero edge cases byte-parity (the divmod-alias sign bug regression
    guard): exp(-5/2, N=1) = -3/2, sin(0) = 0/1, cos(0) = 1/1."""
    assert _native._bigexp_call("srmech_exp_series_truncate_big", -5, 2, 1) \
        == rational.exp_series_truncate(-5, 2, 1) == (-3, 2)
    assert _native._bigexp_call("srmech_sin_series_truncate_big", 0, 1, 5) \
        == (0, 1)
    assert _native._bigexp_call("srmech_cos_series_truncate_big", 0, 1, 5) \
        == (1, 1)
