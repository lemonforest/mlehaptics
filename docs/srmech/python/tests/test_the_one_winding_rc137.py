"""v0.9.0rc137 — the One carries the WINDING w (gh#1276; the metacycle-fold fix).

``the_one(σ, θ)`` stored the ADJOINT ``cosθ·e₁ + sinθ·e_b`` (full-angle,
**2π-periodic → w-BLIND**: it FOLDS the winding away, addressing only the
epicycle). rc137 lifts SO→Spin (the double cover): it STORES the **spinor**
(half-angle, 4π-periodic) total-space state + carries the **winding TRIAD** w
WHOLE, with a **divmod binary-tower** chirality readout (NOT ``σ = w mod 2``).

This pins:
  (i)   the spinor state shows the winding — the (−1)^w double cover (1 winding
        flips, 2 restore);
  (ii)  the divmod binary tower — w carried WHOLE, ``winding_tower`` the graded
        bits, ``w=5 → (1,0,1)`` and ``w=7 → (1,1,1)`` DISTINGUISHED (not melded);
  (iii) the triad fills the 3 B/H/N anchors;
  (iv)  the ROSETTA-PRESERVING ADJOINT — ``to_matrix`` / ``to_flat_rational``
        w-INVARIANT AND rational-identical to the pre-winding the_one;
  (v)   ``unwrapped_phase`` lossless (2π·w + θ reconstructs);
  (vi)  the new readouts correct + JSON-native.
"""

from __future__ import annotations

import json

import pytest

from srmech.amsc.cascade import the_one, One, winding_tower
from srmech.amsc.cascade import one as one_mod
from srmech.amsc.rational import cos_series_truncate, sin_series_truncate


# ── (i) the SPINOR state shows the winding — the (−1)^w double cover ───────────

def test_spinor_stored_is_half_angle_exact():
    # The stored spinor is cos(θ/2) + Î sin(θ/2) at θ/2 = θ_num/(2·θ_den), exact.
    tn, td, terms = 1, 1, 22
    s = the_one(+1, tn, td, terms=terms)
    assert s.spinor[0] == cos_series_truncate(tn, 2 * td, terms)    # scalar cos(θ/2)
    assert s.spinor[1] == sin_series_truncate(tn, 2 * td, terms)    # Î-coeff σ·sin(θ/2)


def test_one_winding_flips_spinor_sign_two_restores():
    # The genuine double cover: w=1 flips the half-angle sign, w=2 restores.
    tn, td = 1, 1
    base = the_one(+1, tn, td, w=(0, 0, 0))
    w1 = the_one(+1, tn, td, w=(1, 0, 0))
    w2 = the_one(+1, tn, td, w=(2, 0, 0))
    assert base.spinor_sign == 1
    assert w1.spinor_sign == -1       # ONE winding → (−1)^1 = −1  (flip)
    assert w2.spinor_sign == 1        # TWO windings → (−1)^2 = +1 (restore, 4π)
    # the stored scalar spinor literally flips + restores
    b0n, b0d = base.spinor[0]
    assert w1.spinor[0] == (-b0n, b0d)      # sign flipped
    assert w2.spinor[0] == base.spinor[0]   # restored — identity at 4π


def test_trace_spinor_shows_the_winding():
    # The half-angle character 2·(−1)^Σw·cos(θ/2) flips with odd total winding —
    # the double-cover read a full-angle (2π-periodic) object CAN'T show.
    tn, td, terms = 2, 3, 24
    base = the_one(-1, tn, td, terms=terms).trace_spinor()
    flip = the_one(-1, tn, td, terms=terms, w=(1, 0, 0)).trace_spinor()
    restore = the_one(-1, tn, td, terms=terms, w=(2, 0, 0)).trace_spinor()
    assert flip == (-base[0], base[1])       # flipped
    assert restore == base                    # restored
    # trace_spinor is the SU(2)-style 2·cos(θ/2), distinct from the full-angle
    # to_scalar trace (which is w-blind); both are exact (num, den).
    two_cos = cos_series_truncate(tn, 2 * td, terms)
    from srmech.amsc.cascade.one import _reduce_rational
    assert base == _reduce_rational(2 * two_cos[0], two_cos[1])


def test_spinor_sign_driven_by_total_winding():
    # (−1)^Σw — the whole triad contributes to the double-cover sign.
    assert the_one(+1, 1, 1, w=(1, 1, 0)).spinor_sign == 1     # Σ=2 even
    assert the_one(+1, 1, 1, w=(1, 1, 1)).spinor_sign == -1    # Σ=3 odd
    assert the_one(+1, 1, 1, w=(4, 2, 0)).spinor_sign == 1     # Σ=6 even


# ── (ii) THE DIVMOD BINARY-TOWER — the grading kept, w=5 ≠ w=7 ─────────────────

def test_winding_tower_is_divmod_recursive_bits():
    # divmod(w,2)=(carry, bit) keeps BOTH; recurse → the LSB-first binary tower.
    assert winding_tower(0) == ()
    assert winding_tower(1) == (1,)
    assert winding_tower(2) == (0, 1)
    assert winding_tower(5) == (1, 0, 1)
    assert winding_tower(7) == (1, 1, 1)
    assert winding_tower(13) == (1, 0, 1, 1)


def test_winding_tower_anti_collapse_5_ne_7():
    # THE anti-collapse proof: w mod 2 MELDS 5≡7≡1 (throws the carry away). The
    # divmod tower keeps the whole GRADING → 5 and 7 are DISTINGUISHED.
    assert winding_tower(5) != winding_tower(7)          # (1,0,1) != (1,1,1)
    assert (5 % 2) == (7 % 2)                             # the melding quotient map
    assert winding_tower(5) == (1, 0, 1)
    assert winding_tower(7) == (1, 1, 1)


def test_winding_tower_lossless_reconstruction():
    # sum(bit << i) recovers the magnitude exactly (no information lost).
    for w in (0, 1, 2, 5, 7, 13, 223, 940):
        bits = winding_tower(w)
        assert sum(b << i for i, b in enumerate(bits)) == w


def test_winding_tower_negative_is_class_k_sign_no_abs():
    # A retrograde winding is the Class-C orientation reversal (-w), never abs();
    # the tower is over the magnitude (sign carried by σ / sigma_effective).
    assert winding_tower(-5) == winding_tower(5) == (1, 0, 1)


def test_one_winding_tower_method_per_component():
    o = the_one(+1, 0, 1, w=(5, 7, 2))
    assert o.winding_tower() == ((1, 0, 1), (1, 1, 1), (0, 1))


def test_winding_carried_whole_never_mod_collapsed():
    # w is a full ℤ per component — stored WHOLE, distinct 5 vs 7 survive.
    assert the_one(+1, 0, 1, w=(5, 0, 0)).winding == (5, 0, 0)
    assert the_one(+1, 0, 1, w=(7, 0, 0)).winding == (7, 0, 0)
    assert the_one(+1, 0, 1, w=(5, 0, 0)).winding != the_one(+1, 0, 1, w=(7, 0, 0)).winding


# ── sigma_effective — via the tower, NOT a bare parity ────────────────────────

def test_sigma_effective_via_tower_distinguishes_5_and_7():
    # σ modulated by the FULL popcount over the tower (every graded bit counts):
    # popcount(5)=2 (even → σ) vs popcount(7)=3 (odd → −σ) — DISTINGUISHED, where
    # the forbidden bare `w mod 2` (5≡7≡1) would MELD them.
    assert the_one(+1, 0, 1, w=(5, 0, 0)).sigma_effective() == +1     # popcount 2
    assert the_one(+1, 0, 1, w=(7, 0, 0)).sigma_effective() == -1     # popcount 3
    # the bare-parity readout the correction forbids WOULD collapse them:
    assert (5 % 2) == (7 % 2)


def test_sigma_effective_is_sigma_at_rest():
    # w=(0,0,0) → popcount 0 → exactly σ (back-compat).
    assert the_one(+1, 0, 1).sigma_effective() == +1
    assert the_one(-1, 0, 1).sigma_effective() == -1


# ── (iii) the triad fills the 3 B/H/N anchors ─────────────────────────────────

def test_winding_is_a_length_3_triad():
    o = the_one(+1, 0, 1, w=(223, 19, 76))
    assert isinstance(o.winding, tuple) and len(o.winding) == 3
    assert o.winding == (223, 19, 76)


def test_triad_maps_to_the_three_grammar_anchors():
    # The three windings fill the B/H/N ℝ·1 grammar anchors (Antikythera dials).
    o = the_one(+1, 5, 4, w=(1, 2, 3))
    phases = o.unwrapped_phase()
    assert [p["anchor"] for p in phases] == ["B", "H", "N"]
    assert [p["metacycle"] for p in phases] == ["saros", "metonic", "callippic"]
    assert [p["turns"] for p in phases] == [1, 2, 3]


@pytest.mark.parametrize("bad", [(1, 2), (1, 2, 3, 4), [1, 2], 5, "abc"])
def test_bad_winding_length_rejected(bad):
    with pytest.raises((ValueError, TypeError)):
        the_one(+1, 0, 1, w=bad)


def test_non_int_winding_component_rejected():
    with pytest.raises(TypeError):
        the_one(+1, 0, 1, w=(1.5, 0, 0))       # type: ignore[arg-type]


# ── (iv) THE ROSETTA-PRESERVING ADJOINT PROJECTION — w-invariant + identical ───

_THETAS = [(0, 1), (1, 1), (99, 100), (7, 3), (22, 7)]
_WINDINGS = [(0, 0, 0), (1, 0, 0), (5, 3, 1), (223, 19, 76), (7, 7, 7)]


@pytest.mark.parametrize("sigma", [+1, -1])
@pytest.mark.parametrize("tn,td", _THETAS)
def test_adjoint_flat_rational_is_w_invariant(sigma, tn, td):
    # The adjoint base folds the winding away — to_flat_rational is IDENTICAL for
    # every winding (the double-cover projection q → R(q) is 2π-periodic).
    baseline = the_one(sigma, tn, td).to_flat_rational()
    for w in _WINDINGS:
        assert the_one(sigma, tn, td, w=w).to_flat_rational() == baseline


@pytest.mark.parametrize("sigma", [+1, -1])
@pytest.mark.parametrize("tn,td", _THETAS)
def test_adjoint_matrix_is_w_invariant(sigma, tn, td):
    baseline = the_one(sigma, tn, td).to_matrix().tolist()
    for w in _WINDINGS:
        assert the_one(sigma, tn, td, w=w).to_matrix().tolist() == baseline


def test_adjoint_identical_to_pre_winding_the_one_for_default():
    # w defaults to (0,0,0) → byte-identical to the pre-winding the_one call
    # signature (the load-bearing back-compat proof).
    for sigma in (+1, -1):
        for tn, td in _THETAS:
            a = the_one(sigma, tn, td)                 # no w — the old call
            b = the_one(sigma, tn, td, w=(0, 0, 0))    # explicit rest
            assert a.to_flat_rational() == b.to_flat_rational()
            assert a.to_matrix().tolist() == b.to_matrix().tolist()
            # the anchors + n=1 σ-only structure are unchanged
            assert all(blk.real == (1, 1) for blk in a.blocks)
            assert a.n1_is_sigma_only is True


def test_to_scalar_trace_is_w_invariant():
    # The full-angle rotation character is w-blind (the adjoint is the base).
    base = the_one(+1, 5, 4).to_scalar(mode="trace")
    wound = the_one(+1, 5, 4, w=(9, 4, 2)).to_scalar(mode="trace")
    assert base == wound


# ── (v) unwrapped_phase — LOSSLESS 2π·w + θ ───────────────────────────────────

def test_unwrapped_phase_lossless_reconstruction():
    import math
    tn, td = 5, 4
    o = the_one(+1, tn, td, w=(3, 0, 2))
    phases = o.unwrapped_phase()
    theta = tn / td
    expected_turns = [3, 0, 2]
    for p, turns in zip(phases, expected_turns):
        assert p["turns"] == turns
        assert (p["theta_num"], p["theta_den"]) == (tn, td)
        # angle_k = 2π·turns + θ reconstructs exactly from the (turns, θ) pair.
        angle = 2 * math.pi * p["turns"] + p["theta_num"] / p["theta_den"]
        assert abs(angle - (2 * math.pi * turns + theta)) < 1e-12


def test_unwrapped_phase_reaches_what_theta_only_cannot():
    # A θ-only object folds the winding away → all three scales identical. Carrying
    # w makes the three metacycle cranks distinct (the fold #1276 recovers).
    o = the_one(+1, 1, 1, w=(1, 5, 9))
    turns = [p["turns"] for p in o.unwrapped_phase()]
    assert turns == [1, 5, 9]
    assert len(set(turns)) == 3


# ── (vi) the readouts are JSON-native ─────────────────────────────────────────

def test_winding_readouts_are_json_native():
    o = the_one(+1, 5, 4, w=(5, 7, 2))
    payload = {
        "winding": o.winding,
        "winding_tower": o.winding_tower(),
        "unwrapped_phase": o.unwrapped_phase(),
        "trace_spinor": o.trace_spinor(),
        "sigma_effective": o.sigma_effective(),
        "spinor_sign": o.spinor_sign,
        "spinor": o.spinor,
    }
    s = json.dumps(payload)
    assert json.loads(s)["winding"] == [5, 7, 2]
    assert json.loads(s)["sigma_effective"] == o.sigma_effective()


def test_trace_spinor_as_float_is_single_terminal_cast():
    o = the_one(+1, 1, 1, w=(0, 0, 0))
    num, den = o.trace_spinor()
    assert o.trace_spinor(as_float=True) == num / den


# ── numpy-absent + repr ───────────────────────────────────────────────────────

def test_repr_mentions_winding():
    r = repr(the_one(+1, 1, 1, w=(5, 0, 0)))
    assert "winding=(5, 0, 0)" in r
    assert "dim=14" in r


def test_the_one_alias_carries_winding():
    from srmech.amsc.cascade import s_generator
    assert s_generator(+1, 1, 1, w=(3, 0, 0)).winding == (3, 0, 0)
