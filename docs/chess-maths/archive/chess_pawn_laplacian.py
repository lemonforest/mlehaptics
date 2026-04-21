#!/usr/bin/env python3
"""
Pawn Directed Laplacian: Spectral Characterization of the Only Directed Piece
=============================================================================

The pawn is the only chess piece with inherently directed movement (forward
only), making it the only piece whose adjacency matrix is non-symmetric.
A naive Laplacian L = D - A is non-Hermitian, breaking the spectral framework
that works for all other pieces.

Solution: Decompose into symmetric and antisymmetric parts.
  A_white: directed adjacency for white pawns (move toward rank 8, i.e. row 0)
  A_black: directed adjacency for black pawns (180-degree rotation of A_white)
  A_sym  = (A_white + A_black) / 2  — Hermitian, Z2-preserving
  A_anti = (A_white - A_black) / 2  — antisymmetric, Z2-breaking

The symmetric part fits the existing spectral framework (Laplacian, eigenvalues,
fiber coordinates, quantum numbers). The antisymmetric part captures the
directional information unique to pawns.

Board convention (same as encoder_512.py):
  r=0 is rank 8 (black's back rank), r=7 is rank 1 (white's back rank)
  sq(r, c) = r*8 + c
  White pawns on rows 1-6 move toward row 0
  Black pawns on rows 1-6 move toward row 7

Dependencies: numpy, scipy, encoder_512 (same directory)
Run: python chess_pawn_laplacian.py
"""

import os
import sys
import io
import numpy as np
from scipy.linalg import eigh, svd, eigvals
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console encoding — must happen BEFORE importing encoder_512
# which also does this and has module-level prints
if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Import from encoder_512 in same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encoder_512 import (
    sq, rc, sqname,
    build_adjacency, graph_laplacian,
    EVECS_GRID, EVALS_GRID, L_GRID,
    PIECE_FNS, SHORT_PFNS, SPECTRAL_VALS,
    FIBER_BASIS, LOCAL_FIBER_3D, LOCAL_ADJ_ROWS,
    fibers_global, upper_idx,
    compute_quantum_numbers,
    board_signal, encode_512,
    build_codebook_qn,
)

np.random.seed(42)


# ═══════════════════════════════════════════════════════════════
# PART 1: DIRECTED ADJACENCY MATRICES
# ═══════════════════════════════════════════════════════════════

def white_pawn_targets(r, c):
    """All squares a white pawn on (r,c) can reach (move + capture).

    White pawns move toward row 0 (rank 8).
    No edges from row 0 (promotion rank) or row 7 (impossible position).
    """
    if r <= 0 or r >= 7:
        return  # no moves from promotion rank or back rank

    # Standard forward move: one square toward row 0
    yield (r - 1, c)

    # Initial double move: from rank 2 (row 6) only
    if r == 6:
        yield (r - 2, c)

    # Capture diagonals (always available as potential moves)
    if c > 0:
        yield (r - 1, c - 1)   # capture left
    if c < 7:
        yield (r - 1, c + 1)   # capture right


def black_pawn_targets(r, c):
    """All squares a black pawn on (r,c) can reach (move + capture).

    Black pawns move toward row 7 (rank 1).
    No edges from row 7 (promotion rank) or row 0 (impossible position).
    """
    if r <= 0 or r >= 7:
        return  # no moves from promotion rank or back rank

    # Standard forward move: one square toward row 7
    yield (r + 1, c)

    # Initial double move: from rank 7 (row 1) only
    if r == 1:
        yield (r + 2, c)

    # Capture diagonals
    if c > 0:
        yield (r + 1, c - 1)
    if c < 7:
        yield (r + 1, c + 1)


def white_pawn_moves_only(r, c):
    """White pawn forward moves only (no captures)."""
    if r <= 0 or r >= 7:
        return
    yield (r - 1, c)
    if r == 6:
        yield (r - 2, c)


def white_pawn_captures_only(r, c):
    """White pawn capture moves only (no forward moves)."""
    if r <= 0 or r >= 7:
        return
    if c > 0:
        yield (r - 1, c - 1)
    if c < 7:
        yield (r - 1, c + 1)


def black_pawn_moves_only(r, c):
    """Black pawn forward moves only (no captures)."""
    if r <= 0 or r >= 7:
        return
    yield (r + 1, c)
    if r == 1:
        yield (r + 2, c)


def black_pawn_captures_only(r, c):
    """Black pawn capture moves only (no forward moves)."""
    if r <= 0 or r >= 7:
        return
    if c > 0:
        yield (r + 1, c - 1)
    if c < 7:
        yield (r + 1, c + 1)


def build_directed_adjacency(fn):
    """Build 64x64 directed adjacency matrix from a target function.

    Unlike build_adjacency() in encoder_512.py, this does NOT symmetrize.
    A[i,j] = 1 means there is an edge FROM square i TO square j.
    """
    A = np.zeros((64, 64))
    for r in range(8):
        for c in range(8):
            for tr, tc in fn(r, c):
                A[sq(r, c), sq(tr, tc)] = 1
    return A


# ═══════════════════════════════════════════════════════════════
# PART 2: SYMMETRIC / ANTISYMMETRIC DECOMPOSITION
# ═══════════════════════════════════════════════════════════════

def decompose_pawn():
    """Compute pawn directed adjacency matrices and their decomposition.

    NOTE: The spec proposed A_sym = (A_white + A_black)/2, claiming this
    is symmetric because A_black = rot180(A_white). This is WRONG:
    rotation != transpose, so the sum of two directed matrices related
    by rotation is NOT symmetric. Verified: 120 asymmetric elements.

    Correct approach: standard matrix decomposition of A_white into
    symmetric and antisymmetric parts via transpose:
        A_sym  = (A_white + A_white^T) / 2   — guaranteed Hermitian
        A_anti = (A_white - A_white^T) / 2   — guaranteed antisymmetric

    A_sym represents undirected pawn reachability (if a white pawn can
    move from i to j, there's also weight from j to i).
    A_anti captures the net directional flow (Z2-breaking).

    By 180-degree rotation symmetry, A_black produces identical spectral
    properties, so we only need to analyze one color.

    We also compute A_combined = A_white + A_black and its decomposition
    for completeness (the "color-averaged" perspective).

    Returns dict with:
        A_white, A_black:         64x64 directed adjacency
        A_sym, A_anti:            transpose-decomposition of A_white
        A_combined:               A_white + A_black (both colors overlaid)
        A_combined_sym:           symmetric part of combined
        color_avg, color_diff:    (A_w + A_b)/2, (A_w - A_b)/2 (user's original)
        L_sym:                    graph Laplacian of A_sym (Hermitian)
        evals_sym, evecs_sym:     eigendecomposition of L_sym
    """
    A_white = build_directed_adjacency(white_pawn_targets)
    A_black = build_directed_adjacency(black_pawn_targets)

    # Correct decomposition: transpose-based (always works)
    A_sym = (A_white + A_white.T) / 2.0
    A_anti = (A_white - A_white.T) / 2.0

    # Verify properties
    assert np.allclose(A_sym, A_sym.T), "A_sym should be symmetric"
    assert np.allclose(A_anti, -A_anti.T), "A_anti should be antisymmetric"
    assert np.allclose(A_white, A_sym + A_anti), "Decomposition should be exact"

    # Combined (both colors) and its decomposition
    A_combined = A_white + A_black
    A_combined_sym = (A_combined + A_combined.T) / 2.0
    A_combined_anti = (A_combined - A_combined.T) / 2.0

    # User's original color-averaging (NOT symmetric — kept for comparison)
    color_avg = (A_white + A_black) / 2.0
    color_diff = (A_white - A_black) / 2.0

    # Symmetric Laplacian (Hermitian — fits existing framework)
    L_sym = graph_laplacian(A_sym)
    evals_sym, evecs_sym = eigh(L_sym)

    return {
        'A_white': A_white,
        'A_black': A_black,
        'A_sym': A_sym,
        'A_anti': A_anti,
        'A_combined': A_combined,
        'A_combined_sym': A_combined_sym,
        'A_combined_anti': A_combined_anti,
        'color_avg': color_avg,
        'color_diff': color_diff,
        'L_sym': L_sym,
        'evals_sym': evals_sym,
        'evecs_sym': evecs_sym,
    }


# ═══════════════════════════════════════════════════════════════
# PART 3: SPECTRAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_symmetric(decomp):
    """Full spectral analysis of the symmetric part.

    Returns dict with spectral properties, quantum numbers, fiber coordinates.
    """
    A_sym = decomp['A_sym']
    L_sym = decomp['L_sym']
    evals_sym = decomp['evals_sym']
    evecs_sym = decomp['evecs_sym']

    # --- Basic graph properties ---
    degrees = A_sym.sum(axis=1)
    mean_degree = degrees.mean()
    spectral_value = mean_degree / 2.6  # same normalization as other pieces

    # Number of connected components (zeros in Laplacian spectrum)
    n_components = int(np.sum(np.abs(evals_sym) < 1e-10))

    # Algebraic connectivity (smallest nonzero eigenvalue)
    nonzero = evals_sym[evals_sym > 1e-10]
    lambda_2 = float(nonzero[0]) if len(nonzero) > 0 else 0.0

    # Spectral bandwidth
    bandwidth = float(evals_sym[-1])

    # Degree regularity
    degree_std = float(np.std(degrees))
    is_regular = degree_std < 0.01

    # --- Parity (bipartiteness from adjacency spectrum) ---
    evals_A = np.sort(np.linalg.eigvals(A_sym).real)
    pos_ev = evals_A[evals_A > 0.01]
    neg_ev = -evals_A[evals_A < -0.01]
    nm = min(len(pos_ev), len(neg_ev))
    sym_err = (np.linalg.norm(np.sort(pos_ev)[:nm] - np.sort(neg_ev)[:nm])
               if nm > 0 else float('inf'))
    parity = int(sym_err < 0.01)

    # --- Quantum number 5-tuple ---
    quantum_numbers = (
        parity,                                              # bipartiteness
        n_components,                                        # connected components
        int(is_regular),                                     # degree regularity
        round(lambda_2, 4),                                  # algebraic connectivity
        round(bandwidth, 2),                                 # spectral bandwidth
    )

    # --- Fiber analysis: project L_sym onto board eigenbasis ---
    C_sym = EVECS_GRID.T @ L_sym @ EVECS_GRID
    C_off = C_sym.copy()
    np.fill_diagonal(C_off, 0)
    fiber_vec = C_off[upper_idx]
    fiber_norm = np.linalg.norm(fiber_vec)

    # Project into 3D fiber space (same basis as other pieces)
    fiber_3d = fiber_vec @ FIBER_BASIS if fiber_norm > 0 else np.zeros(3)

    # Compare with other pieces' fiber vectors
    fiber_sims = {}
    for name, fvec in fibers_global.items():
        fn = np.linalg.norm(fvec)
        if fn > 0 and fiber_norm > 0:
            fiber_sims[name] = float(fiber_vec @ fvec / (fiber_norm * fn))
        else:
            fiber_sims[name] = 0.0

    # Fiber rank: how much of L_sym's structure lives off-diagonal
    # (i.e., content not captured by the board's own eigenbasis)
    diag_energy = np.sum(np.diag(C_sym) ** 2)
    total_energy = np.sum(C_sym ** 2)
    off_diag_fraction = 1.0 - diag_energy / total_energy if total_energy > 0 else 0.0

    return {
        'mean_degree': mean_degree,
        'spectral_value': spectral_value,
        'n_components': n_components,
        'lambda_2': lambda_2,
        'bandwidth': bandwidth,
        'degree_std': degree_std,
        'is_regular': is_regular,
        'parity': parity,
        'quantum_numbers': quantum_numbers,
        'fiber_vec': fiber_vec,
        'fiber_3d': fiber_3d,
        'fiber_norm': fiber_norm,
        'fiber_sims': fiber_sims,
        'off_diag_fraction': off_diag_fraction,
        'degrees': degrees,
        'evals_sym': evals_sym,
    }


def analyze_antisymmetric(decomp):
    """Characterize the antisymmetric (Z2-breaking) part.

    A_anti is real antisymmetric → eigenvalues are pure imaginary conjugate pairs ±iλ.
    """
    A_anti = decomp['A_anti']
    A_sym = decomp['A_sym']

    # Eigenvalues of A_anti (should be pure imaginary pairs)
    evals_anti = eigvals(A_anti)
    imag_parts = np.sort(np.abs(evals_anti.imag))[::-1]
    real_parts = np.abs(evals_anti.real)

    # Verify pure imaginary (real parts should be ~0)
    max_real = float(np.max(real_parts))
    is_pure_imaginary = max_real < 1e-10

    # Nonzero imaginary eigenvalues (conjugate pairs)
    sig_imag = imag_parts[imag_parts > 1e-10]
    n_pairs = len(sig_imag) // 2  # conjugate pairs

    # Norms for relative strength
    norm_anti = float(np.linalg.norm(A_anti, 'fro'))
    norm_sym = float(np.linalg.norm(A_sym, 'fro'))
    anti_ratio = norm_anti / norm_sym if norm_sym > 0 else float('inf')

    # --- Fiber analysis of A_anti ---
    # Project A_anti onto board eigenbasis
    C_anti = EVECS_GRID.T @ A_anti @ EVECS_GRID
    C_anti_off = C_anti.copy()
    np.fill_diagonal(C_anti_off, 0)
    fiber_anti = C_anti_off[upper_idx]
    fiber_anti_norm = np.linalg.norm(fiber_anti)

    # Orthogonality with symmetric fiber
    L_sym = decomp['L_sym']
    C_sym_full = EVECS_GRID.T @ L_sym @ EVECS_GRID
    C_sym_off = C_sym_full.copy()
    np.fill_diagonal(C_sym_off, 0)
    fiber_sym = C_sym_off[upper_idx]
    fiber_sym_norm = np.linalg.norm(fiber_sym)

    if fiber_anti_norm > 0 and fiber_sym_norm > 0:
        sym_anti_cos = float(fiber_anti @ fiber_sym / (fiber_anti_norm * fiber_sym_norm))
    else:
        sym_anti_cos = 0.0

    # Orthogonality with other pieces' fibers
    fiber_anti_sims = {}
    for name, fvec in fibers_global.items():
        fn = np.linalg.norm(fvec)
        if fn > 0 and fiber_anti_norm > 0:
            fiber_anti_sims[name] = float(fiber_anti @ fvec / (fiber_anti_norm * fn))
        else:
            fiber_anti_sims[name] = 0.0

    return {
        'evals_anti': evals_anti,
        'imag_parts': imag_parts,
        'max_real': max_real,
        'is_pure_imaginary': is_pure_imaginary,
        'n_imaginary_pairs': n_pairs,
        'top_imag_eigenvalues': sig_imag[:6],
        'norm_anti': norm_anti,
        'norm_sym': norm_sym,
        'anti_sym_ratio': anti_ratio,
        'fiber_anti': fiber_anti,
        'fiber_anti_norm': fiber_anti_norm,
        'sym_anti_fiber_cos': sym_anti_cos,
        'fiber_anti_sims': fiber_anti_sims,
    }


# ═══════════════════════════════════════════════════════════════
# PART 4: MOVEMENT vs CAPTURE SEPARATION
# ═══════════════════════════════════════════════════════════════

def analyze_movement_vs_capture():
    """Build separate adjacency matrices for forward moves and captures.

    For each sub-graph, compute spectral properties and compare.
    """
    # White sub-graphs
    A_w_move = build_directed_adjacency(white_pawn_moves_only)
    A_w_capt = build_directed_adjacency(white_pawn_captures_only)

    # Black sub-graphs
    A_b_move = build_directed_adjacency(black_pawn_moves_only)
    A_b_capt = build_directed_adjacency(black_pawn_captures_only)

    # Symmetrized sub-graphs
    A_move_sym = (A_w_move + A_b_move) / 2.0
    A_capt_sym = (A_w_capt + A_b_capt) / 2.0

    results = {}
    for label, A in [('move', A_move_sym), ('capture', A_capt_sym)]:
        L = graph_laplacian(A)
        evals, evecs = eigh(L)

        degrees = A.sum(axis=1)
        mean_deg = degrees.mean()
        nonzero = evals[evals > 1e-10]

        # Fiber projection
        C = EVECS_GRID.T @ L @ EVECS_GRID
        C_off = C.copy()
        np.fill_diagonal(C_off, 0)
        fvec = C_off[upper_idx]

        results[label] = {
            'A': A,
            'L': L,
            'evals': evals,
            'mean_degree': mean_deg,
            'spectral_value': mean_deg / 2.6,
            'lambda_2': float(nonzero[0]) if len(nonzero) > 0 else 0.0,
            'bandwidth': float(evals[-1]),
            'n_components': int(np.sum(np.abs(evals) < 1e-10)),
            'fiber_vec': fvec,
            'fiber_norm': np.linalg.norm(fvec),
        }

    # Check additivity: A_sym should equal A_move_sym + A_capt_sym
    A_total = A_move_sym + A_capt_sym
    A_white_full = build_directed_adjacency(white_pawn_targets)
    A_black_full = build_directed_adjacency(black_pawn_targets)
    A_sym_full = (A_white_full + A_black_full) / 2.0
    additivity_error = np.linalg.norm(A_total - A_sym_full)

    # Cosine similarity between move and capture fiber vectors
    fn_m = results['move']['fiber_norm']
    fn_c = results['capture']['fiber_norm']
    if fn_m > 0 and fn_c > 0:
        move_capt_cos = float(
            results['move']['fiber_vec'] @ results['capture']['fiber_vec'] / (fn_m * fn_c))
    else:
        move_capt_cos = 0.0

    results['additivity_error'] = additivity_error
    results['move_capture_fiber_cos'] = move_capt_cos

    return results


# ═══════════════════════════════════════════════════════════════
# PART 5: QUANTUM NUMBER CODEBOOK UPDATE
# ═══════════════════════════════════════════════════════════════

def compute_full_quantum_numbers(sym_analysis):
    """Complete quantum number table including pawn (from symmetric Laplacian).

    Returns dict of {piece_char: 5-tuple} for all 6 piece types.
    """
    # Get existing quantum numbers (N, B, R, Q, K)
    qn = compute_quantum_numbers()

    # Add pawn from our symmetric analysis
    qn['P'] = sym_analysis['quantum_numbers']

    return qn


def build_full_codebook(qn_full, dim=512):
    """Build 512-dim codebook with pawn properly characterized.

    Unlike the fallback random pawn in encoder_512.py, this uses
    the actual quantum numbers from the symmetric Laplacian.
    """
    rng = np.random.RandomState(2024)  # same seed as encoder_512

    # 5 random bipolar base vectors
    bases = [rng.choice([-1, 1], size=dim).astype(float) for _ in range(5)]

    # Normalization ranges (now including pawn)
    all_l2 = [v[3] for v in qn_full.values()]
    all_bw = [v[4] for v in qn_full.values()]
    l2_min, l2_range = min(all_l2), (max(all_l2) - min(all_l2)) or 1.0
    bw_min, bw_range = min(all_bw), (max(all_bw) - min(all_bw)) or 1.0

    codebook = {}
    for pchar, (par, comp, hom, l2, bw) in qn_full.items():
        levels = [
            np.roll(bases[0], par * (dim // 2)),
            np.roll(bases[1], (comp - 1) * (dim // 3)),
            np.roll(bases[2], hom * (dim // 2)),
            np.roll(bases[3], int((l2 - l2_min) / l2_range * dim // 2)),
            np.roll(bases[4], int((bw - bw_min) / bw_range * dim // 2)),
        ]
        codebook[pchar] = levels[0] * levels[1] * levels[2] * levels[3] * levels[4]

    return codebook


# ═══════════════════════════════════════════════════════════════
# PART 6: BENCHMARK COMPARISON
# ═══════════════════════════════════════════════════════════════

def benchmark_with_spectral_pawn(sym_analysis):
    """Re-run encoder benchmarks using the spectrally-derived pawn value.

    Compares three pawn valuations:
      1. Traditional: P = 1.0
      2. Spectral: P = mean_degree / 2.6 (from symmetric Laplacian)
      3. Codebook: proper quantum number encoding (not random)

    Uses the same KRK endgame test positions as encoder_512.py.
    """
    spectral_pawn = sym_analysis['spectral_value']

    # Build three versions of piece values
    vals_traditional = dict(SPECTRAL_VALS)  # already has P=1.0

    vals_spectral = dict(SPECTRAL_VALS)
    vals_spectral['P'] = spectral_pawn
    vals_spectral['p'] = -spectral_pawn

    # Test positions: KRK endgame (same as encoder_512 benchmark)
    test_positions = _generate_krk_positions()

    results = {}
    for label, vals in [('traditional_P=1.0', vals_traditional),
                         (f'spectral_P={spectral_pawn:.3f}', vals_spectral)]:
        encodings = []
        for pos in test_positions:
            sig = board_signal(pos, vals=vals)
            enc = np.zeros(512)
            # Use D4 projection channels (first 320 dims)
            from encoder_512 import project_irrep
            idx = 0
            for irrep in ['A1', 'A2', 'B1', 'B2', 'E']:
                proj = project_irrep(sig, irrep)
                enc[idx:idx+64] = proj
                idx += 64
            encodings.append(enc)

        # Pairwise distances
        n = len(encodings)
        dists = []
        for i in range(n):
            for j in range(i+1, n):
                dists.append(np.linalg.norm(encodings[i] - encodings[j]))

        results[label] = {
            'mean_dist': float(np.mean(dists)),
            'std_dist': float(np.std(dists)),
            'n_positions': n,
        }

    return results


def _generate_krk_positions():
    """Generate diverse test positions with pawns for benchmark comparison."""
    positions = []

    # Position 1: Starting position
    start = {0: 'r', 1: 'n', 2: 'b', 3: 'q', 4: 'k', 5: 'b', 6: 'n', 7: 'r',
             8: 'p', 9: 'p', 10: 'p', 11: 'p', 12: 'p', 13: 'p', 14: 'p', 15: 'p',
             48: 'P', 49: 'P', 50: 'P', 51: 'P', 52: 'P', 53: 'P', 54: 'P', 55: 'P',
             56: 'R', 57: 'N', 58: 'B', 59: 'Q', 60: 'K', 61: 'B', 62: 'N', 63: 'R'}
    positions.append(start)

    # Position 2: After 1.e4 e5
    pos2 = dict(start)
    del pos2[52]; pos2[36] = 'P'   # e4
    del pos2[12]; pos2[28] = 'p'   # e5
    positions.append(pos2)

    # Position 3: Sicilian structure (pawns on e4, d6, c5)
    pos3 = dict(start)
    del pos3[52]; pos3[36] = 'P'   # e4
    del pos3[10]; pos3[26] = 'p'   # ...c5
    del pos3[11]; pos3[19] = 'p'   # ...d6
    positions.append(pos3)

    # Position 4: Isolated queen pawn
    pos4 = {60: 'K', 35: 'P', 4: 'k', 27: 'p'}
    positions.append(pos4)

    # Position 5: Passed pawn (white pawn on 6th rank)
    pos5 = {60: 'K', 56: 'R', 18: 'P', 4: 'k', 7: 'r'}
    positions.append(pos5)

    # Position 6: Pawn chain (d4-e5)
    pos6 = {60: 'K', 35: 'P', 28: 'P', 4: 'k', 21: 'p', 12: 'p'}
    positions.append(pos6)

    # Position 7: Doubled pawns (two white pawns on e-file)
    pos7 = {60: 'K', 36: 'P', 28: 'P', 4: 'k', 12: 'p'}
    positions.append(pos7)

    # Position 8: Pawn majority (3v2 kingside)
    pos8 = {60: 'K', 53: 'P', 54: 'P', 55: 'P', 4: 'k', 14: 'p', 15: 'p'}
    positions.append(pos8)

    return positions


# ═══════════════════════════════════════════════════════════════
# PART 7: DISPLAY AND REPORT
# ═══════════════════════════════════════════════════════════════

def print_adjacency_summary(label, A):
    """Print key properties of an adjacency matrix."""
    n_edges = int(A.sum())
    degrees = A.sum(axis=1)
    nonzero_deg = degrees[degrees > 0]
    print(f"  {label}:")
    print(f"    Edges: {n_edges}")
    print(f"    Squares with edges: {len(nonzero_deg)}/64")
    print(f"    Degree range: [{int(nonzero_deg.min())}, {int(nonzero_deg.max())}]"
          f" (mean={nonzero_deg.mean():.2f})" if len(nonzero_deg) > 0 else "    (empty)")
    print(f"    Symmetric: {np.allclose(A, A.T)}")


def print_degree_map(A, label):
    """Print 8x8 degree map of the board."""
    print(f"\n  {label} — degree per square:")
    print(f"    {'':>4s}", end='')
    for c in range(8):
        print(f"  {'abcdefgh'[c]:>2s}", end='')
    print()
    for r in range(8):
        rank = 8 - r
        print(f"    {rank:>2d}  ", end='')
        for c in range(8):
            d = A[sq(r, c)].sum() + A[:, sq(r, c)].sum()  # in-degree + out-degree for directed
            if d > 0:
                print(f"  {d:2.0f}", end='')
            else:
                print(f"   .", end='')
        print()


def print_eigenvalue_comparison(sym_analysis, other_qn):
    """Print quantum numbers side-by-side with other pieces."""
    pawn_qn = sym_analysis['quantum_numbers']
    print(f"\n  Quantum Number 5-tuple comparison:")
    print(f"  {'Piece':>8s}  {'Parity':>6s}  {'Comp':>4s}  {'Homog':>5s}  "
          f"{'lam2':>8s}  {'BW':>6s}")
    print(f"  {'─'*8}  {'─'*6}  {'─'*4}  {'─'*5}  {'─'*8}  {'─'*6}")

    # Pawn first (highlighted)
    par, comp, hom, l2, bw = pawn_qn
    print(f"  {'Pawn':>8s}  {par:>6d}  {comp:>4d}  {hom:>5d}  {l2:>8.4f}  {bw:>6.2f}  <-- NEW")

    for pc, qn in sorted(other_qn.items()):
        names = {'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}
        par, comp, hom, l2, bw = qn
        print(f"  {names.get(pc, pc):>8s}  {par:>6d}  {comp:>4d}  {hom:>5d}  "
              f"{l2:>8.4f}  {bw:>6.2f}")


# ═══════════════════════════════════════════════════════════════
# MAIN: RUN ALL ANALYSES
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  PAWN DIRECTED LAPLACIAN: SPECTRAL CHARACTERIZATION")
    print("  The only spectrally uncharacterized piece in the framework")
    print("=" * 72)

    # ─── STEP 1: Build directed adjacency matrices ───────────────
    print(f"\n{'─'*72}")
    print(f"  STEP 1: DIRECTED ADJACENCY MATRICES")
    print(f"{'─'*72}")

    decomp = decompose_pawn()

    print_adjacency_summary("A_white (white pawn, directed)", decomp['A_white'])
    print_adjacency_summary("A_black (black pawn, directed)", decomp['A_black'])

    # Verify 180-degree rotation relationship
    rot180 = np.zeros(64, dtype=int)
    for r in range(8):
        for c in range(8):
            rot180[sq(r, c)] = sq(7 - r, 7 - c)

    A_black_from_white = decomp['A_white'][rot180][:, rot180]
    rot_check = np.allclose(A_black_from_white, decomp['A_black'])
    print(f"\n  A_black = rot180(A_white): {rot_check}")

    # IMPORTANT: Document the symmetry correction
    color_avg = decomp['color_avg']
    color_avg_asym = int(np.sum(np.abs(color_avg - color_avg.T) > 1e-10))
    print(f"\n  SYMMETRY CORRECTION:")
    print(f"    Spec proposed A_sym = (A_white + A_black) / 2")
    print(f"    This has {color_avg_asym} asymmetric elements — NOT symmetric!")
    print(f"    Reason: rot180 != transpose. A_black's edges don't reverse A_white's.")
    print(f"    Fix: Use standard transpose decomposition of A_white:")
    print(f"      A_sym  = (A_white + A_white^T) / 2  — guaranteed Hermitian")
    print(f"      A_anti = (A_white - A_white^T) / 2  — guaranteed antisymmetric")

    print_adjacency_summary("\n    A_sym = (A_w + A_w^T) / 2", decomp['A_sym'])
    print_adjacency_summary("    A_anti = (A_w - A_w^T) / 2", decomp['A_anti'])

    # Also show combined graph properties
    print(f"\n  Combined graph (both colors):")
    print_adjacency_summary("    A_combined = A_w + A_b", decomp['A_combined'])
    comb_asym = int(np.sum(np.abs(decomp['A_combined'] - decomp['A_combined'].T) > 1e-10))
    print(f"    Asymmetric elements in A_combined: {comb_asym}")
    comb_anti_norm = np.linalg.norm(decomp['A_combined_anti'], 'fro')
    comb_sym_norm = np.linalg.norm(decomp['A_combined_sym'], 'fro')
    print(f"    ||A_combined_anti|| / ||A_combined_sym|| = "
          f"{comb_anti_norm/comb_sym_norm:.4f}" if comb_sym_norm > 0 else "    (zero)")
    print(f"    (Combined graph is {'nearly' if comb_anti_norm/comb_sym_norm < 0.1 else 'NOT'} "
          f"symmetric — white+black partially cancel directionality)")

    print_degree_map(decomp['A_white'], "White pawn (directed)")
    print_degree_map(decomp['A_black'], "Black pawn (directed)")

    # ─── STEP 2: Symmetric part analysis ─────────────────────────
    print(f"\n{'─'*72}")
    print(f"  STEP 2: SYMMETRIC LAPLACIAN ANALYSIS (Z2-preserving)")
    print(f"{'─'*72}")

    sym = analyze_symmetric(decomp)

    print(f"\n  Graph properties:")
    print(f"    Mean degree: {sym['mean_degree']:.4f}")
    print(f"    Spectral pawn value: {sym['spectral_value']:.4f} "
          f"(vs traditional 1.0, vs current hardcoded 1.0)")
    print(f"    Connected components: {sym['n_components']}")
    print(f"    Algebraic connectivity (lambda_2): {sym['lambda_2']:.6f}")
    print(f"    Spectral bandwidth: {sym['bandwidth']:.4f}")
    print(f"    Degree regularity: {'regular' if sym['is_regular'] else 'irregular'} "
          f"(std={sym['degree_std']:.4f})")
    print(f"    Parity (bipartite): {sym['parity']}")

    # Comparison with other piece spectral values
    print(f"\n  Spectral value comparison (mean_degree / 2.6):")
    all_sv = {}
    for pc, pfn in SHORT_PFNS.items():
        A = build_adjacency(pfn)
        md = A.sum() / 64.0
        sv = md / 2.6
        all_sv[pc] = sv
    all_sv['P_sym'] = sym['spectral_value']

    for pc in ['P_sym', 'N', 'B', 'R', 'Q', 'K']:
        names = {'P_sym': 'Pawn(sym)', 'N': 'Knight', 'B': 'Bishop',
                 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}
        marker = " <-- NEW" if pc == 'P_sym' else ""
        print(f"    {names[pc]:>12s}: {all_sv[pc]:.4f}{marker}")

    # Quantum numbers
    other_qn = compute_quantum_numbers()
    print_eigenvalue_comparison(sym, other_qn)

    # Check uniqueness
    all_qn = dict(other_qn)
    all_qn['P'] = sym['quantum_numbers']
    qn_set = set(all_qn.values())
    print(f"\n  Quantum number uniqueness: {len(qn_set)} unique tuples "
          f"from {len(all_qn)} pieces → "
          f"{'COMPLETE classification' if len(qn_set) == len(all_qn) else 'COLLISION detected!'}")

    if len(qn_set) < len(all_qn):
        # Find collisions
        from collections import Counter
        counts = Counter(all_qn.values())
        for qn_tuple, count in counts.items():
            if count > 1:
                colliders = [k for k, v in all_qn.items() if v == qn_tuple]
                print(f"    COLLISION: {colliders} share {qn_tuple}")

    # Eigenvalue spectrum
    print(f"\n  L_sym eigenvalue spectrum (first 10):")
    for i, ev in enumerate(sym['evals_sym'][:10]):
        print(f"    lambda_{i}: {ev:.6f}")
    print(f"    ... (64 total, last = {sym['evals_sym'][-1]:.6f})")

    # Fiber analysis
    print(f"\n  Fiber analysis (projection onto board eigenbasis):")
    print(f"    Fiber vector norm: {sym['fiber_norm']:.6f}")
    print(f"    Off-diagonal energy fraction: {sym['off_diag_fraction']:.4f}")
    print(f"    Fiber 3D coordinates: [{sym['fiber_3d'][0]:.4f}, "
          f"{sym['fiber_3d'][1]:.4f}, {sym['fiber_3d'][2]:.4f}]")
    print(f"\n    Cosine similarity with other piece fibers:")
    for name, sim in sorted(sym['fiber_sims'].items()):
        print(f"      vs {name:>8s}: {sim:+.4f}")

    # ─── STEP 3: Antisymmetric part analysis ─────────────────────
    print(f"\n{'─'*72}")
    print(f"  STEP 3: ANTISYMMETRIC ANALYSIS (Z2-breaking)")
    print(f"{'─'*72}")

    anti = analyze_antisymmetric(decomp)

    print(f"\n  Eigenvalue properties:")
    print(f"    Pure imaginary: {anti['is_pure_imaginary']} "
          f"(max |Re| = {anti['max_real']:.2e})")
    print(f"    Conjugate pairs: {anti['n_imaginary_pairs']}")

    if len(anti['top_imag_eigenvalues']) > 0:
        print(f"    Top |Im| eigenvalues:")
        for i, v in enumerate(anti['top_imag_eigenvalues'][:6]):
            print(f"      +/-i * {v:.6f}")

    print(f"\n  Norm comparison:")
    print(f"    ||A_anti||_F = {anti['norm_anti']:.6f}")
    print(f"    ||A_sym||_F  = {anti['norm_sym']:.6f}")
    print(f"    Ratio ||anti||/||sym|| = {anti['anti_sym_ratio']:.4f}")
    print(f"    (ratio > 1 means directionality dominates symmetry)")

    print(f"\n  Fiber orthogonality:")
    print(f"    A_anti fiber norm: {anti['fiber_anti_norm']:.6f}")
    print(f"    cos(fiber_sym, fiber_anti) = {anti['sym_anti_fiber_cos']:.6f}")
    print(f"    (0 = orthogonal, meaning sym and anti live in different fiber subspaces)")
    print(f"\n    A_anti fiber similarity with other pieces:")
    for name, sim in sorted(anti['fiber_anti_sims'].items()):
        print(f"      vs {name:>8s}: {sim:+.4f}")

    # ─── STEP 4: Movement vs Capture separation ─────────────────
    print(f"\n{'─'*72}")
    print(f"  STEP 4: MOVEMENT vs CAPTURE GRAPH SEPARATION")
    print(f"{'─'*72}")

    mc = analyze_movement_vs_capture()

    print(f"\n  Additivity check: ||A_move + A_capt - A_sym|| = "
          f"{mc['additivity_error']:.2e}")

    for label in ['move', 'capture']:
        r = mc[label]
        print(f"\n  {label.upper()} sub-graph (symmetrized):")
        print(f"    Mean degree: {r['mean_degree']:.4f}")
        print(f"    Spectral value: {r['spectral_value']:.4f}")
        print(f"    Components: {r['n_components']}")
        print(f"    lambda_2: {r['lambda_2']:.6f}")
        print(f"    Bandwidth: {r['bandwidth']:.4f}")
        print(f"    Fiber norm: {r['fiber_norm']:.4f}")

    print(f"\n  Move-capture fiber cosine: {mc['move_capture_fiber_cos']:.4f}")
    print(f"  (1 = identical structure, 0 = orthogonal, -1 = opposite)")

    # ─── STEP 5: Updated codebook ────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  STEP 5: QUANTUM NUMBER CODEBOOK UPDATE")
    print(f"{'─'*72}")

    qn_full = compute_full_quantum_numbers(sym)
    cb_full = build_full_codebook(qn_full)

    # Also build the old codebook (with random pawn)
    cb_old = build_codebook_qn()

    # Cross-piece similarity comparison
    pieces = ['P', 'N', 'B', 'R', 'Q', 'K']

    print(f"\n  Cross-piece cosine similarity (NEW codebook with spectral pawn):")
    print(f"  {'':>6s}", end='')
    for p2 in pieces:
        print(f"  {p2:>5s}", end='')
    print()

    for p1 in pieces:
        print(f"  {p1:>5s} ", end='')
        for p2 in pieces:
            if p1 == p2:
                print(f"  {'1.00':>5s}", end='')
            else:
                c = float(cb_full[p1] @ cb_full[p2] /
                          (np.linalg.norm(cb_full[p1]) * np.linalg.norm(cb_full[p2])))
                print(f"  {c:+.3f}", end='')
        print()

    # Compare pawn's similarity with old (random) vs new (spectral)
    print(f"\n  Pawn codebook comparison (old random vs new spectral):")
    for p2 in ['N', 'B', 'R', 'Q', 'K']:
        old_sim = float(cb_old['P'] @ cb_old[p2] /
                        (np.linalg.norm(cb_old['P']) * np.linalg.norm(cb_old[p2])))
        new_sim = float(cb_full['P'] @ cb_full[p2] /
                        (np.linalg.norm(cb_full['P']) * np.linalg.norm(cb_full[p2])))
        print(f"    P vs {p2}: old={old_sim:+.3f}, new={new_sim:+.3f}")

    # ─── STEP 6: Benchmark comparison ────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  STEP 6: BENCHMARK WITH SPECTRAL PAWN VALUE")
    print(f"{'─'*72}")

    bench = benchmark_with_spectral_pawn(sym)

    for label, data in bench.items():
        print(f"\n  {label}:")
        print(f"    Mean pairwise distance: {data['mean_dist']:.4f}")
        print(f"    Std pairwise distance:  {data['std_dist']:.4f}")
        print(f"    Test positions: {data['n_positions']}")

    # ─── SUMMARY ─────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  SUMMARY")
    print(f"{'='*72}")

    print(f"""
  1. SPECTRAL PAWN VALUE: {sym['spectral_value']:.4f}
     (from symmetric Laplacian mean_degree / 2.6)
     Traditional: 1.0, Difference: {abs(sym['spectral_value'] - 1.0):.4f}

  2. QUANTUM NUMBERS: {sym['quantum_numbers']}
     Unique among all 6 pieces: {len(qn_set) == len(all_qn)}

  3. Z2 BREAKING (antisymmetric part):
     ||A_anti|| / ||A_sym|| = {anti['anti_sym_ratio']:.4f}
     Fiber orthogonality: cos = {anti['sym_anti_fiber_cos']:.4f}
     Pure imaginary eigenvalues: {anti['is_pure_imaginary']}, {anti['n_imaginary_pairs']} pairs

  4. MOVEMENT vs CAPTURE:
     Move spectral value:    {mc['move']['spectral_value']:.4f}
     Capture spectral value: {mc['capture']['spectral_value']:.4f}
     Fiber cosine:           {mc['move_capture_fiber_cos']:.4f}

  5. FIBER COORDINATES (3D):
     [{sym['fiber_3d'][0]:.4f}, {sym['fiber_3d'][1]:.4f}, {sym['fiber_3d'][2]:.4f}]
     Closest piece: {max(sym['fiber_sims'], key=lambda k: abs(sym['fiber_sims'][k]))} """
          f"(cos={sym['fiber_sims'][max(sym['fiber_sims'], key=lambda k: abs(sym['fiber_sims'][k]))]:+.4f})")

    print(f"\n{'='*72}")
    print(f"  PAWN SPECTRAL CHARACTERIZATION COMPLETE")
    print(f"{'='*72}")

    return {
        'decomp': decomp,
        'symmetric': sym,
        'antisymmetric': anti,
        'movement_capture': mc,
        'quantum_numbers_full': qn_full,
        'codebook_full': cb_full,
        'benchmark': bench,
    }


if __name__ == '__main__':
    results = main()
