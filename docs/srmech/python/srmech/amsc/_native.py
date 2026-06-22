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
