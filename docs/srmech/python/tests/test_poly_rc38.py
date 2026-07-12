"""srmech 0.9.0rc38 — the exact-rational polynomial carrier ``Poly`` (the §76
"telescope" foundation). Numpy-free, math-free.

Covers: construction + canonical trim; degree / leading / is_zero conventions;
+ / - / scalar / polynomial * vs hand-computed; exact long division
(``self == q*other + r`` with ``deg r < deg other``, incl. exact-ℚ non-integer
coefficients); monic Euclidean GCD (divides both + monic + matches a known GCD);
exact Horner eval; the dispersion ``shift`` (``p.shift(h).eval(x) == p.eval(x+h)``);
derivative; the float-boundary collapse.

KEYSTONE bignum parity: huge-rational-coefficient polynomials are run through
divmod / gcd / eval and checked against a ``fractions.Fraction`` oracle EXACTLY —
proving there is no magnitude ceiling (the coefficients exceed ``2**64``).

Python==C parity: when the native ``srmech_poly_*`` peer is present, the C path is
asserted byte/value-exact against the pure-Python path on the bignum keystone
(skipped cleanly when native is absent — the pure path is the complete
alternative + the oracle).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q


# ── a tiny Fraction-list polynomial oracle (independent reimplementation) ──────
def _f_trim(cs):
    cs = list(cs)
    while cs and cs[-1] == 0:
        cs.pop()
    return cs


def _f_mul(a, b):
    a, b = _f_trim(a), _f_trim(b)
    if not a or not b:
        return []
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return _f_trim(out)


def _f_divmod(a, b):
    a, b = _f_trim(a), _f_trim(b)
    assert b, "divide by zero polynomial"
    rem = list(a)
    quo = [Fraction(0)] * (max(len(rem) - len(b), -1) + 1) if len(rem) >= len(b) else []
    while _f_trim(rem) and len(_f_trim(rem)) - 1 >= len(b) - 1:
        rem = _f_trim(rem)
        rdeg = len(rem) - 1
        shift = rdeg - (len(b) - 1)
        factor = rem[rdeg] / b[-1]
        quo[shift] = factor
        for j in range(len(b)):
            rem[shift + j] -= factor * b[j]
        rem = _f_trim(rem)
    return _f_trim(quo), _f_trim(rem)


def _f_monic(p):
    p = _f_trim(p)
    if not p:
        return []
    inv = Fraction(1) / p[-1]
    return [c * inv for c in p]


def _f_gcd(a, b):
    a, b = _f_trim(a), _f_trim(b)
    while b:
        a, b = b, _f_divmod(a, b)[1]
    return _f_monic(a)


def _f_eval(p, x):
    acc = Fraction(0)
    for c in reversed(_f_trim(p)):
        acc = acc * x + c
    return acc


def _coeffs_as_fracs(poly):
    return [Fraction(c.numerator, c.denominator) for c in poly.coeffs]


# ── construction / canonical trim ─────────────────────────────────────────────
def test_construction_and_trim():
    p = Poly.from_coeffs([1, 2, 3, 0, 0])
    assert p.coeffs == (Q(1), Q(2), Q(3))            # trailing zeros dropped
    assert len(p) == 3
    assert p.from_ints([4, 0, 5]).coeffs == (Q(4), Q(0), Q(5))
    assert Poly.from_coeffs([(1, 2), (3, 4)]).coeffs == (Q(1, 2), Q(3, 4))
    assert Poly.from_coeffs([Fraction(2, 3)]).coeffs == (Q(2, 3),)


def test_float_coeff_rejected():
    with pytest.raises(TypeError):
        Poly.from_coeffs([1.5, 2])
    # the float boundary is explicit:
    p = Poly.from_floats([0.5, 0.25])
    assert p.coeffs == (Q(1, 2), Q(1, 4))


def test_degree_leading_iszero_conventions():
    z = Poly.zero()
    assert z.is_zero and z.degree == -1 and z.leading == Q(0) and len(z) == 0
    o = Poly.one()
    assert o.degree == 0 and o.leading == Q(1) and not o.is_zero
    p = Poly.from_coeffs([0, 0, 7])
    assert p.degree == 2 and p.leading == Q(7)
    # indexing past degree returns Q(0); negative index rejected
    assert p[5] == Q(0) and p[2] == Q(7)
    with pytest.raises(IndexError):
        _ = p[-1]


def test_monomial():
    assert Poly.monomial(3).coeffs == (Q(0), Q(0), Q(0), Q(1))
    assert Poly.monomial(2, Q(5)).coeffs == (Q(0), Q(0), Q(5))
    assert Poly.monomial(4, 0).is_zero


# ── arithmetic vs hand-computed ───────────────────────────────────────────────
def test_add_sub_scalar():
    a = Poly.from_coeffs([1, 2, 3])
    b = Poly.from_coeffs([0, 1])
    assert (a + b).coeffs == (Q(1), Q(3), Q(3))
    assert (a - b).coeffs == (Q(1), Q(1), Q(3))
    assert (b - a).coeffs == (Q(-1), Q(-1), Q(-3))
    assert (-a).coeffs == (Q(-1), Q(-2), Q(-3))
    assert (a * 2).coeffs == (Q(2), Q(4), Q(6))
    assert (2 * a).coeffs == (Q(2), Q(4), Q(6))
    assert (a * Q(1, 3)).coeffs == (Q(1, 3), Q(2, 3), Q(1))
    # add cancels to zero polynomial (trim to empty)
    assert (a + (-a)).is_zero


def test_poly_mul():
    a = Poly.from_coeffs([1, 2, 3])          # 1 + 2x + 3x^2
    b = Poly.from_coeffs([0, 1])             # x
    assert (a * b).coeffs == (Q(0), Q(1), Q(2), Q(3))
    # (x+1)(x-1) = x^2 - 1
    p = Poly.from_coeffs([1, 1]) * Poly.from_coeffs([-1, 1])
    assert p.coeffs == (Q(-1), Q(0), Q(1))
    # multiply by zero polynomial
    assert (a * Poly.zero()).is_zero


# ── exact long division ───────────────────────────────────────────────────────
@pytest.mark.parametrize("num,den", [
    ([-1, 0, 1], [-1, 1]),                   # (x^2-1)/(x-1) = x+1, r 0
    ([2, 0, 0, 1], [1, 1]),                  # (x^3+2)/(x+1)
    ([5, 0, 3, 0, 1], [1, 0, 1]),            # (x^4+3x^2+5)/(x^2+1)
    ([(1, 2), (1, 3), 1], [(2, 5), 1]),      # exact-ℚ non-integer coeffs
    ([7], [1, 2, 3]),                        # deg num < deg den -> q=0, r=num
])
def test_divmod_invariant(num, den):
    n = Poly.from_coeffs(num)
    d = Poly.from_coeffs(den)
    q, r = divmod(n, d)
    # self == q*other + r
    assert (q * d + r) == n
    # deg r < deg den (or r == 0)
    assert r.is_zero or r.degree < d.degree
    # // and % agree
    assert (n // d) == q and (n % d) == r


def test_divmod_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divmod(Poly.from_coeffs([1, 2]), Poly.zero())


# ── monic Euclidean GCD ───────────────────────────────────────────────────────
def test_gcd_known():
    # gcd(x^2-1, x-1) = x-1 (monic)
    g = Poly.from_coeffs([-1, 0, 1]).gcd(Poly.from_coeffs([-1, 1]))
    assert g.coeffs == (Q(-1), Q(1))         # x - 1, monic
    # leading coefficient is 1
    assert g.leading == Q(1)


def test_gcd_shared_factor_divides_both():
    # (x-1)(x-2) and (x-1)(x-3) share (x-1)
    f1 = Poly.from_coeffs([1, 1]) * Poly.from_coeffs([-2, 1])   # x^2-?  (x+1)(x-2)
    # use genuine shared factor (x-1):
    a = Poly.from_coeffs([-1, 1]) * Poly.from_coeffs([-2, 1])   # (x-1)(x-2)
    b = Poly.from_coeffs([-1, 1]) * Poly.from_coeffs([-3, 1])   # (x-1)(x-3)
    g = a.gcd(b)
    assert g.coeffs == (Q(-1), Q(1))         # x - 1, monic
    # gcd divides both exactly (remainder 0)
    assert a.divmod(g)[1].is_zero and b.divmod(g)[1].is_zero
    assert g.leading == Q(1)
    del f1


def test_gcd_zero_cases():
    p = Poly.from_coeffs([2, 4])             # 2 + 4x
    assert Poly.zero().gcd(Poly.zero()).is_zero
    # gcd(p, 0) = monic(p) = (1/2 + x)
    g = p.gcd(Poly.zero())
    assert g.coeffs == (Q(1, 2), Q(1)) and g.leading == Q(1)


# ── eval (Horner) ─────────────────────────────────────────────────────────────
def _as_q(x):
    if isinstance(x, Q):
        return x
    if isinstance(x, Fraction):
        return Q(x.numerator, x.denominator)
    return Q(x)


def test_eval_matches_direct():
    p = Poly.from_coeffs([1, 2, 3])          # 1 + 2x + 3x^2
    for x in (0, 1, 2, -3, Q(1, 2), Fraction(2, 3)):
        qx = _as_q(x)
        direct = Q(1) + Q(2) * qx + Q(3) * qx * qx
        assert p.eval(x) == direct
    assert Poly.zero().eval(99) == Q(0)


# ── dispersion shift p(x+h) ───────────────────────────────────────────────────
@pytest.mark.parametrize("coeffs", [
    [1, 2, 3], [5], [0, 0, 0, 1], [(1, 2), 1, (3, 4), 2],
])
@pytest.mark.parametrize("h", [0, 1, -1, 2, Q(1, 2), -3])
def test_shift_eval_identity(coeffs, h):
    p = Poly.from_coeffs(coeffs)
    qh = _as_q(h)
    for x in (0, 1, 2, -4, Q(3, 5)):
        qx = _as_q(x)
        assert p.shift(h).eval(x) == p.eval(qx + qh)


def test_shift_zero_polynomial():
    assert Poly.zero().shift(7).is_zero


# ── derivative ────────────────────────────────────────────────────────────────
def test_derivative():
    p = Poly.from_coeffs([1, 2, 3])          # d/dx = 2 + 6x
    assert p.derivative().coeffs == (Q(2), Q(6))
    assert Poly.from_coeffs([5]).derivative().is_zero
    assert Poly.zero().derivative().is_zero


# ── to_floats boundary ────────────────────────────────────────────────────────
def test_to_floats():
    p = Poly.from_coeffs([(1, 2), (1, 4)])
    assert p.to_floats() == [0.5, 0.25]
    assert Poly.zero().to_floats() == []


# ── equality / hashing / repr ─────────────────────────────────────────────────
def test_eq_hash_repr():
    a = Poly.from_coeffs([1, 2, 3])
    b = Poly.from_coeffs([1, 2, 3, 0])       # trims equal
    assert a == b and hash(a) == hash(b)
    assert a == [1, 2, 3]                      # coercible sequence compare
    assert a != Poly.from_coeffs([1, 2, 4])
    assert "degree=2" in repr(a)


# ── KEYSTONE: bignum parity (coefficients exceed 2**64) ───────────────────────
def _huge_poly():
    """A polynomial with huge-rational coefficients (numerators/denominators far
    past 2**64) — the magnitude-ceiling stress."""
    cs = [
        Q(10 ** 40 + 1, 3 ** 30),
        Q(-(7 ** 50), 11 ** 20),
        Q(2 ** 70 + 3, 5 ** 25),
        Q(13 ** 30, 17 ** 18),
        Q(1, 1),
    ]
    return Poly.from_coeffs(cs)


def test_bignum_divmod_matches_fraction_oracle():
    a = _huge_poly()
    b = Poly.from_coeffs([Q(2 ** 64 + 1, 9), Q(-(3 ** 41), 7), Q(1)])  # deg-2 divisor
    q, r = divmod(a, b)
    # invariant holds exactly
    assert (q * b + r) == a
    assert r.is_zero or r.degree < b.degree
    # vs the independent Fraction oracle
    fq, fr = _f_divmod(_coeffs_as_fracs(a), _coeffs_as_fracs(b))
    assert _coeffs_as_fracs(q) == fq
    assert _coeffs_as_fracs(r) == fr


def test_bignum_gcd_matches_fraction_oracle():
    # build two polynomials sharing a huge-coefficient linear factor
    shared = Poly.from_coeffs([Q(-(10 ** 50), 3 ** 33), Q(1)])         # x - 10^50/3^33
    a = shared * Poly.from_coeffs([Q(7 ** 40, 13), Q(2)])
    b = shared * Poly.from_coeffs([Q(-(5 ** 44), 17), Q(3)])
    g = a.gcd(b)
    # g divides both exactly
    assert a.divmod(g)[1].is_zero and b.divmod(g)[1].is_zero
    assert g.leading == Q(1)                  # monic
    # vs Fraction oracle (exact coefficient match)
    fg = _f_gcd(_coeffs_as_fracs(a), _coeffs_as_fracs(b))
    assert _coeffs_as_fracs(g) == fg


def test_bignum_eval_matches_fraction_oracle():
    a = _huge_poly()
    x = Q(2 ** 65 + 7, 3 ** 19)
    got = a.eval(x)
    oracle = _f_eval(_coeffs_as_fracs(a), Fraction(x.numerator, x.denominator))
    assert Fraction(got.numerator, got.denominator) == oracle


def test_bignum_shift_matches_eval_identity():
    a = _huge_poly()
    h = Q(-(7 ** 33), 2 ** 41)
    x = Q(3 ** 21, 5 ** 14)
    assert a.shift(h).eval(x) == a.eval(x + h)


# ── Python == C parity (native present only) ──────────────────────────────────
def _native_poly():
    """Return the native ``_poly`` parity helper module, or ``None`` if the C
    peer is absent (no-C / pre-rc38 lib)."""
    try:
        from srmech.amsc import _native
    except ImportError:
        return None
    if not getattr(_native, "has_native_poly", lambda: False)():
        return None
    return _native


def test_python_equals_c_bignum_keystone():
    nat = _native_poly()
    if nat is None:
        pytest.skip("native srmech_poly_* peer absent — pure path is the complete alternative")
    a = _huge_poly()
    b = Poly.from_coeffs([Q(2 ** 64 + 1, 9), Q(-(3 ** 41), 7), Q(1)])
    # divmod — the C peer vs the pure path (build pairs explicitly)
    a_pairs = [(c.numerator, c.denominator) for c in a.coeffs]
    b_pairs = [(c.numerator, c.denominator) for c in b.coeffs]
    cq, cr = nat.poly_divmod_c(a_pairs, b_pairs)
    pq, pr = divmod(a, b)
    assert tuple(cq) == tuple((c.numerator, c.denominator) for c in pq.coeffs)
    assert tuple(cr) == tuple((c.numerator, c.denominator) for c in pr.coeffs)
    # mul
    cm = nat.poly_mul_c(a_pairs, b_pairs)
    pm = a * b
    assert tuple(cm) == tuple((c.numerator, c.denominator) for c in pm.coeffs)
    # eval
    x = Q(2 ** 65 + 7, 3 ** 19)
    cv = nat.poly_eval_c(a_pairs, (x.numerator, x.denominator))
    pv = a.eval(x)
    assert cv == (pv.numerator, pv.denominator)
    # shift
    h = Q(-(7 ** 33), 2 ** 41)
    cs = nat.poly_shift_c(a_pairs, (h.numerator, h.denominator))
    ps = a.shift(h)
    assert tuple(cs) == tuple((c.numerator, c.denominator) for c in ps.coeffs)
    # NOTE: gcd C is deferred to rc39-prefix; Poly.gcd stays on the pure-bigint
    # path (its inner long divisions route through srmech_poly_divmod). The
    # bignum gcd parity vs the Fraction oracle is covered by
    # test_bignum_gcd_matches_fraction_oracle (pure path).
