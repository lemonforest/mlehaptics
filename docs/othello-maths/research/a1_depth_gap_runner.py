"""Phase 1c.4 — H9 surrogate: A1-energy vs edax d1/d20 depth-gap.

Direct analog of chess-maths §9h': Stockfish depth-1 vs depth-20
evaluation gap, correlated with A1 energy.  Chess reported
Spearman(A1 energy, |d1-d20| centipawns) = +0.452, p = 0.0005 over
55 positions.

Protocol (per position in corpus)
---------------------------------
  1. Compute A1- energy (Z2-odd magnetisation projection).
  2. Evaluate position with edax at depth 1 (fast static-ish eval).
  3. Evaluate with edax at depth 20 (deep search).
  4. depth_gap = |score_d20 - score_d1|  (unsigned, disc units).

Then Spearman(A1_minus_energy, depth_gap).  Partial correlation
controlling for disc count as a secondary test.

Walltime notes
--------------
Edax at depth 20 takes ~1-10 seconds per position on typical
hardware.  The full Barcelona corpus (2184 positions) at d=20
takes approximately 1-6 hours.  For development iteration, use
``--sample`` to limit; for the final run, omit --sample.

Blocked-on-edax behaviour
-------------------------
If the edax executable cannot be found (EDAX_PATH unset, binary
not on PATH, --edax-path not given), this script writes a
"needs_edax" JSON result and exits with status 2.  The wrapper
(``edax_wrapper.py``) prints install instructions.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import BLACK, N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio, parse_pgn_file, replay
from d4_z2 import project_irrep
from edax_wrapper import (
    EdaxNotFoundError,
    evaluate,
    resolve_edax_path,
    smoke_test,
)

_ensure_utf8_stdio()

_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


def _a1_minus_energy(sig: np.ndarray) -> float:
    return float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)


def state_to_obf(state: np.ndarray, side_to_move: int) -> str:
    player_bb = 0
    opponent_bb = 0
    for i in range(N):
        v = int(state[i])
        if v == side_to_move:
            player_bb |= 1 << i
        elif v == -side_to_move:
            opponent_bb |= 1 << i
    return _ref.bitboards_to_obf(
        player_bb, opponent_bb, player_is_black=(side_to_move == BLACK)
    )


def iterate_corpus(pgn_path: Path):
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
            yield gi, ply, st, side


def run(
    pgn_path: Path,
    edax_path: Path,
    shallow_depth: int,
    deep_depth: int,
    sample: int | None,
    results_dir: Path,
    rng_seed: int,
) -> dict:
    # Collect positions
    positions: list[dict] = []
    for gi, ply, st, side in iterate_corpus(pgn_path):
        if int(np.sum(st == 0)) == 64:
            continue  # empty board would be silly
        positions.append(
            {
                "game": gi,
                "ply": ply,
                "side_to_move": side,
                "state": st.copy(),
                "n_empties": int(np.sum(st == 0)),
            }
        )
    if sample is not None and sample < len(positions):
        rng = np.random.default_rng(rng_seed)
        idx = rng.choice(
            len(positions), size=sample, replace=False
        )
        positions = [positions[int(i)] for i in sorted(idx)]

    n = len(positions)
    print(f"evaluating {n} positions at depth {shallow_depth} and {deep_depth}")
    t0 = time.time()
    per_pos: list[dict] = []
    for i, p in enumerate(positions):
        obf = state_to_obf(p["state"], p["side_to_move"])
        try:
            shallow = evaluate(obf, shallow_depth, edax_path)
            deep = evaluate(obf, deep_depth, edax_path)
        except Exception as exc:
            print(
                f"[{i+1}/{n}] game {p['game']} ply {p['ply']}: "
                f"edax failed: {exc}",
                file=sys.stderr,
            )
            continue
        a1m = _a1_minus_energy(p["state"].astype(float))
        bcount = int(np.sum(p["state"] == BLACK))
        wcount = int(np.sum(p["state"] == -BLACK))
        per_pos.append(
            {
                "game": p["game"],
                "ply": p["ply"],
                "side_to_move": p["side_to_move"],
                "n_empties": p["n_empties"],
                "disc_diff_black_white": bcount - wcount,
                "a1_minus_energy": a1m,
                "edax_score_shallow": shallow.score,
                "edax_score_deep": deep.score,
                "depth_gap": abs(deep.score - shallow.score),
            }
        )
        if (i + 1) % 50 == 0 or (i + 1) == n:
            elapsed = time.time() - t0
            rate = (i + 1) / max(elapsed, 1e-6)
            print(
                f"  [{i+1}/{n}] elapsed {elapsed:.1f}s, "
                f"rate {rate:.2f} pos/s"
            )

    n_ok = len(per_pos)
    summary: dict = {
        "corpus": str(pgn_path),
        "edax_path": str(edax_path),
        "depth_shallow": shallow_depth,
        "depth_deep": deep_depth,
        "sample": sample,
        "n_requested": n,
        "n_evaluated": n_ok,
    }

    if n_ok >= 10:
        a1 = np.array([r["a1_minus_energy"] for r in per_pos])
        dg = np.array([r["depth_gap"] for r in per_pos])
        dd = np.array([r["disc_diff_black_white"] for r in per_pos])
        sp = spearmanr(a1, dg)
        # Partial: regress dg on |dd| and take residuals, then
        # re-correlate a1 with residuals.
        abs_dd = np.abs(dd)
        if np.std(abs_dd) > 0:
            coef = np.polyfit(abs_dd, dg, 1)
            dg_resid = dg - (coef[0] * abs_dd + coef[1])
            sp_partial = spearmanr(a1, dg_resid)
        else:
            sp_partial = None
        summary["spearman_a1_depth_gap"] = {
            "rho": float(sp.statistic),
            "pvalue": float(sp.pvalue),
        }
        if sp_partial is not None:
            summary["spearman_a1_depth_gap_partial_disc_count"] = {
                "rho": float(sp_partial.statistic),
                "pvalue": float(sp_partial.pvalue),
            }
    else:
        summary["spearman_a1_depth_gap"] = None

    results_dir.mkdir(parents=True, exist_ok=True)
    out_json = results_dir / "phase1c_a1_depth_gap.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump({**summary, "per_position": per_pos}, f, indent=2)
    out_csv = results_dir / "phase1c_a1_depth_gap_per_position.csv"
    if per_pos:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(per_pos[0].keys())
            )
            writer.writeheader()
            for r in per_pos:
                writer.writerow(r)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    default_pgn = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "liveothello_Barcelona_EGP_2026.pgn"
    )
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Smoke test: 5 random positions at d=1 and d=10.  Takes ~30 s
  # once edax is installed.
  python research/a1_depth_gap_runner.py \\
      --sample 5 --deep-depth 10

  # Full Barcelona corpus at d=1 and d=20.  Takes 1-6 hours
  # wall time depending on CPU.
  python research/a1_depth_gap_runner.py --deep-depth 20

  # Point at a non-default edax binary.
  EDAX_PATH=/opt/edax/edax research/a1_depth_gap_runner.py

prerequisites:
  edax must be installed.  Set EDAX_PATH to the binary or put
  'edax' on PATH.  See research/edax_wrapper.py --help for install
  instructions.  If the binary is not found this script writes a
  'needs_edax' JSON and exits with status 2 - the rest of the
  pipeline is unaffected.

reading the output:
  'spearman_a1_depth_gap' is the headline against chess
  +0.452 / p = 0.0005 at 55 positions.  The partial correlation
  controlling for |disc_diff| isolates the spectral contribution
  from raw imbalance.
""",
    )
    parser.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="PGN corpus.  Default: Barcelona EGP 2026.",
    )
    parser.add_argument(
        "--edax-path", type=str, default=None,
        help="Path to the edax binary.  Overrides EDAX_PATH env var.",
    )
    parser.add_argument(
        "--shallow-depth", type=int, default=1,
        help="Shallow search depth (analog of chess Stockfish d=1).  "
             "Default: 1.",
    )
    parser.add_argument(
        "--deep-depth", type=int, default=20,
        help="Deep search depth (analog of chess Stockfish d=20).  "
             "Default: 20.  Increasing this past ~22 substantially "
             "inflates walltime.",
    )
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Subsample the corpus to this many positions "
             "(deterministic given --seed).  Default: no subsample; "
             "process the full corpus.  Recommended: 5 for a smoke "
             "test, 50-200 for a pilot run.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Sampling seed when --sample is used.  Default: 42.",
    )
    parser.add_argument(
        "--results-dir", type=Path, default=default_results,
        help="Output directory.  Default: ../results/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    args.results_dir.mkdir(parents=True, exist_ok=True)
    try:
        edax_path = resolve_edax_path(args.edax_path)
    except EdaxNotFoundError as exc:
        print(f"[a1_depth_gap] {exc}", file=sys.stderr)
        # Land a placeholder result so the rest of the pipeline has
        # something to reference.
        placeholder = {
            "status": "needs_edax",
            "message": str(exc),
            "corpus": str(args.pgn),
            "depth_shallow": args.shallow_depth,
            "depth_deep": args.deep_depth,
        }
        out = args.results_dir / "phase1c_a1_depth_gap.json"
        with out.open("w", encoding="utf-8") as f:
            json.dump(placeholder, f, indent=2)
        print(f"wrote placeholder {out}")
        return 2
    if not smoke_test(edax_path):
        print(
            "[a1_depth_gap] edax smoke test failed; aborting.",
            file=sys.stderr,
        )
        return 2
    run(
        args.pgn, edax_path,
        args.shallow_depth, args.deep_depth,
        args.sample, args.results_dir, args.seed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
