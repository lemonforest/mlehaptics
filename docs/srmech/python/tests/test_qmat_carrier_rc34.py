"""0.9.0rc34 — the exact-rational matrix carrier ``QMat`` (the bigint peer of Mat).

``QMat`` is the 2-D exact carrier: a dense matrix whose every entry is an exact
:class:`~srmech.amsc.q.Q` rational (a reduced ``(num, den)`` of Python ``int`` =
arbitrary precision). It is to :class:`srmech.amsc.mat.Mat` what ``Q`` is to a
float scalar — exact dense linear algebra over ℚ with **no magnitude ceiling**.

This ratchet proves:

1. **Construction + coercion** — ``int`` / ``(num, den)`` / ``Q`` / ``Fraction``
   entries; a ``float`` is REJECTED by ``from_rows`` but accepted by
   ``from_float_rows`` (exact and best-rational-snap); ``identity`` / ``zeros``.
2. **Accessors** — ``shape`` / indexing / ``__eq__``.
3. **Exact arithmetic** — add / sub / neg / scalar-mul / ``@`` (associativity +
   a hand-computed product) / ``transpose().T == self``.
4. **Exact linear algebra over ℚ** — ``rref`` / ``rank`` on a rank-deficient
   matrix; ``det`` of a known 3×3; ``inverse() @ A == I``; ``solve`` (``A@x==b``);
   ``nullspace`` dimension + ``A @ n == 0`` exactly.
5. **The boundary collapse** — ``to_mat()`` is a float64 ``Mat``; ``from_mat`` of
   a dyadic ``to_mat`` round-trips exactly; a complex ``Mat`` is rejected.
6. **THE KEYSTONE** — entries with numerators/denominators FAR beyond int64
   (``Q(10**40+1, 3**30)``) run a matmul + det + inverse and stay EXACT bigint
   ``Q``, matching a ``fractions.Fraction`` oracle. This is the reason ``QMat``
   exists: full bigint, no int64 Q61 ceiling.

The whole module is numpy-free AND math-free (it runs on the numpy-ABSENT
matrix); the ``Fraction`` oracle is a stdlib test aid, allowed in a test.
"""

from __future__ import annotations

import importlib.util
from fractions import Fraction

import pytest

from srmech.amsc import QMat
from srmech.amsc.mat import Mat
from srmech.amsc.q import Q


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this QMat carrier ratchet must run on the numpy-ABSENT matrix")


# ── 1. construction + coercion ──────────────────────────────────────────────
def test_construct_from_int_pair_q_fraction():
    A = QMat.from_rows([[1, (3, 4)], [Q(5, 2), Fraction(7, 8)]])
    assert A.shape == (2, 2)
    assert A[0, 0] == Q(1, 1)
    assert A[0, 1] == Q(3, 4)
    assert A[1, 0] == Q(5, 2)
    assert A[1, 1] == Q(7, 8)
    # every entry is an exact Q
    for row in A.to_lists():
        for e in row:
            assert isinstance(e, Q)


def test_init_equivalent_to_from_rows():
    rows = [[1, 2], [3, 4]]
    assert QMat(rows) == QMat.from_rows(rows)


def test_float_rejected_by_from_rows():
    with pytest.raises(TypeError):
        QMat.from_rows([[1.5, 2]])


def test_ragged_rows_rejected():
    with pytest.raises(ValueError):
        QMat.from_rows([[1, 2], [3]])


def test_from_float_rows_exact():
    # dyadic floats lift to their EXACT ratio
    A = QMat.from_float_rows([[0.5, 0.25], [0.125, 1.0]])
    assert A[0, 0] == Q(1, 2)
    assert A[0, 1] == Q(1, 4)
    assert A[1, 0] == Q(1, 8)
    assert A[1, 1] == Q(1, 1)


def test_from_float_rows_best_rational_snap():
    # 0.1 is NOT dyadic; snapping de-noises the float64 round-off to 1/10.
    A = QMat.from_float_rows([[0.1, 0.3333333333333333]], max_denominator=1000)
    assert A[0, 0] == Q(1, 10)
    assert A[0, 1] == Q(1, 3)


def test_identity_and_zeros():
    ident = QMat.identity(3)
    assert ident.shape == (3, 3)
    for i in range(3):
        for j in range(3):
            assert ident[i, j] == (Q(1, 1) if i == j else Q(0, 1))
    z = QMat.zeros(2, 4)
    assert z.shape == (2, 4)
    assert all(z[i, j] == 0 for i in range(2) for j in range(4))


# ── 2. accessors ────────────────────────────────────────────────────────────
def test_indexing_row_and_scalar():
    A = QMat.from_rows([[1, 2, 3], [4, 5, 6]])
    assert A[1, 2] == Q(6, 1)
    assert A[0] == (Q(1, 1), Q(2, 1), Q(3, 1))
    assert A[-1, -1] == Q(6, 1)               # negative-aware
    assert len(A) == 2


def test_eq_exact_and_against_sequence():
    A = QMat.from_rows([[1, 2], [3, 4]])
    assert A == QMat.from_rows([[1, 2], [3, 4]])
    assert A == [[1, 2], [3, 4]]              # coerced compare
    assert A != QMat.from_rows([[1, 2], [3, 5]])
    assert A != QMat.from_rows([[1, 2]])      # shape mismatch ⇒ not equal


# ── 3. exact arithmetic ─────────────────────────────────────────────────────
def test_add_sub_neg():
    A = QMat.from_rows([[1, 2], [3, 4]])
    B = QMat.from_rows([[5, 6], [7, 8]])
    assert A + B == QMat.from_rows([[6, 8], [10, 12]])
    assert B - A == QMat.from_rows([[4, 4], [4, 4]])
    assert -A == QMat.from_rows([[-1, -2], [-3, -4]])
    with pytest.raises(ValueError):
        A + QMat.from_rows([[1, 2, 3]])


def test_scalar_mul():
    A = QMat.from_rows([[1, 2], [3, 4]])
    assert A * Q(1, 2) == QMat.from_rows([[(1, 2), 1], [(3, 2), 2]])
    assert 3 * A == QMat.from_rows([[3, 6], [9, 12]])


def test_matmul_against_hand_computed():
    A = QMat.from_rows([[1, 2], [3, 4]])
    B = QMat.from_rows([[5, 6], [7, 8]])
    # [[1*5+2*7, 1*6+2*8],[3*5+4*7, 3*6+4*8]] = [[19,22],[43,50]]
    assert A @ B == QMat.from_rows([[19, 22], [43, 50]])
    assert A.matmul(B) == A @ B


def test_matmul_associativity():
    A = QMat.from_rows([[1, 2], [0, 3]])
    B = QMat.from_rows([[2, 1], [1, 4]])
    C = QMat.from_rows([[1, 0], [5, 2]])
    assert (A @ B) @ C == A @ (B @ C)


def test_matmul_inner_dim_check():
    A = QMat.from_rows([[1, 2, 3]])           # 1×3
    with pytest.raises(ValueError):
        A @ QMat.from_rows([[1, 2]])          # 1×2 — inner dims 3 != 1


def test_transpose_involution():
    A = QMat.from_rows([[1, 2, 3], [4, 5, 6]])
    assert A.transpose().shape == (3, 2)
    assert A.transpose().T == A
    assert A.T[2, 1] == A[1, 2]


# ── 4. exact linear algebra over ℚ ──────────────────────────────────────────
def test_rref_and_rank_rank_deficient():
    # row3 = row1, and col-space dim 2 ⇒ rank 2 of this 3×3.
    A = QMat.from_rows([[1, 2, 3], [4, 5, 6], [1, 2, 3]])
    assert A.rank() == 2
    R = A.rref()
    # RREF of this matrix: [[1,0,-1],[0,1,2],[0,0,0]]
    assert R == QMat.from_rows([[1, 0, -1], [0, 1, 2], [0, 0, 0]])


def test_det_known_3x3():
    # det [[2,5,3],[1,-2,-1],[1,3,4]] = exact integer.
    A = QMat.from_rows([[2, 5, 3], [1, -2, -1], [1, 3, 4]])
    # Fraction oracle (cofactor expansion)
    rows = [[Fraction(x) for x in r] for r in [[2, 5, 3], [1, -2, -1], [1, 3, 4]]]
    oracle = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
              - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
              + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    assert A.det() == Q(oracle.numerator, oracle.denominator)


def test_det_rational_entries():
    A = QMat.from_rows([[(1, 2), (1, 3)], [(1, 4), (1, 5)]])
    # det = 1/2*1/5 - 1/3*1/4 = 1/10 - 1/12 = 1/60
    assert A.det() == Q(1, 60)


def test_det_singular_is_zero():
    A = QMat.from_rows([[1, 2], [2, 4]])
    assert A.det() == Q(0, 1)


def test_inverse_times_a_is_identity():
    A = QMat.from_rows([[4, 7], [2, 6]])
    Ainv = A.inverse()
    assert Ainv @ A == QMat.identity(2)
    assert A @ Ainv == QMat.identity(2)
    # exact inverse of [[4,7],[2,6]]: det=10 ⇒ 1/10 [[6,-7],[-2,4]]
    assert Ainv == QMat.from_rows([[(6, 10), (-7, 10)], [(-2, 10), (4, 10)]])


def test_inverse_singular_raises():
    with pytest.raises(ValueError):
        QMat.from_rows([[1, 2], [2, 4]]).inverse()


def test_solve_exact():
    A = QMat.from_rows([[2, 1], [1, 3]])
    b = QMat.from_rows([[5], [10]])
    x = A.solve(b)
    assert A @ x == b
    # 2x+y=5, x+3y=10 ⇒ x=1, y=3
    assert x == QMat.from_rows([[1], [3]])


def test_solve_flat_rhs():
    A = QMat.from_rows([[1, 0], [0, 2]])
    x = A.solve([3, 8])                       # flat ⇒ column
    assert x == QMat.from_rows([[3], [4]])


def test_solve_singular_raises():
    A = QMat.from_rows([[1, 2], [2, 4]])
    with pytest.raises(ValueError):
        A.solve([1, 2])


def test_nullspace_dimension_and_annihilation():
    A = QMat.from_rows([[1, 2, 3], [2, 4, 6], [1, 1, 1]])
    ns = A.nullspace()
    # rank 2 (rows 1,2 dependent) over 3 cols ⇒ nullity 1.
    assert A.rank() == 2
    assert len(ns) == 1
    zero = QMat.zeros(3, 1)
    for v in ns:
        assert v.shape == (3, 1)
        assert A @ v == zero                  # exact annihilation
    # full-rank ⇒ empty nullspace
    assert QMat.identity(3).nullspace() == []


# ── 5. the boundary collapse ────────────────────────────────────────────────
def test_to_mat_returns_float_mat():
    A = QMat.from_rows([[(1, 2), (3, 4)], [1, 2]])
    m = A.to_mat()
    assert isinstance(m, Mat)
    assert not m.is_complex
    assert m.tolist() == [[0.5, 0.75], [1.0, 2.0]]


def test_from_mat_roundtrip_dyadic():
    qm = QMat.from_rows([[(1, 2), (3, 4)], [(5, 8), 1]])
    assert QMat.from_mat(qm.to_mat()) == qm


def test_from_mat_rejects_complex():
    cm = Mat.from_rows([[1 + 2j, 3]])
    with pytest.raises(ValueError):
        QMat.from_mat(cm)


# ── 6. THE KEYSTONE — bigint, no magnitude ceiling ──────────────────────────
# Entries far beyond int64: a = (10^40 + 1) / 3^30. Both num and den exceed 2^64.
_BIG_N = 10 ** 40 + 1
_BIG_D = 3 ** 30
_FA = Fraction(_BIG_N, _BIG_D)                # the exact-rational oracle scalar


def test_keystone_entries_exceed_int64():
    a = Q(_BIG_N, _BIG_D)
    # the entry numerator (10^40 + 1) is ~41 digits, far beyond int64; the
    # denominator 3^30 is ~15 digits (below int64), but a² and the inverse push
    # BOTH num and den past 2^64 (test_keystone_matmul_det_inverse_stay_exact).
    assert a.numerator > 2 ** 64
    assert _BIG_N > 2 ** 64 > _BIG_D          # asymmetric: only num exceeds int64 here


def test_keystone_matmul_det_inverse_stay_exact_bigint():
    a = Q(_BIG_N, _BIG_D)
    # Upper-triangular A = [[a, 1], [0, a]]; det = a², (A@A)[0,1] = 2a.
    A = QMat.from_rows([[a, Q(1, 1)], [Q(0, 1), a]])

    # ── matmul: (A@A)[0,1] == 2a, exact bigint ──
    A2 = A @ A
    two_a = 2 * _FA
    assert A2[0, 1] == Q(two_a.numerator, two_a.denominator)
    assert A2[0, 1].numerator == 20000000000000000000000000000000000000002
    assert A2[0, 1].denominator == 205891132094649
    assert A2[0, 0] == Q((_FA * _FA).numerator, (_FA * _FA).denominator)  # a²

    # ── det == a², exact bigint (81-digit numerator, far beyond int64) ──
    det = A.det()
    oracle_det = _FA * _FA
    assert det == Q(oracle_det.numerator, oracle_det.denominator)
    # the asserted huge-integer num/den (the proof of no magnitude ceiling):
    assert det.numerator == (
        100000000000000000000000000000000000000020000000000000000000000000000000000000001)
    assert det.denominator == 42391158275216203514294433201
    assert det.numerator > 2 ** 64 and det.denominator > 2 ** 64

    # ── inverse exact: A⁻¹ = [[1/a, -1/a²], [0, 1/a]]; verify A@A⁻¹ == I ──
    Ainv = A.inverse()
    assert A @ Ainv == QMat.identity(2)
    inv_a = 1 / _FA                            # 1/a oracle
    neg_inv_a2 = -(1 / (_FA * _FA))            # -1/a² oracle
    assert Ainv[0, 0] == Q(inv_a.numerator, inv_a.denominator)
    assert Ainv[1, 1] == Q(inv_a.numerator, inv_a.denominator)
    assert Ainv[0, 1] == Q(neg_inv_a2.numerator, neg_inv_a2.denominator)
    assert Ainv[1, 0] == Q(0, 1)
    # the inverse entries are themselves bigint exact
    assert Ainv[0, 1].denominator > 2 ** 64


def test_keystone_solve_stays_exact_bigint():
    a = Q(_BIG_N, _BIG_D)
    A = QMat.from_rows([[a, Q(1, 1)], [Q(0, 1), a]])
    b = QMat.from_rows([[a], [Q(1, 1)]])
    x = A.solve(b)
    # exact round-trip A@x == b with bigint entries
    assert A @ x == b
