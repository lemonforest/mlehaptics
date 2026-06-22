"""Path A ICA-JADE — joint approximate diagonalisation of eigen-matrices.

Identity per the implementation plan §1: ICA-JADE IS a Class L (joint
diagonalisation of fourth-order cumulant matrices) ∘ Class K (independence
threshold / projection onto the maximally-decorrelated basis) composition.

The closed-form reference ships a simplified JADE-style ICA via FastICA-
adjacent approach: whitening (PCA) + Givens-rotation-based joint diagonal-
isation of cumulant slices.

Path B dual in Phase 6 (Path B joint diagonalisation in B-native
eigendecomposition).

rc126 (#564): this is the **last** ``srmech.signal_processing`` numpy CARRIER —
flipped numpy-FREE so the whole subpackage imports + runs with numpy genuinely
absent. The covariance eigendecomposition routes through the numpy-free
``mat_hermitian_eigendecompose`` over the :class:`~srmech.amsc.mat.Mat` carrier
(NOT the carrier ``hermitian_eigendecompose`` / ``dense_matmul_real`` /
``elementwise_sqrt``, which RAISE numpy-absent); the whitening / cumulant /
Givens-rotation linear algebra are explicit numpy-free loops over plain Python
``float`` lists (the 4-D cumulant tensor is nested lists — `Mat` is 2-D only —
and the two cumulant rotations are explicit first-axis contractions, preserving
the original behaviour byte-for-byte incl. the inert ``if False`` branch);
whitening magnitudes use the Class-N ``rational.sqrt`` and the Givens angle the
Class-N ``rational.atan2``/``cos``/``sin``. ``op`` returns the sources ``S`` and
unmixing matrix ``W`` as :class:`Mat` (was an array return).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Cardoso &
Souloumiac (1993) original JADE + Hyvarinen & Oja (2000) ICA survey.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import mat_hermitian_eigendecompose
from srmech.amsc.mat import Mat

OPERATION_NAME = "ica_jade"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "shallow-cascade-iterative"
SSOT_CITATION = (
    "Cardoso & Souloumiac (1993), 'Blind beamforming for non-Gaussian "
    "signals', IEE Proc. F 140(6), 362-370. DOI 10.1049/ip-f-2.1993.0054 "
    "(Crossref). Hyvarinen & Oja (2000), 'Independent component analysis: "
    "Algorithms and applications', Neural Networks 13(4-5), 411-430. DOI "
    "10.1016/S0893-6080(00)00026-5."
)


def _abs(x: float) -> float:
    """Class-K sign-branch magnitude (no ALU ``abs()``)."""
    return x if x >= 0.0 else -x


def _matmul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Real dense matrix product ``a·b`` as an explicit triple-loop (numpy-free)."""
    r = len(a)
    inner = len(b)
    cols = len(b[0]) if b else 0
    out = [[0.0] * cols for _ in range(r)]
    for i in range(r):
        ai = a[i]
        oi = out[i]
        for t in range(inner):
            scale = ai[t]
            if scale == 0.0:
                continue
            bt = b[t]
            for j in range(cols):
                oi[j] += scale * bt[j]
    return out


def _rotate_first_axis(
    cum: List[List[List[List[float]]]], g: List[List[float]], k: int
) -> List[List[List[List[float]]]]:
    """``out[a,j,l,m] = Σ_i G[i,a]·cum[i,j,l,m]`` — the numpy-free equivalent of
    rotating the cumulant tensor's first axis by ``G.T`` (``G.T[a,i] = G[i,a]``)."""
    out = [[[[0.0] * k for _ in range(k)] for _ in range(k)] for _ in range(k)]
    for a in range(k):
        oa = out[a]
        for i in range(k):
            g_ia = g[i][a]
            if g_ia == 0.0:
                continue
            ci = cum[i]
            for j in range(k):
                cij = ci[j]
                oaj = oa[j]
                for l in range(k):
                    cijl = cij[l]
                    oajl = oaj[l]
                    for m in range(k):
                        oajl[m] += g_ia * cijl[m]
    return out


def op(
    X,
    *,
    n_components: Optional[int] = None,
    max_iter: int = 100,
    tol: float = 1e-6,
    D: int = 8192,
) -> Tuple["Mat", "Mat"]:
    """Independent-component-analysis via simplified JADE-style cumulant diagonalisation.

    Parameters
    ----------
    X:
        ``(n_samples, n_features)`` observation matrix (any 2-D sequence).
    n_components:
        Number of independent components; default = n_features.
    max_iter:
        Maximum Givens-sweep iterations.
    tol:
        Convergence tolerance on off-diagonal cumulant magnitude.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        ``(S, W)`` where ``S`` is the recovered sources ``(n_samples, k)``
        and ``W`` is the unmixing matrix ``(k, n_features)`` — both
        :class:`~srmech.amsc.mat.Mat` (rc126: numpy-free).
    """
    rows = [[float(v) for v in row] for row in X]
    n = len(rows)
    p = len(rows[0]) if n else 0
    if n == 0 or any(len(row) != p for row in rows):
        raise ValueError(f"ica_jade expects 2-D X; got {(n, p)}")
    if n_components is None:
        n_components = p
    k = n_components
    # Centring (subtract per-feature mean).
    means = [sum(rows[t][c] for t in range(n)) / n for c in range(p)]
    Xc = [[rows[t][c] - means[c] for c in range(p)] for t in range(n)]
    # Whitening via PCA (Class L: covariance eigendecomposition). ``cov`` is a
    # REAL symmetric covariance; the whitening arithmetic is real, so take the
    # (mathematically exact) real part of the always-complex eigenvectors.
    cov = [[0.0] * p for _ in range(p)]
    for a in range(p):
        for b in range(a, p):
            s = 0.0
            for t in range(n):
                s += Xc[t][a] * Xc[t][b]
            v = s / n
            cov[a][b] = v
            cov[b][a] = v
    evals_mat, evecs_mat = mat_hermitian_eigendecompose(
        Mat.from_rows(cov, is_complex=True)
    )
    eigvals = [complex(evals_mat[i, 0]).real for i in range(p)]
    eigvecs = [[complex(evecs_mat[i, j]).real for j in range(p)] for i in range(p)]
    # Sort by descending eigenvalue.
    order = sorted(range(p), key=lambda idx: eigvals[idx], reverse=True)
    # Keep top n_components and whiten. ``W_whiten = diag(1/√λ) · Vᵀ`` (k×p).
    lam = [eigvals[order[c]] if eigvals[order[c]] > 1e-12 else 1e-12 for c in range(k)]
    # Whitening magnitudes feed the float JADE Givens sweep below (an iterative
    # FPU diagonaliser); the exact-Q roots rotate to float here so the sweep
    # stays on the FPU (Q carried through the sweep would grow num/den each pass).
    inv_sqrt = [1.0 / float(_srn.sqrt(lam[c])) for c in range(k)]
    W_whiten = [[inv_sqrt[c] * eigvecs[i][order[c]] for i in range(p)] for c in range(k)]
    # Whitened sources ``Z = (W_whiten · Xᵀ)ᵀ`` (n×k).
    Z = [
        [sum(Xc[t][i] * W_whiten[c][i] for i in range(p)) for c in range(k)]
        for t in range(n)
    ]

    # Fourth-order cumulant approximation (JADE simplified). The 4-D tensor is
    # nested Python lists — ``Mat`` is 2-D only.
    cumulants = [
        [[[0.0] * k for _ in range(k)] for _ in range(k)] for _ in range(k)
    ]
    for i in range(k):
        for j in range(k):
            for l in range(k):
                for m in range(k):
                    s = 0.0
                    for t in range(n):
                        s += Z[t][i] * Z[t][j] * Z[t][l] * Z[t][m]
                    v = s / n
                    if (i == j) and (l == m):
                        v -= 1.0
                    if (i == l) and (j == m):
                        v -= 1.0
                    if (i == m) and (j == l):
                        v -= 1.0
                    cumulants[i][j][l][m] = v

    # Joint diagonalisation via Givens sweeps.
    V = [[1.0 if a == b else 0.0 for b in range(k)] for a in range(k)]
    for _it in range(max_iter):
        off = 0.0
        for i in range(k):
            for j in range(i + 1, k):
                # JADE simplified Givens: rotate to diagonalise the (i, j) slice.
                num = 2.0 * cumulants[i][j][i][j]
                den = cumulants[i][i][i][i] - cumulants[j][j][j][j]
                # Class-K sign-branch (no abs()).
                if _abs(num) + _abs(den) < 1e-15:
                    continue
                theta = 0.25 * _srn.atan2(num, den + 1e-15)
                # Class-K sign-branch (no abs()).
                if _abs(theta) < tol:
                    continue
                off += _abs(theta)
                c, s = float(_srn.cos(theta)), float(_srn.sin(theta))  # float Givens
                # Givens rotation G.
                G = [[1.0 if a == b else 0.0 for b in range(k)] for a in range(k)]
                G[i][i] = c
                G[j][j] = c
                G[i][j] = -s
                G[j][i] = s
                # Apply rotation to V and to the cumulant slices.
                V = _matmul(V, G)
                # Rotate cumulant tensor along the first axis, TWICE per Givens
                # step (the original applied the same first-axis rotation twice;
                # the alternate subscript sat behind an inert ``if False``), so
                # the behaviour is preserved exactly — carrier-swap, not bugfix.
                cumulants = _rotate_first_axis(cumulants, G, k)
                cumulants = _rotate_first_axis(cumulants, G, k)
        if off < tol:
            break

    # ``W = Vᵀ · W_whiten`` (k×p); ``S = (W · Xᵀ)ᵀ`` (n×k).
    Vt = [[V[a][b] for a in range(k)] for b in range(k)]
    W = _matmul(Vt, W_whiten)
    S = [
        [sum(Xc[t][i] * W[c][i] for i in range(p)) for c in range(k)]
        for t in range(n)
    ]
    return Mat.from_rows(S, is_complex=False), Mat.from_rows(W, is_complex=False)
