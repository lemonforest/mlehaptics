"""Python <-> C encoder parity regression.

Runs encode_768 through both the Python reference and the C
reference binary, asserts byte-for-byte equality at float32
precision.

The C binary must be built first:

    cd docs/othello-maths/research
    python -m othello_spectral.codegen.emit_c_tables
    cc -std=c17 -Wall -Wextra -O2 \\
       -I othello_spectral/c_encoder/include \\
       othello_spectral/c_encoder/src/othello_spectral.c \\
       othello_spectral/c_encoder/src/encode_cli.c \\
       -o othello_spectral/c_encoder/encode_cli

Then this test spawns encode_cli as a subprocess, feeds it OBF
strings, captures its 768 float32 LE output, compares against the
Python encoder's output cast to float32.

The test is skipped (not FAILED) if the C binary does not exist,
so the smoke-test suite remains runnable in Python-only setups.
"""

from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from othello_spectral import encode_768  # noqa: E402
from othello_spectral.tables import ENCODING_DIM  # noqa: E402


_BINARY_CANDIDATES = [
    _RESEARCH_DIR / "othello_spectral" / "c_encoder" / "encode_cli",
    _RESEARCH_DIR / "othello_spectral" / "c_encoder" / "encode_cli.exe",
]


def _find_binary() -> Path | None:
    for p in _BINARY_CANDIDATES:
        if p.exists():
            return p
    return None


def _state_to_obf(state: np.ndarray, side_is_black: bool = True) -> str:
    """Encode a length-64 state in {-1, 0, +1} to OBF.  The encoder
    is state-only so side-to-move's role here is just to emit a
    syntactically-valid OBF."""
    out = []
    for v in state:
        if v == 0:
            out.append("-")
        elif v == 1:
            out.append("X")
        elif v == -1:
            out.append("O")
        else:
            raise ValueError(f"state value out of range: {v}")
    return "".join(out) + " " + ("X" if side_is_black else "O") + ";"


def _c_encode(binary: Path, obf: str) -> np.ndarray:
    """Run the C binary with --obf and return its 768-dim float32 array."""
    result = subprocess.run(
        [str(binary), "--obf", obf],
        capture_output=True, check=True,
    )
    raw = result.stdout
    expected = 4 * ENCODING_DIM
    if len(raw) != expected:
        raise RuntimeError(
            f"C binary emitted {len(raw)} bytes, expected {expected}"
        )
    arr = np.array(
        struct.unpack(f"<{ENCODING_DIM}f", raw), dtype=np.float32,
    )
    return arr


def _random_state(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.choice([-1, 0, 1], size=64, p=[0.4, 0.2, 0.4]).astype(int)


def _starting_state() -> np.ndarray:
    s = np.zeros(64, dtype=int)
    s[3 * 8 + 3] = -1
    s[3 * 8 + 4] = +1
    s[4 * 8 + 3] = +1
    s[4 * 8 + 4] = -1
    return s


def test_c_py_parity_starting_position() -> None:
    binary = _find_binary()
    if binary is None:
        print("SKIP (C binary not built)")
        return
    s = _starting_state()
    py_f32 = np.asarray(encode_768(s), dtype=np.float32)
    c_f32 = _c_encode(binary, _state_to_obf(s))
    # Byte-for-byte at float32 precision
    assert np.array_equal(py_f32, c_f32), (
        f"parity failure on starting position: "
        f"{int(np.sum(py_f32 != c_f32))} of {len(py_f32)} dims differ; "
        f"first mismatches: "
        f"{[(i, float(py_f32[i]), float(c_f32[i])) for i in np.where(py_f32 != c_f32)[0][:5]]}"
    )


def test_c_py_parity_random_states() -> None:
    binary = _find_binary()
    if binary is None:
        print("SKIP (C binary not built)")
        return
    for seed in (1, 2, 3, 7, 11, 17, 42, 100):
        s = _random_state(seed)
        py_f32 = np.asarray(encode_768(s), dtype=np.float32)
        c_f32 = _c_encode(binary, _state_to_obf(s))
        assert np.array_equal(py_f32, c_f32), (
            f"parity failure on seed {seed}"
        )


def test_ctypes_dll_parity_if_present() -> None:
    """If a DLL is built, verify encode_768_c_ctypes matches Python
    at float64 precision across 8 random states."""
    from othello_spectral.runtime import find_c_dll, encode_768_c_ctypes
    try:
        dll = find_c_dll()
    except FileNotFoundError:
        dll = None
    if dll is None:
        print("SKIP (DLL not built)")
        return
    for seed in (1, 2, 3, 7, 11, 17, 42, 100):
        s = _random_state(seed)
        py_f64 = np.asarray(encode_768(s), dtype=np.float64)
        c_f64 = encode_768_c_ctypes(s)
        assert np.array_equal(py_f64, c_f64), (
            f"ctypes parity failure on seed {seed}: "
            f"{int(np.sum(py_f64 != c_f64))} of {len(py_f64)} dims differ"
        )


ALL_TESTS = [
    test_c_py_parity_starting_position,
    test_c_py_parity_random_states,
    test_ctypes_dll_parity_if_present,
]


if __name__ == "__main__":
    binary = _find_binary()
    if binary is None:
        print(
            "C binary not found.  Build first:\n"
            "  cd docs/othello-maths/research\n"
            "  python -m othello_spectral.codegen.emit_c_tables\n"
            "  cc -std=c17 -Wall -Wextra -O2 "
            "-I othello_spectral/c_encoder/include \\\n"
            "     othello_spectral/c_encoder/src/othello_spectral.c \\\n"
            "     othello_spectral/c_encoder/src/encode_cli.c \\\n"
            "     -o othello_spectral/c_encoder/encode_cli"
        )
        sys.exit(0)
    print(f"using binary: {binary}")
    # Print the C binary version as a sanity check
    ver = subprocess.run(
        [str(binary), "--version"], capture_output=True, check=True, text=True,
    ).stdout.strip()
    print(f"binary version string: {ver!r}")

    failures = 0
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            print(f"FAIL  {fn.__name__}: {exc}")
            failures += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failures += 1
    if failures:
        print(f"\n{failures} failures")
        sys.exit(1)
    print("\nall C/Py parity tests passed")
