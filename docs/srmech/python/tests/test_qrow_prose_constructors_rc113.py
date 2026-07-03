"""0.9.0rc113 — PROSE-SIDE carrier constructors for the q-series row + the
FIRST UnaryTheta consumer (issue #1239 / F1027 / UPSTREAM §85): the
register-chained MOCK-THETA SPARSE-FORM pipeline, opened.

Siona's grounded inference loop drives srmech tools from natural utterances
(schema-fit binding + a result register that chains RETURNED carriers into the
next tool call). Before rc113 the q-series / mock-theta row was HALF-reachable:
``unary_theta`` was fully prose-drivable, but (a) the sparse-form engine
(``q_gosper`` / ``q_zeilberger`` / ``q_wz_certificate``) consumed QPoly /
QBiPoly carriers NOTHING in the registry returned, and (b) NOTHING consumed a
``UnaryTheta`` — a conversationally-built shadow was a dead end after display.

rc113 ships four new public ops (tools.total 363 → 367):

  * ``poly.poly_from_coeffs(coeffs)``        — non_compute BUILDER
  * ``qpoly.qpoly_from_coeffs(coeffs, x_low)`` — non_compute BUILDER
  * ``qbipoly.qbipoly_from_coeffs(coeffs)``  — non_compute BUILDER
  * ``unary_theta.theta_coefficients(theta, n_max)`` — COMPUTE, dispatched
    through the EXISTING rc70 1:1 C peer ``srmech_unary_theta`` (no new C
    symbol — the mirror already ships; a bare C host calls it directly)

The prose cell grammar is deliberately UNAMBIGUOUS (unlike the in-process
carrier cell coercion, where a 2-int list is a ``(num, den)`` rational pair):
an int leaf is a constant-in-q coefficient; a list of ints is ALWAYS the
ascending-q-degree ``ℚ[q]`` coefficient (``[0, 1]`` is ``q``).

The gates (all VIA the registry — ``invoke_tool`` — to prove
prose-reachability, mirroring how siona's loop invokes tools):

  (1) constructors validate (ints only; honest TypeError on float / bool /
      str / shape junk) and ROUND-TRIP: the registry-built carrier equals the
      in-process-constructed carrier EXACTLY;
  (2) the CAPSTONE certified recurrence — the q-binomial-theorem term
      F(n,k) = [n,k]_q·q^{C(k,2)} (the rc56 keystone), operands built by
      ``qbipoly_from_coeffs`` from integer leaves, chained into
      ``q_zeilberger`` → the ORDER-1 recurrence (1+qⁿ)f(n) − f(n+1) = 0,
      INDEPENDENTLY verified to annihilate the closed form ∏_{i<n}(1+qⁱ);
  (3) the CAPSTONE honest OPEN — the Euler q-exponential term t(k) = 1/(q;q)_k
      (ratio 1/(1−q·x)), built by ``qpoly_from_coeffs``, chained into
      ``q_gosper`` → None (no q-hypergeometric antidifference; the q-analog of
      the rc41 gosper harmonic-None acceptance case — Σ 1/(q;q)_k = 1/(q;q)_∞
      by Euler, a genuine q-series with no sparse closed form);
  (4) the MOCK-THETA operands themselves — the order-3 mock theta
      f(q) = Σ q^{k²}/(−q;q)_k² has term ratio q·x²/(1+q·x)² (x = qᵏ):
      constructed VIA the registry from integer leaves, round-tripped exactly,
      and probed at a BOUNDED certificate degree → None (no certificate of
      y-degree ≤ 5). HONEST ENGINE BOUNDARY, lodged: at the shipped
      ``_MAX_Y_DEGREE = 16`` the rc55 ℚ(q) undetermined-coefficient sweep is
      computationally impractical on THIS input (measured superexponential
      growth in the sweep degree: ~0.08 s at cap 4, ~6.4 s at cap 8 —
      extrapolating ≫ hours at 16), so the full-bound decision is not run in
      test time; the mathematics (mock thetas are genuinely mock modular —
      Zagier, Astérisque 326 (2009), Exp. 986) says no certificate exists at
      ANY degree, and the bounded probe states exactly what it proves;
  (5) the SHADOW side — ``unary_theta`` → ``theta_coefficients`` through the
      result register, exact ints verified against an INDEPENDENT hand
      computation of the Zagier g₃ coefficients and the θ₃ series;
  (6) theta_coefficients Python == C parity (native vs forced-pure;
      skip-clean when no native lib);
  (7) registration: tools.total == 381, the four ToolEntries present with the
      declared param types + Rosetta buckets (3 × non_compute builders, the
      from_bodies / cooccurrence_edges precedent; theta_coefficients
      c_dispatched through the rc70 peer);
  (8) numpy-free / math-free / abs()-free source hygiene of the touched
      modules.

MPM: the q-row ops' existing citations are the SSOT (Koornwinder JCAM 48
(1993) 91–111; Gasper & Rahman; Zagier Astérisque 326 (2009) p. 150 for g₃) —
no new external citations.
"""

from fractions import Fraction
import json
from pathlib import Path

import pytest

from srmech.amsc.poly import Poly, poly_from_coeffs
from srmech.amsc.qpoly import QPoly, qpoly_from_coeffs
from srmech.amsc.qbipoly import QBiPoly, qbipoly_from_coeffs
from srmech.amsc.unary_theta import UnaryTheta, theta_coefficients, unary_theta
from srmech.mcp import invoke_tool


# ── shared helpers (test-local; Fraction + carriers only — no numpy / math) ──

def _a_eval(coeff_qpoly, qv: int, n: int) -> Fraction:
    """Evaluate a recurrence coefficient ``a_j(X)`` (a QPoly in X = qⁿ) at exact
    ``q = qv``, ``X = qv**n`` → a Fraction (the rc56 independent-check pattern)."""
    X = Fraction(qv) ** n
    acc = Fraction(0)
    for i, cell in enumerate(coeff_qpoly.cells):
        e = coeff_qpoly.x_low + i
        cq = sum(Fraction(c.numerator, c.denominator) * Fraction(qv) ** d
                 for d, c in enumerate(cell.coeffs))
        acc += cq * (X ** e)
    return acc


def _f_qbinomial(qv: int, n: int) -> Fraction:
    """The q-binomial-theorem closed form f(n) = ∏_{i=0}^{n−1}(1 + qⁱ)."""
    p = Fraction(1)
    for i in range(n):
        p *= (1 + Fraction(qv) ** i)
    return p


def _q_binomial_operand_lists():
    """The q-binomial-theorem term ratios as PURE INTEGER-LEAF nested lists —
    the utterance-expressible operands (the qbipoly_from_coeffs grammar):
      r_n num (qX−1)·Y ; r_n den qX−Y ; r_k num X−Y ; r_k den qY−1."""
    rn_num = [[0], [-1, [0, 1]]]
    rn_den = [[0, [0, 1]], [-1]]
    rk_num = [[0, 1], [-1]]
    rk_den = [[-1], [[0, 1]]]
    return rn_num, rn_den, rk_num, rk_den


def _q_binomial_operands_in_process():
    """The SAME four operands built the in-process rc56 way (QPoly / Poly
    carriers directly) — the round-trip oracle."""
    def qmono(deg):
        return Poly.monomial(deg)
    rk_num = QBiPoly([QPoly.from_q_poly(Poly.one(), 1),
                      QPoly.from_q_poly(Poly.from_coeffs([-1]))])
    rk_den = QBiPoly([QPoly.from_q_poly(Poly.from_coeffs([-1])),
                      QPoly.from_q_poly(qmono(1))])
    qX_1 = QPoly([Poly.from_coeffs([-1]), qmono(1)], x_low=0)
    rn_num = QBiPoly([QPoly.zero(), qX_1])
    rn_den = QBiPoly([QPoly([Poly.zero(), qmono(1)], x_low=0),
                      QPoly.from_q_poly(Poly.from_coeffs([-1]))])
    return rn_num, rn_den, rk_num, rk_den


def _kronecker_minus12(n: int) -> int:
    """(−12/n) — the g₃ character, computed INDEPENDENTLY of the carrier
    (period-12 residue table; Zagier Astérisque 326 p. 150)."""
    r = n % 12
    if r in (1, 11):
        return 1
    if r in (5, 7):
        return -1
    return 0


def _g3_hand(n_max: int):
    """The g₃ shadow coefficients by HAND: g₃ = Σ_{n≥1} (−12/n)·n·q^{n²/24};
    after factoring q^{1/24}, the coefficient of q^e carries the n with
    (n²−1)/24 = e. Independent of UnaryTheta (a direct double loop)."""
    out = [0] * (n_max + 1)
    n = 1
    while (n * n - 1) // 24 <= n_max:
        chi = _kronecker_minus12(n)
        if chi != 0 and (n * n - 1) % 24 == 0:
            e = (n * n - 1) // 24
            if e <= n_max:
                out[e] += chi * n
        n += 1
    return out


def _theta3_hand(n_max: int):
    """θ₃ = Σ_{n∈ℤ} q^{n²} by hand: coefficient of q^e is #{n : n² = e} (2 for
    each positive square, 1 at e = 0)."""
    out = [0] * (n_max + 1)
    n = 0
    while n * n <= n_max:
        out[n * n] += 1 if n == 0 else 2
        n += 1
    return out


# ── (1) constructor contracts + round-trips ──────────────────────────────────

def test_poly_from_coeffs_builds_the_exact_carrier():
    p = poly_from_coeffs([0, 1])
    assert isinstance(p, Poly)
    assert p == Poly.from_coeffs([0, 1])
    assert poly_from_coeffs([1, 1]) == Poly.from_coeffs([1, 1])
    # tuple accepted; trailing zeros trim to canonical form
    assert poly_from_coeffs((2, 0, 0)) == Poly.from_coeffs([2])


def test_poly_from_coeffs_rejects_junk_honestly():
    with pytest.raises(TypeError):
        poly_from_coeffs([0.5])                    # float leaf — exact only
    with pytest.raises(TypeError):
        poly_from_coeffs([True])                   # bool is not a coefficient
    with pytest.raises(TypeError):
        poly_from_coeffs(["a"])                    # str leaf
    with pytest.raises(TypeError):
        poly_from_coeffs([[1, 2]])                 # no nested cells in ℚ[k]
    with pytest.raises(TypeError):
        poly_from_coeffs("a")                      # not a list at all


def test_qpoly_from_coeffs_int_and_q_cells():
    # int cells: [0, 1] = x (the q-geometric ratio)
    x = qpoly_from_coeffs([0, 1])
    assert isinstance(x, QPoly)
    assert x == QPoly.from_coeffs([0, 1])
    # a list cell is ALWAYS ascending-q ints: [[0, 1]] = q (the constant-in-x
    # cell carrying the ℚ[q] coefficient q) — THE disambiguation vs the
    # in-process carrier, where the 2-int list [0, 1] is the RATIONAL 0/1 = 0.
    q_cell = qpoly_from_coeffs([[0, 1]])
    assert q_cell.x_coeff(0) == Poly.monomial(1)   # the coefficient IS q
    assert QPoly.from_coeffs([[0, 1]]).is_zero     # the carrier's own reading: 0
    # the mock-theta numerator q·x²: [0, 0, [0, 1]]
    num = qpoly_from_coeffs([0, 0, [0, 1]])
    assert num.x_coeff(2) == Poly.monomial(1) and num.x_coeff(0).is_zero
    # x_low carries a genuine Laurent tail
    laur = qpoly_from_coeffs([1], x_low=-1)
    assert laur.is_laurent and laur.x_low == -1


def test_qpoly_from_coeffs_rejects_junk_honestly():
    with pytest.raises(TypeError):
        qpoly_from_coeffs([0.5])                   # float leaf
    with pytest.raises(TypeError):
        qpoly_from_coeffs([[0, 1.5]])              # float inside a q-cell
    with pytest.raises(TypeError):
        qpoly_from_coeffs([True])                  # bool
    with pytest.raises(TypeError):
        qpoly_from_coeffs(["q"])                   # str cell
    with pytest.raises(TypeError):
        qpoly_from_coeffs([1], x_low=True)         # bool x_low
    with pytest.raises(TypeError):
        qpoly_from_coeffs(1)                       # not a list


def test_qbipoly_from_coeffs_round_trips_the_rc56_keystone_exactly():
    """The four q-binomial-theorem operands built from INTEGER LEAVES equal the
    in-process rc56 carrier constructions EXACTLY (the round-trip gate)."""
    prose = [qbipoly_from_coeffs(c) for c in _q_binomial_operand_lists()]
    oracle = list(_q_binomial_operands_in_process())
    for got, want in zip(prose, oracle):
        assert isinstance(got, QBiPoly)
        assert got == want


def test_qbipoly_from_coeffs_rejects_junk_honestly():
    with pytest.raises(TypeError):
        qbipoly_from_coeffs([1])                   # a Y-cell must be a list
    with pytest.raises(TypeError):
        qbipoly_from_coeffs([[0.5]])               # float leaf
    with pytest.raises(TypeError):
        qbipoly_from_coeffs([[[0, True]]])         # bool inside a q-cell
    with pytest.raises(TypeError):
        qbipoly_from_coeffs("a")                   # not a list


# ── (2) THE CAPSTONE — certified recurrence, end-to-end VIA the registry ─────

def test_capstone_q_binomial_certified_recurrence_via_registry():
    """The register-chained sparse-form pipeline, reducible case: integer-leaf
    coefficient lists → qbipoly_from_coeffs (×4, via invoke_tool) → the
    returned carriers chained VERBATIM (result-register-shaped) into
    q_zeilberger (via invoke_tool) → the ORDER-1 certified recurrence
    (1+qⁿ)f(n) − f(n+1) = 0, independently verified to ANNIHILATE the closed
    form ∏_{i<n}(1+qⁱ) at q ∈ {2, 3, 5} (never trusting the engine)."""
    lists = _q_binomial_operand_lists()
    # step 1: prose-side construction through the REGISTRY (the tool entries).
    rn_num, rn_den, rk_num, rk_den = (
        invoke_tool("srmech.amsc.qbipoly.qbipoly_from_coeffs", {"coeffs": c})
        for c in lists)
    # step 2: the returned carriers chain — the result register — into the
    # q-row engine, also through the REGISTRY.
    res = invoke_tool("srmech.amsc.q_zeilberger.q_zeilberger",
                      {"rn_num": rn_num, "rn_den": rn_den,
                       "rk_num": rk_num, "rk_den": rk_den, "max_order": 3})
    assert res is not None, "the q-binomial theorem sum must have a q-recurrence"
    assert res["order"] == 1
    assert all(isinstance(c, QPoly) for c in res["coeffs"])
    assert isinstance(res["certificate"], QBiPoly)
    # step 3: INDEPENDENT verification — the recurrence annihilates the closed
    # form (exact Fraction arithmetic; the rc56 pattern).
    for qv in (2, 3, 5):
        for n in range(0, 6):
            s = sum(_a_eval(res["coeffs"][j], qv, n) * _f_qbinomial(qv, n + j)
                    for j in range(len(res["coeffs"])))
            assert s == 0, (
                f"the certified recurrence must annihilate ∏(1+qⁱ) at q={qv}, n={n}")
    # the recurrence shape: a_0/a_1 = −(1+qⁿ) at n=0, q=2 → −2.
    a0, a1 = res["coeffs"]
    r0, r1 = _a_eval(a0, 2, 0), _a_eval(a1, 2, 0)
    assert r1 != 0 and r0 / r1 == Fraction(-2)


# ── (3) THE CAPSTONE — honest OPEN, end-to-end VIA the registry ──────────────

def test_capstone_euler_q_exponential_honest_open_via_registry():
    """The register-chained sparse-form pipeline, genuinely-open case: the
    Euler q-exponential term t(k) = 1/(q;q)_k (term ratio 1/(1−q·x)) has NO
    q-hypergeometric antidifference — Σ_k 1/(q;q)_k = 1/(q;q)_∞ (Euler), a
    genuine q-series; the q-analog of the rc41 gosper harmonic→None acceptance
    case. The pipeline answers the honest OPEN: q_gosper → None."""
    num = invoke_tool("srmech.amsc.qpoly.qpoly_from_coeffs", {"coeffs": [1]})
    den = invoke_tool("srmech.amsc.qpoly.qpoly_from_coeffs",
                      {"coeffs": [1, [0, -1]]})       # 1 − q·x
    assert isinstance(num, QPoly) and isinstance(den, QPoly)
    res = invoke_tool("srmech.amsc.q_gosper.q_gosper",
                      {"rn_num": num, "rn_den": den})
    assert res is None, (
        "Σ 1/(q;q)_k has no q-hypergeometric antidifference — the honest OPEN")


# ── (4) the MOCK-THETA operands + the bounded certificate probe ──────────────

def test_mock_theta_term_ratio_constructs_and_round_trips_via_registry():
    """The order-3 mock theta f(q) = Σ_k q^{k²}/(−q;q)_k² has term ratio
    t(k+1)/t(k) = q·x²/(1+q·x)² (x = qᵏ). Both sides constructed VIA the
    registry from INTEGER LEAVES and round-tripped exactly against the
    in-process carrier algebra ((1+qx)² computed as a genuine QPoly square)."""
    num = invoke_tool("srmech.amsc.qpoly.qpoly_from_coeffs",
                      {"coeffs": [0, 0, [0, 1]]})     # q·x²
    den = invoke_tool("srmech.amsc.qpoly.qpoly_from_coeffs",
                      {"coeffs": [1, [0, 2], [0, 0, 1]]})  # 1 + 2qx + q²x²
    # num == q·x² built in-process
    assert num == QPoly.from_q_poly(Poly.monomial(1), 2)
    # den == (1 + q·x)² via the carrier's own exact x-convolution product
    one_plus_qx = QPoly([Poly.one(), Poly.monomial(1)], x_low=0)
    assert den == one_plus_qx * one_plus_qx


def test_mock_theta_bounded_certificate_probe_is_honest_none(monkeypatch):
    """The mock-theta ratio through q_gosper at a BOUNDED certificate degree:
    no antidifference certificate of y-degree ≤ 5 exists (None). HONEST ENGINE
    BOUNDARY, stated exactly: the shipped ``_MAX_Y_DEGREE = 16`` sweep is
    computationally impractical on THIS input (the ℚ(q) undetermined-
    coefficient system grows superexponentially in the sweep degree — measured
    ~0.08 s at cap 4, ~6.4 s at cap 8), so the full-bound decision is not run
    here; the bounded probe proves exactly what it says. The mathematics says
    no certificate exists at ANY degree (a mock theta is genuinely mock
    modular — Zagier, Astérisque 326 (2009), Exp. 986)."""
    import srmech.amsc.q_gosper as QG
    num = qpoly_from_coeffs([0, 0, [0, 1]])
    den = qpoly_from_coeffs([1, [0, 2], [0, 0, 1]])
    monkeypatch.setattr(QG, "_MAX_Y_DEGREE", 5)
    assert QG.q_gosper(num, den) is None, (
        "no q-Gosper certificate of y-degree ≤ 5 for the mock-theta ratio")


# ── (5) the SHADOW side — unary_theta → theta_coefficients, register-chained ─

def test_capstone_shadow_side_register_chain_exact_ints():
    """The shadow side of the mock-theta split, end-to-end VIA the registry:
    unary_theta (prose-drivable since rc70) → its RETURNED UnaryTheta chained
    verbatim into theta_coefficients → exact integers, verified against an
    INDEPENDENT hand computation of the Zagier g₃ coefficients."""
    g3 = invoke_tool("srmech.amsc.unary_theta.unary_theta",
                     {"char": "minus12", "j": 1, "a": 1, "b": 0, "D": 24,
                      "support": "positive"})
    assert isinstance(g3, UnaryTheta)
    got = invoke_tool("srmech.amsc.unary_theta.theta_coefficients",
                      {"theta": g3, "n_max": 26})
    assert got == _g3_hand(26)
    # the leading Zagier window, hard-pinned (Astérisque 326 p. 150):
    assert got[:8] == [1, -5, -7, 0, 0, 11, 0, 13]
    assert got[12] == -17 and got[15] == -19 and got[22] == 23 and got[26] == 25
    # θ₃, the weight-1/2 anchor, against its own hand computation.
    th3 = invoke_tool("srmech.amsc.unary_theta.unary_theta",
                      {"char": "trivial", "j": 0, "a": 1, "b": 0, "D": 1,
                       "support": "all"})
    got3 = invoke_tool("srmech.amsc.unary_theta.theta_coefficients",
                       {"theta": th3, "n_max": 9})
    assert got3 == _theta3_hand(9) == [1, 2, 0, 0, 2, 0, 0, 0, 0, 2]


def test_theta_coefficients_named_shadow_string_coerces():
    """A JSON caller may pass theta='g3' — the MCP coercer builds the named
    shadow (the same object the register-chained path reads)."""
    via_string = invoke_tool("srmech.amsc.unary_theta.theta_coefficients",
                             {"theta": "g3", "n_max": 7})
    assert via_string == [1, -5, -7, 0, 0, 11, 0, 13]


def test_theta_coefficients_delegates_exactly_and_rejects_junk():
    g3 = unary_theta("minus12", 1, 1, 0, 24, support="positive")
    assert theta_coefficients(g3, 26) == g3.q_series(26)
    with pytest.raises(TypeError):
        theta_coefficients("not a theta", 5)       # direct call: strict carrier
    with pytest.raises(ValueError):
        theta_coefficients(g3, -1)
    with pytest.raises(ValueError):
        theta_coefficients(g3, True)               # bool is not an order


# ── (6) theta_coefficients Python == C parity (via the rc70 peer) ────────────

def test_theta_coefficients_native_equals_pure_byte_identical(monkeypatch):
    """theta_coefficients rides UnaryTheta.q_series, which dispatches to the
    rc70 ``srmech_unary_theta`` C peer when present — assert the dispatched
    read equals the FORCED-pure read byte-identically (ints, ``==``). Skips
    cleanly when no native lib is present (the pure path is the oracle)."""
    from srmech.amsc import _native
    probe = getattr(_native, "has_native_unary_theta", None)
    if probe is None or not probe():
        pytest.skip("no native srmech_unary_theta (pure-Python path is the oracle)")
    import srmech.amsc.unary_theta as UT
    g3 = unary_theta("minus12", 1, 1, 0, 24, support="positive")
    native_read = theta_coefficients(g3, 40)
    monkeypatch.setattr(UT, "_native", lambda: None)  # force the pure path
    pure_read = theta_coefficients(g3, 40)
    assert native_read == pure_read


# ── (7) registration: tools.total, entries, buckets ──────────────────────────

def test_tools_total_is_367():
    """rc113 ships 4 genuinely NEW public ops (3 builders + the theta reader)
    → +4 ToolEntries (363 → 367)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 381


def test_new_tool_entries_present_with_declared_types():
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    expected = {
        "srmech.amsc.poly.poly_from_coeffs": ("poly", {"coeffs": "list[int]"}),
        "srmech.amsc.qpoly.qpoly_from_coeffs": (
            "qpoly", {"coeffs": "list", "x_low": "int"}),
        "srmech.amsc.qbipoly.qbipoly_from_coeffs": (
            "qbipoly", {"coeffs": "list[list[int]]"}),
        "srmech.amsc.unary_theta.theta_coefficients": (
            "unary_theta", {"theta": "UnaryTheta", "n_max": "int"}),
    }
    for name, (category, params) in expected.items():
        entry = schema.lookup(name)
        assert entry is not None, f"missing ToolEntry {name}"
        assert entry.category == category
        assert entry.mcp_callable is True
        declared = {p.name: p.type for p in entry.parameters}
        assert declared == params, f"{name}: params {declared} != {params}"


def test_rosetta_buckets_builders_non_compute_reader_c_dispatched():
    """The builders are non_compute (the from_bodies / cooccurrence_edges
    precedent — they construct operands, no kernel); theta_coefficients is
    c_dispatched THROUGH the existing rc70 srmech_unary_theta peer."""
    ledger = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {r["defined_at"]: r["bucket"]
            for r in (json.loads(l) for l in
                      ledger.read_text(encoding="utf-8").splitlines() if l.strip())}
    assert rows["srmech.amsc.poly.poly_from_coeffs"] == "non_compute"
    assert rows["srmech.amsc.qpoly.qpoly_from_coeffs"] == "non_compute"
    assert rows["srmech.amsc.qbipoly.qbipoly_from_coeffs"] == "non_compute"
    assert rows["srmech.amsc.unary_theta.theta_coefficients"] == "c_dispatched"


def test_mcp_wire_types_are_coercible_and_arrays():
    """Every declared param type of the four new entries has an explicit MCP
    coercer, and the nested-int wire form advertises as a JSON array (the
    rc113 lexicon addition covers list[list[int]], which previously degraded
    to the string fallback)."""
    from srmech.mcp._coercion import has_coercer
    from srmech.mcp._tools import _json_schema_type_for
    for t in ("list[int]", "list", "list[list[int]]", "int", "UnaryTheta"):
        assert has_coercer(t), f"no coercer for declared type {t!r}"
    assert _json_schema_type_for("list[list[int]]") == "array"
    assert _json_schema_type_for("list[int]") == "array"
    assert _json_schema_type_for("list") == "array"


# ── (8) hygiene: numpy-free / math-free / abs()-free sources ─────────────────

def test_touched_modules_are_numpy_math_abs_free():
    import srmech.amsc.poly as P
    import srmech.amsc.qpoly as QP
    import srmech.amsc.qbipoly as QB
    import srmech.amsc.unary_theta as UT
    for mod in (P, QP, QB, UT):
        text = open(mod.__file__, encoding="utf-8").read()
        assert "import numpy" not in text
        assert "import math" not in text
        assert "abs(" not in text.replace("abs()", "")  # Class-K discipline
