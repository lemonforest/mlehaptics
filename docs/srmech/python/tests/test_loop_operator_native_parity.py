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

rc125 (numpy-free, #564): this test is itself numpy-FREE — the loop family
returns ``list[float]`` (single-element) / :class:`srmech.amsc.mat.Mat` (the
L/R operators); column extraction / norms use the ``Mat`` API + ``mat_norm``,
random vectors come from stdlib ``random.Random`` (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""

import random

import pytest

from srmech.amsc.laplacian import mat_norm
from srmech.amsc.mat import Mat
from srmech.amsc import hdc
from srmech.amsc.hdc import LOOP_DIM


def _require_native(symbol):
    if not hdc._loop_native_ready(symbol):
        pytest.skip(f"native {symbol} not present (pure-Python wheel)")


def _vsub(u, v):
    return [u[i] - v[i] for i in range(len(u))]


def _unit(seed):
    rng = random.Random(seed)
    v = [rng.gauss(0.0, 1.0) for _ in range(LOOP_DIM)]
    nrm = sum(x * x for x in v) ** 0.5
    return [x / nrm for x in v]


def _basis(k):
    e = [0.0] * LOOP_DIM
    e[k] = 1.0
    return e


def _column(mat, k):
    return [mat[i, k] for i in range(mat.n_rows)]


def _colstack(cols):
    """A Mat whose column k is cols[k] (numpy-free column-stack)."""
    n = len(cols[0])
    rows = [[cols[k][i] for k in range(len(cols))] for i in range(n)]
    return Mat.from_rows(rows)


# ----------------------------------------------------------------------
# native peer == pure-Python recursion (Rosetta agreement)
# ----------------------------------------------------------------------


def test_native_associator_matches_python_recursion():
    _require_native("srmech_loop_associator_f64")
    a, b, c = _unit(1), _unit(2), _unit(3)
    native = hdc._try_native_loop_associator(a, b, c)
    assert native is not None
    want = _vsub(hdc._loop_bind_raw(hdc._loop_bind_raw(a, b), c),
                 hdc._loop_bind_raw(a, hdc._loop_bind_raw(b, c)))
    assert mat_norm(_vsub(native, want)) < 1e-12


def test_native_left_op_matches_python_recursion():
    _require_native("srmech_loop_left_op_f64")
    a = _unit(4)
    native = hdc._try_native_loop_left_op(a)
    assert native is not None
    want = _colstack([hdc._loop_bind_raw(a, _basis(k)) for k in range(LOOP_DIM)])
    assert native.shape == (LOOP_DIM, LOOP_DIM)
    assert mat_norm(_mat_sub(native, want)) < 1e-12


def test_native_right_op_matches_python_recursion():
    _require_native("srmech_loop_right_op_f64")
    a = _unit(5)
    native = hdc._try_native_loop_right_op(a)
    assert native is not None
    want = _colstack([hdc._loop_bind_raw(_basis(k), a) for k in range(LOOP_DIM)])
    assert native.shape == (LOOP_DIM, LOOP_DIM)
    assert mat_norm(_mat_sub(native, want)) < 1e-12


# ----------------------------------------------------------------------
# the public wrappers return the native result when the peer is present
# ----------------------------------------------------------------------


def test_wrappers_dispatch_to_native_when_present():
    _require_native("srmech_loop_associator_f64")
    a, b, c = _unit(6), _unit(7), _unit(8)
    assert hdc.loop_associator(a, b, c) == hdc._try_native_loop_associator(a, b, c)
    assert hdc.loop_left_op(a) == hdc._try_native_loop_left_op(a)
    assert hdc.loop_right_op(a) == hdc._try_native_loop_right_op(a)


# ----------------------------------------------------------------------
# the associator's known octonion structure survives on the native path
# ----------------------------------------------------------------------


def test_associator_is_alternating_native():
    # The octonion associator is totally antisymmetric (alternating):
    #   [a,a,c] = 0  and  [a,b,c] = -[b,a,c].
    a, b, c = _unit(11), _unit(12), _unit(13)
    assert mat_norm(hdc.loop_associator(a, a, c)) < 1e-12
    neg = [-v for v in hdc.loop_associator(b, a, c)]
    assert mat_norm(_vsub(hdc.loop_associator(a, b, c), neg)) < 1e-12


def test_associator_zero_on_quaternionic_triple_native():
    # e1, e2, e3=e1·e2 lie in a quaternion subalgebra (associative) → assoc = 0.
    e1, e2 = _basis(1), _basis(2)
    e3 = hdc.loop_bind(e1, e2)
    assert mat_norm(hdc.loop_associator(e1, e2, e3)) < 1e-12


def test_left_op_right_op_columns_are_binds_native():
    # L_a e_k = a·e_k ; R_a e_k = e_k·a (column semantics).
    a = _unit(14)
    L, R = hdc.loop_left_op(a), hdc.loop_right_op(a)
    for k in range(LOOP_DIM):
        assert mat_norm(_vsub(_column(L, k), hdc.loop_bind(a, _basis(k)))) < 1e-12
        assert mat_norm(_vsub(_column(R, k), hdc.loop_bind(_basis(k), a))) < 1e-12


def _mat_sub(a: Mat, b: Mat) -> Mat:
    ar, br = a.tolist(), b.tolist()
    return Mat.from_rows([[ar[i][j] - br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))])
