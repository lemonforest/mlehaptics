"""srmech.amsc.cascade.matrix_cascades — QR / SVD / lstsq / einsum / eig as A-N cascades.

Per ``docs/srmech/notes/continuous_math_as_14_class_cascade.md``: the matrix
factorizations and solvers are not numpy-``linalg`` primitives, they are
compositions of the 14 A-N class operations built on srmech's own roots
(:func:`srmech.amsc.rational.sqrt` / :func:`~srmech.amsc.rational.hypot`) and
its own Hermitian eigendecomposition
(:func:`srmech.amsc.laplacian.hermitian_eigendecompose`, the cyclic-Jacobi
Class-L cascade). numpy is used ONLY as the array CONTAINER (matmul / outer /
slicing = the Class-M bind layer) — **never** as the decomposition engine:
there is no ``the NumPy linalg family`` anywhere in the call graph.

- :func:`qr` — ``A = Q·R`` via **Householder reflections**. Q is a product
  (**Class M**) of elementary orthogonal reflectors ``H = I − β v vᴴ``; each
  reflector is **Class K** (the sign-flip across a hyperplane) ∘ **Class M**
  (the outer-product ``v vᴴ`` bind) ∘ **Class N** (the ``2/(vᴴv)`` scale,
  with the column norm a :func:`~srmech.amsc.rational.sqrt`). The Householder
  phase choice ``α = −phase·‖x‖`` is the **Class K** pin-slot that avoids
  cancellation.
- :func:`svd` — ``A = U·Σ·Vᴴ`` reached from the Hermitian eigendecomposition
  of the Gram matrix: **Class L** (eig of ``AᴴA`` or ``AAᴴ``) ∘ **Class N∘K**
  (``Σ = √eigvals``, the singular values) ∘ **Class M** (``U = A·V·Σ⁻¹``).
  The Gram route squares the condition number, so very small singular values
  carry ``√ε``-scale error (the documented caveat); the singular values
  themselves match ``NumPy SVD`` to round-off for well-conditioned
  inputs.
- :func:`lstsq` — least-squares ``min‖A x − b‖`` = **{QR}** factorization ∘
  **Class M** (the ``Qᴴ b`` product) ∘ **Class I** (back-substitution = the
  ordered/sequential triangular solve on ℤ).
- :func:`einsum` — the tensor contraction = **Class B/D** (the subscript spec
  is a typed pattern) ∘ **Class I** (iterate over index tuples) ∘ **Class M**
  (the sum-of-products bundle). The general index-iteration definition — it
  handles every subscript string (matmul / trace / transpose / dot / outer /
  arbitrary contraction), just unoptimised.
- :func:`eigvals` — non-Hermitian eigenvalues via the **shifted-QR
  iteration**: **Class K** (iterate-to-convergence asymptotic-DoF) ∘ **Class L**
  (the spectral content) ∘ **{QR}** (the per-step factorization) ∘ **Class C**
  (the Wilkinson spectral shifts). Runs in complex arithmetic, so it converges
  to complex eigenvalues of real matrices directly (no 2×2 real-block special
  case). Eigenvalues are unique as a SET; the multiset matches
  ``NumPy eigvals`` to ~1e-12 for moderate sizes.
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

# numpy-FREE (#564): the matrix factorisations operate on, and return, plain
# nested Python lists (matrices) / flat lists (vectors / eigenvalues). The heavy
# numpy-free engines live in :mod:`srmech.amsc.laplacian` over the
# :class:`~srmech.amsc.mat.Mat` carrier (native-dispatched, no numpy): ``svd`` /
# ``lstsq`` / ``eigvals`` delegate to ``mat_svd`` / ``mat_lstsq`` / ``mat_eigvals``;
# ``qr`` is a list-based Householder; ``einsum`` is the nested-list
# index-iteration definition. There is NO ``import numpy`` anywhere here.
from srmech.amsc import _native as _native  # rc140: real QR/SVD C dispatch (F2)
from srmech.amsc.mat import Mat as _Mat
from srmech.amsc.vec import Vec as _Vec  # rc131: 1-D carrier for singular values / vector solutions / eigenvalues
from srmech.amsc.laplacian import (
    mat_eigvals as _mat_eigvals,
    mat_lstsq as _mat_lstsq,
    mat_svd as _mat_svd,
)
from srmech.amsc.rational import hypot as _rhypot
from srmech.amsc.rational import sqrt as _rsqrt

__all__ = ["qr", "svd", "lstsq", "einsum", "eigvals", "char_poly", "eigvals_exact",
           "eigvec_exact", "eigvec_exact_float", "factor_integer_poly", "eig_exact",
           "jordan_chains_exact", "jordan_form_exact"]


def _modulus(z: complex) -> float:
    """|z| via the Class-N hypot cascade (no ``abs()`` — discipline).

    0.9.0rc7: ``rational.hypot`` now returns an exact ``Q``; this magnitude
    feeds the iterative FPU kernels below (Householder QR, the eigenvalue
    iteration), which converge by float round-off, so the root rotates to
    float at this subroutine boundary (a ``Q`` carried through the sweep would
    grow num/den unboundedly). The exact ``Q`` magnitude is the one EXACT
    consumers call directly; this is its float projection."""
    return float(_rhypot(float(z.real), float(z.imag)))


# ── numpy-free nested-list helpers (shape / index / build / collapse) ──────────
def _to_rows(a) -> List[List[complex]]:
    """A 2-D array-like → a nested ``list[list[complex]]`` (rows), numpy-free."""
    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    return [[complex(v) for v in r] for r in rows]


def _input_is_complex(a) -> bool:
    """True iff any leaf of the (possibly nested) array-like is a Python
    ``complex`` — the numpy-free stand-in for ``np.iscomplexobj`` (dtype-, not
    value-, based: ``complex(1, 0)`` still counts as complex INPUT)."""
    def _walk(x):
        if isinstance(x, complex):
            return True
        if isinstance(x, (list, tuple)):
            return any(_walk(e) for e in x)
        if hasattr(x, "tolist"):
            return _walk(x.tolist())
        return False
    return _walk(a)


def _all_imag_zero(nested, tol: float = 1e-12) -> bool:
    """True iff every complex leaf has ``|imag| <= tol`` (real-collapse gate)."""
    if isinstance(nested, (list, tuple)):
        return all(_all_imag_zero(e, tol) for e in nested)
    z = complex(nested)
    return -tol <= z.imag <= tol


def _real_of(nested):
    """Map every complex leaf to its real part (used after the imag-zero gate)."""
    if isinstance(nested, (list, tuple)):
        return [_real_of(e) for e in nested]
    return complex(nested).real


def _norm2(v: List[complex]) -> float:
    """Euclidean norm ‖v‖ = √(vᴴv) via the Class-N sqrt cascade — numpy-free.
    The sum-of-squares ``vᴴv = Σ|vᵢ|²`` is a Class-M self-bind; the root is
    :func:`srmech.amsc.rational.sqrt` (no ``abs``, no numpy norm engine)."""
    sq = 0.0
    for vi in v:
        z = complex(vi)
        sq += z.real * z.real + z.imag * z.imag
    # 0.9.0rc7: float-project the exact-Q root — this norm feeds the iterative
    # Householder QR (a float kernel; see ``_modulus``).
    return float(_rsqrt(sq)) if sq > 0.0 else 0.0


def qr(a, *, mode: str = "reduced") -> Tuple["_Mat", "_Mat"]:
    """Householder QR factorization ``A = Q·R`` (numpy-free, list-based).

    Parameters
    ----------
    a
        ``(m, n)`` real or complex 2-D array-like.
    mode
        ``"reduced"`` (default, matching ``NumPy QR``): ``Q`` is
        ``(m, k)``, ``R`` is ``(k, n)`` with ``k = min(m, n)``.
        ``"complete"``: ``Q`` is ``(m, m)``, ``R`` is ``(m, n)``.

    Returns
    -------
    (Q, R)
        A ``tuple`` of two numpy-free :class:`~srmech.amsc.mat.Mat` carriers
        (rc131; ``.shape`` + ``m[i, j]`` + a native C interleaved-buffer wire
        form), NOT bare nested lists — a Mat IS a C dense buffer, a list is not.
        ``Q`` has orthonormal columns (``Qᴴ Q = I``), ``R`` is upper triangular;
        Q·R reconstructs A to round-off. QR is unique only up to column/row
        signs, so ``Q``/``R`` need not match ``NumPy QR`` element-wise — the
        defining INVARIANTS (reconstruction, orthonormal Q, upper-triangular R)
        do. Real input with a real result yields real Mats (else complex Mats).
    """
    if mode not in ("reduced", "complete"):
        raise ValueError(f"mode must be 'reduced' or 'complete'; got {mode!r}")
    R = _to_rows(a)
    m = len(R)
    n = len(R[0]) if m else 0
    if any(len(r) != n for r in R):
        raise ValueError("qr: a must be a rectangular 2-D array-like")
    k = min(m, n)
    # rc140 (Foundation F2): a REAL input dispatches to the native Householder
    # ``srmech_qr_f64`` (direct, no iteration). ``qr_f64_c`` returns ``None`` on
    # a no-C host → the pure list-Householder below runs (the complete
    # alternative + parity oracle). Complex input stays on the list-Householder.
    if not _input_is_complex(a) and m > 0 and n > 0:
        native = _native.qr_f64_c([[R[i][j].real for j in range(n)]
                                   for i in range(m)])
        if native is not None:
            Qf, Rf = native                       # Q (m,m) real, R (m,n) real
            if mode == "reduced":
                Qf = [[Qf[i][c] for c in range(k)] for i in range(m)]  # (m, k)
                Rf = [Rf[i][:n] for i in range(k)]                     # (k, n)
            return (_Mat.from_rows(Qf, is_complex=False),
                    _Mat.from_rows(Rf, is_complex=False))
    Q = [[1 + 0j if i == j else 0j for j in range(m)] for i in range(m)]
    for j in range(k):
        x = [R[i][j] for i in range(j, m)]            # column j, rows j..m-1
        normx = _norm2(x)
        if normx == 0.0:
            continue
        x0 = x[0]
        modx0 = _modulus(x0)
        phase = (x0 / modx0) if modx0 > 0.0 else complex(1.0, 0.0)
        alpha = -phase * normx                        # Class K: pin-slot phase
        v = list(x)
        v[0] = x0 - alpha
        vhv = 0.0
        for vi in v:
            vhv += (vi.conjugate() * vi).real         # Class N: vᴴv (real)
        if vhv == 0.0:
            continue
        beta = 2.0 / vhv                              # Class N: 1/(vᴴv) scale
        # R[j:, :] ← (I − β v vᴴ) R[j:, :]  (Class M outer bind, numpy-free).
        vh_R = [sum(v[idx].conjugate() * R[j + idx][col] for idx in range(len(v)))
                for col in range(n)]                  # conj(v)·R over trailing rows
        for idx in range(len(v)):
            i = j + idx
            for col in range(n):
                R[i][col] -= beta * v[idx] * vh_R[col]
        # Q[:, j:] ← Q[:, j:] (I − β v vᴴ).
        Q_v = [sum(Q[row][j + t] * v[t] for t in range(len(v))) for row in range(m)]
        for row in range(m):
            for t in range(len(v)):
                Q[row][j + t] -= beta * Q_v[row] * v[t].conjugate()
    if mode == "reduced":
        Q = [[Q[i][c] for c in range(k)] for i in range(m)]
        R = [R[i][:n] for i in range(k)]
    real_input = not _input_is_complex(a)
    # rc131 carrier-format law: return Mat carriers, not bare nested lists.
    if real_input and _all_imag_zero(Q) and _all_imag_zero(R):
        return (_Mat.from_rows(_real_of(Q), is_complex=False),
                _Mat.from_rows(_real_of(R), is_complex=False))
    return (_Mat.from_rows(Q, is_complex=True),
            _Mat.from_rows(R, is_complex=True))


def svd(a, *, full_matrices: bool = False) -> Tuple["_Mat", "_Vec", "_Mat"]:
    """Singular value decomposition ``A = U·diag(s)·Vᴴ`` (numpy-free).

    Delegates to the Mat-carrier :func:`srmech.amsc.laplacian.mat_svd` (Gram
    ``AᴴA`` Hermitian-eigen route, native-dispatched, numpy-free) and slices its
    full ``(m, m)`` / ``(n, n)`` factors down to the reduced form.

    Parameters
    ----------
    a
        ``(m, n)`` real or complex 2-D array-like.
    full_matrices
        ``False`` (default, matching ``NumPy SVD``'s reduced form):
        ``U`` is ``(m, k)``, ``s`` is ``(k,)``, ``Vh`` is ``(k, n)`` with
        ``k = min(m, n)``.

    Returns
    -------
    (U, s, Vh)
        A ``tuple`` of numpy-free carriers (rc131): ``U`` / ``Vh`` as
        :class:`~srmech.amsc.mat.Mat` (``.shape`` + ``m[i, j]``) and the
        DESCENDING singular values ``s`` as a 1-D :class:`~srmech.amsc.vec.Vec`
        (``.shape == (k,)`` + scalar ``v[i]``) — NOT bare lists (a Mat/Vec IS a C
        dense buffer, a list is not). ``U``/``Vh`` have orthonormal columns/rows
        and reconstruct ``A`` (value-faithful, not bit-identical, to NumPy — the
        Gram route squares the condition number; see
        ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]``).
        Real input with a real result yields real ``U``/``Vh`` Mats.
    """
    if full_matrices:
        raise NotImplementedError(
            "matrix_cascades.svd supplies the reduced form (full_matrices="
            "False); the full orthonormal completion is the follow-on."
        )
    rows = _to_rows(a)
    m = len(rows)
    n = len(rows[0]) if m else 0
    k = min(m, n)
    if k == 0:
        return (_Mat.from_rows([[] for _ in range(m)] if m else [], is_complex=False),
                _Vec.from_sequence([], is_complex=False),
                _Mat.from_rows([], is_complex=False))
    is_cx = _input_is_complex(a)
    U_full, S, Vh_full = _mat_svd(_Mat.from_rows(rows, is_complex=is_cx))
    U_rows = U_full.tolist()                           # (m, m)
    Vh_rows = Vh_full.tolist()                         # (n, n)
    U = [[complex(U_rows[i][c]) for c in range(k)] for i in range(m)]   # (m, k)
    Vh = [[complex(Vh_rows[i][c]) for c in range(n)] for i in range(k)]  # (k, n)
    s = [float(S[j]) for j in range(k)]
    # rc131 carrier-format law: Mat for U/Vh, Vec for the 1-D singular values.
    s_vec = _Vec.from_sequence(s, is_complex=False)
    if not is_cx and _all_imag_zero(U) and _all_imag_zero(Vh):
        return (_Mat.from_rows(_real_of(U), is_complex=False), s_vec,
                _Mat.from_rows(_real_of(Vh), is_complex=False))
    return (_Mat.from_rows(U, is_complex=True), s_vec,
            _Mat.from_rows(Vh, is_complex=True))


def _qr_lstsq_real(a_real, b_real):
    """Real least-squares ``min‖A x − b‖`` via the native QR (Foundation F2).

    ``a_real`` is ``(m, n)`` (``m ≥ n``), ``b_real`` is ``(m, w)`` — both nested
    ``float`` lists. Returns the ``(n, w)`` solution as nested ``complex`` lists
    (imag 0) so the caller's carrier-format assembly is unchanged, OR ``None``
    when the native QR is absent OR ``R`` is rank-deficient (a zero diagonal
    pivot) — the caller then falls back to the pure normal-equations solve.

    Method (Golub & Van Loan §5.3.3): ``A = Q·R`` (reduced), then ``x`` solves
    the upper-triangular ``R x = Qᵀ b`` by back-substitution — the **{QR}**
    factorisation ∘ **Class M** (the ``Qᵀ b`` product) ∘ **Class I** (the
    ordered triangular solve)."""
    native = _native.qr_f64_c(a_real)
    if native is None:
        return None
    Q, R = native                                      # Q (m, m), R (m, n) real
    m = len(a_real)
    n = len(a_real[0]) if m else 0
    w = len(b_real[0]) if b_real else 0
    # Reduced factors: thin Q (m, n) columns, R (n, n) upper-triangular block.
    for i in range(n):
        if R[i][i] == 0.0:
            return None                                # rank-deficient → pure path
    x_rows = [[0j] * w for _ in range(n)]
    for c in range(w):
        # y = Qᵀ b[:, c]  (length n) — Class M projection onto the thin Q columns.
        y = [sum(Q[r][j] * b_real[r][c] for r in range(m)) for j in range(n)]
        # Back-substitution R x = y (Class I: ordered triangular solve).
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            acc = y[i] - sum(R[i][j] * x[j] for j in range(i + 1, n))
            x[i] = acc / R[i][i]
        for i in range(n):
            x_rows[i][c] = complex(x[i])
    return x_rows


def lstsq(a, b):
    """Least-squares solution of ``A x = b`` (minimising ``‖A x − b‖``), numpy-free.

    Delegates to the Mat-carrier :func:`srmech.amsc.laplacian.mat_lstsq` (the
    normal-equations ``(AᴴA)⁻¹Aᴴb`` over the native ``mat_*`` trio). Supports the
    overdetermined / square case ``m ≥ n`` (full column rank); ``b`` may be a
    vector ``(m,)`` or a stack of right-hand sides ``(m, k)``.

    Returns the solution ``x`` in the numpy-free **carrier** (rc131): a 1-D
    :class:`~srmech.amsc.vec.Vec` for a vector ``b`` (``.shape == (n,)`` + scalar
    ``v[i]``) or a :class:`~srmech.amsc.mat.Mat` for a matrix ``b`` (``.shape`` +
    ``m[i, j]``) — NOT a bare list (a Mat/Vec IS a C dense buffer, a list is not).
    Matches ``NumPy lstsq(a, b)[0]`` to round-off for full-rank inputs. Real
    input with a real result yields a real carrier.
    """
    arows = _to_rows(a)
    m = len(arows)
    n = len(arows[0]) if m else 0
    if m < n:
        raise NotImplementedError(
            "matrix_cascades.lstsq supplies the overdetermined/square (m>=n) "
            "normal-equations path; the underdetermined min-norm case is the "
            "follow-on."
        )
    b_list = b.tolist() if hasattr(b, "tolist") else b
    b_is_1d = not (b_list and isinstance(b_list[0], (list, tuple)))
    if b_is_1d:
        b_rows = [[complex(v)] for v in b_list]        # (m, 1) column
    else:
        b_rows = [[complex(v) for v in r] for r in b_list]
    is_cx = _input_is_complex(a) or _input_is_complex(b)
    # rc140 (Foundation F2): the REAL overdetermined/square path routes through
    # the native QR (``srmech_qr_f64``) — the numerically-preferred least-squares
    # method (Golub & Van Loan §5.3.3: solve ``R x = Qᵀ b``, more stable than the
    # normal equations, which square κ). A rank-deficient ``R`` (zero pivot) or a
    # no-C host returns ``None`` from ``_qr_lstsq_real`` → the pure normal-
    # equations ``mat_lstsq`` runs (the complete alternative + parity oracle).
    x_rows = None
    if not is_cx and m > 0 and n > 0:
        x_rows = _qr_lstsq_real(
            [[arows[i][j].real for j in range(n)] for i in range(m)],
            [[b_rows[i][j].real for j in range(len(b_rows[0]))] for i in range(m)],
        )
    if x_rows is None:
        A_mat = _Mat.from_rows(arows, is_complex=is_cx)
        B_mat = _Mat.from_rows(b_rows, is_complex=is_cx)
        X = _mat_lstsq(A_mat, B_mat)                    # Mat (n, w)
        x_rows = [[complex(X[i, j]) for j in range(X.n_cols)]
                  for i in range(X.n_rows)]
    real_out = (not _input_is_complex(a) and not _input_is_complex(b)
                and _all_imag_zero(x_rows))
    # rc131 carrier-format law: 1-D solution → Vec, 2-D stack of solutions → Mat.
    if b_is_1d:
        flat = [row[0] for row in x_rows]              # (n,)
        if real_out:
            flat = _real_of(flat)
        return _Vec.from_sequence(flat, is_complex=not real_out)
    rows_out = _real_of(x_rows) if real_out else x_rows
    return _Mat.from_rows(rows_out, is_complex=not real_out)


def einsum(subscripts: str, *operands):
    """Einstein-summation tensor contraction via the index-iteration definition
    (numpy-free, nested-list operands).

    **Class B/D** (the subscript string is a typed index-pattern spec) ∘
    **Class I** (iterate over every free + summed index tuple) ∘ **Class M**
    (the sum-of-products bundle). Handles any subscript string (``'ij,jk->ik'``
    matmul, ``'ii->'`` trace, ``'ij->ji'`` transpose, ``'i,i->'`` dot,
    ``'i,j->ij'`` outer, arbitrary contractions), unoptimised. Implicit output
    (no ``->``) follows numpy's rule: free labels (appearing once) in sorted
    order.

    Returns the numpy-free carrier matching the result rank (rc131): a 2-D result
    is a :class:`~srmech.amsc.mat.Mat`, a 1-D result is a
    :class:`~srmech.amsc.vec.Vec`, a rank-0 result is a plain ``float`` /
    ``complex`` scalar; a genuine rank-3+ tensor stays a nested ``list`` (no
    higher-rank carrier exists). A Mat/Vec IS a C dense buffer; a list is not.
    """
    ops = [_nd_to_lists(o) for o in operands]
    inspec, arrow, outspec = subscripts.replace(" ", "").partition("->")
    in_labels = inspec.split(",")
    if len(in_labels) != len(ops):
        raise ValueError(
            f"einsum: {len(in_labels)} operand specs but {len(ops)} operands"
        )
    sizes: Dict[str, int] = {}
    shapes = [_nd_shape(op) for op in ops]
    for labels, shape in zip(in_labels, shapes):
        if len(labels) != len(shape):
            raise ValueError(
                f"einsum: spec {labels!r} rank {len(labels)} != operand ndim "
                f"{len(shape)}"
            )
        for axis, lab in enumerate(labels):
            sizes[lab] = shape[axis]
    if arrow == "":                                   # implicit output (Class B/D)
        # Plain-dict label tally (the STOP-list forbids hand-rolled Counter()):
        # implicit einsum output = labels appearing exactly once, sorted.
        counts: Dict[str, int] = {}
        for lab in "".join(in_labels):
            counts[lab] = counts.get(lab, 0) + 1
        outspec = "".join(sorted(lab for lab in counts if counts[lab] == 1))
    summed = [lab for lab in sizes if lab not in outspec]
    out_shape = tuple(sizes[lab] for lab in outspec)
    out = _nd_zeros(out_shape)
    any_cx = any(_input_is_complex(o) for o in operands)
    free_ranges = [range(sizes[lab]) for lab in outspec]
    sum_ranges = [range(sizes[lab]) for lab in summed]

    def _accumulate(free_idx):
        index_map = dict(zip(outspec, free_idx))
        acc = 0j
        for sum_idx in itertools.product(*sum_ranges):  # Class I: summed indices
            index_map.update(zip(summed, sum_idx))
            term = complex(1.0, 0.0)
            for labels, op in zip(in_labels, ops):
                term *= _nd_get(op, tuple(index_map[lab] for lab in labels))  # Class M
            acc += term
        return acc

    if not out_shape:                                 # rank-0 output (trace / dot)
        scalar = _accumulate(())
        return scalar.real if (not any_cx and _all_imag_zero(scalar)) else scalar
    for free_idx in itertools.product(*free_ranges):  # Class I: free indices
        _nd_set(out, free_idx, _accumulate(free_idx))
    real_out = not any_cx and _all_imag_zero(out)
    result = _real_of(out) if real_out else out
    # rc131 carrier-format law: rank-1 → Vec, rank-2 → Mat, rank-3+ → nested list.
    rank = len(out_shape)
    if rank == 1:
        return _Vec.from_sequence(result, is_complex=not real_out)
    if rank == 2:
        return _Mat.from_rows(result, is_complex=not real_out)
    return result


# ── nested-list N-D tensor helpers for einsum (numpy-free) ─────────────────────
def _nd_to_lists(o):
    """An array-like (ndarray / nested list / scalar) → nested ``list``s."""
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, (list, tuple)):
        return [_nd_to_lists(e) for e in o]
    return o


def _nd_shape(o) -> Tuple[int, ...]:
    """Shape of a (possibly ragged-free) nested list — rank from nesting depth."""
    shape: List[int] = []
    cur = o
    while isinstance(cur, (list, tuple)):
        shape.append(len(cur))
        cur = cur[0] if len(cur) else None
    return tuple(shape)


def _nd_zeros(shape: Tuple[int, ...]):
    """A nested-list zero tensor of the given shape (rank-0 → a bare ``0j``)."""
    if not shape:
        return 0j
    return [_nd_zeros(shape[1:]) for _ in range(shape[0])]


def _nd_get(o, idx: Tuple[int, ...]):
    """Multi-index read into a nested list (empty idx → the scalar itself)."""
    cur = o
    for i in idx:
        cur = cur[i]
    return cur


def _nd_set(o, idx: Tuple[int, ...], value) -> None:
    """Multi-index write into a nested list. A rank-0 ``out`` cannot be set in
    place; the caller handles that by reading the single accumulated value."""
    if not idx:
        raise ValueError("_nd_set: cannot set a rank-0 tensor in place")
    cur = o
    for i in idx[:-1]:
        cur = cur[i]
    cur[idx[-1]] = value


def eigvals(a, *, max_sweeps: int = 500) -> "_Vec":
    """Eigenvalue MULTISET of a general (non-Hermitian) square matrix (numpy-free).

    Delegates to the Mat-carrier :func:`srmech.amsc.laplacian.mat_eigvals` — the
    shifted-QR iteration (**Class K** iterate-to-convergence ∘ **Class L**
    spectral content ∘ ``{QR}`` Householder ∘ **Class C** Wilkinson shift) in
    plain ``complex`` lists, native-dispatched ``RQ`` recombination, no numpy.

    Returns the length-``n`` eigenvalue multiset as a 1-D complex
    :class:`~srmech.amsc.vec.Vec` (rc131; ``.shape == (n,)`` + scalar ``v[i]``),
    NOT a bare ``list[complex]`` — a Vec IS a C dense buffer, a list is not. The
    eigenvalues are unique only as a SET; the multiset matches ``NumPy eigvals``
    to ~1e-9 for moderate sizes.
    """
    rows = _to_rows(a)
    n = len(rows)
    if any(len(r) != n for r in rows):
        raise ValueError(f"a must be square 2-D; got {n} rows")
    if n == 0:
        return _Vec.from_sequence([], is_complex=True)
    eigs = _mat_eigvals(_Mat.from_rows(rows, is_complex=True), max_sweeps=max_sweeps)
    # rc131 carrier-format law: the 1-D eigenvalue multiset returns as a Vec.
    return _Vec.from_sequence(eigs, is_complex=True)


def _char_poly_int(A: List[List[int]], n: int) -> List[int]:
    """Faddeev–LeVerrier on an integer matrix → exact integer monic char-poly.

    Each ``c_k = -trace(A·M_k)/k`` is an exact integer (a Faddeev–LeVerrier
    theorem: ``trace(A·M_k)`` is divisible by ``k`` for integer ``A``); the
    ``% k`` assert is the Class-K exactness guard (never a float division)."""
    M = [[1 if i == j else 0 for j in range(n)] for i in range(n)]  # M_1 = I
    coeffs: List[int] = [1]
    for k in range(1, n + 1):
        AM = [[sum(A[i][t] * M[t][j] for t in range(n)) for j in range(n)]
              for i in range(n)]
        tr = sum(AM[i][i] for i in range(n))
        assert tr % k == 0, "Faddeev-LeVerrier integer invariant violated"
        ck = -(tr // k)
        coeffs.append(ck)
        M = [[AM[i][j] + (ck if i == j else 0) for j in range(n)] for i in range(n)]
    return coeffs


def _char_poly_float(rows: List[List[complex]], n: int) -> List[complex]:
    """Faddeev–LeVerrier in complex float (the non-integer fallback)."""
    A = [[complex(v) for v in r] for r in rows]
    M = [[1 + 0j if i == j else 0j for j in range(n)] for i in range(n)]
    coeffs: List[complex] = [1 + 0j]
    for k in range(1, n + 1):
        AM = [[sum(A[i][t] * M[t][j] for t in range(n)) for j in range(n)]
              for i in range(n)]
        tr = sum(AM[i][i] for i in range(n))
        ck = -tr / k
        coeffs.append(ck)
        M = [[AM[i][j] + (ck if i == j else 0) for j in range(n)] for i in range(n)]
    return coeffs


def char_poly(a) -> List:
    """Exact integer characteristic polynomial ``det(xI - A)`` (Faddeev–LeVerrier).

    For an **integer** matrix this returns the EXACT integer coefficients of the
    monic characteristic polynomial (high→low: ``[1, c1, …, cn]``) in
    arbitrary-precision integer arithmetic — the exact ALGEBRAIC substrate of the
    eigenproblem: the exact trace (``= -c1``), the exact determinant
    (``= (-1)^n · c_n``), and all elementary symmetric functions of the spectrum,
    with **no floating point**.

    The eigenvalues are the ROOTS of this exact polynomial — but unlike the DFT's
    well-conditioned lift, extracting roots from polynomial COEFFICIENTS is
    ill-conditioned (Wilkinson), so :func:`eigvals` keeps its direct float
    eigensolver and this op exposes the exact polynomial rather than rerouting the
    eigenvalues. A non-integer (or complex) matrix falls back to a float
    Faddeev–LeVerrier. Pure-Python; numpy is a container only.

    **Class L** (spectral / algebraic content) ∘ **Class M** (the matrix-product
    + trace accumulate) ∘ **Class K** (the exact ``// k`` step division).
    """
    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    if n == 0:
        return [1]
    if any(len(r) != n for r in rows):
        raise ValueError(f"char_poly: a must be square 2-D; got {n}x{len(rows[0])}")
    real_integer = True
    for r in rows:
        for v in r:
            vr = v.real if hasattr(v, "real") else v
            vi = v.imag if hasattr(v, "imag") else 0
            if vi != 0 or int(vr) != vr:
                real_integer = False
                break
        if not real_integer:
            break
    if real_integer:
        A = [[int(v.real) if hasattr(v, "real") else int(v) for v in r] for r in rows]
        return _char_poly_int(A, n)
    return _char_poly_float(rows, n)


# ── exact real-eigenvalue cascade: char-poly → Sturm isolation → bisection ──────
# The eigenvalues of an integer matrix are ALGEBRAIC numbers, not transcendental:
# the Wilkinson ill-conditioning of "float root-finding from char-poly
# coefficients" is a float-perturbation artifact, NOT inherent. Kept in EXACT
# integer/rational arithmetic the whole way — char_poly (Class L∘M∘K) → Sturm
# sign-sequence isolation (Class C sign-count at Class K interval pin-slots) →
# rational bisection (Class N anchors → the algebraic asymptote) → one FPU lift —
# the eigenvalues come out exact-to-arbitrary-precision and well-conditioned.

from fractions import Fraction as _FR  # noqa: E402  (exact rational substrate)


def _poly_trim(p: List) -> List:
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p


def _poly_deriv(p: List) -> List:
    return _poly_trim([p[i] * i for i in range(1, len(p))]) if len(p) > 1 else [_FR(0)]


def _poly_divmod(a: List, b: List) -> Tuple[List, List]:
    """Exact polynomial division over ℚ → (quotient, remainder)."""
    a = _poly_trim(list(a))
    b = _poly_trim(b)
    q = [_FR(0)] * max(len(a) - len(b) + 1, 1)
    while len(a) >= len(b) and any(x != 0 for x in a):
        c = a[-1] / b[-1]
        d = len(a) - len(b)
        q[d] = c
        for i in range(len(b)):
            a[d + i] -= c * b[i]
        a = _poly_trim(a)
        if a == [_FR(0)]:
            break
    return _poly_trim(q), _poly_trim(a)


def _poly_gcd(a: List, b: List) -> List:
    a = _poly_trim(a)
    b = _poly_trim(b)
    while _poly_trim(b) != [_FR(0)]:
        _, r = _poly_divmod(a, b)
        a, b = b, r
    if a[-1] != 0:                                   # normalise monic
        a = [c / a[-1] for c in a]
    return _poly_trim(a)


def _poly_sub(a: List, b: List) -> List:
    n = max(len(a), len(b))
    return _poly_trim([(a[i] if i < len(a) else _FR(0)) - (b[i] if i < len(b) else _FR(0))
                       for i in range(n)])


def _square_free_factors(p: List) -> List[Tuple[List, int]]:
    """Yun square-free factorisation → ``[(factor_k, k)]`` where ``factor_k`` is
    the product of the roots of EXACT multiplicity ``k`` (so an eigenvalue of
    multiplicity ``k`` is a degree-1 factor at ``k``)."""
    p = _poly_trim(p)
    a = _poly_gcd(p, _poly_deriv(p))
    b, _ = _poly_divmod(p, a)
    c, _ = _poly_divmod(_poly_deriv(p), a)
    d = _poly_sub(c, _poly_deriv(b))
    out: List[Tuple[List, int]] = []
    k = 1
    while len(b) > 1:
        g = _poly_gcd(b, d)
        if len(g) > 1:
            out.append((g, k))
        b, _ = _poly_divmod(b, g)
        c, _ = _poly_divmod(d, g)
        d = _poly_sub(c, _poly_deriv(b))
        k += 1
    return out


def _sturm_chain(p: List) -> List[List]:
    chain = [_poly_trim(p), _poly_deriv(p)]
    while len(chain[-1]) > 1:
        _, r = _poly_divmod(chain[-2], chain[-1])
        if _poly_trim(r) == [_FR(0)]:
            break
        chain.append([-x for x in r])
    return chain


def _poly_eval(p: List, x):
    s = _FR(0)
    for c in reversed(p):
        s = s * x + c
    return s


def _sturm_V(chain: List[List], x) -> int:
    signs = [1 if v > 0 else -1 for v in (_poly_eval(p, x) for p in chain) if v != 0]
    return sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])


def _mag(x):
    """Class-K magnitude: the sign-branch ``x if x >= 0 else -x``, never the ALU
    builtin. Sign is the pin-slot (Class K) re-applied as Class C — discipline."""
    return x if x >= 0 else -x


def _isolate_real_roots(factor: List, bits: int) -> List[Tuple]:
    """Sturm-isolate the DISTINCT real roots of a square-free ``factor`` and
    bisect each to width ``< 2^-bits``. Returns ``(lo, hi)`` Fraction intervals."""
    chain = _sturm_chain(factor)
    lead = _mag(factor[-1])
    bound = _FR(1) + max((_mag(c) / lead for c in factor[:-1]), default=_FR(0))
    eps = _FR(1, 1 << bits)
    out: List[Tuple] = []
    stack = [(-bound, bound)]
    while stack:
        a, b = stack.pop()
        cnt = _sturm_V(chain, a) - _sturm_V(chain, b)
        if cnt == 0:
            continue
        if cnt == 1:
            while b - a > eps:                       # Class N anchors → asymptote
                m = (a + b) / 2
                if _sturm_V(chain, a) - _sturm_V(chain, m) == 1:
                    b = m
                else:
                    a = m
            out.append((a, b))
        else:
            m = (a + b) / 2                           # Class K pin-slot split
            stack.append((a, m))
            stack.append((m, b))
    return out


# ── exact COMPLEX-root isolation: the argument-principle box-count (rc24, rc-E) ──
# The exact REAL eigenvalues come out of the Sturm cascade above; the COMPLEX ones
# (conjugate pairs of an integer char-poly) are isolated by the SAME exact-substrate
# discipline — PURE rational-box subdivision over the upper half-plane
# (``_isolate_complex_roots_upper``), with NO float-QR candidate seeding: each box
# is CERTIFIED with the argument principle — the number of roots of an integer
# polynomial strictly inside an open rational box equals the winding number of p
# around the box boundary, computed in EXACT ``Fraction`` arithmetic (no float in
# the count). Along each edge ``p`` restricts to ``U(t)+iV(t)`` with U,V ∈ ℚ[t];
# the boundary change-of-argument is the sum of the per-edge Cauchy indices of
# ``V/U`` (a Sturm-style sign-variation count, the same machinery as the real
# isolation). The float is the single terminal projection of the exact box center.


def _poly_real_imag_on_edge(p: List, x0, y0, dx, dy) -> Tuple[List, List]:
    """For ``z(t) = (x0 + dx·t) + i·(y0 + dy·t)`` substitute into the integer/ℚ
    polynomial ``p`` (low→high) and return ``(U, V)`` — the real/imag parts as
    polynomials in ``t`` over ℚ. Exact: ``z = a(t) + i·b(t)`` with
    ``a = x0 + dx·t``, ``b = y0 + dy·t``; powers of ``z`` are accumulated by
    complex multiply of the (U, V) pair, all in ``Fraction``."""
    a = [_FR(x0), _FR(dx)]                            # real part of z(t)
    b = [_FR(y0), _FR(dy)]                            # imag part of z(t)
    U = [_FR(0)]
    V = [_FR(0)]
    powU = [_FR(1)]                                   # z^0 = 1 + 0i
    powV = [_FR(0)]
    for coeff in p:                                   # low→high: coeff · z^k
        c = _FR(coeff)
        U = _poly_add(U, [c * t for t in powU])
        V = _poly_add(V, [c * t for t in powV])
        # powU+i·powV ← (powU+i·powV)·(a+i·b)
        ra = _poly_sub(_poly_mul(powU, a), _poly_mul(powV, b))
        rb = _poly_add(_poly_mul(powU, b), _poly_mul(powV, a))
        powU, powV = ra, rb
    return _poly_trim(U), _poly_trim(V)


def _poly_add(a: List, b: List) -> List:
    n = max(len(a), len(b))
    return _poly_trim([(a[i] if i < len(a) else _FR(0)) + (b[i] if i < len(b) else _FR(0))
                       for i in range(n)])


def _poly_mul(a: List, b: List) -> List:
    a = _poly_trim(a)
    b = _poly_trim(b)
    out = [_FR(0)] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        if av == 0:
            continue
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return _poly_trim(out)


def _sturm_seq_general(f: List, g: List) -> List[List]:
    """The generalised Sturm (Sturm–Habicht-style) remainder sequence starting
    ``f, g`` — ``s0 = f``, ``s1 = g``, ``s_{k+1} = −rem(s_{k−1}, s_k)`` — used for
    the Cauchy index of ``g/f``. Pure ℚ; terminates when the remainder is 0."""
    seq = [_poly_trim(f), _poly_trim(g)]
    while _poly_trim(seq[-1]) != [_FR(0)]:
        _, r = _poly_divmod(seq[-2], seq[-1])
        r = _poly_trim(r)
        if r == [_FR(0)]:
            break
        seq.append([-x for x in r])
    return seq


def _cauchy_index_open(f: List, g: List, a, b) -> int:
    """The Cauchy index ``I_a^b(g/f)`` over the OPEN interval ``(a, b)`` — the
    number of −∞→+∞ jumps minus +∞→−∞ jumps of ``g/f`` as ``t`` runs ``a → b``.
    Equals ``V(a) − V(b)`` of the generalised Sturm sequence sign-variation count
    (``f, g, −rem, …``) evaluated at the endpoints. Exact ℚ."""
    seq = _sturm_seq_general(f, g)
    return _sturm_V(seq, a) - _sturm_V(seq, b)


def _count_roots_in_box(p: List, x0, x1, y0, y1) -> int:
    """The number of roots (with multiplicity) of the integer/ℚ polynomial ``p``
    (coeffs **low→high**) STRICTLY inside the open rational box
    ``(x0, x1) × (y0, y1)`` — the **argument principle** in EXACT ``Fraction``
    arithmetic (no float in the count). The winding number of ``p`` around the
    rectangular boundary (traversed counter-clockwise) equals that root count.

    Along each edge, ``p(z(t)) = U(t) + i·V(t)`` with ``U, V ∈ ℚ[t]``; the change
    of argument over the edge is ``−π · I(V/U)`` (the Cauchy index of ``V/U`` over
    the edge), so the total winding ``= −½ · Σ_edges I_edge(V/U)``. The caller must
    supply rational corners whose boundary is root-free (generic rationals miss the
    algebraic roots); a root ON the boundary makes the count ill-defined — nudge
    the corners. Returns a non-negative ``int``.

    **Class L** (the spectral root count) ∘ **Class C** (the per-edge Cauchy-index
    sign-count) ∘ **Class K** (the ℚ interval pin-slots). See Henrici,
    *Applied and Computational Complex Analysis* vol. 1 §6.2 (the argument
    principle by Cauchy-index summation over a polygon).
    """
    p = [_FR(c) for c in p]
    if _poly_trim(p) == [_FR(0)]:
        raise ValueError("_count_roots_in_box: zero polynomial has no isolated roots")
    x0, x1, y0, y1 = _FR(x0), _FR(x1), _FR(y0), _FR(y1)
    if not (x0 < x1 and y0 < y1):
        raise ValueError("_count_roots_in_box: need x0 < x1 and y0 < y1")
    # The four edges as (x_start, y_start, dx, dy), parameter t in [0, 1],
    # traversed counter-clockwise: bottom → right → top → left.
    edges = (
        (x0, y0, x1 - x0, _FR(0)),                    # bottom: y = y0, x: x0→x1
        (x1, y0, _FR(0), y1 - y0),                    # right:  x = x1, y: y0→y1
        (x1, y1, x0 - x1, _FR(0)),                    # top:    y = y1, x: x1→x0
        (x0, y1, _FR(0), y0 - y1),                    # left:   x = x0, y: y1→y0
    )
    total_index = 0
    for (xs, ys, dx, dy) in edges:
        U, V = _poly_real_imag_on_edge(p, xs, ys, dx, dy)
        # A boundary root would make U and V vanish simultaneously somewhere on
        # the edge → gcd(U, V) non-constant. The caller is told to nudge corners;
        # guard so an on-boundary corner cannot silently corrupt the count.
        if _poly_trim(U) == [_FR(0)] and _poly_trim(V) == [_FR(0)]:
            raise ValueError(
                "_count_roots_in_box: p vanishes on an entire edge — degenerate "
                "box (corners hit a root); nudge the rational corners")
        # Cauchy index over the OPEN edge (0, 1); the corners are the box vertices,
        # which the caller keeps root-free.
        total_index += _cauchy_index_open(U, V, _FR(0), _FR(1))
    # winding = −½ · Σ I_edge ; the box is traced counter-clockwise so a root
    # inside contributes +1 to the winding ⇒ the magnitude is the count.
    n2 = -total_index
    if n2 % 2 != 0:
        raise ValueError(
            "_count_roots_in_box: half-integer winding — a root lies ON the box "
            "boundary; nudge the rational corners")
    count = n2 // 2
    if count < 0:
        raise ValueError(
            "_count_roots_in_box: negative winding — boundary orientation/edge "
            "bug or a boundary root; nudge the corners")
    return count


def _cauchy_root_bound(p: List) -> _FR:
    """A rational bound ``B`` with every root of ``p`` (low→high) satisfying
    ``|root| < B`` — the Cauchy bound ``1 + max|a_i / a_n|``. Exact ℚ, Class-K
    magnitude (sign-branch, no ``abs()``)."""
    p = _poly_trim([_FR(c) for c in p])
    lead = _mag(p[-1])
    return _FR(1) + max((_mag(c) / lead for c in p[:-1]), default=_FR(0))


def _isolate_complex_roots_upper(p: List, want: int, bits: int) -> List[complex]:
    """Exactly isolate the ``want`` roots of the integer/ℚ polynomial ``p`` in the
    OPEN UPPER half-plane (im > 0) by recursive rational-box subdivision, certified
    by :func:`_count_roots_in_box` (exact argument principle — no float in the
    count), each refined to ``bits`` of precision. This is the ONLY complex-root
    path (rc28): pure exact subdivision over a square-free factor, with NO float-QR
    candidate seeding — so it is robust where a float QR would stall (e.g. a cyclic
    permutation matrix). Returns the box centers as ``complex`` (im > 0). The
    conjugates (im < 0) are the caller's mirror."""
    B = _cauchy_root_bound(p)
    # The upper-half search box: x ∈ (−B, B), y ∈ (η, B) with a small positive η so
    # the real axis (where the real roots live) is excluded. η is a generic small
    # rational; jitter the box corners so they miss the algebraic roots.
    eta = _FR(1, 1 << 24)
    jx = _FR(1, 997)
    jy = _FR(1, 991)
    found: List[Tuple[_FR, _FR]] = []
    # work-stack of (x0, x1, y0, y1, expected_count); seed with the whole strip.
    x0, x1, y0, y1 = -B - jx, B + jx, eta, B + jy
    try:
        total = _count_roots_in_box(p, x0, x1, y0, y1)
    except ValueError:
        # a corner/edge hit a root — nudge and retry once with a different jitter.
        x0, x1, y0, y1 = -B - _FR(1, 503), B + _FR(1, 509), eta, B + _FR(1, 521)
        total = _count_roots_in_box(p, x0, x1, y0, y1)
    stack = [(x0, x1, y0, y1, total)]
    guard = 0
    while stack:
        guard += 1
        if guard > 20000:
            # The only callers pass a SQUARE-FREE polynomial (rc28), whose roots are
            # all simple → subdivision always separates them well under this bound. A
            # non-square-free input (a coincident root) would spin forever here with
            # exploding Fraction denominators, so fail FAST rather than hang.
            raise ValueError("_isolate_complex_roots_upper: subdivision did not "
                             "terminate (input must be square-free)")
        bx0, bx1, by0, by1, cnt = stack.pop()
        if cnt == 0:
            continue
        wx, wy = bx1 - bx0, by1 - by0
        if cnt == 1 and wx <= _FR(1) and wy <= _FR(1):
            # isolated → refine to bits via root-free-cut bisection.
            cx, cy = _refine_box(p, bx0, bx1, by0, by1, bits)
            found.append((cx, cy))
            continue
        # split the longer axis at a root-free cut near the midpoint.
        if wx >= wy:
            cut = _root_free_split(p, bx0, bx1, by0, by1, axis="x")
            left = _count_roots_in_box(p, bx0, cut, by0, by1)
            right = cnt - left
            if left:
                stack.append((bx0, cut, by0, by1, left))
            if right:
                stack.append((cut, bx1, by0, by1, right))
        else:
            cut = _root_free_split(p, bx0, bx1, by0, by1, axis="y")
            bottom = _count_roots_in_box(p, bx0, bx1, by0, cut)
            top = cnt - bottom
            if bottom:
                stack.append((bx0, bx1, by0, cut, bottom))
            if top:
                stack.append((bx0, bx1, cut, by1, top))
    return [complex(float(cx), float(cy)) for (cx, cy) in found]


def _root_free_split(p: List, x0, x1, y0, y1, axis: str) -> _FR:
    """A cut value near the midpoint of the chosen ``axis`` of the box such that
    BOTH resulting sub-boxes have a well-defined root count (no root on the cut).
    Jitters off the midpoint until :func:`_count_roots_in_box` does not raise."""
    lo, hi = (x0, x1) if axis == "x" else (y0, y1)
    span = hi - lo
    for k in range(80):
        frac = _FR(1, 2) + _FR((k * 13 + 5) % 101 - 50, 1 << 11)
        if frac <= 0 or frac >= 1:
            continue
        cut = lo + span * frac
        try:
            if axis == "x":
                _count_roots_in_box(p, x0, cut, y0, y1)
                _count_roots_in_box(p, cut, x1, y0, y1)
            else:
                _count_roots_in_box(p, x0, x1, y0, cut)
                _count_roots_in_box(p, x0, x1, cut, y1)
        except ValueError:
            continue
        return cut
    raise ValueError("_root_free_split: no root-free cut found")


def _refine_box(p: List, x0, x1, y0, y1, bits: int) -> Tuple[_FR, _FR]:
    """Refine an isolating box (guaranteed to hold exactly ONE root) to half-width
    ``< 2^-bits`` by root-free-cut bisection; return the box center ``(re, im)``.

    Each step takes ONE jittered cut near the midpoint of the longer axis and ONE
    :func:`_count_roots_in_box` on the lower/left sub-box (count 1 → keep it, else
    keep the complement) — re-jittering only on the boundary-root guard. The cut
    is a low-denominator rational (the jitter is a coarse dyadic-ish fraction) so
    the ``Fraction`` numerators stay small as the box shrinks."""
    eps = _FR(1, 1 << bits)
    lo_x, hi_x, lo_y, hi_y = x0, x1, y0, y1
    # A short cycle of jitter fractions near 1/2 — generic enough to miss the root,
    # low-denominator to keep the Fractions small.
    jitters = (_FR(1, 2), _FR(127, 256), _FR(129, 256), _FR(63, 128), _FR(65, 128),
               _FR(31, 64), _FR(33, 64), _FR(509, 1024), _FR(515, 1024))
    while (hi_x - lo_x) > eps or (hi_y - lo_y) > eps:
        x_axis = (hi_x - lo_x) >= (hi_y - lo_y)
        lo, hi = (lo_x, hi_x) if x_axis else (lo_y, hi_y)
        span = hi - lo
        chosen = None
        for fr in jitters:
            cut = lo + span * fr
            try:
                if x_axis:
                    c = _count_roots_in_box(p, lo_x, cut, lo_y, hi_y)
                else:
                    c = _count_roots_in_box(p, lo_x, hi_x, lo_y, cut)
            except ValueError:
                continue
            chosen = (cut, c)
            break
        if chosen is None:
            raise ValueError("_refine_box: no root-free refinement cut found")
        cut, c = chosen
        if x_axis:
            if c == 1:
                hi_x = cut
            else:
                lo_x = cut
        else:
            if c == 1:
                hi_y = cut
            else:
                lo_y = cut
    return ((lo_x + hi_x) / 2, (lo_y + hi_y) / 2)


def eigvals_exact(a, *, bits: int = 64, return_intervals: bool = False,
                  include_complex: bool = False):
    """Exact eigenvalues of an integer matrix — the well-conditioned
    exact-until-rotation cascade (no Wilkinson ill-conditioning).

    ``char_poly`` (exact integer) → Yun square-free factorisation (exact
    multiplicities) → **Sturm** sign-sequence isolation (**Class C** sign-count at
    **Class K** interval boundaries) → rational **bisection** (**Class N** anchors
    → the algebraic asymptote), kept in exact ``Fraction`` arithmetic the whole
    way. Each eigenvalue stays an exact algebraic number until the single FPU
    lift. ``bits`` sets the refinement precision; ``return_intervals=True`` yields
    the exact ``(lo, hi)`` rational isolating intervals (real eigenvalues only)
    instead of floats.

    With ``include_complex=False`` (default) returns ONLY the real eigenvalues
    ascending **with multiplicity** — byte-for-byte the historic behaviour. A
    symmetric integer matrix has an all-real spectrum (complete); a matrix with
    complex eigenvalues returns only its real ones here — compare ``len(...)`` to
    the matrix order to detect that case.

    With ``include_complex=True`` the COMPLEX eigenvalues are ALSO returned,
    **exactly isolated** by PURE rational-box subdivision over the upper half-plane
    (:func:`_isolate_complex_roots_upper`), per square-free factor (rc28), with NO
    float-QR candidate seeding. Each box is CERTIFIED as holding exactly one root of
    the exact integer characteristic polynomial by the argument-principle count
    :func:`_count_roots_in_box` (winding number in exact ``Fraction`` arithmetic —
    no float in the count), then refined to ``bits`` of precision; the emitted
    ``complex`` is the single terminal projection of the certified box center (the
    exact-substrate object is the integer char-poly + the certified isolating box).
    This is exact isolation — qualitatively distinct from the unconditioned float-QR
    spectrum of :func:`~srmech.amsc.laplacian.mat_eigvals` (which is not consulted
    here at all). Conjugate symmetry holds (``a+bi`` with ``b>0`` pairs with
    ``a−bi``). Returns
    **all n** eigenvalues with multiplicity: the reals first (ascending, as
    ``float``), then the complex (sorted by ``(re, im)``, as ``complex``).
    ``return_intervals`` is honoured for the real part only and ignored for the
    complex part (a box, not an interval).

    **Class L** (the spectral content) ∘ **Class C** (the Cauchy-index winding) ∘
    **Class K** (the ℚ box/interval pin-slots) ∘ **Class N** (the rational
    refinement anchors).
    """
    cp = char_poly(a)                                # monic, high→low
    p = [_FR(c) for c in reversed(cp)]               # low→high over ℚ
    eigs: List[Tuple] = []
    for factor, mult in _square_free_factors(p):
        for (lo, hi) in _isolate_real_roots(factor, bits):
            for _ in range(mult):
                eigs.append((lo, hi))
    eigs.sort(key=lambda iv: iv[0] + iv[1])
    # ``return_intervals`` yields the exact real isolating intervals; it applies to
    # the real spectrum only (a complex root is a box, not an interval), so it is
    # honoured solely on the real-only path and ignored when include_complex=True.
    if return_intervals and not include_complex:
        return eigs
    real_out = [float((lo + hi) / 2) for (lo, hi) in eigs]
    if not include_complex:
        return real_out

    # ── complex eigenvalues: isolate PER SQUARE-FREE FACTOR (rc28 fix) ─────────
    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    n_real = len(eigs)
    if n_real == n:                                   # all-real spectrum — done
        return real_out
    n_complex = n - n_real                            # comes in conjugate pairs
    want_upper = n_complex // 2
    # MIRROR THE REAL PATH: isolate the complex roots PER SQUARE-FREE FACTOR.
    # ``_square_free_factors(p)`` returns ``[(factor, mult)]`` where each ``factor``
    # is SQUARE-FREE — so ALL its roots are SIMPLE. Box-subdivision can only ever
    # separate SIMPLE roots (a coincident pair has count ≥ 2 in EVERY enclosing box,
    # so the isolators would spin to their guards — the rc28 hang). Isolating the
    # upper-half (im > 0) roots of each square-free factor therefore ALWAYS
    # terminates; each isolated root is emitted ``mult`` times (and its conjugate
    # ``mult`` times), exactly as the real path appends each simple real root
    # ``mult`` times. There is NO float-QR candidate seeding on this path (rc28): the
    # whole branch routes through the always-terminating per-factor
    # ``_isolate_complex_roots_upper`` — pure exact subdivision, correctness- and
    # termination-first (a candidate-seeded accelerator must never run on a
    # non-square-free polynomial, where it would loop on a coincident pair).
    certified: List[complex] = []
    certified_upper = 0
    for factor, mult in _square_free_factors(p):
        deg = len(_poly_trim(factor)) - 1
        if deg < 2:                                   # deg ≤ 1 → only a real root
            continue
        # this square-free factor's upper-half complex count =
        # (deg − #real_roots) // 2 (real roots come in singles, complex in pairs).
        n_real_factor = len(_isolate_real_roots(factor, bits))
        want_upper_factor = (deg - n_real_factor) // 2
        if want_upper_factor == 0:
            continue
        # factor is SQUARE-FREE → all roots simple → isolation ALWAYS terminates.
        upper_roots = _isolate_complex_roots_upper(factor, want_upper_factor, bits)
        if len(upper_roots) != want_upper_factor:
            raise ValueError(
                f"eigvals_exact: certified {len(upper_roots)} upper-half complex "
                f"roots of a square-free factor but expected {want_upper_factor}")
        for z in upper_roots:
            for _ in range(mult):                     # mirror the real path's mult
                certified.append(complex(z.real, z.imag))
                certified.append(complex(z.real, -z.imag))   # conjugate (im < 0)
            certified_upper += mult
    # Reconcile the summed per-factor multiplicities with the char-poly count.
    if certified_upper != want_upper:
        raise ValueError(
            f"eigvals_exact: certified {certified_upper} upper-half complex roots "
            f"but the char-poly multiplicity expects {want_upper} "
            f"(n={n}, real={n_real})")
    certified.sort(key=lambda z: (z.real, z.imag))
    return real_out + certified


# ── exact EIGENVECTORS over ℚ(λ) = Qalg: null space of A−λI by exact RREF ────────
# The exact eigenvalues `eigvals_exact` give the spectrum; their EIGENVECTORS are
# the genuinely-new rc-D capability. For an integer/rational matrix A and an
# eigenvalue λ that is a root of an IRREDUCIBLE integer polynomial m, ℚ(λ) =
# ℚ[x]/(m) is a FIELD, so the eigenvector lives in the null space of (A − λI) over
# that field. We represent λ as a `Qalg` over m, build M = A − λI with Qalg
# entries, and do EXACT Gaussian elimination over the Qalg field — every pivot
# operation is exact-`Q` (rotation-last: the body stays exact; the ONE terminal
# rotation is `.to_complex()`/`.to_float()` per component in eigvec_exact_float).
# This is the Tajima–Ohara–Terui regime (S. Tajima, K. Ohara, A. Terui, "An
# extension and efficient calculation of the Horner's rule for matrices" /
# exact eigenvector computation via the minimal annihilating polynomial,
# arXiv:1811.09149) done as a DIRECT exact null-space.


def _eigvec_exact_qalg(a, lam):
    """The shared exact engine: returns ``(null_vectors, Qalg_one, free_cols)``
    where ``null_vectors`` is a ``list[list[Qalg]]`` (one per free column = a
    basis of the null space of ``A − λI`` over ℚ(λ)). See :func:`eigvec_exact`
    for the public contract."""
    # Lazy import (avoid any circular-import risk at module load; mirrors the
    # laplacian.py exact route).
    from srmech.amsc.qalg import Qalg

    if not isinstance(lam, Qalg):
        raise TypeError(
            "eigvec_exact: lam must be a Qalg eigenvalue (carrying its "
            f"irreducible m + embedding root); got {type(lam).__name__}")
    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    if n == 0:
        raise ValueError("eigvec_exact: a must be a non-empty square matrix")
    if any(len(r) != n for r in rows):
        raise ValueError(
            f"eigvec_exact: a must be square 2-D; got {n}x{len(rows[0])}")
    m = lam.m
    root = lam.root

    def _q_entry(v):
        """Coerce an integer/rational matrix entry to a constant ``Qalg`` over m."""
        vr = v.real if hasattr(v, "real") else v
        vi = v.imag if hasattr(v, "imag") else 0
        if vi != 0:
            raise ValueError(
                "eigvec_exact: a must be an integer/rational (real) matrix; "
                f"got complex entry {v!r}")
        if hasattr(vr, "numerator") and hasattr(vr, "denominator"):
            num, den = int(vr.numerator), int(vr.denominator)
        elif int(vr) == vr:
            num, den = int(vr), 1
        else:                                          # a bare float — exact ratio
            fr = _FR(vr)
            num, den = fr.numerator, fr.denominator
        return Qalg.rational((num, den), m, root=root)

    # Build M = A − λI with Qalg entries (the diagonal subtracts λ).
    M = [[_q_entry(rows[i][j]) for j in range(n)] for i in range(n)]
    for i in range(n):
        M[i][i] = M[i][i] - lam

    # Exact Gaussian elimination over the Qalg field → reduced row echelon form.
    pivot_cols: List[int] = []
    pivot_row_of_col: Dict[int, int] = {}
    r = 0
    for c in range(n):
        # Find a pivot: the first row at/below r with a nonzero Qalg entry in col c.
        piv = None
        for rr in range(r, n):
            if bool(M[rr][c]):
                piv = rr
                break
        if piv is None:
            continue                                   # a free column
        M[r], M[piv] = M[piv], M[r]                    # swap pivot row up
        # Normalize the pivot row by the pivot's inverse (exact Qalg inverse).
        try:
            inv = M[r][c].inverse()
        except ZeroDivisionError as exc:               # m reducible ⇒ not a field
            raise ValueError(
                "eigvec_exact: lam.m must be the IRREDUCIBLE minimal polynomial "
                "of the eigenvalue — a reducible m makes ℚ[x]/(m) a non-field "
                "(a zero-divisor pivot was hit); polynomial factorization of the "
                "char-poly is the rc-E follow-up.") from exc
        M[r] = [M[r][j] * inv for j in range(n)]
        # Eliminate column c from every OTHER row (full RREF).
        for rr in range(n):
            if rr != r and bool(M[rr][c]):
                f = M[rr][c]
                M[rr] = [M[rr][j] - f * M[r][j] for j in range(n)]
        pivot_cols.append(c)
        pivot_row_of_col[c] = r
        r += 1
        if r == n:
            break

    free_cols = [c for c in range(n) if c not in pivot_row_of_col]

    # Each free column gives one null-space basis vector: set that free variable
    # to 1, every other free variable to 0, and back-substitute the pivot
    # variables (in RREF, pivot var = −(its row entry in the free column)).
    one = Qalg.rational((1, 1), m, root=root)
    zero = Qalg.rational((0, 1), m, root=root)
    null_vectors: List[List[Qalg]] = []
    for fc in free_cols:
        v = [zero for _ in range(n)]
        v[fc] = one
        for c in pivot_cols:
            pr = pivot_row_of_col[c]
            v[c] = -M[pr][fc]
        null_vectors.append(v)
    return null_vectors, one, free_cols


def eigvec_exact(a, lam):
    """Exact EIGENVECTOR(S) of an integer/rational matrix via the null space of
    ``A − λI`` over the number field ℚ(λ) = ``Qalg`` (rotation-last rc-D).

    ``a`` is an integer/rational square matrix (list-of-lists or :class:`~srmech.amsc.mat.Mat`);
    ``lam`` is a :class:`~srmech.amsc.qalg.Qalg` — the eigenvalue, carrying its
    IRREDUCIBLE minimal polynomial ``m`` and (optionally) an embedding ``root``.
    For an eigenvalue that is a root of an irreducible integer polynomial ``m``,
    ℚ(λ) = ℚ[x]/(m) is a FIELD, so the eigenvector lives in the null space of
    ``A − λI`` over that field. We build ``M = A − λI`` with ``Qalg`` entries
    (the diagonal subtracts λ) and run EXACT Gaussian elimination over the
    ``Qalg`` field (pivot → normalize by the pivot's ``inverse()`` → eliminate
    the column) to reduced row echelon form; the null space is read off the free
    columns. Every step is exact ``Q`` arithmetic — the body NEVER touches a
    float (the single terminal rotation is in :func:`eigvec_exact_float`).

    **Return contract.** For a SIMPLE eigenvalue (rank ``A − λI`` = ``n−1`` → a
    1-dimensional null space) this returns the single null vector as a
    ``list[Qalg]`` (the supported headline case). For a DEGENERATE / repeated
    eigenvalue (null-space dim > 1) it returns a list of the basis vectors — a
    ``list[list[Qalg]]`` — one per free column. (A free-column count of 0 cannot
    happen for a genuine eigenvalue, since ``A − λI`` is singular by definition;
    it raises a clear ``ValueError`` if it somehow does — λ was not an eigenvalue.)

    The eigen-relation ``A·v == λ·v`` is verified EXACTLY over ``Qalg`` (all-Qalg
    equality, componentwise) before returning — an assert, not a float check.

    Raises ``ValueError`` if ``lam.m`` is REDUCIBLE (a zero-divisor pivot is hit,
    because ℚ[x]/(m) is then not a field — polynomial factorization of the
    char-poly is the rc-E follow-up), or if ``a`` is non-square / complex.

    This is the Tajima–Ohara–Terui (arXiv:1811.09149) exact-eigenvector regime
    done as a direct exact null-space. **Class L** (the eigenspace = the spectral
    null space) ∘ **Class N** (the exact ``Q`` field arithmetic) ∘ **Class K**
    (the sign in subtraction / negation — never an ALU ``abs``).
    """
    from srmech.amsc.qalg import Qalg  # noqa: F401  (kept for the verify below)

    null_vectors, _one_unused, free_cols = _eigvec_exact_qalg(a, lam)
    if not free_cols:
        raise ValueError(
            "eigvec_exact: A − λI is non-singular (null space is trivial) — "
            "lam is not an eigenvalue of a (or its m does not match a's "
            "spectrum). The eigenvector null space is empty.")

    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)

    def _verify(vec):
        """Assert ``A·vec == λ·vec`` exactly over Qalg, componentwise."""
        for i in range(n):
            # (A·v)[i] = Σ_j a[i][j] · v[j]  — Qalg arithmetic (a[i][j] scalar).
            acc = None
            for j in range(n):
                term = vec[j] * rows[i][j]             # Qalg · (int/Fraction scalar)
                acc = term if acc is None else acc + term
            lhs = acc
            rhs = lam * vec[i]
            assert lhs == rhs, (
                f"eigvec_exact: eigen-relation A·v == λ·v FAILED at component {i} "
                f"({lhs!r} != {rhs!r}) — internal error")

    if len(free_cols) == 1:
        v = null_vectors[0]
        _verify(v)
        return v
    # Degenerate / repeated eigenvalue: null space dim > 1 → return ALL basis
    # vectors. Each basis vector independently satisfies the eigen-relation.
    for v in null_vectors:
        _verify(v)
    return null_vectors


def eigvec_exact_float(a, lam):
    """Float read-out of :func:`eigvec_exact` — the ONE terminal projection.

    Calls :func:`eigvec_exact` (exact ``Qalg`` body), then **terminal-projects**
    each component via :meth:`Qalg.to_complex` (or :meth:`Qalg.to_float` when
    ``lam.root`` is real) — one FPU lift per component, the rotation-last
    boundary. ``lam`` MUST carry an embedding ``root`` (the projection needs it).

    Returns a ``list[complex]`` (or ``list[float]`` for a real root) for a simple
    eigenvalue, or a ``list[list[...]]`` (one float vector per basis vector) for
    a degenerate eigenvalue — mirroring :func:`eigvec_exact`'s shape.
    """
    if getattr(lam, "root", None) is None:
        raise ValueError(
            "eigvec_exact_float: lam must carry an embedding root for the "
            "terminal projection; attach one with Qalg(m, coords, root=...) or "
            ".with_root(root)")
    real_root = not (isinstance(lam.root, complex) and lam.root.imag != 0)

    def _project(comp):
        return comp.to_float() if real_root else comp.to_complex()

    result = eigvec_exact(a, lam)
    # Shape-faithful: result is list[Qalg] (simple) or list[list[Qalg]] (degenerate).
    if result and isinstance(result[0], list):
        return [[_project(c) for c in vec] for vec in result]
    return [_project(c) for c in result]


# ── exact JORDAN CHAINS over ℚ(λ) = Qalg: generalized eigenvectors (rc27, rc-G) ──
# The rc23 `eigvec_exact` returns the GEOMETRIC eigenvectors (the null space of
# N = A − λI) — for a DEFECTIVE eigenvalue that is FEWER than the algebraic
# multiplicity μ, so it is NOT a complete basis. This closes that gap: the
# generalized eigenvectors / Jordan chains. N is nilpotent on the generalized
# eigenspace `null(Nᵘ)` (dim μ). By the exact `Qalg`-Gaussian-elimination rank of
# the matrix powers `Nᵏ` (k = 0,1,…,p where p is the smallest power with
# `null(N^p) = null(N^{p+1})`), the Jordan structure is read off the rank jumps:
#   • # blocks of size ≥ k = dim null(Nᵏ) − dim null(N^{k-1}) = r_{k-1} − r_k,
#   • # blocks of size exactly k = r_{k-1} − 2·r_k + r_{k+1}.
# The chains are built top-down (the classical construction): for the largest
# block size p, pick generalized eigenvectors in `null(N^p)` not in `null(N^{p-1})`
# and form the chain v, N·v, N²·v, …, N^{p-1}·v (bottom = a genuine geometric
# eigenvector, N·bottom = 0); at each smaller size, choose new top vectors
# independent modulo the chains already built. All arithmetic is exact `Qalg`.
# Ref: R. A. Horn & C. R. Johnson, *Matrix Analysis*, 2nd ed. (Cambridge Univ.
# Press, 2013), §3.1–3.2 (the Jordan canonical form + chain construction); see
# also G. H. Golub & C. F. Van Loan, *Matrix Computations*, 4th ed. §7.6.5.


def _qalg_matrix_of(a, lam):
    """``(N = A − λI, A_qalg, n, one, zero)`` with ``Qalg`` entries over ``lam``'s
    field — the shared exact set-up for the Jordan machinery (mirrors the build at
    the top of :func:`_eigvec_exact_qalg`)."""
    from srmech.amsc.qalg import Qalg

    if not isinstance(lam, Qalg):
        raise TypeError(
            "jordan: lam must be a Qalg eigenvalue (carrying its irreducible m + "
            f"embedding root); got {type(lam).__name__}")
    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    if n == 0:
        raise ValueError("jordan: a must be a non-empty square matrix")
    if any(len(r) != n for r in rows):
        raise ValueError(f"jordan: a must be square 2-D; got {n}x{len(rows[0])}")
    m = lam.m
    root = lam.root

    def _q_entry(v):
        vr = v.real if hasattr(v, "real") else v
        vi = v.imag if hasattr(v, "imag") else 0
        if vi != 0:
            raise ValueError(
                "jordan: a must be an integer/rational (real) matrix; "
                f"got complex entry {v!r}")
        if hasattr(vr, "numerator") and hasattr(vr, "denominator"):
            num, den = int(vr.numerator), int(vr.denominator)
        elif int(vr) == vr:
            num, den = int(vr), 1
        else:
            fr = _FR(vr)
            num, den = fr.numerator, fr.denominator
        return Qalg.rational((num, den), m, root=root)

    A_q = [[_q_entry(rows[i][j]) for j in range(n)] for i in range(n)]
    one = Qalg.rational((1, 1), m, root=root)
    zero = Qalg.rational((0, 1), m, root=root)
    # N = A − λI.
    N = [[A_q[i][j] for j in range(n)] for i in range(n)]
    for i in range(n):
        N[i][i] = N[i][i] - lam
    return N, A_q, n, one, zero


def _qalg_matmul(P, Q, n, zero):
    """Exact ``Qalg`` matrix product ``P·Q`` (both n×n) — the Class-M bind."""
    out = [[zero for _ in range(n)] for _ in range(n)]
    for i in range(n):
        Pi = P[i]
        for k in range(n):
            pik = Pi[k]
            if not pik:                                 # exact Qalg zero
                continue
            Qk = Q[k]
            row = out[i]
            for j in range(n):
                qkj = Qk[j]
                if qkj:
                    row[j] = row[j] + pik * qkj
    return out


def _qalg_matvec(M, v, n, zero):
    """Exact ``Qalg`` matrix·vector ``M·v`` — the Class-M bind on a single column."""
    out = [zero for _ in range(n)]
    for i in range(n):
        acc = zero
        Mi = M[i]
        for j in range(n):
            mij = Mi[j]
            if mij and v[j]:
                acc = acc + mij * v[j]
        out[i] = acc
    return out


def _qalg_rref(M, n):
    """Exact reduced row echelon form of an n×n ``Qalg`` matrix (a COPY is reduced).
    Returns ``(R, pivot_cols, pivot_row_of_col)`` — the RREF, the pivot columns, and
    the column→pivot-row map. Same Gaussian-elimination kernel as
    :func:`_eigvec_exact_qalg`, over the ``Qalg`` field (every pivot inverse is the
    exact :meth:`Qalg.inverse`)."""
    R = [list(row) for row in M]
    pivot_cols: List[int] = []
    pivot_row_of_col: Dict[int, int] = {}
    r = 0
    for c in range(n):
        piv = None
        for rr in range(r, n):
            if bool(R[rr][c]):
                piv = rr
                break
        if piv is None:
            continue
        R[r], R[piv] = R[piv], R[r]
        try:
            inv = R[r][c].inverse()
        except ZeroDivisionError as exc:
            raise ValueError(
                "jordan: lam.m must be the IRREDUCIBLE minimal polynomial of the "
                "eigenvalue — a reducible m makes ℚ[x]/(m) a non-field (a "
                "zero-divisor pivot was hit).") from exc
        R[r] = [R[r][j] * inv for j in range(n)]
        for rr in range(n):
            if rr != r and bool(R[rr][c]):
                f = R[rr][c]
                R[rr] = [R[rr][j] - f * R[r][j] for j in range(n)]
        pivot_cols.append(c)
        pivot_row_of_col[c] = r
        r += 1
        if r == n:
            break
    return R, pivot_cols, pivot_row_of_col


def _qalg_nullspace(M, n, one, zero):
    """Exact null-space basis of an n×n ``Qalg`` matrix (the free-column
    construction, identical to :func:`_eigvec_exact_qalg`): a ``list[list[Qalg]]``,
    one basis vector per free column."""
    R, pivot_cols, pivot_row_of_col = _qalg_rref(M, n)
    free_cols = [c for c in range(n) if c not in pivot_row_of_col]
    basis: List[List] = []
    for fc in free_cols:
        v = [zero for _ in range(n)]
        v[fc] = one
        for c in pivot_cols:
            pr = pivot_row_of_col[c]
            v[c] = -R[pr][fc]
        basis.append(v)
    return basis


def _qalg_rank(M, n):
    """Exact rank of an n×n ``Qalg`` matrix = the pivot count of its RREF."""
    _R, pivot_cols, _prc = _qalg_rref(M, n)
    return len(pivot_cols)


def _qalg_independent_modulo(cand, spanning, n, zero):
    """Is the ``Qalg`` vector ``cand`` linearly INDEPENDENT of the columns in
    ``spanning`` (a ``list[list[Qalg]]``)? Exact: row-reduce the (n × (k+1)) matrix
    whose columns are ``spanning`` then ``cand`` and check the rank rose by one.
    (Used to pick chain tops independent modulo the already-built chains + the
    lower null space.)"""
    base_rank = _qalg_column_rank(spanning, n)
    aug_rank = _qalg_column_rank(list(spanning) + [cand], n)
    return aug_rank > base_rank


def _qalg_column_rank(cols, n):
    """Exact rank of the span of a list of ``Qalg`` column vectors (each length n).
    Builds the matrix with those columns and counts RREF pivots (rank is
    transpose-invariant, so a row-reduction of the column-matrix works)."""
    k = len(cols)
    if k == 0:
        return 0
    # Build an n×k matrix (column j = cols[j]); rank = pivots of its RREF. RREF here
    # is over a possibly-non-square shape, so reduce directly (not via _qalg_rref,
    # which is n×n). Inline a rectangular Gaussian elimination over Qalg.
    M = [[cols[j][i] for j in range(k)] for i in range(n)]
    r = 0
    rank = 0
    for c in range(k):
        piv = None
        for rr in range(r, n):
            if bool(M[rr][c]):
                piv = rr
                break
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        inv = M[r][c].inverse()
        M[r] = [M[r][j] * inv for j in range(k)]
        for rr in range(n):
            if rr != r and bool(M[rr][c]):
                f = M[rr][c]
                M[rr] = [M[rr][j] - f * M[r][j] for j in range(k)]
        rank += 1
        r += 1
        if r == n:
            break
    return rank


def jordan_chains_exact(a, lam):
    """Exact JORDAN CHAINS (generalized eigenvectors) of an integer/rational matrix
    for an eigenvalue ``λ`` — the complete generalized eigenspace over ℚ(λ) = ``Qalg``
    (rotation-last rc-G; closes the eigensolver for DEFECTIVE matrices).

    ``a`` is an integer/rational square matrix; ``lam`` is a
    :class:`~srmech.amsc.qalg.Qalg` eigenvalue (over its IRREDUCIBLE minimal
    polynomial ``m``, optionally carrying an embedding ``root``) of algebraic
    multiplicity μ. With ``N = A − λI``, the generalized eigenspace ``null(Nᵘ)``
    has dimension μ and ``N`` is nilpotent on it. The Jordan structure is read off
    the EXACT ``Qalg``-Gaussian-elimination ranks ``r_k = rank(Nᵏ)``:

    * ``# blocks of size ≥ k`` = ``r_{k-1} − r_k``;
    * ``# blocks of size exactly k`` = ``r_{k-1} − 2·r_k + r_{k+1}``.

    The chains are built TOP-DOWN (the classical construction): for the largest
    block size ``p`` down to 1, pick generalized eigenvectors ``v`` in ``null(N^p)``
    not in ``null(N^{p-1})`` (independent modulo the chains already built), and form
    the chain ``v, N·v, N²·v, …, N^{p-1}·v`` (the bottom ``N^{p-1}·v`` is a genuine
    geometric eigenvector). All arithmetic is exact ``Qalg``.

    **Return.** ``(chains, block_sizes)`` where ``chains`` is a ``list`` of chains,
    each chain a ``list[list[Qalg]]`` of generalized eigenvectors ordered so the
    BOTTOM (last) entry is the geometric eigenvector and ``N · chain[i] == chain[i-1]``
    (``N · chain[0] == 0``); ``block_sizes`` is the ``list[int]`` of the chains'
    lengths (= the Jordan block sizes for λ, summing to μ). The chain relations are
    VERIFIED exactly over ``Qalg`` (``(A−λI)·top == next-down``, bottom annihilated)
    before returning.

    For a NON-defective λ every chain has length 1 (the geometric eigenvectors),
    so this reduces to :func:`eigvec_exact`'s basis. Raises ``ValueError`` if
    ``lam.m`` is reducible (ℚ[x]/(m) is then not a field) or ``a`` is non-square /
    complex.

    Ref: R. A. Horn & C. R. Johnson, *Matrix Analysis*, 2nd ed. (Cambridge, 2013),
    §3.1–3.2; G. H. Golub & C. F. Van Loan, *Matrix Computations*, 4th ed. §7.6.5.

    **Class L** (the generalized eigenspace = the iterated spectral null space) ∘
    **Class N** (the exact ``Q`` field arithmetic) ∘ **Class K** (the sign in
    subtraction / negation — never an ALU ``abs``).
    """
    N, _A_q, n, one, zero = _qalg_matrix_of(a, lam)

    # ── ranks r_k = rank(Nᵏ) for k = 0,1,… until null space stops growing ─────────
    # N⁰ = I (rank n, nullity 0). Accumulate powers exactly; stop at the smallest p
    # with rank(N^p) == rank(N^{p+1}) (the generalized eigenspace has stabilised).
    identity = [[one if i == j else zero for j in range(n)] for i in range(n)]
    powers = [identity]                                  # powers[k] = Nᵏ
    ranks = [n]                                          # ranks[k] = rank(Nᵏ)
    Nk = identity
    while True:
        Nk = _qalg_matmul(Nk, N, n, zero)
        rk = _qalg_rank(Nk, n)
        powers.append(Nk)
        ranks.append(rk)
        if rk == ranks[-2]:                              # rank stopped dropping
            break
        if len(ranks) > n + 1:                           # safety (cannot exceed n)
            break
    p = len(ranks) - 1                                   # smallest stabilising power
    # nullities m_k = dim null(Nᵏ) = n − r_k.
    nul = [n - r for r in ranks]
    mu = nul[p]                                          # algebraic multiplicity (= dim null(N^p))

    # block-size counts: # blocks of size exactly k = m_k − 2·m_{k-1} + m_{k-2}
    # (with the rank form r_{k-1} − 2·r_k + r_{k+1}). Read for k = 1..p.
    block_sizes: List[int] = []
    for k in range(1, p + 1):
        rk_m1 = ranks[k - 1]
        rk = ranks[k]
        rk_p1 = ranks[k + 1] if k + 1 < len(ranks) else ranks[-1]
        count_exactly_k = rk_m1 - 2 * rk + rk_p1
        for _ in range(count_exactly_k):
            block_sizes.append(k)

    # ── TOP-DOWN chain construction ───────────────────────────────────────────────
    # For block size s from p down to 1, the chain TOPS live in null(N^s) but not in
    # null(N^{s-1}); each top must be independent modulo (the lower null space
    # null(N^{s-1})) ∪ (the chain vectors already chosen at this level and above).
    # `used` accumulates every generalized eigenvector chosen so far (all levels),
    # so a new top is required independent of all of them together with null(N^{s-1}).
    null_of = {}                                         # k → basis of null(Nᵏ)

    def _null_basis(k):
        if k not in null_of:
            null_of[k] = _qalg_nullspace(powers[k], n, one, zero)
        return null_of[k]

    chains: List[List[List]] = []
    # number of blocks of size exactly s, for the top-down loop.
    n_blocks_size = {}
    for k in range(1, p + 1):
        rk_m1 = ranks[k - 1]
        rk = ranks[k]
        rk_p1 = ranks[k + 1] if k + 1 < len(ranks) else ranks[-1]
        n_blocks_size[k] = rk_m1 - 2 * rk + rk_p1

    chosen_tops: List[List] = []                         # all chain tops + their lower-null context
    for s in range(p, 0, -1):
        need = n_blocks_size.get(s, 0)
        if need == 0:
            continue
        lower = _null_basis(s - 1) if s - 1 >= 1 else []
        # candidate tops = null(N^s) basis vectors; pick `need` of them independent
        # modulo (lower ∪ already-chosen chain vectors).
        cand_basis = _null_basis(s)
        picked = 0
        # The spanning context a new top must be independent of: the lower null space
        # PLUS every generalized vector already placed in a chain (so distinct chains
        # stay independent). Built fresh each pick (vectors grow as chains form).
        for cand in cand_basis:
            if picked == need:
                break
            context = list(lower)
            for ch in chains:
                context.extend(ch)
            if _qalg_independent_modulo(cand, context, n, zero):
                # build the chain v, N·v, …, N^{s-1}·v (top→bottom).
                chain_top_down = [cand]
                cur = cand
                for _ in range(s - 1):
                    cur = _qalg_matvec(N, cur, n, zero)
                    chain_top_down.append(cur)
                # store bottom→top so chain[i-1] = N·chain[i] and chain[0] is the
                # geometric eigenvector (the documented order).
                chain = list(reversed(chain_top_down))
                chains.append(chain)
                chosen_tops.append(cand)
                picked += 1
        if picked != need:
            raise ValueError(
                f"jordan_chains_exact: could not find {need} independent size-{s} "
                f"chain tops (found {picked}) for eigenvalue with min_poly "
                f"{lam.m!r} — internal Jordan-structure bug")

    # ── exact verification of the chain relations over Qalg ───────────────────────
    # For each chain (bottom→top): N·chain[0] == 0 and N·chain[i] == chain[i-1].
    for chain in chains:
        bottom = chain[0]
        Nb = _qalg_matvec(N, bottom, n, zero)
        for comp in Nb:
            assert not comp, (
                "jordan_chains_exact: chain bottom is not a geometric eigenvector "
                f"((A−λI)·bottom != 0) for min_poly {lam.m!r} — internal error")
        for i in range(1, len(chain)):
            Nv = _qalg_matvec(N, chain[i], n, zero)
            for j in range(n):
                assert Nv[j] == chain[i - 1][j], (
                    "jordan_chains_exact: chain relation (A−λI)·chain[i] == "
                    f"chain[i-1] FAILED at level {i}, component {j} for min_poly "
                    f"{lam.m!r} — internal error")

    # sanity: Σ block sizes == μ.
    assert sum(len(ch) for ch in chains) == mu, (
        f"jordan_chains_exact: chain lengths sum {sum(len(ch) for ch in chains)} "
        f"!= algebraic multiplicity {mu} — internal error")
    return chains, [len(ch) for ch in chains]


# ── Part 1 — factor an integer polynomial into irreducibles over ℚ (Zassenhaus) ──
# Factoring over ℚ ≡ factoring over ℤ (Gauss's lemma: the product of two primitive
# polynomials is primitive, so a ℚ-factorisation of a primitive ℤ-polynomial has
# primitive ℤ-factors up to a rational unit). The classical algorithm (Zassenhaus):
#   1. split off content + square-free-decompose (reuse the Yun helper above);
#   2. factor each square-free primitive f mod a good prime p (f square-free mod p),
#      via distinct-degree + equal-degree (Cantor–Zassenhaus) splitting over 𝔽_p;
#   3. Hensel-lift the mod-p factorisation to mod p^k with p^k ≥ 2·B+1 (B = the
#      Mignotte coefficient bound for true factors), so a true factor's coefficients
#      are recoverable as the symmetric residues mod p^k;
#   4. RECOMBINE: over increasing subset sizes of the lifted factors, multiply mod
#      p^k, take symmetric integer representatives, scale by the leading-coeff
#      cofactor, and trial-divide f over ℤ; a clean division peels off a true
#      irreducible factor.
# All EXACT integer / Fraction arithmetic — no float, no ``math`` (gcd routes
# through srmech.amsc.cyclic.gcd, sign-handled). Refs: D. E. Knuth, *TAOCP* Vol. 2
# §4.6.2 (factorisation of polynomials); J. von zur Gathen & J. Gerhen, *Modern
# Computer Algebra*, ch. 15 (factoring over finite fields) + ch. 16 (Hensel lifting
# + short-vector / Zassenhaus recombination).


def _ipoly_trim(p: List[int]) -> List[int]:
    """Drop trailing zeros of an integer coefficient list (low→high)."""
    q = list(p)
    while len(q) > 1 and q[-1] == 0:
        q.pop()
    return q


def _int_gcd(a: int, b: int) -> int:
    """Sign-safe Class-I Euclidean gcd over ℤ (``cyclic.gcd`` takes magnitudes;
    sign is the Class-K pin-slot re-applied here, never an ALU ``abs``)."""
    from srmech.amsc.cyclic import gcd as _cyclic_gcd
    return _cyclic_gcd(_mag(a), _mag(b))


def _ipoly_content(p: List[int]) -> int:
    """The content = gcd of the integer coefficients (0 for the zero poly)."""
    g = 0
    for c in p:
        g = _int_gcd(g, c)
    return g


def _ipoly_primitive(p: List[int]) -> Tuple[int, List[int]]:
    """Split ``p`` into ``(content_signed, primitive_part)`` with the primitive part
    having content 1 and POSITIVE leading coefficient. The signed content carries
    both the gcd and the overall sign so ``content · primitive == p``."""
    p = _ipoly_trim(p)
    cont = _ipoly_content(p)
    if cont == 0:
        return 0, [0]
    if p[-1] < 0:                                    # Class-K sign pin-slot → positive lead
        cont = -cont
    prim = [c // cont for c in p]
    return cont, prim


def _ipoly_mul(a: List[int], b: List[int]) -> List[int]:
    """Exact integer polynomial multiply (low→high)."""
    a = _ipoly_trim(a)
    b = _ipoly_trim(b)
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        if av:
            for j, bv in enumerate(b):
                out[i + j] += av * bv
    return _ipoly_trim(out)


def _ipoly_exact_divmod(a: List[int], b: List[int]) -> Tuple[List[int], List[int]]:
    """Integer polynomial division ``a = q·b + r`` when it is EXACT over ℤ (every
    coefficient quotient is integral); returns ``(q, r)`` with ``r == [0]`` on a
    clean divide. If a coefficient step is non-integral, returns ``(None, None)``
    (the trial-division signal)."""
    a = _ipoly_trim(list(a))
    b = _ipoly_trim(list(b))
    if b == [0]:
        raise ZeroDivisionError("polynomial division by zero")
    q = [0] * max(len(a) - len(b) + 1, 1)
    r = list(a)
    while len(r) >= len(b) and _ipoly_trim(r) != [0]:
        if r[-1] % b[-1] != 0:
            return None, None                        # not an exact integer divide
        c = r[-1] // b[-1]
        d = len(r) - len(b)
        q[d] = c
        for i in range(len(b)):
            r[d + i] -= c * b[i]
        r = _ipoly_trim(r)
    return _ipoly_trim(q), _ipoly_trim(r)


# ── 𝔽_p[x] arithmetic (pure integer mod-p; Class-I cyclic field) ────────────────
def _fp_trim(p: List[int], q: int) -> List[int]:
    out = [c % q for c in p]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _fp_mulmod(a: List[int], b: List[int], q: int) -> List[int]:
    a = _fp_trim(a, q)
    b = _fp_trim(b, q)
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        if av:
            for j, bv in enumerate(b):
                out[i + j] = (out[i + j] + av * bv) % q
    return _fp_trim(out, q)


def _fp_divmod(a: List[int], b: List[int], q: int) -> Tuple[List[int], List[int]]:
    a = _fp_trim(a, q)
    b = _fp_trim(b, q)
    if b == [0]:
        raise ZeroDivisionError("𝔽_p polynomial division by zero")
    inv_lead = pow(b[-1], q - 2, q)                  # Fermat inverse in 𝔽_p
    quo = [0] * max(len(a) - len(b) + 1, 1)
    r = list(a)
    while len(r) >= len(b) and _fp_trim(r, q) != [0]:
        c = (r[-1] * inv_lead) % q
        d = len(r) - len(b)
        quo[d] = c
        for i in range(len(b)):
            r[d + i] = (r[d + i] - c * b[i]) % q
        r = _fp_trim(r, q)
    return _fp_trim(quo, q), _fp_trim(r, q)


def _fp_gcd(a: List[int], b: List[int], q: int) -> List[int]:
    a = _fp_trim(a, q)
    b = _fp_trim(b, q)
    while b != [0]:
        _, r = _fp_divmod(a, b, q)
        a, b = b, r
    if a != [0] and a[-1] != 1:                      # make monic
        inv = pow(a[-1], q - 2, q)
        a = [(c * inv) % q for c in a]
    return a


def _fp_deriv(p: List[int], q: int) -> List[int]:
    if len(p) <= 1:
        return [0]
    return _fp_trim([(p[i] * i) % q for i in range(1, len(p))], q)


def _fp_powmod(base: List[int], e: int, mod: List[int], q: int) -> List[int]:
    """``base^e mod (mod, q)`` by square-and-multiply in 𝔽_p[x]/(mod)."""
    result = [1]
    b = _fp_divmod(base, mod, q)[1]
    while e:
        if e & 1:
            result = _fp_divmod(_fp_mulmod(result, b, q), mod, q)[1]
        e >>= 1
        if e:
            b = _fp_divmod(_fp_mulmod(b, b, q), mod, q)[1]
    return _fp_trim(result, q)


def _fp_make_monic(p: List[int], q: int) -> List[int]:
    p = _fp_trim(p, q)
    if p == [0] or p[-1] == 1:
        return p
    inv = pow(p[-1], q - 2, q)
    return _fp_trim([(c * inv) % q for c in p], q)


def _distinct_degree_factor(f: List[int], q: int) -> List[Tuple[List[int], int]]:
    """Distinct-degree factorisation of a SQUARE-FREE monic ``f`` over 𝔽_p:
    returns ``[(g_d, d)]`` where ``g_d`` is the product of all monic irreducible
    factors of ``f`` of degree exactly ``d`` (von zur Gathen–Gerhard §14.2)."""
    out: List[Tuple[List[int], int]] = []
    fstar = _fp_make_monic(f, q)
    d = 1
    x = [0, 1]
    xqd = x                                          # x^(q^0) tracked via repeated power
    while len(fstar) - 1 >= 2 * d:
        # xqd ← x^(q^d) mod fstar  (raise the previous power to the q-th power)
        xqd = _fp_powmod(xqd, q, fstar, q)
        g = _fp_gcd(_fp_trim(_poly_sub_fp(xqd, x, q), q), fstar, q)
        if g != [1] and g != [0]:
            out.append((_fp_make_monic(g, q), d))
            fstar, _ = _fp_divmod(fstar, g, q)
            fstar = _fp_make_monic(fstar, q)
        d += 1
    if fstar != [1] and len(fstar) > 1:              # the remaining factor is irreducible
        out.append((fstar, len(fstar) - 1))
    return out


def _poly_sub_fp(a: List[int], b: List[int], q: int) -> List[int]:
    n = max(len(a), len(b))
    return _fp_trim([((a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0)) % q
                     for i in range(n)], q)


def _equal_degree_split(f: List[int], d: int, q: int,
                        rng) -> List[List[int]]:
    """Cantor–Zassenhaus equal-degree factorisation: split the product of
    distinct monic irreducibles of degree ``d`` in ``f`` (over 𝔽_p, p odd) into
    its irreducible factors. Deterministic-seeded randomness for reproducibility
    (von zur Gathen–Gerhard §14.3)."""
    f = _fp_make_monic(f, q)
    deg = len(f) - 1
    if deg == d:
        return [f]
    factors = [f]
    out: List[List[int]] = []
    exp = (pow(q, d) - 1) // 2
    n = len(f) - 1
    while factors:
        g = factors.pop()
        if len(g) - 1 == d:
            out.append(g)
            continue
        # random degree < deg(g) polynomial
        while True:
            r = [rng(q) for _ in range(len(g) - 1)]
            r = _fp_trim(r, q)
            if r != [0] and len(r) > 1:
                break
        h = _fp_powmod(r, exp, g, q)
        h = _poly_sub_fp(h, [1], q)                  # h = r^exp − 1
        gg = _fp_gcd(h, g, q)
        if gg == [1] or _fp_trim(gg, q) == _fp_make_monic(g, q):
            factors.append(g)                        # split failed; retry
            continue
        gg = _fp_make_monic(gg, q)
        other, _ = _fp_divmod(g, gg, q)
        factors.append(gg)
        factors.append(_fp_make_monic(other, q))
    return out


def _factor_mod_p(f: List[int], q: int, rng) -> List[List[int]]:
    """Full factorisation of a SQUARE-FREE monic ``f`` over 𝔽_p into monic
    irreducibles (distinct-degree then equal-degree)."""
    fac: List[List[int]] = []
    for g, d in _distinct_degree_factor(f, q):
        if len(g) - 1 == d:
            fac.append(g)
        else:
            fac.extend(_equal_degree_split(g, d, q, rng))
    return [_fp_make_monic(g, q) for g in fac]


# ── Mignotte bound + Hensel lifting ─────────────────────────────────────────────
def _mignotte_bound(f: List[int]) -> int:
    """An integer bound ``B`` on every coefficient of any integer factor of ``f``:
    the Mignotte bound ``B = 2^deg · ‖f‖₂ · |lead|`` (a coarse, always-valid
    over-estimate — using ‖f‖₂ ≤ ‖f‖₁ keeps it integer + exact). Class-K magnitudes
    throughout (no ``abs``)."""
    deg = len(f) - 1
    norm1 = sum(_mag(c) for c in f)                  # ‖f‖₁ ≥ ‖f‖₂
    lead = _mag(f[-1])
    return (1 << deg) * norm1 * lead + 1


def _hensel_step(f: List[int], g: List[int], h: List[int],
                 s: List[int], t: List[int], modulus: int):
    """One quadratic-Hensel lift from ``mod m`` to ``mod m²`` for the relation
    ``f ≡ g·h`` with Bézout cofactors ``s·g + t·h ≡ 1``. Returns the lifted
    ``(g, h, s, t)`` mod ``m²`` (von zur Gathen–Gerhard Algorithm 15.10)."""
    m2 = modulus * modulus
    # e = f − g·h  (mod m²)
    e = _poly_sub_mod(f, _mul_mod(g, h, m2), m2)
    q_, r_ = _divmod_mod(_mul_mod(s, e, m2), h, m2, modulus)
    g_star = _poly_add_mod(_poly_add_mod(g, _mul_mod(t, e, m2), m2),
                           _mul_mod(q_, g, m2), m2)
    h_star = _poly_add_mod(h, r_, m2)
    # lift the cofactors: b = s·g_star + t·h_star − 1
    b = _poly_sub_mod(_poly_add_mod(_mul_mod(s, g_star, m2),
                                    _mul_mod(t, h_star, m2), m2), [1], m2)
    c_, d_ = _divmod_mod(_mul_mod(s, b, m2), h_star, m2, modulus)
    s_star = _poly_sub_mod(s, d_, m2)
    t_star = _poly_sub_mod(_poly_sub_mod(t, _mul_mod(t, b, m2), m2),
                           _mul_mod(c_, g_star, m2), m2)
    return (_trim_mod(g_star, m2), _trim_mod(h_star, m2),
            _trim_mod(s_star, m2), _trim_mod(t_star, m2))


def _trim_mod(p: List[int], m: int) -> List[int]:
    out = [c % m for c in p]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _poly_add_mod(a: List[int], b: List[int], m: int) -> List[int]:
    n = max(len(a), len(b))
    return _trim_mod([((a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)) % m
                      for i in range(n)], m)


def _poly_sub_mod(a: List[int], b: List[int], m: int) -> List[int]:
    n = max(len(a), len(b))
    return _trim_mod([((a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0)) % m
                      for i in range(n)], m)


def _mul_mod(a: List[int], b: List[int], m: int) -> List[int]:
    a = _trim_mod(a, m)
    b = _trim_mod(b, m)
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        if av:
            for j, bv in enumerate(b):
                out[i + j] = (out[i + j] + av * bv) % m
    return _trim_mod(out, m)


def _divmod_mod(a: List[int], b: List[int], m: int, prime: int) -> Tuple[List[int], List[int]]:
    """Division of ``a`` by a MONIC-mod-prime ``b`` modulo ``m`` (m a power of
    ``prime``). The leading coeff of ``b`` is a unit mod m (it is 1 mod prime), so
    its inverse mod m exists and the division is exact-style with quotient +
    remainder (deg r < deg b)."""
    a = _trim_mod(a, m)
    b = _trim_mod(b, m)
    inv_lead = pow(b[-1], -1, m)                     # b[-1] is a unit mod m
    quo = [0] * max(len(a) - len(b) + 1, 1)
    r = list(a)
    while len(r) >= len(b) and _trim_mod(r, m) != [0]:
        c = (r[-1] * inv_lead) % m
        d = len(r) - len(b)
        quo[d] = c
        for i in range(len(b)):
            r[d + i] = (r[d + i] - c * b[i]) % m
        r = _trim_mod(r, m)
    return _trim_mod(quo, m), _trim_mod(r, m)


def _multi_hensel_lift(f: List[int], factors_modp: List[List[int]],
                       prime: int, target: int) -> List[List[int]]:
    """Lift a list of pairwise-coprime monic factors of ``f mod prime`` to factors
    mod ``prime^k`` with ``prime^k ≥ target``, by a balanced product tree of
    quadratic Hensel steps. ``f`` need not be monic; the leading coefficient is
    folded onto the FIRST factor so the lifted product matches ``f`` mod p^k."""
    # Make the lifted product reproduce f mod p^k: work with f_monic = f scaled so
    # its lead is a unit; we lift factors of f mod p^k whose product ≡ lead^{-1}? —
    # simpler & standard: lift the MONIC associate of f, recombination re-applies
    # the leading-coefficient cofactor.
    if len(factors_modp) == 1:
        # single factor: its monic form mod p^k IS the monic associate of f.
        k = 1
        m = prime
        while m < target:
            k += 1
            m *= prime
        lead = f[-1]
        inv_lead = pow(lead % m, -1, m)
        fm = _trim_mod([(c * inv_lead) % m for c in f], m)
        return [fm]
    # split the factor list in two, lift the pair (g,h), recurse on each side.
    mid = len(factors_modp) // 2
    g0 = _product_modp(factors_modp[:mid], prime)
    h0 = _product_modp(factors_modp[mid:], prime)
    # Make g0,h0 monic mod prime (they are, being products of monic factors).
    # f's monic associate mod the lift modulus:
    k = 1
    m = prime
    while m < target:
        k += 1
        m *= prime
    lead = f[-1]
    inv_lead = pow(lead % m, -1, m)
    fm = _trim_mod([(c * inv_lead) % m for c in f], m)
    # Bézout cofactors mod prime: s·g0 + t·h0 ≡ 1.
    s, t = _bezout_modp(g0, h0, prime)
    g, h, s, t = g0, h0, s, t
    modn = prime
    while modn < m:
        # one quadratic step doubles the modulus; cap at m.
        g, h, s, t = _hensel_step(fm, g, h, s, t, modn)
        modn = modn * modn
        if modn > m:
            g = _trim_mod(g, m)
            h = _trim_mod(h, m)
            modn = m
    g = _trim_mod(g, m)
    h = _trim_mod(h, m)
    left = _multi_hensel_lift_factors(g, factors_modp[:mid], prime, m)
    right = _multi_hensel_lift_factors(h, factors_modp[mid:], prime, m)
    return left + right


def _multi_hensel_lift_factors(g_lifted: List[int], factors_modp: List[List[int]],
                               prime: int, m: int) -> List[List[int]]:
    """Recurse: ``g_lifted`` is a monic-mod-m lift whose mod-prime image is the
    product of ``factors_modp``; split it into the per-factor lifts mod m."""
    if len(factors_modp) == 1:
        return [_trim_mod(g_lifted, m)]
    mid = len(factors_modp) // 2
    a0 = _product_modp(factors_modp[:mid], prime)
    b0 = _product_modp(factors_modp[mid:], prime)
    s, t = _bezout_modp(a0, b0, prime)
    a, b, s, t = a0, b0, s, t
    modn = prime
    while modn < m:
        a, b, s, t = _hensel_step(g_lifted, a, b, s, t, modn)
        modn = modn * modn
        if modn > m:
            a = _trim_mod(a, m)
            b = _trim_mod(b, m)
            modn = m
    a = _trim_mod(a, m)
    b = _trim_mod(b, m)
    return (_multi_hensel_lift_factors(a, factors_modp[:mid], prime, m)
            + _multi_hensel_lift_factors(b, factors_modp[mid:], prime, m))


def _product_modp(factors: List[List[int]], q: int) -> List[int]:
    out = [1]
    for f in factors:
        out = _fp_mulmod(out, f, q)
    return out


def _bezout_modp(g: List[int], h: List[int], q: int) -> Tuple[List[int], List[int]]:
    """Bézout cofactors ``s·g + t·h ≡ 1 (mod q)`` for coprime monic g, h over 𝔽_p
    via the extended Euclidean algorithm in 𝔽_p[x]."""
    old_r, r = _fp_trim(g, q), _fp_trim(h, q)
    old_s, s = [1], [0]
    old_t, t = [0], [1]
    while r != [0]:
        quo, _ = _fp_divmod(old_r, r, q)
        old_r, r = r, _poly_sub_fp(old_r, _fp_mulmod(quo, r, q), q)
        old_s, s = s, _poly_sub_fp(old_s, _fp_mulmod(quo, s, q), q)
        old_t, t = t, _poly_sub_fp(old_t, _fp_mulmod(quo, t, q), q)
    # normalise so old_r (the gcd, a unit) becomes 1
    g0 = old_r[0]
    inv = pow(g0, q - 2, q)
    s_out = _fp_trim([(c * inv) % q for c in old_s], q)
    t_out = _fp_trim([(c * inv) % q for c in old_t], q)
    return s_out, t_out


def _symmetric_rep(p: List[int], m: int) -> List[int]:
    """Symmetric integer representatives of a mod-m coefficient list (centred in
    ``(−m/2, m/2]``) — the lift back to ℤ a true factor's coefficients fall in."""
    out = []
    half = m // 2
    for c in p:
        c %= m
        if c > half:
            c -= m
        out.append(c)
    return _ipoly_trim(out)


def _factor_square_free_primitive(f: List[int], *, subset_cap: int = 18
                                  ) -> Tuple[List[List[int]], bool]:
    """Factor a SQUARE-FREE primitive integer polynomial ``f`` (positive lead,
    content 1, deg ≥ 1) into irreducible integer factors. Returns
    ``(factors, hit_cap)`` where ``hit_cap`` flags that the recombination
    subset-size guard was reached (the factorisation is then returned as-far-as-
    peeled with the leftover as one factor — never hangs)."""
    f = _ipoly_trim(f)
    deg = len(f) - 1
    if deg <= 1:
        return [f], False

    # 1. choose a prime p ∤ lead with f square-free mod p.
    from srmech.amsc.primes import is_prime
    lead = f[-1]
    prime = None
    cand = 3
    while cand < 100000:
        if is_prime(cand) and lead % cand != 0:
            fp = _fp_trim(f, cand)
            if _fp_gcd(fp, _fp_deriv(fp, cand), cand) == [1]:
                prime = cand
                break
        cand += 2
    if prime is None:
        raise ValueError(
            "factor_integer_poly: no good reduction prime found below 100000 "
            "(degenerate input?)")

    # deterministic-seeded 𝔽_p randomness for reproducible Cantor–Zassenhaus.
    state = [0x2545F4914F6CDD1D ^ (prime * (deg + 1))]

    def _rng(q):
        # a tiny xorshift → uniform-ish residue; deterministic for a given prime.
        x = state[0]
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 7
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        state[0] = x
        return x % q

    # 2. factor f (its monic associate) mod p.
    fp_monic = _fp_make_monic(f, prime)
    modp_factors = _factor_mod_p(fp_monic, prime, _rng)
    if len(modp_factors) == 1:
        return [f], False                            # irreducible (one factor mod p)

    # 3. Hensel-lift to mod p^k with p^k ≥ 2·B+1.
    bound = _mignotte_bound(f)
    target = 2 * bound + 1
    m = prime
    while m < target:
        m *= prime
    lifted = _multi_hensel_lift(f, modp_factors, prime, m)
    lifted = [_trim_mod(g, m) for g in lifted]

    # 4. recombination: increasing subset sizes; trial-divide over ℤ.
    remaining = list(range(len(lifted)))
    irreducibles: List[List[int]] = []
    f_work = list(f)
    lead_work = f_work[-1]
    size = 1
    hit_cap = False
    while remaining and size <= len(remaining):
        if size > subset_cap:
            hit_cap = True
            break
        found = None
        for combo in itertools.combinations(remaining, size):
            # candidate = lead · Π lifted[i]  (mod m), symmetric rep, primitive part.
            prod = [lead_work % m]
            for i in combo:
                prod = _mul_mod(prod, lifted[i], m)
            cand_poly = _symmetric_rep(prod, m)
            _c, cand_prim = _ipoly_primitive(cand_poly)
            if len(cand_prim) <= 1:
                continue
            quo, rem = _ipoly_exact_divmod(f_work, cand_prim)
            if quo is not None and rem == [0]:
                found = (combo, cand_prim, quo)
                break
        if found is None:
            size += 1
            continue
        combo, cand_prim, quo = found
        irreducibles.append(cand_prim)
        for i in combo:
            remaining.remove(i)
        f_work = _ipoly_trim(quo)
        lead_work = f_work[-1] if f_work != [0] else 1
        # f_work may now be a unit (±1) if all factors peeled.
        if len(f_work) <= 1:
            break
        size = 1                                     # restart subset search on the smaller f
    # whatever is left (deg ≥ 1) is the final irreducible factor (or the cap leftover).
    if len(f_work) > 1:
        _c, leftover = _ipoly_primitive(f_work)
        irreducibles.append(leftover)
    return irreducibles, hit_cap


def factor_integer_poly(coeffs):
    """Factor an integer polynomial into its IRREDUCIBLE factors over ℚ (Zassenhaus).

    ``coeffs`` is the integer coefficient sequence **low→high** (``coeffs[0]`` the
    constant term). Returns a ``list[tuple[factor_coeffs, multiplicity]]`` — each
    ``factor_coeffs`` a primitive **irreducible** integer polynomial (low→high,
    content 1, POSITIVE leading coefficient), paired with its multiplicity ``≥ 1``.
    The product ``Π factor**mult`` reconstructs the input up to its overall sign and
    content (the ``self-check`` below asserts exactly that).

    Algorithm (Gauss's lemma: factoring over ℚ ≡ factoring over ℤ):

    1. split off content + primitive part; **Yun square-free decomposition**
       (reuse :func:`_square_free_factors`) so each multiplicity is handled exactly;
    2. for each square-free primitive ``f`` (deg ≥ 1): deg ≤ 1 ⇒ irreducible; else
       choose a prime ``p ∤ lead(f)`` with ``f`` square-free mod ``p``, factor
       ``f mod p`` in 𝔽_p[x] (distinct-degree + **Cantor–Zassenhaus** equal-degree),
       **Hensel-lift** to mod ``p^k`` with ``p^k ≥ 2·B+1`` (``B`` = the **Mignotte**
       coefficient bound), then **recombine** over increasing subset sizes (multiply
       mod ``p^k``, take symmetric integer reps, scale by the leading-coeff cofactor,
       trial-divide over ℤ — a clean division peels off a true irreducible factor),
       guarded by a subset-size cap so the worst case cannot hang.

    All EXACT integer / ``fractions.Fraction`` arithmetic — no float, no ``math``
    module (gcd routes through ``srmech.amsc.cyclic.gcd``; primality through
    ``srmech.amsc.primes.is_prime``). Refs: D. E. Knuth, *The Art of Computer
    Programming* Vol. 2 §4.6.2; J. von zur Gathen & J. Gerhard, *Modern Computer
    Algebra*, ch. 15–16 (factoring over finite fields + Hensel lifting + Zassenhaus
    recombination).

    **Class L** (the algebraic / spectral content) ∘ **Class J** (the prime-field
    reduction + Hensel lift) ∘ **Class I** (the 𝔽_p modular arithmetic) ∘ **Class K**
    (the symmetric-rep sign pin-slots — never an ALU ``abs``).
    """
    coeffs = [int(c) for c in coeffs]
    p = _ipoly_trim(coeffs)
    if p == [0]:
        raise ValueError("factor_integer_poly: the zero polynomial has no factorisation")
    if len(p) == 1:                                  # a nonzero constant — no factors
        return []
    cont, prim = _ipoly_primitive(p)                 # content (signed) · primitive part

    # square-free decomposition over ℚ (Yun) → [(square_free_part, multiplicity)].
    prim_q = [_FR(c) for c in prim]
    sf = _square_free_factors(prim_q)                # [(monic ℚ factor, k)]

    factors_out: List[Tuple[Tuple[int, ...], int]] = []
    capped = False
    for (g_q, mult) in sf:
        # g_q is a monic ℚ polynomial; clear denominators → primitive ℤ polynomial.
        den_lcm = 1
        for c in g_q:
            den_lcm = den_lcm * c.denominator // _int_gcd(den_lcm, c.denominator)
        g_int = _ipoly_trim([int(c * den_lcm) for c in g_q])
        _c, g_prim = _ipoly_primitive(g_int)
        irr, hit = _factor_square_free_primitive(g_prim)
        if hit:
            capped = True
        for fac in irr:
            _c2, fac_prim = _ipoly_primitive(fac)
            factors_out.append((tuple(fac_prim), mult))

    # merge identical factors (a square-free part can in principle repeat across the
    # decomposition only with the SAME multiplicity, but consolidate defensively).
    merged: Dict[Tuple[int, ...], int] = {}
    for fac, mult in factors_out:
        merged[fac] = merged.get(fac, 0) + mult
    result = sorted(merged.items(), key=lambda kv: (len(kv[0]), kv[0]))

    # ── self-check: Π factor**mult == ± content · input (up to sign/content) ──────
    if not capped:
        recon = [1]
        for fac, mult in result:
            for _ in range(mult):
                recon = _ipoly_mul(recon, list(fac))
        # recon should equal `prim` up to sign (both primitive, positive lead by
        # construction of _ipoly_primitive); compare primitive parts.
        _rc, recon_prim = _ipoly_primitive(recon)
        assert recon_prim == prim or recon_prim == [(-c) for c in prim], (
            f"factor_integer_poly self-check FAILED: Π factor**mult = {recon_prim} "
            f"!= primitive input {prim} — internal Zassenhaus bug")
    return [(fac, mult) for fac, mult in result]


# ── Part 2 — turnkey exact eigensolver: matrix → all exact eigenpairs ────────────
def eig_exact(a, *, bits: int = 64, project: bool = True):
    """Turnkey EXACT eigensolver — a matrix → ALL its exact eigenpairs (rc-F).

    Chains the rotation-last exact machinery into one call:
    ``char_poly(a)`` → Yun square-free → :func:`factor_integer_poly` (the
    IRREDUCIBLE factors ``m_i``, each carrying its algebraic multiplicity) → for
    each ``m_i`` isolate ALL its roots (real via the Sturm cascade, complex via the
    rc-E argument-principle box subdivision) → each root ``λ`` becomes a
    :class:`~srmech.amsc.qalg.Qalg` over ``m_i`` (its EXACT irreducible substrate,
    embedded at the isolated float/complex root) → :func:`eigvec_exact` for the
    exact eigenvector(s) = the null space of ``A − λI`` over ℚ(λ).

    ``a`` must be an INTEGER (or rational-integer) square matrix.

    With ``project=True`` (default) returns a ``list[dict]`` — one entry per
    DISTINCT eigenvalue — each::

        {"value": complex,                 # the terminal float/complex projection
         "vector": list[complex],          # the (first) eigenvector, projected
         "algebraic_multiplicity": int,    # from the char-poly factor multiplicity
         "geometric_multiplicity": int,    # dim of the A−λI null space
         "min_poly": tuple[int],           # the exact irreducible m_i (low→high)
         "defective": bool,                # geometric < algebraic
         "jordan_blocks": list[int],       # Jordan block sizes for λ (sum = alg-mult)
         "generalized_vectors": list[list[complex]]}  # FULL μ-many basis, by chain

    ``value`` / ``vector`` are the single TERMINAL projections (rotation-last);
    ``min_poly`` is the eigenvalue's exact irreducible substrate. For a DEGENERATE
    eigenvalue (geometric > 1) ``vector`` is the first null-space basis vector — the
    full basis is reachable via :func:`eigvec_exact_float`.

    **rc27 — the COMPLETE generalized basis (closes the eigensolver).** Each entry
    now also carries ``"jordan_blocks"`` (the Jordan block sizes for λ — all ``1``s
    ⇒ diagonalizable-at-this-λ, a ``2`` ⇒ a size-2 defective chain, …; they sum to
    the algebraic multiplicity) and ``"generalized_vectors"`` — the FULL μ-many
    generalized eigenvectors organized by chain (each chain bottom→top, the bottom a
    geometric eigenvector). For a NON-defective λ the chains are all length 1, so
    ``generalized_vectors`` equals the geometric eigenvectors and existing behaviour
    is preserved; for a DEFECTIVE λ this is the new COMPLETE basis (the Jordan chains
    from :func:`jordan_chains_exact`). ``generalized_vectors`` are float/complex when
    ``project=True``, exact ``Qalg`` when ``project=False``.

    With ``project=False`` returns the EXACT objects for callers staying in the
    field: each dict swaps ``value`` → ``value_qalg`` (a :class:`~srmech.amsc.qalg.Qalg`)
    and ``vector`` → ``vectors_qalg`` (``list[list[Qalg]]``, the exact null-space
    basis), keeping ``min_poly`` + the multiplicities + ``defective`` +
    ``jordan_blocks`` + ``generalized_vectors`` (the latter as ``list[list[Qalg]]``).

    **SELF-VALIDATION** (asserted before returning — this is what catches a
    factorisation bug): (a) ``Σ algebraic_multiplicity == n`` AND the FULL
    generalized basis has exactly ``n`` vectors (the complete-basis guarantee);
    (b) the eigenvalue multiset (with algebraic multiplicity) reconstructs the monic
    char-poly (``Π (x − value_k) ≈`` char-poly to ~1e-7, numeric); (c) every returned
    ``(value, vector)`` satisfies ``A·vector ≈ value·vector`` to ~1e-9, AND the full
    generalized basis ``P`` (all eigenvalues' chains together) satisfies
    ``A·P ≈ P·J`` to ~1e-9 where ``J`` is the Jordan form. A clear ``ValueError`` is
    raised on any failure (it means an upstream bug).

    **Class L** (the spectral content) ∘ **Class J** (the irreducible-factor
    substrate) ∘ **Class N** (the exact ℚ(λ) field arithmetic) ∘ **Class K** (the
    terminal float/complex projection — rotation-last).
    """
    from srmech.amsc.qalg import Qalg

    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    if n == 0:
        return []
    if any(len(r) != n for r in rows):
        raise ValueError(f"eig_exact: a must be square 2-D; got {n}x{len(rows[0])}")

    cp = char_poly(a)                                # monic, high→low
    cp_low = [int(c) for c in reversed(cp)]          # low→high integer coeffs

    # factor the char-poly into irreducibles with algebraic multiplicities.
    irr_factors = factor_integer_poly(cp_low)        # [(m_i low→high tuple, alg_mult)]

    eigenpairs: List[dict] = []
    for (m_tuple, alg_mult) in irr_factors:
        m_low = list(m_tuple)                        # primitive irreducible, low→high
        # make m monic over ℤ (it must be — char-poly is monic, factors of a monic
        # integer poly with positive lead are monic; assert it).
        if m_low[-1] != 1:
            raise ValueError(
                f"eig_exact: irreducible factor {m_tuple} is not monic — the "
                "char-poly factorisation is inconsistent (internal bug)")
        m_int = tuple(int(c) for c in m_low)         # Qalg wants an int tuple low→high

        # isolate ALL roots of this irreducible factor (real + complex), as floats/
        # complex — the embeddings for the Qalg projection. We build a tiny companion
        # of m and reuse eigvals_exact's exact isolation on it.
        roots = _roots_of_irreducible(m_low, bits)

        for root in roots:
            lam = Qalg.alpha(m_int, root=root)
            res = eigvec_exact(a, lam)               # list[Qalg] or list[list[Qalg]]
            if res and isinstance(res[0], list):
                basis = res                          # geometric mult > 1
            else:
                basis = [res]
            geom = len(basis)
            defective = geom < alg_mult
            # rc27: the COMPLETE generalized eigenspace = the Jordan chains. For a
            # NON-defective λ every chain is length 1, so the union of chain vectors
            # equals the geometric basis (existing behaviour); for a DEFECTIVE λ this
            # is the full μ-many basis. Chains are bottom→top (bottom = geometric).
            chains, block_sizes = jordan_chains_exact(a, lam)
            gen_qalg = [vec for chain in chains for vec in chain]  # flatten by chain
            entry = {
                "min_poly": m_int,
                "algebraic_multiplicity": alg_mult,
                "geometric_multiplicity": geom,
                "defective": defective,
                "jordan_blocks": list(block_sizes),
            }
            real_root = not (isinstance(root, complex) and root.imag != 0)
            if project:
                entry["value"] = (lam.to_float() + 0j if not isinstance(root, complex)
                                  else lam.to_complex())
                # primary vector = first GEOMETRIC basis vector, projected component-wise.
                first = basis[0]
                entry["vector"] = [
                    (c.to_float() + 0j if real_root else c.to_complex()) for c in first]
                entry["generalized_vectors"] = [
                    [(c.to_float() + 0j if real_root else c.to_complex()) for c in vec]
                    for vec in gen_qalg]
            else:
                entry["value_qalg"] = lam
                entry["vectors_qalg"] = basis
                entry["generalized_vectors"] = gen_qalg
            eigenpairs.append(entry)

    # deterministic order: by (value real, value imag) when projected, else by the
    # isolated root carried on the Qalg.
    def _sort_key(e):
        if project:
            v = e["value"]
            return (v.real, v.imag)
        r = e["value_qalg"].root
        rc = complex(r)
        return (rc.real, rc.imag)
    eigenpairs.sort(key=_sort_key)

    # ── SELF-VALIDATION ──────────────────────────────────────────────────────────
    # (a) Σ algebraic_multiplicity == n AND the FULL generalized basis is n-many.
    total_alg = sum(e["algebraic_multiplicity"] for e in eigenpairs)
    if total_alg != n:
        raise ValueError(
            f"eig_exact self-validation (a) FAILED: Σ algebraic_multiplicity = "
            f"{total_alg} != n = {n} — the char-poly factorisation lost/gained a "
            "root (upstream bug)")
    # rc27 complete-basis guarantee: the union of all eigenvalues' generalized
    # vectors (the Jordan chains) is a basis of ℂⁿ — exactly n vectors, defective
    # or not.
    total_gen = sum(len(e["generalized_vectors"]) for e in eigenpairs)
    if total_gen != n:
        raise ValueError(
            f"eig_exact self-validation (a) FAILED: the full generalized basis has "
            f"{total_gen} vectors != n = {n} — the Jordan-chain construction is "
            "incomplete (upstream bug)")

    # the float/complex eigenvalue list (with algebraic multiplicity) for (b)/(c).
    if project:
        eval_list = [(e["value"], e["algebraic_multiplicity"]) for e in eigenpairs]
    else:
        eval_list = []
        for e in eigenpairs:
            lam = e["value_qalg"]
            r = lam.root
            val = (lam.to_complex() if (isinstance(r, complex) and r.imag != 0)
                   else complex(lam.to_float(), 0.0))
            eval_list.append((val, e["algebraic_multiplicity"]))

    # (b) Π (x − value_k)^mult ≈ monic char-poly (numeric, ~1e-7).
    recon = [1.0 + 0j]                               # low→high complex poly
    for (val, mlt) in eval_list:
        for _ in range(mlt):
            # multiply by (x − val): shift up minus val·current.
            nxt = [0j] * (len(recon) + 1)
            for i, c in enumerate(recon):
                nxt[i] += -val * c
                nxt[i + 1] += c
            recon = nxt
    cp_monic_low = [complex(c) for c in reversed(cp)]  # monic char-poly low→high
    if len(recon) != len(cp_monic_low):
        raise ValueError(
            "eig_exact self-validation (b) FAILED: reconstructed degree "
            f"{len(recon) - 1} != char-poly degree {len(cp_monic_low) - 1}")
    for i in range(len(recon)):
        if _modulus(recon[i] - cp_monic_low[i]) > 1e-7:
            raise ValueError(
                "eig_exact self-validation (b) FAILED: Π(x − value) does not "
                f"reconstruct the char-poly at coeff {i} "
                f"({recon[i]!r} vs {cp_monic_low[i]!r}) — factorisation bug")

    # (c) A·vector ≈ value·vector to ~1e-9 for every returned (value, vector).
    af = [[complex(rows[i][j]) for j in range(n)] for i in range(n)]
    for e in eigenpairs:
        if project:
            val = e["value"]
            vecs = [e["vector"]]
        else:
            lam = e["value_qalg"]
            r = lam.root
            val = (lam.to_complex() if (isinstance(r, complex) and r.imag != 0)
                   else complex(lam.to_float(), 0.0))
            real_root = not (isinstance(r, complex) and r.imag != 0)
            vecs = [[(c.to_complex() if not real_root else complex(c.to_float(), 0.0))
                     for c in vec] for vec in e["vectors_qalg"]]
        for vec in vecs:
            for i in range(n):
                lhs = sum(af[i][j] * complex(vec[j]) for j in range(n))
                rhs = val * complex(vec[i])
                if _modulus(lhs - rhs) > 1e-9:
                    raise ValueError(
                        "eig_exact self-validation (c) FAILED: A·v != λ·v at "
                        f"component {i} for eigenvalue {val!r} "
                        f"({lhs!r} vs {rhs!r}) — eigenvector bug")

    # rc27 (c') the FULL generalized basis P satisfies A·P ≈ P·J (the complete
    # Jordan relation, defective or not): build P (columns = each eigenvalue's
    # generalized vectors, chain by chain) and J (the Jordan matrix — λ on the
    # diagonal, a super-diagonal 1 WITHIN each chain) in float/complex, then check
    # ‖A·P − P·J‖∞ ≤ ~1e-9. (For project=False the Qalg columns are projected here;
    # eig_exact's float check is the rotation-last read-out of the exact relation
    # jordan_chains_exact already asserted bit-exactly over Qalg.)
    cols: List[List[complex]] = []                       # P columns (n-vectors)
    jblocks: List[Tuple[complex, int]] = []              # (λ, chain_len) per chain
    for e in eigenpairs:
        if project:
            val = e["value"]
            gv = [[complex(c) for c in vec] for vec in e["generalized_vectors"]]
            sizes = e["jordan_blocks"]
        else:
            lam = e["value_qalg"]
            r = lam.root
            val = (lam.to_complex() if (isinstance(r, complex) and r.imag != 0)
                   else complex(lam.to_float(), 0.0))
            real_root = not (isinstance(r, complex) and r.imag != 0)
            gv = [[(c.to_complex() if not real_root else complex(c.to_float(), 0.0))
                   for c in vec] for vec in e["generalized_vectors"]]
            sizes = e["jordan_blocks"]
        # the generalized_vectors are laid out chain-by-chain (bottom→top); slice
        # them back into the chains so J gets a super-diagonal 1 only WITHIN a chain.
        off = 0
        for s in sizes:
            for k in range(s):
                cols.append(gv[off + k])
            jblocks.append((val, s))
            off += s
    if len(cols) == n:                                   # (defensive — (a) ensures it)
        # J: block-diagonal Jordan, columns/rows in the same chain-by-chain order as P.
        J = [[0j] * n for _ in range(n)]
        pos = 0
        for (val, s) in jblocks:
            for k in range(s):
                J[pos + k][pos + k] = val
                if k + 1 < s:                            # super-diagonal 1 within chain
                    J[pos + k][pos + k + 1] = 1.0 + 0j
            pos += s
        # P has the generalized vectors as COLUMNS: P[i][col] = cols[col][i].
        # Check A·P ≈ P·J columnwise: (A·P)[:,c] = A·cols[c]; (P·J)[:,c] = Σ_k P[:,k]·J[k][c].
        for c in range(n):
            ap = [sum(af[i][j] * cols[c][j] for j in range(n)) for i in range(n)]
            pj = [sum(cols[k][i] * J[k][c] for k in range(n)) for i in range(n)]
            for i in range(n):
                if _modulus(ap[i] - pj[i]) > 1e-9:
                    raise ValueError(
                        "eig_exact self-validation (c') FAILED: A·P != P·J at "
                        f"row {i}, column {c} ({ap[i]!r} vs {pj[i]!r}) — Jordan-form "
                        "bug")

    return eigenpairs


def _roots_of_irreducible(m_low: List[int], bits: int) -> List:
    """All roots (real ``float`` + complex ``complex``) of a monic irreducible
    integer polynomial ``m`` (low→high) — the embeddings for the Qalg projection.
    Reuses the exact isolation cascade on the companion matrix of ``m`` (so the
    Sturm real-root + argument-principle complex-root machinery is shared), but a
    degree-1 ``m`` is just its single rational root, handled directly."""
    m_low = _ipoly_trim(m_low)
    deg = len(m_low) - 1
    if deg == 1:                                     # m = m0 + x → root −m0
        return [float(-m_low[0])]
    # companion matrix of the MONIC m (low→high): roots of m are its eigenvalues.
    # C = [[0,...,0,−m0],[1,0,...,0,−m1],...,[0,...,1,−m_{n-1}]] (last col = −coeffs).
    comp = [[0] * deg for _ in range(deg)]
    for i in range(1, deg):
        comp[i][i - 1] = 1
    for i in range(deg):
        comp[i][deg - 1] = -m_low[i]
    # m is irreducible → its roots are all simple → eigvals_exact returns them all.
    evs = eigvals_exact(comp, bits=bits, include_complex=True)
    return list(evs)


# ── Part 3 — the complete-eigensolver CAPSTONE: matrix → exact Jordan form ────────
def jordan_form_exact(a, *, bits: int = 64, project: bool = True):
    """The canonical exact JORDAN CANONICAL FORM of an integer/rational matrix —
    every square matrix → ``A = P·J·P⁻¹`` with ``J`` the Jordan form (rc27, rc-G).

    The complete-eigensolver capstone: chains :func:`eig_exact` (char-poly →
    irreducible factors → exact roots → :func:`jordan_chains_exact` for every
    eigenvalue's generalized eigenvectors) into the canonical ``{P, J}`` decomposition.
    Unlike a numeric eig, this is exact even when ``A`` is DEFECTIVE (non-diagonalizable):
    the generalized eigenvectors / Jordan chains give a COMPLETE basis, and ``J``
    carries the genuine super-diagonal 1s of the defective blocks.

    ``a`` must be an INTEGER (or rational-integer) square matrix.

    Returns ``{"blocks": list[(eigenvalue, size)], "P": n×n generalized-eigenvector
    matrix (columns), "J": the n×n Jordan matrix}``. With ``project=True`` (default)
    ``eigenvalue`` / ``P`` / ``J`` are float/``complex``; with ``project=False`` the
    eigenvalues are exact :class:`~srmech.amsc.qalg.Qalg` and ``P`` / ``J`` are
    ``list[list[Qalg]]`` (exact). The blocks are ordered to match ``P``'s columns
    and ``J``'s diagonal blocks (chain by chain, bottom→top within each chain), so
    column ``c`` of ``P`` is the generalized eigenvector whose Jordan position is
    diagonal entry ``J[c][c]``.

    **SELF-VALIDATION** (asserted before returning): ``A·P == P·J`` EXACTLY over
    ``Qalg`` (the exact-substrate relation — no float in the check) AND ``A·P ≈ P·J``
    to ~1e-9 in the projected float/complex read-out. A clear ``ValueError`` is
    raised on any failure (it means an upstream bug).

    Ref: R. A. Horn & C. R. Johnson, *Matrix Analysis*, 2nd ed. (Cambridge, 2013),
    §3.1–3.2; G. H. Golub & C. F. Van Loan, *Matrix Computations*, 4th ed. §7.6.5.

    **Class L** (the spectral content) ∘ **Class J** (the irreducible-factor
    substrate) ∘ **Class N** (the exact ℚ(λ) field arithmetic) ∘ **Class K** (the
    terminal float/complex projection — rotation-last).
    """
    from srmech.amsc.qalg import Qalg

    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    if n == 0:
        return {"blocks": [], "P": [], "J": []}
    if any(len(r) != n for r in rows):
        raise ValueError(
            f"jordan_form_exact: a must be square 2-D; got {n}x{len(rows[0])}")

    cp = char_poly(a)
    cp_low = [int(c) for c in reversed(cp)]
    irr_factors = factor_integer_poly(cp_low)

    # gather, per eigenvalue, its Qalg value + chains (exact). Order eigenvalues by
    # the isolated embedding root (deterministic), matching eig_exact's sort.
    eig_entries: List[Tuple[complex, "Qalg", List[List[List]]]] = []
    for (m_tuple, _alg_mult) in irr_factors:
        m_low = list(m_tuple)
        if m_low[-1] != 1:
            raise ValueError(
                f"jordan_form_exact: irreducible factor {m_tuple} is not monic — "
                "char-poly factorisation inconsistent (internal bug)")
        m_int = tuple(int(c) for c in m_low)
        for root in _roots_of_irreducible(m_low, bits):
            lam = Qalg.alpha(m_int, root=root)
            chains, _block_sizes = jordan_chains_exact(a, lam)
            rc = complex(root)
            eig_entries.append((rc, lam, chains))
    eig_entries.sort(key=lambda t: (t[0].real, t[0].imag))

    # build the EXACT Qalg P (columns) + J (Jordan), chain by chain (bottom→top).
    # m for the field one/zero: every eigenvalue's Qalg shares no single m across
    # distinct factors, so build P/J entries per-eigenvalue with that λ's field, and
    # keep a global zero/one per cell from the column's own λ (the cells are filled
    # explicitly; untouched cells need a zero — use the FIRST eigenvalue's field for
    # those, since over ℂ they are all the rational 0). To keep one consistent field
    # for the J zeros we use each block's own λ.one()/λ-zero for its own cells and a
    # rational-0 placeholder elsewhere.
    blocks_out: List[Tuple] = []
    P_cols_qalg: List[List] = []                         # each a length-n Qalg column
    J_spec: List[Tuple["Qalg", int]] = []                # (λ_qalg, chain_len) per chain
    for (_rc, lam, chains) in eig_entries:
        for chain in chains:                             # chain bottom→top
            s = len(chain)
            for vec in chain:
                P_cols_qalg.append(list(vec))
            J_spec.append((lam, s))
            blocks_out.append((lam, s))

    # exact Qalg J (n×n) over a single shared scalar field: all entries are λ (a
    # Qalg) or 1/0 (rationals coerced into the column's λ field). We assemble J as a
    # list[list[Qalg]] where each diagonal cell carries its own λ's field and the
    # super-diagonal 1 / off cells carry that λ's one()/zero.
    # When eigenvalues span DIFFERENT number fields (distinct min-polys) there is no
    # single Qalg field holding all of P+J; each COLUMN of J lives in ITS OWN
    # eigenvalue's field (J is block-diagonal, so column c only ever couples to
    # column-c's block, same λ). So every cell of J carries a zero in that column's
    # field, keeping each column internally field-consistent — for both the exact
    # check and the project=False return.
    if not eig_entries:
        raise ValueError("jordan_form_exact: no eigenvalues found (internal bug)")
    # λ per column (chain by chain, bottom→top), in J_spec order.
    col_lam: List["Qalg"] = []
    for (lam, s) in J_spec:
        col_lam.extend([lam] * s)
    col_zero = [lam.one() - lam.one() for lam in col_lam]   # the rational 0 per column field

    J_qalg: List[List] = [[col_zero[c] for c in range(n)] for _ in range(n)]
    pos = 0
    for (lam, s) in J_spec:
        lone = lam.one()
        for k in range(s):
            J_qalg[pos + k][pos + k] = lam                # diagonal λ (this column's field)
            if k + 1 < s:
                J_qalg[pos + k][pos + k + 1] = lone       # super-diagonal 1 within chain
        pos += s

    # ── EXACT self-validation: A·P == P·J over Qalg (columnwise, per-column field) ──
    # A·P column c = A·P_cols[c]; P·J column c = Σ_k P_cols[k]·J[k][c]. Both stay in
    # column c's field (A entries are field-agnostic rational scalars; J[k][c] is
    # nonzero only for k in column c's block → same λ as P_cols[k]).
    def _col_equal_exact(c):
        zc = col_zero[c]
        # (A·P)[:,c]
        ap = []
        for i in range(n):
            acc = zc
            for j in range(n):
                acc = acc + P_cols_qalg[c][j] * rows[i][j]
            ap.append(acc)
        # (P·J)[:,c] = Σ_k P_cols[k] · J[k][c]
        pj = [zc for _ in range(n)]
        for k in range(n):
            jkc = J_qalg[k][c]
            if not jkc:
                continue
            for i in range(n):
                pj[i] = pj[i] + P_cols_qalg[k][i] * jkc
        for i in range(n):
            if ap[i] != pj[i]:
                return (i, ap[i], pj[i])
        return None

    for c in range(n):
        bad = _col_equal_exact(c)
        if bad is not None:
            i, av, pv = bad
            raise ValueError(
                "jordan_form_exact exact self-validation FAILED: A·P != P·J over "
                f"Qalg at row {i}, column {c} ({av!r} vs {pv!r}) — Jordan-form bug")

    if not project:
        return {"blocks": blocks_out, "P": _P_cols_to_matrix(P_cols_qalg, n),
                "J": J_qalg}

    # ── terminal projection — the ONE rotation ────────────────────────────────────
    def _proj_scalar(lam):
        r = lam.root
        return (lam.to_complex() if (isinstance(r, complex) and r.imag != 0)
                else complex(lam.to_float(), 0.0))

    def _proj_comp(comp, lam):
        r = lam.root
        real_root = not (isinstance(r, complex) and r.imag != 0)
        return comp.to_complex() if not real_root else complex(comp.to_float(), 0.0)

    # project P: column c belongs to the chain whose λ is J's diagonal at c
    # (``col_lam`` built above tracks λ per column in J_spec order).
    P_float = _P_cols_to_matrix(
        [[_proj_comp(P_cols_qalg[c][i], col_lam[c]) for i in range(n)]
         for c in range(n)], n)
    # Build J_float directly from J_spec (not by inspecting Qalg truthiness — a λ=0
    # diagonal would be falsy). λ on the diagonal, a super-diagonal 1 WITHIN a chain.
    J_float = [[0j] * n for _ in range(n)]
    pos = 0
    for (lam, s) in J_spec:
        lval = _proj_scalar(lam)
        for k in range(s):
            J_float[pos + k][pos + k] = lval
            if k + 1 < s:
                J_float[pos + k][pos + k + 1] = 1.0 + 0j
        pos += s
    blocks_float = [(_proj_scalar(lam), s) for (lam, s) in blocks_out]

    # float self-validation A·P ≈ P·J to ~1e-9.
    af = [[complex(rows[i][j]) for j in range(n)] for i in range(n)]
    Pm = P_float                                         # P[i][c]
    for c in range(n):
        ap = [sum(af[i][j] * Pm[j][c] for j in range(n)) for i in range(n)]
        pj = [sum(Pm[i][k] * J_float[k][c] for k in range(n)) for i in range(n)]
        for i in range(n):
            if _modulus(ap[i] - pj[i]) > 1e-9:
                raise ValueError(
                    "jordan_form_exact float self-validation FAILED: A·P != P·J at "
                    f"row {i}, column {c} ({ap[i]!r} vs {pj[i]!r}) — Jordan-form bug")

    return {"blocks": blocks_float, "P": P_float, "J": J_float}


def _P_cols_to_matrix(cols, n):
    """Assemble a list of COLUMN vectors (each length ``n``) into the row-major
    matrix ``P`` with those columns: ``P[i][c] = cols[c][i]``."""
    return [[cols[c][i] for c in range(len(cols))] for i in range(n)]
