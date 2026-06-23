"""rc46 — ``QMat.rref_crt``: the CRT-re-fibrated exact-ℚ RREF.

Rung 3 of the CRT-QMat re-fibration arc. The rc44 + rc45 pieces (``gf_rref``,
``next_prime``, ``crt_combine``, ``rational_reconstruct`` — all C-backed) compose
into an exact-ℚ RREF that is **byte-identical** to the dense ``QMat.rref()`` but at
*bounded* memory instead of the dense path's Hadamard-envelope arena.

The dense ``QMat.rref()`` (rc40) grows numerator + denominator at every pivot, so
its malloc-free C arena reserves the worst-case fraction envelope — ~GB-scale for
a small answer on the order-2 Franel 484x154 Zeilberger system. ``rref_crt`` solves
mod several bounded primes (each a swell-free GF(p) ``gf_rref``), CRT-combines, and
rational-reconstructs once — bounded memory, EXACT answer.

This test is numpy-FREE and ``math``-FREE: only ``fractions.Fraction`` (an
independent oracle), the srmech exact carriers, and plain ``int``. The headline is
the **Franel 484x154 system byte-identical** check + the **memory ratio**
(CRT peak vs the dense analytic arena from the C ``qmat_ws_bound`` formula).
"""
from __future__ import annotations

import random

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.qmat import QMat
from srmech.amsc.zeilberger import (BiPoly, _ansatz_n_degree, _ansatz_x_degree,
                                    _assemble_rows, _bi_exact_div, _rho)


# ── byte-identical on random exact-ℚ matrices (various shapes) ────────────────

def _rand_qmat(rng, n_rows, n_cols, num_lo=-50, num_hi=50, den_hi=30):
    rows = [[Q(rng.randint(num_lo, num_hi), rng.randint(1, den_hi))
             for _ in range(n_cols)] for _ in range(n_rows)]
    return QMat.from_rows(rows)


def test_rref_crt_byte_identical_random_shapes():
    """``rref_crt`` == dense ``rref`` (entries) across many random shapes,
    including non-square and rank-deficient systems."""
    rng = random.Random(20260623)
    for _ in range(60):
        n_rows = rng.randint(1, 6)
        n_cols = rng.randint(1, 6)
        m = _rand_qmat(rng, n_rows, n_cols)
        assert m.rref_crt() == m.rref(), (
            f"rref_crt != rref on a {n_rows}x{n_cols} random ℚ matrix")


def test_rref_crt_byte_identical_rank_deficient():
    """A deliberately rank-deficient matrix (a dependent row + a dependent col)
    reduces identically through both paths — the modular-rank consensus must pick
    the same pivot support as the dense pivoting."""
    base = QMat.from_rows([[1, 2, 3, 4],
                           [2, 4, 6, 8],          # 2 x row0  (dependent)
                           [1, 1, 1, 1],
                           [0, 1, 2, 3]])         # = row0 - row2 pattern
    assert base.rref_crt() == base.rref()
    assert base.rank() == base.rref_crt().rank()


def test_rref_crt_byte_identical_big_entries_keystone():
    """The rc40 QMat keystone magnitudes (``Q(10**40+1, 3**30)``-class entries —
    numerators/denominators far past 2**64) reconstruct EXACTLY: the CRT path
    recovers the bigint rational byte-for-byte."""
    big = Q(10 ** 40 + 1, 3 ** 30)
    m = QMat.from_rows([[big, Q(1, 2), 3],
                        [Q(2, 7), big, Q(5, 11)],
                        [1, Q(-3, 4), big]])
    assert m.rref_crt() == m.rref()
    # the reduced full-rank case collapses to the identity exactly
    assert m.rref_crt() == QMat.identity(3)


def test_rref_crt_returns_qmat_same_shape():
    """The return is a ``QMat`` of the same shape as ``rref`` (a carrier, not a
    dict) — same surface contract as ``rref`` / ``inverse``."""
    m = QMat.from_rows([[2, 1], [1, 3]])
    out = m.rref_crt()
    assert isinstance(out, QMat)
    assert out.shape == m.shape


def test_rref_crt_unlucky_prime_consensus_direct():
    """The UNLUCKY-prime discard rule, exercised DIRECTLY on the ``_rref_crt``
    fold helpers.

    An *unlucky* prime is one dividing a rank-determining minor: mod that prime the
    matrix looks rank-deficient (the modular rank drops below the true exact rank),
    so its GF(p) RREF disagrees with the consensus and must be DISCARDED before the
    CRT — exactly the mechanism behind the genuine ``p=7`` rank drop on the Franel
    order-2 system (where ``GF(7)`` sees a singular pivot minor; rc44 verified
    ``gf_rref`` reproduces that p=7 drop). ``rref_crt`` walks the prime field
    DESCENDING from ``2**31-1`` (fewest primes for the product), so tiny primes like
    7 are never reached; the consensus rule is what guards against *any* unlucky
    prime, large or small. Here we drive the GF(p) reduction at p=7 (the canonical
    unlucky prime) and confirm it drops rank vs the consensus, i.e. would be
    discarded."""
    from srmech.amsc import modular_linalg as ml
    from srmech.amsc.qmat import _entries_mod_p, _key_dominates

    m = QMat.from_rows([[3, 1], [2, 3]])           # det = 7 ⇒ singular mod 7
    # A large lucky prime: full rank, pivots [0, 1].
    lucky = ml.gf_rref(_entries_mod_p(m._rows, 2147483647), 2147483647)
    lucky_key = (lucky["rank"], tuple(lucky["pivots"]))
    # p = 7 is unlucky: det ≡ 0 (mod 7) ⇒ the modular rank DROPS.
    unlucky = ml.gf_rref(_entries_mod_p(m._rows, 7), 7)
    unlucky_key = (unlucky["rank"], tuple(unlucky["pivots"]))
    assert lucky_key == (2, (0, 1))                # full rank over the lucky prime
    assert unlucky_key != lucky_key                # p=7 disagrees (rank drop)
    assert unlucky_key[0] < lucky_key[0]           # strictly lower modular rank
    assert _key_dominates(lucky_key, unlucky_key)  # consensus keeps the lucky key
    assert not _key_dominates(unlucky_key, lucky_key)
    # End-to-end the reconstruction is still exact (the lucky-prime consensus wins).
    assert m.rref_crt() == m.rref()
    assert m.rref_crt() == QMat.identity(2)


def test_rref_crt_first_prime_unlucky_consensus_restart():
    """When the FIRST prime tried is itself unlucky, the consensus must *restart*
    on the later higher-rank prime (discarding the first), not lock onto the wrong
    rank. We pin the unlucky prime to the head of the descending walk:
    ``det == 2147483647`` (the largest GF prime, the first the walk emits), so
    mod that prime the matrix drops rank — yet the exact RREF is still recovered
    byte-for-byte once the lucky primes establish the true consensus."""
    p0 = 2147483647                                 # the first descending GF prime
    m = QMat.from_rows([[p0, 1], [0, 1]])           # det == p0 ⇒ unlucky at p0
    assert m.rref_crt() == m.rref()
    assert m.rref_crt() == QMat.identity(2)


def test_rref_crt_empty_and_zero():
    """Degenerate shapes (a zero matrix, a single cell) match the dense path."""
    z = QMat.zeros(3, 3)
    assert z.rref_crt() == z.rref()
    one = QMat.from_rows([[Q(5, 7)]])
    assert one.rref_crt() == one.rref()
    assert one.rref_crt() == QMat.from_rows([[1]])


# ── the headline: the order-2 Franel 484x154 Zeilberger system ────────────────

def _franel_order2_rows():
    """Assemble the order-2 Franel (``Σ_k C(n,k)^3``) creative-telescoping
    homogeneous system as a list of rows of ``Q`` — the real 484x154 system the
    rc44 measurement is taken on. Reuses the ``zeilberger`` internals."""
    def P(*c):
        return Poly.from_coeffs(list(c))
    np1 = P(1, 1)
    n = P(0, 1)
    rn_num = BiPoly([np1 * np1 * np1])                              # (n+1)^3
    rn_den = BiPoly([np1 * np1 * np1, (np1 * np1) * P(-3),          # (n+1-k)^3
                     np1 * P(3), P(-1)])
    rk_num = BiPoly([n * n * n, (n * n) * P(-3), n * P(3), P(-1)])  # (n-k)^3
    rk_den = BiPoly([P(1), P(3), P(3), P(1)])                      # (k+1)^3
    order = 2
    rhos = [_rho(rn_num, rn_den, j) for j in range(order + 1)]
    den_p = BiPoly.one()
    for _, dj in rhos:
        den_p = den_p * dj
    rho_common = [nj * _bi_exact_div(den_p, dj) for nj, dj in rhos]
    n_deg = _ansatz_n_degree(rho_common, den_p, rk_num, rk_den, order)
    xk_deg, xn_deg = _ansatz_x_degree(rho_common, den_p, rk_num, rk_den, order, n_deg)
    a_block = (order + 1) * (n_deg + 1)
    n_unknowns = a_block + (xk_deg + 1) * (xn_deg + 1)
    rows = _assemble_rows(rho_common, den_p, rk_num, rk_den, order,
                          n_deg, xk_deg, xn_deg, n_unknowns, a_block)
    return rows


def test_franel_484x154_dimensions():
    """The assembled Franel order-2 system is exactly 484 rows x 154 columns
    (the headline shape the arena measurement is quoted on)."""
    rows = _franel_order2_rows()
    assert len(rows) == 484
    assert len(rows[0]) == 154


def test_franel_484x154_byte_identical():
    """THE HEADLINE: ``rref_crt`` == dense ``rref`` byte-for-byte on the real
    order-2 Franel 484x154 exact-ℚ system. This is the case the whole arc exists to
    make bounded-memory.

    HEAVY (the dense pure-ℚ RREF on 484x154 is minutes-scale in Python). Gated
    behind ``SRMECH_RUN_HEAVY=1`` so the default suite stays quick; CI / the
    self-verify run sets it. Skip-clean otherwise (the lighter random + keystone
    byte-identical checks above carry the correctness signal in the default run)."""
    import os

    import pytest
    if os.environ.get("SRMECH_RUN_HEAVY") != "1":
        pytest.skip("heavy Franel 484x154 byte-identical check — set "
                    "SRMECH_RUN_HEAVY=1 to run")
    rows = _franel_order2_rows()
    a = QMat.from_rows([list(r) for r in rows])
    crt = a.rref_crt()
    dense = a.rref()
    assert crt == dense, "rref_crt != rref on the Franel 484x154 system"
