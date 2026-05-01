"""ctypes wrapper for the native cs_bitboard4d shared library.

1.7.0 D2 M2.1 foundation. Loads the library shipped in the wheel under
``chess_spectral/_native/`` (alongside the ``spectral`` /
``spectral_4d`` binaries). If the library isn't present (sdist install
without C toolchain, Pyodide WASM-less install, etc.), the module
exposes ``HAS_NATIVE = False`` and the pure-Python ``Bitboard4D``
remains the only path.

Per ADR-001 fallback discipline: all callers MUST guard usage with
``if HAS_NATIVE: ...``; never assume the library is loadable. The
fallback is correctness; the native path is performance.

Loaded functions match ``include/cs_bitboard4d.h``. ABI version
checked at load time; mismatched binaries are treated as missing
(``HAS_NATIVE = False``).
"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Optional


# Number of uint64 words per Bitboard4D. Mirror of CS_BB4_N_WORDS;
# kept in sync with the header.
N_WORDS: int = 64
N_SQUARES: int = 4096

# Bumped on incompatible C ABI changes; must match CS_BB4_ABI_VERSION
# in cs_bitboard4d.h.
EXPECTED_ABI_VERSION: int = 1


def _candidate_library_names() -> list[str]:
    """Return the platform-specific filenames the library may have.

    The wheel installs to ``chess_spectral/_native/`` with the
    canonical name; we list a few fallbacks for in-tree development
    (e.g. running from a CMake build dir without ``pip install -e .``).
    """
    if sys.platform.startswith("win"):
        return ["cs_bitboard4d.dll"]
    if sys.platform == "darwin":
        return ["libcs_bitboard4d.dylib", "cs_bitboard4d.dylib"]
    return ["libcs_bitboard4d.so", "cs_bitboard4d.so"]


def _find_library() -> Optional[Path]:
    """Locate the shared library, or None if not shipped/built.

    Search order:
      1. Wheel-install location: ``<package>/_native/``.
      2. Env-var override: ``CS_BITBOARD4D_LIB`` (absolute path).
      3. CMake build directory: ``<repo>/build/`` for in-tree dev.
    """
    pkg_native = Path(__file__).resolve().parent / "_native"
    candidates = []
    for name in _candidate_library_names():
        candidates.append(pkg_native / name)

    env = os.environ.get("CS_BITBOARD4D_LIB")
    if env:
        candidates.insert(0, Path(env))

    # In-tree dev: chess-spectral/build/* is where CMake puts artefacts.
    build_dir = Path(__file__).resolve().parents[2] / "build"
    if build_dir.exists():
        for name in _candidate_library_names():
            candidates.append(build_dir / name)
        # CMake on Windows typically places into build/Release/.
        for cfg in ("Release", "Debug"):
            for name in _candidate_library_names():
                candidates.append(build_dir / cfg / name)

    for p in candidates:
        if p.exists():
            return p
    return None


def _bind(lib: ctypes.CDLL) -> None:
    """Set ``argtypes`` / ``restype`` for every exported symbol.

    Doing this once at load time means every call has correct
    type marshalling and the GIL is released around the C call (ctypes
    default for non-PyObject return types).
    """
    u64_p = ctypes.POINTER(ctypes.c_uint64)
    cu64_p = ctypes.POINTER(ctypes.c_uint64)  # const-qualified at the C side

    lib.cs_bb4_popcount.argtypes = [cu64_p]
    lib.cs_bb4_popcount.restype = ctypes.c_int

    for name in ("cs_bb4_and", "cs_bb4_or", "cs_bb4_xor", "cs_bb4_sub"):
        getattr(lib, name).argtypes = [u64_p, cu64_p, cu64_p]
        getattr(lib, name).restype = None

    lib.cs_bb4_not.argtypes = [u64_p, cu64_p]
    lib.cs_bb4_not.restype = None

    for name in ("cs_bb4_set_square", "cs_bb4_clear_square",
                 "cs_bb4_toggle_square"):
        getattr(lib, name).argtypes = [u64_p, ctypes.c_int]
        getattr(lib, name).restype = None

    lib.cs_bb4_test_square.argtypes = [cu64_p, ctypes.c_int]
    lib.cs_bb4_test_square.restype = ctypes.c_int

    for name in ("cs_bb4_is_empty", "cs_bb4_is_full"):
        getattr(lib, name).argtypes = [cu64_p]
        getattr(lib, name).restype = ctypes.c_int

    for name in ("cs_bb4_equals", "cs_bb4_intersects"):
        getattr(lib, name).argtypes = [cu64_p, cu64_p]
        getattr(lib, name).restype = ctypes.c_int

    lib.cs_bb4_abi_version.argtypes = []
    lib.cs_bb4_abi_version.restype = ctypes.c_int


# ──────────────────────────────────────────────────────────────────────
# One-shot load at import. Failure is non-fatal — the package still
# imports and ``HAS_NATIVE`` reports False.
# ──────────────────────────────────────────────────────────────────────

_LIB_PATH: Optional[Path] = _find_library()
LIB: Optional[ctypes.CDLL] = None
LIB_PATH: Optional[Path] = None
ABI_VERSION: Optional[int] = None
HAS_NATIVE: bool = False
LOAD_ERROR: Optional[str] = None

if _LIB_PATH is not None:
    try:
        _candidate_lib = ctypes.CDLL(str(_LIB_PATH))
        _bind(_candidate_lib)
        version = int(_candidate_lib.cs_bb4_abi_version())
        if version != EXPECTED_ABI_VERSION:
            LOAD_ERROR = (
                f"native bitboard ABI mismatch at {_LIB_PATH}: "
                f"binary is v{version}, Python expects v{EXPECTED_ABI_VERSION}; "
                "rebuild the C extension or fall back to pure Python."
            )
        else:
            LIB = _candidate_lib
            LIB_PATH = _LIB_PATH
            ABI_VERSION = version
            HAS_NATIVE = True
    except (OSError, AttributeError, ValueError) as exc:
        LOAD_ERROR = f"failed to load {_LIB_PATH}: {exc}"
else:
    LOAD_ERROR = (
        "native bitboard library not found in chess_spectral/_native/; "
        "this is normal for sdist installs and Pyodide. Pure-Python "
        "Bitboard4D will be used."
    )


__all__ = [
    "HAS_NATIVE",
    "LIB",
    "LIB_PATH",
    "ABI_VERSION",
    "LOAD_ERROR",
    "N_WORDS",
    "N_SQUARES",
    "EXPECTED_ABI_VERSION",
]
