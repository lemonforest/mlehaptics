"""rc26 — srmech.asymptotic_calculus / srmech.trigonometry alias modules.

The documented ``srmech.asymptotic_calculus.*`` import path (CLAUDE.md §2)
had no importable module — the continuous-calculus primitives live in
:mod:`srmech.math.rational` (Class N) + the
``srmech/amsc/attested/asymptotic_calculus/`` catalog. rc26 ships thin
re-export modules so the advertised path resolves; this test pins the
re-export identity (same callables, not copies) and that the surface is
importable + callable.
"""
import importlib

import srmech.asymptotic_calculus as ac
import srmech.trigonometry as trig
from srmech.math import rational as R
from srmech.math.q import Q


def test_asymptotic_calculus_imports():
    assert importlib.import_module("srmech.asymptotic_calculus") is ac


def test_trigonometry_imports():
    assert importlib.import_module("srmech.trigonometry") is trig


def test_reexport_identity_not_copies():
    """The alias re-exports the *same* callables (no divergent copies)."""
    for name in (
        "sin_series_truncate",
        "cos_series_truncate",
        "exp_series_truncate",
        "log1p_series_truncate",
        "atan_series_truncate",
        "best_rational",
        "continued_fraction",
        "continued_fraction_convergents",
        "rational_add",
        "rational_mul",
        "rational_div",
        "rational_pow_uint",
        "pi_cascade_digits",
    ):
        assert getattr(ac, name) is getattr(R, name), name


def test_trigonometry_is_the_trig_subset():
    for name in ("sin_series_truncate", "cos_series_truncate",
                 "atan_series_truncate"):
        assert getattr(trig, name) is getattr(R, name), name


def test_everything_in_dunder_all_is_present():
    for name in ac.__all__:
        assert hasattr(ac, name), name
    for name in trig.__all__:
        assert hasattr(trig, name), name


def test_sin_series_truncate_returns_exact_q():
    """The substrate-native 'continuous' trig returns an exact rational.

    rc452 (`#T1166`) — the RETURN-TYPE PIN, flipped with the contract it pins.
    Through rc451 this asserted ``isinstance(out, tuple)``; the nine
    chain-dispatched Class-N ops now return :class:`srmech.math.q.Q`, the same
    exact-ℚ scalar the C ops build as ``CR_RATIONAL`` and the chain wire spells
    ``q``. The pin is not weakened by the flip — ``Q`` is a STRICTER assertion
    than ``tuple``, because a 2-tuple of ints is also what a Class-K pin pair
    and a Class-B ``pair`` step return, and telling those apart is the whole
    point of the rc.

    The function was renamed with the assertion: a test still called
    ``..._returns_rational_tuple`` while asserting a ``Q`` is a falsehood that
    ships in the sdist. This is the ONE edit in rc452's test sweep that is not
    the mechanical subscript→accessor pattern, and it is declared as such.

    ``num, den = out`` below is UNCHANGED and still passes: ``Q`` defines
    ``__iter__``, so unpacking a rational into its two ints keeps working. What
    a ``Q`` does not have is ``[0]`` — it is a scalar, not a container.
    """
    out = ac.sin_series_truncate(1, 2, 8)
    assert isinstance(out, Q), type(out).__name__
    num, den = out
    assert isinstance(num, int) and isinstance(den, int) and den != 0
    # sin(0.5) ≈ 0.4794; the rational should be within a loose band.
    assert abs(num / den - 0.479425) < 1e-3
