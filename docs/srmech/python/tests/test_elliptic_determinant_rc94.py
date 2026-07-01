"""rc94 — elliptic_cauchy_determinant: Frobenius's elliptic Cauchy determinant evaluation.

The constructed closed form (Rosengren Ex 1.6.6) must equal the determinant of the theta
matrix det_{i,j}[theta(t x_i y_j)/theta(x_i y_j)] — verified by the carrier's own exact-Q
truncated-theta eval vs a cofactor-expansion determinant of the same matrix at exact-Q
sample points. numpy-free.
"""

import itertools

import pytest

from srmech.amsc.ellbase import EllMonomial as M, Theta
from srmech.amsc.q import Q
from srmech.amsc.elliptic_determinant import elliptic_cauchy_determinant

_TRUNC = 20
_VALS_BASE = {"p": Q(1, 19), "t": Q(4, 7)}
_XV = [Q(2, 3), Q(5, 4), Q(9, 8), Q(7, 11)]
_YV = [Q(3, 5), Q(7, 6), Q(11, 10), Q(4, 13)]


def _det_leibniz(mat):
    n = len(mat)
    tot = Q(0, 1)
    for perm in itertools.permutations(range(n)):
        s = 1
        pl = list(perm)
        for i in range(n):
            for j in range(i + 1, n):
                if pl[i] > pl[j]:
                    s = -s
        term = Q(s, 1)
        for i in range(n):
            term = term * mat[i][perm[i]]
        tot = tot + term
    return tot


def _setup(n):
    t = M.symbol("t")
    xs = [M.symbol(f"x{i}") for i in range(n)]
    ys = [M.symbol(f"y{j}") for j in range(n)]
    vals = dict(_VALS_BASE)
    for i in range(n):
        vals[f"x{i}"] = _XV[i]
        vals[f"y{i}"] = _YV[i]
    return t, xs, ys, vals


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_frobenius_closed_form_equals_matrix_determinant(n):
    t, xs, ys, vals = _setup(n)
    mat = [[Theta(t * xs[i] * ys[j]).eval_trunc(vals, _TRUNC)
            / Theta(xs[i] * ys[j]).eval_trunc(vals, _TRUNC)
            for j in range(n)] for i in range(n)]
    det = _det_leibniz(mat)
    closed = elliptic_cauchy_determinant(t, xs, ys).eval_trunc(vals, _TRUNC)
    # both sides use the SAME truncation depth; they agree to the truncation floor.
    rel = abs(float(det - closed)) / (abs(float(det)) + abs(float(closed)) + 1e-40)
    assert rel < 1e-10


def test_n1_is_the_trivial_entry():
    # det of a 1x1 matrix is its single entry: theta(t x1 y1)/theta(x1 y1).
    t, xs, ys, vals = _setup(1)
    closed = elliptic_cauchy_determinant(t, xs, ys).eval_trunc(vals, _TRUNC)
    entry = (Theta(t * xs[0] * ys[0]).eval_trunc(vals, _TRUNC)
             / Theta(xs[0] * ys[0]).eval_trunc(vals, _TRUNC))
    assert abs(float(closed - entry)) < 1e-12


def test_shape_validation():
    a = M.symbol("a")
    with pytest.raises(ValueError):
        elliptic_cauchy_determinant(a, [a, a], [a])   # len mismatch
    with pytest.raises(ValueError):
        elliptic_cauchy_determinant(a, [], [])        # empty
    with pytest.raises(TypeError):
        elliptic_cauchy_determinant(a, [1], [a])      # non-EllMonomial variable
