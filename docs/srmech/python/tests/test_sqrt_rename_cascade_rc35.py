"""rc35 — Class-N sqrt/hypot cascade + the asymptotic_calculus → calculus rename.

sqrt = Class-N rational Newton (integer floor-isqrt on a scaled bignum) ∘
Class-K convergence; hypot = Class-M sum-of-squares bind ∘ sqrt. The module
``srmech.asymptotic_calculus`` is renamed to ``srmech.calculus`` with a
no-break back-compat alias.
"""
import math

import pytest

from srmech.amsc import rational as R


def test_sqrt_matches_libm():
    for x in [0.0, 1.0, 2.0, 7.5, 0.25, 1e6, 1e-6, 123456.789, 2.0 ** 60]:
        assert abs(R.sqrt(x) - math.sqrt(x)) <= 1e-12 * max(1.0, math.sqrt(x)), x


def test_sqrt_negative_raises():
    with pytest.raises(ValueError):
        R.sqrt(-1.0)


def test_hypot_matches_libm():
    for a, b in [(3.0, 4.0), (1.0, 1.0), (-5.0, 12.0), (0.3, 0.4), (1e3, 1e3), (0.0, 0.0)]:
        assert abs(R.hypot(a, b) - math.hypot(a, b)) <= 1e-12 * max(1.0, math.hypot(a, b)), (a, b)


def test_sqrt_no_libm_in_call_graph():
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(R))
    banned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "sqrt" and isinstance(node.func.value, ast.Name) and node.func.value.id in {"math", "np"}:
                banned.add(f"{node.func.value.id}.sqrt")
    assert not banned, f"forbidden libm sqrt call(s) in rational.py: {banned}"


def test_calculus_canonical_module():
    from srmech import calculus
    for name in ("cos", "sin", "exp", "cexp", "complex_exp", "sqrt", "hypot",
                 "sin_series_truncate", "pi_cascade_digits", "best_rational"):
        assert hasattr(calculus, name), name


def test_asymptotic_calculus_is_backcompat_alias():
    """Old import path keeps working and re-exports the SAME callables."""
    from srmech import calculus
    from srmech import asymptotic_calculus as ac
    # same function objects (a true alias, not a divergent copy)
    for name in ("sqrt", "hypot", "cos", "sin", "exp", "cexp", "complex_exp"):
        assert getattr(ac, name) is getattr(calculus, name), name
    assert ac.__all__ == calculus.__all__


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
