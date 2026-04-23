"""Dynamic sheaf Laplacian — Phase 2 minimal instantiation.

Section 10.7 of the chess notebook frames Othello's state-dependent
flank structure as a cellular sheaf with evolving restriction maps.
Hansen-Ghrist 2019 define the degree-0 sheaf Laplacian on a cell
complex (X, F) as

    (L_F x)_v = sum_{v lhd e} F_{v lhd e}^T * (F_{v lhd e} x_v
                                              - F_{w lhd e} x_w)

which reduces to the graph Laplacian when stalks are ``R`` and
restriction maps are identity.

Minimal viable sheaf used here
------------------------------
- Vertex stalks F(v) = R^3 carrying the 3-state Blume-Capel fiber
  (one-hot (empty, black, white)).
- Edge set: for each directed ray segment (v, w) with w = v + d and
  both in bounds, we admit an edge iff the flank structure gates it
  (see restriction maps below).  Edges are symmetrised.
- Edge stalk F(e) = R^3.  Restriction map F_{v lhd e} depends on
  the cell state at v:

  * v is empty: projector onto the empty-state coordinate
    (the cell cannot originate a flank).
  * v holds a friendly disc (matches the "owner" we index by):
    identity — the ray originates here at full strength.
  * v holds an opponent disc: middle-of-ray projector
    (partial weight 1/2), modelling a bracket-in-progress.

  (This is a deliberately crude surrogate.  A more faithful
  construction would make restrictions depend on the SEGMENT's
  bracket validity, not just the endpoint.  The qualitative
  behaviour of the spectrum should survive refinement.)

What we observe at each move
----------------------------
- Spectral gap lambda_2 (algebraic connectivity of the sheaf
  Laplacian).
- Spectral entropy  H = -sum p_i log p_i  over normalised
  eigenvalues.
- Kernel dimension |{lambda_i < 1e-9}|.
- Disc density rho and number of legal moves (context variables).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from othello_utils import (
    BOARD_SIZE,
    N,
    OthelloBoard,
    RAY_OFFSETS,
    idx_to_rc,
    rc_to_idx,
    in_bounds,
    EMPTY,
    BLACK,
    WHITE,
)


# Stalk dimension for vertex and edge stalks.
STALK_DIM = 3


def _onehot(state_val: int) -> np.ndarray:
    """Map cell state in {-1, 0, +1} to one-hot in R^3 with order
    (empty, black, white)."""
    v = np.zeros(STALK_DIM)
    if state_val == EMPTY:
        v[0] = 1.0
    elif state_val == BLACK:
        v[1] = 1.0
    elif state_val == WHITE:
        v[2] = 1.0
    return v


def _restriction_map(state_val: int, owner: int) -> np.ndarray:
    """Return the 3x3 restriction map F_{v lhd e}.

    ``owner`` in {BLACK, WHITE} selects the player whose influence
    we are encoding along this edge.  The map returns a projector
    whose weight depends on whether v is empty / friendly / enemy.
    """
    if state_val == EMPTY:
        # Empty cell projects only onto the 'empty' component.
        P = np.zeros((STALK_DIM, STALK_DIM))
        P[0, 0] = 1.0
        return P
    if state_val == owner:
        # Friendly disc: identity on the friendly component.
        P = np.zeros((STALK_DIM, STALK_DIM))
        idx = 1 if owner == BLACK else 2
        P[idx, idx] = 1.0
        return P
    # Opponent disc — mid-flank: half weight on opponent component.
    P = np.zeros((STALK_DIM, STALK_DIM))
    idx = 1 if (-owner) == BLACK else 2
    P[idx, idx] = 0.5
    return P


def sheaf_laplacian(state: np.ndarray, owner: int = BLACK) -> np.ndarray:
    """Construct the minimal Othello sheaf Laplacian at the given
    board state (length-64 int array in {-1, 0, +1}).

    Returns an (N*STALK_DIM, N*STALK_DIM) symmetric PSD matrix.
    """
    M = N * STALK_DIM
    L = np.zeros((M, M))
    seen_edges: set[tuple[int, int]] = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = rc_to_idx(r, c)
            for d_name, (dr, dc) in RAY_OFFSETS.items():
                rr, cc = r + dr, c + dc
                if not in_bounds(rr, cc):
                    continue
                w = rc_to_idx(rr, cc)
                key = (min(v, w), max(v, w))
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                Fv = _restriction_map(int(state[v]), owner)
                Fw = _restriction_map(int(state[w]), owner)
                # block contributions
                vv_block = Fv.T @ Fv
                ww_block = Fw.T @ Fw
                vw_block = -(Fv.T @ Fw)
                wv_block = vw_block.T
                vi = v * STALK_DIM
                wi = w * STALK_DIM
                L[vi:vi + STALK_DIM, vi:vi + STALK_DIM] += vv_block
                L[wi:wi + STALK_DIM, wi:wi + STALK_DIM] += ww_block
                L[vi:vi + STALK_DIM, wi:wi + STALK_DIM] += vw_block
                L[wi:wi + STALK_DIM, vi:vi + STALK_DIM] += wv_block
    return L


def spectrum_summary(L: np.ndarray) -> dict:
    w = np.linalg.eigvalsh((L + L.T) / 2)
    w = np.clip(w, 0.0, None)
    kernel_dim = int(np.sum(w < 1e-9))
    # Second smallest eigenvalue (after kernel)
    nonzero = w[w >= 1e-9]
    lambda_2 = float(nonzero[0]) if nonzero.size else 0.0
    lambda_max = float(w.max())
    # Spectral entropy on the normalised spectrum
    total = float(w.sum())
    p = (w / total) if total > 0 else w
    mask = p > 1e-15
    ent = float(-np.sum(p[mask] * np.log(p[mask])))
    return {
        "lambda_2": lambda_2,
        "lambda_max": lambda_max,
        "kernel_dim": kernel_dim,
        "entropy": ent,
        "total_mass": total,
    }


def sample_game_trajectory(seed: int = 123) -> list[dict]:
    rng = np.random.default_rng(seed)
    bb = OthelloBoard()
    out: list[dict] = []
    # Record pre-move spectrum at each step.
    while not bb.is_terminal():
        move_no = len(bb.move_history)
        L = sheaf_laplacian(bb.state, owner=BLACK)
        spec_b = spectrum_summary(L)
        L_w = sheaf_laplacian(bb.state, owner=WHITE)
        spec_w = spectrum_summary(L_w)
        b, w, e = bb.disc_counts()
        lm = bb.legal_moves()
        out.append(
            {
                "move_no": move_no,
                "side_to_move": int(bb.side_to_move),
                "rho": (b + w) / 64.0,
                "black_count": b,
                "white_count": w,
                "empty_count": e,
                "n_legal_moves": len(lm),
                "sheaf_black_lambda2": spec_b["lambda_2"],
                "sheaf_black_lambdamax": spec_b["lambda_max"],
                "sheaf_black_kerdim": spec_b["kernel_dim"],
                "sheaf_black_entropy": spec_b["entropy"],
                "sheaf_white_lambda2": spec_w["lambda_2"],
                "sheaf_white_lambdamax": spec_w["lambda_max"],
                "sheaf_white_kerdim": spec_w["kernel_dim"],
                "sheaf_white_entropy": spec_w["entropy"],
            }
        )
        if lm:
            bb.play(int(rng.choice(lm)))
        else:
            bb.play(None)
    return out


def main() -> None:
    traj = sample_game_trajectory()
    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "phase2_sheaf_trajectory.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(traj, f, indent=2)

    # Summary for human consumption
    rho = np.array([t["rho"] for t in traj])
    lam2_b = np.array([t["sheaf_black_lambda2"] for t in traj])
    ent_b = np.array([t["sheaf_black_entropy"] for t in traj])
    kdim_b = np.array([t["sheaf_black_kerdim"] for t in traj])
    legals = np.array([t["n_legal_moves"] for t in traj])
    print(f"trajectory length: {len(traj)} moves")
    print(f"rho: min={rho.min():.3f}, max={rho.max():.3f}")
    print(
        f"sheaf_black lambda_2: min={lam2_b.min():.3f}, "
        f"max={lam2_b.max():.3f}, mean={lam2_b.mean():.3f}"
    )
    print(
        f"sheaf_black entropy: min={ent_b.min():.3f}, "
        f"max={ent_b.max():.3f}"
    )
    print(
        f"sheaf_black kernel dim: min={int(kdim_b.min())}, "
        f"max={int(kdim_b.max())}"
    )
    print(f"legal-move count: min={legals.min()}, max={legals.max()}")
    # Correlations
    from scipy.stats import spearmanr

    sp_rho_lam2 = spearmanr(rho, lam2_b)
    sp_lm_lam2 = spearmanr(legals, lam2_b)
    print(
        f"Spearman(rho, lambda_2) = {sp_rho_lam2.statistic:+.3f} "
        f"(p={sp_rho_lam2.pvalue:.1e})"
    )
    print(
        f"Spearman(legal_moves, lambda_2) = {sp_lm_lam2.statistic:+.3f} "
        f"(p={sp_lm_lam2.pvalue:.1e})"
    )
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
