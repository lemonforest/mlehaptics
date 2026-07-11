"""siona._native — the ctypes shim for Siona's native plugin (libsiona_native.so).

Mirrors srmech's own ``srmech.amsc._native`` pattern: locate the shared library
inside the package's ``_native/`` dir, verify the ABI handshake, expose
``HAS_NATIVE`` + wrapped symbols, and provide a pure-Python REFERENCE twin for
every native op so the surface works identically with or without the ``.so``
(the has_native dispatch pattern). srmech's ``profile_loader`` loads the SAME
library independently as ``srmech.profile("siona").native``; this module is
Siona's own internal dispatch path.

Scaffold op: FNV-1a-64 content hash (the bytes->int shape the tokenize /
content-address hot-path needs). ``fnv1a64(data)`` dispatches to the native
symbol when present, else to the validated pure-Python ``_fnv1a64_py``.
Parity (native == python, bit-for-bit) is asserted by tests/test_native_parity.py.
"""
from __future__ import annotations

import array as _array
import ctypes
from pathlib import Path
from typing import Optional

EXPECTED_ABI_VERSION = 1
_U64_MASK = (1 << 64) - 1
_FNV64_OFFSET_BASIS = 14695981039346656037
_FNV64_PRIME = 1099511628211

HAS_NATIVE: bool = False
LOAD_ERROR: Optional[str] = None
NATIVE_ABI_VERSION: Optional[int] = None
LIB_PATH: Optional[str] = None

_LIB: Optional[ctypes.CDLL] = None


def _candidate_names() -> tuple[str, ...]:
    import sys
    if sys.platform == "win32":
        return ("siona_native.dll", "libsiona_native.dll")
    if sys.platform == "darwin":
        return ("libsiona_native.dylib",)
    return ("libsiona_native.so",)


def _load() -> None:
    """Locate + bind libsiona_native, run the ABI handshake. On any failure
    HAS_NATIVE stays False and LOAD_ERROR is populated (pure-Python fallback)."""
    global HAS_NATIVE, LOAD_ERROR, NATIVE_ABI_VERSION, LIB_PATH, _LIB
    native_dir = Path(__file__).resolve().parent / "_native"
    names = _candidate_names()
    lib_path = next((native_dir / n for n in names if (native_dir / n).exists()), None)
    if lib_path is None:
        LOAD_ERROR = f"no {names} in {native_dir}"
        return
    try:
        lib = ctypes.CDLL(str(lib_path))
        lib.siona_native_abi_version.argtypes = []
        lib.siona_native_abi_version.restype = ctypes.c_int
        observed = int(lib.siona_native_abi_version())
        if observed != EXPECTED_ABI_VERSION:
            LOAD_ERROR = f"ABI {observed} != expected {EXPECTED_ABI_VERSION}"
            return
        lib.siona_native_fnv1a64.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        lib.siona_native_fnv1a64.restype = ctypes.c_uint64
        lib.siona_native_tokenize.argtypes = [
            ctypes.c_char_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t]
        lib.siona_native_tokenize.restype = ctypes.c_long
        lib.siona_native_cooccurrence_accumulate.argtypes = [
            ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t, ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_size_t]
        lib.siona_native_cooccurrence_accumulate.restype = ctypes.c_long
        lib.siona_native_arena_compact.argtypes = [
            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_size_t, ctypes.POINTER(ctypes.c_int32),
            ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_size_t]
        lib.siona_native_arena_compact.restype = ctypes.c_long
    except (OSError, AttributeError) as exc:
        LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        return
    _LIB = lib
    NATIVE_ABI_VERSION = observed
    LIB_PATH = str(lib_path)
    HAS_NATIVE = True


def _fnv1a64_py(data: bytes) -> int:
    """The validated pure-Python reference (the fallback + the parity oracle)."""
    h = _FNV64_OFFSET_BASIS
    for b in data:
        h = ((h ^ b) * _FNV64_PRIME) & _U64_MASK
    return h


def fnv1a64(data: bytes) -> int:
    """FNV-1a-64 content hash — native when available, else pure-Python."""
    if HAS_NATIVE and _LIB is not None:
        return int(_LIB.siona_native_fnv1a64(data, len(data)))
    return _fnv1a64_py(data)


# ── tokenize (byte-scan word boundaries) ───────────────────────────────
def _is_word_byte(c: int) -> bool:
    return (48 <= c <= 57) or (97 <= c <= 122) or (65 <= c <= 90) or c >= 0x80


def _tokenize_spans_py(data: bytes) -> list:
    """Pure-Python reference: (start, length) byte-spans of tokens."""
    out, i, n = [], 0, len(data)
    while i < n:
        while i < n and not _is_word_byte(data[i]):
            i += 1
        if i >= n:
            break
        s = i
        while i < n and _is_word_byte(data[i]):
            i += 1
        out.append((s, i - s))
    return out


def tokenize_spans(data: bytes) -> list:
    """(start, length) token byte-spans — native scan when available."""
    if HAS_NATIVE and _LIB is not None:
        n = len(data)
        cap = n // 2 + 2                       # >= max possible tokens
        buf = (ctypes.c_int32 * (2 * cap))()
        got = int(_LIB.siona_native_tokenize(data, n, buf, cap))
        if got >= 0:
            return [(buf[2 * k], buf[2 * k + 1]) for k in range(got)]
    return _tokenize_spans_py(data)


def tokenize(text) -> list:
    """Lowercased token strings (span-scan + slice + casefold)."""
    data = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    return [data[s:s + ln].decode("utf-8", "replace").lower()
            for s, ln in tokenize_spans(data)]


# ── windowed co-occurrence (tokens -> edge weights; the encode hot loop) ─
def flatten_docs(docs) -> tuple:
    """[[id,...], ...] -> (token_ids, doc_ends) with cumulative exclusive ends."""
    token_ids, doc_ends, cum = [], [], 0
    for d in docs:
        token_ids.extend(d)
        cum += len(d)
        doc_ends.append(cum)
    return token_ids, doc_ends


def _cooccurrence_counts_py(token_ids, doc_ends, window) -> dict:
    """The validated reference: {(i, j): count}, i < j, window resets per doc."""
    counts, start, n = {}, 0, len(token_ids)
    for raw_end in doc_ends:
        end = raw_end if raw_end <= n else n
        for a in range(start, end):
            ia = token_ids[a]
            bmax = min(a + window, end - 1)
            for b in range(a + 1, bmax + 1):
                jb = token_ids[b]
                if ia == jb:
                    continue
                key = (ia, jb) if ia < jb else (jb, ia)
                counts[key] = counts.get(key, 0) + 1
        start = end
    return counts


def _next_pow2(x: int) -> int:
    p = 1
    while p < x:
        p <<= 1
    return p


def _as_c_int32(seq):
    """Python int-seq -> (backing, c_int32 ptr). Buffer-protocol when itemsize
    matches (avoids per-element ctypes unpacking); returns backing to keep alive."""
    a = _array.array("i", seq)
    if a.itemsize == 4:
        return a, (ctypes.c_int32 * len(a)).from_buffer(a)
    ca = (ctypes.c_int32 * len(seq))(*seq)
    return ca, ca


def _cooccurrence_native_edges(token_ids, doc_ends, window):
    """Native accumulate + C-side compact. Returns (i_list, j_list, w_list) with
    the arena read back IN C (never a Python scan of the sparse arena), or None
    to fall back (arena / output overflow, or arena too big to allocate)."""
    n = len(token_ids)
    cap = _next_pow2(max(16, 2 * n * window))  # loose upper bound on pairs
    if cap > (1 << 26):                        # too big -> let Python handle
        return None
    _kt, tid = _as_c_int32(token_ids)
    _kd, de = _as_c_int32(doc_ends)
    keys = (ctypes.c_uint64 * cap)()
    ctypes.memset(keys, 0xFF, cap * 8)         # prefill to ARENA_EMPTY
    vals = (ctypes.c_uint32 * cap)()
    got = int(_LIB.siona_native_cooccurrence_accumulate(
        tid, n, de, len(doc_ends), window, keys, vals, cap))
    if got < 0:
        return None                            # arena full -> fall back
    oi = (ctypes.c_int32 * got)()
    oj = (ctypes.c_int32 * got)()
    ow = (ctypes.c_uint32 * got)()
    m = int(_LIB.siona_native_arena_compact(keys, vals, cap, oi, oj, ow, got))
    if m < 0:
        return None
    return oi[:m], oj[:m], ow[:m]              # ctypes slices = fast C-level lists


def _cooccurrence_counts_native(token_ids, doc_ends, window):
    """Native accumulator returning the counts dict (parity shape), or None."""
    res = _cooccurrence_native_edges(token_ids, doc_ends, window)
    if res is None:
        return None
    ii, jj, ww = res
    return {(ii[k], jj[k]): ww[k] for k in range(len(ii))}


def cooccurrence_edges_parallel(token_ids, doc_ends, window=2) -> tuple:
    """Windowed co-occurrence -> THREE PARALLEL lists (i_list, j_list, w_list),
    each edge (i_list[k], j_list[k]) with i < j, weight w_list[k]. ORDER UNSPECIFIED.

    THIS is the fast form — it keeps the native win (~1.3x in the encode's
    large-vocab regime) because it never builds Python (i, j) tuples or a dict.
    Feed the three arrays straight to a Laplacian builder. The FFI lesson: the edge
    list is Theta(input) for a large vocabulary, so ANY per-edge Python
    materialisation (dict rebuild 0.6x, tuple list ~0.9x, sort 0.55x) gives the C
    win back — the pipeline pays off only while the data stays dense/native (which
    is why tokens->edges->laplacian wants to stay together in C). Native when the
    lib is present + the arena fits; pure-Python fallback otherwise.
    """
    token_ids, doc_ends = list(token_ids), list(doc_ends)
    if HAS_NATIVE and _LIB is not None:
        res = _cooccurrence_native_edges(token_ids, doc_ends, window)
        if res is not None:
            return res
    counts = _cooccurrence_counts_py(token_ids, doc_ends, window)
    return ([k[0] for k in counts], [k[1] for k in counts], list(counts.values()))


def cooccurrence_edges(token_ids, doc_ends, window=2) -> tuple:
    """Convenience: (edges, weights) with edges as (i, j) tuples. Prefer
    cooccurrence_edges_parallel() for speed — building the (i, j) tuples here is
    the per-edge Python cost that erases the native win for a large vocabulary."""
    ii, jj, ww = cooccurrence_edges_parallel(token_ids, doc_ends, window)
    return list(zip(ii, jj)), ww


def native_status() -> dict:
    """Public introspection — mirrors srmech.native_status()."""
    return {
        "has_native": HAS_NATIVE,
        "abi_version": NATIVE_ABI_VERSION,
        "expected_abi": EXPECTED_ABI_VERSION,
        "library_path": LIB_PATH,
        "load_error": LOAD_ERROR,
    }


_load()
