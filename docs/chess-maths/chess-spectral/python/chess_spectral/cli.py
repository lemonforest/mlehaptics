#!/usr/bin/env python3
"""
spectral_py — Python CLI mirror of the C `spectral` binary.

Commands (symmetric with the C side):
    csv        <file.spectral[z]> [-o out.csv]
               Read a .spectral or .spectralz and emit the chat-friendly
               CSV (17 columns: inter-frame metrics + channel energies).

    encode     { -i game.ndjson | --pgn game.pgn | --url URL }
               [--pgn-start N] [--pgn-count K] -o game.spectral[z] [-z]
               Encode a PGN / NDJSON / URL stream into a v2 .spectral
               file. With --pgn/--url, auto-pipes through pgn_bridge.py
               (supports --pgn-start / --pgn-count for multi-game
               slicing). With -z, writes gzip-compressed output.

    encode-fen --fen "<fen>" [-o single.spectral]
               Encode a single FEN string to a one-ply .spectral file.

    corpus     --pgn PATH [PATH ...] [--run-id NAME] [--results-root DIR]
               Wrap one or more local PGNs as a corpus-layout folder
               consumable by the chess-maths-viewer (web app
               that expects manifest.json + corpus_index.csv +
               pgn/ ndjson/ spectralz/ subdirs). Equivalent to running
               run_corpus_sweep.py for a fetched corpus, but on a PGN
               you already have on disk.

    version    Print version / format info.

Not yet implemented: query, analyze, heatmap, compare.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Iterable, Iterator, TextIO

import numpy as np

from chess_spectral import (
    encode_640, normalize_pos, Frame, write_file, write_csv,
    FILE_VERSION, ENCODING_DIM, fen_to_pos, uci_to_indices,
    process_game, extract_features,
    parse_local_pgn, iter_local_pgn_games,
    write_index_csv, write_summary_md,
)

VERSION = "0.1.0-py"

# Paths for the `corpus` subcommand. This module lives at
# <repo>/docs/chess-maths/chess-spectral/python/chess_spectral/cli.py, so:
#   bridge  = <repo>/docs/chess-maths/chess-spectral/bridge/pgn_bridge.py
#   results = <repo>/docs/chess-maths/results/
HERE = os.path.dirname(os.path.abspath(__file__))
_BRIDGE_SCRIPT = os.path.abspath(os.path.join(
    HERE, os.pardir, os.pardir, "bridge", "pgn_bridge.py"))
_DEFAULT_RESULTS_ROOT = os.path.abspath(os.path.join(
    HERE, os.pardir, os.pardir, os.pardir, "results"))


def _find_c_binary() -> str | None:
    """Locate the native spectral binary built from chess-spectral/src/.
    Checks (1) CS_SPECTRAL_BIN env var, (2) standard CMake Release/Debug
    output paths under chess-spectral/build/. Returns None if no binary
    is found — callers should fall back to the Python encoder."""
    env = os.environ.get("CS_SPECTRAL_BIN")
    if env and os.path.isfile(env):
        return env
    build_root = os.path.abspath(os.path.join(
        HERE, os.pardir, os.pardir, "build"))
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = os.path.join(build_root, sub, f"spectral{suffix}")
        if os.path.isfile(cand):
            return cand
    return None


# ─── Filename derivation helpers ────────────────────────────────────────
#
# Always use os.path.splitext (or pathlib.Path.stem), NEVER str.split('.')
# — the latter truncates at the FIRST dot, which mangles names like
# "lichess_pgn_2026.04.14_Fabsid_vs_Qvagmire.VEYpgB14.pgn" into
# "lichess_pgn_2026".

def _strip_known_ext(path: str) -> str:
    """Strip a single recognised extension from `path`, preserving any
    interior dots. Recognises both single-dot (`.pgn`, `.csv`) and
    compound (`.spectral.gz`, `.spectralz`) extensions.
    """
    known = (".spectralz", ".spectral.gz", ".spectral",
             ".ndjson", ".pgn", ".csv", ".json")
    low = path.lower()
    for ext in known:
        if low.endswith(ext):
            return path[: -len(ext)]
    # Fallback: strip exactly one extension using splitext (which is
    # correct for multi-dot names — it splits on the LAST dot).
    return os.path.splitext(path)[0]


def _auto_output(input_path: str, new_ext: str) -> str:
    """Derive an output filename by replacing the extension on
    `input_path` with `new_ext` (which may be multi-part like
    '.spectralz'). Keeps the directory intact."""
    return _strip_known_ext(input_path) + new_ext


def _sibling_if_exists(input_path: str, ext: str) -> str | None:
    """Return `basename(input) + ext` if that file exists on disk, else
    None. Used for auto-picking a --meta NDJSON next to a .spectralz."""
    candidate = _auto_output(input_path, ext)
    return candidate if os.path.isfile(candidate) else None


def cmd_csv(args: argparse.Namespace) -> int:
    # Default output: <input>.csv  (preserves multi-dot basenames).
    if args.output:
        out = args.output
    elif args.stdout:
        out = "-"
    else:
        out = _auto_output(args.input, ".csv")

    # Default meta: <input>.ndjson if it exists alongside the .spectral[z].
    # Skipped when the user explicitly passed --no-meta.
    meta = args.meta
    if meta is None and not args.no_meta:
        meta = _sibling_if_exists(args.input, ".ndjson")

    try:
        n = write_csv(args.input, out, meta_path=meta)
    except (IOError, ValueError) as e:
        print(f"csv: {e}", file=sys.stderr)
        return 3
    suffix = "" if out == "-" else f" to {out}"
    meta_tag = f" (+meta from {meta})" if meta else ""
    print(f"csv: wrote {n} rows from {args.input}{suffix}{meta_tag}",
          file=sys.stderr)
    return 0


def _iter_ndjson_stream(stream: TextIO, source_label: str) -> Iterator[Frame]:
    """Stream per-ply records from a text iterable produced by
    pgn_bridge.py and yield encoded Frames. Accepts all three
    schemas emitted by the bridge over time:

      - v2 ndjson-fen-v2: fen/uci/san with move_from/move_to preset
        and optional nag/eval/clk/comment fields (all ignored here —
        the encoder only needs the position).
      - v1 ndjson-fen: fen/uci/san only; move indices derived from uci.
      - legacy: pos (string-keyed dict) + move_from/move_to.

    `type:"game_header"` records and the top-level bridge header are
    skipped. `source_label` is used only for error messages."""
    for line_no, line in enumerate(stream, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{source_label}:{line_no}: bad JSON ({e})") from e
        if rec.get("type") == "game_header":
            continue

        pos = rec.get("pos")
        fen = rec.get("fen")
        if pos is None and fen is None:
            continue  # top-level header or unrelated record
        pos_dict = normalize_pos(pos) if pos is not None \
            else fen_to_pos(fen)

        if "move_from" in rec:
            move_from = int(rec["move_from"]) & 0xFF
            move_to = int(rec.get("move_to", 0xFF)) & 0xFF
            move_promo = int(rec.get("move_promo", 0)) & 0xFF
        else:
            uci = rec.get("uci") or ""
            move_from, move_to, move_promo = uci_to_indices(uci)
        move_flags = int(rec.get("move_flags", 0)) & 0xFF

        enc = encode_640(pos_dict)
        yield Frame(
            encoding=enc.astype(np.float32),
            ply=int(rec.get("ply", 0)),
            move_from=move_from,
            move_to=move_to,
            move_promo=move_promo,
            move_flags=move_flags,
        )


def _iter_ndjson_frames(path: str) -> Iterator[Frame]:
    """Open an NDJSON file and yield encoded Frames. See
    `_iter_ndjson_stream` for schema details."""
    with open(path, "r", encoding="utf-8") as f:
        yield from _iter_ndjson_stream(f, path)


def _spawn_bridge(pgn: str | None, url: str | None,
                  pgn_start: int, pgn_count: int):
    """Launch pgn_bridge.py as a subprocess and return a (Popen, stdout)
    pair. stdout is a text-mode file-like stream of NDJSON lines that
    the caller can iterate. The caller is responsible for closing the
    stream and checking Popen.wait()."""
    if pgn is None and url is None:
        raise ValueError("_spawn_bridge requires --pgn or --url")
    cmd = [sys.executable, _BRIDGE_SCRIPT]
    if url:
        cmd.extend(["--url", url])
    else:
        cmd.extend(["--input", pgn])
    if pgn_start > 0 or pgn_count > 0:
        cmd.extend(["--start-game", str(max(0, pgn_start)),
                    "--max-games",  str(max(0, pgn_count))])
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,  # line-buffered
    )
    return proc, proc.stdout


def cmd_encode(args: argparse.Namespace) -> int:
    sources = [bool(args.input), bool(args.pgn), bool(args.url)]
    if sum(sources) == 0:
        print("encode: one of -i/--input, --pgn, --url required",
              file=sys.stderr)
        return 2
    if sum(sources) > 1:
        print("encode: -i/--input, --pgn, and --url are mutually exclusive",
              file=sys.stderr)
        return 2

    pgn_start = int(getattr(args, "pgn_start", 0) or 0)
    pgn_count = int(getattr(args, "pgn_count", 0) or 0)
    if pgn_start < 0 or pgn_count < 0:
        print("encode: --pgn-start/--pgn-count must be >= 0", file=sys.stderr)
        return 2
    if (pgn_start > 0 or pgn_count > 0) and args.input:
        print("encode: --pgn-start/--pgn-count only apply with --pgn/--url "
              "(NDJSON input is sliced at the bridge step)", file=sys.stderr)
        return 2

    # Auto-derive output from whichever source is set.
    src_for_name = args.input or args.pgn or args.url or "out"
    output = args.output or _auto_output(
        src_for_name,
        ".spectralz" if args.compress else ".spectral",
    )

    proc = None
    try:
        if args.input:
            frames = _iter_ndjson_frames(args.input)
        else:
            proc, stream = _spawn_bridge(args.pgn, args.url,
                                         pgn_start, pgn_count)
            frames = _iter_ndjson_stream(stream, args.pgn or args.url)
        n = write_file(output, frames, compress=args.compress)
    except (IOError, ValueError) as e:
        print(f"encode: {e}", file=sys.stderr)
        if proc is not None:
            proc.kill()
            proc.wait()
        return 3
    finally:
        if proc is not None and proc.stdout is not None:
            proc.stdout.close()

    if proc is not None:
        rc = proc.wait()
        if rc != 0:
            print(f"encode: pgn_bridge.py exited with status {rc}",
                  file=sys.stderr)
            return 3

    tag = "(gzip)" if args.compress else ""
    print(f"encode: wrote {n} frames to {output} {tag}".rstrip(),
          file=sys.stderr)
    return 0


def cmd_encode_fen(args: argparse.Namespace) -> int:
    pos = fen_to_pos(args.fen)
    enc = encode_640(pos)
    fr = Frame(encoding=enc.astype(np.float32), ply=0)
    out = args.output or "single.spectral"
    # Compress if -z given explicitly, OR if output path ends .spectralz.
    compress = bool(args.compress) or out.endswith(".spectralz")
    try:
        write_file(out, [fr], compress=compress)
    except (IOError, ValueError) as e:
        print(f"encode-fen: {e}", file=sys.stderr)
        return 3
    tag = " (gzip)" if compress else ""
    print(f"encode-fen: wrote 1 frame to {out}{tag}", file=sys.stderr)
    return 0


def cmd_corpus(args: argparse.Namespace) -> int:
    """Wrap one or more local PGNs into a corpus-layout folder for the
    chess-maths-viewer. Produces the same manifest.json /
    corpus_index.csv / corpus_summary.md / pgn/ ndjson/ spectralz/
    layout as run_corpus_sweep.py, but for PGNs already on disk."""
    import datetime as _dt
    import time as _time
    from pathlib import Path as _Path

    pgn_paths = [_Path(p) for p in args.pgn]
    for p in pgn_paths:
        if not p.is_file():
            print(f"corpus: not a file: {p}", file=sys.stderr)
            return 2

    if args.run_id:
        run_id = args.run_id
    elif len(pgn_paths) == 1:
        run_id = f"single_{_strip_known_ext(pgn_paths[0].name)}"
    else:
        today = _dt.date.today().isoformat()
        run_id = f"local_N{len(pgn_paths)}_{today}"

    results_root = _Path(args.results_root or _DEFAULT_RESULTS_ROOT)
    run_dir = results_root / run_id
    for sub in ("pgn", "ndjson", "spectralz"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    print(f"corpus: run_id = {run_id}", file=sys.stderr)
    print(f"corpus: output = {run_dir}", file=sys.stderr)
    print(f"corpus: games  = {len(pgn_paths)}", file=sys.stderr)

    t0 = _time.time()
    bridge_script = _Path(_BRIDGE_SCRIPT)
    encoder_script = _Path(os.path.abspath(__file__))

    encoder_binary: _Path | None = None
    if getattr(args, "encoder", "py") == "c":
        c_bin = _find_c_binary()
        if c_bin is None:
            print("corpus: --encoder c requested but no spectral binary "
                  "found (set CS_SPECTRAL_BIN or build "
                  "chess-spectral/build/Release/spectral)",
                  file=sys.stderr)
            return 4
        encoder_binary = _Path(c_bin)
        print(f"corpus: encoder = c ({c_bin})", file=sys.stderr)
    else:
        print("corpus: encoder = py (reference)", file=sys.stderr)

    rows: list = []
    n_encoded = 0
    n_errors = 0
    idx = 0
    limit = getattr(args, "limit", None)
    stop = False
    for p in pgn_paths:
        if stop:
            break
        for game in iter_local_pgn_games(p):
            idx += 1
            if limit is not None and idx > limit:
                idx -= 1
                stop = True
                break
            print(f"corpus: [{idx}] {p.name} — "
                  f"{game['headers'].get('White','?')} vs "
                  f"{game['headers'].get('Black','?')}",
                  file=sys.stderr)
            entry = process_game(
                game, run_dir, idx, bridge_script, encoder_script,
                encoder_binary=encoder_binary,
            )
            if "error" in entry:
                n_errors += 1
                print(f"corpus:   error: {entry['error']}",
                      file=sys.stderr)
                rows.append(entry)
                continue
            try:
                entry.update(extract_features(
                    run_dir / entry["spectralz"],
                    run_dir / entry["ndjson"],
                ))
                n_encoded += 1
            except Exception as e:  # noqa: BLE001
                entry["error"] = f"features: {e}"
                n_errors += 1
                print(f"corpus:   feature extraction failed: {e}",
                      file=sys.stderr)
            rows.append(entry)

    elapsed_s = _time.time() - t0

    n_fetched = idx
    write_index_csv(rows, run_dir / "corpus_index.csv", run_id)
    write_summary_md(
        rows, run_dir / "corpus_summary.md",
        run_id, elapsed_s,
        n_requested=n_fetched, n_fetched=n_fetched,
        n_encoded=n_encoded, n_errors=n_errors,
    )

    manifest = {
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "run_id":        run_id,
        "source":        "local_pgn",
        "fetch_params":  {
            "pgn_paths": [str(p) for p in pgn_paths],
            "limit":     limit,
            "encoder":   "c" if encoder_binary else "py",
        },
        "tool_versions": {
            "python":  sys.version.split()[0],
            "bridge":  str(bridge_script).replace("\\", "/"),
            "encoder": str(encoder_script).replace("\\", "/"),
        },
        "aggregates": {
            "n_requested": n_fetched,
            "n_fetched":   n_fetched,
            "n_encoded":   n_encoded,
            "n_errors":    n_errors,
            "wall_time_s": round(elapsed_s, 2),
        },
        "games": rows,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"corpus: wrote {n_encoded}/{n_fetched} games to {run_dir}",
          file=sys.stderr)
    return 0 if n_errors == 0 else 3


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"spectral_py {VERSION}")
    print(f"  file format v{FILE_VERSION}  encoding_dim {ENCODING_DIM}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="spectral_py",
        description="Python mirror of the C `spectral` CLI.",
    )
    # Not required=True — we want to show full help when the user runs
    # `python spectral_py.py` with no args, rather than a terse error.
    sub = ap.add_subparsers(dest="cmd")

    p_csv = sub.add_parser("csv", help="Export .spectral[z] to CSV")
    p_csv.add_argument("input", help="game.spectral or game.spectralz")
    p_csv.add_argument("-o", "--output",
                       help="output .csv path (default: <input>.csv)")
    p_csv.add_argument("--stdout", action="store_true",
                       help="write CSV to stdout instead of a file")
    p_csv.add_argument("--meta", metavar="NDJSON",
                       help="pgn_bridge NDJSON to merge eval/clk/nag columns "
                            "(default: auto-detect <input>.ndjson if present)")
    p_csv.add_argument("--no-meta", action="store_true",
                       help="disable auto-detection of sibling NDJSON")
    p_csv.set_defaults(func=cmd_csv)

    p_enc = sub.add_parser(
        "encode",
        help="Encode PGN / NDJSON / URL → .spectral[z] "
             "(mirrors the C `spectral encode` CLI)",
    )
    p_enc.add_argument("-i", "--input",
                       help="pre-produced NDJSON (from pgn_bridge.py)")
    p_enc.add_argument("--pgn",
                       help="PGN file path; auto-pipes through pgn_bridge.py")
    p_enc.add_argument("-u", "--url",
                       help="URL returning PGN text; auto-pipes through "
                            "pgn_bridge.py (lichess / chess.com export)")
    p_enc.add_argument("--pgn-start", type=int, default=0,
                       help="With --pgn/--url: skip to game N (0-indexed) "
                            "before encoding. Combine with --pgn-count to "
                            "slice a window.")
    p_enc.add_argument("--pgn-count", type=int, default=0,
                       help="With --pgn/--url: encode at most K games "
                            "starting at --pgn-start (0 = no limit)")
    p_enc.add_argument("-o", "--output",
                       help="output path (default: <input>.spectralz with -z, "
                            "else <input>.spectral)")
    p_enc.add_argument("-z", "--compress", action="store_true",
                       help="gzip the output in place")
    p_enc.set_defaults(func=cmd_encode)

    p_fen = sub.add_parser("encode-fen", help="Encode single FEN → 1-frame file")
    p_fen.add_argument("--fen", required=True, help="FEN string")
    p_fen.add_argument("-o", "--output", help="output path (default single.spectral)")
    p_fen.add_argument("-z", "--compress", action="store_true",
                       help="gzip the output (inferred from .spectralz ext otherwise)")
    p_fen.set_defaults(func=cmd_encode_fen)

    p_cor = sub.add_parser(
        "corpus",
        help="Wrap a local PGN into a viewer-ready corpus folder",
        description=(
            "Wrap a single local PGN file into the corpus-layout folder "
            "expected by chess-maths-viewer "
            "(https://lemonforest.github.io/chess-maths-viewer/). "
            "Produces manifest.json + corpus_index.csv + corpus_summary.md "
            "alongside pgn/, ndjson/, and spectralz/ subdirs — the same "
            "shape as run_corpus_sweep.py output, but for a PGN you "
            "already have on disk. Archive the run folder (e.g. `7z a "
            "run.7z <run-dir>`) and feed the archive to the viewer."
        ),
    )
    p_cor.add_argument("--pgn", required=True, nargs="+",
                       help="one or more PGN file paths; each file may "
                            "contain multiple games (all are ingested)")
    p_cor.add_argument("--limit", type=int, default=None,
                       help="max total games to process across all --pgn "
                            "files (default: no limit)")
    p_cor.add_argument("--encoder", choices=("py", "c"), default="py",
                       help="NDJSON→.spectralz backend: 'py' = Python "
                            "reference (default, trust); 'c' = native "
                            "binary ~38x faster, byte-identical output "
                            "(requires chess-spectral/build/Release/"
                            "spectral or $CS_SPECTRAL_BIN)")
    p_cor.add_argument("--run-id",
                       help="output folder name under --results-root "
                            "(default: single_<pgn-stem>)")
    p_cor.add_argument("--results-root",
                       help=f"parent directory for the run folder "
                            f"(default: {_DEFAULT_RESULTS_ROOT})")
    p_cor.set_defaults(func=cmd_corpus)

    p_ver = sub.add_parser("version", help="Print version info")
    p_ver.set_defaults(func=cmd_version)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "cmd", None):
        ap.print_help(sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
