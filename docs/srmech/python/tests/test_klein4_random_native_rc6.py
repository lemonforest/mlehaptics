"""§60 / F864 standalone-C MT19937 for ``klein4_expand`` (0.9.0rc6).

``klein4_expand``'s deterministic integer-seed path graduates from
``python_only_debt`` to ``c_dispatched``: a native ``srmech_klein4_expand``
(named ``srmech_klein4_random`` until the rc290 regime split)
reproduces CPython ``random.Random(seed).randrange(4)`` BYTE-FOR-BYTE (MT19937
seeded by ``init_by_array`` over the seed's little-endian uint32 words; each draw
= ``getrandbits(3)`` with rejection of >= 4). With it the §60 byte/glyph encoder
— and the 256-byte vocab + position keys — is fully native.

Tests are numpy-free. The GROUND-TRUTH oracle is the stdlib ``random.Random`` —
the exact generator ``klein4_expand``'s pure path uses — so the contract test
passes whether or not native is present; a separate native-vs-pure byte-parity
test exercises the C twin when ``HAS_NATIVE`` (skipped on a no-C dev env, run in
CI / the shipped wheel).
"""
import random

import pytest

from srmech import _native
from srmech.math import hdc

D = 512
SEEDS = [0, 1, 2, 255, 256, 0x10000, 0x10005, 12345, 2**31, 2**32, 2**33 + 7,
         2**64 + 12345]


def _ref(seed, n):
    """The stdlib oracle: one Random(seed), drawn n times (NOT re-seeded)."""
    r = random.Random(seed)
    return [r.randrange(4) for _ in range(n)]


# ── the contract: klein4_expand == random.Random(seed).randrange(4) stream ──

@pytest.mark.parametrize("seed", SEEDS)
def test_public_matches_stdlib_random(seed):
    hv = hdc.klein4_expand(D, seed)
    assert list(bytes(hv.buffer)) == _ref(seed, D)
    assert hv.sectors == 4


def test_codes_in_range_and_dim():
    hv = hdc.klein4_expand(1000, 7)
    assert len(hv) == 1000
    assert all(0 <= c <= 3 for c in bytes(hv.buffer))


def test_deterministic_same_seed():
    a = hdc.klein4_expand(D, 99)
    b = hdc.klein4_expand(D, 99)
    assert bytes(a.buffer) == bytes(b.buffer)
    assert bytes(hdc.klein4_expand(D, 99).buffer) != \
        bytes(hdc.klein4_expand(D, 100).buffer)


def test_negative_seed_uses_abs():
    # CPython random.Random seeds on abs(seed); klein4_expand matches.
    assert list(bytes(hdc.klein4_expand(D, -12345).buffer)) == _ref(-12345, D)


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
    """rc292 repair — this test was DEAD from rc290 to rc291.

    rc290 renamed the op and its C twin (``srmech_klein4_random`` ->
    ``srmech_klein4_expand``, ``_klein4_random_native`` ->
    ``_klein4_expand_native``) but did not update this module. The guard
    below therefore asked for a symbol that no longer existed, so the test
    SKIPPED unconditionally — on CI and in the shipped wheel alike — and had
    it ever run, it would have raised ``AttributeError`` on the helper. Two
    rcs of native-vs-pure byte parity for the expand path were not actually
    covered by anything.

    The skip is now conditioned on ``HAS_NATIVE`` alone, and a missing symbol
    under native is an ASSERTION rather than a skip. A seam that stops
    observing has to fail loudly; silently skipping is how it hid for two rcs.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        pytest.skip("no native library (no-C dev env)")
    assert hasattr(_native.LIB, "srmech_klein4_expand"), (
        "native is present but srmech_klein4_expand is absent — a stale "
        "libsrmech, not a reason to skip"
    )
    for seed in SEEDS:
        native = hdc._klein4_expand_native(D, seed)
        assert native is not None, f"native returned None at seed={seed}"
        assert list(native) == _ref(seed, D), f"native diverged at seed={seed}"


# ── §60 morphology regression: encode_bytes still recovers sub-word structure ──

def test_encode_bytes_morphology_regression():
    def sim(a, b):
        return float(hdc.klein4_similarity(hdc.klein4_encode_bytes(a, 4096),
                                           hdc.klein4_encode_bytes(b, 4096)))
    assert sim(b"cat", b"cats") > sim(b"cat", b"dog") + 0.2


# ── surface bookkeeping: still public, no op added (C peer + reclassify only) ──

def test_klein4_expand_public_and_count_unchanged():
    assert "klein4_expand" in hdc.__all__
    # rc292: the STOCHASTIC sibling is gone; expand is the surviving mint.
    assert "klein4_random" not in hdc.__all__
    assert not hasattr(hdc, "klein4_random")
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] >= 317
