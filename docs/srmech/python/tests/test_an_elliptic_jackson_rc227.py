"""rc227 — the Aₙ (type-A / Milne) elliptic Jackson reduction row: the sibling
root-system member beside the shipped Cₙ capstone — the OPEN the Cₙ row's own
``_OPEN_HINTS`` named.

The identity (MPM-verified at build from the extracted PDF, sha256
``299d2738c4539a390a437c795a0b0084a5c82d403566c4f549db39482e3076ce``): Hjalmar
Rosengren, "New transformations for elliptic hypergeometric series on the root
system Aₙ", arXiv:math/0305379v1 [math.CA] (27 May 2003), Eq. (6) — the elliptic
analogue of Milne's Aₙ Jackson summation. Over the SIMPLEX ``y₁+…+yₙ = N`` (the
``C(N+n−1, n−1)`` compositions), with the type-A Vandermonde ``Δ(z·q^y)/Δ(z)``
and the COMPUTED balancing ``w = z₁⋯zₙ·a₁⋯a_{n+1}``:

    Σ_{|y|=N} Δ(z·q^y)/Δ(z) · ∏ₖ ∏ⱼ(aⱼzₖ)_{yₖ} / [(wzₖ)_{yₖ}·∏ⱼ(qzₖ/zⱼ)_{yₖ}]
      = ∏_{j=1}^{n+1}(w/aⱼ)_N / [∏_{j=1}^{n}(wzⱼ)_N·(q)_N].

What this suite pins:
  1. THE ENGINE PROVES END-TO-END — ``multivariate_elliptic_jackson_an(...,
     verify=True)`` returns ``verified is True`` on genuine n ≥ 2 (and n = 3, 4)
     cross-variable instances: the constructed closed form ACTUALLY EQUALS the
     constructed simplex sum via the exact multi-variable ``ThetaSum.is_zero``
     (measured feasible: every case with ≤ 6 compositions, both native AND pure
     arms). The n = 1 case is pinned for what it IS — a trivial single-term
     degeneration where LHS == RHS term-by-term (NOT the ₈ω₇).
  2. The check DISCRIMINATES — a perturbed closed form gives False.
  3. The honest None beyond the measured feasibility cap (instant, no hang).
  4. The p = 0 exact-ℚ degeneration (θ → 1 − z under ``eval_trunc``) — the basic
     (Milne) case of the identity holds EXACTLY in rational arithmetic: the
     in-repo re-verification of the source formula reading (the MPM check).
  5. Native == pure parity for both ops; clean decline when absent.
  6. The ``sigma_elliptic_an`` dispatch row: tag + 4-key structural sniff routes
     to the verified reducer; ``verified`` surfaced; malformed → OPEN; the Cₙ
     row is uncollided; ``_OPEN_HINTS`` updated on both rows.
  7. Registration: ToolEntry ×2 (tools.total == 418), Rosetta ledger rows
     (c_dispatched), the rc225 responsion edges (verified + open).

numpy-free (exact modified-theta algebra); no ``abs()`` (Class-K sign via the
EllMonomial sign-branch). Run from ``docs/srmech/python`` with
``PYTHONPATH=$(pwd)``.
"""

import json
from pathlib import Path

import pytest

from srmech import introspect
from srmech.amsc.dispatch import _OPEN_HINTS, infer
from srmech.amsc.ellbase import EllMonomial as M, EllRatio
from srmech.amsc.elliptic_jackson_an import (
    an_vwp_multisum_lhs,
    multivariate_elliptic_jackson_an,
    _an_lhs_thetasum,
    _an_vwp_multisum_lhs_c,
    _balancing_w,
    _max_thetas_per_side,
    _multivariate_elliptic_jackson_an_c,
    _multivariate_elliptic_jackson_an_py,
    _num_compositions,
    _verify_an_reduction,
    _VERIFY_MAX_COMPOSITIONS,
)
from srmech.amsc.q import Q
from srmech.amsc.thetasum import ThetaSum


def _operand(n):
    z = [M.symbol(f"z{i + 1}") for i in range(n)]
    a = [M.symbol(f"a{j + 1}") for j in range(n + 1)]
    return z, a, M.symbol("q")


# ── (0) call shapes: plain → bare EllRatio; verify=True → the dict ──────────────────────
def test_plain_call_returns_bare_ellratio():
    z, a, q = _operand(2)
    r = multivariate_elliptic_jackson_an(z, a, q, 1)
    assert isinstance(r, EllRatio)
    r_explicit = multivariate_elliptic_jackson_an(z, a, q, 1, verify=False)
    assert isinstance(r_explicit, EllRatio) and r_explicit == r


def test_verify_true_returns_dict_shape():
    z, a, q = _operand(2)
    out = multivariate_elliptic_jackson_an(z, a, q, 1, verify=True)
    assert isinstance(out, dict)
    assert set(out.keys()) == {"closed_form", "verified"}
    assert isinstance(out["closed_form"], EllRatio)
    assert out["verified"] in (True, False, None)
    assert out["closed_form"] == multivariate_elliptic_jackson_an(z, a, q, 1)


# ── (1) THE ENGINE PROVES END-TO-END: verified is True on the GENUINE feasible set,
#        including the n ≥ 2 cross-variable instances that carry the type-A Vandermonde
#        coupling (the anti-shell gate: the reduction actually PROVES, not just builds) ──
@pytest.mark.parametrize("n,N", [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1),
                                 (2, 3), (3, 2), (4, 1)])
def test_verified_true_feasible_cases(n, N):
    z, a, q = _operand(n)
    assert _num_compositions(N, n) <= _VERIFY_MAX_COMPOSITIONS
    out = multivariate_elliptic_jackson_an(z, a, q, N, verify=True)
    assert out["verified"] is True, (
        f"n={n} N={N}: the closed form PROVABLY equals the Aₙ simplex sum, so "
        f"is_zero(LHS-RHS) must be True — a False means the symbolic LHS "
        f"construction (or the closed form) is wrong")


def test_n1_is_the_trivial_single_term_degeneration_not_8w7():
    # For n = 1 the simplex {y₁ = N} has ONE composition, and the balancing
    # w = z₁a₁a₂ makes the single summand EQUAL the closed form term-by-term
    # (w/a₁ = z₁a₂, w/a₂ = z₁a₁) — a trivial degeneration, NOT the ₈ω₇
    # Frenkel–Turaev sum (that is the Cₙ row's n = 1). Pinned exactly: the
    # 1-term LHS ThetaSum IS the RHS EllRatio.
    z, a, q = _operand(1)
    for N in (1, 2, 3):
        assert _num_compositions(N, 1) == 1
        lhs = an_vwp_multisum_lhs(z, a, q, N)
        rhs = multivariate_elliptic_jackson_an(z, a, q, N)
        assert lhs == ThetaSum.from_ellratio(rhs)


# ── (2) the check DISCRIMINATES: a perturbed closed form is caught (False) ──────────────
def test_perturbed_closed_form_is_false():
    z, a, q = _operand(2)
    N = 1                                            # a feasible, cross-variable case
    zz, aa = tuple(z), tuple(a)
    closed = multivariate_elliptic_jackson_an(z, a, q, N)
    # the genuine closed form verifies True ...
    assert _verify_an_reduction(zz, aa, q, N, closed) is True
    # ... scaling the RHS prefactor by 2 breaks the identity -> provably NOT zero
    scaled = EllRatio(closed.prefactor * M.scalar(Q(2, 1)), num=closed.num, den=closed.den)
    assert _verify_an_reduction(zz, aa, q, N, scaled) is False
    # ... dropping a numerator theta also breaks it -> False
    assert len(closed.num) >= 1
    dropped = EllRatio(closed.prefactor, num=closed.num[:-1], den=closed.den)
    assert _verify_an_reduction(zz, aa, q, N, dropped) is False


# ── (3) the HONEST-infeasible None path — beyond the composition-count cap, no hang ─────
def test_verified_none_beyond_cap():
    # (3, 3) has C(5, 2) = 10 compositions > cap 6: the per-call proof is not
    # attempted (measured at build: the pure decision does not finish in-budget
    # at this scale) — the op returns verified=None instantly, with the
    # constructive (build-verified) closed form still returned.
    z, a, q = _operand(3)
    assert _num_compositions(3, 3) > _VERIFY_MAX_COMPOSITIONS
    out = multivariate_elliptic_jackson_an(z, a, q, 3, verify=True)
    assert out["verified"] is None
    assert isinstance(out["closed_form"], EllRatio)
    # a deliberately-oversized ceiling also caps out honestly (7 compositions)
    z2, a2, q2 = _operand(2)
    assert _num_compositions(6, 2) == 7 > _VERIFY_MAX_COMPOSITIONS
    out2 = multivariate_elliptic_jackson_an(z2, a2, q2, 6, verify=True)
    assert out2["verified"] is None
    assert isinstance(out2["closed_form"], EllRatio)


# ── (4) the MPM re-verification IN-REPO: the p = 0 exact-ℚ degeneration (θ → 1 − z
#        under eval_trunc, so both sides collapse to exact rationals — the basic /
#        Milne case of Eq. 6). This pins the SOURCE formula reading forever. ────────────
@pytest.mark.parametrize("n,N", [(2, 2), (3, 1)])
def test_p0_exact_rational_degeneration(n, N):
    z, a, q = _operand(n)
    values = {"p": Q(0, 1), "q": Q(2, 1)}
    zvals = [Q(3, 1), Q(5, 1), Q(17, 1)][:n]
    avals = [Q(7, 1), Q(11, 1), Q(13, 1), Q(19, 1)][:n + 1]
    for i in range(n):
        values[f"z{i + 1}"] = zvals[i]
    for j in range(n + 1):
        values[f"a{j + 1}"] = avals[j]
    lhs = an_vwp_multisum_lhs(z, a, q, N)
    rhs = multivariate_elliptic_jackson_an(z, a, q, N)
    assert lhs.eval_trunc(values, 2) == rhs.eval_trunc(values, 2)


def test_balancing_w_is_computed_product():
    z, a, q = _operand(2)
    w = _balancing_w(tuple(z), tuple(a))
    expect = z[0] * z[1] * a[0] * a[1] * a[2]
    assert w == expect


# ── (5) native == pure parity (both ops), clean decline when absent ─────────────────────
@pytest.mark.parametrize("n,N", [(1, 1), (2, 1), (2, 2), (3, 1)])
def test_native_matches_pure_lhs(n, N):
    from srmech.amsc import _native as _nat
    z, a, q = _operand(n)
    zz, aa = tuple(z), tuple(a)
    pure = _an_lhs_thetasum(zz, aa, q, N)
    native = _an_vwp_multisum_lhs_c(zz, aa, q, N)
    if _nat.has_native_an_vwp_multisum_lhs():
        assert native is not None, "native symbols present but dispatch declined"
        assert native == pure
    else:
        assert native is None                         # clean decline, pure is complete
    assert an_vwp_multisum_lhs(z, a, q, N) == pure


@pytest.mark.parametrize("n,N", [(1, 1), (2, 1), (2, 2), (3, 1)])
def test_native_matches_pure_rhs(n, N):
    from srmech.amsc import _native as _nat
    z, a, q = _operand(n)
    zz, aa = tuple(z), tuple(a)
    pure = _multivariate_elliptic_jackson_an_py(zz, aa, q, N)
    native = _multivariate_elliptic_jackson_an_c(zz, aa, q, N)
    if _nat.has_native_multivariate_elliptic_jackson_an():
        assert native is not None, "native symbols present but dispatch declined"
        assert native == pure
    else:
        assert native is None
    assert multivariate_elliptic_jackson_an(z, a, q, N) == pure


# ── (6a) validation contracts ────────────────────────────────────────────────────────────
def test_validation_contracts():
    z, a, q = _operand(2)
    with pytest.raises(TypeError, match="an_vwp_multisum_lhs"):
        an_vwp_multisum_lhs("z1", a, q, 1)             # z not a list
    with pytest.raises(TypeError):
        multivariate_elliptic_jackson_an(z, a, "q", 1)  # q not an EllMonomial
    with pytest.raises(TypeError):
        multivariate_elliptic_jackson_an([z[0], "z2"], a, q, 1)  # a non-EllMonomial entry
    with pytest.raises(TypeError):
        multivariate_elliptic_jackson_an(z, a, q, 1.0)  # float N
    with pytest.raises(ValueError):
        multivariate_elliptic_jackson_an(z, a[:2], q, 1)  # len(a) != n + 1
    with pytest.raises(ValueError):
        multivariate_elliptic_jackson_an([], a[:1], q, 1)  # n < 1
    with pytest.raises(ValueError):
        multivariate_elliptic_jackson_an(z, a, q, 0)    # N < 1


# ── (6b) the sizing helpers the native wire rides (pure integer arithmetic) ─────────────
def test_sizing_helpers():
    # compositions of N into n parts = C(N+n-1, n-1)
    assert _num_compositions(1, 1) == 1
    assert _num_compositions(3, 1) == 1
    assert _num_compositions(1, 2) == 2
    assert _num_compositions(2, 2) == 3
    assert _num_compositions(3, 2) == 4
    assert _num_compositions(1, 3) == 3
    assert _num_compositions(2, 3) == 6
    assert _num_compositions(3, 3) == 10
    assert _num_compositions(1, 4) == 4
    # per-side max theta count: n(n-1)/2 + (n+1)N
    assert _max_thetas_per_side(1, 1) == 0 + 2
    assert _max_thetas_per_side(2, 2) == 1 + 6
    assert _max_thetas_per_side(1, 3) == 3 + 4
    assert _max_thetas_per_side(2, 3) == 3 + 8


# ── (7) ROUTER: the sigma_elliptic_an row ────────────────────────────────────────────────
def test_router_tagged_routes_and_surfaces_verified_true():
    rel = {"row": "sigma_elliptic_an",
           "z": ["z1", "z2"], "a_vec": ["a1", "a2", "a3"], "q": "q", "N": 1}
    out = infer(rel)
    assert out["reducible"] is True
    assert out["row"] == "sigma_elliptic_an"
    assert out["reducer"] == "multivariate_elliptic_jackson_an"
    assert out["verified"] is True                    # a genuine per-call PROOF
    assert isinstance(out["closed_form"], EllRatio)


def test_router_untagged_4key_sniff_routes():
    rel = {"z": ["z1", "z2", "z3"], "a_vec": ["a1", "a2", "a3", "a4"],
           "q": "q", "N": 1}
    out = infer(rel)
    assert out["reducible"] is True
    assert out["reducer"] == "multivariate_elliptic_jackson_an"
    assert out["verified"] is True


def test_router_surfaces_verified_none_beyond_cap():
    rel = {"row": "sigma_elliptic_an",
           "z": ["z1", "z2", "z3"], "a_vec": ["a1", "a2", "a3", "a4"],
           "q": "q", "N": 3}
    out = infer(rel)
    assert out["reducible"] is True
    assert out["verified"] is None
    assert isinstance(out["closed_form"], EllRatio)


def test_router_malformed_params_route_to_open():
    # N < 1 makes the op raise -> the router catches it and routes to honest OPEN.
    rel = {"row": "sigma_elliptic_an",
           "z": ["z1", "z2"], "a_vec": ["a1", "a2", "a3"], "q": "q", "N": 0}
    out = infer(rel)
    assert out["reducible"] is False
    assert out["row"] is None
    # a length-mismatched a_vec too
    rel2 = {"row": "sigma_elliptic_an",
            "z": ["z1", "z2"], "a_vec": ["a1", "a2"], "q": "q", "N": 1}
    out2 = infer(rel2)
    assert out2["reducible"] is False


def test_router_cn_row_uncollided():
    # the Cₙ 8-key payload still routes to the Cₙ reducer (the Aₙ 4-key set
    # never collides with it).
    rel = {"a": "a", "b": "b", "c": "c", "d": "d", "x": "x", "q": "q",
           "N": 1, "n": 2}
    out = infer(rel)
    assert out["reducible"] is True
    assert out["reducer"] == "multivariate_elliptic_jackson"


def test_open_hints_updated_on_both_rows():
    assert "sigma_elliptic_an" in _OPEN_HINTS
    # the Aₙ row's own hint names the NEXT frontier honestly
    hint_an = _OPEN_HINTS["sigma_elliptic_an"]
    assert "Dₙ/BCₙ" in hint_an and "higher-genus" in hint_an
    # the Cₙ row's hint now records the Aₙ row as SHIPPED (+ the row tag)
    hint_cn = _OPEN_HINTS["sigma_elliptic_multivar"]
    assert "sigma_elliptic_an" in hint_cn


# ── (8) registration: ToolEntry ×2 + tools.total == 418 + Rosetta rows + __all__ ────────
def test_registration():
    import srmech.amsc.elliptic_jackson_an as eja
    assert "multivariate_elliptic_jackson_an" in eja.__all__
    assert "an_vwp_multisum_lhs" in eja.__all__
    schema = introspect.describe()
    assert schema["tools"]["total"] == 419
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert ("srmech.amsc.elliptic_jackson_an.multivariate_elliptic_jackson_an"
            in names)
    assert "srmech.amsc.elliptic_jackson_an.an_vwp_multisum_lhs" in names
    for nm in ("srmech.amsc.elliptic_jackson_an.multivariate_elliptic_jackson_an",
               "srmech.amsc.elliptic_jackson_an.an_vwp_multisum_lhs"):
        entry = next(t for t in get_tool_schema().tools if t.name == nm)
        assert "0305379" in entry.summary              # the MPM-verified keystone
    # the Rosetta ledger rows (the #928 everything-mirrors ratchet feed)
    ndjson = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(line) for line in
            ndjson.read_text(encoding="utf-8").splitlines() if line.strip()]
    for nm in ("srmech.amsc.elliptic_jackson_an.multivariate_elliptic_jackson_an",
               "srmech.amsc.elliptic_jackson_an.an_vwp_multisum_lhs"):
        mine = [r for r in rows if r["exposed_as"] == nm]
        assert len(mine) == 1 and mine[0]["bucket"] == "c_dispatched"


# ── (9) the rc225 responsion edges: the new verified reducer edge + the row's
#        honest-OPEN edge (answers_with VERBATIM from _OPEN_HINTS) ──────────────────────
def test_responsion_edges():
    from srmech.amsc.responsion_schema import responsion_schema
    schema = responsion_schema()
    v_key = ("srmech.amsc.elliptic_jackson_an.multivariate_elliptic_jackson_an"
             "|EllMonomial")
    assert v_key in schema
    assert any(r["kind"] == "closed_form" and r["status"] == "verified"
               for r in schema[v_key])
    open_key = "srmech.amsc.dispatch.infer|EllMonomial"
    assert open_key in schema
    answers = [r["answers_with"] for r in schema[open_key]
               if r.get("status") == "open"]
    assert _OPEN_HINTS["sigma_elliptic_an"] in answers
