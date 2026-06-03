"""v0.7.0rc21 — native C peers for the last pure-Python loop-bind ops
(``loop_associator`` / ``loop_left_op`` / ``loop_right_op``) agree with the
pure-Python Cayley-Dickson recursion.

These three were the residual ops named in #814's spec that still computed via
``_loop_bind_raw`` (pure Python) while ``cross7`` / ``g2_three_form`` already had
dedicated C symbols. rc21 adds ``srmech_loop_{associator,left_op,right_op}_f64``,
completing the "C = transpiled Python" Rosetta parity (notebook §3.29.4–§3.29.5)
for the whole loop-bind surface. These tests compare the native peer against the
pure-Python recursion engine — the Rosetta agreement-attestation. Skip with a log
when the native lib is absent (the pure-Python path is covered elsewhere).
"""

import numpy as np
import pytest

from srmech.amsc import hdc
from srmech.amsc.hdc import LOOP_DIM


def _require_native(symbol):
    if not hdc._loop_native_ready(symbol):
        pytest.skip(f"native {symbol} not present (pure-Python wheel)")


def _unit(seed):
    v = np.random.default_rng(seed).standard_normal(LOOP_DIM)
    return v / np.linalg.norm(v)


def _basis(k):
    e = np.zeros(LOOP_DIM)
    e[k] = 1.0
    return e


# ----------------------------------------------------------------------
# native peer == pure-Python recursion (Rosetta agreement)
# ----------------------------------------------------------------------


def test_native_associator_matches_python_recursion():
    _require_native("srmech_loop_associator_f64")
    a, b, c = _unit(1), _unit(2), _unit(3)
    native = hdc._try_native_loop_associator(a, b, c)
    assert native is not None
    want = (hdc._loop_bind_raw(hdc._loop_bind_raw(a, b), c)
            - hdc._loop_bind_raw(a, hdc._loop_bind_raw(b, c)))
    assert np.allclose(native, want, atol=1e-12)


def test_native_left_op_matches_python_recursion():
    _require_native("srmech_loop_left_op_f64")
    a = _unit(4)
    native = hdc._try_native_loop_left_op(a)
    assert native is not None
    want = np.column_stack([hdc._loop_bind_raw(a, _basis(k)) for k in range(LOOP_DIM)])
    assert native.shape == (LOOP_DIM, LOOP_DIM)
    assert np.allclose(native, want, atol=1e-12)


def test_native_right_op_matches_python_recursion():
    _require_native("srmech_loop_right_op_f64")
    a = _unit(5)
    native = hdc._try_native_loop_right_op(a)
    assert native is not None
    want = np.column_stack([hdc._loop_bind_raw(_basis(k), a) for k in range(LOOP_DIM)])
    assert native.shape == (LOOP_DIM, LOOP_DIM)
    assert np.allclose(native, want, atol=1e-12)


# ----------------------------------------------------------------------
# the public wrappers return the native result when the peer is present
# ----------------------------------------------------------------------


def test_wrappers_dispatch_to_native_when_present():
    _require_native("srmech_loop_associator_f64")
    a, b, c = _unit(6), _unit(7), _unit(8)
    assert np.array_equal(hdc.loop_associator(a, b, c),
                          hdc._try_native_loop_associator(a, b, c))
    assert np.array_equal(hdc.loop_left_op(a), hdc._try_native_loop_left_op(a))
    assert np.array_equal(hdc.loop_right_op(a), hdc._try_native_loop_right_op(a))


# ----------------------------------------------------------------------
# the associator's known octonion structure survives on the native path
# ----------------------------------------------------------------------


def test_associator_is_alternating_native():
    # The octonion associator is totally antisymmetric (alternating):
    #   [a,a,c] = 0  and  [a,b,c] = -[b,a,c].
    a, b, c = _unit(11), _unit(12), _unit(13)
    assert np.allclose(hdc.loop_associator(a, a, c), 0.0, atol=1e-12)
    assert np.allclose(hdc.loop_associator(a, b, c),
                       -hdc.loop_associator(b, a, c), atol=1e-12)


def test_associator_zero_on_quaternionic_triple_native():
    # e1, e2, e3=e1·e2 lie in a quaternion subalgebra (associative) → assoc = 0.
    e1, e2 = _basis(1), _basis(2)
    e3 = hdc.loop_bind(e1, e2)
    assert np.allclose(hdc.loop_associator(e1, e2, e3), 0.0, atol=1e-12)


def test_left_op_right_op_columns_are_binds_native():
    # L_a e_k = a·e_k ; R_a e_k = e_k·a (column semantics).
    a = _unit(14)
    L, R = hdc.loop_left_op(a), hdc.loop_right_op(a)
    for k in range(LOOP_DIM):
        assert np.allclose(L[:, k], hdc.loop_bind(a, _basis(k)), atol=1e-12)
        assert np.allclose(R[:, k], hdc.loop_bind(_basis(k), a), atol=1e-12)
