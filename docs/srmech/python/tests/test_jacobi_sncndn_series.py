"""Jacobi elliptic sn/cn/dn Maclaurin truncation — exact-Q + C-parity tests.

``srmech.amsc.rational.jacobi_sncndn_series_truncate(p, q, m_p, m_q, N)`` is the
"rotation-last" exact-rational sibling of ``sin_series_truncate`` /
``cos_series_truncate``: it builds the Maclaurin coefficient sequences of the
three Jacobi elliptic functions sn/cn/dn from the coupled power-series ODE
(A&S §16.4) and evaluates each at ``u = p/q`` with modulus parameter
``m = m_p/m_q``, ENTIRELY in the exact ``(num, den)`` fiber (no float, no
mid-body projection).

This test pins:
  (a) the exact-Q Pythagorean identities ``sn²+cn²=1`` and ``dn²+m·sn²=1``
      hold as truncated series (all higher coefficients cancel exactly);
  (b) the ``m=0`` degeneracy: sn coeffs == sin Maclaurin (1, −1/6, 1/120, …),
      cn coeffs == cos Maclaurin (1, −1/2, 1/24, …), dn ≡ 1;
  (c) the ``m=1`` degeneracy: sn == tanh series, cn == dn == sech series;
  (d) native == pure BYTE-IDENTICAL (gated on ``has_native_jacobi_sncndn``);
  (e) the float projection matches the AGM oracle at (u=0.7, m=0.5).

numpy-FREE + math-FREE (no ``import numpy``, no ``import math``): exact-rational
arithmetic via ``fractions.Fraction`` only; the float projection is the lone
terminal ``num/den`` division.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc import rational


_JS = rational.jacobi_sncndn_series_truncate


# ──────────────────────────────────────────────────────────────────────
# Helpers — rebuild the coefficient sequences via the public exact-Q ops,
# and form exact convolution products, using only fractions.Fraction.
# ──────────────────────────────────────────────────────────────────────

def _coeff_sequences(m_p: int, m_q: int, n: int):
    """The sn/cn/dn Maclaurin coefficient sequences (length n+1) as
    ``fractions.Fraction`` via the same recurrence the op uses.

    Mirrors the documented recurrence so the identity tests operate on the
    coefficient arrays directly (where the cancellation is exact)."""
    ra = rational.rational_add
    rm = rational.rational_mul
    rr = rational._reduce_rational
    m = rr(m_p, m_q)
    a = [(0, 1)]
    b = [(1, 1)]
    c = [(1, 1)]
    for k in range(n):
        bc = (0, 1)
        ac = (0, 1)
        ab = (0, 1)
        for i in range(k + 1):
            j = k - i
            bc = ra(bc, rm(b[i], c[j]))
            ac = ra(ac, rm(a[i], c[j]))
            ab = ra(ab, rm(a[i], b[j]))
        inv = (1, k + 1)
        a.append(rm(bc, inv))
        b.append(rm((-ac[0], ac[1]), inv))
        c.append(rm(rm((-ab[0], ab[1]), m), inv))
    to_f = lambda t: Fraction(t[0], t[1])
    return [to_f(x) for x in a], [to_f(x) for x in b], [to_f(x) for x in c]


def _series_square(seq, n):
    """Coefficients of ``(Σ seq[k]·u^k)²`` up to degree n (exact Fraction)."""
    out = [Fraction(0)] * (n + 1)
    for i in range(len(seq)):
        for j in range(len(seq)):
            if i + j <= n:
                out[i + j] += seq[i] * seq[j]
    return out


# ──────────────────────────────────────────────────────────────────────
# (a) exact-Q Pythagorean identities (coefficient-level cancellation)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("m_p,m_q", [(0, 1), (1, 1), (1, 2), (3, 7), (9, 10)])
def test_exact_pythagorean_identities(m_p, m_q):
    n = 14
    a, b, c = _coeff_sequences(m_p, m_q, n)
    m = Fraction(m_p, m_q)
    sn2 = _series_square(a, n)
    cn2 = _series_square(b, n)
    dn2 = _series_square(c, n)
    # sn² + cn² == 1 exactly: constant 1, every higher coefficient 0.
    id1 = [sn2[k] + cn2[k] for k in range(n + 1)]
    assert id1[0] == 1
    assert all(coeff == 0 for coeff in id1[1:]), id1
    # dn² + m·sn² == 1 exactly.
    id2 = [dn2[k] + m * sn2[k] for k in range(n + 1)]
    assert id2[0] == 1
    assert all(coeff == 0 for coeff in id2[1:]), id2


# ──────────────────────────────────────────────────────────────────────
# (b) m = 0 → sn = sin, cn = cos, dn = 1
# ──────────────────────────────────────────────────────────────────────

def test_m0_recovers_sin_cos_coefficients():
    a, b, c = _coeff_sequences(0, 1, 9)
    # sn Maclaurin == sin: 0, 1, 0, −1/6, 0, 1/120, …
    assert a[0] == 0 and a[1] == 1 and a[2] == 0
    assert a[3] == Fraction(-1, 6)
    assert a[5] == Fraction(1, 120)
    assert a[7] == Fraction(-1, 5040)
    # cn Maclaurin == cos: 1, 0, −1/2, 0, 1/24, …
    assert b[0] == 1 and b[1] == 0
    assert b[2] == Fraction(-1, 2)
    assert b[4] == Fraction(1, 24)
    assert b[6] == Fraction(-1, 720)
    # dn ≡ 1 when m = 0.
    assert c[0] == 1
    assert all(coeff == 0 for coeff in c[1:]), c


# ──────────────────────────────────────────────────────────────────────
# (c) m = 1 → sn = tanh, cn = dn = sech
# ──────────────────────────────────────────────────────────────────────

def test_m1_recovers_tanh_sech_coefficients():
    a, b, c = _coeff_sequences(1, 1, 9)
    # sn == tanh: 0, 1, 0, −1/3, 0, 2/15, …
    assert a[1] == 1
    assert a[3] == Fraction(-1, 3)
    assert a[5] == Fraction(2, 15)
    assert a[7] == Fraction(-17, 315)
    # cn == sech: 1, 0, −1/2, 0, 5/24, …
    assert b[0] == 1
    assert b[2] == Fraction(-1, 2)
    assert b[4] == Fraction(5, 24)
    assert b[6] == Fraction(-61, 720)
    # dn == cn == sech when m = 1.
    assert c == b, (c, b)


# ──────────────────────────────────────────────────────────────────────
# (d) native == pure byte-identical (gated on has_native)
# ──────────────────────────────────────────────────────────────────────

_PARITY_CASES = [
    (0, 1, 0, 1, 5),       # u=0, m=0
    (7, 10, 1, 2, 30),     # the AGM keystone
    (1, 1, 1, 1, 20),      # u=1, m=1
    (-7, 10, 1, 2, 30),    # negative u
    (3, 5, 3, 7, 25),      # generic rational m
    (11, 13, 1, 1, 22),    # coprime large-ish u, m=1
    (1, 3, 9, 10, 40),     # near-1 modulus, deep N
    (0, 1, 0, 1, 50),      # N at the cap
]


def _pure(p, q, mp, mq, n):
    """Force the pure-Python body by suppressing native dispatch."""
    saved = getattr(_native, "jacobi_sncndn_c", None)
    _native.jacobi_sncndn_c = None
    try:
        return _JS(p, q, mp, mq, n)
    finally:
        _native.jacobi_sncndn_c = saved


@pytest.mark.skipif(
    not _native.has_native_jacobi_sncndn(),
    reason=(
        "native srmech_jacobi_sncndn not loaded; the pure-Python bignum path "
        "in srmech.amsc.rational is the only path (and the parity oracle). "
        "Skipped — never xfailed."
    ),
)
@pytest.mark.parametrize("p,q,mp,mq,n", _PARITY_CASES)
def test_native_equals_pure_byte_identical(p, q, mp, mq, n):
    native = _native.jacobi_sncndn_c(p, q, mp, mq, n)
    assert native is not None
    pure = _pure(p, q, mp, mq, n)
    assert native == pure, (native, pure)


# ──────────────────────────────────────────────────────────────────────
# (e) float projection matches the AGM oracle at (u=0.7, m=0.5)
# ──────────────────────────────────────────────────────────────────────

def test_float_matches_agm_oracle():
    sn, cn, dn = _JS(7, 10, 1, 2, 30)
    # The single terminal observer-frame rotation: one num/den division each.
    sn_f = sn[0] / sn[1]
    cn_f = cn[0] / cn[1]
    dn_f = dn[0] / dn[1]
    # Reference values from the AGM evaluation of sn/cn/dn(0.7, m=0.5).
    assert abs(sn_f - 0.6243400909) < 1e-9, sn_f
    assert abs(cn_f - 0.7811526425) < 1e-9, cn_f
    assert abs(dn_f - 0.8972734953) < 1e-9, dn_f


# ──────────────────────────────────────────────────────────────────────
# Domain guards (Class-N / Class-K contract errors)
# ──────────────────────────────────────────────────────────────────────

def test_domain_guards():
    with pytest.raises(ValueError):
        _JS(1, 0, 1, 2, 5)            # denominator must be > 0
    with pytest.raises(ValueError):
        _JS(1, 2, 1, 0, 5)            # m_denominator must be > 0
    with pytest.raises(ValueError):
        _JS(1, 2, 1, 2, 51)           # num_terms > 50 cap
    with pytest.raises(TypeError):
        _JS(1, 2, "x", 2, 5)          # m_numerator must be int
