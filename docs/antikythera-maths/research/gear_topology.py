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


def candidate_attachment_points(allow_core: bool = False,
                                avoid_crank: bool = True,
                                ) -> List[str]:
    """Where a missing gear can attach under the periphery rule.

    Default: peripheral leaves only, and avoid the crank input shaft
    (a1) because (a) the crank is the operator interface and adding
    bronze there blocks the user, (b) the crank shaft already carries
    high mechanical stress per Voulgaris & Mouratidis 2018 (Mech.
    Mach. Theory 122: 207-218; "Calculating the torque on the shafts
    of the Antikythera Mechanism").

    ``allow_core=True`` includes bridge gears (b1, e5) -- typically
    required for planetary trains since Freeth 2021's planetary plate
    physically attaches to b1's shaft.
    """
    rep = topology_report()
    out = [e.name for e in rep if e.is_leaf]
    if allow_core:
        out += [e.name for e in rep if e.is_bridge]
    if avoid_crank and "a1" in out:
        out.remove("a1")
    return sorted(set(out))


def evaluate_attachment(attachment_point: str) -> Dict[str, object]:
    """Score a hypothetical attachment point against the periphery rule.

    Returns a dict with keys:
      gear            : the proposed attachment gear
      periphery_score : composite 0..1 (higher = safer)
      degree          : current degree (will increment by 1 if gear added)
      is_crank_shaft  : True iff attachment is at a1 (or shares its axle)
      verdict         : 'STRONG' | 'OK' | 'CAUTION' | 'AVOID'

    Verdict rules:
      STRONG  : leaf (degree 1), periphery >= 0.85, not crank
      OK      : periphery >= 0.65, degree <= 2, not crank
      CAUTION : periphery in [0.4, 0.65) -- transmission gear
      AVOID   : periphery < 0.4 (bridge / core), or crank shaft
    """
    rep = {e.name: e for e in topology_report()}
    if attachment_point not in rep:
        return {"gear": attachment_point, "verdict": "UNKNOWN",
                "note": "not in surviving DAG"}
    e = rep[attachment_point]
    is_crank = (attachment_point == "a1")

    if is_crank:
        verdict = "AVOID"
        note = ("Crank shaft (a1).  Adding bronze here blocks the "
                "operator's keyway and increases an already-high-"
                "torque shaft load (Voulgaris & Mouratidis 2018).")
    elif e.periphery_score < 0.4:
        verdict = "AVOID"
        note = ("Bridge / core gear.  Adding a mesh here perturbs "
                "multiple downstream trains' ground truth.")
    elif e.periphery_score < 0.65:
        verdict = "CAUTION"
        note = ("Mid-chain transmission.  Single perturbation propagates "
                "to one downstream train; acceptable if no peripheral "
                "alternative exists.")
    elif e.is_leaf and e.periphery_score >= 0.85:
        verdict = "STRONG"
        note = ("Pure leaf at the periphery.  Single-output impact; "
                "ideal for a single-purpose compensator.")
    else:
        verdict = "OK"
        note = ("Peripheral but not pure leaf.  Adding a mesh extends "
                "one train without core impact.")

    return {
        "gear": attachment_point,
        "periphery_score": e.periphery_score,
        "degree": e.degree,
        "is_crank_shaft": is_crank,
        "is_leaf": e.is_leaf,
        "is_bridge": e.is_bridge,
        "verdict": verdict,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Visualisation: portable SVG with manual layout (no graphviz dependency)
# ---------------------------------------------------------------------------

def _periphery_color(score: float) -> str:
    """Map periphery_score [0, 1] to a heat color (red = central, blue = peripheral).

    HSL hue: 0 (red) -> 240 (blue) over the [0, 1] range.
    """
    hue = int(240 * max(0.0, min(1.0, score)))
    return f"hsl({hue}, 75%, 55%)"


def _tooth_count_for_node(name: str) -> int:
    """Look up tooth count from gear_database, fallback to 50."""
    try:
        from .gear_database import ALL_GEARS, FREETH_2021
        for g in ALL_GEARS:
            if g.name == name:
                return g.canonical_count(FREETH_2021)
    except Exception:
        pass
    return 50


def render_svg(out_path: str = "figures/gear_topology.svg",
               width: int = 1100, height: int = 600) -> str:
    """Emit a self-contained SVG of the surviving gear DAG.

    Layout: BFS-distance-from-a1 on x-axis (input on left, leaves on right);
    deterministic y-axis spread within each distance band.
    Node color = periphery_score (red = central, blue = peripheral).
    Node size = tooth count.
    Solid edges = mesh; dashed = axle-share.
    """
    from .gear_database import MESH_EDGES

    rep = {e.name: e for e in topology_report()}
    if not rep:
        raise RuntimeError("No gears in DAG")

    # BFS distance from a1 for x-position
    max_dist = max(
        (e.distance_from_a1 for e in rep.values()
         if e.distance_from_a1 is not None),
        default=1,
    )

    # Group gears by distance band
    bands: Dict[int, List[str]] = defaultdict(list)
    for e in rep.values():
        d = e.distance_from_a1 if e.distance_from_a1 is not None else 0
        bands[d].append(e.name)
    for d in bands:
        bands[d].sort(key=lambda n: rep[n].train + n)

    # Position
    margin_x, margin_y = 60, 50
    inner_w = width - 2 * margin_x
    inner_h = height - 2 * margin_y
    pos: Dict[str, Tuple[float, float]] = {}
    for d, names in bands.items():
        x = margin_x + (d / max(1, max_dist)) * inner_w
        n = len(names)
        for i, name in enumerate(names):
            if n == 1:
                y = margin_y + inner_h / 2
            else:
                y = margin_y + (i / (n - 1)) * inner_h
            pos[name] = (x, y)

    # Build SVG
    out: List[str] = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {width} {height}" '
               f'font-family="sans-serif" font-size="11">')
    out.append('<rect width="100%" height="100%" fill="white"/>')

    # Title + legend
    out.append(f'<text x="{margin_x}" y="20" font-size="14" font-weight="bold">'
               'Antikythera surviving gear DAG '
               '(color = periphery score; size = tooth count)</text>')
    out.append(f'<text x="{margin_x}" y="38" font-size="10" fill="#888">'
               'red = core / bridge ; blue = leaf / extremity ; '
               'solid edge = mesh ; dashed = axle-share</text>')

    # Edges first (so nodes draw on top)
    for driver, driven, label in MESH_EDGES:
        if driver not in pos or driven not in pos:
            continue
        x1, y1 = pos[driver]
        x2, y2 = pos[driven]
        is_axle = (label is None)
        style = ('stroke="#888" stroke-width="1" stroke-dasharray="4,3"'
                 if is_axle else 'stroke="#444" stroke-width="1.5"')
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
                   f'x2="{x2:.1f}" y2="{y2:.1f}" {style}/>')

    # Nodes
    for name, e in rep.items():
        if name not in pos:
            continue
        x, y = pos[name]
        teeth = _tooth_count_for_node(name)
        # Radius: log-scaled tooth count, range ~8..22 px
        import math
        r = max(8.0, min(22.0, 7.0 + 4.0 * math.log10(max(2, teeth))))
        color = _periphery_color(e.periphery_score)
        stroke = "#000" if e.is_bridge else "#666"
        sw = 2 if e.is_bridge else 1
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                   f'fill="{color}" stroke="{stroke}" stroke-width="{sw}"/>')
        # Label below
        out.append(f'<text x="{x:.1f}" y="{y + r + 12:.1f}" '
                   f'text-anchor="middle" font-weight="bold">'
                   f'{name}</text>')
        out.append(f'<text x="{x:.1f}" y="{y + r + 24:.1f}" '
                   f'text-anchor="middle" fill="#666">'
                   f'{teeth}t  p={e.periphery_score:.2f}</text>')

    # Crank annotation (a1 is the operator interface; keyway only -- handle lost)
    if "a1" in pos:
        x, y = pos["a1"]
        out.append(f'<text x="{x:.1f}" y="{y - 28:.1f}" '
                   f'text-anchor="middle" font-style="italic" fill="#a00" '
                   f'font-size="10">(crank keyway -- handle lost)</text>')

    out.append("</svg>")

    from pathlib import Path
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text("\n".join(out), encoding="utf-8")
    return str(out_p.resolve())


def render_dot(out_path: str = "figures/gear_topology.dot") -> str:
    """Emit a Graphviz .dot file of the gear DAG (for users with graphviz)."""
    from .gear_database import MESH_EDGES

    rep = {e.name: e for e in topology_report()}
    lines: List[str] = ['digraph antikythera_gears {',
                        '  rankdir=LR;',
                        '  node [shape=circle, style=filled];']
    for name, e in rep.items():
        teeth = _tooth_count_for_node(name)
        color = _periphery_color(e.periphery_score)
        lines.append(f'  "{name}" [fillcolor="{color}", '
                     f'label="{name}\\n{teeth}t\\np={e.periphery_score:.2f}"];')
    for driver, driven, label in MESH_EDGES:
        if label is None:
            lines.append(f'  "{driver}" -> "{driven}" [style=dashed];')
        else:
            lines.append(f'  "{driver}" -> "{driven}";')
    lines.append('}')

    from pathlib import Path
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text("\n".join(lines), encoding="utf-8")
    return str(out_p.resolve())


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
        "--candidates", action="store_true",
        help="Print legal attachment points for missing gears "
             "(periphery rule + crank avoidance).",
    )
    parser.add_argument(
        "--allow-core", action="store_true",
        help="With --candidates: also include bridge gears "
             "(b1, e5).  Required for planetary-plate attachments.",
    )
    parser.add_argument(
        "--evaluate-attachment", default=None, metavar="GEAR",
        help="Score a hypothetical attachment point against the periphery "
             "rule and print STRONG/OK/CAUTION/AVOID verdict.",
    )
    parser.add_argument(
        "--train",
        choices=("main", "metonic", "lunar", "saros", "unknown", "all"),
        default="all",
        help="Filter to one train (default: all).",
    )
    parser.add_argument(
        "--svg", default=None, metavar="PATH",
        help="Render a self-contained SVG to PATH (default: "
             "figures/gear_topology.svg if --visualise without value).",
    )
    parser.add_argument(
        "--dot", default=None, metavar="PATH",
        help="Render a Graphviz .dot file to PATH.",
    )
    parser.add_argument(
        "--visualise", action="store_true",
        help="Shorthand for --svg figures/gear_topology.svg "
             "--dot figures/gear_topology.dot.",
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

    # Visualisation paths
    if args.visualise:
        if args.svg is None:
            args.svg = "figures/gear_topology.svg"
        if args.dot is None:
            args.dot = "figures/gear_topology.dot"
    if args.svg:
        path = render_svg(out_path=args.svg)
        print(f"Wrote SVG: {path}")
    if args.dot:
        path = render_dot(out_path=args.dot)
        print(f"Wrote DOT: {path}")
    if args.svg or args.dot:
        return 0

    # Attachment-point queries
    if args.evaluate_attachment:
        result = evaluate_attachment(args.evaluate_attachment)
        print(f"Attachment evaluation for {args.evaluate_attachment!r}:")
        for k, v in result.items():
            print(f"  {k:<18}: {v}")
        return 0

    if args.candidates:
        pts = candidate_attachment_points(allow_core=args.allow_core)
        print(f"Legal attachment points "
              f"(periphery rule, "
              f"{'incl. core' if args.allow_core else 'leaves only, no crank'}):")
        rep = {e.name: e for e in topology_report()}
        for name in pts:
            if name in rep:
                e = rep[name]
                print(f"  {name:<6} train={e.train:<8} "
                      f"degree={e.degree} "
                      f"periphery={e.periphery_score:.3f}")
        return 0

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
