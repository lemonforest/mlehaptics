"""srmech.amsc.cascade.matrix_cascades — QR + SVD as A-N cascades.

Per ``docs/srmech/notes/continuous_math_as_14_class_cascade.md``: the matrix
factorizations are not numpy-``linalg`` primitives, they are compositions of
the 14 A-N class operations built on srmech's own roots
(:func:`srmech.amsc.rational.sqrt` / :func:`~srmech.amsc.rational.hypot`) and
its own Hermitian eigendecomposition
(:func:`srmech.amsc.laplacian.hermitian_eigendecompose`, the cyclic-Jacobi
Class-L cascade). numpy is used ONLY as the array CONTAINER (matmul / outer /
slicing = the Class-M bind layer) — **never** as the decomposition engine:
there is no ``np.linalg.qr`` / ``np.linalg.svd`` anywhere in the call graph.

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
"""
from __future__ import annotations

from typing import Tuple

import numpy as np

from srmech.amsc.laplacian import hermitian_eigendecompose
from srmech.amsc.rational import hypot as _rhypot
from srmech.amsc.rational import sqrt as _rsqrt

__all__ = ["qr", "svd"]


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
