"""Phase 1d — Takizawa knowledge-archive loader.

Reads the per-50-empty-position knowledge files from Takizawa's
figshare drop (downloaded separately, typically ~171 GB
decompressed at a drive-letter path).  Each file is named

    knowledge_<64-char-OBF-of-50-empty>.csv

and contains, per line, a 36-empty sub-problem reached under optimal
play from the 50-empty parent.  Schema (confirmed against
reversi-scripts/solve_one_e50_subproblem.py parser regex):

    obf, depth(=36), accuracy, score_lb, score_ub, nodes

``accuracy`` is the edax @XX% confidence percentage; 100 means exact,
99 means single-point uncertainty acceptable at that search.

This loader does two things:

1. ``aggregate_parent(path)`` — stream the file, compute aggregate
   bounds across children: mean / median / min / max of score_lb
   and score_ub, plus count of exact-accuracy (=100) children.

2. ``enumerate_archive(root)`` — iterate all 2587 knowledge files in
   the archive, yielding (parent_obf, path) pairs.  No file reads,
   just filename parsing.

The aggregation is deliberately shallow — we do not reconstruct the
minimax proof tree.  For correlation with spectral observables at
the 50-empty parent, the aggregate summary statistics are
sufficient.  Users who need strict minimax should re-implement on
top of ``aggregate_parent``.

CLI:
    python research/takizawa_archive_loader.py \\
        --archive /n/NORMSTOR/knowledge_archive \\
        --out ../results/phase1d_archive_summary.csv \\
        --sample 50

Output rows: parent_obf, n_children, mean_lb, mean_ub, min_lb,
max_ub, median_lb, median_ub, exact_count, exact_fraction, bytes.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import time
from pathlib import Path

from othello_pgn_loader import _ensure_utf8_stdio

_ensure_utf8_stdio()


_LINE_RE = re.compile(
    r"^([-OX]{64}\s[OX];),(-?\d+),(-?\d+),(-?\d+),(-?\d+),-?\d+\s*$"
)
_FILENAME_RE = re.compile(
    r"^knowledge_(?P<obf>[-OX]{64})\.csv$"
)


def parent_obf_from_filename(path: Path) -> str | None:
    """Return the 66-char parent OBF (64 board + ' X;') or None."""
    m = _FILENAME_RE.match(path.name)
    if m is None:
        return None
    return m.group("obf") + " X;"


def aggregate_parent(path: Path) -> dict:
    """Stream one knowledge file; return aggregate stats over its
    child rows.

    Uses running sums + a min-heap-free approach (mean / min / max
    only), plus a reservoir of all lb / ub for median computation.
    For large files (~200 MB) the reservoirs hold ~1-3M integers
    each; acceptable RAM at a few hundred MB peak.
    """
    n = 0
    sum_lb = 0
    sum_ub = 0
    min_lb = 10_000
    max_ub = -10_000
    exact = 0
    lbs: list[int] = []
    ubs: list[int] = []
    parse_errors = 0
    file_bytes = path.stat().st_size
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _LINE_RE.match(line)
            if m is None:
                parse_errors += 1
                continue
            # m.group(1) is the child OBF; we ignore it here.
            accuracy = int(m.group(3))
            score_lb = int(m.group(4))
            score_ub = int(m.group(5))
            n += 1
            sum_lb += score_lb
            sum_ub += score_ub
            if score_lb < min_lb:
                min_lb = score_lb
            if score_ub > max_ub:
                max_ub = score_ub
            if accuracy == 100:
                exact += 1
            lbs.append(score_lb)
            ubs.append(score_ub)
    if n == 0:
        return {
            "n_children": 0,
            "parse_errors": parse_errors,
            "bytes": file_bytes,
            "mean_lb": None, "mean_ub": None,
            "min_lb": None, "max_ub": None,
            "median_lb": None, "median_ub": None,
            "exact_count": 0, "exact_fraction": 0.0,
        }
    lbs.sort()
    ubs.sort()
    median_lb = lbs[n // 2]
    median_ub = ubs[n // 2]
    return {
        "n_children": n,
        "parse_errors": parse_errors,
        "bytes": file_bytes,
        "mean_lb": sum_lb / n,
        "mean_ub": sum_ub / n,
        "min_lb": min_lb,
        "max_ub": max_ub,
        "median_lb": median_lb,
        "median_ub": median_ub,
        "exact_count": exact,
        "exact_fraction": exact / n,
    }


def enumerate_archive(root: Path):
    """Yield (parent_obf_with_X_suffix, path) for every knowledge
    file in ``root``.  Skips anything whose filename does not match
    the regex."""
    for p in root.iterdir():
        if not p.is_file():
            continue
        obf = parent_obf_from_filename(p)
        if obf is None:
            continue
        yield obf, p


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Summarise a sample of 50 archive files to a CSV.
  python research/takizawa_archive_loader.py \\
      --archive /n/NORMSTOR/knowledge_archive \\
      --sample 50 \\
      --out ../results/phase1d_archive_summary.csv

  # Full scan (171 GB; takes minutes to hours depending on disk).
  python research/takizawa_archive_loader.py \\
      --archive /n/NORMSTOR/knowledge_archive \\
      --out ../results/phase1d_archive_summary_full.csv

reading the output:
  One row per knowledge file.  ``exact_fraction`` near 1.0 indicates
  all child sub-problems were solved to accuracy=100 (no residual
  uncertainty).  ``mean_lb`` / ``mean_ub`` are summary bounds for
  the parent's game-theoretic value.
""",
    )
    parser.add_argument(
        "--archive", type=Path, required=True,
        help="Root directory of Takizawa's knowledge archive "
             "(contains 2587 knowledge_*.csv files).",
    )
    parser.add_argument(
        "--out", type=Path, required=True,
        help="Output CSV path (parents created).",
    )
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Process only N files (deterministic order: sorted by "
             "filename).  Default: process all.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-file progress; only print the final summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if not args.archive.exists():
        print(f"archive root not found: {args.archive}", file=sys.stderr)
        return 2

    files = sorted(p for _, p in enumerate_archive(args.archive))
    if args.sample is not None:
        files = files[:args.sample]
    n = len(files)
    print(f"archive: {args.archive}")
    print(f"processing {n} knowledge files")

    t0 = time.time()
    fieldnames = [
        "parent_obf", "n_children", "bytes",
        "mean_lb", "mean_ub", "min_lb", "max_ub",
        "median_lb", "median_ub",
        "exact_count", "exact_fraction", "parse_errors",
    ]
    with args.out.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for i, path in enumerate(files, 1):
            parent_obf = parent_obf_from_filename(path)
            stats = aggregate_parent(path)
            row = {"parent_obf": parent_obf, **{
                k: stats.get(k) for k in fieldnames if k != "parent_obf"
            }}
            writer.writerow(row)
            if not args.quiet and (i % 50 == 0 or i == n):
                elapsed = time.time() - t0
                rate = i / max(elapsed, 1e-6)
                print(
                    f"  [{i}/{n}] {elapsed:.1f}s elapsed, "
                    f"{rate:.2f} files/s"
                )
    elapsed = time.time() - t0
    print(f"wrote {args.out}  ({elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
