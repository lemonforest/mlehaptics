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
- :func:`mat_matvec` — dtype-polymorphic ``M·v`` over the Mat/Vec carriers.
- :func:`mat_dot` — dtype-polymorphic bilinear inner product ``Σ aᵢbᵢ``.
- :func:`mat_outer` — dtype-polymorphic rank-1 outer product ``aᵢbⱼ``.
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
- :func:`mat_matvec` — dtype-polymorphic matrix-vector multiplication.
- :func:`elementwise_multiply_complex` — pointwise complex multiply.
- :func:`elementwise_transcendental` — vectorised transcendentals.

The module-level :data:`LAPLACIAN_OPS` constant exposes all available
op names for the composition-engine registry.

C-path bound
------------

Most of the C native surface operates on ``n ≤ MAX_NATIVE_NODES`` (256),
which caps the stack-allocated / static degree / row-scaling / augmented
buffers (embedded-safe). When ``HAS_NATIVE`` and ``n ≤ 256`` the dense build
+ ``jacobi_eigvals`` + ``dense_solve`` + ``mat_matvec``/``mat_matmul`` dispatch
to the C symbol **with or without numpy** — the numpy-absent path marshals a
flat ctypes buffer straight from Python ``list``s (UPSTREAM §38; ``jacobi``
~49× faster than the pure-Python cascade). For ``n > 256`` (or no native lib)
srmech's own pure-Python Class-L cascades run.

The numpy-free Hermitian eigen**vector** decomposition
(:func:`mat_hermitian_eigendecompose`) is the one path with a HIGHER native
bound — a **config-driven** sanity ceiling (default 2048, raisable via
``_native.config_load_toml``/``_file``; rc161). It routes through the
reentrant ``srmech_hermitian_eigendecompose_ws`` C entry, which takes a
caller-supplied ``2*n*n``-double workspace (allocated as a ctypes buffer here)
and so has NO 256-sized static/stack array — only that config ceiling. This keeps the
fast native Jacobi (not the minutes-long pure-Python fallback) reachable for
QM grid sizes (e.g. a hydrogen radial grid up to ~1000). Eigenvector sign /
degenerate-subspace rotation is non-unique, so element-wise C/Python parity is
not meaningful (correctness is pinned by eigenvalues + reconstruction +
orthonormality).
"""

from __future__ import annotations

import ctypes
import os  # §52 Part 2: disk-backed work queue + tome files for the out-of-core driver
import struct  # §52 Part 2: pack/unpack the on-disk edge records for the out-of-core Fiedler
import tempfile  # §52 Part 2: default scratch dir for recursive_cut
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


# 0.9.0rc7 (stay-rational, F868): ``rational.sqrt`` / ``rational.hypot`` now
# return an exact :class:`~srmech.amsc.q.Q`. That is right for EXACT contexts,
# but the iterative dense-linear-algebra kernels below — the Jacobi eigen-sweep,
# Householder QR, the Gram-SVD, the Fiedler power-iteration, the complex √ — are
# genuinely **FPU float algorithms**: their rotations are irrational and they
# converge by float round-off, so a ``Q`` carried through a sweep grows the
# num/den unboundedly each iteration (the sweep never terminates in finite
# rational arithmetic). The root is therefore a **float subroutine** here — it
# rotates to float at the call boundary (``[[user_stance_alu_all_the_way_fpu_last_mile]]``:
# this IS that boundary, the iterative kernel lives on the FPU). The exact-``Q``
# root is the one the EXACT consumers call directly; ``_fsqrt`` / ``_fhypot`` are
# the float PROJECTION of it, used only inside these float kernels.
def _fsqrt(x) -> float:
    """``float(rational.sqrt(x))`` — the float projection for the FPU kernels.

    libm-faithful on the FULL float domain these iterative sweeps reach: rc7's
    stay-rational ``rational.sqrt`` RAISES on a non-finite ``x`` (a ``Q`` cannot
    be ±inf / nan), but a Jacobi / QR rotation legitimately forms
    ``1.0 + tau*tau == inf`` for a huge rotation ratio, where ``sqrt(inf) = inf``
    yields the correct degenerate angle (``t = -1/(-tau + inf) = -0``). So mirror
    ``math.sqrt`` at the edges (``sqrt(+inf)=+inf``, ``sqrt(nan)=nan``); every
    FINITE non-negative ``x`` still routes the exact Class-N cascade."""
    x = float(x)
    if x != x:                          # nan → nan
        return x
    if x == float("inf"):               # sqrt(+inf) = +inf (libm-faithful)
        return x
    if x == float("-inf"):              # outside domain → nan sentinel (no kernel hits this)
        return float("nan")
    return float(_rsqrt(x))


def _fhypot(a, b) -> float:
    """``float(rational.hypot(a, b))`` — the float projection for the FPU kernels.

    libm-faithful at the non-finite edges the sweeps reach (``hypot(inf, ·)=inf``,
    ``hypot(nan, ·)=nan``); every finite pair routes the exact Class-N cascade."""
    fa = float(a)
    fb = float(b)
    if fa != fa or fb != fb:            # nan in → nan
        return float("nan")
    if fa in (float("inf"), float("-inf")) or fb in (float("inf"), float("-inf")):
        return float("inf")            # hypot(inf, ·) = inf (libm-faithful)
    return float(_rhypot(fa, fb))


# §564/rc13: numpy-free AND math-free π — 4·atan(1) via the Class-N atan
# cascade (c_dispatched; NO stdlib math.pi, NO np.pi), projected to float once
# at import (the ×4 is an exact power of two, so 4·atan(1) == math.pi bit-for-bit).
from srmech.amsc.rational import atan as _atan_pi
_PI = 4.0 * float(_atan_pi(1.0))

from .mat import Mat  # §564: the numpy-free 2-D carrier the mat_* engine returns
from .vec import Vec  # rc129: the numpy-free 1-D carrier (vectors / eigenvalues)

from . import _native

__all__ = [
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "jacobi_eigvals",
    "fiedler_sparse",
    "normalized_cut_bisect",
    "write_packed_graph",
    "fiedler_sparse_file",
    "recursive_cut",
    "spectral_block_dispatch",
    "dense_solve",
    "schur_complement",
    "dirichlet_to_neumann",
    "hermitian_eigendecompose",
    "symmetric_eigendecompose",
    "mat_matmul",
    "mat_solve",
    "mat_hermitian_eigendecompose",
    "mat_lstsq",
    "mat_eigvals",
    "mat_svd",
    "mat_norm",
    "mat_dot",
    "mat_matvec",
    "mat_outer",
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

# Hermitian-eig-only native bound — the built-in DEFAULT, not a hard cap.
# The reentrant C entry ``srmech_hermitian_eigendecompose_ws`` takes a
# CALLER-SUPPLIED 2*n*n-double workspace (allocated here as a ctypes buffer),
# so its native Jacobi path has NO 256-sized stack/static array. As of rc161
# the native sanity ceiling is CONFIG-DRIVEN (C ``srmech_config_hermitian_max_nodes()``,
# default 2048, raisable via ``_native.config_load_toml``/``_file``); the live
# dispatch gate in :func:`mat_hermitian_eigendecompose` reads that getter, so a
# raised config lifts the gate in lockstep. This constant mirrors the C
# *default* (``SRMECH_HERMITIAN_DEFAULT_MAX_NODES``) for documentation / no-native
# environments; it is NO LONGER the gate. Every OTHER native path in this module
# (jacobi_eigvals, dense_solve, mat_matvec/mat_matmul) still relies on a
# 256-sized fixed buffer and stays gated by ``MAX_NATIVE_NODES`` = 256.
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
    # No node cap (standalone-honor rc157): the C graph ops write only into
    # the caller's matrix (degree per-row / d^(−1/2) stashed in the diagonal /
    # Jacobi rotates in place), so the bound is the caller's RAM, not 256.
    # Native is authoritative when present; the pure-Python path is the
    # complete alternative for a no-C environment.
    return _native.HAS_NATIVE and _native.LIB is not None


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
    d_inv_sqrt = [(1.0 / _fsqrt(d)) if d > 0 else 0.0 for d in deg]
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
        off = _fsqrt(
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
                    t = 1.0 / (tau + _fsqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + _fsqrt(1.0 + tau * tau))
                c = 1.0 / _fsqrt(1.0 + t * t)
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
        off = _fsqrt(
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
                    t = 1.0 / (tau + _fsqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + _fsqrt(1.0 + tau * tau))
                c = 1.0 / _fsqrt(1.0 + t * t)
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


def _is_exact_scalar(x) -> bool:
    """True iff ``x`` is an EXACT scalar — a plain ``int`` (not ``bool``) or a
    :class:`numbers.Rational` (covers :class:`fractions.Fraction` and the srmech
    ``Q`` carrier, both registered as ``numbers.Rational``). A ``float`` /
    ``complex`` / ``bool`` is NOT exact (``bool`` is excluded so a truthy entry
    can't masquerade as the integer 1)."""
    import numbers
    if isinstance(x, bool):
        return False
    if isinstance(x, int):
        return True
    return isinstance(x, numbers.Rational)


def _jacobi_eigvals_exact(matrix) -> "Vec":
    """Exact-substrate symmetric eigenvalues (rc-B; the ``exact=True`` route of
    :func:`jacobi_eigvals`).

    Validates ``matrix`` is SQUARE, **exact** (every entry an ``int`` /
    :class:`fractions.Fraction` / srmech ``Q``), and SYMMETRIC, then routes to
    the exact-substrate cascade :func:`srmech.amsc.cascade.matrix_cascades.eigvals_exact`
    (lazily imported here to avoid any circular-import risk). Returns the
    ascending eigenvalues **with multiplicity** as a 1-D :class:`Vec` — the same
    return contract as the float-Jacobi path.

    Raises :class:`ValueError` on a non-square / float-bearing / non-symmetric
    input: exact eigenvalues are only achievable for an integer/rational
    SYMMETRIC matrix (a non-symmetric integer matrix can have complex
    eigenvalues that the real-root ``eigvals_exact`` returns incompletely)."""
    rows = [list(r) for r in matrix]
    n = len(rows)
    if n == 0 or any(len(r) != n for r in rows):
        raise ValueError(
            "jacobi_eigvals(exact=True) requires a square n×n matrix; "
            f"got row lengths {[len(r) for r in rows]} for n={n}"
        )
    for i in range(n):
        for j in range(n):
            if not _is_exact_scalar(rows[i][j]):
                raise ValueError(
                    "jacobi_eigvals(exact=True) requires every entry to be "
                    "EXACT (int / fractions.Fraction / srmech Q) — never a "
                    f"float/complex; entry [{i}][{j}] = {rows[i][j]!r} is "
                    f"{type(rows[i][j]).__name__}. Exact eigenvalues are only "
                    "achievable on an exact substrate."
                )
    for i in range(n):
        for j in range(i + 1, n):
            if rows[i][j] != rows[j][i]:
                raise ValueError(
                    "jacobi_eigvals(exact=True) requires a SYMMETRIC matrix "
                    f"(a[i][j] == a[j][i]); entry [{i}][{j}] = {rows[i][j]!r} "
                    f"!= [{j}][{i}] = {rows[j][i]!r}. A non-symmetric integer "
                    "matrix can have complex eigenvalues that the real-root "
                    "eigvals_exact returns incompletely."
                )
    # Lazy import (avoid a circular-import risk at module load).
    from srmech.amsc.cascade.matrix_cascades import eigvals_exact
    eigs = eigvals_exact(rows)  # ascending, with multiplicity (real spectrum)
    return Vec.from_sequence(eigs, is_complex=False)


def jacobi_eigvals(
    matrix,
    max_sweeps: int = 100,
    tolerance: float = 1e-12,
    *,
    exact: bool = False,
) -> "Vec":
    """Symmetric Jacobi eigendecomposition.

    Returns the sorted (ascending) eigenvalues of a real symmetric matrix.
    The C path uses an in-place algebraic Jacobi rotation (pi-free) and has
    **no node cap** (standalone-honor rc157) — it rotates the caller's matrix
    in place, so the bound is the caller's RAM. When there is no native lib the
    fallback is **srmech's own pure-Python Jacobi cascade**
    (:func:`_jacobi_eigvals_py`) — NOT ``numpy.linalg.eigvalsh``: when srmech
    can do the math with its own cascade, it does (so the Class-L spectrum runs
    without LAPACK/numpy, UPSTREAM §22). Input is a ``list[list[float]]`` /
    ``Mat``; return is a ``Vec``.

    numpy-absent dispatch (UPSTREAM §38 / F708): the bound ``srmech_jacobi_eigvals``
    C symbol IS reachable without numpy — when ``HAS_NATIVE`` the numpy-free
    path marshals the ``list[list[float]]`` into a flat ctypes ``double`` buffer
    and calls it (native-authoritative), falling back to the pure-Python cascade
    only when there is no native lib or the C status is non-OK.

    ``matrix`` is **not** modified by the wrapper — the native path marshals into
    a fresh ctypes buffer; the pure-Python cascade copies its rows.

    Numpy-free (rc129): the input is a :class:`~srmech.amsc.mat.Mat` /
    ``list[list[float]]`` (or any nested sequence) and the return is a 1-D
    :class:`~srmech.amsc.vec.Vec` of the ascending eigenvalues (``.shape == (n,)``
    + scalar ``v[i]``), NOT a bare ``list[float]``. When ``HAS_NATIVE`` and
    ``n ≤ 256`` the numpy-free list-marshal native path runs; else srmech's own
    pure-Python Jacobi cascade.

    Rotation-last exact route (rc-B, ``exact=``, keyword-only)
    ---------------------------------------------------------
    * ``exact=False`` (the default): **unchanged** — the float-Jacobi path
      above, verbatim. Float-Jacobi stays the default speed path (the
      iterative FPU last-mile, classified PRIMITIVE_NA in the rotation-last
      audit — an intrinsic-float limit, NOT an avoidable violation).
    * ``exact=True``: route to the exact-substrate cascade. The matrix is
      validated SQUARE, **exact** (every entry an ``int`` /
      :class:`fractions.Fraction` / srmech ``Q`` — never a ``float`` /
      ``complex``), and SYMMETRIC (``a[i][j] == a[j][i]``); any failure
      raises :class:`ValueError`. (Exact eigenvalues are only achievable for
      an integer/rational SYMMETRIC matrix: a non-symmetric integer matrix
      can have complex eigenvalues that the real-root ``eigvals_exact``
      returns incompletely.) The spectrum then stays exact — char-poly
      Faddeev–LeVerrier → Yun square-free → Sturm isolation → ``Fraction``
      bisection — until the single terminal float lift (the rotation-last
      "exact-substrate-achievable" case). The return is the same contract as
      the float path: a 1-D :class:`~srmech.amsc.vec.Vec` of ``n`` ascending
      eigenvalues, **with multiplicity**.
    """
    if exact:
        return _jacobi_eigvals_exact(matrix)
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
    ``list[Fraction]`` for a vector RHS) — the exact path keeps the rational
    leaves. With ``exact=False`` (the default) the float realization rides the
    numpy-free Mat engine (:func:`mat_solve` — native ``srmech_dense_solve_f64_ws``
    Gauss–Jordan with partial pivoting, the Class-K magnitude pivot — a sign
    branch, not ``abs()``; else srmech's own exact Fraction fallback coerced to
    float). The float ``X`` is returned in the numpy-free **carrier** (rc131):
    a :class:`~srmech.amsc.mat.Mat` for a matrix RHS (``.shape`` + ``m[i, j]``)
    or a 1-D :class:`~srmech.amsc.vec.Vec` for a vector RHS (``.shape == (n,)``
    + scalar ``v[i]``), NOT a bare ``list`` — a list has no honest C
    representation, a Mat/Vec is a contiguous double buffer. A complex system
    rides the real 2n×2n block embedding inside :func:`mat_solve`, so the carrier
    comes back complex.

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
    # rc131 carrier-format law: return the numpy-free Vec (vector RHS) / Mat
    # (matrix RHS), NOT a bare list — a Mat/Vec IS a C dense buffer, a list is not.
    if is_vec:
        return Vec.from_sequence([r[0] for r in rows_out], is_complex=cx)
    return Mat.from_rows(rows_out, is_complex=cx)


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
    (conjugate) → Class K (``1/‖·‖²``); no ``abs()``. With ``exact=True`` the
    solve is **exact-rational** Gauss–Jordan elimination in
    :class:`fractions.Fraction` (the Class-N rational core — division is exact,
    never a float reciprocal) and ``S`` is returned as ``list[list[Fraction]]``.
    With ``exact=False`` (the default) the float realization rides the numpy-free
    Mat engine (:func:`dense_solve` → :func:`mat_solve`) and ``S`` is returned in
    the numpy-free **carrier** — a ``|∂|×|∂|`` :class:`~srmech.amsc.mat.Mat`
    (rc131; ``.shape`` + ``m[i, j]``), NOT a bare ``list`` (a Mat IS a C dense
    buffer, a list is not). Canonical SSoT: Zhang, *The Schur Complement and Its
    Applications* (2005) §0; the DtN map is textbook (Golub & Van Loan §3.2).

    Parameters
    ----------
    L : matrix, ``n×n``
        A :class:`~srmech.amsc.mat.Mat` or ``list[list]`` — a symmetric
        positive-semidefinite operator (a graph Laplacian from
        :func:`dense_laplacian`, or any SPD matrix).
    boundary_idx : sequence[int]
        The boundary node indices ``∂``; ``1 ≤ |∂| ≤ n``, no duplicates.
    exact : bool, default ``False``
        Force the exact-rational :class:`~fractions.Fraction` solve (returns
        ``list[list[Fraction]]``).

    Returns
    -------
    S : ``|∂|×|∂|`` boundary effective operator
        a real :class:`~srmech.amsc.mat.Mat` (float path) or
        ``list[list[Fraction]]`` (exact path).

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
        return Mat.from_rows([[float(v) for v in r] for r in L_pp], is_complex=False)

    L_pi = _block(b, i)  # L_∂i
    L_ip = _block(i, b)  # L_i∂
    L_ii = _block(i, i)  # L_ii

    if exact:
        # Interior solve L_ii · X = L_i∂ (X is |i|×|∂|) via the Class-L
        # dense_solve primitive — exact-rational Gauss–Jordan (Class-N).
        X = dense_solve(L_ii, L_ip, exact=True)  # list[list[Fraction]]
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
    # the numpy-free Mat-engine dense_solve (returns a Mat — rc131 carrier law);
    # the cheap boundary matmul + subtract is a pure-Python list loop reading the
    # Mat via X[k, c]:  S[a][c] = L_∂∂[a][c] − Σ_k L_∂i[a][k] · X[k][c].
    X = dense_solve(L_ii, L_ip)  # |i|×|∂| Mat
    S = [
        [
            float(L_pp[a][c])
            - sum(float(L_pi[a][k]) * X[k, c] for k in range(len(i)))
            for c in range(len(b))
        ]
        for a in range(len(b))
    ]
    # rc131 carrier-format law: the float boundary operator returns as a Mat.
    return Mat.from_rows(S, is_complex=False)


def dirichlet_to_neumann(L, boundary_idx: Sequence[int], *, exact: bool = False):
    """Alias for :func:`schur_complement` — the discrete Dirichlet-to-Neumann
    (DtN) map ``S = L_∂∂ − L_∂i · L_ii⁻¹ · L_i∂`` (UPSTREAM §26; #897). Given
    boundary values, ``S`` returns the boundary normal-derivative of their
    harmonic extension into the interior. Returns the same carrier as
    :func:`schur_complement`: a real :class:`~srmech.amsc.mat.Mat` (float path)
    or ``list[list[Fraction]]`` (``exact=True``)."""
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
    # Native zero-copy path (nonzero dims): Mat buffer → C kernel → Mat. No node
    # cap (standalone-honor rc157) — the C kernel writes only the caller's output
    # buffer, so the bound is the caller's RAM; native is authoritative here.
    if (m and k and n
            and _native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_dense_matmul_complex")):
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
    the native ``srmech_dense_solve_f64_ws`` reads, so both operands feed the
    kernel **zero-copy** (``from_buffer``) with **NO numpy** (the C side takes
    them ``const``, so the `Mat`\\ s are not mutated); the output is a fresh
    ``array('d')`` wrapped back into a `Mat`. There is **no size cap** (rc158
    standalone-complete honor): the augmented ``[A|B]`` scratch is carved from a
    caller arena sized per call via ``srmech_dense_solve_arena_bytes``, so the
    bound is the caller's RAM. Native is authoritative when present (a singular
    ``A`` → ``SRMECH_ERR_BAD_INPUT`` → ``ZeroDivisionError``); with **no native
    lib** the complete alternative is srmech's own **exact-rational Gauss–Jordan**
    (:func:`_solve_exact`, Class-N ``Fraction`` division, numpy-free) coerced to
    float64 — itself uncapped, so the op is unconditionally numpy-free either way.

    ``srmech_dense_solve_f64_ws`` is **real-f64 only**; a complex `Mat` (rc95)
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
    # Native zero-copy path — NO size cap (rc158 standalone-complete honor):
    # the augmented [A|B] scratch is carved from a caller arena we size per call
    # (srmech_dense_solve_arena_bytes), so the bound is this process's RAM, not a
    # compiled-in 256. Native is AUTHORITATIVE when present: the cheap shape
    # validation above raised the precise ValueErrors; a singular A surfaces as
    # SRMECH_ERR_BAD_INPUT, which we translate to the documented ZeroDivisionError
    # (the exact path raises the same — two complete impls, not one rescuing the
    # other). cf. [[feedback_c_must_be_standalone_complete_no_python_fallback]].
    if (_native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_dense_solve_f64_ws")):
        a_buf = (ctypes.c_double * (n * n)).from_buffer(a.buffer)  # zero-copy (real)
        b_buf = (ctypes.c_double * (n * w)).from_buffer(b.buffer)  # zero-copy (real)
        out = (ctypes.c_double * (n * w))()
        ws_bytes = int(_native.LIB.srmech_dense_solve_arena_bytes(
            ctypes.c_uint32(n), ctypes.c_uint32(w),
        ))
        ws_buf = (ctypes.c_char * ws_bytes)()                     # caller arena
        rc = _native.LIB.srmech_dense_solve_f64_ws(
            ctypes.c_uint32(n), ctypes.c_uint32(w), a_buf, b_buf, out,
            ctypes.cast(ws_buf, ctypes.c_void_p), ctypes.c_size_t(ws_bytes),
        )
        if rc == _native.SRMECH_OK:
            return Mat(array("d", out), n, w)
        if rc == _native.SRMECH_ERR_BAD_INPUT:
            raise ZeroDivisionError("mat_solve: A is singular (zero pivot column)")
        raise RuntimeError(f"srmech_dense_solve_f64_ws returned non-OK status {rc}")
    # No native lib (pure wheel / Pyodide): srmech's own exact-rational
    # Gauss–Jordan (Class-N) is the COMPLETE alternative implementation, not a
    # fallback rescue — it is the no-C host's only solve and is uncapped too.
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
    def _mgs(vec, ev_cur):
        """Modified Gram–Schmidt: subtract the projection of ``vec`` onto every
        already-accepted eigenvector in the SAME degenerate eigenspace."""
        for ev_prev, w_prev in cols:
            if _fsqrt((ev_cur - ev_prev) * (ev_cur - ev_prev)) <= 1e-9:
                proj = sum(w_prev[i].conjugate() * vec[i] for i in range(n))
                vec = [vec[i] - proj * w_prev[i] for i in range(n)]
        return vec

    cols: List[Tuple[float, List[complex]]] = []
    for k in range(n):
        col = 2 * k
        ev = evals2[col]
        w = _mgs([complex(V2[i][col], V2[i + n][col]) for i in range(n)], ev)
        norm2 = sum(x.real * x.real + x.imag * x.imag for x in w)
        if _fsqrt(norm2) <= 1e-12:
            # Degenerate eigenvalue: this embedding column reconstructed onto an
            # eigenvector we already accepted (the real 2n-embedding DOUBLES each
            # complex eigenvector via the J-rotation i·z, so the "every other
            # column" pick can land on a linearly-dependent direction — e.g. the
            # identity matrix, eigenvalue 1 with full multiplicity). Scan every
            # embedding column at the SAME eigenvalue for one whose reconstruction
            # survives Gram–Schmidt; the eigenspace still has more independent
            # directions than we have accepted, so one must exist.
            for j in range(m):
                if _fsqrt((evals2[j] - ev) * (evals2[j] - ev)) > 1e-9:
                    continue
                cand = _mgs([complex(V2[i][j], V2[i + n][j]) for i in range(n)], ev)
                cn2 = sum(x.real * x.real + x.imag * x.imag for x in cand)
                if _fsqrt(cn2) > 1e-12:
                    w, norm2 = cand, cn2
                    break
        inv = 1.0 / _fsqrt(norm2)
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
    here as a ctypes buffer), so the fast native Jacobi serves ``n`` up to the
    **config-driven** ceiling (``_native.config_hermitian_max_nodes()``, default
    2048, raisable; rc161) without a 256-sized static/stack buffer. With no
    native lib — or ``n`` above the configured ceiling, or a native convergence
    miss — the complete alternative is srmech's own pure-Python **cyclic Jacobi**
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
    # The native compute-guard ceiling is CONFIG-DRIVEN (rc161): default 2048,
    # raisable via ``_native.config_load_toml``/``_file``. Gate on the LIVE
    # value (``_native.config_hermitian_max_nodes()``) so a raised config lifts
    # the native gate in lockstep; above it, the complete alternative is
    # srmech's own pure-Python cyclic Jacobi (no ceiling) — NOT a smaller native
    # cap. (rc161 removed the older no-``_ws`` ``srmech_hermitian_eigendecompose``
    # — a 1 MiB thread-local static with its own n≤256 cap and no live caller.)
    if (have_native
            and hasattr(_native.LIB, "srmech_hermitian_eigendecompose_ws")
            and n <= _native.config_hermitian_max_nodes()):
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
    return _fhypot(float(z.real), float(z.imag))


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
    mod = _fhypot(a, b)                             # Class-N |w| (≥ |a| exactly)
    re_arg = (mod + a) / 2.0                        # both radicands ≥ 0
    im_arg = (mod - a) / 2.0                        # mathematically; a tiny <0 is
    re = _fsqrt(re_arg) if re_arg > 0.0 else 0.0    # float round-off → Class-K
    im = _fsqrt(im_arg) if im_arg > 0.0 else 0.0    # pin-slot at zero
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
        normx = _fsqrt(normx2)                       # Class-N ‖x‖
        x0 = R[k][k]
        modx0 = _fhypot(x0.real, x0.imag)
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
    it = 0                                            # iterations since last deflate
    sweep_ceiling = max_sweeps * n
    while m > 0:
        if m == 1:
            eigs.append(H[0][0])                      # Class-L: last eigenvalue
            break
        scale = _modulus_c(H[m - 2][m - 2]) + _modulus_c(H[m - 1][m - 1])
        if _modulus_c(H[m - 1][m - 2]) <= _MAT_EIG_DEFLATE_TOL * (scale + 1e-300):
            eigs.append(H[m - 1][m - 1])              # Class-L: deflate eigenvalue
            m -= 1
            it = 0                                    # new deflation-target: reset stall
            continue
        if m == 2:
            lam1, lam2 = _eig2x2(H[0][0], H[0][1], H[1][0], H[1][1])  # closed form
            eigs.append(lam1)
            eigs.append(lam2)
            break
        # Shift selection. The plain Wilkinson μ is the trailing-2×2 eigenvalue
        # closest to H[m-1][m-1]. BUT on a cyclic-permutation / companion block the
        # trailing 2×2 is [[0,0],[1,0]] → both roots 0 → μ=0 → an UNSHIFTED step,
        # and an equal-modulus spectrum (e.g. roots of unity) then never deflates.
        # The classic EISPACK ``hqr`` / LAPACK cure is an EXCEPTIONAL shift injected
        # on a stall: at it==10 and it==20 (the EISPACK cadence) we replace μ with an
        # ad-hoc shift built from the local sub-diagonal magnitudes, perturbing the
        # spectrum estimate enough to dislodge the equal-modulus lock. (Golub & Van
        # Loan §7.5; EISPACK ``hqr``.) ``_modulus_c`` is the Class-K magnitude — no
        # bare ``abs()`` per the cascade-honesty rule.
        if it == 10 or it == 20:
            mu = _modulus_c(H[m - 1][m - 2])          # EISPACK exceptional shift
            if m - 3 >= 0:
                mu += _modulus_c(H[m - 2][m - 3])
            mu = complex(mu, 0.0)                     # Class-C real ad-hoc shift
        else:
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
        it += 1
        if sweeps > sweep_ceiling:                    # genuine non-convergence:
            # NEVER silently return the raw diagonal of an UN-converged block — for a
            # companion matrix that diagonal is all zeros (the historic all-zero bug).
            # Raise instead so the caller sees the failure (the exact integer oracle
            # ``cascade.matrix_cascades.eigvals_exact`` is the convergent alternative).
            raise RuntimeError(
                f"mat_eigvals failed to converge in {sweeps} QR sweeps "
                f"(n={n}, remaining block m={m}); the input may be pathological "
                f"for the float shifted-QR path — use the exact integer oracle "
                f"srmech.amsc.cascade.matrix_cascades.eigvals_exact for certified roots"
            )
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
    sigma = [_fsqrt(lam[order[j]] if lam[order[j]] > 0.0 else 0.0) for j in range(n)]
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
        norm = _fsqrt(sum(x.real * x.real + x.imag * x.imag for x in cand))
        if norm > 1e-12:
            inv = 1.0 / norm
            ucols.append([x * inv for x in cand])
        e += 1

    u_rows = [[ucols[c][i] for c in range(m)] for i in range(m)]   # column c = ucols[c]
    U = Mat.from_rows(u_rows, is_complex=True)
    v_rows = [[vcols[j][i] for j in range(n)] for i in range(n)]   # V (n,n): col j = vcols[j]
    Vh = Mat.from_rows(v_rows, is_complex=True).conj().T           # Vᴴ
    return U, S, Vh


# ── Mat-carrier numpy-FREE norm + dot (#564 carrier arc; v0.7.6 consolidation) ─
#
# :func:`mat_norm`, :func:`mat_dot`, :func:`mat_matvec` and :func:`mat_outer` are
# THE numpy-free ‖x‖ / a·b / M·v / a⊗b over the :class:`Mat` / :class:`Vec` /
# :class:`HV` carriers — the qm Clifford / unitarity / η-Hermiticity residuals +
# so8 Gram-Schmidt route their norms / dots / products through them. The v0.7.6
# carrier consolidation removed the redundant loose-input ``dense_norm`` /
# ``dense_dot_*`` / ``dense_matvec_*`` / ``dense_outer_*`` generation AND the
# rc114 ``mat_dot_real`` / ``mat_dot_complex`` dtype-split: these dtype-
# polymorphic ops ARE the single carrier surface now. Pure-Python float
# sum-of-products (≈1 ULP vs the NumPy 2-norm / dot), NOT bit-exact.


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
        if isinstance(x, (list, tuple)):  # nested list = matrix rows → flatten one level
            for y in x:
                yield y
        else:
            yield x


def mat_norm(x) -> float:
    """Euclidean (vector 2-norm) / Frobenius (matrix) norm ``‖x‖ = √(Σ|xᵢ|²)`` →
    ``float`` — numpy-FREE over the Mat / Vec / HV carriers.

    Accepts a :class:`Mat` (Frobenius over all elements), an :class:`HV`, or a
    flat real/complex sequence (vector 2-norm). Sums ``|xᵢ|²`` over a pure-Python
    reduction — for complex ``z`` the squared modulus is ``z.real² + z.imag²``
    (NO ``abs()``, NO ``math.hypot``) — then takes the libm-free **Class-N**
    :func:`srmech.amsc.rational.sqrt` root. Value-faithful to the NumPy 2-norm /
    Frobenius norm to round-off (~1 ULP); empty → ``0.0``.

    **Class N** (``rational.sqrt`` root) ∘ **Class M** (the ``Σ|xᵢ|²`` self-bind).
    Canonical SSoT: Golub & Van Loan §2.3 (vector / Frobenius norms)."""
    total = 0.0
    for s in _iter_mat_scalars(x):
        if isinstance(s, complex):
            total += s.real * s.real + s.imag * s.imag
        else:
            sv = float(s)
            total += sv * sv
    return _fsqrt(total) if total > 0.0 else 0.0


def _operand_is_complex(x) -> bool:
    """True iff ``x`` carries complex scalars — reads the carrier ``is_complex``
    flag when present (Mat / Vec / HV), else scans the flat scalars. The dtype
    gate the consolidated dtype-polymorphic ``mat_*`` ops share (numpy-free)."""
    if hasattr(x, "is_complex"):
        return bool(x.is_complex)
    return any(isinstance(s, complex) for s in _iter_mat_scalars(x))


def mat_dot(a, b):
    """Dtype-polymorphic bilinear inner product ``a · b = Σ aᵢ bᵢ`` over the
    numpy-free :class:`Mat` / :class:`Vec` / :class:`HV` / flat-sequence carriers
    — **complex** when either operand is complex, else **float**. The single
    consolidated dot the carrier ``·`` idiom and the QM η-sandwiches route
    through (v0.7.6 carrier consolidation: unifies the rc114
    ``mat_dot_real`` / ``mat_dot_complex`` split **and** the superseded
    loose-input ``dense_dot_real`` / ``dense_dot_complex`` pair into one op).

    Plain **bilinear** ``Σ aᵢ bᵢ`` (matching NumPy ``a·b`` on two 1-D arrays,
    **NOT** the Hermitian ``vdot`` that conjugates its first argument — callers
    wanting the Hermitian form pass ``a.conj()`` explicitly). Pure-Python
    reduction over the flattened scalars.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook inner product)."""
    if _operand_is_complex(a) or _operand_is_complex(b):
        total = 0j
        for x, y in zip(_iter_mat_scalars(a), _iter_mat_scalars(b)):
            total += complex(x) * complex(y)
        return total
    total = 0.0
    for x, y in zip(_iter_mat_scalars(a), _iter_mat_scalars(b)):
        total += float(x) * float(y)
    return total


def mat_matvec(m, v) -> "Vec":
    """Dtype-polymorphic dense matrix-vector product ``M·v`` → :class:`Vec`
    (complex iff either operand is) over the numpy-free carriers — rides
    :func:`mat_matmul` over a column :class:`Mat` (native zero-copy when present,
    else a pure-Python triple loop). v0.7.6 carrier consolidation: unifies the
    rc129 ``dense_matvec_real`` / ``dense_matvec_complex`` pair.

    Canonical SSoT: Golub & Van Loan §1.1 (textbook matrix-vector product)."""
    M_rows = _rows(m)
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
    cplx = (getattr(m, "is_complex", False) or getattr(v, "is_complex", False)
            or any(isinstance(x, complex) for row in M_rows for x in row)
            or any(isinstance(x, complex) for x in v_list))
    if rows == 0:
        return Vec(array("d"), 0, is_complex=cplx)
    col = Mat.from_rows(
        [[(complex(x) if cplx else float(x))] for x in v_list], is_complex=cplx
    )
    out = mat_matmul(Mat.from_rows(M_rows, is_complex=cplx), col)
    if cplx:
        return Vec.from_sequence(
            [complex(out[i, 0]) for i in range(out.n_rows)], is_complex=True
        )
    return Vec.from_sequence(
        [float(out[i, 0]) for i in range(out.n_rows)], is_complex=False
    )


def mat_outer(a, b) -> "Mat":
    """Dtype-polymorphic outer product ``a ⊗ b`` → :class:`Mat` ``out[i,j]=aᵢbⱼ``
    (complex iff either operand is) over the numpy-free carriers. Plain bilinear
    ``aᵢ bⱼ`` (NO conjugation — like NumPy ``outer``; callers wanting
    ``|ψ⟩⟨ψ|`` pass ``b = ψ.conj()``). v0.7.6 carrier consolidation: unifies the
    rc129 ``dense_outer_real`` / ``dense_outer_complex`` pair.

    Canonical SSoT: Golub & Van Loan §1.1 (rank-1 outer product)."""
    a_list = _vec(a)
    b_list = _vec(b)
    cplx = (getattr(a, "is_complex", False) or getattr(b, "is_complex", False)
            or any(isinstance(x, complex) for x in a_list)
            or any(isinstance(x, complex) for x in b_list))
    if not a_list:
        return Mat(array("d"), 0, len(b_list), is_complex=cplx)
    if cplx:
        rows = [[complex(ai) * complex(bj) for bj in b_list] for ai in a_list]
        return Mat.from_rows(rows, is_complex=True)
    rows = [[float(ai) * float(bj) for bj in b_list] for ai in a_list]
    return Mat.from_rows(rows, is_complex=False)


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
            mag = _fhypot(a, b)
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
    flat = [_fhypot(float(ai), float(bi)) for ai, bi in zip(flat_a, flat_b)]
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
    out = [_fsqrt(x) for x in flat]
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
    # phase[r][c] = exp(i·2π·q·(W[r][c] − W[c][r])); 2π via the Class-N atan
    # cascade (_PI = 4·atan(1); no stdlib math.pi).
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


# --- §51 (issue #1097): the SPARSE / iterative normalized-cut Fiedler ---------
# The n-unbounded peer of the dense fiedler_vector / symmetric_eigendecompose
# path. Power iteration on the NORMALIZED operator B = I + D^-1/2 W D^-1/2
# (= 2I - L_sym; eigenvalues in [0, 2] -> well-conditioned, unlike sigma*I - L
# on a dense graph where the ratio (sigma-lambda2)/(sigma-lambda1) -> 1 and it
# fails to converge). Matvec-only -> O(edges) time + memory, n unbounded.

def _fiedler_sparse_py(
    n: int,
    edge_list: List[Tuple[int, int]],
    w_list: List[float],
    max_iters: int,
) -> List[float]:
    """Pure-Python sparse normalized-cut Fiedler (the complete no-native path).

    Transcribes the F785/F786-verified prototype: build the normalized operator
    B = I + D^-1/2 W D^-1/2 implicitly, deflate the √deg (λ₀) mode each step,
    power-iterate, stop on sign-stability. No ``abs()``: the max-magnitude
    rescale reads the Class-K magnitude-SQUARE (pin-slot-free) then takes one
    Class-N root; √deg / D^-1/2 are Class-N :func:`~srmech.amsc.rational.sqrt`.
    """
    if n < 2:
        return [0.0] * n
    nbr: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    deg = [0.0] * n
    for (a, b), w in zip(edge_list, w_list):
        nbr[a].append((b, w)); deg[a] += w
        nbr[b].append((a, w)); deg[b] += w
    s = [(1.0 / _fsqrt(deg[i])) if deg[i] > 0 else 0.0 for i in range(n)]  # D^-1/2
    p = [_fsqrt(deg[i]) if deg[i] > 0 else 0.0 for i in range(n)]          # √deg (λ₀)
    pn2 = sum(x * x for x in p)
    if pn2 <= 0:
        return [0.0] * n
    pnorm = _fsqrt(pn2)
    p = [x / pnorm for x in p]
    # Deterministic, order-independent init — a Class-I multiplicative scramble
    # keyed by node index (Knuth 2654435761), mapped to [−1, 1). NOT the parity
    # vector [1, −1, 1, …]: that is orthogonal to the Fiedler whenever the
    # community split aligns with index parity (a block-ordered regular graph),
    # so power iteration would have no Fiedler component to amplify and stall.
    # The scramble has a generic Fiedler component → it converges regardless of
    # node ordering, and is bit-identical uint32 arithmetic for the C twin.
    v = [(((k * 2654435761 + 1013904223) & 0xFFFFFFFF) / 4294967296.0) * 2.0 - 1.0
         for k in range(n)]
    dot = sum(v[i] * p[i] for i in range(n))
    v = [v[i] - dot * p[i] for i in range(n)]              # deflate λ₀
    prev_sign: Optional[Tuple[int, ...]] = None
    stable = 0
    for it in range(max_iters):
        tmp = [s[j] * v[j] for j in range(n)]
        u = [v[i] + s[i] * sum(w * tmp[j] for j, w in nbr[i]) for i in range(n)]  # u = B v
        dot = sum(u[i] * p[i] for i in range(n))
        u = [u[i] - dot * p[i] for i in range(n)]          # re-deflate λ₀
        max_sq = 0.0
        for x in u:
            xsq = x * x                                    # Class-K magnitude-square (no abs)
            if xsq > max_sq:
                max_sq = xsq
        if max_sq <= 0:
            break
        mx = _fsqrt(max_sq)                                # Class-N root -> max |u|
        v = [x / mx for x in u]
        sign = tuple(1 if x >= 0 else 0 for x in v)
        if sign == prev_sign and it >= 20:                 # stable sign (after warmup)
            stable += 1
            if stable >= 5:
                break
        else:
            stable = 0
        prev_sign = sign
    return v


def _fiedler_sparse_native(
    n: int,
    edge_list: List[Tuple[int, int]],
    w_list: List[float],
    max_iters: int,
) -> Optional[List[float]]:
    """numpy-free native dispatch for :func:`fiedler_sparse` (issue #1097).

    Marshals the edge endpoints into two ``(c_uint32 * n_edges)`` buffers + the
    weights into a ``(c_double * n_edges)`` buffer and calls the standalone-C
    ``srmech_laplacian_fiedler_sparse`` with a CALLER-allocated scratch arena
    (9·n doubles — the bound is the caller's RAM, not a compiled-in cap). The
    matvec power iteration runs in C; the sign is bit-identical to the cascade.
    Returns the length-n Fiedler vector as ``list[float]``, or ``None`` on any
    non-OK status (caller then uses the pure-Python cascade)."""
    n_edges = len(edge_list)
    eu = (ctypes.c_uint32 * n_edges)(*(int(a) for a, _ in edge_list))
    ev = (ctypes.c_uint32 * n_edges)(*(int(b) for _, b in edge_list))
    wbuf = (ctypes.c_double * n_edges)(*(float(w) for w in w_list))
    out = (ctypes.c_double * n)()
    ws = (ctypes.c_double * (9 * n))()
    rc = _native.LIB.srmech_laplacian_fiedler_sparse(
        ctypes.c_uint32(n),
        ctypes.c_uint32(n_edges),
        eu, ev, wbuf,
        ctypes.c_uint32(int(max_iters)),
        out,
        ws,
        ctypes.c_size_t(9 * n),
    )
    if rc != _native.SRMECH_OK:
        return None
    return list(out)


def fiedler_sparse(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    max_iters: int = 250,
) -> "Vec":
    """Sparse / iterative normalized-cut Fiedler vector — the ``n``-unbounded
    peer of :func:`fiedler_vector` (issue #1097 / UPSTREAM §51).

    Power iteration on the normalized operator ``B = I + D^(−1/2) W D^(−1/2)``
    (``= 2I − L_sym``; eigenvalues in ``[0, 2]`` → well-conditioned, unlike
    ``σI − L`` on a dense graph). The dominant mode is the trivial ``√deg``
    (``λ₀`` of ``L_sym``); deflating it each step leaves the **Fiedler** vector
    (``λ₂`` of ``L_sym``) as the converged direction — its **sign** is the
    normalized-cut bisection (the sign of ``D^(−1/2) u₁``, since the scaling is
    positive). Matvec-only → **O(edges)** time + memory, ``n`` unbounded; this
    breaks the ``n ≤ 256`` dense-eigensolver wall (on :func:`fiedler_vector` /
    :func:`symmetric_eigendecompose`) for corpus-scale graph partitioning
    (spectral clumping — partition a >256-node co-occurrence graph into
    community tomes; F778 → F785/F786).

    Stops early on **sign-stability** (5 consecutive identical sign-partitions
    after a 20-iteration warmup — the sign converges well before full
    eigenvector precision). Dispatches to the standalone-C
    ``srmech_laplacian_fiedler_sparse`` when ``HAS_NATIVE`` (matvec in C, no
    caps, caller-arena), else the pure-Python cascade — bit-identical sign.

    Parameters
    ----------
    n : int
        Number of graph nodes.
    edges : Iterable[Tuple[int, int]]
        Undirected edges ``(u, v)`` with ``0 ≤ u, v < n``.
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``); same length as ``edges``.
    max_iters : int
        Power-iteration cap (sign-stability usually stops earlier).

    Returns
    -------
    Vec
        The sign-bearing Fiedler vector (numpy-free 1-D carrier, ``.shape ==
        (n,)``). For ``n < 2`` the zero vector (no cut).
    """
    edge_list, w_list = _validate_edges_weights_py(n, edges, weights)
    if _native.has_native_fiedler_sparse() and n >= 2:
        vals = _fiedler_sparse_native(n, edge_list, w_list, int(max_iters))
        if vals is not None:
            return Vec.from_sequence(vals, is_complex=False)
    return Vec.from_sequence(
        _fiedler_sparse_py(n, edge_list, w_list, int(max_iters)), is_complex=False
    )


def normalized_cut_bisect(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    max_iters: int = 250,
) -> Tuple[List[int], List[int]]:
    """Sparse normalized-cut bisection — split the nodes by the sign of the
    :func:`fiedler_sparse` vector (issue #1097 / UPSTREAM §51).

    The ergonomic recursion primitive for spectral clumping: bisect, then
    recurse on each side (each sub-bisection is ``O(edges)`` and ``n``-unbounded,
    so the full-vocab partition is a longer run of the SAME proven method, never
    the dense ``n ≤ 256`` wall). Returns ``(left, right)`` node-index lists —
    ``left`` = negative-sign nodes, ``right`` = non-negative-sign nodes. A pure
    composition of :func:`fiedler_sparse` (a C-dispatched op) + a Class-K sign
    split (the cut). For a degenerate graph (``n < 2``) all nodes land in
    ``right`` (sign ≥ 0)."""
    fv = fiedler_sparse(n, edges, weights, max_iters=max_iters)
    left = [i for i in range(n) if fv[i] < 0]
    right = [i for i in range(n) if fv[i] >= 0]
    return left, right


# §52 Part 2 (F793): the OUT-OF-CORE streaming Fiedler. The bounded co-occurrence
# graph (§52.1 cooccurrence_topk) is written to a packed binary edge file — one
# 16-byte record per edge (uint32 u | uint32 v | double w, host byte order) — and
# the Fiedler power iteration STREAMS it from disk, so only the O(n) working
# vectors are ever resident. This bounds the PARTITION step's RAM the way
# cooccurrence_topk bounds the edge SET, and is the on-disk adjacency the
# recursive out-of-core driver reads sub-graph chunks from.
_GRAPH_REC = struct.Struct("=IId")  # 16 bytes: uint32 u, uint32 v, double w (native order)
_GRAPH_CHUNK_RECS = 4096            # records per streamed read (never straddles a record)


def write_packed_graph(
    path: str,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> int:
    """Write a packed binary edge file for the out-of-core streaming Fiedler
    (§52 Part 2 / F793) — the on-disk adjacency :func:`fiedler_sparse_file`
    (and the recursive out-of-core driver) reads.

    One 16-byte record per undirected edge: ``uint32 u | uint32 v | double w``
    (host byte order; records never straddle a read chunk). The edge list lives
    on **disk**, never fully resident — this is what lets a low-RAM target build
    + partition a corpus-scale co-occurrence graph (whose materialised edge list
    is the dominant encode peak; F793). Streams the rows out as it goes (peak
    RAM = one chunk), so writing the file is itself bounded.

    Parameters
    ----------
    path : str
        Destination file (overwritten).
    edges : Iterable[Tuple[int, int]]
        Undirected edges ``(u, v)`` with ``u, v ≥ 0``.
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``); same length as ``edges``.

    Returns
    -------
    int
        The number of edge records written.
    """
    edge_iter = iter(edges)
    if weights is None:
        weight_iter: Iterable[Optional[float]] = iter(lambda: 1.0, None)  # endless 1.0
    else:
        weight_iter = iter(weights)
    written = 0
    buf = bytearray()
    pack = _GRAPH_REC.pack_into
    with open(path, "wb") as fh:
        for (a, b) in edge_iter:
            try:
                w = float(next(weight_iter))  # type: ignore[arg-type]
            except StopIteration:
                raise ValueError("weights shorter than edges") from None
            ia, ib = int(a), int(b)
            if ia < 0 or ib < 0:
                raise ValueError("edge endpoints must be non-negative")
            off = len(buf)
            buf.extend(b"\x00" * _GRAPH_REC.size)
            pack(buf, off, ia & 0xFFFFFFFF, ib & 0xFFFFFFFF, w)
            written += 1
            if len(buf) >= _GRAPH_REC.size * _GRAPH_CHUNK_RECS:
                fh.write(buf)
                buf = bytearray()
        if buf:
            fh.write(buf)
    return written


def _read_packed_graph(path: str) -> Tuple[List[Tuple[int, int]], List[float]]:
    """Read a packed edge file back into ``(edges, weights)`` (the no-native
    complete path — correct, NOT bounded; the native streaming path is bounded).
    Streams in record-aligned chunks; a non-record-multiple read is a truncated
    file → ``ValueError`` (mirrors the C ``SRMECH_ERR_BAD_INPUT`` guard)."""
    edges: List[Tuple[int, int]] = []
    weights: List[float] = []
    rec = _GRAPH_REC.size
    unpack_from = _GRAPH_REC.unpack_from
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(rec * _GRAPH_CHUNK_RECS)
            if not chunk:
                break
            if len(chunk) % rec != 0:
                raise ValueError("truncated packed graph file (not a whole record)")
            for off in range(0, len(chunk), rec):
                u, v, w = unpack_from(chunk, off)
                edges.append((u, v))
                weights.append(w)
    return edges, weights


def _fiedler_sparse_file_native(
    n: int, graph_path: str, max_iters: int
) -> Optional[List[float]]:
    """numpy-free native dispatch for :func:`fiedler_sparse_file` (§52 Part 2).

    Calls the standalone-C ``srmech_laplacian_fiedler_sparse_file`` with a
    CALLER-allocated scratch arena (9·n doubles — the bound is the caller's RAM,
    not a compiled-in cap). The matvec power iteration runs in C reading the
    adjacency from ``graph_path`` via the PAL streaming-read; only the O(n)
    arena is resident. Returns the length-n Fiedler vector as ``list[float]``,
    or ``None`` on any non-OK status (caller then uses the pure-Python path)."""
    out = (ctypes.c_double * n)()
    ws = (ctypes.c_double * (9 * n))()
    rc = _native.LIB.srmech_laplacian_fiedler_sparse_file(
        ctypes.c_uint32(n),
        graph_path.encode("utf-8"),
        ctypes.c_uint32(int(max_iters)),
        out,
        ws,
        ctypes.c_size_t(9 * n),
    )
    if rc != _native.SRMECH_OK:
        return None
    return list(out)


def fiedler_sparse_file(
    n: int,
    graph_path: str,
    *,
    max_iters: int = 250,
) -> "Vec":
    """Out-of-core sparse normalized-cut Fiedler — the streaming peer of
    :func:`fiedler_sparse` that reads its adjacency from a packed edge FILE
    instead of an in-RAM edge list (§52 Part 2 / F793).

    Identical power iteration to :func:`fiedler_sparse` (so the result equals
    ``fiedler_sparse(n, edges, weights)`` for the same graph), but the edges
    NEVER become resident: each matvec STREAMS the file (written by
    :func:`write_packed_graph`) via the PAL. Only the O(n) working vectors live
    in RAM, so a low-RAM target can partition a graph whose edge list exceeds
    RAM — the low-RAM ENCODE for graph **partition** (composes §52.1
    :func:`~srmech.amsc.text.cooccurrence_topk` for the bounded edge SET). The
    recursive out-of-core driver feeds sub-graph chunks through this.

    Dispatches to the standalone-C ``srmech_laplacian_fiedler_sparse_file`` when
    ``HAS_NATIVE`` (the bounded path — caller-arena, no caps). On a no-C lib the
    complete alternative reads the file in and runs the in-RAM cascade — correct
    but NOT bounded (the bound is a native-path property).

    Parameters
    ----------
    n : int
        Number of graph nodes.
    graph_path : str
        Packed edge file written by :func:`write_packed_graph`.
    max_iters : int
        Power-iteration cap (sign-stability usually stops earlier).

    Returns
    -------
    Vec
        The sign-bearing Fiedler vector (``.shape == (n,)``). For ``n < 2`` the
        zero vector (no cut).
    """
    if n < 2:
        return Vec.from_sequence([0.0] * max(int(n), 0), is_complex=False)
    if _native.has_native_fiedler_sparse_file():
        vals = _fiedler_sparse_file_native(int(n), graph_path, int(max_iters))
        if vals is not None:
            return Vec.from_sequence(vals, is_complex=False)
    edge_list, w_list = _read_packed_graph(graph_path)
    return Vec.from_sequence(
        _fiedler_sparse_py(int(n), edge_list, w_list, int(max_iters)),
        is_complex=False,
    )


# §52 Part 2 (F793): the OUT-OF-CORE RECURSIVE PARTITION driver. Recursively bisect
# the bounded graph into community tomes, but NEVER hold the whole structure in RAM:
# the adjacency + every pending sub-graph + every finished tome live on DISK; each
# bisection streams its sub-graph's induced edges through the rc168 fiedler_sparse_file
# (only the O(|S|) working vectors resident). Peak RAM = the single largest sub-graph
# being bisected (the top-level O(n)) — the recursion descends into shrinking
# sub-graphs, so nothing else is ever resident. This is git's "work on one object at a
# time" applied to spectral clumping.
_NODE_REC = struct.Struct("=I")  # one node id per 4-byte record in a node-set file


def _write_node_set(path: str, ids: Iterable[int]) -> int:
    """Write a node-set (original node ids) to disk as packed uint32 records.
    Streams out in bounded chunks — the set is never doubled in RAM."""
    written = 0
    buf = bytearray()
    pack = _NODE_REC.pack_into
    with open(path, "wb") as fh:
        for nid in ids:
            off = len(buf)
            buf.extend(b"\x00" * _NODE_REC.size)
            pack(buf, off, int(nid) & 0xFFFFFFFF)
            written += 1
            if len(buf) >= _NODE_REC.size * 65536:
                fh.write(buf)
                buf = bytearray()
        if buf:
            fh.write(buf)
    return written


def _read_node_set(path: str) -> List[int]:
    """Read a node-set file back into a list of original node ids."""
    out: List[int] = []
    rec = _NODE_REC.size
    unpack_from = _NODE_REC.unpack_from
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(rec * 65536)
            if not chunk:
                break
            if len(chunk) % rec != 0:
                raise ValueError("truncated node-set file")
            for off in range(0, len(chunk), rec):
                out.append(unpack_from(chunk, off)[0])
    return out


def _stream_induced_subgraph(
    parent_path: str, orig_to_local: Dict[int, int], out_path: str
) -> int:
    """Stream the parent packed-graph file and write the sub-graph induced on the
    nodes of ``orig_to_local`` (keys) to ``out_path``, RELABELLED to the local
    index ``0..|S|-1`` (so the rc168 streaming Fiedler can run on it directly). The
    parent edges never become resident — only the membership/relabel map (O(|S|))
    and a bounded I/O buffer. Returns the induced edge count."""
    rec = _GRAPH_REC.size
    written = 0
    buf = bytearray()
    unpack_from = _GRAPH_REC.unpack_from
    pack_into = _GRAPH_REC.pack_into
    get = orig_to_local.get
    with open(parent_path, "rb") as fin, open(out_path, "wb") as fout:
        while True:
            chunk = fin.read(rec * _GRAPH_CHUNK_RECS)
            if not chunk:
                break
            if len(chunk) % rec != 0:
                raise ValueError("truncated packed graph file")
            for off in range(0, len(chunk), rec):
                u, v, w = unpack_from(chunk, off)
                lu = get(u)
                lv = get(v)
                if lu is not None and lv is not None:
                    o2 = len(buf)
                    buf.extend(b"\x00" * rec)
                    pack_into(buf, o2, lu, lv, w)
                    written += 1
                    if len(buf) >= rec * _GRAPH_CHUNK_RECS:
                        fout.write(buf)
                        buf = bytearray()
        if buf:
            fout.write(buf)
    return written


def recursive_cut(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    max_tome: int = 256,
    work_dir: Optional[str] = None,
    max_iters: int = 250,
    max_depth: int = 64,
) -> Dict[str, object]:
    """Out-of-core recursive spectral partition into community **tomes** (§52 Part 2,
    F793) — the same recursion as bisecting with :func:`normalized_cut_bisect` and
    recursing on each side, but executed **out-of-core**: the adjacency, every pending
    sub-graph, and every finished tome live on **disk**, so peak RAM is the single
    largest sub-graph being bisected (the top-level ``O(n)`` working vectors), not the
    whole structure.

    The bounded graph (e.g. the ``(n, edges, weights)`` from §52.1
    :func:`~srmech.amsc.text.cooccurrence_topk`) is written to a packed file
    (:func:`write_packed_graph`); a **disk-backed work queue** of node-set files drives
    the recursion. Each step streams its sub-graph's induced edges (relabelled
    ``0..|S|-1``) to a temp file, runs the rc168 :func:`fiedler_sparse_file` (only
    ``O(|S|)`` resident), sign-splits, writes the two child node-sets to disk, and
    recurses until ``|S| ≤ max_tome`` (or ``max_depth`` / an uncuttable homogeneous
    block). A composition of :func:`fiedler_sparse_file` (a C-dispatched op) +
    :func:`write_packed_graph` + the disk-spilled recursion.

    Parameters
    ----------
    n : int
        Number of graph nodes.
    edges : Iterable[Tuple[int, int]]
        Undirected edges ``(u, v)`` with ``0 ≤ u, v < n``.
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``).
    max_tome : int
        A sub-graph with ``≤ max_tome`` nodes becomes a leaf tome (no further cut).
    work_dir : Optional[str]
        Scratch directory for the on-disk graph / queue / tomes. ``None`` → a fresh
        temp dir (the caller owns it; it is NOT auto-deleted — the tome files live
        there). Reused across calls if given.
    max_iters : int
        Per-bisection power-iteration cap (forwarded to :func:`fiedler_sparse_file`).
    max_depth : int
        Recursion-depth guard (a degenerate graph can't recurse forever).

    Returns
    -------
    Dict[str, object]
        ``{"n_tomes", "tome_paths", "tomes", "work_dir"}`` — ``tome_paths`` are the
        on-disk node-set files (the bounded record; read one with
        :func:`_read_node_set`); ``tomes`` is the convenience in-RAM list of node-id
        lists (a partition of the ``n`` nodes, so ``O(n)`` total — the same floor as
        the Fiedler vectors).
    """
    edge_list, w_list = _validate_edges_weights_py(n, edges, weights)
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="srmech_cut_")
    os.makedirs(work_dir, exist_ok=True)
    queue_dir = os.path.join(work_dir, "queue")
    tomes_dir = os.path.join(work_dir, "tomes")
    os.makedirs(queue_dir, exist_ok=True)
    os.makedirs(tomes_dir, exist_ok=True)
    graph_path = os.path.join(work_dir, "graph.bin")
    write_packed_graph(graph_path, edge_list, w_list)

    root = os.path.join(queue_dir, "set_0.bin")
    _write_node_set(root, range(int(n)))
    pending: List[Tuple[str, int]] = [(root, 0)]
    tome_paths: List[str] = []
    serial = 1
    sub_path = os.path.join(work_dir, "sub.bin")
    while pending:
        set_path, depth = pending.pop()
        ids = _read_node_set(set_path)
        if len(ids) <= int(max_tome) or len(ids) < 2 or depth >= int(max_depth):
            dest = os.path.join(tomes_dir, "tome_%d.bin" % len(tome_paths))
            os.replace(set_path, dest)                 # MOVE the survivor, never copy
            tome_paths.append(dest)
            continue
        orig_to_local = {orig: i for i, orig in enumerate(ids)}
        _stream_induced_subgraph(graph_path, orig_to_local, sub_path)
        fv = fiedler_sparse_file(len(ids), sub_path, max_iters=int(max_iters))
        left = [ids[i] for i in range(len(ids)) if fv[i] < 0]
        right = [ids[i] for i in range(len(ids)) if fv[i] >= 0]
        os.remove(set_path)
        if not left or not right:                      # uncuttable homogeneous block
            dest = os.path.join(tomes_dir, "tome_%d.bin" % len(tome_paths))
            _write_node_set(dest, ids)
            tome_paths.append(dest)
            continue
        lp = os.path.join(queue_dir, "set_%d.bin" % serial); serial += 1
        rp = os.path.join(queue_dir, "set_%d.bin" % serial); serial += 1
        _write_node_set(lp, left)
        _write_node_set(rp, right)
        pending.append((lp, depth + 1))
        pending.append((rp, depth + 1))
    if os.path.exists(sub_path):
        os.remove(sub_path)
    return {
        "n_tomes": len(tome_paths),
        "tome_paths": tome_paths,
        "tomes": [_read_node_set(t) for t in tome_paths],
        "work_dir": work_dir,
    }


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
    "fiedler_sparse",
    "normalized_cut_bisect",
    "write_packed_graph",
    "fiedler_sparse_file",
    "recursive_cut",
    "jacobi_eigvals",
    "spectral_block_dispatch",
    "hermitian_eigendecompose",
    "symmetric_eigendecompose",
    "mat_matmul",
    "mat_solve",
    "mat_hermitian_eigendecompose",
    "mat_lstsq",
    "mat_eigvals",
    "mat_svd",
    "mat_norm",
    "mat_dot",
    "mat_matvec",
    "mat_outer",
    "elementwise_multiply_complex",
    "elementwise_transcendental",
    "elementwise_hypot",
    "elementwise_sqrt",
    "dense_solve",
    "schur_complement",
    "dirichlet_to_neumann",
)
