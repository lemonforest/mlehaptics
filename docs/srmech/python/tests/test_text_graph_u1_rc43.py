"""v0.7.5rc43 — the text→graph stage primitives (§17 U1; RBS-LM #855 R3 U1).

`tokenize` (Class B/G text-segmentation) and `cooccurrence_edges` (Class-L
precursor) are the only links the K1 presence-kernel build was missing between
raw `text` and the already-shipped `dense_laplacian`. With them, K1 is an
authorable composite end-to-end: `tokenize → cooccurrence_edges →
dense_laplacian → eigendecompose → …`. Both pure-Python, numpy-free.

Validates: the tokenizer contract (lowercase / min_len / stopwords / custom
pattern), the co-occurrence builder (vocab cap, window, integer weights, the
`(n, edges, weights)` shape `dense_laplacian` consumes), the full K1 round-trip
into the Laplacian eigvals, and that both ops are registered (ToolEntry + the
`describe()` total bumped 274 → 277).
"""
from __future__ import annotations

import pytest

from srmech.amsc import laplacian
from srmech.amsc.laplacian import tokenize, cooccurrence_edges


# ── tokenize — Class B/G text-segmentation ───────────────────────────────────

def test_tokenize_lowercases_and_splits_on_default_pattern():
    assert tokenize("The Cascade ROTATES at the end") == \
        ["the", "cascade", "rotates", "at", "the", "end"]


def test_tokenize_min_len_drops_short_tokens():
    # the default pattern already requires >=2 chars (a letter + >=1 more), so
    # single chars ("a", "I") never appear; min_len filters further on top of it.
    assert tokenize("a chain is I am ok", min_len=2) == ["chain", "is", "am", "ok"]
    assert tokenize("the cascade rotates", min_len=4) == ["cascade", "rotates"]  # "the"(3) dropped
    # a single-char-capable pattern + min_len=1 keeps 1-char tokens
    assert tokenize("a b cd", min_len=1, pattern=r"[A-Za-z0-9]+") == ["a", "b", "cd"]


def test_tokenize_stopwords_are_case_insensitive():
    out = tokenize("The cascade and THE chain", stopwords={"the", "and"})
    assert out == ["cascade", "chain"]


def test_tokenize_custom_pattern_is_group_safe():
    # a pattern WITH a capture group must still yield whole matches (finditer/group(0))
    assert tokenize("aa-bb cc", pattern=r"([a-z]+)") == ["aa", "bb", "cc"]


def test_tokenize_default_pattern_keeps_internal_hyphen_underscore():
    assert tokenize("ephemerides-spectral srmech_v0") == ["ephemerides-spectral", "srmech_v0"]


@pytest.mark.parametrize("bad", [123, None, b"bytes", ["already", "tokens"]])
def test_tokenize_rejects_non_str(bad):
    with pytest.raises(TypeError):
        tokenize(bad)


@pytest.mark.parametrize("bad", [0, -1, 1.5, "2"])
def test_tokenize_rejects_bad_min_len(bad):
    with pytest.raises((ValueError, TypeError)):
        tokenize("text", min_len=bad)


# ── cooccurrence_edges — Class-L precursor ───────────────────────────────────

def test_cooccurrence_returns_n_edges_weights_for_dense_laplacian():
    toks = ["a", "b", "a", "c"]
    n, edges, weights = cooccurrence_edges(toks, window=1, vocab_size=10)
    assert n == 3                              # 3 distinct tokens → 3 nodes
    assert len(edges) == len(weights)
    # every edge is an ordered (u < v) int pair within range
    for (u, v) in edges:
        assert isinstance(u, int) and isinstance(v, int) and 0 <= u < v < n
    # weights are exact integer counts (floats are for the FPU lift; none here)
    assert all(isinstance(w, int) and not isinstance(w, bool) for w in weights)


def test_cooccurrence_window_counts_repeated_pairs():
    # "a b a b a" with window 1: pairs (a,b) occur 4× as adjacent neighbours
    n, edges, weights = cooccurrence_edges(["a", "b", "a", "b", "a"], window=1, vocab_size=10)
    assert n == 2 and edges == [(0, 1)] and weights == [4]


def test_cooccurrence_vocab_cap_truncates_by_frequency():
    toks = ["x"] * 5 + ["y"] * 3 + ["z"] * 1     # x,y kept at vocab_size=2; z dropped
    n, edges, weights = cooccurrence_edges(toks, window=2, vocab_size=2)
    assert n == 2


def test_cooccurrence_empty_and_singleton_are_safe():
    assert cooccurrence_edges([], window=2, vocab_size=5) == (0, [], [])
    assert cooccurrence_edges(["solo"], window=2, vocab_size=5) == (1, [], [])


@pytest.mark.parametrize("window,vocab", [(0, 5), (-1, 5), (5, 0), (5, -1), (1.5, 5)])
def test_cooccurrence_rejects_bad_params(window, vocab):
    with pytest.raises((ValueError, TypeError)):
        cooccurrence_edges(["a", "b"], window=window, vocab_size=vocab)


# ── the K1 chain front: tokenize → cooccurrence_edges → dense_laplacian ───────

def test_k1_round_trip_into_laplacian_eigvals():
    text = ("The cascade rotates at the end. A cascade is a chain; "
            "the chain rotates, the chain holds. Cascade end.")
    toks = tokenize(text, stopwords={"the", "a", "is", "at", "an"}, min_len=2)
    n, edges, weights = cooccurrence_edges(toks, window=3, vocab_size=64)
    L = laplacian.dense_laplacian(n, edges, weights)      # consumes the triple directly
    eigs = list(laplacian.jacobi_eigvals(L))
    assert len(eigs) == n
    # a graph Laplacian is PSD with a near-zero smallest eigenvalue (the constant mode)
    assert abs(eigs[0]) < 1e-9
    assert all(e >= -1e-9 for e in eigs)


def test_ops_registered_in_all_and_laplacian_ops():
    for name in ("tokenize", "cooccurrence_edges", "DEFAULT_TOKEN_PATTERN"):
        assert name in laplacian.__all__
    assert "tokenize" in laplacian.LAPLACIAN_OPS
    assert "cooccurrence_edges" in laplacian.LAPLACIAN_OPS


def test_tool_entries_registered_and_total_bumped():
    from srmech import introspect
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.tokenize" in names
    assert "srmech.amsc.laplacian.cooccurrence_edges" in names
    assert introspect.describe()["tools"]["total"] == 277
