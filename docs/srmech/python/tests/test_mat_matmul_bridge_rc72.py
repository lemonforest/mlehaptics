"""rc72 — the Mat↔native-dense-kernel bridge: numpy-free 2-D matmul (#564).

Foundation #2 of the carrier-removal arc. rc69 built the numpy-free 2-D ``Mat``
carrier (flat ``array('d')``, row-major, interleaved-``(re,im)`` for complex =
C99 ``double _Complex``); rc71 made signal_processing import-reachable numpy-
free. ``laplacian.mat_matmul`` is the bridge: it feeds ``Mat.buffer`` STRAIGHT
into the native ``srmech_dense_matmul_complex`` (zero-copy for complex, a one-
shot ``(re, 0)`` interleave for real) with **no numpy** on the dispatch path,
and falls back to a pure-Python triple loop (a cascade, never numpy ``@``) when
there is no native lib — so the op is unconditionally numpy-free.

numpy was REMOVED ENTIRELY from srmech (#564): these tests run + PASS with numpy
absent. The differential oracle is the textbook triple-loop product over the
input rows (``Σ_t A[i][t]·B[t][j]``), NOT numpy ``matmul`` / ``@``. The load-bearing
claim — that the op COMPUTES with numpy genuinely absent, on BOTH the native and
fallback paths — is proved in a subprocess that blocks numpy at ``sys.meta_path``
before the first import.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from srmech.amsc.laplacian import mat_matmul, LAPLACIAN_OPS
from srmech.amsc import laplacian as _lap
from srmech.amsc.mat import Mat


def _oracle(A_rows, B_rows):
    """Textbook triple-loop product Σ_t A[i][t]·B[t][j] (numpy-free oracle)."""
    m, k, n = len(A_rows), len(A_rows[0]), len(B_rows[0])
    return [
        [sum(complex(A_rows[i][t]) * complex(B_rows[t][j]) for t in range(k))
         for j in range(n)]
        for i in range(m)
    ]


def _max_abs_diff(C: Mat, ref) -> float:
    """max |C[i,j] − ref[i][j]| over a Mat and a list-of-lists oracle."""
    worst = 0.0
    for i in range(C.n_rows):
        for j in range(C.n_cols):
            worst = max(worst, abs(complex(C[i, j]) - complex(ref[i][j])))
    return worst


def test_mat_matmul_real_value():
    A = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])      # 2x3
    B = Mat.from_rows([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])    # 3x2
    C = mat_matmul(A, B)
    assert isinstance(C, Mat) and not C.is_complex
    assert C.shape == (2, 2)
    assert C.tolist() == [[4.0, 5.0], [10.0, 11.0]]


def test_mat_matmul_complex_value_vs_oracle():
    Ac = Mat.from_rows([[1 + 1j, 2 + 0j], [0 + 1j, 1 - 1j]])
    Bc = Mat.from_rows([[1 + 0j, 0 + 1j], [2 - 1j, 1 + 1j]])
    C = mat_matmul(Ac, Bc)
    assert isinstance(C, Mat) and C.is_complex
    ref = _oracle(Ac.tolist(), Bc.tolist())  # textbook triple loop, NOT @
    assert _max_abs_diff(C, ref) < 1e-12


def test_mat_matmul_rectangular_random_vs_oracle():
    rng_a = [[float((i * 7 + j * 3) % 11 - 5) for j in range(5)] for i in range(4)]
    rng_b = [[float((i * 5 + j * 2) % 9 - 4) for j in range(6)] for i in range(5)]
    C = mat_matmul(Mat.from_rows(rng_a), Mat.from_rows(rng_b))
    ref = _oracle(rng_a, rng_b)
    assert _max_abs_diff(C, ref) < 1e-9
    assert C.shape == (4, 6)


def test_mat_matmul_associativity():
    # (A·B)·C == A·(B·C) — the defining structural property, oracle-free.
    A = Mat.from_rows([[1.0, 2.0], [0.0, 1.0], [3.0, -1.0]])  # 3x2
    B = Mat.from_rows([[2.0, 0.0, 1.0], [1.0, 1.0, 0.0]])     # 2x3
    C = Mat.from_rows([[1.0, -1.0], [0.0, 2.0], [1.0, 1.0]])  # 3x2
    left = mat_matmul(mat_matmul(A, B), C)
    right = mat_matmul(A, mat_matmul(B, C))
    assert left.shape == right.shape == (3, 2)
    for i in range(3):
        for j in range(2):
            assert abs(left[i, j] - right[i, j]) < 1e-12


def test_mat_matmul_identity_is_neutral():
    # A·I == A and I·A == A.
    A = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])  # 2x3
    I3 = Mat.from_rows([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    I2 = Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])
    assert mat_matmul(A, I3).tolist() == A.tolist()
    assert mat_matmul(I2, A).tolist() == A.tolist()


def test_mat_matmul_fallback_matches_native(monkeypatch):
    """Forcing the no-native path (HAS_NATIVE False) yields the same values as
    the native path — the pure-Python triple loop is value-faithful."""
    Ac = Mat.from_rows([[1 + 1j, 2 + 0j], [0 + 1j, 1 - 1j]])
    Bc = Mat.from_rows([[1 + 0j, 0 + 1j], [2 - 1j, 1 + 1j]])
    native = mat_matmul(Ac, Bc)
    monkeypatch.setattr(_lap._native, "HAS_NATIVE", False)
    fallback = mat_matmul(Ac, Bc)
    assert isinstance(fallback, Mat) and fallback.is_complex
    assert fallback.shape == native.shape
    for i in range(native.n_rows):
        for j in range(native.n_cols):
            assert abs(complex(fallback[i, j]) - complex(native[i, j])) < 1e-12


def test_mat_matmul_shape_mismatch_raises():
    A = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])  # 2x3
    with pytest.raises(ValueError, match="incompatible"):
        mat_matmul(A, A)  # (2,3)·(2,3) — inner dims 3 vs 2


def test_mat_matmul_zero_inner_dim_is_zero_matrix():
    # A (2,0) · B (0,4) = the (2,4) zero matrix.
    Z = mat_matmul(Mat.from_rows([[], []]), Mat.from_flat([], 0, 4))
    assert Z.shape == (2, 4)
    assert Z.tolist() == [[0.0] * 4, [0.0] * 4]


def test_mat_matmul_rejects_non_mat():
    with pytest.raises(AssertionError):
        mat_matmul([[1.0]], [[1.0]])  # plain lists are not Mat


def test_mat_matmul_registered_in_all_and_ops():
    assert "mat_matmul" in _lap.__all__
    assert "mat_matmul" in LAPLACIAN_OPS


# ── the load-bearing numpy-FREE proof (subprocess; numpy blocked from start) ──

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


def test_mat_matmul_computes_numpy_free_native_and_fallback():
    proc = _run_numpy_free(
        """
        import sys
        assert "numpy" not in sys.modules
        from srmech.amsc.laplacian import mat_matmul
        from srmech.amsc import laplacian as lap
        from srmech.amsc.mat import Mat
        assert "numpy" not in sys.modules, "import pulled numpy in"

        Ac = Mat.from_rows([[1+1j, 2+0j],[0+1j, 1-1j]])
        Bc = Mat.from_rows([[1+0j, 0+1j],[2-1j, 1+1j]])

        def oracle(A, B):
            m, k, n = len(A), len(A[0]), len(B[0])
            return [[sum(complex(A[i][t])*complex(B[t][j]) for t in range(k))
                     for j in range(n)] for i in range(m)]
        ref = oracle(Ac.tolist(), Bc.tolist())

        # (1) native path, numpy absent
        C = mat_matmul(Ac, Bc)
        assert isinstance(C, Mat) and C.is_complex
        assert all(abs(complex(C[i, j]) - ref[i][j]) < 1e-9
                   for i in range(2) for j in range(2)), "native numpy-free mismatch"

        # (2) pure-Python fallback, numpy absent (HAS_NATIVE off)
        saved = lap._native.HAS_NATIVE
        lap._native.HAS_NATIVE = False
        try:
            F = mat_matmul(Ac, Bc)
            assert isinstance(F, Mat)
            assert all(abs(complex(F[i, j]) - ref[i][j]) < 1e-9
                       for i in range(2) for j in range(2)), "fallback numpy-free mismatch"
        finally:
            lap._native.HAS_NATIVE = saved

        # (3) real path, numpy absent
        R = mat_matmul(Mat.from_rows([[1.0,2.0,3.0],[4.0,5.0,6.0]]),
                       Mat.from_rows([[1.0,0.0],[0.0,1.0],[1.0,1.0]]))
        assert R.tolist() == [[4.0,5.0],[10.0,11.0]] and not R.is_complex
        print("MAT_MATMUL_NUMPY_FREE_OK")
        """
    )
    assert proc.returncode == 0, f"mat_matmul not numpy-free:\n{proc.stderr}"
    assert "MAT_MATMUL_NUMPY_FREE_OK" in proc.stdout, proc.stdout
