"""Faithful sheaf Laplacian — bracket-aware restriction maps.

Addresses §3.1 caveat of the notebook:

    (The current dynamic_sheaf.py restrictions depend only on cell-
    endpoint state — empty/friendly/opponent.  A more faithful
    construction would make restrictions depend on the SEGMENT's
    bracket validity, not just the endpoint.)

Design
------

An Othello *flank bracket* from cell ``v`` in direction ``d`` (one of
the 8 compass offsets) is the 3-part structure

    s(v) = c                     (friendly endpoint,  c in {+1, -1})
    s(v + k*d) = -c for k = 1..r (opponent run of length r >= 1)
    s(v + (r+1)*d) = c           (closing friendly disc)

with no empty cell in positions 1..r+1.  If instead the closing
position is empty or out of bounds, the (v, d) segment does NOT carry
a valid bracket — and by Othello's rules, a DIFFERENT friendly disc
placed at v + (r+1)*d would flip the opponent run and realise the
bracket.  So we also admit "pending brackets" as edges that carry
lower-weight restrictions.

Faithful edge set
-----------------

For each (v, d) with v non-empty:

    classify the ray from v+d:
        R1_NONE         : ray is empty or starts with friendly (no bracket)
        R2_COMPLETE     : valid opp run + friendly close
                           (this segment's discs would flip if the
                            friendly endpoint relocated, but already
                            stable)
        R3_PENDING      : valid opp run + empty at v + (r+1)*d
                           (flippable: a friendly placement at that
                            empty square would flip the run)
        R4_OPEN         : opp run runs to the boundary with no close
                           (no bracket, no pending flip)

Edges are added between v and every cell in the opp run for R2 and
R3 classes.  Restriction maps are:

    F_{v <- e}  = identity on the friendly component             (v is the origin)
    F_{w <- e}  = projector onto the OPPONENT component scaled
                   by alpha(class) in (0, 1]
                   - alpha = 1.0 for R3_PENDING (flippable now)
                   - alpha = 0.5 for R2_COMPLETE (stable flank)

R1 and R4 contribute no edges — faithful in the sense that the
sheaf captures only currently-active flanking structure.

This is still a minimal implementation (no edge stalks larger than
R^3, no cross-ray coupling beyond shared cell vertices).  It is
strictly more informative than the endpoint-only crude version, and
its spectrum should differ in observable ways — the smoke test
verifies that the rank and lambda_2 diverge from the crude sheaf on
non-trivial positions.
"""

from __future__ import annotations

__version__ = "0.2.0"  # paired with othello_spectral v0.2.0

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from othello_utils import (
    BLACK, BOARD_SIZE, EMPTY, N, OthelloBoard, RAY_OFFSETS, WHITE,
    in_bounds, rc_to_idx, idx_to_rc,
)


STALK_DIM = 3  # (empty, black, white) one-hot

# Bracket classes (see module docstring).
R1_NONE, R2_COMPLETE, R3_PENDING, R4_OPEN = 0, 1, 2, 3

_ALPHA_COMPLETE = 0.5   # existing flank, stable
_ALPHA_PENDING = 1.0    # flippable now, full weight


def classify_ray(
    state: np.ndarray, v_idx: int, dr: int, dc: int,
) -> tuple[int, list[int]]:
    """Classify the ray starting at v_idx+1*(dr,dc) for bracket
    structure originating at v_idx.  Returns (class, opp_cells)
    where opp_cells is the list of intermediate indices holding
    opponent discs (empty for R1/R4)."""
    v_r, v_c = idx_to_rc(v_idx)
    v_val = int(state[v_idx])
    if v_val == EMPTY:
        return R1_NONE, []
    # Walk the ray
    opp_cells: list[int] = []
    r, c = v_r + dr, v_c + dc
    while in_bounds(r, c):
        w_idx = rc_to_idx(r, c)
        w_val = int(state[w_idx])
        if w_val == EMPTY:
            # opp run + empty => pending
            if opp_cells:
                return R3_PENDING, opp_cells
            return R1_NONE, []
        if w_val == v_val:
            # opp run + friendly close => complete
            if opp_cells:
                return R2_COMPLETE, opp_cells
            return R1_NONE, []
        # w is opposite: add to run, continue
        opp_cells.append(w_idx)
        r += dr
        c += dc
    # Ran off the board with (possibly) an opp run => open
    return R4_OPEN, opp_cells


def faithful_edges(state: np.ndarray) -> list[tuple[int, int, int]]:
    """Enumerate (v, w, alpha_class) edges from the full bracket
    scan.  Each edge appears once per (v, d, w) triple — no
    symmetrisation; the sheaf Laplacian builder handles the
    symmetric combination explicitly."""
    edges: list[tuple[int, int, int]] = []
    for v in range(N):
        if int(state[v]) == EMPTY:
            continue
        for dr, dc in RAY_OFFSETS.values():
            cls, opp = classify_ray(state, v, dr, dc)
            if cls == R1_NONE or cls == R4_OPEN:
                continue
            for w in opp:
                edges.append((v, w, cls))
    return edges


def _onehot(v: int) -> np.ndarray:
    o = np.zeros(STALK_DIM, dtype=np.float64)
    if v == EMPTY:
        o[0] = 1.0
    elif v == BLACK:
        o[1] = 1.0
    elif v == WHITE:
        o[2] = 1.0
    return o


def _restriction_v_friendly(owner_player: int) -> np.ndarray:
    """At the bracket origin v we are a friendly disc; project onto
    that player's stalk component."""
    P = np.zeros((STALK_DIM, STALK_DIM), dtype=np.float64)
    idx = 1 if owner_player == BLACK else 2
    P[idx, idx] = 1.0
    return P


def _restriction_w_opponent(owner_player: int, alpha: float) -> np.ndarray:
    """At an opponent cell inside the run, project onto the opponent
    component with weight alpha."""
    P = np.zeros((STALK_DIM, STALK_DIM), dtype=np.float64)
    opp = -owner_player
    idx = 1 if opp == BLACK else 2
    P[idx, idx] = alpha
    return P


def faithful_sheaf_laplacian(
    state: np.ndarray, owner: int = BLACK,
) -> np.ndarray:
    """Build the degree-0 sheaf Laplacian with faithful bracket-
    aware restrictions, from the viewpoint of ``owner`` player.

    Edges are brackets originating at friendly discs of either
    colour (we include both BLACK-originated and WHITE-originated
    brackets to preserve the full flank structure — but only those
    that carry the ``owner``'s potential-flip content contribute
    non-trivially under the owner-indexed restriction maps).
    """
    M = N * STALK_DIM
    L = np.zeros((M, M), dtype=np.float64)

    edges = faithful_edges(state)
    for v, w, cls in edges:
        alpha = _ALPHA_PENDING if cls == R3_PENDING else _ALPHA_COMPLETE
        # Only brackets originating from the owner's discs contribute
        # to the owner's sheaf.  Skip brackets originating from the
        # opponent (they belong to the opponent's sheaf).
        if int(state[v]) != owner:
            continue
        Fv = _restriction_v_friendly(owner)
        Fw = _restriction_w_opponent(owner, alpha)
        vv = v * STALK_DIM
        ww = w * STALK_DIM
        vv_block = Fv.T @ Fv
        ww_block = Fw.T @ Fw
        vw_block = -(Fv.T @ Fw)
        wv_block = vw_block.T
        L[vv:vv + STALK_DIM, vv:vv + STALK_DIM] += vv_block
        L[ww:ww + STALK_DIM, ww:ww + STALK_DIM] += ww_block
        L[vv:vv + STALK_DIM, ww:ww + STALK_DIM] += vw_block
        L[ww:ww + STALK_DIM, vv:vv + STALK_DIM] += wv_block
    return L


def spectrum_summary(L: np.ndarray) -> dict:
    w = np.linalg.eigvalsh((L + L.T) / 2)
    w = np.clip(w, 0.0, None)
    kernel_dim = int(np.sum(w < 1e-9))
    nonzero = w[w >= 1e-9]
    lambda_2 = float(nonzero[0]) if nonzero.size else 0.0
    lambda_max = float(w.max())
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


def bracket_summary(state: np.ndarray) -> dict:
    """For diagnostics: tally bracket classes per ray-origin pair."""
    counts = {"R1_NONE": 0, "R2_COMPLETE": 0, "R3_PENDING": 0, "R4_OPEN": 0}
    for v in range(N):
        if int(state[v]) == EMPTY:
            continue
        for dr, dc in RAY_OFFSETS.values():
            cls, _ = classify_ray(state, v, dr, dc)
            if cls == R1_NONE:
                counts["R1_NONE"] += 1
            elif cls == R2_COMPLETE:
                counts["R2_COMPLETE"] += 1
            elif cls == R3_PENDING:
                counts["R3_PENDING"] += 1
            else:
                counts["R4_OPEN"] += 1
    return counts


def compare_to_crude(state: np.ndarray, owner: int = BLACK) -> dict:
    """Compare faithful vs crude sheaf spectrum on one state.

    The crude version lives in ``dynamic_sheaf``; this function
    imports it lazily so ``faithful_sheaf`` stays standalone.
    """
    from dynamic_sheaf import sheaf_laplacian as crude_sheaf
    crude = crude_sheaf(state, owner=owner)
    faithful = faithful_sheaf_laplacian(state, owner=owner)
    return {
        "owner": "BLACK" if owner == BLACK else "WHITE",
        "bracket_counts": bracket_summary(state),
        "crude":    spectrum_summary(crude),
        "faithful": spectrum_summary(faithful),
        "diff": {
            "delta_lambda_2":
                spectrum_summary(faithful)["lambda_2"]
                - spectrum_summary(crude)["lambda_2"],
            "delta_kernel_dim":
                spectrum_summary(faithful)["kernel_dim"]
                - spectrum_summary(crude)["kernel_dim"],
        },
    }


def sample_trajectory(seed: int = 123, owner: int = BLACK) -> list[dict]:
    """Record per-ply crude+faithful sheaf spectra along a random-play
    trajectory.  Mirrors dynamic_sheaf.sample_game_trajectory but
    adds the bracket-count diagnostics."""
    rng = np.random.default_rng(seed)
    bb = OthelloBoard()
    out: list[dict] = []
    while not bb.is_terminal():
        move_no = len(bb.move_history)
        cmp = compare_to_crude(bb.state, owner=owner)
        b, w, e = bb.disc_counts()
        lm = bb.legal_moves()
        out.append({
            "move_no": move_no,
            "side_to_move": int(bb.side_to_move),
            "rho": (b + w) / 64.0,
            "n_legal_moves": len(lm),
            "bracket_counts": cmp["bracket_counts"],
            "crude_lambda2":    cmp["crude"]["lambda_2"],
            "faithful_lambda2": cmp["faithful"]["lambda_2"],
            "crude_kerdim":     cmp["crude"]["kernel_dim"],
            "faithful_kerdim":  cmp["faithful"]["kernel_dim"],
            "delta_lambda2": cmp["diff"]["delta_lambda_2"],
            "delta_kerdim":  cmp["diff"]["delta_kernel_dim"],
        })
        bb.play(int(rng.choice(lm)) if lm else None)
    return out


def _build_parser():
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase2_faithful_sheaf_trajectory.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # One random-play trajectory, seed 123, write
  # ../results/phase2_faithful_sheaf_trajectory.json.
  python research/faithful_sheaf.py

  # Custom seed and output.
  python research/faithful_sheaf.py --seed 42 --out /tmp/out.json

notes:
  The faithful sheaf Laplacian differs from the crude dynamic_sheaf
  in two ways:
    - Only friendly-originated brackets (R2, R3 classes) contribute
      edges; crude sheaf adds edges at every ray-adjacent pair.
    - Restriction maps are projectors onto bracket-relevant stalk
      components with alpha weights tied to bracket status
      (R3_PENDING alpha=1.0, R2_COMPLETE alpha=0.5).

  Predicts the kernel dim should drop below crude's 128 on
  positions with active flanks; §3.4 notebook caveat.
""",
    )
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument(
        "--owner", choices=["black", "white"], default="black",
        help="Sheaf owner (for viewpoint-specific bracket counting).",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    owner = BLACK if args.owner == "black" else WHITE
    traj = sample_trajectory(seed=args.seed, owner=owner)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(traj, f, indent=2)
    # Summary
    print(f"trajectory length: {len(traj)} moves")
    crude_l2 = np.array([t["crude_lambda2"] for t in traj])
    faithful_l2 = np.array([t["faithful_lambda2"] for t in traj])
    crude_k = np.array([t["crude_kerdim"] for t in traj])
    faithful_k = np.array([t["faithful_kerdim"] for t in traj])
    print(f"crude    lambda_2  min {crude_l2.min():.3f}  max {crude_l2.max():.3f}  mean {crude_l2.mean():.3f}")
    print(f"faithful lambda_2  min {faithful_l2.min():.3f}  max {faithful_l2.max():.3f}  mean {faithful_l2.mean():.3f}")
    print(f"crude    kernel    {int(crude_k.min())} .. {int(crude_k.max())} (mean {crude_k.mean():.1f})")
    print(f"faithful kernel    {int(faithful_k.min())} .. {int(faithful_k.max())} (mean {faithful_k.mean():.1f})")
    delta_l2 = np.array([t["delta_lambda2"] for t in traj])
    print(f"delta lambda_2 (faithful - crude)  mean {delta_l2.mean():+.3f}  abs_mean {np.abs(delta_l2).mean():.3f}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
