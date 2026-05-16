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
#   v2 — Phase B4: srmech_ndjson_iter callback signature gained
#        `size_t lineno` (the callback typedef wire-format changed).
EXPECTED_ABI_VERSION: int = 2


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


# Callback type for srmech_ndjson_iter. Wire-format-locked by ABI v2:
#   typedef srmech_status_t (*srmech_ndjson_line_cb)(
#       const char *line, size_t line_len, size_t lineno, void *user);
# The wrapper bytes-buffer convention follows ctypes: c_char_p
# materialises the line as a Python bytes object (auto-NUL-terminated
# at line_len). We don't trust c_char_p NUL semantics in this codebase
# because JSON lines may contain embedded NULs in malformed inputs;
# use ctypes.string_at(ptr, length) to slice explicitly by length.
_NDJSON_LINE_CB = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,   # line — opaque pointer; we ctypes.string_at it
    ctypes.c_size_t,   # line_len
    ctypes.c_size_t,   # lineno (1-indexed over all lines including empty)
    ctypes.c_void_p,   # user (we pass None / NULL from Python)
)


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

    # int srmech_ndjson_iter(const char *path,
    #                        srmech_ndjson_line_cb cb,
    #                        void *user)
    lib.srmech_ndjson_iter.argtypes = [
        ctypes.c_char_p,
        _NDJSON_LINE_CB,
        ctypes.c_void_p,
    ]
    lib.srmech_ndjson_iter.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class I — cyclic-group / modular arithmetic (Task #217 Phase C1).
    # All six functions share the (uint64..., uint64 *out) -> int shape.
    # ------------------------------------------------------------------
    # int srmech_gcd(uint64_t a, uint64_t b, uint64_t *out)
    lib.srmech_gcd.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_gcd.restype = ctypes.c_int

    # int srmech_lcm(uint64_t a, uint64_t b, uint64_t *out)
    lib.srmech_lcm.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_lcm.restype = ctypes.c_int

    # int srmech_mod_add(uint64_t a, uint64_t b, uint64_t n, uint64_t *out)
    lib.srmech_mod_add.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_mod_add.restype = ctypes.c_int

    # int srmech_mod_mul(uint64_t a, uint64_t b, uint64_t n, uint64_t *out)
    lib.srmech_mod_mul.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_mod_mul.restype = ctypes.c_int

    # int srmech_mod_pow(uint64_t a, uint64_t k, uint64_t n, uint64_t *out)
    lib.srmech_mod_pow.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_mod_pow.restype = ctypes.c_int

    # int srmech_mod_inv(uint64_t a, uint64_t n, uint64_t *out)
    lib.srmech_mod_inv.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_mod_inv.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class L — graph Laplacian (Task #217 Phase C1 rc2).
    # All three matrix builders share the
    # (n, n_edges, *u, *v, *w, *out) -> int shape.
    # ------------------------------------------------------------------
    _GRAPH_BUILDER_ARGS = [
        ctypes.c_uint32,                    # n
        ctypes.c_uint32,                    # n_edges
        ctypes.POINTER(ctypes.c_uint32),    # edges_u
        ctypes.POINTER(ctypes.c_uint32),    # edges_v
        ctypes.POINTER(ctypes.c_double),    # weights (or NULL)
        ctypes.POINTER(ctypes.c_double),    # out_matrix (n*n doubles)
    ]
    lib.srmech_graph_dense_adjacency.argtypes = _GRAPH_BUILDER_ARGS
    lib.srmech_graph_dense_adjacency.restype = ctypes.c_int

    lib.srmech_graph_dense_laplacian.argtypes = _GRAPH_BUILDER_ARGS
    lib.srmech_graph_dense_laplacian.restype = ctypes.c_int

    lib.srmech_graph_normalized_laplacian.argtypes = _GRAPH_BUILDER_ARGS
    lib.srmech_graph_normalized_laplacian.restype = ctypes.c_int

    # int srmech_jacobi_eigvals(uint32_t n, double *matrix,
    #                           uint32_t max_sweeps, double tolerance,
    #                           double *out_eigvals)
    lib.srmech_jacobi_eigvals.argtypes = [
        ctypes.c_uint32,                    # n
        ctypes.POINTER(ctypes.c_double),    # matrix (in-place)
        ctypes.c_uint32,                    # max_sweeps
        ctypes.c_double,                    # tolerance
        ctypes.POINTER(ctypes.c_double),    # out_eigvals (n doubles)
    ]
    lib.srmech_jacobi_eigvals.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class J — prime-factorisation / period (Task #217 Phase C1 rc3).
    # ------------------------------------------------------------------
    # int srmech_is_prime(uint64_t n, bool *out)
    lib.srmech_is_prime.argtypes = [
        ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool),
    ]
    lib.srmech_is_prime.restype = ctypes.c_int

    # int srmech_factor(uint64_t n, uint64_t *primes, uint8_t *exps,
    #                   uint32_t max_count, uint32_t *out_count)
    lib.srmech_factor.argtypes = [
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.srmech_factor.restype = ctypes.c_int

    # int srmech_cyclic_period(uint64_t a, uint64_t n, uint64_t max_k,
    #                          uint64_t *out_period)
    lib.srmech_cyclic_period.argtypes = [
        ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_cyclic_period.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class B (tagged-tuple TLV) — Task #217 Phase C1 rc4.
    # ------------------------------------------------------------------
    # int srmech_tlv_pack(uint8_t tag, const uint8_t *value,
    #                     uint32_t value_len, uint8_t *out, uint32_t cap,
    #                     uint32_t *out_written)
    lib.srmech_tlv_pack.argtypes = [
        ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.srmech_tlv_pack.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class G (byte-pattern search) — Task #217 Phase C1 rc4.
    # ------------------------------------------------------------------
    # int srmech_byte_search(const uint8_t *haystack, uint32_t h_len,
    #                        const uint8_t *needle, uint32_t n_len,
    #                        uint32_t *out_offset)
    lib.srmech_byte_search.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.srmech_byte_search.restype = ctypes.c_int


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


class NativeNDJsonError(Exception):
    """srmech_ndjson_iter returned a non-OK status.

    Distinct from MPRValidationError because the failure is upstream
    of JSON parsing — it's a file-IO or buffer-overflow error from
    the C layer, not a per-record validation failure.
    """

    def __init__(self, status: int, path: str) -> None:
        self.status = status
        self.path = path
        kind = {
            SRMECH_ERR_NULL_ARG: "NULL_ARG",
            SRMECH_ERR_IO: "IO (fopen / fread failed)",
            SRMECH_ERR_OVERFLOW: f"OVERFLOW (line exceeded "
                                 f"SRMECH_NDJSON_MAX_LINE_BYTES = 1 MiB)",
        }.get(status, f"status {status}")
        super().__init__(f"srmech_ndjson_iter({path!r}) failed: {kind}")


def ndjson_lines_c(path: str) -> list[tuple[int, bytes]]:
    """Read an NDJSON file via the native loader.

    Returns a list of ``(lineno, line_bytes)`` tuples, one per
    non-empty line in the file. ``lineno`` is 1-indexed over ALL
    lines in the file (including the skipped empty ones), so
    callsites can use it directly in error messages and the numbers
    line up with what an editor shows.

    The Python side then runs ``json.loads`` (and
    ``MPRRecord.from_json_line``) on each line. JSON parsing stays
    in Python; the C side just does the IO + line tokenisation.

    Must only be called when ``HAS_NATIVE`` is True.

    Raises ``NativeNDJsonError`` on file-IO or overflow failure.
    """
    if not HAS_NATIVE or LIB is None:
        raise RuntimeError(
            "srmech.amsc._native.ndjson_lines_c called but HAS_NATIVE "
            "is False; use srmech.amsc.format.read_ndjson (which "
            "dispatches correctly)"
        )

    results: list[tuple[int, bytes]] = []

    def _on_line(line_ptr: int,
                 line_len: int,
                 lineno: int,
                 _user: int) -> int:
        # ctypes.string_at slices exactly line_len bytes starting at
        # line_ptr — safe even if the line contains embedded NULs.
        # We hold the GIL inside this callback (ctypes does that
        # automatically for CFUNCTYPE wrappers), so list.append is
        # thread-safe vs. the calling thread.
        line_bytes = ctypes.string_at(line_ptr, line_len)
        results.append((lineno, line_bytes))
        return SRMECH_OK

    cb = _NDJSON_LINE_CB(_on_line)
    rc = LIB.srmech_ndjson_iter(
        path.encode("utf-8"),
        cb,
        None,
    )
    if rc != SRMECH_OK:
        raise NativeNDJsonError(rc, path)
    return results


__all__ = [
    "EXPECTED_ABI_VERSION",
    "HAS_NATIVE",
    "LIB",
    "LOAD_ERROR",
    "NATIVE_ABI_VERSION",
    "NATIVE_VERSION",
    "NativeNDJsonError",
    "ndjson_lines_c",
    "sha256_hex_c",
    "SRMECH_OK",
    "SRMECH_ERR_NULL_ARG",
    "SRMECH_ERR_BAD_INPUT",
    "SRMECH_ERR_IO",
    "SRMECH_ERR_OVERFLOW",
    "SRMECH_ERR_NOT_IMPL",
    "SRMECH_ERR_INTERNAL",
]
