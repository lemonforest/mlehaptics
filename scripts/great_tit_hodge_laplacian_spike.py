"""Gap #1 spike — Hodge-Laplacian / Betti-trajectory across great-tit ontogenetic stages.

Dataset: Wild, Alarcón-Nieto & Aplin (2024), Dryad DOI 10.5061/dryad.x95x69ps8.
Branch: research/comparative-ethology-age-sociality (commit 1962bad6).
Scope:   per-stage simplicial complex from co-occurrence of RFID feeder visits;
         compute Betti numbers B_0, B_1, B_2 + top eigenvalues of Hodge Laplacians
         L_0, L_1, L_2; falsify the juvenile-B_1-peak prediction under a stage-
         label-permutation null (n=1000).

Stage definition (per dataset README + Behavioral Ecology companion paper):
    The dataset has a binary age class (adult / juvenile) in species_age.txt and
    four observational seasons (summer, autumn, winter, spring). Juveniles are
    first-year birds tracked across all four seasons; adults are >1y birds
    sampled in the same windows. The natural ontogeny trajectory is therefore:
       juvenile-summer  (immediate post-fledging dispersal)
       juvenile-autumn  (first-flock formation)
       juvenile-winter  (territorial settling)
       juvenile-spring  (sexually-mature, pre-breeding)
       adult-pooled     (contrast cohort, all seasons pooled)
    We stratify into 5 stage-slices and ask whether B_1 (cycle content) peaks in
    one of the juvenile slices vs the adult contrast.

Co-occurrence definition:
    Two birds (i, j) share an edge if they visited the SAME feeder location
    within a SAME-FLOCK time window of <= delta_t seconds, in the slice.
    Edge weight = count of such co-occurrences. delta_t = 60 s (asnipe gmmevents
    default order; conservative — same-flock co-presence at a single antenna).
    Triangles are 2-simplices iff all 3 pairs co-occur above the threshold (flag
    complex). 2-simplices form when 3 birds are simultaneously at the same
    feeder within delta_t.

Falsifiability:
    H0: B_1 within stages is indistinguishable from B_1 under random stage-label
        permutation (n=1000, p < 0.05 threshold).
    H1: B_1 in at least one juvenile slice significantly exceeds the adult
        contrast and the permutation null.

Output: NDJSON to docs/srmech/notes/great_tit_hodge_laplacian_spike_results_2026-05-13.ndjson
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import gudhi

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "great_tit_wild_2024"
OUT_NDJSON = REPO / "docs" / "srmech" / "notes" / "great_tit_hodge_laplacian_spike_results_2026-05-13.ndjson"

# ---------------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------------

SEASONS = ("summer", "autumn", "winter", "spring")

# Stage slices used in the analysis. Each slice = list of (season, age_filter).
# age_filter ∈ {"juvenile", "adult", "any"}.
STAGES: dict[str, list[tuple[str, str]]] = {
    "juvenile-summer": [("summer", "juvenile")],
    "juvenile-autumn": [("autumn", "juvenile")],
    "juvenile-winter": [("winter", "juvenile")],
    "juvenile-spring": [("spring", "juvenile")],
    "adult-pooled":    [("summer", "adult"), ("autumn", "adult"),
                         ("winter", "adult"), ("spring", "adult")],
}


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_species_age() -> dict[str, str]:
    df = pd.read_csv(DATA / "species_age.txt", sep="\t")
    # Columns: Ring Species Pit Age_in_2020
    # Note: Pit is the PIT-tag column (matches Mill.data.*.PIT)
    pit2age: dict[str, str] = {}
    for _, row in df.iterrows():
        pit2age[str(row["Pit"]).strip()] = str(row["Age_in_2020"]).strip().lower()
    return pit2age


def load_season(season: str) -> pd.DataFrame:
    path = DATA / f"Mill.data.{season}.txt"
    # File format varies: summer is space-separated R-style, autumn/winter/spring
    # are comma-separated with quoted strings. Detect by sniffing the header.
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        header = fh.readline()
    sep = "," if "," in header else r"\s+"
    df = pd.read_csv(path, sep=sep, engine="python",
                     quotechar='"', index_col=0)
    df = df.reset_index(drop=True)
    # Strip quotes from column names (pandas keeps them when sep != ',')
    df.columns = [c.strip().strip('"') for c in df.columns]
    # Strip residual quoting on string fields if any survived
    for col in ("Antenna", "PIT", "location"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.strip('"')
    return df


# ---------------------------------------------------------------------------
# Edge construction
# ---------------------------------------------------------------------------

def parse_datetime(series: pd.Series) -> pd.Series:
    """Mill.data uses yymmddHHMMSS as a single integer string."""
    s = series.astype(str).str.zfill(12)
    return pd.to_datetime(s, format="%y%m%d%H%M%S", errors="coerce")


def co_occurrence_edges(
    df: pd.DataFrame,
    delta_t_seconds: int,
) -> dict[frozenset[str], int]:
    """For each (location, antenna), find all pairs of distinct PITs whose visits
    fall within delta_t seconds. Return weighted edge dict.

    Computes the FULL co-occurrence graph across all PITs in the dataset, ignoring
    age-class filtering — that is applied downstream. This is the heavy step; cache
    its output per season.
    """
    if df.empty:
        return {}
    df = df.copy()
    df["dt"] = parse_datetime(df["Date.Time"])
    df = df.dropna(subset=["dt"]).sort_values(["location", "Antenna", "dt"])

    edges: dict[frozenset[str], int] = defaultdict(int)
    delta = pd.Timedelta(seconds=delta_t_seconds)

    for (_loc, _ant), grp in df.groupby(["location", "Antenna"], sort=False):
        dts = grp["dt"].to_numpy()
        pits = grp["PIT"].to_numpy()
        n = len(dts)
        j = 0
        for i in range(n):
            if j <= i:
                j = i + 1
            while j < n and (dts[j] - dts[i]) <= delta:
                if pits[i] != pits[j]:
                    edges[frozenset((pits[i], pits[j]))] += 1
                j += 1
    return edges


_SEASON_EDGE_CACHE: dict[tuple[str, int], dict[frozenset[str], int]] = {}


def cached_season_edges(season: str, delta_t_seconds: int) -> dict[frozenset[str], int]:
    """Cache: load season DF once, compute co-occurrence once. Re-used across perms."""
    key = (season, delta_t_seconds)
    if key not in _SEASON_EDGE_CACHE:
        df = load_season(season)
        _SEASON_EDGE_CACHE[key] = co_occurrence_edges(df, delta_t_seconds)
        del df
    return _SEASON_EDGE_CACHE[key]


def stage_edges(
    stage: str,
    pit2age: dict[str, str],
    delta_t_seconds: int = 60,
) -> tuple[dict[frozenset[str], int], list[str]]:
    """Filter cached co-occurrence by stage definition.

    A stage = list of (season, age_filter). For each edge in the cached season
    graph, keep it iff BOTH endpoints' age class matches the slice's age_filter.
    """
    slices = STAGES[stage]
    all_edges: dict[frozenset[str], int] = defaultdict(int)
    pits_seen: set[str] = set()
    for season, age_filter in slices:
        allowed = {pit for pit, age in pit2age.items() if age == age_filter}
        season_edges = cached_season_edges(season, delta_t_seconds)
        for e, w in season_edges.items():
            a, b = tuple(e)
            if a in allowed and b in allowed:
                all_edges[e] += w
                pits_seen.add(a)
                pits_seen.add(b)
    return dict(all_edges), sorted(pits_seen)


# ---------------------------------------------------------------------------
# Simplicial complex + Hodge Laplacians
# ---------------------------------------------------------------------------

def threshold_edges(
    edges: dict[frozenset[str], int],
    percentile: float,
) -> set[frozenset[str]]:
    if not edges:
        return set()
    weights = np.array(list(edges.values()))
    cut = np.percentile(weights, percentile)
    return {e for e, w in edges.items() if w >= cut}


def build_flag_complex(
    edges: set[frozenset[str]],
    nodes: list[str],
    max_dim: int = 2,
) -> gudhi.SimplexTree:
    """Vietoris-Rips / flag complex up to triangles."""
    st = gudhi.SimplexTree()
    pit2idx = {p: i for i, p in enumerate(nodes)}
    for p in nodes:
        st.insert([pit2idx[p]], filtration=0.0)
    for e in edges:
        i, j = (pit2idx[p] for p in e)
        st.insert([i, j], filtration=1.0)
    # Expand to flag complex up to max_dim
    st.expansion(max_dim)
    return st


def boundary_matrices(
    st: gudhi.SimplexTree,
    max_dim: int = 2,
) -> tuple[list[list[tuple[int, ...]]], list[sp.csr_matrix]]:
    """Return (simplices_by_dim, boundary_matrices) where boundaries[k] = B_k
    mapping C_k -> C_{k-1}. B_0 is shape (1, num_vertices) by convention is
    omitted; we use B_1 (edges -> vertices) and B_2 (triangles -> edges).
    """
    simplices_by_dim: list[list[tuple[int, ...]]] = [[] for _ in range(max_dim + 1)]
    for simplex, _filtration in st.get_simplices():
        d = len(simplex) - 1
        if d <= max_dim:
            simplices_by_dim[d].append(tuple(sorted(simplex)))
    for d in range(max_dim + 1):
        simplices_by_dim[d].sort()

    idx_maps: list[dict[tuple[int, ...], int]] = [
        {s: i for i, s in enumerate(simplices_by_dim[d])} for d in range(max_dim + 1)
    ]

    boundaries: list[sp.csr_matrix] = []
    for k in range(1, max_dim + 1):
        rows, cols, data = [], [], []
        for j, sk in enumerate(simplices_by_dim[k]):
            for i_skip in range(k + 1):
                face = sk[:i_skip] + sk[i_skip + 1:]
                if face in idx_maps[k - 1]:
                    rows.append(idx_maps[k - 1][face])
                    cols.append(j)
                    data.append((-1) ** i_skip)
        nrows = len(simplices_by_dim[k - 1])
        ncols = len(simplices_by_dim[k])
        boundaries.append(sp.csr_matrix((data, (rows, cols)), shape=(nrows, ncols)))
    return simplices_by_dim, boundaries


def hodge_laplacians(
    simplices_by_dim: list[list[tuple[int, ...]]],
    boundaries: list[sp.csr_matrix],
    max_dim: int = 2,
) -> list[sp.csr_matrix]:
    """L_k = B_{k+1} B_{k+1}^T + B_k^T B_k where B_k : C_k -> C_{k-1}.

    boundaries[0] = B_1 (edges -> vertices),  shape (n_v, n_e)
    boundaries[1] = B_2 (triangles -> edges), shape (n_e, n_t)
    L_0 = B_1 B_1^T                              (graph Laplacian)
    L_1 = B_2 B_2^T + B_1^T B_1
    L_2 = B_3 B_3^T + B_2^T B_2; here B_3 = 0    (top dimension)
    """
    laplacians: list[sp.csr_matrix] = []
    for k in range(max_dim + 1):
        n_k = len(simplices_by_dim[k])
        L_parts: list[sp.csr_matrix] = []
        # Up term: B_{k+1} B_{k+1}^T  -- requires boundaries[k] = B_{k+1} to exist
        if k < max_dim and k < len(boundaries):
            Bup = boundaries[k]  # this is B_{k+1}
            if Bup.shape[0] == n_k:
                L_parts.append((Bup @ Bup.T).tocsr())
        # Down term: B_k^T B_k -- requires boundaries[k-1] = B_k to exist
        if k >= 1 and (k - 1) < len(boundaries):
            Bdown = boundaries[k - 1]  # this is B_k
            if Bdown.shape[1] == n_k:
                L_parts.append((Bdown.T @ Bdown).tocsr())
        if not L_parts:
            L = sp.csr_matrix((max(1, n_k), max(1, n_k)), dtype=float)
        else:
            L = L_parts[0]
            for part in L_parts[1:]:
                L = L + part
        laplacians.append(L.tocsr())
    return laplacians


def betti_from_boundaries(
    simplices_by_dim: list[list[tuple[int, ...]]],
    boundaries: list[sp.csr_matrix],
    max_dim: int,
) -> list[int]:
    """Compute Betti numbers via boundary-matrix rank (Euler-style).

    B_k = n_k - rank(B_k) - rank(B_{k+1})
    where B_k: C_k -> C_{k-1} (boundaries[k-1] in our 0-indexed list) and
          B_{k+1}: C_{k+1} -> C_k (boundaries[k]).

    For B_0: B_0 = n_0 - rank(B_1)  (rank(B_0) = 0 by convention)
    For B_k (k = max_dim): B_k = n_k - rank(B_k)  (no B_{k+1} above)
    """
    bettis: list[int] = []
    ranks: list[int] = [0]  # rank(B_0) = 0 by convention (no -1 simplices)
    for k in range(1, max_dim + 1):
        Bk = boundaries[k - 1]
        if Bk.shape[1] == 0 or Bk.shape[0] == 0:
            ranks.append(0)
        else:
            # Dense rank — fast for our sizes (max ~900 triangles)
            ranks.append(int(np.linalg.matrix_rank(Bk.toarray().astype(float))))
    # B_k = n_k - rank(B_k from below) - rank(B_{k+1} from above)
    for k in range(max_dim + 1):
        n_k = len(simplices_by_dim[k])
        rank_below = ranks[k] if k <= max_dim else 0
        rank_above = ranks[k + 1] if (k + 1) <= max_dim else 0
        bettis.append(max(0, n_k - rank_below - rank_above))
    return bettis


def betti_from_laplacian(L: sp.csr_matrix, tol: float = 1e-8) -> int:
    """Legacy single-Laplacian Betti via dense eigvalsh."""
    n = L.shape[0]
    if n == 0:
        return 0
    eigvals = np.linalg.eigvalsh(L.toarray().astype(float))
    return int(np.sum(np.abs(eigvals) < tol))


def top_eigenvalues(L: sp.csr_matrix, k: int = 10) -> list[float]:
    n = L.shape[0]
    if n == 0:
        return []
    eigvals = np.linalg.eigvalsh(L.toarray().astype(float))
    return sorted(float(v) for v in eigvals)[-k:]


# ---------------------------------------------------------------------------
# Permutation null
# ---------------------------------------------------------------------------

def permute_stage_labels(
    pit2age: dict[str, str],
    rng: np.random.Generator,
) -> dict[str, str]:
    pits = list(pit2age.keys())
    ages = list(pit2age.values())
    rng.shuffle(ages)
    return dict(zip(pits, ages))


# ---------------------------------------------------------------------------
# Main spike
# ---------------------------------------------------------------------------

def run_observed(
    pit2age: dict[str, str],
    delta_t: int,
    percentile: float,
    max_dim: int,
    top_k: int,
) -> dict[str, dict]:
    """Compute observed per-stage Betti + top eigenvalues."""
    out: dict[str, dict] = {}
    for stage in STAGES:
        t0 = time.time()
        edges, nodes = stage_edges(stage, pit2age, delta_t)
        n_birds = len(nodes)
        if n_birds < 3:
            out[stage] = {
                "n_individuals": n_birds,
                "n_edges_total": len(edges),
                "skipped": "insufficient_birds",
            }
            continue
        kept_edges = threshold_edges(edges, percentile)
        st = build_flag_complex(kept_edges, nodes, max_dim=max_dim)
        simplices_by_dim, boundaries = boundary_matrices(st, max_dim=max_dim)
        # Fast-path Betti (boundary-rank) AND Laplacian spectra (top-k via eigvalsh)
        bettis = betti_from_boundaries(simplices_by_dim, boundaries, max_dim)
        laplacians = hodge_laplacians(simplices_by_dim, boundaries, max_dim=max_dim)
        eigs = [top_eigenvalues(L, k=top_k) for L in laplacians]
        n_simplices = [len(simplices_by_dim[k]) for k in range(max_dim + 1)]
        out[stage] = {
            "n_individuals": n_birds,
            "n_edges_total": len(edges),
            "n_edges_kept": len(kept_edges),
            "n_simplices_by_dim": n_simplices,
            "betti": bettis,
            "top_eigenvalues_by_dim": eigs,
            "elapsed_s": round(time.time() - t0, 2),
        }
        print(f"[OBS] {stage:22s}  n_ind={n_birds:4d}  edges={len(kept_edges):5d}  "
              f"simplices={n_simplices}  betti={bettis}  ({time.time()-t0:.1f}s)")
    return out


def run_permutation_null(
    pit2age: dict[str, str],
    delta_t: int,
    percentile: float,
    max_dim: int,
    n_perm: int,
    seed: int,
) -> dict[str, dict[str, list[float]]]:
    """Permute the age labels across PITs and recompute Betti per stage."""
    rng = np.random.default_rng(seed)
    null: dict[str, dict[str, list[float]]] = {
        stage: {"B0": [], "B1": [], "B2": []} for stage in STAGES
    }
    for p in range(n_perm):
        t0 = time.time()
        try:
            permuted = permute_stage_labels(pit2age, rng)
            for stage in STAGES:
                edges, nodes = stage_edges(stage, permuted, delta_t)
                if len(nodes) < 3:
                    for k_lbl in ("B0", "B1", "B2"):
                        null[stage][k_lbl].append(float("nan"))
                    continue
                kept_edges = threshold_edges(edges, percentile)
                st = build_flag_complex(kept_edges, nodes, max_dim=max_dim)
                simplices_by_dim, boundaries = boundary_matrices(st, max_dim=max_dim)
                bettis = betti_from_boundaries(simplices_by_dim, boundaries, max_dim)
                for k, k_lbl in enumerate(("B0", "B1", "B2")):
                    if k <= max_dim:
                        null[stage][k_lbl].append(bettis[k])
        except Exception as exc:  # noqa: BLE001
            print(f"[PERM] {p+1} FAILED: {type(exc).__name__}: {exc}", flush=True)
            # Pad with NaN so per-stage list lengths stay aligned
            for stage in STAGES:
                for k_lbl in ("B0", "B1", "B2"):
                    if len(null[stage][k_lbl]) < p + 1:
                        null[stage][k_lbl].append(float("nan"))
        if (p + 1) % 25 == 0 or p == 0 or p == 4 or p == 9:
            print(f"[PERM] {p+1}/{n_perm}  ({time.time()-t0:.2f}s/perm)", flush=True)
    return null


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta-t", type=int, default=60,
                    help="Co-occurrence window in seconds (default 60)")
    ap.add_argument("--percentile", type=float, default=70.0,
                    help="Edge-weight percentile threshold (default 70 = top 30 pct)")
    ap.add_argument("--max-dim", type=int, default=2,
                    help="Max simplex dimension (default 2 = triangles)")
    ap.add_argument("--top-k", type=int, default=10,
                    help="How many top eigenvalues to record per Laplacian (default 10)")
    ap.add_argument("--n-perm", type=int, default=1000,
                    help="Permutation null draws (default 1000)")
    ap.add_argument("--seed", type=int, default=20260513)
    ap.add_argument("--quick", action="store_true",
                    help="Run with n_perm=50 for sanity check")
    args = ap.parse_args()

    if args.quick:
        args.n_perm = 50

    pit2age = load_species_age()
    n_ad = sum(1 for v in pit2age.values() if v == "adult")
    n_juv = sum(1 for v in pit2age.values() if v == "juvenile")
    print(f"Loaded species_age: {len(pit2age)} PITs ({n_ad} adult, {n_juv} juvenile)")

    print("\n=== Observed Betti + Hodge spectra per stage ===")
    observed = run_observed(pit2age, args.delta_t, args.percentile,
                            args.max_dim, args.top_k)

    print("\n=== Permutation null (label-shuffle on age, n=%d) ===" % args.n_perm)
    null = run_permutation_null(pit2age, args.delta_t, args.percentile,
                                 args.max_dim, args.n_perm, args.seed)

    # Compute p-values per (stage, statistic) and emit NDJSON
    OUT_NDJSON.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    git_commit = "1962bad6"  # branch HEAD at spike start

    records: list[dict] = []
    # Header record (provenance)
    records.append({
        "record_type": "header",
        "spike_id": "gap-1-hodge-laplacian-great-tit-2026-05-13",
        "dataset_doi": "10.5061/dryad.x95x69ps8",
        "dataset_citation": "Wild, Alarcón-Nieto & Aplin (2024). Behav Ecol 35(2):arae011.",
        "branch": "research/comparative-ethology-age-sociality",
        "branch_head_at_spike_start": git_commit,
        "stages": list(STAGES.keys()),
        "stage_definition": "season × age-class slice of RFID feeder co-presence",
        "co_occurrence_window_seconds": args.delta_t,
        "edge_threshold_percentile": args.percentile,
        "max_simplex_dim": args.max_dim,
        "permutation_null_n": args.n_perm,
        "permutation_label": "age_class (juvenile vs adult) shuffled across PIT tags",
        "rng_seed": args.seed,
        "timestamp_utc": timestamp,
        "toolchain": {
            "python": sys.version.split()[0],
            "gudhi": gudhi.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": __import__("scipy").__version__,
        },
    })

    # Per-stage per-statistic records
    for stage in STAGES:
        obs = observed.get(stage, {})
        if "betti" not in obs:
            records.append({
                "record_type": "stage_result",
                "stage": stage,
                "skipped": obs.get("skipped", "no_data"),
                "n_individuals": obs.get("n_individuals", 0),
            })
            continue
        for k, k_lbl in enumerate(("B0", "B1", "B2")):
            if k > args.max_dim:
                continue
            obs_val = obs["betti"][k]
            null_draws = np.array([v for v in null[stage][k_lbl]
                                   if not (isinstance(v, float) and np.isnan(v))])
            if len(null_draws) > 0:
                null_mean = float(null_draws.mean())
                null_std = float(null_draws.std())
                # Two-sided p-value: fraction of null at-or-beyond obs
                p_two_sided = float(np.mean(np.abs(null_draws - null_mean) >= abs(obs_val - null_mean)))
                p_greater = float(np.mean(null_draws >= obs_val))
            else:
                null_mean = null_std = p_two_sided = p_greater = float("nan")
            records.append({
                "record_type": "stage_result",
                "stage": stage,
                "statistic": k_lbl,
                "value": obs_val,
                "permutation_null_mean": null_mean,
                "permutation_null_std": null_std,
                "permutation_null_n": len(null_draws),
                "p_value_two_sided": p_two_sided,
                "p_value_greater": p_greater,
                "n_individuals": obs["n_individuals"],
                "n_simplices_by_dim": obs["n_simplices_by_dim"],
            })
        # Top eigenvalues per stage (one record per Laplacian)
        for k, k_lbl in enumerate(("L0", "L1", "L2")):
            if k > args.max_dim:
                continue
            records.append({
                "record_type": "stage_eigenvalues",
                "stage": stage,
                "operator": k_lbl,
                "top_eigenvalues": obs["top_eigenvalues_by_dim"][k],
            })

    with OUT_NDJSON.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, default=str) + "\n")
    print(f"\nWrote {len(records)} records to {OUT_NDJSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
