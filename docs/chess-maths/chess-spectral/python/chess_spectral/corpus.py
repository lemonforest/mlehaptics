"""corpus — shared primitives for corpus-scale pipelines.

Two layers:

  process_game(game_dict, out_dir, idx, bridge_script, encoder_script)
      PGN text → file → NDJSON → spectralz. Returns the per-game
      manifest entry (what the pilot and sweep drivers write under
      "games":[...]). Any subprocess failure is captured into an
      `error` field rather than raised, so bulk runs don't abort on a
      single bad game.

  extract_features(spectralz_path, ndjson_path)
      Read the encoded frames and the source NDJSON; return a dict of
      sortable numeric features (mean per-channel energy, chaos ratio,
      NAG counts, ply count). Called by the sweep driver to assemble
      corpus_index.csv.

Both primitives are pure Python — no CLI arg parsing, no file-system
layout assumptions beyond what the caller passes in.
"""
from __future__ import annotations

import csv
import io
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .frame import read_encodings
from .encoder import CHANNELS, BOARD_DIM

_IRREP_CHANNELS = ("A1", "A2", "B1", "B2", "E", "F1", "F2", "F3")
_FIBER_CHANNELS = ("FA", "FD")


# ─── Subprocess helpers ─────────────────────────────────────────────────

def _run(cmd: list[str]) -> None:
    """Run a subprocess, raising with command + stderr on failure."""
    proc = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"--- stderr ---\n{proc.stderr}"
        )


# ─── Per-game processing (PGN → NDJSON → spectralz) ─────────────────────

def _describe_game(game: dict, idx: int) -> dict[str, Any]:
    """Extract the header-derived fields we always carry in the manifest."""
    h = game.get("headers", {})
    return {
        "index":       idx,
        "white":       h.get("White", "?"),
        "black":       h.get("Black", "?"),
        "result":      h.get("Result", "?"),
        "event":       h.get("Event", ""),
        "date":        h.get("Date", ""),
        "white_elo":   h.get("WhiteElo", ""),
        "black_elo":   h.get("BlackElo", ""),
        "n_moves":     game.get("n_moves"),
        "source_date": game.get("source_date"),
        "source_test": game.get("source_test"),
        "source_tc":   game.get("source_tc"),
    }


def process_game(
    game: dict,
    out_dir: Path,
    idx: int,
    bridge_script: Path,
    encoder_script: Path,
    stem: str | None = None,
    encoder_binary: Path | None = None,
) -> dict[str, Any]:
    """PGN text → written PGN file → bridged NDJSON → encoded .spectralz.

    `out_dir` is expected to contain sibling `pgn/`, `ndjson/`,
    `spectralz/` subdirs (caller's responsibility — we don't mkdir
    here, so the sweep driver's single mkdir pass stays visible).

    `encoder_binary` selects the NDJSON→.spectralz backend:
        None (default) → Python reference encoder (`encoder_script`)
        Path           → native C binary (spectral.exe), ~38× faster,
                         byte-identical output verified by parity test.

    Returns the manifest entry for this game. On subprocess failure the
    entry has an `"error"` field populated and the downstream artifacts
    may be missing.
    """
    stem = stem or f"game_{idx:03d}"
    pgn_path      = out_dir / "pgn"       / f"{stem}.pgn"
    ndjson_path   = out_dir / "ndjson"    / f"{stem}.ndjson"
    spectral_path = out_dir / "spectralz" / f"{stem}.spectralz"

    desc = _describe_game(game, idx)
    desc["pgn"]       = f"pgn/{stem}.pgn"
    desc["ndjson"]    = f"ndjson/{stem}.ndjson"
    desc["spectralz"] = f"spectralz/{stem}.spectralz"

    try:
        pgn_path.write_text(game["pgn"].rstrip() + "\n", encoding="utf-8")
        desc["pgn_bytes"] = pgn_path.stat().st_size
    except (KeyError, OSError) as e:
        desc["error"] = f"write_pgn: {e}"
        return desc

    try:
        _run([sys.executable, str(bridge_script),
              "--input", str(pgn_path), "-o", str(ndjson_path)])
        desc["ndjson_bytes"] = ndjson_path.stat().st_size
    except (RuntimeError, OSError) as e:
        desc["error"] = f"bridge: {e}"
        return desc

    try:
        if encoder_binary is not None:
            # C binary: positional input, no -i flag
            _run([str(encoder_binary), "encode",
                  str(ndjson_path), "-o", str(spectral_path), "-z"])
        else:
            _run([sys.executable, str(encoder_script), "encode",
                  "-i", str(ndjson_path), "-o", str(spectral_path), "-z"])
        desc["spectralz_bytes"] = spectral_path.stat().st_size
    except (RuntimeError, OSError) as e:
        desc["error"] = f"encode: {e}"
        return desc

    return desc


# ─── Per-game feature extraction ────────────────────────────────────────

def _frame_channel_energies(arr: np.ndarray) -> dict[str, np.ndarray]:
    """Return {channel_name: (n_plies,) energy vector}. Per-frame
    ||channel||² — same formula as channel_energies(), vectorised."""
    out = {}
    for name, start in CHANNELS:
        sub = arr[:, start:start + BOARD_DIM]
        out[name] = np.einsum("ij,ij->i", sub, sub)
    return out


def _count_nags(ndjson_path: Path) -> tuple[int, int, int, bool, bool]:
    """Walk the per-ply records of a v2 NDJSON file and return
    (total_nags, blunders, mistakes, had_any_eval, had_any_clk)."""
    total = blunders = mistakes = 0
    had_eval = had_clk = False
    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "game_header":
                continue
            if "fen" not in rec and "pos" not in rec:
                continue
            if "nag" in rec:
                total += 1
                if rec["nag"] == "??":
                    blunders += 1
                elif rec["nag"] == "?":
                    mistakes += 1
            if "eval" in rec:
                had_eval = True
            if "clk" in rec:
                had_clk = True
    return total, blunders, mistakes, had_eval, had_clk


def extract_features(
    spectralz_path: str | Path,
    ndjson_path: str | Path,
) -> dict[str, Any]:
    """Compute sortable per-game features from the encoded frames + the
    source NDJSON. Numeric columns are rounded to 4 decimals so CSV
    output stays human-readable.

    Features
    --------
    - n_plies
    - mean_<channel> for each of the 10 channels
    - chaos_ratio = mean(L2_fiber) / mean(L2_irrep), per-frame L2 norms
    - nag_count, blunder_count, mistake_count
    - has_eval, has_clk (did the source PGN carry those macros?)
    """
    _, arr = read_encodings(str(spectralz_path))
    n_plies = int(arr.shape[0])

    feats: dict[str, Any] = {"n_plies": n_plies}

    if n_plies == 0:
        for name, _ in CHANNELS:
            feats[f"mean_{name}"] = 0.0
        feats["chaos_ratio"] = 0.0
    else:
        per_frame = _frame_channel_energies(arr)
        for name, energies in per_frame.items():
            feats[f"mean_{name}"] = round(float(energies.mean()), 4)

        l2_irrep = np.sqrt(sum(per_frame[c] for c in _IRREP_CHANNELS))
        l2_fiber = np.sqrt(sum(per_frame[c] for c in _FIBER_CHANNELS))
        mean_irrep = float(l2_irrep.mean())
        mean_fiber = float(l2_fiber.mean())
        feats["chaos_ratio"] = (
            round(mean_fiber / mean_irrep, 4) if mean_irrep > 0.0 else 0.0
        )

    total, blunders, mistakes, had_eval, had_clk = _count_nags(Path(ndjson_path))
    feats["nag_count"] = total
    feats["blunder_count"] = blunders
    feats["mistake_count"] = mistakes
    feats["has_eval"] = had_eval
    feats["has_clk"] = had_clk

    return feats


# ─── Corpus-layout writers (manifest / index / summary) ─────────────────
#
# Shared schema for `results/<run_id>/` folders consumed by the
# chess-maths-viewer. Fetch-driven sweeps (run_corpus_sweep.py) and
# single-PGN wraps (spectral_py.py corpus) both emit the same layout:
#
#     <run_id>/
#         manifest.json
#         corpus_index.csv      (columns: INDEX_COLUMNS)
#         corpus_summary.md
#         pgn/game_NNN.pgn
#         ndjson/game_NNN.ndjson
#         spectralz/game_NNN.spectralz

_IDENTITY_COLS = (
    "index", "run_id", "result", "n_moves", "n_plies",
    "white", "black", "white_elo", "black_elo",
    "event", "date", "source_tc",
)
_FEATURE_COLS = (
    "chaos_ratio", "nag_count", "blunder_count", "mistake_count",
    "has_eval", "has_clk",
)
_CHANNEL_COLS = tuple(f"mean_{name}" for name, _ in CHANNELS)
_BYTES_COLS = ("pgn_bytes", "ndjson_bytes", "spectralz_bytes")
_ERROR_COL = ("error",)
INDEX_COLUMNS = (
    _IDENTITY_COLS + _FEATURE_COLS + _CHANNEL_COLS + _BYTES_COLS + _ERROR_COL
)


def row_for_csv(entry: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Flatten a manifest entry + features dict into one CSV row. Missing
    numeric fields become '' so the spreadsheet shows blanks (not zero)
    for failed games."""
    row = {col: "" for col in INDEX_COLUMNS}
    row["run_id"] = run_id
    for col in INDEX_COLUMNS:
        if col in entry:
            row[col] = entry[col]
    return row


def _top_n(rows: list[dict[str, Any]], key: str, n: int = 5,
           reverse: bool = True) -> list[dict[str, Any]]:
    viable = [r for r in rows if isinstance(r.get(key), (int, float))]
    viable.sort(key=lambda r: r[key], reverse=reverse)
    return viable[:n]


def _fmt_row_for_summary(row: dict[str, Any]) -> str:
    white = row.get("white", "?")
    black = row.get("black", "?")
    res = row.get("result", "?")
    return f"#{row['index']:>3} {white} vs {black} ({res})"


def write_index_csv(rows: Iterable[dict[str, Any]], out_path: str | Path,
                    run_id: str) -> None:
    """Write corpus_index.csv with INDEX_COLUMNS header + one row per game."""
    out_path = Path(out_path)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(INDEX_COLUMNS))
        w.writeheader()
        for entry in rows:
            w.writerow(row_for_csv(entry, run_id))


def write_summary_md(rows: list[dict[str, Any]], out_path: str | Path,
                     run_id: str, elapsed_s: float,
                     n_requested: int, n_fetched: int,
                     n_encoded: int, n_errors: int) -> None:
    """Write corpus_summary.md — aggregates + top-5 tables per feature."""
    ok = [r for r in rows if not r.get("error")]

    def _stat(key: str) -> tuple[float, float, float] | None:
        vals = [r[key] for r in ok if isinstance(r.get(key), (int, float))]
        if not vals:
            return None
        return (
            statistics.mean(vals),
            statistics.median(vals),
            statistics.stdev(vals) if len(vals) > 1 else 0.0,
        )

    result_counts: dict[str, int] = {}
    for r in ok:
        result_counts[r.get("result", "?")] = \
            result_counts.get(r.get("result", "?"), 0) + 1

    lines: list[str] = []
    lines.append(f"# Corpus sweep summary — `{run_id}`")
    lines.append("")
    lines.append(f"- Games requested: **{n_requested}**")
    lines.append(f"- Games fetched:   **{n_fetched}**")
    lines.append(f"- Games encoded:   **{n_encoded}**")
    lines.append(f"- Errors:          **{n_errors}**")
    lines.append(f"- Wall time:       **{elapsed_s:.1f}s**")
    lines.append("")
    if result_counts:
        lines.append("## Result distribution")
        lines.append("")
        for res, count in sorted(result_counts.items(),
                                 key=lambda kv: -kv[1]):
            lines.append(f"- `{res}`: {count}")
        lines.append("")

    lines.append("## Numeric feature stats (successful games)")
    lines.append("")
    lines.append("| Feature | mean | median | stdev |")
    lines.append("|---|---|---|---|")
    for key in ("n_plies", "chaos_ratio", "nag_count", "blunder_count",
                "mean_F3", "mean_FA", "mean_FD"):
        st = _stat(key)
        if st:
            m, md, sd = st
            lines.append(f"| {key} | {m:.4f} | {md:.4f} | {sd:.4f} |")
    lines.append("")

    for key, label, rev in (
        ("chaos_ratio",   "Top 5 by chaos ratio (sharpest)", True),
        ("blunder_count", "Top 5 by blunder count (NAG heavy)", True),
        ("nag_count",     "Top 5 by total NAGs", True),
        ("n_plies",       "Top 5 by length", True),
    ):
        top = _top_n(ok, key, 5, reverse=rev)
        if not top:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for r in top:
            v = r[key]
            tag = f"{v:.4f}" if isinstance(v, float) else str(v)
            lines.append(f"- `{tag:>10}`  {_fmt_row_for_summary(r)}")
        lines.append("")

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


# ─── Local-PGN ingestion (for single-game corpora) ──────────────────────

def _game_to_dict(game: Any) -> dict[str, Any]:
    """Convert a python-chess Game object to the dict shape process_game
    expects. Emits PGN text for just this one game (so multi-game files
    don't get all their games re-encoded by the bridge)."""
    import chess.pgn  # local import

    exporter = chess.pgn.StringExporter(
        headers=True, variations=False, comments=True,
    )
    pgn_text = game.accept(exporter)

    headers = dict(game.headers)
    n_plies = 0
    node = game
    while node.variations:
        node = node.variations[0]
        n_plies += 1
    n_moves = (n_plies + 1) // 2

    return {
        "pgn":         pgn_text,
        "headers":     headers,
        "n_moves":     n_moves,
        "source_date": headers.get("Date"),
        "source_test": None,
        "source_tc":   headers.get("TimeControl"),
    }


def parse_local_pgn(pgn_path: str | Path) -> dict[str, Any]:
    """Parse the *first* game of a local PGN file into the game-dict shape
    that process_game expects. For multi-game files use
    iter_local_pgn_games() instead.

    Raises ValueError if the file contains no parseable game."""
    import chess.pgn  # local import so corpus.py stays import-cheap

    pgn_path = Path(pgn_path)
    with open(pgn_path, encoding="utf-8") as f:
        game = chess.pgn.read_game(f)
    if game is None:
        raise ValueError(f"no game found in {pgn_path}")
    return _game_to_dict(game)


def iter_local_pgn_games(pgn_path: str | Path,
                         limit: int | None = None) -> Any:
    """Yield game-dicts for every game in a multi-game PGN file.

    Streams via chess.pgn.read_game so large PGN files (Lichess monthly
    dumps, broadcast archives) don't need to be held fully in memory. If
    a single game fails to parse, the exception propagates — the caller
    is responsible for deciding whether to skip or abort.
    """
    import chess.pgn
    pgn_path = Path(pgn_path)
    count = 0
    with open(pgn_path, encoding="utf-8") as f:
        while True:
            if limit is not None and count >= limit:
                return
            game = chess.pgn.read_game(f)
            if game is None:
                return
            yield _game_to_dict(game)
            count += 1
