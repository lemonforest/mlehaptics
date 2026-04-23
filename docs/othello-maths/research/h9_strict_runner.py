"""Phase 1d — H9-strict / E8 spectral × Takizawa perfect-play correlations.

Scales the Phase 1c.3 N=15 peek to N=2587 by using Takizawa's full
perfect-play knowledge.  Two cooperating sources:

1. ``empty50_tasklist_edax_knowledge.csv`` (204 KB, committed in
   Phase 1c.3).  Schema: obf, count, score, alpha, beta.  One row
   per D4-canonical 50-empty position Takizawa needed to solve.
   The ``score`` column is edax's pre-proof predicted value.

2. ``knowledge_<64-char-OBF>.csv`` files (171 GB, not in repo,
   typically at a drive-letter path).  One file per 50-empty
   parent, listing 36-empty sub-problems reached under optimal play
   with their exact game-theoretic bounds.

This runner:

- Loads the 2587-row tasklist → gets ``score`` (edax prediction).
- For every row, computes the full spectral observable battery on
  the 50-empty signal: A1-, B1, B2, E energies under the D4xZ2
  projection, plus the D4-only A1 on s^2 (occupation).
- Optionally, if ``--archive`` is provided, also reads each of the
  2587 knowledge files and appends aggregate bounds (mean/min/max
  lb/ub) from the proof tree.  This is the strict H9 augmentation.
- Emits ``phase1d_spectral_vs_perfectplay.csv`` (one row per
  position) + ``phase1d_correlations.json`` (aggregate Spearmans).

Correlations reported (for each spectral observable × each
value-proxy):

  Spearman(obs, predicted_score)         — from small CSV
  Spearman(obs, |predicted_score|)       — magnitude (disc-count-like)
  Spearman(obs, archive_mean_lb)         — requires --archive
  Spearman(obs, archive_mean_ub)
  Partial controlling for |disc_diff|

The 50-empty positions all have 14 discs placed, so disc_diff is a
relatively narrow control (|disc_diff| in [0, 14]) but still worth
partialling out.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import BLACK, N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep

_ensure_utf8_stdio()

_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


# ---------------------------------------------------------------------------
# Signal extraction from OBF
# ---------------------------------------------------------------------------


def obf_to_state(obf: str) -> tuple[np.ndarray, int]:
    """Convert an OBF string to (64-dim state in {-1, 0, +1},
    side_to_move in {BLACK, -BLACK})."""
    player_bb, opponent_bb = _ref.obf_to_bitboards(obf)
    # OBF encodes player as the side-to-move's stones.
    side = BLACK if obf[65] == "X" else -BLACK
    state = np.zeros(N, dtype=int)
    for i in range(N):
        if (player_bb >> i) & 1:
            state[i] = side
        elif (opponent_bb >> i) & 1:
            state[i] = -side
    return state, side


# ---------------------------------------------------------------------------
# Spectral observables
# ---------------------------------------------------------------------------


def _d4_only_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = 2 if irrep == "E" else 1
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def spectral_observables(state: np.ndarray) -> dict:
    sig = state.astype(float)
    return {
        "a1_minus_energy": float(
            np.linalg.norm(project_irrep(sig, "A1-")) ** 2
        ),
        "b1_energy": _d4_only_energy(sig, "B1"),
        "b2_energy": _d4_only_energy(sig, "B2"),
        "e_energy": _d4_only_energy(sig, "E"),
        "d4_a1_occupation_energy": _d4_only_energy(sig ** 2, "A1"),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _load_tasklist(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _load_archive_summary(path: Path) -> dict[str, dict]:
    """Load the per-parent summary produced by
    takizawa_archive_loader.py.  Returns {parent_obf -> stats}."""
    out = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out[row["parent_obf"]] = row
    return out


def run(
    tasklist_path: Path,
    archive_summary_path: Path | None,
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    rows = _load_tasklist(tasklist_path)
    print(f"tasklist: {len(rows)} positions")

    archive_summary: dict[str, dict] = {}
    if archive_summary_path is not None and archive_summary_path.exists():
        archive_summary = _load_archive_summary(archive_summary_path)
        print(f"archive summary: {len(archive_summary)} parents")

    records: list[dict] = []
    for row in rows:
        obf = row["obf"]
        state, side = obf_to_state(obf)
        spec = spectral_observables(state)
        b = int(np.sum(state == BLACK))
        w = int(np.sum(state == -BLACK))
        e = int(np.sum(state == 0))
        rec = {
            "obf": obf,
            "side_to_move": side,
            "n_empties": e,
            "black_count": b,
            "white_count": w,
            "disc_diff_player_minus_opp": (
                b - w if side == BLACK else w - b
            ),
            "count_wthor": int(row["count"]),
            "edax_score": int(row["score"]),
            "edax_alpha": int(row["alpha"]),
            "edax_beta": int(row["beta"]),
            **spec,
        }
        arc = archive_summary.get(obf)
        if arc is not None:
            def _f(key):
                v = arc.get(key, "")
                if v == "" or v is None:
                    return None
                try:
                    return float(v)
                except ValueError:
                    return None
            rec["archive_n_children"] = int(arc.get("n_children", 0))
            rec["archive_mean_lb"] = _f("mean_lb")
            rec["archive_mean_ub"] = _f("mean_ub")
            rec["archive_median_lb"] = _f("median_lb")
            rec["archive_median_ub"] = _f("median_ub")
            rec["archive_min_lb"] = _f("min_lb")
            rec["archive_max_ub"] = _f("max_ub")
            rec["archive_exact_fraction"] = _f("exact_fraction")
        records.append(rec)

    elapsed = time.time() - t0
    print(
        f"computed spectral observables for {len(records)} positions "
        f"in {elapsed:.1f}s"
    )

    # ------------------------------------------------------------
    # CSV output
    # ------------------------------------------------------------
    csv_path = out_dir / "phase1d_spectral_vs_perfectplay.csv"
    if records:
        fieldnames = list(records[0].keys())
        # union with any record that carries archive fields
        for r in records:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                writer.writerow(r)

    # ------------------------------------------------------------
    # Correlations
    # ------------------------------------------------------------
    summary: dict = {
        "n_positions": len(records),
        "tasklist_path": str(tasklist_path),
        "archive_summary_path": (
            str(archive_summary_path) if archive_summary_path else None
        ),
        "wall_time_seconds": elapsed,
    }

    spectral_keys = [
        "a1_minus_energy", "b1_energy", "b2_energy",
        "e_energy", "d4_a1_occupation_energy",
    ]
    value_keys = ["edax_score"]
    if archive_summary:
        value_keys.extend([
            "archive_mean_lb", "archive_mean_ub",
            "archive_median_lb", "archive_median_ub",
        ])

    def _vec(key):
        return np.array([
            r.get(key) for r in records if r.get(key) is not None
        ], dtype=float)

    def _aligned(k1, k2):
        xs, ys = [], []
        for r in records:
            a = r.get(k1); b = r.get(k2)
            if a is None or b is None:
                continue
            xs.append(float(a)); ys.append(float(b))
        return np.array(xs), np.array(ys)

    correlations: dict[str, dict] = {}
    for sk in spectral_keys:
        for vk in value_keys:
            xs, ys = _aligned(sk, vk)
            if xs.size < 3:
                continue
            sp = spearmanr(xs, ys)
            correlations[f"spearman__{sk}__vs__{vk}"] = {
                "rho": float(sp.statistic),
                "pvalue": float(sp.pvalue),
                "n": int(xs.size),
            }
            # Also the absolute-value variant
            sp_abs = spearmanr(xs, np.abs(ys))
            correlations[f"spearman__{sk}__vs__abs_{vk}"] = {
                "rho": float(sp_abs.statistic),
                "pvalue": float(sp_abs.pvalue),
                "n": int(xs.size),
            }

    # Partial correlation controlling for |disc_diff|
    partials: dict[str, dict] = {}
    disc_diff = np.array([
        abs(r["disc_diff_player_minus_opp"]) for r in records
    ], dtype=float)
    for sk in spectral_keys:
        xs = np.array([r[sk] for r in records], dtype=float)
        ys = np.array([r["edax_score"] for r in records], dtype=float)
        if np.std(disc_diff) > 0:
            coef = np.polyfit(disc_diff, ys, 1)
            ys_resid = ys - (coef[0] * disc_diff + coef[1])
            sp = spearmanr(xs, ys_resid)
            partials[f"partial__{sk}__vs__edax_score__ctrl_abs_disc_diff"] = {
                "rho": float(sp.statistic),
                "pvalue": float(sp.pvalue),
                "n": int(xs.size),
            }

    summary["correlations"] = correlations
    summary["partial_correlations"] = partials

    json_path = out_dir / "phase1d_correlations.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nwrote {csv_path}")
    print(f"wrote {json_path}")

    # Stdout-friendly highlights
    print(f"\n=== Phase 1d correlation highlights (N = {len(records)}) ===")
    for key, info in correlations.items():
        if "edax_score" not in key and "archive_mean" not in key:
            continue
        if abs(info["rho"]) < 0.05 and info["pvalue"] > 0.1:
            continue  # skip noise
        print(
            f"  {key:72s}  rho={info['rho']:+.3f}  "
            f"p={info['pvalue']:.2e}  N={info['n']}"
        )
    for key, info in partials.items():
        print(
            f"  {key:72s}  rho={info['rho']:+.3f}  "
            f"p={info['pvalue']:.2e}  N={info['n']}"
        )
    return summary


def _build_parser() -> argparse.ArgumentParser:
    default_tasklist = (
        Path(__file__).resolve().parent.parent / "dataset"
        / "reversi_scripts" / "empty50_tasklist_edax_knowledge.csv"
    )
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Phase 1d.a: tasklist-only (fast, ~2 sec, N=2587)
  python research/h9_strict_runner.py

  # Phase 1d.b: tasklist + archive bounds (first generate the
  # archive summary with takizawa_archive_loader.py)
  python research/takizawa_archive_loader.py \\
      --archive /n/NORMSTOR/knowledge_archive \\
      --out ../results/phase1d_archive_summary.csv
  python research/h9_strict_runner.py \\
      --archive-summary ../results/phase1d_archive_summary.csv

notes:
  All 2587 tasklist positions have 50 empty squares.  ``edax_score``
  from the tasklist is edax's pre-proof predicted value with
  alpha/beta=-64/64.  For strict H9, pair with --archive-summary.
""",
    )
    parser.add_argument(
        "--tasklist", type=Path, default=default_tasklist,
        help="Path to empty50_tasklist_edax_knowledge.csv (default: "
             "the committed file under dataset/reversi_scripts/).",
    )
    parser.add_argument(
        "--archive-summary", type=Path, default=None,
        help="Optional path to the per-file aggregate CSV produced "
             "by takizawa_archive_loader.py.  If given, archive "
             "bounds are joined into the per-position records and "
             "correlated.",
    )
    parser.add_argument(
        "--results-dir", type=Path, default=default_results,
        help="Output directory for phase1d_spectral_vs_perfectplay.csv "
             "and phase1d_correlations.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.tasklist.exists():
        print(f"tasklist not found: {args.tasklist}", file=sys.stderr)
        return 2
    run(args.tasklist, args.archive_summary, args.results_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
