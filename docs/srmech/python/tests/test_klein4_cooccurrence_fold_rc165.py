"""rc165 — the §50 native Klein-4 co-occurrence fold matches the pure-Python fold.

``srmech.amsc.hdc.cooccurrence_fold`` gained a native fast-path (the corpus-linear
windowed accumulation in one C call, ``srmech_klein4_cooccurrence_fold``). This
proves the native fold is bit-identical to the pure-Python loop it replaces — the
resolved per-token bundles match exactly — so the holographic store built at
corpus scale (§50.1 loopshelf / tome-leaves) is the SAME store, just faster.

numpy-free (the hdc module is numpy-free; the test must be too).
"""

import pytest

from srmech.amsc import _native, hdc


def _bundles_identical(a, b):
    """Every token's resolved bundle is bit-identical (klein4_similarity == 1.0)."""
    if set(a["vocab"]) != set(b["vocab"]):
        return False
    if set(a["bundles"]) != set(b["bundles"]):
        return False
    for tok, hv_a in a["bundles"].items():
        if hdc.klein4_similarity(hv_a, b["bundles"][tok]) != 1.0:
            return False
    return True


def test_native_cooccurrence_fold_matches_pure(monkeypatch):
    """The native fold == the pure-Python fold (skip when no native lib)."""
    if not _native.has_native_klein4_fold():
        pytest.skip("no native klein4 co-occurrence fold (pure-Python-only lib)")

    tokens = ("the", "cat", "sat", "on", "the", "mat", "cat", "sat", "the", "mat")
    kw = dict(window=2, dim=96, seed=7)

    native = hdc.cooccurrence_fold(tokens, **kw)        # native fast-path
    monkeypatch.setattr(_native, "has_native_klein4_fold", lambda: False)
    pure = hdc.cooccurrence_fold(tokens, **kw)          # forced pure-Python

    # vocab order + codes are built identically (deterministic per-token seed)
    assert native["vocab"] == pure["vocab"]
    assert native["n_tokens"] == pure["n_tokens"] == len(tokens)
    for tok in native["vocab"]:
        assert hdc.klein4_similarity(native["codes"][tok], pure["codes"][tok]) == 1.0
    # the resolved holographic bundles are bit-identical
    assert _bundles_identical(native, pure)


def test_native_fold_window_and_dim_sweep(monkeypatch):
    """Parity holds across a few (window, dim) shapes + a single-token edge case."""
    if not _native.has_native_klein4_fold():
        pytest.skip("no native klein4 co-occurrence fold")

    streams = [
        ("a", "b", "a", "c", "b", "a", "d", "c"),
        tuple("mississippi"),
        ("solo",),                         # n == 1 -> empty bundles (no native path)
    ]
    for toks in streams:
        for window in (1, 3):
            for dim in (8, 128):
                kw = dict(window=window, dim=dim, seed=3)
                monkeypatch.setattr(_native, "has_native_klein4_fold",
                                    lambda: True, raising=False)
                native = hdc.cooccurrence_fold(toks, **kw)
                monkeypatch.setattr(_native, "has_native_klein4_fold",
                                    lambda: False)
                pure = hdc.cooccurrence_fold(toks, **kw)
                assert native["vocab"] == pure["vocab"]
                assert _bundles_identical(native, pure), (
                    f"mismatch for toks={toks} window={window} dim={dim}")
