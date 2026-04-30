"""Graph-Laplacian eigenbasis move-legality oracle (4D).

4D analogue of :mod:`chess_spectral.spectral_legality`. Same shape
at higher dimension: 4096-square graph (8^4) and the per-piece
Laplacian factors as a Kronecker sum of four P_8 path-graph
Laplacians, so the eigenbasis is the same DCT-II tower the encoder
already uses (no new caching beyond the per-piece adjacency).

Used as the in-house 4D move-gen backend for the §16 search /
tournament harness. Avoids adding `python-chess4d-oana-chiru` as a
runtime dep (it stays in `[test]` extras for the parity gates that
need the upstream rule library).

Method
------
The 4D piece adjacencies live in :func:`tables_4d.piece_adjacencies_4d`
as sparse CSR matrices. We reuse them directly and compute the
graph-Laplacian eigendecomposition lazily per piece. Since the 4096×
4096 dense decomposition is too heavy to compute eagerly on import,
we eigendecompose on first call to :func:`piece_eigendecomposition`
and cache.

For 4D the dense materialisation of A_p is fine memory-wise (4096^2
int8 = 16 MB per piece, 5 pieces = 80 MB total, all cacheable on
demand). The eigendecomposition is heavier (4096^2 float64 = 134 MB
per piece), so we compute on demand and let the user choose the
trade-off.

Public API matches the 2D module's surface, with `_4d` suffixes on
piece-aware functions where ambiguity matters:

  is_reachable_4d(piece, from_sq4, to_sq4) -> bool
  reachable_targets_4d(piece, from_sq4) -> frozenset[int]
  spectral_reach_score_4d(piece, from_sq4, to_sq4) -> float
  piece_eigendecomposition_4d(piece) -> (eigvals, eigvecs)  -- LAZY
  supported_pieces_4d() -> list[str]
"""
from __future__ import annotations

from typing import Dict, FrozenSet, List, Tuple

import numpy as np
import scipy.sparse as sp

from . import tables_4d as _t4


# Cache: piece char -> dense (4096, 4096) adjacency.
_ADJ_CACHE_4D: Dict[str, np.ndarray] = {}

# Cache: piece char -> (eigenvalues[4096], eigenvectors[4096, 4096]).
_EIG_CACHE_4D: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

# Pieces this oracle covers (Hermitian reach predicates only). 4D pawns
# are W-axis or Y-axis, both directed -- same deferral as 2D pawns.
_HERMITIAN_PIECES_4D = frozenset({'N', 'B', 'R', 'Q', 'K'})

# Order of pieces in tables_4d.piece_adjacencies_4d() output.
_PIECE_INDEX_4D: Dict[str, int] = {
    'N': 0, 'B': 1, 'R': 2, 'Q': 3, 'K': 4,
}


def _piece_adjacency_4d(piece: str) -> np.ndarray:
    """Cached 4096×4096 dense adjacency for piece p on the 8^4 lattice.

    Materialised from the sparse adjacency in tables_4d. Symmetric
    (non-pawn pieces have involutive reach predicates).
    """
    if piece in _ADJ_CACHE_4D:
        return _ADJ_CACHE_4D[piece]
    if piece not in _HERMITIAN_PIECES_4D:
        raise ValueError(
            f"unknown piece {piece!r}; expected one of "
            f"{sorted(_HERMITIAN_PIECES_4D)} (pawns deferred -- see "
            f"module docstring)"
        )
    adjs = _t4.piece_adjacencies_4d()
    A_sparse = adjs[_PIECE_INDEX_4D[piece]]
    A = A_sparse.toarray().astype(np.float64)
    # Symmetrise defensively (no-op in steady state).
    A = np.maximum(A, A.T)
    _ADJ_CACHE_4D[piece] = A
    return A


def _piece_laplacian_4d(piece: str) -> np.ndarray:
    """L_p = D_p - A_p on the 4096-square lattice."""
    A = _piece_adjacency_4d(piece)
    deg = A.sum(axis=1)
    L = -A.copy()
    np.fill_diagonal(L, deg)
    return L


def piece_eigendecomposition_4d(piece: str
                                ) -> Tuple[np.ndarray, np.ndarray]:
    """Return (eigenvalues[4096], eigenvectors[4096, 4096]) of L_p.

    LAZY: the first call to this function for a given piece pays the
    eigendecomposition cost (~100 MB peak, ~5 seconds on a modern CPU
    for a 4096×4096 dense symmetric matrix). Subsequent calls return
    the cached pair.

    Eigenvalues ascending; eigenvectors as columns. Real-valued from
    Hermitian symmetry; rounding ~1e-12.
    """
    if piece in _EIG_CACHE_4D:
        return _EIG_CACHE_4D[piece]
    L = _piece_laplacian_4d(piece)
    eigvals, eigvecs = np.linalg.eigh(L)
    _EIG_CACHE_4D[piece] = (eigvals, eigvecs)
    return eigvals, eigvecs


def is_reachable_4d(piece: str, from_sq4: int, to_sq4: int) -> bool:
    """True iff piece p can geometrically reach `to_sq4` from
    `from_sq4` on an empty 8^4 lattice.

    O(1) integer lookup against the cached dense adjacency. Square
    indices in [0, 4096); use :func:`tables_4d.sq4` to convert
    4-tuple coordinates to indices.
    """
    if not 0 <= from_sq4 < _t4.N_SQUARES:
        raise ValueError(
            f"from_sq4 {from_sq4} out of range [0, {_t4.N_SQUARES})"
        )
    if not 0 <= to_sq4 < _t4.N_SQUARES:
        raise ValueError(
            f"to_sq4 {to_sq4} out of range [0, {_t4.N_SQUARES})"
        )
    A = _piece_adjacency_4d(piece)
    return bool(A[from_sq4, to_sq4] >= 0.5)


def reachable_targets_4d(piece: str, from_sq4: int) -> FrozenSet[int]:
    """Return the set of squares piece p can reach from from_sq4
    on an empty 8^4 lattice. O(4096) per query."""
    if not 0 <= from_sq4 < _t4.N_SQUARES:
        raise ValueError(
            f"from_sq4 {from_sq4} out of range [0, {_t4.N_SQUARES})"
        )
    A = _piece_adjacency_4d(piece)
    return frozenset(int(j) for j in np.flatnonzero(A[from_sq4] >= 0.5))


def spectral_reach_score_4d(piece: str,
                            from_sq4: int,
                            to_sq4: int) -> float:
    """Reconstruct A_p[from_sq4, to_sq4] from the eigenbasis directly.

    Same identity as 2D: A_ij = -L_ij = -sum_k λ_k v_k[i] v_k[j] for
    i != j; 0 for i == j (no self-loops).

    Triggers an eigendecomposition on first call (~5 sec); subsequent
    calls O(4096).

    Useful as the illustrative spectral oracle. For the fast lookup
    use :func:`is_reachable_4d`.
    """
    if not 0 <= from_sq4 < _t4.N_SQUARES:
        raise ValueError(
            f"from_sq4 {from_sq4} out of range [0, {_t4.N_SQUARES})"
        )
    if not 0 <= to_sq4 < _t4.N_SQUARES:
        raise ValueError(
            f"to_sq4 {to_sq4} out of range [0, {_t4.N_SQUARES})"
        )
    if from_sq4 == to_sq4:
        return 0.0
    eigvals, eigvecs = piece_eigendecomposition_4d(piece)
    L_ij = float(np.sum(eigvals * eigvecs[from_sq4] * eigvecs[to_sq4]))
    return float(-L_ij)


def supported_pieces_4d() -> List[str]:
    """The set of pieces this oracle covers ('N', 'B', 'R', 'Q', 'K').

    4D pawns (W-axis and Y-axis) are excluded; their reach is
    directed and breaks Hermiticity, same physics as the 2D pawn.
    """
    return sorted(_HERMITIAN_PIECES_4D)


__all__ = [
    "is_reachable_4d",
    "reachable_targets_4d",
    "spectral_reach_score_4d",
    "piece_eigendecomposition_4d",
    "supported_pieces_4d",
]
