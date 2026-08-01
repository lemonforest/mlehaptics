"""rc237 (F2) — separate_winding_curvature: the ``the_one(σ,θ,w)`` WINDING
instance of rc236's ``separate_frame_curvature`` connection/curvature split.

fixed_frame = the w-INVARIANT adjoint (the unwound w=0 rep — the frame the
winding folds away in); curvature = the winding-HOLONOMY (the full ℤ³ grading
BEYOND the ±1 spinor_sign); is_flat = full-period-trivial (w == (0,0,0)), NOT
merely even-parity.

The NON-shell proof (the rc236 agent's shell-risk): the curvature record
DISTINGUISHES w=2 (tower (0,1)) from w=4 (tower (0,0,1)) — content the ±1
``spinor_sign`` CONFLATES (both Σ even → +1) — and calls BOTH curved. Only
w == (0,0,0) is flat. Exact + sound; numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.cascade.one import One, separate_winding_curvature, the_one


# ── fixed_frame = the w-INVARIANT adjoint (the unwound representative) ─────────

def test_fixed_frame_is_the_unwound_w0_representative():
    """The fixed frame is byte-identical to the unwound w=0 One's adjoint — the
    winding folds away in the frame (the 2π-periodic adjoint is w-BLIND)."""
    wound = the_one(+1, 3, 4, w=(2, 5, 7))
    unwound = the_one(+1, 3, 4, w=(0, 0, 0))
    res = separate_winding_curvature(wound)
    assert res["fixed_frame"] == unwound.to_flat_rational()
    # ...and the fixed frame does NOT depend on the winding at all.
    assert res["fixed_frame"] == wound.to_flat_rational()


def test_fixed_frame_is_14_exact_rationals():
    res = separate_winding_curvature(the_one(-1, 1, 1, w=(1, 0, 0)))
    ff = res["fixed_frame"]
    assert len(ff) == 14
    assert all(isinstance(n, int) and isinstance(d, int) for (n, d) in ff)


# ── is_flat: full-period-trivial (w == 0), NOT even-parity ────────────────────

def test_unwound_is_flat_with_zero_holonomy():
    res = separate_winding_curvature(the_one(+1, 5, 7, w=(0, 0, 0)))
    assert res["is_flat"] is True
    assert res["curvature"]["holonomy"] == 0
    assert res["curvature"]["winding"] == (0, 0, 0)
    assert res["curvature"]["spinor_sign"] == 1


def test_single_winding_is_not_flat():
    res = separate_winding_curvature(the_one(+1, 0, 1, w=(1, 0, 0)))
    assert res["is_flat"] is False
    assert res["curvature"]["holonomy"] == 1
    assert res["curvature"]["spinor_sign"] == -1        # (−1)^1


def test_even_parity_winding_is_still_curved_not_flat():
    """THE non-shell proof, part 1: a w=(2,0,0) has ``spinor_sign`` +1 (Σ even)
    — the naive Z/2 read would call it "trivial" — yet it is NOT flat: the
    winding carries a genuine holonomy the unwound rep does not."""
    res = separate_winding_curvature(the_one(+1, 0, 1, w=(2, 0, 0)))
    assert res["curvature"]["spinor_sign"] == 1         # the SHELL would say flat
    assert res["is_flat"] is False                      # the TRUTH: curved
    assert res["curvature"]["holonomy"] == 2


def test_w2_and_w4_share_spinor_sign_but_differ_in_curvature():
    """THE non-shell proof, part 2: w=2 and w=4 share ``spinor_sign`` +1, but
    the curvature record's divmod TOWERS distinguish them — content beyond the
    ±1 parity (the rc137 grading kept, not melded)."""
    r2 = separate_winding_curvature(the_one(+1, 0, 1, w=(2, 0, 0)))
    r4 = separate_winding_curvature(the_one(+1, 0, 1, w=(4, 0, 0)))
    # same shell (the conflation the ±1 sign would ship)
    assert r2["curvature"]["spinor_sign"] == r4["curvature"]["spinor_sign"] == 1
    # DIFFERENT genuine holonomy — the full ℤ³ grading, via the divmod towers
    assert r2["curvature"]["towers"][0] == (0, 1)       # 2 = 0b10
    assert r4["curvature"]["towers"][0] == (0, 0, 1)    # 4 = 0b100
    assert r2["curvature"]["towers"] != r4["curvature"]["towers"]
    assert r2["curvature"]["holonomy"] != r4["curvature"]["holonomy"]  # 2 vs 4
    # both are CURVED (both wound) — the shell would (wrongly) call both flat
    assert r2["is_flat"] is False and r4["is_flat"] is False


def test_retrograde_winding_holonomy_is_magnitude_not_signed():
    """A negative (retrograde) winding is Class-C orientation; its holonomy is
    the Class-K MAGNITUDE (never abs()), so it is non-zero and NOT flat."""
    res = separate_winding_curvature(the_one(+1, 0, 1, w=(-3, 0, 0)))
    assert res["is_flat"] is False
    assert res["curvature"]["holonomy"] == 3            # |−3|, Class-K magnitude
    assert res["curvature"]["winding"] == (-3, 0, 0)    # the signed grading kept


def test_multi_component_holonomy_sums_magnitudes():
    res = separate_winding_curvature(the_one(-1, 0, 1, w=(2, -3, 5)))
    assert res["curvature"]["holonomy"] == 2 + 3 + 5    # Σ |w_k|
    assert res["is_flat"] is False


# ── the One method mirrors the module-level function ─────────────────────────

def test_one_method_matches_module_function():
    one = the_one(+1, 2, 3, w=(1, 2, 3))
    assert one.separate_winding_curvature() == separate_winding_curvature(one)


def test_holonomy_and_flatness_are_exact_integers():
    """Exact: the holonomy is a Python int (int-in → int-magnitude-out), never a
    float — no numpy, no float shell."""
    res = separate_winding_curvature(the_one(+1, 0, 1, w=(7, 0, 0)))
    assert type(res["curvature"]["holonomy"]) is int
    assert res["curvature"]["holonomy"] == 7


def test_type_error_on_non_one():
    with pytest.raises(TypeError, match="expects a One"):
        separate_winding_curvature([[1, 0], [0, 1]])
    with pytest.raises(TypeError):
        separate_winding_curvature(42)


def test_record_shape():
    res = separate_winding_curvature(the_one(+1, 1, 1, w=(1, 0, 0)))
    assert set(res) == {"fixed_frame", "curvature", "is_flat"}
    assert set(res["curvature"]) == {
        "winding", "towers", "spinor_sign", "holonomy"}
    assert isinstance(res["is_flat"], bool)


def test_returns_a_one_that_is_a_one():
    """Sanity: the op takes the real carrier."""
    assert isinstance(the_one(+1, 0, 1), One)
