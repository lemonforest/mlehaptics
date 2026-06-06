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
    # int srmech_hermitian_eigendecompose(uint32_t n,
    #     const double *H_il, double *out_eigvals,
    #     double *out_eigvecs_il)
    lib.srmech_hermitian_eigendecompose.argtypes = [
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_hermitian_eigendecompose.restype = ctypes.c_int

    # int srmech_dense_matvec_complex(uint32_t rows, uint32_t cols,
    #     const double *M_il, const double *v_il, double *out_il)
    lib.srmech_dense_matvec_complex.argtypes = [
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.srmech_dense_matvec_complex.restype = ctypes.c_int

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

    # int srmech_dense_solve_f64(uint32_t n, uint32_t nrhs,
    #     const double *A, const double *B, double *out_X)
    # v0.7.1rc3 additive symbol (#897 §26): the reusable Class-L dense
    # linear solve A·X = B the Schur/DtN float path composes over.
    # hasattr-guarded because EXPECTED_ABI_VERSION stays 3 — a stale ABI-3
    # lib built before this rc lacks the symbol; an unguarded bind would
    # AttributeError and disable the whole native surface.
    if hasattr(lib, "srmech_dense_solve_f64"):
        lib.srmech_dense_solve_f64.argtypes = [
            ctypes.c_uint32,                    # n
            ctypes.c_uint32,                    # nrhs
            ctypes.POINTER(ctypes.c_double),    # A (n*n, row-major)
            ctypes.POINTER(ctypes.c_double),    # B (n*nrhs, row-major)
            ctypes.POINTER(ctypes.c_double),    # out_X (n*nrhs, row-major)
        ]
        lib.srmech_dense_solve_f64.restype = ctypes.c_int

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

        # int srmech_klein4_similarity(const uint8_t *a, const uint8_t *b,
        #                              uint32_t n, double *out)
        lib.srmech_klein4_similarity.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.srmech_klein4_similarity.restype = ctypes.c_int

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
