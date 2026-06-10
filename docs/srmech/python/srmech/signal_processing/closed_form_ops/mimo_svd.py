"""Path A MIMO SVD — closed-form singular-value decomposition for channel matrix.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only (multi-antenna baseband
processing).

Identity per the implementation plan §1: MIMO-SVD IS a Class L (singular-value
decomposition on the channel matrix substrate) operation. The SVD ``H = U S V^H``
gives the closed-form precoder ``V`` and combiner ``U^H``.

Path B dual in Phase 6 (Path B channel-matrix SVD as bound vectors).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Telatar
(1999) + Golub & Van Loan (2013, 4th ed.) §8.6 (SVD algorithm).
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

OPERATION_NAME = "mimo_svd"
CLASS_COMPOSITION = ("L",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Telatar (1999), 'Capacity of multi-antenna Gaussian channels', European "
    "Trans. Telecommun. 10(6), 585-595. DOI 10.1002/ett.4460100604 "
    "(Crossref). Golub & Van Loan (2013, 4th ed.), 'Matrix Computations', "
    "Johns Hopkins, §8.6 (SVD)."
)


def op(channel_matrix, *, D: int = 8192) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """SVD of a MIMO channel matrix ``H``.

    Parameters
    ----------
    channel_matrix:
        ``(n_rx, n_tx)`` complex channel matrix.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        ``(U, S, Vh)`` such that ``H = U·diag(S)·Vh``.
        ``U`` is unitary ``(n_rx, n_rx)``, ``S`` is real non-negative
        ``(min(n_rx, n_tx),)``, ``Vh`` is unitary ``(n_tx, n_tx)``.
    """
    H = np.asarray(channel_matrix, dtype=np.complex128)
    if H.ndim != 2:
        raise ValueError(f"mimo_svd expects 2-D channel matrix; got {H.shape}")
    return np.linalg.svd(H, full_matrices=True)
