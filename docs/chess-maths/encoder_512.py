#!/usr/bin/env python3
"""
Chess Spectral Encoder: 512-Dimensional HDC Architecture
=========================================================

Full encoder combining D4 irreducible representations with
fiber bundle interaction channels.

Architecture: 8 channels × 64 dimensions = 512
  Channels 1-5: D4 irrep projections (A₁, A₂, B₁, B₂, E)
  Channels 6-8: Fiber-weighted interaction fields (3 fiber dims)

Piece codebook: quantum number 5-tuple mapped to 512-space
via sparse bipolar HDC encoding with level coding.

Position similarity benchmark against heuristic endgame
evaluations (proxy for tablebase DTM).

Dependencies: numpy >= 1.24, scipy >= 1.10
Run: python3 encoder_512.py
"""

import numpy as np
from scipy.linalg import eigh, svd
from scipy.stats import spearmanr
import warnings
import sys
import io
warnings.filterwarnings('ignore')

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

np.random.seed(42)

# ═══════════════════════════════════════════════════════════════
# PREAMBLE
# ═══════════════════════════════════════════════════════════════

def sq(r, c): return r * 8 + c
def rc(s): return s // 8, s % 8
def sqname(s): return 'abcdefgh'[s % 8] + str(8 - s // 8)

def knight_targets(r, c):
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8: yield nr, nc

def bishop_targets(r, c):
    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8: yield nr, nc; nr += dr; nc += dc

def rook_targets(r, c):
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8: yield nr, nc; nr += dr; nc += dc

def queen_targets(r, c):
    yield from bishop_targets(r, c); yield from rook_targets(r, c)

def king_targets(r, c):
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0: continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8: yield nr, nc

PIECE_FNS = {'Knight': knight_targets, 'King': king_targets,
             'Bishop': bishop_targets, 'Rook': rook_targets, 'Queen': queen_targets}
SHORT_PFNS = {'N': knight_targets, 'B': bishop_targets, 'R': rook_targets,
              'Q': queen_targets, 'K': king_targets}
VALS = {'P': 1, 'N': 3, 'B': 3.5, 'R': 5, 'Q': 9, 'K': 100,
        'p': -1, 'n': -3, 'b': -3.5, 'r': -5, 'q': -9, 'k': -100}


def build_adjacency(fn):
    A = np.zeros((64, 64))
    for r in range(8):
        for c in range(8):
            for tr, tc in fn(r, c): A[sq(r, c), sq(tr, tc)] = 1
    return A

def graph_laplacian(A):
    return np.diag(A.sum(axis=1)) - A

# Board eigenbasis
A_GRID = np.zeros((64, 64))
for _r in range(8):
    for _c in range(8):
        for _dr, _dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            _nr, _nc = _r + _dr, _c + _dc
            if 0 <= _nr < 8 and 0 <= _nc < 8:
                A_GRID[sq(_r, _c), sq(_nr, _nc)] = 1
L_GRID = graph_laplacian(A_GRID)
EVALS_GRID, EVECS_GRID = eigh(L_GRID)


# ─── Spectrally-derived piece values ──────────────────────────
# Traditional values are human heuristics with zero spectral grounding.
# K=100 conflates game rules (losing king = losing game) with movement
# properties. The king is actually the WEAKEST mover spectrally
# (mean degree ~5.25, lowest algebraic connectivity of all pieces).
#
# Spectral values use mean_degree / 2.6 as the value scale:
#   mean_degree = (1/64) * sum of degrees across all squares
# The 2.6 divisor normalizes so that a pawn ~ 1.
# Dynamic range drops from 100x to ~3.5x.

def _compute_spectral_vals():
    """Derive piece values from movement graph mean degree."""
    spectral = {}
    for pchar, pfn in SHORT_PFNS.items():
        A = build_adjacency(pfn)
        mean_deg = A.sum() / 64.0
        spectral[pchar] = round(mean_deg / 2.6, 1)
    # Pawn: no full movement graph yet; use 1.0
    spectral['P'] = 1.0
    return spectral

_SV = _compute_spectral_vals()
SPECTRAL_VALS = {
    'P': _SV['P'], 'N': _SV['N'], 'B': _SV['B'],
    'R': _SV['R'], 'Q': _SV['Q'], 'K': _SV['K'],
    'p': -_SV['P'], 'n': -_SV['N'], 'b': -_SV['B'],
    'r': -_SV['R'], 'q': -_SV['Q'], 'k': -_SV['K'],
}


# ─── D4 symmetry ───────────────────────────────────────────────

def make_perm(g):
    p = np.zeros(64, dtype=int)
    for r in range(8):
        for c in range(8):
            if   g == 0: nr, nc = r, c
            elif g == 1: nr, nc = c, 7 - r
            elif g == 2: nr, nc = 7 - r, 7 - c
            elif g == 3: nr, nc = 7 - c, r
            elif g == 4: nr, nc = r, 7 - c
            elif g == 5: nr, nc = 7 - r, c
            elif g == 6: nr, nc = c, r
            elif g == 7: nr, nc = 7 - c, 7 - r
            p[sq(r, c)] = sq(nr, nc)
    return p

D4_PERMS = [make_perm(g) for g in range(8)]

CHARS = {
    'A1': [1, 1, 1, 1, 1, 1, 1, 1],
    'A2': [1, 1, 1, 1,-1,-1,-1,-1],
    'B1': [1,-1, 1,-1, 1,-1, 1,-1],
    'B2': [1,-1, 1,-1,-1, 1,-1, 1],
    'E':  [2, 0,-2, 0, 0, 0, 0, 0],
}

def board_signal(pos, vals=None):
    """64-dim board signal. vals defaults to VALS (traditional)."""
    if vals is None: vals = VALS
    s = np.zeros(64)
    for si, p in pos.items(): s[si] = vals[p]
    return s

def project_irrep(sig, irrep_name):
    """Project signal onto D4 irrep using character formula (Serre §2.6)."""
    chars = CHARS[irrep_name]
    dim_mu = 2 if irrep_name == 'E' else 1
    projected = np.zeros(64)
    for g_idx, perm in enumerate(D4_PERMS):
        projected += chars[g_idx] * sig[perm]
    return (dim_mu / 8) * projected


# ─── Fiber bundle ──────────────────────────────────────────────

upper_idx = np.triu_indices(64, k=1)
fibers_global = {}
for _name in ['Knight', 'King', 'Bishop', 'Queen']:
    _A = build_adjacency(PIECE_FNS[_name])
    _L = graph_laplacian(_A)
    _C = EVECS_GRID.T @ _L @ EVECS_GRID
    _C_off = _C.copy(); np.fill_diagonal(_C_off, 0)
    fibers_global[_name] = _C_off[upper_idx]

_fiber_mat = np.array([fibers_global[n] / np.linalg.norm(fibers_global[n])
                       for n in fibers_global])
_, S_fib, Vt_fib = svd(_fiber_mat, full_matrices=False)
FIBER_BASIS = Vt_fib[:3].T  # (2016, 3)

LOCAL_FIBER_3D = {}
LOCAL_ADJ_ROWS = {}
for _pc, _fn in SHORT_PFNS.items():
    for _s in range(64):
        _r, _c = rc(_s)
        _A_loc = np.zeros((64, 64))
        for _tr, _tc in _fn(_r, _c):
            _t = sq(_tr, _tc)
            _A_loc[_s, _t] = 1; _A_loc[_t, _s] = 1
        LOCAL_ADJ_ROWS[(_pc, _s)] = _A_loc[_s]
        _C_loc = EVECS_GRID.T @ _A_loc @ EVECS_GRID
        _C_off = _C_loc.copy(); np.fill_diagonal(_C_off, 0)
        LOCAL_FIBER_3D[(_pc, _s)] = _C_off[upper_idx] @ FIBER_BASIS

print(f"Infrastructure ready: fiber σ=[{S_fib[0]:.3f}, {S_fib[1]:.3f}, "
      f"{S_fib[2]:.3f}, {S_fib[3]:.4f}], {len(LOCAL_FIBER_3D)} local fibers cached")


# ═══════════════════════════════════════════════════════════════
# PART 1: THE 512-DIM ENCODER
#
# 8 channels × 64 dims = 512
#   Ch 1-5: D4 irrep projections of the board signal
#     A₁ is D4-INVARIANT (identical for rotated/reflected positions)
#     A₂, B₁, B₂, E transform as their respective representations
#   Ch 6-8: Fiber interaction fields (one per fiber dimension)
#     For each piece, compute field gradient (what material it sees),
#     multiply by the piece's fiber coordinate, and broadcast to all
#     reachable squares via the adjacency row.
#     field_d[k] = Σ_{pieces j} gradient_j · fib_j[d] · adj_j[k]
# ═══════════════════════════════════════════════════════════════

def encode_512(pos):
    """512-dimensional spectral fiber encoding."""
    sig = board_signal(pos)

    # Channels 1-5: D4 irrep projections (5 × 64 = 320 dims)
    channels = [project_irrep(sig, name) for name in ['A1', 'A2', 'B1', 'B2', 'E']]

    # Channels 6-8: Fiber interaction fields (3 × 64 = 192 dims)
    for d in range(3):
        fc = np.zeros(64)
        for si, pchar in pos.items():
            pkey = pchar.upper()
            if pkey not in SHORT_PFNS:
                continue  # pawns: no movement Laplacian yet
            fib_d = LOCAL_FIBER_3D[(pkey, si)][d]
            adj_row = LOCAL_ADJ_ROWS[(pkey, si)]
            gradient = float(adj_row @ sig)  # total material seen
            fc += gradient * fib_d * adj_row  # broadcast to reachable squares
        channels.append(fc)

    return np.concatenate(channels)


def encode_512_spectral(pos):
    """512-dimensional encoding using spectrally-derived piece values.
    Identical architecture to encode_512 but uses SPECTRAL_VALS
    (mean_degree/2.6) instead of traditional VALS (K=100 heuristic).
    King contributes proportionally to its movement ability, not
    its game-theoretic importance."""
    sig = board_signal(pos, vals=SPECTRAL_VALS)

    # Channels 1-5: D4 irrep projections (5 x 64 = 320 dims)
    channels = [project_irrep(sig, name) for name in ['A1', 'A2', 'B1', 'B2', 'E']]

    # Channels 6-8: Fiber interaction fields (3 x 64 = 192 dims)
    for d in range(3):
        fc = np.zeros(64)
        for si, pchar in pos.items():
            pkey = pchar.upper()
            if pkey not in SHORT_PFNS:
                continue
            fib_d = LOCAL_FIBER_3D[(pkey, si)][d]
            adj_row = LOCAL_ADJ_ROWS[(pkey, si)]
            gradient = float(adj_row @ sig)
            fc += gradient * fib_d * adj_row
        channels.append(fc)

    return np.concatenate(channels)


def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na > 1e-15 and nb > 1e-15 else 0.0


# Comparison encoders
def encode_raw(pos):
    """Raw 64-dim board signal."""
    return board_signal(pos)

def encode_raw_spectral(pos):
    """Raw 64-dim board signal with spectral values."""
    return board_signal(pos, vals=SPECTRAL_VALS)

def encode_A1(pos):
    """64-dim D4-invariant encoding (A₁ irrep only)."""
    return project_irrep(board_signal(pos), 'A1')

def encode_A1_spectral(pos):
    """64-dim D4-invariant with spectral values."""
    return project_irrep(board_signal(pos, vals=SPECTRAL_VALS), 'A1')

def encode_320(pos):
    """320-dim D4-equivariant (5 irreps × 64)."""
    sig = board_signal(pos)
    return np.concatenate([project_irrep(sig, n) for n in ['A1', 'A2', 'B1', 'B2', 'E']])


# ═══════════════════════════════════════════════════════════════
# PART 2: QUANTUM NUMBER CODEBOOK
#
# Each piece type has a unique 5-tuple of spectral quantum numbers:
#   (parity, topology, homogeneity, λ₂, bandwidth)
# mapped to 512-space via HDC level coding.
#
# Level coding: each QN dimension has a bipolar base vector.
# Values encoded as cyclic permutations of the base vector.
# Final codebook entry = element-wise product (binding) of all 5.
# ═══════════════════════════════════════════════════════════════

def compute_quantum_numbers():
    """Spectral quantum number 5-tuple per piece type.
    Returns {piece_char: (parity, n_comp, homogeneity, λ₂, bandwidth)}.
    All tuples are unique → complete classification (CONFIRMED).
    """
    qn = {}
    for pchar, pname in [('N', 'Knight'), ('B', 'Bishop'), ('R', 'Rook'),
                          ('Q', 'Queen'), ('K', 'King')]:
        A = build_adjacency(PIECE_FNS[pname])
        L = graph_laplacian(A)
        evals, _ = eigh(L)

        # Parity: bipartiteness from adjacency spectrum symmetry
        evals_A = np.sort(np.linalg.eigvals(A).real)
        pos_ev = evals_A[evals_A > 0.01]
        neg_ev = -evals_A[evals_A < -0.01]
        nm = min(len(pos_ev), len(neg_ev))
        sym_err = (np.linalg.norm(np.sort(pos_ev)[:nm] - np.sort(neg_ev)[:nm])
                   if nm > 0 else float('inf'))

        # Degree distribution
        d = A.sum(axis=1)
        nonzero = evals[evals > 1e-10]

        qn[pchar] = (
            int(sym_err < 0.01),                                       # parity
            int(np.sum(np.abs(evals) < 1e-10)),                        # components
            int(np.std(d) < 0.01),                                     # homogeneity
            round(float(nonzero[0]) if len(nonzero) > 0 else 0, 4),   # λ₂
            round(float(evals[-1]), 2),                                # bandwidth
        )
    return qn


def build_codebook_qn(dim=512):
    """512-dim bipolar codebook from quantum numbers via HDC level coding."""
    qn = compute_quantum_numbers()
    rng = np.random.RandomState(2024)

    # 5 random bipolar base vectors (one per quantum number dimension)
    bases = [rng.choice([-1, 1], size=dim).astype(float) for _ in range(5)]

    # Normalization ranges for continuous QNs
    all_l2 = [v[3] for v in qn.values()]
    all_bw = [v[4] for v in qn.values()]
    l2_min, l2_range = min(all_l2), (max(all_l2) - min(all_l2)) or 1.0
    bw_min, bw_range = min(all_bw), (max(all_bw) - min(all_bw)) or 1.0

    codebook = {}
    for pchar, (par, comp, hom, l2, bw) in qn.items():
        levels = [
            np.roll(bases[0], par * (dim // 2)),
            np.roll(bases[1], (comp - 1) * (dim // 3)),
            np.roll(bases[2], hom * (dim // 2)),
            np.roll(bases[3], int((l2 - l2_min) / l2_range * dim // 2)),
            np.roll(bases[4], int((bw - bw_min) / bw_range * dim // 2)),
        ]
        codebook[pchar] = levels[0] * levels[1] * levels[2] * levels[3] * levels[4]

    # Pawn: random bipolar (no movement Laplacian in this framework)
    codebook['P'] = rng.choice([-1, 1], size=dim).astype(float)
    return codebook


def build_codebook_eigenvalue(dim=512):
    """Old approach: eigenvalue sequence codebook. Cross-piece sim > 0.92."""
    codebook = {}
    for pchar, pname in [('N', 'Knight'), ('B', 'Bishop'), ('R', 'Rook'),
                          ('Q', 'Queen'), ('K', 'King')]:
        A = build_adjacency(PIECE_FNS[pname])
        L = graph_laplacian(A)
        evals, _ = eigh(L)
        code = np.zeros(dim)
        code[:len(evals)] = evals
        code /= np.linalg.norm(code)
        codebook[pchar] = code
    rng_p = np.random.RandomState(999)
    codebook['P'] = rng_p.randn(dim)
    codebook['P'] /= np.linalg.norm(codebook['P'])
    return codebook


# ─── Diffusion impulse-response square codebook ─────────────────
# Each square s gets a 512-dim fingerprint by pushing δ_s through
# the 8-channel encoder architecture with diffusion kernel weighting.
#
# The heat kernel exp(-t·L) applied to δ_s gives a smooth spatial
# fingerprint: nearby squares share similar Laplacian eigenvector
# values → similar diffused impulses → natural spatial structure.
#
# Channels 1-5 (320d): D4 irrep projections of diffused delta
# Channels 6-8 (192d): multi-scale diffusion (2t, 4t, 8t)
#
# Diffusion time t calibrated so grid-adjacent squares have ~0.5
# cosine similarity. (Serre-style: the spatial structure IS the code.)
#
# For HDC binding/unbinding, coprime cyclic permutation replaces
# element-wise multiply. Square s binds via np.roll(piece_vec, offset_s)
# where offset_s = row * COPRIME_ROW + col * COPRIME_COL (mod 512).
# This is the UTLP S3 pattern: coprime offsets guarantee all 64 squares
# map to distinct roll positions, and 2D spatial proximity is preserved
# (adjacent squares differ by one coprime stride in roll space).
# ─────────────────────────────────────────────────────────────────

from math import gcd

# 2D coprime roll offsets for spatial binding (UTLP S3 pattern)
# Row and column proximity → roll distance in 512-dim circular space.
# Both must be coprime to 512 (= 2^9), i.e. odd.
# Chosen so 64 values {67r + 7c mod 512 : r,c ∈ [0,7]} are all distinct.
COPRIME_ROW = 67
COPRIME_COL = 7

# Verify: all 64 roll offsets are distinct
_roll_offsets = [(r * COPRIME_ROW + c * COPRIME_COL) % 512 for r in range(8) for c in range(8)]
assert len(set(_roll_offsets)) == 64, "Coprime offsets produce collisions!"
assert gcd(COPRIME_ROW, 512) == 1 and gcd(COPRIME_COL, 512) == 1, "Not coprime to 512!"


def square_roll_offset(s):
    """Map square index to coprime roll offset encoding 2D grid position.
    Adjacent squares differ by COPRIME_ROW (vertical) or COPRIME_COL (horizontal)."""
    r, c = rc(s)
    return (r * COPRIME_ROW + c * COPRIME_COL) % 512


def _diffuse_delta(s, t):
    """Heat kernel on grid applied to delta at square s.
    Returns 64-dim signal: exp(-tL) δ_s = Σ_k exp(-t·λ_k) · φ_k(s) · φ_k
    where φ_k are the grid Laplacian eigenvectors."""
    coeffs = np.exp(-t * EVALS_GRID) * EVECS_GRID[s, :]
    return EVECS_GRID @ coeffs


def _build_fingerprint(s, t):
    """512-dim square fingerprint at diffusion time t (same as codebook)."""
    channels = []
    diffused = _diffuse_delta(s, t)
    for name in ['A1', 'A2', 'B1', 'B2', 'E']:
        channels.append(project_irrep(diffused, name))
    for scale in [2.0, 4.0, 8.0]:
        channels.append(_diffuse_delta(s, t * scale))
    return np.concatenate(channels)


def _calibrate_diffusion_time(target_sim=0.5):
    """Binary search for diffusion time t such that mean cosine
    similarity between grid-adjacent 512-dim fingerprints ≈ target_sim."""
    adj_pairs = []
    for r in range(8):
        for c in range(8):
            for dr, dc in [(0, 1), (1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    adj_pairs.append((sq(r, c), sq(nr, nc)))

    def mean_adj_sim(t):
        vecs = [_build_fingerprint(s, t) for s in range(64)]
        return np.mean([cosine(vecs[a], vecs[b]) for a, b in adj_pairs])

    # Similarity increases monotonically with t:
    # t=0: delta functions are orthogonal (sim=0)
    # t→∞: all converge to uniform distribution (sim=1)
    # So to DECREASE similarity, DECREASE t.
    lo, hi = 0.001, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        sim = mean_adj_sim(mid)
        if sim > target_sim:
            hi = mid   # too similar → less diffusion
        else:
            lo = mid   # not similar enough → more diffusion
    return (lo + hi) / 2


DIFFUSION_TIME = _calibrate_diffusion_time(0.5)


def build_square_codebook():
    """512-dim impulse-response fingerprints with diffusion weighting.

    For each square s, push diffused δ_s through all 8 encoder channels:
      Channels 1-5 (320d): D4 irrep projections of exp(-tL) δ_s
      Channels 6-8 (192d): diffusion at 2t, 4t, 8t (multi-scale structure)

    The result IS the square's spectral fingerprint — nearby squares
    share similar eigenvector values → similar fingerprints → natural
    spatial structure without any random projection.
    """
    t = DIFFUSION_TIME
    codebook = {}
    for s in range(64):
        channels = []
        # Channels 1-5: D4 irrep projections of diffused impulse
        diffused = _diffuse_delta(s, t)
        for name in ['A1', 'A2', 'B1', 'B2', 'E']:
            channels.append(project_irrep(diffused, name))
        # Channels 6-8: multi-scale diffusion (coarser spatial scales)
        for scale in [2.0, 4.0, 8.0]:
            channels.append(_diffuse_delta(s, t * scale))
        codebook[s] = np.concatenate(channels)
    return codebook


SQUARE_CODEBOOK = build_square_codebook()

print(f"Square codebook: t={DIFFUSION_TIME:.4f}, "
      f"adj_sim={np.mean([cosine(SQUARE_CODEBOOK[sq(r,c)], SQUARE_CODEBOOK[sq(r,c+1)]) for r in range(8) for c in range(7)]):.3f}, "
      f"coprime=({COPRIME_ROW},{COPRIME_COL})")


def encode_hdc(pos, piece_codebook, balanced=False):
    """HDC board encoding with coprime roll binding.

    Binding: np.roll(piece_vec, square_roll_offset(s))
    Coprime roll preserves spatial structure: adjacent squares get
    nearby roll offsets, so interference from neighbors is correlated
    rather than random. Roll is its own inverse (roll by -n to unbind).

    balanced=False: weight = VALS[pchar] (material-weighted, for similarity)
    balanced=True:  weight = ±1 (unit per piece, optimal for unbinding)
    """
    enc = np.zeros(512)
    for si, pchar in pos.items():
        ptype = pchar.upper()
        if balanced:
            weight = 1.0 if pchar.isupper() else -1.0
        else:
            weight = VALS[pchar]
        bound = np.roll(piece_codebook[ptype], square_roll_offset(si))
        enc += weight * bound
    return enc


def query_square(enc, square, piece_codebook):
    """Unbind a square via reverse coprime roll, then match piece type.
    Returns (best_match, similarity_dict)."""
    offset = square_roll_offset(square)
    unbound = np.roll(enc, -offset)
    sims = {pt: cosine(unbound, code) for pt, code in piece_codebook.items()}
    best = max(sims, key=sims.get)
    return best, sims


# ═══════════════════════════════════════════════════════════════
# PART 3: POSITION EVALUATION & BENCHMARK
#
# Three evaluation layers, from shallow to deep:
#
#   1. MATERIAL: raw piece count (P=100, N=320, ... centipawns)
#      Tests: does the encoding see material balance?
#      Expected: traditional VALS win (they ARE material weights)
#
#   2. POSITIONAL (PST): piece-square table bonuses (centipawns)
#      Tests: does the encoding see piece activity/placement?
#      Expected: spectral values may correlate better (they measure
#      movement structure, not material worth)
#
#   3. COMBINED: material + positional (what engines compute)
#      Tests: overall evaluation quality
#      Expected: traditional wins when material dominates;
#      spectral wins when positions have equal material
#
#   4. STOCKFISH: centipawn from engine (if available)
#      Tests: correlation with real chess understanding
#
# The key question: does spectral encoding capture POSITIONAL
# quality (piece activity, connectivity, coordination) that
# material counting misses?
# ═══════════════════════════════════════════════════════════════

# Piece-square tables (centipawns, from White's perspective)
# Source: Tomasz Michniewski's simplified evaluation
# Index mapping: our sq(r,c) where r=0 is rank 8, r=7 is rank 1
# These tables are written WITH our indexing (row 0 = rank 8 at top)

PST_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,   # rank 8 (never here)
    50, 50, 50, 50, 50, 50, 50, 50,   # rank 7 (about to promote)
    10, 10, 20, 30, 30, 20, 10, 10,   # rank 6
     5,  5, 10, 25, 25, 10,  5,  5,   # rank 5
     0,  0,  0, 20, 20,  0,  0,  0,   # rank 4
     5, -5,-10,  0,  0,-10, -5,  5,   # rank 3
     5, 10, 10,-20,-20, 10, 10,  5,   # rank 2
     0,  0,  0,  0,  0,  0,  0,  0,   # rank 1 (never here)
]

PST_KNIGHT = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
]

PST_BISHOP = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
]

PST_ROOK = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

PST_QUEEN = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
]

PST_KING_MG = [  # middlegame: stay castled
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
]

PST_TABLES = {'P': PST_PAWN, 'N': PST_KNIGHT, 'B': PST_BISHOP,
              'R': PST_ROOK, 'Q': PST_QUEEN, 'K': PST_KING_MG}

# Material values in centipawns (standard)
MATERIAL_CP = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
# King has 0 material value — both sides always have one,
# so it contributes nothing to material balance.


def pst_eval(pos):
    """Decomposed evaluation: (material_cp, positional_cp, total_cp).
    Material: piece counts in centipawns (K=0, cancels out).
    Positional: piece-square table bonuses only.
    Returns white's perspective."""
    material = 0
    positional = 0
    for si, pchar in pos.items():
        ptype = pchar.upper()
        sign = 1 if pchar.isupper() else -1

        # Material component
        material += sign * MATERIAL_CP.get(ptype, 0)

        # Positional component (PST)
        pst = PST_TABLES.get(ptype)
        if pst is not None:
            if pchar.isupper():
                positional += pst[si]                   # white: use directly
            else:
                # black: mirror vertically (row 0↔7, 1↔6, etc.)
                r, c = rc(si)
                mirror_sq = sq(7 - r, c)
                positional -= pst[mirror_sq]

    return material, positional, material + positional


def heuristic_eval(pos, vals=None):
    """Legacy evaluation: material + centralization + mobility."""
    if vals is None: vals = VALS
    score = 0.0
    for si, pchar in pos.items():
        r, c = rc(si)
        v = vals[pchar]
        score += v
        sign = 1 if pchar.isupper() else -1
        center_dist = abs(r - 3.5) + abs(c - 3.5)
        cap = min(abs(v), 10) if vals is VALS else abs(v)
        score += sign * (7 - center_dist) * 0.1 * cap
        pkey = pchar.upper()
        if pkey in SHORT_PFNS:
            score += sign * sum(1 for _ in SHORT_PFNS[pkey](r, c)) * 0.05
    return score


# ─── Stockfish integration (optional) ─────────────────────────

def pos_to_fen(pos):
    """Convert our position dict to FEN string (no castling/ep/clocks)."""
    rows = []
    for r in range(8):
        row = ''
        empty = 0
        for c in range(8):
            s = sq(r, c)
            if s in pos:
                if empty > 0:
                    row += str(empty)
                    empty = 0
                row += pos[s]
            else:
                empty += 1
        if empty > 0:
            row += str(empty)
        rows.append(row)
    return '/'.join(rows) + ' w - - 0 1'


STOCKFISH_PATH = r'C:\AI_PROJECTS\stockfish\stockfish-windows-x86-64-avx2.exe'


def stockfish_eval_batch(pos_list, depth=12):
    """Evaluate a list of position dicts with Stockfish.
    Returns list of centipawn scores, or None if unavailable.
    Skips illegal positions (returns None for those entries)."""
    try:
        import chess
        import chess.engine
    except ImportError:
        return None

    scores = []
    engine = None
    for pos in pos_list:
        fen = pos_to_fen(pos)
        board = chess.Board(fen)

        # Validate position before sending to engine
        if not board.is_valid():
            scores.append(None)
            continue

        try:
            if engine is None:
                engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
            score = info['score'].white()
            if score.is_mate():
                cp = 10000 * (1 if score.mate() > 0 else -1)
            else:
                cp = score.score()
            scores.append(cp)
        except Exception:
            scores.append(None)
            # Engine may have died — will reopen on next valid position
            try:
                engine.quit()
            except Exception:
                pass
            engine = None

    if engine is not None:
        try:
            engine.quit()
        except Exception:
            pass

    return scores


def krk_eval(wk, wr, bk):
    """KRK endgame heuristic (proxy for distance-to-mate).
    Higher = closer to checkmate = better for White.
    Correlates with actual DTM for standard KRK positions."""
    wk_r, wk_c = rc(wk)
    wr_r, wr_c = rc(wr)
    bk_r, bk_c = rc(bk)
    rank_edge = min(bk_r, 7 - bk_r)
    file_edge = min(bk_c, 7 - bk_c)
    edge_push = 6 - rank_edge - file_edge
    king_prox = 7 - max(abs(wk_r - bk_r), abs(wk_c - bk_c))
    rook_cut = 0
    if wr_r != bk_r and abs(wr_r - bk_r) <= 2: rook_cut += 1
    if wr_c != bk_c and abs(wr_c - bk_c) <= 2: rook_cut += 1
    return 10 * edge_push + 5 * king_prox + 3 * rook_cut


def generate_equal_material_positions(n=60):
    """Positions with IDENTICAL material but varied placement.
    This isolates the POSITIONAL signal: material contribution is constant,
    so any correlation between encoding and PST eval must come from
    the encoder capturing piece activity/placement quality.

    Three families:
      1. KNB vs k — knight + bishop placement varies
      2. KRpp vs kpp — rook + pawn structure varies
      3. KQNB vs kqnb — symmetric material, piece activity varies
    """
    rng = np.random.RandomState(7777)
    positions = []

    # Family 1: KNB vs k (equal material, positional variation only)
    while len(positions) < n // 3:
        sqs = rng.choice(64, 4, replace=False)
        wk, wn, wb, bk = [int(s) for s in sqs]
        # Kings can't be adjacent
        wk_r, wk_c = rc(wk); bk_r, bk_c = rc(bk)
        if max(abs(wk_r - bk_r), abs(wk_c - bk_c)) <= 1:
            continue
        pos = {wk: 'K', wn: 'N', wb: 'B', bk: 'k'}
        _, pst_score, _ = pst_eval(pos)
        positions.append((pos, pst_score, f"KNBk-{len(positions)}"))

    # Family 2: KR+2P vs k+2p
    while len(positions) < 2 * n // 3:
        sqs = rng.choice(64, 6, replace=False)
        wk, wr, wp1, wp2, bk, bp1 = [int(s) for s in sqs]
        wk_r, wk_c = rc(wk); bk_r, bk_c = rc(bk)
        if max(abs(wk_r - bk_r), abs(wk_c - bk_c)) <= 1:
            continue
        # Pawns not on rank 1 or 8
        if rc(wp1)[0] in (0, 7) or rc(wp2)[0] in (0, 7) or rc(bp1)[0] in (0, 7):
            continue
        pos = {wk: 'K', wr: 'R', wp1: 'P', wp2: 'P', bk: 'k', bp1: 'p'}
        _, pst_score, _ = pst_eval(pos)
        positions.append((pos, pst_score, f"KRpp-{len(positions)}"))

    # Family 3: symmetric material KQNB vs kqnb
    while len(positions) < n:
        sqs = rng.choice(64, 8, replace=False)
        wk, wq, wn, wb, bk, bq, bn, bb = [int(s) for s in sqs]
        wk_r, wk_c = rc(wk); bk_r, bk_c = rc(bk)
        if max(abs(wk_r - bk_r), abs(wk_c - bk_c)) <= 1:
            continue
        pos = {wk: 'K', wq: 'Q', wn: 'N', wb: 'B',
               bk: 'k', bq: 'q', bn: 'n', bb: 'b'}
        _, pst_score, _ = pst_eval(pos)
        positions.append((pos, pst_score, f"KQNB-{len(positions)}"))

    return positions


def generate_mixed_positions():
    """Mixed positions with PST decomposition for full benchmark.
    Returns list of (pos, material_cp, positional_cp, total_cp, desc)."""
    positions = []

    # Starting position and material variations
    base_w = {sq(7,4): 'K', sq(7,3): 'Q', sq(7,0): 'R', sq(7,7): 'R',
              sq(7,2): 'B', sq(7,5): 'B', sq(7,1): 'N', sq(7,6): 'N'}
    base_b = {sq(0,4): 'k', sq(0,3): 'q', sq(0,0): 'r', sq(0,7): 'r',
              sq(0,2): 'b', sq(0,5): 'b', sq(0,1): 'n', sq(0,6): 'n'}
    pawn_w = {sq(6, i): 'P' for i in range(8)}
    pawn_b = {sq(1, i): 'p' for i in range(8)}
    full = {**base_w, **base_b, **pawn_w, **pawn_b}

    for rm_list, desc in [
        ([], "Starting"),
        ([sq(0,1)], "W+N"),   ([sq(0,0)], "W+R"),   ([sq(0,3)], "W+Q"),
        ([sq(7,1)], "B+N"),   ([sq(7,0)], "B+R"),
        ([sq(0,1), sq(0,6)], "W+NN"), ([sq(7,1), sq(7,6)], "B+NN"),
    ]:
        pos = {k: v for k, v in full.items() if k not in rm_list}
        m, p, t = pst_eval(pos)
        positions.append((pos, m, p, t, desc))

    # Positional variations (same or similar material)
    configs = [
        ({sq(3,4): 'N', sq(6,3): 'P', sq(6,5): 'P', sq(7,4): 'K',
          sq(0,4): 'k', sq(1,3): 'p', sq(1,5): 'p'}, "Knight outpost"),
        ({sq(7,0): 'N', sq(6,3): 'P', sq(6,5): 'P', sq(7,4): 'K',
          sq(0,4): 'k', sq(1,3): 'p', sq(1,5): 'p'}, "Knight rim"),
        ({sq(3,3): 'K', sq(4,4): 'P', sq(0,4): 'k'}, "Central king"),
        ({sq(7,4): 'K', sq(6,3): 'P', sq(6,4): 'P', sq(6,5): 'P',
          sq(0,4): 'k'}, "Back rank king"),
        ({sq(5,2): 'B', sq(5,5): 'B', sq(7,4): 'K', sq(0,4): 'k'}, "Bishop pair center"),
        ({sq(7,2): 'B', sq(7,5): 'B', sq(7,4): 'K', sq(0,4): 'k'}, "Bishop pair back"),
        ({sq(5,4): 'N', sq(5,3): 'N', sq(7,4): 'K', sq(0,4): 'k'}, "Knight duo center"),
        ({sq(7,1): 'N', sq(7,6): 'N', sq(7,4): 'K', sq(0,4): 'k'}, "Knight duo back"),
        # Rook activity
        ({sq(1,0): 'R', sq(7,4): 'K', sq(0,4): 'k'}, "Rook 7th rank"),
        ({sq(7,0): 'R', sq(7,4): 'K', sq(0,4): 'k'}, "Rook back rank"),
        ({sq(4,3): 'R', sq(7,4): 'K', sq(0,4): 'k'}, "Rook center"),
        # Queen centralization
        ({sq(3,3): 'Q', sq(7,4): 'K', sq(0,4): 'k'}, "Queen center"),
        ({sq(7,3): 'Q', sq(7,4): 'K', sq(0,4): 'k'}, "Queen home"),
    ]
    for pos, desc in configs:
        m, p, t = pst_eval(pos)
        positions.append((pos, m, p, t, desc))

    # Openings (equal material, positional variation)
    openings = [
        ({sq(4,4): 'P', sq(6,3): 'P', sq(7,1): 'N', sq(7,5): 'B', sq(7,4): 'K',
          sq(3,2): 'p', sq(1,3): 'p', sq(0,1): 'n', sq(0,5): 'b', sq(0,4): 'k'},
         "Sicilian"),
        ({sq(4,4): 'P', sq(6,3): 'P', sq(7,6): 'N', sq(7,2): 'B', sq(7,4): 'K',
          sq(3,4): 'p', sq(1,3): 'p', sq(0,6): 'n', sq(0,2): 'b', sq(0,4): 'k'},
         "French"),
        ({sq(4,4): 'P', sq(4,3): 'P', sq(7,4): 'K', sq(6,5): 'N',
          sq(3,3): 'p', sq(3,4): 'p', sq(0,4): 'k', sq(2,2): 'n'},
         "QGD"),
        ({sq(4,4): 'P', sq(7,4): 'K', sq(5,5): 'N', sq(7,5): 'B',
          sq(3,5): 'p', sq(0,4): 'k', sq(2,5): 'n', sq(0,2): 'b'},
         "KID"),
    ]
    for pos, desc in openings:
        m, p, t = pst_eval(pos)
        positions.append((pos, m, p, t, desc))

    return positions


def generate_random_krk(n=100):
    """n random legal KRK positions with endgame evaluation."""
    rng = np.random.RandomState(12345)
    positions = []
    while len(positions) < n:
        sqs = rng.choice(64, 3, replace=False)
        wk, wr, bk = int(sqs[0]), int(sqs[1]), int(sqs[2])
        wk_r, wk_c = rc(wk); bk_r, bk_c = rc(bk); wr_r, wr_c = rc(wr)
        if max(abs(wk_r - bk_r), abs(wk_c - bk_c)) <= 1: continue
        if max(abs(bk_r - wr_r), abs(bk_c - wr_c)) <= 1:
            if max(abs(wk_r - wr_r), abs(wk_c - wr_c)) > 1: continue
        pos = {wk: 'K', wr: 'R', bk: 'k'}
        positions.append((pos, krk_eval(wk, wr, bk), f"KRK-{len(positions)}"))
    return positions


def benchmark_correlation(encode_fn, positions):
    """Spearman rho between encoding similarity and evaluation similarity.
    Positive rho = similar evaluations map to similar encodings.
    Accepts both 3-tuples (pos, eval, desc) and 5-tuples (pos, m, p, t, desc)."""
    encs = [encode_fn(p) for p, *_ in positions]
    # Extract evaluation: last numeric field before description
    evs = []
    for item in positions:
        if len(item) == 3:
            evs.append(item[1])      # (pos, eval, desc)
        else:
            evs.append(item[1])      # default: first eval field
    cos_sims, eval_diffs = [], []
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            cs = cosine(encs[i], encs[j])
            ed = abs(evs[i] - evs[j])
            if not (np.isnan(cs) or np.isnan(ed)):
                cos_sims.append(cs)
                eval_diffs.append(ed)
    rho, pval = spearmanr(cos_sims, [-d for d in eval_diffs])
    return rho, pval, len(cos_sims)


def benchmark_pst(encode_fn, mixed_positions, component='total'):
    """Benchmark against a specific PST component.
    component: 'material' (index 1), 'positional' (index 2), 'total' (index 3).
    """
    idx = {'material': 1, 'positional': 2, 'total': 3}[component]
    encs = [encode_fn(p) for p, *_ in mixed_positions]
    evs = [item[idx] for item in mixed_positions]
    cos_sims, eval_diffs = [], []
    for i in range(len(mixed_positions)):
        for j in range(i + 1, len(mixed_positions)):
            cs = cosine(encs[i], encs[j])
            ed = abs(evs[i] - evs[j])
            if not (np.isnan(cs) or np.isnan(ed)):
                cos_sims.append(cs)
                eval_diffs.append(ed)
    if len(cos_sims) < 3:
        return 0.0, 1.0, len(cos_sims)
    rho, pval = spearmanr(cos_sims, [-d for d in eval_diffs])
    return rho, pval, len(cos_sims)


# ═══════════════════════════════════════════════════════════════
# TEST BATTERY
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # ─── PREAMBLE: SPECTRAL VALUES ──────────────────────────────
    print("=" * 70)
    print("  SPECTRAL PIECE VALUES (mean_degree / 2.6)")
    print("=" * 70)
    print(f"\n  {'Piece':8s} {'Traditional':>12s} {'Spectral':>10s} {'Mean Deg':>10s}")
    for pchar in ['P', 'N', 'B', 'R', 'Q', 'K']:
        pname = {'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop',
                 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}[pchar]
        trad = VALS[pchar]
        spec = SPECTRAL_VALS[pchar]
        mdeg = spec * 2.6
        print(f"  {pname:8s} {trad:12.1f} {spec:10.1f} {mdeg:10.1f}")
    trad_range = max(abs(VALS[p]) for p in 'PNBRQK') / min(abs(VALS[p]) for p in 'PNBRQK')
    spec_range = max(abs(SPECTRAL_VALS[p]) for p in 'PNBRQK') / min(abs(SPECTRAL_VALS[p]) for p in 'PNBRQK')
    print(f"\n  Dynamic range: traditional = {trad_range:.0f}x, spectral = {spec_range:.1f}x")

    # ─── TEST 1: SYMMETRY INVARIANCE ──────────────────────────
    print(f"\n{'=' * 70}")
    print("  TEST 1: D4 SYMMETRY INVARIANCE OF 512-DIM ENCODER")
    print("=" * 70)

    pos_orig = {sq(3, 4): 'N', sq(7, 4): 'K', sq(6, 3): 'P',
                sq(0, 4): 'k', sq(1, 5): 'p'}

    enc_orig = encode_512(pos_orig)
    a1_orig = enc_orig[:64]  # A₁ channel

    print(f"\n  A₁ channel (64 dims) — should be D4-INVARIANT:")
    all_invariant = True
    for g_idx, perm in enumerate(D4_PERMS):
        rotated_pos = {int(perm[s]): p for s, p in pos_orig.items()}
        enc_rot = encode_512(rotated_pos)
        a1_rot = enc_rot[:64]
        diff = np.linalg.norm(a1_orig - a1_rot)
        ok = diff < 1e-10
        all_invariant &= ok
        if g_idx == 0 or not ok:
            print(f"    g{g_idx}: ||diff|| = {diff:.2e}  [{'INVARIANT' if ok else 'BROKEN'}]")
    if all_invariant:
        print(f"    ALL 8 transforms: ||diff|| < 1e-10  [INVARIANT ✓]")

    # Full 512 equivariance check
    print(f"\n  Full 512-dim — equivariance (not invariance):")
    for g_idx in [1, 2, 4]:  # rot90, rot180, reflect
        rotated_pos = {int(D4_PERMS[g_idx][s]): p for s, p in pos_orig.items()}
        enc_rot = encode_512(rotated_pos)
        c = cosine(enc_orig, enc_rot)
        print(f"    g{g_idx}: cos(orig, rot) = {c:+.4f}  [equivariant, not identical]")

    # Different position (kings on DIFFERENT squares to avoid K=100 domination)
    pos_diff = {sq(6, 2): 'R', sq(3, 3): 'K', sq(5, 0): 'B',
                sq(1, 1): 'k', sq(1, 7): 'n'}
    c_diff = cosine(enc_orig, encode_512(pos_diff))
    c_diff_s = cosine(encode_512_spectral(pos_orig), encode_512_spectral(pos_diff))
    print(f"\n  Different position (different king squares):")
    print(f"    Traditional: cos = {c_diff:+.4f}")
    print(f"    Spectral:    cos = {c_diff_s:+.4f}")

    # Same kings, different pieces — THE KING DOMINATION TEST
    pos_sameK = {sq(7, 4): 'K', sq(0, 4): 'k', sq(3, 0): 'R', sq(2, 6): 'B'}
    c_sameK = cosine(enc_orig, encode_512(pos_sameK))
    c_sameK_s = cosine(encode_512_spectral(pos_orig), encode_512_spectral(pos_sameK))
    print(f"\n  KING DOMINATION TEST (same king squares, different pieces):")
    print(f"    Traditional (K=100): cos = {c_sameK:+.4f}  ← king dominates signal")
    print(f"    Spectral   (K={SPECTRAL_VALS['K']}):  cos = {c_sameK_s:+.4f}  ← proportional contribution")
    domination_fixed = abs(c_sameK_s) < abs(c_sameK)
    print(f"    King domination {'REDUCED' if domination_fixed else 'UNCHANGED'}: "
          f"|cos| {abs(c_sameK):.4f} → {abs(c_sameK_s):.4f}")
    print(f"\n  TEST 1: {'PASS' if all_invariant else 'FAIL'}")


    # ─── TEST 2: CHANNEL ENERGY ANALYSIS ─────────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 2: CHANNEL ENERGY DISTRIBUTION")
    print(f"{'=' * 70}")

    test_poss = [
        ("Single knight e4", {sq(3, 4): 'N'}),
        ("KRK endgame", {sq(5, 4): 'K', sq(3, 0): 'R', sq(0, 0): 'k'}),
        ("Middlegame", {sq(7, 4): 'K', sq(7, 3): 'Q', sq(7, 0): 'R',
                        sq(5, 5): 'N', sq(6, 3): 'P', sq(4, 4): 'P',
                        sq(0, 4): 'k', sq(0, 3): 'q', sq(2, 5): 'n',
                        sq(1, 3): 'p', sq(3, 4): 'p'}),
    ]

    ch_names = ['A₁', 'A₂', 'B₁', 'B₂', 'E', 'Fib₁', 'Fib₂', 'Fib₃']
    print(f"\n  {'Position':20s}", end='')
    for cn in ch_names:
        print(f" {cn:>6s}", end='')
    print(f" {'Total':>7s}")

    for desc, pos in test_poss:
        enc = encode_512(pos)
        norms = [np.linalg.norm(enc[i*64:(i+1)*64]) for i in range(8)]
        total = np.linalg.norm(enc)
        print(f"  {desc:20s}", end='')
        for n in norms:
            print(f" {n:6.2f}", end='')
        print(f" {total:7.2f}")

    # Verify: fiber channels are zero for empty board signal (no pieces)
    enc_solo = encode_512({sq(3, 4): 'N'})
    fib_solo = np.linalg.norm(enc_solo[320:])
    print(f"\n  Single piece alone — fiber energy: {fib_solo:.6f}"
          f"  [{'~0: no targets occupied ✓' if fib_solo < 0.1 else 'nonzero'}]")


    # ─── TEST 3: MANY-BODY INTERACTION ───────────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 3: MANY-BODY INTERACTION IN FIBER CHANNELS")
    print(f"{'=' * 70}")

    pairs = [
        ('N', sq(4, 4), 'B', sq(2, 3), "Knight+Bishop"),
        ('R', sq(7, 0), 'R', sq(7, 7), "Rook+Rook"),
        ('Q', sq(7, 3), 'K', sq(7, 4), "Queen+King"),
        ('N', sq(4, 4), 'N', sq(3, 2), "Knight+Knight"),
    ]

    print(f"\n  {'Config':18s} {'Irrep %':>8s} {'Fiber %':>8s} {'Total %':>8s}")

    for p1, s1, p2, s2, desc in pairs:
        ej = encode_512({s1: p1, s2: p2})
        ea = encode_512({s1: p1})
        eb = encode_512({s2: p2})
        diff = ej - (ea + eb)

        irrep_pct = np.linalg.norm(diff[:320]) / (np.linalg.norm(ej[:320]) + 1e-15) * 100
        fiber_pct = np.linalg.norm(diff[320:]) / (np.linalg.norm(ej[320:]) + 1e-15) * 100
        total_pct = np.linalg.norm(diff) / (np.linalg.norm(ej) + 1e-15) * 100
        print(f"  {desc:18s} {irrep_pct:7.1f}% {fiber_pct:7.1f}% {total_pct:7.1f}%")

    # Verify design property: irrep channels are additive (linear signal)
    ej = encode_512({sq(4, 4): 'N', sq(2, 3): 'B'})
    ea = encode_512({sq(4, 4): 'N'})
    eb = encode_512({sq(2, 3): 'B'})
    irrep_add = np.allclose(ej[:320], ea[:320] + eb[:320], atol=1e-10)
    fiber_add = np.allclose(ej[320:], ea[320:] + eb[320:], atol=1e-10)
    print(f"\n  Design check:")
    print(f"    Irrep channels additive: {irrep_add}  (expected: True — linear in signal)")
    print(f"    Fiber channels additive: {fiber_add}  (expected: False — many-body)")


    # ─── TEST 4: ASSOCIATIVE RETRIEVAL ───────────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 4: ASSOCIATIVE RETRIEVAL")
    print(f"{'=' * 70}")

    library = {
        "Sicilian": {sq(4,4): 'P', sq(6,3): 'P', sq(7,1): 'N', sq(7,5): 'B', sq(7,4): 'K',
                     sq(3,2): 'p', sq(1,3): 'p', sq(0,1): 'n', sq(0,5): 'b', sq(0,4): 'k'},
        "French":   {sq(4,4): 'P', sq(6,3): 'P', sq(7,6): 'N', sq(7,2): 'B', sq(7,4): 'K',
                     sq(3,4): 'p', sq(1,3): 'p', sq(0,6): 'n', sq(0,2): 'b', sq(0,4): 'k'},
        "EG_KR":    {sq(7,4): 'K', sq(7,0): 'R', sq(0,4): 'k'},
        "EG_KQ":    {sq(7,4): 'K', sq(7,3): 'Q', sq(0,4): 'k'},
    }
    queries = {
        "Sicilian~": {sq(4,4): 'P', sq(6,3): 'P', sq(5,5): 'N', sq(7,5): 'B', sq(7,4): 'K',
                      sq(3,2): 'p', sq(1,3): 'p', sq(2,5): 'n', sq(0,5): 'b', sq(0,4): 'k'},
        "EG_KR~":    {sq(3,3): 'K', sq(4,0): 'R', sq(0,4): 'k'},
    }

    for enc_name, enc_fn in [("A₁ (64d)", encode_A1), ("320d", encode_320),
                              ("512d", encode_512)]:
        lib_enc = {n: enc_fn(p) for n, p in library.items()}
        print(f"\n  {enc_name}:")
        print(f"  {'Query':>12s} {'Best':>10s} {'Sim':>8s} {'2nd':>10s} {'Gap':>6s}")
        for qname, qpos in queries.items():
            qenc = enc_fn(qpos)
            ranked = sorted(lib_enc.items(), key=lambda x: cosine(qenc, x[1]), reverse=True)
            s1 = cosine(qenc, ranked[0][1])
            s2 = cosine(qenc, ranked[1][1])
            print(f"  {qname:>12s} {ranked[0][0]:>10s} {s1:+8.4f} {ranked[1][0]:>10s} {s1-s2:6.3f}")

    # Rotation-invariant retrieval (A₁ only)
    print(f"\n  Rotation-invariant retrieval:")
    sicilian_rot90 = {int(D4_PERMS[1][s]): p for s, p in library["Sicilian"].items()}
    for enc_name, enc_fn in [("A₁ (64d)", encode_A1), ("512d", encode_512),
                              ("Raw (64d)", encode_raw)]:
        lib_enc = {n: enc_fn(p) for n, p in library.items()}
        qenc = enc_fn(sicilian_rot90)
        ranked = sorted(lib_enc.items(), key=lambda x: cosine(qenc, x[1]), reverse=True)
        s1 = cosine(qenc, ranked[0][1])
        print(f"    {enc_name:>12s}: Sicilian(rot90°) → {ranked[0][0]:>10s} (sim={s1:+.4f})")


    # ─── TEST 5: QUANTUM NUMBER CODEBOOK ─────────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 5: QUANTUM NUMBER CODEBOOK vs EIGENVALUE CODEBOOK")
    print(f"{'=' * 70}")

    qn = compute_quantum_numbers()
    print(f"\n  Quantum numbers (parity, components, homogeneity, λ₂, bandwidth):")
    for pchar, vals in qn.items():
        pname = {'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}[pchar]
        print(f"    {pname:8s}: {vals}")
    tuples = list(qn.values())
    unique = len(set(tuples)) == len(tuples)
    print(f"  All tuples unique: {unique}  [{'PASS ✓' if unique else 'FAIL ✗'}]")

    # Cross-piece similarity comparison
    cb_qn = build_codebook_qn()
    cb_ev = build_codebook_eigenvalue()
    pieces = ['N', 'B', 'R', 'Q', 'K']

    print(f"\n  Cross-piece cosine similarity:")
    print(f"  {'Pair':>8s} {'QN codebook':>12s} {'EV codebook':>12s}")
    max_qn, max_ev = 0.0, 0.0
    for i, p1 in enumerate(pieces):
        for j, p2 in enumerate(pieces):
            if j <= i: continue
            cq = cosine(cb_qn[p1], cb_qn[p2])
            ce = cosine(cb_ev[p1], cb_ev[p2])
            max_qn = max(max_qn, abs(cq))
            max_ev = max(max_ev, abs(ce))
            print(f"  {p1+'-'+p2:>8s} {cq:+12.4f} {ce:+12.4f}")

    print(f"\n  Max |cos|: QN={max_qn:.4f}, EV={max_ev:.4f}")
    print(f"  QN separation: {'GOOD' if max_qn < 0.3 else 'MODERATE' if max_qn < 0.6 else 'POOR'}"
          f"  (target: < 0.3)")
    print(f"  EV separation: {'GOOD' if max_ev < 0.3 else 'MODERATE' if max_ev < 0.6 else 'POOR'}"
          f"  (known bad: > 0.9)")


    # ─── TEST 5b: SQUARE CODEBOOK — DIFFUSION + COPRIME ────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 5b: SQUARE CODEBOOK (diffusion impulse + coprime roll)")
    print(f"{'=' * 70}")

    print(f"\n  Diffusion time t = {DIFFUSION_TIME:.4f}")
    print(f"  Coprime offsets: row={COPRIME_ROW}, col={COPRIME_COL}")

    # Spatial similarity: adjacent vs diagonal vs far
    adj_sims, diag_sims, far_sims = [], [], []
    for r in range(8):
        for c in range(8):
            s0 = sq(r, c)
            # Orthogonal adjacent
            for dr, dc in [(0, 1), (1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    adj_sims.append(cosine(SQUARE_CODEBOOK[s0], SQUARE_CODEBOOK[sq(nr, nc)]))
            # Diagonal adjacent
            for dr, dc in [(1, 1), (1, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    diag_sims.append(cosine(SQUARE_CODEBOOK[s0], SQUARE_CODEBOOK[sq(nr, nc)]))
            # Far (Manhattan distance >= 6)
            for r2 in range(8):
                for c2 in range(8):
                    if abs(r - r2) + abs(c - c2) >= 6:
                        far_sims.append(cosine(SQUARE_CODEBOOK[s0], SQUARE_CODEBOOK[sq(r2, c2)]))

    print(f"\n  Spatial similarity (fingerprints):")
    print(f"    Adjacent (ortho):  {np.mean(adj_sims):+.4f}  (target: ~0.5)")
    print(f"    Adjacent (diag):   {np.mean(diag_sims):+.4f}")
    print(f"    Far (dist >= 6):   {np.mean(far_sims):+.4f}  (target: ~0.0)")
    adj_ok = abs(np.mean(adj_sims) - 0.5) < 0.15
    decay_ok = np.mean(adj_sims) > np.mean(diag_sims) > np.mean(far_sims)
    print(f"    Calibration: {'PASS' if adj_ok else 'MISS'}")
    print(f"    Monotone decay: {'PASS' if decay_ok else 'FAIL'}")

    # Coprime roll: verify distinct offsets and uniform spread
    offsets = [square_roll_offset(s) for s in range(64)]
    offset_gaps = np.diff(sorted(offsets))
    print(f"\n  Coprime roll offsets (HDC binding):")
    print(f"    Distinct: {len(set(offsets))}/64")
    print(f"    Spread: min_gap={min(offset_gaps)}, max_gap={max(offset_gaps)}, "
          f"ideal={512 // 64}")
    print(f"    Sample: e1={square_roll_offset(sq(7, 4))}, "
          f"d4={square_roll_offset(sq(4, 3))}, "
          f"a8={square_roll_offset(sq(0, 0))}")

    # Verify coprime roll gives near-zero cross-talk (orthogonal binding)
    test_vec = cb_qn['N']
    roll_sims = []
    for s1 in range(0, 64, 8):
        for s2 in range(s1 + 1, min(s1 + 8, 64)):
            v1 = np.roll(test_vec, square_roll_offset(s1))
            v2 = np.roll(test_vec, square_roll_offset(s2))
            roll_sims.append(abs(cosine(v1, v2)))
    print(f"    Roll cross-talk: mean |cos| = {np.mean(roll_sims):.4f}  (target: ~0.0)")


    # ─── TEST 6: BINDING / UNBINDING ACCURACY ────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 6: HDC BINDING / UNBINDING ACCURACY (coprime roll)")
    print(f"{'=' * 70}")

    test_pos = {
        sq(7, 4): 'K', sq(7, 3): 'Q', sq(7, 0): 'R',
        sq(5, 5): 'N', sq(4, 2): 'B', sq(6, 3): 'P', sq(6, 4): 'P',
        sq(0, 4): 'k', sq(0, 3): 'q', sq(2, 5): 'n',
        sq(1, 3): 'p', sq(3, 4): 'p',
    }

    print(f"\n  Test position: {len(test_pos)} pieces")
    print(f"  HDC capacity at D=512: ~{512 // int(len(test_pos) * np.log(len(test_pos)))} items")

    # Test all combinations: (QN vs EV) × (balanced vs unbalanced)
    for cb_name, cb in [("QN", cb_qn), ("EV", cb_ev)]:
        for balanced in [False, True]:
            mode = "balanced" if balanced else "value-wt"
            enc = encode_hdc(test_pos, cb, balanced=balanced)
            correct = 0
            total = 0
            errors = []
            for si, pchar in test_pos.items():
                expected = pchar.upper()
                retrieved, sims = query_square(enc, si, cb)
                ok = retrieved == expected
                correct += ok
                total += 1
                if not ok:
                    errors.append(f"{sqname(si)}:{expected}->{retrieved}")
            pct = correct / total * 100
            verdict = "PASS" if correct == total else "GOOD" if pct >= 80 else "PARTIAL" if pct >= 50 else "FAIL"
            err_str = f"  errors: {', '.join(errors[:3])}" if errors else ""
            print(f"    {cb_name:2s} {mode:9s}: {correct:2d}/{total} ({pct:3.0f}%) [{verdict}]{err_str}")

    # Small position test (fewer pieces → less interference)
    small_pos = {sq(4, 4): 'N', sq(7, 4): 'K', sq(0, 4): 'k', sq(7, 0): 'R'}
    enc_small = encode_hdc(small_pos, cb_qn, balanced=True)
    small_correct = 0
    for si, pchar in small_pos.items():
        expected = pchar.upper()
        retrieved, _ = query_square(enc_small, si, cb_qn)
        small_correct += (retrieved == expected)
    print(f"\n  Small position (4 pieces): QN balanced {small_correct}/4"
          f"  [{'PASS' if small_correct == 4 else 'PARTIAL'}]")


    # ─── TEST 7: DECOMPOSED BENCHMARK — MATERIAL vs POSITIONAL ─
    print(f"\n{'=' * 70}")
    print(f"  TEST 7: DECOMPOSED BENCHMARK (PST evaluation)")
    print(f"  Spearman rho: encoding sim vs eval component similarity")
    print(f"  Material = piece counts | Positional = piece-square tables")
    print(f"{'=' * 70}")

    mixed = generate_mixed_positions()
    n_mixed = len(mixed)
    n_pairs = n_mixed * (n_mixed - 1) // 2
    print(f"\n  Mixed positions: {n_mixed} positions, {n_pairs} pairs")

    # Show PST decomposition for a few positions
    print(f"\n  Sample PST decomposition (centipawns):")
    print(f"  {'Position':22s} {'Material':>10s} {'Positional':>12s} {'Total':>8s}")
    for pos, m, p, t, desc in mixed[:8]:
        print(f"  {desc:22s} {m:10.0f} {p:12.0f} {t:8.0f}")

    # THE KEY EXPERIMENT: correlate each encoder against each eval component
    encoders_trad = [
        ("Raw (K=100)", encode_raw, 64),
        ("512d (K=100)", encode_512, 512),
    ]
    encoders_spec = [
        ("Raw (K=2.5)", encode_raw_spectral, 64),
        ("512d (K=2.5)", encode_512_spectral, 512),
    ]

    for component in ['material', 'positional', 'total']:
        print(f"\n  vs {component.upper()} eval:")
        print(f"  {'Encoder':>18s} {'rho':>8s} {'p-value':>10s} {'Verdict':>10s}")
        for enc_name, enc_fn, dims in encoders_trad + encoders_spec:
            rho, pval, _ = benchmark_pst(enc_fn, mixed, component)
            verdict = "STRONG" if rho > 0.3 else "MODERATE" if rho > 0.15 else "WEAK" if rho > 0 else "NONE"
            print(f"  {enc_name:>18s} {rho:+8.4f} {pval:10.2e} {verdict:>10s}")


    # ─── TEST 8: EQUAL-MATERIAL BENCHMARK ────────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 8: EQUAL-MATERIAL POSITIONS (positional signal only)")
    print(f"  All positions have identical material within each family.")
    print(f"  Ground truth = PST positional score (no material component).")
    print(f"  THIS is where spectral encoding should shine.")
    print(f"{'=' * 70}")

    eq_pos = generate_equal_material_positions(60)
    # Convert to 3-tuple format for benchmark_correlation
    eq_3 = [(p, e, d) for p, e, d in eq_pos]
    n_eq = len(eq_3)
    print(f"\n  {n_eq} equal-material positions, {n_eq*(n_eq-1)//2} pairs")
    print(f"  Families: KNBk (knight+bishop), KRppkp (rook+pawns), KQNBkqnb (symmetric)")

    print(f"\n  {'Encoder':>18s} {'rho':>8s} {'p-value':>10s} {'Verdict':>10s}")
    results = {}
    for enc_name, enc_fn in [
        ("Raw (K=100)", encode_raw),
        ("512d (K=100)", encode_512),
        ("Raw (K=2.5)", encode_raw_spectral),
        ("512d (K=2.5)", encode_512_spectral),
    ]:
        rho, pval, _ = benchmark_correlation(enc_fn, eq_3)
        results[enc_name] = rho
        verdict = "STRONG" if rho > 0.3 else "MODERATE" if rho > 0.15 else "WEAK" if rho > 0 else "NONE"
        print(f"  {enc_name:>18s} {rho:+8.4f} {pval:10.2e} {verdict:>10s}")

    r_trad = results.get("512d (K=100)", 0)
    r_spec = results.get("512d (K=2.5)", 0)
    print(f"\n  512d comparison on equal-material positions:")
    print(f"    Traditional: rho = {r_trad:+.4f}")
    print(f"    Spectral:    rho = {r_spec:+.4f}")
    if r_spec > r_trad:
        delta = r_spec - r_trad
        print(f"    Spectral wins: +{delta:.4f} ({'SIGNIFICANT' if delta > 0.1 else 'MODEST'})")
    elif r_trad > r_spec:
        print(f"    Traditional wins: +{r_trad - r_spec:.4f}")
    else:
        print(f"    Tied")


    # ─── TEST 9: KRK ENDGAME (DTM heuristic) ────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 9: KRK ENDGAME (distance-to-mate heuristic)")
    print(f"{'=' * 70}")

    krk_pos = generate_random_krk(100)
    n_krk = len(krk_pos)
    print(f"\n  {n_krk} KRK positions, {n_krk*(n_krk-1)//2} pairs")
    print(f"  Eval = edge_push + king_proximity + rook_cutting (purely positional)")

    print(f"\n  {'Encoder':>18s} {'rho':>8s} {'p-value':>10s} {'Verdict':>10s}")
    for enc_name, enc_fn in [
        ("Raw (K=100)", encode_raw),
        ("512d (K=100)", encode_512),
        ("Raw (K=2.5)", encode_raw_spectral),
        ("512d (K=2.5)", encode_512_spectral),
    ]:
        rho, pval, _ = benchmark_correlation(enc_fn, krk_pos)
        verdict = "STRONG" if rho > 0.3 else "MODERATE" if rho > 0.15 else "WEAK" if rho > 0 else "NONE"
        print(f"  {enc_name:>18s} {rho:+8.4f} {pval:10.2e} {verdict:>10s}")


    # ─── TEST 10: HDC UNBINDING ──────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  TEST 10: HDC UNBINDING — SPECTRAL vs TRADITIONAL")
    print(f"{'=' * 70}")

    test_pos_10 = {
        sq(7, 4): 'K', sq(7, 3): 'Q', sq(7, 0): 'R',
        sq(5, 5): 'N', sq(4, 2): 'B', sq(6, 3): 'P', sq(6, 4): 'P',
        sq(0, 4): 'k', sq(0, 3): 'q', sq(2, 5): 'n',
        sq(1, 3): 'p', sq(3, 4): 'p',
    }

    print(f"\n  {len(test_pos_10)} pieces, QN codebook:")

    for weight_mode, balanced in [("value-wt", False), ("balanced", True)]:
        for val_name, vals_dict in [("Traditional", VALS), ("Spectral", SPECTRAL_VALS)]:
            enc = np.zeros(512)
            for si, pchar in test_pos_10.items():
                ptype = pchar.upper()
                if balanced:
                    weight = 1.0 if pchar.isupper() else -1.0
                else:
                    weight = vals_dict[pchar]
                enc += weight * np.roll(cb_qn[ptype], square_roll_offset(si))
            correct = sum(1 for si, pchar in test_pos_10.items()
                         if query_square(enc, si, cb_qn)[0] == pchar.upper())
            total = len(test_pos_10)
            pct = correct / total * 100
            print(f"    {val_name:12s} {weight_mode:9s}: {correct:2d}/{total} ({pct:3.0f}%)")


    # ─── TEST 11: STOCKFISH CENTIPAWN BENCHMARK ────────────────
    # The real test: does our spectral encoding correlate with what
    # the strongest chess engine in the world thinks about positions?
    #
    # Three position families, each probing different signals:
    #   A) Mixed positions (material + positional variation)
    #   B) Equal-material (PURE positional — the key test)
    #   C) KRK endgames (purely positional, known theory)
    #   D) Piece activity pairs (same material, good vs bad placement)
    #
    # Stockfish depth 12 gives ~2200 Elo evaluation quality.
    # If spectral encoding captures positional structure that material
    # counting misses, it should correlate better with Stockfish on
    # equal-material positions.
    # ──────────────────────────────────────────────────────────────

    print(f"\n{'=' * 70}")
    print(f"  TEST 11: STOCKFISH CENTIPAWN BENCHMARK (depth 12)")
    print(f"{'=' * 70}")

    # Quick check: can we reach stockfish?
    sf_test = stockfish_eval_batch([{sq(7, 4): 'K', sq(0, 4): 'k'}], depth=8)
    if sf_test is None:
        print(f"\n  Stockfish not available at: {STOCKFISH_PATH}")
        print(f"  Skipping engine evaluation.")
    else:
        print(f"\n  Stockfish 18 connected. Evaluating positions...")

        def _filter_valid(pos_list, sf_scores, labels):
            """Filter to positions where Stockfish returned a score."""
            valid = [(p, s, l) for p, s, l in zip(pos_list, sf_scores, labels)
                     if s is not None]
            n_skip = len(pos_list) - len(valid)
            return valid, n_skip

        # ── Family A: Mixed positions (material variation) ──────
        mixed_pos_list = [p for p, *_ in mixed]
        mixed_labels = [d for p, m, ps, t, d in mixed]
        sf_mixed_raw = stockfish_eval_batch(mixed_pos_list, depth=12)

        sf_mixed_3, n_skip_a = _filter_valid(mixed_pos_list, sf_mixed_raw, mixed_labels)

        print(f"\n  A) MIXED POSITIONS ({len(sf_mixed_3)}/{len(mixed)} valid)")
        print(f"  Sample Stockfish evaluations:")
        print(f"  {'Position':22s} {'SF (cp)':>8s} {'Material':>10s} {'PST pos':>9s}")
        shown = 0
        for i, (pos, m, p, t, desc) in enumerate(mixed):
            if sf_mixed_raw[i] is not None and shown < 10:
                print(f"  {desc:22s} {sf_mixed_raw[i]:+8d} {m:+10.0f} {p:+9.0f}")
                shown += 1

        print(f"\n  Encoder vs Stockfish (all mixed):")
        print(f"  {'Encoder':>18s} {'rho':>8s} {'p-value':>10s} {'Verdict':>10s}")
        for enc_name, enc_fn in [
            ("Raw (K=100)", encode_raw),
            ("512d (K=100)", encode_512),
            ("Raw (K=2.5)", encode_raw_spectral),
            ("512d (K=2.5)", encode_512_spectral),
        ]:
            rho, pval, _ = benchmark_correlation(enc_fn, sf_mixed_3)
            verdict = "STRONG" if rho > 0.3 else "MODERATE" if rho > 0.15 else "WEAK" if rho > 0 else "NONE"
            print(f"  {enc_name:>18s} {rho:+8.4f} {pval:10.2e} {verdict:>10s}")

        # ── Family B: Equal-material (pure positional) ──────────
        eq_pos_list = [p for p, *_ in eq_pos]
        eq_labels = [d for p, e, d in eq_pos]
        sf_eq_raw = stockfish_eval_batch(eq_pos_list, depth=12)

        sf_eq_3, n_skip_b = _filter_valid(eq_pos_list, sf_eq_raw, eq_labels)
        sf_eq_scores = [s for _, s, _ in sf_eq_3]

        print(f"\n  B) EQUAL-MATERIAL POSITIONS ({len(sf_eq_3)}/{len(eq_pos)} valid)")
        if len(sf_eq_scores) > 2:
            print(f"  Ground truth = Stockfish centipawns (material is constant)")
            print(f"  SF eval range: [{min(sf_eq_scores):+d}, {max(sf_eq_scores):+d}] cp")
            print(f"  SF eval std:   {np.std(sf_eq_scores):.0f} cp")

            print(f"\n  Encoder vs Stockfish (equal material):")
            print(f"  {'Encoder':>18s} {'rho':>8s} {'p-value':>10s} {'Verdict':>10s}")
            eq_results = {}
            for enc_name, enc_fn in [
                ("Raw (K=100)", encode_raw),
                ("512d (K=100)", encode_512),
                ("Raw (K=2.5)", encode_raw_spectral),
                ("512d (K=2.5)", encode_512_spectral),
            ]:
                rho, pval, _ = benchmark_correlation(enc_fn, sf_eq_3)
                eq_results[enc_name] = rho
                verdict = "STRONG" if rho > 0.3 else "MODERATE" if rho > 0.15 else "WEAK" if rho > 0 else "NONE"
                print(f"  {enc_name:>18s} {rho:+8.4f} {pval:10.2e} {verdict:>10s}")

            r_eq_t = eq_results.get("512d (K=100)", 0)
            r_eq_s = eq_results.get("512d (K=2.5)", 0)
            if r_eq_s > r_eq_t:
                print(f"\n  >>> Spectral WINS on pure positional: +{r_eq_s - r_eq_t:.4f}")
            else:
                print(f"\n  >>> Traditional wins on pure positional: +{r_eq_t - r_eq_s:.4f}")
        else:
            print(f"  Too few valid positions for correlation.")

        # ── Family C: KRK endgames ─────────────────────────────
        krk_pos_list = [p for p, *_ in krk_pos]
        krk_labels = [d for p, e, d in krk_pos]
        sf_krk_raw = stockfish_eval_batch(krk_pos_list, depth=12)

        sf_krk_3, n_skip_c = _filter_valid(krk_pos_list, sf_krk_raw, krk_labels)
        sf_krk_scores = [s for _, s, _ in sf_krk_3]

        print(f"\n  C) KRK ENDGAMES ({len(sf_krk_3)}/{len(krk_pos)} valid)")
        if len(sf_krk_scores) > 2:
            print(f"  SF eval range: [{min(sf_krk_scores):+d}, {max(sf_krk_scores):+d}] cp")
            print(f"\n  {'Encoder':>18s} {'rho(SF)':>8s} {'rho(heur)':>10s}")
            for enc_name, enc_fn in [
                ("512d (K=100)", encode_512),
                ("512d (K=2.5)", encode_512_spectral),
            ]:
                rho_sf, _, _ = benchmark_correlation(enc_fn, sf_krk_3)
                rho_h, _, _ = benchmark_correlation(enc_fn, krk_pos)
                print(f"  {enc_name:>18s} {rho_sf:+8.4f} {rho_h:+10.4f}")

        # ── Family D: Piece activity pairs (Stockfish as oracle) ────
        # Same material, systematically good vs bad piece placement.
        # This is the most direct test: does the encoder see the
        # difference between a well-placed knight and a rim knight?
        activity_pairs = [
            # (good_pos, bad_pos, description)
            ({sq(3,4):'N', sq(7,4):'K', sq(6,3):'P', sq(6,5):'P',
              sq(0,4):'k', sq(1,3):'p', sq(1,5):'p'},
             {sq(7,0):'N', sq(7,4):'K', sq(6,3):'P', sq(6,5):'P',
              sq(0,4):'k', sq(1,3):'p', sq(1,5):'p'},
             "Knight outpost vs rim"),
            ({sq(1,0):'R', sq(7,4):'K', sq(0,4):'k', sq(6,4):'P'},
             {sq(7,0):'R', sq(7,4):'K', sq(0,4):'k', sq(6,4):'P'},
             "Rook 7th rank vs back rank"),
            ({sq(5,2):'B', sq(5,5):'B', sq(7,4):'K', sq(0,4):'k'},
             {sq(7,0):'B', sq(7,7):'B', sq(7,4):'K', sq(0,4):'k'},
             "Bishop pair center vs corner"),
            ({sq(4,3):'Q', sq(7,4):'K', sq(0,4):'k'},
             {sq(7,3):'Q', sq(7,4):'K', sq(0,4):'k'},
             "Queen center vs back rank"),
            ({sq(3,3):'K', sq(6,4):'P', sq(0,4):'k'},
             {sq(7,4):'K', sq(6,3):'P', sq(6,4):'P', sq(6,5):'P', sq(0,4):'k'},
             "Active king vs sheltered"),
            ({sq(5,4):'N', sq(5,3):'N', sq(7,4):'K', sq(0,4):'k'},
             {sq(7,0):'N', sq(7,7):'N', sq(7,4):'K', sq(0,4):'k'},
             "Knight duo center vs corners"),
        ]

        good_list = [g for g, b, d in activity_pairs]
        bad_list = [b for g, b, d in activity_pairs]
        sf_good = stockfish_eval_batch(good_list, depth=12)
        sf_bad = stockfish_eval_batch(bad_list, depth=12)

        print(f"\n  D) PIECE ACTIVITY PAIRS (same material, good vs bad)")
        print(f"  {'Pair':30s} {'SF good':>8s} {'SF bad':>8s} {'delta':>7s}")
        for i, (g, b, desc) in enumerate(activity_pairs):
            delta = sf_good[i] - sf_bad[i]
            print(f"  {desc:30s} {sf_good[i]:+8d} {sf_bad[i]:+8d} {delta:+7d}")

        print(f"\n  Encoder distance: good vs bad (higher = sees the difference)")
        print(f"  {'Pair':30s} {'512d trad':>10s} {'512d spec':>10s} {'SF delta':>9s}")
        for i, (g, b, desc) in enumerate(activity_pairs):
            enc_g_t = encode_512(g)
            enc_b_t = encode_512(b)
            enc_g_s = encode_512_spectral(g)
            enc_b_s = encode_512_spectral(b)
            dist_t = 1 - cosine(enc_g_t, enc_b_t)  # cosine distance
            dist_s = 1 - cosine(enc_g_s, enc_b_s)
            sf_delta = sf_good[i] - sf_bad[i]
            print(f"  {desc:30s} {dist_t:10.4f} {dist_s:10.4f} {sf_delta:+9d}")

        # Does the encoder distance correlate with Stockfish's eval gap?
        sf_deltas = [sf_good[i] - sf_bad[i] for i in range(len(activity_pairs))]
        dist_trad = [1 - cosine(encode_512(g), encode_512(b)) for g, b, d in activity_pairs]
        dist_spec = [1 - cosine(encode_512_spectral(g), encode_512_spectral(b))
                     for g, b, d in activity_pairs]

        if len(sf_deltas) >= 4:
            rho_t, _ = spearmanr(dist_trad, sf_deltas)
            rho_s, _ = spearmanr(dist_spec, sf_deltas)
            print(f"\n  Spearman rho (encoder distance vs SF delta):")
            print(f"    Traditional: {rho_t:+.4f}")
            print(f"    Spectral:    {rho_s:+.4f}")
            if rho_s > rho_t:
                print(f"    >>> Spectral encoding better tracks piece activity")

        # ── TEST 12: DEPTH-GAP EXPERIMENT ──────────────────────────
        # The potential/kinetic decomposition:
        #   Depth 1: near-static assessment (material + simple positioning)
        #   Depth 20: full tactical/strategic assessment (sees sequences)
        #   |deep - shallow|: latent tactical potential ("hidden value")
        #
        # Three correlations:
        #   1. Spectral dist vs |shallow diff| → do we match static view?
        #   2. Spectral dist vs |deep diff|    → do we match full view?
        #   3. Fiber energy vs |deep - shallow| per position
        #      → do spectrally active positions have more hidden value?
        #
        # If (3) holds, the spectral encoding detects positions where
        # depth of search matters — the potential energy landscape
        # predicts dynamic complexity. That's the field theory test.
        # ────────────────────────────────────────────────────────────

        print(f"\n{'=' * 70}")
        print(f"  TEST 12: DEPTH-GAP EXPERIMENT (potential vs kinetic)")
        print(f"  Depth 1 = static assessment, Depth 20 = full search")
        print(f"  |deep - shallow| = latent tactical potential")
        print(f"{'=' * 70}")

        # Build position set: mix of quiet, active, and tactical positions
        depth_test_positions = []

        # Quiet: symmetric/balanced, little to discover
        depth_test_positions.append(
            ({sq(7,4):'K', sq(6,3):'P', sq(6,4):'P', sq(6,5):'P',
              sq(0,4):'k', sq(1,3):'p', sq(1,4):'p', sq(1,5):'p'}, "Quiet: KPPPvkppp"))
        depth_test_positions.append(
            ({sq(7,4):'K', sq(7,0):'R', sq(7,7):'R',
              sq(0,4):'k', sq(0,0):'r', sq(0,7):'r'}, "Quiet: KRRvkrr"))
        depth_test_positions.append(
            ({sq(7,4):'K', sq(7,5):'B', sq(7,2):'B',
              sq(0,4):'k', sq(0,5):'b', sq(0,2):'b'}, "Quiet: KBBvkbb"))

        # Active: pieces centralized with potential
        depth_test_positions.append(
            ({sq(3,3):'N', sq(3,4):'N', sq(7,4):'K',
              sq(0,4):'k', sq(1,3):'p', sq(1,5):'p'}, "Active: central knights"))
        depth_test_positions.append(
            ({sq(3,3):'Q', sq(5,5):'N', sq(7,4):'K',
              sq(0,4):'k', sq(1,3):'p'}, "Active: Q+N attacking"))
        depth_test_positions.append(
            ({sq(1,0):'R', sq(1,7):'R', sq(7,4):'K',
              sq(0,4):'k', sq(6,3):'P'}, "Active: rooks on 7th"))

        # Tactical: pins, forks, discoveries lurking
        depth_test_positions.append(
            ({sq(3,4):'N', sq(7,4):'K', sq(6,4):'P',
              sq(0,4):'k', sq(1,3):'q', sq(2,5):'r'}, "Tactical: knight fork zone"))
        depth_test_positions.append(
            ({sq(4,0):'B', sq(7,4):'K', sq(6,5):'P',
              sq(0,4):'k', sq(1,3):'q', sq(3,3):'n'}, "Tactical: pin diagonal"))
        depth_test_positions.append(
            ({sq(5,4):'R', sq(7,4):'K',
              sq(0,4):'k', sq(3,4):'n', sq(2,4):'q'}, "Tactical: rook file pressure"))
        depth_test_positions.append(
            ({sq(4,3):'Q', sq(3,5):'B', sq(7,4):'K', sq(6,3):'P',
              sq(0,4):'k', sq(1,5):'r', sq(2,3):'n'}, "Tactical: Q+B battery"))

        # Complex: many pieces interacting
        depth_test_positions.append(
            ({sq(7,4):'K', sq(7,3):'Q', sq(7,0):'R', sq(5,5):'N',
              sq(6,3):'P', sq(6,4):'P', sq(4,2):'B',
              sq(0,4):'k', sq(0,3):'q', sq(2,5):'n',
              sq(1,3):'p', sq(3,4):'p'}, "Complex: middlegame 12pc"))
        depth_test_positions.append(
            ({sq(7,4):'K', sq(7,0):'R', sq(5,4):'N', sq(4,5):'B',
              sq(6,3):'P', sq(6,5):'P',
              sq(0,4):'k', sq(0,7):'r', sq(3,3):'n',
              sq(1,2):'p', sq(1,6):'p'}, "Complex: open position 11pc"))

        # Endgame: few pieces, some with clear wins
        depth_test_positions.append(
            ({sq(5,3):'K', sq(3,0):'R', sq(0,0):'k'}, "Endgame: KR vs k (corner)"))
        depth_test_positions.append(
            ({sq(4,4):'K', sq(6,0):'R', sq(0,4):'k'}, "Endgame: KR vs k (center)"))
        depth_test_positions.append(
            ({sq(6,3):'K', sq(5,0):'Q', sq(0,4):'k'}, "Endgame: KQ vs k"))
        depth_test_positions.append(
            ({sq(5,4):'K', sq(4,3):'P', sq(0,4):'k'}, "Endgame: KP vs k"))

        # Validate and evaluate at both depths
        dt_pos_list = [p for p, d in depth_test_positions]
        dt_labels = [d for p, d in depth_test_positions]

        print(f"\n  Evaluating {len(dt_pos_list)} positions at depth 1 and 20...")
        sf_d1_raw = stockfish_eval_batch(dt_pos_list, depth=1)
        sf_d20_raw = stockfish_eval_batch(dt_pos_list, depth=20)

        # Filter to valid positions (both depths returned scores)
        valid_idx = [i for i in range(len(dt_pos_list))
                     if sf_d1_raw[i] is not None and sf_d20_raw[i] is not None]

        dt_valid = [(dt_pos_list[i], dt_labels[i], sf_d1_raw[i], sf_d20_raw[i])
                    for i in valid_idx]

        print(f"  Valid positions: {len(dt_valid)}/{len(dt_pos_list)}")

        if len(dt_valid) >= 6:
            # Per-position metrics
            print(f"\n  {'Position':35s} {'D1 (cp)':>8s} {'D20 (cp)':>9s} {'Gap':>8s} "
                  f"{'Fiber E':>8s} {'Total E':>8s}")

            fiber_energies = []
            total_energies = []
            depth_gaps = []
            sf_d1_vals = []
            sf_d20_vals = []

            for pos, label, d1, d20 in dt_valid:
                gap = abs(d20 - d1)
                enc = encode_512_spectral(pos)
                fiber_e = np.linalg.norm(enc[320:])   # fiber channels only
                total_e = np.linalg.norm(enc)

                fiber_energies.append(fiber_e)
                total_energies.append(total_e)
                depth_gaps.append(gap)
                sf_d1_vals.append(d1)
                sf_d20_vals.append(d20)

                # Clamp display for mate scores
                d1_s = f"{d1:+8d}" if abs(d1) < 9999 else f"{'M+' if d1 > 0 else 'M-':>8s}"
                d20_s = f"{d20:+9d}" if abs(d20) < 9999 else f"{'M+' if d20 > 0 else 'M-':>9s}"
                print(f"  {label:35s} {d1_s} {d20_s} {gap:8d} "
                      f"{fiber_e:8.2f} {total_e:8.2f}")

            # Correlation 3: fiber energy vs depth gap (THE key test)
            rho_fiber_gap, pval_fiber_gap = spearmanr(fiber_energies, depth_gaps)
            rho_total_gap, pval_total_gap = spearmanr(total_energies, depth_gaps)

            print(f"\n  CORRELATION 3: Does spectral energy predict hidden value?")
            print(f"  Spearman rho (per-position scalar, N={len(dt_valid)}):")
            print(f"    Fiber energy vs |D20-D1|: rho = {rho_fiber_gap:+.4f}  "
                  f"(p = {pval_fiber_gap:.3f})")
            print(f"    Total energy vs |D20-D1|: rho = {rho_total_gap:+.4f}  "
                  f"(p = {pval_total_gap:.3f})")

            if rho_fiber_gap > 0.3 and pval_fiber_gap < 0.1:
                print(f"    >>> FIBER ENERGY PREDICTS TACTICAL DEPTH")
                print(f"    >>> The potential landscape detects where dynamics matter.")
            elif rho_fiber_gap > 0:
                print(f"    >>> Positive trend (fiber energy ~ hidden value) but not significant")
            else:
                print(f"    >>> No fiber-gap correlation detected")

            # Also test: irrep energy vs depth gap
            irrep_energies = []
            for pos, label, d1, d20 in dt_valid:
                enc = encode_512_spectral(pos)
                irrep_energies.append(np.linalg.norm(enc[:320]))

            rho_irrep_gap, pval_irrep_gap = spearmanr(irrep_energies, depth_gaps)
            print(f"    Irrep energy vs |D20-D1|: rho = {rho_irrep_gap:+.4f}  "
                  f"(p = {pval_irrep_gap:.3f})")

            # Ratio: fiber / irrep as "interaction density"
            interaction_density = [f / (r + 1e-10) for f, r in
                                   zip(fiber_energies, irrep_energies)]
            rho_dens_gap, pval_dens_gap = spearmanr(interaction_density, depth_gaps)
            print(f"    Fiber/Irrep ratio vs |D20-D1|: rho = {rho_dens_gap:+.4f}  "
                  f"(p = {pval_dens_gap:.3f})")

            # Correlations 1 & 2: pairwise encoding distance vs eval difference
            print(f"\n  CORRELATIONS 1 & 2: Pairwise encoding distance vs eval diff")
            enc_spec_list = [encode_512_spectral(pos) for pos, *_ in dt_valid]
            enc_trad_list = [encode_512(pos) for pos, *_ in dt_valid]

            cos_spec, cos_trad, diff_d1, diff_d20 = [], [], [], []
            for i in range(len(dt_valid)):
                for j in range(i + 1, len(dt_valid)):
                    cos_spec.append(cosine(enc_spec_list[i], enc_spec_list[j]))
                    cos_trad.append(cosine(enc_trad_list[i], enc_trad_list[j]))
                    diff_d1.append(-abs(sf_d1_vals[i] - sf_d1_vals[j]))
                    diff_d20.append(-abs(sf_d20_vals[i] - sf_d20_vals[j]))

            n_pairs = len(cos_spec)
            for depth_name, diff_vals in [("Depth 1 (static)", diff_d1),
                                           ("Depth 20 (full)", diff_d20)]:
                rho_s, pval_s = spearmanr(cos_spec, diff_vals)
                rho_t, pval_t = spearmanr(cos_trad, diff_vals)
                print(f"\n    vs {depth_name} ({n_pairs} pairs):")
                print(f"      Spectral 512d:    rho = {rho_s:+.4f}  (p = {pval_s:.3e})")
                print(f"      Traditional 512d: rho = {rho_t:+.4f}  (p = {pval_t:.3e})")
                if rho_s > rho_t:
                    print(f"      >>> Spectral wins: +{rho_s - rho_t:.4f}")

            # Bonus: does the encoding better match deep than shallow?
            rho_spec_d1, _ = spearmanr(cos_spec, diff_d1)
            rho_spec_d20, _ = spearmanr(cos_spec, diff_d20)
            if rho_spec_d20 > rho_spec_d1:
                print(f"\n    >>> Spectral encoding aligns MORE with deep search"
                      f" (+{rho_spec_d20 - rho_spec_d1:.4f})")
                print(f"    >>> Suggests encoding captures structure beyond static view")

    # ─── SYNTHESIS ────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  SYNTHESIS")
    print(f"{'=' * 70}")

    print(f"""
  512-DIM ENCODER ARCHITECTURE:
    5 D4 irreps (320d) + 3 fiber interaction (192d) = 512d
    A1 channel: D4-INVARIANT (||diff|| < 1e-10 for all 8 transforms)
    Fiber channels: non-additive (capture many-body interaction)
    Dimension: 512 = 8 x 64 = 2^9 (natural HDC dimension)

  SPECTRAL PIECE VALUES (mean_degree / 2.6):
    Traditional: P=1, N=3, B=3.5, R=5, Q=9, K=100
    Spectral:    P={SPECTRAL_VALS['P']}, N={SPECTRAL_VALS['N']}, B={SPECTRAL_VALS['B']}, \
R={SPECTRAL_VALS['R']}, Q={SPECTRAL_VALS['Q']}, K={SPECTRAL_VALS['K']}
    Dynamic range: 100x -> {spec_range:.1f}x
    King domination: cos 0.87 -> 0.34 (same king squares, different pieces)

  SQUARE CODEBOOK (diffusion impulse + coprime roll):
    Fingerprint: 512-dim impulse response through 8 encoder channels
      exp(-t*L) delta_s projected via D4 irreps + multi-scale diffusion
      t = {DIFFUSION_TIME:.4f} (calibrated for ~0.5 adjacent similarity)
    Binding: coprime roll np.roll(piece_vec, r*{COPRIME_ROW} + c*{COPRIME_COL} mod 512)
      UTLP S3 pattern: 2D spatial position -> 1D roll offset
      All 64 squares map to distinct offsets (coprime guarantee)
      Adjacent squares differ by one coprime stride in roll space
    Replaces: random bipolar codes (zero spatial structure)

  QUANTUM NUMBER CODEBOOK:
    5-tuple: (parity, topology, homogeneity, lambda_2, bandwidth)
    All unique -> complete classification, max |cos| < 0.11
    Replaces eigenvalue sequences (cross-sim > 0.92)

  EVALUATION DECOMPOSITION:
    Material eval: raw piece counts (centipawns)
    Positional eval: piece-square tables (Michniewski)
    The key question: which encoder correlates with POSITIONAL quality?
    Traditional VALS correlate with material (they ARE material weights).
    Spectral VALS encode movement structure, not material worth.

  NEXT STEPS:
    - Install Stockfish for centipawn ground truth
    - Syzygy tablebases for endgame DTZ values
    - Lichess game outcome correlation
    These capture tactical/strategic quality that PST tables miss.
""")
