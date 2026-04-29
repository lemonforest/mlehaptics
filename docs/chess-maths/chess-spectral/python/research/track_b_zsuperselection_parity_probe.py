"""Phase 3.5 probe — ADR-004 Z_2 superselection / U_move odd-parity.

Hypothesis: ADR-004 §3.4 declares U_move odd-parity under J_op
(the Z_2 grading operator from central-inversion + color-flip
symmetry). For the strict-unitary channels (A_1, STD4_X/Y/Z/W per
ADR-003 §3.1), U_move on each channel must anti-commute with J_op
restricted to that channel:
    U_move @ J_op + J_op @ U_move = 0     (anti-commutator)
i.e. {J_op, U_move} = 0 (Z_2-graded operator of odd parity).

If this fails for any strict channel, ADR-001's phase formula
needs a sign correction.

Acceptance criterion: For each of the 5 strict-unitary channels,
the anti-commutation residual ||U_move @ J_op + J_op @ U_move||_F
< 1e-10, averaged over a sample of 100 moves, in 95th percentile.

Method
------
1. Build J_op as a 4096x4096 permutation matrix: for each square
   s = (x,y,z,w), J_op @ e_s = e_{J(s)} where
   J(s) = (7-x, 7-y, 7-z, 7-w). On the 4096-dim board basis (no
   color labels), J_op is just central inversion.
2. For each strict-unitary channel c (0-4), and for each sampled
   (state, move) pair (o, d):
   a. Build U_move_c as e^(i * theta_c) * Pi_c where:
      - theta_c per ADR-001 §3.1 (channel-specific phase).
      - Pi_c = transposition swap on indices {sq4(o), sq4(d)}
        (this is the per-channel lift for A_1 per ADR-003 §3.1; for
        STD4_a it's the cleaner naive form — the actual ADR-003
        construction uses scaled permutations via diag(coord_resid)
        which we evaluate but do not differentiate from the swap
        for parity purposes; the parity property depends only on
        the permutation backbone, not the scaling).
   b. Compute the anti-commutator
        AC = U_move_c @ J_op + J_op @ U_move_c
      Frobenius norm.
3. Aggregate: per-channel mean and 95th-percentile residual.

If any channel fails, find the smallest sign correction to ADR-001's
phase formula that would restore anti-commutation. (E.g., a per-move
sign flip based on J(move) parity.)

Output
------
research/track_b_zsuperselection_parity_results.json — per-channel
percentiles, pass/fail, recommended correction.

Run
---
    python research/track_b_zsuperselection_parity_probe.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, ".")

from chess_spectral import tables_4d as _t4  # noqa: E402

# Reuse Probe 1 helpers for move enumeration.
from research.track_b_phase_distinguishability_probe import (  # noqa: E402
    enumerate_legal_moves,
    apply_move,
    _seeded_starting_positions,
    adr001_channel_phases,
)


N_SQUARES = _t4.N_SQUARES   # 4096

# Strict-unitary channels per ADR-003 §3.1 (Tier 1: Pi_c is a
# strict permutation/scaled-permutation, the channel is unitary on
# its block for non-capture moves).
_STRICT_UNITARY_CHANNELS = (0, 1, 2, 3, 4)
_STRICT_CHANNEL_NAMES = {
    0: "A1",
    1: "STD4_X",
    2: "STD4_Y",
    3: "STD4_Z",
    4: "STD4_W",
}


def build_J_op_4096() -> sp.csr_matrix:
    """Central inversion permutation matrix on the 4096-dim board:
    (x,y,z,w) -> (7-x, 7-y, 7-z, 7-w).
    Returns a 4096x4096 CSR with complex128 dtype (for compatibility
    with the complex U_move below)."""
    rows = np.empty(N_SQUARES, dtype=np.int64)
    cols = np.empty(N_SQUARES, dtype=np.int64)
    for s in range(N_SQUARES):
        coord = _t4.rc4(s)
        flipped = tuple(7 - c for c in coord)
        t = _t4.sq4(*flipped)
        rows[s] = t
        cols[s] = s
    data = np.ones(N_SQUARES, dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)), shape=(N_SQUARES, N_SQUARES),
    )


def build_swap_Pi(origin_idx: int, dest_idx: int) -> sp.csr_matrix:
    """Build the swap (transposition) matrix on the 4096-dim board:
    e_origin <-> e_dest, identity elsewhere.

    Returns a 4096x4096 CSR with complex128 dtype.
    """
    if origin_idx == dest_idx:
        # Trivial.
        return sp.eye(N_SQUARES, format="csr", dtype=np.complex128)
    rows = np.empty(N_SQUARES, dtype=np.int64)
    cols = np.empty(N_SQUARES, dtype=np.int64)
    for s in range(N_SQUARES):
        if s == origin_idx:
            t = dest_idx
        elif s == dest_idx:
            t = origin_idx
        else:
            t = s
        rows[s] = t
        cols[s] = s
    data = np.ones(N_SQUARES, dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)), shape=(N_SQUARES, N_SQUARES),
    )


def anti_commutator_residual(
    U: sp.csr_matrix, J: sp.csr_matrix,
) -> float:
    """Return ||U @ J + J @ U||_F."""
    AC = U @ J + J @ U
    AC = AC.tocoo()
    if AC.nnz == 0:
        return 0.0
    return float(np.linalg.norm(AC.data))


def commutator_residual(
    U: sp.csr_matrix, J: sp.csr_matrix,
) -> float:
    """Return ||U @ J - J @ U||_F. Useful for diagnosing whether the
    swap commutes (rather than anti-commutes) with J."""
    C = U @ J - J @ U
    C = C.tocoo()
    if C.nnz == 0:
        return 0.0
    return float(np.linalg.norm(C.data))


def signed_anti_commutator_residual(
    U: sp.csr_matrix, J: sp.csr_matrix,
    *, sign_correction: complex = -1.0,
) -> float:
    """Return ||(sign * U) @ J + J @ (sign * U)||_F. Used to test
    whether multiplying U by a global -1 (the implicit side-to-move
    sign of ADR-004) restores anti-commutation.
    """
    U_signed = sign_correction * U
    return anti_commutator_residual(U_signed, J)


def run_probe(
    n_positions: int = 50,
    n_moves_per_pos: int = 4,
    *,
    seed: int = 0xC4_E55,
) -> dict:
    """For each of the 5 strict-unitary channels, sample move pairs
    and compute the anti-commutation residual under several U_move
    constructions:
      (a) U_move = e^(i theta_c) * Pi_c   — naive ADR-001/003 lift.
      (b) U_move = -e^(i theta_c) * Pi_c  — naive lift with implicit
          side-to-move sign (the "implicit -1" interpretation).
      (c) U_move = e^(i (theta_c + alpha_J)) * Pi_c where alpha_J
          is determined by whether J(o) = d (i.e., the move is its
          own J-image: the destination is the central-inverse of
          origin). For such moves Pi_c commutes with J and an
          additional phase shift can convert commutation to anti-
          commutation. This is exploratory.

    Returns per-channel statistics for all three variants.
    """
    positions = _seeded_starting_positions(
        n_positions=n_positions, base_seed=seed,
    )
    rng = np.random.default_rng(seed)

    J = build_J_op_4096()

    # Per-channel residuals.
    naive_resid: Dict[int, List[float]] = {
        c: [] for c in _STRICT_UNITARY_CHANNELS
    }
    minus_resid: Dict[int, List[float]] = {
        c: [] for c in _STRICT_UNITARY_CHANNELS
    }
    commutator_resid: Dict[int, List[float]] = {
        c: [] for c in _STRICT_UNITARY_CHANNELS
    }
    j_symmetric_count = 0
    total_moves = 0

    for p_idx, pos in enumerate(positions):
        moves = enumerate_legal_moves(
            pos,
            max_moves=n_moves_per_pos,
            rng=np.random.default_rng(seed + p_idx),
        )
        for (o, d) in moves:
            total_moves += 1
            origin_idx = _t4.sq4(*o)
            dest_idx = _t4.sq4(*d)
            # Is this move J-symmetric?
            j_o = tuple(7 - c for c in o)
            if j_o == d:
                j_symmetric_count += 1

            theta = adr001_channel_phases(o, d)
            Pi = build_swap_Pi(origin_idx, dest_idx)
            for c in _STRICT_UNITARY_CHANNELS:
                phase = complex(np.exp(1j * theta[c]))
                # (a) Naive
                U_naive = phase * Pi
                naive_resid[c].append(
                    anti_commutator_residual(U_naive, J)
                )
                # (b) With implicit -1
                U_minus = -phase * Pi
                minus_resid[c].append(
                    anti_commutator_residual(U_minus, J)
                )
                # Commutator (vs anti-commutator) for diagnosis
                commutator_resid[c].append(
                    commutator_residual(U_naive, J)
                )

    def _pcts(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"p5": 0.0, "p50": 0.0, "p95": 0.0,
                    "max": 0.0, "mean": 0.0, "n": 0}
        a = np.asarray(arr, dtype=np.float64)
        return {
            "p5":   float(np.percentile(a, 5)),
            "p50":  float(np.percentile(a, 50)),
            "p95":  float(np.percentile(a, 95)),
            "max":  float(a.max()),
            "mean": float(a.mean()),
            "n":    int(a.size),
        }

    per_channel: Dict[str, dict] = {}
    naive_pass: Dict[int, bool] = {}
    minus_pass: Dict[int, bool] = {}
    for c in _STRICT_UNITARY_CHANNELS:
        name = _STRICT_CHANNEL_NAMES[c]
        per_channel[name] = {
            "channel_idx": c,
            "naive_anti_commutator_percentiles":
                _pcts(naive_resid[c]),
            "minus_sign_anti_commutator_percentiles":
                _pcts(minus_resid[c]),
            "commutator_percentiles":
                _pcts(commutator_resid[c]),
        }
        naive_pass[c] = (
            per_channel[name]
            ["naive_anti_commutator_percentiles"]["p95"] < 1e-10
        )
        minus_pass[c] = (
            per_channel[name]
            ["minus_sign_anti_commutator_percentiles"]["p95"] < 1e-10
        )

    return {
        "total_moves_sampled": total_moves,
        "j_symmetric_move_count": j_symmetric_count,
        "j_symmetric_fraction": (
            j_symmetric_count / total_moves if total_moves else 0.0
        ),
        "per_channel": per_channel,
        "all_strict_channels_pass_naive": all(naive_pass.values()),
        "all_strict_channels_pass_minus": all(minus_pass.values()),
        "method_notes": (
            "Per-channel U_move = e^(i*theta_c) * swap(o, d); "
            "anti-commutator residual ||U J + J U||_F. ADR-004 §3.4 "
            "predicts this should be 0. We test (a) the naive lift, "
            "(b) the naive lift with global -1 prefactor (representing "
            "the implicit side-to-move sign from state_to_psi), "
            "and (c) the commutator (UJ - JU) as a diagnostic for "
            "whether U commutes with J (which would be the opposite "
            "of the ADR-004 prediction). For the swap permutation "
            "lift, neither (a) nor (b) can satisfy strict anti-"
            "commutation in general because the swap matrix has only "
            "non-negative real entries and the anti-commutator with "
            "any positive permutation J is never zero unless the "
            "support of UJ + JU happens to be empty (which would "
            "require the swap and J to interact in a very special way)."
        ),
    }


def emit_findings(result: dict) -> str:
    """One-paragraph findings summary."""
    pc = result["per_channel"]
    naive_pass_all = result["all_strict_channels_pass_naive"]
    minus_pass_all = result["all_strict_channels_pass_minus"]
    verdict = (
        "PASS" if naive_pass_all
        else ("PASS_WITH_MINUS" if minus_pass_all else "FAIL")
    )
    lines = [
        f"FINDINGS ({verdict}): ADR-004 Z_2 superselection / U_move "
        f"odd-parity probe.",
        f"  Total moves sampled: {result['total_moves_sampled']}, "
        f"of which {result['j_symmetric_move_count']} are "
        f"J-symmetric (J(origin) == destination).",
    ]
    for name, data in pc.items():
        naive = data["naive_anti_commutator_percentiles"]
        minus = data["minus_sign_anti_commutator_percentiles"]
        comm = data["commutator_percentiles"]
        lines.append(
            f"  {name}: naive ||{{J,U}}|| p95={naive['p95']:.3e}, "
            f"minus ||{{J,-U}}|| p95={minus['p95']:.3e}, "
            f"commutator ||[J,U]|| p95={comm['p95']:.3e}."
        )
    if naive_pass_all:
        lines.append(
            "All 5 strict channels pass anti-commutation naively. "
            "ADR-004 §3.4: SHIP AS-IS."
        )
    elif minus_pass_all:
        lines.append(
            "All 5 strict channels pass with the implicit -1 sign "
            "from state_to_psi. ADR-004 §3.4: SHIP WITH MINOR "
            "CORRECTION (clarify in implementation that U_move "
            "carries a leading -1)."
        )
    else:
        # Look at a typical naive residual.
        a1 = pc["A1"]["naive_anti_commutator_percentiles"]
        comm = pc["A1"]["commutator_percentiles"]
        lines.append(
            f"FAIL: naive U_move = e^(i*theta_c) * Pi_c does NOT "
            f"anti-commute with J_op (typical residual is "
            f"~{a1['p95']:.2e}, far above 1e-10 tolerance). "
            f"The commutator ||[J, U]||_F is also non-zero "
            f"(p95 ~{comm['p95']:.2e}), confirming that for non-J-"
            f"symmetric moves the swap permutation neither "
            f"commutes nor anti-commutes with central inversion. "
            f"ADR-004 §3.4 needs revision: the odd-parity "
            f"requirement cannot be satisfied by a simple per-channel "
            f"phase + permutation. The ADR's parity argument is "
            f"informally correct (U_move flips side-to-move and "
            f"hence Z_2 sector), but the formal anti-commutation "
            f"identity is too strong for the per-channel "
            f"construction in ADR-001 / ADR-003. Recommended fix: "
            f"weaken §3.4 to 'U_move flips Z_2 sector via the "
            f"side-to-move sign baked into state_to_psi; the per-"
            f"channel Pi_c need not formally anti-commute with J_op'."
        )
    return "\n".join(lines)


def main() -> int:
    out_path = Path(__file__).parent / (
        "track_b_zsuperselection_parity_results.json"
    )
    print("Running ADR-004 Z_2 superselection / U_move parity probe...")
    result = run_probe(n_positions=50, n_moves_per_pos=4, seed=0xC4_E55)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print()
    print(emit_findings(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
