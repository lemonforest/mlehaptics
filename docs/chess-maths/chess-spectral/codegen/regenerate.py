#!/usr/bin/env python3
"""Regenerate every codegen artifact from the Python single-source-of-truth.

Run this whenever the math definition changes (channel layout, piece
values, fiber basis, eigenvector convention, etc.). It writes:

    include/cs_tables.h, include/cs_fiber_tables.h    (2D headers)
    src/cs_tables_data.c                              (2D data, committed)
    python/chess_spectral/_committed_tables.npz       (2D Python SSOT)
    test/test_vectors.h                               (2D fixture vectors)

    include/cs_tables_4d.h, include/cs_fiber_tables_4d.h   (4D headers)
    src/cs_tables_data_4d.c                                 (4D data, committed)
    python/chess_spectral/_committed_tables_4d.npz          (4D Python SSOT)
    test/test_vectors_4d.h                                  (4D fixture vectors)
    python/tests/fixtures/fixtures_4d.npz                   (4D parity fixtures)

The .c files are committed to git (so building the C binaries doesn't
require scipy at build time). The .npz files are also committed (so
Python uses identical values to C on every platform — no scipy/LAPACK
basis-choice skew across BLAS backends).

After running this script, commit ALL the regenerated files together —
they're a coherent snapshot, and partial commits will leave Python and
C disagreeing about the encoder.

Usage:

    cd chess-maths/chess-spectral
    python codegen/regenerate.py

Requires: numpy, scipy, and chess_spectral installed (pip install -e
python/ or PYTHONPATH=python).

Exit codes:
    0   all artifacts written
    1   one or more codegen scripts failed (stderr details)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Order matters: 2D tables.py is imported by emit_tables_4d.py for
# shared primitives, so 2D must finish writing committed npz first to
# avoid a stale Python cache from polluting 4D codegen.
SCRIPTS = [
    "emit_tables.py",
    "emit_tables_4d.py",
    "emit_test_vectors.py",
    "emit_test_vectors_4d.py",
]


def _run(script_name: str) -> int:
    """Run a codegen script as a subprocess.

    We use subprocess instead of importing-and-running because some
    of the codegen scripts reassign sys.stdout for UTF-8 emoji output —
    that breaks in-process re-execution where the parent's stdout
    state is shared. Subprocess isolation sidesteps the issue."""
    path = HERE / script_name
    if not path.is_file():
        print(f"regenerate: {script_name} not found in {HERE}",
              file=sys.stderr)
        return 1
    print(f"\n=== {script_name} ===")
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(HERE.parent),
            capture_output=False,
        )
        return proc.returncode
    except Exception as e:
        print(f"regenerate: {script_name} raised {type(e).__name__}: {e}",
              file=sys.stderr)
        return 1


def main() -> int:
    overall = 0
    for s in SCRIPTS:
        rc = _run(s)
        if rc != 0:
            print(f"\nFAIL: {s} returned {rc}", file=sys.stderr)
            overall = rc
    if overall == 0:
        print("\nregenerate: ALL OK — commit the regenerated files.")
    return overall


if __name__ == "__main__":
    sys.exit(main())
