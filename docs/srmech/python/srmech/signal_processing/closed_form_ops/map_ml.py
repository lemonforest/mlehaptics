"""Path A MAP / ML — closed-form Bayesian maximum-a-posteriori / maximum-likelihood.

Identity per the implementation plan §1: MAP / ML IS a Class L (eigen-
decomposition on the prior + likelihood covariance composite) ∘ Class K
(sparse-support / argmax projection picking the MAP / ML estimate)
composition.

The closed-form reference ships the linear-Gaussian MAP estimator
``x_hat = (A^T R_v^{-1} A + R_x^{-1})^{-1} A^T R_v^{-1} y`` (Kay 1993 §11)
and the corresponding ML estimator when ``R_x^{-1} = 0`` (improper prior).

Carrier-removal #564 (rc102): numpy-FREE — the Class-L covariance inverse
(``R_v^{-1}`` / ``R_x^{-1}``) and the normal-equation solve route through the
native :func:`~srmech.amsc.laplacian.mat_solve` over the numpy-free
:class:`~srmech.amsc.mat.Mat` carrier; ``A^T R_v^{-1}`` rides
:func:`~srmech.amsc.laplacian.mat_matmul` and the ``A^T R_v^{-1} y`` /
``R_x^{-1} mu`` matvecs are pure-Python sums. No top-level ``import numpy``.

Path B dual in Phase 6 (Path B eigendecomposition + threshold).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Kay (1993)
*Fundamentals of Statistical Signal Processing: Estimation Theory* §7
(MLE) + §11 (MAP).
"""

from __future__ import annotations

from typing import List

from srmech.amsc.laplacian import mat_matmul, mat_solve
from srmech.amsc.mat import Mat

OPERATION_NAME = "map_ml"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Kay (1993), 'Fundamentals of Statistical Signal Processing: "
    "Estimation Theory', Prentice Hall, §7 (Maximum Likelihood) + §11 "
    "(MAP / Linear Bayesian)."
)


def _as_vec(v) -> List[float]:
    """Coerce a 1-D array-like to a list of float (numpy-free)."""
    raw = v.tolist() if hasattr(v, "tolist") else list(v)
    if raw and isinstance(raw[0], (list, tuple)):
        raise ValueError("expected 1-D vector")
    return [float(x) for x in raw]


def _as_rows(a) -> List[List[float]]:
    """Coerce a 2-D array-like to a list-of-rows of float (numpy-free)."""
    return [[float(x) for x in r] for r in (a.tolist() if hasattr(a, "tolist") else [list(r) for r in a])]


def _identity(n: int) -> "Mat":
    """Numpy-free ``(n, n)`` identity ``Mat`` (the ``np.eye`` replacement)."""
    return Mat.from_rows([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])


def op(
    y,
    A,
    R_noise,
    *,
    R_prior=None,
    mean_prior=None,
    D: int = 8192,
) -> List[float]:
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
    list[float]
        ``(n,)`` MAP / ML estimate of x.
    """
    yv = _as_vec(y)
    Arows = _as_rows(A)
    Rv = _as_rows(R_noise)
    m = len(Arows)
    if m == 0:
        raise ValueError("A must be 2-D and non-empty")
    n = len(Arows[0])
    if any(len(r) != n for r in Arows):
        raise ValueError("A must be 2-D (ragged rows)")
    if len(yv) != m:
        raise ValueError(f"y length {len(yv)} != A rows {m}")
    if len(Rv) != m or any(len(r) != m for r in Rv):
        raise ValueError(f"R_noise must be ({m}, {m})")
    # R_v^{-1} via the native Mat-carrier dense solve R_v · X = I (the covariance
    # inverse IS the linear solve against the identity; rides srmech_dense_solve_f64).
    Rv_inv = mat_solve(Mat.from_rows(Rv), _identity(m))                     # (m, m)
    # A^T · R_v^{-1} : A^T is (n, m), R_v^{-1} is (m, m) -> (n, m).
    A_T = Mat.from_rows([[Arows[j][i] for j in range(m)] for i in range(n)])  # (n, m)
    ATRinv = mat_matmul(A_T, Rv_inv)                                        # (n, m)
    # A^T R_v^{-1} y  (n,) pure-Python matvec.
    aty = [sum(float(ATRinv[i, j]) * yv[j] for j in range(m)) for i in range(n)]
    # A^T R_v^{-1} A  (n, n).
    M = mat_matmul(ATRinv, Mat.from_rows(Arows))                            # (n, n)
    if R_prior is None:
        # ML: x_hat = (A^T R_v^{-1} A)^{-1} A^T R_v^{-1} y.
        rhs = Mat.from_rows([[aty[i]] for i in range(n)])                   # (n, 1)
        x = mat_solve(M, rhs)                                               # (n, 1)
        return [float(x[i, 0]) for i in range(n)]
    # MAP: add the Gaussian-prior precision R_x^{-1}.
    Rx = _as_rows(R_prior)
    if len(Rx) != n or any(len(r) != n for r in Rx):
        raise ValueError(f"R_prior must be ({n}, {n})")
    mu = [0.0] * n if mean_prior is None else _as_vec(mean_prior)
    if len(mu) != n:
        raise ValueError(f"mean_prior must be ({n},)")
    Rx_inv = mat_solve(Mat.from_rows(Rx), _identity(n))                     # (n, n)
    # M' = A^T R_v^{-1} A + R_x^{-1} ; rhs = A^T R_v^{-1} y + R_x^{-1} mu.
    Mp = Mat.from_rows([[float(M[i, j]) + float(Rx_inv[i, j]) for j in range(n)] for i in range(n)])
    rxmu = [sum(float(Rx_inv[i, j]) * mu[j] for j in range(n)) for i in range(n)]
    rhs = Mat.from_rows([[aty[i] + rxmu[i]] for i in range(n)])             # (n, 1)
    x = mat_solve(Mp, rhs)                                                  # (n, 1)
    return [float(x[i, 0]) for i in range(n)]
