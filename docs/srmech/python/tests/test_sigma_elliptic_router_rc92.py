"""rc92 — the F929 dispatch.infer router auto-routes the elliptic-hypergeometric
Σ sub-row (``sigma_elliptic``) to ``elliptic_wz_certificate``.

The Frenkel–Turaev ₈ω₇ / ₁₀E₉ summation is the TOP of the base-axis degeneration
tower (ordinary → q → elliptic). rc90/rc91 shipped the reducers
(``elliptic_zeilberger`` / ``elliptic_wz_certificate``); this rc wires the elliptic
row into the ONE F929 dispatch table so an arbitrary stored relationship whose
structure matches the ₈ω₇ term-ratio auto-routes, is proved, and returns the closed
form — else an honest OPEN. Non-compute orchestration (no new ToolEntry / C peer).
numpy-free.
"""

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.thetasum import _Y
from srmech.amsc.dispatch import infer, _detect_row


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


def test_detect_row_sigma_elliptic_structural_and_tagged():
    r = _make_8w7()
    # structural sniff: the distinct elliptic_term_ratio key
    assert _detect_row({"elliptic_term_ratio": r}) == "sigma_elliptic"
    # explicit tags
    for tag in ("sigma_elliptic", "elliptic", "8w7", "10e9",
                "elliptic_hypergeometric", "frenkel_turaev"):
        assert _detect_row({"row": tag}) == "sigma_elliptic"
        assert _detect_row({"kind": tag}) == "sigma_elliptic"


def test_infer_routes_8w7_to_elliptic_wz_certificate_verified():
    res = infer({"elliptic_term_ratio": _make_8w7()})
    assert res["reducible"] is True
    assert res["row"] == "sigma_elliptic"
    assert res["reducer"] == "elliptic_wz_certificate"
    assert res["verified"] is True
    # the reduced payload carries the elliptic_wz_certificate closed form cf(n)
    cf = res["closed_form"]
    assert cf["verified"] is True
    assert cf["certificate"]["method"] == "connection_coefficient_induction"
    assert len(cf["closed_form"]["num"]) == 4 and len(cf["closed_form"]["den"]) == 4


def test_infer_non_8w7_elliptic_is_honest_open():
    # an elliptic ratio that is NOT a canonical ₈ω₇ → honest OPEN (never a
    # fabricated reduction; the anti-hallucination gate reads the reducer's flag).
    q = M.symbol(_Q_SYM); a = M.symbol("a"); xk = M.symbol(_X)
    bad = R(q, num=[Theta(a * xk)], den=[Theta(q * xk)])
    res = infer({"elliptic_term_ratio": bad})
    assert res["reducible"] is False
    assert res["candidate_next_theory"]  # a truthful next-theory hint is present


def test_existing_rows_unaffected():
    # the elliptic wiring must not regress the other rows (a spectral edges payload
    # still routes to resonant_spectrum, verified by the L²==L·L contract).
    res = infer({"edges": [(0, 1), (1, 2), (2, 0)]})
    assert res["reducible"] is True
    assert res["reducer"] == "resonant_spectrum"
