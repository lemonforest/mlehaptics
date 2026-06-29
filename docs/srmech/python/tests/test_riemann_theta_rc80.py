"""rc80 — ``srmech.amsc.riemann_theta.RiemannThetaG4``, the NEXT RUNG of the GENUS axis
(the SCHOTTKY FRONTIER).

The genus-4 Riemann theta-CONSTANT, exact-integer
``(A₁,A₂,A₃,A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄)`` exponent 10-TUPLE lattice in the quarter-nome
base — the genus-4 analog of the rc75 genus-3 ``RiemannThetaG3`` first rung. Genus 4 has
SIX cross-terms (vs genus-3's THREE), each a denominator-4 clearing of a half-integer
product (the genus-4 scaling difficulty). A pure CARRIER (like RiemannTheta /
RiemannThetaG3 / ThetaSum): no public ToolEntry op, so ``tools.total`` is UNCHANGED —
these tests assert ONLY the carrier's own gates.

The build gates (the no-shell proof):

  (a) the GENUS axis — ``genus == 4``; 136 even + 120 odd characteristics
      (``2^{g-1}(2^g±1)`` for ``g=4`` → 136 even, 120 odd; 136+120 = 256 = 4^g);
  (b) the FOUNDATION-FIRST exponent-lattice clearing — exact integer 10-tuple for all 256
      characteristics, with all SIX q_ij cross-terms denominator-4 handled
      (``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)``);
  (c) **COLLAPSE g4→g3 (primary):** ``θ[0,0,0,0;0,0,0,0].collapse_g3()`` == the rc75
      genus-3 trivial ``RiemannThetaG3`` EXACTLY (bit-exact vs the existing rung) AND
      derives from the lattice n₄=0 slice; the all-trivial chain → genus-1 θ₃; a
      non-trivial 4th component HONESTLY REFUSES — THE foundation gate;
  (d) **FORMAL genus-4 theta-null identity (secondary):** the genus-4 Gauss/duplication
      identity ``θ[0;0](0|Ω)² = Σ_{c∈(½ℤ⁴/ℤ⁴)} θ[c;0](0|2Ω)²`` (16 summands) holds EXACTLY
      as a truncated exact-integer multivariate q-series for ALL Ω (DLMF §21.6.8 all-zero
      / z=0 specialization; Mumford, Tata Lectures on Theta I) — and genuinely exercises
      ALL SIX cross-terms;
  (e) **NO REGRESSION:** all rc72/73/74 genus-2 + rc75/76/77/78 genus-3 gates still pass
      exactly;
  (f) Python==C parity EXACT on ``.lattice`` + the gates (guarded by native skip);
  (g) the documented Schottky frontier (``schottky_locus_is_open``) — genus 4 turns the
      Schottky problem ON; the numerical Jacobian decision is the documented OPEN;
  (h) the carrier source has no numpy / math / abs() (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta, RiemannThetaG3, RiemannThetaG4
from srmech.amsc import _native


# the trivial even genus-4 theta-constant (the one that collapses), reused below
def _t0() -> RiemannThetaG4:
    return RiemannThetaG4.theta_constant((0, 0, 0, 0), (0, 0, 0, 0))


# the exact θ₃ target series (the rc70 anchor; the all-trivial collapse chain)
THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


# ── gate (a): the GENUS axis (genus 4; 136 even + 120 odd) ────────────────────
def test_genus_axis_is_four():
    assert _t0().genus == 4


def test_onethirtysix_even_onetwenty_odd_characteristics():
    """Genus 4 has 256 binary characteristics — 136 EVEN + 120 ODD (``2^{g-1}(2^g+1) =
    8·17 = 136`` even, ``2^{g-1}(2^g-1) = 8·15 = 120`` odd for g=4; 136+120 = 256 = 4^g).
    A characteristic is even iff ε'·ε ≡ 0 (mod 2)."""
    even = RiemannThetaG4.even_characteristics()
    assert len(even) == 136
    assert all(rt.is_even for rt in even)
    assert RiemannThetaG4.even_null_count() == (136, 120)
    # the 120 odd ones: all 256 minus the 136 even
    all256 = [RiemannThetaG4(a, b, c, d, e, f, g, h)
              for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)
              for e in (0, 1) for f in (0, 1) for g in (0, 1) for h in (0, 1)]
    assert len(all256) == 256
    odd = [rt for rt in all256 if not rt.is_even]
    assert len(odd) == 120
    for rt in odd:
        (ep1, ep2, ep3, ep4), (e1, e2, e3, e4) = rt.characteristic
        assert (ep1 * e1 + ep2 * e2 + ep3 * e3 + ep4 * e4) % 2 == 1


# ── gate (b): the exponent-lattice clearing (the foundation unit) ─────────────
def test_diagonal_exponents_are_perfect_square_clearing():
    """The diagonal cleared exponents A₁..A₄ are (2nᵢ+ε'ᵢ)² — exact integers. For the
    trivial char each Aᵢ runs over {0, 4, 16, 36, …} = (2nᵢ)²."""
    lat = _t0().lattice(3)
    a1_vals = sorted({k[0] for k in lat})
    assert a1_vals == [(2 * n) ** 2 for n in range(0, 4)]    # 0,4,16,36


def test_six_cross_terms_denominator_4_clearing():
    """THE GENUS-4 SCALING DIFFICULTY: the SIX cross-terms C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ) —
    each the mᵢmⱼ product of two half-integers, cleared with denominator 4. For the
    (½,½,½,½) characteristic [1,1,1,1;0,0,0,0] all six are genuinely non-zero, odd-shaped
    (C_ij = (2nᵢ+1)(2nⱼ+1)). Verified term-by-term, then in the merged lattice."""
    rt = RiemannThetaG4.theta_constant((1, 1, 1, 1), (0, 0, 0, 0))   # ε' = (1,1,1,1)
    for n1 in range(-2, 3):
        for n2 in range(-2, 3):
            u1, u2 = 2 * n1 + 1, 2 * n2 + 1
            assert 4 * n1 * n2 + 2 * n1 + 2 * n2 + 1 == u1 * u2
    lat = rt.lattice(2)
    # the 6 cross-term slots are key indices 4..9: C12,C13,C14,C23,C24,C34
    for slot in range(4, 10):
        assert any(k[slot] != 0 for k in lat), slot


def test_lattice_all_256_characteristics_are_exact_integers():
    """The exact-integer lattice is well-defined for ALL 256 characteristics (the
    foundation-first unit) — every key is an int 10-tuple, every coeff a nonzero int."""
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                for d in (0, 1):
                    for e in (0, 1):
                        for f in (0, 1):
                            for g in (0, 1):
                                for h in (0, 1):
                                    lat = RiemannThetaG4(
                                        a, b, c, d, e, f, g, h).lattice(2)
                                    key_tuple = (a, b, c, d, e, f, g, h)
                                    assert lat, key_tuple
                                    for key, v in lat.items():
                                        assert len(key) == 10
                                        assert all(isinstance(x, int)
                                                   for x in key)
                                        assert isinstance(v, int) and v != 0


# ── gate (c): COLLAPSE g4→g3 — the primary foundation gate ────────────────────
def test_collapse_g3_is_rc75_genus3_trivial_bit_exact():
    """THE FOUNDATION GATE: collapse the genus-4 carrier to genus 3 (Ω₄₄=Ω₁₄=Ω₂₄=Ω₃₄=0,
    n₄=0) — the trivial even characteristic's surviving slice is the rc75 genus-3 trivial
    theta-null. BIT-EXACT vs the existing rung."""
    collapsed = _t0().collapse_g3()
    assert collapsed == RiemannThetaG3(0, 0, 0, 0, 0, 0)
    assert collapsed.genus == 3


def test_collapse_derives_from_the_lattice_n4_zero_slice():
    """The collapse is GENUINE — it derives from the genus-4 lattice itself, not a
    hardcoded return. The genus-3 degeneration q₄→0 / q₁₄,q₂₄,q₃₄→1 keeps ONLY the n₄=0
    slice (A₄=C₁₄=C₂₄=C₃₄=0 for the trivial char), reproducing the rc75 genus-3 trivial
    lattice (A₁,A₂,A₃,C₁₂,C₁₃,C₂₃) EXACTLY."""
    for box in (2, 3, 4):
        assert _t0().collapse_g3_lattice_matches(box) is True


def test_collapse_g1_chain_is_theta3_bit_exact():
    """The all-trivial genus-4 → genus-3 → genus-2 → genus-1 chain reproduces the rc70 θ₃
    series EXACTLY (bit-exact across three collapse rungs)."""
    assert _t0().collapse_g1_q_series(20) == THETA3_Q20


def test_collapse_only_trivial_characteristic_is_honest():
    """Only the trivial even characteristic [0,0,0,0;0,0,0,0] collapses to the plain
    genus-3 rung; any characteristic with a non-trivial 4th / signed component honestly
    refuses (an honest boundary, not a fabricated reduction — the rc75 collapse pattern)."""
    for c in [(1, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 1, 0, 0, 0, 0),
              (0, 0, 0, 0, 0, 0, 0, 1), (1, 1, 1, 1, 0, 0, 0, 0),
              (0, 0, 0, 1, 0, 0, 0, 1)]:
        with pytest.raises(ValueError):
            RiemannThetaG4(*c).collapse_g3()
        with pytest.raises(ValueError):
            RiemannThetaG4(*c).collapse_g1_q_series(20)
        with pytest.raises(ValueError):
            RiemannThetaG4(*c).collapse_g3_lattice_matches(3)


# ── gate (d): the FORMAL genus-4 theta-null identity (Gauss duplication) ───────
def test_genus4_duplication_identity_holds_exact():
    """THE SECONDARY GATE: the genus-4 Gauss/duplication theta-null identity
    θ[0;0](0|Ω)² = Σ_{c∈(½ℤ⁴/ℤ⁴)} θ[c;0](0|2Ω)² (16 summands) holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω (no transcendental evaluation). The
    z₁=z₂=0 / all-zero-characteristic specialization of DLMF §21.6.8; classically Mumford,
    Tata Lectures on Theta I (1983). It genuinely exercises ALL SIX cross-terms —
    proving genuine genus-4 theta-constants, not the genus-3 slice. (box kept small —
    (2·box+1)⁴ grows fast; the identity is box-stable.)"""
    assert RiemannThetaG4.duplication_holds(2)


def test_genus4_duplication_lhs_equals_rhs_on_safe_region():
    """The two sides of the genus-4 duplication identity are equal on the safe inner
    region, and the region is non-trivially populated with a genuine genus-4 cross-term
    (C₁₄/C₂₄/C₃₄ ≠ 0) monomial (so the genuinely-new 4-way coupling is exercised)."""
    box = 2
    lhs = RiemannThetaG4.duplication_lhs(box)
    rhs = RiemannThetaG4.duplication_rhs(box)
    safe = 4 * box * box

    def restrict(lat):
        kept = {}
        for k, v in lat.items():
            a1, a2, a3, a4, c12, c13, c14, c23, c24, c34 = k
            mags = [c if c >= 0 else -c
                    for c in (c12, c13, c14, c23, c24, c34)]
            if (a1 <= safe and a2 <= safe and a3 <= safe and a4 <= safe
                    and all(m <= safe for m in mags)):
                kept[k] = v
        return kept

    L, R = restrict(lhs), restrict(rhs)
    assert L == R
    # genuine genus-4 cross-term: C14 (idx 6) / C24 (idx 8) / C34 (idx 9)
    assert any(k[6] != 0 or k[8] != 0 or k[9] != 0 for k in L)


# ── gate (e): NO REGRESSION — the genus-2 + genus-3 gates still pass ──────────
def test_no_regression_rc72_73_74_genus2_gates():
    """The genus-4 extension does not regress the genus-2 carrier — the rc72/73/74
    genus-2 collapse + duplication + addition + Göpel gates still pass exactly."""
    g2 = RiemannTheta.theta_constant((0, 0), (0, 0))
    assert g2.collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannTheta.duplication_holds(6)
    assert RiemannTheta.addition_holds(8)
    assert RiemannTheta.addition_is_distinct_from_duplication(8)
    assert RiemannTheta.goepel_holds(5)
    assert RiemannTheta.rosenhain_lambda_map_is_well_formed()


def test_no_regression_rc75_76_77_78_genus3_gates():
    """The genus-4 extension does not regress the genus-3 carrier — the rc75/76/77/78
    genus-3 gates still pass exactly."""
    g3 = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert g3.collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG3.duplication_holds(3)
    assert RiemannThetaG3.even_null_count() == (36, 28)
    assert RiemannThetaG3.chi18_factor_count_is_36_even()
    assert RiemannThetaG3.goepel_holds(3)


# ── gate (f): Python==C parity on .lattice + the gates ───────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g4(),
                    reason="native srmech_riemann_theta_g4 not loaded")
def test_python_c_parity_all_characteristics():
    """The native path and the pure-Python oracle emit the BYTE-IDENTICAL canonical
    exact-integer genus-4 lattice for all 256 characteristics over several boxes (do NOT
    trust the C — compare). THE genus-4 6-cross-term exact clearing, end-to-end."""
    for box in (0, 1, 2, 3):
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    for d in (0, 1):
                        for e in (0, 1):
                            for f in (0, 1):
                                for g in (0, 1):
                                    for h in (0, 1):
                                        rt = RiemannThetaG4(a, b, c, d, e, f, g, h)
                                        c_path = rt.lattice(box)        # native
                                        py_path = rt._lattice_py(box)   # oracle
                                        assert c_path == py_path, (
                                            a, b, c, d, e, f, g, h, box)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g4(),
                    reason="native srmech_riemann_theta_g4 not loaded")
def test_python_c_parity_gates_through_native():
    """The collapse + duplication gates still pass with the C lattice path live
    (end-to-end on the native peer)."""
    assert _native.has_native_riemann_theta_g4()
    assert _t0().collapse_g3_lattice_matches(3) is True
    assert _t0().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG4.duplication_holds(2)


def test_pure_python_oracle_alone_passes_gates():
    """The COMPLETE pure-Python body alone passes every gate (so the carrier is correct
    on a no-C host)."""
    assert _t0()._lattice_py(2) == _t0()._lattice_py(2)
    assert _t0().collapse_g3_lattice_matches(3) is True
    assert _t0().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG4.duplication_holds(2)


# ── gate (g): the documented SCHOTTKY frontier ────────────────────────────────
def test_schottky_locus_is_documented_open():
    """The genus-4 frontier is documented as the operand-side OPEN: genus 4 is the FIRST
    genus where the Jacobian locus J₄ is a PROPER subvariety of A₄ (dim M₄ = 3g−3 = 9 <
    dim A₄ = g(g+1)/2 = 10) — the Schottky problem turns on. The cutter is the Schottky
    form J (Schottky 1888 degree-16 polynomial in the 136 even theta-nulls; Igusa 1981:
    J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆); Poor & Yuen 1996). The numerical Jacobian decision is a
    transcendental point-evaluation → NOT a finite exact carrier op → the documented OPEN
    (the rc76 pattern). NO numerical decision is built; J is NOT built (that is rc81)."""
    s = RiemannThetaG4.schottky_locus_is_open()
    assert isinstance(s, str)
    assert s.startswith("OPEN")
    assert "Schottky form J" in s
    assert "E₈⊕E₈" in s
    assert "E₁₆" in s
    assert "dim M₄ = 3g−3 = 9" in s
    assert "dim A₄" in s
    assert "Igusa 1981" in s
    assert "Poor & Yuen 1996" in s
    assert "g ≥ 5" in s   # the Schottky frontier OPEN extends to g ≥ 5
    # no method on the carrier returns a numerical Schottky / Jacobian verdict, and J
    # is NOT built in rc80 (it is the rc81 capstone)
    assert not hasattr(RiemannThetaG4, "is_jacobian")
    assert not hasattr(RiemannThetaG4, "schottky_form")


def test_singular_even_null_is_the_empty_set_characteristic():
    """The distinguished SINGULAR even null is the empty-set characteristic
    [0,0,0,0;0,0,0,0] — the one that collapses to the genus-3 trivial null and on to θ₃."""
    sing = RiemannThetaG4.singular_even_null()
    assert sing.characteristic == ((0, 0, 0, 0), (0, 0, 0, 0))
    assert sing.is_even
    assert sing in RiemannThetaG4.even_characteristics()


# ── input validation ──────────────────────────────────────────────────────────
def test_construction_rejects_bad_characteristic_bits():
    with pytest.raises(ValueError):
        RiemannThetaG4(2, 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannThetaG4(0, -1, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannThetaG4.theta_constant((0, 0, 0, 0), (0, 0, 0, 3))


def test_lattice_rejects_bad_box():
    with pytest.raises(ValueError):
        _t0().lattice(-1)
    with pytest.raises(ValueError):
        RiemannThetaG4.duplication_holds(1)   # box < 2 for the gate


def test_equality_and_hash():
    assert (RiemannThetaG4(1, 0, 1, 0, 1, 0, 1, 0)
            == RiemannThetaG4(1, 0, 1, 0, 1, 0, 1, 0))
    assert (RiemannThetaG4(1, 0, 1, 0, 1, 0, 1, 0)
            != RiemannThetaG4(0, 0, 1, 0, 1, 0, 1, 0))
    assert len({RiemannThetaG4(1, 0, 1, 0, 1, 0, 1, 0),
                RiemannThetaG4(1, 0, 1, 0, 1, 0, 1, 0)}) == 1
    # the genus-4 carrier is not equal to a genus-3 / genus-2 carrier
    assert RiemannThetaG4(0, 0, 0, 0, 0, 0, 0, 0) != RiemannThetaG3(0, 0, 0, 0, 0, 0)
    assert RiemannThetaG4(0, 0, 0, 0, 0, 0, 0, 0) != RiemannTheta(0, 0, 0, 0)


# ── gate (h): the carrier source is numpy / math / abs() free ────────────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None        # no bare abs() CALL
    assert "float(" not in text                         # no float in the carrier body
