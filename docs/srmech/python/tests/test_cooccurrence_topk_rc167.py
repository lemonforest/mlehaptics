"""rc167 — streaming / bounded top-K co-occurrence (UPSTREAM §52 / F793).

``srmech.amsc.text.cooccurrence_topk`` is the LOW-RAM ENCODE peer of the all-in-
RAM ``cooccurrence_edges``: it streams the documents (never all resident) and
keeps only a bounded top-K-per-node store via chunked merge, so the encode peak
is ``O(vocab × k·cap_slack)`` instead of the full ~9 M-edge list. These tests
prove (A) **bit-exactness** to the full-graph top-K when no truncation happens,
(B) the **bound** holds under truncation, (C) **distinct-weight exactness** even
at a tight cap (within-chunk weights accumulate fully — no mid-accumulation
loss), (C2) **heavy hitters survive** across many tiny chunks, and (D) the
bounded triple **composes** with the §51 sparse Fiedler to a coherent cut.

numpy-free (the text module is numpy-free; this test is too — the exact-top-K
reference is built from the package's own ``cooccurrence_edges``).
"""

import random
from collections import defaultdict

from srmech.amsc import text as T
from srmech.amsc import laplacian as L


def _two_topic_corpus(seed=11, n_docs=400):
    rng = random.Random(seed)
    coreA = [f"a{i}" for i in range(5)]; periA = [f"a{i}" for i in range(5, 40)]
    coreB = [f"b{i}" for i in range(5)]; periB = [f"b{i}" for i in range(5, 40)]
    docs = []
    for _ in range(n_docs):
        core, peri = (coreA, periA) if rng.random() < 0.5 else (coreB, periB)
        docs.append(list(core) + [rng.choice(peri) for _ in range(rng.randint(3, 8))])
    vocab = sorted(set(w for d in docs for w in d))
    return docs, vocab, set(coreA + coreB)


def _exact_topk(n, edges, weights, vocab, k):
    adj = defaultdict(dict)
    for (u, v), w in zip(edges, weights):
        adj[u][v] = w; adj[v][u] = w
    return {vocab[u]: [(vocab[v], w)
                       for v, w in sorted(adj[u].items(), key=lambda kv: (-kv[1], kv[0]))[:k]]
            for u in range(n) if u in adj}


def test_no_truncation_is_bit_exact():
    """With a cap above every node's degree, top-K == the full-graph top-K."""
    docs, vocab, _ = _two_topic_corpus()
    nF, eF, wF = T.cooccurrence_edges(docs, window=6, vocab=vocab)
    res = T.cooccurrence_topk((d for d in docs), window=6, k=12, vocab=vocab, cap_slack=999)
    assert res["topk"] == _exact_topk(nF, eF, wF, vocab, 12)


def test_bounded_under_truncation():
    """The bounded edge set never exceeds n*k and is strictly smaller than full."""
    docs, vocab, _ = _two_topic_corpus()
    nF, eF, _wF = T.cooccurrence_edges(docs, window=6, vocab=vocab)
    res = T.cooccurrence_topk((d for d in docs), window=6, k=12, vocab=vocab, cap_slack=4)
    n, edges = res["n"], res["edges"]
    assert len(edges) <= n * 12
    assert len(edges) < len(eF)            # genuinely sparsified


def test_distinct_weight_exact_at_tight_cap():
    """A strictly-increasing-weight chain has an unambiguous top-1 per node; the
    chunked merge keeps it exact even at k=1, cap_slack=1 (the chain fits one
    chunk so its weights accumulate fully before any truncation)."""
    chain = []
    for i in range(60):
        chain += [[f"w{i}", f"w{i + 1}"]] * (i + 1)
    cv = sorted(set(w for d in chain for w in d))
    nc, ec, wc = T.cooccurrence_edges(chain, window=1, vocab=cv)
    res = T.cooccurrence_topk((d for d in chain), window=1, k=1, vocab=cv, cap_slack=1)
    assert res["topk"] == _exact_topk(nc, ec, wc, cv, 1)


def test_heavy_hitters_survive_many_tiny_chunks():
    """Across many tiny chunks, the heavy core-core edges all survive (the merge
    keeps full summed weight for retained neighbours)."""
    docs, vocab, core = _two_topic_corpus()
    nF, eF, wF = T.cooccurrence_edges(docs, window=6, vocab=vocab)
    core_idx = {vocab.index(w) for w in core}
    core_core = {tuple(sorted((u, v))) for (u, v) in eF
                 if u in core_idx and v in core_idx and vocab[u][0] == vocab[v][0]}
    res = T.cooccurrence_topk((d for d in docs), window=6, k=12, vocab=vocab,
                              cap_slack=4, chunk_docs=8)
    kept = set(res["edges"])
    assert all(e in kept for e in core_core)


def test_composes_with_sparse_fiedler():
    """The bounded (n, edges, weights) triple feeds normalized_cut_bisect to a
    clean two-community cut."""
    docs, vocab, _ = _two_topic_corpus()
    res = T.cooccurrence_topk((d for d in docs), window=6, k=12, vocab=vocab, cap_slack=4)
    n, edges, weights = res["n"], res["edges"], res["weights"]
    left, right = L.normalized_cut_bisect(n, edges, weights)
    vc = res["vocab"]
    lt = {vc[i][0] for i in left}; rt = {vc[i][0] for i in right}
    assert len(lt) == 1 and len(rt) == 1 and lt != rt   # each side single-topic


def test_topk_view_contract_and_flat_input():
    """The {token: [(neighbour, weight)<=k]} view holds; a flat token sequence is
    treated as one document; an explicit-vocab token outside it is skipped."""
    res = T.cooccurrence_topk(["x", "y", "z", "x", "y"], window=2, k=2)
    assert res["n"] == 3 and set(res["vocab"]) == {"x", "y", "z"}
    assert all(isinstance(t, str) and len(nbrs) <= 2 for t, nbrs in res["topk"].items())
    # out-of-vocab tokens are skipped when an explicit vocab is given
    res2 = T.cooccurrence_topk([["a", "b", "ZZZ", "a"]], window=2, k=2, vocab=["a", "b"])
    assert res2["n"] == 2 and "ZZZ" not in res2["vocab"]


def test_rejects_bad_args():
    import pytest
    with pytest.raises(TypeError):
        T.cooccurrence_topk("raw string is not tokens", window=2, k=2)
    for bad in ({"window": 0}, {"k": 0}, {"cap_slack": 0}, {"chunk_docs": 0}):
        with pytest.raises(ValueError):
            T.cooccurrence_topk([["a", "b"]], **bad)
