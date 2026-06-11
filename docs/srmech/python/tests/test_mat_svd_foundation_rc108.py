"""rc108 — the `mat_svd` foundation: numpy-free **full** singular-value
decomposition over the Mat carrier (carrier-removal #564, foundation op #5).

`laplacian.mat_svd(A: Mat) -> (U: Mat, S: list[float], Vh: Mat)` mirrors
NumPy's ``numpy.linalg.svd(A, full_matrices=True)`` shape contract (U (m,m),
S (min(m,n),), Vh (n,n)) with **NO numpy**: it composes the native-backed
`mat_matmul` + `mat_hermitian_eigendecompose` on the Hermitian PSD Gram AᴴA
(right vectors = eigvecs, σ = √λ via the Class-N `rational.sqrt`), then
`uⱼ = A·vⱼ/σⱼ` + a pure-Python orthonormal Gram–Schmidt completion of the
left-nullspace block.

Per ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]`` the
contract is **value-faithful, NOT bit-identical**: SVD is non-unique (a per-pair
phase, and an arbitrary unitary basis inside a degenerate-σ / null subspace), so
correctness is pinned by **reconstruction** (`A ≈ U[:, :k]·diag(S)·Vh[:k, :]`),
**unitarity** (`UᴴU ≈ I`, `Vh·Vhᴴ ≈ I`), and **singular-value match** to NumPy
(the large σ; the small ones carry the documented ~1e-7 caveat) — never
element-wise parity. The numpy-free claim is pinned by a subprocess that blocks
numpy at `sys.meta_path` before the first import.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from srmech.amsc.laplacian import mat_svd, mat_matmul, LAPLACIAN_OPS
from srmech.amsc.mat import Mat

np = pytest.importorskip("numpy")


# ── numpy-free correctness helpers (no numpy in the asserts themselves) ──

def _recon_resid(A: Mat, U: Mat, S, Vh: Mat) -> float:
    """max |A_ij − Σ_k U[i,k]·S_k·Vh[k,j]| — reconstruction residual."""
    m, n = A.n_rows, A.n_cols
    k = len(S)
    worst = 0.0
    for i in range(m):
        for j in range(n):
            acc = 0j
            for t in range(k):
                acc += complex(U[i, t]) * S[t] * complex(Vh[t, j])
            worst = max(worst, abs(complex(A[i, j]) - acc))
    return worst


def _unitarity(M: Mat) -> float:
    """max |（Mᴴ·M − I)_ij| — how far M's columns are from orthonormal."""
    g = mat_matmul(M.conj().T, M)
    n = g.n_rows
    worst = 0.0
    for i in range(n):
        for j in range(n):
            expect = 1.0 if i == j else 0.0
            worst = max(worst, abs(complex(g[i, j]) - expect))
    return worst


# ── the matrices under test: real/complex × square/tall/wide × ranks ──

def _cases():
    cases = []
    # square full-rank real
    cases.append([[2.0, 0.0], [0.0, 3.0]])
    cases.append([[1.0, 2.0, 0.0], [0.0, 1.0, 1.0], [1.0, 0.0, 2.0]])
    # tall (m > n)
    cases.append([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    # wide (m < n)
    cases.append([[1.0, 0.0, 2.0], [0.0, 1.0, 1.0]])
    # complex square
    cases.append([[1 + 1j, 2 - 1j], [0 + 1j, 3 + 0j]])
    # complex tall
    cases.append([[1 + 0j, 0 + 1j], [1 - 1j, 2 + 0j], [0 + 0j, 1 + 1j]])
    # rank-deficient (row 2 = 2·row 0) — the documented small-σ caveat regime
    cases.append([[1.0, 2.0, 3.0], [0.0, 1.0, 1.0], [2.0, 4.0, 6.0]])
    return cases


@pytest.mark.parametrize("rows", _cases())
def test_mat_svd_reconstructs_and_is_unitary(rows):
    A = Mat.from_rows(rows)
    m, n = A.n_rows, A.n_cols
    U, S, Vh = mat_svd(A)
    # shapes match numpy full_matrices=True
    assert U.shape == (m, m)
    assert Vh.shape == (n, n)
    assert len(S) == min(m, n)
    # singular values descending + non-negative
    assert all(S[i] >= -1e-12 for i in range(len(S)))
    assert all(S[i] >= S[i + 1] - 1e-9 for i in range(len(S) - 1))
    # reconstruction A ≈ U[:, :k]·diag(S)·Vh[:k, :]
    assert _recon_resid(A, U, S, Vh) < 1e-7
    # U and Vh unitary
    assert _unitarity(U) < 1e-7
    assert _unitarity(Vh) < 1e-7


@pytest.mark.parametrize("rows", _cases())
def test_mat_svd_singular_values_match_numpy(rows):
    A = Mat.from_rows(rows)
    _, S, _ = mat_svd(A)
    s_np = np.linalg.svd(np.asarray(rows, dtype=np.complex128), compute_uv=False)
    # singular values are unique (unlike the U/V bases) — compare sorted desc.
    s_np = sorted([float(x) for x in s_np], reverse=True)
    assert len(S) == len(s_np)
    for got, ref in zip(S, s_np):
        # large σ ~1e-9; the smallest (near-zero / nullspace) carry the
        # documented ~1e-7 caveat — an absolute tolerance covers both.
        assert abs(got - ref) < 1e-6


def test_mat_svd_registered_and_rejects_empty():
    from array import array

    assert "mat_svd" in LAPLACIAN_OPS
    with pytest.raises(ValueError):
        mat_svd(Mat(array("d"), 0, 0))


def test_mat_svd_numpy_free_on_blocked_import():
    """mat_svd computes with numpy genuinely ABSENT (blocked at meta_path)."""
    code = textwrap.dedent(
        """
        import sys
        class _Block:
            def find_spec(self, name, path=None, target=None):
                if name == "numpy" or name.startswith("numpy."):
                    raise ImportError("numpy blocked for the test")
                return None
        sys.meta_path.insert(0, _Block())
        import importlib.util as u
        assert u.find_spec is not None
        from srmech.amsc.laplacian import mat_svd
        from srmech.amsc.mat import Mat
        A = Mat.from_rows([[2.0, 0.0, 1.0], [0.0, 3.0, 0.0], [1.0, 0.0, 2.0]])
        U, S, Vh = mat_svd(A)
        assert len(S) == 3 and S[0] >= S[1] >= S[2] >= -1e-12
        # reconstruction without numpy
        worst = 0.0
        for i in range(3):
            for j in range(3):
                acc = 0j
                for t in range(3):
                    acc += complex(U[i, t]) * S[t] * complex(Vh[t, j])
                worst = max(worst, abs(complex(A[i, j]) - acc))
        assert worst < 1e-7, worst
        assert "numpy" not in sys.modules, sorted(m for m in sys.modules if "numpy" in m)
        print("MAT_SVD_NUMPY_FREE_OK")
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert "MAT_SVD_NUMPY_FREE_OK" in out.stdout, (out.stdout, out.stderr)
