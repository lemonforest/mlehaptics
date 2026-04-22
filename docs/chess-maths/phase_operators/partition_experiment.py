"""Section11.6 Phase A CLI: partition detection in phase space.

For each game in a corpus, encode every ply, compute pairwise cosine
similarity, detect phase clusters at a sweep of thresholds, and emit a
per-ply CSV with cluster assignments and partition-boundary features.

Run from phase_operators/ directory:
    python partition_experiment.py \\
        --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 \\
        [--thresholds 0.70 0.80 0.85 0.90 0.95] \\
        [--stockfish-csv ../results/stockfish_correlation/stockfish_evaluations_v2.csv] \\
        [--out PATH]
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from partition_detector import per_ply_features, run_partition_analysis
from phase_similarity import encode_640, fen_to_pos  # reuse locate_encoder


CSV_FIELDS = [
    "game_id", "ply_index", "position_fen", "threshold",
    "cluster_id", "cluster_size", "distance_to_nearest_boundary",
    "similarity_to_previous_ply", "similarity_to_next_ply",
    "similarity_to_cluster_centroid",
    "sigma_local", "stockfish_cp", "stockfish_depth_gap",
    "kappa_annihilate", "kappa_threat", "delta_v1",
]


def iter_game_plies(ndjson_path: Path):
    """Yield (ply_index, fen) in order for one game ndjson file."""
    with ndjson_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "fen" in d and "ply" in d:
                yield int(d["ply"]), d["fen"]


def load_stockfish_aggregates(csv_path: Path) -> dict:
    """Load per-move Stockfish CSV and aggregate to per-position
    (game_id, ply) -> dict of aggregates.

    Aggregation: mean across all candidate moves at that position for
    stockfish_cp, kappa_annihilate, kappa_threat, delta.
    """
    buckets: dict = defaultdict(list)
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["game_id"], int(row["ply"]))
            buckets[key].append(row)
    agg: dict = {}
    for key, rows in buckets.items():
        def _mean(col):
            vals = []
            for r in rows:
                v = r.get(col, "")
                if v == "" or v is None:
                    continue
                try:
                    vals.append(float(v))
                except ValueError:
                    continue
            if not vals:
                return None
            return sum(vals) / len(vals)
        agg[key] = {
            "stockfish_cp": _mean("stockfish_cp"),
            "kappa_annihilate": _mean("kappa_annihilate"),
            "kappa_threat": _mean("kappa_threat"),
            "delta_v1": _mean("delta"),
        }
    return agg


def encode_game(fens: list) -> np.ndarray:
    """Encode a list of FEN strings into an (n_plies, 640) matrix."""
    if not fens:
        return np.zeros((0, 640))
    rows = [encode_640(fen_to_pos(fen)) for fen in fens]
    return np.vstack(rows)


def _fmt(x):
    if x is None:
        return ""
    if isinstance(x, float):
        if x != x:  # NaN
            return ""
        return f"{x:.12f}"
    return str(x)


def run(corpus_dir: Path, thresholds: tuple, stockfish_csv: Path,
        out_path: Path, games_limit: int, verbose: bool) -> dict:
    ndjson_dir = corpus_dir / "ndjson"
    if not ndjson_dir.is_dir():
        raise FileNotFoundError(f"No ndjson/ under {corpus_dir}")
    shards = sorted(ndjson_dir.glob("game_*.ndjson"))
    if games_limit > 0:
        shards = shards[:games_limit]
    if not shards:
        raise FileNotFoundError(f"No game_*.ndjson under {ndjson_dir}")

    sf_aggregates: dict = {}
    if stockfish_csv is not None and stockfish_csv.is_file():
        sf_aggregates = load_stockfish_aggregates(stockfish_csv)
        if verbose:
            print(f"Loaded {len(sf_aggregates)} Stockfish "
                  f"per-position aggregates from {stockfish_csv.name}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    cluster_stats_by_tau: dict = {tau: {"clusters_per_game": [],
                                        "cluster_sizes": []}
                                  for tau in thresholds}
    sf_rows_populated = 0
    total_rows = 0
    total_plies_unique = 0
    games_processed = 0

    # For the continuous-drift check: collect similarity-to-previous
    # vs ply-index-modulo-cluster across all plies at each tau.
    drift_data: dict = {tau: {"sim_prev": [], "within_cluster_idx": []}
                        for tau in thresholds}

    with out_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for shard in shards:
            game_id = shard.stem  # "game_001"
            plies = list(iter_game_plies(shard))
            if not plies:
                continue
            plies.sort(key=lambda t: t[0])
            ply_indices = [p for p, _ in plies]
            fens = [f for _, f in plies]

            encodings = encode_game(fens)
            results = run_partition_analysis(encodings,
                                             thresholds=thresholds)

            games_processed += 1
            total_plies_unique += len(plies)
            if verbose:
                print(f"[{games_processed}/{len(shards)}] "
                      f"{game_id}: {len(plies)} plies encoded")

            # Accumulate cluster stats per tau.
            for tau, res in results.items():
                n_clusters = int(res.cluster_ids.max()) + 1 if \
                    res.cluster_ids.size else 0
                cluster_stats_by_tau[tau]["clusters_per_game"].append(
                    n_clusters)
                for cid in range(n_clusters):
                    size = int(np.sum(res.cluster_ids == cid))
                    cluster_stats_by_tau[tau]["cluster_sizes"].append(
                        size)

            for local_i, (ply_idx, fen) in enumerate(plies):
                sf = sf_aggregates.get((game_id, ply_idx), {})
                any_sf_populated = any(
                    sf.get(k) is not None
                    for k in ("stockfish_cp", "kappa_annihilate",
                              "kappa_threat", "delta_v1"))
                if any_sf_populated:
                    sf_rows_populated += 1

                for tau, res in results.items():
                    feats = per_ply_features(res, local_i)

                    # Collect drift datum: similarity_to_previous_ply
                    # vs the ply's index within its cluster.
                    cid = feats["cluster_id"]
                    cluster_mask = res.cluster_ids == cid
                    cluster_indices = np.where(cluster_mask)[0]
                    within_cluster_idx = int(
                        np.where(cluster_indices == local_i)[0][0])
                    sp = feats["similarity_to_previous_ply"]
                    if sp == sp:  # not NaN
                        drift_data[tau]["sim_prev"].append(sp)
                        drift_data[tau]["within_cluster_idx"].append(
                            within_cluster_idx)

                    row = {
                        "game_id": game_id,
                        "ply_index": ply_idx,
                        "position_fen": fen,
                        "threshold": f"{tau:.2f}",
                        "cluster_id": feats["cluster_id"],
                        "cluster_size": feats["cluster_size"],
                        "distance_to_nearest_boundary":
                            feats["distance_to_nearest_boundary"],
                        "similarity_to_previous_ply":
                            _fmt(feats["similarity_to_previous_ply"]),
                        "similarity_to_next_ply":
                            _fmt(feats["similarity_to_next_ply"]),
                        "similarity_to_cluster_centroid":
                            _fmt(feats[
                                "similarity_to_cluster_centroid"]),
                        "sigma_local": "",   # deferred (Section11.6.4 Phase B)
                        "stockfish_cp":
                            _fmt(sf.get("stockfish_cp")),
                        "stockfish_depth_gap": "",  # deferred (Phase B)
                        "kappa_annihilate":
                            _fmt(sf.get("kappa_annihilate")),
                        "kappa_threat":
                            _fmt(sf.get("kappa_threat")),
                        "delta_v1": _fmt(sf.get("delta_v1")),
                    }
                    writer.writerow(row)
                    total_rows += 1

    return {
        "games": games_processed,
        "plies_unique": total_plies_unique,
        "rows_written": total_rows,
        "thresholds": thresholds,
        "cluster_stats_by_tau": cluster_stats_by_tau,
        "drift_data": drift_data,
        "sf_rows_populated": sf_rows_populated,
        "out_path": out_path,
        "corpus_name": corpus_dir.name,
    }


def _stats(values):
    if not values:
        return {"mean": 0.0, "median": 0, "max": 0, "p95": 0}
    arr = np.asarray(values)
    return {
        "mean": float(arr.mean()),
        "median": int(np.median(arr)),
        "max": int(arr.max()),
        "p95": int(np.percentile(arr, 95)),
    }


def _spearman_drift(sim_prev, within_idx):
    """Spearman rho between similarity_to_previous_ply and within-
    cluster position index.

    Returns (rho, n). Drift hypothesis: if |rho| large, similarity
    decays monotonically with within-cluster position -> looks like
    drift, not partitioning.
    """
    if len(sim_prev) < 3:
        return float("nan"), len(sim_prev)
    from scipy.stats import spearmanr
    a = np.asarray(sim_prev, dtype=float)
    b = np.asarray(within_idx, dtype=float)
    if np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan"), len(sim_prev)
    rho, _ = spearmanr(a, b)
    return float(rho), len(sim_prev)


def print_summary(result: dict) -> None:
    print("\n[Section 11.6 Phase A] complete:")
    print(f"  Corpus:        {result['corpus_name']}")
    print(f"  Games:         {result['games']}")
    print(f"  Plies:         {result['plies_unique']}")
    print(f"  Thresholds swept: "
          f"{list(result['thresholds'])}")
    print("")
    print("  Per-threshold cluster statistics:")

    drift_rhos = {}
    for tau in result["thresholds"]:
        cpg = _stats(result["cluster_stats_by_tau"][tau]
                     ["clusters_per_game"])
        sz = _stats(result["cluster_stats_by_tau"][tau]
                    ["cluster_sizes"])
        print(f"  tau={tau:.2f}: clusters/game mean={cpg['mean']:.1f} "
              f"median={cpg['median']} max={cpg['max']}; "
              f"cluster_size mean={sz['mean']:.1f} "
              f"median={sz['median']} p95={sz['p95']}")
        rho, n = _spearman_drift(
            result["drift_data"][tau]["sim_prev"],
            result["drift_data"][tau]["within_cluster_idx"])
        drift_rhos[tau] = (rho, n)

    print("")
    print("  Continuous-drift check "
          "(Spearman rho(sim_to_prev, within_cluster_position)):")
    for tau, (rho, n) in drift_rhos.items():
        rs = f"{rho:+.3f}" if rho == rho else "nan"
        print(f"  tau={tau:.2f}: rho={rs} (n={n})")
    print("  (|rho| near 0 -> partitioning real; "
          "strongly positive or negative -> drift-like behavior "
          "within clusters.)")
    print("")

    # Outcome label: look for a tau where clusters/game is modest
    # (2..20) AND within-cluster drift rho is modest (|rho| < 0.3).
    label = "INDETERMINATE"
    best_tau = None
    for tau in result["thresholds"]:
        cpg_mean = _stats(result["cluster_stats_by_tau"][tau]
                          ["clusters_per_game"])["mean"]
        rho, _ = drift_rhos[tau]
        if 2.0 <= cpg_mean <= 30.0 and rho == rho and abs(rho) < 0.3:
            label = "CLEAR"
            best_tau = tau
            break
    if label != "CLEAR":
        # Check for continuous drift: any tau where ALL clusters are
        # singletons (cpg_mean ~= plies) or where drift rho is
        # strongly negative at every tau.
        all_strongly_drifting = True
        for tau in result["thresholds"]:
            rho, _ = drift_rhos[tau]
            if not (rho == rho and abs(rho) > 0.4):
                all_strongly_drifting = False
                break
        if all_strongly_drifting:
            label = "DRIFT"

    if label == "CLEAR":
        interp = (f"Clear partitions at tau={best_tau:.2f} -- "
                  f"Phase B cross-reference data acquisition is the "
                  f"next step")
    elif label == "DRIFT":
        interp = ("Continuous drift across all tau -- partition "
                  "hypothesis for the 640-dim encoder is closed")
    else:
        interp = ("Mixed behavior across tau sweep -- researcher "
                  "inspects per-threshold stats")

    print(f"  Phase A outcome: {label} -- {interp}")
    print("")
    print(f"  CSV written to: {result['out_path']}")
    print(f"  Stockfish cross-reference columns populated: "
          f"{result['sf_rows_populated']}/"
          f"{result['plies_unique']} unique plies")
    print(f"  sigma and depth-gap columns: empty "
          f"(Phase B deferred per 11.6.4/11.6.5)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--corpus", type=Path, required=True,
        help="Path to corpus directory containing ndjson/")
    parser.add_argument(
        "--thresholds", type=float, nargs="+",
        default=[0.70, 0.80, 0.85, 0.90, 0.95])
    parser.add_argument(
        "--stockfish-csv", type=Path, default=None,
        help="Optional per-move Stockfish CSV for cross-reference join")
    parser.add_argument(
        "--out", type=Path,
        default=Path("../results/phase_operator_experiments/"
                     "exp4_partitions.csv"))
    parser.add_argument("--games", type=int, default=0,
                        help="Limit to first N games (default: all)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    result = run(
        corpus_dir=args.corpus,
        thresholds=tuple(args.thresholds),
        stockfish_csv=args.stockfish_csv,
        out_path=args.out,
        games_limit=args.games,
        verbose=args.verbose,
    )
    print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
