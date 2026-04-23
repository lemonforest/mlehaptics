"""Phase 1c.3 — Edax 50-empty knowledge anchor.

The reversi-scripts repo ships
``empty50_tasklist_edax_knowledge.csv`` — 2587 D4-canonical
positions at exactly 50 empty squares, annotated with edax's
predicted game-theoretic value plus the alpha/beta search window
used.  Schema:

    obf, count, score, alpha, beta

``count``  is the WTHOR frequency (same as the opening-book file).
``score``  is edax's predicted score at the position with side-to-
           move as the player bitboard (positive = good for mover).
``alpha, beta`` is the search window; these are usually -64/64 but
           Takizawa's scripts sometimes narrow them.

This tool walks a PGN corpus, finds every position at exactly 50
empty squares, canonicalises it, and looks it up in the tasklist.
For matching positions we report

    Spearman(A1_minus_energy, edax_score)

as a lightweight anchor for the H9 spectral / perfect-play
correlation — without needing the 20 GB figshare table.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import BLACK, N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio, parse_pgn_file, replay
from opening_book_loader import canonical_key
from d4_z2 import project_irrep

_ensure_utf8_stdio()

_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


def _a1_minus_energy(sig: np.ndarray) -> float:
    return float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)


def load_tasklist(
    csv_path: Path,
) -> dict[tuple[int, int], dict]:
    """Return {(player_bb, opponent_bb) D4-canonical: row_dict}."""
    out: dict[tuple[int, int], dict] = {}
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obf = row["obf"]
            pb, ob = _ref.obf_to_bitboards(obf)
            key = tuple(_ref.board_unique(pb, ob))
            out[key] = {
                "count": int(row["count"]),
                "score": int(row["score"]),
                "alpha": int(row["alpha"]),
                "beta": int(row["beta"]),
            }
    return out


def iterate_corpus_50empty(pgn_path: Path):
    """Yield (game_idx, ply, state, side_to_move) for every position
    in the PGN corpus with exactly 50 empty squares."""
    games = parse_pgn_file(pgn_path)
    for gi, g in enumerate(games):
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        side = None
        for ply, st in enumerate(states):
            if ply == 0:
                side = BLACK
            else:
                side = -move_log[ply - 1]["side"]
            if int(np.sum(st == 0)) == 50:
                yield gi, ply, st, side


def _build_parser() -> argparse.ArgumentParser:
    default_pgn = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "liveothello_Barcelona_EGP_2026.pgn"
    )
    default_tasklist = (
        Path(__file__).resolve().parent.parent / "dataset"
        / "reversi_scripts" / "empty50_tasklist_edax_knowledge.csv"
    )
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1c_50empty_anchor.json"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: Barcelona EGP 2026 at 50 empties vs the
  # Takizawa 2587-position tasklist.
  python research/edax_knowledge_anchor.py

  # Use a different corpus or tasklist.
  python research/edax_knowledge_anchor.py \\
      --pgn dataset/other_tournament.pgn \\
      --tasklist /path/to/other_tasklist.csv

reading the output:
  'n_matches' is the number of 50-empty positions in the corpus
  that also appear in the tasklist.  If fewer than 20, the
  correlation is not reported (too few samples).  The
  'spearman_a1_vs_edax_score' correlation — when present — is the
  lightweight H9 surrogate anchor.
""",
    )
    parser.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="PGN corpus.  Default: Barcelona EGP 2026.",
    )
    parser.add_argument(
        "--tasklist", type=Path, default=default_tasklist,
        help="empty50_tasklist_edax_knowledge.csv as vendored in "
             "dataset/reversi_scripts/.  Default: that file.",
    )
    parser.add_argument(
        "--out", type=Path, default=default_results,
        help="Output JSON path (parents created).  Default: "
             "../results/phase1c_50empty_anchor.json.",
    )
    parser.add_argument(
        "--min-matches", type=int, default=20,
        help="Minimum number of (corpus, tasklist) matches required "
             "to report a correlation.  Below this, the tool reports "
             "match count only.  Default: 20.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    print(f"loading tasklist: {args.tasklist}")
    tasklist = load_tasklist(args.tasklist)
    print(f"tasklist positions: {len(tasklist)}")

    rows: list[dict] = []
    for gi, ply, st, side in iterate_corpus_50empty(args.pgn):
        key = canonical_key(st, side)
        entry = tasklist.get(key)
        if entry is None:
            rows.append(
                {
                    "game": gi,
                    "ply": ply,
                    "side_to_move": side,
                    "match": False,
                }
            )
            continue
        a1m = _a1_minus_energy(st.astype(float))
        rows.append(
            {
                "game": gi,
                "ply": ply,
                "side_to_move": side,
                "match": True,
                "wthor_count": entry["count"],
                "edax_score": entry["score"],
                "edax_alpha": entry["alpha"],
                "edax_beta": entry["beta"],
                "a1_minus_energy": a1m,
            }
        )

    matched = [r for r in rows if r["match"]]
    n_corpus = len(rows)
    n_match = len(matched)
    summary: dict = {
        "corpus": str(args.pgn),
        "tasklist": str(args.tasklist),
        "n_tasklist_entries": len(tasklist),
        "n_50empty_positions_in_corpus": n_corpus,
        "n_matches": n_match,
        "match_rate": n_match / max(n_corpus, 1),
    }

    if n_match >= args.min_matches:
        a1 = np.array([r["a1_minus_energy"] for r in matched])
        edax = np.array([r["edax_score"] for r in matched])
        sp = spearmanr(a1, edax)
        summary["spearman_a1_vs_edax_score"] = {
            "rho": float(sp.statistic),
            "pvalue": float(sp.pvalue),
        }
    else:
        summary["spearman_a1_vs_edax_score"] = None
        summary["note"] = (
            f"only {n_match} matches; "
            f"below --min-matches={args.min_matches}, so correlation "
            f"not reported"
        )

    with args.out.open("w", encoding="utf-8") as f:
        json.dump({**summary, "per_position": rows}, f, indent=2)

    print(
        f"50-empty positions in corpus: {n_corpus}, "
        f"matches in tasklist: {n_match} "
        f"({100.0 * summary['match_rate']:.1f}%)"
    )
    if summary["spearman_a1_vs_edax_score"] is not None:
        r = summary["spearman_a1_vs_edax_score"]
        print(
            f"Spearman(A1- energy, edax_score) = "
            f"{r['rho']:+.3f}, p={r['pvalue']:.2e}"
        )
    else:
        print(summary["note"])
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
