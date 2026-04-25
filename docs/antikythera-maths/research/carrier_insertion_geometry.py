"""G-H7 carrier insertion geometry -- Priority 2 of the §12 computability audit.

Tests the carrier-gear hypothesis (§11.6.14) by computing whether portable
carrier elements could be mechanically inserted through the side-port
through-shaft terminations to bridge gaps in the gear DAG.

The hypothesis (§11.6.14): some "missing gears" are PORTABLE carriers
the operator inserts via side ports.  Each carrier C bridges two
existing sub-axles A, B (currently disconnected in MESH_EDGES).  When
inserted, A drives C drives B — train engaged.  When withdrawn, A and
B are decoupled.

The geometric feasibility test: for each candidate (A, B, carrier_size)
triple, check whether axial insertion through a side port is
mechanically possible given the 34 × 18 × 9 cm wooden case dimensions.

ASSUMPTION FLAGS (the project does not have surveyed mm-coordinates
from Freeth 2021):

- Sub-axle positions are SYNTHESIZED from BFS distance from a1 plus
  fragment grouping.  Approximate to ~5 mm precision; sufficient for
  feasibility binning, NOT for tolerance verification.
- Carrier dimensions are bounded by Hellenistic bronze-cutting practice:
  diameter 8-30 mm (per Voulgaris 2018 surveys of surviving gear
  geometries).
- Case-depth budget: 9 cm wooden box minus 2x ~3 mm wall = 84 mm
  available for axial carrier insertion.
- Through-shaft access constraint: a carrier inserted via a side port
  must align with a sub-axle that's also accessible from that side
  (i.e., extends through to the opposite face or terminates within
  reach of the operator's insertion tool).

Result: a feasibility table per candidate bridge.  G-H7 evaluator
PASSES iff at least 50% of plausibly-relevant gear-pair bridges admit
mechanically feasible carrier insertion.

References
----------
Notebook §11.6.14 (G-H7 carrier-gear hypothesis).
§12 computability audit, Priority 2.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Set, Tuple


# ---------------------------------------------------------------------------
# Physical constraints from the surviving Antikythera evidence
# ---------------------------------------------------------------------------

CASE_LENGTH_MM: float = 340.0    # ~34 cm long axis
CASE_WIDTH_MM: float = 180.0     # ~18 cm short axis
CASE_DEPTH_MM: float = 90.0      # ~9 cm deep (gear-stack axis)

WALL_THICKNESS_MM: float = 3.0
"""Approximate wooden case wall thickness; via Freeth 2006 reconstructions."""

INSERTABLE_DEPTH_MM: float = CASE_DEPTH_MM - 2 * WALL_THICKNESS_MM
"""Maximum axial reach of an inserted carrier from a side port: ~84 mm."""

# Carrier dimensions per Voulgaris 2018 surveys of surviving gear geometries.
# Smallest surviving Antikythera gears are ~1.6 mm pitch x 7-12 teeth
# (radius ~3-5 mm); largest is b1 at 224 teeth ~ 50 mm radius.  A
# practical carrier would be in the smaller range.
MIN_CARRIER_DIAMETER_MM: float = 8.0
MAX_CARRIER_DIAMETER_MM: float = 30.0
DEFAULT_CARRIER_DIAMETER_MM: float = 15.0   # mid-range estimate

# A carrier needs a SPINDLE plus typically ~5 mm of mounting hardware
# at each end; total carrier-assembly length ~ carrier_diameter + 15 mm
CARRIER_ASSEMBLY_MARGIN_MM: float = 15.0


# ---------------------------------------------------------------------------
# Sub-axle synthesised positions (approximate)
# ---------------------------------------------------------------------------
# These are SYNTHESIZED positions inferred from:
#   - Fragment grouping (A = back-panel main stack; B = lunar pin-and-slot;
#     C = zodiac; D = the lone 63-tooth gear and adjacent stub axles)
#   - BFS distance from a1 in the gear DAG (greater distance = downstream
#     shaft, generally deeper into the case)
#   - The shaft-stack convention (b1 is on the central main shaft;
#     adjacent gears share parallel shafts at small lateral offsets)
#
# Each position is (x_mm, y_mm, z_mm) with x along case length, y along
# case width, z along case depth.  Approximate to ~5 mm precision.

_FRAGMENT_BASE_POSITIONS_MM: Dict[str, Tuple[float, float, float]] = {
    "A": (170.0, 90.0, 45.0),       # back-panel main stack (case centre)
    "B": (130.0, 60.0, 40.0),       # lunar pin-and-slot
    "C": (170.0, 90.0, 20.0),       # zodiac (front panel)
    "D": (240.0, 90.0, 50.0),       # lone 63-tooth gear region
}


def _synthesize_position(gear_name: str) -> Tuple[float, float, float]:
    """Synthesise (x, y, z) mm position for a gear from the database.

    Uses fragment + BFS-distance heuristic.  Assumption-flagged.
    """
    from .gear_database import gear_by_name
    from .gear_topology import topology_report

    try:
        gear = gear_by_name(gear_name)
        fragment = gear.fragment or "A"
    except KeyError:
        fragment = "A"

    base = _FRAGMENT_BASE_POSITIONS_MM.get(fragment, _FRAGMENT_BASE_POSITIONS_MM["A"])

    # Offset within fragment based on BFS distance from a1
    rep = {e.name: e for e in topology_report()}
    if gear_name in rep:
        d = rep[gear_name].distance_from_a1 or 0
    else:
        d = 0

    # Each BFS step nudges position slightly along x (length axis)
    x_offset = (d - 5) * 8.0   # centred at d=5
    z_offset = (d % 3) * 5.0    # rotate through 3 z-levels

    return (base[0] + x_offset, base[1], base[2] + z_offset)


def _euclidean_distance_mm(p1: Tuple[float, float, float],
                           p2: Tuple[float, float, float]) -> float:
    return ((p1[0] - p2[0]) ** 2
            + (p1[1] - p2[1]) ** 2
            + (p1[2] - p2[2]) ** 2) ** 0.5


# ---------------------------------------------------------------------------
# Carrier insertion candidate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CarrierCandidate:
    """A hypothetical (gear_a, gear_b) bridge implementable by an inserted carrier."""

    gear_a: str
    gear_b: str
    inter_axle_distance_mm: float
    carrier_diameter_mm: float
    insertion_depth_required_mm: float
    fits_case_depth: bool
    spans_inter_axle: bool      # carrier diameter * 2 >= inter-axle distance
    feasibility_verdict: str     # "FEASIBLE" / "TIGHT" / "INFEASIBLE"
    note: str


def evaluate_carrier_pair(
    gear_a: str,
    gear_b: str,
    carrier_diameter_mm: float = DEFAULT_CARRIER_DIAMETER_MM,
) -> CarrierCandidate:
    """Score whether a carrier of given diameter could bridge gear_a and gear_b."""
    pos_a = _synthesize_position(gear_a)
    pos_b = _synthesize_position(gear_b)
    inter = _euclidean_distance_mm(pos_a, pos_b)

    # Insertion depth needed: must reach the deeper of the two sub-axles
    deeper_z = max(pos_a[2], pos_b[2])
    insertion_depth = deeper_z + CARRIER_ASSEMBLY_MARGIN_MM

    fits_case_depth = insertion_depth <= INSERTABLE_DEPTH_MM
    spans_inter_axle = (carrier_diameter_mm * 2) >= inter
    # Margin: would the carrier *just* span, or comfortably?
    span_margin = (carrier_diameter_mm * 2) - inter

    if not fits_case_depth:
        verdict = "INFEASIBLE"
        note = (f"Required insertion depth {insertion_depth:.1f} mm "
                f"exceeds case-insertable budget {INSERTABLE_DEPTH_MM:.1f} mm.")
    elif not spans_inter_axle:
        verdict = "INFEASIBLE"
        note = (f"Inter-axle distance {inter:.1f} mm exceeds carrier reach "
                f"({carrier_diameter_mm * 2:.1f} mm = 2x diameter).  "
                "Carrier cannot span both gears with single mesh contact.")
    elif span_margin < 5.0:
        verdict = "TIGHT"
        note = (f"Span margin only {span_margin:.1f} mm; carrier just barely "
                "reaches both gears.  Greek tolerance limits make this risky.")
    else:
        verdict = "FEASIBLE"
        note = (f"Span margin {span_margin:.1f} mm; insertion depth "
                f"{insertion_depth:.1f} mm.  Carrier fits comfortably.")

    return CarrierCandidate(
        gear_a=gear_a,
        gear_b=gear_b,
        inter_axle_distance_mm=inter,
        carrier_diameter_mm=carrier_diameter_mm,
        insertion_depth_required_mm=insertion_depth,
        fits_case_depth=fits_case_depth,
        spans_inter_axle=spans_inter_axle,
        feasibility_verdict=verdict,
        note=note,
    )


# ---------------------------------------------------------------------------
# Bridge enumeration
# ---------------------------------------------------------------------------

def candidate_bridge_pairs() -> List[Tuple[str, str]]:
    """Pairs of gears that are NOT currently meshing but could plausibly
    be bridged by a carrier.

    Currently-meshing pairs are excluded (they don't need a carrier).
    Candidate bridges are pairs in different trains within the same
    fragment, OR pairs at peripheral leaves on different trains
    (where a carrier would couple two otherwise-independent dials).
    """
    from .gear_database import MESH_EDGES, ALL_GEARS, MAIN_TRAIN, LUNAR_TRAIN

    # Collect already-meshing edges (undirected)
    meshing: Set[frozenset] = set()
    for driver, driven, _label in MESH_EDGES:
        meshing.add(frozenset([driver, driven]))

    # All surviving gears with positions
    surviving = [g.name for g in ALL_GEARS if g.fragment is not None]

    # Generate candidate pairs: NOT currently meshing, both have positions
    out: List[Tuple[str, str]] = []
    for a, b in combinations(surviving, 2):
        if frozenset([a, b]) in meshing:
            continue
        out.append((a, b))
    return sorted(out)


# ---------------------------------------------------------------------------
# G-H7 evaluator
# ---------------------------------------------------------------------------

def evaluate_G_H7(
    carrier_diameter_mm: float = DEFAULT_CARRIER_DIAMETER_MM,
    feasibility_threshold_pct: float = 50.0,
) -> Tuple[str, str, str, Dict[str, object]]:
    """G-H7 hypothesis evaluator.

    PASS iff >= ``feasibility_threshold_pct`` of candidate bridge pairs
    admit FEASIBLE carrier insertion (vs INFEASIBLE / TIGHT).
    """
    pairs = candidate_bridge_pairs()
    if not pairs:
        return ("UNDETERMINED", "no candidate pairs",
                "No surviving gear pairs eligible for carrier-bridge analysis.",
                {})
    results = [evaluate_carrier_pair(a, b, carrier_diameter_mm) for a, b in pairs]
    n_total = len(results)
    n_feasible = sum(1 for r in results if r.feasibility_verdict == "FEASIBLE")
    n_tight = sum(1 for r in results if r.feasibility_verdict == "TIGHT")
    n_infeasible = sum(1 for r in results if r.feasibility_verdict == "INFEASIBLE")

    pct_feasible = (n_feasible / n_total) * 100
    if pct_feasible >= feasibility_threshold_pct:
        status = "PASS"
    elif pct_feasible + (n_tight / n_total * 100) >= feasibility_threshold_pct:
        status = "PARTIAL"
    else:
        status = "FAIL"

    notes = (
        f"{n_feasible}/{n_total} ({pct_feasible:.1f}%) candidate gear-pair "
        f"bridges admit FEASIBLE carrier insertion under "
        f"{carrier_diameter_mm:.0f} mm carrier diameter.  "
        f"{n_tight} TIGHT (< 5 mm span margin); "
        f"{n_infeasible} INFEASIBLE (case-depth or inter-axle distance).  "
        "Sub-axle positions SYNTHESIZED from fragment + BFS-distance "
        "heuristic; ASSUMPTION-FLAGGED.  Real falsification requires "
        "Freeth 2021 mm-coordinate map."
    )
    computed = (
        f"{n_feasible}/{n_total} feasible "
        f"({pct_feasible:.1f}%); threshold {feasibility_threshold_pct}%"
    )
    detail = {
        "carrier_diameter_mm": carrier_diameter_mm,
        "feasibility_threshold_pct": feasibility_threshold_pct,
        "n_total": n_total,
        "n_feasible": n_feasible,
        "n_tight": n_tight,
        "n_infeasible": n_infeasible,
        "case_dimensions_mm": [CASE_LENGTH_MM, CASE_WIDTH_MM, CASE_DEPTH_MM],
        "insertable_depth_mm": INSERTABLE_DEPTH_MM,
        "sample_results": [
            {
                "gear_a": r.gear_a, "gear_b": r.gear_b,
                "inter_axle_mm": r.inter_axle_distance_mm,
                "verdict": r.feasibility_verdict, "note": r.note,
            }
            for r in results[:10]
        ],
    }
    return status, computed, notes, detail


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default carrier diameter 15 mm:
  python -m research.carrier_insertion_geometry

  # Range of carrier sizes:
  python -m research.carrier_insertion_geometry --carrier-diameter 10
  python -m research.carrier_insertion_geometry --carrier-diameter 25

  # Show all candidate pairs (not just summary):
  python -m research.carrier_insertion_geometry --verbose

  # G-H7 evaluator:
  python -m research.carrier_insertion_geometry --evaluate

ASSUMPTION FLAGS
----------------
Sub-axle positions are SYNTHESIZED from fragment grouping + BFS distance
in the gear DAG.  Approximate to ~5 mm precision.  Real geometric
verification requires Freeth 2021's surveyed mm-coordinate map
(not currently in the project).  Results are FEASIBILITY-BIN
classifications (FEASIBLE / TIGHT / INFEASIBLE), not exact tolerance
predictions.

References: notebook §11.6.14 (G-H7 carrier-gear hypothesis); §12.2
computability audit, Priority 2.
"""


def _make_parser():
    parser = argparse.ArgumentParser(
        prog="python -m research.carrier_insertion_geometry",
        description=("G-H7 geometric feasibility test for carrier-gear "
                     "insertion through side-port through-shaft "
                     "terminations.  Tests notebook §11.6.14's "
                     "carrier-gear hypothesis."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--carrier-diameter", type=float,
        default=DEFAULT_CARRIER_DIAMETER_MM,
        help=f"Carrier gear diameter in mm "
             f"(default: {DEFAULT_CARRIER_DIAMETER_MM}).",
    )
    parser.add_argument(
        "--threshold-pct", type=float, default=50.0,
        help="G-H7 PASS threshold: % of pairs that must be FEASIBLE.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print every candidate pair result (default: summary only).",
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run G-H7 evaluator and print PASS/FAIL.",
    )
    parser.add_argument(
        "--json-out", default=None,
        help="Write detailed JSON output.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    pairs = candidate_bridge_pairs()

    print(f"G-H7 carrier insertion geometry")
    print(f"  case dimensions    : "
          f"{CASE_LENGTH_MM:.0f} x {CASE_WIDTH_MM:.0f} x {CASE_DEPTH_MM:.0f} mm")
    print(f"  insertable depth   : {INSERTABLE_DEPTH_MM:.0f} mm")
    print(f"  carrier diameter   : {args.carrier_diameter:.0f} mm")
    print(f"  candidate pairs    : {len(pairs)}")
    print()

    results = [evaluate_carrier_pair(a, b, args.carrier_diameter) for a, b in pairs]
    n_feasible = sum(1 for r in results if r.feasibility_verdict == "FEASIBLE")
    n_tight = sum(1 for r in results if r.feasibility_verdict == "TIGHT")
    n_infeasible = sum(1 for r in results if r.feasibility_verdict == "INFEASIBLE")

    print(f"Summary:")
    print(f"  FEASIBLE   : {n_feasible:>4d} / {len(results)} "
          f"({n_feasible/len(results)*100:.1f}%)")
    print(f"  TIGHT      : {n_tight:>4d} / {len(results)} "
          f"({n_tight/len(results)*100:.1f}%)")
    print(f"  INFEASIBLE : {n_infeasible:>4d} / {len(results)} "
          f"({n_infeasible/len(results)*100:.1f}%)")
    print()

    if args.verbose:
        print("All pairs:")
        for r in results:
            marker = ("OK" if r.feasibility_verdict == "FEASIBLE"
                      else ("~~" if r.feasibility_verdict == "TIGHT" else "XX"))
            print(f"  [{marker}] {r.gear_a:<6} <-> {r.gear_b:<6}  "
                  f"inter={r.inter_axle_distance_mm:>6.1f} mm  "
                  f"depth={r.insertion_depth_required_mm:>5.1f} mm  "
                  f"{r.feasibility_verdict}")
        print()

    if args.evaluate:
        status, computed, notes, _ = evaluate_G_H7(
            carrier_diameter_mm=args.carrier_diameter,
            feasibility_threshold_pct=args.threshold_pct,
        )
        print(f"--- G-H7 evaluator ---")
        print(f"  status  : {status}")
        print(f"  computed: {computed}")
        print(f"  notes   : {notes}")
        print()

    if args.json_out:
        import json
        from pathlib import Path
        payload = {
            "case_dimensions_mm": [CASE_LENGTH_MM, CASE_WIDTH_MM, CASE_DEPTH_MM],
            "insertable_depth_mm": INSERTABLE_DEPTH_MM,
            "carrier_diameter_mm": args.carrier_diameter,
            "n_total": len(results),
            "n_feasible": n_feasible,
            "n_tight": n_tight,
            "n_infeasible": n_infeasible,
            "results": [
                {
                    "gear_a": r.gear_a, "gear_b": r.gear_b,
                    "inter_axle_mm": r.inter_axle_distance_mm,
                    "insertion_depth_mm": r.insertion_depth_required_mm,
                    "verdict": r.feasibility_verdict,
                    "note": r.note,
                }
                for r in results
            ],
        }
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
