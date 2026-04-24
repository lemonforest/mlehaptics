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


def encode_768(state: Sequence[int] | np.ndarray) -> np.ndarray:
    """Compute the 768-dim spectral encoding of an Othello state.

    Parameters
    ----------
    state : length-64 integer sequence in {-1, 0, +1}
        World-frame Blume-Capel signal.  +1 = black disc, -1 = white
        disc, 0 = empty cell.  Ordering is row-major (row * 8 + col).

    Returns
    -------
    np.ndarray of shape (768,), dtype float64.
    """
    sig = np.asarray(state, dtype=np.float64)
    if sig.shape != (64,):
        raise ValueError(
            f"state must have shape (64,), got {sig.shape}"
        )
    # Blume-Capel values are {-1, 0, +1}; occupation = s^2 lands in
    # {0, 1}.
    occ = sig * sig

    out = np.zeros(ENCODING_DIM, dtype=np.float64)
    # 5 Z2-odd channels on magnetisation
    for i, irrep in enumerate(magn_irreps()):
        out[channel_slice(i)] = projector(irrep) @ sig
    # 5 Z2-even channels on occupation, starting at channel index 5
    for i, irrep in enumerate(occ_irreps()):
        out[channel_slice(5 + i)] = projector(irrep) @ occ
    # 2 orbit-Laplacian fiber channels on magnetisation, indices 10, 11
    L_ortho, L_diag = orbit_laplacian_pair()
    out[channel_slice(10)] = L_ortho @ sig
    out[channel_slice(11)] = L_diag @ sig
    return out


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
