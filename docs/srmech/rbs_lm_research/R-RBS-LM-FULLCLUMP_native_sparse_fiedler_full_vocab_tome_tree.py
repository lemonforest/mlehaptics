r"""R-RBS-LM-FULLCLUMP (#1 — the uncapped, spectrally-navigable smallwiki) — partition the FULL simplewiki vocab into
a hierarchical TOME-TREE with the rc166 NATIVE §51 sparse Fiedler (validated 100% vs dense). Finishes the F778→F785→
F786 arc at corpus scale: the n≤256 wall is gone natively, so this is a longer run of the SAME method, persisted.

Graph SOURCE: the assoc side-store (`simplewiki_assoc.json`, word → top-K co-occurrence neighbours) — already a sparse
k-NN co-occurrence graph, so NO 240k-article rescan. De-lensed (F784/F786): drop the top-H in-degree HUBS + sub-3-char
function tokens; IDF edge-weight w=idf(a)·idf(b) (idf from in-degree → suppress hub-incident edges). Recursive native
`normalized_cut_bisect` → the tome-tree (clumps-of-clumps, F780). Persisted to ~/corpora (OUTSIDE the repo).

srmech 0.7.5rc166 (native fiedler_sparse / normalized_cut_bisect). No numpy; no abs; no CAD; CC-BY-SA. Run:
  MAX_NODES=20000 /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-FULLCLUMP_...py   # sanity
  MAX_NODES=0     /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-FULLCLUMP_...py   # full
"""
import json
import os
import resource
import sys
import time
from pathlib import Path
import srmech
from srmech.amsc import laplacian as L

ASSOC = Path.home() / "corpora" / "wikipedia" / "simplewiki_assoc.json"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_tome_tree.json"
H_DROP = 300          # drop top-H in-degree hubs (de-lens TOP, F786)
MIN_INDEG = 3         # drop the rare/noise FLOOR (hapax + extraction artifacts aren't navigable communities)
MAXTOME = 12          # leaf when a clump is this small
MAX_ITERS = 250
MAX_NODES = int(os.environ.get("MAX_NODES", "0"))   # 0 = full content band
PROBES = "ketchup tomato planet star music guitar france dog volcano computer".split()


def main():
    sys.setrecursionlimit(1_000_000)
    print(f"=== R-RBS-LM-FULLCLUMP — full-vocab native tome-tree (srmech {srmech.__version__}) ===")
    t0 = time.time()
    assoc = json.loads(ASSOC.read_text()).get("assoc", {})
    indeg = {}
    for w, nbrs in assoc.items():
        for nb in nbrs:
            indeg[nb] = indeg.get(nb, 0) + 1
    # the CONTENT BAND (F786): rank by in-degree, drop the top-H hubs AND the rare/noise floor (in-degree < MIN_INDEG).
    ranked = sorted(indeg, key=indeg.get, reverse=True)
    hubs = set(ranked[:H_DROP])
    words = [w for w in ranked[H_DROP:] if indeg[w] >= MIN_INDEG and len(w) >= 3]
    if MAX_NODES:
        words = words[:MAX_NODES]                       # the most-connected MAX_NODES of the content band
    idx = {w: i for i, w in enumerate(words)}
    nv = len(words)

    def idf(w):
        return 1.0 / (1.0 + indeg.get(w, 0))

    adj = [dict() for _ in range(nv)]
    for w in words:
        i = idx[w]
        for nb in assoc.get(w, ()):
            j = idx.get(nb)
            if j is None or j == i:
                continue
            wt = idf(w) * idf(nb)
            if wt > adj[i].get(j, 0.0):
                adj[i][j] = wt
                adj[j][i] = wt
    n_edges = sum(len(d) for d in adj) // 2
    print(f"  graph: {nv} content words (dropped top-{H_DROP} hubs, e.g. {sorted(hubs, key=lambda w: -indeg[w])[:5]}), "
          f"{n_edges} edges ({time.time()-t0:.1f}s)")

    calls = [0]

    def bisect(nodes):
        if len(nodes) <= MAXTOME:
            return {"m": nodes, "c": None}
        pos = {g: k for k, g in enumerate(nodes)}
        edges, weights = [], []
        for g in nodes:
            for j, wt in adj[g].items():
                if j > g and j in pos:                 # j>g dedups; both must be members
                    edges.append((pos[g], pos[j])); weights.append(wt)
        if not edges:
            return {"m": nodes, "c": None}
        calls[0] += 1
        left, right = L.normalized_cut_bisect(len(nodes), edges, weights, max_iters=MAX_ITERS)
        if not left or not right:
            return {"m": nodes, "c": None}
        return {"m": nodes, "c": [bisect([nodes[k] for k in left]), bisect([nodes[k] for k in right])]}

    t1 = time.time()
    tree = bisect(list(range(nv)))
    dt = time.time() - t1
    ram_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    leaves = []

    def collect(node, depth):
        if node["c"] is None:
            leaves.append((node["m"], depth))
        else:
            collect(node["c"][0], depth + 1); collect(node["c"][1], depth + 1)
    collect(tree, 0)
    tome_of = {}
    for t, (mem, _) in enumerate(leaves):
        for g in mem:
            tome_of[g] = t
    win = cross = 0.0
    for g in range(nv):
        for j, wt in adj[g].items():
            if j > g:
                if tome_of[g] == tome_of[j]:
                    win += wt
                else:
                    cross += wt
    depths = [d for _, d in leaves]
    sizes = sorted((len(m) for m, _ in leaves), reverse=True)
    print(f"  recursive native bisection -> {len(leaves)} tomes in {dt:.1f}s ({calls[0]} native cuts), peak RAM {ram_mb:.0f} MB")
    print(f"  tree depth {min(depths)}..{max(depths)}; tome sizes max {sizes[0]} median {sizes[len(sizes)//2]}")
    print(f"  community: within edge-weight {win:.1f} vs cross {cross:.1f} -> within-fraction {win/max(1e-9,win+cross):.1%}")

    OUT.write_text(json.dumps({
        "source": "simplewiki_assoc", "srmech": srmech.__version__,
        "n_nodes": nv, "n_edges": n_edges, "h_drop": H_DROP, "maxtome": MAXTOME, "n_tomes": len(leaves),
        "tomes": [[words[g] for g in mem] for mem, _ in leaves], "depths": depths,
        "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/", "license": "CC-BY-SA-4.0",
                        "method": "native §51 normalized_cut_bisect recursive (srmech " + srmech.__version__ + ")"}}))
    print(f"  persisted tome-tree -> {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB)")
    print("\n  PROBE tomes (the tome each real word landed in — is it coherent?):")
    for p in PROBES:
        g = idx.get(p)
        if g is None:
            print(f"    {p:9}: (not in content band)"); continue
        mem = leaves[tome_of[g]][0]
        others = [words[k] for k in mem if k != g][:11]
        print(f"    {p:9}: {{{', '.join(others)}}}")


if __name__ == "__main__":
    main()
