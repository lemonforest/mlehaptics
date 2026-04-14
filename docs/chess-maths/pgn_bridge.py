#!/usr/bin/env python3
"""
PGN Bridge — Export chess games to NDJSON for Python + C17 consumption
======================================================================

Converts PGN games (from any pgn_fetcher source) into NDJSON bridge files.
Each line represents one position (ply) from a game, containing the FEN,
pos_dict, and provenance metadata.

The bridge format is designed for two consumers:
  1. Python experiments — json.loads(line) per position
  2. Future C17 spectral encoder — parse with cJSON (single-header, MIT)

Bridge NDJSON format:
  Line 1 (header):
    {"bridge_version":1,"created":"2026-04-13","n_games":42,"n_positions":3847}
  Lines 2+:
    {"fen":"...","pos":{"0":"R","1":"N",...},"source":"twic/tatamast26",
     "game_idx":0,"ply":1,"move":"e4","result":"1-0"}

Optional field (with --include-signal):
    "signal_64": [0.0, 0.0, ..., 1.08, ...]  (64 floats, board signal)

C17 usage example:
    // Read line, parse with cJSON:
    cJSON *root = cJSON_Parse(line);
    const char *fen = cJSON_GetObjectItem(root, "fen")->valuestring;
    cJSON *pos = cJSON_GetObjectItem(root, "pos");
    cJSON *sq = pos->child;
    while (sq) {
        int index = atoi(sq->string);
        char piece = sq->valuestring[0];
        board[index] = piece;
        sq = sq->next;
    }
    cJSON_Delete(root);

Dependencies: python-chess (pip install chess)
Optional: encoder_512 (for --include-signal)

Usage:
    # Export from a TWIC tournament
    python pgn_bridge.py --source twic --event tatamast26 --output bridge.ndjson

    # Export from chessgames.com
    python pgn_bridge.py --source chessgames --gid 1011478 1937789 -o bridge.ndjson

    # Export from a local PGN file
    python pgn_bridge.py --input games.pgn --output bridge.ndjson

    # Include pre-computed board signal (for C17 encoder)
    python pgn_bridge.py --input games.pgn --include-signal -o bridge.ndjson

    # Read back in Python
    for pos in read_ndjson('bridge.ndjson'):
        print(pos['fen'], pos['ply'], pos['move'])
"""

import os
import sys
import json
import io
import argparse
from datetime import date

import chess
import chess.pgn

# Import from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pgn_fetcher import MultiFetcher, PGNSource


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

BRIDGE_VERSION = 1


# ═══════════════════════════════════════════════════════════════
# FEN / POS CONVERSION (self-contained, no encoder dependency)
# ═══════════════════════════════════════════════════════════════

def fen_to_pos(fen):
    """Convert a FEN string to a pos_dict {sq_index: piece_char}.

    Uses python-chess for robust parsing (handles all FEN variants).
    Coordinate convention: sq(r, c) = r*8 + c, row 0 = rank 8.
    """
    board = chess.Board(fen)
    pos = {}
    for square, piece in board.piece_map().items():
        # chess.square: 0=a1, 1=b1, ..., 63=h8
        rank = chess.square_rank(square)   # 0=rank 1, 7=rank 8
        file = chess.square_file(square)   # 0=a, 7=h
        our_row = 7 - rank                 # 0=rank 8, 7=rank 1
        our_col = file
        idx = our_row * 8 + our_col
        pos[idx] = piece.symbol()
    return pos


# ═══════════════════════════════════════════════════════════════
# GAME REPLAY
# ═══════════════════════════════════════════════════════════════

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


def _nag_tag(nags: set[int]) -> str | None:
    for n in _NAG_PRIORITY:
        if n in nags:
            return _NAG_MAP[n]
    return None


def _eval_str(node) -> str | None:
    """Extract `[%eval ...]` from a node. Returns 'cp' as pawn-equivalent
    float string like '0.15' or mate as '#5' / '#-3'. None if absent."""
    pov = node.eval()
    if pov is None:
        return None
    sc = pov.white()  # always from White's POV so signs are stable
    m = sc.mate()
    if m is not None:
        return f"#{m}"
    cp = sc.score()
    if cp is None:
        return None
    return f"{cp / 100.0:.2f}"


def _clock_str(node) -> str | None:
    """Extract `[%clk ...]` from a node as 'M:SS' (or 'H:MM:SS' for long
    time controls). None if absent."""
    s = node.clock()
    if s is None:
        return None
    total = int(round(s))
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


# ─── Move-index conversion ───────────────────────────────────────────────
#
# python-chess uses 0=a1 ... 63=h8 (rank-major from White's side). The
# .spectral v2 move_from/move_to bytes are raw 0-63 indices with 0xFF as
# the "no move" sentinel. We pass python-chess's native indexing straight
# through — the C side currently emits 0xFF placeholders, so Python is
# the first writer to populate these. Downstream tools treating 0-63 as
# a1-h8 will interpret them correctly.
#
# Promotion: python-chess `move.promotion` is a chess.PieceType (2..5) or
# None. Map to the v2 byte: 0 = no promotion, else the piece type integer.
_PROMO_NONE = 0


def _move_indices(move: chess.Move) -> tuple[int, int, int]:
    """Return (from_sq, to_sq, promo) for writing to the v2 frame.
    from_sq/to_sq are 0..63 (python-chess convention). promo is the
    chess.PieceType integer (KNIGHT=2, BISHOP=3, ROOK=4, QUEEN=5) or 0."""
    promo = move.promotion if move.promotion is not None else _PROMO_NONE
    return (move.from_square & 0xFF, move.to_square & 0xFF, int(promo) & 0xFF)


def game_to_positions(game_dict):
    """Replay a game and yield position records with PGN annotations.

    Args:
        game_dict: Normalized game dict from pgn_fetcher (has 'pgn' key)

    Yields:
        (ply, move_san, fen, pos_dict, eval_str, clk_str, nag,
         move_from, move_to, move_promo) tuples.
        ply=0 is the starting position — eval/clk/nag all None, and
        move_from/move_to/move_promo are all 0xFF/0 sentinels.
        eval_str / clk_str / nag may be None if the source PGN didn't
        include them.
    """
    pgn_text = game_dict.get('pgn', '')
    if not pgn_text:
        return

    try:
        game = chess.pgn.read_game(io.StringIO(pgn_text))
    except Exception:
        return

    if game is None:
        return

    board = game.board()

    # Starting position (no move metadata to attach; 0xFF sentinels).
    pos = fen_to_pos(board.fen())
    yield (0, 'start', board.fen(), pos, None, None, None, 0xFF, 0xFF, 0)

    # Replay moves by walking the node tree (mainline_moves() drops NAGs
    # and comments; we need both).
    ply = 1
    node = game
    while node.variations:
        nxt = node.variation(0)
        move = nxt.move
        san = board.san(move)
        mf, mt, mp = _move_indices(move)
        board.push(move)
        pos = fen_to_pos(board.fen())

        eval_s = _eval_str(nxt)
        clk_s  = _clock_str(nxt)
        nag    = _nag_tag(nxt.nags) if nxt.nags else None

        yield (ply, san, board.fen(), pos, eval_s, clk_s, nag, mf, mt, mp)
        node = nxt
        ply += 1


# ═══════════════════════════════════════════════════════════════
# NDJSON EXPORT
# ═══════════════════════════════════════════════════════════════

def _try_import_signal():
    """Try to import board_signal from encoder_512. Returns (func, vals) or None."""
    try:
        from encoder_512 import board_signal, SPECTRAL_VALS
        return board_signal, SPECTRAL_VALS
    except ImportError:
        return None, None


def export_ndjson(games, output, include_signal=False, verbose=True):
    """Write bridge NDJSON from a list of game dicts.

    Args:
        games: List of normalized game dicts (from pgn_fetcher)
        output: File-like object or file path string
        include_signal: If True, pre-compute 64-dim board signal per position
        verbose: Print progress
    """
    signal_fn, signal_vals = None, None
    if include_signal:
        signal_fn, signal_vals = _try_import_signal()
        if signal_fn is None:
            print("  Warning: encoder_512 not available, "
                  "skipping --include-signal", file=sys.stderr)
            include_signal = False

    # Determine output target
    should_close = False
    if isinstance(output, str):
        output = open(output, 'w', encoding='utf-8')
        should_close = True

    try:
        # Count positions for the header (two-pass: replay first to count)
        # Actually, write header as a placeholder, then update? No — NDJSON
        # header is informational. Write it with what we know, then positions.
        total_positions = 0
        sources_seen = set()

        # First pass: collect all position records
        all_records = []
        for game_idx, game in enumerate(games):
            source = game.get('source', 'unknown')
            source_id = game.get('source_id', '')
            result = game.get('headers', {}).get('Result', '*')
            source_key = f"{source}/{source_id}" if source_id else source
            sources_seen.add(source_key)

            for (ply, move, fen, pos, ev, clk, nag,
                 mf, mt, mp) in game_to_positions(game):
                record = {
                    'fen': fen,
                    'pos': {str(k): v for k, v in pos.items()},
                    'source': source_key,
                    'game_idx': game_idx,
                    'ply': ply,
                    'move': move,
                    # Move indices (0..63, 0xFF=no move). Native python-chess
                    # indexing: 0=a1 ... 63=h8. Written verbatim into the
                    # v2 frame's move_from/move_to bytes by spectral_py.
                    'move_from': mf,
                    'move_to': mt,
                    'result': result,
                }
                # Promotion byte is only meaningful on promotions; omit
                # otherwise to keep records compact.
                if mp:
                    record['move_promo'] = mp
                # Optional PGN annotations — only emitted when present so
                # records from unannotated PGNs stay compact.
                if ev is not None:
                    record['eval'] = ev
                if clk is not None:
                    record['clk'] = clk
                if nag is not None:
                    record['nag'] = nag

                if include_signal:
                    import numpy as np
                    sig = signal_fn(pos, vals=signal_vals)
                    record['signal_64'] = [round(float(x), 6) for x in sig]

                all_records.append(record)

            if verbose and (game_idx + 1) % 10 == 0:
                print(f"  Processed {game_idx + 1}/{len(games)} games "
                      f"({len(all_records)} positions)", flush=True)

        # Write header
        header = {
            'bridge_version': BRIDGE_VERSION,
            'created': date.today().isoformat(),
            'n_games': len(games),
            'n_positions': len(all_records),
            'sources': sorted(sources_seen),
        }
        output.write(json.dumps(header) + '\n')

        # Write position records
        for record in all_records:
            output.write(json.dumps(record, separators=(',', ':')) + '\n')

        if verbose:
            print(f"  Wrote {len(all_records)} positions from "
                  f"{len(games)} games", flush=True)

    finally:
        if should_close:
            output.close()


# ═══════════════════════════════════════════════════════════════
# NDJSON READER
# ═══════════════════════════════════════════════════════════════

def read_ndjson(input_file):
    """Read bridge NDJSON and yield position dicts.

    Args:
        input_file: File path string or file-like object

    Yields:
        Position dicts (skips the header line).
        The pos field is converted back to {int: str} keys.
    """
    should_close = False
    if isinstance(input_file, str):
        input_file = open(input_file, 'r', encoding='utf-8')
        should_close = True

    try:
        for line_num, line in enumerate(input_file):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip header line
            if 'bridge_version' in record:
                continue

            # Convert pos keys back to int
            if 'pos' in record:
                record['pos'] = {int(k): v for k, v in record['pos'].items()}

            yield record
    finally:
        if should_close:
            input_file.close()


def read_ndjson_header(input_file):
    """Read just the header from a bridge NDJSON file.

    Returns the header dict, or None if no header found.
    """
    should_close = False
    if isinstance(input_file, str):
        input_file = open(input_file, 'r', encoding='utf-8')
        should_close = True

    try:
        for line in input_file:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                return None
            if 'bridge_version' in record:
                return record
            return None  # first non-empty line isn't a header
    finally:
        if should_close:
            input_file.close()

    return None


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog='pgn_bridge',
        description='Export chess games to NDJSON bridge format for C17 encoder',
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i',
                             help='Input PGN file path')
    input_group.add_argument('--source', '-s',
                             choices=['hf', 'huggingface', 'chessgames', 'twic'],
                             help='Fetch from a pgn_fetcher source')

    # Output. Default: mirror the input basename with a .ndjson extension
    # (e.g. "lichess_pgn_2026.04.14_Fabsid.VEYpg.pgn" → "…VEYpg.ndjson").
    # Uses os.path.splitext so multi-dot basenames are preserved (splitting
    # on the LAST dot, never the first).
    parser.add_argument('--output', '-o',
                        help='Output NDJSON file path '
                             '(default: <input-basename>.ndjson when -i is used)')

    # Source-specific args
    parser.add_argument('--event', help='TWIC event name')
    parser.add_argument('--gid', type=int, nargs='+',
                        help='chessgames.com GID(s)')
    parser.add_argument('--n', type=int, default=20,
                        help='Number of games for HF source (default: 20)')
    parser.add_argument('--seed', type=int, help='Random seed (HF)')
    parser.add_argument('--max-games', type=int, help='Max games to export')

    # Bridge options
    parser.add_argument('--include-signal', action='store_true',
                        help='Pre-compute 64-dim board signal (requires encoder_512)')

    args = parser.parse_args()

    # Get games
    if args.input:
        # Read from local PGN file
        print(f"  Reading PGN from {args.input}...")
        with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
            pgn_text = f.read()
        games = PGNSource.parse_games(pgn_text, max_games=args.max_games)
        # Add source metadata. splitext splits on the LAST dot, so names
        # like "lichess_pgn_2026.04.14_Fabsid.VEYpg.pgn" keep their full
        # stem ("…VEYpg") rather than being chopped at the first dot.
        basename = os.path.splitext(os.path.basename(args.input))[0]
        for g in games:
            g['source'] = 'file'
            g['source_id'] = basename
        # Auto-derive output path if -o wasn't given: sit the .ndjson
        # next to the .pgn and use the same stem.
        if not args.output:
            d = os.path.dirname(args.input)
            args.output = (os.path.join(d, basename + ".ndjson")
                           if d else basename + ".ndjson")
        print(f"  Parsed {len(games)} games from file")

    else:
        # Fetch from source
        multi = MultiFetcher(verbose=True)

        if args.source in ('chessgames',):
            if not args.gid:
                parser.error("--gid required for chessgames source")
            games = multi.fetch('chessgames', gids=args.gid)

        elif args.source in ('twic',):
            if not args.event:
                parser.error("--event required for twic source")
            games = multi.fetch('twic', event=args.event,
                                max_games=args.max_games or args.n)

        elif args.source in ('hf', 'huggingface'):
            games = multi.fetch('huggingface', n=args.n, seed=args.seed)

        else:
            parser.error(f"Unknown source: {args.source}")
            return

        print(f"  Fetched {len(games)} games")

    if not games:
        print("  No games to export.")
        return

    # Require an output path — fetcher sources (no --input) don't auto-derive.
    if not args.output:
        parser.error("--output is required when using --source "
                     "(only --input auto-derives)")

    # Export
    print(f"  Exporting to {args.output}...")
    export_ndjson(games, args.output, include_signal=args.include_signal)
    print(f"  Done: {args.output}")


if __name__ == '__main__':
    main()
