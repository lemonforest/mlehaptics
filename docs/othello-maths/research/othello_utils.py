"""Othello shared utilities.

Single source of truth for:
- Board dimensions and index conversions (``rc_to_idx``, ``idx_to_rc``).
- 8x8 grid Laplacian (``grid_laplacian_8x8``) — sanity checked against the
  2D DCT basis in Phase 0 (see ``sanity_grid_dct``).
- The 8 ray directions (``ray_offsets``, ``RAY_NAMES``).
- Board signal encoders:
    * ``blume_capel_signal`` — world-frame {-1,0,+1} spin-1 field.
    * ``mine_yours_empty_signal`` — player-relative 3-channel encoding
      (Nanda-Lee-Wattenberg 2023 / Othello-GPT representation).
- A minimal pure-Python Othello board class (``OthelloBoard``) — 80 lines
  target; enough for move generation, flank counting, and game replay.

All downstream scripts import from here — do not duplicate any of this
construction elsewhere.
"""

from __future__ import annotations

import numpy as np
from typing import Iterable, Iterator

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

BOARD_SIZE: int = 8
N: int = BOARD_SIZE * BOARD_SIZE  # 64

# Site fiber states (Blume-Capel spin-1)
EMPTY: int = 0
BLACK: int = 1   # +1 in Blume-Capel; "X" in WTHOR notation
WHITE: int = -1  # -1 in Blume-Capel; "O"

# ---------------------------------------------------------------------------
# Index conversions
# ---------------------------------------------------------------------------


def rc_to_idx(r: int, c: int) -> int:
    return r * BOARD_SIZE + c


def idx_to_rc(i: int) -> tuple[int, int]:
    return divmod(i, BOARD_SIZE)


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


# ---------------------------------------------------------------------------
# Grid Laplacian
# ---------------------------------------------------------------------------


def grid_laplacian_8x8() -> np.ndarray:
    """P_8 box P_8 graph Laplacian on 64 vertices.

    Identical construction to chess §2.  Eigenvectors are the 2D DCT
    basis to machine precision (sanity-checked in ``sanity_grid_dct``).
    """
    L = np.zeros((N, N), dtype=float)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            i = rc_to_idx(r, c)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc):
                    j = rc_to_idx(rr, cc)
                    L[i, j] = -1.0
                    L[i, i] += 1.0
    return L


def dct_basis_2d() -> np.ndarray:
    """Return the 64-column orthonormal 2D DCT-II basis used to verify
    the grid Laplacian spectrum.  Column index = a*8+b for (a,b) mode."""
    # 1D DCT-II of length 8 on the [0,7] grid (Neumann BCs: phi_k(n)
    # proportional to cos(pi k (n+1/2)/8)).  Both 1D bases diagonalise
    # P_8, so their Kronecker product diagonalises P_8 box P_8.
    n = BOARD_SIZE
    idx = np.arange(n)
    phi = np.zeros((n, n))
    for k in range(n):
        alpha = np.sqrt(1.0 / n) if k == 0 else np.sqrt(2.0 / n)
        phi[:, k] = alpha * np.cos(np.pi * k * (idx + 0.5) / n)
    # Tensor product: column index = a*n + b; basis[r*n+c, a*n+b] =
    # phi[r,a] * phi[c,b].
    basis = np.zeros((N, N))
    for a in range(n):
        for b in range(n):
            col = a * n + b
            outer = np.outer(phi[:, a], phi[:, b])
            basis[:, col] = outer.reshape(N)
    return basis


def sanity_grid_dct(tol: float = 1e-10) -> dict:
    """H1 sanity: eigenvectors of L_grid match 2D DCT basis to
    machine precision.  Returns diagnostic dict (max |cos| after
    alignment, eigenvalue residual)."""
    L = grid_laplacian_8x8()
    vals, vecs = np.linalg.eigh(L)
    dct = dct_basis_2d()
    # Sort DCT columns by their Laplacian quadratic form to match
    # eigenvalue ordering.
    dct_eigs = np.array([v @ L @ v for v in dct.T])
    order = np.argsort(dct_eigs)
    dct_sorted = dct[:, order]
    dct_eigs_sorted = dct_eigs[order]
    # Degenerate subspaces: within blocks of equal eigenvalue, compare
    # *subspace* overlap rather than individual vectors.
    max_subspace_gap = 0.0
    i = 0
    while i < N:
        j = i
        while j < N and abs(vals[j] - vals[i]) < 1e-9:
            j += 1
        Vblock = vecs[:, i:j]
        Dblock = dct_sorted[:, i:j]
        # Orthogonal projection distance: ||V V^T - D D^T||
        gap = np.linalg.norm(Vblock @ Vblock.T - Dblock @ Dblock.T)
        max_subspace_gap = max(max_subspace_gap, gap)
        i = j
    eig_residual = float(np.max(np.abs(vals - dct_eigs_sorted)))
    return {
        "max_subspace_gap": float(max_subspace_gap),
        "eig_residual": eig_residual,
        "pass": max_subspace_gap < tol and eig_residual < tol,
    }


# ---------------------------------------------------------------------------
# Rays
# ---------------------------------------------------------------------------

RAY_NAMES: tuple[str, ...] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
RAY_OFFSETS: dict[str, tuple[int, int]] = {
    "N": (-1, 0),
    "NE": (-1, 1),
    "E": (0, 1),
    "SE": (1, 1),
    "S": (1, 0),
    "SW": (1, -1),
    "W": (0, -1),
    "NW": (-1, -1),
}
# D4 orbit partition: orthogonal {N,E,S,W} and diagonal {NE,SE,SW,NW}.
ORTHO_RAYS: tuple[str, ...] = ("N", "E", "S", "W")
DIAG_RAYS: tuple[str, ...] = ("NE", "SE", "SW", "NW")


def ray_offsets() -> dict[str, tuple[int, int]]:
    return dict(RAY_OFFSETS)


# ---------------------------------------------------------------------------
# Board signal encoders
# ---------------------------------------------------------------------------


def blume_capel_signal(board_state: np.ndarray) -> np.ndarray:
    """World-frame Blume-Capel signal.

    ``board_state`` is a length-64 array with values in {-1, 0, +1}
    (or the 2D 8x8 form).  Returns the same 64-vector as float.
    """
    arr = np.asarray(board_state, dtype=float).reshape(-1)
    assert arr.shape == (N,), f"expected {N}-vector, got {arr.shape}"
    return arr.copy()


def mine_yours_empty_signal(
    board_state: np.ndarray, side_to_move: int
) -> np.ndarray:
    """Player-relative signal a la Nanda-Lee-Wattenberg (2023).

    Returns a 64x3 array; columns are [mine, yours, empty] as one-hot
    indicators in the player-relative frame.  ``side_to_move`` is +1
    for black or -1 for white.
    """
    arr = np.asarray(board_state, dtype=int).reshape(N)
    assert side_to_move in (BLACK, WHITE)
    mine = (arr == side_to_move).astype(float)
    yours = (arr == -side_to_move).astype(float)
    empty = (arr == EMPTY).astype(float)
    return np.stack([mine, yours, empty], axis=1)


# ---------------------------------------------------------------------------
# Othello board
# ---------------------------------------------------------------------------


class OthelloBoard:
    """Minimal pure-Python Othello implementation.

    Design goals: correctness, inspectability, easy iteration over game
    histories.  NOT optimised for speed.  Board state is a length-64
    numpy array in {-1, 0, +1}.
    """

    def __init__(self) -> None:
        self.state = np.zeros(N, dtype=int)
        # Standard starting position — two pairs of diagonally-opposed
        # central discs.  d4, e5 = white; d5, e4 = black (WTHOR convention).
        self.state[rc_to_idx(3, 3)] = WHITE
        self.state[rc_to_idx(4, 4)] = WHITE
        self.state[rc_to_idx(3, 4)] = BLACK
        self.state[rc_to_idx(4, 3)] = BLACK
        self.side_to_move: int = BLACK  # Black plays first in Othello.
        self.pass_count: int = 0  # consecutive passes
        self.move_history: list[int | None] = []  # idx or None for pass

    def copy(self) -> "OthelloBoard":
        b = OthelloBoard.__new__(OthelloBoard)
        b.state = self.state.copy()
        b.side_to_move = self.side_to_move
        b.pass_count = self.pass_count
        b.move_history = list(self.move_history)
        return b

    # ---- core rules ----

    def flips_from(self, r: int, c: int, player: int) -> list[int]:
        """Return list of disc indices that would flip if ``player``
        placed at (r, c).  Empty list => illegal placement."""
        if not in_bounds(r, c) or self.state[rc_to_idx(r, c)] != EMPTY:
            return []
        flips: list[int] = []
        opp = -player
        for dr, dc in RAY_OFFSETS.values():
            ray_flips: list[int] = []
            rr, cc = r + dr, c + dc
            while in_bounds(rr, cc) and self.state[rc_to_idx(rr, cc)] == opp:
                ray_flips.append(rc_to_idx(rr, cc))
                rr += dr
                cc += dc
            if (
                ray_flips
                and in_bounds(rr, cc)
                and self.state[rc_to_idx(rr, cc)] == player
            ):
                flips.extend(ray_flips)
        return flips

    def legal_moves(self, player: int | None = None) -> list[int]:
        """Indices of all legal placements for ``player`` (default:
        current side to move)."""
        p = self.side_to_move if player is None else player
        out: list[int] = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.flips_from(r, c, p):
                    out.append(rc_to_idx(r, c))
        return out

    def play(self, idx: int | None) -> None:
        """Play a move (index 0..63) or a pass (None).  Raises
        ValueError if the move is illegal or if a pass was played
        while legal moves exist."""
        if idx is None:
            if self.legal_moves():
                raise ValueError("illegal pass: legal moves exist")
            self.side_to_move = -self.side_to_move
            self.pass_count += 1
            self.move_history.append(None)
            return
        r, c = idx_to_rc(idx)
        flips = self.flips_from(r, c, self.side_to_move)
        if not flips:
            raise ValueError(f"illegal move at ({r},{c})")
        self.state[idx] = self.side_to_move
        for f in flips:
            self.state[f] = self.side_to_move
        self.side_to_move = -self.side_to_move
        self.pass_count = 0
        self.move_history.append(idx)

    def is_terminal(self) -> bool:
        """Game ends when neither side has a legal move."""
        if self.legal_moves(BLACK) or self.legal_moves(WHITE):
            return False
        return True

    def disc_counts(self) -> tuple[int, int, int]:
        """Return (black, white, empty) counts."""
        b = int(np.sum(self.state == BLACK))
        w = int(np.sum(self.state == WHITE))
        e = int(np.sum(self.state == EMPTY))
        return b, w, e


# ---------------------------------------------------------------------------
# Smoke tests for the board class
# ---------------------------------------------------------------------------


def _sanity_othello_board() -> dict:
    b = OthelloBoard()
    counts = b.disc_counts()
    start_moves = b.legal_moves()
    # After any one legal opening move the responder has 3 replies in
    # standard Othello (all four first moves are strategically
    # symmetric — the opponent has exactly three counters).
    b2 = b.copy()
    first_idx = start_moves[0]
    b2.play(first_idx)
    reply_moves = b2.legal_moves()
    return {
        "start_counts": counts,
        "n_start_moves": len(start_moves),
        "n_reply_moves_after_first": len(reply_moves),
    }


if __name__ == "__main__":
    print("=== othello_utils sanity ===")
    r = sanity_grid_dct()
    print(
        f"H1 grid Laplacian vs 2D DCT: max subspace gap = "
        f"{r['max_subspace_gap']:.3e}, eig residual = "
        f"{r['eig_residual']:.3e}, PASS = {r['pass']}"
    )
    s = _sanity_othello_board()
    print(f"OthelloBoard start disc counts: {s['start_counts']}")
    print(f"OthelloBoard start legal moves: {s['n_start_moves']}")
    print(
        f"OthelloBoard legal replies after opening: "
        f"{s['n_reply_moves_after_first']}"
    )
