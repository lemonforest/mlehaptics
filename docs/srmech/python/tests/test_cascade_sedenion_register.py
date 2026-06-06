"""Sedenion-addressable hyper-loop RBS-HDC instrument (UPSTREAM §31; F465 + F468).

v0.7.4rc1 ships the sedenion box as an addressable RBS-HDC instrument —
`srmech.amsc.cascade.SedenionRegister`. It is a pure composition of shipped
v0.7.3 primitives (no new algebra); the genuinely-new surface is the address↔CD
`navigate` homomorphism + the `is_navigable` reversibility gate.

The storage + working-word paths are the scientific tier (numpy on call) and skip
cleanly without numpy; `navigate` / `is_navigable` / `carry` / `correct` are
numpy-free and always run.
"""
from fractions import Fraction

import pytest

from srmech.amsc.cascade import (
    SedenionRegister,
    sedenion_register,
    NUM_SLOTS,
    OCT_BLOCK,
    EC_BLOCK,
    WORKING_WORD_CAP,
)
from srmech.amsc.cascade import cayley_dickson as cd

try:
    import numpy  # noqa: F401
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False

SKIP_NO_NUMPY = pytest.mark.skipif(
    not _HAS_NUMPY, reason="storage / working-word use the scientific tier (numpy)"
)


# ── constants + construction ──────────────────────────────────────────────────

def test_constants():
    assert NUM_SLOTS == 16
    assert OCT_BLOCK == tuple(range(0, 8))
    assert EC_BLOCK == tuple(range(8, 16))
    assert WORKING_WORD_CAP == 7


def test_factory_returns_register():
    reg = sedenion_register()
    assert isinstance(reg, SedenionRegister)
    assert reg.D == 8192


# ── [A] addressable HDC storage (scientific tier) ─────────────────────────────

@SKIP_NO_NUMPY
def test_addressable_read_back_octonion_block():
    reg = sedenion_register(D=8192)
    truth = {0: "alpha", 1: "beta", 2: "gamma", 3: "delta",
             4: "eps", 5: "zeta", 6: "eta", 7: "theta"}
    for s, k in truth.items():
        reg.write(s, k)
    hits = sum(reg.read(s)[0] == truth[s] for s in truth)
    assert hits == 8, f"only {hits}/8 slots read back cleanly"


@SKIP_NO_NUMPY
def test_empty_register_read_is_none():
    assert sedenion_register().read(0) == (None, 1)


@SKIP_NO_NUMPY
def test_materialize_empty_raises():
    with pytest.raises(ValueError):
        sedenion_register().materialize()


# ── [B] the ≤7 reversible working word ────────────────────────────────────────

@SKIP_NO_NUMPY
def test_working_word_couple_uncouple_bit_exact():
    reg = sedenion_register()
    vals = [1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0]
    oct_word = reg.couple_working(vals)
    assert len(oct_word) == 8
    rec = reg.uncouple_working(oct_word)
    assert max(abs(rec[i] - vals[i]) for i in range(7)) < 1e-9


def test_working_word_rejects_eighth_value():
    # numpy-free: the cap check happens before any coupler call
    with pytest.raises(ValueError):
        sedenion_register().couple_working([1.0] * 8)


# ── [C] the EC / carry block (numpy-free; Hamming) ────────────────────────────

def test_carry_and_correct_single_error():
    reg = sedenion_register()
    enc = reg.carry([1, 0, 1, 1], 3)         # Hamming(7,4)
    assert len(enc) == 7
    bad = list(enc)
    bad[2] ^= 1                               # corrupt one bit in the carry block
    dec = reg.correct(bad)
    assert dec["error_position"] == 3
    assert dec["data"] == [1, 0, 1, 1]


# ── [D] the operational hyper-loop: navigate (numpy-free) ─────────────────────

def test_navmap_matches_cd_basis_product():
    reg = sedenion_register()
    for j in range(NUM_SLOTS):
        m = reg.navmap(j)
        for i in range(NUM_SLOTS):
            assert m[i] == cd.cd_basis_product(NUM_SLOTS, i, j)


def test_navigate_routes_per_cd_table():
    reg = sedenion_register()
    # populate the slot assignment WITHOUT minting (write records the assignment;
    # we read the assignment dict directly, which is numpy-free).
    for s in range(8):
        reg._slots[s] = (f"theme{s}", 1)
    j = 1
    nav = reg.navigate(j)
    m = reg.navmap(j)
    routed = 0
    for i, (key, sgn) in reg.slots().items():
        k, s = m[i]
        assert nav.slots()[k] == (key, sgn * s)
        routed += 1
    assert routed == 8


def test_navigate_twice_is_global_sign_flip():
    reg = sedenion_register()
    for s in range(8):
        reg._slots[s] = (f"v{s}", 1)
    j = 1
    nav2 = reg.navigate(j).navigate(j)            # e_j² = −1
    for i, (key, sgn) in reg.slots().items():
        k, s = nav2.slots()[i]                      # back to slot i...
        assert k == key                            # same content key
        assert s == -sgn                           # ...with global sign flip


def test_navmap_rejects_bad_basis():
    with pytest.raises(ValueError):
        sedenion_register().navmap(16)


# ── is_navigable: the reversibility horizon (numpy-free) ───────────────────────

def test_is_navigable_octonion_reversible():
    reg = sedenion_register()
    oct_dir = [Fraction(0)] * 8
    oct_dir[1] = Fraction(1)
    oct_dir[2] = Fraction(1)                        # composite octonion direction
    assert reg.is_navigable(oct_dir) is True


def test_is_navigable_sedenion_zero_divisor_irreversible():
    reg = sedenion_register()
    witness = cd.sedenion_zero_divisor_witness()["x"]
    assert reg.is_navigable(witness) is False       # the Hurwitz horizon


def test_single_basis_always_navigable():
    reg = sedenion_register()
    for j in range(1, NUM_SLOTS):                    # every basis e_j (one-hot)
        e = [Fraction(0)] * NUM_SLOTS
        e[j] = Fraction(1)
        assert reg.is_navigable(e) is True


# ── slot validation ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [-1, 16, 99])
def test_write_rejects_out_of_range_slot(bad):
    with pytest.raises(ValueError):
        sedenion_register().write(bad, "x")
