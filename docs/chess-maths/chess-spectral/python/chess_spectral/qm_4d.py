"""chess_spectral.qm_4d - quantum-mechanical front-end for the 4D
spectral encoder.

Wraps the existing 45 056-dim float32 encoder output as a quantum
state psi in C^45056, exposes Hermitian piece-reach observables, the
11-channel projection-valued measure, and Born-rule helpers.

This is the KINEMATIC-only layer (Phase 2 / Track A). Full
move-as-unitary dynamics live in Track B
(:mod:`chess_spectral.qm_4d_dynamics`). As of Phase 4 milestone B1,
that sibling module ships the A_1-channel move unitary via
``u_move_a1`` and a ``apply_move_qm`` bridge-surface stub; the
remaining 10 channels (STD4_*, FA_PAWN_*, FIB_SYM_*, FD_DIAG) land in
B2-B5 per ADR-003's tiered plan.

Design references:
  - Cross-disciplinary motivation:
    docs/chess-maths/chess_spectral_research_notebook.md sec 15
  - Pre-flight findings constraining this implementation:
    docs/chess-maths/chess_spectral_4d_notebook.md
        sec qm_4d-pre-flight-findings

Pre-flight constraints (from the 2026-04-29 audit):
  Pre-flight 1 -- encode_4d is invariant under (central inversion +
    color flip) Z_2 on the synthetic anti-podal-king + diagonal-piece
    family. Real-game corpora are 100% injective. The QM module
    resolves the degeneracy by taking the side-to-move bit and
    multiplying psi by +-1 accordingly. Equivalently psi lives on
    `configurations / Z_2`.
  Pre-flight 2 -- the non-pawn `P_*4` predicates lift to real-symmetric
    Hermitian matrices on C^4096 with integer spectra in [-4, 28] for
    rook (cross-checked on knight). Pawn observables break Hermiticity
    under the standard inner product -- deferred to Track B.
  Pre-flight 3 -- the encoder's 4096 modes ARE the simultaneous
    eigenbasis of (Delta = P_8 box P_8 box P_8 box P_8) and the B_4
    commutant. Used in research/qm_spectral_identity_demo.py.

Public API (kinematic only):
  state_to_psi(state, side_to_move) -> psi : C^45056
  inner_product(psi1, psi2) -> complex
  norm(psi) -> float
  expectation(O, psi) -> float
  is_normalized(psi, tol=1e-10) -> bool
  is_unitary(U, tol=1e-10) -> bool
  is_hermitian(H, tol=1e-10) -> bool
  b4_unitary_rep_4096(g) -> sparse unitary on C^4096 (one channel)
  b4_unitary_rep_full(g)  -> sparse unitary on C^45056 (all channels)
  channel_projector(c) -> sparse projector onto channel c (0..10)
  prob_channel(psi, c) -> Born-rule probability for channel c
  measure_channel_distribution(psi) -> ndarray[11] of probabilities
  H_rook_4, H_bishop_4, H_queen_4, H_king_4, H_knight_4
        -> sparse Hermitians on C^4096 (lazily cached at first access)
  build_H_piece_4(piece) -> rebuild any of the above from scratch
  H_pawn_w_4, H_pawn_y_4 -> raise NotImplementedError (Track B)

Conventions:
  - dtype is complex128 throughout (psi, sparse operators).
  - The 4096-dim factor uses sq4 ordering (matches the encoder's
    channel layout). Equivalent to the predicate-form ordering up
    to a permutation of basis vectors.
  - The "full" 45056-dim space is the direct sum of 11 copies of
    C^4096; channel-restricted operators act as I_11 (x) O_4096
    when lifted (or as a block-diagonal selection projector).
  - This module imports from chess_spectral.encoder_4d and
    chess_spectral.tables_4d only; no modifications to those.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix

from chess_spectral import encoder_4d as _enc4
from chess_spectral import tables_4d as _t4


# ---- Dimension constants --------------------------------------------

# Channel sizes mirror the encoder layout. Source of truth lives in
# encoder_4d; we re-export the values here for direct module use and
# defensively assert they match.
N_CHANNELS: int = _enc4.N_CHANNELS_4D            # 11
CHANNEL_DIM: int = _enc4.CHANNEL_DIM             # 4096
ENCODING_DIM: int = _enc4.ENCODING_DIM_4D        # 45056

assert CHANNEL_DIM * N_CHANNELS == ENCODING_DIM, (
    "Channel layout mismatch: CHANNEL_DIM * N_CHANNELS != ENCODING_DIM "
    f"({CHANNEL_DIM} * {N_CHANNELS} != {ENCODING_DIM})"
)


# ---- State construction ---------------------------------------------


def state_to_psi(position: Dict[int, _enc4.PieceValue],
                 side_to_move: bool) -> np.ndarray:
    """Encode a chess position to a normalized complex amplitude
    psi in C^ENCODING_DIM = C^45056.

    Z_2 sector convention
    ---------------------
    Per ADR-004 §3.2 (formalized) and the Phase 3.5 amendment to §3.4
    (PHASE_3_5_PROBE_RESULTS.md, Probe 4), this function is the
    **canonical Z_2 sector-flip mechanism** for the QM extension. The
    encoded vector is multiplied by:

      * +1 for ``side_to_move=True``  (white-to-move; H_+ sector)
      * -1 for ``side_to_move=False`` (black-to-move; H_- sector)

    Equivalently, ``state_to_psi(state, white) == -state_to_psi(state,
    black)`` exactly (sign-flip implementation, not a unitary
    rotation). The Z_2 grading thus lives at the **state-vector
    level**, NOT at the operator level: per-channel U_move operators
    (B1's `u_move_a1`, B3a's `u_move_std4`, B3b's `u_move_fa_pawn`)
    are **not** required to formally anti-commute with J_op (the
    central-inversion permutation matrix). This was the rejected
    ADR-004 §3.4 original requirement, killed by Probe 4's empirical
    finding that ``{U_move, J_op} = 0`` is mathematically impossible
    for the swap-permutation construction.

    Test surface: the positive-side complement (state_to_psi IS the
    sector-flip mechanism) lives in
    :mod:`tests.test_qm_4d_z2_grading`; the negative-side complement
    (per-channel U_move does NOT operator-anti-commute with J_op) lives
    in the corresponding ``test_b1/_b3a/_b3b_no_anti_commutation_with_J_op``
    tests in the per-channel B1/B3a/B3b test modules.

    Parameters
    ----------
    position : dict {sq4_index -> piece value}
        Same schema as encoder_4d.encode_4d. Pawn values may be either
        a tuple ('P'/'p', axis) or a legacy single char (legacy emits
        a DeprecationWarning from encode_4d).
    side_to_move : bool
        True = white to move, False = black to move. See "Z_2 sector
        convention" above. The (central inversion + color flip)
        involution that breaks encoder injectivity on synthetic
        anti-podal-king configurations is resolved by the side-to-move
        parity per Pre-flight 1.

    Returns
    -------
    psi : ndarray[complex128, (45056,)]
        L2-normalized amplitude. ||psi||_2 == 1 (within float
        rounding). For an empty position the encoder returns the zero
        vector; we return the same zero vector as a non-physical
        sentinel and warn -- see note below.

    Note: empty positions encode to the zero vector and cannot be
    normalized. `state_to_psi({}, ...)` returns the zero vector and
    `is_normalized` will return False; callers requiring physical
    states should reject empty positions upstream.
    """
    enc = _enc4.encode_4d(position).astype(np.complex128)
    if not side_to_move:
        enc = -enc
    n = float(np.linalg.norm(enc))
    if n == 0.0:
        # Cannot normalize -- empty / cancelling position. Return the
        # zero vector unchanged (callers can detect via is_normalized).
        return enc
    return enc / n


# ---- Inner product / norm / expectation -----------------------------


def inner_product(a: np.ndarray, b: np.ndarray) -> complex:
    """Hermitian inner product <a|b> = sum_i a_i^* b_i.

    Uses numpy.vdot which conjugates the first argument. Returns
    a complex scalar.
    """
    if a.shape != b.shape:
        raise ValueError(
            f"inner_product: shape mismatch {a.shape} vs {b.shape}"
        )
    return complex(np.vdot(a, b))


def norm(psi: np.ndarray) -> float:
    """L2 norm sqrt(<psi|psi>). Returns a real non-negative float."""
    return float(np.linalg.norm(psi))


def expectation(O: csr_matrix | np.ndarray, psi: np.ndarray) -> float:
    """Expectation value <O> = <psi|O|psi> for a Hermitian operator O.

    Returns the real part (the imaginary part should be zero up to
    floating-point error if O is Hermitian and psi is well-formed).
    No Hermiticity check is performed here -- callers should validate
    O via :func:`is_hermitian` if needed.

    Accepts either a scipy.sparse matrix or a dense ndarray.
    """
    if sp.issparse(O):
        Opsi = O @ psi
    else:
        Opsi = np.asarray(O) @ psi
    val = np.vdot(psi, Opsi)
    return float(val.real)


# ---- Validation helpers ---------------------------------------------


def is_normalized(psi: np.ndarray, tol: float = 1e-10) -> bool:
    """True iff |||psi|| - 1| < tol."""
    return abs(norm(psi) - 1.0) < tol


def is_hermitian(H: csr_matrix | np.ndarray, tol: float = 1e-10) -> bool:
    """True iff H == H^dagger within tol (max element-wise abs diff).

    Works for both scipy.sparse and dense arrays.
    """
    if sp.issparse(H):
        diff = (H - H.conj().T)
        # max abs entry. Sparse matrices: use .data; if data empty, 0.
        if diff.nnz == 0:
            return True
        return float(np.max(np.abs(diff.data))) < tol
    H = np.asarray(H)
    return float(np.max(np.abs(H - H.conj().T))) < tol


def is_unitary(U: csr_matrix | np.ndarray, tol: float = 1e-10) -> bool:
    """True iff U U^dagger == I within tol (max element-wise abs).

    Works for both scipy.sparse (returns sparse identity) and dense
    arrays.
    """
    if sp.issparse(U):
        n = U.shape[0]
        prod = (U @ U.conj().T) - sp.eye(n, format="csr",
                                          dtype=U.dtype)
        if prod.nnz == 0:
            return True
        return float(np.max(np.abs(prod.data))) < tol
    U = np.asarray(U)
    n = U.shape[0]
    return float(np.max(np.abs(U @ U.conj().T - np.eye(n)))) < tol


# ---- B_4 unitary representation -------------------------------------

# Cache for the 4096-dim B_4 unitaries. Keyed by group element (g is a
# (perm, signs) tuple). Built lazily as callers request them.
_B4_UNITARY_CACHE: Dict[object, csr_matrix] = {}


def b4_unitary_rep_4096(g: _t4.GroupElem) -> csr_matrix:
    """Return the 4096x4096 sparse unitary representing g in C^4096.

    Wraps :func:`tables_4d.b4_permutation_matrix` and casts to
    complex128. Real orthogonal permutation matrices are unitary
    over C; the cast keeps the dtype consistent with the rest of
    the QM module (psi is complex128).

    Caches results per group element so repeated calls are O(1).
    """
    key = (tuple(g[0]), tuple(g[1]))
    if key in _B4_UNITARY_CACHE:
        return _B4_UNITARY_CACHE[key]
    P = _t4.b4_permutation_matrix(g).astype(np.complex128)
    P = P.tocsr()
    _B4_UNITARY_CACHE[key] = P
    return P


def b4_unitary_rep_full(g: _t4.GroupElem) -> csr_matrix:
    """Return the 45056x45056 sparse unitary representing g on the
    full encoder space. This is I_11 (x) U_4096(g) -- the same B_4
    action applied independently to each of the 11 channels.

    Built by Kronecker-ing an identity in the channel slot. Returns
    a CSR sparse matrix with complex128 dtype.
    """
    U_block = b4_unitary_rep_4096(g)
    I_chan = sp.eye(N_CHANNELS, format="csr", dtype=np.complex128)
    return sp.kron(I_chan, U_block, format="csr")


# ---- Channel projection-valued measure ------------------------------


def channel_projector(c: int) -> csr_matrix:
    """Sparse 45056x45056 projector P_c onto channel c (0..10).

    P_c is diagonal with 1's on rows [c*4096 : (c+1)*4096) and 0
    elsewhere. The 11 projectors form a complete orthogonal PVM:
    sum_c P_c == I_45056 and P_c P_d == delta_{cd} P_c.
    """
    if not 0 <= c < N_CHANNELS:
        raise ValueError(f"channel index {c} out of range [0, {N_CHANNELS})")
    diag = np.zeros(ENCODING_DIM, dtype=np.complex128)
    start = c * CHANNEL_DIM
    diag[start:start + CHANNEL_DIM] = 1.0
    return sp.diags(diag, format="csr", dtype=np.complex128)


def prob_channel(psi: np.ndarray, c: int) -> float:
    """Born-rule probability of measuring psi in channel c.

    Equivalent to <psi|P_c|psi> = ||segment of psi on channel c||^2.
    Skips materialising the projector for speed -- just slices and
    sums |psi|^2 on the relevant block.
    """
    if not 0 <= c < N_CHANNELS:
        raise ValueError(f"channel index {c} out of range [0, {N_CHANNELS})")
    start = c * CHANNEL_DIM
    block = psi[start:start + CHANNEL_DIM]
    # |psi_block|^2 summed -- works for complex128 by .conj() product.
    return float(np.vdot(block, block).real)


def measure_channel_distribution(psi: np.ndarray) -> np.ndarray:
    """Born-rule probabilities for all 11 channels.

    Returns a real ndarray of shape (11,). For a normalized psi the
    sum is 1.0 within float rounding; the caller can verify via
    `np.allclose(probs.sum(), 1.0)`.
    """
    probs = np.empty(N_CHANNELS, dtype=np.float64)
    for c in range(N_CHANNELS):
        start = c * CHANNEL_DIM
        block = psi[start:start + CHANNEL_DIM]
        probs[c] = float(np.vdot(block, block).real)
    return probs


# ---- Hermitian piece observables ------------------------------------

# Map from piece char to the index in tables_4d's piece_adjacencies_4d
# return list. Source of truth: tables_4d._PIECE_TARGETS_4D order is
# (N, B, R, Q, K).
_PIECE_TO_ADJ_IDX: Dict[str, int] = {
    'N': 0,
    'B': 1,
    'R': 2,
    'Q': 3,
    'K': 4,
}


# Cache of materialised Hermitians; built once on first access.
_H_PIECE_CACHE: Dict[str, csr_matrix] = {}


# Allowed pieces for the Hermitian observable lift. Excludes pawns
# (directed push breaks Hermiticity -- see Pre-flight 2). Track B
# will introduce pseudo-Hermitian / PT-symmetric pawn observables
# under a non-trivial metric eta.
_HERMITIAN_PIECES = frozenset({'N', 'B', 'R', 'Q', 'K'})

# Pawn keys that should raise NotImplementedError with an informative
# message pointing to Track B.
_PAWN_HERMITIAN_KEYS = frozenset({'P', 'p', 'P_w', 'P_y', 'p_w', 'p_y'})


def build_H_piece_4(piece: str) -> csr_matrix:
    """Build the Hermitian operator H_piece on C^4096 from the
    chess-symmetric reach predicate for the given piece.

    Construction (sq4 ordering -- matches the encoder's channel
    layout):
      H[i, j] = 1 iff square i is reachable from square j by the
      piece on an otherwise-empty 8^4 board.

    The reach relation is symmetric for all non-pawn pieces (a step
    in any direction is reversed by the opposite step), so H is
    real-symmetric and therefore Hermitian on C^4096 with eta = I.
    Pre-flight 2 verified this lift: for rook nnz = 114688, integer
    spectrum in [-4, 28]; cross-checked on knight.

    Parameters
    ----------
    piece : str
        One of 'N', 'B', 'R', 'Q', 'K'. Pawns ('P', 'p', 'P_w',
        'P_y', 'p_w', 'p_y') raise NotImplementedError -- they
        require pseudo-Hermitian machinery deferred to Track B.

    Returns
    -------
    csr_matrix of shape (4096, 4096), complex128 dtype.
    """
    if piece in _PAWN_HERMITIAN_KEYS:
        raise NotImplementedError(
            f"H_pawn ({piece!r}) is not implemented in qm_4d (Track A "
            "kinematic). Pawn reach is directed (forward push), so the "
            "lift breaks Hermiticity under the standard inner product. "
            "Track B (qm_4d_dynamics) introduces a pseudo-Hermitian "
            "metric eta and a parity-time symmetry for pawn dynamics. "
            "See docs/chess-maths/chess-spectral/python/research/"
            "phase_operators_4d_pseudo_hermitian_audit.md sec 6.2 for "
            "the design sketch."
        )
    if piece not in _HERMITIAN_PIECES:
        raise ValueError(
            f"unknown piece char {piece!r}; expected one of "
            f"{sorted(_HERMITIAN_PIECES)} (Hermitian observables) or "
            f"{sorted(_PAWN_HERMITIAN_KEYS)} (pawns -> Track B)"
        )
    adjs = _t4.piece_adjacencies_4d()
    A = adjs[_PIECE_TO_ADJ_IDX[piece]]
    H = A.astype(np.complex128).tocsr()
    # Validate Hermiticity at construction time. A.dtype == int8 from
    # tables_4d; the symmetry test is exact on integer entries, so any
    # asymmetry would be a hard bug we want to surface.
    diff = H - H.conj().T
    diff.eliminate_zeros()
    if diff.nnz != 0:
        raise AssertionError(
            f"H_{piece} from tables_4d is not symmetric -- "
            f"diff has {diff.nnz} nonzero entries, "
            f"max |diff| = {float(np.max(np.abs(diff.data)))}. "
            "This is a tables_4d invariant violation; see "
            "tables_4d.build_adjacency_4d's symmetrize step."
        )
    return H


def _get_or_build_H(piece: str) -> csr_matrix:
    """Cached accessor for piece Hermitians. Builds on first call."""
    if piece not in _H_PIECE_CACHE:
        _H_PIECE_CACHE[piece] = build_H_piece_4(piece)
    return _H_PIECE_CACHE[piece]


def __getattr__(name: str) -> csr_matrix:
    """Module-level lazy attribute access for the H_<piece>_4 names.

    Allows `from chess_spectral.qm_4d import H_rook_4` without paying
    the construction cost at import time. Each is built once on first
    access and cached.

    Recognized names:
        H_rook_4, H_bishop_4, H_queen_4, H_king_4, H_knight_4
        H_pawn_w_4, H_pawn_y_4   (raise NotImplementedError)
    """
    H_NAME_MAP = {
        'H_rook_4':   'R',
        'H_bishop_4': 'B',
        'H_queen_4':  'Q',
        'H_king_4':   'K',
        'H_knight_4': 'N',
    }
    if name in H_NAME_MAP:
        return _get_or_build_H(H_NAME_MAP[name])
    PAWN_NAME_MAP = {
        'H_pawn_w_4': 'P_w',
        'H_pawn_y_4': 'P_y',
    }
    if name in PAWN_NAME_MAP:
        # Trigger the same NotImplementedError as build_H_piece_4 so
        # callers get the Track B pointer.
        return build_H_piece_4(PAWN_NAME_MAP[name])
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


# ---- Spectral measurement helpers -----------------------------------


def measure_observable_distribution(
    H: csr_matrix | np.ndarray,
    psi: np.ndarray,
    tol: float = 1e-10,
) -> tuple[np.ndarray, np.ndarray]:
    """Spectral decomposition + Born-rule probabilities for H on psi.

    Diagonalizes H via dense eigh (assumes H is small enough to fit
    in memory as dense -- 4096x4096 is fine, 45056x45056 is NOT).
    Returns (eigenvalues, probabilities) where probabilities are
    Born-rule weights |<phi_k|psi>|^2 grouped by distinct eigenvalue.

    Parameters
    ----------
    H : sparse or dense Hermitian operator.
    psi : ndarray of compatible dimension.
    tol : float, eigenvalue grouping tolerance.

    Returns
    -------
    eigvals : ndarray[float64] of distinct eigenvalues (ascending).
    probs   : ndarray[float64] of Born probabilities, sum = ||psi||^2.

    Raises
    ------
    ValueError : if H.shape != (n, n) where n == len(psi).
    """
    if sp.issparse(H):
        H_dense = H.toarray()
    else:
        H_dense = np.asarray(H)
    if H_dense.shape[0] != H_dense.shape[1]:
        raise ValueError(f"H must be square; got shape {H_dense.shape}")
    if H_dense.shape[0] != psi.shape[0]:
        raise ValueError(
            f"shape mismatch: H is {H_dense.shape}, psi is {psi.shape}"
        )

    eigs, evecs = np.linalg.eigh(H_dense)
    # |c_k|^2 amplitudes in the eigenbasis
    coeffs = evecs.conj().T @ psi      # complex
    weights = (coeffs.conj() * coeffs).real  # |c_k|^2

    # Group by eigenvalue (within tol).
    order = np.argsort(eigs)
    eigs_sorted = eigs[order]
    weights_sorted = weights[order]
    grouped_eigs: list[float] = []
    grouped_probs: list[float] = []
    start = 0
    for k in range(1, len(eigs_sorted) + 1):
        if k == len(eigs_sorted) or (
            abs(eigs_sorted[k] - eigs_sorted[start]) > tol
        ):
            grouped_eigs.append(float(np.mean(eigs_sorted[start:k])))
            grouped_probs.append(float(weights_sorted[start:k].sum()))
            start = k
    return (np.asarray(grouped_eigs, dtype=np.float64),
            np.asarray(grouped_probs, dtype=np.float64))


# ---- Public API list ------------------------------------------------

__all__ = [
    # constants
    'N_CHANNELS', 'CHANNEL_DIM', 'ENCODING_DIM',
    # state construction
    'state_to_psi',
    # linear-algebra primitives
    'inner_product', 'norm', 'expectation',
    # validation helpers
    'is_normalized', 'is_unitary', 'is_hermitian',
    # B_4 unitary rep
    'b4_unitary_rep_4096', 'b4_unitary_rep_full',
    # channel PVM
    'channel_projector', 'prob_channel', 'measure_channel_distribution',
    # observables
    'build_H_piece_4',
    'H_rook_4', 'H_bishop_4', 'H_queen_4', 'H_king_4', 'H_knight_4',
    # spectral helpers
    'measure_observable_distribution',
    # NOTE: H_pawn_w_4 / H_pawn_y_4 are intentionally NOT in __all__:
    # they raise NotImplementedError on access, so a `from qm_4d import *`
    # would crash. They remain accessible by explicit attribute lookup
    # (qm_4d.H_pawn_w_4) for callers who want the Track B pointer.
]
