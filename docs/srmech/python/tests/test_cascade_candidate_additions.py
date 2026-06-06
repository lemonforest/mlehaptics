"""RBS-LM UPSTREAM_NOTES candidate-additions (v0.7.4rc2; PR #687 §1.2/§1.3 + rbs_nn Note 1).

Three pure-composition additions, all numpy-free:
- `cascade.signed_sum_squared` — the coupling-score (Class K bipolar ∘ Class L square)
- `cascade.top_k_by_score` — catalog selection (Class E sort ∘ Class K truncate)
- `hdc.bundle_with_ties` — majority for any N + the tie (Class K event) surfaced
"""
import pytest

from srmech.amsc.cascade import signed_sum_squared, top_k_by_score
from srmech.amsc import hdc


# ── §1.2 signed_sum_squared ───────────────────────────────────────────────────

def test_signed_sum_squared_all_agree():
    # 3 identical all-ones rows → per position s = +3 → s² = 9
    assert signed_sum_squared([[1, 1, 1], [1, 1, 1], [1, 1, 1]]) == [9, 9, 9]


def test_signed_sum_squared_cancel():
    # two opposite rows → s = 0 → 0 (incoherent)
    assert signed_sum_squared([[1, 0, 1], [0, 1, 0]]) == [0, 0, 0]


def test_signed_sum_squared_mixed():
    # col0: (+1+1−1)=+1→1 ; col1: (−1+1+1)=+1→1 ; col2: (+1−1−1)=−1→1
    assert signed_sum_squared([[1, 0, 1], [1, 1, 0], [0, 1, 0]]) == [1, 1, 1]


def test_signed_sum_squared_single_source():
    # one row → s = ±1 → all 1
    assert signed_sum_squared([[1, 0, 1, 0]]) == [1, 1, 1, 1]


def test_signed_sum_squared_no_abs_uses_square():
    # coherent-down (all zeros, 4 rows) → s = −4 → 16 (square carries the sign)
    assert signed_sum_squared([[0], [0], [0], [0]]) == [16]


def test_signed_sum_squared_rejects_ragged():
    with pytest.raises(ValueError):
        signed_sum_squared([[1, 0], [1, 0, 1]])


def test_signed_sum_squared_rejects_non_bit():
    with pytest.raises(ValueError):
        signed_sum_squared([[1, 2, 0]])


def test_signed_sum_squared_rejects_empty():
    with pytest.raises(ValueError):
        signed_sum_squared([])


# ── §1.3 top_k_by_score ───────────────────────────────────────────────────────

def test_top_k_largest():
    assert top_k_by_score([0.1, 0.9, 0.3, 0.7], 2) == [1, 3]


def test_top_k_smallest():
    assert top_k_by_score([0.1, 0.9, 0.3, 0.7], 2, largest=False) == [0, 2]


def test_top_k_stable_ties_ascending_index():
    # equal scores keep ascending index order (both directions)
    assert top_k_by_score([5, 5, 5, 5], 2) == [0, 1]
    assert top_k_by_score([5, 5, 5, 5], 2, largest=False) == [0, 1]


def test_top_k_zero_and_full():
    assert top_k_by_score([3, 1, 2], 0) == []
    assert top_k_by_score([3, 1, 2], 3) == [0, 2, 1]


def test_top_k_rejects_bad_k():
    with pytest.raises(ValueError):
        top_k_by_score([1, 2, 3], 4)
    with pytest.raises(ValueError):
        top_k_by_score([1, 2, 3], -1)


# ── rbs_nn Note 1 bundle_with_ties ────────────────────────────────────────────

def test_bundle_with_ties_odd_matches_bundle():
    # for odd N, majority must equal hdc.bundle exactly, and ties is all-zero
    vs = [bytes([0b10110010]), bytes([0b11000110]), bytes([0b10100011])]
    maj, ties = hdc.bundle_with_ties(vs)
    assert maj == hdc.bundle(vs)
    assert ties == bytes(1)            # no ties possible at odd N


def test_bundle_with_ties_even_surfaces_ties():
    # 2 vectors, one all-zero one all-ones → every bit is an exact tie
    z = bytes([0x00, 0x00])
    o = bytes([0xFF, 0xFF])
    maj, ties = hdc.bundle_with_ties([z, o])
    assert maj == bytes([0x00, 0x00])   # tie resolves majority to 0
    assert ties == bytes([0xFF, 0xFF])  # every position is a Class K tie event


def test_bundle_with_ties_even_strict_majority():
    # 4 vectors: a bit set in 3/4 → strict majority (set, not tied)
    vs = [bytes([0b1]), bytes([0b1]), bytes([0b1]), bytes([0b0])]
    maj, ties = hdc.bundle_with_ties(vs)
    assert (maj[0] & 1) == 1
    assert (ties[0] & 1) == 0


def test_bundle_with_ties_rejects_empty():
    with pytest.raises(ValueError):
        hdc.bundle_with_ties([])


def test_bundle_with_ties_rejects_ragged():
    with pytest.raises(ValueError):
        hdc.bundle_with_ties([bytes(2), bytes(3)])
