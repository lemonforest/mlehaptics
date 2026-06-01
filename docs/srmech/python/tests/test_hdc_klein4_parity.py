"""Klein-4 {0,1,2,3} Class M variant — algebraic properties + C/Python parity.

Klein-4 (v0.4.3rc2) is rank-2 abelian Class M over (F₂)² = Z₂×Z₂: uint8
hypervectors over {0,1,2,3}, bind = component-wise XOR (self-inverse, abelian,
identity 0), bundle = per-bit majority (ties → 0). The four states map to the
four (γ₅, iω₇) chirality sectors. See ``srmech.amsc.hdc.klein4_*`` +
UPSTREAM_NOTES §4.

Two tiers: numpy-reference property tests (always run) + C↔Python bit-exact
parity (native only; built in the cibuildwheel matrix).
"""

import ctypes

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc import hdc


_K4_NATIVE = _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_klein4_bind")
_requires_native = pytest.mark.skipif(
    not _K4_NATIVE,
    reason="native klein-4 surface not present (pure-Python or pre-klein4 lib)",
)


# --------------------------------------------------------------------------
# Algebraic properties (numpy reference) — always run
# --------------------------------------------------------------------------

def test_klein4_group_axioms():
    rng = np.random.default_rng(1)
    a, b, c = (hdc.klein4_random(128, rng) for _ in range(3))
    assert set(np.unique(a).tolist()) <= {0, 1, 2, 3}
    # identity 0, self-inverse, commutative, associative
    assert (hdc.klein4_bind(a, np.zeros_like(a)) == a).all()
    assert (hdc.klein4_bind(a, hdc.klein4_bind(a, b)) == b).all()
    assert (hdc.klein4_bind(a, b) == hdc.klein4_bind(b, a)).all()
    assert (hdc.klein4_bind(hdc.klein4_bind(a, b), c)
            == hdc.klein4_bind(a, hdc.klein4_bind(b, c))).all()
    # every element is its own inverse (Klein-four group property)
    assert (hdc.klein4_bind(a, a) == 0).all()


def test_klein4_unbind():
    rng = np.random.default_rng(2)
    a = hdc.klein4_random(256, rng); b = hdc.klein4_random(256, rng)
    assert (hdc.klein4_unbind(hdc.klein4_bind(a, b), a) == b).all()


def test_klein4_chirality_flips():
    rng = np.random.default_rng(3)
    a = hdc.klein4_random(64, rng)
    # γ₅ = XOR 2, iω₇ = XOR 1, CPT = XOR 3 = both flips composed
    assert (hdc.klein4_chirality_flip_omega7(hdc.klein4_chirality_flip_gamma5(a))
            == hdc.klein4_cpt_mirror(a)).all()
    # each flip is an involution
    for flip in (hdc.klein4_chirality_flip_gamma5,
                 hdc.klein4_chirality_flip_omega7,
                 hdc.klein4_cpt_mirror):
        assert (flip(flip(a)) == a).all()
    # explicit sector map
    base = np.array([0, 1, 2, 3], dtype=np.uint8)
    assert list(hdc.klein4_chirality_flip_gamma5(base)) == [2, 3, 0, 1]
    assert list(hdc.klein4_chirality_flip_omega7(base)) == [1, 0, 3, 2]
    assert list(hdc.klein4_cpt_mirror(base)) == [3, 2, 1, 0]


def test_klein4_bundle_per_bit_majority():
    v1 = np.array([0, 3, 1], dtype=np.uint8)
    v2 = np.array([0, 3, 2], dtype=np.uint8)
    v3 = np.array([1, 0, 3], dtype=np.uint8)
    # pos0: bit0 {0,0,1}->0, bit1 {0,0,0}->0 => 0
    # pos1: states 3,3,0: bit0 {1,1,0}->1, bit1 {1,1,0}->1 => 3
    # pos2: states 1,2,3: bit0 {1,0,1}->1, bit1 {0,1,1}->1 => 3
    assert list(hdc.klein4_bundle(v1, v2, v3)) == [0, 3, 3]
    # even count, exact tie on a bit → 0
    assert list(hdc.klein4_bundle(np.array([1], np.uint8), np.array([2], np.uint8))) == [0]


def test_klein4_similarity_and_sector_count():
    rng = np.random.default_rng(4)
    a = hdc.klein4_random(200, rng)
    assert hdc.klein4_similarity(a, a) == 1.0
    x = np.array([0, 1, 2, 3], np.uint8); y = np.array([0, 1, 3, 3], np.uint8)
    assert hdc.klein4_similarity(x, y) == pytest.approx(0.75)
    assert hdc.klein4_sector_count(np.array([0, 0, 1, 2, 2, 2, 3], np.uint8)).tolist() == [2, 1, 3, 1]


def test_klein4_validation():
    with pytest.raises(ValueError):
        hdc.klein4_bind(np.array([4, 0], np.uint8), np.array([1, 1], np.uint8))
    with pytest.raises(ValueError):
        hdc.klein4_bundle()


# --------------------------------------------------------------------------
# C ↔ Python bit-exact parity (native only)
# --------------------------------------------------------------------------

def _c_bind(a, b):
    n = a.size
    ab = (ctypes.c_uint8 * n).from_buffer_copy(a.astype(np.uint8).tobytes())
    bb = (ctypes.c_uint8 * n).from_buffer_copy(b.astype(np.uint8).tobytes())
    out = (ctypes.c_uint8 * n)()
    assert _native.LIB.srmech_klein4_bind(ab, bb, n, out) == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.uint8).copy()


def _c_bundle(vecs):
    n = vecs[0].size; nv = len(vecs)
    bufs = [(ctypes.c_uint8 * n).from_buffer_copy(v.astype(np.uint8).tobytes()) for v in vecs]
    ptr = (ctypes.POINTER(ctypes.c_uint8) * nv)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_uint8)) for b in bufs)
    )
    out = (ctypes.c_uint8 * n)()
    assert _native.LIB.srmech_klein4_bundle(ptr, nv, n, out) == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.uint8).copy()


def _c_similarity(a, b):
    n = a.size
    ab = (ctypes.c_uint8 * n).from_buffer_copy(a.astype(np.uint8).tobytes())
    bb = (ctypes.c_uint8 * n).from_buffer_copy(b.astype(np.uint8).tobytes())
    out = ctypes.c_double(0.0)
    assert _native.LIB.srmech_klein4_similarity(ab, bb, n, ctypes.byref(out)) == _native.SRMECH_OK
    return out.value


@_requires_native
def test_parity_klein4_bind():
    rng = np.random.default_rng(10)
    for _ in range(20):
        a = hdc.klein4_random(257, rng); b = hdc.klein4_random(257, rng)
        assert (_c_bind(a, b) == hdc.klein4_bind(a, b)).all()


@_requires_native
def test_parity_klein4_bundle():
    rng = np.random.default_rng(11)
    for nv in (1, 2, 3, 8, 33):
        vecs = [hdc.klein4_random(129, rng) for _ in range(nv)]
        assert (_c_bundle(vecs) == hdc.klein4_bundle(*vecs)).all()


@_requires_native
def test_parity_klein4_similarity():
    rng = np.random.default_rng(12)
    for _ in range(20):
        a = hdc.klein4_random(200, rng); b = hdc.klein4_random(200, rng)
        assert _c_similarity(a, b) == pytest.approx(hdc.klein4_similarity(a, b))


# --------------------------------------------------------------------------
# v0.6.0rc13 — the sectors= / parallel= / mode= flag (§11.3 forward-ask).
# Two modes: chunk (data-parallel, BIT-IDENTICAL) + chirality (F233 4-sector,
# klein4-native XOR-flips). Default-ON at >=4 cores; all defaults are
# value-preserving. Pure-Python orchestration (co-equal parity: it does NOT
# route through the C peer).
# --------------------------------------------------------------------------

def _k4(seed, D=257):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 4, size=D, dtype=np.uint8)


def test_klein4_sectors_value_preserving_across_modes():
    """bind/bundle/similarity are value-preserving under BOTH default modes."""
    a, b = _k4(20), _k4(21)
    vs = [_k4(30 + i) for i in range(5)]
    bind1 = hdc.klein4_bind(a, b, sectors=1)
    bund1 = hdc.klein4_bundle(*vs, sectors=1)
    sim1 = hdc.klein4_similarity(a, b, sectors=1)
    # bind: chunk + chirality both == serial (XOR collapses all 4 sectors).
    assert np.array_equal(hdc.klein4_bind(a, b, sectors=4, mode="chunk"), bind1)
    assert np.array_equal(hdc.klein4_bind(a, b, sectors=4, mode="chirality"), bind1)
    # bundle: chunk bit-identical; chirality runs + preserves shape.
    assert np.array_equal(hdc.klein4_bundle(*vs, sectors=4, mode="chunk"), bund1)
    assert hdc.klein4_bundle(*vs, sectors=4, mode="chirality").shape == bund1.shape
    # similarity: chunk + chirality(sector-0) both EXACTLY == serial float.
    assert hdc.klein4_similarity(a, b, sectors=4, mode="chunk") == sim1
    assert hdc.klein4_similarity(a, b, sectors=4, mode="chirality") == sim1


def test_klein4_sectors_chunk_partitions_all_sector_counts():
    """Chunk mode is bit-identical for every lane count 1..4 (and odd D)."""
    a, b = _k4(40, D=130), _k4(41, D=130)
    serial = hdc.klein4_bind(a, b, sectors=1)
    for n in (1, 2, 3, 4):
        assert np.array_equal(hdc.klein4_bind(a, b, sectors=n, mode="chunk"), serial)


def test_klein4_parallel_alias_and_default_on():
    """parallel=True→4, parallel=False→1; the default (None) is value-preserving
    regardless of the machine's core count."""
    a, b = _k4(50), _k4(51)
    serial = hdc.klein4_bind(a, b, sectors=1)
    assert np.array_equal(hdc.klein4_bind(a, b, parallel=True), serial)
    assert np.array_equal(hdc.klein4_bind(a, b, parallel=False), serial)
    assert np.array_equal(hdc.klein4_bind(a, b), serial)  # default-on path
    # default sectors policy: 4 when >=4 cores else 1.
    from srmech.amsc.hdc import _klein4_default_sectors
    import os
    assert _klein4_default_sectors() == (4 if (os.cpu_count() or 1) >= 4 else 1)


def test_klein4_sectors_range_and_mode_guards():
    a, b = _k4(60), _k4(61)
    for bad in (0, 5, -1):
        with pytest.raises(ValueError, match="1..4|sectors"):
            hdc.klein4_bind(a, b, sectors=bad)
    with pytest.raises(ValueError, match="sectors"):
        hdc.klein4_bind(a, b, sectors=True)  # bool is not a valid int
    for op in (hdc.klein4_bind, hdc.klein4_similarity):
        with pytest.raises(ValueError, match="mode"):
            op(a, b, sectors=4, mode="bogus")
    with pytest.raises(ValueError, match="mode"):
        hdc.klein4_bundle(_k4(62), sectors=4, mode="bogus")


def test_klein4_unbind_still_self_inverse_under_default_flag():
    """unbind (which routes through bind, now flag-bearing) stays self-inverse."""
    a, b = _k4(70), _k4(71)
    c = hdc.klein4_bind(a, b)
    assert np.array_equal(hdc.klein4_unbind(c, a), b)


# --------------------------------------------------------------------------
# v0.6.0rc18 — the co-equal C peer srmech_klein4_triality_cycle (the A-arc's
# silicon tier). Differential C-vs-Python on the order-3 S3 = Aut(V4) relabel,
# both directions. Guarded by its OWN symbol hasattr — a klein4-capable but
# pre-rc18 lib (rc13-rc17) has bind but not triality_cycle, so the parity
# test SKIPS there and runs in CI where the lib is freshly built.
# --------------------------------------------------------------------------

_K4_TRIALITY_NATIVE = _K4_NATIVE and hasattr(
    _native.LIB, "srmech_klein4_triality_cycle"
)
_requires_triality_native = pytest.mark.skipif(
    not _K4_TRIALITY_NATIVE,
    reason="native srmech_klein4_triality_cycle absent (pure-Python or pre-rc18 lib)",
)


def _c_triality(arr, inverse=False):
    n = arr.size
    inp = (ctypes.c_uint8 * n).from_buffer_copy(arr.astype(np.uint8).tobytes())
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_klein4_triality_cycle(
        inp, n, 1 if inverse else 0, out
    )
    assert rc == _native.SRMECH_OK
    return np.frombuffer(bytes(out), dtype=np.uint8).copy()


@_requires_triality_native
def test_parity_klein4_triality_cycle():
    rng = np.random.default_rng(18)
    for _ in range(20):
        a = hdc.klein4_random(257, rng)
        assert (_c_triality(a, False) == hdc.klein4_triality_cycle(a)).all()
        assert (_c_triality(a, True)
                == hdc.klein4_triality_cycle(a, inverse=True)).all()
    # explicit maps + order-3 identity, computed in C
    base = np.array([0, 1, 2, 3], dtype=np.uint8)
    assert _c_triality(base).tolist() == [0, 2, 3, 1]
    assert _c_triality(base, True).tolist() == [0, 3, 1, 2]
    assert (_c_triality(_c_triality(_c_triality(base))) == base).all()


@_requires_triality_native
def test_parity_klein4_triality_rejects_out_of_range():
    bad = np.array([0, 1, 4], dtype=np.uint8)
    n = bad.size
    inp = (ctypes.c_uint8 * n).from_buffer_copy(bad.tobytes())
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_klein4_triality_cycle(inp, n, 0, out)
    assert rc != _native.SRMECH_OK  # SRMECH_ERR_BAD_INPUT
