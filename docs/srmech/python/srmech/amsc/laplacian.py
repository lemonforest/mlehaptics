"""Class L — graph-Laplacian primitive (Task #217 Phase C1).

Public Python surface for four load-bearing graph-Laplacian operations.
Each operation dispatches to the native C implementation when
``srmech.amsc._native`` loaded successfully (``HAS_NATIVE = True``) and
the input size fits the C-path bound (``n ≤ 256``); falls back to a
numpy implementation otherwise.

Class L is the structural workhorse of Spike #24's cumulative
cross-substrate audit (instantiated at six of six bonus substrates).
The closed-form spectrum of a cyclic graph (``λ_k = 2(1 − cos(2πk/n))``)
is pi-bearing and NOT shipped on the C surface per
`[[user_stance_pi_as_projection]]`; users computing cyclic-graph
spectra should compose Class I (cyclic-group representation, pi-free
modular arithmetic) with Class L's dense-Laplacian build + Jacobi
eigvals, or use numpy/scipy at the Python layer for the trig-bearing
shortcut.

API
---

- :func:`dense_adjacency` — ``A`` from edge list, n×n dense.
- :func:`dense_laplacian` — ``L = D − A``.
- :func:`normalized_laplacian` — ``L_sym = I − D^(−1/2) A D^(−1/2)``.
- :func:`jacobi_eigvals` — symmetric Jacobi eigendecomposition (small ``n``).

Inputs
------

- ``n`` (int): number of nodes.
- ``edges`` (iterable of (u, v) pairs): undirected edges (uint32-range).
- ``weights`` (optional iterable of floats): per-edge weight; ``None``
  → unit weights.
- ``matrix`` (numpy.ndarray, shape ``(n, n)``, dtype ``float64``): for
  :func:`jacobi_eigvals`, the symmetric matrix to decompose.

Outputs
-------

All operations return ``numpy.ndarray`` of dtype ``float64``. Matrices
are row-major ``(n, n)``; eigvals are length-``n`` 1-D.

C-path bound
------------

The C native path operates on ``n ≤ 256`` (caps the stack-allocated
degree / row-scaling buffers at ~2 KB, embedded-safe). For ``n > 256``
the wrappers fall back to numpy unconditionally; HAS_NATIVE doesn't
matter. Cascade-composition use-cases typically stay well under this
bound (per-factor ``C_n`` with ``n ≤ 30`` in bonus 10).
"""

from __future__ import annotations

import ctypes
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np

from . import _native

__all__ = [
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "jacobi_eigvals",
    "MAX_NATIVE_NODES",
]

MAX_NATIVE_NODES: int = 256


def _normalize_edges_weights(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"n must be non-negative int; got {n!r}")
    if n > 0xFFFF_FFFF:
        raise ValueError(f"n exceeds uint32 range; got {n}")
    edge_list = [tuple(e) for e in edges]
    n_edges = len(edge_list)
    edges_u = np.empty(n_edges, dtype=np.uint32)
    edges_v = np.empty(n_edges, dtype=np.uint32)
    for i, (uu, vv) in enumerate(edge_list):
        if not (0 <= uu < n and 0 <= vv < n):
            raise ValueError(
                f"edge {i} = ({uu}, {vv}) outside node range [0, {n})"
            )
        edges_u[i] = uu
        edges_v[i] = vv
    if weights is None:
        ws = np.ones(n_edges, dtype=np.float64)
    else:
        ws = np.asarray(list(weights), dtype=np.float64)
        if ws.shape != (n_edges,):
            raise ValueError(
                f"weights length {ws.shape[0]} != n_edges {n_edges}"
            )
    return edges_u, edges_v, ws


def _can_dispatch_native(n: int) -> bool:
    return (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and n <= MAX_NATIVE_NODES
    )


def _build_matrix_native(
    fn_name: str,
    n: int,
    edges_u: np.ndarray,
    edges_v: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    assert _native.LIB is not None
    out = np.zeros((n, n), dtype=np.float64)
    fn = getattr(_native.LIB, fn_name)
    n_edges = int(edges_u.shape[0])
    eu_ptr = edges_u.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
    ev_ptr = edges_v.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
    w_ptr = weights.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    out_ptr = out.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    rc = fn(
        ctypes.c_uint32(n),
        ctypes.c_uint32(n_edges),
        eu_ptr if n_edges > 0 else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32)),
        ev_ptr if n_edges > 0 else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32)),
        w_ptr if n_edges > 0 else ctypes.cast(None, ctypes.POINTER(ctypes.c_double)),
        out_ptr,
    )
    if rc == _native.SRMECH_ERR_OVERFLOW:
        raise OverflowError(f"{fn_name} requires n <= {MAX_NATIVE_NODES}; got {n}")
    if rc != _native.SRMECH_OK:
        raise RuntimeError(f"{fn_name} returned non-OK status {rc}")
    return out


def _fallback_dense_adjacency(
    n: int,
    edges_u: np.ndarray,
    edges_v: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    A = np.zeros((n, n), dtype=np.float64)
    for u, v, w in zip(edges_u, edges_v, weights):
        u_i, v_i = int(u), int(v)
        A[u_i, v_i] += float(w)
        if u_i != v_i:
            A[v_i, u_i] += float(w)
    return A


def dense_adjacency(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> np.ndarray:
    """Build the dense ``n×n`` adjacency matrix from an undirected edge
    list.

    Self-loops add ``2*w`` to the diagonal (standard graph-theory
    convention). Parallel edges accumulate weights additively.
    """
    edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
    if _can_dispatch_native(n):
        return _build_matrix_native(
            "srmech_graph_dense_adjacency", n, edges_u, edges_v, ws
        )
    return _fallback_dense_adjacency(n, edges_u, edges_v, ws)


def dense_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> np.ndarray:
    """Combinatorial graph Laplacian ``L = D − A``.

    Returns an ``n×n`` symmetric positive-semidefinite matrix. For a
    connected graph the smallest eigenvalue is 0 with multiplicity 1
    (Fiedler vector spans the complement).
    """
    edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
    if _can_dispatch_native(n):
        return _build_matrix_native(
            "srmech_graph_dense_laplacian", n, edges_u, edges_v, ws
        )
    A = _fallback_dense_adjacency(n, edges_u, edges_v, ws)
    # Degree = sum over off-diagonal entries per row.
    diag_idx = np.arange(n)
    A_off = A.copy()
    A_off[diag_idx, diag_idx] = 0.0
    deg = A_off.sum(axis=1)
    L = -A_off
    L[diag_idx, diag_idx] = deg
    return L


def normalized_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> np.ndarray:
    """Symmetric normalised Laplacian ``L_sym = I − D^(−1/2) A D^(−1/2)``.

    Isolated vertices (degree 0) have diagonal entry 0 by convention
    (not 1; the ``I`` term only applies where ``D > 0``).
    """
    edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
    if _can_dispatch_native(n):
        return _build_matrix_native(
            "srmech_graph_normalized_laplacian", n, edges_u, edges_v, ws
        )
    A = _fallback_dense_adjacency(n, edges_u, edges_v, ws)
    diag_idx = np.arange(n)
    A_off = A.copy()
    A_off[diag_idx, diag_idx] = 0.0
    deg = A_off.sum(axis=1)
    d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(np.where(deg > 0, deg, 1.0)), 0.0)
    L = np.zeros((n, n), dtype=np.float64)
    # Off-diagonal: -A[r,c] * d_inv_sqrt[r] * d_inv_sqrt[c]
    L = -A_off * d_inv_sqrt[:, None] * d_inv_sqrt[None, :]
    # Diagonal: 1 where d > 0, else 0
    L[diag_idx, diag_idx] = (deg > 0).astype(np.float64)
    return L


def jacobi_eigvals(
    matrix: np.ndarray,
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
) -> np.ndarray:
    """Symmetric Jacobi eigendecomposition.

    Returns the sorted (ascending) eigenvalues of a real symmetric
    matrix. The C path is bounded by ``MAX_NATIVE_NODES = 256`` and
    uses an in-place algebraic Jacobi rotation (pi-free). For larger
    ``n`` (or when ``HAS_NATIVE`` is False) the fallback uses
    ``numpy.linalg.eigvalsh``.

    ``matrix`` is **not** modified by the wrapper — a copy is made
    before the in-place C path runs.
    """
    M = np.ascontiguousarray(matrix, dtype=np.float64)
    if M.ndim != 2 or M.shape[0] != M.shape[1]:
        raise ValueError(f"matrix must be square 2-D; got shape {M.shape}")
    n = M.shape[0]
    if _can_dispatch_native(n):
        work = np.ascontiguousarray(M.copy(), dtype=np.float64)
        out = np.zeros(n, dtype=np.float64)
        rc = _native.LIB.srmech_jacobi_eigvals(
            ctypes.c_uint32(n),
            work.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            ctypes.c_uint32(int(max_sweeps)),
            ctypes.c_double(float(tolerance)),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_ERR_OVERFLOW:
            return np.sort(np.linalg.eigvalsh(M))
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_jacobi_eigvals returned non-OK status {rc}")
        return np.sort(out)
    return np.sort(np.linalg.eigvalsh(M))
