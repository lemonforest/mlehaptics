"""§58 / F837 capacity-bounded chunk-set + max-resonance read (0.9.0rc4).

The LM-agnostic VSA cleanup-memory graduates from siona to srmech per UPSTREAM
§62: ``klein4_chunk_bundle`` (capacity-bounded chunk-set) + ``klein4_chunk_resolve``
(max-resonance read). Tests are numpy-free and assert EXACT ``Q`` scores
(stay-rational, F868) — the recall ranks on the integer match-count.
"""
import pytest

from srmech.amsc import hdc
from srmech.amsc.q import Q
from srmech.amsc._native import HAS_NATIVE


def _substrate(D=2000, n=5):
    vocab = {w: hdc.klein4_random(D, seed=100 + i)
             for i, w in enumerate(["cat", "dog", "sun", "moon", "tree"][:n])}
    keys = {f"k{i}": hdc.klein4_random(D, seed=900 + i) for i in range(n)}
    names = list(vocab)
    binds = [hdc.klein4_bind(keys[f"k{i}"], vocab[names[i]]) for i in range(n)]
    return vocab, keys, names, binds


# ── chunk_bundle: the capacity-bounded chunk-set ──

def test_chunk_bundle_splits_by_capacity():
    _, _, _, binds = _substrate(n=5)
    assert len(hdc.klein4_chunk_bundle(binds, 2)) == 3   # ceil(5/2)
    assert len(hdc.klein4_chunk_bundle(binds, 1)) == 5
    assert len(hdc.klein4_chunk_bundle(binds, 99)) == 1  # cap ≥ n → one bundle


def test_chunk_bundle_capacity_n_equals_plain_bundle():
    _, _, _, binds = _substrate(n=4)
    one = hdc.klein4_chunk_bundle(binds, 99)[0]
    plain = hdc.klein4_bundle(*binds)
    assert bytes(one.buffer) == bytes(plain.buffer)


def test_chunk_bundle_rejects_bad_args():
    _, _, _, binds = _substrate(n=3)
    with pytest.raises(ValueError):
        hdc.klein4_chunk_bundle([], 2)
    with pytest.raises(ValueError):
        hdc.klein4_chunk_bundle(binds, 0)


# ── chunk_resolve: the max-resonance read (EXACT Q, stay-rational) ──

def test_chunk_resolve_recovers_bound_value():
    vocab, keys, names, binds = _substrate(n=5)
    chunks = hdc.klein4_chunk_bundle(binds, 2)
    cands = list(vocab.values())
    for i, name in enumerate(names):
        scores = hdc.klein4_chunk_resolve(chunks, keys[f"k{i}"], cands)
        assert all(isinstance(s, Q) for s in scores)         # stay-rational
        best = max(range(len(scores)), key=lambda j: scores[j])
        assert names[best] == name                            # recovers the bind


def test_chunk_resolve_scores_are_exact_match_fraction():
    # one chunk == one bind: the score is EXACTLY match_count/D (a Q)
    vocab, keys, names, binds = _substrate(n=3)
    chunks = hdc.klein4_chunk_bundle(binds[:1], 1)            # single chunk = bind 0
    D = len(binds[0])
    recovered = hdc.klein4_bind(chunks[0], keys["k0"])        # unbind
    cand = vocab[names[0]]
    expect = hdc.klein4_similarity(recovered, cand)           # the exact Q
    got = hdc.klein4_chunk_resolve(chunks, keys["k0"], [cand])[0]
    assert isinstance(got, Q) and got == expect


def test_chunk_resolve_rejects_bad_args():
    vocab, keys, _, binds = _substrate(n=3)
    chunks = hdc.klein4_chunk_bundle(binds, 2)
    cands = list(vocab.values())
    with pytest.raises(ValueError):
        hdc.klein4_chunk_resolve([], keys["k0"], cands)       # no chunks
    with pytest.raises(ValueError):
        hdc.klein4_chunk_resolve(chunks, keys["k0"], [])      # no candidates
    with pytest.raises(ValueError):
        hdc.klein4_chunk_resolve(chunks, hdc.klein4_random(8, seed=1), cands)  # len ≠ D


# ── surface bookkeeping ──

def test_chunk_ops_public_and_counted():
    assert "klein4_chunk_bundle" in hdc.__all__
    assert "klein4_chunk_resolve" in hdc.__all__
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 316


@pytest.mark.skipif(not HAS_NATIVE, reason="native lib absent")
def test_chunk_resolve_native_matches_pure():
    from srmech.amsc.hdc import (
        _as_klein4_buf, _klein4_chunk_resolve_core, _klein4_chunk_resolve_native)
    vocab, keys, _, binds = _substrate(n=5)
    chunks = hdc.klein4_chunk_bundle(binds, 2)
    chunk_bufs = [_as_klein4_buf(c, "t") for c in chunks]
    cand_bufs = [_as_klein4_buf(c, "t") for c in vocab.values()]
    key_buf = _as_klein4_buf(keys["k2"], "t")
    D = len(key_buf)
    nat = _klein4_chunk_resolve_native(chunk_bufs, key_buf, cand_bufs, D)
    pure = _klein4_chunk_resolve_core(chunk_bufs, key_buf, cand_bufs)
    assert nat == pure
