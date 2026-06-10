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
from collections import Counter
from typing import Dict, List, Tuple

# numpy is the [scientific] extra (v0.7.0). This module mixes a numpy-free
# path with ndarray-typed ops; the lazy proxy keeps the module importable
# on a plain install and only the ndarray ops raise the [scientific] hint.
from srmech._scientific import lazy_numpy as _lazy_numpy
np = _lazy_numpy("srmech.amsc.cascade.matrix_cascades")

from srmech.amsc.laplacian import (
    dense_dot_complex,
    dense_matmul_complex,
    dense_matvec_complex,
    dense_outer_complex,
    hermitian_eigendecompose,
)
from srmech.amsc.rational import hypot as _rhypot
from srmech.amsc.rational import sqrt as _rsqrt

__all__ = ["qr", "svd", "lstsq", "einsum", "eigvals", "char_poly", "eigvals_exact"]


def _modulus(z: complex) -> float:
    """|z| via the Class-N hypot cascade (no ``abs()`` — discipline)."""
    return _rhypot(float(z.real), float(z.imag))


def _complex_sqrt(w: complex) -> complex:
    """Principal complex square root via the Class-N real cascades — no
    ``cmath.sqrt``. For ``w = a + i·b``: ``|w|`` is the Class-N hypot cascade,
    and ``√w = √((|w|+a)/2) + i·sign(b)·√((|w|-a)/2)`` is two Class-N real
    ``sqrt`` cascades joined by a Class-K sign-branch (principal branch, ``Re ≥
    0``). Matches ``cmath.sqrt`` to ~1e-13; the continuous root stays a cascade
    of the 14 even on this float (round-off-faithful) path."""
    a = float(w.real)
    b = float(w.imag)
    if a == 0.0 and b == 0.0:
        return 0j
    m = _rhypot(a, b)                       # Class-N |w|  (≥ |a| exactly)
    re_arg = (m + a) / 2.0                  # both radicands ≥ 0 mathematically;
    im_arg = (m - a) / 2.0                  # a tiny <0 is float round-off →
    re = _rsqrt(re_arg) if re_arg > 0.0 else 0.0   # Class-K pin-slot at zero
    im = _rsqrt(im_arg) if im_arg > 0.0 else 0.0   # (the _norm2 idiom)
    return complex(re, im if b >= 0.0 else -im)    # Class-K sign-branch (no copysign)


def _norm2(v: np.ndarray) -> float:
    """Euclidean norm ‖v‖ = √(vᴴv) via the Class-N sqrt cascade. The
    sum-of-squares ``vᴴv`` is a Class-M bind (the Class-M self-bind) routed
    through :func:`dense_dot_complex` (``conj(v)`` passed explicitly — the
    Hermitian inner product); the root is :func:`srmech.amsc.rational.sqrt` —
    no ``NumPy norm`` / ``abs`` / numpy contraction engine."""
    sq = float(dense_dot_complex(np.conj(v), v).real)
    return _rsqrt(sq) if sq > 0.0 else 0.0


def qr(a, *, mode: str = "reduced") -> Tuple[np.ndarray, np.ndarray]:
    """Householder QR factorization ``A = Q·R``.

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
        ``Q`` has orthonormal columns (``Qᴴ Q = I``), ``R`` is upper
        triangular. Q·R reconstructs A to round-off. QR is unique only up to
        column/row signs, so ``Q``/``R`` need not match ``NumPy QR``
        element-wise — the defining INVARIANTS (reconstruction, orthonormal
        Q, upper-triangular R) do.
    """
    if mode not in ("reduced", "complete"):
        raise ValueError(f"mode must be 'reduced' or 'complete'; got {mode!r}")
    A = np.array(a, dtype=np.complex128)
    if A.ndim != 2:
        raise ValueError(f"a must be 2-D; got shape {A.shape}")
    m, n = A.shape
    R = A.copy()
    Q = np.eye(m, dtype=np.complex128)
    k = min(m, n)
    for j in range(k):
        x = R[j:, j].copy()
        normx = _norm2(x)
        if normx == 0.0:
            continue
        x0 = complex(x[0])
        modx0 = _modulus(x0)
        phase = (x0 / modx0) if modx0 > 0.0 else complex(1.0, 0.0)
        alpha = -phase * normx                       # Class K: pin-slot phase
        v = x.astype(np.complex128)
        v[0] = x0 - alpha
        vhv = float(dense_dot_complex(np.conj(v), v).real)
        if vhv == 0.0:
            continue
        beta = 2.0 / vhv                              # Class N: 1/(vᴴv) scale
        # H = I − β v vᴴ applied to the trailing block (Class M outer bind),
        # each matvec/outer routed through the dense_* kernel cascade (numpy
        # carriers-only — no numpy contraction/outer engine here).
        vh_R = dense_matvec_complex(R[j:, :].T, np.conj(v))   # conj(v)·R = Rᵀ·conj(v)
        R[j:, :] -= beta * dense_outer_complex(v, vh_R)
        Q_v = dense_matvec_complex(Q[:, j:], v)               # Q·v
        Q[:, j:] -= beta * dense_outer_complex(Q_v, np.conj(v))
    if mode == "reduced":
        Q = Q[:, :k].copy()
        R = R[:k, :].copy()
    if not np.iscomplexobj(a) and np.allclose(R.imag, 0.0) and np.allclose(Q.imag, 0.0):
        return Q.real.copy(), R.real.copy()
    return Q, R


def svd(a, *, full_matrices: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Singular value decomposition ``A = U·diag(s)·Vᴴ`` via the Gram-matrix
    Hermitian eigendecomposition.

    Parameters
    ----------
    a
        ``(m, n)`` real or complex 2-D array-like.
    full_matrices
        ``False`` (default, matching ``NumPy SVD``'s reduced form):
        ``U`` is ``(m, k)``, ``s`` is ``(k,)``, ``Vh`` is ``(k, n)`` with
        ``k = min(m, n)``. (``full_matrices=True`` is not yet supplied; the
        reduced form is the one downstream consumers use.)

    Returns
    -------
    (U, s, Vh)
        ``s`` is the length-``k`` array of singular values in DESCENDING
        order (matching ``NumPy SVD`` to round-off for well-
        conditioned inputs); ``U``/``Vh`` have orthonormal columns/rows and
        reconstruct ``A``. U/V are unique only up to signs, so they need not
        match numpy element-wise — the invariants do.
    """
    if full_matrices:
        raise NotImplementedError(
            "matrix_cascades.svd supplies the reduced form (full_matrices="
            "False); the full orthonormal completion is the follow-on."
        )
    A = np.array(a, dtype=np.complex128)
    if A.ndim != 2:
        raise ValueError(f"a must be 2-D; got shape {A.shape}")
    m, n = A.shape
    k = min(m, n)
    if k == 0:
        return (np.zeros((m, 0), dtype=np.complex128),
                np.zeros(0, dtype=np.float64),
                np.zeros((0, n), dtype=np.complex128))
    if m >= n:
        gram = dense_matmul_complex(np.conj(A.T), A)  # AᴴA (n×n); Class-L matmul cascade
        eigvals, V = hermitian_eigendecompose(gram)  # Class L
        order = np.argsort(eigvals)[::-1]            # descending
        V = V[:, order]
        s = np.array([_rsqrt(ev) if ev > 0.0 else 0.0 for ev in eigvals[order]])
        U = dense_matmul_complex(A, V)               # Class-L matmul cascade
        for j in range(k):
            if s[j] > 0.0:
                U[:, j] = U[:, j] / s[j]             # Class N: U = A·V·Σ⁻¹
        Vh = np.conj(V.T)
    else:
        gram = dense_matmul_complex(A, np.conj(A.T))  # AAᴴ (m×m); Class-L matmul cascade
        eigvals, U = hermitian_eigendecompose(gram)
        order = np.argsort(eigvals)[::-1]
        U = U[:, order]
        s = np.array([_rsqrt(ev) if ev > 0.0 else 0.0 for ev in eigvals[order]])
        V = dense_matmul_complex(np.conj(A.T), U)    # Aᴴ·U; Class-L matmul cascade
        for j in range(k):
            if s[j] > 0.0:
                V[:, j] = V[:, j] / s[j]
        Vh = np.conj(V.T)
    U = U[:, :k].copy()
    Vh = Vh[:k, :].copy()
    if not np.iscomplexobj(a) and np.allclose(U.imag, 0.0) and np.allclose(Vh.imag, 0.0):
        return U.real.copy(), s, Vh.real.copy()
    return U, s, Vh


def lstsq(a, b) -> np.ndarray:
    """Least-squares solution of ``A x = b`` (minimising ``‖A x − b‖``).

    **{QR}** factorization ∘ **Class M** (the ``Qᴴ b`` product) ∘ **Class I**
    (back-substitution = the ordered triangular solve). Supports the
    overdetermined / square case ``m ≥ n`` (full column rank); ``b`` may be a
    vector ``(m,)`` or a stack of right-hand sides ``(m, k)``. The
    underdetermined ``m < n`` min-norm solution is the follow-on.

    Returns the solution ``x`` (shape ``(n,)`` or ``(n, k)``), matching
    ``NumPy lstsq(a, b)[0]`` to round-off for full-rank inputs.
    """
    A = np.array(a, dtype=np.complex128)
    B = np.array(b, dtype=np.complex128)
    if A.ndim != 2:
        raise ValueError(f"a must be 2-D; got shape {A.shape}")
    m, n = A.shape
    if m < n:
        raise NotImplementedError(
            "matrix_cascades.lstsq supplies the overdetermined/square (m>=n) "
            "QR path; the underdetermined min-norm case is the follow-on."
        )
    Q, R = qr(A)                                      # reduced: Q (m,n), R (n,n)
    Qh = np.conj(Q.T)                                 # Qᴴ (carrier transpose+conj)
    # Class M: Qᴴ·b routed through the dense_* kernel cascade (matvec for a 1-D
    # rhs, matmul for a multi-column rhs — numpy carriers-only, no numpy matmul).
    rhs = (dense_matvec_complex(Qh, B) if B.ndim == 1
           else dense_matmul_complex(Qh, B))
    x = np.zeros((n,) + B.shape[1:], dtype=np.complex128)
    for i in range(n - 1, -1, -1):                    # Class I: back-substitution
        tail = R[i, i + 1:]                           # the already-solved span
        if tail.shape[0] == 0:
            acc = 0.0                                 # nothing solved above row i
        elif x.ndim == 1:
            acc = dense_dot_complex(tail, x[i + 1:])  # 1-D rhs: a Class-M dot
        else:
            acc = dense_matvec_complex(x[i + 1:].T, tail)  # k-col rhs: xᵀ·tail
        x[i] = (rhs[i] - acc) / R[i, i]
    if not np.iscomplexobj(a) and not np.iscomplexobj(b) and np.allclose(x.imag, 0.0):
        return x.real.copy()
    return x


def einsum(subscripts: str, *operands) -> np.ndarray:
    """Einstein-summation tensor contraction via the index-iteration definition.

    **Class B/D** (the subscript string is a typed index-pattern spec) ∘
    **Class I** (iterate over every free + summed index tuple) ∘ **Class M**
    (the sum-of-products bundle). This is the *general* definition — it handles
    any subscript string (``'ij,jk->ik'`` matmul, ``'ii->'`` trace, ``'ij->ji'``
    transpose, ``'i,i->'`` dot, ``'i,j->ij'`` outer, arbitrary contractions),
    just unoptimised (no path planning). Implicit output (no ``->``) follows
    numpy's rule: free labels (appearing once) in sorted order. Value-faithful
    to the NumPy einsum contraction.
    """
    ops = [np.asarray(o, dtype=np.complex128) for o in operands]
    inspec, arrow, outspec = subscripts.replace(" ", "").partition("->")
    in_labels = inspec.split(",")
    if len(in_labels) != len(ops):
        raise ValueError(
            f"einsum: {len(in_labels)} operand specs but {len(ops)} operands"
        )
    sizes: Dict[str, int] = {}
    for labels, op in zip(in_labels, ops):
        if len(labels) != op.ndim:
            raise ValueError(
                f"einsum: spec {labels!r} rank {len(labels)} != operand ndim {op.ndim}"
            )
        for axis, lab in enumerate(labels):
            sizes[lab] = op.shape[axis]
    if arrow == "":                                   # implicit output (Class B/D)
        counts = Counter("".join(in_labels))
        outspec = "".join(sorted(lab for lab in counts if counts[lab] == 1))
    summed = [lab for lab in sizes if lab not in outspec]
    out = np.zeros(tuple(sizes[lab] for lab in outspec), dtype=np.complex128)
    free_ranges = [range(sizes[lab]) for lab in outspec]
    sum_ranges = [range(sizes[lab]) for lab in summed]
    for free_idx in itertools.product(*free_ranges):  # Class I: free indices
        index_map = dict(zip(outspec, free_idx))
        acc = 0j
        for sum_idx in itertools.product(*sum_ranges):  # Class I: summed indices
            index_map.update(zip(summed, sum_idx))
            term = complex(1.0, 0.0)
            for labels, op in zip(in_labels, ops):
                term *= op[tuple(index_map[lab] for lab in labels)]  # Class M
            acc += term
        out[free_idx] = acc
    if not any(np.iscomplexobj(o) for o in operands) and np.allclose(out.imag, 0.0):
        return out.real.copy()
    return out


_EIG_DEFLATE_TOL = 1e-14


def eigvals(a, *, max_sweeps: int = 500) -> np.ndarray:
    """Eigenvalues of a general (non-Hermitian) square matrix via shifted QR.

    **Class K** (iterate-to-convergence asymptotic-DoF) ∘ **Class L** (the
    spectral content) ∘ **{QR}** (the per-step factorization, srmech's
    Householder :func:`qr`) ∘ **Class C** (the Wilkinson spectral shifts). The
    iteration runs in complex arithmetic, so it converges to complex
    eigenvalues of real matrices directly (the 2×2 rotation ``[[0,−1],[1,0]]``
    yields ``±i``). Deflates a Schur eigenvalue whenever the trailing
    subdiagonal entry falls below :data:`_EIG_DEFLATE_TOL` of the local scale.

    Returns the length-``n`` complex eigenvalue array. Eigenvalues are unique
    only as a SET; the multiset matches ``NumPy eigvals`` to ~1e-12 for
    moderate sizes (the Hermitian-input case is the already-shipped special
    case — pure **Class L**, the cyclic Jacobi — and is exact there).
    """
    H = np.array(a, dtype=np.complex128)
    if H.ndim != 2 or H.shape[0] != H.shape[1]:
        raise ValueError(f"a must be square 2-D; got shape {H.shape}")
    n = H.shape[0]
    if n == 0:
        return np.zeros(0, dtype=np.complex128)
    eigs: List[complex] = []
    m = n
    sweeps = 0
    while m > 0:
        if m == 1:
            eigs.append(complex(H[0, 0]))
            break
        scale = _modulus(H[m - 2, m - 2]) + _modulus(H[m - 1, m - 1])
        if _modulus(H[m - 1, m - 2]) <= _EIG_DEFLATE_TOL * (scale + 1e-300):
            eigs.append(complex(H[m - 1, m - 1]))     # Class L: deflate eigenvalue
            m -= 1
            continue
        # Wilkinson shift: the trailing-2×2 eigenvalue closest to H[m-1,m-1].
        aa, bb = H[m - 2, m - 2], H[m - 2, m - 1]
        cc, dd = H[m - 1, m - 2], H[m - 1, m - 1]
        tr = aa + dd
        det = aa * dd - bb * cc
        disc = _complex_sqrt(tr * tr - 4.0 * det)     # Class C: complex shift root (Class-N cascade)
        lam1 = (tr + disc) / 2.0
        lam2 = (tr - disc) / 2.0
        mu = lam1 if _modulus(lam1 - dd) < _modulus(lam2 - dd) else lam2
        eye = np.eye(m, dtype=np.complex128)
        Q, R = qr(H[:m, :m] - mu * eye)               # {QR}
        # Class K: A <- RQ + muI; the RQ contraction via the Class-L matmul cascade.
        H[:m, :m] = dense_matmul_complex(R, Q) + mu * eye
        sweeps += 1
        if sweeps > max_sweeps * n:                   # no-silent-hang backstop
            for i in range(m):
                eigs.append(complex(H[i, i]))
            break
    return np.array(eigs, dtype=np.complex128)


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
