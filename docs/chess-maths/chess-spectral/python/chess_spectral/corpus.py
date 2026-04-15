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

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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
) -> dict[str, Any]:
    """PGN text → written PGN file → bridged NDJSON → encoded .spectralz.

    `out_dir` is expected to contain sibling `pgn/`, `ndjson/`,
    `spectralz/` subdirs (caller's responsibility — we don't mkdir
    here, so the sweep driver's single mkdir pass stays visible).

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
