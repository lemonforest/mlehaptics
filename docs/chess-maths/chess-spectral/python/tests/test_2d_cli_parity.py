"""C ↔ Python parity test for the 2D CLI commands wired in v1.2.4.

Covers compare / query / analyze / heatmap / export / play. For each
command, both implementations run on the same input and produce
byte-identical text output (for compare/analyze/query/export) or
structurally-identical output (for heatmap/play, where ANSI bytes are
compared byte-for-byte).

Skip behavior: if the `spectral` C binary is not built, every test
SKIPS. Set CS_SPECTRAL_BIN to override.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
REPO_SPECTRAL = PY_DIR.parent


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


C_BINARY = _find_c_binary()
_REQUIRES_C = pytest.mark.skipif(
    C_BINARY is None,
    reason=("spectral C binary not found "
            "(set CS_SPECTRAL_BIN or build "
            "chess-spectral/build/Release/spectral)"),
)


# Fixtures for the e2e tests: produce a small .spectral file from a
# canned NDJSON sequence and reuse it across all parity tests via a
# session-scoped fixture.
@pytest.fixture(scope="module")
def sample_spectral(tmp_path_factory):
    """Build a 3-ply .spectral fixture using the C encoder."""
    if C_BINARY is None:
        pytest.skip("C binary unavailable; cannot build fixture")
    tmp = tmp_path_factory.mktemp("2d_cli_fixture")
    nd = tmp / "sample.ndjson"
    nd.write_text(
        '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","ply":0}\n'
        '{"fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",'
        '"ply":1,"move_from":12,"move_to":28}\n'
        '{"fen":"rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",'
        '"ply":2,"move_from":52,"move_to":36}\n',
        encoding="utf-8",
    )
    sp = tmp / "test.spectral"
    subprocess.run([str(C_BINARY), "encode", str(nd), "-o", str(sp)],
                   check=True, capture_output=True)
    return sp


def _run_c(args, capture=True):
    return subprocess.run([str(C_BINARY)] + list(args),
                          check=True, capture_output=capture, text=True,
                          encoding="utf-8")


def _run_py(args):
    """Run the Python CLI in-process for speed and to share the
    interpreter env. Returns the captured stdout as text."""
    from chess_spectral.cli import build_parser
    import io, contextlib

    ap = build_parser()
    ns = ap.parse_args(args)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ns.func(ns)
    assert rc == 0, f"Python {args[0]} returned {rc}"
    return buf.getvalue()


# ─── compare ─────────────────────────────────────────────────────────


@_REQUIRES_C
def test_compare_self_self(sample_spectral):
    """Comparing a file with itself yields cos_min/mean/max = 1.0000."""
    c_out = _run_c(["compare", str(sample_spectral), str(sample_spectral)]).stdout
    py_out = _run_py(["compare", str(sample_spectral), str(sample_spectral)])
    assert c_out == py_out, f"C:\n{c_out!r}\nPy:\n{py_out!r}"
    assert "cos_min=1.0000" in c_out


# ─── query ───────────────────────────────────────────────────────────


@_REQUIRES_C
@pytest.mark.parametrize("ply", [0, 1, 2])
def test_query_byte_identical(sample_spectral, ply):
    c_out = _run_c(["query", str(sample_spectral), "--ply", str(ply)]).stdout
    py_out = _run_py(["query", str(sample_spectral), "--ply", str(ply)])
    assert c_out == py_out, (
        f"query ply={ply} differs:\nC:\n{c_out}\nPy:\n{py_out}"
    )


# ─── analyze ─────────────────────────────────────────────────────────


@_REQUIRES_C
def test_analyze_byte_identical(sample_spectral):
    c_out = _run_c(["analyze", str(sample_spectral)]).stdout
    py_out = _run_py(["analyze", str(sample_spectral)])
    assert c_out == py_out, (
        f"analyze differs:\nC:\n{c_out}\nPy:\n{py_out}"
    )


# ─── heatmap ─────────────────────────────────────────────────────────


@_REQUIRES_C
@pytest.mark.parametrize("channel", ["A1", "A2", "B1", "E", "F2", "FA"])
def test_heatmap_byte_identical(sample_spectral, channel):
    """Heatmap output (header + glyph grid + ANSI escape codes) must
    match byte-for-byte. The ANSI color choices are also documented to
    match: cyan(36) for +, red(31) for -, intensity glyph from
    ' .,:-=+*#@'."""
    c_out = _run_c(["heatmap", str(sample_spectral), "--ply", "1",
                    "--channel", channel]).stdout
    py_out = _run_py(["heatmap", str(sample_spectral), "--ply", "1",
                      "--channel", channel])
    assert c_out == py_out, (
        f"heatmap channel={channel} differs:\nC:\n{c_out}\nPy:\n{py_out}"
    )


# ─── export ──────────────────────────────────────────────────────────


@_REQUIRES_C
def test_export_byte_identical(sample_spectral, tmp_path):
    """JSON export must match C and Python byte-for-byte. The %.6f and
    %.6g formatters in both code paths produce identical bytes for the
    same input on any standards-conforming libc/CPython combo."""
    c_json  = tmp_path / "c.json"
    py_json = tmp_path / "py.json"
    _run_c(["export", str(sample_spectral), "-o", str(c_json)])
    # Python: capture stdout to file
    py_out = _run_py(["export", str(sample_spectral), "-o", str(py_json)])
    assert c_json.read_bytes() == py_json.read_bytes(), (
        "export JSON bytes differ between C and Python"
    )


# ─── play (smoke only — non-interactive listing) ─────────────────────


@_REQUIRES_C
def test_play_list_mode_runs(sample_spectral):
    """play in list mode prints one row per ply; smoke-test that it
    succeeds and emits the expected number of rows."""
    out = _run_c(["play", str(sample_spectral)]).stdout
    rows = [r for r in out.split("\n") if r.strip()]
    # 1 header + 3 plies
    assert len(rows) == 4, f"expected 4 rows, got {len(rows)}: {rows!r}"


# ─── safety_field default-path coverage ──────────────────────────────


def test_safety_field_default_path_returns_expected_keys():
    """Smoke test: the §9o safety field still computes its scalars
    from a small fixture. The function is preserved for §9o
    reproducibility per the chess_spectral_research_notebook null
    result; the previous ``include_pawns`` extension hook was removed
    in this release because the parent hypothesis (ΔS tracks
    engine-Δeval) didn't validate."""
    from chess_spectral.safety_field import compute_safety_field
    pos = {0: 'K', 7: 'k', 8: 'Q'}
    res = compute_safety_field(pos)
    expected_keys = {
        "per_piece", "S_white", "S_black", "S_total",
        "hanging", "most_exposed",
    }
    assert expected_keys.issubset(set(res.keys()))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
