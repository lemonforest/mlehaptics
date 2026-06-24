"""F929 — the OPEN/infer ROUTER (``srmech.amsc.dispatch.infer``).

The meta-dispatcher that makes srmech's three shipped closed-form
reduction-theory rows (cyclic / spectral / Σ) ONE callable. Given an arbitrary
STORED RELATIONSHIP (a descriptor dict), ``infer`` DETECTS which row's structure
the relationship matches, TRIES the matching shipped reducer AND VERIFIES it
actually reduced (reads the reducer's OWN verification), and returns the verified
closed form — else an honest ``OPEN``. It composes the EXISTING verified reducers
(``the_one`` / ``resonant_spectrum`` / ``telescope`` = gosper/zeilberger/
wz_certificate) — NO new math.

The POINT of the OPEN residue: ``infer`` NEVER returns ``reducible: True`` for a
reduction it did not verify — the executable no-magic-numbers / no-hallucination
discipline. This test pins exactly that.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it
uses only the srmech carriers + plain Python arithmetic + ``fractions.Fraction``.

Coverage:
  (a) a graph relationship → routes to SPECTRAL, verified, closed_form is the
      spectrum (tensions/modes/force_orders/resonances);
  (b) the definite sum Σ_k C(n,k)=2ⁿ → routes to Σ, runs wz_certificate, returns
      verified:True;
  (c) a cyclic relationship (σ, θ) → routes to CYCLIC, builds the One;
  (d) an unrecognizable / non-reducible input → honest OPEN (reducible:False, a
      reason, a candidate hint) — and the router NEVER returns reducible:True
      without the reducer's verification actually being True.
"""

from fractions import Fraction

import pytest

from srmech.amsc.dispatch import infer
from srmech.amsc.poly import Poly
from srmech.amsc.zeilberger import BiPoly


# ── the canonical Σ-row term-ratios for Σ_k C(n,k) = 2ⁿ ──────────────────────
# F(n,k)=C(n,k)/2ⁿ (Σ_k F=1): r_n=(n+1)/(2(n+1−k)), r_k=(n−k)/(k+1).
# (Same operands as test_wz_certificate_rc43._ratios_binomial.)
def _ratios_binomial():
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])                          # n+1
    rn_den = BiPoly([Poly.from_coeffs([2, 2]), Poly.from_coeffs([-2])])  # 2(n+1) − 2k
    rk_num = BiPoly([Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])])  # n − k
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])      # k + 1
    return rn_num, rn_den, rk_num, rk_den


# ===========================================================================
# (a) the SPECTRAL row — a graph relationship routes + verifies.
# ===========================================================================

def test_spectral_row_from_edges_verifies():
    """A graph (edges) relationship → SPECTRAL row, resonant_spectrum, verified.
    The closed form IS the spectrum (tensions ascending, modes, force_orders,
    resonances)."""
    # A path graph P4: 0—1—2—3 (the §75 P4 exemplar; spectrum [0, 0.586, 2, 3.414]).
    rel = {"edges": [(0, 1), (1, 2), (2, 3)], "n": 4}
    out = infer(rel)
    assert out["reducible"] is True
    assert out["row"] == "spectral"
    assert out["reducer"] == "resonant_spectrum"
    assert out["verified"] is True
    spec = out["closed_form"]
    assert set(spec.keys()) == {"tensions", "modes", "force_orders", "resonances"}
    tens = spec["tensions"]
    # ascending; the smallest tension of a connected Laplacian is the 0 mode.
    vals = [float(tens[i]) for i in range(tens.shape[0])]
    assert vals == sorted(vals)
    assert vals[0] < 1e-9                      # the connected-graph zero mode
    assert len(spec["force_orders"]) == 2      # [L, L²]


def test_spectral_row_explicit_tag_and_adjacency():
    """An explicit row='spectral' tag + an adjacency payload routes the same way."""
    # Triangle adjacency (3-cycle): every off-diagonal 1.
    adj = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]
    out = infer({"row": "spectral", "adjacency": adj})
    assert out["reducible"] is True
    assert out["row"] == "spectral"
    assert out["verified"] is True


def test_spectral_row_explicit_laplacian_matrix():
    """An explicit 'laplacian' matrix payload (already a Laplacian) routes."""
    # P3 Laplacian directly: 0—1—2.
    lap = [[1.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 1.0]]
    out = infer({"laplacian": lap})
    assert out["reducible"] is True
    assert out["row"] == "spectral"
    assert out["verified"] is True


# ===========================================================================
# (b) the Σ row — the definite sum Σ_k C(n,k)=2ⁿ → wz_certificate, verified.
# ===========================================================================

def test_sigma_row_binomial_identity_verifies():
    """Σ_k C(n,k)=2ⁿ given by its four term-ratios → Σ row, wz_certificate,
    verified:True. The closed_form carries the verified WZ certificate."""
    rn_num, rn_den, rk_num, rk_den = _ratios_binomial()
    rel = {"rn_num": rn_num, "rn_den": rn_den, "rk_num": rk_num, "rk_den": rk_den}
    out = infer(rel)
    assert out["reducible"] is True
    assert out["row"] == "sigma"
    assert out["reducer"] == "wz_certificate"
    assert out["verified"] is True
    cf = out["closed_form"]
    # the reducer's OWN verification flag is the gate the router trusted.
    assert cf["verified"] is True
    assert set(cf["certificate"].keys()) == {"num", "den"}


def test_sigma_row_explicit_tag():
    """An explicit row='sigma' tag routes a definite sum to the Σ reducers."""
    rn_num, rn_den, rk_num, rk_den = _ratios_binomial()
    out = infer({"row": "sigma", "rn_num": rn_num, "rn_den": rn_den,
                 "rk_num": rk_num, "rk_den": rk_den})
    assert out["reducible"] is True
    assert out["row"] == "sigma"
    assert out["verified"] is True


def test_sigma_row_gosper_indefinite():
    """An indefinite term-ratio (single-variable) → Σ row via gosper. The sum
    Σ k has term-ratio t(k+1)/t(k)=(k+1)/k for t(k)=k, which IS Gosper-summable."""
    # t(k) = k : ratio (k+1)/k. gosper returns a rational certificate.
    rel = {"term_ratio_num": Poly.from_coeffs([1, 1]),   # k + 1
           "term_ratio_den": Poly.from_coeffs([0, 1])}   # k
    out = infer(rel)
    assert out["reducible"] is True
    assert out["row"] == "sigma"
    assert out["reducer"] == "gosper"
    assert out["verified"] is True


# ===========================================================================
# (c) the CYCLIC row — a (σ, θ) relationship → the_one.
# ===========================================================================

def test_cyclic_row_the_one_verifies():
    """A cyclic relationship (sigma + theta_num) → CYCLIC row, the_one, verified.
    The closed form IS the One S(σ,θ) with the (1,3,7,3) substrate partition."""
    out = infer({"sigma": 1, "theta_num": 0, "theta_den": 1})
    assert out["reducible"] is True
    assert out["row"] == "cyclic"
    assert out["reducer"] == "the_one"
    assert out["verified"] is True
    one = out["closed_form"]
    assert one.partition == (1, 3, 7, 3)
    assert one.plane_counts == (0, 1, 3)
    assert one.dim == 14


def test_cyclic_row_explicit_tag_with_period():
    """An explicit row='cyclic' tag + a 'period' payload (used as θ) routes."""
    out = infer({"row": "cyclic", "sigma": -1, "period": 3})
    assert out["reducible"] is True
    assert out["row"] == "cyclic"
    assert out["verified"] is True
    assert out["closed_form"].sigma == -1


def test_cyclic_row_bad_sigma_is_open_not_crash():
    """A cyclic-tagged relationship with an invalid σ (not ±1) → honest OPEN,
    never a crash and never a false reducible:True."""
    out = infer({"row": "cyclic", "sigma": 5, "theta_num": 1})
    assert out["reducible"] is False
    assert out["row"] is None
    assert "candidate_next_theory" in out


# ===========================================================================
# (d) the OPEN residue — unrecognizable input + the anti-hallucination guarantee.
# ===========================================================================

def test_unrecognizable_input_is_honest_open():
    """An input matching NO row → honest OPEN: reducible:False, a reason, and a
    candidate next-theory hint (the no-magic-numbers residue made executable)."""
    out = infer({"flavor": "strawberry", "count": 7})
    assert out["reducible"] is False
    assert out["row"] is None
    assert out["reason"] == "not reducible in current vocabulary"
    assert isinstance(out["candidate_next_theory"], str)
    assert out["candidate_next_theory"]          # non-empty honest hint


def test_explicit_unknown_tag_is_open():
    """An explicit but UNKNOWN row tag → honest OPEN (we never guess a reducer
    for a row we don't have)."""
    out = infer({"row": "topological_field_theory", "edges": [(0, 1)]})
    assert out["reducible"] is False
    assert out["row"] is None


def test_sigma_non_wz_summable_is_open():
    """A Σ-tagged relationship whose term is NOT WZ-summable (wz_certificate
    returns None) → honest OPEN — the router does NOT fabricate a reduction.
    The harmonic-like ratio r_n=r_k=1 makes a non-constant raw sum (no WZ cert)."""
    one = BiPoly([Poly.from_coeffs([1])])
    out = infer({"row": "sigma", "rn_num": one, "rn_den": one,
                 "rk_num": one, "rk_den": one})
    assert out["reducible"] is False
    assert out["row"] is None
    assert "candidate_next_theory" in out


def test_gosper_non_summable_is_open():
    """An indefinite term with NO hypergeometric closed form (the harmonic
    t(k)=1/k, ratio k/(k+1), gosper→None) → honest OPEN."""
    rel = {"term_ratio_num": Poly.from_coeffs([0, 1]),   # k
           "term_ratio_den": Poly.from_coeffs([1, 1])}   # k + 1
    out = infer(rel)
    assert out["reducible"] is False
    assert out["row"] is None


def test_router_never_claims_reducible_without_verification():
    """The ANTI-HALLUCINATION guarantee: across a battery of inputs, the router
    NEVER returns reducible:True unless verified is True AND the underlying
    reducer's OWN verification actually holds."""
    rn_num, rn_den, rk_num, rk_den = _ratios_binomial()
    cases = [
        # verified-reducible cases:
        {"edges": [(0, 1), (1, 2), (2, 3)], "n": 4},                       # spectral
        {"rn_num": rn_num, "rn_den": rn_den,
         "rk_num": rk_num, "rk_den": rk_den},                              # sigma/wz
        {"sigma": 1, "theta_num": 1, "theta_den": 2},                      # cyclic
        # OPEN cases:
        {"nonsense": 1},                                                   # no row
        {"row": "sigma", "rn_num": BiPoly([Poly.from_coeffs([1])]),
         "rn_den": BiPoly([Poly.from_coeffs([1])]),
         "rk_num": BiPoly([Poly.from_coeffs([1])]),
         "rk_den": BiPoly([Poly.from_coeffs([1])])},                       # not WZ
        {"row": "cyclic", "sigma": 99},                                    # bad σ
    ]
    for rel in cases:
        out = infer(rel)
        if out["reducible"] is True:
            # the invariant: a True reduction ALWAYS carries verified:True AND a
            # named row + reducer + a closed form. There is no other True path.
            assert out["verified"] is True
            assert out["row"] in ("spectral", "sigma", "cyclic")
            assert out["reducer"] in ("resonant_spectrum", "wz_certificate",
                                      "gosper", "zeilberger", "the_one")
            assert out["closed_form"] is not None
            # and the reducer's own verification, where it exposes one, is True.
            cf = out["closed_form"]
            if isinstance(cf, dict) and "verified" in cf:
                assert cf["verified"] is True
        else:
            # OPEN is always honest: a reason + a candidate hint, row=None.
            assert out["row"] is None
            assert out["reason"] == "not reducible in current vocabulary"
            assert out["candidate_next_theory"]


def test_infer_rejects_non_dict():
    """A non-dict relationship is a contract error (TypeError), not a silent OPEN."""
    with pytest.raises(TypeError):
        infer([("edges", [(0, 1)])])


# ===========================================================================
# numpy-free + math-free self-check (this test must run numpy-ABSENT).
# ===========================================================================

def test_module_is_numpy_and_math_free():
    """The router source imports neither numpy nor math (the §2 discipline)."""
    import re

    import srmech.amsc.dispatch as d
    src = d.__file__
    with open(src, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    # the Class-K discipline: no bare abs() CALL in the source. The prose form
    # ``abs()`` (empty parens — a discipline reference in a docstring/comment) is
    # fine; a real call ``abs(<arg>)`` always has a non-``)`` char after the paren.
    assert re.search(r"abs\([^)]", text) is None
