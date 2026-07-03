"""rc86 — ``srmech.amsc.riemann_theta.RiemannThetaG5``, the NEXT RUNG of the GENUS axis
(PAST the SCHOTTKY FRONTIER, into the GENUINELY-OPEN regime).

The genus-5 Riemann theta-CONSTANT, exact-integer
``(A₁..A₅,C₁₂,C₁₃,C₁₄,C₁₅,C₂₃,C₂₄,C₂₅,C₃₄,C₃₅,C₄₅)`` exponent 15-TUPLE lattice in the
quarter-nome base — the genus-5 analog of the rc80 genus-4 ``RiemannThetaG4`` rung. Genus
5 has TEN cross-terms (vs genus-4's SIX), each a denominator-4 clearing of a half-integer
product (the genus-5 scaling difficulty). A pure CARRIER (like RiemannTheta /
RiemannThetaG3 / RiemannThetaG4 / ThetaSum): no public ToolEntry op, so ``tools.total`` is
UNCHANGED — these tests assert ONLY the carrier's own gates.

MEMORY of the box blowup: ``(2·box+1)⁵`` grows fast (box 1 → 243, box 2 → 3125, box 3 →
16807); the genus-5 duplication square at box ≥ 2 is catastrophic (> 5 min pure-Python).
So every lattice-touching test is kept at box ≤ 2, the duplication gate at box = 1, and
the cheap parity invariant ``even_null_count() == (528, 496)`` is the primary assertion.

The build gates (the no-shell proof):

  (a) the GENUS axis — ``genus == 5``; 528 even + 496 odd characteristics
      (``2^{g-1}(2^g±1)`` for ``g=5`` → 528 even, 496 odd; 528+496 = 1024 = 4^g);
  (b) the FOUNDATION-FIRST exponent-lattice clearing — exact integer 15-tuple, with all
      TEN q_ij cross-terms denominator-4 handled (``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)``);
  (c) **COLLAPSE g5→g4 (primary):** ``θ[0⁵;0⁵].collapse_g4()`` == the rc80 genus-4 trivial
      ``RiemannThetaG4`` EXACTLY (bit-exact) AND derives from the lattice n₅=0 slice; the
      all-trivial chain → genus-1 θ₃; a non-trivial 5th component HONESTLY REFUSES;
  (d) **FORMAL genus-5 theta-null identity (secondary):** the genus-5 Gauss/duplication
      identity ``θ[0;0](0|Ω)² = Σ_{c∈(½ℤ⁵/ℤ⁵)} θ[c;0](0|2Ω)²`` (32 summands) holds EXACTLY
      as a truncated exact-integer multivariate q-series for ALL Ω (DLMF §21.6.8 all-zero
      / z=0 specialization; Mumford, Tata Lectures on Theta I) — and genuinely exercises
      ALL TEN cross-terms (box = 1, the minimal box);
  (e) **NO REGRESSION:** the genus-2 / genus-3 / genus-4 gates still pass exactly;
  (f) Python==C parity EXACT on ``.lattice`` + the gates (guarded by native skip);
  (g) the documented GENUINELY-OPEN genus-5 Schottky frontier
      (``schottky_g5_decision_is_open``) — codim J₅ = 3 in A₅ (NOT a hypersurface), NO
      single form cuts J_g, only the Andreotti–Mayer / Schottky–Jung superset + KP/Shiota;
  (h) the carrier source has no numpy / math / abs() (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import (RiemannTheta, RiemannThetaG3, RiemannThetaG4,
                                       RiemannThetaG5)
from srmech.amsc import _native


# the trivial even genus-5 theta-constant (the one that collapses), reused below
def _t0() -> RiemannThetaG5:
    return RiemannThetaG5.theta_constant((0, 0, 0, 0, 0), (0, 0, 0, 0, 0))


# the exact θ₃ target series (the rc70 anchor; the all-trivial collapse chain)
THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


# a small curated set of genus-5 characteristics for the heavier (box=2) sweeps
def _curated_chars():
    return [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),   # trivial even
        (1, 1, 1, 1, 1, 0, 0, 0, 0, 0),   # (½,½,½,½,½) — all 10 cross-terms odd
        (0, 0, 0, 0, 1, 0, 0, 0, 0, 0),   # only the 5th upper component
        (1, 0, 0, 0, 1, 0, 0, 0, 0, 0),   # C₁₅ ≠ 0
        (1, 0, 1, 0, 1, 1, 0, 1, 0, 1),   # mixed, odd characteristic
        (1, 1, 0, 0, 0, 1, 1, 0, 0, 0),   # even, genus-2-ish slice
    ]


# ── gate (a): the GENUS axis (genus 5; 528 even + 496 odd) ────────────────────
def test_genus_axis_is_five():
    assert _t0().genus == 5


def test_528_even_496_odd_characteristics():
    """Genus 5 has 1024 binary characteristics — 528 EVEN + 496 ODD (``2^{g-1}(2^g+1) =
    16·33 = 528`` even, ``2^{g-1}(2^g-1) = 16·31 = 496`` odd for g=5; 528+496 = 1024 = 4^g).
    A characteristic is even iff ε'·ε ≡ 0 (mod 2). THE headline genus-5 invariant — pure
    parity, no lattice sum. (Grushevsky arXiv:1009.0369: 2^{g-1}(2^g+1) even theta nulls.)"""
    even = RiemannThetaG5.even_characteristics()
    assert len(even) == 528
    assert all(rt.is_even for rt in even)
    # the method returns a TUPLE (528, 496) — compare tuple-to-tuple, not tuple-to-int
    assert RiemannThetaG5.even_null_count() == (528, 496)
    # the 496 odd ones: all 1024 minus the 528 even
    all1024 = []
    for bits in range(1024):
        ep = [(bits >> i) & 1 for i in range(5)]
        e = [(bits >> (5 + i)) & 1 for i in range(5)]
        all1024.append(RiemannThetaG5(*(ep + e)))
    assert len(all1024) == 1024
    odd = [rt for rt in all1024 if not rt.is_even]
    assert len(odd) == 496
    for rt in odd:
        (ep1, ep2, ep3, ep4, ep5), (e1, e2, e3, e4, e5) = rt.characteristic
        assert (ep1 * e1 + ep2 * e2 + ep3 * e3 + ep4 * e4 + ep5 * e5) % 2 == 1


# ── gate (b): the exponent-lattice clearing (the foundation unit) ─────────────
def test_diagonal_exponents_are_perfect_square_clearing():
    """The diagonal cleared exponents A₁..A₅ are (2nᵢ+ε'ᵢ)² — exact integers. For the
    trivial char each Aᵢ runs over {0, 4, 16, …} = (2nᵢ)²."""
    lat = _t0().lattice(2)
    a1_vals = sorted({k[0] for k in lat})
    assert a1_vals == [(2 * n) ** 2 for n in range(0, 3)]    # 0,4,16


def test_ten_cross_terms_denominator_4_clearing():
    """THE GENUS-5 SCALING DIFFICULTY: the TEN cross-terms C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ) —
    each the mᵢmⱼ product of two half-integers, cleared with denominator 4. For the
    (½,½,½,½,½) characteristic [1,1,1,1,1;0,0,0,0,0] all ten are genuinely non-zero,
    odd-shaped (C_ij = (2nᵢ+1)(2nⱼ+1)). Verified term-by-term, then in the merged lattice."""
    rt = RiemannThetaG5.theta_constant((1, 1, 1, 1, 1), (0, 0, 0, 0, 0))
    for n1 in range(-2, 3):
        for n2 in range(-2, 3):
            u1, u2 = 2 * n1 + 1, 2 * n2 + 1
            assert 4 * n1 * n2 + 2 * n1 + 2 * n2 + 1 == u1 * u2
    lat = rt.lattice(2)
    # the 10 cross-term slots are key indices 5..14
    for slot in range(5, 15):
        assert any(k[slot] != 0 for k in lat), slot


def test_lattice_keys_are_exact_integer_15_tuples():
    """The exact-integer lattice is a 15-tuple → nonzero-int dict for a representative set
    of characteristics (the foundation-first unit)."""
    for ch in _curated_chars():
        lat = RiemannThetaG5(*ch).lattice(2)
        assert lat, ch
        for key, v in lat.items():
            assert len(key) == 15
            assert all(isinstance(x, int) for x in key)
            assert isinstance(v, int) and v != 0


# ── gate (c): COLLAPSE g5→g4 — the primary foundation gate ────────────────────
def test_collapse_g4_is_rc80_genus4_trivial_bit_exact():
    """THE FOUNDATION GATE: collapse the genus-5 carrier to genus 4
    (Ω₅₅=Ω₁₅=Ω₂₅=Ω₃₅=Ω₄₅=0, n₅=0) — the trivial even characteristic's surviving slice is
    the rc80 genus-4 trivial theta-null. BIT-EXACT vs the existing rung."""
    collapsed = _t0().collapse_g4()
    assert collapsed == RiemannThetaG4(0, 0, 0, 0, 0, 0, 0, 0)
    assert collapsed.genus == 4


def test_collapse_derives_from_the_lattice_n5_zero_slice():
    """The collapse is GENUINE — it derives from the genus-5 lattice itself, not a
    hardcoded return. The genus-4 degeneration q₅→0 / q₁₅,q₂₅,q₃₅,q₄₅→1 keeps ONLY the
    n₅=0 slice (A₅=C₁₅=C₂₅=C₃₅=C₄₅=0 for the trivial char), reproducing the rc80 genus-4
    trivial lattice (A₁..A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄) EXACTLY."""
    for box in (1, 2):
        assert _t0().collapse_g4_lattice_matches(box) is True


def test_collapse_g1_chain_is_theta3_bit_exact():
    """The all-trivial genus-5 → genus-4 → genus-3 → genus-2 → genus-1 chain reproduces the
    rc70 θ₃ series EXACTLY (bit-exact across four collapse rungs)."""
    assert _t0().collapse_g1_q_series(20) == THETA3_Q20


def test_collapse_only_trivial_characteristic_is_honest():
    """Only the trivial even characteristic [0⁵;0⁵] collapses to the plain genus-4 rung;
    any characteristic with a non-trivial 5th / signed component honestly refuses (an
    honest boundary, not a fabricated reduction — the rc80 collapse pattern)."""
    for c in [(1, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 1, 0, 0, 0, 0, 0),
              (0, 0, 0, 0, 0, 0, 0, 0, 0, 1), (1, 1, 1, 1, 1, 0, 0, 0, 0, 0),
              (0, 0, 0, 1, 0, 0, 0, 0, 0, 1)]:
        with pytest.raises(ValueError):
            RiemannThetaG5(*c).collapse_g4()
        with pytest.raises(ValueError):
            RiemannThetaG5(*c).collapse_g1_q_series(20)
        with pytest.raises(ValueError):
            RiemannThetaG5(*c).collapse_g4_lattice_matches(2)


# ── gate (d): the FORMAL genus-5 theta-null identity (Gauss duplication) ───────
def test_genus5_duplication_identity_holds_exact():
    """THE SECONDARY GATE: the genus-5 Gauss/duplication theta-null identity
    θ[0;0](0|Ω)² = Σ_{c∈(½ℤ⁵/ℤ⁵)} θ[c;0](0|2Ω)² (32 summands) holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω (no transcendental evaluation). The
    z₁=z₂=0 / all-zero-characteristic specialization of DLMF §21.6.8; classically Mumford,
    Tata Lectures on Theta I (1983). It genuinely exercises ALL TEN cross-terms. (box = 1,
    the minimal box — (2·box+1)⁵ grows fast; the identity is box-stable.)"""
    assert RiemannThetaG5.duplication_holds(1)


def test_genus5_duplication_lhs_equals_rhs_on_safe_region():
    """The two sides of the genus-5 duplication identity are equal on the safe inner
    region, and the region is non-trivially populated with a genuine genus-5 cross-term
    (C₁₅/C₂₅/C₃₅/C₄₅ ≠ 0) monomial (so the genuinely-new 5-way coupling is exercised)."""
    box = 1
    lhs = RiemannThetaG5.duplication_lhs(box)
    rhs = RiemannThetaG5.duplication_rhs(box)
    safe = 4 * box * box

    def restrict(lat):
        kept = {}
        for k, v in lat.items():
            a = k[:5]
            mags = [c if c >= 0 else -c for c in k[5:]]
            if all(x <= safe for x in a) and all(m <= safe for m in mags):
                kept[k] = v
        return kept

    L, R = restrict(lhs), restrict(rhs)
    assert L == R
    # genuine genus-5 cross-term: C₁₅ (idx 8) / C₂₅ (idx 11) / C₃₅ (idx 13) / C₄₅ (idx 14)
    assert any(k[8] != 0 or k[11] != 0 or k[13] != 0 or k[14] != 0 for k in L)


def test_duplication_rejects_box_below_one():
    with pytest.raises(ValueError):
        RiemannThetaG5.duplication_holds(0)


# ── gate (e): NO REGRESSION — the genus-2/3/4 gates still pass ────────────────
def test_no_regression_genus2_3_4_gates():
    """The genus-5 extension does not regress the lower-genus carriers — the genus-2 /
    genus-3 / genus-4 collapse + duplication + enumeration gates still pass exactly."""
    g2 = RiemannTheta.theta_constant((0, 0), (0, 0))
    assert g2.collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannTheta.duplication_holds(6)
    g3 = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert g3.collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG3.even_null_count() == (36, 28)
    g4 = RiemannThetaG4.theta_constant((0, 0, 0, 0), (0, 0, 0, 0))
    assert g4.collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG4.even_null_count() == (136, 120)
    assert RiemannThetaG4.duplication_holds(2)
    assert g4.collapse_g3_lattice_matches(2) is True


# ── gate (f): Python==C parity on .lattice + the gates ───────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g5(),
                    reason="native srmech_riemann_theta_g5 not loaded")
def test_python_c_parity_all_1024_chars_box01():
    """The native path and the pure-Python oracle emit the BYTE-IDENTICAL canonical
    exact-integer genus-5 lattice for ALL 1024 characteristics over boxes 0 and 1 (do NOT
    trust the C — compare). THE genus-5 10-cross-term exact clearing, end-to-end."""
    for box in (0, 1):
        for bits in range(1024):
            ep = [(bits >> i) & 1 for i in range(5)]
            e = [(bits >> (5 + i)) & 1 for i in range(5)]
            rt = RiemannThetaG5(*(ep + e))
            assert rt.lattice(box) == rt._lattice_py(box), (ep, e, box)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g5(),
                    reason="native srmech_riemann_theta_g5 not loaded")
def test_python_c_parity_curated_chars_box2():
    """Python==C byte-exact on the curated genus-5 characteristics at box 2 (the heavier
    5⁵=3125-point lattice; box kept ≤ 2 — the genus-5 blowup)."""
    for ch in _curated_chars():
        rt = RiemannThetaG5(*ch)
        assert rt.lattice(2) == rt._lattice_py(2), ch


@pytest.mark.skipif(not _native.has_native_riemann_theta_g5(),
                    reason="native srmech_riemann_theta_g5 not loaded")
def test_python_c_parity_gates_through_native():
    """The collapse + duplication gates still pass with the C lattice path live
    (end-to-end on the native peer)."""
    assert _native.has_native_riemann_theta_g5()
    assert _t0().collapse_g4_lattice_matches(2) is True
    assert _t0().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG5.duplication_holds(1)


def test_pure_python_oracle_alone_passes_gates(pure_riemann_theta):
    """The COMPLETE pure-Python body alone passes every gate (so the carrier is correct
    on a no-C host) — the native path is FORCED OFF (rc106: every
    ``has_native_riemann_theta*`` gate monkeypatched False + record-and-raise
    sentinels on the ``riemann_theta*_c`` bindings; a native hit fails loudly.
    Before rc106 this test carried NO monkeypatch — on a native host it re-ran the
    dispatched path a second time under a pure-sounding name; on a no-C host it
    duplicated the primary gates byte-for-byte). Same windows as before — the
    duplication gate at its validated minimum box 1 (THE g5 gate, kept complete
    pure)."""
    assert _t0().lattice(2) == _t0()._lattice_py(2)   # dispatch fell to the oracle
    assert _t0().collapse_g4_lattice_matches(2) is True
    assert _t0().collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG5.duplication_holds(1)
    assert pure_riemann_theta == []      # no native symbol was ever reached


# ── gate (g): the documented GENUINELY-OPEN genus-5 Schottky frontier ─────────
def test_schottky_g5_decision_is_documented_open():
    """The genus-5 frontier is documented as the GENUINELY-OPEN operand-side OPEN: codim J₅
    = 3 in A₅ (dim A₅ = 15, dim J₅ = 12) — NOT a hypersurface, so NO single modular form
    cuts J_g (none is known to exist); only the over-inclusive Andreotti–Mayer N₁ /
    Schottky–Jung superset + the non-effective KP/Shiota characterization exist. The
    framework refuses to fabricate a numerical Jacobian verdict. NO is_jacobian /
    schottky_form_g5 / jacobian_verdict is built (the decision is the genuine OPEN)."""
    s = RiemannThetaG5.schottky_g5_decision_is_open()
    assert isinstance(s, str)
    assert s.startswith("OPEN")
    assert "g ≥ 5" in s
    assert "CODIMENSION 15 − 12 = 3" in s
    assert "dim A₅ = g(g+1)/2 = 15" in s
    assert "dim J₅ = dim M₅ = 3g−3 = 12" in s
    assert "NOT a hypersurface" in s
    assert "Andreotti–Mayer" in s
    assert "Schottky–Jung" in s
    assert "Shiota" in s
    assert "θ⁴(E₈⊕E₈) − θ⁴(E₁₆)" in s   # the contrast with the (existing) g4 form
    # NO numerical Schottky / Jacobian verdict method, and NO g5 form is built
    assert not hasattr(RiemannThetaG5, "is_jacobian")
    assert not hasattr(RiemannThetaG5, "schottky_form_g5")
    assert not hasattr(RiemannThetaG5, "jacobian_verdict")


def test_singular_even_null_is_the_empty_set_characteristic():
    """The distinguished SINGULAR even null is the empty-set characteristic [0⁵;0⁵] — the
    one that collapses to the genus-4 trivial null and on to θ₃."""
    sing = RiemannThetaG5.singular_even_null()
    assert sing.characteristic == ((0, 0, 0, 0, 0), (0, 0, 0, 0, 0))
    assert sing.is_even
    assert sing in RiemannThetaG5.even_characteristics()


# ── input validation + identity ───────────────────────────────────────────────
def test_construction_rejects_bad_characteristic_bits():
    with pytest.raises(ValueError):
        RiemannThetaG5(2, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannThetaG5(0, -1, 0, 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        RiemannThetaG5.theta_constant((0, 0, 0, 0, 0), (0, 0, 0, 0, 3))


def test_lattice_rejects_bad_box():
    with pytest.raises(ValueError):
        _t0().lattice(-1)


def test_equality_and_hash():
    assert (RiemannThetaG5(1, 0, 1, 0, 1, 1, 0, 1, 0, 1)
            == RiemannThetaG5(1, 0, 1, 0, 1, 1, 0, 1, 0, 1))
    assert (RiemannThetaG5(1, 0, 1, 0, 1, 1, 0, 1, 0, 1)
            != RiemannThetaG5(0, 0, 1, 0, 1, 1, 0, 1, 0, 1))
    assert len({RiemannThetaG5(1, 0, 1, 0, 1, 1, 0, 1, 0, 1),
                RiemannThetaG5(1, 0, 1, 0, 1, 1, 0, 1, 0, 1)}) == 1
    # the genus-5 carrier is not equal to a genus-4 / genus-3 / genus-2 carrier
    assert RiemannThetaG5(0, 0, 0, 0, 0, 0, 0, 0, 0, 0) != RiemannThetaG4(0, 0, 0, 0, 0, 0, 0, 0)
    assert RiemannThetaG5(0, 0, 0, 0, 0, 0, 0, 0, 0, 0) != RiemannThetaG3(0, 0, 0, 0, 0, 0)


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
