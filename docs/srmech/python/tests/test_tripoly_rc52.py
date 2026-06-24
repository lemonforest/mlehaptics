"""srmech 0.9.0rc52 — the exact-rational TRIVARIATE polynomial carrier ``TriPoly``
(``ℚ[n,j,k]``; the 3-variable sibling of ``BiPoly`` and the foundation of the
multivariate "sums of sums" creative-telescoping row the rc53 ``apagodu_zeilberger``
op consumes). Numpy-free, math-free.

Covers:

* construction (``from_dict`` / ``from_coeffs`` / ``monomial`` / ``zero`` / ``one``)
  + canonical trim; degree accessors in n/j/k;
* the algebra LAWS — commutativity / associativity of ``+``, distributivity of
  ``*`` over ``+``, associativity of ``*`` — all checked exactly against a
  ``fractions.Fraction`` sparse-monomial oracle;
* ``eval`` consistency (the carrier value at sampled integer points equals the
  oracle value), including across ``+`` / ``-`` / ``*``;
* the shift operators ``shift_n`` / ``shift_j`` / ``shift_k`` (``f.shift_x(s)``
  evaluated at a point equals ``f`` at the shifted point);
* the DIFFERENCE operators ``delta_j`` / ``delta_k`` and the telescoping identity
  ``Σ_{j=0}^{m} delta_j(G)(n,j,k) == G(n,m+1,k) − G(n,0,k)`` (exact over ℚ — the
  rc53 Apagodu–Zeilberger contract);
* a representability check that the term ratios of ``F(n,j,k) =
  C(n,j)·C(n,k)·C(j+k,j)`` fit the carrier (the pieces, not the telescoping —
  that is rc53);
* the bignum keystone (coefficients past ``2**64``) exercised exactly vs the
  ``Fraction`` oracle — proving there is no magnitude ceiling;
* Python==C parity: when the native ``srmech_tripoly_*`` peer is present, the C
  path is asserted byte/value-exact against the pure-Python path on the bignum
  keystone (skipped cleanly when native is absent — the pure path is the complete
  alternative + the oracle).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.tripoly import TriPoly


# ── a tiny sparse-monomial Fraction oracle (independent reimplementation) ──────
#
# A polynomial is a dict {(dn, dj, dk): Fraction}. This is a deliberately
# different representation from the carrier's nested-block form, so agreement is
# a genuine cross-check, not a tautology.

def _o_norm(terms):
    return {k: v for k, v in terms.items() if v != 0}


def _o_add(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, Fraction(0)) + v
    return _o_norm(out)


def _o_sub(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, Fraction(0)) - v
    return _o_norm(out)


def _o_mul(a, b):
    out = {}
    for (an, aj, ak), av in a.items():
        for (bn, bj, bk), bv in b.items():
            key = (an + bn, aj + bj, ak + bk)
            out[key] = out.get(key, Fraction(0)) + av * bv
    return _o_norm(out)


def _o_eval(terms, n, j, k):
    s = Fraction(0)
    for (dn, dj, dk), c in terms.items():
        s += c * Fraction(n) ** dn * Fraction(j) ** dj * Fraction(k) ** dk
    return s


def _o_shift(terms, var, s):
    """Substitute one variable -> variable + s, expanded back to monomials."""
    idx = {"n": 0, "j": 1, "k": 2}[var]
    out = {}
    for key, c in terms.items():
        d = key[idx]
        # (var + s)^d expanded by the binomial theorem, exact integer coeffs.
        for t in range(d + 1):
            binom = _comb(d, t)
            newkey = list(key)
            newkey[idx] = t
            newkey = tuple(newkey)
            out[newkey] = out.get(newkey, Fraction(0)) + c * binom * Fraction(s) ** (d - t)
    return _o_norm(out)


def _comb(n, r):
    if r < 0 or r > n:
        return 0
    num = 1
    den = 1
    for i in range(r):
        num *= (n - i)
        den *= (i + 1)
    return num // den


def _asF(q):
    return Fraction(q.numerator, q.denominator)


def _tri(terms):
    """Build a TriPoly from a {(dn,dj,dk): int/Fraction} dict."""
    return TriPoly.from_dict({k: (Q(v.numerator, v.denominator)
                                  if isinstance(v, Fraction) else v)
                              for k, v in terms.items()})


# ── sample polynomials (mix of degrees + exact-ℚ + sign) ──────────────────────
_TA = {(0, 0, 0): Fraction(2), (1, 1, 0): Fraction(3), (0, 0, 1): Fraction(1, 2),
       (2, 1, 1): Fraction(5), (0, 2, 0): Fraction(-7, 3), (0, 0, 2): Fraction(4)}
_TB = {(0, 0, 0): Fraction(-1), (0, 1, 1): Fraction(7), (1, 0, 0): Fraction(3, 4),
       (1, 1, 1): Fraction(-2)}
_TC = {(0, 0, 0): Fraction(1), (0, 1, 0): Fraction(-1), (0, 0, 1): Fraction(2, 5)}

_PTS = [(n, j, k) for n in range(-2, 3) for j in range(-2, 3) for k in range(-2, 3)]


# ── construction + accessors ──────────────────────────────────────────────────
def test_zero_one_and_trim():
    z = TriPoly.zero()
    assert z.is_zero
    assert z.j_degree == -1 and z.k_degree == -1 and z.n_degree == -1
    o = TriPoly.one()
    assert not o.is_zero
    assert o.j_degree == 0 and o.k_degree == 0 and o.n_degree == 0
    assert o.eval(Q(5), Q(9), Q(-3)) == Q(1)
    # a polynomial whose top blocks/terms are zero trims to canonical form.
    a = TriPoly.from_dict({(0, 0, 0): 0, (1, 0, 0): 3})
    assert a.j_degree == 0 and a.k_degree == 0 and a.n_degree == 1


def test_degree_accessors():
    a = _tri(_TA)
    assert a.j_degree == 2     # j^2 term
    assert a.k_degree == 2     # k^2 term
    assert a.n_degree == 2     # n^2 term
    assert a.coeff(2, 1, 1) == Q(5)
    assert a.coeff(0, 2, 0) == Q(-7, 3)
    assert a.coeff(9, 9, 9) == Q(0)


def test_monomial_and_from_dict_agree():
    m = TriPoly.monomial(2, 1, 1, Q(5))
    a = TriPoly.from_dict({(2, 1, 1): 5})
    assert m == a
    for (n, j, k) in _PTS:
        assert m.eval(Q(n), Q(j), Q(k)) == Q(5) * Q(n) ** 2 * Q(j) * Q(k)


def test_from_dict_rejects_float_and_negative_degree():
    with pytest.raises(TypeError):
        TriPoly.from_dict({(0, 0, 0): 1.5})
    with pytest.raises(ValueError):
        TriPoly.from_dict({(-1, 0, 0): 1})


# ── eval consistency vs the oracle ────────────────────────────────────────────
def test_eval_matches_oracle():
    a = _tri(_TA)
    for (n, j, k) in _PTS:
        assert _asF(a.eval(Q(n), Q(j), Q(k))) == _o_eval(_TA, n, j, k)


# ── algebra LAWS (vs the Fraction oracle) ─────────────────────────────────────
def test_add_sub_match_oracle():
    a, b = _tri(_TA), _tri(_TB)
    s, d = a + b, a - b
    os, od = _o_add(_TA, _TB), _o_sub(_TA, _TB)
    for (n, j, k) in _PTS:
        assert _asF(s.eval(Q(n), Q(j), Q(k))) == _o_eval(os, n, j, k)
        assert _asF(d.eval(Q(n), Q(j), Q(k))) == _o_eval(od, n, j, k)


def test_mul_matches_oracle():
    a, b = _tri(_TA), _tri(_TB)
    p = a * b
    op = _o_mul(_TA, _TB)
    for (n, j, k) in _PTS:
        assert _asF(p.eval(Q(n), Q(j), Q(k))) == _o_eval(op, n, j, k)


def test_add_is_commutative_and_associative():
    a, b, c = _tri(_TA), _tri(_TB), _tri(_TC)
    assert a + b == b + a
    assert (a + b) + c == a + (b + c)


def test_mul_is_commutative_and_associative():
    a, b, c = _tri(_TA), _tri(_TB), _tri(_TC)
    assert a * b == b * a
    assert (a * b) * c == a * (b * c)


def test_mul_distributes_over_add():
    a, b, c = _tri(_TA), _tri(_TB), _tri(_TC)
    assert a * (b + c) == a * b + a * c
    assert (a + b) * c == a * c + b * c


def test_scalar_multiply():
    a = _tri(_TA)
    s = a * Q(3, 7)
    for (n, j, k) in _PTS:
        assert _asF(s.eval(Q(n), Q(j), Q(k))) == _o_eval(_TA, n, j, k) * Fraction(3, 7)
    assert (a * Q(0)).is_zero


def test_neg_and_self_difference_is_zero():
    a = _tri(_TA)
    assert (a + (-a)).is_zero
    assert (a - a).is_zero


# ── shift operators (var -> var + s) ──────────────────────────────────────────
@pytest.mark.parametrize("s", [-2, -1, 1, 2, 3])
def test_shift_n_j_k_match_oracle(s):
    a = _tri(_TA)
    sn, sj, sk = a.shift_n(s), a.shift_j(s), a.shift_k(s)
    on = _o_shift(_TA, "n", s)
    oj = _o_shift(_TA, "j", s)
    ok = _o_shift(_TA, "k", s)
    for (n, j, k) in _PTS:
        assert _asF(sn.eval(Q(n), Q(j), Q(k))) == _o_eval(on, n, j, k)
        assert _asF(sj.eval(Q(n), Q(j), Q(k))) == _o_eval(oj, n, j, k)
        assert _asF(sk.eval(Q(n), Q(j), Q(k))) == _o_eval(ok, n, j, k)
    # the direct definition: shift_x(s) at (n,j,k) == f at the shifted point.
    for (n, j, k) in _PTS:
        assert sn.eval(Q(n), Q(j), Q(k)) == a.eval(Q(n + s), Q(j), Q(k))
        assert sj.eval(Q(n), Q(j), Q(k)) == a.eval(Q(n), Q(j + s), Q(k))
        assert sk.eval(Q(n), Q(j), Q(k)) == a.eval(Q(n), Q(j), Q(k + s))


def test_shift_zero_is_identity():
    a = _tri(_TA)
    assert a.shift_n(0) == a and a.shift_j(0) == a and a.shift_k(0) == a


# ── DIFFERENCE operators + the telescoping identity (the rc53 contract) ────────
def test_delta_j_delta_k_match_definition():
    a = _tri(_TA)
    dj, dk = a.delta_j(), a.delta_k()
    for (n, j, k) in _PTS:
        assert dj.eval(Q(n), Q(j), Q(k)) == (
            a.eval(Q(n), Q(j + 1), Q(k)) - a.eval(Q(n), Q(j), Q(k)))
        assert dk.eval(Q(n), Q(j), Q(k)) == (
            a.eval(Q(n), Q(j), Q(k + 1)) - a.eval(Q(n), Q(j), Q(k)))


def test_delta_j_telescoping_identity():
    """Σ_{j=0}^{m} delta_j(G)(n,j,k) == G(n,m+1,k) − G(n,0,k) — exact over ℚ."""
    g_terms = {(1, 2, 1): Fraction(3), (0, 1, 0): Fraction(-2),
               (2, 0, 1): Fraction(5, 2), (0, 3, 2): Fraction(1),
               (0, 0, 0): Fraction(7)}
    G = _tri(g_terms)
    dG = G.delta_j()
    for m in range(0, 5):
        for n in range(-2, 3):
            for k in range(-2, 3):
                lhs = Q(0)
                for jj in range(0, m + 1):
                    lhs = lhs + dG.eval(Q(n), Q(jj), Q(k))
                rhs = (G.eval(Q(n), Q(m + 1), Q(k)) - G.eval(Q(n), Q(0), Q(k)))
                assert lhs == rhs


def test_delta_k_telescoping_identity():
    """The k-partner: Σ_{k=0}^{m} delta_k(G)(n,j,k) == G(n,j,m+1) − G(n,j,0)."""
    g_terms = {(1, 1, 2): Fraction(3), (0, 0, 1): Fraction(-2),
               (2, 1, 0): Fraction(5, 2), (0, 2, 3): Fraction(1),
               (0, 0, 0): Fraction(7)}
    G = _tri(g_terms)
    dG = G.delta_k()
    for m in range(0, 5):
        for n in range(-2, 3):
            for j in range(-2, 3):
                lhs = Q(0)
                for kk in range(0, m + 1):
                    lhs = lhs + dG.eval(Q(n), Q(j), Q(kk))
                rhs = (G.eval(Q(n), Q(j), Q(m + 1)) - G.eval(Q(n), Q(j), Q(0)))
                assert lhs == rhs


def test_joint_certificate_shape_assembles():
    """The rc53 joint-certificate shape Σ_i a_i(n)·F(n+i,j,k) = Δ_j G_j + Δ_k G_k
    must be EXPRESSIBLE with the carrier API (we assemble both sides exactly and
    confirm the algebra closes — the actual SOLVE is rc53). Here we just confirm
    the difference operators + the shift_n ladder + the ℚ-scaled add compose into
    one TriPoly identity."""
    F = _tri(_TA)
    Gj = _tri(_TB)
    Gk = _tri(_TC)
    # an arbitrary order-2 left side ladder with Poly-in-n (here constant) coeffs.
    lhs = F.shift_n(0) * Q(1) + F.shift_n(1) * Q(-3) + F.shift_n(2) * Q(2)
    rhs = Gj.delta_j() + Gk.delta_k()
    diff = lhs - rhs
    # diff is a perfectly good TriPoly; evaluate it at points (closure check).
    for (n, j, k) in _PTS[:30]:
        v = diff.eval(Q(n), Q(j), Q(k))
        assert isinstance(v, Q)


# ── C(n,j)·C(n,k)·C(j+k,j) term-ratio representability ─────────────────────────
def test_binomial_product_term_ratios_representable():
    """F(n,j,k) = C(n,j)·C(n,k)·C(j+k,j). Its term ratios are rational functions
    of (n,j,k) whose numerator + denominator pieces are polynomials — the carrier
    must HOLD them exactly (rc53 telescopes them; rc52 only confirms the pieces).

      r_n = F(n+1,j,k)/F(n,j,k) = (n+1)^2 / [ (n+1-j)(n+1-k) ]
    """
    rn_num = TriPoly.from_dict({(2, 0, 0): 1, (1, 0, 0): 2, (0, 0, 0): 1})  # (n+1)^2
    # (n+1-j)(n+1-k) = (n+1)^2 - (n+1)k - (n+1)j + jk
    rn_den = TriPoly.from_dict({
        (2, 0, 0): 1, (1, 0, 0): 2, (0, 0, 0): 1,    # (n+1)^2
        (1, 0, 1): -1, (0, 0, 1): -1,                 # -(n+1)k
        (1, 1, 0): -1, (0, 1, 0): -1,                 # -(n+1)j
        (0, 1, 1): 1,                                 # +jk
    })
    for n in range(0, 5):
        for j in range(0, 5):
            for k in range(0, 5):
                assert _asF(rn_num.eval(Q(n), Q(j), Q(k))) == Fraction((n + 1) ** 2)
                assert _asF(rn_den.eval(Q(n), Q(j), Q(k))) == Fraction(n + 1 - j) * Fraction(n + 1 - k)
    # r_j = F(n,j+1,k)/F(n,j,k) = (n-j)/(j+1) · (j+k+1)/(k+1)·... pieces:
    #   numerator   (n-j)(j+k+1),  denominator  (j+1)(k+1) ... all representable.
    # (n-j)(j+k+1) = n*j + n*k + n - j^2 - j*k - j
    rj_num = TriPoly.from_dict({(1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 1,
                                (0, 2, 0): -1, (0, 1, 1): -1, (0, 1, 0): -1})
    for n in range(0, 5):
        for j in range(0, 5):
            for k in range(0, 5):
                assert _asF(rj_num.eval(Q(n), Q(j), Q(k))) == Fraction(n - j) * Fraction(j + k + 1)
    # the carrier even holds the full product F's piece C(j+k,j) numerator (j+k)!
    # ratio factor (j+k+1) as a TriPoly — degree (j,k)=(1,1), representable.
    cfac = TriPoly.from_dict({(0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 1})  # j+k+1
    assert cfac.j_degree == 1 and cfac.k_degree == 1


# ── bignum keystone (no magnitude ceiling) ────────────────────────────────────
def _huge():
    """A TriPoly whose coefficients exceed 2**64 — exercises the bignum path."""
    return TriPoly.from_dict({
        (0, 0, 0): Q(10 ** 40 + 1, 3 ** 30),
        (2, 1, 0): Q(-(7 ** 41), 11),
        (1, 0, 2): Q(2 ** 70 + 3, 5 ** 19),
        (0, 2, 1): Q(13 ** 25, 2),
    })


def _huge_b():
    return TriPoly.from_dict({
        (0, 0, 0): Q(-(2 ** 65), 9),
        (1, 1, 1): Q(3 ** 41 + 1, 7),
        (0, 0, 1): Q(10 ** 30, 2 ** 17),
    })


def test_bignum_keystone_vs_fraction_oracle():
    a, b = _huge(), _huge_b()
    ta = {key: _asF(a.coeff(*key)) for key in
          [(0, 0, 0), (2, 1, 0), (1, 0, 2), (0, 2, 1)]}
    tb = {key: _asF(b.coeff(*key)) for key in
          [(0, 0, 0), (1, 1, 1), (0, 0, 1)]}
    s, d, p = a + b, a - b, a * b
    os, od, op = _o_add(ta, tb), _o_sub(ta, tb), _o_mul(ta, tb)
    for (n, j, k) in [(3, 2, 1), (-2, 1, 4), (5, -3, 2), (0, 0, 0), (1, 1, 1)]:
        assert _asF(s.eval(Q(n), Q(j), Q(k))) == _o_eval(os, n, j, k)
        assert _asF(d.eval(Q(n), Q(j), Q(k))) == _o_eval(od, n, j, k)
        assert _asF(p.eval(Q(n), Q(j), Q(k))) == _o_eval(op, n, j, k)


# ── the float boundary collapse (the ONE rotation) ────────────────────────────
def test_to_floats_is_the_only_float():
    a = TriPoly.from_dict({(0, 0, 0): Q(1, 2), (1, 1, 1): Q(3, 4)})
    grid = a.to_floats()
    # j-block 0 has k-term 0 (the constant 1/2 in n^0) and j-block 1 carries 3/4.
    assert grid[0][0][0] == 0.5
    assert grid[1][1][1] == 0.75


# ── Python == C parity (native present only; byte-identical) ───────────────────
def _native_tripoly():
    try:
        from srmech.amsc import _native
    except ImportError:
        return None
    if not getattr(_native, "has_native_tripoly", lambda: False)():
        return None
    return _native


def _grid_pairs(t: TriPoly):
    """The nested [[[(num,den)…]_n]_k]_j bridge form (matches _tri_pairs)."""
    out = []
    for bib in t.blocks:
        kgrid = []
        for kp in bib.terms:
            kgrid.append([(c.numerator, c.denominator) for c in kp.coeffs])
        out.append(kgrid)
    return out


def _pad_grid(grid, oj, ok):
    """Pad a bridge grid to the (oj x ok) rectangle (missing cells → empty)."""
    out = []
    for dj in range(oj):
        kg = grid[dj] if dj < len(grid) else []
        row = [kg[dk] if dk < len(kg) else [] for dk in range(ok)]
        out.append(row)
    return out


def _trim_grid(grid):
    """Trim trailing-empty j-blocks / k-terms so a padded grid compares equal to
    the carrier's canonical bridge form."""
    out = []
    for kg in grid:
        krow = list(kg)
        while krow and not krow[-1]:
            krow.pop()
        out.append(krow)
    while out and not out[-1]:
        out.pop()
    return [list(kg) for kg in out]


def test_python_equals_c_bignum_keystone():
    nat = _native_tripoly()
    if nat is None:
        pytest.skip("native srmech_tripoly_* peer absent — pure path is the complete alternative")
    a, b = _huge(), _huge_b()
    ag, bg = _grid_pairs(a), _grid_pairs(b)

    # add — the C peer vs the pure path, byte-identical (trim-normalized).
    cs = nat.tripoly_add_c(ag, bg)
    ps = a + b
    assert _trim_grid(cs) == _grid_pairs(ps)

    # sub
    cd = nat.tripoly_sub_c(ag, bg)
    pd = a - b
    assert _trim_grid(cd) == _grid_pairs(pd)

    # mul (the 2-D (j,k) convolution)
    cm = nat.tripoly_mul_c(ag, bg)
    pm = a * b
    assert _trim_grid(cm) == _grid_pairs(pm)


def test_python_equals_c_small_random_grids():
    nat = _native_tripoly()
    if nat is None:
        pytest.skip("native srmech_tripoly_* peer absent — pure path is the complete alternative")
    a, b, c = _tri(_TA), _tri(_TB), _tri(_TC)
    for x in (a, b, c):
        for y in (a, b, c):
            xg, yg = _grid_pairs(x), _grid_pairs(y)
            assert _trim_grid(nat.tripoly_add_c(xg, yg)) == _grid_pairs(x + y)
            assert _trim_grid(nat.tripoly_sub_c(xg, yg)) == _grid_pairs(x - y)
            assert _trim_grid(nat.tripoly_mul_c(xg, yg)) == _grid_pairs(x * y)
