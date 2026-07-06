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

__all__ = ["plan", "run", "run_goal", "carrier_graph"]


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


# ---------------------------------------------------------------------------------------------------------------
# The RUN-step (F1108, #255) — PLAN + EXECUTE: plan the op-chain, then thread the actual value through it,
# attaching a provenance record per step. Most planner ops (promote/project/octonion/…) are NOT in the
# op_provenance.carry registry (that covers only the asymptotic-tower frontier), so we attach our OWN lightweight
# provenance — op address + input_sha256 (via the framework hash) + in/out carrier — which is still re-runnable
# BY NAME (the F1106 language). Verified-or-honest-OPEN: no route → OPEN; a step that cannot execute → honest
# "planned but not runnable", never a faked result.
import importlib as _importlib

from srmech.amsc.format import sha256_bytes as _sha256_bytes


def _resolve(dotted):
    mod, fn = dotted.rsplit(".", 1)
    return getattr(_importlib.import_module(mod), fn)


def run(start_value, goal, *, start_carrier=None):
    """PLAN + RUN a novel composition (#255/F1108): plan the op-chain from ``start_value``'s carrier to ``goal``,
    then EXECUTE it — resolve each op tool, thread the value through (output → next input), and attach a
    provenance record per step. Returns ``{"found": True, "ran": True, "value": …, "carrier": …, "chain": […],
    "steps": [{op, in, out, input_sha256}]}`` — the composition RUN with provenance — or an honest OPEN (no
    route) / "planned-but-not-runnable" (a step could not execute). ``start_carrier`` defaults to the value's type."""
    sc = start_carrier or type(start_value).__name__
    p = plan(sc, goal)
    if not p["found"]:
        return {"found": False, "open": True, "start_carrier": sc, "goal": goal}
    val, steps = start_value, []
    for op in p["chain"]:
        prev = type(val).__name__
        in_sha = _sha256_bytes(repr(val).encode("utf-8"))         # framework hash (already hex), per discipline
        try:
            val = _resolve(op)(val)                               # thread: op applied to the running value
        except Exception as exc:                                  # honest: planned but a step won't execute
            return {"found": True, "ran": False, "failed_at": op, "error": str(exc)[:140],
                    "chain": p["chain"], "steps": steps}
        steps.append({"op": op, "in": prev, "out": type(val).__name__, "input_sha256": in_sha})
    return {"found": True, "ran": True, "value": val, "carrier": type(val).__name__,
            "chain": p["chain"], "steps": steps}


def run_goal(start_value, goal_text, *, start_carrier=None):
    """NL-goal → PLAN + RUN (#255/F1109): TYPE the natural-language ``goal_text`` to a carrier
    (:func:`siona.goal_typing.goal_carrier`), then :func:`run`. Returns run()'s result annotated with
    ``goal_text`` + ``goal_carrier`` — or ``{"found": False, "untyped": True}`` when the goal cannot be typed
    (honest — no guess, F552). Closes the natural-language goal-end of #255."""
    from siona.goal_typing import goal_carrier
    gc = goal_carrier(goal_text)
    if gc is None:
        return {"found": False, "untyped": True, "goal_text": goal_text}
    out = run(start_value, gc, start_carrier=start_carrier)
    out["goal_text"], out["goal_carrier"] = goal_text, gc
    return out
