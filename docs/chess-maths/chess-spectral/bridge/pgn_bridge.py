#!/usr/bin/env python3
"""pgn_bridge.py — convert PGN (file / stdin / URL) to NDJSON for the
640-dim spectral encoder.

This is the ONLY Python dependency of the spectral pipeline. It exists
because PGN ingestion requires a move parser + legal-move generator +
SAN-disambiguation rules (castling, en-passant, check), which python-chess
already solves robustly. The C encoder consumes NDJSON (one JSON object
per ply) with a "fen" field and computes the 640-dim vector from there.

Usage (as a standalone tool):
    python pgn_bridge.py --input  game.pgn     -o game.ndjson
    python pgn_bridge.py --url    https://lichess.org/game/export/<id>.pgn
    cat game.pgn | python pgn_bridge.py -i -

The C binary `spectral` invokes this script automatically when given a
PGN file or a --url, streaming NDJSON over a pipe (no temp files). You
can also run it by hand to inspect the intermediate NDJSON.

Output schema (one JSON object per line, UTF-8):
    {"game": G, "ply": P, "fen": "...", "uci": "e2e4", "san": "e4"}

  - game: 0-indexed game number (PGN files can contain many games).
  - ply:  0 = starting position (uci and san are empty strings).
          1 = position after the first half-move, etc.
  - fen:  full FEN (the C side only consumes the placement field).
  - uci / san: move that produced this position.

The first emitted line is a header record (not a ply) that lets the C
side sanity-check the stream:
    {"bridge_version": 1, "format": "ndjson-fen"}

Exit codes:
    0 success
    2 missing dependency (python-chess not installed)
    3 input error (no games, unreadable URL/file)
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request

try:
    import chess
    import chess.pgn
except ImportError:
    sys.stderr.write(
        "pgn_bridge: 'python-chess' is required.\n"
        "  Install with:  pip install python-chess\n"
    )
    sys.exit(2)


def open_input(args: argparse.Namespace):
    """Return a text stream yielding PGN content."""
    if args.url:
        try:
            with urllib.request.urlopen(args.url, timeout=30) as r:
                data = r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"pgn_bridge: URL fetch failed: {e}\n")
            sys.exit(3)
        return io.StringIO(data)
    if args.input is None or args.input == "-":
        return sys.stdin
    try:
        return open(args.input, "r", encoding="utf-8", errors="replace")
    except OSError as e:
        sys.stderr.write(f"pgn_bridge: cannot open {args.input}: {e}\n")
        sys.exit(3)


def emit_line(out, obj) -> None:
    out.write(json.dumps(obj, separators=(",", ":")))
    out.write("\n")


def emit_game(out, game: "chess.pgn.Game", game_idx: int) -> int:
    board = game.board()
    emit_line(out, {
        "game": game_idx, "ply": 0,
        "fen": board.fen(), "uci": "", "san": "",
    })
    ply = 0
    for move in game.mainline_moves():
        san = board.san(move)
        uci = move.uci()
        board.push(move)
        ply += 1
        emit_line(out, {
            "game": game_idx, "ply": ply,
            "fen": board.fen(), "uci": uci, "san": san,
        })
    return ply


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PGN -> NDJSON (one position per ply) for the spectral encoder",
    )
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--input", "-i",
                     help="PGN file path, or '-' for stdin")
    src.add_argument("--url", "-u",
                     help="URL returning PGN text (e.g. lichess/chess.com export)")
    ap.add_argument("--output", "-o",
                    help="NDJSON output file (default: stdout)")
    ap.add_argument("--max-games", type=int, default=0,
                    help="Stop after N games (0 = no limit)")
    args = ap.parse_args()

    src_stream = open_input(args)
    if args.output:
        try:
            out = open(args.output, "w", encoding="utf-8", newline="\n")
        except OSError as e:
            sys.stderr.write(f"pgn_bridge: cannot create {args.output}: {e}\n")
            return 3
    else:
        # Force line-buffered stdout so the C side sees frames as they arrive.
        out = sys.stdout
        try:
            out.reconfigure(line_buffering=True)  # py3.7+
        except Exception:  # noqa: BLE001
            pass

    emit_line(out, {"bridge_version": 1, "format": "ndjson-fen"})

    total_games = 0
    total_plies = 0
    try:
        while True:
            game = chess.pgn.read_game(src_stream)
            if game is None:
                break
            total_plies += emit_game(out, game, total_games)
            total_games += 1
            if args.max_games and total_games >= args.max_games:
                break
    finally:
        if args.output:
            out.close()

    if total_games == 0:
        sys.stderr.write("pgn_bridge: no games found in input\n")
        return 3
    sys.stderr.write(
        f"pgn_bridge: emitted {total_games} game(s), {total_plies} plies\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
