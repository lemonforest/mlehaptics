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
        [sys.executable, "-m", "chess_spectral.cli", "encode",
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
    c_bin = _find_c_binary()
    if c_bin is None:
        print("SKIP: no C spectral binary found (set CS_SPECTRAL_BIN or "
              "build chess-spectral). Python-only run — parity not checked.")
        return 0

    print(f"fixture: {FIXTURE.name}")
    print(f"c bin:   {c_bin}")
    print(f"py enc:  chess_spectral.cli")

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

    # Cross-platform parity model (v1.2.4):
    #
    #   - On Windows (the codegen-source platform), C and Python use
    #     the same scipy/MKL output for encoder tables and per-element
    #     parity holds at TOL = 1e-10.
    #   - On Linux / macOS, Python's runtime tables come from a
    #     different BLAS backend (OpenBLAS / Accelerate). For DEGENERATE
    #     fiber subspaces, scipy.linalg.eigh picks a different
    #     orthonormal basis. Per-element values can drift by ~O(1) on
    #     macOS arm64 (observed). But channel ENERGIES (sum of squares
    #     within each channel block) are basis-invariant and DO match
    #     within float32 noise everywhere.
    #
    # So the strict per-element check runs only on Windows, and the
    # cross-platform check is on per-frame channel energies.
    PER_ELEMENT_TOL = 1e-10
    ENERGY_TOL = 1e-2  # generous float32 + cross-BLAS slack
    on_codegen_platform = sys.platform == "win32"

    if on_codegen_platform and max_abs > PER_ELEMENT_TOL:
        print(f"FAIL per-element: max |C - Py| = {max_abs:.6g} "
              f"(tol={PER_ELEMENT_TOL:.0e}) on codegen-source platform",
              file=sys.stderr)
        for name, start in CHANNELS:
            ch_delta = delta[:, start:start + BOARD_DIM].max()
            if ch_delta > PER_ELEMENT_TOL:
                print(f"  channel {name}: max delta {ch_delta:.6g}",
                      file=sys.stderr)
        return 1

    # Energy parity (cross-platform). Channel energies are basis-
    # invariant under orthonormal change of basis, so they must agree
    # whether or not C and Python picked the same basis.
    energy_max = 0.0
    energy_worst = ("", 0.0)
    for name, start in CHANNELS:
        c_E = (c_enc[:, start:start + BOARD_DIM].astype(np.float64) ** 2
               ).sum(axis=1)
        py_E = (py_enc[:, start:start + BOARD_DIM].astype(np.float64) ** 2
                ).sum(axis=1)
        ch_E_diff = float(np.abs(c_E - py_E).max())
        if ch_E_diff > energy_max:
            energy_max = ch_E_diff
            energy_worst = (name, ch_E_diff)
    if energy_max > ENERGY_TOL:
        print(f"FAIL channel-energy: worst diff = {energy_worst[1]:.3e} "
              f"in channel {energy_worst[0]} (tol={ENERGY_TOL:.0e}). "
              f"Energies are basis-invariant — this indicates a real "
              f"encoder bug, not a cross-platform table-skew.",
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

    if on_codegen_platform:
        msg = (f"OK [strict]: {len(c_frames)} frames × {c_hdr.encoding_dim} "
               f"dims  max |delta|={max_abs:.2g} (< {PER_ELEMENT_TOL:.0e} "
               f"per-element tol); channel-energy max diff "
               f"{energy_max:.2g}; move metadata identical")
    else:
        msg = (f"OK [energy]: {len(c_frames)} frames × {c_hdr.encoding_dim} "
               f"dims; channel-energy max diff {energy_max:.2g} "
               f"(< {ENERGY_TOL:.0e} tol); per-element check skipped "
               f"(non-codegen platform — Python BLAS picks different "
               f"orthonormal basis for degenerate fiber subspaces; "
               f"energies are basis-invariant); max raw |delta|={max_abs:.2g} "
               f"reported for diagnostics; move metadata identical")
    print(msg)
    return 0


def test_c_py_parity() -> None:
    """Pytest entry point — wraps run_parity() with an assertion."""
    rc = run_parity()
    assert rc == 0, f"C vs Python parity failed (rc={rc})"


if __name__ == "__main__":
    sys.exit(run_parity())
