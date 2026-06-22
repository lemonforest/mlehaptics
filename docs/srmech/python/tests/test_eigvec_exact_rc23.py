"""0.9.0rc23 — exact EIGENVECTORS via the ``Qalg`` number-field carrier (rc-D).

srmech already had exact eigenVALUES (``eigvals_exact`` — char-poly → Yun → Sturm
→ Fraction bisection). The genuinely-new rc-D capability the rotation-last audit
unlocked is exact eigenVECTORS: for an integer/rational matrix ``A`` and an
eigenvalue λ that is a root of an IRREDUCIBLE integer polynomial ``m``, ℚ(λ) =
ℚ[x]/(m) is a FIELD, so the eigenvector is a null-space vector of ``A − λI`` over
that field. ``eigvec_exact`` builds ``M = A − λI`` with ``Qalg`` entries and does
EXACT Gaussian elimination over the ``Qalg`` field; the body stays exact ``Q``,
the ONE terminal rotation is per-component ``.to_complex()`` / ``.to_float()`` in
``eigvec_exact_float`` (rotation-last). This ratchet proves:

1. **A=[[1,1],[1,2]]** (char poly λ²−3λ+1, ℚ(√5)) — exact eigenvector for BOTH
   roots λ=(3±√5)/2; the eigen-relation ``A·v == λ·v`` holds EXACTLY over Qalg;
   the float read-out matches a numeric cross-check (up to scale).
2. **A 3×3 integer matrix** with an irreducible cubic (companion of x³−x−1) —
   exact eigenvector, eigen-relation exact over Qalg, float read-out matches an
   independent numeric eigenvector up to scale.
3. **Rational-eigenvalue degenerate case** (m linear, ℚ(λ)=ℚ): A=[[2,1],[1,2]],
   λ=3→[1,1], λ=1→[1,−1] (exact rational eigenvectors).
4. **Reducible-m guard** — a ``lam`` over a reducible ``m`` raises a clear
   ``ValueError`` (ℚ[x]/(m) is not a field).
5. Determinism + the multi-dimensional-null-space (repeated eigenvalue) case
   returns ``list[list[Qalg]]`` as documented.

Eigenvectors are defined only UP TO SCALE, so all eigenvector comparisons here
check proportionality (cross-ratio), not literal equality — the free-variable
convention can return any nonzero scalar multiple of the eigenvector.

The whole module is numpy-free (it runs on the numpy-ABSENT matrix).
"""

from __future__ import annotations

import importlib.util
from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.qalg import Qalg
from srmech.amsc.cascade.matrix_cascades import (
    eigvec_exact,
    eigvec_exact_float,
    eigvals_exact,
)


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this eigvec_exact ratchet must run on the numpy-ABSENT matrix")


# ── exact / float helpers (eigenvectors compared UP TO SCALE) ────────────────
def _matvec(A, v):
    """``A·v`` over whatever scalar type the entries are (Qalg / float)."""
    n = len(A)
    out = []
    for i in range(n):
        acc = None
        for j in range(n):
            term = v[j] * A[i][j]
            acc = term if acc is None else acc + term
        out.append(acc)
    return out


def _eigen_relation_exact(A, v, lam):
    """``A·v == λ·v`` EXACTLY over Qalg, componentwise."""
    Av = _matvec(A, v)
    return all(Av[i] == lam * v[i] for i in range(len(v)))


def _proportional_float(u, w, tol=1e-9):
    """True iff float vectors ``u``, ``w`` are scalar multiples (cross-ratio = 0
    on every coordinate pair: ``u[i]·w[j] == u[j]·w[i]``)."""
    n = len(u)
    for i in range(n):
        for j in range(n):
            if abs(u[i] * w[j] - u[j] * w[i]) > tol:
                return False
    return True


def _abs(x):
    """Class-K magnitude (sign-branch, not the ALU builtin) for tolerance checks."""
    return x if x >= 0 else -x


def _independent_float_eigenvector(A, lam_float, tol=1e-12):
    """An INDEPENDENT float eigenvector of ``A`` for eigenvalue ``lam_float`` via
    a small float Gaussian elimination on ``A − λI`` (does NOT call
    ``eigvec_exact``) — the numeric cross-check oracle, returned up to scale."""
    n = len(A)
    M = [[float(A[i][j]) - (lam_float if i == j else 0.0) for j in range(n)]
         for i in range(n)]
    r = 0
    pivot_row_of_col = {}
    for c in range(n):
        p = None
        for rr in range(r, n):
            if _abs(M[rr][c]) > tol:
                p = rr
                break
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        inv = 1.0 / M[r][c]
        M[r] = [x * inv for x in M[r]]
        for rr in range(n):
            if rr != r and _abs(M[rr][c]) > tol:
                f = M[rr][c]
                M[rr] = [M[rr][j] - f * M[r][j] for j in range(n)]
        pivot_row_of_col[c] = r
        r += 1
    free = [c for c in range(n) if c not in pivot_row_of_col]
    v = [0.0] * n
    fc = free[0]
    v[fc] = 1.0
    for c in pivot_row_of_col:
        v[c] = -M[pivot_row_of_col[c]][fc]
    return v


# ── 1. A=[[1,1],[1,2]] — char poly λ²−3λ+1, ℚ(√5) ───────────────────────────
_A2 = [[1, 1], [1, 2]]
_M2 = (1, -3, 1)                                   # λ²−3λ+1, low→high, monic


def test_2x2_sqrt5_plus_root_exact_eigenvector():
    """λ = (3+√5)/2 — exact eigenvector + exact eigen-relation + float read-out."""
    root = (3 + 5 ** 0.5) / 2
    lam = Qalg.alpha(_M2, root=root)
    v = eigvec_exact(_A2, lam)
    # exact eigen-relation over Qalg (the op also asserts this internally)
    assert _eigen_relation_exact(_A2, v, lam)
    # float read-out: the eigenvector is [λ−2, 1] ∝ [1, λ−1]; check up to scale
    vf = eigvec_exact_float(_A2, lam)
    assert _proportional_float(vf, [1.0, root - 1.0])
    # and the float eigen-relation A·v ≈ λ·v
    Av = _matvec([[float(x) for x in r] for r in _A2], vf)
    assert all(_abs(Av[i] - root * vf[i]) < 1e-9 for i in range(2))


def test_2x2_sqrt5_minus_root_exact_eigenvector():
    """λ = (3−√5)/2 — the OTHER root; same field m, different embedding root."""
    root = (3 - 5 ** 0.5) / 2
    lam = Qalg.alpha(_M2, root=root)
    v = eigvec_exact(_A2, lam)
    assert _eigen_relation_exact(_A2, v, lam)
    vf = eigvec_exact_float(_A2, lam)
    assert _proportional_float(vf, [1.0, root - 1.0])
    Av = _matvec([[float(x) for x in r] for r in _A2], vf)
    assert all(_abs(Av[i] - root * vf[i]) < 1e-9 for i in range(2))


def test_2x2_real_root_gives_float_not_complex():
    """A real embedding root → ``to_float`` per component → a list[float]."""
    root = (3 + 5 ** 0.5) / 2
    lam = Qalg.alpha(_M2, root=root)
    vf = eigvec_exact_float(_A2, lam)
    assert all(isinstance(x, float) for x in vf)


# ── 2. a 3×3 integer matrix with an irreducible cubic (x³−x−1) ──────────────
# Companion matrix of x³ − x − 1 (irreducible over ℚ; the plastic number ρ).
_A3 = [[0, 0, 1], [1, 0, 1], [0, 1, 0]]
_M3 = (-1, -1, 0, 1)                               # x³ − x − 1, low→high, monic


def test_3x3_irreducible_cubic_exact_eigenvector():
    """The real eigenvalue ρ ≈ 1.3247 of x³−x−1 — exact eigenvector over ℚ(ρ),
    exact eigen-relation, float read-out matches an independent numeric vector."""
    roots = eigvals_exact(_A3)                      # the one real eigenvalue
    assert len(roots) == 1
    root = roots[0]
    lam = Qalg.alpha(_M3, root=root)
    v = eigvec_exact(_A3, lam)
    assert len(v) == 3
    assert _eigen_relation_exact(_A3, v, lam)
    # float read-out + numeric cross-check (build the eigenvector independently).
    vf = eigvec_exact_float(_A3, lam)
    Af = [[float(x) for x in r] for r in _A3]
    Av = _matvec(Af, vf)
    assert all(_abs(Av[i] - root * vf[i]) < 1e-9 for i in range(3))
    # Independent numeric eigenvector (built by a separate float Gaussian
    # elimination, NOT eigvec_exact) — confirm proportionality up to scale.
    indep = _independent_float_eigenvector(_A3, root)
    assert _proportional_float(vf, indep)


# ── 3. rational-eigenvalue degenerate case (m linear, ℚ(λ)=ℚ) ───────────────
_A2S = [[2, 1], [1, 2]]                            # eigenvalues 3 and 1


def test_rational_eigenvalue_three():
    """λ = 3, m=(-3,1) linear ⇒ ℚ(λ)=ℚ ⇒ a purely RATIONAL eigenvector [1,1]."""
    lam = Qalg.alpha((-3, 1), root=3.0)
    v = eigvec_exact(_A2S, lam)
    assert _eigen_relation_exact(_A2S, v, lam)
    # exact rational eigenvector: each coord is a rational constant (degree-0).
    assert all(c.coords[0].denominator == 1 for c in v)
    vf = eigvec_exact_float(_A2S, lam)
    assert _proportional_float(vf, [1.0, 1.0])


def test_rational_eigenvalue_one():
    """λ = 1, m=(-1,1) ⇒ eigenvector [1,−1] (exact rational)."""
    lam = Qalg.alpha((-1, 1), root=1.0)
    v = eigvec_exact(_A2S, lam)
    assert _eigen_relation_exact(_A2S, v, lam)
    vf = eigvec_exact_float(_A2S, lam)
    assert _proportional_float(vf, [1.0, -1.0])


# ── 4. reducible-m guard ─────────────────────────────────────────────────────
def test_reducible_m_raises_clear_value_error():
    """A ``lam`` over a REDUCIBLE m (x²−1 = (x−1)(x+1)) makes ℚ[x]/(m) a non-field;
    a zero-divisor pivot is hit ⇒ a clear ``ValueError`` (NOT a bare
    ZeroDivisionError)."""
    A = [[1, 0], [0, 3]]
    m_red = (-1, 0, 1)                              # x²−1, REDUCIBLE
    lam = Qalg.alpha(m_red, root=1.0)
    with pytest.raises(ValueError, match="IRREDUCIBLE"):
        eigvec_exact(A, lam)


# ── 5. determinism + the multi-dimensional-null-space case ──────────────────
def test_determinism():
    root = (3 + 5 ** 0.5) / 2
    lam = Qalg.alpha(_M2, root=root)
    v1 = eigvec_exact(_A2, lam)
    v2 = eigvec_exact(_A2, lam)
    assert [c.coords for c in v1] == [c.coords for c in v2]
    assert eigvec_exact_float(_A2, lam) == eigvec_exact_float(_A2, lam)


def test_multi_dimensional_null_space_returns_all_basis_vectors():
    """A repeated eigenvalue with geometric multiplicity > 1 (A = 2·I, λ=2 has a
    2-D eigenspace) returns ``list[list[Qalg]]`` — one basis vector per free
    column — and each independently satisfies the eigen-relation."""
    A = [[2, 0], [0, 2]]
    lam = Qalg.alpha((-2, 1), root=2.0)            # λ=2, linear m
    res = eigvec_exact(A, lam)
    # documented multi-dim shape: a list of basis vectors (list-of-lists)
    assert isinstance(res, list) and res and isinstance(res[0], list)
    assert len(res) == 2                            # 2-D eigenspace
    for vec in res:
        assert _eigen_relation_exact(A, vec, lam)
    # float read-out mirrors the nested shape
    vf = eigvec_exact_float(A, lam)
    assert isinstance(vf[0], list) and len(vf) == 2


def test_eigvec_exact_float_requires_root():
    """``eigvec_exact_float`` needs an embedding root for the terminal projection."""
    lam = Qalg.alpha(_M2)                           # no root attached
    with pytest.raises(ValueError, match="root"):
        eigvec_exact_float(_A2, lam)


def test_lam_must_be_qalg():
    """A non-Qalg ``lam`` is a clear TypeError."""
    with pytest.raises(TypeError):
        eigvec_exact(_A2, 1.5)


def test_eigvec_exact_accepts_fraction_and_q_coords_path():
    """Sanity: the exact path is pure Q/Qalg — eigenvector coords are Qalg over
    the supplied m (no float leaks into the body)."""
    root = (3 + 5 ** 0.5) / 2
    lam = Qalg.alpha(_M2, root=root)
    v = eigvec_exact(_A2, lam)
    assert all(isinstance(c, Qalg) for c in v)
    assert all(isinstance(c.coords[0], Q) for c in v)
    # an irrational coord (α-bearing) is present — the eigenvector is genuinely
    # in ℚ(√5), not ℚ (one coord has a nonzero α-coefficient).
    assert any(c.coords[1] != Fraction(0) for c in v)
