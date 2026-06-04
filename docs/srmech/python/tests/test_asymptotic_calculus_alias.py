"""rc26 — srmech.asymptotic_calculus / srmech.trigonometry alias modules.

The documented ``srmech.asymptotic_calculus.*`` import path (CLAUDE.md §2)
had no importable module — the continuous-calculus primitives live in
:mod:`srmech.amsc.rational` (Class N) + the
``srmech/amsc/attested/asymptotic_calculus/`` catalog. rc26 ships thin
re-export modules so the advertised path resolves; this test pins the
re-export identity (same callables, not copies) and that the surface is
importable + callable.
"""
import importlib

import srmech.asymptotic_calculus as ac
import srmech.trigonometry as trig
from srmech.amsc import rational as R


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


def test_sin_series_truncate_returns_rational_tuple():
    """The substrate-native 'continuous' trig returns an exact rational."""
    out = ac.sin_series_truncate(1, 2, 8)
    assert isinstance(out, tuple) and len(out) == 2
    num, den = out
    assert isinstance(num, int) and isinstance(den, int) and den != 0
    # sin(0.5) ≈ 0.4794; the rational should be within a loose band.
    assert abs(num / den - 0.479425) < 1e-3
