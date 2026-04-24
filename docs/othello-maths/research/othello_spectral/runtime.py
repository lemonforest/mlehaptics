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
    # first float32 against Python's.
    import numpy as _np
    s = _np.zeros(64, dtype=int)
    s[3 * 8 + 3] = -1  # d4 white
    s[3 * 8 + 4] = +1  # e4 black
    s[4 * 8 + 3] = +1  # d5 black
    s[4 * 8 + 4] = -1  # e5 white
    obf = "".join(
        {0: "-", 1: "X", -1: "O"}[int(v)] for v in s
    ) + " X;"
    try:
        out = subprocess.run(
            [str(binary), "--obf", obf],
            capture_output=True, check=True, timeout=10.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"--obf smoke-test failed: {exc}"
    if len(out.stdout) != 4 * ENCODING_DIM:
        return False, (
            f"binary emitted {len(out.stdout)} bytes; expected "
            f"{4 * ENCODING_DIM}"
        )
    c_arr = _np.array(
        struct.unpack(f"<{ENCODING_DIM}f", out.stdout),
        dtype=_np.float32,
    )
    py_arr = _np.asarray(_py_encode(s), dtype=_np.float32)
    if not _np.array_equal(c_arr, py_arr):
        n_diff = int(_np.sum(c_arr != py_arr))
        return False, (
            f"binary output does NOT match Python: {n_diff} of "
            f"{ENCODING_DIM} dims differ at float32 precision"
        )
    return True, "ok"


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


def encode_768_c_stream(
    states: Iterable, binary: Path,
) -> list[np.ndarray]:
    """Stream many states through a single C subprocess via
    --stdin-stream mode.  Amortises subprocess startup over the
    full batch.  Returns a list of float64 arrays (one per state).
    """
    states = list(states)
    proc = subprocess.Popen(
        [str(binary), "--stdin-stream"],
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
