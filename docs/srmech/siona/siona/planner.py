"""siona.planner — the NOVEL COMPOSITION planner (#255, F1107): the missing piece over the substrate F1106 found.

F1106 established that the novel composition LANGUAGE already exists — the provenance-carrying ``carry``-chain
(``op_provenance.carry`` atoms + ``dispatch.infer`` verified routing + ``carrier_ladder_descriptor`` reachability).
What was missing is the PLANNER that BUILDS the chain from a goal. This is it: given a start carrier (what you
HAVE) and a goal carrier (what you WANT), GRAPH-SEARCH the carrier ladder for a chain of ops from start → goal,
and emit the composition as an ordered op-list — or an honest OPEN when no route exists (never a hallucinated
one; F929's no-hallucination discipline made structural).

The carrier graph (from ``carrier_ladder_descriptor``, F1038/#1254):
  * NODES  = carrier types — ``(ladder, rung)`` (e.g. ``variable:1`` = Poly) or a leaf ``type`` (``float`` / ``Mat``).
  * EDGES  = (a) OPS: each op's ``consumes`` → ``produces`` (label = the op tool); (b) LADDER promote/project
             between consecutive rungs (label = the ladder's promote/project op).

The planner searches the FLAT peer carrier-graph (F1102 — no privileged root to force queries through). The
emitted chain is runnable via ``op_provenance.carry``, so the composition is verified-or-honest-OPEN by
construction. This is novel-reduction-on-request (F1042): novel COMPOSITION of known ops, held whole. numpy-free.
"""
import collections

import srmech.amsc.carrier_ladder as _CL

__all__ = ["plan", "carrier_graph"]


def _node(spec):
    """Canonical node key for a carrier spec ``{ladder, rung}`` or a leaf ``{ladder: None, type}``."""
    if spec.get("ladder"):
        return "%s:%s" % (spec["ladder"], spec["rung"])
    return spec.get("type") or "?"


def carrier_graph():
    """Build the typed reachability graph from ``carrier_ladder_descriptor``: ``{node: [(next_node, op_label)]}``,
    plus a ``{carrier_name: node}`` alias map (``Poly`` → ``variable:1``)."""
    d = _CL.carrier_ladder_descriptor()
    adj = collections.defaultdict(list)
    for name, op in d["ops"].items():                    # (a) ops: consumes -> produces
        adj[_node(op["consumes"])].append((_node(op["produces"]), op["tool"]))
    for lname, lad in d["ladders"].items():              # (b) ladder promote/project between consecutive rungs
        rungs = sorted(lad["rungs"].values())
        for r in rungs:
            if (r + 1) in rungs:
                lo, hi = "%s:%d" % (lname, r), "%s:%d" % (lname, r + 1)
                adj[lo].append((hi, lad.get("promote", "promote")))    # promote UP
                adj[hi].append((lo, lad.get("project", "project")))    # project DOWN
    names = {nm: _node({"ladder": c.get("ladder"), "rung": c.get("rung")}) for nm, c in d["carriers"].items()}
    return adj, names


def plan(start, goal, *, max_hops=6):
    """GRAPH-SEARCH the carrier ladder for an op-chain from ``start`` carrier to ``goal`` carrier (#255/F1107).

    ``start`` / ``goal`` are carrier NAMES (``Poly``, ``BiPoly``) or canonical nodes (``variable:1``,
    ``cayley_dickson:8``, ``float``). Returns ``{"found": True, "chain": [op tools], "path": [nodes]}`` — the
    composition, a provenance-carrying carry-chain — or an honest ``{"found": False, "open": True, …}`` when no
    route exists (never a hallucinated one; F929). BFS ⇒ the SHORTEST op-chain."""
    adj, names = carrier_graph()
    s, g = names.get(start, start), names.get(goal, goal)
    q = collections.deque([(s, [], [s])])
    seen = {s}
    while q:
        node, chain, path = q.popleft()
        if node == g:
            return {"found": True, "chain": chain, "path": path}
        if len(chain) >= max_hops:
            continue
        for nxt, op in adj.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, chain + [op], path + [nxt]))
    return {"found": False, "open": True, "start": s, "goal": g}   # honest OPEN — no route, not a hallucination
