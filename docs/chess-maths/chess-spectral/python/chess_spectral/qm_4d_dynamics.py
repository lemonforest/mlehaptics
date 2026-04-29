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

from typing import Mapping, Tuple, Union

import math

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix

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
    # Bridge stub (canonical home: chess_spectral.qm_4d_bridge)
    'apply_move_qm',
]
