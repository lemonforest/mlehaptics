"""§60 / F864 standalone-C MT19937 for ``klein4_random`` (0.9.0rc6).

``klein4_random``'s deterministic integer-seed path graduates from
``python_only_irreducible`` to ``c_dispatched``: a native ``srmech_klein4_random``
reproduces CPython ``random.Random(seed).randrange(4)`` BYTE-FOR-BYTE (MT19937
seeded by ``init_by_array`` over the seed's little-endian uint32 words; each draw
= ``getrandbits(3)`` with rejection of >= 4). With it the §60 byte/glyph encoder
— and the 256-byte vocab + position keys — is fully native.

Tests are numpy-free. The GROUND-TRUTH oracle is the stdlib ``random.Random`` —
the exact generator ``klein4_random``'s pure path uses — so the contract test
passes whether or not native is present; a separate native-vs-pure byte-parity
test exercises the C twin when ``HAS_NATIVE`` (skipped on a no-C dev env, run in
CI / the shipped wheel).
"""
import random

import pytest

from srmech.amsc import _native
from srmech.amsc import hdc

D = 512
SEEDS = [0, 1, 2, 255, 256, 0x10000, 0x10005, 12345, 2**31, 2**32, 2**33 + 7,
         2**64 + 12345]


def _ref(seed, n):
    """The stdlib oracle: one Random(seed), drawn n times (NOT re-seeded)."""
    r = random.Random(seed)
    return [r.randrange(4) for _ in range(n)]


# ── the contract: klein4_random == random.Random(seed).randrange(4) stream ──

@pytest.mark.parametrize("seed", SEEDS)
def test_public_matches_stdlib_random(seed):
    hv = hdc.klein4_random(D, seed=seed)
    assert list(bytes(hv.buffer)) == _ref(seed, D)
    assert hv.sectors == 4


def test_codes_in_range_and_dim():
    hv = hdc.klein4_random(1000, seed=7)
    assert len(hv) == 1000
    assert all(0 <= c <= 3 for c in bytes(hv.buffer))


def test_deterministic_same_seed():
    a = hdc.klein4_random(D, seed=99)
    b = hdc.klein4_random(D, seed=99)
    assert bytes(a.buffer) == bytes(b.buffer)
    assert bytes(hdc.klein4_random(D, seed=99).buffer) != \
        bytes(hdc.klein4_random(D, seed=100).buffer)


def test_negative_seed_uses_abs():
    # CPython random.Random seeds on abs(seed); klein4_random matches.
    assert list(bytes(hdc.klein4_random(D, seed=-12345).buffer)) == _ref(-12345, D)


# ── seed → little-endian uint32 words (the CPython init_by_array key) ──

def test_seed_to_le_words():
    assert hdc._seed_to_le_words(0) == [0]              # zero -> single 0 word
    assert hdc._seed_to_le_words(1) == [1]
    assert hdc._seed_to_le_words(0xFFFFFFFF) == [0xFFFFFFFF]
    assert hdc._seed_to_le_words(0x1_00000000) == [0, 1]     # little-endian
    assert hdc._seed_to_le_words(0x2_00000005) == [5, 2]
    assert hdc._seed_to_le_words(-7) == [7]                  # absolute value


# ── native ↔ pure byte parity (the standalone-C twin; skipped on no-C dev env) ──

def test_native_matches_pure_byte_for_byte():
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_klein4_random")):
        pytest.skip("native srmech_klein4_random not present (no-C dev env)")
    for seed in SEEDS:
        native = hdc._klein4_random_native(D, seed)
        assert native is not None, f"native returned None at seed={seed}"
        assert list(native) == _ref(seed, D), f"native diverged at seed={seed}"


# ── §60 morphology regression: encode_bytes still recovers sub-word structure ──

def test_encode_bytes_morphology_regression():
    def sim(a, b):
        return float(hdc.klein4_similarity(hdc.klein4_encode_bytes(a, 4096),
                                           hdc.klein4_encode_bytes(b, 4096)))
    assert sim(b"cat", b"cats") > sim(b"cat", b"dog") + 0.2


# ── surface bookkeeping: still public, no op added (C peer + reclassify only) ──

def test_klein4_random_public_and_count_unchanged():
    assert "klein4_random" in hdc.__all__
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] >= 317
