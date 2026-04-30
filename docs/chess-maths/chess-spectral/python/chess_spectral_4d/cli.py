#!/usr/bin/env python3
"""chess_spectral_4d.cli — argparse CLI for the 4D chess-spectral encoder.

Every subcommand exposes `--help`. This is the discovery contract for the
4D tooling: run `--help` first, always.

Subcommands:

    tables-verify   Run validation gates from each implementation phase.
                    --phase 1 checks piece mobility on Z_8^4 (rook=28,
                    king=80, knight=48, bishop 2 components).
    encode-fen4     Encode a FEN4 v1 literal (docs/FEN4_FORMAT.md) to a
                    single-frame v4 .spectralz4. Output is byte-identical
                    to the C `spectral_4d encode-fen4` binary.
    encode-moves4   Encode a JSONL move log to a v4 .spectralz4.
                    Schema: one JSON object per line with fields
                    {ply, from:[x,y,z,w], to:[x,y,z,w], promo, flags}.
                    (stubbed; awaits 4D move semantics in Phase B.)
    corpus-gen      Wrap N JSONL move logs into a corpus folder mirroring
                    the 2D `spectral_py corpus` layout. (stubbed; Phase B.)
    version         Print version + v3/v4 magic/format info.

Exit codes:
    0   success
    2   argument / usage error (also the argparse default)
    3   runtime error (I/O, validation failure, etc.)
    4   not implemented yet in this build
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Iterable, Iterator, Tuple

from chess_spectral_4d import (
    VERSION,
    ENCODING_DIM_4D,
    BOARD_SIDE_4D,
    N_DIMENSIONS_4D,
)
from chess_spectral import frame_4d as _frame_4d
from chess_spectral import fen_4d as _fen_4d
from chess_spectral.encoder_4d import encode_4d as _encode_4d

SPECTRALZ_MAGIC = _frame_4d.SPECTRALZ_MAGIC.decode("ascii")
SPECTRALZ_VERSION = _frame_4d.SPECTRALZ_VERSION
# Retained alias for older callers that referenced the v3 magic name.
SPECTRALZ_V3_MAGIC = SPECTRALZ_MAGIC


# --- stub helper ---------------------------------------------------------

def _not_implemented(cmd: str, what: str) -> int:
    print(
        f"{cmd}: {what} is not yet implemented in this build.\n"
        f"       See ROADMAP.md for the phase order.",
        file=sys.stderr,
    )
    return 4


# --- tables-verify -------------------------------------------------------

def cmd_tables_verify(args: argparse.Namespace) -> int:
    """Run one (or all) phase validation gates. Each gate prints a single
    pass/fail line. Return 0 iff every requested gate passes."""
    if args.phase == "all":
        phases = ["1", "2", "3", "4", "5", "pawn-axis"]
    else:
        phases = [args.phase]

    overall = 0
    for p in phases:
        if p == "1":
            rc = _run_phase_gate("1", "verify_phase1", verbose=args.verbose)
        elif p == "2":
            rc = _run_phase_gate("2", "verify_phase2", verbose=args.verbose)
        elif p == "3":
            rc = _run_phase_gate("3", "verify_phase3", verbose=args.verbose)
        elif p == "4":
            rc = _run_phase_gate("4", "verify_phase4", verbose=args.verbose)
        elif p == "5":
            rc = _run_phase_gate("5", "verify_phase5", verbose=args.verbose)
        elif p == "pawn-axis":
            rc = _run_phase_gate("pawn-axis", "verify_pawn_axis",
                                 verbose=args.verbose)
        else:
            print(f"tables-verify: unknown phase {p!r}", file=sys.stderr)
            rc = 2
        sys.stdout.flush()
        if rc != 0 and overall == 0:
            overall = rc

    return overall


def _run_phase_gate(phase: str, fn_name: str, verbose: bool) -> int:
    """Generic phase-gate runner: import `fn_name` from
    chess_spectral.tables_4d, call it with verbose=..., print report
    lines, return 0 on success / 3 on AssertionError or ImportError."""
    try:
        from chess_spectral import tables_4d
        fn = getattr(tables_4d, fn_name)
    except (ImportError, AttributeError) as e:
        print(f"tables-verify phase {phase}: import error ({e})",
              file=sys.stderr)
        return 3

    try:
        report = fn(verbose=verbose)
    except AssertionError as e:
        print(f"tables-verify phase {phase}: FAIL -- {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"tables-verify phase {phase}: ERROR -- {type(e).__name__}: {e}",
              file=sys.stderr)
        return 3

    for line in report:
        print(f"  {line}")
    print(f"tables-verify phase {phase}: PASS")
    return 0


# --- encode-fen4 ---------------------------------------------------------

def cmd_encode_fen4(args: argparse.Namespace) -> int:
    """Parse a FEN4 v1 literal, encode to 45056 float32, write a one-frame
    v4 .spectralz4 (optionally gzip-compressed). Output byte-identical to
    the C `spectral_4d encode-fen4` binary."""
    try:
        pos4 = _fen_4d.parse(args.fen4)
    except _fen_4d.Fen4ParseError as e:
        print(f"encode-fen4: {e}", file=sys.stderr)
        return 3

    enc = _encode_4d(pos4)

    frame_bytes = ENCODING_DIM_4D * 4 + _frame_4d.FRAME_TAIL_BYTES
    header = _frame_4d.pack_header(ENCODING_DIM_4D, frame_bytes, n_plies=1)
    frame = _frame_4d.pack_frame(
        enc, ply=0,
        from_sq=(0, 0, 0, 0), to_sq=(0, 0, 0, 0),
        promo=0, flags=0,
        encoding_dim=ENCODING_DIM_4D,
    )
    payload = header + frame

    output = args.output
    if not output or output == "-":
        if args.compress:
            print("encode-fen4: -z requires --output <path>; "
                  "cannot gzip-stream to stdout", file=sys.stderr)
            return 2
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
        return 0

    out_path = Path(output)
    if args.compress:
        # `mtime=0` makes gzip output deterministic across runs (no
        # timestamp drift), which is mandatory for byte-for-byte parity
        # with the C side. The C writer (cs_gzip.c) also writes mtime=0.
        with gzip.GzipFile(filename=str(out_path), mode="wb",
                           mtime=0) as fp:
            fp.write(payload)
    else:
        out_path.write_bytes(payload)
    return 0


# --- encode-moves4 -------------------------------------------------------

def _iter_ndjson4(path: Path) -> Iterator[Tuple[int, dict]]:
    """Yield (line_no, parsed_json_obj) for each non-skipped line in
    `path`. Lines containing 'bridge_version' are skipped (matching
    the 2D producer convention). Malformed JSON lines are skipped with
    a warning to stderr."""
    with open(path, "r", encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, start=1):
            line = line.strip()
            if not line or "bridge_version" in line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as e:
                print(f"encode-moves4: line {line_no}: JSON decode error: {e}",
                      file=sys.stderr)
                continue


def _frame_from_record(rec: dict, fallback_ply: int):
    """Build a Frame4D from one NDJSON4 record. Returns (frame, error)
    where error is None on success or a string describing the parse
    failure (caller skips the line)."""
    fen4 = rec.get("fen4")
    if not isinstance(fen4, str):
        return None, "missing 'fen4' field"
    try:
        pos4 = _fen_4d.parse(fen4)
    except _fen_4d.Fen4ParseError as e:
        return None, str(e)
    enc = _encode_4d(pos4)

    def _coord(rec, key):
        v = rec.get(key)
        if isinstance(v, list) and len(v) == 4 and all(
            isinstance(x, int) and 0 <= x <= 255 for x in v
        ):
            return tuple(v)
        return (0, 0, 0, 0)

    ply = rec.get("ply")
    if not isinstance(ply, int) or ply < 0:
        ply = fallback_ply
    return _frame_4d.Frame4D(
        encoding=enc,
        ply=ply,
        from_sq=_coord(rec, "move_from"),
        to_sq=_coord(rec, "move_to"),
        promo=int(rec.get("promo", 0)) & 0xFF,
        flags=int(rec.get("flags", 0)) & 0xFF,
    ), None


def cmd_encode_moves4(args: argparse.Namespace) -> int:
    """Encode an NDJSON4 ply-log to a v4 .spectralz4 file. Each line is
    one position represented by a FEN4 v1 literal (see
    docs/NDJSON4_FORMAT.md). Output is byte-identical (decompressed) to
    `spectral_4d encode`."""
    src = Path(args.moves)
    if not src.is_file():
        print(f"encode-moves4: input not found: {src}", file=sys.stderr)
        return 3

    output = args.output
    if not output:
        print("encode-moves4: missing --output <path>", file=sys.stderr)
        return 2

    frames = []
    n_skipped = 0
    for line_no, rec in _iter_ndjson4(src):
        fr, err = _frame_from_record(rec, fallback_ply=len(frames))
        if err:
            print(f"encode-moves4: line {line_no}: {err}", file=sys.stderr)
            n_skipped += 1
            continue
        # Optional --start / --count ply gating, matching the existing
        # argparse surface (defaults: start=0, count=0=no-limit).
        if args.start and fr.ply < args.start:
            continue
        if args.count and len(frames) >= args.count:
            break
        frames.append(fr)

    if not frames:
        print("encode-moves4: warning — no plies written "
              "(empty input or all FEN4 parse errors)", file=sys.stderr)

    frame_bytes = ENCODING_DIM_4D * 4 + _frame_4d.FRAME_TAIL_BYTES
    header = _frame_4d.pack_header(ENCODING_DIM_4D, frame_bytes,
                                   n_plies=len(frames))
    out_path = Path(output)
    if args.compress:
        with gzip.GzipFile(filename=str(out_path), mode="wb",
                           mtime=0) as fp:
            fp.write(header)
            for fr in frames:
                fp.write(_frame_4d.pack_frame(
                    fr.encoding, fr.ply, fr.from_sq, fr.to_sq,
                    fr.promo, fr.flags, encoding_dim=ENCODING_DIM_4D,
                ))
    else:
        with open(out_path, "wb") as fp:
            fp.write(header)
            for fr in frames:
                fp.write(_frame_4d.pack_frame(
                    fr.encoding, fr.ply, fr.from_sq, fr.to_sq,
                    fr.promo, fr.flags, encoding_dim=ENCODING_DIM_4D,
                ))
    return 0


# --- corpus-gen ----------------------------------------------------------

def cmd_corpus_gen(args: argparse.Namespace) -> int:
    """Wrap N NDJSON4 ply-logs into a corpus folder mirroring the layout
    used by the 2D `chess-spectral corpus`. For each input game:

        <results_root>/<run_id>/
            ndjson/<stem>.ndjson    (copy of the input)
            spectralz/<stem>.spectralz4
        <results_root>/<run_id>/manifest.json   (per-game metadata)

    Honors --limit to cap the number of games processed."""
    games = [Path(g) for g in args.games]
    missing = [g for g in games if not g.is_file()]
    if missing:
        for m in missing:
            print(f"corpus-gen: input not found: {m}", file=sys.stderr)
        return 3

    if args.limit and args.limit > 0:
        games = games[: args.limit]

    if not args.run_id or not args.results_root:
        print("corpus-gen: --run-id and --results-root are required",
              file=sys.stderr)
        return 2

    run_dir = Path(args.results_root) / args.run_id
    ndjson_dir = run_dir / "ndjson"
    spectralz_dir = run_dir / "spectralz"
    ndjson_dir.mkdir(parents=True, exist_ok=True)
    spectralz_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for idx, src in enumerate(games):
        stem = f"game_{idx:03d}"
        # Copy the source NDJSON into the corpus.
        dst_ndjson = ndjson_dir / f"{stem}.ndjson"
        dst_ndjson.write_bytes(src.read_bytes())

        # Encode to .spectralz4 by re-using cmd_encode_moves4 directly.
        dst_spectralz = spectralz_dir / f"{stem}.spectralz4"
        class _Args:
            pass
        eargs = _Args()
        eargs.moves = str(dst_ndjson)
        eargs.output = str(dst_spectralz)
        eargs.compress = True
        eargs.start = 0
        eargs.count = 0
        rc = cmd_encode_moves4(eargs)
        manifest.append({
            "index": idx,
            "stem": stem,
            "source": str(src),
            "ndjson": f"ndjson/{stem}.ndjson",
            "spectralz": f"spectralz/{stem}.spectralz4",
            "encode_rc": rc,
        })

    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": args.run_id, "n_games": len(games),
                    "games": manifest}, indent=2),
        encoding="utf-8",
    )
    print(f"corpus-gen: wrote {len(games)} games to {run_dir}",
          file=sys.stderr)
    return 0


# --- version -------------------------------------------------------------

def cmd_version(args: argparse.Namespace) -> int:
    print(f"chess_spectral_4d {VERSION}")
    print(f"  spectralz magic:    {SPECTRALZ_MAGIC!r}")
    print(f"  spectralz version:  {SPECTRALZ_VERSION}")
    print(f"  encoding_dim:       {ENCODING_DIM_4D}")
    print(f"  board_dim_side:     {BOARD_SIDE_4D}")
    print(f"  n_dimensions:       {N_DIMENSIONS_4D}")
    return 0


# --- parser --------------------------------------------------------------

def _sq4_to_coord_str(sq: int) -> str:
    """Format a 4D flat index as 'x,y,z,w' for CLI output."""
    side = 8
    w = sq % side
    z = (sq // side) % side
    y = (sq // (side * side)) % side
    x = (sq // (side * side * side)) % side
    return f"{x},{y},{z},{w}"


def cmd_search_4d(args: argparse.Namespace) -> int:
    """4D analogue of the 2D `search` command. See spectral_py search --help.

    The agent spec syntax is identical (evaluator / depth / weights /
    ablations / etc.) — only the binding differs (chess_spectral_4d
    modules). This is the §16's symmetric per-side configuration: a
    user can drive 4D search with the same spec format as 2D.
    """
    import json as _json
    from chess_spectral.engine.tournament.agent_spec import (
        parse_spec, build_agent_4d,
    )
    from chess_spectral.spatial_4d.board import Board4D

    if args.fen4:
        board = Board4D.from_fen(args.fen4)
    else:
        # No 4D starting-position helper yet; require explicit fen4.
        print(
            "search: --fen4 required (no default starting position for "
            "4D yet; pass an explicit FEN4 v1 literal -- see "
            "docs/FEN4_FORMAT.md)",
            file=sys.stderr,
        )
        return 2

    spec = parse_spec(args.agent)
    agent = build_agent_4d(spec)

    result = agent.search_fn(board, agent.evaluator, agent.search_options)

    if result.best_move is not None:
        m = result.best_move
        move_str = (
            f"({_sq4_to_coord_str(m.from_sq)})->"
            f"({_sq4_to_coord_str(m.to_sq)})"
        )
    else:
        move_str = None

    out = {
        "agent": agent.label,
        "best_move": move_str,
        "best_score": result.best_score,
        "depth_reached": result.depth_reached,
        "nodes_searched": result.nodes_searched,
        "elapsed_ms": result.elapsed_ms,
        "tt_hits": getattr(result, "tt_hits", 0),
        "tt_size": getattr(result, "tt_size", 0),
    }
    if args.json:
        print(_json.dumps(out, indent=2))
    else:
        print(f"agent: {out['agent']}")
        print(f"best:  {out['best_move']} (score={out['best_score']:.3f})")
        print(f"depth: {out['depth_reached']}  nodes: {out['nodes_searched']}  "
              f"time: {out['elapsed_ms']:.1f}ms")
        if agent.search_options.use_tt:
            print(f"tt:    hits={out['tt_hits']}  size={out['tt_size']}")
    return 0


def cmd_tournament_4d(args: argparse.Namespace) -> int:
    """4D analogue of the 2D `tournament` command.

    Agents are configured via the same agent-spec format. Round-robin
    games play in 4D Board4D positions.

    NOTE: the 4D move generator in pure Python is slow (~250 s for the
    starting position's 2152-move legal set). Realistic tournaments
    will set ``time_budget_ms`` per agent and ``--max-plies`` low.
    """
    import json as _json
    from chess_spectral.engine.tournament.agent_spec import (
        parse_spec, build_agent_4d,
    )
    from chess_spectral.engine.tournament import run_round_robin
    from chess_spectral.spatial_4d.board import Board4D

    if len(args.agent) < 2:
        print("tournament: need at least 2 --agent specs", file=sys.stderr)
        return 2

    if not args.start_fen4:
        print(
            "tournament: --start-fen4 required (4D has no canonical "
            "starting position; pass an explicit FEN4 v1 literal that "
            "every game starts from -- see docs/FEN4_FORMAT.md)",
            file=sys.stderr,
        )
        return 2

    agents = [build_agent_4d(parse_spec(spec)) for spec in args.agent]
    start_fen = args.start_fen4

    def _board_factory():
        return Board4D.from_fen(start_fen)

    result = run_round_robin(
        agents,
        n_games_per_pair=args.n_games_per_pair,
        board_factory=_board_factory,
        max_plies=args.max_plies,
    )

    out = {
        "agents": [a.label for a in agents],
        "n_games_per_pair": args.n_games_per_pair,
        "max_plies": args.max_plies,
        "start_fen4": start_fen,
        "elo": {label: round(rating, 1) for label, rating in result.final_elos.items()},
        "pair_records": {
            f"{a}_vs_{b}": {"wins": w, "losses": l, "draws": d}
            for (a, b), (w, l, d) in result.pair_records.items()
        },
        "elapsed_ms": result.elapsed_ms,
        "games": [
            {
                "white": g.white.label,
                "black": g.black.label,
                "score_white": g.score_white,
                "termination": g.termination,
                "plies": g.plies_played,
                "elapsed_ms": g.elapsed_ms,
            }
            for g in result.games
        ],
    }
    text = _json.dumps(out, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(text)
            fp.write("\n")
        print(f"tournament: wrote {len(result.games)} games to {args.output}",
              file=sys.stderr)
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="chess_spectral_4d.cli",
        description=(
            "CLI for the 4D chess-spectral encoder (B4 symmetry, Z_8^4 "
            "lattice; Oana & Chiru 2026). Mirrors the C `spectral_4d` "
            "binary; encode-fen4 / encode-moves4 / corpus-gen produce "
            "byte-identical output to their C counterparts."
        ),
    )
    # Optional subcommand so bare invocation prints full help, matching
    # the 2D spectral_py CLI.
    sub = ap.add_subparsers(dest="cmd")

    # tables-verify
    p_tv = sub.add_parser(
        "tables-verify",
        help="Run phase-N validation gates (pre-flight before encoding)",
        description=(
            "Run validation gates from each implementation phase. "
            "--phase 1 covers piece mobility on the Z_8^4 lattice and "
            "cross-checks against Oana & Chiru (AppliedMath 6(3):48, "
            "2026) section 3."
        ),
    )
    p_tv.add_argument(
        "--phase",
        choices=("1", "2", "3", "4", "5", "pawn-axis", "all"),
        default="all",
        help=("which phase gate(s) to run (default: all, which also runs "
              "the v1.1.1 pawn-axis orthogonality gate)"),
    )
    p_tv.add_argument(
        "-v", "--verbose", action="store_true",
        help="print per-check details (sample squares, degrees, etc.)",
    )
    p_tv.set_defaults(func=cmd_tables_verify)

    # encode-fen4
    p_fen = sub.add_parser(
        "encode-fen4",
        help="Encode a FEN4 v1 literal to a single-frame v4 .spectralz4",
        description=(
            "Parse a FEN4 v1 placement literal (see docs/FEN4_FORMAT.md), "
            "encode it to 45 056 float32 via encode_4d, and write a "
            "single-frame v4 .spectralz4. Output is byte-identical to the "
            "C binary `spectral_4d encode-fen4`."
        ),
    )
    p_fen.add_argument("--fen4", required=True,
                       help="FEN4 v1 literal, e.g. '4d-fen v1: K@0,0,0,0; "
                            "k@7,7,7,7'")
    p_fen.add_argument("-o", "--output",
                       help="output path; '-' or omitted writes raw bytes "
                            "to stdout (incompatible with -z)")
    p_fen.add_argument("-z", "--compress", action="store_true",
                       help="gzip the output (RFC 1952, mtime=0 for "
                            "deterministic bytes)")
    p_fen.set_defaults(func=cmd_encode_fen4)

    # encode-moves4
    p_mv = sub.add_parser(
        "encode-moves4",
        help="Encode an NDJSON4 ply-log to a v4 .spectralz4",
        description=(
            "Encode an NDJSON4 ply-log (one FEN4 v1 literal per line) to "
            "a v4 .spectralz4. See docs/NDJSON4_FORMAT.md for the schema. "
            "Each line: {ply, fen4, move_from?, move_to?, promo?, flags?}. "
            "Output is decompressed-byte-identical to `spectral_4d encode`."
        ),
    )
    p_mv.add_argument("--moves", required=True,
                      help="path to NDJSON4 ply-log (one FEN4 per line)")
    p_mv.add_argument("-o", "--output",
                      help="output .spectral4 / .spectralz4 path")
    p_mv.add_argument("-z", "--compress", action="store_true",
                      help="gzip the output (RFC 1952, mtime=0)")
    p_mv.add_argument("--start", type=int, default=0,
                      help="skip to ply N (0-indexed) before encoding")
    p_mv.add_argument("--count", type=int, default=0,
                      help="encode at most K plies (0 = no limit)")
    p_mv.set_defaults(func=cmd_encode_moves4)

    # corpus-gen
    p_cor = sub.add_parser(
        "corpus-gen",
        help="Wrap N NDJSON4 ply-logs into a viewer-ready corpus folder",
        description=(
            "Wrap N NDJSON4 ply-logs into a corpus folder mirroring the 2D "
            "`chess-spectral corpus` layout: ndjson/<game>.ndjson, "
            "spectralz/<game>.spectralz4, and a manifest.json with "
            "per-game metadata. Honors --limit to cap processed games."
        ),
    )
    p_cor.add_argument("--games", required=True, nargs="+",
                       help="one or more NDJSON4 ply-log paths")
    p_cor.add_argument("--run-id",
                       help="output folder name under --results-root")
    p_cor.add_argument("--results-root",
                       help="parent directory for the run folder")
    p_cor.add_argument("--limit", type=int, default=None,
                       help="max total games to process (default: no limit)")
    p_cor.set_defaults(func=cmd_corpus_gen)

    # version
    p_ver = sub.add_parser(
        "version",
        help="Print version + format info",
        description=(
            "Print the chess_spectral_4d package version, the .spectralz4 "
            "magic and on-disk version, the encoding dimensionality "
            "(45 056 = 8^4 * 11), and the lattice geometry (n_dimensions=4, "
            "board_dim_side=8). Useful for verifying byte-format parity "
            "against the C `spectral_4d` binary."
        ),
    )
    p_ver.set_defaults(func=cmd_version)

    # search (4D)
    p_search = sub.add_parser(
        "search",
        help="Run §16.2 search at a 4D position",
        description=(
            "Iterative-deepening alpha-beta search on a 4D Board4D. "
            "Mirrors `spectral_py search` with the same agent-spec "
            "syntax. Requires --fen4 (no 4D canonical starting position "
            "yet; see docs/FEN4_FORMAT.md). Per-spec the user can pick "
            "evaluator (material/spectral/qm), depth, time budget, "
            "weights file, and ablations -- the §16's symmetric per-side "
            "configuration surface."
        ),
    )
    p_search.add_argument("--fen4", required=True,
                          help="FEN4 v1 literal of the position to search")
    p_search.add_argument("--agent", required=True, metavar="SPEC",
                          help="agent spec (e.g. 'evaluator=material,depth=2')")
    p_search.add_argument("--json", action="store_true",
                          help="emit machine-readable JSON instead of human summary")
    p_search.set_defaults(func=cmd_search_4d)

    # tournament (4D)
    p_tour = sub.add_parser(
        "tournament",
        help="Run round-robin self-play tournament between 4D agents",
        description=(
            "4D round-robin tournament. Each --agent SPEC produces a "
            "configured engine (white/black are independently spec'd "
            "per pairing); round-robin pits each pair both ways. "
            "Output is JSON with Elo ratings + per-game records.\n\n"
            "Realistic settings: --max-plies 20 and per-agent "
            "time_budget_ms=5000 keep wall time bounded since pure-"
            "Python 4D move generation is slow.\n\n"
            "Requires --start-fen4 (no canonical 4D starting position)."
        ),
    )
    p_tour.add_argument("--agent", required=True, action="append", metavar="SPEC",
                        help="agent spec; repeat for each agent (minimum 2)")
    p_tour.add_argument("--start-fen4", required=True,
                        help="FEN4 v1 literal each game starts from")
    p_tour.add_argument("--n-games-per-pair", type=int, default=2,
                        help="games per pair (default: 2)")
    p_tour.add_argument("--max-plies", type=int, default=20,
                        help="hard cap on plies per game (default: 20; lower "
                             "than 2D's 200 because pure-Python 4D move-gen "
                             "is slow)")
    p_tour.add_argument("-o", "--output",
                        help="write tournament JSON to FILE instead of stdout")
    p_tour.set_defaults(func=cmd_tournament_4d)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "func", None) is None:
        ap.print_help(sys.stderr)
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
