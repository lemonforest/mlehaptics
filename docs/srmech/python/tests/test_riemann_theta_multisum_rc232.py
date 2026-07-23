"""rc232 — the HIGHER-GENUS (genus-g Riemann theta) theta-multisum reduction row.

Pins Spiridonov's multiparameter summation formula for genus-g Riemann theta
functions (arXiv:math/0408366, the Theorem, Eq. sum) — the genus-axis lift of the
elliptic (genus-1) Aₙ/Cₙ Jackson rows:

  1. Carrier: the genus-g odd-theta ThetaBracket / ThetaBracketSum (antisymmetry
     [-u] = -[u]; the free commutative ℤ-algebra of bracket products).
  2. The identity verifies (n = 0..5), incl. the genuinely-new g ≥ 2 regime — via
     the Fay trisecant identity (Eq. Fay, the n=0 base) + exact telescoping.
  3. The Fay identity is the load-bearing input: the RAW (free-algebra) residual
     LHS − RHS is NON-zero; only the Fay-reduced LHS telescopes to exactly zero.
  4. Discrimination: a wrong/perturbed closed form is caught (verified is False).
  5. The exact-ℚ telescoping base oracle (the p=0-oracle analogue).
  6. C↔pure parity for both builders (when the native lib is present).
  7. Registration: ToolEntry ×2 (tools.total == 421), Rosetta rows, __all__.
  8. MPM provenance: the source PDF sha256 is lodged in the module docstring.

Exact over the theta-bracket algebra — no float, no abs(), no numpy / math.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from srmech.amsc.ellbase import EllMonomial as E
from srmech.amsc.q import Q
from srmech.amsc import riemann_theta_multisum as R
from srmech.amsc.riemann_theta_multisum import (
    ThetaBracket, ThetaBracketSum, riemann_theta_multisum_lhs,
    multivariate_riemann_theta_sum,
)


def _make(n):
    """The n+1 free vectors z_k + the 4(n+1) distinct points a_k,b_k,c_k,d_k."""
    z = [E.symbol(f"z{k}") for k in range(n + 1)]
    pts = [(E.symbol(f"a{k}"), E.symbol(f"b{k}"), E.symbol(f"c{k}"), E.symbol(f"d{k}"))
           for k in range(n + 1)]
    return z, pts


# ── (1) the carrier ──────────────────────────────────────────────────────────────
def test_v_abelian_integral_antisymmetric_and_additive():
    a, b, c = E.symbol("a"), E.symbol("b"), E.symbol("c")
    assert R._v(a, b).inv() == R._v(b, a)                 # v(a,b) = -v(b,a)
    assert R._v(a, b) * R._v(b, c) == R._v(a, c)          # v(a,b)+v(b,c) = v(a,c)
    assert R._v(a, a).is_unit                             # v(a,a) = 0


def test_odd_theta_antisymmetry_class_k_sign():
    u = E.symbol("a") * E.symbol("b").inv()               # a nonzero argument
    s_pos, u0 = R._odd(u)
    s_neg, u0n = R._odd(u.inv())                          # [-u] = -[u]
    assert u0 == u0n                                       # same canonical rep
    assert s_pos * s_neg == Q(-1, 1)                       # opposite signs (Class-K)
    # a UNIT argument is the zero bracket [0] = 0
    s0, _ = R._odd(E.one())
    assert s0 == Q(0, 1)
    # a zero bracket kills a product
    assert ThetaBracketSum.bracket_product([E.one(), u]).is_zero


def test_bracket_product_and_ring_algebra():
    a, b = E.symbol("a"), E.symbol("b")
    one = ThetaBracketSum.one()
    p = ThetaBracketSum.bracket_product([R._v(a, b)])
    assert one * p == p and p * one == p
    assert (p - p).is_zero
    assert not p.is_zero
    # a bracket-product with a reversed argument is the SIGN-flipped monomial
    q = ThetaBracketSum.bracket_product([R._v(b, a)])
    assert (p + q).is_zero                                 # [v(a,b)] + [v(b,a)] = 0
    assert isinstance(ThetaBracket(R._v(a, b)).arg, E)


# ── (2) the identity verifies through the genus-g regime ─────────────────────────
@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5])
def test_multisum_identity_verifies(n):
    z, pts = _make(n)
    res = multivariate_riemann_theta_sum(z, pts, verify=True)
    assert res["verified"] is True, f"n={n} failed to verify"
    lhs = riemann_theta_multisum_lhs(z, pts)
    assert lhs.n_terms == n + 1                            # n+1 summands
    assert res["closed_form"].n_terms == 2                 # ∏g − ∏h


# ── (3) Fay is the load-bearing input (the n=0 base case) ────────────────────────
def test_fay_is_load_bearing_free_residual_nonzero():
    z, pts = _make(0)
    zz, ptt, nn = R._coerce_operand(z, pts, "x")
    lhs = R._lhs_py(zz, ptt, nn)                           # = L_0
    rhs = R._rhs_py(zz, ptt, nn)                           # = g_0 − h_0
    # WITHOUT Fay, over the free antisymmetric algebra, L_0 ≠ g_0 − h_0:
    assert not (lhs - rhs).is_zero
    # the Fay-reduced LHS DOES telescope to exactly zero against the RHS:
    assert (R._fay_reduce_lhs(zz, ptt, nn) - rhs).is_zero


# ── (4) discrimination ───────────────────────────────────────────────────────────
def test_wrong_closed_form_is_caught():
    z, pts = _make(3)
    zz, ptt, nn = R._coerce_operand(z, pts, "x")
    good = R._rhs_py(zz, ptt, nn)
    assert R._verify_reduction(zz, ptt, nn, good) is True
    bad = good + ThetaBracketSum.bracket_product([E.symbol("z0")])
    assert R._verify_reduction(zz, ptt, nn, bad) is False


# ── (5) the exact-ℚ telescoping base oracle ──────────────────────────────────────
@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5])
def test_telescoping_rational_oracle(n):
    # The telescoping is a RING IDENTITY (holds for ARBITRARY g_k, h_k once
    # L_k = g_k − h_k), so the exact-ℚ oracle confirms it for every assignment —
    # the p=0-oracle analogue proving the skeleton exactly in ℚ (no float).
    gv = [Q(2 * k + 3, 5) for k in range(n + 1)]
    hv = [Q(k + 7, 4) for k in range(n + 1)]
    assert R._telescoping_rational_oracle(gv, hv) is True
    # negatives + a different assignment — still an identity, still exact
    gv2 = [Q(-(k + 1), 3) for k in range(n + 1)]
    hv2 = [Q(2 * k - 5, 7) for k in range(n + 1)]
    assert R._telescoping_rational_oracle(gv2, hv2) is True


# ── (6) C ↔ pure parity (skips cleanly when the native lib is absent) ────────────
@pytest.mark.parametrize("n", [0, 1, 2, 3, 4])
def test_native_parity(n):
    from srmech.amsc import _native as nat
    if not nat.has_native_riemann_theta_multisum():
        pytest.skip("native srmech_riemann_theta_multisum not loaded")
    z, pts = _make(n)
    zz, ptt, nn = R._coerce_operand(z, pts, "x")
    assert R._lhs_c(zz, ptt, nn) == R._lhs_py(zz, ptt, nn)
    assert R._rhs_c(zz, ptt, nn) == R._rhs_py(zz, ptt, nn)


# ── (7) registration: ToolEntry ×2 + tools.total == 421 + Rosetta rows + __all__ ─
def test_registration_and_coverage():
    from srmech import introspect
    schema = introspect.describe()
    assert schema["tools"]["total"] == 486
    # name check via the raw tool schema
    from srmech.amsc.tool_schema import get_tool_schema
    reg = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.riemann_theta_multisum.multivariate_riemann_theta_sum" in reg
    assert "srmech.amsc.riemann_theta_multisum.riemann_theta_multisum_lhs" in reg
    assert set(R.__all__) == {
        "riemann_theta_multisum_lhs", "multivariate_riemann_theta_sum",
        "ThetaBracket", "ThetaBracketSum"}


def test_rosetta_rows_present():
    import json
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    for op in ("multivariate_riemann_theta_sum", "riemann_theta_multisum_lhs"):
        key = f"srmech.amsc.riemann_theta_multisum.{op}"
        assert rows.get(key) == "c_dispatched", f"{key} not classified c_dispatched"


# ── (8) MPM provenance ───────────────────────────────────────────────────────────
def test_source_sha256_lodged():
    doc = R.__doc__ or ""
    assert "8478af7407d26d0b0504d381cbe3c32a00f950c3b0c6ab8001a023b7e0c4c319" in doc
    assert "math/0408366" in doc
    assert "Spiridonov" in doc


# ── operand validation ───────────────────────────────────────────────────────────
def test_operand_validation():
    z, pts = _make(1)
    with pytest.raises(TypeError):
        riemann_theta_multisum_lhs(E.symbol("z0"), pts)   # z not a list
    with pytest.raises(ValueError):
        multivariate_riemann_theta_sum(z, pts[:1])        # len(points) != len(z)
    with pytest.raises(ValueError):
        multivariate_riemann_theta_sum(z, [(E.symbol("a"),)] * 2)  # not a 4-tuple
