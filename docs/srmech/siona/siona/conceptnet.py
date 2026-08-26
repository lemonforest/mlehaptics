"""siona.conceptnet — the 3rd coherency PERSPECTIVE for the k=3 Rosetta (F1131): a word's neighborhood in the
ConceptNet TYPED relationship graph.

A genuinely DIFFERENT type from `relate` (F1126): `relate` is UNTYPED co-occurrence PROXIMITY; ConceptNet is
TYPED semantic edges (/r/Synonym, /r/IsA, /r/RelatedTo, /r/SimilarTo, /r/FormOf …). Three types — FORM (byte),
PROXIMITY-relation (`relate`), TYPED-relation (`conceptnet`) — are the 3 sampling axes the QDFT reconstruction
needs (F1131: k=2 detects, k=3 corrects).

Same sparse discipline as `relate`: set/graph ops, numpy-free, a compact cached top-K neighbor index (the full
34M-edge dump stays external). Cross-lingual coverage is SPARSE for ancient/creole tongues (Bislama 563 edges,
Sumerian 1975, Egyptian 2975) — a partial bridge, not a full one; English is dense (12.4M edges).

ATTESTED to ConceptNet 5.7 (Speer, Chin, Havasi, *AAAI* 2017; CC BY-SA 4.0; `conceptnet-assertions-5.7.0.csv.gz`).
"""
import gzip
import json
import os
import re

__all__ = ["load", "neighbors", "related", "relatedness", "have_graph", "build"]

_SRC = "/home/skirklan/corpora/conceptnet/conceptnet-assertions-5.7.0.csv.gz"
# TYPED semantic relations — the sense-bearing subset (NOT the whole dump; e.g. no /r/EtymologicallyRelatedTo noise)
_KEEP = frozenset(("/r/RelatedTo", "/r/Synonym", "/r/SimilarTo", "/r/IsA", "/r/FormOf",
                   "/r/DerivedFrom", "/r/PartOf", "/r/HasContext", "/r/UsedFor", "/r/HasA"))
_lang = "en"
_neigh = None


def _cache_path(lang="en"):
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "siona", "conceptnet_%s_neighbors.json" % lang)


def _term(uri, lang):
    m = re.match(r"^/c/%s/([^/]+)" % lang, uri)          # /c/en/word[/n] → word
    return m.group(1) if m else None


def build(src=None, lang="en", topk=60, cache_path=None):
    """Stream the ConceptNet dump ONCE, keep the TYPED semantic edges in ``lang``, build word → top-K neighbors,
    cache the compact index. Sparse — a dict of neighbor-counts, never a dense matrix."""
    from collections import defaultdict
    src = src or _SRC
    adj = defaultdict(dict)
    with gzip.open(src, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.split("\t")
            if len(p) < 4 or p[1] not in _KEEP:
                continue
            a, b = _term(p[2], lang), _term(p[3], lang)
            if not a or not b or a == b:
                continue
            adj[a][b] = adj[a].get(b, 0) + 1
            adj[b][a] = adj[b].get(a, 0) + 1
    idx = {w: [k for k, _ in sorted(ns.items(), key=lambda kv: -kv[1])[:topk]]
           for w, ns in adj.items() if len(ns) >= 1}
    cp = cache_path or _cache_path(lang)
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    json.dump(idx, open(cp, "w", encoding="utf-8"), separators=(",", ":"))
    return idx


def load(lang="en", cache_path=None):
    """The word→typed-neighbor-set index (cached; built from the dump on first run via ``build``). ``{}`` if
    neither the cache nor the dump is present."""
    global _neigh
    if _neigh is not None:
        return _neigh
    cp = cache_path or _cache_path(lang)
    if os.path.exists(cp):
        _neigh = {w: frozenset(ns) for w, ns in json.load(open(cp, encoding="utf-8")).items()}
        return _neigh
    _neigh = {w: frozenset(ns) for w, ns in build(lang=lang, cache_path=cp).items()} if os.path.exists(_SRC) else {}
    return _neigh


def have_graph():
    return bool(load())


def neighbors(word):
    return load().get((word or "").strip().lower(), frozenset())


def related(a, b):
    """Typed-relation sense-relatedness = shared-neighbor overlap (Jaccard)."""
    A, B = neighbors(a), neighbors(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def relatedness(words, context):
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
