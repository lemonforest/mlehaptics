"""Parity tests for ``srmech.amsc.cascade.chiral_dual``.

v0.4.5rc8 — the LAST cascade op in the C-parity + TOML retrofit arc
and the ONLY higher-order one. The C peer ``srmech_cascade_chiral_dual_f64``
uses a function-pointer callback ABI
(``srmech_cascade_op_callback_f64_t``); the Python dispatch wraps the
user's callable via ``ctypes.CFUNCTYPE``. Tests cover:

- identity / negation / non-trivial ops produce the expected
  conjugation result;
- ndarray / list / tuple inputs (homogeneous float64) take the native
  path;
- empty + singleton boundary cases;
- random sweep agreement between native and Python composition;
- callback exception propagation (Python ZeroDivisionError surfaces
  through the trampoline);
- callback wrong-length-output guard (ValueError);
- mixed-type sequences / strings / non-callable ops fall back to
  Python composition.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import chiral_dual, chiral_flip


SKIP_IF_NO_CHIRAL_DUAL_NATIVE = pytest.mark.skipif(
    not _native.HAS_NATIVE
    or _native.LIB is None
    or not hasattr(_native.LIB, "srmech_cascade_chiral_dual_f64"),
    reason="chiral_dual native symbol not available",
)


# ---------------------------------------------------------------------
# Basic semantic correctness
# ---------------------------------------------------------------------


def test_chiral_dual_identity_op_list():
    """Identity op: chiral_flip applied twice cancels."""
    result = chiral_dual(lambda v: v, [1.0, 2.0, 3.0])
    assert list(result) == [1.0, 2.0, 3.0]


def test_chiral_dual_negation_op_list():
    """Negation op: result is the element-wise negation (order unchanged
    because the two chiral_flips cancel around the order-preserving op)."""
    result = chiral_dual(lambda v: [-x for x in v], [1.0, 2.0, 3.0])
    assert list(result) == [-1.0, -2.0, -3.0]


def test_chiral_dual_non_trivial_op_agrees_with_python():
    """A non-order-preserving op (shift-by-one): the chiral-dual must
    agree with the pure-Python composition chiral_flip(op(chiral_flip(x)))."""
    def op(v):
        # Cycle-shift by one; not order-preserving so chiral_flip matters.
        out = list(v)
        if len(out) > 1:
            out = [out[-1]] + out[:-1]
        return out
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    py_ref = chiral_flip(op(chiral_flip(x)))
    result = chiral_dual(op, x)
    assert list(result) == list(py_ref)


def test_chiral_dual_tuple_preserves_type():
    """A tuple input should return a tuple."""
    result = chiral_dual(lambda v: [x * 2.0 for x in v], (1.0, 2.0, 3.0))
    assert isinstance(result, tuple)
    assert result == (2.0, 4.0, 6.0)


# ---------------------------------------------------------------------
# ndarray input
# ---------------------------------------------------------------------


def test_chiral_dual_ndarray_returns_ndarray():
    """An ndarray input should return an ndarray."""
    result = chiral_dual(np.negative, np.array([1.0, 2.0, 3.0]))
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([-1.0, -2.0, -3.0]))


def test_chiral_dual_ndarray_non_trivial_op():
    """Non-trivial op on ndarray agrees with Python composition."""
    def op(v):
        # Reverse + add 10 (not order-preserving)
        return v[::-1] + 10.0
    x = np.array([1.0, 2.0, 3.0, 4.0])
    py_ref = np.asarray(chiral_flip(op(chiral_flip(x))))
    result = chiral_dual(op, x)
    np.testing.assert_array_equal(np.asarray(result), py_ref)


def test_chiral_dual_ndarray_non_float64_falls_back():
    """An int64 ndarray should fall back to Python (no native int path)."""
    x = np.array([1, 2, 3], dtype=np.int64)
    # Identity-style op working on int sequences.
    result = chiral_dual(lambda v: v, x)
    # Python fallback returns whatever chiral_flip(op(chiral_flip(x)))
    # returns; for an int64 ndarray that's still an int64 ndarray.
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([1, 2, 3], dtype=np.int64))


# ---------------------------------------------------------------------
# Boundary cases
# ---------------------------------------------------------------------


def test_chiral_dual_empty_list():
    """Empty list: returns empty list."""
    result = chiral_dual(lambda v: v, [])
    assert result == [] or list(result) == []


def test_chiral_dual_singleton_list():
    """Singleton: a sequence of length 1 reverses to itself, so the
    chiral_dual reduces to op."""
    result = chiral_dual(lambda v: [v[0] * 2.0], [5.0])
    assert list(result) == [10.0]


def test_chiral_dual_empty_ndarray():
    """Empty ndarray: returns empty ndarray."""
    result = chiral_dual(lambda v: v, np.array([], dtype=np.float64))
    assert isinstance(result, np.ndarray)
    assert result.size == 0


# ---------------------------------------------------------------------
# Random sweep — native vs Python
# ---------------------------------------------------------------------


def test_chiral_dual_random_sweep_native_matches_python():
    """50-sample random sweep with a fixed op: native and Python
    composition agree to machine precision."""
    rng = random.Random(0xC0FFEE)
    for _ in range(50):
        n = rng.randint(0, 20)
        x = [rng.uniform(-100.0, 100.0) for _ in range(n)]
        op = lambda v: [val + 1.0 for val in v]
        py_ref = chiral_flip(op(chiral_flip(x)))
        result = chiral_dual(op, x)
        assert list(result) == list(py_ref), (
            f"native/Python divergence at n={n}: native={result} ref={py_ref}"
        )


# ---------------------------------------------------------------------
# Exception propagation through the callback trampoline
# ---------------------------------------------------------------------


@SKIP_IF_NO_CHIRAL_DUAL_NATIVE
def test_chiral_dual_callback_exception_propagates():
    """Python exception raised inside the op callback must surface as the
    same exception on the Python side — proving the trampoline captures
    the error and re-raises after the C function returns. Critical: a
    bare except + silent fall-through would let the failing op run a
    SECOND time on the Python path."""
    def bad_op(v):
        return 1 / 0  # noqa: E501 — intentional ZeroDivisionError
    with pytest.raises(ZeroDivisionError):
        chiral_dual(bad_op, [1.0, 2.0])


@SKIP_IF_NO_CHIRAL_DUAL_NATIVE
def test_chiral_dual_callback_wrong_length_raises():
    """If the op returns a sequence with the wrong length, the trampoline
    must surface a ValueError (not silently truncate or extend)."""
    with pytest.raises(ValueError, match="length"):
        chiral_dual(lambda v: [v[0]], [1.0, 2.0])


# ---------------------------------------------------------------------
# Fallback paths (Python composition)
# ---------------------------------------------------------------------


def test_chiral_dual_mixed_type_list_falls_back():
    """A mixed-int+float list falls back to Python composition."""
    result = chiral_dual(lambda v: v, [1, 2.0, 3])
    # Python fallback: chiral_flip(op(chiral_flip([1, 2.0, 3]))) =
    # chiral_flip([3, 2.0, 1]) = [1, 2.0, 3] (identity round-trip).
    assert list(result) == [1, 2.0, 3]


def test_chiral_dual_string_falls_back():
    """A string falls back to Python composition (str[::-1] in / out)."""
    # Identity op on the reversed string returns "cba"; reversing again
    # gives "abc".
    result = chiral_dual(lambda s: s, "abc")
    assert result == "abc"


def test_chiral_dual_string_uppercase_op():
    """A string with a transforming op exercises the Python fallback."""
    # chiral_flip("abc") = "cba"; op.upper() = "CBA"; chiral_flip("CBA")
    # = "ABC".
    result = chiral_dual(lambda s: s.upper(), "abc")
    assert result == "ABC"


def test_chiral_dual_non_callable_op_raises():
    """Passing a non-callable op falls back to Python which raises
    TypeError when Python tries to invoke it."""
    with pytest.raises(TypeError):
        chiral_dual(None, [1.0, 2.0, 3.0])


# ---------------------------------------------------------------------
# Native-symbol exposure
# ---------------------------------------------------------------------


@SKIP_IF_NO_CHIRAL_DUAL_NATIVE
def test_chiral_dual_native_symbol_available():
    """Sanity-check the C symbol + ctypes callback typedef are exposed."""
    assert hasattr(_native.LIB, "srmech_cascade_chiral_dual_f64")
    assert hasattr(_native, "CASCADE_OP_CALLBACK_F64")
    # The CFUNCTYPE should have the expected return type.
    cb_type = _native.CASCADE_OP_CALLBACK_F64
    # ctypes CFUNCTYPE objects don't expose argtypes directly but the
    # creation should not have raised; existence is the contract.
    assert cb_type is not None


@SKIP_IF_NO_CHIRAL_DUAL_NATIVE
def test_chiral_dual_native_path_returns_correct_type_for_list():
    """The native path returns a list when given a list."""
    result = chiral_dual(lambda v: v, [1.0, 2.0, 3.0])
    assert isinstance(result, list)


@SKIP_IF_NO_CHIRAL_DUAL_NATIVE
def test_chiral_dual_native_path_returns_tuple_for_tuple():
    """The native path returns a tuple when given a tuple."""
    result = chiral_dual(lambda v: v, (1.0, 2.0, 3.0))
    assert isinstance(result, tuple)


@SKIP_IF_NO_CHIRAL_DUAL_NATIVE
def test_chiral_dual_native_ndarray_dtype_preserved():
    """The native path returns a float64 ndarray when given one."""
    x = np.array([1.0, 2.0, 3.0])
    result = chiral_dual(lambda v: v, x)
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float64
