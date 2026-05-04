"""C ↔ Python parity test for ephemerides-spectral.

Builds and runs the C smoke test, parses its PARITY_PAYLOAD line,
encodes the same JD with the Python reference, and asserts byte-for-
byte agreement on the per-body uint32 phase residues.

Run from the c/ directory or anywhere else; paths are absolute.

    python test/test_parity_python.py

Exit code 0 = parity holds; 1 = divergence (with diff dump).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_C_ROOT = _HERE.parent
_PROJECT_ROOT = _C_ROOT.parents[1]      # docs/antikythera-maths
_REPO_ROOT = _PROJECT_ROOT.parents[1]     # repo root

# Make the Python research modules importable.
sys.path.insert(0, str(_PROJECT_ROOT))


def _build_c_test() -> Path:
    """Compile the C smoke test if needed; return the binary path."""
    out = _C_ROOT / "build" / ("test_es_encode.exe" if os.name == "nt" else "test_es_encode")
    out.parent.mkdir(parents=True, exist_ok=True)

    cc = os.environ.get("CC", "gcc")
    # Try -std=c17 first (newer toolchains); fall back to -std=c11
    # for older ones (the source is C11-compatible).
    sources = [str(p) for p in (_C_ROOT / "src").glob("*.c")]
    sources.append(str(_C_ROOT / "test" / "test_es_encode.c"))
    include = str(_C_ROOT / "include")

    for std in ("c17", "c11"):
        cmd = [cc, f"-std={std}", "-Wall", "-Wextra", "-Wpedantic", "-O2",
               "-I", include, *sources, "-lm", "-o", str(out)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return out
        if "unrecognized command line option '-std=c17'" not in proc.stderr:
            print(proc.stdout, file=sys.stderr)
            print(proc.stderr, file=sys.stderr)
            raise SystemExit(f"C build failed under -std={std}: {proc.returncode}")
    raise SystemExit("Neither -std=c17 nor -std=c11 worked")


def _run_c(binary: Path) -> dict:
    """Run the C binary, parse the PARITY_PAYLOAD line."""
    proc = subprocess.run([str(binary)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"C binary failed: {proc.returncode}")
    m = re.search(r"PARITY_PAYLOAD:\s*(\{.*\})", proc.stdout)
    if not m:
        raise SystemExit(
            f"PARITY_PAYLOAD line missing from C output:\n{proc.stdout}"
        )
    return json.loads(m.group(1))


def _python_phases(delta_t_days: float) -> list[int]:
    """Encode the same JD with the Python reference."""
    from research.bip_instrument import EphemerisBIPInstrument, REFERENCE_JD

    inst = EphemerisBIPInstrument(D=2**16, kernel="de421")
    phases = inst.encode_state(REFERENCE_JD + delta_t_days)
    return [int(p) for p in phases.tolist()]


def main() -> int:
    binary = _build_c_test()
    c_payload = _run_c(binary)
    delta_t = float(c_payload["delta_t_days"])
    c_phases = list(map(int, c_payload["phases_uint32"]))

    py_phases = _python_phases(delta_t)

    if c_phases == py_phases:
        print(f"PARITY OK: 26 bodies match byte-for-byte at delta_t = {delta_t} d")
        return 0

    print("PARITY MISMATCH:")
    print(f"  delta_t = {delta_t} days")
    n_mismatches = 0
    for i, (c, py) in enumerate(zip(c_phases, py_phases)):
        if c != py:
            n_mismatches += 1
            print(f"  body[{i}]: C={c} != Python={py} (diff={c - py})")
    print(f"\n{n_mismatches} / {len(c_phases)} bodies differ")
    return 1


if __name__ == "__main__":
    sys.exit(main())
