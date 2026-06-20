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

__all__ = ["qr", "svd", "lstsq", "einsum", "eigvals", "char_poly", "eigvals_exact"]


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


def eigvals_exact(a, *, bits: int = 64, return_intervals: bool = False):
    """Exact REAL eigenvalues of an integer matrix — the well-conditioned
    exact-until-rotation cascade (no Wilkinson ill-conditioning).

    ``char_poly`` (exact integer) → Yun square-free factorisation (exact
    multiplicities) → **Sturm** sign-sequence isolation (**Class C** sign-count at
    **Class K** interval boundaries) → rational **bisection** (**Class N** anchors
    → the algebraic asymptote), kept in exact ``Fraction`` arithmetic the whole
    way. Each eigenvalue stays an exact algebraic number until the single FPU
    lift. ``bits`` sets the refinement precision; ``return_intervals=True`` yields
    the exact ``(lo, hi)`` rational isolating intervals instead of floats.

    Returns the real eigenvalues ascending **with multiplicity**. A symmetric
    integer matrix has an all-real spectrum (complete); a matrix with complex
    eigenvalues returns only its real ones (exact complex isolation is a
    follow-up) — compare ``len(...)`` to the matrix order to detect that case.
    """
    cp = char_poly(a)                                # monic, high→low
    p = [_FR(c) for c in reversed(cp)]               # low→high over ℚ
    eigs: List[Tuple] = []
    for factor, mult in _square_free_factors(p):
        for (lo, hi) in _isolate_real_roots(factor, bits):
            for _ in range(mult):
                eigs.append((lo, hi))
    eigs.sort(key=lambda iv: iv[0] + iv[1])
    if return_intervals:
        return eigs
    return [float((lo + hi) / 2) for (lo, hi) in eigs]
