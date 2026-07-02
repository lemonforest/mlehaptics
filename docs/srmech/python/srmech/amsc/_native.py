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
import json
import os
import sys
from pathlib import Path
from typing import Optional


# Mirror of ``SRMECH_ABI_VERSION`` in srmech.h. Bump in lockstep with
# the C side whenever the wire format of any exported function
# changes.
#   v1 — Phase B3 baseline: srmech_sha256_hex.
#   v2 — Phase B4: srmech_ndjson_iter callback signature gained
#        `size_t lineno` (the callback typedef wire-format changed).
#   v3 — v0.5.0rc2: srmech_bus_* C peer; new function-pointer typedef
#        srmech_bus_handler_callback_t. Adding a typedef carries a
#        wire-format implication for the Python ctypes shim
#        (CFUNCTYPE construction), so ABI bumps.
EXPECTED_ABI_VERSION: int = 3

# Back-compat alias: downstream code reading ``_native.ABI_VERSION`` gets the
# expected (compiled-against) ABI == EXPECTED_ABI_VERSION (NOT the runtime-
# detected NATIVE_ABI_VERSION, which is None when no native lib is present).
ABI_VERSION: int = EXPECTED_ABI_VERSION


SRMECH_OK: int = 0
SRMECH_ERR_NULL_ARG: int = 1
SRMECH_ERR_BAD_INPUT: int = 2
SRMECH_ERR_IO: int = 3
SRMECH_ERR_OVERFLOW: int = 4
SRMECH_ERR_NOT_IMPL: int = 5
SRMECH_ERR_INTERNAL: int = 6


# Class L broadening (Phase 2): transcendental op-id enum.
# Mirrors SRMECH_TRANS_{EXP,COS,SIN,LOG} in c/include/srmech.h.
SRMECH_TRANS_EXP: int = 0
SRMECH_TRANS_COS: int = 1
SRMECH_TRANS_SIN: int = 2
SRMECH_TRANS_LOG: int = 3


# Mirror of ``srmech_bigint_t`` in c/include/srmech.h — the caller-arena,
# arbitrary-precision integer carrier (base-2^32 little-endian sign-magnitude
# over caller-owned limbs). Used by the rc35 bignum-exact transcendental
# series (srmech_*_series_truncate_big / srmech_rational_pow_uint_big) to
# marshal exact-rational (num, den) operands + results. Layout MUST match:
#   { int32_t sign; uint32_t n; uint32_t cap; uint32_t *limbs }.
class _SrmechBigint(ctypes.Structure):
    _fields_ = [
        ("sign", ctypes.c_int32),
        ("n", ctypes.c_uint32),
        ("cap", ctypes.c_uint32),
        ("limbs", ctypes.POINTER(ctypes.c_uint32)),
    ]


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


# rc8 chiral_dual: higher-order callback ABI for Class C ∘ op ∘ Class C.
# The callback signature must match the C typedef
# srmech_cascade_op_callback_f64_t exactly:
#
#   typedef srmech_status_t (*srmech_cascade_op_callback_f64_t)(
#       const double *in, size_t n, double *out, void *user_data);
#
# Exposed at module scope (not inside _bind) so the Python dispatch in
# srmech.amsc.cascade can construct callback instances without reaching
# into the library-binding closure.
CASCADE_OP_CALLBACK_F64 = ctypes.CFUNCTYPE(
    ctypes.c_int,                            # srmech_status_t return
    ctypes.POINTER(ctypes.c_double),         # const double *in
    ctypes.c_size_t,                          # size_t n
    ctypes.POINTER(ctypes.c_double),         # double *out
    ctypes.c_void_p,                          # void *user_data
)


# v0.6.0rc7 (#771): the cascade `body` callback ABI for the Klein-4
# four-sector PARALLEL dispatch C peer. Mirror of the C typedef
#
#   typedef srmech_status_t (*srmech_cascade_body_f64)(
#       const double *in, size_t n, double *out, void *user);
#
# Same wire-shape as CASCADE_OP_CALLBACK_F64 (named separately for the
# dispatch role; identical ctypes signature).
#
# GIL + CONCURRENCY (v0.6.0rc8 — empirically settled). The C dispatch
# spawns up to 4 threads (pthread / CreateThread) and invokes this
# callback from EACH of them. ctypes invokes a CFUNCTYPE callback from a
# foreign (C-spawned) thread SAFELY — it acquires the GIL via
# PyGILState_Ensure (creating a thread-state on demand) for the duration
# of the callback and releases it after. So the multi-sector threaded
# fan-out with a Python body IS safe, and the shim below drives ONE
# n_sectors=N dispatch (not N serial n_sectors=1 calls). Concurrency:
# srmech's ctypes CDLL releases the GIL across the dispatch call, so a
# GIL-RELEASING body (native / IO / numpy / sleep) lets the <=4 callback
# threads genuinely OVERLAP — measured ~4x on a sleep body (rc8 fix for
# the rc7 serial-shim slowdown). A CPU-bound PURE-Python body is still
# GIL-serialised across threads (the inherent CPython limit; Python 3.13
# free-threading lifts it) — correct, just not faster.
CASCADE_BODY_CALLBACK_F64 = CASCADE_OP_CALLBACK_F64


# v0.5.0rc2: srmech.bus handler-dispatch callback ABI. Mirror of the
# C typedef in srmech.h:
#
#   typedef srmech_status_t (*srmech_bus_handler_callback_t)(
#       const uint8_t *request, size_t request_len,
#       uint8_t       *response, size_t *response_len_inout,
#       void          *user_data);
#
# Exposed at module scope so srmech.bus dispatch can construct
# trampolines without reaching into the closure. Same rationale as
# CASCADE_OP_CALLBACK_F64.
BUS_HANDLER_CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,                            # srmech_status_t return
    ctypes.c_void_p,                          # const uint8_t *request
    ctypes.c_size_t,                          # size_t request_len
    ctypes.c_void_p,                          # uint8_t *response
    ctypes.POINTER(ctypes.c_size_t),         # size_t *response_len_inout
    ctypes.c_void_p,                          # void *user_data
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

    # v0.7.0rc10 (F292 graft #1): N-way SIMD SHA-256 batch. NEW symbol —
    # hasattr-guarded so a stale lib built before rc10 doesn't disable the
    # whole native surface (same best-effort pattern as the cascade/polar/
    # klein4 blocks below).
    #   int srmech_sha256_batch(const uint8_t *const *msgs,
    #                           const size_t *lens, size_t n,
    #                           uint8_t *out_digests)   /* n*32 bytes */
    if hasattr(lib, "srmech_sha256_batch"):
        lib.srmech_sha256_batch.argtypes = [
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.srmech_sha256_batch.restype = ctypes.c_int

    # v0.7.0rc18 (F292 graft #3): SHA-NI single-stream SHA-256. NEW symbol —
    # hasattr-guarded (stale-lib-safe). Writes the RAW 32-byte digest; the
    # Python wrapper hexlifies. Internally dispatches scalar-or-SHA-NI by
    # cpuid, so this is bit-exact + safe on hosts without the SHA feature.
    #   int srmech_sha256_shani(const uint8_t *data, size_t len,
    #                           uint8_t *out_digest)   /* 32 bytes */
    if hasattr(lib, "srmech_sha256_shani"):
        lib.srmech_sha256_shani.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.srmech_sha256_shani.restype = ctypes.c_int

    # v0.7.0rc18: SIMD HAL host-capability probe (exported via
    # WINDOWS_EXPORT_ALL_SYMBOLS). Lets native_status() / the parity test
    # see whether THIS run's host carries the SHA feature (so the SHA-NI
    # kernel is exercise-if-present / skip-with-log, not silently assumed).
    #   int srmech_simd_has_shani(void)
    if hasattr(lib, "srmech_simd_has_shani"):
        lib.srmech_simd_has_shani.argtypes = []
        lib.srmech_simd_has_shani.restype = ctypes.c_int

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
    # Class L broadening (ADR-0002 Phase 2 / v0.4.1rc5).
    # Complex numbers travel as interleaved-double pairs (re, im).
    # ------------------------------------------------------------------
    # int srmech_hermitian_eigendecompose_ws(uint32_t n,
    #     const double *H_il, double *out_eigvals,
    #     double *out_eigvecs_il, double *workspace, size_t ws_len)
    # Reentrant variant taking a caller-supplied 2*n*n-double workspace, so the
    # native Jacobi path serves n up to the CONFIG-DRIVEN ceiling
    # (srmech_config_hermitian_max_nodes(), default 2048) with no static/stack
    # buffer. (rc161 removed the older no-`_ws` srmech_hermitian_eigendecompose
    # — it self-buffered a 1 MiB thread-local static + an n≤256 cap and had no
    # live caller; the `_ws` entry is the only native Hermitian path now.)
    # hasattr-guarded (ABI stays 3 — additive symbol) so a stale ABI-3 lib
    # built before this rc keeps the rest of the native surface instead of
    # AttributeError-ing here.
    if hasattr(lib, "srmech_hermitian_eigendecompose_ws"):
        lib.srmech_hermitian_eigendecompose_ws.argtypes = [
            ctypes.c_uint32,                    # n
            ctypes.POINTER(ctypes.c_double),    # H_il
            ctypes.POINTER(ctypes.c_double),    # out_eigvals (n doubles)
            ctypes.POINTER(ctypes.c_double),    # out_eigvecs_il (2*n*n)
            ctypes.POINTER(ctypes.c_double),    # workspace (ws_len doubles)
            ctypes.c_size_t,                    # ws_len
        ]
        lib.srmech_hermitian_eigendecompose_ws.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Config layer (rc161) — the Hermitian-eig compute-guard ceiling is a
    # RUNTIME config value, not a compiled-in #define. The getter is the
    # authority for the native dispatch gate in laplacian.py; load_toml /
    # load_file / reset let a caller tune it (a TOML blob in RAM, or a file
    # read through the PAL). All hasattr-guarded → additive, ABI stays 3.
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_config_hermitian_max_nodes"):
        # uint32_t srmech_config_hermitian_max_nodes(void)
        lib.srmech_config_hermitian_max_nodes.argtypes = []
        lib.srmech_config_hermitian_max_nodes.restype = ctypes.c_uint32
    if hasattr(lib, "srmech_config_reset_defaults"):
        # void srmech_config_reset_defaults(void)
        lib.srmech_config_reset_defaults.argtypes = []
        lib.srmech_config_reset_defaults.restype = None
    if hasattr(lib, "srmech_config_load_toml"):
        # int srmech_config_load_toml(const char *toml, size_t len,
        #     void *ws, size_t ws_len)
        lib.srmech_config_load_toml.argtypes = [
            ctypes.c_char_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_config_load_toml.restype = ctypes.c_int
    if hasattr(lib, "srmech_config_load_file"):
        # int srmech_config_load_file(const char *path, void *ws, size_t ws_len)
        lib.srmech_config_load_file.argtypes = [
            ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_config_load_file.restype = ctypes.c_int

    # int srmech_elementwise_multiply_complex(uint32_t n,
    #     const double *a_il, const double *b_il, double *out_il)
    lib.srmech_elementwise_multiply_complex.argtypes = [
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_elementwise_multiply_complex.restype = ctypes.c_int

    # int srmech_elementwise_transcendental(uint32_t n,
    #     const double *arr, int op_id, double *out)
    lib.srmech_elementwise_transcendental.argtypes = [
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_elementwise_transcendental.restype = ctypes.c_int

    # size_t srmech_dense_solve_arena_bytes(uint32_t n, uint32_t nrhs)
    # int srmech_dense_solve_f64_ws(uint32_t n, uint32_t nrhs,
    #     const double *A, const double *B, double *out_X,
    #     void *ws, size_t ws_len)
    # v0.7.5rc158 standalone-complete honor: the augmented [A|B] scratch is
    # carved from a CALLER arena (no compiled-in 256 cap), so the bound is the
    # caller's RAM. mat_solve sizes ws via srmech_dense_solve_arena_bytes. Both
    # symbols hasattr-guarded — a stale lib (the old capped srmech_dense_solve_f64,
    # now removed) lacks them, so EXPECTED_ABI_VERSION stays 3 and that lib falls
    # to the pure-Python exact-rational solve (the complete alternative impl).
    if hasattr(lib, "srmech_dense_solve_arena_bytes"):
        lib.srmech_dense_solve_arena_bytes.argtypes = [
            ctypes.c_uint32,                    # n
            ctypes.c_uint32,                    # nrhs
        ]
        lib.srmech_dense_solve_arena_bytes.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_dense_solve_f64_ws"):
        lib.srmech_dense_solve_f64_ws.argtypes = [
            ctypes.c_uint32,                    # n
            ctypes.c_uint32,                    # nrhs
            ctypes.POINTER(ctypes.c_double),    # A (n*n, row-major)
            ctypes.POINTER(ctypes.c_double),    # B (n*nrhs, row-major)
            ctypes.POINTER(ctypes.c_double),    # out_X (n*nrhs, row-major)
            ctypes.c_void_p,                    # ws (caller arena)
            ctypes.c_size_t,                    # ws_len (arena bytes)
        ]
        lib.srmech_dense_solve_f64_ws.restype = ctypes.c_int

    # int srmech_exact_dft_i64(uint32_t n, int inverse, const int64_t *re,
    #     const int64_t *im, int64_t *out_re, int64_t *out_im)
    # v0.7.5rc29 additive symbol (#928): the exact cyclotomic-integer DFT —
    # a power-of-two integer signal → exact ℤ[ζ_N] spectrum by pure integer
    # add/subtract. out_re/out_im are length n*(n/2) int64. hasattr-guarded
    # (EXPECTED_ABI_VERSION stays 3; a stale ABI-3 lib lacks the symbol).
    if hasattr(lib, "srmech_exact_dft_i64"):
        lib.srmech_exact_dft_i64.argtypes = [
            ctypes.c_uint32,                    # n
            ctypes.c_int,                       # inverse (0/1)
            ctypes.POINTER(ctypes.c_int64),     # re (n)
            ctypes.POINTER(ctypes.c_int64),     # im (n)
            ctypes.POINTER(ctypes.c_int64),     # out_re (n*(n/2))
            ctypes.POINTER(ctypes.c_int64),     # out_im (n*(n/2))
        ]
        lib.srmech_exact_dft_i64.restype = ctypes.c_int

    # int srmech_dense_matmul_complex(uint32_t m, uint32_t k, uint32_t n,
    #     const double *A_il, const double *B_il, double *out_il)
    # v0.7.5rc14 additive symbol (#928, matmul-kernel phase): the dense complex
    # matrix-matrix product (m,k)@(k,n)=(m,n) the QM / matrix_cascades layer's
    # ``@`` math routes through. hasattr-guarded (ABI stays 3) so a stale ABI-3
    # lib keeps the rest of the native surface.
    if hasattr(lib, "srmech_dense_matmul_complex"):
        lib.srmech_dense_matmul_complex.argtypes = [
            ctypes.c_uint32,                    # m
            ctypes.c_uint32,                    # k
            ctypes.c_uint32,                    # n
            ctypes.POINTER(ctypes.c_double),    # A (m*k interleaved, row-major)
            ctypes.POINTER(ctypes.c_double),    # B (k*n interleaved, row-major)
            ctypes.POINTER(ctypes.c_double),    # out (m*n interleaved, row-major)
        ]
        lib.srmech_dense_matmul_complex.restype = ctypes.c_int

    # §75 (F928): the resonant-spectrum closure — the C twin of
    # srmech.amsc.coupling.resonant_spectrum. A Class-L coupling composite over
    # srmech_hermitian_eigendecompose_ws + srmech_best_rational + srmech_factor.
    # NEW symbols, hasattr-guarded (ABI stays 3) so a stale ABI-3 lib keeps the
    # rest of the native surface and the pure-Python op is the complete path.
    #   size_t srmech_resonant_spectrum_arena_bytes(uint32_t n)
    if hasattr(lib, "srmech_resonant_spectrum_arena_bytes"):
        lib.srmech_resonant_spectrum_arena_bytes.argtypes = [ctypes.c_uint32]
        lib.srmech_resonant_spectrum_arena_bytes.restype = ctypes.c_size_t
    #   int srmech_resonant_spectrum(uint32_t n, const double *L_rowmajor,
    #       uint32_t orders, uint64_t max_den, double *out_tensions,
    #       double *out_modes, double *out_force_orders, int32_t *out_res_pairs,
    #       uint64_t *out_res_ratio, int32_t *out_res_locked,
    #       uint32_t *out_res_count, double *ws, size_t ws_len)
    if hasattr(lib, "srmech_resonant_spectrum"):
        lib.srmech_resonant_spectrum.argtypes = [
            ctypes.c_uint32,                    # n
            ctypes.POINTER(ctypes.c_double),    # L_rowmajor (n*n real)
            ctypes.c_uint32,                    # orders
            ctypes.c_uint64,                    # max_den
            ctypes.POINTER(ctypes.c_double),    # out_tensions (n)
            ctypes.POINTER(ctypes.c_double),    # out_modes (n*n real, columns)
            ctypes.POINTER(ctypes.c_double),    # out_force_orders (orders*n*n)
            ctypes.POINTER(ctypes.c_int32),     # out_res_pairs ((n-1)*2)
            ctypes.POINTER(ctypes.c_uint64),    # out_res_ratio ((n-1)*2)
            ctypes.POINTER(ctypes.c_int32),     # out_res_locked (n-1)
            ctypes.POINTER(ctypes.c_uint32),    # out_res_count
            ctypes.POINTER(ctypes.c_double),    # ws (caller arena)
            ctypes.c_size_t,                    # ws_len (arena bytes)
        ]
        lib.srmech_resonant_spectrum.restype = ctypes.c_int

    # v0.7.2rc2 (#910 / §30; F442/F449): Hamming / GF(2) block-code family.
    # NEW symbols — hasattr-guarded so a stale lib (pre-rc2) keeps the rest of
    # the native surface. uint8 0/1 buffers; lean-ALU XOR (no float, no libm).
    #   int srmech_hamming_encode(const uint8_t *data, size_t k, int n,
    #                             uint8_t *out_codeword)
    if hasattr(lib, "srmech_hamming_encode"):
        lib.srmech_hamming_encode.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),     # data (k bits)
            ctypes.c_size_t,                    # k
            ctypes.c_int,                       # n (parity-bit count)
            ctypes.POINTER(ctypes.c_uint8),     # out_codeword (2^n-1 bits)
        ]
        lib.srmech_hamming_encode.restype = ctypes.c_int
    #   int srmech_hamming_syndrome(const uint8_t *codeword, size_t len,
    #                               int *out_pos)
    if hasattr(lib, "srmech_hamming_syndrome"):
        lib.srmech_hamming_syndrome.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),     # codeword (len bits)
            ctypes.c_size_t,                    # len
            ctypes.POINTER(ctypes.c_int),       # out_pos (1-indexed; 0 clean)
        ]
        lib.srmech_hamming_syndrome.restype = ctypes.c_int
    #   int srmech_hamming_decode_correct(const uint8_t *codeword, size_t len,
    #                                     uint8_t *out_data, int *out_pos)
    if hasattr(lib, "srmech_hamming_decode_correct"):
        lib.srmech_hamming_decode_correct.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),     # codeword (len bits)
            ctypes.c_size_t,                    # len
            ctypes.POINTER(ctypes.c_uint8),     # out_data (len-n bits)
            ctypes.POINTER(ctypes.c_int),       # out_pos
        ]
        lib.srmech_hamming_decode_correct.restype = ctypes.c_int

    # Cayley-Dickson basis-unit cocycle (v0.7.3rc1; #915 / MFO §VII.6.23) — the
    # integer structural core of the open-exterior demonstrator. hasattr-guarded
    # so a stale lib (pre-rc1) keeps the rest of the native surface.
    #   int srmech_cd_basis_product(int dim, int i, int j,
    #                               int *out_index, int *out_sign)
    if hasattr(lib, "srmech_cd_basis_product"):
        lib.srmech_cd_basis_product.argtypes = [
            ctypes.c_int,                       # dim (power of two <= 64)
            ctypes.c_int,                       # i (basis index)
            ctypes.c_int,                       # j (basis index)
            ctypes.POINTER(ctypes.c_int),       # out_index (== i ^ j)
            ctypes.POINTER(ctypes.c_int),       # out_sign (+1 / -1)
        ]
        lib.srmech_cd_basis_product.restype = ctypes.c_int

    # Qi exact-complex (Gaussian-rational) carrier C-host peer (0.9.0rc15) —
    # carrier-internal (NOT a Rosetta op), four int64 limbs {re_num, re_den,
    # im_num, im_den}. hasattr-guarded so a stale lib (pre-rc15) keeps the rest.
    #   int srmech_qi_{add,sub,mul}(const int64_t a[4], const int64_t b[4],
    #                               int64_t out[4])
    for _qi_op in ("srmech_qi_add", "srmech_qi_sub", "srmech_qi_mul"):
        if hasattr(lib, _qi_op):
            getattr(lib, _qi_op).argtypes = [
                ctypes.POINTER(ctypes.c_int64),     # a[4]
                ctypes.POINTER(ctypes.c_int64),     # b[4]
                ctypes.POINTER(ctypes.c_int64),     # out[4]
            ]
            getattr(lib, _qi_op).restype = ctypes.c_int
    #   int srmech_qi_conjugate(const int64_t a[4], int64_t out[4])
    if hasattr(lib, "srmech_qi_conjugate"):
        lib.srmech_qi_conjugate.argtypes = [
            ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int64)]
        lib.srmech_qi_conjugate.restype = ctypes.c_int
    #   int srmech_qi_quadrant(const int64_t a[4], int *out_quadrant)
    if hasattr(lib, "srmech_qi_quadrant"):
        lib.srmech_qi_quadrant.argtypes = [
            ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int)]
        lib.srmech_qi_quadrant.restype = ctypes.c_int
    #   int srmech_qi_norm_sq(const int64_t a[4], int64_t out[2])
    if hasattr(lib, "srmech_qi_norm_sq"):
        lib.srmech_qi_norm_sq.argtypes = [
            ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int64)]
        lib.srmech_qi_norm_sq.restype = ctypes.c_int

    # Exact-Q61 (σ,θ,μ) octonion coupler C-host peer (0.9.0rc16) — the
    # hypercomplex_couple rewrite that closes the rc12 sed_couple/uncouple
    # transitive-ratchet allowlist. hasattr-guarded (pre-rc16 lib keeps the rest).
    #   int srmech_hypercomplex_couple_q61(double eff, const int64_t streams[8],
    #       const int64_t mu[8], int form_is_left, int64_t out[8])
    if hasattr(lib, "srmech_hypercomplex_couple_q61"):
        lib.srmech_hypercomplex_couple_q61.argtypes = [
            ctypes.c_double,                    # eff = sigma*(-1 if inv)*theta
            ctypes.POINTER(ctypes.c_int64),     # streams[8] (Q61)
            ctypes.POINTER(ctypes.c_int64),     # mu[8] (Q61, unit pure-imag)
            ctypes.c_int,                       # form_is_left (1=left, 0=right)
            ctypes.POINTER(ctypes.c_int64),     # out[8] (Q61)
        ]
        lib.srmech_hypercomplex_couple_q61.restype = ctypes.c_int

    # Sedenion address layer (v0.9.0rc12; UPSTREAM §31 / F465+F468) — the
    # navigation + reversibility gate a C-only host needs for "Siona's address
    # layer." hasattr-guarded so a stale lib (pre-rc12) keeps the rest.
    #   int srmech_sedenion_navmap(int j, int *out_dest, int *out_sign)
    if hasattr(lib, "srmech_sedenion_navmap"):
        lib.srmech_sedenion_navmap.argtypes = [
            ctypes.c_int,                       # j (basis direction)
            ctypes.POINTER(ctypes.c_int),       # out_dest[16]
            ctypes.POINTER(ctypes.c_int),       # out_sign[16]
        ]
        lib.srmech_sedenion_navmap.restype = ctypes.c_int
    #   int srmech_sedenion_navigate(int j, const int *in_slots,
    #       const int *in_signs, size_t count, int *out_slots, int *out_signs)
    if hasattr(lib, "srmech_sedenion_navigate"):
        lib.srmech_sedenion_navigate.argtypes = [
            ctypes.c_int,                       # j
            ctypes.POINTER(ctypes.c_int),       # in_slots
            ctypes.POINTER(ctypes.c_int),       # in_signs (+1/-1)
            ctypes.c_size_t,                    # count
            ctypes.POINTER(ctypes.c_int),       # out_slots
            ctypes.POINTER(ctypes.c_int),       # out_signs
        ]
        lib.srmech_sedenion_navigate.restype = ctypes.c_int
    #   int srmech_sedenion_is_navigable(const int64_t *direction, size_t n,
    #                                    int *out_invertible)  (modular rank)
    if hasattr(lib, "srmech_sedenion_is_navigable"):
        lib.srmech_sedenion_is_navigable.argtypes = [
            ctypes.POINTER(ctypes.c_int64),     # direction (integer vector)
            ctypes.c_size_t,                    # n (power of two <= 64)
            ctypes.POINTER(ctypes.c_int),       # out_invertible (0/1)
        ]
        lib.srmech_sedenion_is_navigable.restype = ctypes.c_int

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

    # rc44: int srmech_next_prime(uint64_t n, uint64_t *out) — the prime
    # successor (Class J). NEW symbol — hasattr-guarded so a stale pre-rc44 lib
    # keeps the rest of the native surface (ABI stays 3; pure-Python is complete).
    if hasattr(lib, "srmech_next_prime"):
        lib.srmech_next_prime.argtypes = [
            ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
        ]
        lib.srmech_next_prime.restype = ctypes.c_int

    # rc44: int srmech_gf_rref(int64_t *matrix, uint32_t n_rows, uint32_t n_cols,
    #     uint64_t p, uint32_t *out_pivots, uint32_t *out_rank) — the swell-free
    # GF(p) reduced-row-echelon kernel (Class I modular linear algebra, rung 1 of
    # the CRT-QMat re-fibration arc). In-place over a caller-owned row-major int64
    # buffer; pivots + rank into caller buffers. NEW symbol — hasattr-guarded (ABI
    # stays 3; the pure-Python srmech.amsc.modular_linalg.gf_rref is complete).
    if hasattr(lib, "srmech_gf_rref"):
        lib.srmech_gf_rref.argtypes = [
            ctypes.POINTER(ctypes.c_int64),     # matrix (n_rows*n_cols, row-major)
            ctypes.c_uint32,                    # n_rows
            ctypes.c_uint32,                    # n_cols
            ctypes.c_uint64,                    # p (2 < p < 2**31)
            ctypes.POINTER(ctypes.c_uint32),    # out_pivots (>= min(rows,cols))
            ctypes.POINTER(ctypes.c_uint32),    # out_rank
        ]
        lib.srmech_gf_rref.restype = ctypes.c_int

    # rc45: the CRT closers (rung 2 of the CRT-QMat re-fibration arc), both over
    # the caller-arena srmech_bigint (the combined modulus + reconstructed
    # numerator/denominator are bignum). NEW symbols — hasattr-guarded so a stale
    # pre-rc45 lib keeps the rest of the native surface (ABI stays 3; the
    # pure-Python bodies in modular_linalg / rational are complete).
    #
    # size_t srmech_crt_combine_ws_bound(size_t k)
    # srmech_status_t srmech_crt_combine(const uint64_t *residues,
    #     const uint64_t *moduli, uint32_t k, srmech_bigint_t *out_residue,
    #     srmech_bigint_t *out_modulus, void *ws, size_t ws_len)
    if hasattr(lib, "srmech_crt_combine_ws_bound"):
        lib.srmech_crt_combine_ws_bound.argtypes = [ctypes.c_size_t]
        lib.srmech_crt_combine_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_crt_combine"):
        lib.srmech_crt_combine.argtypes = [
            ctypes.POINTER(ctypes.c_uint64),     # residues[k]
            ctypes.POINTER(ctypes.c_uint64),     # moduli[k]
            ctypes.c_uint32,                     # k
            ctypes.POINTER(_SrmechBigint),       # out_residue (bignum)
            ctypes.POINTER(_SrmechBigint),       # out_modulus (bignum)
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_crt_combine.restype = ctypes.c_int

    # size_t srmech_rational_reconstruct_ws_bound(size_t modulus_limbs)
    # srmech_status_t srmech_rational_reconstruct(const srmech_bigint_t *residue,
    #     const srmech_bigint_t *modulus, const srmech_bigint_t *num_bound,
    #     const srmech_bigint_t *den_bound, srmech_bigint_t *out_num,
    #     srmech_bigint_t *out_den, int32_t *out_found, void *ws, size_t ws_len)
    if hasattr(lib, "srmech_rational_reconstruct_ws_bound"):
        lib.srmech_rational_reconstruct_ws_bound.argtypes = [ctypes.c_size_t]
        lib.srmech_rational_reconstruct_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_rational_reconstruct"):
        lib.srmech_rational_reconstruct.argtypes = [
            ctypes.POINTER(_SrmechBigint),       # residue
            ctypes.POINTER(_SrmechBigint),       # modulus
            ctypes.POINTER(_SrmechBigint),       # num_bound
            ctypes.POINTER(_SrmechBigint),       # den_bound
            ctypes.POINTER(_SrmechBigint),       # out_num
            ctypes.POINTER(_SrmechBigint),       # out_den
            ctypes.POINTER(ctypes.c_int32),      # out_found (1 = found, 0 = None)
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_rational_reconstruct.restype = ctypes.c_int

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

    # ------------------------------------------------------------------
    # Class D (dispatch / multi-needle pattern match) — Phase C1 rc5.
    # int srmech_dispatch_match(input, in_len, patterns_buf,
    #                           pat_offsets, pat_lengths, tags, n_rules,
    #                           *out_matched, *out_tag)
    # ------------------------------------------------------------------
    lib.srmech_dispatch_match.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),     # input
        ctypes.c_uint32,                    # input_len
        ctypes.POINTER(ctypes.c_uint8),     # patterns_buffer
        ctypes.POINTER(ctypes.c_uint32),    # pattern_offsets
        ctypes.POINTER(ctypes.c_uint32),    # pattern_lengths
        ctypes.POINTER(ctypes.c_uint32),    # tags
        ctypes.c_uint32,                    # n_rules
        ctypes.POINTER(ctypes.c_bool),      # out_matched
        ctypes.POINTER(ctypes.c_uint32),    # out_tag
    ]
    lib.srmech_dispatch_match.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class E (catalog / sorted-key lookup) — Phase C1 rc5.
    # int srmech_catalog_lookup(key, key_len, keys_buf, key_offsets,
    #                           key_lengths, values_buf, value_offsets,
    #                           value_lengths, n_entries,
    #                           *out_found, *out_value_offset,
    #                           *out_value_length)
    # ------------------------------------------------------------------
    lib.srmech_catalog_lookup.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),     # key
        ctypes.c_uint32,                    # key_len
        ctypes.POINTER(ctypes.c_uint8),     # keys_buffer
        ctypes.POINTER(ctypes.c_uint32),    # key_offsets
        ctypes.POINTER(ctypes.c_uint32),    # key_lengths
        ctypes.POINTER(ctypes.c_uint32),    # value_offsets
        ctypes.POINTER(ctypes.c_uint32),    # value_lengths
        ctypes.c_uint32,                    # n_entries
        ctypes.POINTER(ctypes.c_bool),      # out_found
        ctypes.POINTER(ctypes.c_uint32),    # out_value_offset
        ctypes.POINTER(ctypes.c_uint32),    # out_value_length
    ]
    lib.srmech_catalog_lookup.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class F (template render with {key} substitution) — Phase C1 rc5.
    # int srmech_template_render(tmpl, tmpl_len, keys_buf, ..., n_pairs,
    #                            out_buf, out_capacity, *out_written)
    # ------------------------------------------------------------------
    lib.srmech_template_render.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),     # tmpl
        ctypes.c_uint32,                    # tmpl_len
        ctypes.POINTER(ctypes.c_uint8),     # keys_buffer
        ctypes.POINTER(ctypes.c_uint32),    # key_offsets
        ctypes.POINTER(ctypes.c_uint32),    # key_lengths
        ctypes.POINTER(ctypes.c_uint8),     # values_buffer
        ctypes.POINTER(ctypes.c_uint32),    # value_offsets
        ctypes.POINTER(ctypes.c_uint32),    # value_lengths
        ctypes.c_uint32,                    # n_pairs
        ctypes.POINTER(ctypes.c_uint8),     # out_buf
        ctypes.c_uint32,                    # out_capacity
        ctypes.POINTER(ctypes.c_uint32),    # out_written
    ]
    lib.srmech_template_render.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class N — rational-approximation (Task #217 Phase C1 rc6).
    # ------------------------------------------------------------------
    # int srmech_continued_fraction(uint64_t p, uint64_t q,
    #                               uint64_t *terms, uint32_t max_terms,
    #                               uint32_t *out_count)
    lib.srmech_continued_fraction.argtypes = [
        ctypes.c_uint64,
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.srmech_continued_fraction.restype = ctypes.c_int

    # int srmech_best_rational(uint64_t p, uint64_t q,
    #                          uint64_t max_denominator,
    #                          uint64_t *out_p, uint64_t *out_q)
    lib.srmech_best_rational.argtypes = [
        ctypes.c_uint64,
        ctypes.c_uint64,
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_best_rational.restype = ctypes.c_int

    # rc8: int srmech_exp_series_truncate(int64_t  x_num,
    #                                      uint64_t x_den,
    #                                      uint32_t num_terms,
    #                                      int64_t *out_num,
    #                                      uint64_t *out_den)
    # exp Taylor partial sum as exact rational, num_terms <= 20.
    # Returns SRMECH_ERR_OVERFLOW for inputs beyond u64 range; Python
    # bignum fallback in srmech.amsc.rational.exp_series_truncate
    # handles unbounded N.
    lib.srmech_exp_series_truncate.argtypes = [
        ctypes.c_int64,
        ctypes.c_uint64,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_exp_series_truncate.restype = ctypes.c_int

    # rc10: Class N rational arithmetic primitives.
    # int srmech_rational_add(int64_t a_num, uint64_t a_den,
    #                          int64_t b_num, uint64_t b_den,
    #                          int64_t *out_num, uint64_t *out_den)
    for _op in ("srmech_rational_add", "srmech_rational_mul", "srmech_rational_div"):
        getattr(lib, _op).argtypes = [
            ctypes.c_int64,
            ctypes.c_uint64,
            ctypes.c_int64,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.POINTER(ctypes.c_uint64),
        ]
        getattr(lib, _op).restype = ctypes.c_int
    # int srmech_rational_pow_uint(int64_t base_num, uint64_t base_den,
    #                               uint32_t exp_val,
    #                               int64_t *out_num, uint64_t *out_den)
    lib.srmech_rational_pow_uint.argtypes = [
        ctypes.c_int64,
        ctypes.c_uint64,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    lib.srmech_rational_pow_uint.restype = ctypes.c_int

    # rc12: Class N π geometric-cascade primitives (Milestone #4).
    # int srmech_cf_convergents_int64(const int64_t *coefs, size_t n,
    #                                  int64_t *out_nums, int64_t *out_dens)
    # Best-effort binding: not all srmech installs have the rc12 symbol
    # (sdist builds against older headers fall through to bignum-Python).
    if hasattr(lib, "srmech_cf_convergents_int64"):
        lib.srmech_cf_convergents_int64.argtypes = [
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.POINTER(ctypes.c_int64),
        ]
        lib.srmech_cf_convergents_int64.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class K — equation-of-centre / pin-slot (Task #217 Phase C1 rc7).
    # ------------------------------------------------------------------
    # int srmech_pin_slot(double theta, double pin_offset,
    #                     double pin_distance, double *out_phi)
    lib.srmech_pin_slot.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_pin_slot.restype = ctypes.c_int

    # int srmech_kepler_solve(double M_rad, double e, double tolerance,
    #                         uint32_t max_iter, double *out_E_rad)
    lib.srmech_kepler_solve.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_kepler_solve.restype = ctypes.c_int

    # int srmech_equation_of_centre(double M_rad, double e,
    #                               uint32_t n_terms,
    #                               double *out_delta_rad)
    lib.srmech_equation_of_centre.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_equation_of_centre.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class M — HDC binary spatter codes (Task #217 Phase C1 rc8).
    # ------------------------------------------------------------------
    # int srmech_hdc_bind(const uint8_t *a, const uint8_t *b,
    #                     uint32_t n_bytes, uint8_t *out)
    lib.srmech_hdc_bind.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.srmech_hdc_bind.restype = ctypes.c_int

    # int srmech_hdc_bundle(const uint8_t * const *vectors,
    #                       uint32_t n_vectors, uint32_t n_bytes,
    #                       uint8_t *out)
    lib.srmech_hdc_bundle.argtypes = [
        ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.srmech_hdc_bundle.restype = ctypes.c_int

    # int srmech_hdc_permute(const uint8_t *a, uint32_t n_bytes,
    #                        int32_t rotate_bits, uint8_t *out)
    lib.srmech_hdc_permute.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.srmech_hdc_permute.restype = ctypes.c_int

    # int srmech_hdc_similarity(const uint8_t *a, const uint8_t *b,
    #                           uint32_t n_bytes, double *out)
    lib.srmech_hdc_similarity.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_hdc_similarity.restype = ctypes.c_int

    # int srmech_hdc_hamming(const uint8_t *a, const uint8_t *b,
    #                        uint32_t n_bytes, uint32_t *out)
    # NEW in v0.9.0rc2 (F868 stay-rational) — guard with its own hasattr so a
    # pre-rc2 lib doesn't AttributeError; the integer bit-Hamming distance backs
    # the exact Q-returning hdc.similarity / the public hdc.hamming op.
    if hasattr(lib, "srmech_hdc_hamming"):
        lib.srmech_hdc_hamming.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        lib.srmech_hdc_hamming.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class M — polar {-1, 0, +1} variant (v0.4.3rc1). NEW symbols; guard
    # with hasattr so a stale lib built before these landed doesn't
    # disable the whole native surface (mirrors the rc12 best-effort
    # binding pattern for srmech_cf_convergents_int64).
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_polar_bind"):
        # int srmech_polar_bind(const int8_t *a, const int8_t *b,
        #                       uint32_t n, int8_t *out)
        lib.srmech_polar_bind.argtypes = [
            ctypes.POINTER(ctypes.c_int8),
            ctypes.POINTER(ctypes.c_int8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_int8),
        ]
        lib.srmech_polar_bind.restype = ctypes.c_int

        # int srmech_polar_bundle(const int8_t * const *vectors,
        #                         uint32_t n_vectors, uint32_t n,
        #                         int8_t *out)
        lib.srmech_polar_bundle.argtypes = [
            ctypes.POINTER(ctypes.POINTER(ctypes.c_int8)),
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_int8),
        ]
        lib.srmech_polar_bundle.restype = ctypes.c_int

        # int srmech_polar_similarity(const int8_t *a, const int8_t *b,
        #                             uint32_t n, int32_t skip_zero,
        #                             double *out)
        lib.srmech_polar_similarity.argtypes = [
            ctypes.POINTER(ctypes.c_int8),
            ctypes.POINTER(ctypes.c_int8),
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_polar_similarity.restype = ctypes.c_int

        # int srmech_polar_density(const int8_t *v, uint32_t n,
        #                          double *out)
        lib.srmech_polar_density.argtypes = [
            ctypes.POINTER(ctypes.c_int8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_polar_density.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class M — Klein-4 {0,1,2,3} variant (v0.4.3rc2). NEW symbols;
    # hasattr-guarded (same rationale as the polar block above).
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_klein4_bind"):
        # int srmech_klein4_bind(const uint8_t *a, const uint8_t *b,
        #                        uint32_t n, uint8_t *out)
        lib.srmech_klein4_bind.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.srmech_klein4_bind.restype = ctypes.c_int

        # §59 / F861: int srmech_klein4_phase_key(uint32_t D, uint32_t start,
        #                          uint32_t width, uint8_t elem, uint8_t *out)
        if hasattr(lib, "srmech_klein4_phase_key"):
            lib.srmech_klein4_phase_key.argtypes = [
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint8,
                ctypes.POINTER(ctypes.c_uint8),
            ]
            lib.srmech_klein4_phase_key.restype = ctypes.c_int

        # §58 / F837: int srmech_klein4_chunk_resolve(const uint8_t *chunks,
        #     uint32_t n_chunks, const uint8_t *key, uint32_t D,
        #     const uint8_t *candidates, uint32_t n_candidates,
        #     uint32_t *out_counts)
        if hasattr(lib, "srmech_klein4_chunk_resolve"):
            lib.srmech_klein4_chunk_resolve.argtypes = [
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
            ]
            lib.srmech_klein4_chunk_resolve.restype = ctypes.c_int

        # §60 / F864: int srmech_klein4_random(const uint32_t *key,
        #     size_t key_length, uint32_t D, uint8_t *out) — MT19937 seeded by
        # init_by_array(key); each draw byte-identical to random.Random(seed)
        # .randrange(4). NEW in rc6 — guard with its own hasattr so a pre-rc6
        # klein4-capable lib doesn't AttributeError here.
        if hasattr(lib, "srmech_klein4_random"):
            lib.srmech_klein4_random.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.c_size_t,
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint8),
            ]
            lib.srmech_klein4_random.restype = ctypes.c_int

        # int srmech_klein4_bundle(const uint8_t * const *vectors,
        #                          uint32_t n_vectors, uint32_t n,
        #                          uint8_t *out)
        lib.srmech_klein4_bundle.argtypes = [
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.srmech_klein4_bundle.restype = ctypes.c_int

        # rc18 / F900: int srmech_klein4_compose(const uint8_t *parts,
        #   uint32_t n, uint32_t D, uint32_t *acc, uint8_t *scratch, uint8_t *out)
        if hasattr(lib, "srmech_klein4_compose"):
            lib.srmech_klein4_compose.argtypes = [
                ctypes.POINTER(ctypes.c_uint8),   # parts (n*D)
                ctypes.c_uint32,                  # n
                ctypes.c_uint32,                  # D
                ctypes.POINTER(ctypes.c_uint32),  # acc (1 + 2*D)
                ctypes.POINTER(ctypes.c_uint8),   # scratch (2*D)
                ctypes.POINTER(ctypes.c_uint8),   # out (D)
            ]
            lib.srmech_klein4_compose.restype = ctypes.c_int

        # int srmech_klein4_similarity(const uint8_t *a, const uint8_t *b,
        #                              uint32_t n, double *out)
        lib.srmech_klein4_similarity.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_klein4_similarity.restype = ctypes.c_int

        # int srmech_klein4_match_count(const uint8_t *a, const uint8_t *b,
        #                               uint32_t n, uint32_t *out)
        # NEW in v0.9.0rc1 (F868 stay-rational) — guard with its own hasattr so
        # a pre-rc1 klein4-capable lib doesn't AttributeError here; the integer
        # match count backs the exact Q-returning klein4_similarity / the public
        # klein4_match_count op.
        if hasattr(lib, "srmech_klein4_match_count"):
            lib.srmech_klein4_match_count.argtypes = [
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
            ]
            lib.srmech_klein4_match_count.restype = ctypes.c_int

        # int srmech_klein4_triality_cycle(const uint8_t *in, uint32_t n,
        #                                  int inverse, uint8_t *out)
        # NEW in v0.6.0rc18 — guard with its own hasattr so a klein4-capable
        # but pre-rc18 lib (rc13-rc17) doesn't AttributeError here.
        if hasattr(lib, "srmech_klein4_triality_cycle"):
            lib.srmech_klein4_triality_cycle.argtypes = [
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_uint32,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint8),
            ]
            lib.srmech_klein4_triality_cycle.restype = ctypes.c_int

        # int srmech_klein4_bundle_accumulate(uint32_t *acc, const uint8_t *v,
        #                                     size_t dim)  — UPSTREAM §50 (rc155).
        # NEW — guard with its own hasattr so a pre-rc155 klein4-capable lib
        # doesn't AttributeError here.
        if hasattr(lib, "srmech_klein4_bundle_accumulate"):
            lib.srmech_klein4_bundle_accumulate.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_size_t,
            ]
            lib.srmech_klein4_bundle_accumulate.restype = ctypes.c_int
        # int srmech_klein4_bundle_resolve(const uint32_t *acc, uint8_t *out,
        #                                  size_t dim)
        if hasattr(lib, "srmech_klein4_bundle_resolve"):
            lib.srmech_klein4_bundle_resolve.argtypes = [
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_size_t,
            ]
            lib.srmech_klein4_bundle_resolve.restype = ctypes.c_int
        # int srmech_klein4_cooccurrence_fold(const uint8_t *codes,
        #     uint32_t n_codes, const uint32_t *tok_idx, uint32_t n_tokens,
        #     uint32_t window, size_t dim, uint32_t *out_accs)  — UPSTREAM §50
        #     (rc165): the corpus-linear windowed fold, fully in C. NEW — its own
        #     hasattr so a pre-rc165 klein4 lib doesn't AttributeError here.
        if hasattr(lib, "srmech_klein4_cooccurrence_fold"):
            lib.srmech_klein4_cooccurrence_fold.argtypes = [
                ctypes.POINTER(ctypes.c_uint8),   # codes (n_codes * dim)
                ctypes.c_uint32,                   # n_codes
                ctypes.POINTER(ctypes.c_uint32),  # tok_idx (n_tokens)
                ctypes.c_uint32,                   # n_tokens
                ctypes.c_uint32,                   # window
                ctypes.c_size_t,                   # dim
                ctypes.POINTER(ctypes.c_uint32),  # out_accs (n_codes*(1+2*dim))
            ]
            lib.srmech_klein4_cooccurrence_fold.restype = ctypes.c_int
        # srmech_status_t srmech_laplacian_fiedler_sparse(uint32_t n,
        #     uint32_t n_edges, const uint32_t *edge_u, const uint32_t *edge_v,
        #     const double *weights, uint32_t max_iters, double *out_vec,
        #     double *ws, size_t ws_len)  — issue #1097 / UPSTREAM §51 (rc166):
        #     the sparse normalized-cut Fiedler (matvec power iteration, n
        #     unbounded). Caller-arena ws (9*n doubles) → no compiled-in cap. NEW
        #     — own hasattr so a pre-rc166 lib doesn't AttributeError here.
        if hasattr(lib, "srmech_laplacian_fiedler_sparse"):
            lib.srmech_laplacian_fiedler_sparse.argtypes = [
                ctypes.c_uint32,                   # n
                ctypes.c_uint32,                   # n_edges
                ctypes.POINTER(ctypes.c_uint32),  # edge_u (n_edges)
                ctypes.POINTER(ctypes.c_uint32),  # edge_v (n_edges)
                ctypes.POINTER(ctypes.c_double),  # weights (n_edges)
                ctypes.c_uint32,                   # max_iters
                ctypes.POINTER(ctypes.c_double),  # out_vec (n)
                ctypes.POINTER(ctypes.c_double),  # ws (9*n scratch arena)
                ctypes.c_size_t,                   # ws_len (in doubles)
            ]
            lib.srmech_laplacian_fiedler_sparse.restype = ctypes.c_int

        # srmech_status_t srmech_laplacian_fiedler_sparse_file(uint32_t n,
        #     const char *path, uint32_t max_iters, double *out_vec,
        #     double *ws, size_t ws_len)  — §52 Part 2 / F793 (rc168): the
        #     OUT-OF-CORE streaming Fiedler. Same power iteration, but the
        #     adjacency STREAMS from a packed 16-byte-record edge file via the
        #     PAL — only the O(n) ws arena is resident, so a low-RAM target can
        #     partition a graph whose edge list does not fit RAM. NEW symbol —
        #     own hasattr so a pre-rc168 lib doesn't AttributeError here.
        if hasattr(lib, "srmech_laplacian_fiedler_sparse_file"):
            lib.srmech_laplacian_fiedler_sparse_file.argtypes = [
                ctypes.c_uint32,                   # n
                ctypes.c_char_p,                   # path (packed edge file)
                ctypes.c_uint32,                   # max_iters
                ctypes.POINTER(ctypes.c_double),  # out_vec (n)
                ctypes.POINTER(ctypes.c_double),  # ws (9*n scratch arena)
                ctypes.c_size_t,                   # ws_len (in doubles)
            ]
            lib.srmech_laplacian_fiedler_sparse_file.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Cascade catalog — v0.4.5rc1 C-parity + TOML retrofit.
    # Corrects the v0.4.3rc6 / v0.4.4rc1 carve-out that shipped cascade
    # ops Python-only. NEW symbols — guard with hasattr so a stale lib
    # built before these landed doesn't disable the whole native
    # surface (same best-effort pattern as the rc12 / polar / klein4
    # blocks above).
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_cascade_chiral_flip_i64"):
        # int srmech_cascade_chiral_flip_i64(const int64_t *in,
        #                                     size_t         n,
        #                                     int64_t       *out)
        lib.srmech_cascade_chiral_flip_i64.argtypes = [
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
        ]
        lib.srmech_cascade_chiral_flip_i64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_chiral_flip_f64"):
        # int srmech_cascade_chiral_flip_f64(const double *in,
        #                                     size_t        n,
        #                                     double       *out)
        lib.srmech_cascade_chiral_flip_f64.argtypes = [
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_cascade_chiral_flip_f64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_pin_slot_at_zero_f64"):
        # int srmech_cascade_pin_slot_at_zero_f64(double  x,
        #                                          int8_t *orientation_out,
        #                                          double *magnitude_out)
        # v0.4.5rc2 — Class K pin-slot at zero (scalar in, two outputs).
        lib.srmech_cascade_pin_slot_at_zero_f64.argtypes = [
            ctypes.c_double,
            ctypes.POINTER(ctypes.c_int8),
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_cascade_pin_slot_at_zero_f64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_magnitude_f64"):
        # int srmech_cascade_magnitude_f64(double  x,
        #                                   double *magnitude_out)
        # v0.4.5rc3 — Class K pin-slot magnitude-only (scalar in / out).
        lib.srmech_cascade_magnitude_f64.argtypes = [
            ctypes.c_double,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_cascade_magnitude_f64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_reorient_i64"):
        # int srmech_cascade_reorient_i64(int8_t   orientation,
        #                                  int64_t  value,
        #                                  int64_t *out)
        # v0.4.5rc4 — Class C cascade-orientation re-application (i64).
        lib.srmech_cascade_reorient_i64.argtypes = [
            ctypes.c_int8,
            ctypes.c_int64,
            ctypes.POINTER(ctypes.c_int64),
        ]
        lib.srmech_cascade_reorient_i64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_reorient_f64"):
        # int srmech_cascade_reorient_f64(int8_t  orientation,
        #                                  double  value,
        #                                  double *out)
        # v0.4.5rc4 — Class C cascade-orientation re-application (f64).
        lib.srmech_cascade_reorient_f64.argtypes = [
            ctypes.c_int8,
            ctypes.c_double,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_cascade_reorient_f64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_net_chirality_i8"):
        # int srmech_cascade_net_chirality_i8(const int8_t *orientations,
        #                                      size_t        n,
        #                                      int8_t       *out)
        # v0.4.5rc5 — Class C net handedness invariant (sequence in /
        # scalar out via output pointer; empty input -> +1; zero-element
        # short-circuits to 0).
        lib.srmech_cascade_net_chirality_i8.argtypes = [
            ctypes.POINTER(ctypes.c_int8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int8),
        ]
        lib.srmech_cascade_net_chirality_i8.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_cyclic_gcd_u64"):
        # int srmech_cascade_cyclic_gcd_u64(uint64_t  a,
        #                                    uint64_t  b,
        #                                    uint64_t *out)
        # v0.4.5rc6 — Class I cyclic-group gcd, cascade-namespace
        # wrapper. FIRST of the delegating cascade ops: the cascade
        # entry IS the Class I primitive (srmech_gcd); this wrapper
        # exists to maintain the srmech_cascade_* namespace invariant.
        lib.srmech_cascade_cyclic_gcd_u64.argtypes = [
            ctypes.c_uint64,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_uint64),
        ]
        lib.srmech_cascade_cyclic_gcd_u64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_best_rational_signed_f64"):
        # int srmech_cascade_best_rational_signed_f64(
        #     double    x, int64_t max_denominator, int64_t fine_scale,
        #     int64_t  *out_num, int64_t *out_den)
        # v0.4.5rc7 — Class K ∘ Class N ∘ Class C; multi-stage cascade
        # delegating the Class N stage to srmech_best_rational with the
        # Class K + Class C stages inlined. Banker's rounding via
        # llrint() under default IEEE-754 FE_TONEAREST mode for parity
        # with Python's built-in round().
        lib.srmech_cascade_best_rational_signed_f64.argtypes = [
            ctypes.c_double,
            ctypes.c_int64,
            ctypes.c_int64,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.POINTER(ctypes.c_int64),
        ]
        lib.srmech_cascade_best_rational_signed_f64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_chiral_dual_f64"):
        # int srmech_cascade_chiral_dual_f64(
        #     srmech_cascade_op_callback_f64_t op,
        #     void                              *user_data,
        #     const double                     *in,
        #     size_t                            n,
        #     double                           *out,
        #     double                           *workspace)
        # v0.4.5rc8 — HIGHER-ORDER Class C ∘ op ∘ Class C conjugation.
        # CLOSES the cascade-catalog C-parity arc (op 8 of 8). Function-
        # pointer callback for the inner op (chosen over Class-ID enum
        # dispatch so arbitrary callables work per the cascade-catalog
        # public API contract). Workspace is caller-allocated per JPL
        # Rule 3 (no malloc inside libsrmech). Delegates the Class C
        # inner+outer chiral_flip to the rc1 native peer.
        lib.srmech_cascade_chiral_dual_f64.argtypes = [
            CASCADE_OP_CALLBACK_F64,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_cascade_chiral_dual_f64.restype = ctypes.c_int

    if hasattr(lib, "srmech_cascade_parallel_sector_dispatch"):
        # int srmech_cascade_parallel_sector_dispatch(
        #     srmech_cascade_body_f64 body, void *user,
        #     const double *in, size_t n,
        #     uint32_t n_sectors,
        #     double *out_sectors,
        #     double *scratch, size_t scratch_len)
        # v0.6.0rc7 (#771) — C-orchestration parity for the rc6 Python
        # parallel_sector_dispatch. Runs the ≤4 Klein-4 chirality
        # sectors of a caller-supplied cascade body and writes the four
        # sector duals into the disjoint out_sectors[s*n ..] slices,
        # each sector using its own disjoint scratch[s*n ..] slice (the
        # F233 4-way independence ⇒ 0 cross-thread writes). Threaded on
        # POSIX/Windows; SERIAL fallback (bit-identical) on thread-less
        # targets. Workspace caller-allocated (JPL Rule 3, no malloc).
        lib.srmech_cascade_parallel_sector_dispatch.argtypes = [
            CASCADE_BODY_CALLBACK_F64,               # body
            ctypes.c_void_p,                          # user
            ctypes.POINTER(ctypes.c_double),         # in
            ctypes.c_size_t,                          # n
            ctypes.c_uint32,                          # n_sectors (1..4)
            ctypes.POINTER(ctypes.c_double),         # out_sectors
            ctypes.POINTER(ctypes.c_double),         # scratch
            ctypes.c_size_t,                          # scratch_len
        ]
        lib.srmech_cascade_parallel_sector_dispatch.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # v0.5.0rc2: srmech.bus C peer (6 public symbols).
    # All bus symbols are hasattr-guarded — a stale rc1 lib (ABI v2)
    # won't have them and the load will fall through to the rc1
    # Python-only path. (ABI v2 vs v3 mismatch ALSO bails earlier in
    # the load sequence; this is double-defence.)
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_bus_serve"):
        # srmech_status_t srmech_bus_serve(
        #     const char *name, srmech_bus_handler_callback_t handler,
        #     void *user_data, srmech_bus_server_handle_t **out_handle)
        lib.srmech_bus_serve.argtypes = [
            ctypes.c_char_p,
            BUS_HANDLER_CALLBACK,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        lib.srmech_bus_serve.restype = ctypes.c_int

    if hasattr(lib, "srmech_bus_server_accept_one"):
        # srmech_status_t srmech_bus_server_accept_one(
        #     srmech_bus_server_handle_t *h)
        lib.srmech_bus_server_accept_one.argtypes = [ctypes.c_void_p]
        lib.srmech_bus_server_accept_one.restype = ctypes.c_int

    if hasattr(lib, "srmech_bus_server_stop"):
        # srmech_status_t srmech_bus_server_stop(
        #     srmech_bus_server_handle_t *h)
        lib.srmech_bus_server_stop.argtypes = [ctypes.c_void_p]
        lib.srmech_bus_server_stop.restype = ctypes.c_int

    if hasattr(lib, "srmech_bus_connect"):
        # srmech_status_t srmech_bus_connect(
        #     const char *name, srmech_bus_client_handle_t **out_handle)
        lib.srmech_bus_connect.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        lib.srmech_bus_connect.restype = ctypes.c_int

    if hasattr(lib, "srmech_bus_send_recv"):
        # srmech_status_t srmech_bus_send_recv(
        #     srmech_bus_client_handle_t *h,
        #     const uint8_t *request, size_t request_len,
        #     uint8_t *response, size_t *response_len_inout)
        lib.srmech_bus_send_recv.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        lib.srmech_bus_send_recv.restype = ctypes.c_int

    if hasattr(lib, "srmech_bus_client_close"):
        # srmech_status_t srmech_bus_client_close(
        #     srmech_bus_client_handle_t *h)
        lib.srmech_bus_client_close.argtypes = [ctypes.c_void_p]
        lib.srmech_bus_client_close.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # v0.7.0rc16: C-transpile of the rc12 chiral primitives (Classes
    # I / D / G). NEW symbols — hasattr-guarded so a stale lib built
    # before rc16 doesn't disable the whole native surface (same
    # best-effort pattern as the cascade/polar/klein4 blocks above).
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_three_cycle"):
        # int srmech_three_cycle(uint64_t value, uint64_t *out)
        lib.srmech_three_cycle.argtypes = [
            ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
        ]
        lib.srmech_three_cycle.restype = ctypes.c_int
    if hasattr(lib, "srmech_mirror_pattern"):
        # int srmech_mirror_pattern(const uint8_t *pattern,
        #                           uint32_t pattern_len, uint8_t *out)
        lib.srmech_mirror_pattern.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.srmech_mirror_pattern.restype = ctypes.c_int
    if hasattr(lib, "srmech_byte_search_backward"):
        # int srmech_byte_search_backward(const uint8_t *haystack,
        #     uint32_t haystack_len, const uint8_t *needle,
        #     uint32_t needle_len, uint32_t *out_offset)
        lib.srmech_byte_search_backward.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        lib.srmech_byte_search_backward.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # v0.7.0rc17: C-transpile of the last two rc12 chiral primitives
    # (Class L three-fold band split, Class E reverse-order). NEW symbols
    # — hasattr-guarded so a stale lib built before rc17 doesn't disable
    # the whole native surface (same best-effort pattern as the rc16 block
    # above).
    # ------------------------------------------------------------------
    if hasattr(lib, "srmech_three_fold_bands"):
        # int srmech_three_fold_bands(uint32_t n, uint32_t *out_low,
        #     uint32_t *out_mid, uint32_t *out_high)
        lib.srmech_three_fold_bands.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        lib.srmech_three_fold_bands.restype = ctypes.c_int
    if hasattr(lib, "srmech_reverse_order"):
        # int srmech_reverse_order(uint32_t n, uint32_t *out_order)
        lib.srmech_reverse_order.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        lib.srmech_reverse_order.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # v0.7.5rc2: bind the rc43-46 C transcendental cascade so the Python
    # float-projection ops (``rational.{sin,cos,atan,atan2,exp,log,sqrt}``)
    # actually DISPATCH to the executable C. The C cascade was built across
    # rc43-46 (srmech_{sin,cos,atan,atan2,rational_sqrt,exp,log}) but never
    # wired to Python, so the runtime ran the pure-Python bignum series on
    # EVERY install — the v0.7.0 "C-transpile triality" was source-only, the
    # executable never agreed with itself. NEW-symbol hasattr guards (a
    # pre-rc43 lib still loads). ``int srmech_<fn>(double x, double *out)``;
    # ``srmech_atan2`` takes ``(double y, double x, double *out)``.
    # ------------------------------------------------------------------
    for _scalar_trans in ("srmech_sin", "srmech_cos", "srmech_atan",
                          "srmech_exp", "srmech_log", "srmech_rational_sqrt"):
        if hasattr(lib, _scalar_trans):
            getattr(lib, _scalar_trans).argtypes = [
                ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
            getattr(lib, _scalar_trans).restype = ctypes.c_int
    # 0.9.0rc7 stay-rational Q61 peers (F868). One-output (sin/cos/atan) return
    # the int64 Q61 value; two-output (exp/log/sqrt) return (mantissa, exponent).
    for _q1 in ("srmech_sin_q61", "srmech_cos_q61", "srmech_atan_q61"):
        if hasattr(lib, _q1):
            getattr(lib, _q1).argtypes = [
                ctypes.c_double, ctypes.POINTER(ctypes.c_int64)]
            getattr(lib, _q1).restype = ctypes.c_int
    for _q2 in ("srmech_exp_q61", "srmech_log_q61", "srmech_sqrt_q61"):
        if hasattr(lib, _q2):
            getattr(lib, _q2).argtypes = [
                ctypes.c_double, ctypes.POINTER(ctypes.c_int64),
                ctypes.POINTER(ctypes.c_int64)]
            getattr(lib, _q2).restype = ctypes.c_int
    if hasattr(lib, "srmech_atan2"):
        lib.srmech_atan2.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        lib.srmech_atan2.restype = ctypes.c_int
    # 0.9.0rc10 hypercomplex exp(mu*theta) twiddle (F882): fills out8 (8 int64
    # Q61 components). ``int srmech_hypercomplex_exp_q61(double theta, int k_axes,
    # int64_t *out8)``. hasattr guard — a pre-rc10 lib still loads.
    if hasattr(lib, "srmech_hypercomplex_exp_q61"):
        lib.srmech_hypercomplex_exp_q61.argtypes = [
            ctypes.c_double, ctypes.c_int, ctypes.POINTER(ctypes.c_int64)]
        lib.srmech_hypercomplex_exp_q61.restype = ctypes.c_int
    # 0.9.0rc13 public integer floor-sqrt (the stdlib `math.isqrt` purge):
    # ``int srmech_isqrt(uint64_t nhi, uint64_t nlo, uint64_t *out_root)``.
    if hasattr(lib, "srmech_isqrt"):
        lib.srmech_isqrt.argtypes = [
            ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
        lib.srmech_isqrt.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # v0.7.5rc153 (UPSTREAM §49): bind the 11 genome file-management C
    # symbols + the JSON writer (for catalog's tree return). The genome
    # C family (srmech_genome.c, §41–§46 / §43 / §45) writes turns.bin +
    # manifest.json BYTE-IDENTICAL to the pure-Python path — proven by the
    # WSL2 ctypes byte-parity harness across rc143–rc152 — so genome.py can
    # DISPATCH to them when HAS_NATIVE with zero on-disk divergence (this
    # closes the §38/F708 "C exists but Python doesn't call it" gap for the
    # genome family). NEW symbols → hasattr-guarded (a pre-rc143 lib still
    # loads). Binding existing symbols is additive → ABI unaffected (3).
    if hasattr(lib, "srmech_genome_save"):
        _U8 = ctypes.POINTER(ctypes.c_uint8)
        _SZ = ctypes.c_size_t
        _PSZ = ctypes.POINTER(ctypes.c_size_t)
        _U32 = ctypes.c_uint32
        _CP = ctypes.c_char_p
        _VP = ctypes.c_void_p
        # save(dir, body, body_len, leaf_dim, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_save.argtypes = [_CP, _U8, _SZ, _U32, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_save.restype = ctypes.c_int
        # load(dir, out, out_cap, &out_len, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_load.argtypes = [_CP, _U8, _SZ, _PSZ, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_load.restype = ctypes.c_int
        # catalog(dir, the_one, the_one_len, ws, ws_len, &out_manifest_tree)
        lib.srmech_genome_catalog.argtypes = [_CP, _U8, _SZ, _VP, _SZ,
                                              ctypes.POINTER(_VP)]
        lib.srmech_genome_catalog.restype = ctypes.c_int
        # window(dir, label, out, out_cap, &out_len, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_window.argtypes = [_CP, _CP, _U8, _SZ, _PSZ, _U8, _SZ,
                                             _VP, _SZ]
        lib.srmech_genome_window.restype = ctypes.c_int
        # append(dir, label, region, region_len, leaf_dim, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_append.argtypes = [_CP, _CP, _U8, _SZ, _U32, _U8, _SZ,
                                             _VP, _SZ]
        lib.srmech_genome_append.restype = ctypes.c_int
        # remove(dir, label, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_remove.argtypes = [_CP, _CP, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_remove.restype = ctypes.c_int
        # replace(dir, label, region, region_len, leaf_dim, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_replace.argtypes = [_CP, _CP, _U8, _SZ, _U32, _U8, _SZ,
                                              _VP, _SZ]
        lib.srmech_genome_replace.restype = ctypes.c_int
        # export(dir, label, out_path, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_export.argtypes = [_CP, _CP, _CP, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_export.restype = ctypes.c_int
        # import(chr_path, dest, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_import.argtypes = [_CP, _CP, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_import.restype = ctypes.c_int
        # explode(dir, out_dir, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_explode.argtypes = [_CP, _CP, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_explode.restype = ctypes.c_int
        # pack(loose_dir, dest, the_one, the_one_len, ws, ws_len)
        lib.srmech_genome_pack.argtypes = [_CP, _CP, _U8, _SZ, _VP, _SZ]
        lib.srmech_genome_pack.restype = ctypes.c_int
        # json_write_ws(value, buf, buf_len, &out_len, ws, ws_len) — serialise
        # the catalog's tree; the writer's key-sort scratch is carved from the
        # caller arena `ws` (rc160: no compiled-in object-width cap). Size `ws`
        # with srmech_json_write_arena_bytes(value).
        if hasattr(lib, "srmech_json_write_ws"):
            lib.srmech_json_write_arena_bytes.argtypes = [_VP]
            lib.srmech_json_write_arena_bytes.restype = ctypes.c_size_t
            lib.srmech_json_write_ws.argtypes = [_VP, _CP, _SZ, _PSZ, _VP, _SZ]
            lib.srmech_json_write_ws.restype = ctypes.c_int

    # ------------------------------------------------------------------
    # Class N — ROTATION-LAST Chudnovsky π on srmech_bigint (0.9.0rc19).
    # The two srmech_pi_* symbols are the C-host peer of
    # srmech.amsc.rational.pi_chudnovsky_digits — exact bigint body, ONE
    # terminal isqrt+division, byte-identical "3.<digits>". The underlying
    # srmech_bigint is carrier-internal (NO Python surface — not bound
    # here). NEW symbols → hasattr-guarded (a stale ABI-3 lib keeps the
    # rest of the native surface); additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_pi_chudnovsky_ws_bound(uint32_t num_digits)
    if hasattr(lib, "srmech_pi_chudnovsky_ws_bound"):
        lib.srmech_pi_chudnovsky_ws_bound.argtypes = [ctypes.c_uint32]
        lib.srmech_pi_chudnovsky_ws_bound.restype = ctypes.c_size_t
    #   srmech_status_t srmech_pi_chudnovsky(uint32_t num_digits, char *out,
    #       size_t out_cap, size_t *out_len, void *ws, size_t ws_len)
    if hasattr(lib, "srmech_pi_chudnovsky"):
        lib.srmech_pi_chudnovsky.argtypes = [
            ctypes.c_uint32,                    # num_digits
            ctypes.POINTER(ctypes.c_char),      # out
            ctypes.c_size_t,                    # out_cap
            ctypes.POINTER(ctypes.c_size_t),    # out_len
            ctypes.c_void_p,                    # ws (caller arena)
            ctypes.c_size_t,                    # ws_len (arena bytes)
        ]
        lib.srmech_pi_chudnovsky.restype = ctypes.c_int

    # rc35: BIGNUM-EXACT Class-N transcendental Taylor truncations on the
    # caller-arena srmech_bigint (the standalone-honor closure removing the
    # int64/Q61 ceiling the C peers had vs. the Python bignum path). The
    # operand/result rationals are srmech_bigint pairs; all scratch is caller-
    # arena (sized via srmech_bigexp_ws_bound). NEW symbols → hasattr-guarded;
    # additive → EXPECTED_ABI_VERSION stays 3. srmech_bigint is carrier-internal
    # (bound here only to marshal the *_big operands, mirroring the pi_chudnovsky
    # bigint-ws pattern).
    #   size_t srmech_bigexp_ws_bound(size_t num_limbs, size_t den_limbs,
    #                                 uint32_t num_terms)
    if hasattr(lib, "srmech_bigexp_ws_bound"):
        lib.srmech_bigexp_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_uint32,
        ]
        lib.srmech_bigexp_ws_bound.restype = ctypes.c_size_t
    # srmech_bigint marshalling helpers (decimal <-> srmech_bigint) needed to
    # feed the *_big ops their bigint operands + read the bigint results.
    #   size_t srmech_bigint_to_dec_bound(size_t a_n)
    if hasattr(lib, "srmech_bigint_to_dec_bound"):
        lib.srmech_bigint_to_dec_bound.argtypes = [ctypes.c_size_t]
        lib.srmech_bigint_to_dec_bound.restype = ctypes.c_size_t
    #   srmech_status_t srmech_bigint_from_dec(srmech_bigint_t *out,
    #                                          const char *s, size_t len)
    if hasattr(lib, "srmech_bigint_from_dec"):
        lib.srmech_bigint_from_dec.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.c_char_p, ctypes.c_size_t,
        ]
        lib.srmech_bigint_from_dec.restype = ctypes.c_int
    #   srmech_status_t srmech_bigint_to_dec(const srmech_bigint_t *a, char *buf,
    #       size_t cap, size_t *out_len, void *ws, size_t ws_len)
    if hasattr(lib, "srmech_bigint_to_dec"):
        lib.srmech_bigint_to_dec.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(ctypes.c_char),
            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_bigint_to_dec.restype = ctypes.c_int
    # The six *_big ops — all share the signature
    #   srmech_status_t fn(const srmech_bigint_t *x_num,
    #       const srmech_bigint_t *x_den, uint32_t num_terms,
    #       srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    #       void *ws, size_t ws_len)
    _BIGEXP_SIG = [
        ctypes.POINTER(_SrmechBigint),   # x_num / base_num
        ctypes.POINTER(_SrmechBigint),   # x_den / base_den
        ctypes.c_uint32,                 # num_terms / exp_val
        ctypes.POINTER(_SrmechBigint),   # out_num
        ctypes.POINTER(_SrmechBigint),   # out_den
        ctypes.c_void_p,                 # ws
        ctypes.c_size_t,                 # ws_len
    ]
    for _bop in ("srmech_exp_series_truncate_big",
                 "srmech_sin_series_truncate_big",
                 "srmech_cos_series_truncate_big",
                 "srmech_log1p_series_truncate_big",
                 "srmech_atan_series_truncate_big",
                 "srmech_rational_pow_uint_big"):
        if hasattr(lib, _bop):
            getattr(lib, _bop).argtypes = list(_BIGEXP_SIG)
            getattr(lib, _bop).restype = ctypes.c_int

    # Jacobi elliptic sn/cn/dn Maclaurin truncation C peer (the C twin of
    # srmech.amsc.rational.jacobi_sncndn_series_truncate). Same caller-arena
    # srmech_bigint substrate as bigexp; two rational operands (u, m) in, three
    # rational outputs (sn, cn, dn). NEW symbols → hasattr-guarded; additive →
    # EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_jacobi_sncndn_ws_bound(size_t num_limbs, size_t den_limbs,
    #       size_t m_num_limbs, size_t m_den_limbs, uint32_t num_terms)
    if hasattr(lib, "srmech_jacobi_sncndn_ws_bound"):
        lib.srmech_jacobi_sncndn_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t,
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_uint32,
        ]
        lib.srmech_jacobi_sncndn_ws_bound.restype = ctypes.c_size_t
    #   srmech_status_t srmech_jacobi_sncndn(const srmech_bigint_t *u_num,
    #       const srmech_bigint_t *u_den, const srmech_bigint_t *m_num,
    #       const srmech_bigint_t *m_den, uint32_t num_terms,
    #       srmech_bigint_t *sn_num, *sn_den, *cn_num, *cn_den, *dn_num, *dn_den,
    #       void *ws, size_t ws_len)
    if hasattr(lib, "srmech_jacobi_sncndn"):
        lib.srmech_jacobi_sncndn.argtypes = [
            ctypes.POINTER(_SrmechBigint),   # u_num
            ctypes.POINTER(_SrmechBigint),   # u_den
            ctypes.POINTER(_SrmechBigint),   # m_num
            ctypes.POINTER(_SrmechBigint),   # m_den
            ctypes.c_uint32,                 # num_terms
            ctypes.POINTER(_SrmechBigint),   # sn_num
            ctypes.POINTER(_SrmechBigint),   # sn_den
            ctypes.POINTER(_SrmechBigint),   # cn_num
            ctypes.POINTER(_SrmechBigint),   # cn_den
            ctypes.POINTER(_SrmechBigint),   # dn_num
            ctypes.POINTER(_SrmechBigint),   # dn_den
            ctypes.c_void_p,                 # ws
            ctypes.c_size_t,                 # ws_len
        ]
        lib.srmech_jacobi_sncndn.restype = ctypes.c_int

    # rc38: the EXACT-RATIONAL polynomial carrier C peer (srmech_poly_*) — the
    # §76 telescope Sigma-row foundation. Each op takes parallel srmech_bigint
    # coefficient arrays (nums[]/dens[], ascending degree) + a caller arena, all
    # over the same bignum substrate as bigexp (no int64/Q61 ceiling). NEW
    # symbols → hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3. Bound
    # here only to marshal the coefficient arrays (mirroring the bigexp pattern);
    # Poly carries the math, the C accelerates it byte-identically.
    #   size_t srmech_poly_ws_bound(size_t coeff_limbs, size_t n_terms)
    if hasattr(lib, "srmech_poly_ws_bound"):
        lib.srmech_poly_ws_bound.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_poly_ws_bound.restype = ctypes.c_size_t
    # add / sub / mul share the
    #   fn(a_n, a_d, na, b_n, b_d, nb, out_n, out_d, *out_len, ws, ws_len)
    # shape over srmech_bigint coefficient arrays.
    _POLY_BINOP_SIG = [
        ctypes.POINTER(_SrmechBigint),   # a_n[]
        ctypes.POINTER(_SrmechBigint),   # a_d[]
        ctypes.c_size_t,                 # na
        ctypes.POINTER(_SrmechBigint),   # b_n[]
        ctypes.POINTER(_SrmechBigint),   # b_d[]
        ctypes.c_size_t,                 # nb
        ctypes.POINTER(_SrmechBigint),   # out_n[]
        ctypes.POINTER(_SrmechBigint),   # out_d[]
        ctypes.POINTER(ctypes.c_size_t), # *out_len
        ctypes.c_void_p,                 # ws
        ctypes.c_size_t,                 # ws_len
    ]
    for _pop in ("srmech_poly_add", "srmech_poly_sub", "srmech_poly_mul"):
        if hasattr(lib, _pop):
            getattr(lib, _pop).argtypes = list(_POLY_BINOP_SIG)
            getattr(lib, _pop).restype = ctypes.c_int
    #   srmech_poly_divmod(a_n,a_d,na, b_n,b_d,nb, q_n,q_d,*qn, r_n,r_d,*rn, ws,wl)
    if hasattr(lib, "srmech_poly_divmod"):
        lib.srmech_poly_divmod.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_poly_divmod.restype = ctypes.c_int
    # rc39: srmech_poly_gcd (the deferred rc38 item) — the monic Euclidean GCD
    # over Q in one native call, with a SEPARATE chain-scaled ws-bound
    # (srmech_poly_gcd_ws_bound). Same coefficient-array shape as add/sub.
    if hasattr(lib, "srmech_poly_gcd_ws_bound"):
        lib.srmech_poly_gcd_ws_bound.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_poly_gcd_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_poly_gcd"):
        lib.srmech_poly_gcd.argtypes = list(_POLY_BINOP_SIG)
        lib.srmech_poly_gcd.restype = ctypes.c_int
    #   srmech_poly_eval(p_n,p_d,n, x_n,x_d, out_num,out_den, ws,wl)
    if hasattr(lib, "srmech_poly_eval"):
        lib.srmech_poly_eval.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_poly_eval.restype = ctypes.c_int
    #   srmech_poly_shift(p_n,p_d,n, h_n,h_d, acc_n,acc_d,*alen, ws,wl)
    if hasattr(lib, "srmech_poly_shift"):
        lib.srmech_poly_shift.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_poly_shift.restype = ctypes.c_int
    # rc70: the EXACT-INTEGER UNARY THETA q-series C peer (srmech_unary_theta) —
    # the first WEIGHT-GRADED carrier. Computes out[e]=Σ_{n:E(n)=e} χ(n)·n^j over
    # caller-arena srmech_bigint (the same exact-integer substrate as poly; no
    # int64 ceiling on the coefficient n^j). NEW symbols → hasattr-guarded;
    # additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_unary_theta_ws_bound(uint32_t j, size_t coeff_limbs)
    if hasattr(lib, "srmech_unary_theta_ws_bound"):
        lib.srmech_unary_theta_ws_bound.argtypes = [
            ctypes.c_uint32, ctypes.c_size_t]
        lib.srmech_unary_theta_ws_bound.restype = ctypes.c_size_t
    #   srmech_unary_theta_q_series(modulus, chi_table, j, a, b, D, support, N,
    #                               out[], *out_len, ws, ws_len)
    if hasattr(lib, "srmech_unary_theta_q_series"):
        lib.srmech_unary_theta_q_series.argtypes = [
            ctypes.c_uint32,                  # modulus
            ctypes.POINTER(ctypes.c_int32),   # chi_table[modulus]
            ctypes.c_uint32,                  # j
            ctypes.c_int64,                   # a
            ctypes.c_int64,                   # b
            ctypes.c_uint32,                  # D
            ctypes.c_int,                     # support (0/1/2)
            ctypes.c_size_t,                  # N
            ctypes.POINTER(_SrmechBigint),    # out[]
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
            ctypes.c_void_p, ctypes.c_size_t, # ws, ws_len
        ]
        lib.srmech_unary_theta_q_series.restype = ctypes.c_int
    # rc82: the EXACT-INTEGER ETA-QUOTIENT q-series C peer (srmech_eta_quotient) —
    # a WEIGHT-axis carrier. Computes the coefficients of ∏_d ∏_{m≥1}(1−q^{dm})^{r_d}
    # over caller-arena srmech_bigint (the same exact-integer substrate as poly /
    # unary_theta; no int64 ceiling — the coefficients grow, e.g. the Ramanujan τ).
    # NEW symbols → hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_eta_quotient_ws_bound(size_t coeff_limbs)
    if hasattr(lib, "srmech_eta_quotient_ws_bound"):
        lib.srmech_eta_quotient_ws_bound.argtypes = [ctypes.c_size_t]
        lib.srmech_eta_quotient_ws_bound.restype = ctypes.c_size_t
    #   srmech_eta_quotient_qseries(ds[], rs[], n_factors, n_terms,
    #                               out[], *out_len, ws, ws_len)
    if hasattr(lib, "srmech_eta_quotient_qseries"):
        lib.srmech_eta_quotient_qseries.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # ds[n_factors]
            ctypes.POINTER(ctypes.c_int64),   # rs[n_factors]
            ctypes.c_size_t,                  # n_factors
            ctypes.c_size_t,                  # n_terms
            ctypes.POINTER(_SrmechBigint),    # out[]
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
            ctypes.c_void_p, ctypes.c_size_t, # ws, ws_len
        ]
        lib.srmech_eta_quotient_qseries.restype = ctypes.c_int
    # rc83: the EXACT-RATIONAL EISENSTEIN-SERIES q-series C peer (srmech_eisenstein)
    # — the SECOND WEIGHT-axis carrier (after rc82 eta-quotient). Computes the
    # reduced (num, den) coefficients of E_k = 1 − (2k/B_k)·Σ σ_{k−1}(n) qⁿ over
    # caller-arena srmech_bigint (the same exact substrate as poly / eta_quotient;
    # here carrying RATIONAL coeffs — e.g. E₁₂ has c₁ = 65520/691). NEW symbols →
    # hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_eisenstein_ws_bound(size_t coeff_limbs, size_t k)
    if hasattr(lib, "srmech_eisenstein_ws_bound"):
        lib.srmech_eisenstein_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_eisenstein_ws_bound.restype = ctypes.c_size_t
    #   srmech_eisenstein_qseries(k, n_terms, out_num[], out_den[],
    #                             *out_len, ws, ws_len)
    if hasattr(lib, "srmech_eisenstein_qseries"):
        lib.srmech_eisenstein_qseries.argtypes = [
            ctypes.c_size_t,                  # k
            ctypes.c_size_t,                  # n_terms
            ctypes.POINTER(_SrmechBigint),    # out_num[]
            ctypes.POINTER(_SrmechBigint),    # out_den[]
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
            ctypes.c_void_p, ctypes.c_size_t, # ws, ws_len
        ]
        lib.srmech_eisenstein_qseries.restype = ctypes.c_int
    # rc84: the level-1 ℂ[E₄,E₆] MODULAR-FORMS-RING membership-decision C peer
    # (srmech_modular_forms_ring_represent) — the THIRD WEIGHT-axis rung (after rc82
    # eta-quotient + rc83 Eisenstein). Builds the weight-k monomial-basis matrix from
    # the E₄/E₆ q-series (rc83 srmech_eisenstein_qseries + an exact-ℚ truncated
    # convolution), dispatches the square subsystem to the PUBLIC srmech_qmat_solve,
    # VERIFIES all terms, returns the reduced (num, den) rep coeffs or a no-solution
    # flag — all over caller-arena srmech_bigint (no int64 ceiling on a coeff like
    # Δ's 1/1728). NEW symbols → hasattr-guarded; additive → EXPECTED_ABI_VERSION
    # stays 3.
    #   size_t srmech_modular_forms_ring_represent_ws_bound(cl, n_terms, k)
    if hasattr(lib, "srmech_modular_forms_ring_represent_ws_bound"):
        lib.srmech_modular_forms_ring_represent_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_modular_forms_ring_represent_ws_bound.restype = ctypes.c_size_t
    #   size_t srmech_modular_forms_ring_entry_cap(cl, n_terms, k)
    if hasattr(lib, "srmech_modular_forms_ring_entry_cap"):
        lib.srmech_modular_forms_ring_entry_cap.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_modular_forms_ring_entry_cap.restype = ctypes.c_size_t
    #   srmech_modular_forms_ring_represent(k, f_n[], f_d[], n_terms,
    #                                       out_num[], out_den[], *out_has, ws, ws_len)
    if hasattr(lib, "srmech_modular_forms_ring_represent"):
        lib.srmech_modular_forms_ring_represent.argtypes = [
            ctypes.c_size_t,                  # k
            ctypes.POINTER(_SrmechBigint),    # f_n[]
            ctypes.POINTER(_SrmechBigint),    # f_d[]
            ctypes.c_size_t,                  # n_terms
            ctypes.POINTER(_SrmechBigint),    # out_num[]
            ctypes.POINTER(_SrmechBigint),    # out_den[]
            ctypes.POINTER(ctypes.c_size_t),  # *out_has
            ctypes.c_void_p, ctypes.c_size_t, # ws, ws_len
        ]
        lib.srmech_modular_forms_ring_represent.restype = ctypes.c_int
    # rc89: the level-1 ℂ[E₂,E₄,E₆] QUASIMODULAR-FORMS-RING membership-decision C
    # peer (srmech_quasimodular_forms_ring_represent) — the FOURTH WEIGHT-axis rung
    # (after rc82 eta-quotient + rc83 Eisenstein + rc84 ModularFormsRing). Builds the
    # weight-k monomial-basis matrix from the E₂/E₄/E₆ q-series (rc83
    # srmech_eisenstein_qseries — k=2 for E₂ via its quasimodular branch — + an
    # exact-ℚ truncated convolution), dispatches the square subsystem to the PUBLIC
    # srmech_qmat_solve, VERIFIES all terms, returns the reduced (num, den) rep coeffs
    # or a no-solution flag — all over caller-arena srmech_bigint. NEW symbols →
    # hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_quasimodular_forms_ring_represent_ws_bound(cl, n_terms, k)
    if hasattr(lib, "srmech_quasimodular_forms_ring_represent_ws_bound"):
        lib.srmech_quasimodular_forms_ring_represent_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_quasimodular_forms_ring_represent_ws_bound.restype = ctypes.c_size_t
    #   size_t srmech_quasimodular_forms_ring_entry_cap(cl, n_terms, k)
    if hasattr(lib, "srmech_quasimodular_forms_ring_entry_cap"):
        lib.srmech_quasimodular_forms_ring_entry_cap.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_quasimodular_forms_ring_entry_cap.restype = ctypes.c_size_t
    #   srmech_quasimodular_forms_ring_represent(k, f_n[], f_d[], n_terms,
    #                                       out_num[], out_den[], *out_has, ws, ws_len)
    if hasattr(lib, "srmech_quasimodular_forms_ring_represent"):
        lib.srmech_quasimodular_forms_ring_represent.argtypes = [
            ctypes.c_size_t,                  # k
            ctypes.POINTER(_SrmechBigint),    # f_n[]
            ctypes.POINTER(_SrmechBigint),    # f_d[]
            ctypes.c_size_t,                  # n_terms
            ctypes.POINTER(_SrmechBigint),    # out_num[]
            ctypes.POINTER(_SrmechBigint),    # out_den[]
            ctypes.POINTER(ctypes.c_size_t),  # *out_has
            ctypes.c_void_p, ctypes.c_size_t, # ws, ws_len
        ]
        lib.srmech_quasimodular_forms_ring_represent.restype = ctypes.c_int
    # rc71: the EXACT-INTEGER HOLOMORPHIC mock-part q-series C peer
    # (srmech_harmonic_maass) — the HarmonicMaass / MockQSeries PAIR carrier that
    # makes research item #9 a finite exact object. Computes the order-3 mock theta
    # f(q) = Σ q^{n²}/∏(1+qʲ)² integer q-series over caller-arena srmech_bigint
    # (the same exact-integer substrate as poly / unary_theta; no int64 ceiling on
    # the coefficient). NEW symbols → hasattr-guarded; additive →
    # EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_harmonic_maass_ws_bound(size_t N, size_t coeff_limbs)
    if hasattr(lib, "srmech_harmonic_maass_ws_bound"):
        lib.srmech_harmonic_maass_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_harmonic_maass_ws_bound.restype = ctypes.c_size_t
    #   srmech_harmonic_maass_hol_q_series(N, out[], *out_len, ws, ws_len)
    if hasattr(lib, "srmech_harmonic_maass_hol_q_series"):
        lib.srmech_harmonic_maass_hol_q_series.argtypes = [
            ctypes.c_size_t,                  # N
            ctypes.POINTER(_SrmechBigint),    # out[]
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
            ctypes.c_void_p, ctypes.c_size_t, # ws, ws_len
        ]
        lib.srmech_harmonic_maass_hol_q_series.restype = ctypes.c_int
    # rc72: the EXACT-INTEGER (A,B,C) EXPONENT LATTICE of a GENUS-2 RIEMANN
    # THETA-CONSTANT C peer (srmech_riemann_theta) — the FIRST RUNG of the GENUS
    # axis. Emits the [A,B,C,sign] quadruple lattice over a box (the genus-2
    # cross-term denominator-4 clearing + the Class-K sign); plain int64 quadruples
    # (the theta-constant coefficients are small +-1 lattice counts, no bignum). NEW
    # symbols → hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_count"):
        lib.srmech_riemann_theta_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_lattice(ep1,ep2,e1,e2, box, out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_lattice"):
        lib.srmech_riemann_theta_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1,ep2,e1,e2
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_lattice.restype = ctypes.c_int
    # rc73: the SECOND GENUS RUNG — the Sp(4,Z) characteristic TRANSFORMATION + the
    # EIGHTH-nome lattice (the addition gate). Two additive C peers; NEW symbols →
    # hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   srmech_riemann_theta_sp4_char(gamma[16], ep1,ep2,e1,e2, out_char[4], *kexp)
    #   gamma is the 16 int entries (A,B,C,D blocks row-major); out_char is the 4
    #   transformed bits (ep1',ep2',e1',e2'); *kexp is the 8th-root exponent k in
    #   Z/8. Returns SRMECH_ERR_BAD_INPUT if gamma is not symplectic.
    if hasattr(lib, "srmech_riemann_theta_sp4_char"):
        lib.srmech_riemann_theta_sp4_char.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # gamma[16]
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1,ep2,e1,e2
            ctypes.POINTER(ctypes.c_int),     # out_char[4]
            ctypes.POINTER(ctypes.c_int),     # *kexp
        ]
        lib.srmech_riemann_theta_sp4_char.restype = ctypes.c_int
    #   size_t srmech_riemann_theta_eighth_count(uint32_t box)  (== count, reused
    #   shape: (2*box+1)^2 points * 4 int64 [A,B,C,sign])
    if hasattr(lib, "srmech_riemann_theta_eighth_count"):
        lib.srmech_riemann_theta_eighth_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_eighth_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_eighth_lattice(s1,s2,e1,e2, at_two_omega, box,
    #                                       out[], out_cap, *out_len)
    #   at_two_omega: 0 -> theta at Omega (A=2(2n+s)^2 ...); 1 -> at 2Omega
    #   (A=(4n+s)^2 ...). s1,s2 are the DOUBLED upper characteristic (any int).
    if hasattr(lib, "srmech_riemann_theta_eighth_lattice"):
        lib.srmech_riemann_theta_eighth_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # s1,s2,e1,e2
            ctypes.c_int,                     # at_two_omega (0/1)
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_eighth_lattice.restype = ctypes.c_int
    # rc74: the GENUS-AXIS CAPSTONE — the Eilers genus-2 ETA-MAP (branch-point index
    #   set -> characteristic; arXiv:1707.08855, eq 4.4). Pure GF(2) / mod-2 algebra.
    #   srmech_riemann_theta_eta_char(indices[], n_idx, out_char[4])
    if hasattr(lib, "srmech_riemann_theta_eta_char"):
        lib.srmech_riemann_theta_eta_char.argtypes = [
            ctypes.POINTER(ctypes.c_int),     # indices[]
            ctypes.c_size_t,                  # n_idx
            ctypes.POINTER(ctypes.c_int),     # out_char[4]
        ]
        lib.srmech_riemann_theta_eta_char.restype = ctypes.c_int
    # rc75: the NEXT GENUS RUNG — the GENUS-3 EXACT-INTEGER EXPONENT LATTICE C peer
    # (srmech_riemann_theta_g3). Emits the [A1,A2,A3,C12,C13,C23,sign] septuple
    # lattice over a box (the genus-3 THREE cross-terms, each a denominator-4
    # clearing + the Class-K sign); plain int64 septuples (the genus-3 theta-constant
    # coefficients are small +-1 lattice counts, no bignum). NEW symbols →
    # hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_g3_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g3_count"):
        lib.srmech_riemann_theta_g3_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g3_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g3_lattice(ep1,ep2,ep3,e1,e2,e3, box,
    #                                   out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g3_lattice"):
        lib.srmech_riemann_theta_g3_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1,ep2,ep3
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1,e2,e3
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g3_lattice.restype = ctypes.c_int
    # rc80: the NEXT GENUS RUNG (the SCHOTTKY FRONTIER) — the GENUS-4 EXACT-INTEGER
    # EXPONENT LATTICE C peer (srmech_riemann_theta_g4). Emits the
    # [A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign] 11-tuple lattice over a box (the genus-4
    # SIX cross-terms, each a denominator-4 clearing + the Class-K sign); plain int64
    # 11-tuples (the genus-4 theta-constant coefficients are small +-1 lattice counts, no
    # bignum). NEW symbols → hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_g4_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g4_count"):
        lib.srmech_riemann_theta_g4_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g4_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g4_lattice(ep1,ep2,ep3,ep4, e1,e2,e3,e4, box,
    #                                   out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g4_lattice"):
        lib.srmech_riemann_theta_g4_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1..ep4
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1..e4
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g4_lattice.restype = ctypes.c_int
    # rc86: the NEXT GENUS RUNG (PAST the SCHOTTKY FRONTIER) — the GENUS-5 EXACT-INTEGER
    # EXPONENT LATTICE C peer (srmech_riemann_theta_g5). Emits the
    # [A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign] 16-tuple lattice over a box
    # (the genus-5 TEN cross-terms, each a denominator-4 clearing + the Class-K sign);
    # plain int64 16-tuples (the genus-5 theta-constant coefficients are small +-1 lattice
    # counts, no bignum). NEW symbols → hasattr-guarded; additive → EXPECTED_ABI_VERSION
    # stays 3.
    #   size_t srmech_riemann_theta_g5_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g5_count"):
        lib.srmech_riemann_theta_g5_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g5_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g5_lattice(ep1..ep5, e1..e5, box, out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g5_lattice"):
        lib.srmech_riemann_theta_g5_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1..ep5
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1..e5
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g5_lattice.restype = ctypes.c_int
    # rc87: EXACT theta evaluation at a RATIONAL argument (the genus-axis Fay-trisecant
    # / KP-Hirota FOUNDATION). srmech_riemann_theta_at (g2) emits [A,B,C,e_mod,sign]
    # quintuples; srmech_riemann_theta_g3_at (g3) emits the 8-tuple. NEW symbols →
    # hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_at_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_at_count"):
        lib.srmech_riemann_theta_at_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_at_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_at(ep1,ep2,e1,e2, z1,z2,m, box, out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_at"):
        lib.srmech_riemann_theta_at.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,   # ep1,ep2,e1,e2
            ctypes.c_int64, ctypes.c_int64, ctypes.c_int64,           # z1, z2, m
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_at.restype = ctypes.c_int
    #   size_t srmech_riemann_theta_g3_at_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g3_at_count"):
        lib.srmech_riemann_theta_g3_at_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g3_at_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g3_at(ep1,ep2,ep3,e1,e2,e3, z1,z2,z3,m, box, out[],
    #                              out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g3_at"):
        lib.srmech_riemann_theta_g3_at.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int,                 # ep1,ep2,ep3
            ctypes.c_int, ctypes.c_int, ctypes.c_int,                 # e1,e2,e3
            ctypes.c_int64, ctypes.c_int64, ctypes.c_int64,           # z1,z2,z3
            ctypes.c_int64,                   # m
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g3_at.restype = ctypes.c_int
    # rc88: srmech_riemann_theta_cyc_mul — the exact ℤ[ζ_m] power-basis multiply (the
    # genus-axis Fay/Hirota bilinear verifier's only new exact-integer kernel). NEW symbol
    # → hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   srmech_riemann_theta_cyc_mul(a[deg], b[deg], deg, table[m*deg], m, out[deg])
    if hasattr(lib, "srmech_riemann_theta_cyc_mul"):
        lib.srmech_riemann_theta_cyc_mul.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # a[deg]
            ctypes.POINTER(ctypes.c_int64),   # b[deg]
            ctypes.c_uint32,                  # deg
            ctypes.POINTER(ctypes.c_int64),   # table[m*deg]
            ctypes.c_uint32,                  # m
            ctypes.POINTER(ctypes.c_int64),   # out[deg]
        ]
        lib.srmech_riemann_theta_cyc_mul.restype = ctypes.c_int
    # rc81: the GENUS-4 CAPSTONE — the SCHOTTKY FORM J = theta^4(E8+E8) - theta^4(E16)
    # representation-number COUNTER (srmech_riemann_theta_g4_schottky_count). Counts
    # ordered g-tuples of minimal (doubled) lattice vectors with a prescribed off-diagonal
    # doubled Gram (genus 1/2/3/4) over a caller bitset arena. NEW symbols →
    # hasattr-guarded; additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_g4_schottky_arena(size_t n)
    if hasattr(lib, "srmech_riemann_theta_g4_schottky_arena"):
        lib.srmech_riemann_theta_g4_schottky_arena.argtypes = [ctypes.c_size_t]
        lib.srmech_riemann_theta_g4_schottky_arena.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g4_schottky_count(vecs[], n, dim, genus, gram_off[],
    #                                          arena[], arena_cap, *out_count)
    if hasattr(lib, "srmech_riemann_theta_g4_schottky_count"):
        lib.srmech_riemann_theta_g4_schottky_count.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # vecs[] (n*dim, doubled)
            ctypes.c_size_t,                  # n
            ctypes.c_size_t,                  # dim
            ctypes.c_int,                     # genus
            ctypes.POINTER(ctypes.c_int64),   # gram_off[]
            ctypes.POINTER(ctypes.c_uint64),  # arena[]
            ctypes.c_size_t,                  # arena_cap
            ctypes.POINTER(ctypes.c_int64),   # *out_count
        ]
        lib.srmech_riemann_theta_g4_schottky_count.restype = ctypes.c_int
    #   size_t srmech_riemann_theta_g4_schottky_shell_count(int genus)
    if hasattr(lib, "srmech_riemann_theta_g4_schottky_shell_count"):
        lib.srmech_riemann_theta_g4_schottky_shell_count.argtypes = [ctypes.c_int]
        lib.srmech_riemann_theta_g4_schottky_shell_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g4_schottky_shell(vecs[], n, dim, genus, arena[],
    #                                          arena_cap, out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g4_schottky_shell"):
        lib.srmech_riemann_theta_g4_schottky_shell.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # vecs[]
            ctypes.c_size_t,                  # n
            ctypes.c_size_t,                  # dim
            ctypes.c_int,                     # genus
            ctypes.POINTER(ctypes.c_uint64),  # arena[]
            ctypes.c_size_t,                  # arena_cap
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g4_schottky_shell.restype = ctypes.c_int
    # rc76: IGUSA'S chi_18 — the EXACT product of the 36 even genus-3 theta-nulls
    # (srmech_riemann_theta_g3_chi18). Emits the leading-part [A1,A2,A3,C12,C13,C23,
    # coeff] septuples (the cusp-vanishing structure of the 36-even-null product) over a
    # caller-arena work[] (sized via the count helper). int64-exact (max |coeff|=2^34, no
    # bignum). NEW symbols -> hasattr-guarded; additive -> EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_g3_chi18_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g3_chi18_count"):
        lib.srmech_riemann_theta_g3_chi18_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g3_chi18_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g3_chi18(box, work[], work_cap, out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g3_chi18"):
        lib.srmech_riemann_theta_g3_chi18.argtypes = [
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # work[]
            ctypes.c_size_t,                  # work_cap
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g3_chi18.restype = ctypes.c_int
    # rc77: the genus-3 Sp(6,Z) characteristic TRANSFORMATION + the genus-3 EIGHTH-nome
    # lattice (the addition gate) — the g=2->g=3 parametric extension of the rc73 peers.
    # Two additive C peers; NEW symbols → hasattr-guarded; additive → ABI stays 3.
    #   srmech_riemann_theta_g3_sp6_char(gamma[36], ep1,ep2,ep3,e1,e2,e3,
    #                                    out_char[6], *kexp)
    #   gamma is the 36 int entries (A,B,C,D 3x3 blocks row-major); out_char is the 6
    #   transformed bits (ep1',ep2',ep3',e1',e2',e3'); *kexp is the 8th-root exponent
    #   k in Z/8. Returns SRMECH_ERR_BAD_INPUT if gamma is not symplectic.
    if hasattr(lib, "srmech_riemann_theta_g3_sp6_char"):
        lib.srmech_riemann_theta_g3_sp6_char.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # gamma[36]
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1,ep2,ep3
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1,e2,e3
            ctypes.POINTER(ctypes.c_int),     # out_char[6]
            ctypes.POINTER(ctypes.c_int),     # *kexp
        ]
        lib.srmech_riemann_theta_g3_sp6_char.restype = ctypes.c_int
    #   size_t srmech_riemann_theta_g3_eighth_count(uint32_t box)
    #   shape: (2*box+1)^3 points * 7 int64 [A1,A2,A3,C12,C13,C23,sign]
    if hasattr(lib, "srmech_riemann_theta_g3_eighth_count"):
        lib.srmech_riemann_theta_g3_eighth_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g3_eighth_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g3_eighth_lattice(s1,s2,s3,e1,e2,e3, at_two_omega, box,
    #                                          out[], out_cap, *out_len)
    #   at_two_omega: 0 -> theta at Omega (A=2(2n+s)^2 ...); 1 -> at 2Omega
    #   (A=(4n+s)^2 ...). s1,s2,s3 are the DOUBLED upper characteristic (any int).
    if hasattr(lib, "srmech_riemann_theta_g3_eighth_lattice"):
        lib.srmech_riemann_theta_g3_eighth_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # s1,s2,s3
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1,e2,e3
            ctypes.c_int,                     # at_two_omega (0/1)
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g3_eighth_lattice.restype = ctypes.c_int
    # rc78: the genus-3 GÖPEL / FROBENIUS quadratic theta-null SYZYGY gate
    # (srmech_riemann_theta_g3_goepel). Decides the 4-pair / 8-null same-Omega syzygy
    # over the box-stable safe region; *out_holds <- LHS==RHS, *out_has_cross <- genuine
    # genus-3 cross-term present. Caller-arena work[] (sized via the count helper). NEW
    # symbols -> hasattr-guarded; additive -> EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_riemann_theta_g3_goepel_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g3_goepel_count"):
        lib.srmech_riemann_theta_g3_goepel_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g3_goepel_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g3_goepel(box, work[], work_cap, *out_holds, *out_has_cross)
    if hasattr(lib, "srmech_riemann_theta_g3_goepel"):
        lib.srmech_riemann_theta_g3_goepel.argtypes = [
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # work[]
            ctypes.c_size_t,                  # work_cap
            ctypes.POINTER(ctypes.c_int),     # *out_holds
            ctypes.POINTER(ctypes.c_int),     # *out_has_cross
        ]
        lib.srmech_riemann_theta_g3_goepel.restype = ctypes.c_int
    # rc85: the genus-4 Sp(8,ℤ) characteristic TRANSFORMATION + the genus-4 EIGHTH-nome
    # lattice (the addition gate) + the genus-4 Göpel relation gate — the g=3->g=4
    # parametric extension of the rc77/rc78 genus-3 peers. NEW symbols → hasattr-guarded;
    # additive → ABI stays 3.
    #   srmech_riemann_theta_g4_sp8_char(gamma[64], ep1,ep2,ep3,ep4,e1,e2,e3,e4,
    #                                    out_char[8], *kexp)
    #   gamma is the 64 int entries (A,B,C,D 4x4 blocks row-major); out_char is the 8
    #   transformed bits (ep1'..ep4',e1'..e4'); *kexp is the 8th-root exponent k in Z/8.
    #   Returns SRMECH_ERR_BAD_INPUT if gamma is not symplectic.
    if hasattr(lib, "srmech_riemann_theta_g4_sp8_char"):
        lib.srmech_riemann_theta_g4_sp8_char.argtypes = [
            ctypes.POINTER(ctypes.c_int64),   # gamma[64]
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # ep1..ep4
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1..e4
            ctypes.POINTER(ctypes.c_int),     # out_char[8]
            ctypes.POINTER(ctypes.c_int),     # *kexp
        ]
        lib.srmech_riemann_theta_g4_sp8_char.restype = ctypes.c_int
    #   size_t srmech_riemann_theta_g4_eighth_count(uint32_t box)
    #   shape: (2*box+1)^4 points * 11 int64 [A1..A4,C12,C13,C14,C23,C24,C34,sign]
    if hasattr(lib, "srmech_riemann_theta_g4_eighth_count"):
        lib.srmech_riemann_theta_g4_eighth_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g4_eighth_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g4_eighth_lattice(s1..s4,e1..e4, at_two_omega, box,
    #                                          out[], out_cap, *out_len)
    if hasattr(lib, "srmech_riemann_theta_g4_eighth_lattice"):
        lib.srmech_riemann_theta_g4_eighth_lattice.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # s1..s4
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # e1..e4
            ctypes.c_int,                     # at_two_omega (0/1)
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # out[]
            ctypes.c_size_t,                  # out_cap
            ctypes.POINTER(ctypes.c_size_t),  # *out_len
        ]
        lib.srmech_riemann_theta_g4_eighth_lattice.restype = ctypes.c_int
    #   size_t srmech_riemann_theta_g4_goepel_count(uint32_t box)
    if hasattr(lib, "srmech_riemann_theta_g4_goepel_count"):
        lib.srmech_riemann_theta_g4_goepel_count.argtypes = [ctypes.c_uint32]
        lib.srmech_riemann_theta_g4_goepel_count.restype = ctypes.c_size_t
    #   srmech_riemann_theta_g4_goepel(box, work[], work_cap, *out_holds, *out_has_cross)
    if hasattr(lib, "srmech_riemann_theta_g4_goepel"):
        lib.srmech_riemann_theta_g4_goepel.argtypes = [
            ctypes.c_uint32,                  # box
            ctypes.POINTER(ctypes.c_int64),   # work[]
            ctypes.c_size_t,                  # work_cap
            ctypes.POINTER(ctypes.c_int),     # *out_holds
            ctypes.POINTER(ctypes.c_int),     # *out_has_cross
        ]
        lib.srmech_riemann_theta_g4_goepel.restype = ctypes.c_int
    # rc54: the EXACT q-shift CARRIER C peer (srmech_qpoly_*) — the q-analog of
    # the poly carrier, the q-hypergeometric F929 reduction-row foundation. A
    # QPoly is a ROW of q-Poly cells over an x-window; the bridge flattens the
    # row of q-runs into a single concatenated _SrmechBigint pair + a qlen[]
    # array (mirroring tripoly), plus the q-shift. NEW symbols → hasattr-guarded;
    # additive → EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_qpoly_ws_bound(size_t coeff_limbs, size_t n_terms)
    if hasattr(lib, "srmech_qpoly_ws_bound"):
        lib.srmech_qpoly_ws_bound.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_qpoly_ws_bound.restype = ctypes.c_size_t
    # add / sub share the x-index-aligned cellwise shape
    #   fn(a_n,a_d,a_qlen,cells, b_n,b_d,b_qlen, out_n,out_d,out_qlen, ws,wl)
    _QPOLY_ADDSUB_SIG = [
        ctypes.POINTER(_SrmechBigint),   # a_n[]
        ctypes.POINTER(_SrmechBigint),   # a_d[]
        ctypes.POINTER(ctypes.c_size_t), # a_qlen[]
        ctypes.c_size_t,                 # cells
        ctypes.POINTER(_SrmechBigint),   # b_n[]
        ctypes.POINTER(_SrmechBigint),   # b_d[]
        ctypes.POINTER(ctypes.c_size_t), # b_qlen[]
        ctypes.POINTER(_SrmechBigint),   # out_n[]
        ctypes.POINTER(_SrmechBigint),   # out_d[]
        ctypes.POINTER(ctypes.c_size_t), # out_qlen[]
        ctypes.c_void_p,                 # ws
        ctypes.c_size_t,                 # ws_len
    ]
    for _qpop in ("srmech_qpoly_add", "srmech_qpoly_sub"):
        if hasattr(lib, _qpop):
            getattr(lib, _qpop).argtypes = list(_QPOLY_ADDSUB_SIG)
            getattr(lib, _qpop).restype = ctypes.c_int
    #   srmech_qpoly_mul(a_n,a_d,a_qlen,acells, b_n,b_d,b_qlen,bcells,
    #                    out_n,out_d,out_qlen, out_off, accum, ws,wl)
    if hasattr(lib, "srmech_qpoly_mul"):
        lib.srmech_qpoly_mul.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qpoly_mul.restype = ctypes.c_int
    #   srmech_qpoly_qshift(a_n,a_d,a_qlen,cells, s, x_low,
    #                       out_n,out_d,out_qlen, out_off, ws,wl)
    if hasattr(lib, "srmech_qpoly_qshift"):
        lib.srmech_qpoly_qshift.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t,
            ctypes.c_int64, ctypes.c_int64,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qpoly_qshift.restype = ctypes.c_int
    # rc52: the EXACT-RATIONAL TRIVARIATE polynomial carrier C peer
    # (srmech_tripoly_*) — the 3-variable sibling of BiPoly, the multivariate
    # "sums of sums" creative-telescoping foundation. A TriPoly is a ROW-MAJOR
    # (j,k) grid of n-Poly coefficient runs over the same bignum substrate as poly
    # (no int64/Q61 ceiling). NEW symbols → hasattr-guarded; additive →
    # EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_tripoly_ws_bound(size_t coeff_limbs, size_t n_terms)
    if hasattr(lib, "srmech_tripoly_ws_bound"):
        lib.srmech_tripoly_ws_bound.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_tripoly_ws_bound.restype = ctypes.c_size_t
    # add / sub share the cellwise-aligned grid shape
    #   fn(a_n,a_d,a_nlen,cells, b_n,b_d,b_nlen, out_n,out_d,out_nlen, ws,wl)
    _TRIPOLY_ADDSUB_SIG = [
        ctypes.POINTER(_SrmechBigint),   # a_n[]
        ctypes.POINTER(_SrmechBigint),   # a_d[]
        ctypes.POINTER(ctypes.c_size_t), # a_nlen[]
        ctypes.c_size_t,                 # cells
        ctypes.POINTER(_SrmechBigint),   # b_n[]
        ctypes.POINTER(_SrmechBigint),   # b_d[]
        ctypes.POINTER(ctypes.c_size_t), # b_nlen[]
        ctypes.POINTER(_SrmechBigint),   # out_n[]
        ctypes.POINTER(_SrmechBigint),   # out_d[]
        ctypes.POINTER(ctypes.c_size_t), # out_nlen[]
        ctypes.c_void_p,                 # ws
        ctypes.c_size_t,                 # ws_len
    ]
    for _trop in ("srmech_tripoly_add", "srmech_tripoly_sub"):
        if hasattr(lib, _trop):
            getattr(lib, _trop).argtypes = list(_TRIPOLY_ADDSUB_SIG)
            getattr(lib, _trop).restype = ctypes.c_int
    #   srmech_tripoly_mul(a_n,a_d,a_nlen,aj,ak, b_n,b_d,b_nlen,bj,bk,
    #                      out_n,out_d,out_nlen, out_off, ocols, accum, ws,wl)
    if hasattr(lib, "srmech_tripoly_mul"):
        lib.srmech_tripoly_mul.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_size_t), ctypes.c_size_t, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_tripoly_mul.restype = ctypes.c_int
    # rc40: the EXACT-RATIONAL matrix carrier C peer (srmech_qmat_*) — the exact
    # ℚ-linear-algebra peer of srmech.amsc.qmat.QMat (the §76 gosper exact solve
    # foundation). Each op takes ROW-MAJOR parallel _SrmechBigint entry arrays.
    #   size_t srmech_qmat_ws_bound(coeff_limbs, n_rows, total_cols)
    #   size_t srmech_qmat_entry_cap(coeff_limbs, n_rows, total_cols)
    for _qsz in ("srmech_qmat_ws_bound", "srmech_qmat_entry_cap"):
        if hasattr(lib, _qsz):
            getattr(lib, _qsz).argtypes = [
                ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
            getattr(lib, _qsz).restype = ctypes.c_size_t
    #   srmech_qmat_rref(a_n,a_d, n_rows,n_cols, o_n,o_d, *rank, piv[], ws,wl)
    if hasattr(lib, "srmech_qmat_rref"):
        lib.srmech_qmat_rref.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_rref.restype = ctypes.c_int
    #   srmech_qmat_rank(a_n,a_d, n_rows,n_cols, *rank, ws,wl)
    if hasattr(lib, "srmech_qmat_rank"):
        lib.srmech_qmat_rank.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_rank.restype = ctypes.c_int
    #   srmech_qmat_det(a_n,a_d, n, o_num,o_den, ws,wl)
    if hasattr(lib, "srmech_qmat_det"):
        lib.srmech_qmat_det.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_det.restype = ctypes.c_int
    #   srmech_qmat_inverse(a_n,a_d, n, o_n,o_d, *singular, ws,wl)
    if hasattr(lib, "srmech_qmat_inverse"):
        lib.srmech_qmat_inverse.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_inverse.restype = ctypes.c_int
    #   srmech_qmat_solve(a_n,a_d, n, b_n,b_d, b_cols, o_n,o_d, *singular, ws,wl)
    if hasattr(lib, "srmech_qmat_solve"):
        lib.srmech_qmat_solve.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_solve.restype = ctypes.c_int
    #   srmech_qmat_nullspace(a_n,a_d, n_rows,n_cols, o_n,o_d, *nfree, ws,wl)
    if hasattr(lib, "srmech_qmat_nullspace"):
        lib.srmech_qmat_nullspace.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_nullspace.restype = ctypes.c_int
    # rc48: srmech_qmat_rref_crt — the CRT re-fibration of the exact-Q RREF as ONE
    # standalone C symbol (the CLOSER of the CRT-QMat arc). Same wire shape as
    # srmech_qmat_rref; bounded (answer-sized) arena via srmech_qmat_rref_crt_ws_bound.
    #   size_t srmech_qmat_rref_crt_ws_bound(coeff_limbs, n_rows, n_cols)
    #   size_t srmech_qmat_rref_crt_entry_cap(coeff_limbs, n_rows, n_cols)
    for _csz in ("srmech_qmat_rref_crt_ws_bound", "srmech_qmat_rref_crt_entry_cap"):
        if hasattr(lib, _csz):
            getattr(lib, _csz).argtypes = [
                ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
            getattr(lib, _csz).restype = ctypes.c_size_t
    #   srmech_qmat_rref_crt(a_n,a_d, n_rows,n_cols, o_n,o_d, *rank, piv[], ws,wl)
    if hasattr(lib, "srmech_qmat_rref_crt"):
        lib.srmech_qmat_rref_crt.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_qmat_rref_crt.restype = ctypes.c_int

    # rc41: srmech_gosper — Gosper's indefinite hypergeometric summation (the §76
    # telescope Sigma-row's first public op). Orchestrates the exact-Q poly/qmat
    # kernels into one caller-arena symbol. Term ratio num/den (parallel
    # _SrmechBigint coefficient arrays) -> the rational certificate R = r_num/r_den
    # (or "no solution"). NEW symbols -> hasattr-guarded; additive -> ABI stays 3.
    #   size_t srmech_gosper_ws_bound(coeff_limbs, degree)
    #   size_t srmech_gosper_out_cap(coeff_limbs, degree)
    for _gsz in ("srmech_gosper_ws_bound", "srmech_gosper_out_cap"):
        if hasattr(lib, _gsz):
            getattr(lib, _gsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t]
            getattr(lib, _gsz).restype = ctypes.c_size_t
    #   srmech_gosper(num_n,num_d,n_num, den_n,den_d,n_den, *has,
    #       r_num_n,r_num_d,*rnum, r_den_n,r_den_d,*rden, ws,wl)
    if hasattr(lib, "srmech_gosper"):
        lib.srmech_gosper.argtypes = [
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(_SrmechBigint), ctypes.POINTER(_SrmechBigint),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.srmech_gosper.restype = ctypes.c_int

    # rc55: srmech_q_gosper — the q-analog of Gosper (the FIRST public op of the
    # q-hypergeometric F929 row). The two QPoly term-ratio operands ride in the
    # QPoly bridge form (concatenated ascending-q (num, den) runs + a per-x-cell
    # qlen[] array + the x_low offset); the certificate R = rn/rd comes back the
    # same way. The native peer completes the constant-ratio case + declines the
    # rest (has=0 -> Python re-decides). NEW symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_q_gosper_ws_bound(coeff_limbs, qdeg)
    #   size_t srmech_q_gosper_out_cap(coeff_limbs, qdeg)
    for _qgsz in ("srmech_q_gosper_ws_bound", "srmech_q_gosper_out_cap"):
        if hasattr(lib, _qgsz):
            getattr(lib, _qgsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t]
            getattr(lib, _qgsz).restype = ctypes.c_size_t
    if hasattr(lib, "srmech_q_gosper"):
        _qbi = ctypes.POINTER(_SrmechBigint)
        _qszp = ctypes.POINTER(ctypes.c_size_t)
        lib.srmech_q_gosper.argtypes = [
            _qbi, _qbi, _qszp, ctypes.c_size_t, ctypes.c_int64,  # num n/d, qlen, cells, xlow
            _qbi, _qbi, _qszp, ctypes.c_size_t, ctypes.c_int64,  # den
            ctypes.POINTER(ctypes.c_int),                        # out_has
            _qbi, _qbi, _qszp, _qszp, ctypes.POINTER(ctypes.c_int64),  # rn n/d, qlen, cells, xlow
            _qbi, _qbi, _qszp, _qszp, ctypes.POINTER(ctypes.c_int64),  # rd n/d, qlen, cells, xlow
            ctypes.c_void_p, ctypes.c_size_t,                    # ws, ws_len
        ]
        lib.srmech_q_gosper.restype = ctypes.c_int

    # srmech_elliptic_gosper — the GENUINE ELLIPTIC analog of Gosper (the FIRST engine
    # op of the ELLIPTIC F929 row). The term-ratio rides as the FULL EllRatio wire form
    # (the interned symbol-table dimension + the x/p/q interned indices + the num/den
    # theta counts + the flat exact-Q monomial coeff arrays + the flat int32 exponent
    # rows, like srmech_ellratio_is_elliptic); the certificate EllRatio comes back as
    # out_pref_num/out_pref_den + the flat out_exps_flat rows + the out_n_num/out_n_den
    # counts. The native peer runs the genuine peel + Weierstrass-key-equation solve +
    # exact ThetaSum.is_zero verify; it declines the rest (has=0 -> Python re-decides).
    # NEW signature (the genuine rebuild) -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_elliptic_gosper_ws_bound(n_syms, n_num, n_den, coeff_limbs)
    #   size_t srmech_elliptic_gosper_out_cap(coeff_limbs)
    if hasattr(lib, "srmech_elliptic_gosper_ws_bound"):
        lib.srmech_elliptic_gosper_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_gosper_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_gosper_out_cap"):
        lib.srmech_elliptic_gosper_out_cap.argtypes = [ctypes.c_size_t]
        lib.srmech_elliptic_gosper_out_cap.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_gosper"):
        _ebi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_gosper.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, psym, qsym
            ctypes.c_size_t, ctypes.c_size_t,    # n_num, n_den
            _ebi, _ebi,                          # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_has
            _ebi, _ebi,                          # out_pref_num, out_pref_den
            ctypes.POINTER(ctypes.c_int32),      # out_exps_flat
            ctypes.c_size_t,                     # out_exps_cap_rows
            ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),  # out_n_num/den
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_gosper.restype = ctypes.c_int

    # rc63: srmech_thetasum_is_zero — the C peer of the ThetaSum carrier's is_zero (the
    # load-bearing EXACT Weierstrass three-term + quasi-periodicity decision). The
    # cleared numerator rides as the interned symbol-table dimension + the p/x/y
    # indices + the per-term theta counts + the flat monomial coeff arrays
    # (coeff_num/coeff_den) + the flat int32 exponent rows. *out_is_zero comes back.
    #   size_t srmech_thetasum_ws_bound(n_syms, n_terms, max_thetas, coeff_limbs)
    if hasattr(lib, "srmech_thetasum_ws_bound"):
        lib.srmech_thetasum_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_thetasum_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_thetasum_is_zero"):
        _tbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_thetasum_is_zero.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, ysym, psym
            ctypes.c_size_t,                     # n_terms
            ctypes.POINTER(ctypes.c_size_t),     # term_nthetas
            _tbi, _tbi,                          # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_is_zero
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_thetasum_is_zero.restype = ctypes.c_int

    # rc99: srmech_thetasum_is_zero_interpolation — the C peer of the ThetaSum
    # STRUCTURAL ELLIPTIC-INTERPOLATION is_zero completion (the COMPLETE multi-
    # variable elliptic decision; the pure-Python ThetaSum._is_zero_interpolation
    # parity oracle). SAME wire form as srmech_thetasum_is_zero (n_syms + p/x/y
    # indices + per-term theta counts + flat monomial coeff/exps). The ws sizer
    # additionally takes max_abs_exp for degree-aware base-case band sizing.
    #   size_t srmech_thetasum_is_zero_interpolation_ws_bound(
    #       n_syms, n_terms, max_thetas, coeff_limbs, max_abs_exp)
    if hasattr(lib, "srmech_thetasum_is_zero_interpolation_ws_bound"):
        lib.srmech_thetasum_is_zero_interpolation_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
            ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_thetasum_is_zero_interpolation_ws_bound.restype = ctypes.c_size_t
    # rc102: the degree-aware sizer. Adds max_theta_sq_sum (the TRUE ti_deg base-case
    # band degree = max over terms of SUM of squared THETA exponents in a base var) so
    # the base case (>=2 same-var thetas: SUM(e^2) >> max(e^2)) is not UNDER-sized -> no
    # SRMECH_ERR_OVERFLOW false-decline. Additive symbol -> EXPECTED_ABI_VERSION stays 3.
    #   size_t srmech_thetasum_is_zero_interpolation_ws_bound2(
    #       n_syms, n_terms, max_thetas, coeff_limbs, max_abs_exp, max_theta_sq_sum)
    if hasattr(lib, "srmech_thetasum_is_zero_interpolation_ws_bound2"):
        lib.srmech_thetasum_is_zero_interpolation_ws_bound2.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_thetasum_is_zero_interpolation_ws_bound2.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_thetasum_is_zero_interpolation"):
        _tbi2 = ctypes.POINTER(_SrmechBigint)
        lib.srmech_thetasum_is_zero_interpolation.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, ysym, psym
            ctypes.c_size_t,                     # n_terms
            ctypes.POINTER(ctypes.c_size_t),     # term_nthetas
            _tbi2, _tbi2,                        # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_is_zero
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_thetasum_is_zero_interpolation.restype = ctypes.c_int

    # rc64: srmech_ellratio_is_elliptic — the C peer of the EllRatio carrier's
    # is_elliptic (the BALANCING / very-well-poised predicate = pshift() == self). The
    # canonical EllRatio rides as the interned symbol-table dimension + the x/p indices
    # + the numerator/denominator theta counts + the flat monomial coeff arrays
    # (coeff_num/coeff_den, in order prefactor, num0..K, den0..L) + the flat int32
    # exponent rows. *out_is_elliptic comes back. Shares the srmech_bigint decimal
    # marshal helpers (already in _THETASUM_SYMS) with the thetasum peer.
    #   size_t srmech_ellratio_ws_bound(n_syms, n_num, n_den, coeff_limbs)
    if hasattr(lib, "srmech_ellratio_ws_bound"):
        lib.srmech_ellratio_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_ellratio_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_ellratio_is_elliptic"):
        _ebi2 = ctypes.POINTER(_SrmechBigint)
        lib.srmech_ellratio_is_elliptic.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int,          # xsym, psym
            ctypes.c_size_t, ctypes.c_size_t,    # n_num, n_den
            _ebi2, _ebi2,                        # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_is_elliptic
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_ellratio_is_elliptic.restype = ctypes.c_int

    # rc67: srmech_elliptic_lagrange_basis — the C peer of the EllRatio-carrier op
    # srmech.amsc.ellbase.elliptic_lagrange_basis (rc66, Python-only; C mirror owed
    # by the everything-mirrors same-rc discipline). The k point monomials ride as
    # flat (coeff_num/coeff_den) srmech_bigint arrays + the flat int32 exponent rows;
    # the multiplier as a single monomial; the k basis EllRatios come back as the
    # per-element prefactor coeff arrays + the per-element theta counts + the flat
    # canonical exponent rows. Shares the srmech_bigint decimal-marshal helpers (in
    # _ELLRATIO_SYMS) with the ellratio / thetasum peers.
    #   size_t srmech_elliptic_lagrange_basis_ws_bound(n_syms, k, coeff_limbs)
    if hasattr(lib, "srmech_elliptic_lagrange_basis_ws_bound"):
        lib.srmech_elliptic_lagrange_basis_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_lagrange_basis_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_lagrange_basis"):
        _ebi3 = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_lagrange_basis.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int,          # varsym, psym
            ctypes.c_size_t,                     # k
            _ebi3, _ebi3,                        # pt_coeff_num, pt_coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # pt_exps_flat
            _ebi3, _ebi3,                        # mult_num, mult_den
            ctypes.POINTER(ctypes.c_int32),      # mult_exps
            ctypes.c_uint32,                     # coeff_cap
            _ebi3, _ebi3,                        # out_coeff_num, out_coeff_den (per row)
            ctypes.POINTER(ctypes.c_int32),      # out_exps_flat
            ctypes.c_size_t,                     # out_exps_cap_rows
            ctypes.POINTER(ctypes.c_size_t),     # out_n_num (k)
            ctypes.POINTER(ctypes.c_size_t),     # out_n_den (k)
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_lagrange_basis.restype = ctypes.c_int

    # rc94: srmech_elliptic_cauchy_determinant — the C peer of the EllRatio-carrier op
    # srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant (Frobenius's elliptic
    # Cauchy determinant, the foundation of the multivariable Cₙ elliptic reduction row).
    # The parameter t + the n x-monomials + the n y-monomials ride as flat
    # (coeff_num/coeff_den) srmech_bigint arrays + the flat int32 exponent rows; the single
    # closed-form EllRatio comes back as the per-row prefactor/theta coeff arrays + the
    # survivor theta counts + the flat canonical exponent rows. Shares the srmech_bigint
    # decimal-marshal helpers (in _ELLRATIO_SYMS) with the ellratio / lagrange peers.
    #   size_t srmech_elliptic_cauchy_determinant_ws_bound(n_syms, n, coeff_limbs)
    if hasattr(lib, "srmech_elliptic_cauchy_determinant_ws_bound"):
        lib.srmech_elliptic_cauchy_determinant_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_cauchy_determinant_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_cauchy_determinant"):
        _ecdbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_cauchy_determinant.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int,                        # psym
            ctypes.c_size_t,                     # n
            _ecdbi, _ecdbi,                      # t_num, t_den
            ctypes.POINTER(ctypes.c_int32),      # t_exps
            _ecdbi, _ecdbi,                      # xs_num, xs_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # xs_exps_flat
            _ecdbi, _ecdbi,                      # ys_num, ys_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # ys_exps_flat
            ctypes.c_uint32,                     # coeff_cap
            _ecdbi, _ecdbi,                      # out_coeff_num, out_coeff_den (per row)
            ctypes.POINTER(ctypes.c_int32),      # out_exps_flat
            ctypes.c_size_t,                     # out_exps_cap_rows
            ctypes.POINTER(ctypes.c_size_t),     # out_n_num (1)
            ctypes.POINTER(ctypes.c_size_t),     # out_n_den (1)
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_cauchy_determinant.restype = ctypes.c_int

    # rc95: srmech_elliptic_partial_fraction — the C peer of the ThetaSum-returning op
    # srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction (the elliptic
    # partial-fraction expansion, the reduction engine of the multivariable Cₙ elliptic
    # row). The variable x + the n z-monomials + the n y-monomials ride as flat
    # (coeff_num/coeff_den) srmech_bigint arrays + the flat int32 exponent rows; the n
    # TERM EllRatios come back as the per-row prefactor/theta coeff arrays + the per-term
    # survivor theta counts (out_n_num[n] / out_n_den[n]) + the flat canonical exponent
    # rows (the Python side sums the n forms into the ThetaSum). Shares the srmech_bigint
    # decimal-marshal helpers (in _ELLRATIO_SYMS) with the ellratio / lagrange peers.
    #   size_t srmech_elliptic_partial_fraction_ws_bound(n_syms, n, coeff_limbs)
    if hasattr(lib, "srmech_elliptic_partial_fraction_ws_bound"):
        lib.srmech_elliptic_partial_fraction_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_partial_fraction_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_partial_fraction"):
        _epfbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_partial_fraction.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int,                        # psym
            ctypes.c_size_t,                     # n
            _epfbi, _epfbi,                      # x_num, x_den
            ctypes.POINTER(ctypes.c_int32),      # x_exps
            _epfbi, _epfbi,                      # zs_num, zs_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # zs_exps_flat
            _epfbi, _epfbi,                      # ys_num, ys_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # ys_exps_flat
            ctypes.c_uint32,                     # coeff_cap
            _epfbi, _epfbi,                      # out_coeff_num, out_coeff_den (per row)
            ctypes.POINTER(ctypes.c_int32),      # out_exps_flat
            ctypes.c_size_t,                     # out_exps_cap_rows
            ctypes.POINTER(ctypes.c_size_t),     # out_n_num (n)
            ctypes.POINTER(ctypes.c_size_t),     # out_n_den (n)
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_partial_fraction.restype = ctypes.c_int

    # rc96: srmech_multivariate_elliptic_jackson — the C peer of the EllRatio-carrier op
    # srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson (the eq-5 Cₙ
    # elliptic Jackson summation reducer, the capstone of the multivariable Cₙ elliptic
    # reduction row). The parameters a, b, c, d + the base variables x, q ride as
    # (coeff_num/coeff_den) srmech_bigint pairs + their flat int32 exponent rows; the two
    # positive ints N (partition ceiling) + n (rank) size the vector Pochhammer. The single
    # closed-form EllRatio comes back as the per-row prefactor/theta coeff arrays + the
    # survivor theta counts (out_n_num[1] / out_n_den[1]) + the flat canonical exponent rows.
    # Mirrors rc94's single-EllRatio elliptic_cauchy_determinant wire form. Shares the
    # srmech_bigint decimal-marshal helpers (in _ELLRATIO_SYMS) with the ellratio peers.
    #   size_t srmech_multivariate_elliptic_jackson_ws_bound(n_syms, N, n, coeff_limbs)
    if hasattr(lib, "srmech_multivariate_elliptic_jackson_ws_bound"):
        lib.srmech_multivariate_elliptic_jackson_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_multivariate_elliptic_jackson_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_multivariate_elliptic_jackson"):
        _mejbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_multivariate_elliptic_jackson.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int,                        # psym
            ctypes.c_size_t,                     # N (partition ceiling)
            ctypes.c_size_t,                     # n (rank)
            _mejbi, _mejbi, ctypes.POINTER(ctypes.c_int32),   # a_num, a_den, a_exps
            _mejbi, _mejbi, ctypes.POINTER(ctypes.c_int32),   # b_num, b_den, b_exps
            _mejbi, _mejbi, ctypes.POINTER(ctypes.c_int32),   # c_num, c_den, c_exps
            _mejbi, _mejbi, ctypes.POINTER(ctypes.c_int32),   # d_num, d_den, d_exps
            _mejbi, _mejbi, ctypes.POINTER(ctypes.c_int32),   # x_num, x_den, x_exps
            _mejbi, _mejbi, ctypes.POINTER(ctypes.c_int32),   # q_num, q_den, q_exps
            ctypes.c_uint32,                     # coeff_cap
            _mejbi, _mejbi,                      # out_coeff_num, out_coeff_den (per row)
            ctypes.POINTER(ctypes.c_int32),      # out_exps_flat
            ctypes.c_size_t,                     # out_exps_cap_rows
            ctypes.POINTER(ctypes.c_size_t),     # out_n_num (1)
            ctypes.POINTER(ctypes.c_size_t),     # out_n_den (1)
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_multivariate_elliptic_jackson.restype = ctypes.c_int

    # rc68: srmech_elliptic_recurrence_8w7 — the ELLIPTIC Σ-row ORDER-1 RECURRENCE op for
    # the Frenkel–Turaev ₈ω₇ summation. The C peer of
    # srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7. The term-ratio rides as the
    # FULL EllRatio wire form (the interned symbol-table dimension + the x/p/q/y interned
    # indices + the num/den theta counts + the flat exact-Q coeff arrays + the flat int32
    # exponent rows, like srmech_elliptic_gosper but with the added y index for the
    # recurrence axis); the recurrence coefficient ρ EllRatio comes back as
    # out_pref_num/out_pref_den + the flat out_exps_flat rows + the out_n_num/out_n_den
    # counts. The native peer runs the genuine recognize-decompose-construct; a has=0
    # (not ₈ω₇) -> Python re-decides. NEW symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_elliptic_recurrence_8w7_ws_bound(n_syms, n_num, n_den, coeff_limbs)
    #   size_t srmech_elliptic_recurrence_8w7_out_cap(coeff_limbs)
    if hasattr(lib, "srmech_elliptic_recurrence_8w7_ws_bound"):
        lib.srmech_elliptic_recurrence_8w7_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_recurrence_8w7_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_recurrence_8w7_out_cap"):
        lib.srmech_elliptic_recurrence_8w7_out_cap.argtypes = [ctypes.c_size_t]
        lib.srmech_elliptic_recurrence_8w7_out_cap.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_recurrence_8w7"):
        _erbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_recurrence_8w7.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, psym, qsym, ysym
            ctypes.c_size_t, ctypes.c_size_t,    # n_num, n_den
            _erbi, _erbi,                        # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_has
            _erbi, _erbi,                        # out_pref_num, out_pref_den
            ctypes.POINTER(ctypes.c_int32),      # out_exps_flat
            ctypes.c_size_t,                     # out_exps_cap_rows
            ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),  # out_n_num/den
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_recurrence_8w7.restype = ctypes.c_int

    # rc90: srmech_elliptic_zeilberger — the ELLIPTIC Σ-row CREATIVE-TELESCOPING op for
    # the Frenkel–Turaev ₈ω₇ summation. The C peer of
    # srmech.amsc.elliptic_zeilberger.elliptic_zeilberger. The term-ratio rides as the
    # SAME full EllRatio wire form srmech_elliptic_recurrence_8w7 parses (the interned
    # symbol-table dimension + the x/p/q/y interned indices + the num/den theta counts +
    # the flat exact-Q coeff arrays + the flat int32 exponent rows), PLUS the two extra
    # interned indices nsym/ksym for the certificate's recurrence index symbols N = qⁿ,
    # K = qᵏ. The peer recognizes + decomposes the ₈ω₇, builds the connection-coefficient
    # split certificate (Rosengren Eq. 2.12–2.14 → Eq. 1.12) and decides it ≡ 0 via the
    # shared srmech_thetasum_is_zero kernel; *out_has comes back (1 iff recognized AND the
    # certificate is exactly zero). No ρ emission (the Python builds + re-verifies ρ). NEW
    # symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_elliptic_zeilberger_ws_bound(n_syms, n_num, n_den, coeff_limbs)
    if hasattr(lib, "srmech_elliptic_zeilberger_ws_bound"):
        lib.srmech_elliptic_zeilberger_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_zeilberger_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_zeilberger"):
        _ezbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_zeilberger.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, psym, qsym, ysym
            ctypes.c_int, ctypes.c_int,          # nsym, ksym (the cert's N = qⁿ, K = qᵏ)
            ctypes.c_size_t, ctypes.c_size_t,    # n_num, n_den
            _ezbi, _ezbi,                        # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_has
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_zeilberger.restype = ctypes.c_int

    # rc91: srmech_elliptic_wz_certificate — the ELLIPTIC Σ-row IDENTITY-PROOF op for the
    # Frenkel–Turaev ₈ω₇ SUMMATION. The C peer of
    # srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate. IDENTICAL wire shape to
    # srmech_elliptic_zeilberger (the full EllRatio + the nsym/ksym certificate index
    # symbols N = qⁿ, K = qᵏ); the proof reduces to the SAME connection-coefficient split
    # certificate decided via srmech_thetasum_is_zero, so the peer returns only *out_has
    # (1 iff recognized AND the certificate is exactly zero). The Python builds the
    # closed-form endpoints {aq,aq/bc,aq/bd,aq/cd}/{aq/b,aq/c,aq/d,aq/bcd} on its side (the
    # analogue of "the Python builds ρ"). NEW symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_elliptic_wz_certificate_ws_bound(n_syms, n_num, n_den, coeff_limbs)
    if hasattr(lib, "srmech_elliptic_wz_certificate_ws_bound"):
        lib.srmech_elliptic_wz_certificate_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_elliptic_wz_certificate_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_elliptic_wz_certificate"):
        _ewzbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_elliptic_wz_certificate.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, psym, qsym, ysym
            ctypes.c_int, ctypes.c_int,          # nsym, ksym (the cert's N = qⁿ, K = qᵏ)
            ctypes.c_size_t, ctypes.c_size_t,    # n_num, n_den
            _ewzbi, _ewzbi,                      # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_has
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_elliptic_wz_certificate.restype = ctypes.c_int

    # rc69: srmech_carrier_spectrum — the OPERAND-side dual of the_one (the C peer of
    # srmech.amsc.carrier_spectrum.carrier_spectrum). The carrier element rides as the
    # SAME full EllRatio wire form srmech_elliptic_recurrence_8w7 parses (n_syms + the
    # x/p/q/y interned indices + the num/den theta counts + the flat exact-Q coeff arrays
    # + the flat int32 exponent rows). The channel READ comes back as the distinct
    # x-exponents (out_cyclic[] + out_n_cyclic) + the per-theta q-stripped block-label
    # exponent rows (out_block_flat + out_n_thetas). The Python rebuilds + re-verifies
    # the spectrum byte-for-byte. NEW symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_carrier_spectrum_ws_bound(n_syms, n_num, n_den, coeff_cap)
    if hasattr(lib, "srmech_carrier_spectrum_ws_bound"):
        lib.srmech_carrier_spectrum_ws_bound.argtypes = [
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
        lib.srmech_carrier_spectrum_ws_bound.restype = ctypes.c_size_t
    if hasattr(lib, "srmech_carrier_spectrum"):
        _csbi = ctypes.POINTER(_SrmechBigint)
        lib.srmech_carrier_spectrum.argtypes = [
            ctypes.c_size_t,                     # n_syms
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # xsym, psym, qsym, ysym
            ctypes.c_size_t, ctypes.c_size_t,    # n_num, n_den
            _csbi, _csbi,                        # coeff_num, coeff_den (flat)
            ctypes.POINTER(ctypes.c_int32),      # exps_flat
            ctypes.c_uint32,                     # coeff_cap
            ctypes.POINTER(ctypes.c_int),        # out_has
            ctypes.POINTER(ctypes.c_int32),      # out_cyclic
            ctypes.c_size_t,                     # cyclic_cap
            ctypes.POINTER(ctypes.c_size_t),     # out_n_cyclic
            ctypes.POINTER(ctypes.c_int32),      # out_block_flat
            ctypes.c_size_t,                     # block_cap_rows
            ctypes.POINTER(ctypes.c_size_t),     # out_n_thetas
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_carrier_spectrum.restype = ctypes.c_int

    # rc42: srmech_zeilberger — Zeilberger's creative telescoping (the §76 telescope
    # Sigma-row's SECOND public op). The four BIVARIATE term ratios ride as flat
    # (num, den) coefficient arrays (k-then-n order) + a per-k length array + the
    # k-degree count; the recurrence coeffs + certificate come back the same way.
    #   size_t srmech_zeilberger_ws_bound(coeff_limbs, order, degree)
    #   size_t srmech_zeilberger_out_cap(coeff_limbs, order, degree)
    for _zsz in ("srmech_zeilberger_ws_bound", "srmech_zeilberger_out_cap"):
        if hasattr(lib, _zsz):
            getattr(lib, _zsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t,
                                           ctypes.c_size_t]
            getattr(lib, _zsz).restype = ctypes.c_size_t
    if hasattr(lib, "srmech_zeilberger"):
        _bi = ctypes.POINTER(_SrmechBigint)
        _szp = ctypes.POINTER(ctypes.c_size_t)
        lib.srmech_zeilberger.argtypes = [
            _bi, _bi, _szp, ctypes.c_size_t,     # rn_num n/d, klen, kdeg
            _bi, _bi, _szp, ctypes.c_size_t,     # rn_den
            _bi, _bi, _szp, ctypes.c_size_t,     # rk_num
            _bi, _bi, _szp, ctypes.c_size_t,     # rk_den
            ctypes.c_size_t, ctypes.c_size_t,    # max_order, n_stride
            ctypes.POINTER(ctypes.c_int), _szp,  # out_has, out_order
            _bi, _bi, _szp,                      # coeff n/d, coeff_nlen
            _bi, _bi, _szp,                      # cert n/d, cert_klen
            _szp,                                # out_cert_kdeg
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_zeilberger.restype = ctypes.c_int

    # rc53: srmech_apagodu_zeilberger — the Apagodu-Zeilberger multivariate "sums of
    # sums" creative telescoping (CLOSES the multivariate F929 row). The three
    # TRIVARIATE term ratios ride as flat (num, den) coefficient arrays (j-major then
    # k-then-n order) + a per-(j,k)-cell n-run length array + the (jdeg, kdeg) shape;
    # the recurrence coeffs + the two certificates come back the same way.
    #   size_t srmech_apagodu_zeilberger_ws_bound(coeff_limbs, order, degree)
    #   size_t srmech_apagodu_zeilberger_out_cap(coeff_limbs, order, degree)
    for _azsz in ("srmech_apagodu_zeilberger_ws_bound",
                  "srmech_apagodu_zeilberger_out_cap"):
        if hasattr(lib, _azsz):
            getattr(lib, _azsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t,
                                            ctypes.c_size_t]
            getattr(lib, _azsz).restype = ctypes.c_size_t
    if hasattr(lib, "srmech_apagodu_zeilberger"):
        _bi = ctypes.POINTER(_SrmechBigint)
        _szp = ctypes.POINTER(ctypes.c_size_t)
        lib.srmech_apagodu_zeilberger.argtypes = [
            _bi, _bi, _szp, ctypes.c_size_t, ctypes.c_size_t,  # rn_num n/d, nlen, jdeg, kdeg
            _bi, _bi, _szp, ctypes.c_size_t, ctypes.c_size_t,  # rn_den
            _bi, _bi, _szp, ctypes.c_size_t, ctypes.c_size_t,  # rj_num
            _bi, _bi, _szp, ctypes.c_size_t, ctypes.c_size_t,  # rj_den
            _bi, _bi, _szp, ctypes.c_size_t, ctypes.c_size_t,  # rk_num
            _bi, _bi, _szp, ctypes.c_size_t, ctypes.c_size_t,  # rk_den
            ctypes.c_size_t, ctypes.c_size_t,                  # max_order, degree_hint
            ctypes.POINTER(ctypes.c_int), _szp,                # out_has, out_order
            _bi, _bi, _szp,                                    # coeff n/d, coeff_nlen
            _bi, _bi, _szp, _szp, _szp,                        # cert_j n/d, nlen, jdeg, kdeg
            _bi, _bi, _szp, _szp, _szp,                        # cert_k n/d, nlen, jdeg, kdeg
            ctypes.c_void_p, ctypes.c_size_t,                  # ws, ws_len
        ]
        lib.srmech_apagodu_zeilberger.restype = ctypes.c_int

    # rc56: srmech_q_zeilberger — the q-analog of Zeilberger's creative telescoping
    # (the SECOND public op of the q-hypergeometric F929 row). The four QBiPoly term
    # ratios ride as flat (num, den) q-runs (Y-major then X-major) + per-(Y,X)-cell
    # qlen[] + per-Y-cell x_low[]/x_cells[] + Y-cell count; the recurrence coeffs +
    # certificate come back the same way. The native peer completes the canonical
    # k-free q-geometric order-1 case + declines the rest (has=0 -> Python re-decides).
    #   size_t srmech_q_zeilberger_ws_bound(coeff_limbs, order, qdeg)
    #   size_t srmech_q_zeilberger_out_cap(coeff_limbs, order, qdeg)
    for _qzsz in ("srmech_q_zeilberger_ws_bound", "srmech_q_zeilberger_out_cap"):
        if hasattr(lib, _qzsz):
            getattr(lib, _qzsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t,
                                            ctypes.c_size_t]
            getattr(lib, _qzsz).restype = ctypes.c_size_t
    if hasattr(lib, "srmech_q_zeilberger"):
        _qbi = ctypes.POINTER(_SrmechBigint)
        _qszp = ctypes.POINTER(ctypes.c_size_t)
        _qi64p = ctypes.POINTER(ctypes.c_int64)
        # one QBiPoly input slot = (n, d, qlen, xlow, xcells, ycells).
        _qbipoly_in = [_qbi, _qbi, _qszp, _qi64p, _qszp, ctypes.c_size_t]
        lib.srmech_q_zeilberger.argtypes = (
            _qbipoly_in        # rn_num
            + _qbipoly_in      # rn_den
            + _qbipoly_in      # rk_num
            + _qbipoly_in      # rk_den
            + [ctypes.c_size_t,                                   # max_order
               ctypes.POINTER(ctypes.c_int), _qszp,              # out_has, out_order
               _qbi, _qbi, _qszp, _qi64p, _qszp, _qszp,          # coeff n/d, qlen, xlow, xcells, count
               _qbi, _qbi, _qszp, _qi64p, _qszp, _qszp,          # cert n/d, qlen, xlow, xcells, ycells
               ctypes.c_void_p, ctypes.c_size_t]                 # ws, ws_len
        )
        lib.srmech_q_zeilberger.restype = ctypes.c_int

    # rc43: srmech_wz_verify — the Wilf-Zeilberger VERIFY primitive (the §76 telescope
    # Sigma-row's THIRD/FINAL public op). The COMPLETE C mirror of the verify half of
    # srmech.amsc.wz_certificate: an EXACT bivariate-Q rational-function identity check
    # (bounded only by input DEGREE, not by any order — unlike the rc42 order-<=1 peer).
    # The six bivariate inputs (r_n num/den, r_k num/den, cert num/den) ride as flat
    # (num, den) coefficient arrays + per-k length arrays + the k-degree count, the same
    # _SrmechBigint bridge as zeilberger. NEW symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_wz_verify_ws_bound(coeff_limbs, degree)
    #   size_t srmech_wz_verify_out_cap(coeff_limbs, degree)
    for _wsz in ("srmech_wz_verify_ws_bound", "srmech_wz_verify_out_cap"):
        if hasattr(lib, _wsz):
            getattr(lib, _wsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t]
            getattr(lib, _wsz).restype = ctypes.c_size_t
    if hasattr(lib, "srmech_wz_verify"):
        _wbi = ctypes.POINTER(_SrmechBigint)
        _wszp = ctypes.POINTER(ctypes.c_size_t)
        lib.srmech_wz_verify.argtypes = [
            _wbi, _wbi, _wszp, ctypes.c_size_t,  # rn_num n/d, klen, kdeg
            _wbi, _wbi, _wszp, ctypes.c_size_t,  # rn_den
            _wbi, _wbi, _wszp, ctypes.c_size_t,  # rk_num
            _wbi, _wbi, _wszp, ctypes.c_size_t,  # rk_den
            _wbi, _wbi, _wszp, ctypes.c_size_t,  # cert_num
            _wbi, _wbi, _wszp, ctypes.c_size_t,  # cert_den
            ctypes.POINTER(ctypes.c_int),        # out_equal
            ctypes.c_void_p, ctypes.c_size_t,    # ws, ws_len
        ]
        lib.srmech_wz_verify.restype = ctypes.c_int

    # rc57: srmech_q_wz_verify — the q-analog of the Wilf-Zeilberger VERIFY primitive
    # (the THIRD/FINAL public op of the q-hypergeometric F929 row, the q-row CLOSER).
    # The COMPLETE C mirror of the verify half of srmech.amsc.q_wz_certificate: an EXACT
    # bivariate-Q[q] rational-function identity check (bounded only by input DEGREE, not
    # by any order — unlike the rc56 q_zeilberger order-<=1 peer). The six bivariate-q
    # inputs (r_n num/den, r_k num/den, cert num/den) ride the SAME QBiPoly bridge as
    # srmech_q_zeilberger (n/d flat q-runs + per-(Y,X) qlen[] + per-Y xlow[]/xcells[] +
    # ycells). NEW symbols -> hasattr-guarded; ABI stays 3.
    #   size_t srmech_q_wz_verify_ws_bound(coeff_limbs, degree)
    #   size_t srmech_q_wz_verify_out_cap(coeff_limbs, degree)
    for _qwsz in ("srmech_q_wz_verify_ws_bound", "srmech_q_wz_verify_out_cap"):
        if hasattr(lib, _qwsz):
            getattr(lib, _qwsz).argtypes = [ctypes.c_size_t, ctypes.c_size_t]
            getattr(lib, _qwsz).restype = ctypes.c_size_t
    if hasattr(lib, "srmech_q_wz_verify"):
        _qwbi = ctypes.POINTER(_SrmechBigint)
        _qwszp = ctypes.POINTER(ctypes.c_size_t)
        _qwi64p = ctypes.POINTER(ctypes.c_int64)
        # one QBiPoly input slot = (n, d, qlen, xlow, xcells, ycells).
        _qwbipoly_in = [_qwbi, _qwbi, _qwszp, _qwi64p, _qwszp, ctypes.c_size_t]
        lib.srmech_q_wz_verify.argtypes = (
            _qwbipoly_in       # rn_num
            + _qwbipoly_in     # rn_den
            + _qwbipoly_in     # rk_num
            + _qwbipoly_in     # rk_den
            + _qwbipoly_in     # cert_num
            + _qwbipoly_in     # cert_den
            + [ctypes.POINTER(ctypes.c_int),        # out_equal
               ctypes.c_void_p, ctypes.c_size_t]    # ws, ws_len
        )
        lib.srmech_q_wz_verify.restype = ctypes.c_int


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


# ----------------------------------------------------------------------
# v0.7.5rc2: scalar transcendental cascade wrappers — the Python-callable
# face of the rc43-46 C cascade. The float-projection ops in
# ``srmech.amsc.rational`` dispatch through these when ``has_native_trig()``.
# ----------------------------------------------------------------------

def has_native_trig() -> bool:
    """True iff the C transcendental cascade is loaded + bound (rc43+ lib)."""
    return bool(HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_sin"))


def has_native_explog() -> bool:
    """True iff the C exp/log cascade is loaded + bound (rc46+ lib)."""
    return bool(HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_exp"))


def has_native_sqrt() -> bool:
    """True iff the C integer-isqrt sqrt cascade is loaded + bound (rc45+ lib)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_rational_sqrt"))


def has_native_pi_chudnovsky() -> bool:
    """True iff the rotation-last Chudnovsky π C symbols are loaded + bound
    (0.9.0rc19+ lib): :func:`srmech.amsc.rational.pi_chudnovsky_digits`
    dispatches to the exact-bigint native path. False on a no-C or pre-rc19
    lib — the pure-Python int-bignum body is the complete alternative (and the
    parity oracle); the two paths emit byte-identical ``"3.<digits>"``."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_pi_chudnovsky")
                and hasattr(LIB, "srmech_pi_chudnovsky_ws_bound"))


def pi_chudnovsky_c(num_digits: int) -> "str | None":
    """Native rotation-last Chudnovsky π → ``"3.<num_digits digits>"`` or None.

    Returns ``None`` when the native symbols are absent (no-C / pre-rc19 lib)
    so the caller falls through to the pure-Python bignum body. Sizes the
    caller arena via ``srmech_pi_chudnovsky_ws_bound``, then calls the exact
    C path; a non-OK status raises :class:`RuntimeError`. Byte-identical to the
    pure-Python oracle (proven C==Python==Archimedes at 1000 + 10000 digits)."""
    if not has_native_pi_chudnovsky():
        return None
    ws_len = int(LIB.srmech_pi_chudnovsky_ws_bound(ctypes.c_uint32(num_digits)))
    ws = (ctypes.c_uint8 * max(ws_len, 1))()
    out_cap = num_digits + 8                      # "3." + digits + NUL + slack
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_pi_chudnovsky(
        ctypes.c_uint32(num_digits),
        out,
        ctypes.c_size_t(out_cap),
        ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p),
        ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_pi_chudnovsky returned non-OK status {rc}"
        )
    return bytes(out)[:out_len.value].decode("ascii")


# ----------------------------------------------------------------------
# rc35: bignum-exact Class-N transcendental series (exact-rational-in →
# exact-rational-out over the caller-arena srmech_bigint). These remove the
# int64/Q61 magnitude ceiling the C peers had vs. the Python bignum path, so
# a C-only host gets Python's unbounded exact (num, den). The Python wrappers
# below marshal Python ints ⇄ srmech_bigint (via the decimal bridge) and size
# the caller arena via srmech_bigexp_ws_bound — the same bigint-ws pattern as
# pi_chudnovsky_c.
# ----------------------------------------------------------------------

_BIGEXP_SYMS = (
    "srmech_bigexp_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_bigexp() -> bool:
    """True iff the rc35 bignum-exact transcendental series + the srmech_bigint
    decimal-marshal helpers are loaded + bound. False on a no-C or pre-rc35 lib
    — the pure-Python bignum body in ``srmech.amsc.rational`` is the complete
    alternative (and the parity oracle); both emit byte-identical ``(num,
    den)``."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _BIGEXP_SYMS) and hasattr(
        LIB, "srmech_exp_series_truncate_big"
    )


def _bigint_from_int(value: int, cap_limbs: int):
    """Build a ``_SrmechBigint`` carrying ``value`` over a fresh ``cap_limbs``
    limb buffer. Returns ``(bigint, limbs_buf)`` — the caller MUST keep
    ``limbs_buf`` alive for the bigint's lifetime (ctypes won't)."""
    bi = _SrmechBigint()
    limbs = (ctypes.c_uint32 * cap_limbs)()
    bi.limbs = ctypes.cast(limbs, ctypes.POINTER(ctypes.c_uint32))
    bi.cap = cap_limbs
    bi.n = 0
    bi.sign = 0
    s = str(value).encode("ascii")
    rc = LIB.srmech_bigint_from_dec(ctypes.byref(bi), s, len(s))
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_bigint_from_dec returned non-OK status {rc}")
    return bi, limbs


def _bigint_to_int(bi) -> int:
    """Read a ``_SrmechBigint`` back to a Python ``int`` via the decimal bridge."""
    a_n = bi.n if bi.n else 1
    cap = int(LIB.srmech_bigint_to_dec_bound(ctypes.c_size_t(a_n))) + 8
    buf = ctypes.create_string_buffer(cap)
    out_len = ctypes.c_size_t(0)
    scratch_words = a_n * 12 + 64
    scratch = (ctypes.c_uint8 * (scratch_words * 4))()
    rc = LIB.srmech_bigint_to_dec(
        ctypes.byref(bi), buf, ctypes.c_size_t(cap), ctypes.byref(out_len),
        ctypes.cast(scratch, ctypes.c_void_p),
        ctypes.c_size_t(scratch_words * 4),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_bigint_to_dec returned non-OK status {rc}")
    return int(bytes(buf)[:out_len.value].decode("ascii"))


def _bigexp_call(symbol: str, numerator: int, denominator: int,
                 num_terms: int) -> "tuple[int, int] | None":
    """Invoke one ``*_big`` op and return its reduced ``(num, den)`` or ``None``.

    Returns ``None`` when the native symbols are absent (caller falls through to
    the pure-Python bignum oracle). A non-OK C status (other than absence)
    raises :class:`RuntimeError`. The operand/result rationals + the caller
    arena are all sized from the input magnitudes + ``num_terms`` so the bignum
    path has NO ceiling (byte-identical to ``srmech.amsc.rational`` at any
    magnitude)."""
    if not has_native_bigexp() or not hasattr(LIB, symbol):
        return None
    # Limb sizing: 9 decimal digits ≈ 1 limb; pad generously. The output /
    # working carriers are sized to hold the reduced result, which for these
    # series is bounded by q^E·E! (E ~ 2N+1); 32·(N+digits)+64 limbs is a safe
    # envelope across the per-op term caps (exp N≤512, trig N≤50, log/atan N≤64,
    # pow exp≤65535 — but exp_val that large is the caller's arena to size).
    num_digits = len(str(numerator).lstrip("-")) + len(str(denominator))
    out_cap = 32 * (num_terms + num_digits) + 64
    num_limbs = max(len(str(numerator).lstrip("-")) // 9 + 2, 2)
    den_limbs = max(len(str(denominator)) // 9 + 2, 2)
    ws_len = int(LIB.srmech_bigexp_ws_bound(
        ctypes.c_size_t(num_limbs), ctypes.c_size_t(den_limbs),
        ctypes.c_uint32(num_terms),
    ))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    x_num, _xnl = _bigint_from_int(numerator, out_cap)
    x_den, _xdl = _bigint_from_int(denominator, out_cap)
    out_num, _onl = _bigint_from_int(0, out_cap)
    out_den, _odl = _bigint_from_int(0, out_cap)
    rc = getattr(LIB, symbol)(
        ctypes.byref(x_num), ctypes.byref(x_den), ctypes.c_uint32(num_terms),
        ctypes.byref(out_num), ctypes.byref(out_den),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"{symbol} returned non-OK status {rc}")
    return _bigint_to_int(out_num), _bigint_to_int(out_den)


def has_native_jacobi_sncndn() -> bool:
    """True iff the Jacobi elliptic sn/cn/dn C peer + the srmech_bigint decimal
    marshal helpers are loaded + bound. False on a no-C or pre-jacobi lib — the
    pure-Python bignum body in ``srmech.amsc.rational`` is the complete
    alternative (and the parity oracle); both emit byte-identical (sn, cn,
    dn)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _BIGEXP_SYMS)
            and hasattr(LIB, "srmech_jacobi_sncndn")
            and hasattr(LIB, "srmech_jacobi_sncndn_ws_bound"))


def jacobi_sncndn_c(numerator: int, denominator: int,
                    m_numerator: int, m_denominator: int,
                    num_terms: int) -> "tuple | None":
    """Invoke ``srmech_jacobi_sncndn`` and return the reduced
    ``((sn_num, sn_den), (cn_num, cn_den), (dn_num, dn_den))`` triple, or
    ``None`` when the native symbols are absent (caller falls through to the
    pure-Python bignum oracle). The operand/result rationals + the caller arena
    are all sized from the input magnitudes + ``num_terms`` so the bignum path
    has NO ceiling (byte-identical to ``srmech.amsc.rational`` at any
    magnitude)."""
    if not has_native_jacobi_sncndn():
        return None
    # Limb sizing — see _bigexp_call; the coefficient denominators grow like
    # (k+1)!·m_den^k, so size the output / working carriers generously off N and
    # the input digit lengths (over-sizing is free; under-sizing → OVERFLOW).
    u_digits = len(str(numerator).lstrip("-")) + len(str(denominator))
    m_digits = len(str(m_numerator).lstrip("-")) + len(str(m_denominator))
    out_cap = 48 * (num_terms + u_digits + m_digits) + 128
    num_limbs = max(len(str(numerator).lstrip("-")) // 9 + 2, 2)
    den_limbs = max(len(str(denominator)) // 9 + 2, 2)
    mn_limbs = max(len(str(m_numerator).lstrip("-")) // 9 + 2, 2)
    md_limbs = max(len(str(m_denominator)) // 9 + 2, 2)
    ws_len = int(LIB.srmech_jacobi_sncndn_ws_bound(
        ctypes.c_size_t(num_limbs), ctypes.c_size_t(den_limbs),
        ctypes.c_size_t(mn_limbs), ctypes.c_size_t(md_limbs),
        ctypes.c_uint32(num_terms),
    ))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    u_num, _u0 = _bigint_from_int(numerator, out_cap)
    u_den, _u1 = _bigint_from_int(denominator, out_cap)
    m_num, _m0 = _bigint_from_int(m_numerator, out_cap)
    m_den, _m1 = _bigint_from_int(m_denominator, out_cap)
    sn_n, _s0 = _bigint_from_int(0, out_cap)
    sn_d, _s1 = _bigint_from_int(0, out_cap)
    cn_n, _c0 = _bigint_from_int(0, out_cap)
    cn_d, _c1 = _bigint_from_int(0, out_cap)
    dn_n, _d0 = _bigint_from_int(0, out_cap)
    dn_d, _d1 = _bigint_from_int(0, out_cap)
    rc = LIB.srmech_jacobi_sncndn(
        ctypes.byref(u_num), ctypes.byref(u_den),
        ctypes.byref(m_num), ctypes.byref(m_den),
        ctypes.c_uint32(num_terms),
        ctypes.byref(sn_n), ctypes.byref(sn_d),
        ctypes.byref(cn_n), ctypes.byref(cn_d),
        ctypes.byref(dn_n), ctypes.byref(dn_d),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_jacobi_sncndn returned non-OK status {rc}")
    return (
        (_bigint_to_int(sn_n), _bigint_to_int(sn_d)),
        (_bigint_to_int(cn_n), _bigint_to_int(cn_d)),
        (_bigint_to_int(dn_n), _bigint_to_int(dn_d)),
    )


# ----------------------------------------------------------------------
# rc38: the EXACT-RATIONAL polynomial carrier C peer (srmech_poly_*). The
# Python srmech.amsc.poly.Poly routes its add/sub/mul/divmod/gcd/eval/shift
# through these when has_native_poly(); the pure-Python body is the COMPLETE
# alternative (and the parity oracle) — both emit byte-identical exact (num,
# den) coefficients at any magnitude. The marshalling builds parallel
# _SrmechBigint coefficient arrays over the decimal bridge (same pattern as
# _bigexp_call), keeping the backing limb buffers alive for the call.
# ----------------------------------------------------------------------

_POLY_SYMS = (
    "srmech_poly_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_poly() -> bool:
    """True iff the rc38 srmech_poly_* ops + the srmech_bigint decimal-marshal
    helpers are loaded + bound. False on a no-C or pre-rc38 lib — the
    pure-Python ``srmech.amsc.poly.Poly`` body is the complete alternative (and
    the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _POLY_SYMS) and hasattr(
        LIB, "srmech_poly_add"
    )


def _poly_coeff_limbs(coeffs) -> int:
    """The largest significant-limb count across a coefficient ``(num, den)``
    sequence (9 decimal digits ≈ 1 limb; pad)."""
    cl = 1
    for num, den in coeffs:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    return cl


def _poly_make_array(coeffs, out_cap):
    """Build parallel ``_SrmechBigint`` arrays (nums, dens) over the decimal
    bridge from a ``(num, den)`` coefficient sequence, each carrier sized to
    ``out_cap`` limbs. Returns ``(num_arr, den_arr, keepalive)`` — the caller
    MUST keep ``keepalive`` (the limb buffers) alive for the call."""
    n = len(coeffs)
    num_arr = (_SrmechBigint * max(n, 1))()
    den_arr = (_SrmechBigint * max(n, 1))()
    keep = []
    for i, (num, den) in enumerate(coeffs):
        bn, kbn = _bigint_from_int(int(num), out_cap)
        bd, kbd = _bigint_from_int(int(den), out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
    return num_arr, den_arr, keep


def _poly_blank_array(n, out_cap):
    """Build parallel blank ``_SrmechBigint`` output arrays of ``n`` slots, each
    sized to ``out_cap`` limbs. Returns ``(num_arr, den_arr, keepalive)``."""
    num_arr = (_SrmechBigint * max(n, 1))()
    den_arr = (_SrmechBigint * max(n, 1))()
    keep = []
    for i in range(n):
        bn, kbn = _bigint_from_int(0, out_cap)
        bd, kbd = _bigint_from_int(1, out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
    return num_arr, den_arr, keep


def _poly_read_array(num_arr, den_arr, length):
    """Read the first ``length`` coefficients of a result ``_SrmechBigint`` array
    pair back to a list of ``(num, den)`` Python-int tuples."""
    out = []
    for i in range(length):
        out.append((_bigint_to_int(num_arr[i]), _bigint_to_int(den_arr[i])))
    return out


def _poly_setup(*coeff_seqs, extra_terms=0):
    """Common sizing: the per-coefficient limb cap (``out_cap``) and the caller
    arena (``ws``, ``ws_len``) for a set of input coefficient sequences. The
    ``out_cap`` over-sizes to the product-of-magnitudes envelope (mirrors the C
    poly_cap_for); the arena is sized from srmech_poly_ws_bound."""
    n_terms = max((len(s) for s in coeff_seqs), default=1) + extra_terms + 1
    cl = 1
    for s in coeff_seqs:
        cl = max(cl, _poly_coeff_limbs(s))
    # Match the C poly_cap_for product-of-magnitudes envelope (generous).
    out_cap = (cl * n_terms + 2) * 2 + cl * 2 + 64
    ws_len = int(LIB.srmech_poly_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    return out_cap, ws, ws_len


def poly_add_c(a_coeffs, b_coeffs):
    """Native exact-Q polynomial add → list of reduced ``(num, den)`` tuples, or
    ``None`` if the native symbols are absent. ``a_coeffs`` / ``b_coeffs`` are
    ``(num, den)`` sequences in ascending degree."""
    return _poly_addsub_c("srmech_poly_add", a_coeffs, b_coeffs)


def poly_sub_c(a_coeffs, b_coeffs):
    """Native exact-Q polynomial subtract (see :func:`poly_add_c`)."""
    return _poly_addsub_c("srmech_poly_sub", a_coeffs, b_coeffs)


def _poly_addsub_c(symbol, a_coeffs, b_coeffs):
    if not has_native_poly() or not hasattr(LIB, symbol):
        return None
    na, nb = len(a_coeffs), len(b_coeffs)
    m = max(na, nb)
    out_cap, ws, ws_len = _poly_setup(a_coeffs, b_coeffs)
    a_n, a_d, ka = _poly_make_array(a_coeffs, out_cap)
    b_n, b_d, kb = _poly_make_array(b_coeffs, out_cap)
    o_n, o_d, ko = _poly_blank_array(max(m, 1), out_cap)
    out_len = ctypes.c_size_t(0)
    rc = getattr(LIB, symbol)(
        a_n, a_d, ctypes.c_size_t(na), b_n, b_d, ctypes.c_size_t(nb),
        o_n, o_d, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"{symbol} returned non-OK status {rc}")
    return _poly_read_array(o_n, o_d, out_len.value)


def poly_mul_c(a_coeffs, b_coeffs):
    """Native exact-Q polynomial product (convolution) → reduced ``(num, den)``
    list, or ``None`` if absent."""
    if not has_native_poly() or not hasattr(LIB, "srmech_poly_mul"):
        return None
    na, nb = len(a_coeffs), len(b_coeffs)
    if na == 0 or nb == 0:
        return []
    m = na + nb - 1
    out_cap, ws, ws_len = _poly_setup(a_coeffs, b_coeffs, extra_terms=m)
    a_n, a_d, ka = _poly_make_array(a_coeffs, out_cap)
    b_n, b_d, kb = _poly_make_array(b_coeffs, out_cap)
    o_n, o_d, ko = _poly_blank_array(m, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_poly_mul(
        a_n, a_d, ctypes.c_size_t(na), b_n, b_d, ctypes.c_size_t(nb),
        o_n, o_d, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_poly_mul returned non-OK status {rc}")
    return _poly_read_array(o_n, o_d, out_len.value)


def poly_divmod_c(a_coeffs, b_coeffs):
    """Native exact-Q polynomial long division → ``(quotient_list,
    remainder_list)`` of reduced ``(num, den)`` tuples, or ``None`` if absent.
    Raises ``ZeroDivisionError`` when ``b_coeffs`` is the zero polynomial."""
    if not has_native_poly() or not hasattr(LIB, "srmech_poly_divmod"):
        return None
    na, nb = len(a_coeffs), len(b_coeffs)
    if nb == 0:
        raise ZeroDivisionError("poly_divmod_c by the zero polynomial")
    qcap = (na - nb + 1) if na >= nb else 0
    out_cap, ws, ws_len = _poly_setup(a_coeffs, b_coeffs, extra_terms=na)
    a_n, a_d, ka = _poly_make_array(a_coeffs, out_cap)
    b_n, b_d, kb = _poly_make_array(b_coeffs, out_cap)
    q_n, q_d, kq = _poly_blank_array(max(qcap, 1), out_cap)
    r_n, r_d, kr = _poly_blank_array(max(na, 1), out_cap)
    qn = ctypes.c_size_t(0)
    rn = ctypes.c_size_t(0)
    rc = LIB.srmech_poly_divmod(
        a_n, a_d, ctypes.c_size_t(na), b_n, b_d, ctypes.c_size_t(nb),
        q_n, q_d, ctypes.byref(qn), r_n, r_d, ctypes.byref(rn),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, kq, kr)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_poly_divmod returned non-OK status {rc}")
    return (_poly_read_array(q_n, q_d, qn.value),
            _poly_read_array(r_n, r_d, rn.value))


def poly_eval_c(p_coeffs, x):
    """Native exact Horner evaluation → one reduced ``(num, den)`` tuple, or
    ``None`` if absent. ``x`` is a ``(num, den)`` tuple."""
    if not has_native_poly() or not hasattr(LIB, "srmech_poly_eval"):
        return None
    n = len(p_coeffs)
    out_cap, ws, ws_len = _poly_setup(p_coeffs, [x], extra_terms=n)
    p_n, p_d, kp = _poly_make_array(p_coeffs, out_cap)
    x_n, kxn = _bigint_from_int(int(x[0]), out_cap)
    x_d, kxd = _bigint_from_int(int(x[1]), out_cap)
    o_n, kon = _bigint_from_int(0, out_cap)
    o_d, kod = _bigint_from_int(1, out_cap)
    rc = LIB.srmech_poly_eval(
        p_n, p_d, ctypes.c_size_t(n), ctypes.byref(x_n), ctypes.byref(x_d),
        ctypes.byref(o_n), ctypes.byref(o_d),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (kp, kxn, kxd, kon, kod)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_poly_eval returned non-OK status {rc}")
    return (_bigint_to_int(o_n), _bigint_to_int(o_d))


def poly_shift_c(p_coeffs, h):
    """Native exact dispersion ``p(x + h)`` → reduced ``(num, den)`` coefficient
    list, or ``None`` if absent. ``h`` is a ``(num, den)`` tuple."""
    if not has_native_poly() or not hasattr(LIB, "srmech_poly_shift"):
        return None
    n = len(p_coeffs)
    if n == 0:
        return []
    out_cap, ws, ws_len = _poly_setup(p_coeffs, [h], extra_terms=n)
    p_n, p_d, kp = _poly_make_array(p_coeffs, out_cap)
    h_n, khn = _bigint_from_int(int(h[0]), out_cap)
    h_d, khd = _bigint_from_int(int(h[1]), out_cap)
    o_n, o_d, ko = _poly_blank_array(n, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_poly_shift(
        p_n, p_d, ctypes.c_size_t(n), ctypes.byref(h_n), ctypes.byref(h_d),
        o_n, o_d, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (kp, khn, khd, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_poly_shift returned non-OK status {rc}")
    return _poly_read_array(o_n, o_d, out_len.value)


# ----------------------------------------------------------------------
# rc70: the EXACT-INTEGER UNARY THETA q-series C peer (srmech_unary_theta) — the
# first WEIGHT-GRADED carrier. The Python srmech.amsc.unary_theta.UnaryTheta
# routes its q_series through this when has_native_unary_theta(); the pure-Python
# body is the COMPLETE alternative (and the parity oracle) — both emit
# byte-identical exact integer coefficients at any magnitude (n^j is full bignum,
# no int64 ceiling).
# ----------------------------------------------------------------------

_SUPPORT_CODE = {"all": 0, "positive": 1, "nonneg": 2}


def _int_isqrt(x: int) -> int:
    """Integer floor-sqrt of a non-negative ``x`` (bisection, no float) — used
    ONLY to over-bound the per-coefficient limb cap for the unary-theta marshal
    (the marshalling layer stays float-free)."""
    if x < 2:
        return x if x >= 0 else 0
    lo, hi = 0, x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo


def has_native_unary_theta() -> bool:
    """True iff the rc70 ``srmech_unary_theta_q_series`` peer + the
    ``srmech_bigint`` decimal-marshal helpers are loaded + bound. False on a
    no-C / pre-rc70 lib — the pure-Python ``srmech.amsc.unary_theta.UnaryTheta``
    body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _POLY_SYMS)
            and hasattr(LIB, "srmech_unary_theta_q_series")
            and hasattr(LIB, "srmech_unary_theta_ws_bound"))


def unary_theta_q_series_c(modulus, chi_table, j, a, b, D, support, N):
    """Native exact-integer unary-theta q-series → a list of ``N + 1`` Python-int
    coefficients (the series after the leading-power factor-out), or ``None`` if
    the native symbols are absent. ``chi_table`` is a length-``modulus`` sequence
    of ``χ(r) ∈ {−1, 0, 1}``; ``support`` is ``'all'`` / ``'positive'`` /
    ``'nonneg'``."""
    if not has_native_unary_theta():
        return None
    sup = _SUPPORT_CODE.get(support)
    if sup is None:
        raise ValueError(f"unary_theta_q_series_c: bad support {support!r}")
    # per-coefficient limb cap: the largest coefficient is bounded by
    # (#terms)·(nmax^j); size generously from N, j, a, D (9 dec digits ≈ 1 limb).
    # nmax ~ √((lead+N·D)/a); over-estimate it with an INTEGER floor-sqrt (no
    # float in the marshalling layer either). A coarse digit estimate is then
    # j·(digits of nmax) + digits of the term count — pad hard.
    bound = max(N, 1) * D + 4 * a
    nmax_est = _int_isqrt(bound) + 4                 # integer over-bound on |n|
    coeff_digits = j * (len(str(nmax_est)) + 1) + len(str(2 * nmax_est + 4)) + 4
    out_cap = coeff_digits // 9 + 8
    cl = out_cap
    ws_len = int(LIB.srmech_unary_theta_ws_bound(
        ctypes.c_uint32(int(j)), ctypes.c_size_t(cl)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # the χ table as an int32 C array
    tab = (ctypes.c_int32 * max(modulus, 1))()
    for i in range(modulus):
        tab[i] = int(chi_table[i])
    # the out[] array of N+1 blank bigints, each cap out_cap
    o_n, _o_d, ko = _poly_blank_array(N + 1, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_unary_theta_q_series(
        ctypes.c_uint32(int(modulus)), tab, ctypes.c_uint32(int(j)),
        ctypes.c_int64(int(a)), ctypes.c_int64(int(b)), ctypes.c_uint32(int(D)),
        ctypes.c_int(int(sup)), ctypes.c_size_t(int(N)),
        o_n, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ko, tab)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_unary_theta_q_series returned non-OK status {rc}")
    return [_bigint_to_int(o_n[i]) for i in range(out_len.value)]


# ----------------------------------------------------------------------
# rc82: the EXACT-INTEGER ETA-QUOTIENT q-series C peer (srmech_eta_quotient) — a
# WEIGHT-axis carrier. The Python srmech.amsc.eta_quotient.EtaQuotient routes its
# q_series through this when has_native_eta_quotient(); the pure-Python body is
# the COMPLETE alternative (and the parity oracle) — both emit byte-identical
# exact integer coefficients at any magnitude (the coefficients grow, e.g. the
# Ramanujan τ, with no int64 ceiling).
# ----------------------------------------------------------------------


def has_native_eta_quotient() -> bool:
    """True iff the rc82 ``srmech_eta_quotient_qseries`` peer + the
    ``srmech_bigint`` decimal-marshal helpers are loaded + bound. False on a
    no-C / pre-rc82 lib — the pure-Python ``srmech.amsc.eta_quotient.EtaQuotient``
    body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _POLY_SYMS)
            and hasattr(LIB, "srmech_eta_quotient_qseries")
            and hasattr(LIB, "srmech_eta_quotient_ws_bound"))


def eta_quotient_qseries_c(ds, rs, n_terms):
    """Native exact-integer eta-quotient q-series → a list of ``n_terms`` Python-int
    coefficients of ``∏_d ∏_{m≥1} (1 − q^{dm})^{r_d}`` (the series after the
    leading-power factor-out), or ``None`` if the native symbols are absent.
    ``ds`` (each ``≥ 1``) / ``rs`` (each ``≠ 0``) are the parallel exponent-vector
    factors ``{ds[i]: rs[i]}``."""
    if not has_native_eta_quotient():
        return None
    if not isinstance(n_terms, int) or n_terms < 1:
        raise ValueError(f"eta_quotient_qseries_c: bad n_terms {n_terms!r}")
    nf = len(ds)
    if nf < 1 or len(rs) != nf:
        raise ValueError("eta_quotient_qseries_c: ds/rs must be equal-length, ≥ 1")
    # per-coefficient limb cap: the coefficients can grow large (the q-series of a
    # high-power eta-quotient). Over-bound from the partial-product envelope: each
    # (1 ± q^e) multiply at worst doubles the magnitude of each coefficient, so the
    # total positive exponent count Σ|r_d|·(#m terms ≈ n_terms/d) bounds the bit
    # growth. Estimate generously in decimal digits → limbs (9 dec digits ≈ 1 limb).
    total_pow = 0
    for d, r in zip(ds, rs):
        rmag = r if r >= 0 else -r          # Class-K magnitude, no abs()
        m_terms = (n_terms - 1) // max(int(d), 1) + 1
        total_pow += rmag * m_terms
    # each factor can shift bits by ~log2(n_terms); pad hard (digits ≈ bits·0.302)
    bit_est = total_pow * (len(bin(max(n_terms, 2))) - 2) + 64
    coeff_digits = bit_est // 3 + 32         # bits → decimal digits (over-estimate)
    out_cap = coeff_digits // 9 + 8
    cl = out_cap
    ws_len = int(LIB.srmech_eta_quotient_ws_bound(ctypes.c_size_t(cl)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    d_arr = (ctypes.c_int64 * max(nf, 1))()
    r_arr = (ctypes.c_int64 * max(nf, 1))()
    for i in range(nf):
        d_arr[i] = int(ds[i])
        r_arr[i] = int(rs[i])
    o_n, _o_d, ko = _poly_blank_array(n_terms, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_eta_quotient_qseries(
        d_arr, r_arr, ctypes.c_size_t(nf), ctypes.c_size_t(int(n_terms)),
        o_n, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ko, d_arr, r_arr)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_eta_quotient_qseries returned non-OK status {rc}")
    return [_bigint_to_int(o_n[i]) for i in range(out_len.value)]


# ----------------------------------------------------------------------
# rc83: the EXACT-RATIONAL EISENSTEIN-SERIES q-series C peer (srmech_eisenstein) —
# the SECOND WEIGHT-axis carrier (after rc82 eta-quotient). The Python
# srmech.amsc.eisenstein.Eisenstein routes its q_series through this when
# has_native_eisenstein(); the pure-Python body is the COMPLETE alternative (and
# the parity oracle) — both emit byte-identical REDUCED (num, den) coefficients at
# any magnitude (the genuine rational case k=12 → 65520/691 is covered, NOT just
# integer-coeff k).
# ----------------------------------------------------------------------


def has_native_eisenstein() -> bool:
    """True iff the rc83 ``srmech_eisenstein_qseries`` peer + the ``srmech_bigint``
    decimal-marshal helpers are loaded + bound. False on a no-C / pre-rc83 lib —
    the pure-Python ``srmech.amsc.eisenstein.Eisenstein`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _POLY_SYMS)
            and hasattr(LIB, "srmech_eisenstein_qseries")
            and hasattr(LIB, "srmech_eisenstein_ws_bound"))


def eisenstein_qseries_c(k, n_terms):
    """Native exact-rational Eisenstein q-series → a list of ``n_terms`` reduced
    ``(num, den)`` Python-int coefficient pairs of
    ``E_k = 1 − (2k/B_k)·Σ σ_{k−1}(n) qⁿ`` (``(1, 1)`` is the constant term), or
    ``None`` if the native symbols are absent. ``k`` is an EVEN int ``≥ 4`` (the
    Python carrier gates k=2 / odd / k<4 before reaching here)."""
    if not has_native_eisenstein():
        return None
    if not isinstance(n_terms, int) or n_terms < 1:
        raise ValueError(f"eisenstein_qseries_c: bad n_terms {n_terms!r}")
    if not isinstance(k, int) or k < 4 or k % 2 != 0:
        raise ValueError(f"eisenstein_qseries_c: bad weight k {k!r}")
    # per-coefficient limb cap: the coefficient c_n = (−2k/B_k)·σ_{k−1}(n). The
    # Bernoulli denominator (von Staudt–Clausen) and σ_{k−1}(n) (up to ~n·n^{k−1})
    # set the magnitude; both grow with k and n. Over-bound from the bit envelope:
    # σ_{k−1}(n) ≲ n^k, and the Bernoulli numerator/denominator grow like k!. Size
    # from k·log2(k) + (k)·log2(n_terms) bits, padded hard. 9 dec digits ≈ 1 limb.
    kbits = k * (len(bin(max(k, 2))) - 2)              # ~ k·log2(k) (Bernoulli)
    nbits = k * (len(bin(max(n_terms, 2))) - 2)        # ~ k·log2(n)  (σ_{k-1})
    bit_est = kbits + nbits + 256
    coeff_digits = bit_est // 3 + 64                   # bits → decimal (over-est)
    out_cap = coeff_digits // 9 + 16
    cl = out_cap
    ws_len = int(LIB.srmech_eisenstein_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(int(k))))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    o_n, o_d, ko = _poly_blank_array(n_terms, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_eisenstein_qseries(
        ctypes.c_size_t(int(k)), ctypes.c_size_t(int(n_terms)),
        o_n, o_d, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = ko
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_eisenstein_qseries returned non-OK status {rc}")
    return _poly_read_array(o_n, o_d, out_len.value)


def eisenstein_e2_qseries_c(n_terms):
    """Native exact-rational WEIGHT-2 QUASIMODULAR Eisenstein q-series → a list of
    ``n_terms`` reduced ``(num, den)`` Python-int coefficient pairs of
    ``E₂ = 1 − 24·Σ σ₁(n) qⁿ`` (``(1, 1)`` is the constant term, ``(−24, 1)`` the
    q¹ coefficient), or ``None`` if the native symbols are absent. Routes through the
    rc83 ``srmech_eisenstein_qseries`` C peer at ``k = 2`` (its quasimodular
    branch); the rc89 ``srmech.amsc.quasimodular_forms_ring.eisenstein_e2`` carrier
    dispatches here. ``E₂`` is the QUASIMODULAR generator — the modular ``Eisenstein``
    carrier still rejects ``k = 2``; this is a separate object."""
    if not has_native_eisenstein():
        return None
    if not isinstance(n_terms, int) or n_terms < 1:
        raise ValueError(f"eisenstein_e2_qseries_c: bad n_terms {n_terms!r}")
    # per-coefficient limb cap: c_n = −24·σ₁(n) ≲ 24·n² grows mildly; over-bound from
    # the n-bit envelope (same shape as eisenstein_qseries_c at k=2).
    nbits = 2 * (len(bin(max(n_terms, 2))) - 2)        # ~ 2·log2(n) (σ₁)
    bit_est = nbits + 256
    coeff_digits = bit_est // 3 + 64
    out_cap = coeff_digits // 9 + 16
    cl = out_cap
    ws_len = int(LIB.srmech_eisenstein_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(2)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    o_n, o_d, ko = _poly_blank_array(n_terms, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_eisenstein_qseries(
        ctypes.c_size_t(2), ctypes.c_size_t(int(n_terms)),
        o_n, o_d, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = ko
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_eisenstein_qseries (E₂, k=2) returned non-OK status {rc}")
    return _poly_read_array(o_n, o_d, out_len.value)


# ----------------------------------------------------------------------
# rc84: the level-1 ℂ[E₄,E₆] MODULAR-FORMS-RING membership-decision C peer
# (srmech_modular_forms_ring_represent) — the THIRD WEIGHT-axis rung. The Python
# srmech.amsc.modular_forms_ring.ModularFormsRing.represent routes its membership
# solve through this when has_native_modular_forms_ring(); the pure-Python body is
# the COMPLETE alternative (and the parity oracle) — both emit the byte-identical
# reduced rep {(a,b): (num, den)} / None. Unlike the carrier q-series peers
# (eisenstein / eta_quotient) this is a genuine REDUCER (a Rosetta ledger op,
# c_dispatched). Additive symbol → EXPECTED_ABI_VERSION stays 3.
# ----------------------------------------------------------------------

_MFR_SYMS = (
    "srmech_modular_forms_ring_represent_ws_bound",
    "srmech_modular_forms_ring_entry_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_modular_forms_ring() -> bool:
    """True iff the rc84 ``srmech_modular_forms_ring_represent`` peer + its
    ws/entry-cap sizers + the ``srmech_bigint`` decimal-marshal helpers are loaded
    + bound (it composes the rc83 ``srmech_eisenstein`` + the rc40 ``srmech_qmat``
    peers, both required). False on a no-C / pre-rc84 lib — the pure-Python
    ``srmech.amsc.modular_forms_ring.ModularFormsRing.represent`` body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _MFR_SYMS)
            and hasattr(LIB, "srmech_modular_forms_ring_represent")
            and has_native_eisenstein()
            and has_native_qmat())


def modular_forms_ring_represent_c(f_pairs, k):
    """Native level-1 ℂ[E₄,E₆] membership decision → ``(has_solution, rep_pairs)``
    where ``rep_pairs`` is the list of ``dim(k)`` reduced ``(num, den)`` rep
    coefficients (monomial order — ascending ``a`` in ``E₄^a E₆^b``), or ``None``
    if the native symbols are absent. ``f_pairs`` is the q-series as a list of
    reduced ``(num, den)`` int pairs; ``k`` the (even) claimed weight. ``has_
    solution`` False means the q-series is NOT a level-1 weight-``k`` modular form
    within this carrier (the caller returns ``None``)."""
    if not has_native_modular_forms_ring():
        return None
    if not isinstance(k, int) or k < 0:
        raise ValueError(f"modular_forms_ring_represent_c: bad weight k {k!r}")
    n_terms = len(f_pairs)
    # dim M_k for even k≥0; 0 for odd k
    d = 0 if (k % 2 != 0) else (k // 12 + (0 if k % 12 == 2 else 1))
    # the entry-coefficient magnitude: the E₄/E₆ q-series coefficients grow ~n^{k-1}
    # times a Bernoulli factor; the Cramer solve adds log-headroom. Over-bound from
    # the bit envelope + the input coefficients.
    cl = _qmat_coeff_limbs(f_pairs) if f_pairs else 1
    kbits = (k + 1) * (len(bin(max(n_terms, 2))) - 2)   # ~ k·log2(n) per E coeff
    cl = max(cl, kbits // 9 + 8)
    out_cap = int(LIB.srmech_modular_forms_ring_entry_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms), ctypes.c_size_t(int(k))))
    ws_len = int(LIB.srmech_modular_forms_ring_represent_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms), ctypes.c_size_t(int(k))))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    f_n, f_d, kf = _qmat_make_array(f_pairs, out_cap)
    o_n, o_d, ko = _qmat_blank_array(max(d, 1), out_cap)
    has = ctypes.c_size_t(0)
    rc = LIB.srmech_modular_forms_ring_represent(
        ctypes.c_size_t(int(k)), f_n, f_d, ctypes.c_size_t(n_terms),
        o_n, o_d, ctypes.byref(has),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (kf, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_modular_forms_ring_represent returned non-OK status {rc}")
    if not has.value:
        return False, []
    return True, _qmat_read_array(o_n, o_d, d)


# ----------------------------------------------------------------------
# rc89: the level-1 ℂ[E₂,E₄,E₆] QUASIMODULAR-FORMS-RING membership-decision C peer
# (srmech_quasimodular_forms_ring_represent) — the FOURTH WEIGHT-axis rung. The
# Python srmech.amsc.quasimodular_forms_ring.QuasiModularFormsRing.represent routes
# its membership solve through this when has_native_quasimodular_forms_ring(); the
# pure-Python body is the COMPLETE alternative (and the parity oracle) — both emit
# the byte-identical reduced rep {(a,b,c): (num, den)} / None. A genuine REDUCER (a
# Rosetta ledger op, c_dispatched). Additive symbol → EXPECTED_ABI_VERSION stays 3.
# ----------------------------------------------------------------------

_QMFR_SYMS = (
    "srmech_quasimodular_forms_ring_represent_ws_bound",
    "srmech_quasimodular_forms_ring_entry_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_quasimodular_forms_ring() -> bool:
    """True iff the rc89 ``srmech_quasimodular_forms_ring_represent`` peer + its
    ws/entry-cap sizers + the ``srmech_bigint`` decimal-marshal helpers are loaded
    + bound (it composes the rc83 ``srmech_eisenstein`` — k=2 quasimodular branch
    for E₂ — + the rc40 ``srmech_qmat`` peers, both required). False on a no-C /
    pre-rc89 lib — the pure-Python ``srmech.amsc.quasimodular_forms_ring.
    QuasiModularFormsRing.represent`` body is the complete alternative (and the
    parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _QMFR_SYMS)
            and hasattr(LIB, "srmech_quasimodular_forms_ring_represent")
            and has_native_eisenstein()
            and has_native_qmat())


def quasimodular_forms_ring_represent_c(f_pairs, k):
    """Native level-1 ℂ[E₂,E₄,E₆] membership decision → ``(has_solution, rep_pairs)``
    where ``rep_pairs`` is the list of ``dim(k)`` reduced ``(num, den)`` rep
    coefficients (monomial order — ascending ``a`` then ``b`` in ``E₂^a E₄^b E₆^c``),
    or ``None`` if the native symbols are absent. ``f_pairs`` is the q-series as a
    list of reduced ``(num, den)`` int pairs; ``k`` the (even) claimed weight.
    ``has_solution`` False means the q-series is NOT a level-1 weight-``k``
    quasimodular form within this carrier (the caller returns ``None``)."""
    if not has_native_quasimodular_forms_ring():
        return None
    if not isinstance(k, int) or k < 0:
        raise ValueError(f"quasimodular_forms_ring_represent_c: bad weight k {k!r}")
    n_terms = len(f_pairs)
    # dim M̃_k = #{(a,b,c): 2a+4b+6c=k} for even k≥0; 0 for odd k (enumerated).
    if k % 2 != 0 or k < 0:
        d = 0
    else:
        d = 0
        a = 0
        while 2 * a <= k:
            b = 0
            while 2 * a + 4 * b <= k:
                if (k - 2 * a - 4 * b) % 6 == 0:
                    d += 1
                b += 1
            a += 1
    # the entry-coefficient magnitude: the E₂/E₄/E₆ q-series coefficients grow ~n^{k-1}
    # times a Bernoulli factor; the Cramer solve adds log-headroom. Over-bound from
    # the bit envelope + the input coefficients.
    cl = _qmat_coeff_limbs(f_pairs) if f_pairs else 1
    kbits = (k + 1) * (len(bin(max(n_terms, 2))) - 2)   # ~ k·log2(n) per E coeff
    cl = max(cl, kbits // 9 + 8)
    out_cap = int(LIB.srmech_quasimodular_forms_ring_entry_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms), ctypes.c_size_t(int(k))))
    ws_len = int(LIB.srmech_quasimodular_forms_ring_represent_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms), ctypes.c_size_t(int(k))))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    f_n, f_d, kf = _qmat_make_array(f_pairs, out_cap)
    o_n, o_d, ko = _qmat_blank_array(max(d, 1), out_cap)
    has = ctypes.c_size_t(0)
    rc = LIB.srmech_quasimodular_forms_ring_represent(
        ctypes.c_size_t(int(k)), f_n, f_d, ctypes.c_size_t(n_terms),
        o_n, o_d, ctypes.byref(has),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (kf, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_quasimodular_forms_ring_represent returned non-OK status {rc}")
    if not has.value:
        return False, []
    return True, _qmat_read_array(o_n, o_d, d)


# ----------------------------------------------------------------------
# rc71: the EXACT-INTEGER HOLOMORPHIC mock-part q-series C peer
# (srmech_harmonic_maass) — the HarmonicMaass / MockQSeries PAIR carrier that
# makes research item #9 a finite exact object. The Python
# srmech.amsc.harmonic_maass.MockQSeries routes its Eulerian f(q) q_series through
# this when has_native_harmonic_maass(); the pure-Python body is the COMPLETE
# alternative (and the parity oracle) — both emit byte-identical exact integer
# coefficients at any magnitude.
# ----------------------------------------------------------------------


def has_native_harmonic_maass() -> bool:
    """True iff the rc71 ``srmech_harmonic_maass_hol_q_series`` peer + the
    ``srmech_bigint`` decimal-marshal helpers are loaded + bound. False on a
    no-C / pre-rc71 lib — the pure-Python ``srmech.amsc.harmonic_maass`` body is
    the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (all(hasattr(LIB, s) for s in _POLY_SYMS)
            and hasattr(LIB, "srmech_harmonic_maass_hol_q_series")
            and hasattr(LIB, "srmech_harmonic_maass_ws_bound"))


def harmonic_maass_eulerian_c(N):
    """Native exact-integer order-3 mock theta ``f(q) = Σ q^{n²}/∏(1+qʲ)²`` q-series
    → a list of ``N + 1`` Python-int coefficients (leading power 0), or ``None`` if
    the native symbols are absent."""
    if not has_native_harmonic_maass():
        return None
    if not isinstance(N, int) or N < 0:
        raise ValueError(f"harmonic_maass_eulerian_c: bad N {N!r}")
    # per-coefficient limb cap: the f(q) coefficients grow sub-exponentially
    # (partition-like); 9 dec digits ≈ 1 limb. Size generously from N.
    coeff_digits = N + 16
    out_cap = coeff_digits // 9 + 8
    ws_len = int(LIB.srmech_harmonic_maass_ws_bound(
        ctypes.c_size_t(int(N)), ctypes.c_size_t(out_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    o_n, _o_d, ko = _poly_blank_array(N + 1, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_harmonic_maass_hol_q_series(
        ctypes.c_size_t(int(N)), o_n, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = ko
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_harmonic_maass_hol_q_series returned non-OK status {rc}")
    return [_bigint_to_int(o_n[i]) for i in range(out_len.value)]


# ----------------------------------------------------------------------
# rc72: the EXACT-INTEGER (A,B,C) EXPONENT LATTICE of a GENUS-2 RIEMANN
# THETA-CONSTANT C peer (srmech_riemann_theta) — the FIRST RUNG of the GENUS axis.
# The Python srmech.amsc.riemann_theta.RiemannTheta routes its .lattice() through
# this when has_native_riemann_theta(); the pure-Python body is the COMPLETE
# alternative (and the parity oracle) — both accumulate the [A,B,C,sign] quadruples
# into the byte-identical canonical {(A,B,C): coeff} lattice.
# ----------------------------------------------------------------------


def has_native_riemann_theta() -> bool:
    """True iff the rc72 ``srmech_riemann_theta_lattice`` peer + its count helper
    are loaded + bound. False on a no-C / pre-rc72 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannTheta`` body is the complete alternative (and
    the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_lattice")
            and hasattr(LIB, "srmech_riemann_theta_count"))


def riemann_theta_lattice_c(ep1, ep2, e1, e2, box):
    """Native exact-integer genus-2 theta-constant exponent lattice → the canonical
    ``{(A, B, C): coeff}`` dict (the accumulated ``[A, B, C, sign]`` quadruples over
    the box ``|nᵢ| ≤ box``), or ``None`` if the native symbols are absent. The
    accumulation merges duplicate ``(A, B, C)`` keys by summing the ``±1`` signs —
    byte-identical to the pure-Python ``_lattice_py``. ``ep1, ep2, e1, e2`` are the
    characteristic bits (each in ``{0, 1}``)."""
    if not has_native_riemann_theta():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_lattice(
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]))
        lat[key] = lat.get(key, 0) + int(out[i + 3])
        i += 4
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc73: the SECOND GENUS RUNG — the Sp(4,Z) characteristic TRANSFORMATION + the
# EIGHTH-nome lattice (the addition gate). The Python
# srmech.amsc.riemann_theta.RiemannTheta routes .transform() / the addition gate
# through these when the symbols are loaded; the pure-Python bodies are the
# COMPLETE alternatives (and the parity oracles).
# ----------------------------------------------------------------------


def has_native_riemann_theta_sp4() -> bool:
    """True iff the rc73 ``srmech_riemann_theta_sp4_char`` peer (the EXACT integer
    Sp(4,Z) characteristic transformation + the κ 8th-root exponent) is loaded +
    bound. False on a no-C / pre-rc73 lib — the pure-Python
    ``RiemannTheta.transform`` body is the complete alternative (and the parity
    oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return hasattr(LIB, "srmech_riemann_theta_sp4_char")


def has_native_riemann_theta_eighth() -> bool:
    """True iff the rc73 ``srmech_riemann_theta_eighth_lattice`` peer (the COMMON
    eighth-nome lattice at Ω / 2Ω that the addition gate convolves) + its count
    helper are loaded + bound. False on a no-C / pre-rc73 lib — the pure-Python
    addition body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_eighth_lattice")
            and hasattr(LIB, "srmech_riemann_theta_eighth_count"))


def riemann_theta_sp4_char_c(gamma, ep1, ep2, e1, e2):
    """Native EXACT Sp(4,Z) characteristic transformation: returns
    ``((ep1', ep2', e1', e2'), kexp)`` — the four transformed characteristic bits
    and the 8th-root multiplier exponent ``kexp ∈ ℤ/8`` (the multiplier is
    ``ζ₈^kexp``) — or ``None`` if the native symbol is absent. ``gamma`` is the
    Sp(4,Z) element as four 2×2 integer blocks ``(A, B, C, D)``; the bridge flattens
    it to the 16 int entries (A,B,C,D row-major). Byte-identical to the pure-Python
    ``RiemannTheta._char_transform_int`` + ``_kappa_exp8``. Raises if gamma is not
    symplectic (the C peer returns SRMECH_ERR_BAD_INPUT)."""
    if not has_native_riemann_theta_sp4():
        return None
    a, b, c, d = gamma
    flat = (ctypes.c_int64 * 16)(
        a[0][0], a[0][1], a[1][0], a[1][1],
        b[0][0], b[0][1], b[1][0], b[1][1],
        c[0][0], c[0][1], c[1][0], c[1][1],
        d[0][0], d[0][1], d[1][0], d[1][1])
    out_char = (ctypes.c_int * 4)()
    kexp = ctypes.c_int(0)
    rc = LIB.srmech_riemann_theta_sp4_char(
        flat, ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        out_char, ctypes.byref(kexp))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_sp4_char returned non-OK status {rc}")
    return ((int(out_char[0]), int(out_char[1]),
             int(out_char[2]), int(out_char[3])), int(kexp.value) % 8)


def riemann_theta_eighth_lattice_c(s1, s2, e1, e2, at_two_omega, box):
    """Native eighth-nome genus-2 theta-constant lattice → the canonical
    ``{(A, B, C): coeff}`` dict, or ``None`` if the native symbols are absent.
    ``at_two_omega`` selects θ at Ω (0) or at 2Ω (1); ``s1, s2`` are the DOUBLED
    upper characteristic. Byte-identical to the pure-Python
    ``RiemannTheta._theta_omega_eighth`` / ``_theta_two_omega_eighth``."""
    if not has_native_riemann_theta_eighth():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_eighth_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_eighth_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_eighth_lattice(
        ctypes.c_int(int(s1)), ctypes.c_int(int(s2)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        ctypes.c_int(1 if at_two_omega else 0),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_eighth_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]))
        lat[key] = lat.get(key, 0) + int(out[i + 3])
        i += 4
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc74: the GENUS-AXIS CAPSTONE — the Eilers genus-2 ETA-MAP (branch-point index
# set → characteristic; arXiv:1707.08855, eq 4.4). The Python
# srmech.amsc.riemann_theta.RiemannTheta routes .branch_set_characteristic()
# through this when the symbol is loaded; the pure-Python body is the COMPLETE
# alternative (and the parity oracle). Pure GF(2) / mod-2 algebra — exact integer.
# ----------------------------------------------------------------------


def has_native_riemann_theta_eta() -> bool:
    """True iff the rc74 ``srmech_riemann_theta_eta_char`` peer (the EXACT GF(2)
    Eilers genus-2 η-map: branch-point index set → characteristic) is loaded +
    bound. False on a no-C / pre-rc74 lib — the pure-Python
    ``RiemannTheta.branch_set_characteristic`` body is the complete alternative
    (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return hasattr(LIB, "srmech_riemann_theta_eta_char")


def riemann_theta_eta_char_c(indices):
    """Native EXACT Eilers genus-2 η-map: a branch-point index tuple
    ``indices ⊆ {1,…,6}`` → the ``((ε'₁, ε'₂), (ε₁, ε₂))`` (mod-2) characteristic of
    ``[ε(I)] = Σ_{k∈I} [𝔄_k] − [K∞]`` (arXiv:1707.08855, eq 4.4), or ``None`` if the
    native symbol is absent. Byte-identical to the pure-Python
    ``RiemannTheta.branch_set_characteristic``. Raises if an index is out of
    ``{1,…,6}`` (the C peer returns SRMECH_ERR_BAD_INPUT)."""
    if not has_native_riemann_theta_eta():
        return None
    idx = tuple(int(i) for i in indices)
    n = len(idx)
    arr = (ctypes.c_int * max(n, 1))(*idx) if n else (ctypes.c_int * 1)()
    out_char = (ctypes.c_int * 4)()
    rc = LIB.srmech_riemann_theta_eta_char(
        arr, ctypes.c_size_t(n), out_char)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_eta_char returned non-OK status {rc}")
    return ((int(out_char[0]), int(out_char[1])),
            (int(out_char[2]), int(out_char[3])))


# ----------------------------------------------------------------------
# rc75: the NEXT GENUS RUNG — the GENUS-3 EXACT-INTEGER EXPONENT LATTICE C peer
# (srmech_riemann_theta_g3). The Python
# srmech.amsc.riemann_theta.RiemannThetaG3 routes its .lattice() through this when
# has_native_riemann_theta_g3(); the pure-Python body is the COMPLETE alternative
# (and the parity oracle) — both accumulate the [A1,A2,A3,C12,C13,C23,sign] septuples
# into the byte-identical canonical {(A1,A2,A3,C12,C13,C23): coeff} lattice.
# ----------------------------------------------------------------------


def has_native_riemann_theta_g3() -> bool:
    """True iff the rc75 ``srmech_riemann_theta_g3_lattice`` peer + its count helper
    are loaded + bound. False on a no-C / pre-rc75 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannThetaG3`` body is the complete alternative (and
    the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g3_lattice")
            and hasattr(LIB, "srmech_riemann_theta_g3_count"))


def riemann_theta_g3_lattice_c(ep1, ep2, ep3, e1, e2, e3, box):
    """Native exact-integer genus-3 theta-constant exponent lattice → the canonical
    ``{(A₁, A₂, A₃, C₁₂, C₁₃, C₂₃): coeff}`` dict (the accumulated
    ``[A1,A2,A3,C12,C13,C23,sign]`` septuples over the box ``|nᵢ| ≤ box``), or ``None``
    if the native symbols are absent. The accumulation merges duplicate sextuple keys
    by summing the ``±1`` signs — byte-identical to the pure-Python ``_lattice_py``.
    ``ep1, ep2, ep3, e1, e2, e3`` are the characteristic bits (each in ``{0, 1}``)."""
    if not has_native_riemann_theta_g3():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_g3_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g3_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g3_lattice(
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)), ctypes.c_int(int(ep3)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)), ctypes.c_int(int(e3)),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g3_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]),
               int(out[i + 3]), int(out[i + 4]), int(out[i + 5]))
        lat[key] = lat.get(key, 0) + int(out[i + 6])
        i += 7
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc80: the NEXT GENUS RUNG (the SCHOTTKY FRONTIER) — the GENUS-4 EXACT-INTEGER EXPONENT
# LATTICE (srmech_riemann_theta_g4). The Python RiemannThetaG4.lattice routes through
# this when has_native_riemann_theta_g4(); the pure-Python body is the COMPLETE
# alternative (and the parity oracle) — both emit the byte-identical canonical
# {(A1,A2,A3,A4,C12,C13,C14,C23,C24,C34): coeff} lattice.
# ----------------------------------------------------------------------


def has_native_riemann_theta_g4() -> bool:
    """True iff the rc80 ``srmech_riemann_theta_g4_lattice`` peer + its count helper are
    loaded + bound. False on a no-C / pre-rc80 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannThetaG4`` body is the complete alternative (and
    the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g4_lattice")
            and hasattr(LIB, "srmech_riemann_theta_g4_count"))


def riemann_theta_g4_lattice_c(ep1, ep2, ep3, ep4, e1, e2, e3, e4, box):
    """Native exact-integer genus-4 theta-constant exponent lattice → the canonical
    ``{(A₁,A₂,A₃,A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄): coeff}`` dict (the accumulated
    ``[A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign]`` 11-tuples over the box ``|nᵢ| ≤ box``),
    or ``None`` if the native symbols are absent. The accumulation merges duplicate
    10-tuple keys by summing the ``±1`` signs — byte-identical to the pure-Python
    ``_lattice_py``. ``ep1..ep4, e1..e4`` are the characteristic bits (each in
    ``{0, 1}``)."""
    if not has_native_riemann_theta_g4():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_g4_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g4_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g4_lattice(
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)),
        ctypes.c_int(int(ep3)), ctypes.c_int(int(ep4)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        ctypes.c_int(int(e3)), ctypes.c_int(int(e4)),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g4_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]), int(out[i + 3]),
               int(out[i + 4]), int(out[i + 5]), int(out[i + 6]),
               int(out[i + 7]), int(out[i + 8]), int(out[i + 9]))
        lat[key] = lat.get(key, 0) + int(out[i + 10])
        i += 11
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc86: the NEXT GENUS RUNG (PAST the SCHOTTKY FRONTIER) — the GENUS-5 EXACT-INTEGER
# EXPONENT LATTICE (srmech_riemann_theta_g5). The Python RiemannThetaG5.lattice routes
# through this when has_native_riemann_theta_g5(); the pure-Python body is the COMPLETE
# alternative (and the parity oracle) — both emit the byte-identical canonical
# {(A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45): coeff} lattice.
# ----------------------------------------------------------------------


def has_native_riemann_theta_g5() -> bool:
    """True iff the rc86 ``srmech_riemann_theta_g5_lattice`` peer + its count helper are
    loaded + bound. False on a no-C / pre-rc86 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannThetaG5`` body is the complete alternative (and
    the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g5_lattice")
            and hasattr(LIB, "srmech_riemann_theta_g5_count"))


def riemann_theta_g5_lattice_c(ep1, ep2, ep3, ep4, ep5, e1, e2, e3, e4, e5, box):
    """Native exact-integer genus-5 theta-constant exponent lattice → the canonical
    ``{(A₁..A₅,C₁₂,C₁₃,C₁₄,C₁₅,C₂₃,C₂₄,C₂₅,C₃₄,C₃₅,C₄₅): coeff}`` dict (the accumulated
    ``[A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign]`` 16-tuples over the box
    ``|nᵢ| ≤ box``), or ``None`` if the native symbols are absent. The accumulation merges
    duplicate 15-tuple keys by summing the ``±1`` signs — byte-identical to the pure-Python
    ``_lattice_py``. ``ep1..ep5, e1..e5`` are the characteristic bits (each in
    ``{0, 1}``)."""
    if not has_native_riemann_theta_g5():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_g5_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g5_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g5_lattice(
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)), ctypes.c_int(int(ep3)),
        ctypes.c_int(int(ep4)), ctypes.c_int(int(ep5)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)), ctypes.c_int(int(e3)),
        ctypes.c_int(int(e4)), ctypes.c_int(int(e5)),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g5_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]), int(out[i + 3]),
               int(out[i + 4]), int(out[i + 5]), int(out[i + 6]),
               int(out[i + 7]), int(out[i + 8]), int(out[i + 9]),
               int(out[i + 10]), int(out[i + 11]), int(out[i + 12]),
               int(out[i + 13]), int(out[i + 14]))
        lat[key] = lat.get(key, 0) + int(out[i + 15])
        i += 16
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc87: EXACT theta evaluation at a RATIONAL argument (the genus-axis Fay-trisecant /
# KP-Hirota FOUNDATION). The Python RiemannTheta.theta_at / RiemannThetaG3.theta_at
# route through these when the symbols are loaded; the pure-Python bodies are the
# COMPLETE alternatives (and the parity oracles). The C peer emits one
# [A,B,C,e_mod,sign] (g2) / [A1,A2,A3,C12,C13,C23,e_mod,sign] (g3) per lattice point;
# these marshallers parse the flat array into the shared (key, e_mod, sign) TERM stream
# that the Python theta_at accumulates (via the reused exact-DFT cyclotomic ring) —
# byte-identical to the pure-Python term stream.
# ----------------------------------------------------------------------


def has_native_riemann_theta_at() -> bool:
    """True iff the rc87 ``srmech_riemann_theta_at`` peer + its count helper are loaded
    + bound. False on a no-C / pre-rc87 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannTheta.theta_at`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_at")
            and hasattr(LIB, "srmech_riemann_theta_at_count"))


def riemann_theta_at_c(ep1, ep2, e1, e2, z1, z2, m, box):
    """Native exact genus-2 theta_at term stream → a list of ``(key, e_mod, sign)``
    tuples (``key = (A, B, C)``), or ``None`` if the native symbols are absent. The
    Python ``RiemannTheta.theta_at`` accumulates these into the canonical cyclotomic
    ``{(A, B, C): coeff}`` lattice (the same accumulation the pure path runs), so the
    native and pure paths are byte-identical. ``z1, z2`` the argument numerator, ``m``
    the root-of-unity order ``2·z_den``."""
    if not has_native_riemann_theta_at():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_at_c: bad box {box!r}")
    if not isinstance(m, int) or m < 2:
        raise ValueError(f"riemann_theta_at_c: bad m {m!r}")
    need = int(LIB.srmech_riemann_theta_at_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_at(
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        ctypes.c_int64(int(z1)), ctypes.c_int64(int(z2)), ctypes.c_int64(int(m)),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_riemann_theta_at returned non-OK status {rc}")
    terms = []
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]))
        terms.append((key, int(out[i + 3]), int(out[i + 4])))
        i += 5
    return terms


def has_native_riemann_theta_g3_at() -> bool:
    """True iff the rc87 ``srmech_riemann_theta_g3_at`` peer + its count helper are
    loaded + bound. False on a no-C / pre-rc87 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannThetaG3.theta_at`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g3_at")
            and hasattr(LIB, "srmech_riemann_theta_g3_at_count"))


def riemann_theta_g3_at_c(ep1, ep2, ep3, e1, e2, e3, z1, z2, z3, m, box):
    """Native exact genus-3 theta_at term stream → a list of ``(key, e_mod, sign)``
    tuples (``key = (A₁,A₂,A₃,C₁₂,C₁₃,C₂₃)``), or ``None`` if the native symbols are
    absent. The Python ``RiemannThetaG3.theta_at`` accumulates these into the canonical
    cyclotomic lattice (the same accumulation the pure path runs), so the native and
    pure paths are byte-identical. ``z1, z2, z3`` the argument numerator, ``m`` the
    root-of-unity order ``2·z_den``."""
    if not has_native_riemann_theta_g3_at():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_g3_at_c: bad box {box!r}")
    if not isinstance(m, int) or m < 2:
        raise ValueError(f"riemann_theta_g3_at_c: bad m {m!r}")
    need = int(LIB.srmech_riemann_theta_g3_at_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g3_at(
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)), ctypes.c_int(int(ep3)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)), ctypes.c_int(int(e3)),
        ctypes.c_int64(int(z1)), ctypes.c_int64(int(z2)), ctypes.c_int64(int(z3)),
        ctypes.c_int64(int(m)),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_riemann_theta_g3_at returned non-OK status {rc}")
    terms = []
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]),
               int(out[i + 3]), int(out[i + 4]), int(out[i + 5]))
        terms.append((key, int(out[i + 6]), int(out[i + 7])))
        i += 8
    return terms


def has_native_riemann_theta_cyc_mul() -> bool:
    """True iff the rc88 ``srmech_riemann_theta_cyc_mul`` peer is loaded + bound. False on
    a no-C / pre-rc88 lib — the pure-Python ``srmech.amsc.riemann_theta._cyc_mul_py`` body
    is the complete alternative (and the parity oracle + bignum fallback)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return hasattr(LIB, "srmech_riemann_theta_cyc_mul")


def riemann_theta_cyc_mul_c(a, b, table, m):
    """Native exact ``ℤ[ζ_m]`` power-basis product ``a · b`` → a length-``deg`` tuple, or
    ``None`` if the native symbol is absent / the table shape is wrong / a coefficient
    would exceed the int64 fast-path guard (the Python ``_cyc_mul_py`` body is the COMPLETE
    bignum alternative + the parity oracle). ``a``, ``b`` are length-``deg`` integer coeff
    vectors (``deg = φ(m)``); ``table`` the rc29 cyclotomic reduction table (``m`` rows ×
    ``deg`` cols, ``table[j]`` = ``ζ_m^j`` in the power basis). Byte-identical to the pure
    body on every native hit (the rc88 verifier's bilinear ring multiply)."""
    if not has_native_riemann_theta_cyc_mul():
        return None
    deg = len(a)
    if deg == 0 or len(b) != deg:
        raise ValueError("riemann_theta_cyc_mul_c: a, b must be equal nonzero length")
    if not isinstance(m, int) or m < 2:
        raise ValueError(f"riemann_theta_cyc_mul_c: bad m {m!r}")
    flat = []
    for row in table:
        flat.extend(int(x) for x in row)
    if len(flat) != m * deg:
        return None                       # table shape mismatch → pure path
    c_a = (ctypes.c_int64 * deg)(*[int(x) for x in a])
    c_b = (ctypes.c_int64 * deg)(*[int(x) for x in b])
    c_t = (ctypes.c_int64 * (m * deg))(*flat)
    c_out = (ctypes.c_int64 * deg)()
    rc = LIB.srmech_riemann_theta_cyc_mul(
        c_a, c_b, ctypes.c_uint32(deg), c_t, ctypes.c_uint32(int(m)), c_out)
    if rc == SRMECH_ERR_OVERFLOW:
        return None                       # exceeds int64 fast path → pure bignum path
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_riemann_theta_cyc_mul returned status {rc}")
    return tuple(int(c_out[k]) for k in range(deg))


# ----------------------------------------------------------------------
# rc81: the GENUS-4 CAPSTONE — the SCHOTTKY FORM J = theta^4(E8+E8) - theta^4(E16)
# representation-number COUNTER (srmech_riemann_theta_g4_schottky_count). The Python
# SchottkyFormG4._count_gram routes through this when has_native_riemann_theta_g4_schottky();
# the pure-Python body is the COMPLETE alternative (and the parity oracle) — both emit the
# byte-identical exact non-negative integer count of ordered g-tuples of minimal vectors
# with the prescribed off-diagonal doubled Gram.
# ----------------------------------------------------------------------


def has_native_riemann_theta_g4_schottky() -> bool:
    """True iff the rc81 ``srmech_riemann_theta_g4_schottky_count`` peer + its arena helper
    are loaded + bound. False on a no-C / pre-rc81 lib — the pure-Python
    ``srmech.amsc.riemann_theta.SchottkyFormG4._count_gram_py`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g4_schottky_count")
            and hasattr(LIB, "srmech_riemann_theta_g4_schottky_arena"))


def riemann_theta_g4_schottky_count_c(vecs, gram_off):
    """Native exact-integer count of ordered g-tuples of minimal (doubled) lattice vectors
    whose off-diagonal doubled Gram is ``gram_off`` (length 0/1/3/6 → genus 1/2/3/4), or
    ``None`` if the native symbols are absent. ``vecs`` is the list of doubled-integer
    minimal vectors (all the same length ``dim``); ``gram_off`` is the off-diagonal
    doubled-Gram tuple. Byte-identical to the pure-Python ``_count_gram_py``. Returns an
    exact non-negative ``int``."""
    if not has_native_riemann_theta_g4_schottky():
        return None
    n = len(vecs)
    if n == 0:
        return 0
    dim = len(vecs[0])
    genus = {0: 1, 1: 2, 3: 3, 6: 4}.get(len(gram_off))
    if genus is None:
        raise ValueError(
            f"riemann_theta_g4_schottky_count_c: gram_off length must be 0/1/3/6; "
            f"got {len(gram_off)}")
    flat = (ctypes.c_int64 * (n * dim))()
    p = 0
    for v in vecs:
        if len(v) != dim:
            raise ValueError("riemann_theta_g4_schottky_count_c: ragged vecs")
        for x in v:
            flat[p] = int(x)
            p += 1
    g_arr = (ctypes.c_int64 * max(len(gram_off), 1))()
    for idx, x in enumerate(gram_off):
        g_arr[idx] = int(x)
    arena_n = int(LIB.srmech_riemann_theta_g4_schottky_arena(ctypes.c_size_t(n)))
    arena = (ctypes.c_uint64 * max(arena_n, 1))()
    out_count = ctypes.c_int64(0)
    rc = LIB.srmech_riemann_theta_g4_schottky_count(
        flat, ctypes.c_size_t(n), ctypes.c_size_t(dim), ctypes.c_int(genus),
        g_arr, arena, ctypes.c_size_t(arena_n), ctypes.byref(out_count),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g4_schottky_count returned non-OK status {rc}")
    return int(out_count.value)


def has_native_riemann_theta_g4_schottky_shell() -> bool:
    """True iff the rc81 ``srmech_riemann_theta_g4_schottky_shell`` peer + its size helper
    are loaded + bound. False on a no-C / pre-rc81 lib — the pure-Python
    ``srmech.amsc.riemann_theta.SchottkyFormG4._full_shell_grams_py`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g4_schottky_shell")
            and hasattr(LIB, "srmech_riemann_theta_g4_schottky_shell_count"))


def riemann_theta_g4_schottky_shell_c(vecs, genus):
    """Native exact-integer FULL minimal-shell off-Gram histogram → the dict
    ``{off_gram (doubled, i<j tuple): count}`` (only nonzero counts), or ``None`` if the
    native symbols are absent. ``vecs`` is the doubled-integer minimal vectors; ``genus ∈
    {1,2,3,4}``. Byte-identical to the pure-Python ``_full_shell_grams_py``."""
    if not has_native_riemann_theta_g4_schottky_shell():
        return None
    if genus not in (1, 2, 3, 4):
        raise ValueError(f"riemann_theta_g4_schottky_shell_c: bad genus {genus!r}")
    n = len(vecs)
    if n == 0:
        return {}
    dim = len(vecs[0])
    noff = genus * (genus - 1) // 2
    flat = (ctypes.c_int64 * (n * dim))()
    p = 0
    for v in vecs:
        if len(v) != dim:
            raise ValueError("riemann_theta_g4_schottky_shell_c: ragged vecs")
        for x in v:
            flat[p] = int(x)
            p += 1
    arena_n = int(LIB.srmech_riemann_theta_g4_schottky_arena(ctypes.c_size_t(n)))
    arena = (ctypes.c_uint64 * max(arena_n, 1))()
    out_cap = int(LIB.srmech_riemann_theta_g4_schottky_shell_count(ctypes.c_int(genus)))
    out = (ctypes.c_int64 * max(out_cap, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g4_schottky_shell(
        flat, ctypes.c_size_t(n), ctypes.c_size_t(dim), ctypes.c_int(genus),
        arena, ctypes.c_size_t(arena_n), out, ctypes.c_size_t(out_cap),
        ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g4_schottky_shell returned non-OK status {rc}")
    res = {}
    m = int(out_len.value)
    i = 0
    while i < m:
        key = tuple(int(out[i + w]) for w in range(noff))
        res[key] = int(out[i + noff])
        i += noff + 1
    return res


# ----------------------------------------------------------------------
# rc76: IGUSA'S chi_18 — the EXACT product of the 36 even genus-3 theta-nulls
# (srmech_riemann_theta_g3_chi18). The Python RiemannThetaG3.chi18_leading_part routes
# through this when has_native_riemann_theta_g3_chi18(); the pure-Python body is the
# COMPLETE alternative (and the parity oracle) — both emit the byte-identical canonical
# {(A1,A2,A3,C12,C13,C23): coeff} leading-part lattice.
# ----------------------------------------------------------------------


def has_native_riemann_theta_g3_chi18() -> bool:
    """True iff the rc76 ``srmech_riemann_theta_g3_chi18`` peer + its count helper are
    loaded + bound. False on a no-C / pre-rc76 lib — the pure-Python
    ``srmech.amsc.riemann_theta.RiemannThetaG3.chi18_leading_part`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g3_chi18")
            and hasattr(LIB, "srmech_riemann_theta_g3_chi18_count"))


def riemann_theta_g3_chi18_c(box):
    """Native exact-integer Igusa χ₁₈ leading-part lattice → the canonical
    ``{(A₁, A₂, A₃, C₁₂, C₁₃, C₂₃): coeff}`` dict (the leading-order homogeneous part of
    the product of the 36 even genus-3 theta-nulls), or ``None`` if the native symbols
    are absent. Byte-identical to the pure-Python ``_chi18_leading_part_py``. ``box`` is
    for signature parity (must be ≥ 1; the leading part is box-independent)."""
    if not has_native_riemann_theta_g3_chi18():
        return None
    if not isinstance(box, int) or box < 1:
        raise ValueError(f"riemann_theta_g3_chi18_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g3_chi18_count(ctypes.c_uint32(int(box))))
    work = (ctypes.c_int64 * max(need, 1))()
    out_cap = need                                  # out[] sized like the work arena
    out = (ctypes.c_int64 * max(out_cap, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g3_chi18(
        ctypes.c_uint32(int(box)), work, ctypes.c_size_t(need),
        out, ctypes.c_size_t(out_cap), ctypes.byref(out_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g3_chi18 returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]),
               int(out[i + 3]), int(out[i + 4]), int(out[i + 5]))
        lat[key] = lat.get(key, 0) + int(out[i + 6])
        i += 7
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc77: the genus-3 Sp(6,Z) characteristic TRANSFORMATION + the genus-3 EIGHTH-nome
# lattice (the addition gate) — the g=2->g=3 parametric extension of the rc73 peers.
# The Python srmech.amsc.riemann_theta.RiemannThetaG3.{transform,addition_*} route
# through these when the symbols are loaded; the pure-Python bodies are the COMPLETE
# alternatives (and the parity oracles).
# ----------------------------------------------------------------------


def has_native_riemann_theta_g3_sp6() -> bool:
    """True iff the rc77 ``srmech_riemann_theta_g3_sp6_char`` peer (the EXACT integer
    Sp(6,Z) characteristic transformation + the κ 8th-root exponent) is loaded +
    bound. False on a no-C / pre-rc77 lib — the pure-Python
    ``RiemannThetaG3.transform`` body is the complete alternative (and the parity
    oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return hasattr(LIB, "srmech_riemann_theta_g3_sp6_char")


def has_native_riemann_theta_g3_eighth() -> bool:
    """True iff the rc77 ``srmech_riemann_theta_g3_eighth_lattice`` peer (the COMMON
    genus-3 eighth-nome lattice at Ω / 2Ω that the addition gate convolves) + its
    count helper are loaded + bound. False on a no-C / pre-rc77 lib — the pure-Python
    genus-3 addition body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g3_eighth_lattice")
            and hasattr(LIB, "srmech_riemann_theta_g3_eighth_count"))


def riemann_theta_g3_sp6_char_c(gamma, ep1, ep2, ep3, e1, e2, e3):
    """Native EXACT genus-3 Sp(6,Z) characteristic transformation: returns
    ``((ep1', ep2', ep3', e1', e2', e3'), kexp)`` — the six transformed characteristic
    bits and the 8th-root multiplier exponent ``kexp ∈ ℤ/8`` (the multiplier is
    ``ζ₈^kexp``) — or ``None`` if the native symbol is absent. ``gamma`` is the
    Sp(6,Z) element as four 3×3 integer blocks ``(A, B, C, D)``; the bridge flattens
    it to the 36 int entries (A,B,C,D row-major). Byte-identical to the pure-Python
    ``RiemannThetaG3._char_transform_int`` + ``_kappa_exp8``. Raises if gamma is not
    symplectic (the C peer returns SRMECH_ERR_BAD_INPUT)."""
    if not has_native_riemann_theta_g3_sp6():
        return None
    a, b, c, d = gamma
    flat = (ctypes.c_int64 * 36)(
        a[0][0], a[0][1], a[0][2], a[1][0], a[1][1], a[1][2],
        a[2][0], a[2][1], a[2][2],
        b[0][0], b[0][1], b[0][2], b[1][0], b[1][1], b[1][2],
        b[2][0], b[2][1], b[2][2],
        c[0][0], c[0][1], c[0][2], c[1][0], c[1][1], c[1][2],
        c[2][0], c[2][1], c[2][2],
        d[0][0], d[0][1], d[0][2], d[1][0], d[1][1], d[1][2],
        d[2][0], d[2][1], d[2][2])
    out_char = (ctypes.c_int * 6)()
    kexp = ctypes.c_int(0)
    rc = LIB.srmech_riemann_theta_g3_sp6_char(
        flat, ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)), ctypes.c_int(int(ep3)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)), ctypes.c_int(int(e3)),
        out_char, ctypes.byref(kexp))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g3_sp6_char returned non-OK status {rc}")
    return ((int(out_char[0]), int(out_char[1]), int(out_char[2]),
             int(out_char[3]), int(out_char[4]), int(out_char[5])),
            int(kexp.value) % 8)


def riemann_theta_g3_eighth_lattice_c(s1, s2, s3, e1, e2, e3, at_two_omega, box):
    """Native eighth-nome genus-3 theta-constant lattice → the canonical
    ``{(A₁, A₂, A₃, C₁₂, C₁₃, C₂₃): coeff}`` dict, or ``None`` if the native symbols
    are absent. ``at_two_omega`` selects θ at Ω (0) or at 2Ω (1); ``s1, s2, s3`` are
    the DOUBLED upper characteristic. Byte-identical to the pure-Python
    ``RiemannThetaG3._theta_omega_eighth`` / ``_theta_two_omega_eighth``."""
    if not has_native_riemann_theta_g3_eighth():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_g3_eighth_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g3_eighth_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g3_eighth_lattice(
        ctypes.c_int(int(s1)), ctypes.c_int(int(s2)), ctypes.c_int(int(s3)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)), ctypes.c_int(int(e3)),
        ctypes.c_int(1 if at_two_omega else 0),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g3_eighth_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]),
               int(out[i + 3]), int(out[i + 4]), int(out[i + 5]))
        lat[key] = lat.get(key, 0) + int(out[i + 6])
        i += 7
    return {k: v for k, v in lat.items() if v != 0}


# ----------------------------------------------------------------------
# rc78: the genus-3 GÖPEL / FROBENIUS quadratic theta-null SYZYGY gate
# (srmech_riemann_theta_g3_goepel). The Python RiemannThetaG3.goepel_holds routes
# through this when has_native_riemann_theta_g3_goepel(); the pure-Python body is the
# COMPLETE alternative (and the parity oracle) — both decide the same exact gate.
# ----------------------------------------------------------------------


def has_native_riemann_theta_g3_goepel() -> bool:
    """True iff the rc78 ``srmech_riemann_theta_g3_goepel`` peer (the genus-3
    Göpel/Frobenius quadratic theta-null syzygy gate) + its count helper are loaded +
    bound. False on a no-C / pre-rc78 lib — the pure-Python
    ``RiemannThetaG3.goepel_holds`` body is the complete alternative (and the parity
    oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g3_goepel")
            and hasattr(LIB, "srmech_riemann_theta_g3_goepel_count"))


def riemann_theta_g3_goepel_c(box):
    """Native genus-3 Göpel-syzygy gate decision → ``(holds, has_cross)`` (two bools) —
    ``holds`` iff the 4-pair / 8-null syzygy ``θ²[a]θ²[b] = θ²[c]θ²[d] + θ²[e]θ²[f]
    − θ²[g]θ²[h]`` holds EXACTLY on the box-stable safe region (LHS == RHS), and
    ``has_cross`` iff a genuine genus-3 cross-term (C₁₃ or C₂₃ ≠ 0) populates that
    region — or ``None`` if the native symbols are absent. Byte-identical decision to the
    pure-Python ``RiemannThetaG3.goepel_holds`` body. ``box`` must be ≥ 3."""
    if not has_native_riemann_theta_g3_goepel():
        return None
    if not isinstance(box, int) or box < 3:
        raise ValueError(f"riemann_theta_g3_goepel_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g3_goepel_count(ctypes.c_uint32(int(box))))
    work = (ctypes.c_int64 * max(need, 1))()
    out_holds = ctypes.c_int(0)
    out_has_cross = ctypes.c_int(0)
    rc = LIB.srmech_riemann_theta_g3_goepel(
        ctypes.c_uint32(int(box)), work, ctypes.c_size_t(need),
        ctypes.byref(out_holds), ctypes.byref(out_has_cross))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g3_goepel returned non-OK status {rc}")
    return (bool(out_holds.value), bool(out_has_cross.value))


# ----------------------------------------------------------------------
# rc85: the genus-4 Sp(8,ℤ) characteristic TRANSFORMATION + the genus-4 EIGHTH-nome
# lattice (the addition gate) + the genus-4 Göpel relation gate — the g=3->g=4
# parametric extension of the rc77/rc78 genus-3 peers. The Python
# srmech.amsc.riemann_theta.RiemannThetaG4.{transform,addition_*,goepel_holds} route
# through these when the symbols are loaded; the pure-Python bodies are the COMPLETE
# alternatives (and the parity oracles).
# ----------------------------------------------------------------------


def has_native_riemann_theta_g4_sp8() -> bool:
    """True iff the rc85 ``srmech_riemann_theta_g4_sp8_char`` peer (the EXACT integer
    Sp(8,ℤ) characteristic transformation + the κ 8th-root exponent) is loaded + bound.
    False on a no-C / pre-rc85 lib — the pure-Python ``RiemannThetaG4.transform`` body
    is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return hasattr(LIB, "srmech_riemann_theta_g4_sp8_char")


def has_native_riemann_theta_g4_eighth() -> bool:
    """True iff the rc85 ``srmech_riemann_theta_g4_eighth_lattice`` peer (the COMMON
    genus-4 eighth-nome lattice at Ω / 2Ω that the addition gate convolves) + its count
    helper are loaded + bound. False on a no-C / pre-rc85 lib — the pure-Python genus-4
    addition body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g4_eighth_lattice")
            and hasattr(LIB, "srmech_riemann_theta_g4_eighth_count"))


def riemann_theta_g4_sp8_char_c(gamma, ep1, ep2, ep3, ep4, e1, e2, e3, e4):
    """Native EXACT genus-4 Sp(8,ℤ) characteristic transformation: returns
    ``((ep1',ep2',ep3',ep4',e1',e2',e3',e4'), kexp)`` — the eight transformed
    characteristic bits and the 8th-root multiplier exponent ``kexp ∈ ℤ/8`` (the
    multiplier is ``ζ₈^kexp``) — or ``None`` if the native symbol is absent. ``gamma`` is
    the Sp(8,ℤ) element as four 4×4 integer blocks ``(A, B, C, D)``; the bridge flattens
    it to the 64 int entries (A,B,C,D row-major). Byte-identical to the pure-Python
    ``RiemannThetaG4._char_transform_int`` + ``_kappa_exp8``. Raises if gamma is not
    symplectic (the C peer returns SRMECH_ERR_BAD_INPUT)."""
    if not has_native_riemann_theta_g4_sp8():
        return None
    a, b, c, d = gamma
    flat = (ctypes.c_int64 * 64)()
    idx = 0
    for blk in (a, b, c, d):
        for r in range(4):
            for col in range(4):
                flat[idx] = int(blk[r][col])
                idx += 1
    out_char = (ctypes.c_int * 8)()
    kexp = ctypes.c_int(0)
    rc = LIB.srmech_riemann_theta_g4_sp8_char(
        flat,
        ctypes.c_int(int(ep1)), ctypes.c_int(int(ep2)),
        ctypes.c_int(int(ep3)), ctypes.c_int(int(ep4)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        ctypes.c_int(int(e3)), ctypes.c_int(int(e4)),
        out_char, ctypes.byref(kexp))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g4_sp8_char returned non-OK status {rc}")
    return ((int(out_char[0]), int(out_char[1]), int(out_char[2]), int(out_char[3]),
             int(out_char[4]), int(out_char[5]), int(out_char[6]), int(out_char[7])),
            int(kexp.value) % 8)


def riemann_theta_g4_eighth_lattice_c(s1, s2, s3, s4, e1, e2, e3, e4,
                                      at_two_omega, box):
    """Native eighth-nome genus-4 theta-constant lattice → the canonical
    ``{(A₁..A₄, C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄): coeff}`` dict, or ``None`` if the native
    symbols are absent. ``at_two_omega`` selects θ at Ω (0) or at 2Ω (1); ``s1..s4`` are
    the DOUBLED upper characteristic. Byte-identical to the pure-Python
    ``RiemannThetaG4._theta_omega_eighth`` / ``_theta_two_omega_eighth``."""
    if not has_native_riemann_theta_g4_eighth():
        return None
    if not isinstance(box, int) or box < 0:
        raise ValueError(f"riemann_theta_g4_eighth_lattice_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g4_eighth_count(ctypes.c_uint32(int(box))))
    out = (ctypes.c_int64 * max(need, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_riemann_theta_g4_eighth_lattice(
        ctypes.c_int(int(s1)), ctypes.c_int(int(s2)),
        ctypes.c_int(int(s3)), ctypes.c_int(int(s4)),
        ctypes.c_int(int(e1)), ctypes.c_int(int(e2)),
        ctypes.c_int(int(e3)), ctypes.c_int(int(e4)),
        ctypes.c_int(1 if at_two_omega else 0),
        ctypes.c_uint32(int(box)), out, ctypes.c_size_t(need),
        ctypes.byref(out_len))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g4_eighth_lattice returned non-OK status {rc}")
    lat = {}
    n = int(out_len.value)
    i = 0
    while i < n:
        key = (int(out[i]), int(out[i + 1]), int(out[i + 2]), int(out[i + 3]),
               int(out[i + 4]), int(out[i + 5]), int(out[i + 6]),
               int(out[i + 7]), int(out[i + 8]), int(out[i + 9]))
        lat[key] = lat.get(key, 0) + int(out[i + 10])
        i += 11
    return {k: v for k, v in lat.items() if v != 0}


def has_native_riemann_theta_g4_goepel() -> bool:
    """True iff the rc85 ``srmech_riemann_theta_g4_goepel`` peer (the genus-4 universal
    Göpel quadratic theta-null relation gate) + its count helper are loaded + bound.
    False on a no-C / pre-rc85 lib — the pure-Python ``RiemannThetaG4.goepel_holds``
    body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return (hasattr(LIB, "srmech_riemann_theta_g4_goepel")
            and hasattr(LIB, "srmech_riemann_theta_g4_goepel_count"))


def riemann_theta_g4_goepel_c(box):
    """Native genus-4 Göpel-relation gate decision → ``(holds, has_cross)`` (two bools) —
    ``holds`` iff the 8-pair / 16-null relation ``Σ_{+} θ²[a]θ²[b] = Σ_{−} θ²[a]θ²[b]``
    holds EXACTLY on the box-stable safe region, and ``has_cross`` iff a genuine genus-4
    cross-term (C₁₄, C₂₄ or C₃₄ ≠ 0) populates that region — or ``None`` if the native
    symbols are absent. Byte-identical decision to the pure-Python
    ``RiemannThetaG4.goepel_holds`` body. ``box`` must be ≥ 2."""
    if not has_native_riemann_theta_g4_goepel():
        return None
    if not isinstance(box, int) or box < 2:
        raise ValueError(f"riemann_theta_g4_goepel_c: bad box {box!r}")
    need = int(LIB.srmech_riemann_theta_g4_goepel_count(ctypes.c_uint32(int(box))))
    work = (ctypes.c_int64 * max(need, 1))()
    out_holds = ctypes.c_int(0)
    out_has_cross = ctypes.c_int(0)
    rc = LIB.srmech_riemann_theta_g4_goepel(
        ctypes.c_uint32(int(box)), work, ctypes.c_size_t(need),
        ctypes.byref(out_holds), ctypes.byref(out_has_cross))
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_riemann_theta_g4_goepel returned non-OK status {rc}")
    return (bool(out_holds.value), bool(out_has_cross.value))


def has_native_poly_gcd() -> bool:
    """True iff the rc39 ``srmech_poly_gcd`` single-call monic Euclidean GCD peer
    is loaded + bound (needs the rc38 poly base + the rc39 gcd symbol + its
    separate chain-scaled ws-bound). False on a no-C / pre-rc39 lib — the
    pure-Python ``Poly.gcd`` Euclid driver (whose inner long divisions still route
    through ``srmech_poly_divmod``) is the complete, ceiling-free alternative."""
    return bool(has_native_poly()
                and hasattr(LIB, "srmech_poly_gcd")
                and hasattr(LIB, "srmech_poly_gcd_ws_bound"))


def _poly_gcd_setup(a_coeffs, b_coeffs):
    """Sizing for the GCD chain: the per-coefficient limb cap + the SEPARATE
    chain-scaled caller arena (``srmech_poly_gcd_ws_bound``). The ``out_cap``
    over-sizes to the C ``poly_gcd_cap_for`` envelope (degree-squared headroom)
    so the output coefficients never overflow before the C op's own guard."""
    n_terms = max(len(a_coeffs), len(b_coeffs), 1)
    cl = max(_poly_coeff_limbs(a_coeffs) if a_coeffs else 1,
             _poly_coeff_limbs(b_coeffs) if b_coeffs else 1)
    # Match the C poly_gcd_cap_for: cl*nt + 2 step, * nt chain accumulation.
    step = cl * n_terms + 2
    out_cap = step * n_terms + step * 2 + 32 + 64
    ws_len = int(LIB.srmech_poly_gcd_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    return out_cap, ws, ws_len


def poly_gcd_c(a_coeffs, b_coeffs):
    """Native single-call monic Euclidean GCD over ℚ → reduced ``(num, den)``
    coefficient list (monic; ascending degree), or ``None`` if the native gcd
    peer is absent. ``gcd(0, 0) -> []`` (the zero polynomial)."""
    if not has_native_poly_gcd():
        return None
    na, nb = len(a_coeffs), len(b_coeffs)
    m = max(na, nb)
    if m == 0:
        return []
    out_cap, ws, ws_len = _poly_gcd_setup(a_coeffs, b_coeffs)
    a_n, a_d, ka = _poly_make_array(a_coeffs, out_cap)
    b_n, b_d, kb = _poly_make_array(b_coeffs, out_cap)
    o_n, o_d, ko = _poly_blank_array(m, out_cap)
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_poly_gcd(
        a_n, a_d, ctypes.c_size_t(na), b_n, b_d, ctypes.c_size_t(nb),
        o_n, o_d, ctypes.byref(out_len),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_poly_gcd returned non-OK status {rc}")
    return _poly_read_array(o_n, o_d, out_len.value)


# ----------------------------------------------------------------------
# rc54: the EXACT q-shift CARRIER C peer (srmech_qpoly_*). The Python
# srmech.amsc.qpoly.QPoly routes its add/sub/mul + the q-shift through these when
# has_native_qpoly(); the pure-Python body is the COMPLETE alternative (and the
# parity oracle) — both emit byte-identical exact (num, den) q-coefficients at any
# magnitude. The Python bridge form of a QPoly is (x_low, [[(num,den)…]_q]_x): the
# x-low offset plus an ascending-x list, each entry an ascending-q-degree q-run.
# The C peer flattens the x-row of q-runs into a single concatenated _SrmechBigint
# pair + a qlen[] array (the same pattern as the tripoly grid, one dimension
# lighter). add/sub require x-aligned inputs, so the wrapper pads both to the union
# x-window before the call and carries the result x_low itself.
# ----------------------------------------------------------------------

_QPOLY_SYMS = (
    "srmech_qpoly_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_qpoly() -> bool:
    """True iff the rc54 srmech_qpoly_* ops + the srmech_bigint decimal-marshal
    helpers are loaded + bound. False on a no-C or pre-rc54 lib — the pure-Python
    ``srmech.amsc.qpoly.QPoly`` body is the complete alternative (and the parity
    oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _QPOLY_SYMS) and hasattr(
        LIB, "srmech_qpoly_add"
    )


def _qp_row_coeff_limbs(rows):
    """The largest significant-limb count across every (num, den) in an x-row of
    q-runs (9 decimal digits ≈ 1 limb; pad)."""
    cl = 1
    for run in rows:
        for num, den in run:
            cl = max(cl, len(str(num).lstrip("-")) // 9 + 2,
                     len(str(den)) // 9 + 2)
    return cl


def _qp_flatten(rows, out_cap):
    """Flatten an x-row of q-runs to concatenated _SrmechBigint arrays + a qlen[]
    array. Returns ``(num_arr, den_arr, qlen_arr, keepalive)`` — the caller MUST
    keep ``keepalive`` (the limb buffers) alive for the call."""
    cells = len(rows)
    qlen = (ctypes.c_size_t * max(cells, 1))()
    total = sum(len(run) for run in rows)
    num_arr = (_SrmechBigint * max(total, 1))()
    den_arr = (_SrmechBigint * max(total, 1))()
    keep = []
    idx = 0
    for cidx, run in enumerate(rows):
        qlen[cidx] = len(run)
        for num, den in run:
            bn, kbn = _bigint_from_int(int(num), out_cap)
            bd, kbd = _bigint_from_int(int(den), out_cap)
            num_arr[idx] = bn
            den_arr[idx] = bd
            keep.append(kbn)
            keep.append(kbd)
            idx += 1
    return num_arr, den_arr, qlen, keep


def _qp_blank_cells(cell_caps, out_cap):
    """Build the concatenated blank output arrays. ``cell_caps`` is the per-x-cell
    pre-trim q-run capacity list. Returns ``(num_arr, den_arr, qlen_arr, offsets,
    keepalive)`` — ``offsets`` is each cell's base index, ``qlen_arr`` pre-zeroed."""
    cells = len(cell_caps)
    total = sum(cell_caps)
    num_arr = (_SrmechBigint * max(total, 1))()
    den_arr = (_SrmechBigint * max(total, 1))()
    qlen = (ctypes.c_size_t * max(cells, 1))()
    offsets = (ctypes.c_size_t * max(cells, 1))()
    keep = []
    idx = 0
    for cidx, cap in enumerate(cell_caps):
        offsets[cidx] = idx
        qlen[cidx] = 0
        for _ in range(cap):
            bn, kbn = _bigint_from_int(0, out_cap)
            bd, kbd = _bigint_from_int(1, out_cap)
            num_arr[idx] = bn
            den_arr[idx] = bd
            keep.append(kbn)
            keep.append(kbd)
            idx += 1
    return num_arr, den_arr, qlen, offsets, keep


def _qp_read_row(num_arr, den_arr, qlen, offsets, cells):
    """Read the concatenated result arrays back into an x-row of q-runs (the
    ascending-x list), using the per-cell trimmed lengths qlen[] + base
    offsets[]."""
    rows = []
    for cell in range(cells):
        base = offsets[cell]
        length = qlen[cell]
        run = []
        for i in range(length):
            run.append((_bigint_to_int(num_arr[base + i]),
                        _bigint_to_int(den_arr[base + i])))
        rows.append(run)
    return rows


def _qp_setup(*rows_seqs, accum_terms=1):
    """Common sizing for a set of input x-rows: the per-coefficient limb cap
    (``out_cap``) and the caller arena (``ws``, ``ws_len``). ``accum_terms`` is the
    worst-case output q-run length (the convolution depth)."""
    cl = 1
    for rows in rows_seqs:
        cl = max(cl, _qp_row_coeff_limbs(rows))
    n_terms = accum_terms + 1
    # Match the C qp_cap_for product-of-magnitudes envelope (generous).
    out_cap = (cl * n_terms + 2) * 2 + cl * 2 + 64
    ws_len = int(LIB.srmech_qpoly_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    return out_cap, ws, ws_len


def qpoly_addsub_c(a_form, b_form, sub):
    """Native exact-ℚ[q] x-cellwise add/sub → the ``(x_low, rows)`` bridge form, or
    ``None`` if absent. ``a_form`` / ``b_form`` are ``(x_low, rows)`` pairs (each
    ``rows`` an ascending-x list of ascending-q (num, den) runs). The wrapper pads
    both inputs to the union x-window so the C op aligns by index, then carries the
    union ``x_low`` on the result."""
    symbol = "srmech_qpoly_sub" if sub else "srmech_qpoly_add"
    if not has_native_qpoly() or not hasattr(LIB, symbol):
        return None
    a_lo, a_rows = a_form
    b_lo, b_rows = b_form
    lo = min(a_lo, b_lo)
    hi = max(a_lo + len(a_rows) - 1, b_lo + len(b_rows) - 1)
    cells = hi - lo + 1 if (a_rows or b_rows) else 0
    if cells <= 0:
        return (lo, [])
    a_pad = _qp_align_rows(a_rows, a_lo, lo, cells)
    b_pad = _qp_align_rows(b_rows, b_lo, lo, cells)
    out_cap, ws, ws_len = _qp_setup(a_pad, b_pad)
    a_n, a_d, a_q, ka = _qp_flatten(a_pad, out_cap)
    b_n, b_d, b_q, kb = _qp_flatten(b_pad, out_cap)
    # output cell q-run capacity = max(na, nb) per cell — this IS the C op's
    # internal write stride (o_off += max(na,nb)); use it EXACTLY (no floor) so
    # the Python read offsets match the C cell strides byte-for-byte.
    cell_caps = [max(len(a_pad[i]), len(b_pad[i])) for i in range(cells)]
    o_n, o_d, o_q, o_off, ko = _qp_blank_cells(cell_caps, out_cap)
    rc = getattr(LIB, symbol)(
        a_n, a_d, a_q, ctypes.c_size_t(cells), b_n, b_d, b_q,
        o_n, o_d, o_q, ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"{symbol} returned non-OK status {rc}")
    rows = _qp_read_row(o_n, o_d, o_q, o_off, cells)
    return (lo, rows)


def _qp_align_rows(rows, src_lo, dst_lo, cells):
    """Pad an x-row to the window ``[dst_lo, dst_lo + cells)`` with empty q-runs for
    the missing low/high x-cells (so two rows align by index for the C op)."""
    out = [[] for _ in range(cells)]
    for i, run in enumerate(rows):
        out[(src_lo + i) - dst_lo] = run
    return out


def qpoly_mul_c(a_form, b_form):
    """Native exact-ℚ[q] x-convolution product → the ``(x_low, rows)`` bridge form,
    or ``None`` if absent. The output x_low is ``a_lo + b_lo``."""
    if not has_native_qpoly() or not hasattr(LIB, "srmech_qpoly_mul"):
        return None
    a_lo, a_rows = a_form
    b_lo, b_rows = b_form
    acells, bcells = len(a_rows), len(b_rows)
    if acells == 0 or bcells == 0:
        return (0, [])
    ocells = acells + bcells - 1
    amax = max((len(run) for run in a_rows), default=0)
    bmax = max((len(run) for run in b_rows), default=0)
    accum = max(amax + bmax - 1, 1)
    out_cap, ws, ws_len = _qp_setup(a_rows, b_rows, accum_terms=accum)
    a_n, a_d, a_q, ka = _qp_flatten(a_rows, out_cap)
    b_n, b_d, b_q, kb = _qp_flatten(b_rows, out_cap)
    cell_caps = [accum] * ocells
    o_n, o_d, o_q, o_off, ko = _qp_blank_cells(cell_caps, out_cap)
    rc = LIB.srmech_qpoly_mul(
        a_n, a_d, a_q, ctypes.c_size_t(acells),
        b_n, b_d, b_q, ctypes.c_size_t(bcells),
        o_n, o_d, o_q, o_off, ctypes.c_size_t(accum),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qpoly_mul returned non-OK status {rc}")
    rows = _qp_read_row(o_n, o_d, o_q, o_off, ocells)
    return (a_lo + b_lo, rows)


def qpoly_qshift_c(a_form, s):
    """Native exact-ℚ[q] q-shift ``σ**s : x ↦ q**s·x`` → the ``(x_low, rows)`` bridge
    form, or ``None`` if absent. Each cell's q-run shifts up by ``s·e`` q-degrees;
    a negative ``s·e`` raises ``ValueError`` (leaves ℚ[q]). x-window unchanged."""
    if not has_native_qpoly() or not hasattr(LIB, "srmech_qpoly_qshift"):
        return None
    x_low, rows = a_form
    cells = len(rows)
    if cells == 0:
        return (x_low, [])
    # output cell q-run capacity = in q-len + s·e (the shift grows the run).
    cell_caps = []
    for i, run in enumerate(rows):
        e = x_low + i
        sh = s * e
        if sh < 0:
            raise ValueError(
                f"qpoly_qshift_c: negative q-shift s·e={sh} leaves ℚ[q]")
        cell_caps.append(max(len(run) + sh, 1))
    out_cap, ws, ws_len = _qp_setup(rows, accum_terms=max(cell_caps))
    a_n, a_d, a_q, ka = _qp_flatten(rows, out_cap)
    o_n, o_d, o_q, o_off, ko = _qp_blank_cells(cell_caps, out_cap)
    rc = LIB.srmech_qpoly_qshift(
        a_n, a_d, a_q, ctypes.c_size_t(cells),
        ctypes.c_int64(int(s)), ctypes.c_int64(int(x_low)),
        o_n, o_d, o_q, o_off,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qpoly_qshift returned non-OK status {rc}")
    rows_out = _qp_read_row(o_n, o_d, o_q, o_off, cells)
    return (x_low, rows_out)


# ----------------------------------------------------------------------
# rc52: the EXACT-RATIONAL TRIVARIATE polynomial carrier C peer
# (srmech_tripoly_*). The Python srmech.amsc.tripoly.TriPoly routes its
# add/sub/mul through these when has_native_tripoly(); the pure-Python body is
# the COMPLETE alternative (and the parity oracle) — both emit byte-identical
# exact (num, den) coefficients at any magnitude.
#
# The Python bridge form of a TriPoly is the nested [[[(num,den)…]_n]_k]_j grid
# (j-major, then k, then ascending-n Poly coefficients). The C peer consumes the
# (j,k) grid FLATTENED row-major into a single concatenated _SrmechBigint
# coefficient array pair (nums[]/dens[], cells in row-major (j,k) order, ascending
# n within each cell) plus a parallel cell-length array nlen[] (length aj*ak).
# ----------------------------------------------------------------------

_TRIPOLY_SYMS = (
    "srmech_tripoly_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_tripoly() -> bool:
    """True iff the rc52 srmech_tripoly_* ops + the srmech_bigint decimal-marshal
    helpers are loaded + bound. False on a no-C or pre-rc52 lib — the pure-Python
    ``srmech.amsc.tripoly.TriPoly`` body is the complete alternative (and the
    parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _TRIPOLY_SYMS) and hasattr(
        LIB, "srmech_tripoly_add"
    )


def _tri_grid_dims(grid):
    """A nested [[[(num,den)…]_n]_k]_j grid → (aj, ak), the j-degree+1 and the max
    k-degree+1 across all j-blocks (the rectangular (j,k) shape the flat C form
    pads to)."""
    aj = len(grid)
    ak = 0
    for kgrid in grid:
        if len(kgrid) > ak:
            ak = len(kgrid)
    return aj, ak


def _tri_grid_coeff_limbs(grid):
    """The largest significant-limb count across every (num, den) in a nested
    grid (9 decimal digits ≈ 1 limb; pad)."""
    cl = 1
    for kgrid in grid:
        for run in kgrid:
            for num, den in run:
                cl = max(cl, len(str(num).lstrip("-")) // 9 + 2,
                         len(str(den)) // 9 + 2)
    return cl


def _tri_flatten(grid, aj, ak, out_cap):
    """Flatten a nested grid to row-major (j,k) concatenated _SrmechBigint arrays
    over the (aj x ak) rectangle (missing cells → empty n-runs). Returns
    ``(num_arr, den_arr, nlen_arr, keepalive)`` — the caller MUST keep
    ``keepalive`` (the limb buffers) alive for the call."""
    runs = []
    cells = aj * ak
    nlen = (ctypes.c_size_t * max(cells, 1))()
    total = 0
    for dj in range(aj):
        kgrid = grid[dj] if dj < len(grid) else []
        for dk in range(ak):
            run = kgrid[dk] if dk < len(kgrid) else []
            runs.append(run)
            nlen[dj * ak + dk] = len(run)
            total += len(run)
    num_arr = (_SrmechBigint * max(total, 1))()
    den_arr = (_SrmechBigint * max(total, 1))()
    keep = []
    idx = 0
    for run in runs:
        for num, den in run:
            bn, kbn = _bigint_from_int(int(num), out_cap)
            bd, kbd = _bigint_from_int(int(den), out_cap)
            num_arr[idx] = bn
            den_arr[idx] = bd
            keep.append(kbn)
            keep.append(kbd)
            idx += 1
    return num_arr, den_arr, nlen, keep


def _tri_blank_cells(cell_caps, out_cap):
    """Build the concatenated blank output arrays. ``cell_caps`` is the per-cell
    pre-trim n-run capacity list; the total is their sum. Returns
    ``(num_arr, den_arr, nlen_arr, offsets, keepalive)`` — ``offsets`` is each
    cell's base index into the concatenated arrays, ``nlen_arr`` is pre-zeroed."""
    cells = len(cell_caps)
    total = sum(cell_caps)
    num_arr = (_SrmechBigint * max(total, 1))()
    den_arr = (_SrmechBigint * max(total, 1))()
    nlen = (ctypes.c_size_t * max(cells, 1))()
    offsets = (ctypes.c_size_t * max(cells, 1))()
    keep = []
    idx = 0
    for cidx, cap in enumerate(cell_caps):
        offsets[cidx] = idx
        nlen[cidx] = 0
        for _ in range(cap):
            bn, kbn = _bigint_from_int(0, out_cap)
            bd, kbd = _bigint_from_int(1, out_cap)
            num_arr[idx] = bn
            den_arr[idx] = bd
            keep.append(kbn)
            keep.append(kbd)
            idx += 1
    return num_arr, den_arr, nlen, offsets, keep


def _tri_read_grid(num_arr, den_arr, nlen, offsets, aj, ak):
    """Read the concatenated result arrays back into the nested
    [[[(num,den)…]_n]_k]_j grid (j-major, then k), using the per-cell trimmed
    lengths nlen[] + base offsets[]. Trailing-empty cells/blocks stay (the carrier
    re-trims on the Python side)."""
    grid = []
    for dj in range(aj):
        kgrid = []
        for dk in range(ak):
            cell = dj * ak + dk
            base = offsets[cell]
            length = nlen[cell]
            run = []
            for i in range(length):
                run.append((_bigint_to_int(num_arr[base + i]),
                            _bigint_to_int(den_arr[base + i])))
            kgrid.append(run)
        grid.append(kgrid)
    return grid


def _tri_setup(*grids, accum_terms=1):
    """Common sizing for a set of input grids: the per-coefficient limb cap
    (``out_cap``) and the caller arena (``ws``, ``ws_len``). ``accum_terms`` is the
    worst-case output n-run length (the convolution depth)."""
    cl = 1
    for g in grids:
        cl = max(cl, _tri_grid_coeff_limbs(g))
    n_terms = accum_terms + 1
    # Match the C tri_cap_for product-of-magnitudes envelope (generous).
    out_cap = (cl * n_terms + 2) * 2 + cl * 2 + 64
    ws_len = int(LIB.srmech_tripoly_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_terms)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    return out_cap, ws, ws_len


def tripoly_add_c(a_grid, b_grid):
    """Native exact-ℚ trivariate add → the nested [[[(num,den)…]_n]_k]_j grid, or
    ``None`` if the native symbols are absent."""
    return _tripoly_addsub_c("srmech_tripoly_add", a_grid, b_grid)


def tripoly_sub_c(a_grid, b_grid):
    """Native exact-ℚ trivariate subtract (see :func:`tripoly_add_c`)."""
    return _tripoly_addsub_c("srmech_tripoly_sub", a_grid, b_grid)


def _tripoly_addsub_c(symbol, a_grid, b_grid):
    if not has_native_tripoly() or not hasattr(LIB, symbol):
        return None
    aj, ak = _tri_grid_dims(a_grid)
    bj, bk = _tri_grid_dims(b_grid)
    oj, ok = max(aj, bj), max(ak, bk)            # the aligned rectangle
    cells = oj * ok
    out_cap, ws, ws_len = _tri_setup(a_grid, b_grid, accum_terms=1)
    a_n, a_d, a_nlen, ka = _tri_flatten(a_grid, oj, ok, out_cap)
    b_n, b_d, b_nlen, kb = _tri_flatten(b_grid, oj, ok, out_cap)
    # per-cell pre-trim stride = max(a_cell_len, b_cell_len) — EXACTLY the C
    # tri_addsub stride `o_off += max(na, nb)` (an empty+empty cell strides 0, so
    # the Python offset layout must NOT floor to 1 or it would diverge after the
    # first all-empty cell).
    cell_caps = [max(a_nlen[c], b_nlen[c]) for c in range(cells)]
    o_n, o_d, o_nlen, o_off, ko = _tri_blank_cells(cell_caps, out_cap)
    rc = getattr(LIB, symbol)(
        a_n, a_d, a_nlen, ctypes.c_size_t(cells),
        b_n, b_d, b_nlen,
        o_n, o_d, o_nlen,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"{symbol} returned non-OK status {rc}")
    return _tri_read_grid(o_n, o_d, o_nlen, o_off, oj, ok)


def tripoly_mul_c(a_grid, b_grid):
    """Native exact-ℚ trivariate product (2-D (j,k) convolution; each cell an
    n-run convolution) → the nested grid, or ``None`` if absent."""
    if not has_native_tripoly() or not hasattr(LIB, "srmech_tripoly_mul"):
        return None
    aj, ak = _tri_grid_dims(a_grid)
    bj, bk = _tri_grid_dims(b_grid)
    if aj == 0 or ak == 0 or bj == 0 or bk == 0:
        return []
    oj, ok = aj + bj - 1, ak + bk - 1
    cells = oj * ok
    # worst-case output n-run length = max input n-run lengths summed - 1.
    amax = max((len(run) for kg in a_grid for run in kg), default=0)
    bmax = max((len(run) for kg in b_grid for run in kg), default=0)
    accum = max(amax + bmax - 1, 1)
    out_cap, ws, ws_len = _tri_setup(a_grid, b_grid, accum_terms=accum)
    a_n, a_d, a_nlen, ka = _tri_flatten(a_grid, aj, ak, out_cap)
    b_n, b_d, b_nlen, kb = _tri_flatten(b_grid, bj, bk, out_cap)
    cell_caps = [accum] * cells
    o_n, o_d, o_nlen, o_off, ko = _tri_blank_cells(cell_caps, out_cap)
    rc = LIB.srmech_tripoly_mul(
        a_n, a_d, a_nlen, ctypes.c_size_t(aj), ctypes.c_size_t(ak),
        b_n, b_d, b_nlen, ctypes.c_size_t(bj), ctypes.c_size_t(bk),
        o_n, o_d, o_nlen, o_off, ctypes.c_size_t(ok), ctypes.c_size_t(accum),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_tripoly_mul returned non-OK status {rc}")
    return _tri_read_grid(o_n, o_d, o_nlen, o_off, oj, ok)


# ----------------------------------------------------------------------
# rc40: the EXACT-RATIONAL matrix carrier C peer (srmech_qmat_*). The Python
# srmech.amsc.qmat.QMat routes its rref/rank/det/inverse/solve/nullspace through
# these when has_native_qmat(); the pure-Python Gauss-Jordan body is the COMPLETE
# alternative (and the parity oracle) — both emit byte-identical exact (num, den)
# entries at any magnitude. The marshalling builds ROW-MAJOR parallel
# _SrmechBigint entry arrays over the decimal bridge (same pattern as the poly
# peer), keeping the backing limb buffers alive for the call.
# ----------------------------------------------------------------------

_QMAT_SYMS = (
    "srmech_qmat_ws_bound",
    "srmech_qmat_entry_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_qmat() -> bool:
    """True iff the rc40 srmech_qmat_* ops + the srmech_bigint decimal-marshal
    helpers are loaded + bound. False on a no-C or pre-rc40 lib — the pure-Python
    ``srmech.amsc.qmat.QMat`` Gauss-Jordan body is the complete alternative (and
    the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _QMAT_SYMS) and hasattr(
        LIB, "srmech_qmat_rref"
    )


def _qmat_coeff_limbs(pairs) -> int:
    """The largest significant-limb count across a flat ``(num, den)`` entry
    sequence (9 decimal digits ~ 1 limb; pad)."""
    cl = 1
    for num, den in pairs:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    return cl


def _qmat_make_array(pairs, out_cap):
    """Build ROW-MAJOR parallel ``_SrmechBigint`` arrays (nums, dens) from a flat
    ``(num, den)`` entry sequence, each carrier ``out_cap`` limbs. Returns
    ``(num_arr, den_arr, keepalive)`` — keep the limb buffers alive for the call."""
    n = len(pairs)
    num_arr = (_SrmechBigint * max(n, 1))()
    den_arr = (_SrmechBigint * max(n, 1))()
    keep = []
    for i, (num, den) in enumerate(pairs):
        bn, kbn = _bigint_from_int(int(num), out_cap)
        bd, kbd = _bigint_from_int(int(den), out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
    return num_arr, den_arr, keep


def _qmat_blank_array(n, out_cap):
    """Build blank ``(num=0, den=1)`` parallel ``_SrmechBigint`` output arrays of
    ``n`` slots, each ``out_cap`` limbs."""
    num_arr = (_SrmechBigint * max(n, 1))()
    den_arr = (_SrmechBigint * max(n, 1))()
    keep = []
    for i in range(n):
        bn, kbn = _bigint_from_int(0, out_cap)
        bd, kbd = _bigint_from_int(1, out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
    return num_arr, den_arr, keep


def _qmat_read_array(num_arr, den_arr, length):
    """Read the first ``length`` entries of a result ``_SrmechBigint`` array pair
    back to a list of ``(num, den)`` Python-int tuples."""
    return [(_bigint_to_int(num_arr[i]), _bigint_to_int(den_arr[i]))
            for i in range(length)]


def _qmat_setup(a_pairs, total_cols, n_rows, *extra):
    """Common sizing: the per-entry limb cap (``out_cap`` = the C qmat_entry_cap,
    so output entries never overflow before the op's own guard) + the caller arena
    (``ws``, ``ws_len`` = srmech_qmat_ws_bound). ``extra`` is further pair
    sequences (e.g. the solve RHS) folded into the coeff-limb estimate."""
    cl = _qmat_coeff_limbs(a_pairs)
    for seq in extra:
        if seq:
            cl = max(cl, _qmat_coeff_limbs(seq))
    out_cap = int(LIB.srmech_qmat_entry_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_rows), ctypes.c_size_t(total_cols)))
    ws_len = int(LIB.srmech_qmat_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_rows), ctypes.c_size_t(total_cols)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    return out_cap, ws, ws_len


def qmat_rref_c(a_pairs, n_rows, n_cols):
    """Native exact-ℚ RREF → ``(rref_pairs, rank, pivot_cols)`` (rref_pairs is the
    row-major reduced matrix as ``(num, den)`` tuples), or ``None`` if absent.
    ``a_pairs`` is the row-major ``(num, den)`` entry sequence."""
    if not has_native_qmat() or not hasattr(LIB, "srmech_qmat_rref"):
        return None
    out_cap, ws, ws_len = _qmat_setup(a_pairs, n_cols, n_rows)
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    o_n, o_d, ko = _qmat_blank_array(max(n_rows * n_cols, 1), out_cap)
    rank = ctypes.c_size_t(0)
    piv = (ctypes.c_size_t * max(n_cols, 1))()
    rc = LIB.srmech_qmat_rref(
        a_n, a_d, ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols),
        o_n, o_d, ctypes.byref(rank), piv,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qmat_rref returned non-OK status {rc}")
    pairs = _qmat_read_array(o_n, o_d, n_rows * n_cols)
    return pairs, rank.value, [piv[i] for i in range(rank.value)]


def qmat_rank_c(a_pairs, n_rows, n_cols):
    """Native exact-ℚ rank → ``int``, or ``None`` if absent."""
    if not has_native_qmat() or not hasattr(LIB, "srmech_qmat_rank"):
        return None
    out_cap, ws, ws_len = _qmat_setup(a_pairs, n_cols, n_rows)
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    rank = ctypes.c_size_t(0)
    rc = LIB.srmech_qmat_rank(
        a_n, a_d, ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols),
        ctypes.byref(rank),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = ka
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qmat_rank returned non-OK status {rc}")
    return rank.value


def qmat_det_c(a_pairs, n):
    """Native exact-ℚ determinant → one reduced ``(num, den)`` tuple, or ``None``
    if absent."""
    if not has_native_qmat() or not hasattr(LIB, "srmech_qmat_det"):
        return None
    out_cap, ws, ws_len = _qmat_setup(a_pairs, n + n, n)
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    o_n, kon = _bigint_from_int(0, out_cap)
    o_d, kod = _bigint_from_int(1, out_cap)
    rc = LIB.srmech_qmat_det(
        a_n, a_d, ctypes.c_size_t(n),
        ctypes.byref(o_n), ctypes.byref(o_d),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kon, kod)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qmat_det returned non-OK status {rc}")
    return (_bigint_to_int(o_n), _bigint_to_int(o_d))


def qmat_inverse_c(a_pairs, n):
    """Native exact-ℚ inverse → ``(inv_pairs, singular)`` (inv_pairs is the
    row-major inverse as ``(num, den)`` tuples; ``singular`` is True when A is not
    invertible, in which case inv_pairs is unspecified), or ``None`` if absent."""
    if not has_native_qmat() or not hasattr(LIB, "srmech_qmat_inverse"):
        return None
    out_cap, ws, ws_len = _qmat_setup(a_pairs, n + n, n)
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    o_n, o_d, ko = _qmat_blank_array(max(n * n, 1), out_cap)
    sing = ctypes.c_int(0)
    rc = LIB.srmech_qmat_inverse(
        a_n, a_d, ctypes.c_size_t(n), o_n, o_d, ctypes.byref(sing),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qmat_inverse returned non-OK status {rc}")
    if sing.value:
        return [], True
    return _qmat_read_array(o_n, o_d, n * n), False


def qmat_solve_c(a_pairs, n, b_pairs, b_cols):
    """Native exact-ℚ solve A x = b → ``(x_pairs, singular)`` (x_pairs is the
    row-major n×b_cols solution; ``singular`` True when A is not full-rank), or
    ``None`` if absent. ``b_pairs`` is the row-major n×b_cols RHS block."""
    if not has_native_qmat() or not hasattr(LIB, "srmech_qmat_solve"):
        return None
    out_cap, ws, ws_len = _qmat_setup(a_pairs, n + b_cols, n, b_pairs)
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    b_n, b_d, kb = _qmat_make_array(b_pairs, out_cap)
    o_n, o_d, ko = _qmat_blank_array(max(n * b_cols, 1), out_cap)
    sing = ctypes.c_int(0)
    rc = LIB.srmech_qmat_solve(
        a_n, a_d, ctypes.c_size_t(n), b_n, b_d, ctypes.c_size_t(b_cols),
        o_n, o_d, ctypes.byref(sing),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, kb, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qmat_solve returned non-OK status {rc}")
    if sing.value:
        return [], True
    return _qmat_read_array(o_n, o_d, n * b_cols), False


def qmat_nullspace_c(a_pairs, n_rows, n_cols):
    """Native exact-ℚ kernel basis → list of column basis vectors, each a list of
    ``n_cols`` ``(num, den)`` tuples (matching QMat.nullspace's per-column basis),
    or ``None`` if absent. Empty list iff A has full column rank."""
    if not has_native_qmat() or not hasattr(LIB, "srmech_qmat_nullspace"):
        return None
    out_cap, ws, ws_len = _qmat_setup(a_pairs, n_cols, n_rows)
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    # the C stores the (n_cols x nfree) basis column-major into an n_cols*n_cols
    # row-major block: out[i*n_cols + j] is entry i of basis column j.
    o_n, o_d, ko = _qmat_blank_array(max(n_cols * n_cols, 1), out_cap)
    nfree = ctypes.c_size_t(0)
    rc = LIB.srmech_qmat_nullspace(
        a_n, a_d, ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols),
        o_n, o_d, ctypes.byref(nfree),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, ko)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_qmat_nullspace returned non-OK status {rc}")
    flat = _qmat_read_array(o_n, o_d, n_cols * n_cols)
    # rebuild the nfree column vectors: column j's entry i is flat[i*n_cols + j].
    return [[flat[i * n_cols + j] for i in range(n_cols)]
            for j in range(nfree.value)]


def has_native_qmat_rref_crt() -> bool:
    """True iff the rc48 srmech_qmat_rref_crt CRT re-fibration peer (the CLOSER of
    the CRT-QMat arc) + its ws-bound helper are loaded + bound. False on a no-C /
    pre-rc48 lib — the pure-Python ``QMat.rref_crt`` body (composing the Class-I
    gf_rref / crt_combine over the Class-J descending prime field + the Class-N
    rational_reconstruct) is the complete, byte-identical alternative (and the
    parity oracle)."""
    return bool(has_native_qmat()
                and hasattr(LIB, "srmech_qmat_rref_crt")
                and hasattr(LIB, "srmech_qmat_rref_crt_ws_bound")
                and hasattr(LIB, "srmech_qmat_rref_crt_entry_cap"))


def qmat_rref_crt_c(a_pairs, n_rows, n_cols):
    """Native bounded-memory exact-ℚ RREF via CRT re-fibration →
    ``(rref_pairs, rank, pivot_cols)`` (rref_pairs is the row-major reduced matrix
    as ``(num, den)`` tuples), or ``None`` if the native symbol is absent / the C
    op reports OVERFLOW (the pure-Python CRT body is the complete fallback).

    Same wire shape as :func:`qmat_rref_c`, but BOTH the arena
    (``srmech_qmat_rref_crt_ws_bound``) AND the output entry cap
    (``srmech_qmat_rref_crt_entry_cap``) are sized from the ANSWER-Hadamard
    good-prime bound, NOT the dense Cramer-minor cap (using the dense
    ``srmech_qmat_entry_cap`` for the output would re-reserve the ~2.3 GB the CRT
    row exists to escape). Bounded (answer-sized) memory end-to-end."""
    if not has_native_qmat_rref_crt():
        return None
    cl = _qmat_coeff_limbs(a_pairs)
    out_cap = int(LIB.srmech_qmat_rref_crt_entry_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols)))
    ws_len = int(LIB.srmech_qmat_rref_crt_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    a_n, a_d, ka = _qmat_make_array(a_pairs, out_cap)
    o_n, o_d, ko = _qmat_blank_array(max(n_rows * n_cols, 1), out_cap)
    rank = ctypes.c_size_t(0)
    piv = (ctypes.c_size_t * max(n_cols, 1))()
    rc = LIB.srmech_qmat_rref_crt(
        a_n, a_d, ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols),
        o_n, o_d, ctypes.byref(rank), piv,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (ka, ko)
    if rc != SRMECH_OK:
        # OVERFLOW (answer outgrew the answer-cap, or arena too small) / any
        # non-OK status → fall back to the pure-Python CRT path (complete).
        return None
    pairs = _qmat_read_array(o_n, o_d, n_rows * n_cols)
    return pairs, rank.value, [piv[i] for i in range(rank.value)]


def qmat_rref_crt_arena_bytes(a_pairs, n_rows, n_cols):
    """The C arena size (BYTES) ``srmech_qmat_rref_crt`` requests for this input —
    the answer-sized CRT bound (NOT the dense Hadamard envelope). Returns ``None``
    if the native ws-bound helper is absent. Diagnostic surface for the
    bounded-arena measurement (the rc48 verify gate)."""
    if not has_native_qmat_rref_crt():
        return None
    cl = _qmat_coeff_limbs(a_pairs)
    return int(LIB.srmech_qmat_rref_crt_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(n_rows), ctypes.c_size_t(n_cols)))


# ----------------------------------------------------------------------
# rc41: srmech_gosper — Gosper's indefinite hypergeometric summation (the §76
# telescope Sigma-row's first public op). The Python srmech.amsc.gosper.gosper
# routes through this when has_native_gosper(); the pure-Python body is the
# COMPLETE alternative (and the parity oracle) — both emit the same reduced
# (num, den) certificate at any magnitude. The marshalling reuses the qmat /
# poly _SrmechBigint coefficient-array bridge.
# ----------------------------------------------------------------------

_GOSPER_SYMS = (
    "srmech_gosper_ws_bound",
    "srmech_gosper_out_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_gosper() -> bool:
    """True iff the rc41 srmech_gosper op + its ws/out-cap sizers + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc41 lib — the pure-Python ``srmech.amsc.gosper.gosper`` body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _GOSPER_SYMS) and hasattr(
        LIB, "srmech_gosper"
    )


def gosper_c(num_coeffs, den_coeffs):
    """Native Gosper certificate for the term ratio num/den → ``(has_solution,
    r_num_pairs, r_den_pairs)`` (the certificate coefficient lists are reduced
    ``(num, den)`` tuples, ascending degree), or ``None`` if the native symbols
    are absent. ``num_coeffs`` / ``den_coeffs`` are ``(num, den)`` coefficient
    sequences in ascending degree (the term ratio's numerator / denominator)."""
    if not has_native_gosper():
        return None
    n_num, n_den = len(num_coeffs), len(den_coeffs)
    if n_den == 0:
        raise ValueError("gosper_c: the term-ratio denominator must be nonzero")
    deg = max(n_num, n_den)
    # the per-coefficient out cap + the caller arena (sized from the input limbs).
    cl = max(_qmat_coeff_limbs(num_coeffs) if num_coeffs else 1,
             _qmat_coeff_limbs(den_coeffs) if den_coeffs else 1)
    out_cap = int(LIB.srmech_gosper_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(deg)))
    ws_len = int(LIB.srmech_gosper_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(deg)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    num_n, num_d, kn = _qmat_make_array(num_coeffs, out_cap)
    den_n, den_d, kd = _qmat_make_array(den_coeffs, out_cap)
    rn_n, rn_d, krn = _qmat_blank_array(deg + 2, out_cap)
    rd_n, rd_d, krd = _qmat_blank_array(deg + 2, out_cap)
    has = ctypes.c_int(0)
    lrn = ctypes.c_size_t(0)
    lrd = ctypes.c_size_t(0)
    rc = LIB.srmech_gosper(
        num_n, num_d, ctypes.c_size_t(n_num),
        den_n, den_d, ctypes.c_size_t(n_den),
        ctypes.byref(has),
        rn_n, rn_d, ctypes.byref(lrn),
        rd_n, rd_d, ctypes.byref(lrd),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (kn, kd, krn, krd)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_gosper returned non-OK status {rc}")
    if not has.value:
        return False, [], []
    r_num = _qmat_read_array(rn_n, rn_d, lrn.value)
    r_den = _qmat_read_array(rd_n, rd_d, lrd.value)
    return True, r_num, r_den


# ----------------------------------------------------------------------
# rc55: srmech_q_gosper — the q-analog of Gosper (the FIRST public op of the
# q-hypergeometric F929 row). The Python srmech.amsc.q_gosper.q_gosper routes a
# POSITIVE (certificate-found) C result through this; a has=0 / error falls to the
# complete pure-Python path (the parity oracle + full-coverage decider). The two
# QPoly term-ratio operands + the certificate ride the QPoly (x_low, rows) bridge
# form (concatenated ascending-q (num, den) runs + a per-x-cell qlen[] array), the
# SAME flatten/read helpers the rc54 srmech_qpoly_* ops use.
# ----------------------------------------------------------------------

_Q_GOSPER_SYMS = (
    "srmech_q_gosper_ws_bound",
    "srmech_q_gosper_out_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_q_gosper() -> bool:
    """True iff the rc55 srmech_q_gosper op + its ws/out-cap sizers + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc55 lib — the pure-Python ``srmech.amsc.q_gosper.q_gosper`` body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _Q_GOSPER_SYMS) and hasattr(
        LIB, "srmech_q_gosper"
    )


def q_gosper_c(num_form, den_form):
    """Native q-Gosper certificate for the term ratio num/den → ``(has_solution,
    r_num_form, r_den_form)`` (each ``_form`` the QPoly ``(x_low, rows)`` bridge
    form), or ``None`` if the native symbols are absent. ``num_form`` / ``den_form``
    are ``(x_low, rows)`` pairs (each ``rows`` an ascending-x list of ascending-q
    (num, den) q-runs). The native peer completes the constant-ratio (single-x-cell)
    case + declines the rest (``has_solution`` False → the caller re-decides on the
    pure path)."""
    if not has_native_q_gosper():
        return None
    n_lo, n_rows = num_form
    d_lo, d_rows = den_form
    if not d_rows:
        raise ValueError("q_gosper_c: the term-ratio denominator must be nonzero")
    # the per-coefficient out cap + the caller arena (sized from the input q-runs).
    cl = max(_qp_row_coeff_limbs(n_rows), _qp_row_coeff_limbs(d_rows))
    qdeg = 1
    for run in list(n_rows) + list(d_rows):
        qdeg = max(qdeg, len(run))
    out_cap = int(LIB.srmech_q_gosper_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(qdeg)))
    ws_len = int(LIB.srmech_q_gosper_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(qdeg)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    num_n, num_d, num_q, kn = _qp_flatten(n_rows, out_cap)
    den_n, den_d, den_q, kd = _qp_flatten(d_rows, out_cap)
    # the certificate is a single x-cell each (the native constant-ratio scope); size
    # the output q-run capacity generously (the reduced num0 / (num0-den0) q-degree).
    cert_cap = qdeg + 4
    rn_n, rn_d, rn_q, rn_off, krn = _qp_blank_cells([cert_cap], out_cap)
    rd_n, rd_d, rd_q, rd_off, krd = _qp_blank_cells([cert_cap], out_cap)
    has = ctypes.c_int(0)
    rn_cells = ctypes.c_size_t(0)
    rd_cells = ctypes.c_size_t(0)
    rn_xlow = ctypes.c_int64(0)
    rd_xlow = ctypes.c_int64(0)
    rc = LIB.srmech_q_gosper(
        num_n, num_d, num_q, ctypes.c_size_t(len(n_rows)), ctypes.c_int64(int(n_lo)),
        den_n, den_d, den_q, ctypes.c_size_t(len(d_rows)), ctypes.c_int64(int(d_lo)),
        ctypes.byref(has),
        rn_n, rn_d, rn_q, ctypes.byref(rn_cells), ctypes.byref(rn_xlow),
        rd_n, rd_d, rd_q, ctypes.byref(rd_cells), ctypes.byref(rd_xlow),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (kn, kd, krn, krd)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_q_gosper returned non-OK status {rc}")
    if not has.value:
        return False, (0, []), (0, [])
    r_num_rows = _qp_read_row(rn_n, rn_d, rn_q, rn_off, rn_cells.value)
    r_den_rows = _qp_read_row(rd_n, rd_d, rd_q, rd_off, rd_cells.value)
    return True, (rn_xlow.value, r_num_rows), (rd_xlow.value, r_den_rows)


# ----------------------------------------------------------------------
# rc61: srmech_elliptic_gosper — the ELLIPTIC analog of Gosper (the FIRST engine op
# of the ELLIPTIC F929 row). The Python srmech.amsc.elliptic_gosper.elliptic_gosper
# routes a POSITIVE (certificate-found) C result through this AND re-verifies it in
# exact ℚ before trusting it; a has=0 / error falls to the complete pure-Python path
# (the parity oracle + full-coverage decider). The term-ratio EllRatio rides as its
# exact-ℚ prefactor coefficient (pref_num, pref_den) + the prefactor symbol count +
# the numerator / denominator theta-factor counts; the certificate scalar coefficient
# (the constant-ratio native scope) comes back as rn / rd via the bigint decimal
# bridge.
# ----------------------------------------------------------------------

_ELLIPTIC_GOSPER_SYMS = (
    "srmech_elliptic_gosper_ws_bound",
    "srmech_elliptic_gosper_out_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)

# the interned-symbol-table convention MUST match EllRatio._is_elliptic_c: x / p / q are
# force-included even when the canonical form carries none, because the C peel / qshift /
# pshift INTRODUCE q- and p-powers keyed off the x-exponent (without the slots the C
# shifts would be silent no-ops). _X='x', _P='p', _Q_SYM='q' (srmech.amsc.ellbase).
_EG_FORCE_SYMS = ("p", "q", "x")


def has_native_elliptic_gosper() -> bool:
    """True iff the srmech_elliptic_gosper op + its ws/out-cap sizers + the srmech_bigint
    decimal-marshal helpers are loaded + bound. False on a no-C or pre-op lib — the
    pure-Python ``srmech.amsc.elliptic_gosper.elliptic_gosper`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLIPTIC_GOSPER_SYMS) and hasattr(
        LIB, "srmech_elliptic_gosper"
    )


def elliptic_gosper_c(ratio_form):
    """Native GENUINE elliptic-Gosper certificate for the term-ratio EllRatio
    ``ratio_form`` → ``(has_solution, cert_form)`` (``cert_form`` the EllRatio bridge
    form), or ``None`` if the native symbols are absent. ``ratio_form`` is the dict
    :func:`srmech.amsc.elliptic_gosper._ratio_to_form` emits (``prefactor`` =
    ``(coeff_num, coeff_den, [(sym, exp), …])``; ``num`` / ``den`` = theta-argument
    monomial triples). The native peer runs the genuine peel-coboundary + Weierstrass
    key-equation solve + exact ThetaSum.is_zero verify; it declines an input outside the
    structurally-decidable class (``has_solution`` False → the caller re-decides on the
    pure path AND re-verifies any has=1 in exact ℚ)."""
    if not has_native_elliptic_gosper():
        return None
    pref_num, pref_den, pref_exps = ratio_form["prefactor"]
    if pref_den == 0:
        raise ValueError("elliptic_gosper_c: the prefactor coefficient denominator "
                         "must be nonzero")
    num_monos = ratio_form["num"]
    den_monos = ratio_form["den"]
    n_num = len(num_monos)
    n_den = len(den_monos)
    monos = [(pref_num, pref_den, pref_exps)] + list(num_monos) + list(den_monos)
    # the interned symbol universe = every prefactor / theta-arg symbol + the forced x/p/q.
    syms = set(_EG_FORCE_SYMS)
    for _cn, _cd, exps in monos:
        syms.update(s for s, _e in exps)
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)

    def _row(exps):
        r = [0] * n_syms
        for s, e in exps:
            r[idx[s]] = e
        return r

    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad). The working bigint
    # cap (coeff_cap) is modest -- the theta-algebra coefficients stay tiny; the OUTPUT
    # bigint slots use the larger out_cap. ws_bound + the C call get the SAME coeff_cap.
    cl = 2
    for cn, cd, _e in monos:
        cl = max(cl, len(str(cn).lstrip("-")) // 9 + 2, len(str(cd)) // 9 + 2)
    work_cap = cl + 16
    out_cap = int(LIB.srmech_elliptic_gosper_out_cap(ctypes.c_size_t(cl)))
    if out_cap < work_cap:
        out_cap = work_cap
    ws_len = int(LIB.srmech_elliptic_gosper_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_num),
        ctypes.c_size_t(n_den), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # the flat input wire: coeff arrays (in order prefactor, num0..K, den0..L) + exps rows.
    n_mono = len(monos)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (cn, cd, exps) in enumerate(monos):
        bn, kbn = _bigint_from_int(int(cn), work_cap)
        bd, kbd = _bigint_from_int(int(cd), work_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        exps_flat.extend(_row(exps))
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    # the output buffers: the cert prefactor coeff + a generous flat exps row buffer.
    out_cap_rows = 1 + 2 * (n_num + n_den) + 32
    out_pn, _opnl = _bigint_from_int(0, out_cap)
    out_pd, _opdl = _bigint_from_int(0, out_cap)
    out_exps = (ctypes.c_int32 * max(out_cap_rows * n_syms, 1))()
    out_nn = ctypes.c_size_t(0)
    out_nd = ctypes.c_size_t(0)
    has = ctypes.c_int(0)
    rc = LIB.srmech_elliptic_gosper(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(idx.get("x", -1)), ctypes.c_int(idx.get("p", -1)),
        ctypes.c_int(idx.get("q", -1)),
        ctypes.c_size_t(n_num), ctypes.c_size_t(n_den),
        num_arr, den_arr, exps_c, ctypes.c_uint32(work_cap),
        ctypes.byref(has),
        ctypes.byref(out_pn), ctypes.byref(out_pd),
        out_exps, ctypes.c_size_t(out_cap_rows),
        ctypes.byref(out_nn), ctypes.byref(out_nd),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_elliptic_gosper returned non-OK status {rc}")
    if not has.value:
        return False, None
    # rebuild the certificate EllRatio bridge form from the flat output rows.
    cnn = out_nn.value
    cnd = out_nd.value

    def _exps_from_row(row):
        return [(sym_list[j], int(row[j])) for j in range(n_syms) if row[j] != 0]

    rows = [out_exps[r * n_syms:(r + 1) * n_syms] for r in range(1 + cnn + cnd)]
    cert_form = {
        "prefactor": (_bigint_to_int(out_pn), _bigint_to_int(out_pd),
                      _exps_from_row(rows[0])),
        "num": [(1, 1, _exps_from_row(rows[1 + i])) for i in range(cnn)],
        "den": [(1, 1, _exps_from_row(rows[1 + cnn + i])) for i in range(cnd)],
    }
    return True, cert_form


# ----------------------------------------------------------------------
# rc68: srmech_elliptic_recurrence_8w7 — the C peer of the ELLIPTIC Σ-row ORDER-1
# RECURRENCE op srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7 for the
# Frenkel–Turaev ₈ω₇ summation. The term-ratio EllRatio marshals over the same wire
# convention as elliptic_gosper (the interned symbol table + the x/p/q/y indices + the
# num/den theta counts + the flat coeff arrays + the flat exps rows), with the recurrence
# coefficient ρ EllRatio coming back as a prefactor coeff + the canonical theta exps rows.
# The native peer constructs the EXACT ρ; the Python dispatch trusts it ONLY after a
# byte-for-byte rebuild + the ₈ω₇ verification gate. A has=0 -> Python pure path.
# ----------------------------------------------------------------------

_ELLIPTIC_RECURRENCE_SYMS = (
    "srmech_elliptic_recurrence_8w7_ws_bound",
    "srmech_elliptic_recurrence_8w7_out_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)

# the symbols forced into the interned table even when the canonical form carries none:
# x (the summation axis), p (the nome the theta-canon writes), q (the base; aq = a·q is
# load-bearing in the decompose), and y (the recurrence axis the free-param filter reads).
_ER8W7_FORCE_SYMS = ("p", "q", "x", "y")


def has_native_elliptic_recurrence_8w7() -> bool:
    """True iff the rc68 srmech_elliptic_recurrence_8w7 op + its ws/out-cap sizers + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or pre-rc68
    lib — the pure-Python
    ``srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLIPTIC_RECURRENCE_SYMS) and hasattr(
        LIB, "srmech_elliptic_recurrence_8w7"
    )


def elliptic_recurrence_8w7_c(ratio_form):
    """Native ₈ω₇ order-1 recurrence coefficient ρ for the term-ratio EllRatio
    ``ratio_form`` → ``(has_recurrence, rho_form)`` (``rho_form`` the EllRatio bridge
    form), or ``None`` if the native symbols are absent. ``ratio_form`` is the dict
    :func:`srmech.amsc.elliptic_recurrence._ratio_to_form` emits (``prefactor`` =
    ``(coeff_num, coeff_den, [(sym, exp), …])``; ``num`` / ``den`` = theta-argument
    monomial triples). The native peer runs the genuine recognize-decompose-construct
    pipeline; it declines an input that is NOT a canonical ₈ω₇ (``has_recurrence`` False →
    the caller re-decides on the pure path)."""
    if not has_native_elliptic_recurrence_8w7():
        return None
    pref_num, pref_den, pref_exps = ratio_form["prefactor"]
    if pref_den == 0:
        raise ValueError("elliptic_recurrence_8w7_c: the prefactor coefficient "
                         "denominator must be nonzero")
    num_monos = ratio_form["num"]
    den_monos = ratio_form["den"]
    n_num = len(num_monos)
    n_den = len(den_monos)
    monos = [(pref_num, pref_den, pref_exps)] + list(num_monos) + list(den_monos)
    # the interned symbol universe = every prefactor / theta-arg symbol + the forced x/p/q/y.
    syms = set(_ER8W7_FORCE_SYMS)
    for _cn, _cd, exps in monos:
        syms.update(s for s, _e in exps)
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)

    def _row(exps):
        r = [0] * n_syms
        for s, e in exps:
            r[idx[s]] = e
        return r

    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad).
    cl = 2
    for cn, cd, _e in monos:
        cl = max(cl, len(str(cn).lstrip("-")) // 9 + 2, len(str(cd)) // 9 + 2)
    work_cap = cl + 16
    out_cap = int(LIB.srmech_elliptic_recurrence_8w7_out_cap(ctypes.c_size_t(cl)))
    if out_cap < work_cap:
        out_cap = work_cap
    ws_len = int(LIB.srmech_elliptic_recurrence_8w7_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_num),
        ctypes.c_size_t(n_den), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # the flat input wire: coeff arrays (in order prefactor, num0..K, den0..L) + exps rows.
    n_mono = len(monos)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (cn, cd, exps) in enumerate(monos):
        bn, kbn = _bigint_from_int(int(cn), work_cap)
        bd, kbd = _bigint_from_int(int(cd), work_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        exps_flat.extend(_row(exps))
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    # the output buffers: the ρ prefactor coeff + a generous flat exps row buffer (ρ has
    # 4 num + 4 den thetas + 1 prefactor row; budget generously for cancellation slack).
    out_cap_rows = 1 + 2 * (n_num + n_den) + 32
    out_pn, _opnl = _bigint_from_int(0, out_cap)
    out_pd, _opdl = _bigint_from_int(0, out_cap)
    out_exps = (ctypes.c_int32 * max(out_cap_rows * n_syms, 1))()
    out_nn = ctypes.c_size_t(0)
    out_nd = ctypes.c_size_t(0)
    has = ctypes.c_int(0)
    rc = LIB.srmech_elliptic_recurrence_8w7(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(idx.get("x", -1)), ctypes.c_int(idx.get("p", -1)),
        ctypes.c_int(idx.get("q", -1)), ctypes.c_int(idx.get("y", -1)),
        ctypes.c_size_t(n_num), ctypes.c_size_t(n_den),
        num_arr, den_arr, exps_c, ctypes.c_uint32(work_cap),
        ctypes.byref(has),
        ctypes.byref(out_pn), ctypes.byref(out_pd),
        out_exps, ctypes.c_size_t(out_cap_rows),
        ctypes.byref(out_nn), ctypes.byref(out_nd),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_elliptic_recurrence_8w7 returned non-OK status {rc}")
    if not has.value:
        return False, None
    # rebuild the ρ EllRatio bridge form from the flat output rows.
    cnn = out_nn.value
    cnd = out_nd.value

    def _exps_from_row(row):
        return [(sym_list[j], int(row[j])) for j in range(n_syms) if row[j] != 0]

    rows = [out_exps[r * n_syms:(r + 1) * n_syms] for r in range(1 + cnn + cnd)]
    rho_form = {
        "prefactor": (_bigint_to_int(out_pn), _bigint_to_int(out_pd),
                      _exps_from_row(rows[0])),
        "num": [(1, 1, _exps_from_row(rows[1 + i])) for i in range(cnn)],
        "den": [(1, 1, _exps_from_row(rows[1 + cnn + i])) for i in range(cnd)],
    }
    return True, rho_form


# ----------------------------------------------------------------------
# rc90: srmech_elliptic_zeilberger — the C peer of the ELLIPTIC Σ-row CREATIVE-
# TELESCOPING op srmech.amsc.elliptic_zeilberger.elliptic_zeilberger for the Frenkel–
# Turaev ₈ω₇ summation. The term-ratio marshals over the same wire convention as
# elliptic_recurrence_8w7 (the interned symbol table + the x/p/q/y indices + the num/den
# theta counts + the flat coeff arrays + the flat exps rows) PLUS the two extra interned
# indices for the certificate's recurrence index symbols N = qⁿ, K = qᵏ (force-interned
# here). The native peer recognizes + decomposes the ₈ω₇, builds the connection-
# coefficient split certificate, and decides it ≡ 0 via the shared srmech_thetasum_is_zero
# kernel; only the verdict (has) comes back. The Python dispatch trusts a has=1 ONLY after
# the pure path agrees AND the certificate re-decides ≡ 0 in exact ℚ. A has=0 / error ->
# Python pure path. NEW symbols -> hasattr-guarded; ABI stays 3.
# ----------------------------------------------------------------------

_ELLIPTIC_ZEILBERGER_SYMS = (
    "srmech_elliptic_zeilberger_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)

# the symbols forced into the interned table even when the canonical form carries none:
# x (the summation axis), p (the nome the theta-canon writes), q (the base; aq = a·q is
# load-bearing in the decompose), y (the recurrence axis the free-param filter reads), and
# N = qⁿ / K = qᵏ (the connection-coefficient certificate's own recurrence index symbols).
_EZ_FORCE_SYMS = ("K", "N", "p", "q", "x", "y")


def has_native_elliptic_zeilberger() -> bool:
    """True iff the rc90 srmech_elliptic_zeilberger op + its ws sizer + the srmech_bigint
    decimal-marshal helpers are loaded + bound. False on a no-C or pre-rc90 lib — the
    pure-Python ``srmech.amsc.elliptic_zeilberger.elliptic_zeilberger`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLIPTIC_ZEILBERGER_SYMS) and hasattr(
        LIB, "srmech_elliptic_zeilberger"
    )


def elliptic_zeilberger_c(ratio_form):
    """Native ₈ω₇ CREATIVE-TELESCOPING verdict for the term-ratio EllRatio ``ratio_form``
    → ``(has, None)`` (``has`` True iff the native peer recognizes the ₈ω₇ AND the
    connection-coefficient certificate decides ≡ 0), or ``None`` if the native symbols are
    absent. ``ratio_form`` is the dict :func:`srmech.amsc.elliptic_recurrence._ratio_to_form`
    emits (``prefactor`` = ``(coeff_num, coeff_den, [(sym, exp), …])``; ``num`` / ``den`` =
    theta-argument monomial triples). The peer builds the certificate (the cleared ±-pair
    split) over the additive theta carrier and routes the decision to srmech_thetasum_is_zero;
    it does NOT emit ρ (the caller builds ρ + re-verifies the certificate in exact ℚ before
    trusting a ``has`` True)."""
    if not has_native_elliptic_zeilberger():
        return None
    pref_num, pref_den, pref_exps = ratio_form["prefactor"]
    if pref_den == 0:
        raise ValueError("elliptic_zeilberger_c: the prefactor coefficient "
                         "denominator must be nonzero")
    num_monos = ratio_form["num"]
    den_monos = ratio_form["den"]
    n_num = len(num_monos)
    n_den = len(den_monos)
    monos = [(pref_num, pref_den, pref_exps)] + list(num_monos) + list(den_monos)
    # the interned symbol universe = every prefactor / theta-arg symbol + the forced
    # x/p/q/y AND the certificate's own N = qⁿ, K = qᵏ.
    syms = set(_EZ_FORCE_SYMS)
    for _cn, _cd, exps in monos:
        syms.update(s for s, _e in exps)
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)

    def _row(exps):
        r = [0] * n_syms
        for s, e in exps:
            r[idx[s]] = e
        return r

    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad).
    cl = 2
    for cn, cd, _e in monos:
        cl = max(cl, len(str(cn).lstrip("-")) // 9 + 2, len(str(cd)) // 9 + 2)
    work_cap = cl + 16
    ws_len = int(LIB.srmech_elliptic_zeilberger_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_num),
        ctypes.c_size_t(n_den), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # the flat input wire: coeff arrays (in order prefactor, num0..K, den0..L) + exps rows.
    n_mono = len(monos)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (cn, cd, exps) in enumerate(monos):
        bn, kbn = _bigint_from_int(int(cn), work_cap)
        bd, kbd = _bigint_from_int(int(cd), work_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        exps_flat.extend(_row(exps))
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    has = ctypes.c_int(0)
    rc = LIB.srmech_elliptic_zeilberger(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(idx.get("x", -1)), ctypes.c_int(idx.get("p", -1)),
        ctypes.c_int(idx.get("q", -1)), ctypes.c_int(idx.get("y", -1)),
        ctypes.c_int(idx.get("N", -1)), ctypes.c_int(idx.get("K", -1)),
        ctypes.c_size_t(n_num), ctypes.c_size_t(n_den),
        num_arr, den_arr, exps_c, ctypes.c_uint32(work_cap),
        ctypes.byref(has),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_elliptic_zeilberger returned non-OK status {rc}")
    return bool(has.value), None


# ----------------------------------------------------------------------
# rc91: srmech_elliptic_wz_certificate — the C peer of the ELLIPTIC Σ-row IDENTITY-PROOF
# op srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate for the Frenkel–Turaev
# ₈ω₇ SUMMATION. IDENTICAL marshalling to elliptic_zeilberger (the full EllRatio wire +
# the certificate's recurrence index symbols N = qⁿ, K = qᵏ); the summation proof reduces
# to the SAME connection-coefficient split certificate decided via srmech_thetasum_is_zero,
# so only the verdict (has) comes back. The Python dispatch builds the closed-form
# endpoints {aq,aq/bc,aq/bd,aq/cd}/{aq/b,aq/c,aq/d,aq/bcd} on its side and trusts a has=1
# ONLY after the pure path agrees AND the certificate re-decides ≡ 0 in exact ℚ. A has=0 /
# error -> Python pure path. NEW symbols -> hasattr-guarded; ABI stays 3.
# ----------------------------------------------------------------------

_ELLIPTIC_WZ_CERTIFICATE_SYMS = (
    "srmech_elliptic_wz_certificate_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)

# the symbols forced into the interned table even when the canonical form carries none:
# x (the summation axis), p (the nome the theta-canon writes), q (the base; aq = a·q is
# load-bearing in the decompose), y (the recurrence axis the free-param filter reads), and
# N = qⁿ / K = qᵏ (the connection-coefficient certificate's own recurrence index symbols).
_EWZ_FORCE_SYMS = ("K", "N", "p", "q", "x", "y")


def has_native_elliptic_wz_certificate() -> bool:
    """True iff the rc91 srmech_elliptic_wz_certificate op + its ws sizer + the srmech_bigint
    decimal-marshal helpers are loaded + bound. False on a no-C or pre-rc91 lib — the
    pure-Python ``srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate`` body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLIPTIC_WZ_CERTIFICATE_SYMS) and hasattr(
        LIB, "srmech_elliptic_wz_certificate"
    )


def elliptic_wz_certificate_c(ratio_form):
    """Native ₈ω₇ SUMMATION-identity verdict for the term-ratio EllRatio ``ratio_form``
    → ``(has, None)`` (``has`` True iff the native peer recognizes the ₈ω₇ AND the
    connection-coefficient certificate decides ≡ 0), or ``None`` if the native symbols are
    absent. ``ratio_form`` is the dict :func:`srmech.amsc.elliptic_recurrence._ratio_to_form`
    emits (``prefactor`` = ``(coeff_num, coeff_den, [(sym, exp), …])``; ``num`` / ``den`` =
    theta-argument monomial triples). The peer builds the certificate (the cleared ±-pair
    split) over the additive theta carrier and routes the decision to srmech_thetasum_is_zero;
    it does NOT emit the closed form (the caller builds the Pochhammer endpoints + re-verifies
    the certificate in exact ℚ before trusting a ``has`` True)."""
    if not has_native_elliptic_wz_certificate():
        return None
    pref_num, pref_den, pref_exps = ratio_form["prefactor"]
    if pref_den == 0:
        raise ValueError("elliptic_wz_certificate_c: the prefactor coefficient "
                         "denominator must be nonzero")
    num_monos = ratio_form["num"]
    den_monos = ratio_form["den"]
    n_num = len(num_monos)
    n_den = len(den_monos)
    monos = [(pref_num, pref_den, pref_exps)] + list(num_monos) + list(den_monos)
    # the interned symbol universe = every prefactor / theta-arg symbol + the forced
    # x/p/q/y AND the certificate's own N = qⁿ, K = qᵏ.
    syms = set(_EWZ_FORCE_SYMS)
    for _cn, _cd, exps in monos:
        syms.update(s for s, _e in exps)
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)

    def _row(exps):
        r = [0] * n_syms
        for s, e in exps:
            r[idx[s]] = e
        return r

    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad).
    cl = 2
    for cn, cd, _e in monos:
        cl = max(cl, len(str(cn).lstrip("-")) // 9 + 2, len(str(cd)) // 9 + 2)
    work_cap = cl + 16
    ws_len = int(LIB.srmech_elliptic_wz_certificate_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_num),
        ctypes.c_size_t(n_den), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # the flat input wire: coeff arrays (in order prefactor, num0..K, den0..L) + exps rows.
    n_mono = len(monos)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (cn, cd, exps) in enumerate(monos):
        bn, kbn = _bigint_from_int(int(cn), work_cap)
        bd, kbd = _bigint_from_int(int(cd), work_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        exps_flat.extend(_row(exps))
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    has = ctypes.c_int(0)
    rc = LIB.srmech_elliptic_wz_certificate(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(idx.get("x", -1)), ctypes.c_int(idx.get("p", -1)),
        ctypes.c_int(idx.get("q", -1)), ctypes.c_int(idx.get("y", -1)),
        ctypes.c_int(idx.get("N", -1)), ctypes.c_int(idx.get("K", -1)),
        ctypes.c_size_t(n_num), ctypes.c_size_t(n_den),
        num_arr, den_arr, exps_c, ctypes.c_uint32(work_cap),
        ctypes.byref(has),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_elliptic_wz_certificate returned non-OK status {rc}")
    return bool(has.value), None


# ----------------------------------------------------------------------
# rc69: srmech_carrier_spectrum — the OPERAND-side dual of the_one. The carrier element
# rides as the SAME full EllRatio wire form srmech_elliptic_recurrence_8w7 parses; the
# native peer returns the channel READ (the cyclic σ-eigenspectrum x-exponents + the
# per-theta q-stripped block-label rows). The Python rebuilds the cyclic dict + groups
# the thetas by block, trusting the native result ONLY after the pure rebuild reproduces
# the SAME spectrum byte-for-byte. A has=0 (p absent / over scope) -> Python pure path.
# ----------------------------------------------------------------------

_CARRIER_SPECTRUM_SYMS = ("srmech_carrier_spectrum_ws_bound",)
# x (the cyclic axis read), p (the nome the theta-canon writes), q (stripped for the
# σ-invariant block label), y (the second period direction) are forced into the table.
_CS_FORCE_SYMS = ("p", "q", "x", "y")


def has_native_carrier_spectrum() -> bool:
    """True iff the rc69 srmech_carrier_spectrum op + its ws sizer are loaded + bound.
    False on a no-C or pre-rc69 lib — the pure-Python
    ``srmech.amsc.carrier_spectrum.CarrierSpectrum`` channel read is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _CARRIER_SPECTRUM_SYMS) and hasattr(
        LIB, "srmech_carrier_spectrum"
    )


def carrier_spectrum_c(ratio_form):
    """Native channel read of the carrier element ``ratio_form`` →
    ``(cyclic, blocks)`` or ``None`` if the native symbols are absent. ``ratio_form`` is
    the dict :func:`srmech.amsc.carrier_spectrum._ratio_to_form` emits (``prefactor`` =
    ``(coeff_num, coeff_den, [(sym, exp), …])``; ``num`` / ``den`` = theta-argument
    monomial triples). ``cyclic`` = ``{x-exponent k: 'q**k'}`` (the σ-eigenspectrum);
    ``blocks`` = ``{block-label tuple: [[theta-arg exponent dict], …]}`` (the σ-invariant
    p-character partition). The Python caller re-verifies against its pure read."""
    if not has_native_carrier_spectrum():
        return None
    pref_num, pref_den, pref_exps = ratio_form["prefactor"]
    if pref_den == 0:
        raise ValueError("carrier_spectrum_c: the prefactor coefficient denominator "
                         "must be nonzero")
    num_monos = ratio_form["num"]
    den_monos = ratio_form["den"]
    n_num = len(num_monos)
    n_den = len(den_monos)
    monos = [(pref_num, pref_den, pref_exps)] + list(num_monos) + list(den_monos)
    syms = set(_CS_FORCE_SYMS)
    for _cn, _cd, exps in monos:
        syms.update(s for s, _e in exps)
    sym_list = sorted(syms)
    idx = {s: i for i, s in enumerate(sym_list)}
    n_syms = len(sym_list)

    def _row(exps):
        r = [0] * n_syms
        for s, e in exps:
            r[idx[s]] = e
        return r

    cl = 2
    for cn, cd, _e in monos:
        cl = max(cl, len(str(cn).lstrip("-")) // 9 + 2, len(str(cd)) // 9 + 2)
    work_cap = cl + 16
    ws_len = int(LIB.srmech_carrier_spectrum_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_num),
        ctypes.c_size_t(n_den), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    n_mono = len(monos)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (cn, cd, exps) in enumerate(monos):
        bn, kbn = _bigint_from_int(int(cn), work_cap)
        bd, kbd = _bigint_from_int(int(cd), work_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        exps_flat.extend(_row(exps))
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    n_thetas_total = n_num + n_den
    cyclic_cap = n_syms + n_thetas_total + 8
    block_cap_rows = n_thetas_total + 1
    out_cyclic = (ctypes.c_int32 * max(cyclic_cap, 1))()
    out_block = (ctypes.c_int32 * max(block_cap_rows * n_syms, 1))()
    out_n_cyclic = ctypes.c_size_t(0)
    out_n_thetas = ctypes.c_size_t(0)
    has = ctypes.c_int(0)
    rc = LIB.srmech_carrier_spectrum(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(idx.get("x", -1)), ctypes.c_int(idx.get("p", -1)),
        ctypes.c_int(idx.get("q", -1)), ctypes.c_int(idx.get("y", -1)),
        ctypes.c_size_t(n_num), ctypes.c_size_t(n_den),
        num_arr, den_arr, exps_c, ctypes.c_uint32(work_cap),
        ctypes.byref(has),
        out_cyclic, ctypes.c_size_t(cyclic_cap), ctypes.byref(out_n_cyclic),
        out_block, ctypes.c_size_t(block_cap_rows), ctypes.byref(out_n_thetas),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_carrier_spectrum returned non-OK status {rc}")
    if not has.value:
        return None
    ncy = out_n_cyclic.value
    cyclic = {int(out_cyclic[i]): f"q**{int(out_cyclic[i])}" for i in range(ncy)}
    # group the per-theta block rows by their (q-stripped) block label.
    nth = out_n_thetas.value
    blocks = {}
    for r in range(nth):
        row = out_block[r * n_syms:(r + 1) * n_syms]
        label = tuple(sorted((sym_list[j], int(row[j]))
                             for j in range(n_syms) if int(row[j]) != 0))
        # the theta argument exponent map (the original, NOT the block label) — the input
        # mono for this theta (num then den, in the input order).
        cn, cd, exps = monos[1 + r]
        arg_map = {s: e for s, e in exps}
        blocks.setdefault(label, []).append([arg_map])
    return cyclic, blocks


# ----------------------------------------------------------------------
# rc63: srmech_thetasum_is_zero — the C peer of the ThetaSum carrier's is_zero (the
# load-bearing EXACT Weierstrass three-term + quasi-periodicity decision). The Python
# srmech.amsc.thetasum.ThetaSum.is_zero marshals its cleared numerator terms (each a
# prefactor EllMonomial + a tuple of canonical Theta) over an interned symbol table
# and routes the DECISION through this; the pure-Python body is the COMPLETE
# alternative + the parity oracle. The C verdict EQUALS the Python verdict byte-for-
# byte (a 1:1 structural mirror), so the dispatch trusts it unconditionally when the
# native symbols are present.
# ----------------------------------------------------------------------

_THETASUM_SYMS = (
    "srmech_thetasum_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_thetasum() -> bool:
    """True iff the rc63 srmech_thetasum_is_zero op + its ws sizer + the srmech_bigint
    decimal-marshal helpers are loaded + bound. False on a no-C or pre-rc63 lib — the
    pure-Python ``srmech.amsc.thetasum.ThetaSum.is_zero`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _THETASUM_SYMS) and hasattr(
        LIB, "srmech_thetasum_is_zero"
    )


def thetasum_is_zero_c(n_syms, xsym, ysym, psym, term_nthetas, monomials):
    """Native ThetaSum.is_zero decision for the cleared numerator terms → ``bool`` (the
    C verdict), or ``None`` if the native symbols are absent. ``n_syms`` is the interned
    symbol-table dimension; ``xsym`` / ``ysym`` / ``psym`` the interned indices of
    ``x`` / ``y`` / ``p`` (-1 if absent); ``term_nthetas[i]`` the theta count of term i;
    ``monomials`` the flat list of ``(num, den, exps_row)`` triples in the order
    term0.pref, term0.theta0..K, term1.pref, … (each ``exps_row`` a length-``n_syms``
    int list). An empty numerator (no terms) is zero by definition (handled by the
    caller). A non-OK C status raises ``RuntimeError``."""
    if not has_native_thetasum():
        return None
    n_terms = len(term_nthetas)
    if n_terms == 0:
        return True
    max_thetas = max(term_nthetas) if term_nthetas else 0
    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad).
    cl = 1
    for num, den, _exps in monomials:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    # Headroom for INTERMEDIATE coefficient growth during the Weierstrass three-term
    # reduction: the rewrite + the canonical-pair inversion prefactors MULTIPLY the input
    # coefficients, so the working bigints outgrow the input's limb count. Without this
    # the arena tripped SRMECH_ERR_OVERFLOW on large / multivariate cleared certificates
    # (the C peer then falls back to the exact pure-Python path — this bump lets the
    # native fast path handle them instead). Scale by the theta count (each pairing can
    # compound a coefficient) with a constant floor; over-provisioning only costs arena.
    cl = cl * (max_thetas + 4) + 8
    out_cap = cl
    ws_len = int(LIB.srmech_thetasum_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_terms),
        ctypes.c_size_t(max_thetas), ctypes.c_size_t(cl)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # flat coeff arrays + the flat int32 exponent rows.
    n_mono = len(monomials)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (num, den, exps_row) in enumerate(monomials):
        bn, kbn = _bigint_from_int(int(num), out_cap)
        bd, kbd = _bigint_from_int(int(den), out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        if len(exps_row) != n_syms:
            raise ValueError("thetasum_is_zero_c: exps row length != n_syms")
        exps_flat.extend(int(e) for e in exps_row)
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    nthetas_c = (ctypes.c_size_t * n_terms)(*[int(t) for t in term_nthetas])
    out_is_zero = ctypes.c_int(0)
    rc = LIB.srmech_thetasum_is_zero(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(xsym), ctypes.c_int(ysym), ctypes.c_int(psym),
        ctypes.c_size_t(n_terms), nthetas_c,
        num_arr, den_arr, exps_c,
        ctypes.c_uint32(out_cap), ctypes.byref(out_is_zero),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_thetasum_is_zero returned non-OK status {rc}")
    return bool(out_is_zero.value)


# ----------------------------------------------------------------------
# rc99: srmech_thetasum_is_zero_interpolation — the C peer of the ThetaSum
# STRUCTURAL ELLIPTIC-INTERPOLATION is_zero completion (the COMPLETE multi-variable
# elliptic decision). srmech.amsc.thetasum.ThetaSum._is_zero_interpolation is the
# pure-Python parity oracle; the C verdict EQUALS it byte-for-byte (True AND False),
# so the dispatched is_zero trusts a non-None C verdict directly. When the caller
# arena / coefficient cap is outgrown the C peer returns SRMECH_ERR_OVERFLOW; the
# Python marshaler catches it and returns None -> the caller falls to the pure
# oracle (the C peer is the accelerator, the pure path the authority).
# ----------------------------------------------------------------------

_THETASUM_INTERP_SYMS = (
    "srmech_thetasum_is_zero_interpolation_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_thetasum_interpolation() -> bool:
    """True iff the rc99 srmech_thetasum_is_zero_interpolation op + its ws sizer +
    the srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc99 lib — the pure-Python ``ThetaSum._is_zero_interpolation`` body is then
    the complete decider (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _THETASUM_INTERP_SYMS) and hasattr(
        LIB, "srmech_thetasum_is_zero_interpolation"
    )


def thetasum_is_zero_interpolation_c(n_syms, xsym, ysym, psym, term_nthetas, monomials):
    """Native COMPLETE structural-interpolation ThetaSum.is_zero decision → ``bool``
    (trusted True AND False), or ``None`` if the native symbols are absent OR the C
    peer declined (SRMECH_ERR_OVERFLOW — the caller then falls to the pure oracle).
    ``monomials`` is the flat ``(num, den, exps_row)`` list in the order term0.pref,
    term0.theta0..K, term1.pref, … (identical to :func:`thetasum_is_zero_c`)."""
    if not has_native_thetasum_interpolation():
        return None
    n_terms = len(term_nthetas)
    if n_terms == 0:
        return True
    max_thetas = max(term_nthetas) if term_nthetas else 0
    # per-coefficient limb estimate + the largest |exponent| (max_abs_exp bounds the
    # w-band span + prefactor offset).
    cl = 1
    max_abs_exp = 1
    for num, den, exps in monomials:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
        for e in exps:
            ae = int(e)
            ae = ae if ae >= 0 else -ae
            if ae > max_abs_exp:
                max_abs_exp = ae
    # rc102: the TRUE base-case p-order band degree the C base case (ti_one_var) uses:
    # ti_deg = max over terms of (max over variables of SUM over that term's THETA args
    # of exp^2). A leaf with >=2 same-variable thetas has SUM(e^2) >> max(e^2), so the
    # pre-rc102 max_abs_exp^2 UNDER-sized k -> OVERFLOW false-decline. Walk the flat
    # monomial list by term (layout: term.pref, term.theta0..K-1, next term, ...),
    # skipping the prefactor (ti_deg sums THETA args only, never the prefactor).
    max_theta_sq_sum = 0
    _mi = 0
    for _nt in term_nthetas:
        _mi += 1  # skip the term's prefactor monomial
        _per_var = [0] * n_syms
        for _ti in range(_nt):
            _exps_row = monomials[_mi][2]
            for _vi, _e in enumerate(_exps_row):
                _ie = int(_e)
                _per_var[_vi] += _ie * _ie
            _mi += 1
        if _per_var:
            _m = max(_per_var)
            if _m > max_theta_sq_sum:
                max_theta_sq_sum = _m
    # Headroom for INTERMEDIATE coefficient growth: the base-case q-expansion raises
    # the substituted (prime-product) coefficients to powers and multiplies theta
    # factors, so the working bigints outgrow the input's limb count. Scale generously
    # (over-provisioning only costs arena; a genuine shortfall trips OVERFLOW -> the
    # pure oracle decides). Distinct primes climb to 617 -> ~2 limbs each.
    cl = cl * (max_thetas + 4) * (max_abs_exp + 2) + 16
    out_cap = cl
    _ws2 = getattr(LIB, "srmech_thetasum_is_zero_interpolation_ws_bound2", None)
    if _ws2 is not None:
        # rc102 degree-aware sizer (k from the TRUE ti_deg = max_theta_sq_sum).
        ws_len = int(_ws2(
            ctypes.c_size_t(n_syms), ctypes.c_size_t(n_terms),
            ctypes.c_size_t(max_thetas), ctypes.c_size_t(cl),
            ctypes.c_size_t(max_abs_exp), ctypes.c_size_t(max_theta_sq_sum)))
    else:
        # stale ABI-3 lib without the rc102 symbol: the legacy sizer (max_abs_exp^2).
        ws_len = int(LIB.srmech_thetasum_is_zero_interpolation_ws_bound(
            ctypes.c_size_t(n_syms), ctypes.c_size_t(n_terms),
            ctypes.c_size_t(max_thetas), ctypes.c_size_t(cl),
            ctypes.c_size_t(max_abs_exp)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    n_mono = len(monomials)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (num, den, exps_row) in enumerate(monomials):
        bn, kbn = _bigint_from_int(int(num), out_cap)
        bd, kbd = _bigint_from_int(int(den), out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        if len(exps_row) != n_syms:
            raise ValueError("thetasum_is_zero_interpolation_c: exps row length != n_syms")
        exps_flat.extend(int(e) for e in exps_row)
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    nthetas_c = (ctypes.c_size_t * n_terms)(*[int(t) for t in term_nthetas])
    out_is_zero = ctypes.c_int(0)
    rc = LIB.srmech_thetasum_is_zero_interpolation(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(xsym), ctypes.c_int(ysym), ctypes.c_int(psym),
        ctypes.c_size_t(n_terms), nthetas_c,
        num_arr, den_arr, exps_c,
        ctypes.c_uint32(out_cap), ctypes.byref(out_is_zero),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc == SRMECH_ERR_OVERFLOW:
        # The peer outgrew the provisioned arena / coeff cap — decline to the pure
        # oracle rather than crash (a TOTAL-function dispatch, like thetasum_is_zero_c).
        return None
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_thetasum_is_zero_interpolation returned non-OK status {rc}")
    return bool(out_is_zero.value)


# ----------------------------------------------------------------------
# rc64: srmech_ellratio_is_elliptic — the C peer of the EllRatio carrier's
# is_elliptic (the BALANCING / very-well-poised predicate = pshift() == self).
# srmech.amsc.ellbase.EllRatio.is_elliptic dispatches a positive result through
# here; an absent peer falls to the complete pure-Python body (the parity oracle).
# Shares the srmech_bigint decimal-marshal helpers with the thetasum peer.
# ----------------------------------------------------------------------

_ELLRATIO_SYMS = (
    "srmech_ellratio_ws_bound",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_ellratio() -> bool:
    """True iff the rc64 srmech_ellratio_is_elliptic op + its ws sizer + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc64 lib — the pure-Python ``srmech.amsc.ellbase.EllRatio.is_elliptic`` body
    is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLRATIO_SYMS) and hasattr(
        LIB, "srmech_ellratio_is_elliptic"
    )


def ellratio_is_elliptic_c(n_syms, xsym, psym, n_num, n_den, monomials):
    """Native EllRatio.is_elliptic decision for a CANONICAL ratio → ``bool`` (the C
    verdict), or ``None`` if the native symbols are absent. ``n_syms`` is the interned
    symbol-table dimension; ``xsym`` / ``psym`` the interned indices of ``x`` / ``p``
    (-1 if absent); ``n_num`` / ``n_den`` the numerator / denominator theta counts;
    ``monomials`` the flat list of ``(num, den, exps_row)`` triples in the order
    prefactor, num0..K-1, den0..L-1 (each ``exps_row`` a length-``n_syms`` int list).
    A non-OK C status raises ``RuntimeError``."""
    if not has_native_ellratio():
        return None
    # A pure-scalar ratio (no symbols) clamps to a single all-zero exponent slot so the
    # C (which clamps n_syms -> 1) reads a consistent dense row per monomial.
    if n_syms == 0:
        n_syms = 1
        monomials = [(num, den, [0]) for num, den, _e in monomials]
    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad).
    cl = 1
    for num, den, _exps in monomials:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    out_cap = cl
    ws_len = int(LIB.srmech_ellratio_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n_num),
        ctypes.c_size_t(n_den), ctypes.c_size_t(cl)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    n_mono = len(monomials)
    num_arr = (_SrmechBigint * max(n_mono, 1))()
    den_arr = (_SrmechBigint * max(n_mono, 1))()
    keep = []
    exps_flat = []
    for i, (num, den, exps_row) in enumerate(monomials):
        bn, kbn = _bigint_from_int(int(num), out_cap)
        bd, kbd = _bigint_from_int(int(den), out_cap)
        num_arr[i] = bn
        den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        if len(exps_row) != n_syms:
            raise ValueError("ellratio_is_elliptic_c: exps row length != n_syms")
        exps_flat.extend(int(e) for e in exps_row)
    exps_c = (ctypes.c_int32 * max(len(exps_flat), 1))(*exps_flat)
    out_is_elliptic = ctypes.c_int(0)
    rc = LIB.srmech_ellratio_is_elliptic(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(xsym), ctypes.c_int(psym),
        ctypes.c_size_t(n_num), ctypes.c_size_t(n_den),
        num_arr, den_arr, exps_c,
        ctypes.c_uint32(out_cap), ctypes.byref(out_is_elliptic),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_ellratio_is_elliptic returned non-OK status {rc}")
    return bool(out_is_elliptic.value)


# ----------------------------------------------------------------------
# rc67: srmech_elliptic_lagrange_basis — the C peer of the EllRatio-carrier op
# srmech.amsc.ellbase.elliptic_lagrange_basis (rc66, shipped Python-only; its C
# mirror is owed by the everything-mirrors same-rc discipline). A C-MIRROR PARITY
# build: the k basis EllRatios come back byte-exact equal to the pure-Python op.
# srmech.amsc.ellbase.elliptic_lagrange_basis dispatches through here when the peer
# is loaded; the pure-Python body is the complete alternative + the parity oracle.
# Shares the srmech_bigint decimal-marshal helpers (in _ELLRATIO_SYMS) with the
# ellratio / thetasum peers.
# ----------------------------------------------------------------------


def has_native_elliptic_lagrange_basis() -> bool:
    """True iff the rc67 srmech_elliptic_lagrange_basis op + its ws sizer + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc67 lib — the pure-Python ``srmech.amsc.ellbase.elliptic_lagrange_basis``
    body is the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLRATIO_SYMS) and all(
        hasattr(LIB, s) for s in (
            "srmech_elliptic_lagrange_basis",
            "srmech_elliptic_lagrange_basis_ws_bound",
        )
    )


def elliptic_lagrange_basis_c(n_syms, varsym, psym, k, point_monos, mult_mono):
    """Native ``elliptic_lagrange_basis`` for the k point monomials + the multiplier
    monomial → a list of ``k`` EllRatio bridge forms (each a dict ``{"prefactor":
    (coeff_num, coeff_den, exps), "num": [...], "den": [...]}``), or ``None`` if the
    native symbols are absent. ``n_syms`` is the interned symbol-table dimension;
    ``varsym`` / ``psym`` the interned indices of the interpolation variable + the
    nome ``p`` (-1 if absent); ``point_monos`` the list of ``k`` ``(num, den,
    exps_row)`` point triples (each ``exps_row`` a length-``n_syms`` int list);
    ``mult_mono`` the multiplier ``(num, den, exps_row)`` triple. The returned thetas
    are decoded against ``sym_list`` by the caller. A non-OK C status raises
    ``RuntimeError``."""
    if not has_native_elliptic_lagrange_basis():
        return None
    if k == 0:
        raise ValueError("elliptic_lagrange_basis_c: need at least one interpolation point")
    if n_syms == 0:
        # a pure-scalar table clamps to a single all-zero exponent slot (the C clamps
        # n_syms -> 1) so every monomial reads a consistent dense row.
        n_syms = 1
        point_monos = [(num, den, [0]) for num, den, _e in point_monos]
        m_num, m_den, _me = mult_mono
        mult_mono = (m_num, m_den, [0])
    all_monos = list(point_monos) + [mult_mono]
    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad). The balancing
    # point v_i = (-1)^k·t/∏others multiplies coefficients, so size generously.
    cl = 2
    for num, den, _exps in all_monos:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    out_cap = cl + 8
    work_cap = cl + 8
    ws_len = int(LIB.srmech_elliptic_lagrange_basis_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(k), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    keep = []
    # the k flat point inputs.
    pt_num_arr = (_SrmechBigint * k)()
    pt_den_arr = (_SrmechBigint * k)()
    pt_exps_flat = []
    for i, (num, den, exps_row) in enumerate(point_monos):
        if len(exps_row) != n_syms:
            raise ValueError("elliptic_lagrange_basis_c: point exps row length != n_syms")
        bn, kbn = _bigint_from_int(int(num), work_cap)
        bd, kbd = _bigint_from_int(int(den), work_cap)
        pt_num_arr[i] = bn
        pt_den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        pt_exps_flat.extend(int(e) for e in exps_row)
    pt_exps_c = (ctypes.c_int32 * max(len(pt_exps_flat), 1))(*pt_exps_flat)
    # the multiplier monomial.
    m_num, m_den, m_exps = mult_mono
    if len(m_exps) != n_syms:
        raise ValueError("elliptic_lagrange_basis_c: multiplier exps row length != n_syms")
    mbn, kmbn = _bigint_from_int(int(m_num), work_cap)
    mbd, kmbd = _bigint_from_int(int(m_den), work_cap)
    keep.append(kmbn)
    keep.append(kmbd)
    m_exps_c = (ctypes.c_int32 * max(n_syms, 1))(*[int(e) for e in m_exps])
    # the output buffers: a single ROW stream -- each emitted monomial (a prefactor
    # OR a theta argument) is one row carrying its exact-Q coeff (out_cn / out_cd) +
    # its dense exps row (out_exps). Each L_i emits 1 prefactor row + k num-theta rows
    # + 0 den rows; budget k*(1+k) rows + generous slack. The coeff travels with EVERY
    # row because a theta ARGUMENT can carry a non-unit Class-K coeff (the balancing
    # arg z·v_i^{-1}); assuming coeff 1 (the well-poised gosper convention) drops it.
    out_cap_rows = k * (1 + k) + 8
    out_cn_arr = (_SrmechBigint * out_cap_rows)()
    out_cd_arr = (_SrmechBigint * out_cap_rows)()
    for r in range(out_cap_rows):
        ocn, kocn = _bigint_from_int(0, out_cap)
        ocd, kocd = _bigint_from_int(0, out_cap)
        out_cn_arr[r] = ocn
        out_cd_arr[r] = ocd
        keep.append(kocn)
        keep.append(kocd)
    out_exps = (ctypes.c_int32 * max(out_cap_rows * n_syms, 1))()
    out_nn = (ctypes.c_size_t * k)()
    out_nd = (ctypes.c_size_t * k)()
    rc = LIB.srmech_elliptic_lagrange_basis(
        ctypes.c_size_t(n_syms),
        ctypes.c_int(varsym), ctypes.c_int(psym),
        ctypes.c_size_t(k),
        pt_num_arr, pt_den_arr, pt_exps_c,
        ctypes.byref(mbn), ctypes.byref(mbd), m_exps_c,
        ctypes.c_uint32(work_cap),
        out_cn_arr, out_cd_arr, out_exps, ctypes.c_size_t(out_cap_rows),
        out_nn, out_nd,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_elliptic_lagrange_basis returned non-OK status {rc}")
    # rebuild the k EllRatio bridge forms from the flat output ROW stream (each row
    # = (coeff_num, coeff_den, exps_row)).
    def _read_row(r):
        return (_bigint_to_int(out_cn_arr[r]), _bigint_to_int(out_cd_arr[r]),
                [int(out_exps[r * n_syms + j]) for j in range(n_syms)])

    basis = []
    row = 0
    for i in range(k):
        nn = out_nn[i]
        nd = out_nd[i]
        pref = _read_row(row)
        row += 1
        num_rows = []
        for _ in range(nn):
            num_rows.append(_read_row(row))
            row += 1
        den_rows = []
        for _ in range(nd):
            den_rows.append(_read_row(row))
            row += 1
        basis.append({"prefactor": pref, "num": num_rows, "den": den_rows})
    return basis


# ----------------------------------------------------------------------
# rc94: srmech_elliptic_cauchy_determinant — the C peer of the EllRatio-carrier op
# srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant (Frobenius's elliptic
# Cauchy determinant; the foundation of the multivariable Cₙ elliptic reduction row). A
# C-MIRROR PARITY build: the single closed-form EllRatio comes back byte-exact equal to the
# pure-Python op. srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant dispatches
# through here when the peer is loaded; the pure-Python body is the complete alternative +
# the parity oracle. Shares the srmech_bigint decimal-marshal helpers (in _ELLRATIO_SYMS)
# with the ellratio / lagrange peers.
# ----------------------------------------------------------------------


def has_native_elliptic_cauchy_determinant() -> bool:
    """True iff the rc94 srmech_elliptic_cauchy_determinant op + its ws sizer + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc94 lib — the pure-Python
    ``srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLRATIO_SYMS) and all(
        hasattr(LIB, s) for s in (
            "srmech_elliptic_cauchy_determinant",
            "srmech_elliptic_cauchy_determinant_ws_bound",
        )
    )


def elliptic_cauchy_determinant_c(n_syms, psym, n, t_mono, x_monos, y_monos):
    """Native ``elliptic_cauchy_determinant`` for the parameter monomial ``t_mono`` + the
    ``n`` x-monomials ``x_monos`` + the ``n`` y-monomials ``y_monos`` → the single
    closed-form EllRatio bridge form (a dict ``{"prefactor": (coeff_num, coeff_den, exps),
    "num": [...], "den": [...]}``), or ``None`` if the native symbols are absent.
    ``n_syms`` is the interned symbol-table dimension; ``psym`` the interned index of the
    nome ``p`` (-1 if absent); each mono is a ``(num, den, exps_row)`` triple (each
    ``exps_row`` a length-``n_syms`` int list). The returned thetas are decoded against
    ``sym_list`` by the caller. A non-OK C status raises ``RuntimeError``."""
    if not has_native_elliptic_cauchy_determinant():
        return None
    if n == 0:
        raise ValueError("elliptic_cauchy_determinant_c: need at least one variable")
    if n_syms == 0:
        # a pure-scalar table clamps to a single all-zero exponent slot (the C clamps
        # n_syms -> 1) so every monomial reads a consistent dense row.
        n_syms = 1
        t_mono = (t_mono[0], t_mono[1], [0])
        x_monos = [(num, den, [0]) for num, den, _e in x_monos]
        y_monos = [(num, den, [0]) for num, den, _e in y_monos]
    all_monos = [t_mono] + list(x_monos) + list(y_monos)
    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad). The theta
    # canonicalization + product prefactors multiply coefficients, so size generously.
    cl = 2
    for num, den, _exps in all_monos:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    out_cap = cl + 8
    work_cap = cl + 8
    ws_len = int(LIB.srmech_elliptic_cauchy_determinant_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    keep = []
    # the parameter t.
    t_num, t_den, t_exps = t_mono
    if len(t_exps) != n_syms:
        raise ValueError("elliptic_cauchy_determinant_c: t exps row length != n_syms")
    tbn, ktbn = _bigint_from_int(int(t_num), work_cap)
    tbd, ktbd = _bigint_from_int(int(t_den), work_cap)
    keep.append(ktbn)
    keep.append(ktbd)
    t_exps_c = (ctypes.c_int32 * max(n_syms, 1))(*[int(e) for e in t_exps])
    # the n flat x + y monomial inputs.
    xs_num_arr = (_SrmechBigint * n)()
    xs_den_arr = (_SrmechBigint * n)()
    ys_num_arr = (_SrmechBigint * n)()
    ys_den_arr = (_SrmechBigint * n)()
    xs_exps_flat = []
    ys_exps_flat = []
    for i, (num, den, exps_row) in enumerate(x_monos):
        if len(exps_row) != n_syms:
            raise ValueError("elliptic_cauchy_determinant_c: x exps row length != n_syms")
        bn, kbn = _bigint_from_int(int(num), work_cap)
        bd, kbd = _bigint_from_int(int(den), work_cap)
        xs_num_arr[i] = bn
        xs_den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        xs_exps_flat.extend(int(e) for e in exps_row)
    for i, (num, den, exps_row) in enumerate(y_monos):
        if len(exps_row) != n_syms:
            raise ValueError("elliptic_cauchy_determinant_c: y exps row length != n_syms")
        bn, kbn = _bigint_from_int(int(num), work_cap)
        bd, kbd = _bigint_from_int(int(den), work_cap)
        ys_num_arr[i] = bn
        ys_den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        ys_exps_flat.extend(int(e) for e in exps_row)
    xs_exps_c = (ctypes.c_int32 * max(len(xs_exps_flat), 1))(*xs_exps_flat)
    ys_exps_c = (ctypes.c_int32 * max(len(ys_exps_flat), 1))(*ys_exps_flat)
    # the output ROW stream: a prefactor row + up to n*n num rows + up to n*n den rows
    # (the theta counts shrink under cancellation; budget n*n each + slack). Every row
    # carries its exact-Q coeff (out_cn / out_cd) + its dense exps row (out_exps).
    nsq = n * n
    out_cap_rows = 1 + 2 * nsq + 8
    out_cn_arr = (_SrmechBigint * out_cap_rows)()
    out_cd_arr = (_SrmechBigint * out_cap_rows)()
    for r in range(out_cap_rows):
        ocn, kocn = _bigint_from_int(0, out_cap)
        ocd, kocd = _bigint_from_int(0, out_cap)
        out_cn_arr[r] = ocn
        out_cd_arr[r] = ocd
        keep.append(kocn)
        keep.append(kocd)
    out_exps = (ctypes.c_int32 * max(out_cap_rows * n_syms, 1))()
    out_nn = (ctypes.c_size_t * 1)()
    out_nd = (ctypes.c_size_t * 1)()
    rc = LIB.srmech_elliptic_cauchy_determinant(
        ctypes.c_size_t(n_syms), ctypes.c_int(psym), ctypes.c_size_t(n),
        ctypes.byref(tbn), ctypes.byref(tbd), t_exps_c,
        xs_num_arr, xs_den_arr, xs_exps_c,
        ys_num_arr, ys_den_arr, ys_exps_c,
        ctypes.c_uint32(work_cap),
        out_cn_arr, out_cd_arr, out_exps, ctypes.c_size_t(out_cap_rows),
        out_nn, out_nd,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_elliptic_cauchy_determinant returned non-OK status {rc}")

    # rebuild the single EllRatio bridge form from the flat output ROW stream.
    def _read_row(r):
        return (_bigint_to_int(out_cn_arr[r]), _bigint_to_int(out_cd_arr[r]),
                [int(out_exps[r * n_syms + j]) for j in range(n_syms)])

    n_num = out_nn[0]
    n_den = out_nd[0]
    row = 0
    pref = _read_row(row)
    row += 1
    num_rows = []
    for _ in range(n_num):
        num_rows.append(_read_row(row))
        row += 1
    den_rows = []
    for _ in range(n_den):
        den_rows.append(_read_row(row))
        row += 1
    return {"prefactor": pref, "num": num_rows, "den": den_rows}


# ----------------------------------------------------------------------
# rc95: srmech_elliptic_partial_fraction — the C peer of the ThetaSum-returning op
# srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction (the elliptic
# partial-fraction expansion; the reduction engine of the multivariable Cₙ elliptic
# reduction row). A C-MIRROR PARITY build: the n TERM EllRatios come back byte-exact
# equal to the pure-Python op's terms, and the Python side sums them into the
# ThetaSum. srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction dispatches
# through here when the peer is loaded, trusting the native ThetaSum only after it
# `==` the pure ThetaSum; the pure-Python body is the complete alternative + oracle.
# Shares the srmech_bigint decimal-marshal helpers (in _ELLRATIO_SYMS) with the
# ellratio / lagrange / cauchy-determinant peers.
# ----------------------------------------------------------------------


def has_native_elliptic_partial_fraction() -> bool:
    """True iff the rc95 srmech_elliptic_partial_fraction op + its ws sizer + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc95 lib — the pure-Python
    ``srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction`` body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLRATIO_SYMS) and all(
        hasattr(LIB, s) for s in (
            "srmech_elliptic_partial_fraction",
            "srmech_elliptic_partial_fraction_ws_bound",
        )
    )


def elliptic_partial_fraction_c(n_syms, psym, n, x_mono, z_monos, y_monos):
    """Native ``elliptic_partial_fraction`` for the variable monomial ``x_mono`` + the
    ``n`` z-monomials ``z_monos`` + the ``n`` y-monomials ``y_monos`` → a list of ``n``
    EllRatio TERM bridge forms (each a dict ``{"prefactor": (coeff_num, coeff_den,
    exps), "num": [...], "den": [...]}``), or ``None`` if the native symbols are absent
    (the caller sums the forms into a ThetaSum). ``n_syms`` is the interned symbol-table
    dimension; ``psym`` the interned index of the nome ``p`` (-1 if absent); each mono is
    a ``(num, den, exps_row)`` triple (each ``exps_row`` a length-``n_syms`` int list).
    The returned thetas are decoded against ``sym_list`` by the caller. A non-OK C status
    raises ``RuntimeError``."""
    if not has_native_elliptic_partial_fraction():
        return None
    if n == 0:
        raise ValueError("elliptic_partial_fraction_c: need at least one variable")
    if n_syms == 0:
        # a pure-scalar table clamps to a single all-zero exponent slot (the C clamps
        # n_syms -> 1) so every monomial reads a consistent dense row.
        n_syms = 1
        x_mono = (x_mono[0], x_mono[1], [0])
        z_monos = [(num, den, [0]) for num, den, _e in z_monos]
        y_monos = [(num, den, [0]) for num, den, _e in y_monos]
    all_monos = [x_mono] + list(z_monos) + list(y_monos)
    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad). The theta
    # canonicalization + the Y/Z + x*Y/(y_j*Z) products multiply coefficients, so size
    # generously.
    cl = 2
    for num, den, _exps in all_monos:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    out_cap = cl + 8
    work_cap = cl + 8
    ws_len = int(LIB.srmech_elliptic_partial_fraction_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(n), ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    keep = []
    # the variable x.
    x_num, x_den, x_exps = x_mono
    if len(x_exps) != n_syms:
        raise ValueError("elliptic_partial_fraction_c: x exps row length != n_syms")
    xbn, kxbn = _bigint_from_int(int(x_num), work_cap)
    xbd, kxbd = _bigint_from_int(int(x_den), work_cap)
    keep.append(kxbn)
    keep.append(kxbd)
    x_exps_c = (ctypes.c_int32 * max(n_syms, 1))(*[int(e) for e in x_exps])
    # the n flat z + y monomial inputs.
    zs_num_arr = (_SrmechBigint * n)()
    zs_den_arr = (_SrmechBigint * n)()
    ys_num_arr = (_SrmechBigint * n)()
    ys_den_arr = (_SrmechBigint * n)()
    zs_exps_flat = []
    ys_exps_flat = []
    for i, (num, den, exps_row) in enumerate(z_monos):
        if len(exps_row) != n_syms:
            raise ValueError("elliptic_partial_fraction_c: z exps row length != n_syms")
        bn, kbn = _bigint_from_int(int(num), work_cap)
        bd, kbd = _bigint_from_int(int(den), work_cap)
        zs_num_arr[i] = bn
        zs_den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        zs_exps_flat.extend(int(e) for e in exps_row)
    for i, (num, den, exps_row) in enumerate(y_monos):
        if len(exps_row) != n_syms:
            raise ValueError("elliptic_partial_fraction_c: y exps row length != n_syms")
        bn, kbn = _bigint_from_int(int(num), work_cap)
        bd, kbd = _bigint_from_int(int(den), work_cap)
        ys_num_arr[i] = bn
        ys_den_arr[i] = bd
        keep.append(kbn)
        keep.append(kbd)
        ys_exps_flat.extend(int(e) for e in exps_row)
    zs_exps_c = (ctypes.c_int32 * max(len(zs_exps_flat), 1))(*zs_exps_flat)
    ys_exps_c = (ctypes.c_int32 * max(len(ys_exps_flat), 1))(*ys_exps_flat)
    # the output ROW stream: per term j a prefactor row + up to n+1 num rows + up to
    # n+1 den rows (the theta counts shrink under cancellation); budget n*(1+2*(n+1))
    # rows + slack. Every row carries its exact-Q coeff (out_cn / out_cd) + its dense
    # exps row (out_exps).
    out_cap_rows = n * (1 + 2 * (n + 1)) + 8
    out_cn_arr = (_SrmechBigint * out_cap_rows)()
    out_cd_arr = (_SrmechBigint * out_cap_rows)()
    for r in range(out_cap_rows):
        ocn, kocn = _bigint_from_int(0, out_cap)
        ocd, kocd = _bigint_from_int(0, out_cap)
        out_cn_arr[r] = ocn
        out_cd_arr[r] = ocd
        keep.append(kocn)
        keep.append(kocd)
    out_exps = (ctypes.c_int32 * max(out_cap_rows * n_syms, 1))()
    out_nn = (ctypes.c_size_t * n)()
    out_nd = (ctypes.c_size_t * n)()
    rc = LIB.srmech_elliptic_partial_fraction(
        ctypes.c_size_t(n_syms), ctypes.c_int(psym), ctypes.c_size_t(n),
        ctypes.byref(xbn), ctypes.byref(xbd), x_exps_c,
        zs_num_arr, zs_den_arr, zs_exps_c,
        ys_num_arr, ys_den_arr, ys_exps_c,
        ctypes.c_uint32(work_cap),
        out_cn_arr, out_cd_arr, out_exps, ctypes.c_size_t(out_cap_rows),
        out_nn, out_nd,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_elliptic_partial_fraction returned non-OK status {rc}")

    # rebuild the n EllRatio TERM bridge forms from the flat output ROW stream.
    def _read_row(r):
        return (_bigint_to_int(out_cn_arr[r]), _bigint_to_int(out_cd_arr[r]),
                [int(out_exps[r * n_syms + j]) for j in range(n_syms)])

    forms = []
    row = 0
    for i in range(n):
        nn = out_nn[i]
        nd = out_nd[i]
        pref = _read_row(row)
        row += 1
        num_rows = []
        for _ in range(nn):
            num_rows.append(_read_row(row))
            row += 1
        den_rows = []
        for _ in range(nd):
            den_rows.append(_read_row(row))
            row += 1
        forms.append({"prefactor": pref, "num": num_rows, "den": den_rows})
    return forms


# ----------------------------------------------------------------------
# rc96: srmech_multivariate_elliptic_jackson — the C peer of the EllRatio-carrier op
# srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson (the eq-5 Cₙ
# elliptic Jackson summation reducer; the capstone of the multivariable Cₙ elliptic
# reduction row). A C-MIRROR PARITY build: the single closed-form EllRatio comes back
# byte-exact equal to the pure-Python op.
# srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson dispatches through
# here when the peer is loaded (and trusts it only after it == the pure EllRatio); the
# pure-Python body is the complete alternative + the parity oracle. Shares the srmech_bigint
# decimal-marshal helpers (in _ELLRATIO_SYMS) with the ellratio / lagrange peers.
# ----------------------------------------------------------------------


def has_native_multivariate_elliptic_jackson() -> bool:
    """True iff the rc96 srmech_multivariate_elliptic_jackson op + its ws sizer + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc96 lib — the pure-Python
    ``srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson`` body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ELLRATIO_SYMS) and all(
        hasattr(LIB, s) for s in (
            "srmech_multivariate_elliptic_jackson",
            "srmech_multivariate_elliptic_jackson_ws_bound",
        )
    )


def multivariate_elliptic_jackson_c(n_syms, psym, N, n, a_mono, b_mono, c_mono, d_mono,
                                    x_mono, q_mono):
    """Native ``multivariate_elliptic_jackson`` for the parameter monomials ``a`` / ``b`` /
    ``c`` / ``d`` + the base variables ``x`` / ``q`` + the positive ints ``N`` (partition
    ceiling) / ``n`` (rank) → the single closed-form EllRatio bridge form (a dict
    ``{"prefactor": (coeff_num, coeff_den, exps), "num": [...], "den": [...]}``), or ``None``
    if the native symbols are absent. ``n_syms`` is the interned symbol-table dimension;
    ``psym`` the interned index of the nome ``p`` (-1 if absent); each mono is a
    ``(num, den, exps_row)`` triple (each ``exps_row`` a length-``n_syms`` int list). The
    returned thetas are decoded against ``sym_list`` by the caller. A non-OK C status raises
    ``RuntimeError``."""
    if not has_native_multivariate_elliptic_jackson():
        return None
    if N < 1 or n < 1:
        raise ValueError("multivariate_elliptic_jackson_c: N and n must be >= 1")
    monos = [a_mono, b_mono, c_mono, d_mono, x_mono, q_mono]
    if n_syms == 0:
        # a pure-scalar table clamps to a single all-zero exponent slot (the C clamps
        # n_syms -> 1) so every monomial reads a consistent dense row.
        n_syms = 1
        monos = [(m[0], m[1], [0]) for m in monos]
    # per-coefficient limb estimate (9 decimal digits ~ 1 limb; pad). The theta
    # canonicalization + product prefactors multiply coefficients, so size generously.
    cl = 2
    for num, den, _exps in monos:
        cl = max(cl, len(str(num).lstrip("-")) // 9 + 2, len(str(den)) // 9 + 2)
    out_cap = cl + 8
    work_cap = cl + 8
    ws_len = int(LIB.srmech_multivariate_elliptic_jackson_ws_bound(
        ctypes.c_size_t(n_syms), ctypes.c_size_t(N), ctypes.c_size_t(n),
        ctypes.c_size_t(work_cap)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    keep = []
    # marshal the 6 input monomials into bigint pairs + int32 exponent rows.
    bi_pairs = []
    exps_cs = []
    for (num, den, exps_row) in monos:
        if len(exps_row) != n_syms:
            raise ValueError(
                "multivariate_elliptic_jackson_c: exps row length != n_syms")
        bn, kbn = _bigint_from_int(int(num), work_cap)
        bd, kbd = _bigint_from_int(int(den), work_cap)
        keep.append(kbn)
        keep.append(kbd)
        bi_pairs.append((bn, bd))
        exps_cs.append((ctypes.c_int32 * max(n_syms, 1))(*[int(e) for e in exps_row]))
    # the output ROW stream: a prefactor row + up to 4*N*n num rows + up to 4*N*n den rows
    # (the theta counts shrink under cancellation; budget 4*N*n each + slack). Every row
    # carries its exact-Q coeff (out_cn / out_cd) + its dense exps row (out_exps).
    ntheta = 4 * N * n
    out_cap_rows = 1 + 2 * ntheta + 8
    out_cn_arr = (_SrmechBigint * out_cap_rows)()
    out_cd_arr = (_SrmechBigint * out_cap_rows)()
    for r in range(out_cap_rows):
        ocn, kocn = _bigint_from_int(0, out_cap)
        ocd, kocd = _bigint_from_int(0, out_cap)
        out_cn_arr[r] = ocn
        out_cd_arr[r] = ocd
        keep.append(kocn)
        keep.append(kocd)
    out_exps = (ctypes.c_int32 * max(out_cap_rows * n_syms, 1))()
    out_nn = (ctypes.c_size_t * 1)()
    out_nd = (ctypes.c_size_t * 1)()
    (an, ad), (bbn, bbd), (ccn, ccd), (ddn, ddd), (xn, xd), (qn, qd) = bi_pairs
    rc = LIB.srmech_multivariate_elliptic_jackson(
        ctypes.c_size_t(n_syms), ctypes.c_int(psym),
        ctypes.c_size_t(N), ctypes.c_size_t(n),
        ctypes.byref(an), ctypes.byref(ad), exps_cs[0],
        ctypes.byref(bbn), ctypes.byref(bbd), exps_cs[1],
        ctypes.byref(ccn), ctypes.byref(ccd), exps_cs[2],
        ctypes.byref(ddn), ctypes.byref(ddd), exps_cs[3],
        ctypes.byref(xn), ctypes.byref(xd), exps_cs[4],
        ctypes.byref(qn), ctypes.byref(qd), exps_cs[5],
        ctypes.c_uint32(work_cap),
        out_cn_arr, out_cd_arr, out_exps, ctypes.c_size_t(out_cap_rows),
        out_nn, out_nd,
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_multivariate_elliptic_jackson returned non-OK status {rc}")

    # rebuild the single EllRatio bridge form from the flat output ROW stream.
    def _read_row(r):
        return (_bigint_to_int(out_cn_arr[r]), _bigint_to_int(out_cd_arr[r]),
                [int(out_exps[r * n_syms + j]) for j in range(n_syms)])

    n_num = out_nn[0]
    n_den = out_nd[0]
    row = 0
    pref = _read_row(row)
    row += 1
    num_rows = []
    for _ in range(n_num):
        num_rows.append(_read_row(row))
        row += 1
    den_rows = []
    for _ in range(n_den):
        den_rows.append(_read_row(row))
        row += 1
    return {"prefactor": pref, "num": num_rows, "den": den_rows}


# ----------------------------------------------------------------------
# rc42: srmech_zeilberger — Zeilberger's creative telescoping (the §76 telescope
# Sigma-row's SECOND public op). The Python srmech.amsc.zeilberger.zeilberger
# routes a POSITIVE (recurrence-found) C result through this; a has=0 / error
# falls to the complete pure-Python path (the parity oracle + full-coverage
# decider). The four bivariate ratios + the recurrence/certificate ride the same
# _SrmechBigint coefficient-array bridge as qmat / poly / gosper.
# ----------------------------------------------------------------------

_ZEILBERGER_SYMS = (
    "srmech_zeilberger_ws_bound",
    "srmech_zeilberger_out_cap",
)


def has_native_zeilberger() -> bool:
    """True iff the rc42 srmech_zeilberger op + its ws/out-cap sizers are loaded +
    bound. False on a no-C or pre-rc42 lib — the pure-Python
    ``srmech.amsc.zeilberger.zeilberger`` body is the complete alternative (and the
    parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _ZEILBERGER_SYMS) and hasattr(
        LIB, "srmech_zeilberger"
    )


def _bi_flatten(bi_pairs):
    """A bivariate ``[[(num,den), ...]_k0, ...]`` (the ``BiPoly`` bridge form) →
    ``(flat_pairs, klen_list)`` where ``flat_pairs`` lists every coefficient in
    k-then-n order and ``klen_list[dk]`` is the n-coefficient count of k-slot
    ``dk``."""
    flat = []
    klen = []
    for kp in bi_pairs:
        klen.append(len(kp))
        flat.extend(kp)
    return flat, klen


def zeilberger_c(rn_num, rn_den, rk_num, rk_den, max_order):
    """Native Zeilberger recurrence for the four bivariate term ratios → ``(has,
    order, coeff_pairs, cert_pairs)`` (``coeff_pairs[j]`` the ascending-n
    ``(num,den)`` list of ``a_j(n)``; ``cert_pairs[dk]`` the k-slot ``dk`` n-coeff
    list of the certificate ``x(n,k)``), or ``None`` if the native symbols are
    absent. Each ratio operand is a bivariate-pairs structure (the ``_bi_pairs``
    bridge form). A non-OK status / inability raises ``RuntimeError`` so the caller
    falls to the pure path."""
    if not has_native_zeilberger():
        return None
    flats = []
    klens = []
    for bp in (rn_num, rn_den, rk_num, rk_den):
        f, k = _bi_flatten(bp)
        flats.append(f)
        klens.append(k)
    if len(klens[1]) == 0 or len(klens[3]) == 0:
        raise ValueError("zeilberger_c: r_n / r_k denominators must be nonzero")
    deg = max((len(k) for k in klens), default=1)
    cl = max((_qmat_coeff_limbs(f) if f else 1 for f in flats), default=1)
    out_cap = int(LIB.srmech_zeilberger_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(max_order), ctypes.c_size_t(deg)))
    ws_len = int(LIB.srmech_zeilberger_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(max_order), ctypes.c_size_t(deg)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    # marshal the four inputs (flat coeff arrays + klen size_t arrays).
    in_arrays = []
    keep = []
    for f, k in zip(flats, klens):
        a_n, a_d, ka = _qmat_make_array(f, out_cap)
        klen_arr = (ctypes.c_size_t * max(len(k), 1))(*k)
        in_arrays.append((a_n, a_d, klen_arr, len(k)))
        keep.append(ka)
        keep.append(klen_arr)
    # output arrays: coeff (order+1)*nbound ; cert kbound*nbound. A generous slot
    # count; the C writes contiguously + reports per-segment lengths.
    nbound = (deg + 2) * (max_order + 2) + 8
    coeff_slots = (max_order + 1) * nbound + 8
    cert_slots = nbound * nbound + 8
    coeff_n, coeff_d, kc = _qmat_blank_array(coeff_slots, out_cap)
    cert_n, cert_d, ke = _qmat_blank_array(cert_slots, out_cap)
    coeff_nlen = (ctypes.c_size_t * (max_order + 2))()
    cert_klen = (ctypes.c_size_t * (nbound + 2))()
    has = ctypes.c_int(0)
    order_out = ctypes.c_size_t(0)
    cert_kdeg = ctypes.c_size_t(0)
    rc = LIB.srmech_zeilberger(
        in_arrays[0][0], in_arrays[0][1], in_arrays[0][2], ctypes.c_size_t(in_arrays[0][3]),
        in_arrays[1][0], in_arrays[1][1], in_arrays[1][2], ctypes.c_size_t(in_arrays[1][3]),
        in_arrays[2][0], in_arrays[2][1], in_arrays[2][2], ctypes.c_size_t(in_arrays[2][3]),
        in_arrays[3][0], in_arrays[3][1], in_arrays[3][2], ctypes.c_size_t(in_arrays[3][3]),
        ctypes.c_size_t(max_order), ctypes.c_size_t(deg),
        ctypes.byref(has), ctypes.byref(order_out),
        coeff_n, coeff_d, coeff_nlen,
        cert_n, cert_d, cert_klen,
        ctypes.byref(cert_kdeg),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (keep, kc, ke)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_zeilberger returned non-OK status {rc}")
    if not has.value:
        return False, 0, [], []
    order = int(order_out.value)
    # read the contiguous coeff segments (per coeff_nlen[j]).
    coeff_pairs = []
    off = 0
    for j in range(order + 1):
        ln = int(coeff_nlen[j])
        coeff_pairs.append([(_bigint_to_int(coeff_n[off + i]),
                             _bigint_to_int(coeff_d[off + i])) for i in range(ln)])
        off += ln
    # read the contiguous certificate segments (per cert_klen[dk]).
    cert_pairs = []
    off = 0
    kdeg = int(cert_kdeg.value)
    for dk in range(kdeg):
        ln = int(cert_klen[dk])
        cert_pairs.append([(_bigint_to_int(cert_n[off + i]),
                            _bigint_to_int(cert_d[off + i])) for i in range(ln)])
        off += ln
    return True, order, coeff_pairs, cert_pairs


# ----------------------------------------------------------------------
# rc56: srmech_q_zeilberger — the q-analog of Zeilberger's creative telescoping (the
# SECOND public op of the q-hypergeometric F929 row). The Python
# srmech.amsc.q_zeilberger.q_zeilberger routes a POSITIVE (recurrence-found) C result
# through this; a has=0 / error falls to the complete pure-Python path (the parity
# oracle + full-coverage decider). The four QBiPoly term ratios + the recurrence
# coeffs + the certificate ride the QBiPoly bridge form: a per-Y-cell x_low[] +
# x_cells[] + the concatenated QPoly q-runs (Y-major then X-major) + a per-(Y,X)-cell
# qlen[]. The native peer completes the canonical k-free q-geometric order-1 case +
# declines the rest (has=0 -> Python re-decides).
# ----------------------------------------------------------------------

_Q_ZEILBERGER_SYMS = (
    "srmech_q_zeilberger_ws_bound",
    "srmech_q_zeilberger_out_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_q_zeilberger() -> bool:
    """True iff the rc56 srmech_q_zeilberger op + its ws/out-cap sizers + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc56 lib — the pure-Python ``srmech.amsc.q_zeilberger.q_zeilberger`` body is
    the complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _Q_ZEILBERGER_SYMS) and hasattr(
        LIB, "srmech_q_zeilberger"
    )


def _qbi_flatten(form, out_cap):
    """A QBiPoly ``(y_xlow[], rows)`` bridge form → the flat native arrays
    ``(num_arr, den_arr, qlen_arr, xlow_arr, xcells_arr, ycells, keepalive)``: the
    concatenated q-runs (Y-major then X-major), a per-(Y,X)-cell ``qlen[]``, a per-Y-
    cell ``x_low[]`` and ``x_cells[]``, and the Y-cell count. ``rows[yd]`` is the
    QPoly x-row (an ascending-x list of ascending-q (num, den) runs) of Y-cell
    ``yd``."""
    y_xlow, rows = form
    ycells = len(rows)
    xcells = [len(xrow) for xrow in rows]
    qlens = []
    flat = []
    for xrow in rows:
        for run in xrow:
            qlens.append(len(run))
            flat.extend(run)
    total = max(len(flat), 1)
    num_arr = (_SrmechBigint * total)()
    den_arr = (_SrmechBigint * total)()
    keep = []
    for idx, (num, den) in enumerate(flat):
        bn, kbn = _bigint_from_int(int(num), out_cap)
        bd, kbd = _bigint_from_int(int(den), out_cap)
        num_arr[idx] = bn
        den_arr[idx] = bd
        keep.append(kbn)
        keep.append(kbd)
    qlen_arr = (ctypes.c_size_t * max(len(qlens), 1))(*qlens)
    xlow_arr = (ctypes.c_int64 * max(ycells, 1))(*[int(v) for v in y_xlow])
    xcells_arr = (ctypes.c_size_t * max(ycells, 1))(*xcells)
    keep += [qlen_arr, xlow_arr, xcells_arr]
    return num_arr, den_arr, qlen_arr, xlow_arr, xcells_arr, ycells, keep


def _qbi_row_coeff_limbs(form):
    """The largest significant-limb count across every (num, den) in a QBiPoly bridge
    form (9 decimal digits ≈ 1 limb; pad)."""
    cl = 1
    _y, rows = form
    for xrow in rows:
        for run in xrow:
            for num, den in run:
                cl = max(cl, len(str(num).lstrip("-")) // 9 + 2,
                         len(str(den)) // 9 + 2)
    return cl


def q_zeilberger_c(rn_num, rn_den, rk_num, rk_den, max_order):
    """Native q-Zeilberger recurrence for the four QBiPoly term ratios → ``(has,
    order, coeff_forms, cert_form)`` (``coeff_forms[j]`` the QPoly ``(x_low, rows)``
    bridge form of ``a_j(X)``; ``cert_form`` the QBiPoly ``(y_xlow[], rows)`` bridge
    form of the certificate ``x(X,Y)``), or ``None`` if the native symbols are absent.
    Each ratio operand is a QBiPoly ``(y_xlow[], rows)`` bridge form. The native peer
    completes the canonical k-free q-geometric order-1 case + declines the rest
    (``has`` False → the caller re-decides on the pure path). A non-OK status raises
    ``RuntimeError`` so the caller falls to the pure path."""
    if not has_native_q_zeilberger():
        return None
    forms = (rn_num, rn_den, rk_num, rk_den)
    if not rn_den[1] or not rk_den[1]:
        raise ValueError("q_zeilberger_c: r_n / r_k denominators must be nonzero")
    cl = max(_qbi_row_coeff_limbs(f) for f in forms)
    qdeg = 1
    for f in forms:
        for xrow in f[1]:
            for run in xrow:
                qdeg = max(qdeg, len(run))
    out_cap = int(LIB.srmech_q_zeilberger_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(max_order), ctypes.c_size_t(qdeg)))
    ws_len = int(LIB.srmech_q_zeilberger_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(max_order), ctypes.c_size_t(qdeg)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    keep = []
    in_args = []
    for f in forms:
        nn, dd, ql, xl, xc, yc, k = _qbi_flatten(f, out_cap)
        in_args += [nn, dd, ql, xl, xc, ctypes.c_size_t(yc)]
        keep.append(k)
    # output: up to (max_order+1) coeff QPoly cells (each a single X-cell here) +
    # a certificate QBiPoly (bounded Y-cells). Generous slot counts; the C reports the
    # per-cell lengths + counts.
    coeff_cells = max_order + 2
    cell_q_cap = qdeg + 4
    coeff_total = coeff_cells * cell_q_cap + 8
    cert_total = (qdeg + 4) * cell_q_cap + 8
    coeff_n, coeff_d, kc = _qmat_blank_array(coeff_total, out_cap)
    cert_n, cert_d, ke = _qmat_blank_array(cert_total, out_cap)
    coeff_qlen = (ctypes.c_size_t * (coeff_cells + 2))()
    coeff_xlow = (ctypes.c_int64 * (coeff_cells + 2))()
    coeff_xcells = (ctypes.c_size_t * (coeff_cells + 2))()
    cert_qlen = (ctypes.c_size_t * (qdeg + 8))()
    cert_xlow = (ctypes.c_int64 * (qdeg + 8))()
    cert_xcells = (ctypes.c_size_t * (qdeg + 8))()
    has = ctypes.c_int(0)
    order_out = ctypes.c_size_t(0)
    coeff_count = ctypes.c_size_t(0)
    cert_ycells = ctypes.c_size_t(0)
    rc = LIB.srmech_q_zeilberger(
        *in_args,
        ctypes.c_size_t(max_order),
        ctypes.byref(has), ctypes.byref(order_out),
        coeff_n, coeff_d, coeff_qlen, coeff_xlow, coeff_xcells,
        ctypes.byref(coeff_count),
        cert_n, cert_d, cert_qlen, cert_xlow, cert_xcells,
        ctypes.byref(cert_ycells),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (keep, kc, ke)
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_q_zeilberger returned non-OK status {rc}")
    if not has.value:
        return False, 0, [], (0, [])
    order = int(order_out.value)
    n_coeff = int(coeff_count.value)
    # each coeff a single-X-cell QPoly: read its q-run, wrap as (x_low, [run]).
    coeff_forms = []
    off = 0
    for j in range(n_coeff):
        ln = int(coeff_qlen[j])
        run = [(_bigint_to_int(coeff_n[off + i]), _bigint_to_int(coeff_d[off + i]))
               for i in range(ln)]
        coeff_forms.append((int(coeff_xlow[j]), [run]))
        off += ln
    # the certificate QBiPoly: cert_ycells Y-cells, each a single X-cell here.
    ny = int(cert_ycells.value)
    cert_rows = []
    cert_y_xlow = []
    off = 0
    for yd in range(ny):
        ln = int(cert_qlen[yd])
        run = [(_bigint_to_int(cert_n[off + i]), _bigint_to_int(cert_d[off + i]))
               for i in range(ln)]
        cert_rows.append([run])
        cert_y_xlow.append(int(cert_xlow[yd]))
        off += ln
    return True, order, coeff_forms, (cert_y_xlow, cert_rows)


# ----------------------------------------------------------------------
# rc53: srmech_apagodu_zeilberger — the Apagodu-Zeilberger multivariate "sums of
# sums" creative telescoping (CLOSES the multivariate F929 row). The Python
# srmech.amsc.apagodu_zeilberger.apagodu_zeilberger routes a POSITIVE
# (recurrence-found) C result through this; a has=0 / error falls to the complete
# pure-Python path (the parity oracle + full-coverage decider). The three TRIVARIATE
# ratios + the recurrence + the two certificates ride the nested-bridge (j,k)-cell
# grid form (the same _tri_pairs form tripoly uses).
# ----------------------------------------------------------------------

_APAGODU_SYMS = (
    "srmech_apagodu_zeilberger_ws_bound",
    "srmech_apagodu_zeilberger_out_cap",
)


def has_native_apagodu_zeilberger() -> bool:
    """True iff the rc53 srmech_apagodu_zeilberger op + its ws/out-cap sizers are
    loaded + bound. False on a no-C or pre-rc53 lib — the pure-Python
    ``srmech.amsc.apagodu_zeilberger.apagodu_zeilberger`` body is the complete
    alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _APAGODU_SYMS) and hasattr(
        LIB, "srmech_apagodu_zeilberger"
    )


def _az_tri_flatten(tri_pairs):
    """A trivariate ``[[[(num,den), ...]_n]_k]_j`` (the ``TriPoly`` nested-bridge
    form) → ``(flat_pairs, nlen_list, jdeg, kdeg)`` where ``flat_pairs`` lists every
    coefficient in j-then-k-then-n order, ``nlen_list[dj*kdeg + dk]`` is the n-run
    length of cell ``(dj, dk)``, and ``(jdeg, kdeg)`` is the rectangular block shape
    (each j-block padded to the max k-degree across blocks so the grid is
    rectangular). The Apagodu–Zeilberger bridge flattener (distinct from the
    tripoly-carrier ``_tri_flatten`` which pads to a caller-given (aj, ak))."""
    jdeg = len(tri_pairs)
    kdeg = 0
    for kgrid in tri_pairs:
        if len(kgrid) > kdeg:
            kdeg = len(kgrid)
    if jdeg == 0 or kdeg == 0:
        return [], [], jdeg, kdeg
    flat = []
    nlen = []
    for kgrid in tri_pairs:
        for dk in range(kdeg):
            run = kgrid[dk] if dk < len(kgrid) else []
            nlen.append(len(run))
            flat.extend(run)
    return flat, nlen, jdeg, kdeg


def apagodu_zeilberger_c(rn_num, rn_den, rj_num, rj_den, rk_num, rk_den, max_order):
    """Native Apagodu-Zeilberger recurrence for the six trivariate term-ratio
    operands → ``(has, order, coeff_pairs, cert_j_blocks, cert_k_blocks)``
    (``coeff_pairs[i]`` the ascending-n ``(num,den)`` list of ``a_i(n)``;
    ``cert_*_blocks`` the nested ``[[[(num,den), …]_n]_k]_j`` bridge form of each
    certificate numerator), or ``None`` if the native symbols are absent. Each ratio
    operand is the ``_tri_pairs`` nested-bridge form. A non-OK status / inability
    raises ``RuntimeError`` so the caller falls to the pure path."""
    if not has_native_apagodu_zeilberger():
        return None
    flats = []
    nlens = []
    jdegs = []
    kdegs = []
    for tp in (rn_num, rn_den, rj_num, rj_den, rk_num, rk_den):
        f, nl, jd, kd = _az_tri_flatten(tp)
        flats.append(f)
        nlens.append(nl)
        jdegs.append(jd)
        kdegs.append(kd)
    if jdegs[1] == 0 or jdegs[3] == 0 or jdegs[5] == 0:
        raise ValueError(
            "apagodu_zeilberger_c: r_n / r_j / r_k denominators must be nonzero")
    deg = 1
    for jd, kd, nl in zip(jdegs, kdegs, nlens):
        deg = max(deg, jd, kd, max(nl) if nl else 1)
    cl = max((_qmat_coeff_limbs(f) if f else 1 for f in flats), default=1)
    out_cap = int(LIB.srmech_apagodu_zeilberger_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(max_order), ctypes.c_size_t(deg)))
    ws_len = int(LIB.srmech_apagodu_zeilberger_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(max_order), ctypes.c_size_t(deg)))
    # The dense exact-ℚ RREF arena for a multivariate AZ system swells with the
    # Hadamard fraction-growth bound (the swell the Python path dodges via the CRT
    # re-fibration rref_crt; the C dense path does not). Past a sane ceiling the C
    # peer would need a multi-hundred-MB arena, so we DECLINE to the bounded-memory
    # pure-Python CRT path (the standalone-complete honor — the C never returns a
    # false "no recurrence"; here it simply isn't invoked, and the pure path is the
    # decider). The dense-C accelerates the small textbook cases; a CRT-C re-fibration
    # is the owed everything-mirrors backfill for the wider systems.
    # The dense exact-ℚ RREF entry-cap (Hadamard fraction-growth bound) makes even
    # the smallest genuine double-sum system's caller arena hundreds of MB AND the
    # RREF slow; the Python rref_crt re-fibration is the bounded-memory accelerator.
    # So the C peer DECLINES past a modest arena ceiling (the standalone-complete
    # honor — it never returns a false "no recurrence"; the bounded-memory pure CRT
    # path is the decider). A CRT-C re-fibration of this kernel is the owed
    # everything-mirrors backfill (the QMat-CRT arc precedent). The ceiling is raisable
    # (SRMECH_AZ_WS_CEILING_MB) to exercise the C peer's execution-parity proof on a
    # box with the RAM for it.
    _ceiling_mb = 192
    try:
        _ceiling_mb = max(1, int(os.environ.get("SRMECH_AZ_WS_CEILING_MB", "192")))
    except (TypeError, ValueError):
        _ceiling_mb = 192
    if ws_len > _ceiling_mb * 1024 * 1024:
        return None
    try:
        ws = (ctypes.c_uint8 * max(ws_len, 8))()
    except (MemoryError, OverflowError):
        return None                            # decline to the pure CRT path
    in_arrays = []
    keep = []
    for f, nl, jd, kd in zip(flats, nlens, jdegs, kdegs):
        a_n, a_d, ka = _qmat_make_array(f, out_cap)
        nlen_arr = (ctypes.c_size_t * max(len(nl), 1))(*nl)
        in_arrays.append((a_n, a_d, nlen_arr, jd, kd))
        keep.append(ka)
        keep.append(nlen_arr)
    # output slots: coeff (order+1)*nbound ; each cert (cells)*(nbound). A generous
    # slot count; the C writes contiguously + reports per-segment lengths.
    nbound = (deg + 2) * (max_order + 2) + 8
    cells_bound = (deg + 4) * (deg + 4) + 8
    coeff_slots = (max_order + 1) * nbound + 8
    cert_slots = cells_bound * nbound + 8
    coeff_n, coeff_d, kc = _qmat_blank_array(coeff_slots, out_cap)
    cj_n, cj_d, kj = _qmat_blank_array(cert_slots, out_cap)
    ck_n, ck_d, kk = _qmat_blank_array(cert_slots, out_cap)
    coeff_nlen = (ctypes.c_size_t * (max_order + 2))()
    cj_nlen = (ctypes.c_size_t * (cells_bound + 2))()
    ck_nlen = (ctypes.c_size_t * (cells_bound + 2))()
    has = ctypes.c_int(0)
    order_out = ctypes.c_size_t(0)
    cj_jdeg = ctypes.c_size_t(0)
    cj_kdeg = ctypes.c_size_t(0)
    ck_jdeg = ctypes.c_size_t(0)
    ck_kdeg = ctypes.c_size_t(0)
    args = []
    for (a_n, a_d, nlen_arr, jd, kd) in in_arrays:
        args += [a_n, a_d, nlen_arr, ctypes.c_size_t(jd), ctypes.c_size_t(kd)]
    rc = LIB.srmech_apagodu_zeilberger(
        *args,
        ctypes.c_size_t(max_order), ctypes.c_size_t(deg),
        ctypes.byref(has), ctypes.byref(order_out),
        coeff_n, coeff_d, coeff_nlen,
        cj_n, cj_d, cj_nlen, ctypes.byref(cj_jdeg), ctypes.byref(cj_kdeg),
        ck_n, ck_d, ck_nlen, ctypes.byref(ck_jdeg), ctypes.byref(ck_kdeg),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = (keep, kc, kj, kk)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_apagodu_zeilberger returned non-OK status {rc}")
    if not has.value:
        return False, 0, [], [], []
    order = int(order_out.value)
    coeff_pairs = []
    off = 0
    for i in range(order + 1):
        ln = int(coeff_nlen[i])
        coeff_pairs.append([(_bigint_to_int(coeff_n[off + p]),
                             _bigint_to_int(coeff_d[off + p])) for p in range(ln)])
        off += ln

    def _read_cert(cn, cd, cnlen, jdeg, kdeg):
        blocks = []
        o = 0
        for dj in range(jdeg):
            kgrid = []
            for dk in range(kdeg):
                ln = int(cnlen[dj * kdeg + dk])
                kgrid.append([(_bigint_to_int(cn[o + p]),
                               _bigint_to_int(cd[o + p])) for p in range(ln)])
                o += ln
            blocks.append(kgrid)
        return blocks

    cert_j_blocks = _read_cert(cj_n, cj_d, cj_nlen, int(cj_jdeg.value),
                               int(cj_kdeg.value))
    cert_k_blocks = _read_cert(ck_n, ck_d, ck_nlen, int(ck_jdeg.value),
                               int(ck_kdeg.value))
    return True, order, coeff_pairs, cert_j_blocks, cert_k_blocks


# ----------------------------------------------------------------------
# rc43: srmech_wz_verify — the Wilf-Zeilberger VERIFY primitive (the §76 telescope
# Sigma-row's THIRD/FINAL public op). The Python srmech.amsc.wz_certificate routes
# its VERIFY half through this when has_native_wz_verify(); the pure-Python
# bivariate-Q polynomial compare is the COMPLETE alternative (and the parity oracle)
# — both decide the SAME exact rational-function identity. The six bivariate operands
# ride the same _SrmechBigint coefficient-array bridge (the _bi_flatten form) as
# zeilberger. This is a FULL C mirror (degree-bounded, no order cap): a definite 0/1
# result is trusted both ways.
# ----------------------------------------------------------------------

_WZ_SYMS = (
    "srmech_wz_verify_ws_bound",
    "srmech_wz_verify_out_cap",
)


def has_native_wz_verify() -> bool:
    """True iff the rc43 srmech_wz_verify op + its ws/out-cap sizers are loaded +
    bound. False on a no-C or pre-rc43 lib — the pure-Python
    ``srmech.amsc.wz_certificate`` verify body is the complete alternative (and the
    parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _WZ_SYMS) and hasattr(
        LIB, "srmech_wz_verify"
    )


def wz_verify_c(rn_num, rn_den, rk_num, rk_den, cert_num, cert_den):
    """Native WZ-equation verify for the six bivariate operands → ``True`` / ``False``
    (the WZ certificate identity holds / does not), or ``None`` if the native symbols
    are absent. Each operand is a bivariate-pairs structure (the ``_bi_pairs`` bridge
    form: a k-ascending list of ascending-n ``(num, den)`` lists). A non-OK status /
    inability raises ``RuntimeError`` so the caller falls to the pure path."""
    if not has_native_wz_verify():
        return None
    flats = []
    klens = []
    for bp in (rn_num, rn_den, rk_num, rk_den, cert_num, cert_den):
        f, k = _bi_flatten(bp)
        flats.append(f)
        klens.append(k)
    # r_n den / r_k den / cert den must be nonzero (kdeg > 0).
    if len(klens[1]) == 0 or len(klens[3]) == 0 or len(klens[5]) == 0:
        raise ValueError("wz_verify_c: r_n / r_k / cert denominators must be nonzero")
    deg = max((len(k) for k in klens), default=1)
    # the n-degree also drives the envelope: the max per-k n-coeff count across inputs.
    for k in klens:
        deg = max(deg, max((v for v in k), default=0))
    cl = max((_qmat_coeff_limbs(f) if f else 1 for f in flats), default=1)
    ws_len = int(LIB.srmech_wz_verify_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(deg)))
    out_cap = int(LIB.srmech_wz_verify_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(deg)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    in_arrays = []
    keep = []
    for f, k in zip(flats, klens):
        a_n, a_d, ka = _qmat_make_array(f, out_cap)
        klen_arr = (ctypes.c_size_t * max(len(k), 1))(*k)
        in_arrays.append((a_n, a_d, klen_arr, len(k)))
        keep.append(ka)
        keep.append(klen_arr)
    out_equal = ctypes.c_int(0)
    rc = LIB.srmech_wz_verify(
        in_arrays[0][0], in_arrays[0][1], in_arrays[0][2], ctypes.c_size_t(in_arrays[0][3]),
        in_arrays[1][0], in_arrays[1][1], in_arrays[1][2], ctypes.c_size_t(in_arrays[1][3]),
        in_arrays[2][0], in_arrays[2][1], in_arrays[2][2], ctypes.c_size_t(in_arrays[2][3]),
        in_arrays[3][0], in_arrays[3][1], in_arrays[3][2], ctypes.c_size_t(in_arrays[3][3]),
        in_arrays[4][0], in_arrays[4][1], in_arrays[4][2], ctypes.c_size_t(in_arrays[4][3]),
        in_arrays[5][0], in_arrays[5][1], in_arrays[5][2], ctypes.c_size_t(in_arrays[5][3]),
        ctypes.byref(out_equal),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = keep
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_wz_verify returned non-OK status {rc}")
    return bool(out_equal.value)


# ----------------------------------------------------------------------
# rc57: srmech_q_wz_verify — the q-analog of the Wilf-Zeilberger VERIFY primitive (the
# §76 q-hypergeometric F929 row's THIRD/FINAL public op, the q-row CLOSER). The Python
# srmech.amsc.q_wz_certificate routes its VERIFY half through this when
# has_native_q_wz_verify(); the pure-Python bivariate-Q[q] polynomial compare is the
# COMPLETE alternative (and the parity oracle) — both decide the SAME exact rational-
# function identity. The six bivariate-q operands ride the SAME QBiPoly coefficient
# bridge (the _qbi_flatten form) as q_zeilberger. This is a FULL C mirror (degree-
# bounded, no order cap): a definite 0/1 result is trusted both ways.
# ----------------------------------------------------------------------

_Q_WZ_SYMS = (
    "srmech_q_wz_verify_ws_bound",
    "srmech_q_wz_verify_out_cap",
    "srmech_bigint_from_dec",
    "srmech_bigint_to_dec",
    "srmech_bigint_to_dec_bound",
)


def has_native_q_wz_verify() -> bool:
    """True iff the rc57 srmech_q_wz_verify op + its ws/out-cap sizers + the
    srmech_bigint decimal-marshal helpers are loaded + bound. False on a no-C or
    pre-rc57 lib — the pure-Python ``srmech.amsc.q_wz_certificate`` verify body is the
    complete alternative (and the parity oracle)."""
    if not (HAS_NATIVE and LIB is not None):
        return False
    return all(hasattr(LIB, s) for s in _Q_WZ_SYMS) and hasattr(
        LIB, "srmech_q_wz_verify"
    )


def _qbi_degree(form):
    """The max bivariate-q degree of a QBiPoly bridge form ``(y_xlow[], rows)`` — the
    larger of the Y-cell count, the max X-cell count, and the max q-run length across
    all cells (the per-dimension envelope the C sizer consumes as a single hint)."""
    _y, rows = form
    deg = len(rows)
    for xrow in rows:
        if len(xrow) > deg:
            deg = len(xrow)
        for run in xrow:
            if len(run) > deg:
                deg = len(run)
    return deg


def q_wz_verify_c(rn_num, rn_den, rk_num, rk_den, cert_num, cert_den):
    """Native q-WZ-equation verify for the six bivariate-q operands → ``True`` /
    ``False`` (the q-WZ certificate identity holds / does not), or ``None`` if the
    native symbols are absent. Each operand is a QBiPoly ``(y_xlow[], rows)`` bridge
    form (the SAME form q_zeilberger marshals). A non-OK status / inability raises
    ``RuntimeError`` so the caller falls to the pure path."""
    if not has_native_q_wz_verify():
        return None
    forms = (rn_num, rn_den, rk_num, rk_den, cert_num, cert_den)
    # r_n den / r_k den / cert den must be nonzero (ycells > 0).
    if not rn_den[1] or not rk_den[1] or not cert_den[1]:
        raise ValueError(
            "q_wz_verify_c: r_n / r_k / cert denominators must be nonzero")
    cl = max(_qbi_row_coeff_limbs(f) for f in forms)
    deg = max(_qbi_degree(f) for f in forms)
    if deg < 1:
        deg = 1
    ws_len = int(LIB.srmech_q_wz_verify_ws_bound(
        ctypes.c_size_t(cl), ctypes.c_size_t(deg)))
    out_cap = int(LIB.srmech_q_wz_verify_out_cap(
        ctypes.c_size_t(cl), ctypes.c_size_t(deg)))
    ws = (ctypes.c_uint8 * max(ws_len, 8))()
    keep = []
    in_args = []
    for f in forms:
        nn, dd, ql, xl, xc, yc, k = _qbi_flatten(f, out_cap)
        in_args += [nn, dd, ql, xl, xc, ctypes.c_size_t(yc)]
        keep.append(k)
    out_equal = ctypes.c_int(0)
    rc = LIB.srmech_q_wz_verify(
        *in_args,
        ctypes.byref(out_equal),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    _ = keep
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_q_wz_verify returned non-OK status {rc}")
    return bool(out_equal.value)


def has_native_klein4_fold() -> bool:
    """True iff the §50 native Klein-4 co-occurrence fold is loaded + bound
    (rc165+ lib): the corpus-linear windowed accumulation runs in C, so
    :func:`srmech.amsc.hdc.cooccurrence_fold` builds the holographic store at
    corpus scale (the §50.1 loopshelf/tome-leaf precondition). False on a no-C
    or pre-rc165 lib — the pure-Python fold is the complete alternative."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_klein4_cooccurrence_fold")
                and hasattr(LIB, "srmech_klein4_bundle_accumulate"))


def has_native_klein4_bind() -> bool:
    """True iff the Class-M klein4 CORE primitives — bind / bundle / similarity —
    are loaded + bound (UPSTREAM §53 / F818). The C (sector XOR-bind, per-bit
    majority-bundle, Hamming/sector similarity) ships in libsrmech and is
    ctypes-bound; this gates the dispatch in :func:`srmech.amsc.hdc.klein4_bind`
    / :func:`~srmech.amsc.hdc.klein4_bundle` / :func:`~srmech.amsc.hdc.klein4_similarity`.
    The native path is ~100–1000× the pure-Python one at HDC dimension D≈10⁴, so a
    per-token HDC content-addressed walk (the F808 RBS-HDC recall) becomes viable
    as the live engine. False on a no-C lib — pure-Python is the complete
    alternative (bit-identical)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_klein4_bind")
                and hasattr(LIB, "srmech_klein4_bundle")
                and hasattr(LIB, "srmech_klein4_similarity"))


def has_native_klein4_triality_cycle() -> bool:
    """True iff the Class-I klein4 order-3 triality cycle is loaded + bound
    (UPSTREAM §53 / F818, the last ``c_exists_unbound`` klein4 op). The C
    ``srmech_klein4_triality_cycle(in, n, inverse, out)`` — the order-3
    S₃ = Aut(V₄) relabel (iω₇→γ₅→CPT→iω₇, identity fixed; the V₄-carrier image
    of the so(8) 8v→8s→8c triality) — ships in libsrmech with the SAME forward /
    inverse 3-cycle tables as the pure-Python op, so the native path is
    bit-identical. Gates the dispatch in
    :func:`srmech.amsc.hdc.klein4_triality_cycle`. False on a no-C lib — the
    pure-Python relabel is the complete alternative."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_klein4_triality_cycle"))


def has_native_fiedler_sparse() -> bool:
    """True iff the §51 native sparse normalized-cut Fiedler is loaded + bound
    (rc166+ lib): the matvec power iteration runs in C (n unbounded, caller-
    arena, no caps), so :func:`srmech.amsc.laplacian.fiedler_sparse` /
    :func:`~srmech.amsc.laplacian.normalized_cut_bisect` partition a >256-node
    graph past the dense-eigensolver wall (issue #1097). False on a no-C or
    pre-rc166 lib — the pure-Python cascade is the complete alternative."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_laplacian_fiedler_sparse"))


def has_native_fiedler_sparse_file() -> bool:
    """True iff the §52 Part 2 native OUT-OF-CORE streaming Fiedler is loaded +
    bound (rc168+ lib): the matvec power iteration runs in C reading the
    adjacency from a packed edge FILE via the PAL — only the O(n) working
    vectors are resident, so :func:`srmech.amsc.laplacian.fiedler_sparse_file`
    partitions a graph whose edge list does not fit RAM (F793 low-RAM encode).
    False on a no-C or pre-rc168 lib — the pure-Python path (read the file in,
    run the in-RAM cascade) is the complete alternative (correct, not bounded)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_laplacian_fiedler_sparse_file"))


# ---------------------------------------------------------------------------
# Config layer (rc161). The Hermitian-eig compute-guard ceiling is a runtime
# config value in the C library (default 2048, raisable), not a compiled-in
# cap. These thin wrappers expose the getter (the authority for the native
# dispatch gate) + the TOML loaders. A config set here is process-wide native
# policy; with no native lib it is a no-op (the pure-Python Jacobi fallback
# has no ceiling), and the getter returns the built-in default.
# ---------------------------------------------------------------------------
HERMITIAN_DEFAULT_MAX_NODES: int = 2048  # mirrors C SRMECH_HERMITIAN_DEFAULT_MAX_NODES


def has_native_config() -> bool:
    """True iff the C config layer is loaded + bound (rc161+ lib)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_config_hermitian_max_nodes"))


def config_hermitian_max_nodes() -> int:
    """The live config-driven Hermitian-eig node ceiling.

    Native authority when present (``srmech_config_hermitian_max_nodes()``);
    otherwise the built-in default (the native ceiling is irrelevant with no
    native lib — pure-Python Jacobi has no cap)."""
    if has_native_config():
        return int(LIB.srmech_config_hermitian_max_nodes())
    return HERMITIAN_DEFAULT_MAX_NODES


def config_reset_defaults() -> None:
    """Reset the native config to built-in defaults (no-op with no native lib)."""
    if HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_config_reset_defaults"):
        LIB.srmech_config_reset_defaults()


def _config_ws(extra: int = 0):
    """A 64 KiB ctypes scratch arena for a config parse (caller-arena, no malloc
    in C). 64 KiB dwarfs any realistic limits TOML; `extra` pads the file form
    where the front half also buffers the file bytes."""
    return (ctypes.c_char * (65536 + extra))()


def config_load_toml(toml_text: str) -> None:
    """Apply a TOML config blob to the native limits (no-op with no native lib).

    Raises RuntimeError on a parse/apply failure (non-OK C status)."""
    if not (HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_config_load_toml")):
        return
    raw = toml_text.encode("utf-8")
    ws = _config_ws()
    rc = LIB.srmech_config_load_toml(
        raw, ctypes.c_size_t(len(raw)),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(len(ws)),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_config_load_toml returned non-OK status {rc}")


def config_load_file(path: str) -> None:
    """Read + apply a TOML config FILE through the PAL (no-op with no native lib).

    Raises RuntimeError on read/parse failure (non-OK C status)."""
    if not (HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_config_load_file")):
        return
    # The C side carves the file-read buffer from the front half of ws; size it
    # generously so even a large descriptor file fits alongside the parse arena.
    ws = _config_ws(extra=65536)
    rc = LIB.srmech_config_load_file(
        path.encode("utf-8"),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(len(ws)),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_config_load_file returned non-OK status {rc}")


def _scalar_trans_c(symbol: str, x: float) -> float:
    """Call a single-arg C transcendental ``srmech_<symbol>(double, double*)``."""
    if not HAS_NATIVE or LIB is None or not hasattr(LIB, symbol):
        raise RuntimeError(
            f"{symbol} unavailable; guard calls with _native.has_native_trig()")
    out = ctypes.c_double()
    rc = getattr(LIB, symbol)(ctypes.c_double(x), ctypes.byref(out))
    if rc != SRMECH_OK:
        raise RuntimeError(f"{symbol} returned non-OK status {rc}")
    return out.value


def sin_c(x: float) -> float:
    return _scalar_trans_c("srmech_sin", x)


def cos_c(x: float) -> float:
    return _scalar_trans_c("srmech_cos", x)


def atan_c(x: float) -> float:
    return _scalar_trans_c("srmech_atan", x)


def exp_c(x: float) -> float:
    return _scalar_trans_c("srmech_exp", x)


def log_c(x: float) -> float:
    return _scalar_trans_c("srmech_log", x)


def rational_sqrt_c(x: float) -> float:
    return _scalar_trans_c("srmech_rational_sqrt", x)


# ----------------------------------------------------------------------
# 0.9.0rc7 stay-rational Q61 dispatch (F868). These return the EXACT int64 Q61
# pieces the C cascade computes BEFORE its float projection, so the Python
# ``rational.{sin,cos,atan,exp,log,sqrt}`` dispatch to native AND keep the full
# 61-bit rational (``Q``), not a 52-bit double promoted back. A non-finite /
# out-of-Q61-range argument -> SRMECH_ERR_BAD_INPUT -> ValueError (the pure-Python
# peer raises identically). Byte-exact with the pure cascade (10047/10047 checks).
# ----------------------------------------------------------------------
def has_native_trans_q61() -> bool:
    """True iff the C Q61 transcendental peers are loaded + bound (0.9.0rc7+)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_sin_q61")
                and hasattr(LIB, "srmech_exp_q61")
                and hasattr(LIB, "srmech_sqrt_q61"))


def _q61_one_out(symbol: str, x: float) -> int:
    out = ctypes.c_int64()
    rc = getattr(LIB, symbol)(ctypes.c_double(x), ctypes.byref(out))
    if rc != SRMECH_OK:
        raise ValueError(f"{symbol}: argument has no Q61 rational (status {rc})")
    return out.value


def _q61_two_out(symbol: str, x: float):
    a = ctypes.c_int64()
    b = ctypes.c_int64()
    rc = getattr(LIB, symbol)(
        ctypes.c_double(x), ctypes.byref(a), ctypes.byref(b))
    if rc != SRMECH_OK:
        raise ValueError(f"{symbol}: argument has no Q61 rational (status {rc})")
    return a.value, b.value


def sin_q61_c(x: float) -> int:
    """``sin(x)`` numerator over ``2**61`` (int64)."""
    return _q61_one_out("srmech_sin_q61", x)


def cos_q61_c(x: float) -> int:
    """``cos(x)`` numerator over ``2**61`` (int64)."""
    return _q61_one_out("srmech_cos_q61", x)


def atan_q61_c(x: float) -> int:
    """``atan(x)`` numerator over ``2**61`` (int64)."""
    return _q61_one_out("srmech_atan_q61", x)


def exp_q61_c(x: float):
    """``exp(x) = (core / 2**61) * 2**n`` -> ``(core, n)`` (both int64)."""
    return _q61_two_out("srmech_exp_q61", x)


def log_q61_c(x: float):
    """``log(x) = (logm + e*ln2) / 2**61`` -> ``(logm, e)`` (both int64)."""
    return _q61_two_out("srmech_log_q61", x)


def sqrt_q61_c(x: float):
    """``sqrt(x) = root * 2**p`` -> ``(root, p)`` (both int64)."""
    return _q61_two_out("srmech_sqrt_q61", x)


def has_native_next_prime() -> bool:
    """True iff the rc44 srmech_next_prime prime-successor peer is loaded + bound.
    False on a no-C / pre-rc44 lib — the pure-Python ``primes.next_prime`` body
    (composing ``is_prime`` over odd candidates) is the complete alternative."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_next_prime"))


def has_native_gf_rref() -> bool:
    """True iff the rc44 srmech_gf_rref GF(p) RREF kernel is loaded + bound.
    False on a no-C / pre-rc44 lib — the pure-Python
    ``modular_linalg.gf_rref`` body (composing the Class-I modular primitives) is
    the complete, byte-identical alternative (and the parity oracle)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_gf_rref"))


def has_native_crt_combine() -> bool:
    """True iff the rc45 srmech_crt_combine CRT-combine peer (over srmech_bigint)
    is loaded + bound. False on a no-C / pre-rc45 lib — the pure-Python
    ``modular_linalg.crt_combine`` body (iterative Garner CRT) is the complete,
    byte-identical alternative (and the parity oracle)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_crt_combine")
                and hasattr(LIB, "srmech_crt_combine_ws_bound")
                and hasattr(LIB, "srmech_bigint_to_dec")
                and hasattr(LIB, "srmech_bigint_to_dec_bound"))


def has_native_rational_reconstruct() -> bool:
    """True iff the rc45 srmech_rational_reconstruct peer (over srmech_bigint) is
    loaded + bound. False on a no-C / pre-rc45 lib — the pure-Python
    ``rational.rational_reconstruct`` body (half-GCD / Wang reconstruction) is the
    complete, byte-identical alternative (and the parity oracle)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_rational_reconstruct")
                and hasattr(LIB, "srmech_rational_reconstruct_ws_bound")
                and hasattr(LIB, "srmech_bigint_from_dec")
                and hasattr(LIB, "srmech_bigint_to_dec")
                and hasattr(LIB, "srmech_bigint_to_dec_bound"))


def crt_combine(residues, moduli):
    """Native CRT-combine: ``(residue, modulus)`` or ``None`` if the native
    symbol is absent (the pure-Python Garner body is the complete fallback).

    ``residues`` / ``moduli`` are equal-length lists of non-negative ``int``,
    each ``< 2**64`` (the ~31-bit reduction primes + their residues fit uint64).
    The combined modulus + residue are bignum (no ceiling); they ride the
    srmech_bigint decimal marshal back to a Python ``int``."""
    if not has_native_crt_combine():
        return None
    k = len(moduli)
    if k == 0:
        return None
    _U64_MAX = (1 << 64) - 1
    for v in residues:
        if v < 0 or v > _U64_MAX:
            return None
    for v in moduli:
        if v < 0 or v > _U64_MAX:
            return None
    res_arr = (ctypes.c_uint64 * k)(*residues)
    mod_arr = (ctypes.c_uint64 * k)(*moduli)
    # Combined modulus is ∏ m_i; size the out carriers from the total bit-width.
    total_bits = 0
    for m in moduli:
        total_bits += m.bit_length()
    out_cap = total_bits // 32 + 8
    out_residue, _orl = _bigint_from_int(0, out_cap)
    out_modulus, _oml = _bigint_from_int(0, out_cap)
    ws_len = int(LIB.srmech_crt_combine_ws_bound(ctypes.c_size_t(k)))
    # The Garner fold's scratch grows with the partial-product limb count; the
    # ws_bound returns a generous BYTES envelope already, but pad for safety.
    ws_len = max(ws_len, (out_cap * 8 + 64) * 8)
    ws = (ctypes.c_uint8 * ws_len)()
    rc = LIB.srmech_crt_combine(
        res_arr, mod_arr, ctypes.c_uint32(k),
        ctypes.byref(out_residue), ctypes.byref(out_modulus),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_crt_combine returned non-OK status {rc}")
    return _bigint_to_int(out_residue), _bigint_to_int(out_modulus)


def rational_reconstruct(residue: int, modulus: int,
                         num_bound: int, den_bound: int):
    """Native rational reconstruction: ``(p, q)``, ``(None, None)`` for the
    no-reconstruction case, or ``None`` if the native symbol is absent (the
    pure-Python half-GCD body is the complete fallback).

    All four inputs are arbitrary-precision ``int`` (the modulus + recovered
    p/q can exceed ``2**64``); they ride the srmech_bigint decimal bridge."""
    if not has_native_rational_reconstruct():
        return None
    # Limb sizing from the widest operand (the modulus dominates).
    mod_digits = len(str(modulus))
    out_cap = mod_digits // 9 + 8
    res_bi, _rl = _bigint_from_int(residue, out_cap)
    mod_bi, _ml = _bigint_from_int(modulus, out_cap)
    nb_bi, _nl = _bigint_from_int(num_bound, out_cap)
    db_bi, _dl = _bigint_from_int(den_bound, out_cap)
    out_num, _onl = _bigint_from_int(0, out_cap)
    out_den, _odl = _bigint_from_int(0, out_cap)
    found = ctypes.c_int32(0)
    mod_limbs = mod_bi.n if mod_bi.n else 1
    ws_len = int(LIB.srmech_rational_reconstruct_ws_bound(
        ctypes.c_size_t(mod_limbs)))
    ws_len = max(ws_len, (out_cap * 12 + 64) * 4)
    ws = (ctypes.c_uint8 * ws_len)()
    rc = LIB.srmech_rational_reconstruct(
        ctypes.byref(res_bi), ctypes.byref(mod_bi),
        ctypes.byref(nb_bi), ctypes.byref(db_bi),
        ctypes.byref(out_num), ctypes.byref(out_den),
        ctypes.byref(found),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(ws_len),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_rational_reconstruct returned non-OK status {rc}"
        )
    if found.value == 0:
        return (None, None)
    return _bigint_to_int(out_num), _bigint_to_int(out_den)


def has_native_isqrt() -> bool:
    """True iff the C 128-bit integer floor-sqrt is loaded + bound (0.9.0rc13+)."""
    return bool(HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_isqrt"))


def isqrt128_c(n: int) -> int:
    """``floor(sqrt(n))`` for ``0 <= n < 2**128`` via the native two-limb isqrt.

    Splits ``n`` into 64-bit hi/lo limbs and dispatches ``srmech_isqrt``; the
    Python ``rational._integer_sqrt`` uses this for the bounded radicand and an
    arbitrary-precision integer-Newton fallback beyond 128 bits. Raises if ``n``
    is out of the 128-bit domain (the caller gates on that)."""
    if n < 0 or n >= (1 << 128):
        raise ValueError("isqrt128_c: n must be in [0, 2**128)")
    out = ctypes.c_uint64()
    rc = LIB.srmech_isqrt(
        ctypes.c_uint64(n >> 64), ctypes.c_uint64(n & ((1 << 64) - 1)),
        ctypes.byref(out))
    if rc != SRMECH_OK:
        raise ValueError(f"srmech_isqrt: status {rc}")
    return out.value


# ──────────────────────────────────────────────────────────────────────
# Qi — the exact-complex (Gaussian-rational) carrier C-host peer (0.9.0rc15).
# Carrier-internal (NOT a Rosetta op). Four int64 limbs {re_num, re_den,
# im_num, im_den}; the wrappers return None when native is absent / a limb is
# out of the int64 domain / an intermediate overflowed (the Python `Qi`
# exact-Fraction path is the unbounded oracle) — mirroring the
# `rational._try_c_two_rationals` precedent.
# ──────────────────────────────────────────────────────────────────────
_QI_I64_MAX: int = (1 << 63) - 1
_QI_I64_MIN: int = -(1 << 63)


def has_native_qi() -> bool:
    """True iff the C Qi exact-complex carrier peer is loaded + bound (0.9.0rc15+)."""
    return bool(HAS_NATIVE and LIB is not None and hasattr(LIB, "srmech_qi_mul"))


def _qi_limbs_fit(v) -> bool:
    """True iff the 4 limbs (re_num, re_den, im_num, im_den) fit signed int64
    with positive denominators — the native int64-limb domain."""
    return (_QI_I64_MIN <= v[0] <= _QI_I64_MAX and 0 < v[1] <= _QI_I64_MAX
            and _QI_I64_MIN <= v[2] <= _QI_I64_MAX and 0 < v[3] <= _QI_I64_MAX)


def _qi_binop_c(symbol: str, a, b):
    """Native (a `symbol` b) for two 4-limb Qi vectors → a 4-tuple, or None if
    native is absent / a limb is out of domain / an intermediate overflowed
    int64 (caller falls through to the exact-Fraction path)."""
    if not has_native_qi() or not _qi_limbs_fit(a) or not _qi_limbs_fit(b):
        return None
    a_arr = (ctypes.c_int64 * 4)(*a)
    b_arr = (ctypes.c_int64 * 4)(*b)
    out = (ctypes.c_int64 * 4)()
    rc = getattr(LIB, symbol)(a_arr, b_arr, out)
    if rc == SRMECH_OK:
        return (out[0], out[1], out[2], out[3])
    if rc in (SRMECH_ERR_OVERFLOW, SRMECH_ERR_BAD_INPUT):
        return None
    raise RuntimeError(f"{symbol} returned non-OK status {rc}")


def qi_add_c(a, b):
    """Native Qi add (a + b) as a 4-limb tuple, or None (out of int64 domain)."""
    return _qi_binop_c("srmech_qi_add", a, b)


def qi_sub_c(a, b):
    """Native Qi sub (a − b) as a 4-limb tuple, or None (out of int64 domain)."""
    return _qi_binop_c("srmech_qi_sub", a, b)


def qi_mul_c(a, b):
    """Native Qi mul (a · b) as a 4-limb tuple, or None (out of int64 domain)."""
    return _qi_binop_c("srmech_qi_mul", a, b)


def qi_conjugate_c(a):
    """Native Qi conjugate as a 4-limb tuple, or None (out of int64 domain)."""
    if not has_native_qi() or not _qi_limbs_fit(a):
        return None
    a_arr = (ctypes.c_int64 * 4)(*a)
    out = (ctypes.c_int64 * 4)()
    rc = LIB.srmech_qi_conjugate(a_arr, out)
    if rc == SRMECH_OK:
        return (out[0], out[1], out[2], out[3])
    if rc in (SRMECH_ERR_OVERFLOW, SRMECH_ERR_BAD_INPUT):
        return None
    raise RuntimeError(f"srmech_qi_conjugate returned non-OK status {rc}")


def qi_quadrant_c(a):
    """Native Qi Klein-4 quadrant (int 0..3), or None (out of int64 domain)."""
    if not has_native_qi() or not _qi_limbs_fit(a):
        return None
    a_arr = (ctypes.c_int64 * 4)(*a)
    out = ctypes.c_int(0)
    rc = LIB.srmech_qi_quadrant(a_arr, ctypes.byref(out))
    if rc == SRMECH_OK:
        return out.value
    if rc in (SRMECH_ERR_OVERFLOW, SRMECH_ERR_BAD_INPUT):
        return None
    raise RuntimeError(f"srmech_qi_quadrant returned non-OK status {rc}")


def qi_norm_sq_c(a):
    """Native Qi |a|² as a (num, den) tuple, or None (out of int64 domain)."""
    if not has_native_qi() or not _qi_limbs_fit(a):
        return None
    a_arr = (ctypes.c_int64 * 4)(*a)
    out = (ctypes.c_int64 * 2)()
    rc = LIB.srmech_qi_norm_sq(a_arr, out)
    if rc == SRMECH_OK:
        return (out[0], out[1])
    if rc in (SRMECH_ERR_OVERFLOW, SRMECH_ERR_BAD_INPUT):
        return None
    raise RuntimeError(f"srmech_qi_norm_sq returned non-OK status {rc}")


def has_native_hypercomplex_couple() -> bool:
    """True iff the C exact-Q61 (σ,θ,μ) octonion coupler peer is loaded (0.9.0rc16+)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_hypercomplex_couple_q61"))


def hypercomplex_couple_q61_c(streams8, mu8, eff: float, form_is_left: bool):
    """Native exact-Q61 octonion couple ``T ⊗ q`` → 8 Q61 ints, where ``T =
    exp(eff·μ) = cos eff + sin eff·μ`` and ``⊗`` is left/right octonion multiply.
    ``streams8`` / ``mu8`` are 8 Q61 ints; byte-exact with the pure path.

    Returns ``None`` when a stream limb is outside the int64 Q61 domain
    (``|stream| > 1`` → ``SRMECH_ERR_OVERFLOW``; no bignum in C): the caller's
    pure-Python path (bignum-exact) is the complete alternative — the documented
    native domain ceiling, like ``rational._try_c_two_rationals``."""
    s = (ctypes.c_int64 * 8)(*streams8)
    m = (ctypes.c_int64 * 8)(*mu8)
    out = (ctypes.c_int64 * 8)()
    rc = LIB.srmech_hypercomplex_couple_q61(
        ctypes.c_double(eff), s, m, ctypes.c_int(1 if form_is_left else 0), out)
    if rc == SRMECH_ERR_OVERFLOW:
        return None
    if rc != SRMECH_OK:
        raise ValueError(f"srmech_hypercomplex_couple_q61: status {rc}")
    return [out[i] for i in range(8)]


def has_native_hypercomplex_exp() -> bool:
    """True iff the C hypercomplex exp(μθ) twiddle peer is loaded (0.9.0rc10+)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_hypercomplex_exp_q61"))


def hypercomplex_exp_q61_c(theta: float, k_axes: int):
    """``exp(μθ) = cos θ + μ·sin θ`` (μ unit pure-imaginary over the first
    ``k_axes`` octonion axes, ``k_axes ∈ {1,3,7}``) → a list of 8 Q61 int64
    components over ``2**61`` (out8[0]=cos θ, out8[1..k]=sin θ/√k, rest 0)."""
    out = (ctypes.c_int64 * 8)()
    rc = LIB.srmech_hypercomplex_exp_q61(
        ctypes.c_double(theta), ctypes.c_int(int(k_axes)), out)
    if rc != SRMECH_OK:
        raise ValueError(
            f"srmech_hypercomplex_exp_q61: theta non-finite or k_axes not in "
            f"{{1,3,7}} (status {rc})")
    return [out[i] for i in range(8)]


def atan2_c(y: float, x: float) -> float:
    """Call ``srmech_atan2(double y, double x, double *out)`` (rc43)."""
    if not HAS_NATIVE or LIB is None or not hasattr(LIB, "srmech_atan2"):
        raise RuntimeError(
            "srmech_atan2 unavailable; guard with _native.has_native_trig()")
    out = ctypes.c_double()
    rc = LIB.srmech_atan2(
        ctypes.c_double(y), ctypes.c_double(x), ctypes.byref(out))
    if rc != SRMECH_OK:
        raise RuntimeError(f"srmech_atan2 returned non-OK status {rc}")
    return out.value


def sha256_batch_c(datas: "list[bytes]") -> "list[str]":
    """Native N-way SIMD SHA-256 of many messages (F292 graft #1).

    Returns a list of 64-char lowercase hex digests, one per input — each
    byte-identical to ``hashlib.sha256(d).hexdigest()``. On x86 the native
    peer dispatches to AVX2 8-way / SSE2 4-way; the per-message result is
    bit-exact with the single-stream ``sha256_hex_c``.

    Must only be called when ``HAS_NATIVE`` is True AND the lib carries the
    rc10 symbol (a stale pre-rc10 lib lacks it; callers fall back to a
    hashlib loop in ``srmech.amsc.format.sha256_batch``).
    """
    if not HAS_NATIVE or LIB is None or not hasattr(LIB, "srmech_sha256_batch"):
        raise RuntimeError(
            "srmech.amsc._native.sha256_batch_c called but the native "
            "srmech_sha256_batch symbol is unavailable; use "
            "srmech.amsc.format.sha256_batch (which dispatches correctly)"
        )
    n = len(datas)
    if n == 0:
        return []
    keep = []  # keep per-message buffers alive across the call
    ptrs = (ctypes.POINTER(ctypes.c_uint8) * n)()
    lens = (ctypes.c_size_t * n)()
    for i, d in enumerate(datas):
        b = bytes(d)
        if len(b) == 0:
            ptrs[i] = ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
            lens[i] = ctypes.c_size_t(0)
        else:
            buf = (ctypes.c_uint8 * len(b)).from_buffer_copy(b)
            keep.append(buf)
            ptrs[i] = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8))
            lens[i] = ctypes.c_size_t(len(b))
    out = (ctypes.c_uint8 * (n * 32))()
    rc = LIB.srmech_sha256_batch(
        ptrs, lens, ctypes.c_size_t(n),
        ctypes.cast(out, ctypes.POINTER(ctypes.c_uint8)),
    )
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_sha256_batch returned non-OK status {rc}; "
            f"this should not happen for valid inputs"
        )
    return [bytes(out[i * 32:(i + 1) * 32]).hex() for i in range(n)]


def sha256_shani_c(data: bytes) -> str:
    """Native SHA-NI single-stream SHA-256 (F292 graft #3).

    Returns the 64-char lowercase hex digest, byte-identical to
    ``hashlib.sha256(data).hexdigest()`` / ``sha256_hex_c``. On x86 hosts
    that carry the SHA feature this runs the SHA-NI rnds2/msg1/msg2 kernel;
    elsewhere it runs the scalar path *inside the C call* (so the result is
    correct on every host). Must only be called when ``HAS_NATIVE`` is True
    AND the lib carries the rc18 symbol (a stale lib lacks it; callers fall
    back via ``srmech.amsc.format.sha256_bytes``).
    """
    if not HAS_NATIVE or LIB is None or not hasattr(LIB, "srmech_sha256_shani"):
        raise RuntimeError(
            "srmech.amsc._native.sha256_shani_c called but the native "
            "srmech_sha256_shani symbol is unavailable; use "
            "srmech.amsc.format.sha256_bytes (which dispatches correctly)"
        )
    out = (ctypes.c_uint8 * 32)()
    out_ptr = ctypes.cast(out, ctypes.POINTER(ctypes.c_uint8))
    if len(data) == 0:
        rc = LIB.srmech_sha256_shani(
            ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8)),
            ctypes.c_size_t(0),
            out_ptr,
        )
    else:
        buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        rc = LIB.srmech_sha256_shani(buf, ctypes.c_size_t(len(data)), out_ptr)
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_sha256_shani returned non-OK status {rc}; "
            f"this should not happen for valid inputs"
        )
    return bytes(out).hex()


def has_shani() -> "bool | None":
    """Does THIS run's host carry the Intel SHA Extensions (SHA-NI)?

    Returns ``True`` / ``False`` from the native cpuid probe
    (``srmech_simd_has_shani``), or ``None`` if the native lib / the rc18
    probe symbol is unavailable (so callers can distinguish "host lacks
    SHA-NI" from "can't tell"). Surfaced so the SHA-NI parity test can be
    exercise-if-present / skip-with-log rather than silently assuming
    coverage, and so ``native_status()`` can report build capability.
    """
    if not HAS_NATIVE or LIB is None or not hasattr(LIB, "srmech_simd_has_shani"):
        return None
    return bool(LIB.srmech_simd_has_shani())


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


def cascade_parallel_sector_dispatch_c(body, x, n_sectors: int = 4) -> list:
    """Native Klein-4 four-sector dispatch — must only be called when
    ``HAS_NATIVE`` is True (#771; the C peer of the rc6 Python
    ``parallel_sector_dispatch``).

    Runs the cascade ``body`` (a unary callable mapping a float sequence
    to a float sequence) across its ``n_sectors`` (1..4) Klein-4
    chirality sectors and returns ``[sector0, sector1, ...]`` — a list of
    length ``n_sectors`` whose element ``s`` is the sector dual
    ``T_s(body(T_s(x)))`` as a ``list[float]``.

    CONCURRENT (v0.6.0rc8 — the serial-shim slowdown fix). This drives
    the C dispatch with ONE ``n_sectors=N`` call: the C side spawns up to
    ``N`` threads (pthread / CreateThread), applies the Klein-4 ``T_s``
    transform itself (via the C atoms ``srmech_cascade_reorient_f64`` /
    ``srmech_cascade_chiral_flip_f64`` on disjoint per-sector slices), and
    invokes ``body`` from EACH thread. ``body`` is wrapped as a ctypes
    ``CFUNCTYPE``; ctypes acquires the GIL (``PyGILState_Ensure``) for the
    callback, so calling it from the C-spawned threads is SAFE. Because
    srmech's ``CDLL`` releases the GIL across the dispatch call, a
    GIL-RELEASING body (native / IO / numpy / sleep) lets the ``<=N``
    sector callbacks genuinely OVERLAP (measured ~4x on a sleep body). A
    CPU-bound pure-Python body is GIL-serialised across threads (the
    inherent CPython limit) — correct, just not faster.

    Earlier (rc7) this shim ran ``N`` serial ``n_sectors=1`` calls to
    avoid a (mistaken) GIL/callback hazard — that traded away ALL the
    concurrency (0.99x vs serial). The hazard was empirically disproven;
    the single ``n_sectors=N`` call is both safe and the F233 4-thread
    speedup as shipped (#778 / #771).

    The result is bit-identical to the rc6 Python
    ``parallel_sector_dispatch`` (the sectors are independent /
    order-free, the F233 invariant).

    Raises ``RuntimeError`` if ``HAS_NATIVE`` is False, ``ValueError``
    for ``n_sectors`` out of 1..4, or ``RuntimeError`` on a non-OK
    native status; any exception the body raises propagates out.
    """
    if not HAS_NATIVE or LIB is None:
        raise RuntimeError(
            "srmech.amsc._native.cascade_parallel_sector_dispatch_c called "
            "but HAS_NATIVE is False"
        )
    if not hasattr(LIB, "srmech_cascade_parallel_sector_dispatch"):
        raise RuntimeError(
            "native lib lacks srmech_cascade_parallel_sector_dispatch "
            "(stale dll; rebuild)"
        )
    if not isinstance(n_sectors, int) or isinstance(n_sectors, bool):
        raise ValueError(f"n_sectors must be an int; got {type(n_sectors).__name__}")
    if n_sectors < 1 or n_sectors > 4:
        raise ValueError(f"n_sectors must be in 1..4; got {n_sectors}")

    xs = [float(v) for v in x]
    n = len(xs)
    total = n_sectors * n
    DblIn = ctypes.c_double * n if n > 0 else ctypes.c_double * 1
    c_in = DblIn(*xs) if n > 0 else DblIn()
    OutArr = ctypes.c_double * total if total > 0 else ctypes.c_double * 1
    out_sectors = OutArr()
    scratch = OutArr()
    callback_error: list = [None]

    def _body_trampoline(in_ptr, in_n, out_ptr, _user):
        # Invoked CONCURRENTLY from up to ``n_sectors`` C-spawned threads.
        # ctypes holds the GIL (PyGILState_Ensure) for the duration of this
        # callback, so the Python work is serialised against itself and
        # ``callback_error`` / ``body`` are touched under the GIL. Each
        # thread reads ONLY its own disjoint scratch slice (``in_ptr``) and
        # writes ONLY its own disjoint out slice (``out_ptr``) — 0
        # cross-thread aliasing (the F233 independence the C dispatch relies
        # on). A GIL-releasing body lets the threads overlap.
        try:
            count = int(in_n)
            in_vals = [float(in_ptr[i]) for i in range(count)]
            result = list(body(in_vals))
            if len(result) != count:
                callback_error[0] = ValueError(
                    f"body returned length {len(result)}; expected {count}"
                )
                return SRMECH_ERR_BAD_INPUT
            for i in range(count):
                out_ptr[i] = float(result[i])
            return SRMECH_OK
        except Exception as exc:  # noqa: BLE001 — re-raised on the Python side
            callback_error[0] = exc
            return SRMECH_ERR_INTERNAL

    c_callback = CASCADE_BODY_CALLBACK_F64(_body_trampoline)
    rc = LIB.srmech_cascade_parallel_sector_dispatch(
        c_callback,
        None,
        ctypes.cast(c_in, ctypes.POINTER(ctypes.c_double)),
        ctypes.c_size_t(n),
        ctypes.c_uint32(n_sectors),
        ctypes.cast(out_sectors, ctypes.POINTER(ctypes.c_double)),
        ctypes.cast(scratch, ctypes.POINTER(ctypes.c_double)),
        ctypes.c_size_t(total),
    )
    if callback_error[0] is not None:
        raise callback_error[0]
    if rc != SRMECH_OK:
        raise RuntimeError(
            f"srmech_cascade_parallel_sector_dispatch returned status {rc}"
        )
    return [
        [float(out_sectors[s * n + i]) for i in range(n)]
        for s in range(n_sectors)
    ]


# ----------------------------------------------------------------------
# v0.7.5rc154 (UPSTREAM §49): genome file-management native dispatch — the
# Python-callable face of the 11 ``srmech_genome_*`` C symbols. ``genome.py``
# routes through these when :func:`has_native_genome`; the C family writes
# turns.bin + manifest.json byte-identical to the pure-Python path (proven
# across rc143–rc152), so native is the AUTHORITATIVE accelerator with no
# on-disk divergence. The C carves ALL its scratch from the caller arena we
# size per call here (no compiled-in cap), so it is standalone-complete: there
# is NO "fall back to pure-Python" — pure-Python is the complete ALTERNATIVE
# impl that runs only when there is no C at all. A non-OK status raises
# :class:`NativeGenomeError`, which ``genome.py`` translates (bad-input →
# ``GenomeBoundingError``); it does NOT retry the pure path.
# ----------------------------------------------------------------------

_genome_ws = None  # reused arena buffer, grown to the largest call seen


class NativeGenomeError(RuntimeError):
    """A native ``srmech_genome_*`` call returned a non-OK status. ``.status``
    carries the ``SRMECH_ERR_*`` code; ``genome.py`` translates it (it does NOT
    fall back to pure-Python — native is authoritative when present)."""

    def __init__(self, fn: str, status: int):
        self.status = status
        super().__init__(f"{fn} returned non-OK status {status}")


def has_native_genome() -> bool:
    """True iff the genome file-management C symbols are loaded + bound (a
    rc160+ lib that also exports the arena-based ``srmech_json_write_ws``)."""
    return bool(HAS_NATIVE and LIB is not None
                and hasattr(LIB, "srmech_genome_save")
                and hasattr(LIB, "srmech_json_write_ws")
                and hasattr(LIB, "srmech_genome_arena_bytes"))


def _genome_file_size(path: str) -> int:
    """Byte size of ``path`` (0 if absent)."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def _count_chrom_caps(body: bytes, leaf_dim: int) -> int:
    """Number of §44 CHROM caps (first byte 0x43 at a leaf boundary) in ``body``."""
    if leaf_dim <= 0:
        return 0
    return sum(1 for k in range(0, len(body), leaf_dim) if body[k] == 0x43)


def _genome_chrom_count(dir_: str, the_one: bytes = b"") -> int:
    """Chromosome count of the genome at ``dir_`` — the ``manifest.json`` count
    (cheap) if present, else a scan of ``turns.bin``'s CHROM caps (leaf_dim =
    ``len(the_one)``). Used ONLY to size the native arena exactly via
    :func:`_genome_arena` — the architecture (the C layout) defines capacity."""
    try:
        with open(os.path.join(dir_, "manifest.json"), "rb") as fh:
            return len(json.load(fh)["data"]["chromosomes"])
    except (OSError, KeyError, ValueError, TypeError):
        pass
    leaf_dim = len(the_one)
    if leaf_dim <= 0:
        return 0
    try:
        with open(os.path.join(dir_, "turns.bin"), "rb") as fh:
            body = fh.read()
    except OSError:
        return 0
    return _count_chrom_caps(body, leaf_dim)


def _genome_arena(body_len: int, n_chroms: int, region_len: int = 0):
    """Return ``(c_void_p, size)`` for an arena sized to EXACTLY what the C op
    needs for a genome of ``body_len`` bytes / ``n_chroms`` chromosomes (+ a
    ``region_len``-byte staged region). Capacity is DEFINED by the C layout via
    :c:func:`srmech_genome_arena_bytes` — not a heuristic multiplier. The shared
    buffer is reused, grown to the largest call seen."""
    global _genome_ws
    fn = LIB.srmech_genome_arena_bytes
    if fn.restype is not ctypes.c_size_t:
        fn.restype = ctypes.c_size_t
        fn.argtypes = [ctypes.c_size_t, ctypes.c_uint32, ctypes.c_size_t]
    need = int(fn(ctypes.c_size_t(int(body_len)),
                  ctypes.c_uint32(int(n_chroms)),
                  ctypes.c_size_t(int(region_len))))
    if _genome_ws is None or len(_genome_ws) < need:
        _genome_ws = (ctypes.c_char * need)()
    return ctypes.cast(_genome_ws, ctypes.c_void_p), len(_genome_ws)


def _turns_size(dir_: str) -> int:
    """Byte size of ``<dir>/turns.bin`` (0 if absent)."""
    return _genome_file_size(os.path.join(dir_, "turns.bin"))


def _u8(data: bytes):
    """A ``c_uint8`` buffer copy of ``data`` (NULL for empty)."""
    if len(data) == 0:
        return ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
    return (ctypes.c_uint8 * len(data)).from_buffer_copy(data)


def _require_genome():
    if not has_native_genome():
        raise NativeGenomeError("genome native surface", SRMECH_ERR_NOT_IMPL)


def genome_save_c(dir_: str, body: bytes, leaf_dim: int, the_one: bytes) -> None:
    """Native genome save — writes ``<dir>/turns.bin`` + ``manifest.json``."""
    _require_genome()
    ws, ws_len = _genome_arena(len(body), _count_chrom_caps(body, leaf_dim))
    rc = LIB.srmech_genome_save(
        dir_.encode("utf-8"), _u8(body), ctypes.c_size_t(len(body)),
        ctypes.c_uint32(leaf_dim), _u8(the_one), ctypes.c_size_t(len(the_one)),
        ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_save", rc)


def genome_load_c(dir_: str, the_one: bytes, out_cap: int) -> bytes:
    """Native genome load — reads the whole body (bounds-checked) from
    ``<dir>/turns.bin``; ``out_cap`` should be the turns.bin byte size."""
    _require_genome()
    ws, ws_len = _genome_arena(out_cap, _genome_chrom_count(dir_, the_one))
    out = (ctypes.c_uint8 * max(out_cap, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_genome_load(
        dir_.encode("utf-8"), out, ctypes.c_size_t(out_cap),
        ctypes.byref(out_len), _u8(the_one), ctypes.c_size_t(len(the_one)),
        ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_load", rc)
    return bytes(out[:out_len.value])


def genome_window_c(dir_: str, label: str, the_one: bytes, out_cap: int) -> bytes:
    """Native genome window — reads one chromosome's region bytes (cap-bounded,
    integrity-verified) from ``<dir>``; ``out_cap`` an upper bound (turns.bin
    size is safe)."""
    _require_genome()
    ws, ws_len = _genome_arena(out_cap, _genome_chrom_count(dir_, the_one))
    out = (ctypes.c_uint8 * max(out_cap, 1))()
    out_len = ctypes.c_size_t(0)
    rc = LIB.srmech_genome_window(
        dir_.encode("utf-8"), label.encode("utf-8"), out,
        ctypes.c_size_t(out_cap), ctypes.byref(out_len),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_window", rc)
    return bytes(out[:out_len.value])


def genome_catalog_c(dir_: str, the_one: bytes) -> str:
    """Native genome catalog — parse (or §44 rebuild-by-scan) the manifest and
    return its canonical JSON text (byte-identical to ``manifest.json``);
    ``genome.py`` ``json.loads`` it. ``the_one`` may be empty when a manifest is
    present (only consulted as the rebuild width when it is absent)."""
    _require_genome()
    man_sz = _genome_file_size(os.path.join(dir_, "manifest.json"))
    body_sz = _genome_file_size(os.path.join(dir_, "turns.bin"))
    ws, ws_len = _genome_arena(max(man_sz, body_sz),
                               _genome_chrom_count(dir_, the_one))
    tree = ctypes.c_void_p()
    rc = LIB.srmech_genome_catalog(
        dir_.encode("utf-8"), _u8(the_one), ctypes.c_size_t(len(the_one)),
        ws, ctypes.c_size_t(ws_len), ctypes.byref(tree))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_catalog", rc)
    write_cap = max(256 * 1024, 4 * max(man_sz, body_sz))
    buf = ctypes.create_string_buffer(write_cap + 1)
    out_len = ctypes.c_size_t(0)
    # rc160: the writer carves its key-sort scratch from a caller arena sized
    # to the actual tree (no compiled-in object-width cap).
    jws_len = int(LIB.srmech_json_write_arena_bytes(tree))
    jws = ctypes.create_string_buffer(max(jws_len, 1))
    rc = LIB.srmech_json_write_ws(
        tree, buf, ctypes.c_size_t(write_cap), ctypes.byref(out_len),
        jws, ctypes.c_size_t(len(jws)))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_json_write_ws", rc)
    return buf.raw[:out_len.value].decode("utf-8")


def genome_append_c(dir_: str, label: str, region: bytes, leaf_dim: int,
                    the_one: bytes) -> None:
    """Native genome append — grow ``<dir>`` by one chromosome region."""
    _require_genome()
    ws, ws_len = _genome_arena(
        _turns_size(dir_), _genome_chrom_count(dir_, the_one) + 1, len(region))
    rc = LIB.srmech_genome_append(
        dir_.encode("utf-8"), label.encode("utf-8"), _u8(region),
        ctypes.c_size_t(len(region)), ctypes.c_uint32(leaf_dim),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_append", rc)


def genome_remove_c(dir_: str, label: str, the_one: bytes) -> None:
    """Native genome remove — splice one chromosome out of ``<dir>`` in place."""
    _require_genome()
    ws, ws_len = _genome_arena(_turns_size(dir_),
                               _genome_chrom_count(dir_, the_one))
    rc = LIB.srmech_genome_remove(
        dir_.encode("utf-8"), label.encode("utf-8"),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_remove", rc)


def genome_replace_c(dir_: str, label: str, region: bytes, leaf_dim: int,
                     the_one: bytes) -> None:
    """Native genome replace — splice one chromosome's region in place."""
    _require_genome()
    ws, ws_len = _genome_arena(
        _turns_size(dir_), _genome_chrom_count(dir_, the_one), len(region))
    rc = LIB.srmech_genome_replace(
        dir_.encode("utf-8"), label.encode("utf-8"), _u8(region),
        ctypes.c_size_t(len(region)), ctypes.c_uint32(leaf_dim),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_replace", rc)


def genome_export_c(dir_: str, label: str, out_path: str, the_one: bytes) -> None:
    """Native genome export — bundle one chromosome to ``out_path`` (.chr)."""
    _require_genome()
    ws, ws_len = _genome_arena(  # region <= body bound for the .chr buffers
        _turns_size(dir_), _genome_chrom_count(dir_, the_one), _turns_size(dir_))
    rc = LIB.srmech_genome_export(
        dir_.encode("utf-8"), label.encode("utf-8"), out_path.encode("utf-8"),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_export", rc)


def genome_import_c(chr_path: str, dest: str, the_one: bytes) -> None:
    """Native genome import — re-import a .chr bundle into ``dest`` (seed/append)."""
    _require_genome()
    chr_sz = _genome_file_size(chr_path)
    ws, ws_len = _genome_arena(
        _turns_size(dest) + chr_sz, _genome_chrom_count(dest, the_one) + 1, chr_sz)
    rc = LIB.srmech_genome_import(
        chr_path.encode("utf-8"), dest.encode("utf-8"),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_import", rc)


def genome_explode_c(dir_: str, out_dir: str, the_one: bytes) -> None:
    """Native genome explode — packed genome → dir of <label>.chr bundles."""
    _require_genome()
    ws, ws_len = _genome_arena(  # region <= body bound for each .chr bundle
        _turns_size(dir_), _genome_chrom_count(dir_, the_one), _turns_size(dir_))
    rc = LIB.srmech_genome_explode(
        dir_.encode("utf-8"), out_dir.encode("utf-8"),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_explode", rc)


def genome_pack_c(loose_dir: str, dest: str, the_one: bytes) -> None:
    """Native genome pack — dir of *.chr → one packed genome (canonical order)."""
    _require_genome()
    try:
        chrs = [n for n in os.listdir(loose_dir) if n.endswith(".chr")]
    except OSError:
        chrs = []
    total = sum(_genome_file_size(os.path.join(loose_dir, n)) for n in chrs)
    # the packed body + a per-bundle region are both bounded by the .chr total;
    # one .chr per chromosome → n_chroms = len(chrs).
    ws, ws_len = _genome_arena(total, len(chrs), total)
    rc = LIB.srmech_genome_pack(
        loose_dir.encode("utf-8"), dest.encode("utf-8"),
        _u8(the_one), ctypes.c_size_t(len(the_one)), ws, ctypes.c_size_t(ws_len))
    if rc != SRMECH_OK:
        raise NativeGenomeError("srmech_genome_pack", rc)


__all__ = [
    "ABI_VERSION",
    "BUS_HANDLER_CALLBACK",
    "CASCADE_BODY_CALLBACK_F64",
    "CASCADE_OP_CALLBACK_F64",
    "cascade_parallel_sector_dispatch_c",
    "EXPECTED_ABI_VERSION",
    "HAS_NATIVE",
    "LIB",
    "LOAD_ERROR",
    "NATIVE_ABI_VERSION",
    "NATIVE_VERSION",
    "NativeNDJsonError",
    "NativeGenomeError",
    "has_native_genome",
    "genome_save_c",
    "genome_load_c",
    "genome_catalog_c",
    "genome_window_c",
    "genome_append_c",
    "genome_remove_c",
    "genome_replace_c",
    "genome_export_c",
    "genome_import_c",
    "genome_explode_c",
    "genome_pack_c",
    "ndjson_lines_c",
    "sha256_hex_c",
    "sha256_batch_c",
    "sha256_shani_c",
    "has_shani",
    "SRMECH_OK",
    "SRMECH_ERR_NULL_ARG",
    "SRMECH_ERR_BAD_INPUT",
    "SRMECH_ERR_IO",
    "SRMECH_ERR_OVERFLOW",
    "SRMECH_ERR_NOT_IMPL",
    "SRMECH_ERR_INTERNAL",
    "SRMECH_TRANS_EXP",
    "SRMECH_TRANS_COS",
    "SRMECH_TRANS_SIN",
    "SRMECH_TRANS_LOG",
]
