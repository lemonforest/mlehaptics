"""Engine dispatch for othello_spectral (py | c | auto).

Mirrors chess-spectral's encoder-choice pattern with a few minor
upgrades:

  - adds an explicit ``auto`` mode (prefer C if available, silent
    fallback to Python)
  - env var ``OTHELLO_SPECTRAL_BIN`` overrides the binary search path
  - env var ``OTHELLO_SPECTRAL_ENGINE`` (py / c / auto) sets the
    default engine when CLI / caller doesn't explicitly pick one

Public API
----------
  find_c_binary()     -> Path | None
  resolve_engine(req) -> (engine: str, binary: Path | None)
  encode_768_c(state, binary)       : single-state via subprocess
  encode_768_c_stream(states, binary): many states via one subprocess
"""

from __future__ import annotations

import ctypes
import os
import struct
import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np

from .tables import ENCODING_DIM


_DEFAULT_ENGINE_FROM_ENV = os.environ.get(
    "OTHELLO_SPECTRAL_ENGINE", "auto",
).strip().lower() or "auto"


def default_engine() -> str:
    """Return the default engine based on env var (or 'auto')."""
    return _DEFAULT_ENGINE_FROM_ENV


def find_c_dll() -> Path | None:
    """Locate the encoder shared library.

    Search order:
      1. OTHELLO_SPECTRAL_DLL env var (exact path)
      2. c_encoder/othello_spectral.{dll,so,dylib} (relative to pkg)
    """
    env_override = os.environ.get("OTHELLO_SPECTRAL_DLL")
    if env_override:
        p = Path(env_override)
        if p.is_file():
            return p
        raise FileNotFoundError(
            f"OTHELLO_SPECTRAL_DLL={p!s} set but file does not exist"
        )
    base = Path(__file__).resolve().parent / "c_encoder"
    for suffix in ("dll", "so", "dylib"):
        p = base / f"othello_spectral.{suffix}"
        if p.exists():
            return p
    return None


_DLL_HANDLE = None
_DLL_PATH: Path | None = None

_FIBER_MODE_CODES = {"rank2": 0, "sheaf": 1}


def _load_dll() -> tuple[ctypes.CDLL | None, Path | None]:
    """Load the shared library once; cache the handle.  Returns
    (handle, path) or (None, None) if the DLL is not present or
    fails to load / declare signatures."""
    global _DLL_HANDLE, _DLL_PATH
    if _DLL_HANDLE is not None:
        return _DLL_HANDLE, _DLL_PATH
    try:
        dll = find_c_dll()
    except FileNotFoundError:
        return None, None
    if dll is None:
        return None, None
    try:
        handle = ctypes.CDLL(str(dll))
        handle.othello_spectral_encode_768.restype = ctypes.c_int
        handle.othello_spectral_encode_768.argtypes = [
            ctypes.POINTER(ctypes.c_int8),
            ctypes.POINTER(ctypes.c_double),
        ]
        # v0.3.0: encode_768_v2 lets the caller pick the fiber mode.
        # Tolerate missing symbol on older DLLs and fall back to the
        # rank-2 only code path.
        if hasattr(handle, "othello_spectral_encode_768_v2"):
            handle.othello_spectral_encode_768_v2.restype = ctypes.c_int
            handle.othello_spectral_encode_768_v2.argtypes = [
                ctypes.POINTER(ctypes.c_int8),
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_double),
            ]
    except (OSError, AttributeError) as exc:
        print(
            f"[othello_spectral.runtime] failed to load DLL {dll}: {exc}",
        )
        return None, None
    _DLL_HANDLE = handle
    _DLL_PATH = dll
    return handle, dll


def encode_768_c_ctypes(
    state, fiber_mode: str = "rank2",
) -> np.ndarray:
    """Call the C encoder via ctypes.  Returns a float64 numpy
    array.

    fiber_mode:
      - 'rank2' (backwards-compat; v0.2.0 or v0.3.0 DLL)
      - 'sheaf' (v0.3.0+ only; requires encode_768_v2 symbol)
    """
    handle, _ = _load_dll()
    if handle is None:
        raise RuntimeError(
            "No C encoder DLL available.  Build with "
            "`clang -shared` per c_encoder/README.md, or set "
            "OTHELLO_SPECTRAL_DLL."
        )
    if fiber_mode not in _FIBER_MODE_CODES:
        raise ValueError(
            f"unknown fiber_mode {fiber_mode!r}; expected 'rank2' "
            f"or 'sheaf'"
        )
    code = _FIBER_MODE_CODES[fiber_mode]
    if code != 0 and not hasattr(
        handle, "othello_spectral_encode_768_v2",
    ):
        raise RuntimeError(
            f"DLL does not export encode_768_v2 (v0.2.0 binary?); "
            f"cannot run fiber_mode={fiber_mode}.  Rebuild with "
            f"v0.3.0 source."
        )

    s = np.ascontiguousarray(
        np.asarray(state, dtype=np.int8), dtype=np.int8,
    )
    if s.shape != (64,):
        raise ValueError(
            f"state must have shape (64,), got {s.shape}"
        )
    out = np.zeros(ENCODING_DIM, dtype=np.float64)
    if code == 0:
        rc = handle.othello_spectral_encode_768(
            s.ctypes.data_as(ctypes.POINTER(ctypes.c_int8)),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
    else:
        rc = handle.othello_spectral_encode_768_v2(
            s.ctypes.data_as(ctypes.POINTER(ctypes.c_int8)),
            code,
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
    if rc != 0:
        raise RuntimeError(f"encode_768 returned nonzero status {rc}")
    return out


def find_c_binary() -> Path | None:
    """Locate the encode_cli binary.

    Search order:
      1. OTHELLO_SPECTRAL_BIN env var (exact path)
      2. c_encoder/encode_cli    (relative to the package)
      3. c_encoder/encode_cli.exe
    """
    env_override = os.environ.get("OTHELLO_SPECTRAL_BIN")
    if env_override:
        p = Path(env_override)
        if p.is_file():
            return p
        raise FileNotFoundError(
            f"OTHELLO_SPECTRAL_BIN={p!s} set but file does not exist"
        )
    default = Path(__file__).resolve().parent / "c_encoder" / "encode_cli"
    if default.exists():
        return default
    default_exe = default.with_suffix(".exe")
    if default_exe.exists():
        return default_exe
    return None


def verify_c_binary(binary: Path) -> tuple[bool, str]:
    """Verify that a binary at ``binary`` is a working othello-spectral
    encoder at the current package VERSION.  Returns (ok, reason).

    Two checks:
      1. --version string matches the Python package VERSION.
      2. Encoding the starting Othello position via --obf gives
         the expected 3072 bytes, and the first float32 value
         matches the Python-side encode_768 output for that
         state at float32 precision.
    """
    # Lazy import to avoid pulling encoder into runtime import
    from . import VERSION as _VERSION
    from .encoder import encode_768 as _py_encode

    try:
        ver_result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True, check=True, text=True,
            timeout=10.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"--version invocation failed: {exc}"
    ver = ver_result.stdout.strip()
    if ver != _VERSION:
        return False, (
            f"binary VERSION={ver!r} does not match package "
            f"VERSION={_VERSION!r}"
        )

    # Functional sanity: encode the starting position and compare
    # C output against Python on BOTH fiber modes if the binary
    # supports them.  At v0.3.0 the C binary handles rank2 and sheaf
    # via --fiber flag; older binaries only handle rank2 (no --fiber
    # flag) and are verified on rank2 alone.
    import numpy as _np
    s = _np.zeros(64, dtype=int)
    s[3 * 8 + 3] = -1  # d4 white
    s[3 * 8 + 4] = +1  # e4 black
    s[4 * 8 + 3] = +1  # d5 black
    s[4 * 8 + 4] = -1  # e5 white
    obf = "".join(
        {0: "-", 1: "X", -1: "O"}[int(v)] for v in s
    ) + " X;"

    def _check_mode(fiber_arg: str | None) -> tuple[bool, str]:
        cmd = [str(binary), "--obf", obf]
        if fiber_arg is not None:
            cmd += ["--fiber", fiber_arg]
        try:
            out = subprocess.run(
                cmd, capture_output=True, check=True, timeout=10.0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return False, f"binary invocation failed: {exc}"
        if len(out.stdout) != 4 * ENCODING_DIM:
            return False, (
                f"binary emitted {len(out.stdout)} bytes; expected "
                f"{4 * ENCODING_DIM}"
            )
        c_arr = _np.array(
            struct.unpack(f"<{ENCODING_DIM}f", out.stdout),
            dtype=_np.float32,
        )
        py_mode = fiber_arg if fiber_arg else "rank2"
        py_arr = _np.asarray(
            _py_encode(s, fiber_mode=py_mode), dtype=_np.float32,
        )
        if not _np.array_equal(c_arr, py_arr):
            n_diff = int(_np.sum(c_arr != py_arr))
            return False, (
                f"binary output (fiber={py_mode}) does NOT match "
                f"Python: {n_diff}/{ENCODING_DIM} dims differ "
                f"at float32 precision"
            )
        return True, "ok"

    # Rank-2 always supported.
    ok, reason = _check_mode(None)
    if not ok:
        return False, f"rank2 parity check failed: {reason}"
    # Sheaf supported iff binary recognises --fiber.  Probe with
    # --fiber sheaf; if that errors out, binary is rank2-only.
    ok_sheaf, reason_sheaf = _check_mode("sheaf")
    if not ok_sheaf:
        return True, (
            f"ok (rank2 parity; sheaf parity unavailable — "
            f"{reason_sheaf})"
        )
    return True, "ok (rank2 + sheaf parity)"


def resolve_engine(
    requested: str = "auto",
    *,
    verify: bool = True,
) -> tuple[str, Path | None]:
    """Resolve an engine request to ('py'|'c', binary path or None).

    - 'py':  always Python reference; no binary.
    - 'c':   requires a resolvable binary.  With verify=True (default)
             the binary is smoke-tested for version + byte-identical
             output on the starting position.  Raises if either
             discovery OR verification fails.
    - 'auto': prefer C if a verified binary is available; silently
              fall back to Python on any failure.
    """
    requested = (requested or "auto").strip().lower()
    if requested == "py":
        return "py", None
    if requested == "c":
        binary = find_c_binary()
        if binary is None:
            raise FileNotFoundError(
                "engine='c' requested but no C binary found.  "
                "Build via `clang -std=c17 ...` from "
                "c_encoder/README.md or set OTHELLO_SPECTRAL_BIN."
            )
        if verify:
            ok, reason = verify_c_binary(binary)
            if not ok:
                raise RuntimeError(
                    f"engine='c': binary at {binary!s} failed "
                    f"verification: {reason}"
                )
        return "c", binary
    if requested == "auto":
        binary = find_c_binary()
        if binary is None:
            return "py", None
        if verify:
            ok, _reason = verify_c_binary(binary)
            if not ok:
                return "py", None
        return "c", binary
    raise ValueError(
        f"unknown engine {requested!r}; expected 'py', 'c', or 'auto'."
    )


def _state_to_bytes(state) -> bytes:
    """Convert a length-64 int-like state to raw int8 bytes (two's
    complement, little-endian is irrelevant for 8-bit values)."""
    buf = bytearray(64)
    for i in range(64):
        v = int(state[i])
        if v not in (-1, 0, 1):
            raise ValueError(
                f"state[{i}] = {v} out of valid range {-1, 0, 1}"
            )
        buf[i] = v & 0xff
    return bytes(buf)


def encode_768_c(state, binary: Path) -> np.ndarray:
    """Encode a single state via a subprocess call to the C binary.

    Returns a 768-dim float64 array (upcasted from the C binary's
    float32 output).  See encode_768_c_stream for batch use.
    """
    proc = subprocess.run(
        [str(binary), "--stdin"],
        input=_state_to_bytes(state),
        capture_output=True, check=True,
    )
    if len(proc.stdout) != 4 * ENCODING_DIM:
        raise RuntimeError(
            f"C binary emitted {len(proc.stdout)} bytes, "
            f"expected {4 * ENCODING_DIM}"
        )
    arr = np.array(
        struct.unpack(f"<{ENCODING_DIM}f", proc.stdout), dtype=np.float32,
    )
    return arr.astype(np.float64)


def encode_768_c_ctypes_batch(
    states, fiber_mode: str = "rank2",
) -> list[np.ndarray]:
    """Batch-apply encode_768 via the DLL (one ctypes call per
    state, no subprocess).  Returns a list of float64 arrays.

    fiber_mode: 'rank2' (default) or 'sheaf' (requires v0.3.0+ DLL).
    """
    handle, _ = _load_dll()
    if handle is None:
        raise RuntimeError(
            "No C encoder DLL available.  Build per c_encoder/README.md."
        )
    if fiber_mode not in _FIBER_MODE_CODES:
        raise ValueError(f"unknown fiber_mode {fiber_mode!r}")
    code = _FIBER_MODE_CODES[fiber_mode]
    if code != 0 and not hasattr(
        handle, "othello_spectral_encode_768_v2",
    ):
        raise RuntimeError(
            f"DLL does not export encode_768_v2; cannot run "
            f"fiber_mode={fiber_mode}.  Rebuild at v0.3.0."
        )
    out_list: list[np.ndarray] = []
    for s in states:
        arr = np.ascontiguousarray(
            np.asarray(s, dtype=np.int8), dtype=np.int8,
        )
        if arr.shape != (64,):
            raise ValueError(
                f"state must have shape (64,), got {arr.shape}"
            )
        out = np.zeros(ENCODING_DIM, dtype=np.float64)
        if code == 0:
            rc = handle.othello_spectral_encode_768(
                arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int8)),
                out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            )
        else:
            rc = handle.othello_spectral_encode_768_v2(
                arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int8)),
                code,
                out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            )
        if rc != 0:
            raise RuntimeError(
                f"encode_768 returned nonzero status {rc}"
            )
        out_list.append(out)
    return out_list


def encode_768_c_stream(
    states: Iterable, binary: Path,
    fiber_mode: str = "rank2",
) -> list[np.ndarray]:
    """Stream many states through a single C subprocess via
    --stdin-stream mode.  Amortises subprocess startup over the
    full batch.  Returns a list of float64 arrays (one per state).

    fiber_mode: 'rank2' (v0.2.0 default) or 'sheaf' (v0.3.0+).
    """
    states = list(states)
    cmd = [str(binary), "--stdin-stream", "--fiber", fiber_mode]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Write all states
    buf = b"".join(_state_to_bytes(s) for s in states)
    stdout, stderr = proc.communicate(input=buf)
    if proc.returncode != 0:
        raise RuntimeError(
            f"C binary returned {proc.returncode}.  stderr: "
            f"{stderr.decode(errors='replace')[:400]}"
        )
    expected = 4 * ENCODING_DIM * len(states)
    if len(stdout) != expected:
        raise RuntimeError(
            f"C stream emitted {len(stdout)} bytes, expected {expected}"
        )
    out: list[np.ndarray] = []
    for i in range(len(states)):
        raw = stdout[i * 4 * ENCODING_DIM:(i + 1) * 4 * ENCODING_DIM]
        arr = np.array(
            struct.unpack(f"<{ENCODING_DIM}f", raw), dtype=np.float32,
        )
        out.append(arr.astype(np.float64))
    return out


__all__ = [
    "default_engine",
    "find_c_binary",
    "resolve_engine",
    "encode_768_c",
    "encode_768_c_stream",
]
