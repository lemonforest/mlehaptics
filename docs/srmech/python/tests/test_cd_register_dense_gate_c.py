"""The DENSE reversibility gate, C vs the exact-rational oracle (rc464, `#T1188`).

``srmech_sedenion_is_navigable`` decides invertibility of the signed XOR-circulant
``L(x)[r][c] = sign(r^c, c) * x_{r^c}`` by BIGNUM-FREE modular rank over word-size
primes. This module is the only place that bool is checked against the
Fraction-nullspace reference — ``left_mult_kernel``, which computes the kernel
exactly and is a completely different algorithm — so it is the whole attestation
for that kernel and the header names it as such.

WHY THIS FILE EXISTS UNDER THIS NAME. It was ``test_cascade_sedenion_parity.py``
and it gated three C symbols. rc464 removed two of them
(``srmech_sedenion_navmap`` / ``srmech_sedenion_navigate``) with the 16-slot
``SedenionRegister``, because ``srmech_cd_navmap`` / ``srmech_cd_navigate`` take
the rung as a parameter and reproduce them bit-for-bit at dim 16 — that half's
coverage moved to ``test_cd_register_rc297.py``, which runs it at SEVEN rungs
rather than one. The third symbol STAYS, and it was never sedenion-specific:
``SRMECH_CD_DENSE_MAX_DIM`` is 64, so the kernel serves dims 1..64 and only its
NAME says 16. The file is renamed to what it actually tests.

The kernel's cap is a real bound, not an oversight — the ``dim x dim`` modular-rank
matrix is the library's only quadratic buffer. Past it, ``left_mult_is_invertible``
routes to the exact-rational nullspace, which is C the whole way down through
``srmech_qmat_nullspace``; that route is gated in ``test_cd_rungs_rc298.py``.

numpy-free.
"""
import ctypes
from fractions import Fraction

import pytest

from srmech import _native
from srmech._native import HAS_NATIVE
from srmech.cascade import cayley_dickson as cd

#: The rungs swept EXHAUSTIVELY (every basis unit and every ``e_i ± e_j`` sum).
#: 16 is the important one: it is where the zero-divisor witness lives, the only
#: input class whose False is structural rather than degenerate.
DENSE_RUNGS = (2, 4, 8, 16)

#: The rungs swept by a BOUNDED SAMPLE, and why. The oracle is the exact
#: Fraction nullspace, which is O(dim^3) per case, while the case count is
#: O(dim^2) — so an exhaustive sweep is O(dim^5) and measured at MINUTES per
#: rung by rc464 (the first attempt at exhaustive-to-64 was killed after ~5 min
#: without finishing 64). Sampling is stated here rather than hidden in a
#: parametrize, because a sampled gate that reads as exhaustive is the worse
#: failure: it would report full coverage of a boundary it never reached.
SAMPLED_RUNGS = (32, 64)

#: Sample size per rung, in ``e_i ± e_j`` pairs. Deterministic (a fixed stride),
#: never random — a gate whose case set moves between runs cannot be bisected.
SAMPLE_PAIRS = 24

_GATE_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_sedenion_is_navigable")
)

SKIP_IF_NO_GATE = pytest.mark.skipif(
    not _GATE_NATIVE,
    reason="the loaded libsrmech does not expose the dense reversibility gate",
)


def _c_is_navigable(int_vec):
    n = len(int_vec)
    arr = (ctypes.c_int64 * n)(*int_vec)
    out = ctypes.c_int()
    rc = _native.LIB.srmech_sedenion_is_navigable(arr, n, ctypes.byref(out))
    assert rc == _native.SRMECH_OK, f"rc={rc} for {int_vec}"
    return out.value == 1


def _clear_denominators(x):
    """Scale an exact-rational vector to integers — Class-N, no float."""
    from srmech.math.cyclic import gcd
    den = 1
    for v in x:
        den = den * v.denominator // gcd(den, v.denominator)
    return [int(v * den) for v in x]


# ── structural facts, true with or without the native kernel ────────────────

@pytest.mark.parametrize("dim", DENSE_RUNGS + SAMPLED_RUNGS)
def test_basis_units_navigable_zero_vector_not(dim):
    for j in range(dim):
        e = [Fraction(0)] * dim
        e[j] = Fraction(1)
        assert cd.left_mult_is_invertible(e) is True
    assert cd.left_mult_is_invertible([Fraction(0)] * dim) is False


# ── the C bool vs the exact Fraction-nullspace oracle ───────────────────────

def _pair_cases(dim, pairs=None):
    """``e_i ± e_j`` sums — all of them, or a deterministic stride sample."""
    all_pairs = [(i, j) for i in range(dim) for j in range(i + 1, dim)]
    if pairs is not None and len(all_pairs) > pairs:
        stride = len(all_pairs) // pairs
        all_pairs = [all_pairs[k * stride] for k in range(pairs)]
    out = []
    for i, j in all_pairs:
        for sgn in (1, -1):
            v = [Fraction(0)] * dim
            v[i] = Fraction(1)
            v[j] = Fraction(sgn)
            out.append(tuple(v))
    return out


@SKIP_IF_NO_GATE
@pytest.mark.parametrize("dim", DENSE_RUNGS)
def test_dense_gate_agrees_with_the_fraction_oracle(dim):
    """EXHAUSTIVE: every basis unit and every e_i ± e_j sum, at the low rungs.

    The oracle is ``left_mult_kernel`` — the exact-rational nullspace — NOT the
    dispatching wrapper, which would consult the very kernel under test."""
    cases = [cd.cd_basis(dim, j) for j in range(dim)] + _pair_cases(dim)
    for x in cases:
        oracle = len(cd.left_mult_kernel(x)) == 0
        assert _c_is_navigable(_clear_denominators(x)) == oracle, (
            f"dim {dim}: C and the Fraction oracle disagree on {x}")


@SKIP_IF_NO_GATE
@pytest.mark.parametrize("dim", SAMPLED_RUNGS)
def test_dense_gate_agrees_with_the_fraction_oracle_sampled(dim):
    """SAMPLED at the top two rungs — see ``SAMPLED_RUNGS`` for the cost.

    Every basis unit IS covered exhaustively (that is O(dim) cases, and it is
    the class the addressing premise rides on); only the composite ``e_i ± e_j``
    sums are sampled."""
    cases = ([cd.cd_basis(dim, j) for j in range(dim)]
             + _pair_cases(dim, pairs=SAMPLE_PAIRS))
    for x in cases:
        oracle = len(cd.left_mult_kernel(x)) == 0
        assert _c_is_navigable(_clear_denominators(x)) == oracle, (
            f"dim {dim}: C and the Fraction oracle disagree on {x}")


@SKIP_IF_NO_GATE
def test_the_zero_divisor_pair_is_refused_at_dim_16():
    """The one input whose False is structural: past the Hurwitz wall a
    composite direction can have no inverse at all. Both halves of the witness
    are nonzero and both are refused — that is what makes it a zero DIVISOR
    rather than a degenerate vector."""
    w = cd.cd_zero_divisor_witness(16)
    for half in ("x", "y"):
        vec = w[half]
        assert any(v != 0 for v in vec)
        assert cd.left_mult_kernel(vec), f"{half} should have a nonempty kernel"
        assert _c_is_navigable(_clear_denominators(vec)) is False


@SKIP_IF_NO_GATE
def test_the_gate_declines_past_its_dense_cap():
    """Above ``SRMECH_CD_DENSE_MAX_DIM`` the kernel REFUSES rather than
    answering — the quadratic buffer is a documented bound, and a refusal is
    how it stays one. The Python dispatcher then routes to the exact-rational
    nullspace, so the CAPABILITY is not bounded, only this kernel is."""
    vec = [0] * 128
    vec[1] = 1
    arr = (ctypes.c_int64 * 128)(*vec)
    out = ctypes.c_int()
    rc = _native.LIB.srmech_sedenion_is_navigable(arr, 128, ctypes.byref(out))
    assert rc != _native.SRMECH_OK, (
        "the dense kernel accepted dim 128; its buffer is sized for 64 and a "
        "silent answer there would be reading past it")
    # ...and the capability survives the refusal, through the other route.
    e1 = [Fraction(0)] * 128
    e1[1] = Fraction(1)
    assert cd.left_mult_is_invertible(e1) is True
