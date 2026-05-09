"""ctypes wrapper for the native cs_encoder_pure_phase_4d shared library
(1.18.0+).

C port of :func:`chess_spectral.encoder_pure_phase_4d.encode_4d_pure_phase`,
JPL-compliant, integer-arithmetic-throughout. Loads the library shipped
in the wheel under ``chess_spectral/_native/`` (alongside the
``cs_bitboard4d`` library and ``spectral`` / ``spectral_4d`` binaries).

Per ADR-001 fallback discipline: callers MUST guard usage with
``if HAS_NATIVE_PURE_PHASE: ...``; never assume the library is loadable.
The Python implementation in ``encoder_pure_phase_4d`` remains the
correctness reference; the C path is performance.

API surface
-----------

  * ``HAS_NATIVE_PURE_PHASE`` : bool
        True if the .so / .dll loaded successfully.
  * ``encode_pure_phase_4d_native(pos4) -> np.ndarray (45056,) int32``
        The C-side encoder. Bit-exact parity target with the Python
        reference on every position.

Mirrors the layout of :mod:`chess_spectral._native_bitboard4d`.
"""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np


N_SQUARES_4D: int = 4096
ENCODING_DIM_4D: int = 45_056

# Mirror of cs_position_4d_t in include/cs_types_4d.h. Fixed-size
# arrays per JPL discipline (no dynamic allocation).
_PieceArr = ctypes.c_int8 * N_SQUARES_4D
_AxisArr = ctypes.c_uint8 * N_SQUARES_4D


class _CsPosition4d(ctypes.Structure):
    _fields_ = [
        ("sq", _PieceArr),
        ("pawn_axis", _AxisArr),
    ]


class _CsPurePhaseEncoding4d(ctypes.Structure):
    _fields_ = [("v", ctypes.c_int32 * ENCODING_DIM_4D)]


def _candidate_library_names() -> list[str]:
    if sys.platform.startswith("win"):
        return ["cs_encoder_pure_phase_4d.dll"]
    if sys.platform == "darwin":
        return [
            "libcs_encoder_pure_phase_4d.dylib",
            "cs_encoder_pure_phase_4d.dylib",
        ]
    return [
        "libcs_encoder_pure_phase_4d.so",
        "cs_encoder_pure_phase_4d.so",
    ]


def _find_library() -> Optional[Path]:
    """Locate the shared library (mirrors _native_bitboard4d._find_library).

    Search order:
      1. Wheel install location: ``<package>/_native/``.
      2. ``CS_PURE_PHASE_4D_LIB`` env-var (absolute path).
      3. CMake build directory ``<repo>/build/{Release,release,…}/``.
    """
    pkg_native = Path(__file__).resolve().parent / "_native"
    candidates: list[Path] = []
    for name in _candidate_library_names():
        candidates.append(pkg_native / name)

    env = os.environ.get("CS_PURE_PHASE_4D_LIB")
    if env:
        candidates.insert(0, Path(env))

    build_dir = Path(__file__).resolve().parents[2] / "build"
    if build_dir.exists():
        for name in _candidate_library_names():
            candidates.append(build_dir / name)
        for cfg in ("release", "Release", "RelWithDebInfo"):
            for name in _candidate_library_names():
                candidates.append(build_dir / cfg / name)

    # Also check the CMake test directory used during dev.
    test_build = Path(__file__).resolve().parents[2] / "build_test"
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
    lib.cs_encode_pure_phase_4d.argtypes = [
        ctypes.POINTER(_CsPosition4d),
        ctypes.POINTER(_CsPurePhaseEncoding4d),
    ]
    lib.cs_encode_pure_phase_4d.restype = None


# ──────────────────────────────────────────────────────────────────────
# One-shot load. Failure is non-fatal — the package still imports and
# HAS_NATIVE_PURE_PHASE reports False.
# ──────────────────────────────────────────────────────────────────────

_LIB_PATH: Optional[Path] = _find_library()
_LIB: Optional[ctypes.CDLL] = None
HAS_NATIVE_PURE_PHASE: bool = False

if _LIB_PATH is not None:
    try:
        _LIB = ctypes.CDLL(str(_LIB_PATH))
        _bind(_LIB)
        HAS_NATIVE_PURE_PHASE = True
    except (OSError, AttributeError):
        _LIB = None
        HAS_NATIVE_PURE_PHASE = False


# ──────────────────────────────────────────────────────────────────────
# Position dict → cs_position_4d_t marshalling.
# ──────────────────────────────────────────────────────────────────────


# Pawn axis labels in the C struct (matches CS_PAWN_AXIS_W / Y).
_PAWN_AXIS_W = 0
_PAWN_AXIS_Y = 1


def _build_c_position(
    pos4: Dict[Union[int, str], object],
) -> _CsPosition4d:
    """Marshal a Python position dict into a cs_position_4d_t."""
    cpos = _CsPosition4d()
    # ctypes.Structure default-inits to zero (memset-equivalent), so
    # empty squares and W-axis defaults are correct out of the gate.
    for k, pval in pos4.items():
        s = int(k)
        if not (0 <= s < N_SQUARES_4D):
            raise ValueError(f"square index {s} out of range")
        if isinstance(pval, tuple):
            color, axis = pval
            cpos.sq[s] = ord(color)
            if axis == 'y':
                cpos.pawn_axis[s] = _PAWN_AXIS_Y
            elif axis == 'w':
                cpos.pawn_axis[s] = _PAWN_AXIS_W
            else:
                raise ValueError(
                    f"pawn axis must be 'y' or 'w'; got {axis!r}"
                )
        elif isinstance(pval, str) and len(pval) == 1:
            cpos.sq[s] = ord(pval)
            # pawn_axis stays at 0 (W) which matches the legacy
            # single-char-pawn convention.
        else:
            raise TypeError(
                f"pos4[{s}] must be a single-char str or "
                f"(color, axis) tuple; got {pval!r}"
            )
    return cpos


def encode_pure_phase_4d_native(
    pos4: Dict[Union[int, str], object],
) -> np.ndarray:
    """Native C path for the pure-phase 4D encoder.

    Returns a copy as a numpy ndarray of shape ``(45056,)`` dtype
    ``int32`` — bit-exact identical to
    :func:`chess_spectral.encoder_pure_phase_4d.encode_4d_pure_phase`
    on every position.

    Raises
    ------
    RuntimeError
        If the native library isn't loaded
        (``HAS_NATIVE_PURE_PHASE`` is False).
    """
    if not HAS_NATIVE_PURE_PHASE or _LIB is None:
        raise RuntimeError(
            "native cs_encoder_pure_phase_4d.dll/.so not loaded; "
            "install the wheel with C-toolchain support, or set "
            "CS_PURE_PHASE_4D_LIB to the library path."
        )
    cpos = _build_c_position(pos4)
    enc = _CsPurePhaseEncoding4d()
    _LIB.cs_encode_pure_phase_4d(
        ctypes.byref(cpos), ctypes.byref(enc),
    )
    # Copy to numpy (avoid keeping ctypes alive in the result).
    out = np.frombuffer(
        bytes(enc.v), dtype=np.int32, count=ENCODING_DIM_4D,
    ).copy()
    return out


__all__ = [
    "HAS_NATIVE_PURE_PHASE",
    "encode_pure_phase_4d_native",
    "N_SQUARES_4D",
    "ENCODING_DIM_4D",
]
