"""0.9.0rc116 — the CARRIER CONVERSION LADDER (issue #1248 / F1038): the ORPHAN
FIX + the promote/project rungs + the ladder descriptor.

The tool_schema producer/consumer census (#1248, measured on rc113) found two
ORPHANS: ``BiPoly`` (CONSUMED by ``zeilberger`` + ``wz_certificate``) and
``TriPoly`` (CONSUMED by ``apagodu_zeilberger``) were never PRODUCED from the
registry — rc113 shipped only the q-side ``qbipoly_from_coeffs``, so the classic
non-q Zeilberger / WZ / Apagodu row could not be built by prose. And NO
promote/project ops existed between rungs, though a univariate IS trivially
bivariate (a ``Poly`` can feed ``zeilberger``).

rc116 ships nine genuinely NEW public ops (tools.total 367 → 376):

  * ``zeilberger.bipoly_from_coeffs(coeffs)``   — non_compute BUILDER (orphan fix)
  * ``tripoly.tripoly_from_coeffs(coeffs)``     — non_compute BUILDER (orphan fix)
  * ``carrier_ladder.poly_promote(p, n_vars)``  — non_compute (variable ladder up)
  * ``carrier_ladder.poly_project(p)``          — non_compute (variable ladder down)
  * ``carrier_ladder.qpoly_promote(p, n_vars)`` — non_compute (q ladder up)
  * ``carrier_ladder.qpoly_project(p)``         — non_compute (q ladder down)
  * ``carrier_ladder.carrier_ladder_descriptor()`` — non_compute (routing map)
  * ``cascade.cd_promote(x, dim)``              — non_compute (Hurwitz ladder up)
  * ``cascade.cd_project(x)``                   — non_compute (Hurwitz ladder down)

Everything ships **non_compute** — pure carrier restructuring (trivial embed /
drop; no numerical kernel; the ``from_bodies`` / ``cooccurrence_edges``
precedent; no C peer).

The gates:
  (1) constructors validate (ints only; honest TypeError) and ROUND-TRIP
      against the in-process carrier construction, EXACT;
  (2) the ROUND-TRIP LAW project(promote(x)) == x, EXACT, at every rung of both
      variable ladders (Poly↔BiPoly↔TriPoly, QPoly↔QBiPoly);
  (3) the naming coherency errors — a genuinely-2-variable BiPoly / 3-variable
      TriPoly / 2-variable QBiPoly project NAMES the obstruction (never a
      silent truncation);
  (4) the Hurwitz ladder round-trip at every rung ℝ↪ℂ↪ℍ↪𝕆↪𝕊 + the naming
      coherency error, AND the octonion/quaternion-convention consistency (ℍ is
      the subalgebra ``q₄ ⊕ 0₄`` of 𝕆 under the shared cd_basis_product
      cocycle — cd_mult and qm.octonion agree);
  (5) THE CAPSTONE, end-to-end VIA the registry: a registry-built BiPoly (from
      integer coeff lists) → zeilberger → a certified recurrence (the rc42
      keystone ΣC(n,k)=2ⁿ); a promoted Poly → zeilberger (the univariate-as-
      bivariate case); a genuinely-2-variable BiPoly project → the naming error;
  (6) the descriptor shape + self-consistency;
  (7) registration: tools.total == 381, the nine ToolEntries present, all nine
      Rosetta buckets non_compute;
  (8) numpy-free / math-free / abs()-free source hygiene of the touched modules.

MPM: in-repo SSOT (the carriers' own conventions — Baez 2002 for the CD basis
convention, already cited in qm.octonion / cascade.cayley_dickson); no external
citations.
"""

from fractions import Fraction
import json
from pathlib import Path

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.zeilberger import BiPoly, bipoly_from_coeffs, zeilberger
from srmech.amsc.tripoly import TriPoly, tripoly_from_coeffs
from srmech.amsc.qpoly import QPoly
from srmech.amsc.qbipoly import QBiPoly
from srmech.amsc.carrier_ladder import (
    poly_promote, poly_project, qpoly_promote, qpoly_project,
    carrier_ladder_descriptor,
)
from srmech.amsc.cascade import cd_promote, cd_project, cd_mult
from srmech.mcp import invoke_tool


# ── (1) constructor contracts + round-trips ──────────────────────────────────

def test_bipoly_from_coeffs_builds_the_exact_carrier():
    """The rc42 F(n,k)=C(n,k) operands built from INTEGER LEAVES equal the
    in-process BiPoly constructions EXACTLY."""
    assert bipoly_from_coeffs([[1, 1]]) == BiPoly([Poly.from_coeffs([1, 1])])
    assert bipoly_from_coeffs([[1, 1], [-1]]) == BiPoly(
        [Poly.from_coeffs([1, 1]), Poly.from_coeffs([-1])])
    assert bipoly_from_coeffs([[0, 1], [-1]]) == BiPoly(
        [Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])])
    assert bipoly_from_coeffs([[1], [1]]) == BiPoly(
        [Poly.from_coeffs([1]), Poly.from_coeffs([1])])
    # tuple accepted
    assert bipoly_from_coeffs(([1, 1], [-1])) == bipoly_from_coeffs([[1, 1], [-1]])


def test_bipoly_from_coeffs_rejects_junk_honestly():
    with pytest.raises(TypeError):
        bipoly_from_coeffs([[0.5]])                 # float leaf
    with pytest.raises(TypeError):
        bipoly_from_coeffs([[True]])                # bool leaf
    with pytest.raises(TypeError):
        bipoly_from_coeffs([["a"]])                 # str leaf
    with pytest.raises(TypeError):
        bipoly_from_coeffs([1])                     # a k-cell must be a list
    with pytest.raises(TypeError):
        bipoly_from_coeffs("a")                     # not a list


def test_tripoly_from_coeffs_builds_the_exact_carrier():
    """A trivariate ``n + j`` built from integer leaves equals the in-process
    TriPoly construction EXACTLY."""
    got = tripoly_from_coeffs([[[0, 1]], [[1]]])    # j**0 = n, j**1 = 1  ->  n + j
    want = TriPoly([BiPoly([Poly.from_coeffs([0, 1])]),
                    BiPoly([Poly.from_coeffs([1])])])
    assert got == want
    # cross-check the sparse monomial reading
    assert got == TriPoly.from_dict({(1, 0, 0): 1, (0, 1, 0): 1})


def test_tripoly_from_coeffs_rejects_junk_honestly():
    with pytest.raises(TypeError):
        tripoly_from_coeffs([[[0.5]]])              # float leaf
    with pytest.raises(TypeError):
        tripoly_from_coeffs([[[True]]])             # bool leaf
    with pytest.raises(TypeError):
        tripoly_from_coeffs([[1]])                  # a k-cell must be a list
    with pytest.raises(TypeError):
        tripoly_from_coeffs([1])                    # a j-block must be a list
    with pytest.raises(TypeError):
        tripoly_from_coeffs("a")                    # not a list


# ── (2) the ROUND-TRIP LAW — project(promote(x)) == x, EXACT, at every rung ───

def test_ordinary_ladder_round_trip_law_exact_at_every_rung():
    p = Poly.from_coeffs([1, 1])                    # 1 + k (a univariate-in-k Poly)
    # rung 1 -> 2 -> 1
    b = poly_promote(p)
    assert isinstance(b, BiPoly)
    assert poly_project(b) == p
    # rung 2 -> 3 -> 2 (a genuine BiPoly in (n,k))
    b2 = bipoly_from_coeffs([[1, 1], [-1]])         # (1+n) - k
    t = poly_promote(b2)
    assert isinstance(t, TriPoly)
    assert poly_project(t) == b2
    # multi-rung promote (Poly -> TriPoly), single-rung projects recover
    t2 = poly_promote(p, 3)
    assert isinstance(t2, TriPoly)
    assert poly_project(poly_project(t2)) == p
    # TOTAL: n_vars == current rung is a no-op
    assert poly_promote(p, 1) is p
    assert poly_promote(b2, 2) is b2


def test_q_ladder_round_trip_law_exact():
    qp = QPoly.from_coeffs([0, 1])                  # x = qⁿ
    qb = qpoly_promote(qp)
    assert isinstance(qb, QBiPoly)
    assert qpoly_project(qb) == qp
    # the zero carrier round-trips too
    assert qpoly_project(qpoly_promote(QPoly.zero())) == QPoly.zero()
    # TOTAL no-op
    assert qpoly_promote(qp, 1) is qp


def test_promote_rejects_descent_and_bad_targets():
    b = bipoly_from_coeffs([[1, 1], [-1]])
    with pytest.raises(ValueError):
        poly_promote(b, 1)                          # below current rung
    with pytest.raises(ValueError):
        poly_promote(Poly.from_coeffs([1]), 4)      # out of range
    with pytest.raises(TypeError):
        poly_promote(Poly.from_coeffs([1]), True)   # bool n_vars
    with pytest.raises(TypeError):
        poly_promote("not a carrier")               # not a ladder carrier


# ── (3) the naming coherency errors (variable ladder) ─────────────────────────

def test_genuine_bipoly_project_names_n():
    """A genuinely n-dependent BiPoly cannot drop n — the error NAMES n."""
    b = bipoly_from_coeffs([[1, 1], [-1]])          # (1+n) - k, genuine in n
    with pytest.raises(ValueError) as ei:
        poly_project(b)
    assert "'n' is the genuinely non-trivial variable" in str(ei.value)
    assert "TRUNCATE" in str(ei.value)              # never silent


def test_genuine_tripoly_project_names_j():
    t = tripoly_from_coeffs([[[1]], [[1]]])         # 1 + j, genuine in j
    with pytest.raises(ValueError) as ei:
        poly_project(t)
    assert "'j' is the genuinely non-trivial variable" in str(ei.value)


def test_genuine_qbipoly_project_names_Y():
    # a genuinely Y-dependent QBiPoly: Y**0 = 1, Y**1 = 1  ->  1 + Y
    qb = QBiPoly([QPoly.one(), QPoly.one()])
    assert qb.y_degree == 1
    with pytest.raises(ValueError) as ei:
        qpoly_project(qb)
    assert "'Y' is the genuinely non-trivial variable" in str(ei.value)


def test_base_rung_project_is_a_clean_error():
    with pytest.raises(ValueError):
        poly_project(Poly.from_coeffs([1, 1]))      # a Poly has nothing to drop
    with pytest.raises(ValueError):
        qpoly_project(QPoly.from_coeffs([0, 1]))     # a QPoly has nothing to drop


# ── (4) the Hurwitz (Cayley–Dickson) ladder ───────────────────────────────────

def test_cd_promote_zero_pads_the_convention():
    r = cd_promote([Fraction(3)], 2)
    assert r == (Fraction(3), Fraction(0))
    # a quaternion embeds in 𝕆 as q₄ ⊕ 0₄ (the rc109 restriction convention)
    q4 = [Fraction(2), Fraction(-1), Fraction(3), Fraction(5)]
    assert cd_promote(q4, 8) == tuple(q4) + (Fraction(0),) * 4
    # TOTAL: dim == the element's dim is a no-op
    assert cd_promote(q4, 4) == tuple(q4)


def test_cd_ladder_round_trip_law_exact_at_every_rung():
    for d in (1, 2, 4, 8):
        x = tuple(Fraction(i + 1) for i in range(d))
        assert cd_project(cd_promote(list(x), 2 * d)) == x


def test_cd_project_names_the_present_component():
    with pytest.raises(ValueError) as ei:
        cd_project([Fraction(1), Fraction(2)])       # genuine imaginary part
    msg = str(ei.value)
    assert "genuinely non-trivial coordinate" in msg
    assert "e1" in msg and "TRUNCATE" in msg
    # a real (dim 1) element has no higher half
    with pytest.raises(ValueError):
        cd_project([Fraction(7)])


def test_cd_promote_matches_octonion_quaternion_convention():
    """ℍ IS the subalgebra ``q₄ ⊕ 0₄`` of 𝕆 under the SAME cd_basis_product
    cocycle: (a) cd_mult on promoted quaternions == cd_promote of the quaternion
    product; (b) octonion_left_mult on cd_promote(q₄,8) has quaternion_left_mult
    as its top-left 4×4 block (the rc109 octonion-restriction pattern)."""
    from srmech.qm import octonion as octo
    from srmech.qm.quaternion import quaternion_left_mult, quaternion_right_mult

    a4 = [Fraction(1), Fraction(2), Fraction(-1), Fraction(3)]
    b4 = [Fraction(2), Fraction(-3), Fraction(1), Fraction(-2)]
    # (a) the subalgebra embedding is a homomorphism under cd_mult.
    lhs = cd_mult(cd_promote(a4, 8), cd_promote(b4, 8))
    rhs = cd_promote(cd_mult(a4, b4), 8)
    assert lhs == rhs, "ℍ must embed in 𝕆 as a subalgebra under cd_mult"

    # (b) octonion_left/right_mult on the promoted quaternion == the top-left
    # 4×4 block of the quaternion operator, and the coupling blocks vanish.
    q4 = [0.5, -1.25, 3.75, 0.125]
    q8 = [float(v) for v in cd_promote([Fraction(x).limit_denominator() for x in q4], 8)]
    assert q8 == list(q4) + [0.0] * 4
    for qop, oop in ((quaternion_left_mult, octo.octonion_left_mult),
                     (quaternion_right_mult, octo.octonion_right_mult)):
        m4 = qop(q4).tolist()
        m8 = oop(q8).tolist()
        for r in range(4):
            for c in range(4):
                assert m4[r][c] == m8[r][c]
                assert m8[r][c + 4] == 0.0
                assert m8[r + 4][c] == 0.0


# ── (5) THE CAPSTONE — the orphan fix + the ladder, end-to-end VIA the registry ─

def _ratios_binomial_lists():
    """F(n,k)=C(n,k) term ratios as INTEGER-LEAF nested lists (bipoly grammar):
    r_n=(n+1)/((n+1)−k), r_k=(n−k)/(k+1)."""
    return ([[1, 1]], [[1, 1], [-1]], [[0, 1], [-1]], [[1], [1]])


def _binom(n, k):
    """C(n,k) by exact integer arithmetic (no import math)."""
    if k < 0 or k > n:
        return 0
    num = 1
    for i in range(k):
        num = num * (n - i) // (i + 1)
    return num


def test_capstone_registry_built_bipoly_certified_recurrence():
    """THE ORPHAN FIX end-to-end: integer coeff lists → bipoly_from_coeffs
    (×4, VIA the registry) → the returned BiPoly carriers chained VERBATIM into
    zeilberger (VIA the registry) → the certified order-1 recurrence
    f(n+1) − 2 f(n) = 0 for ΣC(n,k)=2ⁿ, INDEPENDENTLY verified to annihilate the
    actual sum (never trusting the engine)."""
    lists = _ratios_binomial_lists()
    rn_num, rn_den, rk_num, rk_den = (
        invoke_tool("srmech.amsc.zeilberger.bipoly_from_coeffs", {"coeffs": c})
        for c in lists)
    for op in (rn_num, rn_den, rk_num, rk_den):
        assert isinstance(op, BiPoly)
    res = invoke_tool("srmech.amsc.zeilberger.zeilberger",
                      {"rn_num": rn_num, "rn_den": rn_den,
                       "rk_num": rk_num, "rk_den": rk_den, "max_order": 4})
    assert res is not None and res["order"] == 1
    from srmech.amsc.q import Q
    coeffs = res["coeffs"]

    def f(n):                                        # f(n) = Σ_k C(n,k) = 2ⁿ
        return sum(_binom(n, k) for k in range(n + 1))
    for n in range(0, 8):
        s = sum(coeffs[j].eval(Q(n, 1)) * f(n + j) for j in range(len(coeffs)))
        assert s == 0, f"certified recurrence must annihilate ΣC(n,k) at n={n}"
    # the recurrence is proportional to [-2, 1]: a0/a1 = -2.
    a0, a1 = coeffs
    assert a1.eval(Q(0, 1)) != 0
    assert a0.eval(Q(0, 1)) / a1.eval(Q(0, 1)) == Q(-2, 1)


def test_capstone_promoted_poly_feeds_zeilberger_univariate_as_bivariate():
    """THE LADDER end-to-end: r_k denominator k+1 is a univariate-in-k Poly;
    promoted to a BiPoly it feeds zeilberger IDENTICALLY to the raw operand (a
    univariate IS trivially bivariate). The promoted-Poly run gives the SAME
    order-1 recurrence."""
    rn_num, rn_den, rk_num, _rk_den = _ratios_binomial_lists()
    rn_num, rn_den, rk_num = (bipoly_from_coeffs(c)
                              for c in (rn_num, rn_den, rk_num))
    # rk_den = k + 1 as a bare Poly-in-k, promoted UP the ladder to a BiPoly.
    rk_den_poly = Poly.from_coeffs([1, 1])           # 1 + k
    rk_den_promoted = invoke_tool(
        "srmech.amsc.carrier_ladder.poly_promote", {"p": rk_den_poly})
    assert isinstance(rk_den_promoted, BiPoly)
    res = zeilberger(rn_num, rn_den, rk_num, rk_den_promoted, max_order=4)
    assert res is not None and res["order"] == 1
    # identical to feeding the raw Poly (zeilberger coerces it the same way).
    res_raw = zeilberger(rn_num, rn_den, rk_num, rk_den_poly, max_order=4)
    assert res["order"] == res_raw["order"]
    assert res["coeffs"] == res_raw["coeffs"]


def test_capstone_genuine_bipoly_project_naming_error_via_registry():
    """THE LADDER's honest side: a genuinely-2-variable BiPoly cannot project to
    a Poly — VIA the registry, the naming coherency error names n."""
    b = invoke_tool("srmech.amsc.zeilberger.bipoly_from_coeffs",
                    {"coeffs": [[1, 1], [-1]]})      # (1+n) - k
    with pytest.raises(ValueError) as ei:
        invoke_tool("srmech.amsc.carrier_ladder.poly_project", {"p": b})
    assert "'n' is the genuinely non-trivial variable" in str(ei.value)


# ── (6) the ladder descriptor ─────────────────────────────────────────────────

def test_descriptor_shape_and_self_consistency():
    d = invoke_tool(
        "srmech.amsc.carrier_ladder.carrier_ladder_descriptor", {})
    assert d["carriers"]["Poly"] == {"ladder": "variable", "rung": 1}
    assert d["carriers"]["BiPoly"] == {"ladder": "variable", "rung": 2}
    assert d["carriers"]["TriPoly"] == {"ladder": "variable", "rung": 3}
    assert d["carriers"]["QPoly"] == {"ladder": "variable_q", "rung": 1}
    assert d["carriers"]["QBiPoly"] == {"ladder": "variable_q", "rung": 2}
    # every carrier's declared rung agrees with its ladder's rungs table
    for name, spec in d["carriers"].items():
        ladder = d["ladders"][spec["ladder"]]
        assert ladder["rungs"][name] == spec["rung"]
    # the three ladders name a real promote / project op dotted-path
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    for ladder in d["ladders"].values():
        assert schema.lookup(ladder["promote"]) is not None
        assert schema.lookup(ladder["project"]) is not None
    # the CD ladder is keyed by algebra dimension (the cd_promote dim target)
    assert d["ladders"]["cayley_dickson"]["rungs"] == {
        "R": 1, "C": 2, "H": 4, "O": 8, "S": 16}


# ── (7) registration: tools.total, entries, buckets ──────────────────────────

def test_tools_total_is_376():
    """rc116 ships 9 genuinely NEW public ops → +9 ToolEntries (367 → 376)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 395


def test_new_tool_entries_present_with_declared_types():
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    expected = {
        "srmech.amsc.zeilberger.bipoly_from_coeffs": (
            "zeilberger", {"coeffs": "list[list[int]]"}),
        "srmech.amsc.tripoly.tripoly_from_coeffs": (
            "tripoly", {"coeffs": "list[list[list[int]]]"}),
        "srmech.amsc.carrier_ladder.poly_promote": (
            "carrier_ladder", {"p": "Poly | BiPoly", "n_vars": "int"}),
        "srmech.amsc.carrier_ladder.poly_project": (
            "carrier_ladder", {"p": "BiPoly | TriPoly"}),
        "srmech.amsc.carrier_ladder.qpoly_promote": (
            "carrier_ladder", {"p": "QPoly", "n_vars": "int"}),
        "srmech.amsc.carrier_ladder.qpoly_project": (
            "carrier_ladder", {"p": "QBiPoly"}),
        "srmech.amsc.carrier_ladder.carrier_ladder_descriptor": (
            "carrier_ladder", {}),
        "srmech.amsc.cascade.cd_promote": (
            "cascade", {"x": "sequence", "dim": "int"}),
        "srmech.amsc.cascade.cd_project": ("cascade", {"x": "sequence"}),
    }
    for name, (category, params) in expected.items():
        entry = schema.lookup(name)
        assert entry is not None, f"missing ToolEntry {name}"
        assert entry.category == category
        assert entry.mcp_callable is True
        declared = {p.name: p.type for p in entry.parameters}
        assert declared == params, f"{name}: params {declared} != {params}"


def test_rosetta_buckets_all_non_compute():
    """All nine new ops are non_compute (pure carrier restructuring — trivial
    embed / drop; no numerical kernel; the from_bodies / cooccurrence_edges
    precedent)."""
    ledger = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {r["defined_at"]: r["bucket"]
            for r in (json.loads(l) for l in
                      ledger.read_text(encoding="utf-8").splitlines() if l.strip())}
    for defined_at in (
        "srmech.amsc.zeilberger.bipoly_from_coeffs",
        "srmech.amsc.tripoly.tripoly_from_coeffs",
        "srmech.amsc.carrier_ladder.poly_promote",
        "srmech.amsc.carrier_ladder.poly_project",
        "srmech.amsc.carrier_ladder.qpoly_promote",
        "srmech.amsc.carrier_ladder.qpoly_project",
        "srmech.amsc.carrier_ladder.carrier_ladder_descriptor",
        "srmech.amsc.cascade.cayley_dickson.cd_promote",
        "srmech.amsc.cascade.cayley_dickson.cd_project",
    ):
        assert rows.get(defined_at) == "non_compute", defined_at


def test_new_param_types_are_coercible():
    from srmech.mcp._coercion import has_coercer
    for t in ("list[list[int]]", "list[list[list[int]]]", "Poly | BiPoly",
              "BiPoly | TriPoly", "QPoly", "QBiPoly", "sequence", "int"):
        assert has_coercer(t), f"no coercer for declared type {t!r}"


# ── (8) hygiene: numpy-free / math-free / abs()-free sources ─────────────────

def test_touched_modules_are_numpy_math_abs_free():
    import srmech.amsc.zeilberger as Z
    import srmech.amsc.tripoly as T
    import srmech.amsc.carrier_ladder as CL
    import srmech.amsc.cascade.cayley_dickson as CD
    for mod in (Z, T, CL, CD):
        text = open(mod.__file__, encoding="utf-8").read()
        assert "import numpy" not in text
        assert "import math" not in text
        assert "abs(" not in text.replace("abs()", "")  # Class-K discipline
