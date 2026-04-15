#!/usr/bin/env python3
"""
spectral_py — Python CLI mirror of the C `spectral` binary.

Commands (symmetric with the C side):
    csv        <file.spectral[z]> [-o out.csv]
               Read a .spectral or .spectralz and emit the chat-friendly
               CSV (17 columns: inter-frame metrics + channel energies).

    encode     -i game.ndjson -o game.spectral[z] [-z]
               Encode an NDJSON game (from pgn_bridge.py) into a v2
               .spectral file. With -z, writes gzip-compressed output.

    encode-fen --fen "<fen>" [-o single.spectral]
               Encode a single FEN string to a one-ply .spectral file.

    version    Print version / format info.

Not yet implemented: query, analyze, heatmap, compare.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Iterable, Iterator

import numpy as np

# Make `chess_spectral` importable when run as a script from any cwd.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from chess_spectral import (  # noqa: E402
    encode_640, normalize_pos, Frame, write_file, write_csv,
    FILE_VERSION, ENCODING_DIM, fen_to_pos, uci_to_indices,
)

VERSION = "0.1.0-py"


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


def _iter_ndjson_frames(path: str) -> Iterator[Frame]:
    """Stream per-ply records from an NDJSON file produced by
    pgn_bridge.py and yield encoded Frames. Accepts all three
    schemas emitted by the bridge over time:

      - v2 ndjson-fen-v2: fen/uci/san with move_from/move_to preset
        and optional nag/eval/clk/comment fields (all ignored here —
        the encoder only needs the position).
      - v1 ndjson-fen: fen/uci/san only; move indices derived from uci.
      - legacy: pos (string-keyed dict) + move_from/move_to.

    `type:"game_header"` records and the top-level bridge header are
    skipped."""
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: bad JSON ({e})") from e
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


def cmd_encode(args: argparse.Namespace) -> int:
    if not args.input:
        print("encode: -i <file.ndjson> required", file=sys.stderr)
        return 2
    # Auto-derive output: <input-basename>.spectralz (with -z) or .spectral.
    # Preserves multi-dot basenames via _strip_known_ext.
    output = args.output or _auto_output(
        args.input,
        ".spectralz" if args.compress else ".spectral",
    )
    try:
        n = write_file(
            output,
            _iter_ndjson_frames(args.input),
            compress=args.compress,
        )
    except (IOError, ValueError) as e:
        print(f"encode: {e}", file=sys.stderr)
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

    p_enc = sub.add_parser("encode", help="Encode NDJSON game → .spectral[z]")
    p_enc.add_argument("-i", "--input", required=True,
                       help="game.ndjson (from pgn_bridge.py)")
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
