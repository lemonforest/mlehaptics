"""rc96 — multivariate_elliptic_jackson: the eq-5 Cₙ elliptic Jackson summation reducer.

Verifies the REDUCTION end-to-end: the op's closed-form theta-quotient product equals the
actual n-fold Cₙ very-well-poised sum over partitions (Rosengren arXiv:math/0101073 Thm 2.1
Eq 5), computed by an INDEPENDENT exact-ℚ theta oracle. Also pins Warnaar's Lemma 2.2 (the
inductive engine, the Cₙ binary-sum evaluation) in isolation. numpy-free (exact-ℚ + the
carrier's own truncated-theta eval; no float verdict).
"""

import itertools

import pytest

from srmech.amsc.ellbase import EllMonomial as M
from srmech.amsc.q import Q
from srmech.amsc.multivariate_elliptic_jackson import multivariate_elliptic_jackson

_TRUNC = 24
_P = Q(1, 19)


def _E(z):
    """Independent exact-ℚ modified theta θ(z;p) = ∏_{i=0}^{T-1}(1 - z pⁱ)(1 - p^{i+1}/z)."""
    acc = Q(1, 1)
    pj = Q(1, 1)
    for _ in range(_TRUNC):
        acc = acc * (Q(1, 1) - z * pj) * (Q(1, 1) - (_P * pj) / z)
        pj = pj * _P
    return acc


def _poch(u, k, q):
    v = Q(1, 1)
    for i in range(k):
        v = v * _E(u * q ** i)
    return v


def _cn_sum(a, b, c, d, x, q, N, n):
    """The independent n-fold Cₙ VWP sum (Rosengren Thm 2.1 LHS), exact-ℚ. e by balancing."""
    e = a * a * q ** (N + 1) / (b * c * d * x ** (n - 1))

    def vpoch(u, lam):
        v = Q(1, 1)
        for j in range(1, n + 1):
            v = v * _poch(u * x ** (1 - j), lam[j - 1], q)
        return v

    def summand(lam):
        v = Q(1, 1)
        for i in range(1, n + 1):
            li = lam[i - 1]
            v = v * _E(a * x ** (2 * (1 - i)) * q ** (2 * li)) / _E(a * x ** (2 * (1 - i)))
            v = v * q ** li * x ** (2 * (i - 1) * li)
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                li, lj = lam[i - 1], lam[j - 1]
                v = v * _E(x ** (j - i) * q ** (li - lj)) / _E(x ** (j - i))
                v = v * _E(a * x ** (2 - i - j) * q ** (li + lj)) / _E(a * x ** (2 - i - j))
                v = v * _poch(a * x ** (3 - i - j), li + lj, q) * _poch(x ** (j - i + 1), li - lj, q)
                v = v / (_poch(a * q * x ** (1 - i - j), li + lj, q)
                         * _poch(q * x ** (j - i - 1), li - lj, q))
        num_bases = [a * x ** (1 - n), b, c, d, e, q ** (-N)]
        den_bases = [q * x ** (n - 1), a * q / b, a * q / c, a * q / d, a * q / e, a * q ** (N + 1)]
        for u in num_bases:
            v = v * vpoch(u, lam)
        for u in den_bases:
            v = v / vpoch(u, lam)
        return v

    total = Q(0, 1)
    for lam in itertools.product(range(N + 1), repeat=n):
        if all(lam[t] >= lam[t + 1] for t in range(n - 1)):
            total = total + summand(lam)
    return total


_VALS = {"p": _P, "a": Q(4, 7), "b": Q(3, 8), "c": Q(5, 9),
         "d": Q(7, 12), "x": Q(2, 3), "q": Q(2, 1)}


@pytest.mark.parametrize("n,N", [(2, 1), (2, 2), (3, 1)])
def test_closed_form_equals_cn_sum(n, N):
    a, b, c, d, x, q = (M.symbol(s) for s in ("a", "b", "c", "d", "x", "q"))
    closed = multivariate_elliptic_jackson(a, b, c, d, x, q, N, n).eval_trunc(_VALS, _TRUNC)
    lhs = _cn_sum(_VALS["a"], _VALS["b"], _VALS["c"], _VALS["d"], _VALS["x"], _VALS["q"], N, n)
    rel = abs(float(lhs - closed)) / (abs(float(lhs)) + abs(float(closed)) + 1e-40)
    assert rel < 1e-10


def test_n1_is_the_frenkel_turaev_8w7():
    # n=1: the Cₙ sum degenerates to the single-variable ₈ω₇ (Frenkel–Turaev) sum.
    a, b, c, d, x, q = (M.symbol(s) for s in ("a", "b", "c", "d", "x", "q"))
    for N in (1, 2, 3):
        closed = multivariate_elliptic_jackson(a, b, c, d, x, q, N, 1).eval_trunc(_VALS, _TRUNC)
        lhs = _cn_sum(_VALS["a"], _VALS["b"], _VALS["c"], _VALS["d"], _VALS["x"], _VALS["q"], N, 1)
        assert abs(float(lhs - closed)) / (abs(float(lhs)) + abs(float(closed)) + 1e-40) < 1e-10


def test_warnaar_lemma_2_2_engine():
    """Warnaar's Lemma 2.2 (the inductive engine of Thm 2.1): the Cₙ binary-sum
    (k ∈ {0,1}ⁿ) with the balancing a²q^{3-n} = bcde equals the product (Rosengren
    arXiv:math/0101073 Lemma 2.2 / Eq 6). Verified in isolation by the independent exact-ℚ
    theta oracle at n=2 (a²q = bcde), with distinct variables x1, x2:

        Σ_{k1,k2∈{0,1}} ∏_i [∏_{u∈{b,c,d,e}} θ(u x_i)/θ(aq x_i/u)]^{k_i}
            · θ(q^{k1-k2} x1/x2)/θ(x1/x2) · θ(a x1 x2 q^{k1+k2})/θ(a x1 x2 q)
            · (-1)^{k1+k2} q^{k2}
        = (aq/bc, aq/bd, aq/cd; q^{-1})_2
          · ∏_i θ(aq x_i²) / [θ(a/(bcd x_i)) θ(aq x_i/b) θ(aq x_i/c) θ(aq x_i/d)].
    """
    a, b, c, d, q = Q(4, 7), Q(3, 8), Q(5, 9), Q(7, 12), Q(2, 1)
    x1, x2 = Q(2, 3), Q(5, 4)                        # distinct variables
    e = a * a * q / (b * c * d)                      # n=2 balancing a²q = bcde
    xs = [x1, x2]

    def term(k1, k2):
        v = Q(1, 1)
        for i, ki in enumerate((k1, k2)):
            if ki == 1:
                xi = xs[i]
                for u in (b, c, d, e):
                    v = v * _E(u * xi) / _E(a * q * xi / u)
        v = v * _E(q ** (k1 - k2) * x1 / x2) / _E(x1 / x2)          # θ(q^{k1-k2} x1/x2)/θ(x1/x2)
        v = v * _E(a * x1 * x2 * q ** (k1 + k2)) / _E(a * x1 * x2 * q)  # θ(a x1 x2 q^{k1+k2})/θ(a x1 x2 q)
        v = v * Q((-1) ** ((k1 + k2) % 2), 1) * q ** k2            # (-1)^{k1+k2} q^{k2}
        return v

    lhs = Q(0, 1)
    for k1 in (0, 1):
        for k2 in (0, 1):
            lhs = lhs + term(k1, k2)

    rhs = Q(1, 1)
    for pr in (b * c, b * d, c * d):                 # (aq/pr; q^{-1})_2 = θ(aq/pr)·θ(a/pr)
        rhs = rhs * _E(a * q / pr) * _E(a / pr)
    for xi in xs:
        rhs = rhs * _E(a * q * xi * xi)
        rhs = rhs / (_E(a / (b * c * d * xi)) * _E(a * q * xi / b)
                     * _E(a * q * xi / c) * _E(a * q * xi / d))

    rel = abs(float(lhs - rhs)) / (abs(float(lhs)) + abs(float(rhs)) + 1e-40)
    assert rel < 1e-6


def test_shape_validation():
    a = M.symbol("a")
    with pytest.raises(ValueError):
        multivariate_elliptic_jackson(a, a, a, a, a, a, 0, 2)   # N < 1
    with pytest.raises(ValueError):
        multivariate_elliptic_jackson(a, a, a, a, a, a, 1, 0)   # n < 1
    with pytest.raises(TypeError):
        multivariate_elliptic_jackson(1, a, a, a, a, a, 1, 2)   # non-EllMonomial
