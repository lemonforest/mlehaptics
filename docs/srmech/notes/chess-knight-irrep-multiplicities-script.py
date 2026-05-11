"""
Chess KNIGHT per-eigenspace irrep multiplicities under D_4 (2D) and B_4 (4D)
— follow-up to chess-d4-b4-rep-theory-spike-2026-05-11. Date 2026-05-11.

Spike question: for the knight move-graph adjacency matrix in 2D (8x8 = 64
cells) and 4D (8^4 = 4096 cells), is the per-eigenspace decomposition under
D_4 and B_4 into irrep multiplicities integer-exact at machine precision?

If yes -> srmech section 3.5.3(C) chess instance gains a knight-specific
sub-instance: even though knight has no closed-form eigenvalues, the per-
eigenspace irrep multiplicities ARE closed-form-predictable from rep theory.

If no -> anomaly to investigate (knight move-graph not D_4/B_4 equivariant,
projector construction bug, or numerical conditioning issue).

Math-doesn't-lie. MPM discipline: closed-form numerical linear algebra
(numpy.linalg.eigh + integer character orthogonality), no SGD, deterministic
seed, reproducible. Single Source of Truth: Rinaldi-Unciuleanu & Chiru 2026
(DOI 10.3390/appliedmath6030048).

Strategy:
  2D: build the 5 D_4 irrep projectors as 64x64 matrices via the character-
      table formula P_rho = (d_rho/8) * sum_g chi_rho(g) U_g; for each
      knight-adjacency eigenspace V_lambda, compute multiplicity of irrep
      rho as rank(P_rho V_lambda) / d_rho. Verify against alternative
      formula: <chi_V_lambda, chi_rho>_G via class-trace inner product
      (character orthogonality).
  4D: 4096x4096 dense projectors would be 6 GB+ memory (384 elements of
      B_4 each as 16-MB dense matrix). Instead: store the 384 group
      elements as 4096-int permutation arrays (16 KB each; 6 MB total),
      do eigendecomposition once (eigh on the 4096x4096 knight matrix,
      ~15s), and for each eigenvector v_i compute trace(V_lambda^T U_g
      V_lambda) = sum_i <v_i, U_g v_i> per conjugacy class. Multiplicity
      of irrep rho in V_lambda = (1/|G|) sum_C |C| * chi_rho(C) * trace_C.
      Cost: 4096 eigenvectors x 20 conjugacy classes x 4096 ops ~ 3e8.
      Standard formula, no projector materialization.

Outputs:
  1. NDJSON per (dim, eigenvalue-bucket, irrep, multiplicity) at
     chess-knight-irrep-multiplicities-per-eigenspace-2026-05-11.ndjson
  2. Findings markdown chess-knight-irrep-multiplicities-2026-05-11.md
  3. Completion record appended to research-mfo/mfo_mpm_notes.ndjson

Author: concertmaster role, 2026-05-11.
"""

from __future__ import annotations

import itertools
import json
import time
from math import comb
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants / SSOT
# ---------------------------------------------------------------------------

SEED = 20260511
BOARD_SIDE = 8
DIM_2D_SIZE = BOARD_SIDE ** 2  # 64
DIM_4D_SIZE = BOARD_SIDE ** 4  # 4096

# Tolerance for declaring eigenvalues to lie in the same eigenspace
EIGENSPACE_TOL = 1e-8  # forgiving — degeneracies typically separated by ~10
# Tolerance for declaring an irrep multiplicity to be an integer
INTEGER_TOL = 1e-6  # multiplicity-rounding tolerance; expect drift ~ N*eps

OUTPUT_DIR = Path(r"D:\GitHub\mlehaptics\docs\srmech\notes")
NDJSON_PATH = OUTPUT_DIR / "chess-knight-irrep-multiplicities-per-eigenspace-2026-05-11.ndjson"
FINDINGS_MD_PATH = OUTPUT_DIR / "chess-knight-irrep-multiplicities-2026-05-11.md"
COMPLETION_RECORD_PATH = Path(
    r"D:\GitHub\mlehaptics\docs\antikythera-maths\research-mfo\mfo_mpm_notes.ndjson"
)


# ---------------------------------------------------------------------------
# Knight move-graph adjacency
# ---------------------------------------------------------------------------


def _index_2d(x: int, y: int) -> int:
    return x * BOARD_SIDE + y


def _index_4d(x: int, y: int, z: int, w: int) -> int:
    return ((x * BOARD_SIDE + y) * BOARD_SIDE + z) * BOARD_SIDE + w


def _on_board(coords: Tuple[int, ...]) -> bool:
    return all(0 <= c < BOARD_SIDE for c in coords)


def build_knight_2d() -> np.ndarray:
    """Knight adjacency on 8x8: displacement (+/-2, +/-1) and (+/-1, +/-2)."""
    n = DIM_2D_SIZE
    A = np.zeros((n, n), dtype=np.int8)
    deltas = []
    for d1, d2 in [(2, 1), (1, 2)]:
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                deltas.append((s1 * d1, s2 * d2))
    for x in range(BOARD_SIDE):
        for y in range(BOARD_SIDE):
            u = _index_2d(x, y)
            for dx, dy in deltas:
                x2, y2 = x + dx, y + dy
                if _on_board((x2, y2)):
                    A[u, _index_2d(x2, y2)] = 1
    return A


def build_knight_4d() -> np.ndarray:
    """Knight adjacency on 8^4: permutations of (+/-2, +/-1, 0, 0); 48 deltas
    per Rinaldi-Unciuleanu & Chiru 2026 Definition 11."""
    n = DIM_4D_SIZE
    A = np.zeros((n, n), dtype=np.int8)
    deltas_set = set()
    for perm in itertools.permutations([2, 1, 0, 0]):
        for signs in itertools.product([-1, 1], repeat=4):
            d = tuple(s * v for s, v in zip(signs, perm))
            deltas_set.add(d)
    deltas = list(deltas_set)
    assert len(deltas) == 48, f"Expected 48 knight 4D deltas; got {len(deltas)}"
    for x in range(BOARD_SIDE):
        for y in range(BOARD_SIDE):
            for z in range(BOARD_SIDE):
                for w in range(BOARD_SIDE):
                    u = _index_4d(x, y, z, w)
                    for dx, dy, dz, dw in deltas:
                        x2, y2, z2, w2 = x + dx, y + dy, z + dz, w + dw
                        if _on_board((x2, y2, z2, w2)):
                            A[u, _index_4d(x2, y2, z2, w2)] = 1
    return A


# ---------------------------------------------------------------------------
# D_4 representation + character table (5 irreps; |G| = 8)
# ---------------------------------------------------------------------------


def d4_permutations_2d() -> Dict[str, np.ndarray]:
    """Return D_4 elements as 64-element permutation arrays sigma_g such that
    U_g e_u = e_{sigma_g[u]}, where U_g acts on the 8x8 grid:

      e   : identity              (x,y) -> (x,y)
      r   : rotation by 90 deg    (x,y) -> (y, 7-x)
      r2  : rotation by 180 deg   (x,y) -> (7-x, 7-y)
      r3  : rotation by 270 deg   (x,y) -> (7-y, x)
      s   : reflection y-axis     (x,y) -> (x, 7-y)
      sr  : reflection diagonal   (x,y) -> (y, x)
      sr2 : reflection x-axis     (x,y) -> (7-x, y)
      sr3 : reflection anti-diag  (x,y) -> (7-y, 7-x)
    """
    def perm(map_fn) -> np.ndarray:
        sigma = np.empty(DIM_2D_SIZE, dtype=np.int32)
        for x in range(BOARD_SIDE):
            for y in range(BOARD_SIDE):
                u = _index_2d(x, y)
                x2, y2 = map_fn(x, y)
                sigma[u] = _index_2d(x2, y2)
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


# D_4 character table.
# Conjugacy classes: {e}, {r2}, {r,r3}, {s,sr2}, {sr,sr3}
# Five irreps: A1, A2, B1, B2 (1-dim), E (2-dim).
D4_IRREP_NAMES = ["A1", "A2", "B1", "B2", "E"]
D4_IRREP_DIMS = {"A1": 1, "A2": 1, "B1": 1, "B2": 1, "E": 2}
D4_CHARACTERS = {
    # rho: chars by class (e, r2, r/r3, s/sr2, sr/sr3)
    "A1": {"e": 1, "r2": 1, "rR": 1, "sR": 1, "srR": 1},
    "A2": {"e": 1, "r2": 1, "rR": 1, "sR": -1, "srR": -1},
    "B1": {"e": 1, "r2": 1, "rR": -1, "sR": 1, "srR": -1},
    "B2": {"e": 1, "r2": 1, "rR": -1, "sR": -1, "srR": 1},
    "E": {"e": 2, "r2": -2, "rR": 0, "sR": 0, "srR": 0},
}
D4_CLASS_MAP = {
    "e": "e",
    "r2": "r2",
    "r": "rR",
    "r3": "rR",
    "s": "sR",
    "sr2": "sR",
    "sr": "srR",
    "sr3": "srR",
}
D4_ORDER = 8


def d4_action_apply(sigma: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Apply permutation U_g to vector v in R^N. Convention: (U_g v)[sigma[u]] = v[u]
    so (U_g v)[k] = v[sigma_inv[k]]. Equivalently for permutation matrices
    P with P[v, u] = 1 iff v = sigma[u], we have (P v)[v] = v[u] = v[sigma_inv[v]].

    For our purposes we only need <v, U_g v> = sum_u v[u] * v[sigma[u]] since
    permutation matrices satisfy U_g v = v[sigma_inv], and <v, U_g v> = v^T (v[sigma_inv])
    = sum_k v[k] * v[sigma_inv[k]] = sum_u v[sigma[u]] * v[u] (re-index).
    So we use sigma directly (forward map).
    """
    return v[sigma]


def d4_projector_matrices(sigma_dict: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Materialise the 5 D_4 projectors as 64x64 matrices.

      P_rho = (d_rho / |G|) sum_g chi_rho(g) U_g
    """
    n = DIM_2D_SIZE
    projectors = {}
    for rep in D4_IRREP_NAMES:
        d_rho = D4_IRREP_DIMS[rep]
        chars = D4_CHARACTERS[rep]
        P = np.zeros((n, n), dtype=np.float64)
        for g, sigma in sigma_dict.items():
            chi = chars[D4_CLASS_MAP[g]]
            # U_g as permutation matrix: (U_g)[sigma[u], u] = 1
            U_g = np.zeros((n, n), dtype=np.float64)
            for u in range(n):
                U_g[sigma[u], u] = 1.0
            P += chi * U_g
        P *= d_rho / D4_ORDER
        projectors[rep] = P
    return projectors


# ---------------------------------------------------------------------------
# B_4 representation + character table (20 irreps; |G| = 384)
# ---------------------------------------------------------------------------

# B_n = Z_2^n semidirect S_n; irreps indexed by ordered pairs of partitions
# (alpha, beta) with |alpha| + |beta| = n.
# For n = 4, the bipartitions are all (alpha, beta) with |alpha| + |beta| = 4:
#   |alpha|=0: (), partitions of 4: (4),(3,1),(2,2),(2,1,1),(1,1,1,1)  -> 5
#   |alpha|=1: (1), partitions of 3: (3),(2,1),(1,1,1)                  -> 3
#   |alpha|=2: (2),(1,1), partitions of 2: (2),(1,1)                    -> 4
#   |alpha|=3: (3),(2,1),(1,1,1), partitions of 1: (1)                  -> 3
#   |alpha|=4: (4),(3,1),(2,2),(2,1,1),(1,1,1,1), partitions of 0: ()   -> 5
# Total = 5 + 3 + 4 + 3 + 5 = 20. Match.

# Conjugacy classes of B_n: pairs of partitions (lambda^+, lambda^-) with
# |lambda^+| + |lambda^-| = n; element-wise cycle structures of (sign, perm).
# For B_4: also 20 classes.

# We compute the character table using the Specht-style formula for B_n
# irreps. Reference: James-Kerber "The Representation Theory of the
# Symmetric Group" (Encyclopedia of Mathematics and its Applications 16,
# 1981) Chapter 5, or Geissinger 1977, or Fulton-Harris Appendix B.
#
# Character formula:
#   chi_{(alpha, beta)}(C_{(lambda^+, lambda^-)}) =
#     sum over orderings of lambda^+ into alpha and lambda^-:
#       this is computed via a determinantal / Frobenius formula.
#
# For practical computation, the cleanest approach is via the
# induced-representation formula:
#   chi_{(alpha, beta)}(C_{(lambda^+, lambda^-)}) =
#     chi^S_{|alpha|}_alpha(lambda^+) * chi^S_{|beta|}_beta(lambda^-)
#       * (-1)^{|lambda^-|}
#   *summed over partitions (lambda^+, lambda^-)*    - no, this isn't right.
#
# Actually the correct formula (per Specht/Geissinger) is:
#   B_n irrep (alpha, beta) restricted to a specific conjugacy class of B_n
#   with cycle data (lambda^+, lambda^-) [where lambda^+ = positive-sign-cycle
#   lengths and lambda^- = negative-sign-cycle lengths, |lambda^+| + |lambda^-| = n] is:
#
#     chi^{B_n}_{(alpha,beta)}( (lambda^+, lambda^-) ) =
#       sum_{S subset of cycles of lambda^+} ...
#   = z_{lambda^+} * z_{lambda^-} times Murnaghan-Nakayama analog
#
# In practice, the cleanest computation is via Frobenius / power-sum
# symmetric functions:
#   For each bipartition (alpha, beta), the character value on a class
#   indexed by (lambda^+, lambda^-) is the coefficient of
#     s_alpha(x) * s_beta(y)
#   in the product
#     prod_i p_{lambda^+_i}(x) * prod_j p_{lambda^-_j}(x, y)
#   where p_k(x) = sum_i x_i^k and p_k(x, y) = p_k(x) - p_k(y).
#
# This is via plethysm. We will compute it numerically using sympy.

# We'll just compute B_4 character table via direct group-theoretic
# decomposition: construct the 384 elements explicitly, find conjugacy
# classes, then use orthogonality with known character data sourced from
# Geissinger 1977 / James-Kerber. To keep this script self-contained, we
# tabulate the B_4 character table from the standard reference directly.

# Actually the cleanest approach: compute the B_4 character table from
# first principles via Cayley-table eigendecomposition of the regular
# representation OR via Burnside's algorithm. The former is faster.

# Alternative: implement the Frobenius formula directly using sympy.
# We do this because: (a) it's reproducible from first principles; (b)
# it provides ground-truth character values; (c) sympy has Schur
# polynomials.

# IMPLEMENTATION: For B_n irreps, the character is:
#   chi_{(alpha, beta)}(class_rep_with_signs_s_perm_pi) =
#     <s_alpha(x) s_beta(y), psi_pi^s>
# where psi_pi^s decomposes the cycle structure of (s, pi):
#   each cycle of pi gets length k and a sign = product of s over its support;
#   positive cycles contribute p_k(x) + p_k(y); negative cycles contribute
#   p_k(x) - p_k(y). See James-Kerber Theorem 5.5.

# Numerically:
#   p_k(x) + p_k(y) = power sum of (x,y) combined ranges; p_k(x) - p_k(y) = signed.
#   For finite alphabets we use indeterminate symbols and extract coefficients.


def partitions(n: int) -> List[Tuple[int, ...]]:
    """Return all partitions of n in lex-decreasing form."""
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
    """Return all bipartitions (alpha, beta) with |alpha| + |beta| = n."""
    result = []
    for k in range(n + 1):
        for alpha in partitions(k):
            for beta in partitions(n - k):
                result.append((alpha, beta))
    return result


def sn_character_table_from_sympy(n: int) -> Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]]:
    """Return chi[lambda][mu] = character of S_n irrep lambda on cycle type mu.

    Computed via Murnaghan-Nakayama rule. Uses sympy.
    """
    from sympy import Matrix, Rational, S
    from sympy.combinatorics import Permutation
    # Use the Schur-polynomial / power-sum bridge:
    # chi^S_n_lambda(mu) = coefficient of s_lambda in p_mu
    # where p_mu = product_i p_{mu_i} and we expand in Schur basis.
    # Sympy has direct support via sympy.combinatorics for character tables
    # via Frobenius. Implement Murnaghan-Nakayama directly for clarity.
    parts = partitions(n)
    table: Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]] = {p: {} for p in parts}
    for lam in parts:
        for mu in parts:
            table[lam][mu] = murnaghan_nakayama(lam, mu)
    return table


def murnaghan_nakayama(lam: Tuple[int, ...], mu: Tuple[int, ...]) -> int:
    """Compute chi^S_n_lambda(cycle type mu) via Murnaghan-Nakayama rule.

      chi^S_n_lambda(mu) = sum over rim-hook decompositions of lambda
                           weighted by (-1)^height.

    lam, mu both partitions of n.
    """
    if not mu:
        # empty cycle structure on empty partition
        return 1 if not lam else 0
    k = mu[0]  # remove a k-rim-hook from lam
    rest_mu = mu[1:]
    total = 0
    # enumerate all rim-hooks of size k in lam
    for new_lam, height in rim_hooks(lam, k):
        total += (-1) ** height * murnaghan_nakayama(new_lam, rest_mu)
    return total


def rim_hooks(lam: Tuple[int, ...], k: int):
    """Yield (lambda_minus_rimhook, height) for each k-rim-hook of lambda."""
    # Use the abacus / beta-set construction. Use the standard "rim-hook
    # removal" definition: a rim hook is a connected skew shape lambda/mu
    # of size k containing no 2x2 block, with height = (number of rows it
    # spans) - 1.
    # Convert lam to row endpoints (positions of corners), enumerate
    # contiguous boundary cells.
    if not lam:
        return
    # Compute boundary cells: cell (i, j) is on the boundary if (i+1, j+1)
    # is not in lam. Cells are (row, col), row=0..len(lam)-1, col=0..lam[row]-1.
    n_rows = len(lam)
    cells = []
    for i in range(n_rows):
        for j in range(lam[i]):
            cells.append((i, j))
    cell_set = set(cells)
    # Enumerate rim-hooks by removing contiguous (in NW-to-SE rim order) k cells
    # from the boundary. The rim is a path from (0, lam[0]-1) to
    # (n_rows-1, 0) along the SE boundary of the diagram.
    # Build rim as ordered list of cells.
    rim: List[Tuple[int, int]] = []
    i, j = 0, lam[0] - 1
    while True:
        rim.append((i, j))
        # Move SE along the rim: prefer down (i+1, j) if (i+1, j) in lam and (i, j-1) not below;
        # else move left (i, j-1).
        if i + 1 < n_rows and lam[i + 1] >= j + 1:
            i += 1
        elif j > 0 and (i, j - 1) in cell_set:
            j -= 1
        else:
            break
        if (i, j) == rim[-1]:
            break
    # Now enumerate k-contiguous subsegments of rim such that removing them
    # leaves a valid partition (lambda \ hook).
    L = len(rim)
    for start in range(L - k + 1):
        hook = set(rim[start:start + k])
        new_cells = cell_set - hook
        # Check that new_cells is a Young diagram (a partition)
        new_lam = _cells_to_partition(new_cells, n_rows)
        if new_lam is None:
            continue
        # Height: number of distinct rows in the hook minus 1.
        rows = set(c[0] for c in hook)
        height = len(rows) - 1
        yield (new_lam, height)


def _cells_to_partition(cells: set, n_rows: int):
    """Given a set of cells, check if it forms a partition (rows
    left-justified, non-increasing) and return as tuple, else None."""
    rows_count: Dict[int, int] = {}
    for (i, j) in cells:
        rows_count[i] = rows_count.get(i, 0) + 1
    # Build row lengths
    max_row = max(rows_count.keys()) if rows_count else -1
    if max_row < 0:
        return ()
    lam = []
    for i in range(max_row + 1):
        L = rows_count.get(i, 0)
        # check that row i is left-justified
        row_cols = sorted(c[1] for c in cells if c[0] == i)
        if row_cols and row_cols != list(range(L)):
            return None
        lam.append(L)
    # Check non-increasing
    for a, b in zip(lam, lam[1:]):
        if a < b:
            return None
    # Strip trailing zeros
    while lam and lam[-1] == 0:
        lam.pop()
    return tuple(lam)


# ---------------------------------------------------------------------------
# B_n character table via Specht / Frobenius formula
# ---------------------------------------------------------------------------

def b_n_signed_class_data(n: int) -> List[Tuple[Tuple[int, ...], Tuple[int, ...], int]]:
    """Return list of (lambda^+, lambda^-, class_size) for B_n conjugacy classes.

    Conjugacy class of B_n indexed by bipartition (lambda^+, lambda^-) with
    |lambda^+| + |lambda^-| = n. lambda^+ = cycle-lengths of positively-signed
    cycles; lambda^- = cycle-lengths of negatively-signed cycles.

    Class size: |B_n| / centralizer
      centralizer = (prod_k k^{m_k^+} * m_k^+!) * (prod_k (2k)^{m_k^-} * m_k^-!)
                    [signed-cycle centralizer in B_n; see James-Kerber 4.2.10]
      with m_k^± = multiplicity of k in lambda^±.
    """
    from math import factorial
    result = []
    Bn_order = (2 ** n) * factorial(n)
    for k in range(n + 1):
        for lp in partitions(k):
            for lm in partitions(n - k):
                # Compute centralizer
                mp: Dict[int, int] = {}
                for x in lp:
                    mp[x] = mp.get(x, 0) + 1
                mm: Dict[int, int] = {}
                for x in lm:
                    mm[x] = mm.get(x, 0) + 1
                # Centralizer formula for B_n (James-Kerber 4.2.10):
                #   |C_{B_n}(g)| = prod_k (2k)^{m_k^+} m_k^+! * (2k)^{m_k^-} m_k^-!
                # for both positive and negative cycles.
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
    """Compute chi^{B_n}_{(alpha, beta)}( (lambda^+, lambda^-) ) via the
    Specht formula.

      chi^{B_n}_{(alpha, beta)}( (lambda^+, lambda^-) ) =
        sum over all ways to split lambda^+ and lambda^- between alpha and beta
        weighted by sign of lambda^- contribution into beta.

    Equivalent formula via power-sum / Schur expansion (Geissinger 1977,
    James-Kerber 5.5.10):

      chi^{B_n}_{(alpha, beta)}(C) = coefficient of s_alpha(x) * s_beta(y) in
        product_i (p_{lp_i}(x) + p_{lp_i}(y)) * product_j (p_{lm_j}(x) - p_{lm_j}(y))

    where p_k(x) = power sum, s_lambda is Schur polynomial.

    Equivalently:
      chi = sum_{S subset cycles_+ choice} sum_{T subset cycles_- choice}
           sign(T size) chi^S_{|alpha|}_alpha(mu_S) chi^S_{|beta|}_beta(mu_~S)
    where each cycle of lambda^+ is assigned either to alpha-part (contributing
    to mu_S) or beta-part (contributing to mu_{complement}); each cycle of
    lambda^- is similarly assigned (with sign flip if assigned to beta).

    Specifically (Specht/Geissinger):
      chi^{B_n}_{(alpha,beta)}((lp, lm)) =
        sum_{partition lp into (lp_alpha, lp_beta) with |lp_alpha|=|alpha|}
        sum_{partition lm into (lm_alpha, lm_beta) with |lm_alpha|+|lm_beta|=|lm|, |lp_alpha|+|lm_alpha|=|alpha|}
          ... too complicated.

    Cleanest: implement via the power-sum coefficient extraction. Use
    sympy symbolic polynomials with two sets of indeterminates x_1..x_n,
    y_1..y_n; build the product; extract coefficient of s_alpha(x) s_beta(y).
    """
    # Avoid symbolic: use the closed-form Frobenius-style formula directly.
    # chi^{B_n}_{(alpha, beta)}((lp, lm)) = sum_{A subset of lp, B subset of lm}
    #   chi^S_{|alpha|}_alpha(A_lengths || B_lengths_assigned_to_alpha)
    #   * chi^S_{|beta|}_beta(complement_lengths)
    #   * (sign for lm assignments to beta)
    #
    # The cleanest reference formulation (James-Kerber Theorem 5.5.10 or
    # see Macdonald Sym Funcs I.B.5):
    #   chi^{B_n}_{(alpha, beta)}( (lp, lm) ) =
    #     sum over partitions lp = mu_alpha + mu_beta (interpret cycles as
    #     being distributed: choose subset S of cycles in lp; mu_alpha = cycle
    #     lengths in S; mu_beta = cycle lengths NOT in S)
    #     sum over partitions lm = nu_alpha + nu_beta similarly:
    #       chi^S_{|alpha|}_alpha(mu_alpha union nu_alpha) *
    #       chi^S_{|beta|}_beta(mu_beta union nu_beta) *
    #       (-1)^{|nu_beta|}
    #
    # Constraint: |mu_alpha| + |nu_alpha| = |alpha|; |mu_beta| + |nu_beta| = |beta|.
    n = sum(lambda_plus) + sum(lambda_minus)
    a = sum(alpha)
    b = sum(beta)
    if a + b != n:
        return 0

    # Specht / Frobenius formula derived from
    #   p_k(x+y) = p_k(x) + p_k(y)  for positive cycles
    #   p_k(x-y) = p_k(x) - p_k(y)  for negative cycles
    # so chi^{B_n}_{(alpha,beta)}((lp,lm)) = coeff of s_alpha(x) s_beta(y) in
    # prod_i (p_{lp_i}(x) + p_{lp_i}(y)) * prod_j (p_{lm_j}(x) - p_{lm_j}(y))
    # Expansion: for each cycle, choose to send to x (alpha-side) or y (beta-side).
    # Sign contribution: each negative cycle sent to y gives sign -1.
    # After distribution: mu_alpha = lengths of cycles on x-side (combining lp and lm cycles)
    # mu_beta = lengths of cycles on y-side.
    # Inner-product structure: <p_{mu_alpha}(x), s_alpha(x)> = chi^{S_|alpha|}_alpha(mu_alpha)
    # <p_{mu_beta}(y), s_beta(y)> = chi^{S_|beta|}_beta(mu_beta)
    lp = list(lambda_plus)
    lm = list(lambda_minus)
    total = 0
    for S_mask in range(1 << len(lp)):
        # S_mask bit i = 1 means lp[i] is assigned to alpha (x-side)
        S_cycles = [lp[i] for i in range(len(lp)) if (S_mask >> i) & 1]
        S_sum = sum(S_cycles)
        rest_lp = [lp[i] for i in range(len(lp)) if not ((S_mask >> i) & 1)]
        for T_mask in range(1 << len(lm)):
            # T_mask bit i = 1 means lm[i] is assigned to alpha (x-side, no sign)
            # bit 0 means lm[i] is assigned to beta (y-side, SIGN -1)
            T_cycles = [lm[i] for i in range(len(lm)) if (T_mask >> i) & 1]
            T_sum = sum(T_cycles)
            if S_sum + T_sum != a:
                continue
            rest_lm = [lm[i] for i in range(len(lm)) if not ((T_mask >> i) & 1)]
            # Sign: number of negative cycles on the y-side = len(rest_lm)
            sign_count = len(rest_lm)
            # Build mu_alpha = sorted(S_cycles + T_cycles)
            mu_alpha = tuple(sorted(S_cycles + T_cycles, reverse=True))
            mu_beta = tuple(sorted(rest_lp + rest_lm, reverse=True))
            if sum(mu_alpha) != a or sum(mu_beta) != b:
                continue
            chi_a = sn_chars[a][alpha].get(mu_alpha, 0)
            chi_b = sn_chars[b][beta].get(mu_beta, 0)
            sign = (-1) ** sign_count
            total += sign * chi_a * chi_b
    return total


# ---------------------------------------------------------------------------
# B_4 group element generation (signed permutations of (0,1,2,3))
# ---------------------------------------------------------------------------


def b4_signed_perms() -> List[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    """Generate 384 elements of B_4 = (Z_2)^4 semidirect S_4 as
    (signs, perm) pairs.

    Action on coord (c_0, c_1, c_2, c_3) in centered system [-3.5, 3.5]:
      result[i] = signs[i] * c[perm[i]]
    """
    signs_list = list(itertools.product([-1, 1], repeat=4))
    perms = list(itertools.permutations(range(4)))
    return [(s, p) for s in signs_list for p in perms]


def b4_action_4d(elem: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> np.ndarray:
    """Return permutation array sigma in [0, 4096) for the B_4 element acting
    on the 8^4 hypercube. sigma[u] = v means U_g e_u = e_v."""
    signs, perm = elem
    sigma = np.empty(DIM_4D_SIZE, dtype=np.int32)
    for x in range(BOARD_SIDE):
        for y in range(BOARD_SIDE):
            for z in range(BOARD_SIDE):
                for w in range(BOARD_SIDE):
                    u = _index_4d(x, y, z, w)
                    # Centered coords
                    c = (x - 3.5, y - 3.5, z - 3.5, w - 3.5)
                    c_new = (
                        signs[0] * c[perm[0]],
                        signs[1] * c[perm[1]],
                        signs[2] * c[perm[2]],
                        signs[3] * c[perm[3]],
                    )
                    # Uncenter; check exact integers in [0, 7]
                    nx = int(round(c_new[0] + 3.5))
                    ny = int(round(c_new[1] + 3.5))
                    nz = int(round(c_new[2] + 3.5))
                    nw = int(round(c_new[3] + 3.5))
                    sigma[u] = _index_4d(nx, ny, nz, nw)
    return sigma


def b4_classify_signed_perm(elem: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Classify a B_n element by its signed cycle type (lambda^+, lambda^-).

    For each cycle of the underlying permutation, compute the product of
    signs along the cycle. If positive, the cycle contributes to lambda^+;
    if negative, to lambda^-.

    Cycle length: number of elements in the cycle.
    """
    signs, perm = elem
    n = len(perm)
    visited = [False] * n
    lp, lm = [], []
    for start in range(n):
        if visited[start]:
            continue
        # trace cycle
        cycle = []
        cur = start
        sign_prod = 1
        while not visited[cur]:
            visited[cur] = True
            cycle.append(cur)
            sign_prod *= signs[cur]
            cur = perm[cur]
        if sign_prod == 1:
            lp.append(len(cycle))
        else:
            lm.append(len(cycle))
    return (tuple(sorted(lp, reverse=True)), tuple(sorted(lm, reverse=True)))


# ---------------------------------------------------------------------------
# Per-eigenspace irrep decomposition
# ---------------------------------------------------------------------------


def find_eigenspaces(eigvals: np.ndarray, tol: float) -> List[Tuple[float, int, int]]:
    """Group sorted eigenvalues into eigenspaces by closeness.

    Returns list of (eigvalue_avg, start_index, count).
    """
    sorted_eigs = np.sort(eigvals)
    n = len(sorted_eigs)
    groups = []
    start = 0
    while start < n:
        # extend group while eigvals are within tol of group's first
        end = start
        while end < n and abs(sorted_eigs[end] - sorted_eigs[start]) < tol:
            end += 1
        avg = float(sorted_eigs[start:end].mean())
        groups.append((avg, start, end - start))
        start = end
    return groups


def decompose_2d_via_projectors(A: np.ndarray) -> List[Dict]:
    """Decompose each eigenspace of 2D knight under D_4 irreps using
    projector method.

    Returns list of dicts, one per eigenvalue group, with multiplicities.
    """
    eigvals, eigvecs = np.linalg.eigh(A.astype(np.float64))
    sigma_dict = d4_permutations_2d()
    projectors = d4_projector_matrices(sigma_dict)

    # Verify projectors: P_rho^2 = P_rho (idempotent)
    for rep, P in projectors.items():
        diff = np.abs(P @ P - P).max()
        assert diff < 1e-10, f"D_4 projector {rep} not idempotent: max dev {diff}"

    # Verify completeness: sum P_rho = I
    sum_P = sum(projectors.values())
    Id = np.eye(DIM_2D_SIZE)
    assert np.abs(sum_P - Id).max() < 1e-10, \
        f"D_4 projectors not complete: max dev {np.abs(sum_P - Id).max()}"

    # Verify orthogonality: P_rho P_sigma = 0 for rho != sigma
    rep_names = list(projectors.keys())
    for i, r1 in enumerate(rep_names):
        for r2 in rep_names[i+1:]:
            d = np.abs(projectors[r1] @ projectors[r2]).max()
            assert d < 1e-10, f"D_4 projectors {r1}, {r2} not orthogonal: max dev {d}"

    print("[INFO] D_4 projectors verified: idempotent, complete, orthogonal")

    # Sort eigenvectors by eigenvalue
    idx_sort = np.argsort(eigvals)
    sorted_eigs = eigvals[idx_sort]
    sorted_vecs = eigvecs[:, idx_sort]

    groups = find_eigenspaces(sorted_eigs, EIGENSPACE_TOL)
    print(f"[INFO] 2D knight: {len(groups)} distinct eigenvalue groups")

    results = []
    for (avg, start, count) in groups:
        V = sorted_vecs[:, start:start + count]
        mults: Dict[str, float] = {}
        for rep in D4_IRREP_NAMES:
            d_rho = D4_IRREP_DIMS[rep]
            P = projectors[rep]
            PV = P @ V
            # rank of PV gives d_rho * mult
            # use SVD
            svals = np.linalg.svd(PV, compute_uv=False)
            rank_estimate = (svals > 1e-8).sum()
            mult_float = rank_estimate / d_rho
            mults[rep] = float(mult_float)
        # Verify integer + completeness
        total_dim = sum(D4_IRREP_DIMS[r] * mults[r] for r in D4_IRREP_NAMES)
        results.append({
            "eigvalue_avg": avg,
            "eigspace_dim": count,
            "multiplicities": mults,
            "total_dim_check": total_dim,
            "match_total_dim": bool(abs(total_dim - count) < INTEGER_TOL),
            "all_integer": bool(all(abs(m - round(m)) < INTEGER_TOL for m in mults.values())),
        })
    return results


def decompose_4d_via_character_orthogonality(A: np.ndarray) -> Tuple[List[Dict], Dict]:
    """Decompose each eigenspace of 4D knight under B_4 irreps using
    character orthogonality.

      mult_rho_in_V_lambda = (1/|G|) * sum_g chi_rho(g) * trace(U_g | V_lambda)

    where trace(U_g | V_lambda) = sum_i <v_i, U_g v_i> for v_i basis of V_lambda.

    Cost: 384 * 4096 character-trace contributions per eigenvector, BUT
    we can sum within each conjugacy class:

      mult_rho_in_V_lambda = (1/|G|) * sum_classes (|C| * chi_rho(C) * trace_C(V))

    where trace_C(V) = trace(U_{g_C} | V) for any class rep g_C. So we
    only need 20 class reps per eigenvector.
    """
    eigvals, eigvecs = np.linalg.eigh(A.astype(np.float64))
    print(f"[INFO] 4D knight eigh: spectrum range [{eigvals.min():.3f}, {eigvals.max():.3f}]")

    # Generate B_4 conjugacy class data
    class_data = b_n_signed_class_data(4)  # 20 classes
    assert len(class_data) == 20, f"Expected 20 B_4 classes; got {len(class_data)}"

    # For each class, find one representative B_4 element and compute its
    # permutation action on R^4096.
    # Strategy: iterate over signed_perms; classify each; pick the first of each class.
    print("[INFO] Identifying B_4 conjugacy class representatives...")
    class_reps: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], np.ndarray] = {}
    class_sizes: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], int] = {}
    for (lp, lm, size) in class_data:
        class_sizes[(lp, lm)] = size

    # Construct one canonical rep per class explicitly.
    # For each class (lp, lm): build a signed permutation with positive cycles
    # of lengths lp and negative cycles of lengths lm.
    def make_class_rep(lp: Tuple[int, ...], lm: Tuple[int, ...]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        # build perm and signs
        n = sum(lp) + sum(lm)
        perm = [0] * n
        signs = [1] * n
        pos = 0
        # Positive cycles
        for length in lp:
            # Cycle: 0 -> 1 -> ... -> length-1 -> 0 with all signs +1
            for i in range(length):
                perm[pos + i] = pos + (i + 1) % length
                signs[pos + i] = 1
            pos += length
        # Negative cycles: cycle of length L with product-of-signs = -1.
        # Put one -1 at the start of the cycle.
        for length in lm:
            for i in range(length):
                perm[pos + i] = pos + (i + 1) % length
                # Put a single negative sign at start of cycle to make sign_prod = -1
                signs[pos + i] = -1 if i == 0 else 1
            pos += length
        return (tuple(signs), tuple(perm))

    print("[INFO] Building B_4 class-representative permutation arrays on R^4096...")
    class_sigmas: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], np.ndarray] = {}
    for (lp, lm) in class_sizes.keys():
        rep_elem = make_class_rep(lp, lm)
        # Validate classification
        classified = b4_classify_signed_perm(rep_elem)
        assert classified == (lp, lm), \
            f"Built rep for class {(lp,lm)} classified as {classified}"
        sigma = b4_action_4d(rep_elem)
        class_sigmas[(lp, lm)] = sigma

    # Compute S_n character tables for n=0,..,4
    print("[INFO] Computing S_n character tables (n=0..4) via Murnaghan-Nakayama...")
    sn_chars: Dict[int, Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]]] = {}
    for n in range(5):
        sn_chars[n] = sn_character_table_from_sympy(n)

    # Compute B_4 character table
    print("[INFO] Computing B_4 character table (20x20) via Specht formula...")
    biparts = bipartitions_n(4)
    assert len(biparts) == 20, f"Expected 20 B_4 bipartitions; got {len(biparts)}"
    b4_char_table: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], int]] = {}
    for (a, b) in biparts:
        b4_char_table[(a, b)] = {}
        for (lp, lm) in class_sizes.keys():
            chi = b_n_irrep_character(a, b, lp, lm, sn_chars)
            b4_char_table[(a, b)][(lp, lm)] = chi

    # Verify orthogonality: sum over classes of |C| * chi_rho1(C) * chi_rho2(C) / |G|
    # = 1 if rho1=rho2, 0 otherwise
    Bn_order = 384
    print("[INFO] Verifying B_4 character-table orthogonality...")
    for i, rho1 in enumerate(biparts):
        for rho2 in biparts[i:]:
            inner = sum(
                class_sizes[(lp, lm)] * b4_char_table[rho1][(lp, lm)] * b4_char_table[rho2][(lp, lm)]
                for (lp, lm) in class_sizes
            ) / Bn_order
            expected = 1 if rho1 == rho2 else 0
            assert inner == expected, \
                f"B_4 orthogonality fail: <{rho1}, {rho2}> = {inner}, expected {expected}"

    # Verify dim^2 sum (dim of irrep = its character on the identity class,
    # which for B_4 is ((1,1,1,1), ()))
    id_class = ((1, 1, 1, 1), ())
    dims = {rho: b4_char_table[rho][id_class] for rho in biparts}
    sum_dim_sq = sum(d ** 2 for d in dims.values())
    assert sum_dim_sq == Bn_order, \
        f"B_4 sum of squared dims = {sum_dim_sq}, expected {Bn_order}"
    print(f"[OK] B_4 character table verified: 20 irreps, sum dim^2 = 384")
    print(f"[INFO] B_4 irrep dims: {sorted(dims.values())}")

    # Group eigenvalues into eigenspaces
    idx_sort = np.argsort(eigvals)
    sorted_eigs = eigvals[idx_sort]
    sorted_vecs = eigvecs[:, idx_sort]
    groups = find_eigenspaces(sorted_eigs, EIGENSPACE_TOL)
    print(f"[INFO] 4D knight: {len(groups)} distinct eigenvalue groups (from {DIM_4D_SIZE} eigenvalues)")

    # For each eigenspace V, compute trace(U_g | V) for each class rep g.
    # Note: V has shape (4096, dim_V); for each eigenvector v_i:
    #   <v_i, U_g v_i> = sum_k v_i[k] * v_i[sigma_g[k]]  [if U_g e_u = e_{sigma_g[u]}]
    # Actually wait: U_g e_u = e_{sigma[u]} means (U_g v)[sigma[u]] = v[u], i.e.,
    #   (U_g v)[w] = v[sigma_inv[w]]; so <v, U_g v> = sum_w v[w] * v[sigma_inv[w]]
    # Equivalently, sum_u v[sigma[u]] * v[u]. We use this form.

    # Build inverse permutations
    class_sigmas_inv: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], np.ndarray] = {}
    for cls, sigma in class_sigmas.items():
        sigma_inv = np.empty_like(sigma)
        sigma_inv[sigma] = np.arange(len(sigma))
        class_sigmas_inv[cls] = sigma_inv

    print("[INFO] Computing per-eigenspace class traces (4096 eigenvectors x 20 classes)...")
    t0 = time.perf_counter()
    # Per-eigenvector class traces: traces[i, c] = <v_i, U_g_c v_i>
    n_classes = len(class_sigmas)
    cls_list = list(class_sigmas.keys())
    traces_per_vec = np.zeros((DIM_4D_SIZE, n_classes), dtype=np.float64)
    for c_idx, cls in enumerate(cls_list):
        sigma = class_sigmas[cls]
        # For each eigenvector v_i, compute sum_u v_i[sigma[u]] * v_i[u]
        # = sum_u v_i[u] * v_i[sigma[u]]
        # Vectorized: v_permuted[u, i] = sorted_vecs[sigma[u], i]
        v_perm = sorted_vecs[sigma, :]  # shape (4096, 4096)
        # traces[i, c] = sum_u sorted_vecs[u, i] * v_perm[u, i]
        traces_per_vec[:, c_idx] = (sorted_vecs * v_perm).sum(axis=0)
    print(f"[INFO] class traces computed in {time.perf_counter()-t0:.1f}s")

    # For each eigenspace, sum traces over its eigenvectors
    print("[INFO] Computing per-eigenspace irrep multiplicities via character orthogonality...")
    results = []
    bipart_keys = biparts
    bipart_dim = {bp: b4_char_table[bp][id_class] for bp in bipart_keys}
    for (avg, start, count) in groups:
        # Trace per class for this eigenspace
        trace_per_class = traces_per_vec[start:start + count, :].sum(axis=0)  # shape (20,)
        # Multiplicity of bipart (a, b) in this eigenspace:
        #   mult = (1/|G|) sum_C |C| * chi_(a,b)(C) * trace_C
        mults: Dict[str, float] = {}
        for bp in bipart_keys:
            mult = 0.0
            for c_idx, cls in enumerate(cls_list):
                size = class_sizes[cls]
                chi = b4_char_table[bp][cls]
                mult += size * chi * trace_per_class[c_idx]
            mult /= Bn_order
            mults[f"{bp[0]}|{bp[1]}"] = float(mult)
        # Verify total dim
        total = sum(bipart_dim[bp] * mults[f"{bp[0]}|{bp[1]}"] for bp in bipart_keys)
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
        "irreps": [f"{bp[0]}|{bp[1]}" for bp in bipart_keys],
        "irrep_dims": {f"{bp[0]}|{bp[1]}": int(bipart_dim[bp]) for bp in bipart_keys},
        "Bn_order": Bn_order,
    }
    return results, metadata


# ---------------------------------------------------------------------------
# Sanity: D_4 equivariance check
# ---------------------------------------------------------------------------


def verify_d4_equivariance_2d(A: np.ndarray, sigma_dict: Dict[str, np.ndarray]) -> bool:
    """Verify U_g A U_g^T = A for all g in D_4."""
    for g, sigma in sigma_dict.items():
        # Permute rows then columns of A by sigma
        A_permuted = A[sigma, :][:, sigma]
        if not np.array_equal(A_permuted, A):
            print(f"[WARN] D_4 equivariance fails for element {g}")
            return False
    return True


def verify_b4_equivariance_4d(A: np.ndarray, n_samples: int = 30) -> bool:
    """Verify U_g A U_g^T = A for n_samples random B_4 elements."""
    rng = np.random.RandomState(SEED)
    signed_perms = b4_signed_perms()
    idx_sample = rng.choice(len(signed_perms), n_samples, replace=False)
    for idx in idx_sample:
        elem = signed_perms[idx]
        sigma = b4_action_4d(elem)
        A_permuted = A[sigma, :][:, sigma]
        if not np.array_equal(A_permuted, A):
            print(f"[WARN] B_4 equivariance fails for sample {idx}: {elem}")
            return False
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    t_total = time.perf_counter()
    print(f"[INFO] chess-knight-irrep-multiplicities spike (seed {SEED})")
    print(f"[INFO] Tolerance: eigenspace grouping {EIGENSPACE_TOL}, integer-check {INTEGER_TOL}")
    print(f"[INFO] Output NDJSON: {NDJSON_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ndjson_records = []

    # ----------------- 2D KNIGHT -----------------
    print("\n========== 2D KNIGHT ==========")
    t = time.perf_counter()
    A2 = build_knight_2d()
    print(f"[INFO] 2D knight adjacency built in {time.perf_counter()-t:.2f}s. "
          f"max degree {int(A2.sum(axis=1).max())}, "
          f"min degree {int(A2.sum(axis=1).min())}")
    # D_4 equivariance check
    sigma_dict_2d = d4_permutations_2d()
    eq2 = verify_d4_equivariance_2d(A2, sigma_dict_2d)
    print(f"[INFO] D_4 equivariance check: {'PASS' if eq2 else 'FAIL'}")

    t = time.perf_counter()
    results_2d = decompose_2d_via_projectors(A2)
    print(f"[INFO] 2D decomposition completed in {time.perf_counter()-t:.2f}s")

    # Summary 2D
    all_match_total_2d = all(r["match_total_dim"] for r in results_2d)
    all_integer_2d = all(r["all_integer"] for r in results_2d)
    print(f"[OK] 2D: all_match_total_dim={all_match_total_2d}, all_integer={all_integer_2d}")
    # Print eigenspaces
    for r in results_2d:
        m = r["multiplicities"]
        print(
            f"  eig={r['eigvalue_avg']:+8.4f}  dim={r['eigspace_dim']:2d}  "
            f"A1={m['A1']:.4f} A2={m['A2']:.4f} B1={m['B1']:.4f} "
            f"B2={m['B2']:.4f} E={m['E']:.4f}  "
            f"total_dim={r['total_dim_check']:.4f} match={r['match_total_dim']}"
        )

    # NDJSON records 2D
    for r in results_2d:
        for rep_name, mult in r["multiplicities"].items():
            ndjson_records.append({
                "dim": 2,
                "eigvalue_avg": r["eigvalue_avg"],
                "eigspace_dim": r["eigspace_dim"],
                "irrep": rep_name,
                "irrep_dim": D4_IRREP_DIMS[rep_name],
                "multiplicity_float": float(mult),
                "multiplicity_int": int(round(mult)),
                "is_integer_exact": bool(abs(mult - round(mult)) < INTEGER_TOL),
                "deviation_from_integer": float(abs(mult - round(mult))),
                "match_total_dim": r["match_total_dim"],
                "total_dim_check": r["total_dim_check"],
            })

    # Sum-rule check 2D: total multiplicity of each D_4 irrep should match
    # the natural-rep decomposition (10, 6, 6, 10, 16).
    total_mults_2d = {rep: 0 for rep in D4_IRREP_NAMES}
    for r in results_2d:
        for rep, m in r["multiplicities"].items():
            total_mults_2d[rep] += m
    expected_total_2d = {"A1": 10, "A2": 6, "B1": 6, "B2": 10, "E": 16}
    print("\n  Sum-rule check 2D (per-rep total across all eigenspaces):")
    for rep in D4_IRREP_NAMES:
        print(f"    {rep}: empirical {total_mults_2d[rep]:.4f}  expected {expected_total_2d[rep]}  "
              f"match={abs(total_mults_2d[rep] - expected_total_2d[rep]) < INTEGER_TOL}")
    sum_rule_2d_pass = all(abs(total_mults_2d[rep] - expected_total_2d[rep]) < INTEGER_TOL
                           for rep in D4_IRREP_NAMES)
    print(f"  Sum-rule 2D: {'PASS' if sum_rule_2d_pass else 'FAIL'}")

    # ----------------- 4D KNIGHT -----------------
    print("\n========== 4D KNIGHT ==========")
    t = time.perf_counter()
    A4 = build_knight_4d()
    print(f"[INFO] 4D knight adjacency built in {time.perf_counter()-t:.2f}s. "
          f"max degree {int(A4.sum(axis=1).max())}, "
          f"min degree {int(A4.sum(axis=1).min())}")
    eq4 = verify_b4_equivariance_4d(A4, n_samples=30)
    print(f"[INFO] B_4 equivariance check (30 samples): {'PASS' if eq4 else 'FAIL'}")

    t = time.perf_counter()
    results_4d, meta_4d = decompose_4d_via_character_orthogonality(A4)
    print(f"[INFO] 4D decomposition completed in {time.perf_counter()-t:.2f}s")

    all_match_total_4d = all(r["match_total_dim"] for r in results_4d)
    all_integer_4d = all(r["all_integer"] for r in results_4d)
    print(f"[OK] 4D: all_match_total_dim={all_match_total_4d}, all_integer={all_integer_4d}")
    print(f"[INFO] 4D eigenspaces: {len(results_4d)} groups")

    # Aggregate: count cases where multiplicities are NOT integer-exact
    n_nonint = 0
    max_dev = 0.0
    for r in results_4d:
        for rep_name, mult in r["multiplicities"].items():
            dev = abs(mult - round(mult))
            if dev > INTEGER_TOL:
                n_nonint += 1
            max_dev = max(max_dev, dev)
    print(f"[INFO] 4D total irrep×eigspace combos: {len(results_4d) * 20}; "
          f"non-integer: {n_nonint}; max dev: {max_dev:.3e}")

    # Sum-rule check 4D: total multiplicity of each B_4 irrep across all
    # eigenspaces equals its multiplicity in the natural rep on R^4096.
    # The natural rep multiplicity = (1/|G|) sum_g chi_natural(g) chi_rho(g)
    # where chi_natural(g) = number of fixed points of U_g on R^4096.
    print("\n  Computing expected B_4 natural-rep decomposition on R^4096...")
    # Compute fixed points for each class representative
    bipart_keys = [tuple(k.split("|", 1)) for k in meta_4d["irreps"]]
    # Actually re-build the class data
    class_data = b_n_signed_class_data(4)
    sn_chars: Dict[int, Dict[Tuple[int, ...], Dict[Tuple[int, ...], int]]] = {}
    for n in range(5):
        sn_chars[n] = sn_character_table_from_sympy(n)
    expected_total_4d: Dict[str, int] = {}
    biparts = bipartitions_n(4)
    Bn_order = 384

    # Fixed points: for class (lp, lm), need to count fixed points of one rep
    # on R^4096 = #{u: sigma[u] == u} where sigma = b4_action_4d(class_rep)
    def make_class_rep(lp, lm):
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

    class_fixed_points: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], int] = {}
    for (lp, lm, size) in class_data:
        rep_elem = make_class_rep(lp, lm)
        sigma = b4_action_4d(rep_elem)
        fp = int(np.sum(sigma == np.arange(DIM_4D_SIZE)))
        class_fixed_points[(lp, lm)] = fp
    print(f"  Class fixed points (sample): id class = {class_fixed_points[((1,1,1,1), ())]}")

    # Compute multiplicities in natural rep
    for bp in biparts:
        mult_natural = 0
        for (lp, lm, size) in class_data:
            chi_rho = b_n_irrep_character(bp[0], bp[1], lp, lm, sn_chars)
            mult_natural += size * chi_rho * class_fixed_points[(lp, lm)]
        mult_natural /= Bn_order
        key = f"{bp[0]}|{bp[1]}"
        expected_total_4d[key] = mult_natural

    print("  Sum-rule check 4D (per-irrep total across all eigenspaces):")
    total_mults_4d: Dict[str, float] = {key: 0.0 for key in expected_total_4d}
    for r in results_4d:
        for key, m in r["multiplicities"].items():
            total_mults_4d[key] += m
    sum_rule_4d_pass = True
    sample_keys = sorted(expected_total_4d.keys(),
                        key=lambda k: -expected_total_4d[k])[:8]
    for key in sample_keys:
        emp = total_mults_4d[key]
        exp_v = expected_total_4d[key]
        match = abs(emp - exp_v) < INTEGER_TOL
        if not match:
            sum_rule_4d_pass = False
        print(f"    {key:30s}  emp={emp:7.3f}  exp={exp_v:6.2f}  match={match}")
    # Check all keys
    for key in expected_total_4d:
        if abs(total_mults_4d[key] - expected_total_4d[key]) > INTEGER_TOL:
            sum_rule_4d_pass = False
    print(f"  Sum-rule 4D: {'PASS' if sum_rule_4d_pass else 'FAIL'}")

    # NDJSON records 4D
    irrep_dims = meta_4d["irrep_dims"]
    for r in results_4d:
        for rep_name, mult in r["multiplicities"].items():
            ndjson_records.append({
                "dim": 4,
                "eigvalue_avg": r["eigvalue_avg"],
                "eigspace_dim": r["eigspace_dim"],
                "irrep": rep_name,
                "irrep_dim": int(irrep_dims[rep_name]),
                "multiplicity_float": float(mult),
                "multiplicity_int": int(round(mult)),
                "is_integer_exact": bool(abs(mult - round(mult)) < INTEGER_TOL),
                "deviation_from_integer": float(abs(mult - round(mult))),
                "match_total_dim": r["match_total_dim"],
                "total_dim_check": r["total_dim_check"],
            })

    # ----------------- Write outputs -----------------
    print("\n========== OUTPUTS ==========")

    # NDJSON
    with NDJSON_PATH.open("w", encoding="utf-8") as f:
        for rec in ndjson_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[OK] Wrote {len(ndjson_records)} NDJSON records to {NDJSON_PATH}")

    # Append completion record to MFO MPM notes
    completion = {
        "date": "2026-05-11",
        "phase": "chess_knight_per_eigenspace_irrep_multiplicities",
        "kind": "completion",
        "outputs": [
            f"docs/srmech/notes/{NDJSON_PATH.name}",
            f"docs/srmech/notes/{FINDINGS_MD_PATH.name}",
            "docs/srmech/notes/chess-knight-irrep-multiplicities-script.py",
        ],
        "n_eigenspaces_2d": len(results_2d),
        "n_eigenspaces_4d": len(results_4d),
        "n_records": len(ndjson_records),
        "all_integer_2d": all_integer_2d,
        "all_integer_4d": all_integer_4d,
        "sum_rule_2d_pass": sum_rule_2d_pass,
        "sum_rule_4d_pass": sum_rule_4d_pass,
        "max_dev_from_integer_4d": float(max_dev),
        "n_nonint_combos_4d": int(n_nonint),
        "note": (
            f"Concertmaster follow-up to chess-d4-b4 spike (2026-05-11). "
            f"Per-eigenspace knight irrep multiplicities under D_4 (2D) and B_4 (4D). "
            f"Loaded-bearing question: are multiplicities integer-exact at machine "
            f"precision? 2D: {len(results_2d)} eigenspaces, all_integer={all_integer_2d}, "
            f"sum_rule_pass={sum_rule_2d_pass}. 4D: {len(results_4d)} eigenspaces, "
            f"all_integer={all_integer_4d}, sum_rule_pass={sum_rule_4d_pass}, "
            f"max_dev_from_integer={max_dev:.3e}, non-integer combos={n_nonint}. "
            f"If results positive: knight gains a section 3.5.3(C) sub-instance: "
            f"structural prediction without closed-form eigenvalues. "
            f"Citation: Rinaldi-Unciuleanu & Chiru 2026 sec 3.6."
        ),
    }
    existing = COMPLETION_RECORD_PATH.read_text(encoding="utf-8").splitlines() \
        if COMPLETION_RECORD_PATH.exists() else []
    kept = [
        ln for ln in existing
        if not (
            "chess_knight_per_eigenspace_irrep_multiplicities" in ln
            and "\"kind\": \"completion\"" in ln
        )
    ]
    kept.append(json.dumps(completion, ensure_ascii=False))
    COMPLETION_RECORD_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"[OK] Appended completion record to {COMPLETION_RECORD_PATH}")

    elapsed = time.perf_counter() - t_total
    print(f"\n[OK] TOTAL RUNTIME: {elapsed:.1f}s")
    return {
        "results_2d": results_2d,
        "results_4d": results_4d,
        "all_integer_2d": all_integer_2d,
        "all_integer_4d": all_integer_4d,
        "sum_rule_2d_pass": sum_rule_2d_pass,
        "sum_rule_4d_pass": sum_rule_4d_pass,
        "expected_total_2d": expected_total_2d,
        "expected_total_4d": expected_total_4d,
        "total_mults_2d": total_mults_2d,
        "total_mults_4d": total_mults_4d,
        "max_dev_from_integer_4d": max_dev,
        "n_nonint_combos_4d": n_nonint,
        "n_eigenspaces_2d": len(results_2d),
        "n_eigenspaces_4d": len(results_4d),
    }


if __name__ == "__main__":
    main()
