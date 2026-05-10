"""ctypes wrapper for the native cs_encoder_pure_phase_2d shared library
(1.19.0+).

C port of :func:`chess_spectral.encoder_pure_phase.encode_2d_pure_phase`,
JPL-compliant, integer-arithmetic-throughout. Loads the library shipped
in the wheel under ``chess_spectral/_native/`` (alongside the
``cs_bitboard4d``, ``cs_encoder_pure_phase_4d``, and ``spectral`` /
``spectral_4d`` binaries).

Per ADR-001 fallback discipline: callers MUST guard usage with
``if HAS_NATIVE_PURE_PHASE_2D: ...``; never assume the library is
loadable. The Python implementation in
:mod:`chess_spectral.encoder_pure_phase` remains the correctness
reference; the C path is performance.

API surface
-----------

  * ``HAS_NATIVE_PURE_PHASE_2D`` : bool
        True if the .so / .dll loaded successfully.
  * ``encode_pure_phase_2d_native(pos) -> np.ndarray (640,) int32``
        The C-side encoder. Bit-exact parity target with the Python
        reference on every position.

Mirrors the layout of :mod:`chess_spectral._native_pure_phase_4d`.
"""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np


N_SQUARES_2D: int = 64
ENCODING_DIM_2D: int = 640

# Mirror of cs_pure_phase_position_2d_t in
# include/cs_encoder_pure_phase_2d.h. Fixed-size piece char array per
# JPL discipline (no dynamic allocation).
_PieceArr2D = ctypes.c_int8 * N_SQUARES_2D


class _CsPurePhasePosition2d(ctypes.Structure):
    _fields_ = [("sq", _PieceArr2D)]


class _CsPurePhaseEncoding2d(ctypes.Structure):
    _fields_ = [("v", ctypes.c_int32 * ENCODING_DIM_2D)]


def _candidate_library_names() -> list[str]:
    if sys.platform.startswith("win"):
        return ["cs_encoder_pure_phase_2d.dll"]
    if sys.platform == "darwin":
        return [
            "libcs_encoder_pure_phase_2d.dylib",
            "cs_encoder_pure_phase_2d.dylib",
        ]
    return [
        "libcs_encoder_pure_phase_2d.so",
        "cs_encoder_pure_phase_2d.so",
    ]


def _find_library() -> Optional[Path]:
    """Locate the shared library (mirrors _native_pure_phase_4d._find_library).

    Search order:
      1. Wheel install location: ``<package>/_native/``.
      2. ``CS_PURE_PHASE_2D_LIB`` env-var (absolute path).
      3. CMake build directory ``<repo>/build/{Release,release,…}/``.
      4. Dev test build dirs (``build_test``, ``build_test_2d``).
    """
    pkg_native = Path(__file__).resolve().parent / "_native"
    candidates: list[Path] = []
    for name in _candidate_library_names():
        candidates.append(pkg_native / name)

    env = os.environ.get("CS_PURE_PHASE_2D_LIB")
    if env:
        candidates.insert(0, Path(env))

    build_dir = Path(__file__).resolve().parents[2] / "build"
    if build_dir.exists():
        for name in _candidate_library_names():
            candidates.append(build_dir / name)
        for cfg in ("release", "Release", "RelWithDebInfo"):
            for name in _candidate_library_names():
                candidates.append(build_dir / cfg / name)

    for sub in ("build_test", "build_test_2d"):
        test_build = Path(__file__).resolve().parents[2] / sub
        if test_build.exists():
            for cfg in ("Release",):
                for name in _candidate_library_names():
                    candidates.append(test_build / cfg / name)

    for p in candidates:
        if p.exists():
            return p
    return None


def _bind(lib: ctypes.CDLL) -> None:
    """Set argtypes / restype for every exported C symbol used."""
    lib.cs_encode_pure_phase_2d.argtypes = [
        ctypes.POINTER(_CsPurePhasePosition2d),
        ctypes.POINTER(_CsPurePhaseEncoding2d),
    ]
    lib.cs_encode_pure_phase_2d.restype = None


# ──────────────────────────────────────────────────────────────────────
# One-shot load. Failure is non-fatal — the package still imports and
# HAS_NATIVE_PURE_PHASE_2D reports False.
# ──────────────────────────────────────────────────────────────────────

_LIB_PATH: Optional[Path] = _find_library()
_LIB: Optional[ctypes.CDLL] = None
HAS_NATIVE_PURE_PHASE_2D: bool = False

if _LIB_PATH is not None:
    try:
        _LIB = ctypes.CDLL(str(_LIB_PATH))
        _bind(_LIB)
        HAS_NATIVE_PURE_PHASE_2D = True
    except (OSError, AttributeError):
        _LIB = None
        HAS_NATIVE_PURE_PHASE_2D = False


# ──────────────────────────────────────────────────────────────────────
# Position dict → cs_pure_phase_position_2d_t marshalling.
# ──────────────────────────────────────────────────────────────────────


def _build_c_position(
    pos: Dict[Union[int, str], str],
) -> _CsPurePhasePosition2d:
    """Marshal a Python position dict into a cs_pure_phase_position_2d_t.

    Accepts both int- and str-keyed dicts (NDJSON-friendly). Empty
    squares are zero-initialized by ctypes default.
    """
    cpos = _CsPurePhasePosition2d()
    if not pos:
        return cpos
    for k, pchar in pos.items():
        s = int(k)
        if not (0 <= s < N_SQUARES_2D):
            raise ValueError(f"square index {s} out of range")
        if not isinstance(pchar, str) or len(pchar) != 1:
            raise TypeError(
                f"pos[{s}] must be a single-char piece string; got {pchar!r}"
            )
        cpos.sq[s] = ord(pchar)
    return cpos


def encode_pure_phase_2d_native(
    pos: Dict[Union[int, str], str],
) -> np.ndarray:
    """Native C path for the pure-phase 2D encoder.

    Returns a copy as a numpy ndarray of shape ``(640,)`` dtype
    ``int32`` — bit-exact identical to
    :func:`chess_spectral.encoder_pure_phase.encode_2d_pure_phase`
    on every position.

    Raises
    ------
    RuntimeError
        If the native library isn't loaded
        (``HAS_NATIVE_PURE_PHASE_2D`` is False).
    """
    if not HAS_NATIVE_PURE_PHASE_2D or _LIB is None:
        raise RuntimeError(
            "native cs_encoder_pure_phase_2d.dll/.so not loaded; "
            "install the wheel with C-toolchain support, or set "
            "CS_PURE_PHASE_2D_LIB to the library path."
        )
    cpos = _build_c_position(pos)
    enc = _CsPurePhaseEncoding2d()
    _LIB.cs_encode_pure_phase_2d(
        ctypes.byref(cpos), ctypes.byref(enc),
    )
    # Copy to numpy (avoid keeping ctypes alive in the result).
    out = np.frombuffer(
        bytes(enc.v), dtype=np.int32, count=ENCODING_DIM_2D,
    ).copy()
    return out


__all__ = [
    "HAS_NATIVE_PURE_PHASE_2D",
    "encode_pure_phase_2d_native",
    "N_SQUARES_2D",
    "ENCODING_DIM_2D",
]
