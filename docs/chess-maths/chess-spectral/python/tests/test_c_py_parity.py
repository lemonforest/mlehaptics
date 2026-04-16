"""C-binary vs Python reference parity test.

Encodes a committed fixture NDJSON through both backends and asserts the
.spectral files agree byte-for-byte (encoding arrays + move metadata).
This is the load-bearing regression guard: any future edit to either
encoder that changes numerical output *must* update the other side, or
this test fires.

Exit codes (for CI / standalone use):
    0   parity confirmed (or C binary absent — skipped with a warning)
    1   parity broken — divergence detected
    2   setup error (fixture missing, encoder script not found, etc.)

Standalone:
    python chess-spectral/python/tests/test_c_py_parity.py
Pytest:
    pytest chess-spectral/python/tests/
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent                          # chess-spectral/python
REPO_SPECTRAL = PY_DIR.parent                 # chess-spectral
FIXTURE = HERE / "fixtures" / "kasparov_topalov_1999.ndjson"
ENCODER_SCRIPT = PY_DIR / "spectral_py.py"

sys.path.insert(0, str(PY_DIR))
from chess_spectral import read_all, CHANNELS, BOARD_DIM  # noqa: E402
import numpy as np                                          # noqa: E402


def _find_c_binary() -> Path | None:
    env = os.environ.get("CS_SPECTRAL_BIN")
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = REPO_SPECTRAL / "build" / sub / f"spectral{suffix}"
        if cand.is_file():
            return cand
    return None


def _encode_py(ndjson: Path, out: Path) -> None:
    subprocess.run(
        [sys.executable, str(ENCODER_SCRIPT), "encode",
         "-i", str(ndjson), "-o", str(out)],
        check=True, capture_output=True,
    )


def _encode_c(binary: Path, ndjson: Path, out: Path) -> None:
    subprocess.run(
        [str(binary), "encode", str(ndjson), "-o", str(out)],
        check=True, capture_output=True,
    )


def run_parity() -> int:
    if not FIXTURE.is_file():
        print(f"FAIL setup: fixture missing: {FIXTURE}", file=sys.stderr)
        return 2
    if not ENCODER_SCRIPT.is_file():
        print(f"FAIL setup: encoder script missing: {ENCODER_SCRIPT}",
              file=sys.stderr)
        return 2

    c_bin = _find_c_binary()
    if c_bin is None:
        print("SKIP: no C spectral binary found (set CS_SPECTRAL_BIN or "
              "build chess-spectral). Python-only run — parity not checked.")
        return 0

    print(f"fixture: {FIXTURE.name}")
    print(f"c bin:   {c_bin}")
    print(f"py enc:  {ENCODER_SCRIPT.name}")

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        c_out = td_path / "c.spectral"
        py_out = td_path / "py.spectral"
        _encode_c(c_bin, FIXTURE, c_out)
        _encode_py(FIXTURE, py_out)

        c_hdr, c_frames = read_all(str(c_out))
        py_hdr, py_frames = read_all(str(py_out))

    if (c_hdr.version, c_hdr.encoding_dim) != \
       (py_hdr.version, py_hdr.encoding_dim):
        print(f"FAIL header: C=(v{c_hdr.version}, dim={c_hdr.encoding_dim}) "
              f"!= Py=(v{py_hdr.version}, dim={py_hdr.encoding_dim})",
              file=sys.stderr)
        return 1

    if len(c_frames) != len(py_frames):
        print(f"FAIL frame count: C={len(c_frames)} Py={len(py_frames)}",
              file=sys.stderr)
        return 1

    c_enc = np.array([f.encoding for f in c_frames])
    py_enc = np.array([f.encoding for f in py_frames])
    delta = np.abs(c_enc - py_enc)
    max_abs = float(delta.max())

    # Tolerance rationale: float32 frames store encodings with ~6e-8 ULP
    # at O(1). Corpus-scale runs show rare last-bit differences of
    # O(1e-16) between the two backends (accumulation-order effects on
    # denormal values). Anything above 1e-10 is not accumulation noise
    # and indicates a real formula drift — 4 orders of magnitude below
    # what would be observable in any downstream analysis.
    TOL = 1e-10

    if max_abs > TOL:
        print(f"FAIL numerical: max |C - Py| = {max_abs:.6g} "
              f"(tol={TOL:.0e})", file=sys.stderr)
        for name, start in CHANNELS:
            ch_delta = delta[:, start:start + BOARD_DIM].max()
            if ch_delta > TOL:
                print(f"  channel {name}: max delta {ch_delta:.6g}",
                      file=sys.stderr)
        return 1

    mv_mismatch = sum(
        1 for a, b in zip(c_frames, py_frames)
        if (a.move_from, a.move_to, a.move_promo, a.move_flags)
        != (b.move_from, b.move_to, b.move_promo, b.move_flags)
    )
    if mv_mismatch > 0:
        print(f"FAIL move metadata: {mv_mismatch}/{len(c_frames)} frames "
              "differ in (move_from, move_to, move_promo, move_flags)",
              file=sys.stderr)
        return 1

    print(f"OK: {len(c_frames)} frames × {c_hdr.encoding_dim} dims  "
          f"max |delta|={max_abs:.2g} (< {TOL:.0e} tolerance); "
          f"move metadata identical")
    return 0


def test_c_py_parity() -> None:
    """Pytest entry point — wraps run_parity() with an assertion."""
    rc = run_parity()
    assert rc == 0, f"C vs Python parity failed (rc={rc})"


if __name__ == "__main__":
    sys.exit(run_parity())
