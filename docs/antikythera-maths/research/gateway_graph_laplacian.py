"""Gateway-graph Laplacian — Fiedler-partition vs empirical low-Δv ITN accessibility.

Research prototype for notebook §12.5 (post-§12.4). Tests the v0.17.x
research thesis from notebook §12.3:

    Does the gateway-graph Laplacian's Fiedler partition agree with
    empirical low-Δv accessibility classes?

If yes, a pure-spectral query becomes a fast first-pass filter before the
costly Dijkstra search in :func:`ephemerides_spectral.bridge.find_itn_chains`.

Method
======

1. **Graph construction.** Vertices: heliocentric bodies (planets + dwarf
   + asteroids; Sun excluded — it is the central potential, not a transit
   node; moons excluded — no parent-frame Δv model in v0.17.0). Edges:
   complete graph on the 13 vertices. Two edge weightings tested:

   * ``w_dv`` — inverse Hohmann Δv: ``w_ij = 1 / (Δv_ij + ε)``. Cheaper
     transfers ⇒ stronger graph edges. Most directly aligned with the
     empirical metric we are testing against.
   * ``w_syn`` — inverse synodic period: ``w_ij = 1 / T_syn_ij``. Short
     synodic period ⇒ frequent Hohmann windows. A *cadence* metric
     orthogonal to ``w_dv`` (which is a *cost* metric).

2. **Spectral predictor.** Combinatorial graph Laplacian L = D - W.
   Compute eigendecomposition; extract Fiedler vector f₂ (eigenvector of
   the second-smallest eigenvalue λ₂). Two predictors:

   * **Fiedler partition** — sign of f₂ bipartitions the vertex set;
     predict within-partition pairs have cheaper chains than across-
     partition pairs.
   * **Fiedler distance** — ``d_F(i, j) = |f₂[i] - f₂[j]|`` is a 1-D
     Euclidean spectral embedding distance; predict it correlates with
     empirical min-Δv across all C(13, 2) = 78 pairs.

3. **Empirical ground truth.** For each unordered pair, call
   :func:`bridge.find_itn_chains` over a 50-yr window at J2000 with
   ``max_legs=3, dv_budget_kms=30, threshold=0.1``; record
   ``min(total_dv_kms)`` (or +inf if no chain in budget).

4. **Validation metrics.** Spearman rank correlation (predictor vs
   observed); confusion matrix on a median split of observed Δv vs
   Fiedler-partition membership.

Outputs
=======

* Console: numerical verdict line.
* PNG figures in ``docs/antikythera-maths/figures/``:
   * ``gateway_laplacian_fiedler_dv.png`` — scatter Fiedler-distance vs
     observed min-Δv, colour by partition pair (within / across).
   * ``gateway_laplacian_partition.png`` — bar chart Fiedler-vector
     entries by body, colour by partition sign.

The script is self-contained: ``python gateway_graph_laplacian.py`` from
anywhere with the project's Python environment.

Author: research subagent / 2026-05-06.
"""

from __future__ import annotations

import io
import itertools
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Console encoding: ensure UTF-8 stdout on Windows (default cp1252 chokes
# on Greek letters λ, ρ in the verdict line).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# --------------------------------------------------------------------------
# Project imports — bridge for the empirical ground-truth Dijkstra search,
# itn_window primitives for the closed-form Hohmann edge weights.
# --------------------------------------------------------------------------
from ephemerides_spectral import bridge
from ephemerides_spectral._research.itn_window import (
    hohmann_total_dv_kms,
    synodic_period_days,
)
from ephemerides_spectral._research.bodies import BODIES


# --------------------------------------------------------------------------
# Named constants (NO magic numbers per project policy).
# --------------------------------------------------------------------------

# J2000.0 epoch in Julian Date (TDB). Same anchor as bip_instrument.
REFERENCE_JD: float = 2451545.0

# Sweep horizon for the empirical Dijkstra search, in years. 50 years
# covers ~25 Earth-Mars synodic periods, ~4 Earth-Jupiter, ~2 Earth-
# Saturn — enough launch-window density that a feasible chain, if one
# exists in [0, dv_budget], will appear.
SWEEP_YEARS: float = 50.0
DAYS_PER_YEAR: float = 365.25
SWEEP_DAYS: float = SWEEP_YEARS * DAYS_PER_YEAR

# find_itn_chains parameters. Match the brief: max_legs=3, dv_budget=30,
# threshold=0.1. max_chains caps Dijkstra emission per pair (we only need
# the cheapest).
ITN_MAX_LEGS: int = 3
ITN_DV_BUDGET_KMS: float = 30.0
ITN_TOF_BUDGET_DAYS: float = DAYS_PER_YEAR * 20.0  # 20-yr TOF cap
ITN_THRESHOLD: float = 0.1
ITN_MAX_CHAINS: int = 50

# Heliocentric body subset. Planets + classical dwarf + main-belt
# asteroids. Sun excluded (central potential, not a transit node).
# Moons excluded (no parent-frame Δv model in v0.17.0).
HELIOCENTRIC_BODIES: List[str] = [
    "mercury", "venus", "terra", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "ceres", "vesta", "pallas", "hygiea",
]

# Numerical safety: floor on Δv added before inversion to avoid divide-by-
# zero. Smallest meaningful Hohmann Δv in the roster (mercury → venus) is
# ~5 km/s, so 1e-3 is well below the noise floor.
EPS_DV_KMS: float = 1.0e-3
EPS_SYN_DAYS: float = 1.0e-3

# Sentinel for "no chain found within budget". Used in scatter plots.
NO_CHAIN_DV_KMS: float = float("inf")

# Output directory for figures. Resolved relative to this file.
_THIS_DIR = Path(__file__).resolve().parent
FIGURES_DIR: Path = _THIS_DIR.parent / "figures"


# --------------------------------------------------------------------------
# Graph construction.
# --------------------------------------------------------------------------

def build_weight_matrix(
    bodies: List[str],
    weighting: str,
) -> np.ndarray:
    """Build the symmetric weight matrix W for the gateway graph.

    Parameters
    ----------
    bodies : list of body names; W is indexed in this order.
    weighting : one of {"inv_dv", "inv_synodic"}.

        * ``"inv_dv"`` — ``w_ij = 1 / (Δv_ij + EPS_DV_KMS)`` where Δv_ij
          is the closed-form total Hohmann Δv between bodies i and j.
        * ``"inv_synodic"`` — ``w_ij = 1 / (T_syn_ij + EPS_SYN_DAYS)``
          using the closed-form synodic period (in days).

    Returns
    -------
    W : (n, n) ndarray, symmetric, zero diagonal, all off-diagonal > 0.
    """
    n = len(bodies)
    W = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            p_i = BODIES[bodies[i]].period_days
            p_j = BODIES[bodies[j]].period_days
            if weighting == "inv_dv":
                dv = hohmann_total_dv_kms(p_i, p_j)
                w = 1.0 / (dv + EPS_DV_KMS)
            elif weighting == "inv_synodic":
                t_syn = synodic_period_days(p_i, p_j)
                w = 1.0 / (t_syn + EPS_SYN_DAYS)
            else:
                raise ValueError(f"unknown weighting {weighting!r}")
            W[i, j] = w
            W[j, i] = w
    return W


def build_laplacian(W: np.ndarray) -> np.ndarray:
    """Combinatorial graph Laplacian L = D - W."""
    D = np.diag(W.sum(axis=1))
    return D - W


def fiedler_eigvec(L: np.ndarray) -> Tuple[float, np.ndarray]:
    """Return (λ₂, Fiedler eigenvector) for symmetric Laplacian L.

    Uses ``np.linalg.eigh`` (symmetric eigensolver). Eigenvalues are
    returned ascending; index 0 is the trivial λ₁ = 0 (constant vector,
    connected graph). λ₂ is the algebraic connectivity; its eigenvector
    is the Fiedler vector.
    """
    eigvals, eigvecs = np.linalg.eigh(L)
    return float(eigvals[1]), eigvecs[:, 1]


# --------------------------------------------------------------------------
# Empirical ground truth via bridge.find_itn_chains.
# --------------------------------------------------------------------------

def empirical_min_dv(
    departure: str,
    target: str,
) -> Tuple[float, int]:
    """Run find_itn_chains and return (min total_dv_kms, n_chains_found).

    Returns (NO_CHAIN_DV_KMS, 0) if no chain fits the budget.
    """
    result = bridge.find_itn_chains(
        jd_lo=REFERENCE_JD,
        jd_hi=REFERENCE_JD + SWEEP_DAYS,
        departure=departure,
        target=target,
        max_legs=ITN_MAX_LEGS,
        dv_budget_kms=ITN_DV_BUDGET_KMS,
        tof_budget_days=ITN_TOF_BUDGET_DAYS,
        threshold=ITN_THRESHOLD,
        max_chains=ITN_MAX_CHAINS,
    )
    if not result.get("ok") or not result.get("chains"):
        return (NO_CHAIN_DV_KMS, 0)
    chains = result["chains"]
    min_dv = min(float(c["total_dv_kms"]) for c in chains)
    return (min_dv, len(chains))


# --------------------------------------------------------------------------
# Validation metrics.
# --------------------------------------------------------------------------

def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation. Hand-rolled (no scipy.stats dep).

    Ranks computed via argsort of argsort. Returns NaN if either array
    has zero variance after ranking (degenerate case).
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    rx = np.argsort(np.argsort(x)).astype(np.float64)
    ry = np.argsort(np.argsort(y)).astype(np.float64)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = math.sqrt(float((rx * rx).sum()) * float((ry * ry).sum()))
    if denom == 0.0:
        return float("nan")
    return float((rx * ry).sum() / denom)


def confusion_matrix(
    pred_within: np.ndarray,
    obs_cheap: np.ndarray,
) -> Dict[str, int]:
    """2×2 confusion matrix.

    Rows: observed cheap (Δv ≤ median) vs expensive (> median).
    Cols: predicted within-Fiedler-partition vs across.

    Returns dict with keys: {within_cheap, within_expensive,
    across_cheap, across_expensive}.
    """
    within_cheap = int(np.sum(pred_within & obs_cheap))
    within_expensive = int(np.sum(pred_within & ~obs_cheap))
    across_cheap = int(np.sum(~pred_within & obs_cheap))
    across_expensive = int(np.sum(~pred_within & ~obs_cheap))
    return {
        "within_cheap": within_cheap,
        "within_expensive": within_expensive,
        "across_cheap": across_cheap,
        "across_expensive": across_expensive,
    }


# --------------------------------------------------------------------------
# Figures.
# --------------------------------------------------------------------------

def plot_scatter(
    fiedler_dist: np.ndarray,
    obs_dv: np.ndarray,
    same_partition: np.ndarray,
    pair_labels: List[str],
    weighting: str,
    rho: float,
    out_path: Path,
) -> None:
    """Scatter: Fiedler distance vs observed min-Δv, colour by partition."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    finite_mask = np.isfinite(obs_dv)
    inf_mask = ~finite_mask

    # Finite (chain found)
    fin_within = finite_mask & same_partition
    fin_across = finite_mask & ~same_partition
    ax.scatter(
        fiedler_dist[fin_within], obs_dv[fin_within],
        c="tab:blue", marker="o", s=42, alpha=0.8,
        label=f"within-partition (n={int(fin_within.sum())})",
    )
    ax.scatter(
        fiedler_dist[fin_across], obs_dv[fin_across],
        c="tab:red", marker="s", s=42, alpha=0.8,
        label=f"across-partition (n={int(fin_across.sum())})",
    )

    # Infinite (no chain) — plot at top of axis as triangles for visibility.
    if inf_mask.any():
        finite_dv = obs_dv[finite_mask]
        ceiling = (finite_dv.max() if finite_dv.size else 1.0) * 1.10
        inf_within = inf_mask & same_partition
        inf_across = inf_mask & ~same_partition
        ax.scatter(
            fiedler_dist[inf_within],
            np.full(int(inf_within.sum()), ceiling),
            c="tab:blue", marker="^", s=64, alpha=0.6,
            label=f"no chain — within (n={int(inf_within.sum())})",
        )
        ax.scatter(
            fiedler_dist[inf_across],
            np.full(int(inf_across.sum()), ceiling),
            c="tab:red", marker="^", s=64, alpha=0.6,
            label=f"no chain — across (n={int(inf_across.sum())})",
        )

    ax.set_xlabel("Fiedler-vector distance |f₂[i] − f₂[j]|")
    ax.set_ylabel("Observed min total_dv_kms (find_itn_chains)")
    ax.set_title(
        f"Gateway-graph Laplacian — Fiedler distance vs empirical Δv\n"
        f"weighting={weighting}   Spearman ρ = {rho:+.3f}   "
        f"n_pairs = {len(fiedler_dist)}"
    )
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_partition(
    bodies: List[str],
    fiedler: np.ndarray,
    weighting: str,
    out_path: Path,
) -> None:
    """Bar chart of Fiedler-vector entries by body, coloured by sign."""
    import matplotlib.pyplot as plt

    order = np.argsort(fiedler)
    sorted_bodies = [bodies[i] for i in order]
    sorted_f = fiedler[order]
    colours = ["tab:red" if v < 0.0 else "tab:blue" for v in sorted_f]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(range(len(sorted_bodies)), sorted_f, color=colours)
    ax.set_xticks(range(len(sorted_bodies)))
    ax.set_xticklabels(sorted_bodies, rotation=45, ha="right")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_ylabel("Fiedler-vector entry  f₂[body]")
    ax.set_title(
        f"Gateway-graph Laplacian — Fiedler partition (weighting={weighting})\n"
        f"red = negative partition, blue = positive partition"
    )
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------
# Main driver.
# --------------------------------------------------------------------------

def run_one_weighting(
    bodies: List[str],
    weighting: str,
    obs_dv_matrix: np.ndarray,
) -> Dict[str, object]:
    """Build Laplacian, compute Fiedler, validate against obs_dv_matrix.

    obs_dv_matrix is (n, n) symmetric with NO_CHAIN_DV_KMS for non-pairs.
    Returns dict of summary stats + writes figures.
    """
    n = len(bodies)
    W = build_weight_matrix(bodies, weighting)
    L = build_laplacian(W)
    lam2, fiedler = fiedler_eigvec(L)

    # Per-pair arrays over the C(n, 2) unordered pairs.
    pair_idx: List[Tuple[int, int]] = list(itertools.combinations(range(n), 2))
    fiedler_dist = np.array(
        [abs(fiedler[i] - fiedler[j]) for (i, j) in pair_idx]
    )
    obs_dv = np.array([obs_dv_matrix[i, j] for (i, j) in pair_idx])
    same_partition = np.array(
        [(fiedler[i] >= 0.0) == (fiedler[j] >= 0.0) for (i, j) in pair_idx]
    )

    # Spearman ρ on FINITE pairs only — Spearman of inf vs anything is
    # ill-defined. Report n_inf separately.
    finite_mask = np.isfinite(obs_dv)
    n_finite = int(finite_mask.sum())
    n_inf = int((~finite_mask).sum())
    if n_finite >= 2:
        rho = spearman_rho(fiedler_dist[finite_mask], obs_dv[finite_mask])
    else:
        rho = float("nan")

    # Confusion matrix on a median split. Treat NO_CHAIN_DV_KMS as
    # "expensive" (it is the ultimate expensive — no chain at all).
    if n_finite >= 1:
        median_dv = float(np.median(obs_dv[finite_mask]))
    else:
        median_dv = NO_CHAIN_DV_KMS
    obs_cheap = (obs_dv <= median_dv) & finite_mask
    cm = confusion_matrix(same_partition, obs_cheap)

    # Figures.
    pair_labels = [f"{bodies[i]}-{bodies[j]}" for (i, j) in pair_idx]
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    scatter_path = FIGURES_DIR / f"gateway_laplacian_fiedler_dv_{weighting}.png"
    partition_path = FIGURES_DIR / f"gateway_laplacian_partition_{weighting}.png"
    plot_scatter(
        fiedler_dist, obs_dv, same_partition, pair_labels,
        weighting, rho, scatter_path,
    )
    plot_partition(bodies, fiedler, weighting, partition_path)

    return {
        "weighting": weighting,
        "lambda_2": lam2,
        "fiedler": fiedler.tolist(),
        "rho_spearman": rho,
        "n_finite": n_finite,
        "n_inf": n_inf,
        "median_dv_kms": median_dv,
        "confusion_matrix": cm,
        "scatter_path": str(scatter_path),
        "partition_path": str(partition_path),
    }


def _cache_path(bodies: List[str]) -> Path:
    """Cache file under research/_cache/; key is body roster + sweep config.

    Uses hashlib (deterministic across Python invocations — Python's
    builtin ``hash()`` randomises per-process, which would defeat the
    cache on every fresh interpreter start).

    Cache lives in ``research/_cache/`` (a sibling of this script),
    NOT in ``figures/`` — figures is for committable artefacts; the
    cache is per-host scratch and should be gitignored.
    """
    import hashlib
    key = "|".join(bodies) + f"|{int(SWEEP_YEARS)}yr|dv{int(ITN_DV_BUDGET_KMS)}"
    short = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    cache_dir = _THIS_DIR / "_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"obs_dv_matrix_{short}.npy"


def main() -> int:
    bodies = HELIOCENTRIC_BODIES
    n = len(bodies)
    n_pairs = n * (n - 1) // 2
    print(f"# Gateway-graph Laplacian — research prototype")
    print(f"# n_bodies = {n} ({', '.join(bodies)})")
    print(f"# n_pairs  = {n_pairs}  (sweep window = {SWEEP_YEARS:.0f} yr at J2000)")
    print()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(bodies)

    # 1. Empirical ground truth: min_dv per (i, j) pair. Take
    #    min(forward, reverse) to be robust to Dijkstra path-asymmetries
    #    (Hohmann Δv is direction-symmetric in the closed-form model, but
    #    chain composition through intermediates is not necessarily so).
    if cache_file.exists():
        print(f"[1/3] Loading cached ground truth from {cache_file.name}...")
        obs_dv_matrix = np.load(cache_file)
    else:
        print(f"[1/3] Running find_itn_chains over {n_pairs} pairs...")
        obs_dv_matrix = np.full((n, n), NO_CHAIN_DV_KMS)
        t_start = time.time()
        n_done = 0
        for i, j in itertools.combinations(range(n), 2):
            n_done += 1
            dv_fwd, _ = empirical_min_dv(bodies[i], bodies[j])
            dv_rev, _ = empirical_min_dv(bodies[j], bodies[i])
            dv = min(dv_fwd, dv_rev)
            obs_dv_matrix[i, j] = dv
            obs_dv_matrix[j, i] = dv
            if n_done % 10 == 0 or n_done == n_pairs:
                print(
                    f"      [{n_done}/{n_pairs}] {bodies[i]:<8s} "
                    f"<-> {bodies[j]:<8s}  min_dv = "
                    f"{dv if math.isfinite(dv) else float('inf'):>7.3f} km/s",
                    flush=True,
                )
        elapsed = time.time() - t_start
        np.save(cache_file, obs_dv_matrix)
        print(f"      cached to {cache_file.name} ({elapsed:.1f}s)")
    n_finite_pairs = int(np.isfinite(obs_dv_matrix[np.triu_indices(n, k=1)]).sum())
    print(
        f"      ground truth: {n_finite_pairs}/{n_pairs} pairs feasible\n"
    )

    # 2. Two weightings.
    print("[2/3] Building gateway Laplacians + Fiedler eigenvectors...")
    summaries = []
    for weighting in ("inv_dv", "inv_synodic"):
        s = run_one_weighting(bodies, weighting, obs_dv_matrix)
        summaries.append(s)
        cm = s["confusion_matrix"]
        print(
            f"      weighting={weighting:<11s}  λ₂={s['lambda_2']:.4e}  "
            f"Spearman ρ={s['rho_spearman']:+.3f}  "
            f"(n_finite={s['n_finite']}, n_inf={s['n_inf']})"
        )
        print(
            f"        confusion matrix (median split @ {s['median_dv_kms']:.2f} km/s):"
        )
        print(
            f"          within_cheap={cm['within_cheap']:>3d}  "
            f"within_expensive={cm['within_expensive']:>3d}"
        )
        print(
            f"          across_cheap={cm['across_cheap']:>3d}  "
            f"across_expensive={cm['across_expensive']:>3d}"
        )
        # Cohen's "phi" (Matthews correlation) as a single-number metric
        # on the 2×2 confusion matrix.
        a = cm["within_cheap"]
        b = cm["within_expensive"]
        c = cm["across_cheap"]
        d = cm["across_expensive"]
        denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
        phi = (a * d - b * c) / denom if denom > 0.0 else float("nan")
        print(f"        Matthews φ = {phi:+.3f}")
        print(f"        figures: {s['scatter_path']}")
        print(f"                 {s['partition_path']}\n")

    # 3. Verdict.
    print("[3/3] Verdict")
    print("-" * 64)
    rho_dv = summaries[0]["rho_spearman"]
    rho_syn = summaries[1]["rho_spearman"]
    primary_rho = rho_dv  # primary predictor: inv_dv weighting
    if not math.isfinite(primary_rho):
        verdict = "DEGENERATE — too few feasible pairs for Spearman"
    elif primary_rho >= 0.7:
        verdict = "STRONG SUPPORT — Fiedler distance predicts Δv (ρ ≥ 0.7)"
    elif primary_rho >= 0.4:
        verdict = "PARTIAL SUPPORT — Fiedler captures gross structure (0.4 ≤ ρ < 0.7)"
    elif primary_rho >= 0.2:
        verdict = "WEAK SUPPORT — Fiedler weakly correlates (0.2 ≤ ρ < 0.4)"
    else:
        verdict = "NULL RESULT — Fiedler does not predict empirical Δv (ρ < 0.2)"
    print(f"VERDICT: {verdict}")
    print(f"  primary (inv_dv  weighting) Spearman ρ = {rho_dv:+.3f}")
    print(f"  control (inv_syn weighting) Spearman ρ = {rho_syn:+.3f}")
    print(f"  See figures in {FIGURES_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
