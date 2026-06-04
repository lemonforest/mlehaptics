"""#797 op (a2) — Klein-4 holographic erasure code (F353 measured substitute).

v0.7.0rc27. The order-2 Klein-4 store is k=2-DETECT natively (F294: no Z3,
3∤4). This holographic-erasure code supplies k=3-CORRECT with **no Z3** —
the *measured substitute* for the (a1) explicit triality corrector. Replicate
the store across `replicas` blocks; any one surviving replica-subregion
(1/replicas) reconstructs the whole.

F353 measured tolerances, pinned here:
  * known-location erasure: (replicas-1)/replicas = 3/4 at the default;
  * blind correction: 1 error guaranteed (1/4); fails at 3 errors.
"""
import numpy as np
import pytest

from srmech.amsc import hdc as H


def _v(seed=0, D=64):
    return np.random.default_rng(seed).integers(0, 4, size=D).astype(np.uint8)


def test_encode_shape_and_replica_major():
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    assert store.shape == (v.size * 4,)
    # replica-major: each block is a full copy.
    assert np.array_equal(store.reshape(4, v.size)[0], v)


def test_round_trip_no_error():
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    assert np.array_equal(H.klein4_holographic_decode(store), v)


def test_known_erasure_three_quarters_recovers_exactly():
    """Drop 3 of 4 replica-blocks (3/4 of the store) → exact recovery."""
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    erased = np.zeros(store.size, dtype=bool)
    erased[: v.size * 3] = True            # wipe first 3 replicas
    assert np.array_equal(H.klein4_holographic_decode(store, erased=erased), v)


def test_known_erasure_any_single_surviving_block_reconstructs():
    """Any one of the four replica-subregions suffices (holographic)."""
    v = _v(seed=3)
    store = H.klein4_holographic_encode(v, replicas=4)
    for keep in range(4):
        erased = np.ones(store.size, dtype=bool)
        erased[keep * v.size : (keep + 1) * v.size] = False
        assert np.array_equal(
            H.klein4_holographic_decode(store, erased=erased), v
        ), keep


def test_blind_one_error_corrected():
    """1 of 4 copies corrupted per position → 3-of-4 majority recovers (1/4)."""
    v = _v()
    blocks = H.klein4_holographic_encode(v, replicas=4).reshape(4, v.size)
    blocks[0] = (blocks[0] + 1) % 4
    assert np.array_equal(H.klein4_holographic_decode(blocks.reshape(-1)), v)


def test_blind_three_errors_fails_past_capacity():
    """3 of 4 corrupted to the same wrong value → majority lost (no silent claim)."""
    v = _v()
    blocks = H.klein4_holographic_encode(v, replicas=4).reshape(4, v.size)
    wrong = (v + 1) % 4
    blocks[0] = wrong
    blocks[1] = wrong
    blocks[2] = wrong
    rec = H.klein4_holographic_decode(blocks.reshape(-1))
    assert not np.array_equal(rec, v)      # past the 1/4 blind capacity


def test_all_replicas_erased_raises():
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    with pytest.raises(ValueError):
        H.klein4_holographic_decode(store, erased=np.ones(store.size, dtype=bool))


def test_rejects_bad_replicas():
    v = _v()
    for bad in (1, 0, -2, True, 2.0):
        with pytest.raises((ValueError, TypeError)):
            H.klein4_holographic_encode(v, replicas=bad)


def test_decode_rejects_misshaped_store():
    with pytest.raises(ValueError):
        H.klein4_holographic_decode(np.zeros(7, dtype=np.uint8), replicas=4)


def test_replicas_three_gives_two_thirds_erasure():
    """Tolerance scales with replicas: replicas=3 → 2/3 known-erasure."""
    v = _v(seed=5)
    store = H.klein4_holographic_encode(v, replicas=3)
    erased = np.zeros(store.size, dtype=bool)
    erased[: v.size * 2] = True            # drop 2 of 3
    assert np.array_equal(
        H.klein4_holographic_decode(store, replicas=3, erased=erased), v
    )
