"""Path A DCT — closed-form discrete cosine transform (DCT-II / DCT-III).

Identity per the implementation plan §1: DCT IS a Class L (graph-Laplacian
eigenbasis on the Type-II line-graph) composition; the cosine basis is the
eigenbasis of the chain-graph Laplacian.

Carrier-removal #564 (rc103/rc104): numpy-FREE — the cosine basis matrix is
built directly as a list-of-lists through the Class-N ``rational.cos`` cascade
over the substrate-native ``_PI`` source (no ``np.cos`` / ``np.pi``), and the
transform is a pure-Python matvec (1-D) / per-axis row|column transform (2-D).
The old ``scipy.fft.dct`` fast-path is dropped (it requires numpy as a carrier);
the cascade DCT-matrix path IS the substrate-native realisation and stays
value-faithful to ``scipy_dct(..., norm=None)`` to ~1e-9. No top-level
``import numpy``.

Path B dual in Phase 6 (eigenbasis as bound-vector lookup).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Ahmed,
Natarajan & Rao (1974) + Rao & Yip (1990).
"""

from __future__ import annotations

from typing import List

from srmech.amsc import rational as _srn

OPERATION_NAME = "dct"
CLASS_COMPOSITION = ("L",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Ahmed, Natarajan & Rao (1974), 'Discrete cosine transform', IEEE Trans. "
    "Computers C-23(1), 90-93. DOI 10.1109/T-C.1974.223784 (Crossref). "
    "Rao & Yip (1990), 'Discrete Cosine Transform: Algorithms, Advantages, "
    "Applications', Academic Press."
)

# Class-N π cascade (Archimedes hexagon-doubling, Spike #32) — the substrate-
# native π source for the DCT basis angles; NOT math.pi / np.pi.
_PI = float(_srn.pi_cascade_digits(30))


def _dct_matrix(n: int, dct_type: int = 2) -> List[List[float]]:
    """Explicit DCT-II / DCT-III cosine basis matrix as a numpy-free
    list-of-lists. Each entry routes through the Class-N ``rational.cos``
    cascade (pi-free range reduction); value-faithful to the ``np.cos`` matrix
    to ~1e-9. ``op`` applies the ``2.0 *`` / normalisation scaling.
    """
    if dct_type == 2:
        # DCT-II: M[k][j] = cos(pi * k * (2j + 1) / (2N))
        return [
            [_srn.cos(_PI * k * (2.0 * j + 1.0) / (2.0 * n)) for j in range(n)]
            for k in range(n)
        ]
    if dct_type == 3:
        # DCT-III: M[k][j] = cos(pi * (2k + 1) * j / (2N))  (inverse of DCT-II)
        return [
            [_srn.cos(_PI * (2.0 * k + 1.0) * j / (2.0 * n)) for j in range(n)]
            for k in range(n)
        ]
    raise ValueError(f"dct_type must be 2 or 3; got {dct_type}")


def _transform(m: List[List[float]], x, n: int, dct_type: int) -> List[float]:
    """Apply the DCT basis to a length-``n`` vector, matching scipy's
    ``norm=None`` scaling exactly.

    DCT-II: ``y_k = 2 * sum_j M[k][j] x_j`` (every term weight 2).
    DCT-III: ``y_k = x_0 + 2 * sum_{j>=1} M[k][j] x_j`` — the ``j == 0`` term
    carries weight 1, not 2 (``M[k][0] = cos(0) = 1``), so DCT-III is the exact
    inverse of DCT-II up to the ``1/(2N)`` scaling. This is what the old
    ``scipy.fft.dct`` fast-path produced; the prior matrix fallback's blanket
    ``2.0 *`` was only reached when scipy was absent.
    """
    if dct_type == 3:
        return [
            x[0] * m[k][0] + 2.0 * sum(m[k][j] * x[j] for j in range(1, n))
            for k in range(n)
        ]
    return [2.0 * sum(m[k][j] * x[j] for j in range(n)) for k in range(n)]


def op(signal, *, dct_type: int = 2, axis: int = -1, D: int = 8192):
    """Discrete cosine transform of ``signal`` (numpy-free).

    Parameters
    ----------
    signal:
        Real array-like, 1-D or 2-D.
    dct_type:
        2 (DCT-II, default; the JPEG / audio-codec standard) or 3 (DCT-III,
        the inverse).
    axis:
        Axis over which to compute the DCT. Default last axis. For a 2-D input,
        ``-1``/``1`` transform each row, ``0`` transforms each column.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[float] (1-D input) or list[list[float]] (2-D input)
        Real DCT coefficients along ``axis`` (matches ``scipy_dct(..., norm=
        None)``: ``2 * (basis matvec)``).
    """
    data = signal.tolist() if hasattr(signal, "tolist") else list(signal)
    if len(data) == 0:
        return []

    if not isinstance(data[0], (list, tuple)):
        # 1-D transform.
        x = [float(v) for v in data]
        n = len(x)
        return _transform(_dct_matrix(n, dct_type), x, n, dct_type)

    if isinstance(data[0][0] if data[0] else 0.0, (list, tuple)):
        raise NotImplementedError(
            "numpy-free dct supports 1-D and 2-D signals only; got >2-D"
        )

    rows = [[float(v) for v in r] for r in data]
    h = len(rows)
    w = len(rows[0])
    if any(len(r) != w for r in rows):
        raise ValueError("dct expects a rectangular 2-D signal")

    if axis in (-1, 1):
        # Transform each ROW (length w).
        m = _dct_matrix(w, dct_type)
        return [_transform(m, rows[i], w, dct_type) for i in range(h)]
    if axis == 0:
        # Transform each COLUMN (length h) → output (h, w).
        m = _dct_matrix(h, dct_type)
        cols = [_transform(m, [rows[i][c] for i in range(h)], h, dct_type) for c in range(w)]
        # cols[c][k] is the k-th coefficient of column c; re-assemble as (h, w).
        return [[cols[c][k] for c in range(w)] for k in range(h)]
    raise ValueError(f"dct axis must be 0, 1, or -1 for 2-D input; got {axis}")
