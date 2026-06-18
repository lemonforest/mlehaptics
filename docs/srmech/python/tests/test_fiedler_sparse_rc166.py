"""rc166 — the §51 sparse / iterative normalized-cut Fiedler (issue #1097).

``srmech.amsc.laplacian.fiedler_sparse`` is the ``n``-unbounded peer of the dense
``fiedler_vector`` / ``symmetric_eigendecompose`` path: power iteration on the
normalized operator ``B = I + D^-1/2 W D^-1/2``, deflating the √deg mode. These
tests prove (1) its **sign partition** agrees with the trusted dense
``normalized_laplacian`` + ``symmetric_eigendecompose`` 2nd-eigenvector reference
(the F785/F786 correctness gate — 100% on a worst-case dense graph), (2) the
``normalized_cut_bisect`` convenience splits the nodes by that sign, and (3) the
native standalone-C dispatch is sign-identical to the pure-Python cascade.

numpy-free (the laplacian module is numpy-free; this test must be too — the dense
reference is the package's own eigensolver, never numpy).
"""

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L


def _dense_normalized_fiedler_sign(n, edges, weights):
    """Reference sign partition: the 2nd eigenvector (col 1, ascending) of the
    dense normalized Laplacian, via the package's own numpy-free eigensolver."""
    _eig, V = L.symmetric_eigendecompose(L.normalized_laplacian(n, edges, weights))
    return [1 if V[i, 1] >= 0 else 0 for i in range(n)]


def _agree(a, b):
    """Sign-partition agreement up to a global flip."""
    m = sum(1 for x, y in zip(a, b) if x == y) / len(a)
    return max(m, 1.0 - m)


def _two_block_graph(nA, nB, *, within=1.0, bridge=0.05, order="blocked"):
    """A planted two-community graph (each block a clique, joined by a weak
    bridge). order='parity' interleaves the community labels by index parity —
    the case that defeats a naive [1,-1,1,...] init (orthogonal to the Fiedler).
    """
    n = nA + nB
    if order == "parity":
        label = [i % 2 for i in range(n)]
    else:
        label = [0 if i < nA else 1 for i in range(n)]
    edges, weights = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if label[i] == label[j]:
                edges.append((i, j)); weights.append(within)
    # one weak cross-bridge between the first node of each community
    a = label.index(0)
    b = label.index(1)
    edges.append((a, b)); weights.append(bridge)
    return n, edges, weights, label


@pytest.mark.parametrize("order", ["blocked", "parity"])
def test_sign_agrees_with_dense_reference(order):
    """The sparse Fiedler sign == the dense normalized-Fiedler sign (the gate)."""
    n, edges, weights, _label = _two_block_graph(12, 12, order=order)
    dense = _dense_normalized_fiedler_sign(n, edges, weights)
    fv = L.fiedler_sparse(n, edges, weights)
    sparse = [1 if fv[i] >= 0 else 0 for i in range(n)]
    assert _agree(dense, sparse) == 1.0, f"order={order}: {dense} vs {sparse}"


def test_fiedler_sparse_returns_vec_shape():
    """The result is a numpy-free 1-D Vec of length n."""
    n, edges, weights, _ = _two_block_graph(8, 8)
    fv = L.fiedler_sparse(n, edges, weights)
    assert fv.shape == (n,)
    assert sum(1 for i in range(n) if fv[i] >= 0) > 0  # not all one sign


def test_normalized_cut_bisect_splits_communities():
    """The bisection separates the two planted communities (up to a flip)."""
    n, edges, weights, label = _two_block_graph(10, 10, order="blocked")
    left, right = L.normalized_cut_bisect(n, edges, weights)
    assert sorted(left + right) == list(range(n))      # a partition
    assert left and right                              # a real cut
    # every left node shares a community; every right node shares a community
    assert len({label[i] for i in left}) == 1
    assert len({label[i] for i in right}) == 1
    assert {label[i] for i in left} != {label[i] for i in right}


def test_degenerate_graphs():
    """n < 2 -> zero vector (no cut); an edgeless graph -> zero vector."""
    fv0 = L.fiedler_sparse(1, [], [])
    assert fv0.shape == (1,) and fv0[0] == 0.0
    fv_edgeless = L.fiedler_sparse(5, [], [])
    assert all(fv_edgeless[i] == 0.0 for i in range(5))
    left, right = L.normalized_cut_bisect(1, [], [])
    assert (left, right) == ([], [0])                  # degenerate -> all right


def test_native_matches_pure(monkeypatch):
    """The native standalone-C fold is sign-identical to the pure cascade."""
    if not _native.has_native_fiedler_sparse():
        pytest.skip("no native sparse Fiedler (pure-Python-only lib)")
    n, edges, weights, _ = _two_block_graph(30, 30, order="parity", bridge=0.1)
    native = L.fiedler_sparse(n, edges, weights)
    native_sign = [1 if native[i] >= 0 else 0 for i in range(n)]
    monkeypatch.setattr(_native, "has_native_fiedler_sparse", lambda: False)
    pure = L.fiedler_sparse(n, edges, weights)
    pure_sign = [1 if pure[i] >= 0 else 0 for i in range(n)]
    assert native_sign == pure_sign
