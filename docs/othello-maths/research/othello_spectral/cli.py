"""Command-line entry points for othello_spectral.

Subcommands
-----------
  encode-pgn PGN [--out PATH] [--metadata STR] [--engine E]
             [--fiber F] [--replay-engine R]
      Encode every ply of every game in a PGN corpus to a
      .spectralz binary file (float32 frames, little-endian).
      v0.3.2+: replay uses SheafMoveOperator by default (2.5x
      end-to-end speedup over OthelloBoard; byte-identical output).

  encode-obf OBF [--out PATH]
      Encode a single OBF string and print the 12 channel energies
      (optionally writing the full 768-dim vector as a .spectralz
      single-frame file).

  channels
      Print the 12 channel names + 64-dim slice addresses.

  version
      Print the encoder VERSION, encoding dim, and channel count.

  engine [--engine py|c|auto]
      Diagnose which encoder engine would be selected without
      running an encode.  Respects $OTHELLO_SPECTRAL_ENGINE,
      $OTHELLO_SPECTRAL_BIN, and $OTHELLO_SPECTRAL_DLL.

Environment variables
---------------------
  $OTHELLO_SPECTRAL_ENGINE  -- default engine: py / c / auto
  $OTHELLO_SPECTRAL_BIN     -- path to encode_cli.exe (subprocess fallback)
  $OTHELLO_SPECTRAL_DLL     -- path to othello_spectral.dll (ctypes fast path)

Examples
--------
    cd docs/othello-maths/research

    # Full corpus encode (defaults: C engine, sheaf fiber, sheaf replay)
    python -m othello_spectral.cli encode-pgn \\
        ../dataset/liveothello-2026-APR.pgn \\
        --out ../results/apr_2026.spectralz

    # Force the legacy OthelloBoard replay path for audit
    python -m othello_spectral.cli encode-pgn \\
        ../dataset/liveothello-2026-APR.pgn \\
        --replay-engine othelloboard

    # Single-position channel energies
    python -m othello_spectral.cli encode-obf \\
        '---------------------------OX------XO--------------------------- X;'

    # Introspection subcommands
    python -m othello_spectral.cli channels
    python -m othello_spectral.cli version
    python -m othello_spectral.cli engine --engine auto
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

# research/ on path for flat-module imports
_RESEARCH_DIR = Path(__file__).resolve().parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from othello_spectral import (  # noqa: E402
    CHANNEL_NAMES, ENCODING_DIM, VERSION, channel_energies, encode_768,
)
from othello_spectral.frame import Frame, write_file  # noqa: E402
from othello_spectral.runtime import (  # noqa: E402
    default_engine, encode_768_c_ctypes_batch, encode_768_c_stream,
    find_c_binary, find_c_dll, resolve_engine,
)


def _obf_to_state(obf: str) -> np.ndarray:
    """Convert an OBF string to a length-64 world-frame signal.

    OBF encodes the 64-char board from a1 (index 0) to h8 (index 63):
      '-' empty, 'X' black, 'O' white.
    Side-to-move is the 66th char ('X' or 'O'); we ignore it since the
    encoder operates on the world-frame signal.  A standalone
    sanity check: len(obf) == 66 (64 + ' ' + side + ';').
    """
    if len(obf) < 66 or obf[64] != " " or obf[65] not in "XO":
        raise ValueError(f"bad OBF string: {obf!r}")
    state = np.zeros(64, dtype=int)
    for i, ch in enumerate(obf[:64]):
        if ch == "X":
            state[i] = 1
        elif ch == "O":
            state[i] = -1
        elif ch == "-":
            state[i] = 0
        else:
            raise ValueError(f"bad OBF char {ch!r} at pos {i}")
    return state


def cmd_channels(_args) -> int:
    for i, name in enumerate(CHANNEL_NAMES):
        dim_lo = i * 64
        print(f"  {i:2d}  dims [{dim_lo:3d}:{dim_lo + 64:3d})  {name}")
    return 0


def cmd_version(_args) -> int:
    print(f"othello_spectral VERSION = {VERSION}")
    print(f"encoding dim = {ENCODING_DIM}")
    print(f"n channels   = {len(CHANNEL_NAMES)}")
    return 0


def cmd_encode_obf(args) -> int:
    state = _obf_to_state(args.obf)
    enc = encode_768(state)
    en = channel_energies(enc)
    print(f"obf: {args.obf}")
    print(f"||enc||^2 = {float(np.dot(enc, enc)):.6f}")
    print("channel energies:")
    for i, name in enumerate(CHANNEL_NAMES):
        print(f"  {i:2d}  {name:18s}  {en[name]:+12.6f}")
    if args.out:
        out = Path(args.out)
        write_file(
            out, [Frame(data=enc, ply=0)],
            metadata=f"othello_spectral v{VERSION} obf_single_frame",
        )
        print(f"wrote {out}")
    return 0


def cmd_encode_pgn(args) -> int:
    # Lazy import — othello_pgn_loader pulls numpy + othello_utils
    import othello_pgn_loader as pgn_loader
    from othello_utils import BLACK, OthelloBoard
    pgn_path = Path(args.pgn)
    if not pgn_path.exists():
        print(f"PGN not found: {pgn_path}", file=sys.stderr)
        return 2
    out_path = Path(
        args.out or (
            pgn_path.with_suffix(".spectralz").name
        )
    )
    if args.out is None:
        out_path = pgn_path.parent / out_path.name

    # Engine dispatch.  Both rank2 and sheaf fibers supported in C
    # since v0.3.0; the C engine may still fall back if the DLL /
    # binary doesn't expose encode_768_v2 (older builds).
    fiber_mode = getattr(args, "fiber", "sheaf")
    replay_engine = getattr(args, "replay_engine", "sheaf")
    requested_engine = args.engine or default_engine()
    try:
        engine, c_binary = resolve_engine(requested_engine)
    except FileNotFoundError as exc:
        print(f"engine resolution failed: {exc}", file=sys.stderr)
        return 4
    print(
        f"encoder engine: {engine}  fiber: {fiber_mode}  "
        f"replay: {replay_engine}"
        + (f"  binary={c_binary}" if c_binary else "")
    )

    games = pgn_loader.parse_pgn_file(pgn_path)
    print(f"parsed {len(games)} games from {pgn_path.name}")

    # First pass: replay all games to collect states in memory.
    # Default path uses SheafMoveOperator (~8x faster than OthelloBoard
    # on clean corpora).  Byte-for-byte parity between the two is
    # guaranteed by test_move_operator.py::test_random_game_parity.
    replayed: list[list] = []  # one list of state arrays per game
    failures = 0
    if replay_engine == "sheaf":
        from othello_spectral.move_operator import SheafMoveOperator
        _op = SheafMoveOperator()
        _replay_fn = lambda mvs: pgn_loader.replay_sheaf(mvs, _op)
    else:
        _replay_fn = pgn_loader.replay
    t_replay_start = time.time()
    for gi, g in enumerate(games):
        try:
            _, states, _ = _replay_fn(g["moves"])
        except Exception as exc:
            print(
                f"  game {gi}: replay failed: {exc}",
                file=sys.stderr,
            )
            failures += 1
            replayed.append([])
            continue
        replayed.append(list(states))
    t_replay = time.time() - t_replay_start
    print(
        f"replay: {t_replay:.2f}s for {len(games)} games "
        f"({len(games) - failures}/{len(games)} clean, "
        f"engine={replay_engine})"
    )

    # Second pass: encode every state.  Engine dispatch here.
    all_states: list = []
    game_lengths: list[int] = []
    for states in replayed:
        game_lengths.append(len(states))
        all_states.extend(states)

    t0 = time.time()
    # When engine is 'c', prefer the ctypes DLL path if available
    # (skip subprocess overhead).  Fall back to subprocess binary
    # if only exe is present.
    used_path = engine
    if engine == "c":
        dll = None
        try:
            dll = find_c_dll()
        except FileNotFoundError:
            dll = None
        if dll is not None:
            encs = encode_768_c_ctypes_batch(
                all_states, fiber_mode=fiber_mode,
            )
            used_path = f"c (ctypes: {dll.name}, fiber={fiber_mode})"
        else:
            encs = encode_768_c_stream(
                all_states, c_binary, fiber_mode=fiber_mode,
            )
            used_path = (
                f"c (subprocess: {c_binary.name}, fiber={fiber_mode})"
            )
    else:
        encs = [encode_768(st, fiber_mode=fiber_mode) for st in all_states]
        used_path = f"py (fiber={fiber_mode})"
    print(
        f"encoded {len(encs)} states in {time.time() - t0:.1f}s "
        f"(engine={used_path})"
    )

    # Reassemble frames with a monotone ply counter across games.
    frames: list[Frame] = []
    ply = 0
    offset = 0
    for L in game_lengths:
        for i in range(L):
            frames.append(Frame(data=encs[offset + i], ply=ply))
            ply += 1
        offset += L

    metadata = (
        args.metadata or
        f"othello_spectral v{VERSION} corpus={pgn_path.name} "
        f"games={len(games) - failures} engine={engine}"
    )
    write_file(out_path, frames, metadata=metadata)
    print(
        f"wrote {out_path}  ({len(frames)} frames, "
        f"{len(games) - failures}/{len(games)} games)"
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="othello_spectral",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pver = sub.add_parser(
        "version",
        help="Print encoder VERSION + dim + channel count",
        description="Print the current encoder VERSION (semver), the "
                    "encoding dimension (768 at v0.3.x), and the "
                    "number of channels (12).  Useful for smoke-check "
                    "that the installed package matches the corpus "
                    "you're about to re-encode.",
    )
    pver.set_defaults(func=cmd_version)

    pchan = sub.add_parser(
        "channels",
        help="List the 12 channel names + dim ranges",
        description="Dump the full channel layout (index, 64-dim slice, "
                    "name).  Channels 0-4: D4-Z2 '-' irreps on the "
                    "magnetisation field s.  Channels 5-9: D4 irreps "
                    "on the occupation field s^2.  Channels 10-11: "
                    "sheaf-pending fiber (black / white) under "
                    "fiber_mode='sheaf' (default, v0.3.0+).",
    )
    pchan.set_defaults(func=cmd_channels)

    pobf = sub.add_parser(
        "encode-obf",
        help="Encode a single OBF position and print channel energies",
        description="Encode one OBF-format board string to a 768-dim "
                    "vector and print the 12 per-channel squared norms. "
                    "OBF = 64 cells of {-, X, O} + space + side-to-move "
                    "(X/O) + ';'.  Example: "
                    "'---------------------------OX------XO----"
                    "---------------------- X;' is the starting "
                    "position with black to move.  The encoder "
                    "operates on the world-frame signal so side-to-"
                    "move is not part of the encoding.",
    )
    pobf.add_argument("obf", help="OBF position string (66 chars)")
    pobf.add_argument(
        "--out", type=str, default=None,
        help="Optional .spectralz output path.  Writes a single-frame "
             "file (header + one 768-dim float32 vector) at the given "
             "path, suitable for downstream spectralz analysis tooling.",
    )
    pobf.set_defaults(func=cmd_encode_obf)

    ppgn = sub.add_parser(
        "encode-pgn",
        help="Encode every state in a PGN corpus to a .spectralz file",
    )
    ppgn.add_argument("pgn", help="Path to a PGN corpus file")
    ppgn.add_argument(
        "--out", type=str, default=None,
        help="Output .spectralz path.  Default: alongside the PGN "
             "with extension swapped to .spectralz.",
    )
    ppgn.add_argument(
        "--metadata", type=str, default=None,
        help="Free-form metadata string written into the file header "
             "(232 bytes max).",
    )
    ppgn.add_argument(
        "--engine", choices=["py", "c", "auto"], default=None,
        help="Encoder engine (which implementation does the 768-dim "
             "encode_768 projection).  'py' = Python reference "
             "(always works, ~25x slower); 'c' = the compiled C "
             "binary/DLL (rank2 + sheaf fibers both supported at "
             "v0.3.1+); 'auto' = prefer 'c' if available AND verified "
             "via version+smoke check, else fall back to 'py'.  "
             "Default: value of $OTHELLO_SPECTRAL_ENGINE, or 'auto'. "
             "Use the 'engine' subcommand to inspect the resolved "
             "path without running an encode.",
    )
    ppgn.add_argument(
        "--fiber", choices=["sheaf", "rank2"], default="sheaf",
        help="Fiber mode for channels 10-11.  'sheaf' (default, "
             "v0.3.0+): per-cell R3_PENDING bracket counts from the "
             "faithful sheaf -- state-dependent, captures bracket "
             "potential (correlates at rho=-0.447 w/ edax d=20 vs "
             "rho=-0.319 for a1_minus).  'rank2' (legacy v0.2.0): "
             "orbit Laplacians applied to s, state-linear.  Both are "
             "available in py + c engines since v0.3.1.",
    )
    ppgn.add_argument(
        "--replay-engine", choices=["sheaf", "othelloboard"],
        default="sheaf",
        help="Move-replay backend.  'sheaf' (default, v0.3.2+): use "
             "othello_spectral.move_operator.SheafMoveOperator.  "
             "Walks only the 8 rays from the target cell per ply "
             "(~8x faster than 'othelloboard' on APR 2026: 0.81s vs "
             "6.67s / 414 games).  Byte-for-byte parity with "
             "OthelloBoard.play() is proven by "
             "test_move_operator.py::test_random_game_parity, so "
             "encoded output is identical.  'othelloboard': legacy "
             "OthelloBoard.legal_moves()+play() -- use for audit / "
             "debugging or if you suspect operator divergence.",
    )
    ppgn.set_defaults(func=cmd_encode_pgn)

    # Engine-diagnostic subcommand — prints which engine would be
    # selected under the current environment + CLI overrides.
    peng = sub.add_parser(
        "engine",
        help="Diagnose which encoder engine would be selected now",
        description="Resolve and print the encoder engine that "
                    "encode-pgn / encode-obf would use under the "
                    "current environment without running an encode. "
                    "Shows the requested engine (from CLI or "
                    "$OTHELLO_SPECTRAL_ENGINE), the resolved engine "
                    "after version+smoke verification, the "
                    "subprocess binary path ($OTHELLO_SPECTRAL_BIN), "
                    "and the ctypes DLL path ($OTHELLO_SPECTRAL_DLL). "
                    "Exit code 4 if 'c' was requested but no verified "
                    "binary/DLL is available.",
    )
    peng.add_argument(
        "--engine", choices=["py", "c", "auto"], default=None,
        help="Override the engine choice for this diagnostic run. "
             "Same semantics as encode-pgn's --engine flag.  Omit "
             "to use $OTHELLO_SPECTRAL_ENGINE (or 'auto' if unset).",
    )

    def cmd_engine(args):
        req = args.engine or default_engine()
        try:
            e, b = resolve_engine(req)
        except FileNotFoundError as exc:
            print(f"requested: {req}")
            print(f"error: {exc}")
            return 4
        dll = None
        try:
            dll = find_c_dll()
        except FileNotFoundError as exc:
            print(f"DLL env override points to missing file: {exc}")
        print(f"requested:        {req}")
        print(f"resolved engine:  {e}")
        print(f"subprocess binary: {b or '(none)'}")
        print(f"ctypes DLL:       {dll or '(none)'}")
        print(f"default_from_env: {default_engine()}")
        if e == "c" and dll is not None:
            print("  -> 'c' will use ctypes DLL (fast path)")
        elif e == "c" and b is not None:
            print("  -> 'c' will use subprocess binary (slow path)")
        return 0
    peng.set_defaults(func=cmd_engine)

    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
