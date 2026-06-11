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
- :func:`dense_matvec_complex` — general complex ``M·v``.
- :func:`dense_dot_complex` — complex bilinear inner product ``Σ aᵢbᵢ``.
- :func:`dense_matmul_real` / :func:`dense_matvec_real` / :func:`dense_dot_real`
  — float64 peers riding the complex kernel (drop the zero imaginary part).
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
degree / row-scaling buffers, embedded-safe). When ``HAS_NATIVE`` and
``n ≤ 256`` the dense build + ``jacobi_eigvals`` dispatch to the C
symbol **with or without numpy** — the numpy-absent path marshals a flat
ctypes buffer straight from Python ``list``s (UPSTREAM §38; ``jacobi``
~49× faster than the pure-Python cascade). For ``n > 256`` (or no native
lib) srmech's own pure-Python Class-L cascades run. The one numpy-only
exception is the eigen**vector** decomposition (``hermitian_`` /
``symmetric_eigendecompose``): it stays the LAPACK ``eigh`` path by design —
eigenvector sign / degenerate-subspace rotation is non-unique, so
element-wise C/Python parity is not meaningful (correctness is pinned by
eigenvalues + reconstruction + orthonormality). Cascade-composition
use-cases typically stay well under the ``n ≤ 256`` bound.
"""

from __future__ import annotations

import ctypes
from array import array  # §564: numpy-free 2-D Mat carrier buffer (interleaved-complex)
from fractions import Fraction  # §26: exact-rational interior solve (Class-N), no float
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from srmech.amsc.rational import sqrt as _rsqrt  # §22: scalar root via Class-N, not libm
from srmech.amsc.rational import hypot as _rhypot  # Class-N |z| magnitude, not libm
from srmech.amsc.rational import exp as _rexp  # Class-N exp cascade, not libm
from srmech.amsc.rational import cos as _rcos  # Class-N cos cascade, not libm
from srmech.amsc.rational import sin as _rsin  # Class-N sin cascade, not libm
from srmech.amsc.rational import log as _rlog  # Class-N log cascade, not libm
from srmech.amsc.rational import atan2 as _ratan2  # Class-N atan2 cascade, not libm
from srmech.amsc.rational import complex_exp as _rcomplex_exp  # Class-N e^z, not libm

try:  # UPSTREAM §22: the real-symmetric Class-L core is numpy-absent-safe.
    import numpy as np
except ImportError:  # pragma: no cover - exercised in the numpy-absent path only
    # The real-symmetric build → eigvals chain (dense_adjacency / dense_laplacian
    # / normalized_laplacian / jacobi_eigvals) has a pure-Python fallback that
    # runs without numpy/LAPACK (it returns list[list[float]] / list[float]).
    # The complex-Hermitian / signed / magnetic ops are scientific tier (§22) and
    # raise a clear ImportError (via _require_np at the _complex_to_interleaved /
    # _normalize_edges_weights chokepoints) when called with numpy absent; the
    # remaining numpy-tier ops (symmetric_eigendecompose / fiedler_vector /
    # elementwise_transcendental) require numpy and fail at their first numpy use.
    np = None  # type: ignore[assignment]

from . import _native

__all__ = [
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "jacobi_eigvals",
    "spectral_block_dispatch",
    "dense_solve",
    "schur_complement",
    "dirichlet_to_neumann",
    "hermitian_eigendecompose",
    "symmetric_eigendecompose",
    "dense_matvec_complex",
    "dense_matmul_complex",
    "mat_matmul",
    "mat_solve",
    "mat_hermitian_eigendecompose",
    "mat_lstsq",
    "dense_dot_complex",
    "dense_matmul_real",
    "dense_matvec_real",
    "dense_dot_real",
    "dense_norm",
    "dense_outer_complex",
    "dense_outer_real",
    "elementwise_multiply_complex",
    "elementwise_transcendental",
    "elementwise_hypot",
    "elementwise_sqrt",
    "LAPLACIAN_OPS",
    "MAX_NATIVE_NODES",
    "three_fold_eigvec_groups",
]

MAX_NATIVE_NODES: int = 256


def three_fold_eigvec_groups(L: "np.ndarray") -> dict:
    """Harmonic-3 three-fold spectral reading of a real-symmetric Laplacian
    (F150): partition the ``n`` eigenvectors (ascending eigenvalue) into three
    contiguous LOW / MID / HIGH bands. Class L is harmonic-3 (chiral rotation /
    3-cycle) per F150 §6.1 — the order-3 reading of the Class-L spectrum. When
    ``n`` is not divisible by 3 the remainder rows go to the later bands so
    ``|low| <= |mid| <= |high|``. Returns ``{"low", "mid", "high"}`` each an
    ``(n, k)`` float64 array of the eigenvector COLUMNS in that band; the
    chirality-aware companion to :func:`symmetric_eigendecompose`.
    """
    _eigvals, V = symmetric_eigendecompose(L)
    n = int(V.shape[1]) if V.ndim == 2 else 0
    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_three_fold_bands")
        and n <= 0xFFFF_FFFF
    ):
        lo = ctypes.c_uint32(0)
        mid = ctypes.c_uint32(0)
        hi = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_three_fold_bands(
            ctypes.c_uint32(n),
            ctypes.byref(lo),
            ctypes.byref(mid),
            ctypes.byref(hi),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_three_fold_bands returned non-OK status {rc}"
            )
        n_low, n_mid, n_high = lo.value, mid.value, hi.value
    else:
        base = n // 3
        rem = n - 3 * base
        n_low = base
        n_mid = base + (1 if rem >= 2 else 0)
        n_high = n - n_low - n_mid
    assert n_low + n_mid + n_high == n
    return {
        "low": V[:, :n_low],
        "mid": V[:, n_low:n_low + n_mid],
        "high": V[:, n_low + n_mid:],
    }


def _normalize_edges_weights(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # The numpy edge/weight arrays feed the native-C builders + the scientific
    # signed/magnetic Laplacians (§22). The numpy-FREE real builds use the
    # pure-Python _validate_edges_weights_py path and never reach here.
    _require_np("a numpy-tier graph-Laplacian build")
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


def _build_matrix_native_listmarshal(fn_name, n, edge_list, w_list):
    """numpy-FREE native graph build (UPSTREAM §38): marshal Python lists into
    ctypes arrays (edge endpoints uint32, weights double) + reshape the flat
    output to ``list[list[float]]`` — no numpy. Returns the matrix, or ``None``
    on a non-OK status (caller then uses the pure-Python builder). Same C symbol
    the numpy path calls; reachable on the numpy-absent install."""
    n_edges = len(edge_list)
    out = (ctypes.c_double * (n * n))()
    null_u = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32))
    null_d = ctypes.cast(None, ctypes.POINTER(ctypes.c_double))
    if n_edges:
        eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in edge_list))
        ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in edge_list))
        ws = (ctypes.c_double * n_edges)(*(float(w) for w in w_list))
    else:
        eu = ev = null_u
        ws = null_d
    rc = getattr(_native.LIB, fn_name)(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, ws, out
    )
    if rc != _native.SRMECH_OK:
        return None
    return [[out[r * n + c] for c in range(n)] for r in range(n)]


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


# ── UPSTREAM §22: numpy-absent-safe real-symmetric Class-L core ────────
# When numpy is unavailable the build → eigvals chain runs in pure Python
# (``list[list[float]]`` matrices, ``list[float]`` eigenvalues). The native C
# path marshals its buffers via numpy, so numpy-absent ⇒ pure-Python (the
# stdlib-array native marshalling is a tracked later voxel). The complex-
# Hermitian / vectorised-transcendental ops stay numpy (scientific tier) and
# raise a clear ImportError via ``_require_np`` when called with numpy absent.

def _require_np(op_name: str) -> None:
    if np is None:  # pragma: no cover - exercised only in the numpy-absent path
        raise ImportError(
            f"srmech.amsc.laplacian.{op_name} is a scientific-tier op "
            "(complex-Hermitian / vectorised linear algebra) and requires "
            "numpy (UPSTREAM §22: the heavy linear algebra keeps numpy). The "
            "real-symmetric core — dense_adjacency / dense_laplacian / "
            "normalized_laplacian / jacobi_eigvals — runs without numpy."
        )


def _validate_edges_weights_py(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]],
) -> Tuple[List[Tuple[int, int]], List[float]]:
    """Pure-Python edge/weight validation mirroring _normalize_edges_weights."""
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"n must be non-negative int; got {n!r}")
    if n > 0xFFFF_FFFF:
        raise ValueError(f"n exceeds uint32 range; got {n}")
    edge_list = [tuple(e) for e in edges]
    for i, (uu, vv) in enumerate(edge_list):
        if not (0 <= uu < n and 0 <= vv < n):
            raise ValueError(f"edge {i} = ({uu}, {vv}) outside node range [0, {n})")
    if weights is None:
        w_list = [1.0] * len(edge_list)
    else:
        w_list = [float(w) for w in weights]
        if len(w_list) != len(edge_list):
            raise ValueError(
                f"weights length {len(w_list)} != n_edges {len(edge_list)}"
            )
    return edge_list, w_list


def _dense_adjacency_py(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]],
) -> List[List[float]]:
    edge_list, w_list = _validate_edges_weights_py(n, edges, weights)
    A = [[0.0] * n for _ in range(n)]
    for (u, v), w in zip(edge_list, w_list):
        # Self-loops (u == v) hit the same cell twice → 2*w on the diagonal
        # (matches the C path / the numpy fallback).
        A[u][v] += w
        A[v][u] += w
    return A


def _dense_laplacian_py(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]],
) -> List[List[float]]:
    A = _dense_adjacency_py(n, edges, weights)
    L = [[0.0] * n for _ in range(n)]
    for r in range(n):
        deg = 0.0
        for c in range(n):
            if c == r:
                continue
            deg += A[r][c]
            L[r][c] = -A[r][c]
        L[r][r] = deg
    return L


def _normalized_laplacian_py(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]],
) -> List[List[float]]:
    A = _dense_adjacency_py(n, edges, weights)
    deg = [sum(A[r][c] for c in range(n) if c != r) for r in range(n)]
    d_inv_sqrt = [(1.0 / _rsqrt(d)) if d > 0 else 0.0 for d in deg]
    L = [[0.0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if r == c:
                L[r][r] = 1.0 if deg[r] > 0 else 0.0
            else:
                L[r][c] = -A[r][c] * d_inv_sqrt[r] * d_inv_sqrt[c]
    return L


def _jacobi_eigvals_py(
    matrix: Sequence[Sequence[float]],
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
) -> List[float]:
    """Pure-Python cyclic Jacobi eigenvalues of a real symmetric matrix.

    The numpy-free fallback for :func:`jacobi_eigvals` (UPSTREAM §22): the
    classical cyclic Jacobi rotation — the similarity transform ``A ← JᵀAJ``
    that zeroes each off-diagonal in turn; the converged diagonal IS the
    spectrum. Returns the sorted (ascending) eigenvalues as a ``list[float]``.
    Matches the native-C / ``numpy.linalg.eigvalsh`` path to Jacobi round-off.
    No LAPACK, no numpy. No ``abs()``: the off-diagonal magnitude is read as a
    sum of squares (inherently non-negative) and the rotation tangent handles
    its sign explicitly via the ``tau >= 0`` branch (Class-K sign-handling, not
    an ALU ``abs()``).
    """
    rows = [list(row) for row in matrix]
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(
                f"matrix must be square 2-D; got a {n}-row matrix with a "
                f"width-{len(r)} row"
            )
    if n == 0:
        return []
    a = [[float(rows[i][j]) for j in range(n)] for i in range(n)]
    if n == 1:
        return [a[0][0]]
    for _sweep in range(max_sweeps):
        off = _rsqrt(
            sum(a[p][q] * a[p][q] for p in range(n) for q in range(p + 1, n))
        )
        if off <= tolerance:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                apq = a[p][q]
                if apq == 0.0:
                    continue
                tau = (a[q][q] - a[p][p]) / (2.0 * apq)
                if tau >= 0.0:
                    t = 1.0 / (tau + _rsqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + _rsqrt(1.0 + tau * tau))
                c = 1.0 / _rsqrt(1.0 + t * t)
                s = t * c
                # A ← Jᵀ A J  (Givens rotation in the (p, q) plane):
                # pass 1 — columns p, q  (B = A J)
                for k in range(n):
                    akp = a[k][p]
                    akq = a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                # pass 2 — rows p, q  (A' = Jᵀ B)
                for k in range(n):
                    apk = a[p][k]
                    aqk = a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
    return sorted(a[i][i] for i in range(n))


def _jacobi_eig_py(
    matrix: Sequence[Sequence[float]],
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
) -> Tuple[List[float], List[List[float]]]:
    """Pure-Python cyclic Jacobi eigenVALUES **and** eigenVECTORS of a real
    symmetric matrix — the eigenvector-accumulating sibling of
    :func:`_jacobi_eigvals_py`, the numpy-free fallback the Hermitian ``Mat``
    bridge (:func:`mat_hermitian_eigendecompose`) leans on.

    Returns ``(eigvals, V)`` with ``eigvals`` ascending and ``V`` the matching
    orthogonal eigenvector matrix (``V[i][j]`` = i-th component of the j-th
    eigenvector; columns are eigenvectors), so ``A = V·diag(eigvals)·Vᵀ`` to
    Jacobi round-off. Same engine as :func:`_jacobi_eigvals_py` (the similarity
    transform ``A ← JᵀAJ``) plus the standard eigenvector accumulation
    ``V ← V·J`` — only columns ``p, q`` of ``V`` change per rotation. No LAPACK,
    no numpy, no ``abs()`` (off-diagonal magnitude is a sum of squares; the
    rotation tangent's sign is the explicit ``tau >= 0`` Class-K branch).

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §8.5.3 (cyclic-Jacobi eigenvector accumulation).
    """
    rows = [list(r) for r in matrix]
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(
                f"matrix must be square 2-D; got a {n}-row matrix with a "
                f"width-{len(r)} row"
            )
    if n == 0:
        return [], []
    a = [[float(rows[i][j]) for j in range(n)] for i in range(n)]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    if n == 1:
        return [a[0][0]], [[1.0]]
    for _sweep in range(max_sweeps):
        off = _rsqrt(
            sum(a[p][q] * a[p][q] for p in range(n) for q in range(p + 1, n))
        )
        if off <= tolerance:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                apq = a[p][q]
                if apq == 0.0:
                    continue
                tau = (a[q][q] - a[p][p]) / (2.0 * apq)
                if tau >= 0.0:
                    t = 1.0 / (tau + _rsqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + _rsqrt(1.0 + tau * tau))
                c = 1.0 / _rsqrt(1.0 + t * t)
                s = t * c
                # A ← Jᵀ A J  (Givens rotation in the (p, q) plane)
                for k in range(n):
                    akp = a[k][p]
                    akq = a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk = a[p][k]
                    aqk = a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                # V ← V J  (eigenvector accumulation; only columns p, q change)
                for k in range(n):
                    vkp = v[k][p]
                    vkq = v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq
    # Sort eigenpairs ascending by eigenvalue, permuting V columns to match.
    eig = [a[i][i] for i in range(n)]
    order = sorted(range(n), key=lambda j: eig[j])
    eigvals = [eig[j] for j in order]
    V = [[v[i][order[j]] for j in range(n)] for i in range(n)]
    return eigvals, V


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
    if np is not None and _can_dispatch_native(n):
        edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
        return _build_matrix_native(
            "srmech_graph_dense_adjacency", n, edges_u, edges_v, ws
        )
    if np is None and _can_dispatch_native(n):  # UPSTREAM §38: numpy-free native
        el, wl = _validate_edges_weights_py(n, edges, weights)
        m = _build_matrix_native_listmarshal("srmech_graph_dense_adjacency", n, el, wl)
        if m is not None:
            return m
    # srmech's own pure-Python builder (UPSTREAM §22 + the cascade-over-numpy
    # discipline): numpy-absent → list[list[float]]; numpy-present-no-native →
    # the SAME srmech build wrapped as an ndarray for API stability (the wrap
    # is container layout, NOT numpy math).
    A = _dense_adjacency_py(n, edges, weights)
    return np.asarray(A, dtype=np.float64) if np is not None else A


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
    if np is not None and _can_dispatch_native(n):
        edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
        return _build_matrix_native(
            "srmech_graph_dense_laplacian", n, edges_u, edges_v, ws
        )
    if np is None and _can_dispatch_native(n):  # UPSTREAM §38: numpy-free native
        el, wl = _validate_edges_weights_py(n, edges, weights)
        m = _build_matrix_native_listmarshal("srmech_graph_dense_laplacian", n, el, wl)
        if m is not None:
            return m
    L = _dense_laplacian_py(n, edges, weights)
    return np.asarray(L, dtype=np.float64) if np is not None else L


def normalized_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> np.ndarray:
    """Symmetric normalised Laplacian ``L_sym = I − D^(−1/2) A D^(−1/2)``.

    Isolated vertices (degree 0) have diagonal entry 0 by convention
    (not 1; the ``I`` term only applies where ``D > 0``).
    """
    if np is not None and _can_dispatch_native(n):
        edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
        return _build_matrix_native(
            "srmech_graph_normalized_laplacian", n, edges_u, edges_v, ws
        )
    if np is None and _can_dispatch_native(n):  # UPSTREAM §38: numpy-free native
        el, wl = _validate_edges_weights_py(n, edges, weights)
        m = _build_matrix_native_listmarshal(
            "srmech_graph_normalized_laplacian", n, el, wl
        )
        if m is not None:
            return m
    L = _normalized_laplacian_py(n, edges, weights)
    return np.asarray(L, dtype=np.float64) if np is not None else L


def _jacobi_eigvals_native_listmarshal(rows, n, max_sweeps, tolerance):
    """numpy-FREE native dispatch for :func:`jacobi_eigvals` (UPSTREAM §38).

    Marshals a ``list[list[float]]`` straight into a flat ``(c_double * n*n)``
    ctypes buffer (row-major) and calls the bound ``srmech_jacobi_eigvals`` C
    symbol — no numpy needed. The fresh ctypes buffer is the in-place work
    array, so the caller's ``rows`` is untouched. Returns the sorted ascending
    eigenvalues as ``list[float]``, or ``None`` on any non-OK status (caller
    then uses the pure-Python Jacobi cascade). ~49× faster than the cascade at
    n=256 (1.4 s vs 68 s; F708) while staying numpy-free."""
    work = (ctypes.c_double * (n * n))(
        *(float(rows[i][j]) for i in range(n) for j in range(n))
    )
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_jacobi_eigvals(
        ctypes.c_uint32(n),
        work,
        ctypes.c_uint32(int(max_sweeps)),
        ctypes.c_double(float(tolerance)),
        out,
    )
    if rc != _native.SRMECH_OK:
        return None  # OVERFLOW / non-convergence → caller's pure-Python cascade
    return sorted(out)


def jacobi_eigvals(
    matrix: np.ndarray,
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
) -> np.ndarray:
    """Symmetric Jacobi eigendecomposition.

    Returns the sorted (ascending) eigenvalues of a real symmetric matrix.
    The C path is bounded by ``MAX_NATIVE_NODES = 256`` and uses an in-place
    algebraic Jacobi rotation (pi-free). For larger ``n`` (or when
    ``HAS_NATIVE`` is False) the fallback is **srmech's own pure-Python Jacobi
    cascade** (:func:`_jacobi_eigvals_py`) — NOT ``numpy.linalg.eigvalsh``:
    when srmech can do the math with its own cascade, it does (and so the
    Class-L spectrum runs without LAPACK/numpy, UPSTREAM §22). With numpy
    absent the input is a ``list[list[float]]`` and the return is a
    ``list[float]``; with numpy present the return is an ``ndarray``.

    numpy-absent dispatch (UPSTREAM §38 / F708): the bound ``srmech_jacobi_eigvals``
    C symbol IS reachable without numpy — when ``HAS_NATIVE`` and ``n ≤
    MAX_NATIVE_NODES`` the numpy-free path marshals the ``list[list[float]]``
    into a flat ctypes ``double`` buffer and calls it (~49× faster than the
    pure-Python cascade at n=256), falling back to the cascade only when there
    is no native lib, ``n`` is too large, or the C status is non-OK.

    ``matrix`` is **not** modified by the wrapper — a copy is made before the
    in-place C path runs.
    """
    if np is None:
        # numpy absent. Try the bound native symbol via numpy-free list
        # marshalling (UPSTREAM §38); else srmech's pure-Python Jacobi cascade.
        rows = [[float(x) for x in row] for row in matrix]
        n = len(rows)
        if n > 0 and all(len(r) == n for r in rows) and _can_dispatch_native(n):
            ev = _jacobi_eigvals_native_listmarshal(rows, n, max_sweeps, tolerance)
            if ev is not None:
                return ev
        return _jacobi_eigvals_py(matrix, max_sweeps, tolerance)
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
            # srmech's OWN Jacobi cascade — never numpy's LAPACK eigvalsh.
            return np.asarray(
                _jacobi_eigvals_py(M.tolist(), max_sweeps, tolerance),
                dtype=np.float64,
            )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_jacobi_eigvals returned non-OK status {rc}")
        return np.sort(out)
    # No native: srmech's OWN Jacobi cascade — never numpy's LAPACK eigvalsh.
    return np.asarray(
        _jacobi_eigvals_py(M.tolist(), max_sweeps, tolerance),
        dtype=np.float64,
    )


# =====================================================================
# UPSTREAM §26 (#897) — the Class-L Schur complement / Dirichlet-to-Neumann
# (DtN) map: the operator|operand FUSION op (F412 / F417 / F419)
# =====================================================================
#
# Every other Class-L op in the corpus PROJECTS — it maps a spatial graph
# (operand, 2:4:8) to a cyclic spectrum (operator, 1:3:7) and DROPS the
# spatial structure (F417, the one-way seam). The Schur complement KEEPS
# BOTH: the spatial boundary AND its operator spectrum. That is the
# fusion, not the projection.
#
# Holographic reading (F412): boundary = base, bulk = total, fiber =
# emergent radial dim. Integrating the bulk out leaves a boundary effective
# operator whose SIZE is |∂| (the boundary), not n (the bulk). That
# dimensional reduction n → |∂| IS the area law.


def _as_rows(L) -> List[list]:
    """Coerce a matrix (ndarray / list-of-lists / sequence-of-sequences) to a
    square list-of-lists, validating squareness. No numpy required."""
    if np is not None and isinstance(L, np.ndarray):
        if L.ndim != 2 or L.shape[0] != L.shape[1]:
            raise ValueError(f"L must be square 2-D; got shape {L.shape}")
        return L.tolist()
    rows = [list(r) for r in L]
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(f"L must be square n×n; got a row of length {len(r)} for n={n}")
    return rows


def _validate_boundary(n: int, boundary_idx: Sequence[int]) -> Tuple[List[int], List[int]]:
    """Split {0..n-1} into the boundary list ∂ (sorted, deduped, validated) and
    the interior list i (the complement, sorted)."""
    b = sorted(set(int(k) for k in boundary_idx))
    if len(b) != len(list(boundary_idx)):
        raise ValueError("boundary_idx must not contain duplicate indices")
    if not b:
        raise ValueError("boundary_idx must be non-empty (1 ≤ |∂| ≤ n)")
    if b[0] < 0 or b[-1] >= n:
        raise ValueError(f"boundary_idx entries must be in [0, {n}); got {b}")
    bset = set(b)
    i = [k for k in range(n) if k not in bset]
    return b, i


def _solve_exact(A: List[list], B: List[list]) -> List[List[Fraction]]:
    """Exact-rational solve of ``A · X = B`` over the rationals — Gauss–Jordan
    elimination in :class:`fractions.Fraction` (the Class-N exact-rational
    primitive; division here is exact, never a float reciprocal — F392). ``A``
    is m×m, ``B`` is m×w, the returned ``X`` is m×w. No numpy, no ``abs()``:
    the pivot is the FIRST nonzero at/below the diagonal (exact arithmetic
    needs no magnitude-based partial pivoting for stability — only a nonzero
    pivot). A wholly-zero pivot column ⇒ a singular interior block."""
    m = len(A)
    w = len(B[0]) if B else 0
    # Augmented [A | B] in exact rationals.
    M = [[Fraction(A[r][c]) for c in range(m)] + [Fraction(B[r][c]) for c in range(w)]
         for r in range(m)]
    for col in range(m):
        pivot = None
        for r in range(col, m):
            if M[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            raise ZeroDivisionError(
                "singular interior block L_ii: an interior component is "
                "disconnected from the boundary (no harmonic extension exists)."
            )
        if pivot != col:
            M[col], M[pivot] = M[pivot], M[col]
        inv_piv = M[col][col]
        M[col] = [x / inv_piv for x in M[col]]  # exact rational division (Class-N)
        for r in range(m):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [M[r][cc] - f * M[col][cc] for cc in range(m + w)]
    return [[M[r][m + cc] for cc in range(w)] for r in range(m)]


def _as_solve_rhs(B, n: int):
    """Normalise a dense-solve right-hand side to ``(is_vector, rows)`` where
    ``rows`` is an ``n``-row list-of-lists. A 1-D ``B`` (length ``n``) is a
    single column (returned ``is_vector=True``); a 2-D ``B`` is used as-is.
    Values are preserved verbatim — NO float coercion — so the exact-rational
    path keeps ints / :class:`~fractions.Fraction` inputs exact."""
    if np is not None and isinstance(B, np.ndarray):
        if B.ndim == 1:
            if B.shape[0] != n:
                raise ValueError(f"B vector length {B.shape[0]} != A dimension {n}")
            return True, [[v] for v in B]
        rows = [list(row) for row in B]
    else:
        seq = list(B)
        is_1d = bool(seq) and not isinstance(seq[0], (list, tuple)) and not (
            np is not None and isinstance(seq[0], np.ndarray)
        )
        if is_1d:
            if len(seq) != n:
                raise ValueError(f"B vector length {len(seq)} != A dimension {n}")
            return True, [[v] for v in seq]
        rows = [list(row) for row in seq]
    if len(rows) != n:
        raise ValueError(f"B must have {n} rows to match A ({n}×{n}); got {len(rows)}")
    return False, rows


def dense_solve(A, B, *, exact: bool = False):
    """Class-L dense linear solve ``A · X = B``
    (v0.7.1rc3; [#897](https://github.com/lemonforest/mlehaptics/issues/897) §26).

    The reusable solve the Schur-complement / Dirichlet-to-Neumann float path
    composes over — its interior solve ``L_ii⁻¹ · L_i∂`` IS an ``A · X = B``.
    Promoted to its own exported Class-L primitive: a dense solve is a
    fundamental, reusable matrix op, and the solve (not the downstream matmul)
    is where the cost lives.

    ``A`` is ``n×n``; ``B`` is ``n×w`` (a matrix → ``X`` is ``n×w``) or length
    ``n`` (a vector → ``X`` is length ``n``).

    With **numpy absent** (or ``exact=True``) the solve is **exact-rational**
    Gauss–Jordan in :class:`fractions.Fraction` (the Class-N core — division is
    exact, never a float reciprocal, F392) and ``X`` is ``list[list[Fraction]]``
    (or ``list[Fraction]`` for a vector RHS). With numpy present (and
    ``exact=False``) the float realization rides the ``[scientific]`` tier: the
    native C peer ``srmech_dense_solve_f64`` (Gauss–Jordan with partial
    pivoting — the Class-K magnitude pivot, a sign branch not ``abs()``;
    bounded ``n, w ≤ 256``) when available, else ``numpy.linalg.solve``.

    Raises
    ------
    ValueError
        Non-square ``A``; ``B`` row-count ≠ ``n``.
    ZeroDivisionError
        Singular ``A`` (exact path — no unique solution).
    """
    A_rows = _as_rows(A)
    n = len(A_rows)
    if n == 0:
        raise ValueError("A must be a non-empty square matrix")
    for r in A_rows:
        if len(r) != n:
            raise ValueError(
                f"A must be square; got an {n}-row matrix with a width-{len(r)} row"
            )
    is_vec, B_rows = _as_solve_rhs(B, n)
    w = len(B_rows[0]) if B_rows and B_rows[0] else 0

    if exact or np is None:
        X = _solve_exact(A_rows, B_rows)  # exact Fraction Gauss–Jordan (Class-N)
        return [row[0] for row in X] if is_vec else X

    # Float realization — native dense_solve C peer, else numpy.linalg.solve.
    A_arr = np.ascontiguousarray(A_rows, dtype=np.float64)
    B_arr = np.ascontiguousarray(B_rows, dtype=np.float64)
    if (
        _can_dispatch_native(n)
        and w <= MAX_NATIVE_NODES
        and hasattr(_native.LIB, "srmech_dense_solve_f64")
    ):
        out = np.zeros((n, w), dtype=np.float64)
        rc = _native.LIB.srmech_dense_solve_f64(
            ctypes.c_uint32(n),
            ctypes.c_uint32(w),
            A_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            B_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_OK:
            return out[:, 0] if is_vec else out
        if rc not in (_native.SRMECH_ERR_OVERFLOW, _native.SRMECH_ERR_BAD_INPUT):
            raise RuntimeError(f"srmech_dense_solve_f64 returned non-OK status {rc}")
        # OVERFLOW (over the native bound) or BAD_INPUT (singular) → numpy.
    X = np.linalg.solve(A_arr, B_arr)
    return X[:, 0] if is_vec else X


def _dense_solve_complex(A, B):
    """Complex dense solve ``A · X = B`` via the real 2n×2n block embedding of
    the (real, native) :func:`dense_solve`.

    A complex linear system ``(Aᵣ + i Aᵢ)(u + i v) = (bᵣ + i bᵢ)`` is, splitting
    real and imaginary parts, the **real** ``2n×2n`` system ::

        ⎡ Aᵣ  −Aᵢ ⎤ ⎡ u ⎤   ⎡ bᵣ ⎤
        ⎣ Aᵢ   Aᵣ ⎦ ⎣ v ⎦ = ⎣ bᵢ ⎦

    so ``X = u + i v``. The embedding is exact (pure ``concatenate`` / slice —
    NumPy a carrier only) and rides the shipped native real ``dense_solve``;
    for a well-conditioned ``A`` (e.g. an HPD Gram matrix ``V·Vᴴ``) it is
    value-faithful to NumPy's complex solve / ``inv`` to ~1e-9. The complex
    inverse is just ``_dense_solve_complex(A, eye(n))`` (``A · X = I``).

    Private (underscore) — an internal Class-L helper, not a public catalog op.
    Requires numpy (the ``[scientific]`` tier); complex linear algebra has no
    numpy-absent exact-rational path here.
    """
    A = np.asarray(A, dtype=np.complex128)
    B = np.asarray(B, dtype=np.complex128)
    n = A.shape[0]
    is_vec = (B.ndim == 1)
    B_mat = B.reshape(n, 1) if is_vec else B
    A_re, A_im = A.real, A.imag
    block = np.concatenate(
        [
            np.concatenate([A_re, -A_im], axis=1),
            np.concatenate([A_im, A_re], axis=1),
        ],
        axis=0,
    )                                                            # (2n, 2n) real
    rhs = np.concatenate([B_mat.real, B_mat.imag], axis=0)       # (2n, w) real
    sol = np.asarray(dense_solve(block, rhs))                    # [u; v]
    X = sol[:n, :] + 1j * sol[n:, :]
    return X[:, 0] if is_vec else X


def schur_complement(L, boundary_idx: Sequence[int], *, exact: bool = False):
    """Class-L Schur complement / discrete Dirichlet-to-Neumann (DtN) map
    (UPSTREAM §26; [#897](https://github.com/lemonforest/mlehaptics/issues/897)).

    Integrate the interior (bulk) out of ``L`` and keep the boundary effective
    operator::

        S = L_∂∂ − L_∂i · L_ii⁻¹ · L_i∂

    where ``∂ = boundary_idx`` and ``i`` is the interior complement. ``S`` is
    the discrete **Dirichlet-to-Neumann map**: given boundary values ``x_∂``,
    the unique harmonic extension into the interior solves
    ``L_ii x_i = −L_i∂ x_∂`` and ``S x_∂`` is the boundary normal-derivative of
    that extension. **Boundary data ⟹ the whole interior field.**

    The operator|operand FUSION op (F412 / F417 / F419): every other Class-L
    cascade PROJECTS (spatial operand → cyclic operator, F417's one-way seam),
    dropping the spatial structure; ``schur_complement`` keeps BOTH the spatial
    boundary and its spectrum. Holographic reading (F412): the bulk is
    integrated out, the effective theory lives on the boundary — ``S`` has
    ``|∂|`` modes (the boundary), not ``n`` (the bulk). That reduction
    ``n → |∂|`` is the area law.

    Cascade-honesty: the interior solve ``L_ii⁻¹`` is an inverse = Class C
    (conjugate) → Class K (``1/‖·‖²``); no ``abs()``. With **numpy absent** (or
    ``exact=True``) the solve is **exact-rational** Gauss–Jordan elimination in
    :class:`fractions.Fraction` (the Class-N rational core — division is exact,
    never a float reciprocal) and ``S`` is returned as ``list[list[Fraction]]``.
    With numpy present (and ``exact=False``) the float realization rides the
    ``[scientific]`` tier (``numpy.linalg.solve``) and ``S`` is an
    ``ndarray``. Canonical SSoT: Zhang, *The Schur Complement and Its
    Applications* (2005) §0; the DtN map is textbook (Golub & Van Loan §3.2).

    Parameters
    ----------
    L : matrix, ``n×n``
        ``ndarray`` (numpy present) or ``list[list]`` — a symmetric
        positive-semidefinite operator (a graph Laplacian from
        :func:`dense_laplacian`, or any SPD matrix).
    boundary_idx : sequence[int]
        The boundary node indices ``∂``; ``1 ≤ |∂| ≤ n``, no duplicates.
    exact : bool, default ``False``
        Force the exact-rational :class:`~fractions.Fraction` solve even when
        numpy is present (returns ``list[list[Fraction]]``).

    Returns
    -------
    S : ``|∂|×|∂|`` boundary effective operator
        ``ndarray`` (float path) or ``list[list[Fraction]]`` (exact path).

    Raises
    ------
    ValueError
        Non-square ``L``; empty / out-of-range / duplicate ``boundary_idx``.
    ZeroDivisionError
        Singular interior block ``L_ii`` — an interior component disconnected
        from the boundary, so no harmonic extension exists.

    Notes
    -----
    For a pure graph Laplacian the DtN map (a Kron reduction) inherits the
    all-ones null vector, so ``rank(S) = |∂| − c`` where ``c`` is the number of
    connected components of the boundary-reduced graph (``= |∂| − 1`` for a
    connected graph). The *area law* is the dimensional reduction ``n → |∂|``
    (the effective operator lives on the boundary), not a full-rank claim.
    """
    rows = _as_rows(L)
    n = len(rows)
    if n == 0:
        raise ValueError("L must be a non-empty square matrix")
    b, i = _validate_boundary(n, boundary_idx)

    # Block extraction (pure container slicing — numpy-free).
    def _block(rs, cs):
        return [[rows[p][q] for q in cs] for p in rs]

    L_pp = _block(b, b)  # L_∂∂

    if not i:
        # No interior to integrate out — the boundary IS the whole space.
        if exact or np is None:
            return [[Fraction(v) for v in r] for r in L_pp]
        return np.asarray(L_pp, dtype=np.float64)

    L_pi = _block(b, i)  # L_∂i
    L_ip = _block(i, b)  # L_i∂
    L_ii = _block(i, i)  # L_ii

    if exact or np is None:
        # Interior solve L_ii · X = L_i∂ (X is |i|×|∂|) via the Class-L
        # dense_solve primitive — exact-rational Gauss–Jordan (Class-N).
        X = dense_solve(L_ii, L_ip, exact=True)
        # S = L_∂∂ − L_∂i · X  (all exact Fraction).
        S = [
            [
                Fraction(L_pp[a][c])
                - sum(Fraction(L_pi[a][k]) * X[k][c] for k in range(len(i)))
                for c in range(len(b))
            ]
            for a in range(len(b))
        ]
        return S

    # Float realization — the [scientific] tier. The expensive interior solve
    # rides the native dense_solve C peer (numpy fallback inside dense_solve);
    # the cheap boundary GEMM + subtract stay numpy.
    X = dense_solve(L_ii, L_ip)
    S = np.asarray(L_pp, dtype=np.float64) - np.asarray(L_pi, dtype=np.float64) @ X
    return S


def dirichlet_to_neumann(L, boundary_idx: Sequence[int], *, exact: bool = False):
    """Alias for :func:`schur_complement` — the discrete Dirichlet-to-Neumann
    (DtN) map ``S = L_∂∂ − L_∂i · L_ii⁻¹ · L_i∂`` (UPSTREAM §26; #897). Given
    boundary values, ``S`` returns the boundary normal-derivative of their
    harmonic extension into the interior."""
    return schur_complement(L, boundary_idx, exact=exact)


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
    _require_np("a complex-valued Class-L operation")  # scientific tier (§22)
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
    _require_np("hermitian_eigendecompose")  # complex scientific tier (§22)
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


def _canonicalize_eigenvector_signs(V):
    """Pin each real eigenvector column's sign (Class K) deterministically.

    An eigenvector is defined only up to a ``±`` sign (a ``Z₂`` gauge for a
    real-symmetric problem); LAPACK and the native Jacobi peer pick it
    arbitrarily — a *hidden, non-settable* convention. This flips each column so
    its largest-magnitude entry is positive: a deterministic, **settable**
    convention (the endianness precedent), reconstruction-invariant. The flip IS
    the Class-K sign boundary; the magnitude pivot is selected via ``col²`` so
    there is **no** ``abs()`` and **no** float square root. NumPy is a carrier
    only (``argmax`` + slice + negate) — no ``linalg``/``fft``/matmul/ufunc/
    float-power. (Within a degenerate eigenspace the larger ``U(k)`` basis
    freedom is solver-chosen and reconstruction-invariant; this pins only the
    per-column ``Z₂``.)
    """
    arr = np.asarray(V)
    if arr.ndim != 2 or arr.shape[1] == 0:
        return arr
    out = arr.copy()
    for j in range(arr.shape[1]):
        col = arr[:, j]
        k = int(np.argmax(col * col))     # largest-|·| entry via col² (no abs/sqrt)
        if col[k] < 0.0:                  # Class-K sign pin: pivot → positive
            out[:, j] = -col
    return out


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
        Symmetry is not enforced (caller's responsibility).

    Returns
    -------
    (eigvals, V)
        ``eigvals`` is a length-``n`` float64 array of real eigenvalues
        in ascending order. ``V`` is an ``(n, n)`` float64 orthogonal
        matrix whose columns are the corresponding eigenvectors.

    Class L. Canonical SSoT: Golub & Van Loan, *Matrix Computations*
    (4th ed., Johns Hopkins, 2013) §8.3 (symmetric eigenproblem).

    Computed by delegating to the **C-backed** :func:`hermitian_
    eigendecompose` (real-symmetric IS complex-Hermitian — native Jacobi
    peer when available; NumPy ``eigh`` only as that op's OWN shared
    fallback). The eigenvectors of a real-symmetric matrix are real (the
    Hermitian path returns them with imaginary part ~0), so we take
    ``.real`` and sign-canonicalise each column (Class-K,
    :func:`_canonicalize_eigenvector_signs`). Eigenvalues come out
    ascending. Correctness is pinned by eigenvalues + reconstruction +
    orthonormality (the eigenvector sign / degenerate-subspace basis is
    non-unique), not element-wise C/Python parity.
    """
    L_arr = np.ascontiguousarray(np.real(np.asarray(L)), dtype=np.float64)
    if L_arr.ndim != 2 or L_arr.shape[0] != L_arr.shape[1]:
        raise ValueError(f"L must be square 2-D; got shape {L_arr.shape}")
    n = L_arr.shape[0]
    if n == 0:
        return (np.zeros(0, dtype=np.float64),
                np.zeros((0, 0), dtype=np.float64))
    eigvals, V_complex = hermitian_eigendecompose(L_arr.astype(np.complex128))
    V = _canonicalize_eigenvector_signs(np.real(V_complex))
    return (np.ascontiguousarray(eigvals, dtype=np.float64),
            np.ascontiguousarray(V, dtype=np.float64))


def dense_matvec_complex(M: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Dense complex matrix-vector multiplication: ``M·v``.

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


def dense_matmul_complex(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Dense complex matrix-matrix multiplication ``A·B``.

    The srmech Class-L contraction the QM / ``matrix_cascades`` matmul math routes
    through, so numpy stays carriers-only (no ``np`` matmul engine). Native
    ``srmech_dense_matmul_complex`` when present (each dim ≤ 256); else composes
    the :func:`dense_matvec_complex` cascade column-by-column — the no-native
    fallback is itself a cascade, **never** numpy ``@``.

    Parameters
    ----------
    A
        ``(m, k)`` complex matrix.
    B
        ``(k, n)`` complex matrix.

    Returns
    -------
    out
        ``(m, n)`` complex128 array.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix multiplication).
    """
    A_arr = np.ascontiguousarray(A, dtype=np.complex128)
    B_arr = np.ascontiguousarray(B, dtype=np.complex128)
    if A_arr.ndim != 2 or B_arr.ndim != 2:
        raise ValueError(
            f"A and B must be 2-D; got ndim {A_arr.ndim} and {B_arr.ndim}"
        )
    m, k = A_arr.shape
    k2, n = B_arr.shape
    if k2 != k:
        raise ValueError(
            f"A shape {A_arr.shape} incompatible with B shape {B_arr.shape}"
        )
    if (_native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_dense_matmul_complex")
            and m <= MAX_NATIVE_NODES
            and k <= MAX_NATIVE_NODES
            and n <= MAX_NATIVE_NODES):
        A_il = _complex_to_interleaved(A_arr)
        B_il = _complex_to_interleaved(B_arr)
        out_il = np.zeros(2 * m * n, dtype=np.float64)
        rc = _native.LIB.srmech_dense_matmul_complex(
            ctypes.c_uint32(m),
            ctypes.c_uint32(k),
            ctypes.c_uint32(n),
            A_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            B_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            out_il.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        if rc == _native.SRMECH_OK:
            return _interleaved_to_complex(out_il, (m, n))
    # No-native / over-bound fallback: compose the matvec cascade per column of
    # B (a cascade, not numpy matmul — keeps numpy carriers-only here too).
    out = np.empty((m, n), dtype=np.complex128)
    for j in range(n):
        out[:, j] = dense_matvec_complex(A_arr, B_arr[:, j])
    return out


# =====================================================================
# §564 — the Mat↔native-dense-kernel bridge (carrier-removal foundation #2)
# =====================================================================
#
# The numpy-using dense_* kernels above marshal via numpy (`_complex_to_
# interleaved` = np.view) — they need numpy on the input/marshal path even on
# the native dispatch. The Mat carrier (rc69; flat array('d'), row-major,
# interleaved-(re,im) for complex = C99 double _Complex) IS already the exact
# layout the C symbols read, so it feeds them with ZERO numpy. mat_matmul is
# foundation #2 of the carrier-removal arc (#564): the numpy-free 2-D `@` the
# qm.* matmul callsites flip onto. mat_solve / mat_hermitian_eigendecompose are
# the follow-on rcs (each its own numpy-free fallback).


def _mat_to_interleaved_cbuf(m: "Mat", n_elems: int):
    """A ``(c_double * 2*n_elems)`` ctypes buffer of ``m``'s elements as
    interleaved ``(re, im)`` doubles — numpy-free.

    When ``m`` is complex its ``array('d')`` buffer IS already the interleaved
    ``(re, im)`` layout, so this is a **zero-copy** ``from_buffer`` view (the C
    kernel reads it ``const``). When ``m`` is real the buffer is one double per
    element, so a fresh interleaved buffer is filled ``(re, 0.0)`` once."""
    buf = m.buffer  # array('d')
    if m.is_complex:
        return (ctypes.c_double * (2 * n_elems)).from_buffer(buf)  # zero-copy
    cbuf = (ctypes.c_double * (2 * n_elems))()
    for idx in range(n_elems):
        cbuf[2 * idx] = buf[idx]  # imag slot stays 0.0
    return cbuf


def _mat_from_interleaved_cbuf(cbuf, n_rows: int, n_cols: int, *, want_complex: bool):
    """Wrap an interleaved ``(re, im)`` ctypes buffer back into a ``Mat``
    (numpy-free). ``want_complex`` keeps the interleaved layout; otherwise the
    real parts (every even slot) form a real ``Mat``."""
    from .mat import Mat  # numpy-free carrier; local import keeps load-order clean
    if want_complex:
        return Mat(array("d", cbuf), n_rows, n_cols, is_complex=True)
    n = n_rows * n_cols
    return Mat(array("d", (cbuf[2 * i] for i in range(n))), n_rows, n_cols)


def mat_matmul(a: "Mat", b: "Mat") -> "Mat":
    """Numpy-free dense matrix multiply ``A·B`` over the
    :class:`~srmech.amsc.mat.Mat` carrier — the 2-D ``@`` replacement for the
    numpy-CARRIER removal arc (#564, foundation #2).

    ``A`` ``(m, k)`` · ``B`` ``(k, n)`` → ``Mat`` ``(m, n)``. The ``Mat`` buffer
    is already flat row-major interleaved-complex (= C99 ``double _Complex``), so
    the native ``srmech_dense_matmul_complex`` reads/writes it with **NO numpy**:
    a complex operand feeds the kernel **zero-copy** (``from_buffer``), a real
    operand is interleaved ``(re, 0)`` once, and the output is a fresh
    ``array('d')`` wrapped back into a ``Mat`` (complex iff either input is). With
    no native lib — or any dim > ``MAX_NATIVE_NODES`` (256) — the fallback is a
    pure-Python triple loop over the ``Mat`` (a cascade, **never** numpy ``@``),
    so the op is unconditionally numpy-free.

    rc69 built ``Mat``; rc71 made signal_processing import-reachable numpy-free;
    this is the bridge the 2-D ``qm.*`` matmul callsites flip onto (rc73+) to
    compute numpy-free on the native path.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1 (textbook matrix multiplication).
    """
    from .mat import Mat
    assert isinstance(a, Mat) and isinstance(b, Mat), (
        "mat_matmul operands must be Mat (the numpy-free 2-D carrier)"
    )
    m, k = a.n_rows, a.n_cols
    k2, n = b.n_rows, b.n_cols
    if k2 != k:
        raise ValueError(f"mat_matmul: A {a.shape} incompatible with B {b.shape}")
    is_complex = a.is_complex or b.is_complex
    # Native zero-copy path (each dim ≤ 256, nonzero): Mat buffer → C kernel → Mat.
    if (m and k and n
            and _native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_dense_matmul_complex")
            and m <= MAX_NATIVE_NODES
            and k <= MAX_NATIVE_NODES
            and n <= MAX_NATIVE_NODES):
        a_il = _mat_to_interleaved_cbuf(a, m * k)
        b_il = _mat_to_interleaved_cbuf(b, k * n)
        out_il = (ctypes.c_double * (2 * m * n))()
        rc = _native.LIB.srmech_dense_matmul_complex(
            ctypes.c_uint32(m), ctypes.c_uint32(k), ctypes.c_uint32(n),
            a_il, b_il, out_il,
        )
        if rc == _native.SRMECH_OK:
            return _mat_from_interleaved_cbuf(out_il, m, n, want_complex=is_complex)
    # numpy-free pure-Python fallback (triple loop; never numpy @).
    out = array("d")
    if is_complex:
        for i in range(m):
            for j in range(n):
                s = 0j
                for t in range(k):
                    s += complex(a[i, t]) * complex(b[t, j])
                out.append(s.real)
                out.append(s.imag)
    else:
        for i in range(m):
            for j in range(n):
                s = 0.0
                for t in range(k):
                    s += float(a[i, t]) * float(b[t, j])
                out.append(s)
    return Mat(out, m, n, is_complex=is_complex)


def mat_solve(a: "Mat", b: "Mat") -> "Mat":
    """Numpy-free dense linear solve ``A·X = B`` over the
    :class:`~srmech.amsc.mat.Mat` carrier — bridge primitive #2 of the
    numpy-CARRIER removal arc (#564), the peer of :func:`mat_matmul`.

    ``A`` ``(n, n)`` real `Mat` · solves for ``X`` ``(n, w)`` given ``B``
    ``(n, w)`` real `Mat`. ``Mat.buffer`` is already the flat row-major float64
    the native ``srmech_dense_solve_f64`` reads, so both operands feed the kernel
    **zero-copy** (``from_buffer``) with **NO numpy** (the C side takes them
    ``const``, so the `Mat`\\ s are not mutated); the output is a fresh
    ``array('d')`` wrapped back into a `Mat`. With no native lib — or any dim >
    ``MAX_NATIVE_NODES`` (256), or the native path flagging singular — the
    fallback is srmech's own **exact-rational Gauss–Jordan**
    (:func:`_solve_exact`, Class-N ``Fraction`` division, numpy-free) coerced to
    float64, so the op is unconditionally numpy-free.

    ``srmech_dense_solve_f64`` is **real-f64 only**; a complex `Mat` (rc95)
    routes through :func:`_mat_solve_complex` — the real ``2n×2n`` block
    embedding ``[[Aᵣ,−Aᵢ],[Aᵢ,Aᵣ]]·[u;v]=[bᵣ;bᵢ]`` over this same native real
    solve (numpy-free), so ``mat_solve`` now handles complex too.

    Raises ``ValueError`` (non-square ``A`` / ``B`` row mismatch / empty ``A``),
    ``ZeroDivisionError`` (singular ``A``, exact-path signal).

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §3.4 (Gaussian elimination with partial pivoting).
    """
    from .mat import Mat
    assert isinstance(a, Mat) and isinstance(b, Mat), (
        "mat_solve operands must be Mat (the numpy-free 2-D carrier)"
    )
    if a.is_complex or b.is_complex:
        # Complex solve via the real 2n×2n block embedding (rc95), riding the
        # native real path below — numpy-free, value-faithful for well-
        # conditioned A. cf. the same embedding in _hermitian_eig_py.
        return _mat_solve_complex(a, b)
    n = a.n_rows
    if n == 0:
        raise ValueError("mat_solve: A must be a non-empty square matrix")
    if a.n_cols != n:
        raise ValueError(f"mat_solve: A must be square; got {a.shape}")
    if b.n_rows != n:
        raise ValueError(
            f"mat_solve: B row-count {b.n_rows} incompatible with A size {n}"
        )
    w = b.n_cols
    if w == 0:
        return Mat(array("d"), n, 0)  # n×0 solve → n×0 X (degenerate but valid)
    # Native zero-copy path (n, w ≤ 256): real Mat buffers → C kernel → Mat.
    if (_native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_dense_solve_f64")
            and n <= MAX_NATIVE_NODES
            and w <= MAX_NATIVE_NODES):
        a_buf = (ctypes.c_double * (n * n)).from_buffer(a.buffer)  # zero-copy (real)
        b_buf = (ctypes.c_double * (n * w)).from_buffer(b.buffer)  # zero-copy (real)
        out = (ctypes.c_double * (n * w))()
        rc = _native.LIB.srmech_dense_solve_f64(
            ctypes.c_uint32(n), ctypes.c_uint32(w), a_buf, b_buf, out,
        )
        if rc == _native.SRMECH_OK:
            return Mat(array("d", out), n, w)
        if rc not in (_native.SRMECH_ERR_OVERFLOW, _native.SRMECH_ERR_BAD_INPUT):
            raise RuntimeError(f"srmech_dense_solve_f64 returned non-OK status {rc}")
        # OVERFLOW (over the native bound) / BAD_INPUT (singular) → exact fallback.
    # numpy-free fallback: srmech's own exact-rational Gauss–Jordan (Class-N).
    X = _solve_exact(a.tolist(), b.tolist())  # list[list[Fraction]]; raises if singular
    return Mat.from_rows([[float(x) for x in row] for row in X])


def _mat_solve_complex(a: "Mat", b: "Mat") -> "Mat":
    """Numpy-free complex dense solve ``A·X = B`` (``A`` complex ``n×n``, ``B``
    complex ``n×w``) via the real ``2n×2n`` block embedding of the native real
    :func:`mat_solve` — the Mat-carrier peer of :func:`_dense_solve_complex`
    (rc95, carrier-removal #564).

    Splitting ``(Aᵣ + iAᵢ)(u + iv) = (bᵣ + ibᵢ)`` into real/imag parts gives the
    **real** ``2n×2n`` system ``[[Aᵣ,−Aᵢ],[Aᵢ,Aᵣ]]·[u;v] = [bᵣ;bᵢ]``, so
    ``X = u + iv``. The embedding is built from plain ``Mat`` indexing (no numpy)
    and rides the shipped native real :func:`mat_solve`; value-faithful to
    NumPy's complex solve to ~1e-9 for a well-conditioned ``A`` (the
    signal-subspace projections esprit/the matrix-heavy DSP ops feed it).
    """
    from .mat import Mat
    n = a.n_rows
    if n == 0:
        raise ValueError("mat_solve: A must be a non-empty square matrix")
    if a.n_cols != n:
        raise ValueError(f"mat_solve: A must be square; got {a.shape}")
    if b.n_rows != n:
        raise ValueError(
            f"mat_solve: B row-count {b.n_rows} incompatible with A size {n}"
        )
    w = b.n_cols
    if w == 0:
        return Mat(array("d"), n, 0, is_complex=True)  # n×0 → n×0 (degenerate)
    av = [[complex(a[i, j]) for j in range(n)] for i in range(n)]
    block_rows = (
        [[av[i][j].real for j in range(n)] + [-av[i][j].imag for j in range(n)]
         for i in range(n)]
        + [[av[i][j].imag for j in range(n)] + [av[i][j].real for j in range(n)]
           for i in range(n)]
    )                                                      # (2n, 2n) real
    block = Mat.from_rows(block_rows, is_complex=False)
    bv = [[complex(b[i, j]) for j in range(w)] for i in range(n)]
    rhs_rows = (
        [[bv[i][j].real for j in range(w)] for i in range(n)]
        + [[bv[i][j].imag for j in range(w)] for i in range(n)]
    )                                                      # (2n, w) real
    rhs = Mat.from_rows(rhs_rows, is_complex=False)
    sol = mat_solve(block, rhs)                            # [u; v] (native, real)
    out_rows = [
        [complex(sol[i, j], sol[i + n, j]) for j in range(w)] for i in range(n)
    ]
    return Mat.from_rows(out_rows, is_complex=True)


def mat_lstsq(a: "Mat", b: "Mat") -> "Mat":
    """Numpy-free least-squares solution of ``A·X ≈ B`` (minimising
    ``‖A·X − B‖``) over the :class:`~srmech.amsc.mat.Mat` carrier — the
    Mat-return peer of ``matrix_cascades.lstsq`` (rc96, carrier-removal #564).

    Overdetermined / square ``A`` ``(m, n)`` with ``m ≥ n`` (full column rank).
    Built as the **normal equations** ``X = (Aᴴ·A)⁻¹·Aᴴ·B``, composed entirely
    from the native ``mat_*`` trio: ``mat_solve(mat_matmul(Aᴴ, A),
    mat_matmul(Aᴴ, B))`` with ``Aᴴ = A.conj().T`` — fully numpy-free for real
    **and** complex ``A`` (rc95 made :func:`mat_solve` complex-capable via the
    real 2n×2n block embedding). Value-faithful to NumPy's ``lstsq(A, B)[0]``
    to ~1e-9 for a well-conditioned ``A`` (the normal equations square the
    condition number — fine for the orthonormal signal-subspace projections the
    DSP ops feed it; an ill-conditioned ``A`` wants the QR path of
    ``matrix_cascades.lstsq`` instead). The result is complex iff ``A`` is.

    Raises ``ValueError`` (underdetermined ``m < n`` / ``A``-``B`` row mismatch),
    ``ZeroDivisionError`` (rank-deficient ``A``, surfaced by the solve).

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §5.3 (normal-equations least squares).
    """
    from .mat import Mat
    assert isinstance(a, Mat) and isinstance(b, Mat), (
        "mat_lstsq operands must be Mat (the numpy-free 2-D carrier)"
    )
    m, n = a.n_rows, a.n_cols
    if m < n:
        raise ValueError(
            f"mat_lstsq supplies the overdetermined/square (m>=n) normal-"
            f"equations path; got A {a.shape} (underdetermined)"
        )
    if b.n_rows != m:
        raise ValueError(
            f"mat_lstsq: B row-count {b.n_rows} incompatible with A rows {m}"
        )
    ah = a.conj().T                       # Aᴴ (n, m) — Class-K conjugate ∘ transpose
    aha = mat_matmul(ah, a)               # (n, n) Hermitian, PD if A full column rank
    ahb = mat_matmul(ah, b)               # (n, w)
    return mat_solve(aha, ahb)            # numpy-free (complex via the rc95 embedding)


def _hermitian_eig_py(h: "Mat") -> Tuple["Mat", "Mat"]:
    """Numpy-free Hermitian eigendecomposition fallback for
    :func:`mat_hermitian_eigendecompose`.

    A **real-symmetric** input is diagonalised directly by
    :func:`_jacobi_eig_py`. A **complex-Hermitian** input ``H = A + iB`` is
    diagonalised through its real ``2n×2n`` symmetric embedding
    ``M = [[A, -B], [B, A]]`` (whose spectrum is ``H``'s, each eigenvalue
    doubled); the complex eigenvectors are reconstructed ``vⱼ = topⱼ + i·botⱼ``
    from one embedding eigenvector per equal-eigenvalue pair (``|topⱼ + i·botⱼ|``
    is already 1 — it equals the embedding vector's ℝ²ⁿ norm), then
    same-eigenvalue modified Gram–Schmidt re-orthonormalised (a no-op for a
    non-degenerate spectrum; it pins a unitary basis inside a degenerate
    eigenspace). Returns ``(eigvals (n, 1) real Mat, eigvecs (n, n) complex
    Mat)``.
    """
    from .mat import Mat
    n = h.n_rows
    if not h.is_complex:
        evals, V = _jacobi_eig_py(h.tolist())
        ev_mat = Mat(array("d", (float(e) for e in evals)), n, 1)
        vc = array("d")  # real eigenvectors → complex Mat (imag 0), native-shape
        for i in range(n):
            for j in range(n):
                vc.append(float(V[i][j]))
                vc.append(0.0)
        return ev_mat, Mat(vc, n, n, is_complex=True)
    # Complex Hermitian: H = A + iB → real symmetric embedding M = [[A,-B],[B,A]].
    A = [[h[i, j].real for j in range(n)] for i in range(n)]
    B = [[h[i, j].imag for j in range(n)] for i in range(n)]
    m = 2 * n
    M = [[0.0] * m for _ in range(m)]
    for i in range(n):
        for j in range(n):
            M[i][j] = A[i][j]
            M[i][j + n] = -B[i][j]
            M[i + n][j] = B[i][j]
            M[i + n][j + n] = A[i][j]
    evals2, V2 = _jacobi_eig_py(M)
    # 2n eigenvalues come in equal pairs (ascending) → take every other for n;
    # reconstruct vⱼ = top + i·bot, then same-eigenvalue Gram–Schmidt → unitary.
    cols: List[Tuple[float, List[complex]]] = []
    for k in range(n):
        col = 2 * k
        ev = evals2[col]
        w = [complex(V2[i][col], V2[i + n][col]) for i in range(n)]
        for ev_prev, w_prev in cols:
            if _rsqrt((ev - ev_prev) * (ev - ev_prev)) <= 1e-9:  # same eigenvalue
                proj = sum(w_prev[i].conjugate() * w[i] for i in range(n))
                w = [w[i] - proj * w_prev[i] for i in range(n)]
        norm2 = sum(x.real * x.real + x.imag * x.imag for x in w)
        inv = 1.0 / _rsqrt(norm2)
        w = [x * inv for x in w]
        cols.append((ev, w))
    ev_mat = Mat(array("d", (float(ev) for ev, _ in cols)), n, 1)
    vc = array("d")
    for i in range(n):        # row i
        for k in range(n):    # column k = eigenvector k
            z = cols[k][1][i]
            vc.append(z.real)
            vc.append(z.imag)
    return ev_mat, Mat(vc, n, n, is_complex=True)


def mat_hermitian_eigendecompose(h: "Mat") -> Tuple["Mat", "Mat"]:
    """Numpy-free Hermitian eigendecomposition ``H = V·diag(λ)·Vᴴ`` over the
    :class:`~srmech.amsc.mat.Mat` carrier — bridge primitive **#3** (the last) of
    the numpy-CARRIER removal arc (#564), completing the family with
    :func:`mat_matmul` (#1) and :func:`mat_solve` (#2).

    ``H`` is an ``(n, n)`` Hermitian `Mat` (real-symmetric or complex-Hermitian).
    Returns ``(eigvals, eigvecs)``:

    * ``eigvals`` — ``(n, 1)`` **real** `Mat`, the eigenvalues ascending;
    * ``eigvecs`` — ``(n, n)`` **complex** `Mat`, the unitary matrix whose columns
      are the eigenvectors (**always** complex, mirroring
      :func:`hermitian_eigendecompose`; a caller that knows the input is
      real-symmetric takes ``.real``, exactly as :func:`symmetric_eigendecompose`
      does).

    ``Mat.buffer`` is already the flat interleaved-``(re, im)`` row-major layout
    the native ``srmech_hermitian_eigendecompose`` reads, so a complex `Mat` feeds
    the kernel **zero-copy** (``from_buffer``) and a real `Mat` is interleaved
    ``(re, 0)`` once — **NO numpy** on the native path. With no native lib — or
    ``n`` > ``MAX_NATIVE_NODES`` (256), or a native convergence miss — the fallback
    is srmech's own pure-Python **cyclic Jacobi** (:func:`_hermitian_eig_py`,
    real-symmetric directly / complex-Hermitian via the real ``2n×2n`` embedding),
    so the op is unconditionally numpy-free.

    Correctness is pinned by eigenvalues + reconstruction (``H ≈ V·diag(λ)·Vᴴ``)
    + unitarity (``Vᴴ·V ≈ I``), NOT element-wise parity — an eigenvector is fixed
    only up to a unit-modulus phase, and a degenerate eigenspace's basis is
    solver-chosen.

    Once :func:`mat_matmul` + :func:`mat_solve` + this op exist, a ``qm.*`` module
    can hold its working matrices in `Mat` and flip numpy-free — the first
    ``CEIL_NUMPY_CARRIER`` decrement.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §8.5 (Hermitian eigenproblem via unitary Jacobi rotations).
    """
    from .mat import Mat
    assert isinstance(h, Mat), (
        "mat_hermitian_eigendecompose operand must be Mat (numpy-free 2-D carrier)"
    )
    n = h.n_rows
    if h.n_cols != n:
        raise ValueError(
            f"mat_hermitian_eigendecompose: H must be square; got {h.shape}"
        )
    if n == 0:
        return Mat(array("d"), 0, 1), Mat(array("d"), 0, 0, is_complex=True)
    # Native zero-copy path (n ≤ 256): Mat interleaved buffer → C kernel → Mats.
    if (_native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_hermitian_eigendecompose")
            and n <= MAX_NATIVE_NODES):
        h_il = _mat_to_interleaved_cbuf(h, n * n)
        eigvals_buf = (ctypes.c_double * n)()
        v_il = (ctypes.c_double * (2 * n * n))()
        rc = _native.LIB.srmech_hermitian_eigendecompose(
            ctypes.c_uint32(n), h_il, eigvals_buf, v_il,
        )
        if rc == _native.SRMECH_OK:
            eigvals = Mat(array("d", eigvals_buf), n, 1)
            eigvecs = _mat_from_interleaved_cbuf(v_il, n, n, want_complex=True)
            return eigvals, eigvecs
        # Non-OK (convergence miss / over-bound) → numpy-free Jacobi fallback.
    return _hermitian_eig_py(h)


def dense_dot_complex(a: np.ndarray, b: np.ndarray) -> complex:
    """Dense complex bilinear inner product ``a · b = Σ aᵢ bᵢ``.

    The 1-D contraction the QM η-sandwiches and the ``matrix_cascades``
    back-solves route through, so numpy stays carriers-only (no numpy
    contraction engine). This is the **plain bilinear** form ``Σ aᵢ bᵢ``
    (matching numpy ``a·b`` on two 1-D arrays — NOT the Hermitian ``vdot``,
    which conjugates its first argument). Callers that want the Hermitian inner
    product pass ``a.conj()`` explicitly (the ``.conj()`` is a carrier
    transform, not math-engine), exactly as the ``a.conj()·eta·b`` sites
    already spell it.

    Composes the :func:`elementwise_multiply_complex` cascade (native-dispatched
    when present) with a reduction sum — **never** a numpy contraction operator.
    The reduction sits on the carrier⇄math boundary (the ledger's DEFERRED
    category), so this helper adds nothing to the tight engine ceilings while
    removing a contraction-engine callsite.

    Parameters
    ----------
    a, b
        Length-``n`` complex vectors (same length).

    Returns
    -------
    out
        Python ``complex`` scalar ``Σ aᵢ bᵢ``.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1 (textbook inner product).
    """
    a_arr = np.ascontiguousarray(a, dtype=np.complex128).reshape(-1)
    b_arr = np.ascontiguousarray(b, dtype=np.complex128).reshape(-1)
    if a_arr.shape[0] != b_arr.shape[0]:
        raise ValueError(
            f"dense_dot_complex: a length {a_arr.shape[0]} != b length "
            f"{b_arr.shape[0]}"
        )
    if a_arr.shape[0] == 0:
        return complex(0.0)
    # Class-M elementwise bind (native dispatch) + reduction (carrier boundary).
    products = elementwise_multiply_complex(a_arr, b_arr)
    return complex(np.sum(products))


# ---------------------------------------------------------------------------
# Real-typed peers. The complex kernel IS the contraction engine; a real
# matmul/matvec/dot is the complex one on imag-free input with the (exactly
# zero) imaginary part dropped — so these ride the native complex kernel and
# return float64. They exist so the real-typed scientific-tier sites (Spin(8)
# / g₂ / triality octonion-rep algebra, octonion-DFT regular representation,
# Minkowski real 4-momenta, real DSP) can leave numpy `@`/`.dot` for a cascade
# without a dtype change. Each is `composition_of_c` (no own C symbol; the math
# rides the c_dispatched complex kernel; standalone-ready).
# ---------------------------------------------------------------------------
def dense_matmul_real(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Dense real matrix-matrix multiplication ``A·B`` → float64.

    Routes the real contraction through :func:`dense_matmul_complex` (the
    native complex kernel on imag-free input) and drops the exactly-zero
    imaginary part. numpy stays carriers-only — no numpy matmul engine.

    Parameters
    ----------
    A
        ``(m, k)`` real matrix.
    B
        ``(k, n)`` real matrix.

    Returns
    -------
    out
        ``(m, n)`` float64 array.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix multiplication).
    """
    out = dense_matmul_complex(
        np.ascontiguousarray(A, dtype=np.float64),
        np.ascontiguousarray(B, dtype=np.float64),
    )
    return np.ascontiguousarray(out.real, dtype=np.float64)


def dense_matvec_real(M: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Dense real matrix-vector multiplication ``M·v`` → float64.

    Real peer of :func:`dense_matvec_complex` (rides the native complex kernel
    on imag-free input, drops the zero imaginary part). numpy carriers-only.

    Parameters
    ----------
    M
        ``(rows, cols)`` real matrix.
    v
        Length-``cols`` real vector.

    Returns
    -------
    out
        Length-``rows`` float64 array.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix-vector product).
    """
    out = dense_matvec_complex(
        np.ascontiguousarray(M, dtype=np.float64),
        np.ascontiguousarray(v, dtype=np.float64),
    )
    return np.ascontiguousarray(out.real, dtype=np.float64)


def dense_dot_real(a: np.ndarray, b: np.ndarray) -> float:
    """Dense real inner product ``Σ aᵢ bᵢ`` → Python ``float``.

    Real peer of :func:`dense_dot_complex` (rides the native elementwise-bind
    cascade on imag-free input + reduction). numpy carriers-only.

    Parameters
    ----------
    a, b
        Length-``n`` real vectors (same length).

    Returns
    -------
    out
        Python ``float`` ``Σ aᵢ bᵢ``.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook inner product).
    """
    return float(
        dense_dot_complex(
            np.ascontiguousarray(a, dtype=np.float64),
            np.ascontiguousarray(b, dtype=np.float64),
        ).real
    )


def dense_norm(x: np.ndarray) -> float:
    """Euclidean (2-norm) / Frobenius norm ``‖x‖ = √(Σ|xᵢ|²)`` → ``float``.

    The default vector 2-norm and matrix Frobenius norm the QM self-consistency
    residuals + signal-processing taper normalisations route through, so numpy
    stays carriers-only (no numpy norm engine). It is **Class N (the
    :func:`srmech.amsc.rational.sqrt` root) ∘ Class M (the
    :func:`dense_dot_complex` self-bind ``Σ|xᵢ|²``)** — the array is flattened
    (a carrier reshape), the sum-of-squares rides the native elementwise-bind
    cascade, and the root is the libm-free Class-N sqrt. Value-faithful to the
    NumPy 2-norm / Frobenius norm to round-off (~1 ULP) for every shape and
    dtype; for ``ord=None`` it is exactly that flat √(Σ|·|²).

    Parameters
    ----------
    x
        Real or complex array of any shape (flattened to a vector).

    Returns
    -------
    out
        Python ``float`` ``√(Σ|xᵢ|²)`` (``0.0`` for an empty array).

    Canonical SSoT: Golub & Van Loan §2.3 (vector / Frobenius norms).
    """
    arr = np.ascontiguousarray(x).reshape(-1)
    if arr.shape[0] == 0:
        return 0.0
    if np.iscomplexobj(arr):
        sq = float(dense_dot_complex(np.conj(arr), arr).real)   # Σ conj(x)·x = Σ|x|²
    else:
        sq = dense_dot_real(arr, arr)                           # Σ x·x = Σ|x|²
    return _rsqrt(sq) if sq > 0.0 else 0.0


def dense_outer_complex(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Dense complex outer product ``a ⊗ b`` → ``out[i, j] = aᵢ bⱼ``.

    The rank-1 contraction the QM density-matrix / momentum-tensor sites route
    through, so numpy stays carriers-only (no numpy ``outer`` engine). An outer
    product IS a ``k = 1`` matrix product — ``a`` as a column, ``b`` as a row —
    so this is exactly :func:`dense_matmul_complex` on the reshaped pair: it
    rides the native ``srmech_dense_matmul_complex`` kernel directly, with no
    inner summation (each entry is a single complex multiply), so the result is
    **bit-identical** to numpy ``outer``.

    Like numpy ``outer`` this does NOT conjugate ``b`` — the plain bilinear
    ``aᵢ bⱼ``. Callers wanting ``|ψ⟩⟨ψ|`` pass ``b = ψ.conj()`` explicitly (the
    ``.conj()`` is a carrier transform, not a math-engine op), exactly as the
    ``outer(psi, psi.conj())`` sites already spell it.

    Parameters
    ----------
    a
        Length-``m`` complex vector (the column).
    b
        Length-``n`` complex vector (the row).

    Returns
    -------
    out
        ``(m, n)`` complex128 array ``aᵢ bⱼ``.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1 (rank-1 update / outer product).
    """
    a_col = np.ascontiguousarray(a, dtype=np.complex128).reshape(-1, 1)
    b_row = np.ascontiguousarray(b, dtype=np.complex128).reshape(1, -1)
    if a_col.shape[0] == 0 or b_row.shape[1] == 0:
        return np.zeros((a_col.shape[0], b_row.shape[1]), dtype=np.complex128)
    return dense_matmul_complex(a_col, b_row)


def dense_outer_real(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Dense real outer product ``a ⊗ b`` → ``out[i, j] = aᵢ bⱼ`` (float64).

    Real peer of :func:`dense_outer_complex` (rides the native complex kernel on
    imag-free input, drops the exactly-zero imaginary part). numpy carriers-only;
    bit-identical to numpy ``outer`` on real input.

    Parameters
    ----------
    a
        Length-``m`` real vector.
    b
        Length-``n`` real vector.

    Returns
    -------
    out
        ``(m, n)`` float64 array ``aᵢ bⱼ``.

    Canonical SSoT: Golub & Van Loan §1.1 (rank-1 outer product).
    """
    return dense_outer_complex(
        np.ascontiguousarray(a, dtype=np.float64),
        np.ascontiguousarray(b, dtype=np.float64),
    ).real


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


def _real_transcendental_loop(flat_real: np.ndarray, op_name: str) -> np.ndarray:
    """numpy-free real ``exp``/``cos``/``sin``/``log`` via the Class-N scalar cascades.

    The pure-Python / no-native fallback for :func:`elementwise_transcendental`
    (the native path runs ``srmech_elementwise_transcendental``). numpy carries
    the flat float64 buffer only; every element runs the libm-free
    :mod:`srmech.amsc.rational` cascade. ``flat_real`` is a 1-D float64 array.
    """
    if op_name == "log" and flat_real.shape[0] and float(flat_real.min()) <= 0.0:
        raise ValueError("log requires all arr[i] > 0")
    fn = {"exp": _rexp, "cos": _rcos, "sin": _rsin, "log": _rlog}[op_name]
    out = np.zeros(flat_real.shape[0], dtype=np.float64)
    for i in range(flat_real.shape[0]):
        out[i] = fn(float(flat_real[i]))
    return out


def _complex_transcendental_loop(arr: np.ndarray, op_name: str) -> np.ndarray:
    """numpy-free complex ``exp``/``cos``/``sin``/``log`` via Class-N real cascades.

    The complex-input path for :func:`elementwise_transcendental`, numpy-free
    (numpy carries the complex128 buffer only). Each entry ``z = a + bi`` runs:

    * ``exp(z)`` = :func:`rational.complex_exp` (``e^a (cos b + i sin b)``);
    * ``cos(z)`` = ``cos a · cosh b − i · sin a · sinh b``;
    * ``sin(z)`` = ``sin a · cosh b + i · cos a · sinh b``  (``cosh``/``sinh``
      built from ``rational.exp``: ``cosh b = (e^b + e^{-b})/2`` etc.);
    * ``log(z)`` = ``log|z| + i·arg z`` = ``rational.log(rational.hypot(a, b))
      + i·rational.atan2(b, a)`` (principal branch; ``z ≠ 0``).
    """
    flat = np.ascontiguousarray(arr, dtype=np.complex128).reshape(-1)
    out = np.zeros(flat.shape[0], dtype=np.complex128)
    for i in range(flat.shape[0]):
        z = complex(flat[i])
        a, b = z.real, z.imag
        if op_name == "exp":
            out[i] = _rcomplex_exp(z)
        elif op_name == "log":
            mag = _rhypot(a, b)
            if mag <= 0.0:
                raise ValueError("log requires arr[i] != 0")
            out[i] = complex(_rlog(mag), _ratan2(b, a))
        else:
            eb = _rexp(b)
            enb = _rexp(-b)
            cosh_b = (eb + enb) / 2.0
            sinh_b = (eb - enb) / 2.0
            ca, sa = _rcos(a), _rsin(a)
            if op_name == "cos":
                out[i] = complex(ca * cosh_b, -(sa * sinh_b))
            else:  # sin
                out[i] = complex(sa * cosh_b, ca * sinh_b)
    return out.reshape(np.shape(arr))


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
            # numpy-free Class-N cos/sin cascade (the no-native / Pyodide path)
            cos_out = _real_transcendental_loop(real_arr, "cos")
            sin_out = _real_transcendental_loop(real_arr, "sin")
        result = (cos_out + 1j * sin_out).astype(np.complex128)
        return result.reshape(np.shape(arr))
    if op_name not in _TRANS_OP_IDS:
        raise ValueError(
            f"unknown op_name {op_name!r}; legal: "
            f"{sorted(set(_TRANS_OP_IDS) | {'exp_i'})}"
        )
    # Complex inputs run the numpy-free per-element Class-N complex cascades
    # (exp via rational.complex_exp; cos/sin via cosh/sinh from rational.exp;
    # log via rational.log(hypot) + i·rational.atan2). numpy carries the
    # complex128 buffer only — no numpy transcendental engine.
    if np.iscomplexobj(arr):
        return _complex_transcendental_loop(arr, op_name)
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
    # numpy-free Class-N scalar cascade (the no-native / Pyodide path). The
    # log domain check (all arr[i] > 0, parity with the C BAD_INPUT contract)
    # lives inside _real_transcendental_loop.
    return _real_transcendental_loop(real_arr, op_name).reshape(np.shape(arr))


def elementwise_hypot(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Array Euclidean magnitude ``√(aᵢ² + bᵢ²)`` via the Class-N hypot cascade.

    The numpy-free magnitude op the DSP modules' ``|z| = √(re² + im²)`` sites
    route through, so numpy stays carriers-only (no numpy ``hypot`` engine). Each
    element runs :func:`srmech.amsc.rational.hypot` (Class M sum-of-squares ∘
    Class N∘K :func:`~srmech.amsc.rational.sqrt`; native ``srmech_rational_sqrt``
    -dispatched) — the math is the libm-free cascade, not numpy's. The numpy-only
    work is array packing (``asarray`` / ``reshape`` / the output buffer).

    Round-off-faithful to numpy's hypot (the rational sqrt is floor-projected vs
    IEEE round-to-nearest — a ≤1-ULP shift, accepted per the cascades-replace-
    numpy-math discipline; bit-exact whenever ``aᵢ² + bᵢ²`` is a perfect square).

    Parameters
    ----------
    a, b
        Same-shape real arrays (typically ``z.real`` / ``z.imag``).

    Returns
    -------
    out
        Float64 array of ``√(aᵢ² + bᵢ²)``, same shape as ``a``.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1 (Euclidean length).
    """
    a_arr = np.ascontiguousarray(a, dtype=np.float64)
    b_arr = np.ascontiguousarray(b, dtype=np.float64)
    if a_arr.shape != b_arr.shape:
        raise ValueError(
            f"elementwise_hypot: shape mismatch {a_arr.shape} vs {b_arr.shape}"
        )
    flat_a = a_arr.reshape(-1)
    flat_b = b_arr.reshape(-1)
    out = np.zeros(flat_a.shape[0], dtype=np.float64)
    for i in range(flat_a.shape[0]):
        out[i] = _rhypot(float(flat_a[i]), float(flat_b[i]))
    return out.reshape(a_arr.shape)


def elementwise_sqrt(arr: np.ndarray) -> np.ndarray:
    """Array element-wise ``√arrᵢ`` via the Class-N rational sqrt cascade.

    The numpy-free square-root op for non-negative real arrays — the companion
    to :func:`elementwise_hypot`, so numpy stays carriers-only (no numpy ``sqrt``
    ufunc). Each element runs :func:`srmech.amsc.rational.sqrt` (Class-N∘K
    integer-``isqrt`` cascade; native ``srmech_rational_sqrt``-dispatched) — the
    math is the libm-free cascade, not numpy's. The numpy-only work is array
    packing (``asarray`` / ``reshape`` / the output buffer).

    Round-off-faithful to numpy's sqrt (the rational sqrt is floor-projected vs
    IEEE round-to-nearest — a ≤1-ULP shift, accepted per the cascades-replace-
    numpy-math discipline; bit-exact whenever ``arrᵢ`` is a perfect square).

    Parameters
    ----------
    arr
        Real array with all entries ``>= 0`` (square-root domain).

    Returns
    -------
    out
        Float64 array of ``√arrᵢ``, same shape as ``arr``.

    Raises
    ------
    ValueError
        If any ``arrᵢ < 0`` (matches the C path's domain contract; numpy's
        ``sqrt`` would silently emit ``nan`` with a RuntimeWarning).

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1.
    """
    a_arr = np.ascontiguousarray(arr, dtype=np.float64)
    flat = a_arr.reshape(-1)
    if flat.shape[0] and float(flat.min()) < 0.0:
        raise ValueError("elementwise_sqrt requires all arr[i] >= 0")
    out = np.zeros(flat.shape[0], dtype=np.float64)
    for i in range(flat.shape[0]):
        out[i] = _rsqrt(float(flat[i]))
    return out.reshape(a_arr.shape)


# =====================================================================
# Directed / signed Laplacian (#797 op (b); the F240/F241 directed-
# coupling gap + the dissolved Class-O signed-metric absorbed into L)
# =====================================================================
#
# The undirected combinatorial Laplacian (``dense_laplacian``) is the
# F348 navigation control (Fiedler shuffle-fragile r=0.214). Two
# directed/signed generalisations live here:
#
#   * ``signed_laplacian`` — real-symmetric; off-diagonal weights may be
#     negative (the **signed-metric**, the operation Spike #24 located as
#     "Class O" and which was DISSOLVED into Class L per
#     ``[[feedback_no_privileged_primitive_classes]]``). PSD signed
#     Laplacian L = D̄ − A with D̄_ii = Σ_j |A_ij| (Kunegis et al. 2010).
#   * ``magnetic_laplacian`` — complex **Hermitian**; encodes edge
#     *direction* as a phase, so a directed graph stays Hermitian and the
#     existing :func:`hermitian_eigendecompose` (C-backed) diagonalises
#     it. The complex eigenpair IS the directed-navigation signature.
#
# Both feed the existing C-backed eigensolvers; the heavy work (the
# eigendecomposition) is native today. The standalone-C *builder* peers
# (``srmech_graph_signed_laplacian`` / ``..._magnetic_laplacian``) are
# the tracked next voxel, mirroring the loop_bind Python-first→C-peer
# cadence (rc1 → rc7/rc20/rc21). Class-K discipline: the |A_ij| magnitude
# in the signed degree is the Class-K magnitude of the signed-metric, not
# an ALU ``abs()`` in a cascade
# (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).


def _directed_adjacency(
    n: int,
    edges_u: np.ndarray,
    edges_v: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    """Build the dense ``n×n`` **directed** adjacency ``W[u, v] += w``.

    Unlike :func:`_fallback_dense_adjacency` this does NOT mirror the
    transpose — direction is preserved (``W`` is generally asymmetric).
    """
    W = np.zeros((n, n), dtype=np.float64)
    for u, v, w in zip(edges_u, edges_v, weights):
        W[int(u), int(v)] += float(w)
    return W


def signed_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> np.ndarray:
    """Signed graph Laplacian ``L = D̄ − A`` (real-symmetric, PSD).

    The off-diagonal weights may be **negative** — this is the
    signed-metric leg (the dissolved "Class O", now a Class-L
    sub-operation). The signed degree ``D̄_ii = Σ_j |A_ij|`` uses the
    **Class-K magnitude** of each coupling (not an ALU ``abs()`` in a
    cascade — this is the library-internal signed-metric per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``), which
    makes ``L`` positive-semidefinite even with negative (frustrated)
    edges (Kunegis, J. et al. (2010) "Spectral Analysis of Signed
    Graphs", SDM 2010).

    Returns an ``n×n`` real-symmetric matrix; pair with
    :func:`symmetric_eigendecompose` or :func:`fiedler_vector` for the
    signed navigation embedding.
    """
    edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
    A = _fallback_dense_adjacency(n, edges_u, edges_v, ws)  # symmetric, signed
    diag_idx = np.arange(n)
    A_off = A.copy()
    A_off[diag_idx, diag_idx] = 0.0
    # Class-K magnitude of the signed couplings → the signed degree. Expressed
    # as an EXPLICIT sign-branch (pin-slot + re-orientation), NOT an ALU abs():
    # |A_ij| = A_ij where A_ij >= 0 else -A_ij. (Honours "abs() is never fine".)
    A_mag = np.where(A_off >= 0.0, A_off, -A_off)
    deg = A_mag.sum(axis=1)
    L = -A_off
    L[diag_idx, diag_idx] = deg
    return L


def magnetic_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    q: float = 0.25,
) -> np.ndarray:
    """Magnetic (Hermitian) Laplacian of a **directed** graph.

    Direction is encoded as a complex phase so the result stays
    **Hermitian** and the existing :func:`hermitian_eigendecompose`
    (C-backed) diagonalises it — the complex eigenpair is the
    directed-navigation signature (#797 op (b)). For directed edges
    ``u → v`` with magnitude ``w``:

    * symmetrised magnitude ``A_s = (W + Wᵀ) / 2``;
    * net flow ``Θ = W − Wᵀ`` (antisymmetric);
    * ``H = A_s ⊙ exp(i · 2π · q · Θ)`` (Hermitian: ``A_s`` symmetric,
      the phase conjugate-antisymmetric);
    * ``L⁽q⁾ = diag(Σ_j A_s,ij) − H``.

    ``q`` is the charge / flux parameter in turns per unit net flow:
    ``q = 0`` collapses to the real symmetrised Laplacian (the F348
    undirected control); ``q = 1/4`` is a quarter-turn per unit
    imbalance. The construction is the magnetic / Hermitian Laplacian
    for directed graphs (Lieb & Loss, fluxes on graphs); a precise
    attested citation belongs in the research notebook under the MPM
    discipline.

    Returns an ``n×n`` complex128 Hermitian matrix.
    """
    if not isinstance(q, (int, float)):
        raise TypeError(f"q must be a real number; got {type(q).__name__}")
    edges_u, edges_v, ws = _normalize_edges_weights(n, edges, weights)
    W = _directed_adjacency(n, edges_u, edges_v, ws)
    A_s = 0.5 * (W + W.T)
    theta = W - W.T
    phase = elementwise_transcendental((2.0 * np.pi * float(q)) * theta, "exp_i")
    H = A_s * phase
    diag_idx = np.arange(n)
    H[diag_idx, diag_idx] = 0.0  # no self-phase; degree carries the diagonal
    deg = A_s.sum(axis=1)
    L = -H
    L[diag_idx, diag_idx] = deg.astype(np.complex128)
    return L


def fiedler_vector(matrix: np.ndarray) -> np.ndarray:
    """The Fiedler navigation embedding — eigenvector of ``λ₂``.

    Returns the eigenvector of the **second-smallest** eigenvalue of a
    Laplacian (real-symmetric *or* complex-Hermitian): the algebraic-
    connectivity / Fiedler vector that embeds the graph for navigation
    (F348). Dispatches to :func:`hermitian_eigendecompose` for complex
    input (e.g. a :func:`magnetic_laplacian`) and
    :func:`symmetric_eigendecompose` for real input (e.g.
    :func:`signed_laplacian` / :func:`dense_laplacian`) — so the heavy
    eigendecomposition runs on the existing C-backed path.

    For ``n < 2`` there is no second eigenvector; raises ``ValueError``.
    """
    M = np.asarray(matrix)
    if M.ndim != 2 or M.shape[0] != M.shape[1]:
        raise ValueError(f"matrix must be square 2-D; got shape {M.shape}")
    if M.shape[0] < 2:
        raise ValueError("fiedler_vector requires n >= 2")
    if np.iscomplexobj(M):
        _eigvals, V = hermitian_eigendecompose(M)
    else:
        _eigvals, V = symmetric_eigendecompose(M)
    # Eigenvalues are ascending; column 0 is the trivial λ₁≈0, column 1
    # is the Fiedler vector (λ₂).
    return V[:, 1].copy()


# The per-block dense-eig cap is MAX_NATIVE_NODES (256); 4 blocks × 256 = 1024.
# 4 is the Klein-4 4-rung (F220/F233): 8+ sectors need the order-3 triality.
SPECTRAL_BLOCK_CAP: int = 4


def spectral_block_dispatch(
    blocks: Sequence,
    *,
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
    combine: bool = True,
) -> Dict[str, object]:
    """Eigendecompose ≤4 dense symmetric blocks in parallel — the 1024-node
    4-sector spectral one-call (RBS-LM UPSTREAM Ask-3; F233 4-rung).

    Runs :func:`jacobi_eigvals` on each of ``blocks`` (1..4 real-symmetric
    matrices, each ``n_i ≤ MAX_NATIVE_NODES`` = 256) on its own thread of a
    4-worker pool — the threaded-Klein-4-streams pattern (F233; the same 4-way
    fan-out as :func:`srmech.amsc.cascade.parallel_sector_dispatch`, but over
    DISTINCT spectral blocks rather than chirality-transforms of one input).
    Four ≤256-node blocks reach **4 × 256 = 1024 nodes** within the native
    dense-eig bound. Each worker reads ONLY its own block (0 cross-thread
    reads), so the parallel spectrum equals the serial spectrum bit-for-bit;
    wall-clock overlap depends on the native GIL-release / free-threaded build.

    Class L (graph-spectral eigendecomposition) over the 4-rung parallel
    dispatch. Numpy-free: a block may be a ``list[list[float]]`` (numpy-absent)
    or an ``ndarray``; per-block eigenvalues are returned as ``list[float]``.

    Parameters
    ----------
    blocks
        A sequence of 1..4 real-symmetric matrices (each ``n_i ≤ 256``).
    max_sweeps, tolerance
        Forwarded to :func:`jacobi_eigvals` per block.
    combine
        When ``True`` (default), also return ``"combined"`` — every block's
        eigenvalues merged and sorted ascending (the whole ≤1024-node
        spectrum). ``False`` leaves ``"combined"`` ``None`` (per-block only).

    Returns
    -------
    dict
        ``{"ok": True, "n_blocks", "block_sizes": [n_i, ...], "n_nodes": Σn_i,
        "blocks": [[eigvals_0...], ...], "combined": [sorted spectrum] | None}``.

    Raises
    ------
    ValueError
        If ``blocks`` is empty, has > 4 entries (the F220 Klein-4 4-cap — 8+
        sectors need the order-3 triality, not this 4-rung), a block is not
        square, or a block has ``n_i > 256`` (the per-block dense-eig bound).
    """
    blist = list(blocks)
    if not blist:
        raise ValueError("spectral_block_dispatch: blocks must be non-empty")
    if len(blist) > SPECTRAL_BLOCK_CAP:
        raise ValueError(
            f"spectral_block_dispatch: at most {SPECTRAL_BLOCK_CAP} blocks "
            f"(the Klein-4 4-rung; 8+ need the order-3 triality, not this "
            f"4-cap); got {len(blist)}"
        )
    sizes: List[int] = []
    for k, blk in enumerate(blist):
        rows = blk.tolist() if hasattr(blk, "tolist") else [list(r) for r in blk]
        nb = len(rows)
        if nb == 0 or any(len(r) != nb for r in rows):
            raise ValueError(
                f"spectral_block_dispatch: block {k} must be square; got "
                f"{nb} rows"
            )
        if nb > MAX_NATIVE_NODES:
            raise ValueError(
                f"spectral_block_dispatch: block {k} has n={nb} > the per-block "
                f"dense-eig bound {MAX_NATIVE_NODES} (4 × {MAX_NATIVE_NODES} = "
                f"1024 nodes max)"
            )
        sizes.append(nb)

    def _eig(blk):
        ev = jacobi_eigvals(blk, max_sweeps=max_sweeps, tolerance=tolerance)
        return list(ev.tolist()) if hasattr(ev, "tolist") else list(ev)

    # The F233 4-rung: each block on its own thread (0 cross-thread reads, so
    # parallel == serial bit-for-bit).
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=SPECTRAL_BLOCK_CAP) as ex:
        per_block = list(ex.map(_eig, blist))

    combined: "Optional[List[float]]" = None
    if combine:
        merged = [float(x) for ev in per_block for x in ev]
        merged.sort()
        combined = merged
    return {
        "ok": True,
        "n_blocks": len(blist),
        "block_sizes": sizes,
        "n_nodes": sum(sizes),
        "blocks": per_block,
        "combined": combined,
    }


# Registry of available Class L op names for the composition engine.
# Order is documentary; consumers iterate by name not position.
LAPLACIAN_OPS: Tuple[str, ...] = (
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "signed_laplacian",
    "magnetic_laplacian",
    "fiedler_vector",
    "jacobi_eigvals",
    "spectral_block_dispatch",
    "hermitian_eigendecompose",
    "symmetric_eigendecompose",
    "dense_matvec_complex",
    "dense_matmul_complex",
    "mat_matmul",
    "mat_solve",
    "mat_hermitian_eigendecompose",
    "mat_lstsq",
    "dense_dot_complex",
    "dense_matmul_real",
    "dense_matvec_real",
    "dense_dot_real",
    "dense_norm",
    "dense_outer_complex",
    "dense_outer_real",
    "elementwise_multiply_complex",
    "elementwise_transcendental",
    "elementwise_hypot",
    "elementwise_sqrt",
    "dense_solve",
    "schur_complement",
    "dirichlet_to_neumann",
)
