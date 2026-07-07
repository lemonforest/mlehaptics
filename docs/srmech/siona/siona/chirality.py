"""siona.chirality — the CLASS-C opponent / chirality axis (F1135/F1136): the 3rd TYPE-INDEPENDENT semantic DoF.

Antonyms are co-occurrence METAMERS — `hot`/`cold` co-occur, so proximity (`relate`) AND typed-relation
(`conceptnet`) both read them as ~as-related-as synonyms, and neither can tell synonym from antonym (the classic
distributional-antonymy failure). The axis that resolves them is CHIRALITY (Class C / γ₅): antonyms are OPPOSITE
POLES OF ONE DIMENSION = an opponent pair — exactly color vision's OPPONENT PROCESS (the DoF the 3rd cone enables,
F1134). MEASURED (F1136): this axis is genuinely independent (Kendall τ vs proximity +0.25, vs typed +0.42, vs
form −0.07 — far more independent than typed↔prox's +0.63) and RESOLVES the antonym metamer (antonyms fire 1.00,
synonyms ~0), adding the synonym-vs-antonym distinction the relational axes lacked. That is the graft-as-growth
DoF done RIGHT: a coherent graft of the RIGHT TYPE (chirality) adds a DoF; a redundant type (another relation
flavor) does not.

Sparse (opponent edge-sets), numpy-free. Attested to ConceptNet 5.7 /r/Antonym + /r/DistinctFrom (Speer, Chin,
Havasi, *AAAI* 2017; CC BY-SA 4.0).
"""
import gzip
import json
import os
import re

__all__ = ["load", "poles", "opposite", "have_axis", "build"]

_SRC = "/home/skirklan/corpora/conceptnet/conceptnet-assertions-5.7.0.csv.gz"
_KEEP = frozenset(("/r/Antonym", "/r/DistinctFrom"))       # the opponent / opposite-pole relations
_neigh = None       # word -> frozenset(opposite-pole words)


def _cache_path():
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "siona", "conceptnet_en_antonym.json")


def _term(uri):
    m = re.match(r"^/c/en/([^/]+)", uri)
    return m.group(1) if m else None


def build(src=None, cache_path=None):
    """Stream the ConceptNet dump once, keep the opponent (/r/Antonym + /r/DistinctFrom) English edges, cache the
    word → opposite-poles index. Sparse — an edge-set per word, never a matrix."""
    from collections import defaultdict
    adj = defaultdict(set)
    with gzip.open(src or _SRC, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.split("\t")
            if len(p) < 4 or p[1] not in _KEEP:
                continue
            a, b = _term(p[2]), _term(p[3])
            if a and b and a != b:
                adj[a].add(b)
                adj[b].add(a)
    idx = {w: sorted(s) for w, s in adj.items()}
    cp = cache_path or _cache_path()
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    json.dump(idx, open(cp, "w", encoding="utf-8"), separators=(",", ":"))
    return idx


def load(cache_path=None):
    """The word→opposite-poles index (cached; built from the dump on first run). ``{}`` if neither is present."""
    global _neigh
    if _neigh is not None:
        return _neigh
    cp = cache_path or _cache_path()
    if os.path.exists(cp):
        _neigh = {w: frozenset(s) for w, s in json.load(open(cp, encoding="utf-8")).items()}
        return _neigh
    _neigh = {w: frozenset(s) for w, s in build(cache_path=cp).items()} if os.path.exists(_SRC) else {}
    return _neigh


def have_axis():
    return bool(load())


def poles(word):
    """The opposite-pole words for ``word`` (its chirality-flip partners)."""
    return load().get((word or "").strip().lower(), frozenset())


def opposite(a, b):
    """The CLASS-C chirality signal: 1.0 iff ``a`` and ``b`` are opposite poles (an opponent pair), else 0.0. The
    axis that resolves the antonym metamer the relational axes collapse."""
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    return 1.0 if (b in load().get(a, ()) or a in load().get(b, ())) else 0.0
