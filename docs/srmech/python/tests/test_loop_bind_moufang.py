"""v0.7.0rc1 — the Moufang loop-bind (k=7 gauge arithmetic; MS #21 / #814).

Ports the F271/F272 reference self-tests (the `loop_bind_moufang.py` oracle)
against the PRODUCTION `srmech.amsc.hdc` loop-bind family:

  - exactly 7 associator-zero basis triples = the associative 3-planes (Fano lines)
  - L_a != R_a != R_aᵀ, and [L_a, R_b]·x == -loop_associator(a, x, b)
  - the three Moufang identities hold (the loop is Moufang)
  - the tangent algebra is Mal'cev, NOT Lie (Jacobi fails, Mal'cev holds)
  - the inverse unbinds: loop_bind(x, loop_inv(x)) == e0 (Moufang division)
  - associativity on a two-generator subalgebra (Artin's theorem)

Class-K clean throughout: zero-tests via the inner-product norm² ⟨v,v⟩, never
abs() (`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`).
"""
import itertools

import numpy as np

from srmech.amsc.hdc import (
    LOOP_DIM,
    loop_associator,
    loop_bind,
    loop_conj,
    loop_inv,
    loop_left_op,
    loop_right_op,
)

DIM = 8
SEED = 12345  # attested-B reproducibility seed (matches the reference oracle)


def _e(i, dim=DIM):
    v = np.zeros(dim)
    v[i] = 1.0
    return v


def _normsq(v):
    v = np.asarray(v, dtype=float)
    return float(np.dot(v, v))


def _commutator(a, b):
    return loop_bind(a, b) - loop_bind(b, a)


def _fano_lines():
    return [
        t
        for t in itertools.combinations(range(1, DIM), 3)
        if _normsq(loop_associator(_e(t[0]), _e(t[1]), _e(t[2]))) < 1e-9
    ]


def test_loop_dim_is_octonion():
    assert LOOP_DIM == 8


def test_seven_associative_fano_lines():
    # [1] exactly 7 associator-zero triples = the associative 3-planes
    assert len(_fano_lines()) == 7


def test_left_right_distinct_and_residue_identity():
    # [2] L != R != Rᵀ ; and [L_a, R_b]·x == -associator(a, x, b)
    a, b, x = _e(1), _e(2), _e(4)
    La, Ra = loop_left_op(a), loop_right_op(a)
    assert not np.allclose(La, Ra)
    assert not np.allclose(La, Ra.T)
    lr = loop_left_op(a) @ loop_right_op(b) - loop_right_op(b) @ loop_left_op(a)
    assert np.allclose(lr @ x, -loop_associator(a, x, b))


def test_three_moufang_identities():
    # [3] all three Moufang identities hold (the loop is Moufang)
    rng = np.random.default_rng(SEED)
    rnd = lambda: rng.standard_normal(DIM)
    worst = 0.0
    for _ in range(50):
        z, u, w = rnd(), rnd(), rnd()
        m1 = loop_bind(z, loop_bind(u, loop_bind(z, w))) - loop_bind(
            loop_bind(loop_bind(z, u), z), w
        )
        m2 = loop_bind(u, loop_bind(z, loop_bind(w, z))) - loop_bind(
            loop_bind(loop_bind(u, z), w), z
        )
        m3 = loop_bind(loop_bind(u, w), loop_bind(z, u)) - loop_bind(
            u, loop_bind(loop_bind(w, z), u)
        )
        worst = max(worst, _normsq(m1), _normsq(m2), _normsq(m3))
    assert worst < 1e-18


def test_jacobi_fails_malcev_holds():
    # [4] tangent algebra is Mal'cev, NOT Lie
    rng = np.random.default_rng(SEED)
    rnd = lambda: rng.standard_normal(DIM)

    def jac(p, q, r):
        return (
            _commutator(_commutator(p, q), r)
            + _commutator(_commutator(q, r), p)
            + _commutator(_commutator(r, p), q)
        )

    assert _normsq(jac(_e(1), _e(2), _e(4))) > 1e-6  # nonzero => not Lie
    xs, ys, zs = rnd(), rnd(), rnd()
    mal = jac(xs, ys, loop_bind(xs, zs)) - loop_bind(jac(xs, ys, zs), xs)
    assert _normsq(mal) < 1e-18


def test_inverse_unbinds_moufang_division():
    # loop_inv is the unbind key: x · x⁻¹ == x⁻¹ · x == e0 ; unit inv == conj
    rng = np.random.default_rng(SEED)
    x = rng.standard_normal(DIM)
    assert np.allclose(loop_bind(x, loop_inv(x)), _e(0))
    assert np.allclose(loop_bind(loop_inv(x), x), _e(0))
    u = x / np.sqrt(_normsq(x))
    assert np.allclose(loop_inv(u), loop_conj(u))


def test_associator_zero_on_two_generator_subalgebra():
    # Artin: any two octonions generate an associative subalgebra, so the
    # associator of a, b, and their product vanishes.
    a, b = _e(1), _e(2)
    c = loop_bind(a, b)
    assert _normsq(loop_associator(a, b, c)) < 1e-12


def test_real_anchor_is_identity():
    # e0 is the loop identity (the real anchor binds as 1).
    rng = np.random.default_rng(SEED)
    x = rng.standard_normal(DIM)
    assert np.allclose(loop_bind(_e(0), x), x)
    assert np.allclose(loop_bind(x, _e(0)), x)
