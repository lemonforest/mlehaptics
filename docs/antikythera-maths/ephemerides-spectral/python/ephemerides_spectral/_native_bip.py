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
EXPECTED_ABI_VERSION: int = 3

# Mirrors c/include/ephemerides_spectral.h.
ES_PATCH_NAME_MAX: int = 64
ES_MAX_PATCHES: int = 32
ES_PATCH_KIND_SINUSOID: int = 0
ES_PATCH_KIND_COUPLED_SINUSOID: int = 1

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
    type drift here vs the ABI v2 layout would silently corrupt
    patch registration; the field layout is locked in by the C
    side's ``ES_ABI_VERSION = 2`` and the load-time abi-version check.
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


# ──────────────────────────────────────────────────────────────────────
# Module-level state
# ──────────────────────────────────────────────────────────────────────

_LIB_PATH: Optional[Path] = _find_library()
LIB: Optional[ctypes.CDLL] = None
LIB_PATH: Optional[Path] = None
ABI_VERSION: Optional[int] = None
N_BODIES: Optional[int] = None
HAS_NATIVE: bool = False
LOAD_ERROR: Optional[str] = None

if _LIB_PATH is not None:
    try:
        _candidate_lib = ctypes.CDLL(str(_LIB_PATH))
        _bind(_candidate_lib)
        version = int(_candidate_lib.es_abi_version())
        if version != EXPECTED_ABI_VERSION:
            LOAD_ERROR = (
                f"native ABI mismatch at {_LIB_PATH}: "
                f"binary is v{version}, Python expects v{EXPECTED_ABI_VERSION}; "
                "rebuild the C extension or fall back to pure Python."
            )
        else:
            LIB = _candidate_lib
            LIB_PATH = _LIB_PATH
            ABI_VERSION = version
            N_BODIES = int(_candidate_lib.es_n_bodies())
            HAS_NATIVE = True
    except (OSError, AttributeError, ValueError) as exc:
        LOAD_ERROR = f"failed to load {_LIB_PATH}: {exc}"
else:
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


def native_clear_patches() -> int:
    """Wipe the C-side patch registry. Returns prior count.

    No-op (returns 0) if HAS_NATIVE is False.
    """
    if not HAS_NATIVE:
        return 0
    assert LIB is not None
    return int(LIB.es_clear_patches())


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
]
