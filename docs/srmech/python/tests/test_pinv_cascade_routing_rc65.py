"""rc65 — so8 Killing-form pseudoinverse → cascade SVD reconstruct.

The numpy-removal ``linalg_fft`` sweep's next single-site decrement. The lone
``np.linalg.pinv`` call in ``srmech/qm/so8.py`` (the ``_killing_form``
structure-constant least-squares solve) routes onto a ``_pinv`` helper that
reconstructs the Moore-Penrose pseudoinverse from the cascade SVD::

    A = U·diag(s)·Vᴴ   ⟹   A⁺ = V·diag(1/s)·Uᴴ

with NumPy's ``rcond = 1e-15`` small-singular-value cutoff. The pseudoinverse
is unique, so the per-factor U/V column-sign ambiguity of the SVD cancels —
value-faithful to NumPy's dense ``pinv`` (~1e-7) for the full-column-rank
generator stacks ``_killing_form`` forms (every singular value well clear of
the cutoff). Reconstruction uses ``laplacian.dense_matmul_real`` (the Class-L
cascade), NOT ``@``, so the numpy-math ledger stays honest.

(eigh / complex-inv / eig / svd-direct are deferred; ``matrix_rank`` stays on
numpy permanently — its cascade-SVD nullspace accuracy is insufficient for an
absolute-tol rank count on a rank-deficient matrix, a numpy-as-accuracy site.)
"""

from __future__ import annotations

import re
import pathlib

import numpy as np

from srmech.qm import so8


def test_pinv_helper_matches_numpy_pinv_full_rank():
    """_pinv == numpy.linalg.pinv for full-column-rank stacks (incl. matvec)."""
    rng = np.random.default_rng(0)
    for shape in [(28, 6), (28, 14), (28, 21), (28, 28), (10, 4), (6, 6)]:
        a = rng.standard_normal(shape)  # full column rank w.p. 1
        cascade = np.asarray(so8._pinv(a))
        np.testing.assert_allclose(cascade, np.linalg.pinv(a), atol=1e-7)
        # the actual usage shape: pinv applied as a matvec operator
        b = rng.standard_normal(shape[0])
        np.testing.assert_allclose(cascade @ b, np.linalg.pinv(a) @ b, atol=1e-7)


def test_pinv_pseudoinverse_identities():
    """The reconstruction satisfies the defining Moore-Penrose identity A·A⁺·A = A."""
    rng = np.random.default_rng(7)
    a = rng.standard_normal((28, 12))
    p = np.asarray(so8._pinv(a))
    np.testing.assert_allclose(a @ p @ a, a, atol=1e-7)


def test_killing_form_semisimple_full_rank():
    """The routed _killing_form still certifies g₂ semisimplicity (full rank 14)."""
    g2 = list(so8.g2_subalgebra())
    k = so8._killing_form(g2)
    assert k.shape == (len(g2), len(g2))
    # symmetric Killing form
    np.testing.assert_allclose(k, k.T, atol=1e-9)
    # Cartan's criterion: semisimple ⟺ non-degenerate (full rank) Killing form
    assert np.linalg.matrix_rank(k) == len(g2)


def test_no_residual_np_linalg_pinv_call_in_so8():
    """No `np.linalg.pinv(` / `numpy.linalg.pinv(` call survives in so8."""
    import srmech

    src = (
        pathlib.Path(srmech.__file__).parent / "qm" / "so8.py"
    ).read_text(encoding="utf-8")
    assert not re.search(r"\b(?:np|numpy)\.linalg\.pinv\s*\(", src)
    assert "_pinv(" in src
    # reconstruction must use the cascade matmul, not the `@` operator
    assert "dense_matmul_real(vh.T * s_inv, u.T)" in src
