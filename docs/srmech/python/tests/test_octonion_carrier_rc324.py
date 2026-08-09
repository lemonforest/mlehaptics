"""§𝕆 / rc324 — the ELEMENT_TYPE_OCTONION genome carrier PROVE-GATES.

The discrete octonion Moufang loop ``{±e₀, …, ±e₇}`` as 4-bit bytes
(:mod:`srmech.math.octonion`) is wired into the GENOME as a NEW ``element_type``
path (:data:`~srmech.biology.genome.ELEMENT_TYPE_OCTONION`) — the Cayley–Dickson rung
ABOVE Q₈, and it COEXISTS with the shipped klein4 (type 0) + Q₈ (type 1) paths,
byte-untouched. 𝕆 is globally NON-associative, but each slot holds ONE signed basis
unit and the Moufang loop has the INVERSE PROPERTY ``(x·y)·y⁻¹ = x``, so the
right-conjugate decouple round-trips byte-exact.

rc324 is the CARRIER (element-type registration + coupling/decoupling + the 4-bit
turn codec + the byte-exact C peers). The octonion associator / fiber-holonomy
channel that READS the non-associativity is a LATER rc — this file proves the
carrier can STORE the index-4..7 turns that later rc will read, and does NOT
compute the associator.

  1. Round-trip — recall(chromosome(leaves, one, 𝕆), one, 𝕆) == leaves, INCLUDING
     the non-quaternionic indices 4..7.
  2. Python↔C parity — oct_mult and the C peer match on ALL 256 basis-unit pairs;
     native couple/decouple == pure on ≥200 random strands; monkeypatch native→None
     and re-assert.
  3. Algebra pin — oct_mult matches cd_basis_product(8,·,·) AND the exact-rational
     full-vector cd_mult reduced to basis units.
  4. Non-quaternionic representable — a strand of indices 4..7 (e.g. e₄·e₅, e₆·e₇)
     round-trips; the carrier HOLDS the turns rc325 will read (no associator here).
  5. Backward-compat — klein4 (type 0) + Q₈ (type 1) strands still encode/decode/
     round-trip unchanged; a pre-rc324 strand still opens.
  6. Registration ratchet — the 3 carrier ops are tool-registered (tools.total 503)
     and present in __all__ + the tool schema.

numpy-free (``ctypes`` + stdlib only). The JPL Power-of-Ten audit of
``srmech_octonion_carrier.c`` rides the mechanical ratchet ``test_jpl_audit.py``.
"""
from __future__ import annotations

import ctypes
import random

import pytest

from tests._native_gate import require_native
from srmech import _native
from srmech.biology import genome as G
from srmech.math import octonion as O
from srmech.cascade.cayley_dickson import cd_basis_product, cd_mult
from srmech.biology.genome import (
    ELEMENT_TYPE_KLEIN4,
    ELEMENT_TYPE_OCTONION,
    ELEMENT_TYPE_Q8,
    OCT,
    OCTONION_SECTORS,
    QUAD,
    chromosome,
    quad_turn,
    recall,
    telomere,
)
from srmech.math.hdc import klein4_bind
from srmech.math.hv import HV
from srmech.math.octonion import oct_bind, oct_conjugate, oct_mult
from srmech.biology.q8 import q8_bind

ALL16 = range(16)


# ── the reference octonion product from cd_basis_product ──────────────────────
def _cd_oct_mult(a: int, b: int) -> int:
    """Reference octonion product built from the shipped cd_basis_product cocycle.

    A byte o encodes the signed basis unit (sign=o>>3, index=o&7). cd_basis_product
    supplies e_xa·e_xb = sign·e_idx (idx == xa^xb always); the result byte re-encodes
    it — the exact spec the carrier claims."""
    xa, xb = a & 7, b & 7
    sa, sb = a >> 3, b >> 3
    idx, sign = cd_basis_product(8, xa, xb)
    assert idx == (xa ^ xb)              # the ⊕ index lane is intrinsic to the cocycle
    sign_bit = 0 if sign == 1 else 1
    return ((sa ^ sb ^ sign_bit) << 3) | idx


def _byte_to_vec(o: int):
    """One octonion byte → its length-8 basis vector (±1 at index o&7)."""
    idx = o & 7
    sign = -1 if (o >> 3) else 1
    v = [0] * 8
    v[idx] = sign
    return v


def _vec_to_byte(v) -> int:
    """A single-nonzero ±1 length-8 vector → the octonion byte it encodes."""
    nz = [(i, int(val)) for i, val in enumerate(v) if int(val) != 0]
    assert len(nz) == 1, f"expected a single nonzero basis component; got {nz}"
    i, val = nz[0]
    assert val in (1, -1), f"basis-unit product must be ±1; got {val}"
    return ((0 if val == 1 else 1) << 3) | i


def _rand_oct_leaves(rng, n_leaves, leaf_dim, lo=0, hi=OCTONION_SECTORS):
    """``n_leaves`` random octonion leaves (sectors=16 HVs, bytes in [lo, hi))."""
    return [HV.from_sequence(bytes(rng.randrange(lo, hi) for _ in range(leaf_dim)),
                             sectors=OCTONION_SECTORS)
            for _ in range(n_leaves)]


def _rand_oct_one(rng, leaf_dim):
    return HV.from_sequence(bytes(rng.randrange(OCTONION_SECTORS) for _ in range(leaf_dim)),
                            sectors=OCTONION_SECTORS)


def _lists(hvs):
    return [h.tolist() for h in hvs]


# =====================================================================
# the octonion product IS genuine 𝕆 (group laws + non-associativity)
# =====================================================================
def test_oct_is_genuine_octonion_vs_cd_basis_product():
    for a in ALL16:
        for b in ALL16:
            assert oct_mult(a, b) == _cd_oct_mult(a, b)


def test_closure_and_identity():
    for a in ALL16:
        for b in ALL16:
            assert 0 <= oct_mult(a, b) < 16
        assert oct_mult(0, a) == a          # +e₀ left identity
        assert oct_mult(a, 0) == a          # +e₀ right identity


def test_imaginary_squares_are_minus_one():
    # e_i² = −1 (byte 8) for every imaginary unit — INCLUDING the non-quaternionic 4..7
    for i in range(1, 8):
        assert oct_mult(i, i) == 8
    assert oct_mult(8, 8) == 0              # (−1)² = +1


def test_octonion_is_non_associative():
    # the octonion associator is nonzero for ≥3 independent units: the canonical
    # e₁(e₂·e₄) ≠ (e₁·e₂)e₄ witness. (This is a PROPERTY of the product; the carrier
    # does not COMPUTE the associator — that is rc325.)
    left = oct_mult(1, oct_mult(2, 4))
    right = oct_mult(oct_mult(1, 2), 4)
    assert left != right, "the octonion product must be non-associative on independent units"
    # ... yet it stays ALTERNATIVE: a(ab) = (aa)b for any two units (Artin)
    for a in range(1, 8):
        for b in range(1, 8):
            assert oct_mult(a, oct_mult(a, b)) == oct_mult(oct_mult(a, a), b)


def test_conjugate_is_loop_inverse():
    for a in ALL16:
        ca = oct_conjugate(a)
        assert 0 <= ca < 16
        assert oct_mult(a, ca) == 0        # a · conj(a) = +e₀ (byte 0)
        assert oct_mult(ca, a) == 0        # conj(a) · a = +e₀ (Moufang inverse property)
        assert (ca & 7) == (a & 7)         # only the center sign moves


def test_conjugate_center_and_involution():
    assert oct_conjugate(0) == 0           # +1 self-inverse
    assert oct_conjugate(8) == 8           # −1 self-inverse
    assert oct_conjugate(5) == 13          # conj(+e₅) = −e₅  (5 ^ 8)
    assert oct_conjugate(13) == 5          # conj(−e₅) = +e₅
    for a in ALL16:
        assert oct_conjugate(oct_conjugate(a)) == a


# =====================================================================
# 3. ALGEBRA PIN — oct_mult vs cd_basis_product AND cd_mult (full vector)
# =====================================================================
def test_oct_mult_pins_to_cd_mult_full_vector():
    """oct_mult on basis units == the exact-rational full-vector octonion product
    cd_mult reduced back to a basis unit — the byte object IS the real octonion
    algebra, not a look-alike table."""
    for a in ALL16:
        for b in ALL16:
            prod_vec = cd_mult(_byte_to_vec(a), _byte_to_vec(b))
            assert _vec_to_byte(prod_vec) == oct_mult(a, b)
            # and cd_basis_product agrees on the index+sign
            idx, sign = cd_basis_product(8, a & 7, b & 7)
            assert idx == (oct_mult(a, b) & 7)
            assert (0 if sign == 1 else 1) == ((oct_mult(a, b) >> 3) ^ (a >> 3) ^ (b >> 3))


# =====================================================================
# the buffer op == the scalar op; validation
# =====================================================================
def test_bind_equals_elementwise_mult():
    turn = bytes([0, 1, 2, 7, 8, 9, 14, 15])
    one = bytes([1, 2, 4, 1, 5, 6, 7, 3])
    got = oct_bind(turn, one)
    assert got == bytes(oct_mult(turn[i], one[i]) for i in range(len(turn)))
    assert isinstance(got, bytes)


def test_empty_and_validation():
    assert oct_bind(b"", b"") == b""
    for bad in (-1, 16, 17, 255):
        with pytest.raises(ValueError):
            oct_mult(bad, 0)
        with pytest.raises(ValueError):
            oct_conjugate(bad)
    with pytest.raises(ValueError):
        oct_bind(b"\x00\x01", b"\x00")       # length mismatch
    with pytest.raises(ValueError):
        oct_bind([1, 2, 99], [0, 0, 0])      # non-octonion byte


# =====================================================================
# 2. PYTHON ↔ C PARITY
# =====================================================================
def test_native_is_actually_loaded():
    require_native("the octonion carrier's C peers")
    for sym in ("srmech_oct_mult", "srmech_oct_conjugate", "srmech_oct_bind"):
        assert hasattr(_native.LIB, sym), sym


def _all_scalar_results():
    mult = [[oct_mult(a, b) for b in ALL16] for a in ALL16]
    conj = [oct_conjugate(a) for a in ALL16]
    turn = bytes(range(16))
    one = bytes(reversed(range(16)))
    return mult, conj, oct_bind(turn, one)


def test_native_equals_pure_byte_for_byte(monkeypatch):
    require_native("the octonion native-vs-pure differential")
    native = _all_scalar_results()
    assert _native.HAS_NATIVE                      # sanity: the first pass used the C peers
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = _all_scalar_results()
    assert native == pure


def test_c_bind_out_may_alias_in_place():
    require_native("the C srmech_oct_bind out-aliasing contract")
    n = 8
    turn_vals = [0, 1, 2, 7, 8, 12, 14, 15]
    one_vals = [1, 1, 2, 2, 3, 4, 5, 6]
    expected = [oct_mult(turn_vals[i], one_vals[i]) for i in range(n)]
    buf = (ctypes.c_uint8 * n)(*turn_vals)         # out aliases turn
    one = (ctypes.c_uint8 * n)(*one_vals)
    rc = _native.LIB.srmech_oct_bind(buf, one, ctypes.c_uint32(n), buf)
    assert rc == _native.SRMECH_OK
    assert list(buf) == expected


def test_c_null_arg_rejected():
    require_native("the C srmech_oct_bind NULL-arg rejection")
    n = 4
    out = (ctypes.c_uint8 * n)()
    one = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_oct_bind(None, one, ctypes.c_uint32(n), out)
    assert rc == _native.SRMECH_ERR_NULL_ARG


def test_native_pure_parity_couple_over_random_strands(monkeypatch):
    """The octonion couple/decouple is byte-identical native vs pure over ≥200 random
    strands (definitional for the exact-integer product; the gate re-verifies it)."""
    rng = random.Random(32401)
    trials = 0
    for _ in range(220):
        leaf_dim = rng.randrange(8, 48)
        turn = bytes(rng.randrange(16) for _ in range(leaf_dim))
        one = bytes(rng.randrange(16) for _ in range(leaf_dim))
        native = oct_bind(turn, one)
        with monkeypatch.context() as m:
            m.setattr(_native, "HAS_NATIVE", False)
            pure = oct_bind(turn, one)
        assert native == pure
        # and the round-trip recovers exactly (Moufang inverse property, both paths)
        assert bytes(G._oct_uncouple_bytes(native, one)) == turn
        trials += 1
    assert trials == 220


# =====================================================================
# 1 + 4. ROUND-TRIP incl. non-quaternionic indices 4..7
# =====================================================================
def test_octonion_chromosome_recall_roundtrip():
    rng = random.Random(32402)
    trials = 0
    for _ in range(250):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 9)
        leaves = _rand_oct_leaves(rng, n_leaves, leaf_dim)
        one = _rand_oct_one(rng, leaf_dim)
        strand = chromosome(leaves, one, element_type=ELEMENT_TYPE_OCTONION)
        rec = recall(strand, one, element_type=ELEMENT_TYPE_OCTONION)
        assert _lists(rec) == _lists(leaves)
        assert all(all(0 <= b < OCTONION_SECTORS for b in h.tolist()) for h in rec)
        assert all(h.sectors == OCTONION_SECTORS for h in rec)
        trials += 1
    assert trials == 250


def test_non_quaternionic_indices_4_to_7_roundtrip():
    """A strand whose leaves live ENTIRELY in the non-quaternionic units e₄..e₇ (both
    signs → bytes {4,5,6,7,12,13,14,15}) round-trips exactly — the carrier HOLDS the
    turns rc325's associator will read. We do NOT compute the associator here."""
    rng = random.Random(32403)
    hi_bytes = [4, 5, 6, 7, 12, 13, 14, 15]
    for _ in range(120):
        leaf_dim = rng.randrange(16, 40)   # ≥ 11 so the 'chromosome' telomere label fits
        leaves = [HV.from_sequence(bytes(rng.choice(hi_bytes) for _ in range(leaf_dim)),
                                   sectors=OCTONION_SECTORS)
                  for _ in range(rng.randrange(1, 6))]
        one = _rand_oct_one(rng, leaf_dim)
        strand = chromosome(leaves, one, element_type=ELEMENT_TYPE_OCTONION)
        rec = recall(strand, one, element_type=ELEMENT_TYPE_OCTONION)
        assert _lists(rec) == _lists(leaves)
        # the leaves genuinely used indices 4..7 (would be UNREPRESENTABLE in Q₈)
        assert any(b & 7 >= 4 for h in leaves for b in h.tolist())
    # the loose products the carrier stored: e₄·e₅ and e₆·e₇ are real octonion turns
    assert oct_mult(4, 5) == _cd_oct_mult(4, 5)
    assert oct_mult(6, 7) == _cd_oct_mult(6, 7)


def test_quad_turn_unturn_octonion_involution_on_the_right_side():
    """quad_turn (right-couple) then _quad_unturn (right-conjugate decouple) is the
    identity for octonion — the shipped path asserts its own side and round-trips."""
    rng = random.Random(32404)
    for _ in range(100):
        leaf_dim = rng.randrange(8, 40)
        turn = _rand_oct_one(rng, leaf_dim)
        one = _rand_oct_one(rng, leaf_dim)
        stored = quad_turn(turn, one, element_type=ELEMENT_TYPE_OCTONION)  # asserts internally
        assert stored.sectors == OCTONION_SECTORS
        back = G._quad_unturn(stored, one, element_type=ELEMENT_TYPE_OCTONION)
        assert back.tolist() == turn.tolist()


def test_wrong_coupling_side_fails_loudly():
    """𝕆 is non-commutative: a LEFT-couple does NOT invert via the right-conjugate
    decouple, so _oct_side_ok is False and the shipped couple's HARD-ASSERT fires."""
    rng = random.Random(32405)
    leaf_dim = 96
    turn = bytearray(rng.randrange(16) for _ in range(leaf_dim))
    one = bytearray(rng.randrange(16) for _ in range(leaf_dim))
    turn[0], one[0] = 1, 2                          # e₁, e₂ anticommute → guaranteed side error
    turn, one = bytes(turn), bytes(one)
    right = oct_bind(turn, one)
    left = bytes(oct_mult(o, t) for t, o in zip(turn, one))
    assert left != right
    assert G._oct_side_ok(right, turn, one) is True
    assert G._oct_side_ok(left, turn, one) is False

    def _left_couple_with_guard(t, o):
        stored = bytes(oct_mult(oo, tt) for tt, oo in zip(t, o))
        assert G._oct_side_ok(stored, t, o), "octonion couple side error"
        return stored

    with pytest.raises(AssertionError):
        _left_couple_with_guard(turn, one)


# =====================================================================
# the 4-bit turn codec (carrier codec — directly round-tripped)
# =====================================================================
def test_octonion_turn_codec_roundtrip():
    rng = random.Random(32406)
    for leaf_dim in list(range(1, 40)) + [64, 127, 256]:
        block = bytes(rng.randrange(16) for _ in range(leaf_dim))
        packed = G._pack_turn_block_octonion(block)
        assert packed[0] == G.OCTONION_PACKED_TURN_MARKER
        assert len(packed) == 1 + G._packed_payload_len_octonion(leaf_dim)
        back = G._unpack_turn_payload_octonion(packed[1:], leaf_dim)
        assert bytes(back) == block


def test_octonion_codec_rejects_non_octonion_symbol():
    with pytest.raises(ValueError):
        G._pack_turn_block_octonion(bytes([0, 16, 3]))   # 16 is out of range


def test_octonion_marker_distinct_from_klein4_and_q8():
    markers = {G.PACKED_TURN_MARKER, G.Q8_PACKED_TURN_MARKER,
               G.OCTONION_PACKED_TURN_MARKER}
    assert len(markers) == 3
    assert G.OCTONION_PACKED_TURN_MARKER > 3      # never a klein4 data byte


# =====================================================================
# 5. BACKWARD-COMPAT — klein4 (type 0) + Q₈ (type 1) UNCHANGED
# =====================================================================
def test_klein4_backward_compat_unchanged():
    rng = random.Random(32407)
    for _ in range(80):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 7)
        leaves = [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)),
                                   sectors=QUAD) for _ in range(n_leaves)]
        one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)),
                               sectors=QUAD)
        for strand in (chromosome(leaves, one),
                       chromosome(leaves, one, element_type=ELEMENT_TYPE_KLEIN4)):
            data = [h for h in strand if G._cap_kind(h) is None]
            golden = [klein4_bind(leaf, one) for leaf in leaves]
            assert _lists(data) == _lists(golden)
            assert _lists(recall(strand, one)) == _lists(leaves)


def test_q8_backward_compat_unchanged():
    rng = random.Random(32408)
    for _ in range(80):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 7)
        leaves = [HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)),
                                   sectors=OCT) for _ in range(n_leaves)]
        one = HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)),
                               sectors=OCT)
        strand = chromosome(leaves, one, element_type=ELEMENT_TYPE_Q8)
        rec = recall(strand, one, element_type=ELEMENT_TYPE_Q8)
        assert _lists(rec) == _lists(leaves)
        # the Q₈ stored turns are still the plain q8_bind (no octonion leakage)
        data = [h for h in strand if G._cap_kind(h) is None]
        golden = [q8_bind(leaf.tobytes(), one.tobytes()) for leaf in leaves]
        assert [bytes(h.tolist()) for h in data] == [bytes(g) for g in golden]


def test_pre_rc324_strand_still_opens():
    """A strand built with NO element_type (the pre-rc324 default klein4 path) still
    recalls exactly — the octonion carrier is purely additive."""
    rng = random.Random(32409)
    leaf_dim = 32
    leaves = [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)),
                               sectors=QUAD) for _ in range(4)]
    one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
    cap = telomere("chromosome", dim=leaf_dim)
    strand = [cap] + [quad_turn(leaf, one) for leaf in leaves]   # default element_type
    assert _lists(recall(strand, one)) == _lists(leaves)


# =====================================================================
# 6. REGISTRATION RATCHET
# =====================================================================
def test_registration_ratchet():
    import srmech
    assert srmech.describe()["tools"]["total"] == 598
    for name in ("oct_mult", "oct_conjugate", "oct_bind"):
        assert name in O.__all__


def test_tool_schema_entries_present():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    for op in ("oct_mult", "oct_conjugate", "oct_bind"):
        assert f"srmech.math.octonion.{op}" in names


def test_element_type_registration():
    assert ELEMENT_TYPE_OCTONION == 2
    assert G._ELEMENT_TYPE_NAMES[ELEMENT_TYPE_OCTONION] == "octonion"
    assert G._ELEMENT_TYPE_CODES["octonion"] == 2
    assert OCTONION_SECTORS == 16 and OCT == 8      # OCT is NOT overloaded
