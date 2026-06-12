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
the cutoff).

rc123 (numpy-free, #564): ``_pinv`` now takes a LIST OF COLUMNS (the
``(m, n)`` column stack the so8 callers form) and returns the ``(n, m)``
pseudoinverse as a nested ``list[list[float]]``; the reconstruction rides the
numpy-free ``mat_svd`` (the cascade SVD GEOMETRY carrier). This test is itself
numpy-FREE — the Moore-Penrose identity ``A·A⁺·A = A`` is checked over nested
lists (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""

from __future__ import annotations

import random
import re
import pathlib

from srmech.qm import so8


def _matmul(a, b):
    m, k, n = len(a), len(a[0]), len(b[0])
    return [[sum(a[i][t] * b[t][j] for t in range(k)) for j in range(n)]
            for i in range(m)]


def _max_abs(a):
    return max(abs(a[i][j]) for i in range(len(a)) for j in range(len(a[0])))


def _diff(a, b):
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _random_full_rank_columns(rng, m, n):
    """``n`` length-``m`` column vectors (Gaussian → full column rank w.p. 1)."""
    return [[rng.gauss(0.0, 1.0) for _ in range(m)] for _ in range(n)]


def _columns_to_matrix(columns):
    """Stack a list of column vectors into the (m, n) matrix (numpy-free)."""
    m = len(columns[0])
    n = len(columns)
    return [[columns[c][r] for c in range(n)] for r in range(m)]


def test_pinv_pseudoinverse_identity():
    """The reconstruction satisfies the defining Moore-Penrose identity
    ``A·A⁺·A = A`` for full-column-rank column stacks (the so8 usage shape)."""
    rng = random.Random(7)
    for m, n in [(28, 6), (28, 14), (28, 21), (10, 4), (6, 6)]:
        cols = _random_full_rank_columns(rng, m, n)
        A = _columns_to_matrix(cols)               # (m, n)
        Aplus = so8._pinv(cols)                     # (n, m) nested list
        recon = _matmul(_matmul(A, Aplus), A)       # A·A⁺·A
        assert _max_abs(_diff(recon, A)) < 1e-7


def test_pinv_left_inverse_on_full_column_rank():
    """For full column rank, ``A⁺·A = I_n`` (the left-inverse identity)."""
    rng = random.Random(0)
    m, n = 28, 12
    cols = _random_full_rank_columns(rng, m, n)
    A = _columns_to_matrix(cols)
    Aplus = so8._pinv(cols)
    prod = _matmul(Aplus, A)                         # (n, n) ≈ I
    eye = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    assert _max_abs(_diff(prod, eye)) < 1e-7


def test_killing_form_semisimple_full_rank():
    """The routed _killing_form still certifies g₂ semisimplicity (full rank 14)."""
    g2 = list(so8._g2_lists())
    k = so8._killing_form(g2)                        # nested list (rc123)
    n = len(g2)
    assert len(k) == n and len(k[0]) == n
    # symmetric Killing form.
    assert max(abs(k[i][j] - k[j][i]) for i in range(n) for j in range(n)) < 1e-9
    # Cartan's criterion: semisimple ⟺ non-degenerate (full rank) Killing form,
    # via the float-tolerant rank (the Killing form is SVD-derived float).
    cols = [[k[r][c] for r in range(n)] for c in range(n)]
    assert so8._rank_float(cols) == n


def test_no_residual_np_linalg_pinv_call_in_so8():
    """No `np.linalg.pinv(` / `numpy.linalg.pinv(` call survives in so8, and the
    pseudoinverse routes through the numpy-free cascade SVD (mat_svd)."""
    import srmech

    src = (
        pathlib.Path(srmech.__file__).parent / "qm" / "so8.py"
    ).read_text(encoding="utf-8")
    assert not re.search(r"\b(?:np|numpy)\.linalg\.pinv\s*\(", src)
    assert "_pinv(" in src
    # reconstruction must use the numpy-free cascade SVD, not numpy.
    assert "mat_svd(" in src
