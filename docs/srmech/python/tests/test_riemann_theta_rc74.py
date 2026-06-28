"""rc74 — the GENUS-AXIS CAPSTONE: the Thomae / Rosenhain bridge on ``RiemannTheta``.

rc74 extends the rc72 genus-2 carrier + rc73 transform/addition with the THREE
exact, no-shell pieces of the Thomae/Rosenhain bridge:

  (A) the FROBENIUS / GÖPEL quadratic syzygy among the even theta-NULLS — a GENUINE
      NEW exact relation ``θ²[a]θ²[b] = θ²[c]θ²[d] − θ²[e]θ²[f]`` that holds for ALL
      Ω (the genus-2 specialization of the quartic Riemann theta relation, DLMF
      §21.6.6/§21.6.7; Mumford, Tata Lectures on Theta II; Igusa, Theta Functions
      §IV), checked EXACTLY as a truncated exact-ℚ q-series — and PROVEN genuinely
      DISTINCT from rc72 duplication AND rc73 addition (it is a relation among the
      nulls at the SAME Ω, no Ω-doubling; and it is degree-4 where both
      duplication and addition LHS are degree-2);
  (B) the SYMBOLIC Rosenhain λ-map — the 3 Rosenhain moduli of
      ``y² = x(x−1)(x−λ₁)(x−λ₂)(x−λ₃)`` as FORMAL theta-null RATIOS (Eilers Cor 2.4,
      eq 2.18; the η-map eq 4.4) — represented SYMBOLICALLY (numerator/denominator
      characteristics), NOT as numerical values;
  (C) the documented operand-side OPEN — the NUMERICAL branch-point/λ recovery needs
      the transcendental period map (a string, never a fabricated number).

A pure CARRIER extension (like rc72/rc73): no public ToolEntry op, so ``tools.total``
is UNCHANGED — these tests assert ONLY the carrier's own new gates.

The build gates (the no-shell proof):

  (1) the GÖPEL syzygy holds EXACT (all Ω) AND is provably distinct from
      duplication + addition;
  (2) the symbolic λ-map returns the correct MPM-verified theta-null ratios
      (the right η-map characteristics; all even nulls; three distinct moduli);
  (3) NO REGRESSION — rc72 collapse + duplication, rc73 addition + transform/sp4
      gates all still pass;
  (4) Python==C parity EXACT on the new η-map kernel (guarded by native skip);
  (5) the carrier source has no numpy / math / abs() / float (the ratchet);
  (6) the documented OPEN is a string, never a number.
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta
from srmech.amsc import _native


def _t00() -> RiemannTheta:
    return RiemannTheta.theta_constant((0, 0), (0, 0))


THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


def _is_even(ch) -> bool:
    (ep1, ep2), (e1, e2) = ch
    return (ep1 * e1 + ep2 * e2) % 2 == 0


# ── gate (1): the FROBENIUS / GÖPEL quadratic syzygy (rc74's EXACT CORE) ──────
def test_goepel_syzygy_holds_exact():
    """THE rc74 GATE: the genus-2 Frobenius/Göpel quadratic theta-null syzygy
    θ²[a]θ²[b] = θ²[c]θ²[d] − θ²[e]θ²[f] holds EXACTLY as a truncated exact-integer
    multivariate q-series, for ALL Ω (DLMF §21.6.6/§21.6.7; Mumford, Tata Lectures on
    Theta II; Igusa §IV). No transcendental evaluation."""
    assert RiemannTheta.goepel_holds(4)
    assert RiemannTheta.goepel_holds(5)
    assert RiemannTheta.goepel_holds(6)


def test_goepel_triple_is_syzygous():
    """The canonical Göpel triple is genuinely SYZYGOUS — three pairs of DISTINCT
    EVEN nulls all sharing ONE common GF(2) characteristic sum (a Göpel system). This
    is the structural fingerprint that it is a Frobenius/Göpel relation, not an
    accident."""
    assert RiemannTheta.goepel_is_syzygous()
    triple = RiemannTheta.goepel_syzygy_triple()
    # six distinct even theta-nulls
    involved = [c for p in triple for c in p]
    assert len(set(involved)) == 6
    assert all(_is_even(c) for c in involved)
    # the three pairs share ONE characteristic sum
    sums = [RiemannTheta._char_add_mod2(p[0], p[1]) for p in triple]
    assert sums[0] == sums[1] == sums[2]


def test_goepel_lhs_equals_rhs_on_safe_region():
    """The two sides of the Göpel syzygy are equal on the safe inner region the box
    provably resolves, and the region is non-trivially populated with cross-term
    (C ≠ 0) monomials — proving genuine genus-2 content, not the genus-1 slice."""
    box = 5
    lhs = RiemannTheta.goepel_lhs(box)
    rhs = RiemannTheta.goepel_rhs(box)
    safe = box * box

    def restrict(lat):
        return {(a, b, c): v for (a, b, c), v in lat.items()
                if a <= safe and b <= safe and (c if c >= 0 else -c) <= safe}

    L, R = restrict(lhs), restrict(rhs)
    assert L == R
    assert any(c != 0 for (_a, _b, c) in L)            # genuinely cross-term


def test_goepel_inner_region_is_box_stable():
    """THE NO-TRUNCATION-ARTIFACT PROOF: a FIXED inner region (bound 16) is IDENTICAL
    across box = 4, 5, 6 on the Göpel LHS — so the region is genuinely fully resolved
    (any truncation artifact would change when the box grows). This is the no-shell
    guarantee that the exact q-series identity is real, not a low-box coincidence."""
    S = 16

    def restrict(lat):
        return {(a, b, c): v for (a, b, c), v in lat.items()
                if a <= S and b <= S and (c if c >= 0 else -c) <= S}

    l4 = restrict(RiemannTheta.goepel_lhs(4))
    l5 = restrict(RiemannTheta.goepel_lhs(5))
    l6 = restrict(RiemannTheta.goepel_lhs(6))
    assert l4 == l5 == l6
    assert any(c != 0 for (_a, _b, c) in l4)


def test_goepel_is_genuinely_distinct_from_duplication_and_addition():
    """THE rc74 NO-SHELL PROOF: the Göpel syzygy is GENUINELY DISTINCT from BOTH rc72
    duplication AND rc73 addition. Its LHS (a degree-4 product of squares of two
    DISTINCT even nulls at Ω) is NOT equal to the duplication LHS θ[0;0]² (degree-2)
    nor to ANY addition LHS θ[a]θ[b] (degree-2) — different total theta-degree, and
    no Ω-doubling. So it is the genuine new relation, not a relabel."""
    assert RiemannTheta.goepel_is_distinct_from_duplication_and_addition(4)
    assert RiemannTheta.goepel_is_distinct_from_duplication_and_addition(5)
    # explicit: the Göpel LHS differs from the duplication LHS and every addition LHS
    box = 5
    glhs = RiemannTheta.goepel_lhs(box)
    assert glhs != RiemannTheta.duplication_lhs(box)
    for a1 in (0, 1):
        for a2 in (0, 1):
            for b1 in (0, 1):
                for b2 in (0, 1):
                    assert glhs != RiemannTheta.addition_lhs((a1, a2), (b1, b2), box)


def test_goepel_is_purely_at_omega_not_two_omega():
    """STRUCTURAL distinctness: the Göpel syzygy is built ENTIRELY from theta-nulls
    at Ω (via the rc72 quarter-nome ``.lattice``), with NO ``_double_exps`` /
    eighth-nome-at-2Ω lattice — whereas duplication + addition both relate Ω to 2Ω.
    The Göpel LHS equals the 4-fold convolution of the rc72 Ω-lattices exactly."""
    box = 4
    a, b = RiemannTheta.goepel_syzygy_triple()[0]
    la = RiemannTheta.theta_constant(a[0], a[1]).lattice(box)
    lb = RiemannTheta.theta_constant(b[0], b[1]).lattice(box)
    sa = RiemannTheta._square_lattice(la)
    sb = RiemannTheta._square_lattice(lb)
    direct = RiemannTheta._square_lattice_pair(sa, sb)
    assert direct == RiemannTheta.goepel_lhs(box)


def test_goepel_rejects_small_box():
    with pytest.raises(ValueError):
        RiemannTheta.goepel_holds(3)                    # box < 4 for the gate


# ── gate (2): the SYMBOLIC Rosenhain λ-map (theta-null ratios, NOT numbers) ───
def test_eta_map_six_odd_ten_even():
    """The Eilers η-map (eq 4.4) is internally consistent: the 6 SINGLE branch-point
    indices give the 6 ODD characteristics; the 10 PAIRS of finite indices {1,…,5}
    give the 10 EVEN theta-nulls (10 distinct)."""
    odd = [RiemannTheta.branch_set_characteristic((i,)) for i in range(1, 7)]
    assert len(odd) == 6
    assert all(not _is_even(c) for c in odd)
    even = set()
    for i in range(1, 6):
        for j in range(i + 1, 6):
            even.add(RiemannTheta.branch_set_characteristic((i, j)))
    assert len(even) == 10
    assert all(_is_even(c) for c in even)


def test_riemann_constant_value():
    """The vector of Riemann constants characteristic [K∞] = [𝔄₂]+[𝔄₄]+[𝔄₆] (mod 2)
    in the Eilers Fig.-1 basis is ((1,1),(0,1)) (arXiv:1707.08855, eq 4.3)."""
    assert RiemannTheta.riemann_constant() == ((1, 1), (0, 1))


def test_rosenhain_lambda_map_is_symbolic_theta_null_ratios():
    """The Rosenhain λ-map returns the 3 moduli as FORMAL theta-null RATIOS (Eilers
    Cor 2.4) — each a dict with numerator/denominator EVEN-null characteristics and
    the branch-index data — NOT numerical values. No float anywhere in the result."""
    lam = RiemannTheta.rosenhain_lambda_map()
    assert set(lam) == {"lambda1", "lambda2", "lambda3"}
    for name, obj in lam.items():
        assert set(obj) == {"num", "den", "branch_indices", "cross_ratio"}
        # numerator/denominator are EVEN-null characteristics (theta-null ratios)
        assert len(obj["num"]) == 2 and len(obj["den"]) == 2
        for ch in obj["num"] + obj["den"]:
            assert _is_even(ch), (name, ch)
            # a characteristic is a bit-tuple, NOT a number
            (ep1, ep2), (e1, e2) = ch
            assert all(isinstance(x, int) and x in (0, 1)
                       for x in (ep1, ep2, e1, e2))
        # the cross-ratio is a SYMBOLIC string, never a number
        assert isinstance(obj["cross_ratio"], str)
        assert "e" in obj["cross_ratio"]


def test_rosenhain_lambda_map_is_well_formed():
    """The symbolic λ-map matches the η-map characteristics EXACTLY (no fabricated
    characteristic), every ratio entry is an EVEN null, and the three λᵢ use distinct
    k indices (the three distinct moduli e₃, e₄, e₅)."""
    assert RiemannTheta.rosenhain_lambda_map_is_well_formed()


def test_rosenhain_lambda_characteristics_match_eta_map():
    """Each λᵢ numerator/denominator characteristic is EXACTLY the η-map ε(k,S),
    ε(k,T) / ε(l,S), ε(l,T) for its branch-index data — the no-fabrication check."""
    lam = RiemannTheta.rosenhain_lambda_map()
    for name, obj in lam.items():
        bi = obj["branch_indices"]
        k, l, s, t = bi["k"], bi["l"], bi["S"], bi["T"]
        want_num = [RiemannTheta.branch_set_characteristic((k, s)),
                    RiemannTheta.branch_set_characteristic((k, t))]
        want_den = [RiemannTheta.branch_set_characteristic((l, s)),
                    RiemannTheta.branch_set_characteristic((l, t))]
        assert obj["num"] == want_num, name
        assert obj["den"] == want_den, name


# ── gate (3): NO REGRESSION (rc72 + rc73 gates still pass) ────────────────────
def test_rc72_collapse_still_bit_exact():
    assert _t00().collapse_g1_q_series(20) == THETA3_Q20


def test_rc72_duplication_still_holds():
    assert RiemannTheta.duplication_holds(8)


def test_rc73_addition_still_holds():
    assert RiemannTheta.addition_holds(6)
    assert RiemannTheta.addition_is_distinct_from_duplication(6)


def test_rc73_transform_still_holds():
    """The rc73 Sp(4,ℤ) transform parity-preservation + κ-exponent gates still pass."""
    g = RiemannTheta.sp4_translation(((1, 0), (0, 0)))
    assert RiemannTheta.sp4_is_symplectic(g)
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                for d in (0, 1):
                    rt = RiemannTheta(a, b, c, d)
                    new, k = rt.transform(g)
                    assert new.is_even == rt.is_even
                    assert 0 <= k < 8


# ── gate (4): Python==C parity on the η-map kernel ───────────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_eta(),
                    reason="native srmech_riemann_theta_eta_char not loaded")
def test_python_c_parity_eta_map():
    """The native Eilers η-map equals the pure oracle EXACTLY on all single indices,
    all finite pairs, and the empty set (do NOT trust the C — compare)."""
    # singletons
    for i in range(1, 7):
        c_path = _native.riemann_theta_eta_char_c((i,))
        py_path = RiemannTheta._eta_char_py((i,))
        assert c_path == py_path, i
    # pairs (finite + with ∞)
    for i in range(1, 7):
        for j in range(i + 1, 7):
            c_path = _native.riemann_theta_eta_char_c((i, j))
            py_path = RiemannTheta._eta_char_py((i, j))
            assert c_path == py_path, (i, j)
    # the empty set (= −[K∞] = [K∞])
    assert _native.riemann_theta_eta_char_c(()) == RiemannTheta._eta_char_py(())


@pytest.mark.skipif(not _native.has_native_riemann_theta_eta(),
                    reason="native peer not loaded")
def test_lambda_map_and_goepel_through_native():
    """The λ-map + the Göpel gate still pass with the native η-map path live
    (end-to-end on the C peer)."""
    assert RiemannTheta.rosenhain_lambda_map_is_well_formed()
    assert RiemannTheta.goepel_holds(5)
    assert RiemannTheta.goepel_is_distinct_from_duplication_and_addition(5)


def test_pure_python_alone_passes_new_gates():
    """The COMPLETE pure-Python body alone passes the new gates (so the carrier is
    correct on a no-C host)."""
    assert RiemannTheta.goepel_holds(5)
    assert RiemannTheta.goepel_is_distinct_from_duplication_and_addition(5)
    assert RiemannTheta.rosenhain_lambda_map_is_well_formed()


def test_eta_map_rejects_bad_index():
    with pytest.raises(ValueError):
        RiemannTheta.branch_set_characteristic((0,))   # index 0 out of {1..6}
    with pytest.raises(ValueError):
        RiemannTheta.branch_set_characteristic((7,))   # index 7 out of {1..6}


# ── gate (6): the documented OPEN is honest (a string, never a number) ────────
def test_branch_point_recovery_is_documented_open_not_a_number():
    """The NUMERICAL branch-point / λ recovery is the documented operand-side OPEN
    (transcendental period map) — returned as a STRING, never a fabricated number
    (the rc72 'refuse to fabricate' pattern)."""
    s = RiemannTheta.rosenhain_branch_point_recovery_is_open()
    assert isinstance(s, str)
    assert "OPEN" in s
    assert "transcendental" in s
    assert "period" in s
    # it is NOT a number / numeric container
    assert not isinstance(s, (int, float, complex, list, dict, tuple))


# ── gate (5): the carrier source is numpy / math / abs() / float free ─────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None        # no bare abs() CALL
    assert "float(" not in text                          # no float in the carrier
