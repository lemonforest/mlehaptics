"""rc48 — ``srmech_qmat_rref_crt``: the single-symbol C orchestration of the
bounded-memory exact-ℚ CRT solve (the CLOSER of the CRT-QMat re-fibration arc).

rc44–rc47 shipped the fiber (``gf_rref`` / ``crt_combine`` / ``rational_reconstruct``
/ ``next_prime``, all C-backed) and routed the consumers; rc48 composes those four
into ONE malloc-free, caller-arena, JPL-clean C symbol — ``srmech_qmat_rref_crt`` —
so a bare-C host (no Python) can call the whole CRT solve with one call. This
discharges the owed everything-mirrors backlog for ``QMat.rref_crt``.

The gate is **native == pure == dense, byte-for-byte**: the new C symbol's exact-ℚ
RREF must equal the pure-Python ``rref_crt`` (the rc46 algorithm) AND the dense
``QMat.rref`` exactly, at every shape — random / rank-deficient / non-square, the
``Q(10**40+1, 3**30)`` keystone magnitudes (num/den > 2**64), the first-prime-
unlucky consensus-restart case, and the real Franel 484x154 system (heavy, gated).

THE ARENA BOUND (the crux). The C arena (from ``srmech_qmat_rref_crt_ws_bound``) is
sized from the ANSWER-Hadamard good-prime budget, NOT the dense elimination swell —
so it is answer-sized (MB-scale on Franel) instead of the ~2.3 GB the dense
``srmech_qmat_ws_bound`` reserves. This test asserts that ratio directly.

numpy-FREE and ``math``-FREE: only ``fractions.Fraction`` (an independent oracle),
the srmech exact carriers, and plain ``int``.
"""
from __future__ import annotations

import os
import random
import sys

import pytest

from srmech.amsc import _native
from srmech.amsc import qmat as _qmat
from srmech.amsc.q import Q
from srmech.amsc.qmat import QMat

_HAVE_NATIVE = _native.HAS_NATIVE and _native.has_native_qmat_rref_crt()

requires_native = pytest.mark.skipif(
    not _HAVE_NATIVE,
    reason="srmech_qmat_rref_crt native symbol absent (pure path is the complete "
           "fallback; the byte-identity gate needs the C peer present)",
)


# ── helpers (numpy-free, math-free) ───────────────────────────────────────────

def _flat(m: QMat):
    return [(q._n, q._d) for r in m._rows for q in r]


def _pairs(m: QMat):
    return [[(q._n, q._d) for q in r] for r in m._rows]


def _native_rref_crt(m: QMat):
    """The exact-ℚ RREF via the single C symbol ``srmech_qmat_rref_crt`` ONLY."""
    res = _native.qmat_rref_crt_c(_flat(m), m.n_rows, m.n_cols)
    assert res is not None, "native path returned None (absent / OVERFLOW)"
    pairs, _rank, _piv = res
    return _qmat._qmat_from_flat(pairs, m.n_rows, m.n_cols)


def _pure_rref_crt(m: QMat):
    """The pure-Python CRT body ONLY (bypassing the native dispatch)."""
    out = _qmat._rref_crt_rows(m._rows, m.n_rows, m.n_cols, m.n_cols)
    assert out is not None
    rows, _piv, _prc = out
    return QMat.__new__(QMat)._init_from(rows)


def _assert_triple(m: QMat, label: str):
    """native == pure == dense, byte-for-byte (the rc48 gate)."""
    dense = _pairs(m.rref())
    pure = _pairs(_pure_rref_crt(m))
    nat = _pairs(_native_rref_crt(m))
    assert dense == pure, f"pure != dense [{label}] {m.shape}"
    assert dense == nat, f"native != dense [{label}] {m.shape}"


# ── the test itself is numpy-free ─────────────────────────────────────────────

def test_no_numpy_imported():
    """This module (a test for a numpy-free C op) must itself be numpy-free."""
    assert "numpy" not in sys.modules


def test_native_symbol_present_or_clean_skip():
    """The rc48 symbol is bound when the lib is present; a pre-rc48 / no-C lib
    cleanly reports absent (the pure path is then the complete alternative)."""
    if _HAVE_NATIVE:
        assert hasattr(_native.LIB, "srmech_qmat_rref_crt")
        assert hasattr(_native.LIB, "srmech_qmat_rref_crt_ws_bound")
        assert hasattr(_native.LIB, "srmech_qmat_rref_crt_entry_cap")
    else:
        # absent → QMat.rref_crt still works (pure path); exercise it.
        m = QMat.from_rows([[2, 1], [1, 3]])
        assert m.rref_crt() == m.rref()


# ── native == pure == dense across shapes ─────────────────────────────────────

@requires_native
def test_random_shapes_byte_identical():
    """40+ random exact-ℚ matrices (square / non-square / rank-deficient): native
    == pure == dense byte-for-byte."""
    rng = random.Random(48_2026)
    n = 0
    for _ in range(48):
        nr = rng.randint(1, 6)
        nc = rng.randint(1, 6)
        rows = [[Q(rng.randint(-9, 9), rng.randint(1, 7)) for _ in range(nc)]
                for _ in range(nr)]
        m = QMat.from_rows(rows)
        _assert_triple(m, f"rand{m.shape}")
        n += 1
    assert n >= 40


@requires_native
def test_rank_deficient_byte_identical():
    """A duplicated row + a zero column → the modular-rank consensus must pick the
    same pivot support as the dense pivoting (native == pure == dense)."""
    base = QMat.from_rows([[1, 2, 3, 4],
                           [2, 4, 6, 8],          # 2 x row0 (dependent)
                           [1, 1, 1, 1],
                           [0, 1, 2, 3]])
    _assert_triple(base, "rank-deficient 4x4")
    # an explicit zero column + a dependent row, non-square
    z = QMat.from_rows([[1, 0, 3, 5, 2],
                        [2, 0, 6, 1, 4],
                        [1, 0, 3, 5, 2]])        # = row0
    _assert_triple(z, "rank-deficient 3x5 zero-col")


@requires_native
def test_non_square_free_columns_byte_identical():
    """Free (non-pivot) columns carry FRACTIONAL rationals through the RREF — the
    case that catches a residue / sign-lift bug (native == pure == dense)."""
    for rows in [
        [[Q(1, 2), Q(1, 3), Q(1, 5), Q(1, 7), Q(1, 11)],
         [Q(1, 13), Q(1, 17), Q(1, 19), Q(1, 23), Q(1, 29)]],
        [[Q(-3, 4), Q(5, 6), Q(-7, 8), Q(9, 10)],
         [Q(2, 3), Q(-1, 5), Q(4, 7), Q(-6, 11)],
         [Q(1, 2), Q(2, 3), Q(3, 5), Q(5, 7)]],
    ]:
        _assert_triple(QMat.from_rows(rows), "free-col fractional")


@requires_native
def test_keystone_big_magnitudes_byte_identical():
    """The ``Q(10**40+1, 3**30)`` keystone (num/den far past 2**64). The square
    case collapses to the identity; the AUGMENTED [A|B] case carries the bigint
    rationals into the free columns so the ANSWER entries themselves exceed 2**64
    — the genuine bigint-reconstruction keystone (native == pure == dense)."""
    big = Q(10 ** 40 + 1, 3 ** 30)
    sq = QMat.from_rows([[big, Q(1, 2), 3],
                         [Q(2, 7), big, Q(5, 11)],
                         [1, Q(-3, 4), big]])
    _assert_triple(sq, "keystone square")
    assert _native_rref_crt(sq) == QMat.identity(3)

    aug = QMat.from_rows([[2, 1, 3, big, 1],
                          [1, 4, 1, 7, big],
                          [3, 2, 5, 1, Q(2, 3 ** 30)]])
    _assert_triple(aug, "keystone augmented")
    out = _native_rref_crt(aug)
    max_bits = max(max(q._n.bit_length(), q._d.bit_length())
                   for r in out._rows for q in r)
    assert max_bits > 64, "augmented keystone answer should carry a >2**64 entry"


@requires_native
def test_first_prime_unlucky_consensus_restart_byte_identical():
    """When the FIRST descending prime is itself unlucky (the matrix drops rank mod
    that prime), the consensus must RESTART on the later higher-rank prime — yet the
    exact RREF is recovered byte-for-byte (native == pure == dense). We pin the
    unlucky prime to the head of the walk with ``det == 2147483647`` (the first
    descending GF prime)."""
    p0 = 2147483647
    m = QMat.from_rows([[p0, 1], [0, 1]])        # det == p0 ⇒ unlucky at p0
    _assert_triple(m, "first-prime-unlucky restart")
    assert _native_rref_crt(m) == QMat.identity(2)


@requires_native
def test_degenerate_shapes_byte_identical():
    """A zero matrix + a single cell match the dense path (native == pure ==
    dense)."""
    _assert_triple(QMat.zeros(3, 3), "zeros(3,3)")
    _assert_triple(QMat.from_rows([[Q(5, 7)]]), "single cell")


# ── the arena is ANSWER-sized, not the dense Hadamard envelope ────────────────

@requires_native
def test_arena_is_answer_sized_not_dense_envelope():
    """The C CRT arena (``srmech_qmat_rref_crt_ws_bound``) is answer-sized — well
    below the dense ``srmech_qmat_ws_bound`` Hadamard envelope. On a Franel-scale
    484x154 system the CRT arena is sub-GB while the dense one is ~2.3 GB."""
    import ctypes
    cl, nr, nc = 2, 484, 154
    crt_ws = int(_native.LIB.srmech_qmat_rref_crt_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(nr), ctypes.c_size_t(nc)))
    dense_ws = int(_native.LIB.srmech_qmat_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(nr), ctypes.c_size_t(nc)))
    # answer-sized: sub-GB, and a clear multiple smaller than the dense envelope.
    assert crt_ws < (1 << 30), f"CRT arena {crt_ws} should be < 1 GiB"
    assert crt_ws * 4 < dense_ws, (
        f"CRT arena {crt_ws} should be well below the dense envelope {dense_ws}")


# ── the headline: the real Franel 484x154 system (heavy, gated) ───────────────

def _franel_order2_rows():
    """Assemble the order-2 Franel (``Σ_k C(n,k)^3``) creative-telescoping
    homogeneous system — the real 484x154 system. Reuses the rc46 test's builder
    path via the ``zeilberger`` internals."""
    from srmech.amsc.poly import Poly
    from srmech.amsc.zeilberger import (BiPoly, _ansatz_n_degree,
                                        _ansatz_x_degree, _assemble_rows,
                                        _bi_exact_div, _rho)

    def P(*c):
        return Poly.from_coeffs(list(c))
    np1 = P(1, 1)
    n = P(0, 1)
    rn_num = BiPoly([np1 * np1 * np1])
    rn_den = BiPoly([np1 * np1 * np1, (np1 * np1) * P(-3), np1 * P(3), P(-1)])
    rk_num = BiPoly([n * n * n, (n * n) * P(-3), n * P(3), P(-1)])
    rk_den = BiPoly([P(1), P(3), P(3), P(1)])
    order = 2
    rhos = [_rho(rn_num, rn_den, j) for j in range(order + 1)]
    den_p = BiPoly.one()
    for _, dj in rhos:
        den_p = den_p * dj
    rho_common = [nj * _bi_exact_div(den_p, dj) for nj, dj in rhos]
    n_deg = _ansatz_n_degree(rho_common, den_p, rk_num, rk_den, order)
    xk_deg, xn_deg = _ansatz_x_degree(rho_common, den_p, rk_num, rk_den, order,
                                      n_deg)
    a_block = (order + 1) * (n_deg + 1)
    n_unknowns = a_block + (xk_deg + 1) * (xn_deg + 1)
    return _assemble_rows(rho_common, den_p, rk_num, rk_den, order, n_deg,
                          xk_deg, xn_deg, n_unknowns, a_block)


@requires_native
def test_franel_484x154_native_byte_identical():
    """THE HEADLINE: ``srmech_qmat_rref_crt`` (native) == pure CRT == dense
    ``rref``, byte-for-byte, on the real order-2 Franel 484x154 exact-ℚ system,
    at the bounded answer-sized arena.

    HEAVY (the dense pure-ℚ RREF on 484x154 is minutes-scale). Gated behind
    ``SRMECH_RUN_HEAVY=1``."""
    if os.environ.get("SRMECH_RUN_HEAVY") != "1":
        pytest.skip("heavy Franel 484x154 — set SRMECH_RUN_HEAVY=1 to run")
    rows = _franel_order2_rows()
    a = QMat.from_rows([list(r) for r in rows])
    assert a.shape == (484, 154)
    native = _native_rref_crt(a)
    pure = _pure_rref_crt(a)
    dense = a.rref()
    assert _pairs(native) == _pairs(pure), "native != pure on Franel"
    assert _pairs(native) == _pairs(dense), "native != dense on Franel"
    assert native.rank() == 151
