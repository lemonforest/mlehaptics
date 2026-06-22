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
           "eigvec_exact", "eigvec_exact_float"]


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
    Q = [[1 + 0j if i == j else 0j for j in range(m)] for i in range(m)]
    k = min(m, n)
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
    A_mat = _Mat.from_rows(arows, is_complex=is_cx)
    B_mat = _Mat.from_rows(b_rows, is_complex=is_cx)
    X = _mat_lstsq(A_mat, B_mat)                        # Mat (n, w)
    x_rows = [[complex(X[i, j]) for j in range(X.n_cols)] for i in range(X.n_rows)]
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
# discipline — find them numerically (float-QR ``mat_eigvals`` candidates), then
# CERTIFY each with the argument principle: the number of roots of an integer
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


def _certify_complex_root(p: List, cand: complex, others: List[complex],
                          bits: int) -> Tuple[_FR, _FR]:
    """Isolate ONE simple complex root of the integer/ℚ polynomial ``p`` near the
    numeric candidate ``cand`` and refine it to ``bits`` of precision. Grows /
    shrinks a JITTERED rational box around ``cand`` until ``_count_roots_in_box
    == 1``; then refines via :func:`_refine_box`. Returns the exact rational box
    center ``(re, im)``. The candidate-SEEDED path (the float-QR accelerator); the
    pure-subdivision :func:`_isolate_complex_roots_upper` is the always-works
    fallback when the candidates are unreliable."""
    cx = _FR(cand.real).limit_denominator(1 << 40)
    cy = _FR(cand.imag).limit_denominator(1 << 40)
    # Initial half-width: a fraction of the nearest-candidate gap (so the box can
    # only ever hold ONE root), floored to something small but nonzero.
    gap = None
    for o in others:
        d = _modulus(complex(o) - complex(cand))
        if d > 0 and (gap is None or d < gap):
            gap = d
    h = _FR(1, 1 << 8)
    if gap is not None and gap > 0:
        hg = _FR(gap).limit_denominator(1 << 40) / 4
        if hg > 0 and hg < h:
            h = hg
    hy = h * _FR(1021, 1024)                          # asymmetric → generic corners
    tries = 0
    while True:
        tries += 1
        if tries > 4000:
            raise ValueError(
                f"_certify_complex_root: failed to isolate a single root near "
                f"{cand!r} after {tries} attempts")
        hy = h * _FR(1021, 1024)
        try:
            c = _count_roots_in_box(p, cx - h, cx + h, cy - hy, cy + hy)
        except ValueError:
            h = h * _FR(9, 8)                          # boundary root → grow + re-jitter
            cx = cx + _FR(1, 1 << 50)
            continue
        if c == 1:
            break
        if c == 0:
            h = h * 2                                  # box too small → grow
            continue
        h = h / 2                                      # >1 root boxed → shrink
    return _refine_box(p, cx - h, cx + h, cy - hy, cy + hy, bits)


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
    count), each refined to ``bits`` of precision. The pure-subdivision fallback
    when the float-QR candidates are unreliable (e.g. QR stalls on a cyclic
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
        if guard > 200000:
            raise ValueError("_isolate_complex_roots_upper: subdivision did not terminate")
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
    **exactly isolated**: a float-QR candidate (:func:`~srmech.amsc.laplacian.mat_eigvals`)
    is CERTIFIED as a unique root of the exact integer characteristic polynomial in
    a rational box by the argument-principle count :func:`_count_roots_in_box`
    (winding number in exact ``Fraction`` arithmetic — no float in the count), then
    the box is refined to ``bits`` of precision; the emitted ``complex`` is the
    single terminal projection of the certified box center (the exact-substrate
    object is the integer char-poly + the certified isolating box). This is exact
    isolation — qualitatively distinct from the unconditioned float-QR spectrum of
    :func:`~srmech.amsc.laplacian.mat_eigvals`, whose candidates it merely seeds.
    Conjugate symmetry holds (``a+bi`` with ``b>0`` pairs with ``a−bi``). Returns
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

    # ── complex eigenvalues: certify the float-QR candidates exactly ──────────
    rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
    n = len(rows)
    n_real = len(eigs)
    if n_real == n:                                   # all-real spectrum — done
        return real_out
    n_complex = n - n_real                            # comes in conjugate pairs
    want_upper = n_complex // 2
    # PRIMARY: certify the float-QR candidates (the accelerator). FALLBACK: the
    # pure argument-principle subdivision, which never stalls (float-QR can — e.g.
    # on a cyclic permutation matrix). Either way EVERY emitted value is a CERTIFIED
    # unique root of the exact integer char-poly in a rational box (exact-substrate);
    # the float is the single terminal projection of the box center.
    upper_roots: List[complex] = []
    try:
        from srmech.amsc.mat import Mat
        cand = list(_mat_eigvals(Mat.from_rows(
            [[complex(v) for v in r] for r in rows], is_complex=True)))
        cplx_cands = [z for z in cand if z.imag != 0]
        upper_cands = sorted((z for z in cplx_cands if z.imag > 0),
                             key=lambda z: (round(z.real, 9), round(z.imag, 9)))
        if len(upper_cands) != want_upper:
            raise ValueError("candidate complex count mismatch — use subdivision")
        seen: List[Tuple[_FR, _FR]] = []
        for z in upper_cands:
            others = [w for w in cplx_cands if w is not z]
            cx, cy = _certify_complex_root(p, z, others, bits)
            seen.append((cx, cy))
            upper_roots.append(complex(float(cx), float(cy)))
    except (ValueError, AssertionError):
        # Float-QR was unreliable (stall / wrong count / un-isolable seed) — fall
        # back to the always-works exact subdivision from the Cauchy root bound.
        upper_roots = _isolate_complex_roots_upper(p, want_upper, bits)
    # Reconcile the certified count with the algebraic multiplicity from the
    # char-poly: the upper-half count must be exactly n_complex / 2.
    if len(upper_roots) != want_upper:
        raise ValueError(
            f"eigvals_exact: certified {len(upper_roots)} upper-half complex roots "
            f"but the char-poly multiplicity expects {want_upper} "
            f"(n={n}, real={n_real})")
    certified: List[complex] = []
    for z in upper_roots:
        certified.append(complex(z.real, z.imag))
        certified.append(complex(z.real, -z.imag))    # conjugate (im < 0)
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
