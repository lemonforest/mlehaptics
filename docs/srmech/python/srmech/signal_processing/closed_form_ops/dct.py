"""Path A DCT — closed-form discrete cosine transform (DCT-II / DCT-III).

Identity per the implementation plan §1: DCT IS a Class L (graph-Laplacian
eigenbasis on the Type-II line-graph) composition; the cosine basis is the
eigenbasis of the chain-graph Laplacian.

The closed-form reference uses scipy.fft.dct if available, else a numpy
matrix-multiply against the explicit DCT-II basis. Both are algebra-content
identical at D1 to the Class L eigenbasis projection.

Path B dual in Phase 6 (eigenbasis as bound-vector lookup).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Ahmed,
Natarajan & Rao (1974) + Rao & Yip (1990).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

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


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade).

    Replaces ``np.cos`` on the DCT-basis angle matrix — routes each angle
    through ``srmech.amsc.rational.cos`` (pi-free range reduction); numpy is
    used only as the array container. The broadcast (n, n) angle expression is
    materialised by ``np.asarray`` before per-element evaluation.
    """
    a = np.asarray(a, dtype=float)
    return np.array(
        [_srn.cos(float(v)) for v in a.ravel()], dtype=float
    ).reshape(a.shape)


def _dct_matrix(n: int, dct_type: int = 2) -> np.ndarray:
    """Explicit DCT-II / DCT-III orthonormal basis matrix."""
    k = np.arange(n)[:, None]
    j = np.arange(n)[None, :]
    if dct_type == 2:
        # DCT-II: X_k = sum_j x_j * cos(pi * k * (2j + 1) / (2N))
        return _ccos(np.pi * k * (2.0 * j + 1.0) / (2.0 * n))
    if dct_type == 3:
        # DCT-III: inverse of DCT-II (up to normalization)
        return _ccos(np.pi * (2.0 * k + 1.0) * j / (2.0 * n))
    raise ValueError(f"dct_type must be 2 or 3; got {dct_type}")


def op(signal, *, dct_type: int = 2, axis: int = -1, D: int = 8192):
    """Discrete cosine transform of ``signal``.

    Parameters
    ----------
    signal:
        Real array-like.
    dct_type:
        2 (DCT-II, default; the JPEG / audio-codec standard) or 3 (DCT-III,
        the inverse).
    axis:
        Axis over which to compute the DCT. Default last axis.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Real DCT coefficients along ``axis``.
    """
    arr = np.asarray(signal, dtype=np.float64)
    try:
        # Prefer scipy.fft.dct if available (fast, validated).
        from scipy.fft import dct as scipy_dct  # type: ignore[import-untyped]

        return scipy_dct(arr, type=dct_type, axis=axis, norm=None)
    except ImportError:
        if arr.ndim != 1:
            arr_2d = np.moveaxis(arr, axis, -1)
            n = arr_2d.shape[-1]
            M = _dct_matrix(n, dct_type=dct_type)
            out_2d = 2.0 * (arr_2d @ M.T)
            return np.moveaxis(out_2d, -1, axis)
        n = arr.shape[0]
        M = _dct_matrix(n, dct_type=dct_type)
        return 2.0 * (M @ arr)
