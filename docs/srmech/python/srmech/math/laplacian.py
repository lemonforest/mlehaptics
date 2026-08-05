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
from srmech.math.q import Q, to_q  # §26: exact-rational interior solve (Class-N), no float
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from srmech.math.rational import sqrt as _rsqrt  # §22: scalar root via Class-N, not libm
from srmech.math.rational import hypot as _rhypot  # Class-N |z| magnitude, not libm
from srmech.math.rational import exp as _rexp  # Class-N exp cascade, not libm
from srmech.math.rational import cos as _rcos  # Class-N cos cascade, not libm
from srmech.math.rational import sin as _rsin  # Class-N sin cascade, not libm
from srmech.math.rational import log as _rlog  # Class-N log cascade, not libm
from srmech.math.rational import atan2 as _ratan2  # Class-N atan2 cascade, not libm
from srmech.math.rational import complex_exp as _rcomplex_exp  # Class-N e^z, not libm
from srmech.math.rational import exp_series_truncate as _exp_series  # rc136 EPH: Class-N exp
from srmech.math.rational import cos_series_truncate as _cos_series  # rc136 EPH: Class-N cos
from srmech.math.rational import sin_series_truncate as _sin_series  # rc136 EPH: Class-N sin
from srmech.math.rational import atan_series_truncate as _atan_series  # rc136 EPH: Machin-2π


# 0.9.0rc7 (stay-rational, F868): ``rational.sqrt`` / ``rational.hypot`` now
# return an exact :class:`~srmech.math.q.Q`. That is right for EXACT contexts,
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
from srmech.math.rational import atan as _atan_pi
_PI = 4.0 * float(_atan_pi(1.0))

from .mat import Mat  # §564: the numpy-free 2-D carrier the mat_* engine returns
from .vec import Vec  # rc129: the numpy-free 1-D carrier (vectors / eigenvalues)

from .. import _native

# §101 (rc275) progress-event mirrors — shared by the pure + native tick paths so
# the emitted dict is byte-identical across them (the C↔Python parity contract).
_PROGRESS_STRUCT_SIZE = _native.PROGRESS_STRUCT_SIZE
_PHASE_PARTITIONING = _native.SRMECH_PHASE_PARTITIONING

__all__ = [
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "mass_normalized_laplacian",
    "cotangent_weights",
    "klein4_gain_laplacian",
    "klein4_relational_structure",
    "quaternion_laplacian",
    "octonion_laplacian",
    "hypercomplex_perspectives",
    "cycle_holonomy",
    "eulerian_path",
    "eulerian_circuit",
    "recover_check",
    "recover_check_structural",
    "recover_check_spectral",
    "order_fingerprint",
    "recover_check_order",
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
    "heat_trace",
    "ground_state_flux_response",
    "propagate",
    "eph_harvest",
    "propagate_sparse",
    "propagate_wound",
    "responsion",
    "LAPLACIAN_OPS",
    "MAX_NATIVE_NODES",
    "MAX_NATIVE_HERMITIAN_NODES",
    "three_fold_eigvec_groups",
    "spectral_spine",
    "relational_structure",
    "generalized_ngon",
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
    ``(n, k)`` real :class:`~srmech.math.mat.Mat` of the eigenvector COLUMNS in
    that band (rc129; ``.shape`` + ``m[i, j]``, NOT a bare nested list); the
    chirality-aware companion to :func:`symmetric_eigendecompose`.

    rc154 (BATCH B10, ``composition_of_c``): the op COMPOSES the
    ``composition_of_c`` :func:`symmetric_eigendecompose` (which dispatches to the
    C-backed Hermitian eigendecomposition) for the spectrum + the c_dispatched
    ``srmech_three_fold_bands`` for the integer band split; the column-slice into
    three ``Mat`` bands is exact integer glue. Parity is **eig-INVARIANT** (the
    Jacobi eigenbasis is non-unique): native == pure agree on the band SIZES
    (exact) and the per-band SPAN, not element-wise — the rc146 so7 / rc152
    ``casimir_eigenvalue`` invariant precedent. No new C symbol.
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

    Numpy-free (rc129): returns a real :class:`~srmech.math.mat.Mat` (``.shape``
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

    Numpy-free (rc129): returns a real :class:`~srmech.math.mat.Mat` (``.shape``
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

    Numpy-free (rc129): returns a real :class:`~srmech.math.mat.Mat` (``.shape``
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


# ── 0.9.0rc328 (task #893 / #888 rec (c)) — the Laplace–Beltrami α-family ──
# mass_normalized_laplacian generalises normalized_laplacian from degree-D to
# an arbitrary diagonal mass M; cotangent_weights emits the discrete LB edge
# weights. See docs/srmech/notes/laplace_beltrami_scoping.md — LB is a
# WEIGHTING/NORMALIZATION of the shipped Class-L Laplacian, not a PDE solver.
_MASS_NORM_KINDS: dict = {"symmetric": 0, "rw": 1}


def _mass_normalized_laplacian_py(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    ml: Optional[List[float]],
    kind_code: int,
) -> List[List[float]]:
    """Pure-Python mass-normalized Laplacian (the numpy-free fallback).

    Builds ``L = D − W`` then applies the diagonal scale ``s_i``. ``ml is None``
    → ``m_i`` is the degree ``L[i][i]`` (α=0 connectivity); else ``m_i = ml[i]``
    (α=1 metric). Symmetric (kind 0): ``L̂[r,c] = L[r,c]·s_r·s_c``, ``s_i =
    1/sqrt(m_i)``; random-walk (kind 1): ``L̂[r,c] = L[r,c]·s_r``, ``s_i =
    1/m_i``. ``m_i <= 0`` → ``s_i = 0`` (isolated / massless vertex, mirroring
    normalized_laplacian). No ``abs()``: the ``m_i > 0`` guard is a Class-K
    pin-slot on the sqrt/reciprocal domain, not an ALU magnitude."""
    L = _dense_laplacian_py(n, el, wl)  # list[list[float]], diagonal = degree
    m = [L[i][i] for i in range(n)] if ml is None else list(ml)
    s = [0.0] * n
    for i in range(n):
        mi = m[i]
        if mi > 0.0:
            s[i] = (1.0 / _fsqrt(mi)) if kind_code == 0 else (1.0 / mi)
    for r in range(n):
        sr = s[r]
        for c in range(n):
            L[r][c] = (L[r][c] * sr * s[c]) if kind_code == 0 else (L[r][c] * sr)
    return L


def _mass_normalized_laplacian_native(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    ml: Optional[List[float]],
    kind_code: int,
) -> Optional[List[List[float]]]:
    """numpy-free native dispatch for :func:`mass_normalized_laplacian` (rc328).

    Marshals the edge / weight / mass lists into ctypes buffers and calls the
    standalone-C ``srmech_graph_mass_normalized_laplacian`` with a caller
    ``scale_ws`` workspace (n doubles) + an ``n*n``-double output. The C peer
    runs the SAME Class-N ``srmech_rational_sqrt`` the pure path runs, so the
    result is bit-identical. Returns the nested ``list[list[float]]``, or
    ``None`` on any non-OK status / missing symbol (caller then uses the pure
    Python build)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_graph_mass_normalized_laplacian")
    ):
        return None
    n_edges = len(el)
    out = (ctypes.c_double * (n * n))()
    scale_ws = (ctypes.c_double * n)()
    null_u = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32))
    null_d = ctypes.cast(None, ctypes.POINTER(ctypes.c_double))
    if n_edges:
        eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in el))
        ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in el))
        wbuf = (ctypes.c_double * n_edges)(*(float(w) for w in wl))
    else:
        eu = ev = null_u
        wbuf = null_d
    mbuf = null_d if ml is None else (ctypes.c_double * n)(*(float(x) for x in ml))
    rc = _native.LIB.srmech_graph_mass_normalized_laplacian(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, wbuf,
        mbuf, ctypes.c_uint32(kind_code), scale_ws, out,
    )
    if rc != _native.SRMECH_OK:
        return None
    return [[out[r * n + c] for c in range(n)] for r in range(n)]


def mass_normalized_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    masses: Optional[Iterable[float]] = None,
    *,
    kind: str = "symmetric",
) -> "Mat":
    """Mass-normalized (Laplace–Beltrami α-family) Laplacian.

    Builds the weighted combinatorial Laplacian ``L = D − W`` and normalizes it
    by a diagonal mass ``M``:

    * ``kind="symmetric"`` → ``L̂ = M^(−1/2) (D − W) M^(−1/2)`` (real-symmetric,
      PSD; the constant nullvector becomes ``M^(1/2)·𝟙``);
    * ``kind="rw"`` → ``L̂ = M^(−1) (D − W)`` (the random-walk Laplacian; every
      row sums to 0).

    ``masses`` (length ``n``) is the diagonal mass. **This selects the position
    on the Coifman–Lafon diffusion-maps ``α``-family** (*Diffusion Maps*, ACHA
    21(1):5–30, 2006 — author-hosted OA):

    * ``masses=None`` → ``M = D`` (the weighted **degree**): the **α = 0**
      *connectivity*-normalization. Symmetric with ``masses=None`` recovers
      :func:`normalized_laplacian` (``I − D^(−1/2) A D^(−1/2)``) up to the
      exact-1 diagonal convention (here the diagonal is ``d_i·s_i²``, float-1);
    * ``masses`` = Voronoi/barycentric areas → the **α = 1** *metric*-
      normalization: the geometrically-faithful **discrete Laplace–Beltrami**
      spectrum (generalized eigenproblem ``L_c v = λ M v``), recovered
      independent of sampling density. Feed cotangent stiffness weights (see
      :func:`cotangent_weights`) as ``weights`` and Voronoi areas as ``masses``.

    A mass ``m_i <= 0`` yields scale 0 (isolated / massless vertex, mirroring
    :func:`normalized_laplacian`); **no** ``abs()`` — the ``m_i > 0`` guard is a
    Class-K pin-slot on the sqrt/reciprocal domain. The one algebraic step is
    the ``M^(−1/2)`` sqrt (the Class-N ``srmech_rational_sqrt`` cascade, NOT
    libm). Native (rc328): dispatches to the standalone-C
    ``srmech_graph_mass_normalized_laplacian`` (bit-identical; the pure-Python
    build is the complete no-native alternative). No node cap.

    Attested scoping SSoT: ``docs/srmech/notes/laplace_beltrami_scoping.md``
    (task #888) — LB is a *weighting* of the Class-L Laplacian, not a new member.

    Returns an ``n×n`` real :class:`~srmech.math.mat.Mat` (``.shape`` +
    ``m[i, j]``, NOT a bare ``list[list[float]]``).
    """
    kind_code = _MASS_NORM_KINDS.get(kind)
    if kind_code is None:
        raise ValueError(
            f"kind must be 'symmetric' or 'rw'; got {kind!r}"
        )
    el, wl = _validate_edges_weights_py(n, edges, weights)
    ml: Optional[List[float]] = None
    if masses is not None:
        ml = [float(x) for x in masses]
        if len(ml) != n:
            raise ValueError(f"masses length {len(ml)} != n {n}")
    rows = _mass_normalized_laplacian_native(n, el, wl, ml, kind_code)
    if rows is None:
        rows = _mass_normalized_laplacian_py(n, el, wl, ml, kind_code)
    return Mat.from_rows(rows, is_complex=False)


def _cotangent_weights_py(
    tris: List[Tuple[int, int, int]],
    pos: List[List[float]],
    dim: int,
) -> Tuple[List[Tuple[int, int]], List[float]]:
    """Pure-Python cotangent-weight contributions (the numpy-free fallback).

    Per triangle, emits the three per-corner ``½·cot(θ)`` contributions — one
    per edge, opposite each vertex. cot θ = (u·v)/|u×v| with the Lagrange cross
    magnitude ``|u×v| = sqrt(|u|²|v|² − (u·v)²)`` (≥ 0 in 2-D and 3-D; NO
    ``abs()``). Raises on a degenerate (collinear) triangle."""
    edges: List[Tuple[int, int]] = []
    weights: List[float] = []
    for (a, b, c) in tris:
        v3 = (a, b, c)
        for corner in range(3):
            ka = v3[corner]
            ib = v3[(corner + 1) % 3]
            jc = v3[(corner + 2) % 3]
            uvec = [float(pos[ib][d]) - float(pos[ka][d]) for d in range(dim)]
            vvec = [float(pos[jc][d]) - float(pos[ka][d]) for d in range(dim)]
            dot = 0.0
            uu = 0.0
            vv = 0.0
            for d in range(dim):
                dot += uvec[d] * vvec[d]
                uu += uvec[d] * uvec[d]
                vv += vvec[d] * vvec[d]
            cross2 = uu * vv - dot * dot  # |u×v|² (Lagrange identity)
            if not (cross2 > 0.0):
                raise ValueError(
                    f"degenerate (collinear) triangle {(a, b, c)}: the cross "
                    "magnitude vanishes so the cotangent is undefined"
                )
            cot = dot / _fsqrt(cross2)
            edges.append((ib, jc))
            weights.append(0.5 * cot)
    return edges, weights


def _cotangent_weights_native(
    tris: List[Tuple[int, int, int]],
    pos: List[List[float]],
    dim: int,
    n_vert: int,
) -> Optional[Tuple[List[Tuple[int, int]], List[float]]]:
    """numpy-free native dispatch for :func:`cotangent_weights` (rc328).

    Marshals the triangle indices + flat positions into ctypes buffers and
    calls the standalone-C ``srmech_graph_cotangent_weights`` with 3·n_tri
    output slots. Same Class-N ``srmech_rational_sqrt`` → bit-identical.
    Returns ``(edges, weights)``, or ``None`` on any non-OK status / missing
    symbol (caller then uses the pure-Python build, which raises the same
    degenerate-triangle error)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_graph_cotangent_weights")
    ):
        return None
    n_tri = len(tris)
    if n_tri == 0:
        return [], []
    flat_tri: List[int] = []
    for (a, b, c) in tris:
        flat_tri.extend((a, b, c))
    flat_pos: List[float] = []
    for p in pos:
        for d in range(dim):
            flat_pos.append(float(p[d]))
    n_slots = 3 * n_tri
    tri_buf = (ctypes.c_uint32 * (3 * n_tri))(*flat_tri)
    pos_buf = (ctypes.c_double * len(flat_pos))(*flat_pos)
    out_u = (ctypes.c_uint32 * n_slots)()
    out_v = (ctypes.c_uint32 * n_slots)()
    out_w = (ctypes.c_double * n_slots)()
    rc = _native.LIB.srmech_graph_cotangent_weights(
        ctypes.c_uint32(n_tri), tri_buf, pos_buf,
        ctypes.c_uint32(dim), ctypes.c_uint32(n_vert),
        out_u, out_v, out_w,
    )
    if rc != _native.SRMECH_OK:
        return None
    edges = [(int(out_u[i]), int(out_v[i])) for i in range(n_slots)]
    weights = [out_w[i] for i in range(n_slots)]
    return edges, weights


def cotangent_weights(
    triangles: Iterable[Tuple[int, int, int]],
    positions: Iterable[Iterable[float]],
) -> Tuple[List[Tuple[int, int]], List[float]]:
    """Cotangent-weight Laplacian weights — the discrete Laplace–Beltrami
    edge weights on a triangulated manifold (Pinkall & Polthier 1993).

    Takes the triangle geometry as given **numbers** (``positions`` as data —
    this is algebra/spectral only, **NOT** CAD mesh-contact / fabrication
    geometry) and returns ``(edges, weights)`` ready to feed
    :func:`dense_laplacian`: for each triangle it emits the THREE per-corner
    contributions ``½·cot(θ_k)`` for the edge opposite vertex ``k``, with the
    two edge vectors ``u = p_i − p_k``, ``v = p_j − p_k`` taken from ``k``:

        cot θ = (u·v) / |u×v|,   |u×v| = sqrt(|u|²|v|² − (u·v)²)   (Lagrange)

    **No trig** (no ``cos``/``sin``/``atan``): the only irrationality is one
    algebraic ``sqrt`` per corner (the Class-N ``srmech_rational_sqrt``
    cascade); the Lagrange cross magnitude is ≥ 0 in 2-D and 3-D alike, so
    there is **no** ``abs()`` (the signed area is a Class-K pin-slot the
    magnitude never needs). In 2-D the cotangent is fully rational; in 3-D the
    single ``sqrt`` is ``2·Area``.

    The returned ``edges`` list holds the 3·n_tri per-corner contributions
    (the two triangles sharing an edge appear as parallel edges), so::

        L_cot = dense_laplacian(n_vertices, *cotangent_weights(tris, positions))

    accumulates them — via :func:`dense_laplacian`'s parallel-edge summation —
    into the standard cotangent Laplacian ``w_ij = ½(cot α_ij + cot β_ij)``
    (symmetric, every row summing to 0). This is the ``α = 1`` metric leg's
    stiffness matrix; pair it with Voronoi ``masses`` in
    :func:`mass_normalized_laplacian` for the discrete LB spectrum.

    Attested SSoT: U. Pinkall & K. Polthier, "Computing Discrete Minimal
    Surfaces and Their Conjugates", Exp. Math. 2(1):15–36 (1993) (Project
    Euclid OA); scoping in ``docs/srmech/notes/laplace_beltrami_scoping.md``.

    Native (rc328): dispatches to the standalone-C
    ``srmech_graph_cotangent_weights`` (bit-identical). Raises ``ValueError``
    on a degenerate (collinear) triangle or a non-2-D/3-D / ragged position.
    """
    pos: List[List[float]] = [list(p) for p in positions]
    n_vert = len(pos)
    if n_vert == 0:
        raise ValueError("positions must be non-empty")
    dim = len(pos[0])
    if dim not in (2, 3):
        raise ValueError(f"positions must be 2-D or 3-D; got dim={dim}")
    for i, p in enumerate(pos):
        if len(p) != dim:
            raise ValueError(
                f"position {i} has dimension {len(p)} != {dim} (ragged)"
            )
    tris: List[Tuple[int, int, int]] = []
    for t in triangles:
        tt = tuple(int(x) for x in t)
        if len(tt) != 3:
            raise ValueError(f"triangle {tt} is not a 3-tuple of vertex indices")
        for idx in tt:
            if not (0 <= idx < n_vert):
                raise ValueError(
                    f"triangle vertex {idx} outside node range [0, {n_vert})"
                )
        tris.append(tt)  # type: ignore[arg-type]
    res = _cotangent_weights_native(tris, pos, dim, n_vert)
    if res is None:
        res = _cotangent_weights_py(tris, pos, dim)
    return res


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
    the exact-substrate cascade :func:`srmech.cascade.matrix_cascades.eigvals_exact`
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
    from srmech.cascade.matrix_cascades import eigvals_exact
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

    Numpy-free (rc129): the input is a :class:`~srmech.math.mat.Mat` /
    ``list[list[float]]`` (or any nested sequence) and the return is a 1-D
    :class:`~srmech.math.vec.Vec` of the ascending eigenvalues (``.shape == (n,)``
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
      Faddeev–LeVerrier → Yun square-free → Sturm isolation → ``Q``
      bisection — until the single terminal float lift (the rotation-last
      "exact-substrate-achievable" case). The return is the same contract as
      the float path: a 1-D :class:`~srmech.math.vec.Vec` of ``n`` ascending
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


def _solve_exact(A: List[list], B: List[list]) -> List[List[Q]]:
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
    M = [[to_q(A[r][c]) for c in range(m)] + [to_q(B[r][c]) for c in range(w)]
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
    float reciprocal, F392) and ``X`` is ``list[list[Q]]`` (or
    ``list[Q]`` for a vector RHS) — the exact path keeps the rational
    leaves. With ``exact=False`` (the default) the float realization rides the
    numpy-free Mat engine (:func:`mat_solve` — native ``srmech_dense_solve_f64_ws``
    Gauss–Jordan with partial pivoting, the Class-K magnitude pivot — a sign
    branch, not ``abs()``; else srmech's own exact Q fallback coerced to
    float). The float ``X`` is returned in the numpy-free **carrier** (rc131):
    a :class:`~srmech.math.mat.Mat` for a matrix RHS (``.shape`` + ``m[i, j]``)
    or a 1-D :class:`~srmech.math.vec.Vec` for a vector RHS (``.shape == (n,)``
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
        X = _solve_exact(A_rows, B_rows)  # exact Q Gauss–Jordan (Class-N)
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
    never a float reciprocal) and ``S`` is returned as ``list[list[Q]]``.
    With ``exact=False`` (the default) the float realization rides the numpy-free
    Mat engine (:func:`dense_solve` → :func:`mat_solve`) and ``S`` is returned in
    the numpy-free **carrier** — a ``|∂|×|∂|`` :class:`~srmech.math.mat.Mat`
    (rc131; ``.shape`` + ``m[i, j]``), NOT a bare ``list`` (a Mat IS a C dense
    buffer, a list is not). Canonical SSoT: Zhang, *The Schur Complement and Its
    Applications* (2005) §0; the DtN map is textbook (Golub & Van Loan §3.2).

    Parameters
    ----------
    L : matrix, ``n×n``
        A :class:`~srmech.math.mat.Mat` or ``list[list]`` — a symmetric
        positive-semidefinite operator (a graph Laplacian from
        :func:`dense_laplacian`, or any SPD matrix).
    boundary_idx : sequence[int]
        The boundary node indices ``∂``; ``1 ≤ |∂| ≤ n``, no duplicates.
    exact : bool, default ``False``
        Force the exact-rational :class:`~fractions.Fraction` solve (returns
        ``list[list[Q]]``).

    Returns
    -------
    S : ``|∂|×|∂|`` boundary effective operator
        a real :class:`~srmech.math.mat.Mat` (float path) or
        ``list[list[Q]]`` (exact path).

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
            return [[to_q(v) for v in r] for r in L_pp]
        return Mat.from_rows([[float(v) for v in r] for r in L_pp], is_complex=False)

    L_pi = _block(b, i)  # L_∂i
    L_ip = _block(i, b)  # L_i∂
    L_ii = _block(i, i)  # L_ii

    if exact:
        # Interior solve L_ii · X = L_i∂ (X is |i|×|∂|) via the Class-L
        # dense_solve primitive — exact-rational Gauss–Jordan (Class-N).
        X = dense_solve(L_ii, L_ip, exact=True)  # list[list[Q]]
        # S = L_∂∂ − L_∂i · X  (all exact Q).
        S = [
            [
                to_q(L_pp[a][c])
                - sum(to_q(L_pi[a][k]) * X[k][c] for k in range(len(i)))
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
    :func:`schur_complement`: a real :class:`~srmech.math.mat.Mat` (float path)
    or ``list[list[Q]]`` (``exact=True``)."""
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
        ``eigvals`` is a length-``n`` real :class:`~srmech.math.vec.Vec` of
        eigenvalues in ascending order (``.shape == (n,)`` + scalar ``v[i]``).
        ``V`` is an ``n×n`` complex :class:`~srmech.math.mat.Mat` — the unitary
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
    :class:`~srmech.math.mat.Mat`; the result is the (possibly modified) nested
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


def _pin_eigenvector_phases(V):
    """Rotate each COMPLEX eigenvector column onto the real axis (rc351, ``#T1004``).

    A Hermitian eigenvector is defined up to a ``U(1)`` phase, not merely a ``Z₂``
    sign — and inside a DEGENERATE eigenspace the Jacobi cascade is free to hand back
    a basis carrying an arbitrary phase, because every unitary basis of that
    eigenspace is equally correct. :func:`symmetric_eigendecompose` used to project
    with a bare ``.real``, whose docstring asserted *"the Hermitian path returns them
    with imaginary part ~0"*. **That premise is false on a degenerate spectrum.**
    ``symmetric_eigendecompose`` of the 3×3 IDENTITY measured

        V = [[1, 0, 0], [0, 0, 1j], [0, 1, 0]]

    — a perfectly valid unitary basis whose middle column is ``i·e₂``. ``.real``
    annihilated it, returning a matrix with a zero row that neither reconstructs
    (``V·diag(w)·Vᵀ`` came back 0 where ``L`` was 1) nor is orthonormal. The native
    Jacobi peer happens to return real columns, so this was visible ONLY with no
    native library — which is why it sat unobserved until the rc351
    ``fallback (pure-Python, no native)`` CI cell ran the suite that way for the
    first time.

    The pin: pick each column's largest-magnitude entry (via ``re²+im²``, so no
    ``abs()``) and multiply the column by ``conj(pivot)/|pivot|``. The pivot becomes
    real and POSITIVE, so this SUBSUMES the ``Z₂`` pin of
    :func:`_canonicalize_eigenvector_signs` (a real negative pivot gives the factor
    ``−1``). ``V`` is a nested ``list`` of ``complex``; returns the pinned nested list.

    **The magnitude is a Class-N cascade, not an FPU power.** The first cut of this
    wrote ``best ** 0.5`` and the A-N cascade ratchet caught it on every CI cell at
    once (``float_pow: live=1 ceiling=0``) — ``CEIL_FLOAT_POW`` is a hard-won zero and
    is not to be spent. ``|pivot|`` is a complex modulus, which is exactly what
    :func:`_fhypot` (``float(rational.hypot(re, im))``) is for. Sign-handling and
    MAGNITUDE are both cascade ops; doing the Class-K half right and then reaching for
    the FPU for the other half is half the discipline.

    A root here is genuinely unavoidable — producing a UNIT column from a non-unit one
    is a normalisation, and every route to it (phase pin, ``Re``/``Im`` selection, or
    ``Re(zᵣ·conj(z_k))``, all of which were checked) lands on the same ``√(re²+im²)``.
    What IS avoidable is paying for it when there is no phase to remove: a pivot
    already ON the real axis needs only the ``±1`` Class-K flip. **Measured over the
    same 804-matrix corpus (3214 columns pinned): the native path needs the root for
    0 columns — 0.00%, the C Jacobi always returns real columns — and the pure path
    for 150, 4.67%.** So the cascade call is confined to exactly the degenerate
    columns that motivate this function, and costs nothing anywhere else.

    **Measured, not assumed:** over 804 real-symmetric matrices (5 hand-built
    degenerate fixtures + 400 random-symmetric + 400 exactly-degenerate diagonals,
    n ≤ 6) the residual imaginary part after pinning is **identically 0.0** — the
    cascade's columns are real up to a GLOBAL phase, never a genuine mixture of two
    real eigenvectors. So the projection below is exact, not an approximation, and
    the caller can drop the imaginary part with nothing left in it.
    """
    n_rows = len(V)
    if n_rows == 0:
        return V
    n_cols = len(V[0])
    for j in range(n_cols):
        # Largest-|·| entry of column j via re²+im² (no abs()).
        k, best = 0, -1.0
        for r in range(n_rows):
            z = V[r][j]
            cur = z.real * z.real + z.imag * z.imag
            if cur > best:
                best = cur
                k = r
        if best <= 0.0:
            continue                          # an all-zero column carries no phase
        pivot = V[k][j]
        if pivot.imag == 0.0:
            # Already on ℝ: the phase is ±1, so this is the Class-K sign pin alone —
            # no modulus, no root, no cascade call. The overwhelmingly common case.
            if pivot.real < 0.0:
                for r in range(n_rows):
                    V[r][j] = -V[r][j]
            continue
        # A genuinely complex pivot: conj(pivot)/|pivot| is the unit phase that
        # rotates it onto ℝ₊. |pivot| is a COMPLEX MODULUS — the Class-N cascade
        # op (_fhypot = float(rational.hypot(re, im))), never an FPU `** 0.5`.
        phase = complex(pivot.real, -pivot.imag) / _fhypot(pivot.real, pivot.imag)
        for r in range(n_rows):
            V[r][j] = V[r][j] * phase
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
        ``eigvals`` is a length-``n`` real :class:`~srmech.math.vec.Vec` of
        eigenvalues in ascending order (``.shape == (n,)`` + scalar ``v[i]``).
        ``V`` is an ``n×n`` **real** :class:`~srmech.math.mat.Mat` whose COLUMNS
        are the corresponding eigenvectors (``V[i, j]``).

    Class L. Canonical SSoT: Golub & Van Loan, *Matrix Computations*
    (4th ed., Johns Hopkins, 2013) §8.3 (symmetric eigenproblem).

    Numpy-free (rc129): delegates to :func:`hermitian_eigendecompose`
    (real-symmetric IS complex-Hermitian — native Jacobi peer when available,
    else srmech's own pure-Python cyclic Jacobi).

    rc351 (``#T1004``): the eigenvectors of a real-symmetric matrix are real **up to
    a phase**, and on a DEGENERATE spectrum the pure cascade really does return a
    column carrying one (``i·e₂`` for the 3×3 identity). This used to project with a
    bare ``.real``, which annihilated such a column and returned a matrix that
    neither reconstructed nor was orthonormal — a defect the native Jacobi masked, so
    it was observable only with no native library. Each column is now rotated onto
    the real axis first (:func:`_pin_eigenvector_phases`, which also subsumes the
    Class-K ``Z₂`` pivot-sign pin of :func:`_canonicalize_eigenvector_signs`) and the
    projection is exact. Eigenvalues come out ascending as a ``Vec``. Correctness is
    pinned by eigenvalues + reconstruction + orthonormality (the eigenvector sign /
    degenerate-subspace basis is non-unique), not element-wise parity.
    """
    rows = _as_rows(L)
    real_rows = [[float(v.real) if isinstance(v, complex) else float(v) for v in r]
                 for r in rows]
    n = len(real_rows)
    if n == 0:
        return (Vec(array("d"), 0), Mat(array("d"), 0, 0))
    eigvals, V_complex = hermitian_eigendecompose(real_rows)
    # Rotate each column onto ℝ (the U(1) gauge) BEFORE dropping the imaginary part:
    # on a degenerate eigenspace the basis is only real up to a global phase.
    V_pinned = _pin_eigenvector_phases([list(r) for r in V_complex])
    V_real = [[x.real for x in r] for r in V_pinned]
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


def mat_matmul(a: "Mat", b: "Mat") -> "Mat":
    """Numpy-free dense matrix multiply ``A·B`` over the
    :class:`~srmech.math.mat.Mat` carrier — the 2-D ``@`` replacement for the
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
    :class:`~srmech.math.mat.Mat` carrier — bridge primitive #2 of the
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
    (:func:`_solve_exact`, Class-N ``Q`` division, numpy-free) coerced to
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
    X = _solve_exact(a.tolist(), b.tolist())  # list[list[Q]]; raises if singular
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
    ``‖A·X − B‖``) over the :class:`~srmech.math.mat.Mat` carrier — the
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
    :class:`~srmech.math.mat.Mat` carrier — bridge primitive **#3** (the last) of
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
    (:func:`srmech.math.rational.hypot` + ``sqrt``) — no ``cmath.sqrt``. The
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


def _cmax_component(z: complex) -> float:
    """``max(|Re z|, |Im z|)`` — a magnitude PROXY that needs no square root, so
    it is exact at every scale. Sign is a **Class-K** pin-slot with **Class-C**
    re-application (never a bare ``abs()``)."""
    r = z.real if z.real >= 0.0 else -z.real
    i = z.imag if z.imag >= 0.0 else -z.imag
    return r if r >= i else i


# Below this fraction of the (scaled, O(1)) column norm, ``x0``'s phase is taken
# as real rather than as ``x0/|x0|``. The window is bounded on BOTH sides:
#
#  * ABOVE it, ``_fhypot`` must be accurate enough that ``x0/_fhypot(x0)`` is a
#    unit phase — measured relative error is 1.1e-13 at 1e-4 but 5.3e-10 at
#    1e-8, and any error there lands directly on ``|α| = ‖x‖``;
#  * BELOW it, the real branch must not cancel in ``v[0] = x0 − α``. With
#    ``α = −‖x‖`` that is ``v[0] = x0 + ‖x‖``, which cancels only if ``x0`` is
#    real-NEGATIVE and comparable to ``‖x‖`` — impossible once ``|x0|`` is
#    capped at this fraction of it, giving ``|v[0]| ≥ (1 − 1e-4)·‖x‖``.
_HOUSEHOLDER_PHASE_REL = 1e-4


def _householder_reflector(x: List[complex]):
    """Householder reflector ``P = I − β·v·vᴴ`` with ``P·x = α·e₁``, returned as
    ``(v, β)`` — or ``None`` when there is nothing to annihilate.

    **Scale-invariance is a CORRECTNESS requirement here (rc285), not a nicety.**
    ``P`` is invariant under ``v → v/c``, so the vector is first divided by its
    largest component magnitude, putting every entry at ``O(1)``. That matters
    because ``_fhypot`` is a **bounded-denominator Class-N rational cascade**,
    not libm's ``hypot``: it carries ≈ −2e−5 relative error at ``1e-12`` and
    returns **exactly 0.0** below ≈ ``1e-17``. So for a small ``x0`` the phase
    ``x0 / _fhypot(x0)`` is **not** a unit complex number — measured 1.25 for
    ``x0 = 6.9e-17`` — which makes ``|α| ≠ ‖x‖``, and then ``P`` is not a
    reflector at all. In :func:`_hessenberg_complex` that silently turned the
    reduction into a NON-similarity: 1.6e-1 asymmetry from a symmetric input and
    1.4e-2 of spectral drift on an 11-vertex broom graph. Scaling to ``O(1)``
    first keeps every ``_fhypot`` call inside its accurate range.

    Canonical SSoT: Golub & Van Loan §5.1.3 (Householder vectors, and the
    standard practice of scaling ``x`` before forming them).
    """
    scale = 0.0
    for z in x:
        c = _cmax_component(z)                       # exact at every magnitude
        if c > scale:
            scale = c
    if scale == 0.0:
        return None                                  # x is the zero vector
    xs = [z / scale for z in x]                      # every entry now O(1)
    normx2 = 0.0
    for z in xs:
        normx2 += (z.conjugate() * z).real
    if normx2 <= 0.0:
        return None
    normx = _fsqrt(normx2)                           # Class-N ‖x‖
    x0 = xs[0]
    modx0 = _fhypot(x0.real, x0.imag)                # Class-K magnitude (no abs())
    # The phase exists ONLY to keep v[0] = x0 − α away from cancellation. When
    # |x0| is negligible against ‖x‖ there is no cancellation to avoid and x0's
    # phase is noise, so the real branch is both safe and better conditioned.
    if modx0 > _HOUSEHOLDER_PHASE_REL * normx:
        phase = x0 / modx0
    else:
        phase = complex(1.0, 0.0)
    alpha = -phase * normx                           # Class-K pin-slot phase
    v = list(xs)
    v[0] = v[0] - alpha
    vhv = 0.0
    for z in v:
        vhv += (z.conjugate() * z).real
    if vhv == 0.0:
        return None
    return v, 2.0 / vhv                              # Class-N 1/(vᴴv) scale


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
        # rc285: the reflector is built by the SCALE-INVARIANT
        # :func:`_householder_reflector` — see its docstring for why dividing by
        # ``_fhypot(x0)`` unscaled does not yield a unit phase.
        refl = _householder_reflector([R[i][k] for i in range(k, m)])
        if refl is None:
            continue
        v, beta = refl
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


def _balance_radix2(H: List[List[complex]]) -> List[List[complex]]:
    """Parlett–Reinsch balancing of a square ``complex`` matrix ``H`` in place,
    using **RADIX-2** scaling so the diagonal similarity ``D⁻¹·H·D`` is **EXACT**.

    Each index ``i`` is scaled by a power of two ``f = 2^k`` — row ``i`` divided by
    ``f`` and column ``i`` multiplied by ``f`` (the similarity ``D⁻¹HD`` with
    ``D = diag(2^{k_i})``). Because ``f`` is a power of two, every multiply/divide
    is an EXACT binary shift of the mantissa (no floating rounding), so the
    eigenvalue multiset is **invariant** — unchanged for well-scaled input, more
    accurate for badly-scaled input (the QR sweep no longer amplifies a lopsided
    row-norm/col-norm split). The iteration equalises each index's row-norm ``r``
    against its column-norm ``c`` by the standard Parlett–Reinsch test, accepting a
    step only when it REDUCES ``r + c``; sweeps repeat until no index changes.

    The norms use the Class-K :func:`_modulus_c` magnitude (no bare ``abs()`` per
    the cascade-honesty rule). This is a pure pre-conditioning step on ``H`` — the
    exceptional-shift QR that follows is unchanged.

    Canonical SSoT: Parlett & Reinsch, "Balancing a matrix for calculation of
    eigenvalues and eigenvectors", *Numer. Math.* **13** (1969) 293–304; Golub &
    Van Loan, *Matrix Computations* (4th ed., 2013) §7.5.1.
    """
    n = len(H)
    radix = 2.0
    radix2 = radix * radix                            # β² (exact: 4.0)
    converged = False
    while not converged:
        converged = True
        for i in range(n):
            r = 0.0                                    # row-norm  Σ_{j≠i} |H[i][j]|
            c = 0.0                                    # col-norm  Σ_{j≠i} |H[j][i]|
            for j in range(n):
                if j == i:
                    continue
                r += _modulus_c(H[i][j])               # Class-K magnitude (no abs())
                c += _modulus_c(H[j][i])               # Class-K magnitude (no abs())
            if c == 0.0 or r == 0.0:
                continue                               # an isolated index — skip
            # The EISPACK ``balanc`` (Parlett–Reinsch) inner test, radix-2: choose
            # the power of two ``f`` that drives the SCALED col-norm ``c`` toward the
            # row-norm ``r`` — bring c UP while it is below ``r/β`` (each step c·β²,
            # f·β), then DOWN while it is at/above ``r·β`` (each step c/β², f/β).
            f = 1.0                                    # the radix-2 scale 2^k
            s = c + r                                  # the quantity to reduce
            g = r / radix
            while c < g:
                f *= radix
                c *= radix2
            g = r * radix
            while c >= g:
                f /= radix
                c /= radix2
            # Accept only if the SCALED sum (c + r)/f genuinely drops below 0.95·s.
            # Dividing by f is what makes ``s`` strictly DECREASE on every accepted
            # step (the row-norm becomes r/f, the col-norm becomes c·f → their sum
            # is (c·f + r/f); NR tracks the post-scale col-norm in ``c`` already, so
            # the comparison quantity is (c + r)/f). This monotone decrease is the
            # Parlett–Reinsch termination guarantee — without the ``/f`` the sweeps
            # can OSCILLATE and never converge.
            if (c + r) < 0.95 * s * f and f != 1.0:
                converged = False                      # a change → another sweep
                for j in range(n):                     # row i ÷ f, col i × f (exact)
                    H[i][j] = H[i][j] / f
                    H[j][i] = H[j][i] * f
    return H


def _hessenberg_complex(A: List[List[complex]]) -> List[List[complex]]:
    """Unitary reduction of a square ``complex`` matrix to **upper-Hessenberg**
    form ``P·A·Pᴴ`` by Householder reflectors — the step :func:`mat_eigvals`
    was missing (rc285; issue #1440).

    **Why the shifted-QR sweep cannot skip this.** The sweep's deflation test
    inspects the single subdiagonal entry ``H[m-1][m-2]`` and, when it is
    negligible, accepts ``H[m-1][m-1]`` as a converged eigenvalue. That test is
    sound **only for an upper-Hessenberg matrix**, where the sub-subdiagonal is
    structurally zero and so ``H[m-1][m-2]`` is the *whole* of the last row
    below the diagonal. On a matrix that was never reduced, the last row can
    hold large entries at ``H[m-1][j]`` for ``j < m-2`` while ``H[m-1][m-2]``
    is exactly 0, and the sweep then deflates a NON-eigenvalue and continues on
    the wrong leading block. That is precisely a sparse graph Laplacian whose
    last two vertices are non-adjacent — a star (every pair of leaves), and
    equally many paths / trees / forests under an unlucky vertex labelling.

    Each reflector ``P_k = I − β·v·vᴴ`` annihilates column ``k`` below the
    subdiagonal. ``P_k`` is Hermitian AND unitary (an involution), so the
    two-sided application ``A ← P_k·A·P_k`` is a **similarity** — the
    eigenvalue multiset is invariant, exactly as for the :func:`_balance_radix2`
    diagonal similarity that precedes it. The reflector phase is a **Class-K**
    pin-slot (no bare ``abs()``); the annihilated entries are pinned to exact
    zero rather than left at round-off, so the Hessenberg structure the
    deflation test relies on is a structural fact, not a tolerance.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §7.4.3 (Householder reduction to Hessenberg form) — the
    prerequisite §7.5's practical shifted-QR algorithm assumes throughout.
    """
    n = len(A)
    H = [[complex(A[i][j]) for j in range(n)] for i in range(n)]
    for k in range(n - 2):
        # The reflector is built by the SCALE-INVARIANT
        # :func:`_householder_reflector`. Building it from the UNSCALED column
        # is what made this reduction stop being a similarity: see that
        # function's docstring for the ``_fhypot`` phase defect and the measured
        # 1.4e-2 spectral drift it caused.
        refl = _householder_reflector([H[i][k] for i in range(k + 1, n)])
        if refl is None:                               # column already reduced
            for i in range(k + 2, n):
                H[i][k] = 0j                           # Class-K pin-slot at zero
            continue
        v, beta = refl
        for j in range(n):                             # LEFT: H ← (I − β v vᴴ)·H
            s = 0j
            for idx, i in enumerate(range(k + 1, n)):
                s += v[idx].conjugate() * H[i][j]
            s *= beta
            for idx, i in enumerate(range(k + 1, n)):
                H[i][j] -= v[idx] * s
        for i in range(n):                             # RIGHT: H ← H·(I − β v vᴴ)
            s = 0j
            for idx, j in enumerate(range(k + 1, n)):
                s += H[i][j] * v[idx]
            s *= beta
            for idx, j in enumerate(range(k + 1, n)):
                H[i][j] -= s * v[idx].conjugate()
        for i in range(k + 2, n):                      # Class-K pin-slot at zero:
            H[i][k] = 0j                               # structural, not tolerance
    return H


def _mat_eigvals_native(H: List[List[complex]], n: int, max_sweeps: int):
    """Route the general non-Hermitian eigenproblem to ``srmech_mat_eigvals_ws``.

    Returns the ``list[complex]`` multiset, or ``None`` when the native path is
    unavailable or reports non-convergence — in which case the caller runs the
    pure sweep, which is the COMPLETE alternative (not a smaller-cap one).
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    if not hasattr(_native.LIB, "srmech_mat_eigvals_ws"):
        return None
    a_il = (ctypes.c_double * (2 * n * n))()
    for i in range(n):
        for j in range(n):
            z = H[i][j]
            a_il[(i * n + j) * 2] = z.real
            a_il[(i * n + j) * 2 + 1] = z.imag
    ws_len = int(_native.LIB.srmech_mat_eigvals_ws_size(ctypes.c_uint32(n)))
    workspace = (ctypes.c_double * ws_len)()
    out = (ctypes.c_double * (2 * n))()
    rc = _native.LIB.srmech_mat_eigvals_ws(
        ctypes.c_uint32(n), a_il, ctypes.c_uint32(max_sweeps),
        out, workspace, ctypes.c_size_t(ws_len),
    )
    if rc != _native.SRMECH_OK:
        return None                                   # → pure sweep (or its raise)
    return [complex(out[i * 2], out[i * 2 + 1]) for i in range(n)]


def mat_eigvals(a: "Mat", *, max_sweeps: int = 500) -> List[complex]:
    """Eigenvalue MULTISET of a general (non-Hermitian) square matrix over the
    :class:`~srmech.math.mat.Mat` carrier — foundation op #4 of the numpy-CARRIER
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

    * **Balancing (Parlett–Reinsch, radix-2).** Before the QR sweep ``H`` is
      pre-conditioned by :func:`_balance_radix2` — an EXACT diagonal similarity
      ``D⁻¹·H·D`` with ``D`` a diagonal of powers of two, chosen to equalise each
      index's row-norm against its column-norm. Powers of two make every scale a
      binary shift of the mantissa (no floating rounding), so the eigenvalue
      multiset is **invariant**: unchanged for well-scaled input, MORE ACCURATE
      for badly-scaled input (a lopsided row/col-norm split otherwise loses digits
      in the QR iteration). The shifted-QR step below is unchanged.

    * **Hessenberg reduction (rc285; issue #1440).** After balancing and before
      the QR sweep, ``H`` is reduced to upper-Hessenberg form by
      :func:`_hessenberg_complex` — a two-sided Householder similarity
      ``P·H·Pᴴ``, so the multiset is again invariant. This is a **correctness**
      prerequisite, not a speed-up: the sweep's deflation test reads only the
      subdiagonal ``H[m-1][m-2]``, which is the whole of the last row below the
      diagonal ONLY in Hessenberg form. Before rc285 the reduction was absent,
      so any matrix with ``H[m-1][m-2] == 0`` but a non-negligible ``H[m-1][j]``
      for ``j < m-2`` deflated a NON-eigenvalue and then solved the wrong
      leading block. Every graph Laplacian whose last two vertices are
      non-adjacent has exactly that shape — every star (its leaves are pairwise
      non-adjacent), and any path / tree / forest under an unlucky labelling —
      so ``mat_eigvals`` returned a spectrum with the correct trace and correct
      interior but a wrong extreme pair, violating the ``λ_min == 0`` Laplacian
      invariant.

    * **Active-block QR step (rc285).** Each shifted step is applied to
      ``H[lo:m, lo:m]`` — the trailing UNREDUCED block — after every negligible
      subdiagonal has been pinned to exact zero. A pinned zero splits the
      Hessenberg matrix, and the spectrum is then the union of the blocks'
      spectra, so the off-diagonal blocks need no update when only eigenvalues
      are wanted. Applying a step whose Wilkinson shift was chosen from the
      BOTTOM corner across an already-split leading block degrades that block's
      eigenvalues sweep after sweep. **This is hardening, not the #1440 bug:**
      over the ratchet's 230 (graph × relabelling) cases the split fires in 181,
      and forcing ``lo = 0`` with everything else at rc285 still leaves 229 of
      230 correct (the straggler drifts to 6.5e-9, against 3.9e-14 with the
      split respected).

    * **Scale-invariant Householder reflectors (rc285).** Both this path's
      reduction and its per-step ``{QR}`` build reflectors through
      :func:`_householder_reflector`, which divides the column by its largest
      component magnitude first. ``_fhypot`` is a bounded-denominator Class-N
      rational cascade, not libm ``hypot`` — it returns exactly ``0.0`` below
      ≈``1e-17`` — so an unscaled ``x0 / _fhypot(x0)`` is not a unit phase for a
      small ``x0``, and the "reflector" built from it is not a reflector. That
      turned the reduction into a NON-similarity (1.6e-1 asymmetry from a
      symmetric input, 1.4e-2 of spectral drift on an 11-vertex broom graph).
      ``cascade.matrix_cascades.qr`` carried the same unsafe division and is
      fixed with it; every other ``_fhypot`` use in the package is a comparison
      or a magnitude readout, where snapping a sub-1e-17 value to zero is
      benign. **Division is the only unsafe consumption of ``_fhypot``.**

      All of the above are ratcheted by
      ``test_laplacian_kernel_invariant_rc285.py``, whose ``λ_min == 0`` /
      relabelling-invariance properties hold over EVERY shipped eigensolver,
      not just this one.

    Canonical SSoT: Golub & Van Loan, *Matrix Computations* (4th ed., Johns
    Hopkins, 2013) §7.4.3 (Householder reduction to Hessenberg form) + §7.5 (the
    practical QR algorithm with Wilkinson shifts) + §7.5.1 (balancing); Parlett &
    Reinsch, "Balancing a matrix for calculation of eigenvalues and
    eigenvectors", *Numer. Math.* **13** (1969) 293–304.
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
    # rc299 (`#918`) — the whole-op native peer. Before it, this op was
    # classified ``composition_of_c`` ("standalone-ready") while every step that
    # matters (balancing, the Hessenberg reduction, deflation, the Wilkinson
    # shift ladder, {QR}) was Python-only and only the RQ recombine reached C.
    # A bare-C host could not run it for ANY input, Hermitian included, because
    # there is no Hermitian fast path here. ``srmech_mat_eigvals_ws`` is the
    # same algorithm in C, so the classification is now true rather than
    # narrowed. NUMERIC (FPU-tol) parity — see the C file's header for the one
    # divergence (the exact-rational vs scaled-float modulus, ~1 ulp).
    native = _mat_eigvals_native(H, n, max_sweeps)
    if native is not None:
        return native
    # Parlett–Reinsch RADIX-2 balancing pre-step: an EXACT diagonal similarity
    # D⁻¹·H·D (powers of two only → no floating rounding) that equalises each
    # index's row-norm against its column-norm. Eigenvalues are invariant under a
    # similarity, so the multiset is UNCHANGED for well-scaled input and MORE
    # ACCURATE for badly-scaled input. (Parlett & Reinsch 1969; G&VL §7.5.1.)
    H = _balance_radix2(H)
    # Householder reduction to upper-HESSENBERG form (rc285, issue #1440) — a
    # unitary similarity P·H·Pᴴ, so the multiset is invariant. This is what makes
    # the deflation test below (which reads ONLY the subdiagonal H[m-1][m-2])
    # SOUND: on a Hessenberg matrix the subdiagonal IS the whole of the last row
    # below the diagonal. Without it, a matrix with H[m-1][m-2] == 0 but a
    # non-negligible H[m-1][j], j < m-2 — every sparse Laplacian whose last two
    # vertices are non-adjacent, e.g. any star's two leaves — deflates a
    # NON-eigenvalue and then solves the wrong leading block. (G&VL §7.4.3.)
    H = _hessenberg_complex(H)
    eigs: List[complex] = []
    m = n
    sweeps = 0
    it = 0                                            # iterations since last deflate
    sweep_ceiling = max_sweeps * n
    while m > 0:
        if m == 1:
            eigs.append(H[0][0])                      # Class-L: last eigenvalue
            break
        # Negligible-subdiagonal PIN (rc285). Any subdiagonal small against its
        # two diagonal neighbours is pinned to EXACT zero — a Class-K pin-slot,
        # not a tolerance carried forward. Every such zero SPLITS the Hessenberg
        # matrix into independent diagonal blocks whose spectra are disjoint.
        for i in range(1, m):
            nbr = _modulus_c(H[i - 1][i - 1]) + _modulus_c(H[i][i])
            if _modulus_c(H[i][i - 1]) <= _MAT_EIG_DEFLATE_TOL * (nbr + 1e-300):
                H[i][i - 1] = 0j                      # Class-K pin-slot at zero
        if H[m - 1][m - 2] == 0j:
            eigs.append(H[m - 1][m - 1])              # Class-L: deflate eigenvalue
            m -= 1
            it = 0                                    # new deflation-target: reset stall
            continue
        if m == 2:
            lam1, lam2 = _eig2x2(H[0][0], H[0][1], H[1][0], H[1][1])  # closed form
            eigs.append(lam1)
            eigs.append(lam2)
            break
        # ACTIVE-BLOCK search (rc285). ``lo`` is the first row of the trailing
        # UNREDUCED block: scan up from m-1 while the subdiagonal is non-zero.
        # The QR step below is applied to H[lo:m, lo:m] ALONE.
        #
        # WHY: the Wilkinson shift μ is chosen from the trailing 2×2, i.e. tuned
        # to the BOTTOM block. Before rc285 a step with that shift was applied
        # to the whole leading block, pushing a shift wrong for the top block
        # through already-split rows. Because H[lo][lo-1] is EXACTLY zero the
        # matrix is block upper-triangular there, so the spectrum is the union
        # of the blocks' spectra and the off-diagonal blocks need no update when
        # only eigenvalues are wanted. (Golub & Van Loan §7.5.2, the "Francis QR
        # step applied to the active submatrix" structure.)
        #
        # HONEST SCOPE — this is hardening, not the #1440 bug. Measured over the
        # ratchet's 230 (graph × relabelling) cases: the split fires (lo > 0) in
        # 181, and forcing lo = 0 with everything else at rc285 leaves 229 of
        # 230 still correct, the one straggler drifting to 6.5e-9 (against
        # 3.9e-14 with the split respected). So it buys real accuracy and is the
        # textbook structure, but it is NOT what produced the wrong star
        # spectrum — the missing Hessenberg reduction was — and it is NOT what
        # produced the 1.4e-2 broom drift, which was the non-unit reflector
        # phase (see :func:`_householder_reflector`).
        lo = m - 1
        while lo > 0 and H[lo][lo - 1] != 0j:
            lo -= 1
        if m - lo == 2:                               # active block is 2×2 exactly
            lam1, lam2 = _eig2x2(
                H[lo][lo], H[lo][lo + 1], H[lo + 1][lo], H[lo + 1][lo + 1]
            )
            eigs.append(lam1)
            eigs.append(lam2)
            m = lo
            it = 0
            continue
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
            if m - 3 >= lo:
                mu += _modulus_c(H[m - 2][m - 3])
            mu = complex(mu, 0.0)                     # Class-C real ad-hoc shift
        else:
            lam1, lam2 = _eig2x2(
                H[m - 2][m - 2], H[m - 2][m - 1], H[m - 1][m - 2], H[m - 1][m - 1]
            )
            dd = H[m - 1][m - 1]
            mu = lam1 if _modulus_c(lam1 - dd) < _modulus_c(lam2 - dd) else lam2
        # QR of the ACTIVE block H[lo:m, lo:m] minus μI; then that block
        # ← R·Q + μI, the RQ contraction routed through the native Mat-carrier
        # mat_matmul (Class K). Rows/cols outside [lo, m) are untouched — the
        # exact zero at H[lo][lo-1] makes them a separate spectral block.
        k = m - lo
        sub = [
            [H[lo + i][lo + j] - (mu if i == j else 0j) for j in range(k)]
            for i in range(k)
        ]
        Q, R = _qr_complex_list(sub)                  # {QR} numpy-free
        rq = mat_matmul(
            Mat.from_rows(R, is_complex=True), Mat.from_rows(Q, is_complex=True)
        )
        for i in range(k):
            for j in range(k):
                H[lo + i][lo + j] = complex(rq[i, j]) + (mu if i == j else 0j)
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
                f"srmech.cascade.matrix_cascades.eigvals_exact for certified roots"
            )
    return eigs


def mat_svd(a: "Mat") -> Tuple["Mat", List[float], "Mat"]:
    """Numpy-free **full** singular-value decomposition ``A = U·diag(S)·Vᴴ`` over
    the :class:`~srmech.math.mat.Mat` carrier — foundation op **#5** of the
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

    # Descending singular values ``sigma`` (len n) + right singular vectors
    # ``vcols[j]``. rc140 (Foundation F2): a REAL, tall/square (m>=n) input
    # dispatches to the native one-sided-Jacobi ``srmech_svd_f64`` — a directly-
    # computed SVD that does NOT square the condition number (contrast the Gram
    # AᴴA eigen-route below). The native kernel returns a NOT-converged status
    # on a (rare) sweep-cap miss, in which case ``svd_f64_c`` returns ``None``
    # and we fall through to the pure Gram route (never a silent wrong answer).
    sigma = None
    vcols = None
    if (not a.is_complex) and m >= n:
        native = _native.svd_f64_c(
            [[float(a[i, j]) for j in range(n)] for i in range(m)]
        )
        if native is not None:
            sigma, vcols = native                     # sigma desc (n); vcols[j] (n)
    if sigma is None:
        # Gram-eigen route: right singular vectors = eigenvectors of the
        # Hermitian PSD Gram AᴴA (n×n) — the COMPLETE alternative (complex input,
        # m<n, no-C host, or a non-converged native sweep).
        ah = a.conj().T                               # Aᴴ (n, m) — Class-K conj ∘ T
        aha = mat_matmul(ah, a)                       # (n, n) Hermitian PSD
        evals, V = mat_hermitian_eigendecompose(aha)  # λ (n,1) asc; V (n,n) unitary
        lam = [float(evals[i, 0]) for i in range(n)]
        order = sorted(range(n), key=lambda i: lam[i], reverse=True)  # desc λ → σ
        vcols = [[V[i, order[j]] for i in range(n)] for j in range(n)]
        sigma = [_fsqrt(lam[order[j]] if lam[order[j]] > 0.0 else 0.0)
                 for j in range(n)]
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
    :func:`srmech.math.rational.sqrt` root. Value-faithful to the NumPy 2-norm /
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
# return float64. They exist so the real-typed consumer sites (Spin(8)
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
    a complex :class:`~srmech.math.mat.Mat` out; a :class:`Vec` / 1-D flat ``a``
    → a complex :class:`~srmech.math.vec.Vec` out (rc129 — NOT a bare
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
    :mod:`srmech.math.rational` cascade.
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
        Rank-preserving (rc129): a :class:`~srmech.math.mat.Mat` for a 2-D
        input, a :class:`~srmech.math.vec.Vec` for a 1-D input (NOT a bare
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
    route through. Each element runs :func:`srmech.math.rational.hypot` (Class M
    sum-of-squares ∘ Class N∘K :func:`~srmech.math.rational.sqrt`; native
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
        Rank-preserving (rc129): a real :class:`~srmech.math.mat.Mat` for a 2-D
        ``a``, a real :class:`~srmech.math.vec.Vec` for a 1-D ``a`` — ``√(aᵢ² +
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
    :func:`srmech.math.rational.sqrt` (Class-N∘K integer-``isqrt`` cascade;
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
        Rank-preserving (rc129): a real :class:`~srmech.math.mat.Mat` for a 2-D
        input, a real :class:`~srmech.math.vec.Vec` for a 1-D input — ``√arrᵢ``
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

    Returns an ``n×n`` real-symmetric :class:`~srmech.math.mat.Mat` (rc129;
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


# rc105 (#1234 Item 3): sentinel distinguishing "q not passed" from every
# real value, so the q ⊕ charges mutual-exclusion contract can reject ANY
# explicit q alongside charges while `q` unset stays byte-for-byte the
# rc28 default (0.25).
_MAGNETIC_Q_DEFAULT = 0.25
_MAGNETIC_Q_UNSET = object()


def _magnetic_laplacian_scalar_py(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    q: float,
) -> List[List[complex]]:
    """The rc28 scalar-q construction (pure Python) — UNCHANGED math.

    ``A_s = (W + Wᵀ)/2``; ``L[r,c] = −A_s[r,c]·exp(i·2π·q·(W[r,c]−W[c,r]))``;
    diagonal = symmetrised degree. Split out of :func:`magnetic_laplacian`
    verbatim (rc105) so the native dispatch has a pure twin to parity-test
    against; every float op and accumulation order is byte-identical to rc104.
    """
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
    return L


def _magnetic_laplacian_charges_py(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    cl: List[float],
) -> List[List[complex]]:
    """Per-edge CHIRAL construction (pure Python) — rc105, F1006/F1007.

    Each edge ``k = (u, v)`` with weight ``w`` and charge ``c`` (in TURNS,
    the same unit as the scalar ``q``) accumulates the conjugate Hermitian
    pair::

        L[u, v] += −(w/2)·exp(+i·2π·c)
        L[v, u] += −(w/2)·exp(−i·2π·c)
        deg[u] += w/2;  deg[v] += w/2;   L[r, r] = deg[r]

    Hermitian BY CONSTRUCTION (the two writes are exact conjugates); the
    ``w/2`` matches the scalar mode's ``(W + Wᵀ)/2`` magnitude scale, and
    ``(u, v, c)`` is equivalent to ``(v, u, −c)``. A dual-sense pair
    ``(is-a: weight a, charge +q)`` + ``(is-not-a: weight b, charge −q)``
    on the same ``(u, v)`` yields the off-diagonal
    ``−[(a+b)/2·cos(2πq) + i·(a−b)/2·sin(2πq)]`` — the conjugate partners
    SURVIVE (contrast :func:`signed_laplacian`, where ``+a`` and ``−b``
    with ``a == b`` sum to zero and the relationship vanishes).
    """
    two_pi = 2.0 * _PI
    L = [[0j] * n for _ in range(n)]
    deg = [0.0] * n
    for (u, v), w, ch in zip(el, wl, cl):
        u = int(u)  # same endpoint coercion as _directed_adjacency /
        v = int(v)  # the native uint32 marshal (float endpoints accepted)
        hw = 0.5 * w
        deg[u] += hw
        deg[v] += hw
        if u == v:
            continue  # no self-phase; degree carries the diagonal
        ang = two_pi * ch
        re = float(_rcos(ang))
        im = float(_rsin(ang))
        L[u][v] += complex(-(hw * re), -(hw * im))
        L[v][u] += complex(-(hw * re), hw * im)
    for r in range(n):
        L[r][r] = complex(deg[r])
    return L


def _magnetic_laplacian_native(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    q: float,
    cl: Optional[List[float]],
) -> Optional[List[List[complex]]]:
    """numpy-free native dispatch for :func:`magnetic_laplacian` (rc105).

    Marshals the edge endpoints into ``(c_uint32 * n_edges)`` buffers +
    weights (and per-edge charges, when given) into ``(c_double * n_edges)``
    buffers and calls the standalone-C ``srmech_graph_magnetic_laplacian``
    with a caller-allocated ``2*n*n``-double interleaved-complex output (no
    scratch arena — the C peer stages W in the output's imaginary slots).
    The C peer runs the SAME Q61 trig cascade the pure path runs, so the
    result is bit-identical. Returns the nested ``list[list[complex]]``, or
    ``None`` on any non-OK status / missing symbol (caller then uses the
    pure-Python cascade)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_graph_magnetic_laplacian")
    ):
        return None
    n_edges = len(el)
    out = (ctypes.c_double * (2 * n * n))()
    null_u = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32))
    null_d = ctypes.cast(None, ctypes.POINTER(ctypes.c_double))
    if n_edges:
        eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in el))
        ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in el))
        wbuf = (ctypes.c_double * n_edges)(*(float(w) for w in wl))
    else:
        eu = ev = null_u
        wbuf = null_d
    cbuf = null_d
    if cl is not None and n_edges:
        cbuf = (ctypes.c_double * n_edges)(*(float(c) for c in cl))
    rc = _native.LIB.srmech_graph_magnetic_laplacian(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, wbuf,
        ctypes.c_double(float(q)), cbuf, out,
    )
    if rc != _native.SRMECH_OK:
        return None
    return [
        [complex(out[2 * (r * n + c)], out[2 * (r * n + c) + 1])
         for c in range(n)]
        for r in range(n)
    ]


def magnetic_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    q: float = _MAGNETIC_Q_UNSET,  # type: ignore[assignment]  # sentinel; 0.25 when unset
    charges: Optional[Iterable[float]] = None,
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
    for directed graphs. Attested SSoT: E. H. Lieb & M. Loss, "Fluxes,
    Laplacians, and Kasteleyn's Theorem", Duke Math. J. 71 (1993)
    337–363 (OA preprint arXiv:cond-mat/9209031); the complex-unit-
    gain-graph spectral framing is N. Reff, "Spectral Properties of
    Complex Unit Gain Graphs", Linear Algebra Appl. 436 (2012)
    3165–3176 (arXiv:1110.4554).

    **Per-edge charges (rc105; issue #1234 Item 3 / F1006 / F1007) — the
    CHIRAL Laplacian for dual-sense knowledge graphs.** ``charges`` is an
    optional iterable parallel to ``edges`` (validated
    ``len(charges) == len(edges)``), each entry a per-edge charge in
    **turns** (the same unit as ``q``). When given, each edge
    ``k = (u, v, w, c)`` accumulates the conjugate Hermitian pair
    ``L[u,v] += −(w/2)·e^{+i·2π·c}`` / ``L[v,u] += −(w/2)·e^{−i·2π·c}``
    (``(u, v, c) ≡ (v, u, −c)``; the ``w/2`` matches the scalar mode's
    ``(W + Wᵀ)/2`` magnitude scale), and the real diagonal carries the
    magnitude degree ``Σ w/2``. WHY (F1006/F1007): on an **exactly
    balanced** dual-sense edge the real :func:`signed_laplacian`
    ANNIHILATES it — "is-a" (+1) and "is-not-a" (−1) sum to 0 and the
    relationship vanishes — while the two phase senses ``e^{±i·2π·q}``
    are conjugate partners that SURVIVE: a dual-sense pair ``(a, +q)`` +
    ``(b, −q)`` reads ``−[(a+b)/2·cos(2πq) + i·(a−b)/2·sin(2πq)]`` — the
    symmetric part in the real cosine, the is-a/is-not-a IMBALANCE in the
    imaginary sine residue (chiral flux, not cancellation).

    **The balanced case is the ONLY case that cancels — do not read this
    as chiral preservation of a bias** (measured, workflow ``w8y06lpew``
    2026-07-25). When ``a ≠ b`` the real operator does NOT annihilate: it
    returns exactly ``−(a − b)`` (300/300, worst deviation 0.0), because
    :func:`_dense_adjacency_py` sums parallel edges *before* the Class-K
    magnitude. That is **twice** the ``(a − b)/2`` the chiral mode
    retains, so on an imbalanced pair the REAL operator carries the
    imbalance more strongly, not less. Neither mode amplifies: the
    chirality order parameter grows as ``tanh(2k·atanh(s/d))``, which a
    real ABELIAN 2×2 with the same splitting reproduces to 9 decimal
    places — ``k ~ 1/ε`` linear filtering, not ``k ~ log(1/ε)``
    autocatalysis (a Hermitian operator has a real spectrum and cannot
    beat its own eigenvalue ratio). Any apparent ε-floor difference
    between the two modes is an ENCODING artefact, not a property of
    chirality: under a scale-free encoding the chiral mode's relative
    splitting is ``1.0000`` from ``ε = 1e-6`` down to ``1e-100``.

    **Contract: ``q`` and ``charges`` are mutually exclusive.** Passing
    ``charges`` moves every edge's phase onto the edge itself, so a scalar
    ``q`` has no role there — passing BOTH raises ``ValueError`` (silent
    ignore would hide a modelling error). ``charges=None`` (default) is the
    scalar-``q`` construction, byte-for-byte the rc28 behaviour
    (``q`` unset → 0.25).

    Numpy-free (rc129): the ``2π`` is the Class-N ``4·atan(1)`` cascade π
    (no stdlib ``math.pi``, no ``np.pi``); the per-element phase is the
    libm-free Class-N ``cos``/``sin`` cascade. Native (rc105): both modes
    dispatch to the standalone-C ``srmech_graph_magnetic_laplacian`` (the
    same Q61 trig cascade → bit-identical; pure Python is the complete
    no-native alternative). Returns an ``n×n`` Hermitian complex
    :class:`~srmech.math.mat.Mat` (``.shape`` + ``m[i, j]``, NOT a bare
    ``list[list[complex]]``).
    """
    if charges is not None:
        if q is not _MAGNETIC_Q_UNSET:
            raise ValueError(
                "q and charges are mutually exclusive: per-edge charges carry "
                "the phase themselves, so a scalar q has no role — pass one "
                "or the other"
            )
        el, wl = _validate_edges_weights_py(n, edges, weights)
        cl = [float(c) for c in charges]
        if len(cl) != len(el):
            raise ValueError(
                f"charges length {len(cl)} != n_edges {len(el)}"
            )
        rows = _magnetic_laplacian_native(n, el, wl, 0.0, cl)
        if rows is None:
            rows = _magnetic_laplacian_charges_py(n, el, wl, cl)
        return Mat.from_rows(rows, is_complex=True)
    qv = _MAGNETIC_Q_DEFAULT if q is _MAGNETIC_Q_UNSET else q
    if not isinstance(qv, (int, float)):
        raise TypeError(f"q must be a real number; got {type(qv).__name__}")
    el, wl = _validate_edges_weights_py(n, edges, weights)
    rows = _magnetic_laplacian_native(n, el, wl, float(qv), None)
    if rows is None:
        rows = _magnetic_laplacian_scalar_py(n, el, wl, float(qv))
    # Always complex layout (a Hermitian Laplacian is genuinely complex even
    # when q=0 collapses the imaginary part — pin the carrier dtype explicitly).
    return Mat.from_rows(rows, is_complex=True)


# =====================================================================
# rc308 (#944) — the ℍ (associative) sibling of magnetic_laplacian: the
# QUATERNION gain Laplacian + the hypercomplex-perspective reader.
# =====================================================================
#
# magnetic_laplacian is the ℂ (dim-2) complex-unit-gain Laplacian (Reff 2012);
# quaternion_laplacian is its ℍ (dim-4) ASSOCIATIVE rung — a 4n×4n
# REAL-SYMMETRIC matrix whose (u, v) block is the 4×4 real left-multiplication
# rep ``L(g_uv)`` of a unit-quaternion gain, with the (v, u) block
# ``L(conj g_uv) == L(g_uv)ᵀ`` (so the matrix is symmetric BY CONSTRUCTION).
# Two spectral facts distinguish ℍ from the ℂ leg:
#
#   * GAUGE INVARIANCE — a node-wise unit-quaternion gauge ``s_u ∈ Sp(1)``
#     conjugates the matrix by the ORTHOGONAL block-diagonal ``diag(L(s_u))``
#     (``L`` of a unit quaternion is orthogonal), so the spectrum is fixed
#     (proven ~3.3e-15 in the tests). This mirrors the U(1) gauge-invariance of
#     the complex-unit-gain Laplacian, one rung up the Cayley–Dickson ladder.
#   * ×4 DEGENERACY (a THEOREM, not an accident) — because ℍ is ASSOCIATIVE,
#     left- and right-multiplication COMMUTE, so the whole (left-built) matrix
#     commutes with the fixed RIGHT-ℍ action (the Sp(1) commutant ``R_i/R_j/R_k``
#     block-diagonalised). A real matrix commuting with the standard right-ℍ
#     action has right-ℍ-module eigenspaces → EVERY eigenvalue has multiplicity
#     a multiple of 4. Callers dedupe by taking every 4th eigenvalue.
#
# CLASS: **Class L** (graph spectral) composing **Class-M** atoms
# (:func:`srmech.physics.qm.quaternion.quaternion_left_mult` is the Clifford / HDC
# bind); the gain conjugate is **Class C**
# (:func:`srmech.physics.qm.quaternion.quaternion_conjugate`) and the gain
# normalisation is **Class K + Class C**
# (:func:`srmech.physics.qm.quaternion.quaternion_norm` — an exact-rational 4-vector
# hypot, NEVER an ALU ``abs()``; the 2-arg complex ``_modulus_c`` cannot take a
# 4-vector, and the scalar cascade ``magnitude`` raises on a vector). Attested
# SSoT (DERIVED-from-open-premises; the complex-unit-gain framing generalises
# one Cayley–Dickson rung): N. Reff, "Spectral Properties of Complex Unit Gain
# Graphs", Linear Algebra Appl. 436 (2012) 3165–3176 (arXiv:1110.4554);
# the ℍ gain algebra is the octonion module's Cayley–Dickson convention at
# dim 4 (Baez, J.C. (2002) The Octonions, arXiv:math/0105155, §1). The op
# composes SHIPPED atoms only — ``quaternion_left_mult`` →
# ``srmech_quaternion_left_mult`` and ``mat_hermitian_eigendecompose`` →
# ``srmech_hermitian_eigendecompose_ws`` — so a bare-C host assembles both
# matrices and eigendecomposes (honest C parity; no new C symbol, ABI stays 10).

_QUATERNION_DIM = 4
_QUATERNION_IDENTITY_GAIN: Tuple[float, ...] = (1.0, 0.0, 0.0, 0.0)


def _resolve_quaternion_gains(
    el: List[Tuple[int, int]],
    gains: Optional[Iterable[Sequence[float]]],
) -> List[List[float]]:
    """Resolve ``gains`` to one UNIT quaternion (4-vector) per edge.

    ``gains=None`` → the identity gain ``e0 = (1, 0, 0, 0)`` on every edge (the
    undirected control: ``L(e0) = I₄``, so the build collapses to
    ``½·(dense graph Laplacian) ⊗ I₄``). A supplied gain is normalised to
    ``Sp(1)`` via the **Class-K + Class-C**
    :func:`srmech.physics.qm.quaternion.quaternion_norm` (exact-rational 4-vector hypot,
    never ``abs()``); a zero-norm gain raises. Resolved ONCE per public call so
    the assembly consumes identical floats.
    """
    from srmech.physics.qm.quaternion import quaternion_norm as _qnorm
    if gains is None:
        return [list(_QUATERNION_IDENTITY_GAIN) for _ in el]
    gl = [[float(c) for c in g] for g in gains]
    if len(gl) != len(el):
        raise ValueError(f"gains length {len(gl)} != n_edges {len(el)}")
    out: List[List[float]] = []
    for k, g in enumerate(gl):
        if len(g) != _QUATERNION_DIM:
            raise ValueError(
                f"gain {k} must be a 4-vector quaternion; got length {len(g)}")
        nrm = _qnorm(g)
        if nrm == 0.0:
            raise ValueError(f"gain {k} must be a non-zero quaternion")
        inv = 1.0 / nrm
        out.append([g[0] * inv, g[1] * inv, g[2] * inv, g[3] * inv])
    return out


def _quaternion_laplacian_blocks(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    gl: List[List[float]],
) -> List[List[float]]:
    """Assemble the ``4n×4n`` real-symmetric quaternion gain Laplacian as a
    nested ``list[list[float]]`` (numpy-free).

    Per edge ``k = (u, v, w, g)`` (``g`` an already-unit quaternion): the
    ``(u, v)`` block accumulates ``−(w/2)·L(g)``, the ``(v, u)`` block
    ``−(w/2)·L(conj g)`` — and ``L(conj g) == L(g)ᵀ`` for the fixed
    Cayley–Dickson convention, so ``L[bu+a, bv+b] == L[bv+b, bu+a]`` term by
    term (the matrix is EXACTLY symmetric, no float asymmetry). Each endpoint's
    diagonal block gains ``(w/2)·I₄``; the accumulated ``deg[r]·I₄`` mirrors
    :func:`magnetic_laplacian`'s per-edge ``w/2`` magnitude scale.
    ``L(g)`` = :func:`srmech.physics.qm.quaternion.quaternion_left_mult` (Class-M bind,
    native-dispatched); ``conj`` = :func:`srmech.physics.qm.quaternion.quaternion_conjugate`
    (Class C).
    """
    from srmech.physics.qm.quaternion import quaternion_left_mult as _qlm
    from srmech.physics.qm.quaternion import quaternion_conjugate as _qconj
    d = _QUATERNION_DIM
    dim = d * n
    L = [[0.0] * dim for _ in range(dim)]
    deg = [0.0] * n
    for (u, v), w, g in zip(el, wl, gl):
        u = int(u)
        v = int(v)
        hw = 0.5 * float(w)
        deg[u] += hw
        deg[v] += hw
        if u == v:
            continue  # self-loop: no off-diagonal block; the degree carries it
        lg = _qlm(g).tolist()               # 4×4 real: x → g·x
        lgc = _qlm(_qconj(g)).tolist()      # 4×4 real: x → conj(g)·x  (== lgᵀ)
        bu = d * u
        bv = d * v
        for a in range(d):
            for b in range(d):
                L[bu + a][bv + b] += -(hw * lg[a][b])
                L[bv + a][bu + b] += -(hw * lgc[a][b])
    for r in range(n):
        base = d * r
        dval = deg[r]
        for a in range(d):
            L[base + a][base + a] += dval
    return L


def quaternion_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    gains: Optional[Iterable[Sequence[float]]] = None,
) -> "Mat":
    """Quaternion (ℍ) gain Laplacian of a graph — the ASSOCIATIVE dim-4 rung of
    :func:`magnetic_laplacian` (the ℂ dim-2 complex-unit-gain Laplacian).

    Each edge ``(u, v)`` carries a unit-quaternion **gain** ``g ∈ Sp(1)``; the
    ``4n×4n`` **real-symmetric** matrix is assembled block-wise from the 4×4
    real left-multiplication rep ``L(g)``
    (:func:`srmech.physics.qm.quaternion.quaternion_left_mult`):

    * off-diagonal block ``(u, v) = −(w/2)·L(g)`` and
      ``(v, u) = −(w/2)·L(conj g) = −(w/2)·L(g)ᵀ`` (Hermitian-analogue —
      real-SYMMETRIC by construction, since ``L(conj g) == L(g)ᵀ``);
    * diagonal block ``(r, r) = (Σ_incident w/2)·I₄`` — the magnitude degree,
      the same ``w/2`` scale :func:`magnetic_laplacian`'s per-edge charge mode
      uses.

    Feed the result to :func:`mat_hermitian_eigendecompose` (a real-symmetric
    ``Mat`` is a Hermitian ``Mat``). TWO spectral facts:

    * **Gauge-invariant spectrum** — a node-wise unit-quaternion gauge
      ``s_u ∈ Sp(1)`` (mapping ``g_uv → s_u·g_uv·conj(s_v)``) conjugates the
      matrix by the ORTHOGONAL block-diagonal ``diag(L(s_u))``, so the
      eigenvalues are unchanged (proven ~3.3e-15). The ℍ generalisation of the
      complex-unit-gain U(1) gauge invariance.
    * **×4 degeneracy (THEOREM)** — ℍ is associative, so left- and
      right-multiplication commute; the left-built matrix commutes with the
      fixed right-ℍ action (the Sp(1) commutant), forcing EVERY eigenvalue to a
      multiplicity that is a multiple of 4. **Callers dedupe by taking every
      4th eigenvalue.** Split the eigenvectors into channels with
      :func:`hypercomplex_perspectives` (``dim=4``).

    ``gains=None`` (default) puts the identity gain ``e0`` on every edge — the
    undirected control ``½·(dense graph Laplacian) ⊗ I₄``. A supplied gain is
    normalised to ``Sp(1)`` via the Class-K+Class-C
    :func:`srmech.physics.qm.quaternion.quaternion_norm` (never ``abs()``).

    Numpy-free; **Class L** composing **Class-M** ``quaternion_left_mult`` atoms
    (native-dispatched to ``srmech_quaternion_left_mult``; ``conj`` is Class C).
    No new C symbol — a bare-C host assembles this matrix and eigendecomposes it
    (ABI stays 10). Attested SSoT (DERIVED, complex-unit-gain framing one
    Cayley–Dickson rung up): N. Reff, "Spectral Properties of Complex Unit Gain
    Graphs", Linear Algebra Appl. 436 (2012) 3165–3176 (arXiv:1110.4554); the
    ℍ gain algebra is Baez, J.C. (2002) *The Octonions* (arXiv:math/0105155) §1
    at dim 4.

    Args:
        n: Node count (non-negative int).
        edges: Iterable of ``(u, v)`` endpoint pairs (``0 ≤ u, v < n``).
        weights: Optional per-edge magnitudes (default all ``1.0``); length must
            match ``edges``.
        gains: Optional per-edge unit quaternions (4-vectors) parallel to
            ``edges``; default the identity gain ``(1, 0, 0, 0)`` on every edge.
            Each is normalised to ``Sp(1)``.

    Returns:
        The ``4n×4n`` real-symmetric quaternion gain Laplacian as a
        :class:`~srmech.math.mat.Mat` (``.shape == (4n, 4n)``, real layout).

    Raises:
        ValueError: bad ``n`` / out-of-range endpoint / weights-length mismatch
            / gains-length mismatch / a non-4-vector or zero-norm gain.
    """
    el, wl = _validate_edges_weights_py(n, edges, weights)
    gl = _resolve_quaternion_gains(el, gains)
    rows = _quaternion_laplacian_blocks(n, el, wl, gl)
    return Mat.from_rows(rows, is_complex=False)


# =====================================================================
# rc384 (`#T957`) — the 𝕆 (NON-associative) sibling of quaternion_laplacian:
# the OCTONION gain Laplacian, the Class-L instrument that MEASURES 𝕆's
# frame-committed coherence CEILING by a shipped op.
# =====================================================================
#
# octonion_laplacian is the ℍ→𝕆 rung of quaternion_laplacian: an 8n×8n
# REAL-SYMMETRIC matrix whose (u, v) block is the 8×8 real left-multiplication
# rep L(g_uv) of a unit-octonion gain, with the (v, u) block L(conj g_uv) ==
# L(g_uv)ᵀ (symmetric BY CONSTRUCTION — MEASURED max|L(conj g)−L(g)ᵀ| = 0, a
# composition-algebra fact that survives to 𝕆). But the TWO spectral facts that
# held at ℍ DO NOT survive the doubling seam — and that failure IS the point:
#
#   * GAUGE INVARIANCE FAILS. A node-wise unit-octonion gauge s_u maps
#     g_uv → s_u·g_uv·conj(s_v); at ℍ (associative) that conjugates the matrix
#     by the ORTHOGONAL block-diagonal diag(L(s_u)) because L(s·g) == L(s)·L(g),
#     so the spectrum is fixed (~1e-15). At 𝕆 L is NOT a homomorphism —
#     L(s·g) ≠ L(s)·L(g) in general (non-associativity) — so the gauge move does
#     NOT conjugate the matrix orthogonally and the spectrum MOVES. MEASURED
#     (octonion_frame_read_rc384.py): a triangle deviates ~0.21, a 4-cycle ~0.06,
#     versus the shipped quaternion_laplacian's ~1e-15 Sp(1)-invariance on the
#     same experiment. This is §3.41's "no frame-free invariant" (F1301/F1302)
#     made operational: there is no gauge-invariant scalar spectrum at 𝕆.
#   * NO ×8 DEGENERACY THEOREM. ℍ's ×4 degeneracy is a THEOREM (associativity →
#     left/right multiplication COMMUTE → the left-built matrix commutes with the
#     fixed right action). 𝕆 is non-associative, left and right multiplication do
#     NOT commute, so NO multiplicity theorem holds — callers must NOT dedupe by
#     taking every 8th eigenvalue (the single-edge ×8 blocks are trivial rank
#     structure, not a spectral degeneracy).
#
# The frame-COMMITTED coherence that DOES survive at 𝕆 is not spectral — it is
# the ℍ-valued quaternionic-Hopf base read by
# :func:`srmech.cascade.octonion_frame_read` (frame-free UNDER the S³ fiber).
# The two ops together ARE the ceiling: the frame-read recovers the coherent
# note; this Laplacian MEASURES that it does NOT lift to a gauge-invariant
# spectrum. FORM, not identity.
#
# CLASS: **Class L** (graph spectral) composing **Class-M** atoms
# (:func:`srmech.physics.qm.octonion.octonion_left_mult`); the gain conjugate is
# **Class C** (:func:`srmech.physics.qm.octonion.octonion_conjugate`) and the
# gain normalisation is **Class K + Class C**
# (:func:`srmech.physics.qm.octonion.octonion_norm` — an exact 8-vector hypot,
# NEVER an ALU ``abs()``). Attested SSoT (DERIVED — the complex-unit-gain framing
# two Cayley–Dickson rungs up): N. Reff, "Spectral Properties of Complex Unit
# Gain Graphs", Linear Algebra Appl. 436 (2012) 3165–3176 (arXiv:1110.4554); the
# 𝕆 gain algebra + the associator seam-confinement are Baez, J.C. (2002) *The
# Octonions* (arXiv:math/0105155) §2. The op composes SHIPPED atoms only —
# ``octonion_left_mult`` → ``srmech_loop_left_op_f64`` and
# ``mat_hermitian_eigendecompose`` → ``srmech_hermitian_eigendecompose_ws`` — so
# a bare-C host assembles the matrix and eigendecomposes (honest C parity; no new
# C symbol, ABI stays 10).

_OCTONION_DIM = 8
_OCTONION_IDENTITY_GAIN: Tuple[float, ...] = (1.0, 0.0, 0.0, 0.0,
                                              0.0, 0.0, 0.0, 0.0)


def _resolve_octonion_gains(
    el: List[Tuple[int, int]],
    gains: Optional[Iterable[Sequence[float]]],
) -> List[List[float]]:
    """Resolve ``gains`` to one UNIT octonion (8-vector) per edge.

    ``gains=None`` → the identity gain ``e0`` on every edge (``L(e0) = I₈``, so
    the build collapses to ``½·(dense graph Laplacian) ⊗ I₈``). A supplied gain
    is normalised to the unit sphere via the **Class-K + Class-C**
    :func:`srmech.physics.qm.octonion.octonion_norm` (exact 8-vector hypot, never
    ``abs()``); a zero-norm gain raises. Resolved ONCE per public call so the
    assembly consumes identical floats.
    """
    from srmech.physics.qm.octonion import octonion_norm as _onorm
    if gains is None:
        return [list(_OCTONION_IDENTITY_GAIN) for _ in el]
    gl = [[float(c) for c in g] for g in gains]
    if len(gl) != len(el):
        raise ValueError(f"gains length {len(gl)} != n_edges {len(el)}")
    out: List[List[float]] = []
    for k, g in enumerate(gl):
        if len(g) != _OCTONION_DIM:
            raise ValueError(
                f"gain {k} must be an 8-vector octonion; got length {len(g)}")
        nrm = _onorm(g)
        if nrm == 0.0:
            raise ValueError(f"gain {k} must be a non-zero octonion")
        inv = 1.0 / nrm
        out.append([c * inv for c in g])
    return out


def _octonion_laplacian_blocks(
    n: int,
    el: List[Tuple[int, int]],
    wl: List[float],
    gl: List[List[float]],
) -> List[List[float]]:
    """Assemble the ``8n×8n`` real-symmetric octonion gain Laplacian as a nested
    ``list[list[float]]`` (numpy-free).

    Per edge ``k = (u, v, w, g)`` (``g`` an already-unit octonion): the
    ``(u, v)`` block accumulates ``−(w/2)·L(g)``, the ``(v, u)`` block
    ``−(w/2)·L(conj g)`` — and ``L(conj g) == L(g)ᵀ`` for the octonion norm form
    (MEASURED exact), so the matrix is EXACTLY symmetric term by term. Each
    endpoint's diagonal block gains ``(w/2)·I₈``. ``L(g)`` =
    :func:`srmech.physics.qm.octonion.octonion_left_mult` (Class-M bind,
    native-dispatched); ``conj`` =
    :func:`srmech.physics.qm.octonion.octonion_conjugate` (Class C).
    """
    from srmech.physics.qm.octonion import octonion_left_mult as _olm
    from srmech.physics.qm.octonion import octonion_conjugate as _oconj
    d = _OCTONION_DIM
    dim = d * n
    L = [[0.0] * dim for _ in range(dim)]
    deg = [0.0] * n
    for (u, v), w, g in zip(el, wl, gl):
        u = int(u)
        v = int(v)
        hw = 0.5 * float(w)
        deg[u] += hw
        deg[v] += hw
        if u == v:
            continue  # self-loop: no off-diagonal block; the degree carries it
        lg = _olm(g).tolist()               # 8×8 real: x → g·x
        lgc = _olm(_oconj(g)).tolist()      # 8×8 real: x → conj(g)·x  (== lgᵀ)
        bu = d * u
        bv = d * v
        for a in range(d):
            for b in range(d):
                L[bu + a][bv + b] += -(hw * lg[a][b])
                L[bv + a][bu + b] += -(hw * lgc[a][b])
    for r in range(n):
        base = d * r
        dval = deg[r]
        for a in range(d):
            L[base + a][base + a] += dval
    return L


def octonion_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    gains: Optional[Iterable[Sequence[float]]] = None,
) -> "Mat":
    """Octonion (𝕆) gain Laplacian of a graph — the NON-ASSOCIATIVE dim-8 rung of
    :func:`quaternion_laplacian` (the ℍ dim-4 gain Laplacian) and the shipped
    instrument for measuring 𝕆's frame-committed coherence CEILING (rc384,
    `#T957`).

    Each edge ``(u, v)`` carries a unit-octonion **gain** ``g``; the ``8n×8n``
    **real-symmetric** matrix is assembled block-wise from the 8×8 real
    left-multiplication rep ``L(g)``
    (:func:`srmech.physics.qm.octonion.octonion_left_mult`):

    * off-diagonal block ``(u, v) = −(w/2)·L(g)`` and
      ``(v, u) = −(w/2)·L(conj g) = −(w/2)·L(g)ᵀ`` (real-SYMMETRIC by
      construction — ``L(conj g) == L(g)ᵀ`` for the octonion norm form, MEASURED
      exact; this composition-algebra fact survives to 𝕆);
    * diagonal block ``(r, r) = (Σ_incident w/2)·I₈`` — the magnitude degree.

    Feed the result to :func:`mat_hermitian_eigendecompose` (a real-symmetric
    ``Mat`` is a Hermitian ``Mat``).

    ⚠️ **THE CEILING — the ℍ spectral facts DO NOT survive the seam.** This op
    exists to MEASURE that, not to hide it:

    * **Gauge invariance FAILS at 𝕆.** A node-wise unit-octonion gauge (mapping
      ``g_uv → s_u·g_uv·conj(s_v)``) leaves the ℍ spectrum fixed (~1e-15) because
      ``L`` is a homomorphism there (associativity). At 𝕆 ``L`` is NOT a
      homomorphism — ``L(s·g) ≠ L(s)·L(g)`` (non-associativity) — so the gauge
      move does not conjugate the matrix orthogonally and the **spectrum MOVES**.
      MEASURED (``docs/srmech/notes/octonion_frame_read_rc384.py``): triangle
      deviation ``~0.21``, 4-cycle ``~0.06``, versus the shipped
      :func:`quaternion_laplacian`'s ``~1e-15`` on the same experiment. This is
      §3.41's "no frame-free invariant" (F1301/F1302) made operational.
    * **No ×8 degeneracy THEOREM.** ℍ's ×4 degeneracy is forced by
      associativity; 𝕆 is non-associative (left/right multiplication do not
      commute), so no multiplicity theorem holds. **Do NOT dedupe** by taking
      every 8th eigenvalue.

    The frame-committed coherence that DOES survive at 𝕆 is the ℍ-valued
    quaternionic-Hopf base of :func:`srmech.cascade.octonion_frame_read`
    (frame-free UNDER the S³ fiber, exact-ℚ). The two ops together are the
    ceiling: the frame-read recovers the coherent note, this Laplacian measures
    that it does not lift to a gauge-invariant spectrum. FORM, not identity
    (`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`).

    ``gains=None`` (default) puts the identity gain ``e0`` on every edge — the
    undirected control ``½·(dense graph Laplacian) ⊗ I₈``. A supplied gain is
    normalised via the Class-K+Class-C
    :func:`srmech.physics.qm.octonion.octonion_norm` (never ``abs()``).

    Numpy-free; **Class L** composing **Class-M**
    :func:`srmech.physics.qm.octonion.octonion_left_mult` atoms
    (native-dispatched to ``srmech_loop_left_op_f64``; ``conj`` is Class C). No
    new C symbol — a bare-C host assembles this matrix and eigendecomposes it
    (ABI stays 10). Attested SSoT (DERIVED, gain-graph framing two Cayley–Dickson
    rungs up): N. Reff, "Spectral Properties of Complex Unit Gain Graphs", Linear
    Algebra Appl. 436 (2012) 3165–3176 (arXiv:1110.4554); the 𝕆 gain algebra +
    the associator seam-confinement are Baez, J.C. (2002) *The Octonions*
    (arXiv:math/0105155) §2.

    Args:
        n: Node count (non-negative int).
        edges: Iterable of ``(u, v)`` endpoint pairs (``0 ≤ u, v < n``).
        weights: Optional per-edge magnitudes (default all ``1.0``); length must
            match ``edges``.
        gains: Optional per-edge unit octonions (8-vectors) parallel to
            ``edges``; default the identity gain ``e0`` on every edge. Each is
            normalised to the unit sphere.

    Returns:
        The ``8n×8n`` real-symmetric octonion gain Laplacian as a
        :class:`~srmech.math.mat.Mat` (``.shape == (8n, 8n)``, real layout).

    Raises:
        ValueError: bad ``n`` / out-of-range endpoint / weights-length mismatch
            / gains-length mismatch / a non-8-vector or zero-norm gain.
    """
    el, wl = _validate_edges_weights_py(n, edges, weights)
    gl = _resolve_octonion_gains(el, gains)
    rows = _octonion_laplacian_blocks(n, el, wl, gl)
    return Mat.from_rows(rows, is_complex=False)


#: The hypercomplex channel names, ``e0`` (scalar) + the imaginary axes.
_HYPERCOMPLEX_CHANNELS: Tuple[str, ...] = ("e0", "e1", "e2", "e3")


def hypercomplex_perspectives(eigvecs: "Mat", dim: int = 4) -> Dict:
    """Split each eigenvector into a scalar channel ``e0`` + ``(dim−1)``
    imaginary phase channels — the hypercomplex reader for
    :func:`quaternion_laplacian` (``dim=4``, ℍ, ``4 = 1 + 3``) that ALSO closes
    the latent dim-2 read of :func:`magnetic_laplacian` (``dim=2``, ℂ,
    ``2 = 1 + 1``).

    ``eigvecs`` is the ``(N×M)`` eigenvector :class:`~srmech.math.mat.Mat` whose
    COLUMNS are eigenvectors (the second return of
    :func:`mat_hermitian_eigendecompose`). ``dim`` is the number of real
    components per hypercomplex unit:

    * ``dim=1`` (ℝ) — each real entry is a scalar; one channel ``e0``, no phase.
    * ``dim=2`` (ℂ) — each COMPLEX entry is one hypercomplex number: ``e0`` its
      real (scalar) part, ``e1`` its imaginary (phase) part. The
      :func:`magnetic_laplacian` read — the complex eigenvector's latent
      two-channel view.
    * ``dim=4`` (ℍ) — each consecutive block of 4 REAL entries is one quaternion
      at one node: ``e0`` the scalar, ``(e1, e2, e3)`` the three imaginary axes.
      The :func:`quaternion_laplacian` read — the ``4n``-real eigenvector's
      ``n``-quaternion view (``mat_hermitian_eigendecompose`` returns a complex
      carrier even for a real-symmetric input, so the real part is taken).

    **Class L** (spectral read-out — a pure structural split of an already-
    decomposed carrier; no cascade math).

    Args:
        eigvecs: The ``(N, M)`` eigenvector ``Mat`` (columns = eigenvectors).
        dim: Real components per hypercomplex unit — 1 (ℝ), 2 (ℂ) or 4 (ℍ).

    Returns:
        A ``dict`` with keys ``dim``, ``n_vectors`` (``M``), ``n_blocks`` (the
        hypercomplex units per eigenvector), ``channel_names`` (``["e0", …]``
        length ``dim``), and ``vectors`` — one ``dict`` per eigenvector mapping
        each channel name to a length-``n_blocks`` ``list[float]``.

    Raises:
        TypeError: ``eigvecs`` is not a ``Mat``.
        ValueError: ``dim`` not in ``{1, 2, 4}``; or (``dim`` in ``{1, 4}``) the
            eigenvector length ``N`` is not a multiple of ``dim``.
    """
    if not isinstance(eigvecs, Mat):
        raise TypeError(
            "hypercomplex_perspectives: eigvecs must be a Mat (the eigenvector "
            f"carrier); got {type(eigvecs).__name__}")
    if dim not in (1, 2, 4):
        raise ValueError(f"dim must be 1 (R), 2 (C) or 4 (H); got {dim!r}")
    n_rows = eigvecs.n_rows
    n_vectors = eigvecs.n_cols
    names = list(_HYPERCOMPLEX_CHANNELS[:dim])
    vectors: List[Dict[str, List[float]]] = []
    if dim == 2:
        # Each complex entry IS one hypercomplex number: e0 = re, e1 = im.
        n_blocks = n_rows
        for j in range(n_vectors):
            e0 = [0.0] * n_rows
            e1 = [0.0] * n_rows
            for i in range(n_rows):
                z = complex(eigvecs[i, j])
                e0[i] = z.real
                e1[i] = z.imag
            vectors.append({"e0": e0, "e1": e1})
    else:
        # dim in {1, 4}: the real component of each entry, grouped in blocks.
        if n_rows % dim != 0:
            raise ValueError(
                f"hypercomplex_perspectives: eigenvector length {n_rows} is not "
                f"a multiple of dim={dim}")
        n_blocks = n_rows // dim
        for j in range(n_vectors):
            reals = [complex(eigvecs[i, j]).real for i in range(n_rows)]
            chans: Dict[str, List[float]] = {
                name: [0.0] * n_blocks for name in names}
            for b in range(n_blocks):
                base = b * dim
                for c in range(dim):
                    chans[names[c]][b] = reals[base + c]
            vectors.append(chans)
    return {
        "dim": dim,
        "n_vectors": n_vectors,
        "n_blocks": n_blocks,
        "channel_names": names,
        "vectors": vectors,
    }


# =====================================================================
# rc229 (#687) — the fuller asymmetric-halves lattice handle: the V4-gain
# (Klein-4-sector) Laplacian (EVEN channel) + cycle_holonomy (ODD channel).
# =====================================================================
#
# magnetic_laplacian is a ONE-axis, chirality-EVEN U(1) projection: flipping
# ALL chirality conjugates the matrix entrywise, and Hermitian spectra are
# conjugation-invariant, so NO eigenvalue read can carry the which-way sign
# (F552 "diagnostic, not predictive"). The fuller object has FOUR real
# character sectors (the EVEN channel, klein4_gain_laplacian) + the cycle
# holonomies (the ODD channel, cycle_holonomy that the spectrum provably
# cannot carry). Together they make the relational read complete.

# The four V4 = Z2 x Z2 characters, keyed χ_ab(g0,g1) = (−1)^(a·g0 + b·g1).
# Sector index k = 2·a + b (matches the C sector-major layout): k=0 → chi00
# (trivial), 1 → chi01, 2 → chi10, 3 → chi11. The two gain bits are treated
# SYMMETRICALLY — neither is privileged (the phase-vs-beat semantic binding is
# a framework decision reserved for the user; the math is bit-symmetric).
_KLEIN4_SECTORS: Tuple[str, ...] = ("chi00", "chi01", "chi10", "chi11")


def _klein4_char_sign(a: int, b: int, g: int) -> int:
    """χ_ab(g) ∈ {+1, −1}: the parity of (a & g0) ^ (b & g1), g = (g1<<1)|g0.
    A Class-K sign (pin-slot), never an ALU magnitude."""
    g0 = g & 1
    g1 = (g >> 1) & 1
    return -1 if ((a & g0) ^ (b & g1)) else 1


def _normalize_gains_py(gains, n_edges: int) -> List[int]:
    """Validate a per-edge V4 gain list parallel to the edges: each entry an
    int in {0,1,2,3} (two sign bits, low..high) or a 2-tuple/2-list ``(g0, g1)``
    of bits. ``gains=None`` → all identity (0). Raises ``ValueError`` on a bad
    length or an out-of-range gain."""
    if gains is None:
        return [0] * n_edges
    out: List[int] = []
    for k, g in enumerate(gains):
        if isinstance(g, (tuple, list)):
            if len(g) != 2:
                raise ValueError(
                    f"gain {k} = {g!r} must be a 2-tuple (g0, g1) of bits"
                )
            g0, g1 = int(g[0]) & 1, int(g[1]) & 1
            gi = (g1 << 1) | g0
        else:
            gi = int(g)
        if gi < 0 or gi > 3:
            raise ValueError(
                f"gain {k} = {g!r} out of range: a V4 gain is an int in "
                f"{{0,1,2,3}} (two sign bits) or a 2-tuple of bits"
            )
        out.append(gi)
    return out


def _klein4_gain_laplacian_native(n, el, wl, gl):
    """numpy-free native dispatch for :func:`klein4_gain_laplacian` — marshals
    the edge endpoints (uint32), weights (double) and per-edge gains (uint8)
    into ctypes buffers and calls ``srmech_graph_klein4_gain_laplacian`` with a
    caller-allocated ``4*n*n``-double sector-major output. Returns a list of
    four nested ``list[list[float]]`` sector Laplacians, or ``None`` on a
    missing symbol / non-OK status (caller runs the pure-Python cascade)."""
    if not _native.has_native_klein4_gain_laplacian():
        return None
    n_edges = len(el)
    block = n * n
    out = (ctypes.c_double * (4 * block))()
    null_u = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32))
    null_d = ctypes.cast(None, ctypes.POINTER(ctypes.c_double))
    null_b = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
    if n_edges:
        eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in el))
        ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in el))
        wb = (ctypes.c_double * n_edges)(*(float(w) for w in wl))
        gb = (ctypes.c_uint8 * n_edges)(*(int(g) for g in gl))
    else:
        eu = ev = null_u
        wb = null_d
        gb = null_b
    rc = _native.LIB.srmech_graph_klein4_gain_laplacian(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, wb, gb, out
    )
    if rc != _native.SRMECH_OK:
        return None
    return [
        [[out[k * block + r * n + c] for c in range(n)] for r in range(n)]
        for k in range(4)
    ]


def _klein4_gain_laplacian_py(n, el, wl, gl):
    """Pure-Python complete alternative for :func:`klein4_gain_laplacian`:
    build the four sector Laplacians as :func:`signed_laplacian` on the
    χ-transformed weights ``χ_ab(g_e)·w_e``. Since ``|χ·w| = |w|``, each
    sector's signed degree is identical — the four differ only by the
    off-diagonal signs. Returns four nested ``list[list[float]]``."""
    sectors = []
    for k in range(4):
        a, b = k >> 1, k & 1
        w_sec = [_klein4_char_sign(a, b, g) * float(w) for g, w in zip(gl, wl)]
        L = signed_laplacian(n, el, w_sec)  # Mat
        sectors.append([[L[i, j] for j in range(n)] for i in range(n)])
    return sectors


def klein4_gain_laplacian(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    gains: Optional[Iterable] = None,
) -> Dict[str, "Mat"]:
    """The V₄-gain (Klein-4-sector) Laplacian — the EVEN-channel fuller partner
    of :func:`magnetic_laplacian` (gh#687).

    Each edge carries a **V₄ = ℤ₂×ℤ₂ gain** = TWO sign bits (``gains`` parallel
    to ``edges``, each an int in ``{0,1,2,3}`` = ``(g1<<1)|g0`` or a 2-tuple
    ``(g0, g1)``; ``gains=None`` → all identity). V₄ has FOUR real characters
    ``χ_ab(g) = (−1)^(a·g0 + b·g1)``, so the object decomposes into FOUR real
    signed Laplacians ``L_χ = D̄ − χ(g_e)·A`` — the two-bit generalization of
    exactly how :func:`signed_laplacian` is the ℤ₂ (one-bit) instance. The two
    gain bits are handled **symmetrically** — no bit is privileged (the
    phase-vs-beat semantic binding is a framework decision reserved for the
    user; the math is bit-symmetric).

    The signed degree ``D̄_ii = Σ_j |A_ij|`` is the **Class-K magnitude**
    (a sign-branch, never ``abs()``); since ``|χ·w| = |w|`` the degree is
    **character-independent**, so the four sectors differ only in their
    off-diagonal signs — ``L_χ00`` (the trivial character) equals
    :func:`dense_laplacian` for unit gains.

    The four sector Laplacians drop directly into
    :func:`spectral_block_dispatch` (its Klein-4 4-cap IS this shape); the
    joint read-out (per-sector tensions + the Class-K sector-asymmetry meter)
    is :func:`klein4_relational_structure`. **Honest boundary (F552):** a
    Laplacian whose *eigenvalues* carry the which-way sign is provably
    impossible (conjugation-invariance of Hermitian/real-symmetric spectra);
    this composite reads the ASYMMETRY (sectors differ), the ORIENTATION LABEL
    needs the ODD-channel :func:`cycle_holonomy` (diagnostic, not predictive).

    Attested SSoT: N. Reff, "Spectral Properties of Complex Unit Gain Graphs",
    Linear Algebra Appl. 436 (2012) 3165–3176 (arXiv:1110.4554); the abelian-
    cover character decomposition (the V₄-cover generalization of the Bilu–
    Linial ℤ₂ 2-lift, Combinatorica 26 (2006) 495–519, arXiv:math/0312022).

    Parameters
    ----------
    n : int
        Node count.
    edges : Iterable[Tuple[int, int]]
        Undirected relational edges ``(u, v)``.
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``); may be negative.
    gains : Optional[Iterable]
        Per-edge V₄ gains parallel to ``edges`` (int ``{0,1,2,3}`` or 2-tuple
        of bits); ``None`` → all identity (all four sectors coincide).

    Returns
    -------
    dict[str, Mat]
        ``{"chi00", "chi01", "chi10", "chi11"}`` → the four ``n×n`` real-
        symmetric PSD sector Laplacians (numpy-free :class:`~srmech.math.mat.Mat`).

    Dispatches to the standalone-C ``srmech_graph_klein4_gain_laplacian`` (all
    four sectors in one call) when ``HAS_NATIVE``; else four
    :func:`signed_laplacian` builds on the χ-transformed weights (byte-identical
    — integer sign × the same weights). numpy-free; no ``abs()``.
    """
    el, wl = _validate_edges_weights_py(n, edges, weights)
    gl = _normalize_gains_py(gains, len(el))
    rows = _klein4_gain_laplacian_native(n, el, wl, gl)
    if rows is None:
        rows = _klein4_gain_laplacian_py(n, el, wl, gl)
    return {
        _KLEIN4_SECTORS[k]: Mat.from_rows(rows[k], is_complex=False)
        for k in range(4)
    }


def klein4_relational_structure(
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    gains: Optional[Iterable] = None,
    *,
    n: Optional[int] = None,
) -> dict:
    """The joint EVEN-channel read-out of a V₄-gain relational graph (gh#687) —
    per-sector spectral tensions + the Class-K sector-asymmetry meter.

    Builds the four sector Laplacians (:func:`klein4_gain_laplacian`) and reads
    each with ONE :func:`symmetric_eigendecompose`::

        {"sectors": ("chi00","chi01","chi10","chi11"),
         "tension":   {sector: λ_min},   # spectral frustration (0 = balanced)
         "coherence": {sector: λ₂},      # algebraic connectivity (Fiedler value)
         "sector_asymmetry": |tension[chi10] − tension[chi01]|}

    ``tension`` is the smallest eigenvalue λ_min of each sector's signed
    Laplacian — 0 exactly when that sector is balanced (Kunegis et al. 2010),
    positive under frustration; ``coherence`` is the second-smallest eigenvalue
    λ₂. ``sector_asymmetry`` is the **Class-K magnitude** (a sign-branch, never
    ``abs()``) of the difference between the two MIXED sectors χ10/χ01 — the
    ``(4:3)|(3:4)`` sector-occupancy diagnostic (F552): a chirality-collapse
    deviation lands here, random noise does not. Diagnostic, not predictive —
    the orientation LABEL needs the ODD-channel :func:`cycle_holonomy`.

    Composes :func:`klein4_gain_laplacian` + :func:`symmetric_eigendecompose`
    (one eigensolve per sector) — a pure composition of the C-backed atoms, no
    dedicated C symbol. numpy-free.

    Parameters
    ----------
    edges, weights, gains
        As :func:`klein4_gain_laplacian`.
    n : Optional[int]
        Node count (keyword-only); inferred as one past the largest endpoint
        when ``None`` (isolated high-index nodes carry no relationship).

    Returns
    -------
    dict
        The per-sector tensions / coherences + the mixed-sector asymmetry.
    """
    edge_list = [tuple(e) for e in edges]
    nn = _infer_n_from_edges(edge_list) if n is None else int(n)
    if nn == 0:
        zero = {s: 0.0 for s in _KLEIN4_SECTORS}
        return {"sectors": _KLEIN4_SECTORS, "tension": dict(zero),
                "coherence": dict(zero), "sector_asymmetry": 0.0}
    _el, w_list = _validate_edges_weights_py(nn, edge_list, weights)
    sectors = klein4_gain_laplacian(nn, edge_list, w_list, gains)
    tension: Dict[str, float] = {}
    coherence: Dict[str, float] = {}
    for s in _KLEIN4_SECTORS:
        eigvals, _V = symmetric_eigendecompose(sectors[s])
        tension[s] = float(eigvals[0])                       # λ_min (frustration)
        coherence[s] = float(eigvals[1]) if nn >= 2 else 0.0  # λ₂ (connectivity)
    # Class-K magnitude of the mixed-sector (χ10 vs χ01) tension gap — the
    # (4:3)|(3:4) sector-occupancy diagnostic (a sign-branch, NOT abs()).
    d = tension["chi10"] - tension["chi01"]
    asym = d if d >= 0.0 else -d
    return {
        "sectors": _KLEIN4_SECTORS,
        "tension": tension,
        "coherence": coherence,
        "sector_asymmetry": asym,
    }


def _to_fraction(c) -> Q:
    """Coerce a charge (turns) to an exact :class:`~srmech.math.q.Q` (#845: the
    exact-ℚ carrier, was ``fractions.Fraction``). Accepts an ``int`` / a
    ``numbers.Rational`` carrier (a srmech ``Q``, a stdlib ``fractions.Fraction``)
    exactly; a ``float`` is projected to denominator ≤ 10¹² via the Class-N
    ``best_rational`` (the old ``Fraction(x).limit_denominator(10**12)`` — dyadic
    floats like 0.25 stay exact, ``to_q(0.25) == 1/4`` needs no snap)."""
    if isinstance(c, float):
        # signed float→ℚ snap (the old Fraction(x).limit_denominator(10**12)):
        # the SIGNED Class-K∘N∘C cascade handles a NEGATIVE charge (turns can be
        # negative), which the bare Class-N best_rational rejects. Function-local
        # import — cascade/__init__ imports this module, so a top-level import
        # would cycle.
        from srmech.cascade import best_rational_signed as _brs
        return Q.from_pair(_brs(c, max_denominator=10 ** 12))
    return to_q(c)                                      # int / Fraction / Q / Rational — exact


def _cycle_holonomy_py(n, edge_list, charges):
    """Pure-Python complete alternative for :func:`cycle_holonomy` — exact
    :class:`~fractions.Fraction` arithmetic (the odd channel). Spanning forest
    by union-find (first-encountered edge = tree edge), pot[i] = tree-path
    charge (root → i), holonomy(u,v,c) = c + pot[u] − pot[v] mod 1. Returns
    ``(holonomies, cycle_edges)`` — the SAME spanning-tree choice as the C peer
    (identical edge order → identical fundamental-cycle basis)."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree: List[Tuple[int, int, Q]] = []
    cotree: List[Tuple[int, int, Q]] = []
    for (u, v), c in zip(edge_list, charges):
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[rv] = ru
            tree.append((u, v, c))
        else:
            cotree.append((u, v, c))
    # pot[i] = signed tree-path charge from the component root to i.
    pot: List[Optional[Q]] = [None] * n
    adj: List[List[Tuple[int, Q]]] = [[] for _ in range(n)]
    for (u, v, c) in tree:
        adj[u].append((v, c))     # u -> v : +c
        adj[v].append((u, -c))    # v -> u : -c
    for s in range(n):
        if pot[s] is not None:
            continue
        pot[s] = Q(0)
        stack = [s]
        while stack:
            x = stack.pop()
            for (y, c) in adj[x]:
                if pot[y] is None:
                    pot[y] = pot[x] + c
                    stack.append(y)
    holonomies: List[Q] = []
    cycle_edges: List[Tuple[int, int]] = []
    for (u, v, c) in cotree:
        h = c + pot[u] - pot[v]
        h = h - (h.numerator // h.denominator)   # mod 1 → [0, 1); Class-I cyclic
        holonomies.append(h)
        cycle_edges.append((u, v))
    return holonomies, cycle_edges


_HOLO_RAT_LIMIT = 10 ** 9  # matches SRMECH_HOLO_RAT_LIMIT in the C peer


def _cycle_holonomy_native(n, edge_list, charges):
    """numpy-free native dispatch for :func:`cycle_holonomy` — marshals the edge
    endpoints (uint32) + per-edge charge num/den (int64) into ctypes buffers and
    calls ``srmech_graph_cycle_holonomy`` with a caller arena sized from
    ``srmech_graph_cycle_holonomy_arena_bytes``. Returns
    ``(holonomies, cycle_edges)`` as exact ``Q`` + ``(u, v)`` pairs, or
    ``None`` on a missing symbol / non-OK status / an out-of-int64-range charge
    (caller then runs the exact pure-Python Q cascade)."""
    if not _native.has_native_cycle_holonomy():
        return None
    num: List[int] = []
    den: List[int] = []
    for c in charges:
        f = _to_fraction(c)
        an = f.numerator if f.numerator >= 0 else -f.numerator  # Class-K, no abs()
        if an > _HOLO_RAT_LIMIT or f.denominator > _HOLO_RAT_LIMIT:
            return None                       # out of int64 range → exact pure path
        num.append(f.numerator)
        den.append(f.denominator)
    n_edges = len(edge_list)
    eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in edge_list))
    ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in edge_list))
    cn = (ctypes.c_int64 * n_edges)(*num) if n_edges else \
        ctypes.cast(None, ctypes.POINTER(ctypes.c_int64))
    cd = (ctypes.c_int64 * n_edges)(*den) if n_edges else \
        ctypes.cast(None, ctypes.POINTER(ctypes.c_int64))
    onum = (ctypes.c_int64 * max(n_edges, 1))()
    oden = (ctypes.c_int64 * max(n_edges, 1))()
    ocu = (ctypes.c_uint32 * max(n_edges, 1))()
    ocv = (ctypes.c_uint32 * max(n_edges, 1))()
    ncyc = ctypes.c_uint32(0)
    ws_bytes = int(_native.LIB.srmech_graph_cycle_holonomy_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges)))
    ws = (ctypes.c_char * ws_bytes)()
    rc = _native.LIB.srmech_graph_cycle_holonomy(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, cn, cd,
        onum, oden, ocu, ocv, ctypes.byref(ncyc),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_bytes),
    )
    if rc != _native.SRMECH_OK:
        return None
    m = ncyc.value
    holonomies = [Q(int(onum[i]), int(oden[i])) for i in range(m)]
    cycle_edges = [(int(ocu[i]), int(ocv[i])) for i in range(m)]
    return holonomies, cycle_edges


def cycle_holonomy(
    edges: Iterable[Tuple[int, int]],
    charges: Optional[Iterable] = None,
    *,
    n: Optional[int] = None,
) -> dict:
    """The cycle holonomies of a gain graph — the ODD channel the (Hermitian /
    signed) SPECTRUM provably cannot carry (gh#687).

    A gain graph is determined up to switching (node re-gauging) by its cycle
    gains (Zaslavsky's switching theory). This computes them exactly: a
    **spanning forest** (union-find; first-encountered edge = tree edge) → the
    **fundamental cycle** for each co-tree edge → that cycle's **net charge**
    (per-edge ``charges`` in TURNS, exact :class:`~fractions.Fraction`, reduced
    **mod 1**). It is **Class I** (mod-1 cyclic) ∘ **Class L** (graph): exact
    integer/rational arithmetic, **NO eigensolve**.

    Why it is the odd channel: :func:`magnetic_laplacian`'s Hermitian spectrum
    is conjugation-invariant, so flipping all chirality leaves the eigenvalues
    fixed — the which-way ± sign is invisible to any spectral read (F552). The
    cycle holonomy is the gauge-invariant ODD datum: it is **invariant under
    node re-gauging** (a coboundary telescopes around any cycle), is **0 for
    every cycle IFF the gain graph is balanced** (Zaslavsky's balance
    criterion), and **distinguishes +c from −c** (``1/4`` vs ``3/4`` mod 1) —
    the chirality the sector spectra cannot. Honest boundary: it detects
    which-way *relative to a chosen base gauge*, not absolutely (the absolute
    orientation label still needs an external frame anchor — F552's diagnostic-
    not-predictive ceiling).

    Pairs with :func:`klein4_gain_laplacian` to make the relational read
    complete: the sector spectra are the EVEN channel, the holonomies the ODD.
    Attested SSoT: T. Zaslavsky, "Signed graphs", Discrete Appl. Math. 4 (1982)
    47–74.

    Parameters
    ----------
    edges : Iterable[Tuple[int, int]]
        The graph edges ``(u, v)``. A parallel edge closes a digon cycle; a
        self-loop is a 1-cycle carrying its own charge.
    charges : Optional[Iterable]
        Per-edge charge in TURNS parallel to ``edges`` (int / ``Q`` /
        rational carrier exact; a ``float`` projected via ``limit_denominator``).
        ``None`` → all 0 (a trivially balanced graph). ``(u, v, c) ≡ (v, u, −c)``.
    n : Optional[int]
        Node count (keyword-only); inferred as one past the largest endpoint
        when ``None``.

    Returns
    -------
    dict
        ``{"n_cycles": int, "holonomies": list[Q], "cycle_edges":
        list[(u, v)], "balanced": bool}`` — one holonomy in ``[0, 1)`` per
        fundamental cycle (indexed by its co-tree edge), and ``balanced`` iff
        every holonomy is 0.

    Dispatches to the standalone-C ``srmech_graph_cycle_holonomy`` (exact int64
    rational, caller-arena) when ``HAS_NATIVE`` and every charge is within the
    int64 range; else srmech's own exact-``Q`` cascade (the complete
    alternative — never a wrong answer, and it handles any denominator). The
    two paths use the SAME spanning-tree choice, so the fundamental-cycle basis
    is identical. numpy-free; no ``abs()``.
    """
    edge_list = [tuple(e) for e in edges]
    nn = _infer_n_from_edges(edge_list) if n is None else int(n)
    if charges is None:
        ch = [Q(0)] * len(edge_list)
    else:
        ch = [_to_fraction(c) for c in charges]
        if len(ch) != len(edge_list):
            raise ValueError(
                f"charges length {len(ch)} != n_edges {len(edge_list)}"
            )
    for k, (u, v) in enumerate(edge_list):
        if not (0 <= u < nn and 0 <= v < nn):
            raise ValueError(
                f"edge {k} = ({u}, {v}) outside node range [0, {nn})"
            )
    if nn == 0:
        return {"n_cycles": 0, "holonomies": [], "cycle_edges": [],
                "balanced": True}
    res = _cycle_holonomy_native(nn, edge_list, ch)
    if res is None:
        res = _cycle_holonomy_py(nn, edge_list, ch)
    holonomies, cycle_edges = res
    balanced = all(h == 0 for h in holonomies)
    return {
        "n_cycles": len(holonomies),
        "holonomies": holonomies,
        "cycle_edges": cycle_edges,
        "balanced": balanced,
    }


# =====================================================================
# rc108 (#1234 Item 2 / F1007) — the spectral theta / heat trace
# Θ(t) = Tr(e^{−tL}) = Σₖ e^{−t·λₖ} + the ground-state flux reader.
# =====================================================================


def _finite_real(x: float) -> bool:
    """True iff ``x`` is a finite float — ``x − x == 0`` (NaN fails ``x == x``;
    ±Inf fails ``Inf − Inf == 0``). No ``math.isfinite`` import
    (``[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]``)."""
    return x == x and x - x == 0.0


def _heat_trace_native(flat, n: int, is_complex: bool, t_list):
    """numpy-free native dispatch for :func:`heat_trace` — marshals the flat
    matrix buffer (real row-major, or interleaved-complex) + the t-values into
    ctypes ``double`` buffers and calls the composite C peer
    ``srmech_heat_trace`` with a caller arena sized from
    ``srmech_heat_trace_arena_bytes``. Returns the ``list[float]`` Θ values, or
    ``None`` on any missing symbol / non-OK status (caller then runs the
    pure-Python complete alternative)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_heat_trace")
        and hasattr(_native.LIB, "srmech_heat_trace_arena_bytes")
    ):
        return None
    L_c = (ctypes.c_double * len(flat))(*flat)
    n_t = len(t_list)
    tb = (ctypes.c_double * n_t)(*t_list)
    out = (ctypes.c_double * n_t)()
    ws_bytes = _native.LIB.srmech_heat_trace_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0)
    )
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_heat_trace(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0), L_c,
        ctypes.c_uint32(n_t), tb, out, ws, ctypes.c_size_t(wsd * 8),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [out[i] for i in range(n_t)]


def _heat_trace_py(rows, is_complex: bool, t_list):
    """The pure-Python complete alternative for :func:`heat_trace` — the ONE
    eigensolve (:func:`jacobi_eigvals` real / :func:`hermitian_eigendecompose`
    Hermitian, both srmech's own Class-L cascades) then
    ``Θ(t) = Σₖ float(rational.exp(−t·λₖ))`` summed in ascending-λ order (the
    Class-N Q61 exp cascade — the same cascade the C peer's ``srmech_exp``
    runs, so the exp step matches value-for-value given the same spectrum)."""
    if is_complex:
        eigvals, _V = hermitian_eigendecompose(rows)
        lam = [float(eigvals[i]) for i in range(eigvals.shape[0])]
    else:
        # A real-VALUED matrix may still carry complex-typed entries (a
        # complex-layout Mat with imag == 0) — coerce to the real part
        # before the real Jacobi (which floats every entry).
        real_rows = [[float(x.real if isinstance(x, complex) else x)
                      for x in r] for r in rows]
        ev = jacobi_eigvals(real_rows)
        lam = [float(ev[i]) for i in range(ev.shape[0])]
    return [sum(float(_rexp(-(tv * lk))) for lk in lam) for tv in t_list]


# ── #1390 item 3: eulerian_path / eulerian_circuit ──────────────────────────
# The Hierholzer walk-reconstruction the directed Class-L genome store recovers
# an ordered sequence with (the sandroing/word round-trip). Faithful port of
# R-RBS-LM-EULERWALK: a node-agnostic Eulerian trail / circuit over a DIRECTED
# edge multiset. Feasibility is CHECKED (degree balance + full-edge-consumption
# connectivity) — an infeasible graph returns None, never a partial walk.
# Deterministic (adjacency consumed from the END — the pop() order). The C peer
# srmech_eulerian_walk mirrors it byte-for-byte for integer nodes [0, n).

_NO_NATIVE_EULER = object()


def _eulerian_degrees(edges):
    """(outs, outdeg, indeg, nodes) — the per-node out-lists (edge order) +
    out/in degrees + the node set. Nodes may be any hashable."""
    outs, outdeg, indeg, nodes = {}, {}, {}, set()
    for u, v in edges:
        outs.setdefault(u, []).append(v)
        outdeg[u] = outdeg.get(u, 0) + 1
        indeg[v] = indeg.get(v, 0) + 1
        nodes.add(u)
        nodes.add(v)
    return outs, outdeg, indeg, nodes


def _eulerian_native(edges, start, circuit_only):
    """Dispatch to the C peer when nodes are non-negative ints. Returns the walk
    (list), ``None`` (infeasible), or the ``_NO_NATIVE_EULER`` sentinel (native
    absent / non-int nodes → the pure body runs)."""
    if not _native.has_native_eulerian():
        return _NO_NATIVE_EULER
    try:
        n_nodes = 0
        for u, v in edges:
            if (not isinstance(u, int) or not isinstance(v, int)
                    or isinstance(u, bool) or isinstance(v, bool)
                    or u < 0 or v < 0):
                return _NO_NATIVE_EULER
            n_nodes = max(n_nodes, u + 1, v + 1)
        s = -1
        if start is not None:
            if (not isinstance(start, int) or isinstance(start, bool)
                    or start < 0 or start >= n_nodes):
                return _NO_NATIVE_EULER            # pure handles the odd start
            s = start
        return _native.eulerian_walk_c(edges, n_nodes, s, bool(circuit_only))
    except Exception:
        return _NO_NATIVE_EULER


def eulerian_path(edges, start=None):
    """The Eulerian trail of a DIRECTED edge multiset ``[(u, v), ...]`` (repeats
    / self-loops ok; nodes any hashable) as a node list of length
    ``len(edges)+1``, or ``None`` if no single Eulerian trail exists (#1390
    item 3). Feasibility is CHECKED (degree balance + full-consumption
    connectivity). Deterministic start: the +1 out-degree node (path) or the min
    out-bearing node (circuit; ``start`` overrides). O(|E|) Hierholzer; the C
    peer ``srmech_eulerian_walk`` is byte-identical for integer nodes."""
    edges = [tuple(e) for e in edges]
    if not edges:
        return [start] if start is not None else []
    native = _eulerian_native(edges, start, circuit_only=False)
    if native is not _NO_NATIVE_EULER:
        return native
    outs, outdeg, indeg, nodes = _eulerian_degrees(edges)
    plus = [n for n in nodes if outdeg.get(n, 0) - indeg.get(n, 0) == 1]
    minus = [n for n in nodes if indeg.get(n, 0) - outdeg.get(n, 0) == 1]
    imbalanced = [n for n in nodes if outdeg.get(n, 0) != indeg.get(n, 0)]
    if not imbalanced:                                  # EULERIAN CIRCUIT
        s = start if start is not None else min(
            n for n in nodes if outdeg.get(n, 0) > 0)
    elif len(plus) == 1 and len(minus) == 1 and len(imbalanced) == 2:
        s = plus[0]                                     # EULERIAN PATH: forced start
    else:
        return None                                     # no Eulerian trail
    avail = {n: list(v) for n, v in outs.items()}       # consume EVERY edge once
    stack, walk = [s], []
    while stack:
        v = stack[-1]
        if avail.get(v):
            stack.append(avail[v].pop())                # pop the END (determinism)
        else:
            walk.append(stack.pop())
    walk.reverse()
    if len(walk) != len(edges) + 1:                     # not all edges consumed
        return None                                     # -> DISCONNECTED
    return walk


def eulerian_circuit(edges, start=None):
    """As :func:`eulerian_path` but REQUIRES a closed circuit (every node
    balanced): returns a walk with ``start == end``, or ``None`` if the graph is
    not balanced + connected (#1390 item 3)."""
    edges = [tuple(e) for e in edges]
    if not edges:
        return [start] if start is not None else []
    native = _eulerian_native(edges, start, circuit_only=True)
    if native is not _NO_NATIVE_EULER:
        return native
    _outs, outdeg, indeg, nodes = _eulerian_degrees(edges)
    if any(outdeg.get(n, 0) != indeg.get(n, 0) for n in nodes):
        return None                                     # not balanced -> no circuit
    return eulerian_path(edges, start=start)


# ── #1390 item 4: recover_check (+ the F1227 structural / spectral split) ────
# The packaged round-trip integrity check for a stored directed Class-L graph.
# Faithful port of R-RBS-LM-RECOVERCHECK (the four faculties) + the F1227
# corpus-scale split (R-RBS-LM-SIONA231): the dense op / responsion faculties do
# not scale past the native n<=256 wall, so the full recover_check (bounded) is
# joined by recover_check_structural (sparse, O(edges), any scale) +
# recover_check_spectral (op / responsion on a BOUNDED principal submatrix). A
# domain-free composition of shipped C-routed ops (dense_laplacian /
# symmetric_eigendecompose / magnetic_laplacian / responsion / cycle_holonomy):
# composition_of_c, no new C symbol. numpy-free; no abs() (Class-K magnitude).

_RECOVER_TOL = Q(1, 10 ** 9)


def _recover_mag(x):
    """Class-K real magnitude (NOT the abs builtin)."""
    return x if x >= 0 else -x


def _recover_op_spectral(dim, edges, weights):
    """The ``op`` faculty on ``dim`` nodes: L = D − A eigendecomposes (PSD, a ~0
    null mode, len == dim). Returns ``(op_bool, diag_updates)``."""
    diag = {}
    try:
        lap = dense_laplacian(dim, edges, [float(w) for w in weights])
        evals, _v = symmetric_eigendecompose(lap)
        ev = sorted(float(x) for x in evals)
        diag["n_modes"] = len(ev)
        diag["eig_range"] = (round(ev[0], 6), round(ev[-1], 6))
        psd = ev[0] > -1e-9
        # signed float→ℚ snap of the smallest eigenvalue (which can be slightly
        # NEGATIVE for a near-zero mode — see the psd guard above): the SIGNED
        # Class-K∘N∘C cascade, since the bare Class-N best_rational rejects a
        # negative numerator. Function-local import to avoid the cascade cycle.
        from srmech.cascade import best_rational_signed as _brs
        zero_mode = _recover_mag(Q.from_pair(
            _brs(ev[0], max_denominator=10 ** 6))) < _RECOVER_TOL
        return (len(ev) == dim and psd and zero_mode), diag
    except Exception as e:                          # a malformed op fails HONESTLY
        diag["op_error"] = "%s: %s" % (type(e).__name__, e)
        return False, diag


def _recover_responsion(dim, edges, weights, charges):
    """The ``responsion`` faculty on ``dim`` nodes: the propagator e^{−zL} is
    excitable (reach > 0). Returns ``(responsion_bool, diag_updates)``."""
    diag = {}
    try:
        mx = max((float(w) for w in weights), default=1.0) * max(dim, 1)
        lm = magnetic_laplacian(dim, edges, [float(w) for w in weights],
                                charges=[float(c) for c in charges]
                                if charges is not None else None)
        r = responsion(lm, [1.0] + [0.0] * (dim - 1), 5.0 / (mx or 1.0),
                       kind="propagator")
        reach = sum((x.real * x.real + x.imag * x.imag) for x in r)  # Σ|·|², no abs
        # Σ|·|² directly — the responsion faculty is reach > 0; a bare float
        # sqrt is banned by the A-N cascade ratchet (float = FPU-lift only).
        diag["propagator_reach_sq"] = round(reach, 6)
        return reach > 0, diag
    except Exception as e:
        diag["responsion_error"] = "%s: %s" % (type(e).__name__, e)
        return False, diag


def _recover_curvature(vocab_size, edges, charges):
    """The ``curvature`` faculty: a directed store keeps its charge. Phase-scale
    the integer charge (q = 1/(2·max|c|+1)) so it does not alias to 0 mod 1."""
    directed = charges is not None and any(c != 0 for c in charges)
    n_cycles = 0
    holonomy_nonzero = False
    if directed:
        mc = max((_recover_mag(c) for c in charges), default=0) or 1
        q = Q(1, 2 * mc + 1)                 # phase unit that exposes holonomy
        ph = [Q(int(c)) * q for c in charges]
        hol = cycle_holonomy(edges, charges=ph, n=vocab_size)
        n_cycles = hol["n_cycles"]
        holonomy_nonzero = any(h != 0 for h in hol["holonomies"])
    if not directed:
        verdict = "symmetric-bag (flat, F1210 flag)"
    elif n_cycles == 0:
        verdict = "carries-direction (acyclic -> structurally flat, F1218)"
    elif holonomy_nonzero:
        verdict = "carries-direction + curvature (nonzero holonomy)"
    else:
        verdict = "carries-direction (coherent net-zero holonomy, F1146)"
    return {"directed": directed, "n_cycles": n_cycles,
            "holonomy_nonzero": holonomy_nonzero, "verdict": verdict}


def recover_check(vocab_size, edges, weights, charges=None):
    """The packaged round-trip integrity check of a stored directed Class-L
    graph (#1390 item 4): the four faculties a genome must recover — ``op``
    (L = D − A eigendecomposes, PSD, ~0 mode), ``operand`` (weighted edges
    present, non-degenerate, uncapped), ``responsion`` (the propagator e^{−zL}
    is excitable), and ``curvature`` (a directed store keeps its charge; a
    symmetric bag is flagged flat, F1210). ``ok == op and operand and
    responsion`` — curvature is REPORTED honestly, NOT a hard gate (a
    legitimately acyclic / coherent directed graph is never a false failure).
    A domain-free composition of shipped ops; the dense op / responsion
    faculties need ``vocab_size <= 256`` — use :func:`recover_check_structural`
    / :func:`recover_check_spectral` at corpus scale (F1227). Faithful port of
    R-RBS-LM-RECOVERCHECK. Returns ``{ok, op, operand, responsion,
    curvature:{directed, n_cycles, holonomy_nonzero, verdict}, diagnostics}``."""
    edges = [tuple(e) for e in edges]
    diag = {}
    operand = (len(edges) > 0 and len(edges) == len(weights)
               and all(w >= 1 for w in weights))
    deg = {}
    for (i, j) in edges:
        deg[i] = deg.get(i, 0) + 1
        deg[j] = deg.get(j, 0) + 1
    diag["max_degree"] = max(deg.values()) if deg else 0
    diag["n_edges"] = len(edges)
    op, op_diag = _recover_op_spectral(vocab_size, edges, weights)
    diag.update(op_diag)
    responsion, r_diag = _recover_responsion(vocab_size, edges, weights, charges)
    diag.update(r_diag)
    curvature = _recover_curvature(vocab_size, edges, charges)
    return {"ok": bool(op and operand and responsion), "op": op,
            "operand": operand, "responsion": responsion,
            "curvature": curvature, "diagnostics": diag}


def recover_check_structural(vocab_size, edges, weights, charges=None, *,
                             cycle_sample=48):
    """The O(edges) faculties only — ``operand`` (edges present / valid) + a
    SAMPLED curvature read — so integrity is checkable at ANY vocab size (the
    dense op / responsion faculties do not scale past the native n<=256 wall).
    The F1227 sparse peer of :func:`recover_check_spectral` (#1390 item 4).
    Faithful port of R-RBS-LM-SIONA231. Returns ``{operand, directed,
    curvature_sampled_nonzero, ok_structural}``."""
    edges = [tuple(e) for e in edges]
    operand = (len(edges) > 0 and len(edges) == len(weights)
               and all(w >= 1 for w in weights))
    directed = charges is not None and any(c != 0 for c in charges)
    seen = {}
    holo = False
    ch = charges if charges is not None else [0] * len(edges)
    for idx, ((i, j), c) in enumerate(zip(edges, ch)):
        seen[(i, j)] = c
        for k in range(min(vocab_size, 64)):        # cheap triangle probe
            a = seen.get((min(i, k), max(i, k)))
            b = seen.get((min(k, j), max(k, j)))
            if a is not None and b is not None and k not in (i, j):
                mc = _recover_mag(c)
                q = Q(1, 2 * max(1, mc) + 1)
                hh = cycle_holonomy(
                    [(i, k), (k, j), (i, j)],
                    charges=[Q(int(a)) * q, Q(int(b)) * q,
                             Q(int(c)) * q], n=vocab_size)
                if any(h != 0 for h in hh["holonomies"]):
                    holo = True
                    break
        if holo or idx > cycle_sample * 200:
            break
    return {"operand": operand, "directed": directed,
            "curvature_sampled_nonzero": holo, "ok_structural": operand}


def recover_check_spectral(vocab_size, edges, weights, charges=None, *,
                           max_dim=256):
    """The ``op`` + ``responsion`` (spectral) faculties on a BOUNDED principal
    submatrix — the first ``min(vocab_size, max_dim)`` nodes + the edges within
    that block — so the dense n×n eigendecompose stays within the native n<=256
    wall at ANY corpus vocab. The F1227 bounded-spectral peer of
    :func:`recover_check_structural` (#1390 item 4). Returns ``{op, responsion,
    dim, diagnostics}``."""
    edges = [tuple(e) for e in edges]
    dim = min(vocab_size, max_dim)
    sub_e, sub_w, sub_c = [], [], []
    ch = charges if charges is not None else None
    for idx, (i, j) in enumerate(edges):
        if i < dim and j < dim:
            sub_e.append((i, j))
            sub_w.append(weights[idx])
            if ch is not None:
                sub_c.append(ch[idx])
    diag = {"dim": dim, "n_edges_in_block": len(sub_e)}
    if dim < 1:
        return {"op": False, "responsion": False, "dim": dim, "diagnostics": diag}
    op, op_diag = _recover_op_spectral(dim, sub_e, sub_w)
    diag.update(op_diag)
    responsion, r_diag = _recover_responsion(
        dim, sub_e, sub_w, sub_c if ch is not None else None)
    diag.update(r_diag)
    return {"op": op, "responsion": responsion, "dim": dim, "diagnostics": diag}


# ── #1390 item 4b: the octonion ORDER faculty (recover_check upgrade) ────────
# An additive 5th recover_check faculty (F1231): an ORDER-sensitive fingerprint
# that catches a walk-order corruption the graph-level faculties are BLIND to
# (F1079 / F1230 — two orders can share the IDENTICAL directed graph, so even
# the ℂ magnetic Laplacian passes them both). The path-ordered product of a
# GENERIC octonion per node along the walk = 8 ints, length-independent. A
# faithful port of R-RBS-LM-OCTRECOVER: EXACT integer products via the C-routed
# qm.so8.octonion_mult_table (composition_of_c) — no mod (a VERIFIER, lossy by
# pigeonhole F1230, NOT a store). numpy-free; no abs().


def _order_node_octonion(node_id):
    """A deterministic GENERIC octonion per node — real part 1 + seven
    DISTINCT-per-axis id-derived imaginary parts (each axis has its own
    multiplier + offset + modulus so the components do NOT collapse to a uniform
    value; a plain ``1 + id % m`` generator degenerates to ``[1,2,2,2,2,2,2,2]``
    for small ids — as bad as a basis unit, F1230)."""
    out = [1]
    for k in range(7):
        out.append(1 + ((node_id * (2 * k + 3) + (5 * k + 1)) % (11 + 2 * k)))
    return out


def order_fingerprint(fiber_ids):
    """The path-ORDERED octonion product along a walk — an order-sensitive
    fingerprint of the fiber, 8 ints, independent of walk length (#1390 item 4b;
    F1229 / F1231; the ℍ/𝕆 grade of the walk). It CATCHES a graph-preserving
    reorder the op / operand / responsion / ℂ-curvature faculties are blind to
    (F1079 / F1230). A VERIFIER (lossy by pigeonhole), NEVER a store. Composes
    the C-routed ``srmech.physics.qm.so8.octonion_mult_table`` with a generic (non-basis,
    non-uniform-component) per-node octonion.

    rc352 (`#T997`): the step multiplication is the SHIPPED
    :func:`srmech.cascade.table_product`. This op previously carried its
    own private dim-8-hardcoded triple loop (``_order_omul``) — a third copy of
    the table-driven product, kept only because no shipped op took a table. It
    is gone; the values are unchanged (exact integers, no mod, the same
    ``octonion_mult_table`` constants), and the step now rides the
    ``srmech_algebra_table_product`` C kernel."""
    from srmech.physics.qm.so8 import octonion_mult_table
    from srmech.cascade import table_product
    table = octonion_mult_table()
    acc = [1, 0, 0, 0, 0, 0, 0, 0]
    for nid in fiber_ids:
        acc = [int(v) for v in
               table_product(table, acc, _order_node_octonion(int(nid)))]
    return acc


def recover_check_order(true_fingerprint, recovered_fiber_ids):
    """PASS (True) iff a recovered fiber reproduces the stored order fingerprint
    (#1390 item 4b) — the order-integrity guard on top of the graph faculties.
    Store :func:`order_fingerprint` of the true walk beside the genome; on recall
    recompute it from the :func:`eulerian_path` reconstruction and compare. A
    mismatch flags an order corruption / F1079 graph-ambiguity (the fiber must be
    stored explicitly) that op / operand / responsion / ℂ-curvature all pass."""
    return order_fingerprint(recovered_fiber_ids) == list(true_fingerprint)


def heat_trace(L, t):
    """The spectral theta / heat trace ``Θ(t) = Tr(e^{−tL}) = Σₖ e^{−t·λₖ}``
    of a Laplacian (rc108; issue #1234 Item 2 / F1007).

    The heat trace IS a theta function of the Laplacian — on a cycle graph it
    is the Jacobi-θ family sum over the closed-form cyclic spectrum
    ``λ_k = c·(1 − cos(2πk/n))`` — and it is the natural READ-INDEPENDENT
    spectral summary (a function of the eigenvalue multiset only; no
    eigenvector, no read basis). F1007: under magnetic flux the FULL trace is
    flux-invariant (Poisson → the modular / holomorphic part) while the flux
    shadow lives only in the ground state ``λ_min(Φ)`` — read that with the
    companion :func:`ground_state_flux_response`.

    Args:
        L: an ``(n, n)`` Laplacian — real-symmetric OR complex-Hermitian
            (:class:`~srmech.math.mat.Mat` / list-of-rows / ndarray-like).
            Dispatches real → :func:`jacobi_eigvals`, complex →
            :func:`hermitian_eigendecompose` (the same forms the eigensolve
            ops accept; symmetry/Hermiticity is the caller's responsibility,
            their contract).
        t: a single diffusion time (a real scalar → returns a ``float``) OR a
            sequence of times (→ returns a real
            :class:`~srmech.math.vec.Vec`, one Θ per t). Multi-t is the cheap
            generalization: ONE eigensolve serves every t. Each t must be a
            finite real (the usual heat-trace domain is ``t ≥ 0``; a negative
            t is accepted — Θ is a finite sum either way).

    Returns:
        ``Θ(t)`` — a ``float`` for scalar ``t``, a real ``Vec`` for a
        sequence of t values. An empty ``L`` (n = 0) gives the empty-spectrum
        trace ``Θ = 0.0``.

    Exp convention (stated per the transcendental discipline): ``heat_trace``
    is a float64-carrier Class-L composite like the existing eigensolve ops —
    the eigensolve is the FPU float algorithm, and the exp is the Class-N Q61
    cascade (:func:`srmech.math.rational.exp` pure / ``srmech_exp`` native —
    libm-free) applied at the spectral-summary boundary. Θ is a spectral
    SUMMARY, not an exact decision — no float transcendental sits on any
    exact decision path.

    Native (rc108): dispatches to the composite C peer ``srmech_heat_trace``
    (ONE eigensolve — ``srmech_jacobi_eigvals`` real /
    ``srmech_hermitian_eigendecompose_ws`` Hermitian — then ``srmech_exp``
    per term, summed ascending); pure Python is the complete alternative.
    numpy-free; no ``abs()``.

    Raises:
        ValueError: non-square ``L``, an empty / non-finite ``t``.
    """
    rows = _as_rows(L)
    n = len(rows)
    scalar_t = isinstance(t, (int, float)) and not isinstance(t, bool)
    t_list = [float(t)] if scalar_t else [float(x) for x in t]
    if not t_list:
        raise ValueError("heat_trace: t must be a scalar or a NON-EMPTY sequence")
    for tv in t_list:
        if not _finite_real(tv):
            raise ValueError(f"heat_trace: every t must be a finite real; got {tv!r}")
    if n == 0:
        # The empty spectrum: Θ(t) = Σ over nothing = 0.
        return 0.0 if scalar_t else Vec.from_sequence([0.0] * len(t_list),
                                                      is_complex=False)
    is_complex = _has_complex(rows)
    if is_complex:
        flat = []
        for r in rows:
            for x in r:
                z = complex(x)
                flat.append(z.real)
                flat.append(z.imag)
    else:
        flat = [float(x.real if isinstance(x, complex) else x)
                for r in rows for x in r]
    out = _heat_trace_native(flat, n, is_complex, t_list)
    if out is None:
        out = _heat_trace_py(rows, is_complex, t_list)
    return out[0] if scalar_t else Vec.from_sequence(out, is_complex=False)


def _ground_state_flux_response_native(n, el, wl, pattern, flux_list):
    """numpy-free native dispatch for :func:`ground_state_flux_response` —
    marshals the edge endpoints / weights / per-edge charge pattern / flux
    values into ctypes buffers and calls the composite C peer
    ``srmech_ground_state_flux_response`` (per flux: the rc105 chiral
    magnetic build + the ONE Hermitian eigensolve → λ_min) with a caller
    arena sized from ``srmech_ground_state_flux_response_arena_bytes``.
    Returns the ``list[float]`` λ_min values, or ``None`` on any missing
    symbol / non-OK status (caller then runs the pure-Python complete
    alternative)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_ground_state_flux_response")
        and hasattr(_native.LIB, "srmech_ground_state_flux_response_arena_bytes")
    ):
        return None
    n_edges = len(el)
    null_u = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32))
    null_d = ctypes.cast(None, ctypes.POINTER(ctypes.c_double))
    if n_edges:
        eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in el))
        evb = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in el))
        wbuf = (ctypes.c_double * n_edges)(*(float(x) for x in wl))
        pbuf = (ctypes.c_double * n_edges)(*(float(p) for p in pattern))
    else:
        eu = evb = null_u
        wbuf = pbuf = null_d
    n_flux = len(flux_list)
    fbuf = (ctypes.c_double * n_flux)(*flux_list)
    out = (ctypes.c_double * n_flux)()
    ws_bytes = _native.LIB.srmech_ground_state_flux_response_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges)
    )
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_ground_state_flux_response(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, evb, wbuf, pbuf,
        ctypes.c_uint32(n_flux), fbuf, out, ws, ctypes.c_size_t(wsd * 8),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [out[i] for i in range(n_flux)]


def ground_state_flux_response(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    fluxes,
    charges: Optional[Iterable[float]] = None,
):
    """``λ_min(Φ)`` — the magnetic ground state as a function of flux: the
    F1007 SHADOW reader (rc108; issue #1234 Item 2).

    F1007's mock-theta split: the FULL heat trace ``Θ(t)`` of a magnetic
    Laplacian is flux-invariant (Poisson → the modular / holomorphic part),
    while the flux SHADOW lives only in the ground state — on a flux-threaded
    cycle ``λ_min`` moves 0 → positive as Φ: 0 → 1/2 turn and is periodic in
    integer flux (integer holonomy ``e^{i2πΦ} = 1`` is gauge-equivalent to
    no flux). Overtone (trace) / undertone (ground state) = the holomorphic +
    shadow split — the same asymmetric-beat family as the elliptic ``−z⁻¹``
    arc (F999–F1002).

    Args:
        n: node count (``≥ 1`` — an empty graph has no ground state).
        edges: the directed edge list ``(u, v)`` (the
            :func:`magnetic_laplacian` convention).
        weights: optional per-edge magnitudes (default 1.0 each).
        fluxes: a single total flux Φ in TURNS (a real scalar → returns a
            ``float``) OR a sequence of fluxes (→ returns a real
            :class:`~srmech.math.vec.Vec`, one λ_min per Φ).
        charges: optional per-edge charge PATTERN, parallel to ``edges``
            (validated ``len(charges) == len(edges)``) — the rc105 chiral
            surface, composable as-is: each edge ``k`` gets charge
            ``Φ · charges[k]`` (turns). Default ``None`` = the UNIFORM
            pattern ``1/n_edges`` per edge, so a single cycle's total
            holonomy is exactly Φ turns (the F1007 convention).

    Returns:
        ``λ_min(Φ)`` — a ``float`` for scalar ``fluxes``, a real ``Vec`` for
        a sequence.

    The op composes SHIPPED ops only — :func:`magnetic_laplacian` with the
    rc105 ``charges=`` (per flux: the scaled pattern) +
    :func:`hermitian_eigendecompose` (ascending → ``eigvals[0]`` IS λ_min).
    Native (rc108): the composite C peer
    ``srmech_ground_state_flux_response`` runs the same
    ``srmech_graph_magnetic_laplacian`` + ``srmech_hermitian_eigendecompose_ws``
    kernels per flux; pure Python is the complete alternative. numpy-free;
    no ``abs()``.

    Raises:
        ValueError: ``n < 1``, a bad edge/weight/charge (the
            :func:`magnetic_laplacian` contracts), a charges-length mismatch,
            or an empty / non-finite ``fluxes``.
    """
    if not isinstance(n, int) or n < 1:
        raise ValueError(
            f"ground_state_flux_response: n must be an int >= 1 (an empty "
            f"graph has no ground state); got {n!r}")
    el, wl = _validate_edges_weights_py(n, edges, weights)
    n_edges = len(el)
    if charges is not None:
        pattern = [float(c) for c in charges]
        if len(pattern) != n_edges:
            raise ValueError(
                f"ground_state_flux_response: charges length {len(pattern)} "
                f"!= n_edges {n_edges}")
    else:
        # The uniform default: total holonomy around a single cycle = Φ turns.
        pattern = [1.0 / n_edges] * n_edges if n_edges else []
    scalar_f = isinstance(fluxes, (int, float)) and not isinstance(fluxes, bool)
    flux_list = [float(fluxes)] if scalar_f else [float(x) for x in fluxes]
    if not flux_list:
        raise ValueError(
            "ground_state_flux_response: fluxes must be a scalar or a "
            "NON-EMPTY sequence")
    for fv in flux_list:
        if not _finite_real(fv):
            raise ValueError(
                f"ground_state_flux_response: every flux must be a finite "
                f"real; got {fv!r}")
    out = _ground_state_flux_response_native(n, el, wl, pattern, flux_list)
    if out is None:
        out = []
        for phi in flux_list:
            scaled = [phi * p for p in pattern]
            Lm = magnetic_laplacian(n, el, wl, charges=scaled)
            eigvals, _V = hermitian_eigendecompose(Lm)
            out.append(float(eigvals[0]))
    return out[0] if scalar_f else Vec.from_sequence(out, is_complex=False)


# =====================================================================
# EPH — the complex-time Wick-rotation propagator (0.9.0rc136; siona
# gh#1274). harvest = e^{-zL}·u0, the ONE propagator with the arg(z)
# coherence dial + the MANDATORY 2π seam-fold + the Born-rule harvest.
# =====================================================================
#
# EPH = harvest = Propagate·excite generalises the op⊗operand pattern to a
# full retrieval / inference cascade — a propagator P = e^{-zL} (operator)
# applied to an excitation u0 (operand) → the harvest H. The thermal e^{-tL}
# and the coherent e^{-itL} are NOT two ops: they are the ONE complex-time
# propagator e^{-zL} with z COMPLEX, the ``i`` being the WICK-ROTATION PHASE.
# arg(z) is the coherence dial (z real → thermal/decoherent, z imaginary →
# coherent/unitary, arg(z) between → partial coherence — the regime only the
# unified form can name). RBS-SNN = EPH-with-a-synaptic-propagator (the
# neuron is one propagator choice P = connectome/weight matrix); no
# privileged instance.

# The seam-fold's series depths. The oscillation (cos/sin) is folded to
# |arg| ≤ π then evaluated — a Class-N Taylor of ≤ π converges to < 1e-16 by
# ~15 terms; the exp damping is halved to |arg| ≤ 1/2 then squared back.
_EPH_EXP_TERMS: int = 24
_EPH_TRIG_TERMS: int = 18
_EPH_ATAN_TERMS: int = 45          # 2π-via-Machin depth (≤ 1e-40 residual)
_EPH_TWO_PI_DEN: int = 1 << 80     # 2π fixed-point denominator (~1e-24 grid)
_EPH_FOLD_DEN: int = 1 << 44       # folded-angle series denominator (~6e-14)


def _eph_round_div(num: int, den: int) -> int:
    """Nearest integer to ``num/den`` (den > 0) — round-half-up, exact
    integer arithmetic (the winding number of the 2π seam-fold)."""
    q, r = divmod(num, den)            # den > 0 → r in [0, den)
    if 2 * r >= den:
        q += 1
    return q


def _eph_two_pi_rational() -> Tuple[int, int]:
    """2π as a Class-N rational via the Machin identity
    ``2π = 32·atan(1/5) − 8·atan(1/239)`` (each atan by the exact Class-N
    :func:`atan_series_truncate`), quantised to the fixed denominator
    :data:`_EPH_TWO_PI_DEN` (exact-integer rounding, no float). The residual
    vs true 2π is ≤ the atan truncation (~1e-40) then the fixed-grid round
    (~1e-24) — far below float64, so the winding fold is exact at any t·λ."""
    a5 = _atan_series(1, 5, _EPH_ATAN_TERMS)       # ≈ atan(1/5)
    a239 = _atan_series(1, 239, _EPH_ATAN_TERMS)   # ≈ atan(1/239)
    # 32·a5 − 8·a239 over the common denominator a5.den·a239.den
    num = 32 * a5[0] * a239[1] - 8 * a239[0] * a5[1]
    den = a5[1] * a239[1]
    return (_eph_round_div(num * _EPH_TWO_PI_DEN, den), _EPH_TWO_PI_DEN)


#: 2π as a fixed-denominator exact-Machin rational — computed once (the seam
#: anchor). Denominator :data:`_EPH_TWO_PI_DEN`; value ≈ 2π to ~1e-24.
_EPH_TWO_PI: Tuple[int, int] = _eph_two_pi_rational()


def _eph_exp_real(g: float) -> float:
    """``exp(g)`` for any real ``g`` via the Class-N
    :func:`exp_series_truncate` on a power-of-two-reduced argument
    (``|g|/2^s ≤ 1/2``), squared back ``s`` times. The reduced argument is
    the EXACT dyadic rational of the reduced float (``as_integer_ratio``);
    the series is exact; only the final projection + squaring is float64
    (the FPU last-mile). Robust for a strongly-damped mode (``exp(−44) →
    ~7.6e-20``) without the raw series blowing up."""
    if g == 0.0:
        return 1.0
    mag = g if g >= 0.0 else -g        # Class-K magnitude, never abs()
    s = 0
    r = mag
    while r > 0.5:
        r *= 0.5
        s += 1
    red = g / float(1 << s)            # signed reduced argument, |red| ≤ 1/2
    rn, rd = float(red).as_integer_ratio()
    en, ed = _exp_series(rn, rd, _EPH_EXP_TERMS)
    e = en / ed                        # project to float (FPU last-mile)
    for _ in range(s):
        e = e * e
    return e


def _eph_seam_fold(theta: float) -> Tuple[int, int]:
    """The 2π seam-fold as the DIVMOD it is — ``(w, qn)`` with the quotient
    KEPT (0.9.0rc207; gh#1276 — the #741 mod-should-be-divmod audit's first
    concrete instance).

    ``w = round(θ/2π)`` (exact rational arithmetic on the dyadic θ over the
    Machin-2π :data:`_EPH_TWO_PI` — round-half-toward-+∞ via
    :func:`_eph_round_div`) is the **metacycle winding** — the whole 2π
    turns. ``qn`` is the **epicycle residue** ``θ − w·2π`` quantised to the
    fixed grid ``qn / _EPH_FOLD_DEN`` (``|θ_fold| ≤ π``). Lossless:
    ``2π·w + qn/_EPH_FOLD_DEN`` reconstructs θ to the fold grid (the
    ``One.unwrapped_phase`` reconstruction). :func:`_eph_cos_sin` calls this
    and discards ``w`` (the trig readout is 2π-periodic);
    :func:`propagate_wound` calls the SAME fold and KEEPS it — one divmod,
    both harvests."""
    if theta == 0.0:
        return (0, 0)
    tn, td = float(theta).as_integer_ratio()   # EXACT dyadic rational of θ
    pn, pd = _EPH_TWO_PI
    # winding w = round(θ / 2π) = round((tn·pd) / (td·pn)); td > 0, pn > 0.
    w = _eph_round_div(tn * pd, td * pn)
    # folded = θ − w·2π = (tn·pd − w·pn·td) / (td·pd), exact; |folded| ≤ π.
    fn = tn * pd - w * pn * td
    fd = td * pd
    # re-quantise the small folded angle to the fixed-grid denominator
    # _EPH_FOLD_DEN (exact-integer rounding) so the bounded series stays fast.
    qn = _eph_round_div(fn * _EPH_FOLD_DEN, fd)
    return (w, qn)


def _eph_cos_sin(theta: float) -> Tuple[float, float]:
    """``(cos θ, sin θ)`` via the MANDATORY 2π seam-fold + the Class-N
    :func:`cos_series_truncate` / :func:`sin_series_truncate`.

    THE CORRECTNESS CRUX: the raw trig series BLOW UP past a convergence
    radius (``cos_series_truncate(44, 1, N)`` is ~2.3e17, not ~1.0). Before
    the series, argument-reduce (seam-fold) ``θ`` modulo 2π — the BEAT SEAM —
    via :func:`_eph_seam_fold` (the exact Machin-2π divmod): the winding
    ``w = round(θ/2π)`` is stripped in exact rational arithmetic, leaving
    ``|θ − w·2π| ≤ π`` where the bounded series is exact. This restores
    exactness at ANY t·λ. (This 2π-periodic readout discards ``w`` — the
    epicycle side of the seam; :func:`propagate_wound` (rc207, gh#1276)
    keeps the SAME fold's quotient to expose the metacycle harvest.)"""
    if theta == 0.0:
        return (1.0, 0.0)
    _w, qn = _eph_seam_fold(theta)         # the SAME divmod; w folds away here
    c_n, c_d = _cos_series(qn, _EPH_FOLD_DEN, _EPH_TRIG_TERMS)
    s_n, s_d = _sin_series(qn, _EPH_FOLD_DEN, _EPH_TRIG_TERMS)
    return (c_n / c_d, s_n / s_d)


def _eph_wick_factor(zr: float, zi: float, lam: float) -> complex:
    """The per-mode complex scalar ``e^{-z·λ} = e^{-Re(z)·λ}·(cos(Im(z)·λ) −
    i·sin(Im(z)·λ))`` — damping via :func:`_eph_exp_real` (Class-N exp),
    oscillation via :func:`_eph_cos_sin` (Class-N trig + the 2π seam-fold)."""
    e = _eph_exp_real(-(zr * lam))            # real damping
    c, s = _eph_cos_sin(zi * lam)             # seam-folded oscillation
    return complex(e * c, -(e * s))           # Class-C sign, never abs()


def _eph_propagate_native(rows, u, zr: float, zi: float, is_complex: bool):
    """numpy-free native dispatch for :func:`propagate` — marshals the flat
    matrix + the interleaved u0 into ctypes buffers and calls the composite C
    peer ``srmech_eph_propagate`` with a caller arena sized from
    ``srmech_eph_propagate_arena_bytes``. Returns the ``list[complex]``
    harvest, or ``None`` on any missing symbol / non-OK status (caller then
    runs the pure-Python complete alternative)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_eph_propagate")
        and hasattr(_native.LIB, "srmech_eph_propagate_arena_bytes")
    ):
        return None
    n = len(rows)
    if is_complex:
        flat = []
        for r in rows:
            for x in r:
                z = complex(x)
                flat.append(z.real)
                flat.append(z.imag)
    else:
        flat = [float(x.real if isinstance(x, complex) else x)
                for r in rows for x in r]
    L_c = (ctypes.c_double * len(flat))(*flat)
    u_il = []
    for x in u:
        z = complex(x)
        u_il.append(z.real)
        u_il.append(z.imag)
    u_c = (ctypes.c_double * (2 * n))(*u_il)
    out = (ctypes.c_double * (2 * n))()
    ws_bytes = _native.LIB.srmech_eph_propagate_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0)
    )
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_eph_propagate(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0), L_c, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), out, ws,
        ctypes.c_size_t(wsd * 8),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [complex(out[2 * i], out[2 * i + 1]) for i in range(n)]


def _eph_propagate_eig_py(rows, u, zr: float, zi: float, is_complex: bool):
    """The pure-Python EPH eigenbasis cascade — returns ``(harvest, lam)``:
    the ONE eigensolve (:func:`symmetric_eigendecompose` real /
    :func:`hermitian_eigendecompose` complex, srmech's own Class-L cascades),
    then per-mode scale by the seam-folded Class-N Wick factor and recombine.
    harvest = V·diag(e^{-z·λ_k})·V^H·u0 (basis-invariant, so it matches the C
    peer regardless of the eigenvector sign / degenerate basis). ``lam`` is
    returned alongside so :func:`propagate_wound` (rc207) can fold the SAME
    per-mode oscillation arguments the harvest used — one eigensolve, both
    harvests."""
    n = len(rows)
    if is_complex:
        eigvals, V = hermitian_eigendecompose(rows)
    else:
        eigvals, V = symmetric_eigendecompose(rows)
    Vl = V.tolist()                              # nested list, numpy-free
    lam = [float(eigvals[k]) for k in range(n)]
    factors = [_eph_wick_factor(zr, zi, lam[k]) for k in range(n)]
    uc = [complex(x) for x in u]
    # project + scale: c_k = (Σ_i conj(V[i,k])·u0[i]) · e^{-z·λ_k}
    c = [0j] * n
    for k in range(n):
        acc = 0j
        for i in range(n):
            vik = Vl[i][k]
            vik_c = vik.conjugate() if isinstance(vik, complex) else vik
            acc += vik_c * uc[i]
        c[k] = acc * factors[k]
    # recombine: harvest_i = Σ_k V[i,k]·c_k
    harvest = [0j] * n
    for i in range(n):
        acc = 0j
        for k in range(n):
            acc += Vl[i][k] * c[k]
        harvest[i] = acc
    return harvest, lam


def _eph_propagate_py(rows, u, zr: float, zi: float, is_complex: bool):
    """The pure-Python complete alternative for :func:`propagate` — the
    harvest half of :func:`_eph_propagate_eig_py` (byte-identical; the
    eigenvalues are simply not read here)."""
    harvest, _lam = _eph_propagate_eig_py(rows, u, zr, zi, is_complex)
    return harvest


def propagate(L, u0, z) -> "Vec":
    """EPH — the complex-time Wick-rotation propagator ``harvest = e^{-zL}·u0``
    (0.9.0rc136; siona gh#1274). The ONE propagator with the arg(z) coherence
    dial + the mandatory 2π seam-fold.

    EPH = harvest = Propagate·excite: a propagator ``P = e^{-zL}`` (operator)
    applied to an excitation ``u0`` (operand) → the harvest ``H``. The thermal
    ``e^{-tL}`` and the coherent ``e^{-itL}`` are NOT two ops — they are the
    ONE complex-time propagator ``e^{-zL}`` with ``z`` COMPLEX, the ``i``
    being the WICK-ROTATION PHASE. **arg(z) is the coherence dial:**

    * ``z`` REAL → thermal diffusion (decoherent — real damping ``e^{-tλ}``);
    * ``z`` IMAGINARY → coherent unitary quantum walk (‖harvest‖ = ‖u0‖
      conserved, a phase rotation per mode);
    * ``arg(z)`` BETWEEN → PARTIAL coherence (``z = t·e^{iφ}``, ``φ`` = the
      dial ∈ ``[0, π/2]``) — the real chloroplast regime ONLY the unified
      form can name (two separate thermal / coherent ops cannot express the
      middle). RBS-SNN = EPH-with-a-synaptic-propagator (``P`` = connectome /
      weight matrix); no privileged instance. Composes the framework's
      Class-L Wick rotation (the signed-metric / Wick op = a Class-L
      signed-Laplacian variant).

    IMPL (eigenbasis, ``n ≤ 256`` native): ONE eigensolve
    (:func:`symmetric_eigendecompose` real / :func:`hermitian_eigendecompose`
    complex) → project ``c = V^H·u0`` → per-mode scale ``c_k·e^{-z·λ_k}`` →
    recombine ``V·(scaled c)``. The per-mode scalar
    ``e^{-zλ_k} = e^{-Re(z)·λ_k}·(cos(Im(z)·λ_k) − i·sin(Im(z)·λ_k))`` uses
    the Class-N :func:`exp_series_truncate` (real damping) +
    :func:`cos_series_truncate` / :func:`sin_series_truncate` (oscillation).

    THE MANDATORY 2π SEAM-FOLD (the correctness crux): the raw trig series
    BLOW UP past a convergence radius (``cos_series_truncate(44, 1, N)`` is
    ~2.3e17, not ~1.0). ``propagate`` argument-reduces (seam-folds) the
    oscillation argument ``Im(z)·λ_k`` modulo 2π — the beat seam — using the
    exact Machin-2π (``2π = 32·atan(1/5) − 8·atan(1/239)``), so it is EXACT at
    ANY t·λ. (This 2π-periodic readout discards the winding ``w``;
    :func:`propagate_wound` (rc207, gh#1276) keeps the SAME fold's quotient
    to expose the metacycle harvest alongside the identical epicycle one.)

    Args:
        L: an ``(n, n)`` real-symmetric OR complex-Hermitian Laplacian /
            operator (:class:`~srmech.math.mat.Mat` / list-of-rows /
            ndarray-like). Symmetry / Hermiticity is the caller's
            responsibility (the eigensolve ops' contract).
        u0: the excitation vector (length ``n``, real or complex;
            :class:`~srmech.math.vec.Vec` / list). Content-neutral (Class-M
            grounding) — the seed the propagator acts on.
        z: the complex time ``z = Re(z) + i·Im(z)`` (a Python ``complex`` or a
            ``[re, im]`` pair). ``arg(z)`` is the coherence dial; build the
            partial regime as ``z = t·(cos φ + i·sin φ)``, ``φ ∈ [0, π/2]``.

    Returns:
        the harvest ``e^{-zL}·u0`` — a length-``n`` complex
        :class:`~srmech.math.vec.Vec` (the coherent / partial part is
        genuinely complex). An empty ``L`` (n = 0) gives the empty harvest.

    Native (rc136): dispatches to the composite C peer ``srmech_eph_propagate``
    (ONE ``srmech_hermitian_eigendecompose_ws`` + ``srmech_exp`` /
    ``srmech_cos`` / ``srmech_sin`` per mode — the Q61 octant reduction is the
    2π fold in the fixed-point basis); pure Python is the complete
    alternative. The harvest is basis-invariant, so Python == C to the
    eigensolve tolerance regardless of the eigenvector convention. numpy-free;
    no ``abs()`` (Class-K magnitude / Class-C sign).

    → extended by :func:`responsion` (rc208, F1186): ``propagate`` IS the
    time-domain member of the RESPONSION response-function family —
    ``responsion(L, u0, z, kind="propagator")`` delegates here verbatim,
    and ``kind="resolvent"`` is its Laplace-transform dual
    ``(zI − L)^{−1}·u0`` (the Green's function).

    Raises:
        ValueError: non-square ``L``, or ``len(u0) != n``.
    """
    rows = _as_rows(L)
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(f"propagate: L must be square; got {n} rows")
    z = complex(z)
    u = _vec(u0)
    if len(u) != n:
        raise ValueError(
            f"propagate: len(u0) ({len(u)}) must equal n ({n})"
        )
    if n == 0:
        return Vec(array("d"), 0, is_complex=True)
    is_complex = _has_complex(rows)
    harvest = _eph_propagate_native(rows, u, z.real, z.imag, is_complex)
    if harvest is None:
        harvest = _eph_propagate_py(rows, u, z.real, z.imag, is_complex)
    return Vec.from_sequence(harvest, is_complex=True)


def eph_harvest(L, u0, z) -> dict:
    """The EPH cascade read (0.9.0rc136; siona gh#1274) — excite → propagate →
    Born-rule harvest-rank the reaction center.

    A composition op: excite (seed ``u0`` — Class-M grounding, content-neutral)
    → :func:`propagate` (``harvest = e^{-zL}·u0`` with the arg(z) coherence
    dial) → the **Born-rule harvest** ``|harvest_i|²`` per node (the reaction-
    center energy; energy = relevance) → rank the nodes by energy. The neuron
    is one propagator choice (RBS-SNN); this is the generic retrieval /
    inference cascade one layer up from :func:`propagate`.

    Args:
        L, u0, z: as :func:`propagate` (the operator, the excitation, the
            complex time / coherence dial).

    Returns:
        a JSON-native dict:

        * ``ranked_nodes`` — node indices sorted by Born energy DESCENDING
          (the reaction-center ranking; energy = relevance);
        * ``energies`` — ``|harvest_i|²`` per node in NODE order (the Born-rule
          reaction-center energy; Class-K ``re² + im²``, no ``abs()``);
        * ``reaction_center`` — the top-ranked node (highest energy), or
          ``None`` for an empty ``L``;
        * ``total_energy`` — ``Σ_i |harvest_i|²`` = the coherence budget
          (conserved = ‖u0‖² in the coherent limit ``z`` imaginary; damped
          below it in the thermal limit ``z`` real — the monotonic Wick dial);
        * ``harvest_re`` / ``harvest_im`` — the raw complex harvest components.

    Composes :func:`propagate` (c_dispatched) + the Born magnitude + rank — no
    new C symbol. numpy-free; no ``abs()``.
    """
    harvest = propagate(L, u0, z)
    n = harvest.shape[0]
    energies = []
    hre = []
    him = []
    total = 0.0
    for i in range(n):
        h = complex(harvest[i])
        e = h.real * h.real + h.imag * h.imag     # Born |·|², Class-K squares
        energies.append(e)
        hre.append(h.real)
        him.append(h.imag)
        total += e
    ranked = sorted(range(n), key=lambda i: energies[i], reverse=True)
    return {
        "ranked_nodes": ranked,
        "energies": energies,
        "reaction_center": ranked[0] if ranked else None,
        "total_energy": total,
        "harvest_re": hre,
        "harvest_im": him,
    }


# =====================================================================
# EPH WOUND — the wound propagator (0.9.0rc207; siona gh#1276). The SAME
# harvest e^{-zL}·u0 as :func:`propagate` with the 2π seam-fold's DIVMOD
# QUOTIENT KEPT: the fold is a divmod (quotient = the metacycle winding
# w, remainder = the epicycle residue θ); propagate discards w (the
# mod-collapse); propagate_wound keeps the GRADING — both harvests at
# the seam. The #741 mod-should-be-divmod audit's first concrete
# instance; the_one(σ, θ, w) is the crank vocabulary of the readout.
# =====================================================================


def _eph_propagate_wound_native(rows, u, zr: float, zi: float,
                                is_complex: bool):
    """numpy-free native dispatch for :func:`propagate_wound` — ONE call to
    the composite C peer ``srmech_eph_propagate_wound`` (the
    ``srmech_eph_propagate`` cascade + the per-mode winding readout composed
    from the EXISTING gh#1276 winding C peers). Returns ``(harvest, lam, w,
    theta, sigma_eff, spinor)`` lists, or ``None`` on any missing symbol /
    non-OK status (caller then runs the pure-Python complete
    alternative)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_eph_propagate_wound")
        and hasattr(_native.LIB, "srmech_eph_propagate_wound_arena_bytes")
    ):
        return None
    n = len(rows)
    if is_complex:
        flat = []
        for r in rows:
            for x in r:
                z = complex(x)
                flat.append(z.real)
                flat.append(z.imag)
    else:
        flat = [float(x.real if isinstance(x, complex) else x)
                for r in rows for x in r]
    L_c = (ctypes.c_double * len(flat))(*flat)
    u_il = []
    for x in u:
        z = complex(x)
        u_il.append(z.real)
        u_il.append(z.imag)
    u_c = (ctypes.c_double * (2 * n))(*u_il)
    out = (ctypes.c_double * (2 * n))()
    out_lam = (ctypes.c_double * n)()
    out_w = (ctypes.c_int64 * n)()
    out_theta = (ctypes.c_double * n)()
    out_sig = (ctypes.c_int32 * n)()
    out_spin = (ctypes.c_int32 * n)()
    ws_bytes = _native.LIB.srmech_eph_propagate_wound_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0)
    )
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_eph_propagate_wound(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0), L_c, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), out, out_lam, out_w,
        out_theta, out_sig, out_spin, ws, ctypes.c_size_t(wsd * 8),
    )
    if rc != _native.SRMECH_OK:
        return None
    harvest = [complex(out[2 * i], out[2 * i + 1]) for i in range(n)]
    return (harvest,
            [float(out_lam[k]) for k in range(n)],
            [int(out_w[k]) for k in range(n)],
            [float(out_theta[k]) for k in range(n)],
            [int(out_sig[k]) for k in range(n)],
            [int(out_spin[k]) for k in range(n)])


def _eph_propagate_wound_py(rows, u, zr: float, zi: float, is_complex: bool):
    """The pure-Python complete alternative for :func:`propagate_wound` —
    the SAME :func:`_eph_propagate_eig_py` cascade :func:`propagate`'s pure
    path runs (byte-identical harvest), then the SAME :func:`_eph_seam_fold`
    divmod the harvest's Wick factors folded with, per mode — quotient KEPT
    this time. The chirality readouts reuse the One's EXISTING gh#1276
    winding surface (never re-derived)."""
    from srmech.cascade.one import (      # lazy: no import cycle
        _sigma_effective_from_triad, _spinor_sign_from_triad)
    n = len(rows)
    harvest, lam = _eph_propagate_eig_py(rows, u, zr, zi, is_complex)
    w_list = []
    theta_list = []
    sig_list = []
    spin_list = []
    for k in range(n):
        w, qn = _eph_seam_fold(zi * lam[k])    # the SAME divmod, KEPT
        w_list.append(w)
        theta_list.append(qn / _EPH_FOLD_DEN)  # the epicycle residue, |θ| ≤ π
        triad = (w, 0, 0)                      # the mode's metacycle triad
        sig_list.append(_sigma_effective_from_triad(1, triad))
        spin_list.append(_spinor_sign_from_triad(triad))
    return harvest, lam, w_list, theta_list, sig_list, spin_list


def propagate_wound(L, u0, z) -> dict:
    """EPH WOUND — :func:`propagate` with the 2π seam-fold's DIVMOD quotient
    KEPT (0.9.0rc207; siona gh#1276 — the #741 mod-should-be-divmod audit's
    first concrete instance).

    :func:`propagate`'s mandatory 2π seam-fold argument-reduces each
    per-mode oscillation argument ``Im(z)·λ_k`` modulo 2π. That fold IS a
    divmod: **quotient** ``w_k = round(Im(z)·λ_k / 2π)`` = the METACYCLE
    winding (the whole 2π turns — what ``propagate`` throws away, the
    mod-collapse), **remainder** ``θ_k`` = the EPICYCLE residue (``|θ| ≤ π``
    — what ``propagate`` keeps). ``propagate_wound`` keeps the GRADING:
    BOTH harvests at the seam, from the SAME fold (:func:`_eph_seam_fold`
    pure / ``srmech_winding_fold`` native — the exact Machin-2π / Q61 2/π
    constants ``propagate`` already folds with; no forked path). Carrying
    ``w`` does NOT perturb the epicycle harvest: it is byte-identical to
    ``propagate``'s at the same dispatch tier (same cascade, same order).

    THE CRANK — ``the_one(σ, θ, w)`` is the readout vocabulary (per mode,
    the winding fills the One's fast metacycle dial as the triad
    ``(w_k, 0, 0)``):

    * ``winding`` — ``w_k`` (whole ℤ, never ``% 2``): the metacycle turns;
    * ``theta`` — ``θ_k``: the epicycle phase; ``2π·w_k + θ_k`` reconstructs
      ``Im(z)·λ_k`` LOSSLESSLY on the fold grid (the
      :meth:`~srmech.cascade.one.One.unwrapped_phase` reconstruction);
    * ``sigma_effective`` — the tower-graded chirality dial ``±1`` via the
      winding's divmod binary tower (the EXISTING
      :meth:`~srmech.cascade.one.One.sigma_effective` readout — NOT the
      melding bare ``w mod 2``: ``w=5`` (popcount 2) and ``w=7`` (popcount
      3) are DISTINGUISHED);
    * ``spinor_sign`` — the double-cover sign ``(−1)^{w_k}`` (the EXISTING
      :meth:`~srmech.cascade.one.One.spinor_sign` readout — one full
      winding flips the spinor, two restore it).

    Lift a mode into a full One with
    ``the_one(+1, theta_num, theta_den, w=(w_k, 0, 0))``.

    Args:
        L, u0, z: exactly as :func:`propagate` (the operator, the
            excitation, the complex time / coherence dial).

    Returns:
        a JSON-native dict, per-mode arrays in the eigensolve's mode order:

        * ``harvest_re`` / ``harvest_im`` — the epicycle harvest
          ``e^{-zL}·u0`` per NODE (byte-identical to :func:`propagate` at
          the same dispatch tier);
        * ``eigenvalues`` — ``λ_k`` per mode;
        * ``winding`` — ``w_k`` (int) per mode: the metacycle turns the
          seam-fold used to discard;
        * ``theta`` — ``θ_k`` (float, ``|θ| ≤ π``) per mode: the folded
          epicycle residue;
        * ``sigma_effective`` — ``±1`` per mode (tower-graded);
        * ``spinor_sign`` — ``±1`` per mode (double-cover).

    Native (rc207): ONE call to the composite C peer
    ``srmech_eph_propagate_wound`` (the ``srmech_eph_propagate`` cascade +
    ``srmech_winding_fold`` + the EXISTING ``srmech_sigma_effective`` /
    ``srmech_spinor_sign`` winding peers per mode); pure Python is the
    complete alternative (the same :func:`_eph_propagate_eig_py` +
    :func:`_eph_seam_fold` cascade). numpy-free; no ``abs()`` (the winding
    sign is the Class-K pin, retrograde is the Class-C negate — carried by
    the reused readouts).

    Raises:
        ValueError: non-square ``L``, or ``len(u0) != n``.
    """
    rows = _as_rows(L)
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(
                f"propagate_wound: L must be square; got {n} rows")
    z = complex(z)
    u = _vec(u0)
    if len(u) != n:
        raise ValueError(
            f"propagate_wound: len(u0) ({len(u)}) must equal n ({n})"
        )
    if n == 0:
        return {
            "harvest_re": [], "harvest_im": [], "eigenvalues": [],
            "winding": [], "theta": [], "sigma_effective": [],
            "spinor_sign": [],
        }
    is_complex = _has_complex(rows)
    got = _eph_propagate_wound_native(rows, u, z.real, z.imag, is_complex)
    if got is None:
        got = _eph_propagate_wound_py(rows, u, z.real, z.imag, is_complex)
    harvest, lam, w_list, theta_list, sig_list, spin_list = got
    return {
        "harvest_re": [h.real for h in harvest],
        "harvest_im": [h.imag for h in harvest],
        "eigenvalues": lam,
        "winding": w_list,
        "theta": theta_list,
        "sigma_effective": sig_list,
        "spinor_sign": spin_list,
    }


# =====================================================================
# RESPONSION — the response-function family (0.9.0rc208; F1186). The
# op⊗operand DUALITY (A-N operator verbs ⊗ carrier operand nouns =
# field⊗excitation) has a k=3 completion: the RESPONSION — the
# answering-correspondence between successive op-on-operand
# applications, the stored relationship itself (srmech = Stored-
# RELATIONSHIP Mechanism — the responsion is the package's reason for
# being). The exact/discrete regime sees one op(operand)=result; the
# continuous/asymptotic regime (the beat, the resolvent, the
# propagator) is where the responsion lives. Two canonical members,
# LAPLACE-TRANSFORM DUALS: the propagator e^{-zL} (time domain — the
# shipped EPH) and the resolvent (zI−L)^{-1} (frequency/energy domain —
# the Green's function, NEW here).
# =====================================================================


def _responsion_resolvent_native(rows, u, zr: float, zi: float,
                                 is_complex: bool):
    """numpy-free native dispatch for :func:`responsion` kind="resolvent" —
    marshals the flat matrix + the interleaved u0 into ctypes buffers and
    calls the composite C peer ``srmech_responsion`` (kind=1) with a caller
    arena sized from ``srmech_responsion_arena_bytes``. Returns the
    ``list[complex]`` response, raises :class:`ZeroDivisionError` on the
    C peer's honest pole signal (``SRMECH_ERR_BAD_INPUT`` — ``z`` exactly
    in the spectrum of ``L``), or returns ``None`` on any missing symbol /
    other non-OK status (caller then runs the pure-Python complete
    alternative)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_responsion")
        and hasattr(_native.LIB, "srmech_responsion_arena_bytes")
    ):
        return None
    n = len(rows)
    if is_complex:
        flat = []
        for r in rows:
            for x in r:
                zc = complex(x)
                flat.append(zc.real)
                flat.append(zc.imag)
    else:
        flat = [float(x.real if isinstance(x, complex) else x)
                for r in rows for x in r]
    L_c = (ctypes.c_double * len(flat))(*flat)
    u_il = []
    for x in u:
        zc = complex(x)
        u_il.append(zc.real)
        u_il.append(zc.imag)
    u_c = (ctypes.c_double * (2 * n))(*u_il)
    out = (ctypes.c_double * (2 * n))()
    ws_bytes = _native.LIB.srmech_responsion_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0),
        ctypes.c_int(1),
    )
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_responsion(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0),
        ctypes.c_int(1), L_c, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), out, ws,
        ctypes.c_size_t(wsd * 8),
    )
    if rc == _native.SRMECH_ERR_BAD_INPUT:
        # The C peer's honest resolvent-pole signal: z ∈ spec(L) ⇒ the
        # block embedding of (zI − L) is singular. Same exception the
        # pure path's solve raises — two complete implementations, one
        # documented pole contract.
        raise ZeroDivisionError(
            "responsion: z is a pole of the resolvent (z is in the "
            "spectrum of L — (zI − L) is singular)"
        )
    if rc != _native.SRMECH_OK:
        return None
    return [complex(out[2 * i], out[2 * i + 1]) for i in range(n)]


def _responsion_resolvent_py(rows, u, zr: float, zi: float):
    """The pure-Python complete alternative for :func:`responsion`
    kind="resolvent" — build ``A = zI − L`` (complex leaves; the ``z − L``
    subtraction is Class-C signed arithmetic) and solve ``A·x = u0`` via
    :func:`_dense_solve_complex` (the SAME real 2n×2n block embedding the
    C peer runs, over :func:`mat_solve`). A singular ``A`` (``z`` exactly
    in the spectrum of ``L`` — the resolvent pole) raises
    :class:`ZeroDivisionError` from the solve — the same honest pole
    contract as the native path."""
    n = len(rows)
    z = complex(zr, zi)
    A = [[(z if i == j else 0j) - complex(rows[i][j]) for j in range(n)]
         for i in range(n)]
    x = _dense_solve_complex(A, [complex(v) for v in u])
    return [complex(v) for v in x]


def responsion(L, u0, z, *, kind: str = "propagator") -> "Vec":
    """RESPONSION — the response-function family of a generator ``L``
    acting on an excitation ``u0`` (0.9.0rc208; F1186 — the
    op⊗operand⊗responsion k=3 completion).

    The op⊗operand DUALITY (A-N operator verbs ⊗ carrier operand nouns =
    field⊗excitation) completes at k=3 with the RESPONSION: the
    answering-correspondence between successive op-on-operand
    applications — **the stored relationship itself** (srmech =
    Stored-RELATIONSHIP Mechanism). The exact/discrete regime sees one
    ``op(operand) = result``; the continuous/asymptotic regime (the beat,
    the resolvent, the propagator) is where the responsion lives. The
    family generalizes EPH's ``e^{−zL}`` to the general response function
    of ``L``, and its two canonical continuous-form members are
    **Laplace-transform duals** — a tight, framework-honest pair, not a
    grab-bag:

    * ``kind="propagator"`` (time domain): ``e^{−zL}·u0`` — this IS the
      shipped EPH :func:`propagate` (rc136), and the call DELEGATES to it
      verbatim (same arg(z) coherence dial: z real → thermal, imaginary →
      coherent, between → partial; same mandatory 2π seam-fold; same
      native/pure dispatch). ``responsion`` SUBSUMES ``propagate`` as its
      time-domain member; ``propagate`` remains the named EPH surface
      (back-compat + the :func:`propagate_wound` / :func:`propagate_sparse`
      / :func:`eph_harvest` sibling family hangs off it).
    * ``kind="resolvent"`` (frequency/energy domain — the Green's
      function): ``(zI − L)^{−1}·u0`` — **NEW**. The Laplace transform of
      the (semigroup) propagator::

          (zI − L)^{−1} = ∫₀^∞ e^{−zt}·e^{tL} dt      (Re z > max λ(L))

      with ``e^{tL}·u0 = propagate(L, u0, −t)`` (the shipped propagator at
      negative time), so per eigenmode the dual pair is ``e^{−z·λ}`` ⟷
      ``1/(z − λ)``. Realised as a REAL complex linear solve
      ``(zI − L)·x = u0`` — the real 2n×2n block embedding
      ``[[Aᵣ,−Aᵢ],[Aᵢ,Aᵣ]]·[u;v] = [bᵣ;bᵢ]`` over the shipped
      Gauss–Jordan kernel (native: the composite C peer
      ``srmech_responsion`` composing ``srmech_dense_solve_f64_ws``;
      pure: :func:`_dense_solve_complex` — the SAME embedding, the
      complete alternative). ``z`` exactly in the spectrum of ``L`` is a
      **resolvent pole** and raises :class:`ZeroDivisionError` honestly
      (the pole IS the physics — never a garbage number).

    Args:
        L: an ``(n, n)`` real-symmetric OR complex-Hermitian operator
            (:class:`~srmech.math.mat.Mat` / list-of-rows / ndarray-like),
            exactly as :func:`propagate`.
        u0: the excitation vector (length ``n``, real or complex) — the
            seed the response acts on.
        z: the complex argument. For the propagator: the complex time
            (arg(z) = the coherence dial). For the resolvent: the complex
            frequency/energy (the Green's-function argument; poles at the
            spectrum of ``L``).
        kind: ``"propagator"`` (default — delegates to :func:`propagate`)
            or ``"resolvent"`` (the new Laplace-dual member).

    Returns:
        the response — a length-``n`` complex :class:`~srmech.math.vec.Vec`
        (the :func:`propagate` return contract). An empty ``L`` (n = 0)
        gives the empty response.

    Raises:
        ValueError: unknown ``kind``, non-square ``L``, or
            ``len(u0) != n``.
        ZeroDivisionError: kind="resolvent" with ``z`` in the spectrum of
            ``L`` (the resolvent pole).

    Native (rc208): the composite C peer ``srmech_responsion`` — kind 0
    delegates to ``srmech_eph_propagate``, kind 1 composes
    ``srmech_dense_solve_f64_ws`` via the block embedding — so a bare-C
    host runs BOTH members. numpy-free; no ``abs()`` (the ``z − L``
    subtraction is Class-C signed arithmetic; the solve pivot is the
    composed kernel's Class-K sign branch).
    """
    if kind not in ("propagator", "resolvent"):
        raise ValueError(
            f"responsion: unknown kind {kind!r} — the family members are "
            f"'propagator' (e^{{-zL}}·u0, the time-domain EPH) and "
            f"'resolvent' ((zI-L)^{{-1}}·u0, the Laplace-dual Green's "
            f"function)"
        )
    if kind == "propagator":
        # The time-domain member IS the shipped EPH propagator — pure
        # delegation (same dispatch, same seam-fold, same coherence dial).
        return propagate(L, u0, z)
    rows = _as_rows(L)
    n = len(rows)
    for r in rows:
        if len(r) != n:
            raise ValueError(f"responsion: L must be square; got {n} rows")
    z = complex(z)
    u = _vec(u0)
    if len(u) != n:
        raise ValueError(
            f"responsion: len(u0) ({len(u)}) must equal n ({n})"
        )
    if n == 0:
        return Vec(array("d"), 0, is_complex=True)
    is_complex = _has_complex(rows)
    resp = _responsion_resolvent_native(rows, u, z.real, z.imag, is_complex)
    if resp is None:
        resp = _responsion_resolvent_py(rows, u, z.real, z.imag)
    return Vec.from_sequence(resp, is_complex=True)


# =====================================================================
# EPH SPARSE — the sparse-scaled propagator (0.9.0rc206; siona gh#1274
# item 1c, the corpus-scale residual). The SAME harvest e^{-zL}·u0 as
# :func:`propagate` (same complex-z convention, same arg(z) coherence
# dial, same seam-folded Wick factor) computed by a CHEBYSHEV polynomial
# of the operator applied with MATRIX-VECTOR PRODUCTS ONLY — no
# eigendecomposition, no dense e^{-zL} — so it runs on a corpus-scale L
# past the n <= 256 dense-eigensolve cap.
# =====================================================================

#: Initial Chebyshev node count of the adaptive expansion (doubled up to
#: max_degree+1). 64 covers |z|·λ_max up to ~40 at tol 1e-10.
_EPH_SPARSE_M0: int = 64

#: Sanity cap on the caller's max_degree (matches the C peer's bound —
#: keeps the uint32 node count from wrapping and the arena finite).
_EPH_SPARSE_DEGREE_CAP: int = 1 << 28


def _eph_sparse_degrees(
    n: int,
    edge_list: List[Tuple[int, int]],
    w_list: List[float],
) -> Tuple[List[float], float]:
    """Signed degrees ``deg[i] = Σ_incident |w|`` (a Class-K sign BRANCH,
    never ``abs()``; self-loops skipped — the :func:`signed_laplacian`
    convention; duplicate edges read PER-EDGE) + the Gershgorin bound
    ``λ_max = 2·max_i deg[i]`` (the signed Laplacian is PSD, so the
    spectral interval is ``[0, λ_max]`` — deterministic, an overestimate
    only widens the interval). A non-finite weight raises ``ValueError``
    (the C peer's ``SRMECH_ERR_BAD_INPUT``)."""
    deg = [0.0] * n
    for (a, b), w in zip(edge_list, w_list):
        if a == b:
            continue                       # self-loop cancels in D̄ − A
        if not _finite_real(w):
            raise ValueError(
                f"propagate_sparse: edge weight must be finite; got {w!r}")
        m = w if w >= 0.0 else -w          # Class-K magnitude, never abs()
        deg[a] += m
        deg[b] += m
    lam_max = 0.0
    for d in deg:
        if 2.0 * d > lam_max:
            lam_max = 2.0 * d
    return deg, lam_max


def _eph_sparse_coeffs(
    zr: float,
    zi: float,
    cc: float,
    h: float,
    tol: float,
    max_degree: int,
) -> List[complex]:
    """Adaptive Chebyshev interpolation coefficients of the propagator
    scalar ``g(s) = e^{-z·(cc + h·s)}`` on ``s ∈ [-1, 1]`` — the SAME
    schedule as the C peer's ``ephs_expand``: evaluate ``g`` at the M
    Chebyshev nodes ``s_j = cos(π(2j+1)/(2M))`` (the rc136 Wick-factor
    machinery — Class-N exp + the Machin-2π seam-folded cos/sin), form
    ``c_k = (2−δ_k0)/M · Σ_j g(s_j)·cos(k·θ_j)`` with ``cos(k·θ_j)`` by
    the 3-term recurrence (j-outer / k-inner, NO per-(k,j) trig), accept
    when the coefficient tail (the top eighth — the aliasing guard) falls
    below ``tol·max_j|g(s_j)|`` (compared in SQUARES — no ``abs()``, no
    sqrt), else DOUBLE M up to the hard cap ``max_degree+1``. Returns the
    truncated coefficient list ``c_0..c_m``; not converged at the cap →
    honest ``ValueError`` (raise max_degree or shrink |z|)."""
    mcap = max_degree + 1
    M = _EPH_SPARSE_M0 if _EPH_SPARSE_M0 < mcap else mcap
    while True:
        cosn = [0.0] * M
        f = [0j] * M
        scale2 = 0.0
        for j in range(M):
            theta = _PI * (2 * j + 1) / (2.0 * M)
            cth, _sth = _eph_cos_sin(theta)
            lam = cc + h * cth
            fj = _eph_wick_factor(zr, zi, lam)
            if not (_finite_real(fj.real) and _finite_real(fj.imag)):
                raise ValueError(
                    f"propagate_sparse: propagator magnitude e^{{-Re(z)·λ}} "
                    f"overflowed at λ={lam!r} (backward z too large)")
            cosn[j] = cth
            f[j] = fj
            m2 = fj.real * fj.real + fj.imag * fj.imag
            if m2 > scale2:
                scale2 = m2
        coeff = [0j] * M
        for j in range(M):                 # j-outer / k-inner (the C order)
            fj = f[j]
            t_prev = 1.0                   # T_0(s_j)
            t_cur = cosn[j]                # T_1(s_j)
            coeff[0] += fj
            if M > 1:
                coeff[1] += fj * t_cur
            for k in range(2, M):
                t_next = 2.0 * cosn[j] * t_cur - t_prev
                coeff[k] += fj * t_next
                t_prev, t_cur = t_cur, t_next
        inv = 1.0 / M
        coeff[0] *= inv
        for k in range(1, M):
            coeff[k] *= 2.0 * inv
        thresh2 = (tol * tol) * scale2
        m_eff = 0
        for k in range(M - 1, -1, -1):
            ck = coeff[k]
            if ck.real * ck.real + ck.imag * ck.imag > thresh2:
                m_eff = k
                break
        guard = M // 8 if M // 8 > 1 else 1
        if m_eff + guard <= M - 1:
            return coeff[: m_eff + 1]
        if M >= mcap:
            raise ValueError(
                f"propagate_sparse: Chebyshev tail not below tol={tol} within "
                f"max_degree={max_degree} (|z|·λ_max needs a higher degree — "
                f"raise max_degree or shrink |z|)")
        M = 2 * M if M <= mcap // 2 else mcap


def _eph_sparse_matvec(
    n: int,
    edge_list: List[Tuple[int, int]],
    w_list: List[float],
    deg: List[float],
    cc: float,
    hinv: float,
    v: List[complex],
) -> List[complex]:
    """One scaled matvec ``L̃·v = ((L·v) − cc·v)/h`` on the sparse signed
    Laplacian: ``(L v)[i] = deg[i]·v[i] − Σ_{(a,b) edge} w·v[other]`` by
    edge-scatter — the SAME accumulation order as the C peer's
    ``ephs_matvec``. O(n + n_edges) per call; matvec-only is the whole
    point (no dense matrix is ever formed)."""
    out = [deg[i] * v[i] for i in range(n)]
    for (a, b), w in zip(edge_list, w_list):
        if a == b:
            continue                       # self-loop cancels in D̄ − A
        out[a] -= w * v[b]
        out[b] -= w * v[a]
    return [(out[i] - cc * v[i]) * hinv for i in range(n)]


def _eph_propagate_sparse_py(
    n: int,
    edge_list: List[Tuple[int, int]],
    w_list: List[float],
    u,
    zr: float,
    zi: float,
    tol: float,
    max_degree: int,
) -> List[complex]:
    """The pure-Python complete alternative for :func:`propagate_sparse` —
    the Chebyshev cascade (degrees → adaptive coefficients → forward
    ``T_{k+1} = 2·L̃·T_k − T_{k−1}`` vector recurrence), the SAME
    algorithm and accumulation order as the C peer (value-parity within
    tol, not a rescue)."""
    deg, lam_max = _eph_sparse_degrees(n, edge_list, w_list)
    uc = [complex(x) for x in u]
    if lam_max <= 0.0:
        return uc                          # L = 0 → e^{-z·0} = I
    cc = 0.5 * lam_max
    hinv = 2.0 / lam_max
    coeff = _eph_sparse_coeffs(zr, zi, cc, 0.5 * lam_max, tol, max_degree)
    y = [coeff[0] * x for x in uc]
    if len(coeff) > 1:
        v_prev = uc
        v_cur = _eph_sparse_matvec(n, edge_list, w_list, deg, cc, hinv, uc)
        for k in range(1, len(coeff)):
            ck = coeff[k]
            for i in range(n):
                y[i] += ck * v_cur[i]
            if k == len(coeff) - 1:
                break                      # last term: no further matvec
            mv = _eph_sparse_matvec(n, edge_list, w_list, deg, cc, hinv,
                                    v_cur)
            v_next = [2.0 * mv[i] - v_prev[i] for i in range(n)]
            v_prev, v_cur = v_cur, v_next
    return y


def _eph_propagate_sparse_native(
    n: int,
    edge_list: List[Tuple[int, int]],
    w_list: List[float],
    u,
    zr: float,
    zi: float,
    tol: float,
    max_degree: int,
):
    """numpy-free native dispatch for :func:`propagate_sparse` — marshals
    the edge endpoints / weights / interleaved u0 into ctypes buffers and
    calls the standalone-C ``srmech_eph_propagate_sparse`` with a caller
    arena sized from ``srmech_eph_propagate_sparse_arena_bytes``. Returns
    the ``list[complex]`` harvest, or ``None`` on any missing symbol /
    non-OK status (caller then runs the pure-Python complete
    alternative)."""
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_eph_propagate_sparse")
        and hasattr(_native.LIB, "srmech_eph_propagate_sparse_arena_bytes")
    ):
        return None
    n_edges = len(edge_list)
    if n_edges:
        eu = (ctypes.c_uint32 * n_edges)(*(int(a) for a, _ in edge_list))
        ev = (ctypes.c_uint32 * n_edges)(*(int(b) for _, b in edge_list))
        wbuf = (ctypes.c_double * n_edges)(*(float(w) for w in w_list))
    else:
        eu = ev = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint32))
        wbuf = ctypes.cast(None, ctypes.POINTER(ctypes.c_double))
    u_il = []
    for x in u:
        z = complex(x)
        u_il.append(z.real)
        u_il.append(z.imag)
    u_c = (ctypes.c_double * (2 * n))(*u_il)
    out = (ctypes.c_double * (2 * n))()
    deg_used = ctypes.c_uint32(0)
    ws_bytes = _native.LIB.srmech_eph_propagate_sparse_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges),
        ctypes.c_uint32(int(max_degree)),
    )
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_eph_propagate_sparse(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, wbuf, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), ctypes.c_double(tol),
        ctypes.c_uint32(int(max_degree)), out, ctypes.byref(deg_used), ws,
        ctypes.c_size_t(wsd * 8),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [complex(out[2 * i], out[2 * i + 1]) for i in range(n)]


def propagate_sparse(
    n: int,
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    u0,
    z,
    tol: float = 1e-10,
    max_degree: int = 2048,
) -> "Vec":
    """EPH SPARSE — the sparse-scaled propagator ``harvest = e^{-zL}·u0``
    (0.9.0rc206; siona gh#1274 item 1c — the corpus-scale residual).

    The SAME harvest as :func:`propagate` (same complex-z convention, same
    ``arg(z)`` coherence dial — z real → thermal, z imaginary → coherent,
    between → partial — same seam-folded Wick factor) computed by a
    **Chebyshev polynomial of the operator applied with matrix-vector
    products ONLY**: no eigendecomposition, no dense ``e^{-zL}``, so it
    runs on a corpus-scale ``L`` past the ``n ≤ 256`` dense-eigensolve cap
    (``O(m·n_edges)`` time, ``O(n)`` memory, ``m`` = the Chebyshev degree).
    Compose with the Born-rule read exactly as :func:`eph_harvest` does
    over :func:`propagate`.

    The operator is the SIGNED graph Laplacian read straight off the edge
    list (the :func:`signed_laplacian` convention, matching the sparse-
    graph input of :func:`fiedler_sparse` / :func:`spectral_spine`):
    ``(L v)[i] = deg[i]·v[i] − Σ_{(i,j)} w_ij·v[j]`` with the signed degree
    ``deg[i] = Σ_incident |w|`` (Class-K magnitude — a sign branch, never
    ``abs()``), self-loops skipped. Duplicate edges are read PER-EDGE (each
    contributes ``|w|`` to the degree) — pre-merge duplicates that may
    carry opposite signs if exact :func:`signed_laplacian` parity is
    needed for such a list.

    Method (deterministic Chebyshev — no Lanczos, no orthogonalisation, no
    randomness): the spectral interval ``[0, 2·max_i deg[i]]`` by
    Gershgorin (cheap + deterministic; the signed Laplacian is PSD; an
    overestimate only widens the interval), affine-mapped to ``[-1, 1]``;
    Chebyshev interpolation coefficients of ``e^{-z·λ(s)}`` from the
    Chebyshev nodes (the rc136 Wick-factor machinery — Class-N exp + the
    MANDATORY Machin-2π seam-folded cos/sin, so it stays exact at any
    ``t·λ``); the node count adaptively DOUBLES from 64 up to the HARD CAP
    ``max_degree+1``, accepting when the coefficient tail (the top eighth
    — the aliasing guard) falls below ``tol·max|e^{-z·λ}|``; then the
    forward ``T_{k+1} = 2·L̃·T_k − T_{k−1}`` vector recurrence (``T_k`` of
    an operator with spectrum in ``[-1, 1]`` has norm ≤ 1 → stable).

    Convergence regime (honest): the needed degree grows like
    ``|z|·λ_max/2 + O(log 1/tol)`` — super-geometric once past the wave
    zone (the Bessel-tail decay of the exp expansion). Thermal ``z``
    (real, ≥ 0) truncates earliest; coherent ``z`` (imaginary) needs the
    full ``~|z|·λ_max/2`` terms before the tail drops; backward
    propagation (``Re z < 0``) converges but its error is relative to the
    max propagator magnitude over the WHOLE interval
    (``~tol·e^{|Re z|·λ_max}`` absolute — inherent to any polynomial
    approximation of exp on an interval). Not converged within
    ``max_degree`` → an honest ``ValueError`` (raise ``max_degree`` or
    shrink ``|z|``); the tolerance is never silently degraded.

    Parameters
    ----------
    n : int
        Number of graph nodes.
    edges : Iterable[Tuple[int, int]]
        Undirected edges ``(u, v)`` with ``0 ≤ u, v < n`` (the
        :func:`fiedler_sparse` / :func:`signed_laplacian` convention).
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``); same length as ``edges``.
        May be negative — the signed degree keeps ``L`` PSD.
    u0 : Vec | list (keyword-only)
        The excitation vector (length ``n``, real or complex) — the seed
        the propagator acts on (as :func:`propagate`).
    z : complex (keyword-only)
        The complex time; ``arg(z)`` is the coherence dial (as
        :func:`propagate`; a ``[re, im]`` pair is accepted).
    tol : float
        Relative coefficient-tail tolerance (relative to the max
        propagator magnitude over the spectral interval). Default 1e-10.
    max_degree : int
        The HARD Chebyshev degree cap (1 .. 2^28). Default 2048 — covers
        ``|z|·λ_max`` up to ~4000 at the default tol.

    Returns
    -------
    Vec
        The harvest ``e^{-zL}·u0`` — a length-``n`` complex
        :class:`~srmech.math.vec.Vec` (the :func:`propagate` return
        contract). ``n = 0`` gives the empty harvest.

    Native (rc206): dispatches to the standalone-C
    ``srmech_eph_propagate_sparse`` (degrees + node evaluation +
    coefficients + the vector recurrence all in C, caller-arena, no
    caps beyond the caller's ``max_degree``); pure Python is the complete
    alternative — same algorithm, same accumulation order, NUMERIC
    (FPU-tol) within-tol parity (differential-tested), not byte-for-byte.
    numpy-free; no ``abs()`` (Class-K sign branch / magnitude-squares).

    Raises:
        ValueError: bad ``n`` / edge / weight (the
            :func:`fiedler_sparse` contracts), ``len(u0) != n``, a
            non-finite weight, ``tol <= 0``, ``max_degree`` out of range,
            or a coefficient tail not below ``tol`` within ``max_degree``
            (the honest non-convergence).
    """
    edge_list, w_list = _validate_edges_weights_py(n, edges, weights)
    z = complex(z[0], z[1]) if isinstance(z, (list, tuple)) else complex(z)
    u = _vec(u0)
    if len(u) != n:
        raise ValueError(
            f"propagate_sparse: len(u0) ({len(u)}) must equal n ({n})")
    tol = float(tol)
    if not (tol > 0.0):
        raise ValueError(f"propagate_sparse: tol must be > 0; got {tol!r}")
    max_degree = int(max_degree)
    if max_degree < 1 or max_degree > _EPH_SPARSE_DEGREE_CAP:
        raise ValueError(
            f"propagate_sparse: max_degree must be in 1..2^28; got "
            f"{max_degree}")
    if n == 0:
        return Vec(array("d"), 0, is_complex=True)
    harvest = _eph_propagate_sparse_native(
        n, edge_list, w_list, u, z.real, z.imag, tol, max_degree)
    if harvest is None:
        harvest = _eph_propagate_sparse_py(
            n, edge_list, w_list, u, z.real, z.imag, tol, max_degree)
    return Vec.from_sequence(harvest, is_complex=True)


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
    :class:`~srmech.math.vec.Vec` (``.shape == (n,)`` + scalar ``v[i]``;
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


# =====================================================================
# rc204 (gh#1324; F1167–F1169) — the spectral SPINE: the DOMINANT-mode
# read-out that completes the community/spine pair with the LOW-mode
# fiedler_vector / fiedler_sparse (2-way) + three_fold_eigvec_groups (3-way).
# =====================================================================
#
# The community side reads the LOW modes of a graph Laplacian (λ₂ = the Fiedler
# navigation / bisection; the three low/mid/high bands). The SPINE is the dual
# read: the DOMINANT eigenvector (largest λ) of the (signed) Laplacian
# concentrates on the structurally CENTRAL items of the relational graph, so its
# top-|component| nodes ARE the spine (F1167–F1169). Domain-free — the edge list
# is any relational graph (siona describe-spine; ephemerides central bodies).


def _infer_n_from_edges(edge_list: List[Tuple[int, int]]) -> int:
    """The node count of a relational graph given only its edges: one past the
    largest endpoint (isolated high-index nodes carry no relationship, so they
    are never central and their omission never changes the spine). No ``abs()``
    — endpoints are non-negative node indices."""
    n = 0
    for (u, v) in edge_list:
        iu, iv = int(u), int(v)
        if iu + 1 > n:
            n = iu + 1
        if iv + 1 > n:
            n = iv + 1
    return n


def _spine_from_V(V, k: int) -> List[int]:
    """Top-``min(k, n)`` node indices by |component|² of the DOMINANT eigenvector
    (the LAST column of an ascending-eigenvalue ``V`` — the largest λ), ordered by
    descending magnitude, ties broken by ascending index. Class-K magnitude-square
    (``re²+im²``; sign-invariant, so no eigenvector sign-canon is needed) — NO
    ``abs()`` and NO float square root. Mirrors the C ``spine_select_topk`` sort
    key exactly."""
    n_rows = V.n_rows
    if n_rows == 0 or k <= 0:
        return []
    col = V.n_cols - 1  # dominant = largest eigenvalue (ascending spectrum)
    magsq: List[float] = []
    for i in range(n_rows):
        x = V[i, col]
        if isinstance(x, complex):
            magsq.append(x.real * x.real + x.imag * x.imag)
        else:
            magsq.append(x * x)
    order = sorted(range(n_rows), key=lambda i: (-magsq[i], i))
    return order[: min(int(k), n_rows)]


def _spectral_spine_native(n, edge_list, w_list, k) -> Optional[List[int]]:
    """numpy-free native dispatch for :func:`spectral_spine` — marshals the edge
    endpoints (uint32) + weights (double) into ctypes buffers and calls the
    composite C peer ``srmech_spectral_spine`` with a caller arena sized from
    ``srmech_spectral_spine_arena_bytes``. Returns the ``list[int]`` spine, or
    ``None`` on any missing symbol / non-OK status (caller then runs the
    pure-Python complete alternative)."""
    if not _native.has_native_spectral_spine():
        return None
    n_edges = len(edge_list)
    want = min(int(k), n)
    if want <= 0:
        return []
    eu = (ctypes.c_uint32 * n_edges)(*(int(u) for u, _ in edge_list))
    ev = (ctypes.c_uint32 * n_edges)(*(int(v) for _, v in edge_list))
    wb = (ctypes.c_double * n_edges)(*(float(w) for w in w_list))
    out = (ctypes.c_uint32 * want)()
    cnt = ctypes.c_uint32(0)
    ws_bytes = _native.LIB.srmech_spectral_spine_arena_bytes(ctypes.c_uint32(n))
    wsd = int(ws_bytes) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_spectral_spine(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, wb,
        ctypes.c_uint32(int(k)), out, ctypes.byref(cnt), ws,
        ctypes.c_size_t(wsd * 8),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [int(out[i]) for i in range(cnt.value)]


def spectral_spine(
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
    *,
    k: int = 8,
) -> List[int]:
    """The spectral SPINE of a relational graph — the structurally CENTRAL nodes
    (gh#1324; F1167–F1169).

    Build the (signed) Laplacian ``L = D̄ − A`` from the edge list, take the
    DOMINANT eigenvector (the largest-eigenvalue eigenvector via
    :func:`symmetric_eigendecompose`), and return the top-``k`` nodes by
    |component| (Class-K magnitude). The largest-eigenvalue eigenvector of a
    graph Laplacian concentrates on the structurally central items, so its
    top-magnitude nodes ARE the spine — the DOMINANT-mode read-out that completes
    the community/spine PAIR with the LOW-mode :func:`fiedler_vector` /
    :func:`fiedler_sparse` (2-way community) + :func:`three_fold_eigvec_groups`
    (3-way). Domain-free: ``edges`` is any relational graph (siona describe-spine;
    ephemerides central bodies).

    Parameters
    ----------
    edges : Iterable[Tuple[int, int]]
        Undirected relational edges ``(u, v)`` with non-negative node indices.
        The node count ``n`` is inferred as one past the largest endpoint
        (isolated high-index nodes are never central, so their omission never
        changes the spine); mirror the ``(edges, weights)`` convention of the
        other edge-taking Class-L ops (:func:`signed_laplacian` /
        :func:`fiedler_sparse`).
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``); same length as ``edges``. May be
        negative — the signed Laplacian's signed degree ``Σ|A_ij|`` keeps ``L``
        PSD (the dissolved Class-O signed-metric leg).
    k : int
        Spine cap (keyword-only; default 8). At most ``min(k, n)`` node indices
        are returned. ``k <= 0`` → ``[]``.

    Returns
    -------
    list[int]
        Up to ``k`` central node indices, ordered by descending |component| of
        the dominant eigenvector (ties broken by ascending index). ``[]`` for an
        empty graph (no edges → no relational structure).

    Dispatches to the standalone-C composite ``srmech_spectral_spine`` when
    ``HAS_NATIVE`` (the build + eigensolve + top-k selection run in C, caller-
    arena, no caps); else srmech's own pure-Python cascade
    (:func:`signed_laplacian` + :func:`symmetric_eigendecompose` + top-k). NUMERIC
    (FPU-tol): the eigenvector basis is non-unique, so native == pure agrees
    WITHIN-TOL — the selected index set / order is stable for a non-degenerate
    dominant eigenvalue, NOT byte-for-byte. numpy-free; no ``abs()``.
    """
    edge_list = [tuple(e) for e in edges]
    n = _infer_n_from_edges(edge_list)
    if n == 0:
        return []
    _el, w_list = _validate_edges_weights_py(n, edge_list, weights)
    kk = min(int(k), n)
    if kk <= 0:
        return []
    idxs = _spectral_spine_native(n, edge_list, w_list, k)
    if idxs is not None:
        return idxs
    # Pure-Python complete alternative: signed Laplacian → eigendecompose → top-k.
    L = signed_laplacian(n, edge_list, w_list)
    _eigvals, V = symmetric_eigendecompose(L)
    return _spine_from_V(V, kk)


def relational_structure(
    edges: Iterable[Tuple[int, int]],
    weights: Optional[Iterable[float]] = None,
) -> dict:
    """The full spectral structure of a relational graph in ONE call (gh#1324) —
    the ergonomic sugar that composes the Class-L atoms.

    Reads a graph as BOTH its central spine AND its community split from a single
    eigendecomposition of the (signed) Laplacian::

        {"spine": [...],          # top-8 central nodes (the DOMINANT mode)
         "communities": [L, R],   # the Fiedler 2-way sign bisection (the LOW mode)
         "coherence": λ₂}         # algebraic connectivity (the Fiedler value)

    Composes :func:`signed_laplacian` + :func:`symmetric_eigendecompose` (ONE
    eigensolve) + the :func:`spectral_spine` top-k selection (dominant column) +
    the Fiedler sign split (λ₂ column) — no dedicated C symbol, a pure composition
    of the C-backed atoms. ``"communities"`` is ``[left, right]`` where ``left``
    are the negative-Fiedler-sign nodes and ``right`` the non-negative (the
    :func:`normalized_cut_bisect` convention; a Class-K sign split, no ``abs()``).
    ``"coherence"`` is the second-smallest eigenvalue λ₂ (the algebraic
    connectivity — small ⇒ a near-disconnected graph). numpy-free.

    Parameters
    ----------
    edges : Iterable[Tuple[int, int]]
        Undirected relational edges (``n`` inferred as in :func:`spectral_spine`).
    weights : Optional[Iterable[float]]
        Per-edge weights (default all ``1.0``); may be negative.

    Returns
    -------
    dict
        ``{"spine": list[int], "communities": [list[int], list[int]],
        "coherence": float}``. An empty graph → empty spine, empty communities,
        ``coherence = 0.0``; a single node → spine ``[0]``, communities
        ``[[0], []]``, ``coherence = 0.0`` (no λ₂).
    """
    edge_list = [tuple(e) for e in edges]
    n = _infer_n_from_edges(edge_list)
    if n == 0:
        return {"spine": [], "communities": [[], []], "coherence": 0.0}
    _el, w_list = _validate_edges_weights_py(n, edge_list, weights)
    L = signed_laplacian(n, edge_list, w_list)
    eigvals, V = symmetric_eigendecompose(L)  # ascending eigvals, columns = eigvecs
    spine = _spine_from_V(V, min(8, n))
    if n >= 2:
        # λ₂ Fiedler vector = column 1; the sign split is the normalized cut.
        left = [i for i in range(n) if V[i, 1] < 0.0]
        right = [i for i in range(n) if V[i, 1] >= 0.0]
        coherence = float(eigvals[1])
    else:
        left, right = [0], []          # a single node: no bisection
        coherence = 0.0
    return {"spine": spine, "communities": [left, right], "coherence": coherence}


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
    progress=None,
) -> List[float]:
    """Pure-Python sparse normalized-cut Fiedler (the complete no-native path).

    Transcribes the F785/F786-verified prototype: build the normalized operator
    B = I + D^-1/2 W D^-1/2 implicitly, deflate the √deg (λ₀) mode each step,
    power-iterate, stop on sign-stability. No ``abs()``: the max-magnitude
    rescale reads the Class-K magnitude-SQUARE (pin-slot-free) then takes one
    Class-N root; √deg / D^-1/2 are Class-N :func:`~srmech.math.rational.sqrt`.
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
        if progress is not None and progress(
                {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_PARTITIONING,
                 "done": it + 1, "total": int(max_iters)}):
            # §101 CLEAN cancel — the zeroed "no cut" vector, byte-parity with the C
            # overload (which returns out_vec left as the zeroed init on cancel).
            return [0.0] * n
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
    # rc307: ws_len is BYTES (was a DOUBLES count) — pass the buffer's byte size,
    # which comfortably exceeds srmech_laplacian_fiedler_sparse_arena_bytes(n) = 8*n*8.
    rc = _native.LIB.srmech_laplacian_fiedler_sparse(
        ctypes.c_uint32(n),
        ctypes.c_uint32(n_edges),
        eu, ev, wbuf,
        ctypes.c_uint32(int(max_iters)),
        out,
        ws,
        ctypes.c_size_t(ctypes.sizeof(ws)),
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
    # rc307: ws_len is BYTES (was a DOUBLES count) — pass the buffer's byte size.
    rc = _native.LIB.srmech_laplacian_fiedler_sparse_file(
        ctypes.c_uint32(n),
        graph_path.encode("utf-8"),
        ctypes.c_uint32(int(max_iters)),
        out,
        ws,
        ctypes.c_size_t(ctypes.sizeof(ws)),
    )
    if rc != _native.SRMECH_OK:
        return None
    return list(out)


def fiedler_sparse_file(
    n: int,
    graph_path: str,
    *,
    max_iters: int = 250,
    progress=None,
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
    :func:`~srmech.math.text.cooccurrence_topk` for the bounded edge SET). The
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
    if progress is None:
        if _native.has_native_fiedler_sparse_file():
            vals = _fiedler_sparse_file_native(int(n), graph_path, int(max_iters))
            if vals is not None:
                return Vec.from_sequence(vals, is_complex=False)
        edge_list, w_list = _read_packed_graph(graph_path)
        return Vec.from_sequence(
            _fiedler_sparse_py(int(n), edge_list, w_list, int(max_iters)),
            is_complex=False,
        )
    # §101 progress path: the native ENCODE-PROGRESS overload first (same tick
    # sequence + byte-parity), else the pure power loop threaded with the tick. A
    # truthy progress return cancels -> the zeroed "no cut" Vec (bare-return op;
    # the caller owns the callback, so it knows it cancelled — libcurl semantics).
    if _native.has_native_fiedler_sparse_file_progress():
        vals = _native.fiedler_sparse_file_native_progress(
            int(n), graph_path, int(max_iters), progress)
        if vals is not None:
            return Vec.from_sequence(vals, is_complex=False)
    edge_list, w_list = _read_packed_graph(graph_path)
    return Vec.from_sequence(
        _fiedler_sparse_py(int(n), edge_list, w_list, int(max_iters), progress=progress),
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
    progress=None,
) -> Dict[str, object]:
    """Out-of-core recursive spectral partition into community **tomes** (§52 Part 2,
    F793) — the same recursion as bisecting with :func:`normalized_cut_bisect` and
    recursing on each side, but executed **out-of-core**: the adjacency, every pending
    sub-graph, and every finished tome live on **disk**, so peak RAM is the single
    largest sub-graph being bisected (the top-level ``O(n)`` working vectors), not the
    whole structure.

    The bounded graph (e.g. the ``(n, edges, weights)`` from §52.1
    :func:`~srmech.math.text.cooccurrence_topk`) is written to a packed file
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

    # §100 G1 (rc284): the whole `while pending` recursion has a standalone-C peer
    # — queue, induced sub-graphs, sign-split and tome retirement all run in C, so
    # a bare-C host builds the partition with no Python present. The pure driver
    # below is the complete alternative AND the byte-parity oracle: both
    # projections write byte-identical tome files in byte-identical order.
    _rc = _native.recursive_cut_c(
        int(n), graph_path, work_dir, int(max_tome), int(max_iters),
        int(max_depth), int(n) + 1, progress=progress)
    if _rc is not None:
        _paths, _sizes, _cancelled = _rc
        return {
            "n_tomes": len(_paths),
            "tome_paths": _paths,
            "tomes": [_read_node_set(t) for t in _paths],
            "work_dir": work_dir,
            "status": "cancelled" if _cancelled else "ok",
        }

    root = os.path.join(queue_dir, "set_0.bin")
    _write_node_set(root, range(int(n)))
    pending: List[Tuple[str, int]] = [(root, 0)]
    tome_paths: List[str] = []
    serial = 1
    sub_path = os.path.join(work_dir, "sub.bin")
    resolved = 0                                       # §101: Σ finalized-tome sizes (exact,
    #                                                    monotone; == n when pending empties)
    while pending:
        if progress is not None and progress(
                {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_PARTITIONING,
                 "done": resolved, "total": int(n)}):
            # §101 CLEAN partial: promote every still-pending set to a (coarse, uncut)
            # tome. Finalized tomes + promoted pending still partition ALL n nodes — a
            # valid (coarser) partition + a status, never a torn strand. No genome hits
            # disk half-written (recursive_cut only moves whole node-set files).
            for sp, _d in pending:
                dest = os.path.join(tomes_dir, "tome_%d.bin" % len(tome_paths))
                os.replace(sp, dest)
                tome_paths.append(dest)
            if os.path.exists(sub_path):
                os.remove(sub_path)
            return {
                "n_tomes": len(tome_paths),
                "tome_paths": tome_paths,
                "tomes": [_read_node_set(t) for t in tome_paths],
                "work_dir": work_dir,
                "status": "cancelled",
            }
        set_path, depth = pending.pop()
        ids = _read_node_set(set_path)
        if len(ids) <= int(max_tome) or len(ids) < 2 or depth >= int(max_depth):
            dest = os.path.join(tomes_dir, "tome_%d.bin" % len(tome_paths))
            os.replace(set_path, dest)                 # MOVE the survivor, never copy
            tome_paths.append(dest)
            resolved += len(ids)                       # §101 exact progress bookkeeping
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
            resolved += len(ids)                       # §101 exact progress bookkeeping
            continue
        lp = os.path.join(queue_dir, "set_%d.bin" % serial); serial += 1
        rp = os.path.join(queue_dir, "set_%d.bin" % serial); serial += 1
        _write_node_set(lp, left)
        _write_node_set(rp, right)
        pending.append((lp, depth + 1))
        pending.append((rp, depth + 1))
    if os.path.exists(sub_path):
        os.remove(sub_path)
    if progress is not None:                           # §101 terminal 100% heartbeat
        progress({"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_PARTITIONING,
                  "done": resolved, "total": int(n)})  # done == n; return ignored (done)
    return {
        "n_tomes": len(tome_paths),
        "tome_paths": tome_paths,
        "tomes": [_read_node_set(t) for t in tome_paths],
        "work_dir": work_dir,
        "status": "ok",
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
    fan-out as :func:`srmech.cascade.parallel_sector_dispatch`, but over
    DISTINCT spectral blocks rather than chirality-transforms of one input).
    Four ≤256-node blocks reach **4 × 256 = 1024 nodes** within the native
    dense-eig bound. Each worker reads ONLY its own block (0 cross-thread
    reads), so the parallel spectrum equals the serial spectrum bit-for-bit;
    wall-clock overlap depends on the native GIL-release / free-threaded build.

    Class L (graph-spectral eigendecomposition) over the 4-rung parallel
    dispatch. Numpy-free (rc129): a block may be a :class:`~srmech.math.mat.Mat`,
    a ``list[list[float]]`` (numpy-absent) or an ``ndarray``; per-block
    eigenvalues are returned as a 1-D :class:`~srmech.math.vec.Vec` (``.shape ==
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


# ──────────────────────────────────────────────────────────────────────
# Generalized n-gon incidence graph + Feit–Higman spectral read
# (rc399, `#T1064` Tier 3). A generalized n-gon is an INCIDENCE GEOMETRY
# (points + lines + flags) whose bipartite incidence graph has girth 2n,
# diameter n and a Feit–Higman-constrained spectrum. This is a Class-L
# READ of a SUPPLIED combinatorial object — girth/diameter are GRAPH
# metrics (BFS), NOT drawings; nothing here is CAD / continuum
# (`[[feedback_cad_ban_is_gpu_numerical_not_closedform_physical]]`). §3.41.7
# consumes exactly this guarded surface and NOT the Tits–Weiss n=4/6/8
# classification machinery (Albert / char-2 Ree carriers srmech declines).
#
# SSoT: J. Tits & R. Weiss (2002), *Moufang Polygons*, Springer Monographs
# in Mathematics — the Moufang n-gons, n ∈ {3,4,6,8}; H. Van Maldeghem
# (1998), *Generalized Polygons*, Monographs in Mathematics 93, Birkhäuser
# — the Feit–Higman constraint and incidence-graph spectra; W. Feit &
# G. Higman (1964), *J. Algebra* 1, 114–131 — the {2,3,4,6,8} theorem.
# ──────────────────────────────────────────────────────────────────────

#: Thick finite generalized n-gons exist ONLY for these n (Feit–Higman 1964;
#: n=2 is the degenerate complete-bipartite case). Thin (ordinary) n-gons
#: exist for every n.
_FEIT_HIGMAN_THICK_N: Tuple[int, ...] = (2, 3, 4, 6, 8)


def _ngon_bipartite_edges(
    n_points: int, lines: Sequence[Sequence[int]]
) -> "Tuple[int, List[Tuple[int, int]]]":
    """Bipartite incidence graph: vertices ``0..n_points-1`` = points,
    ``n_points..n_points+n_lines-1`` = lines; edge ``(p, n_points+li)`` for each
    point ``p`` on line ``li``. Returns ``(n_vertices, edges)``."""
    edges: List[Tuple[int, int]] = []
    for li, pts_on_line in enumerate(lines):
        for p in pts_on_line:
            if not (0 <= int(p) < n_points):
                raise ValueError(
                    f"generalized_ngon: line {li} references point {p} outside "
                    f"[0, {n_points})")
            edges.append((int(p), n_points + li))
    return n_points + len(lines), edges


def _ngon_adjacency_lists(
    n_vertices: int, edges: Sequence[Tuple[int, int]]
) -> List[List[int]]:
    adj: List[set] = [set() for _ in range(n_vertices)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return [sorted(a) for a in adj]


def _ngon_diameter(adj: List[List[int]]) -> int:
    """Max shortest-path distance (BFS from every vertex). ``-1`` iff the graph
    is disconnected (some pair is unreachable)."""
    from collections import deque

    n = len(adj)
    diam = 0
    for s in range(n):
        dist = [-1] * n
        dist[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for w in adj[u]:
                if dist[w] < 0:
                    dist[w] = dist[u] + 1
                    q.append(w)
        if any(d < 0 for d in dist):
            return -1
        diam = max(diam, max(dist))
    return diam


def _ngon_girth(adj: List[List[int]]) -> int:
    """Length of the shortest cycle (BFS from every vertex, tracking the parent
    so the tree edge is not miscounted). ``-1`` iff the graph is a forest."""
    from collections import deque

    n = len(adj)
    best = -1
    for s in range(n):
        dist = [-1] * n
        par = [-1] * n
        dist[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for w in adj[u]:
                if dist[w] < 0:
                    dist[w] = dist[u] + 1
                    par[w] = u
                    q.append(w)
                elif par[u] != w:
                    cyc = dist[u] + dist[w] + 1
                    if best < 0 or cyc < best:
                        best = cyc
    return best


def _standard_ngon_incidence(name: str) -> "Tuple[int, List[Tuple[int, ...]], int, bool]":
    """The built-in standard incidence structures. Returns
    ``(n_points, lines, expected_n, thick)``.

    * ``"fano"`` — the Fano plane ``PG(2,2)`` (n=3 THICK): 7 points = the nonzero
      vectors of ``𝔽₂³``, 7 lines = the triples XOR-summing to 0. Incidence
      graph = the Heawood graph.
    * ``"doily"`` — the generalized quadrangle ``GQ(2,2)`` / "doily" (n=4 THICK):
      15 points = the duads (2-subsets) of ``{1..6}``, 15 lines = the synthemes
      (partitions into three duads). Incidence graph = the Tutte–Coxeter graph.
    * ``"ordinary_k"`` — the THIN ordinary k-gon (order (1,1)): incidence graph =
      the ``2k``-cycle ``C_{2k}``; valid for every ``k ≥ 2`` (including 6 and 8,
      which the THICK carriers §3.41.7 declines to build).
    """
    key = name.strip().lower()
    if key == "fano":
        lines = []
        for a in range(1, 8):
            for b in range(a + 1, 8):
                c = a ^ b
                if c > b:
                    lines.append((a - 1, b - 1, c - 1))
        return 7, lines, 3, True
    if key == "doily":
        from itertools import combinations

        duads = list(combinations(range(6), 2))
        d_index = {d: i for i, d in enumerate(duads)}
        synthemes: List[tuple] = []
        for a in combinations(range(6), 2):
            rest = [x for x in range(6) if x not in a]
            for b in combinations(rest, 2):
                c = tuple(x for x in rest if x not in b)
                syn = tuple(sorted([a, b, c]))
                if syn not in synthemes:
                    synthemes.append(syn)
        lines = [tuple(d_index[d] for d in syn) for syn in synthemes]
        return len(duads), lines, 4, True
    if key.startswith("ordinary_"):
        try:
            k = int(key.split("_", 1)[1])
        except ValueError:
            k = -1
        if k >= 2:
            return k, [(i, (i + 1) % k) for i in range(k)], k, False
    raise ValueError(
        f"generalized_ngon: unknown example {name!r}; known: 'fano' (n=3), "
        f"'doily' (n=4), 'ordinary_k' for k≥2 (thin k-gon = C_2k)")


def generalized_ngon(
    n_points: Optional[int] = None,
    lines: Optional[Sequence[Sequence[int]]] = None,
    example: Optional[str] = None,
    spectral_max_nodes: int = 256,
) -> Dict[str, Any]:
    """VALIDATE + spectrally READ a generalized n-gon from its incidence
    structure — the bipartite incidence-graph girth/diameter/biregularity plus
    the Feit–Higman spectral constraint (rc399, `#T1064`, Class-L, guarded).

    A **generalized n-gon** is an incidence geometry (points, lines, flags) whose
    bipartite **incidence graph** (point ↔ line, edge = flag) has girth ``2n``,
    diameter ``n`` and is biregular of order ``(s, t)`` (every line has ``s+1``
    points, every point lies on ``t+1`` lines). Its incidence graph is
    **distance-regular** of diameter ``n``, hence has exactly ``n+1`` distinct
    adjacency eigenvalues — the checkable Feit–Higman/Higman spectral constraint.
    This op is a **read of a SUPPLIED object**: girth and diameter are BFS graph
    metrics (never a drawing — nothing here is CAD / continuum); the spectrum
    routes through the shipped :func:`dense_adjacency` + :func:`jacobi_eigvals`.

    Supply either an ``example`` name or an explicit ``(n_points, lines)``:

    * ``example="fano"`` — the Fano plane (n=3 THICK; Heawood incidence graph).
    * ``example="doily"`` — ``GQ(2,2)`` (n=4 THICK; Tutte–Coxeter incidence
      graph).
    * ``example="ordinary_k"`` — the THIN ordinary k-gon ``C_{2k}`` (any ``k≥2``).
    * ``n_points`` + ``lines`` — an arbitrary structure (``lines`` = a sequence
      of point-index sequences).

    ⚠️ **Scope (honest, §3.41.7).** The THICK n=3 and n=4 examples are built from
    pure combinatorics (𝔽₂³ / the S₆ duads–synthemes) with NO exceptional-group
    machinery. The THICK **n=6** (split Cayley hexagon, needs G₂) and **n=8**
    (Ree–Tits octagon, needs the char-2 ²F₄) built-ins are **NOT** provided —
    they require the Albert / char-2 Ree carriers §3.41.7 deliberately declines.
    For n=6/8 the THIN ordinary k-gon (``ordinary_6`` / ``ordinary_8``) is the
    carrier-free witness that girth ``2n`` / diameter ``n`` hold; a SUPPLIED
    thick n=6/8 structure is validated and classified correctly all the same.

    Args:
        n_points: number of points (with ``lines``); ignored if ``example`` set.
        lines: a sequence of point-index sequences (one per line); ignored if
            ``example`` set.
        example: a built-in structure name (see above); when given, ``n_points``
            / ``lines`` are derived from it.
        spectral_max_nodes: skip the adjacency-spectrum read above this vertex
            count (default 256, the native Jacobi bound); girth/diameter are
            still computed. Set ``0`` to skip the spectral read entirely.

    Returns:
        A ``dict`` with: ``n`` (girth//2, the polygon order, ``None`` if not a
        polygon), ``n_points`` / ``n_lines`` / ``n_vertices``, ``girth`` /
        ``diameter``, ``point_degree`` / ``line_size`` and the geometry order
        ``order_s`` (= line_size−1) / ``order_t`` (= point_degree−1),
        ``biregular`` / ``connected`` (bool), ``thick`` (bool, ``s,t ≥ 2``),
        ``feit_higman_allowed`` (``n`` in ``{2,3,4,6,8}`` when thick, else any
        ``n`` for thin), ``is_generalized_polygon`` (the combinatorial verdict),
        ``eigenvalues`` (sorted floats, or ``None`` if skipped) /
        ``distinct_eigenvalues`` / ``n_distinct_eigenvalues``,
        ``spectral_consistent`` (``n_distinct == diameter+1``), and ``example``.

    Note:
        The graph build + spectrum are ``composition_of_c`` over the C-dispatched
        :func:`dense_adjacency` / :func:`jacobi_eigvals`; the girth/diameter BFS
        is exact integer glue (Class L). NO new C symbol —
        ``SRMECH_ABI_VERSION`` unchanged.

    Canonical SSoT: Feit & Higman (1964), *J. Algebra* **1** 114–131 (the
    ``{2,3,4,6,8}`` theorem); Van Maldeghem (1998), *Generalized Polygons*
    (incidence-graph spectra); Tits & Weiss (2002), *Moufang Polygons*.
    """
    if example is not None:
        np_, lns, _expected, _thick = _standard_ngon_incidence(str(example))
        n_points, lines = np_, lns
    if n_points is None or lines is None:
        raise ValueError(
            "generalized_ngon: supply either example= or both n_points= and "
            "lines=")
    n_points = int(n_points)
    lines = [tuple(int(p) for p in ln) for ln in lines]
    n_lines = len(lines)

    n_vertices, edges = _ngon_bipartite_edges(n_points, lines)
    adj = _ngon_adjacency_lists(n_vertices, edges)

    # biregularity: point-degrees vs line-sizes (each a singleton set ⟺ regular)
    point_degs = {len(adj[i]) for i in range(n_points)}
    line_degs = {len(adj[n_points + i]) for i in range(n_lines)}
    biregular = len(point_degs) == 1 and len(line_degs) == 1
    point_degree = next(iter(point_degs)) if len(point_degs) == 1 else None
    line_size = next(iter(line_degs)) if len(line_degs) == 1 else None
    order_s = (line_size - 1) if line_size is not None else None
    order_t = (point_degree - 1) if point_degree is not None else None

    diameter = _ngon_diameter(adj)
    connected = diameter >= 0
    girth = _ngon_girth(adj)

    n = (girth // 2) if (girth > 0 and girth % 2 == 0) else None
    thick = bool(order_s is not None and order_t is not None
                 and order_s >= 2 and order_t >= 2)
    feit_higman_allowed = (n in _FEIT_HIGMAN_THICK_N) if thick else (n is not None)

    # spectral read — the Feit–Higman distinct-eigenvalue constraint
    eigenvalues: Optional[List[float]] = None
    distinct_eigenvalues: Optional[List[float]] = None
    n_distinct: Optional[int] = None
    spectral_consistent: Optional[bool] = None
    if spectral_max_nodes and n_vertices <= spectral_max_nodes:
        A = dense_adjacency(n_vertices, edges)
        ev = jacobi_eigvals(A)
        eigenvalues = sorted(round(float(x), 6) for x in ev)
        distinct_eigenvalues = []
        for x in eigenvalues:
            # eigenvalues is sorted ascending, so x >= the last kept value: the gap
            # is non-negative by construction and needs no abs() (a Class-K magnitude
            # would be a no-op here — there is no sign to re-apply).
            if not distinct_eigenvalues or (x - distinct_eigenvalues[-1]) > 1e-6:
                distinct_eigenvalues.append(x)
        n_distinct = len(distinct_eigenvalues)
        spectral_consistent = (connected and n_distinct == diameter + 1)

    is_generalized_polygon = bool(
        connected
        and biregular
        and n is not None
        and diameter == n
        and girth == 2 * n
        and (spectral_consistent in (None, True))
    )

    return {
        "n": n,
        "n_points": n_points,
        "n_lines": n_lines,
        "n_vertices": n_vertices,
        "girth": girth,
        "diameter": diameter,
        "point_degree": point_degree,
        "line_size": line_size,
        "order_s": order_s,
        "order_t": order_t,
        "biregular": biregular,
        "connected": connected,
        "thick": thick,
        "feit_higman_allowed": feit_higman_allowed,
        "is_generalized_polygon": is_generalized_polygon,
        "eigenvalues": eigenvalues,
        "distinct_eigenvalues": distinct_eigenvalues,
        "n_distinct_eigenvalues": n_distinct,
        "spectral_consistent": spectral_consistent,
        "example": str(example) if example is not None else None,
    }


# Registry of available Class L op names for the composition engine.
# Order is documentary; consumers iterate by name not position.
LAPLACIAN_OPS: Tuple[str, ...] = (
    "dense_adjacency",
    "dense_laplacian",
    "normalized_laplacian",
    "mass_normalized_laplacian",
    "cotangent_weights",
    "signed_laplacian",
    "magnetic_laplacian",
    "quaternion_laplacian",
    "octonion_laplacian",
    "hypercomplex_perspectives",
    "klein4_gain_laplacian",
    "klein4_relational_structure",
    "cycle_holonomy",
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
    "heat_trace",
    "ground_state_flux_response",
    "propagate",
    "eph_harvest",
    "propagate_sparse",
    "propagate_wound",
    "responsion",
    "dense_solve",
    "schur_complement",
    "dirichlet_to_neumann",
    "generalized_ngon",
)
