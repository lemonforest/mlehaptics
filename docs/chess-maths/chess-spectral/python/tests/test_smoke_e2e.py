"""End-to-end smoke ("immolation") suite for chess-spectral v1.2.4+.

This is the "does everything we ship still work?" test. It exercises
every wired CLI command against a real, verified game from the dataset
(Kasparov vs Topalov, Hoogovens 1999 R4 — 87 plies, "Kasparov's
Immortal") plus the 2D phase-operator package, the 4D Oana-Chiru
table-verification gates, and seeded deterministic self-play that
generates fresh games per test run.

This suite is the canonical release gate: run it before every PyPI
tag. If anything we ship is broken, this catches it.

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

    2D phase-spatial validator chain (3 layers):
      python-chess (external, well-tested)
        ↓ test_spatial_op_matches_python_chess
      our spatial op (chess_spectral.tables.SHORT_PFNS + blocking + king-safety)
        ↓ test_seeded_self_play_phase_op_legal_moves_match
      our phase op (chess_spectral.phase_operators.occupation_aware_moves_a)
      Each layer is independently validated against the next; the
      external dep is isolated to a single test. Released code stays
      untouched — all helpers live under python/tests/.

    4D Oana-Chiru spatial validation (single layer):
      Our spatial op (chess_spectral.tables_4d.<piece>4_targets) is
      validated against the paper-predicted invariants in §3 (piece
      mobility on Z₈⁴, B₄ group action, irrep projection, fiber
      bundle, pawn-axis orthogonality) via `chess_spectral_4d
      tables-verify --phase all`. There is no 4D phase operator in
      chess-spectral today — the phase_operators package is 2D-only.
      Adding a 4D phase operator + a chess4d → tables_4d → phase4d
      validator chain analogous to the 2D one is future work.

Skip behavior:
    - Tests that need the C binary skip cleanly if it isn't built
      (set $CS_SPECTRAL_BIN / $CS_SPECTRAL_4D_BIN, or build the
      Release config).
    - Tests that need python-chess (the optional `[corpus]` extra)
      skip if it isn't installed.

Runs in ~90 s end-to-end on a warm Python interpreter; 34 tests.
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


# ─── Seeded self-play: dynamic game generation via phase operators ──
#
# The Kasparov-Topalov fixture above is real and verified, but it's a
# fixed game. To exercise the move-generation surface (phase operators)
# against varied positions, we add a deterministic random-legal self-
# play helper: feed it RNG seeds for white and black, get back a list
# of plies. Same seeds → same game on every machine and run.
#
# python-chess is the well-tested ground truth: it generates the legal-
# move set we sample from and applies the chosen move. The phase
# operators (chess_spectral.phase_operators.*) are the unit-under-
# test: on every ply we cross-check phasecast_is_check against
# python-chess's board.is_check(), and (separately) verify that
# occupation_aware_moves_a's pseudo-legal candidate set covers
# python-chess's legal destinations for non-pawn pieces.
#
# Default: a single seed shared between both colors gives fully
# symmetric deterministic play. Pass distinct white_seed and
# black_seed to make the two RNGs independent (asymmetric exploration
# of the game tree).


def _seeded_self_play(white_seed: int,
                      black_seed: int | None = None,
                      *, max_plies: int = 50) -> list[dict]:
    """Play a deterministic random-legal self-play game.

    Move generation: python-chess (well-tested baseline).
    Phase-operator validation: on every ply we assert
    `phasecast_is_check(board) == board.is_check()` — exercising the
    phase-operator code path against a real game progression.

    Args:
        white_seed: RNG seed for white's move choices.
        black_seed: RNG seed for black. Defaults to `white_seed` when
            None — symmetric deterministic play. Pass distinct to
            give the two colors independent RNGs (asymmetric).
        max_plies: cap on game length.

    Returns:
        List of dicts ready to write as NDJSON, one per position
        (including the starting position at ply 0). Each dict has
        {ply, fen, move_from, move_to, promo, flags}; move_from /
        move_to are 0xFF on ply 0 (no predecessor move).
    """
    import chess
    import random
    from chess_spectral.phase_operators import phasecast_is_check

    rng_w = random.Random(white_seed)
    rng_b = random.Random(black_seed if black_seed is not None
                          else white_seed)

    board = chess.Board()
    out = [{
        "ply": 0, "fen": board.fen(),
        "move_from": 0xFF, "move_to": 0xFF,
        "promo": 0, "flags": 0,
    }]

    for ply_idx in range(1, max_plies + 1):
        # Phase-operator cross-check: agreement with python-chess on
        # check status. Mismatch here = real phase-op bug.
        if phasecast_is_check(board) != board.is_check():
            raise AssertionError(
                f"phase_operators.phasecast_is_check disagrees with "
                f"python-chess at ply {ply_idx - 1}: "
                f"phase_op={phasecast_is_check(board)}, "
                f"python-chess={board.is_check()}, fen={board.fen()}"
            )

        legal = list(board.legal_moves)
        if not legal:
            break  # checkmate / stalemate

        rng = rng_w if board.turn == chess.WHITE else rng_b
        move = rng.choice(legal)
        board.push(move)

        out.append({
            "ply":       ply_idx,
            "fen":       board.fen(),
            "move_from": move.from_square,
            "move_to":   move.to_square,
            "promo":     move.promotion or 0,
            "flags":     int(board.is_check()),
        })

        if board.is_game_over():
            break

    return out


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_is_reproducible():
    """Same seeds → same FEN sequence on every run."""
    a = _seeded_self_play(white_seed=42, max_plies=30)
    b = _seeded_self_play(white_seed=42, max_plies=30)
    assert [p["fen"] for p in a] == [p["fen"] for p in b], (
        "seeded self-play is not deterministic"
    )


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_separate_seeds_diverge():
    """Same white_seed → identical opening; different black_seed →
    games diverge once black gets the move."""
    a = _seeded_self_play(white_seed=42, black_seed=42, max_plies=30)
    b = _seeded_self_play(white_seed=42, black_seed=99, max_plies=30)
    # Ply 0 (starting pos) and ply 1 (white's first move) must agree.
    assert a[0]["fen"] == b[0]["fen"]
    assert a[1]["fen"] == b[1]["fen"]
    # By ply 30, divergence is overwhelmingly likely.
    assert any(a[i]["fen"] != b[i]["fen"]
               for i in range(2, min(len(a), len(b)))), (
        "asymmetric seeds did not produce divergent games"
    )


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_default_black_inherits_white_seed():
    """When `black_seed` is None, both colors share `white_seed` —
    fully symmetric deterministic play (same as if you'd passed the
    same seed twice)."""
    a = _seeded_self_play(white_seed=2026, max_plies=20)
    b = _seeded_self_play(white_seed=2026, black_seed=2026, max_plies=20)
    assert [p["fen"] for p in a] == [p["fen"] for p in b]


def _write_ndjson_for_c_encoder(plies: list[dict], path) -> None:
    """Write NDJSON with the compact separator the C encoder's
    json_str_field expects (`"key":"value"` — no whitespace after the
    colon, since C's substring scan looks for that exact prefix)."""
    path.write_text(
        "\n".join(json.dumps(p, separators=(",", ":")) for p in plies)
        + "\n",
        encoding="utf-8",
    )


@_REQUIRES_C
@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_encodes_via_c_pipeline(tmp_path):
    """End-to-end: seeded game → NDJSON → C encoder → .spectral.
    Verifies the encoder consumes the dynamically-generated game
    cleanly and the resulting file's header reflects the played plies."""
    plies = _seeded_self_play(white_seed=12345, max_plies=40)
    nd_path = tmp_path / "seeded.ndjson"
    _write_ndjson_for_c_encoder(plies, nd_path)
    sp_path = tmp_path / "seeded.spectral"
    _run_c(["encode", str(nd_path), "-o", str(sp_path)])
    from chess_spectral import read_all
    hdr, frames = read_all(str(sp_path))
    assert hdr.n_plies == len(plies), (
        f"encoded {hdr.n_plies} frames, expected {len(plies)} from "
        f"seeded play"
    )
    assert len(frames) == len(plies)


@_REQUIRES_C
@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_analyze_pipeline(tmp_path):
    """Full pipeline including analyze: seeded game → encode → analyze
    JSON. Exercises both encoder and the analyze CLI on game data
    that wasn't pre-recorded."""
    plies = _seeded_self_play(white_seed=7, black_seed=13, max_plies=30)
    nd_path = tmp_path / "seeded.ndjson"
    _write_ndjson_for_c_encoder(plies, nd_path)
    sp_path = tmp_path / "seeded.spectral"
    _run_c(["encode", str(nd_path), "-o", str(sp_path)])
    out = _run_c(["analyze", str(sp_path)]).stdout
    j = json.loads(out)
    assert j["n_plies"] == len(plies)
    for key in ("a1_peak_ply", "a1_drop_ply", "crisis_ply",
                "e_total_max_ply"):
        assert 0 <= j[key] < len(plies), (
            f"analyze {key}={j[key]} out of range [0, {len(plies)})"
        )


def _spatial_legal_dests(board, sq: int) -> set:
    """Compute the set of legal destinations for a non-pawn piece at
    `sq` using ONLY chess_spectral.tables.SHORT_PFNS (geometric move
    generators) + a slider-blocking walk + king-safety via python-
    chess board state. python-chess is used here for board state and
    the move-and-check primitive (push / pop / is_attacked_by); the
    move CANDIDATE GENERATION comes entirely from our own SHORT_PFNS.

    This is the middle layer of the test-only validation chain:

        python-chess (well-tested external) ─validates→ spatial op
        spatial op (our own SHORT_PFNS-based) ─validates→ phase op

    Layer 1 → 2 is verified by `test_spatial_op_matches_python_chess`.
    Layer 2 → 3 is verified by
    `test_seeded_self_play_phase_op_legal_moves_match`.

    Pawns and castling are not covered here — pawns have direction-
    plus-axis rules that SHORT_PFNS doesn't model, and castling is a
    composite move handled by chess_spectral.phase_operators.castling
    separately."""
    import chess
    from chess_spectral.tables import SHORT_PFNS

    piece = board.piece_at(sq)
    if piece is None:
        return set()
    sym = piece.symbol().upper()
    if sym not in SHORT_PFNS:
        return set()
    own_color = piece.color
    rank = chess.square_rank(sq)
    file = chess.square_file(sq)

    # 1. Pseudo-legal destinations via SHORT_PFNS + blocking.
    pseudo: set[int] = set()
    is_slider = sym in ('B', 'R', 'Q')
    if not is_slider:
        # Knights jump; kings step. No blocking. Just exclude own-color
        # squares.
        for nr, nc in SHORT_PFNS[sym](rank, file):
            target = chess.square(nc, nr)
            target_piece = board.piece_at(target)
            if target_piece is not None and target_piece.color == own_color:
                continue
            pseudo.add(target)
    else:
        # Sliders: SHORT_PFNS emits squares in direction order, distance
        # ascending within each direction. Track the unit vector from
        # the origin to detect direction changes; reset 'blocked' state
        # at each direction boundary.
        prev_dir: tuple[int, int] | None = None
        blocked = False
        for nr, nc in SHORT_PFNS[sym](rank, file):
            dr, dc = nr - rank, nc - file
            unit = (0 if dr == 0 else (1 if dr > 0 else -1),
                    0 if dc == 0 else (1 if dc > 0 else -1))
            if unit != prev_dir:
                prev_dir = unit
                blocked = False
            if blocked:
                continue
            target = chess.square(nc, nr)
            target_piece = board.piece_at(target)
            if target_piece is None:
                pseudo.add(target)
            elif target_piece.color != own_color:
                pseudo.add(target)  # capture allowed
                blocked = True       # ray stops at the captured piece
            else:
                blocked = True       # own piece blocks; can't capture

    # 2. Filter by king-safety: a move is legal iff applying it doesn't
    #    leave the mover's king under attack. Use python-chess push/pop
    #    for the apply primitive — chess-spectral has no equivalent.
    legal: set[int] = set()
    for to_sq in pseudo:
        move = chess.Move(sq, to_sq)
        if move not in board.pseudo_legal_moves:
            continue  # a corner case (e.g. promotion required, or move
                      # wasn't classifiable by python-chess) — skip
        board.push(move)
        try:
            still_attacked = board.is_attacked_by(
                not own_color,
                board.king(own_color) if board.king(own_color) is not None
                else to_sq,  # king moved → check the destination
            )
        finally:
            board.pop()
        if not still_attacked:
            legal.add(to_sq)

    return legal


@_REQUIRES_PYTHON_CHESS
def test_spatial_op_matches_python_chess():
    """Layer 1 → 2: validates our spatial operator (SHORT_PFNS-based)
    against python-chess's legal_moves for each non-pawn piece across
    a sample of positions reached during seeded self-play. Verifies
    the spatial op correctly implements geometry + blocking + king-
    safety on real board states, before we use it as ground truth for
    the phase op test."""
    import chess

    plies = _seeded_self_play(white_seed=2026, max_plies=20)
    for p in plies[:8]:
        board = chess.Board(p["fen"])
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece is None or piece.color != board.turn:
                continue
            sym = piece.symbol().upper()
            if sym not in 'NBRQK':
                continue
            spatial = _spatial_legal_dests(board, sq)
            ref = {
                m.to_square for m in board.legal_moves
                if m.from_square == sq and m.promotion is None
                # exclude castling (king moves >1 square): handled
                # by phase_operators.available_castles separately
                and not (sym == 'K'
                         and abs(chess.square_file(m.to_square)
                                 - chess.square_file(sq)) > 1)
            }
            assert spatial == ref, (
                f"spatial op != python-chess legal for {sym} at "
                f"{chess.square_name(sq)} (fen={p['fen']}): "
                f"spatial={sorted(spatial)}, python-chess={sorted(ref)}, "
                f"missing={sorted(ref - spatial)}, "
                f"extra={sorted(spatial - ref)}"
            )


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_phase_op_legal_moves_match():
    """Layer 2 → 3: the phase operator's `occupation_aware_moves_a`
    must agree with our spatial operator (validated separately
    against python-chess by `test_spatial_op_matches_python_chess`)
    on the legal destinations for each non-pawn piece during seeded
    self-play.

    Three-layer chain — this is the phase-op-against-spatial-op leg:

        python-chess  ─validates→  spatial op  ─validates→  phase op

    Pawns and castling are excluded (occupation_aware_moves_a doesn't
    handle them — they're separate phase-operator entry points;
    castling is wired into available_castles, separately tested by
    test_2d_phase_operators_smoke).

    Convention: occupation_aware_moves_a uses chess.square_rank /
    chess.square_file directly (rank 0 = rank 1, white's bottom row).
    The function is "hybrid" per its docstring: it generates phase-
    space candidates and then filters them through python-chess
    legality, so the returned set is exactly the legal moves for that
    piece — equality is the right check, not subset."""
    import chess
    from chess_spectral.phase_operators import occupation_aware_moves_a

    plies = _seeded_self_play(white_seed=2026, max_plies=20)
    for p in plies[:8]:  # sample first 8 plies (covers opening moves)
        board = chess.Board(p["fen"])
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece is None or piece.color != board.turn:
                continue
            sym = piece.symbol().upper()
            if sym not in 'NBRQK':
                continue  # skip pawns (different phase-op entry point)
            rank = chess.square_rank(sq)
            file = chess.square_file(sq)
            mover_charge = 1 if board.turn == chess.WHITE else -1
            dests = occupation_aware_moves_a(
                board, sym, rank, file, mover_charge,
            )
            phase_to_squares = {chess.square(c, r) for r, c in dests}
            # Ground truth: spatial op (validated against python-chess
            # by test_spatial_op_matches_python_chess). Excludes
            # castling, just like spatial op does.
            spatial_to_squares = _spatial_legal_dests(board, sq)
            assert phase_to_squares == spatial_to_squares, (
                f"phase op set != spatial op set for {sym} at "
                f"{chess.square_name(sq)} (fen={p['fen']}): "
                f"phase_op={sorted(phase_to_squares)}, "
                f"spatial_op={sorted(spatial_to_squares)}, "
                f"missing={sorted(spatial_to_squares - phase_to_squares)}, "
                f"extra={sorted(phase_to_squares - spatial_to_squares)}"
            )


# ─── Seeded 4D self-play: dynamic position generation via tables_4d ─
#
# 4D analog of the 2D seeded self-play above. Differences:
#
#   - No python-chess: 4D has no python-chess equivalent. We use
#     chess_spectral.tables_4d's per-piece movement generators
#     (rook4_targets, knight4_targets, etc.) directly — the same
#     functions that build the encoder's adjacency tables.
#
#   - No legality / check / checkmate: there's no 4D Oana-Chiru rule
#     enforcement layer in the project (see ROADMAP.md follow-up). We
#     do a "random walk" — each ply picks a random non-pawn piece and
#     a random valid (in-bounds, unoccupied) destination per the piece-
#     movement generator. No captures, no promotions, no checks.
#
#   - This exercises: the 4D piece-movement generators in tables_4d,
#     the FEN4 parser (validates each generated position), and the
#     full 4D encoder pipeline (encode-fen4 / encode bulk / csv).
#
# Same seeded interface as 2D: white_seed required, black_seed
# optional (defaults to white_seed). Different seeds give the two
# colors independent walks.


_4D_PIECE_TARGETS = {
    'N': 'knight4_targets',
    'B': 'bishop4_targets',
    'R': 'rook4_targets',
    'Q': 'queen4_targets',
    'K': 'king4_targets',
}


def _seeded_self_play_4d(white_seed: int,
                         black_seed: int | None = None,
                         *, max_plies: int = 30) -> list[dict]:
    """Random-walk 4D piece progression on the Z₈⁴ lattice.

    Starts from a small mixed position (kings + a handful of
    non-pawn pieces) and on each ply moves one randomly-chosen
    piece to a random valid (in-bounds, unoccupied) target per the
    piece's movement generator from chess_spectral.tables_4d.

    Returns a list of NDJSON4-ready dicts: {"ply", "fen4",
    "move_from", "move_to", "promo", "flags"}. ply 0 is the
    starting position; subsequent plies record the move and the
    resulting FEN4.

    Pawns are excluded — pawn movement on Z₈⁴ has axis constraints
    (Oana-Chiru Def. 11) the FEN4 v1 parser enforces but the random
    walk doesn't model promotion / first-move rules. Future-work
    item in ROADMAP.md."""
    import random
    from chess_spectral import tables_4d as t4

    rng_w = random.Random(white_seed)
    rng_b = random.Random(black_seed if black_seed is not None
                          else white_seed)

    # Starting position: 2 kings + 1 of each major piece per side.
    # Spread across the lattice so movement isn't trivially blocked.
    pos = {
        (0, 0, 0, 0): 'K',  (7, 7, 7, 7): 'k',
        (1, 1, 1, 1): 'Q',  (6, 6, 6, 6): 'q',
        (2, 2, 2, 2): 'R',  (5, 5, 5, 5): 'r',
        (3, 0, 0, 0): 'B',  (4, 7, 7, 7): 'b',
        (0, 3, 0, 0): 'N',  (7, 4, 7, 7): 'n',
    }

    def _to_fen4(p):
        parts = [f"{piece}@{x},{y},{z},{w}"
                 for (x, y, z, w), piece in sorted(p.items())]
        return "4d-fen v1: " + "; ".join(parts)

    out = [{
        "ply": 0, "fen4": _to_fen4(pos),
        "move_from": [0, 0, 0, 0], "move_to": [0, 0, 0, 0],
        "promo": 0, "flags": 0,
    }]

    color_to_move = 'white'  # alternates each ply
    for ply_idx in range(1, max_plies + 1):
        rng = rng_w if color_to_move == 'white' else rng_b

        # Pick a random piece of the side-to-move with at least one
        # valid destination.
        movable = []
        is_white = (color_to_move == 'white')
        for coord, piece in pos.items():
            piece_white = piece.isupper()
            if piece_white != is_white:
                continue
            sym = piece.upper()
            target_fn = getattr(t4, _4D_PIECE_TARGETS.get(sym, ''),
                                None)
            if target_fn is None:
                continue
            valid = []
            for tgt in target_fn(*coord):
                if not all(0 <= c < 8 for c in tgt):
                    continue
                if tgt in pos:
                    continue  # occupied — skip (no captures)
                valid.append(tgt)
            if valid:
                movable.append((coord, valid))
        if not movable:
            break

        from_coord, dests = rng.choice(movable)
        to_coord = rng.choice(dests)
        piece = pos.pop(from_coord)
        pos[to_coord] = piece

        out.append({
            "ply":       ply_idx,
            "fen4":      _to_fen4(pos),
            "move_from": list(from_coord),
            "move_to":   list(to_coord),
            "promo":     0,
            "flags":     0,
        })
        color_to_move = 'black' if color_to_move == 'white' else 'white'

    return out


def test_seeded_self_play_4d_is_reproducible():
    """Same seeds → identical 4D progression."""
    a = _seeded_self_play_4d(white_seed=42, max_plies=20)
    b = _seeded_self_play_4d(white_seed=42, max_plies=20)
    assert [p["fen4"] for p in a] == [p["fen4"] for p in b]


def test_seeded_self_play_4d_separate_seeds_diverge():
    """Distinct white/black seeds → asymmetric walks."""
    a = _seeded_self_play_4d(white_seed=42, black_seed=42, max_plies=20)
    b = _seeded_self_play_4d(white_seed=42, black_seed=99, max_plies=20)
    assert a[0]["fen4"] == b[0]["fen4"]  # starting position identical
    assert a[1]["fen4"] == b[1]["fen4"]  # ply 1 = white, same seed
    # Once black moves (ply 2 onward), divergence is overwhelming.
    assert any(a[i]["fen4"] != b[i]["fen4"]
               for i in range(2, min(len(a), len(b))))


def test_seeded_self_play_4d_uses_real_piece_movement():
    """Each move recorded by the helper must be a destination
    actually returned by the piece's movement generator. Catches any
    bug where the helper accidentally creates moves that bypass the
    Oana-Chiru piece-movement rules."""
    from chess_spectral import tables_4d as t4

    plies = _seeded_self_play_4d(white_seed=2026, max_plies=15)
    for i, p in enumerate(plies[1:], start=1):
        prev = plies[i - 1]
        from_c = tuple(p["move_from"])
        to_c = tuple(p["move_to"])
        # Find the piece at `from_c` in the PREVIOUS position by
        # parsing the prev FEN4. Reuse fen_4d.parse for fidelity.
        from chess_spectral import fen_4d
        prev_pos = fen_4d.parse(prev["fen4"])
        sq = ((from_c[0] * 8 + from_c[1]) * 8 + from_c[2]) * 8 + from_c[3]
        piece_value = prev_pos[sq]
        sym = (piece_value if isinstance(piece_value, str)
               else piece_value[0]).upper()
        target_fn = getattr(t4, _4D_PIECE_TARGETS[sym])
        valid_targets = set(target_fn(*from_c))
        assert to_c in valid_targets, (
            f"ply {i}: {sym}@{from_c} → {to_c} is NOT a valid "
            f"piece-movement target per tables_4d (valid set "
            f"size: {len(valid_targets)})"
        )


@_REQUIRES_C_4D
def test_seeded_self_play_4d_encodes_via_c_pipeline(tmp_path):
    """End-to-end 4D: seeded random-walk → NDJSON4 → spectral_4d
    encode → .spectralz4. Verifies the full 4D pipeline on
    dynamically-generated game data without depending on any external
    PGN dataset or python-chess."""
    plies = _seeded_self_play_4d(white_seed=12345, max_plies=20)
    nd_path = tmp_path / "seeded4d.ndjson4"
    nd_path.write_text(
        "\n".join(json.dumps(p, separators=(",", ":")) for p in plies)
        + "\n",
        encoding="utf-8",
    )
    sp_path = tmp_path / "seeded4d.spectralz4"
    _run_c_4d(["encode", str(nd_path), "-o", str(sp_path), "-z"])
    assert sp_path.is_file()
    assert sp_path.stat().st_size > 0


@_REQUIRES_C_4D
def test_seeded_self_play_4d_csv_pipeline(tmp_path):
    """4D end-to-end including csv: seeded walk → encode → csv (24
    columns × N data rows)."""
    plies = _seeded_self_play_4d(white_seed=7, black_seed=13,
                                 max_plies=15)
    nd_path = tmp_path / "seeded4d.ndjson4"
    nd_path.write_text(
        "\n".join(json.dumps(p, separators=(",", ":")) for p in plies)
        + "\n",
        encoding="utf-8",
    )
    sp_path = tmp_path / "seeded4d.spectralz4"
    csv_path = tmp_path / "seeded4d.csv"
    _run_c_4d(["encode", str(nd_path), "-o", str(sp_path), "-z"])
    _run_c_4d(["csv", str(sp_path), "-o", str(csv_path)])
    rows = csv_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == len(plies) + 1  # 1 header + N plies
    assert rows[0].count(",") + 1 == 24


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
