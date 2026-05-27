"""Class K ∘ L signed-sum coupling score — ``srmech.amsc.coupling``.

``signed_sum_squared(sources)`` = per-element ``(Σ_sources (2·bit − 1))²``
(v0.4.3rc3, UPSTREAM_NOTES §1.2). A composition of Class K (bipolar sign-
projection) ∘ Class L (signed-magnitude-squared) over a stack of bit-arrays;
no dedicated native symbol, so these are pure numpy-reference property tests.
"""

import numpy as np
import pytest

from srmech.amsc import coupling


def test_known_values():
    # 3 sources, agreement vs balance per position.
    s1 = np.array([1, 1, 0, 1], dtype=np.uint8)
    s2 = np.array([1, 0, 0, 1], dtype=np.uint8)
    s3 = np.array([1, 0, 1, 0], dtype=np.uint8)
    # bipolar sums per pos: (+1+1+1)=3, (+1-1-1)=-1, (-1-1+1)=-1, (+1+1-1)=1
    # squared:               9,                1,            1,           1
    assert coupling.signed_sum_squared([s1, s2, s3]).tolist() == [9, 1, 1, 1]


def test_full_agreement_and_balance():
    ones = [np.ones(5, dtype=np.uint8) for _ in range(4)]
    # all +1 -> sum 4 -> 16 everywhere (n_sources² = 16)
    assert coupling.signed_sum_squared(ones).tolist() == [16] * 5
    # two +1, two -1 -> balanced sum 0 -> 0
    bal = [np.ones(3, np.uint8), np.ones(3, np.uint8),
           np.zeros(3, np.uint8), np.zeros(3, np.uint8)]
    assert coupling.signed_sum_squared(bal).tolist() == [0, 0, 0]


def test_single_source_is_one_everywhere():
    # one source: (2b-1)² = 1 for both b=0 and b=1
    out = coupling.signed_sum_squared([np.array([0, 1, 0, 1], np.uint8)])
    assert out.tolist() == [1, 1, 1, 1]


def test_matches_reference_formula_random():
    rng = np.random.default_rng(0)
    srcs = [rng.integers(0, 2, size=64, dtype=np.uint8) for _ in range(7)]
    expected = (sum(2 * s.astype(np.int64) - 1 for s in srcs)) ** 2
    assert (coupling.signed_sum_squared(srcs) == expected).all()


def test_output_is_int64_nonnegative():
    rng = np.random.default_rng(1)
    srcs = [rng.integers(0, 2, size=32, dtype=np.uint8) for _ in range(5)]
    out = coupling.signed_sum_squared(srcs)
    assert out.dtype == np.int64
    assert (out >= 0).all() and (out <= 25).all()  # in [0, n_sources²]


def test_validation():
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([])
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([np.array([0, 2], np.uint8)])  # not a bit
    with pytest.raises(ValueError):
        coupling.signed_sum_squared([np.array([0, 1], np.uint8),
                                     np.array([1], np.uint8)])  # length mismatch
