"""Siona's recall surface (the srmech-profile bridge): the de Bruijn fiber walk (F805/F818) + the full-body
recall path (F825), pure-Python and exact. Symbol-agnostic — operates on integer ids, so the same ops serve
text tokens, DNA bases (de Bruijn graphs ARE genome assembly), or any discrete stream.

rc1 is pure-Python (portable). A C-native accelerator (F824, ~3× faster at scale) is a follow-on `[profile.native]`
platform-wheel tier; the bridge will prefer it when present and fall back to this walk."""
import json

__all__ = ["walk", "recall"]


def walk(ids, k):
    """Reconstruct a sequence by walking its de Bruijn (k-1)-gram → successor map from the seed.
    `ids`: a list of hashable symbols (ints/strings); `k`: the window. Returns the reconstructed list
    (== `ids` when the walk is unique, i.e. k ≥ k*; otherwise the most-likely / first-seen-successor walk)."""
    if k < 2 or len(ids) < k:
        return list(ids)
    succ = {}
    for i in range(k - 1, len(ids)):
        succ.setdefault(tuple(ids[i - (k - 1):i]), ids[i])   # first successor wins (unique when k ≥ k*)
    out = list(ids[:k - 1])
    for _ in range(len(ids) - (k - 1)):
        nxt = succ.get(tuple(out[-(k - 1):]))
        if nxt is None:
            break
        out.append(nxt)
    return out


_IDX_CACHE = {}


def _index(index_path):
    idx = _IDX_CACHE.get(index_path)
    if idx is None:
        with open(index_path) as f:
            idx = json.load(f)
        _IDX_CACHE[index_path] = idx
    return idx


def recall(title, instrument_path, index_path):
    """THE RECALL PATH: reconstruct an entire body by title. Resolve title → byte offset via the index, seek the
    NDJSON instrument, read the record (`s` = space-joined tokens, `k` = the unique-walk window), walk the de
    Bruijn shape. Returns {tokens, k, exact, native} or None if the title isn't in the instrument. The host
    supplies its own instrument + index paths — the op stays general (any RBS-HDC instrument, any process)."""
    off = _index(index_path).get(title.lower())
    if off is None:
        return None
    with open(instrument_path) as f:
        f.seek(off)
        rec = json.loads(f.readline())
    toks = rec["s"].split()
    k = rec["k"]
    out = walk(toks, k)
    return {"tokens": out, "k": k, "exact": out == toks, "native": False}
