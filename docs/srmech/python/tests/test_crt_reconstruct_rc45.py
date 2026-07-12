"""rc45 — the CRT closers ``crt_combine`` + ``rational_reconstruct``.

Rung 2 of the CRT-QMat re-fibration arc. After the swell-free GF(p) elimination
(``gf_rref``, rc44) produces one residue per reduction prime, these two ops turn
the per-prime residues back into the EXACT rational answer:

  * ``modular_linalg.crt_combine``  (Class I) — Chinese-Remainder-combine the
    per-prime residues into one residue modulo the product of the primes
    (iterative Garner; the combined modulus is bignum for k >= 3 of the ~31-bit
    reduction primes).
  * ``rational.rational_reconstruct`` (Class N) — recover the bounded p/q
    congruent to that residue (half-GCD / Wang reconstruction).

This test is numpy-FREE and ``math``-FREE: it uses only ``fractions.Fraction`` +
the srmech ``cyclic`` / ``rational`` primitives + plain Python ``int``. Every
result is cross-checked against an INDEPENDENT in-test oracle (its own iterative
CRT via ``pow(m, -1, …)``; its own reconstruction round-trip), never the library
against itself. The capstone is the MINI END-TO-END (prefigures rc46):
``gf_rref`` over several primes -> ``crt_combine`` -> ``rational_reconstruct``
== the ``Fraction`` dense-RREF answer BYTE-FOR-BYTE.
"""
from __future__ import annotations

import random
from fractions import Fraction

from srmech.amsc import cyclic as _cyclic
from srmech.amsc.modular_linalg import crt_combine, gf_rref
from srmech.amsc.primes import next_prime
from srmech.amsc.rational import _py_isqrt, rational_reconstruct


# ── independent oracles (Fraction + plain int; no numpy, no math) ─────────────

def _crt_oracle(residues, moduli):
    """An INDEPENDENT iterative CRT (``pow(m, -1, …)``), distinct from the
    library's ``cyclic.mod_inv`` path. Returns ``(residue, modulus)``."""
    cur = residues[0] % moduli[0]
    mod = moduli[0]
    for i in range(1, len(moduli)):
        m_i = moduli[i]
        inv = pow(mod % m_i, -1, m_i)
        t = ((residues[i] - cur) * inv) % m_i
        cur += mod * t
        mod *= m_i
    return cur % mod, mod


def _prime_pool(count, start=2_000_000_000):
    """``count`` distinct ~31-bit primes from ``next_prime``."""
    pool = []
    n = start
    while len(pool) < count:
        p = next_prime(n)
        pool.append(p)
        n = p
    return pool


def _fraction_rref(rows):
    """Exact ``Fraction`` dense reduced-row-echelon form (the reconstruction
    oracle). Returns ``(rref, pivots, rank)``."""
    m = [[Fraction(v) for v in r] for r in rows]
    nr, nc = len(m), len(m[0])
    pr = 0
    pivots = []
    for col in range(nc):
        if pr >= nr:
            break
        sel = next((r for r in range(pr, nr) if m[r][col] != 0), None)
        if sel is None:
            continue
        m[pr], m[sel] = m[sel], m[pr]
        inv = Fraction(1) / m[pr][col]
        m[pr] = [v * inv for v in m[pr]]
        for r in range(nr):
            if r != pr and m[r][col] != 0:
                f = m[r][col]
                m[r] = [m[r][c] - f * m[pr][c] for c in range(nc)]
        pivots.append(col)
        pr += 1
    return m, pivots, pr


# ── crt_combine ───────────────────────────────────────────────────────────────

def test_crt_combine_vs_oracle_random():
    """``crt_combine`` matches an independent iterative-CRT oracle on random
    residue / distinct-prime sets (2..6 primes), and the combined residue is
    congruent to every input residue modulo its prime."""
    rng = random.Random(2718281828)
    pool = _prime_pool(20)
    for _ in range(300):
        k = rng.randint(2, 6)
        moduli = rng.sample(pool, k)
        residues = [rng.randrange(0, m) for m in moduli]
        out = crt_combine(residues, moduli)
        ores, omod = _crt_oracle(residues, moduli)
        assert out == {"residue": ores, "modulus": omod}
        for r, m in zip(residues, moduli):
            assert out["residue"] % m == r % m
        prod = 1
        for m in moduli:
            prod *= m
        assert out["modulus"] == prod


def test_crt_combine_modulus_exceeds_64_bits():
    """k >= 3 of the ~31-bit primes pushes the combined modulus past 2**64 — the
    accumulator is genuinely bignum (no ceiling)."""
    pool = _prime_pool(5)
    out = crt_combine([1, 2, 3, 4, 5], pool)
    assert out["modulus"] > (1 << 64)
    for r, m in zip([1, 2, 3, 4, 5], pool):
        assert out["residue"] % m == r % m


def test_crt_combine_single_congruence():
    """k == 1 returns the lone residue reduced into [0, m_0)."""
    out = crt_combine([17], [13])
    assert out == {"residue": 4, "modulus": 13}


def test_crt_combine_rejects_bad_input():
    import pytest
    with pytest.raises(ValueError):
        crt_combine([], [])
    with pytest.raises(ValueError):
        crt_combine([1, 2], [5])              # length mismatch
    with pytest.raises(ValueError):
        crt_combine([1, 2], [5, 5])           # non-distinct moduli


# ── rational_reconstruct ──────────────────────────────────────────────────────

def test_rational_reconstruct_round_trip():
    """Pick known p/q within the Wang bound, form ``residue = p·q⁻¹ (mod M)``,
    and assert the reconstruction recovers the reduced signed ``(p, q)``."""
    rng = random.Random(31415926)
    pool = _prime_pool(20)
    checked = 0
    for _ in range(300):
        k = rng.randint(3, 5)
        moduli = rng.sample(pool, k)
        M = 1
        for m in moduli:
            M *= m
        bound = _py_isqrt(M // 2)
        cap = min(bound, 10 ** 9)
        q = rng.randint(1, cap)
        p = rng.randint(-cap, cap)
        g = _cyclic.gcd(p if p >= 0 else -p, q) if p else q
        if g == 0:
            continue
        p //= g
        q //= g
        if q == 0:
            q = 1
        if _cyclic.gcd(q, M) != 1:
            continue
        residue = (p * pow(q, -1, M)) % M
        got = rational_reconstruct(residue, M)
        assert got == (p, q), (got, (p, q))
        assert Fraction(got[0], got[1]) == Fraction(p, q)
        checked += 1
    assert checked > 100            # the filters never starve the test


def test_rational_reconstruct_none_out_of_bound():
    """A rational whose denominator exceeds the default Wang bound has NO valid
    reconstruction in-bounds — the op returns ``None``."""
    pool = _prime_pool(3)
    M = 1
    for m in pool:
        M *= m
    bound = _py_isqrt(M // 2)
    big_q = bound + 12345
    while _cyclic.gcd(big_q, M) != 1:
        big_q += 1
    big_p = bound // 2 + 7
    residue = (big_p * pow(big_q, -1, M)) % M
    assert rational_reconstruct(residue, M) is None


def test_rational_reconstruct_zero_and_integer():
    """Zero residue reconstructs to 0/1; an exact integer residue r (|r| <= bound)
    reconstructs to r/1."""
    pool = _prime_pool(4)
    M = 1
    for m in pool:
        M *= m
    assert rational_reconstruct(0, M) == (0, 1)
    assert rational_reconstruct(5, M) == (5, 1)
    # a negative integer rides the modular representative M - 5.
    assert rational_reconstruct((-5) % M, M) == (-5, 1)


# ── THE MINI END-TO-END (prefigures rc46) ─────────────────────────────────────

def test_mini_end_to_end_crt_solve_equals_fraction_rref():
    """gf_rref over SEVERAL primes -> crt_combine the per-entry residues ->
    rational_reconstruct each == the Fraction dense-RREF answer BYTE-FOR-BYTE.

    Proves Class I∘J∘N composes to recover the exact ℚ result at bounded memory.
    Unlucky primes (where the GF(p) rank / pivot structure diverges from the
    consensus) are SKIPPED — noted via ``skipped`` below."""
    A_aug = [
        [2, 3, 1, 1],
        [4, 1, 2, 2],
        [1, 2, 5, 3],
    ]
    oracle_rref, oracle_pivots, oracle_rank = _fraction_rref(A_aug)

    pool = _prime_pool(12)
    per_prime_rref = []
    used = []
    skipped = []
    for p in pool:
        out = gf_rref(A_aug, p)
        if out["rank"] != oracle_rank or out["pivots"] != oracle_pivots:
            skipped.append(p)            # unlucky prime — rank/pivot drop
            continue
        per_prime_rref.append(out["rref"])
        used.append(p)
        if len(used) >= 7:
            break
    assert len(used) >= 5

    M = 1
    for p in used:
        M *= p
    bound = _py_isqrt(M // 2)

    n_rows = len(A_aug)
    n_cols = len(A_aug[0])
    recovered = []
    for i in range(n_rows):
        row = []
        for j in range(n_cols):
            residues = [per_prime_rref[k][i][j] for k in range(len(used))]
            combo = crt_combine(residues, used)
            rr = rational_reconstruct(combo["residue"], combo["modulus"],
                                      num_bound=bound, den_bound=bound)
            assert rr is not None, (i, j)
            row.append(Fraction(rr[0], rr[1]))
        recovered.append(row)

    assert recovered == oracle_rref
    # the solution column (full-rank 3x3 -> last column is x,y,z).
    assert [recovered[i][-1] for i in range(n_rows)] == [
        Fraction(2, 9), Fraction(0), Fraction(5, 9),
    ]


def test_mini_end_to_end_skips_unlucky_prime():
    """A system with det(A) == 7 makes GF(7) singular — the consensus-rank skip
    correctly drops prime 7 and still recovers the exact Fraction solution."""
    A_aug = [
        [3, 1, 5],
        [2, 3, 4],
    ]                                  # det(A) = 3*3 - 1*2 = 7
    oracle_rref, oracle_pivots, oracle_rank = _fraction_rref(A_aug)

    pool = [7] + _prime_pool(8)        # prime 7 deliberately first (det % 7 == 0)
    per_prime_rref = []
    used = []
    skipped = []
    for p in pool:
        out = gf_rref(A_aug, p)
        if out["rank"] != oracle_rank or out["pivots"] != oracle_pivots:
            skipped.append(p)
            continue
        per_prime_rref.append(out["rref"])
        used.append(p)
        if len(used) >= 6:
            break
    assert 7 in skipped                # the unlucky prime WAS skipped

    M = 1
    for p in used:
        M *= p
    bound = _py_isqrt(M // 2)
    recovered = []
    for i in range(len(A_aug)):
        row = []
        for j in range(len(A_aug[0])):
            residues = [per_prime_rref[k][i][j] for k in range(len(used))]
            combo = crt_combine(residues, used)
            rr = rational_reconstruct(combo["residue"], combo["modulus"],
                                      num_bound=bound, den_bound=bound)
            assert rr is not None
            row.append(Fraction(rr[0], rr[1]))
        recovered.append(row)
    assert recovered == oracle_rref
    assert [recovered[i][-1] for i in range(2)] == [Fraction(11, 7), Fraction(2, 7)]
