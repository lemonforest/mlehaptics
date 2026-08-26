"""siona.relate — the deeper-`A⁻¹` SENSE layer: a word's neighborhood in the sparse CO-OCCURRENCE RELATIONSHIP
GRAPH (F1126).

NOT gloss text — the RELATIONSHIP graph, encoded SPARSE (top-K neighbor sets / Class-L), where synonyms cluster
because they share neighbors (``car``/``automobile`` both co-occur with road/drive/vehicle). Measured: this beats
the gloss-TEXT ladder 2× — synonym-NN 60% vs 31% for gloss-genome and 3% for bytes — and sidesteps the F871
bundle-saturation entirely (set/graph ops, never a bundle). This is "relationships, sparse srmech encoding"
(`[[feedback_stay_rbs_hdc_sparse_never_dense]]`) as the RIGHT deeper-`A⁻¹`.

numpy-free; set/graph ops only (no dense matrix, no ``Counter``). Attested to the simplewiki co-occurrence kernel
(`simplewiki_full_sparse_kernel.json`, 145k vocab × 5.1M edges, F778 family). The full graph stays external
(108 MB); a compact top-K neighbor index is cached (version-free — the graph is static).
"""
import json
import os

__all__ = ["load", "neighbors", "related", "relatedness", "have_graph"]

_GRAPH = "/home/skirklan/corpora/wikipedia/simplewiki_full_sparse_kernel.json"
_neigh = None       # word -> frozenset(top-K co-occurrence neighbor words)


def _cache_path():
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "siona", "cooc_neighbors.json")


def _build(graph_path, cache_path, vocab_cap=40000, topk=60):
    """Build word → top-K co-occurrence neighbors for the top ``vocab_cap`` frequent words (content words live
    here); cache the compact index. Iterates the sparse edge-list ONCE — no dense adjacency matrix."""
    from collections import defaultdict
    d = json.load(open(graph_path, encoding="utf-8"))
    vocab, freq, el, ew = d["vocab"], d["freq"], d["edge_list"], d["edge_weights"]
    keep = set(sorted(range(len(vocab)), key=lambda i: -freq[i])[:vocab_cap])
    adj = defaultdict(list)
    for e, w in zip(el, ew):
        a, b = e
        if a in keep:
            adj[a].append((b, w))
        if b in keep:
            adj[b].append((a, w))
    idx = {vocab[i]: [vocab[n] for n, _ in sorted(adj.get(i, ()), key=lambda t: -t[1])[:topk]] for i in keep}
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    json.dump(idx, open(cache_path, "w", encoding="utf-8"), separators=(",", ":"))
    return idx


def load(graph_path=None, cache_path=None):
    """The word→neighbor-set index (cached; built from the co-occurrence graph on first run). ``{}`` if neither
    the cache nor the graph is present (callers then fall back to their shallow scorer)."""
    global _neigh
    if _neigh is not None:
        return _neigh
    cp = cache_path or _cache_path()
    if os.path.exists(cp):
        _neigh = {w: frozenset(ns) for w, ns in json.load(open(cp, encoding="utf-8")).items()}
        return _neigh
    gp = graph_path or _GRAPH
    _neigh = {w: frozenset(ns) for w, ns in _build(gp, cp).items()} if os.path.exists(gp) else {}
    return _neigh


def have_graph():
    return bool(load())


def neighbors(word):
    """The word's co-occurrence neighborhood (its sense-field, sparse)."""
    return load().get((word or "").strip().lower(), frozenset())


def related(a, b):
    """Sense-relatedness of two words = shared-neighbor overlap (Jaccard of neighborhoods)."""
    A, B = neighbors(a), neighbors(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def relatedness(words, context):
    """How related a SENSE-FIELD ``words`` is to a ``context`` — the max shared-neighbor overlap between any
    sense word and the context's combined neighborhood. The deeper-`A⁻¹` sense score (F1126)."""
    ctx = set()
    for c in context:
        ctx |= neighbors(c) | {str(c).strip().lower()}
    if not ctx:
        return 0.0
    best = 0.0
    for w in words:
        n = neighbors(w) | {str(w).strip().lower()}
        o = len(n & ctx) / len(n | ctx)
        if o > best:
            best = o
    return best
