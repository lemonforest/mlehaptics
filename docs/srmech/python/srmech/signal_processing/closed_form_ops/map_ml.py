"""Path A MAP / ML — closed-form Bayesian maximum-a-posteriori / maximum-likelihood.

Identity per the implementation plan §1: MAP / ML IS a Class L (eigen-
decomposition on the prior + likelihood covariance composite) ∘ Class K
(sparse-support / argmax projection picking the MAP / ML estimate)
composition.

The closed-form reference ships the linear-Gaussian MAP estimator
``x_hat = (A^T R_v^{-1} A + R_x^{-1})^{-1} A^T R_v^{-1} y`` (Kay 1993 §11)
and the corresponding ML estimator when ``R_x^{-1} = 0`` (improper prior).

Path B dual in Phase 6 (Path B eigendecomposition + threshold).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Kay (1993)
*Fundamentals of Statistical Signal Processing: Estimation Theory* §7
(MLE) + §11 (MAP).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from srmech.amsc.laplacian import dense_matmul_real, dense_matvec_real, dense_solve

OPERATION_NAME = "map_ml"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Kay (1993), 'Fundamentals of Statistical Signal Processing: "
    "Estimation Theory', Prentice Hall, §7 (Maximum Likelihood) + §11 "
    "(MAP / Linear Bayesian)."
)


def op(
    y,
    A,
    R_noise,
    *,
    R_prior: Optional[np.ndarray] = None,
    mean_prior: Optional[np.ndarray] = None,
    D: int = 8192,
) -> np.ndarray:
    """MAP estimate (Gaussian prior) or ML estimate (no prior).

    Linear-Gaussian model: ``y = A x + v`` where ``v ~ N(0, R_noise)``.
    With Gaussian prior ``x ~ N(mean_prior, R_prior)`` -> MAP.
    Without prior -> ML.

    Parameters
    ----------
    y:
        ``(m,)`` observation.
    A:
        ``(m, n)`` observation matrix.
    R_noise:
        ``(m, m)`` noise covariance.
    R_prior:
        Optional ``(n, n)`` prior covariance. ``None`` -> ML estimator.
    mean_prior:
        Optional ``(n,)`` prior mean. Default zero.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        ``(n,)`` MAP / ML estimate of x.
    """
    y_arr = np.asarray(y, dtype=np.float64)
    A_arr = np.asarray(A, dtype=np.float64)
    Rv = np.asarray(R_noise, dtype=np.float64)
    if y_arr.ndim != 1:
        raise ValueError(f"y must be 1-D; got {y_arr.shape}")
    if A_arr.ndim != 2:
        raise ValueError(f"A must be 2-D; got {A_arr.shape}")
    m, n = A_arr.shape
    if y_arr.shape[0] != m:
        raise ValueError(f"y length {y_arr.shape[0]} != A rows {m}")
    if Rv.shape != (m, m):
        raise ValueError(f"R_noise must be ({m}, {m}); got {Rv.shape}")
    # Compute A^T R_noise^{-1}
    Rv_inv = np.linalg.inv(Rv)
    ATRinv = dense_matmul_real(A_arr.T, Rv_inv)
    if R_prior is None:
        # ML: x_hat = (A^T R_v^-1 A)^-1 A^T R_v^-1 y
        M = dense_matmul_real(ATRinv, A_arr)
        return dense_solve(M, dense_matvec_real(ATRinv, y_arr))
    # MAP
    Rx = np.asarray(R_prior, dtype=np.float64)
    if Rx.shape != (n, n):
        raise ValueError(f"R_prior must be ({n}, {n}); got {Rx.shape}")
    if mean_prior is None:
        mu = np.zeros(n, dtype=np.float64)
    else:
        mu = np.asarray(mean_prior, dtype=np.float64)
    Rx_inv = np.linalg.inv(Rx)
    M = dense_matmul_real(ATRinv, A_arr) + Rx_inv
    rhs = dense_matvec_real(ATRinv, y_arr) + dense_matvec_real(Rx_inv, mu)
    return dense_solve(M, rhs)
