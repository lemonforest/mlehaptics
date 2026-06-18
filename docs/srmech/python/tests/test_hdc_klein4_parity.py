"""Klein-4 {0,1,2,3} Class M variant — algebraic properties + C/Python parity.

Klein-4 (v0.4.3rc2) is rank-2 abelian Class M over (F₂)² = Z₂×Z₂: uint8
hypervectors over {0,1,2,3}, bind = component-wise XOR (self-inverse, abelian,
identity 0), bundle = per-bit majority (ties → 0). The four states map to the
four (γ₅, iω₇) chirality sectors. See ``srmech.amsc.hdc.klein4_*`` +
UPSTREAM_NOTES §4.

Two tiers: numpy-FREE property tests (always run) + C↔Python bit-exact parity
(native only; built in the cibuildwheel matrix).

#564 (numpy out the door): the klein4 ops return ``HV`` / ``list`` numpy-free
(``HV.__eq__`` against an HV/list, ``.tolist()``, ``.buffer``). The reference
property tests use ``random.Random`` int lists in {0,1,2,3} + hand-computed
expected XOR-sector results — numpy is never imported, so the file PASSES with
numpy absent (the substrate-native discipline). The native-parity tier feeds
the C symbols a stdlib ``bytes`` buffer and compares the returned ``bytes``
to ``HV.tobytes()`` — no ndarray anywhere.
"""

import ctypes
import random

import pytest

from srmech.amsc import _native
from srmech.amsc import hdc
from srmech.amsc.q import Q


_K4_NATIVE = _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_klein4_bind")
_requires_native = pytest.mark.skipif(
    not _K4_NATIVE,
    reason="native klein-4 surface not present (pure-Python or pre-klein4 lib)",
)


def _rand_k4(seed, D=128):
    """A numpy-free random Klein-4 vector: a ``list[int]`` in {0,1,2,3}."""
    r = random.Random(seed)
    return [r.randrange(4) for _ in range(D)]


# --------------------------------------------------------------------------
# Algebraic properties (numpy-FREE reference) — always run
# --------------------------------------------------------------------------

def test_klein4_group_axioms():
    a, b, c = (_rand_k4(s) for s in (1, 2, 3))
    assert set(a) <= {0, 1, 2, 3}
    zero = [0] * len(a)
    # identity 0, self-inverse, commutative, associative
    assert hdc.klein4_bind(a, zero) == a
    assert hdc.klein4_bind(a, hdc.klein4_bind(a, b)) == b
    assert hdc.klein4_bind(a, b) == hdc.klein4_bind(b, a)
    assert (hdc.klein4_bind(hdc.klein4_bind(a, b), c)
            == hdc.klein4_bind(a, hdc.klein4_bind(b, c)))
    # every element is its own inverse (Klein-four group property)
    assert hdc.klein4_bind(a, a).tolist() == [0] * len(a)


def test_klein4_unbind():
    a = _rand_k4(2, D=256)
    b = _rand_k4(12, D=256)
    assert hdc.klein4_unbind(hdc.klein4_bind(a, b), a) == b


def test_klein4_chirality_flips():
    a = _rand_k4(3, D=64)
    # γ₅ = XOR 2, iω₇ = XOR 1, CPT = XOR 3 = both flips composed
    assert (hdc.klein4_chirality_flip_omega7(hdc.klein4_chirality_flip_gamma5(a))
            == hdc.klein4_cpt_mirror(a))
    # each flip is an involution
    for flip in (hdc.klein4_chirality_flip_gamma5,
                 hdc.klein4_chirality_flip_omega7,
                 hdc.klein4_cpt_mirror):
        assert flip(flip(a)) == a
    # explicit sector map (hand-computed XOR)
    base = [0, 1, 2, 3]
    assert hdc.klein4_chirality_flip_gamma5(base).tolist() == [2, 3, 0, 1]
    assert hdc.klein4_chirality_flip_omega7(base).tolist() == [1, 0, 3, 2]
    assert hdc.klein4_cpt_mirror(base).tolist() == [3, 2, 1, 0]


def test_klein4_bundle_per_bit_majority():
    v1 = [0, 3, 1]
    v2 = [0, 3, 2]
    v3 = [1, 0, 3]
    # pos0: bit0 {0,0,1}->0, bit1 {0,0,0}->0 => 0
    # pos1: states 3,3,0: bit0 {1,1,0}->1, bit1 {1,1,0}->1 => 3
    # pos2: states 1,2,3: bit0 {1,0,1}->1, bit1 {0,1,1}->1 => 3
    assert hdc.klein4_bundle(v1, v2, v3).tolist() == [0, 3, 3]
    # even count, exact tie on a bit → 0
    assert hdc.klein4_bundle([1], [2]).tolist() == [0]


def test_klein4_similarity_and_sector_count():
    a = _rand_k4(4, D=200)
    assert hdc.klein4_similarity(a, a) == 1.0
    x = [0, 1, 2, 3]
    y = [0, 1, 3, 3]
    # v0.9.0 (F868): klein4_similarity returns the EXACT Q — assert the rational
    # (3 matches / 4), and the raw integer count via the new klein4_match_count.
    assert hdc.klein4_similarity(x, y) == Q(3, 4)
    assert hdc.klein4_match_count(x, y) == 3
    assert hdc.klein4_sector_count([0, 0, 1, 2, 2, 2, 3]) == [2, 1, 3, 1]


def test_klein4_validation():
    with pytest.raises(ValueError):
        hdc.klein4_bind([4, 0], [1, 1])
    with pytest.raises(ValueError):
        hdc.klein4_bundle()


# --------------------------------------------------------------------------
# C ↔ Python bit-exact parity (native only) — numpy-free buffers
# --------------------------------------------------------------------------

def _to_bytes(v):
    """The op output as raw ``bytes`` (HV.tobytes / list → bytes), numpy-free."""
    if hasattr(v, "tobytes"):
        return v.tobytes()
    return bytes(v)


def _c_bind(a, b):
    n = len(a)
    ab = (ctypes.c_uint8 * n)(*a)
    bb = (ctypes.c_uint8 * n)(*b)
    out = (ctypes.c_uint8 * n)()
    assert _native.LIB.srmech_klein4_bind(ab, bb, n, out) == _native.SRMECH_OK
    return bytes(out)


def _c_bundle(vecs):
    n = len(vecs[0]); nv = len(vecs)
    bufs = [(ctypes.c_uint8 * n)(*v) for v in vecs]
    ptr = (ctypes.POINTER(ctypes.c_uint8) * nv)(
        *(ctypes.cast(b, ctypes.POINTER(ctypes.c_uint8)) for b in bufs)
    )
    out = (ctypes.c_uint8 * n)()
    assert _native.LIB.srmech_klein4_bundle(ptr, nv, n, out) == _native.SRMECH_OK
    return bytes(out)


def _c_similarity(a, b):
    n = len(a)
    ab = (ctypes.c_uint8 * n)(*a)
    bb = (ctypes.c_uint8 * n)(*b)
    out = ctypes.c_double(0.0)
    assert _native.LIB.srmech_klein4_similarity(ab, bb, n, ctypes.byref(out)) == _native.SRMECH_OK
    return out.value


@_requires_native
def test_parity_klein4_bind():
    for s in range(20):
        a = _rand_k4(100 + s, D=257); b = _rand_k4(200 + s, D=257)
        assert _c_bind(a, b) == _to_bytes(hdc.klein4_bind(a, b))


@_requires_native
def test_parity_klein4_bundle():
    for k, nv in enumerate((1, 2, 3, 8, 33)):
        vecs = [_rand_k4(300 + k * 50 + i, D=129) for i in range(nv)]
        assert _c_bundle(vecs) == _to_bytes(hdc.klein4_bundle(*vecs))


@_requires_native
def test_parity_klein4_similarity():
    for s in range(20):
        a = _rand_k4(500 + s, D=200); b = _rand_k4(600 + s, D=200)
        # The C kernel returns a double (the display-boundary collapse); compare
        # it to the Q's float view (F868) — float(Q) is the same boundary cast.
        assert _c_similarity(a, b) == pytest.approx(float(hdc.klein4_similarity(a, b)))


# --------------------------------------------------------------------------
# v0.6.0rc13 — the sectors= / parallel= / mode= flag (§11.3 forward-ask).
# Two modes: chunk (data-parallel, BIT-IDENTICAL) + chirality (F233 4-sector,
# klein4-native XOR-flips). Default-ON at >=4 cores; all defaults are
# value-preserving. Pure-Python orchestration (co-equal parity: it does NOT
# route through the C peer). Numpy-free — HV.__eq__ / .tolist() comparisons.
# --------------------------------------------------------------------------

def _k4(seed, D=257):
    return _rand_k4(seed, D=D)


def test_klein4_sectors_value_preserving_across_modes():
    """bind/bundle/similarity are value-preserving under BOTH default modes."""
    a, b = _k4(20), _k4(21)
    vs = [_k4(30 + i) for i in range(5)]
    bind1 = hdc.klein4_bind(a, b, sectors=1)
    bund1 = hdc.klein4_bundle(*vs, sectors=1)
    sim1 = hdc.klein4_similarity(a, b, sectors=1)
    # bind: chunk + chirality both == serial (XOR collapses all 4 sectors).
    assert hdc.klein4_bind(a, b, sectors=4, mode="chunk") == bind1
    assert hdc.klein4_bind(a, b, sectors=4, mode="chirality") == bind1
    # bundle: chunk bit-identical; chirality runs + preserves shape.
    assert hdc.klein4_bundle(*vs, sectors=4, mode="chunk") == bund1
    assert len(hdc.klein4_bundle(*vs, sectors=4, mode="chirality")) == len(bund1)
    # similarity: chunk + chirality(sector-0) both EXACTLY == serial float.
    assert hdc.klein4_similarity(a, b, sectors=4, mode="chunk") == sim1
    assert hdc.klein4_similarity(a, b, sectors=4, mode="chirality") == sim1


def test_klein4_sectors_chunk_partitions_all_sector_counts():
    """Chunk mode is bit-identical for every lane count 1..4 (and odd D)."""
    a, b = _k4(40, D=130), _k4(41, D=130)
    serial = hdc.klein4_bind(a, b, sectors=1)
    for n in (1, 2, 3, 4):
        assert hdc.klein4_bind(a, b, sectors=n, mode="chunk") == serial


def test_klein4_parallel_alias_and_default_on():
    """parallel=True→4, parallel=False→1; the default (None) is value-preserving
    regardless of the machine's core count."""
    a, b = _k4(50), _k4(51)
    serial = hdc.klein4_bind(a, b, sectors=1)
    assert hdc.klein4_bind(a, b, parallel=True) == serial
    assert hdc.klein4_bind(a, b, parallel=False) == serial
    assert hdc.klein4_bind(a, b) == serial  # default-on path
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
    assert hdc.klein4_unbind(c, a) == b


# --------------------------------------------------------------------------
# v0.6.0rc18 — the co-equal C peer srmech_klein4_triality_cycle (the A-arc's
# silicon tier). Differential C-vs-Python on the order-3 S3 = Aut(V4) relabel,
# both directions. Guarded by its OWN symbol hasattr — a klein4-capable but
# pre-rc18 lib (rc13-rc17) has bind but not triality_cycle, so the parity
# test SKIPS there and runs in CI where the lib is freshly built.
# Numpy-free: bytes buffers in / bytes out, compared to HV.tobytes().
# --------------------------------------------------------------------------

_K4_TRIALITY_NATIVE = _K4_NATIVE and hasattr(
    _native.LIB, "srmech_klein4_triality_cycle"
)
_requires_triality_native = pytest.mark.skipif(
    not _K4_TRIALITY_NATIVE,
    reason="native srmech_klein4_triality_cycle absent (pure-Python or pre-rc18 lib)",
)


def _c_triality(arr, inverse=False):
    n = len(arr)
    inp = (ctypes.c_uint8 * n)(*arr)
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_klein4_triality_cycle(
        inp, n, 1 if inverse else 0, out
    )
    assert rc == _native.SRMECH_OK
    return bytes(out)


@_requires_triality_native
def test_parity_klein4_triality_cycle():
    for s in range(20):
        a = _rand_k4(700 + s, D=257)
        assert _c_triality(a, False) == _to_bytes(hdc.klein4_triality_cycle(a))
        assert (_c_triality(a, True)
                == _to_bytes(hdc.klein4_triality_cycle(a, inverse=True)))
    # explicit maps + order-3 identity, computed in C
    base = [0, 1, 2, 3]
    assert list(_c_triality(base)) == [0, 2, 3, 1]
    assert list(_c_triality(base, True)) == [0, 3, 1, 2]
    assert _c_triality(list(_c_triality(list(_c_triality(base))))) == bytes(base)


@_requires_triality_native
def test_parity_klein4_triality_rejects_out_of_range():
    bad = [0, 1, 4]
    n = len(bad)
    inp = (ctypes.c_uint8 * n)(*bad)
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_klein4_triality_cycle(inp, n, 0, out)
    assert rc != _native.SRMECH_OK  # SRMECH_ERR_BAD_INPUT
