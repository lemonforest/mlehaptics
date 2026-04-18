"""4D extension tables for the chess-spectral encoder.

Mirrors the shape of [tables.py] but operates on the Z_8^4 hypercubic
lattice (4096 squares) under the B_4 hyperoctahedral symmetry group.
Paired with [../chess_spectral_4d/cli.py], which exposes the phase-N
validation gates used to check each implementation stage before moving
on.

Piece movement definitions follow Oana & Chiru, "On a Four-Dimensional
Chess Model," AppliedMath 6(3):48, 2026 — see section 3.

Phase 1 deliverables (this file): piece target generators,
build_adjacency_4d, verify_phase1.

Phase 2-4 deliverables (to follow): P8 eigenbasis, B_4 group action
and irrep projection, fiber bundle construction. Placeholders left
intentionally for the phase gates.
"""
from __future__ import annotations

from itertools import product
from typing import Iterator, Tuple, Callable, List

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.csgraph import connected_components

BOARD_SIDE = 8
N_DIMS = 4
N_SQUARES = BOARD_SIDE ** N_DIMS          # 4096

Coord = Tuple[int, int, int, int]


# ─── Geometry ──────────────────────────────────────────────────────────

def sq4(x: int, y: int, z: int, w: int) -> int:
    """Row-major linear index of square (x,y,z,w) on Z_8^4. x is the
    slowest-varying axis, w the fastest — matches `arr[x,y,z,w]` under
    numpy C-order ravel."""
    return ((x * BOARD_SIDE + y) * BOARD_SIDE + z) * BOARD_SIDE + w


def rc4(s: int) -> Coord:
    """Inverse of sq4."""
    w = s & 7
    s >>= 3
    z = s & 7
    s >>= 3
    y = s & 7
    x = s >> 3
    return x, y, z, w


def _in_bounds(v: int) -> bool:
    return 0 <= v < BOARD_SIDE


# ─── Piece target generators ───────────────────────────────────────────
#
# Each function yields Coord tuples reachable from (x,y,z,w) for that
# piece on an otherwise-empty Z_8^4 board. Used to build undirected
# adjacency (directed for pawns).
#
# Mobility (Oana & Chiru section 3):
#   rook:   28 at every square (K_8 along each of 4 axes)
#   king:   80 at interior (3^4 - 1), fewer at boundaries
#   knight: 48 at deep interior (C(4,2) * 2 * 2 * 2), fewer at boundaries
#   bishop: 2 connected components partitioned by sum(coords) mod 2
#   queen:  union of rook + bishop
#   pawn:   directed single-step on +w axis

def rook4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """4D rook: all other squares differing in exactly one coordinate.
    Graph = K_8 □ K_8 □ K_8 □ K_8 (Hamming H(4,8))."""
    coords = [x, y, z, w]
    for axis in range(N_DIMS):
        fixed = coords[axis]
        for v in range(BOARD_SIDE):
            if v == fixed:
                continue
            out = coords.copy()
            out[axis] = v
            yield (out[0], out[1], out[2], out[3])


def bishop4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """4D bishop: slide along diagonals of any 2-face. Choose 2 axes
    from 4, step by ±k in each with independent signs, k in 1..7.
    Preserves parity of coordinate sum ⇒ 2 connected components."""
    coords = [x, y, z, w]
    for i in range(N_DIMS):
        for j in range(i + 1, N_DIMS):
            for si in (-1, +1):
                for sj in (-1, +1):
                    for k in range(1, BOARD_SIDE):
                        ni, nj = coords[i] + si * k, coords[j] + sj * k
                        if not (_in_bounds(ni) and _in_bounds(nj)):
                            break
                        out = coords.copy()
                        out[i], out[j] = ni, nj
                        yield (out[0], out[1], out[2], out[3])


def knight4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """4D knight: (2,1)-leaper. One axis shifts by ±2, a different axis
    by ±1, the other two unchanged. Interior degree = 4·3·2·2 = 48."""
    coords = [x, y, z, w]
    for a2 in range(N_DIMS):
        for a1 in range(N_DIMS):
            if a1 == a2:
                continue
            for s2 in (-2, +2):
                for s1 in (-1, +1):
                    out = coords.copy()
                    out[a2] = coords[a2] + s2
                    out[a1] = coords[a1] + s1
                    if _in_bounds(out[a2]) and _in_bounds(out[a1]):
                        yield (out[0], out[1], out[2], out[3])


def king4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """4D king: Chebyshev-1. Each coord shifts by -1/0/+1, not all zero.
    Graph = P_8 ⊠ P_8 ⊠ P_8 ⊠ P_8 (strong product). Interior deg = 80."""
    coords = (x, y, z, w)
    for d in product((-1, 0, 1), repeat=N_DIMS):
        if d == (0, 0, 0, 0):
            continue
        out = tuple(coords[i] + d[i] for i in range(N_DIMS))
        if all(_in_bounds(v) for v in out):
            yield out


def queen4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """Queen = rook U bishop (disjoint supports; rook moves along single
    axis, bishop along 2-face diagonals)."""
    yield from rook4_targets(x, y, z, w)
    yield from bishop4_targets(x, y, z, w)


def white_pawn4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """4D white pawn: single-step push on +w axis (w is the 'forward'
    axis by convention). Directed edge only. Captures deferred to a
    follow-up until Oana & Chiru's exact diagonal-capture rule is
    pinned down — the encoder's antisymmetric pawn fiber depends only
    on forward push for Z_2 breaking."""
    if w + 1 < BOARD_SIDE:
        yield (x, y, z, w + 1)


# ─── Adjacency construction ────────────────────────────────────────────

def build_adjacency_4d(
    target_fn: Callable[[int, int, int, int], Iterator[Coord]],
    directed: bool = False,
) -> csr_matrix:
    """Build a 4096×4096 sparse adjacency matrix from a target generator.

    Undirected (default): for symmetric pieces the generator already
    emits edges both ways under iteration over all start squares, but
    we explicitly symmetrize to be safe.

    Directed: leave as-is; pawn is the only current caller."""
    A = lil_matrix((N_SQUARES, N_SQUARES), dtype=np.int8)
    for s in range(N_SQUARES):
        x, y, z, w = rc4(s)
        for t in target_fn(x, y, z, w):
            A[s, sq4(*t)] = 1
    A = A.tocsr()
    if not directed:
        # Symmetrize in case a generator emits edges asymmetrically
        # near boundaries. Undirected pieces should already be symmetric;
        # this is a belt-and-braces check that does nothing in steady
        # state.
        A = A.maximum(A.T)
    return A


def degree_vector(A: csr_matrix) -> np.ndarray:
    """Row-sum degree as a flat (N_SQUARES,) int array."""
    return np.asarray(A.sum(axis=1)).ravel().astype(np.int64)


# ─── Phase 1 gate ──────────────────────────────────────────────────────

def _deep_interior_squares() -> List[Coord]:
    """Squares with every coord in 2..5 — far enough from the boundary
    that knight and king reach their maximum interior degree (knight
    needs ≥2 margin in the ±2 axis; king needs ≥1). 4^4 = 256 squares."""
    return [(x, y, z, w)
            for x in range(2, 6) for y in range(2, 6)
            for z in range(2, 6) for w in range(2, 6)]


def verify_phase1(verbose: bool = False, seed: int = 42,
                  n_sample: int = 100) -> List[str]:
    """Phase 1 mobility + connectivity gate. Raises AssertionError on
    any mismatch. Returns a list of human-readable report lines
    describing what was checked."""
    report: List[str] = []
    rng = np.random.default_rng(seed)

    interior = _deep_interior_squares()
    if n_sample > len(interior):
        n_sample = len(interior)
    sample_idx = rng.choice(len(interior), size=n_sample, replace=False)
    sample = [interior[int(i)] for i in sample_idx]

    if verbose:
        report.append(
            f"(verbose) sampled {n_sample} of {len(interior)} deep-interior "
            f"squares with seed={seed}"
        )

    # Rook: degree 28 everywhere (K_8 on each of 4 axes, boundary-invariant).
    A_rook = build_adjacency_4d(rook4_targets)
    deg_rook = degree_vector(A_rook)
    assert np.all(deg_rook == 28), (
        f"rook: expected deg=28 at all {N_SQUARES} squares, "
        f"got min={deg_rook.min()}, max={deg_rook.max()}"
    )
    report.append(
        f"rook:   deg=28 at all {N_SQUARES} squares "
        f"(Oana-Chiru: 28 everywhere) OK"
    )

    # King: deep-interior deg = 3^4 - 1 = 80.
    A_king = build_adjacency_4d(king4_targets)
    deg_king = degree_vector(A_king)
    for (x, y, z, w) in sample:
        s = sq4(x, y, z, w)
        assert deg_king[s] == 80, (
            f"king at {(x, y, z, w)}: expected deg=80, got {deg_king[s]}"
        )
    report.append(
        f"king:   deg=80 at {n_sample} deep-interior squares "
        f"(Oana-Chiru: 80 interior) OK"
    )

    # Knight: deep-interior deg = C(4,2) * 2 * 2 * 2 = 48.
    A_kn = build_adjacency_4d(knight4_targets)
    deg_kn = degree_vector(A_kn)
    for (x, y, z, w) in sample:
        s = sq4(x, y, z, w)
        assert deg_kn[s] == 48, (
            f"knight at {(x, y, z, w)}: expected deg=48, got {deg_kn[s]}"
        )
    report.append(
        f"knight: deg=48 at {n_sample} deep-interior squares "
        f"(Oana-Chiru: 48 interior) OK"
    )

    # Bishop: exactly 2 connected components, split by parity of coord sum.
    A_bi = build_adjacency_4d(bishop4_targets)
    n_comp, labels = connected_components(A_bi, directed=False)
    assert n_comp == 2, f"bishop: expected 2 components, got {n_comp}"
    parity = np.array([sum(rc4(s)) & 1 for s in range(N_SQUARES)])
    matches_parity = np.array_equal(labels, parity) or \
                     np.array_equal(labels, 1 - parity)
    assert matches_parity, (
        "bishop: 2 components but partition does not match coord-sum parity"
    )
    c0 = int((parity == 0).sum())
    c1 = int((parity == 1).sum())
    report.append(
        f"bishop: 2 components ({c0}/{c1} by coord-sum parity) OK"
    )

    # Queen: superset of rook.
    A_q = build_adjacency_4d(queen4_targets)
    deg_q = degree_vector(A_q)
    assert np.all(deg_q >= 28), (
        f"queen: expected deg >= 28 (rook subset), "
        f"got min={deg_q.min()}"
    )
    # Also: queen = rook U bishop ⇒ A_q should equal A_rook.maximum(A_bi).
    A_union = A_rook.maximum(A_bi)
    diff = (A_q != A_union).nnz
    assert diff == 0, (
        f"queen: adjacency does not match rook U bishop "
        f"(differing entries={diff})"
    )
    report.append("queen:  A_queen == A_rook U A_bishop (union identity) OK")

    # Pawn (directed): out-degree 1 for w < 7, 0 for w == 7.
    A_pw = build_adjacency_4d(white_pawn4_targets, directed=True)
    deg_pw = degree_vector(A_pw)
    for s in range(N_SQUARES):
        x, y, z, w = rc4(s)
        expected = 1 if w < BOARD_SIDE - 1 else 0
        assert deg_pw[s] == expected, (
            f"pawn at {(x, y, z, w)}: expected out-deg={expected}, "
            f"got {deg_pw[s]}"
        )
    report.append(
        "pawn:   directed +w push, out-deg=1 for w<7, 0 for w=7 OK"
    )

    return report
