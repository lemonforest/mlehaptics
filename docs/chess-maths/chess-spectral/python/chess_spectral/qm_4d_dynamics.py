"""chess_spectral.qm_4d_dynamics - Track B move-as-unitary dynamics.

Phase 4 milestone B1: A_1 channel move-as-unitary (the simplest of the
five strict-unitary tier channels per ADR-003 §3.1). This module is the
first concrete piece of Track B; it sits beside :mod:`chess_spectral.qm_4d`
(Track A kinematic) per the convention announced in ADR-002.

Subsequent milestones extend this module:
  - **B2** (next): full Zeno evolution + H_0 wiring.
  - **B3a** (next strict-unitary channels): STD4_X/Y/Z/W per
    ADR-003's per-channel construction.
  - **B3b**: pawn antisymmetric channels (FA_PAWN_W/Y).
  - **B3c**: FIB_SYM_1/2/3 (measurement-only re-encode per Phase 3.5
    Probe 2 amendment).
  - **B3d/e**: FD_DIAG (rank-1 + renormalization).
  - **B5**: capture-move handling (partial isometry on FA_PAWN; rank-1
    update on FD_DIAG; full Stinespring deferred to v1.7+).

This module deliberately ships **only A_1** so the strict-unitary path
can be exercised end-to-end at the smallest granularity. The
:func:`u_move_a1` builder + the :func:`apply_move_qm` stub form the
bridge surface that B2-B5 plug into without touching this file.

Phase 3.5 Probe-Result Amendments
---------------------------------

ADR-003 §3.1 sketches `Pi_0` (the A_1 channel's per-move unitary) as
a bare 4096-square swap matrix. **B1 implements the projector-sandwich
form** ``U_a1 = P_A1 @ U_swap @ P_A1`` per the user-spec for B1: this is
the construction that lives entirely within ``range(P_A1)`` (the A_1
subspace as defined by the encoder). The bare-swap form is unitary on
the full ``C^4096`` but does not preserve the A_1 subspace; the
projector-sandwich is sub-unitary on ``range(P_A1)``.

A new finding from B1: the projector-sandwich is **only sub-unitary
when the swap commutes with P_A1**, which holds iff ``sq_from`` and
``sq_to`` lie in the same B_4 orbit. For typical chess moves (which
cross orbits), ``U_a1.conj().T @ U_a1 != P_A1`` and the
re-encoding-match fails too. See the test module's findings docstrings
for the sample-level numerical evidence; ADR-003 §3.1 will need an
amendment to either restrict the strict-unitary claim to same-orbit
moves or to redesign the lift. The current shipped construction is
**honest about its support**: it is exact on same-orbit non-capture
moves and is a documented-not-strict approximation on cross-orbit
moves (suitable for the channel-marginal phase-rotation visualization
M14.2/M14.3 needs).

ADR-001 §3.1: the A_1 channel phase is exactly ``e^{i * 0} = 1``
(theta_0 = 0 for the trivial irrep). The phase factor is kept
explicit in the implementation so the same code structure scales to
the other 10 channels in B2-B5.

ADR-004 §3.4 (Phase 3.5 Probe-4 amendment): U_move is **not** required
to anti-commute with J_op as algebraic operators. The Z_2 sector flip
is implemented at the state-vector level via ``state_to_psi``'s
side-to-move sign multiplier. Tests in this module verify the
non-anti-commuting behavior (it is automatic for swap-permutation
constructions and is a consistency check, not a regression).

Conventions
-----------
* Move semantics: a move is ``(from_sq, to_sq)`` where each is a
  4-tuple ``(x, y, z, w)`` with ``0 <= component <= 7``. Linear-square
  indices (``0..4095``) are also accepted via the
  :func:`chess_spectral_4d.move_history.coord_to_sq` packing.
* Capture handling: B1 only ships non-capture moves. Calling
  :func:`u_move_a1` with ``assume_non_capture=False`` and a move that
  captures a piece raises ``NotImplementedError`` pointing at B5
  (where the partial-isometry / rank-1-update path lands).
* Output dtype: ``complex128`` throughout, matching :mod:`qm_4d`.
* Sparsity: returns ``scipy.sparse.csr_matrix``. The expected nnz of
  ``U_a1`` is bounded by ``P_A1.nnz`` (sandwich does not add nonzeros
  beyond P_A1's support).

Public API
----------
``u_move_a1(state_pre, move, *, assume_non_capture=True)``
    Build the A_1-channel unitary lift for a non-capture move.
``apply_move_qm(state, move, *, optional_return_unitary=False)``
    Bridge-surface stub. Currently raises ``NotImplementedError`` for
    everything except the A_1 channel; full implementation lands in
    v1.5 with B2-B5.
"""
from __future__ import annotations

from typing import Mapping, Optional, Tuple, Union

import math

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from chess_spectral import qm_4d as _qm4
from chess_spectral import tables_4d as _t4

# Re-export the A_1 channel constants for direct module use.
N_SQUARES: int = _t4.N_SQUARES                  # 4096
N_CHANNELS: int = _qm4.N_CHANNELS                # 11
CHANNEL_DIM: int = _qm4.CHANNEL_DIM              # 4096
ENCODING_DIM: int = _qm4.ENCODING_DIM            # 45056

# Channel index of the A_1 (totally-symmetric / trivial irrep) block.
A1_CHANNEL_IDX: int = 0


# ---- Type aliases ---------------------------------------------------

# Coords accepted for move endpoints. Either a 4-tuple of ints in
# [0, 7] (the chess_spectral_4d.move_history.Coord4D form) or a linear
# square index in [0, 4096). Both are normalised to a linear index
# internally via :func:`_to_linear_idx`.
SquareLike = Union[int, Tuple[int, int, int, int]]


# ---- Private helpers ------------------------------------------------


def _to_linear_idx(sq: SquareLike) -> int:
    """Normalise a square to its linear index in [0, 4096).

    Accepts either ``int`` (already linear) or a 4-tuple
    ``(x, y, z, w)`` with each component in ``[0, 7]``.
    """
    if isinstance(sq, int):
        if not 0 <= sq < N_SQUARES:
            raise ValueError(
                f"linear square index {sq} out of range [0, {N_SQUARES})"
            )
        return sq
    if isinstance(sq, tuple) and len(sq) == 4:
        return int(_t4.sq4(*sq))
    raise TypeError(
        f"move endpoint must be int or 4-tuple, got "
        f"{type(sq).__name__}: {sq!r}"
    )


def _coerce_move(move) -> Tuple[int, int]:
    """Accept a (from, to) tuple or a Move4D instance and return
    ``(from_idx, to_idx)`` as linear-square integers.

    Move4D import is deferred so this module does not introduce a
    package import cycle when chess_spectral_4d itself does not
    depend on qm_4d_dynamics.
    """
    # Move4D-like (duck-type on the .from_sq / .to_sq attributes used
    # by chess_spectral_4d.move_history).
    from_sq = getattr(move, "from_sq", None)
    to_sq = getattr(move, "to_sq", None)
    if from_sq is not None and to_sq is not None:
        return _to_linear_idx(from_sq), _to_linear_idx(to_sq)
    # 2-tuple form
    if isinstance(move, tuple) and len(move) == 2:
        return _to_linear_idx(move[0]), _to_linear_idx(move[1])
    raise TypeError(
        f"move must be a (from_sq, to_sq) tuple or have .from_sq / "
        f".to_sq attributes; got {type(move).__name__}: {move!r}"
    )


def _is_capture(state_pre, from_idx: int, to_idx: int) -> bool:
    """True iff there is a piece on the destination square in
    ``state_pre`` (i.e., a capture).

    ``state_pre`` is accepted as either a position dict (``{sq: piece}``)
    or a :class:`chess_spectral_4d.move_history.GameState4D`-like
    object exposing a ``.position`` attribute.
    """
    pos = getattr(state_pre, "position", state_pre)
    if not isinstance(pos, Mapping):
        raise TypeError(
            f"state_pre must be a position dict or have a .position "
            f"attribute; got {type(state_pre).__name__}"
        )
    return to_idx in pos


def _build_swap_4096(from_idx: int, to_idx: int) -> csr_matrix:
    """4096x4096 sparse permutation matrix that swaps the basis
    vectors at ``from_idx`` and ``to_idx`` and is identity elsewhere.

    ``from_idx == to_idx`` returns the identity (a no-op move; we
    guard against this explicitly so degenerate moves don't generate
    surprising structure).
    """
    if from_idx == to_idx:
        return sp.eye(N_SQUARES, format="csr", dtype=np.complex128)
    rows = np.arange(N_SQUARES, dtype=np.int64).copy()
    rows[from_idx] = to_idx
    rows[to_idx] = from_idx
    cols = np.arange(N_SQUARES, dtype=np.int64)
    data = np.ones(N_SQUARES, dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)), shape=(N_SQUARES, N_SQUARES),
    )


def _get_P_A1() -> csr_matrix:
    """Cached A_1 orbit-projection matrix on C^4096, complex128.

    Wraps ``encoder_4d._load_tables()`` so we share P_A1 with the
    encoder (avoiding a second 695296-nnz construction). Casts to
    ``complex128`` and ensures CSR format.
    """
    # Lazy import to keep the module-level import surface minimal.
    from chess_spectral import encoder_4d as _enc4
    P = _enc4._load_tables()['P_A1']
    if P.dtype != np.complex128:
        P = P.astype(np.complex128)
    if not sp.isspmatrix_csr(P):
        P = P.tocsr()
    return P


# ---- A_1 channel phase factor (ADR-001 §3.1) ------------------------


def _channel_phase_a1(
    from_idx: int,  # noqa: ARG001  (signature parity with B2-B5)
    to_idx: int,    # noqa: ARG001
) -> complex:
    """Return the ADR-001 §3.1 channel phase factor for A_1.

    For the A_1 channel (channel 0, trivial irrep), the phase is
    identically ``e^{i * 0} = 1`` for every move. The signature still
    accepts the move endpoints because the same helper shape will be
    reused for STD4_X/Y/Z/W (B3a) where the phase depends on the
    coordinate displacement, and for FIB_SYM_* / FA_PAWN_* / FD_DIAG
    later. Keeping the call site uniform avoids special-casing A_1.
    """
    theta = 0.0  # ADR-001 §3.1 row "A1"
    return complex(math.cos(theta), math.sin(theta))  # exactly 1+0j


# ---- Public: u_move_a1 ----------------------------------------------


def u_move_a1(
    state_pre,
    move,
    *,
    assume_non_capture: bool = True,
) -> csr_matrix:
    """Build the A_1-channel move unitary as a 4096x4096 sparse matrix.

    Construction (per ADR-001 §3.1 + ADR-003 §3.1, projector-sandwich
    form clarified by the B1 user-spec):

      1. Build ``U_swap = swap(from_idx <-> to_idx)`` on ``C^4096``.
      2. Multiply by the ADR-001 phase factor for A_1 (= 1.0).
      3. Wrap in the P_A1 projector sandwich:
         ``U_a1 = P_A1 @ U_swap @ P_A1``
         (P_A1 is real symmetric so ``P_A1.conj().T == P_A1``;
         the sandwich is the natural sub-unitary onto ``range(P_A1)``).

    The resulting ``U_a1`` is **sub-unitary** on the full ``C^4096``:
    zero outside ``range(P_A1)`` and unitary within when the
    underlying swap commutes with P_A1 (i.e., for same-B_4-orbit
    swaps). For cross-orbit chess moves the sandwich is contractive
    (``||U_a1||_op <= 1``) but does not satisfy
    ``U_a1.conj().T @ U_a1 == P_A1`` exactly — see the module
    docstring's "Phase 3.5 Probe-Result Amendments" section.

    Parameters
    ----------
    state_pre
        Pre-move state. Accepted forms:

        * Position dict ``{sq_index: piece_value}`` (the encoder's
          input schema — see :mod:`chess_spectral.encoder_4d`).
        * Object with ``.position`` attribute holding such a dict
          (e.g., :class:`chess_spectral_4d.GameState4D`).

        Used here only to detect whether the move is a capture; the
        A_1 lift's structure depends on the move endpoints alone (not
        on the rest of the position).
    move
        Move endpoints. Accepted forms:

        * 2-tuple ``(from_sq, to_sq)`` where each endpoint is either
          a linear int in ``[0, 4096)`` or a 4-tuple ``(x, y, z, w)``.
        * :class:`chess_spectral_4d.move_history.Move4D` (or any
          object with ``.from_sq`` / ``.to_sq`` attributes in the
          accepted endpoint forms).
    assume_non_capture
        If ``True`` (default), the caller asserts the move is a
        non-capture; capture detection is performed only for the safety
        check in capture-mode (when ``False``). If ``False`` and the
        move IS a capture, ``NotImplementedError`` is raised pointing
        at the B5 milestone (capture handling).

    Returns
    -------
    csr_matrix of shape ``(4096, 4096)``, dtype ``complex128``.

    Raises
    ------
    NotImplementedError
        If ``assume_non_capture=False`` and the move captures a piece.
        Capture handling for the A_1 channel is deferred to Phase 4
        milestone B5 (per ADR-002 capture renormalization +
        ADR-003 §3.1's note that A_1's swap "maps `e_d` to `e_d` —
        destination square's value updates from `sig_captured` to
        `sig_pre[o]`", which is a non-unitary partial-isometry case
        that needs the B5 framework).
    TypeError
        If ``state_pre`` or ``move`` cannot be normalised to the
        expected forms.
    """
    from_idx, to_idx = _coerce_move(move)

    if not assume_non_capture:
        # Verify the caller's claim. assume_non_capture=True (default)
        # bypasses this check and trusts the caller; this is the fast
        # path the bridge surface uses when move legality has already
        # been validated upstream.
        if _is_capture(state_pre, from_idx, to_idx):
            raise NotImplementedError(
                "Capture moves on the A_1 channel are deferred to "
                "Phase 4 milestone B5 (capture handling). See ADR-002 "
                "(time-evolution semantics + capture renormalization) "
                "and ADR-003 §3.1 (the A_1 capture path is a "
                "partial-isometry — destination basis vector keeps "
                "its index but the source signal value replaces the "
                "captured signal value). B1 ships non-capture moves "
                "only; pass assume_non_capture=True if you have "
                "already filtered captures upstream."
            )

    # Step 1: 4096-dim swap (the underlying basis permutation).
    U_swap = _build_swap_4096(from_idx, to_idx)

    # Step 2: ADR-001 phase factor (= 1.0+0j for A_1 by §3.1).
    # Kept as an explicit multiplication because B2-B5 will reuse this
    # exact code structure with non-trivial phases for the other
    # channels.
    phase = _channel_phase_a1(from_idx, to_idx)
    if phase != 1.0 + 0.0j:
        # Defensive: A_1 phase is mathematically exactly 1, but the
        # multiplication path is left in for code-shape parity with
        # B2-B5. If float arithmetic ever produces a non-unit phase
        # for A_1, escalate (it would indicate a bug in the irrep
        # bookkeeping).
        U_swap = phase * U_swap

    # Step 3: P_A1 projector sandwich. P_A1 is real symmetric, so the
    # conjugate-transpose simplifies to P_A1 itself.
    P_A1 = _get_P_A1()
    U_a1 = (P_A1 @ U_swap @ P_A1).tocsr()

    # Ensure CSR + complex128 invariant for downstream code.
    if U_a1.dtype != np.complex128:
        U_a1 = U_a1.astype(np.complex128)
    return U_a1


# ---- Phase 4 B2: free Hamiltonian H_0 = -Δ_{P_8^4} -----------------
#
# Per ADR-002 §3.1 (Zeno-style Option A), the QM module's free
# Hamiltonian is ``H_0 = -Δ`` where Δ is the 4D path-graph Laplacian
# ``L_{P_8} ⊕ L_{P_8} ⊕ L_{P_8} ⊕ L_{P_8}`` (Kronecker sum of four
# 8-vertex path-graph 1D Laplacians). H_0 acts on a single 4096-dim
# channel block; the full 45 056-dim space evolves as ``I_11 ⊗ H_0``,
# i.e. the eleven 4096-blocks evolve independently under the same H_0.
#
# Sign convention: the encoder's identity in Pre-flight 3 is in terms
# of Δ (not -Δ), and the reported P_8 1D spectrum
# ``[0, 0.15224, 0.58579, 1.23463, 2.0, 2.76537, 3.41421, 3.84776]`` is
# for Δ. H_0 = -Δ has the negation of the Kron-sum spectrum, i.e.
# eigenvalues in ``[-15.39103, ..., 0]`` on C^4096.

# Module-level cache. ``None`` means "not yet built"; first call to
# :func:`evolve_under_h0` (or to :data:`H_FREE_4D` via __getattr__)
# triggers :func:`_build_h_free_4d` and caches the result here.
_H_FREE_4D: Optional[csr_matrix] = None


def _l8_path_laplacian() -> csr_matrix:
    """Return the 8x8 sparse 1D path-graph Laplacian (P_8) as
    ``complex128`` CSR.

    Tridiagonal: degree on the diagonal (1 at endpoints, 2 interior),
    -1 on the super- and sub-diagonals. This is exactly
    :func:`tables_4d.p8_laplacian` cast to sparse complex128.
    """
    n = _t4.BOARD_SIDE  # 8
    # Build via three diagonals so the result is exactly tridiagonal
    # without any explicit zero entries.
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


def _build_h_free_4d() -> csr_matrix:
    """Build ``H_0 = -Δ_{P_8^4}`` as a 4096x4096 sparse matrix.

    Δ is the 4D path-graph Laplacian — Kronecker sum of four copies of
    the 1D 8-node path-graph Laplacian L_8. ``H_0 = -Δ`` is the standard
    free-particle kinetic energy on the lattice; its eigenvalues are
    non-positive (the spectrum of Δ is ``[0, 8 · 3.84776] ≈ [0, 15.39]``,
    so H_0's spectrum is ``[-15.39, 0]``).

    The construction here mirrors
    :func:`research/spectral_identity_4d_verification.kron_sum_laplacian_sparse`
    with ``dim=4`` and uses :func:`scipy.sparse.kron` for each tensor
    product. We do **not** use :func:`tables_4d.laplacian_4d` because
    that path goes through a 4096-square adjacency matrix; the direct
    Kron-sum form is symbolically clearer and exactly matches the
    Pre-flight 3 identity.

    Sign: returns ``-Δ`` (Hermitian, negative-semidefinite). The
    spectrum is the negation of :func:`tables_4d.kron_sum4_eigvals`'s
    output on the P_8 1D eigenvalues.

    Returns
    -------
    csr_matrix of shape ``(4096, 4096)``, dtype ``complex128``.
        Hermitian (real-symmetric, with zero imaginary part). Sparse
        with the Δ structure (each interior site has 9 neighbors,
        including itself).

    Notes
    -----
    Module-level singleton: the result is cached in :data:`_H_FREE_4D`
    on first call so repeated invocations of :func:`evolve_under_h0`
    pay the construction cost only once.
    """
    L1 = _l8_path_laplacian()                   # 8x8 sparse
    n = L1.shape[0]
    eye = sp.eye(n, format="csr", dtype=np.complex128)

    # Δ = sum_{axis in {0,1,2,3}} I ⊗ ... ⊗ L (axis) ⊗ ... ⊗ I
    delta: Optional[csr_matrix] = None
    for axis in range(4):
        factors = [eye] * 4
        factors[axis] = L1
        T = factors[0]
        for f in factors[1:]:
            T = sp.kron(T, f, format="csr")
        delta = T if delta is None else (delta + T)
    assert delta is not None
    delta = delta.tocsr()

    # H_0 = -Δ. The negation preserves sparsity pattern and dtype.
    H0 = (-delta).tocsr()
    if H0.dtype != np.complex128:
        H0 = H0.astype(np.complex128)
    return H0


def _get_h_free_4d() -> csr_matrix:
    """Cached accessor for :data:`H_FREE_4D` — builds on first call."""
    global _H_FREE_4D
    if _H_FREE_4D is None:
        _H_FREE_4D = _build_h_free_4d()
    return _H_FREE_4D


def _channel_offset(channel: str) -> Tuple[int, int]:
    """Map a channel name to its ``(start, end)`` slice into the
    45 056-dim full encoder vector.

    The 11 channel names (in order) are:
    ``A1, STD4_X, STD4_Y, STD4_Z, STD4_W, FIB_SYM_1, FIB_SYM_2,
    FIB_SYM_3, FA_PAWN_W, FA_PAWN_Y, FD_DIAG``.

    Source of truth: :data:`chess_spectral.encoder_4d.CHANNELS_4D`.
    """
    # Lazy import to avoid a top-of-file cycle.
    from chess_spectral import encoder_4d as _enc4
    for name, offset in _enc4.CHANNELS_4D:
        if name == channel:
            return int(offset), int(offset + CHANNEL_DIM)
    valid = [name for name, _ in _enc4.CHANNELS_4D]
    raise ValueError(
        f"unknown channel name {channel!r}; expected one of {valid}"
    )


def evolve_under_h0(
    psi: np.ndarray,
    t: float,
    *,
    channel: Optional[str] = None,
) -> np.ndarray:
    """Evolve ``psi`` under ``U(t) = exp(-i H_0 t)`` for time ``t``.

    Implements ADR-002 §3.1's continuous-time evolution between move
    boundaries. The operator H_0 = -Δ_{P_8^4} is Hermitian and
    real-symmetric (so ``-i H_0 t`` is anti-Hermitian and U(t) is
    unitary). Norm and ``<H_0>`` are preserved exactly up to the
    numerical precision of :func:`scipy.sparse.linalg.expm_multiply`
    (Krylov subspace; typically 1e-12 or better for the parameters
    used in M14.x).

    Parameters
    ----------
    psi : ndarray
        State vector. Two accepted shapes:

        * ``(4096,)``: a single channel block (e.g., the A_1 sub-vector).
          Evolves under H_0 directly.
        * ``(45056,)``: the full 11-channel encoder vector. By default
          all 11 blocks are evolved independently under the same H_0
          (since H_0 acts on the 4096-dim mode space, not the
          channel-typed space — equivalently, the full Hamiltonian on
          C^45056 is ``I_11 ⊗ H_0``). If ``channel`` is provided, only
          that block is evolved; the other ten are returned unchanged.

        Dtype is cast to ``complex128``.
    t : float
        Real evolution time. ``t == 0`` is a no-op (returns a copy of
        ``psi``). Negative ``t`` evolves backward in time, which is
        well-defined because U(t) is unitary and ``U(-t) = U(t)^†``.
    channel : str, optional
        One of the 11 channel names
        (``'A1'``, ``'STD4_X'``, ..., ``'FD_DIAG'``). If given, ``psi``
        must be the full 45 056-dim vector and only the named channel's
        4096-block is evolved; the other 10 are copied through. Useful
        for animating evolution per channel (M14.2 phase-as-color render
        of a single channel marginal). Raises if ``psi`` is the
        4096-dim shape.

    Returns
    -------
    ndarray of the same shape and dtype (``complex128``) as ``psi``.

    Raises
    ------
    ValueError
        If ``psi`` is not 1-D or has a shape other than ``(4096,)`` or
        ``(45056,)``; or if ``channel`` is given with a ``(4096,)``
        ``psi`` (ambiguous — the caller should drop the ``channel`` arg
        or pass the full vector); or if ``channel`` is not a recognized
        name.

    Notes
    -----
    Performance: :func:`scipy.sparse.linalg.expm_multiply` runs in
    milliseconds for typical M14.3 frames (``|t| < 0.2``,
    ``‖H_0‖ ≤ 16``, Krylov dim < 30). The full 45 056-dim case is just
    11 sequential 4096-dim calls; total cost stays within the 60 FPS
    budget on the dev box.

    Eigenbasis-diagonal optimization (ADR-002 §6.1): per Pre-flight 3,
    the encoder basis is the simultaneous eigenbasis of ``(Δ, B_4
    commutant)``, so a future v1.6+ optimization could replace
    ``expm_multiply`` with one matvec into the eigenbasis + an
    elementwise phase multiplication + one matvec out. Deferred until
    profiling shows ``evolve_under_h0`` is a hot path.
    """
    psi_arr = np.ascontiguousarray(psi)
    if psi_arr.ndim != 1:
        raise ValueError(
            f"psi must be 1-D; got shape {psi_arr.shape}"
        )
    if psi_arr.dtype != np.complex128:
        psi_arr = psi_arr.astype(np.complex128)

    # t == 0 is a no-op. Return a copy so callers don't have to worry
    # about whether the result aliases the input.
    if t == 0.0:
        return psi_arr.copy()

    H0 = _get_h_free_4d()
    # ``-1j * t * H0`` is anti-Hermitian; expm_multiply integrates one
    # column at a time. Build it as the product so scipy's pre-scaling
    # logic sees a single sparse operator.
    A = (-1j * float(t)) * H0

    # Single 4096-dim block path
    if psi_arr.shape == (CHANNEL_DIM,):
        if channel is not None:
            raise ValueError(
                "channel argument is only meaningful for full 45 056-dim "
                "psi vectors; got a single 4096-dim block. Drop the "
                "channel argument or pass the full encoder vector."
            )
        return np.asarray(expm_multiply(A, psi_arr), dtype=np.complex128)

    # Full 45 056-dim path
    if psi_arr.shape == (ENCODING_DIM,):
        out = psi_arr.copy()
        if channel is None:
            # Evolve all 11 blocks under the same H_0. expm_multiply has
            # a per-call setup cost (Krylov parameter selection); for
            # 11 blocks at typical t we still finish in a few hundred ms.
            for c in range(N_CHANNELS):
                start = c * CHANNEL_DIM
                end = start + CHANNEL_DIM
                out[start:end] = expm_multiply(A, psi_arr[start:end])
            return out
        # Channel-restricted: only the named block evolves.
        start, end = _channel_offset(channel)
        out[start:end] = expm_multiply(A, psi_arr[start:end])
        return out

    raise ValueError(
        f"psi must have shape ({CHANNEL_DIM},) or ({ENCODING_DIM},); "
        f"got {psi_arr.shape}"
    )


# Module-level lazy attribute access for ``H_FREE_4D``. We expose the
# cached singleton via __getattr__ so importers pay zero construction
# cost on import; the matrix is built only when first accessed (either
# directly via ``qm_4d_dynamics.H_FREE_4D`` or indirectly via
# :func:`evolve_under_h0`).

def __getattr__(name: str):
    if name == "H_FREE_4D":
        return _get_h_free_4d()
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


# ---- Bridge-surface re-export ---------------------------------------
#
# The §17.1 ``applyMoveQm`` lives in :mod:`chess_spectral.qm_4d_bridge`
# (separation: this module holds the per-channel math; the bridge
# module holds the consumer-facing assembly). Re-exported here for
# convenience so callers can write ``from chess_spectral.qm_4d_dynamics
# import apply_move_qm`` if they prefer the dynamics namespace, but
# the canonical home is the bridge module.

from chess_spectral.qm_4d_bridge import apply_move_qm  # noqa: E402, F401


# ---- Public API list ------------------------------------------------

__all__ = [
    # Constants
    'N_SQUARES', 'N_CHANNELS', 'CHANNEL_DIM', 'ENCODING_DIM',
    'A1_CHANNEL_IDX',
    # Type aliases
    'SquareLike',
    # Public builders
    'u_move_a1',
    # B2 free Hamiltonian + Zeno evolution
    'evolve_under_h0',
    # NOTE: H_FREE_4D is intentionally NOT in __all__ because it's a
    # lazy module attribute exposed via __getattr__; ``from
    # chess_spectral.qm_4d_dynamics import *`` would force its
    # construction at import time, which we want to avoid. Callers can
    # still access it via ``qm_4d_dynamics.H_FREE_4D``.
    # Bridge stub (canonical home: chess_spectral.qm_4d_bridge)
    'apply_move_qm',
]
