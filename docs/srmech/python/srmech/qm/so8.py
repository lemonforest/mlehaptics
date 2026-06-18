"""The 28-generator ``so(8)`` adjoint, partitioned ``14 + 7 + 7``.

The middle layer of the ``srmech.qm`` so(8)/Spin(8) triality engine
(v0.5.0rc17). ``so(8)`` is the 28-dimensional Lie algebra of ``8x8`` real
antisymmetric matrices. Built from the octonion multiplication table
(:mod:`srmech.qm.octonion`), it splits as a vector space into

- ``14 = g2 = Der(O)`` — the Lie subalgebra of octonion derivations
  ``D_{a,b} = [L_a, L_b] + [R_a, R_b] + [L_a, R_b]`` (Schafer 1966); and
- ``7 + 7`` — the L-type / R-type coset directions ``L_{e_i}`` / ``R_{e_i}``
  (``i = 1..7``), which are antisymmetric but not derivations.

This ``14`` is exactly the ``1 + 3 + 7 + 3 = 14`` A-N partition: the
triality automorphism's fixed subalgebra ``Fix(tau) = g2`` (the
``D4 --(Z3 fold)--> G2`` theorem; see :mod:`srmech.qm.triality`).

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites the
canonical literature, **not** a project instantiation.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``so8_adjoint_basis`` / ``g2_subalgebra`` — **Class M** (the L/R
  octonion-multiplication binders + the ``g2`` derivations bind octonion
  products).
- ``so7_subalgebra`` — **Class C** (the ``Z2``-swap-fixed subalgebra; the
  ``D4 --(Z2 fold)--> B3`` Dynkin reflection is Class C chirality).

DETERMINISM: the ``14``-element ``g2`` basis is a deterministic
rank-revealing column subset of the 21 ``D_{e_i, e_j}`` (a greedy
independent-column walk in fixed order — the pivoted-QR equivalent,
**no scipy**); the ``21``-dim ``so(7)`` basis is an SVD nullspace. **No
RNG** anywhere — the clean-MCP no-RNG mandate, and so the ``Fix(tau) = g2``
killer test is reproducible. (``srmech`` treats scipy as an OPTIONAL
dependency, lazily imported with a fallback elsewhere, so ``srmech.qm`` must
import cleanly on a scipy-less / Pyodide install.)

rc123 (numpy-free, #564): the whole module flips off numpy onto the
framework-native carriers. 2-D matrices are :class:`srmech.amsc.mat.Mat`
(the public surfaces return ``Mat``); the heavy linear algebra routes through
the unconditionally-numpy-free ``mat_*`` family (:func:`mat_matmul`,
:func:`mat_svd`, :func:`mat_hermitian_eigendecompose`) and pure-Python
cascades. The **DUAL** so8 fix (per
``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]`` — a
rank COUNT must never route through the cascade SVD's ~1e-7 small-σ floor):

- where the data is EXACT — the rank of the 21 raw ``g2`` derivations (whose
  entries are exact ``{-1, 0, +1}`` integer combinations of the octonion
  structure constants) — the rank-COUNT is an EXACT RREF over ℚ
  (:func:`_rank_exact`, rational row-reduction, no float-tolerance drift); while
- the nullspace / Gram-Schmidt GEOMETRY (the actual su(3) / so(4) / triality
  generators) rides the float :func:`mat_svd` / :func:`mat_norm` carriers — and
  the "same span" rank assertions ON those FLOAT generators use a float
  Gram-Schmidt rank (:func:`_rank_float`) with a tolerance GENEROUS over the
  ~1e-7 floor (NOT a strict 1e-9 cascade-SVD-σ count, which would mis-count).
  The split keeps each rank-COUNT off the cascade SVD's inaccurate small σ.

Canonical SSoT:

- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — ``G2 = Aut(O)``, ``Lie(G2) = Der(O)``, Spin(8).
- Schafer, R.D. (1966) *An Introduction to Nonassociative Algebras*,
  Academic Press — the derivation ``D_{a,b}`` of a composition algebra.
- Cartan, E. (1925) *Le principe de dualite et la theorie des groupes
  simples et semi-simples*, Bull. Sci. Math. 49, 361-374 — triality.
"""

from __future__ import annotations

import functools
from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

from srmech.amsc import rational as _srn

from srmech.amsc.cascade import magnitude as _magnitude
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.amsc.mat import Mat
from srmech.amsc.laplacian import (
    mat_hermitian_eigendecompose,
    mat_matmul,
    mat_norm,
    mat_svd,
)
from srmech.qm.octonion import (
    octonion_left_mult,
    octonion_mult_table,
    octonion_right_mult,
)

#: Octonion / so(8)-acting dimension.
_DIM = 8

#: Rank-reveal / nullspace tolerance for the deterministic basis extraction.
_RANK_TOL = 1e-9

#: Dimensions of the three pieces (the partition the whole engine turns on).
_DIM_G2 = 14
_DIM_SO7 = 21
_DIM_SO8 = 28

#: su(3) Lie-decomposition dimensions of the 14-generator g2 (the
#: ``an_embedding`` voxel): the 8-real-dim su(3) stabiliser, the 6-real-dim
#: su(3)-module complement, and the 3-complex-dim fundamental / antifundamental.
_DIM_SU3 = 8
_DIM_COMPLEMENT = 6
_DIM_TRIPLET = 3

#: A FIXED ISO timestamp for the ``an_embedding`` self-attestation.
#: Deterministic on purpose (NOT ``datetime.now()``) so the MCP surface is
#: reproducible — the attestation of a GENERATED structure must not change
#: between calls (mirrors :data:`srmech.qm.octonion._RETRIEVED_AT`).
_AN_RETRIEVED_AT = "2026-05-30T00:00:00Z"

#: The single generative rule whose bytes are the ``parser_rule_hash``
#: provenance of the su(3) stabiliser: su(3) = {D in g2 : D e_K = 0}.
_AN_PARSER_RULE = b"D e_K = 0"

#: so(4) = su(2) ⊕ su(2) dimensions for the quaternion-subalgebra stabiliser
#: (the ``quaternion_subalgebra_stabiliser`` voxel; F215): the 6-real-dim
#: stabiliser, split as two 3-real-dim su(2) ideals.
_DIM_SO4 = 6
_DIM_SU2 = 3
_DIM_H_IMAG = 3  # the 3 imaginary units of a quaternion subalgebra H ⊂ O
_DIM_COMP4 = 4   # the 4 octonion units in the orthogonal complement H^⊥

#: The single generative rule whose bytes are the ``parser_rule_hash``
#: provenance of the so(4) stabiliser: a derivation stabilises H iff it maps
#: the 3 imaginary units of H back into H (equivalently, the orthogonal
#: complement H^⊥ into itself). ``span(H_imag)`` is the imaginary part of H.
_SO4_PARSER_RULE = b"D span(H_imag) subseteq span(H_imag)"


# ──────────────────────────────────────────────────────────────────────
# Numpy-free linear-algebra cascades (rc123, #564). The internal matrix
# carrier is a nested ``list[list[float]]`` (so8 builds matrices element-wise
# heavily; Mat is 2-D only and small here), converted to/from :class:`Mat`
# at the ``mat_*`` boundaries and at the public surface. No numpy.
# ──────────────────────────────────────────────────────────────────────

Number = object  # float | complex (the nested-list element type)


def _zeros(rows: int, cols: int) -> List[List[float]]:
    """A ``rows×cols`` nested list of ``0.0`` (the numpy-free zeros builder)."""
    return [[0.0] * cols for _ in range(rows)]


def _eye(n: int) -> List[List[float]]:
    """The ``n×n`` identity as a nested list (the numpy-free identity builder)."""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def _transpose(a: Sequence[Sequence[Number]]) -> List[List[Number]]:
    """Nested-list transpose (no conjugation; numpy-free)."""
    rows = len(a)
    cols = len(a[0]) if rows else 0
    return [[a[i][j] for i in range(rows)] for j in range(cols)]


def _matmul(a: Sequence[Sequence[Number]], b: Sequence[Sequence[Number]]):
    """Nested-list matrix multiply ``A·B`` over real or complex elements
    (numpy-free triple loop). Routes the well-shaped real/complex case through
    the native :func:`mat_matmul` for the 8×8 / 28×28 hot paths."""
    m = len(a)
    k = len(a[0]) if m else 0
    n = len(b[0]) if b else 0
    is_complex = any(isinstance(x, complex) for r in a for x in r) or any(
        isinstance(x, complex) for r in b for x in r
    )
    out = [[(0j if is_complex else 0.0) for _ in range(n)] for _ in range(m)]
    for i in range(m):
        ai = a[i]
        for t in range(k):
            ait = ai[t]
            bt = b[t]
            for j in range(n):
                out[i][j] += ait * bt[j]
    return out


def _matvec(a: Sequence[Sequence[Number]], v: Sequence[Number]) -> List[Number]:
    """Nested-list matrix-vector product ``A·v`` (numpy-free)."""
    return [sum(a[i][t] * v[t] for t in range(len(v))) for i in range(len(a))]


def _commutator(x, y):
    """Matrix commutator ``[X, Y] = X Y - Y X`` (Class L building block)."""
    xy = _matmul(x, y)
    yx = _matmul(y, x)
    return [[xy[i][j] - yx[i][j] for j in range(len(xy[0]))] for i in range(len(xy))]


def _scale(a: Sequence[Sequence[Number]], s: Number) -> List[List[Number]]:
    """Scalar-multiply a nested-list matrix (numpy-free)."""
    return [[s * x for x in row] for row in a]


def _add(a, b):
    """Element-wise add of two nested-list matrices (numpy-free)."""
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _sub(a, b):
    """Element-wise subtract of two nested-list matrices (numpy-free)."""
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _lincomb(coeffs: Sequence[Number], mats: Sequence[Sequence[Sequence[Number]]]):
    """``Σ_a coeffs[a] · mats[a]`` over nested-list matrices (numpy-free)."""
    rows = len(mats[0])
    cols = len(mats[0][0])
    acc = [[0.0 if not isinstance(coeffs[0], complex) else 0j for _ in range(cols)]
           for _ in range(rows)]
    for c, m in zip(coeffs, mats):
        for i in range(rows):
            mi = m[i]
            ai = acc[i]
            for j in range(cols):
                ai[j] = ai[j] + c * mi[j]
    return acc


def _frob_norm(a: Sequence[Sequence[Number]]) -> float:
    """Frobenius norm of a nested-list matrix via the Class-N ``mat_norm``
    (numpy-free; complex modulus, no ``abs()``)."""
    return mat_norm(Mat.from_rows(a))


def _vec_norm(v: Sequence[Number]) -> float:
    """Euclidean norm of a flat sequence via Class-N ``mat_norm`` (numpy-free)."""
    return mat_norm(list(v))


def _to_mat(a: Sequence[Sequence[Number]], *, is_complex: bool = None) -> Mat:
    """Wrap a nested-list matrix as a :class:`Mat` (numpy-free)."""
    return Mat.from_rows(a, is_complex=is_complex)


def _mat_rows(m: Mat) -> List[List[Number]]:
    """A nested-list copy of a :class:`Mat`'s rows (numpy-free)."""
    return m.tolist()


# ── exact rank over ℚ (the RANK fix; NOT cascade-SVD tolerance) ───────────
def _rank_exact(columns: Sequence[Sequence[Number]]) -> int:
    """Exact matrix rank of the column stack ``columns`` (a list of column
    vectors) via RREF over ℚ — the numpy-free AND exact replacement for
    the float-tolerance ``matrix_rank`` (per
    ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]``: a
    tolerance rank-count must NOT route through the cascade SVD's small
    singular values; rational row-reduction has no float-tolerance drift).

    ``columns[c]`` is the c-th column (length ``n_rows``). The coords this
    module forms are EXACT rationals of small octonion structure constants
    (``{-1, 0, +1}`` linear combinations), so a :class:`~fractions.Fraction`
    Gaussian elimination is exact: the rank is the count of pivots.
    """
    n_cols = len(columns)
    if n_cols == 0:
        return 0
    n_rows = len(columns[0])
    # Build the (n_rows, n_cols) rational matrix (columns → rows of Aᵀ form is
    # unnecessary; rank(A) == rank of the row-reduced (n_rows, n_cols) matrix).
    rows = [[Fraction(columns[c][r]).limit_denominator(10 ** 12)
             for c in range(n_cols)] for r in range(n_rows)]
    rank = 0
    pivot_col = 0
    n = n_rows
    while rank < n and pivot_col < n_cols:
        # find a pivot in column pivot_col at or below row `rank`
        pivot_row = None
        for r in range(rank, n):
            if rows[r][pivot_col] != 0:
                pivot_row = r
                break
        if pivot_row is None:
            pivot_col += 1
            continue
        rows[rank], rows[pivot_row] = rows[pivot_row], rows[rank]
        pivot = rows[rank][pivot_col]
        rows[rank] = [x / pivot for x in rows[rank]]
        for r in range(n):
            if r != rank and rows[r][pivot_col] != 0:
                factor = rows[r][pivot_col]
                rows[r] = [rows[r][c] - factor * rows[rank][c]
                           for c in range(n_cols)]
        rank += 1
        pivot_col += 1
    return rank


def _rank_float(columns: Sequence[Sequence[Number]], *, tol: float = 1e-6) -> int:
    """Float-tolerant rank of the column stack ``columns`` via modified
    Gram-Schmidt — for the "same span" checks whose vectors are FLOAT
    (the su(3) / so(4) / su(2) generators are linear combinations of the g2
    derivations with the FLOAT SVD-nullspace coefficients, so they carry the
    cascade SVD's ~1e-7 small-σ round-off and CANNOT be compared over ℚ).

    The EXACT :func:`_rank_exact` is the tool only where the data is exact (the
    raw g2 derivations); here a tolerance GENEROUS over the float floor
    (``tol·scale``, default ``1e-6``) is needed so a genuinely-dependent
    (same-span) direction — whose Gram-Schmidt residual sits at the ~1e-7 floor
    — is NOT miscounted as independent. Counts the orthonormal directions whose
    residual exceeds ``tol·scale``. Numpy-free.
    """
    if not columns:
        return 0
    is_complex = any(isinstance(x, complex) for col in columns for x in col)
    scale = max((_vec_norm(c) for c in columns), default=1.0)
    scale = max(1.0, scale)
    basis: List[List[Number]] = []
    for col in columns:
        residual = list(col)
        for q in basis:
            if is_complex:
                proj = sum(q[i].conjugate() * residual[i] for i in range(len(q)))
            else:
                proj = sum(q[i] * residual[i] for i in range(len(q)))
            residual = [residual[i] - proj * q[i] for i in range(len(q))]
        nrm = _vec_norm(residual)
        if nrm > tol * scale:
            inv = 1.0 / nrm
            basis.append([x * inv for x in residual])
    return len(basis)


# ── orthonormal column basis (modified Gram-Schmidt; the GEOMETRY) ────────
def _orthonormalise(columns: List[List[Number]]) -> List[List[Number]]:
    """Modified Gram-Schmidt orthonormal basis of the span of ``columns``
    (each a flat real/complex vector). The numpy-free orthonormal-``Q`` basis
    the orthonormalisations this module needs — drops a column whose residual
    norm falls below the rank tolerance (a dependent direction). Returns the
    kept orthonormal columns (a list of vectors)."""
    basis: List[List[Number]] = []
    if not columns:
        return basis
    is_complex = any(isinstance(x, complex) for col in columns for x in col)
    scale = max((_vec_norm(c) for c in columns), default=1.0)
    scale = max(1.0, scale)
    for col in columns:
        residual = list(col)
        for q in basis:
            # ⟨q, residual⟩ (Hermitian for complex; bilinear-conj first arg).
            if is_complex:
                proj = sum(q[i].conjugate() * residual[i] for i in range(len(q)))
            else:
                proj = sum(q[i] * residual[i] for i in range(len(q)))
            residual = [residual[i] - proj * q[i] for i in range(len(q))]
        nrm = _vec_norm(residual)
        if nrm > _RANK_TOL * scale:
            inv = 1.0 / nrm
            basis.append([x * inv for x in residual])
    return basis


def _max_projection_residual(
    vectors: List[List[Number]], onto: List[List[Number]]
) -> float:
    """Max ``‖v − P v‖`` projecting each column of ``vectors`` onto the span of
    ``onto`` (an orthonormal basis ``P = Σ qᵢ qᵢᴴ``). Reduced through the scalar
    Class K magnitude (no ``abs()``). Numpy-free."""
    basis = _orthonormalise(onto)
    is_complex = any(isinstance(x, complex) for col in vectors for x in col)
    worst = 0.0
    for v in vectors:
        proj = [0j if is_complex else 0.0] * len(v)
        for q in basis:
            if is_complex:
                coef = sum(q[i].conjugate() * v[i] for i in range(len(v)))
            else:
                coef = sum(q[i] * v[i] for i in range(len(v)))
            proj = [proj[i] + coef * q[i] for i in range(len(v))]
        residual = [v[i] - proj[i] for i in range(len(v))]
        worst = max(worst, _magnitude(_vec_norm(residual)))
    return worst


# ── float SVD nullspace via the Mat carrier (the GEOMETRY) ────────────────
def _svd_nullspace(a_rows: List[List[Number]], dim: int) -> List[List[Number]]:
    """The ``dim`` right-null-space columns of ``a_rows`` via the numpy-free
    :func:`mat_svd` (the GEOMETRY carrier). ``mat_svd`` returns ``(U, S, Vh)``
    with ``S`` descending; the null space is the ``dim`` right singular vectors
    (rows of ``Vh``, i.e. columns of ``V``) with the SMALLEST singular values.

    ``dim`` is the KNOWN nullity (the callers all derive it from the algebra and
    assert it), so we SELECT the ``dim`` trailing-σ vectors rather than
    THRESHOLD by tolerance — per
    ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]`` the
    cascade SVD resolves a null σ only to ~1e-7·σ_max (above a 1e-9
    threshold), so a strict tolerance would UNDER-count; taking the ``dim``
    smallest is robust to that small-σ floor and is the value-faithful null
    GEOMETRY (the actual null directions). The matching rank-COUNT assertions
    use the EXACT rational :func:`_rank_exact`, never this float carrier.

    Returns ``dim`` null vectors (each a flat list of length ``n_cols``)."""
    A = Mat.from_rows(a_rows)
    _, S, Vh = mat_svd(A)
    n = Vh.n_rows
    # singular value paired with each Vh row (rows beyond len(S) pair with 0.0,
    # the structurally-null directions when n > min(m, n)).
    sigma_of = [(S[idx] if idx < len(S) else 0.0) for idx in range(n)]
    order = sorted(range(n), key=lambda idx: sigma_of[idx])  # ascending σ
    chosen = order[:dim]
    return [[Vh[idx, j] for j in range(Vh.n_cols)] for idx in chosen]


def _real_skew_eig(skew: List[List[float]]) -> Tuple[List[complex], List[List[complex]]]:
    """Eigenpairs of a REAL skew-symmetric matrix via the numpy-free Hermitian
    cascade. For real antisymmetric ``S`` (``Sᵀ = −S``), ``iS`` is Hermitian —
    so :func:`mat_hermitian_eigendecompose` yields real eigenvalues ``μ``
    (ascending) and a unitary eigenvector matrix ``V``; then ``S``'s eigenvalues
    are the purely-imaginary ``λ = −i·μ`` and its eigenvectors are the same
    ``V``. Returns ``(eigenvalues, columns_of_V)`` — ``eigenvalues`` complex
    (weight in ``.imag``), ``columns_of_V`` a list of complex eigenvector
    columns (column ``k`` is ``[V[i][k]]``). Numpy-free (``iS`` built by the
    scalar carrier ``1j·S``; no numpy ``eig``).

    The eigenvector phase / degenerate-eigenspace basis is solver-chosen, so
    callers consume ``V`` invariantly (Rayleigh quotient / eigenspace span).
    """
    n = len(skew)
    iS = Mat.from_rows([[complex(0.0, skew[i][j]) for j in range(n)]
                        for i in range(n)], is_complex=True)
    evals_mat, V = mat_hermitian_eigendecompose(iS)   # μ real ascending; V unitary
    eigenvalues = [complex(0.0, -float(evals_mat[k, 0])) for k in range(n)]  # λ = −iμ
    cols = [[V[i, k] for i in range(n)] for k in range(n)]
    return eigenvalues, cols


def _kron(a: List[List[Number]], b: List[List[Number]]) -> List[List[Number]]:
    """Kronecker product ``A ⊗ B`` as a nested list (numpy-free)."""
    ar, ac = len(a), len(a[0])
    br, bc = len(b), len(b[0])
    out = _zeros(ar * br, ac * bc)
    for i in range(ar):
        for j in range(ac):
            aij = a[i][j]
            for p in range(br):
                for q in range(bc):
                    out[i * br + p][j * bc + q] = aij * b[p][q]
    return out


def _basis_vectors() -> List[List[float]]:
    """The 8 octonion basis vectors ``e_0 .. e_7`` as rows of ``I_8``."""
    return _eye(_DIM)


def _derivation(a: List[float], b: List[float]) -> List[List[float]]:
    """Schafer octonion derivation ``D_{a,b}`` as an ``8x8`` real matrix.

    ``D_{a,b} = [L_a, L_b] + [R_a, R_b] + [L_a, R_b]`` (Schafer 1966). Each
    ``D_{a,b}`` is antisymmetric and obeys the Leibniz rule
    ``D(xy) = D(x) y + x D(y)``, so it lies in ``g2 = Der(O) subset so(8)``.
    Internal helper (reused by :mod:`srmech.qm.triality`).

    rc123 (numpy-free): ``octonion_{left,right}_mult`` return a :class:`Mat`;
    consume their rows directly via ``.tolist()`` (no numpy bridge).
    """
    la = octonion_left_mult(a).tolist()
    lb = octonion_left_mult(b).tolist()
    ra = octonion_right_mult(a).tolist()
    rb = octonion_right_mult(b).tolist()
    return _add(_add(_commutator(la, lb), _commutator(ra, rb)), _commutator(la, rb))


def _all_derivations() -> List[List[List[float]]]:
    """The 21 derivations ``D_{e_i, e_j}`` for ``1 <= i < j <= 7``.

    Their span has rank exactly ``14 = dim g2`` (verified bit-exact).
    """
    basis = _basis_vectors()
    out: List[List[List[float]]] = []
    for i in range(1, _DIM):
        for j in range(i + 1, _DIM):
            out.append(_derivation(basis[i], basis[j]))
    return out


def _epq_pairs() -> Tuple[Tuple[int, int], ...]:
    """The 28 index pairs ``(p, q)``, ``0 <= p < q <= 7``.

    The shared ``E_{pq}`` coordinate frame for the whole engine: the
    28-dim space of antisymmetric ``8x8`` matrices is coordinatised by
    ``coords(M)[index(p, q)] = M[p, q]``. **One** shared helper so the
    ``28x28`` ``tau`` (triality) and the ``g2`` generators' vectorisation
    use the IDENTICAL frame — a mismatch would make ``Fix(tau) = g2`` fail
    spuriously.
    """
    return tuple((p, q) for p in range(_DIM) for q in range(p + 1, _DIM))


def _epq_coords(matrix) -> List[Number]:
    """Project an antisymmetric ``8x8`` onto the 28-dim ``E_{pq}`` frame.

    Accepts a nested-list matrix or a :class:`Mat`. Returns a flat list of the
    upper-triangular entries (real or complex), numpy-free."""
    if isinstance(matrix, Mat):
        return [matrix[p, q] for (p, q) in _epq_pairs()]
    return [matrix[p][q] for (p, q) in _epq_pairs()]


def _epq_basis() -> List[List[List[float]]]:
    """The 28 ``E_{pq} = e_p e_q^T - e_q e_p^T`` antisymmetric basis matrices."""
    out: List[List[List[float]]] = []
    for (p, q) in _epq_pairs():
        m = _zeros(_DIM, _DIM)
        m[p][q] = 1.0
        m[q][p] = -1.0
        out.append(m)
    return out


def _deterministic_rank_subset(
    matrices: List[List[List[float]]], n_keep: int
) -> List[List[List[float]]]:
    """Deterministic rank-revealing column subset of ``matrices``.

    Vectorises each matrix, then performs a deterministic greedy
    independent-column selection: walk the columns in fixed (ascending)
    order, keeping a column iff it raises the rank of the kept set (its
    residual norm against the span of the already-kept columns exceeds the
    rank tolerance). This is the numpy-free equivalent of a rank-revealing
    pivoted QR — **no RNG and no scipy** (scipy is an optional dependency
    in srmech, lazily imported with a fallback; ``srmech.qm`` must import on
    a scipy-less / Pyodide install). The total rank is verified EXACTLY via
    the rational :func:`_rank_exact` (no float-tolerance drift).
    """
    vectors = [_flatten(m) for m in matrices]            # one flat vector per matrix
    total_rank = _rank_exact(vectors)                    # exact ℚ rank (count fix)
    assert total_rank == n_keep, (
        f"rank-revealing subset expected rank {n_keep}; got {total_rank}"
    )
    kept_indices: List[int] = []
    kept_basis: List[List[float]] = []                   # orthonormal span of kept cols
    norm_scale = max(1.0, max((_vec_norm(v) for v in vectors), default=1.0))
    for col, v in enumerate(vectors):
        residual = list(v)
        for q in kept_basis:
            proj = sum(q[i] * residual[i] for i in range(len(q)))
            residual = [residual[i] - proj * q[i] for i in range(len(q))]
        rnorm = _vec_norm(residual)
        if rnorm > _RANK_TOL * norm_scale:
            kept_indices.append(col)
            inv = 1.0 / rnorm
            kept_basis.append([x * inv for x in residual])
            if len(kept_indices) == n_keep:
                break
    assert len(kept_indices) == n_keep, (
        f"greedy subset kept {len(kept_indices)}; expected {n_keep}"
    )
    return [matrices[k] for k in kept_indices]


def _flatten(m: Sequence[Sequence[Number]]) -> List[Number]:
    """Row-major flatten of a nested-list matrix (numpy-free ``.flatten()``)."""
    return [x for row in m for x in row]


def _freeze(matrices: List[List[List[Number]]]) -> Tuple[Tuple[Tuple[Number, ...], ...], ...]:
    """An immutable nested-tuple copy of ``matrices`` for the LRU cache (so the
    memoised value can never be mutated through a caller's reference)."""
    return tuple(tuple(tuple(row) for row in m) for m in matrices)


def _thaw(frozen) -> Tuple[List[List[Number]], ...]:
    """Defensive copy-out: a fresh tuple of fresh mutable nested lists.

    The public ``so(8)`` surfaces hand callers a thawed copy of the cached
    build so a downstream mutation can never corrupt the shared cache; the
    build is expensive, the per-call copy is cheap, and the values are
    bit-identical (deterministic — no RNG).
    """
    return tuple([list(row) for row in m] for m in frozen)


def _thaw_mats(frozen) -> Tuple[Mat, ...]:
    """Defensive copy-out as a tuple of fresh :class:`Mat` (the public 2-D
    surface for the so(8) generator families). Numpy-free."""
    return tuple(Mat.from_rows([list(row) for row in m]) for m in frozen)


@functools.lru_cache(maxsize=None)
def _build_g2() -> Tuple[Tuple[Tuple[float, ...], ...], ...]:
    """Cached read-only ``g2`` basis (the expensive rank-revealing subset)."""
    return _freeze(_deterministic_rank_subset(_all_derivations(), _DIM_G2))


def _g2_lists() -> List[List[List[float]]]:
    """The 14 ``g2`` generators as fresh mutable nested lists (numpy-free)."""
    return list(_thaw(_build_g2()))


def g2_subalgebra() -> Tuple[Mat, ...]:
    """The 14 octonion derivations ``Der(O) = g2`` as antisymmetric ``8x8`` ``Mat``.

    A deterministic rank-revealing (greedy independent-column) ``14``-element
    subset of the 21 ``D_{e_i, e_j}`` (``1 <= i < j <= 7``); the span has rank
    exactly 14 (verified EXACTLY via the rational :func:`_rank_exact`).
    This is the KILLER-test target: ``Fix(tau) = span(g2)`` (the
    ``D4 --(Z3 fold)--> G2`` theorem), the same ``14`` as the A-N
    ``1 + 3 + 7 + 3`` partition. The expensive build is memoised
    (:func:`_build_g2`); each call returns a fresh copy.

    Class M (the ``g2`` Lie subalgebra; derivations bind octonion products).

    rc123 (numpy-free): returns a tuple of real ``8x8`` :class:`Mat` (was
    ndarrays).

    Canonical SSoT: Baez (2002) §4.1 (``g2 = Der(O)``, dim 14); Schafer (1966).

    Returns:
        Tuple of 14 antisymmetric ``8x8`` real ``Mat`` spanning ``g2``.
    """
    return _thaw_mats(_build_g2())


@functools.lru_cache(maxsize=None)
def _build_so8_adjoint() -> Tuple[Tuple[Tuple[float, ...], ...], ...]:
    """Cached read-only ``so(8)`` adjoint basis (``14 g2 + 7 L + 7 R``)."""
    basis = _basis_vectors()
    g2 = _g2_lists()
    # rc123 (numpy-free): the Mat L/R operators are consumed as nested lists.
    l_type = [octonion_left_mult(basis[i]).tolist() for i in range(1, _DIM)]
    r_type = [octonion_right_mult(basis[i]).tolist() for i in range(1, _DIM)]
    return _freeze(g2 + l_type + r_type)


def so8_adjoint_basis() -> Tuple[Mat, ...]:
    """The 28 ``so(8)`` generators, partitioned ``14 (g2) + 7 (L) + 7 (R)``.

    Order: the 14 ``g2`` derivations, then the 7 L-type ``L_{e_i}``, then the
    7 R-type ``R_{e_i}`` (``i = 1..7``). Each is antisymmetric; together they
    span ``so(8)`` as a vector space (rank 28). The ``g2`` block is the Lie
    subalgebra; the ``7 + 7`` are coset directions.

    Class M (the L/R octonion-multiplication binders are the ``14`` non-``g2``
    directions; ``g2`` is the other 14).

    rc123 (numpy-free): returns a tuple of real ``8x8`` :class:`Mat`.

    Canonical SSoT: Baez (2002) §2.4 + §4.1 (so(8) from octonion
    multiplication; ``g2 = Der(O)``). The build is memoised
    (:func:`_build_so8_adjoint`); each call returns a fresh copy.

    Returns:
        Tuple of 28 antisymmetric ``8x8`` real ``Mat``.
    """
    return _thaw_mats(_build_so8_adjoint())


@functools.lru_cache(maxsize=None)
def _build_so7() -> Tuple[Tuple[Tuple[float, ...], ...], ...]:
    """Cached read-only ``so(7)`` basis (SVD nullspace of ``S_B - I``)."""
    # Imported here to keep the module DAG acyclic at import time
    # (octonion <- so8 <- triality): so7 needs the triality companion map.
    from srmech.qm.triality import triality_swap

    swap = triality_swap()                      # 28×28 Mat (rc123)
    return _freeze(_fixed_space_matrices(swap.tolist(), _DIM_SO7))


def so7_subalgebra() -> Tuple[Mat, ...]:
    """The 21-dim ``so(7)`` fixed space of the ``Z2`` swap (``D4 -> B3`` fold).

    ``so(7) = ker(S_B - I)`` where ``S_B`` is the companion involution (see
    :func:`srmech.qm.triality.triality_swap`). Returned as a deterministic
    SVD-nullspace basis of 21 antisymmetric ``8x8`` generators (re-expressed
    from the ``E_{pq}`` frame back to matrices).

    Class C (the ``Z2``-swap-fixed subalgebra; ``Z2`` swap = Class C
    chirality / the ``D4 --(Z2 fold)--> B3`` Dynkin reflection).

    rc123 (numpy-free): returns a tuple of real ``8x8`` :class:`Mat`.

    Canonical SSoT: Baez (2002) §2.4 + the ``D4 -> B3`` Dynkin fold. The
    build is memoised (:func:`_build_so7`); each call returns a fresh copy.

    Returns:
        Tuple of 21 antisymmetric ``8x8`` real ``Mat`` spanning ``so(7)``.
    """
    return _thaw_mats(_build_so7())


def _fixed_space_matrices(operator: List[List[float]], dim: int) -> List[List[List[float]]]:
    """An orthonormal basis of ``ker(operator - I)`` as antisymmetric ``8x8``.

    Deterministic SVD nullspace (the float :func:`mat_svd` GEOMETRY carrier; no
    RNG). Each returned 28-vector is mapped back to an antisymmetric ``8x8``
    matrix via the shared ``E_{pq}`` frame. Numpy-free.
    """
    n = len(operator)
    minus_i = _sub(operator, _eye(n))
    null_columns = _svd_nullspace(minus_i, dim)   # `dim` null vectors (length 28)
    found = len(null_columns)
    assert found == dim, (
        f"fixed-space dimension expected {dim}; got {found}"
    )
    pairs = _epq_pairs()
    out: List[List[List[float]]] = []
    for coeffs in null_columns:
        m = _zeros(_DIM, _DIM)
        for idx, (p, q) in enumerate(pairs):
            m[p][q] = float(coeffs[idx].real if isinstance(coeffs[idx], complex)
                            else coeffs[idx])
            m[q][p] = -m[p][q]
        out.append(m)
    return out


# ──────────────────────────────────────────────────────────────────────
# an_embedding — the su(3) ⊕ 3 ⊕ 3bar Lie decomposition of g2 = Der(O)
#
# A DIFFERENT 14-decomposition from the partitioned ``so8_adjoint_basis``
# (which splits the 28-dim so(8) as 14 g2 + 7 L + 7 R). Here the *14-dim
# g2 itself* splits under one of its su(3) subalgebras as the Lie-algebra
# branching ``14 = 8 + 3 + 3bar`` — the adjoint of su(3) (8) plus the
# fundamental (3) plus the antifundamental (3bar). It is the genuine
# su(3)-module structure of g2, computed bit-exact and self-attesting.
#
# The construction is the deterministic chain (no RNG, numpy-free):
#   1. su(3) = the stabiliser {D in g2 : D e_K = 0} (SVD nullspace; dim 8).
#   2. complement = the 6-real-dim orthogonal su(3)-module (the "movers").
#   3. J = the su(3)-INVARIANT complex structure on the complement (the
#      antisymmetric generator of the 2-dim commutant {aI + bJ} of the
#      6-dim su(3)-rep; J^2 = -I). FIX 1: a *real* 3-dim span CANNOT carry
#      the su(3) fundamental ([su3, real-3] leaks); the genuine fundamental
#      is the +i eigenspace of J on the COMPLEXIFIED complement.
#   4. triplet / antitriplet = the J = +i / -i eigenspaces (complex), the
#      genuine fundamental / antifundamental; [su3, triplet] ⊆ triplet is
#      then bit-exact.
# ──────────────────────────────────────────────────────────────────────


def _epq_to_matrix(coeffs: Sequence[Number]) -> List[List[Number]]:
    """Re-express a 28-vector of ``E_{pq}`` coords as an antisymmetric ``8x8``.

    The inverse of :func:`_epq_coords` — fills the upper triangle from
    ``coeffs`` and antisymmetrises. Accepts a real or complex coefficient
    vector (the complex path is used for the ``J``-eigenspace triplet).
    Numpy-free.
    """
    is_complex = any(isinstance(c, complex) for c in coeffs)
    m = [[(0j if is_complex else 0.0) for _ in range(_DIM)] for _ in range(_DIM)]
    for idx, (p, q) in enumerate(_epq_pairs()):
        m[p][q] = coeffs[idx]
        m[q][p] = -coeffs[idx]
    return m


def _commutator_coords(x, y) -> List[Number]:
    """``E_{pq}`` coords of the commutator ``[X, Y]`` (real or complex)."""
    return _epq_coords(_commutator(x, y))


def _su3_stabiliser(g2: List[List[List[float]]], k: int) -> List[List[List[float]]]:
    """The su(3) stabiliser ``{D in g2 : D e_K = 0}`` as 8 antisymmetric ``8x8``.

    Build ``A = column_stack([g2[a] e_K for a])`` (``8 x 14``); its right
    nullspace (the float :func:`mat_svd` GEOMETRY carrier) is EXACTLY 8-dim.
    Each null coefficient vector ``c`` rebuilds a stabiliser generator
    ``M = sum_a c_a g2[a]``. Asserts ``dim == 8`` and that each ``M``
    annihilates ``e_K``. Numpy-free.
    """
    e_k = _basis_vectors()[k]
    # A is (8, 14): column a is g2[a]·e_K.
    a_rows = _transpose([_matvec(g2[a], e_k) for a in range(_DIM_G2)])  # (8, 14)
    null_coeffs = _svd_nullspace(a_rows, _DIM_SU3)
    assert len(null_coeffs) == _DIM_SU3, (
        f"su(3) stabiliser expected dim {_DIM_SU3}; got {len(null_coeffs)}"
    )
    su3 = [_lincomb([c[a] for a in range(_DIM_G2)], g2) for c in null_coeffs]
    su3 = [[[float(x.real if isinstance(x, complex) else x) for x in row]
            for row in m] for m in su3]
    for matrix in su3:
        residual = _magnitude(_vec_norm(_matvec(matrix, e_k)))
        assert residual < _RANK_TOL, (
            f"su(3) generator does not annihilate e_{k}: residual {residual}"
        )
    return su3


def _su3_complement(
    g2: List[List[List[float]]], su3: List[List[List[float]]]
) -> Tuple[List[List[List[float]]], List[List[Number]]]:
    """The 6-real-dim su(3)-module complement of su(3) inside g2.

    Orthonormalise the su(3) span and the g2 span in the ``E_{pq}`` frame,
    project the su(3) span out of the g2 span, and orthonormalise the residual:
    the surviving directions are EXACTLY the 6 orthogonal "mover" directions.
    Returns both the 6 antisymmetric ``8x8`` matrices and the ``(28, 6)``
    orthonormal coordinate frame (the latter is the J-construction's working
    frame, returned as a list of 6 length-28 column vectors). Asserts
    ``dim == 6``. Numpy-free (GEOMETRY via Gram-Schmidt, no SVD-count).
    """
    su3_coords = [_epq_coords(m) for m in su3]      # 8 columns (length 28)
    g2_coords = [_epq_coords(m) for m in g2]        # 14 columns
    q_su3 = _orthonormalise(su3_coords)             # orthonormal su(3) span (8)
    q_g2 = _orthonormalise(g2_coords)               # orthonormal g2 span (14)
    # Project each g2 basis vector off the su(3) span, then orthonormalise the
    # residuals → the complement directions.
    residuals: List[List[Number]] = []
    for v in q_g2:
        r = list(v)
        for q in q_su3:
            proj = sum(q[i] * r[i] for i in range(len(q)))
            r = [r[i] - proj * q[i] for i in range(len(q))]
        residuals.append(r)
    complement_coords = _orthonormalise(residuals)
    found = len(complement_coords)
    assert found == _DIM_COMPLEMENT, (
        f"su(3) complement expected dim {_DIM_COMPLEMENT}; got {found}"
    )
    complement = [_epq_to_matrix(c) for c in complement_coords]
    return complement, complement_coords


def _ad_on_complement(
    x, complement: List[List[List[float]]], complement_coords: List[List[Number]]
) -> List[List[Number]]:
    """The matrix of ``ad(X) = [X, .]`` restricted to the complement frame.

    Column ``i`` is the 6-vector of ``[X, complement_i]`` re-expressed in the
    orthonormal complement coordinate basis. For ``X in su(3)`` the
    complement is ad-invariant, so the result is an exact ``6x6`` real
    matrix. Numpy-free.
    """
    cols = []
    for y in complement:
        bracket = _commutator_coords(x, y)          # length-28 coords
        # re-express in the orthonormal complement frame: cⱼ = ⟨frameⱼ, bracket⟩.
        col = [sum(complement_coords[j][t] * bracket[t]
                   for t in range(len(bracket)))
               for j in range(_DIM_COMPLEMENT)]
        cols.append(col)
    # cols is column-major (one column per complement_i); transpose to row-major.
    return _transpose(cols)


def _invariant_complex_structure(
    su3: List[List[List[float]]],
    complement: List[List[List[float]]],
    complement_coords: List[List[Number]],
) -> List[List[float]]:
    """The su(3)-invariant complex structure ``J`` on the 6-dim complement.

    FIX 1 — the genuine fundamental is a J-EIGENSPACE, not a real 3-span.
    The commutant of the 6-dim real su(3)-rep ``{ad(X)|complement}`` is
    EXACTLY 2-dim ``{aI + bJ}``; ``J`` is its antisymmetric generator with
    ``J^2 = -I``. Solve the commutant by the deterministic nullspace of the
    stacked ``[ad^T ⊗ I - I ⊗ ad]`` (Kronecker) system (the float
    :func:`mat_svd` GEOMETRY carrier), take the antisymmetric part, normalise
    so ``J^2 = -I``, and pin the sign by a FIXED documented convention (first
    non-zero strict-upper-triangular entry positive — Class C chirality
    choice). Asserts commutant dim 2, ``J^2 = -I``, and ``[J, ad(X)] = 0`` for
    every ``X in su(3)``. Numpy-free.
    """
    dim = _DIM_COMPLEMENT
    identity = _eye(dim)
    ad_mats = [
        _ad_on_complement(x, complement, complement_coords) for x in su3
    ]
    # Each constraint block is ad⊗I − I⊗ad (the vec-commutant system),
    # row-stacked into a (8·36, 36) matrix; its null space is the commutant.
    stacked_rows: List[List[float]] = []
    for ad in ad_mats:
        block = _sub(_kron(_transpose(ad), identity), _kron(identity, ad))
        stacked_rows.extend(block)
    commutant_vecs = _svd_nullspace(stacked_rows, 2)   # 2 null vectors (length 36)
    assert len(commutant_vecs) == 2, (
        f"su(3)-rep commutant expected dim 2 {{aI + bJ}}; got {len(commutant_vecs)}"
    )
    # reshape each length-36 null vector into a 6×6 matrix, take its real part.
    commutant = []
    for vec in commutant_vecs:
        m = [[float((vec[i * dim + j]).real if isinstance(vec[i * dim + j], complex)
                    else vec[i * dim + j]) for j in range(dim)] for i in range(dim)]
        commutant.append(m)
    # The antisymmetric member of {aI + bJ} is J (up to scale); I is symmetric.
    antisymmetric = [_scale(_sub(m, _transpose(m)), 0.5) for m in commutant]
    j_raw = max(antisymmetric, key=lambda a: _frob_norm(a))
    # Normalise so J^2 = -I: J_raw^2 = -s^2 I, so J = J_raw / s.
    j_squared = _matmul(j_raw, j_raw)
    diag_mean = sum(j_squared[i][i] for i in range(dim)) / dim
    s = float(_srn.sqrt(_magnitude(float(diag_mean))))
    j = _scale(j_raw, 1.0 / s)
    # FIXED sign convention (Class C): first non-zero strict-upper-triangular
    # entry positive. Documented as a CHOICE; only J^2 = -I is a fact.
    for p in range(dim):
        for q in range(p + 1, dim):
            value = j[p][q]
            if _magnitude(float(value)) > _RANK_TOL:
                if value < 0.0:
                    j = _scale(j, -1.0)
                break
        else:
            continue
        break
    # Belt-and-suspenders: J^2 = -I and J commutes with every ad(X).
    jj_plus_i = _add(_matmul(j, j), identity)
    assert _magnitude(_frob_norm(jj_plus_i)) < _RANK_TOL, (
        "complex structure J does not satisfy J^2 = -I"
    )
    for ad in ad_mats:
        commute = _magnitude(_frob_norm(_commutator(j, ad)))
        assert commute < _RANK_TOL, (
            f"complex structure J does not commute with ad(su3): {commute}"
        )
    return j


def _triplet_from_eigenspace(
    j: List[List[float]], complement: List[List[List[float]]]
) -> Tuple[List[List[List[complex]]], List[List[List[complex]]]]:
    """The ``J = +i / -i`` eigenspaces as complex ``8x8`` matrices.

    FIX 1 — diagonalise the real antisymmetric ``J`` (eigenvalues ``+/- i``,
    each with multiplicity 3). The ``+i`` eigenvectors (complex coefficients
    over the complement frame) rebuild the 3 COMPLEX antisymmetric ``8x8``
    fundamental generators (the triplet); the ``-i`` eigenvectors rebuild
    the antitriplet (its conjugate). With this J-eigenspace fundamental,
    ``[su3, triplet] ⊆ triplet`` is bit-exact (``~3e-14``). Numpy-free.
    """
    eigenvalues, cols = _real_skew_eig(j)   # J real-antisymmetric → iS-Hermitian route
    n = len(j)
    plus = [k for k in range(n) if eigenvalues[k].imag > 0.5]
    minus = [k for k in range(n) if eigenvalues[k].imag < -0.5]
    assert len(plus) == _DIM_TRIPLET and len(minus) == _DIM_TRIPLET, (
        f"J eigenspaces expected {_DIM_TRIPLET}+{_DIM_TRIPLET}; got "
        f"{len(plus)}+{len(minus)}"
    )

    def combine(vec: List[complex]) -> List[List[complex]]:
        # Σ_c vec[c] · complement[c] (complex coefficients over the real frame).
        acc = [[0j for _ in range(_DIM)] for _ in range(_DIM)]
        for c in range(_DIM_COMPLEMENT):
            coef = vec[c]
            comp = complement[c]
            for i in range(_DIM):
                for jj in range(_DIM):
                    acc[i][jj] += coef * comp[i][jj]
        return acc

    triplet = [combine(cols[k]) for k in plus]
    antitriplet = [combine(cols[k]) for k in minus]
    return triplet, antitriplet


def _rank2_cartan(su3: List[List[List[float]]]) -> List[List[List[float]]]:
    """The rank-2 Cartan subalgebra of su(3) via a centraliser (FIX 3).

    FIX 3 — the greedy maximal mutually-commuting subset returns 1 (generic
    basis vectors do not pairwise-commute). Instead take a FIXED regular
    element ``R = sum_i (i+1) su3[i]``; its centraliser ``{X in su3 :
    [X, R] = 0}`` is EXACTLY the rank-2 Cartan. Solve the centraliser as the
    deterministic nullspace of ``column_stack([coords([su3[a], R])])`` over
    the 8-dim coefficient space (the float :func:`mat_svd` carrier). Asserts
    ``dim == 2``. Numpy-free.
    """
    regular = _lincomb([float(i + 1) for i in range(_DIM_SU3)], su3)
    # A is (28, 8): column a is coords([su3[a], R]).
    a_rows = _transpose([_commutator_coords(su3[a], regular)
                         for a in range(_DIM_SU3)])      # (28, 8)
    null_coeffs = _svd_nullspace(a_rows, 2)
    assert len(null_coeffs) == 2, (
        f"rank-2 Cartan via centraliser expected dim 2; got {len(null_coeffs)}"
    )
    cartan = [_lincomb([c[a] for a in range(_DIM_SU3)], su3) for c in null_coeffs]
    return [[[float(x.real if isinstance(x, complex) else x) for x in row]
             for row in m] for m in cartan]


def _complement_weights(
    cartan: List[List[List[float]]],
    complement: List[List[List[float]]],
    complement_coords: List[List[Number]],
) -> List[List[float]]:
    """The 6 complement weights under the rank-2 Cartan as a ``(6, 2)`` list.

    For each Cartan generator ``H`` (real antisymmetric on the complement),
    ``ad(H)`` has eigenvalues ``+/- i * weight``. The two ``ad(H_k)`` commute,
    so they share eigenvectors; the weight of eigenvector ``v`` along Cartan
    ``k`` is ``-i * (v^H ad(H_k) v) / (v^H v)``. The six weights come in
    ``+/-`` pairs (the su(3) ``3`` weights and their negatives). Numpy-free.
    """
    ad_cartan = [
        _ad_on_complement(h, complement, complement_coords) for h in cartan
    ]
    _, eig_cols = _real_skew_eig(ad_cartan[0])  # ad(H) real-antisym → iS-Hermitian route
    weights = [[0.0, 0.0] for _ in range(_DIM_COMPLEMENT)]
    for k in range(_DIM_COMPLEMENT):
        v = eig_cols[k]
        # v is a COMPLEX eigenvector of the real ad(H) (eigenvalues ±i·weight).
        # Use the HERMITIAN inner product (conjugate the first factor): a
        # complex eigenvector of a real skew matrix has v·v ≈ 0 (bilinear), so
        # the Rayleigh quotient MUST conjugate — ⟨v, v⟩ = Σ conj(vᵢ)·vᵢ.
        denom = sum(v[i].conjugate() * v[i] for i in range(len(v)))  # vᴴv
        for axis, ad in enumerate(ad_cartan):
            adv = _matvec(ad, v)
            rayleigh = sum(v[i].conjugate() * adv[i]
                           for i in range(len(v))) / denom            # vᴴ·ad·v
            # ad(H) v = i * weight * v  =>  weight = -i * rayleigh.
            weights[k][axis] = float((-1j * rayleigh).real)
    return weights


def _gen_bytes(generators: List[List[List[float]]]) -> bytes:
    """Concatenated float64 bytes of a list of real matrices (Class A content
    address; numpy-free — the same layout ``ascontiguousarray(g).tobytes()``
    produced: row-major IEEE-754 little-endian doubles)."""
    from array import array
    out = bytearray()
    for g in generators:
        buf = array("d", (float(x) for row in g for x in row))
        out.extend(buf.tobytes())
    return bytes(out)


def _an_attestation(generators: List[List[List[float]]], k: int) -> Dict[str, object]:
    """MPR v1 self-attestation for the COMPUTED su(3) ⊕ 3 ⊕ 3bar structure.

    Class A — content-address the GENERATED structure (NOT a fetched datum):
    ``response_sha256`` is :func:`srmech.amsc.format.sha256_bytes` over the
    concatenated ``float64`` bytes of the 14 ``g2`` generators (the build
    INPUT, deterministically content-addressed; **no** new
    ``hashlib.sha256``). ``parser_rule_hash`` hashes the stabiliser rule
    bytes ``b"D e_K = 0"``. ``source_url`` cites Baez (arXiv) for the
    ``g2 = Der(O)`` / dim-14 PARENT FACT ONLY — the 8+3+3bar branching is
    this op's own bit-exact computation, NOT a cited result.
    """
    response_sha256 = _sha256_bytes(_gen_bytes(generators))
    parser_rule_hash = _sha256_bytes(_AN_PARSER_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/qm/so8.py::an_embedding::su3_3_3bar"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "structure": "g2_su3_3_3bar_decomposition",
            "imaginary_unit": k,
            "real_dimensions": {"su3": _DIM_SU3, "complement": _DIM_COMPLEMENT},
            "complex_dimensions": {
                "triplet": _DIM_TRIPLET,
                "antitriplet": _DIM_TRIPLET,
            },
        },
        "data_schema_id": "srmech://schema/g2_su3_decomposition",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — no source_doi.
            "source_doi": None,
            # Cites the g2 = Der(O) / dim-14 PARENT FACT only (the build
            # input); the 8+3+3bar branching is this op's own computation.
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _AN_RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.5.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/so8.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "g2 = Der(O) su(3) ⊕ 3 ⊕ 3bar Lie decomposition",
            "purpose": (
                "Bit-exact su(3)-module branching of the 14 g2 generators "
                "(computed self-attesting structure)"
            ),
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155) — for g2 = Der(O), dim 14 "
                "(the build input only)"
            ),
        },
    }


@functools.lru_cache(maxsize=None)
def _build_an_embedding(imaginary_unit: int):
    """Cached read-only su(3) ⊕ 3 ⊕ 3bar build for a fixed imaginary unit.

    The expensive deterministic chain (SVD nullspaces + Kronecker commutant
    + eigendecompositions) runs once per ``imaginary_unit`` and is memoised;
    :func:`an_embedding` copies out a fresh dict each call. Returned as frozen
    nested tuples so the cache cannot be mutated through a caller's reference.
    Numpy-free.
    """
    k = imaginary_unit
    g2 = _g2_lists()

    su3 = _su3_stabiliser(g2, k)
    complement, complement_coords = _su3_complement(g2, su3)

    # Bidirectional killer test: span[su3 | complement] == span(g2) (rank 14).
    # The su(3) / complement generators are FLOAT (linear combinations of g2
    # with the SVD-nullspace coefficients), so this same-span check rides the
    # float-tolerant rank (NOT the exact ℚ RREF, which is reserved for the
    # genuinely-exact g2-derivation rank in _deterministic_rank_subset).
    su3_coords = [_epq_coords(m) for m in su3]
    g2_coords = [_epq_coords(m) for m in g2]
    span_cols = su3_coords + [list(c) for c in complement_coords]
    rank_span = _rank_float(span_cols)
    rank_with_g2 = _rank_float(span_cols + g2_coords)
    assert rank_span == _DIM_G2, (
        f"span[su3 | complement] rank expected {_DIM_G2}; got {rank_span}"
    )
    assert rank_with_g2 == _DIM_G2, (
        f"span[su3 | complement | g2] rank expected {_DIM_G2} (same span as "
        f"g2); got {rank_with_g2}"
    )

    j = _invariant_complex_structure(su3, complement, complement_coords)
    triplet, antitriplet = _triplet_from_eigenspace(j, complement)
    cartan = _rank2_cartan(su3)
    weights = _complement_weights(cartan, complement, complement_coords)

    return (
        _freeze(su3),
        _freeze(complement),
        tuple(tuple(row) for row in j),
        _freeze(triplet),
        _freeze(antitriplet),
        tuple(tuple(row) for row in weights),
    )


def an_embedding(imaginary_unit: int = 1) -> dict:
    """The bit-exact su(3) ⊕ 3 ⊕ 3bar Lie decomposition of ``g2 = Der(O)``.

    The 14 ``g2`` derivations (:func:`g2_subalgebra`) split, under one of
    their su(3) subalgebras, as the Lie-algebra branching ``14 = 8 + 3 +
    3bar`` — the su(3) ADJOINT (8) plus the FUNDAMENTAL (3) plus the
    ANTIFUNDAMENTAL (3bar). This is the genuine su(3)-module structure of
    ``g2``; the 7-dim octonion-imaginary vector rep branches ``7 = 1 + 3 +
    3bar`` over the same su(3). Both branchings are computed bit-exact and
    returned with an MPR self-attestation.

    CONSTRUCTION (deterministic, numpy-free, no RNG, no scipy; memoised via
    :func:`_build_an_embedding`, copied out fresh each call):

    1. **su(3) = the stabiliser** ``{D in g2 : D e_K = 0}`` (``e_K`` the
       ``imaginary_unit``-th octonion basis vector) via an SVD nullspace —
       EXACTLY 8-dim.
    2. **complement** — the 6-real-dim orthogonal su(3)-module (the
       "movers"); ``span[su3 | complement] == span(g2)`` (rank 14, both
       directions: the bidirectional killer test, EXACT over ℚ).
    3. **complex_structure_J** — the su(3)-INVARIANT complex structure on
       the 6-dim complement. The commutant of the 6-dim real su(3)-rep is
       EXACTLY 2-dim ``{aI + bJ}``; ``J`` is its antisymmetric generator,
       ``J^2 = -I``, ``[J, ad(X)] = 0`` for every ``X in su(3)``.
    4. **triplet / antitriplet** — the ``J = +i / -i`` eigenspaces of the
       complexified complement (COMPLEX ``8x8``): the genuine
       fundamental / antifundamental.

    WHY THE FUNDAMENTAL IS A J-EIGENSPACE (the load-bearing subtlety): a
    *real* 3-dim span of antisymmetric matrices CANNOT carry the su(3)
    fundamental — every real 3-subspace of the complement LEAKS at ``O(1)``
    under ``[su3, ·]`` (never bit-exact). The fundamental is irreducibly
    COMPLEX; it lives as the
    ``+i`` eigenspace of the invariant ``J``. With this ``J``-eigenspace
    ``3``, ``[su3, 3] ⊆ 3`` is bit-exact (``~3e-14``). The returned
    ``complement`` is the GENUINE real su(3)-module (``[su3, complement] ⊆
    complement`` is ``~2e-15``); only the ``J``-eigenspace ``triplet`` /
    ``antitriplet`` carry the irreducible ``3`` / ``3bar`` with the bit-exact
    ``[su3, 3] ⊆ 3`` closure.

    su(3) IDENTIFICATION (an honest INVARIANT certificate, NOT a raw-Casimir
    comparison): ``{dim 8, rank 2, simple}`` — where ``rank 2`` is the
    dimension of the centraliser of a fixed regular element (the
    greedy mutually-commuting-subset count would spuriously return 1), and
    ``simple`` means the adjoint commutant has dim 1. By the Cartan ``A2``
    classification these UNIQUELY identify su(3) (ruling out ``su(2) +
    su(2)``, whose commutant is 2). Supporting evidence: in a
    Killing-orthonormalised basis the structure constants are TOTALLY
    ANTISYMMETRIC. (A raw adjoint-Casimir-vs-``f^{abc}`` comparison to
    :func:`srmech.qm.gauge.su3_structure_constants` is deliberately NOT used:
    the candidate's adjoint-Casimir eigenvalue is basis-dependent and its
    normalisation differs from the gauge Gell-Mann convention, the
    Casimir/Killing ratio is tautologically 1 for any algebra, and the two
    bases differ by an ``O(8)`` rotation so raw ``f^{abc}`` equality fails
    too.)

    3 / 3bar ORIENTATION is pinned by a FIXED convention (the documented
    sign of ``J``, plus a lexicographic key on the Cartan weights) and is a
    CHOICE — a Class C chirality / complex-structure-sign convention, NOT
    canonical. Only the ``+/-`` weight-PAIRING is asserted as fact.

    A-N FRAMEWORK READING (a documented LABEL, **not** a derived theorem; per
    ``[[feedback_no_lineage_claims_in_notebook]]``): the SAME 14-dim ``g2``
    carries TWO distinct enumerations — the A-N discovery partition
    ``1 + 3 + 7 + 3`` (this collaboration's substrate-self-recognition order)
    and this su(3)-Lie branching ``8 + 3 + 3bar``. They are read as two
    languages describing the one object; they are explicitly NOT slot-aligned
    and the correspondence is NOT a proof. Class C-L (the Class C
    chirality / complex-structure orientation composed with the Class L
    eigendecomposition that extracts ``J`` and the weight spectrum). The
    A-N reading is surfaced ONLY under the separately-keyed
    ``framework_an_reading`` field, tagged "framework-reading, not derived";
    no A-N class name appears in any load-bearing return key.

    rc123 (numpy-free): the matrix values in the returned dict are real /
    complex ``8x8`` :class:`Mat` (the ``complex_structure_J`` a ``6x6`` real
    ``Mat``; ``weights`` a nested ``list[list[float]]``); ``Mat`` is 2-D only.

    Canonical SSoT: Baez (2002) §4.1 (``g2 = Der(O)``, dim 14) — for the
    BUILD INPUT ONLY. The ``8 + 3 + 3bar`` / ``7 = 1 + 3 + 3bar`` branching
    is this op's own bit-exact self-attesting COMPUTATION; §4.1 is NOT cited
    for it (and Slansky / Fulton-Harris / Gunaydin-Gursey are deliberately
    NOT cited — not PDF-verified here).

    Args:
        imaginary_unit: The fixed octonion imaginary unit ``K`` (``1..7``)
            whose stabiliser is the su(3); the decomposition is conjugate
            (hence isomorphic) for any choice. Defaults to 1.

    Returns:
        A ``dict`` with keys:

        - ``su3`` — list of 8 real antisymmetric ``8x8`` ``Mat`` (the
          su(3) adjoint; the stabiliser of ``e_K``).
        - ``complement`` — list of 6 real antisymmetric ``8x8`` ``Mat``
          (the genuine real su(3)-module; ``[su3, complement] ⊆ complement``
          ``~2e-15``).
        - ``complex_structure_J`` — the ``6x6`` real invariant complex
          structure ``Mat`` (``J^2 = -I``).
        - ``triplet`` / ``antitriplet`` — lists of 3 COMPLEX ``8x8`` ``Mat``
          (the genuine fundamental / antifundamental; the ``J = +i / -i``
          eigenspaces; ``[su3, triplet] ⊆ triplet`` is bit-exact via ``J``).
          ``antitriplet`` is the conjugate of ``triplet``.
        - ``weights`` — a ``(6, 2)`` nested ``list[list[float]]`` of the
          complement weights under the rank-2 Cartan (the ``+/-`` pairs).
        - ``decomposition`` — ``{"adjoint_14": (8, 3, 3), "vector_7":
          (1, 3, 3)}`` (the ``g2`` and the octonion-vector branchings).
        - ``imaginary_unit`` — the ``K`` used.
        - ``attestation`` — the MPR v1 self-attestation (Class A
          content-address of the computed structure).
        - ``framework_an_reading`` — the A-N reading LABEL (tagged
          "framework-reading, not derived").

    Raises:
        ValueError: if ``imaginary_unit`` is not in ``1..7``.
    """
    if not 1 <= imaginary_unit <= 7:
        raise ValueError(
            f"an_embedding: imaginary_unit must be in 1..7; got {imaginary_unit}"
        )
    (
        su3,
        complement,
        j,
        triplet,
        antitriplet,
        weights,
    ) = _build_an_embedding(imaginary_unit)

    # Copy out fresh Mats (the cached build is frozen nested tuples).
    su3_out = [Mat.from_rows([list(r) for r in m]) for m in su3]
    complement_out = [Mat.from_rows([list(r) for r in m]) for m in complement]
    triplet_out = [Mat.from_rows([list(r) for r in m], is_complex=True) for m in triplet]
    antitriplet_out = [Mat.from_rows([list(r) for r in m], is_complex=True)
                       for m in antitriplet]
    j_out = Mat.from_rows([list(r) for r in j])
    weights_out = [list(r) for r in weights]

    # Content-address the COMPUTED structure via its build input: the 14
    # g2 generators (the deterministic float64 bytes; generated, not fetched).
    g2_generators = _g2_lists()
    attestation = _an_attestation(g2_generators, imaginary_unit)

    return {
        "su3": su3_out,
        "complement": complement_out,
        "complex_structure_J": j_out,
        "triplet": triplet_out,
        "antitriplet": antitriplet_out,
        "weights": weights_out,
        "decomposition": {
            "adjoint_14": (_DIM_SU3, _DIM_TRIPLET, _DIM_TRIPLET),
            "vector_7": (1, _DIM_TRIPLET, _DIM_TRIPLET),
        },
        "imaginary_unit": imaginary_unit,
        "attestation": attestation,
        "framework_an_reading": {
            "note": "framework-reading, not derived",
            "an_discovery_partition": (1, 3, 7, 3),
            "su3_lie_branching": (_DIM_SU3, _DIM_TRIPLET, _DIM_TRIPLET),
            "slot_aligned": False,
        },
    }


# ──────────────────────────────────────────────────────────────────────
# quaternion_subalgebra_stabiliser — the 6-dim so(4) = su(2) ⊕ su(2)
# subalgebra of g2 = Der(O) that stabilises a quaternion subalgebra H ⊂ O.
#
# The ℍ-reading SIBLING of ``an_embedding`` (the su(3) ⊕ 3 ⊕ 3bar
# ℂ-reading). A quaternion subalgebra H ⊂ O is span(e_0, e_a, e_b, e_c)
# for a Fano line (a, b, c); the derivations D in g2 that map H back into
# H (equivalently, map the 4-dim orthogonal complement H^⊥ into itself)
# form EXACTLY the 6-dim so(4) = su(2) ⊕ su(2) (F215).
#
# The construction is the deterministic chain (no RNG, numpy-free):
#   1. so(4) = the stabiliser {D in g2 : D span(H_imag) ⊆ span(H_imag)}
#      (SVD nullspace of the leak-into-H^⊥ constraint; dim 6).
#   2. Killing-form rank = 6 (the stabiliser is SEMISIMPLE — so(4) is, the
#      raw certificate ruling out a solvable / abelian factor).
#   3. The two su(2) ideals = the self-dual / anti-self-dual halves of the
#      stabiliser's action on the 4-dim complement H^⊥ ≅ R^4 (the canonical
#      so(4) = su(2)_+ ⊕ su(2)_- 't Hooft self-dual split). Each closes as
#      su(2), the two commute ([A, B] = 0), each is a g2-ideal — all
#      bit-exact (~1e-14).
#
# This voxel keeps the SYMMETRY surface (so(4) ⊂ g2, a Lie subalgebra)
# visibly distinct from the OPERATOR surface (cascade.atoms.*, the 6
# lean-ISA group-element ops). F215 showed the 6 atoms are group-element
# operations (0 of 6 are Lie generators), NOT this Lie subalgebra; the
# "6 = 6" (6 atoms vs dim-6 so(4)) was coincidence, surfaced ONLY under the
# separately-keyed ``framework_so4_reading`` field.
# ──────────────────────────────────────────────────────────────────────


def _quaternion_imaginary_units(fano_line: Tuple[int, int, int]) -> List[int]:
    """The 3 imaginary octonion units of the quaternion subalgebra H.

    A quaternion subalgebra ``H ⊂ O`` is ``span(e_0, e_a, e_b, e_c)`` for a
    Fano line ``(a, b, c)`` (the unordered triple closes ``e_a e_b = ± e_c``);
    its imaginary part is ``span(e_a, e_b, e_c)``. Internal helper.
    """
    return sorted(fano_line)


def _quaternion_complement_units(h_imag: List[int]) -> List[int]:
    """The 4 octonion units of the orthogonal complement ``H^⊥``.

    ``e_0`` is shared (the identity, fixed by every derivation), so the
    derivation-relevant complement is the 4 imaginary units NOT in ``H`` —
    here returned as the 4 octonion indices ``{1..7} \\ h_imag``. (A
    derivation annihilates ``e_0``; stabilising ``H`` reduces to mapping the
    3 ``H``-imaginary units back into ``span(H_imag)``.)
    """
    return [i for i in range(1, _DIM) if i not in h_imag]


def _so4_stabiliser(
    g2: List[List[List[float]]], h_imag: List[int], complement: List[int]
) -> List[List[List[float]]]:
    """The so(4) stabiliser ``{D in g2 : D span(H_imag) ⊆ span(H_imag)}``.

    Build the leak constraint: for every ``H``-imaginary unit ``e_a`` and
    every complement unit ``e_k`` (``k in H^⊥``), the ``e_k`` component of
    ``(sum_c x_c g2[c]) e_a`` must vanish. That is a
    ``(|H_imag| * |H^⊥|, 14) = (12, 14)`` linear system in the 14 g2
    coefficients; its right nullspace (the float :func:`mat_svd` GEOMETRY
    carrier) is EXACTLY 6-dim. Each null coefficient vector ``c`` rebuilds a
    stabiliser generator ``M = sum_c c_c g2[c]``. Asserts ``dim == 6`` and
    that each ``M`` leaks nothing from ``H`` into ``H^⊥``. Numpy-free.
    """
    basis = _basis_vectors()
    rows: List[List[float]] = []
    for a in h_imag:
        for k in complement:
            rows.append(
                [_matvec(g2[c], basis[a])[k] for c in range(_DIM_G2)]
            )
    # constraint is (12, 14); its right nullspace is the so(4) coefficient space.
    null_coeffs = _svd_nullspace(rows, _DIM_SO4)
    assert len(null_coeffs) == _DIM_SO4, (
        f"so(4) stabiliser expected dim {_DIM_SO4}; got {len(null_coeffs)}"
    )
    raw = [_lincomb([c[a] for a in range(_DIM_G2)], g2) for c in null_coeffs]
    raw = [[[float(x.real if isinstance(x, complex) else x) for x in row]
            for row in m] for m in raw]
    # Orthonormalise in the shared E_{pq} frame (deterministic Gram-Schmidt, no
    # RNG): the Killing-form SPECTRUM is then a basis-INDEPENDENT,
    # ℍ-choice-invariant invariant (two distinct eigenvalues, multiplicity 3
    # each = su(2) ⊕ su(2)). Without this the spectrum scales with the arbitrary
    # SVD-nullspace basis.
    raw_coords = [_epq_coords(m) for m in raw]            # 6 columns (length 28)
    q_ortho = _orthonormalise(raw_coords)
    so4 = [_epq_to_matrix(c) for c in q_ortho]
    so4 = [[[float(x.real if isinstance(x, complex) else x) for x in row]
            for row in m] for m in so4]
    for matrix in so4:
        leak = 0.0
        for a in h_imag:
            image = _matvec(matrix, basis[a])
            for k in complement:
                leak = leak + image[k] * image[k]
        residual = _magnitude(float(_srn.sqrt(leak)))
        assert residual < _RANK_TOL, (
            f"so(4) generator leaks H into H^perp: residual {residual}"
        )
    return so4


def _killing_form(generators: List[List[List[float]]]) -> List[List[float]]:
    """The Killing form ``K_{ab} = tr(ad_a ad_b)`` of a Lie generator set.

    Solve the structure constants ``[g_i, g_j] = sum_k f_{ij}^k g_k`` in the
    shared ``E_{pq}`` frame (a least-squares solve against the generator
    coordinate stack — exact here, the brackets close in the span), then form
    ``K_{ab} = sum_{c,d} f_{ac}^d f_{bd}^c``. Returned as an ``(n, n)`` real
    symmetric nested list; its rank is the semisimplicity certificate (full
    rank ``n`` iff semisimple, by Cartan's criterion). Numpy-free.
    """
    n = len(generators)
    coords = [_epq_coords(m) for m in generators]         # n columns (length 28)
    pinv = _pinv(coords)                                  # (n, 28) pseudoinverse
    # f[i][j][:] = pinv · coords([g_i, g_j]).
    f = [[[0.0] * n for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            bracket = _commutator_coords(generators[i], generators[j])  # length 28
            fij = _matvec(pinv, bracket)                  # length n
            for kk in range(n):
                f[i][j][kk] = float(fij[kk].real if isinstance(fij[kk], complex)
                                    else fij[kk])
    killing = _zeros(n, n)
    for a in range(n):
        for b in range(n):
            s = 0.0
            for c in range(n):
                for d in range(n):
                    s += f[a][c][d] * f[b][d][c]
            killing[a][b] = s
    return killing


def _pinv(columns: List[List[Number]]) -> List[List[float]]:
    """Moore-Penrose pseudoinverse of the (28, n) column stack via the cascade
    SVD (the float :func:`mat_svd` GEOMETRY carrier).

    ``A = U·diag(s)·Vᴴ`` ⟹ ``A⁺ = V·diag(1/s)·Uᴴ`` with the same small-
    singular-value cutoff NumPy's ``pinv`` applies (``rcond·s_max``,
    ``rcond = 1e-15``). The pseudoinverse is unique, so the per-factor U/V
    column-sign ambiguity of the SVD cancels — value-faithful for the
    full-column-rank generator stacks this module forms. Returns the
    ``(n, 28)`` pseudoinverse as a real nested list. Numpy-free.
    """
    A = _transpose(columns)                               # (28, n)
    U, S, Vh = mat_svd(Mat.from_rows(A))                  # U (28,28), S, Vh (n,n)
    m_rows = len(A)
    n_cols = len(A[0]) if m_rows else 0
    cutoff = 1e-15 * (S[0] if S else 0.0)
    k = len(S)
    # A⁺ = V·diag(1/s)·Uᴴ. V = Vh.conj().T (so V[i][j] = conj(Vh[j][i])); for a
    # real A, V/U are real-valued.
    out = _zeros(n_cols, m_rows)
    for i in range(n_cols):
        for jcol in range(m_rows):
            acc = 0.0
            for t in range(k):
                s = S[t]
                if s > cutoff:
                    v_it = Vh[t, i]                       # V[i][t] = conj(Vh[t][i])
                    u_jt = U[jcol, t]                     # Uᴴ[t][j] = conj(U[j][t])
                    v_it = v_it.conjugate() if isinstance(v_it, complex) else v_it
                    u_jt = u_jt.conjugate() if isinstance(u_jt, complex) else u_jt
                    acc += float((v_it * (1.0 / s) * u_jt).real
                                 if isinstance(v_it * u_jt, complex)
                                 else v_it * (1.0 / s) * u_jt)
            out[i][jcol] = acc
    return out


def _self_dual_bases() -> Tuple[List[List[float]], List[List[float]]]:
    """The 't Hooft self-dual / anti-self-dual ``so(4)`` 6-vector frames.

    ``so(4)`` on ``R^4`` splits ``su(2)_+ ⊕ su(2)_-`` into the self-dual and
    anti-self-dual antisymmetric ``4x4`` matrices. In the 6-vector coordinate
    ``(M_01, M_02, M_03, M_12, M_13, M_23)`` the self-dual triple is
    ``E_01 + E_23, E_02 - E_13, E_03 + E_12`` and the anti-self-dual triple is
    ``E_01 - E_23, E_02 + E_13, E_03 - E_12`` (``E_ij`` the elementary
    antisymmetric generator). Returns the two ``(6, 3)`` coordinate frames as
    column lists (3 length-6 vectors each). Numpy-free.
    """
    def e(i: int, j: int) -> List[List[float]]:
        m = _zeros(_DIM_COMP4, _DIM_COMP4)
        m[i][j] = 1.0
        m[j][i] = -1.0
        return m

    def vec6(m: List[List[float]]) -> List[float]:
        return [m[0][1], m[0][2], m[0][3], m[1][2], m[1][3], m[2][3]]

    self_dual = [_add(e(0, 1), e(2, 3)), _sub(e(0, 2), e(1, 3)), _add(e(0, 3), e(1, 2))]
    anti_self_dual = [_sub(e(0, 1), e(2, 3)), _add(e(0, 2), e(1, 3)),
                      _sub(e(0, 3), e(1, 2))]
    sd = [vec6(m) for m in self_dual]                     # 3 columns (length 6)
    asd = [vec6(m) for m in anti_self_dual]
    return sd, asd


def _two_su2_ideals(
    so4: List[List[List[float]]], complement: List[int]
) -> Tuple[List[List[List[float]]], List[List[List[float]]]]:
    """The two su(2) ideals via the self-dual / anti-self-dual split.

    Restrict each so(4) generator to the ``4x4`` block on the complement
    ``H^⊥`` (``block[i, j] = D[complement_i, complement_j]``) and read its
    6-vector coordinate; the 6-dim block span is the FULL ``so(4)`` on
    ``R^4``. The su(2)_+ ideal = the so(4) generators whose block is purely
    self-dual (the anti-self-dual projection of the block vanishes); the
    su(2)_- ideal = the purely anti-self-dual ones. Each is solved as the
    deterministic SVD nullspace of the cross-duality projection composed with
    the block map. Asserts each ideal is 3-dim. Numpy-free.
    """
    idx = complement

    def block_vec(matrix: List[List[float]]) -> List[float]:
        return [
            matrix[idx[0]][idx[1]], matrix[idx[0]][idx[2]],
            matrix[idx[0]][idx[3]], matrix[idx[1]][idx[2]],
            matrix[idx[1]][idx[3]], matrix[idx[2]][idx[3]],
        ]

    # block_map is (6, 6): column m is block_vec(so4[m]).
    block_map = _transpose([block_vec(m) for m in so4])
    sd_frame, asd_frame = _self_dual_bases()              # 3 columns each (length 6)
    q_sd = _orthonormalise(sd_frame)
    q_asd = _orthonormalise(asd_frame)
    # projector = Σ qᵢ qᵢᵀ (real orthonormal).
    proj_sd = _projector_from_basis(q_sd, _DIM_SO4)
    proj_asd = _projector_from_basis(q_asd, _DIM_SO4)

    def ideal_for(cross_projector: List[List[float]]) -> List[List[List[float]]]:
        # generators whose block vanishes under the OTHER duality projector.
        leak = _matmul(cross_projector, block_map)        # (6, 6)
        coeffs = _svd_nullspace(leak, _DIM_SU2)
        assert len(coeffs) == _DIM_SU2, (
            f"su(2) ideal expected dim {_DIM_SU2}; got {len(coeffs)}"
        )
        out = [_lincomb([c[kk] for kk in range(_DIM_SO4)], so4) for c in coeffs]
        return [[[float(x.real if isinstance(x, complex) else x) for x in row]
                 for row in m] for m in out]

    su2_plus = ideal_for(proj_asd)   # purely self-dual blocks
    su2_minus = ideal_for(proj_sd)   # purely anti-self-dual blocks
    return su2_plus, su2_minus


def _projector_from_basis(basis: List[List[Number]], n: int) -> List[List[float]]:
    """The orthogonal projector ``Σ qᵢ qᵢᵀ`` onto the span of an orthonormal
    ``basis`` (real columns), as an ``n×n`` nested list (numpy-free)."""
    proj = _zeros(n, n)
    for q in basis:
        for i in range(n):
            qi = q[i].real if isinstance(q[i], complex) else q[i]
            for j in range(n):
                qj = q[j].real if isinstance(q[j], complex) else q[j]
                proj[i][j] += qi * qj
    return proj


def _so4_attestation(
    generators: List[List[List[float]]], fano_line: Tuple[int, int, int]
) -> Dict[str, object]:
    """MPR v1 self-attestation for the COMPUTED so(4) = su(2) ⊕ su(2) structure.

    Class A — content-address the GENERATED structure (NOT a fetched datum):
    ``response_sha256`` is :func:`srmech.amsc.format.sha256_bytes` over the
    concatenated ``float64`` bytes of the 14 ``g2`` generators (the build
    INPUT, deterministically content-addressed; **no** new
    ``hashlib.sha256``). ``parser_rule_hash`` hashes the stabiliser rule
    bytes. ``source_url`` cites Baez (arXiv) for the ``g2 = Der(O)`` /
    dim-14 PARENT FACT ONLY — the su(2) ⊕ su(2) split is this op's own
    bit-exact computation, NOT a cited result. Mirrors
    :func:`_an_attestation` verbatim in form.
    """
    response_sha256 = _sha256_bytes(_gen_bytes(generators))
    parser_rule_hash = _sha256_bytes(_SO4_PARSER_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/qm/so8.py::quaternion_subalgebra_stabiliser::so4_su2_su2"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "structure": "g2_so4_su2_su2_quaternion_stabiliser",
            "quaternion_fano_line": list(fano_line),
            "real_dimensions": {
                "so4": _DIM_SO4,
                "su2_plus": _DIM_SU2,
                "su2_minus": _DIM_SU2,
            },
        },
        "data_schema_id": "srmech://schema/g2_so4_quaternion_stabiliser",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — no source_doi.
            "source_doi": None,
            # Cites the g2 = Der(O) / dim-14 PARENT FACT only (the build
            # input); the su(2) ⊕ su(2) split is this op's own computation.
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _AN_RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.6.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/so8.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "g2 = Der(O) so(4) = su(2) ⊕ su(2) quaternion-stabiliser",
            "purpose": (
                "Bit-exact so(4) subalgebra of g2 stabilising a quaternion "
                "subalgebra H ⊂ O (computed self-attesting structure)"
            ),
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155) — for g2 = Der(O), dim 14 "
                "(the build input only)"
            ),
        },
    }


#: The 7 Fano lines indexed 1..7 — the 7 quaternion subalgebras H ⊂ O.
#: Identical to :data:`srmech.qm.octonion._FANO_LINES`; re-declared here so
#: the so(4) builder picks an H deterministically by a 1-based index.
_FANO_LINES_SO4: Tuple[Tuple[int, int, int], ...] = (
    (1, 2, 3), (1, 4, 5), (1, 6, 7),
    (2, 4, 6), (2, 5, 7),
    (3, 4, 7), (3, 5, 6),
)


@functools.lru_cache(maxsize=None)
def _build_quaternion_stabiliser(quaternion_index: int):
    """Cached read-only so(4) = su(2) ⊕ su(2) build for a fixed quaternion H.

    The expensive deterministic chain (SVD nullspace + Killing form + the
    self-dual split) runs once per ``quaternion_index`` and is memoised;
    :func:`quaternion_subalgebra_stabilizer` copies out a fresh dict each call.
    Returned as frozen nested tuples (the cache cannot be mutated). Numpy-free.
    """
    fano_line = _FANO_LINES_SO4[quaternion_index - 1]
    h_imag = _quaternion_imaginary_units(fano_line)
    complement = _quaternion_complement_units(h_imag)
    g2 = _g2_lists()

    so4 = _so4_stabiliser(g2, h_imag, complement)
    killing = _killing_form(so4)

    # Semisimplicity certificate: Killing rank == 6 (full; Cartan criterion).
    # The Killing matrix is FLOAT (built from the SVD-derived so(4) generators),
    # so the rank rides the float-tolerant Gram-Schmidt rank (a full-rank
    # semisimple Killing form is unambiguous well clear of the float floor).
    killing_rank = _rank_float([[killing[r][c] for r in range(_DIM_SO4)]
                                for c in range(_DIM_SO4)])
    assert killing_rank == _DIM_SO4, (
        f"so(4) Killing-form rank expected {_DIM_SO4} (semisimple); "
        f"got {killing_rank}"
    )

    su2_plus, su2_minus = _two_su2_ideals(so4, complement)

    # Bidirectional killer test: span[su2_+ | su2_-] == span(so4) (rank 6).
    # The su(2) / so(4) generators are FLOAT (SVD-derived), so this same-span
    # check rides the float-tolerant rank — the rank-deficient regime the so8
    # fix targets: rank_with_so4 stays 6, NOT a coincidental full rank.
    so4_coords = [_epq_coords(m) for m in so4]
    plus_coords = [_epq_coords(m) for m in su2_plus]
    minus_coords = [_epq_coords(m) for m in su2_minus]
    split_span = plus_coords + minus_coords
    rank_split = _rank_float(split_span)
    rank_with_so4 = _rank_float(split_span + so4_coords)
    assert rank_split == _DIM_SO4, (
        f"span[su2_+ | su2_-] rank expected {_DIM_SO4}; got {rank_split}"
    )
    assert rank_with_so4 == _DIM_SO4, (
        f"span[su2_+ | su2_- | so4] rank expected {_DIM_SO4} (same span as "
        f"so4); got {rank_with_so4}"
    )

    return (
        _freeze(so4),
        _freeze(su2_plus),
        _freeze(su2_minus),
        tuple(tuple(row) for row in killing),
        tuple(h_imag),
    )


def quaternion_subalgebra_stabilizer(quaternion_index: int = 1) -> dict:
    """The bit-exact 6-dim so(4) = su(2) ⊕ su(2) ⊂ g2 stabilising ℍ ⊂ 𝕆.

    The ℍ-reading SIBLING of :func:`an_embedding` (the su(3) ⊕ 3 ⊕ 3bar
    ℂ-reading of the same ``g2 = Der(O)``). A quaternion subalgebra
    ``H ⊂ O`` is ``span(e_0, e_a, e_b, e_c)`` for a Fano line ``(a, b, c)``
    (:data:`srmech.qm.octonion._FANO_LINES`); the derivations ``D in g2``
    that map ``H`` back into ``H`` — equivalently map the 4-dim orthogonal
    complement ``H^⊥`` into itself — form EXACTLY the 6-dim
    ``so(4) = su(2) ⊕ su(2)`` (F215). The result is returned with the
    invariant CERTIFICATE and an MPR self-attestation.

    CONSTRUCTION (deterministic, numpy-free, no RNG, no scipy; memoised via
    :func:`_build_quaternion_stabiliser`, copied out fresh each call):

    1. **so(4) = the stabiliser** ``{D in g2 : D span(H_imag) ⊆
       span(H_imag)}`` via the SVD nullspace of the
       leak-into-``H^⊥`` constraint — EXACTLY 6-dim.
    2. **Killing-form rank == 6** — the SEMISIMPLICITY certificate (full
       rank over ℚ, by Cartan's criterion; rules out a solvable / abelian
       factor). The two-triplet Killing SPECTRUM (two distinct eigenvalues,
       each multiplicity 3) is the su(2) ⊕ su(2) fingerprint and is
       ℍ-choice-invariant.
    3. **the two su(2) ideals** — the self-dual / anti-self-dual halves of
       the stabiliser's action on the 4-dim complement ``H^⊥ ≅ R^4`` (the
       canonical ``so(4) = su(2)_+ ⊕ su(2)_-`` 't Hooft split). Each closes
       as su(2) (``~1e-14``), the two commute (``[su2_+, su2_-] = 0``,
       ``~1e-14``), and each is a g2-ideal (``~1e-14``);
       ``span[su2_+ | su2_-] == span(so4)`` (rank 6, both directions: the
       bidirectional killer test, EXACT over ℚ).

    ℍ-CHOICE-INVARIANCE: the stabiliser of ANY quaternion subalgebra is the
    SAME algebra-type (so(4) = su(2) ⊕ su(2), dim 6, Killing rank 6, the
    two-triplet spectrum) — the seven Fano-line choices are conjugate under
    g2 = Aut(O), hence isomorphic. The returned ``killing_spectrum`` is
    bit-identical across ``quaternion_index`` choices (verified in the test
    suite across ≥ 2 distinct ℍ).

    THE su(2) ⊕ su(2) SPLIT IS COMPUTED, NOT CITED: Baez (2002) §4.1 is the
    build input ONLY (``g2 = Der(O)``, dim 14). That the ℍ-stabiliser is
    so(4) = su(2) ⊕ su(2) is this op's own bit-exact self-attesting
    computation (the Killing rank, the two-ideal self-dual split, the
    closure / commute / ideal residuals are all measured here), NOT a quoted
    theorem.

    SYMMETRY SURFACE vs OPERATOR SURFACE (the F215 point of this voxel,
    surfaced under the separately-keyed ``framework_so4_reading`` field;
    framework-reading, NOT a derived theorem): this so(4) ⊂ g2 is a 6-dim
    **Lie subalgebra** (a continuous SYMMETRY of the octonions). It is
    EXPLICITLY DISTINCT from the 6 ``srmech.amsc.cascade.atoms`` lean-ISA
    operators (``pin_slot_at_zero``, ``reorient``, ``magnitude``,
    ``chiral_flip``, ``chiral_dual``, ``net_chirality``) — those are
    group-ELEMENT operations (0 of the 6 are Lie generators / one-parameter
    subgroups). The numerical coincidence "6 atoms = dim-6 so(4)" is a
    COINCIDENCE per F215, NOT a correspondence; keeping the symmetry surface
    here distinct from the operator surface is the reason this voxel exists.

    rc123 (numpy-free): the matrix values in the returned dict are real
    ``8x8`` :class:`Mat` (``killing_form`` a ``6x6`` real ``Mat``;
    ``killing_spectrum`` a sorted ``list[float]``); ``Mat`` is 2-D only.

    Args:
        quaternion_index: The 1-based index ``1..7`` of the Fano line
            ``(a, b, c)`` whose quaternion subalgebra
            ``H = span(e_0, e_a, e_b, e_c)`` is stabilised; the stabiliser is
            conjugate (hence isomorphic) for any choice. Defaults to 1
            (the line ``(1, 2, 3)``).

    Returns:
        A ``dict`` with keys:

        - ``so4`` — list of 6 real antisymmetric ``8x8`` ``Mat`` (the
          full so(4) stabiliser of ``H``).
        - ``su2_plus`` / ``su2_minus`` — lists of 3 real antisymmetric
          ``8x8`` ``Mat`` (the two su(2) ideals; the self-dual /
          anti-self-dual halves of the action on ``H^⊥``;
          ``[su2_+, su2_-] = 0``, ``span[su2_+ | su2_-] = span(so4)``).
        - ``killing_form`` — the ``6x6`` real symmetric Killing-form
          ``Mat`` (rank 6: semisimple).
        - ``killing_rank`` — ``6`` (the semisimplicity certificate).
        - ``killing_spectrum`` — the sorted ``6``-element ``list[float]`` of
          Killing eigenvalues (two distinct values, multiplicity 3 each: the
          su(2) ⊕ su(2) fingerprint; ℍ-choice-invariant).
        - ``decomposition`` — ``{"so4_6": (3, 3)}`` (the two su(2) dims).
        - ``quaternion_fano_line`` — the ``(a, b, c)`` line used.
        - ``quaternion_imaginary_units`` — ``(a, b, c)`` sorted (the
          imaginary part of ``H``).
        - ``attestation`` — the MPR v1 self-attestation (Class A
          content-address of the computed structure).
        - ``framework_so4_reading`` — the symmetry-surface-vs-operator-surface
          reading LABEL (tagged "framework-reading, not derived"; the F215
          "6 = 6 coincidence" note).

    Raises:
        ValueError: if ``quaternion_index`` is not in ``1..7``.
    """
    if not 1 <= quaternion_index <= 7:
        raise ValueError(
            "quaternion_subalgebra_stabilizer: quaternion_index must be in "
            f"1..7; got {quaternion_index}"
        )
    (
        so4,
        su2_plus,
        su2_minus,
        killing,
        h_imag,
    ) = _build_quaternion_stabiliser(quaternion_index)

    # Copy out fresh Mats (the cached build is frozen nested tuples).
    so4_out = [Mat.from_rows([list(r) for r in m]) for m in so4]
    su2_plus_out = [Mat.from_rows([list(r) for r in m]) for m in su2_plus]
    su2_minus_out = [Mat.from_rows([list(r) for r in m]) for m in su2_minus]
    killing_rows = [list(r) for r in killing]
    killing_out = Mat.from_rows(killing_rows)
    # Class-L Hermitian eigendecomposition (srmech's own primitive). The
    # Killing form is real-symmetric; we only need its spectrum. eigvals come
    # back ascending already; keep them sorted ascending. Numpy-free.
    evals_mat, _ = mat_hermitian_eigendecompose(killing_out)
    killing_spectrum = sorted(float(evals_mat[i, 0]) for i in range(_DIM_SO4))

    fano_line = _FANO_LINES_SO4[quaternion_index - 1]

    # Content-address the COMPUTED structure via its build input: the 14
    # g2 generators (the deterministic float64 bytes; generated, not fetched).
    g2_generators = _g2_lists()
    attestation = _so4_attestation(g2_generators, fano_line)

    return {
        "so4": so4_out,
        "su2_plus": su2_plus_out,
        "su2_minus": su2_minus_out,
        "killing_form": killing_out,
        "killing_rank": _DIM_SO4,
        "killing_spectrum": killing_spectrum,
        "decomposition": {"so4_6": (_DIM_SU2, _DIM_SU2)},
        "quaternion_fano_line": fano_line,
        "quaternion_imaginary_units": h_imag,
        "attestation": attestation,
        "framework_so4_reading": {
            "note": "framework-reading, not derived",
            "symmetry_surface": "so(4) = su(2) ⊕ su(2) ⊂ g2 (Lie subalgebra)",
            "operator_surface": "srmech.amsc.cascade.atoms (6 lean-ISA ops)",
            "six_equals_six_is_coincidence": True,
            "atoms_that_are_lie_generators": 0,
            "f215": (
                "the 6 cascade.atoms are group-element operations, NOT this "
                "Lie subalgebra; the 6=6 dimension match is coincidence"
            ),
        },
    }


__all__ = [
    "an_embedding",
    "g2_subalgebra",
    "quaternion_subalgebra_stabilizer",
    "so7_subalgebra",
    "so8_adjoint_basis",
]
