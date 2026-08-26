"""rc248 (gh #1390 item 1) — text.cooccurrence_edges(directed=True).

The directed=True branch is a backward-compatible SUPERSET of the shipped
undirected op: on the SAME canonical (i<j) edges it returns
``(n, edges, metric, charge)`` where ``metric`` == the ``directed=False``
weights (``w_fwd + w_bwd``) and ``charge`` == ``w_fwd − w_bwd`` (the direction
the unordered fold discards). Faithful port of
``R-RBS-LM-DIRCOOCCUR_prototype_directed_cooccurrence_edges_metric_plus_charge``.
The pure loop is the parity oracle; the C peer
(``srmech_text_cooccurrence_edges_directed``) is byte-identical when loaded.
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.math import text as T

NATIVE = _native.has_native_text_cooccurrence_edges_directed()

VOCAB = ["alpha", "beta", "gamma", "delta"]
DOCS = [["alpha", "beta", "gamma", "alpha", "beta", "delta", "gamma"]]


def test_directed_false_is_unchanged_triple():
    out = T.cooccurrence_edges(DOCS, window=2, vocab=VOCAB)
    assert len(out) == 3                                     # (n, edges, weights)
    out2 = T.cooccurrence_edges(DOCS, window=2, vocab=VOCAB, directed=False)
    assert out2 == out                                      # explicit False identical


def test_directed_true_is_metric_plus_charge_superset():
    n, edges, metric, charge = T.cooccurrence_edges(DOCS, window=2, vocab=VOCAB,
                                                    directed=True)
    n0, e0, w0 = T.cooccurrence_edges(DOCS, window=2, vocab=VOCAB)
    assert n == n0 and edges == e0                          # SAME canonical edges
    assert metric == w0                                     # metric == undirected weight
    assert edges == [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    assert metric == [3, 2, 1, 3, 1, 1]
    assert charge == [1, 0, 1, 1, 1, -1]                    # the prototype's charge axis
    assert any(c != 0 for c in charge)


def test_reversing_corpus_flips_charge_exactly():
    n, edges, metric, charge = T.cooccurrence_edges(DOCS, window=2, vocab=VOCAB,
                                                    directed=True)
    rn, re, rm, rc = T.cooccurrence_edges([list(reversed(DOCS[0]))], window=2,
                                          vocab=VOCAB, directed=True)
    assert re == edges and rm == metric                    # metric unchanged
    assert rc == [-c for c in charge]                      # charge exactly flipped


def test_charge_is_signed_class_k_not_abs():
    # a strictly one-directional corpus → all-forward charge == metric
    _n, _e, metric, charge = T.cooccurrence_edges([["a", "b", "c"]], window=2,
                                                  vocab=["a", "b", "c"],
                                                  directed=True)
    assert charge == metric                                # every pair earlier→smaller-id


def test_directed_must_be_bool():
    for bad in (1, "yes", None, 0):
        with pytest.raises(ValueError):
            T.cooccurrence_edges(DOCS, vocab=VOCAB, directed=bad)


def test_registered_in_tool_schema():
    from srmech.introspect.tool_schema import get_tool_schema
    tool = next(t for t in get_tool_schema().tools
                if t.name == "srmech.math.text.cooccurrence_edges")
    assert any(p.name == "directed" for p in tool.parameters)


# ── native parity ──────────────────────────────────────────────────────────

def _pure_directed(docs, window, vocab):
    idx = {t: i for i, t in enumerate(vocab)}
    keep = set(vocab)
    fwd, bwd = {}, {}
    for doc in docs:
        toks = [idx[t] for t in doc if t in keep]
        m = len(toks)
        for a in range(m):
            ia = toks[a]
            for b in range(a + 1, min(a + window + 1, m)):
                ib = toks[b]
                if ia == ib:
                    continue
                key = (ia, ib) if ia < ib else (ib, ia)
                (fwd if ia < ib else bwd)[key] = \
                    (fwd if ia < ib else bwd).get(key, 0) + 1
    edges = sorted(set(fwd) | set(bwd))
    return (len(vocab), edges,
            [fwd.get(e, 0) + bwd.get(e, 0) for e in edges],
            [fwd.get(e, 0) - bwd.get(e, 0) for e in edges])


@pytest.mark.skipif(not NATIVE, reason="rc248 directed cooccurrence C peer not loaded")
def test_native_symbol_bound():
    assert hasattr(_native.LIB, "srmech_text_cooccurrence_edges_directed")
    assert _native.NATIVE_ABI_VERSION == 24


@pytest.mark.skipif(not NATIVE, reason="rc248 directed cooccurrence C peer not loaded")
def test_native_equals_pure():
    cases = [
        (VOCAB, DOCS, 2),
        (list("abcdef"), [list("abcabcdefedcba"), list("faceb")], 3),
        (list("mississippi"), [list("mississippi")], 2),
        (["x", "y", "z"], [["x", "y", "z", "z", "y", "x", "x", "y"]], 4),
        (list("abcdefgh"), [list("abcdefgh" * 3)], 1),
    ]
    for vocab, docs, window in cases:
        nat = list(T.cooccurrence_edges(docs, window=window, vocab=vocab,
                                        directed=True))
        assert nat == list(_pure_directed(docs, window, vocab)), (vocab[:3], window)
