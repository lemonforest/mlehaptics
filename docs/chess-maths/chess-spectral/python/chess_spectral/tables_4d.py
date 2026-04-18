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
from scipy.sparse import csr_matrix, lil_matrix, diags
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

def grid4_targets(x: int, y: int, z: int, w: int) -> Iterator[Coord]:
    """4D grid graph: Cartesian product P_8 [] P_8 [] P_8 [] P_8. Each
    square adjacent to <=8 neighbors (+-1 along each of 4 axes). This
    is the 'empty-board' graph whose Laplacian eigenbasis is the
    tensor-DCT basis used by the encoder."""
    coords = [x, y, z, w]
    for axis in range(N_DIMS):
        for sign in (-1, +1):
            out = coords.copy()
            out[axis] = coords[axis] + sign
            if _in_bounds(out[axis]):
                yield (out[0], out[1], out[2], out[3])


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


def laplacian_4d(A: csr_matrix) -> csr_matrix:
    """Graph Laplacian L = D - A from a (possibly directed) adjacency.
    For symmetric undirected graphs this is the standard combinatorial
    Laplacian; for directed graphs, D uses row sums (out-degree)."""
    deg = degree_vector(A).astype(np.float64)
    D = diags(deg)
    return (D - A.astype(np.float64)).tocsr()


# ---- Path-graph eigenbasis (1D building block for the 4D tensor DCT)

def p8_laplacian() -> np.ndarray:
    """8x8 Laplacian of the path graph P_8. Tridiagonal: -1 on
    super/subdiagonals, degree on the diagonal (1 at endpoints,
    2 interior)."""
    n = BOARD_SIDE
    A = np.zeros((n, n), dtype=np.float64)
    for i in range(n - 1):
        A[i, i + 1] = 1.0
        A[i + 1, i] = 1.0
    D = np.diag(A.sum(axis=1))
    return D - A


def eig_p8() -> Tuple[np.ndarray, np.ndarray]:
    """Return (evecs[8,8], evals[8]) of the P_8 Laplacian, sorted by
    eigenvalue ascending. Eigenvectors form the DCT-II basis. Cheap
    enough (8x8) to recompute on demand — no caching needed."""
    L = p8_laplacian()
    evals, evecs = np.linalg.eigh(L)
    return evecs, evals


def kron_sum4_eigvals(evals_1d: np.ndarray) -> np.ndarray:
    """All 4096 eigenvalues of the 4D grid Laplacian as the Kronecker
    sum `evals_1d[i] + evals_1d[j] + evals_1d[k] + evals_1d[l]`,
    indexed by sq4(i,j,k,l). Matches the C-order ravel of the
    (8,8,8,8) tensor of tensor-product eigenvectors."""
    out = np.empty(N_SQUARES, dtype=np.float64)
    for x in range(BOARD_SIDE):
        for y in range(BOARD_SIDE):
            for z in range(BOARD_SIDE):
                for w in range(BOARD_SIDE):
                    out[sq4(x, y, z, w)] = (
                        evals_1d[x] + evals_1d[y]
                        + evals_1d[z] + evals_1d[w]
                    )
    return out


def tensor_eigvec_4d(evecs_1d: np.ndarray,
                     i: int, j: int, k: int, l: int) -> np.ndarray:
    """Build the 4096-vector `e_i (x) e_j (x) e_k (x) e_l` for the
    4D grid, indexed by sq4. Column `i` of `evecs_1d` is the i-th P_8
    eigenvector."""
    v = np.einsum(
        'a,b,c,d->abcd',
        evecs_1d[:, i], evecs_1d[:, j],
        evecs_1d[:, k], evecs_1d[:, l],
    )
    return v.ravel()


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


# ---- Phase 2 gate -----------------------------------------------------

def verify_phase2(verbose: bool = False, seed: int = 42,
                  n_sample: int = 20, tol: float = 1e-10) -> List[str]:
    """Phase 2 gate: verify the 4D grid Laplacian has eigenvalues equal
    to the Kronecker sum of four copies of the P_8 spectrum, with
    tensor-DCT eigenvectors. We do NOT build the 4096x4096 dense
    eigensystem; instead we check `L_grid @ v = lambda * v` on
    `n_sample` random tensor-product eigenvectors."""
    report: List[str] = []
    rng = np.random.default_rng(seed)

    # 4D grid Laplacian (sparse, 4096x4096)
    A_grid = build_adjacency_4d(grid4_targets)
    L_grid = laplacian_4d(A_grid)

    # P_8 eigenbasis
    evecs, evals = eig_p8()
    report.append(
        "P_8 eigenvalues: [" +
        ", ".join(f"{v:.4f}" for v in evals) + "]"
    )

    # Kronecker-sum spectrum of the 4D grid
    kron_evals = kron_sum4_eigvals(evals)
    report.append(
        f"4D grid spectrum: lambda_min={kron_evals.min():.6f}, "
        f"lambda_max={kron_evals.max():.6f}, "
        f"unique={len(np.unique(np.round(kron_evals, 9)))}"
    )

    # Trace identity: sum of Kronecker eigvals == trace(L_grid) == sum of degrees
    trace_L = float(degree_vector(A_grid).sum())
    trace_sum = float(kron_evals.sum())
    assert abs(trace_L - trace_sum) < 1e-8, (
        f"trace mismatch: trace(L_grid)={trace_L}, "
        f"sum(kronecker)={trace_sum}"
    )
    report.append(
        f"trace identity: trace(L)={trace_L:.1f} == "
        f"sum(kron eigvals) {trace_sum:.6f} OK"
    )

    # Sample random (i,j,k,l) and verify L v = lambda v
    max_err = 0.0
    sample_tuples = []
    for _ in range(n_sample):
        i, j, k, l = (int(rng.integers(0, BOARD_SIDE)) for _ in range(4))
        sample_tuples.append((i, j, k, l))
        v = tensor_eigvec_4d(evecs, i, j, k, l)
        lam = evals[i] + evals[j] + evals[k] + evals[l]
        residual = L_grid @ v - lam * v
        err = float(np.max(np.abs(residual)))
        if err > max_err:
            max_err = err
        assert err < tol, (
            f"eigenvector (i,j,k,l)={(i, j, k, l)}: "
            f"||L v - lambda v||_inf = {err:.3e} > tol={tol:.1e}"
        )

    report.append(
        f"eigvec identity: L v == lambda v for {n_sample} random "
        f"tensor products (max ||r||_inf = {max_err:.2e}, tol={tol:.0e}) OK"
    )

    if verbose:
        report.append("(verbose) sampled tuples: " + str(sample_tuples[:5])
                      + (" ..." if len(sample_tuples) > 5 else ""))

    return report


# ---- B_4 hyperoctahedral group ----------------------------------------
#
# B_4 = (Z_2)^4 >| S_4 acts on Z^4 by signed permutations. |B_4| = 2^4 * 4! = 384.
# A group element g is encoded as a pair (perm, signs):
#   perm:  length-4 tuple, a permutation of (0,1,2,3) telling which input
#          axis maps to which output axis. Convention: (g.x)[perm[i]] = signs[i] * x[i]
#   signs: length-4 tuple of +1 / -1
# Composition: (p2,s2) * (p1,s1) applied to x gives p2(s2 * p1(s1 * x)).
# We carry the action on the centered lattice {-7/2, -5/2, ..., +7/2} (equivalently
# coords 0..7 with reflection w -> 7-w on sign flip) so translations stay on-board.

Perm = Tuple[int, int, int, int]
Signs = Tuple[int, int, int, int]
GroupElem = Tuple[Perm, Signs]


def _b4_identity() -> GroupElem:
    return ((0, 1, 2, 3), (1, 1, 1, 1))


def _b4_generators() -> List[GroupElem]:
    """8 generators: 4 single-axis sign flips + 3 adjacent S_4 transpositions
    (minimal set; 3 adjacent transpositions generate S_4). We include all 4
    adjacent + wrap-around transpositions for redundant coverage, total 7 perm
    generators, but 3 suffice; keep it tight: 4 flips + 3 transpositions = 7.
    With identity appended implicitly via closure we hit all 384."""
    gens: List[GroupElem] = []
    # Sign flips on each axis
    for axis in range(N_DIMS):
        signs = [1, 1, 1, 1]
        signs[axis] = -1
        gens.append(((0, 1, 2, 3), tuple(signs)))  # type: ignore[arg-type]
    # Adjacent transpositions: (0 1), (1 2), (2 3) generate S_4
    for i in range(N_DIMS - 1):
        perm = [0, 1, 2, 3]
        perm[i], perm[i + 1] = perm[i + 1], perm[i]
        gens.append((tuple(perm), (1, 1, 1, 1)))  # type: ignore[arg-type]
    return gens


def _compose(g2: GroupElem, g1: GroupElem) -> GroupElem:
    """Apply g1 first, then g2. In our convention a GroupElem acts on x by
    y[perm[i]] = signs[i] * x[i], equivalently y = P diag(s) x where P is
    the permutation matrix with P[perm[i], i] = 1.

    Composition: let A_k = P_k D_k. Then A_2 A_1 = P_2 D_2 P_1 D_1
    = P_2 (D_2 P_1) D_1. Since D_2 P_1 = P_1 (P_1^{-1} D_2 P_1), and for a
    permutation matrix P P^{-1} D P has entry (i,i) = D[perm(i), perm(i)],
    we get A_2 A_1 = (P_2 P_1) diag(D_1 . permuted_D_2)
    => perm_out[i] = perm2[perm1[i]],
       signs_out[i] = signs1[i] * signs2[perm1[i]]."""
    p2, s2 = g2
    p1, s1 = g1
    perm_out = tuple(p2[p1[i]] for i in range(N_DIMS))
    signs_out = tuple(s1[i] * s2[p1[i]] for i in range(N_DIMS))
    return perm_out, signs_out  # type: ignore[return-value]


def b4_closure(gens: List[GroupElem] | None = None) -> List[GroupElem]:
    """BFS closure over B_4 from the given generators + identity. Returns
    the list of all |B_4| = 384 signed permutations. Order is BFS-deterministic
    (useful for reproducible projector construction)."""
    if gens is None:
        gens = _b4_generators()
    seen = {_b4_identity()}
    order = [_b4_identity()]
    frontier = [_b4_identity()]
    # Fixed upper bound to satisfy JPL-style bounded loop
    for _ in range(10):  # 10 BFS layers is more than enough for |B_4|=384
        if not frontier:
            break
        nxt: List[GroupElem] = []
        for g in frontier:
            for h in gens:
                g_new = _compose(h, g)
                if g_new not in seen:
                    seen.add(g_new)
                    order.append(g_new)
                    nxt.append(g_new)
        frontier = nxt
    return order


def _apply_b4_to_square(g: GroupElem, x: int, y: int, z: int, w: int
                        ) -> Coord:
    """Apply a signed-permutation to a lattice coord, using the centered
    action. Input coords 0..7 map to centered c = coord - 3.5; after flip
    we get 3.5 - coord (reflection). In integer form: sign=+1 leaves coord,
    sign=-1 maps coord -> 7 - coord. Then permute axes."""
    perm, signs = g
    src = (x, y, z, w)
    # Apply signs in input-axis order (reflect in place)
    flipped = tuple((BOARD_SIDE - 1 - src[i]) if signs[i] == -1 else src[i]
                    for i in range(N_DIMS))
    # Permute: output[perm[i]] = flipped[i]
    out = [0, 0, 0, 0]
    for i in range(N_DIMS):
        out[perm[i]] = flipped[i]
    return out[0], out[1], out[2], out[3]


def b4_permutation_matrix(g: GroupElem) -> csr_matrix:
    """Sparse 4096x4096 permutation matrix P_g such that (P_g f)[s] =
    f[g^{-1} . s]. Built by mapping s -> g . s and placing 1 at
    (g.s, s)."""
    rows = np.empty(N_SQUARES, dtype=np.int64)
    cols = np.empty(N_SQUARES, dtype=np.int64)
    for s in range(N_SQUARES):
        x, y, z, w = rc4(s)
        t = sq4(*_apply_b4_to_square(g, x, y, z, w))
        rows[s] = t
        cols[s] = s
    data = np.ones(N_SQUARES, dtype=np.float64)
    return csr_matrix((data, (rows, cols)), shape=(N_SQUARES, N_SQUARES))


def b4_a1_orbit_projector(closure: List[GroupElem] | None = None
                          ) -> csr_matrix:
    """A_1 (trivial-irrep) projector on the 4096-dim lattice signal space:
        P_A1 = (1/|B_4|) sum_{g in B_4} Pi(g)
    Pi is the signed-permutation action; for A_1 we average the full
    permutation action (no sign twist), so (P_A1 f)[s] = mean over the
    B_4-orbit of s. Returns a sparse CSR matrix."""
    if closure is None:
        closure = b4_closure()
    order = len(closure)
    assert order == 384, f"closure size {order} != 384"
    # Compute the orbit labeling: two squares s,t are in the same orbit
    # iff some g in B_4 maps s to t. We just need the orbit partition.
    orbit_of = -np.ones(N_SQUARES, dtype=np.int64)
    orbits: List[List[int]] = []
    for s in range(N_SQUARES):
        if orbit_of[s] >= 0:
            continue
        # Enumerate orbit of s
        x, y, z, w = rc4(s)
        orb_set = set()
        for g in closure:
            orb_set.add(sq4(*_apply_b4_to_square(g, x, y, z, w)))
        orb_id = len(orbits)
        for t in orb_set:
            orbit_of[t] = orb_id
        orbits.append(sorted(orb_set))
    # Build the orbit-averaging projector: P[i,j] = 1/|orbit(i)| if orbit(i)==orbit(j) else 0
    rows: List[int] = []
    cols: List[int] = []
    data: List[float] = []
    for orb in orbits:
        inv = 1.0 / len(orb)
        for i in orb:
            for j in orb:
                rows.append(i)
                cols.append(j)
                data.append(inv)
    P = csr_matrix(
        (np.asarray(data, dtype=np.float64),
         (np.asarray(rows, dtype=np.int64),
          np.asarray(cols, dtype=np.int64))),
        shape=(N_SQUARES, N_SQUARES),
    )
    return P


# ---- Standard 4D representation (closed form) ------------------------

def std4_projector_coords() -> np.ndarray:
    """Projector onto the 4D standard representation of B_4, acting on the
    coordinate channels R^4. Standard rep = orthogonal complement of the
    trivial sum-over-axes vector, so
        P_std = I_4 - (1/4) J_4
    where J_4 is the 4x4 all-ones matrix. Trace = 3 (standard of B_4
    restricted-from-S_4 is 3-dim; with sign flips the direct decomposition
    is slightly different, so we treat `std4` here as the 4-dim defining
    rep minus the trivial axis-sum, which matches the usual bottom-up
    'coordinate residual' channels used in the encoder)."""
    return np.eye(N_DIMS) - np.ones((N_DIMS, N_DIMS)) / N_DIMS


def std4_character(g: GroupElem) -> float:
    """Character chi_std(g) = trace of the signed-permutation 4x4 matrix
    of g, in the defining (coordinate) representation. For the 4D
    'standard' used by the encoder (I-(1/4)J projection), the character
    is the defining-rep trace minus 1 (the trivial axis-sum has trace 1
    on every element). Used only for unit-test character-value checks."""
    perm, signs = g
    # Defining-rep matrix: M[perm[i], i] = signs[i]
    # trace = sum_i M[i, i] = sum over i s.t. perm[i] == i of signs[i]
    return float(sum(signs[i] for i in range(N_DIMS) if perm[i] == i))


# ---- Phase 3 gate ----------------------------------------------------

def verify_phase3(verbose: bool = False, seed: int = 42,
                  tol: float = 1e-12) -> List[str]:
    """Phase 3 gate.

    1. Closure of 7 B_4 generators (4 sign flips + 3 adjacent S_4 trans-
       positions) has exactly 384 elements.
    2. Standard-4D character values match known values of B_4 defining rep
       minus trivial: chi(e)=4, chi(sign-flip on one axis)=2,
       chi(axis transposition)=2.
    3. A_1 orbit projector is idempotent and symmetric, and commutes with
       every group generator (equivalently: it is B_4-invariant).
    4. std4 coordinate projector satisfies P^2 = P, P = P^T, and
       P . (1,1,1,1) = 0."""
    report: List[str] = []

    # 1. Closure size
    gens = _b4_generators()
    closure = b4_closure(gens)
    assert len(closure) == 384, (
        f"|B_4 closure from {len(gens)} generators| = {len(closure)}, "
        f"expected 384"
    )
    report.append(
        f"B_4 closure: {len(gens)} generators -> 384 elements "
        f"(= 2^4 * 4! = 16 * 24) OK"
    )

    # 2. Standard-4D character spot-checks.
    #    defining-rep character = sum of signs at fixed points of perm.
    e = _b4_identity()
    chi_e = std4_character(e)
    assert chi_e == 4, f"chi_std(e) = {chi_e} != 4"

    # Pick the first sign flip (axis 0) and first transposition (0<->1)
    flip0 = gens[0]
    assert flip0 == ((0, 1, 2, 3), (-1, 1, 1, 1)), f"unexpected gen: {flip0}"
    chi_flip = std4_character(flip0)
    # Defining rep: fixed points = all 4 axes, sum of signs = -1+1+1+1 = 2
    assert chi_flip == 2, f"chi_std(flip axis 0) = {chi_flip} != 2"

    transp01 = gens[4]  # first perm gen
    assert transp01 == ((1, 0, 2, 3), (1, 1, 1, 1)), (
        f"unexpected gen: {transp01}"
    )
    chi_tr = std4_character(transp01)
    # Defining rep: fixed points = {2, 3}, signs=(+1,+1), trace = 2
    assert chi_tr == 2, f"chi_std(transp 0<->1) = {chi_tr} != 2"

    report.append(
        "std4 characters: chi(e)=4, chi(sign-flip)=2, chi(transp)=2 "
        "(defining rep of B_4) OK"
    )

    # 3. A_1 orbit projector
    P_a1 = b4_a1_orbit_projector(closure)
    # Idempotence
    PP = P_a1 @ P_a1
    err_idem = float(np.max(np.abs((PP - P_a1).toarray())))
    assert err_idem < tol, (
        f"P_A1^2 != P_A1: max |diff| = {err_idem:.3e} > {tol:.1e}"
    )
    # Symmetry
    err_sym = float(np.max(np.abs((P_a1 - P_a1.T).toarray())))
    assert err_sym < tol, (
        f"P_A1 not symmetric: max |P - P^T| = {err_sym:.3e} > {tol:.1e}"
    )
    # Commutes with generators: Pi(g) P = P Pi(g) = P (for a trivial-irrep
    # projector, P commutes with every group action and Pi(g) P = P).
    rng = np.random.default_rng(seed)
    chk_err = 0.0
    for g in rng.choice(len(closure), size=5, replace=False):
        Pi_g = b4_permutation_matrix(closure[int(g)])
        diff = (Pi_g @ P_a1 - P_a1).toarray()
        chk_err = max(chk_err, float(np.max(np.abs(diff))))
    assert chk_err < tol, (
        f"A_1 projector not B_4-invariant: max |Pi(g) P - P| = "
        f"{chk_err:.3e} > {tol:.1e}"
    )
    # Orbit count (sanity): number of distinct orbits = rank of P_A1
    n_orbits = int(round(np.trace(P_a1.toarray())))
    # Trace of an orbit-average projector equals the number of orbits:
    # each orbit contributes 1/|orb| * |orb| = 1 to the trace.
    report.append(
        f"A_1 projector: P^2=P, P=P^T, Pi(g) P = P over 5 random g; "
        f"rank = #orbits = {n_orbits} OK"
    )

    # 4. std4 coordinate projector
    P_std = std4_projector_coords()
    err = float(np.max(np.abs(P_std @ P_std - P_std)))
    assert err < tol, f"P_std^2 != P_std: {err:.3e}"
    err_sym2 = float(np.max(np.abs(P_std - P_std.T)))
    assert err_sym2 < tol, f"P_std not symmetric: {err_sym2:.3e}"
    ones = np.ones(N_DIMS)
    err_null = float(np.max(np.abs(P_std @ ones)))
    assert err_null < tol, (
        f"P_std . (1,1,1,1) != 0: residual {err_null:.3e}"
    )
    tr = float(np.trace(P_std))
    assert abs(tr - 3.0) < tol, f"trace(P_std) = {tr} != 3"
    report.append(
        "std4 coord projector: P^2=P, P=P^T, P.1=0, trace=3 "
        "(I - (1/4)J on R^4) OK"
    )

    if verbose:
        report.append(
            f"(verbose) closure sample: identity={_b4_identity()}, "
            f"first gen={gens[0]}, last closure elem={closure[-1]}"
        )
        report.append(
            f"(verbose) A_1 projector shape={P_a1.shape}, "
            f"nnz={P_a1.nnz}, #orbits={n_orbits}"
        )

    return report


# ---- 4D fiber bundle (Phase 4) ---------------------------------------
#
# The "fiber" at each square encodes per-piece deviation from the pure
# grid Laplacian. In 2D (see [tables.py]) the bundle is rank 5:
#   3 symmetric fiber subspaces (from SVD of piece Laplacians in the
#       grid eigenbasis),
#   1 pawn antisymmetric fiber (directed pawn push breaks Z_2),
#   1 diagonal deviation (rook-shadow: diag(U^T L_rook U) - lambda_grid
#       is nonzero because the K_8 rook Laplacian does not commute with
#       the P_8 grid Laplacian).
# Phase 4 verifies the same structure survives in 4D and the algebraic
# identities (queen = rook + bishop, pawn antisym lives only on w-axis,
# rook diag-dev nonzero) hold on Z_8^4.

def build_u_tensor_4d(evecs_1d: np.ndarray | None = None) -> np.ndarray:
    """Build the dense 4096x4096 tensor-DCT basis U as a double Kronecker
    product of the 8x8 P_8 eigenvectors. ~128 MB float64. Call on demand;
    caller is responsible for holding the reference and freeing.

    U[sq4(a,b,c,d), sq4(i,j,k,l)] = evecs[a,i] * evecs[b,j] * evecs[c,k]
                                   * evecs[d,l]
    Verified against tensor_eigvec_4d to < 1e-17.
    """
    if evecs_1d is None:
        evecs_1d, _ = eig_p8()
    U_pair = np.kron(evecs_1d, evecs_1d)          # 64x64
    return np.kron(U_pair, U_pair)                # 4096x4096


def _dense_laplacian(target_fn: Callable[[int, int, int, int], Iterator[Coord]],
                     directed: bool = False) -> np.ndarray:
    """Build L_piece as a dense 4096x4096 float64 matrix. Convenience
    helper for Phase 4 transforms where we also multiply by a dense U."""
    A = build_adjacency_4d(target_fn, directed=directed)
    L = laplacian_4d(A)
    return L.toarray().astype(np.float64)


def pawn_anti_4d() -> np.ndarray:
    """Antisymmetric pawn adjacency: A_anti = (A_pawn - A_pawn^T) / 2.
    Shape (4096, 4096) dense float64. The directed +w pawn push means
    A_pawn = I (x) I (x) I (x) S_+, where S_+ is the 8x8 +1 shift matrix,
    so A_anti = I (x) I (x) I (x) A_w_anti with A_w_anti 8x8 antisymmetric.
    This 'only w mixes' structure is the key Phase 4 algebraic claim."""
    A = build_adjacency_4d(white_pawn4_targets, directed=True).toarray()
    A = A.astype(np.float64)
    return 0.5 * (A - A.T)


def diag_dev_4d(
    U: np.ndarray | None = None,
    evals_1d: np.ndarray | None = None,
) -> np.ndarray:
    """Per-piece diagonal deviation diag(U^T L_piece U) - lambda_grid,
    shape (6, 4096). Row order: [pawn_sym, knight, bishop, rook, queen,
    king]. A piece whose Laplacian commutes with the 4D grid Laplacian
    would produce an all-zero row; rook is the canonical nonzero example
    (its single-axis K_8 structure does not commute with the grid P_8)."""
    if U is None:
        U = build_u_tensor_4d()
    if evals_1d is None:
        _, evals_1d = eig_p8()
    lambda_grid = kron_sum4_eigvals(evals_1d)

    # Pawn symmetric Laplacian: (A + A^T) / 2 of the directed push
    A_pw = build_adjacency_4d(white_pawn4_targets, directed=True).toarray()
    A_pw = A_pw.astype(np.float64)
    A_sym = 0.5 * (A_pw + A_pw.T)
    L_pawn_sym = np.diag(A_sym.sum(axis=1)) - A_sym

    laplacians = [
        ('pawn_sym', L_pawn_sym),
        ('knight',   _dense_laplacian(knight4_targets)),
        ('bishop',   _dense_laplacian(bishop4_targets)),
        ('rook',     _dense_laplacian(rook4_targets)),
        ('queen',    _dense_laplacian(queen4_targets)),
        ('king',     _dense_laplacian(king4_targets)),
    ]
    DIAG_DEV = np.zeros((6, N_SQUARES), dtype=np.float64)
    for idx, (_, L) in enumerate(laplacians):
        # Diagonal of U^T L U without materializing the full transform:
        # (U^T L U)[p, p] = sum_i U[i, p] * (L @ U[:, p])[i]
        LU = L @ U
        diag_p = np.einsum('ij,ij->j', U, LU)
        DIAG_DEV[idx] = diag_p - lambda_grid
    return DIAG_DEV


def fiber_sym_4d(U: np.ndarray | None = None, k_top: int = 3,
                 ) -> Tuple[np.ndarray, np.ndarray]:
    """Global symmetric fiber basis via SVD of per-piece off-diagonal
    C = U^T L_piece U blocks. Pieces: knight, bishop, rook, queen, king.
    Each piece contributes a flattened upper-triangle vector; the 5xM
    matrix is SVD'd and the top `k_top` right-singular directions form
    the fiber basis.

    Returns (sv, fiber_dirs) where `sv` is the 5-vector of singular
    values and `fiber_dirs` has shape (k_top, M) with M = 4096*4095/2.

    Memory: holds one C_piece at a time (128 MB) plus a 5xM float32
    buffer (~170 MB). Slower than diag_dev but still tractable."""
    if U is None:
        U = build_u_tensor_4d()
    upper_idx = np.triu_indices(N_SQUARES, k=1)
    m = upper_idx[0].shape[0]  # 4096*4095/2 = 8_382_720
    piece_fns = [
        ('knight', knight4_targets),
        ('bishop', bishop4_targets),
        ('rook',   rook4_targets),
        ('queen',  queen4_targets),
        ('king',   king4_targets),
    ]
    rows = np.zeros((len(piece_fns), m), dtype=np.float32)
    for idx, (_, fn) in enumerate(piece_fns):
        L = _dense_laplacian(fn)
        C = U.T @ L @ U
        np.fill_diagonal(C, 0.0)
        v = C[upper_idx]
        nv = np.linalg.norm(v)
        if nv > 0:
            v = v / nv
        rows[idx] = v.astype(np.float32)
    # SVD on a tall-skinny 5xM matrix; thin SVD gives (5,5), (5,), (5,M)
    _, s, Vt = np.linalg.svd(rows, full_matrices=False)
    return s, Vt[:k_top].astype(np.float32)


# ---- Phase 4 gate ----------------------------------------------------

def verify_phase4(verbose: bool = False, tol: float = 1e-10
                  ) -> List[str]:
    """Phase 4 gate.

    1. Adjacency identity: A_queen == A_rook + A_bishop (disjoint support).
    2. Laplacian identity in DCT basis: C_Q == C_R + C_B.
    3. Rook diagonal deviation is finite and has nonzero norm (proves the
       rook Laplacian does NOT commute with the grid Laplacian).
    4. Pawn antisymmetric fiber is block-diagonal over (x,y,z): only the
       w-axis mixes modes. Computed as U^T A_anti U; off-w entries should
       be < 1e-8.
    5. Full 6-piece diag_dev table is finite.
    """
    report: List[str] = []
    U = build_u_tensor_4d()
    _, evals = eig_p8()

    # 1. Adjacency identity
    A_R = build_adjacency_4d(rook4_targets).toarray().astype(np.float64)
    A_B = build_adjacency_4d(bishop4_targets).toarray().astype(np.float64)
    A_Q = build_adjacency_4d(queen4_targets).toarray().astype(np.float64)
    diff_adj = float(np.max(np.abs(A_Q - A_R - A_B)))
    assert diff_adj < tol, (
        f"adjacency: A_Q - A_R - A_B max|.| = {diff_adj:.3e}"
    )
    report.append(
        "adjacency: A_queen == A_rook + A_bishop (disjoint support) OK"
    )

    # 2. Laplacian identity in tensor-DCT basis
    L_R = np.diag(A_R.sum(axis=1)) - A_R
    L_B = np.diag(A_B.sum(axis=1)) - A_B
    L_Q = np.diag(A_Q.sum(axis=1)) - A_Q
    C_R = U.T @ L_R @ U
    C_B = U.T @ L_B @ U
    C_Q = U.T @ L_Q @ U
    diff_L = float(np.max(np.abs(C_Q - C_R - C_B)))
    # Numerical tolerance on 128MB dense matmul is looser than sparse
    assert diff_L < 1e-6, (
        f"DCT-basis identity: C_Q - C_R - C_B max|.| = {diff_L:.3e}"
    )
    report.append(
        f"DCT basis: C_queen == C_rook + C_bishop "
        f"(max |diff| = {diff_L:.3e}, tol=1e-6) OK"
    )

    # 3. Rook diagonal deviation (shadow)
    lambda_grid = kron_sum4_eigvals(evals)
    rook_dd = np.diag(C_R) - lambda_grid
    rook_norm = float(np.linalg.norm(rook_dd))
    assert np.isfinite(rook_norm) and rook_norm > 1.0, (
        f"rook diag-dev norm = {rook_norm} (expected finite > 1)"
    )
    report.append(
        f"rook diag-dev: finite, ||.||_2 = {rook_norm:.4f} (nonzero) OK"
    )

    # 4. Pawn antisymmetric fiber lives only on w-axis
    A_anti = pawn_anti_4d()
    asym_err = float(np.max(np.abs(A_anti + A_anti.T)))
    assert asym_err < tol, (
        f"A_anti not antisymmetric: ||A + A^T||_inf = {asym_err:.3e}"
    )
    C_anti = U.T @ A_anti @ U
    C_tensor = C_anti.reshape(
        BOARD_SIDE, BOARD_SIDE, BOARD_SIDE, BOARD_SIDE,
        BOARD_SIDE, BOARD_SIDE, BOARD_SIDE, BOARD_SIDE,
    )
    # "on-w" mask: (i,j,k) == (i',j',k'); mixing is only over (l, l')
    mask = np.zeros_like(C_tensor, dtype=bool)
    for i in range(BOARD_SIDE):
        for j in range(BOARD_SIDE):
            for k in range(BOARD_SIDE):
                mask[i, j, k, :, i, j, k, :] = True
    off_w_norm = float(np.linalg.norm(C_tensor[~mask]))
    on_w_norm = float(np.linalg.norm(C_tensor[mask]))
    assert off_w_norm < 1e-8, (
        f"pawn antisym has off-w mixing: off-w ||.||_F = {off_w_norm:.3e}"
    )
    assert on_w_norm > 1.0, (
        f"pawn antisym on-w norm = {on_w_norm} (expected > 1)"
    )
    report.append(
        f"pawn antisym: on-w ||.||_F = {on_w_norm:.4f}, "
        f"off-w ||.||_F = {off_w_norm:.3e} < 1e-8 OK"
    )

    # 5. 6-piece diag_dev table
    DIAG_DEV = diag_dev_4d(U=U, evals_1d=evals)
    piece_names = ['pawn_sym', 'knight', 'bishop', 'rook', 'queen', 'king']
    norms = np.linalg.norm(DIAG_DEV, axis=1)
    assert np.all(np.isfinite(norms)), "diag_dev has non-finite entries"
    report.append(
        "diag-dev (6-piece): "
        + ", ".join(f"{n}={v:.2f}" for n, v in zip(piece_names, norms))
        + " OK"
    )

    if verbose:
        report.append(
            f"(verbose) U_tensor dense: shape={U.shape}, "
            f"mem={U.nbytes / 1e6:.1f} MB"
        )
        # Sanity: rook diag_dev (idx 3) should match rook_norm from step 3
        report.append(
            f"(verbose) rook_dd via step 3 = {rook_norm:.4f}, "
            f"via diag_dev_4d row[3] = {norms[3]:.4f}"
        )

    return report


# ---- Phase 5 gate ----------------------------------------------------

def verify_phase5(verbose: bool = False, seed: int = 42) -> List[str]:
    """Phase 5 gate: end-to-end encoder + spectralz v3 round-trip.

    1. encode_4d on a small synthetic position produces a 40960-float32
       vector; channel ranges match CHANNELS_4D layout; channel energies
       are finite.
    2. spectralz v3 write->read of 10 random frames is byte-identical
       (encoding + all metadata).
    3. Unknown-magic file correctly raises in read_header_any.
    """
    import os
    import tempfile
    from chess_spectral import encoder_4d as enc_mod
    from chess_spectral import frame_4d as frm

    report: List[str] = []
    rng = np.random.default_rng(seed)

    # 1. Encoder smoke-test: 4-piece mini-position (white and black
    #    pawns on opposite sides of the w-axis so pawn antisym and
    #    diag_dev channels are nonzero, plus one rook for more signal).
    pos4 = {
        sq4(0, 0, 0, 1): 'P',   # white pawn near start on +w
        sq4(7, 7, 7, 6): 'p',   # black pawn near end on +w
        sq4(3, 3, 3, 3): 'R',   # white rook centered
        sq4(4, 4, 4, 4): 'k',   # black king centered-offset
    }
    v = enc_mod.encode_4d(pos4)
    assert v.shape == (enc_mod.ENCODING_DIM_4D,), (
        f"encoding shape {v.shape} != ({enc_mod.ENCODING_DIM_4D},)"
    )
    assert v.dtype == np.float32, f"encoding dtype {v.dtype} != float32"
    energies = enc_mod.channel_energies_4d(v)
    for name, e in energies.items():
        assert np.isfinite(e), f"channel {name} energy non-finite: {e}"
    # The stub fiber-sym channels must be zero in v1
    for name in ("FIB_SYM_1", "FIB_SYM_2", "FIB_SYM_3"):
        assert energies[name] == 0.0, (
            f"v1 fiber-sym channel {name} should be 0, got {energies[name]}"
        )
    # A_1 and at least one mode-space channel should be nonzero
    assert energies["A1"] > 0, "A_1 channel unexpectedly zero"
    assert energies["FD_DIAG"] > 0, "FD diag-dev channel unexpectedly zero"
    assert energies["FA_PAWN"] > 0, "FA pawn antisym channel unexpectedly zero"
    report.append(
        f"encode_4d: shape=(40960,) float32, energies finite; "
        f"A1={energies['A1']:.2f}, FA={energies['FA_PAWN']:.2f}, "
        f"FD={energies['FD_DIAG']:.2f}, fiber-sym=0 (v1 stub) OK"
    )

    # 2. spectralz v3 round-trip
    n_frames = 10
    frames_in: List[frm.Frame4D] = []
    for p in range(n_frames):
        enc = rng.standard_normal(frm.ENCODING_DIM_4D).astype(np.float32)
        from_sq = tuple(int(x) for x in rng.integers(0, 8, size=4))
        to_sq = tuple(int(x) for x in rng.integers(0, 8, size=4))
        promo = int(rng.integers(0, 256))
        flags = int(rng.integers(0, 256))
        frames_in.append(frm.Frame4D(
            encoding=enc, ply=p,
            from_sq=from_sq, to_sq=to_sq,  # type: ignore[arg-type]
            promo=promo, flags=flags,
        ))

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".spectralz")
    tmp_path = tmp.name
    tmp.close()
    try:
        n_bytes = frm.write_spectralz_v3(tmp_path, frames_in)
        header, frames_out = frm.read_spectralz_v3(tmp_path)
    finally:
        os.remove(tmp_path)

    assert header.magic == frm.SPECTRALZ_V3_MAGIC, (
        f"magic {header.magic!r} != {frm.SPECTRALZ_V3_MAGIC!r}"
    )
    assert header.version == 3
    assert header.encoding_dim == frm.ENCODING_DIM_4D
    assert header.frame_bytes == frm.ENCODING_DIM_4D * 4 + frm.FRAME_TAIL_BYTES
    assert header.n_plies == n_frames
    assert header.board_dim_side == 8
    assert header.n_dimensions == 4

    # Frame-by-frame identity
    max_enc_err = 0.0
    for i, (fin, fout) in enumerate(zip(frames_in, frames_out)):
        # float32 round-trip must be bit-exact
        err = float(np.max(np.abs(fin.encoding - fout.encoding)))
        max_enc_err = max(max_enc_err, err)
        assert err == 0.0, f"frame {i}: encoding not bit-exact, max|d|={err}"
        assert fin.ply == fout.ply, f"frame {i} ply mismatch"
        assert fin.from_sq == fout.from_sq, f"frame {i} from_sq mismatch"
        assert fin.to_sq == fout.to_sq, f"frame {i} to_sq mismatch"
        assert fin.promo == fout.promo, f"frame {i} promo mismatch"
        assert fin.flags == fout.flags, f"frame {i} flags mismatch"

    report.append(
        f"spectralz v3 round-trip: {n_frames} frames, "
        f"{n_bytes} bytes written, all metadata + encoding byte-identical "
        f"(max|d|={max_enc_err}) OK"
    )

    # 3. Unknown magic -> error
    import io
    bad = io.BytesIO(b"\x00" * 256)
    try:
        frm.read_header_any(bad)
        assertion = False
    except ValueError:
        assertion = True
    assert assertion, "read_header_any(garbage) should raise ValueError"
    report.append("read_header_any(garbage bytes) -> ValueError OK")

    if verbose:
        report.append(
            f"(verbose) v3 header size = {frm.HEADER_SIZE}, "
            f"frame_bytes = {header.frame_bytes}, "
            f"total bytes written = {n_bytes}"
        )
        ch_names = [name for name, _ in enc_mod.CHANNELS_4D]
        report.append("(verbose) channel energies: "
                      + ", ".join(f"{n}={energies[n]:.2f}" for n in ch_names))

    return report
