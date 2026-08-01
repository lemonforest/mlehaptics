"""rc330 (`#948` Thread A) — the CORE per-rung CARRIER-ARITHMETIC surface on
``CDRegister``.

rc297 brought the general N-slot register in-tree as an ADDRESSING object; rc301
added the two OPT value-layers (coupling / EC). rc330 surfaces the register's
held Cayley–Dickson ELEMENT and the exact-rational carrier arithmetic over it as
a CORE (always-on) read-only surface: :meth:`~CDRegister.element` /
:meth:`~CDRegister.norm` / :meth:`~CDRegister.conjugate` /
:meth:`~CDRegister.multiply` / :meth:`~CDRegister.add`.

The design (proven by the #948 Thread-A prototype and enforced here):

  * A register slot holds a content NAME + a Class-C sign, magnitude implicit 1,
    so the element a register HOLDS is the signed-basis-unit sum
    ``x = Σ_{i occupied} sign_i·e_i`` (coefficients in ``{-1, 0, +1}``). The KEY
    is ORTHOGONAL — the carrier reads only ``(index, sign)`` via ``slots()``.
  * Each method DELEGATES to the already-C-backed exact-``Q``
    :mod:`~srmech.amsc.cascade.cayley_dickson` ops — no new algebra, no new C
    symbol, no ToolEntry (``composition_of_c``, exactly like ``couple_working``
    is the method-form of ``cd_couple_working``). So the gate is EXACT parity vs
    calling ``cd_norm_sq`` / ``cd_conjugate`` / ``cd_mult`` / ``cd_add`` directly.
  * Design forks (decided): ``multiply`` / ``add`` / ``conjugate`` return a
    ``Q``-tuple (a product / sum of signed-basis sums is generally NOT signed-
    basis, so it cannot round-trip into a coefficient-free slot register);
    ``norm`` returns a ``Q`` scalar; operands are two registers (symmetric).
  * CORE means ALWAYS ON: a bare register (coupling / EC both off) answers the
    carrier arithmetic — the contrast with the GATED ``couple_working`` is
    pinned in :func:`test_carrier_surface_is_core_not_gated`.

Landmines (both asserted):
  1. At dim 16 the carrier ``.multiply()`` is ``cd_mult`` (a WELL-DEFINED
     sedenion product, ``0`` on a zero-divisor pair), NEVER ``couple_working``
     (the ≤7 octonion coupler, which RAISES on the sedenion's 15 slots).
  2. ``CDRegister(16, namespace="SEDENION")`` stays bit-faithful to
     ``SedenionRegister()`` on read / slots — the new methods add no per-instance
     state, so the rc297 oracle equivalence is untouched.

numpy-free (imports only srmech + stdlib); no ``abs()`` (the cascade-honesty AST
scan in ``test_cd_register_rc297.py`` covers the whole module, these methods
included).
"""
from __future__ import annotations

import pytest

from srmech.math.q import Q
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.amsc.cascade.cd_register import CDRegister, cd_couple_working
from srmech.amsc.cascade.sedenion_register import SedenionRegister

# The rungs the carrier surface is proven exact on (2 ℂ / 4 ℍ / 8 𝕆 / 16 𝕊).
CARRIER_RUNGS = (2, 4, 8, 16)


def _mk_reg(dim, occupied):
    """A ``CDRegister`` with ``occupied = {slot: sign}`` written in."""
    r = CDRegister(dim=dim, namespace=f"RC330_{dim}")
    for slot, sign in occupied.items():
        r.write(slot, f"k{slot}", sign=sign)
    return r


def _expected_element(dim, occupied):
    """The coefficient vector built DIRECTLY from the spec — independent of the
    register's internal slot map (the non-tautological expectation)."""
    v = [Q(0)] * dim
    for slot, sign in occupied.items():
        v[slot] = Q(int(sign))
    return tuple(v)


# A deterministic per-dim occupancy roster (a spread of ±1 signs across slots).
_CASES = {
    2:  [{0: 1, 1: 1}, {0: 1, 1: -1}, {1: 1}],
    4:  [{0: 1, 1: 1, 2: 1}, {1: 1, 2: -1}, {3: 1}],
    8:  [{0: 1, 1: 1, 4: 1}, {1: 1, 2: 1, 3: 1}, {7: 1}],
    16: [{0: 1, 3: -1, 10: 1}, {1: 1, 10: 1}, {4: 1, 15: -1}, {8: -1, 12: 1}],
}


# ──────────────────────────────────────────────────────────────────────
# §A  the write→slots()→element() round-trip is FAITHFUL (non-tautological)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", CARRIER_RUNGS)
def test_element_roundtrip_reproduces_the_spec(dim):
    """``element()`` after a ``write`` round-trip reproduces the coefficient
    vector built DIRECTLY from the spec — the accessor is faithful, and its
    length is exactly ``dim``."""
    for occ in _CASES[dim]:
        reg = _mk_reg(dim, occ)
        el = reg.element()
        assert len(el) == dim
        assert el == _expected_element(dim, occ)
        # every coefficient is a Q in {-1, 0, +1} (the signed-basis element)
        assert all(c == 0 or c == 1 or c == -1 for c in el)


# ──────────────────────────────────────────────────────────────────────
# §B  EXACT parity of norm / conjugate / multiply / add vs cd_* directly
#     (the delegation gate — dim 2 / 4 / 8 / 16)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", CARRIER_RUNGS)
def test_norm_parity(dim):
    for occ in _CASES[dim]:
        reg = _mk_reg(dim, occ)
        got = reg.norm()
        want = cd.cd_norm_sq(reg.element())
        assert got == want
        assert isinstance(got, Q)
        # every occupied coeff is ±1, so N(x) == #occupied
        assert got == Q(len(occ))


@pytest.mark.parametrize("dim", CARRIER_RUNGS)
def test_conjugate_parity(dim):
    for occ in _CASES[dim]:
        reg = _mk_reg(dim, occ)
        got = reg.conjugate()
        want = cd.cd_conjugate(reg.element())
        assert got == want
        assert len(got) == dim
        # conjugate of a signed-basis element is still signed-basis (only
        # imaginary-slot signs flip), so it COULD round-trip into a register
        assert all(c == 0 or c == 1 or c == -1 for c in got)


@pytest.mark.parametrize("dim", CARRIER_RUNGS)
def test_multiply_parity(dim):
    cases = _CASES[dim]
    for occ_a in cases:
        ra = _mk_reg(dim, occ_a)
        for occ_b in cases:
            rb = _mk_reg(dim, occ_b)
            got = ra.multiply(rb)
            want = cd.cd_mult(ra.element(), rb.element())
            assert got == want
            assert len(got) == dim
        # symmetric operands: multiply(other) reads other's element the same way
        # element() reads self's — no asymmetry in how the two are consumed
        assert ra.multiply(ra) == cd.cd_mult(ra.element(), ra.element())


@pytest.mark.parametrize("dim", CARRIER_RUNGS)
def test_add_parity(dim):
    cases = _CASES[dim]
    for occ_a in cases:
        ra = _mk_reg(dim, occ_a)
        for occ_b in cases:
            rb = _mk_reg(dim, occ_b)
            got = ra.add(rb)
            want = cd.cd_add(ra.element(), rb.element())
            assert got == want
            assert len(got) == dim
            # add is commutative at the carrier level
            assert ra.add(rb) == rb.add(ra)


# ──────────────────────────────────────────────────────────────────────
# §C  hand-computed algebra anchors — pin the surface to KNOWN mathematics
#     (independent of cd_mult; textbook Cayley–Dickson products)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim,occ_a,occ_b,expect,label", [
    (2,  {1: 1}, {1: 1}, {0: -1}, "C:  i·i = -1"),
    (4,  {1: 1}, {2: 1}, {3: 1},  "H:  i·j = k"),
    (4,  {2: 1}, {1: 1}, {3: -1}, "H:  j·i = -k"),
    (4,  {3: 1}, {3: 1}, {0: -1}, "H:  k·k = -1"),
    (8,  {1: 1}, {2: 1}, {3: 1},  "O:  e1·e2 = e3"),
    (8,  {1: 1}, {4: 1}, {5: 1},  "O:  e1·e4 = e5"),
])
def test_hand_computed_anchors(dim, occ_a, occ_b, expect, label):
    """The register carrier ``.multiply()`` reproduces textbook basis products —
    so parity is pinned to KNOWN mathematics, not just internal self-consistency."""
    got = _mk_reg(dim, occ_a).multiply(_mk_reg(dim, occ_b))
    assert got == _expected_element(dim, expect), label


# ──────────────────────────────────────────────────────────────────────
# §D  LANDMINE 1 — the dim-16 carrier multiply is cd_mult, NOT couple_working
# ──────────────────────────────────────────────────────────────────────

def test_dim16_zero_divisor_multiply_is_zero_and_well_defined():
    """The zero-divisor witness x = e1+e10, y = e4−e15 (both NONZERO, norm 2)
    multiplies to the all-zero element through the register carrier surface — a
    WELL-DEFINED sedenion product (via cd_mult), byte-identical to calling
    cd_mult directly. Norm is NOT multiplicative here (N(x·y)=0 while
    N(x)·N(y)=4), which is exactly the object past the Hurwitz wall."""
    w = cd.sedenion_zero_divisor_witness()
    x, y = w["x"], w["y"]
    assert w["x_norm_sq"] == Q(2) and w["y_norm_sq"] == Q(2)   # both nonzero

    # build two dim-16 registers from the ±1 witness coefficients
    rx = CDRegister(dim=16, namespace="RC330_16")
    ry = CDRegister(dim=16, namespace="RC330_16")
    for i, c in enumerate(x):
        if c != 0:
            rx.write(i, f"x{i}", sign=int(c))
    for i, c in enumerate(y):
        if c != 0:
            ry.write(i, f"y{i}", sign=int(c))

    prod = rx.multiply(ry)
    assert all(c == 0 for c in prod)                      # a well-defined product
    assert prod == cd.cd_mult(x, y)                       # == direct cd_mult
    # both operands' norms are 2 → N(x)·N(y)=4, but N(x·y)=0 (composition fails)
    assert rx.norm() == Q(2) and ry.norm() == Q(2)


def test_dim16_couple_working_raises_on_the_sedenion_slots():
    """couple_working at dim 16 is Hurwitz-pinned at cap 7 (the octonion's 7
    imaginary slots), so it structurally CANNOT couple the sedenion's 15 slots —
    it RAISES. It is a DIFFERENT operation from a per-rung carrier multiply; the
    carrier multiply rides cd_mult, which the previous test showed is defined on
    exactly the pair couple_working cannot even accept."""
    from srmech.amsc.cascade.cd_register import _working_cap
    assert _working_cap(16) == 7                          # NOT 15

    # via the module function (the prototype's probe)
    with pytest.raises(ValueError):
        cd_couple_working([1.0] * 15, dim=16)

    # via the gated register method (coupling opted in) — same Hurwitz cap
    reg = CDRegister(dim=16, namespace="RC330_16", coupling=True)
    with pytest.raises(ValueError):
        reg.couple_working([1.0] * 15)


# ──────────────────────────────────────────────────────────────────────
# §E  LANDMINE 2 — the SEDENION oracle equivalence is untouched by the surface
# ──────────────────────────────────────────────────────────────────────

def test_sedenion_oracle_equivalence_preserved():
    """CDRegister(16, namespace="SEDENION") still matches SedenionRegister() on
    read / slots — the rc330 methods are pure reads over slots() that add NO
    per-instance state, so the rc297 faithfulness gate holds. The carrier surface
    reads the SAME slot map the oracle exposes."""
    cdr = CDRegister(dim=16, namespace="SEDENION", D=512)
    sed = SedenionRegister(D=512)
    occ = {0: 1, 1: -1, 5: 1, 9: 1, 12: -1}
    for s, sign in occ.items():
        cdr.write(s, f"v{s}", sign=sign)
        sed.write(s, f"v{s}", sign=sign)

    # bit-exact read on every slot + identical slot maps (the oracle gate)
    assert all(cdr.read(s) == sed.read(s) for s in range(16))
    assert cdr.slots() == sed.slots()

    # the carrier surface reads that SAME slot map — element / norm are a pure
    # read over slots(); norm == #occupied (each coeff ±1)
    assert cdr.element() == _expected_element(16, occ)
    assert cdr.norm() == Q(len(occ))


# ──────────────────────────────────────────────────────────────────────
# §F  the carrier surface is CORE (always on), unlike the GATED coupling layer
# ──────────────────────────────────────────────────────────────────────

def test_carrier_surface_is_core_not_gated():
    """A BARE register (coupling=False, error_correction=False) answers the
    carrier arithmetic — it is CORE, always on. The contrast: couple_working is
    an OPT layer and RAISES on a bare register. This is what makes element / norm
    / conjugate / multiply / add different from the value-operations."""
    bare = _mk_reg(8, {1: 1, 2: 1})
    assert bare._coupling is False and bare._error_correction is False

    # CORE carrier arithmetic works on the bare register
    assert bare.norm() == Q(2)
    assert bare.conjugate() == cd.cd_conjugate(bare.element())
    other = _mk_reg(8, {2: 1})
    assert bare.multiply(other) == cd.cd_mult(bare.element(), other.element())
    assert bare.add(other) == cd.cd_add(bare.element(), other.element())

    # the GATED coupling layer RAISES on the same bare register
    with pytest.raises(ValueError):
        bare.couple_working([1.0, 2.0])


def test_multiply_and_add_reject_dim_mismatch_and_non_register():
    """Symmetric-operand contract: both take another CDRegister of the same dim;
    a dim mismatch or a non-register operand is rejected loudly."""
    a = _mk_reg(4, {1: 1})
    b16 = _mk_reg(16, {1: 1})
    with pytest.raises(ValueError):
        a.multiply(b16)
    with pytest.raises(ValueError):
        a.add(b16)
    with pytest.raises(TypeError):
        a.multiply(a.element())          # a Q-tuple, not a CDRegister
    with pytest.raises(TypeError):
        a.add(a.element())


if __name__ == "__main__":                                   # pragma: no cover
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
