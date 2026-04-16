#!/usr/bin/env python3
"""pgn_bridge.py — convert PGN (file / stdin / URL) to lossless NDJSON
for the 640-dim spectral encoder.

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

Output schema v2 (one JSON object per line, UTF-8) — LOSSLESS:
    Header:
      {"bridge_version":2,"format":"ndjson-fen-v2"}
    Per-game record (before ply 0 of that game):
      {"type":"game_header","game":G,"headers":{"White":...,"Result":...,...}}
    Per-ply record:
      {"game":G,"ply":P,"fen":"...","uci":"e2e4","san":"e4",
       "move_from":52,"move_to":36,"move_promo":0,
       "nag":"?!","eval":"+0.15","clk":"1:58","comment":"..."}

  - game:      0-indexed game number (PGN files can contain many games).
  - ply:       0 = starting position; uci/san are "" for ply 0.
  - fen:       full FEN; the C side only reads the placement field.
  - uci / san: move that produced this position.
  - move_from, move_to: 0..63 in encoder convention (row 0 = rank 8).
                        0xFF sentinel at ply 0.
  - move_promo: ASCII code of the promotion letter ('Q','R','B','N'),
                0 if not a promotion.
  - nag:       PGN annotation glyph mapped to punctuation (??, ?, ?!,
               !?, !, !!); omitted if absent.
  - eval:      white-POV engine score in pawns ("+0.15") or mate ("#5");
               omitted if absent.
  - clk:       remaining clock time ("M:SS" or "H:MM:SS"); omitted if
               absent.
  - comment:   free-text comment stripped of [%eval …] / [%clk …] macros
               (those live in `eval` / `clk`); omitted if empty.

v1 consumers (reading only fen/uci/san) still work — v2 is strictly
additive. v2 emits `"bridge_version":2` so readers that care can branch
on it.

Exit codes:
    0 success
    2 missing dependency (python-chess not installed)
    3 input error (no games, unreadable URL/file)
"""
from __future__ import annotations

import argparse
import io
import json
import re
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


BRIDGE_VERSION = 2
FORMAT_TAG = "ndjson-fen-v2"


# ─── PGN annotation extraction ──────────────────────────────────────────
#
# NAG (Numeric Annotation Glyph) → punctuation. Priority order matters:
# a move annotated with both $2 and $6 is shown as "?" (stronger), etc.
# python-chess exposes node.nags as a set[int].
_NAG_MAP = {
    4: "??",  # blunder
    2: "?",   # mistake
    6: "?!",  # inaccuracy / dubious
    5: "!?",  # interesting / speculative
    1: "!",   # good move
    3: "!!",  # brilliant
}
_NAG_PRIORITY = (4, 2, 6, 5, 3, 1)   # worst-blunder first so ?? dominates

_EVAL_MACRO_RE = re.compile(r"\[%eval\s+[^\]]+\]")
_CLK_MACRO_RE = re.compile(r"\[%clk\s+[^\]]+\]")


def _nag_tag(nags) -> str | None:
    for n in _NAG_PRIORITY:
        if n in nags:
            return _NAG_MAP[n]
    return None


def _eval_str(node) -> str | None:
    """Extract `[%eval ...]` as pawn-equivalent float ('+0.15') or mate
    ('#5' / '#-3') from White's POV. None if absent."""
    pov = node.eval()
    if pov is None:
        return None
    sc = pov.white()
    m = sc.mate()
    if m is not None:
        return f"#{m}"
    cp = sc.score()
    if cp is None:
        return None
    return f"{cp / 100.0:+.2f}"


def _clock_str(node) -> str | None:
    """Extract `[%clk ...]` as 'M:SS' or 'H:MM:SS'. None if absent."""
    s = node.clock()
    if s is None:
        return None
    total = int(round(s))
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def _comment_text(node) -> str | None:
    """PGN comment with [%eval …] / [%clk …] macros stripped. None if
    the residue is empty (pure-macro comments don't deserve a field)."""
    raw = (node.comment or "").strip()
    if not raw:
        return None
    stripped = _CLK_MACRO_RE.sub("", _EVAL_MACRO_RE.sub("", raw))
    stripped = " ".join(stripped.split())  # collapse whitespace
    return stripped or None


# ─── Square-index conversion (python-chess → encoder convention) ────────
#
# python-chess: 0 = a1 … 63 = h8 (rank-major from White's side).
# encoder:      row*8 + col with row 0 = rank 8 (matches FEN top-to-bottom).

def _pc_to_encoder_sq(pc_sq: int) -> int:
    rank = pc_sq >> 3        # 0 = rank 1 … 7 = rank 8
    file = pc_sq & 7         # 0 = a … 7 = h
    return (7 - rank) * 8 + file


# ─── I/O helpers ────────────────────────────────────────────────────────

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
    out.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
    out.write("\n")


# ─── Core: replay a game, walking the node tree to keep NAGs/comments ───

def emit_game(out, game: "chess.pgn.Game", game_idx: int,
              annotated: bool = True) -> int:
    """Emit one game as NDJSON records. Returns the ply count."""
    # Per-game header: all PGN tag pairs, preserved verbatim.
    headers = {k: v for k, v in game.headers.items()}
    emit_line(out, {
        "type": "game_header",
        "game": game_idx,
        "headers": headers,
    })

    board = game.board()
    emit_line(out, {
        "game": game_idx, "ply": 0,
        "fen": board.fen(), "uci": "", "san": "",
        "move_from": 0xFF, "move_to": 0xFF, "move_promo": 0,
    })

    ply = 0
    node = game
    # Walk the main line while still seeing nags/comments/eval/clk that
    # mainline_moves() drops. node.variation(0) = mainline child.
    while node.variations:
        nxt = node.variation(0)
        move = nxt.move
        san = board.san(move)
        uci = move.uci()
        mf = _pc_to_encoder_sq(move.from_square)
        mt = _pc_to_encoder_sq(move.to_square)
        mp = int(move.promotion) if move.promotion is not None else 0
        # Promotion byte is ASCII of the uppercase piece letter so callers
        # don't need python-chess constants to interpret it.
        if mp:
            mp = ord(chess.piece_symbol(mp).upper())

        board.push(move)
        ply += 1

        rec = {
            "game": game_idx, "ply": ply,
            "fen": board.fen(), "uci": uci, "san": san,
            "move_from": mf & 0xFF, "move_to": mt & 0xFF,
            "move_promo": mp & 0xFF,
        }
        if annotated:
            nag = _nag_tag(nxt.nags) if nxt.nags else None
            if nag is not None:
                rec["nag"] = nag
            ev = _eval_str(nxt)
            if ev is not None:
                rec["eval"] = ev
            clk = _clock_str(nxt)
            if clk is not None:
                rec["clk"] = clk
            cmt = _comment_text(nxt)
            if cmt is not None:
                rec["comment"] = cmt

        emit_line(out, rec)
        node = nxt

    return ply


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PGN -> lossless NDJSON (one position per ply) for "
                    "the spectral encoder",
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
    ap.add_argument("--no-annotations", action="store_true",
                    help="Skip per-ply nag/eval/clk/comment fields "
                         "(smaller records; equivalent to v1 schema)")
    args = ap.parse_args()

    src_stream = open_input(args)
    if args.output:
        try:
            out = open(args.output, "w", encoding="utf-8", newline="\n")
        except OSError as e:
            sys.stderr.write(f"pgn_bridge: cannot create {args.output}: {e}\n")
            return 3
    else:
        out = sys.stdout
        try:
            out.reconfigure(line_buffering=True)  # py3.7+
        except Exception:  # noqa: BLE001
            pass

    emit_line(out, {"bridge_version": BRIDGE_VERSION, "format": FORMAT_TAG})

    total_games = 0
    total_plies = 0
    try:
        while True:
            game = chess.pgn.read_game(src_stream)
            if game is None:
                break
            total_plies += emit_game(out, game, total_games,
                                     annotated=not args.no_annotations)
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
        f"pgn_bridge: emitted {total_games} game(s), {total_plies} plies "
        f"(v{BRIDGE_VERSION})\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
