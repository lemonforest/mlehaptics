"""Phase 1e.6 — sign-flip decomposition of D4-A1(s^2) vs Shannon info
by n_empties bucket.

Phase 1e.3 reported that Spearman(I_move, D4-A1(s^2)) is strongly
POSITIVE in-book (+0.465 at ~676 plies) and strongly NEGATIVE
out-of-book (-0.755 at ~1423 plies).  The overall (all-plies)
correlation is only -0.115 because these two regimes partially
cancel.

This runner asks where along the game trajectory the sign-flip
occurs.  Two decompositions:

  (a) By n_empties bucket (game phase).  Binned Spearman of I_move
      against the spectral observable.
  (b) By book-coverage regime within each bucket.  The WTHOR book
      coverage drops sharply at ~20 empties; the sign-flip could
      either track the book cliff or the game phase directly.

Inputs
------
  results/phase1e_shannon_per_move_observables.csv
    (columns: i_move_bits, n_empties, in_book, d4_a1_occupation_energy,
               d4_e_occupation_energy, ...)

Outputs
-------
  results/phase1e_signflip_decomposition.json
  (stdout also prints a human-readable bucket table)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


OBS_KEYS = [
    "a1_minus_energy",
    "e_minus_energy",
    "d4_a1_occupation_energy",
    "d4_a2_occupation_energy",
    "d4_b1_occupation_energy",
    "d4_b2_occupation_energy",
    "d4_e_occupation_energy",
]


def _load(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _to_float(r: dict, key: str) -> float | None:
    v = r.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _bucket_corr(
    rows: list[dict], obs: str, mask_fn=None, min_n: int = 30,
) -> dict:
    """Return Spearman(i_move, obs) for every n_empties bucket."""
    buckets: dict[int, list[tuple[float, float]]] = {}
    for r in rows:
        if mask_fn is not None and not mask_fn(r):
            continue
        e = int(r["n_empties"])
        im = _to_float(r, "i_move_bits")
        ob = _to_float(r, obs)
        if im is None or ob is None:
            continue
        buckets.setdefault(e, []).append((im, ob))
    out: dict[int, dict] = {}
    for e in sorted(buckets.keys()):
        xs = np.array([b[0] for b in buckets[e]])
        ys = np.array([b[1] for b in buckets[e]])
        if len(xs) < min_n or xs.std() == 0 or ys.std() == 0:
            out[e] = {"n": int(len(xs)), "rho": None, "p": None}
            continue
        sp = spearmanr(xs, ys)
        out[e] = {
            "n": int(len(xs)),
            "rho": float(sp.statistic),
            "p": float(sp.pvalue),
        }
    return out


def _group_ranges_corr(
    rows: list[dict], obs: str, ranges: list[tuple[int, int, str]],
    min_n: int = 30,
) -> dict:
    """Coarser groupings: (e_lo, e_hi, label) inclusive endpoints."""
    out = {}
    for lo, hi, label in ranges:
        group = []
        for r in rows:
            e = int(r["n_empties"])
            if not (lo <= e <= hi):
                continue
            im = _to_float(r, "i_move_bits")
            ob = _to_float(r, obs)
            if im is None or ob is None:
                continue
            group.append((im, ob, int(r.get("in_book", "0") or 0)))
        xs = np.array([g[0] for g in group])
        ys = np.array([g[1] for g in group])
        ib = np.array([g[2] for g in group], dtype=bool)
        if len(xs) < min_n or xs.std() == 0 or ys.std() == 0:
            out[label] = {"n": int(len(xs)), "rho": None}
            continue
        sp_all = spearmanr(xs, ys)
        sp_in = None
        sp_oo = None
        if ib.sum() >= min_n and xs[ib].std() > 0 and ys[ib].std() > 0:
            sp_in = spearmanr(xs[ib], ys[ib])
        if (~ib).sum() >= min_n and xs[~ib].std() > 0 and ys[~ib].std() > 0:
            sp_oo = spearmanr(xs[~ib], ys[~ib])
        out[label] = {
            "n_total": int(len(xs)),
            "n_in_book": int(ib.sum()),
            "n_out_of_book": int((~ib).sum()),
            "e_lo": lo,
            "e_hi": hi,
            "all":        {"rho": float(sp_all.statistic), "p": float(sp_all.pvalue)},
            "in_book":    None if sp_in is None else {"rho": float(sp_in.statistic), "p": float(sp_in.pvalue)},
            "out_of_book":None if sp_oo is None else {"rho": float(sp_oo.statistic), "p": float(sp_oo.pvalue)},
        }
    return out


def run(csv_path: Path, out_json: Path) -> dict:
    rows = _load(csv_path)
    print(f"loaded {len(rows)} per-move rows")
    empties = [int(r["n_empties"]) for r in rows]
    in_book = [int(r.get("in_book", "0") or 0) for r in rows]
    print(
        f"empties range: {min(empties)}..{max(empties)}, "
        f"in_book fraction: {sum(in_book) / len(in_book):.3f}"
    )

    # Per-empties buckets, all plies
    per_bucket_all = {
        obs: _bucket_corr(rows, obs) for obs in OBS_KEYS
    }
    # Per-empties buckets, in-book only
    per_bucket_in = {
        obs: _bucket_corr(
            rows, obs, mask_fn=lambda r: int(r.get("in_book", "0") or 0) == 1
        ) for obs in OBS_KEYS
    }
    # Per-empties buckets, out-of-book only
    per_bucket_oo = {
        obs: _bucket_corr(
            rows, obs, mask_fn=lambda r: int(r.get("in_book", "0") or 0) == 0
        ) for obs in OBS_KEYS
    }

    # Coarser phase ranges
    ranges = [
        (53, 60, "opening (60-53 empties, 100% book cov)"),
        (45, 52, "early midgame (52-45)"),
        (35, 44, "late midgame (44-35)"),
        (25, 34, "endgame entry (34-25)"),
        (10, 24, "deep endgame (24-10)"),
        (0,  9,  "terminal (9-0)"),
    ]
    range_corr = {
        obs: _group_ranges_corr(rows, obs, ranges) for obs in OBS_KEYS
    }

    summary = {
        "source": str(csv_path),
        "n_rows": len(rows),
        "observables": OBS_KEYS,
        "per_bucket_all_plies": per_bucket_all,
        "per_bucket_in_book_only": per_bucket_in,
        "per_bucket_out_of_book_only": per_bucket_oo,
        "phase_ranges": range_corr,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Stdout: sign-flip map for the headline observable
    print("\n=== D4-A1(s^2): n_empties vs Spearman(I_move, obs) ===")
    head_obs = "d4_a1_occupation_energy"
    all_buckets = per_bucket_all[head_obs]
    print(f"  {'empties':>8s} {'n':>6s} {'all rho':>10s} {'in rho':>10s} {'out rho':>10s}")
    for e in sorted(all_buckets.keys(), reverse=True):
        a = all_buckets[e]
        i = per_bucket_in[head_obs].get(e, {})
        o = per_bucket_oo[head_obs].get(e, {})
        def fmt(d):
            r = d.get("rho")
            return f"{r:+.3f}" if r is not None else "  n/a"
        print(
            f"  {e:>8d} {a['n']:>6d} {fmt(a):>10s} "
            f"{fmt(i):>10s} {fmt(o):>10s}"
        )
    print("\n=== Phase range summary (D4-A1 s^2) ===")
    for label, r in range_corr[head_obs].items():
        if r.get("rho") is None and "all" not in r:
            continue
        all_info = r.get("all", {})
        ib_info = r.get("in_book") or {}
        oo_info = r.get("out_of_book") or {}
        print(
            f"  {label:45s}  N={r.get('n_total', 0):5d}  "
            f"all={all_info.get('rho', 0):+.3f}  "
            f"in={ib_info.get('rho', 0) if ib_info else 0:+.3f}  "
            f"out={oo_info.get('rho', 0) if oo_info else 0:+.3f}"
        )
    print(f"\nwrote {out_json}")
    return summary


def _build_parser():
    default_csv = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_shannon_per_move_observables.csv"
    )
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_signflip_decomposition.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python research/phase1e_signflip_decomposition.py

reading the output:
  The per-bucket ``all rho`` column shows how Spearman(I_move,
  D4-A1(s^2)) evolves from opening (high empties) to endgame (low
  empties).  If the sign-flip tracks the WTHOR book cliff (sharp
  drop around empties=20 in the corpus), the 'in rho' and 'out rho'
  columns will remain same-signed within each bucket while the
  book-coverage collapses around the transition.  If the flip
  tracks game phase directly, both 'in rho' and 'out rho' will
  sign-flip together at some empties threshold.
""",
    )
    p.add_argument("--csv", type=Path, default=default_csv)
    p.add_argument("--out-json", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.csv.exists():
        print(f"input CSV not found: {args.csv}", file=sys.stderr)
        return 2
    run(args.csv, args.out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
