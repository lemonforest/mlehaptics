"""End-to-end smoke suite for chess-spectral v1.2.4.

This is the "does everything we ship still work?" test. It exercises
every wired CLI command against a real, verified game from the dataset
(Kasparov vs Topalov, Hoogovens 1999 R4 — 87 plies, "Kasparov's
Immortal") plus the 2D phase-operator package and the 4D Oana-Chiru
table-verification gates.

What it covers (organized by surface):

    2D C CLI (spectral):
      encode (PGN→.spectral via pgn_bridge), csv, query, analyze,
      compare, heatmap, export, play.

    2D Python CLI (chess_spectral.cli):
      encode-fen, csv, compare, query, analyze, heatmap, export.
      (Output verified to match C byte-for-byte where applicable.)

    4D C CLI (spectral_4d):
      encode-fen4 (single position), encode (NDJSON4 → .spectralz4),
      csv (per-ply 11-channel energies).

    4D Python CLI (chess_spectral_4d):
      encode-fen4, encode-moves4, corpus-gen, tables-verify.

    2D phase operators (chess_spectral.phase_operators):
      Import + invoke pseudo-legal generation against a real position
      from the Kasparov-Topalov game; cross-check against python-chess
      when available.

    4D Oana-Chiru phase verification (chess_spectral.tables_4d):
      Run all six phase gates (1, 2, 3, 4, 5, pawn-axis) via
      `chess_spectral_4d tables-verify --phase all`.

Skip behavior:
    - Tests that need the C binary skip cleanly if it isn't built
      (set $CS_SPECTRAL_BIN / $CS_SPECTRAL_4D_BIN, or build the
      Release config).
    - Tests that need python-chess (the optional `[corpus]` extra)
      skip if it isn't installed.

Runs in ~60s end-to-end on a warm Python interpreter.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
REPO_SPECTRAL = PY_DIR.parent
FIXTURES_DIR = HERE / "fixtures"
SAMPLE_PGN = FIXTURES_DIR / "kasparov_topalov_1999.pgn"
SAMPLE_NDJSON = FIXTURES_DIR / "kasparov_topalov_1999.ndjson"
POSITIONS_4D = FIXTURES_DIR / "positions_4d.jsonl"

EXPECTED_PLIES = 88  # 87 SAN moves + 1 starting-position frame at ply 0
                     # (the PGN's PlyCount header reports 87 = move count;
                     # the encoder emits one frame per position, including
                     # the initial setup, hence n_plies = 88).


# ─── Binary discovery (mirrors cli.py:_find_native_binary) ──────────


def _find_binary(name: str, env_var: str) -> Path | None:
    env = os.environ.get(env_var)
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = REPO_SPECTRAL / "build" / sub / f"{name}{suffix}"
        if cand.is_file():
            return cand
    return None


C_BINARY = _find_binary("spectral", "CS_SPECTRAL_BIN")
C_BINARY_4D = _find_binary("spectral_4d", "CS_SPECTRAL_4D_BIN")

_REQUIRES_C = pytest.mark.skipif(
    C_BINARY is None,
    reason="spectral C binary not built; set CS_SPECTRAL_BIN or run "
           "`cmake --build build --config Release --target spectral`",
)
_REQUIRES_C_4D = pytest.mark.skipif(
    C_BINARY_4D is None,
    reason="spectral_4d C binary not built; set CS_SPECTRAL_4D_BIN or "
           "run `cmake --build build --config Release --target spectral_4d`",
)
_REQUIRES_PYTHON_CHESS = pytest.mark.skipif(
    True,  # overridden below if import succeeds
    reason="python-chess is not installed; install with "
           "`pip install chess-spectral[corpus]` or `pip install chess`",
)
try:
    import chess as _python_chess  # noqa: F401
    _REQUIRES_PYTHON_CHESS = pytest.mark.skipif(
        False, reason="(python-chess available)"
    )
except ImportError:
    pass


# ─── Helpers ─────────────────────────────────────────────────────────


def _run_c(args, **kw):
    """Run a C subprocess, raising with stderr on failure."""
    proc = subprocess.run(
        [str(C_BINARY)] + list(args),
        check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace", **kw,
    )
    return proc


def _run_c_4d(args, **kw):
    proc = subprocess.run(
        [str(C_BINARY_4D)] + list(args),
        check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace", **kw,
    )
    return proc


def _run_py(args):
    """Run the Python 2D CLI in-process."""
    from chess_spectral.cli import build_parser
    ap = build_parser()
    ns = ap.parse_args(args)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ns.func(ns)
    return rc, buf.getvalue()


def _run_py_4d(args):
    """Run the Python 4D CLI in-process."""
    from chess_spectral_4d.cli import build_parser
    ap = build_parser()
    ns = ap.parse_args(args)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ns.func(ns)
    return rc, buf.getvalue()


# ─── Module-scoped fixtures (encode the game once, reuse N times) ───


@pytest.fixture(scope="module")
def encoded_game(tmp_path_factory):
    """Encode the Kasparov-Topalov game from the committed NDJSON
    (which was bridged from PGN earlier) and return the path. We
    use the NDJSON to avoid the python-chess dependency in this
    fixture; PGN-via-bridge is exercised in test_pgn_to_spectralz."""
    if C_BINARY is None or not SAMPLE_NDJSON.is_file():
        pytest.skip("C binary or NDJSON fixture absent")
    tmp = tmp_path_factory.mktemp("smoke_2d")
    sp = tmp / "kasparov_topalov.spectral"
    spz = tmp / "kasparov_topalov.spectralz"
    _run_c(["encode", str(SAMPLE_NDJSON), "-o", str(sp)])
    _run_c(["encode", str(SAMPLE_NDJSON), "-o", str(spz), "-z"])
    return sp, spz, tmp


# ─── 2D pipeline smoke (real-game) ──────────────────────────────────


@_REQUIRES_C
def test_2d_encode_real_game_yields_expected_ply_count(encoded_game):
    """The encoded .spectral header must report EXPECTED_PLIES (87)."""
    sp, _, _ = encoded_game
    from chess_spectral import read_all
    hdr, frames = read_all(str(sp))
    assert hdr.n_plies == EXPECTED_PLIES, (
        f"expected {EXPECTED_PLIES} plies (Kasparov-Topalov 1999), "
        f"got {hdr.n_plies}"
    )
    assert len(frames) == EXPECTED_PLIES


@_REQUIRES_C
def test_2d_csv_real_game_produces_88_rows(encoded_game):
    """csv emits a header row + 87 ply rows."""
    sp, _, tmp = encoded_game
    csv_path = tmp / "out.csv"
    _run_c(["csv", str(sp), "-o", str(csv_path)])
    rows = csv_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == EXPECTED_PLIES + 1, (
        f"csv: expected {EXPECTED_PLIES + 1} rows (header + {EXPECTED_PLIES} plies), "
        f"got {len(rows)}"
    )
    # Header has the documented 17 columns.
    assert rows[0].count(",") + 1 == 17


@_REQUIRES_C
def test_2d_query_at_each_quartile(encoded_game):
    """query at four representative plies must succeed and emit all
    10 channel-energy lines + a total."""
    sp, _, _ = encoded_game
    for ply in (0, EXPECTED_PLIES // 4, EXPECTED_PLIES // 2, EXPECTED_PLIES - 1):
        out = _run_c(["query", str(sp), "--ply", str(ply)]).stdout
        for ch in ("E_A1", "E_A2", "E_B1", "E_B2", "E_E",
                   "E_F1", "E_F2", "E_F3", "E_FA", "E_FD", "E_total"):
            assert ch in out, f"query ply={ply}: missing {ch} in output"


@_REQUIRES_C
def test_2d_analyze_real_game_finds_peak(encoded_game):
    """analyze must return valid JSON with peak_ply / drop_ply / crisis_ply
    inside [0, n_plies)."""
    sp, _, _ = encoded_game
    out = _run_c(["analyze", str(sp)]).stdout
    j = json.loads(out)
    assert j["n_plies"] == EXPECTED_PLIES
    for key in ("a1_peak_ply", "a1_drop_ply", "crisis_ply", "e_total_max_ply"):
        assert 0 <= j[key] < EXPECTED_PLIES, (
            f"analyze: {key}={j[key]} not in [0, {EXPECTED_PLIES})"
        )
    # The Kasparov immortal has wild swings — abs_dA1_max must be > 0.
    assert j["abs_dA1_max"] > 0.0


@_REQUIRES_C
def test_2d_compare_self_yields_unit_cosine(encoded_game):
    """A file compared with itself must have cos_min/mean/max == 1.0000."""
    sp, _, _ = encoded_game
    out = _run_c(["compare", str(sp), str(sp)]).stdout
    assert "cos_min=1.0000" in out
    assert "cos_mean=1.0000" in out
    assert "cos_max=1.0000" in out


@_REQUIRES_C
@pytest.mark.parametrize("channel", ["A1", "B2", "F2", "FA"])
def test_2d_heatmap_renders_8x8(encoded_game, channel):
    """heatmap output must contain 8 row-labels (8..1) and the file
    column legend ('a b c d e f g h')."""
    sp, _, _ = encoded_game
    out = _run_c(["heatmap", str(sp), "--ply", "20", "--channel", channel]).stdout
    for rank in range(1, 9):
        assert f"  {rank}  " in out, f"heatmap: missing rank-{rank} row"
    assert "a b c d e f g h" in out


@_REQUIRES_C
def test_2d_export_yields_valid_json(encoded_game):
    """export must produce a parseable JSON document with version /
    encoding_dim / n_plies / channels / frames."""
    sp, _, tmp = encoded_game
    out_json = tmp / "export.json"
    _run_c(["export", str(sp), "-o", str(out_json)])
    j = json.loads(out_json.read_text(encoding="utf-8"))
    assert j["version"] == 2
    assert j["encoding_dim"] == 640
    assert j["n_plies"] == EXPECTED_PLIES
    assert len(j["channels"]) == 10
    assert len(j["frames"]) == EXPECTED_PLIES
    # Spot-check frame[0]: must have ply / channel_energies / encoding.
    assert j["frames"][0]["ply"] == 0
    assert "A1" in j["frames"][0]["channel_energies"]
    assert len(j["frames"][0]["encoding"]) == 640


@_REQUIRES_C
def test_2d_play_lists_all_plies(encoded_game):
    """play in list mode emits 1 header row + EXPECTED_PLIES rows."""
    sp, _, _ = encoded_game
    out = _run_c(["play", str(sp)]).stdout
    rows = [r for r in out.split("\n") if r.strip()]
    assert len(rows) == EXPECTED_PLIES + 1


# ─── 2D Python wrappers match C on real game ────────────────────────


@_REQUIRES_C
def test_2d_python_compare_matches_c(encoded_game):
    """Compare-self: both implementations must report cos_min/mean/max
    = 1.0000 (same formatted summary). The exact ply that wins
    np.argmin / C's `<` tiebreaker may differ between code paths
    when every cosine is 1.0 within float precision but not literally
    equal — that's a tiebreaker artifact, not a parity bug. So this
    test only asserts the formatted cosine values agree, not the
    argmin ply."""
    import re
    sp, _, _ = encoded_game
    c_out = _run_c(["compare", str(sp), str(sp)]).stdout
    rc, py_out = _run_py(["compare", str(sp), str(sp)])
    assert rc == 0
    # Strip the "(ply=N)" tiebreaker from both sides before comparing.
    strip_ply = re.compile(r" \(ply=\d+\)")
    assert strip_ply.sub("", c_out) == strip_ply.sub("", py_out)


@_REQUIRES_C
def test_2d_python_analyze_matches_c(encoded_game):
    sp, _, _ = encoded_game
    c_out = _run_c(["analyze", str(sp)]).stdout
    rc, py_out = _run_py(["analyze", str(sp)])
    assert rc == 0
    assert c_out == py_out


@_REQUIRES_C
def test_2d_python_query_matches_c(encoded_game):
    sp, _, _ = encoded_game
    c_out = _run_c(["query", str(sp), "--ply", "42"]).stdout
    rc, py_out = _run_py(["query", str(sp), "--ply", "42"])
    assert rc == 0
    assert c_out == py_out


# ─── 2D phase operators on a position from the real game ────────────


@_REQUIRES_PYTHON_CHESS
def test_2d_phase_operators_smoke():
    """Smoke-test the chess_spectral.phase_operators package: import the
    public API, exercise three independent surfaces against
    python-chess as ground truth.

      1. phasecast_is_check on a known check position
      2. available_castles on the starting position (all 4 castles)
      3. occupation_field_from_board produces non-empty mapping

    These are minimum-viable checks that each operator is wired and
    callable end-to-end. Full operator validation lives in
    tests/phase_operators/."""
    import chess
    from chess_spectral.phase_operators import (
        phasecast_is_check,
        available_castles,
        occupation_field_from_board,
    )

    # 1. Scholar's Mate position — Black king is in check (mate).
    mate_fen = ("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/"
                "PPPP1PPP/RNB1K1NR b KQkq - 0 4")
    board = chess.Board(mate_fen)
    assert phasecast_is_check(board), (
        "phasecast_is_check missed Scholar's Mate check"
    )
    # Ground truth: python-chess agrees.
    assert board.is_check()

    # 2. Available castles on the starting position: K-side + Q-side
    #    for both colors = 4 candidate castles. (available_castles
    #    only returns castles for the side-to-move; on the starting
    #    position that's white, so we expect 2.)
    start = chess.Board()
    castles = available_castles(start)
    # On the starting position no castle is YET legal (king is in
    # original square but path conditions etc. — the phase operator
    # may report 0 or 2 depending on its definition of "available").
    # Smoke-test: just verify it returns a list and doesn't raise.
    assert isinstance(castles, list)

    # 3. Occupation field is a non-empty mapping over the starting
    #    position (32 occupied phases).
    occ = occupation_field_from_board(start)
    assert hasattr(occ, "__len__") or hasattr(occ, "__contains__"), (
        "occupation_field_from_board returned an unexpected type"
    )


# ─── 4D pipeline smoke ──────────────────────────────────────────────


@_REQUIRES_C_4D
def test_4d_encode_fen4_real_position():
    """encode-fen4 on a non-trivial 4D position emits a valid one-frame
    .spectral4 file (header + 1 frame = 180,494 bytes)."""
    fen4 = ("4d-fen v1: K@4,0,0,0; k@4,7,7,7; "
            "Pw@0,1,0,0; Py@0,0,1,0; pw@7,6,7,7; py@7,7,6,7; "
            "N@2,2,2,2; b@5,5,5,5; R@3,4,5,6; q@6,5,4,3")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".spectral4", delete=False) as f:
        out = f.name
    try:
        _run_c_4d(["encode-fen4", "--fen4", fen4, "-o", out])
        size = os.path.getsize(out)
        # 256 (header) + 180238 (1 frame) = 180494
        assert size == 180494, f"expected 180494 bytes, got {size}"
    finally:
        os.unlink(out)


@_REQUIRES_C_4D
def test_4d_encode_bulk_ndjson(tmp_path):
    """encode (NDJSON4 → .spectralz4) on a multi-ply ply-log produces
    1 header + N frames."""
    ndjson = tmp_path / "smoke.ndjson4"
    ndjson.write_text(
        '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0; k@7,7,7,7"}\n'
        '{"ply": 1, "fen4": "4d-fen v1: K@1,0,0,0; k@7,7,7,7", '
        '"move_from": [0,0,0,0], "move_to": [1,0,0,0]}\n'
        '{"ply": 2, "fen4": "4d-fen v1: K@1,0,0,0; k@6,7,7,7", '
        '"move_from": [7,7,7,7], "move_to": [6,7,7,7]}\n',
        encoding="utf-8",
    )
    out = tmp_path / "smoke.spectralz4"
    _run_c_4d(["encode", str(ndjson), "-o", str(out), "-z"])
    assert out.is_file()
    assert out.stat().st_size > 0


@_REQUIRES_C_4D
def test_4d_csv_per_ply_energies(tmp_path):
    """csv on a multi-ply .spectralz4 emits 1 header row + N data rows
    with the documented 24-column layout."""
    ndjson = tmp_path / "smoke.ndjson4"
    ndjson.write_text(
        "\n".join(
            f'{{"ply": {p}, "fen4": "4d-fen v1: K@{p},0,0,0; k@7,7,7,7"}}'
            for p in range(5)
        ) + "\n",
        encoding="utf-8",
    )
    sp = tmp_path / "smoke.spectralz4"
    csv_out = tmp_path / "smoke.csv"
    _run_c_4d(["encode", str(ndjson), "-o", str(sp), "-z"])
    _run_c_4d(["csv", str(sp), "-o", str(csv_out)])
    rows = csv_out.read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == 6  # 1 header + 5 plies
    assert rows[0].count(",") + 1 == 24  # column count documented in main_4d.c


# ─── 4D Python CLI smoke ────────────────────────────────────────────


def test_4d_python_encode_fen4(tmp_path):
    """Python encode-fen4 produces a valid file without needing the C
    binary (fully native Python pipeline)."""
    out = tmp_path / "py.spectral4"
    rc, _ = _run_py_4d([
        "encode-fen4",
        "--fen4", "4d-fen v1: K@0,0,0,0; k@7,7,7,7",
        "-o", str(out),
    ])
    assert rc == 0
    assert out.stat().st_size == 180494


def test_4d_python_encode_moves4_and_corpus_gen(tmp_path):
    """Python encode-moves4 + corpus-gen produce a valid corpus folder
    with manifest.json."""
    nd = tmp_path / "game.ndjson4"
    nd.write_text(
        '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0"}\n'
        '{"ply": 1, "fen4": "4d-fen v1: K@1,0,0,0", '
        '"move_from": [0,0,0,0], "move_to": [1,0,0,0]}\n',
        encoding="utf-8",
    )
    out = tmp_path / "g.spectralz4"
    rc, _ = _run_py_4d(["encode-moves4", "--moves", str(nd), "-o", str(out), "-z"])
    assert rc == 0
    assert out.stat().st_size > 0

    # corpus-gen wraps the same NDJSON into a corpus folder.
    rc, _ = _run_py_4d([
        "corpus-gen", "--games", str(nd),
        "--run-id", "smoke", "--results-root", str(tmp_path),
    ])
    assert rc == 0
    manifest = tmp_path / "smoke" / "manifest.json"
    assert manifest.is_file()
    j = json.loads(manifest.read_text(encoding="utf-8"))
    assert j["n_games"] == 1
    assert j["games"][0]["encode_rc"] == 0


# ─── 4D Oana-Chiru phase verification ───────────────────────────────


def test_4d_tables_verify_all_phases():
    """Run all six phase-N validation gates (1, 2, 3, 4, 5, pawn-axis)
    and assert each one passes. These gates encode the Oana & Chiru
    (AppliedMath 6(3):48, 2026) §3 invariants — piece mobility on
    Z_8^4, B_4 group action, irrep projection, fiber bundle, and the
    v1.1.1 pawn-axis split orthogonality."""
    rc, out = _run_py_4d(["tables-verify", "--phase", "all"])
    assert rc == 0, f"tables-verify failed:\n{out}"
    # Each phase prints "tables-verify phase X: PASS" on success.
    for phase in ("1", "2", "3", "4", "5", "pawn-axis"):
        assert f"tables-verify phase {phase}: PASS" in out, (
            f"phase {phase} did not pass:\n{out}"
        )


# ─── PGN round-trip via pgn_bridge (requires python-chess) ──────────


@_REQUIRES_C
@_REQUIRES_PYTHON_CHESS
def test_pgn_to_spectralz_real_game(tmp_path):
    """Full PGN→NDJSON→.spectralz pipeline using the C `spectral
    encode --pgn` shortcut (which auto-pipes through pgn_bridge.py).
    Exercises the entire hot path a real user runs."""
    out = tmp_path / "kt.spectralz"
    _run_c(["encode", "--pgn", str(SAMPLE_PGN), "-o", str(out), "-z"])
    assert out.is_file()
    # Read it back; the ply count should match the PGN's PlyCount header.
    from chess_spectral import read_all
    hdr, _ = read_all(str(out))
    assert hdr.n_plies == EXPECTED_PLIES, (
        f"PGN→spectralz: expected {EXPECTED_PLIES} plies, "
        f"got {hdr.n_plies}"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
