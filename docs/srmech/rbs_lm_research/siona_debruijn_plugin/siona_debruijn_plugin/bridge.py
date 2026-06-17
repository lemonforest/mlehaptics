"""bridge.py — the Python surface srmech's profile activates: ctypes-loads the package's libsiona_debruijn.so
and exposes `abi_version()` + `walk(ids, k)`. The de Bruijn fiber walk (F805/F818) in native C, symbol-agnostic
(int64 ids → works for text tokens, DNA bases, any discrete stream)."""
import ctypes
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
