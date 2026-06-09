"""klein4_project_axis — the iω₇-collapse / bipolar projection (v0.7.5rc47).

RBS-LM UPSTREAM_NOTES §18 Tier-2 leaf (F350/F354): the "asymptotic-DoF
render" — project a 2-DoF Klein-4 hypervector (γ₅ ⊕ iω₇) onto ONE chirality
axis, collapsing it to a 1-DoF bipolar {-1,+1} vector. The other axis (and its
self-error-correction) is dropped (F354 axis-split). Class K (bipolar sign
render) ∘ Class C (axis select); numpy-free pure bit ops.

These tests pin the bit-layout (γ₅ = bit 1, iω₇ = bit 0 — matching the
chirality-flip masks), the co-equal axis convention (both first-class, related
by a Class-K axis swap per the settable-chirality discipline), the bipolar
{-1,+1} render, and the F354 axis-split contract (the projection sees errors on
its kept axis but is blind to the projected-out axis).
"""

from __future__ import annotations

import pytest

from srmech.amsc.hdc import (
    HV,
    klein4_chirality_flip_gamma5,
    klein4_chirality_flip_omega7,
    klein4_project_axis,
    klein4_random,
)


def test_bit_layout_matches_flip_masks():
    """γ₅ = bit 1, iω₇ = bit 0 — the same layout the chirality flips use."""
    v = [0, 1, 2, 3]  # (γ₅,iω₇) = (0,0),(0,1),(1,0),(1,1)
    # γ₅ axis = bit 1: 0,0,1,1 → +1,+1,-1,-1
    assert klein4_project_axis(v, axis="gamma5") == [1, 1, -1, -1]
    # iω₇ axis = bit 0: 0,1,0,1 → +1,-1,+1,-1
    assert klein4_project_axis(v, axis="iomega7") == [1, -1, 1, -1]


def test_default_axis_is_gamma5():
    v = [0, 1, 2, 3]
    assert klein4_project_axis(v) == klein4_project_axis(v, axis="gamma5")


def test_output_is_bipolar():
    v = klein4_random(64, seed=7)
    for axis in ("gamma5", "iomega7"):
        proj = klein4_project_axis(v, axis=axis)
        assert all(x in (-1, 1) for x in proj)
        assert len(proj) == 64


def test_axes_are_co_equal_and_independent():
    """Each axis projects its OWN bit; the two are independent (F354)."""
    v = klein4_random(128, seed=11)
    g = klein4_project_axis(v, axis="gamma5")
    o = klein4_project_axis(v, axis="iomega7")
    # Per element, (gamma5_sign, iomega7_sign) recovers the original Klein-4
    # value bit-for-bit: bit1 = (1-g)//2, bit0 = (1-o)//2.
    recovered = [((1 - gs) // 2) * 2 + ((1 - os) // 2) for gs, os in zip(g, o)]
    assert recovered == list(v.tolist() if isinstance(v, HV) else v)


def test_gamma5_flip_negates_only_gamma5_projection():
    """A γ₅ flip flips the γ₅ projection sign; iω₇ projection unchanged (K-flip)."""
    v = klein4_random(96, seed=3)
    flipped = klein4_chirality_flip_gamma5(v)
    g0 = klein4_project_axis(v, axis="gamma5")
    g1 = klein4_project_axis(flipped, axis="gamma5")
    assert g1 == [-x for x in g0]                       # Class-K sign-flip
    assert klein4_project_axis(flipped, axis="iomega7") == \
        klein4_project_axis(v, axis="iomega7")          # other axis untouched


def test_omega7_flip_negates_only_omega7_projection():
    v = klein4_random(96, seed=5)
    flipped = klein4_chirality_flip_omega7(v)
    o0 = klein4_project_axis(v, axis="iomega7")
    o1 = klein4_project_axis(flipped, axis="iomega7")
    assert o1 == [-x for x in o0]
    assert klein4_project_axis(flipped, axis="gamma5") == \
        klein4_project_axis(v, axis="gamma5")


def test_accepts_hv_bytes_and_list():
    expect = [1, -1, 1, -1]  # iomega7 of [0,1,2,3]
    assert klein4_project_axis([0, 1, 2, 3], axis="iomega7") == expect
    assert klein4_project_axis(bytes([0, 1, 2, 3]), axis="iomega7") == expect
    assert klein4_project_axis(HV.from_sequence([0, 1, 2, 3]),
                               axis="iomega7") == expect


def test_bad_axis_rejected():
    for bad in ("nope", "g5", "", None, 1):
        with pytest.raises(ValueError):
            klein4_project_axis([0, 1, 2, 3], axis=bad)


def test_out_of_range_element_rejected():
    with pytest.raises(ValueError):
        klein4_project_axis([0, 1, 4], axis="gamma5")  # 4 ∉ {0,1,2,3}


def test_deterministic():
    v = klein4_random(32, seed=9)
    assert klein4_project_axis(v) == klein4_project_axis(v)


def test_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.hdc.klein4_project_axis" in names
