"""§2c.3 retest at corpus scale — spectral vs edax_score on the
50-empty positions overlap with the Takizawa tasklist.

§2c.3 found Spearman(A1-, edax_score) = +0.820 on N = 15 matching
positions from Barcelona.  That was flagged as "striking but
underpowered".  This runner scales up:

  1. For every PGN game, walk the trajectory and find the first
     position with exactly 50 empty cells.
  2. Compute its D4 canonical form and check for membership in the
     2587-row empty50_tasklist_edax_knowledge.csv.
  3. For matching positions, compute the full spectral battery
     (A1-, B1-, B2-, E-, D4-A1(s^2), D4-E(s^2)) and record
     edax_score + archive_mean_lb from the tasklist / archive
     summary.
  4. Aggregate across all 4 liveothello corpora (Barcelona, 2005 WC,
     APR 2026, 2025-all) for maximum N.
  5. Compute Spearman correlations against both edax_score (pre-proof)
     and archive_mean_lb (proved bounds), with and without
     |disc_diff| partial.

Outputs
-------
  results/phase1e_wthor_scale_retest.csv    (one row per 50-empty
                                              match)
  results/phase1e_wthor_scale_retest.json   (aggregates + summary)
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from othello_utils import BLACK, N, OthelloBoard
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep

_ensure_utf8_stdio()


_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


def _d4_only_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = 2 if irrep == "E" else 1
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def _spectral(state: np.ndarray) -> dict:
    sig = state.astype(float)
    occ = sig ** 2
    return {
        "a1_minus_energy": float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2),
        "b1_minus_energy": float(np.linalg.norm(project_irrep(sig, "B1-")) ** 2),
        "b2_minus_energy": float(np.linalg.norm(project_irrep(sig, "B2-")) ** 2),
        "e_minus_energy":  float(np.linalg.norm(project_irrep(sig, "E-")) ** 2),
        "d4_a1_occupation_energy": _d4_only_energy(occ, "A1"),
        "d4_e_occupation_energy":  _d4_only_energy(occ, "E"),
    }


def _state_to_bitboards(state: np.ndarray, side_to_move: int) -> tuple[int, int]:
    player_bb = 0
    opp_bb = 0
    for i in range(N):
        v = int(state[i])
        if v == side_to_move:
            player_bb |= 1 << i
        elif v == -side_to_move:
            opp_bb |= 1 << i
    return player_bb, opp_bb


def _canonical_key(state: np.ndarray, side_to_move: int) -> tuple[int, int]:
    """Canonical (player_bb, opponent_bb) matching the tasklist's
    key convention.  Uses ``reversi_misc.board_unique`` — same helper
    used to index the 2587-row tasklist — so the key space is
    guaranteed compatible.
    """
    pb, ob = _state_to_bitboards(state, side_to_move)
    return tuple(_ref.board_unique(pb, ob))


def _residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    X = np.concatenate([x.reshape(-1, 1), np.ones((len(y), 1))], axis=1)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ coef


def _load_tasklist(path: Path) -> dict[tuple[int, int], dict]:
    """Load the tasklist keyed by canonical (pb, ob) bitboard tuples."""
    out: dict[tuple[int, int], dict] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pb, ob = _ref.obf_to_bitboards(r["obf"])
            key = tuple(_ref.board_unique(pb, ob))
            out[key] = r
    return out


def _load_archive_summary_by_key(
    path: Path | None,
) -> dict[tuple[int, int], dict]:
    """Archive summary keyed by the same canonical (pb, ob) tuple."""
    if path is None or not path.exists():
        return {}
    out: dict[tuple[int, int], dict] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pb, ob = _ref.obf_to_bitboards(r["parent_obf"])
            key = tuple(_ref.board_unique(pb, ob))
            out[key] = r
    return out




def _iterate_50empty(pgn_path: Path):
    """Yield (state, side_to_move, game_index) for every position
    with exactly 50 empties across every replayable game."""
    games = parse_pgn_file(pgn_path)
    for gi, g in enumerate(games):
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        side = BLACK
        for ply, st in enumerate(states):
            if ply > 0:
                side = -move_log[ply - 1]["side"]
            if int(np.sum(st == 0)) == 50:
                yield gi, ply, st, side
                # Only take first-encountered 50-empty per game to
                # stay aligned with §2c.3 convention.
                break


def analyse(
    pgn_paths: list[Path],
    tasklist_path: Path,
    archive_summary_path: Path | None,
    out_csv: Path,
    out_json: Path,
) -> dict:
    tasklist = _load_tasklist(tasklist_path)
    archive = _load_archive_summary_by_key(archive_summary_path)
    print(f"tasklist rows: {len(tasklist)}")
    print(f"archive summary rows: {len(archive)}")

    matches: list[dict] = []
    n_candidate_positions = 0
    per_corpus_counts: dict[str, dict] = {}
    for pgn in pgn_paths:
        print(f"scanning {pgn.name} ...")
        corpus_match = 0
        corpus_candidate = 0
        for gi, ply, st, side in _iterate_50empty(pgn):
            n_candidate_positions += 1
            corpus_candidate += 1
            key = _canonical_key(st, side)
            if key not in tasklist:
                continue
            corpus_match += 1
            row = tasklist[key]
            spec = _spectral(st)
            bcount = int(np.sum(st == 1))
            wcount = int(np.sum(st == -1))
            # disc_diff_player_minus_opp
            dd = (bcount - wcount) if side == BLACK else (wcount - bcount)
            rec = {
                "corpus": pgn.stem,
                "game": gi,
                "ply": ply,
                "obf_tasklist": row["obf"],
                "edax_score_preproof": int(row["score"]),
                "edax_alpha": int(row["alpha"]),
                "edax_beta": int(row["beta"]),
                "count_wthor": int(row["count"]),
                "disc_diff_player_minus_opp": dd,
                **spec,
            }
            arc = archive.get(key)
            if arc is not None:
                def _f(k):
                    v = arc.get(k, "")
                    if v == "" or v is None:
                        return None
                    try:
                        return float(v)
                    except ValueError:
                        return None
                rec["archive_mean_lb"] = _f("mean_lb")
                rec["archive_mean_ub"] = _f("mean_ub")
                rec["archive_median_lb"] = _f("median_lb")
            matches.append(rec)
        per_corpus_counts[pgn.stem] = {
            "candidate_50empty_positions": corpus_candidate,
            "tasklist_matches": corpus_match,
        }
        print(
            f"  {corpus_candidate} candidate 50-empties, "
            f"{corpus_match} matched tasklist"
        )

    n_matched = len(matches)
    print(f"\ntotal 50-empty candidates: {n_candidate_positions}")
    print(f"total tasklist matches:    {n_matched}")

    # Write per-match CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    if matches:
        fields = list(matches[0].keys())
        for m in matches:
            for k in m.keys():
                if k not in fields:
                    fields.append(k)
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for m in matches:
                writer.writerow(m)

    # Correlations
    summary: dict = {
        "tasklist_path": str(tasklist_path),
        "archive_summary_path": (
            str(archive_summary_path) if archive_summary_path else None
        ),
        "per_corpus_counts": per_corpus_counts,
        "n_total_50empty_candidates": n_candidate_positions,
        "n_tasklist_matches": n_matched,
    }
    if n_matched >= 20:
        obs_keys = [
            "a1_minus_energy", "b1_minus_energy", "b2_minus_energy",
            "e_minus_energy",
            "d4_a1_occupation_energy", "d4_e_occupation_energy",
        ]
        target_keys = ["edax_score_preproof"]
        if any("archive_mean_lb" in m for m in matches):
            target_keys.append("archive_mean_lb")
        correlations: dict = {}
        dd = np.abs(np.array(
            [m["disc_diff_player_minus_opp"] for m in matches],
            dtype=float,
        ))
        for obs in obs_keys:
            x = np.array([m[obs] for m in matches], dtype=float)
            for tg in target_keys:
                y = np.array([m.get(tg) for m in matches], dtype=float)
                mask = ~np.isnan(y) & ~np.isnan(x)
                if mask.sum() < 10:
                    continue
                xr, yr = x[mask], y[mask]
                sp = spearmanr(xr, yr)
                # partial
                if dd[mask].std() > 0:
                    xp = _residualize(xr, dd[mask])
                    yp = _residualize(yr, dd[mask])
                    sp_p = spearmanr(xp, yp)
                    partial = {
                        "rho": float(sp_p.statistic),
                        "p": float(sp_p.pvalue),
                    }
                else:
                    partial = None
                correlations[f"{obs}__vs__{tg}"] = {
                    "raw_rho": float(sp.statistic),
                    "raw_p": float(sp.pvalue),
                    "partial_rho": partial["rho"] if partial else None,
                    "partial_p": partial["p"] if partial else None,
                    "n": int(mask.sum()),
                }
        summary["correlations"] = correlations
    else:
        summary["correlations"] = None
        summary["note"] = (
            f"N = {n_matched} matches; below the 20-row threshold "
            f"for reporting aggregate Spearmans."
        )

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nwrote {out_csv}")
    print(f"wrote {out_json}")

    # Stdout highlights
    if summary.get("correlations"):
        print(f"\n=== Phase 1e wthor-scale retest (N = {n_matched}) ===")
        for key, info in summary["correlations"].items():
            p = info["partial_rho"] if info["partial_rho"] is not None else 0.0
            print(
                f"  {key:52s}  raw {info['raw_rho']:+.3f}  "
                f"partial {p:+.3f}  N = {info['n']}"
            )
        print("\n§2c.3 reference: Spearman(A1- , edax_score) = +0.820 at N = 15.")
    return summary


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    default_pgns = [
        research_dir.parent / "dataset" / fname
        for fname in [
            "liveothello_Barcelona_EGP_2026.pgn",
            "liveothello_World_Championships_2005.pgn",
            "liveothello-2026-APR.pgn",
            "liveothello_2025_all.pgn",
        ]
    ]
    default_tasklist = (
        research_dir.parent / "dataset"
        / "reversi_scripts" / "empty50_tasklist_edax_knowledge.csv"
    )
    default_archive = (
        research_dir.parent / "results" / "phase1d_archive_summary.csv"
    )
    default_csv = (
        research_dir.parent / "results" / "phase1e_wthor_scale_retest.csv"
    )
    default_json = (
        research_dir.parent / "results" / "phase1e_wthor_scale_retest.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: scan all 4 committed PGNs, write per-match CSV + JSON.
  python research/phase1e_wthor_scale_retest.py

  # Custom corpus set.
  python research/phase1e_wthor_scale_retest.py \\
      --pgn ../dataset/liveothello_Barcelona_EGP_2026.pgn

reading the output:
  'correlations' reports Spearman raw + partial rho for each of the
  6 spectral observables (A1-, B1-, B2-, E-, D4-A1(s^2), D4-E(s^2))
  against edax_score_preproof and (if available) archive_mean_lb.
  Headline comparison: does ρ(A1-, edax) from §2c.3's N=15 survive
  at larger N?  If so this tightens §2c.3 into CONFIRMED.
""",
    )
    p.add_argument(
        "--pgn", type=Path, action="append", default=None,
        help="PGN to scan.  Repeatable.  Default: 4 committed liveothello "
             "corpora.",
    )
    p.add_argument("--tasklist", type=Path, default=default_tasklist)
    p.add_argument(
        "--archive-summary", type=Path, default=default_archive,
        help="Optional phase1d_archive_summary.csv for archive_mean_lb "
             "joins.",
    )
    p.add_argument("--out-csv", type=Path, default=default_csv)
    p.add_argument("--out-json", type=Path, default=default_json)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    pgns = args.pgn or [
        Path(__file__).resolve().parent.parent / "dataset" / fname
        for fname in [
            "liveothello_Barcelona_EGP_2026.pgn",
            "liveothello_World_Championships_2005.pgn",
            "liveothello-2026-APR.pgn",
            "liveothello_2025_all.pgn",
        ]
    ]
    pgns = [p for p in pgns if p.exists()]
    if not pgns:
        print("no input PGN files found", file=sys.stderr)
        return 2
    analyse(
        pgns, args.tasklist, args.archive_summary,
        args.out_csv, args.out_json,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
