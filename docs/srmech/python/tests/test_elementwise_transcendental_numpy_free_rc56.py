"""elementwise_transcendental is numpy-free — the ufunc-bucket closeout (rc56).

rc52→rc55 routed every EXTERNAL numpy-math ufunc callsite onto srmech cascades;
the last 10 were `elementwise_transcendental`'s OWN internal numpy fallback (its
complex-input path + its no-native real path). rc56 drives those to zero: the
fallbacks loop the Class-N scalar cascades (`rational.exp`/`cos`/`sin`/`log`/
`complex_exp`/`atan2`/`hypot`), so numpy carries the buffer only — there is no
`np.exp`/`np.cos`/`np.sin`/`np.log` anywhere in the source (the numpy-math
ratchet's `ufunc` ceiling is 0).

These tests pin: (1) the ratchet source-level guarantee, (2) the real path
(native + forced no-native) vs numpy, (3) the exp_i phase, (4) the complex path
(exp/cos/sin/log of a complex array) vs numpy, (5) the log domain guard, (6)
empty/shape handling.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from srmech.amsc import laplacian as L
from srmech.amsc.laplacian import elementwise_transcendental as et


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


# ── real path (native) vs numpy ──────────────────────────────────────────────

@pytest.mark.parametrize("op,ref", [("exp", np.exp), ("cos", np.cos), ("sin", np.sin)])
def test_real_native_matches_numpy(op, ref):
    a = np.array([0.0, 0.3, -1.2, 2.0, -3.0, 0.5])
    assert np.allclose(et(a, op), ref(a), rtol=0, atol=1e-9)


def test_real_log_matches_numpy():
    a = np.array([0.5, 1.0, 2.0, 3.0, 7.5])
    assert np.allclose(et(a, "log"), np.log(a), rtol=0, atol=1e-9)


def test_exp_i_matches_numpy():
    a = np.array([0.0, 0.7, -1.5, 3.0])
    assert np.allclose(et(a, "exp_i"), np.exp(1j * a), rtol=0, atol=1e-9)


# ── complex path vs numpy ────────────────────────────────────────────────────

@pytest.mark.parametrize("op,ref", [
    ("exp", np.exp), ("cos", np.cos), ("sin", np.sin), ("log", np.log)])
def test_complex_path_matches_numpy(op, ref):
    z = np.array([1.2 - 0.7j, -0.5 + 1.3j, 2.0 + 0.0j, 0.1 - 2.1j, -1.4 - 0.9j])
    got = et(z, op)
    assert got.dtype == np.complex128
    assert np.allclose(got, ref(z), rtol=0, atol=1e-9)


def test_complex_2d_shape_preserved():
    z = np.array([[1 + 1j, 2 - 0.5j], [-0.3 + 0.8j, 0.6 + 0.0j]])
    assert et(z, "exp").shape == (2, 2)


def test_complex_log_zero_rejected():
    with pytest.raises(ValueError):
        et(np.array([1 + 1j, 0 + 0j]), "log")


# ── forced no-native path exercises the pure-Python Class-N loop ─────────────

def _force_no_native():
    saved = L._native.HAS_NATIVE
    L._native.HAS_NATIVE = False
    return saved


@pytest.mark.parametrize("op,ref", [("exp", np.exp), ("cos", np.cos), ("sin", np.sin)])
def test_no_native_real_loop_matches_numpy(op, ref):
    saved = _force_no_native()
    try:
        a = np.array([0.0, 0.4, -1.1, 2.2])
        assert np.allclose(et(a, op), ref(a), rtol=0, atol=1e-9)
    finally:
        L._native.HAS_NATIVE = saved


def test_no_native_log_and_exp_i_and_domain_guard():
    saved = _force_no_native()
    try:
        assert np.allclose(et(np.array([0.5, 2.0, 5.0]), "log"),
                           np.log([0.5, 2.0, 5.0]), rtol=0, atol=1e-9)
        a = np.array([0.2, -1.3, 2.0])
        assert np.allclose(et(a, "exp_i"), np.exp(1j * a), rtol=0, atol=1e-9)
        with pytest.raises(ValueError):
            et(np.array([1.0, -2.0]), "log")
    finally:
        L._native.HAS_NATIVE = saved


# ── empty handling ───────────────────────────────────────────────────────────

def test_empty_inputs():
    assert et(np.array([]), "exp").shape == (0,)
    assert et(np.array([], dtype=np.complex128), "exp").shape == (0,)
    assert et(np.array([]), "exp_i").shape == (0,)
