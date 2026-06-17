"""Siona's recall surface (the srmech-profile bridge): the de Bruijn fiber walk (F805/F818) + the full-body recall
path (F825), pure-Python and exact. Symbol-agnostic — operates on integer ids, so the same ops serve text tokens,
DNA bases (de Bruijn graphs ARE genome assembly), or any discrete stream.

rc1 recalls from the loose RBS-HDC instrument (an NDJSON of per-body shapes + a title→offset index). A native
single-file srmech genome (`srmech.amsc.genome`, PKG-3/F832/F833) was prototyped and recalls exactly, but the genome
format is blocked at corpus scale on two counts — it stores each 2-bit Klein-4 lane as a full byte (a flat 4× bloat)
and `genome_pack` is O(n²) in chromosome count — both filed upstream (UPSTREAM_NOTES §55). Native-genome bodies are
revisited once those land; rc1 ships on the loose store. The Klein-4 HV of a token is a deterministic *projection*
(`klein4_random(seed=hash(token))`) recomputed on demand at inference — the store holds the fiber (the sequence),
never a spatial HV per position (F833)."""
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
