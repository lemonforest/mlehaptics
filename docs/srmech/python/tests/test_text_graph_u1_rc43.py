"""v0.9.0rc287 — text→graph stage primitives (supersedes the rc43/rc50 line).

The rc43 ``tokenize`` / ``cooccurrence_edges`` (shipped in
``srmech.math.laplacian``) FAILED the RBS-LM §40 acceptance bar 3/3 (F722).
rc50 moved them to a dedicated ingestion module ``srmech.math.text`` and fixed
all three. **rc287 replaced the unit itself**: the front door emits UAX #29
grapheme clusters, not words.

WHY THESE TESTS CHANGED (and were not deleted)
----------------------------------------------
Most of the assertions in the rc50 version of this file passed *because of*
word-segmentation assumptions that rc287 found to be wrong, so they have been
rewritten to state the corrected claim rather than dropped:

* ``test_tokenize_casefolds_and_splits`` — casefold at the front door is what
  broke Turkish (İ/I/ı) and could not repair Greek uppercase accent loss. Now
  asserts that case is PRESERVED and is a downstream concern.
* ``test_tokenize_drops_short_and_keeps_internal_apostrophe`` — this test was
  pinning TWO bugs as if they were features: the ``_MIN_LEN = 2`` floor deleted
  single-codepoint CJK content words, and the U+2019 handling deleted the
  Hawaiian okina outright. Now asserts both survive.
* ``test_tokenize_default_stoplist_drops_function_words`` — F1257 found the
  operator layer IS the conserved core (94/94 tokens entering it were stoplist
  members), so the default discarded exactly the layer the science found
  load-bearing. Now asserts function words are KEPT.
* ``test_tokenize_unicode_keeps_accents_cyrillic_cjk`` — kept in spirit; the
  §40 #1 / F698 claim (nothing gets truncated) is stronger at glyph level, and
  the CJK half now shows the run splitting rather than surviving "whole".

What is unchanged and still guarded: no silent vocab cap (F708), the
document-boundary window reset, and the full K1 round trip into the Laplacian.
"""
from __future__ import annotations

import logging

import pytest

from srmech.math import laplacian, text
from srmech.math.text import cooccurrence_edges, glyph_stream


# ── glyph_stream — Class B/G Unicode text-segmentation ──────────────────────

def test_glyph_stream_preserves_case():
    """Was ``test_tokenize_casefolds_and_splits``.

    Front-door ``casefold`` is what split Turkish vocabularies (İ folds to TWO
    codepoints; I folds onto dotless ı's identity) and it could never repair
    Greek uppercase accent loss. Case folding is a per-locale decision and now
    lives downstream, so the stream preserves what it was given.
    """
    assert glyph_stream("The Cascade ROTATES") == list("The Cascade ROTATES")
    assert glyph_stream("Cat") != glyph_stream("cat")


def test_glyph_stream_unicode_keeps_accents_cyrillic_and_splits_cjk():
    """§40 #1 / F698, restated at glyph level.

    The rc43 ASCII tokenizer gave ['caf','na','ve'] — accented and non-Latin
    text truncated or dropped. Nothing is truncated now. The CJK half changes
    shape deliberately: 日本語 is no longer ONE token but three glyphs, which
    is the whole point (as one token it was a vocabulary singleton).
    """
    assert glyph_stream("café") == ["c", "a", "f", "é"]
    assert glyph_stream("naïve") == ["n", "a", "ï", "v", "e"]
    assert glyph_stream("Москва") == list("Москва")
    assert glyph_stream("日本語") == ["日", "本", "語"]


def test_short_tokens_and_okina_are_no_longer_deleted():
    """Was ``test_tokenize_drops_short_and_keeps_internal_apostrophe``.

    That test pinned two BUGS as if they were the contract:

    * ``_MIN_LEN = 2`` — ``tokenize('中 国')`` returned ``[]``, deleting both
      single-codepoint CJK content words. There is no length floor now.
    * ``_APOS`` contained U+2019, which was mapped to ASCII "'" and then
      stripped word-initially, so ``'’okina'`` returned ``['okina']`` — the
      Hawaiian okina DELETED. Both okina encodings survive now.
    """
    assert glyph_stream("中 国") == ["中", " ", "国"]
    assert glyph_stream("a I don't go") == list("a I don't go")
    assert glyph_stream("’okina")[0] == "’"          # U+2019 — was deleted
    assert glyph_stream("ʻokina")[0] == "ʻ"          # U+02BB


def test_function_words_are_kept_not_discarded():
    """Was ``test_tokenize_default_stoplist_drops_function_words``.

    The 146-word stoplist was English and was the default for EVERY language,
    silently removing any token colliding with an English function word
    (Turkish ``o``/``bu``, Dutch ``over``). Worse, F1257 found the operator
    layer IS the conserved core — 94/94 tokens entering it were stoplist
    members — so the default discarded precisely the load-bearing layer.
    There is no stoplist at the front door now.
    """
    out = glyph_stream("the cascade and the chain")
    assert "".join(out) == "the cascade and the chain"
    assert out[:3] == ["t", "h", "e"]


def test_glyph_stream_nfc_normalises_by_default():
    """Unchanged in intent: decomposed 'e' + combining acute → precomposed é."""
    assert glyph_stream("cafe\u0301") == ["c", "a", "f", "é"]
    # ...and with normalisation off the pair is still ONE cluster (GB9).
    assert glyph_stream("e\u0301", unicode_normalize=False) == ["e\u0301"]


@pytest.mark.parametrize("bad", [123, None, b"bytes", ["already", "tokens"]])
def test_glyph_stream_rejects_non_str(bad):
    with pytest.raises(TypeError):
        glyph_stream(bad)


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
    with caplog.at_level(logging.INFO, logger="srmech.math.text"):
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


# ── the K1 chain front: glyph_stream → cooccurrence_edges → dense_laplacian ──────

def test_k1_round_trip_into_laplacian_eigvals():
    docs = [
        glyph_stream("The cascade rotates at the end. A cascade is a chain."),
        glyph_stream("The chain rotates, the chain holds. Cascade end."),
    ]
    # NB window is in GLYPHS now — window=3 spans ~3 characters, well under one
    # word. Window semantics need re-deriving per corpus, not rescaling (F-D).
    n, edges, weights = cooccurrence_edges(docs, window=3)
    L = laplacian.dense_laplacian(n, edges, weights)
    eigs = list(laplacian.jacobi_eigvals(L))
    assert len(eigs) == n
    assert abs(eigs[0]) < 1e-9                       # PSD, near-zero constant mode
    assert all(e >= -1e-9 for e in eigs)


# ── registration: relocated to srmech.math.text (count 282 incl. rc51 dense_outer) ──

def test_ops_in_text_all_and_gone_from_laplacian():
    assert "glyph_stream" in text.__all__
    assert "cooccurrence_edges" in text.__all__
    # rc287 removed the word front door outright — no shim, no legacy mode.
    assert "tokenize" not in text.__all__
    assert "DEFAULT_STOPLIST" not in text.__all__
    assert not hasattr(text, "tokenize")
    assert not hasattr(text, "DEFAULT_STOPLIST")
    # laplacian is purely spectral again — the text ops are NOT there
    assert "tokenize" not in laplacian.__all__
    assert "cooccurrence_edges" not in laplacian.__all__


def test_tool_entries_relocated_and_total_unchanged():
    from srmech import introspect
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.math.text.glyph_stream" in names
    assert "srmech.math.text.cooccurrence_edges" in names
    assert "srmech.math.text.tokenize" not in names           # retired at rc287
    assert "srmech.math.laplacian.tokenize" not in names      # relocated, not duplicated
    assert introspect.describe()["tools"]["total"] == 543
