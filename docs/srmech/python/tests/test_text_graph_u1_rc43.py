"""v0.7.5rc50 — text→graph stage primitives, §40 acceptance fix (supersedes rc43).

The rc43 `tokenize` / `cooccurrence_edges` (shipped in `srmech.amsc.laplacian`)
were SHIPPED but FAILED the RBS-LM §40 acceptance bar **3/3** (F722). rc50 moves
them to a dedicated ingestion module `srmech.amsc.text` (laplacian stays purely
spectral) and fixes all three:

1. **Unicode (F698)** — keep runs of Unicode letter|mark codepoints (café /
   Москва / naïve / 日本語 survive), casefold; NOT an ASCII ``\\w+`` (which gave
   ``['caf','na','ve']``).
2. **No silent vocab cap (F708)** — the full ranked vocabulary by default; a
   top-K cap is an explicit, logged caller opt-in (``vocab_size=``), never a
   silent ``vocab_size=1000`` default.
3. **Document-boundary window reset** — co-occurrence never crosses a document
   boundary (``docs`` is a sequence of token-sequences; a flat list is one doc).

Validates the corrected contract, the three acceptance criteria explicitly, the
full K1 round-trip into the Laplacian eigvals, and that both ops are registered
at the new ``srmech.amsc.text.*`` names (ToolEntry + ``describe()`` total = 282 after the rc51 dense_outer additions; the
relocation itself is count-neutral).
"""
from __future__ import annotations

import logging

import pytest

from srmech.amsc import laplacian, text
from srmech.amsc.text import DEFAULT_STOPLIST, cooccurrence_edges, tokenize


# ── tokenize — Class B/G Unicode text-segmentation ───────────────────────────

def test_tokenize_casefolds_and_splits():
    assert tokenize("The Cascade ROTATES", stoplist=None) == \
        ["the", "cascade", "rotates"]


def test_tokenize_unicode_keeps_accents_cyrillic_cjk():
    # §40 #1 / F698: the rc43 ASCII tokenizer gave ['caf','na','ve'] — every
    # accented / non-Latin token truncated or dropped. The fix keeps them whole.
    out = tokenize("café Москва naïve 日本語", stoplist=None)
    assert out == ["café".casefold(), "Москва".casefold(), "naïve".casefold(),
                   "日本語"]


def test_tokenize_drops_short_and_keeps_internal_apostrophe():
    assert tokenize("a I don't go", stoplist=None) == ["don't", "go"]  # 'a','i' < 2 dropped


def test_tokenize_default_stoplist_drops_function_words():
    # default stoplist = DEFAULT_STOPLIST (function words carry no association mass)
    assert tokenize("the cascade and the chain") == ["cascade", "chain"]
    assert "the" in DEFAULT_STOPLIST and "throughout" in DEFAULT_STOPLIST  # F714 preposition


def test_tokenize_custom_stoplist_extends():
    out = tokenize("cascade chain rotates", stoplist={"chain"})
    assert out == ["cascade", "rotates"]


def test_tokenize_nfc_normalises_by_default():
    # decomposed 'e' + combining acute → NFC precomposed 'é' (one token, canonical)
    assert tokenize("café", stoplist=None) == ["café"]


@pytest.mark.parametrize("bad", [123, None, b"bytes", ["already", "tokens"]])
def test_tokenize_rejects_non_str(bad):
    with pytest.raises(TypeError):
        tokenize(bad)


# ── cooccurrence_edges — Class-L precursor ───────────────────────────────────

def test_cooccurrence_returns_n_edges_weights_for_dense_laplacian():
    n, edges, weights = cooccurrence_edges(["a", "b", "a", "c"], window=1)
    assert n == 3
    assert len(edges) == len(weights)
    for (u, v) in edges:
        assert isinstance(u, int) and isinstance(v, int) and 0 <= u < v < n
    assert all(isinstance(w, int) and not isinstance(w, bool) for w in weights)


def test_cooccurrence_window_counts_repeated_pairs():
    n, edges, weights = cooccurrence_edges(["a", "b", "a", "b", "a"], window=1)
    assert n == 2 and edges == [(0, 1)] and weights == [4]


# ── §40 #2 — no silent vocab cap (F708) ──────────────────────────────────────

def test_cooccurrence_no_silent_vocab_cap_by_default():
    words = [f"w{i}" for i in range(1500)]
    n, _, _ = cooccurrence_edges(words)            # default: keep ALL (no cap)
    assert n == 1500


def test_cooccurrence_cap_is_explicit_opt_in_and_logged(caplog):
    words = [f"w{i}" for i in range(1500)]
    with caplog.at_level(logging.INFO, logger="srmech.amsc.text"):
        n, _, _ = cooccurrence_edges(words, vocab_size=1000)
    assert n == 1000
    assert any("dropped" in r.message for r in caplog.records)  # the drop is LOGGED


def test_cooccurrence_explicit_vocab_is_used_verbatim():
    n, edges, _ = cooccurrence_edges([["b", "a", "b"]], window=2, vocab=["b", "a"])
    assert n == 2                                   # caller's vocab order → b=0, a=1
    assert edges == [(0, 1)]


# ── §40 #3 — document-boundary window reset ──────────────────────────────────

def test_cooccurrence_window_resets_at_document_boundaries():
    # two docs: a wide window must NOT bridge the b↔c boundary
    n2, e2, _ = cooccurrence_edges([["a", "b"], ["c", "d"]], window=5)
    assert e2 == [(0, 1), (2, 3)]                   # no cross-doc (1,2) edge
    # the SAME tokens as one document DO produce the bridging edges
    n1, e1, _ = cooccurrence_edges([["a", "b", "c", "d"]], window=5)
    assert (1, 2) in e1 and (1, 2) not in e2


def test_cooccurrence_flat_list_is_one_document():
    # a flat Sequence[str] is treated as a single document (back-compat path)
    n, edges, _ = cooccurrence_edges(["a", "b", "c"], window=5)
    assert n == 3 and (0, 2) in edges               # one doc → a–c co-occur


def test_cooccurrence_empty_and_singleton_are_safe():
    assert cooccurrence_edges([], window=2) == (0, [], [])
    assert cooccurrence_edges(["solo"], window=2) == (1, [], [])


def test_cooccurrence_rejects_raw_str():
    with pytest.raises(TypeError):
        cooccurrence_edges("not tokenized", window=2)


@pytest.mark.parametrize("window,vsize", [(0, None), (-1, None), (1.5, None),
                                          (5, 0), (5, -1), (5, 1.5)])
def test_cooccurrence_rejects_bad_params(window, vsize):
    with pytest.raises((ValueError, TypeError)):
        cooccurrence_edges(["a", "b"], window=window, vocab_size=vsize)


# ── the K1 chain front: tokenize → cooccurrence_edges → dense_laplacian ───────

def test_k1_round_trip_into_laplacian_eigvals():
    docs = [
        tokenize("The cascade rotates at the end. A cascade is a chain."),
        tokenize("The chain rotates, the chain holds. Cascade end."),
    ]
    n, edges, weights = cooccurrence_edges(docs, window=3)
    L = laplacian.dense_laplacian(n, edges, weights)
    eigs = list(laplacian.jacobi_eigvals(L))
    assert len(eigs) == n
    assert abs(eigs[0]) < 1e-9                       # PSD, near-zero constant mode
    assert all(e >= -1e-9 for e in eigs)


# ── registration: relocated to srmech.amsc.text (count 282 incl. rc51 dense_outer) ──

def test_ops_in_text_all_and_gone_from_laplacian():
    assert "tokenize" in text.__all__ and "cooccurrence_edges" in text.__all__
    assert "DEFAULT_STOPLIST" in text.__all__
    # laplacian is purely spectral again — the text ops are NOT there
    assert "tokenize" not in laplacian.__all__
    assert "cooccurrence_edges" not in laplacian.__all__


def test_tool_entries_relocated_and_total_unchanged():
    from srmech import introspect
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.text.tokenize" in names
    assert "srmech.amsc.text.cooccurrence_edges" in names
    assert "srmech.amsc.laplacian.tokenize" not in names      # relocated, not duplicated
    assert introspect.describe()["tools"]["total"] == 292
