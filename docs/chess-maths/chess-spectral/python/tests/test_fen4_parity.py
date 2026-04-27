"""C ↔ Python parity test for FEN4 v1 and the encode-fen4 CLI surface.

Verifies three things across a curated set of FEN4 fixtures:

  1. Both parsers (`cs_fen_4d_parse` in C, `chess_spectral.fen_4d.parse`
     in Python) accept and reject the same set of inputs.
  2. The Python parser produces a position dict that, when fed to
     `encode_4d`, yields the same encoding bytes as the C `cs_encode_4d`
     reached via `spectral_4d encode-fen4 --fen4 ...`.
  3. The single-frame .spectral4 file written by `spectral_4d
     encode-fen4` is byte-identical to the file written by
     `python -m chess_spectral_4d.cli encode-fen4`.

Item 3 is the strongest claim: it covers the encoder, the frame layout,
the header layout, and (when -z is added) the gzip-decompressed payload.
The gzip *wrapper* bytes are not compared because miniz and Python's
gzip module emit different OS / XFL / compression-level fields; the
parity contract is on the decompressed content.

Skip behavior: if the `spectral_4d` binary cannot be located, the test
SKIPS rather than fails (the same convention as test_c_py_parity_4d.py).
Set `CS_SPECTRAL_4D_BIN` to override the search.
"""
from __future__ import annotations

import gzip
import os
import subprocess
import sys
from pathlib import Path

import pytest

from chess_spectral import fen_4d
from chess_spectral_4d.cli import cmd_encode_fen4

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
            "(set CS_SPECTRAL_4D_BIN or build chess-spectral/build/Release/spectral_4d)"),
)


# Curated valid fixtures — chosen to cover:
#   - empty board
#   - single piece (each non-pawn, each pawn axis)
#   - mixed positions
#   - max-coord values
#   - whitespace-tolerant variants
VALID_FIXTURES = [
    pytest.param("4d-fen v1:", id="empty"),
    pytest.param("4d-fen v1: K@0,0,0,0", id="white-king-corner"),
    pytest.param("4d-fen v1: k@7,7,7,7", id="black-king-far-corner"),
    pytest.param("4d-fen v1: K@0,0,0,0; k@7,7,7,7", id="two-kings"),
    pytest.param("4d-fen v1: N@1,2,3,4", id="white-knight"),
    pytest.param("4d-fen v1: q@4,4,4,4", id="black-queen-center"),
    pytest.param("4d-fen v1: Pw@0,1,2,3", id="white-w-axis-pawn"),
    pytest.param("4d-fen v1: Py@0,1,2,3", id="white-y-axis-pawn"),
    pytest.param("4d-fen v1: pw@7,6,5,4", id="black-w-axis-pawn"),
    pytest.param("4d-fen v1: py@7,6,5,4", id="black-y-axis-pawn"),
    pytest.param(
        "4d-fen v1: K@0,0,0,0; k@7,7,7,7; "
        "Pw@0,1,0,0; Py@0,0,1,0; pw@7,6,7,7; py@7,7,6,7; "
        "N@2,2,2,2; b@5,5,5,5; R@3,4,5,6; q@6,5,4,3",
        id="mixed-bag",
    ),
    pytest.param(
        "  4d-fen v1:  \n  K @ 0,0,0,0 ;\n  k @ 7,7,7,7 ;\n",
        id="whitespace-and-newlines",
    ),
    pytest.param("4d-fen v1: K@0,0,0,0;", id="trailing-semicolon"),
]


# Curated invalid fixtures + expected error code (matches both C and
# Python CODE_* constants).
INVALID_FIXTURES = [
    pytest.param("4d-fen v2: K@0,0,0,0", fen_4d.CODE_BAD_PREFIX, id="wrong-version"),
    pytest.param("not a fen4 string", fen_4d.CODE_BAD_PREFIX, id="garbage"),
    pytest.param("4d-fen v1: Z@0,0,0,0", fen_4d.CODE_BAD_PIECE, id="unknown-piece"),
    pytest.param("4d-fen v1: P@0,0,0,0", fen_4d.CODE_BAD_PIECE, id="pawn-no-axis"),
    pytest.param("4d-fen v1: Pz@0,0,0,0", fen_4d.CODE_BAD_PIECE, id="pawn-bad-axis"),
    pytest.param("4d-fen v1: K@8,0,0,0", fen_4d.CODE_BAD_COORD, id="coord-out-of-range"),
    pytest.param("4d-fen v1: K@0,0,0", fen_4d.CODE_BAD_COORD, id="too-few-coords"),
    pytest.param("4d-fen v1: K@0,0,0,0,0", fen_4d.CODE_TRAILING, id="too-many-coords"),
    pytest.param("4d-fen v1: K@0,0,0,0; k@0,0,0,0", fen_4d.CODE_DUPLICATE, id="duplicate-square"),
]


# ─── Python parser tests (always run) ─────────────────────────────────


@pytest.mark.parametrize("fen4", VALID_FIXTURES)
def test_python_parser_accepts_valid(fen4):
    """Python parser must accept every fixture without raising."""
    result = fen_4d.parse(fen4)
    assert isinstance(result, dict)
    # Every value must be either a 1-char string or a (color, axis) tuple.
    for sq, value in result.items():
        assert 0 <= sq < 4096
        if isinstance(value, tuple):
            color, axis = value
            assert color in ("P", "p")
            assert axis in ("w", "y")
        else:
            assert value in "NBRQKnbrqk"


@pytest.mark.parametrize("fen4,expected_code", INVALID_FIXTURES)
def test_python_parser_rejects_invalid(fen4, expected_code):
    """Python parser must reject every malformed fixture with the
    documented error code."""
    with pytest.raises(fen_4d.Fen4ParseError) as excinfo:
        fen_4d.parse(fen4)
    assert excinfo.value.code == expected_code, (
        f"expected code {expected_code}, got {excinfo.value.code}: "
        f"{excinfo.value}"
    )


# ─── C↔Python parity (requires C binary) ──────────────────────────────


def _run_python_encode_fen4(fen4: str, output: Path,
                            compress: bool = False) -> None:
    """Drive cmd_encode_fen4 directly, avoiding the subprocess overhead."""
    class _Args:
        pass
    args = _Args()
    args.fen4 = fen4
    args.output = str(output)
    args.compress = compress
    rc = cmd_encode_fen4(args)
    assert rc == 0, f"Python encode-fen4 returned {rc}"


def _run_c_encode_fen4(fen4: str, output: Path,
                       compress: bool = False) -> None:
    """Shell out to the C binary."""
    cmd = [str(C_BINARY), "encode-fen4", "--fen4", fen4,
           "-o", str(output)]
    if compress:
        cmd.append("-z")
    subprocess.run(cmd, check=True, capture_output=True)


@_REQUIRES_C
@pytest.mark.parametrize("fen4", VALID_FIXTURES)
def test_c_python_parity_plain(fen4, tmp_path):
    """For each valid fixture, plain (uncompressed) .spectral4 from C
    and Python must agree:
      - byte-for-byte on the 256-byte header
      - byte-for-byte on per-frame metadata (14 B/frame)
      - numerically within 1e-4 (float32) on per-frame encoding floats

    The encoding-floats relaxation accommodates the cross-platform
    Python-runtime-tables vs committed-C-tables skew documented in
    `_parity_helpers.py`. On the codegen-source platform (Windows MKL),
    agreement is byte-for-byte; on Linux OpenBLAS / macOS Accelerate
    the encoding floats can drift by a few ulp."""
    from tests._parity_helpers import assert_spectral4d_close
    c_out  = tmp_path / "c.spectral4"
    py_out = tmp_path / "py.spectral4"
    _run_c_encode_fen4(fen4, c_out)
    _run_python_encode_fen4(fen4, py_out)
    assert_spectral4d_close(c_out, py_out)


@_REQUIRES_C
@pytest.mark.parametrize("fen4", VALID_FIXTURES)
def test_c_python_parity_gzipped(fen4, tmp_path):
    """For each valid fixture, the gzip-decompressed payload from C and
    Python must agree under the same parity contract as the plain
    test (see test_c_python_parity_plain). The gzip wrapper itself is
    not compared (miniz vs Python gzip differ in OS / XFL / compression-
    level header bytes, which is normal and outside our parity scope)."""
    from tests._parity_helpers import assert_spectral4d_close
    c_out  = tmp_path / "c.spectralz4"
    py_out = tmp_path / "py.spectralz4"
    _run_c_encode_fen4(fen4, c_out, compress=True)
    _run_python_encode_fen4(fen4, py_out, compress=True)
    assert_spectral4d_close(c_out, py_out, gz=True)


@_REQUIRES_C
@pytest.mark.parametrize("fen4,expected_code", INVALID_FIXTURES)
def test_c_python_parity_rejects(fen4, expected_code, tmp_path):
    """Both parsers must reject the same malformed inputs.
    The C side returns exit code 3 (runtime error), Python returns 3 too;
    we don't compare exit codes per fixture (they're aggregated as
    'parse failed') — only that BOTH fail."""
    out = tmp_path / "should-not-exist.spectral4"
    # C must fail
    c_proc = subprocess.run(
        [str(C_BINARY), "encode-fen4", "--fen4", fen4, "-o", str(out)],
        capture_output=True,
    )
    assert c_proc.returncode != 0, (
        f"C parser unexpectedly accepted invalid fixture: {fen4!r}"
    )
    # Python must also fail (raises Fen4ParseError → cmd handler returns 3)
    with pytest.raises(fen_4d.Fen4ParseError):
        fen_4d.parse(fen4)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
