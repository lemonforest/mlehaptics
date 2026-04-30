"""chess_spectral.qm_2d_dynamics - Track B move-as-unitary dynamics for 2D.

Mirrors :mod:`chess_spectral.qm_4d_dynamics` at the 2D scale: the encoder
output is 640-dim float32 (10 channels x 64 modes), so the per-channel
mode space is ``C^64`` and the full QM Hilbert space is ``C^640`` (with
``H_full = I_10 ⊗ H_0`` for any per-channel observable / Hamiltonian
``H_0`` on ``C^64``).

This module ships the **skeleton** of the 2D dynamics (v1.6.x PR-A):

  * **H_FREE_2D** — the free-particle Hamiltonian ``H_0 = -Δ_{P_8^2}``
    as a 64x64 sparse matrix. Built via Kron-sum of two ``L_8`` 1D
    path-graph Laplacians (the same construction as :mod:`qm_4d_dynamics`'s
    H_FREE_4D, just at d=2 instead of d=4).

  * **evolve_under_h0** — Zeno free-evolution by ``U(t) = exp(-i H_0 t)``.
    Accepts either a single 64-dim channel block or the full 640-dim
    vector (broadcasts H_0 across the 10 channels via ``I_10 ⊗ H_0``).

The per-channel **u_move_*_2d** builders (the 2D analogues of B1/B3a/...
in the 4D module) ship in subsequent v1.6.x PRs (-B, -C, -D). The 2D
QM bridge surface (§17.2) wraps this module in v1.6.x PR-E + PR-F.

Why qm_2d_dynamics ships in v1.6.x
-----------------------------------
The §16.1 evaluator ``qm`` shipped in v1.6 (2D + 4D) and consumes only
the **kinematic** layer (:mod:`qm_2d` / :mod:`qm_4d`) — it computes
expectation values of static observables, not move-as-unitary dynamics.
The dynamics layer is needed by the §17 Pyodide bridge consumers
(chess4d-OC, the upcoming chess2d-OC), which animate per-channel
phase rotations across move boundaries. v1.5 shipped the 4D dynamics
+ bridge; v1.6 shipped 2D kinematics; v1.6.x closes the asymmetry by
shipping the 2D dynamics + bridge.

Design references
-----------------
- :mod:`chess_spectral.qm_4d_dynamics` — the 4D analogue (this module
  mirrors its structure 1:1 at d=2).
- ADR-002 §3.1 (in 4D research notebook) — the Zeno free-evolution
  semantics; the 2D and 4D side share the construction up to lattice
  dimension.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from chess_spectral.qm_2d import (
    CHANNEL_DIM,          # 64 = mode count per channel (8 * 8 squares)
    ENCODING_DIM,         # 640 = N_CHANNELS * CHANNEL_DIM
    N_CHANNELS,           # 10
)

# Note: qm_2d.BOARD_DIM is 64 (the per-channel mode count, == CHANNEL_DIM).
# We need the 1D side length for the L_8 path-graph construction; that
# is not a public symbol elsewhere, so we hard-code it here. CHANNEL_DIM
# == BOARD_SIDE ** 2 == 64.
BOARD_SIDE: int = 8
assert BOARD_SIDE ** 2 == CHANNEL_DIM, (
    f"BOARD_SIDE^2={BOARD_SIDE**2} must equal CHANNEL_DIM={CHANNEL_DIM}"
)


# ─── H_FREE_2D — free-particle Hamiltonian on the per-channel space ──
#
# H_0 = -Δ_{P_8^2}, where Δ is the 2D path-graph Laplacian on Z_8^2.
# Δ is the Kron-sum of two copies of the 1D 8-node path-graph
# Laplacian L_8. Constructed lazily via _build_h_free_2d() and cached
# in the module-level singleton _H_FREE_2D.

_H_FREE_2D: Optional[csr_matrix] = None


def _l8_path_laplacian() -> csr_matrix:
    """1D path-graph Laplacian on 8 nodes. Tridiagonal with diagonal
    [1, 2, 2, 2, 2, 2, 2, 1] (interior degree 2, endpoint degree 1)
    and off-diagonals -1. This is the same matrix used by
    :func:`qm_4d_dynamics._l8_path_laplacian`; we reproduce it here so
    this module is self-contained and doesn't import the 4D-side
    private helper."""
    n = BOARD_SIDE
    main = np.empty(n, dtype=np.complex128)
    main[0] = 1.0
    main[-1] = 1.0
    main[1:-1] = 2.0
    off = -np.ones(n - 1, dtype=np.complex128)
    L = sp.diags(
        [off, main, off], offsets=[-1, 0, 1],
        shape=(n, n), format="csr", dtype=np.complex128,
    )
    return L


def _build_h_free_2d() -> csr_matrix:
    """Build ``H_0 = -Δ_{P_8^2}`` as a 64×64 sparse matrix.

    Δ is the 2D path-graph Laplacian — Kron-sum of two copies of the
    1D 8-node path-graph Laplacian L_8.

    Sign: returns ``-Δ`` (Hermitian, negative-semidefinite). The
    spectrum of Δ is ``[0, ~7.7]`` (sum of two ``[0, ~3.84776]`` 1D
    spectra), so the spectrum of H_0 is ``[-7.7, 0]``.

    Returns
    -------
    csr_matrix of shape ``(64, 64)``, dtype ``complex128``. Hermitian
    (real-symmetric, with zero imaginary part). Sparse with the Δ
    structure (each interior site has 5 neighbors including self;
    each axis-edge site has 4; each corner has 3).
    """
    L1 = _l8_path_laplacian()
    n = L1.shape[0]
    eye = sp.eye(n, format="csr", dtype=np.complex128)

    # Δ = (L_8 ⊗ I_8) + (I_8 ⊗ L_8)
    delta = sp.kron(L1, eye, format="csr") + sp.kron(eye, L1, format="csr")
    delta = delta.tocsr()

    # H_0 = -Δ
    H0 = (-delta).tocsr()
    if H0.dtype != np.complex128:
        H0 = H0.astype(np.complex128)
    return H0


def _get_h_free_2d() -> csr_matrix:
    """Cached accessor for the H_FREE_2D singleton — builds on first call."""
    global _H_FREE_2D
    if _H_FREE_2D is None:
        _H_FREE_2D = _build_h_free_2d()
    return _H_FREE_2D


def _channel_offset_2d(channel: str) -> Tuple[int, int]:
    """Map a 2D channel name to its ``(start, end)`` slice into the
    640-dim full encoder vector.

    The 10 channel names in encoder order are:
    ``A1, A2, B1, B2, E, F1, F2, F3, FA, FD``.

    Source of truth: :data:`chess_spectral.encoder.CHANNELS`.
    """
    from chess_spectral.encoder import CHANNELS
    for name, start in CHANNELS:
        if name == channel:
            return int(start), int(start + CHANNEL_DIM)
    valid = [name for name, _ in CHANNELS]
    raise ValueError(
        f"unknown channel name {channel!r}; expected one of {valid}"
    )


# ─── Public surface ────────────────────────────────────────────────


def H_FREE_2D() -> csr_matrix:
    """Public accessor for the free-particle Hamiltonian ``H_0 = -Δ_{P_8^2}``.

    Returns the cached 64x64 sparse Hermitian matrix. First call builds
    via :func:`_build_h_free_2d`; subsequent calls return the singleton.

    The full 640-dim Hamiltonian (operating on the 10-channel ψ) is
    ``I_{10} ⊗ H_FREE_2D``; we don't materialize that 640×640 explicitly
    because :func:`evolve_under_h0` broadcasts H_0 across the 10 channel
    blocks using :func:`scipy.sparse.linalg.expm_multiply`.
    """
    return _get_h_free_2d()


def evolve_under_h0(
    psi: np.ndarray,
    t: float,
    *,
    channel: Optional[str] = None,
) -> np.ndarray:
    """Evolve ``psi`` under ``U(t) = exp(-i H_0 t)`` for time ``t``.

    Mirrors :func:`chess_spectral.qm_4d_dynamics.evolve_under_h0` at
    2D dimensionality. Implements the Zeno-style continuous-time
    evolution between move boundaries.

    Parameters
    ----------
    psi : ndarray
        State vector. Two accepted shapes:

        * ``(64,)``: a single channel block (one of the 10 channel
          sub-vectors in the 640-dim full state). Evolves under H_0
          directly.
        * ``(640,)``: the full 10-channel encoder vector. By default
          all 10 blocks are evolved independently under the same H_0
          (since H_0 acts on the 64-dim mode space, not the
          channel-typed space — the full Hamiltonian on C^640 is
          ``I_{10} ⊗ H_0``). If ``channel`` is provided, only that
          block is evolved; the other nine are copied through
          unchanged.

        Dtype is cast to ``complex128``.

    t : float
        Real evolution time. ``t == 0`` is a no-op (returns a copy of
        ``psi``). Negative ``t`` evolves backward in time, which is
        well-defined because U(t) is unitary and ``U(-t) = U(t)†``.

    channel : str, optional
        One of the 10 channel names (``'A1'``, ``'A2'``, ``'B1'``,
        ``'B2'``, ``'E'``, ``'F1'``, ``'F2'``, ``'F3'``, ``'FA'``,
        ``'FD'``). If given, ``psi`` must be the full 640-dim vector
        and only the named channel's 64-block is evolved; the other 9
        are copied through. Raises if ``psi`` is the 64-dim shape.

    Returns
    -------
    ndarray of the same shape and dtype (``complex128``) as ``psi``.

    Raises
    ------
    ValueError
        If ``psi`` is not 1-D or has a shape other than ``(64,)`` or
        ``(640,)``; or if ``channel`` is given with a ``(64,)`` ``psi``;
        or if ``channel`` is not a recognized name.
    """
    if psi.ndim != 1:
        raise ValueError(
            f"psi must be 1-D; got shape {psi.shape}"
        )
    if psi.shape[0] not in (CHANNEL_DIM, ENCODING_DIM):
        raise ValueError(
            f"psi must have shape ({CHANNEL_DIM},) or ({ENCODING_DIM},); "
            f"got {psi.shape}"
        )
    if channel is not None and psi.shape[0] != ENCODING_DIM:
        raise ValueError(
            f"channel={channel!r} requires the full 640-dim psi; "
            f"got shape {psi.shape}. Drop channel= or pass the full vector."
        )

    psi_c = np.ascontiguousarray(psi, dtype=np.complex128)
    if t == 0.0:
        return psi_c.copy()

    H0 = _get_h_free_2d()
    # U(t) = exp(-i t H_0); since H_0 is Hermitian, this is unitary.
    # expm_multiply takes A and v and returns exp(A) @ v efficiently
    # via Krylov subspace iteration; A here is the anti-Hermitian
    # operator -i*t*H_0.
    A = (-1j * t) * H0

    if psi_c.shape[0] == CHANNEL_DIM:
        # Single 64-block.
        return np.asarray(expm_multiply(A, psi_c), dtype=np.complex128)

    # Full 640-dim. Evolve per-channel. If `channel` is set, only
    # touch that block; otherwise broadcast H_0 across all 10.
    out = psi_c.copy()
    if channel is not None:
        start, end = _channel_offset_2d(channel)
        out[start:end] = expm_multiply(A, psi_c[start:end])
        return out

    for ch in range(N_CHANNELS):
        start = ch * CHANNEL_DIM
        end = start + CHANNEL_DIM
        out[start:end] = expm_multiply(A, psi_c[start:end])
    return out


__all__ = [
    "H_FREE_2D",
    "evolve_under_h0",
]
