"""C-binary vs Python reference parity test — 4D encoder.

Mirrors test_c_py_parity.py for the 4D encoder port. Loads the
codegen'd fixture pack (fixtures_4d.npz), encodes each position through
spectral_4d, and compares against the Python reference at 1e-10 absolute
tolerance.

v1.1.1 scope: all 11 channels (A1, STD4_{X,Y,Z,W}, FIB_SYM_{1,2,3},
FA_PAWN_W, FA_PAWN_Y, FD_DIAG) are gated at 1e-10. The v1.0 single
FA_PAWN channel was split into per-axis FA_PAWN_W / FA_PAWN_Y by the
pawn-axis routing added in P6; both must agree byte-for-byte with
their Python counterparts across the legacy W-only fixtures *and* the
new Y-axis + mixed fixtures.

Exit codes:
    0   parity confirmed (or C binary absent — skipped with a warning)
    1   parity broken
    2   setup error (fixture pack missing, binary missing, etc.)

Standalone:
    python chess-spectral/python/tests/test_c_py_parity_4d.py
Pytest:
    pytest chess-spectral/python/tests/test_c_py_parity_4d.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent                          # chess-spectral/python
REPO_SPECTRAL = PY_DIR.parent                 # chess-spectral
FIXTURE_PACK = HERE / "fixtures" / "fixtures_4d.npz"
JSONL_PATH   = HERE / "fixtures" / "positions_4d.jsonl"

# Channels that have real C impls at the current milestone. Full set
# at v1.1.1/P6 — every channel is gated at TOL, including both pawn-
# axis sub-channels after the FA_PAWN split.
GATED_CHANNELS = {"A1", "STD4_X", "STD4_Y", "STD4_Z", "STD4_W",
                  "FIB_SYM_1", "FIB_SYM_2", "FIB_SYM_3",
                  "FA_PAWN_W", "FA_PAWN_Y", "FD_DIAG"}
# Channels whose C-side is still a zero stub. Empty at v1.1.1/P6.
STUBBED_CHANNELS: set[str] = set()

# Tolerance rationale: see test_c_py_parity.py. 1e-10 is ~4 orders below
# observable float32 noise; anything above is formula drift, not
# accumulation order.
TOL = 1e-10


def _find_c_binary() -> Path | None:
    env = os.environ.get("CS_SPECTRAL_4D_BIN")
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = REPO_SPECTRAL / "build" / sub / f"spectral_4d{suffix}"
        if cand.is_file():
            return cand
    return None


def _encode_c(binary: Path, name: str) -> np.ndarray:
    """Shell out to spectral_4d encode-fixture and read 45056 float32 LE."""
    result = subprocess.run(
        [str(binary), "encode-fixture",
         "--positions-jsonl", str(JSONL_PATH),
         "--name", name],
        check=True, capture_output=True,
    )
    data = result.stdout
    # v1.1.1: 11 channels × 4096 floats = 45056 floats = 180 224 bytes.
    expected_bytes = 4 * 45056
    if len(data) != expected_bytes:
        raise RuntimeError(
            f"spectral_4d encode-fixture '{name}': expected {expected_bytes} "
            f"bytes on stdout, got {len(data)}"
        )
    return np.frombuffer(data, dtype="<f4").copy()


def run_parity() -> int:
    if not FIXTURE_PACK.is_file():
        print(f"FAIL setup: fixture pack missing: {FIXTURE_PACK}",
              file=sys.stderr)
        print("       run codegen/emit_test_vectors_4d.py first",
              file=sys.stderr)
        return 2
    if not JSONL_PATH.is_file():
        print(f"FAIL setup: positions_4d.jsonl missing: {JSONL_PATH}",
              file=sys.stderr)
        return 2

    c_bin = _find_c_binary()
    if c_bin is None:
        print("SKIP: no spectral_4d binary found (set CS_SPECTRAL_4D_BIN or "
              "build chess-spectral). Python-only run — parity not checked.")
        return 0

    print(f"fixture pack: {FIXTURE_PACK.name}")
    print(f"c bin:        {c_bin}")

    pack = np.load(FIXTURE_PACK, allow_pickle=True)
    names         = pack["names"]
    encodings     = pack["encodings"]        # (N, 45056) float32
    channel_names = pack["channel_names"]    # (11,) object
    channel_starts = pack["channel_starts"]  # (12,) int32

    # Map channel name -> (start, end) slice.
    ch_slice: dict[str, tuple[int, int]] = {}
    for i, ch in enumerate(channel_names):
        ch_slice[str(ch)] = (int(channel_starts[i]), int(channel_starts[i + 1]))

    total_fail = 0
    per_fixture_status = []
    for i, name in enumerate(names):
        name = str(name)
        c_enc = _encode_c(c_bin, name)
        py_enc = encodings[i]

        delta = np.abs(c_enc - py_enc)

        # 1) Gated channels (real C impl) must agree within TOL.
        failed_gated = []
        for ch in GATED_CHANNELS:
            s, e = ch_slice[ch]
            d = float(delta[s:e].max())
            if d > TOL:
                failed_gated.append((ch, d))

        # 2) Stubbed channels (C writes zero). Python may also be zero
        #    (then delta == 0 and the equality holds) OR nonzero (then
        #    C's zero diverges; that's expected at P2b and we skip the
        #    comparison with an informational note).
        stub_present_nonzero = []
        for ch in STUBBED_CHANNELS:
            s, e = ch_slice[ch]
            c_slab = c_enc[s:e]
            py_slab = py_enc[s:e]
            if np.any(c_slab != 0.0):
                # C stub must be identically zero at P2b.
                failed_gated.append((ch, float(np.abs(c_slab).max())))
                continue
            if float(np.abs(py_slab).max()) > 0.0:
                stub_present_nonzero.append(ch)

        status = "ok"
        if failed_gated:
            status = "FAIL"
            total_fail += 1
        per_fixture_status.append((name, status, failed_gated,
                                   stub_present_nonzero))

    # Report.
    print()
    print(f"{'fixture':<28s} {'status':<6s} detail")
    print("-" * 72)
    for name, status, failed, stubs in per_fixture_status:
        detail_parts = []
        if failed:
            detail_parts.append("FAILED gated: "
                                + ", ".join(f"{c}={d:.3g}" for c, d in failed))
        if stubs:
            detail_parts.append("stub-zero vs py-nonzero (lifted in P4): "
                                + ",".join(stubs))
        detail = "; ".join(detail_parts) if detail_parts else "all gated "
        if not detail_parts:
            detail = "all gated channels within tol"
        print(f"{name:<28s} {status:<6s} {detail}")

    if total_fail > 0:
        print(f"\nFAIL: {total_fail}/{len(names)} fixtures diverged above "
              f"tol={TOL:.0e}", file=sys.stderr)
        return 1

    print(f"\nOK: {len(names)} fixtures × {len(GATED_CHANNELS)} gated "
          f"channels all within tol={TOL:.0e}")
    return 0


def test_c_py_parity_4d() -> None:
    """Pytest entry point — wraps run_parity() with an assertion."""
    rc = run_parity()
    assert rc == 0, f"C vs Python 4D parity failed (rc={rc})"


if __name__ == "__main__":
    sys.exit(run_parity())
