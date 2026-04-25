"""Gear-DAG topology analysis -- the "periphery rule" for missing-gear placement.

Architectural prior (notebook section 11.7):

    Single-job gears -- those whose function affects only one output
    pointer -- should be loosely coupled, placed at the extremities of
    the mesh DAG, not in the load-bearing heart.  When adding a
    speculative gear (e.g. a planetary compensator), prefer leaves
    over high-centrality nodes so the core trains' ground truth
    is preserved.

This module operationalises the prior by computing graph-theoretic
metrics on ``gear_database.MESH_EDGES``:

- **degree**             how many other gears this one meshes with
- **distance from a1**   BFS hops from the input crank
- **distance from b1**   BFS hops from the main sun gear
- **leaf**               degree == 1 (terminal pointer or input)
- **bridge candidate**   degree >= 3 (load-bearing junction; perturbations
                         here propagate to multiple outputs)
- **periphery score**    composite: 1.0 = pure leaf, 0.0 = central bridge

The empirical question this module answers: do the surviving gears'
roles (calendar / lunar / Saros / planetary) line up with their
graph-centrality?  If yes, the architectural prior is real and
constrains the missing-gear search.  If not, the prior is an
overgeneralisation and we should look at why.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class TopologyEntry:
    name: str
    degree: int
    distance_from_a1: Optional[int]
    distance_from_b1: Optional[int]
    is_leaf: bool
    is_bridge: bool
    periphery_score: float
    train: str  # 'main', 'metonic', 'lunar', 'saros', 'unknown'


# ---------------------------------------------------------------------------
# Adjacency from gear_database
# ---------------------------------------------------------------------------

def _build_adjacency() -> Dict[str, Set[str]]:
    """Undirected adjacency map from gear_database.MESH_EDGES.

    Treats axle-share edges (label is None) and mesh edges identically
    for graph-centrality purposes; both transmit angular state.
    """
    from .gear_database import MESH_EDGES
    adj: Dict[str, Set[str]] = defaultdict(set)
    for driver, driven, _ in MESH_EDGES:
        adj[driver].add(driven)
        adj[driven].add(driver)
    return adj


def _bfs_distances(adj: Dict[str, Set[str]], source: str) -> Dict[str, int]:
    """BFS hop counts from ``source`` to every reachable node."""
    if source not in adj:
        return {}
    dist: Dict[str, int] = {source: 0}
    q = deque([source])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


# ---------------------------------------------------------------------------
# Train classification (mirrors gear_database.MESH_EDGES section comments)
# ---------------------------------------------------------------------------

_TRAIN_BY_GEAR: Dict[str, str] = {
    # Main drive
    "a1": "main", "b1": "main", "b2": "main",
    # Metonic chain
    "e2": "metonic", "e5": "metonic", "k1": "metonic", "e6": "metonic",
    "l1": "metonic", "l2": "metonic", "m1": "metonic",
    # Lunar / pin-and-slot
    "c1": "lunar", "c2": "lunar", "d1": "lunar", "d2": "lunar",
    "e1": "lunar", "e3": "lunar", "e4": "lunar", "k2": "lunar",
    # Saros
    "f1": "saros", "f2": "saros", "g1": "saros", "g2": "saros",
    "h1": "saros", "h2": "saros", "i1": "saros",
}


def _train_of(gear_name: str) -> str:
    return _TRAIN_BY_GEAR.get(gear_name, "unknown")


# ---------------------------------------------------------------------------
# Composite "periphery score"
# ---------------------------------------------------------------------------

def _periphery_score(degree: int, dist_b1: Optional[int],
                     max_dist: int) -> float:
    """Composite [0, 1] where 1 = pure leaf far from b1, 0 = central bridge.

    Three terms in equal weight:
      - leaf_term       : 1 if degree == 1 else 1 / degree
      - distance_term   : dist_b1 / max_dist (further = more peripheral)
      - non_bridge_term : 1 if degree < 3 else 0 (bridges are central)
    """
    leaf_term = 1.0 if degree <= 1 else 1.0 / degree
    if dist_b1 is None or max_dist == 0:
        distance_term = 0.0
    else:
        distance_term = dist_b1 / max_dist
    non_bridge_term = 1.0 if degree < 3 else 0.0
    return (leaf_term + distance_term + non_bridge_term) / 3.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def topology_report() -> List[TopologyEntry]:
    """Compute centrality + periphery score for every gear in the DAG."""
    adj = _build_adjacency()
    dist_a1 = _bfs_distances(adj, "a1")
    dist_b1 = _bfs_distances(adj, "b1")
    max_dist_b1 = max(dist_b1.values()) if dist_b1 else 1

    entries: List[TopologyEntry] = []
    for name in sorted(adj.keys()):
        deg = len(adj[name])
        d_b1 = dist_b1.get(name)
        entries.append(TopologyEntry(
            name=name,
            degree=deg,
            distance_from_a1=dist_a1.get(name),
            distance_from_b1=d_b1,
            is_leaf=(deg == 1),
            is_bridge=(deg >= 3),
            periphery_score=_periphery_score(deg, d_b1, max_dist_b1),
            train=_train_of(name),
        ))
    return entries


def core_gears(threshold: float = 0.4) -> List[str]:
    """Gears with periphery_score < threshold (load-bearing heart)."""
    return [e.name for e in topology_report()
            if e.periphery_score < threshold]


def peripheral_leaves(threshold: float = 0.65) -> List[str]:
    """Gears with periphery_score >= threshold (extremities; safe to extend)."""
    return [e.name for e in topology_report()
            if e.periphery_score >= threshold]


def bridge_gears() -> List[str]:
    """Gears with degree >= 3 -- candidates for differential / multi-train coupling."""
    return [e.name for e in topology_report() if e.is_bridge]


def candidate_attachment_points(allow_core: bool = False) -> List[str]:
    """Where a missing gear can attach.

    Default: peripheral leaves only.  ``allow_core=True`` includes
    bridges (typically required for planetary trains since the planetary
    plate physically attaches to b1)."""
    rep = topology_report()
    out = [e.name for e in rep if e.is_leaf]
    if allow_core:
        out += [e.name for e in rep if e.is_bridge]
    return sorted(set(out))


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default: full report sorted by periphery score:
  python -m research.gear_topology

  # Just the heart (core gears -- low periphery score):
  python -m research.gear_topology --core

  # Peripheral leaves (safe attachment points for missing gears):
  python -m research.gear_topology --peripheral

  # Bridge gears (degree >= 3 -- load-bearing junctions):
  python -m research.gear_topology --bridges

The "periphery rule" (notebook section 11.7): when adding a candidate
missing gear, prefer attaching at peripheral leaves over central
bridges.  This minimises cross-train error propagation and preserves
the surviving load-bearing chain (Metonic + Saros + lunar) as
ground truth.
"""


def _make_parser():
    parser = argparse.ArgumentParser(
        prog="python -m research.gear_topology",
        description=(
            "Graph-theoretic analysis of the gear DAG.  Operationalises "
            "the 'periphery rule' for missing-gear placement: single-job "
            "gears live at extremities; load-bearing trains live at the "
            "heart of the mesh graph."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--core", action="store_true",
        help="Print only the core gears (periphery_score < 0.4).",
    )
    parser.add_argument(
        "--peripheral", action="store_true",
        help="Print only peripheral leaves (periphery_score >= 0.65).",
    )
    parser.add_argument(
        "--bridges", action="store_true",
        help="Print only bridge gears (degree >= 3).",
    )
    parser.add_argument(
        "--train",
        choices=("main", "metonic", "lunar", "saros", "unknown", "all"),
        default="all",
        help="Filter to one train (default: all).",
    )
    return parser


def _print_entries(entries: List[TopologyEntry]) -> None:
    print(f"{'gear':<6} {'train':<8} {'deg':>3} {'d(a1)':>5} "
          f"{'d(b1)':>5} {'leaf':>4} {'bridge':>6} "
          f"{'periphery':>9}")
    print("-" * 66)
    for e in entries:
        d_a1 = e.distance_from_a1 if e.distance_from_a1 is not None else "-"
        d_b1 = e.distance_from_b1 if e.distance_from_b1 is not None else "-"
        print(f"{e.name:<6} {e.train:<8} {e.degree:>3} {str(d_a1):>5} "
              f"{str(d_b1):>5} {'Y' if e.is_leaf else ' ':>4} "
              f"{'Y' if e.is_bridge else ' ':>6} "
              f"{e.periphery_score:>9.3f}")


def main(argv=None):
    args = _make_parser().parse_args(argv)
    entries = topology_report()

    if args.train != "all":
        entries = [e for e in entries if e.train == args.train]

    if args.core:
        entries = [e for e in entries if e.periphery_score < 0.4]
        print("CORE gears (periphery_score < 0.4) -- the heart.")
        print("Adding missing gears here perturbs the load-bearing trains.")
    elif args.peripheral:
        entries = [e for e in entries if e.periphery_score >= 0.65]
        print("PERIPHERAL leaves (periphery_score >= 0.65) -- the extremities.")
        print("Safe attachment points for new gears (single-output impact).")
    elif args.bridges:
        entries = [e for e in entries if e.is_bridge]
        print("BRIDGE gears (degree >= 3) -- multi-train junctions.")
        print("Candidates for combination/differential roles.")
    else:
        entries = sorted(entries,
                         key=lambda e: (e.periphery_score, e.name))
        print("Full topology report (sorted by periphery_score, ascending):")

    print()
    _print_entries(entries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
