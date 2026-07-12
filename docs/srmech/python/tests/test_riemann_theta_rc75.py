"""rc75 — ``srmech.amsc.riemann_theta.RiemannThetaG3``, the NEXT RUNG of the GENUS axis.

The genus-3 Riemann theta-CONSTANT, exact-integer ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃)`` exponent
SEXTUPLE lattice in the quarter-nome base — the genus-3 analog of the rc72 genus-2
``RiemannTheta`` first rung. Genus 3 has THREE cross-terms (vs genus-2's ONE), each a
denominator-4 clearing of a half-integer product (the hardest part). A pure CARRIER
(like RiemannTheta / ThetaSum): no public ToolEntry op, so ``tools.total`` is UNCHANGED
— these tests assert ONLY the carrier's own gates.

The build gates (the no-shell proof):

  (a) the GENUS axis — ``genus == 3``; 36 even + 28 odd characteristics (Grushevsky,
      arXiv:1009.0369: ``2^{g-1}(2^g±1)`` for ``g=3`` → 36 even, 28 odd);
  (b) the FOUNDATION-FIRST exponent-lattice clearing — exact integer
      ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃)`` for all 64 characteristics, with all THREE q_ij
      cross-terms denominator-4 handled (``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)``);
  (c) **COLLAPSE g3→g2 (primary):** ``θ[0,0,0;0,0,0].collapse_g2()`` == the rc72 genus-2
      trivial ``RiemannTheta`` EXACTLY (bit-exact vs the existing rung) AND derives from
      the lattice n₃=0 slice; the all-trivial chain → genus-1 θ₃; a non-trivial 3rd
      component HONESTLY REFUSES — THE foundation gate;
  (d) **FORMAL genus-3 theta-null identity (secondary):** the genus-3 Gauss/duplication
      identity ``θ[0;0](0|Ω)² = Σ_{c∈(½ℤ³/ℤ³)} θ[c;0](0|2Ω)²`` (8 summands) holds EXACTLY
      as a truncated exact-integer multivariate q-series for ALL Ω (Chai 2014, Thm 1.2(b),
      a=b=0/z=w=0/g=3; Mumford, Tata Lectures on Theta I) — and genuinely exercises ALL
      THREE cross-terms;
  (e) **NO REGRESSION:** all rc72/73/74 genus-2 gates still pass exactly;
  (f) Python==C parity EXACT on ``.lattice`` + the gates (guarded by native skip);
  (g) the documented honest boundary (non-hyperelliptic / vanishing-null) + Schottky;
  (h) the carrier source has no numpy / math / abs() (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta, RiemannThetaG3
from srmech.amsc import _native


# the trivial even genus-3 theta-constant (the one that collapses), reused below
def _t000() -> RiemannThetaG3:
    return RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))


# the exact θ₃ target series (the rc70 anchor; the all-trivial collapse chain)
THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


# ── gate (a): the GENUS axis (genus 3; 36 even + 28 odd) ─────────────────────
def test_genus_axis_is_three():
    assert _t000().genus == 3


def test_thirtysix_even_twentyeight_odd_characteristics():
    """Genus 3 has 64 binary characteristics — 36 EVEN + 28 ODD (Grushevsky, arXiv:
    1009.0369: "there are 2^{g-1}(2^g+1) even theta constants" → g=3 gives 4·9=36 even,
    4·7=28 odd). A characteristic is even iff ε'·ε ≡ 0 (mod 2)."""
    even = RiemannThetaG3.even_characteristics()
    assert len(even) == 36
    assert all(rt.is_even for rt in even)
    assert RiemannThetaG3.even_null_count() == (36, 28)
    # the 28 odd ones: all 64 minus the 36 even
    all64 = [RiemannThetaG3(a, b, c, d, e, f)
             for a in (0, 1) for b in (0, 1) for c in (0, 1)
             for d in (0, 1) for e in (0, 1) for f in (0, 1)]
    odd = [rt for rt in all64 if not rt.is_even]
    assert len(odd) == 28
    for rt in odd:
        (ep1, ep2, ep3), (e1, e2, e3) = rt.characteristic
        assert (ep1 * e1 + ep2 * e2 + ep3 * e3) % 2 == 1


# ── gate (b): the exponent-lattice clearing (the foundation unit) ────────────
def test_diagonal_exponents_are_perfect_square_clearing():
    """The diagonal cleared exponents A₁,A₂,A₃ are (2nᵢ+ε'ᵢ)² — exact integers. For the
    trivial char each Aᵢ runs over {0, 4, 16, 36, …} = (2nᵢ)²."""
    lat = _t000().lattice(3)
    a1_vals = sorted({k[0] for k in lat})
    assert a1_vals == [(2 * n) ** 2 for n in range(0, 4)]    # 0,4,16,36


def test_three_cross_terms_denominator_4_clearing():
    """THE HARDEST PART: the THREE cross-terms C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ) — each the
    mᵢmⱼ product of two half-integers, cleared with denominator 4. For the (½,½,½)
    characteristic [1,1,1;0,0,0] all three are genuinely non-zero, odd-shaped
    (C_ij = (2nᵢ+1)(2nⱼ+1)). Verified term-by-term, then in the merged lattice."""
    rt = RiemannThetaG3.theta_constant((1, 1, 1), (0, 0, 0))   # ε' = (1,1,1)
    for n1 in range(-2, 3):
        for n2 in range(-2, 3):
            for n3 in range(-2, 3):
                u1, u2, u3 = 2 * n1 + 1, 2 * n2 + 1, 2 * n3 + 1
                assert 4 * n1 * n2 + 2 * n1 + 2 * n2 + 1 == u1 * u2
                assert 4 * n1 * n3 + 2 * n1 + 2 * n3 + 1 == u1 * u3
                assert 4 * n2 * n3 + 2 * n2 + 2 * n3 + 1 == u2 * u3
    lat = rt.lattice(3)
    assert any(k[3] != 0 for k in lat)    # C₁₂ ≠ 0
    assert any(k[4] != 0 for k in lat)    # C₁₃ ≠ 0
    assert any(k[5] != 0 for k in lat)    # C₂₃ ≠ 0


def test_lattice_all_sixtyfour_characteristics_are_exact_integers():
    """The exact-integer lattice is well-defined for ALL 64 characteristics (the
    foundation-first unit) — every key is an int sextuple, every coeff a nonzero int."""
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                for d in (0, 1):
                    for e in (0, 1):
                        for f in (0, 1):
                            lat = RiemannThetaG3(a, b, c, d, e, f).lattice(2)
                            assert lat, (a, b, c, d, e, f)
                            for key, v in lat.items():
                                assert len(key) == 6
                                assert all(isinstance(x, int) for x in key)
                                assert isinstance(v, int) and v != 0


# ── gate (c): COLLAPSE g3→g2 — the primary foundation gate ───────────────────
def test_collapse_g2_is_rc72_genus2_trivial_bit_exact():
    """THE FOUNDATION GATE: collapse the genus-3 carrier to genus 2 (Ω₃₃=Ω₁₃=Ω₂₃=0,
    n₃=0) — the trivial even characteristic's surviving slice is the rc72 genus-2
    trivial theta-null. BIT-EXACT vs the existing rung."""
    collapsed = _t000().collapse_g2()
    assert collapsed == RiemannTheta(0, 0, 0, 0)
    assert collapsed.genus == 2


def test_collapse_derives_from_the_lattice_n3_zero_slice():
    """The collapse is GENUINE — it derives from the genus-3 lattice itself, not a
    hardcoded return. The genus-2 degeneration q₃→0 / q₁₃,q₂₃→1 keeps ONLY the n₃=0
    slice (A₃=C₁₃=C₂₃=0 for the trivial char), reproducing the rc72 genus-2 trivial
    lattice (A₁,A₂,C₁₂) EXACTLY."""
    for box in (3, 4, 5):
        assert _t000().collapse_g2_lattice_matches(box) is True


def test_collapse_g1_chain_is_theta3_bit_exact():
    """The all-trivial genus-3 → genus-2 → genus-1 chain reproduces the rc70 θ₃ series
    EXACTLY (bit-exact across two collapse rungs)."""
    assert _t000().collapse_g1_q_series(20) == THETA3_Q20


def test_collapse_only_trivial_characteristic_is_honest():
    """Only the trivial even characteristic [0,0,0;0,0,0] collapses to the plain genus-2
    rung; any characteristic with a non-trivial 3rd / signed component honestly refuses
    (an honest boundary, not a fabricated reduction — the rc72 collapse pattern)."""
    for c in [(1, 0, 0, 0, 0, 0), (0, 0, 1, 0, 0, 0), (0, 0, 0, 0, 0, 1),
              (1, 1, 1, 0, 0, 0), (0, 0, 1, 0, 0, 1)]:
        with pytest.raises(ValueError):
            RiemannThetaG3(*c).collapse_g2()
        with pytest.raises(ValueError):
            RiemannThetaG3(*c).collapse_g1_q_series(20)
        with pytest.raises(ValueError):
            RiemannThetaG3(*c).collapse_g2_lattice_matches(4)


# ── gate (d): the FORMAL genus-3 theta-null identity (Gauss duplication) ──────
def test_genus3_duplication_identity_holds_exact():
    """THE SECONDARY GATE: the genus-3 Gauss/duplication theta-null identity
    θ[0;0](0|Ω)² = Σ_{c∈(½ℤ³/ℤ³)} θ[c;0](0|2Ω)² (8 summands) holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω (no transcendental evaluation). Chai,
    "Riemann's theta formula" (2014), Thm 1.2(b), a=b=0/z=w=0/g=3; classically Mumford,
    Tata Lectures on Theta I (1983). It genuinely exercises ALL THREE cross-terms —
    proving genuine genus-3 theta-constants, not the genus-2/genus-1 slice."""
    assert RiemannThetaG3.duplication_holds(2)
    assert RiemannThetaG3.duplication_holds(3)
    assert RiemannThetaG3.duplication_holds(4)


def test_genus3_duplication_lhs_equals_rhs_on_safe_region():
    """The two sides of the genus-3 duplication identity are equal on the safe inner
    region, and the region is non-trivially populated with a genuine genus-3 cross-term
    (C₁₃ or C₂₃ ≠ 0) monomial (so the genuinely-new 3-way coupling is exercised)."""
    box = 3
    lhs = RiemannThetaG3.duplication_lhs(box)
    rhs = RiemannThetaG3.duplication_rhs(box)
    safe = 4 * box * box

    def restrict(lat):
        kept = {}
        for k, v in lat.items():
            a1, a2, a3, c12, c13, c23 = k
            mags = [c if c >= 0 else -c for c in (c12, c13, c23)]
            if (a1 <= safe and a2 <= safe and a3 <= safe
                    and all(m <= safe for m in mags)):
                kept[k] = v
        return kept

    L, R = restrict(lhs), restrict(rhs)
    assert L == R
    assert any(k[4] != 0 or k[5] != 0 for k in L)   # genuine genus-3 cross-term


# ── gate (e): NO REGRESSION — the rc72/73/74 genus-2 gates still pass ─────────
def test_no_regression_rc72_73_74_genus2_gates():
    """The genus-3 extension does not regress the genus-2 carrier — CHEAP structural
    checks only (rc106): the collapse chain is bit-exact, the symbolic Rosenhain
    λ-map is well-formed, and the even/odd enumeration parity holds. The dense g2
    convolution gates are deliberately NOT re-run here — each is covered by its home
    file's PRIMARY gates in the SAME suite run (``duplication_holds(4/6/8)`` = rc72;
    ``addition_holds(4/6/8)`` + ``addition_is_distinct(6/8)`` = rc73;
    ``goepel_holds(4/5/6)`` + ``goepel_is_distinct(4/5)`` + Rosenhain = rc74) —
    before rc106 this file re-ran ``duplication_holds(6)`` + ``addition_holds(8)`` +
    ``addition_is_distinct(8)`` + ``goepel_holds(5)`` + ``goepel_is_distinct(5)``
    identically (≈35 s of literal duplicate convolution)."""
    g2 = RiemannTheta.theta_constant((0, 0), (0, 0))
    assert g2.collapse_g1_q_series(20) == THETA3_Q20      # rc72 collapse chain
    assert RiemannTheta.rosenhain_lambda_map_is_well_formed()   # rc74 symbolic map
    assert RiemannTheta.even_null_count() == (10, 6)      # enumeration parity


# ── gate (f): Python==C parity on .lattice + the gates ───────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g3(),
                    reason="native srmech_riemann_theta_g3 not loaded")
def test_python_c_parity_all_characteristics():
    """The native path and the pure-Python oracle emit the BYTE-IDENTICAL canonical
    exact-integer genus-3 lattice for all 64 characteristics over several boxes (do NOT
    trust the C — compare)."""
    for box in (0, 1, 2, 3):
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    for d in (0, 1):
                        for e in (0, 1):
                            for f in (0, 1):
                                rt = RiemannThetaG3(a, b, c, d, e, f)
                                c_path = rt.lattice(box)        # native present
                                py_path = rt._lattice_py(box)   # the oracle
                                assert c_path == py_path, (a, b, c, d, e, f, box)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g3(),
                    reason="native srmech_riemann_theta_g3 not loaded")
def test_python_c_parity_gates_through_native():
    """The collapse + duplication gates still pass with the C lattice path live
    (end-to-end on the native peer)."""
    assert _native.has_native_riemann_theta_g3()
    assert _t000().collapse_g2_lattice_matches(4) is True
    assert _t000().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG3.duplication_holds(3)


def test_pure_python_oracle_alone_passes_gates(pure_riemann_theta):
    """The COMPLETE pure-Python body alone passes every gate (so the carrier is correct
    on a no-C host) — the native path is FORCED OFF (rc106: before this the test
    carried NO monkeypatch and re-ran the dispatched path under a pure-sounding
    name). Same windows as before — they were already cheap pure."""
    assert _t000().lattice(3) == _t000()._lattice_py(3)   # dispatch fell to the oracle
    assert _t000().collapse_g2_lattice_matches(4) is True
    assert _t000().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG3.duplication_holds(3)
    assert pure_riemann_theta == []      # no native symbol was ever reached


# ── gate (g): the documented honest boundary (non-hyperelliptic / Schottky) ──
def test_hyperelliptic_locus_is_documented_open():
    """The genus-3 NEW structure is documented as the operand-side OPEN: the GENERIC
    genus-3 curve is NON-hyperelliptic (a smooth plane quartic); the hyperelliptic
    locus is cut out by a VANISHING even theta-null (Poor 1996; Grushevsky Thm
    3.9/5.2). The numerical decision is a transcendental point-evaluation → NOT a finite
    exact carrier op → the documented OPEN (the rc74 pattern). NO numerical decision is
    built."""
    s = RiemannThetaG3.hyperelliptic_locus_is_open()
    assert isinstance(s, str)
    assert s.startswith("OPEN")
    assert "NON-hyperelliptic" in s
    assert "plane quartic" in s
    assert "vanishing even theta-null" in s.lower()
    assert "g ≥ 4" in s   # Schottky frontier stays at g ≥ 4 (genus 3 is clean)
    # no method on the carrier returns a numerical hyperelliptic verdict
    assert not hasattr(RiemannThetaG3, "is_hyperelliptic")


def test_singular_even_null_is_the_empty_set_characteristic():
    """The distinguished SINGULAR even null is the empty-set characteristic
    [0,0,0;0,0,0] — the one that collapses to the genus-2 trivial null and on to θ₃."""
    sing = RiemannThetaG3.singular_even_null()
    assert sing.characteristic == ((0, 0, 0), (0, 0, 0))
    assert sing.is_even
    assert sing in RiemannThetaG3.even_characteristics()


# ── input validation ─────────────────────────────────────────────────────────
def test_construction_rejects_bad_characteristic_bits():
    with pytest.raises(ValueError):
        RiemannThetaG3(2, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannThetaG3(0, -1, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 3))


def test_lattice_rejects_bad_box():
    with pytest.raises(ValueError):
        _t000().lattice(-1)
    with pytest.raises(ValueError):
        RiemannThetaG3.duplication_holds(1)   # box < 2 for the gate


def test_equality_and_hash():
    assert RiemannThetaG3(1, 0, 1, 0, 1, 0) == RiemannThetaG3(1, 0, 1, 0, 1, 0)
    assert RiemannThetaG3(1, 0, 1, 0, 1, 0) != RiemannThetaG3(0, 0, 1, 0, 1, 0)
    assert len({RiemannThetaG3(1, 0, 1, 0, 1, 0),
                RiemannThetaG3(1, 0, 1, 0, 1, 0)}) == 1
    # the genus-3 carrier is not equal to a genus-2 carrier
    assert RiemannThetaG3(0, 0, 0, 0, 0, 0) != RiemannTheta(0, 0, 0, 0)


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
