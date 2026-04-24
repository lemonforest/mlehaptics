"""Open item 4 — §2.H5 holonomy loop characterisation.

§2.H5 (phase 1) tested 4 hand-picked loops and found that one — the
rectangle (0,0)-(0,3)-(1,3)-(1,0)-(0,0) — carried full Z2 holonomy
(cos = -1).  That was enough to confirm H5 PASS, but did not
characterise WHICH loops carry holonomy.

This runner enumerates all minimal plaquettes on the 8x8 grid and
records the holonomy cosine of each:

  unit plaquettes  (1x1 squares) : 7x7 = 49
  2x2 plaquettes   (2x2 squares) : 6x6 = 36
  3x3 plaquettes   (3x3 squares) : 5x5 = 25
  m x 1 "bars"     (1 row, varying width) : 7 * 7 = 49
  1 x n "bars"     (varying height, 1 col): 7 * 7 = 49
  triangle corners (diagonal triangles)   :  4 cases

and clusters loops by whether their cos is near +1 (trivial) or
-1 (Z2-holonomy) or intermediate.

Interpretation: the set of non-trivial loops defines the "Berry
curvature" of the static fiber bundle — a geometric signature of
the 8-ray structure over the 8x8 lattice.  Under §10.4's framework
this curvature is a pure-geometry property, independent of any
piece configuration, so the result is a once-per-board-topology
measurement.

Outputs:
  results/phase1e_holonomy_plaquettes.csv   (one row per loop)
  results/phase1e_holonomy_plaquettes.json  (summary stats)
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from othello_utils import BOARD_SIZE, rc_to_idx
from static_fiber_bundle import parallel_transport_cos


def _unit_plaquettes() -> list[dict]:
    loops = []
    for r in range(BOARD_SIZE - 1):
        for c in range(BOARD_SIZE - 1):
            path = [
                (r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c), (r, c),
            ]
            loops.append({
                "kind": "unit_1x1",
                "top_left_r": r,
                "top_left_c": c,
                "path_rc": path,
            })
    return loops


def _square_plaquettes(side: int) -> list[dict]:
    """side-by-side square plaquette (side in cells).  Path walks
    the perimeter clockwise from top-left."""
    loops = []
    for r in range(BOARD_SIZE - side):
        for c in range(BOARD_SIZE - side):
            path = []
            # top edge  L->R
            for k in range(side + 1):
                path.append((r, c + k))
            # right edge down
            for k in range(1, side + 1):
                path.append((r + k, c + side))
            # bottom edge R->L
            for k in range(1, side + 1):
                path.append((r + side, c + side - k))
            # left edge up back to start
            for k in range(1, side + 1):
                path.append((r + side - k, c))
            loops.append({
                "kind": f"square_{side}x{side}",
                "top_left_r": r,
                "top_left_c": c,
                "path_rc": path,
            })
    return loops


def _rect_bars(width: int, height: int) -> list[dict]:
    loops = []
    for r in range(BOARD_SIZE - height):
        for c in range(BOARD_SIZE - width):
            path = []
            for k in range(width + 1):
                path.append((r, c + k))
            for k in range(1, height + 1):
                path.append((r + k, c + width))
            for k in range(1, width + 1):
                path.append((r + height, c + width - k))
            for k in range(1, height + 1):
                path.append((r + height - k, c))
            loops.append({
                "kind": f"rect_{width}x{height}",
                "top_left_r": r,
                "top_left_c": c,
                "path_rc": path,
            })
    return loops


def _triangle_corners() -> list[dict]:
    """Corner triangles walking along an edge, a diagonal, and back."""
    loops = []
    # main diagonal corners
    corners = [
        [(0, 0), (0, 7), (7, 7), (0, 0)],
        [(0, 0), (7, 0), (7, 7), (0, 0)],
        [(0, 7), (7, 7), (7, 0), (0, 7)],
        [(0, 0), (0, 7), (7, 0), (0, 0)],
    ]
    for i, path in enumerate(corners):
        loops.append({
            "kind": f"triangle_{i}",
            "top_left_r": path[0][0],
            "top_left_c": path[0][1],
            "path_rc": path,
        })
    return loops


def _long_jump_rectangles(
    widths: list[int], heights: list[int],
) -> list[dict]:
    """Long-jump rectangles: the 4-corner version of a wxh rectangle.

    Walks corners directly without intermediate cells — matches the
    §2.H5 convention where the rectangle
    (0,0)-(0,3)-(1,3)-(1,0)-(0,0) was measured as a 4-step loop
    rather than an 8-step perimeter walk.

    The distinction matters: the sign-matched parallel-transport
    algorithm accumulates per-step alignment, so the same *topological*
    loop can give different holonomy depending on how it is
    discretised.
    """
    loops = []
    for h in heights:
        for w in widths:
            for r in range(BOARD_SIZE - h):
                for c in range(BOARD_SIZE - w):
                    path = [
                        (r, c), (r, c + w),
                        (r + h, c + w), (r + h, c),
                        (r, c),
                    ]
                    loops.append({
                        "kind": f"lj_rect_{w}x{h}",
                        "top_left_r": r,
                        "top_left_c": c,
                        "path_rc": path,
                    })
    return loops


def enumerate_loops(include_bars: bool = True) -> list[dict]:
    loops = []
    loops.extend(_unit_plaquettes())
    loops.extend(_square_plaquettes(2))
    loops.extend(_square_plaquettes(3))
    if include_bars:
        # Thin bars: width x 1 and 1 x height where m != n
        for w in range(2, 8):
            loops.extend(_rect_bars(w, 1))
        for h in range(2, 8):
            loops.extend(_rect_bars(1, h))
    loops.extend(_triangle_corners())
    # Long-jump rectangles: 4-corner walks (matches the §2.H5
    # convention where the single non-trivial loop was measured
    # with corner-only transport, not perimeter steps).
    loops.extend(
        _long_jump_rectangles(
            widths=list(range(1, 8)),
            heights=list(range(1, 8)),
        )
    )
    return loops


def measure_loop(loop: dict) -> dict:
    path_rc = loop["path_rc"]
    path_idx = [rc_to_idx(r, c) for r, c in path_rc]
    result = parallel_transport_cos(path_idx)
    return {
        "kind": loop["kind"],
        "top_left_r": loop["top_left_r"],
        "top_left_c": loop["top_left_c"],
        "len_path": result["len_path"],
        "sign_flips": result["sign_flips"],
        "loop_cosine": result["loop_cosine"],
    }


def classify(cos: float, tol: float = 0.01) -> str:
    if abs(cos - 1.0) < tol:
        return "trivial"
    if abs(cos + 1.0) < tol:
        return "Z2_holonomy"
    return "intermediate"


def run(out_csv: Path, out_json: Path, tol: float) -> dict:
    loops = enumerate_loops(include_bars=True)
    print(f"enumerated {len(loops)} loops total")
    rows = []
    for loop in loops:
        r = measure_loop(loop)
        r["classification"] = classify(r["loop_cosine"], tol=tol)
        rows.append(r)

    by_kind: dict[str, dict[str, int]] = {}
    for r in rows:
        d = by_kind.setdefault(
            r["kind"], {"n": 0, "trivial": 0, "Z2": 0, "intermediate": 0}
        )
        d["n"] += 1
        if r["classification"] == "trivial":
            d["trivial"] += 1
        elif r["classification"] == "Z2_holonomy":
            d["Z2"] += 1
        else:
            d["intermediate"] += 1

    # Aggregate overall
    total = {"n": len(rows), "trivial": 0, "Z2": 0, "intermediate": 0}
    for r in rows:
        if r["classification"] == "trivial":
            total["trivial"] += 1
        elif r["classification"] == "Z2_holonomy":
            total["Z2"] += 1
        else:
            total["intermediate"] += 1

    # Write CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    summary = {
        "tol": tol,
        "n_loops": len(rows),
        "total_breakdown": total,
        "by_kind": by_kind,
    }
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Stdout highlights
    print(f"\n=== §2.H5 holonomy characterisation (N = {len(rows)} loops) ===")
    print(f"{'kind':20s}  {'N':>4s}  {'trivial':>8s}  {'Z2':>4s}  {'inter':>6s}")
    for kind, stats in sorted(by_kind.items()):
        print(
            f"{kind:20s}  {stats['n']:>4d}  {stats['trivial']:>8d}  "
            f"{stats['Z2']:>4d}  {stats['intermediate']:>6d}"
        )
    print(f"{'ALL':20s}  {total['n']:>4d}  {total['trivial']:>8d}  "
          f"{total['Z2']:>4d}  {total['intermediate']:>6d}")
    print(f"\nZ2 fraction: {total['Z2'] / total['n']:.3f}")
    print(f"wrote {out_csv}")
    print(f"wrote {out_json}")
    return summary


def _build_parser():
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python research/phase1e_holonomy_plaquettes.py

reading the output:
  'by_kind' breakdown shows which loop families carry Z2 holonomy.
  §2.H5 found the (0,0)-(0,3)-(1,3)-(1,0) rectangle was non-trivial;
  this runner extends that to all rectangles, unit plaquettes,
  squares and corner triangles.  A loop family that is 0/N non-
  trivial is a 'flat' region of the connection; a family mixed
  non-trivial with trivial shows spatial structure in the curvature.
""",
    )
    p.add_argument(
        "--out-csv", type=Path,
        default=default_results / "phase1e_holonomy_plaquettes.csv",
    )
    p.add_argument(
        "--out-json", type=Path,
        default=default_results / "phase1e_holonomy_plaquettes.json",
    )
    p.add_argument(
        "--tol", type=float, default=0.01,
        help="|cos -/+ 1| tolerance for trivial/Z2 classification.",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    run(args.out_csv, args.out_json, args.tol)
    return 0


if __name__ == "__main__":
    sys.exit(main())
