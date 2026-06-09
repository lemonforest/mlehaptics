"""UPSTREAM §26 (#897) — Class-L Schur complement / Dirichlet-to-Neumann map.

The operator|operand FUSION op (F412/F417/F419):
``S = L_∂∂ − L_∂i · L_ii⁻¹ · L_i∂`` — the boundary effective Laplacian with the
interior (bulk) integrated out. Exact-rational (Class-N Fraction core) where
tractable; float realization on the `[scientific]` tier.
"""
from fractions import Fraction

import pytest

from srmech.amsc.laplacian import (
    dense_laplacian,
    schur_complement,
    dirichlet_to_neumann,
)

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


# A 3-edge path graph 0—1—2—3; boundary {0,3}, interior {1,2}. The Schur
# complement is the textbook effective-conductance fact: the two endpoints of
# a 3-edge unit-conductance path see effective conductance 1/3, so
# S = (1/3)·[[1,-1],[-1,1]] EXACTLY.
PATH4 = (4, [(0, 1), (1, 2), (2, 3)])
S_PATH4_EXACT = [
    [Fraction(1, 3), Fraction(-1, 3)],
    [Fraction(-1, 3), Fraction(1, 3)],
]


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


@pytest.mark.skipif(np is None, reason="float path needs numpy")
def test_float_path_matches_exact() -> None:
    L = dense_laplacian(*PATH4)
    S = schur_complement(L, [0, 3])  # default: float / scientific tier
    assert isinstance(S, np.ndarray)
    assert np.allclose(S, np.array([[1 / 3, -1 / 3], [-1 / 3, 1 / 3]]))


@pytest.mark.skipif(np is None, reason="needs numpy for the harmonic solve")
def test_dtn_property_boundary_normal_derivative() -> None:
    """S·x_∂ == (L·x)_∂ when x_i is the harmonic extension (L·x)_i = 0 —
    the defining Dirichlet-to-Neumann property."""
    L = np.asarray(dense_laplacian(*PATH4), dtype=float)
    xb = np.array([5.0, -2.0])
    Lii = L[np.ix_([1, 2], [1, 2])]
    Lip = L[np.ix_([1, 2], [0, 3])]
    xi = -np.linalg.solve(Lii, Lip @ xb)  # harmonic interior extension
    x = np.array([xb[0], xi[0], xi[1], xb[1]])
    S = np.asarray(schur_complement(L, [0, 3]), dtype=float)
    assert np.allclose(S @ xb, (L @ x)[[0, 3]])


@pytest.mark.skipif(np is None, reason="rank via numpy eigvals")
def test_area_law_dimension_and_rank() -> None:
    """Area law: the effective operator lives on the boundary — dim(S) = |∂|
    (not the bulk n). For a connected graph the DtN/Kron reduction inherits the
    all-ones null vector, so rank(S) = |∂| − 1 and the row sums vanish."""
    L = dense_laplacian(*PATH4)
    S = np.asarray(schur_complement(L, [0, 3]), dtype=float)
    assert S.shape == (2, 2)  # |∂| = 2, not n = 4 — the dimensional reduction
    ev = np.linalg.eigvalsh(S)
    assert int(np.sum(ev > 1e-9)) == 1  # rank = |∂| − 1 (connected graph)
    assert np.allclose(S.sum(axis=1), 0.0)  # all-ones null vector preserved


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
    S = schur_complement(L, [0, 1, 2, 3], exact=True)
    assert S == [[Fraction(L[a][b]) for b in range(4)] for a in range(4)]


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
