"""rc73 — the Mat↔native-dense-kernel bridge: numpy-free dense solve (`mat_solve`).

Carrier-removal bridge primitive #2 (#564), the peer of rc72's `mat_matmul`.
`laplacian.mat_solve(A: Mat, B: Mat) -> Mat` solves `A·X = B` with **NO numpy**:
the real `Mat.buffer`s (row-major float64) feed the native `srmech_dense_solve_f64`
zero-copy (`from_buffer`, C side `const`), output → a fresh `Mat`; with no native
lib / dim > 256 / singular it falls back to srmech's own exact-rational
Gauss–Jordan (`_solve_exact`, Class-N `Fraction`) → float64, so it is
unconditionally numpy-free.

numpy was REMOVED ENTIRELY from srmech (#564): these tests run + PASS with numpy
absent. The differential oracle for the real systems is the srmech exact-Fraction
`dense_solve(..., exact=True)`; for the complex system it is the residual
`A·X − B ≈ 0` via the numpy-free `mat_matmul` — NEVER `numpy.linalg.solve`. The
load-bearing claim — that `mat_solve` computes with numpy genuinely absent, on
both the native and the forced-fallback paths — is pinned in a subprocess that
blocks numpy at `sys.meta_path` before the first import.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from srmech.amsc.laplacian import mat_solve, mat_matmul, dense_solve, LAPLACIAN_OPS
from srmech.amsc import laplacian as _lap
from srmech.amsc.mat import Mat


def _max_residual(A: Mat, X: Mat, B: Mat) -> float:
    """max |（A·X − B)_ij| via the numpy-free list/Mat matmul."""
    AX = mat_matmul(A, X)
    worst = 0.0
    for i in range(B.n_rows):
        for j in range(B.n_cols):
            worst = max(worst, abs(complex(AX[i, j]) - complex(B[i, j])))
    return worst


def _max_vs_exact(X: Mat, A: Mat, B: Mat) -> float:
    """max |X[i,j] − exact-Fraction dense_solve(A,B)[i][j]| (real systems)."""
    ref = dense_solve(A.tolist(), B.tolist(), exact=True)  # list[list[Fraction]]
    worst = 0.0
    for i in range(X.n_rows):
        for j in range(X.n_cols):
            worst = max(worst, abs(float(X[i, j]) - float(ref[i][j])))
    return worst


def test_mat_solve_vector_rhs_vs_exact():
    A = Mat.from_rows([[3.0, 2.0, -1.0], [2.0, -2.0, 4.0], [-1.0, 0.5, -1.0]])
    B = Mat.from_rows([[1.0], [-2.0], [0.0]])
    X = mat_solve(A, B)
    assert isinstance(X, Mat) and not X.is_complex and X.shape == (3, 1)
    assert _max_vs_exact(X, A, B) < 1e-9        # oracle = exact-Fraction solve
    assert _max_residual(A, X, B) < 1e-9        # residual A·X − B ≈ 0


def test_mat_solve_matrix_rhs_is_inverse():
    A = Mat.from_rows([[4.0, 3.0], [6.0, 3.0]])
    Iden = Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])  # solve A·X = I → X = A⁻¹
    X = mat_solve(A, Iden)
    assert X.shape == (2, 2)
    assert _max_vs_exact(X, A, Iden) < 1e-9
    # A·X = I check (residual against the identity), numpy-free
    assert _max_residual(A, X, Iden) < 1e-9


def test_mat_solve_inverse_roundtrip():
    A = Mat.from_rows([[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]])
    X = mat_solve(A, A)  # A·X = A → X = I
    Iden = Mat.from_rows([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    worst = max(
        abs(complex(X[i, j]) - complex(Iden[i, j]))
        for i in range(3) for j in range(3)
    )
    assert worst < 1e-9


def test_mat_solve_singular_raises():
    A = Mat.from_rows([[1.0, 2.0], [2.0, 4.0]])  # rank-deficient
    with pytest.raises(ZeroDivisionError):
        mat_solve(A, Mat.from_rows([[1.0], [1.0]]))


def test_mat_solve_complex_via_block_embedding():
    # rc95: complex mat_solve solves via the real 2n×2n block embedding
    # (riding the native real solve) — numpy-free, value-faithful. Oracle =
    # the residual A·X − B ≈ 0 (Fraction can't carry complex, so verify the
    # defining equation directly via the numpy-free mat_matmul).
    A = Mat.from_rows([[2 + 1j, 1 - 1j, 0 + 0j],
                       [0 + 1j, 3 + 0j, 1 + 2j],
                       [1 + 0j, 0 - 1j, 2 + 1j]])
    B = Mat.from_rows([[1 + 1j], [2 - 1j], [0 + 3j]])
    X = mat_solve(A, B)
    assert isinstance(X, Mat) and X.is_complex and X.shape == (3, 1)
    assert _max_residual(A, X, B) < 1e-9


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
        import sys
        from fractions import Fraction as F
        from srmech.amsc.laplacian import mat_solve
        from srmech.amsc import laplacian as lap
        from srmech.amsc.mat import Mat
        assert "numpy" not in sys.modules, "import pulled numpy in"

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
