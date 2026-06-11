"""rc64 — map_ml real covariance inverse → laplacian.dense_solve(M, I).

The numpy-removal `linalg_fft` sweep's smallest, safest sub-step. The two real
covariance-inverse sites in ``signal_processing/closed_form_ops/map_ml.py``
(``R_noise^{-1}`` and ``R_prior^{-1}`` in the ML / MAP estimators) route onto the
already-shipped Class-L solve ``laplacian.dense_solve(M, np.eye(n))`` — the
inverse IS the linear solve ``M · X = I``, unique and (for well-conditioned
covariances) bit-faithful to ``numpy.linalg.inv`` to ~1e-9.

(The so8 ``np.linalg.matrix_rank`` sites are deliberately NOT routed: the cascade
SVD's nullspace / small-singular-value accuracy is insufficient for an
absolute-tol rank count on a rank-deficient matrix — a numpy-as-accuracy site,
kept on numpy.)
"""

from __future__ import annotations

import math
import re
import pathlib

import numpy as np

from srmech.amsc.laplacian import dense_solve


def test_dense_solve_inverse_matches_numpy():
    """dense_solve(M, I) == numpy.linalg.inv(M) for well-conditioned M."""
    rng = np.random.default_rng(0)
    for n in (3, 5, 8, 12):
        a = rng.standard_normal((n, n))
        m = a @ a.T + n * np.eye(n)  # SPD, well-conditioned (a covariance shape)
        inv_cascade = np.asarray(dense_solve(m, np.eye(n)))
        np.testing.assert_allclose(inv_cascade, np.linalg.inv(m), atol=1e-9)


def test_map_ml_ml_and_map_estimators_run():
    """The routed ML and MAP estimators still produce finite estimates."""
    from srmech.signal_processing.closed_form_ops import map_ml

    rng = np.random.default_rng(3)
    m, n = 12, 4
    A = rng.standard_normal((m, n))
    x_true = rng.standard_normal(n)
    Rv = np.eye(m) * 0.1
    y = A @ x_true + rng.standard_normal(m) * 0.05

    x_ml = map_ml.op(y, A, Rv)
    assert isinstance(x_ml, list) and len(x_ml) == n  # rc102: numpy-free list return
    assert all(math.isfinite(v) for v in x_ml)

    Rx = np.eye(n) * 2.0
    x_map = map_ml.op(y, A, Rv, R_prior=Rx)
    assert isinstance(x_map, list) and len(x_map) == n  # rc102: numpy-free list return
    assert all(math.isfinite(v) for v in x_map)


def test_no_residual_np_linalg_inv_in_map_ml():
    import srmech

    pkg = pathlib.Path(srmech.__file__).parent
    txt = (pkg / "signal_processing/closed_form_ops/map_ml.py").read_text(encoding="utf-8")
    assert not re.search(r"\bnp\.linalg\.inv\s*\(", txt)
    # rc102 (carrier-removal #564): the covariance inverse now routes through the
    # numpy-free Mat-carrier ``mat_solve`` (was ``dense_solve``); op is numpy-free.
    # (The column-0 `import numpy` ratchet in test_numpy_carrier_ratchet.py is the
    # authoritative numpy-free gate; here we just confirm the routing target.)
    assert "mat_solve(" in txt
    assert not re.search(r"(?m)^import numpy", txt)
