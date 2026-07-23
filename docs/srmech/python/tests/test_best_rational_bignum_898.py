"""rc319 / `#898` — ``best_rational`` is no longer uint64-bounded.

The music spike hit an EXACT Class-N log anchor whose ratio (and/or the
``max_denominator`` budget) exceeds 2**64. Before rc319 ``best_rational``
validated all three inputs through ``_ensure_uint64`` and raised
``ValueError`` before it could compute. rc319 validates through
``_ensure_nonneg_int`` (non-negative int, NO u64 ceiling) and dispatches:

* every coordinate ≤ 2**64-1  → the fast native path (byte-identical to
  the pure walk, still pinned by ``test_rational_parity.py``); the pure
  walk keeps its u64 overflow guards on THIS branch only;
* any coordinate > 2**64-1    → the pure convergent walk carries Python
  bigints, u64 guards dropped, bounded solely by ``max_denominator``.

These gates prove the bound-lift is correct in the bignum regime AND that
nothing moved in the u64-fit regime. numpy-free; native == pure where the
native path is eligible.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc import _native, rational

_U64 = 0xFFFF_FFFF_FFFF_FFFF


def _best_rational_ref(p: int, q: int, max_q: int):
    """Guard-free CF-convergent oracle (Python bigints, no u64 ceiling).

    The whole point of `#898` is that the u64 guards were blocking a walk
    that is otherwise exact over bignums, so the honest oracle is the same
    Stern-Brocot convergent walk with the guards removed."""
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    best = (0, 1)
    while q != 0:
        a = p // q
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        if k_next > max_q:
            break
        best = (h_next, k_next)
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
        p, q = q, p % q
    return best


# ---------------------------------------------------------------------
# 1. The u64-fit regime is UNCHANGED (the bound-lift touches nothing here)
# ---------------------------------------------------------------------

@pytest.mark.parametrize("p, q, max_q, expected", [
    (22, 7, 7, (22, 7)),
    (22, 7, 3, (3, 1)),
    (355, 113, 100, (22, 7)),
    (355, 113, 200, (355, 113)),
])
def test_u64_fit_reference_unchanged(p, q, max_q, expected):
    assert rational.best_rational(p, q, max_q) == expected


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_u64_fit_native_equals_pure():
    """u64-fit inputs still take the fast native path AND stay byte-identical
    to the pure walk (the guard-branch that rc319 left intact)."""
    saved = _native.HAS_NATIVE
    cases = [(22, 7, 7), (355, 113, 100), (1, 2, 1), (_U64, _U64 - 1, 1000)]
    try:
        for p, q, max_q in cases:
            _native.HAS_NATIVE = True
            nat = rational.best_rational(p, q, max_q)
            _native.HAS_NATIVE = False
            pure = rational.best_rational(p, q, max_q)
            assert nat == pure, f"{p}/{q} @ {max_q}: native={nat} pure={pure}"
    finally:
        _native.HAS_NATIVE = saved


# ---------------------------------------------------------------------
# 2. Bignum RATIO, small max_q — the exact case the old u64 gate blocked
# ---------------------------------------------------------------------

def test_bignum_ratio_small_max_q_hand_verified():
    # p/q = 1 + 2**-70. CF = [1; 2**70]. Convergent [1] = 1/1 fits (k=1≤3);
    # the next term's denominator 2**70 blows past max_q=3 → answer (1,1).
    p, q = 2 ** 70 + 1, 2 ** 70
    assert p > _U64  # the coordinate the old _ensure_uint64 rejected
    assert rational.best_rational(p, q, 3) == (1, 1)


def test_bignum_ratio_small_max_q_matches_oracle():
    # a rich CF whose numerator/denominator both exceed u64
    p, q = 10 ** 25, 10 ** 25 - 3
    assert p > _U64 and q > _U64
    for max_q in (1, 2, 7, 50, 10 ** 6):
        assert rational.best_rational(p, q, max_q) == _best_rational_ref(p, q, max_q)


def _cf_terms(p, q):
    """Guard-free Euclidean CF expansion (bignum-safe — `continued_fraction`
    itself is still u64-bounded, a sibling instance rc319 leaves for the
    declustering / precision arc)."""
    terms = []
    while q != 0:
        terms.append(p // q)
        p, q = q, p % q
    return terms


def _from_terms(terms):
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    for a in terms:
        h_prev, h_curr = a * h_prev + h_curr, h_prev
        k_prev, k_curr = a * k_prev + k_curr, k_prev
    return (h_prev, k_prev)


def test_bignum_ratio_returns_true_convergent():
    p, q = 10 ** 30 + 7, 10 ** 29 + 3
    bp, bq = rational.best_rational(p, q, 10 ** 8)
    assert 0 < bq <= 10 ** 8
    # a genuine convergent of p/q: it appears in p/q's continued fraction
    terms = _cf_terms(p, q)
    convergents = {_from_terms(terms[:i]) for i in range(1, len(terms) + 1)}
    assert (bp, bq) in convergents


# ---------------------------------------------------------------------
# 3. Bignum max_q — the denominator budget itself exceeds u64
# ---------------------------------------------------------------------

def test_bignum_max_q_fits_returns_reduced_ratio():
    # p,q fit u64 but max_q > u64 → NOT fits_u64 → the bignum walk, and the
    # full reduced p/q fits under the huge budget.
    p, q = 123456789, 987654321
    g = Fraction(p, q)
    assert rational.best_rational(p, q, 2 ** 80) == (g.numerator, g.denominator)


def test_bignum_everything_matches_oracle():
    p, q, max_q = 3 ** 60, 2 ** 95 + 1, 2 ** 90
    assert p > _U64 and q > _U64 and max_q > _U64
    assert rational.best_rational(p, q, max_q) == _best_rational_ref(p, q, max_q)


def test_exact_classn_log_anchor_overflows_u64_and_resolves():
    """The music-spike shape: an EXACT log-scale rational whose numerator and
    denominator both exceed u64, anchored to a modest denominator."""
    # ln(2) as an exact rational via the CF convergent [0;1,2,3,1,6,3,1,...]
    # blown up past u64 — here a big exact rational close to ln 2.
    num = 6931471805599453094172321214581765680755  # ~ln(2) * 1e40
    den = 10 ** 40
    assert num > _U64 and den > _U64
    bp, bq = rational.best_rational(num, den, 10 ** 6)
    assert 0 < bq <= 10 ** 6
    # the anchor is a faithful low-denominator stand-in for ln 2
    assert abs(Fraction(bp, bq) - Fraction(num, den)) < Fraction(1, 10 ** 6)
    assert rational.best_rational(num, den, 10 ** 6) == _best_rational_ref(num, den, 10 ** 6)


# ---------------------------------------------------------------------
# 4. The old u64 ValueError is GONE; the real validation still fires
# ---------------------------------------------------------------------

def test_over_u64_no_longer_raises():
    # every one of the three inputs, individually over u64, used to raise
    for args in [(2 ** 65, 3, 2), (5, 2 ** 65, 4), (5, 7, 2 ** 65)]:
        rational.best_rational(*args)  # must not raise


def test_negative_still_raises():
    with pytest.raises(ValueError):
        rational.best_rational(-1, 2, 10)
    with pytest.raises(ValueError):
        rational.best_rational(1, -2, 10)
    with pytest.raises(ValueError):
        rational.best_rational(1, 2, -10)


def test_zero_denominator_and_max_still_raise():
    with pytest.raises(ValueError):
        rational.best_rational(1, 0, 10)
    with pytest.raises(ValueError):
        rational.best_rational(1, 2, 0)


def test_non_int_still_raises():
    with pytest.raises(TypeError):
        rational.best_rational(1.5, 2, 10)
    with pytest.raises(TypeError):
        rational.best_rational(1, 2, 10.0)
