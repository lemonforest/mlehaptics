"""rc97 — dispatch.infer routes the multivariate (Cₙ) elliptic Jackson Σ sub-row.

The F929 dispatch router recognises a balanced Cₙ elliptic Jackson relationship (the eight
a,b,c,d,x,q,N,n parameters — by tag OR by the full key set) and routes it to
multivariate_elliptic_jackson, returning the closed-form theta-quotient product. A
CONSTRUCTIVE reduction (the resonant_spectrum precedent). numpy-free.
"""

import pytest

from srmech.amsc import dispatch
from srmech.amsc.ellbase import EllMonomial as M, EllRatio
from srmech.amsc.elliptic_jackson import multivariate_elliptic_jackson


def _rel(tag=None):
    r = {"a": "a", "b": "b", "c": "c", "d": "d", "x": "x", "q": "q", "N": 2, "n": 3}
    if tag is not None:
        r["row"] = tag
    return r


def _expected_closed_form():
    a, b, c, d, x, q = (M.symbol(s) for s in ("a", "b", "c", "d", "x", "q"))
    return multivariate_elliptic_jackson(a, b, c, d, x, q, 2, 3)


def test_detect_row_by_tag():
    for tag in ("sigma_elliptic_multivar", "cn_jackson", "elliptic_multivar",
                "multivariate_elliptic"):
        assert dispatch._detect_row(_rel(tag)) == "sigma_elliptic_multivar"


def test_detect_row_by_key_set():
    # the untagged 8-key set is distinctive.
    assert dispatch._detect_row(_rel()) == "sigma_elliptic_multivar"


def test_infer_reduces_to_closed_form_tagged():
    out = dispatch.infer(_rel("sigma_elliptic_multivar"))
    assert out["reducible"] is True
    assert out["row"] == "sigma_elliptic_multivar"
    assert out["reducer"] == "multivariate_elliptic_jackson"
    assert isinstance(out["closed_form"], EllRatio)
    assert out["closed_form"] == _expected_closed_form()


def test_infer_reduces_untagged():
    out = dispatch.infer(_rel())
    assert out["reducible"] is True
    assert out["row"] == "sigma_elliptic_multivar"
    assert out["closed_form"] == _expected_closed_form()


def test_infer_accepts_ellmonomial_params():
    r = {k: M.symbol(k) for k in ("a", "b", "c", "d", "x", "q")}
    r.update({"N": 2, "n": 3, "row": "sigma_elliptic_multivar"})
    out = dispatch.infer(r)
    assert out["reducible"] is True
    assert out["closed_form"] == _expected_closed_form()


def test_infer_malformed_routes_to_open():
    # invalid N (< 1) → the op raises → the router routes to honest OPEN.
    bad = _rel("sigma_elliptic_multivar")
    bad["N"] = 0
    out = dispatch.infer(bad)
    assert out["reducible"] is False
    assert "candidate_next_theory" in out


def test_open_hint_present():
    assert "sigma_elliptic_multivar" in dispatch._OPEN_HINTS
    # the hint truthfully names the frontier (the multi-variable is_zero) + Aₙ next row.
    hint = dispatch._OPEN_HINTS["sigma_elliptic_multivar"].lower()
    assert "is_zero" in hint or "aₙ" in hint or "root-system" in hint
