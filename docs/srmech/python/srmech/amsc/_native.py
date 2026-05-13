"""ctypes wrapper for the native srmech shared library.

Loads ``libsrmech.{so,dll,dylib}`` from ``srmech/_native/`` if it
shipped in the wheel. If not (sdist install without a C toolchain,
Pyodide / WASM environments, the pure-Python wheel), the module
exposes ``HAS_NATIVE = False`` and the pure-Python paths in
``srmech.amsc.format`` etc. remain the only path.

Discipline (mirrors ``ephemerides_spectral._native_bip``):
- Callers MUST guard usage with ``if HAS_NATIVE: ...`` — every
  callsite has a pure-Python fallback.
- ABI version is checked at load time. A mismatch is treated as
  missing (``HAS_NATIVE = False``, ``LOAD_ERROR`` populated).
- Pure-Python is correctness; native is performance. The two paths
  produce byte-for-byte-identical output — pinned by the parity
  tests in ``tests/test_native_sha256.py`` (Phase B3) plus the
  cross-language test in ``c/test/test_parity_python.py``.

Bound functions match ``c/include/srmech.h``:

    const char *srmech_version(void)
    int srmech_abi_version(void)
    int srmech_sha256_hex(const uint8_t *data, size_t data_len,
                          char *out_hex)

Status codes (``srmech_status_t``):

    SRMECH_OK             = 0
    SRMECH_ERR_NULL_ARG   = 1
    SRMECH_ERR_BAD_INPUT  = 2
    SRMECH_ERR_IO         = 3
    SRMECH_ERR_OVERFLOW   = 4
    SRMECH_ERR_NOT_IMPL   = 5
    SRMECH_ERR_INTERNAL   = 6
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from typing import Optional


# Mirror of ``SRMECH_ABI_VERSION`` in srmech.h. Bump in lockstep with
# the C side whenever the wire format of any exported function
# changes.
#   v1 — Phase B3 baseline: srmech_sha256_hex.
EXPECTED_ABI_VERSION: int = 1


SRMECH_OK: int = 0
SRMECH_ERR_NULL_ARG: int = 1
SRMECH_ERR_BAD_INPUT: int = 2
SRMECH_ERR_IO: int = 3
SRMECH_ERR_OVERFLOW: int = 4
SRMECH_ERR_NOT_IMPL: int = 5
SRMECH_ERR_INTERNAL: int = 6


def _candidate_lib_names() -> list[str]:
    if sys.platform == "win32":
        # CMake's PREFIX="" override produces srmech.dll (matches
        # the ctypes lookup); fallback to libsrmech.dll if a
        # platform variant ever produces that name.
        return ["srmech.dll", "libsrmech.dll"]
    if sys.platform == "darwin":
        return ["libsrmech.dylib"]
    return ["libsrmech.so"]


def _find_library() -> Optional[Path]:
    """Search the bundled ``_native/`` directory for the shared library.

    Three search strategies in order, so editable installs +
    namespace-package layouts + regular wheel installs all work:

      1. Walk every entry in ``srmech.__path__`` (regular wheel install).
      2. Look one level up from this module file (defensive belt-and-
         braces; same path as 1 for regular installs).
      3. Use ``importlib.metadata.files()`` to enumerate every file
         the ``srmech`` distribution installed and pick out the one
         whose name matches our platform's lib pattern. This catches
         the scikit-build-core editable install case where the .py
         files live in the source tree (visible via __path__) but the
         CMake-installed .so/.dll/.dylib lives in site-packages
         (only visible via the installed-files manifest).
    """
    seen: set[Path] = set()
    candidates: list[Path] = []

    # Strategy 1: srmech.__path__ entries.
    try:
        import srmech  # local import to avoid bootstrap cycle
        candidates.extend(Path(p).resolve() / "_native" for p in srmech.__path__)
    except ImportError:
        pass

    # Strategy 2: relative to this module file.
    candidates.append(Path(__file__).resolve().parent.parent / "_native")

    for native_dir in candidates:
        if native_dir in seen:
            continue
        seen.add(native_dir)
        if not native_dir.exists():
            continue
        for name in _candidate_lib_names():
            p = native_dir / name
            if p.exists():
                return p

    # Strategy 3: importlib.metadata files manifest (editable installs).
    try:
        from importlib.metadata import files as _meta_files
        manifest = _meta_files("srmech")
        if manifest:
            wanted_names = set(_candidate_lib_names())
            for f in manifest:
                if Path(f.name).name in wanted_names:
                    located = Path(f.locate()).resolve()
                    if located.exists():
                        return located
    except Exception:
        pass

    return None


def _bind(lib: ctypes.CDLL) -> None:
    """Set argtypes / restype for every function we call into."""
    # const char *srmech_version(void)
    lib.srmech_version.argtypes = []
    lib.srmech_version.restype = ctypes.c_char_p

    # int srmech_abi_version(void)
    lib.srmech_abi_version.argtypes = []
    lib.srmech_abi_version.restype = ctypes.c_int

    # int srmech_sha256_hex(const uint8_t *, size_t, char *)
    lib.srmech_sha256_hex.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_char_p,
    ]
    lib.srmech_sha256_hex.restype = ctypes.c_int


_LIB_PATH: Optional[Path] = _find_library()
LIB: Optional[ctypes.CDLL] = None
HAS_NATIVE: bool = False
LOAD_ERROR: Optional[str] = None
NATIVE_ABI_VERSION: Optional[int] = None
NATIVE_VERSION: Optional[str] = None

if _LIB_PATH is not None:
    try:
        _candidate_lib = ctypes.CDLL(str(_LIB_PATH))
        # Bind first so we can call the metadata accessors.
        _bind(_candidate_lib)
        NATIVE_ABI_VERSION = int(_candidate_lib.srmech_abi_version())
        _v = _candidate_lib.srmech_version()
        NATIVE_VERSION = _v.decode("ascii") if isinstance(_v, bytes) else str(_v)
        if NATIVE_ABI_VERSION != EXPECTED_ABI_VERSION:
            LOAD_ERROR = (
                f"native lib at {_LIB_PATH}: ABI version mismatch "
                f"(got {NATIVE_ABI_VERSION}, expected {EXPECTED_ABI_VERSION}); "
                f"falling back to pure-Python paths"
            )
        else:
            LIB = _candidate_lib
            HAS_NATIVE = True
    except (OSError, AttributeError) as e:
        # OSError: couldn't load the .so/.dll/.dylib (missing symbol,
        # missing dep, ABI breakage from a stale half-installed wheel).
        # AttributeError: a bound symbol doesn't exist (stale .so from
        # an older srmech version). Either way, fall back cleanly.
        LOAD_ERROR = f"native lib at {_LIB_PATH}: load failed: {e!r}"


def sha256_hex_c(data: bytes) -> str:
    """Native SHA-256 — must only be called when HAS_NATIVE is True.

    Byte-exact with hashlib.sha256(data).hexdigest(). Empty bytes
    are valid (mirrors hashlib semantics).
    """
    if not HAS_NATIVE or LIB is None:
        raise RuntimeError(
            "srmech.amsc._native.sha256_hex_c called but HAS_NATIVE is False; "
            "use srmech.amsc.format.sha256_bytes (which dispatches correctly)"
        )
    out = ctypes.create_string_buffer(65)  # 64 hex chars + NUL
    # Empty bytes: pass a NULL pointer + 0 length, which the C side
    # tolerates (special-cased in srmech_sha256_hex).
    if len(data) == 0:
        rc = LIB.srmech_sha256_hex(
            ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8)),
            ctypes.c_size_t(0),
            out,
        )
    else:
        buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        rc = LIB.srmech_sha256_hex(buf, ctypes.c_size_t(len(data)), out)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_sha256_hex returned non-OK status {rc}; "
            f"this should not happen for valid inputs"
        )
    return out.value.decode("ascii")


__all__ = [
    "EXPECTED_ABI_VERSION",
    "HAS_NATIVE",
    "LIB",
    "LOAD_ERROR",
    "NATIVE_ABI_VERSION",
    "NATIVE_VERSION",
    "sha256_hex_c",
    "SRMECH_OK",
    "SRMECH_ERR_NULL_ARG",
    "SRMECH_ERR_BAD_INPUT",
    "SRMECH_ERR_IO",
    "SRMECH_ERR_OVERFLOW",
    "SRMECH_ERR_NOT_IMPL",
    "SRMECH_ERR_INTERNAL",
]
