"""#797 op (a2) — Klein-4 holographic erasure code (F353 measured substitute).

v0.7.0rc27. The order-2 Klein-4 store is k=2-DETECT natively (F294: no Z3,
3∤4). This holographic-erasure code supplies k=3-CORRECT with **no Z3** —
the *measured substitute* for the (a1) explicit triality corrector. Replicate
the store across `replicas` blocks; any one surviving replica-subregion
(1/replicas) reconstructs the whole.

F353 measured tolerances, pinned here:
  * known-location erasure: (replicas-1)/replicas = 3/4 at the default;
  * blind correction: 1 error guaranteed (1/4); fails at 3 errors.

numpy-FREE (#564): Klein-4 vectors are stdlib ``list[int]`` in {0,1,2,3}
(generated with ``random.Random``), the store is the framework-native ``HV``
carrier (``.tolist()`` / ``.buffer`` / ``==`` / ``len``), erasure masks are
``list[bool]``, and equality is the ``HV`` value-compare — no numpy oracle.
"""
import random

import pytest

from srmech.amsc import hdc as H


def _v(seed=0, D=64):
    """A random Klein-4 vector: ``list[int]`` in {0, 1, 2, 3}, length D."""
    rng = random.Random(seed)
    return [rng.randrange(4) for _ in range(D)]


def _blocks(store, replicas, D):
    """Split a store into ``replicas`` blocks of length ``D`` (replica-major)."""
    flat = store.tolist() if hasattr(store, "tolist") else list(store)
    return [flat[r * D : (r + 1) * D] for r in range(replicas)]


def test_encode_shape_and_replica_major():
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    assert len(store) == len(v) * 4
    # replica-major: each block is a full copy.
    assert _blocks(store, 4, len(v))[0] == v


def test_round_trip_no_error():
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    assert H.klein4_holographic_decode(store) == v


def test_known_erasure_three_quarters_recovers_exactly():
    """Drop 3 of 4 replica-blocks (3/4 of the store) → exact recovery."""
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    erased = [False] * len(store)
    for i in range(len(v) * 3):           # wipe first 3 replicas
        erased[i] = True
    assert H.klein4_holographic_decode(store, erased=erased) == v


def test_known_erasure_any_single_surviving_block_reconstructs():
    """Any one of the four replica-subregions suffices (holographic)."""
    v = _v(seed=3)
    store = H.klein4_holographic_encode(v, replicas=4)
    D = len(v)
    for keep in range(4):
        erased = [True] * len(store)
        for i in range(keep * D, (keep + 1) * D):
            erased[i] = False
        assert H.klein4_holographic_decode(store, erased=erased) == v, keep


def test_blind_one_error_corrected():
    """1 of 4 copies corrupted per position → 3-of-4 majority recovers (1/4)."""
    v = _v()
    D = len(v)
    blocks = _blocks(H.klein4_holographic_encode(v, replicas=4), 4, D)
    blocks[0] = [(x + 1) % 4 for x in blocks[0]]
    flat = [x for blk in blocks for x in blk]
    assert H.klein4_holographic_decode(flat) == v


def test_blind_three_errors_fails_past_capacity():
    """3 of 4 corrupted to the same wrong value → majority lost (no silent claim)."""
    v = _v()
    D = len(v)
    blocks = _blocks(H.klein4_holographic_encode(v, replicas=4), 4, D)
    wrong = [(x + 1) % 4 for x in v]
    blocks[0] = list(wrong)
    blocks[1] = list(wrong)
    blocks[2] = list(wrong)
    flat = [x for blk in blocks for x in blk]
    rec = H.klein4_holographic_decode(flat)
    assert rec != v      # past the 1/4 blind capacity


def test_all_replicas_erased_raises():
    v = _v()
    store = H.klein4_holographic_encode(v, replicas=4)
    with pytest.raises(ValueError):
        H.klein4_holographic_decode(store, erased=[True] * len(store))


def test_rejects_bad_replicas():
    v = _v()
    for bad in (1, 0, -2, True, 2.0):
        with pytest.raises((ValueError, TypeError)):
            H.klein4_holographic_encode(v, replicas=bad)


def test_decode_rejects_misshaped_store():
    with pytest.raises(ValueError):
        H.klein4_holographic_decode([0] * 7, replicas=4)


def test_replicas_three_gives_two_thirds_erasure():
    """Tolerance scales with replicas: replicas=3 → 2/3 known-erasure."""
    v = _v(seed=5)
    store = H.klein4_holographic_encode(v, replicas=3)
    erased = [False] * len(store)
    for i in range(len(v) * 2):           # drop 2 of 3
        erased[i] = True
    assert H.klein4_holographic_decode(store, replicas=3, erased=erased) == v
