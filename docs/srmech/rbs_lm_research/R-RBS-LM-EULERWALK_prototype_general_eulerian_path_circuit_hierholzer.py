r"""R-RBS-LM-EULERWALK (F1224 / #1390 item 3) — PROTOTYPE the general `eulerian_path` / `eulerian_circuit` op.

srmech-upstream candidate #3: the Hierholzer walk-reconstruction srmech LACKS (it has magnetic_/signed_laplacian
but no Eulerian primitive). Rebuilds the ordered sequence from a DIRECTED EDGE MULTISET — the sandroing round-trip
(F1080/F1213), a word = a directed glyph-walk. Here abstracted out of NIVDIRECTED's domain-bound `eulerian_word`
into a clean, node-type-agnostic graph op, PROVEN to (a) reproduce `eulerian_word` on the real directed word kernels
and (b) handle circuits, self-loops, and the HONEST no-Eulerian-path / disconnected cases (returns None, does not lie).

srmech 0.9.0rc241; exact ints; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-EULERWALK_...py

ADOPTED UPSTREAM (F1286): `eulerian_path / eulerian_circuit` now ships in `srmech.amsc.laplacian`. This file is the PROTOTYPE RECORD and is
kept as-run, but NEW code must call the shipped op — copying the local definition forward
means maintaining a second, less-tested implementation of a supported surface.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent


# ------------------------------------------------------------------------------------------------------------------
# THE PROPOSED srmech OP (prototype). Signatures drafted for #1390 item 3, to live under srmech.amsc.laplacian.
#   eulerian_path(edges, start=None)    -> [node,...] (len = |edges|+1)  or None if no Eulerian trail exists
#   eulerian_circuit(edges, start=None) -> [node,...] (start==end)       or None if the graph is not balanced+connected
# edges: a DIRECTED multiset [(u,v),...] (repeats allowed; nodes any hashable; self-loops OK). Hierholzer, O(|E|).
# Feasibility is CHECKED (degree balance + full-consumption connectivity) — an infeasible graph returns None, never a
# partial walk. Deterministic: the derived start is the min out>in node (path) or the min out-bearing node (circuit).
# ------------------------------------------------------------------------------------------------------------------
def _degrees(edges):
    outs, outdeg, indeg, nodes = {}, {}, {}, set()
    for u, v in edges:
        outs.setdefault(u, []).append(v)
        outdeg[u] = outdeg.get(u, 0) + 1
        indeg[v] = indeg.get(v, 0) + 1
        nodes.add(u)
        nodes.add(v)
    return outs, outdeg, indeg, nodes


def eulerian_path(edges, start=None):
    """Directed edge MULTISET -> the Eulerian trail (node list), or None if none exists. Handles self-loops."""
    if not edges:
        return [start] if start is not None else []
    outs, outdeg, indeg, nodes = _degrees(edges)
    plus = [n for n in nodes if outdeg.get(n, 0) - indeg.get(n, 0) == 1]     # the unique open-path START (out = in + 1)
    minus = [n for n in nodes if indeg.get(n, 0) - outdeg.get(n, 0) == 1]    # the unique open-path END   (in = out + 1)
    imbalanced = [n for n in nodes if outdeg.get(n, 0) != indeg.get(n, 0)]
    if not imbalanced:                                                      # EULERIAN CIRCUIT: any out-bearing node
        s = start if start is not None else min(n for n in nodes if outdeg.get(n, 0) > 0)
    elif len(plus) == 1 and len(minus) == 1 and len(imbalanced) == 2:       # EULERIAN PATH: the +1 node is the only start
        s = plus[0]
    else:
        return None                                                        # degree condition fails -> no Eulerian trail
    avail = {n: list(v) for n, v in outs.items()}                          # Hierholzer: consume EVERY edge exactly once
    stack, walk = [s], []
    while stack:
        v = stack[-1]
        if avail.get(v):
            stack.append(avail[v].pop())
        else:
            walk.append(stack.pop())
    walk.reverse()
    if len(walk) != len(edges) + 1:                                        # not all edges consumed -> DISCONNECTED
        return None                                                        # (honest: no single Eulerian trail spans it)
    return walk


def eulerian_circuit(edges, start=None):
    """As eulerian_path, but REQUIRES a closed circuit (every node balanced). Returns a walk with start==end, or None."""
    if not edges:
        return [start] if start is not None else []
    _outs, outdeg, indeg, nodes = _degrees(edges)
    if any(outdeg.get(n, 0) != indeg.get(n, 0) for n in nodes):            # not balanced -> no circuit
        return None
    return eulerian_path(edges, start=start)


# ------------------------------------------------------------------------------------------------------------------
def _load_nivdirected():
    p = HERE / "R-RBS-LM-NIVDIRECTED_word_as_directed_glyph_graph_genome_native.py"
    spec = importlib.util.spec_from_file_location("nivdirected", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _directed_edges(k):
    """Recover the directed glyph-edge multiset from the signed graph (metric+charge) — the magnetic-Laplacian edge
    recovery (w_fwd, w_bwd) = ((w+c)//2, (w-c)//2); domain-agnostic (this split is item-1's inverse)."""
    de = []
    for (i, j), w, c in zip(k["edge_list"], k["edge_weights"], k["edge_charge"]):
        f, r = (w + c) // 2, (w - c) // 2
        de += [(i, j)] * f + [(j, i)] * r
    return de


def main():
    print("=== R-RBS-LM-EULERWALK — general eulerian_path/eulerian_circuit (Hierholzer), item 3 prototype ===\n")

    # (A) EQUIVALENCE: the general op reproduces the domain-bound eulerian_word on the REAL directed word kernels
    N = _load_nivdirected()
    words = "cat listen level banana sandroing vanuatu mississippi reappear committee order ocean".split()
    match = 0
    print("  (A) equivalence vs NIVDIRECTED.eulerian_word (same Hierholzer, node-agnostic):")
    for w in words:
        k = N.word_to_kernel(w)
        idx = eulerian_path(_directed_edges(k), start=k["start"])
        general = "".join(k["vocab"][t] for t in idx) if idx is not None else None
        domain = N.eulerian_word(k)
        same = (general == domain)
        match += same
        print("     %-12s general=%r  eulerian_word=%r  match=%s" % (w, general, domain, "OK" if same else "XX"))
    print("     -> %d/%d identical\n" % (match, len(words)))

    # (B) the graph primitives on synthetic cases: circuit, path, self-loop, and the HONEST refusals
    print("  (B) synthetic graph cases (deterministic):")
    cases = [
        ("triangle circuit", [(0, 1), (1, 2), (2, 0)], "circuit"),
        ("simple path",      [(0, 1), (1, 2), (2, 3)], "path"),
        ("self-loop",        [(0, 0), (0, 1), (1, 0)], "circuit"),
        ("figure-eight",     [(0, 1), (1, 0), (0, 2), (2, 0)], "circuit"),
        ("NO euler (out+2)", [(0, 1), (0, 2)], None),
        ("disconnected",     [(0, 1), (2, 3)], None),
    ]
    ok = 0
    for name, edges, kind in cases:
        p = eulerian_path(edges)
        c = eulerian_circuit(edges)
        if kind is None:
            good = (p is None)                                             # no Eulerian trail -> both refuse
        else:
            good = (p is not None and len(p) == len(edges) + 1
                    and all((p[t], p[t + 1]) in _consume(edges) for t in range(len(p) - 1))
                    and (kind != "circuit" or (c is not None and c[0] == c[-1])))
        ok += good
        print("     %-18s path=%s circuit=%s  %s"
              % (name, p, c, "OK" if good else "XX"))
    print("     -> %d/%d\n" % (ok, len(cases)))

    verdict = (match == len(words) and ok == len(cases))
    print("VERDICT: %s — eulerian_path/eulerian_circuit is a faithful, node-agnostic Hierholzer that reproduces\n"
          "         eulerian_word on real kernels (%d/%d), walks circuits/paths/self-loops, and HONESTLY returns\n"
          "         None for degree-infeasible or disconnected graphs (%d/%d). Ready as #1390 item 3 (with a C mirror)."
          % ("PASS" if verdict else "FAIL — investigate", match, len(words), ok, len(cases)))
    return 0 if verdict else 1


def _consume(edges):
    """the set of directed edges present (for the synthetic validity check — membership, not multiplicity)."""
    return set(edges)


if __name__ == "__main__":
    sys.exit(main())
