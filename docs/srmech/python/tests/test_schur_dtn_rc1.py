"""UPSTREAM §26 (#897) — Class-L Schur complement / Dirichlet-to-Neumann map.

The operator|operand FUSION op (F412/F417/F419):
``S = L_∂∂ − L_∂i · L_ii⁻¹ · L_i∂`` — the boundary effective Laplacian with the
interior (bulk) integrated out. Exact-rational (Class-N Fraction core) where
tractable; float realization composes over the same Class-L solve.

numpy-FREE (#564): numpy is GONE from srmech. ``schur_complement`` now returns a
plain Python ``list[list[float]]`` (exact=True → ``list[list[Fraction]]``); the
float path is verified against the EXACT-Fraction reference (the framework's own
oracle), not numpy. The DtN-property and area-law invariants are checked with the
exact Class-L ``dense_solve`` + stdlib list arithmetic.
"""
from fractions import Fraction

import pytest

from srmech.amsc.laplacian import (
    dense_laplacian,
    schur_complement,
    dirichlet_to_neumann,
    dense_solve,
)


# A 3-edge path graph 0—1—2—3; boundary {0,3}, interior {1,2}. The Schur
# complement is the textbook effective-conductance fact: the two endpoints of
# a 3-edge unit-conductance path see effective conductance 1/3, so
# S = (1/3)·[[1,-1],[-1,1]] EXACTLY.
PATH4 = (4, [(0, 1), (1, 2), (2, 3)])
S_PATH4_EXACT = [
    [Fraction(1, 3), Fraction(-1, 3)],
    [Fraction(-1, 3), Fraction(1, 3)],
]


def _matvec(M, v):
    """Plain-list matrix·vector (numpy-free)."""
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def test_exact_rational_matches_effective_conductance() -> None:
    """exact=True returns the exact Fraction Schur complement (Class-N core)."""
    L = dense_laplacian(*PATH4)
    S = schur_complement(L, [0, 3], exact=True)
    assert S == S_PATH4_EXACT
    # All entries are exact rationals — no float leaked into the core.
    assert all(isinstance(x, Fraction) for row in S for x in row)


def test_dirichlet_to_neumann_alias_agrees() -> None:
    L = dense_laplacian(*PATH4)
    assert dirichlet_to_neumann(L, [0, 3], exact=True) == S_PATH4_EXACT


def test_float_path_matches_exact() -> None:
    """The default float path equals the exact-Fraction reference (numpy-free:
    the EXACT path is the oracle, not numpy)."""
    L = dense_laplacian(*PATH4)
    S = schur_complement(L, [0, 3])  # default: plain list[list[float]]
    assert isinstance(S, list) and isinstance(S[0], list)
    for i in range(2):
        for j in range(2):
            assert abs(S[i][j] - float(S_PATH4_EXACT[i][j])) < 1e-12


def test_dtn_property_boundary_normal_derivative() -> None:
    """S·x_∂ == (L·x)_∂ when x_i is the harmonic extension (L·x)_i = 0 —
    the defining Dirichlet-to-Neumann property. Harmonic interior solve via the
    exact Class-L ``dense_solve`` (Fraction); list arithmetic; numpy-free."""
    L = dense_laplacian(*PATH4).tolist()   # rc129: dense_laplacian → Mat; nested
    Lf = [[Fraction(int(round(L[i][j]))) for j in range(4)] for i in range(4)]
    xb = [Fraction(5), Fraction(-2)]
    interior, boundary = [1, 2], [0, 3]
    # Lii · xi = -Lip · xb  →  harmonic interior extension (exact).
    Lii = [[Lf[i][j] for j in interior] for i in interior]
    Lip = [[Lf[i][j] for j in boundary] for i in interior]
    rhs = [[-v] for v in _matvec(Lip, xb)]
    xi_col = dense_solve(Lii, rhs, exact=True)
    xi = [xi_col[0][0], xi_col[1][0]]
    x = [xb[0], xi[0], xi[1], xb[1]]
    # S (exact) · x_∂ must equal (L · x) restricted to the boundary.
    S = schur_complement(L, boundary, exact=True)
    lhs = _matvec(S, xb)
    Lx = _matvec(Lf, x)
    for k, node in enumerate(boundary):
        assert lhs[k] == Lx[node]


def test_area_law_dimension_and_rank() -> None:
    """Area law: the effective operator lives on the boundary — dim(S) = |∂|
    (not the bulk n). For a connected graph the DtN/Kron reduction inherits the
    all-ones null vector, so the row sums vanish and rank(S) = |∂| − 1. Checked
    over the exact-Fraction Schur complement; numpy-free."""
    L = dense_laplacian(*PATH4)
    S = schur_complement(L, [0, 3], exact=True)
    assert len(S) == 2 and len(S[0]) == 2  # |∂| = 2, not n = 4
    # all-ones null vector preserved: every row sums to exactly 0 (Fraction).
    for row in S:
        assert sum(row) == Fraction(0)
    # rank = |∂| − 1 = 1: S is rank-deficient (rows are proportional) but not
    # the zero matrix. The 2×2 determinant vanishes; some entry is nonzero.
    det = S[0][0] * S[1][1] - S[0][1] * S[1][0]
    assert det == Fraction(0)
    assert any(x != Fraction(0) for row in S for x in row)


def test_singular_interior_raises() -> None:
    """An interior component disconnected from the boundary has no harmonic
    extension — the exact solve raises ZeroDivisionError, not a silent NaN."""
    # Graph 0—1 with isolated nodes 2, 3; boundary {0}, interior {1,2,3}.
    L = dense_laplacian(4, [(0, 1)])
    with pytest.raises(ZeroDivisionError):
        schur_complement(L, [0], exact=True)


def test_no_interior_returns_full_block() -> None:
    """If every node is a boundary node, S = L (nothing to integrate out)."""
    L = dense_laplacian(*PATH4)
    Ln = L.tolist()                        # rc129: dense_laplacian → Mat; nested
    S = schur_complement(L, [0, 1, 2, 3], exact=True)
    assert S == [[Fraction(Ln[a][b]) for b in range(4)] for a in range(4)]


def test_validation_errors() -> None:
    L = dense_laplacian(*PATH4)
    with pytest.raises(ValueError):
        schur_complement(L, [])  # empty boundary
    with pytest.raises(ValueError):
        schur_complement(L, [0, 9])  # out of range
    with pytest.raises(ValueError):
        schur_complement(L, [0, 0, 3])  # duplicate


def test_registered_in_tool_schema() -> None:
    """Both names carry a ToolEntry (the tool-schema coverage ratchet)."""
    from srmech.amsc.tool_schema import get_tool_schema

    schema = get_tool_schema()
    assert schema.lookup("srmech.amsc.laplacian.schur_complement") is not None
    assert schema.lookup("srmech.amsc.laplacian.dirichlet_to_neumann") is not None
