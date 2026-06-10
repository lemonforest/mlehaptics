"""Path A LMMSE — linear minimum-mean-square-error estimator.

Identity per the implementation plan §1: LMMSE IS a Class L (covariance
matrix-vector multiply on the joint observation-signal substrate) ∘ Class N
(rational gain ``R_xy R_yy^{-1}``) composition. Closed-form Wiener-Hopf
for the linear estimator.

Path B dual in Phase 6 (Path B covariance bound-vector).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Kay (1993)
*Fundamentals of Statistical Signal Processing: Estimation Theory* §12.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

# The math runs through srmech cascades, not numpy: ``dense_solve`` is the
# Class-L dense linear solve (native ``srmech_dense_solve_f64`` / exact-rational
# Gauss-Jordan), ``dense_matvec_complex`` the Class-L matrix-vector product.
# numpy stays carriers-only here (asarray / transpose / elementwise +/-).
from ...amsc.laplacian import dense_matvec_complex, dense_solve

OPERATION_NAME = "lmmse"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Kay (1993), 'Fundamentals of Statistical Signal Processing: "
    "Estimation Theory', Prentice Hall, §12 (Linear Bayesian Estimators)."
)


def op(
    y,
    R_yy,
    R_xy,
    *,
    mean_x=None,
    mean_y=None,
    D: int = 8192,
) -> np.ndarray:
    """LMMSE estimate ``x_hat = mean_x + R_xy R_yy^-1 (y - mean_y)``.

    Parameters
    ----------
    y:
        ``(m,)`` observation vector.
    R_yy:
        ``(m, m)`` observation-covariance matrix.
    R_xy:
        ``(n, m)`` signal-observation cross-covariance.
    mean_x:
        Optional ``(n,)`` mean of x. Default zero.
    mean_y:
        Optional ``(m,)`` mean of y. Default zero.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        ``(n,)`` LMMSE estimate of x.
    """
    y_arr = np.asarray(y, dtype=np.float64)
    Ryy = np.asarray(R_yy, dtype=np.float64)
    Rxy = np.asarray(R_xy, dtype=np.float64)
    if y_arr.ndim != 1:
        raise ValueError(f"y must be 1-D; got {y_arr.shape}")
    m = y_arr.shape[0]
    if Ryy.shape != (m, m):
        raise ValueError(f"R_yy must be ({m}, {m}); got {Ryy.shape}")
    if Rxy.shape[1] != m:
        raise ValueError(
            f"R_xy must have {m} columns; got {Rxy.shape}"
        )
    n = Rxy.shape[0]
    if mean_x is None:
        mx = np.zeros(n, dtype=np.float64)
    else:
        mx = np.asarray(mean_x, dtype=np.float64)
    if mean_y is None:
        my = np.zeros(m, dtype=np.float64)
    else:
        my = np.asarray(mean_y, dtype=np.float64)
    # Class-L gain via the srmech dense-solve cascade: K·R_yy = R_xy, i.e.
    # solve R_yy^T · Z = R_xy^T for Z, then K = Z^T. The solve is where the cost
    # (and the math) lives; it rides ``srmech_dense_solve_f64`` (no numpy linalg).
    Z = dense_solve(Ryy.T, Rxy.T)
    K = np.ascontiguousarray(Z, dtype=np.float64).T
    # Estimate x_hat = mean_x + K · (y - mean_y) via the srmech matvec cascade
    # (real result of the complex M·v primitive; numpy does only the ± packing).
    estimate = dense_matvec_complex(K, y_arr - my).real
    return mx + estimate
