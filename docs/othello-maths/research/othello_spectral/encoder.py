"""Othello spectral encoder — 768-dim position encoding.

Given a length-64 Blume-Capel signal (values in {-1, 0, +1} where
+1 = black, -1 = white, 0 = empty) the encoder emits a 768-dim
float64 vector laid out as:

    dims  [ 0:320) : 5 D4xZ2 '-' irreps applied to magnetisation s
    dims  [320:640): 5 D4xZ2 '+' irreps applied to occupation s^2
    dims  [640:768): 2 orbit-Laplacian fiber channels applied to s

Within each 320-block, irreps appear in the order
(A1-, A2-, B1-, B2-, E-) and (A1+, A2+, B1+, B2+, E+) respectively,
each contributing 64 consecutive dims (see tables.CHANNEL_NAMES).

The encoder is a pure function of the board signal.  Side-to-move
is NOT conditioned here; Z2 colour-flip equivariance is expressed
at the irrep level (the '-' irrep coefficients sign-flip under a
global colour inversion).

Determinism
-----------
- No random init, no hashing.
- Internal math: float64 throughout.
- Tables are precomputed rational matrices; character entries are
  in {-1, 0, 1, 2}; orbit Laplacians have integer entries.
- Output is bit-identical across Python/C17 implementations so long
  as both respect the same table contents and float64 multiply-add
  order.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .tables import (
    CELLS_PER_CHANNEL,
    CHANNEL_NAMES,
    ENCODING_DIM,
    N_CHANNELS,
    channel_slice,
    magn_irreps,
    occ_irreps,
    orbit_laplacian_pair,
    projector,
)


def encode_768(
    state: Sequence[int] | np.ndarray,
    fiber_mode: str = "sheaf",
) -> np.ndarray:
    """Compute the 768-dim spectral encoding of an Othello state.

    Parameters
    ----------
    state : length-64 integer sequence in {-1, 0, +1}
        World-frame Blume-Capel signal.  +1 = black disc, -1 = white
        disc, 0 = empty cell.  Ordering is row-major (row * 8 + col).
    fiber_mode : {"sheaf", "rank2"}
        - "sheaf" (default at v0.3.0+, reference): channels 10-11
          are per-cell pending-bracket (R3) counts from the black-
          owner and white-owner faithful sheaves.  State-dependent;
          captures active flank structure.  Exp 1 (§1e.7.x)
          showed that D4 projections of these channels beat the
          rank-2 occupation baselines against archive_mean_lb by
          ~40 % (partial rho -0.447 vs -0.319 for A1).
        - "rank2" (legacy, v0.2.0 reference): channels 10-11 are
          L_ortho @ s, L_diag @ s (pure orbit Laplacians on the
          magnetisation signal; state-linear, pure geometry).
          Kept for the C-encoder bit-identical parity path — C
          cannot yet compute the sheaf fiber.

    Returns
    -------
    np.ndarray of shape (768,), dtype float64.
    """
    sig = np.asarray(state, dtype=np.float64)
    if sig.shape != (64,):
        raise ValueError(
            f"state must have shape (64,), got {sig.shape}"
        )
    occ = sig * sig

    out = np.zeros(ENCODING_DIM, dtype=np.float64)
    # 5 Z2-odd channels on magnetisation
    for i, irrep in enumerate(magn_irreps()):
        out[channel_slice(i)] = projector(irrep) @ sig
    # 5 Z2-even channels on occupation, indices 5..9
    for i, irrep in enumerate(occ_irreps()):
        out[channel_slice(5 + i)] = projector(irrep) @ occ

    if fiber_mode == "rank2":
        L_ortho, L_diag = orbit_laplacian_pair()
        out[channel_slice(10)] = L_ortho @ sig
        out[channel_slice(11)] = L_diag @ sig
    elif fiber_mode == "sheaf":
        # Lazy import to avoid circular dependency on faithful_sheaf
        # and to keep the default encoder import lightweight.
        state_int = np.asarray(state, dtype=int)
        pending_b, pending_w = _sheaf_fiber_channels(state_int)
        out[channel_slice(10)] = pending_b
        out[channel_slice(11)] = pending_w
    else:
        raise ValueError(
            f"unknown fiber_mode {fiber_mode!r}; expected "
            f"'rank2' or 'sheaf'"
        )
    return out


def _sheaf_fiber_channels(state_int: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-cell pending-bracket counts for black and white
    faithful sheaves.  Imported lazily from faithful_sheaf.

    pending_<color>[i] = number of R3_PENDING brackets in which cell
    i participates (as the friendly origin OR as an opponent-run
    member), from the <color>-owner's perspective.  This mirrors the
    Exp 1 feature that beat the occupation D4-A1 channel on the
    Takizawa archive_mean_lb correlation by ~40 %.
    """
    # Sibling import — the faithful_sheaf module lives one level up.
    import sys
    from pathlib import Path as _Path
    _research_dir = _Path(__file__).resolve().parent.parent
    if str(_research_dir) not in sys.path:
        sys.path.insert(0, str(_research_dir))
    from faithful_sheaf import classify_ray, R3_PENDING
    from othello_utils import BLACK, N as _N, RAY_OFFSETS

    pending_b = np.zeros(_N, dtype=np.float64)
    pending_w = np.zeros(_N, dtype=np.float64)
    for v in range(_N):
        s_v = int(state_int[v])
        if s_v == 0:
            continue
        for _, (dr, dc) in RAY_OFFSETS.items():
            cls, opp_cells = classify_ray(state_int, v, dr, dc)
            if cls != R3_PENDING:
                continue
            target = pending_b if s_v == BLACK else pending_w
            target[v] += 1.0
            for w in opp_cells:
                target[w] += 1.0
    return pending_b, pending_w


def channel_energies(enc: np.ndarray) -> dict[str, float]:
    """Return {channel_name -> ||channel_block||^2} for the 12 channels.

    A convenience for reports and regression tests: after encoding a
    position, channel_energies gives the per-irrep + per-fiber-channel
    squared-norm breakdown.  Sum over all channels recovers ||enc||^2.
    """
    if enc.shape != (ENCODING_DIM,):
        raise ValueError(
            f"encoding must have shape ({ENCODING_DIM},), got {enc.shape}"
        )
    out: dict[str, float] = {}
    for i, name in enumerate(CHANNEL_NAMES):
        block = enc[channel_slice(i)]
        out[name] = float(np.dot(block, block))
    return out


def channel_block(enc: np.ndarray, index_or_name: int | str) -> np.ndarray:
    """Return the 64-dim slice for a named or indexed channel."""
    if isinstance(index_or_name, str):
        try:
            i = CHANNEL_NAMES.index(index_or_name)
        except ValueError as exc:
            raise ValueError(
                f"unknown channel {index_or_name!r}; expected one of "
                f"{CHANNEL_NAMES}"
            ) from exc
    else:
        i = int(index_or_name)
    return enc[channel_slice(i)]


__all__ = [
    "encode_768",
    "channel_energies",
    "channel_block",
    "ENCODING_DIM",
    "N_CHANNELS",
    "CHANNEL_NAMES",
]
