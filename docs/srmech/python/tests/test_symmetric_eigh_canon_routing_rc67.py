"""rc67 — symmetric_eigendecompose → C-backed hermitian + eigenvector sign-canon.

Lane 1 of the post-floor numpy-removal: the real-symmetric eigh in
``laplacian.symmetric_eigendecompose`` routes onto the already-shipped, C-backed
``hermitian_eigendecompose`` (real-symmetric IS complex-Hermitian — native Jacobi
peer when present). The eigenvectors of a real-symmetric matrix are real (the
Hermitian path returns them with imaginary part ~0), so we take ``.real`` and
``_canonicalize_eigenvector_signs`` pins each column's ±1 sign (Class-K: flip so
its largest-magnitude entry is positive, ``col²`` magnitude, never ``abs()`` and
no float sqrt).

numpy-FREE (#564): numpy is GONE from srmech. ``symmetric_eigendecompose`` and
``_canonicalize_eigenvector_signs`` return plain Python lists. The eigenvalue
ORACLE is the framework's own exact ``eigvals_exact`` (real-symmetric); the
eigenvector sign / degenerate-subspace basis is non-unique, so correctness is
pinned by the basis-INVARIANT properties (reconstruction ``L = V·diag(w)·Vᵀ`` and
orthonormality) computed with plain-list arithmetic.
"""

from __future__ import annotations

import re
import pathlib

from srmech.amsc import laplacian
from srmech.amsc.cascade.matrix_cascades import eigvals_exact
from srmech.amsc.laplacian import _canonicalize_eigenvector_signs


# ── numpy-free helpers ────────────────────────────────────────────────


def _lcg(seed):
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield (state / 0x3FFFFFFF) - 1.0


def _rand_matrix(n, seed):
    g = _lcg(seed)
    return [[next(g) for _ in range(n)] for _ in range(n)]


def _rand_int_matrix(n, seed):
    """Integer-entried matrix (so the exact ``eigvals_exact`` oracle applies —
    its char-poly stays over ℤ, never ``Fraction(float)``)."""
    g = _lcg(seed)
    return [[int(round(next(g) * 5)) for _ in range(n)] for _ in range(n)]


def _transpose(A):
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def _matmul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _symmetrize(A):
    n = len(A)
    return [[(A[i][j] + A[j][i]) for j in range(n)] for i in range(n)]


def _cases():
    # Integer-entried (incl. the symmetrised random case) so the exact
    # ``eigvals_exact`` oracle applies to every matrix.
    yield "random-sym-5", _symmetrize(_rand_int_matrix(5, 42))
    yield "diagonal", [[v if i == j else 0 for j in range(4)]
                       for i, v in enumerate([3, 1, 5, 2])]
    yield "4-cycle-Laplacian-degen", [
        [int(round(x)) for x in row]
        for row in laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    ]
    yield "identity-fully-degen", [[1 if i == j else 0 for j in range(5)]
                                   for i in range(5)]
    yield "block-degen", [[v if i == j else 0 for j in range(5)]
                          for i, v in enumerate([2, 2, 2, 5, 5])]


def test_symmetric_eigendecompose_real_and_reconstructs_incl_degenerate():
    """Real float V, ascending eigvals == eigvals_exact, exact reconstruction."""
    for label, L in _cases():
        n = len(L)
        w, V = laplacian.symmetric_eigendecompose(L)
        # plain float lists (no numpy dtype), eigenvectors real.
        assert isinstance(w, list) and isinstance(V, list), label
        assert all(isinstance(x, float) for x in w), label
        assert all(isinstance(x, float) for row in V for x in row), label
        # ascending
        for i in range(n - 1):
            assert w[i + 1] - w[i] >= -1e-12, f"{label}: ascending"
        # eigenvalues match the framework's own EXACT oracle (sorted ascending).
        w_ref = sorted(eigvals_exact(L))
        for i in range(n):
            assert abs(w[i] - w_ref[i]) < 1e-9, f"{label}: eigvals"
        # reconstruction V·diag(w)·Vᵀ ≈ L (basis-invariant; holds on degenerate).
        Vd = [[V[i][k] * w[k] for k in range(n)] for i in range(n)]
        rec = _matmul(Vd, _transpose(V))
        for i in range(n):
            for j in range(n):
                assert abs(rec[i][j] - L[i][j]) < 1e-9, f"{label}: reconstruction"
        # orthonormal: Vᵀ·V = I.
        gram = _matmul(_transpose(V), V)
        for i in range(n):
            for j in range(n):
                assert abs(gram[i][j] - (1.0 if i == j else 0.0)) < 1e-9, \
                    f"{label}: orthonormality"


def test_canonicalize_eigenvector_signs_pins_pivot_positive():
    """Each (real) column's largest-magnitude entry is flipped to positive — a
    pure ±1 Class-K sign pin (no abs / no sqrt). numpy-free."""
    V = _rand_matrix(6, 1)
    C = _canonicalize_eigenvector_signs(V)
    n = 6
    for j in range(n):
        col = [C[i][j] for i in range(n)]
        # largest-|·| via col² (matches the helper's Class-K magnitude).
        k = max(range(n), key=lambda i: col[i] * col[i])
        assert col[k] > 0.0
    # a sign flip only multiplies a column by ±1: |C| == |V| columnwise and
    # every column is ± the original.
    for j in range(n):
        col_v = [V[i][j] for i in range(n)]
        col_c = [C[i][j] for i in range(n)]
        same = all(abs(col_c[i] - col_v[i]) < 1e-12 for i in range(n))
        flip = all(abs(col_c[i] + col_v[i]) < 1e-12 for i in range(n))
        assert same or flip, j
        for i in range(n):
            # |C| == |V| (squared, numpy-free).
            assert abs(col_c[i] * col_c[i] - col_v[i] * col_v[i]) < 1e-12


def test_canonicalize_is_deterministic():
    """Same input → same canonical output (a stable, settable convention)."""
    V = _rand_matrix(4, 2)
    assert _canonicalize_eigenvector_signs(V) == _canonicalize_eigenvector_signs(V)


def test_no_residual_np_linalg_eigh_in_symmetric_eigendecompose():
    """symmetric_eigendecompose no longer calls (or names) numpy eigh; it routes
    to hermitian_eigendecompose."""
    import srmech

    src = (pathlib.Path(srmech.__file__).parent / "amsc" / "laplacian.py").read_text(
        encoding="utf-8"
    )
    # isolate the symmetric_eigendecompose function body
    start = src.index("def symmetric_eigendecompose(")
    end = src.index("\ndef ", start + 1)
    body = src[start:end]
    assert not re.search(r"\b(?:np|numpy)\.linalg\.eigh\s*\(", body)
    assert "hermitian_eigendecompose(" in body
    assert "_canonicalize_eigenvector_signs(" in body
