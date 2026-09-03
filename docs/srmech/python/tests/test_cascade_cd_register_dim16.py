"""The addressable RBS-HDC instrument at dim 16 (UPSTREAM §31; F465 + F468).

v0.7.4rc1 shipped the sedenion box as an addressable RBS-HDC instrument. It was a
pure composition of shipped v0.7.3 primitives (no new algebra); the genuinely-new
surface was the address↔CD ``navigate`` homomorphism plus the ``is_navigable``
reversibility gate. rc297 generalised the slot count and rc464 made
:class:`~srmech.cascade.cd_register.CDRegister` the register shape, so this suite
now drives the dim-16 rung of the general register — the SAME instrument, spelled
``cd_register(16, namespace="SEDENION", coupling=True, error_correction=True)``.

Why that spelling and not ``cd_register(16)``:

* ``namespace`` IS the address-mint name (``mint_vector(f"{namespace}:e{slot}")``),
  so it decides the minted address hypervectors and therefore the crosstalk. It
  is the one variable that made the 16-slot register the 16-slot register.
* the two OPT layers are OFF by default on a general register — a bare register is
  a pure signed-pointer addressing object — while the 16-slot class carried them
  unconditionally. Opting in restores the instrument this suite is about.

Both are gated bit-exactly against that class's recorded behaviour in
``test_cd_register_golden_rc464.py``; what is checked HERE is the instrument's
own contract at this rung.

numpy-FREE (#564): the WHOLE instrument is numpy-free — the storage path
(``mint_vector`` + ``hdc.bind``/``bundle``/``similarity``) and the reversible
working word (``hypercomplex_couple``) route through cascades, so every test here
RUNS with numpy NOT installed.

No builtin ``abs()``: the roundtrip band is measured with an explicit Class-K
pin-slot branch, the form ``tests/test_sedenion_addr_c_rc199.py`` established.
"""
from fractions import Fraction

import pytest

from srmech.cascade import cd_register, CDRegister, WORKING_WORD_CAP
from srmech.cascade import cayley_dickson as cd

#: The dim-16 instrument: the address namespace and both OPT layers, i.e. the
#: register the 16-slot class was.
DIM = 16


def _reg(D: int = 8192):
    return cd_register(DIM, D=D, namespace="SEDENION",
                       coupling=True, error_correction=True)


def _within(a: float, b: float, tol: float) -> bool:
    """Class-K pin-slot magnitude on the residual — never builtin ``abs()``."""
    d = a - b
    mag = d if d >= 0.0 else -d
    return mag < tol


# ── the block structure, which replaced the flat 16-slot constants ────────────

def test_block_structure_replaces_the_fixed_slot_constants():
    """``NUM_SLOTS`` / ``OCT_BLOCK`` / ``EC_BLOCK`` were module constants of a
    class hard-wired to one rung. Their general form is per-instance and DERIVED:
    ``dim`` is the address space, ``working_block()`` is the octonion reversible
    block (the Hurwitz cap, 7 imaginary slots at EVERY rung), ``carry_block()``
    everything past the reversibility horizon. At dim 16 they reproduce the old
    constants exactly, which is what makes this a generalisation and not a
    replacement."""
    reg = _reg(D=256)
    assert reg.dim == 16
    assert reg.working_block() == tuple(range(0, 8))
    assert reg.carry_block() == tuple(range(8, 16))
    assert WORKING_WORD_CAP == 7


def test_factory_returns_register():
    reg = _reg()
    assert isinstance(reg, CDRegister)
    assert reg.D == 8192
    assert reg.namespace == "SEDENION"


# ── [A] addressable HDC storage (numpy-free; mint + Class-M bind/bundle) ──────

def test_addressable_read_back_octonion_block():
    reg = _reg(D=8192)
    truth = {0: "alpha", 1: "beta", 2: "gamma", 3: "delta",
             4: "eps", 5: "zeta", 6: "eta", 7: "theta"}
    for s, k in truth.items():
        reg.write(s, k)
    hits = sum(reg.read(s)[0] == truth[s] for s in truth)
    assert hits == 8, f"only {hits}/8 slots read back cleanly"


def test_empty_register_read_is_none():
    assert _reg().read(0) == (None, 1)


def test_materialize_empty_raises():
    with pytest.raises(ValueError):
        _reg().materialize()


# ── [B] the reversible working word (numpy-free; hypercomplex_couple) ────────

def test_working_word_couple_uncouple_bit_exact():
    reg = _reg()
    vals = [1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0]
    oct_word = reg.couple_working(vals)
    assert len(oct_word) == 8
    rec = reg.uncouple_working(oct_word)
    assert all(_within(rec[i], vals[i], 1e-9) for i in range(7))


def test_working_word_rejects_the_eighth_value():
    # numpy-free: the cap check happens before any coupler call. At dim 16 the
    # derived cap min(dim, 8) - 1 coincides with the old flat 7.
    with pytest.raises(ValueError):
        _reg().couple_working([1.0] * 8)


def test_the_working_word_is_an_opt_layer_now():
    """The one behavioural difference from the 16-slot class, stated rather than
    inherited: coupling is OPT on a general register, so a bare one raises."""
    with pytest.raises(ValueError, match="coupling=True"):
        cd_register(DIM, D=256).couple_working([1.0])


# ── [C] the EC / carry block (numpy-free; Hamming) ───────────────────────────

def test_carry_and_correct_single_error():
    reg = _reg()
    enc = reg.carry([1, 0, 1, 1], 3)         # Hamming(7,4)
    assert len(enc) == 7
    bad = list(enc)
    bad[2] ^= 1                               # corrupt one bit in the carry block
    dec = reg.correct(bad)
    assert dec["error_position"] == 3
    assert dec["data"] == [1, 0, 1, 1]


def test_the_ec_block_is_an_opt_layer_now():
    with pytest.raises(ValueError, match="error_correction=True"):
        cd_register(DIM, D=256).carry([1, 0, 1, 1], 3)


# ── [D] the operational hyper-loop: navigate (numpy-free) ────────────────────

def test_navmap_matches_cd_basis_product():
    reg = _reg()
    for j in range(DIM):
        m = reg.navmap(j)
        for i in range(DIM):
            assert m[i] == cd.cd_basis_product(DIM, i, j)


def test_navigate_routes_per_cd_table():
    reg = _reg()
    # populate the slot assignment WITHOUT minting (write records the assignment;
    # we set the assignment dict directly, which is numpy-free).
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
    reg = _reg()
    for s in range(8):
        reg._slots[s] = (f"v{s}", 1)
    j = 1
    nav2 = reg.navigate(j).navigate(j)            # e_j² = −1
    for i, (key, sgn) in reg.slots().items():
        k, s = nav2.slots()[i]                      # back to slot i...
        assert k == key                            # same content key
        assert s == -sgn                           # ...with global sign flip


def test_navigate_carries_the_address_namespace():
    """Routing produces a NEW register, and it must still mint the SAME
    addresses — a navigate that dropped the namespace would silently re-mint
    every address and break the read on the routed register."""
    reg = _reg(D=512)
    reg.write(0, "alpha")
    moved = reg.navigate(1)
    assert moved.namespace == "SEDENION"
    assert moved.dim == 16 and moved.D == 512


def test_navmap_rejects_bad_basis():
    with pytest.raises(ValueError):
        _reg().navmap(16)


# ── is_navigable: the reversibility horizon (numpy-free) ─────────────────────

def test_is_navigable_octonion_reversible():
    reg = _reg()
    oct_dir = [Fraction(0)] * 8
    oct_dir[1] = Fraction(1)
    oct_dir[2] = Fraction(1)                        # composite octonion direction
    assert reg.is_navigable(oct_dir) is True


def test_is_navigable_zero_divisor_irreversible():
    reg = _reg()
    witness = cd.cd_zero_divisor_witness(16)["x"]
    assert reg.is_navigable(witness) is False       # the Hurwitz horizon


def test_single_basis_always_navigable():
    reg = _reg()
    for j in range(1, DIM):                          # every basis e_j (one-hot)
        e = [Fraction(0)] * DIM
        e[j] = Fraction(1)
        assert reg.is_navigable(e) is True


# ── slot validation ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [-1, 16, 99])
def test_write_rejects_out_of_range_slot(bad):
    with pytest.raises(ValueError):
        _reg().write(bad, "x")
