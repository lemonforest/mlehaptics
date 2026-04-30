"""Graph-Laplacian eigenbasis move-legality oracle (2D).

Third independent move-legality oracle alongside python-chess
(reference) and :mod:`chess_spectral.phase_operators`
(modular-arithmetic predicates). Demonstrates that the same
graph-Laplacian eigenbasis the encoder uses for spectral encoding
also functions as a structural lookup table for move legality.

Method
------
For each non-pawn piece p ∈ {N, B, R, Q, K} we build the piece's
movement adjacency `A_p` on the 8×8 board (an existing table in
:mod:`chess_spectral.tables`). Its graph Laplacian
`L_p = D_p - A_p` admits eigendecomposition `L_p = V_p Λ_p V_p^T`
with V_p orthonormal. From spectral identity:

    A_p[i, j] = D_p[i, j] - L_p[i, j]
              = (degree_i if i == j else 0)
                - sum_k Λ_p[k, k] · V_p[i, k] · V_p[j, k]

Move (i, j) is **geometrically reachable** for piece p iff
`A_p[i, j] ≥ 1` (we use `>= 0.5` to absorb float rounding).

The oracle materialises both forms: the dense `A_p` (for fast
queries via integer lookup) AND the eigendecomposition (for
illustrative spectral verification + symmetry-class analysis).
Callers pick which mode suits them.

What this oracle does NOT cover
--------------------------------
* **Occupation-aware legality** (blocked sliders). A_p is the
  empty-board reach predicate. For occupation-aware legality,
  combine with the position dict via :mod:`phase_operators` or
  python-chess.
* **Pawns**. Pawn reach is directed (forward push, diagonal
  capture); the un-symmetrised reach matrix isn't a standard graph
  Laplacian. Pawns deferred to a future pseudo-Hermitian eta-metric
  variant analogous to qm_4d ADR-005.
* **Castling, en passant**. Special moves with non-local rules.
* **Check / pin / discovered attacks**. Whether a candidate move
  exposes the king is a separate predicate; this oracle answers
  only "could the piece geometrically reach the target square."

Cross-validation
----------------
:func:`agrees_with_phase_operators` cross-checks the oracle against
the existing modular-arithmetic predicate on every (piece, from_sq,
to_sq) triple at empty-board reach. Disagreement raises an
AssertionError with the offending triple -- catches drift between
the two oracles immediately.

Public API
----------
- :func:`is_reachable(piece, from_sq, to_sq)` -- O(1) integer lookup
- :func:`reachable_targets(piece, from_sq)` -- returns the set of
  reachable to-squares (sorted)
- :func:`spectral_reach_score(piece, from_sq, to_sq)` -- the raw
  eigenbasis reconstruction value, useful for debugging / research
- :func:`agrees_with_phase_operators(piece)` -- corpus-style
  cross-validation against the existing modular oracle
- :func:`piece_eigendecomposition(piece)` -- exposes (eigvals,
  eigvecs) for direct spectral analysis
"""
from __future__ import annotations

from typing import Dict, FrozenSet, List, Tuple

import numpy as np

from .tables import BOARD_DIM, SHORT_PFNS, build_adjacency


# ---- Piece adjacency + eigendecomposition --------------------------

# Cache: piece char -> dense (64, 64) adjacency.
_ADJ_CACHE: Dict[str, np.ndarray] = {}

# Cache: piece char -> (eigenvalues[64], eigenvectors[64, 64]) of L_p.
_EIG_CACHE: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

# Pieces this oracle covers (Hermitian reach predicates only).
_HERMITIAN_PIECES = frozenset({'N', 'B', 'R', 'Q', 'K'})


def _piece_adjacency(piece: str) -> np.ndarray:
    """Cached 64×64 dense adjacency for piece p on the 8×8 board.

    Uses :func:`tables.build_adjacency` -- the same source-of-truth
    the 2D encoder uses for piece-movement Laplacians. Symmetric for
    all non-pawn pieces; the symmetrize step is a no-op in steady
    state but documented for clarity.
    """
    if piece in _ADJ_CACHE:
        return _ADJ_CACHE[piece]
    if piece not in _HERMITIAN_PIECES:
        raise ValueError(
            f"unknown piece {piece!r}; expected one of "
            f"{sorted(_HERMITIAN_PIECES)} (pawns deferred -- see "
            f"module docstring)"
        )
    A = build_adjacency(SHORT_PFNS[piece])
    # build_adjacency is already symmetric for non-pawn pieces, but
    # symmetrize to be safe (catches any future tables.py change that
    # stops normalising boundary edges).
    A = np.maximum(A, A.T)
    _ADJ_CACHE[piece] = A
    return A


def _piece_laplacian(piece: str) -> np.ndarray:
    """L_p = D_p - A_p, where D_p is the diagonal degree matrix."""
    A = _piece_adjacency(piece)
    deg = A.sum(axis=1)
    return np.diag(deg) - A


def piece_eigendecomposition(piece: str) -> Tuple[np.ndarray, np.ndarray]:
    """Return (eigenvalues[64], eigenvectors[64, 64]) of L_p.

    Eigenvalues are returned ascending; eigenvectors as columns of
    the second array (eigenvectors[:, k] is the k-th eigenvector).
    Cached on first call -- subsequent calls return the cached pair.

    L_p is real-symmetric so :func:`numpy.linalg.eigh` returns real
    eigenvalues and orthonormal eigenvectors. Rounding to ~1e-12 is
    typical.
    """
    if piece in _EIG_CACHE:
        return _EIG_CACHE[piece]
    L = _piece_laplacian(piece)
    eigvals, eigvecs = np.linalg.eigh(L)
    _EIG_CACHE[piece] = (eigvals, eigvecs)
    return eigvals, eigvecs


# ---- Oracle queries -------------------------------------------------


def is_reachable(piece: str, from_sq: int, to_sq: int) -> bool:
    """True iff piece p can geometrically reach `to_sq` from `from_sq`
    on an otherwise-empty 8×8 board.

    O(1) integer lookup against the cached adjacency matrix.

    Parameters
    ----------
    piece : str
        One of 'N', 'B', 'R', 'Q', 'K'. Pawns raise ValueError.
    from_sq, to_sq : int
        Square indices in [0, 64). Encoder convention: 0=a8, 7=h8,
        56=a1, 63=h1 (row-major from a8). Out-of-range indices raise
        ValueError.

    Returns
    -------
    True if the move is in the empty-board reach set; False
    otherwise. Self-loops (from_sq == to_sq) return False -- A_p has
    zero diagonal by construction (graphs without self-loops).
    """
    if not 0 <= from_sq < BOARD_DIM:
        raise ValueError(f"from_sq {from_sq} out of range [0, 64)")
    if not 0 <= to_sq < BOARD_DIM:
        raise ValueError(f"to_sq {to_sq} out of range [0, 64)")
    A = _piece_adjacency(piece)
    return bool(A[from_sq, to_sq] >= 0.5)


def reachable_targets(piece: str, from_sq: int) -> FrozenSet[int]:
    """Return the set of squares piece p can reach from `from_sq`
    on an empty board. Sorted ascending in the returned frozenset
    iteration order? -- frozensets aren't ordered; use sorted() at
    the call site if needed.

    Implementation: row-slice of A_p; O(64) per query, vectorised.
    """
    if not 0 <= from_sq < BOARD_DIM:
        raise ValueError(f"from_sq {from_sq} out of range [0, 64)")
    A = _piece_adjacency(piece)
    return frozenset(int(j) for j in np.flatnonzero(A[from_sq] >= 0.5))


def spectral_reach_score(piece: str,
                         from_sq: int,
                         to_sq: int) -> float:
    """Reconstruct A_p[from_sq, to_sq] from the eigenbasis directly.

    Returns the value of `sum_k λ_k · v_k[from_sq] · v_k[to_sq]`
    via degree-Laplacian identity (`A = D - L`), without
    materialising A_p. Useful as an illustrative cross-check that the
    eigendecomposition reconstruction matches the dense lookup.

    For a clean reach edge, the score is exactly 1.0 (within
    float). For a non-edge, the score is exactly 0.0 (within
    float). Reading values close to 0.5 / spurious values would
    indicate a numerical bug in the eigendecomposition.

    This is the "spectral" oracle path -- :func:`is_reachable` is
    the equivalent fast-path lookup.
    """
    if not 0 <= from_sq < BOARD_DIM:
        raise ValueError(f"from_sq {from_sq} out of range [0, 64)")
    if not 0 <= to_sq < BOARD_DIM:
        raise ValueError(f"to_sq {to_sq} out of range [0, 64)")
    eigvals, eigvecs = piece_eigendecomposition(piece)
    # A = D - L. D is diagonal with degree on the diagonal; A_p has
    # zero diagonal (no self-loops in piece-reach graphs), so:
    #   i == j: A[i, i] = D[i, i] - L[i, i] = 0 by construction.
    #   i != j: A[i, j] = -L[i, j] = -sum_k λ_k v_k[i] v_k[j].
    if from_sq == to_sq:
        return 0.0
    L_ij = float(np.sum(eigvals * eigvecs[from_sq] * eigvecs[to_sq]))
    return float(-L_ij)


def agrees_with_phase_operators(piece: str) -> bool:
    """Cross-validate against
    :mod:`chess_spectral.phase_operators.occupation_aware_moves_c`
    on **every** (from_sq, color) pair for the given piece.

    Both oracles answer "what are the empty-board reach targets"
    when the position dict is empty. Disagreement is a hard bug
    in either oracle.

    Returns True if all 64 from-squares produce identical reach sets
    on both oracles. Raises AssertionError on the first mismatch
    (the AssertionError carries the offending square so debugging
    has a starting point).

    Tested on every piece via :mod:`tests.test_spectral_legality`.
    """
    # Lazy import: phase_operators depends on python-chess at import
    # time, but we don't need it to define the oracle module's API.
    import chess
    from .phase_operators import occupation_aware_moves_c

    board_empty = chess.Board.empty()
    for from_sq_chess in range(64):
        # Convert python-chess square → spectral square.
        rank = chess.square_rank(from_sq_chess)
        file = chess.square_file(from_sq_chess)
        spectral_sq = (7 - rank) * 8 + file

        # Spectral oracle: reach set in spectral indexing.
        spectral_reach = set(reachable_targets(piece, spectral_sq))

        # phase_operators uses (row, col) addressing on python-chess
        # board. We re-express in spectral indices for comparison.
        # occupation_aware_moves_c signature:
        #   (board, piece_char, row, col, color_sign) -> frozenset of
        #   (row, col) tuples.
        # color_sign: +1 for white, -1 for black; on an empty board
        # both colors give the same reach for non-pawns, so we pick +1.
        po_reach_rc = occupation_aware_moves_c(
            board_empty, piece, rank, file, +1
        )
        # Convert (row, col) -> spectral square.
        po_reach_spectral = {
            (7 - r) * 8 + c for (r, c) in po_reach_rc
        }

        if spectral_reach != po_reach_spectral:
            sym_diff = spectral_reach.symmetric_difference(po_reach_spectral)
            raise AssertionError(
                f"oracle disagreement for piece {piece!r} from "
                f"spectral_sq={spectral_sq} (rank={rank}, file={file}):\n"
                f"  spectral oracle: {sorted(spectral_reach)}\n"
                f"  phase_operators: {sorted(po_reach_spectral)}\n"
                f"  symmetric diff:  {sorted(sym_diff)}"
            )
    return True


# ---- Module-level info ---------------------------------------------


def supported_pieces() -> List[str]:
    """The set of pieces this oracle covers ('N', 'B', 'R', 'Q', 'K').

    Pawns are excluded (directed reach -- see module docstring for
    the deferral pointer).
    """
    return sorted(_HERMITIAN_PIECES)


__all__ = [
    "is_reachable",
    "reachable_targets",
    "spectral_reach_score",
    "agrees_with_phase_operators",
    "piece_eigendecomposition",
    "supported_pieces",
]
