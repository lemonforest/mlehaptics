"""Path A LMMSE — linear minimum-mean-square-error estimator.

Identity per the implementation plan §1: LMMSE IS a Class L (covariance
matrix-vector multiply on the joint observation-signal substrate) ∘ Class N
(rational gain ``R_xy R_yy^{-1}``) composition. Closed-form Wiener-Hopf
for the linear estimator.

Carrier-removal #564 (rc101): numpy-FREE — the Class-L gain solve routes through
the native :func:`~srmech.amsc.laplacian.mat_solve` over the numpy-free
:class:`~srmech.amsc.mat.Mat` carrier, and the ``K·(y-mean_y)`` estimate is a
pure-Python matvec. No top-level ``import numpy``.

Path B dual in Phase 6 (Path B covariance bound-vector).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Kay (1993)
*Fundamentals of Statistical Signal Processing: Estimation Theory* §12.
"""

from __future__ import annotations

from typing import List

from srmech.amsc.laplacian import mat_solve
from srmech.amsc.mat import Mat

OPERATION_NAME = "lmmse"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Kay (1993), 'Fundamentals of Statistical Signal Processing: "
    "Estimation Theory', Prentice Hall, §12 (Linear Bayesian Estimators)."
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


def op(
    y,
    R_yy,
    R_xy,
    *,
    mean_x=None,
    mean_y=None,
    D: int = 8192,
) -> List[float]:
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
    list[float]
        ``(n,)`` LMMSE estimate of x.
    """
    yv = _as_vec(y)
    Ryy = _as_rows(R_yy)
    Rxy = _as_rows(R_xy)
    m = len(yv)
    if len(Ryy) != m or any(len(r) != m for r in Ryy):
        raise ValueError(f"R_yy must be ({m}, {m})")
    n = len(Rxy)
    if any(len(r) != m for r in Rxy):
        raise ValueError(f"R_xy must have {m} columns")
    mx = [0.0] * n if mean_x is None else _as_vec(mean_x)
    my = [0.0] * m if mean_y is None else _as_vec(mean_y)
    # Class-L gain via the native Mat-carrier dense solve: K·R_yy = R_xy, i.e.
    # solve R_yyᵀ · Z = R_xyᵀ for Z (m, n), then K = Zᵀ (n, m). The solve is where
    # the cost (and the math) lives; it rides the native srmech_dense_solve_f64.
    Ryy_T = Mat.from_rows([[Ryy[j][i] for j in range(m)] for i in range(m)])  # (m, m)
    Rxy_T = Mat.from_rows([[Rxy[j][i] for j in range(n)] for i in range(m)])  # (m, n)
    Z = mat_solve(Ryy_T, Rxy_T)                                              # (m, n)
    # x_hat[i] = mean_x[i] + (Kᵀ row)·(y - mean_y) = mx[i] + Σ_j Z[j,i]·(y_j - my_j).
    dy = [yv[j] - my[j] for j in range(m)]
    return [mx[i] + sum(float(Z[j, i]) * dy[j] for j in range(m)) for i in range(n)]
