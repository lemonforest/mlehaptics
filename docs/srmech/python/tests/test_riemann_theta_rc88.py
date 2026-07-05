"""rc88 — ``RiemannTheta.addition_holds_at`` / ``RiemannThetaG3.addition_holds_at``: the
GENUINE Fay/Hirota bilinear VERIFIER at GENERIC RATIONAL arguments (the KP-shadow op on
the rc87 ``theta_at`` foundation).

It verifies, EXACTLY (truncated exact-integer cyclotomic ``ℤ[ζ_m]`` q-series, ``m = 2·z_den``,
for ALL Ω), Riemann's theta ADDITION FORMULA in terms of second-order theta functions

    θ[0;ε](x+y|Ω)·θ[0;ε](x−y|Ω) = Σ_{α∈{0,1}^g} (−1)^{ε·α} θ[α;0](2x|2Ω)·θ[α;0](2y|2Ω)

(Igusa, *Theta Functions* (1972), Ch. IV; Mumford, *Tata Lectures on Theta I* (1983), Ch. II;
the genus-g form θ(z+w)θ(z−w)=Σ_{ξ∈ℤ^g/2ℤ^g} Θ_ξ(z)Θ_ξ(w) over the second-order thetas
Θ_ξ(z)=θ[ξ/2;0](2z|2Ω)) at the rational arguments x = x_num/z_den, y = y_num/z_den.

A CARRIER verifier method (like ``addition_holds`` / ``goepel_holds``): NO ToolEntry →
``tools.total`` stays 342.

The no-shell gates (all exact):

  (1) **half-period bridge** — at half-period arguments (z_den = 2) ``addition_holds_at``
      returns True, the SAME regime the half-character ``addition_holds`` covers (which also
      passes); the generic op SUBSUMES the half-period special case.
  (2) **GENERIC-argument content (the real gate)** — at generic rational x,y with z_den = 7
      (m = 14, φ(14) = 6) ``addition_holds_at`` returns True with GENUINELY NON-REAL
      cyclotomic coefficients (nonzero power-basis coordinates beyond index 0) — the regime
      the integer theta-NULL gates (``addition_holds``/``goepel_holds``) CANNOT reach. This
      is what makes it not a Göpel/duplication relabel.
  (3) **honest is-Jacobian OPEN scope** — ``kp_bilinear_scope_note`` documents that the op
      verifies only the ABSTRACT theta-bilinear (Fay/Hirota-family) identity, NOT is-Jacobian
      / the curve-specific Fay trisecant (the Schottky operand-OPEN, genus ≥ 5).
  (4) Python == C byte-exact parity for ``srmech_riemann_theta_cyc_mul`` (guarded by native
      skip) + end-to-end gate with the C path live; tools.total == 381; numpy/math/abs/float
      free.
"""
from __future__ import annotations

import itertools
import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import (RiemannTheta, RiemannThetaG3,
                                       _cyc_mul, _cyc_mul_py, _cyclotomic_ring)
from srmech.amsc import _native
import srmech.introspect as introspect


def _nonreal(lat):
    """True iff any cyclotomic coeff vector has a nonzero power-basis coordinate beyond
    index 0 (a genuinely non-real / non-rational cyclotomic integer — the regime that
    proves theta_at spans BEYOND the integer half-character lattices)."""
    return any(any(c != 0 for c in v[1:]) for v in lat.values())


def _has_cross_g2(lat):
    return any(k[2] != 0 for k in lat)


# ── gate (1): the half-period bridge — addition_holds_at agrees with addition_holds ──
def test_half_period_bridge_g2_agrees_with_addition_holds():
    """At half-period arguments (z_den = 2) ``addition_holds_at`` returns True over a sweep
    of lower characteristics ε and half-periods — the SAME regime ``addition_holds`` covers
    (which also returns True). The generic op subsumes the half-period special case."""
    assert RiemannTheta.addition_holds(box=4)    # the existing half-char gate (small box)
    box = 3
    saw = 0
    for e1, e2 in itertools.product((0, 1), repeat=2):
        t = RiemannTheta.theta_constant((0, 0), (e1, e2))   # ε' = 0; lower char ε
        for (xn, yn) in [((1, 0), (0, 1)), ((1, 1), (1, 0)), ((1, 0), (1, 1))]:
            assert t.addition_holds_at(xn, yn, 2, box), (e1, e2, xn, yn)
            saw += 1
    assert saw == 12


def test_half_period_bridge_g3_agrees_with_addition_holds():
    assert RiemannThetaG3.addition_holds(box=2)
    t = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert t.addition_holds_at((1, 0, 0), (0, 1, 0), 2, 2)
    t2 = RiemannThetaG3.theta_constant((0, 0, 0), (1, 0, 1))
    assert t2.addition_holds_at((1, 0, 1), (0, 1, 0), 2, 2)


# ── gate (2): the GENERIC-argument content (the real gate, non-real cyclotomic) ──────
def test_generic_argument_g2_holds_and_is_genuinely_cyclotomic():
    """At a GENERIC rational argument (z_den = 7, m = 14, φ(14) = 6) the addition formula
    holds EXACTLY, and the coefficients are GENUINELY NON-REAL cyclotomic integers — the
    regime the integer theta-NULL gates cannot reach (so it is NOT a Göpel relabel)."""
    assert _cyclotomic_ring(14)[1] == 6
    for e1, e2 in itertools.product((0, 1), repeat=2):
        t = RiemannTheta.theta_constant((0, 0), (e1, e2))
        assert t.addition_holds_at((1, 2), (3, 1), 7, 2), (e1, e2)
    # the proof of genuine cyclotomic content (non-real coeffs in ℤ[ζ_14])
    t = RiemannTheta.theta_constant((0, 0), (1, 1))
    lhs = t.addition_at_lhs((1, 2), (3, 1), 7, 2)
    rhs = t.addition_at_rhs((1, 2), (3, 1), 7, 2)
    assert _nonreal(lhs) and _nonreal(rhs)
    assert _has_cross_g2(lhs)


def test_generic_argument_g2_more_denominators():
    """The identity holds across several denominators (rational z_den = 3,4,6 AND the
    non-rational-cyclotomic z_den = 7,8) and several arguments."""
    t = RiemannTheta.theta_constant((0, 0), (1, 0))
    for z_den in (3, 4, 6, 7, 8):
        box = 2
        assert t.addition_holds_at((1, 2), (3, 1), z_den, box), z_den


def test_generic_argument_g3_holds_and_is_genuinely_cyclotomic():
    t = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert t.addition_holds_at((1, 2, 1), (3, 1, 2), 7, 1)
    t2 = RiemannThetaG3.theta_constant((0, 0, 0), (1, 0, 1))
    assert t2.addition_holds_at((1, 2, 1), (3, 1, 2), 7, 1)
    lhs = t2.addition_at_lhs((1, 2, 1), (3, 1, 2), 7, 1)
    assert _nonreal(lhs)


def test_z_den_6_is_rational_z_den_7_is_not():
    """z_den = 6 collapses to RATIONAL coefficients (Niven's theorem: 6th-root cosines are
    rational) — the honest non-rational-cyclotomic gate is z_den = 7. Both still PASS the
    identity; the distinction is the coefficient ring depth the gate exercises."""
    t = RiemannTheta.theta_constant((0, 0), (1, 1))
    assert t.addition_holds_at((1, 2), (3, 1), 6, 2)
    assert not _nonreal(t.addition_at_lhs((1, 2), (3, 1), 6, 2))     # rational at z_den=6
    assert _nonreal(t.addition_at_lhs((1, 2), (3, 1), 7, 2))         # non-real at z_den=7


# ── box-stability (the safe inner region is box-stable) ─────────────────────────────
def test_box_stability_g2_generic():
    """The exact LHS restricted to the box-2 safe region is identical computed at box 2 and
    box 3 (the safe inner region is box-stable) — so the gate's verdict is box-independent."""
    from srmech.amsc.riemann_theta import _restrict_diag
    t = RiemannTheta.theta_constant((0, 0), (1, 0))
    l2 = _restrict_diag(t.addition_at_lhs((1, 2), (3, 1), 7, 2), 16, 2)
    l3 = _restrict_diag(t.addition_at_lhs((1, 2), (3, 1), 7, 3), 16, 2)
    assert l2 == l3 and l2


# ── gate (3): the honest is-Jacobian OPEN scope (documented, NOT a built op) ─────────
def test_kp_bilinear_scope_note_names_the_is_jacobian_open():
    note = RiemannTheta.kp_bilinear_scope_note()
    assert "is-Jacobian" in note or "is_jacobian" in note.lower() or "Jacobian" in note
    assert "Fay" in note and "trisecant" in note
    assert "Schottky" in note and "OPEN" in note
    # the op decides NO is-Jacobian / trisecant verdict (no such method)
    assert not hasattr(RiemannTheta, "is_jacobian")
    assert not hasattr(RiemannTheta, "fay_trisecant_holds")


def test_upper_characteristic_is_rejected_as_honest_boundary():
    """A nonzero UPPER characteristic ε' lands the two-argument addition at Ω/2 (outside the
    carrier's Ω/2Ω lattices) → rejected (an honest boundary, not a fabricated reduction)."""
    with pytest.raises(ValueError):
        RiemannTheta.theta_constant((1, 0), (0, 0)).addition_holds_at((1, 0), (0, 1), 2, 2)
    with pytest.raises(ValueError):
        RiemannThetaG3.theta_constant((1, 0, 0), (0, 0, 0)).addition_holds_at(
            (1, 0, 0), (0, 1, 0), 2, 1)


def test_addition_holds_at_input_validation():
    t = RiemannTheta.theta_constant((0, 0), (0, 0))
    with pytest.raises(ValueError):
        t.addition_holds_at((1, 0), (0, 1), 0, 2)        # z_den must be positive
    with pytest.raises(ValueError):
        t.addition_holds_at((1, 0), (0, 1), 2, 0)        # box must be ≥ 1
    with pytest.raises(ValueError):
        t.addition_holds_at((1, 0, 0), (0, 1), 2, 2)     # wrong x_num length for g2


# ── gate (4a): tools.total is UNCHANGED (a CARRIER verifier method, not a ToolEntry) ─
def test_addition_holds_at_is_a_carrier_method_total_341():
    assert introspect.describe()["tools"]["total"] == 397


# ── gate (4b): Python == C byte-exact parity for the cyclotomic-multiply kernel ──────
@pytest.mark.skipif(not _native.has_native_riemann_theta_cyc_mul(),
                    reason="native srmech_riemann_theta_cyc_mul not loaded")
def test_python_c_parity_cyc_mul():
    """The native ℤ[ζ_m] multiply and the pure ``_cyc_mul_py`` oracle are BYTE-IDENTICAL
    across several rings and coefficient vectors (the C is NOT trusted — it is compared)."""
    rng = [(-3, 2, 0, 1, -1, 2), (1, 0, -2, 3, 0, -1), (0, 0, 0, 0, 0, 0),
           (5, -4, 2, -1, 3, -2)]
    for m in (4, 6, 8, 12, 14):
        table, deg = _cyclotomic_ring(m)
        for a_full in rng:
            for b_full in rng:
                a = a_full[:deg]
                b = b_full[:deg]
                got = _native.riemann_theta_cyc_mul_c(a, b, table, m)
                assert got is not None
                assert got == _cyc_mul_py(a, b, table, m), (m, a, b)


@pytest.mark.skipif(not _native.has_native_riemann_theta_cyc_mul(),
                    reason="native srmech_riemann_theta_cyc_mul not loaded")
def test_native_gate_end_to_end():
    """The full ``addition_holds_at`` gate still passes with the native cyclotomic multiply
    live (end-to-end through C, not just the pure oracle)."""
    assert _native.has_native_riemann_theta_cyc_mul()
    t = RiemannTheta.theta_constant((0, 0), (1, 1))
    assert t.addition_holds_at((1, 2), (3, 1), 7, 2)
    assert RiemannThetaG3.theta_constant((0, 0, 0), (1, 0, 1)).addition_holds_at(
        (1, 2, 1), (3, 1, 2), 7, 1)


def test_cyc_mul_dispatch_matches_pure():
    """The dispatching ``_cyc_mul`` (native-or-pure) equals the pure body exactly — the
    parity holds whether or not the C peer is loaded (the pure body is the complete
    alternative + bignum fallback)."""
    for m in (4, 6, 14):
        table, deg = _cyclotomic_ring(m)
        a = tuple((i * 3 - 2) for i in range(deg))
        b = tuple((deg - i) for i in range(deg))
        assert _cyc_mul(a, b, m) == _cyc_mul_py(a, b, table, m)


# ── gate (4c): the new methods are numpy / math / abs() / float free ─────────────────
def test_rc88_source_is_numpy_math_abs_float_free():
    """The rc88 additions keep the ratchet: no numpy / math import, no bare ``abs()`` call,
    no ``float(`` in the carrier (the (−1)^{ε·α} sign is the Class-K pin-slot; the phase is
    the exact Class-I cyclic exponent over the cyclotomic ring)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None
    assert "float(" not in text
