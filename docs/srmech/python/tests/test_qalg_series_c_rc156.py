"""Qalg TAIL Batch 1a (0.9.0rc156): the 6 exact-ℚ bignum oracles earn a
``srmech_bigint``-backed C path — ``bignum_reference → c_dispatched``.

The 5 exact-rational Taylor oracles
``srmech.amsc.rational.{exp,sin,cos,log1p,atan}_series_truncate`` now dispatch to
the caller-arena ``srmech_bigint`` C peers
``srmech_{exp,sin,cos,log1p,atan}_series_truncate_big`` (byte-identical ``(num,
den)`` at ANY magnitude — no int64/Q61 ceiling), and ``srmech.qm.bell.
tsirelson_bound`` (2√2) reaches C because ``rational.sqrt``'s precision integer-
sqrt path (``_integer_sqrt`` for ``n >= 2**128``) now dispatches to
``srmech_bigint_isqrt``.

This test pins:
  1. the native symbols are actually loaded (so parity exercises C, not a silent
     pure fallback on BOTH sides);
  2. native == FORCED-PURE is EXACT / BYTE-IDENTICAL (these are exact ℚ, not
     float) across a range of ``(num, den, num_terms)`` per op;
  3. the value oracles (``exp(1,1,20)≈e``, ``atan(1,1,·)→π/4``, ``cos(0)=1``,
     ``log1p(0)=0``, ``tsirelson=2√2``);
  4. the series LOGIC is genuinely C-reachable (the raw ``_bigexp_call`` /
     ``bigint_isqrt_c`` helpers compute the exact result with no Python bignum);
  5. the 6 Rosetta rows are ``c_dispatched``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import rational as R
from srmech.qm import bell


# (name, fn, max_terms) for the 5 series ops.
_SERIES = [
    ("exp", R.exp_series_truncate, 512),
    ("sin", R.sin_series_truncate, 50),
    ("cos", R.cos_series_truncate, 50),
    ("log1p", R.log1p_series_truncate, 64),
    ("atan", R.atan_series_truncate, 64),
]


def _in_domain_num(name: str, den: int, rng: random.Random) -> int:
    """Draw an in-domain numerator for op ``name`` with denominator ``den``.

    log1p domain is -1 < p/q <= 1  → -den < num <= den.
    atan domain is  |p/q| <= 1     → -den <= num <= den.
    exp/sin/cos are globally convergent (any p/q); keep magnitudes moderate.
    """
    if name == "log1p":
        return rng.randrange(-den + 1, den + 1)
    if name == "atan":
        return rng.randrange(-den, den + 1)
    return rng.randrange(-40, 41)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbols_present():
    # The C foundation is actually loaded, so the parity tests exercise C.
    assert _native.has_native_bigexp()
    assert _native.has_native_bigint_isqrt()
    # The raw *_big helpers compute the exact rational with no Python bignum.
    assert _native._bigexp_call(
        "srmech_exp_series_truncate_big", 1, 1, 20) is not None
    assert _native.bigint_isqrt_c(2 ** 129) == R._py_isqrt(2 ** 129)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("name,fn,max_terms", _SERIES)
def test_series_native_equals_pure_byte_identical(name, fn, max_terms):
    """native == FORCED-PURE EXACT (num, den) across a range of inputs."""
    rng = random.Random(0xC156 ^ hash(name) & 0xFFFF)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(120):
            den = rng.randrange(1, 41)
            num = _in_domain_num(name, den, rng)
            terms = rng.randrange(0, max_terms + 1)
            _native.HAS_NATIVE = True
            nat = fn(num, den, terms)
            _native.HAS_NATIVE = False
            pure = fn(num, den, terms)
            _native.HAS_NATIVE = saved
            assert nat == pure, (name, num, den, terms, nat, pure)
            # positive denominator + lowest terms (canonical exact rational)
            assert nat[1] > 0
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("name,fn,max_terms", _SERIES)
def test_series_edge_terms_native_equals_pure(name, fn, max_terms):
    """Edge N (0, 1, the per-op cap) + a large-magnitude case stay byte-identical."""
    saved = _native.HAS_NATIVE
    cases = [(1, 1, 0), (1, 1, 1), (7, 3, max_terms), (-5, 6, max_terms)]
    if name == "exp":
        cases.append((3, 1, 200))          # far past the int64 fast-path ceiling
    try:
        for num, den, terms in cases:
            # keep atan/log1p in-domain (|x|<=1)
            if name in ("log1p", "atan") and abs(num) > den:
                num = den if name == "log1p" else den
            _native.HAS_NATIVE = True
            nat = fn(num, den, terms)
            _native.HAS_NATIVE = False
            pure = fn(num, den, terms)
            _native.HAS_NATIVE = saved
            assert nat == pure, (name, num, den, terms, nat, pure)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_integer_sqrt_bignum_native_equals_pure():
    """_integer_sqrt's bignum branch (n >= 2^128) is byte-identical to _py_isqrt."""
    rng = random.Random(20260706)
    for _ in range(64):
        bits = rng.randrange(129, 900)
        n = rng.getrandbits(bits)
        r = _native.bigint_isqrt_c(n)
        assert r == R._py_isqrt(n)
        # floor property: r^2 <= n < (r+1)^2
        assert r * r <= n < (r + 1) * (r + 1)
    # exact scaled tsirelson radicand 2^129 and the pi-cascade-scale radicand
    assert _native.bigint_isqrt_c(2 ** 129) == R._py_isqrt(2 ** 129)
    big = 12 * (1 << 4096) * (1 << 4096)
    assert _native.bigint_isqrt_c(big) == R._py_isqrt(big)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_tsirelson_sqrt_native_equals_pure_exact_pair():
    """The exact Q(num, den) of rational.sqrt(2, precision_bits=64) — the
    tsirelson_bound cascade — is byte-identical native vs forced-pure."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        qn = R.sqrt(2.0, precision_bits=64)
        _native.HAS_NATIVE = False
        qp = R.sqrt(2.0, precision_bits=64)
    finally:
        _native.HAS_NATIVE = saved
    assert (qn.numerator, qn.denominator) == (qp.numerator, qp.denominator)


def test_value_oracles():
    """Named value oracles for the 6 ops (native path; also runs pure on no-C)."""
    # exp(1) partial sum → e ≈ 2.71828... (factorial-fast; tight)
    en, ed = R.exp_series_truncate(1, 1, 20)
    assert abs(en / ed - 2.718281828459045) < 1e-9
    # atan(1/2) → 0.4636476... (fast-converging interior point; tight)
    an, ad = R.atan_series_truncate(1, 2, 40)
    assert abs(an / ad - 0.4636476090008061) < 1e-9
    # atan(1) → π/4 (boundary, slow — the "π/4-ish" oracle, loose tol for N=64)
    bn, bd = R.atan_series_truncate(1, 1, 64)
    assert abs(bn / bd - 0.7853981633974483) < 1e-2
    # cos(0) = 1, sin(0) = 0, log1p(0) = 0 (EXACT rationals)
    assert R.cos_series_truncate(0, 1, 10) == (1, 1)
    assert R.sin_series_truncate(0, 1, 10) == (0, 1)
    assert R.log1p_series_truncate(0, 1, 10) == (0, 1)
    # cos(1) → 0.5403023..., sin(1) → 0.8414709... (interior; tight)
    cn, cd = R.cos_series_truncate(1, 1, 30)
    assert abs(cn / cd - 0.5403023058681398) < 1e-9
    sn, sd = R.sin_series_truncate(1, 1, 30)
    assert abs(sn / sd - 0.8414709848078965) < 1e-9
    # log1p(1/2) → ln(1.5) ≈ 0.4054651... (fast interior point; tight)
    ln, ld = R.log1p_series_truncate(1, 2, 60)
    assert abs(ln / ld - 0.4054651081095633) < 1e-9
    # tsirelson = 2√2 ≈ 2.8284271247461903
    assert abs(bell.tsirelson_bound() - 2.8284271247461903) < 1e-12
    assert abs(bell.TSIRELSON_BOUND - 2.0 * (2.0 ** 0.5)) < 1e-15


def test_ledger_rows_are_c_dispatched():
    """The 6 batch ops are classified c_dispatched in the Rosetta ledger."""
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    for da in (
        "srmech.amsc.rational.exp_series_truncate",
        "srmech.amsc.rational.sin_series_truncate",
        "srmech.amsc.rational.cos_series_truncate",
        "srmech.amsc.rational.log1p_series_truncate",
        "srmech.amsc.rational.atan_series_truncate",
        "srmech.qm.bell.tsirelson_bound",
    ):
        assert rows.get(da) == "c_dispatched", (da, rows.get(da))
