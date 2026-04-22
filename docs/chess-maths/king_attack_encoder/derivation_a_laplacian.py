"""Derivation A: king-centered Laplacian eigenchannel.

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.3.

Project the king's unit impulse onto the first k eigenvectors of the
symmetrized attack Laplacian. The projection magnitudes form the
k-dim feature vector.

Discontinuity mechanism: L_ka's topology changes discretely when
attack lines open or close; eigenvectors change discretely too.
This is the mechanism encode_640's bundled superposition lacks.
"""
import chess
import numpy as np
from scipy.linalg import eigh

from .attack_graph import attack_laplacian, king_square


DEFAULT_K = 5


def derivation_a_channel(board: chess.Board,
                         k: int = DEFAULT_K) -> np.ndarray:
    """Return a k-dim feature vector: projections of the king's impulse
    on the first k eigenvectors of the symmetrized attack Laplacian.

    If no king is on the board, returns zeros of length k (degenerate
    FEN). If k is out of [1, 64], raises ValueError.

    Eigenvector ordering: ascending eigenvalue. The k=1 component
    corresponds to the trivial zero-eigenvalue constant eigenvector;
    its projection on δ_king equals 1/sqrt(64), a normalization datum
    rather than structural signal — kept for completeness so the
    variance-explained calculation lines up with the same k.
    """
    if k <= 0 or k > 64:
        raise ValueError(f"k must be in [1, 64], got {k}")
    ks = king_square(board)
    if ks is None:
        return np.zeros(k, dtype=np.float64)
    L = attack_laplacian(board)
    _, eigvecs = eigh(L)
    delta_king = np.zeros(64, dtype=np.float64)
    delta_king[ks] = 1.0
    projections = eigvecs[:, :k].T @ delta_king
    return projections.astype(np.float64)


def derivation_a_similarity(board_before: chess.Board,
                            move: chess.Move,
                            k: int = DEFAULT_K) -> float:
    """Cosine similarity between Derivation A encodings before/after a
    move. Returns a float in [-1, 1]; 0.0 when either side has zero
    norm (degenerate king-absent positions)."""
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    a_before = derivation_a_channel(board_before, k=k)
    a_after = derivation_a_channel(board_after, k=k)
    norm = float(np.linalg.norm(a_before) * np.linalg.norm(a_after))
    if norm == 0.0:
        return 0.0
    return float(np.dot(a_before, a_after) / norm)


def variance_explained(board: chess.Board,
                       k: int = DEFAULT_K) -> float:
    """Diagnostic: what fraction of the king impulse's L2 norm
    (always 1.0 since δ is a unit impulse) is captured by projection
    onto the first k eigenvectors of the symmetrized attack Laplacian.

    Returns a float in [0, 1]. Values below ~0.8 at k = 5 suggest the
    eigenchannel is not a faithful summary of the king's local
    attack-graph environment.
    """
    ks = king_square(board)
    if ks is None:
        return 0.0
    L = attack_laplacian(board)
    _, eigvecs = eigh(L)
    delta_king = np.zeros(64, dtype=np.float64)
    delta_king[ks] = 1.0
    proj_k = eigvecs[:, :k].T @ delta_king
    captured = float(np.dot(proj_k, proj_k))
    return captured  # total norm is 1.0 by construction
