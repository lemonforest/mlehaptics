"""Qalg TAIL Batch 7b (0.9.0rc164): the exact JORDAN CHAINS (generalized
eigenvectors) of an integer/rational matrix for a DEFECTIVE eigenvalue earn a
``srmech_bigint``-backed C path — composing the rc163 Qalg number-field carrier.

The NEW C kernel ``srmech_jordan_chains`` builds ``N = A − λI`` with ``Qalg``
entries over ℚ(λ), computes the ranks of the matrix POWERS ``Nᵏ`` (a new Qalg
matrix MATMUL + RANK over the rc163 field), reads the Jordan structure off the
rank drops (``# blocks of size exactly k = r_{k-1} − 2·r_k + r_{k+1}``), and
builds the chains TOP-DOWN by nested NULLSPACE + column-rank independence —
picking a top ``v`` in ``null(N^s)`` independent of ``null(N^{s-1})`` ∪ the
chains already chosen and forming ``v, N·v, …, N^{s-1}·v``. All arithmetic is
exact ``Qalg``; byte/structurally-identical to the pure
``_jordan_chains_build_pure`` (the RREF is canonical + the top-down selection
deterministic).

This test pins:
  1. the native ``srmech_jordan_chains`` symbol is actually loaded (so parity
     exercises C, not a silent pure fallback on BOTH sides);
  2. ``jordan_chains_exact`` native == FORCED-PURE is BYTE/STRUCTURALLY-IDENTICAL
     — the same chains (same ``Qalg`` vectors, chain lengths, ordering) — across
     diagonalizable / Jordan-block / two-block / mixed-defective / irrational /
     bignum matrices;
  3. the value oracles — a diagonalizable matrix → all chains length 1 (the
     eigenvectors); a Jordan block ``[[λ,1],[0,λ]]`` → one chain length 2; the
     generalized-eigenvector defining relations ``N·vₖ == v_{k-1}`` and
     ``N·bottom == 0`` hold EXACTLY over ``Qalg``;
  4. ``jordan_chains_exact`` dispatches when native + falls back to the
     byte-identical pure oracle (native OFF);
  5. the Rosetta row: ``jordan_chains_exact`` → ``c_dispatched``, and the
     down-only ``CEIL_BIGNUM_REFERENCE`` ratchet is 3.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.qalg import Qalg
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import jordan_chains_exact


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this jordan_chains_exact C ratchet must run on the numpy-ABSENT matrix")


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _lams_for(mat):
    """Every EXACT eigenvalue of ``mat`` as a ``Qalg`` (over its irreducible
    minimal polynomial, embedded at its isolated root) — built DIRECTLY from the
    char-poly factorisation + root isolation. The lam objects never depend on the
    native jordan path."""
    cp = mc.char_poly(mat)
    cp_low = [int(c) for c in reversed(cp)]
    lams = []
    for (m_tuple, _alg_mult) in mc.factor_integer_poly(cp_low):
        m_int = tuple(int(c) for c in m_tuple)
        for root in mc._roots_of_irreducible(list(m_tuple), 64):
            lams.append(Qalg.alpha(m_int, root=root))
    return lams


def _rows_ratio(mat):
    return [[(int(v), 1) for v in row] for row in mat]


# A spread: diagonalizable, single Jordan blocks (2, 3), two equal blocks,
# a {2,1} split, a mixed two-eigenvalue defective, irrational (ℚ(√5)), a
# nilpotent block, and large-magnitude (bignum) Jordan entries.
_MATRICES = [
    [[1, 0, 0], [0, 2, 0], [0, 0, 3]],           # diagonalizable
    [[2, 0, 0], [0, 2, 0], [0, 0, 2]],           # 2·I₃ (three length-1 chains)
    [[2, 1], [0, 2]],                            # one Jordan block, length 2
    [[2, 1, 0], [0, 2, 1], [0, 0, 2]],           # one Jordan block, length 3
    [[2, 1, 0, 0], [0, 2, 0, 0],
     [0, 0, 2, 1], [0, 0, 0, 2]],                # two length-2 blocks
    [[2, 1, 0], [0, 2, 0], [0, 0, 2]],           # {2,1} split
    [[3, 1, 0, 0], [0, 3, 0, 0],
     [0, 0, 5, 0], [0, 0, 0, 5]],                # mixed: λ=3 defective, λ=5 diag
    [[2, 1], [1, 2]],                            # rational λ ∈ {1, 3}
    [[1, 1], [1, 2]],                            # λ = (3±√5)/2, ℚ(√5)
    [[0, 1, 0], [0, 0, 1], [0, 0, 0]],           # nilpotent (one length-3 chain)
    [[10 ** 12, 1], [0, 10 ** 12]],              # bignum Jordan block
]


# ---- native symbol present -------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbol_present():
    assert _native.has_native_jordan_chains()
    # Jordan block [[2,1],[0,2]], λ=2 -> one chain of length 2 via the C kernel.
    lam = Qalg.alpha((-2, 1), root=2.0)
    _chains, block_sizes = _force(True, jordan_chains_exact, [[2, 1], [0, 2]], lam)
    assert block_sizes == [2]


# ---- native == pure byte/structurally-identical ----------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_jordan_chains_native_equals_pure(mat):
    for lam in _lams_for(mat):
        nat_ch, nat_bs = _force(True, jordan_chains_exact, mat, lam)
        pure_ch, pure_bs = _force(False, jordan_chains_exact, mat, lam)
        assert nat_bs == pure_bs               # same chain lengths / ordering
        assert nat_ch == pure_ch               # byte-identical Qalg chains
        # The C path actually RAN (returned non-None, not a silent OVERFLOW fallback).
        rr = _rows_ratio(mat)
        m_int = [int(c) for c in lam.m]
        coords = [(int(c.numerator), int(c.denominator)) for c in lam.coords]
        assert _native.jordan_chains_c(rr, m_int, coords) is not None


# ---- value oracles ---------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_diagonalizable_all_length_one():
    mat = [[1, 0, 0], [0, 2, 0], [0, 0, 3]]
    for lam in _lams_for(mat):
        _ch, bs = _force(True, jordan_chains_exact, mat, lam)
        assert all(b == 1 for b in bs), bs


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_jordan_block_length_two():
    lam = Qalg.alpha((-2, 1), root=2.0)
    chains, bs = _force(True, jordan_chains_exact, [[2, 1], [0, 2]], lam)
    assert bs == [2] and len(chains) == 1 and len(chains[0]) == 2


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mat", _MATRICES)
def test_generalized_eigenvector_relations(mat):
    """N·chain[0] == 0 (geometric eigenvector) and N·chain[i] == chain[i-1],
    exactly over Qalg — the defining relations of a Jordan chain."""
    for lam in _lams_for(mat):
        chains, _bs = _force(True, jordan_chains_exact, mat, lam)
        N, _A_q, n, _one, zero = mc._qalg_matrix_of(mat, lam)
        for chain in chains:
            Nb = mc._qalg_matvec(N, chain[0], n, zero)
            assert all(not comp for comp in Nb)          # N·bottom == 0
            for i in range(1, len(chain)):
                Nv = mc._qalg_matvec(N, chain[i], n, zero)
                assert all(Nv[j] == chain[i - 1][j] for j in range(n))


# ---- dispatch + fallback ---------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_dispatch_and_fallback_agree():
    mat = [[2, 1, 0], [0, 2, 1], [0, 0, 2]]
    lam = Qalg.alpha((-2, 1), root=2.0)
    nat = _force(True, jordan_chains_exact, mat, lam)
    pure = _force(False, jordan_chains_exact, mat, lam)
    assert nat == pure


# ---- Rosetta ledger --------------------------------------------------------

def _classification():
    fx = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in fx.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r["bucket"] for r in rows}


def test_rosetta_row_is_c_dispatched():
    cls = _classification()
    assert cls["srmech.amsc.cascade.matrix_cascades.jordan_chains_exact"] == \
        "c_dispatched"


def test_bignum_reference_count_is_three():
    """rc164 drove the ledger's bignum_reference bucket 4 -> 3; rc165 then drove
    it 3 -> 2 (factor_integer_poly earned a Zassenhaus C path); rc166 (the B9
    CAPSTONE) drove it 2 -> 0 (eig_exact + jordan_form_exact are now
    composition_of_c), so the bucket is EMPTY — the exact-algebra tail is
    python-free."""
    cls = _classification()
    remaining = sorted(
        da.rsplit(".", 1)[-1] for da, b in cls.items() if b == "bignum_reference")
    assert remaining == [], remaining
