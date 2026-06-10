"""rc74 — the Mat↔native-dense-kernel bridge: numpy-free Hermitian
eigendecomposition (`mat_hermitian_eigendecompose`).

Carrier-removal bridge primitive #3 — the LAST — completing the family with
rc72's `mat_matmul` and rc73's `mat_solve`.
`laplacian.mat_hermitian_eigendecompose(H: Mat) -> (eigvals: Mat, eigvecs: Mat)`
diagonalises `H = V·diag(λ)·Vᴴ` with **NO numpy**: the real/complex `Mat.buffer`
(interleaved-(re, im) row-major) feeds the native `srmech_hermitian_eigendecompose`
zero-copy; with no native lib / dim > 256 it falls back to srmech's own
pure-Python cyclic Jacobi (`_hermitian_eig_py` — real-symmetric directly /
complex-Hermitian via the real 2n×2n embedding), so it is unconditionally
numpy-free.

Correctness is pinned by eigenvalues + reconstruction (`H ≈ V·diag(λ)·Vᴴ`) +
unitarity (`Vᴴ·V ≈ I`), NOT element-wise parity (an eigenvector is fixed only
up to a phase; a degenerate eigenspace's basis is solver-chosen). The
load-bearing claim — that it computes with numpy genuinely absent on BOTH the
native and the forced-fallback paths — is pinned by a subprocess that blocks
numpy at `sys.meta_path` before the first import.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from srmech.amsc.laplacian import mat_hermitian_eigendecompose, LAPLACIAN_OPS
from srmech.amsc import laplacian as _lap
from srmech.amsc.mat import Mat

np = pytest.importorskip("numpy")


# ── numpy-free correctness helpers (no numpy in the asserts themselves) ──

def _recon_resid(H: Mat, ev: Mat, V: Mat) -> float:
    """max |H_ij - Σ_k V[i,k]·λ_k·conj(V[j,k])| — reconstruction residual."""
    n = H.n_rows
    worst = 0.0
    for i in range(n):
        for j in range(n):
            s = 0j
            for k in range(n):
                s += complex(V[i, k]) * complex(ev[k, 0]) * complex(V[j, k]).conjugate()
            worst = max(worst, abs(s - complex(H[i, j])))
    return worst


def _unitarity(V: Mat) -> float:
    """max |（Vᴴ·V)_ab - δ_ab| — columns orthonormal under the Hermitian product."""
    n = V.n_rows
    worst = 0.0
    for a in range(n):
        for b in range(n):
            s = sum(complex(V[i, a]).conjugate() * complex(V[i, b]) for i in range(n))
            worst = max(worst, abs(s - (1.0 if a == b else 0.0)))
    return worst


def test_mat_herm_eig_real_symmetric_vs_numpy():
    A = Mat.from_rows([[2.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]])
    ev, V = mat_hermitian_eigendecompose(A)
    assert isinstance(ev, Mat) and isinstance(V, Mat)
    assert ev.shape == (3, 1) and not ev.is_complex      # eigvals real (n,1)
    assert V.shape == (3, 3) and V.is_complex             # eigvecs ALWAYS complex
    ref = np.linalg.eigvalsh(np.array(A.tolist()))
    mine = [ev[i, 0] for i in range(3)]
    assert max(abs(mine[i] - ref[i]) for i in range(3)) < 1e-9
    assert _recon_resid(A, ev, V) < 1e-9
    assert _unitarity(V) < 1e-9


def test_mat_herm_eig_complex_hermitian_vs_numpy():
    H = Mat.from_rows([[2.0 + 0j, 1.0 + 1j, 0 + 0j],
                       [1.0 - 1j, 3.0 + 0j, 0 - 2j],
                       [0 + 0j, 0 + 2j, 1.0 + 0j]])
    ev, V = mat_hermitian_eigendecompose(H)
    ref = np.linalg.eigvalsh(np.array(H.tolist()))
    mine = [ev[i, 0] for i in range(3)]
    assert max(abs(mine[i] - ref[i]) for i in range(3)) < 1e-9
    assert _recon_resid(H, ev, V) < 1e-9
    assert _unitarity(V) < 1e-9


def test_mat_herm_eig_eigenvalue_equation():
    # H·v_k = λ_k·v_k for each eigenpair (the defining property).
    H = Mat.from_rows([[4.0 + 0j, 1.0 - 2j], [1.0 + 2j, 1.0 + 0j]])
    ev, V = mat_hermitian_eigendecompose(H)
    n = 2
    for k in range(n):
        for i in range(n):
            hv = sum(complex(H[i, t]) * complex(V[t, k]) for t in range(n))
            assert abs(hv - complex(ev[k, 0]) * complex(V[i, k])) < 1e-9


def test_mat_herm_eig_degenerate_complex():
    # eigenvalue 2 with multiplicity 2 (+ a distinct 5): the same-eigenvalue
    # Gram-Schmidt in the fallback must still pin a unitary basis.
    D = Mat.from_rows([[2.0 + 0j, 0 + 0j, 0 + 0j],
                       [0 + 0j, 2.0 + 0j, 0 + 0j],
                       [0 + 0j, 0 + 0j, 5.0 + 0j]])
    saved = _lap._native.HAS_NATIVE
    _lap._native.HAS_NATIVE = False  # force the pure-Python embedding fallback
    try:
        ev, V = mat_hermitian_eigendecompose(D)
    finally:
        _lap._native.HAS_NATIVE = saved
    assert [round(ev[i, 0], 9) for i in range(3)] == [2.0, 2.0, 5.0]
    assert _recon_resid(D, ev, V) < 1e-9
    assert _unitarity(V) < 1e-9


def test_mat_herm_eig_non_square_raises():
    A = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])  # 2×3
    with pytest.raises(ValueError, match="square"):
        mat_hermitian_eigendecompose(A)


def test_mat_herm_eig_empty():
    ev, V = mat_hermitian_eigendecompose(Mat.from_rows([]))
    assert ev.shape == (0, 1) and V.shape == (0, 0) and V.is_complex


def test_mat_herm_eig_registered_in_all_and_ops():
    assert "mat_hermitian_eigendecompose" in _lap.__all__
    assert "mat_hermitian_eigendecompose" in LAPLACIAN_OPS


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


def test_mat_herm_eig_computes_numpy_free_native_and_fallback():
    proc = _run_numpy_free(
        """
        from srmech.amsc.laplacian import mat_hermitian_eigendecompose
        from srmech.amsc import laplacian as lap
        from srmech.amsc.mat import Mat

        H = Mat.from_rows([[2.0+0j, 1.0+1j, 0+0j],
                           [1.0-1j, 3.0+0j, 0-2j],
                           [0+0j,   0+2j,   1.0+0j]])

        def recon(H, ev, V):
            n=H.n_rows; worst=0.0
            for i in range(n):
                for j in range(n):
                    s=sum(complex(V[i,k])*complex(ev[k,0])*complex(V[j,k]).conjugate() for k in range(n))
                    worst=max(worst, abs(s-complex(H[i,j])))
            return worst
        def unit(V):
            n=V.n_rows; worst=0.0
            for a in range(n):
                for b in range(n):
                    s=sum(complex(V[i,a]).conjugate()*complex(V[i,b]) for i in range(n))
                    worst=max(worst, abs(s-(1.0 if a==b else 0.0)))
            return worst

        ev, V = mat_hermitian_eigendecompose(H)  # native, numpy absent
        assert isinstance(V, Mat) and V.is_complex
        assert recon(H, ev, V) < 1e-9, "native numpy-free recon"
        assert unit(V) < 1e-9, "native numpy-free unitarity"

        saved = lap._native.HAS_NATIVE
        lap._native.HAS_NATIVE = False
        try:
            evf, Vf = mat_hermitian_eigendecompose(H)  # embedding fallback, numpy absent
            assert recon(H, evf, Vf) < 1e-9, "fallback numpy-free recon"
            assert unit(Vf) < 1e-9, "fallback numpy-free unitarity"
        finally:
            lap._native.HAS_NATIVE = saved
        print("MAT_HERM_EIG_NUMPY_FREE_OK")
        """
    )
    assert proc.returncode == 0, f"mat_hermitian_eigendecompose not numpy-free:\n{proc.stderr}"
    assert "MAT_HERM_EIG_NUMPY_FREE_OK" in proc.stdout, proc.stdout
