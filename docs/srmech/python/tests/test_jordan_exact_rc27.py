"""0.9.0rc27 — exact generalized eigenvectors / Jordan canonical form (rc-G).

rc-G closes the LAST documented eigensolver gap: exact generalized eigenvectors
(Jordan chains) for DEFECTIVE (non-diagonalizable) matrices. Three new ops in
``srmech/amsc/cascade/matrix_cascades.py``:

1. **`jordan_chains_exact(a, lam)`** — the Jordan structure for an eigenvalue λ
   (a ``Qalg`` over its irreducible min-poly): the chains (each a list of ``Qalg``
   generalized eigenvectors, bottom→top with the bottom a geometric eigenvector,
   ``N·chain[i] == chain[i-1]``) + the block sizes, by exact ``Qalg``-Gaussian-
   elimination ranks of ``(A−λI)^k`` + top-down chain construction. The chain
   relations are verified EXACTLY over ``Qalg`` before returning.
2. **`eig_exact(a)`** now returns the FULL generalized basis for defective λ —
   each eigenvalue dict gains ``jordan_blocks`` (block sizes) + ``generalized_vectors``
   (the μ-many basis, organized by chain). Self-validation now asserts the full
   generalized basis has exactly ``n`` vectors AND ``A·P ≈ P·J``.
3. **`jordan_form_exact(a)`** — the capstone: ``{blocks, P, J}`` with ``A·P == P·J``
   self-validated EXACTLY over ``Qalg`` and to ~1e-9 in float.

numpy is GONE from srmech — this module is numpy-free and runs with numpy NOT
installed. Eigenvectors are defined only UP TO SCALE; chain relations are exact.
"""
from __future__ import annotations

import importlib.util

import pytest

from srmech.amsc.cascade.matrix_cascades import (
    eig_exact,
    eigvals_exact,
    jordan_chains_exact,
    jordan_form_exact,
)
from srmech.amsc.qalg import Qalg


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this rc27 Jordan ratchet must run on the numpy-ABSENT matrix")


# ── helpers (numpy-free) ──────────────────────────────────────────────────────────
def _matvec(A, v):
    n = len(A)
    return [sum(complex(A[i][j]) * complex(v[j]) for j in range(n)) for i in range(n)]


def _assert_AP_eq_PJ(A, P, J, tol=1e-9):
    """A·P ≈ P·J columnwise (P columns = generalized vectors, J the Jordan matrix)."""
    n = len(A)
    for c in range(n):
        ap = [sum(complex(A[i][j]) * complex(P[j][c]) for j in range(n))
              for i in range(n)]
        pj = [sum(complex(P[i][k]) * complex(J[k][c]) for k in range(n))
              for i in range(n)]
        for i in range(n):
            assert abs(ap[i] - pj[i]) < tol, (
                f"A·P != P·J at row {i}, col {c}: {ap[i]!r} vs {pj[i]!r}")


def _proj_chain(chain):
    """Project a list of Qalg vectors (a chain) to complex."""
    return [[c.to_complex() if (isinstance(c.root, complex) and c.root.imag != 0)
             else complex(c.to_float(), 0.0) for c in vec] for vec in chain]


def _is_zero_vec(v, tol=1e-12):
    return all(abs(complex(x)) < tol for x in v)


def _proportional(u, w, tol=1e-7):
    n = len(u)
    for i in range(n):
        for j in range(n):
            if abs(complex(u[i]) * complex(w[j]) - complex(u[j]) * complex(w[i])) > tol:
                return False
    return True


# ── defective [[2,1],[0,2]] — one size-2 block ────────────────────────────────────
def test_defective_2x2_jordan_block_chain():
    """[[2,1],[0,2]] → one Jordan block size 2 for λ=2; chain {v0, v1} with
    (A−2I)·v1 == v0 and (A−2I)·v0 == 0 (exact over Qalg)."""
    A = [[2, 1], [0, 2]]
    lam = Qalg.alpha((-2, 1), root=2.0)                  # m = x − 2, root 2
    chains, sizes = jordan_chains_exact(A, lam)
    assert sizes == [2]
    assert len(chains) == 1
    chain = chains[0]                                    # bottom→top: [v0, v1]
    assert len(chain) == 2
    # N = A − 2I.  N·chain[0] == 0 (bottom is the geometric eigenvector);
    # N·chain[1] == chain[0] (the chain relation) — verified EXACTLY over Qalg by
    # jordan_chains_exact, re-check the float read-out here.
    N = [[A[i][j] - (2 if i == j else 0) for j in range(2)] for i in range(2)]
    pc = _proj_chain(chain)
    assert _is_zero_vec(_matvec(N, pc[0]))               # (A−2I)·bottom == 0
    nv1 = _matvec(N, pc[1])                              # (A−2I)·top == bottom
    for a, b in zip(nv1, pc[0]):
        assert abs(a - b) < 1e-12
    # the bottom is ∝ [1, 0] (the geometric eigenvector of [[2,1],[0,2]]).
    assert _proportional(pc[0], [1.0, 0.0])


def test_defective_2x2_jordan_form():
    """jordan_form_exact([[2,1],[0,2]]) → J=[[2,1],[0,2]], A·P == P·J exact."""
    A = [[2, 1], [0, 2]]
    jf = jordan_form_exact(A)
    J = jf["J"]
    assert abs(J[0][0] - 2) < 1e-12 and abs(J[1][1] - 2) < 1e-12
    assert abs(J[0][1] - 1) < 1e-12                      # the super-diagonal 1
    assert abs(J[1][0]) < 1e-12
    assert jf["blocks"] == [(pytest.approx(2.0 + 0j), 2)] or \
        (len(jf["blocks"]) == 1 and abs(jf["blocks"][0][0] - 2) < 1e-12
         and jf["blocks"][0][1] == 2)
    _assert_AP_eq_PJ(A, jf["P"], jf["J"])


def test_defective_2x2_eig_exact_full_basis():
    """eig_exact([[2,1],[0,2]]) gains jordan_blocks=[2] + 2 generalized_vectors."""
    A = [[2, 1], [0, 2]]
    res = eig_exact(A)
    assert len(res) == 1
    e = res[0]
    assert e["value"] == pytest.approx(2.0)
    assert e["algebraic_multiplicity"] == 2
    assert e["geometric_multiplicity"] == 1
    assert e["defective"] is True
    assert e["jordan_blocks"] == [2]
    assert len(e["generalized_vectors"]) == 2            # the FULL basis now
    # the geometric eigenvector (still the primary "vector") is ∝ [1, 0].
    assert _proportional(e["vector"], [1.0, 0.0])


# ── [[2,1,0],[0,2,0],[0,0,2]] — {2,1} blocks (alg-mult 3) ─────────────────────────
def test_blocks_2_and_1():
    """λ=2 alg-mult 3 with blocks {2,1}: jordan_blocks order-insensitive [1,2];
    3 generalized vectors; A·P==P·J."""
    A = [[2, 1, 0], [0, 2, 0], [0, 0, 2]]
    res = eig_exact(A)
    assert len(res) == 1
    e = res[0]
    assert e["algebraic_multiplicity"] == 3
    assert e["geometric_multiplicity"] == 2             # 2 chains → geom 2
    assert e["defective"] is True
    assert sorted(e["jordan_blocks"]) == [1, 2]
    assert len(e["generalized_vectors"]) == 3
    jf = jordan_form_exact(A)
    assert sorted(s for _, s in jf["blocks"]) == [1, 2]
    _assert_AP_eq_PJ(A, jf["P"], jf["J"])
    # exactly ONE super-diagonal 1 in J (the single size-2 block).
    n = len(jf["J"])
    supers = sum(1 for i in range(n) for j in range(n)
                 if i + 1 == j and abs(jf["J"][i][j] - 1) < 1e-12)
    assert supers == 1


# ── single size-3 Jordan block [[5,1,0],[0,5,1],[0,0,5]] ──────────────────────────
def test_single_size_3_block():
    """[[5,1,0],[0,5,1],[0,0,5]] → blocks [3], chain length 3, A·P==P·J exact."""
    A = [[5, 1, 0], [0, 5, 1], [0, 0, 5]]
    lam = Qalg.alpha((-5, 1), root=5.0)
    chains, sizes = jordan_chains_exact(A, lam)
    assert sizes == [3]
    assert len(chains) == 1 and len(chains[0]) == 3
    res = eig_exact(A)
    assert len(res) == 1
    e = res[0]
    assert e["jordan_blocks"] == [3]
    assert e["geometric_multiplicity"] == 1
    assert e["algebraic_multiplicity"] == 3
    assert e["defective"] is True
    assert len(e["generalized_vectors"]) == 3
    jf = jordan_form_exact(A)
    assert sorted(s for _, s in jf["blocks"]) == [3]
    # TWO super-diagonal 1s in a size-3 block.
    n = len(jf["J"])
    supers = sum(1 for i in range(n) for j in range(n)
                 if i + 1 == j and abs(jf["J"][i][j] - 1) < 1e-12)
    assert supers == 2
    _assert_AP_eq_PJ(A, jf["P"], jf["J"])


# ── DIAGONALIZABLE matrices: all blocks size 1, behaviour preserved (regression) ──
def test_diagonalizable_distinct_eigenvalues():
    """[[2,0],[0,3]] → all jordan_blocks [1], generalized == geometric, not defective."""
    A = [[2, 0], [0, 3]]
    res = eig_exact(A)
    assert len(res) == 2
    for e in res:
        assert e["jordan_blocks"] == [1]
        assert e["defective"] is False
        assert e["geometric_multiplicity"] == 1
        assert e["algebraic_multiplicity"] == 1
        # generalized_vectors == geometric eigenvectors (chains all length 1).
        assert len(e["generalized_vectors"]) == 1
        assert _proportional(e["generalized_vectors"][0], e["vector"])
    jf = jordan_form_exact(A)
    # J is diagonal (no super-diagonal 1s) for a diagonalizable matrix.
    n = len(jf["J"])
    assert all(abs(jf["J"][i][j]) < 1e-12
               for i in range(n) for j in range(n) if i != j)
    _assert_AP_eq_PJ(A, jf["P"], jf["J"])


def test_diagonalizable_repeated_2I():
    """2·I → λ=2 alg-mult 2, jordan_blocks [1,1], geom 2, NOT defective; 2 gen vecs."""
    A = [[2, 0], [0, 2]]
    res = eig_exact(A)
    assert len(res) == 1
    e = res[0]
    assert sorted(e["jordan_blocks"]) == [1, 1]
    assert e["defective"] is False
    assert e["geometric_multiplicity"] == 2
    assert e["algebraic_multiplicity"] == 2
    assert len(e["generalized_vectors"]) == 2
    jf = jordan_form_exact(A)
    n = len(jf["J"])
    assert all(abs(jf["J"][i][j]) < 1e-12
               for i in range(n) for j in range(n) if i != j)
    _assert_AP_eq_PJ(A, jf["P"], jf["J"])


def test_diagonalizable_rc25_contract_unchanged():
    """The rc25 contract keys are byte-for-byte unchanged for a diagonalizable
    matrix (no key removed; the NEW keys are additive). [[2,1],[1,2]] → {1,3}."""
    A = [[2, 1], [1, 2]]
    res = eig_exact(A)
    assert len(res) == 2
    for e in res:
        # rc25 keys still present + valued exactly as before.
        for k in ("value", "vector", "algebraic_multiplicity",
                  "geometric_multiplicity", "min_poly", "defective"):
            assert k in e
        assert e["algebraic_multiplicity"] == 1
        assert e["geometric_multiplicity"] == 1
        assert e["defective"] is False
        # rc27 additive keys.
        assert e["jordan_blocks"] == [1]
        assert _proportional(e["generalized_vectors"][0], e["vector"])
    by_val = {round(e["value"].real): e for e in res}
    assert set(by_val) == {1, 3}
    assert _proportional(by_val[1]["vector"], [1.0, -1.0])
    assert _proportional(by_val[3]["vector"], [1.0, 1.0])


# ── COMPLEX-defective: companion of (x²+1)² → ±i each a size-2 defective block ────
def test_complex_defective_block():
    """Companion of (x²+1)² = x⁴+2x²+1 → eigenvalues ±i each alg-mult 2, geom 1,
    a size-2 DEFECTIVE Jordan block; the full n-count generalized basis; A·P==P·J."""
    # companion of low→high coeffs [1, 0, 2, 0, 1] (x⁴ + 2x² + 1):
    C = [[0, 0, 0, -1], [1, 0, 0, 0], [0, 1, 0, -2], [0, 0, 1, 0]]
    res = eig_exact(C, bits=80)
    assert len(res) == 2                                 # ±i, distinct
    total_gen = 0
    for e in res:
        assert e["min_poly"] == (1, 0, 1)                # x²+1
        assert e["algebraic_multiplicity"] == 2
        assert e["geometric_multiplicity"] == 1
        assert e["defective"] is True
        assert e["jordan_blocks"] == [2]
        # genuinely complex eigenvalue.
        assert abs(e["value"].imag) > 0.5
        total_gen += len(e["generalized_vectors"])
    assert total_gen == 4                                # FULL n-count basis
    jf = jordan_form_exact(C, bits=80)
    assert sorted(s for _, s in jf["blocks"]) == [2, 2]
    _assert_AP_eq_PJ(C, jf["P"], jf["J"])
    # two super-diagonal 1s (one per size-2 block).
    n = len(jf["J"])
    supers = sum(1 for i in range(n) for j in range(n)
                 if i + 1 == j and abs(jf["J"][i][j] - 1) < 1e-12)
    assert supers == 2


# ── eig_exact full-n generalized basis on every defective case ────────────────────
def test_full_generalized_basis_count_equals_n():
    """eig_exact's self-validation (asserted internally) now guarantees the union of
    generalized_vectors over all eigenvalues is exactly n — defective or not."""
    cases = [
        [[2, 1], [0, 2]],                                # defective size-2
        [[2, 1, 0], [0, 2, 0], [0, 0, 2]],               # {2,1}
        [[5, 1, 0], [0, 5, 1], [0, 0, 5]],               # size-3
        [[2, 0], [0, 3]],                                # diagonalizable
        [[2, 0], [0, 2]],                                # 2I
        [[0, 0, 0, -1], [1, 0, 0, 0], [0, 1, 0, -2], [0, 0, 1, 0]],  # complex-def
    ]
    for A in cases:
        n = len(A)
        res = eig_exact(A, bits=80)
        total = sum(len(e["generalized_vectors"]) for e in res)
        assert total == n, (A, total, n)


# ── cross-check eigenvalues vs eigvals_exact(include_complex=True) ────────────────
def test_jordan_eigenvalues_cross_check_eigvals_exact():
    """The Jordan-form block eigenvalues (with size as multiplicity) cross-check
    eigvals_exact(include_complex=True).

    rc28: the REPEATED *complex* eigenvalue case (the companion of (x²+1)² → ±i each
    multiplicity 2) is now INCLUDED — the rc24 complex isolator used to STALL on
    repeated complex roots (it isolated on the full char-poly, where box-subdivision
    can't separate a coincident pair), and rc28 fixed it by isolating per square-free
    factor. The companion of (x²+1)² is added below; it must now terminate and agree
    with the Jordan-form eigenvalues."""
    # companion of (x²+1)² = x⁴ + 2x² + 1 (low→high [1,0,2,0,1]) → ±i each mult 2.
    comp_x2p1_sq = [[0, 0, 0, -1], [1, 0, 0, -0], [0, 1, 0, -2], [0, 0, 1, -0]]
    cases = [
        [[2, 1], [0, 2]],                                # real-repeat λ=2 (fine)
        [[2, 1, 0], [0, 2, 0], [0, 0, 2]],               # real-repeat λ=2 (fine)
        [[5, 1, 0], [0, 5, 1], [0, 0, 5]],               # real-repeat λ=5 (fine)
        [[2, 0], [0, 3]],                                # distinct real
        [[0, -1], [1, 0]],                               # distinct complex ±i
        comp_x2p1_sq,                                    # rc28: repeated complex ±i (mult 2)
    ]
    for A in cases:
        n = len(A)
        jf = jordan_form_exact(A, bits=80)
        got = []
        for (val, s) in jf["blocks"]:
            got.extend([complex(val)] * s)
        ref = [complex(r) for r in eigvals_exact(A, include_complex=True, bits=80)]
        assert len(got) == len(ref) == n
        rem = list(ref)
        for g in got:
            k = min(range(len(rem)), key=lambda i: abs(g - rem[i]))
            assert abs(g - rem[k]) < 1e-7, (A, g, rem)
            rem.pop(k)


# ── project=False: exact Qalg objects throughout ─────────────────────────────────
def test_jordan_form_project_false_qalg():
    """jordan_form_exact(project=False) hands back exact Qalg P, J, block eigenvalues;
    A·P == P·J is self-validated EXACTLY over Qalg (no float in the check)."""
    A = [[2, 1], [0, 2]]
    jf = jordan_form_exact(A, project=False)
    assert all(isinstance(jf["J"][i][j], Qalg)
               for i in range(2) for j in range(2))
    assert all(isinstance(jf["P"][i][j], Qalg)
               for i in range(2) for j in range(2))
    assert all(isinstance(v, Qalg) for v, _ in jf["blocks"])


def test_eig_exact_project_false_has_qalg_generalized_vectors():
    """eig_exact(project=False) carries generalized_vectors as list[list[Qalg]]."""
    res = eig_exact([[2, 1], [0, 2]], project=False)
    assert len(res) == 1
    e = res[0]
    assert "generalized_vectors" in e and "jordan_blocks" in e
    assert all(isinstance(c, Qalg) for vec in e["generalized_vectors"] for c in vec)


def test_jordan_determinism():
    A = [[5, 1, 0], [0, 5, 1], [0, 0, 5]]
    a = jordan_form_exact(A)
    b = jordan_form_exact(A)
    assert a["blocks"] == b["blocks"]
    assert a["J"] == b["J"]
    assert a["P"] == b["P"]


def test_jordan_empty_matrix():
    jf = jordan_form_exact([])
    assert jf == {"blocks": [], "P": [], "J": []}
