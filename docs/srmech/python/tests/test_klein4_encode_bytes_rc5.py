"""§60 / F864 byte/glyph-level Klein-4 encoder (0.9.0rc5).

The LM-agnostic byte-composed word encoder graduates from siona to srmech per
UPSTREAM §62: ``klein4_pos_key`` (position role-vector) + ``klein4_encode_bytes``
(position-bound per-byte bundle). Tests are numpy-free and assert the MORPHOLOGY
property — sub-word structure raises similarity above the Klein-4 chance level,
without the word-atomic English/whitespace privilege.
"""
import pytest

from srmech.amsc import hdc
from srmech.amsc.q import Q

D = 4096


def _sim(a, b):
    return hdc.klein4_similarity(hdc.klein4_encode_bytes(a, D),
                                 hdc.klein4_encode_bytes(b, D))


# ── morphology: shared sub-word structure ≫ chance ──

def test_morphology_restored():
    cat_cats = float(_sim(b"cat", b"cats"))      # shared 3-byte prefix
    cat_dog = float(_sim(b"cat", b"dog"))        # unrelated
    assert cat_cats > 0.5                         # F864: ~0.656
    assert cat_dog < 0.35                         # ~0.25 Klein-4 chance
    assert cat_cats > cat_dog + 0.2               # morphology, not chance


def test_shared_prefix_scales():
    # longer shared prefix → higher similarity
    assert float(_sim(b"walk", b"walked")) > float(_sim(b"walk", b"talked"))


def test_encode_similarity_is_Q():
    assert isinstance(_sim(b"cat", b"cats"), Q)
    assert isinstance(hdc.klein4_similarity(
        hdc.klein4_encode_bytes(b"x", 2000),
        hdc.klein4_encode_bytes(b"x", 2000)), Q)


# ── determinism + identity ──

def test_encode_deterministic_and_self_identity():
    a = hdc.klein4_encode_bytes(b"hello", D)
    b = hdc.klein4_encode_bytes(b"hello", D)
    assert bytes(a.buffer) == bytes(b.buffer)                  # deterministic
    assert hdc.klein4_similarity(a, b) == Q(1, 1)             # self == 1


def test_str_is_utf8_encoded():
    assert bytes(hdc.klein4_encode_bytes("café", D).buffer) == \
        bytes(hdc.klein4_encode_bytes("café".encode("utf-8"), D).buffer)


# ── internal position-key helper: deterministic, namespaced off the bytes ──

def test_pos_key_namespaced_off_bytes():
    # _klein4_pos_key(i) must not collide with byte_vec(i) for small i (seeds 0..255)
    from srmech.amsc.hdc import _klein4_pos_key
    for i in range(5):
        pk = _klein4_pos_key(2000, i)
        bv = hdc.klein4_random(2000, seed=i)
        assert bytes(pk.buffer) != bytes(bv.buffer)


def test_pos_key_deterministic():
    from srmech.amsc.hdc import _klein4_pos_key
    assert bytes(_klein4_pos_key(800, 3).buffer) == bytes(_klein4_pos_key(800, 3).buffer)


# ── error paths ──

def test_encode_rejects_bad_args():
    with pytest.raises(ValueError):
        hdc.klein4_encode_bytes(b"", D)            # empty
    with pytest.raises(ValueError):
        hdc.klein4_encode_bytes(b"a", 0)           # D <= 0
    with pytest.raises(TypeError):
        hdc.klein4_encode_bytes(12345, D)          # not bytes/str


def test_pos_key_rejects_bad_args():
    from srmech.amsc.hdc import _klein4_pos_key
    with pytest.raises(ValueError):
        _klein4_pos_key(0, 0)                       # D <= 0
    with pytest.raises(ValueError):
        _klein4_pos_key(8, -1)                      # pos < 0


# ── surface bookkeeping ──

def test_byte_encoder_public_and_counted():
    assert "klein4_encode_bytes" in hdc.__all__     # the graduating public op
    assert "klein4_pos_key" not in hdc.__all__      # position key is internal
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] >= 317
