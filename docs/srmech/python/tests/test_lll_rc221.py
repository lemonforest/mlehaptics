"""rc221 — the exact-ℚ LLL lattice-basis reduction op
(``srmech.amsc.cascade.matrix_cascades.lll_reduce`` + the byte-identical C peer
``srmech_lll_reduce``): the classic Lenstra–Lenstra–Lovász (1982) reduction, the
foundation for a future van Hoeij polynomial-factorization knapsack.

WHY: :func:`factor_integer_poly` recombines the Hensel-lifted mod-p factors by an
EXPONENTIAL Zassenhaus subset search; van Hoeij's fix reframes recombination as a
short-vector problem in a knapsack lattice, solved by LLL. This rc ships ONLY the
foundational LLL primitive (Python op + same-rc byte-identical C peer), exact ℚ
throughout — no float, no libm, no ``abs`` (the ``|μ| ≤ 1/2`` guard is a Class-K
sign branch).

Covers, run on BOTH the native and forced-pure arms (parametrized ``arm``):
  (a) KAT — the classic Wikipedia LLL example → the published reduced basis
      ``[[0,1,0],[1,0,1],[-1,0,2]]``; a 2-D example; an identity+target knapsack
      row that reduces to the identity — asserted EXACTLY;
  (b) size-reduced — ``|μ_{k,j}| ≤ 1/2`` for every ``j < k`` on the output
      (exact Fraction GSO oracle);
  (c) Lovász — ``‖b*_k‖² ≥ (δ − μ²_{k,k−1})·‖b*_{k−1}‖²`` on the output (exact);
  (d) SAME lattice — the recovered unimodular transform ``U = (B·Aᵀ)(A·Aᵀ)⁻¹``
      (exact Fraction) is INTEGER with ``det(U) = ±1`` AND ``U·A == B``;
  (e) native == pure — BYTE-IDENTICAL reduced basis over a deterministic-random
      integer-basis battery (both exact, same algorithm, same rounding);
  (f) delta validation + edge cases (m=0, m=1, ragged, degenerate) + determinism;
  (g) registration — ToolEntry, ``tools.total``, the Rosetta ``c_dispatched`` row,
      ``__all__``.
"""
from __future__ import annotations

import json
import random
from fractions import Fraction as FR
from pathlib import Path

import pytest

from srmech import introspect
from srmech.amsc import _native
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import lll_reduce


# ── arm helpers ────────────────────────────────────────────────────────────────
def _force_pure(fn):
    """Run fn with native dispatch masked → the complete pure path."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


@pytest.fixture(params=["native", "pure"])
def arm(request):
    return request.param


def _reduce(basis, delta, arm):
    if arm == "pure":
        return _force_pure(lambda: lll_reduce(basis, delta))
    return lll_reduce(basis, delta)


# ── exact-Fraction linear-algebra oracle (NOT the module under test) ────────────
def _dot(u, v):
    return sum(int(a) * int(b) for a, b in zip(u, v))


def _gso(rows):
    """Exact-ℚ Gram–Schmidt → (mu, B) with mu[i][j] (j<i), B[i]=‖b*_i‖²."""
    m = len(rows)
    n = len(rows[0]) if rows else 0
    mu = [[FR(0)] * m for _ in range(m)]
    B = [FR(0)] * m
    for i in range(m):
        for j in range(i):
            s = FR(_dot(rows[i], rows[j]))
            for k in range(j):
                s -= mu[j][k] * mu[i][k] * B[k]
            mu[i][j] = s / B[j]
        s = FR(_dot(rows[i], rows[i]))
        for k in range(i):
            s -= mu[i][k] * mu[i][k] * B[k]
        B[i] = s
    return mu, B


def _matmul(P, Q):
    return [[sum(P[i][k] * Q[k][j] for k in range(len(Q)))
             for j in range(len(Q[0]))] for i in range(len(P))]


def _transpose(A):
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def _inverse_fr(A):
    """Exact Fraction inverse of a square matrix via Gauss–Jordan (raises if
    singular)."""
    m = len(A)
    M = [[FR(A[i][j]) for j in range(m)] + [FR(1 if i == j else 0) for j in range(m)]
         for i in range(m)]
    for c in range(m):
        piv = next((r for r in range(c, m) if M[r][c] != 0), None)
        assert piv is not None, "singular matrix in _inverse_fr"
        M[c], M[piv] = M[piv], M[c]
        inv = M[c][c]
        M[c] = [x / inv for x in M[c]]
        for r in range(m):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [M[r][j] - f * M[c][j] for j in range(2 * m)]
    return [row[m:] for row in M]


def _det_fr(A):
    m = len(A)
    M = [[FR(x) for x in row] for row in A]
    det = FR(1)
    for c in range(m):
        piv = next((r for r in range(c, m) if M[r][c] != 0), None)
        if piv is None:
            return FR(0)
        if piv != c:
            M[c], M[piv] = M[piv], M[c]
            det = -det
        det *= M[c][c]
        inv = M[c][c]
        for r in range(c + 1, m):
            f = M[r][c] / inv
            M[r] = [M[r][j] - f * M[c][j] for j in range(m)]
    return det


def _unimodular_transform(A, B):
    """The exact transform U with U·A == B: U = (B·Aᵀ)(A·Aᵀ)⁻¹ (A full row-rank).
    Returns U as a Fraction matrix (the caller asserts integrality + det = ±1)."""
    At = _transpose(A)
    G = _matmul(A, At)           # A·Aᵀ  (m×m Gram, invertible for full rank)
    M = _matmul(B, At)           # B·Aᵀ
    return _matmul(M, _inverse_fr(G))


# ── property assertions (the exact verifications) ───────────────────────────────
def _assert_size_reduced(out):
    mu, _ = _gso(out)
    m = len(out)
    for i in range(m):
        for j in range(i):
            # |mu| <= 1/2 without abs(): -1/2 <= mu <= 1/2
            assert -FR(1, 2) <= mu[i][j] <= FR(1, 2), (
                f"size-reduction violated at μ[{i}][{j}] = {mu[i][j]}")


def _assert_lovasz(out, delta):
    mu, B = _gso(out)
    d = FR(delta[0], delta[1])
    for k in range(1, len(out)):
        assert B[k] >= (d - mu[k][k - 1] ** 2) * B[k - 1], (
            f"Lovász condition violated at k={k}")


def _assert_same_lattice(A, B):
    """B spans the SAME lattice as A: U = (B·Aᵀ)(A·Aᵀ)⁻¹ is integer, det = ±1,
    and U·A == B (recomputed exactly)."""
    assert len(A) == len(B)
    U = _unimodular_transform(A, B)
    for row in U:
        for x in row:
            assert x.denominator == 1, f"transform U not integer: {x}"
    assert _det_fr(U) in (FR(1), FR(-1)), f"det(U) = {_det_fr(U)} != ±1"
    Ui = [[int(x) for x in row] for row in U]
    recon = _matmul(Ui, [[int(v) for v in row] for row in A])
    assert recon == [[int(v) for v in row] for row in B], "U·A != B"


def _gram_det(rows):
    return _det_fr([[FR(_dot(rows[i], rows[j])) for j in range(len(rows))]
                    for i in range(len(rows))])


def _random_full_rank_basis(rng, m, n, lo, hi):
    while True:
        b = [[rng.randint(lo, hi) for _ in range(n)] for _ in range(m)]
        if _gram_det(b) != 0:
            return b


# ── (a) KAT — published reduced bases, asserted EXACTLY ─────────────────────────
def test_kat_wikipedia(arm):
    # A. K. Lenstra / H. W. Lenstra / L. Lovász example (Wikipedia LLL article).
    basis = [[1, 1, 1], [-1, 0, 2], [3, 5, 6]]
    out = _reduce(basis, (3, 4), arm)
    assert out == [[0, 1, 0], [1, 0, 1], [-1, 0, 2]]
    _assert_size_reduced(out)
    _assert_lovasz(out, (3, 4))
    _assert_same_lattice(basis, out)


def test_kat_two_dimensional(arm):
    basis = [[201, 37], [1648, 297]]
    out = _reduce(basis, (3, 4), arm)
    assert out == [[1, 32], [40, 1]]           # deterministic classic-LLL output
    _assert_size_reduced(out)
    _assert_lovasz(out, (3, 4))
    _assert_same_lattice(basis, out)
    # the reduced basis contains a genuinely short vector
    assert min(_dot(r, r) for r in out) <= min(_dot(r, r) for r in basis)


def test_kat_identity_knapsack(arm):
    # a knapsack-shaped basis (identity block + a big target row) reduces to the
    # identity — the shape van Hoeij's recombination lattice takes.
    basis = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [12345, 6789, 101112, 1]]
    out = _reduce(basis, (3, 4), arm)
    assert out == [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    _assert_same_lattice(basis, out)


# ── (b)(c)(d) property battery — size-reduced / Lovász / same-lattice ───────────
_DELTAS = [(3, 4), (1, 1), (99, 100), (51, 100), (2, 3)]


def test_property_battery(arm):
    rng = random.Random(20260711)
    for _ in range(120):
        m = rng.randint(2, 6)
        n = rng.randint(m, m + 3)
        delta = rng.choice(_DELTAS)
        basis = _random_full_rank_basis(rng, m, n, -12, 12)
        out = _reduce(basis, delta, arm)
        assert len(out) == m and all(len(r) == n for r in out)
        _assert_size_reduced(out)
        _assert_lovasz(out, delta)
        _assert_same_lattice(basis, out)


def test_property_larger_magnitude(arm):
    rng = random.Random(99)
    for _ in range(20):
        m = rng.randint(2, 5)
        n = m
        basis = _random_full_rank_basis(rng, m, n, -(10 ** 6), 10 ** 6)
        out = _reduce(basis, (3, 4), arm)
        _assert_size_reduced(out)
        _assert_lovasz(out, (3, 4))
        _assert_same_lattice(basis, out)


# ── (e) native == pure BYTE-IDENTICAL ──────────────────────────────────────────
def test_native_equals_pure_byte_identical():
    if not _native.has_native_lll():
        pytest.skip("no native LLL (pure-only build) — parity is trivially the "
                    "same body")
    rng = random.Random(4242)
    for _ in range(200):
        m = rng.randint(1, 6)
        n = rng.randint(m, m + 3)
        delta = rng.choice(_DELTAS)
        basis = _random_full_rank_basis(rng, m, n, -50, 50)
        nat = lll_reduce(basis, delta)
        pur = _force_pure(lambda: lll_reduce(basis, delta))
        assert nat == pur, (basis, delta, nat, pur)


def test_native_equals_pure_big_ints():
    if not _native.has_native_lll():
        pytest.skip("no native LLL")
    rng = random.Random(7)
    for _ in range(20):
        m = rng.randint(2, 5)
        basis = _random_full_rank_basis(rng, m, m, -(10 ** 9), 10 ** 9)
        nat = lll_reduce(basis, (3, 4))
        pur = _force_pure(lambda: lll_reduce(basis, (3, 4)))
        assert nat == pur


# ── (f) validation + edge cases + determinism ──────────────────────────────────
@pytest.mark.parametrize("bad", [(1, 4), (1, 5), (2, 1), (0, 1), (-3, 4), (3, 0)])
def test_delta_out_of_range_rejected(bad):
    with pytest.raises(ValueError):
        lll_reduce([[1, 0], [0, 1]], bad)


def test_edge_cases(arm):
    assert _reduce([], (3, 4), arm) == []
    assert _reduce([[3, 4, 5]], (3, 4), arm) == [[3, 4, 5]]     # m=1 trivially reduced
    # a single already-short row is returned unchanged
    assert _reduce([[-2, 1]], (3, 4), arm) == [[-2, 1]]


def test_ragged_rows_rejected():
    with pytest.raises(ValueError):
        lll_reduce([[1, 0, 0], [0, 1]], (3, 4))


def test_degenerate_dependent_basis_rejected():
    # row 2 = 2·row 0 → ‖b*_1‖² vanishes → LLL requires an independent basis.
    with pytest.raises(ValueError):
        _force_pure(lambda: lll_reduce([[1, 2, 3], [2, 4, 6]], (3, 4)))


def test_deterministic():
    rng = random.Random(1)
    basis = _random_full_rank_basis(rng, 5, 5, -80, 80)
    assert lll_reduce(basis, (3, 4)) == lll_reduce(basis, (3, 4))


def test_delta_one_terminates_and_reduces(arm):
    # δ = 1 (optimal LLL) still terminates (integer potential strictly drops).
    basis = [[15, 23, 11], [46, 15, 3], [32, 1, 1]]
    out = _reduce(basis, (1, 1), arm)
    _assert_size_reduced(out)
    _assert_lovasz(out, (1, 1))
    _assert_same_lattice(basis, out)


# ── (g) registration — ToolEntry + tools.total + Rosetta row + __all__ ──────────
def test_registration():
    assert "lll_reduce" in mc.__all__
    schema = introspect.describe()
    assert schema["tools"]["total"] == 466
    from srmech.amsc.tool_schema import get_tool_schema
    name = "srmech.amsc.cascade.matrix_cascades.lll_reduce"
    entries = [t for t in get_tool_schema().tools if t.name == name]
    assert len(entries) == 1
    entry = entries[0]
    assert "LLL" in entry.summary or "Lovász" in entry.summary
    assert entry.returns.type in ("list", "Mat")
    ndjson = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(line) for line in
            ndjson.read_text(encoding="utf-8").splitlines() if line.strip()]
    mine = [r for r in rows if r["exposed_as"] == name]
    assert len(mine) == 1 and mine[0]["bucket"] == "c_dispatched"
