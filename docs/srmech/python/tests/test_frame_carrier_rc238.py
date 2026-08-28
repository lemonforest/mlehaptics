"""rc238 — the FRAME-CARRYING CARRIER (#1385 F-thread).

Proves the non-shell win: a 2π-periodic truncated Taylor series is exact WITHIN a
beat but DRIFTS across the 2π seam under the raw carrier; augmenting it with its
local beat-frame (sigma, winding) + a cross-seam compare that PARALLEL-TRANSPORTS
the frame makes the compare BIT-EXACT across the seam, with an exact is_aligned
certificate that is SOUND (a genuinely different value is never falsely aligned).

The frame-carry fixes a drift that winding_fold / the_one alone do NOT:
  * winding_fold returns a FLOAT residue (re-quantised) — it cannot feed the exact
    series the exact residue the fix needs; the transport here is an EXACT-rational
    2π divmod over the SAME Machin-2π anchor _EPH_TWO_PI.
  * the_one folds its winding AWAY in the 2π-periodic adjoint — it never carries a
    truncated-Taylor VALUE across a seam.

numpy-free; the values ride the c_dispatched Class-N sin/cos_series_truncate, the
transport the exact-rational Machin-2π fold, the residual the Class-K magnitude
(never abs()) — so native == pure is byte-identical by construction.
"""
from __future__ import annotations

import pytest

from srmech.cascade.frame_carrier import (
    frame_carrier,
    frame_carrier_compare,
)
from srmech.math.laplacian import _EPH_TWO_PI
from srmech.math.rational import sin_series_truncate, cos_series_truncate

# 2π and π as the EXACT Machin rationals the fold uses (den = 2^80). Building the
# across-seam arguments from these keeps the whole test exact-rational.
_2PI_N, _2PI_D = _EPH_TWO_PI            # 2π ≈ _2PI_N / _2PI_D
_PI_N, _PI_D = _2PI_N, 2 * _2PI_D      # π = 2π / 2


def _add_rat(a, b):
    (an, ad), (bn, bd) = a, b
    return (an * bd + bn * ad, ad * bd)


# ──────────────────────────────────────────────────────────────────────
# 1. THE non-shell win: raw drifts across the seam; the framed compare fixes it.
# ──────────────────────────────────────────────────────────────────────

def test_raw_series_drifts_across_the_2pi_seam():
    """The bare carrier: sin at theta and at theta+2π give DIFFERENT truncated
    rationals — exact within a beat, NOT bit-exact across the seam."""
    theta = (1, 2)                                    # 0.5 rad, within a beat
    theta_plus = _add_rat(theta, (_2PI_N, _2PI_D))    # 0.5 + 2π, across the seam
    raw_here = sin_series_truncate(theta[0], theta[1], 8)
    raw_there = sin_series_truncate(theta_plus[0], theta_plus[1], 8)
    assert raw_here != raw_there, (
        "precondition: the raw truncated series MUST drift across the 2π seam "
        "(else there is no drift to fix and the frame-carry is a shell)")


def test_frame_carry_fixes_the_seam_drift():
    """The framed compare across the 2π seam: raw_equal drifts (False), but
    transported_equal is bit-exact (True), and the cert says aligned."""
    theta = (1, 2)
    theta_plus = _add_rat(theta, (_2PI_N, _2PI_D))    # one 2π turn away
    cmp = frame_carrier_compare("sin", theta[0], theta[1],
                                theta_plus[0], theta_plus[1], 8)
    assert cmp["raw_equal"] is False          # the un-framed compare DRIFTS
    assert cmp["transported_equal"] is True   # the framed compare is BIT-EXACT
    assert cmp["aligned"] is True             # the exact certificate agrees
    assert cmp["residue_delta"] == (0, 1)     # zero holonomy residual
    assert cmp["transport_turns"] == -1       # exactly one 2π turn cranked
    assert cmp["transport_magnitude"] == 1


@pytest.mark.parametrize("turns", [1, 2, 3, 5])
def test_many_turns_all_transport_to_the_same_residue(turns):
    """ANY whole number of 2π turns folds to the identical residue → the framed
    compare is bit-exact for every winding, where the raw series drifts more."""
    theta = (3, 5)
    shifted = theta
    for _ in range(turns):
        shifted = _add_rat(shifted, (_2PI_N, _2PI_D))
    cmp = frame_carrier_compare("cos", theta[0], theta[1],
                                shifted[0], shifted[1], 10)
    assert cmp["raw_equal"] is False
    assert cmp["transported_equal"] is True
    assert cmp["aligned"] is True
    assert cmp["transport_turns"] == -turns
    assert cmp["transport_magnitude"] == turns


# ──────────────────────────────────────────────────────────────────────
# 2. SOUNDNESS — a genuinely different value is NEVER falsely aligned.
# ──────────────────────────────────────────────────────────────────────

def test_pi_shift_is_not_aligned_and_carries_a_real_residual():
    """sin(θ) vs sin(θ+π) = −sin(θ): a HALF turn (not a whole 2π) → not aligned,
    the transported values genuinely differ, and the residual is a real ≈π."""
    theta = (1, 2)
    theta_pi = _add_rat(theta, (_PI_N, _PI_D))
    cmp = frame_carrier_compare("sin", theta[0], theta[1],
                                theta_pi[0], theta_pi[1], 10)
    assert cmp["aligned"] is False
    assert cmp["transported_equal"] is False
    assert cmp["residue_delta"] != (0, 1)     # a genuine non-zero holonomy
    # the residual is ≈ π (a half-turn the transport could not remove)
    rn, rd = cmp["residue_delta"]
    assert abs(rn / rd) == pytest.approx(3.141592653589793, abs=1e-9)


def test_chirality_flip_is_not_aligned():
    """Same residue, opposite chirality σ: the values differ by sign → NOT
    aligned (the frame is (σ, w) — BOTH must match), soundly."""
    cmp = frame_carrier_compare("sin", 1, 2, 1, 2, 10, 1, -1)
    assert cmp["chirality_match"] is False
    assert cmp["aligned"] is False
    assert cmp["transported_equal"] is False   # σ·sin vs −σ·sin


def test_aligned_implies_transported_equal_cert_is_sound():
    """The certificate soundness direction: whenever `aligned` fires, the
    transported values ARE byte-identical — across a sweep of args / turns /
    chiralities, aligned never claims equality of unequal values."""
    args = [(0, 1), (1, 2), (3, 5), (-7, 4), (11, 3)]
    for func in ("sin", "cos"):
        for a in args:
            for turns in (0, 1, 2):
                b = a
                for _ in range(turns):
                    b = _add_rat(b, (_2PI_N, _2PI_D))
                for sa, sb in ((1, 1), (1, -1), (-1, -1)):
                    cmp = frame_carrier_compare(func, a[0], a[1], b[0], b[1],
                                                9, sa, sb)
                    if cmp["aligned"]:
                        assert cmp["transported_equal"] is True, (
                            f"FALSE ALIGNMENT: {func} {a}->{b} σ={sa},{sb}")


# ──────────────────────────────────────────────────────────────────────
# 3. Within a beat: the value is exact-as-today; the frame is trivial.
# ──────────────────────────────────────────────────────────────────────

def test_within_a_beat_value_equals_transported():
    """For |θ| ≤ π the winding is 0 and the residue IS the argument, so the raw
    value and the transported (canonical) value coincide — exact as today."""
    for func in ("sin", "cos"):
        for a in [(0, 1), (1, 2), (1, 1), (-1, 3)]:
            c = frame_carrier(func, a[0], a[1], 8)
            assert c["winding"] == 0
            assert c["residue"] == c["arg"]
            assert c["value"] == c["transported"]


def test_transported_value_is_the_series_at_the_residue():
    """Value-oracle (native == pure faithfulness): the transported leg is exactly
    σ·series(residue, N) — the composition adds no arithmetic of its own."""
    theta_plus = _add_rat((3, 4), (_2PI_N, _2PI_D))   # w = 1
    c = frame_carrier("sin", theta_plus[0], theta_plus[1], 8, -1)
    assert c["winding"] == 1
    rn, rd = c["residue"]
    on, od = sin_series_truncate(rn, rd, 8)
    assert c["transported"] == (-on, od)              # σ = -1 applied
    # and the raw value is the series at the UN-folded (drifting) argument
    vn, vd = sin_series_truncate(theta_plus[0], theta_plus[1], 8)
    assert c["value"] == (-vn, vd)
    assert c["value"] != c["transported"]             # the drift, made explicit


def test_cos_even_symmetry_is_conservative_but_sound():
    """cos(r) == cos(−r): the transported values coincide (cos is even) but the
    winding cert does NOT claim alignment (residues r ≠ −r) — a CONSERVATIVE
    False, never a false-alignment of DIFFERENT values (still sound)."""
    cmp = frame_carrier_compare("cos", 3, 5, -3, 5, 10)
    assert cmp["transported_equal"] is True    # genuine cos evenness
    assert cmp["aligned"] is False             # conservative: not a 2π turn


# ──────────────────────────────────────────────────────────────────────
# 4. Input validation (Class-K/C sign discipline on σ).
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [
    dict(func="tan"),           # not a 2π-periodic framed series
    dict(denominator=0),        # zero denominator
    dict(num_terms=-1),         # negative depth
    dict(sigma=0),              # σ must be ±1, never 0
    dict(sigma=2),              # σ must be ±1, never a bare truthy int
])
def test_frame_carrier_rejects_bad_input(bad):
    kw = dict(func="sin", numerator=1, denominator=2, num_terms=5, sigma=1)
    kw.update(bad)
    with pytest.raises((ValueError, TypeError)):
        frame_carrier(**kw)


# ──────────────────────────────────────────────────────────────────────
# 5. Registration: ToolEntry ×2, tools.total == 440, Rosetta rows, __all__.
# ──────────────────────────────────────────────────────────────────────

def test_registration_and_coverage():
    from srmech import introspect
    schema = introspect.describe()
    assert schema["tools"]["total"] == 679

    from srmech.introspect.tool_schema import get_tool_schema
    reg = {t.name for t in get_tool_schema().tools}
    assert "srmech.cascade.frame_carrier.frame_carrier" in reg
    assert "srmech.cascade.frame_carrier.frame_carrier_compare" in reg


def test_module_all_is_exactly_the_two_public_ops():
    import srmech.cascade.frame_carrier as fc
    assert set(fc.__all__) == {"frame_carrier", "frame_carrier_compare"}
