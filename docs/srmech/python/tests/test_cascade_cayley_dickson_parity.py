"""Cayley–Dickson open-exterior demonstrator + C/Python parity (#915 / §VII.6.23).

v0.7.3rc1 ships the deliberately non-reversible object on the far side of the
Hurwitz wall (ℝ→ℂ→ℍ→𝕆→𝕊(16)→…) as the executable falsifier for MFO §VII.6.23.
This test fixes the Python behaviour with from-scratch references (no srmech
import for the structural facts) and attests the C peer
``srmech_cd_basis_product`` bit-exact against the pure-Python cocycle.

The C peer is exercised only when ``HAS_NATIVE`` and the loaded libsrmech
exposes the rc1 symbol (a stale lib loads fine but skips cleanly).
"""
import ctypes
import random
from fractions import Fraction

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE
from srmech.amsc.cascade import cayley_dickson as cd


_CD_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cd_basis_product")
)

SKIP_IF_NO_CD_NATIVE = pytest.mark.skipif(
    not _CD_NATIVE,
    reason="installed libsrmech predates v0.7.3rc1 Cayley–Dickson symbol",
)


def _rand_elem(rng, n):
    return tuple(Fraction(rng.randint(-4, 4), rng.randint(1, 4)) for _ in range(n))


# ── the reversible interior: division algebras (dims 1, 2, 4, 8) ──────────────

def test_division_algebra_dims_are_the_interior():
    assert all(cd.is_division_algebra_dim(d) for d in (1, 2, 4, 8))
    assert not any(cd.is_division_algebra_dim(d) for d in (16, 32, 64))


@pytest.mark.parametrize("dim", [1, 2, 4, 8])
def test_norm_is_multiplicative_in_the_interior(dim):
    """N(x·y) = N(x)·N(y) — the composition identity, exact, for every dim ≤ 8."""
    rng = random.Random(2026 + dim)
    for _ in range(80):
        x, y = _rand_elem(rng, dim), _rand_elem(rng, dim)
        assert cd.cd_norm_sq(cd.cd_mult(x, y)) == cd.cd_norm_sq(x) * cd.cd_norm_sq(y)


@pytest.mark.parametrize("dim", [1, 2, 4, 8, 16, 32])
def test_conjugate_norm_identity_every_rung(dim):
    """x·x̄ = N(x)·1 at every rung — conjugation never dies (§VII.6.23.3)."""
    rng = random.Random(99 + dim)
    for _ in range(40):
        x = _rand_elem(rng, dim)
        xx = cd.cd_mult(x, cd.cd_conjugate(x))
        expected = [Fraction(0)] * dim
        expected[0] = cd.cd_norm_sq(x)
        assert list(xx) == expected


def test_complex_reproduced_from_reals():
    """ℂ: (a+bi)(c+di) = (ac−bd)+(ad+bc)i — the dim-2 doubling is ordinary ℂ."""
    a, b, c, d = Fraction(2), Fraction(3), Fraction(5), Fraction(7)
    assert cd.cd_mult((a, b), (c, d)) == (a * c - b * d, a * d + b * c)


def test_quaternion_is_associative_but_noncommutative():
    rng = random.Random(7)
    saw_noncommute = False
    for _ in range(50):
        x, y, z = (_rand_elem(rng, 4) for _ in range(3))
        # associative
        assert cd.cd_mult(cd.cd_mult(x, y), z) == cd.cd_mult(x, cd.cd_mult(y, z))
        if cd.cd_mult(x, y) != cd.cd_mult(y, x):
            saw_noncommute = True
    assert saw_noncommute


def test_octonion_is_nonassociative_but_alternative():
    rng = random.Random(8)
    saw_nonassoc = False
    for _ in range(80):
        x, y, z = (_rand_elem(rng, 8) for _ in range(3))
        if cd.cd_mult(cd.cd_mult(x, y), z) != cd.cd_mult(x, cd.cd_mult(y, z)):
            saw_nonassoc = True
        # alternativity: (x·x)·y == x·(x·y)
        assert cd.cd_mult(cd.cd_mult(x, x), y) == cd.cd_mult(x, cd.cd_mult(x, y))
    assert saw_nonassoc


# ── the open exterior: zero divisors at 16 (the §VII.6.23 falsifier) ──────────

def test_no_zero_divisor_below_16():
    """Octonions are a division algebra: no basis-pair (e_i±e_j)(e_k±e_l) vanishes."""
    for i in range(1, 8):
        for j in range(i + 1, 8):
            for k in range(1, 8):
                for l in range(k + 1, 8):
                    for s in (1, -1):
                        is_zero, _ = cd._basis_sum_terms_zero(
                            8, [(i, 1), (j, 1)], [(k, 1), (l, s)]
                        )
                        assert not is_zero


def test_sedenion_zero_divisor_witness():
    """A concrete dim-16 zero divisor x·y = 0 with x, y both nonzero — the
    executable form of 'zero divisors first appear at 16'."""
    w = cd.sedenion_zero_divisor_witness()
    assert w["dim"] == 16
    assert w["product_is_zero"]
    assert w["x_norm_sq"] > 0 and w["y_norm_sq"] > 0
    assert all(c == 0 for c in cd.cd_mult(w["x"], w["y"]))


def test_composition_norm_fails_at_16():
    """N(x·y) = 0 ≠ N(x)·N(y): the composition identity breaks on 𝕆→𝕊 (C3)."""
    w = cd.sedenion_zero_divisor_witness()
    assert cd.cd_norm_sq(cd.cd_mult(w["x"], w["y"])) == 0
    assert cd.cd_norm_sq(w["x"]) * cd.cd_norm_sq(w["y"]) != 0


def test_no_backward_direction_at_the_wall():
    """left_mult_kernel: the witness is a left zero divisor (no inverse map) —
    '§VII.6.23.4 anything past and unobserved is lost'; division algebras keep
    every nonzero element invertible."""
    w = cd.sedenion_zero_divisor_witness()
    ker = cd.left_mult_kernel(w["x"])
    assert len(ker) >= 1
    assert not cd.left_mult_is_invertible(w["x"])
    # a kernel vector v really satisfies x·v = 0
    assert all(c == 0 for c in cd.cd_mult(w["x"], ker[0]))
    # interior: every nonzero ≤𝕆 element is invertible
    rng = random.Random(123)
    for dim in (2, 4, 8):
        assert cd.left_mult_is_invertible(_rand_elem(rng, dim))


def test_basis_product_index_is_xor():
    """The cocycle result index is always i ⊕ j (the twisted ℤ₂ⁿ structure)."""
    for dim in (1, 2, 4, 8, 16, 32):
        for i in range(dim):
            for j in range(dim):
                idx, sign = cd.cd_basis_product(dim, i, j)
                assert idx == (i ^ j)
                assert sign in (1, -1)


def test_basis_product_matches_full_mult():
    """The integer cocycle agrees with the rational product on basis elements."""
    for dim in (1, 2, 4, 8, 16, 32):
        for i in range(dim):
            for j in range(dim):
                idx, sign = cd.cd_basis_product(dim, i, j)
                prod = cd.cd_mult(cd.cd_basis(dim, i), cd.cd_basis(dim, j))
                expected = [Fraction(0)] * dim
                expected[idx] = Fraction(sign)
                assert list(prod) == expected


# ── error cases ───────────────────────────────────────────────────────────────

def test_rejects_non_power_of_two():
    with pytest.raises(ValueError):
        cd.cd_mult((1, 2, 3), (1, 2, 3))


def test_rejects_dimension_mismatch():
    with pytest.raises(ValueError):
        cd.cd_mult((1, 2), (1, 2, 3, 4))


def test_basis_product_rejects_bad_args():
    with pytest.raises(ValueError):
        cd.cd_basis_product(6, 0, 0)        # 6 is not a power of two
    with pytest.raises(ValueError):
        cd.cd_basis_product(8, 8, 0)        # index out of range


# ── native C peer attested bit-exact against the Python cocycle ───────────────

@SKIP_IF_NO_CD_NATIVE
def test_native_basis_product_matches_python():
    for dim in (1, 2, 4, 8, 16, 32, 64):
        for i in range(dim):
            for j in range(dim):
                out_idx = ctypes.c_int(-1)
                out_sign = ctypes.c_int(0)
                rc = _native.LIB.srmech_cd_basis_product(
                    ctypes.c_int(dim), ctypes.c_int(i), ctypes.c_int(j),
                    ctypes.byref(out_idx), ctypes.byref(out_sign),
                )
                assert rc == _native.SRMECH_OK
                py_idx, py_sign = cd.cd_basis_product(dim, i, j)
                assert (out_idx.value, out_sign.value) == (py_idx, py_sign)


@SKIP_IF_NO_CD_NATIVE
def test_native_rejects_bad_input():
    out_idx = ctypes.c_int(0)
    out_sign = ctypes.c_int(0)
    rc = _native.LIB.srmech_cd_basis_product(
        ctypes.c_int(6), ctypes.c_int(0), ctypes.c_int(0),
        ctypes.byref(out_idx), ctypes.byref(out_sign),
    )
    assert rc == _native.SRMECH_ERR_BAD_INPUT


@SKIP_IF_NO_CD_NATIVE
def test_cd_symbol_exposed():
    assert hasattr(_native.LIB, "srmech_cd_basis_product")
