"""Path A MIMO SVD — closed-form singular-value decomposition for channel matrix.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only (multi-antenna baseband
processing).

Identity per the implementation plan §1: MIMO-SVD IS a Class L (singular-value
decomposition on the channel matrix substrate) operation. The SVD ``H = U S V^H``
gives the closed-form precoder ``V`` and combiner ``U^H``.

Carrier-removal #564 (rc109): numpy-FREE — the decomposition routes through the
:func:`srmech.amsc.laplacian.mat_svd` Mat-carrier foundation (rc108): the right
singular vectors are eigenvectors of the Hermitian PSD Gram ``AᴴA`` via the
native-backed ``mat_hermitian_eigendecompose``, the singular values are
``√λ`` (Class-N ``rational.sqrt``), and the left vectors are
``uⱼ = A·vⱼ/σⱼ`` with an orthonormal completion of the null block. Inputs coerce
numpy-free via ``tolist()`` and the op returns plain Python ``list``s. No
top-level ``import numpy``.

**Accuracy** (per ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]``):
value-faithful — reconstruction ``H = U·diag(S)·Vᴴ`` + unitary ``U`` / ``Vh`` +
singular-values matching NumPy to ~1e-9 for the large σ; the small/null σ carry
the documented ~1e-7 caveat (fine for the dominant-mode precoder / combiner).

Path B dual in Phase 6 (Path B channel-matrix SVD as bound vectors).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Telatar
(1999) + Golub & Van Loan (2013, 4th ed.) §8.6 (SVD algorithm).
"""

from __future__ import annotations

from typing import List, Tuple

from srmech.amsc.laplacian import mat_svd
from srmech.amsc.mat import Mat

OPERATION_NAME = "mimo_svd"
CLASS_COMPOSITION = ("L",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Telatar (1999), 'Capacity of multi-antenna Gaussian channels', European "
    "Trans. Telecommun. 10(6), 585-595. DOI 10.1002/ett.4460100604 "
    "(Crossref). Golub & Van Loan (2013, 4th ed.), 'Matrix Computations', "
    "Johns Hopkins, §8.6 (SVD)."
)


def op(channel_matrix, *, D: int = 8192) -> Tuple[list, List[float], list]:
    """SVD of a MIMO channel matrix ``H``.

    Parameters
    ----------
    channel_matrix:
        ``(n_rx, n_tx)`` complex channel matrix (array-like / Mat / list-of-rows).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        ``(U, S, Vh)`` such that ``H = U[:, :k]·diag(S)·Vh[:k, :]``
        (``k = min(n_rx, n_tx)``), as plain Python lists (numpy-free, #564):
        ``U`` is unitary ``(n_rx, n_rx)`` list-of-rows, ``S`` is real
        non-negative descending ``list`` of length ``k``, ``Vh`` is unitary
        ``(n_tx, n_tx)`` list-of-rows.
    """
    seq = channel_matrix.tolist() if hasattr(channel_matrix, "tolist") else list(channel_matrix)
    if not seq or not isinstance(seq[0], (list, tuple)):
        raise ValueError(f"mimo_svd expects a 2-D channel matrix; got 1-D ({len(seq)} elems)")
    A = Mat.from_rows([[complex(x) for x in r] for r in seq], is_complex=True)
    U, S, Vh = mat_svd(A)
    u_rows = [[U[i, j] for j in range(U.n_cols)] for i in range(U.n_rows)]
    vh_rows = [[Vh[i, j] for j in range(Vh.n_cols)] for i in range(Vh.n_rows)]
    return u_rows, list(S), vh_rows
