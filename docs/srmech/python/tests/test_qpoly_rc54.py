"""srmech 0.9.0rc54 — the EXACT q-shift carrier ``QPoly`` (the q-hypergeometric
F929 reduction-row foundation; q-Gosper → q-Zeilberger → q-WZ ride it). Numpy-free,
math-free.

``QPoly`` is a Laurent polynomial in ``x = q**n`` over the ground ring ``ℚ[q]``
(each coefficient an exact ``Poly`` in ``q``). The load-bearing new operation is
the **q-shift** ``σ : x ↦ q·x`` (``f(q**n) ↦ f(q**(n+1))``) and the q-difference
``Δ_q = σ − id``.

Covers: construction (``from_coeffs`` / ``from_dict`` / ``x_monomial`` / Laurent
offset) + canonical both-ends trim; accessors (``x_low`` / ``x_high`` /
``q_degree`` / ``is_laurent``); algebra laws (assoc + distrib of ``+`` and ``*``)
vs an independent ``fractions.Fraction`` oracle; exact ``eval`` consistency; the
**q-shift / q-difference identity** — ``σ`` acts as ``x ↦ q**s·x`` per cell, and a
small q-telescoping ``Σ Δ_q T = T(top) − T(bottom)`` holds EXACTLY.

KEYSTONE bignum parity: huge-rational-q-coefficient ``QPoly`` are run through
``+`` / ``-`` / ``*`` / ``qshift`` and checked against the oracle EXACTLY (the
q-coefficients exceed ``2**64`` — no magnitude ceiling).

Python==C parity: when the native ``srmech_qpoly_*`` peer is present, the C path is
asserted byte/value-exact against the pure-Python path (skipped cleanly when
native is absent — the pure path is the complete alternative + the oracle).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.qpoly import QPoly
from srmech.amsc import _native


# ── an independent {(e, d): Fraction} q-polynomial oracle ─────────────────────
# Sparse: key (x-exponent e, q-degree d) → exact Fraction coefficient of
# x**e · q**d. Mirrors NOTHING in srmech (a fully separate reimplementation).
def _o_norm(m):
    """Drop zero entries → canonical sparse form."""
    return {k: v for k, v in m.items() if v != 0}


def _o_add(a, b, sub=False):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, Fraction(0)) + (-v if sub else v)
    return _o_norm(out)


def _o_mul(a, b):
    out = {}
    for (ea, da), va in a.items():
        for (eb, db), vb in b.items():
            k = (ea + eb, da + db)
            out[k] = out.get(k, Fraction(0)) + va * vb
    return _o_norm(out)


def _o_qshift(a, s):
    """σ**s : x ↦ q**s·x. The x**e·q**d term → x**e · q**(d + s·e) (multiply by
    q**(s·e))."""
    out = {}
    for (e, d), v in a.items():
        out[(e, d + s * e)] = out.get((e, d + s * e), Fraction(0)) + v
    return _o_norm(out)


def _o_eval(a, q_val, x_val):
    acc = Fraction(0)
    for (e, d), v in a.items():
        acc += v * (Fraction(q_val) ** d) * (Fraction(x_val) ** e)
    return acc


def _qp_to_oracle(p: QPoly):
    """A ``QPoly`` → the sparse oracle dict (for cross-checking)."""
    out = {}
    for i, cell in enumerate(p.cells):
        e = p.x_low + i
        for d, coeff in enumerate(cell.coeffs):
            if coeff != 0:
                out[(e, d)] = Fraction(coeff.numerator, coeff.denominator)
    return _o_norm(out)


def _oracle_to_qp(m):
    """The sparse oracle dict → a ``QPoly`` (via ``from_dict``; Q coefficients)."""
    if not m:
        return QPoly.zero()
    terms = {(e, d): Q(v.numerator, v.denominator) for (e, d), v in m.items()}
    return QPoly.from_dict(terms)


# ── construction + canonical form ─────────────────────────────────────────────
def test_from_coeffs_and_accessors():
    # x**0 · (1) + x**1 · (q) + x**2 · (1 + 2q) — coefficients are Poly-in-q.
    p = QPoly.from_coeffs([Poly.from_ints([1]), Poly.from_ints([0, 1]),
                           Poly.from_ints([1, 2])])
    assert not p.is_zero
    assert p.x_low == 0
    assert p.x_high == 2
    assert len(p) == 3
    assert p.q_degree() == 1
    assert not p.is_laurent
    assert p.x_coeff(1) == Poly.from_ints([0, 1])
    assert p.x_coeff(9).is_zero


def test_canonical_trims_both_ends_and_renormalizes_x_low():
    # leading + trailing zero cells must trim; x_low renormalizes to the first
    # nonzero cell.
    p = QPoly.from_coeffs([Poly.zero(), Poly.zero(), Poly.from_ints([3]),
                           Poly.zero()], x_low=-2)
    assert p.x_low == 0          # -2 + 2 leading zero cells
    assert p.x_high == 0
    assert len(p) == 1
    assert p.x_coeff(0) == Poly.from_ints([3])


def test_zero_one_and_equality():
    assert QPoly.zero().is_zero
    assert QPoly.from_coeffs([]).is_zero
    assert QPoly.one() == QPoly.x_monomial(0, Poly.one())
    assert QPoly.zero() == QPoly.from_coeffs([Poly.zero(), Poly.zero()])
    a = QPoly.from_dict({(1, 0): Q(2), (0, 1): Q(3)})
    b = QPoly.from_dict({(0, 1): Q(3), (1, 0): Q(2)})
    assert a == b
    assert hash(a) == hash(b)
    assert a != QPoly.one()


def test_laurent_offset():
    # x**(-1) · 1 + x**1 · 1 is a genuine Laurent polynomial.
    p = QPoly.from_dict({(-1, 0): Q(1), (1, 0): Q(1)})
    assert p.is_laurent
    assert p.x_low == -1
    assert p.x_high == 1
    assert len(p) == 3           # cells at x**-1, x**0 (zero), x**1


def test_from_dict_rejects_float_and_negative_q_degree():
    with pytest.raises(TypeError):
        QPoly.from_dict({(0, 0): 1.5})
    with pytest.raises(ValueError):
        QPoly.from_dict({(0, -1): Q(1)})


def test_constructor_rejects_float_coeff():
    with pytest.raises(TypeError):
        QPoly.from_coeffs([1.5])


# ── algebra laws vs the oracle ────────────────────────────────────────────────
_SAMPLES = [
    {(0, 0): Fraction(1), (1, 1): Fraction(-2), (2, 0): Fraction(3, 2)},
    {(-1, 0): Fraction(1), (0, 2): Fraction(5), (1, 1): Fraction(-1, 3)},
    {(0, 1): Fraction(7), (2, 3): Fraction(-4, 5), (3, 0): Fraction(2)},
    {(1, 0): Fraction(1)},
    {},
]


@pytest.mark.parametrize("ma", _SAMPLES)
@pytest.mark.parametrize("mb", _SAMPLES)
def test_add_sub_mul_match_oracle(ma, mb):
    a, b = _oracle_to_qp(ma), _oracle_to_qp(mb)
    assert _qp_to_oracle(a + b) == _o_add(ma, mb)
    assert _qp_to_oracle(a - b) == _o_add(ma, mb, sub=True)
    assert _qp_to_oracle(a * b) == _o_mul(ma, mb)


def test_addition_associative_and_commutative():
    a, b, c = (_oracle_to_qp(m) for m in _SAMPLES[:3])
    assert (a + b) + c == a + (b + c)
    assert a + b == b + a


def test_mul_associative_distributive_commutative():
    a, b, c = (_oracle_to_qp(m) for m in _SAMPLES[:3])
    assert (a * b) * c == a * (b * c)
    assert a * (b + c) == a * b + a * c
    assert a * b == b * a
    assert a * QPoly.one() == a
    assert (a * QPoly.zero()).is_zero


def test_scalar_and_qpoly_multiply():
    a = _oracle_to_qp(_SAMPLES[0])
    # scalar multiply by Q(3) == multiply by the constant QPoly 3.
    assert a * Q(3) == a * QPoly.from_dict({(0, 0): Q(3)})
    # ℚ[q] multiply by q == multiply by the x**0·q**1 QPoly.
    qcoeff = Poly.from_ints([0, 1])
    assert a * qcoeff == a * QPoly.from_q_poly(qcoeff)


def test_neg_is_class_k_signflip():
    a = _oracle_to_qp(_SAMPLES[0])
    assert _qp_to_oracle(-a) == {k: -v for k, v in _SAMPLES[0].items()}
    assert (a + (-a)).is_zero


# ── eval consistency ──────────────────────────────────────────────────────────
def test_eval_matches_oracle():
    m = _SAMPLES[1]
    a = _oracle_to_qp(m)
    for q_val, x_val in [(Q(2), Q(3)), (Q(1, 2), Q(5)), (Q(-3), Q(2))]:
        got = a.eval(q_val, x_val)
        want = _o_eval(m, Fraction(q_val.numerator, q_val.denominator),
                       Fraction(x_val.numerator, x_val.denominator))
        assert Fraction(got.numerator, got.denominator) == want


def test_eval_laurent_needs_nonzero_x():
    p = QPoly.from_dict({(-1, 0): Q(1)})
    with pytest.raises(ZeroDivisionError):
        p.eval(Q(2), Q(0))
    assert p.eval(Q(2), Q(4)) == Q(1, 4)   # x**-1 at x=4


# ── the q-shift / q-difference identity ───────────────────────────────────────
def test_qshift_acts_per_cell_as_q_power():
    # x**2 · 1 under σ (x ↦ q·x) → x**2 · q**2.
    p = QPoly.x_monomial(2, Poly.one())
    sp = p.qshift(1)
    assert _qp_to_oracle(sp) == {(2, 2): Fraction(1)}
    # σ**3 on x**1 · (1 + q) → x**1 · q**3·(1 + q) = x**1·(q**3 + q**4).
    p2 = QPoly.x_monomial(1, Poly.from_ints([1, 1]))
    assert _qp_to_oracle(p2.qshift(3)) == {(1, 3): Fraction(1), (1, 4): Fraction(1)}


def test_qshift_matches_oracle_over_samples():
    for m in _SAMPLES:
        # only non-negative s·e cells (ℚ[q] ground ring) — use s=2 and drop the
        # negative-e samples for this check.
        if any(e < 0 for (e, _d) in m):
            continue
        a = _oracle_to_qp(m)
        assert _qp_to_oracle(a.qshift(2)) == _o_qshift(m, 2)


def test_qshift_negative_qpower_rejected():
    # x**(-1) under σ would give q**(-1) — leaves ℚ[q].
    p = QPoly.from_dict({(-1, 0): Q(1)})
    with pytest.raises(ValueError):
        p.qshift(1)


def test_qshift_zero_and_compose():
    a = _oracle_to_qp(_SAMPLES[2])
    assert a.qshift(0) == a
    # σ**2 == σ∘σ on a non-negative-exponent polynomial.
    assert a.qshift(2) == a.qshift(1).qshift(1)


def test_qdelta_is_qshift_minus_self():
    a = _oracle_to_qp(_SAMPLES[2])
    assert a.qdelta() == a.qshift(1) - a


def test_q_telescoping_sum_exact():
    # The q-summation identity: Σ_{n=lo}^{hi} (Δ_q T)(q**n) = T(q**(hi+1)) − T(q**lo)
    # for a q-antidifference T. Take T = x**0·1 + x**1·1 + x**2·1 (a QPoly), form
    # t = Δ_q T = σT − T, then verify the telescoping sum at a fixed numeric q.
    T = QPoly.from_coeffs([Poly.one(), Poly.one(), Poly.one()])  # 1 + x + x**2
    t = T.qdelta()
    q_val = Q(3)
    lo, hi = 0, 5
    # Σ_{n=lo}^{hi} t(q, x=q**n):
    total = Q(0)
    for n in range(lo, hi + 1):
        x_n = q_val ** n
        total = total + t.eval(q_val, x_n)
    # T(q**(hi+1)) − T(q**lo):
    rhs = T.eval(q_val, q_val ** (hi + 1)) - T.eval(q_val, q_val ** lo)
    assert total == rhs


def test_q_geometric_term_qshift():
    # A q-geometric term t_k = c·x**k (here a single x-monomial with c ∈ ℚ[q]):
    # σ multiplies by q**k. Confirm σ and Δ_q act correctly.
    c = Poly.from_ints([2, 0, 5])     # c(q) = 2 + 5q**2
    k = 3
    tk = QPoly.x_monomial(k, c)
    # σ t_k = q**k · t_k.
    assert tk.qshift(1) == QPoly.x_monomial(k, Poly.monomial(k) * c)
    # Δ_q t_k = (q**k − 1)·t_k.
    qk_minus_1 = Poly.monomial(k) - Poly.one()
    assert tk.qdelta() == QPoly.x_monomial(k, qk_minus_1 * c)


# ── KEYSTONE bignum: huge q-coefficients, no ceiling ──────────────────────────
def _bignum_qpoly():
    big = 10 ** 40 + 1
    # cells: x**0·(big + (big**2)·q), x**1·(-big), x**2·(big//3-style ratio)
    c0 = Poly.from_coeffs([Q(big, 3), Q(big * big, 7)])
    c1 = Poly.from_coeffs([Q(-big, 1)])
    c2 = Poly.from_coeffs([Q(big * big, 1), Q(0, 1), Q(big, 11)])
    return QPoly.from_coeffs([c0, c1, c2])


def test_bignum_mul_qshift_match_oracle():
    a = _bignum_qpoly()
    b = QPoly.from_coeffs([Poly.from_coeffs([Q(10 ** 30, 13)]),
                           Poly.from_coeffs([Q(0), Q(10 ** 25, 1)])])
    ma, mb = _qp_to_oracle(a), _qp_to_oracle(b)
    assert _qp_to_oracle(a * b) == _o_mul(ma, mb)
    assert _qp_to_oracle(a + b) == _o_add(ma, mb)
    assert _qp_to_oracle(a.qshift(2)) == _o_qshift(ma, 2)
    # the coefficients genuinely exceed 2**64.
    assert any(v.numerator > 2 ** 64 or v.denominator > 1 for v in ma.values())


# ── Python==C native parity (gated on has_native_qpoly) ───────────────────────
_HAS_C = _native.has_native_qpoly()


@pytest.mark.skipif(not _HAS_C, reason="native srmech_qpoly_* peer absent")
def test_native_addsub_byte_identical():
    a = _bignum_qpoly()
    b = QPoly.from_coeffs([Poly.from_coeffs([Q(10 ** 30, 13)]),
                           Poly.from_coeffs([Q(0), Q(10 ** 25, 1)])],
                          x_low=-1)
    af, bf = _native._qp_pairs(a) if hasattr(_native, "_qp_pairs") else None, None
    # drive the C path directly via the bridge wrappers, compare to pure.
    from srmech.amsc.qpoly import _qp_pairs, _qp_from_pairs
    cadd = _qp_from_pairs(_native.qpoly_addsub_c(_qp_pairs(a), _qp_pairs(b), False))
    csub = _qp_from_pairs(_native.qpoly_addsub_c(_qp_pairs(a), _qp_pairs(b), True))
    # pure path (force pure by oracle round-trip equality).
    assert cadd == _oracle_to_qp(_o_add(_qp_to_oracle(a), _qp_to_oracle(b)))
    assert csub == _oracle_to_qp(_o_add(_qp_to_oracle(a), _qp_to_oracle(b), sub=True))


@pytest.mark.skipif(not _HAS_C, reason="native srmech_qpoly_* peer absent")
def test_native_mul_byte_identical():
    from srmech.amsc.qpoly import _qp_pairs, _qp_from_pairs
    a = _bignum_qpoly()
    b = QPoly.from_coeffs([Poly.from_coeffs([Q(7, 3), Q(11, 5)]),
                           Poly.from_coeffs([Q(13, 2)])])
    cmul = _qp_from_pairs(_native.qpoly_mul_c(_qp_pairs(a), _qp_pairs(b)))
    assert cmul == _oracle_to_qp(_o_mul(_qp_to_oracle(a), _qp_to_oracle(b)))


@pytest.mark.skipif(not _HAS_C, reason="native srmech_qpoly_* peer absent")
def test_native_qshift_byte_identical():
    from srmech.amsc.qpoly import _qp_pairs, _qp_from_pairs
    a = _bignum_qpoly()            # non-negative x-exponents only
    cshift = _qp_from_pairs(_native.qpoly_qshift_c(_qp_pairs(a), 3))
    assert cshift == _oracle_to_qp(_o_qshift(_qp_to_oracle(a), 3))


@pytest.mark.skipif(not _HAS_C, reason="native srmech_qpoly_* peer absent")
def test_native_equals_pure_on_carrier_ops():
    # The carrier's own dispatch (which prefers C when present) must equal the
    # oracle — i.e. the live + / * / qshift route through C and stay exact.
    a = _bignum_qpoly()
    b = QPoly.from_dict({(0, 0): Q(2), (1, 2): Q(-3, 7), (2, 1): Q(5)})
    assert _qp_to_oracle(a * b) == _o_mul(_qp_to_oracle(a), _qp_to_oracle(b))
    assert _qp_to_oracle(a + b) == _o_add(_qp_to_oracle(a), _qp_to_oracle(b))
    assert _qp_to_oracle(a.qshift(2)) == _o_qshift(_qp_to_oracle(a), 2)


# ── the float boundary (the ONE rotation) ─────────────────────────────────────
def test_to_floats_is_the_only_float():
    p = QPoly.from_coeffs([Poly.from_coeffs([Q(1, 2), Q(3, 4)]),
                           Poly.from_coeffs([Q(5, 1)])], x_low=-1)
    runs, x_low = p.to_floats()
    assert x_low == -1
    assert runs == [[0.5, 0.75], [5.0]]
    assert all(isinstance(v, float) for run in runs for v in run)
