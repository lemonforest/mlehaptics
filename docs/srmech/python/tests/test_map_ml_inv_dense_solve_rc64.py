"""rc64 — map_ml real covariance inverse → laplacian.dense_solve(M, I).

The numpy-removal `linalg_fft` sweep's smallest, safest sub-step. The two real
covariance-inverse sites in ``signal_processing/closed_form_ops/map_ml.py``
(``R_noise^{-1}`` and ``R_prior^{-1}`` in the ML / MAP estimators) route onto the
already-shipped Class-L solve — the inverse IS the linear solve ``M · X = I``,
unique and (for well-conditioned covariances) bit-faithful.

numpy-FREE (#564): numpy is GONE from srmech, so this test runs with numpy NOT
installed. The solve oracle is the DEFINING IDENTITY ``M · M⁻¹ = I`` checked via
plain-list matmul (no ``np.linalg.inv`` reference); inputs are stdlib
``random.Random`` nested lists, never ndarrays.

(The so8 ``matrix_rank`` sites are deliberately NOT routed: the cascade SVD's
nullspace / small-singular-value accuracy is insufficient for an absolute-tol
rank count on a rank-deficient matrix.)
"""

from __future__ import annotations

import math
import random
import re
import pathlib

from srmech.amsc.laplacian import dense_solve


def _matmul(a, b):
    """Plain-list real matrix product a·b."""
    n, k, m = len(a), len(b), len(b[0])
    return [
        [sum(a[i][p] * b[p][j] for p in range(k)) for j in range(m)]
        for i in range(n)
    ]


def _spd(n: int, rng: random.Random):
    """A well-conditioned SPD matrix M = A·Aᵀ + n·I (a covariance shape)."""
    a = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(n)]
    aat = [
        [sum(a[i][p] * a[j][p] for p in range(n)) for j in range(n)]
        for i in range(n)
    ]
    for i in range(n):
        aat[i][i] += n
    return aat


def test_dense_solve_inverse_satisfies_defining_identity():
    """dense_solve(M, I) is M⁻¹ — verified by the defining identity M·M⁻¹ = I
    via plain-list matmul (numpy-free; no np.linalg.inv oracle)."""
    rng = random.Random(0)
    for n in (3, 5, 8, 12):
        m = _spd(n, rng)
        eye = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        inv_cascade = dense_solve(m, eye)
        assert isinstance(inv_cascade, list) and len(inv_cascade) == n
        prod = _matmul(m, inv_cascade)
        for i in range(n):
            for j in range(n):
                want = 1.0 if i == j else 0.0
                assert abs(prod[i][j] - want) < 1e-9


def test_dense_solve_exact_fraction_path_is_exact_inverse():
    """The EXACT-Fraction path (exact=True) returns a Fraction inverse whose
    M·M⁻¹ = I exactly (Fraction arithmetic — zero float residue)."""
    from fractions import Fraction

    # A small integer-entry SPD matrix has a rational inverse.
    m = [[4.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]]
    eye = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    inv_exact = dense_solve(m, eye, exact=True)
    # Every entry is an exact Fraction.
    assert all(isinstance(inv_exact[i][j], Fraction) for i in range(3) for j in range(3))
    # M (as Fractions) · M⁻¹ == I exactly.
    mfrac = [[Fraction(int(m[i][j])) for j in range(3)] for i in range(3)]
    prod = _matmul(mfrac, inv_exact)
    for i in range(3):
        for j in range(3):
            assert prod[i][j] == (Fraction(1) if i == j else Fraction(0))


def test_map_ml_ml_and_map_estimators_run():
    """The routed ML and MAP estimators still produce finite estimates from
    plain-list (numpy-free) inputs."""
    from srmech.signal_processing.closed_form_ops import map_ml

    rng = random.Random(3)
    m, n = 12, 4
    A = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(m)]
    x_true = [rng.gauss(0.0, 1.0) for _ in range(n)]
    Rv = [[0.1 if i == j else 0.0 for j in range(m)] for i in range(m)]
    y = [
        sum(A[i][j] * x_true[j] for j in range(n)) + rng.gauss(0.0, 1.0) * 0.05
        for i in range(m)
    ]

    x_ml = map_ml.op(y, A, Rv)
    assert isinstance(x_ml, list) and len(x_ml) == n  # rc102: numpy-free list return
    assert all(math.isfinite(v) for v in x_ml)

    Rx = [[2.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
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
