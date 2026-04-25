"""Exp 1 — do sheaf-derived per-cell features correlate with
Takizawa's archive_mean_lb better than the current occupation
channels?

Rationale: the encoder currently emits D4-A1(s^2) and D4-E(s^2)
on the occupation signal, which achieved partial rho = -0.319 /
+0.310 against archive_mean_lb at N=2587 (§1d.b).

This runner computes a sheaf-derived per-cell feature for every
tasklist position and projects it through the D4 projectors to
yield 5 D4-channel energies.  Compares correlations against
archive_mean_lb.

Features tested:
  sheaf_bracket_degree_black  : per-cell bracket participation count
                                 from BLACK-owner faithful sheaf
  sheaf_bracket_degree_white  : ...from WHITE-owner
  sheaf_bracket_degree_total  : sum of both
  sheaf_bracket_pending_count : per-cell R3_PENDING participation
                                 (only flippable brackets)

Each feature is projected through the 5 D4 irreps (A1, A2, B1, B2,
E); per-channel energy is correlated with archive_mean_lb and
archive_mean_ub.

If any sheaf-derived channel beats the current best (|rho_partial|
= 0.319 for D4-A1(s^2)), the sheaf has earned its way into the
encoder.  Otherwise it's a diagnostic only.
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

from d4_z2 import D4_CHARS, D4_DIMS, D4_PERMS
from faithful_sheaf import classify_ray, R2_COMPLETE, R3_PENDING
from othello_utils import BLACK, N, RAY_OFFSETS

_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


def obf_to_state(obf: str) -> tuple[np.ndarray, int]:
    player_bb, opp_bb = _ref.obf_to_bitboards(obf)
    side = BLACK if obf[65] == "X" else -BLACK
    state = np.zeros(N, dtype=int)
    for i in range(N):
        if (player_bb >> i) & 1:
            state[i] = side
        elif (opp_bb >> i) & 1:
            state[i] = -side
    return state, side


def per_cell_sheaf_features(state: np.ndarray) -> dict:
    """For each of 64 cells, count bracket participation under
    faithful restrictions from each owner's perspective."""
    deg_b = np.zeros(N, dtype=float)
    deg_w = np.zeros(N, dtype=float)
    pending_b = np.zeros(N, dtype=float)
    pending_w = np.zeros(N, dtype=float)
    for v in range(N):
        s_v = int(state[v])
        if s_v == 0:
            continue
        for _, (dr, dc) in RAY_OFFSETS.items():
            cls, opp_cells = classify_ray(state, v, dr, dc)
            if cls == R2_COMPLETE or cls == R3_PENDING:
                # v is bracket ORIGIN (own colour)
                if s_v == 1:  # black origin
                    deg_b[v] += 1
                    for w in opp_cells:
                        deg_b[w] += 1
                    if cls == R3_PENDING:
                        pending_b[v] += 1
                        for w in opp_cells:
                            pending_b[w] += 1
                else:          # white origin
                    deg_w[v] += 1
                    for w in opp_cells:
                        deg_w[w] += 1
                    if cls == R3_PENDING:
                        pending_w[v] += 1
                        for w in opp_cells:
                            pending_w[w] += 1
    return {
        "degree_black":  deg_b,
        "degree_white":  deg_w,
        "degree_total":  deg_b + deg_w,
        "pending_black": pending_b,
        "pending_white": pending_w,
        "pending_total": pending_b + pending_w,
    }


def _d4_projection_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = D4_DIMS[irrep]
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def _residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    X = np.concatenate([x.reshape(-1, 1), np.ones((len(y), 1))], axis=1)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ coef


def _load_tasklist(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _load_archive_summary(path: Path) -> dict[str, dict]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            out[r["parent_obf"]] = r
    return out


def run(tasklist: Path, archive: Path, out_json: Path) -> dict:
    tlist = _load_tasklist(tasklist)
    arc = _load_archive_summary(archive)
    print(f"tasklist: {len(tlist)}, archive summary: {len(arc)}")

    sheaf_feature_names = [
        "degree_black", "degree_white", "degree_total",
        "pending_black", "pending_white", "pending_total",
    ]
    irreps = ("A1", "A2", "B1", "B2", "E")

    records = []
    for i, row in enumerate(tlist):
        obf = row["obf"]
        state, side = obf_to_state(obf)
        feats = per_cell_sheaf_features(state)
        b = int(np.sum(state == BLACK))
        w = int(np.sum(state == -BLACK))
        rec = {
            "obf": obf,
            "side_to_move": side,
            "edax_score": int(row["score"]),
            "disc_diff_player_minus_opp": (b - w) if side == BLACK else (w - b),
        }
        for fname in sheaf_feature_names:
            sig = feats[fname]
            for irrep in irreps:
                rec[f"E_{fname}_{irrep}"] = _d4_projection_energy(
                    sig, irrep,
                )
        a = arc.get(obf)
        if a is not None:
            def _f(k):
                v = a.get(k, "")
                if v == "" or v is None:
                    return None
                try: return float(v)
                except ValueError: return None
            rec["archive_mean_lb"] = _f("mean_lb")
            rec["archive_mean_ub"] = _f("mean_ub")
        records.append(rec)
        if (i + 1) % 500 == 0:
            print(f"  processed {i + 1}/{len(tlist)}", flush=True)

    # Correlations
    targets = ["edax_score", "archive_mean_lb", "archive_mean_ub"]
    spectral_keys = [
        f"E_{fn}_{ir}" for fn in sheaf_feature_names for ir in irreps
    ]
    dd = np.abs(np.array(
        [r["disc_diff_player_minus_opp"] for r in records], dtype=float,
    ))

    correlations: dict = {}
    for sk in spectral_keys:
        xs = np.array([r[sk] for r in records], dtype=float)
        for tg in targets:
            ys = [r.get(tg) for r in records]
            mask = np.array([v is not None for v in ys])
            if mask.sum() < 50:
                continue
            x = xs[mask]
            y = np.array([ys[i] for i in range(len(ys)) if mask[i]], dtype=float)
            sp = spearmanr(x, y)
            # partial
            if dd[mask].std() > 0:
                xr = _residualize(x, dd[mask])
                yr = _residualize(y, dd[mask])
                sp_p = spearmanr(xr, yr)
                partial = {
                    "rho": float(sp_p.statistic),
                    "p": float(sp_p.pvalue),
                }
            else:
                partial = None
            correlations[f"{sk}__vs__{tg}"] = {
                "raw_rho": float(sp.statistic),
                "raw_p": float(sp.pvalue),
                "partial_rho": partial["rho"] if partial else None,
                "partial_p": partial["p"] if partial else None,
                "n": int(mask.sum()),
            }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump({
            "n_positions": len(records),
            "sheaf_feature_names": sheaf_feature_names,
            "irreps": list(irreps),
            "correlations": correlations,
        }, f, indent=2)

    # Stdout highlights: strongest per target
    print(f"\n=== Sheaf-derived channel correlations (N={len(records)}) ===")
    for tg in targets:
        filtered = [
            (k, v) for k, v in correlations.items() if k.endswith(f"__{tg}")
        ]
        if not filtered:
            continue
        # Sort by |partial_rho| descending
        filtered.sort(
            key=lambda kv: -abs(kv[1].get("partial_rho") or 0.0),
        )
        print(f"\n  target = {tg}  (top 8 by |partial rho|)")
        print(f"  {'channel':36s}  {'raw':>8s}  {'partial':>8s}  {'N':>5s}")
        for k, v in filtered[:8]:
            ch = k.split("__vs__")[0]
            print(
                f"  {ch:36s}  {v['raw_rho']:+8.3f}  "
                f"{(v['partial_rho'] or 0.0):+8.3f}  {v['n']:>5d}"
            )

    print(f"\nBaseline for comparison (from §1d.b):")
    print(f"  D4-A1(s^2)  vs archive_mean_lb   raw -0.498  partial -0.319")
    print(f"  D4-E(s^2)   vs archive_mean_lb   raw +0.484  partial +0.310")
    print(f"\nwrote {out_json}")
    return correlations


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--tasklist", type=Path,
        default=research_dir.parent / "dataset" / "reversi_scripts"
        / "empty50_tasklist_edax_knowledge.csv",
    )
    p.add_argument(
        "--archive-summary", type=Path,
        default=research_dir.parent / "results"
        / "phase1d_archive_summary.csv",
    )
    p.add_argument(
        "--out", type=Path,
        default=research_dir.parent / "results"
        / "phase1e_sheaf_vs_archive.json",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.tasklist.exists() or not args.archive_summary.exists():
        print("tasklist or archive not found", file=sys.stderr)
        return 2
    run(args.tasklist, args.archive_summary, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
