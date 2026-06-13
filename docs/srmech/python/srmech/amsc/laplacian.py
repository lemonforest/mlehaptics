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

Most of the C native surface operates on ``n ≤ MAX_NATIVE_NODES`` (256),
which caps the stack-allocated / static degree / row-scaling / augmented
buffers (embedded-safe). When ``HAS_NATIVE`` and ``n ≤ 256`` the dense build
+ ``jacobi_eigvals`` + ``dense_solve`` + ``dense_matvec``/``matmul`` dispatch
to the C symbol **with or without numpy** — the numpy-absent path marshals a
flat ctypes buffer straight from Python ``list``s (UPSTREAM §38; ``jacobi``
~49× faster than the pure-Python cascade). For ``n > 256`` (or no native lib)
srmech's own pure-Python Class-L cascades run.

The numpy-free Hermitian eigen**vector** decomposition
(:func:`mat_hermitian_eigendecompose`) is the one path with a HIGHER native
bound — ``n ≤ MAX_NATIVE_HERMITIAN_NODES`` (2048). It routes through the
reentrant ``srmech_hermitian_eigendecompose_ws`` C entry, which takes a
caller-supplied ``2*n*n``-double workspace (allocated as a ctypes buffer here)
and so has NO 256-sized static/stack array — only a sanity cap. This keeps the
fast native Jacobi (not the minutes-long pure-Python fallback) reachable for
QM grid sizes (e.g. a hydrogen radial grid up to ~1000). Eigenvector sign /
degenerate-subspace rotation is non-unique, so element-wise C/Python parity is
not meaningful (correctness is pinned by eigenvalues + reconstruction +
orthonormality).
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

from math import pi as _PI  # §564: numpy-free π (stdlib math.pi — NOT np.pi)

from .mat import Mat  # §564: the numpy-free 2-D carrier the mat_* engine returns
from .vec import Vec  # rc129: the numpy-free 1-D carrier (vectors / eigenvalues)

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
    "mat_eigvals",
    "mat_svd",
    "mat_norm",
    "mat_dot_real",
    "mat_dot_complex",
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
    "MAX_NATIVE_HERMITIAN_NODES",
    "three_fold_eigvec_groups",
]

MAX_NATIVE_NODES: int = 256

# Hermitian-eig-only native bound. The reentrant C entry
# ``srmech_hermitian_eigendecompose_ws`` takes a CALLER-SUPPLIED 2*n*n-double
# workspace (allocated here as a ctypes buffer), so its native Jacobi path has
# NO 256-sized stack/static array — it is bounded only by this sanity cap
# (== C-side SRMECH_HERMITIAN_WS_MAX_NODES = 2048). Every OTHER native path in
# this module (jacobi_eigvals, dense_solve, dense_matvec/matmul, the non-ws
# hermitian wrapper) DOES rely on a 256-sized fixed buffer or hard cap and so
# stays gated by ``MAX_NATIVE_NODES`` = 256. Used ONLY in
# :func:`mat_hermitian_eigendecompose`'s native-dispatch gate.
MAX_NATIVE_HERMITIAN_NODES: int = 2048


def three_fold_eigvec_groups(L) -> dict:
    """Harmonic-3 three-fold spectral reading of a real-symmetric Laplacian
    (F150): partition the ``n`` eigenvectors (ascending eigenvalue) into three
    contiguous LOW / MID / HIGH bands. Class L is harmonic-3 (chiral rotation /
    3-cycle) per F150 §6.1 — the order-3 reading of the Class-L spectrum. When
    ``n`` is not divisible by 3 the remainder rows go to the later bands so
    ``|low| <= |mid| <= |high|``. Returns ``{"low", "mid", "high"}`` each an
    ``(n, k)`` real :class:`~srmech.amsc.mat.Mat` of the eigenvector COLUMNS in
    that band (rc129; ``.shape`` + ``m[i, j]``, NOT a bare nested list); the
    chirality-aware companion to :func:`symmetric_eigendecompose`.
    """
    _eigvals, V = symmetric_eigendecompose(L)  # V real Mat, columns = eigenvectors
    n_rows = V.n_rows
    n = V.n_cols  # number of eigenvector COLUMNS
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
    # Slice COLUMNS of V (real Mat) into the three contiguous bands → real Mats.
    def _band(c_lo: int, c_hi: int) -> "Mat":
        return Mat.from_rows(
            [[V[i, c] for c in range(c_lo, c_hi)] for i in range(n_rows)],
            is_complex=False,
        )
    return {
        "low": _band(0, n_low),
        "mid": _band(n_low, n_low + n_mid),
        "high": _band(n_low + n_mid, n),
    }


def _can_dispatch_native(n: int) -> bool:
    return (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and n <= MAX_NATIVE_NODES
    )


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


# ── §564: numpy-FREE Class-L core ─────────────────────────────────────
# The whole module is numpy-free (#564): the build → eigvals chain returns
# ``list[list[float]]`` matrices / ``list[float]`` eigenvalues, the complex /
# Hermitian / vectorised ops delegate to the numpy-free ``mat_*`` engine + the
# Class-N rational cascades, and the native C symbols are reached via the
# list-marshal / ctypes-buffer paths (NO numpy on the marshal path). All matrix
# returns are plain nested Python ``list``; vectors / eigenvalues are flat lists.

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
) -> "Mat":
    """Build the dense ``n×n`` adjacency matrix from an undirected edge
    list.

    Self-loops add ``2*w`` to the diagonal (standard graph-theory
    convention). Parallel edges accumulate weights additively.

    Numpy-free (rc129): returns a real :class:`~srmech.amsc.mat.Mat` (``.shape``
    + ``m[i, j]`` + a native C interleaved-buffer wire form), NOT a bare
    ``list[list[float]]`` — the native list-marshal path when ``HAS_NATIVE`` and
    ``n ≤ 256``, else srmech's own pure-Python build.
    """
    if _can_dispatch_native(n):  # UPSTREAM §38: numpy-free native list-marshal
        el, wl = _validate_edges_weights_py(n, edges, weights)
        m = _build_matrix_native_listmarshal("srmech_graph_dense_adjacency", n, el, wl)
        if m is not None:
            return Mat.from_rows(m, is_complex=False)
    return Mat.from_rows(_dense_adjacency_py(n, edges, weights), is_complex=False)


def dense_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> "Mat":
    """Combinatorial graph Laplacian ``L = D − A``.

    Returns an ``n×n`` symmetric positive-semidefinite matrix. For a
    connected graph the smallest eigenvalue is 0 with multiplicity 1
    (Fiedler vector spans the complement).

    Numpy-free (rc129): returns a real :class:`~srmech.amsc.mat.Mat` (``.shape``
    + ``m[i, j]`` + a native C wire form), NOT a bare ``list[list[float]]``.
    """
    if _can_dispatch_native(n):  # UPSTREAM §38: numpy-free native list-marshal
        el, wl = _validate_edges_weights_py(n, edges, weights)
        m = _build_matrix_native_listmarshal("srmech_graph_dense_laplacian", n, el, wl)
        if m is not None:
            return Mat.from_rows(m, is_complex=False)
    return Mat.from_rows(_dense_laplacian_py(n, edges, weights), is_complex=False)


def normalized_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> "Mat":
    """Symmetric normalised Laplacian ``L_sym = I − D^(−1/2) A D^(−1/2)``.

    Isolated vertices (degree 0) have diagonal entry 0 by convention
    (not 1; the ``I`` term only applies where ``D > 0``).

    Numpy-free (rc129): returns a real :class:`~srmech.amsc.mat.Mat` (``.shape``
    + ``m[i, j]`` + a native C wire form), NOT a bare ``list[list[float]]``.
    """
    if _can_dispatch_native(n):  # UPSTREAM §38: numpy-free native list-marshal
        el, wl = _validate_edges_weights_py(n, edges, weights)
        m = _build_matrix_native_listmarshal(
            "srmech_graph_normalized_laplacian", n, el, wl
        )
        if m is not None:
            return Mat.from_rows(m, is_complex=False)
    return Mat.from_rows(_normalized_laplacian_py(n, edges, weights), is_complex=False)


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
    matrix,
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
) -> "Vec":
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

    ``matrix`` is **not** modified by the wrapper — the native path marshals into
    a fresh ctypes buffer; the pure-Python cascade copies its rows.

    Numpy-free (rc129): the input is a :class:`~srmech.amsc.mat.Mat` /
    ``list[list[float]]`` (or any nested sequence) and the return is a 1-D
    :class:`~srmech.amsc.vec.Vec` of the ascending eigenvalues (``.shape == (n,)``
    + scalar ``v[i]``), NOT a bare ``list[float]``. When ``HAS_NATIVE`` and
    ``n ≤ 256`` the numpy-free list-marshal native path runs; else srmech's own
    pure-Python Jacobi cascade.
    """
    rows = [[float(x) for x in r] for r in matrix]
    n = len(rows)
    if n > 0 and all(len(r) == n for r in rows) and _can_dispatch_native(n):
        ev = _jacobi_eigvals_native_listmarshal(rows, n, max_sweeps, tolerance)
        if ev is not None:
            return Vec.from_sequence(ev, is_complex=False)
    return Vec.from_sequence(
        _jacobi_eigvals_py(matrix, max_sweeps, tolerance), is_complex=False
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
    """Coerce a matrix (ndarray-like / list-of-lists / sequence-of-sequences) to
    a square list-of-lists, validating squareness. No numpy required — an
    ndarray-like is coerced via its ``.tolist()`` (a carrier convert, not math)."""
    if hasattr(L, "tolist") and not isinstance(L, Mat):
        L = L.tolist()
    rows = [list(r) for r in L]
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(f"L must be square n×n; got a row of length {len(r)} for n={n}")
    return rows


def _has_complex(rows) -> bool:
    """True iff any leaf of ``rows`` is a ``complex`` with a nonzero imaginary
    part — the layout selector for :func:`Mat.from_rows`."""
    for r in rows:
        for x in r:
            if isinstance(x, complex) and x.imag != 0.0:
                return True
    return False


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
    if hasattr(B, "tolist") and not isinstance(B, Mat):
        B = B.tolist()  # ndarray-like → nested list (carrier convert, not math)
    seq = list(B)
    is_1d = bool(seq) and not isinstance(seq[0], (list, tuple))
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

    With ``exact=True`` the solve is **exact-rational** Gauss–Jordan in
    :class:`fractions.Fraction` (the Class-N core — division is exact, never a
    float reciprocal, F392) and ``X`` is ``list[list[Fraction]]`` (or
    ``list[Fraction]`` for a vector RHS). With ``exact=False`` (the default) the
    float realization rides the numpy-free Mat engine (:func:`mat_solve` — native
    ``srmech_dense_solve_f64`` Gauss–Jordan with partial pivoting, the Class-K
    magnitude pivot — a sign branch, not ``abs()``; else srmech's own exact
    Fraction fallback coerced to float). ``X`` is ``list[list[float]]`` (or
    ``list[float]`` for a vector RHS); a complex system rides the real 2n×2n
    block embedding inside :func:`mat_solve`.

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

    if exact:
        X = _solve_exact(A_rows, B_rows)  # exact Fraction Gauss–Jordan (Class-N)
        return [row[0] for row in X] if is_vec else X

    # Float realization — the numpy-FREE Mat engine (§564). A complex system is
    # carried complex through mat_solve (real 2n×2n block embedding internally).
    cx = _has_complex(A_rows) or _has_complex(B_rows)
    X_mat = mat_solve(
        Mat.from_rows(A_rows, is_complex=cx),
        Mat.from_rows(B_rows, is_complex=cx),
    )

    def _leaf(v):
        # Real-collapse a complex leaf whose imaginary part is ~0 to a float.
        if isinstance(v, complex):
            return complex(v) if cx else float(v.real)
        return float(v)

    rows_out = [[_leaf(X_mat[i, j]) for j in range(X_mat.n_cols)]
                for i in range(X_mat.n_rows)]
    return [r[0] for r in rows_out] if is_vec else rows_out


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
    Numpy-free (§564): rides the numpy-free :func:`mat_solve` (which carries the
    real 2n×2n block embedding internally), returning ``list[list[complex]]`` (or
    a flat ``list[complex]`` for a vector ``B``).
    """
    A_rows = _as_rows(A)
    n = len(A_rows)
    is_vec, B_rows = _as_solve_rhs(B, n)
    X_mat = mat_solve(
        Mat.from_rows(A_rows, is_complex=True),
        Mat.from_rows(B_rows, is_complex=True),
    )
    rows_out = [[complex(X_mat[i, j]) for j in range(X_mat.n_cols)]
                for i in range(X_mat.n_rows)]
    return [r[0] for r in rows_out] if is_vec else rows_out


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
        if exact:
            return [[Fraction(v) for v in r] for r in L_pp]
        return [[float(v) for v in r] for r in L_pp]

    L_pi = _block(b, i)  # L_∂i
    L_ip = _block(i, b)  # L_i∂
    L_ii = _block(i, i)  # L_ii

    if exact:
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

    # Float realization (§564, numpy-FREE). The expensive interior solve rides
    # the numpy-free Mat-engine dense_solve (returns list[list[float]]); the
    # cheap boundary matmul + subtract is a pure-Python list loop:
    #   S[a][c] = L_∂∂[a][c] − Σ_k L_∂i[a][k] · X[k][c].
    X = dense_solve(L_ii, L_ip)  # |i|×|∂| list[list[float]]
    S = [
        [
            float(L_pp[a][c])
            - sum(float(L_pi[a][k]) * X[k][c] for k in range(len(i)))
            for c in range(len(b))
        ]
        for a in range(len(b))
    ]
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
# §564: these delegate to the numpy-free Mat eigen-engine
# (:func:`mat_hermitian_eigendecompose`) and return plain Python lists.


def hermitian_eigendecompose(H):
    """Hermitian eigendecomposition: ``H = V · diag(eigvals) · V^H``.

    Parameters
    ----------
    H
        ``(n, n)`` complex Hermitian matrix (list-of-lists / ndarray-like).
        Hermiticity is not enforced (caller's responsibility).

    Returns
    -------
    (eigvals, V)
        ``eigvals`` is a length-``n`` real :class:`~srmech.amsc.vec.Vec` of
        eigenvalues in ascending order (``.shape == (n,)`` + scalar ``v[i]``).
        ``V`` is an ``n×n`` complex :class:`~srmech.amsc.mat.Mat` — the unitary
        matrix whose COLUMNS are the corresponding eigenvectors (``V[i, j]``).

    Numpy-free (rc129): delegates to the Mat engine
    :func:`mat_hermitian_eigendecompose` (native Jacobi when ``HAS_NATIVE``,
    else srmech's own pure-Python cyclic Jacobi) and returns the carriers
    (``Vec`` eigenvalues + ``Mat`` eigenvectors), NOT bare Python lists.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed.,
    Johns Hopkins, 2013) §8.5 (Hermitian eigendecomposition via
    unitary Jacobi rotations).
    """
    rows = _as_rows(H)
    n = len(rows)
    if n == 0:
        return (Vec(array("d"), 0), Mat(array("d"), 0, 0, is_complex=True))
    Hm = Mat.from_rows([[complex(v) for v in r] for r in rows], is_complex=True)
    evals_mat, V_mat = mat_hermitian_eigendecompose(Hm)
    eigvals = Vec.from_sequence(
        [float(evals_mat[i, 0]) for i in range(evals_mat.n_rows)], is_complex=False
    )
    return eigvals, V_mat


def _canonicalize_eigenvector_signs(V):
    """Pin each real eigenvector column's sign (Class K) deterministically.

    An eigenvector is defined only up to a ``±`` sign (a ``Z₂`` gauge for a
    real-symmetric problem); the native Jacobi peer / pure-Python cascade picks
    it arbitrarily — a *hidden, non-settable* convention. This flips each column
    so its largest-magnitude entry is positive: a deterministic, **settable**
    convention (the endianness precedent), reconstruction-invariant. The flip IS
    the Class-K sign boundary; the magnitude pivot is selected via ``v*v`` so
    there is **no** ``abs()`` and **no** float square root. ``V`` is a nested
    ``list`` (columns = eigenvectors) — the **internal** sign-pin worked on by
    :func:`symmetric_eigendecompose` before it wraps the result in a real
    :class:`~srmech.amsc.mat.Mat`; the result is the (possibly modified) nested
    list. (Within a degenerate eigenspace the larger ``U(k)`` basis freedom is
    solver-chosen and reconstruction-invariant; this pins only the per-column
    ``Z₂``.)
    """
    n_rows = len(V)
    if n_rows == 0:
        return V
    n_cols = len(V[0])
    for j in range(n_cols):
        # Largest-|·| entry of column j via v*v (no abs/sqrt).
        k = 0
        best = V[0][j] * V[0][j]
        for r in range(1, n_rows):
            cur = V[r][j] * V[r][j]
            if cur > best:
                best = cur
                k = r
        if V[k][j] < 0.0:  # Class-K sign pin: pivot → positive
            for r in range(n_rows):
                V[r][j] = -V[r][j]
    return V


def symmetric_eigendecompose(
    L,
) -> Tuple["Vec", "Mat"]:
    """Real-symmetric eigendecomposition: ``L = V · diag(eigvals) · Vᵀ``.

    Real-input specialisation of :func:`hermitian_eigendecompose`.
    Guarantees real ``eigvals`` AND real eigenvectors ``V`` (the Hermitian path
    returns complex ``V`` with imaginary part ~0).

    Parameters
    ----------
    L
        ``(n, n)`` real symmetric matrix (Mat / list-of-lists / ndarray-like).
        Symmetry is not enforced (caller's responsibility).

    Returns
    -------
    (eigvals, V)
        ``eigvals`` is a length-``n`` real :class:`~srmech.amsc.vec.Vec` of
        eigenvalues in ascending order (``.shape == (n,)`` + scalar ``v[i]``).
        ``V`` is an ``n×n`` **real** :class:`~srmech.amsc.mat.Mat` whose COLUMNS
        are the corresponding eigenvectors (``V[i, j]``).

    Class L. Canonical SSoT: Golub & Van Loan, *Matrix Computations*
    (4th ed., Johns Hopkins, 2013) §8.3 (symmetric eigenproblem).

    Numpy-free (rc129): delegates to :func:`hermitian_eigendecompose`
    (real-symmetric IS complex-Hermitian — native Jacobi peer when available,
    else srmech's own pure-Python cyclic Jacobi). The eigenvectors of a
    real-symmetric matrix are real (the Hermitian path returns them with
    imaginary part ~0), so we take ``.real`` and sign-canonicalise each column
    (Class-K, :func:`_canonicalize_eigenvector_signs`) before wrapping in a real
    ``Mat``. Eigenvalues come out ascending as a ``Vec``. Correctness is pinned
    by eigenvalues + reconstruction + orthonormality (the eigenvector sign /
    degenerate-subspace basis is non-unique), not element-wise parity.
    """
    rows = _as_rows(L)
    real_rows = [[float(v.real) if isinstance(v, complex) else float(v) for v in r]
                 for r in rows]
    n = len(real_rows)
    if n == 0:
        return (Vec(array("d"), 0), Mat(array("d"), 0, 0))
    eigvals, V_complex = hermitian_eigendecompose(real_rows)
    # V_complex is a complex Mat (imag ~0 for real-symmetric input); take .real.
    V_real = [[x.real for x in r] for r in V_complex]
    V_canon = _canonicalize_eigenvector_signs(V_real)
    return eigvals, Mat.from_rows(V_canon, is_complex=False)


def _rows(x) -> List[list]:
    """Coerce a matrix (ndarray-like / list-of-lists / :class:`Mat`) to a nested
    ``list`` — numpy-free (``.tolist()`` is a carrier convert, not math)."""
    if hasattr(x, "tolist"):
        x = x.tolist()
    return [list(r) for r in x]


def _vec(x) -> list:
    """Coerce a vector (ndarray-like / list / :class:`Mat` row) to a flat
    ``list`` — numpy-free."""
    if hasattr(x, "tolist"):
        x = x.tolist()
    return list(x)


def dense_matvec_complex(M, v) -> "Vec":
    """Dense complex matrix-vector multiplication: ``M·v``.

    Parameters
    ----------
    M
        ``(rows, cols)`` complex matrix (Mat / list-of-lists / ndarray-like).
    v
        Length-``cols`` complex vector (Vec / list / ndarray-like).

    Returns
    -------
    out
        Length-``rows`` complex :class:`~srmech.amsc.vec.Vec` (``.shape ==
        (rows,)`` + scalar ``v[i]``), NOT a bare ``list[complex]`` (rc129).

    Numpy-free (rc129): wraps ``v`` as a column ``Mat`` and rides
    :func:`mat_matmul` (native zero-copy when present, else a pure-Python
    triple loop). Canonical SSoT: Golub & Van Loan §1.1.
    """
    M_rows = _rows(M)
    v_list = _vec(v)
    rows = len(M_rows)
    cols = len(M_rows[0]) if rows else 0
    for r in M_rows:
        if len(r) != cols:
            raise ValueError("M must be a rectangular 2-D matrix")
    if len(v_list) != cols:
        raise ValueError(
            f"M shape ({rows}, {cols}) incompatible with v length {len(v_list)}"
        )
    if rows == 0:
        return Vec(array("d"), 0, is_complex=True)
    col = Mat.from_rows([[complex(x)] for x in v_list], is_complex=True)
    out = mat_matmul(Mat.from_rows(M_rows, is_complex=True), col)
    return Vec.from_sequence(
        [complex(out[i, 0]) for i in range(out.n_rows)], is_complex=True
    )


def dense_matmul_complex(A, B) -> "Mat":
    """Dense complex matrix-matrix multiplication ``A·B``.

    The srmech Class-L contraction the QM / ``matrix_cascades`` matmul math
    routes through. Numpy-free (rc129): rides :func:`mat_matmul` over the
    :class:`~srmech.amsc.mat.Mat` carrier (native zero-copy when present, else a
    pure-Python triple loop — **never** numpy ``@``).

    Parameters
    ----------
    A
        ``(m, k)`` complex matrix (Mat / list-of-lists / ndarray-like).
    B
        ``(k, n)`` complex matrix.

    Returns
    -------
    out
        ``(m, n)`` complex :class:`~srmech.amsc.mat.Mat` (``.shape`` + ``m[i,
        j]``), NOT a bare ``list[list[complex]]`` (rc129).

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix multiplication).
    """
    A_rows = _rows(A)
    B_rows = _rows(B)
    m = len(A_rows)
    k = len(A_rows[0]) if m else 0
    for r in A_rows:
        if len(r) != k:
            raise ValueError("A must be a rectangular 2-D matrix")
    k2 = len(B_rows)
    n = len(B_rows[0]) if k2 else 0
    for r in B_rows:
        if len(r) != n:
            raise ValueError("B must be a rectangular 2-D matrix")
    if k2 != k:
        raise ValueError(
            f"A shape ({m}, {k}) incompatible with B shape ({k2}, {n})"
        )
    if m == 0 or n == 0:
        return Mat(array("d"), m, n, is_complex=True)
    return mat_matmul(
        Mat.from_rows(A_rows, is_complex=True),
        Mat.from_rows(B_rows, is_complex=True),
    )


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


def _vec_to_interleaved_cbuf(v: "Vec", n_elems: int):
    """The 1-D twin of :func:`_mat_to_interleaved_cbuf`: a
    ``(c_double * 2*n_elems)`` ctypes buffer of ``v``'s elements as interleaved
    ``(re, im)`` doubles — numpy-free. A `Vec` IS something in C — a contiguous
    ``double _Complex`` buffer — so this marshals it to the native layer exactly
    like a `Mat`.

    When ``v`` is complex its ``array('d')`` buffer IS already the interleaved
    ``(re, im)`` layout, so this is a **zero-copy** ``from_buffer`` view (the C
    kernel reads it ``const``). When ``v`` is real the buffer is one double per
    element, so a fresh interleaved buffer is filled ``(re, 0.0)`` once."""
    buf = v.buffer  # array('d')
    if v.is_complex:
        return (ctypes.c_double * (2 * n_elems)).from_buffer(buf)  # zero-copy
    cbuf = (ctypes.c_double * (2 * n_elems))()
    for idx in range(n_elems):
        cbuf[2 * idx] = buf[idx]  # imag slot stays 0.0
    return cbuf


def _vec_from_interleaved_cbuf(cbuf, n: int, *, want_complex: bool):
    """The 1-D twin of :func:`_mat_from_interleaved_cbuf`: wrap an interleaved
    ``(re, im)`` ctypes buffer back into a ``Vec`` (numpy-free). ``want_complex``
    keeps the interleaved layout; otherwise the real parts (every even slot)
    form a real ``Vec``."""
    from .vec import Vec  # numpy-free carrier; local import keeps load-order clean
    if want_complex:
        return Vec(array("d", cbuf), n, is_complex=True)
    return Vec(array("d", (cbuf[2 * i] for i in range(n))), n)


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
    the native ``srmech_hermitian_eigendecompose_ws`` reads, so a complex `Mat`
    feeds the kernel **zero-copy** (``from_buffer``) and a real `Mat` is
    interleaved ``(re, 0)`` once — **NO numpy** on the native path. The reentrant
    ``_ws`` entry takes a caller-supplied ``2*n*n``-double workspace (allocated
    here as a ctypes buffer), so the fast native Jacobi serves ``n`` up to
    ``MAX_NATIVE_HERMITIAN_NODES`` (2048) without a 256-sized static/stack
    buffer; on a lib predating the ``_ws`` symbol it falls back to the older
    non-ws ``srmech_hermitian_eigendecompose`` for ``n ≤ MAX_NATIVE_NODES``
    (256). With no native lib — or ``n`` > 2048, or a native convergence miss —
    the fallback is srmech's own pure-Python **cyclic Jacobi**
    (:func:`_hermitian_eig_py`, real-symmetric directly / complex-Hermitian via
    the real ``2n×2n`` embedding), so the op is unconditionally numpy-free.

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
    # Native zero-copy paths: Mat interleaved buffer → C kernel → Mats.
    # Preferred: the reentrant ``_ws`` entry takes a caller-supplied 2*n*n
    # workspace, so the FAST native Jacobi serves n up to
    # MAX_NATIVE_HERMITIAN_NODES (2048) with no 256-sized static buffer. The
    # older non-ws ``srmech_hermitian_eigendecompose`` (1 MiB thread-local
    # static) stays the fallback for n ≤ 256 on libs built before the _ws
    # symbol existed.
    have_native = _native.HAS_NATIVE and _native.LIB is not None
    if (have_native
            and hasattr(_native.LIB, "srmech_hermitian_eigendecompose_ws")
            and n <= MAX_NATIVE_HERMITIAN_NODES):
        h_il = _mat_to_interleaved_cbuf(h, n * n)
        eigvals_buf = (ctypes.c_double * n)()
        v_il = (ctypes.c_double * (2 * n * n))()
        ws_len = 2 * n * n
        workspace = (ctypes.c_double * ws_len)()
        rc = _native.LIB.srmech_hermitian_eigendecompose_ws(
            ctypes.c_uint32(n), h_il, eigvals_buf, v_il,
            workspace, ctypes.c_size_t(ws_len),
        )
        if rc == _native.SRMECH_OK:
            eigvals = Mat(array("d", eigvals_buf), n, 1)
            eigvecs = _mat_from_interleaved_cbuf(v_il, n, n, want_complex=True)
            return eigvals, eigvecs
        # Non-OK (convergence miss / over-bound) → numpy-free Jacobi fallback.
    elif (have_native
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


# ---------------------------------------------------------------------------
# mat_eigvals — Mat-carrier general (non-Hermitian) eigenvalue multiset.
# Foundation op #4 of the numpy-CARRIER removal arc (#564): the numpy-free peer
# of matrix_cascades.eigvals, so esprit's general-eig route can flip off the
# numpy-carrier matrix_cascades stack onto the Mat path. mat_matmul/mat_solve/
# mat_hermitian_eigendecompose handle the Hermitian + linear-system cases; this
# closes the general non-Hermitian eigenproblem.
# ---------------------------------------------------------------------------

_MAT_EIG_DEFLATE_TOL = 1e-14   # subdiagonal/scale below this → Schur deflation


def _modulus_c(z: complex) -> float:
    """|z| via the Class-N hypot cascade (no ``abs()`` — discipline)."""
    return _rhypot(float(z.real), float(z.imag))


def _complex_sqrt_local(w: complex) -> complex:
    """Principal complex square root via the Class-N real cascades
    (:func:`srmech.amsc.rational.hypot` + ``sqrt``) — no ``cmath.sqrt``. The
    laplacian-local twin of ``matrix_cascades._complex_sqrt``, redefined here so
    :func:`mat_eigvals` needs **no** import from ``matrix_cascades`` (which
    imports THIS module — that would be a circular import). For ``w = a + i·b``,
    ``√w = √((|w|+a)/2) + i·sign(b)·√((|w|−a)/2)`` (principal branch, ``Re ≥ 0``):
    two Class-N real ``sqrt`` cascades joined by a **Class-K** sign-branch."""
    a = float(w.real)
    b = float(w.imag)
    if a == 0.0 and b == 0.0:
        return 0j
    mod = _rhypot(a, b)                             # Class-N |w| (≥ |a| exactly)
    re_arg = (mod + a) / 2.0                        # both radicands ≥ 0
    im_arg = (mod - a) / 2.0                        # mathematically; a tiny <0 is
    re = _rsqrt(re_arg) if re_arg > 0.0 else 0.0    # float round-off → Class-K
    im = _rsqrt(im_arg) if im_arg > 0.0 else 0.0    # pin-slot at zero
    return complex(re, im if b >= 0.0 else -im)     # Class-K sign-branch (no copysign)


def _eig2x2(aa: complex, bb: complex, cc: complex, dd: complex) -> Tuple[complex, complex]:
    """Both eigenvalues of the 2×2 ``[[aa,bb],[cc,dd]]`` in closed form:
    ``λ = (tr ± √(tr²−4·det))/2`` (Class-C complex shift root via the Class-N
    :func:`_complex_sqrt_local` cascade)."""
    tr = aa + dd
    det = aa * dd - bb * cc
    disc = _complex_sqrt_local(tr * tr - 4.0 * det)   # Class-C complex shift root
    return (tr + disc) / 2.0, (tr - disc) / 2.0


def _qr_complex_list(
    rows: List[List[complex]],
) -> Tuple[List[List[complex]], List[List[complex]]]:
    """Householder QR of a square complex list-of-lists → ``(Q, R)`` lists,
    numpy-free (the pure-``complex`` twin of ``matrix_cascades.qr`` so the
    shifted-QR sweep in :func:`mat_eigvals` needs no numpy carrier). ``Q``
    unitary, ``R`` upper-triangular, ``Q·R = A`` — exactly the invariant a
    shifted-QR eigen-step requires (``RQ = Qᴴ·A·Q`` is the similarity that
    preserves the spectrum). Reflector phase is a **Class-K** pin-slot."""
    m = len(rows)
    R = [[complex(rows[i][j]) for j in range(m)] for i in range(m)]
    Q = [[1 + 0j if i == j else 0j for j in range(m)] for i in range(m)]
    for k in range(m):
        normx2 = 0.0
        for i in range(k, m):
            normx2 += (R[i][k].conjugate() * R[i][k]).real
        if normx2 <= 0.0:
            continue
        normx = _rsqrt(normx2)                       # Class-N ‖x‖
        x0 = R[k][k]
        modx0 = _rhypot(x0.real, x0.imag)
        phase = (x0 / modx0) if modx0 > 0.0 else complex(1.0, 0.0)
        alpha = -phase * normx                       # Class-K pin-slot phase
        v = [R[i][k] for i in range(k, m)]
        v[0] = v[0] - alpha
        vhv = 0.0
        for vi in v:
            vhv += (vi.conjugate() * vi).real
        if vhv == 0.0:
            continue
        beta = 2.0 / vhv                             # Class-N 1/(vᴴv) scale
        for j in range(m):                           # R ← (I − β v vᴴ) R
            s = 0j
            for idx, i in enumerate(range(k, m)):
                s += v[idx].conjugate() * R[i][j]
            s *= beta
            for idx, i in enumerate(range(k, m)):
                R[i][j] -= v[idx] * s
        for i in range(m):                           # Q ← Q (I − β v vᴴ)
            s = 0j
            for idx, jj in enumerate(range(k, m)):
                s += Q[i][jj] * v[idx]
            s *= beta
            for idx, jj in enumerate(range(k, m)):
                Q[i][jj] -= s * v[idx].conjugate()
    return Q, R


def mat_eigvals(a: "Mat", *, max_sweeps: int = 500) -> List[complex]:
    """Eigenvalue MULTISET of a general (non-Hermitian) square matrix over the
    :class:`~srmech.amsc.mat.Mat` carrier — foundation op #4 of the numpy-CARRIER
    removal arc (#564), the numpy-free peer of ``matrix_cascades.eigvals``.

    The shifted-QR iteration — **Class K** (iterate-to-convergence asymptotic-DoF)
    ∘ **Class L** (the spectral content) ∘ ``{QR}`` (per-step Householder, the
    numpy-free :func:`_qr_complex_list`) ∘ **Class C** (Wilkinson spectral shift)
    — runs in plain ``complex`` lists with the ``RQ`` recombination routed through
    the native :func:`mat_matmul`, so it is **unconditionally numpy-free**. Small
    sizes take a closed form: ``n=1`` is the scalar, the trailing-``2×2`` block
    deflates via :func:`_eig2x2` (the quadratic over :func:`_complex_sqrt_local`).
    The iteration is complex throughout, so it converges to the complex
    eigenvalues of a real matrix directly (e.g. the 2×2 rotation yields ``±i``).

    Returns the length-``n`` ``list[complex]`` eigenvalue multiset — unique only
    as a SET; the multiset matches NumPy ``eigvals`` to ~1e-9 for moderate sizes.
    For a Hermitian ``A`` prefer :func:`mat_hermitian_eigendecompose` (exact
    Jacobi — pure Class L). Raises ``ValueError`` on a non-square ``A``.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §7.5 (the practical QR algorithm with Wilkinson shifts).
    """
    from .mat import Mat
    assert isinstance(a, Mat), (
        "mat_eigvals operand must be Mat (the numpy-free 2-D carrier)"
    )
    n = a.n_rows
    if a.n_cols != n:
        raise ValueError(f"mat_eigvals: A must be square; got {a.shape}")
    if n == 0:
        return []
    H = [[complex(a[i, j]) for j in range(n)] for i in range(n)]
    if n == 1:
        return [H[0][0]]
    eigs: List[complex] = []
    m = n
    sweeps = 0
    while m > 0:
        if m == 1:
            eigs.append(H[0][0])                      # Class-L: last eigenvalue
            break
        scale = _modulus_c(H[m - 2][m - 2]) + _modulus_c(H[m - 1][m - 1])
        if _modulus_c(H[m - 1][m - 2]) <= _MAT_EIG_DEFLATE_TOL * (scale + 1e-300):
            eigs.append(H[m - 1][m - 1])              # Class-L: deflate eigenvalue
            m -= 1
            continue
        if m == 2:
            lam1, lam2 = _eig2x2(H[0][0], H[0][1], H[1][0], H[1][1])  # closed form
            eigs.append(lam1)
            eigs.append(lam2)
            break
        # Wilkinson shift: the trailing-2×2 eigenvalue closest to H[m-1][m-1].
        lam1, lam2 = _eig2x2(
            H[m - 2][m - 2], H[m - 2][m - 1], H[m - 1][m - 2], H[m - 1][m - 1]
        )
        dd = H[m - 1][m - 1]
        mu = lam1 if _modulus_c(lam1 - dd) < _modulus_c(lam2 - dd) else lam2
        # QR of the leading m×m block minus μI; then H[:m,:m] ← R·Q + μI, the RQ
        # contraction routed through the native Mat-carrier mat_matmul (Class K).
        sub = [[H[i][j] - (mu if i == j else 0j) for j in range(m)] for i in range(m)]
        Q, R = _qr_complex_list(sub)                  # {QR} numpy-free
        rq = mat_matmul(
            Mat.from_rows(R, is_complex=True), Mat.from_rows(Q, is_complex=True)
        )
        for i in range(m):
            for j in range(m):
                H[i][j] = complex(rq[i, j]) + (mu if i == j else 0j)
        sweeps += 1
        if sweeps > max_sweeps * n:                   # no-silent-hang backstop
            for i in range(m):
                eigs.append(H[i][i])
            break
    return eigs


def mat_svd(a: "Mat") -> Tuple["Mat", List[float], "Mat"]:
    """Numpy-free **full** singular-value decomposition ``A = U·diag(S)·Vᴴ`` over
    the :class:`~srmech.amsc.mat.Mat` carrier — foundation op **#5** of the
    numpy-CARRIER removal arc (#564), composed from the native-backed
    :func:`mat_matmul` + :func:`mat_hermitian_eigendecompose` trio (plus a
    pure-Python orthonormal completion), so it is **unconditionally numpy-free**.

    ``A`` is an ``(m, n)`` real or complex `Mat`. Returns ``(U, S, Vh)`` matching
    NumPy's full-matrices ``svd(A, full_matrices=True)`` shape contract:

    * ``U`` — ``(m, m)`` **complex** `Mat`, unitary (left singular vectors);
    * ``S`` — ``list[float]`` of length ``min(m, n)``, the singular values
      **descending** (non-negative);
    * ``Vh`` — ``(n, n)`` **complex** `Mat`, unitary (``= Vᴴ``).

    so ``A = U[:, :k]·diag(S)·Vh[:k, :]`` with ``k = min(m, n)``.

    **Method (Gram / eigen-SVD).** The right singular vectors are the
    eigenvectors of the Hermitian PSD ``AᴴA`` (``n×n``) via
    :func:`mat_hermitian_eigendecompose` (ascending → reordered descending);
    the singular values are ``σⱼ = √λⱼ`` (the Class-N :func:`rational.sqrt`,
    libm-free; tiny negative ``λ`` from round-off clamped to 0). The left
    singular vectors are ``uⱼ = A·vⱼ / σⱼ`` for ``σⱼ`` above the rank tolerance
    ``σ_max · max(m, n) · 1e-6`` (relative to the Gram eigen-route's small-σ
    floor ~1e-7·σ_max, NOT machine-eps); ``U`` is then completed from ``rank`` to ``m``
    orthonormal columns by modified Gram–Schmidt against the standard basis
    (the left-nullspace block).

    **Accuracy contract (per ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]``).**
    SVD is non-unique (a per-pair phase, and an arbitrary unitary basis inside a
    degenerate-σ or null subspace), so this is **value-faithful, NOT bit-
    identical** to NumPy: the *reconstruction* ``U·diag(S)·Vᴴ ≈ A`` and the
    *singular values* ``S`` are accurate to ~1e-9 for the large σ; the small/zero
    singular values (and the U/V null-space columns they pair with) sit ~1e-7 —
    fine for the dominant-mode MIMO precoder/combiner the DSP layer feeds it, but
    do **not** route a ``matrix_rank`` / null-space-accuracy consumer through it.

    Raises ``ValueError`` on a non-2-D / empty ``A``.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §8.6 (SVD) + §5.4 (the AᴴA eigen-route and its conditioning).
    """
    from .mat import Mat
    assert isinstance(a, Mat), (
        "mat_svd operand must be Mat (the numpy-free 2-D carrier)"
    )
    m, n = a.n_rows, a.n_cols
    if m == 0 or n == 0:
        raise ValueError(f"mat_svd: A must be a non-empty 2-D matrix; got {a.shape}")

    # Right singular vectors = eigenvectors of the Hermitian PSD Gram AᴴA (n×n).
    ah = a.conj().T                                   # Aᴴ (n, m) — Class-K conj ∘ T
    aha = mat_matmul(ah, a)                           # (n, n) Hermitian PSD
    evals, V = mat_hermitian_eigendecompose(aha)      # λ (n,1) ascending; V (n,n) unitary
    lam = [float(evals[i, 0]) for i in range(n)]
    order = sorted(range(n), key=lambda i: lam[i], reverse=True)   # descending λ → σ
    # V columns reordered descending; vcols[j] is the j-th right singular vector.
    vcols = [[V[i, order[j]] for i in range(n)] for j in range(n)]
    sigma = [_rsqrt(lam[order[j]] if lam[order[j]] > 0.0 else 0.0) for j in range(n)]
    k = min(m, n)
    S = [sigma[j] for j in range(k)]

    # Left singular vectors: uⱼ = A·vⱼ / σⱼ for σⱼ above the rank tolerance.
    # The gate is RELATIVE to σ_max at the cascade's small-σ floor (~1e-6·σ_max),
    # NOT machine-eps: the Gram eigen-route resolves a null σ only to ~√(λ-floor)
    # ≈ 1e-7·σ_max (per [[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]),
    # so a sub-floor σ would make uⱼ = A·vⱼ/σⱼ amplify that error into a non-unit
    # column. Such columns route through the orthonormal completion below instead.
    smax = sigma[0] if n else 0.0
    tol = smax * float(max(m, n)) * 1e-6
    arows = [[complex(a[i, j]) for j in range(n)] for i in range(m)]
    ucols: List[List[complex]] = []
    for j in range(k):
        if sigma[j] > tol:
            vj = vcols[j]
            av = [sum(arows[i][t] * vj[t] for t in range(n)) for i in range(m)]
            inv = 1.0 / sigma[j]
            ucols.append([x * inv for x in av])
        else:
            break                                     # σ descending → rest are ≤ tol

    # Orthonormal completion of U (left-nullspace block) via modified Gram–Schmidt
    # against the standard basis — arbitrary-but-valid (SVD null basis is free).
    e = 0
    while len(ucols) < m and e < m:
        cand = [(1.0 + 0j) if i == e else 0j for i in range(m)]
        for u in ucols:
            proj = sum(u[i].conjugate() * cand[i] for i in range(m))
            cand = [cand[i] - proj * u[i] for i in range(m)]
        norm = _rsqrt(sum(x.real * x.real + x.imag * x.imag for x in cand))
        if norm > 1e-12:
            inv = 1.0 / norm
            ucols.append([x * inv for x in cand])
        e += 1

    u_rows = [[ucols[c][i] for c in range(m)] for i in range(m)]   # column c = ucols[c]
    U = Mat.from_rows(u_rows, is_complex=True)
    v_rows = [[vcols[j][i] for j in range(n)] for i in range(n)]   # V (n,n): col j = vcols[j]
    Vh = Mat.from_rows(v_rows, is_complex=True).conj().T           # Vᴴ
    return U, S, Vh


# ── Mat-carrier numpy-FREE norm + dot (rc114 foundation; #564) ───────────────
#
# ``dense_norm`` / ``dense_dot_real`` / ``dense_dot_complex`` are numpy CARRIERS
# (they call ``np.ascontiguousarray`` / ``np.iscomplexobj`` / the elementwise-
# multiply cascade over numpy arrays) and RAISE on a numpy-absent install — the
# rc70 *runnable ≠ loadable* trap. Nothing in the tree computed ‖x‖ or a·b over
# the numpy-free :class:`Mat` / :class:`HV` carriers. These three close that gap:
# the consumer-flips (qm Clifford / unitarity / η-Hermiticity residuals, so8
# Gram-Schmidt) route their norms / dots through these instead of the dense_*
# carriers, so they run with **no numpy present at all**. Value-faithful to the
# dense_* / numpy peers to ~1 ULP (same float sum-of-products), NOT bit-exact.


def _iter_mat_scalars(v):
    """Yield plain ``float`` / ``complex`` scalars from a :class:`Mat` / :class:`HV`
    / flat sequence (row-major, flattened) — numpy-FREE. The single coercion the
    Mat-carrier norm / dot reductions share."""
    from .mat import Mat
    if isinstance(v, Mat):
        buf = v.buffer
        if v.is_complex:
            for k in range(0, len(buf), 2):
                yield complex(buf[k], buf[k + 1])
        else:
            for x in buf:
                yield float(x)
        return
    seq = v.tolist() if hasattr(v, "tolist") else v  # HV / list / tuple / array / 1-D ndarray
    for x in seq:
        yield x


def mat_norm(x) -> float:
    """Euclidean (vector 2-norm) / Frobenius (matrix) norm ``‖x‖ = √(Σ|xᵢ|²)`` →
    ``float`` — the **numpy-FREE** peer of :func:`dense_norm`.

    Accepts a :class:`Mat` (Frobenius over all elements), an :class:`HV`, or a
    flat real/complex sequence (vector 2-norm). Sums ``|xᵢ|²`` over a pure-Python
    reduction — for complex ``z`` the squared modulus is ``z.real² + z.imag²``
    (NO ``abs()``, NO ``math.hypot``) — then takes the libm-free **Class-N**
    :func:`srmech.amsc.rational.sqrt` root. Value-faithful to :func:`dense_norm`
    / the NumPy 2-norm to round-off (~1 ULP); empty → ``0.0``.

    **Class N** (``rational.sqrt`` root) ∘ **Class M** (the ``Σ|xᵢ|²`` self-bind).
    Canonical SSoT: Golub & Van Loan §2.3 (vector / Frobenius norms)."""
    total = 0.0
    for s in _iter_mat_scalars(x):
        if isinstance(s, complex):
            total += s.real * s.real + s.imag * s.imag
        else:
            sv = float(s)
            total += sv * sv
    return _rsqrt(total) if total > 0.0 else 0.0


def mat_dot_real(a, b) -> float:
    """Real bilinear inner product ``Σ aᵢ bᵢ`` → ``float`` — the **numpy-FREE**
    peer of :func:`dense_dot_real` over :class:`Mat` / :class:`HV` / flat
    sequences (pure-Python reduction; the elements are flattened row-major).

    Canonical SSoT: Golub & Van Loan §1.1 (textbook inner product)."""
    total = 0.0
    for x, y in zip(_iter_mat_scalars(a), _iter_mat_scalars(b)):
        total += float(x.real if isinstance(x, complex) else x) * float(
            y.real if isinstance(y, complex) else y
        )
    return total


def mat_dot_complex(a, b) -> complex:
    """Complex **bilinear** inner product ``a · b = Σ aᵢ bᵢ`` → ``complex`` — the
    **numpy-FREE** peer of :func:`dense_dot_complex`. Plain bilinear (matching
    NumPy ``a·b`` on two 1-D arrays, **NOT** the Hermitian ``vdot`` that
    conjugates its first argument — callers wanting the Hermitian form pass
    ``a.conj()`` explicitly, exactly as the η-sandwich sites already spell it).
    Pure-Python reduction over the flattened :class:`Mat` / :class:`HV` / sequence."""
    total = 0j
    for x, y in zip(_iter_mat_scalars(a), _iter_mat_scalars(b)):
        total += complex(x) * complex(y)
    return total


def dense_dot_complex(a, b) -> complex:
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
    a_list = _vec(a)
    b_list = _vec(b)
    if len(a_list) != len(b_list):
        raise ValueError(
            f"dense_dot_complex: a length {len(a_list)} != b length {len(b_list)}"
        )
    # Plain BILINEAR Σ aᵢ bᵢ (NOT conjugated) — numpy-free pure-Python reduction.
    return complex(sum(complex(ai) * complex(bi) for ai, bi in zip(a_list, b_list)))


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
def dense_matmul_real(A, B) -> "Mat":
    """Dense real matrix-matrix multiplication ``A·B`` → real :class:`Mat`.

    Real peer of :func:`dense_matmul_complex` (the same Mat-carrier matmul on
    imag-free input, dropping the exactly-zero imaginary part). Numpy-free.

    Parameters
    ----------
    A
        ``(m, k)`` real matrix.
    B
        ``(k, n)`` real matrix.

    Returns
    -------
    out
        ``(m, n)`` real :class:`~srmech.amsc.mat.Mat` (``.shape`` + ``m[i, j]``),
        NOT a bare ``list[list[float]]`` (rc129).

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix multiplication).
    """
    out = dense_matmul_complex(A, B)  # complex Mat
    real_rows = [[v.real if isinstance(v, complex) else float(v) for v in r]
                 for r in out]
    return Mat.from_rows(real_rows, is_complex=False)


def dense_matvec_real(M, v) -> "Vec":
    """Dense real matrix-vector multiplication ``M·v`` → real :class:`Vec`.

    Real peer of :func:`dense_matvec_complex` (the same Mat-carrier matvec on
    imag-free input, dropping the zero imaginary part). Numpy-free.

    Parameters
    ----------
    M
        ``(rows, cols)`` real matrix.
    v
        Length-``cols`` real vector.

    Returns
    -------
    out
        Length-``rows`` real :class:`~srmech.amsc.vec.Vec` (``.shape ==
        (rows,)`` + scalar ``v[i]``), NOT a bare ``list[float]`` (rc129).

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix-vector product).
    """
    out = dense_matvec_complex(M, v)  # complex Vec; iterates scalars
    return Vec.from_sequence(
        [x.real if isinstance(x, complex) else float(x) for x in out],
        is_complex=False,
    )


def dense_dot_real(a, b) -> float:
    """Dense real inner product ``Σ aᵢ bᵢ`` → Python ``float``.

    Real peer of :func:`dense_dot_complex` (the same bilinear reduction on
    imag-free input). Numpy-free (§564).

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
    return float(dense_dot_complex(a, b).real)


def _flatten_scalars(x) -> list:
    """Flatten a matrix (nested list / ndarray-like / Mat) OR a vector to a flat
    ``list`` of plain scalars — numpy-free. ``.tolist()`` is a carrier convert."""
    if hasattr(x, "tolist"):
        x = x.tolist()
    flat = []
    for elem in x:
        if isinstance(elem, (list, tuple)):
            flat.extend(elem)
        else:
            flat.append(elem)
    return flat


def dense_norm(x) -> float:
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
    flat = _flatten_scalars(x)
    if not flat:
        return 0.0
    # Σ|xᵢ|² over a pure-Python reduction (re²+im² for complex; NO abs()).
    sq = 0.0
    for v in flat:
        if isinstance(v, complex):
            sq += v.real * v.real + v.imag * v.imag
        else:
            fv = float(v)
            sq += fv * fv
    return _rsqrt(sq) if sq > 0.0 else 0.0


def dense_outer_complex(a, b) -> "Mat":
    """Dense complex outer product ``a ⊗ b`` → ``out[i, j] = aᵢ bⱼ``.

    The rank-1 contraction the QM density-matrix / momentum-tensor sites route
    through, so numpy stays carriers-only (no numpy ``outer`` engine). An outer
    product IS a ``k = 1`` matrix product — ``a`` as a column, ``b`` as a row —
    so this is exactly :func:`dense_matmul_complex` on the reshaped pair, each
    entry a single complex multiply (no inner summation).

    Like numpy ``outer`` this does NOT conjugate ``b`` — the plain bilinear
    ``aᵢ bⱼ``. Callers wanting ``|ψ⟩⟨ψ|`` pass ``b = ψ.conj()`` explicitly (the
    ``.conj()`` is a carrier transform, not a math-engine op), exactly as the
    ``outer(psi, psi.conj())`` sites already spell it.

    Parameters
    ----------
    a
        Length-``m`` complex vector (the column; Vec / list / ndarray-like).
    b
        Length-``n`` complex vector (the row).

    Returns
    -------
    out
        ``(m, n)`` complex :class:`~srmech.amsc.mat.Mat` ``aᵢ bⱼ`` (``.shape`` +
        ``m[i, j]``), NOT a bare ``list[list[complex]]`` (rc129).

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1 (rank-1 update / outer product).
    """
    a_list = _vec(a)
    b_list = _vec(b)
    # Plain bilinear outer aᵢ·bⱼ (NO conjugation) — numpy-free nested loop.
    rows = [[complex(ai) * complex(bj) for bj in b_list] for ai in a_list]
    if not rows:  # m == 0 → empty (0, n) complex Mat
        return Mat(array("d"), 0, len(b_list), is_complex=True)
    return Mat.from_rows(rows, is_complex=True)


def dense_outer_real(a, b) -> "Mat":
    """Dense real outer product ``a ⊗ b`` → ``out[i, j] = aᵢ bⱼ`` (real :class:`Mat`).

    Real peer of :func:`dense_outer_complex` (same bilinear outer on imag-free
    input, dropping the exactly-zero imaginary part). Numpy-free.

    Parameters
    ----------
    a
        Length-``m`` real vector.
    b
        Length-``n`` real vector.

    Returns
    -------
    out
        ``(m, n)`` real :class:`~srmech.amsc.mat.Mat` ``aᵢ bⱼ`` (``.shape`` +
        ``m[i, j]``), NOT a bare ``list[list[float]]`` (rc129).

    Canonical SSoT: Golub & Van Loan §1.1 (rank-1 outer product).
    """
    out = dense_outer_complex(a, b)  # complex Mat
    real_rows = [[v.real if isinstance(v, complex) else float(v) for v in r]
                 for r in out]
    if not real_rows:
        return Mat(array("d"), 0, out.n_cols, is_complex=False)
    return Mat.from_rows(real_rows, is_complex=False)


# ── rc129 shape-polymorphic elementwise rank detection ──────────────────────
# The elementwise ops preserve INPUT RANK: a Mat / 2-D nested input → a Mat out;
# a Vec / 1-D flat input → a Vec out. Rank is read off the input shape — a Mat
# (or a nested list whose first element is itself a sequence) is rank-2; a Vec
# (or a flat list / 1-D ndarray) is rank-1. The element math is unchanged; only
# the output CARRIER tracks the input rank.


def _ew_is_matrix(x) -> bool:
    """True iff ``x`` is a rank-2 elementwise input (a :class:`Mat` or a nested
    list-of-rows). A :class:`Vec`, a flat list / sequence, or a 1-D ndarray-like
    is rank-1 (False)."""
    if isinstance(x, Mat):
        return True
    if isinstance(x, Vec):
        return False
    seq = x.tolist() if hasattr(x, "tolist") else x  # ndarray-like → nested/flat
    try:
        first = next(iter(seq))
    except (TypeError, StopIteration):
        return False  # empty / non-iterable → treat as a (degenerate) vector
    return isinstance(first, (list, tuple))


def _ew_mat_shape(x) -> Tuple[int, int]:
    """``(n_rows, n_cols)`` of a rank-2 elementwise input (Mat / nested list)."""
    if isinstance(x, Mat):
        return x.shape
    rows = x.tolist() if hasattr(x, "tolist") and not isinstance(x, Mat) else x
    rows = list(rows)
    n_rows = len(rows)
    n_cols = len(rows[0]) if n_rows else 0
    return (n_rows, n_cols)


def _ew_pack(flat: list, *, matrix: bool, shape, is_complex: bool):
    """Rebuild an elementwise result from a FLAT list into the rank-preserving
    carrier — a :class:`Mat` (``matrix=True``, reshaped to ``shape``) or a 1-D
    :class:`Vec` (``matrix=False``). ``is_complex`` pins the carrier dtype."""
    if matrix:
        n_rows, n_cols = shape
        rows = [flat[r * n_cols:(r + 1) * n_cols] for r in range(n_rows)]
        if not rows:
            return Mat(array("d"), 0, n_cols, is_complex=is_complex)
        return Mat.from_rows(rows, is_complex=is_complex)
    return Vec.from_sequence(flat, is_complex=is_complex)


def elementwise_multiply_complex(a, b):
    """Elementwise complex multiplication: ``a * b`` — SHAPE-POLYMORPHIC (rc129).

    Equal-shape inputs (numpy-free — no broadcasting; the callers pass
    equal-length operands). Preserves input rank: a :class:`Mat` / 2-D ``a`` →
    a complex :class:`~srmech.amsc.mat.Mat` out; a :class:`Vec` / 1-D flat ``a``
    → a complex :class:`~srmech.amsc.vec.Vec` out (rc129 — NOT a bare
    ``list[complex]``). The shape is read off ``a``."""
    a_mat = _ew_is_matrix(a)
    shape = _ew_mat_shape(a) if a_mat else None
    a_list = _flatten_scalars(a) if a_mat else _vec(a)
    b_list = _flatten_scalars(b) if _ew_is_matrix(b) else _vec(b)
    if len(a_list) != len(b_list):
        raise ValueError(
            f"elementwise_multiply_complex: length mismatch "
            f"{len(a_list)} vs {len(b_list)}"
        )
    flat = [complex(ai) * complex(bi) for ai, bi in zip(a_list, b_list)]
    return _ew_pack(flat, matrix=a_mat, shape=shape, is_complex=True)


_TRANS_OP_IDS = {
    "exp": _native.SRMECH_TRANS_EXP,
    "cos": _native.SRMECH_TRANS_COS,
    "sin": _native.SRMECH_TRANS_SIN,
    "log": _native.SRMECH_TRANS_LOG,
}


def _real_transcendental_native(flat_real: list, op_id: int):
    """numpy-free native ``srmech_elementwise_transcendental`` over a flat list of
    real scalars — marshals into a ``(c_double * n)`` ctypes buffer (numpy-free,
    exactly as :func:`_jacobi_eigvals_native_listmarshal` does) and reads the
    result back into a ``list[float]``. Returns ``(ok, out_list, rc)``; ``ok`` is
    False when there is no native lib (caller runs the pure-Python cascade)."""
    n = len(flat_real)
    if n == 0 or not (_native.HAS_NATIVE and _native.LIB is not None):
        return False, None, None
    inp = (ctypes.c_double * n)(*(float(x) for x in flat_real))
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_elementwise_transcendental(
        ctypes.c_uint32(n), inp, ctypes.c_int(op_id), out,
    )
    if rc == _native.SRMECH_OK:
        return True, [out[i] for i in range(n)], rc
    return True, None, rc


def _real_transcendental_loop(flat_real: list, op_name: str) -> list:
    """numpy-free real ``exp``/``cos``/``sin``/``log`` via the Class-N scalar cascades.

    The pure-Python / no-native fallback for :func:`elementwise_transcendental`.
    ``flat_real`` is a flat ``list`` of real scalars; returns a flat
    ``list[float]``. Every element runs the libm-free
    :mod:`srmech.amsc.rational` cascade.
    """
    flat = [float(x) for x in flat_real]
    if op_name == "log" and flat and min(flat) <= 0.0:
        raise ValueError("log requires all arr[i] > 0")
    fn = {"exp": _rexp, "cos": _rcos, "sin": _rsin, "log": _rlog}[op_name]
    return [fn(x) for x in flat]


def _complex_transcendental_loop(flat, op_name: str) -> list:
    """numpy-free complex ``exp``/``cos``/``sin``/``log`` via Class-N real cascades.

    The complex-input path for :func:`elementwise_transcendental`. ``flat`` is a
    flat sequence of (complex) scalars; returns a flat ``list[complex]``. Each
    entry ``z = a + bi`` runs:

    * ``exp(z)`` = :func:`rational.complex_exp` (``e^a (cos b + i sin b)``);
    * ``cos(z)`` = ``cos a · cosh b − i · sin a · sinh b``;
    * ``sin(z)`` = ``sin a · cosh b + i · cos a · sinh b``  (``cosh``/``sinh``
      built from ``rational.exp``: ``cosh b = (e^b + e^{-b})/2`` etc.);
    * ``log(z)`` = ``log|z| + i·arg z`` = ``rational.log(rational.hypot(a, b))
      + i·rational.atan2(b, a)`` (principal branch; ``z ≠ 0``).
    """
    out = []
    for elem in flat:
        z = complex(elem)
        a, b = z.real, z.imag
        if op_name == "exp":
            out.append(_rcomplex_exp(z))
        elif op_name == "log":
            mag = _rhypot(a, b)
            if mag <= 0.0:
                raise ValueError("log requires arr[i] != 0")
            out.append(complex(_rlog(mag), _ratan2(b, a)))
        else:
            eb = _rexp(b)
            enb = _rexp(-b)
            cosh_b = (eb + enb) / 2.0
            sinh_b = (eb - enb) / 2.0
            ca, sa = _rcos(a), _rsin(a)
            if op_name == "cos":
                out.append(complex(ca * cosh_b, -(sa * sinh_b)))
            else:  # sin
                out.append(complex(sa * cosh_b, ca * sinh_b))
    return out


def _flat_has_complex(flat) -> bool:
    """True iff any scalar in the flat sequence is a complex with nonzero imag."""
    for x in flat:
        if isinstance(x, complex) and x.imag != 0.0:
            return True
    return False


def elementwise_transcendental(arr, op_name: str):
    """Array-vectorised transcendental operation — SHAPE-POLYMORPHIC (rc129).

    Parameters
    ----------
    arr
        Real or complex input — a :class:`Mat` / 2-D nested sequence, or a
        :class:`Vec` / 1-D flat sequence.
    op_name
        One of ``"exp"``, ``"cos"``, ``"sin"``, ``"log"``, ``"exp_i"``.
        ``"exp_i"`` returns ``exp(1j * arr)`` (the TDSE-relevant complex
        exponential of a real argument); implemented via ``cos`` + ``sin``.

    Returns
    -------
    out
        Rank-preserving (rc129): a :class:`~srmech.amsc.mat.Mat` for a 2-D
        input, a :class:`~srmech.amsc.vec.Vec` for a 1-D input (NOT a bare
        list). Complex carrier for ``"exp_i"`` (or complex input), real
        otherwise.

    Numpy-free: the native ``srmech_elementwise_transcendental`` path marshals
    the flat list into a ctypes ``(c_double * n)`` buffer (numpy-free); the
    no-native / complex paths run the Class-N rational cascades per element.

    Canonical SSoT: ANSI C99 §7.12 libm.
    """
    is_mat = _ew_is_matrix(arr)
    shape = _ew_mat_shape(arr) if is_mat else None
    flat = _flatten_scalars(arr)
    if op_name == "exp_i":
        real_flat = [float(x.real if isinstance(x, complex) else x) for x in flat]
        n = len(real_flat)
        if n == 0:
            return _ew_pack([], matrix=is_mat, shape=shape, is_complex=True)
        ok_c, cos_out, _ = _real_transcendental_native(
            real_flat, _native.SRMECH_TRANS_COS
        )
        ok_s, sin_out, _ = _real_transcendental_native(
            real_flat, _native.SRMECH_TRANS_SIN
        )
        if not (ok_c and ok_s and cos_out is not None and sin_out is not None):
            # numpy-free Class-N cos/sin cascade (the no-native / Pyodide path)
            cos_out = _real_transcendental_loop(real_flat, "cos")
            sin_out = _real_transcendental_loop(real_flat, "sin")
        flat_out = [complex(cos_out[i], sin_out[i]) for i in range(n)]
        return _ew_pack(flat_out, matrix=is_mat, shape=shape, is_complex=True)
    if op_name not in _TRANS_OP_IDS:
        raise ValueError(
            f"unknown op_name {op_name!r}; legal: "
            f"{sorted(set(_TRANS_OP_IDS) | {'exp_i'})}"
        )
    # Complex inputs run the numpy-free per-element Class-N complex cascades.
    if _flat_has_complex(flat):
        flat_out = _complex_transcendental_loop(flat, op_name)
        return _ew_pack(flat_out, matrix=is_mat, shape=shape, is_complex=True)
    real_flat = [float(x.real if isinstance(x, complex) else x) for x in flat]
    n = len(real_flat)
    if n == 0:
        return _ew_pack([], matrix=is_mat, shape=shape, is_complex=False)
    op_id = _TRANS_OP_IDS[op_name]
    ok, out, rc = _real_transcendental_native(real_flat, op_id)
    if ok:
        if out is not None:
            return _ew_pack(out, matrix=is_mat, shape=shape, is_complex=False)
        if rc == _native.SRMECH_ERR_BAD_INPUT and op_name == "log":
            raise ValueError("log requires all arr[i] > 0")
    # numpy-free Class-N scalar cascade (the no-native / Pyodide path). The
    # log domain check (all arr[i] > 0, parity with the C BAD_INPUT contract)
    # lives inside _real_transcendental_loop.
    flat_out = _real_transcendental_loop(real_flat, op_name)
    return _ew_pack(flat_out, matrix=is_mat, shape=shape, is_complex=False)


def elementwise_hypot(a, b):
    """Array Euclidean magnitude ``√(aᵢ² + bᵢ²)`` via the Class-N hypot cascade —
    SHAPE-POLYMORPHIC (rc129).

    The numpy-free magnitude op the DSP modules' ``|z| = √(re² + im²)`` sites
    route through. Each element runs :func:`srmech.amsc.rational.hypot` (Class M
    sum-of-squares ∘ Class N∘K :func:`~srmech.amsc.rational.sqrt`; native
    ``srmech_rational_sqrt``-dispatched) — the math is the libm-free cascade.

    Round-off-faithful to numpy's hypot (the rational sqrt is floor-projected vs
    IEEE round-to-nearest — a ≤1-ULP shift, accepted per the cascades-replace-
    numpy-math discipline; bit-exact whenever ``aᵢ² + bᵢ²`` is a perfect square).

    Parameters
    ----------
    a, b
        Equal-length real inputs (typically ``z.real`` / ``z.imag``) — a
        :class:`Mat` / 2-D nested, or a :class:`Vec` / 1-D flat sequence.

    Returns
    -------
    out
        Rank-preserving (rc129): a real :class:`~srmech.amsc.mat.Mat` for a 2-D
        ``a``, a real :class:`~srmech.amsc.vec.Vec` for a 1-D ``a`` — ``√(aᵢ² +
        bᵢ²)`` (NOT a bare ``list[float]``). The shape is read off ``a``.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1 (Euclidean length).
    """
    is_mat = _ew_is_matrix(a)
    shape = _ew_mat_shape(a) if is_mat else None
    flat_a = _flatten_scalars(a)
    flat_b = _flatten_scalars(b)
    if len(flat_a) != len(flat_b):
        raise ValueError(
            f"elementwise_hypot: length mismatch {len(flat_a)} vs {len(flat_b)}"
        )
    flat = [_rhypot(float(ai), float(bi)) for ai, bi in zip(flat_a, flat_b)]
    return _ew_pack(flat, matrix=is_mat, shape=shape, is_complex=False)


def elementwise_sqrt(arr):
    """Array element-wise ``√arrᵢ`` via the Class-N rational sqrt cascade —
    SHAPE-POLYMORPHIC (rc129).

    The numpy-free square-root op for non-negative real arrays — the companion
    to :func:`elementwise_hypot`. Each element runs
    :func:`srmech.amsc.rational.sqrt` (Class-N∘K integer-``isqrt`` cascade;
    native ``srmech_rational_sqrt``-dispatched) — the math is the libm-free cascade.

    Round-off-faithful to numpy's sqrt (the rational sqrt is floor-projected vs
    IEEE round-to-nearest — a ≤1-ULP shift, accepted per the cascades-replace-
    numpy-math discipline; bit-exact whenever ``arrᵢ`` is a perfect square).

    Parameters
    ----------
    arr
        Real input with all entries ``>= 0`` (square-root domain) — a
        :class:`Mat` / 2-D nested, or a :class:`Vec` / 1-D flat sequence.

    Returns
    -------
    out
        Rank-preserving (rc129): a real :class:`~srmech.amsc.mat.Mat` for a 2-D
        input, a real :class:`~srmech.amsc.vec.Vec` for a 1-D input — ``√arrᵢ``
        (NOT a bare ``list[float]``).

    Raises
    ------
    ValueError
        If any ``arrᵢ < 0`` (matches the C path's domain contract).

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §1.1.
    """
    is_mat = _ew_is_matrix(arr)
    shape = _ew_mat_shape(arr) if is_mat else None
    flat = [float(x) for x in _flatten_scalars(arr)]
    if flat and min(flat) < 0.0:
        raise ValueError("elementwise_sqrt requires all arr[i] >= 0")
    out = [_rsqrt(x) for x in flat]
    return _ew_pack(out, matrix=is_mat, shape=shape, is_complex=False)


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
    edges_u: Sequence[int],
    edges_v: Sequence[int],
    weights: Sequence[float],
) -> List[List[float]]:
    """Build the dense ``n×n`` **directed** adjacency ``W[u, v] += w`` as a nested
    ``list[list[float]]`` — numpy-free.

    Unlike the undirected build this does NOT mirror the transpose — direction is
    preserved (``W`` is generally asymmetric).
    """
    W = [[0.0] * n for _ in range(n)]
    for u, v, w in zip(edges_u, edges_v, weights):
        W[int(u)][int(v)] += float(w)
    return W


def signed_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> "Mat":
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

    Returns an ``n×n`` real-symmetric :class:`~srmech.amsc.mat.Mat` (rc129;
    ``.shape`` + ``m[i, j]``, NOT a bare ``list[list[float]]``); pair with
    :func:`symmetric_eigendecompose` or :func:`fiedler_vector` for the
    signed navigation embedding.
    """
    _validate_edges_weights_py(n, edges, weights)  # validate (raises on bad input)
    A = _dense_adjacency_py(n, edges, weights)  # symmetric, signed (list[list])
    L = [[0.0] * n for _ in range(n)]
    deg = [0.0] * n
    for r in range(n):
        for c in range(n):
            if c == r:
                continue
            a = A[r][c]
            # Class-K magnitude of the signed coupling → the signed degree.
            # EXPLICIT sign-branch (pin-slot + re-orientation), NOT an ALU abs():
            # |a| = a where a >= 0 else -a. (Honours "abs() is never fine".)
            deg[r] += a if a >= 0.0 else -a
            L[r][c] = -a
    for r in range(n):
        L[r][r] = deg[r]
    return Mat.from_rows(L, is_complex=False)


def magnetic_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    q: float = 0.25,
) -> "Mat":
    """Magnetic (Hermitian) Laplacian of a **directed** graph.

    Direction is encoded as a complex phase so the result stays
    **Hermitian** and the existing :func:`hermitian_eigendecompose`
    diagonalises it — the complex eigenpair is the
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

    Numpy-free (rc129): the ``2π`` is stdlib ``math.pi`` (not ``np.pi``); the
    per-element phase ``exp(i·2π·q·Θ)`` is the libm-free Class-N
    ``cos``/``sin`` cascade. Returns an ``n×n`` Hermitian complex
    :class:`~srmech.amsc.mat.Mat` (``.shape`` + ``m[i, j]``, NOT a bare
    ``list[list[complex]]``).
    """
    if not isinstance(q, (int, float)):
        raise TypeError(f"q must be a real number; got {type(q).__name__}")
    el, wl = _validate_edges_weights_py(n, edges, weights)
    W = _directed_adjacency(n, [u for u, _ in el], [v for _, v in el], wl)
    A_s = [[0.5 * (W[r][c] + W[c][r]) for c in range(n)] for r in range(n)]
    # phase[r][c] = exp(i·2π·q·(W[r][c] − W[c][r])); 2π via stdlib math.pi.
    two_pi_q = 2.0 * _PI * float(q)
    L = [[0j] * n for _ in range(n)]
    deg = [0.0] * n
    for r in range(n):
        for c in range(n):
            deg[r] += A_s[r][c]
            if c == r:
                continue  # no self-phase; degree carries the diagonal
            ang = two_pi_q * (W[r][c] - W[c][r])
            phase = complex(_rcos(ang), _rsin(ang))
            L[r][c] = -(A_s[r][c] * phase)
    for r in range(n):
        L[r][r] = complex(deg[r])
    # Always complex layout (a Hermitian Laplacian is genuinely complex even
    # when q=0 collapses the imaginary part — pin the carrier dtype explicitly).
    return Mat.from_rows(L, is_complex=True)


def fiedler_vector(matrix) -> "Vec":
    """The Fiedler navigation embedding — eigenvector of ``λ₂``.

    Returns the eigenvector of the **second-smallest** eigenvalue of a
    Laplacian (real-symmetric *or* complex-Hermitian): the algebraic-
    connectivity / Fiedler vector that embeds the graph for navigation
    (F348). Dispatches to :func:`hermitian_eigendecompose` for complex
    input (e.g. a :func:`magnetic_laplacian`) and
    :func:`symmetric_eigendecompose` for real input (e.g.
    :func:`signed_laplacian` / :func:`dense_laplacian`).

    Numpy-free (rc129): returns the λ₂ eigenvector as a 1-D
    :class:`~srmech.amsc.vec.Vec` (``.shape == (n,)`` + scalar ``v[i]``;
    ``complex`` carrier for a Hermitian input, ``float`` for a real one), NOT a
    bare ``list``. For ``n < 2`` there is no second eigenvector; raises
    ``ValueError``.
    """
    rows = _as_rows(matrix)
    n = len(rows)
    if n < 2:
        raise ValueError("fiedler_vector requires n >= 2")
    if _has_complex(rows):
        _eigvals, V = hermitian_eigendecompose(rows)  # V complex Mat
        is_cx = True
    else:
        _eigvals, V = symmetric_eigendecompose(rows)  # V real Mat
        is_cx = False
    # Eigenvalues are ascending; column 0 is the trivial λ₁≈0, column 1
    # is the Fiedler vector (λ₂).
    return Vec.from_sequence(
        [V[i, 1] for i in range(V.n_rows)], is_complex=is_cx
    )


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
    dispatch. Numpy-free (rc129): a block may be a :class:`~srmech.amsc.mat.Mat`,
    a ``list[list[float]]`` (numpy-absent) or an ``ndarray``; per-block
    eigenvalues are returned as a 1-D :class:`~srmech.amsc.vec.Vec` (``.shape ==
    (n_i,)``), the combined spectrum as a single ``Vec`` — NOT bare lists.

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
        "blocks": [Vec(eigvals_0), ...], "combined": Vec(sorted spectrum) |
        None}`` — each eigenvalue collection a 1-D ``Vec`` (rc129).

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

    def _eig(blk) -> "Vec":
        ev = jacobi_eigvals(blk, max_sweeps=max_sweeps, tolerance=tolerance)
        # jacobi_eigvals returns a Vec (rc129); keep it as the per-block carrier.
        return ev if isinstance(ev, Vec) else Vec.from_sequence(
            list(ev.tolist()) if hasattr(ev, "tolist") else list(ev),
            is_complex=False,
        )

    # The F233 4-rung: each block on its own thread (0 cross-thread reads, so
    # parallel == serial bit-for-bit).
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=SPECTRAL_BLOCK_CAP) as ex:
        per_block = list(ex.map(_eig, blist))

    combined: "Optional[Vec]" = None
    if combine:
        merged = [float(x) for ev in per_block for x in ev]  # Vec iterates scalars
        merged.sort()
        combined = Vec.from_sequence(merged, is_complex=False)
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
    "mat_eigvals",
    "mat_svd",
    "mat_norm",
    "mat_dot_real",
    "mat_dot_complex",
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
