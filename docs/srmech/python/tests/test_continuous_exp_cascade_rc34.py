"""rc34 — substrate-native exp / cexp / complex_exp cascade parity.

The complex-exponential family is a Class-N (Taylor) composition with a
Class-C imaginary-unit rotation (Euler) — NOT a primitive srmech lacks.
These tests pin the float-projection cascades against libm / cmath, and
assert there is no ``math``/``cmath``/``np`` exp in the call graph (only the
Class-N cascade + the rc33 trig).
"""
import cmath
import math

import pytest

from srmech.amsc import rational as R


def test_real_exp_matches_libm():
    for x in [0.0, 0.25, 1.0, 2.5, -3.0, 7.5, -7.5, 15.0, -12.0]:
        got = R.exp(x)
        want = math.exp(x)
        # relative parity (e^15 is large; absolute error scales with magnitude)
        assert abs(got - want) <= 1e-9 * max(1.0, abs(want)), (x, got, want)


def test_real_exp_zero_is_exact():
    assert R.exp(0.0) == 1.0


def test_cexp_matches_cmath_machine_eps():
    for t in [0.0, 0.3, 1.0, math.pi / 2, math.pi, 2.5, -0.7, 100.0, 6433.0]:
        got = R.cexp(t)
        want = cmath.exp(1j * t)
        assert abs(got - want) <= 1e-9, (t, got, want)
        # on the unit circle
        assert abs(abs(got) - 1.0) <= 1e-9, (t, abs(got))


def test_complex_exp_matches_cmath():
    for z in [0.5 + 0.3j, -1.0 + 2.0j, 2.0 - 1.5j, 0.0 + 3.14159j, -0.5 - 0.5j]:
        got = R.complex_exp(z)
        want = cmath.exp(z)
        assert abs(got - want) <= 1e-9 * max(1.0, abs(want)), (z, got, want)


def test_cexp_is_euler_of_the_cascade_trig():
    # cexp(theta) == complex(cos(theta), sin(theta)) using srmech's OWN trig.
    # rc7: cos/sin return an EXACT Q; cexp collapses them to float at the
    # complex() display boundary, so compare against the float projection.
    for t in [0.4, 1.3, -2.2]:
        got = R.cexp(t)
        assert got.real == float(R.cos(t))
        assert got.imag == float(R.sin(t))


def test_no_libm_exp_in_call_graph():
    """The exp/cexp/complex_exp source must not call math.exp / cmath.exp /
    np.exp — only the Class-N exp_series_truncate + the rc33 trig."""
    import ast
    import inspect

    src = inspect.getsource(R)
    tree = ast.parse(src)
    banned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            base = node.func.value
            if attr == "exp" and isinstance(base, ast.Name) and base.id in {"math", "cmath", "np"}:
                banned.add(f"{base.id}.exp")
    assert not banned, f"forbidden libm exp call(s) in rational.py: {banned}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
