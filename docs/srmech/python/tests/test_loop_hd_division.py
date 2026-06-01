"""v0.7.0rc5 — the per-block HD Moufang-division family + the loop_inv/loop_conj
HD footgun guard (upstream §12.1 / §12.2).

A bug-test sweep caught a silent footgun: ``loop_inv`` / ``loop_conj`` are
single-Cayley-Dickson-element ops, but the HD width 2048 = 256·8 is ALSO a power
of two, so an HD block-octonion vector slipped through ``_as_loop`` and got the
GLOBAL conjugate/inverse — wrong by ~‖·‖, no exception. The natural
``loop_bind_hd(E, loop_inv(c))`` right-peel was silently wrong.

This voxel:
  - adds the per-block atoms ``loop_conj_hd`` / ``loop_inv_hd`` (the missing
    direct-sum ⊕ of NB dim-8 ops),
  - adds ``loop_runbind_hd`` — the HD RIGHT-unbind (peels the RIGHT factor, what a
    left-fold sequence store needs), complementing the LEFT-division
    ``loop_unbind_hd``,
  - makes ``loop_inv`` / ``loop_conj`` RAISE on an HD block vector (loud failure
    replaces the silent-wrong global result), single-octonion path unchanged.

All per-block ops are the shipped single-element op applied block-wise, so they
agree with ``loop_bind`` by construction (no convention guess). NO new class.
"""

import numpy as np
import pytest

from srmech.amsc import hdc
from srmech.amsc.hdc import LOOP_DIM

NB = 64  # blocks; D = NB * 8 = 512 (an HD width, > one octonion)


def _unit_blocks(seed):
    """NB unit-norm dim-8 octonion blocks, flattened to one HD vector."""
    rng = np.random.default_rng(seed)
    b = rng.standard_normal((NB, LOOP_DIM))
    b /= np.linalg.norm(b, axis=1, keepdims=True)
    return b.reshape(-1)


def _blocks(v):
    return np.asarray(v, dtype=float).reshape(-1, LOOP_DIM)


# ----------------------------------------------------------------------
# Per-block atoms = the shipped single-element op, block-wise
# ----------------------------------------------------------------------


def test_loop_conj_hd_is_single_loop_conj_per_block():
    x = _unit_blocks(12345)
    got = _blocks(hdc.loop_conj_hd(x))
    want = np.stack([hdc.loop_conj(xb) for xb in _blocks(x)])
    assert np.array_equal(got, want)


def test_loop_inv_hd_is_single_loop_inv_per_block():
    # non-unit blocks too: scale each block by a distinct factor.
    x = _unit_blocks(777)
    xb = _blocks(x).copy()
    for k in range(NB):
        xb[k] *= (1.0 + 0.1 * k)
    x = xb.reshape(-1)
    got = _blocks(hdc.loop_inv_hd(x))
    want = np.stack([hdc.loop_inv(b) for b in _blocks(x)])
    assert np.allclose(got, want, atol=1e-15)


def test_loop_inv_hd_equals_loop_conj_hd_on_unit_blocks():
    # unit octonion: x⁻¹ = x̄ exactly.
    x = _unit_blocks(23)
    assert np.allclose(hdc.loop_inv_hd(x), hdc.loop_conj_hd(x), atol=1e-14)


def test_loop_inv_hd_is_the_per_block_bind_identity():
    # loop_bind_hd(x, loop_inv_hd(x)) == per-block e0 (the unbind key).
    x = _unit_blocks(99)
    prod = _blocks(hdc.loop_bind_hd(x, hdc.loop_inv_hd(x)))
    e0 = np.zeros(LOOP_DIM)
    e0[0] = 1.0
    for k in range(NB):
        assert np.allclose(prod[k], e0, atol=1e-13)


# ----------------------------------------------------------------------
# RIGHT-unbind (loop_runbind_hd) vs LEFT-unbind (loop_unbind_hd)
# ----------------------------------------------------------------------


def test_loop_runbind_hd_recovers_right_factor():
    # b = loop_bind_hd(v, a) = v_k·a_k  ⟹  loop_runbind_hd(a, b) == v
    a = _unit_blocks(811)
    v = _unit_blocks(812)
    b = hdc.loop_bind_hd(v, a)
    rec = hdc.loop_runbind_hd(a, b)
    assert np.allclose(rec, v, atol=1e-12)


def test_loop_unbind_hd_recovers_left_built_factor():
    # b = loop_bind_hd(a, v) = a_k·v_k  ⟹  loop_unbind_hd(a, b) == v
    a = _unit_blocks(813)
    v = _unit_blocks(814)
    b = hdc.loop_bind_hd(a, v)
    rec = hdc.loop_unbind_hd(a, b)
    assert np.allclose(rec, v, atol=1e-12)


def test_left_and_right_unbind_are_distinct():
    # The loop bind is non-commutative, so the LEFT unbind does NOT recover the
    # right-built factor (and vice versa) — proving the two peels are different.
    a = _unit_blocks(815)
    v = _unit_blocks(816)
    b_right_built = hdc.loop_bind_hd(v, a)   # v on the LEFT, a on the RIGHT
    wrong = hdc.loop_unbind_hd(a, b_right_built)  # left-division: wrong factor
    assert not np.allclose(wrong, v, atol=1e-6)
    # the right-division recovers it:
    assert np.allclose(hdc.loop_runbind_hd(a, b_right_built), v, atol=1e-12)


def test_loop_runbind_hd_left_fold_sequence_peel():
    # A left-fold store c = ((s0·s1)·s2); peel s2 off the RIGHT with runbind.
    s0 = _unit_blocks(1)
    s1 = _unit_blocks(2)
    s2 = _unit_blocks(3)
    c = hdc.loop_bind_hd(hdc.loop_bind_hd(s0, s1), s2)
    peeled = hdc.loop_runbind_hd(s2, c)              # recovers (s0·s1)
    assert np.allclose(peeled, hdc.loop_bind_hd(s0, s1), atol=1e-12)


# ----------------------------------------------------------------------
# Footgun guard: loop_inv / loop_conj RAISE on HD block input (§12.1)
# ----------------------------------------------------------------------


def test_loop_inv_raises_on_hd_block_vector():
    x = _unit_blocks(5)  # length NB*8 = 512, a multiple of 8 wider than one octonion
    with pytest.raises(ValueError, match="HD block-octonion"):
        hdc.loop_inv(x)


def test_loop_conj_raises_on_hd_block_vector():
    x = _unit_blocks(6)
    with pytest.raises(ValueError, match="HD block-octonion"):
        hdc.loop_conj(x)


def test_single_octonion_loop_inv_conj_unchanged():
    # dim-8 (one octonion) is NOT guarded; the existing behaviour holds.
    rng = np.random.default_rng(42)
    u = rng.standard_normal(LOOP_DIM)
    u /= np.linalg.norm(u)
    e0 = np.zeros(LOOP_DIM)
    e0[0] = 1.0
    assert np.allclose(hdc.loop_bind(u, hdc.loop_inv(u)), e0, atol=1e-14)
    assert np.allclose(hdc.loop_inv(u), hdc.loop_conj(u), atol=1e-14)
    # dims 1,2,4 (real/complex/quaternion) are also single elements — not guarded.
    q = rng.standard_normal(4)
    assert hdc.loop_conj(q).shape == (4,)


# ----------------------------------------------------------------------
# multiple-of-8 validation on the new HD ops
# ----------------------------------------------------------------------


@pytest.mark.parametrize("fn", ["loop_conj_hd", "loop_inv_hd"])
def test_hd_unary_requires_multiple_of_8(fn):
    bad = np.ones(8 * 3 + 1)  # 25, not a multiple of 8
    with pytest.raises(AssertionError, match="positive multiple"):
        getattr(hdc, fn)(bad)


def test_loop_runbind_hd_requires_multiple_of_8_and_equal_length():
    bad = np.ones(8 * 3 + 1)
    with pytest.raises(AssertionError, match="positive multiple"):
        hdc.loop_runbind_hd(bad, bad)
    a = _unit_blocks(7)
    with pytest.raises(AssertionError, match="equal length"):
        hdc.loop_runbind_hd(a, a[:-LOOP_DIM])
