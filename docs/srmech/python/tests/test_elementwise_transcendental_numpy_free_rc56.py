"""elementwise_transcendental is numpy-free — the ufunc-bucket closeout (rc56).

rc52→rc55 routed every EXTERNAL numpy-math ufunc callsite onto srmech cascades;
the last 10 were `elementwise_transcendental`'s OWN internal numpy fallback (its
complex-input path + its no-native real path). rc56 drives those to zero: the
fallbacks loop the Class-N scalar cascades (`rational.exp`/`cos`/`sin`/`log`/
`complex_exp`/`atan2`/`hypot`). With numpy removed entirely (#564) the input is
a plain list and the result is a FLAT list (complex for `exp_i` / complex input,
else float) — there is no `np.exp`/`np.cos`/`np.sin`/`np.log` anywhere in the
source.

These tests pin (with stdlib ``math``/``cmath`` as the oracle): (1) the ratchet
source-level guarantee, (2) the real path (native + forced no-native), (3) the
exp_i phase, (4) the complex path (exp/cos/sin/log of a complex list), (5) the
log domain guard, (6) empty handling.
"""
from __future__ import annotations

import cmath
import math
import re
from pathlib import Path

import pytest

from srmech.amsc import laplacian as L
from srmech.amsc.laplacian import elementwise_transcendental as et

_TOL = 1e-9

# stdlib scalar oracles (per-element); exp_i = e^{i·x}
_REAL_OP = {"exp": math.exp, "cos": math.cos, "sin": math.sin, "log": math.log}
_CPLX_OP = {"exp": cmath.exp, "cos": cmath.cos, "sin": cmath.sin, "log": cmath.log}


def _close(got, ref, tol=_TOL):
    return abs(complex(got) - complex(ref)) < tol


# ── source-level guarantee: no numpy transcendental ufunc anywhere ───────────

def test_no_numpy_ufunc_callsites_in_source():
    pkg = Path(L.__file__).resolve().parent.parent
    rx = re.compile(
        r"\b(?:np|numpy)\.(?:sin|cos|tan|exp|expm1|log|log1p|log2|log10|sqrt|"
        r"cbrt|sign|abs|absolute|arcsin|arccos|arctan|arctan2|power|float_power|"
        r"hypot|square|reciprocal)\("
    )
    hits = []
    for p in pkg.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if rx.search(p.read_text(encoding="utf-8")):
            hits.append(str(p.relative_to(pkg)))
    assert hits == [], f"numpy ufunc callsites remain: {hits}"


# ── real path (native) vs stdlib ─────────────────────────────────────────────

@pytest.mark.parametrize("op", ["exp", "cos", "sin"])
def test_real_native_matches_stdlib(op):
    a = [0.0, 0.3, -1.2, 2.0, -3.0, 0.5]
    out = et(a, op)
    assert all(isinstance(x, float) for x in out)
    for got, ai in zip(out, a):
        assert _close(got, _REAL_OP[op](ai))


def test_real_log_matches_stdlib():
    a = [0.5, 1.0, 2.0, 3.0, 7.5]
    for got, ai in zip(et(a, "log"), a):
        assert _close(got, math.log(ai))


def test_exp_i_matches_stdlib():
    a = [0.0, 0.7, -1.5, 3.0]
    out = et(a, "exp_i")
    assert all(isinstance(x, complex) for x in out)
    for got, ai in zip(out, a):
        assert _close(got, cmath.exp(1j * ai))


# ── complex path vs stdlib ───────────────────────────────────────────────────

@pytest.mark.parametrize("op", ["exp", "cos", "sin", "log"])
def test_complex_path_matches_stdlib(op):
    z = [1.2 - 0.7j, -0.5 + 1.3j, 2.0 + 0.0j, 0.1 - 2.1j, -1.4 - 0.9j]
    got = et(z, op)
    assert all(isinstance(x, complex) for x in got)
    for g, zi in zip(got, z):
        assert _close(g, _CPLX_OP[op](zi))


def test_complex_input_returns_complex_list():
    z = [1 + 1j, 2 - 0.5j, -0.3 + 0.8j, 0.6 + 0.0j]
    out = et(z, "exp")
    assert isinstance(out, list) and len(out) == 4
    assert all(isinstance(x, complex) for x in out)


def test_complex_log_zero_rejected():
    with pytest.raises(ValueError):
        et([1 + 1j, 0 + 0j], "log")


# ── forced no-native path exercises the pure-Python Class-N loop ─────────────

def _force_no_native():
    saved = L._native.HAS_NATIVE
    L._native.HAS_NATIVE = False
    return saved


@pytest.mark.parametrize("op", ["exp", "cos", "sin"])
def test_no_native_real_loop_matches_stdlib(op):
    saved = _force_no_native()
    try:
        a = [0.0, 0.4, -1.1, 2.2]
        for got, ai in zip(et(a, op), a):
            assert _close(got, _REAL_OP[op](ai))
    finally:
        L._native.HAS_NATIVE = saved


def test_no_native_log_and_exp_i_and_domain_guard():
    saved = _force_no_native()
    try:
        for got, ai in zip(et([0.5, 2.0, 5.0], "log"), [0.5, 2.0, 5.0]):
            assert _close(got, math.log(ai))
        a = [0.2, -1.3, 2.0]
        for got, ai in zip(et(a, "exp_i"), a):
            assert _close(got, cmath.exp(1j * ai))
        with pytest.raises(ValueError):
            et([1.0, -2.0], "log")
    finally:
        L._native.HAS_NATIVE = saved


# ── empty handling ───────────────────────────────────────────────────────────

def test_empty_inputs():
    assert et([], "exp") == []
    assert et([], "exp_i") == []
