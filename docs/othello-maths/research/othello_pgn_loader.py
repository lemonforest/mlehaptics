"""Othello PGN / transcript loader.

Parses the eOthello / liveothello transcript format:

    [Event "Barcelona EGP"]
    [Date "2026.04.12"]
    [Black "Berg Matthias"]
    [White "Tastet Marc"]
    [Result "37-27"]
    1. d3 c5
    3. f6 f5
    ...
    59. h1 a1
    37-27

Move notation is Othello-standard: column letter a-h + row digit 1-8
(NOT chess algebraic - no piece prefixes, no captures marker).
Games are separated by blank lines.  Passes are NOT recorded
explicitly - this loader inserts them automatically when the side
to move has no legal moves.

Exposes:
  - parse_pgn_file(path)   -> list of {headers, moves}
  - move_to_idx(move_str)  -> int in 0..63 for an Othello coordinate
  - replay(moves)          -> (OthelloBoard, list_of_states, move_log)
                              where move_log includes inserted passes

CLI: load a PGN, print summary, optionally validate every move
through OthelloBoard.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator

from othello_utils import OthelloBoard, rc_to_idx

# ---------------------------------------------------------------------------
# Unicode-safe stdout on Windows consoles (cp1252 default).  We keep all
# help-text + stdout output ASCII by convention; this block is belt-and-
# braces for any future contributor who uses a non-ASCII glyph.
# ---------------------------------------------------------------------------
def _ensure_utf8_stdio() -> None:
    """Idempotently set stdout/stderr to utf-8 on Windows consoles.

    Uses TextIOWrapper.reconfigure (Python 3.7+) so that repeated
    import-time invocations from multiple modules do not double-
    wrap and close the underlying buffer.
    """
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except Exception:
            pass


_ensure_utf8_stdio()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(r'^\[(\w+)\s+"(.*)"\]\s*$')
# Accept both lower- and upper-case column letters (e.g. "d3" and
# "D3") - the liveothello 2005 world-championships transcript uses
# uppercase throughout while other corpora use lowercase.
_MOVE_TOKEN_RE = re.compile(r"^[a-hA-H][1-8]$")
_MOVE_NUMBER_RE = re.compile(r"^\d+\.$")
_SCORE_RE = re.compile(r"^\d+-\d+$")


def move_to_idx(move: str) -> int:
    """Convert Othello coordinate like 'd3' or 'D3' to a 0..63 linear
    index.

    Column letter (a..h or A..H) -> 0..7.  Row digit (1..8) -> 0..7.
    Layout is row-major: idx = r * 8 + c.
    """
    if not _MOVE_TOKEN_RE.match(move):
        raise ValueError(f"not an Othello coordinate: {move!r}")
    c = ord(move[0].lower()) - ord("a")
    r = int(move[1]) - 1
    return rc_to_idx(r, c)


def idx_to_move(idx: int) -> str:
    r, c = divmod(idx, 8)
    return f"{chr(ord('a') + c)}{r + 1}"


def parse_pgn_file(path: Path) -> list[dict]:
    """Parse a multi-game PGN into a list of game dicts.

    Each dict has:
      - 'headers': {tag: value} mapping
      - 'moves':   list of Othello move strings (e.g. ['d3', 'c5', 'f6', ...])

    Malformed lines are reported to stderr but do not abort parsing -
    this is research ingestion, best-effort tolerance is preferred.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    games: list[dict] = []
    cur_headers: dict[str, str] = {}
    cur_moves: list[str] = []

    def flush() -> None:
        if cur_moves or cur_headers:
            games.append(
                {"headers": dict(cur_headers), "moves": list(cur_moves)}
            )
        cur_headers.clear()
        cur_moves.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        hm = _HEADER_RE.match(line)
        if hm:
            cur_headers[hm.group(1)] = hm.group(2)
            continue
        if _SCORE_RE.match(line):
            cur_headers["FinalScore"] = line
            continue
        # Otherwise a move list line like: "1. d3 c5"
        for tok in line.split():
            if _MOVE_NUMBER_RE.match(tok):
                continue
            if _MOVE_TOKEN_RE.match(tok):
                # Canonicalise to lowercase so replay() / move_to_idx
                # downstream does not have to care.
                cur_moves.append(tok.lower())
            elif tok.lower() in ("ps", "pass"):
                cur_moves.append("pass")
            else:
                # Unrecognised token: skip but flag.
                print(
                    f"[othello_pgn_loader] ignoring token {tok!r} "
                    f"in line: {line!r}",
                    file=sys.stderr,
                )
    flush()
    return games


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def replay(moves: Iterable[str]) -> tuple[OthelloBoard, list, list]:
    """Replay a move sequence through OthelloBoard.

    Inserts passes automatically when the side to move has no legal
    moves (the standard Othello convention; passes are not usually
    written in transcripts).

    Returns (final_board, states_per_ply, move_log).  states_per_ply
    includes the initial state at index 0.  move_log is a list of
    dicts with keys {'idx', 'is_pass', 'side', 'ply'}, one entry per
    actual ply played (including inserted passes).
    """
    bb = OthelloBoard()
    states: list = [bb.state.copy()]
    move_log: list[dict] = []
    ply = 0
    i = 0
    moves = list(moves)
    while i < len(moves):
        mv = moves[i]
        legal = bb.legal_moves()
        if mv == "pass":
            if legal:
                raise ValueError(
                    f"recorded pass at ply {ply}, but legal moves exist: "
                    f"{[idx_to_move(x) for x in legal]}"
                )
            move_log.append(
                {"idx": None, "is_pass": True, "side": bb.side_to_move,
                 "ply": ply}
            )
            bb.play(None)
            states.append(bb.state.copy())
            ply += 1
            i += 1
            continue
        idx = move_to_idx(mv)
        if not legal:
            # Side to move must pass first.
            move_log.append(
                {"idx": None, "is_pass": True, "side": bb.side_to_move,
                 "ply": ply}
            )
            bb.play(None)
            states.append(bb.state.copy())
            ply += 1
            # Do NOT advance i; re-try the recorded move with the
            # other side now active.
            continue
        if idx not in legal:
            raise ValueError(
                f"recorded move {mv} at ply {ply} is not legal. "
                f"Side {bb.side_to_move}, legal moves: "
                f"{[idx_to_move(x) for x in legal]}"
            )
        move_log.append(
            {"idx": idx, "is_pass": False, "side": bb.side_to_move,
             "ply": ply}
        )
        bb.play(idx)
        states.append(bb.state.copy())
        ply += 1
        i += 1
    # Trailing passes until terminal (rare, but possible)
    while not bb.is_terminal():
        legal = bb.legal_moves()
        if legal:
            break
        move_log.append(
            {"idx": None, "is_pass": True, "side": bb.side_to_move,
             "ply": ply}
        )
        bb.play(None)
        states.append(bb.state.copy())
        ply += 1
    return bb, states, move_log


def replay_sheaf(
    moves: Iterable[str], op=None,
) -> tuple[object, list, list]:
    """Replay a move sequence using ``othello_spectral.move_operator
    .SheafMoveOperator`` as the mutation primitive.

    Functionally equivalent to :func:`replay` — produces the same
    ``(final_board, states_per_ply, move_log)`` tuple with identical
    state sequences and move-log semantics.  Guaranteed by the
    byte-for-byte parity test
    ``tests/test_move_operator.py::test_random_game_parity`` (20
    random games, 100 plies each, zero divergences).

    Why a second entry point?  The happy path of :func:`replay` calls
    ``OthelloBoard.legal_moves()`` on every ply, which scans all 64
    cells and invokes ``flips_from`` 64 times.  The vast majority of
    that work is discarded.  :class:`SheafMoveOperator` walks the 8
    rays from the single target cell instead, calling out to
    ``faithful_sheaf.classify_ray`` — a ~8× speedup on clean corpora
    (liveothello-2026-APR benchmark: 6.67 s → 0.81 s for 414 games).

    The slow path (forced-pass detection when a cell move fails)
    *does* fall back to ``op.legal_moves`` so behaviour on
    anomalous transcripts matches :func:`replay`.

    Parameters
    ----------
    moves : iterable of str
        Sequence of Othello coordinates ("d3", "e6", …) with the
        literal "pass" token for explicitly-recorded passes.
    op : SheafMoveOperator, optional
        Pre-constructed operator to reuse across many replays
        (saves a few import / attribute-cache setups per game).
        If ``None`` a fresh one is constructed per call.

    Returns
    -------
    (final_board, states_per_ply, move_log)
        ``final_board`` is a lightweight object exposing ``.state``
        (int ndarray) and ``.side_to_move`` (int) — enough for
        downstream callers that only need the terminal state.  If
        a full :class:`OthelloBoard` is required use :func:`replay`.
    """
    import numpy as np
    # Lazy import — keeps this module import-cheap for callers that
    # don't use the sheaf path.
    import sys
    from pathlib import Path as _Path
    _research_dir = _Path(__file__).resolve().parent
    if str(_research_dir) not in sys.path:
        sys.path.insert(0, str(_research_dir))
    from othello_spectral.move_operator import SheafMoveOperator
    from othello_utils import BLACK

    if op is None:
        op = SheafMoveOperator()

    state = np.zeros(64, dtype=int)
    state[27] = -1  # d4
    state[28] = +1  # e4
    state[35] = +1  # d5
    state[36] = -1  # e5
    side = BLACK  # +1
    states: list = [state.copy()]
    move_log: list[dict] = []
    ply = 0
    i = 0
    moves = list(moves)

    def _flip_side():
        nonlocal side
        side = -side

    while i < len(moves):
        mv = moves[i]
        if mv == "pass":
            # Explicit pass: trust the transcript, match replay()
            # behaviour (which would raise if legal moves exist).
            legal = op.legal_moves(state, side)
            if legal:
                raise ValueError(
                    f"recorded pass at ply {ply}, but legal moves "
                    f"exist: {[idx_to_move(x) for x in legal]}"
                )
            move_log.append(
                {"idx": None, "is_pass": True, "side": side,
                 "ply": ply}
            )
            _flip_side()
            states.append(state.copy())
            ply += 1
            i += 1
            continue
        idx = move_to_idx(mv)
        flipped = op.flipped_cells(state, idx, side)
        if not flipped:
            # Either the move is genuinely illegal OR the side is
            # forced to pass first.  Check legal_moves() to
            # disambiguate — this is the only per-ply legal_moves
            # call in the sheaf path.
            legal = op.legal_moves(state, side)
            if legal:
                # Genuine illegality
                raise ValueError(
                    f"recorded move {mv} at ply {ply} is not legal. "
                    f"Side {side}, legal moves: "
                    f"{[idx_to_move(x) for x in legal]}"
                )
            # Forced pass; insert and retry same move with other side
            move_log.append(
                {"idx": None, "is_pass": True, "side": side,
                 "ply": ply}
            )
            _flip_side()
            states.append(state.copy())
            ply += 1
            continue
        # Apply the move — copy state, place disc, flip brackets
        state = state.copy()
        state[idx] = side
        for c in flipped:
            state[c] = side
        move_log.append(
            {"idx": idx, "is_pass": False, "side": side, "ply": ply}
        )
        _flip_side()
        states.append(state)
        ply += 1
        i += 1

    # Trailing forced passes until both sides have no moves.
    while True:
        legal_self = op.legal_moves(state, side)
        legal_other = op.legal_moves(state, -side)
        if legal_self or (not legal_self and not legal_other):
            # Either we have a move (stop), or game is terminal (stop)
            if legal_self:
                break
            if not legal_self and not legal_other:
                break
        # Here: legal_self == [] but legal_other != []  →  insert pass
        move_log.append(
            {"idx": None, "is_pass": True, "side": side, "ply": ply}
        )
        _flip_side()
        states.append(state.copy())
        ply += 1

    # Return a lightweight shim with the same .state / .side_to_move
    # attributes as OthelloBoard for callers that only peek.
    class _Shim:
        __slots__ = ("state", "side_to_move")

        def __init__(self, s, stm):
            self.state = s
            self.side_to_move = stm

    return _Shim(state, side), states, move_log


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _summarise_game(g: dict) -> dict:
    moves = g["moves"]
    try:
        bb, states, log = replay(moves)
        n_passes = sum(1 for m in log if m["is_pass"])
        b, w, e = bb.disc_counts()
        outcome = (
            "black_wins" if b > w
            else "white_wins" if w > b
            else "draw"
        )
        return {
            "event": g["headers"].get("Event", ""),
            "date": g["headers"].get("Date", ""),
            "black": g["headers"].get("Black", ""),
            "white": g["headers"].get("White", ""),
            "reported_final_score": g["headers"].get("FinalScore", ""),
            "n_moves_in_transcript": len(moves),
            "n_plies_replayed": len(log),
            "n_passes_inserted": n_passes,
            "computed_black": b,
            "computed_white": w,
            "computed_empty": e,
            "outcome": outcome,
            "ok": True,
        }
    except Exception as exc:
        return {
            "event": g["headers"].get("Event", ""),
            "date": g["headers"].get("Date", ""),
            "black": g["headers"].get("Black", ""),
            "white": g["headers"].get("White", ""),
            "reported_final_score": g["headers"].get("FinalScore", ""),
            "n_moves_in_transcript": len(moves),
            "error": str(exc),
            "ok": False,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Print one-line summary of every game in the Barcelona EGP file,
  # including auto-inserted passes and computed final score.
  python research/othello_pgn_loader.py \\
      --input dataset/liveothello_Barcelona_EGP_2026.pgn

  # Same, but also write a JSON summary to the results directory.
  python research/othello_pgn_loader.py \\
      --input dataset/liveothello_Barcelona_EGP_2026.pgn \\
      --out results/barcelona_egp_summary.json

  # Exit non-zero if any game fails to replay (useful for CI).
  python research/othello_pgn_loader.py \\
      --input dataset/liveothello_Barcelona_EGP_2026.pgn \\
      --fail-on-error

notes:
  The loader automatically inserts passes when a side has no legal
  move - this is the Othello rule (passes are mandatory when forced)
  but is rarely written in transcripts.  The 'n_passes_inserted'
  column reports how many were added per game.
""",
    )
    parser.add_argument(
        "--input", type=Path, required=True,
        help="Path to an Othello PGN / transcript file.  Expected "
             "format is eOthello-style 'N. <move> <move>' lines with "
             "column letter a-h and row digit 1-8.  Header tags "
             "([Event ...], [Black ...], etc.) are optional.  Games "
             "are separated by blank lines.",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Optional JSON output path for the per-game summary "
             "(parent directories are created if missing).  If "
             "omitted, the summary is printed to stdout only.",
    )
    parser.add_argument(
        "--fail-on-error", action="store_true",
        help="Exit with status 1 if any game in the file fails to "
             "replay (illegal move, malformed transcript, etc.).  "
             "Default: print the error per-game but exit 0.  Use "
             "this flag in CI to catch corpus corruption.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress the per-game summary table; only print the "
             "aggregate line at the end.  Useful when piping to "
             "other tools.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    games = parse_pgn_file(args.input)
    summaries = [_summarise_game(g) for g in games]

    n_ok = sum(1 for s in summaries if s.get("ok"))
    n_err = len(summaries) - n_ok

    if not args.quiet:
        print(f"parsed {len(games)} games from {args.input}")
        print(f"{'idx':>3s}  {'plies':>5s}  {'passes':>6s}  "
              f"{'B-W':>7s}  {'reported':>10s}  status  black vs white")
        for i, s in enumerate(summaries):
            if s.get("ok"):
                bw = f"{s['computed_black']}-{s['computed_white']}"
                print(
                    f"{i:>3d}  {s['n_plies_replayed']:>5d}  "
                    f"{s['n_passes_inserted']:>6d}  {bw:>7s}  "
                    f"{s['reported_final_score']:>10s}  OK      "
                    f"{s['black']} vs {s['white']}"
                )
            else:
                print(
                    f"{i:>3d}  {'-':>5s}  {'-':>6s}  "
                    f"{'-':>7s}  {s['reported_final_score']:>10s}  "
                    f"FAIL    {s.get('error', '')[:80]}"
                )

    print(f"\nsummary: {n_ok}/{len(summaries)} games replayed cleanly"
          f" ({n_err} errors)")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as f:
            json.dump(
                {"input": str(args.input), "games": summaries}, f, indent=2
            )
        print(f"wrote {args.out}")

    if args.fail_on_error and n_err:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
