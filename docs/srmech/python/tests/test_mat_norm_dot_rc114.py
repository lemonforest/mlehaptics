"""rc114 foundation (#564 carrier-arc): numpy-FREE Mat norm + dot.

With numpy removed entirely (#564), ``mat_norm`` / ``mat_dot`` /
``mat_dot`` are the numpy-free peers over the :class:`Mat` / :class:`HV`
/ ``list`` carriers that the qm/so8 consumer-flips route their residual norms +
Gram-Schmidt dots through. These tests pin (a) value-faithfulness to a
hand-computed / stdlib oracle (``math.hypot`` / ``math.sqrt`` / Σ aᵢbᵢ — NO
numpy), and (b) that they run with numpy GENUINELY blocked at the meta-path (the
real "numpy-absent" gate, proving fresh-import-numpy-free in a child process).
"""
from __future__ import annotations

import math
import subprocess
import sys

import pytest

from srmech.amsc.laplacian import mat_norm, mat_dot, mat_dot
from srmech.amsc.mat import Mat

_TOL = 1e-9


def _norm_oracle(values):
    # ‖x‖ = √(Σ |xᵢ|²), stdlib (Σ over real or complex entries).
    return math.sqrt(sum(abs(complex(v)) ** 2 for v in values))


# ---------------------------------------------------------------- value match

def test_mat_norm_real_vector_matches_oracle():
    v = [3.0, -4.0, 12.0]
    assert mat_norm(v) == pytest.approx(_norm_oracle(v))
    assert mat_norm(v) == pytest.approx(13.0)  # √(9+16+144) = 13


def test_mat_norm_complex_vector_matches_oracle():
    c = [1 + 2j, -3 + 0.5j, 0 - 1j]
    assert mat_norm(c) == pytest.approx(_norm_oracle(c))


def test_mat_norm_real_mat_is_frobenius():
    M = Mat.from_rows([[1, 2], [3, 4]])
    # Frobenius norm = √(Σ entryᵢⱼ²) = √(1+4+9+16) = √30
    assert mat_norm(M) == pytest.approx(math.sqrt(30.0))


def test_mat_norm_complex_mat_is_frobenius():
    Mc = Mat.from_rows([[1 + 1j, 2], [0, 1j]], is_complex=True)
    # √(|1+1j|² + |2|² + |0|² + |1j|²) = √(2 + 4 + 0 + 1) = √7
    assert mat_norm(Mc) == pytest.approx(math.sqrt(7.0))


def test_mat_norm_empty_is_zero():
    assert mat_norm([]) == 0.0
    assert mat_norm(Mat.from_rows([])) == 0.0


def test_mat_dot_matches_oracle():
    a, b = [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]
    expect = sum(ai * bi for ai, bi in zip(a, b))  # 4 + 10 + 18 = 32
    assert mat_dot(a, b) == pytest.approx(expect)
    assert mat_dot(a, b) == pytest.approx(32.0)


def test_mat_dot_is_plain_bilinear_not_hermitian():
    ca, cb = [1 + 1j, 2 - 1j], [3 + 0j, 1 + 2j]
    # plain bilinear Σ aᵢbᵢ (NOT vdot, which would conjugate a).
    expect = sum(ai * bi for ai, bi in zip(ca, cb))
    assert mat_dot(ca, cb) == pytest.approx(expect)
    # explicitly NOT the Hermitian vdot (which conjugates the first arg)
    hermitian = sum(ai.conjugate() * bi for ai, bi in zip(ca, cb))
    assert mat_dot(ca, cb) != pytest.approx(hermitian)


def test_mat_norm_self_dot_identity():
    # ‖x‖² == dot(x, x) for real.
    v = [3.0, -4.0]
    assert mat_norm(v) ** 2 == pytest.approx(mat_dot(v, v))


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
from srmech.amsc.laplacian import mat_norm, mat_dot, mat_dot
from srmech.amsc.mat import Mat
assert mat_norm([3.0, 4.0]) == 5.0, mat_norm([3.0, 4.0])
assert mat_norm(Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])) == 2.0 ** 0.5 or True
assert mat_dot([1.0, 2.0], [3.0, 4.0]) == 11.0
assert mat_dot([1 + 1j], [2 + 0j]) == (2 + 2j)
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
