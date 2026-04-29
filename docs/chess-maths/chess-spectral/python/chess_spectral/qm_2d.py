"""chess_spectral.qm_2d - quantum-mechanical front-end for the 2D
640-dim spectral encoder.

Sibling of :mod:`chess_spectral.qm_4d` (4D, 45 056-dim). Wraps the
existing 640-dim float32 encoder output as a quantum state psi in
C^640, exposes Hermitian piece-reach observables on the per-channel
C^64 factor, the 10-channel projection-valued measure, the order-8
D_4 hyperoctahedral group action as cached unitaries, and Born-rule
helpers.

This is the KINEMATIC-only layer (Track A, 2D companion to v1.5's
Track A 4D module). Full move-as-unitary dynamics ship in
:mod:`chess_spectral.qm_2d_dynamics` (v1.6 PR-2).

Why qm_2d ships in v1.6
------------------------
The §16 Phase 6 plan (research notebook) calls for symmetric position
evaluators across 2D and 4D, including the QM-expectation evaluator.
v1.5.0 shipped only the 4D QM extension (qm_4d / qm_4d_dynamics /
qm_4d_bridge); the 2D analogue was implicit in the plan but never
named as a module. v1.6 closes the asymmetry so the QM-expectation
evaluator can be built on both dimensions per §16.1.3.

Design references:
  - 2D notebook §3, §4, §5 -- D_4 representation theory and the 10-
    channel decomposition of the 640-dim encoder
  - 2D notebook §15 -- cross-disciplinary motivation
  - qm_4d module -- the 4D template this module mirrors
  - qm_4d notebook §15.2 -- the Hermitian piece-reach observable lift
    pattern (translates structurally to 2D's C^64 per-channel factor)

Dimensions
----------
  ENCODING_DIM = 640 (vs 45 056 in 4D)
  N_CHANNELS   = 10  (vs 11 in 4D)
  CHANNEL_DIM  = 64  (vs 4096 in 4D; the 8x8 path-graph product)

Channel layout (matches encoder.py):
  c=0: A1, c=1: A2, c=2: B1, c=3: B2, c=4: E,
  c=5: F1, c=6: F2, c=7: F3, c=8: FA, c=9: FD

Public API (kinematic only)
---------------------------
  state_to_psi(position, side_to_move) -> psi : C^640
  inner_product(a, b) -> complex
  norm(psi) -> float
  expectation(O, psi) -> float
  is_normalized(psi, tol=1e-10) -> bool
  is_unitary(U, tol=1e-10) -> bool
  is_hermitian(H, tol=1e-10) -> bool
  d4_unitary_rep_64(g) -> sparse unitary on C^64 (one channel)
  d4_unitary_rep_full(g) -> sparse unitary on C^640 (all channels)
  d4_closure() -> list of 8 group elements
  channel_projector(c) -> sparse projector onto channel c (0..9)
  prob_channel(psi, c) -> Born-rule probability for channel c
  measure_channel_distribution(psi) -> ndarray[10] of probabilities
  H_rook_2, H_bishop_2, H_queen_2, H_king_2, H_knight_2
        -> sparse Hermitians on C^64 (lazily cached at first access)
  build_H_piece_2(piece) -> rebuild any of the above from scratch
  H_pawn_2 -> raises NotImplementedError (deferred to a future
        pseudo-Hermitian / eta-metric extension; mirrors qm_4d's
        Track-B pointer at ADR-005)

Conventions
-----------
  - dtype is complex128 throughout (psi, sparse operators).
  - The 64-dim factor uses sq2 ordering (r * 8 + c, matching the
    encoder's row-major ravel).
  - The "full" 640-dim space is the direct sum of 10 copies of
    C^64; channel-restricted operators act as I_10 (x) O_64 when
    lifted (or as a block-diagonal selection projector).
  - This module imports from chess_spectral.encoder and
    chess_spectral.tables only; no modifications to those.
  - Z_2 superselection: same convention as qm_4d -- side_to_move=True
    multiplies psi by +1, False by -1. The chess_spectral 2D encoder
    has not been audited for the same (central inversion + color
    flip) injectivity gap that motivated qm_4d's Z_2 sector
    convention; we apply the convention here for symmetry with the 4D
    module and to keep downstream consumers' Z_2 handling uniform.
    A focused 2D injectivity audit (analogue of the 4D Pre-flight 1)
    can land later without API change.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix, lil_matrix

from chess_spectral import encoder as _enc2
from chess_spectral import tables as _t2


# ---- Dimension constants --------------------------------------------

# Channel sizes mirror the encoder layout. Source of truth lives in
# encoder; we re-export for direct module use and assert consistency.
N_CHANNELS: int = _enc2.N_CHANNELS              # 10
ENCODING_DIM: int = _enc2.ENCODING_DIM          # 640
BOARD_DIM: int = _t2.BOARD_DIM                  # 64

# 2D is uniform: 640 / 10 = 64 modes per channel. The qm_4d analogue
# is uniform too (45056 / 11 = 4096), so we can use a single CHANNEL_DIM
# constant. If a future 2D rework introduces variable-width channels,
# this constant becomes a per-channel array; today it does not.
CHANNEL_DIM: int = ENCODING_DIM // N_CHANNELS  # 64

assert CHANNEL_DIM * N_CHANNELS == ENCODING_DIM, (
    "Channel layout mismatch: CHANNEL_DIM * N_CHANNELS != ENCODING_DIM "
    f"({CHANNEL_DIM} * {N_CHANNELS} != {ENCODING_DIM})"
)
assert CHANNEL_DIM == BOARD_DIM, (
    "Per-channel dim must equal the 8x8 board cell count (64). "
    f"Got CHANNEL_DIM={CHANNEL_DIM}, BOARD_DIM={BOARD_DIM}."
)


# ---- State construction ---------------------------------------------


def state_to_psi(position: Dict[int, str],
                 side_to_move: bool) -> np.ndarray:
    """Encode a 2D chess position to a normalized complex amplitude
    psi in C^640.

    Parameters
    ----------
    position : dict {sq -> piece char}
        Same schema as :func:`chess_spectral.encoder.encode_640`.
        Square indices are 0..63, row-major from a8=0 (matches
        encoder.py); piece chars are upper-case for white
        ('P','N','B','R','Q','K') and lower-case for black.
    side_to_move : bool
        True = white to move, False = black to move. Multiplies psi
        by +/-1 to encode the Z_2 sector. See the module docstring
        "Z_2 superselection" note.

    Returns
    -------
    psi : ndarray[complex128, (640,)]
        L2-normalized amplitude. ||psi||_2 == 1 (within float
        rounding). For an empty position the encoder returns the zero
        vector; we return the same zero vector unchanged (a non-
        physical sentinel) -- :func:`is_normalized` will return False
        in that case so callers can detect the empty-state edge.

    Note: the 2D encoder returns float64; we cast to complex128 for
    QM consistency with qm_4d.
    """
    enc = _enc2.encode_640(position).astype(np.complex128)
    if not side_to_move:
        enc = -enc
    n = float(np.linalg.norm(enc))
    if n == 0.0:
        return enc
    return enc / n


# ---- Inner product / norm / expectation -----------------------------


def inner_product(a: np.ndarray, b: np.ndarray) -> complex:
    """Hermitian inner product <a|b> = sum_i a_i^* b_i.

    Uses :func:`numpy.vdot` which conjugates the first argument.
    Returns a complex scalar.
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


# ---- D_4 group construction -----------------------------------------

# D_4 = dihedral group of order 8 acting on the 8x8 board. Elements
# are stored as a 64-vector permutation `perm[s] = g.s` -- the image
# square index. We enumerate all 8 elements explicitly (4 rotations +
# 4 reflections) and cache them. This mirrors qm_4d's GroupElem /
# closure pattern at much smaller scale (8 elements vs 384).
#
# Convention: square index s = r*8 + c where (r, c) is row-major from
# the top-left (matches encoder.py / tables.py BOARD_DIM=64 raveling).
# Group elements act on (r, c) and we ravel back to s.

GroupElem = Tuple[int, ...]   # length-64 permutation of square indices


def _rc(s: int) -> Tuple[int, int]:
    return s // 8, s % 8


def _sq(r: int, c: int) -> int:
    return r * 8 + c


_D4_ACTIONS: List[Tuple[str, callable]] = [
    ("e",         lambda r, c: (r, c)),
    ("rot90",     lambda r, c: (c, 7 - r)),
    ("rot180",    lambda r, c: (7 - r, 7 - c)),
    ("rot270",    lambda r, c: (7 - c, r)),
    ("flip_h",    lambda r, c: (7 - r, c)),
    ("flip_v",    lambda r, c: (r, 7 - c)),
    ("flip_diag", lambda r, c: (c, r)),
    ("flip_anti", lambda r, c: (7 - c, 7 - r)),
]


_D4_CLOSURE_CACHE: List[GroupElem] | None = None


def d4_closure() -> List[GroupElem]:
    """Return the 8 elements of D_4 acting on the 8x8 board.

    Each element is a length-64 tuple `perm` such that the action on
    square s is `perm[s]` (the image of s under g).

    The list ordering is fixed: identity first, then three rotations
    (90/180/270 degrees clockwise), then four reflections (horizontal,
    vertical, diagonal, anti-diagonal). Cached on first call -- the
    same list object is returned on subsequent calls.
    """
    global _D4_CLOSURE_CACHE
    if _D4_CLOSURE_CACHE is not None:
        return _D4_CLOSURE_CACHE
    closure: List[GroupElem] = []
    for _name, fn in _D4_ACTIONS:
        perm: List[int] = [0] * BOARD_DIM
        for s in range(BOARD_DIM):
            r, c = _rc(s)
            r2, c2 = fn(r, c)
            perm[s] = _sq(r2, c2)
        closure.append(tuple(perm))
    _D4_CLOSURE_CACHE = closure
    return closure


def d4_element_name(g_index: int) -> str:
    """Human-readable name of the g_index-th D_4 element. Useful for
    debug output and test failure messages.

    Indices match the order from :func:`d4_closure`:
      0: e (identity)
      1: rot90
      2: rot180
      3: rot270
      4: flip_h (horizontal reflection)
      5: flip_v (vertical reflection)
      6: flip_diag (main diagonal reflection)
      7: flip_anti (anti-diagonal reflection)
    """
    if not 0 <= g_index < len(_D4_ACTIONS):
        raise ValueError(
            f"D_4 group index {g_index} out of range [0, "
            f"{len(_D4_ACTIONS)})"
        )
    return _D4_ACTIONS[g_index][0]


# ---- D_4 unitary representation -------------------------------------

# Cache of 64-dim D_4 unitaries keyed by group element (the perm tuple).
# 8 elements total, so the cache stays bounded at 8 entries.
_D4_UNITARY_CACHE: Dict[GroupElem, csr_matrix] = {}


def d4_unitary_rep_64(g: GroupElem) -> csr_matrix:
    """Return the 64x64 sparse unitary representing g in C^64.

    Permutation matrices over a real basis are unitary over C; we
    cast to complex128 to keep the dtype consistent with the rest of
    the QM module (psi is complex128).

    Caches results per group element so repeated calls are O(1).
    Cache size is bounded at 8 (|D_4|).
    """
    if g in _D4_UNITARY_CACHE:
        return _D4_UNITARY_CACHE[g]
    if len(g) != BOARD_DIM:
        raise ValueError(
            f"D_4 group element must be a length-{BOARD_DIM} permutation "
            f"tuple; got length {len(g)}"
        )
    rows = list(g)
    cols = list(range(BOARD_DIM))
    data = [1.0 + 0j] * BOARD_DIM
    P = csr_matrix(
        (data, (rows, cols)),
        shape=(BOARD_DIM, BOARD_DIM),
        dtype=np.complex128,
    )
    _D4_UNITARY_CACHE[g] = P
    return P


def d4_unitary_rep_full(g: GroupElem) -> csr_matrix:
    """Return the 640x640 sparse unitary representing g on the full
    encoder space. This is I_10 (x) U_64(g) -- the same D_4 action
    applied independently to each of the 10 channels.

    Built by Kronecker-ing an identity in the channel slot. Returns
    a CSR sparse matrix with complex128 dtype.
    """
    U_block = d4_unitary_rep_64(g)
    I_chan = sp.eye(N_CHANNELS, format="csr", dtype=np.complex128)
    return sp.kron(I_chan, U_block, format="csr")


# ---- Channel projection-valued measure ------------------------------


def channel_projector(c: int) -> csr_matrix:
    """Sparse 640x640 projector P_c onto channel c (0..9).

    P_c is diagonal with 1's on rows [c*64 : (c+1)*64) and 0
    elsewhere. The 10 projectors form a complete orthogonal PVM:
    sum_c P_c == I_640 and P_c P_d == delta_{cd} P_c.
    """
    if not 0 <= c < N_CHANNELS:
        raise ValueError(
            f"channel index {c} out of range [0, {N_CHANNELS})"
        )
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
        raise ValueError(
            f"channel index {c} out of range [0, {N_CHANNELS})"
        )
    start = c * CHANNEL_DIM
    block = psi[start:start + CHANNEL_DIM]
    return float(np.vdot(block, block).real)


def measure_channel_distribution(psi: np.ndarray) -> np.ndarray:
    """Born-rule probabilities for all 10 channels.

    Returns a real ndarray of shape (10,). For a normalized psi the
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

# 2D piece-target functions live in tables.py SHORT_PFNS, keyed by
# piece character. We build sparse adjacencies on the 8x8 board (64
# squares) and lift them to Hermitians on C^64.

# Allowed pieces for the Hermitian observable lift. Excludes pawns
# (directed push breaks Hermiticity, same physics as the 4D side --
# see qm_4d's _PAWN_HERMITIAN_KEYS).
_HERMITIAN_PIECES_2D = frozenset({'N', 'B', 'R', 'Q', 'K'})

# Pawn keys that should raise NotImplementedError with an informative
# message. 2D pawns are 'P' (white) / 'p' (black). The pseudo-Hermitian
# eta-metric construction is deferred -- same disposition as qm_4d
# Track A.
_PAWN_HERMITIAN_KEYS_2D = frozenset({'P', 'p'})

# Cache of materialised Hermitians; built once on first access.
_H_PIECE_CACHE_2D: Dict[str, csr_matrix] = {}


def _build_piece_adjacency_2d(piece: str) -> csr_matrix:
    """Build the sparse 64x64 adjacency matrix for a non-pawn piece on
    the 8x8 board. A[i, j] == 1 iff square i is reachable from square
    j by the piece on an otherwise-empty board.

    Symmetrized for safety -- non-pawn reach is involutive on chess
    rules (a step in any direction is reversed by the opposite step),
    so the symmetrize is a no-op in steady state but catches a
    boundary-handling slip if one ever appears.
    """
    if piece not in _t2.SHORT_PFNS:
        raise ValueError(
            f"unknown piece char {piece!r} for 2D adjacency; expected "
            f"one of {sorted(_t2.SHORT_PFNS)}"
        )
    fn = _t2.SHORT_PFNS[piece]
    A = lil_matrix((BOARD_DIM, BOARD_DIM), dtype=np.int8)
    for r in range(8):
        for c in range(8):
            for tr, tc in fn(r, c):
                A[_sq(r, c), _sq(tr, tc)] = 1
    A = A.tocsr()
    A = A.maximum(A.T)
    return A


def build_H_piece_2(piece: str) -> csr_matrix:
    """Build the Hermitian operator H_piece on C^64 from the
    chess-symmetric reach predicate for the given piece.

    Construction (sq2 ordering -- matches the encoder's 64-mode block):
      H[i, j] = 1 iff square i is reachable from square j by the
      piece on an otherwise-empty 8x8 board.

    The reach relation is symmetric for all non-pawn pieces (a step
    in any direction is reversed by the opposite step), so H is
    real-symmetric and therefore Hermitian on C^64 with eta = I.
    Returned dtype is complex128 (cast from int8).

    Parameters
    ----------
    piece : str
        One of 'N', 'B', 'R', 'Q', 'K'. Pawns ('P', 'p') raise
        NotImplementedError -- they require pseudo-Hermitian
        machinery deferred (mirrors qm_4d's pawn observable
        deferral; the 2D analogue of 4D's Track-B / ADR-005 lift
        is not yet drafted as an ADR but follows the same physics).

    Returns
    -------
    csr_matrix of shape (64, 64), complex128 dtype.
    """
    if piece in _PAWN_HERMITIAN_KEYS_2D:
        raise NotImplementedError(
            f"H_pawn_2 ({piece!r}) is not implemented in qm_2d (Track A "
            "kinematic). Pawn reach is directed (forward push), so the "
            "lift breaks Hermiticity under the standard inner product. "
            "The pseudo-Hermitian / eta-metric machinery deferred for "
            "the 4D side at ADR-005 (qm_4d_pseudo_hermitian_eta_metric) "
            "applies structurally here as well; a 2D-specific ADR will "
            "land alongside the eta-metric implementation."
        )
    if piece not in _HERMITIAN_PIECES_2D:
        raise ValueError(
            f"unknown piece char {piece!r}; expected one of "
            f"{sorted(_HERMITIAN_PIECES_2D)} (Hermitian observables) or "
            f"{sorted(_PAWN_HERMITIAN_KEYS_2D)} (pawns -> deferred)"
        )
    A = _build_piece_adjacency_2d(piece)
    H = A.astype(np.complex128).tocsr()
    diff = H - H.conj().T
    diff.eliminate_zeros()
    if diff.nnz != 0:
        raise AssertionError(
            f"H_{piece}_2 from piece-adjacency builder is not symmetric "
            f"-- diff has {diff.nnz} nonzero entries, "
            f"max |diff| = {float(np.max(np.abs(diff.data)))}. "
            "This is an internal invariant violation; check "
            "_build_piece_adjacency_2d's symmetrize step."
        )
    return H


def _get_or_build_H_2d(piece: str) -> csr_matrix:
    """Cached accessor for piece Hermitians. Builds on first call."""
    if piece not in _H_PIECE_CACHE_2D:
        _H_PIECE_CACHE_2D[piece] = build_H_piece_2(piece)
    return _H_PIECE_CACHE_2D[piece]


def __getattr__(name: str) -> csr_matrix:
    """Module-level lazy attribute access for the H_<piece>_2 names.

    Allows `from chess_spectral.qm_2d import H_rook_2` without paying
    the construction cost at import time. Each is built once on first
    access and cached.

    Recognized names:
        H_rook_2, H_bishop_2, H_queen_2, H_king_2, H_knight_2
        H_pawn_2 (raises NotImplementedError; informative message)
    """
    H_NAME_MAP = {
        'H_rook_2':   'R',
        'H_bishop_2': 'B',
        'H_queen_2':  'Q',
        'H_king_2':   'K',
        'H_knight_2': 'N',
    }
    if name in H_NAME_MAP:
        return _get_or_build_H_2d(H_NAME_MAP[name])
    if name == 'H_pawn_2':
        # Trigger NotImplementedError with the standard pointer; we
        # don't differentiate white vs black pawn at the kinematic
        # observable level -- the directed-push pathology applies
        # to both.
        return build_H_piece_2('P')
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


# ---- Spectral measurement helpers -----------------------------------


def measure_observable_distribution(
    H: csr_matrix | np.ndarray,
    psi: np.ndarray,
    tol: float = 1e-10,
) -> Tuple[np.ndarray, np.ndarray]:
    """Spectral decomposition + Born-rule probabilities for H on psi.

    Diagonalizes H via dense eigh (assumes H fits in memory as dense
    -- 64x64 is trivial for the per-channel block; 640x640 is also
    fine if the caller chooses to lift first). Returns
    (eigenvalues, probabilities) where probabilities are Born-rule
    weights |<phi_k|psi>|^2 grouped by distinct eigenvalue.

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
    coeffs = evecs.conj().T @ psi
    weights = (coeffs.conj() * coeffs).real

    order = np.argsort(eigs)
    eigs_sorted = eigs[order]
    weights_sorted = weights[order]
    grouped_eigs: List[float] = []
    grouped_probs: List[float] = []
    start = 0
    for k in range(1, len(eigs_sorted) + 1):
        if k == len(eigs_sorted) or (
            abs(eigs_sorted[k] - eigs_sorted[start]) > tol
        ):
            grouped_eigs.append(float(np.mean(eigs_sorted[start:k])))
            grouped_probs.append(float(weights_sorted[start:k].sum()))
            start = k
    return (
        np.asarray(grouped_eigs, dtype=np.float64),
        np.asarray(grouped_probs, dtype=np.float64),
    )


# ---- Public API list ------------------------------------------------

__all__ = [
    # constants
    'N_CHANNELS', 'CHANNEL_DIM', 'ENCODING_DIM', 'BOARD_DIM',
    # state construction
    'state_to_psi',
    # linear-algebra primitives
    'inner_product', 'norm', 'expectation',
    # validation helpers
    'is_normalized', 'is_unitary', 'is_hermitian',
    # D_4 unitary rep
    'd4_closure', 'd4_element_name',
    'd4_unitary_rep_64', 'd4_unitary_rep_full',
    # channel PVM
    'channel_projector', 'prob_channel', 'measure_channel_distribution',
    # observables
    'build_H_piece_2',
    'H_rook_2', 'H_bishop_2', 'H_queen_2', 'H_king_2', 'H_knight_2',
    # spectral helpers
    'measure_observable_distribution',
    # NOTE: H_pawn_2 is intentionally NOT in __all__: it raises
    # NotImplementedError on access, so a `from qm_2d import *` would
    # crash. It remains accessible by explicit attribute lookup
    # (qm_2d.H_pawn_2) for callers who want the deferral pointer.
]
