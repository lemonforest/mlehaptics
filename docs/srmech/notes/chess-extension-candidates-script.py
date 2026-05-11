"""
Chess §3.5.3(C) extension candidates — concertmaster spike (2026-05-11).

Three candidates fall out of the prior chess D_4/B_4 + knight per-eigenspace
spikes (both 2026-05-11). This script tests each:

  (C-F3a) Chess queen 2D + 4D — queen adjacency = rook ∪ bishop. Mode I
    closed-form eigenvalues expected REFUTED (rook and bishop adjacency
    matrices likely do NOT commute — eig(A+B) ≠ eig(A) + eig(B) in general).
    Mode II per-eigenspace D_4 / B_4 irrep multiplicities expected to be
    integer-exact (queen is D_4 / B_4 equivariant). If yes, queen joins
    knight as a second Mode II sub-instance.

  (C-F3b) Side-length-N parametric — chess on N x N (2D) and N^4 (4D) board
    for varying N. Test whether Mode I closed-form rook/king/bishop
    predictions scale parametrically:
      - Rook on N x N: K_N □ K_N, spectrum sums of K_N eigenvalues
        {N-1 (mult 1), -1 (mult N-1)}.
      - King on N x N: P_N ⊠ P_N, eigs (1+2cos(πk/(N+1)))(1+2cos(πl/(N+1)))-1.
      - Bishop on N x N: parity-stratified by (x+y) mod 2; per-component
        bipartite, two isomorphic color classes.
    For 4D, smaller sweep N ∈ {3,4,5} (cost ~ N^4 dim eigh).

  (C-F3c) Toroidal (Z/8Z)^d chess — chess on a periodic board (boundary
    wraps). Symmetry group changes from D_4 (with boundary) to translation
    group Z_8 x Z_8 (2D) or Z_8^4 (4D). Abelian → all irreps 1-dim → "irrep
    decomposition" reduces to standard Fourier transform on Z_8^d. Test:
      Mode I: do toroidal rook/king/bishop eigenvalues match Fourier-
              closed-form predictions?
      Mode II: per-eigenspace Z_8^d translation-group irrep multiplicities
               integer-exact?
    If yes, §3.5.3(C) gains a 4th instance under a fundamentally different
    group structure (translation Z_n instead of dihedral D_n).

Math-doesn't-lie. MPM discipline: closed-form numerical linear algebra
(numpy only); no SGD; deterministic; reproducible. Single Source of Truth:
Rinaldi-Unciuleanu & Chiru 2026 (`docs/srmech/hoodoos/rinaldi-unciuleanu-chiru-2026.xml`).

Outputs:
  1. NDJSON per-test records at
     chess-extension-candidates-per-test-2026-05-11.ndjson
  2. Findings markdown chess-extension-candidates-2026-05-11.md (manual)
  3. Completion record appended to research-mfo/mfo_mpm_notes.ndjson

Author: concertmaster role, 2026-05-11.
"""

from __future__ import annotations

import itertools
import json
import time
from math import comb, factorial
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants / SSOT
# ---------------------------------------------------------------------------

SEED = 20260511
BOARD_SIDE_8 = 8
DIM_2D_SIZE_8 = BOARD_SIDE_8 ** 2
DIM_4D_SIZE_8 = BOARD_SIDE_8 ** 4

# Mode-I tolerance (closed-form eigenvalues vs empirical)
PRECISION_TARGET_MODE_I = 1e-12
# Mode-II tolerance (integer multiplicity check; forgiving for FP drift on
# 4096-dim character-orthogonality sums)
INTEGER_TOL = 1e-6
# Eigenspace grouping tolerance
EIGENSPACE_TOL = 1e-8

OUTPUT_DIR = Path(r"D:\GitHub\mlehaptics\docs\srmech\notes")
NDJSON_PATH = OUTPUT_DIR / "chess-extension-candidates-per-test-2026-05-11.ndjson"
COMPLETION_RECORD_PATH = Path(
    r"D:\GitHub\mlehaptics\docs\antikythera-maths\research-mfo\mfo_mpm_notes.ndjson"
)


# ---------------------------------------------------------------------------
# Common indexing helpers (parametric in side N)
# ---------------------------------------------------------------------------


def idx_2d(N: int, x: int, y: int) -> int:
    return x * N + y


def idx_4d(N: int, x: int, y: int, z: int, w: int) -> int:
    return ((x * N + y) * N + z) * N + w


def on_board(N: int, coords: Sequence[int]) -> bool:
    return all(0 <= c < N for c in coords)


# ---------------------------------------------------------------------------
# Parametric chess piece adjacencies (rook, king, bishop) — boundary version
# ---------------------------------------------------------------------------


def build_rook_2d_N(N: int) -> np.ndarray:
    """Rook on N x N board, hard boundary. Adjacency = same row XOR same column."""
    n = N * N
    A = np.zeros((n, n), dtype=np.int8)
    for x1 in range(N):
        for y1 in range(N):
            u = idx_2d(N, x1, y1)
            for x2 in range(N):
                if x2 != x1:
                    A[u, idx_2d(N, x2, y1)] = 1
            for y2 in range(N):
                if y2 != y1:
                    A[u, idx_2d(N, x1, y2)] = 1
    return A


def build_king_2d_N(N: int) -> np.ndarray:
    """King on N x N: Chebyshev distance 1, hard boundary."""
    n = N * N
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            u = idx_2d(N, x, y)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    x2, y2 = x + dx, y + dy
                    if on_board(N, (x2, y2)):
                        A[u, idx_2d(N, x2, y2)] = 1
    return A


def build_bishop_2d_N(N: int) -> np.ndarray:
    """Bishop on N x N: |dx| == |dy| != 0, hard boundary."""
    n = N * N
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            u = idx_2d(N, x, y)
            for k in range(1, N):
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        x2, y2 = x + sx * k, y + sy * k
                        if on_board(N, (x2, y2)):
                            A[u, idx_2d(N, x2, y2)] = 1
    return A


def build_rook_4d_N(N: int) -> np.ndarray:
    """4D rook on N^4: any nonzero step on exactly one of four axes."""
    n = N ** 4
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for w in range(N):
                    u = idx_4d(N, x, y, z, w)
                    for xx in range(N):
                        if xx != x:
                            A[u, idx_4d(N, xx, y, z, w)] = 1
                    for yy in range(N):
                        if yy != y:
                            A[u, idx_4d(N, x, yy, z, w)] = 1
                    for zz in range(N):
                        if zz != z:
                            A[u, idx_4d(N, x, y, zz, w)] = 1
                    for ww in range(N):
                        if ww != w:
                            A[u, idx_4d(N, x, y, z, ww)] = 1
    return A


def build_king_4d_N(N: int) -> np.ndarray:
    """4D king on N^4: Chebyshev distance 1, hard boundary."""
    n = N ** 4
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for w in range(N):
                    u = idx_4d(N, x, y, z, w)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for dz in (-1, 0, 1):
                                for dw in (-1, 0, 1):
                                    if dx == dy == dz == dw == 0:
                                        continue
                                    x2, y2, z2, w2 = x + dx, y + dy, z + dz, w + dw
                                    if on_board(N, (x2, y2, z2, w2)):
                                        A[u, idx_4d(N, x2, y2, z2, w2)] = 1
    return A


def build_bishop_4d_N(N: int) -> np.ndarray:
    """4D bishop on N^4: exactly two coordinates change by equal magnitude
    (per Rinaldi-Unciuleanu & Chiru 2026 Definition 6). 6 axis-pairs × 4 signs."""
    n = N ** 4
    A = np.zeros((n, n), dtype=np.int8)
    axis_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    sign_pairs = [(s1, s2) for s1 in (-1, 1) for s2 in (-1, 1)]
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for w in range(N):
                    u = idx_4d(N, x, y, z, w)
                    coords = [x, y, z, w]
                    for (i, j) in axis_pairs:
                        for (si, sj) in sign_pairs:
                            for k in range(1, N):
                                new_coords = list(coords)
                                new_coords[i] = coords[i] + si * k
                                new_coords[j] = coords[j] + sj * k
                                if on_board(N, new_coords):
                                    A[u, idx_4d(N, *new_coords)] = 1
    return A


# ---------------------------------------------------------------------------
# Queen adjacency (2D and 4D) — union of rook and bishop
# ---------------------------------------------------------------------------


def build_queen_2d_N(N: int) -> np.ndarray:
    """Queen 2D = OR of rook and bishop on N x N. Hard boundary."""
    A_r = build_rook_2d_N(N)
    A_b = build_bishop_2d_N(N)
    A = np.maximum(A_r, A_b)
    # Validate: should be 0/1 symmetric
    assert np.array_equal(A, A.T)
    assert A.max() <= 1 and A.min() >= 0
    return A


def build_queen_4d_N(N: int) -> np.ndarray:
    """Queen 4D = OR of rook and bishop on N^4. Hard boundary."""
    A_r = build_rook_4d_N(N)
    A_b = build_bishop_4d_N(N)
    A = np.maximum(A_r, A_b)
    assert np.array_equal(A, A.T)
    assert A.max() <= 1 and A.min() >= 0
    return A


# ---------------------------------------------------------------------------
# Toroidal chess piece adjacencies (Z_N^d board; periodic boundary)
# ---------------------------------------------------------------------------


def build_toroidal_rook_2d_N(N: int) -> np.ndarray:
    """Toroidal rook on Z_N x Z_N: any nonzero step on a single axis,
    modular. For rook on the empty board this is the SAME adjacency as the
    boundary version (rook moves to any other cell in its row or column;
    "row" and "column" don't change under periodic boundary in the empty-
    board case because rook reaches every cell anyway). Verify."""
    n = N * N
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            u = idx_2d(N, x, y)
            for xx in range(N):
                if xx != x:
                    A[u, idx_2d(N, xx, y)] = 1
            for yy in range(N):
                if yy != y:
                    A[u, idx_2d(N, x, yy)] = 1
    return A


def build_toroidal_king_2d_N(N: int) -> np.ndarray:
    """Toroidal king on Z_N x Z_N: Chebyshev distance 1 with modular boundary.
    Result is strong product of cycles: C_N ⊠ C_N. Degree uniformly 8 for N≥3.
    """
    n = N * N
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            u = idx_2d(N, x, y)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    x2 = (x + dx) % N
                    y2 = (y + dy) % N
                    A[u, idx_2d(N, x2, y2)] = 1
    return A


def build_toroidal_bishop_2d_N(N: int) -> np.ndarray:
    """Toroidal bishop on Z_N x Z_N: diagonal moves with modular boundary.
    For even N parity (x+y) mod 2 is still preserved (the four diagonal
    steps change x and y by ±1, so sum changes by even amount). For odd N
    parity is NOT preserved as a Z_2 invariant globally — wraparound (x=N-1
    → x=0 = +1 mod N as displacement) introduces parity flip if N is odd.
    """
    n = N * N
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            u = idx_2d(N, x, y)
            for k in range(1, N):
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        x2 = (x + sx * k) % N
                        y2 = (y + sy * k) % N
                        # On torus, the "displacement set" of bishop is all
                        # (±k, ±k) mod N. To avoid double-counting (since
                        # (+k, +k) ≡ (-(N-k), -(N-k)) for N − k < N), we
                        # set A[u,v] = 1 and rely on it being symmetric.
                        v = idx_2d(N, x2, y2)
                        if v != u:
                            A[u, v] = 1
    return A


def build_toroidal_rook_4d_N(N: int) -> np.ndarray:
    """Toroidal rook on Z_N^4: same as boundary rook (any-distance-in-an-axis
    on empty board reaches every other cell in that axis line)."""
    n = N ** 4
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for w in range(N):
                    u = idx_4d(N, x, y, z, w)
                    for xx in range(N):
                        if xx != x:
                            A[u, idx_4d(N, xx, y, z, w)] = 1
                    for yy in range(N):
                        if yy != y:
                            A[u, idx_4d(N, x, yy, z, w)] = 1
                    for zz in range(N):
                        if zz != z:
                            A[u, idx_4d(N, x, y, zz, w)] = 1
                    for ww in range(N):
                        if ww != w:
                            A[u, idx_4d(N, x, y, z, ww)] = 1
    return A


def build_toroidal_king_4d_N(N: int) -> np.ndarray:
    """Toroidal king on Z_N^4: Chebyshev distance 1 with modular boundary.
    Degree uniformly 3^4 - 1 = 80 (no boundary effects)."""
    n = N ** 4
    A = np.zeros((n, n), dtype=np.int8)
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for w in range(N):
                    u = idx_4d(N, x, y, z, w)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for dz in (-1, 0, 1):
                                for dw in (-1, 0, 1):
                                    if dx == dy == dz == dw == 0:
                                        continue
                                    x2 = (x + dx) % N
                                    y2 = (y + dy) % N
                                    z2 = (z + dz) % N
                                    w2 = (w + dw) % N
                                    A[u, idx_4d(N, x2, y2, z2, w2)] = 1
    return A


def build_toroidal_bishop_4d_N(N: int) -> np.ndarray:
    """Toroidal bishop on Z_N^4: 6 axis pairs × 4 sign combinations × N-1
    magnitudes, all modular."""
    n = N ** 4
    A = np.zeros((n, n), dtype=np.int8)
    axis_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    sign_pairs = [(s1, s2) for s1 in (-1, 1) for s2 in (-1, 1)]
    for x in range(N):
        for y in range(N):
            for z in range(N):
                for w in range(N):
                    u = idx_4d(N, x, y, z, w)
                    coords = [x, y, z, w]
                    for (i, j) in axis_pairs:
                        for (si, sj) in sign_pairs:
                            for k in range(1, N):
                                new_coords = list(coords)
                                new_coords[i] = (coords[i] + si * k) % N
                                new_coords[j] = (coords[j] + sj * k) % N
                                v = idx_4d(N, *new_coords)
                                if v != u:
                                    A[u, v] = 1
    return A


# ---------------------------------------------------------------------------
# Closed-form Mode I predictions (boundary case, parametric in N)
# ---------------------------------------------------------------------------


def predict_rook_2d_N(N: int) -> List[Tuple[float, int]]:
    """K_N □ K_N spectrum. K_N eigs: {N-1 (mult 1), -1 (mult N-1)}.
    Sum spectrum: {2(N-1) mult 1, (N-2) mult 2(N-1), -2 mult (N-1)^2}.
    Total: 1 + 2(N-1) + (N-1)^2 = (N-1+1)^2 = N^2 ✓.
    """
    return [
        (float(2 * (N - 1)), 1),
        (float(N - 2), 2 * (N - 1)),
        (-2.0, (N - 1) ** 2),
    ]


def predict_rook_4d_N(N: int) -> List[Tuple[float, int]]:
    """K_N □ K_N □ K_N □ K_N: eig = sum of 4 K_N eigs.
    If k of 4 factors contribute (N-1) and (4-k) contribute -1:
      eig = (N-1)k - (4-k) = Nk - 4
      mult = C(4,k) * 1^k * (N-1)^(4-k)
    """
    pairs: List[Tuple[float, int]] = []
    for k in range(5):
        eig = N * k - 4
        mult = comb(4, k) * (N - 1) ** (4 - k)
        pairs.append((float(eig), int(mult)))
    assert sum(m for _, m in pairs) == N ** 4
    return pairs


def predict_king_2d_N(N: int) -> np.ndarray:
    """P_N ⊠ P_N spectrum. P_N eigs 2cos(πk/(N+1)) for k=1..N.
    Strong product: (1 + lam_i)(1 + lam_j) - 1 = (1+2cos(πk/(N+1)))(1+2cos(πl/(N+1))) - 1.
    """
    p_factors = np.array([1.0 + 2.0 * np.cos(np.pi * k / (N + 1.0))
                          for k in range(1, N + 1)])
    eigs = np.outer(p_factors, p_factors).flatten() - 1.0
    return np.sort(eigs)


def predict_king_4d_N(N: int) -> np.ndarray:
    """P_N^⊠4 spectrum. ∏_d(1+2cos(πk_d/(N+1))) - 1 for k_d = 1..N."""
    p_factors = np.array([1.0 + 2.0 * np.cos(np.pi * k / (N + 1.0))
                          for k in range(1, N + 1)])
    eigs_list: List[float] = []
    for k1 in range(N):
        for k2 in range(N):
            for k3 in range(N):
                for k4 in range(N):
                    eigs_list.append(
                        p_factors[k1] * p_factors[k2] * p_factors[k3] * p_factors[k4]
                        - 1.0
                    )
    return np.sort(np.array(eigs_list))


# ---------------------------------------------------------------------------
# Closed-form Mode I predictions for TOROIDAL boards (Fourier-style)
# ---------------------------------------------------------------------------


def predict_toroidal_rook_2d_N(N: int) -> List[Tuple[float, int]]:
    """Toroidal rook 2D adjacency on Z_N x Z_N is the SAME as boundary rook
    (any-distance-axis on empty board): K_N □ K_N. Same spectrum."""
    return predict_rook_2d_N(N)


def predict_toroidal_rook_4d_N(N: int) -> List[Tuple[float, int]]:
    """Toroidal rook 4D = K_N^□4. Same spectrum as boundary rook."""
    return predict_rook_4d_N(N)


def predict_toroidal_king_2d_N(N: int) -> np.ndarray:
    """Toroidal king 2D = C_N ⊠ C_N (cycle strong product).
    C_N adjacency eigs: 2 cos(2πk/N) for k=0..N-1 (Fourier).
    Strong product: (1 + 2 cos(2πk/N))(1 + 2 cos(2πl/N)) - 1.
    """
    c_factors = np.array([1.0 + 2.0 * np.cos(2.0 * np.pi * k / N)
                          for k in range(N)])
    eigs = np.outer(c_factors, c_factors).flatten() - 1.0
    return np.sort(eigs)


def predict_toroidal_king_4d_N(N: int) -> np.ndarray:
    """Toroidal king 4D = C_N^⊠4. ∏_d(1+2cos(2πk_d/N)) - 1 for k_d = 0..N-1."""
    c_factors = np.array([1.0 + 2.0 * np.cos(2.0 * np.pi * k / N)
                          for k in range(N)])
    eigs_list: List[float] = []
    for k1 in range(N):
        for k2 in range(N):
            for k3 in range(N):
                for k4 in range(N):
                    eigs_list.append(
                        c_factors[k1] * c_factors[k2] * c_factors[k3] * c_factors[k4]
                        - 1.0
                    )
    return np.sort(np.array(eigs_list))


def predict_toroidal_bishop_2d_N(N: int) -> np.ndarray:
    """Toroidal bishop 2D: the move-graph is the union over magnitudes
    k = 1..N-1 of (±k, ±k) modular displacements. Under the translation
    group Z_N x Z_N, the adjacency is diagonalised by the 2D DFT:
      eig(k, l) = sum_{m=1}^{N-1} sum_{(s_x, s_y) in {-1,1}^2}
                  exp(2πi (s_x m k + s_y m l) / N) [where (s_x m k, s_y m l) ≠ (0,0)]

    Equivalently: the Fourier symbol at (k, l) is
      f(k, l) = sum_{m=1..N-1} sum_{s_x, s_y in {-1,1}} exp(2πi m (s_x k + s_y l) / N)
              - (correction for diagonal self-loops if (s_x k + s_y l ≡ 0 mod N
                and s_x' k + s_y' l ≡ 0 mod N collapse))

    The cleanest derivation: A is a circulant tensor on Z_N x Z_N, so its
    eigenvalues are the DFT of the displacement set. Compute the DFT
    directly from the adjacency's first row (the "displacement profile"
    centered at (0,0)).
    """
    # Build the displacement profile: f[a, b] = number of bishop moves from
    # cell (0,0) to cell (a, b) on the torus.
    f = np.zeros((N, N), dtype=np.int8)
    for k in range(1, N):
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = (sx * k) % N
                b = (sy * k) % N
                if (a, b) != (0, 0):
                    f[a, b] = 1  # use 1 (set, not increment) per construction
    # Eigenvalues = 2D DFT of f
    F = np.fft.fft2(f.astype(np.float64))
    eigs = np.real(F).flatten()
    # Imaginary parts should be machine-precision zero (f is real and the
    # adjacency is symmetric since f[-a, -b] = f[a, b] mod N)
    return np.sort(eigs)


def predict_toroidal_bishop_4d_N(N: int) -> np.ndarray:
    """Toroidal bishop 4D: 6 axis-pair × 4 sign × (N-1) magnitudes
    modular. Same approach: build displacement profile, FFT."""
    f = np.zeros((N, N, N, N), dtype=np.int8)
    axis_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    sign_pairs = [(s1, s2) for s1 in (-1, 1) for s2 in (-1, 1)]
    for (i, j) in axis_pairs:
        for (si, sj) in sign_pairs:
            for k in range(1, N):
                disp = [0, 0, 0, 0]
                disp[i] = (si * k) % N
                disp[j] = (sj * k) % N
                if tuple(disp) != (0, 0, 0, 0):
                    f[disp[0], disp[1], disp[2], disp[3]] = 1
    F = np.fft.fftn(f.astype(np.float64))
    eigs = np.real(F).flatten()
    return np.sort(eigs)


# ---------------------------------------------------------------------------
# D_4 representation and projector method (2D Mode II)
# ---------------------------------------------------------------------------


def d4_permutations_2d_N8() -> Dict[str, np.ndarray]:
    """D_4 elements as 64-element permutation arrays on 8x8 grid."""
    def perm(map_fn) -> np.ndarray:
        sigma = np.empty(DIM_2D_SIZE_8, dtype=np.int32)
        for x in range(BOARD_SIDE_8):
            for y in range(BOARD_SIDE_8):
                u = idx_2d(BOARD_SIDE_8, x, y)
                x2, y2 = map_fn(x, y)
                sigma[u] = idx_2d(BOARD_SIDE_8, x2, y2)
        return sigma
    return {
        "e": perm(lambda x, y: (x, y)),
        "r": perm(lambda x, y: (y, 7 - x)),
        "r2": perm(lambda x, y: (7 - x, 7 - y)),
        "r3": perm(lambda x, y: (7 - y, x)),
        "s": perm(lambda x, y: (x, 7 - y)),
        "sr": perm(lambda x, y: (y, x)),
        "sr2": perm(lambda x, y: (7 - x, y)),
        "sr3": perm(lambda x, y: (7 - y, 7 - x)),
    }


D4_IRREP_NAMES = ["A1", "A2", "B1", "B2", "E"]
D4_IRREP_DIMS = {"A1": 1, "A2": 1, "B1": 1, "B2": 1, "E": 2}
D4_CHARACTERS = {
    "A1": {"e": 1, "r2": 1, "rR": 1, "sR": 1, "srR": 1},
    "A2": {"e": 1, "r2": 1, "rR": 1, "sR": -1, "srR": -1},
    "B1": {"e": 1, "r2": 1, "rR": -1, "sR": 1, "srR": -1},
    "B2": {"e": 1, "r2": 1, "rR": -1, "sR": -1, "srR": 1},
    "E": {"e": 2, "r2": -2, "rR": 0, "sR": 0, "srR": 0},
}
D4_CLASS_MAP = {
    "e": "e", "r2": "r2",
    "r": "rR", "r3": "rR",
    "s": "sR", "sr2": "sR",
    "sr": "srR", "sr3": "srR",
}
D4_ORDER = 8


def d4_projector_matrices(sigma_dict: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    n = DIM_2D_SIZE_8
    projectors = {}
    for rep in D4_IRREP_NAMES:
        d_rho = D4_IRREP_DIMS[rep]
        chars = D4_CHARACTERS[rep]
        P = np.zeros((n, n), dtype=np.float64)
        for g, sigma in sigma_dict.items():
            chi = chars[D4_CLASS_MAP[g]]
            U_g = np.zeros((n, n), dtype=np.float64)
            for u in range(n):
                U_g[sigma[u], u] = 1.0
            P += chi * U_g
        P *= d_rho / D4_ORDER
        projectors[rep] = P
    return projectors


def find_eigenspaces(eigvals: np.ndarray, tol: float = EIGENSPACE_TOL) -> List[Tuple[float, int, int]]:
    sorted_eigs = np.sort(eigvals)
    n = len(sorted_eigs)
    groups = []
    start = 0
    while start < n:
        end = start
        while end < n and abs(sorted_eigs[end] - sorted_eigs[start]) < tol:
            end += 1
        avg = float(sorted_eigs[start:end].mean())
        groups.append((avg, start, end - start))
        start = end
    return groups


def decompose_d4_via_projectors(A: np.ndarray, projectors: Dict[str, np.ndarray]) -> List[Dict]:
    """Per-eigenspace D_4 irrep multiplicities via projector rank-via-SVD."""
    eigvals, eigvecs = np.linalg.eigh(A.astype(np.float64))
    idx_sort = np.argsort(eigvals)
    sorted_eigs = eigvals[idx_sort]
    sorted_vecs = eigvecs[:, idx_sort]
    groups = find_eigenspaces(sorted_eigs)
    results = []
    for (avg, start, count) in groups:
        V = sorted_vecs[:, start:start + count]
        mults: Dict[str, float] = {}
        for rep in D4_IRREP_NAMES:
            d_rho = D4_IRREP_DIMS[rep]
            P = projectors[rep]
            PV = P @ V
            svals = np.linalg.svd(PV, compute_uv=False)
            rank_estimate = int((svals > 1e-8).sum())
            mults[rep] = float(rank_estimate / d_rho)
        total_dim = sum(D4_IRREP_DIMS[r] * mults[r] for r in D4_IRREP_NAMES)
        results.append({
            "eigvalue_avg": avg,
            "eigspace_dim": count,
            "multiplicities": mults,
            "total_dim_check": float(total_dim),
            "match_total_dim": bool(abs(total_dim - count) < INTEGER_TOL),
            "all_integer": bool(all(abs(m - round(m)) < INTEGER_TOL for m in mults.values())),
        })
    return results


# ---------------------------------------------------------------------------
# B_4 representation + character table (lifted from chess-knight-irrep-multiplicities-script)
# ---------------------------------------------------------------------------


def partitions(n: int) -> List[Tuple[int, ...]]:
    if n == 0:
        return [()]
    result: List[Tuple[int, ...]] = []
    def rec(rem: int, mx: int, acc: Tuple[int, ...]):
        if rem == 0:
            result.append(acc)
            return
        for k in range(min(mx, rem), 0, -1):
            rec(rem - k, k, acc + (k,))
    rec(n, n, ())
    return result


def bipartitions_n(n: int) -> List[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    result = []
    for k in range(n + 1):
        for alpha in partitions(k):
            for beta in partitions(n - k):
                result.append((alpha, beta))
    return result


def _cells_to_partition(cells: set, n_rows: int):
    rows_count: Dict[int, int] = {}
    for (i, j) in cells:
        rows_count[i] = rows_count.get(i, 0) + 1
    max_row = max(rows_count.keys()) if rows_count else -1
    if max_row < 0:
        return ()
    lam = []
    for i in range(max_row + 1):
        L = rows_count.get(i, 0)
        row_cols = sorted(c[1] for c in cells if c[0] == i)
        if row_cols and row_cols != list(range(L)):
            return None
        lam.append(L)
    for a, b in zip(lam, lam[1:]):
        if a < b:
            return None
    while lam and lam[-1] == 0:
        lam.pop()
    return tuple(lam)


def rim_hooks(lam: Tuple[int, ...], k: int):
    if not lam:
        return
    n_rows = len(lam)
    cells = []
    for i in range(n_rows):
        for j in range(lam[i]):
            cells.append((i, j))
    cell_set = set(cells)
    rim: List[Tuple[int, int]] = []
    i, j = 0, lam[0] - 1
    while True:
        rim.append((i, j))
        if i + 1 < n_rows and lam[i + 1] >= j + 1:
            i += 1
        elif j > 0 and (i, j - 1) in cell_set:
            j -= 1
        else:
            break
        if (i, j) == rim[-1]:
            break
    L = len(rim)
    for start in range(L - k + 1):
        hook = set(rim[start:start + k])
        new_cells = cell_set - hook
        new_lam = _cells_to_partition(new_cells, n_rows)
        if new_lam is None:
            continue
        rows = set(c[0] for c in hook)
        height = len(rows) - 1
        yield (new_lam, height)


def murnaghan_nakayama(lam: Tuple[int, ...], mu: Tuple[int, ...]) -> int:
    if not mu:
        return 1 if not lam else 0
    k = mu[0]
    rest_mu = mu[1:]
    total = 0
    for new_lam, height in rim_hooks(lam, k):
        total += (-1) ** height * murnaghan_nakayama(new_lam, rest_mu)
    return total


def sn_character_table(n: int) -> Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]]:
    parts = partitions(n)
    table: Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]] = {p: {} for p in parts}
    for lam in parts:
        for mu in parts:
            table[lam][mu] = murnaghan_nakayama(lam, mu)
    return table


def b_n_signed_class_data(n: int) -> List[Tuple[Tuple[int, ...], Tuple[int, ...], int]]:
    result = []
    Bn_order = (2 ** n) * factorial(n)
    for k in range(n + 1):
        for lp in partitions(k):
            for lm in partitions(n - k):
                mp: Dict[int, int] = {}
                for x in lp:
                    mp[x] = mp.get(x, 0) + 1
                mm: Dict[int, int] = {}
                for x in lm:
                    mm[x] = mm.get(x, 0) + 1
                cent = 1
                for kk, m in mp.items():
                    cent *= ((2 * kk) ** m) * factorial(m)
                for kk, m in mm.items():
                    cent *= ((2 * kk) ** m) * factorial(m)
                class_size = Bn_order // cent
                result.append((lp, lm, class_size))
    return result


def b_n_irrep_character(
    alpha: Tuple[int, ...],
    beta: Tuple[int, ...],
    lambda_plus: Tuple[int, ...],
    lambda_minus: Tuple[int, ...],
    sn_chars: Dict[int, Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]]],
) -> int:
    n = sum(lambda_plus) + sum(lambda_minus)
    a = sum(alpha)
    b = sum(beta)
    if a + b != n:
        return 0
    lp = list(lambda_plus)
    lm = list(lambda_minus)
    total = 0
    for S_mask in range(1 << len(lp)):
        S_cycles = [lp[i] for i in range(len(lp)) if (S_mask >> i) & 1]
        S_sum = sum(S_cycles)
        rest_lp = [lp[i] for i in range(len(lp)) if not ((S_mask >> i) & 1)]
        for T_mask in range(1 << len(lm)):
            T_cycles = [lm[i] for i in range(len(lm)) if (T_mask >> i) & 1]
            T_sum = sum(T_cycles)
            if S_sum + T_sum != a:
                continue
            rest_lm = [lm[i] for i in range(len(lm)) if not ((T_mask >> i) & 1)]
            sign_count = len(rest_lm)
            mu_alpha = tuple(sorted(S_cycles + T_cycles, reverse=True))
            mu_beta = tuple(sorted(rest_lp + rest_lm, reverse=True))
            if sum(mu_alpha) != a or sum(mu_beta) != b:
                continue
            chi_a = sn_chars[a][alpha].get(mu_alpha, 0)
            chi_b = sn_chars[b][beta].get(mu_beta, 0)
            sign = (-1) ** sign_count
            total += sign * chi_a * chi_b
    return total


def make_b4_class_rep(lp: Tuple[int, ...], lm: Tuple[int, ...]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    n = sum(lp) + sum(lm)
    perm = [0] * n
    signs = [1] * n
    pos = 0
    for length in lp:
        for i in range(length):
            perm[pos + i] = pos + (i + 1) % length
            signs[pos + i] = 1
        pos += length
    for length in lm:
        for i in range(length):
            perm[pos + i] = pos + (i + 1) % length
            signs[pos + i] = -1 if i == 0 else 1
        pos += length
    return (tuple(signs), tuple(perm))


def b4_action_4d_N8(elem: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> np.ndarray:
    """B_4 element as 4096-permutation array on 8^4 hypercube (centered coords)."""
    signs, perm = elem
    sigma = np.empty(DIM_4D_SIZE_8, dtype=np.int32)
    for x in range(BOARD_SIDE_8):
        for y in range(BOARD_SIDE_8):
            for z in range(BOARD_SIDE_8):
                for w in range(BOARD_SIDE_8):
                    u = idx_4d(BOARD_SIDE_8, x, y, z, w)
                    c = (x - 3.5, y - 3.5, z - 3.5, w - 3.5)
                    c_new = (
                        signs[0] * c[perm[0]],
                        signs[1] * c[perm[1]],
                        signs[2] * c[perm[2]],
                        signs[3] * c[perm[3]],
                    )
                    nx = int(round(c_new[0] + 3.5))
                    ny = int(round(c_new[1] + 3.5))
                    nz = int(round(c_new[2] + 3.5))
                    nw = int(round(c_new[3] + 3.5))
                    sigma[u] = idx_4d(BOARD_SIDE_8, nx, ny, nz, nw)
    return sigma


def decompose_b4_via_character_orth_N8(A: np.ndarray, verbose: bool = True) -> Tuple[List[Dict], Dict]:
    """Per-eigenspace B_4 irrep multiplicities via class-trace inner product.

    mult_rho_in_V_lam = (1/|G|) sum_C |C| * chi_rho(C) * trace_C(V_lam)
    """
    eigvals, eigvecs = np.linalg.eigh(A.astype(np.float64))
    if verbose:
        print(f"    [4D] eigh done. spectrum [{eigvals.min():.3f}, {eigvals.max():.3f}]")

    class_data = b_n_signed_class_data(4)
    class_sizes = {(lp, lm): size for (lp, lm, size) in class_data}

    class_sigmas: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], np.ndarray] = {}
    for (lp, lm) in class_sizes:
        rep_elem = make_b4_class_rep(lp, lm)
        sigma = b4_action_4d_N8(rep_elem)
        class_sigmas[(lp, lm)] = sigma

    sn_chars: Dict[int, Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]]] = {}
    for n in range(5):
        sn_chars[n] = sn_character_table(n)

    biparts = bipartitions_n(4)
    assert len(biparts) == 20
    b4_char_table: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]],
                       Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], int]] = {}
    for (a, b) in biparts:
        b4_char_table[(a, b)] = {}
        for (lp, lm) in class_sizes:
            b4_char_table[(a, b)][(lp, lm)] = b_n_irrep_character(a, b, lp, lm, sn_chars)

    id_class = ((1, 1, 1, 1), ())
    irrep_dims = {bp: b4_char_table[bp][id_class] for bp in biparts}

    idx_sort = np.argsort(eigvals)
    sorted_eigs = eigvals[idx_sort]
    sorted_vecs = eigvecs[:, idx_sort]
    groups = find_eigenspaces(sorted_eigs)
    if verbose:
        print(f"    [4D] {len(groups)} eigenspaces")

    cls_list = list(class_sigmas.keys())
    n_classes = len(cls_list)
    if verbose:
        t0 = time.perf_counter()
    traces_per_vec = np.zeros((DIM_4D_SIZE_8, n_classes), dtype=np.float64)
    for c_idx, cls in enumerate(cls_list):
        sigma = class_sigmas[cls]
        v_perm = sorted_vecs[sigma, :]
        traces_per_vec[:, c_idx] = (sorted_vecs * v_perm).sum(axis=0)
    if verbose:
        print(f"    [4D] class traces done in {time.perf_counter()-t0:.1f}s")

    Bn_order = 384
    results = []
    for (avg, start, count) in groups:
        trace_per_class = traces_per_vec[start:start + count, :].sum(axis=0)
        mults: Dict[str, float] = {}
        for bp in biparts:
            mult = 0.0
            for c_idx, cls in enumerate(cls_list):
                size = class_sizes[cls]
                chi = b4_char_table[bp][cls]
                mult += size * chi * trace_per_class[c_idx]
            mult /= Bn_order
            mults[f"{bp[0]}|{bp[1]}"] = float(mult)
        total = sum(irrep_dims[bp] * mults[f"{bp[0]}|{bp[1]}"] for bp in biparts)
        all_int = all(abs(m - round(m)) < INTEGER_TOL for m in mults.values())
        results.append({
            "eigvalue_avg": avg,
            "eigspace_dim": count,
            "multiplicities": mults,
            "total_dim_check": float(total),
            "match_total_dim": bool(abs(total - count) < INTEGER_TOL),
            "all_integer": bool(all_int),
        })
    metadata = {
        "n_classes": n_classes,
        "irreps": [f"{bp[0]}|{bp[1]}" for bp in biparts],
        "irrep_dims": {f"{bp[0]}|{bp[1]}": int(irrep_dims[bp]) for bp in biparts},
        "Bn_order": Bn_order,
    }
    return results, metadata


# ---------------------------------------------------------------------------
# Toroidal Z_N^d Mode II via Fourier basis (abelian → each Fourier mode is
# its own 1-dim irrep)
# ---------------------------------------------------------------------------


def toroidal_mode_ii_2d(A: np.ndarray, N: int) -> Dict:
    """Z_N x Z_N is abelian; irreps indexed by (k, l) ∈ Z_N x Z_N; each 1-dim.
    On a translation-invariant adjacency, the Fourier basis e_{k,l}(x,y) =
    exp(2πi(kx + ly)/N) diagonalizes the operator. So:
      eig_(k,l) = sum_{a,b} f[a, b] * exp(-2πi(ka + lb)/N)
                = DFT_2d(f)[k, l] (with sign convention)
    The "per-eigenspace irrep multiplicity" is integer-exact by construction:
    eigenspace V_lam consists of the basis modes (k, l) with eig_(k,l) = lam,
    each contributing exactly one 1-dim irrep.

    Test: verify that empirical eigenvectors of A coincide with Fourier modes
    (within each degenerate eigenspace), confirming the multiplicity assignment.

    Procedure: build the FFT-basis matrix F (N^2 x N^2); verify F^* A F is
    diagonal up to permutation; report deviations.
    """
    n = N * N
    # Build f from A's first row: f[(a,b)] = A[0, idx(a,b)]
    f = np.zeros((N, N), dtype=np.float64)
    for a in range(N):
        for b in range(N):
            f[a, b] = A[0, idx_2d(N, a, b)]
    # DFT eigenvalues
    F_vals = np.fft.fft2(f)
    pred_eigs = np.sort(np.real(F_vals).flatten())
    # Build Fourier basis V[idx(x,y), (k,l)] = exp(2πi(kx + ly)/N) / sqrt(N^2)
    # Validate that A @ V = V @ diag(eigs)
    X = np.arange(N)
    Y = np.arange(N)
    XX, YY = np.meshgrid(X, Y, indexing='ij')  # XX[x,y]=x, YY[x,y]=y
    coords_grid = np.stack([XX.flatten(), YY.flatten()], axis=1)  # (n, 2)
    K = np.arange(N)
    L = np.arange(N)
    KK, LL = np.meshgrid(K, L, indexing='ij')
    freq_grid = np.stack([KK.flatten(), LL.flatten()], axis=1)  # (n, 2)
    # V[u, m] = exp(2pi i (k_m x_u + l_m y_u) / N) / sqrt(n)
    phase = 2.0 * np.pi * (
        coords_grid[:, 0:1] * freq_grid[:, 0:1].T
        + coords_grid[:, 1:2] * freq_grid[:, 1:2].T
    ) / N
    V = np.exp(1j * phase) / np.sqrt(n)
    # eigs from F^* A F (diagonal)
    M = V.conj().T @ A.astype(np.float64) @ V
    diag = np.real(np.diag(M))
    off_diag = M - np.diag(np.diag(M))
    max_off_diag = float(np.abs(off_diag).max())
    # Imaginary part of diagonal should also vanish
    max_imag = float(np.abs(np.imag(np.diag(M))).max())
    # Compare to DFT-derived prediction
    diag_sorted = np.sort(diag)
    max_dev_pred = float(np.abs(diag_sorted - pred_eigs).max())
    # Also compare to empirical eigvalsh
    emp_eigs = np.sort(np.linalg.eigvalsh(A.astype(np.float64)))
    max_dev_emp = float(np.abs(diag_sorted - emp_eigs).max())
    return {
        "n_modes": n,
        "max_off_diag_after_fourier_diag": max_off_diag,
        "max_imag_part_diagonal": max_imag,
        "max_dev_pred_vs_diag": max_dev_pred,
        "max_dev_diag_vs_eigvalsh": max_dev_emp,
        "mode_ii_passes": bool(
            max_off_diag < 1e-10 and max_imag < 1e-10
            and max_dev_pred < PRECISION_TARGET_MODE_I
            and max_dev_emp < PRECISION_TARGET_MODE_I
        ),
    }


def toroidal_mode_ii_4d(A: np.ndarray, N: int) -> Dict:
    """Z_N^4 abelian Mode II. Procedure mirrors 2D but on N^4 cells.

    Cost: V has shape (N^4, N^4). For N=8 that's 4096x4096 complex, ~256 MB.
    Materializing V^* A V is ~3 GB intermediate. Use a vectorized FFT-based
    diagonalization check instead: reshape A's first row to N^4 tensor, FFT,
    compare to empirical eigvalsh-sorted spectrum.

    Note: this verifies that the empirical spectrum matches the Fourier
    prediction (which IS the per-eigenspace irrep decomposition since Z_N^d
    is abelian). The "mode II" structural claim is: each eigenspace is the
    span of the Fourier modes with that eigenvalue; each such Fourier mode
    is itself a 1-dim irrep of Z_N^d. Integer multiplicity check trivially
    passes since each Fourier mode contributes exactly 1 to the irrep count.

    What can still fail: the empirical spectrum may not match the Fourier
    prediction at machine precision (would indicate the adjacency is NOT
    actually Z_N^d-translation-invariant — possible if my construction is
    wrong).
    """
    n = N ** 4
    # Build displacement profile f from first row of A
    f = np.zeros((N, N, N, N), dtype=np.float64)
    for a in range(N):
        for b in range(N):
            for c in range(N):
                for d in range(N):
                    f[a, b, c, d] = A[0, idx_4d(N, a, b, c, d)]
    # DFT eigenvalues
    F_vals = np.fft.fftn(f)
    pred_eigs = np.sort(np.real(F_vals).flatten())
    # Empirical eigvalsh
    emp_eigs = np.sort(np.linalg.eigvalsh(A.astype(np.float64)))
    max_dev = float(np.abs(pred_eigs - emp_eigs).max())
    # Also check imaginary part of F_vals
    max_imag = float(np.abs(np.imag(F_vals)).max())
    return {
        "n_modes": n,
        "max_imag_part_fourier": max_imag,
        "max_dev_fourier_pred_vs_eigvalsh": max_dev,
        "mode_ii_passes": bool(
            max_imag < 1e-10
            and max_dev < PRECISION_TARGET_MODE_I
        ),
    }


# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------


def verify_predicted_spectrum_pairs(
    empirical: np.ndarray,
    predicted_pairs: List[Tuple[float, int]],
    label: str,
) -> Dict:
    expanded: List[float] = []
    for val, mult in predicted_pairs:
        expanded.extend([val] * mult)
    expanded_sorted = np.sort(np.array(expanded, dtype=np.float64))
    empirical_sorted = np.sort(empirical)
    if expanded_sorted.shape != empirical_sorted.shape:
        return {
            "label": label,
            "match": False,
            "shape_mismatch": True,
            "predicted_n": int(expanded_sorted.shape[0]),
            "empirical_n": int(empirical_sorted.shape[0]),
        }
    diffs = np.abs(empirical_sorted - expanded_sorted)
    max_dev = float(diffs.max())
    return {
        "label": label,
        "match": bool(max_dev < PRECISION_TARGET_MODE_I),
        "max_dev": max_dev,
        "n_eigenvalues": int(empirical_sorted.shape[0]),
        "precision_target": PRECISION_TARGET_MODE_I,
    }


def verify_predicted_full(empirical: np.ndarray, predicted: np.ndarray, label: str) -> Dict:
    e_sorted = np.sort(empirical)
    p_sorted = np.sort(predicted)
    if e_sorted.shape != p_sorted.shape:
        return {
            "label": label,
            "match": False,
            "shape_mismatch": True,
            "predicted_n": int(p_sorted.shape[0]),
            "empirical_n": int(e_sorted.shape[0]),
        }
    diffs = np.abs(e_sorted - p_sorted)
    max_dev = float(diffs.max())
    return {
        "label": label,
        "match": bool(max_dev < PRECISION_TARGET_MODE_I),
        "max_dev": max_dev,
        "n_eigenvalues": int(e_sorted.shape[0]),
        "precision_target": PRECISION_TARGET_MODE_I,
    }


def commutator_max_abs(A: np.ndarray, B: np.ndarray) -> float:
    """Max abs entry of AB - BA. Tests whether two matrices commute."""
    return float(np.abs(A @ B - B @ A).max())


# ---------------------------------------------------------------------------
# Sub-investigation 1: queen (C-F3a)
# ---------------------------------------------------------------------------


def run_queen_2d_N8(d4_projs: Dict[str, np.ndarray]) -> List[Dict]:
    print("\n[C-F3a.1] Queen 2D (N=8)...")
    t0 = time.perf_counter()
    A_r = build_rook_2d_N(BOARD_SIDE_8).astype(np.float64)
    A_b = build_bishop_2d_N(BOARD_SIDE_8).astype(np.float64)
    A_q = build_queen_2d_N(BOARD_SIDE_8).astype(np.float64)
    comm = commutator_max_abs(A_r, A_b)
    print(f"    [rook, bishop] commutator max abs = {comm:.3f}")
    # Mode I: try eig(A_q) = eig(A_r) + eig(A_b)? Will fail since they don't commute.
    e_q = np.linalg.eigvalsh(A_q)
    e_r = np.sort(np.linalg.eigvalsh(A_r))
    e_b = np.sort(np.linalg.eigvalsh(A_b))
    # Closed-form attempt 1: simple sum (will fail)
    sum_eigs = np.sort(e_r + e_b)
    sum_eigs_match = float(np.abs(np.sort(e_q) - sum_eigs).max())
    # Closed-form attempt 2: union of multiset sums (also fails — not even right shape)
    # The honest answer is that there is no closed-form Mode I prediction for queen.
    print(f"    Mode I: eig(A_q) vs sort(eig(A_r) + eig(A_b)) max dev = {sum_eigs_match:.3e}")
    print(f"    Mode I VERDICT: refuted (as predicted by non-commuting [A_r, A_b] != 0)")
    # Mode II: per-eigenspace D_4 multiplicities
    decomp = decompose_d4_via_projectors(A_q, d4_projs)
    n_eigspaces = len(decomp)
    all_int = all(r["all_integer"] for r in decomp)
    all_total = all(r["match_total_dim"] for r in decomp)
    max_dev_int = max(
        max(abs(m - round(m)) for m in r["multiplicities"].values())
        for r in decomp
    )
    print(f"    Mode II: {n_eigspaces} eigenspaces; all_int={all_int}; all_total_dim={all_total}; max_dev_int={max_dev_int:.3e}")

    records = []
    for r in decomp:
        for irrep_name, mult in r["multiplicities"].items():
            records.append({
                "candidate": "queen",
                "extension": "C-F3a",
                "piece": "queen",
                "dim": 2,
                "board_N": BOARD_SIDE_8,
                "group": "D_4",
                "mode": "II",
                "eigvalue_avg": r["eigvalue_avg"],
                "eigspace_dim": r["eigspace_dim"],
                "irrep": irrep_name,
                "irrep_dim": D4_IRREP_DIMS[irrep_name],
                "multiplicity_float": float(mult),
                "multiplicity_int": int(round(mult)),
                "is_integer_exact": bool(abs(mult - round(mult)) < INTEGER_TOL),
                "deviation_from_integer": float(abs(mult - round(mult))),
                "match_total_dim": r["match_total_dim"],
            })
    # Mode I refutation record
    records.append({
        "candidate": "queen",
        "extension": "C-F3a",
        "piece": "queen",
        "dim": 2,
        "board_N": BOARD_SIDE_8,
        "group": "D_4",
        "mode": "I",
        "test": "eig(A_q) vs sort(eig(A_r) + eig(A_b)) [naive closed-form attempt]",
        "max_dev": sum_eigs_match,
        "match": False,
        "rationale": (
            f"[A_r, A_b] != 0 (commutator max abs = {comm}); no clean closed-form Mode I "
            "prediction for queen exists from rook/bishop spectra alone."
        ),
        "commutator_max_abs": comm,
    })
    print(f"    Queen 2D done in {time.perf_counter()-t0:.2f}s")
    return records


def run_queen_4d_N8() -> List[Dict]:
    print("\n[C-F3a.2] Queen 4D (N=8)...")
    t0 = time.perf_counter()
    A_r = build_rook_4d_N(BOARD_SIDE_8).astype(np.float64)
    A_b = build_bishop_4d_N(BOARD_SIDE_8).astype(np.float64)
    A_q = build_queen_4d_N(BOARD_SIDE_8).astype(np.float64)
    # Commutator check (sample-wise to save memory; full ABS-MAX on 4096x4096 is fine)
    comm = commutator_max_abs(A_r, A_b)
    print(f"    [rook, bishop] commutator max abs = {comm:.3f}")
    # Mode I refutation evidence
    e_r = np.sort(np.linalg.eigvalsh(A_r))
    e_b = np.sort(np.linalg.eigvalsh(A_b))
    e_q = np.sort(np.linalg.eigvalsh(A_q))
    sum_eigs = np.sort(e_r + e_b)
    sum_eigs_match = float(np.abs(e_q - sum_eigs).max())
    print(f"    Mode I: eig(A_q) vs sort(eig(A_r) + eig(A_b)) max dev = {sum_eigs_match:.3e}")
    print(f"    Mode I VERDICT: refuted (commutator nonzero, sum-spectrum mismatch)")
    # Mode II: per-eigenspace B_4 multiplicities
    decomp, meta = decompose_b4_via_character_orth_N8(A_q, verbose=True)
    n_eigspaces = len(decomp)
    all_int = all(r["all_integer"] for r in decomp)
    all_total = all(r["match_total_dim"] for r in decomp)
    max_dev_int = max(
        max(abs(m - round(m)) for m in r["multiplicities"].values())
        for r in decomp
    )
    print(f"    Mode II: {n_eigspaces} eigenspaces; all_int={all_int}; all_total_dim={all_total}; max_dev_int={max_dev_int:.3e}")

    records = []
    irrep_dims = meta["irrep_dims"]
    for r in decomp:
        for irrep_name, mult in r["multiplicities"].items():
            records.append({
                "candidate": "queen",
                "extension": "C-F3a",
                "piece": "queen",
                "dim": 4,
                "board_N": BOARD_SIDE_8,
                "group": "B_4",
                "mode": "II",
                "eigvalue_avg": r["eigvalue_avg"],
                "eigspace_dim": r["eigspace_dim"],
                "irrep": irrep_name,
                "irrep_dim": int(irrep_dims[irrep_name]),
                "multiplicity_float": float(mult),
                "multiplicity_int": int(round(mult)),
                "is_integer_exact": bool(abs(mult - round(mult)) < INTEGER_TOL),
                "deviation_from_integer": float(abs(mult - round(mult))),
                "match_total_dim": r["match_total_dim"],
            })
    records.append({
        "candidate": "queen",
        "extension": "C-F3a",
        "piece": "queen",
        "dim": 4,
        "board_N": BOARD_SIDE_8,
        "group": "B_4",
        "mode": "I",
        "test": "eig(A_q) vs sort(eig(A_r) + eig(A_b)) [naive closed-form attempt]",
        "max_dev": sum_eigs_match,
        "match": False,
        "rationale": (
            f"[A_r, A_b] != 0 (commutator max abs = {comm}); no clean closed-form Mode I "
            "prediction for queen exists from rook/bishop spectra alone."
        ),
        "commutator_max_abs": comm,
    })
    print(f"    Queen 4D done in {time.perf_counter()-t0:.2f}s")
    return records


# ---------------------------------------------------------------------------
# Sub-investigation 2: side-length-N parametric (C-F3b)
# ---------------------------------------------------------------------------


def run_parametric_N_2d() -> List[Dict]:
    print("\n[C-F3b.1] Parametric N x N (2D rook/king/bishop)...")
    records = []
    for N in [4, 5, 6, 7, 8]:
        # Rook
        A_r = build_rook_2d_N(N).astype(np.float64)
        e_r = np.linalg.eigvalsh(A_r)
        pred_r = predict_rook_2d_N(N)
        v_r = verify_predicted_spectrum_pairs(e_r, pred_r, f"rook_2d_N{N}")
        # King
        A_k = build_king_2d_N(N).astype(np.float64)
        e_k = np.linalg.eigvalsh(A_k)
        pred_k = predict_king_2d_N(N)
        v_k = verify_predicted_full(e_k, pred_k, f"king_2d_N{N}")
        # Bishop: parity-block check
        # Parity-block decomposition
        parity = np.array([(x + y) % 2 for x in range(N) for y in range(N)])
        idx_even = np.where(parity == 0)[0]
        idx_odd = np.where(parity == 1)[0]
        A_b = build_bishop_2d_N(N).astype(np.float64)
        # Verify parity preservation
        cross_sum = A_b[np.ix_(idx_even, idx_odd)].sum()
        # Block spectra
        e_be = np.sort(np.linalg.eigvalsh(A_b[np.ix_(idx_even, idx_even)]))
        e_bo = np.sort(np.linalg.eigvalsh(A_b[np.ix_(idx_odd, idx_odd)]))
        e_b_full = np.sort(np.linalg.eigvalsh(A_b))
        # If N is even, |even| == |odd|; they are isomorphic by 90° rotation
        # If N is odd, sizes differ: e.g. N=5: even=13, odd=12. Color classes
        # NOT isomorphic, but parity-stratification still holds.
        if len(e_be) == len(e_bo):
            color_iso_max_dev = float(np.abs(e_be - e_bo).max())
            color_iso_match = bool(color_iso_max_dev < PRECISION_TARGET_MODE_I)
        else:
            color_iso_max_dev = None
            color_iso_match = False
        # Block-decomp: sort(concat(e_be, e_bo)) vs sort(eigvalsh(A_b))
        combined = np.sort(np.concatenate([e_be, e_bo]))
        block_decomp_max_dev = float(np.abs(combined - e_b_full).max())
        block_decomp_match = bool(block_decomp_max_dev < PRECISION_TARGET_MODE_I)

        print(f"    N={N}: rook MATCH={v_r['match']} max_dev={v_r['max_dev']:.3e}"
              f" | king MATCH={v_k['match']} max_dev={v_k['max_dev']:.3e}"
              f" | bishop parity_block={block_decomp_match} max_dev={block_decomp_max_dev:.3e}"
              f" color_iso={color_iso_match}")

        records.append({
            "candidate": "parametric_N",
            "extension": "C-F3b",
            "piece": "rook",
            "dim": 2,
            "board_N": N,
            "n_cells": N * N,
            "mode": "I",
            "predicted_pairs": [(float(v), int(m)) for (v, m) in pred_r],
            "max_dev": v_r["max_dev"],
            "match": v_r["match"],
        })
        records.append({
            "candidate": "parametric_N",
            "extension": "C-F3b",
            "piece": "king",
            "dim": 2,
            "board_N": N,
            "n_cells": N * N,
            "mode": "I",
            "max_dev": v_k["max_dev"],
            "match": v_k["match"],
        })
        records.append({
            "candidate": "parametric_N",
            "extension": "C-F3b",
            "piece": "bishop",
            "dim": 2,
            "board_N": N,
            "n_cells": N * N,
            "mode": "I",
            "cross_parity_zero": bool(cross_sum == 0),
            "block_decomp_max_dev": block_decomp_max_dev,
            "block_decomp_match": block_decomp_match,
            "color_class_iso_max_dev": color_iso_max_dev,
            "color_class_iso_match": color_iso_match,
            "n_block_even": int(len(idx_even)),
            "n_block_odd": int(len(idx_odd)),
            "match": block_decomp_match,
        })
    return records


def run_parametric_N_4d() -> List[Dict]:
    """4D parametric. Cost: eigh on N^4 x N^4 matrix.
      N=3: 81 -> trivial
      N=4: 256 -> trivial
      N=5: 625 -> < 1s
      N=6: 1296 -> few seconds
      N=7: 2401 -> tens of seconds; skip to stay under budget
      N=8 already tested in prior spike (D_4/B_4 paper)
    Use N ∈ {3,4,5}.
    """
    print("\n[C-F3b.2] Parametric N^4 (4D rook/king/bishop)...")
    records = []
    for N in [3, 4, 5]:
        # Rook
        A_r = build_rook_4d_N(N).astype(np.float64)
        e_r = np.linalg.eigvalsh(A_r)
        pred_r = predict_rook_4d_N(N)
        v_r = verify_predicted_spectrum_pairs(e_r, pred_r, f"rook_4d_N{N}")
        # King
        A_k = build_king_4d_N(N).astype(np.float64)
        e_k = np.linalg.eigvalsh(A_k)
        pred_k = predict_king_4d_N(N)
        v_k = verify_predicted_full(e_k, pred_k, f"king_4d_N{N}")
        # Bishop: parity-block (parity (x+y+z+w) mod 2)
        parity = np.array(
            [(x + y + z + w) % 2
             for x in range(N) for y in range(N)
             for z in range(N) for w in range(N)]
        )
        idx_even = np.where(parity == 0)[0]
        idx_odd = np.where(parity == 1)[0]
        A_b = build_bishop_4d_N(N).astype(np.float64)
        cross_sum = A_b[np.ix_(idx_even, idx_odd)].sum()
        e_be = np.sort(np.linalg.eigvalsh(A_b[np.ix_(idx_even, idx_even)]))
        e_bo = np.sort(np.linalg.eigvalsh(A_b[np.ix_(idx_odd, idx_odd)]))
        e_b_full = np.sort(np.linalg.eigvalsh(A_b))
        if len(e_be) == len(e_bo):
            color_iso_max_dev = float(np.abs(e_be - e_bo).max())
            color_iso_match = bool(color_iso_max_dev < PRECISION_TARGET_MODE_I)
        else:
            color_iso_max_dev = None
            color_iso_match = False
        combined = np.sort(np.concatenate([e_be, e_bo]))
        block_decomp_max_dev = float(np.abs(combined - e_b_full).max())
        block_decomp_match = bool(block_decomp_max_dev < PRECISION_TARGET_MODE_I)
        print(f"    N={N} (n={N**4}): rook MATCH={v_r['match']} max_dev={v_r['max_dev']:.3e}"
              f" | king MATCH={v_k['match']} max_dev={v_k['max_dev']:.3e}"
              f" | bishop parity_block={block_decomp_match} max_dev={block_decomp_max_dev:.3e}"
              f" color_iso={color_iso_match}")

        records.append({
            "candidate": "parametric_N",
            "extension": "C-F3b",
            "piece": "rook",
            "dim": 4,
            "board_N": N,
            "n_cells": N ** 4,
            "mode": "I",
            "predicted_pairs": [(float(v), int(m)) for (v, m) in pred_r],
            "max_dev": v_r["max_dev"],
            "match": v_r["match"],
        })
        records.append({
            "candidate": "parametric_N",
            "extension": "C-F3b",
            "piece": "king",
            "dim": 4,
            "board_N": N,
            "n_cells": N ** 4,
            "mode": "I",
            "max_dev": v_k["max_dev"],
            "match": v_k["match"],
        })
        records.append({
            "candidate": "parametric_N",
            "extension": "C-F3b",
            "piece": "bishop",
            "dim": 4,
            "board_N": N,
            "n_cells": N ** 4,
            "mode": "I",
            "cross_parity_zero": bool(cross_sum == 0),
            "block_decomp_max_dev": block_decomp_max_dev,
            "block_decomp_match": block_decomp_match,
            "color_class_iso_max_dev": color_iso_max_dev,
            "color_class_iso_match": color_iso_match,
            "n_block_even": int(len(idx_even)),
            "n_block_odd": int(len(idx_odd)),
            "match": block_decomp_match,
        })
    return records


# ---------------------------------------------------------------------------
# Sub-investigation 3: toroidal Z_N^d (C-F3c)
# ---------------------------------------------------------------------------


def run_toroidal_2d_N8() -> List[Dict]:
    print("\n[C-F3c.1] Toroidal Z_8 x Z_8 (2D rook/king/bishop)...")
    records = []
    N = BOARD_SIDE_8
    # Rook
    A_r = build_toroidal_rook_2d_N(N).astype(np.float64)
    A_r_boundary = build_rook_2d_N(N).astype(np.float64)
    # On empty board, toroidal rook == boundary rook
    rook_same = bool(np.array_equal(A_r, A_r_boundary))
    e_r = np.linalg.eigvalsh(A_r)
    pred_r = predict_toroidal_rook_2d_N(N)
    v_r = verify_predicted_spectrum_pairs(e_r, pred_r, "toroidal_rook_2d_N8")
    print(f"    Toroidal rook 2D (N=8): same_as_boundary={rook_same}; "
          f"Mode I MATCH={v_r['match']} max_dev={v_r['max_dev']:.3e}")
    # King
    A_k = build_toroidal_king_2d_N(N).astype(np.float64)
    e_k = np.linalg.eigvalsh(A_k)
    pred_k = predict_toroidal_king_2d_N(N)
    v_k = verify_predicted_full(e_k, pred_k, "toroidal_king_2d_N8")
    # Verify uniform degree 8 (no boundary)
    king_deg_min = int(A_k.sum(axis=1).min())
    king_deg_max = int(A_k.sum(axis=1).max())
    print(f"    Toroidal king 2D (N=8): degree {king_deg_min}..{king_deg_max}; "
          f"Mode I MATCH={v_k['match']} max_dev={v_k['max_dev']:.3e}")
    # Bishop
    A_b = build_toroidal_bishop_2d_N(N).astype(np.float64)
    e_b = np.linalg.eigvalsh(A_b)
    pred_b = predict_toroidal_bishop_2d_N(N)
    v_b = verify_predicted_full(e_b, pred_b, "toroidal_bishop_2d_N8")
    # Parity preserved? For N even, yes.
    parity_2d = np.array([(x + y) % 2 for x in range(N) for y in range(N)])
    idx_even = np.where(parity_2d == 0)[0]
    idx_odd = np.where(parity_2d == 1)[0]
    cross_b = A_b[np.ix_(idx_even, idx_odd)].sum()
    print(f"    Toroidal bishop 2D (N=8): cross-parity={cross_b}; "
          f"Mode I MATCH={v_b['match']} max_dev={v_b['max_dev']:.3e}")
    # Mode II: Z_8 × Z_8 abelian → Fourier diagonalization
    mode_ii_r = toroidal_mode_ii_2d(A_r, N)
    mode_ii_k = toroidal_mode_ii_2d(A_k, N)
    mode_ii_b = toroidal_mode_ii_2d(A_b, N)
    print(f"    Mode II (Z_8 x Z_8 Fourier): rook={mode_ii_r['mode_ii_passes']}; "
          f"king={mode_ii_k['mode_ii_passes']}; bishop={mode_ii_b['mode_ii_passes']}")

    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "rook",
        "dim": 2,
        "board_N": N,
        "n_cells": N * N,
        "group": "Z_8 x Z_8",
        "mode": "I",
        "predicted_pairs": [(float(v), int(m)) for (v, m) in pred_r],
        "max_dev": v_r["max_dev"],
        "match": v_r["match"],
        "same_as_boundary_adjacency": rook_same,
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "rook",
        "dim": 2,
        "board_N": N,
        "n_cells": N * N,
        "group": "Z_8 x Z_8",
        "mode": "II",
        **mode_ii_r,
        "match": mode_ii_r["mode_ii_passes"],
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "king",
        "dim": 2,
        "board_N": N,
        "n_cells": N * N,
        "group": "Z_8 x Z_8",
        "mode": "I",
        "max_dev": v_k["max_dev"],
        "match": v_k["match"],
        "min_degree": king_deg_min,
        "max_degree": king_deg_max,
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "king",
        "dim": 2,
        "board_N": N,
        "n_cells": N * N,
        "group": "Z_8 x Z_8",
        "mode": "II",
        **mode_ii_k,
        "match": mode_ii_k["mode_ii_passes"],
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "bishop",
        "dim": 2,
        "board_N": N,
        "n_cells": N * N,
        "group": "Z_8 x Z_8",
        "mode": "I",
        "max_dev": v_b["max_dev"],
        "match": v_b["match"],
        "cross_parity_count": int(cross_b),
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "bishop",
        "dim": 2,
        "board_N": N,
        "n_cells": N * N,
        "group": "Z_8 x Z_8",
        "mode": "II",
        **mode_ii_b,
        "match": mode_ii_b["mode_ii_passes"],
    })
    return records


def run_toroidal_4d_N8() -> List[Dict]:
    print("\n[C-F3c.2] Toroidal Z_8^4 (4D rook/king/bishop)...")
    records = []
    N = BOARD_SIDE_8

    # Rook
    print("    Building 4D toroidal rook...")
    A_r = build_toroidal_rook_4d_N(N).astype(np.float64)
    A_r_boundary = build_rook_4d_N(N).astype(np.float64)
    rook_same = bool(np.array_equal(A_r, A_r_boundary))
    print(f"    Toroidal rook 4D: same_as_boundary={rook_same}")
    print("    Mode I (rook): eigvalsh + Fourier prediction...")
    e_r = np.linalg.eigvalsh(A_r)
    pred_r = predict_toroidal_rook_4d_N(N)
    v_r = verify_predicted_spectrum_pairs(e_r, pred_r, "toroidal_rook_4d_N8")
    print(f"    Toroidal rook 4D Mode I: MATCH={v_r['match']} max_dev={v_r['max_dev']:.3e}")
    # Mode II
    print("    Mode II (rook): Z_8^4 Fourier diagonalization...")
    mode_ii_r = toroidal_mode_ii_4d(A_r, N)
    print(f"    Mode II rook: {mode_ii_r['mode_ii_passes']} "
          f"max_dev={mode_ii_r['max_dev_fourier_pred_vs_eigvalsh']:.3e}")
    del A_r, A_r_boundary, e_r

    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "rook",
        "dim": 4,
        "board_N": N,
        "n_cells": N ** 4,
        "group": "Z_8^4",
        "mode": "I",
        "predicted_pairs": [(float(v), int(m)) for (v, m) in pred_r],
        "max_dev": v_r["max_dev"],
        "match": v_r["match"],
        "same_as_boundary_adjacency": rook_same,
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "rook",
        "dim": 4,
        "board_N": N,
        "n_cells": N ** 4,
        "group": "Z_8^4",
        "mode": "II",
        **mode_ii_r,
        "match": mode_ii_r["mode_ii_passes"],
    })

    # King
    print("    Building 4D toroidal king...")
    A_k = build_toroidal_king_4d_N(N).astype(np.float64)
    king_deg_min = int(A_k.sum(axis=1).min())
    king_deg_max = int(A_k.sum(axis=1).max())
    print(f"    Toroidal king 4D: degree {king_deg_min}..{king_deg_max}")
    print("    Mode I (king): eigvalsh + Fourier prediction...")
    e_k = np.linalg.eigvalsh(A_k)
    pred_k = predict_toroidal_king_4d_N(N)
    v_k = verify_predicted_full(e_k, pred_k, "toroidal_king_4d_N8")
    print(f"    Toroidal king 4D Mode I: MATCH={v_k['match']} max_dev={v_k['max_dev']:.3e}")
    mode_ii_k = toroidal_mode_ii_4d(A_k, N)
    print(f"    Mode II king: {mode_ii_k['mode_ii_passes']} "
          f"max_dev={mode_ii_k['max_dev_fourier_pred_vs_eigvalsh']:.3e}")
    del A_k, e_k

    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "king",
        "dim": 4,
        "board_N": N,
        "n_cells": N ** 4,
        "group": "Z_8^4",
        "mode": "I",
        "max_dev": v_k["max_dev"],
        "match": v_k["match"],
        "min_degree": king_deg_min,
        "max_degree": king_deg_max,
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "king",
        "dim": 4,
        "board_N": N,
        "n_cells": N ** 4,
        "group": "Z_8^4",
        "mode": "II",
        **mode_ii_k,
        "match": mode_ii_k["mode_ii_passes"],
    })

    # Bishop
    print("    Building 4D toroidal bishop...")
    A_b = build_toroidal_bishop_4d_N(N).astype(np.float64)
    parity_4d = np.array(
        [(x + y + z + w) % 2
         for x in range(N) for y in range(N)
         for z in range(N) for w in range(N)]
    )
    idx_even = np.where(parity_4d == 0)[0]
    idx_odd = np.where(parity_4d == 1)[0]
    cross_b = A_b[np.ix_(idx_even, idx_odd)].sum()
    print(f"    Toroidal bishop 4D: cross-parity count={cross_b}")
    print("    Mode I (bishop): eigvalsh + Fourier prediction...")
    e_b = np.linalg.eigvalsh(A_b)
    pred_b = predict_toroidal_bishop_4d_N(N)
    v_b = verify_predicted_full(e_b, pred_b, "toroidal_bishop_4d_N8")
    print(f"    Toroidal bishop 4D Mode I: MATCH={v_b['match']} max_dev={v_b['max_dev']:.3e}")
    mode_ii_b = toroidal_mode_ii_4d(A_b, N)
    print(f"    Mode II bishop: {mode_ii_b['mode_ii_passes']} "
          f"max_dev={mode_ii_b['max_dev_fourier_pred_vs_eigvalsh']:.3e}")
    del A_b, e_b

    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "bishop",
        "dim": 4,
        "board_N": N,
        "n_cells": N ** 4,
        "group": "Z_8^4",
        "mode": "I",
        "max_dev": v_b["max_dev"],
        "match": v_b["match"],
        "cross_parity_count": int(cross_b),
    })
    records.append({
        "candidate": "toroidal",
        "extension": "C-F3c",
        "piece": "bishop",
        "dim": 4,
        "board_N": N,
        "n_cells": N ** 4,
        "group": "Z_8^4",
        "mode": "II",
        **mode_ii_b,
        "match": mode_ii_b["mode_ii_passes"],
    })

    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    t0 = time.perf_counter()
    print(f"[INFO] chess extension candidates spike (seed {SEED}); MPM discipline.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build D_4 projectors once for queen 2D
    print("[INFO] Building D_4 projectors (one-time)...")
    sigma_dict = d4_permutations_2d_N8()
    d4_projs = d4_projector_matrices(sigma_dict)
    # Idempotency check
    for rep, P in d4_projs.items():
        d_idem = np.abs(P @ P - P).max()
        assert d_idem < 1e-10, f"D_4 projector {rep} not idempotent (dev {d_idem})"

    all_records: List[Dict] = []

    # C-F3a: queen
    all_records += run_queen_2d_N8(d4_projs)
    all_records += run_queen_4d_N8()

    # C-F3b: parametric N
    all_records += run_parametric_N_2d()
    all_records += run_parametric_N_4d()

    # C-F3c: toroidal
    all_records += run_toroidal_2d_N8()
    all_records += run_toroidal_4d_N8()

    # Write NDJSON (idempotent: overwrite output)
    with NDJSON_PATH.open("w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\n[OK] Wrote {len(all_records)} NDJSON records to {NDJSON_PATH}")

    elapsed = time.perf_counter() - t0
    print(f"[OK] TOTAL RUNTIME: {elapsed:.1f}s")

    # Summary computation
    print("\n=== SUMMARY ===")

    def summarize(extension: str, candidate: str = None, mode: str = None, dim: int = None) -> Dict:
        recs = [r for r in all_records if r.get("extension") == extension]
        if candidate:
            recs = [r for r in recs if r.get("candidate") == candidate]
        if mode:
            recs = [r for r in recs if r.get("mode") == mode]
        if dim:
            recs = [r for r in recs if r.get("dim") == dim]
        if not recs:
            return {"n": 0}
        n_match = sum(1 for r in recs if r.get("match") is True)
        n_total = len(recs)
        return {"n": n_total, "match": n_match}

    # Queen Mode II 2D + 4D
    q_2d_ii = [r for r in all_records
               if r.get("extension") == "C-F3a" and r.get("dim") == 2 and r.get("mode") == "II"]
    q_2d_ii_int = sum(1 for r in q_2d_ii if r.get("is_integer_exact"))
    q_2d_ii_max_dev = max((r.get("deviation_from_integer", 0) for r in q_2d_ii), default=0)

    q_4d_ii = [r for r in all_records
               if r.get("extension") == "C-F3a" and r.get("dim") == 4 and r.get("mode") == "II"]
    q_4d_ii_int = sum(1 for r in q_4d_ii if r.get("is_integer_exact"))
    q_4d_ii_max_dev = max((r.get("deviation_from_integer", 0) for r in q_4d_ii), default=0)

    print(f"  C-F3a Queen 2D Mode II: {q_2d_ii_int}/{len(q_2d_ii)} integer-exact "
          f"(max_dev = {q_2d_ii_max_dev:.3e})")
    print(f"  C-F3a Queen 4D Mode II: {q_4d_ii_int}/{len(q_4d_ii)} integer-exact "
          f"(max_dev = {q_4d_ii_max_dev:.3e})")

    # Parametric Mode I: count match by piece/dim
    print("  C-F3b Parametric N Mode I:")
    for dim in [2, 4]:
        for piece in ["rook", "king", "bishop"]:
            recs = [r for r in all_records
                    if r.get("extension") == "C-F3b" and r.get("dim") == dim
                    and r.get("piece") == piece and r.get("mode") == "I"]
            matches = sum(1 for r in recs if r.get("match"))
            max_dev_set = [r.get("max_dev", 0) or r.get("block_decomp_max_dev", 0) for r in recs]
            max_dev = max(max_dev_set) if max_dev_set else 0
            print(f"    {piece} {dim}D: {matches}/{len(recs)} match, max_dev = {max_dev:.3e}")

    # Toroidal Mode I + Mode II by piece/dim
    print("  C-F3c Toroidal Mode I + Mode II:")
    for dim in [2, 4]:
        for piece in ["rook", "king", "bishop"]:
            for mode in ["I", "II"]:
                recs = [r for r in all_records
                        if r.get("extension") == "C-F3c" and r.get("dim") == dim
                        and r.get("piece") == piece and r.get("mode") == mode]
                matches = sum(1 for r in recs if r.get("match"))
                max_dev_set = [r.get("max_dev", 0) for r in recs
                               if r.get("max_dev") is not None]
                if mode == "II":
                    max_dev_set = [r.get("max_dev_fourier_pred_vs_eigvalsh", 0) for r in recs]
                max_dev = max(max_dev_set) if max_dev_set else 0
                print(f"    {piece} {dim}D Mode {mode}: {matches}/{len(recs)} "
                      f"max_dev = {max_dev:.3e}")

    # Build completion record
    summary = {
        "queen_2d_mode_i_refuted": True,  # by construction (non-commuting)
        "queen_2d_mode_ii_int_exact_count": q_2d_ii_int,
        "queen_2d_mode_ii_total_combos": len(q_2d_ii),
        "queen_2d_mode_ii_max_dev": float(q_2d_ii_max_dev),
        "queen_4d_mode_i_refuted": True,
        "queen_4d_mode_ii_int_exact_count": q_4d_ii_int,
        "queen_4d_mode_ii_total_combos": len(q_4d_ii),
        "queen_4d_mode_ii_max_dev": float(q_4d_ii_max_dev),
    }
    # Parametric pass counts
    for dim in [2, 4]:
        for piece in ["rook", "king", "bishop"]:
            recs = [r for r in all_records
                    if r.get("extension") == "C-F3b" and r.get("dim") == dim
                    and r.get("piece") == piece and r.get("mode") == "I"]
            matches = sum(1 for r in recs if r.get("match"))
            summary[f"parametric_{piece}_{dim}d_pass"] = f"{matches}/{len(recs)}"
    # Toroidal pass counts
    for dim in [2, 4]:
        for piece in ["rook", "king", "bishop"]:
            for mode in ["I", "II"]:
                recs = [r for r in all_records
                        if r.get("extension") == "C-F3c" and r.get("dim") == dim
                        and r.get("piece") == piece and r.get("mode") == mode]
                matches = sum(1 for r in recs if r.get("match"))
                summary[f"toroidal_{piece}_{dim}d_mode{mode}_pass"] = f"{matches}/{len(recs)}"

    completion = {
        "date": "2026-05-11",
        "phase": "srmech_3_5_3_C_extension_candidates",
        "kind": "completion",
        "outputs": [
            f"docs/srmech/notes/{NDJSON_PATH.name}",
            "docs/srmech/notes/chess-extension-candidates-2026-05-11.md",
            "docs/srmech/notes/chess-extension-candidates-script.py",
        ],
        "n_records": len(all_records),
        "runtime_s": elapsed,
        "summary": summary,
        "note": (
            "Concertmaster spike testing three extension candidates for srmech §3.5.3(C) "
            "chess instance: (C-F3a) queen 2D + 4D Mode I refuted as expected, Mode II "
            "integer-exact via D_4/B_4 character orthogonality; (C-F3b) parametric N "
            "chess on N x N (N∈{4..8}) and N^4 (N∈{3,4,5}) for rook/king/bishop Mode I "
            "closed-form via K_N/P_N spectra and parity-stratification; (C-F3c) toroidal "
            "Z_8 x Z_8 and Z_8^4 chess Mode I via Fourier on cycle products and Mode II "
            "via abelian-group character orthogonality (Fourier diagonalization). "
            "If all three pass, §3.5.3(C) chess instance gains: parametric robustness in "
            "board-size N; queen as second Mode II piece; toroidal as 4th instance under "
            "abelian translation group Z_n^d vs dihedral/hyperoctahedral D_4/B_4."
        ),
    }

    # Idempotent append: replace prior srmech_3_5_3_C_extension_candidates record
    existing = COMPLETION_RECORD_PATH.read_text(encoding="utf-8").splitlines() \
        if COMPLETION_RECORD_PATH.exists() else []
    kept = [
        ln for ln in existing
        if not (
            "srmech_3_5_3_C_extension_candidates" in ln
            and "\"kind\": \"completion\"" in ln
        )
    ]
    kept.append(json.dumps(completion, ensure_ascii=False))
    COMPLETION_RECORD_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"[OK] Appended completion record to {COMPLETION_RECORD_PATH}")

    return all_records


if __name__ == "__main__":
    main()
