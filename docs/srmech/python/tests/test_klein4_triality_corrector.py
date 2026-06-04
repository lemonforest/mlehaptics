"""#797 op (a1) — explicit order-3 triality-recursion corrector (F359 contract).

v0.7.0rc28. The order-2 Klein-4 store is k=2-DETECT natively (F294: no Z3,
3∤4). The EXPLICIT k=3-CORRECT path past the order-2 4-cap uses the order-3
triality (τ³=I): the store carries the triality ORBIT [v, T(v), T²(v)] for
T = klein4_triality_cycle, and decode brings every orbit-block back to the
common v-frame (T⁻¹/T) then 2-of-3 majority-votes.

The F359 5-bar contract, each pinned below:
  1. blind correction beats the F353 holographic 0.25 baseline (single-error
     recovery exact, rate 1.0);
  2. the 3rd vote IS the order-3 triality orbit of the same value (block2=T²v);
  3. C/Python parity (Python-first; C peer is the tracked next voxel);
  4. disable the order-3 op → degrade to k=2-DETECT (correction attributable to
     the triality, not to plain replication);
  5. WIDTH-step only — depth != 1 raises (continuum count-recursion is open).
"""
import numpy as np
import pytest

from srmech.amsc import hdc as H


def _v(seed=0, D=64):
    return np.random.default_rng(seed).integers(0, 4, size=D).astype(np.uint8)


# --- encode shape + orbit-major layout --------------------------------------

def test_encode_shape_is_triple():
    v = _v()
    store = H.klein4_triality_encode(v)
    assert store.shape == (v.size * 3,)
    assert store.dtype == np.uint8


def test_encode_blocks_are_the_triality_orbit():
    """Bar 2: the three blocks ARE [v, T(v), T²(v)] — the order-3 orbit; the
    third vote is the triality orbit's third element, not an external render."""
    v = _v(3)
    store = H.klein4_triality_encode(v)
    b0, b1, b2 = store.reshape(3, v.size)
    t1 = H.klein4_triality_cycle(v)
    t2 = H.klein4_triality_cycle(t1)
    assert np.array_equal(b0, v)
    assert np.array_equal(b1, t1)
    assert np.array_equal(b2, t2)


# --- clean round-trip + single-error correction (bar 1) ---------------------

def test_round_trip_no_error():
    v = _v()
    store = H.klein4_triality_encode(v)
    assert np.array_equal(H.klein4_triality_correct(store), v)


def test_single_error_always_corrected():
    """Bar 1: a single error in any one block is outvoted 2-of-3 → exact
    recovery (rate 1.0 over random single errors), strictly beating the F353
    holographic blind baseline of 0.25."""
    v = _v(11, D=48)
    store = H.klein4_triality_encode(v)
    rng = np.random.default_rng(5)
    ok = 0
    N = 300
    for _ in range(N):
        s = store.copy()
        i = int(rng.integers(0, s.size))
        s[i] = np.uint8((int(s[i]) + int(rng.integers(1, 4))) % 4)  # flip sector
        ok += int(np.array_equal(H.klein4_triality_correct(s), v))
    rate = ok / N
    assert rate == 1.0, f"single-error recovery {rate} != 1.0"
    assert rate > 0.25  # beats the F353 holographic blind baseline


def test_corrects_one_error_in_each_block_position():
    """One corrupted position, swept across all three blocks → corrected."""
    v = _v(2, D=16)
    store = H.klein4_triality_encode(v)
    for block in range(3):
        for pos in range(v.size):
            s = store.copy()
            idx = block * v.size + pos
            s[idx] = np.uint8((int(s[idx]) + 1) % 4)
            assert np.array_equal(H.klein4_triality_correct(s), v)


# --- bar 4: order-3 triality is load-bearing --------------------------------

def test_order3_disabled_degrades_to_detect_not_correct():
    """Bar 4: WITHOUT the inverse-to-frame step (the order-3 op), the raw
    orbit-blocks {v, Tv, T²v} disagree on every non-zero sector, so a naive
    majority does NOT recover v — you fall back to k=2-DETECT. The correct
    op (with the triality inversion) DOES recover v. Correction is therefore
    attributable to the order-3 triality, not to plain replication."""
    v = np.array([1, 2, 3, 1, 2, 3, 2, 3], dtype=np.uint8)  # has 2s and 3s
    store = H.klein4_triality_encode(v)
    blocks = store.reshape(3, v.size)
    # Naive majority over the RAW blocks (order-3 op disabled / not inverted):
    counts = np.zeros((v.size, 4), dtype=np.int64)
    for st in range(4):
        counts[:, st] = (blocks == st).sum(axis=0)
    naive = counts.argmax(axis=1).astype(np.uint8)
    assert not np.array_equal(naive, v)  # detect-only; cannot correct
    # The real op (triality inverted to the common frame) recovers v:
    assert np.array_equal(H.klein4_triality_correct(store), v)


# --- bar 5: width-step only -------------------------------------------------

def test_depth_other_than_one_raises():
    """Bar 5: only the width-step (depth=1) is in domain; the continuum
    count-recursion is open math and must RAISE, not fabricate."""
    v = _v()
    store = H.klein4_triality_encode(v)
    for bad in (0, 2, 3, -1):
        with pytest.raises(NotImplementedError):
            H.klein4_triality_correct(store, depth=bad)
    # depth=1 (default) is fine:
    assert np.array_equal(H.klein4_triality_correct(store, depth=1), v)


# --- input validation -------------------------------------------------------

def test_encode_rejects_non_klein4():
    with pytest.raises((ValueError, TypeError)):
        H.klein4_triality_encode(np.array([0, 1, 4, 2], dtype=np.uint8))  # 4∉{0..3}


def test_correct_rejects_non_multiple_of_three():
    with pytest.raises(ValueError):
        H.klein4_triality_correct(np.array([0, 1, 2, 3], dtype=np.uint8))  # len 4


def test_correct_rejects_empty():
    with pytest.raises(ValueError):
        H.klein4_triality_correct(np.array([], dtype=np.uint8))


# --- identity sector (0) is triality-fixed ----------------------------------

def test_all_identity_store_round_trips():
    """T fixes sector 0, so an all-0 store is invariant under the orbit and
    still corrects (the trivial fixed point)."""
    v = np.zeros(12, dtype=np.uint8)
    store = H.klein4_triality_encode(v)
    assert np.array_equal(store, np.zeros(36, dtype=np.uint8))
    assert np.array_equal(H.klein4_triality_correct(store), v)
