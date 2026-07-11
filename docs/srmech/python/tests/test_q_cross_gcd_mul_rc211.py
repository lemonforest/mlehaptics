"""#786 (0.9.0rc211): cross-gcd-first ``Q`` multiply — Knuth TAOCP Vol 2,
§4.5.1, the ``fractions.Fraction._mul`` discipline.

``Q.__mul__``/``__rmul__`` now divide the two CROSS gcds out of the operands
BEFORE multiplying (``g1 = gcd(|a_num|, b_den)``, ``g2 = gcd(|b_num|,
a_den)``), so intermediates stay near OPERAND scale instead of PRODUCT scale.
This is purely an intermediate-size optimisation at the carrier level (the
srmech_bigint / rational C layers are untouched); the result must be
BYTE-IDENTICAL to the old multiply-then-reduce path.

This test pins:
  1. DIFFERENTIAL byte-identity: ``(q1 * q2).as_pair()`` equals the OLD-path
     result ``rational_mul(q1.as_pair(), q2.as_pair())`` (multiply-then-
     reduce — exactly what ``Q.__mul__`` shipped before rc211) across random
     operands at every size tier (below / at / above the 64-bit cross-reduce
     gate and the 1024-bit bigq threshold), signs included;
  2. adversarial cross-cancelling shapes: ``a/b × b/a`` (reciprocals),
     ``a/b × b/c`` (chained), shared-prime-power pairs, zeros, ±1, u64
     boundary values, One-scale (~100-digit) shared-factor operands — plus a
     ``fractions.Fraction`` second witness on every case;
  3. the operand-interop surface is unchanged: int / bool / float / 2-tuple
     operands, the reflected ``__rmul__``, ``NotImplemented`` → ``TypeError``
     for a non-rational operand, and the canonical ``ValueError`` for a
     non-positive tuple denominator (the delegation path);
  4. the u64-fit gate: below ``_CROSS_REDUCE_MIN_BITS`` the helper delegates
     to ``rational_mul`` outright (same object result), and the constant is
     the attested u64 scalar-C domain boundary (64);
  5. perf sanity (generous CI bands; the measured table lives in the
     CHANGELOG 0.9.0rc211 entry): the small-operand path is not slower than
     the old path beyond noise, and the cross-cancelling big-ℚ multiply is
     genuinely FASTER than the simulated old path.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import random
import time
from fractions import Fraction

import pytest

from srmech.amsc import q as _q_mod
from srmech.amsc import rational as _rational
from srmech.amsc.q import Q, _mul_cross_reduced


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "the rc211 cross-gcd multiply tests must run on the numpy-ABSENT "
        "matrix")


def _old_path_mul(a_pair, b_pair):
    """The pre-rc211 ``Q.__mul__`` body: multiply-then-reduce via
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


# ── 1. differential byte-identity across size tiers ─────────────────────────
@pytest.mark.parametrize("bits", [8, 32, 63, 64, 65, 128, 500, 1024, 2200])
def test_differential_random_operands(bits):
    """new-Q.mul == old-Q.mul (the fully-reduced pair) at every size tier —
    below/at/above the 64-bit cross-reduce gate AND the 1024-bit bigq
    threshold; random signs; random (already-reduced-by-Q) operands."""
    rng = random.Random(0xC211 + bits)
    for i in range(30):
        an = rng.getrandbits(bits) - (1 << (bits - 1))
        ad = rng.getrandbits(bits) + 1
        bn = rng.getrandbits(bits) - (1 << (bits - 1))
        bd = rng.getrandbits(bits) + 1
        _assert_mul_identical(Q(an, ad), Q(bn, bd), f"random@{bits}#{i}")


def test_differential_cross_cancelling_reciprocals():
    """a/b × b/a == 1 exactly — the maximal cross-cancellation shape (the
    Knuth win case): every factor cancels in the cross gcds."""
    rng = random.Random(0xAB1)
    for bits in (16, 80, 300, 1500, 4000):
        a = rng.getrandbits(bits) | 1
        b = rng.getrandbits(bits) | (1 << (bits - 1))
        q = Q(a, b) * Q(b, a)
        assert q.as_pair() == (1, 1), f"reciprocal@{bits}: {q!r}"
        _assert_mul_identical(Q(a, b), Q(b, a), f"reciprocal@{bits}")
        _assert_mul_identical(Q(-a, b), Q(b, a), f"neg-reciprocal@{bits}")
        assert (Q(-a, b) * Q(b, a)).as_pair() == (-1, 1)


def test_differential_chained_and_shared_prime_powers():
    """a/b × b/c (one full cross-cancel) and shared prime-power operands
    (partial cross-cancels on both diagonals)."""
    rng = random.Random(0xAB2)
    for bits in (24, 200, 1200):
        a = rng.getrandbits(bits) | 1
        b = rng.getrandbits(bits) | (1 << (bits - 1))
        c = rng.getrandbits(bits) | 1
        _assert_mul_identical(Q(a, b), Q(b, c), f"chain@{bits}")
    # shared prime powers: (2^i·3^j·x)/(5^k·y) × (5^m·u)/(2^n·3^p·v)
    for i, (p1, p2) in enumerate([(2, 5), (3, 7), (2 ** 5, 3 ** 4)]):
        x = p1 ** 40 * 11
        y = p2 ** 35 * 13
        u = p2 ** 50 * 17
        v = p1 ** 30 * 19
        _assert_mul_identical(Q(x, y), Q(u, v), f"prime-powers#{i}")
        _assert_mul_identical(Q(-x, y), Q(u, v), f"neg-prime-powers#{i}")
        _assert_mul_identical(Q(x, y), Q(-u, v), f"prime-powers-neg#{i}")


def test_differential_zeros_ones_and_boundaries():
    """Zeros (either side), ±1, and the u64 boundary sliver (bit-length 63/
    64/65 magnitudes) — where the old path's C-fast-path eligibility and the
    new gate can disagree about the ENGINE while the VALUE must not move."""
    big = (1 << 200) + 7
    boundary = [
        (1 << 63) - 1, 1 << 63, (1 << 64) - 1, (1 << 64) + 1,
    ]
    cases = [
        (Q(0, 1), Q(3, 4)), (Q(3, 4), Q(0, 5)), (Q(0, 7), Q(0, 11)),
        (Q(1, 1), Q(big, big + 2)), (Q(-1, 1), Q(big, 3)),
        (Q(big, 3), Q(1, 1)),
    ]
    for m in boundary:
        cases.append((Q(m, 3), Q(3, m)))
        cases.append((Q(-m, m + 2), Q(m + 2, m)))
        cases.append((Q(m, m + 1), Q(m + 1, m + 3)))
    for i, (q1, q2) in enumerate(cases):
        _assert_mul_identical(q1, q2, f"edge#{i}")


def test_differential_one_scale_shared_factor():
    """The One-scale regime (~100-digit numerators, the carrier's design
    load): operands built around a shared ~100-digit factor so BOTH cross
    gcds are huge — the exact shape the cross-reduce exists for."""
    rng = random.Random(0x0E5)
    g = rng.getrandbits(340) | (1 << 339)          # ~103 digits
    a = g * (rng.getrandbits(120) | 1)
    b = rng.getrandbits(333) | 1
    c = rng.getrandbits(120) | 1
    d = g * (rng.getrandbits(333) | 1)
    _assert_mul_identical(Q(a, b), Q(c, d), "one-scale-g1")
    _assert_mul_identical(Q(-a, b), Q(c, d), "one-scale-g1-neg")
    _assert_mul_identical(Q(b, a), Q(d, c), "one-scale-g2")


# ── 3. the operand-interop surface is unchanged ──────────────────────────────
def test_interop_surface_unchanged():
    q = Q(3, 4)
    assert (q * 2).as_pair() == (3, 2)
    assert (2 * q).as_pair() == (3, 2)                 # __rmul__
    assert (q * True).as_pair() == (3, 4)              # bool-as-int
    assert (q * 0.5).as_pair() == (3, 8)               # exact float pair
    assert (q * (2, 3)).as_pair() == (1, 2)            # house-form tuple
    assert ((2, 3) * q).as_pair() == (1, 2)
    big = (1 << 100) + 1
    assert (Q(big, 3) * (3, big)).as_pair() == (1, 1)  # big tuple operand
    assert q.__mul__("nope") is NotImplemented
    with pytest.raises(TypeError):
        _ = q * "nope"
    with pytest.raises(TypeError):
        _ = q * None
    # the canonical ValueError for a non-positive tuple denominator is
    # preserved (the helper delegates that path to rational_mul), at BOTH
    # size tiers:
    with pytest.raises(ValueError):
        _ = q * (3, -4)
    with pytest.raises(ValueError):
        _ = Q((1 << 100) + 1, 3) * (3, -((1 << 100) + 3))


def test_rmul_matches_mul_exactly():
    rng = random.Random(0xB111)
    for bits in (20, 200, 1500):
        an = rng.getrandbits(bits) - (1 << (bits - 1))
        ad = rng.getrandbits(bits) + 1
        bn = rng.getrandbits(bits) - (1 << (bits - 1))
        bd = rng.getrandbits(bits) + 1
        q1, q2 = Q(an, ad), Q(bn, bd)
        assert (q1 * q2).as_pair() == q1.__rmul__(q2).as_pair()


# ── 4. the gate constant + delegation ────────────────────────────────────────
def test_cross_reduce_gate_is_the_u64_domain_boundary():
    """64 is attested-to-structure (Class A): the u64 native scalar domain
    boundary — below it srmech_rational_mul is ONE fused C call and the
    cross gcds would be pure dispatch overhead. A change here must come with
    a new rationale (see CHANGELOG 0.9.0rc211)."""
    assert _q_mod._CROSS_REDUCE_MIN_BITS == 64


def test_helper_below_gate_matches_rational_mul():
    """Below the gate the helper IS rational_mul (delegation, same fused
    path); above it the result is still the identical reduced pair."""
    for a, b in [((3, 4), (8, 9)), ((-6, 35), (7, 2)), ((0, 1), (5, 9))]:
        assert _mul_cross_reduced(a, b) == _rational.rational_mul(a, b)
    big = (1 << 500) + 1
    for a, b in [((big, 3), (3, big)), ((-big, 7), (14, big + 2))]:
        assert _mul_cross_reduced(a, b) == _rational.rational_mul(a, b)


# ── 5. perf sanity (generous bands; measured table in CHANGELOG rc211) ──────
def _old_body_mul(q1: Q, q2: Q) -> Q:
    """The EXACT pre-rc211 ``Q.__mul__`` body (same ``_combine``/``_as_pair``
    dunder machinery, only the op differs) — the fair perf baseline."""
    return q1._combine(q2, _rational.rational_mul)


def test_perf_small_operands_not_pathologically_slower():
    """u64-fit operands delegate to the same fused path — the only new cost
    is the four-bit_length gate. Generous 2× band (CI noise; the real
    numbers are in the CHANGELOG). Interleaved best-of rounds to damp
    scheduler noise."""
    q1, q2 = Q(355, 113), Q(113, 355)
    t_new = t_old = None
    for _ in range(5):
        t0 = time.perf_counter()
        for _ in range(4000):
            _ = q1 * q2
        dt = time.perf_counter() - t0
        t_new = dt if t_new is None else min(t_new, dt)
        t0 = time.perf_counter()
        for _ in range(4000):
            _ = _old_body_mul(q1, q2)
        dt = time.perf_counter() - t0
        t_old = dt if t_old is None else min(t_old, dt)
    assert t_new <= 2.0 * t_old, (
        f"small-operand multiply pathologically slower: new={t_new:.6f}s "
        f"vs old={t_old:.6f}s")


def test_perf_cross_cancelling_big_q_wins():
    """The Knuth payoff case: reciprocal-shaped 20000-bit operands. The old
    path multiplies to 40000-bit products then gcd-reduces them; the new
    path cancels everything in two operand-scale gcds. Require a genuine
    win (≥ 1.3×; measured much larger — see CHANGELOG rc211)."""
    rng = random.Random(0xFEED211)
    bits = 20000
    a = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
    b = rng.getrandbits(bits) | (1 << (bits - 1))
    q1, q2 = Q(a, b), Q(b, a)
    t_new = t_old = None
    for _ in range(4):
        t0 = time.perf_counter()
        for _ in range(5):
            _ = q1 * q2
        dt = time.perf_counter() - t0
        t_new = dt if t_new is None else min(t_new, dt)
        t0 = time.perf_counter()
        for _ in range(5):
            _ = _old_body_mul(q1, q2)
        dt = time.perf_counter() - t0
        t_old = dt if t_old is None else min(t_old, dt)
    assert (q1 * q2).as_pair() == (1, 1)
    assert t_new * 1.3 <= t_old, (
        f"cross-cancelling big-ℚ multiply shows no win: new={t_new:.6f}s "
        f"vs old={t_old:.6f}s")
