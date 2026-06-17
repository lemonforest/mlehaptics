"""bridge.py — the Python surface srmech's profile activates: ctypes-loads the package's libsiona_debruijn.so
and exposes `abi_version()` + `walk(ids, k)` + `recall(title, instrument_path, index_path)`. The de Bruijn fiber
walk (F805/F818) in native C, symbol-agnostic (int64 ids → text tokens, DNA bases, any discrete stream); `recall`
is the full RECALL PATH (F825) — title → seek the NDJSON instrument via its offset index → C-walk → reconstructed
sequence — so the host (Siona) activates this profile and gets its recall from it, instead of walking inline."""
import ctypes
import json
import os

_LIB = None


def _lib():
    global _LIB
    if _LIB is None:
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("libsiona_debruijn.so", "libsiona_debruijn.dylib", "siona_debruijn.dll"):
            p = os.path.join(here, name)
            if os.path.exists(p):
                lib = ctypes.CDLL(p)
                lib.siona_debruijn_abi_version.restype = ctypes.c_int
                lib.siona_debruijn_load.argtypes = [ctypes.POINTER(ctypes.c_int64), ctypes.c_int64]
                lib.siona_debruijn_load.restype = ctypes.c_int
                lib.siona_debruijn_walk.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int64), ctypes.c_int64]
                lib.siona_debruijn_walk.restype = ctypes.c_int64
                _LIB = lib
                break
        else:
            raise OSError("siona_debruijn native library not found beside bridge.py")
    return _LIB


def abi_version():
    """The native plugin's ABI version (smoke-test target)."""
    return _lib().siona_debruijn_abi_version()


def walk(ids, k):
    """Reconstruct an int-id sequence by walking its de Bruijn (k-1)-gram → successor map, in native C.
    `ids`: list[int]; `k`: window. Returns the reconstructed list[int] (== ids when the walk is unique)."""
    n = len(ids)
    arr = (ctypes.c_int64 * n)(*ids)
    out = (ctypes.c_int64 * (n + 8))()
    lib = _lib()
    if lib.siona_debruijn_load(arr, n) != 0:
        raise ValueError("sequence too long for the native de Bruijn buffer")
    m = lib.siona_debruijn_walk(int(k), out, n + 8)
    if m < 0:
        raise ValueError("native de Bruijn walk failed (bad k / overflow)")
    return [out[i] for i in range(m)]


_IDX_CACHE = {}


def _index(index_path):
    """Load + cache a title→byte-offset index (the instrument's random-access map, F814)."""
    idx = _IDX_CACHE.get(index_path)
    if idx is None:
        with open(index_path) as f:
            idx = json.load(f)
        _IDX_CACHE[index_path] = idx
    return idx


def recall(title, instrument_path, index_path):
    """THE RECALL PATH (F825): reconstruct an entire body by title. Resolve title → byte offset, seek the NDJSON
    instrument, read the record (`s` = space-joined tokens, `k` = the unique-walk window), map tokens→int ids, walk
    the de Bruijn shape in native C, map back. Returns {tokens, k, exact, native} or None if the title is absent.
    Symbol-stream-agnostic: the host supplies its own instrument; another process with its own instrument reuses this."""
    off = _index(index_path).get(title.lower())
    if off is None:
        return None
    with open(instrument_path) as f:
        f.seek(off)
        rec = json.loads(f.readline())
    toks = rec["s"].split()
    k = rec["k"]
    vocab = {}
    ids = [vocab.setdefault(t, len(vocab)) for t in toks]
    inv = [t for t, _ in sorted(vocab.items(), key=lambda kv: kv[1])]
    rtoks = [inv[i] for i in walk(ids, k)]
    return {"tokens": rtoks, "k": k, "exact": rtoks == toks, "native": True}
