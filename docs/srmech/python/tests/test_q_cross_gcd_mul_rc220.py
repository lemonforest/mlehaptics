"""#786 completion (0.9.0rc220): self-hosted coprime product for the
cross-gcd-first ``Q`` multiply — closes the rc212 honest-note follow-up.

rc212 gave ``Q.__mul__`` the full ``fractions.Fraction._mul`` discipline
(Knuth TAOCP Vol 2 §4.5.1: cross-reduce BEFORE multiplying; build the
proven-coprime product pair directly via ``Q._from_coprime`` — no
product-scale gcd). Its honest note flagged the one leg still off-substrate:
the fast path's final raw product rode CPython ``int`` multiply, because
``_native`` exposed no *raw* bigint multiply — only the fused ``bigq_mul_c``
whose built-in product-scale gcd-reduce is exactly the work the theorem
eliminates. rc220 adds ``_native.bigint_mul_c`` (RAW ``srmech_bigint_mul`` /
rc168 Karatsuba product — no gcd, no reduce) and routes the two coprime
products through it at/above the ``rational._BIGQ_MIN_BITS`` (1024-bit)
threshold via ``q._coprime_product`` — the #765 self-hosting discipline.

This test pins:
  1. DIFFERENTIAL byte-identity (the whole-op correctness gate, re-pinned
     over the rc220 routing): ``(q1 * q2).as_pair()`` equals the OLD
     multiply-then-reduce path ``rational_mul(q1.as_pair(), q2.as_pair())``
     (the exact pre-rc212 ``Q.__mul__`` body) AND the ``fractions.Fraction``
     second witness, across random operands at every size tier (below / at /
     above the 64-bit cross-reduce gate AND the 1024-bit bigq threshold,
     up to 4096 bits), signs, zeros, ±1, u64 boundary slivers, reciprocals
     ``a/b × b/a`` → exactly ``(1, 1)``, chained ``a/b × b/c``,
     shared-prime-power pairs, One-scale shared-factor operands;
  2. the SAME differential on the FORCED-PURE arm (in-file
     ``monkeypatch.setattr(_native, "HAS_NATIVE", False)`` — the rc213/rc217
     convention) — native == fully-pure == Fraction in a single run;
  3. rc220-specific: ``bigint_mul_c(a, b) == a·b`` byte-identity (signs,
     zero, ±1, u64 boundary, 4096-bit), the genuine-dispatch proof
     (``BIGQ_DISPATCH_COUNT`` moves on a big-ℚ ``Q`` multiply — never a
     silent fallback), the clean ``None`` decline when native is absent,
     and the ``_coprime_product`` routing gate is ``rational._BIGQ_MIN_BITS``
     (attested-to-measurement: the rc167 #765 dispatch threshold).

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import random
from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc import q as _q_mod
from srmech.amsc import rational as _rational
from srmech.amsc.q import Q, _coprime_product


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "the rc220 coprime-product tests must run on the numpy-ABSENT "
        "matrix")


def _old_path_mul(a_pair, b_pair):
    """The pre-rc212 ``Q.__mul__`` body: multiply-then-reduce via
    ``rational_mul`` on the raw operand pairs (ONE gcd on the double-width
    products). The differential oracle."""
    return _rational.rational_mul(a_pair, b_pair)


def _assert_mul_identical(q1: Q, q2: Q, ctx: str) -> None:
    got = q1 * q2
    want = _old_path_mul(q1.as_pair(), q2.as_pair())
    assert got.as_pair() == want, (
        f"{ctx}: new={got.as_pair()} vs old-path={want}")
    # Fraction second witness (independent implementation of the same math)
    f = (Fraction(q1.numerator, q1.denominator)
         * Fraction(q2.numerator, q2.denominator))
    assert got.as_pair() == (f.numerator, f.denominator), (
        f"{ctx}: new={got.as_pair()} vs Fraction={f}")


def _differential_sweep(tag: str) -> None:
    """The whole correctness gate as one sweep, runnable on either arm:
    random size tiers + adversarial cross-cancelling shapes + edges."""
    rng = random.Random(0xC220)
    # size tiers: below/at/above the 64-bit cross-reduce gate AND the
    # 1024-bit bigq threshold, through the huge (4096-bit) band
    for bits in (8, 32, 63, 64, 65, 128, 500, 1023, 1024, 1025, 2048, 4096):
        for i in range(12):
            an = rng.getrandbits(bits) - (1 << (bits - 1))
            ad = rng.getrandbits(bits) + 1
            bn = rng.getrandbits(bits) - (1 << (bits - 1))
            bd = rng.getrandbits(bits) + 1
            _assert_mul_identical(Q(an, ad), Q(bn, bd),
                                  f"{tag}:random@{bits}#{i}")
    # cross-cancelling reciprocals: a/b × b/a == 1 exactly (the Knuth win)
    for bits in (16, 80, 300, 1024, 1500, 4096):
        a = rng.getrandbits(bits) | 1
        b = rng.getrandbits(bits) | (1 << (bits - 1))
        assert (Q(a, b) * Q(b, a)).as_pair() == (1, 1), f"{tag}:recip@{bits}"
        assert (Q(-a, b) * Q(b, a)).as_pair() == (-1, 1)
        _assert_mul_identical(Q(a, b), Q(b, a), f"{tag}:recip@{bits}")
    # chained a/b × b/c (one full cross-cancel)
    for bits in (24, 200, 1200, 3000):
        a = rng.getrandbits(bits) | 1
        b = rng.getrandbits(bits) | (1 << (bits - 1))
        c = rng.getrandbits(bits) | 1
        _assert_mul_identical(Q(a, b), Q(b, c), f"{tag}:chain@{bits}")
    # shared prime powers (partial cross-cancels on both diagonals),
    # sized into the ≥1024-bit routing band
    for i, (p1, p2) in enumerate([(2, 5), (3, 7), (2 ** 5, 3 ** 4)]):
        x = p1 ** 400 * 11
        y = p2 ** 350 * 13
        u = p2 ** 500 * 17
        v = p1 ** 300 * 19
        _assert_mul_identical(Q(x, y), Q(u, v), f"{tag}:prime-powers#{i}")
        _assert_mul_identical(Q(-x, y), Q(u, v), f"{tag}:neg-prime-powers#{i}")
        _assert_mul_identical(Q(x, y), Q(-u, v), f"{tag}:prime-powers-neg#{i}")
    # zeros / ±1 / u64 boundary slivers
    big = (1 << 2000) + 7
    cases = [
        (Q(0, 1), Q(3, 4)), (Q(3, 4), Q(0, 5)), (Q(0, 7), Q(0, 11)),
        (Q(1, 1), Q(big, big + 2)), (Q(-1, 1), Q(big, 3)),
        (Q(big, 3), Q(1, 1)),
    ]
    for m in ((1 << 63) - 1, 1 << 63, (1 << 64) - 1, (1 << 64) + 1):
        cases.append((Q(m, 3), Q(3, m)))
        cases.append((Q(-m, m + 2), Q(m + 2, m)))
        cases.append((Q(m, m + 1), Q(m + 1, m + 3)))
    for i, (q1, q2) in enumerate(cases):
        _assert_mul_identical(q1, q2, f"{tag}:edge#{i}")
    # One-scale (~100-digit) shared-factor operands: BOTH cross gcds huge
    g = rng.getrandbits(340) | (1 << 339)
    a = g * (rng.getrandbits(120) | 1)
    b = rng.getrandbits(333) | 1
    c = rng.getrandbits(120) | 1
    d = g * (rng.getrandbits(333) | 1)
    _assert_mul_identical(Q(a, b), Q(c, d), f"{tag}:one-scale-g1")
    _assert_mul_identical(Q(-a, b), Q(c, d), f"{tag}:one-scale-g1-neg")
    _assert_mul_identical(Q(b, a), Q(d, c), f"{tag}:one-scale-g2")


# ── 1. the whole-op differential gate, native arm ────────────────────────────
def test_differential_native_arm():
    """new-Q.mul == old multiply-then-reduce == Fraction, on whatever native
    surface is present (the shipped configuration)."""
    _differential_sweep("native")


# ── 2. the same gate, forced-pure arm (rc213/rc217 convention) ───────────────
def test_differential_forced_pure_arm(monkeypatch):
    """The SAME sweep with the WHOLE native surface off (HAS_NATIVE False →
    every has_native_* gate declines: bigint_mul_c, bigint_gcd_c and the u64
    scalar ops all fall to the complete pure bodies) — native == fully-pure
    is asserted within a single run of this file."""
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        assert _native.has_native_bigq() is False
        _differential_sweep("pure")


# ── 3. rc220-specific: the raw bigint product primitive ─────────────────────
def test_bigint_mul_c_byte_identity_or_clean_decline():
    """``bigint_mul_c(a, b)`` equals CPython ``a·b`` exactly (the integer
    product is unique) across signs, zero, ±1, u64 boundary and the 4096-bit
    band — or declines with ``None`` when the native surface is absent."""
    rng = random.Random(0xB220)
    vals = [0, 1, -1, 2, -3, (1 << 63) - 1, 1 << 63, (1 << 64) + 1]
    for bits in (128, 1024, 4096):
        vals.append(rng.getrandbits(bits) | (1 << (bits - 1)))
        vals.append(-(rng.getrandbits(bits) | (1 << (bits - 1))))
    if not _native.has_native_bigq():
        assert _native.bigint_mul_c(vals[-1], vals[-2]) is None
        pytest.skip("native srmech_bigint core absent — clean None decline "
                    "pinned; byte-identity runs on the native matrix")
    for a in vals:
        for b in vals:
            got = _native.bigint_mul_c(a, b)
            assert got == a * b, (
                f"bigint_mul_c({a!r}, {b!r}) = {got!r} != {a * b!r}")


def test_bigint_mul_c_declines_none_when_forced_pure(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        assert _native.bigint_mul_c(1 << 2000, (1 << 2000) + 1) is None


def test_coprime_product_routes_and_matches():
    """``_coprime_product`` is byte-identical to ``x·y`` on both sides of the
    routing gate (below: CPython int; at/above: the raw C bignum when
    present), including signs and zero."""
    rng = random.Random(0xAB220)
    small = [(3, 4), (-7, 9), (0, 5), (1, -1),
             ((1 << 500) + 1, 3)]        # below the 1024-bit gate
    big = []
    for bits in (1024, 1025, 2048, 4096):
        x = rng.getrandbits(bits) | (1 << (bits - 1))
        y = rng.getrandbits(bits) | 1
        big.extend([(x, y), (-x, y), (x, -y), (0, x), (1, -x)])
    for x, y in small + big:
        assert _coprime_product(x, y) == x * y, f"({x!r}, {y!r})"


def test_genuine_dispatch_big_q_mul_moves_the_counter():
    """The proof the routing is real: a big cross-gcd ``Q`` multiply whose
    cross-reduced parts sit at/above the 1024-bit threshold must move
    ``BIGQ_DISPATCH_COUNT`` (bigint_mul_c and/or bigint_gcd_c crossings) —
    never a silent CPython fallback on the native matrix."""
    if not _native.has_native_bigq():
        pytest.skip("native srmech_bigint core absent")
    rng = random.Random(0xD220)
    # coprime-ish random 2048-bit operands: cross gcds are small, so the
    # cross-reduced parts STAY ≥ 1024 bits → both products route native
    a = rng.getrandbits(2048) | (1 << 2047) | 1
    b = rng.getrandbits(2048) | (1 << 2047)
    c = rng.getrandbits(2048) | (1 << 2047) | 1
    d = rng.getrandbits(2048) | (1 << 2047)
    q1, q2 = Q(a, b), Q(c, d)
    before = _native.BIGQ_DISPATCH_COUNT
    got = q1 * q2
    after = _native.BIGQ_DISPATCH_COUNT
    assert after > before, (
        "big-ℚ Q multiply did not touch the srmech_bigint dispatch counter")
    f = Fraction(a, b) * Fraction(c, d)
    assert got.as_pair() == (f.numerator, f.denominator)


def test_routing_gate_is_the_bigq_threshold():
    """The ``_coprime_product`` gate constant IS ``rational._BIGQ_MIN_BITS``
    (attested-to-measurement, Class B: the rc167 #765 parity-onset
    threshold — 1024). A change there must retune the routing with it."""
    assert _rational._BIGQ_MIN_BITS == 1024
    # and q.py routes by exactly that constant (no shadow copy):
    import inspect
    src = inspect.getsource(_q_mod._coprime_product)
    assert "_BIGQ_MIN_BITS" in src


# ── 4. interop surface unchanged (spot re-pin over the rc220 routing) ───────
def test_interop_surface_unchanged():
    q = Q(3, 4)
    assert (q * 2).as_pair() == (3, 2)
    assert (2 * q).as_pair() == (3, 2)                 # __rmul__
    assert (q * 0.5).as_pair() == (3, 8)               # exact float pair
    big = (1 << 2000) + 1
    assert (Q(big, 3) * (3, big)).as_pair() == (1, 1)  # big tuple operand
    assert q.__mul__("nope") is NotImplemented
    with pytest.raises(TypeError):
        _ = q * "nope"
    with pytest.raises(ValueError):
        _ = Q(big, 3) * (3, -(big + 2))
