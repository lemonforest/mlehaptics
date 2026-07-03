"""rc76 — Igusa's χ₁₈ on ``srmech.amsc.riemann_theta.RiemannThetaG3``.

The genus-3 hyperelliptic / vanishing-theta-null structure, realized as Igusa's χ₁₈ —
the weight-18 degree-3 Siegel cusp form DEFINED AS THE PRODUCT OF ALL 36 EVEN
THETA-CONSTANTS (theta-nulls). χ₁₈ ∈ S₁₈(Γ₃), each θ-null weight ½ → 36·½ = 18; its
divisor is H₃ + 2D (H₃ the hyperelliptic locus, D the divisor at infinity), so χ₁₈
vanishes EXACTLY on the genus-3 hyperelliptic locus (Bernatska–Kopeliovich,
arXiv:2306.14889, p.1, the exact sequence ``0 → χ₁₈𝔄(Γ₃) → 𝔄(Γ₃) →^ρ 𝒮(2,8)`` with
"χ₁₈ the cusp form of weight 18, defined as the product of all even theta constants";
van der Geer, *SMF Degree 2&3 + Invariant Theory*). An extension of the rc75
``RiemannThetaG3`` carrier; a pure CARRIER (classmethods on the Ω-universal formal
object), so ``tools.total`` is UNCHANGED — these tests assert ONLY the carrier's own
gates.

The build gates (the no-shell proof):

  (1) **χ₁₈ exact construction:** ``chi18_leading_part`` is the exact formal q-series
      leading part = product of the 36 even theta-nulls; NONZERO, correct/documented
      leading q-order (48 quarter-nome units = 12 in qᵢ, the cusp-vanishing structure),
      product of EXACTLY 36 even nulls (each a genuine even null). Exact-ℚ/int,
      numpy-free.
  (2) **Combinatorics:** the 36-even ↔ partition / even_null enumeration consistent with
      rc75 (36 even, singular = empty-set char); leading order decomposes as the
      wt(ε')-sum 0·8 + 1·12 + 2·12 + 3·4 = 48.
  (3) **Honest OPEN preserved:** ``hyperelliptic_locus_is_open`` references χ₁₈
      explicitly + returns the OPEN string; NO numerical hyperelliptic decision is built.
  (4) **No regression:** all rc72/73/74 genus-2 gates + rc75 genus-3 gates still pass
      exactly.
  (5) Python==C parity EXACT on χ₁₈ (guarded by native skip).
  (6) the carrier source has no numpy / math / abs() (the ratchet).
"""
from __future__ import annotations

import os
import re
import tokenize

import pytest

from srmech.amsc.riemann_theta import RiemannTheta, RiemannThetaG3
from srmech.amsc import _native


THETA3_Q20 = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0]


# ── gate (1): χ₁₈ exact construction (product of the 36 even theta-nulls) ─────
def test_chi18_is_product_of_exactly_36_even_nulls():
    """Igusa's χ₁₈ = ∏ over the 36 even theta-nulls (each weight ½ → 36·½ = 18). The
    factor list is exactly the 36 even genus-3 theta-constants, every one even, and it
    contains the distinguished singular even null (empty-set char) — Bernatska–Kopeliovich
    arXiv:2306.14889 p.1; van der Geer SMF Degree 2&3 + Invariant Theory."""
    factors = RiemannThetaG3.chi18_even_null_factors()
    assert len(factors) == 36
    assert all(f.is_even for f in factors)
    assert RiemannThetaG3.singular_even_null() in factors
    assert factors == RiemannThetaG3.even_characteristics()
    assert RiemannThetaG3.chi18_factor_count_is_36_even() is True


def test_chi18_leading_part_is_nonzero():
    """χ₁₈ is a NONZERO formal q-series — its leading-order part is non-empty with a
    nonzero coefficient (the 36-even-null product does NOT cancel at leading order). So
    χ₁₈ ≢ 0 (a genuine weight-18 cusp form, not the zero form)."""
    lead = RiemannThetaG3.chi18_leading_part()
    assert lead
    assert any(v != 0 for v in lead.values())
    assert RiemannThetaG3.chi18_is_nonzero() is True


def test_chi18_leading_q_order_is_48_quarter_12_nome():
    """The EXACT leading (minimal) diagonal q-order of χ₁₈ = 48 quarter-nome units = 12
    in the diagonal nome qᵢ (= Qᵢ⁴) — the cusp-vanishing structure. Every monomial of
    the leading part sits at diagonal quarter-order A₁+A₂+A₃ = 48."""
    assert RiemannThetaG3.chi18_leading_order_quarter() == 48
    assert RiemannThetaG3.chi18_leading_order_nome() == 12
    assert RiemannThetaG3.chi18_leading_part_is_at_order_48() is True
    lead = RiemannThetaG3.chi18_leading_part()
    assert all(k[0] + k[1] + k[2] == 48 for k in lead)


def test_chi18_leading_part_is_exact_integer_and_box_independent():
    """The χ₁₈ leading part is an exact-integer lattice (every coeff a nonzero int) and
    is box-independent for box ≥ 1 (the leading slice does not change with the
    truncation box) — the no-shell, well-defined exact object."""
    lead2 = RiemannThetaG3.chi18_leading_part(2)
    lead3 = RiemannThetaG3.chi18_leading_part(3)
    assert lead2 == lead3
    for key, v in lead2.items():
        assert len(key) == 6
        assert all(isinstance(x, int) for x in key)
        assert isinstance(v, int) and v != 0


def test_chi18_leading_part_derives_from_the_even_nulls():
    """The χ₁₈ leading part GENUINELY derives from the product of the 36 even-null
    lattices (not a hardcoded table): convolving the 36 nulls' own minimal-diagonal
    slices reproduces it exactly."""
    import collections
    prod = {(0, 0, 0, 0, 0, 0): 1}
    for rt in RiemannThetaG3.even_characteristics():
        lat = rt.lattice(2)
        mn = min(k[0] + k[1] + k[2] for k in lat)
        slc = {k: v for k, v in lat.items() if k[0] + k[1] + k[2] == mn}
        nxt = collections.defaultdict(int)
        for k1, v1 in prod.items():
            for k2, v2 in slc.items():
                key = tuple(k1[i] + k2[i] for i in range(6))
                nxt[key] += v1 * v2
        prod = {k: v for k, v in nxt.items() if v != 0}
    assert prod == RiemannThetaG3.chi18_leading_part()


# ── gate (2): combinatorics (36 even ↔ partition; the wt(ε')-sum) ─────────────
def test_chi18_leading_order_is_the_weight_sum_over_36_evens():
    """The leading diagonal quarter-order = Σ wt(ε') over the 36 even nulls (each null's
    minimal diagonal order is wt(ε'), the number of set bits of ε'). The distribution is
    8 nulls of wt 0, 12 of wt 1, 12 of wt 2, 4 of wt 3 → 0·8 + 1·12 + 2·12 + 3·4 = 48 —
    the exact 36-even ↔ partition combinatorics."""
    dist = {0: 0, 1: 0, 2: 0, 3: 0}
    total = 0
    for rt in RiemannThetaG3.even_characteristics():
        (ep1, ep2, ep3), _ = rt.characteristic
        w = ep1 + ep2 + ep3
        dist[w] += 1
        total += w
    assert dist == {0: 8, 1: 12, 2: 12, 3: 4}
    assert total == 48
    assert total == RiemannThetaG3.chi18_leading_order_quarter()


def test_chi18_combinatorics_consistent_with_rc75():
    """The χ₁₈ even-null factors are exactly the rc75 even enumeration (36 even, 28 odd;
    the singular even null is the empty-set characteristic)."""
    assert RiemannThetaG3.even_null_count() == (36, 28)
    assert len(RiemannThetaG3.chi18_even_null_factors()) == 36
    assert RiemannThetaG3.singular_even_null().characteristic == ((0, 0, 0), (0, 0, 0))


# ── gate (3): the honest OPEN preserved + now names χ₁₈ explicitly ────────────
def test_hyperelliptic_locus_open_references_chi18_and_no_numerical_decision():
    """The hyperelliptic-locus decision STAYS the documented operand-side OPEN, now
    NAMED EXPLICITLY as χ₁₈ (the form whose transcendental vanishing decides it). NO
    numerical hyperelliptic / χ₁₈-vanishing decision is built."""
    s = RiemannThetaG3.hyperelliptic_locus_is_open()
    assert isinstance(s, str)
    assert s.startswith("OPEN")
    assert "χ₁₈" in s                                  # names Igusa's χ₁₈ explicitly
    assert "H₃ + 2D" in s                              # the divisor
    assert "even theta-null" in s.lower()
    assert "NON-hyperelliptic" in s
    assert "plane quartic" in s
    assert "g ≥ 4" in s                                # Schottky frontier stays at g ≥ 4
    # NO numerical hyperelliptic / chi18-vanishing verdict method is built
    assert not hasattr(RiemannThetaG3, "is_hyperelliptic")
    assert not hasattr(RiemannThetaG3, "chi18_vanishes")
    assert not hasattr(RiemannThetaG3, "chi18_evaluate")


# ── gate (4): NO REGRESSION — rc72/73/74 genus-2 + rc75 genus-3 gates ─────────
def test_no_regression_rc72_73_74_genus2_gates():
    """The χ₁₈ extension does not regress the genus-2 carrier — CHEAP structural
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


def test_no_regression_rc75_genus3_gates():
    """The rc75 genus-3 gates (collapse g3→g2, duplication, even-null count) still pass
    exactly."""
    t000 = RiemannThetaG3.theta_constant((0, 0, 0), (0, 0, 0))
    assert t000.collapse_g2() == RiemannTheta(0, 0, 0, 0)
    assert t000.collapse_g2_lattice_matches(4) is True
    assert t000.collapse_g1_q_series(20) == THETA3_Q20
    assert RiemannThetaG3.duplication_holds(3)
    assert RiemannThetaG3.even_null_count() == (36, 28)


# ── gate (5): Python==C parity on χ₁₈ ─────────────────────────────────────────
@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_chi18(),
                    reason="native srmech_riemann_theta_g3_chi18 not loaded")
def test_python_c_parity_chi18_leading_part():
    """The native χ₁₈ peer and the pure-Python oracle emit the BYTE-IDENTICAL canonical
    exact-integer leading-part lattice (do NOT trust the C — compare)."""
    for box in (1, 2, 3):
        c_path = _native.riemann_theta_g3_chi18_c(box)
        py_path = RiemannThetaG3._chi18_leading_part_py(box)
        assert c_path == py_path, box
        # the dispatched method (uses C when present) equals the oracle too
        assert RiemannThetaG3.chi18_leading_part(box) == py_path, box


@pytest.mark.skipif(not _native.has_native_riemann_theta_g3_chi18(),
                    reason="native srmech_riemann_theta_g3_chi18 not loaded")
def test_python_c_parity_chi18_gates_through_native():
    """The χ₁₈ gates still pass with the C lattice path live (end-to-end on the native
    peer)."""
    assert _native.has_native_riemann_theta_g3_chi18()
    assert RiemannThetaG3.chi18_is_nonzero() is True
    assert RiemannThetaG3.chi18_leading_part_is_at_order_48() is True
    assert RiemannThetaG3.chi18_leading_order_quarter() == 48


def test_pure_python_oracle_alone_passes_chi18_gates():
    """The COMPLETE pure-Python body alone passes every χ₁₈ gate (so the carrier is
    correct on a no-C host)."""
    py = RiemannThetaG3._chi18_leading_part_py(2)
    assert py
    assert all(k[0] + k[1] + k[2] == 48 for k in py)
    assert any(v != 0 for v in py.values())


# ── input validation ─────────────────────────────────────────────────────────
def test_chi18_rejects_bad_box():
    with pytest.raises(ValueError):
        RiemannThetaG3.chi18_leading_part(0)
    with pytest.raises(ValueError):
        RiemannThetaG3._chi18_leading_part_py(-1)


# ── gate (6): the carrier source is numpy / math / abs() free ────────────────
def test_riemann_theta_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "riemann_theta.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None        # no bare abs() CALL
    assert "float(" not in text                         # no float in the carrier body
