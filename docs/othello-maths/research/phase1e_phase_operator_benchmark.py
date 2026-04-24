"""Benchmark the sheaf-phased operator modes against archive_mean_lb.

For each mode of SheafPhaseOperator, apply the operator to the
encoding of every 2587 tasklist position, extract the D4-A1
occupation-channel energy + pending_white channel energy from the
phased encoding, and Spearman-correlate against `archive_mean_lb`.

Compares against the raw (unphased) v0.3.0 encoder baseline
(§1e.7.x Exp 1: D4-A1(sheaf_pending_white) partial rho = -0.447 at
N=2587, the current best).  If any phase mode beats that, we've
got a phase-operator win.

Note: the baseline channel used throughout phase-1e is DERIVED
from the 64-dim sheaf_pending_white block via a D4-A1 projection
(see phase1e_sheaf_vs_archive.py), NOT a direct raw channel
energy.  For an apples-to-apples comparison this runner also
computes D4-projected channel energies on the phased output.
"""

from __future__ import annotations

__version__ = "0.3.1"

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from d4_z2 import D4_CHARS, D4_DIMS, D4_PERMS
from othello_spectral import encode_768
from othello_spectral.phase_operator import SheafPhaseOperator, VALID_MODES
from othello_utils import BLACK, N

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


def d4_project_energy(sig: np.ndarray, irrep: str) -> float:
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


def run(tasklist: Path, archive: Path, out_json: Path) -> dict:
    with tasklist.open("r", encoding="utf-8") as f:
        trows = list(csv.DictReader(f))
    with archive.open("r", encoding="utf-8") as f:
        arows = {r["parent_obf"]: r for r in csv.DictReader(f)}
    print(f"tasklist: {len(trows)}, archive: {len(arows)}")

    modes_to_test = [m for m in VALID_MODES if m != "scale_by_feature_coupling"]
    operators = {m: SheafPhaseOperator(mode=m) for m in modes_to_test}

    # Collect records: D4-projected channel energies on phased
    # encoding plus archive_mean_lb.
    records = []
    for i, r in enumerate(trows):
        obf = r["obf"]
        state, side = obf_to_state(obf)
        base_enc = encode_768(state)  # v0.3.0 sheaf default
        b = int(np.sum(state == BLACK))
        w = int(np.sum(state == -BLACK))
        dd = (b - w) if side == BLACK else (w - b)
        rec = {
            "obf": obf,
            "disc_diff_abs": abs(dd),
            "edax_score": int(r["score"]),
        }
        a = arows.get(obf)
        if a is not None:
            try:
                rec["archive_mean_lb"] = float(a.get("mean_lb", "") or "nan")
            except ValueError:
                rec["archive_mean_lb"] = float("nan")

        for mode, op in operators.items():
            phased = op.apply(base_enc, state)
            # Fiber blocks (channels 10, 11) are the sheaf pending
            # per-cell vectors; project through D4 A1 and E.
            pend_b = phased[10 * 64:11 * 64]
            pend_w = phased[11 * 64:12 * 64]
            rec[f"{mode}__fiber_pb_A1"] = d4_project_energy(pend_b, "A1")
            rec[f"{mode}__fiber_pw_A1"] = d4_project_energy(pend_w, "A1")
            rec[f"{mode}__fiber_pb_E"]  = d4_project_energy(pend_b, "E")
            rec[f"{mode}__fiber_pw_E"]  = d4_project_energy(pend_w, "E")

        records.append(rec)
        if (i + 1) % 500 == 0:
            print(f"  processed {i + 1}/{len(trows)}", flush=True)

    # Correlations
    targets = ["edax_score", "archive_mean_lb"]
    dd_arr = np.array([r["disc_diff_abs"] for r in records], dtype=float)

    correlations: dict = {}
    metrics = ["fiber_pb_A1", "fiber_pw_A1", "fiber_pb_E", "fiber_pw_E"]
    for mode in modes_to_test:
        for m in metrics:
            key_src = f"{mode}__{m}"
            xs = np.array([r[key_src] for r in records], dtype=float)
            for tg in targets:
                ys = [r.get(tg) for r in records]
                mask = np.array([
                    v is not None and not (
                        isinstance(v, float) and np.isnan(v)
                    )
                    for v in ys
                ])
                if mask.sum() < 50:
                    continue
                x = xs[mask]
                y = np.array(
                    [ys[i] for i in range(len(ys)) if mask[i]],
                    dtype=float,
                )
                sp = spearmanr(x, y)
                if dd_arr[mask].std() > 0:
                    xr = _residualize(x, dd_arr[mask])
                    yr = _residualize(y, dd_arr[mask])
                    sp_p = spearmanr(xr, yr)
                    partial = {
                        "rho": float(sp_p.statistic),
                        "p": float(sp_p.pvalue),
                    }
                else:
                    partial = None
                correlations[f"{key_src}__vs__{tg}"] = {
                    "raw_rho": float(sp.statistic),
                    "raw_p": float(sp.pvalue),
                    "partial_rho": (
                        partial["rho"] if partial else None
                    ),
                    "partial_p": (
                        partial["p"] if partial else None
                    ),
                    "n": int(mask.sum()),
                }

    summary = {
        "n_positions": len(records),
        "modes_tested": modes_to_test,
        "correlations": correlations,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Stdout: top metrics per mode, sorted by |partial rho| vs archive
    print(f"\n=== Phase operator modes vs archive_mean_lb (N={len(records)}) ===")
    print(f"{'mode':38s}  {'metric':14s}  {'raw rho':>8s}  {'partial':>8s}")
    for mode in modes_to_test:
        print(f"\n  mode = {mode}")
        ranked = []
        for m in metrics:
            key = f"{mode}__{m}__vs__archive_mean_lb"
            info = correlations.get(key)
            if info:
                ranked.append((m, info))
        ranked.sort(
            key=lambda kv: -abs(kv[1].get("partial_rho") or 0.0)
        )
        for m, info in ranked:
            print(
                f"{'':4s}{m:16s}  raw = {info['raw_rho']:+.4f}  "
                f"partial = {info.get('partial_rho', 0.0):+.4f}"
            )
    print(f"\nBaseline for comparison (§1e.7.x Exp 1):")
    print(f"  pending_white through D4-A1  partial rho = -0.447")
    print(f"\nwrote {out_json}")
    return summary


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
        / "phase1e_phase_operator_benchmark.json",
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
