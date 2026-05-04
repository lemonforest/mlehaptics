"""1.9.0 immolation: legal-moves CLI commands.

Smoke-tests for the new ``chess-spectral legal-moves`` and
``chess-spectral-4d legal-moves`` subcommands. Both shell out to the
package's CLI entry point via ``python -m`` to verify the wiring as a
real downstream consumer would experience it.

Coverage:
  - 2D: startpos has exactly 20 legal moves
  - 2D: --format json includes per-move flags
  - 2D: --with-sheets emits the 11-dim aux block
  - 2D: stdin via '--fen -' works
  - 2D: bad FEN returns a non-zero exit code
  - 4D: canonical Oana-Chiru §3.3 startpos enumerates legal moves
    (count is positive and consistent with prior runs; we don't
    lock the exact count because 4D move-gen evolves)
  - 4D: --format json structure includes 4D-coord 'from'/'to'
  - 4D: --with-sheets has castling/EP slots zero per ruleset
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)


def _run_cli(module: str, *args: str, stdin: str | None = None,
             ) -> subprocess.CompletedProcess:
    """Run a `python -m <module> <args...>` invocation in the package
    directory and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=PKG,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


# ─── 2D legal-moves ─────────────────────────────────────────────────


def test_legal_moves_2d_startpos_has_20_moves():
    """The 2D starting position has exactly 20 legal moves: 8 pawn
    single-pushes + 8 pawn double-pushes + 4 knight moves."""
    pytest.importorskip("chess")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    r = _run_cli("chess_spectral.cli", "legal-moves", "--fen", fen)
    assert r.returncode == 0, f"stderr={r.stderr}"
    moves = [line for line in r.stdout.strip().splitlines() if line]
    assert len(moves) == 20, f"got {len(moves)} moves, expected 20"


def test_legal_moves_2d_json_format_has_per_move_flags():
    pytest.importorskip("chess")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    r = _run_cli("chess_spectral.cli", "legal-moves",
                 "--fen", fen, "--format", "json")
    assert r.returncode == 0, f"stderr={r.stderr}"
    d = json.loads(r.stdout)
    assert d["n_moves"] == 20
    assert d["side_to_move"] == "white"
    # Every move has the expected keys.
    expected_keys = {
        "uci", "san", "from", "to",
        "is_capture", "is_castling", "is_en_passant", "is_promotion",
    }
    for m in d["moves"]:
        assert set(m.keys()) == expected_keys


def test_legal_moves_2d_with_sheets_emits_aux_block():
    """--with-sheets adds the 11-dim aux block + decoded SheetState
    fields to the JSON output."""
    pytest.importorskip("chess")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    r = _run_cli("chess_spectral.cli", "legal-moves",
                 "--fen", fen, "--format", "json", "--with-sheets")
    assert r.returncode == 0, f"stderr={r.stderr}"
    d = json.loads(r.stdout)
    assert "sheet_state" in d
    s = d["sheet_state"]
    # All four castling rights alive at startpos.
    assert s["castling_wk"] is True
    assert s["castling_wq"] is True
    assert s["castling_bk"] is True
    assert s["castling_bq"] is True
    assert s["ep_file"] is None
    assert s["side_to_move_white"] is True
    assert s["halfmove_clock"] == 0
    assert s["repetition_count"] == 0
    assert isinstance(s["aux_block_11d"], list)
    assert len(s["aux_block_11d"]) == 11


def test_legal_moves_2d_san_format():
    """SAN output is one move per line, in standard algebraic notation."""
    pytest.importorskip("chess")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    r = _run_cli("chess_spectral.cli", "legal-moves",
                 "--fen", fen, "--format", "san")
    assert r.returncode == 0
    moves = [line for line in r.stdout.strip().splitlines() if line]
    assert len(moves) == 20
    # SAN at startpos: pawn pushes are bare files (a3, a4, ...) and
    # knight moves carry an N prefix (Na3, Nf3, ...). Both must
    # appear in any complete startpos legal-move list.
    assert any(m.startswith("N") for m in moves), (
        f"expected at least one knight move with N prefix; got {moves}"
    )
    assert any(m in ("a3", "a4", "h3", "h4") for m in moves), (
        f"expected a pawn push (a3/a4/h3/h4) in SAN output; got {moves}"
    )


def test_legal_moves_2d_stdin_input():
    """--fen - reads from stdin, useful for piping."""
    pytest.importorskip("chess")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    r = _run_cli("chess_spectral.cli", "legal-moves",
                 "--fen", "-", stdin=fen)
    assert r.returncode == 0, f"stderr={r.stderr}"
    moves = [line for line in r.stdout.strip().splitlines() if line]
    assert len(moves) == 20


def test_legal_moves_2d_bad_fen_returns_nonzero():
    pytest.importorskip("chess")
    r = _run_cli("chess_spectral.cli", "legal-moves",
                 "--fen", "this is not a fen")
    assert r.returncode != 0
    assert "invalid FEN" in r.stderr or "ValueError" in r.stderr


# ─── 4D legal-moves ─────────────────────────────────────────────────


def _starting_fen4() -> str:
    """Lift the canonical Oana-Chiru §3.3 starting FEN4 from the
    package; avoids hardcoding a 4500-character string in this file."""
    sys.path.insert(0, PKG)
    try:
        from chess_spectral_4d import STARTING_FEN4
        return STARTING_FEN4
    finally:
        if PKG in sys.path:
            sys.path.remove(PKG)


def test_legal_moves_4d_startpos_returns_positive_count():
    """The canonical Oana-Chiru §3.3 starting position has many
    legal moves (4D-OC is dense — 28 kings/side, 448 pieces/side).
    We don't lock the exact count, but it must be > 100 to confirm
    the move-gen pipeline ran end-to-end."""
    fen4 = _starting_fen4()
    r = _run_cli("chess_spectral_4d.cli", "legal-moves",
                 "--fen4", fen4, "--format", "json")
    assert r.returncode == 0, f"stderr={r.stderr}"
    d = json.loads(r.stdout)
    assert d["n_moves"] > 100, (
        f"4D startpos returned {d['n_moves']} moves; expected > 100"
    )
    assert d["side_to_move"] == "white"


def test_legal_moves_4d_json_per_move_structure():
    fen4 = _starting_fen4()
    r = _run_cli("chess_spectral_4d.cli", "legal-moves",
                 "--fen4", fen4, "--format", "json")
    assert r.returncode == 0, f"stderr={r.stderr}"
    d = json.loads(r.stdout)
    expected_keys = {
        "from", "to", "from_sq", "to_sq",
        "promotion", "is_double_push", "is_ep_capture",
    }
    # Sample first 10 moves' shape.
    for m in d["moves"][:10]:
        assert set(m.keys()) == expected_keys
        # 4D coords are 4-vectors of ints in [0, 7]
        assert len(m["from"]) == 4
        assert len(m["to"]) == 4
        for c in m["from"] + m["to"]:
            assert 0 <= c < 8


def test_legal_moves_4d_with_sheets_castling_ep_zero():
    """4D-OC has no castling and no EP per the ruleset; the sheet
    block must reflect that."""
    fen4 = _starting_fen4()
    r = _run_cli("chess_spectral_4d.cli", "legal-moves",
                 "--fen4", fen4, "--format", "json", "--with-sheets")
    assert r.returncode == 0, f"stderr={r.stderr}"
    d = json.loads(r.stdout)
    assert "sheet_state" in d
    s = d["sheet_state"]
    assert s["castling_wk"] is False
    assert s["castling_wq"] is False
    assert s["castling_bk"] is False
    assert s["castling_bq"] is False
    assert s["ep_file"] is None
    # 4D startpos: white to move, halfmove 0
    assert s["side_to_move_white"] is True
    assert s["halfmove_clock"] == 0


def test_legal_moves_4d_compact_format_default():
    """Default compact output: one line per move, 'x,y,z,w->x,y,z,w' form."""
    fen4 = _starting_fen4()
    r = _run_cli("chess_spectral_4d.cli", "legal-moves",
                 "--fen4", fen4)
    assert r.returncode == 0
    lines = [line for line in r.stdout.strip().splitlines() if line]
    assert len(lines) > 100  # many moves in 4D-OC
    # Each line matches the 'a,b,c,d->e,f,g,h' shape (with optional
    # trailing tags).
    sample = lines[0]
    assert "->" in sample, f"expected arrow separator in compact output; got {sample!r}"
    head, _, tail = sample.partition("->")
    assert head.count(",") == 3, f"from-coord should have 4 parts; got {head!r}"
    # Tail may have an optional space + tag suffix; the first
    # comma-split part must be a 4-tuple.
    tail_first = tail.split()[0]
    assert tail_first.count(",") == 3, (
        f"to-coord should have 4 parts; got {tail!r}"
    )


def test_legal_moves_4d_bad_fen4_returns_nonzero():
    r = _run_cli("chess_spectral_4d.cli", "legal-moves",
                 "--fen4", "garbage not a valid fen4")
    assert r.returncode != 0


def test_legal_moves_4d_side_to_move_override():
    """--side-to-move flag changes which side's legal moves are
    enumerated. Different sides = different move counts at the
    canonical startpos (it's a symmetric position but the
    enumeration is asymmetric in implementation)."""
    fen4 = _starting_fen4()
    r_white = _run_cli("chess_spectral_4d.cli", "legal-moves",
                       "--fen4", fen4, "--format", "json",
                       "--side-to-move", "white")
    r_black = _run_cli("chess_spectral_4d.cli", "legal-moves",
                       "--fen4", fen4, "--format", "json",
                       "--side-to-move", "black")
    assert r_white.returncode == 0
    assert r_black.returncode == 0
    d_white = json.loads(r_white.stdout)
    d_black = json.loads(r_black.stdout)
    assert d_white["side_to_move"] == "white"
    assert d_black["side_to_move"] == "black"
    # Both sides must have legal moves at the canonical startpos.
    assert d_white["n_moves"] > 0
    assert d_black["n_moves"] > 0
