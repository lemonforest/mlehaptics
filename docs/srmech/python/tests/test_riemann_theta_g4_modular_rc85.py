"""rc85 — the GENUS-4 Sp(8,ℤ) MODULAR ACTION KIT (closes the genus-ladder gap):
``RiemannThetaG4`` gains the SAME modular-action surface g2/g3 already expose —
transform / sp8 generators / automorphy / addition / Göpel. The g=3→g=4 parametric
extension of the rc77/rc78 genus-3 work, on the rc80 ``RiemannThetaG4`` carrier.

A pure CARRIER extension (like rc72/73/75/77/78): no public ToolEntry op, so
``tools.total`` is UNCHANGED (stays 342) — these tests assert ONLY the carrier's own
new gates.

The build gates (the no-shell proof):

  (A) the Sp(8,ℤ) TRANSFORMATION — the modular action on the genus-4 binary
      characteristic m=[ε';ε] (eight bits) is bit-exact (DLMF §21.5.9 holds for
      GENERAL genus g; here 4×4 blocks) on the standard generators (translation T,
      GL-twist U, inversion J); even ⇄ even / odd ⇄ odd parity is PRESERVED across
      all 256 chars; the group law composes exactly
      (transform(g₂·g₁) == transform(g₂)∘transform(g₁)); J⁴ acts trivially on chars;
      κ(γ) is the correct 8th root (exponent k ∈ ℤ/8, exact);
  (B) the ADDITION relation — the genuine two-argument genus-4 theta addition
      theorem (DLMF §21.6.8 at z₁=z₂=0, g=4 — sum over r ∈ (ℤ/2)⁴, SIXTEEN terms)
      holds EXACTLY as a truncated exact-integer multivariate q-series for ALL Ω,
      AND is provably GENUINELY DISTINCT from the genus-4 duplication, exercising the
      genus-4 cross-terms;
  (C) the universal GÖPEL relation — an 8-pair / 16-null same-Ω quadratic theta-null
      relation holds EXACTLY and is genuinely syzygous (a Göpel system);
  (D) collapse-to-g3 CONSISTENCY — transform commutes with collapse_g3 where the g3
      sub-block embeds;
  (E) NO REGRESSION — rc80/rc81 genus-4 + rc75–78 genus-3 gates still pass;
  (F) Python==C parity EXACT on the transformation + the eighth-nome lattices + the
      Göpel decision;
  (G) the carrier source has no numpy / math / abs().
"""
from __future__ import annotations

import itertools
import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import (
    RiemannTheta, RiemannThetaG3, RiemannThetaG4)
from srmech.amsc import _native


def _t0() -> RiemannThetaG4:
    return RiemannThetaG4.theta_constant((0, 0, 0, 0), (0, 0, 0, 0))


# the four standard Sp(8,ℤ) generators (the test fixtures)
def _gens():
    return {
        "T11": RiemannThetaG4.sp8_translation(
            ((1, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
        "Toff": RiemannThetaG4.sp8_translation(
            ((0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1), (0, 0, 1, 0))),
        "Uperm": RiemannThetaG4.sp8_gl_twist(
            ((0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1), (1, 0, 0, 0))),  # det ±1 cycle
        "Ushear": RiemannThetaG4.sp8_gl_twist(
            ((1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1))),  # det +1 unitri
        "J": RiemannThetaG4.sp8_inversion(),
    }


# a SAMPLE of the 256 characteristics (full enumeration where cheap; a 32-sample where
# the gate is per-char heavy). The deterministic first-32 lexicographic sample.
ALL256 = [RiemannThetaG4(*bits) for bits in itertools.product((0, 1), repeat=8)]
SAMPLE = ALL256[:32] + ALL256[-8:]


# ── gate (A): the Sp(8,ℤ) transformation ─────────────────────────────────────
def test_generators_are_symplectic():
    """Every standard genus-4 generator is genuinely symplectic (γ·J·γᵀ = J — the
    exact integer 4×4 block conditions AᵀC sym, BᵀD sym, AᵀD−CᵀB=I)."""
    for name, g in _gens().items():
        assert RiemannThetaG4.sp8_is_symplectic(g), name


def test_compose_product_is_symplectic():
    """A composed product J·Ushear is genuinely symplectic (the group law preserves
    the symplectic condition)."""
    g = RiemannThetaG4.sp8_compose(_gens()["J"], _gens()["Ushear"])
    assert RiemannThetaG4.sp8_is_symplectic(g)


def test_non_symplectic_is_rejected():
    """A deliberately non-symplectic 8×8 (AᵀD ≠ I) is NOT symplectic and transform
    refuses it — an honest boundary."""
    I4 = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    Z4 = ((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))
    badC = ((2, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    bad = (I4, Z4, Z4, badC)                            # AᵀD ≠ I
    assert not RiemannThetaG4.sp8_is_symplectic(bad)
    with pytest.raises(ValueError):
        _t0().transform(bad)


def test_translation_rejects_asymmetric_block():
    """The translation block B must be symmetric (the Sp(8,ℤ) condition) — an
    asymmetric B is rejected loudly (honest boundary)."""
    with pytest.raises(ValueError):
        RiemannThetaG4.sp8_translation(
            ((0, 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)))  # B01≠B10


def test_gl_twist_rejects_non_unimodular():
    """The GL-twist block A must be in GL(4,ℤ) (det = ±1) so (Aᵀ)⁻¹ is integer —
    a non-unimodular A is rejected loudly (honest boundary)."""
    with pytest.raises(ValueError):
        RiemannThetaG4.sp8_gl_twist(
            ((2, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))   # det 2


def test_gl_twist_inverse_is_integer_and_unimodular():
    """The GL-twist (Aᵀ)⁻¹ block is EXACT integer for a unimodular A (the adjugate /
    det is exact, det = ±1); the resulting γ is symplectic. Verified on a det = −1
    swap."""
    a_swap = ((0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))  # det −1
    g = RiemannThetaG4.sp8_gl_twist(a_swap)
    assert RiemannThetaG4.sp8_is_symplectic(g)
    _A, _B, _C, D = g
    for row in D:                                       # D = (Aᵀ)⁻¹ all-integer
        for x in row:
            assert isinstance(x, int)


def test_characteristic_action_preserves_parity():
    """The genus-4 modular action preserves the even/odd parity (even ⇄ even,
    odd ⇄ odd — the action factors through Sp(8,ℤ₂)) on ALL 256 characteristics, for
    every generator. THE structural invariant of the transformation."""
    for name, g in _gens().items():
        for rt in ALL256:
            new, _k = rt.transform(g)
            assert new.is_even == rt.is_even, (name, rt.characteristic)


def test_transform_is_bit_exact_concrete():
    """A concrete bit-exact check of the genus-4 characteristic map (DLMF §21.5.9 at
    g=4) — verified against the explicit affine formula on a sample characteristic
    under the inversion J (which swaps the upper/lower roles)."""
    rt = RiemannThetaG4.theta_constant((1, 0, 1, 0), (0, 1, 0, 1))
    npp, nep = RiemannThetaG4._char_transform_int(
        _gens()["J"], (1, 0, 1, 0), (0, 1, 0, 1))
    new, _k = rt.transform(_gens()["J"])
    assert new.characteristic == (
        (npp[0] % 2, npp[1] % 2, npp[2] % 2, npp[3] % 2),
        (nep[0] % 2, nep[1] % 2, nep[2] % 2, nep[3] % 2))


def test_group_law_composes_exactly():
    """The genus-4 characteristic action is a GROUP ACTION: transform(g₂·g₁) ==
    transform(g₂) after transform(g₁), exactly, on a sample of characteristics over
    all pairs of generators (the cocycle base — Sp(8,ℤ) acts by the block matrix
    product)."""
    gens = list(_gens().values())
    for g1 in gens:
        for g2 in gens:
            g21 = RiemannThetaG4.sp8_compose(g2, g1)
            assert RiemannThetaG4.sp8_is_symplectic(g21)
            for rt in SAMPLE:
                direct, _kd = rt.transform(g21)
                step1, _k1 = rt.transform(g1)
                step2, _k2 = step1.transform(g2)
                assert direct.characteristic == step2.characteristic, (
                    rt.characteristic)


def test_inversion_fourth_power_acts_trivially_on_characteristics():
    """J⁴ acts TRIVIALLY on the characteristics (J² = −I on the symplectic lattice,
    J⁴ = I) — a structural check on all 256 characteristics."""
    J = _gens()["J"]
    J2 = RiemannThetaG4.sp8_compose(J, J)
    J4 = RiemannThetaG4.sp8_compose(J2, J2)
    assert RiemannThetaG4.sp8_is_symplectic(J4)
    for rt in ALL256:
        new, _k = rt.transform(J4)
        assert new.characteristic == rt.characteristic, rt.characteristic


def test_kappa_is_eighth_root_exponent():
    """κ(γ) is the correct 8th root — the exponent k ∈ ℤ/8 (the multiplier ζ₈^k) is
    an exact integer in {0,…,7} for every generator and every characteristic; it is
    non-trivial on some generator. The transcendental automorphy factor
    det(Cτ+D)^{1/2} is NOT part of this exponent."""
    seen_nonzero = False
    for name, g in _gens().items():
        for rt in ALL256:
            _new, k = rt.transform(g)
            assert isinstance(k, int) and 0 <= k < 8, (name, rt.characteristic, k)
            if k != 0:
                seen_nonzero = True
    assert seen_nonzero, "the κ multiplier should be non-trivial on some generator"


def test_kappa_translation_values():
    """The translation T11 = [[I,B],[0,I]], B = diag(1,0,0,0) gives the κ exponent
    k ∈ {0,4} (the ±1 = ζ₈⁰/ζ₈⁴ phase) across the characteristics — the classical
    lattice-shift sign of the genus-4 theta-constant."""
    g = RiemannThetaG4.sp8_translation(
        ((1, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)))
    ks = {rt.transform(g)[1] for rt in ALL256}
    assert ks <= {0, 4}
    assert 4 in ks            # the shift genuinely flips a sign on some char


def test_automorphy_factor_is_symbolic_not_evaluated():
    """The transcendental automorphy factor det(C·Ω+D)^{1/2} is returned SYMBOLIC
    (a string), never numerically evaluated — off every decision path. The genus-4
    string carries 4×4 C/D blocks."""
    s = RiemannThetaG4.automorphy_factor(_gens()["J"])
    assert isinstance(s, str)
    assert "Omega" in s or "Ω" in s
    assert "1/2" in s          # it is a square root, carried symbolically


# ── gate (D): collapse-to-g3 transform consistency ───────────────────────────
def test_transform_restricts_to_g3_sub_block():
    """The genus-4 Sp(8,ℤ) action EMBEDDED from a g3 Sp(6,ℤ) generator (the g3 A,B,C,D
    blocks in the upper-left 3×3 corner, identity on the 4th coordinate) RESTRICTS
    consistently to the g3 action: for a genus-4 characteristic with a TRIVIAL 4th
    component (ε'₄=ε₄=0), the transformed first-three characteristic bits + the κ phase
    EQUAL the genus-3 transform of the corresponding g3 characteristic, and the 4th
    component stays trivial. The no-shell proof that the g4 modular action restricts to
    the g3 sub-block (so the genus ladder is uniform). Verified on every g3 generator
    over all 64 trivial-4th characteristics."""
    def embed(g3):
        a3, b3, c3, d3 = g3

        def lift(m3):
            return tuple(tuple(m3[i][j] if (i < 3 and j < 3)
                               else (1 if (i == 3 and j == 3) else 0)
                               for j in range(4)) for i in range(4))
        # the 4th diagonal of A and D is 1 (identity); B and C are 0 on the 4th
        def lift_off(m3):
            return tuple(tuple(m3[i][j] if (i < 3 and j < 3) else 0
                               for j in range(4)) for i in range(4))
        return (lift(a3), lift_off(b3), lift_off(c3), lift(d3))

    g3gens = {
        "T": RiemannThetaG3.sp6_translation(((1, 0, 0), (0, 0, 0), (0, 0, 0))),
        "U": RiemannThetaG3.sp6_gl_twist(((0, 1, 0), (0, 0, 1), (1, 0, 0))),
        "J": RiemannThetaG3.sp6_inversion(),
    }
    for name, g3 in g3gens.items():
        g4 = embed(g3)
        assert RiemannThetaG4.sp8_is_symplectic(g4), name
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    for d in (0, 1):
                        for e in (0, 1):
                            for f in (0, 1):
                                rt3 = RiemannThetaG3(a, b, c, d, e, f)
                                rt4 = RiemannThetaG4(a, b, c, 0, d, e, f, 0)
                                n3, k3 = rt3.transform(g3)
                                n4, k4 = rt4.transform(g4)
                                (ep4, e4) = n4.characteristic
                                (ep3, e3) = n3.characteristic
                                # first three bits + κ match; 4th stays trivial
                                assert ep4[:3] == ep3 and e4[:3] == e3, (name, rt3)
                                assert ep4[3] == 0 and e4[3] == 0, (name, rt3)
                                assert k4 == k3, (name, rt3, k4, k3)


# ── gate (B): the genus-4 ADDITION relation ──────────────────────────────────
def test_addition_identity_holds_exact():
    """THE rc85 (B) GATE: the genuine genus-4 theta addition theorem (DLMF §21.6.8 at
    z₁=z₂=0, g=4 — sum over r ∈ (ℤ/2)⁴, SIXTEEN terms) holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω. It verifies genuine a≠b pairs (the
    real addition content) AND that they exercise the genus-4 cross-terms."""
    assert RiemannThetaG4.addition_holds(2)


def test_addition_is_genuinely_distinct_from_duplication():
    """THE NO-SHELL PROOF: the genus-4 addition relation is GENUINELY DISTINCT from the
    genus-4 duplication. Its LEFT side θ[a;0]·θ[b;0] with a≠b is a product of two
    DIFFERENT theta-nulls — NOT equal to ANY duplication LHS θ[c;0]² (a single null
    squared, c ∈ {0,1}⁴)."""
    assert RiemannThetaG4.addition_is_distinct_from_duplication(2)


def test_addition_exercises_genus4_cross_terms():
    """The genus-4 addition identity genuinely exercises the genus-4 cross-terms
    (C₁₄, C₂₄ or C₃₄ ≠ 0 monomials present) for a pair spanning the fourth coordinate —
    it proves genuine genus-4 content, not the genus-3 slice."""
    L = RiemannThetaG4.addition_lhs((1, 0, 0, 1), (0, 0, 0, 0), 2)
    assert any((c14 != 0 or c24 != 0 or c34 != 0)
               for (_a1, _a2, _a3, _a4, _c12, _c13, c14, _c23, c24, c34) in L)


# ── gate (C): the genus-4 universal GÖPEL relation ───────────────────────────
def test_goepel_is_syzygous():
    """The canonical genus-4 Göpel relation is genuinely SYZYGOUS — eight signed pairs,
    sixteen DISTINCT even nulls all sharing the common GF(2) sum [1,1,1,1;1,1,1,1],
    balanced ±1 signs (four +1, four −1)."""
    assert RiemannThetaG4.goepel_is_syzygous()


def test_goepel_holds_exact():
    """THE rc85 (C) GATE: the genus-4 universal Göpel quadratic theta-null relation
    Σ_{+} θ²[a]θ²[b] = Σ_{−} θ²[a]θ²[b] (an 8-pair / 16-null same-Ω relation) holds
    EXACTLY on the box-stable safe region, with a genuine genus-4 cross-term present."""
    assert RiemannThetaG4.goepel_holds(2)


def test_goepel_is_distinct_from_duplication_and_addition():
    """The genus-4 Göpel relation is GENUINELY DISTINCT from the genus-4 duplication and
    addition relations (degree-4 same-Ω vs degree-2 Ω-vs-2Ω)."""
    assert RiemannThetaG4.goepel_is_distinct_from_duplication_and_addition(2)


# ── gate (E): NO REGRESSION (rc75–78 genus-3 + rc80/81 genus-4 gates) ─────────
def test_no_regression_genus3_gates():
    t000 = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert RiemannThetaG3.duplication_holds(4)              # rc75 duplication
    assert RiemannThetaG3.addition_holds(3)                 # rc77 addition
    assert RiemannThetaG3.goepel_holds(3)                   # rc78 Göpel
    assert t000.collapse_g2() == RiemannTheta(0, 0, 0, 0)   # rc75 collapse


def test_no_regression_genus4_carrier_gates():
    assert _t0().collapse_g3() == RiemannThetaG3(0, 0, 0, 0, 0, 0)   # rc80 collapse
    assert RiemannThetaG4.duplication_holds(2)                       # rc80 duplication
    assert RiemannThetaG4.even_null_count() == (136, 120)           # rc80 enumeration


def test_genus2_even_null_count_uniformity():
    """The rc85 uniformity bonus — all three genus carriers expose even_null_count."""
    assert RiemannTheta.even_null_count() == (10, 6)
    assert RiemannThetaG3.even_null_count() == (36, 28)
    assert RiemannThetaG4.even_null_count() == (136, 120)


# ── gate (F): Python==C parity ───────────────────────────────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_sp8(),
                    reason="native srmech_riemann_theta_g4_sp8_char not loaded")
def test_python_c_parity_transformation():
    """The native Sp(8,ℤ) characteristic transform + κ exponent equal the pure oracle
    EXACTLY for all 256 characteristics over all generators (do NOT trust the C —
    compare)."""
    for name, g in _gens().items():
        gv = RiemannThetaG4._validate_gamma8(g)
        for rt in ALL256:
            c_path = _native.riemann_theta_g4_sp8_char_c(
                gv, rt._ep1, rt._ep2, rt._ep3, rt._ep4,
                rt._e1, rt._e2, rt._e3, rt._e4)
            npp, nep = RiemannThetaG4._char_transform_int(
                g, (rt._ep1, rt._ep2, rt._ep3, rt._ep4),
                (rt._e1, rt._e2, rt._e3, rt._e4))
            kpy = RiemannThetaG4._kappa_exp8(
                g, (rt._ep1, rt._ep2, rt._ep3, rt._ep4),
                (rt._e1, rt._e2, rt._e3, rt._e4))
            assert c_path == ((npp[0] % 2, npp[1] % 2, npp[2] % 2, npp[3] % 2,
                               nep[0] % 2, nep[1] % 2, nep[2] % 2, nep[3] % 2), kpy), (
                name, rt.characteristic)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_eighth(),
                    reason="native srmech_riemann_theta_g4_eighth_lattice not loaded")
def test_python_c_parity_eighth_lattice():
    """The native genus-4 eighth-nome lattice equals the pure oracle EXACTLY at Ω and at
    2Ω over several boxes and characteristics."""
    for box in (0, 1, 2):
        for s1 in (-1, 0, 1, 2):
            for s4 in (0, 1):
                for e1 in (0, 1):
                    for at2 in (False, True):
                        c_path = _native.riemann_theta_g4_eighth_lattice_c(
                            s1, 0, 1, s4, e1, 0, 1, 0, at2, box)
                        py = _pure_eighth(s1, 0, 1, s4, e1, 0, 1, 0, at2, box)
                        assert c_path == py, (box, s1, s4, e1, at2)


def _pure_eighth(s1, s2, s3, s4, e1, e2, e3, e4, at2, box):
    out = {}
    step = 4 if at2 else 2
    m = 1 if at2 else 2
    for n1 in range(-box, box + 1):
        u1 = step * n1 + s1
        for n2 in range(-box, box + 1):
            u2 = step * n2 + s2
            for n3 in range(-box, box + 1):
                u3 = step * n3 + s3
                for n4 in range(-box, box + 1):
                    u4 = step * n4 + s4
                    key = (m * u1 * u1, m * u2 * u2, m * u3 * u3, m * u4 * u4,
                           m * u1 * u2, m * u1 * u3, m * u1 * u4,
                           m * u2 * u3, m * u2 * u4, m * u3 * u4)
                    sign = 1 if (e1 * n1 + e2 * n2 + e3 * n3 + e4 * n4) % 2 == 0 else -1
                    out[key] = out.get(key, 0) + sign
    return {k: w for k, w in out.items() if w != 0}


@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_goepel(),
                    reason="native srmech_riemann_theta_g4_goepel not loaded")
def test_python_c_parity_goepel_decision():
    """The native genus-4 Göpel-relation gate decision equals the pure-Python decision
    EXACTLY (holds == True, has_cross == True) at box 2 and 3."""
    for box in (2, 3):
        c_path = _native.riemann_theta_g4_goepel_c(box)
        assert c_path == (True, True), (box, c_path)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g4_sp8(),
                    reason="native peers not loaded")
def test_gates_pass_through_native():
    """The transformation gate still passes with the native path live (end-to-end on
    the C peer)."""
    for g in _gens().values():
        for rt in ALL256:
            new, k = rt.transform(g)
            assert new.is_even == rt.is_even
            assert 0 <= k < 8


def test_pure_python_alone_passes_new_gates(pure_riemann_theta):
    """The COMPLETE pure-Python body alone passes the new gates (so the carrier is
    correct on a no-C host) — the native path is FORCED OFF (rc106: every
    ``has_native_riemann_theta*`` gate monkeypatched False + record-and-raise
    sentinels on the ``riemann_theta*_c`` bindings; a native hit fails loudly).

    What runs pure, and why this IS the honest full pure coverage:

    - ``goepel_holds(2)`` runs the COMPLETE pure decision body at the shipped gate
      box — the native ``srmech_riemann_theta_g4_goepel`` peer replaces the WHOLE
      decision on a native host, so this is the one rc85 gate whose pure body a
      native run never touches;
    - the eighth-nome fallback builders (Ω and 2Ω) — the ONLY native-dispatched
      component of the ADDITION gate — are proven against this file's independent
      ``_pure_eighth`` oracle at the gate box, for characteristics spanning the
      genus-4 cross-terms and both sign branches.

    The pre-rc106 version re-ran ``addition_holds(2)`` + ``goepel_holds(2)`` with
    NO monkeypatch (≈213 s that never left the dispatched path — the single
    largest duplicate in the #707 family profile). The addition DECISION body
    (convolution + safe-region compare) has NO native peer — it is one always-pure
    body already executed by ``test_addition_identity_holds_exact`` — so re-running
    it here proved nothing the primary gate + the pure-lattice oracle checks below
    do not."""
    # the complete pure Göpel decision body, at the shipped gate box
    assert RiemannThetaG4.goepel_holds(2)
    # the pure eighth-nome fallback builders == the independent oracle (Ω + 2Ω)
    for (a, e) in (((1, 0, 0, 1), (0, 0, 0, 0)),   # spans the 4th coord (C₁₄ ≠ 0)
                   ((1, 1, 1, 1), (0, 0, 0, 0)),   # all six cross-terms odd
                   ((0, 0, 0, 0), (1, 0, 0, 1))):  # non-trivial sign branch
        got_omega = RiemannThetaG4._theta_omega_eighth(*a, *e, 2)
        assert got_omega == _pure_eighth(*a, *e, False, 2), (a, e)
        got_2omega = RiemannThetaG4._theta_two_omega_eighth(*a, *e, 2)
        assert got_2omega == _pure_eighth(*a, *e, True, 2), (a, e)
    assert pure_riemann_theta == []      # no native symbol was ever reached


# ── gate (G): the carrier source is numpy / math / abs() free ────────────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL
    assert "float(" not in text                          # no float in the carrier
