"""Tests for the v0.4.3rc6 foundational cross-domain cascade catalog.

``srmech.amsc.cascade`` promotes the cascades imported across 20+
unsolved-maths scripts (precursor ``docs/unsolved-maths/_cascade_helpers.py``)
into srmech as a composition catalog. Coverage:

- Class K ``pin_slot_at_zero`` orientation/magnitude split.
- ``magnitude`` matches ``|x|`` (the cascade-honest abs() replacement).
- Class C ``reorient`` sign re-application.
- Class K∘N∘C ``best_rational_signed`` rational anchor (sign in numerator,
  positive denominator, bounded denominator, origin → (0,1)).
- Class I ``cyclic_gcd`` matches ``math.gcd``.
- Back-compat aliases identity.
- Validation + registry / ``__all__`` membership.

No ``abs()`` in the module under test — verified structurally.
"""

from __future__ import annotations

import math

import pytest

from srmech.amsc import cascade


# ----------------------------------------------------------------------
# Class K — pin_slot_at_zero / magnitude
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "x,expected",
    [
        (3.5, (+1, 3.5)),
        (-2.0, (-1, 2.0)),
        (0.0, (0, 0.0)),
        (1e-30, (+1, 1e-30)),
        (-1e-30, (-1, 1e-30)),
    ],
)
def test_pin_slot_at_zero(x, expected):
    assert cascade.pin_slot_at_zero(x) == expected


def test_pin_slot_orientation_in_three_state_alphabet():
    for x in (-5.0, 0.0, 5.0):
        orient, mag = cascade.pin_slot_at_zero(x)
        assert orient in (-1, 0, 1)
        assert mag >= 0.0


@pytest.mark.parametrize("x", [3.5, -2.0, 0.0, -1e-9, 1e9, -1e9])
def test_magnitude_matches_abs(x):
    assert cascade.magnitude(x) == abs(x)


# ----------------------------------------------------------------------
# Class C — reorient
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "orientation,value,expected",
    [(-1, 5, -5), (+1, 5, 5), (0, 5, 5), (-1, 2.5, -2.5)],
)
def test_reorient(orientation, value, expected):
    assert cascade.reorient(value, orientation=orientation) == expected


def test_pin_slot_reorient_round_trip():
    for x in (3.5, -2.0, 0.0):
        orient, mag = cascade.pin_slot_at_zero(x)
        assert cascade.reorient(mag, orientation=orient) == x


# ----------------------------------------------------------------------
# Class K∘N∘C — best_rational_signed
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "x,expected",
    [(0.5, (1, 2)), (-0.75, (-3, 4)), (0.25, (1, 4)), (0.0, (0, 1)), (-1e-30, (0, 1))],
)
def test_best_rational_signed_known_values(x, expected):
    assert cascade.best_rational_signed(x) == expected


def test_best_rational_signed_pi_anchor():
    n, d = cascade.best_rational_signed(math.pi, max_denominator=100)
    assert d <= 100 and n > 0
    assert abs(n / d - math.pi) < 1e-2  # 22/7 territory


def test_best_rational_signed_sign_lives_in_numerator():
    n, d = cascade.best_rational_signed(-math.e, max_denominator=50)
    assert n < 0, "negative input -> negative numerator (Class C)"
    assert d > 0, "denominator stays positive (sign not split into it)"


def test_best_rational_signed_denominator_bounded():
    for md in (5, 20, 100):
        _, d = cascade.best_rational_signed(math.sqrt(2), max_denominator=md)
        assert 1 <= d <= md


@pytest.mark.parametrize("bad", [{"max_denominator": 0}, {"fine_scale": 0}])
def test_best_rational_signed_rejects_bad_params(bad):
    with pytest.raises(ValueError):
        cascade.best_rational_signed(0.5, **bad)


# ----------------------------------------------------------------------
# Class I — cyclic_gcd
# ----------------------------------------------------------------------


@pytest.mark.parametrize("a,b", [(12, 18), (17, 5), (100, 75), (0, 7), (1, 1)])
def test_cyclic_gcd_matches_math_gcd(a, b):
    assert cascade.cyclic_gcd(a, b) == math.gcd(a, b)


# ----------------------------------------------------------------------
# Back-compat aliases + registry
# ----------------------------------------------------------------------


def test_back_compat_aliases_are_identity():
    assert cascade.class_k_pin_slot_at_zero is cascade.pin_slot_at_zero
    assert cascade.class_c_reorient is cascade.reorient
    assert cascade.best_rat_signed is cascade.best_rational_signed


def test_cascade_ops_registry_and_all():
    for name in cascade.CASCADE_OPS:
        assert name in cascade.__all__
        assert callable(getattr(cascade, name))
    assert cascade.DEFAULT_MAX_DENOMINATOR == 100
    assert cascade.DEFAULT_FINE_SCALE == 1_000_000


def test_no_abs_call_in_source():
    """Cascade-honesty: the module handles sign via Class K/C, never abs().

    AST-level (not string-level): a literal ``abs()`` *call* would fail, but
    the word ``abs()`` appearing in the docstring prose (where the principle
    is explained) is fine.
    """
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(cascade))
    abs_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "abs"
    ]
    assert not abs_calls, "cascade module must not call abs() (Class K/C only)"
