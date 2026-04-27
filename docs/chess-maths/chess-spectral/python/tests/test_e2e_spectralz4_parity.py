"""C ↔ Python end-to-end parity test for `.spectralz4` bulk generation.

Verifies:
  1. `spectral_4d encode` (C, NDJSON4 → .spectralz4) produces byte-identical
     output to `python -m chess_spectral_4d.cli encode-moves4` for the
     same input — both plain and gzip-decompressed forms.
  2. `spectral_4d csv` (C only at v1.2.4) produces identical CSV bytes
     when re-run on the same .spectralz4 — i.e. the read path is
     deterministic.

This is the closing parity test for Phase B (inventory item #23 from
the audit plan). Combined with test_fen4_parity.py (which covers the
single-frame / encode-fen4 path), the C and Python encoders are now
gated end-to-end at byte-for-byte equivalence for both 1-frame and
N-frame .spectralz4 files.

Skip behavior: if `spectral_4d` is not built, every test SKIPS rather
than fails. Set `CS_SPECTRAL_4D_BIN` to override the binary path.
"""
from __future__ import annotations

import gzip
import os
import subprocess
from pathlib import Path

import pytest

from chess_spectral_4d.cli import cmd_encode_moves4

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
REPO_SPECTRAL = PY_DIR.parent


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


C_BINARY = _find_c_binary()
_REQUIRES_C = pytest.mark.skipif(
    C_BINARY is None,
    reason=("spectral_4d C binary not found "
            "(set CS_SPECTRAL_4D_BIN or build "
            "chess-spectral/build/Release/spectral_4d)"),
)


# Curated NDJSON4 fixtures: each is a list of JSON-line strings written
# verbatim into a tempfile per test.
NDJSON4_FIXTURES = [
    pytest.param(
        [
            '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0; k@7,7,7,7"}',
        ],
        id="single-ply",
    ),
    pytest.param(
        [
            '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0; k@7,7,7,7"}',
            '{"ply": 1, "fen4": "4d-fen v1: K@1,0,0,0; k@7,7,7,7", '
            '"move_from": [0,0,0,0], "move_to": [1,0,0,0]}',
            '{"ply": 2, "fen4": "4d-fen v1: K@1,0,0,0; k@6,7,7,7", '
            '"move_from": [7,7,7,7], "move_to": [6,7,7,7]}',
        ],
        id="three-ply-with-moves",
    ),
    pytest.param(
        [
            # Mixed pawns + non-pawns + every move-metadata field.
            '{"ply": 0, "fen4": "4d-fen v1: '
            'K@4,0,0,0; k@4,7,7,7; '
            'Pw@0,1,0,0; Py@0,0,1,0; pw@7,6,7,7; py@7,7,6,7; '
            'N@2,2,2,2; b@5,5,5,5; R@3,4,5,6; q@6,5,4,3"}',
            '{"ply": 1, "fen4": "4d-fen v1: '
            'K@4,0,0,0; k@4,7,7,7; '
            'Pw@0,3,0,0; Py@0,0,1,0; pw@7,6,7,7; py@7,7,6,7; '
            'N@2,2,2,2; b@5,5,5,5; R@3,4,5,6; q@6,5,4,3", '
            '"move_from": [0,1,0,0], "move_to": [0,3,0,0], '
            '"promo": 0, "flags": 1}',
        ],
        id="mixed-pieces-with-flags",
    ),
    pytest.param(
        [
            # Producer header line — must be skipped by both encoders.
            '{"bridge_version": "4d-1.0", "produced_at": "2026-04-25"}',
            '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0"}',
            '{"ply": 1, "fen4": "4d-fen v1: K@0,0,0,1", '
            '"move_from": [0,0,0,0], "move_to": [0,0,0,1]}',
        ],
        id="with-bridge-header",
    ),
    pytest.param(
        [
            # Empty board — should produce one all-zero frame.
            '{"ply": 0, "fen4": "4d-fen v1:"}',
        ],
        id="empty-board-frame",
    ),
]


def _write_ndjson4(lines: list[str], path: Path) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_c_encode(input_path: Path, output: Path,
                  compress: bool = False) -> None:
    cmd = [str(C_BINARY), "encode", "-i", str(input_path),
           "-o", str(output)]
    if compress:
        cmd.append("-z")
    subprocess.run(cmd, check=True, capture_output=True)


def _run_python_encode(input_path: Path, output: Path,
                       compress: bool = False) -> None:
    class _Args:
        pass
    args = _Args()
    args.moves = str(input_path)
    args.output = str(output)
    args.compress = compress
    args.start = 0
    args.count = 0
    rc = cmd_encode_moves4(args)
    assert rc == 0, f"Python encode-moves4 returned {rc}"


# ─── plain (.spectral4) parity ────────────────────────────────────────


@_REQUIRES_C
@pytest.mark.parametrize("lines", NDJSON4_FIXTURES)
def test_c_python_parity_plain(lines, tmp_path):
    """For each NDJSON4 fixture, plain (uncompressed) .spectral4 bytes
    written by C and Python must be byte-identical."""
    src = tmp_path / "input.ndjson4"
    _write_ndjson4(lines, src)
    c_out  = tmp_path / "c.spectral4"
    py_out = tmp_path / "py.spectral4"
    _run_c_encode(src, c_out)
    _run_python_encode(src, py_out)
    c_bytes  = c_out.read_bytes()
    py_bytes = py_out.read_bytes()
    assert len(c_bytes) == len(py_bytes), (
        f"size mismatch: c={len(c_bytes)} py={len(py_bytes)}"
    )
    assert c_bytes == py_bytes, (
        f"first diff at offset "
        f"{next(i for i,(a,b) in enumerate(zip(c_bytes,py_bytes)) if a!=b)}"
    )


# ─── gzipped (.spectralz4) parity ─────────────────────────────────────


@_REQUIRES_C
@pytest.mark.parametrize("lines", NDJSON4_FIXTURES)
def test_c_python_parity_gzipped(lines, tmp_path):
    """For each NDJSON4 fixture, the gzip-decompressed payload from C
    and Python must be byte-identical. The gzip wrapper bytes are not
    compared (miniz vs Python gzip differ in OS / XFL / level fields,
    which is normal and outside the parity contract)."""
    src = tmp_path / "input.ndjson4"
    _write_ndjson4(lines, src)
    c_out  = tmp_path / "c.spectralz4"
    py_out = tmp_path / "py.spectralz4"
    _run_c_encode(src, c_out, compress=True)
    _run_python_encode(src, py_out, compress=True)
    c_decompressed  = gzip.open(c_out,  "rb").read()
    py_decompressed = gzip.open(py_out, "rb").read()
    assert c_decompressed == py_decompressed, (
        f"decompressed bytes mismatch: c={len(c_decompressed)} bytes, "
        f"py={len(py_decompressed)} bytes"
    )


# ─── csv determinism ─────────────────────────────────────────────────


@_REQUIRES_C
@pytest.mark.parametrize("lines", NDJSON4_FIXTURES)
def test_c_csv_deterministic(lines, tmp_path):
    """`spectral_4d csv` must be deterministic: re-running on the same
    input produces byte-identical CSV. Also smoke-checks that the CSV
    header line appears, has the expected column count, and that every
    data row has the same column count as the header."""
    src = tmp_path / "input.ndjson4"
    _write_ndjson4(lines, src)
    sp = tmp_path / "out.spectralz4"
    _run_c_encode(src, sp, compress=True)

    csv1 = tmp_path / "out1.csv"
    csv2 = tmp_path / "out2.csv"
    subprocess.run([str(C_BINARY), "csv", str(sp), "-o", str(csv1)],
                   check=True, capture_output=True)
    subprocess.run([str(C_BINARY), "csv", str(sp), "-o", str(csv2)],
                   check=True, capture_output=True)
    assert csv1.read_bytes() == csv2.read_bytes(), "csv output non-deterministic"

    rows = csv1.read_text(encoding="utf-8").strip().split("\n")
    header_cols = rows[0].count(",") + 1
    # Header has: ply + 4 from + 4 to + dist/cos/dA1 + 11 channels + total = 24 cols
    assert header_cols == 24, (
        f"unexpected csv header column count: {header_cols}"
    )
    for i, row in enumerate(rows[1:], start=1):
        assert row.count(",") + 1 == header_cols, (
            f"row {i} column count mismatch: {row.count(',')+1} vs {header_cols}"
        )


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
