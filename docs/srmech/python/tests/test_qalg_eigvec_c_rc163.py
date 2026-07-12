"""Qalg TAIL Batch 7a (0.9.0rc163): the exact EIGENVECTORS over the number field
ℚ(λ) = ℚ[x]/(m) (``eigvec_exact`` + ``eigvec_exact_float``) earn a
``srmech_bigint``-backed C path — the SECOND hard Qalg foundation (the
eigenvectors carry ALGEBRAIC-NUMBER, not plain-ℚ, coordinates).

The NEW C kernel ``srmech_eigvec_exact`` builds ``M = A − λI`` with ``Qalg``
entries and runs EXACT Gaussian elimination over the ℚ(λ) FIELD — pivot on the
first nonzero ``Qalg`` at/below the current row, normalise by the pivot's ``Qalg``
INVERSE (extended Euclid on ℚ[x]), clear every other row — then reads the
null-space basis off the canonical RREF. The Qalg field arithmetic COMPOSES the
exact-Q ``srmech_poly_*`` kernels (add/sub coefficientwise; mul = convolution then
REDUCE mod m via ``srmech_poly_divmod``; inverse = the extended Euclidean algorithm
``b⁻¹ = u/g`` mod m). Byte/structurally-identical to the pure ``_eigvec_exact_qalg``
(the RREF is canonical).

This test pins:
  1. the native ``srmech_eigvec_exact`` symbol is actually loaded (so parity
     exercises C, not a silent pure fallback on BOTH sides);
  2. ``eigvec_exact`` native == FORCED-PURE is BYTE-IDENTICAL — the exact ``Qalg``
     null-space basis — across diagonal / symmetric / cubic / degenerate / bignum
     matrices, real AND algebraic (irrational) eigenvalues;
  3. ``eigvec_exact_float`` native == FORCED-PURE (the terminal projection);
  4. the value oracles — ``diag(1,2,3)`` → the standard basis; ``[[2,1],[1,2]]`` →
     ``(1,1)`` / ``(1,−1)`` for λ=3 / 1; ``A·v == λ·v`` EXACTLY over ``Qalg``; an
     IRRATIONAL eigenvalue (ℚ(√5)) → the correct ℚ(λ) entries; a repeated
     eigenvalue → the full ``list[list[Qalg]]`` basis;
  5. ``eigvec_exact`` dispatches when native + falls back to the byte-identical
     pure oracle (native OFF);
  6. the Rosetta rows: ``eigvec_exact`` + ``eigvec_exact_float`` → ``c_dispatched``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.qalg import Qalg
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import (
    eigvec_exact,
    eigvec_exact_float,
)


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this eigvec_exact C ratchet must run on the numpy-ABSENT matrix")


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _companion(coeffs_low_to_high_monic):
    """Bottom-companion matrix whose char-poly is x^n + Σ c_i x^i."""
    c = coeffs_low_to_high_monic
    n = len(c) - 1
    m = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(1, n):
        m[i][i - 1] = 1
    for i in range(n):
        m[i][n - 1] = -c[i]
    return m


def _lams_for(mat):
    """Every EXACT eigenvalue of ``mat`` as a ``Qalg`` (over its irreducible
    minimal polynomial, embedded at its isolated root) — built DIRECTLY from the
    char-poly factorisation + root isolation (NOT via ``eig_exact``, whose FLOAT
    self-validation catastrophically cancels for a 10^15-conditioned eigenvalue —
    a limitation of the float projection, orthogonal to the exact eigvec path we
    test here). The lam objects themselves never depend on the native eigvec path."""
    cp = mc.char_poly(mat)
    cp_low = [int(c) for c in reversed(cp)]
    lams = []
    for (m_tuple, _alg_mult) in mc.factor_integer_poly(cp_low):
        m_int = tuple(int(c) for c in m_tuple)
        for root in mc._roots_of_irreducible(list(m_tuple), 64):
            lams.append(Qalg.alpha(m_int, root=root))
    return lams


def _matvec_qalg(A, v):
    """``A·v`` over ``Qalg`` (A entries are int scalars, v is ``list[Qalg]``)."""
    n = len(A)
    out = []
    for i in range(n):
        acc = None
        for j in range(n):
            term = v[j] * A[i][j]
            acc = term if acc is None else acc + term
        out.append(acc)
    return out


def _rows_ratio(mat):
    return [[(int(v), 1) for v in row] for row in mat]


# A spread: diagonal, symmetric, companion cubic, repeated-eigenvalue (Jordan +
# scalar), irrational-eigenvalue, and large-magnitude (bignum) entries.
_MATRICES = [
    [[5]],
    [[2, 1], [1, 2]],                            # λ ∈ {1, 3}, rational
    [[1, 1], [1, 2]],                            # λ = (3±√5)/2, ℚ(√5)
    [[1, 0, 0], [0, 2, 0], [0, 0, 3]],           # diagonal
    [[2, 0, 0], [0, 2, 0], [0, 0, 2]],           # 2·I₃ (null space dim 3)
    [[2, 1, 0], [0, 2, 1], [0, 0, 2]],           # Jordan block (geom mult 1)
    _companion([-1, -1, 0, 1]),                  # x³ − x − 1 (irreducible cubic)
    [[4, 1, 0], [1, 4, 1], [0, 1, 4]],           # symmetric tridiagonal (ℚ(√2))
    [[10 ** 15, 1], [1, 2]],                     # bignum entry
]


# ---- native symbol present -------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbol_present():
    assert _native.has_native_eigvec_exact()
    # diag(1,2,3), λ=2 -> the standard basis vector e₂ via the C kernel.
    lam = Qalg.alpha((-2, 1), root=2.0)
    v = _force(True, eigvec_exact, [[1, 0, 0], [0, 2, 0], [0, 0, 3]], lam)
    # e₂ up to scale: only component 1 nonzero.
    assert bool(v[1]) and not bool(v[0]) and not bool(v[2])


# ---- native == pure byte-identical (exact Qalg basis) ----------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_eigvec_exact_native_equals_pure(mat):
    for lam in _lams_for(mat):
        nat = _force(True, eigvec_exact, mat, lam)
        pure = _force(False, eigvec_exact, mat, lam)
        assert nat == pure                       # byte-identical Qalg structure
        # The C path actually RAN (returned non-None, not a silent OVERFLOW fallback).
        rr = _rows_ratio(mat)
        m_int = [int(c) for c in lam.m]
        coords = [(int(c.numerator), int(c.denominator)) for c in lam.coords]
        assert _native.eigvec_exact_c(rr, m_int, coords) is not None


# ---- eigvec_exact_float native == pure -------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_eigvec_exact_float_native_equals_pure(mat):
    for lam in _lams_for(mat):
        nat = _force(True, eigvec_exact_float, mat, lam)
        pure = _force(False, eigvec_exact_float, mat, lam)
        assert nat == pure                       # identical float/complex read-out


# ---- value oracles ---------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_oracle_diag_standard_basis():
    A = [[1, 0, 0], [0, 2, 0], [0, 0, 3]]
    for idx, ev in ((0, 1), (1, 2), (2, 3)):
        lam = Qalg.alpha((-ev, 1), root=float(ev))
        v = _force(True, eigvec_exact, A, lam)
        for k in range(3):
            assert bool(v[k]) == (k == idx)      # only the ev-th component nonzero


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_oracle_symmetric_2x2():
    A = [[2, 1], [1, 2]]
    # λ = 3 -> (1, 1); λ = 1 -> (1, −1), up to scale.
    v3 = _force(True, eigvec_exact, A, Qalg.alpha((-3, 1), root=3.0))
    v1 = _force(True, eigvec_exact, A, Qalg.alpha((-1, 1), root=1.0))
    # v3 components equal (proportional to (1,1)); v1 opposite (proportional to (1,−1)).
    assert v3[0] == v3[1]
    assert v1[0] == -v1[1]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_oracle_eigen_relation_exact(mat):
    """``A·v == λ·v`` EXACTLY over Qalg for every native eigenvector."""
    for lam in _lams_for(mat):
        res = _force(True, eigvec_exact, mat, lam)
        basis = res if (res and isinstance(res[0], list)) else [res]
        for v in basis:
            Av = _matvec_qalg(mat, v)
            assert all(Av[i] == lam * v[i] for i in range(len(v)))


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_oracle_irrational_eigenvalue_qalg_entries():
    """A=[[1,1],[1,2]], λ=(3±√5)/2 over ℚ(√5): the eigenvector carries genuine
    ℚ(λ) (nonzero α-coefficient) coordinates."""
    A = [[1, 1], [1, 2]]
    lam = _lams_for(A)[0]
    v = _force(True, eigvec_exact, A, lam)
    # at least one component is a NON-constant ℚ(λ) element (nonzero α coord).
    assert any(comp.coords[1] != 0 for comp in v)
    # and it satisfies the exact eigen-relation.
    Av = _matvec_qalg(A, v)
    assert all(Av[i] == lam * v[i] for i in range(2))


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_oracle_repeated_eigenvalue_full_basis():
    """2·I₃, λ=2: geometric multiplicity 3 -> list[list[Qalg]] of 3 basis vectors."""
    A = [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
    lam = Qalg.alpha((-2, 1), root=2.0)
    res = _force(True, eigvec_exact, A, lam)
    assert isinstance(res, list) and isinstance(res[0], list)
    assert len(res) == 3


# ---- dispatch + fallback ---------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_dispatch_and_fallback_agree():
    A = [[1, 1], [1, 2]]
    for lam in _lams_for(A):
        assert _force(True, eigvec_exact, A, lam) == _force(False, eigvec_exact, A, lam)


def test_pure_path_always_available():
    """The pure oracle (native OFF) computes the eigenvector with no C at all."""
    A = [[2, 1], [1, 2]]
    lam = Qalg.alpha((-3, 1), root=3.0)
    v = _force(False, eigvec_exact, A, lam)
    assert v[0] == v[1]                           # (1, 1) up to scale


# ---- Rosetta ledger --------------------------------------------------------

def test_rosetta_rows_are_c_dispatched():
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    for op in ("srmech.amsc.cascade.matrix_cascades.eigvec_exact",
               "srmech.amsc.cascade.matrix_cascades.eigvec_exact_float"):
        assert rows[op] == "c_dispatched", (op, rows.get(op))


# ---- reducible-m guard rides the pure error semantics ----------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_reducible_m_raises_via_pure_fallback():
    """A ``lam`` over a REDUCIBLE m (ℚ[x]/(m) not a field): the C returns
    BAD_INPUT -> the pure path raises the same ValueError."""
    A = [[2, 1], [1, 2]]
    # m = x² − 3x + 2 = (x−1)(x−2) is REDUCIBLE (not a minimal polynomial), so
    # ℚ[x]/(m) is NOT a field — a zero-divisor pivot has no inverse.
    bad = Qalg.alpha((2, -3, 1), root=2.0)       # α over the reducible m
    with pytest.raises(ValueError):
        _force(True, eigvec_exact, A, bad)       # C -> BAD_INPUT -> pure raises
    with pytest.raises(ValueError):
        _force(False, eigvec_exact, A, bad)


def test_unused_fraction_import():
    """Keep the Fraction import live (exact-rational substrate marker)."""
    assert Fraction(3, 4) + Fraction(1, 4) == 1
