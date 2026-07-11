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
