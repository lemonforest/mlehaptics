"""rc73 — the Mat↔native-dense-kernel bridge: numpy-free dense solve (`mat_solve`).

Carrier-removal bridge primitive #2 (#564), the peer of rc72's `mat_matmul`.
`laplacian.mat_solve(A: Mat, B: Mat) -> Mat` solves `A·X = B` with **NO numpy**:
the real `Mat.buffer`s (row-major float64) feed the native `srmech_dense_solve_f64`
zero-copy (`from_buffer`, C side `const`), output → a fresh `Mat`; with no native
lib / dim > 256 / singular it falls back to srmech's own exact-rational
Gauss–Jordan (`_solve_exact`, Class-N `Fraction`) → float64, so it is
unconditionally numpy-free.

Pins value-correctness (vs `numpy.linalg.solve` when numpy is present) AND —
the load-bearing claim — that `mat_solve` computes with numpy genuinely absent,
on both the native and the forced-fallback paths, in a subprocess that blocks
numpy at `sys.meta_path` before the first import.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from srmech.amsc.laplacian import mat_solve, LAPLACIAN_OPS
from srmech.amsc import laplacian as _lap
from srmech.amsc.mat import Mat

np = pytest.importorskip("numpy")


def test_mat_solve_vector_rhs_vs_numpy():
    A = Mat.from_rows([[3.0, 2.0, -1.0], [2.0, -2.0, 4.0], [-1.0, 0.5, -1.0]])
    B = Mat.from_rows([[1.0], [-2.0], [0.0]])
    X = mat_solve(A, B)
    assert isinstance(X, Mat) and not X.is_complex and X.shape == (3, 1)
    ref = np.linalg.solve(np.array(A.tolist()), np.array(B.tolist()))
    assert np.max(np.abs(np.array(X.tolist()) - ref)) < 1e-9


def test_mat_solve_matrix_rhs_vs_numpy():
    A = Mat.from_rows([[4.0, 3.0], [6.0, 3.0]])
    B = Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])  # solve A·X = I → X = A⁻¹
    X = mat_solve(A, B)
    ref = np.linalg.solve(np.array(A.tolist()), np.array(B.tolist()))
    assert np.max(np.abs(np.array(X.tolist()) - ref)) < 1e-9
    assert X.shape == (2, 2)
    # A·X = I check
    AX = np.array(A.tolist()) @ np.array(X.tolist())
    assert np.allclose(AX, np.eye(2), atol=1e-9)


def test_mat_solve_inverse_roundtrip():
    A = Mat.from_rows([[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]])
    Ainv = mat_solve(A, A)  # A·X = A → X = I
    assert np.allclose(np.array(Ainv.tolist()), np.eye(3), atol=1e-9)


def test_mat_solve_singular_raises():
    A = Mat.from_rows([[1.0, 2.0], [2.0, 4.0]])  # rank-deficient
    with pytest.raises(ZeroDivisionError):
        mat_solve(A, Mat.from_rows([[1.0], [1.0]]))


def test_mat_solve_complex_via_block_embedding():
    # rc95: complex mat_solve now solves via the real 2n×2n block embedding
    # (riding the native real solve) — numpy-free, value-faithful.
    A = Mat.from_rows([[2 + 1j, 1 - 1j, 0 + 0j],
                       [0 + 1j, 3 + 0j, 1 + 2j],
                       [1 + 0j, 0 - 1j, 2 + 1j]])
    B = Mat.from_rows([[1 + 1j], [2 - 1j], [0 + 3j]])
    X = mat_solve(A, B)
    assert isinstance(X, Mat) and X.is_complex and X.shape == (3, 1)
    ref = np.linalg.solve(np.array(A.tolist()), np.array(B.tolist()))
    assert np.max(np.abs(np.array(X.tolist()) - ref)) < 1e-9
    # A·X = B residual check
    AX = np.array(A.tolist()) @ np.array(X.tolist())
    assert np.allclose(AX, np.array(B.tolist()), atol=1e-9)


def test_mat_solve_shape_errors():
    A = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])  # 2x3 non-square
    with pytest.raises(ValueError, match="square"):
        mat_solve(A, Mat.from_rows([[1.0], [2.0]]))
    sq = Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])
    with pytest.raises(ValueError, match="row-count"):
        mat_solve(sq, Mat.from_rows([[1.0], [2.0], [3.0]]))  # B rows ≠ n


def test_mat_solve_registered_in_all_and_ops():
    assert "mat_solve" in _lap.__all__
    assert "mat_solve" in LAPLACIAN_OPS


# ── numpy-FREE proof (subprocess; numpy blocked from the first import) ──

_BLOCK_NUMPY = textwrap.dedent(
    """
    import sys
    class _NoNumpy:
        def find_spec(self, name, path=None, target=None):
            if name == "numpy" or name.startswith("numpy."):
                raise ModuleNotFoundError("No module named 'numpy'", name="numpy")
            return None
    sys.meta_path.insert(0, _NoNumpy())
    """
)


def _run_numpy_free(body: str) -> subprocess.CompletedProcess:
    script = _BLOCK_NUMPY + textwrap.dedent(body)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in sys.path if p)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env
    )


def test_mat_solve_computes_numpy_free_native_and_fallback():
    proc = _run_numpy_free(
        """
        from fractions import Fraction as F
        from srmech.amsc.laplacian import mat_solve
        from srmech.amsc import laplacian as lap
        from srmech.amsc.mat import Mat

        A = Mat.from_rows([[3.0,2.0,-1.0],[2.0,-2.0,4.0],[-1.0,0.5,-1.0]])
        B = Mat.from_rows([[1.0],[-2.0],[0.0]])

        def oracle(Ar, Br):
            n=len(Ar); w=len(Br[0])
            M=[[F(Ar[r][c]) for c in range(n)]+[F(Br[r][c]) for c in range(w)] for r in range(n)]
            for col in range(n):
                p=next(r for r in range(col,n) if M[r][col]!=0)
                M[col],M[p]=M[p],M[col]; iv=M[col][col]; M[col]=[x/iv for x in M[col]]
                for r in range(n):
                    if r!=col and M[r][col]!=0:
                        f=M[r][col]; M[r]=[M[r][cc]-f*M[col][cc] for cc in range(n+w)]
            return [[float(M[r][n+cc]) for cc in range(w)] for r in range(n)]
        ref = oracle(A.tolist(), B.tolist())

        X = mat_solve(A, B)  # native, numpy absent
        assert isinstance(X, Mat) and not X.is_complex
        assert all(abs(X[i,0]-ref[i][0]) < 1e-9 for i in range(3)), "native numpy-free mismatch"

        saved = lap._native.HAS_NATIVE
        lap._native.HAS_NATIVE = False
        try:
            Xf = mat_solve(A, B)  # exact-rational fallback, numpy absent
            assert isinstance(Xf, Mat)
            assert all(abs(Xf[i,0]-ref[i][0]) < 1e-9 for i in range(3)), "fallback numpy-free mismatch"
        finally:
            lap._native.HAS_NATIVE = saved
        print("MAT_SOLVE_NUMPY_FREE_OK")
        """
    )
    assert proc.returncode == 0, f"mat_solve not numpy-free:\n{proc.stderr}"
    assert "MAT_SOLVE_NUMPY_FREE_OK" in proc.stdout, proc.stdout
