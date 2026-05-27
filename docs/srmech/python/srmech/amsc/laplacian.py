"""Class L — graph-Laplacian + dense-matrix linear algebra primitive.

ADR-0002 Phase 2 broadening (v0.4.1rc5): Class L's identity broadens
from "graph Laplacian" to "dense-matrix linear algebra including
eigendecomposition, matrix-vector multiplication, and elementwise
operations on dense arrays". The graph-Laplacian-specific ops
(``dense_adjacency``, ``dense_laplacian``, ``normalized_laplacian``,
``jacobi_eigvals``) remain specialisations of the general dense-matrix
scope. Four new ops added to accommodate the closed-form TDSE
evolution ``ψ(t) = V·diag(exp(-iλt))·V^H·ψ(0)`` (Sakurai *Modern QM*
§2.1.5 eq 2.1.40):

- :func:`hermitian_eigendecompose` — complex Hermitian generalisation
  of :func:`jacobi_eigvals` returning eigenvalues + unitary eigvecs.
- :func:`dense_matvec_complex` — general complex ``M @ v``.
- :func:`elementwise_multiply_complex` — vectorised ``a * b``.
- :func:`elementwise_transcendental` — array-vectorised ``exp/cos/sin
  /log`` plus the TDSE-relevant ``exp_i(x) = exp(1j*x)``.

The broadening is a *dissolve-before-promote* per
``[[feedback_no_privileged_primitive_classes]]`` — no Class P promoted;
vocabulary stays at 14 classes A–N. See ADR-0002 Phase 1 §4 spike
finding and the Phase 1 report
(``docs/srmech/notes/adr_0002_phase_1_dsl_design_2026-05-16.md``) for
the dissolve rationale.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``:

- Hermitian eigendecomposition: Golub & Van Loan, *Matrix Computations*
  (4th ed., Johns Hopkins, 2013) §8.4 (Jacobi method), §8.5
  (Hermitian-specific via unitary rotations).
- Matrix-vector multiplication: Golub & Van Loan §1.1.
- Elementwise transcendentals: ANSI C99 §7.12 libm (``exp``, ``cos``,
  ``sin``, ``log``).
- TDSE motivation: Sakurai, *Modern Quantum Mechanics* (3rd ed.,
  Cambridge, 2021) §2.1.5 eq 2.1.40.

Class L is the structural workhorse of Spike #24's cumulative
cross-substrate audit (instantiated at six of six bonus substrates).
The closed-form spectrum of a cyclic graph (``λ_k = 2(1 − cos(2πk/n))``)
is pi-bearing and NOT shipped on the C surface per
``[[user_stance_pi_as_projection]]``; users computing cyclic-graph
spectra should compose Class I (cyclic-group representation, pi-free
modular arithmetic) with Class L's dense-Laplacian build + Jacobi
eigvals, or use numpy/scipy at the Python layer for the trig-bearing
shortcut.

API
---

Graph-Laplacian specialisations (original Class L surface):

- :func:`dense_adjacency` — ``A`` from edge list, n×n dense.
- :func:`dense_laplacian` — ``L = D − A``.
- :func:`normalized_laplacian` — ``L_sym = I − D^(−1/2) A D^(−1/2)``.
- :func:`jacobi_eigvals` — symmetric Jacobi eigendecomposition (small ``n``).

Phase 2 broadening (dense-matrix linear algebra):

- :func:`hermitian_eigendecompose` — Hermitian eigendecomposition.
- :func:`dense_matvec_complex` — complex matrix-vector multiplication.
- :func:`elementwise_multiply_complex` — pointwise complex multiply.
- :func:`elementwise_transcendental` — vectorised transcendentals.

The module-level :data:`LAPLACIAN_OPS` constant exposes all available
op names for the composition-engine registry.

C-path bound
------------

The C native path operates on ``n ≤ 256`` (caps the stack-allocated
degree / row-scaling buffers, embedded-safe). For ``n > 256`` the
wrappers fall back to numpy unconditionally; HAS_NATIVE doesn't
matter. Cascade-composition use-cases typically stay well under this
bound.
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
    "hermitian_eigendecompose",
    "symmetric_eigendecompose",
    "dense_matvec_complex",
    "elementwise_multiply_complex",
    "elementwise_transcendental",
    "LAPLACIAN_OPS",
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
        # Both writes always execute; for self-loops (u == v) they hit
        # the same cell and naturally accumulate 2*w on the diagonal
        # (standard graph-theory convention; matches the C path).
        A[u_i, v_i] += float(w)
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


# =====================================================================
# ADR-0002 Phase 2 — Class L broadening
# =====================================================================
#
# Complex numbers travel as interleaved-double pairs (re, im) on the
# C boundary. The helpers below convert between numpy complex arrays
# and the interleaved-double representation.


def _complex_to_interleaved(arr: np.ndarray) -> np.ndarray:
    """View a complex128 array as interleaved float64 (re, im pairs).

    Returns a 1-D contiguous float64 array of length 2*arr.size.
    """
    c = np.ascontiguousarray(arr, dtype=np.complex128)
    return c.view(np.float64).reshape(-1).copy()


def _interleaved_to_complex(arr: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    """Reconstruct complex128 array of the given shape from interleaved
    float64 (re, im pairs).
    """
    a = np.ascontiguousarray(arr, dtype=np.float64).reshape(-1)
    return a.view(np.complex128).reshape(shape).copy()


def hermitian_eigendecompose(
    H: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Hermitian eigendecomposition: ``H = V · diag(eigvals) · V^H``.

    Parameters
    ----------
    H
        ``(n, n)`` complex Hermitian matrix (dtype castable to
        complex128). Hermiticity is not enforced (caller's
        responsibility); a non-Hermitian input will produce undefined
        rotation behaviour in the C path.

    Returns
    -------
    (eigvals, V)
        ``eigvals`` is a length-``n`` float64 array of real eigenvalues
        in ascending order. ``V`` is an ``(n, n)`` complex128 unitary
        matrix whose columns are the corresponding eigenvectors.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed.,
    Johns Hopkins, 2013) §8.5 (Hermitian eigendecomposition via
    unitary Jacobi rotations).

    Dispatch: native C path for ``n ≤ MAX_NATIVE_NODES`` when
    ``HAS_NATIVE``; falls back to ``numpy.linalg.eigh`` otherwise.
    """
    H_arr = np.ascontiguousarray(H, dtype=np.complex128)
    if H_arr.ndim != 2 or H_arr.shape[0] != H_arr.shape[1]:
        raise ValueError(f"H must be square 2-D; got shape {H_arr.shape}")
    n = H_arr.shape[0]
    if n == 0:
        return (np.zeros(0, dtype=np.float64),
                np.zeros((0, 0), dtype=np.complex128))
    if _can_dispatch_native(n):
        H_il = _complex_to_interleaved(H_arr)
        eigvals = np.zeros(n, dtype=np.float64)
        V_il = np.zeros(2 * n * n, dtype=np.float64)
        rc = _native.LIB.srmech_hermitian_eigendecompose(
            ctypes.c_uint32(n),
            H_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            eigvals.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            V_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_OK:
            V = _interleaved_to_complex(V_il, (n, n))
            return eigvals, V
        # Convergence failure or other non-OK: fall back to numpy.
    eigvals, V = np.linalg.eigh(H_arr)
    return eigvals, V


def symmetric_eigendecompose(
    L: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Real-symmetric eigendecomposition: ``L = V · diag(eigvals) · Vᵀ``.

    Real-input specialisation of :func:`hermitian_eigendecompose`.
    Guarantees real float64 ``eigvals`` AND real float64 eigenvectors
    ``V`` (the Hermitian path returns complex128 ``V``, which triggers
    a ``ComplexWarning`` when a caller knows the input is real-symmetric
    — e.g. a graph Laplacian).

    Parameters
    ----------
    L
        ``(n, n)`` real symmetric matrix (dtype castable to float64).
        Symmetry is not enforced (caller's responsibility); only the
        lower triangle is referenced by ``numpy.linalg.eigh``.

    Returns
    -------
    (eigvals, V)
        ``eigvals`` is a length-``n`` float64 array of real eigenvalues
        in ascending order. ``V`` is an ``(n, n)`` float64 orthogonal
        matrix whose columns are the corresponding eigenvectors.

    Class L. Canonical SSoT: Golub & Van Loan, *Matrix Computations*
    (4th ed., Johns Hopkins, 2013) §8.3 (symmetric eigenproblem).

    Computed via ``numpy.linalg.eigh``; no native C dispatch (eigvector
    sign / degenerate-subspace rotation is non-unique, so C/Python
    element-wise parity is not meaningful — correctness is pinned by
    eigenvalues + reconstruction + orthonormality instead).
    """
    L_arr = np.ascontiguousarray(np.real(np.asarray(L)), dtype=np.float64)
    if L_arr.ndim != 2 or L_arr.shape[0] != L_arr.shape[1]:
        raise ValueError(f"L must be square 2-D; got shape {L_arr.shape}")
    n = L_arr.shape[0]
    if n == 0:
        return (np.zeros(0, dtype=np.float64),
                np.zeros((0, 0), dtype=np.float64))
    eigvals, V = np.linalg.eigh(L_arr)
    return (np.ascontiguousarray(eigvals, dtype=np.float64),
            np.ascontiguousarray(V, dtype=np.float64))


def dense_matvec_complex(M: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Dense complex matrix-vector multiplication: ``M @ v``.

    Parameters
    ----------
    M
        ``(rows, cols)`` complex matrix.
    v
        Length-``cols`` complex vector.

    Returns
    -------
    out
        Length-``rows`` complex128 array.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix-vector
    multiplication).
    """
    M_arr = np.ascontiguousarray(M, dtype=np.complex128)
    v_arr = np.ascontiguousarray(v, dtype=np.complex128).reshape(-1)
    if M_arr.ndim != 2:
        raise ValueError(f"M must be 2-D; got ndim {M_arr.ndim}")
    rows, cols = M_arr.shape
    if v_arr.shape[0] != cols:
        raise ValueError(
            f"M shape {M_arr.shape} incompatible with v length "
            f"{v_arr.shape[0]}"
        )
    if (_native.HAS_NATIVE
            and _native.LIB is not None
            and rows <= MAX_NATIVE_NODES
            and cols <= MAX_NATIVE_NODES):
        M_il = _complex_to_interleaved(M_arr)
        v_il = _complex_to_interleaved(v_arr)
        out_il = np.zeros(2 * rows, dtype=np.float64)
        rc = _native.LIB.srmech_dense_matvec_complex(
            ctypes.c_uint32(rows),
            ctypes.c_uint32(cols),
            M_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            v_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            out_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_OK:
            return _interleaved_to_complex(out_il, (rows,))
    return (M_arr @ v_arr).astype(np.complex128)


def elementwise_multiply_complex(
    a: np.ndarray, b: np.ndarray
) -> np.ndarray:
    """Elementwise complex multiplication: ``a * b``.

    Both arrays must be the same shape (after broadcasting via
    ``numpy.broadcast``). Returns complex128.
    """
    a_arr = np.ascontiguousarray(np.broadcast_to(a,
                                  np.broadcast_shapes(np.shape(a), np.shape(b))),
                                 dtype=np.complex128)
    b_arr = np.ascontiguousarray(np.broadcast_to(b, a_arr.shape),
                                 dtype=np.complex128)
    n = int(a_arr.size)
    if n == 0:
        return np.zeros_like(a_arr)
    if _native.HAS_NATIVE and _native.LIB is not None:
        a_il = _complex_to_interleaved(a_arr.reshape(-1))
        b_il = _complex_to_interleaved(b_arr.reshape(-1))
        out_il = np.zeros(2 * n, dtype=np.float64)
        rc = _native.LIB.srmech_elementwise_multiply_complex(
            ctypes.c_uint32(n),
            a_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            b_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            out_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_OK:
            return _interleaved_to_complex(out_il, a_arr.shape)
    return (a_arr * b_arr).astype(np.complex128)


_TRANS_OP_IDS = {
    "exp": _native.SRMECH_TRANS_EXP,
    "cos": _native.SRMECH_TRANS_COS,
    "sin": _native.SRMECH_TRANS_SIN,
    "log": _native.SRMECH_TRANS_LOG,
}


def elementwise_transcendental(
    arr: np.ndarray, op_name: str
) -> np.ndarray:
    """Array-vectorised transcendental operation.

    Parameters
    ----------
    arr
        Real or complex array.
    op_name
        One of ``"exp"``, ``"cos"``, ``"sin"``, ``"log"``, ``"exp_i"``.
        ``"exp_i"`` returns ``exp(1j * arr)`` (the TDSE-relevant
        complex exponential of a real argument); the C path
        implements this via ``cos`` + ``sin`` over the real argument.

    Returns
    -------
    out
        Array of the same shape as ``arr``. dtype is complex128 for
        ``"exp_i"`` (or when ``arr`` itself is complex); float64
        otherwise.

    Canonical SSoT: ANSI C99 §7.12 libm.
    """
    if op_name == "exp_i":
        real_arr = np.ascontiguousarray(arr, dtype=np.float64).reshape(-1)
        n = int(real_arr.size)
        cos_out = np.zeros(n, dtype=np.float64)
        sin_out = np.zeros(n, dtype=np.float64)
        used_native = False
        if n > 0 and _native.HAS_NATIVE and _native.LIB is not None:
            rc_c = _native.LIB.srmech_elementwise_transcendental(
                ctypes.c_uint32(n),
                real_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                ctypes.c_int(_native.SRMECH_TRANS_COS),
                cos_out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            )
            rc_s = _native.LIB.srmech_elementwise_transcendental(
                ctypes.c_uint32(n),
                real_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                ctypes.c_int(_native.SRMECH_TRANS_SIN),
                sin_out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            )
            if rc_c == _native.SRMECH_OK and rc_s == _native.SRMECH_OK:
                used_native = True
        if not used_native:
            cos_out = np.cos(real_arr)
            sin_out = np.sin(real_arr)
        result = (cos_out + 1j * sin_out).astype(np.complex128)
        return result.reshape(np.shape(arr))
    if op_name not in _TRANS_OP_IDS:
        raise ValueError(
            f"unknown op_name {op_name!r}; legal: "
            f"{sorted(set(_TRANS_OP_IDS) | {'exp_i'})}"
        )
    # Complex inputs always fall back to numpy (libm scalar path
    # doesn't handle complex elementwise — would need C complex
    # ops, out of scope for the v1 broadening).
    if np.iscomplexobj(arr):
        if op_name == "exp":
            return np.exp(arr).astype(np.complex128)
        if op_name == "cos":
            return np.cos(arr).astype(np.complex128)
        if op_name == "sin":
            return np.sin(arr).astype(np.complex128)
        return np.log(arr).astype(np.complex128)
    real_arr = np.ascontiguousarray(arr, dtype=np.float64).reshape(-1)
    n = int(real_arr.size)
    if n == 0:
        return np.zeros(np.shape(arr), dtype=np.float64)
    op_id = _TRANS_OP_IDS[op_name]
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = np.zeros(n, dtype=np.float64)
        rc = _native.LIB.srmech_elementwise_transcendental(
            ctypes.c_uint32(n),
            real_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            ctypes.c_int(op_id),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_OK:
            return out.reshape(np.shape(arr))
        if rc == _native.SRMECH_ERR_BAD_INPUT and op_name == "log":
            raise ValueError("log requires all arr[i] > 0")
    if op_name == "exp":
        return np.exp(real_arr).reshape(np.shape(arr))
    if op_name == "cos":
        return np.cos(real_arr).reshape(np.shape(arr))
    if op_name == "sin":
        return np.sin(real_arr).reshape(np.shape(arr))
    # log: defensive precondition check (parity with C native path).
    # numpy 2.x changed behaviour: np.log(0) returns -inf with a
    # RuntimeWarning rather than raising. Enforce the same domain
    # contract as the C path (srmech_elementwise_transcendental
    # returns SRMECH_ERR_BAD_INPUT for non-positive inputs).
    if not np.all(real_arr > 0.0):
        raise ValueError("log requires all arr[i] > 0")
    return np.log(real_arr).reshape(np.shape(arr))


# Registry of available Class L op names for the composition engine.
# Order is documentary; consumers iterate by name not position.
LAPLACIAN_OPS: Tuple[str, ...] = (
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "jacobi_eigvals",
    "hermitian_eigendecompose",
    "symmetric_eigendecompose",
    "dense_matvec_complex",
    "elementwise_multiply_complex",
    "elementwise_transcendental",
)
