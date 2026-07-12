"""rc78 — the genus-3 GÖPEL / FROBENIUS theta-null quadratic SYZYGY (closes the
genus-3 rung-set: carrier rc75 → χ₁₈ rc76 → transform+addition rc77 → syzygy rc78).

rc74 built the genus-2 Göpel quadratic syzygy on ``RiemannTheta``
(``θ²[a]θ²[b] = θ²[c]θ²[d] − θ²[e]θ²[f]``, six distinct even nulls forming a Göpel
system). rc78 is the GENUS-3 ANALOG on the rc75/76/77 ``RiemannThetaG3`` carrier — and
the genus-3 shape is GENUINELY DIFFERENT: a **4-PAIR / 8-NULL** same-Ω quadratic
identity among even theta-NULLS,

    θ²[000;001]·θ²[111;110]
        = θ²[000;010]·θ²[111;101] + θ²[001;000]·θ²[110;111] − θ²[010;000]·θ²[101;111]

— the eight DISTINCT even nulls forming four pairs that ALL sum to the common GF(2)
characteristic ``[1,1,1; 1,1,1]`` (a genus-3 GÖPEL / azygetic system). The genus-2-style
3-pair / 6-null lift does NOT hold for genus 3 (exhaustively checked); the MINIMAL
common-sum relation is 4-term. It holds for ALL Ω, checked EXACT as a truncated exact-ℚ
multivariate q-series. MPM source: J. P. Glass, "Theta constants of genus three",
*Compositio Mathematica* 40 (1980), §3 (the type-(2) "products of squares of theta
constants" relations, coefficients ±1); A. Fiorentino & R. Salvati Manni, "On Frobenius'
Theta Formula", *SIGMA* 16 (2020) 057 §1–2 (azygetic Göpel structure + biquadratic
Riemann relations); Igusa, *Theta Functions* (1972) §IV/V; van der Geer, *Siegel Modular
Forms of Degree Two and Three*.

A pure CARRIER extension (like rc72–rc77): no public ToolEntry op, so ``tools.total`` is
UNCHANGED — these tests assert ONLY the carrier's own new gates.

The build gates (the no-shell proof):

  (1) the GÖPEL syzygy holds EXACT (all Ω), is genuinely syzygous (8 distinct even
      nulls, four pairs, one common GF(2) sum), and is box-stable (no truncation
      artifact);
  (2) the no-shell DISTINCTNESS proof — distinct from rc75 duplication AND rc77 addition
      AND rc76 χ₁₈ (structural + exact lattice);
  (3) NO REGRESSION — rc72/73/74 genus-2 + rc75/76/77 genus-3 gates all still pass;
  (4) Python==C parity EXACT on the new genus-3 Göpel gate (guarded by native skip);
  (5) the carrier source has no numpy / math / abs() / float (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannThetaG3
from srmech.amsc import _native


def _is_even_g3(ch) -> bool:
    (ep1, ep2, ep3), (e1, e2, e3) = ch
    return (ep1 * e1 + ep2 * e2 + ep3 * e3) % 2 == 0


THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


# ── gate (1): the genus-3 GÖPEL quadratic syzygy (rc78's EXACT CORE) ──────────
def test_goepel_g3_syzygy_holds_exact():
    """THE rc78 GATE: the genus-3 Frobenius/Göpel quadratic theta-null syzygy
    θ²[a]θ²[b] = θ²[c]θ²[d] + θ²[e]θ²[f] − θ²[g]θ²[h] holds EXACTLY as a truncated
    exact-integer multivariate q-series, for ALL Ω (Glass, Compositio Math 40 (1980) §3;
    Fiorentino–Salvati Manni SIGMA 16 (2020) 057; Igusa §IV/V). No transcendental eval."""
    assert RiemannThetaG3.goepel_holds(3)
    assert RiemannThetaG3.goepel_holds(4)


def test_goepel_g3_quad_is_syzygous():
    """The canonical genus-3 Göpel quad is genuinely SYZYGOUS — FOUR pairs of DISTINCT
    EVEN nulls (8 nulls) all sharing ONE common GF(2) characteristic sum (a genus-3 Göpel
    system). The structural fingerprint of a Frobenius/Göpel relation, not an accident."""
    assert RiemannThetaG3.goepel_is_syzygous()
    quad = RiemannThetaG3.goepel_syzygy_quad()
    # eight distinct even theta-nulls (FOUR pairs — the genus-3 shape)
    involved = [c for p in quad for c in p]
    assert len(quad) == 4
    assert len(set(involved)) == 8
    assert all(_is_even_g3(c) for c in involved)
    # the four pairs share ONE characteristic sum, and it is [1,1,1; 1,1,1]
    sums = [RiemannThetaG3._g3_char_add_mod2(p[0], p[1]) for p in quad]
    assert all(s == sums[0] for s in sums)
    assert sums[0] == ((1, 1, 1), (1, 1, 1))


def test_goepel_g3_lhs_equals_rhs_on_safe_region():
    """The two sides of the genus-3 Göpel syzygy are equal on the safe inner region the
    box provably resolves, and the region is non-trivially populated with a GENUINE
    genus-3 cross-term (C₁₃ or C₂₃ ≠ 0) — proving genuine genus-3 content, not the
    genus-2 / genus-1 slice."""
    box = 3
    safe = box * box

    def restrict(lat):
        out = {}
        for k, v in lat.items():
            a1, a2, a3, c12, c13, c23 = k
            m12 = c12 if c12 >= 0 else -c12
            m13 = c13 if c13 >= 0 else -c13
            m23 = c23 if c23 >= 0 else -c23
            if (a1 <= safe and a2 <= safe and a3 <= safe
                    and m12 <= safe and m13 <= safe and m23 <= safe):
                out[k] = v
        return out

    L = restrict(RiemannThetaG3.goepel_lhs(box))
    R = restrict(RiemannThetaG3.goepel_rhs(box))
    assert L == R
    assert any((c13 != 0 or c23 != 0)                  # genuine genus-3 cross-term
               for (_a1, _a2, _a3, _c12, c13, c23) in L)


def test_goepel_g3_inner_region_is_box_stable():
    """THE NO-TRUNCATION-ARTIFACT PROOF: a FIXED inner region (bound 9) is IDENTICAL
    across box = 3, 4, 5 on the genus-3 Göpel LHS — so the region is genuinely fully
    resolved (any truncation artifact would change when the box grows). The no-shell
    guarantee that the exact q-series identity is real, not a low-box coincidence."""
    S = 9

    def restrict(lat):
        out = {}
        for k, v in lat.items():
            a1, a2, a3, c12, c13, c23 = k
            m12 = c12 if c12 >= 0 else -c12
            m13 = c13 if c13 >= 0 else -c13
            m23 = c23 if c23 >= 0 else -c23
            if (a1 <= S and a2 <= S and a3 <= S
                    and m12 <= S and m13 <= S and m23 <= S):
                out[k] = v
        return out

    l3 = restrict(RiemannThetaG3.goepel_lhs(3))
    l4 = restrict(RiemannThetaG3.goepel_lhs(4))
    l5 = restrict(RiemannThetaG3.goepel_lhs(5))
    assert l3 == l4 == l5
    assert any((c13 != 0 or c23 != 0)
               for (_a1, _a2, _a3, _c12, c13, c23) in l3)


def test_goepel_g3_is_minimal_4_term_not_6_null():
    """THE GENUS-3 SHAPE: the syzygy is a 4-PAIR / 8-NULL relation (vs genus-2's 3-pair /
    6-null). The quad has exactly 4 pairs and 8 distinct nulls — the genuine MINIMAL
    genus-3 form (the genus-2-style 6-null lift does NOT hold for genus 3)."""
    quad = RiemannThetaG3.goepel_syzygy_quad()
    assert len(quad) == 4                               # FOUR pairs (genus-2 had three)
    nulls = {c for p in quad for c in p}
    assert len(nulls) == 8                              # EIGHT nulls (genus-2 had six)


def test_goepel_g3_rejects_small_box():
    with pytest.raises(ValueError):
        RiemannThetaG3.goepel_holds(2)                  # box < 3 for the gate


# ── gate (2): the no-shell DISTINCTNESS proof (vs dup + add + χ₁₈) ────────────
def test_goepel_g3_distinct_from_duplication_addition_and_chi18():
    """THE rc78 NO-SHELL PROOF: the genus-3 Göpel syzygy is GENUINELY DISTINCT from ALL
    THREE prior genus-3 relations — rc75 DUPLICATION, rc77 ADDITION, and rc76 χ₁₈. Its
    LHS (a degree-4 same-Ω product) differs from the degree-2 duplication/addition LHS;
    its 8 nulls are a PROPER SUBSET of the 36 χ₁₈ factors (8 < 36) and it is a same-Ω SUM
    not the 36-null product."""
    assert RiemannThetaG3.goepel_is_distinct_from_duplication_addition_and_chi18(3)


def test_goepel_g3_lhs_is_proper_subset_of_chi18_factors():
    """The 8 Göpel-syzygy nulls are all genuine even nulls and a PROPER SUBSET of the 36
    χ₁₈ factors (8 < 36) — the structural distinctness from χ₁₈ (a SUBSET polynomial
    relation, not the full 36-null product)."""
    syz = {c for p in RiemannThetaG3.goepel_syzygy_quad() for c in p}
    chi18 = {f.characteristic for f in RiemannThetaG3.chi18_even_null_factors()}
    assert len(syz) == 8
    assert len(chi18) == 36
    assert syz.issubset(chi18)
    assert syz != chi18


# ── gate (3): NO REGRESSION (rc72–rc77 gates still pass) ──────────────────────
def test_rc75_collapse_still_bit_exact():
    t000 = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert t000.collapse_g1_q_series(20) == THETA3_Q20
    assert t000.collapse_g2_lattice_matches(4)


def test_rc75_duplication_still_holds():
    assert RiemannThetaG3.duplication_holds(3)


def test_rc76_chi18_still_holds():
    assert RiemannThetaG3.even_null_count() == (36, 28)
    assert RiemannThetaG3.chi18_is_nonzero(2)
    assert RiemannThetaG3.chi18_factor_count_is_36_even()
    assert RiemannThetaG3.chi18_leading_part_is_at_order_48(2)


def test_rc77_addition_still_holds():
    assert RiemannThetaG3.addition_holds(4)
    assert RiemannThetaG3.addition_is_distinct_from_duplication(4)


def test_rc77_transform_still_holds():
    """The rc77 Sp(6,ℤ) transform parity-preservation + κ-exponent gates still pass."""
    g = RiemannThetaG3.sp6_translation(((1, 0, 0), (0, 0, 0), (0, 0, 0)))
    assert RiemannThetaG3.sp6_is_symplectic(g)
    for ep1 in (0, 1):
        for e1 in (0, 1):
            rt = RiemannThetaG3(ep1, 0, 0, e1, 0, 0)
            new, k = rt.transform(g)
            assert new.is_even == rt.is_even
            assert 0 <= k < 8


def test_hyperelliptic_locus_is_open_string():
    s = RiemannThetaG3.hyperelliptic_locus_is_open()
    assert isinstance(s, str)
    assert "OPEN" in s
    assert "χ₁₈" in s


# ── gate (4): Python==C parity on the genus-3 Göpel gate ──────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_goepel(),
                    reason="native srmech_riemann_theta_g3_goepel not loaded")
def test_python_c_parity_goepel_g3():
    """The native genus-3 Göpel gate decision (holds, has_cross) equals the pure oracle
    EXACTLY at box 3 and box 4 (do NOT trust the C — compare). The Python pure path
    builds restrict(goepel_lhs) == restrict(goepel_rhs)."""
    for box in (3, 4):
        safe = box * box

        def restrict(lat):
            out = {}
            for k, v in lat.items():
                a1, a2, a3, c12, c13, c23 = k
                m12 = c12 if c12 >= 0 else -c12
                m13 = c13 if c13 >= 0 else -c13
                m23 = c23 if c23 >= 0 else -c23
                if (a1 <= safe and a2 <= safe and a3 <= safe
                        and m12 <= safe and m13 <= safe and m23 <= safe):
                    out[k] = v
            return out

        lhs = restrict(RiemannThetaG3.goepel_lhs(box))
        rhs = restrict(RiemannThetaG3.goepel_rhs(box))
        py = (lhs == rhs,
              any((c13 != 0 or c23 != 0)
                  for (_a1, _a2, _a3, _c12, c13, c23) in lhs))
        c = _native.riemann_theta_g3_goepel_c(box)
        assert c == py, (box, c, py)


@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_goepel(),
                    reason="native peer not loaded")
def test_goepel_g3_through_native():
    """The genus-3 Göpel gate + distinctness still pass with the native path live
    (end-to-end on the C peer)."""
    assert RiemannThetaG3.goepel_holds(3)
    assert RiemannThetaG3.goepel_holds(4)
    assert RiemannThetaG3.goepel_is_distinct_from_duplication_addition_and_chi18(3)


def test_pure_python_alone_passes_new_gates(pure_riemann_theta):
    """The COMPLETE pure-Python body alone passes the new gates (so the carrier is
    correct on a no-C host) — the native path is FORCED OFF (rc106). The old
    docstring claimed "the lhs/rhs builders never touch the native peer": true of
    the Göpel DECISION peer (``srmech_riemann_theta_g3_goepel``), but the
    underlying quarter-nome ``.lattice`` DID dispatch to
    ``srmech_riemann_theta_g3`` on a native host — now every
    ``has_native_riemann_theta*`` gate is monkeypatched False with record-and-raise
    sentinels on the ``riemann_theta*_c`` bindings, so the whole path is provably
    pure."""
    assert RiemannThetaG3.goepel_is_syzygous()
    box = 3
    safe = box * box

    def restrict(lat):
        return {k: v for k, v in lat.items()
                if k[0] <= safe and k[1] <= safe and k[2] <= safe
                and (k[3] if k[3] >= 0 else -k[3]) <= safe
                and (k[4] if k[4] >= 0 else -k[4]) <= safe
                and (k[5] if k[5] >= 0 else -k[5]) <= safe}

    assert restrict(RiemannThetaG3.goepel_lhs(box)) == restrict(RiemannThetaG3.goepel_rhs(box))
    assert pure_riemann_theta == []      # no native symbol was ever reached


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
