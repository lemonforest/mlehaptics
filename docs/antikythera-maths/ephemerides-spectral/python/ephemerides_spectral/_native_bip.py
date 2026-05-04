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
from typing import List, Optional

import numpy as np


# Mirror of ``ES_ABI_VERSION`` in the C header. Bump in lockstep with
# the C side whenever the wire format of any exported function
# changes. v1 = the v0.3.1 baseline.
EXPECTED_ABI_VERSION: int = 1

#: Status codes from ``es_status_t``.
ES_OK = 0
ES_ERR_DELTA_OUT_OF_RANGE = 1
ES_ERR_NULL_OUTPUT = 2
ES_ERR_NON_FINITE_INPUT = 3


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


__all__ = [
    "HAS_NATIVE",
    "LIB",
    "LIB_PATH",
    "ABI_VERSION",
    "N_BODIES",
    "LOAD_ERROR",
    "EXPECTED_ABI_VERSION",
    "encode_state",
    "encode_at_jd",
    "native_version",
]
