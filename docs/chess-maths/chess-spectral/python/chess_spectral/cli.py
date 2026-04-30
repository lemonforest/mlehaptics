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

    compare    <a.spectral[z]> <b.spectral[z]>
               Cosine-similarity report between two .spectral files.

    query      <file.spectral[z]> --ply N
               Print 10-channel breakdown at ply N.

    heatmap    <file.spectral[z]> --ply N --channel A1
               ANSI 8x8 heatmap of one channel at one ply.

    analyze    <file.spectral[z]>
               Per-game peak / drop / crisis ply (JSON; mirrors C output).

    export     <file.spectral[z]> [-o out.json]
               Dump frames to JSON for the web viewer.

    version    Print version / format info.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Iterable, Iterator, TextIO

# Windows console: default cp1252 cannot encode the em-dash, arrow,
# and box-drawing glyphs used in this CLI's help text and status
# output. Reconfigure stdout/stderr to UTF-8 so `--help` renders on
# any platform.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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


def _find_native_binary(name: str, env_var: str) -> str | None:
    """Locate a native binary by name. Search order (v1.2.4):
      (1) ``$<env_var>`` environment variable (if set and is a file)
      (2) wheel-bundled location: ``<package>/_native/<name>{.exe}``
          (populated by scikit-build-core when building the wheel)
      (3) repo-build paths: ``<repo>/build/{Release,Debug}/<name>{.exe}``
          (developer workflow)

    Returns None if the binary is not found in any of those locations.
    Callers are expected to fall back to the Python implementation."""
    env = os.environ.get(env_var)
    if env and os.path.isfile(env):
        return env
    suffix = ".exe" if os.name == "nt" else ""
    # (2) wheel-bundled
    wheel_native = os.path.join(HERE, "_native", f"{name}{suffix}")
    if os.path.isfile(wheel_native):
        return wheel_native
    # (3) developer repo build
    build_root = os.path.abspath(os.path.join(
        HERE, os.pardir, os.pardir, "build"))
    for sub in ("Release", "Debug", ""):
        cand = os.path.join(build_root, sub, f"{name}{suffix}")
        if os.path.isfile(cand):
            return cand
    return None


def _find_c_binary() -> str | None:
    """2D spectral binary. Honors $CS_SPECTRAL_BIN. See _find_native_binary."""
    return _find_native_binary("spectral", "CS_SPECTRAL_BIN")


def _find_c_binary_4d() -> str | None:
    """4D spectral_4d binary. Honors $CS_SPECTRAL_4D_BIN. See _find_native_binary."""
    return _find_native_binary("spectral_4d", "CS_SPECTRAL_4D_BIN")


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


# ─── 2D commands wired in v1.2.4 (compare/query/heatmap/analyze/export) ──
#
# Native Python implementations, so that the C↔Python parity tests in
# python/tests/test_2d_cli_parity.py compare two independent code paths.
# The numeric outputs (compare summary, analyze JSON, query channel
# energies) match the C binary byte-for-byte modulo float-formatter
# conventions documented in each command's helper.

_2D_CHANNELS = (
    ("A1", 0), ("A2", 64), ("B1", 128), ("B2", 192), ("E", 256),
    ("F1", 320), ("F2", 384), ("F3", 448), ("FA", 512), ("FD", 576),
)
_BOARD_DIM_2D = 64
_ENCODING_DIM_2D = 640


def _read_all_encodings_2d(path: str):
    """Returns (header, encodings) where encodings is shape (n_plies, 640)."""
    from chess_spectral import read_all
    hdr, frames = read_all(path)
    arr = np.empty((hdr.n_plies, _ENCODING_DIM_2D), dtype=np.float32)
    for i, fr in enumerate(frames):
        arr[i] = fr.encoding
    return hdr, frames, arr


def cmd_compare(args: argparse.Namespace) -> int:
    hdr_a, _, ea = _read_all_encodings_2d(args.a)
    hdr_b, _, eb = _read_all_encodings_2d(args.b)
    if hdr_a.n_plies != hdr_b.n_plies:
        print(f"compare: ply counts differ ({hdr_a.n_plies} vs {hdr_b.n_plies}); "
              f"comparing first {min(hdr_a.n_plies, hdr_b.n_plies)} plies",
              file=sys.stderr)
    n = min(hdr_a.n_plies, hdr_b.n_plies)
    if n == 0:
        print("compare: n_plies=0 (nothing to compare)")
        return 0
    # Per-ply cosine in float64 to match the C binary's accumulation type.
    a64 = ea[:n].astype(np.float64)
    b64 = eb[:n].astype(np.float64)
    dot = np.einsum("ij,ij->i", a64, b64)
    na = np.linalg.norm(a64, axis=1)
    nb = np.linalg.norm(b64, axis=1)
    denom = na * nb
    cos = np.where(denom > 0.0, dot / np.where(denom > 0.0, denom, 1.0), 1.0)
    cmin = float(cos.min())
    cmean = float(cos.mean())
    cmax = float(cos.max())
    cmin_ply = int(cos.argmin())
    print(f"compare: n_plies={n}  cos_min={cmin:.4f} (ply={cmin_ply})  "
          f"cos_mean={cmean:.4f}  cos_max={cmax:.4f}")
    return 0


def cmd_query_2d(args: argparse.Namespace) -> int:
    hdr, frames, _ = _read_all_encodings_2d(args.input)
    ply = args.ply
    if ply < 0 or ply >= hdr.n_plies:
        print(f"query: ply {ply} out of range (n_plies={hdr.n_plies})",
              file=sys.stderr)
        return 3
    fr = frames[ply]
    print(f"ply {fr.ply}  move_from={fr.move_from}  move_to={fr.move_to}  "
          f"promo={fr.move_promo}  flags={fr.move_flags}")
    total = 0.0
    enc = fr.encoding.astype(np.float64)
    for name, start in _2D_CHANNELS:
        E = float(np.sum(enc[start:start + _BOARD_DIM_2D] ** 2))
        total += E
        print(f"  E_{name:<3s} = {E:12.4f}   dims {start:3d}..{start + _BOARD_DIM_2D - 1:3d}")
    print(f"  E_total= {total:12.4f}")
    return 0


def cmd_heatmap(args: argparse.Namespace) -> int:
    chan_idx = -1
    for i, (name, _start) in enumerate(_2D_CHANNELS):
        if name == args.channel:
            chan_idx = i
            break
    if chan_idx < 0:
        print(f"heatmap: unknown channel {args.channel!r} "
              "(valid: A1,A2,B1,B2,E,F1,F2,F3,FA,FD)", file=sys.stderr)
        return 2
    hdr, frames, _ = _read_all_encodings_2d(args.input)
    if args.ply < 0 or args.ply >= hdr.n_plies:
        print(f"heatmap: ply {args.ply} out of range (n_plies={hdr.n_plies})",
              file=sys.stderr)
        return 3
    fr = frames[args.ply]
    name, start = _2D_CHANNELS[chan_idx]
    block = fr.encoding[start:start + _BOARD_DIM_2D]
    absmax = float(max(abs(block.min()), abs(block.max()), 1e-20))
    print(f"heatmap: {args.input} ply={fr.ply} channel={name} absmax={absmax:.4f}")
    glyphs = " .,:-=+*#@"
    for r in range(8):
        print(f"  {8 - r}  ", end="")
        for c in range(8):
            v = float(block[r * 8 + c])
            a = abs(v) / absmax
            bucket = min(int(a * 8.0), 8)
            ch = glyphs[bucket]
            col = 36 if v >= 0 else 31  # cyan + / red -
            print(f"\x1b[{col}m{ch}\x1b[0m ", end="")
        print()
    print("     a b c d e f g h")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Per-game spectral arc summary. Emits JSON matching the C binary
    byte-for-byte (same field order, same %.6f formatting). Heuristics
    follow chess_spectral_research_notebook.md §p.1636-1648 (ΔA₁
    derivative analysis)."""
    hdr, frames, _ = _read_all_encodings_2d(args.input)
    if hdr.n_plies == 0:
        print('{"n_plies":0}')
        return 0

    a1_peak = -1.0
    a1_peak_ply = 0
    dA1_drop = 0.0
    dA1_drop_ply = 0
    abs_dA1_max = 0.0
    crisis_ply = 0
    e_total_max = 0.0
    e_total_max_ply = 0

    prev_a1 = None
    for fr in frames:
        enc = fr.encoding.astype(np.float64)
        E_A1 = float(np.sum(enc[0:_BOARD_DIM_2D] ** 2))
        if E_A1 > a1_peak:
            a1_peak = E_A1
            a1_peak_ply = fr.ply
        E_total = 0.0
        for _name, s in _2D_CHANNELS:
            E_total += float(np.sum(enc[s:s + _BOARD_DIM_2D] ** 2))
        if E_total > e_total_max:
            e_total_max = E_total
            e_total_max_ply = fr.ply
        if prev_a1 is not None:
            d = enc[0:_BOARD_DIM_2D] - prev_a1
            dA1 = float(np.sqrt(float(np.sum(d * d))))
            prev_E_A1 = float(np.sum(prev_a1 ** 2))
            dA1_signed = -dA1 if E_A1 < prev_E_A1 else dA1
            if dA1_signed < dA1_drop:
                dA1_drop = dA1_signed
                dA1_drop_ply = fr.ply
            abs_d = abs(dA1_signed)
            if abs_d > abs_dA1_max:
                abs_dA1_max = abs_d
                crisis_ply = fr.ply
        prev_a1 = enc[0:_BOARD_DIM_2D].copy()

    # Match C printf(...) format byte-for-byte.
    print("{")
    print(f"  \"n_plies\":         {hdr.n_plies},")
    print(f"  \"a1_peak_ply\":     {a1_peak_ply},")
    print(f"  \"a1_peak_value\":   {a1_peak:.6f},")
    print(f"  \"a1_drop_ply\":     {dA1_drop_ply},")
    print(f"  \"a1_drop_value\":   {dA1_drop:.6f},")
    print(f"  \"crisis_ply\":      {crisis_ply},")
    print(f"  \"abs_dA1_max\":     {abs_dA1_max:.6f},")
    print(f"  \"e_total_max_ply\": {e_total_max_ply},")
    print(f"  \"e_total_max\":     {e_total_max:.6f}")
    print("}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Emit JSON for the web viewer. Mirrors the C binary's format
    exactly so test_2d_cli_parity.py can byte-compare."""
    hdr, frames, _ = _read_all_encodings_2d(args.input)
    out_fp = sys.stdout if not args.output or args.output == "-" else \
        open(args.output, "w", encoding="utf-8")
    try:
        out_fp.write("{\n")
        out_fp.write(f"  \"version\": {hdr.version},\n")
        out_fp.write(f"  \"encoding_dim\": {hdr.encoding_dim},\n")
        out_fp.write(f"  \"n_plies\": {hdr.n_plies},\n")
        out_fp.write("  \"channels\": [")
        for i, (name, start) in enumerate(_2D_CHANNELS):
            sep = "" if i == 0 else ","
            out_fp.write(f"{sep}{{\"name\":\"{name}\",\"start\":{start},"
                         f"\"end\":{start + _BOARD_DIM_2D - 1}}}")
        out_fp.write("],\n  \"frames\": [")
        for i, fr in enumerate(frames):
            sep = "" if i == 0 else ","
            out_fp.write(f"{sep}\n    {{")
            out_fp.write(f"\"ply\":{fr.ply},\"move_from\":{fr.move_from},"
                         f"\"move_to\":{fr.move_to},")
            out_fp.write(f"\"promo\":{fr.move_promo},\"flags\":{fr.move_flags},")
            out_fp.write("\"channel_energies\":{")
            enc = fr.encoding.astype(np.float64)
            for j, (name, start) in enumerate(_2D_CHANNELS):
                csep = "" if j == 0 else ","
                E = float(np.sum(enc[start:start + _BOARD_DIM_2D] ** 2))
                out_fp.write(f"{csep}\"{name}\":{E:.6f}")
            out_fp.write("},\"encoding\":[")
            for k in range(_ENCODING_DIM_2D):
                esep = "" if k == 0 else ","
                # %.6g matches C's printf("%.6g") precisely.
                out_fp.write(f"{esep}{float(fr.encoding[k]):.6g}")
            out_fp.write("]}")
        out_fp.write("\n  ]\n}\n")
    finally:
        if out_fp is not sys.stdout:
            out_fp.close()
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Run a single iterative-deepening search at the requested
    position and print the best move + key statistics.

    Drives the §16.2 search core with a single agent spec (the
    ``--agent`` argument). The CLI surface is intentionally symmetric
    with `tournament` so that "white spec" / "black spec" can be
    factored out into a single shared parser.
    """
    import json as _json
    import chess as _chess
    from chess_spectral.engine.tournament.agent_spec import (
        parse_spec, build_agent_2d,
    )

    board = _chess.Board(args.fen) if args.fen else _chess.Board()
    spec = parse_spec(args.agent)
    agent = build_agent_2d(spec)

    result = agent.search_fn(board, agent.evaluator, agent.search_options)

    out = {
        "agent": agent.label,
        "fen": board.fen(),
        "best_move": result.best_move.uci() if result.best_move else None,
        "best_score": result.best_score,
        "depth_reached": result.depth_reached,
        "nodes_searched": result.nodes_searched,
        "elapsed_ms": result.elapsed_ms,
        "pv": [m.uci() for m in result.pv],
        "tt_hits": result.tt_hits,
        "tt_size": result.tt_size,
    }
    if args.json:
        print(_json.dumps(out, indent=2))
    else:
        print(f"agent: {out['agent']}")
        print(f"fen:   {out['fen']}")
        print(f"best:  {out['best_move']} (score={out['best_score']:.3f})")
        print(f"depth: {out['depth_reached']}  nodes: {out['nodes_searched']}  "
              f"time: {out['elapsed_ms']:.1f}ms")
        if out["pv"]:
            print("pv:    " + " ".join(out["pv"]))
        if agent.search_options.use_tt:
            print(f"tt:    hits={out['tt_hits']}  size={out['tt_size']}")
    return 0


def cmd_tournament(args: argparse.Namespace) -> int:
    """Run a round-robin tournament between two or more agents.

    Each ``--agent SPEC`` produces one configured engine. Pairs play
    ``--n-games-per-pair`` games (alternating colors). Outputs Elo
    ratings + per-pair scores in JSON.

    The flow matches §16's ship gate: pit (evaluator, depth) cells
    against each other, log who beat whom, compute Elo, decide ship.
    """
    import json as _json
    import chess as _chess
    from chess_spectral.engine.tournament.agent_spec import (
        parse_spec, build_agent_2d,
    )
    from chess_spectral.engine.tournament import run_round_robin

    if len(args.agent) < 2:
        print("tournament: need at least 2 --agent specs", file=sys.stderr)
        return 2

    agents = [build_agent_2d(parse_spec(spec)) for spec in args.agent]

    result = run_round_robin(
        agents,
        n_games_per_pair=args.n_games_per_pair,
        board_factory=_chess.Board,
        max_plies=args.max_plies,
    )

    out = {
        "agents": [a.label for a in agents],
        "n_games_per_pair": args.n_games_per_pair,
        "max_plies": args.max_plies,
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
        prog="spectral_py",
        description="Python mirror of the C `spectral` CLI.",
    )
    # Not required=True — we want to show full help when the user runs
    # `python spectral_py.py` with no args, rather than a terse error.
    sub = ap.add_subparsers(dest="cmd")

    p_csv = sub.add_parser(
        "csv",
        help="Export .spectral[z] to CSV",
        description=(
            "Read a .spectral or .spectralz file and emit the chat-friendly "
            "17-column CSV (per-ply inter-frame metrics + 10 channel "
            "energies). Auto-detects a sibling NDJSON for eval/clk/nag "
            "merge unless --no-meta is given."
        ),
    )
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
        description=(
            "Encode a PGN / NDJSON / URL stream into a v2 .spectral file. "
            "With --pgn / --url, auto-pipes through pgn_bridge.py "
            "(supports --pgn-start / --pgn-count for multi-game slicing). "
            "With -z, writes gzip-compressed output. Mirrors the C "
            "`spectral encode` CLI byte-for-byte."
        ),
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

    p_fen = sub.add_parser(
        "encode-fen",
        help="Encode single FEN → 1-frame file",
        description=(
            "Encode a single FEN string to a one-ply .spectral file. "
            "Output is byte-identical (modulo gzip framing) to the C "
            "`spectral encode-fen` binary; gzip output is inferred from "
            "an .spectralz suffix if -z is not given explicitly."
        ),
    )
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

    p_ver = sub.add_parser(
        "version",
        help="Print version info",
        description=(
            "Print the spectral_py CLI version, the .spectral file-format "
            "version, and the encoding dimensionality. Useful for "
            "matching a wheel against expected C-side output."
        ),
    )
    p_ver.set_defaults(func=cmd_version)

    # ─── 2D commands wired in v1.2.4 ───
    p_cmp = sub.add_parser(
        "compare",
        help="Cosine-similarity report between two .spectral files",
        description=(
            "Print per-ply cosine similarity statistics between two "
            ".spectral / .spectralz files (min, mean, max + ply of min). "
            "Float64 accumulation matches the C binary's reduction order; "
            "ply counts may differ — only the common prefix is compared."
        ),
    )
    p_cmp.add_argument("a", help="first .spectral or .spectralz file")
    p_cmp.add_argument("b", help="second .spectral or .spectralz file")
    p_cmp.set_defaults(func=cmd_compare)

    p_qry = sub.add_parser(
        "query",
        help="Print 10-channel breakdown at ply N",
        description=(
            "Print the 10-channel energy breakdown (A1, A2, B1, B2, E, "
            "F1, F2, F3, FA, FD) for a single ply, along with move "
            "metadata. Output format mirrors the C binary."
        ),
    )
    p_qry.add_argument("input", help="game.spectral or .spectralz")
    p_qry.add_argument("--ply", type=int, required=True,
                       help="ply index (0-based)")
    p_qry.set_defaults(func=cmd_query_2d)

    p_hm = sub.add_parser(
        "heatmap",
        help="ANSI 8x8 of one channel at one ply",
        description=(
            "Render an ANSI-colored 8x8 heatmap of one of the 10 spectral "
            "channels (A1/A2/B1/B2/E/F1/F2/F3/FA/FD) at one ply. Cyan = "
            "positive, red = negative, glyph density tracks magnitude "
            "relative to the slice's absmax."
        ),
    )
    p_hm.add_argument("input", help="game.spectral or .spectralz")
    p_hm.add_argument("--ply", type=int, required=True,
                      help="ply index (0-based)")
    p_hm.add_argument("--channel", default="A1",
                      help="channel name: A1,A2,B1,B2,E,F1,F2,F3,FA,FD")
    p_hm.set_defaults(func=cmd_heatmap)

    p_ana = sub.add_parser(
        "analyze",
        help="Per-game JSON summary (A1 peak/drop/crisis ply)",
        description=(
            "Per-game spectral arc summary mirroring the C binary "
            "byte-for-byte. Heuristics: chess_spectral_research_notebook.md "
            "§p.1636-1648 (ΔA₁ derivative analysis)."
        ),
    )
    p_ana.add_argument("input", help="game.spectral or .spectralz")
    p_ana.set_defaults(func=cmd_analyze)

    p_exp = sub.add_parser(
        "export",
        help="Dump frames to JSON for the web viewer",
        description=(
            "Dump every frame in a .spectral / .spectralz file to JSON, "
            "in the format consumed by the chess-maths-viewer web app. "
            "Output is byte-identical to the C `spectral export` binary "
            "modulo float-formatter conventions (%.6g, see source)."
        ),
    )
    p_exp.add_argument("input", help="game.spectral or .spectralz")
    p_exp.add_argument("-o", "--output",
                       help="output JSON path (default: stdout)")
    p_exp.set_defaults(func=cmd_export)

    p_search = sub.add_parser(
        "search",
        help="Run §16.2 search at a given position",
        description=(
            "Iterative-deepening alpha-beta search. The --agent argument "
            "is a comma-separated key=value spec, e.g.:\n\n"
            "  evaluator=spectral,depth=4,weights=spectral_v1.json\n"
            "  evaluator=qm,depth=3,no_quiescence,time_budget_ms=2000\n\n"
            "Recognized keys: label, evaluator (material/spectral/qm), "
            "depth, time_budget_ms, weights (path), quiescence_max_depth, "
            "no_tt, no_mvv_lva, no_quiescence (boolean flags). Default "
            "depth=4, all optimizations on."
        ),
    )
    p_search.add_argument(
        "--fen",
        help="FEN string of the position to search (default: starting position)",
    )
    p_search.add_argument(
        "--agent", required=True, metavar="SPEC",
        help="agent spec (e.g. 'evaluator=spectral,depth=4')",
    )
    p_search.add_argument(
        "--json", action="store_true",
        help="emit machine-readable JSON instead of human summary",
    )
    p_search.set_defaults(func=cmd_search)

    p_tour = sub.add_parser(
        "tournament",
        help="Run round-robin self-play tournament between agents",
        description=(
            "Round-robin tournament. Pass two or more --agent specs; "
            "each pair plays --rounds-per-pair games with alternating "
            "colors. Output is JSON with Elo ratings, wins/draws/losses, "
            "and per-game termination + ply counts.\n\n"
            "This is the §16 ship-gate driver: pit (evaluator, depth) "
            "cells against each other, accumulate Elo evidence, decide "
            "whether the spectral framework empirically beats the "
            "material baseline.\n\n"
            "Example -- 3-cell mini-sweep at depth 2:\n"
            "  spectral_py tournament \\\n"
            "    --agent 'label=mat,evaluator=material,depth=2' \\\n"
            "    --agent 'label=spec,evaluator=spectral,depth=2' \\\n"
            "    --agent 'label=qm,evaluator=qm,depth=2' \\\n"
            "    --rounds-per-pair 4 -o sweep_d2.json"
        ),
    )
    p_tour.add_argument(
        "--agent", required=True, action="append", metavar="SPEC",
        help="agent spec; repeat for each agent in the round-robin "
             "(minimum 2; agents play each other in both colors)",
    )
    p_tour.add_argument(
        "--n-games-per-pair", type=int, default=2,
        help="games per pair (default: 2 -- one as white, one as black; "
             "each player plays the other twice)",
    )
    p_tour.add_argument(
        "--max-plies", type=int, default=200,
        help="hard cap on plies per game (default: 200; long endgames "
             "draw on this rule)",
    )
    p_tour.add_argument(
        "-o", "--output",
        help="write tournament JSON to FILE instead of stdout",
    )
    p_tour.set_defaults(func=cmd_tournament)

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
