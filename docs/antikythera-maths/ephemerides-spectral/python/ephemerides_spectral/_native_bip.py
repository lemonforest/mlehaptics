"""ctypes wrapper for the native ephemerides_spectral shared library.

Loads the library shipped in the wheel under ``ephemerides_spectral/_native/``.
If the library isn't present (sdist install without a C toolchain,
Pyodide / WASM environments, the pure-Python wheel), the module
exposes ``HAS_NATIVE = False`` and the pure-Python BIP encoder
remains the only path.

Discipline:
- Callers MUST guard usage with ``if HAS_NATIVE: ...``.
- ABI version is checked at load time. A mismatch is treated as
  missing (``HAS_NATIVE = False``, ``LOAD_ERROR`` populated).
- Pure-Python is correctness; native is performance. The two paths
  produce byte-for-byte-identical phase residues — pinned by the
  three-way parity test in ``tests/test_native_parity.py``.

Bound functions match ``c/include/ephemerides_spectral.h``:

    int es_encode_state(double delta_t_days, uint32_t *phases_out)
    int es_encode_at_jd(double jd_tdb,        uint32_t *phases_out)
    size_t es_body_index(const char *name)
    int32_t es_cos_lut(uint32_t phase_residue, uint32_t n_lobes)
    double  es_residue_to_radians(uint32_t residue)
    const char *es_version(void)
    int es_abi_version(void)
    int es_n_bodies(void)

Status codes (``es_status_t``):

    ES_OK                       = 0
    ES_ERR_DELTA_OUT_OF_RANGE   = 1
    ES_ERR_NULL_OUTPUT          = 2
    ES_ERR_NON_FINITE_INPUT     = 3
"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# Mirror of ``ES_ABI_VERSION`` in the C header. Bump in lockstep with
# the C side whenever the wire format of any exported function
# changes.
#   v1 — v0.3.1 baseline (encode-only surface).
#   v2 — v0.4.1: diagnosed-fiber overlay (es_patch_t struct +
#       es_apply_patch / es_clear_patches / es_n_active_patches /
#       es_get_patch_at).
#   v3 — v0.6.0: C/Python parity Tier 1 (es_breathing_modulation,
#       es_syzygy_t struct + es_find_syzygies). Encoder hot path
#       unchanged; net-new entry points only.
#   v4 — v0.6.1: Tier 2a foundation (es_complex64_t struct,
#       es_channel_basis, splitmix64 plumbing). Encoder hot path
#       unchanged.
#   v5 — v0.7.0: Tier 2b HD pipeline. es_encode_state_hd,
#       es_bind_observer, es_get_eclipse_probability + body-basis /
#       observer-coord / syzygy-node seed constants. Encoder hot
#       path unchanged.
#   v6 — v0.13.4: JPL Power-of-Ten Rule 1 + Rule 3 fixes. The three
#       HD-pipeline entries gain caller-supplied scratch buffer
#       parameters so the C library no longer calls malloc/free
#       (Rule 3) and no longer needs the goto-cleanup pattern
#       (Rule 1). Encoder math is byte-identical to v5; only the
#       wire format changed (extra pointer params). The Python
#       shim allocates the scratch buffers once per call alongside
#       the existing `out_state` buffer, so the user-facing bridge
#       API is unchanged.
#   v7 — v0.15.0: Sol Moon Times classical-roster completion. The
#       BODIES roster grew (Pluto-Charon + remaining Uranians), which
#       changed ES_N_BODIES + the on-the-wire size of every per-body
#       array. Encoder math unchanged on shared bodies; the ABI bump
#       captures the roster-cardinality wire-format change.
#   v8 — v0.16.0: Tier-1 BODIES expansion (Lagrange trojans + retrograde
#       irregulars + Neptune sub-graph). ES_N_BODIES = 52 (current).
#       Same wire-format-by-roster-size mechanism as v7. Stable through
#       v0.27.0 / v0.28.0rc1; the v0.28.0rc2 realignment is a pure
#       Python-side EXPECTED_ABI_VERSION catch-up — the C side has been
#       at v8 since v0.16.0 but this constant was left at 6, silently
#       forcing HAS_NATIVE = False on every wheel install.
#   v9 — v0.28.0rc5: Phase 10a EOC C-side completion.
#       Added: ES_PATCH_KIND_ECCENTRICITY_CORRECTION + 3 trailing
#       double fields on `es_patch_t` (eccentricity,
#       mean_anomaly_at_j2000_rad, n_rad_per_day). Additive — original
#       field offsets preserved, but sizeof(es_patch_t) increased.
#       Closes the rc1 backend_caveat: EOC patches now work on
#       backend="c" and produce byte-exact agreement with the Python
#       BIP path (pinned by test_eoc_catalog's both-backends parity).
EXPECTED_ABI_VERSION: int = 9

# Mirrors c/include/ephemerides_spectral.h.
ES_PATCH_NAME_MAX: int = 64
ES_MAX_PATCHES: int = 64  # v0.28.0rc5: bumped 32 → 64 to fit 51-body EOC catalog
ES_PATCH_KIND_SINUSOID: int = 0
ES_PATCH_KIND_COUPLED_SINUSOID: int = 1
ES_PATCH_KIND_ECCENTRICITY_CORRECTION: int = 2  # v0.28.0rc5 (ABI v9)

# Patch registry status codes (es_apply_patch / es_get_patch_at).
ES_ERR_PATCH_FULL: int = 100
ES_ERR_PATCH_DUPLICATE_NAME: int = 101
ES_ERR_PATCH_BAD_KIND: int = 102
ES_ERR_PATCH_BAD_INDEX: int = 103
ES_ERR_PATCH_BAD_PARAM: int = 104
ES_ERR_PATCH_OUT_OF_RANGE: int = 105


class EsPatch(ctypes.Structure):
    """Wire-format mirror of ``es_patch_t`` from the C header.

    Field order MUST match the C struct exactly. Any field-order or
    type drift here vs the ABI v9 layout would silently corrupt
    patch registration; the field layout is locked in by the C
    side's ``ES_ABI_VERSION = 9`` and the load-time abi-version check.

    ABI v9 (v0.28.0rc5) extended the struct with 3 trailing double
    fields for the ECC patch kind. Original field offsets are
    unchanged — older patches written through ABI v2/v8 layouts
    remain valid as long as the new ECC fields are zero-initialised
    (which `EsPatch()` default-construct does).
    """
    _fields_ = [
        ("kind", ctypes.c_int32),
        ("name", ctypes.c_char * ES_PATCH_NAME_MAX),
        ("body_idx_a", ctypes.c_int32),
        ("body_idx_b", ctypes.c_int32),
        ("amplitude_deg", ctypes.c_double),
        ("period_days", ctypes.c_double),
        ("phase_rad", ctypes.c_double),
        ("correlation", ctypes.c_int32),
        # ── v0.28.0rc5 (ABI v9): eccentricity-correction fields ────
        ("eccentricity", ctypes.c_double),
        ("mean_anomaly_at_j2000_rad", ctypes.c_double),
        ("n_rad_per_day", ctypes.c_double),
    ]

#: Status codes from ``es_status_t``.
ES_OK = 0
ES_ERR_DELTA_OUT_OF_RANGE = 1
ES_ERR_NULL_OUTPUT = 2
ES_ERR_NON_FINITE_INPUT = 3
ES_ERR_INVALID_INDEX = 4         # v0.6.0 (ABI v3)
ES_ERR_INVALID_KIND = 5          # v0.6.0
ES_ERR_INVALID_THRESHOLD = 6     # v0.6.0


# ABI v3 (v0.6.0) — Tier 1 parity surface.
ES_SYZYGY_KIND_SOLAR = 0
ES_SYZYGY_KIND_LUNAR = 1
ES_SYZYGY_KIND_FILTER_SOLAR = 0
ES_SYZYGY_KIND_FILTER_LUNAR = 1
ES_SYZYGY_KIND_FILTER_ALL = 2


class EsComplex64(ctypes.Structure):
    """Wire-format mirror of ``es_complex64_t`` (Tier 2a / ABI v4).

    Two contiguous floats (real, imag); 8 bytes per element. Matches
    numpy's ``complex64`` so callers can read the ctypes buffer
    directly into a numpy array without copying.
    """
    _fields_ = [
        ("real", ctypes.c_float),
        ("imag", ctypes.c_float),
    ]


class EsSyzygy(ctypes.Structure):
    """Wire-format mirror of ``es_syzygy_t`` from the C header.

    Field order MUST match the C struct exactly.
    """
    _fields_ = [
        ("jd_tdb", ctypes.c_double),
        ("kind", ctypes.c_int32),
        # NOTE: 4-byte padding here in C; ctypes inserts it automatically
        # because the next field is c_double which is 8-byte aligned.
        ("synodic_phase_resid", ctypes.c_double),
        ("draconic_phase_resid", ctypes.c_double),
        ("score", ctypes.c_double),
    ]


# ──────────────────────────────────────────────────────────────────────
# Library discovery
# ──────────────────────────────────────────────────────────────────────

def _candidate_lib_names() -> List[str]:
    """Per-platform shared-library filenames CMake produces.

    Windows: ``ephemerides_spectral.dll`` (we drop the ``lib`` prefix
    in CMakeLists for Windows).
    Linux:   ``libephemerides_spectral.so``.
    macOS:   ``libephemerides_spectral.dylib``.
    """
    if sys.platform == "win32":
        return ["ephemerides_spectral.dll"]
    if sys.platform == "darwin":
        return ["libephemerides_spectral.dylib"]
    return ["libephemerides_spectral.so"]


def _find_library() -> Optional[Path]:
    """Search the bundled ``_native/`` directory next to this module."""
    native_dir = Path(__file__).resolve().parent / "_native"
    if not native_dir.exists():
        return None
    for name in _candidate_lib_names():
        p = native_dir / name
        if p.exists():
            return p
    return None


def _load_via_srmech_profile() -> Optional[Tuple[ctypes.CDLL, Path]]:
    """Try to load the native library via the srmech profile.

    PR-c (v0.28.0rc4): when srmech is importable AND the ephemerides
    profile has its plugin tier loaded, return the same CDLL handle
    srmech already loaded — avoiding a duplicate dlopen of the same
    library file.

    Returns ``(cdll, library_path)`` on success; ``None`` if srmech
    isn't installed, the profile isn't registered, or the plugin tier
    didn't load. All failures are silent: the direct ``_find_library``
    + ``ctypes.CDLL`` fallback handles every case the profile path
    doesn't cover (sdist installs, Pyodide / WASM, srmech import
    errors, profile-loader bugs).

    Design note: doing the import lazily here (rather than at module
    top) keeps ``ephemerides_spectral._native_bip`` importable even
    when srmech isn't installed — critical for test environments
    that only need the pure-Python BIP path.
    """
    try:
        import srmech  # noqa: F401 — module-availability probe.
    except ImportError:
        return None

    try:
        profile = srmech.profile("ephemerides")
    except Exception:
        # Any error from the profile loader (not registered,
        # InvalidProfileError, AbiMismatchError, etc.) — fall through
        # to the direct path. The direct path's ABI check will
        # report a coherent LOAD_ERROR if something is wrong with
        # the underlying library.
        return None

    if profile.native is None:
        # Profile resolved but plugin tier didn't load (pure-Python
        # wheel, missing native binary, etc.). Direct path will see
        # the same condition and report it.
        return None

    meta = profile._native_meta or {}
    lib_path_str = meta.get("library_path")
    if not lib_path_str:
        return None
    return profile.native, Path(lib_path_str)


# ──────────────────────────────────────────────────────────────────────
# ctypes prototype binding
# ──────────────────────────────────────────────────────────────────────

def _bind(lib: ctypes.CDLL) -> None:
    """Set argtypes / restype for every function we call into."""
    # int es_encode_state(double, uint32_t *out)
    lib.es_encode_state.argtypes = [
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.es_encode_state.restype = ctypes.c_int

    # int es_encode_at_jd(double, uint32_t *out)
    lib.es_encode_at_jd.argtypes = [
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.es_encode_at_jd.restype = ctypes.c_int

    # size_t es_body_index(const char *)
    lib.es_body_index.argtypes = [ctypes.c_char_p]
    lib.es_body_index.restype = ctypes.c_size_t

    # int32_t es_cos_lut(uint32_t, uint32_t)
    lib.es_cos_lut.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    lib.es_cos_lut.restype = ctypes.c_int32

    # double es_residue_to_radians(uint32_t)
    lib.es_residue_to_radians.argtypes = [ctypes.c_uint32]
    lib.es_residue_to_radians.restype = ctypes.c_double

    # const char *es_version(void)
    lib.es_version.argtypes = []
    lib.es_version.restype = ctypes.c_char_p

    # int es_abi_version(void)
    lib.es_abi_version.argtypes = []
    lib.es_abi_version.restype = ctypes.c_int

    # int es_n_bodies(void)
    lib.es_n_bodies.argtypes = []
    lib.es_n_bodies.restype = ctypes.c_int

    # ABI v2 (v0.4.1) — diagnosed-fiber overlay.
    # int es_apply_patch(const es_patch_t *)
    lib.es_apply_patch.argtypes = [ctypes.POINTER(EsPatch)]
    lib.es_apply_patch.restype = ctypes.c_int

    # size_t es_clear_patches(void)
    lib.es_clear_patches.argtypes = []
    lib.es_clear_patches.restype = ctypes.c_size_t

    # size_t es_n_active_patches(void)
    lib.es_n_active_patches.argtypes = []
    lib.es_n_active_patches.restype = ctypes.c_size_t

    # int es_get_patch_at(size_t idx, es_patch_t *out)
    lib.es_get_patch_at.argtypes = [ctypes.c_size_t, ctypes.POINTER(EsPatch)]
    lib.es_get_patch_at.restype = ctypes.c_int

    # ABI v9 (v0.28.0rc5) — Phase 10a EOC C-side completion.
    # size_t es_clear_eoc_patches(void)
    lib.es_clear_eoc_patches.argtypes = []
    lib.es_clear_eoc_patches.restype = ctypes.c_size_t

    # ABI v3 (v0.6.0) — Tier 1 parity surface.
    # es_status_t es_breathing_modulation(
    #     double delta_t_days, size_t body_idx_a, size_t body_idx_b,
    #     int n_a, int n_b,
    #     uint32_t *out_phase, int32_t *out_cos_q14, double *out_modulation)
    lib.es_breathing_modulation.argtypes = [
        ctypes.c_double,
        ctypes.c_size_t, ctypes.c_size_t,
        ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.es_breathing_modulation.restype = ctypes.c_int

    # es_status_t es_find_syzygies(
    #     double jd_lo, double jd_hi, int kind,
    #     double threshold, size_t max_candidates,
    #     es_syzygy_t *out_buf, size_t out_capacity,
    #     size_t *out_count)
    lib.es_find_syzygies.argtypes = [
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double, ctypes.c_size_t,
        ctypes.POINTER(EsSyzygy), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.es_find_syzygies.restype = ctypes.c_int

    # ABI v4 (v0.6.1) — Tier 2a foundation: channel-basis emission.
    # es_status_t es_channel_basis(uint64_t seed, es_complex64_t *out, size_t D)
    lib.es_channel_basis.argtypes = [
        ctypes.c_uint64,
        ctypes.POINTER(EsComplex64),
        ctypes.c_size_t,
    ]
    lib.es_channel_basis.restype = ctypes.c_int

    # ABI v6 (v0.13.4) — Tier 2b HD pipeline with caller-supplied scratch
    # buffers (JPL Power-of-Ten Rule 1 + Rule 3 fixes).
    # es_status_t es_encode_state_hd(double, es_complex64_t *out,
    #                                 es_complex64_t *scratch_basis,
    #                                 es_complex64_t *scratch_rolled,
    #                                 size_t D)
    lib.es_encode_state_hd.argtypes = [
        ctypes.c_double,
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.c_size_t,
    ]
    lib.es_encode_state_hd.restype = ctypes.c_int

    # es_status_t es_bind_observer(const es_complex64_t *state_in,
    #                               size_t body_idx, double lat, double lon,
    #                               es_complex64_t *out,
    #                               es_complex64_t *scratch_body_basis,
    #                               es_complex64_t *scratch_coord_basis,
    #                               es_complex64_t *scratch_coord_op,
    #                               size_t D)
    lib.es_bind_observer.argtypes = [
        ctypes.POINTER(EsComplex64),
        ctypes.c_size_t,
        ctypes.c_double, ctypes.c_double,
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.c_size_t,
    ]
    lib.es_bind_observer.restype = ctypes.c_int

    # es_status_t es_get_eclipse_probability(const es_complex64_t *state,
    #                                         size_t D, size_t sun_idx,
    #                                         size_t moon_idx,
    #                                         es_complex64_t *scratch_sun_b,
    #                                         es_complex64_t *scratch_moon_b,
    #                                         es_complex64_t *scratch_node_b,
    #                                         es_complex64_t *scratch_s_op,
    #                                         double *out)
    lib.es_get_eclipse_probability.argtypes = [
        ctypes.POINTER(EsComplex64),
        ctypes.c_size_t,
        ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(EsComplex64),
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.es_get_eclipse_probability.restype = ctypes.c_int


# ──────────────────────────────────────────────────────────────────────
# Module-level state
# ──────────────────────────────────────────────────────────────────────

LIB: Optional[ctypes.CDLL] = None
LIB_PATH: Optional[Path] = None
ABI_VERSION: Optional[int] = None
N_BODIES: Optional[int] = None
HAS_NATIVE: bool = False
LOAD_ERROR: Optional[str] = None
LOAD_SOURCE: Optional[str] = None
"""``"srmech_profile"`` if the library handle came from
``srmech.profile("ephemerides").native``; ``"direct_ctypes"`` if from
the local ``_find_library()`` + ``ctypes.CDLL()`` fallback. ``None``
when ``HAS_NATIVE`` is False. PR-c surfaces this so callers + tests
can prove the profile-tier path is exercised when available."""

# ── PR-c (v0.28.0rc4): prefer srmech profile-loaded handle ─────────
# When srmech is installed AND the ephemerides profile's plugin tier
# loaded successfully, reuse THAT CDLL handle rather than opening the
# library a second time. Object identity matters here: srmech-side
# bindings (e.g. tool_schema introspection, future cross-profile
# dispatch) and ephemerides-spectral's own ``LIB.*`` calls then share
# state — avoids the class of bug where two CDLL instances of the same
# .so/.dll see different runtime state in patch-registry-style globals.
#
# Fallback to the direct ``_find_library`` + ``ctypes.CDLL`` path on
# any failure of the profile route. Both paths converge on the same
# ABI handshake + binding logic below.
_LIB_PATH: Optional[Path] = None
_candidate_lib: Optional[ctypes.CDLL] = None
_srmech_handle = _load_via_srmech_profile()
if _srmech_handle is not None:
    _candidate_lib, _LIB_PATH = _srmech_handle
    LOAD_SOURCE = "srmech_profile"
else:
    _LIB_PATH = _find_library()
    if _LIB_PATH is not None:
        try:
            _candidate_lib = ctypes.CDLL(str(_LIB_PATH))
            LOAD_SOURCE = "direct_ctypes"
        except OSError as exc:
            LOAD_ERROR = f"failed to load {_LIB_PATH}: {exc}"

if _candidate_lib is not None:
    try:
        _bind(_candidate_lib)
        version = int(_candidate_lib.es_abi_version())
        if version != EXPECTED_ABI_VERSION:
            LOAD_ERROR = (
                f"native ABI mismatch at {_LIB_PATH}: "
                f"binary is v{version}, Python expects v{EXPECTED_ABI_VERSION}; "
                "rebuild the C extension or fall back to pure Python."
            )
            LOAD_SOURCE = None
        else:
            LIB = _candidate_lib
            LIB_PATH = _LIB_PATH
            ABI_VERSION = version
            N_BODIES = int(_candidate_lib.es_n_bodies())
            HAS_NATIVE = True
    except (AttributeError, ValueError) as exc:
        LOAD_ERROR = f"failed to bind {_LIB_PATH}: {exc}"
        LOAD_SOURCE = None
elif LOAD_ERROR is None:
    LOAD_ERROR = (
        "native library not found in ephemerides_spectral/_native/; "
        "this is normal for sdist installs without a C toolchain and "
        "for Pyodide / WASM environments. Pure-Python BIP encoder will "
        "be used."
    )


# ──────────────────────────────────────────────────────────────────────
# High-level helper — the path callers actually use
# ──────────────────────────────────────────────────────────────────────

def encode_state(delta_t_days: float) -> np.ndarray:
    """Native BIP encode_state — returns ``uint32[N_BODIES]`` phase residues.

    Caller-side guard required: only invoke when ``HAS_NATIVE`` is True.
    Raises ``RuntimeError`` if the C library returned a non-zero status.
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native library not loaded; check HAS_NATIVE before calling "
            "encode_state. LOAD_ERROR: " + (LOAD_ERROR or "<unknown>")
        )
    assert LIB is not None
    assert N_BODIES is not None

    phases = np.zeros(N_BODIES, dtype=np.uint32)
    status = LIB.es_encode_state(
        ctypes.c_double(float(delta_t_days)),
        phases.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
    )
    if status == ES_OK:
        return phases
    if status == ES_ERR_DELTA_OUT_OF_RANGE:
        raise OverflowError(
            f"delta_t_days={delta_t_days} exceeds the int64 envelope "
            f"(~1.86 Myr); native encoder rejected the input"
        )
    if status == ES_ERR_NON_FINITE_INPUT:
        raise OverflowError(f"delta_t_days={delta_t_days} is not finite")
    raise RuntimeError(f"native es_encode_state returned status={status}")


def encode_at_jd(jd_tdb: float) -> np.ndarray:
    """Convenience: encode at an absolute JD via the native path."""
    if not HAS_NATIVE:
        raise RuntimeError("native library not loaded")
    assert LIB is not None
    assert N_BODIES is not None
    phases = np.zeros(N_BODIES, dtype=np.uint32)
    status = LIB.es_encode_at_jd(
        ctypes.c_double(float(jd_tdb)),
        phases.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
    )
    if status != ES_OK:
        raise RuntimeError(f"native es_encode_at_jd returned status={status}")
    return phases


def native_version() -> Optional[str]:
    """Version string baked into the loaded C binary, or None if not loaded."""
    if not HAS_NATIVE:
        return None
    assert LIB is not None
    raw = LIB.es_version()
    return raw.decode("ascii") if raw else None


# ──────────────────────────────────────────────────────────────────────
# Diagnosed-fiber runtime overlay (ABI v2)
# ──────────────────────────────────────────────────────────────────────
#
# These helpers are called from `bridge.apply_patch` / `clear_patches`
# to keep the C-side registry in sync with the Python-side one. The
# bridge mutates Python first, then mirrors to C; if C rejects (e.g.
# capacity exceeded) the bridge reverts the Python-side change so the
# two registries never drift.
#
# Each helper is a no-op when ``HAS_NATIVE`` is False — pure-Python /
# Pyodide users are unaffected.


def native_apply_sinusoid_patch(name: str, body_idx: int,
                                amplitude_deg: float, period_days: float,
                                phase_rad: float = 0.0) -> int:
    """Mirror a sinusoid patch into the C-side registry.

    Returns ``ES_OK`` (0) on success, otherwise one of
    ``ES_ERR_PATCH_FULL`` / ``DUPLICATE_NAME`` / ``BAD_INDEX`` /
    ``BAD_PARAM`` / ``BAD_KIND``.

    No-op (returns ``ES_OK`` immediately) if HAS_NATIVE is False.
    """
    if not HAS_NATIVE:
        return ES_OK
    assert LIB is not None
    patch = EsPatch(
        kind=ES_PATCH_KIND_SINUSOID,
        name=name.encode("utf-8")[: ES_PATCH_NAME_MAX - 1],
        body_idx_a=int(body_idx),
        body_idx_b=-1,
        amplitude_deg=float(amplitude_deg),
        period_days=float(period_days),
        phase_rad=float(phase_rad),
        correlation=0,
    )
    return int(LIB.es_apply_patch(ctypes.byref(patch)))


def native_apply_coupled_patch(name: str, body_idx_a: int, body_idx_b: int,
                               amplitude_deg: float, period_days: float,
                               phase_rad: float = 0.0,
                               correlation: int = -1) -> int:
    """Mirror a coupled-sinusoid patch into the C-side registry."""
    if not HAS_NATIVE:
        return ES_OK
    assert LIB is not None
    patch = EsPatch(
        kind=ES_PATCH_KIND_COUPLED_SINUSOID,
        name=name.encode("utf-8")[: ES_PATCH_NAME_MAX - 1],
        body_idx_a=int(body_idx_a),
        body_idx_b=int(body_idx_b),
        amplitude_deg=float(amplitude_deg),
        period_days=float(period_days),
        phase_rad=float(phase_rad),
        correlation=int(correlation),
    )
    return int(LIB.es_apply_patch(ctypes.byref(patch)))


def native_apply_eoc_patch(name: str, body_idx: int,
                           eccentricity: float,
                           mean_anomaly_at_j2000_rad: float,
                           n_rad_per_day: float) -> int:
    """Mirror a Phase 10a eccentricity-correction patch into the C
    registry (v0.28.0rc5, ABI v9).

    The C-side evaluator Newton-solves Kepler's equation and applies
    the half-angle true-anomaly formula in lockstep with the Python
    BIP encoder's `EccentricityCorrectionPatch.evaluate()`; with both
    sides registered, `default_encode(..., backend="c")` byte-matches
    `backend="bip"` even when EOC patches are active.

    Returns ``ES_OK`` (0) on success, otherwise one of the
    ``ES_ERR_PATCH_*`` codes (``BAD_PARAM`` if eccentricity is out of
    [0, 1) or n_rad_per_day is zero / non-finite).

    No-op (returns ``ES_OK`` immediately) if HAS_NATIVE is False.
    """
    if not HAS_NATIVE:
        return ES_OK
    assert LIB is not None
    patch = EsPatch(
        kind=ES_PATCH_KIND_ECCENTRICITY_CORRECTION,
        name=name.encode("utf-8")[: ES_PATCH_NAME_MAX - 1],
        body_idx_a=int(body_idx),
        body_idx_b=-1,
        amplitude_deg=0.0,
        period_days=0.0,
        phase_rad=0.0,
        correlation=0,
        eccentricity=float(eccentricity),
        mean_anomaly_at_j2000_rad=float(mean_anomaly_at_j2000_rad),
        n_rad_per_day=float(n_rad_per_day),
    )
    return int(LIB.es_apply_patch(ctypes.byref(patch)))


def native_clear_patches() -> int:
    """Wipe the C-side patch registry. Returns prior count.

    No-op (returns 0) if HAS_NATIVE is False.
    """
    if not HAS_NATIVE:
        return 0
    assert LIB is not None
    return int(LIB.es_clear_patches())


def native_clear_eoc_patches() -> int:
    """Selectively clear only EOC patches (kind ==
    ``ES_PATCH_KIND_ECCENTRICITY_CORRECTION``) from the C-side
    registry. Sinusoid + coupled-sinusoid patches are left intact.
    Returns the count of EOC patches removed.

    Mirrors ``_eoc_catalog.clear_eoc_patches()`` on the Python side
    so the two registries stay in sync. v0.28.0rc5 (ABI v9).

    No-op (returns 0) if HAS_NATIVE is False.
    """
    if not HAS_NATIVE:
        return 0
    assert LIB is not None
    return int(LIB.es_clear_eoc_patches())


def native_n_active_patches() -> int:
    """Number of patches currently in the C-side registry; 0 if no native."""
    if not HAS_NATIVE:
        return 0
    assert LIB is not None
    return int(LIB.es_n_active_patches())


# ──────────────────────────────────────────────────────────────────────
# C/Python parity Tier 1 surface (ABI v3, v0.6.0)
# ──────────────────────────────────────────────────────────────────────


def native_breathing_modulation(delta_t_days: float, body_idx_a: int,
                                body_idx_b: int, n_a: int, n_b: int,
                                ) -> Tuple[int, int, float]:
    """Resonant-pair breathing modulation at a single JD.

    Returns ``(phase_residue, cos_q14, modulation_factor)``.

    Raises RuntimeError on any non-OK status from the C side.
    Caller-side guard required: only invoke when ``HAS_NATIVE`` is True.
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native_breathing_modulation called without native library"
        )
    assert LIB is not None
    out_phase = ctypes.c_uint32(0)
    out_cos_q14 = ctypes.c_int32(0)
    out_modulation = ctypes.c_double(0.0)
    rc = int(LIB.es_breathing_modulation(
        ctypes.c_double(float(delta_t_days)),
        ctypes.c_size_t(int(body_idx_a)),
        ctypes.c_size_t(int(body_idx_b)),
        ctypes.c_int(int(n_a)),
        ctypes.c_int(int(n_b)),
        ctypes.byref(out_phase),
        ctypes.byref(out_cos_q14),
        ctypes.byref(out_modulation),
    ))
    if rc != ES_OK:
        raise RuntimeError(
            f"es_breathing_modulation returned status {rc}"
        )
    return int(out_phase.value), int(out_cos_q14.value), float(out_modulation.value)


def native_find_syzygies(jd_lo: float, jd_hi: float, *,
                         kind: int = ES_SYZYGY_KIND_FILTER_ALL,
                         threshold: float = 0.05,
                         max_candidates: int = 1000,
                         out_capacity: int = 1024,
                         ) -> List[Dict[str, Any]]:
    """Enumerate syzygy candidates in [jd_lo, jd_hi] (TDB).

    Returns a list of dicts with keys jd_tdb, kind ('solar'/'lunar'),
    synodic_phase_resid, draconic_phase_resid, score.

    Raises RuntimeError on any non-OK status from the C side.
    Caller-side guard required: only invoke when ``HAS_NATIVE`` is True.

    The ``out_capacity`` parameter sizes the internal C-side buffer.
    If the actual count exceeds capacity, the result is truncated to
    capacity (matches behaviour of `max_candidates`); callers can
    raise ``out_capacity`` to recover.
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native_find_syzygies called without native library"
        )
    assert LIB is not None
    capacity = max(1, min(int(out_capacity), int(max_candidates)))
    buf = (EsSyzygy * capacity)()
    out_count = ctypes.c_size_t(0)
    rc = int(LIB.es_find_syzygies(
        ctypes.c_double(float(jd_lo)),
        ctypes.c_double(float(jd_hi)),
        ctypes.c_int(int(kind)),
        ctypes.c_double(float(threshold)),
        ctypes.c_size_t(int(max_candidates)),
        buf,
        ctypes.c_size_t(capacity),
        ctypes.byref(out_count),
    ))
    if rc != ES_OK:
        raise RuntimeError(f"es_find_syzygies returned status {rc}")
    n = int(out_count.value)
    n = min(n, capacity)
    out: List[Dict[str, Any]] = []
    for i in range(n):
        e = buf[i]
        kind_str = "solar" if e.kind == ES_SYZYGY_KIND_SOLAR else "lunar"
        out.append({
            "jd_tdb": float(e.jd_tdb),
            "kind": kind_str,
            "synodic_phase_resid": float(e.synodic_phase_resid),
            "draconic_phase_resid": float(e.draconic_phase_resid),
            "score": float(e.score),
        })
    return out


def native_encode_state_hd(delta_t_days: float, D: int) -> Any:
    """Run the C-side BIP encode + lift to D-dim hypervector.

    Returns a `numpy.complex64` array of length D (unit-norm).

    Caller-side guard required: only invoke when ``HAS_NATIVE`` is True.

    ABI v6 note: scratch buffers are allocated here in Python and passed
    by pointer; the C library no longer allocates internally (Rule 3).
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native_encode_state_hd called without native library"
        )
    assert LIB is not None
    import numpy as np
    buf = (EsComplex64 * D)()
    scratch_basis = (EsComplex64 * D)()
    scratch_rolled = (EsComplex64 * D)()
    rc = int(LIB.es_encode_state_hd(
        ctypes.c_double(float(delta_t_days)),
        buf,
        scratch_basis,
        scratch_rolled,
        ctypes.c_size_t(int(D)),
    ))
    if rc != ES_OK:
        raise RuntimeError(f"es_encode_state_hd returned status {rc}")
    return np.frombuffer(buf, dtype=np.complex64).copy()


def native_bind_observer(state: Any, body_idx: int, lat_deg: float,
                         lon_deg: float) -> Any:
    """Run the C-side topocentric observer-bind.

    `state` must be a numpy `complex64` array; the returned array is
    the same shape.

    ABI v6 note: scratch buffers allocated here (Rule 3).
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native_bind_observer called without native library"
        )
    assert LIB is not None
    import numpy as np
    state_c64 = np.ascontiguousarray(state, dtype=np.complex64)
    D = int(state_c64.shape[0])
    in_buf = state_c64.ctypes.data_as(ctypes.POINTER(EsComplex64))
    out_buf = (EsComplex64 * D)()
    scratch_body_basis = (EsComplex64 * D)()
    scratch_coord_basis = (EsComplex64 * D)()
    scratch_coord_op = (EsComplex64 * D)()
    rc = int(LIB.es_bind_observer(
        in_buf,
        ctypes.c_size_t(int(body_idx)),
        ctypes.c_double(float(lat_deg)),
        ctypes.c_double(float(lon_deg)),
        out_buf,
        scratch_body_basis,
        scratch_coord_basis,
        scratch_coord_op,
        ctypes.c_size_t(D),
    ))
    if rc != ES_OK:
        raise RuntimeError(f"es_bind_observer returned status {rc}")
    return np.frombuffer(out_buf, dtype=np.complex64).copy()


def native_get_eclipse_probability(state: Any, sun_body_idx: int,
                                    moon_body_idx: int) -> float:
    """Run the C-side syzygy projection. Returns scalar probability.

    ABI v6 note: scratch buffers allocated here (Rule 3).
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native_get_eclipse_probability called without native library"
        )
    assert LIB is not None
    import numpy as np
    state_c64 = np.ascontiguousarray(state, dtype=np.complex64)
    D = int(state_c64.shape[0])
    in_buf = state_c64.ctypes.data_as(ctypes.POINTER(EsComplex64))
    scratch_sun_b = (EsComplex64 * D)()
    scratch_moon_b = (EsComplex64 * D)()
    scratch_node_b = (EsComplex64 * D)()
    scratch_s_op = (EsComplex64 * D)()
    out_prob = ctypes.c_double(0.0)
    rc = int(LIB.es_get_eclipse_probability(
        in_buf,
        ctypes.c_size_t(D),
        ctypes.c_size_t(int(sun_body_idx)),
        ctypes.c_size_t(int(moon_body_idx)),
        scratch_sun_b,
        scratch_moon_b,
        scratch_node_b,
        scratch_s_op,
        ctypes.byref(out_prob),
    ))
    if rc != ES_OK:
        raise RuntimeError(
            f"es_get_eclipse_probability returned status {rc}"
        )
    return float(out_prob.value)


def native_channel_basis(seed: int, D: int) -> Any:
    """Generate a deterministic complex64 channel basis of dimension D.

    Returns a numpy array of dtype `complex64`, length `D`. Bit-
    identical to the Python-side `_research/portable_prng.splitmix64_phases`
    output passed through `exp(1j*phi)` and cast to complex64.

    Caller-side guard required: only invoke when ``HAS_NATIVE`` is True.
    """
    if not HAS_NATIVE:
        raise RuntimeError(
            "native_channel_basis called without native library"
        )
    assert LIB is not None
    import numpy as np
    buf = (EsComplex64 * D)()
    rc = int(LIB.es_channel_basis(
        ctypes.c_uint64(int(seed) & ((1 << 64) - 1)),
        buf,
        ctypes.c_size_t(int(D)),
    ))
    if rc != ES_OK:
        raise RuntimeError(f"es_channel_basis returned status {rc}")
    # Reinterpret the raw buffer as numpy complex64 without copy.
    arr = np.frombuffer(buf, dtype=np.complex64).copy()
    return arr


__all__ = [
    "HAS_NATIVE",
    "LIB",
    "LIB_PATH",
    "ABI_VERSION",
    "N_BODIES",
    "LOAD_ERROR",
    "EXPECTED_ABI_VERSION",
    "ES_PATCH_KIND_SINUSOID",
    "ES_PATCH_KIND_COUPLED_SINUSOID",
    "ES_MAX_PATCHES",
    "EsPatch",
    "EsSyzygy",
    "EsComplex64",
    "ES_SYZYGY_KIND_SOLAR",
    "ES_SYZYGY_KIND_LUNAR",
    "ES_SYZYGY_KIND_FILTER_SOLAR",
    "ES_SYZYGY_KIND_FILTER_LUNAR",
    "ES_SYZYGY_KIND_FILTER_ALL",
    "encode_state",
    "encode_at_jd",
    "native_version",
    "native_apply_sinusoid_patch",
    "native_apply_coupled_patch",
    "native_clear_patches",
    "native_n_active_patches",
    "native_breathing_modulation",
    "native_find_syzygies",
    "native_channel_basis",
    "native_encode_state_hd",
    "native_bind_observer",
    "native_get_eclipse_probability",
]
