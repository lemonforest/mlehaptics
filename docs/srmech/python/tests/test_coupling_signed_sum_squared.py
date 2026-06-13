"""Class K ∘ L signed-sum coupling score — ``srmech.amsc.coupling``.

``signed_sum_squared(sources)`` = per-element ``(Σ_sources (2·bit − 1))²``
(v0.4.3rc3, UPSTREAM_NOTES §1.2). A composition of Class K (bipolar sign-
projection) ∘ Class L (signed-magnitude-squared) over a stack of bit-arrays;
no dedicated native symbol.

numpy-FREE (#564); rc129 restores the numpy-carrier FORMAT: ``signed_sum_squared``
takes plain ``list[int]`` bit-arrays and returns a numpy-free 1-D ``Vec``
(``.shape`` + scalar ``v[i]``; the small non-negative integer scores are exact
as float64 doubles) — NOT a bare ``list[int]``. The reference values are
hand-computed and the property checks are stdlib arithmetic; no numpy oracle.
"""
import random

import pytest

from srmech.amsc import coupling
from srmech.amsc.vec import Vec


def _ref_signed_sum_squared(sources):
    """Reference: per position, ``(Σ_sources (2·bit − 1))²`` (stdlib)."""
    n = len(sources[0])
    out = []
    for pos in range(n):
        s = sum(2 * src[pos] - 1 for src in sources)
        out.append(s * s)
    return out


def test_known_values():
    # 3 sources, agreement vs balance per position.
    s1 = [1, 1, 0, 1]
    s2 = [1, 0, 0, 1]
    s3 = [1, 0, 1, 0]
    # bipolar sums per pos: (+1+1+1)=3, (+1-1-1)=-1, (-1-1+1)=-1, (+1+1-1)=1
    # squared:               9,                1,            1,           1
    assert coupling.signed_sum_squared([s1, s2, s3]) == [9, 1, 1, 1]


def test_full_agreement_and_balance():
    ones = [[1] * 5 for _ in range(4)]
    # all +1 -> sum 4 -> 16 everywhere (n_sources² = 16)
    assert coupling.signed_sum_squared(ones) == [16] * 5
    # two +1, two -1 -> balanced sum 0 -> 0
    bal = [[1] * 3, [1] * 3, [0] * 3, [0] * 3]
    assert coupling.signed_sum_squared(bal) == [0, 0, 0]


def test_single_source_is_one_everywhere():
    # one source: (2b-1)² = 1 for both b=0 and b=1
    out = coupling.signed_sum_squared([[0, 1, 0, 1]])
    assert out == [1, 1, 1, 1]


def test_matches_reference_formula_random():
    rng = random.Random(0)
    srcs = [[rng.randrange(2) for _ in range(64)] for _ in range(7)]
    assert coupling.signed_sum_squared(srcs) == _ref_signed_sum_squared(srcs)


def test_output_is_vec_nonnegative():
    rng = random.Random(1)
    srcs = [[rng.randrange(2) for _ in range(32)] for _ in range(5)]
    out = coupling.signed_sum_squared(srcs)
    assert isinstance(out, Vec)                      # rc129: numpy-free Vec carrier
    assert out.shape == (32,)
    # the integer scores are exact as float64 doubles (value-faithful)
    vals = out.tolist()
    assert all(x == int(x) for x in vals)            # integral-valued
    assert all(0 <= x <= 25 for x in vals)           # in [0, n_sources²]
    for x in out:                                    # Vec iterates SCALARS
        assert isinstance(x, float)


def test_validation():
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([])
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([[0, 2]])  # not a bit
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([[0, 1], [1]])  # length mismatch
