"""0.9.0rc15 — the EXACT-complex `Qi` carrier's native C-host peer is bit-exact.

The C/Python parity ratchet for `srmech_qi_*` (the NORTH STAR C-host parity for
the `Qi` carrier). On a platform wheel (native present) it asserts the native
`qi_*_c` wrappers reassemble the SAME exact rational limbs as a stdlib
`Fraction` oracle, and that the routed `Qi` dunders (which dispatch through the
native peer when the limbs fit int64) match too. The int64-limb domain ceiling
is honoured: limbs past int64 make the wrapper return `None` and the dunder
falls through to the exact-`Fraction` path (the unbounded reference) — still
exact. Numpy-free by construction; asserted numpy-absent so it PASSES (not
skips) on the numpy-absent matrix.
"""

import importlib.util
from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc.q import Q
from srmech.amsc.qi import Qi

_HAS_NATIVE_QI = _native.has_native_qi()
_native_only = pytest.mark.skipif(
    not _HAS_NATIVE_QI, reason="srmech_qi_* native peer not loaded (pure wheel)")

# (re_num, re_den, im_num, im_den) over signs / zero / integers / fractions.
_GRID = [(3, 4, 1, 2), (-3, 4, 1, 2), (3, 4, -1, 2), (-3, 4, -1, 2),
         (0, 1, 1, 1), (1, 1, 0, 1), (5, 2, 7, 3), (-100, 7, 9, 4),
         (2, 1, -3, 1), (0, 1, 0, 1)]


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this Qi C-parity ratchet must run on the numpy-ABSENT matrix")


def _qi(t):
    return Qi(Q(t[0], t[1]), Q(t[2], t[3]))


def _fp(t):
    return (Fraction(t[0], t[1]), Fraction(t[2], t[3]))


def _red(fr, fi):
    return (fr.numerator, fr.denominator, fi.numerator, fi.denominator)


# ── the routed Qi dunders match the oracle (native OR pure — the contract) ──

@pytest.mark.parametrize("ta", _GRID)
@pytest.mark.parametrize("tb", _GRID)
def test_qi_dunders_match_oracle(ta, tb):
    a, b = _qi(ta), _qi(tb)
    fa, fb = _fp(ta), _fp(tb)
    for got, (er, ei) in (
        (a + b, (fa[0] + fb[0], fa[1] + fb[1])),
        (a - b, (fa[0] - fb[0], fa[1] - fb[1])),
        (a * b, (fa[0] * fb[0] - fa[1] * fb[1], fa[0] * fb[1] + fa[1] * fb[0])),
    ):
        rn, rd = got.real.as_pair()
        inum, iden = got.imag.as_pair()
        assert (rn, rd, inum, iden) == _red(er, ei)


@pytest.mark.parametrize("t", _GRID)
def test_qi_norm_sq_dunder_matches_oracle(t):
    fa = _fp(t)
    ns = fa[0] * fa[0] + fa[1] * fa[1]
    assert _qi(t).norm_sq().as_pair() == (ns.numerator, ns.denominator)


# ── native wrappers themselves are bit-exact (platform wheel only) ──

@_native_only
@pytest.mark.parametrize("ta", _GRID)
@pytest.mark.parametrize("tb", _GRID)
def test_native_qi_binops_match_oracle(ta, tb):
    fa, fb = _fp(ta), _fp(tb)
    assert _native.qi_add_c(ta, tb) == _red(fa[0] + fb[0], fa[1] + fb[1])
    assert _native.qi_sub_c(ta, tb) == _red(fa[0] - fb[0], fa[1] - fb[1])
    assert _native.qi_mul_c(ta, tb) == _red(
        fa[0] * fb[0] - fa[1] * fb[1], fa[0] * fb[1] + fa[1] * fb[0])


@_native_only
@pytest.mark.parametrize("t", _GRID)
def test_native_qi_unary_match_oracle(t):
    fa = _fp(t)
    assert _native.qi_conjugate_c(t) == _red(fa[0], -fa[1])
    ns = fa[0] * fa[0] + fa[1] * fa[1]
    assert _native.qi_norm_sq_c(t) == (ns.numerator, ns.denominator)
    expect_q = (1 if fa[0] < 0 else 0) | ((1 if fa[1] < 0 else 0) << 1)
    assert _native.qi_quadrant_c(t) == expect_q


@_native_only
def test_int64_limb_domain_ceiling_falls_through_to_exact():
    """A product past the int64 limb domain makes the native wrapper return
    None (no bignum); the routed dunder still gives the EXACT Fraction result
    via the pure path (the unbounded oracle)."""
    huge = (4_000_000_000, 1, 0, 1)            # (4e9)² overflows int64
    assert _native.qi_mul_c(huge, huge) is None
    a = Qi(Q(4_000_000_000), Q(0))
    prod = a * a
    assert prod.real.as_pair() == (16_000_000_000_000_000_000, 1)
    assert prod.imag.as_pair() == (0, 1)
