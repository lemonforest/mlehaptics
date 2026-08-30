"""rc378 (`#T1049`) — the ``primitive_integer_vector`` keystone.

The smallest integer vector on an exact ℚ-vector's ray (Class I ∘ K ∘ C): the
op the chemistry stoichiometry domain (`#T1050`, balancing a reaction = the
integer nullspace of the stoichiometric matrix) consumes. This module pins the
semantics, the input-shape parity (QMat column vs list vs (num, den) pairs), the
sign / zero / single-element / already-primitive edges, the ``with_content``
reversibility, the C↔Python byte-parity (native path forced ON then OFF), and
the arbitrary-precision (bignum) fallback that overflows the int64 C fast path.

Numpy-ABSENT by construction: every carrier here is ``Q`` / ``QMat`` / plain
``int`` / ``fractions.Fraction`` — no numpy import anywhere.
"""
from __future__ import annotations

import random
from fractions import Fraction

import pytest

from srmech import _native
from srmech.math import cyclic
from srmech.math.q import Q
from srmech.math.qmat import QMat

from tests._native_gate import require_native


# ── an INDEPENDENT oracle (no srmech ops) — the primitive vector, pure Python ──
def _oracle(pairs):
    """Smallest integer vector on the ray of [num_i/den_i], first-nonzero
    positive. Uses ``fractions``/``math`` only — a genuinely separate witness
    so the parity check is not a tautology against srmech's own body."""
    import math
    # normalise dens > 0
    norm = []
    for num, den in pairs:
        if den == 0:
            raise ValueError("zero denominator")
        if den < 0:
            num, den = -num, -den
        norm.append((num, den))
    denom_lcm = 1
    for _num, den in norm:
        denom_lcm = denom_lcm * den // math.gcd(denom_lcm, den)
    cleared = [num * (denom_lcm // den) for num, den in norm]
    g = 0
    for c in cleared:
        g = math.gcd(g, abs(c))
    if g == 0:
        return [0 for _ in cleared]
    orient = 1
    for c in cleared:
        if c != 0:
            orient = 1 if c > 0 else -1
            break
    return [orient * (c // g) for c in cleared]


# ──────────────────────────────────────────────────────────────────────
# Semantics
# ──────────────────────────────────────────────────────────────────────

def test_clears_denominators_and_strips_content():
    # [1/2, 1/3] -> clear by lcm 6 -> [3, 2] -> gcd 1 -> [3, 2]
    assert cyclic.primitive_integer_vector([(1, 2), (1, 3)]) == [3, 2]


def test_strips_content_to_one():
    # [4, 6, 2] -> gcd 2 -> [2, 3, 1]
    assert cyclic.primitive_integer_vector([4, 6, 2]) == [2, 3, 1]


def test_first_nonzero_is_pinned_positive():
    # first nonzero is negative -> whole vector flips so it leads positive
    assert cyclic.primitive_integer_vector([-4, 6, -2]) == [2, -3, 1]
    assert cyclic.primitive_integer_vector([0, -3, 6]) == [0, 1, -2]


def test_zero_vector_maps_to_zeros():
    assert cyclic.primitive_integer_vector([0, 0, 0]) == [0, 0, 0]
    assert cyclic.primitive_integer_vector([(0, 5), (0, 7)]) == [0, 0]


def test_single_element():
    assert cyclic.primitive_integer_vector([Q(-7, 3)]) == [1]     # any nonzero -> [1]
    assert cyclic.primitive_integer_vector([Q(5, 1)]) == [1]
    assert cyclic.primitive_integer_vector([0]) == [0]


def test_already_primitive_is_unchanged():
    assert cyclic.primitive_integer_vector([3, 2]) == [3, 2]
    assert cyclic.primitive_integer_vector([1, 0, 0]) == [1, 0, 0]


def test_empty_vector():
    assert cyclic.primitive_integer_vector([]) == []
    assert cyclic.primitive_integer_vector([], with_content=True) == (0, [])


def test_negative_denominator_normalised():
    # 1/-2 == -1/2 ; [-1/2, 1/2] cleared -> [-1, 1] -> first nonzero neg -> [1, -1]
    assert cyclic.primitive_integer_vector([(1, -2), (1, 2)]) == [1, -1]


# ──────────────────────────────────────────────────────────────────────
# Input-shape parity: QMat column ≡ list of Q ≡ (num, den) pairs
# ──────────────────────────────────────────────────────────────────────

def test_qmat_column_matches_list_input():
    col = QMat([[Q(2, 3)], [Q(-4, 9)], [Q(0, 1)]])       # a 3×1 column
    as_q = [Q(2, 3), Q(-4, 9), Q(0, 1)]
    as_pairs = [(2, 3), (-4, 9), (0, 1)]
    expect = _oracle([(2, 3), (-4, 9), (0, 1)])
    assert cyclic.primitive_integer_vector(col) == expect
    assert cyclic.primitive_integer_vector(as_q) == expect
    assert cyclic.primitive_integer_vector(as_pairs) == expect


def test_qmat_row_vector_accepted():
    row = QMat([[Q(1, 2), Q(1, 3), Q(1, 6)]])            # a 1×3 row
    assert cyclic.primitive_integer_vector(row) == _oracle([(1, 2), (1, 3), (1, 6)])


def test_qmat_nullspace_column_is_the_real_consumer():
    # A rank-deficient system: the kernel column is exact ℚ; the op turns it
    # into the smallest integer vector on that ray (the chemistry use).
    A = QMat([[Q(1), Q(1), Q(-1)], [Q(2), Q(-1), Q(-1)]])
    basis = A.nullspace()
    assert basis, "expected a nontrivial kernel"
    for col in basis:
        prim = cyclic.primitive_integer_vector(col)
        # prim must be integer, on the same ray, and satisfy A·prim == 0
        acc = [sum(int(A[i, j]) * prim[j] for j in range(A.n_cols))
               for i in range(A.n_rows)]
        assert acc == [0] * A.n_rows
        # content 1 and first nonzero positive
        assert prim == _oracle([(int(c.numerator), int(c.denominator))
                                for row in col for c in row])


def test_non_vector_qmat_rejected():
    m = QMat([[Q(1), Q(2)], [Q(3), Q(4)]])
    with pytest.raises(ValueError):
        cyclic.primitive_integer_vector(m)


def test_fraction_and_int_entries():
    assert cyclic.primitive_integer_vector([Fraction(1, 2), Fraction(1, 3)]) == [3, 2]
    assert cyclic.primitive_integer_vector([Fraction(2, 1), 4, 6]) == [1, 2, 3]


def test_zero_denominator_rejected():
    with pytest.raises(ValueError):
        cyclic.primitive_integer_vector([(1, 0)])


# ──────────────────────────────────────────────────────────────────────
# with_content reversibility
# ──────────────────────────────────────────────────────────────────────

def test_with_content_reconstructs_cleared_vector():
    pairs = [(1, 2), (-1, 3), (0, 1)]
    content, prim = cyclic.primitive_integer_vector(pairs, with_content=True)
    # cleared = L·v with L = lcm(2,3,1) = 6 -> [3, -2, 0]
    cleared = [3, -2, 0]
    assert [content * p for p in prim] == cleared
    # the primitive itself leads positive with content 1
    assert prim == _oracle(pairs)


def test_with_content_zero_vector():
    content, prim = cyclic.primitive_integer_vector([0, 0], with_content=True)
    assert content == 0
    assert prim == [0, 0]


# ──────────────────────────────────────────────────────────────────────
# C ↔ Python byte-parity (native forced ON, then OFF)
# ──────────────────────────────────────────────────────────────────────

def test_native_path_is_actually_exercised():
    """The C fast path must be REACHED for an int64-fittable input — otherwise
    the parity test below silently checks pure against pure."""
    require_native("srmech_primitive_integer_vector")
    got = cyclic._primitive_integer_vector_c([(1, 2), (1, 3)])
    assert got is not None, "C peer returned None for an int64-fittable vector"
    content, prim = got
    assert prim == [3, 2]


def test_native_matches_pure_random_sweep():
    require_native("srmech_primitive_integer_vector")
    rng = random.Random(20260801)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(300):
            n = rng.randrange(1, 8)
            pairs = []
            for _i in range(n):
                num = rng.randrange(-1000, 1000)
                den = rng.choice([d for d in range(-30, 31) if d != 0])
                pairs.append((num, den))
            _native.HAS_NATIVE = True
            native = cyclic.primitive_integer_vector(pairs)
            native_c = cyclic.primitive_integer_vector(pairs, with_content=True)
            _native.HAS_NATIVE = False
            pure = cyclic.primitive_integer_vector(pairs)
            pure_c = cyclic.primitive_integer_vector(pairs, with_content=True)
            assert native == pure == _oracle(pairs), pairs
            assert native_c == pure_c, pairs
    finally:
        _native.HAS_NATIVE = saved


def test_native_edge_cases_match_pure():
    require_native("srmech_primitive_integer_vector")
    cases = [
        [0, 0, 0],
        [-4, 6, -2],
        [(1, 2), (1, 3), (1, 6)],
        [(1, -2), (1, 2)],
        [5],
        [0, -3, 6],
    ]
    saved = _native.HAS_NATIVE
    try:
        for pairs in cases:
            _native.HAS_NATIVE = True
            native = cyclic.primitive_integer_vector(pairs)
            _native.HAS_NATIVE = False
            pure = cyclic.primitive_integer_vector(pairs)
            assert native == pure, pairs
    finally:
        _native.HAS_NATIVE = saved


# ──────────────────────────────────────────────────────────────────────
# Bignum fallback — int64 C fast path bails, pure path stays exact
# ──────────────────────────────────────────────────────────────────────

def test_bignum_overflows_c_fast_path_but_pure_is_exact():
    # denominators/numerators far beyond int64 — the C peer must decline
    # (return None), and the pure body must produce the exact answer.
    big = 10 ** 40
    pairs = [(big + 1, 2 * big), (big - 1, 3 * big)]
    # the C marshal declines (entries out of int64 domain)
    assert cyclic._primitive_integer_vector_c(pairs) is None
    got = cyclic.primitive_integer_vector(pairs)
    assert got == _oracle(pairs)
    # every entry is an int and content is 1 (gcd of results == 1)
    import math
    g = 0
    for v in got:
        g = math.gcd(g, abs(v))
    assert g == 1


def test_int64_intermediate_overflow_falls_back():
    # entries fit int64 but the denominator LCM blows int64 → C returns
    # overflow → pure path (bignum) is exact.
    pairs = [(1, 2147483647), (1, 2147483629), (1, 2147483587)]  # 3 large primes
    got = cyclic.primitive_integer_vector(pairs)
    assert got == _oracle(pairs)


# ──────────────────────────────────────────────────────────────────────
# describe() op count
# ──────────────────────────────────────────────────────────────────────

def test_describe_total_is_pinned():
    # NAME CARRIES NO NUMBER ON PURPOSE. This pin tracks a value that MOVES;
    # a name that spells the value is falsified by the next bump and was —
    # 16 such tests were found tree-wide, one named for 367 asserting 663.
    # See test_pinned_names_carry_no_value_rc447.py.
    import srmech
    assert srmech.describe()["tools"]["total"] == 695


def test_registered_in_tool_schema():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {e.name for e in get_tool_schema().tools}
    assert "srmech.math.cyclic.primitive_integer_vector" in names
