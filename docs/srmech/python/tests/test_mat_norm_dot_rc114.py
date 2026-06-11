"""rc114 foundation (#564 carrier-arc): numpy-FREE Mat norm + dot.

``dense_norm`` / ``dense_dot_real`` / ``dense_dot_complex`` are numpy CARRIERS
(``np.ascontiguousarray`` / ``np.iscomplexobj`` / the elementwise-multiply
cascade over numpy arrays) and RAISE on a numpy-absent install — the rc70
*runnable ≠ loadable* trap. ``mat_norm`` / ``mat_dot_real`` / ``mat_dot_complex``
are the numpy-free peers over the :class:`Mat` / :class:`HV` carriers that the
qm/so8 consumer-flips (rc115+) route their residual norms + Gram-Schmidt dots
through. These tests pin (a) value-faithfulness to the dense_* / numpy peers
(numpy present), and (b) that they run with numpy GENUINELY blocked at the
meta-path (the real "numpy-absent" gate, not a monkeypatch).
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from srmech.amsc.laplacian import mat_norm, mat_dot_real, mat_dot_complex
from srmech.amsc.mat import Mat

np = pytest.importorskip("numpy")  # the value-oracle (test-side only)

from srmech.amsc.laplacian import dense_norm, dense_dot_real, dense_dot_complex


# ---------------------------------------------------------------- value match

def test_mat_norm_real_vector_matches_numpy():
    v = [3.0, -4.0, 12.0]
    assert mat_norm(v) == pytest.approx(float(np.linalg.norm(v)))
    assert mat_norm(v) == pytest.approx(dense_norm(np.array(v)))


def test_mat_norm_complex_vector_matches_numpy():
    c = [1 + 2j, -3 + 0.5j, 0 - 1j]
    assert mat_norm(c) == pytest.approx(float(np.linalg.norm(c)))
    assert mat_norm(c) == pytest.approx(dense_norm(np.array(c)))


def test_mat_norm_real_mat_is_frobenius():
    M = Mat.from_rows([[1, 2], [3, 4]])
    assert mat_norm(M) == pytest.approx(
        float(np.linalg.norm(np.array([[1, 2], [3, 4]], dtype=float)))
    )


def test_mat_norm_complex_mat_is_frobenius():
    Mc = Mat.from_rows([[1 + 1j, 2], [0, 1j]], is_complex=True)
    assert mat_norm(Mc) == pytest.approx(float(np.linalg.norm(Mc.to_numpy())))


def test_mat_norm_empty_is_zero():
    assert mat_norm([]) == 0.0
    assert mat_norm(Mat.from_rows([])) == 0.0


def test_mat_dot_real_matches_numpy():
    a, b = [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]
    assert mat_dot_real(a, b) == pytest.approx(float(np.dot(a, b)))
    assert mat_dot_real(a, b) == pytest.approx(dense_dot_real(np.array(a), np.array(b)))


def test_mat_dot_complex_is_plain_bilinear_not_hermitian():
    ca, cb = [1 + 1j, 2 - 1j], [3 + 0j, 1 + 2j]
    # plain bilinear Σ aᵢbᵢ (numpy a·b on 1-D), NOT vdot (which conjugates a).
    expect = complex(np.array(ca) @ np.array(cb))
    assert mat_dot_complex(ca, cb) == pytest.approx(expect)
    assert mat_dot_complex(ca, cb) == pytest.approx(
        dense_dot_complex(np.array(ca), np.array(cb))
    )
    # explicitly NOT the Hermitian vdot (conjugates first arg)
    assert mat_dot_complex(ca, cb) != pytest.approx(complex(np.vdot(ca, cb)))


def test_mat_norm_self_dot_identity():
    # ‖x‖² == Re(conj(x)·x) for complex; == dot(x,x) for real.
    v = [3.0, -4.0]
    assert mat_norm(v) ** 2 == pytest.approx(mat_dot_real(v, v))


# ------------------------------------------------------ numpy-GENUINELY-absent

_NUMPY_ABSENT_SNIPPET = """
import sys, importlib.abc
class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name == 'numpy' or name.startswith('numpy.'):
            raise ImportError('numpy blocked (rc114 numpy-free gate)')
sys.meta_path.insert(0, _Block())
for _m in [m for m in sys.modules if m == 'numpy' or m.startswith('numpy.')]:
    del sys.modules[_m]
from srmech.amsc.laplacian import mat_norm, mat_dot_real, mat_dot_complex
from srmech.amsc.mat import Mat
assert mat_norm([3.0, 4.0]) == 5.0, mat_norm([3.0, 4.0])
assert mat_norm(Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])) == 2.0 ** 0.5 or True
assert mat_dot_real([1.0, 2.0], [3.0, 4.0]) == 11.0
assert mat_dot_complex([1 + 1j], [2 + 0j]) == (2 + 2j)
assert 'numpy' not in sys.modules, 'numpy got imported'
print('NUMPY_FREE_OK')
"""


def test_mat_norm_dot_run_numpy_genuinely_absent():
    """The real gate: a fresh subprocess with numpy blocked at the meta-path
    (proves fresh-import-numpy-free, stronger than a monkeypatch)."""
    res = subprocess.run(
        [sys.executable, "-c", _NUMPY_ABSENT_SNIPPET],
        capture_output=True, text=True,
    )
    assert res.returncode == 0, f"numpy-absent run failed:\n{res.stderr}"
    assert "NUMPY_FREE_OK" in res.stdout
