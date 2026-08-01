"""rc263 (#845): the stdlib-``fractions`` → srmech ``Q`` carrier purge.

Three guarantees the purge must keep:

1. ``to_q(v)`` is a byte-exact drop-in for one-arg ``Fraction(v)`` over every
   scalar srmech's own math used to build a ``Fraction`` from.
2. ``Q`` and a stdlib ``Fraction`` interoperate in BOTH directions (a caller's
   stray ``Fraction`` must still combine/compare with a srmech ``Q``) — the
   ``_as_pair`` ``numbers.Rational`` bridge.
3. The migrated ops now EMIT ``Q`` (never a stdlib ``Fraction``), while still
   ACCEPTING a ``Fraction`` on input via the numeric protocol.
"""
from __future__ import annotations

from fractions import Fraction as F

from srmech.amsc.q import Q, to_q


# ── 1. to_q parity with one-arg Fraction ─────────────────────────────────────
def test_to_q_matches_one_arg_fraction():
    for v in [0, 5, -7, True, (3, 4), [6, 8], Q(2, 5), F(7, 3), F(-4, 6)]:
        q = to_q(v)
        exp = F(*v) if isinstance(v, (tuple, list)) else F(v)
        assert isinstance(q, Q)
        assert (q.numerator, q.denominator) == (exp.numerator, exp.denominator), v


def test_to_q_float_is_exact_like_fraction_float():
    for x in [0.25, 0.5, -0.125, 3.0]:
        assert to_q(x).as_pair() == F(x).as_integer_ratio()


def test_to_q_passthrough_and_reject():
    q = Q(1, 3)
    assert to_q(q) is q                             # a Q rides through unchanged
    import pytest
    with pytest.raises(TypeError):
        to_q(object())


# ── 2. Q ↔ Fraction interoperate BOTH directions ─────────────────────────────
def test_q_fraction_arithmetic_both_directions():
    assert Q(1, 2) * F(1, 3) == Q(1, 6)
    assert F(1, 3) * Q(1, 2) == Q(1, 6)             # Fraction.__mul__ NotImplemented → Q.__rmul__
    assert Q(1, 3) + F(1, 6) == Q(1, 2)
    assert F(1, 6) + Q(1, 3) == Q(1, 2)
    assert Q(1, 3) - F(1, 4) == Q(1, 12)
    assert F(3, 4) / Q(1, 2) == Q(3, 2)
    # a mixed sum (int 0 seed → Fraction → Q) reduces exactly
    assert sum([F(1, 2), Q(1, 4), F(1, 8)]) == Q(7, 8)


def test_q_fraction_comparison_and_equality():
    assert Q(1, 3) < F(1, 2)
    assert Q(2, 4) == F(1, 2)
    assert F(1, 2) == Q(1, 2)
    assert not (Q(3, 4) < F(1, 2))
    # Fraction of a Q reads its numerator/denominator (Q is a numbers.Rational)
    assert F(Q(3, 8)) == F(3, 8)


# ── 3. migrated ops EMIT Q, still ACCEPT Fraction input ──────────────────────
def test_cayley_dickson_emits_q_accepts_fraction():
    from srmech.amsc.cascade import cayley_dickson as C
    prod = C.cd_mult([1, 2, 3, 4], [4, 3, 2, 1])           # quaternion product
    assert all(isinstance(v, Q) for v in prod)
    n = C.cd_norm_sq([F(1, 2), F(1, 3), 0, 0])             # Fraction INPUT
    assert isinstance(n, Q) and n == Q(13, 36)


def test_dense_solve_and_schur_emit_q():
    from srmech.math.laplacian import dense_solve, schur_complement, dense_laplacian
    X = dense_solve([[2, 0], [0, 4]], [[2], [8]], exact=True)
    assert all(isinstance(v, Q) for row in X for v in row)
    assert X == [[Q(1)], [Q(2)]]
    S = schur_complement(dense_laplacian(4, [(0, 1), (1, 2), (2, 3)]), [0, 3], exact=True)
    assert all(isinstance(v, Q) for row in S for v in row)


def test_cycle_holonomy_emits_q_accepts_fraction_charges():
    from srmech.math.laplacian import cycle_holonomy
    res = cycle_holonomy([(0, 1), (1, 2), (2, 0)], charges=[F(1, 3), 0, 0], n=3)
    assert all(isinstance(h, Q) for h in res["holonomies"])
    assert res["holonomies"] == [Q(1, 3)]


def test_negative_float_snaps_via_signed_cascade():
    # regression: the float→ℚ snap sites (cycle_holonomy charge, so8 rank, the
    # eigenvalue recover) must handle a NEGATIVE input — the bare Class-N
    # best_rational rejects a negative numerator (octonion structure constants
    # are {-1,0,+1}; charges/eigenvalues can be negative), so they route the
    # SIGNED Class-K∘N∘C best_rational_signed.
    from srmech.math.laplacian import _to_fraction, cycle_holonomy
    assert _to_fraction(-0.25) == Q(-1, 4)
    res = cycle_holonomy([(0, 1), (1, 2), (2, 0)], charges=[-0.25, 0.0, 0.0], n=3)
    assert all(isinstance(h, Q) for h in res["holonomies"])
    from srmech.qm.so8 import _rank_exact, g2_subalgebra
    assert _rank_exact([[-4, 2], [1, -1], [0, 3]]) == 2   # negative coords
    assert len(g2_subalgebra()) == 14                     # the CI capstone path


def test_op_provenance_rational_roundtrip_is_q():
    # a stdlib Fraction canonicalises via the duck-typed numerator/denominator
    # branch, and decanon rebuilds the exact rational as a srmech Q (#845).
    from srmech.introspect.op_provenance import _canon, _decanon
    canon, exact = _canon(F(1, 2))                         # Fraction INPUT
    assert exact and canon == {"__rational__": [1, 2]}
    back = _decanon(canon)
    assert isinstance(back, Q) and back == Q(1, 2)
