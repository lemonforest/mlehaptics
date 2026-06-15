"""§50 (rc155): the streaming holographic Klein-4 bundle-accumulate primitives.

``klein4_bundle_accumulate`` / ``klein4_bundle_resolve`` are the INCREMENTAL form
of the batch :func:`srmech.amsc.hdc.klein4_bundle` — they fold one Klein-4 vector
at a time into a fixed-width ``(1 + 2*D)`` uint32 accumulator, so a holographic
store of N relationships never materialises the N inputs and stays fixed-width
(it grows with the #coordinates ``D``, not the #folded vectors — the fix for "why
is the HDC object growing to gigs?"). ``cooccurrence_fold`` is the holographic
DUAL of the explicit-edge §17-U1 ``cooccurrence_edges``.

The headline contract: ``resolve(accumulate(... each v ...)) == klein4_bundle(*vs)``
BIT-IDENTICALLY, native OR pure-Python. The native standalone-C kernels
(``srmech_klein4_bundle_accumulate`` / ``_resolve``) run the fold at corpus scale;
pure-Python is the complete alternative for a no-C environment.

numpy-free per the module's discipline (no numpy import, no ``np.``).
"""
import array

import srmech.amsc._native as _native
from srmech.amsc.hdc import (
    klein4_random,
    klein4_bundle,
    klein4_bundle_accumulate,
    klein4_bundle_resolve,
    klein4_similarity,
    cooccurrence_fold,
)


def _bundle_via_fold(vs):
    acc = None
    for v in vs:
        acc = klein4_bundle_accumulate(acc, v)
    return klein4_bundle_resolve(acc)


def test_accumulate_resolve_is_bit_identical_to_batch_bundle():
    """The load-bearing §50 contract: the incremental fold == the batch bundle,
    bit-for-bit, for even AND odd counts (the tie→0 boundary is the even case)."""
    for n in (1, 2, 3, 4, 5, 8, 16, 33, 64):
        vs = [klein4_random(48, seed=4000 + i) for i in range(n)]
        folded = _bundle_via_fold(vs)
        batch = klein4_bundle(*vs)
        assert bytes(folded._buf) == bytes(batch._buf), f"n={n} fold != batch"


def test_accumulator_is_fixed_width_independent_of_count():
    """The accumulator is ``1 + 2*D`` uint32 no matter how many vectors fold in —
    the store grows with D, not the #inputs (the whole point of §50)."""
    d = 32
    acc = None
    for i in range(500):
        acc = klein4_bundle_accumulate(acc, klein4_random(d, seed=i))
    assert isinstance(acc, array.array) and acc.typecode == "I"
    assert len(acc) == 1 + 2 * d        # fixed width
    assert acc[0] == 500                # n folded recorded


def test_accumulate_creates_and_then_reuses_the_same_array():
    """``acc=None`` creates a fresh accumulator; subsequent folds mutate it in
    place and return the SAME object (so ``acc = accumulate(acc, v)`` is a fold)."""
    v0 = klein4_random(16, seed=1)
    acc = klein4_bundle_accumulate(None, v0)
    same = klein4_bundle_accumulate(acc, klein4_random(16, seed=2))
    assert same is acc and acc[0] == 2


def test_resolve_of_single_vector_is_that_vector():
    """A bundle of one is the vector itself (majority of one)."""
    v = klein4_random(40, seed=99)
    acc = klein4_bundle_accumulate(None, v)
    assert bytes(klein4_bundle_resolve(acc)._buf) == bytes(_as(v))


def test_dimension_mismatch_rejected():
    import pytest
    acc = klein4_bundle_accumulate(None, klein4_random(16, seed=1))
    with pytest.raises(ValueError):
        klein4_bundle_accumulate(acc, klein4_random(17, seed=2))


def test_native_matches_forced_pure_bit_for_bit():
    """When the native kernel is built, the C fold is byte-identical to the pure
    fold — the standalone-C parity proof (skips on a pure-wheel dev tree)."""
    if not (_native.HAS_NATIVE
            and hasattr(_native.LIB, "srmech_klein4_bundle_accumulate")):
        return  # no native kernel here — the pure path is the only path
    vs = [klein4_random(56, seed=7000 + i) for i in range(20)]
    native = _bundle_via_fold(vs)
    orig = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        pure = _bundle_via_fold(vs)
    finally:
        _native.HAS_NATIVE = orig
    assert bytes(native._buf) == bytes(pure._buf)


def test_cooccurrence_fold_readout_and_bounded_width():
    """Co-occurring tokens score above non-neighbours under similarity-cleanup, and
    every per-token bundle is the SAME fixed width (vocab-bounded, not edge-bounded)."""
    toks = ["a", "b", "c", "a", "b", "d", "a", "c", "e"]
    res = cooccurrence_fold(toks, window=1, dim=128, seed=3)
    assert set(res["bundles"]) == set(res["codes"]) == set(res["vocab"])
    assert res["n_tokens"] == len(toks)
    # every bundle is one fixed-width Klein-4 vector (dim bytes)
    assert all(len(b._buf) == 128 for b in res["bundles"].values())
    # 'a' co-occurs with 'b' and 'c' (neighbours) but never 'e' → higher similarity
    s_ab = klein4_similarity(res["bundles"]["a"], res["codes"]["b"])
    s_ac = klein4_similarity(res["bundles"]["a"], res["codes"]["c"])
    s_ae = klein4_similarity(res["bundles"]["a"], res["codes"]["e"])
    assert s_ab > s_ae and s_ac > s_ae


def test_cooccurrence_codes_are_deterministic_in_seed():
    """The same (token, seed) always yields the same atomic code, so a readout is
    reproducible across calls/streams."""
    r1 = cooccurrence_fold(["x", "y", "x"], window=1, dim=64, seed=11)
    r2 = cooccurrence_fold(["y", "x", "y"], window=1, dim=64, seed=11)
    assert bytes(r1["codes"]["x"]._buf) == bytes(r2["codes"]["x"]._buf)


def _as(v):
    # the klein4 HV carrier's raw bytes, robust to HV vs bytes inputs
    return bytes(v._buf) if hasattr(v, "_buf") else bytes(v)
