"""Phase 3.5 probe — ADR-001 phase-distinguishability test.

Hypothesis: ADR-001's per-channel phase formula (Option D — phases
derived from the channel's B_4 irrep label) produces *distinguishable*
quantum states for distinct chess moves. If the formula collapses to
trivial phases for too many moves, the Aaronson escape valve closes
and the QM mapping becomes a notational restatement of classical
permutations.

Acceptance criterion: for at least 80% of pairs (move_A, move_B) with
distinct from->to coordinates on the same starting position,
|<psi_after_A | psi_after_B>| < 0.99 (i.e., the resulting states are
at least 1% distinguishable in inner product).

Method
------
1. Sample ~50 starting positions via the seeded random walker
   (matches tests/test_smoke_e2e.py::_seeded_self_play_4d).
2. For each starting position, enumerate up to ~20 distinct legal
   moves of the piece-set on the board (using tables_4d.*_targets
   generators; pawnless corpus, matching the seeded walker).
3. For each pair (move_A, move_B) on the same starting state,
   synthesise the post-move ψ_A and ψ_B as follows:
     - Encode the post-move position classically via encode_4d.
     - Multiply each channel block by the ADR-001 phase factor
       e^(i * theta_c(o, d, t)) where theta_c is per ADR-001 §3.1.
     - Renormalize.
   Track A's `state_to_psi` is used as the underlying encoder; the
   sign factor for side-to-move is *not* applied here because we are
   probing phase distinguishability between two moves on the SAME
   starting state (the side-to-move flips identically in both cases).
4. Compute |<psi_A | psi_B>| for each pair. Histogram & percentiles.

Output: research/track_b_phase_distinguishability_results.json, plus a
1-paragraph findings note printed at the end of __main__.

Scope
-----
This probe does NOT build a full U_move; it builds the encoded
post-move ψ-shape and applies ADR-001's phase scaling. Strict-unitary
channels (0-4, 8-9) and best-effort channels (5-7, 10) are treated
uniformly here for the purpose of measuring phase-induced
distinguishability — the linearization quality of channels 5-7 / 10
is the subject of Probe 2 (linearization quality).

Reproducibility
---------------
All random sampling is seeded (NumPy default_rng with explicit seed,
plus the seeded self-play sampler from tests). No time-dependent
randomness.

Run
---
    python research/track_b_phase_distinguishability_probe.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Ensure the in-tree package is importable from the python/ working dir.
sys.path.insert(0, ".")

from chess_spectral import encoder_4d as _enc4  # noqa: E402
from chess_spectral import tables_4d as _t4  # noqa: E402
from chess_spectral import qm_4d as _qm4  # noqa: E402


# ---- ADR-001 §3.1 phase formula ------------------------------------

# Channel index -> (irrep type tag, phase formula). Mirrors
# ADR-001-phase-convention-for-unitary-moves.md §3.1.
_CHANNEL_PHASE_DESC: Dict[int, str] = {
    0:  "A1: theta=0",
    1:  "STD4_X: theta=(pi/4)*(x'-x)",
    2:  "STD4_Y: theta=(pi/4)*(y'-y)",
    3:  "STD4_Z: theta=(pi/4)*(z'-z)",
    4:  "STD4_W: theta=(pi/4)*(w'-w)",
    5:  "FIB_SYM_1: theta=(2pi/3)*d_path",
    6:  "FIB_SYM_2: theta=(4pi/3)*d_path",
    7:  "FIB_SYM_3: theta=(2pi)*d_path",
    8:  "FA_PAWN_W: theta=(pi/2)*sgn(w'-w)",
    9:  "FA_PAWN_Y: theta=(pi/2)*sgn(y'-y)",
    10: "FD_DIAG: theta=pi if diagonal_step else 0",
}


def _is_diagonal_step(o: Tuple[int, int, int, int],
                      d: Tuple[int, int, int, int]) -> bool:
    """Diagonal step iff the displacement has at least 2 non-zero
    components. Bishop steps and queen-diag steps land True; rook
    and king-axis-aligned steps land False."""
    delta = tuple(d[i] - o[i] for i in range(4))
    nonzero = sum(1 for x in delta if x != 0)
    return nonzero >= 2


def _chebyshev_path_length(o: Tuple[int, int, int, int],
                           d: Tuple[int, int, int, int]) -> int:
    """Chebyshev path length — number of single-step hops the piece
    traverses. For non-sliders this is the Chebyshev distance; for
    sliders this is the slide length (which is also Chebyshev distance
    on this lattice for axis-aligned and 2-face-diagonal moves)."""
    delta = tuple(d[i] - o[i] for i in range(4))
    return max(abs(x) for x in delta)


def adr001_channel_phases(o: Tuple[int, int, int, int],
                          d: Tuple[int, int, int, int],
                          ) -> np.ndarray:
    """Return the 11 per-channel phase angles (in radians) per
    ADR-001 §3.1.

    Inputs
    ------
    o : 4-tuple, origin square coords (each in [0, 7]).
    d : 4-tuple, destination square coords (each in [0, 7]).

    Returns
    -------
    theta : ndarray[float64], shape (11,)
    """
    delta = tuple(d[i] - o[i] for i in range(4))
    d_path = _chebyshev_path_length(o, d)
    pi = math.pi

    theta = np.zeros(_qm4.N_CHANNELS, dtype=np.float64)
    # Channel 0: A_1 — trivial irrep, theta = 0.
    theta[0] = 0.0
    # Channels 1-4: STD4_X/Y/Z/W — (pi/4) * delta_axis.
    theta[1] = (pi / 4.0) * delta[0]
    theta[2] = (pi / 4.0) * delta[1]
    theta[3] = (pi / 4.0) * delta[2]
    theta[4] = (pi / 4.0) * delta[3]
    # Channels 5-7: FIB_SYM_1/2/3 — (2pi/3, 4pi/3, 2pi) * d_path.
    theta[5] = (2.0 * pi / 3.0) * d_path
    theta[6] = (4.0 * pi / 3.0) * d_path
    theta[7] = (2.0 * pi) * d_path
    # Channels 8-9: FA_PAWN_W/Y — (pi/2) * sgn(delta_axis).
    theta[8] = (pi / 2.0) * float(np.sign(delta[3]))
    theta[9] = (pi / 2.0) * float(np.sign(delta[1]))
    # Channel 10: FD_DIAG — pi if diagonal step else 0.
    theta[10] = pi if _is_diagonal_step(o, d) else 0.0
    return theta


def apply_adr001_phases(enc: np.ndarray,
                        theta: np.ndarray,
                        ) -> np.ndarray:
    """Multiply each channel block of a 45056-vector by
    e^(i * theta_c). Returns complex128 ndarray of shape (45056,).

    The encoded `enc` is real-valued (encoder output); we cast to
    complex128 first.
    """
    if enc.shape[0] != _qm4.ENCODING_DIM:
        raise ValueError(
            f"enc must have shape ({_qm4.ENCODING_DIM},); got {enc.shape}"
        )
    if theta.shape != (_qm4.N_CHANNELS,):
        raise ValueError(
            f"theta must have shape ({_qm4.N_CHANNELS},); got {theta.shape}"
        )
    out = enc.astype(np.complex128)
    for c in range(_qm4.N_CHANNELS):
        start = c * _qm4.CHANNEL_DIM
        stop = start + _qm4.CHANNEL_DIM
        out[start:stop] *= np.exp(1j * theta[c])
    return out


# ---- Move enumeration ----------------------------------------------

# Map upper-case piece char -> tables_4d *_targets generator.
_PIECE_TARGETS_BY_SYMBOL: Dict[str, str] = {
    'N': 'knight4_targets',
    'B': 'bishop4_targets',
    'R': 'rook4_targets',
    'Q': 'queen4_targets',
    'K': 'king4_targets',
}


def enumerate_legal_moves(
    pos: Dict[Tuple[int, int, int, int], str],
    *,
    max_moves: int = 20,
    rng: Optional[np.random.Generator] = None,
) -> List[Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]]:
    """Enumerate up to `max_moves` legal moves from `pos`.

    A "legal" move here is any (origin, destination) where
      - origin holds a piece in pos.
      - destination is in the piece's *_targets() generator output,
        in-bounds, and unoccupied (no captures — matches the seeded
        self-play walker's rules).
    Pawns are skipped (the seeded walker doesn't produce them, and
    our probe doesn't attempt to model directed pawn pushes).

    If more than `max_moves` candidates exist, a deterministic
    sub-sample (via `rng`) is returned.
    """
    candidates: List[Tuple[Tuple[int, int, int, int],
                           Tuple[int, int, int, int]]] = []
    for coord, piece in pos.items():
        sym = piece.upper()
        gen_name = _PIECE_TARGETS_BY_SYMBOL.get(sym)
        if gen_name is None:
            continue  # pawn or unknown
        target_fn = getattr(_t4, gen_name)
        for tgt in target_fn(*coord):
            if not all(0 <= c < 8 for c in tgt):
                continue
            if tgt in pos:
                continue
            candidates.append((coord, tgt))
    if rng is None:
        rng = np.random.default_rng(0xCAFE_F00D)
    if len(candidates) <= max_moves:
        return candidates
    idx = rng.choice(len(candidates), size=max_moves, replace=False)
    return [candidates[int(i)] for i in idx]


def apply_move(
    pos: Dict[Tuple[int, int, int, int], str],
    origin: Tuple[int, int, int, int],
    dest: Tuple[int, int, int, int],
) -> Dict[Tuple[int, int, int, int], str]:
    """Apply a non-capture move; returns a new dict (does not mutate
    in place). Caller asserts the move was generated by
    `enumerate_legal_moves`."""
    new_pos = dict(pos)
    piece = new_pos.pop(origin)
    new_pos[dest] = piece
    return new_pos


# ---- Probe driver --------------------------------------------------


def _seeded_starting_positions(
    n_positions: int = 50,
    *,
    base_seed: int = 0xC4_E55,
    max_plies: int = 12,
) -> List[Dict[Tuple[int, int, int, int], str]]:
    """Generate a deterministic corpus of starting positions by running
    the seeded random walker for several plies from the canonical
    starting position. Each base seed yields a distinct (reproducible)
    walk; we record positions at varying plies so the corpus has
    structural variety.

    Returns a list of `pos` dicts (coord -> piece char).
    """
    base_pos = {
        (0, 0, 0, 0): 'K',  (7, 7, 7, 7): 'k',
        (1, 1, 1, 1): 'Q',  (6, 6, 6, 6): 'q',
        (2, 2, 2, 2): 'R',  (5, 5, 5, 5): 'r',
        (3, 0, 0, 0): 'B',  (4, 7, 7, 7): 'b',
        (0, 3, 0, 0): 'N',  (7, 4, 7, 7): 'n',
    }
    out: List[Dict[Tuple[int, int, int, int], str]] = []
    rng = np.random.default_rng(base_seed)

    # Always include the base position once (canonical anchor).
    out.append(dict(base_pos))

    # Build the rest by random walks at varying lengths.
    for i in range(1, n_positions):
        seed = int(rng.integers(0, 2**31 - 1))
        plies = int(rng.integers(1, max_plies + 1))
        pos = dict(base_pos)
        walk_rng = random.Random(seed)
        is_white = True
        for _ in range(plies):
            moves = enumerate_legal_moves(
                pos,
                max_moves=10**6,  # full enumeration for the walker
                rng=np.random.default_rng(seed + 1),
            )
            # Filter to side-to-move (matches walker semantics).
            side_moves = [
                (o, d) for (o, d) in moves
                if (pos[o].isupper() if is_white else pos[o].islower())
            ]
            if not side_moves:
                break
            o, d = walk_rng.choice(side_moves)
            pos = apply_move(pos, o, d)
            is_white = not is_white
        out.append(pos)
    return out


def _move_piece_type(
    pos: Dict[Tuple[int, int, int, int], str],
    origin: Tuple[int, int, int, int],
) -> str:
    """Upper-case piece symbol at `origin`."""
    return pos[origin].upper()


def run_probe(
    n_positions: int = 50,
    n_moves_per_pos: int = 20,
    *,
    seed: int = 0xC4_E55,
) -> dict:
    """Run the full probe and return a result dict.

    The result dict has keys:
      n_positions, n_moves_per_pos, total_pairs,
      overlap_percentiles (5/25/50/75/95),
      fraction_below_0.99, fraction_below_0.50,
      pass_acceptance (bool),
      per_position_summary (list).
    """
    positions = _seeded_starting_positions(
        n_positions=n_positions, base_seed=seed,
    )

    rng = np.random.default_rng(seed)
    overlaps: List[float] = []
    per_position: List[dict] = []
    total_distinct_pairs = 0

    for p_idx, pos in enumerate(positions):
        moves = enumerate_legal_moves(
            pos,
            max_moves=n_moves_per_pos,
            rng=np.random.default_rng(seed + p_idx),
        )
        if len(moves) < 2:
            per_position.append({
                "position_idx": p_idx,
                "n_moves": len(moves),
                "skipped": True,
            })
            continue

        # Pre-compute post-move psi for each move.
        psis: List[np.ndarray] = []
        coords: List[Tuple[Tuple[int, int, int, int],
                           Tuple[int, int, int, int]]] = []
        for (o, d) in moves:
            new_pos = apply_move(pos, o, d)
            new_pos_idx = {
                _t4.sq4(*c): p for c, p in new_pos.items()
            }
            enc = _enc4.encode_4d(new_pos_idx)
            theta = adr001_channel_phases(o, d)
            psi = apply_adr001_phases(enc, theta)
            n = float(np.linalg.norm(psi))
            if n == 0.0:
                # Degenerate — skip.
                psis.append(None)  # type: ignore[arg-type]
            else:
                psis.append(psi / n)
            coords.append((o, d))

        # Compute pairwise overlaps.
        position_overlaps: List[float] = []
        for i, j in combinations(range(len(moves)), 2):
            if psis[i] is None or psis[j] is None:
                continue
            (oi, di) = coords[i]
            (oj, dj) = coords[j]
            if (oi == oj) and (di == dj):
                continue  # not distinct
            total_distinct_pairs += 1
            overlap = abs(complex(np.vdot(psis[i], psis[j])))
            overlaps.append(overlap)
            position_overlaps.append(overlap)

        per_position.append({
            "position_idx": p_idx,
            "n_moves": len(moves),
            "n_pairs": len(position_overlaps),
            "overlap_50pct": float(np.median(position_overlaps))
                              if position_overlaps else None,
            "overlap_max": float(max(position_overlaps))
                             if position_overlaps else None,
        })

    overlaps_np = np.asarray(overlaps, dtype=np.float64)

    if overlaps_np.size == 0:
        # Pathological — no pairs at all.
        return {
            "n_positions": n_positions,
            "n_moves_per_pos": n_moves_per_pos,
            "total_pairs": 0,
            "overlap_percentiles": {},
            "fraction_below_0.99": None,
            "fraction_below_0.50": None,
            "pass_acceptance": False,
            "per_position_summary": per_position,
        }

    pcts = {
        "p5":  float(np.percentile(overlaps_np, 5)),
        "p25": float(np.percentile(overlaps_np, 25)),
        "p50": float(np.percentile(overlaps_np, 50)),
        "p75": float(np.percentile(overlaps_np, 75)),
        "p95": float(np.percentile(overlaps_np, 95)),
    }
    frac_99 = float((overlaps_np < 0.99).mean())
    frac_50 = float((overlaps_np < 0.50).mean())

    return {
        "n_positions": n_positions,
        "n_moves_per_pos": n_moves_per_pos,
        "total_pairs": int(overlaps_np.size),
        "overlap_percentiles": pcts,
        "fraction_below_0.99": frac_99,
        "fraction_below_0.50": frac_50,
        "pass_acceptance": frac_99 >= 0.80,
        "per_position_summary": per_position,
        "channel_phase_formulas": _CHANNEL_PHASE_DESC,
    }


def _emit_findings(result: dict) -> str:
    """Emit a one-paragraph findings note suitable for stdout."""
    if not result.get("total_pairs"):
        return "FINDINGS: probe failed to enumerate any move pairs."
    pcts = result["overlap_percentiles"]
    frac_99 = result["fraction_below_0.99"]
    frac_50 = result["fraction_below_0.50"]
    verdict = "PASS" if result["pass_acceptance"] else "FAIL"
    return (
        f"FINDINGS ({verdict}): probed {result['total_pairs']:,} "
        f"distinct (move_A, move_B) pairs across "
        f"{result['n_positions']} positions. Inner-product overlap "
        f"|<psi_A|psi_B>| has p5={pcts['p5']:.4f}, p50={pcts['p50']:.4f}, "
        f"p95={pcts['p95']:.4f}. Fraction below 0.99 (the 1% "
        f"distinguishability threshold): {frac_99:.2%}; fraction below "
        f"0.50 (strong distinguishability): {frac_50:.2%}. "
        f"Acceptance gate: at least 80% pairs below 0.99. "
        f"Result: {verdict}. "
        "ADR-001 verdict: SHIP AS-IS if PASS, REVISE otherwise."
    )


def main() -> int:
    out_path = Path(__file__).parent / (
        "track_b_phase_distinguishability_results.json"
    )
    print("Running ADR-001 phase-distinguishability probe...")
    result = run_probe(n_positions=50, n_moves_per_pos=20, seed=0xC4_E55)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print()
    print(_emit_findings(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
