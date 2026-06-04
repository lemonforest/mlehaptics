"""klein4_triality_cycle — the order-3 S₃ = Aut(V₄) generator (v0.6.0rc17).

The V₄-carrier image of the so(8) triality ``8v → 8s → 8c``
(:func:`srmech.qm.triality.triality_cycle`): the three non-identity Klein-4
involutions cycle ``iω₇(1) → γ₅(2) → CPT(3) → iω₇(1)``, identity(0) fixed.
Order 3 (``T∘T∘T = id``, ``T² = T⁻¹``). Class I — a pure uint8 relabel, no
sign / no ``abs()``. This is the "third axis" (F182) that the three order-2
flips cannot reach: order-3 cycling of the involutions, not a fourth order-2
chirality. rc17 ships it pure-Python; rc18 adds the co-equal C peer.
"""
import numpy as np
import pytest

from srmech.amsc import hdc


def _all_sectors():
    return np.array([0, 1, 2, 3], dtype=np.uint8)


def test_explicit_forward_mapping():
    # 0->0, 1->2, 2->3, 3->1  (the 3-cycle on {1,2,3}, identity fixed)
    out = hdc.klein4_triality_cycle(_all_sectors())
    assert out.tolist() == [0, 2, 3, 1]
    assert out.buffer.typecode == "B"  # uint8-backed (HV)


def test_explicit_inverse_mapping():
    # reverse cycle 1->3->2->1
    out = hdc.klein4_triality_cycle(_all_sectors(), inverse=True)
    assert out.tolist() == [0, 3, 1, 2]


def test_order_three_identity():
    v = _all_sectors()
    once = hdc.klein4_triality_cycle(v)
    twice = hdc.klein4_triality_cycle(once)
    thrice = hdc.klein4_triality_cycle(twice)
    assert (thrice == v), "T∘T∘T must be the identity (order 3)"


def test_square_equals_inverse():
    v = _all_sectors()
    twice = hdc.klein4_triality_cycle(hdc.klein4_triality_cycle(v))
    inv = hdc.klein4_triality_cycle(v, inverse=True)
    assert (twice == inv), "T² must equal T⁻¹"


def test_forward_then_inverse_is_identity():
    rng = np.random.default_rng(7)
    v = hdc.klein4_random(256, rng)
    rt = hdc.klein4_triality_cycle(hdc.klein4_triality_cycle(v), inverse=True)
    assert (rt == v)


def test_identity_sector_is_fixed():
    v = np.zeros(64, dtype=np.uint8)
    assert (hdc.klein4_triality_cycle(v).tolist() == [0] * len(v))


def test_is_a_permutation_of_the_three_involutions():
    # forward maps 1->2, 2->3, 3->1, so the occupancy of involution-2 after
    # the cycle equals involution-1 before, etc.; identity(0) is invariant.
    rng = np.random.default_rng(11)
    v = hdc.klein4_random(4096, rng)
    n0, n1, n2, n3 = hdc.klein4_sector_count(v)
    c0, c1, c2, c3 = hdc.klein4_sector_count(hdc.klein4_triality_cycle(v))
    assert c0 == n0
    assert (c2, c3, c1) == (n1, n2, n3)


def test_rejects_out_of_range():
    with pytest.raises(ValueError):
        hdc.klein4_triality_cycle(np.array([0, 1, 4], dtype=np.uint8))


def test_so8_triality_cycle_is_also_order_three():
    # the V₄-carrier op mirrors the so(8) rep-cycle's order-3 structure
    from srmech.qm.triality import triality_cycle

    assert triality_cycle(triality_cycle(triality_cycle("v"))) == "v"


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema()}
    assert "srmech.amsc.hdc.klein4_triality_cycle" in names
