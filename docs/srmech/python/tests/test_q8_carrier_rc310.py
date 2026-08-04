"""rc310 — the DISCRETE quaternion group Q8 = {±1, ±i, ±j, ±k} as 3-bit bytes:
the discrete peer of the continuous ℍ surface (``srmech.physics.qm.quaternion``).

The load-bearing proofs:

- ``test_q8_is_genuine_q8_vs_cd_basis_product`` — the Q8 product byte-table IS
  the signed-basis multiplication of the shipped Cayley–Dickson cocycle
  ``srmech.cascade.cayley_dickson.cd_basis_product`` at dim 4 (non-abelian,
  i²=j²=k²=−1, associative over all 8×8×8).
- ``test_pi_homomorphism_differential_contract`` — the abelian projection is
  EXACT: ``(q8_mult(a,b) & 3) == ((a&3) ^ (b&3))`` for all a,b, i.e. ``V4 = q&3``
  is the F380/R21 homomorphism ``π: Q8 → V4``; and it agrees with
  ``hdc.klein4_bind`` at the buffer level (``π(q8_bind(A,B)) ==
  klein4_bind(π A, π B)``) — why a future Q8-genome sequence-read is
  backward-faithful.
- ``test_native_equals_pure_byte_for_byte`` — the C peers ``srmech_q8_*`` are
  byte-for-byte identical to the pure paths on every input (these are EXACT
  integer ops, so parity is definitional; the gate re-verifies it).

numpy-free (``ctypes`` + stdlib only; the numpy-absent-venv guards elsewhere in
the suite verify numpy is genuinely absent). The JPL Power-of-Ten audit of
``srmech_q8.c`` rides the mechanical ratchet ``test_jpl_audit.py`` (the *.c glob).
"""
from __future__ import annotations

import ctypes

import pytest

from tests._native_gate import require_native
from srmech import _native
from srmech.biology import q8
from srmech.cascade.cayley_dickson import cd_basis_product
from srmech.math.hdc import klein4_bind

ALL8 = range(8)


# ── the reference Q8 table built straight from cd_basis_product ───────────────
def _cd_q8_mult(a: int, b: int) -> int:
    """Reference Q8 product built from the shipped cd_basis_product cocycle.

    A byte q encodes the signed basis unit (sign=q>>2, coset=q&3). The product
    of two signed units is (sa·e_xa)(sb·e_xb) = sa·sb·(e_xa·e_xb); cd_basis_product
    supplies e_xa·e_xb = sign·e_idx, and the result byte re-encodes it."""
    xa, xb = a & 3, b & 3
    sa, sb = a >> 2, b >> 2
    idx, sign = cd_basis_product(4, xa, xb)
    assert idx == (xa ^ xb)  # the V4 homomorphism is intrinsic to the cocycle
    sign_bit = 0 if sign == 1 else 1
    return ((sa ^ sb ^ sign_bit) << 2) | idx


# =====================================================================
# the Q8 product IS genuine Q8 (verified against cd_basis_product)
# =====================================================================
def test_q8_is_genuine_q8_vs_cd_basis_product():
    for a in ALL8:
        for b in ALL8:
            assert q8.q8_mult(a, b) == _cd_q8_mult(a, b)


def test_closure_and_identity():
    for a in ALL8:
        for b in ALL8:
            p = q8.q8_mult(a, b)
            assert 0 <= p < 8
        assert q8.q8_mult(0, a) == a          # left identity
        assert q8.q8_mult(a, 0) == a          # right identity


def test_non_abelian():
    # the canonical witnesses: i·j = k (+k=3), j·i = −k (7)
    assert q8.q8_mult(1, 2) == 3
    assert q8.q8_mult(2, 1) == 7
    assert any(q8.q8_mult(a, b) != q8.q8_mult(b, a) for a in ALL8 for b in ALL8)


def test_imaginary_squares_are_minus_one():
    # i²=j²=k²=−1  (byte 4 = −1)
    assert q8.q8_mult(1, 1) == 4
    assert q8.q8_mult(2, 2) == 4
    assert q8.q8_mult(3, 3) == 4
    # and (−1)² = +1
    assert q8.q8_mult(4, 4) == 0


def test_associativity_over_all_8x8x8():
    m = q8.q8_mult
    for a in ALL8:
        for b in ALL8:
            for c in ALL8:
                assert m(m(a, b), c) == m(a, m(b, c))


# =====================================================================
# the conjugate is the group inverse (and an involution)
# =====================================================================
def test_conjugate_is_group_inverse():
    for a in ALL8:
        ca = q8.q8_conjugate(a)
        assert 0 <= ca < 8
        assert q8.q8_mult(a, ca) == 0     # a · conj(a) = 1 (byte 0)
        assert q8.q8_mult(ca, a) == 0     # conj(a) · a = 1
        # the center (±1) is self-inverse; imaginary cosets flip only the sign
        assert (ca & 3) == (a & 3)


def test_conjugate_is_involution():
    for a in ALL8:
        assert q8.q8_conjugate(q8.q8_conjugate(a)) == a


def test_conjugate_center_is_fixed():
    assert q8.q8_conjugate(0) == 0   # +1 self-inverse
    assert q8.q8_conjugate(4) == 4   # −1 self-inverse
    assert q8.q8_conjugate(1) == 5   # conj(+i) = −i
    assert q8.q8_conjugate(5) == 1   # conj(−i) = +i


# =====================================================================
# the π: Q8 → V4 homomorphism — the load-bearing differential contract
# =====================================================================
def test_pi_homomorphism_differential_contract():
    # (a·b) & 3 == (a&3) ^ (b&3) for all a, b — V4 is the EXACT abelian
    # projection (the F380/R21 homomorphism π: Q8 → V4 = Z2 × Z2).
    for a in ALL8:
        for b in ALL8:
            assert (q8.q8_mult(a, b) & 3) == ((a & 3) ^ (b & 3))


def test_project_v4_is_coset_read():
    q = bytes(ALL8)
    assert q8.q8_project_v4(q) == bytes(x & 3 for x in ALL8)


def test_q8_projects_to_klein4_bind():
    # π(q8_bind(A, B)) == klein4_bind(π A, π B) over the full 8×8 pair grid:
    # V4 collapses this NON-abelian module exactly onto hdc.klein4's abelian
    # value algebra (the reason the sequence-read is backward-faithful).
    A = bytes(a for a in ALL8 for _ in ALL8)
    B = bytes(b for _ in ALL8 for b in ALL8)
    pi_prod = q8.q8_project_v4(q8.q8_bind(A, B))
    bridge = klein4_bind(q8.q8_project_v4(A), q8.q8_project_v4(B))
    assert bytes(pi_prod) == bytes(bridge)


# =====================================================================
# the buffer ops == the scalar ops
# =====================================================================
def test_bind_equals_elementwise_mult():
    turn = bytes([0, 1, 2, 3, 4, 5, 6, 7])
    one = bytes([1, 2, 3, 1, 2, 3, 1, 2])
    got = q8.q8_bind(turn, one)
    assert got == bytes(q8.q8_mult(turn[i], one[i]) for i in range(len(turn)))
    assert isinstance(got, bytes)


def test_bind_accepts_list_and_bytearray():
    assert q8.q8_bind([1, 2, 3], bytearray([2, 1, 3])) == bytes(
        [q8.q8_mult(1, 2), q8.q8_mult(2, 1), q8.q8_mult(3, 3)])


def test_empty_buffers():
    assert q8.q8_bind(b"", b"") == b""
    assert q8.q8_project_v4(b"") == b""


# =====================================================================
# native == pure, BYTE-FOR-BYTE (the parity gate)
# =====================================================================
def _all_results():
    mult = [[q8.q8_mult(a, b) for b in ALL8] for a in ALL8]
    conj = [q8.q8_conjugate(a) for a in ALL8]
    turn = bytes([0, 1, 2, 3, 4, 5, 6, 7])
    one = bytes([7, 6, 5, 4, 3, 2, 1, 0])
    bind = q8.q8_bind(turn, one)
    proj = q8.q8_project_v4(bytes(ALL8))
    return mult, conj, bind, proj


def test_native_is_actually_loaded():
    # a meaningful parity gate needs the native peers present
    require_native("the Q₈ carrier's C peers")
    for sym in ("srmech_q8_mult", "srmech_q8_conjugate",
                "srmech_q8_bind", "srmech_q8_project_v4"):
        assert hasattr(_native.LIB, sym), sym


def test_native_equals_pure_byte_for_byte(monkeypatch):
    require_native("the Q₈ native-vs-pure differential")
    native = _all_results()
    assert _native.HAS_NATIVE  # sanity: the first pass used the C peers
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = _all_results()
    assert native == pure


# =====================================================================
# the C out-aliasing contract (in-place bind / project) — direct ctypes
# =====================================================================
def test_c_bind_out_may_alias_in_place():
    if not _native.HAS_NATIVE or not hasattr(_native.LIB, "srmech_q8_bind"):
        pytest.skip("native srmech_q8_bind not available")
    n = 8
    turn_vals = [0, 1, 2, 3, 4, 5, 6, 7]
    one_vals = [1, 1, 2, 2, 3, 3, 1, 2]
    expected = [q8.q8_mult(turn_vals[i], one_vals[i]) for i in range(n)]
    buf = (ctypes.c_uint8 * n)(*turn_vals)   # out aliases turn
    one = (ctypes.c_uint8 * n)(*one_vals)
    rc = _native.LIB.srmech_q8_bind(buf, one, ctypes.c_uint32(n), buf)
    assert rc == _native.SRMECH_OK
    assert list(buf) == expected


def test_c_null_arg_rejected():
    if not _native.HAS_NATIVE or not hasattr(_native.LIB, "srmech_q8_project_v4"):
        pytest.skip("native srmech_q8_project_v4 not available")
    n = 4
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_q8_project_v4(None, ctypes.c_uint32(n), out)
    assert rc == _native.SRMECH_ERR_NULL_ARG


# =====================================================================
# input validation (the Python surface)
# =====================================================================
@pytest.mark.parametrize("bad", [-1, 8, 9, 255])
def test_mult_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        q8.q8_mult(bad, 0)
    with pytest.raises(ValueError):
        q8.q8_conjugate(bad)


def test_bind_length_mismatch_rejected():
    with pytest.raises(ValueError):
        q8.q8_bind(b"\x00\x01", b"\x00")


def test_buffer_rejects_non_q8_byte():
    with pytest.raises(ValueError):
        q8.q8_bind([1, 2, 99], [0, 0, 0])
    with pytest.raises(ValueError):
        q8.q8_project_v4([0, 8])


# =====================================================================
# registration ratchet
# =====================================================================
def test_registration_ratchet():
    import srmech
    assert srmech.describe()["tools"]["total"] == 543
    for name in ("q8_mult", "q8_conjugate", "q8_bind", "q8_project_v4"):
        assert name in q8.__all__


def test_tool_schema_entries_present():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    for op in ("q8_mult", "q8_conjugate", "q8_bind", "q8_project_v4"):
        assert f"srmech.biology.q8.{op}" in names
