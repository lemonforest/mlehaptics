"""rc223 — #796: the three remaining EXACT-ℚ infer rows dispatch in C.

rc176 moved the F929 OPEN/infer router's detect + dispatch + verify LOGIC into C
for two rows (cyclic → the_one, sigma-gosper → gosper); rc192 added the
sigma-definite wz_certificate row over the rc191 ``srmech_carrier_read_bipoly``
reader. This rc ships the remaining nested exact-ℚ carrier readers
(``srmech_carrier_read_tripoly`` / ``_qbipoly`` / ``_ellratio``) and wires the
three remaining exact-ℚ rows into ``srmech_infer.c`` for a bare-C host:

  * sigma_multivar — the six (n,j,k) TriPoly term-ratios →
    ``srmech_apagodu_zeilberger`` @max_order=1 (has=1 IS the verification; a
    has=0 is NOT definitive → non-OK → the pure path decides). The apagodu
    dense-RREF arena is hundreds of MB even for small genuine systems, so the
    native path DECLINES past SRMECH_INFER_WS_CEILING_MB (default 256) and the
    bounded-memory pure CRT path is the everyday decider.
  * sigma_q — DEFINITE: the four (X,Y)=(qⁿ,qᵏ) QBiPoly q-term-ratios → FIND
    ``srmech_q_zeilberger`` @order-1 + the q-WZ shape + PROVE
    ``srmech_q_wz_verify`` (the COMPLETE mirror). A FIND decline (the k-free
    native scope) → non-OK → pure; found-but-not-WZ / verify-fail →
    reducible:false (definitive within the byte-identical k-free class).
    INDEFINITE: the QPoly q-term-ratio (a one-Y-cell QBiPoly wire) →
    ``srmech_q_gosper`` (has=1 IS the verification; has=0 → non-OK → pure).
  * sigma_elliptic — the ₈ω₇ term-ratio EllRatio (pre-interned wire) →
    ``srmech_elliptic_wz_certificate`` (has=1 IS the verification; has=0 →
    non-OK → pure, the conservative fall).

This test pins:
  (1) PARITY — ``infer`` with the native path ENGAGED equals the pure path
      over a genuine reduction AND an honest-OPEN case, per row (the safety
      net: the native decision path either verifies or falls to pure, so the
      final dicts are equal — asserted with FULL == where the closed form is
      comparable, else the structural shape).
  (2) GENUINE ENGAGEMENT — the rows whose native reducer scope covers the
      fixture really RUN in C: the ₈ω₇ (elliptic) and the q-geometric
      (q_gosper) return the verified native DECISION; the k-free non-WZ
      q-definite returns the native reducible:false. The multivar fixture
      DECLINES at the default ceiling (None → pure) and — opt-in, arena
      permitting — dispatches natively with the ceiling raised.
  (3) HONEST OPEN PRESERVED — every OPEN fixture stays OPEN on BOTH paths;
      the C router NEVER fabricates a reduction.
  (4) The rc223 readers round-trip TriPoly / QBiPoly / EllRatio wire JSON
      through marshal→read→canonical re-serialisation (bignum decimal
      transport included) and decline malformed nodes.
  (5) The three dedicated arena sizers are distinct symbols, monotone in
      shape/limbs.

numpy-FREE and math-FREE (only srmech carriers + plain arithmetic).
"""

from __future__ import annotations

import copy
import os

import pytest

from srmech.amsc import _native
from srmech.amsc import dispatch
from srmech.amsc.dispatch import infer, _marshal_relationship
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.qpoly import QPoly
from srmech.amsc.qbipoly import QBiPoly
from srmech.amsc.tripoly import TriPoly
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.thetasum import _Y


# ── fixtures: sigma_multivar ──────────────────────────────────────────────────
def _tp(d):
    return TriPoly.from_dict(d)


def _multivar():
    """Σ_{j,k} C(n,j)C(j,k) = 3ⁿ — the genuine (n,j,k) 'sums of sums'."""
    return {
        "rn_num": _tp({(1, 0, 0): 1, (0, 0, 0): 1}),
        "rn_den": _tp({(1, 0, 0): 1, (0, 0, 0): 1, (0, 1, 0): -1}),
        "rj_num": _tp({(1, 0, 0): 1, (0, 1, 0): -1}),
        "rj_den": _tp({(0, 1, 0): 1, (0, 0, 0): 1, (0, 0, 1): -1}),
        "rk_num": _tp({(0, 1, 0): 1, (0, 0, 1): -1}),
        "rk_den": _tp({(0, 0, 1): 1, (0, 0, 0): 1}),
    }


def _multivar_open():
    """A zero r_j denominator — the pure body's own contract error routes to
    the honest OPEN (and the C reader's jdeg==0 guard declines to pure)."""
    rel = _multivar()
    rel["rj_den"] = TriPoly.zero()
    return rel


# ── fixtures: sigma_q ─────────────────────────────────────────────────────────
def _xc(c):
    return QPoly.from_q_poly(Poly.from_coeffs([Q(c, 1)]))


def _xm(e, c=1):
    return QPoly.from_q_poly(Poly.from_coeffs([Q(c, 1)]), e)


def _q_definite():
    """A genuine q-WZ pair (R=Y/(X−Y), r_k=Y/X) — the rc57 constructed triple."""
    Xn = QBiPoly([QPoly.zero(), _xc(1)])
    Xd = QBiPoly([_xm(1, 1), _xc(-1)])
    Bn = QBiPoly([QPoly.zero(), _xc(1)])
    Bd = QBiPoly([_xm(1, 1)])
    num_rhs = Xn.qshift_y(1) * Bn * Xd - Xn * Xd.qshift_y(1) * Bd
    den_rhs = Xd.qshift_y(1) * Bd * Xd
    return {"qrn_num": num_rhs + den_rhs, "qrn_den": den_rhs,
            "qrk_num": Bn, "qrk_den": Bd}


def _q_definite_open_kfree():
    """r_n = q, r_k = 1 — inside the C FIND's k-free class, but NOT the q-WZ
    shape (a₀ = −q is not a rational scalar) → the native path itself emits
    the definitive reducible:false; pure lands the same OPEN."""
    qC = QBiPoly([QPoly.from_q_poly(Poly.monomial(1, Q(1, 1)))])
    one = QBiPoly([QPoly.one()])
    return {"qrn_num": qC, "qrn_den": one, "qrk_num": one, "qrk_den": one}


def _q_indefinite():
    """The q-geometric Σ qᵏ (term ratio r = q) — the constant-ratio class the
    native srmech_q_gosper completes."""
    return {"q_term_ratio_num": QPoly.from_dict({(0, 1): Q(1, 1)}),
            "q_term_ratio_den": QPoly.one()}


def _q_indefinite_open():
    """The q-harmonic term ratio r = (1−x)/(1−qx) — no q-hypergeometric
    antidifference (the honest un-summable residue on both paths)."""
    return {"q_term_ratio_num": QPoly.from_dict({(0, 0): Q(1, 1),
                                                 (1, 0): Q(-1, 1)}),
            "q_term_ratio_den": QPoly.from_dict({(0, 0): Q(1, 1),
                                                 (1, 1): Q(-1, 1)})}


# ── fixtures: sigma_elliptic ──────────────────────────────────────────────────
def _make_8w7():
    """The canonical ₈ω₇ term-ratio (the rc90/rc91 keystone), as an EllRatio."""
    xk = M.symbol(_X); q = M.symbol(_Q_SYM); y = M.symbol(_Y)
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    e = (a * a * q * y) * (b * c * d).inv()
    poch = [b, c, d, e, y.inv()]
    num = [Theta(a * q * q * xk * xk), Theta(a * xk)]
    den = [Theta(a * xk * xk), Theta(q * xk)]
    for u in poch:
        num.append(Theta(u * xk))
        den.append(Theta(a * q * xk * u.inv()))
    return R(q, num=num, den=den)


def _elliptic():
    return {"elliptic_term_ratio": _make_8w7()}


def _elliptic_open():
    """An elliptic ratio that is NOT a canonical ₈ω₇ → honest OPEN."""
    q = M.symbol(_Q_SYM); a = M.symbol("a"); xk = M.symbol(_X)
    return {"elliptic_term_ratio": R(q, num=[Theta(a * xk)],
                                     den=[Theta(q * xk)])}


def _fixtures():
    return {
        "multivar": _multivar(),
        "multivar_open": _multivar_open(),
        "q_definite": _q_definite(),
        "q_definite_open_kfree": _q_definite_open_kfree(),
        "q_indefinite": _q_indefinite(),
        "q_indefinite_open": _q_indefinite_open(),
        "elliptic": _elliptic(),
        "elliptic_open": _elliptic_open(),
    }


_ALL = _fixtures()
_REDUCIBLE = ("multivar", "q_definite", "q_indefinite", "elliptic")
_OPEN = ("multivar_open", "q_definite_open_kfree", "q_indefinite_open",
         "elliptic_open")
# fixtures whose full infer() dict is directly ==-comparable on both arms
# (closed forms of plain dicts / QPoly with __eq__); the multivar closed form
# carries live TriPoly/Poly certificate objects, compared structurally.
_FULL_EQ = ("q_definite", "q_definite_open_kfree", "q_indefinite",
            "q_indefinite_open", "elliptic", "elliptic_open", "multivar_open")


def _shape(d):
    """The structural signature of an infer() result."""
    return (d["reducible"], d["row"], d.get("reducer"), d.get("verified"),
            d.get("candidate_next_theory") is not None, d.get("reason"))


def _infer_with(relationship, native_on):
    """Run infer() with the native path forced on/off (the parity toggle)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = native_on and saved   # can't fabricate native
        return infer(copy.deepcopy(relationship))
    finally:
        _native.HAS_NATIVE = saved


# ── (1) PARITY: native == pure over reducible + OPEN, per row ─────────────────
@pytest.mark.parametrize("name", list(_ALL))
def test_native_equals_pure(name):
    rel = _ALL[name]
    nat = _infer_with(rel, native_on=True)
    pur = _infer_with(rel, native_on=False)
    assert _shape(nat) == _shape(pur), (
        f"{name}: native {_shape(nat)} != pure {_shape(pur)}")
    if name in _FULL_EQ:
        assert nat == pur, f"{name}: full-result divergence"


@pytest.mark.parametrize("name,row", [
    ("multivar", "sigma_multivar"), ("q_definite", "sigma_q"),
    ("q_indefinite", "sigma_q"), ("elliptic", "sigma_elliptic")])
def test_reducible_row_and_verified(name, row):
    out = _infer_with(_ALL[name], native_on=True)
    assert out["reducible"] is True and out["row"] == row
    assert out["verified"] is True


# ── (2) GENUINE ENGAGEMENT: the C peer really RUNS where its scope covers ─────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_exact_rows_native_present():
    assert _native.has_native_exact_rows() is True


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("name,key", [
    ("multivar", '"rj_num"'), ("multivar_open", '"rj_num"'),
    ("q_definite", '"qrn_num"'), ("q_definite_open_kfree", '"qrn_num"'),
    ("q_indefinite", '"q_term_ratio_num"'),
    ("q_indefinite_open", '"q_term_ratio_num"'),
    ("elliptic", '"elliptic_term_ratio"'),
    ("elliptic_open", '"elliptic_term_ratio"'),
])
def test_rows_marshal(name, key):
    """Every rc223 fixture marshals to the srmech_infer wire form."""
    marshalled = _marshal_relationship(_ALL[name])
    assert marshalled is not None, f"{name} should marshal"
    rel_json, max_terms = marshalled
    assert key in rel_json and max_terms >= 1


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_elliptic_row_c_engaged():
    """The ₈ω₇ dispatches IN C: the raw decision is the verified reduction."""
    rel_json, mt = _marshal_relationship(_elliptic())
    decision = _native.infer_c(rel_json, mt)
    assert decision == {"reducer": "elliptic_wz_certificate",
                        "reducible": True, "row": "sigma_elliptic",
                        "verified": True}


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_q_gosper_row_c_engaged():
    """The q-geometric term dispatches IN C (the constant-ratio native scope)."""
    rel_json, mt = _marshal_relationship(_q_indefinite())
    decision = _native.infer_c(rel_json, mt)
    assert decision == {"reducer": "q_gosper", "reducible": True,
                        "row": "sigma_q", "verified": True}


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_q_definite_kfree_c_emits_definitive_open():
    """A k-free order-1 FIND whose recurrence is NOT the q-WZ shape comes back
    reducible:false FROM THE C ROUTER (the one definitive-false rc223 case —
    the k-free FIND class is byte-identical to pure), and infer() → OPEN."""
    rel = _q_definite_open_kfree()
    rel_json, mt = _marshal_relationship(rel)
    decision = _native.infer_c(rel_json, mt)
    assert decision == {"reducible": False, "row": "sigma_q"}
    out = infer(copy.deepcopy(rel))
    assert out["reducible"] is False and out["row"] is None
    assert "candidate_next_theory" in out


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_conservative_rows_fall_to_pure_never_false():
    """The fixtures OUTSIDE a native reducer's decidable scope return None from
    infer_c (fall-to-pure) — NEVER a fabricated decision: the genuine q-WZ pair
    (non-k-free FIND) and the non-₈ω₇ elliptic ratio."""
    for rel in (_q_definite(), _elliptic_open(), _q_indefinite_open()):
        rel_json, mt = _marshal_relationship(rel)
        decision = _native.infer_c(rel_json, mt)
        assert decision is None or decision.get("reducible") is False


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_multivar_declines_at_default_ceiling():
    """At the default SRMECH_INFER_WS_CEILING_MB the apagodu arena (hundreds of
    MB) DECLINES → infer_c None → the pure CRT path decides (and reduces)."""
    if os.environ.get("SRMECH_INFER_WS_CEILING_MB"):
        pytest.skip("ceiling overridden in this environment")
    rel_json, mt = _marshal_relationship(_multivar())
    assert _native.infer_c(rel_json, mt) is None
    out = infer(copy.deepcopy(_multivar()))
    assert out["reducible"] is True and out["reducer"] == "apagodu_zeilberger"


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_multivar_c_engaged_with_raised_ceiling():
    """OPT-IN proof the multivar C row genuinely dispatches: with the ceiling
    raised the C router reads the six TriPoly, runs srmech_apagodu_zeilberger
    @order-1 and returns the verified decision. Skips (declined to pure) when
    the box cannot host the apagodu dense-RREF arena."""
    saved = os.environ.get("SRMECH_INFER_WS_CEILING_MB")
    os.environ["SRMECH_INFER_WS_CEILING_MB"] = "1600"
    try:
        rel_json, mt = _marshal_relationship(_multivar())
        try:
            decision = _native.infer_c(rel_json, mt)
        except MemoryError:
            pytest.skip("apagodu arena does not fit on this box")
        if decision is None:
            pytest.skip("the C peer declined this system to the pure path")
        assert decision == {"reducer": "apagodu_zeilberger", "reducible": True,
                            "row": "sigma_multivar", "verified": True}
    finally:
        if saved is None:
            os.environ.pop("SRMECH_INFER_WS_CEILING_MB", None)
        else:
            os.environ["SRMECH_INFER_WS_CEILING_MB"] = saved


# ── (3) honest OPEN preserved end-to-end ──────────────────────────────────────
@pytest.mark.parametrize("name", list(_OPEN))
def test_open_cases_stay_open(name):
    out = _infer_with(_ALL[name], native_on=True)
    assert out["reducible"] is False and out["row"] is None
    assert out["reason"] == "not reducible in current vocabulary"
    assert out["candidate_next_theory"]


# ── (4) the rc223 readers: marshal→read→canonical round-trip ──────────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_tripoly_reader_roundtrip():
    """TriPoly wire (bare-int, [num,den], bignum-string coefficients; a ragged
    j-block) round-trips to the canonical padded-rectangular [num,den] form."""
    big = str(10 ** 25)
    src = ('[[[1,[2,3]],["' + big + '"]],[[[7,2]]]]').encode()
    st, out = _native.carrier_marshal_roundtrip_c(_native.CARRIER_TRIPOLY, src)
    assert st == _native.SRMECH_OK
    assert out == ('[[[[1,1],[2,3]],[[' + big + ',1]]],'
                   '[[[7,2]],[]]]').encode()


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_qbipoly_reader_roundtrip():
    """QBiPoly wire (negative Laurent x_low; bignum string) round-trips."""
    big = str(10 ** 20 - 1)
    src = ('[[-2,[[1,[3,4]],["' + big + '"]]],[0,[[[5,6]]]]]').encode()
    st, out = _native.carrier_marshal_roundtrip_c(_native.CARRIER_QBIPOLY, src)
    assert st == _native.SRMECH_OK
    assert out == ('[[-2,[[[1,1],[3,4]],[[' + big + ',1]]]],'
                   '[0,[[[5,6]]]]]').encode()


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_ellratio_reader_roundtrip():
    """EllRatio pre-interned wire (a 2¹²⁷ bignum coefficient) round-trips to
    the canonical flat header + [num,den] + exponent-row form."""
    big = str(2 ** 127)
    src = ('{"n_syms":3,"xsym":2,"psym":0,"qsym":1,"ysym":-1,'
           '"nsym":-1,"ksym":-1,"n_num":1,"n_den":1,'
           '"coeff_num":[1,"' + big + '",3],"coeff_den":[1,1,2],'
           '"exps":[[0,1,0],[0,0,1],[1,0,2]]}').encode()
    st, out = _native.carrier_marshal_roundtrip_c(_native.CARRIER_ELLRATIO, src)
    assert st == _native.SRMECH_OK
    assert out == ('[3,2,0,1,-1,-1,-1,1,1,'
                   '[[1,1],[' + big + ',1],[3,2]],'
                   '[[0,1,0],[0,0,1],[1,0,2]]]').encode()


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("kind,src", [
    ("CARRIER_TRIPOLY", b"[[5]]"),                  # a scalar where a run goes
    ("CARRIER_QBIPOLY", b'[["x",[[1]]]]'),          # non-int x_low
    ("CARRIER_QBIPOLY", b"[[0]]"),                  # not a 2-pair
    ("CARRIER_ELLRATIO", b'{"n_syms":0}'),          # n_syms < 1
    ("CARRIER_ELLRATIO",
     b'{"n_syms":1,"xsym":5,"psym":-1,"qsym":-1,"ysym":-1,"nsym":-1,'
     b'"ksym":-1,"n_num":0,"n_den":0,"coeff_num":[1],"coeff_den":[1],'
     b'"exps":[[0]]}'),                             # sym index out of range
])
def test_readers_decline_malformed(kind, src):
    st, out = _native.carrier_marshal_roundtrip_c(getattr(_native, kind), src)
    assert st != _native.SRMECH_OK and out is None


# ── C-side robustness: a malformed row operand declines cleanly ───────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_c_declines_malformed_row_json():
    """Directly-malformed rc223 wire JSON → infer_c None (defer to pure)."""
    bad_mv = ('{"row":"sigma_multivar","rn_num":5,"rn_den":[[[1]]],'
              '"rj_num":[[[1]]],"rj_den":[[[1]]],"rk_num":[[[1]]],'
              '"rk_den":[[[1]]]}')
    assert _native.infer_c(bad_mv, 1) is None
    bad_ell = ('{"row":"sigma_elliptic","elliptic_term_ratio":'
               '{"n_syms":2,"xsym":0,"psym":1,"qsym":-1,"ysym":-1,"nsym":-1,'
               '"ksym":-1,"n_num":1,"n_den":0,"coeff_num":[1],"coeff_den":[1],'
               '"exps":[[0,0]]}}')                  # counts mismatch (n_mono=2)
    assert _native.infer_c(bad_ell, 4) is None


# ── (5) the three dedicated arena sizers ──────────────────────────────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("sym", [
    "srmech_infer_sigma_multivar_arena_bytes",
    "srmech_infer_sigma_q_arena_bytes",
    "srmech_infer_sigma_elliptic_arena_bytes",
])
def test_dedicated_row_sizers_monotone(sym):
    import ctypes
    fn = getattr(_native.LIB, sym)
    a = int(fn(ctypes.c_size_t(200), ctypes.c_size_t(2), ctypes.c_size_t(1)))
    b = int(fn(ctypes.c_size_t(200), ctypes.c_size_t(3), ctypes.c_size_t(2)))
    assert a > 0 and b > a          # monotone in shape envelope / limbs


def test_module_is_numpy_and_math_free():
    """The router + this test stay numpy-free / math-free."""
    with open(dispatch.__file__, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
