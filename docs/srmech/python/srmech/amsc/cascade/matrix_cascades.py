"""srmech.amsc.cascade.matrix_cascades — QR / SVD / lstsq / einsum / eig as A-N cascades.

Per ``docs/srmech/notes/continuous_math_as_14_class_cascade.md``: the matrix
factorizations and solvers are not numpy-``linalg`` primitives, they are
compositions of the 14 A-N class operations built on srmech's own roots
(:func:`srmech.amsc.rational.sqrt` / :func:`~srmech.amsc.rational.hypot`) and
its own Hermitian eigendecomposition
(:func:`srmech.amsc.laplacian.hermitian_eigendecompose`, the cyclic-Jacobi
Class-L cascade). numpy is used ONLY as the array CONTAINER (matmul / outer /
slicing = the Class-M bind layer) — **never** as the decomposition engine:
there is no ``np.linalg.{qr,svd,eig,eigh,lstsq}`` anywhere in the call graph.

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
  themselves match ``numpy.linalg.svd`` to round-off for well-conditioned
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
  ``numpy.linalg.eigvals`` to ~1e-12 for moderate sizes.
"""
from __future__ import annotations

import cmath
import itertools
from collections import Counter
from typing import Dict, List, Tuple

# numpy is the [scientific] extra (v0.7.0). This module mixes a numpy-free
# path with ndarray-typed ops; the lazy proxy keeps the module importable
# on a plain install and only the ndarray ops raise the [scientific] hint.
from srmech._scientific import lazy_numpy as _lazy_numpy
np = _lazy_numpy("srmech.amsc.cascade.matrix_cascades")

from srmech.amsc.laplacian import hermitian_eigendecompose
from srmech.amsc.rational import hypot as _rhypot
from srmech.amsc.rational import sqrt as _rsqrt

__all__ = ["qr", "svd", "lstsq", "einsum", "eigvals"]


def _modulus(z: complex) -> float:
    """|z| via the Class-N hypot cascade (no ``abs()`` — discipline)."""
    return _rhypot(float(z.real), float(z.imag))


def _norm2(v: np.ndarray) -> float:
    """Euclidean norm ‖v‖ = √(vᴴv) via the Class-N sqrt cascade. The
    sum-of-squares ``vᴴv`` is a Class-M bind (``np.vdot``); the root is
    :func:`srmech.amsc.rational.sqrt` — no ``np.linalg.norm`` / ``abs``."""
    sq = float(np.vdot(v, v).real)
    return _rsqrt(sq) if sq > 0.0 else 0.0


def qr(a, *, mode: str = "reduced") -> Tuple[np.ndarray, np.ndarray]:
    """Householder QR factorization ``A = Q·R``.

    Parameters
    ----------
    a
        ``(m, n)`` real or complex 2-D array-like.
    mode
        ``"reduced"`` (default, matching ``numpy.linalg.qr``): ``Q`` is
        ``(m, k)``, ``R`` is ``(k, n)`` with ``k = min(m, n)``.
        ``"complete"``: ``Q`` is ``(m, m)``, ``R`` is ``(m, n)``.

    Returns
    -------
    (Q, R)
        ``Q`` has orthonormal columns (``Qᴴ Q = I``), ``R`` is upper
        triangular. Q·R reconstructs A to round-off. QR is unique only up to
        column/row signs, so ``Q``/``R`` need not match ``numpy.linalg.qr``
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
        vhv = float(np.vdot(v, v).real)
        if vhv == 0.0:
            continue
        beta = 2.0 / vhv                              # Class N: 1/(vᴴv) scale
        # H = I − β v vᴴ applied to the trailing block (Class M outer bind).
        R[j:, :] -= beta * np.outer(v, np.conj(v) @ R[j:, :])
        Q[:, j:] -= beta * np.outer(Q[:, j:] @ v, np.conj(v))
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
        ``False`` (default, matching ``numpy.linalg.svd``'s reduced form):
        ``U`` is ``(m, k)``, ``s`` is ``(k,)``, ``Vh`` is ``(k, n)`` with
        ``k = min(m, n)``. (``full_matrices=True`` is not yet supplied; the
        reduced form is the one downstream consumers use.)

    Returns
    -------
    (U, s, Vh)
        ``s`` is the length-``k`` array of singular values in DESCENDING
        order (matching ``numpy.linalg.svd`` to round-off for well-
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
        gram = np.conj(A.T) @ A                      # AᴴA (n×n), Class M bind
        eigvals, V = hermitian_eigendecompose(gram)  # Class L
        order = np.argsort(eigvals)[::-1]            # descending
        V = V[:, order]
        s = np.array([_rsqrt(ev) if ev > 0.0 else 0.0 for ev in eigvals[order]])
        U = A @ V                                    # Class M
        for j in range(k):
            if s[j] > 0.0:
                U[:, j] = U[:, j] / s[j]             # Class N: U = A·V·Σ⁻¹
        Vh = np.conj(V.T)
    else:
        gram = A @ np.conj(A.T)                      # AAᴴ (m×m)
        eigvals, U = hermitian_eigendecompose(gram)
        order = np.argsort(eigvals)[::-1]
        U = U[:, order]
        s = np.array([_rsqrt(ev) if ev > 0.0 else 0.0 for ev in eigvals[order]])
        V = np.conj(A.T) @ U                         # Aᴴ·U
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
    ``numpy.linalg.lstsq(a, b)[0]`` to round-off for full-rank inputs.
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
    rhs = np.conj(Q.T) @ B                            # Class M: Qᴴ b
    x = np.zeros((n,) + B.shape[1:], dtype=np.complex128)
    for i in range(n - 1, -1, -1):                    # Class I: back-substitution
        x[i] = (rhs[i] - R[i, i + 1:] @ x[i + 1:]) / R[i, i]
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
    to ``numpy.einsum``.
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
    only as a SET; the multiset matches ``numpy.linalg.eigvals`` to ~1e-12 for
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
        disc = cmath.sqrt(tr * tr - 4.0 * det)        # Class C: complex shift root
        lam1 = (tr + disc) / 2.0
        lam2 = (tr - disc) / 2.0
        mu = lam1 if _modulus(lam1 - dd) < _modulus(lam2 - dd) else lam2
        eye = np.eye(m, dtype=np.complex128)
        Q, R = qr(H[:m, :m] - mu * eye)               # {QR}
        H[:m, :m] = R @ Q + mu * eye                  # Class K: A <- RQ + muI
        sweeps += 1
        if sweeps > max_sweeps * n:                   # no-silent-hang backstop
            for i in range(m):
                eigs.append(complex(H[i, i]))
            break
    return np.array(eigs, dtype=np.complex128)
