"""Phase 1e.1 — edax d=20 on the 2587 Takizawa tasklist OBFs.

Generates a third target for the D4-A1(s^2) correlation so we can
separate the two readings of the 43 % gain reported in §2d.b:

  Reading A (aggregation): archive_mean_lb is a smoother y-variable
                            than pre-proof edax_score, inflating
                            |rho|.
  Reading B (alignment):    the spectral channel carries ground-
                            truth-aligned content beyond what even a
                            strong deep-search engine captures.

Decision rule:
  If rho(D4_A1, edax_d20) comes out near rho(D4_A1, archive_mean_lb)
  (~ -0.498 raw / -0.319 partial)  -> Reading A dominates.
  If it comes out near rho(D4_A1, edax_score_preproof)
  (~ -0.349 raw / -0.279 partial)  -> Reading B dominates.

Input:  dataset/reversi_scripts/empty50_tasklist_edax_knowledge.csv
Output: results/phase1e_edax_d20.csv

Resumable: existing rows in the output CSV are skipped on restart.
Per-position rows flushed to disk immediately so crashes preserve
progress.

Walltime estimate: ~6 s per position at d=20, 2587 positions total,
                    ~4 hours wall.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from edax_wrapper import (
    EdaxNotFoundError,
    evaluate,
    resolve_edax_path,
    smoke_test,
)


def _load_tasklist(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _load_done(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    done = set()
    with out_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("obf"):
                done.add(r["obf"])
    return done


def run(
    tasklist: Path, out: Path, edax: Path, depth: int,
    limit: int | None,
) -> None:
    rows = _load_tasklist(tasklist)
    if limit is not None:
        rows = rows[:limit]
    already = _load_done(out)
    todo = [r for r in rows if r["obf"] not in already]
    print(f"tasklist: {len(rows)} positions")
    print(f"already done: {len(already)}")
    print(f"to evaluate: {len(todo)} at depth {depth}")
    if not todo:
        print("nothing to do")
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    file_exists = out.exists()
    mode = "a" if file_exists else "w"
    fieldnames = [
        "obf", "edax_d20_score", "edax_d20_depth_observed",
        "edax_d20_best_move", "parse_ok",
    ]
    with out.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            f.flush()
        t0 = time.time()
        for i, r in enumerate(todo, 1):
            obf = r["obf"]
            try:
                result = evaluate(obf, depth, edax, timeout_s=900.0)
                row = {
                    "obf": obf,
                    "edax_d20_score": result.score,
                    "edax_d20_depth_observed": result.depth,
                    "edax_d20_best_move": result.best_move or "",
                    "parse_ok": 1,
                }
            except Exception as exc:
                print(
                    f"[{i}/{len(todo)}] edax failed on {obf[:32]}... : {exc}",
                    file=sys.stderr,
                )
                row = {
                    "obf": obf,
                    "edax_d20_score": "",
                    "edax_d20_depth_observed": "",
                    "edax_d20_best_move": "",
                    "parse_ok": 0,
                }
            writer.writerow(row)
            f.flush()
            if (i % 20 == 0) or (i == len(todo)):
                elapsed = time.time() - t0
                rate = i / max(elapsed, 1e-6)
                eta_s = (len(todo) - i) / max(rate, 1e-6)
                print(
                    f"  [{i}/{len(todo)}] elapsed {elapsed:.0f}s  "
                    f"rate {rate:.2f} pos/s  eta {eta_s/60:.1f} min"
                )


def _build_parser():
    default_tasklist = (
        Path(__file__).resolve().parent.parent / "dataset"
        / "reversi_scripts" / "empty50_tasklist_edax_knowledge.csv"
    )
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_edax_d20.csv"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Full run (resumable).  Edits phase1e_edax_d20.csv in place.
  python research/phase1e_edax_d20_tasklist.py

  # Smoke test: first 5 positions at d=10.
  python research/phase1e_edax_d20_tasklist.py --limit 5 --depth 10

  # Custom edax path (overrides EDAX_PATH env var).
  python research/phase1e_edax_d20_tasklist.py \\
      --edax-path ../edax-4.5.5/bin/wEdax-x86-64.exe
""",
    )
    p.add_argument("--tasklist", type=Path, default=default_tasklist)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument("--edax-path", type=str, default=None)
    p.add_argument("--depth", type=int, default=20)
    p.add_argument("--limit", type=int, default=None,
                   help="Process only first N positions.")
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        edax_path = resolve_edax_path(args.edax_path)
    except EdaxNotFoundError as exc:
        print(f"{exc}", file=sys.stderr)
        return 2
    if not smoke_test(edax_path):
        print("edax smoke test failed", file=sys.stderr)
        return 2
    run(args.tasklist, args.out, edax_path, args.depth, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
