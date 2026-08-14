"""rc433 (`#T1131`) — the siblings the pinned sites would have left behind.

WHY THIS MODULE EXISTS
======================
rc433 promoted twelve package ``assert``\\ s to real ``raise`` statements
because a test somewhere pinned each one. That is exactly the failure mode this
project keeps hitting: **the test coverage decides what gets repaired.**

``assert isinstance(..., Mat)`` appears IDENTICALLY in six Class-L ops —
``mat_matmul``, ``mat_solve``, ``mat_lstsq``, ``mat_hermitian_eigendecompose``,
``mat_eigvals``, ``mat_svd``. Only ``mat_matmul`` was pinned by a test. Fixing
only the pinned one would have left five identical live defects standing purely
because nobody had written a test for them, and an ungated surface becomes
BELIEVED ABSENT. The same reasoning covers the two big-ℚ zero-denominator
guards and the single-element ``loop_inv``.

Every op below was UNPINNED before this module. Measured under ``python -O`` at
rc432, all five ``mat_*`` siblings failed the same way::

    AttributeError: 'list' object has no attribute 'n_rows'

— the callee's PRIVATE attribute name escaping as if it were the contract.

The ``-O`` INVARIANCE of these same contracts is gated separately, in
``tests/test_input_contracts_rc431.py`` §1, which already runs each case in a
fresh interpreter with and without ``-O``. This module gates the TYPE; that one
gates the mode-invariance.
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.math import hdc, laplacian
from srmech.math.mat import Mat


# ── 1. the five unpinned Class-L carrier-type siblings ────────────────────

#: ``(op_name, args)`` — each arg list carries a plain list where a ``Mat`` is
#: required. ``mat_matmul`` is deliberately ABSENT: it is pinned by
#: ``test_mat_matmul_bridge_rc72.py`` and this roster is the set that had NO
#: test at all.
_NON_MAT = [[1.0, 0.0], [0.0, 1.0]]

_UNARY_MAT_OPS = ["mat_hermitian_eigendecompose", "mat_eigvals", "mat_svd"]
_BINARY_MAT_OPS = ["mat_solve", "mat_lstsq"]


@pytest.mark.parametrize("op_name", _UNARY_MAT_OPS)
def test_unary_mat_op_rejects_non_mat(op_name):
    """FALSIFIER: revert the ``raise`` to an ``assert`` and this still passes
    in the default interpreter — which is precisely why the ``-O`` roster in
    ``test_input_contracts_rc431.py`` exists alongside it. Here we pin the
    TYPE, so a silent downgrade to ``AttributeError`` is caught."""
    op = getattr(laplacian, op_name)
    with pytest.raises(TypeError, match="must be Mat"):
        op(_NON_MAT)


@pytest.mark.parametrize("op_name", _BINARY_MAT_OPS)
def test_binary_mat_op_rejects_non_mat_in_either_position(op_name):
    """Both operand positions — a mixed ``(Mat, list)`` call failed the same
    way under ``-O``, so fixing only the all-lists case would be half a fix."""
    op = getattr(laplacian, op_name)
    good = Mat.from_rows([[1.0, 0.0], [0.0, 1.0]])
    with pytest.raises(TypeError, match="must be Mat"):
        op(_NON_MAT, _NON_MAT)
    with pytest.raises(TypeError, match="must be Mat"):
        op(good, _NON_MAT)
    with pytest.raises(TypeError, match="must be Mat"):
        op(_NON_MAT, good)


@pytest.mark.parametrize("op_name", _UNARY_MAT_OPS + _BINARY_MAT_OPS)
def test_the_same_ops_still_accept_a_real_mat(op_name):
    """POSITIVE CONTROL — a gate that fires on correct code is a broken gate.

    Without this, the three tests above would pass just as well against an op
    that rejected EVERYTHING, including valid input.
    """
    op = getattr(laplacian, op_name)
    a = Mat.from_rows([[2.0, 0.0], [0.0, 1.0]])
    b = Mat.from_rows([[1.0], [1.0]])
    result = op(a, b) if op_name in _BINARY_MAT_OPS else op(a)
    assert result is not None


# ── 2. the two unpinned big-ℚ zero-denominator guards ─────────────────────
#
# NOTE ON REACHABILITY, stated openly. Both public entry points
# (``_reduce_rational`` and ``rational_div``) already raise ZeroDivisionError
# for this input BEFORE dispatching here, so these guards are NOT reachable
# through the ordinary rational API. They are reachable by a direct call — a
# shipped test already makes one (``test_fast_gcd_rc169.py`` calls
# ``_native.bigq_reduce_c`` directly) — and rc433 additionally hoisted each
# check ABOVE the ``has_native_bigq()`` early return, because whether an
# argument is valid cannot depend on whether an accelerator happens to be
# loaded. Below that early return the guard was unreachable, and therefore
# untestable, in any native-absent environment — including this one.


def test_bigq_reduce_c_rejects_a_zero_denominator():
    """``ZeroDivisionError``, matching the pure projection of the same op."""
    with pytest.raises(ZeroDivisionError, match="den"):
        _native.bigq_reduce_c(5, 0)


def test_the_two_rational_reduce_projections_agree_on_a_zero_denominator():
    """CO-EQUAL PROJECTIONS must raise the SAME type (rc433, `#T1131`).

    This is the load-bearing one, and it is why ``bigq_reduce_c`` raises
    ``ZeroDivisionError`` rather than ``ValueError``.

    The tree draws a real distinction — an op that DIVIDES raises
    ``ZeroDivisionError``, an op merely VALIDATING an input pair raises
    ``ValueError``. Read mechanically, ``bigq_reduce_c`` looks like the second
    kind: inside ``_bigq_reduce_inplace`` the denominator is a DIVIDEND
    (divided by the gcd), never a divisor.

    But ``bigq_reduce_c`` IS ``_reduce_rational`` on the C bignum — its
    docstring declares the two byte-identical — and ``_reduce_rational``
    (``rational.py:662``) raises ``ZeroDivisionError`` here. srmech is
    multi-implementation with co-equal projections, so a divergence would make
    the raised type depend on whether ``libsrmech`` happened to load.

    FALSIFIER: re-type either projection alone and this fails. It compares the
    two to EACH OTHER rather than pinning a literal, so it stays correct even
    if the pair is later moved to a different type together.
    """
    from srmech.math import rational

    pure, native = None, None
    try:
        rational._reduce_rational(5, 0)
    except BaseException as exc:  # noqa: BLE001
        pure = type(exc)
    try:
        _native.bigq_reduce_c(5, 0)
    except BaseException as exc:  # noqa: BLE001
        native = type(exc)

    assert pure is not None and native is not None, (
        f"one projection did not raise at all: pure={pure}, native={native}")
    assert pure is native, (
        f"the pure projection raises {pure.__name__} but the native dispatch "
        f"raises {native.__name__} for the same (5, 0) — co-equal projections "
        f"of one op must agree, or the type depends on whether libsrmech loaded")


def test_bigq_div_c_rejects_a_zero_divisor_numerator():
    with pytest.raises(ZeroDivisionError, match="b_num"):
        _native.bigq_div_c(1, 2, 0, 1)


def test_bigq_helpers_still_return_none_for_valid_args_without_native():
    """POSITIVE CONTROL for the hoist.

    The validation moved ABOVE the ``has_native_bigq()`` early return. If that
    hoist had broken the contract, VALID arguments would now raise instead of
    returning ``None``/a pair. Whichever way native availability falls, a valid
    call must NOT raise — that is the invariant this pins.
    """
    assert _native.bigq_reduce_c(4, 6) in (None, (2, 3))
    assert _native.bigq_div_c(1, 2, 3, 4) in (None, (2, 3))


# ── 3. the single-element loop_inv zero vector ────────────────────────────


def test_loop_inv_zero_vector_raises_zero_division():
    """The single-element peer of the pinned ``loop_inv_hd`` guard.

    ``loop_inv_hd``'s per-block zero check was pinned; this one-element
    ``loop_inv`` was not, despite being the same algebra and the same failure.
    Under ``-O`` both already produced ``ZeroDivisionError`` from ``1.0/nsq``,
    so the assert was MASKING the ruled-correct type in the default mode.
    """
    with pytest.raises(ZeroDivisionError, match="zero vector"):
        hdc.loop_inv([0.0] * 8)


def test_loop_inv_still_inverts_a_nonzero_vector():
    """POSITIVE CONTROL — the guard must not have swallowed the happy path."""
    out = hdc.loop_inv([1.0] + [0.0] * 7)
    assert len(out) == 8 and out[0] == 1.0
