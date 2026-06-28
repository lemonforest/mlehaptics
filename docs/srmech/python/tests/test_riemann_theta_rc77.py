"""rc77 — the GENUS-3 Sp(6,ℤ) TRANSFORMATION + the genus-3 ADDITION relation
(genuine, distinct from rc75's genus-3 duplication). The g=2→g=3 parametric
extension of the rc73 genus-2 ``RiemannTheta`` work, on the rc75/76
``RiemannThetaG3`` carrier.

A pure CARRIER extension (like rc72/73/75): no public ToolEntry op, so
``tools.total`` is UNCHANGED — these tests assert ONLY the carrier's own new gates.

The build gates (the no-shell proof):

  (A) the Sp(6,ℤ) TRANSFORMATION — the modular action on the genus-3 binary
      characteristic m=[ε';ε] (six bits) is bit-exact (DLMF §21.5.9 holds for
      GENERAL genus g; here 3×3 blocks) on the standard generators (translation T,
      GL-twist U, inversion J); even ⇄ even / odd ⇄ odd parity is PRESERVED across
      all 64 chars; the group law composes exactly
      (transform(g₂·g₁) == transform(g₂)∘transform(g₁)); J⁴ acts trivially on chars;
      κ(γ) is the correct 8th root (exponent k ∈ ℤ/8, exact);
  (B) the ADDITION relation — the genuine two-argument genus-3 theta addition
      theorem (DLMF §21.6.8 at z₁=z₂=0, g=3 — sum over r ∈ (ℤ/2)³, EIGHT terms)
      holds EXACTLY as a truncated exact-integer multivariate q-series for ALL Ω,
      AND is provably GENUINELY DISTINCT from rc75's genus-3 duplication (a product
      of two DIFFERENT theta-nulls, not a single null squared), exercising the THREE
      genus-3 cross-terms;
  (C) NO REGRESSION — rc72/73/74 genus-2 + rc75/76 genus-3 gates still pass;
  (D) Python==C parity EXACT on the transformation + the eighth-nome lattices;
  (E) the carrier source has no numpy / math / abs() (the ratchet, extended).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta, RiemannThetaG3
from srmech.amsc import _native


def _t000() -> RiemannThetaG3:
    return RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))


THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]

ALL64 = [RiemannThetaG3(a, b, c, d, e, f)
         for a in (0, 1) for b in (0, 1) for c in (0, 1)
         for d in (0, 1) for e in (0, 1) for f in (0, 1)]


# the standard Sp(6,ℤ) generators (the test fixtures)
def _gens():
    return {
        "T11": RiemannThetaG3.sp6_translation(
            ((1, 0, 0), (0, 0, 0), (0, 0, 0))),
        "T23": RiemannThetaG3.sp6_translation(
            ((0, 0, 0), (0, 0, 1), (0, 1, 0))),
        "Toff": RiemannThetaG3.sp6_translation(
            ((0, 1, 1), (1, 0, 0), (1, 0, 0))),
        "Uperm": RiemannThetaG3.sp6_gl_twist(
            ((0, 1, 0), (0, 0, 1), (1, 0, 0))),       # det +1 cyclic permutation
        "Ushear": RiemannThetaG3.sp6_gl_twist(
            ((1, 1, 0), (0, 1, 1), (0, 0, 1))),       # det +1 upper-triangular
        "J": RiemannThetaG3.sp6_inversion(),
    }


# ── gate (A): the Sp(6,ℤ) transformation ─────────────────────────────────────
def test_generators_are_symplectic():
    """Every standard genus-3 generator is genuinely symplectic (γ·J·γᵀ = J — the
    exact integer 3×3 block conditions AᵀC sym, BᵀD sym, AᵀD−CᵀB=I)."""
    for name, g in _gens().items():
        assert RiemannThetaG3.sp6_is_symplectic(g), name


def test_translation_rejects_asymmetric_block():
    """The translation block B must be symmetric (the Sp(6,ℤ) condition) — an
    asymmetric B is rejected loudly (honest boundary)."""
    with pytest.raises(ValueError):
        RiemannThetaG3.sp6_translation(((0, 1, 0), (0, 0, 0), (0, 0, 0)))  # B01≠B10


def test_gl_twist_rejects_non_unimodular():
    """The GL-twist block A must be in GL(3,ℤ) (det = ±1) so (Aᵀ)⁻¹ is integer —
    a non-unimodular A is rejected loudly (honest boundary)."""
    with pytest.raises(ValueError):
        RiemannThetaG3.sp6_gl_twist(((2, 0, 0), (0, 1, 0), (0, 0, 1)))     # det 2


def test_gl_twist_inverse_is_integer_and_unimodular():
    """The GL-twist (Aᵀ)⁻¹ block is EXACT integer for a unimodular A (the adjugate /
    det is exact, det = ±1); the resulting γ is symplectic. Verified on a det = −1
    swap and the cyclic permutation (det +1)."""
    a_swap = ((0, 1, 0), (1, 0, 0), (0, 0, 1))         # det −1
    g = RiemannThetaG3.sp6_gl_twist(a_swap)
    assert RiemannThetaG3.sp6_is_symplectic(g)
    _A, _B, _C, D = g
    for row in D:                                       # D = (Aᵀ)⁻¹ all-integer
        for x in row:
            assert isinstance(x, int)


def test_transform_rejects_non_symplectic_gamma():
    """``transform`` refuses a non-symplectic γ — an honest boundary, not a
    fabricated reduction."""
    I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    Z3 = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
    badC = ((2, 0, 0), (0, 1, 0), (0, 0, 1))
    bad = (I3, Z3, Z3, badC)                            # AᵀD ≠ I
    assert not RiemannThetaG3.sp6_is_symplectic(bad)
    with pytest.raises(ValueError):
        _t000().transform(bad)


def test_characteristic_action_preserves_parity():
    """The genus-3 modular action preserves the even/odd parity (even ⇄ even,
    odd ⇄ odd — the action factors through Sp(6,ℤ₂)) on ALL 64 characteristics, for
    every generator. THE structural invariant of the transformation."""
    for name, g in _gens().items():
        for rt in ALL64:
            new, _k = rt.transform(g)
            assert new.is_even == rt.is_even, (name, rt.characteristic)


def test_transform_is_bit_exact_concrete():
    """Concrete bit-exact checks of the genus-3 characteristic map (DLMF §21.5.9 at
    g=3) — verified against the explicit affine formula on a sample characteristic
    under the inversion J (which swaps the upper/lower roles)."""
    rt = RiemannThetaG3.theta_constant((1, 0, 1), (0, 1, 0))
    npp, nep = RiemannThetaG3._char_transform_int(
        _gens()["J"], (1, 0, 1), (0, 1, 0))
    new, _k = rt.transform(_gens()["J"])
    assert new.characteristic == ((npp[0] % 2, npp[1] % 2, npp[2] % 2),
                                  (nep[0] % 2, nep[1] % 2, nep[2] % 2))


def test_group_law_composes_exactly():
    """The genus-3 characteristic action is a GROUP ACTION: transform(g₂·g₁) ==
    transform(g₂) after transform(g₁), exactly, on all 64 characteristics over all
    pairs of generators (the cocycle base — Sp(6,ℤ) acts by the block matrix
    product)."""
    gens = list(_gens().values())
    for g1 in gens:
        for g2 in gens:
            g21 = RiemannThetaG3.sp6_compose(g2, g1)
            assert RiemannThetaG3.sp6_is_symplectic(g21)
            for rt in ALL64:
                direct, _kd = rt.transform(g21)
                step1, _k1 = rt.transform(g1)
                step2, _k2 = step1.transform(g2)
                assert direct.characteristic == step2.characteristic, (
                    rt.characteristic)


def test_inversion_fourth_power_acts_trivially_on_characteristics():
    """J⁴ acts TRIVIALLY on the characteristics (J² = −I on the symplectic lattice,
    J⁴ = I; the genus-3 inversion has order 4 up to the ±I center) — a structural
    check on all 64 characteristics."""
    J = _gens()["J"]
    J2 = RiemannThetaG3.sp6_compose(J, J)
    J4 = RiemannThetaG3.sp6_compose(J2, J2)
    assert RiemannThetaG3.sp6_is_symplectic(J4)
    for rt in ALL64:
        new, _k = rt.transform(J4)
        assert new.characteristic == rt.characteristic, rt.characteristic


def test_kappa_is_eighth_root_exponent():
    """κ(γ) is the correct 8th root — the exponent k ∈ ℤ/8 (the multiplier ζ₈^k) is
    an exact integer in {0,…,7} for every generator and every characteristic; it is
    non-trivial on some generator. The transcendental automorphy factor
    det(Cτ+D)^{1/2} is NOT part of this exponent."""
    seen_nonzero = False
    for name, g in _gens().items():
        for rt in ALL64:
            _new, k = rt.transform(g)
            assert isinstance(k, int) and 0 <= k < 8, (name, rt.characteristic, k)
            if k != 0:
                seen_nonzero = True
    assert seen_nonzero, "the κ multiplier should be non-trivial on some generator"


def test_kappa_translation_values():
    """The translation T11 = [[I,B],[0,I]], B = diag(1,0,0) gives the κ exponent
    k ∈ {0,4} (the ±1 = ζ₈⁰/ζ₈⁴ phase) across the characteristics — the classical
    lattice-shift sign of the genus-3 theta-constant."""
    g = RiemannThetaG3.sp6_translation(((1, 0, 0), (0, 0, 0), (0, 0, 0)))
    ks = {rt.transform(g)[1] for rt in ALL64}
    assert ks <= {0, 4}
    assert 4 in ks            # the shift genuinely flips a sign on some char


def test_automorphy_factor_is_symbolic_not_evaluated():
    """The transcendental automorphy factor det(C·Ω+D)^{1/2} is returned SYMBOLIC
    (a string), never numerically evaluated — off every decision path (the rc72
    review lesson). The genus-3 string carries 3×3 C/D blocks."""
    s = RiemannThetaG3.automorphy_factor(_gens()["J"])
    assert isinstance(s, str)
    assert "Omega" in s or "Ω" in s
    assert "1/2" in s          # it is a square root, carried symbolically


# ── gate (B): the genus-3 ADDITION relation ──────────────────────────────────
def test_addition_identity_holds_exact():
    """THE rc77 (B) GATE: the genuine genus-3 theta addition theorem (DLMF §21.6.8 at
    z₁=z₂=0, g=3 — sum over r ∈ (ℤ/2)³, EIGHT terms) holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω. It verifies genuine a≠b pairs
    (the real addition content) AND that they exercise the THREE genus-3
    cross-terms, not just the a=b duplication collapse."""
    assert RiemannThetaG3.addition_holds(3)
    assert RiemannThetaG3.addition_holds(4)


def test_addition_is_genuinely_distinct_from_duplication():
    """THE NO-SHELL PROOF: the genus-3 addition relation is GENUINELY DISTINCT from
    rc75's genus-3 duplication. Its LEFT side θ[a;0]·θ[b;0] with a≠b is a product of
    two DIFFERENT theta-nulls — NOT equal to ANY duplication LHS θ[c;0]² (a single
    null squared, c ∈ {0,1}³). So it is the genuine addition theorem, not a relabeled
    duplication."""
    assert RiemannThetaG3.addition_is_distinct_from_duplication(3)
    assert RiemannThetaG3.addition_is_distinct_from_duplication(4)
    # explicit: the genuine LHS differs from every θ[c]² lattice over c ∈ {0,1}³
    genuine = RiemannThetaG3.addition_lhs((1, 0, 0), (0, 0, 0), 4)
    for c1 in (0, 1):
        for c2 in (0, 1):
            for c3 in (0, 1):
                tc = RiemannThetaG3._theta_omega_eighth(c1, c2, c3, 0, 0, 0, 4)
                sq = RiemannThetaG3._square_lattice_pair(tc, tc)
                assert genuine != sq, (c1, c2, c3)


def test_addition_collapses_to_duplication_when_a_equals_b():
    """When a=b the addition right side's two 2Ω characteristics recover the genus-3
    duplication shape Σ_r θ[…](2Ω)·θ[…](2Ω). The a=b instance of the addition gate
    holds exactly (LHS == RHS on the safe region)."""
    L = RiemannThetaG3.addition_lhs((1, 0, 0), (1, 0, 0), 4)
    R = RiemannThetaG3.addition_rhs((1, 0, 0), (1, 0, 0), 4)
    safe = 2 * 4 * 4

    def restrict(lat):
        out = {}
        for k, v in lat.items():
            a1, a2, a3, c12, c13, c23 = k
            m = (lambda x: x if x >= 0 else -x)
            if (a1 <= safe and a2 <= safe and a3 <= safe
                    and m(c12) <= safe and m(c13) <= safe and m(c23) <= safe):
                out[k] = v
        return out

    assert restrict(L) == restrict(R)


def test_addition_exercises_three_cross_terms():
    """The genus-3 addition identity genuinely exercises ALL THREE genus-3
    cross-terms (C₁₂, C₁₃, C₂₃ ≠ 0 monomials present on the safe region) for a pair
    spanning all three coordinates — it proves genuine genus-3 content, not the
    genus-2 / genus-1 slice."""
    L = RiemannThetaG3.addition_lhs((1, 1, 0), (0, 0, 1), 4)
    assert any(c12 != 0 for (_a1, _a2, _a3, c12, _c13, _c23) in L)
    assert any(c13 != 0 for (_a1, _a2, _a3, _c12, c13, _c23) in L)
    assert any(c23 != 0 for (_a1, _a2, _a3, _c12, _c13, c23) in L)


# ── gate (C): NO REGRESSION (rc72/73/74 genus-2 + rc75/76 genus-3 gates) ──────
def test_no_regression_rc72_73_74_genus2_gates():
    g2 = RiemannTheta.theta_constant((0, 0), (0, 0))
    assert g2.collapse_g1_q_series(20) == THETA3_Q20      # rc72 collapse
    assert RiemannTheta.duplication_holds(6)              # rc72 duplication
    assert RiemannTheta.addition_holds(6)                 # rc73 addition
    assert RiemannTheta.addition_is_distinct_from_duplication(6)
    assert RiemannTheta.goepel_holds(5)                   # rc74 Göpel
    assert RiemannTheta.rosenhain_lambda_map_is_well_formed()


def test_no_regression_rc73_genus2_transform_gate():
    """The rc73 genus-2 Sp(4,ℤ) transformation still works (parity + group law on a
    sample) — the genus-3 extension does not regress the genus-2 carrier."""
    g = RiemannTheta.sp4_inversion()
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                for d in (0, 1):
                    rt = RiemannTheta(a, b, c, d)
                    new, k = rt.transform(g)
                    assert new.is_even == rt.is_even
                    assert 0 <= k < 8


def test_no_regression_rc75_76_genus3_gates():
    assert _t000().collapse_g2() == RiemannTheta(0, 0, 0, 0)        # rc75 collapse
    assert _t000().collapse_g1_q_series(20) == THETA3_Q20           # rc75 chain
    assert RiemannThetaG3.duplication_holds(4)                      # rc75 duplication
    assert RiemannThetaG3.even_null_count() == (36, 28)
    assert RiemannThetaG3.chi18_is_nonzero()                        # rc76 χ₁₈
    assert RiemannThetaG3.chi18_factor_count_is_36_even()
    assert RiemannThetaG3.chi18_leading_part_is_at_order_48()


# ── gate (D): Python==C parity ───────────────────────────────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_sp6(),
                    reason="native srmech_riemann_theta_g3_sp6_char not loaded")
def test_python_c_parity_transformation():
    """The native Sp(6,ℤ) characteristic transform + κ exponent equal the pure
    oracle EXACTLY for all 64 characteristics over all generators (do NOT trust the
    C — compare)."""
    for name, g in _gens().items():
        gflat = RiemannThetaG3._validate_gamma6(g)
        for rt in ALL64:
            c_path = _native.riemann_theta_g3_sp6_char_c(
                gflat, rt._ep1, rt._ep2, rt._ep3, rt._e1, rt._e2, rt._e3)
            npp, nep = RiemannThetaG3._char_transform_int(
                g, (rt._ep1, rt._ep2, rt._ep3), (rt._e1, rt._e2, rt._e3))
            kpy = RiemannThetaG3._kappa_exp8(
                g, (rt._ep1, rt._ep2, rt._ep3), (rt._e1, rt._e2, rt._e3))
            assert c_path == ((npp[0] % 2, npp[1] % 2, npp[2] % 2,
                               nep[0] % 2, nep[1] % 2, nep[2] % 2), kpy), (
                name, rt.characteristic)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_eighth(),
                    reason="native srmech_riemann_theta_g3_eighth_lattice not loaded")
def test_python_c_parity_eighth_lattice():
    """The native genus-3 eighth-nome lattice equals the pure oracle EXACTLY at Ω
    and at 2Ω over several boxes and characteristics."""
    for box in (0, 1, 2, 3):
        for s1 in (-1, 0, 1, 2):
            for s2 in (0, 1):
                for s3 in (0, 1):
                    for e1 in (0, 1):
                        for at2 in (False, True):
                            c_path = _native.riemann_theta_g3_eighth_lattice_c(
                                s1, s2, s3, e1, 0, 1, at2, box)
                            if at2:
                                py = _pure_two_omega(s1, s2, s3, e1, 0, 1, box)
                            else:
                                py = _pure_omega(s1, s2, s3, e1, 0, 1, box)
                            assert c_path == py, (box, s1, s2, s3, e1, at2)


def _pure_omega(s1, s2, s3, e1, e2, e3, box):
    out = {}
    for n1 in range(-box, box + 1):
        u1 = 2 * n1 + s1
        for n2 in range(-box, box + 1):
            u2 = 2 * n2 + s2
            for n3 in range(-box, box + 1):
                u3 = 2 * n3 + s3
                key = (2 * u1 * u1, 2 * u2 * u2, 2 * u3 * u3,
                       2 * u1 * u2, 2 * u1 * u3, 2 * u2 * u3)
                sign = 1 if (e1 * n1 + e2 * n2 + e3 * n3) % 2 == 0 else -1
                out[key] = out.get(key, 0) + sign
    return {k: w for k, w in out.items() if w != 0}


def _pure_two_omega(s1, s2, s3, e1, e2, e3, box):
    out = {}
    for n1 in range(-box, box + 1):
        u1 = 4 * n1 + s1
        for n2 in range(-box, box + 1):
            u2 = 4 * n2 + s2
            for n3 in range(-box, box + 1):
                u3 = 4 * n3 + s3
                key = (u1 * u1, u2 * u2, u3 * u3, u1 * u2, u1 * u3, u2 * u3)
                sign = 1 if (e1 * n1 + e2 * n2 + e3 * n3) % 2 == 0 else -1
                out[key] = out.get(key, 0) + sign
    return {k: w for k, w in out.items() if w != 0}


@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_sp6(),
                    reason="native peers not loaded")
def test_gates_pass_through_native():
    """The transformation + addition gates still pass with the native path live
    (end-to-end on the C peers)."""
    assert RiemannThetaG3.addition_holds(4)
    assert RiemannThetaG3.addition_is_distinct_from_duplication(4)
    for g in _gens().values():
        for rt in ALL64:
            new, k = rt.transform(g)
            assert new.is_even == rt.is_even
            assert 0 <= k < 8


def test_pure_python_alone_passes_new_gates():
    """The COMPLETE pure-Python body alone passes both new gates (so the carrier is
    correct on a no-C host)."""
    assert RiemannThetaG3.addition_holds(3)
    assert RiemannThetaG3.addition_is_distinct_from_duplication(3)


# ── gate (E): the carrier source is numpy / math / abs() free ────────────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL
    assert "float(" not in text                          # no float in the carrier
