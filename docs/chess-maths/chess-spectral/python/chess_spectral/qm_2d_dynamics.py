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
(chess4d-OC for 4D — short for chess4d-oana-chiru, the specific
ruleset from Oana & Chiru 2026; and the upcoming 2D consumer using
standard chess rules), which animate per-channel phase rotations
across move boundaries. v1.5 shipped the 4D dynamics + bridge;
v1.6 shipped 2D kinematics; v1.6.x closes the asymmetry by shipping
the 2D dynamics + bridge.

Eigenbasis-diagonal optimization (ADR-002 §6.1)
-----------------------------------------------
``evolve_under_h0`` now implements the eigenbasis-diagonal optimization
from ADR-002 §6 future-work item 1 (originally deferred from v1.5.0).
The 64×64 ``H_0`` is real-symmetric so :func:`numpy.linalg.eigh` decomposes
it as ``H_0 = V @ diag(λ) @ V^H`` once, lazily cached at first call. Time
evolution then reduces to the diagonal-phase form::

    U(t) = V @ diag(exp(-i*λ*t)) @ V^H

For the full 640-dim 10-channel state, the 10 blocks are evolved in
parallel via two ``(10, 64) @ (64, 64)`` matrix products — the
"hyper-wrap-for-parallel-ops" interpretation of ``H_full = I_10 ⊗ H_0``
as a fiber-bundle operator (chess-spectral / srmech §3.5.4 sub-row
covering ``I_fiber ⊗ O_base`` factorisations). At chess-2D scale the
synthetic benchmark in :file:`docs/srmech/notes/chess-channels-and-hyper-parallel-script.py`
measures **~196× speedup** over the previous per-channel
``scipy.sparse.linalg.expm_multiply`` loop, with max-abs deviation
``1.8e-16`` (machine-precision bit-equivalent against the sparse path).

Norm and energy preservation hold exactly because ``V`` is unitary
(``V^H V = I``) and the phase factors ``exp(-i λ t)`` are unit-modulus.
The eigenbasis cache is invalidated only if the H_0 cache is rebuilt
(which currently only happens via module reload or explicit
``_H_FREE_2D = None`` poke — neither is part of the public API).

ADR conformance: the eigenbasis is computed via ``numpy.linalg.eigh``
(LAPACK syevd / syevr) at module-first-call (lazy), kept in
``complex128``, and shared between the single-block and full-vector
paths. Per ADR-002 §6.1, the 4D analogue is **not** enabled because
its 4096×4096 eigendecomposition takes ~124 s one-shot and the per-call
cost inverts to slower-than-sparse (`docs/srmech/notes/chess-channels-and-hyper-parallel-2026-05-11.md`).

Design references
-----------------
- :mod:`chess_spectral.qm_4d_dynamics` — the 4D analogue (this module
  mirrors its structure 1:1 at d=2, except the 4D side keeps the
  sparse ``expm_multiply`` path per the 2026-05-11 honest-negative
  benchmark finding above).
- ADR-002 §3.1 (in 4D research notebook) — the Zeno free-evolution
  semantics; the 2D and 4D side share the construction up to lattice
  dimension.
- ADR-002 §6.1 — the eigenbasis-diagonal optimization spec implemented
  here.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix

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


# ─── Eigenbasis cache (ADR-002 §6.1 optimization) ──────────────────
#
# Lazy module-level cache of ``eigh(H_FREE_2D.toarray())``. Holds
# ``(λ, V)`` where ``λ`` is a real ``(64,)`` array of eigenvalues and
# ``V`` is a unitary ``(64, 64)`` complex128 array of eigenvectors as
# columns, satisfying ``H_0 == V @ diag(λ) @ V.conj().T`` to machine
# precision. ``H_0`` is real-symmetric (Hermitian with zero imaginary
# part) so :func:`numpy.linalg.eigh` returns a *real* λ and the V is
# real-orthogonal in principle; we keep V in complex128 so the
# downstream phase-multiplication is a single dtype-clean operation.

_H0_EIGENBASIS_2D: Optional[Tuple[np.ndarray, np.ndarray]] = None


def _get_h0_eigenbasis_2d() -> Tuple[np.ndarray, np.ndarray]:
    """Cached accessor for the eigendecomposition of H_FREE_2D.

    Returns ``(eigvals, eigvecs)`` where ``eigvals`` is a real
    ``(CHANNEL_DIM,)`` float64 array (ascending order) and ``eigvecs``
    is a complex128 ``(CHANNEL_DIM, CHANNEL_DIM)`` array with the k-th
    eigenvector in column k. ``H_FREE_2D() == eigvecs @ diag(eigvals)
    @ eigvecs.conj().T`` to machine precision.

    Built on first call via :func:`numpy.linalg.eigh` on the dense
    64×64 form; cost is well under 1 ms (negligible against any
    realistic propagation workload). The 4D analogue is deliberately
    NOT enabled — see ADR-002 §6.1 and the 2026-05-11 benchmark in
    :file:`docs/srmech/notes/chess-channels-and-hyper-parallel-2026-05-11.md`
    for the breakeven calculation that justified the deferral.
    """
    global _H0_EIGENBASIS_2D
    if _H0_EIGENBASIS_2D is None:
        H0_dense = _get_h_free_2d().toarray()
        # eigh returns real eigvals and a real-orthogonal V for
        # real-symmetric input; we lift V to complex128 so the
        # subsequent phase-multiplication stays in one dtype.
        eigvals, eigvecs = np.linalg.eigh(H0_dense)
        eigvecs = np.ascontiguousarray(eigvecs, dtype=np.complex128)
        # eigvals stays float64; we never need it as complex (phases are
        # exp(-i * eigvals * t), and the multiplication promotes to
        # complex128 naturally).
        _H0_EIGENBASIS_2D = (eigvals, eigvecs)
    return _H0_EIGENBASIS_2D


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
    because :func:`evolve_under_h0` evaluates ``U(t) = exp(-i H_0 t)``
    in the eigenbasis of ``H_0`` (cached via
    :func:`_get_h0_eigenbasis_2d`) and broadcasts the unitary across
    the 10 channel blocks via a single ``(10, 64) @ (64, 64)`` matmul
    pair. See ADR-002 §6.1.
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

    # ADR-002 §6.1 eigenbasis-diagonal path:
    #   U(t) = exp(-i t H_0) = V @ diag(exp(-i λ t)) @ V^H
    # H_0 is real-symmetric Hermitian; eigh decomposes once at module-
    # first-call and we apply U(t) per-block as two matrix products
    # with an elementwise phase factor in between. At chess-2D scale
    # this is ~196× faster than the previous per-channel
    # ``scipy.sparse.linalg.expm_multiply`` loop, with max-abs
    # deviation 1.8e-16 (machine-precision bit-equivalent). See the
    # 2026-05-11 benchmark in
    # ``docs/srmech/notes/chess-channels-and-hyper-parallel-2026-05-11.md``.
    eigvals, V = _get_h0_eigenbasis_2d()
    phases = np.exp(-1j * eigvals * t)  # (CHANNEL_DIM,) complex128

    if psi_c.shape[0] == CHANNEL_DIM:
        # Single 64-block: V^H @ ψ → phase-multiply → V @ result.
        # V is unitary (V^H V = I); phases are unit-modulus; so the
        # whole operation is exactly the action of U(t) on ψ.
        coefs = V.conj().T @ psi_c          # (n,)
        coefs *= phases                     # (n,) elementwise
        return np.ascontiguousarray(V @ coefs, dtype=np.complex128)

    # Full 640-dim. If `channel` is set, only touch that block;
    # otherwise broadcast V across all 10 channel blocks in one batched
    # matmul ("hyper-wrap-for-parallel-ops" via the I_10 ⊗ H_0 fiber
    # factorisation — see chess-spectral / srmech §3.5.4 fiber-bundle
    # row covering ``I_fiber ⊗ O_base`` operators).
    out = psi_c.copy()
    if channel is not None:
        start, end = _channel_offset_2d(channel)
        block = psi_c[start:end]
        coefs = V.conj().T @ block
        coefs *= phases
        out[start:end] = V @ coefs
        return out

    # Reshape psi_c into (N_CHANNELS, CHANNEL_DIM) and apply U(t) to
    # all 10 channel blocks simultaneously via two matmuls. The
    # ``ravel()`` at the end returns a contiguous 1-D array; we
    # explicitly cast for dtype-clarity.
    psi_blocks = psi_c.reshape(N_CHANNELS, CHANNEL_DIM)
    coefs = psi_blocks @ V.conj()   # (N, n): equivalent to (V^H @ psi.T).T per row
    coefs *= phases                  # broadcasts (N, n) * (n,)
    psi_out_blocks = coefs @ V.T     # (N, n) @ (n, n) -> (N, n)
    return np.ascontiguousarray(psi_out_blocks.ravel(), dtype=np.complex128)


# ─── A_1 channel (D_4 trivial irrep) projector ─────────────────────
#
# P_A1 = (1/|D_4|) * sum_{g in D_4} Pi(g)  on  C^64
#
# Pi is the D_4 permutation action on the 64-dim lattice signal
# space (8x8 chessboard, D_4 symmetries: 4 rotations × {identity,
# reflection} = 8 elements). The averaged operator P_A1 is the
# orthogonal projector onto the A_1 (trivial) irrep — the
# totally-symmetric (rotation- and reflection-invariant) signals.
#
# This is the 2D analogue of `tables_4d.b4_a1_orbit_projector` (4D);
# we construct it here from the existing `qm_2d.d4_closure` +
# `d4_unitary_rep_64` rather than adding a tables.py builder, since
# the 2D D_4 group is small (8 elements) and the construction is a
# 5-line average.

_P_A1_2D: Optional[csr_matrix] = None


def _build_p_a1_2d() -> csr_matrix:
    """Build the A_1 D_4 orbit projector on C^64.

    P_A1 = (1/8) * sum_{g in D_4} Pi(g) where Pi(g) is the 64-dim
    permutation matrix for group element g. P_A1 is real-symmetric
    (so Hermitian as a complex matrix), idempotent (P_A1 @ P_A1 ==
    P_A1), and orthogonal-projector-rank == number of D_4 orbits on
    the 8x8 board (= 10).
    """
    from chess_spectral.qm_2d import d4_closure, d4_unitary_rep_64
    closure = d4_closure()
    order = len(closure)
    assert order == 8, f"D_4 closure size {order} != 8"
    P: Optional[csr_matrix] = None
    for g in closure:
        Pi = d4_unitary_rep_64(g)
        P = Pi if P is None else (P + Pi)
    assert P is not None
    P = (P / order).tocsr()
    if P.dtype != np.complex128:
        P = P.astype(np.complex128)
    return P


def _get_p_a1_2d() -> csr_matrix:
    """Cached accessor for the A_1 D_4 orbit projector P_A1 on C^64."""
    global _P_A1_2D
    if _P_A1_2D is None:
        _P_A1_2D = _build_p_a1_2d()
    return _P_A1_2D


def P_A1_2D() -> csr_matrix:
    """Public accessor for the A_1 D_4 orbit projector on C^64.

    Returns a 64x64 sparse Hermitian projector. ``P_A1.conj().T == P_A1``
    and ``P_A1 @ P_A1 == P_A1`` exactly (idempotent). The rank equals
    the number of D_4 orbits on the 8x8 lattice (10).
    """
    return _get_p_a1_2d()


# ─── Move-as-unitary builders (Track B) ────────────────────────────


def _swap_unitary_2d(from_idx: int, to_idx: int) -> csr_matrix:
    """Return the 64x64 sparse permutation that swaps basis vectors
    ``from_idx`` and ``to_idx`` (and leaves the other 62 fixed).

    This is the bare swap operator U_swap on C^64 — unitary on the
    full space, but does NOT in general commute with the D_4 orbit
    projector P_A1. The projector-sandwich
    ``P_A1 @ U_swap @ P_A1`` is sub-unitary on ``range(P_A1)``;
    strict unitarity on the A_1 subspace requires the swap to be
    intra-orbit.
    """
    if not 0 <= from_idx < CHANNEL_DIM:
        raise ValueError(
            f"from_idx {from_idx} out of range [0, {CHANNEL_DIM})"
        )
    if not 0 <= to_idx < CHANNEL_DIM:
        raise ValueError(
            f"to_idx {to_idx} out of range [0, {CHANNEL_DIM})"
        )
    # Permutation matrix that swaps from_idx and to_idx.
    perm = np.arange(CHANNEL_DIM, dtype=np.int64)
    perm[from_idx], perm[to_idx] = to_idx, from_idx
    rows = perm.tolist()
    cols = list(range(CHANNEL_DIM))
    data = [1.0 + 0j] * CHANNEL_DIM
    return csr_matrix(
        (data, (rows, cols)),
        shape=(CHANNEL_DIM, CHANNEL_DIM),
        dtype=np.complex128,
    )


def u_move_a1_2d(
    from_sq: int,
    to_sq: int,
) -> csr_matrix:
    """Build the A_1 channel move-as-unitary on C^64 (2D analogue of
    :func:`chess_spectral.qm_4d_dynamics.u_move_a1`).

    Construction (mirroring the 4D B1 milestone, projector-sandwich
    form):

      1. Build ``U_swap = swap(from_sq <-> to_sq)`` on ``C^64``.
      2. Multiply by the A_1 channel phase factor (= 1.0 for the
         trivial irrep, per ADR-001 §3.1's row "A1").
      3. Wrap in the P_A1 projector sandwich:
         ``U_a1 = P_A1 @ U_swap @ P_A1``.

    The result ``U_a1`` is **sub-unitary** on the full C^64: zero
    outside ``range(P_A1)`` and unitary within when ``U_swap``
    commutes with ``P_A1`` (i.e., when ``from_sq`` and ``to_sq`` lie
    in the same D_4 orbit). For typical chess moves (which often
    cross orbits), ``U_a1.conj().T @ U_a1 != P_A1`` exactly — the
    sandwich is contractive but not strict-unitary.

    This is the 2D analogue of ADR-003 §3.1's amended Phase 3.5
    finding for the 4D side: same algebra, same caveats, same
    interpretation (suitable for channel-marginal phase rotation
    visualizations; falls short of strict unitarity for cross-orbit
    moves).

    Capture path is deferred to v1.6.x PR-D (B5 analog).

    Parameters
    ----------
    from_sq : int
        Source square index in ``[0, 64)`` (8x8 = 64 squares).
    to_sq : int
        Destination square index in ``[0, 64)``.

    Returns
    -------
    csr_matrix of shape ``(64, 64)``, dtype ``complex128``.

    Raises
    ------
    ValueError
        If either endpoint is out of range, or the move is null
        (``from_sq == to_sq``).
    """
    if from_sq == to_sq:
        raise ValueError(
            f"u_move_a1_2d: null move ({from_sq} -> {to_sq}) is undefined"
        )
    U_swap = _swap_unitary_2d(from_sq, to_sq)
    # A_1 channel phase factor is exactly 1.0 (ADR-001 §3.1 row "A1").
    # We multiply explicitly for symmetry with future per-channel
    # builders that have non-trivial phases.
    phase: complex = complex(1.0, 0.0)
    P_A1 = _get_p_a1_2d()
    # P_A1 is real-symmetric, so P_A1.conj().T == P_A1; we don't need
    # to explicitly conjugate the trailing sandwich.
    U_a1 = P_A1 @ (phase * U_swap) @ P_A1
    return U_a1.tocsr()


__all__ = [
    "H_FREE_2D",
    "evolve_under_h0",
    "P_A1_2D",
    "u_move_a1_2d",
]
