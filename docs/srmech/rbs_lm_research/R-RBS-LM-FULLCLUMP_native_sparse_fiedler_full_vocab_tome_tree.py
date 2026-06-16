r"""R-RBS-LM-FULLCLUMP (#1 + #223 tail — the uncapped, spectrally-navigable smallwiki) — partition the FULL simplewiki
vocab into a hierarchical TOME-TREE with the rc166 NATIVE §51 sparse Fiedler, and persist BOTH the tree (per-leaf path,
for zoom-to-parent) AND the inter-tome WEB (cut edges, for cross-clump hops) — the F780 clumps-of-clumps + webs, so
Siona can etak-navigate it (FIND→RIDE→WEB-HOP, F791).

Graph SOURCE: the assoc side-store (word → top-K co-occurrence neighbours; sparse — no 240k rescan). De-lensed (F784/
F786): drop the top-H in-degree HUBS + the rare floor (in-degree < MIN_INDEG) + ARTIFACT tokens (concatenation junk:
overlong, or word+month merges from infobox extraction). IDF edge-weight w=idf(a)·idf(b). Recursive native
`normalized_cut_bisect` → leaves carry their L/R PATH (the tree); cut edges aggregated → per-tome top bridge tomes.

srmech 0.7.5rc166 (native fiedler). No numpy; no abs; no CAD; CC-BY-SA. Persisted OUTSIDE the repo. Run:
  MAX_NODES=0 /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-FULLCLUMP_...py
"""
import json
import os
import re
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path
import srmech
from srmech.amsc import laplacian as L

ASSOC = Path.home() / "corpora" / "wikipedia" / "simplewiki_assoc.json"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_tome_tree.json"
H_DROP = 300
MIN_INDEG = 3
MAXTOME = 12
MAX_ITERS = 250
MAX_NODES = int(os.environ.get("MAX_NODES", "0"))
PROBES = "ketchup tomato planet star music guitar france dog volcano computer".split()
_MONTH = re.compile(r".+(january|february|march|april|may|june|july|august|september|october|november|december)$")


def is_artifact(w):
    """concatenation junk from infobox extraction: overlong tokens, or a word+month merge (e.g. 'bouncedecember')."""
    return len(w) > 18 or bool(_MONTH.match(w))


def main():
    sys.setrecursionlimit(1_000_000)
    print(f"=== R-RBS-LM-FULLCLUMP — full-vocab native tome-tree + web (srmech {srmech.__version__}) ===")
    t0 = time.time()
    assoc = json.loads(ASSOC.read_text()).get("assoc", {})
    indeg = {}
    for w, nbrs in assoc.items():
        for nb in nbrs:
            indeg[nb] = indeg.get(nb, 0) + 1
    ranked = sorted(indeg, key=indeg.get, reverse=True)
    hubs = set(ranked[:H_DROP])
    words = [w for w in ranked[H_DROP:] if indeg[w] >= MIN_INDEG and 3 <= len(w) <= 18 and not is_artifact(w)]
    if MAX_NODES:
        words = words[:MAX_NODES]
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
                adj[i][j] = wt; adj[j][i] = wt
    n_edges = sum(len(d) for d in adj) // 2
    print(f"  graph: {nv} content words (dropped top-{H_DROP} hubs + rare/artifact), {n_edges} edges ({time.time()-t0:.1f}s)")

    leaves = []                       # (members, path) — path is the L/R tree address (F780 clumps-of-clumps)
    calls = [0]

    def bisect(nodes, path):
        if len(nodes) <= MAXTOME:
            leaves.append((nodes, path)); return
        pos = {g: k for k, g in enumerate(nodes)}
        edges, weights = [], []
        for g in nodes:
            for j, wt in adj[g].items():
                if j > g and j in pos:
                    edges.append((pos[g], pos[j])); weights.append(wt)
        if not edges:
            leaves.append((nodes, path)); return
        calls[0] += 1
        left, right = L.normalized_cut_bisect(len(nodes), edges, weights, max_iters=MAX_ITERS)
        if not left or not right:
            leaves.append((nodes, path)); return
        bisect([nodes[k] for k in left], path + "L")
        bisect([nodes[k] for k in right], path + "R")

    t1 = time.time()
    bisect(list(range(nv)), "")
    dt = time.time() - t1
    ram_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    tome_of = {}
    for t, (mem, _) in enumerate(leaves):
        for g in mem:
            tome_of[g] = t

    # the WEB: aggregate cut edges per tome-pair, remember the strongest bridge word-pair (F780)
    web = {}
    win = cross = 0.0
    for g in range(nv):
        for j, wt in adj[g].items():
            if j <= g:
                continue
            ta, tb = tome_of[g], tome_of[j]
            if ta == tb:
                win += wt; continue
            cross += wt
            key = (ta, tb) if ta < tb else (tb, ta)
            e = web.get(key)
            if e is None:
                web[key] = [wt, wt, g, j]
            else:
                e[0] += wt
                if wt > e[1]:
                    e[1] = wt; e[2] = g; e[3] = j
    byt = defaultdict(list)
    for (ta, tb), (tot, _bw, gi, gj) in web.items():
        byt[ta].append((tot, tb, gi, gj)); byt[tb].append((tot, ta, gi, gj))
    webout = {}
    for t, lst in byt.items():
        lst.sort(reverse=True)
        webout[t] = [[other, round(tot, 4), words[gi], words[gj]] for tot, other, gi, gj in lst[:3]]

    depths = [len(p) for _, p in leaves]
    print(f"  native bisection -> {len(leaves)} tomes in {dt:.1f}s ({calls[0]} cuts), peak RAM {ram_mb:.0f} MB; depth {min(depths)}..{max(depths)}")
    print(f"  community: within {win:.1f} vs cross {cross:.1f} -> within-fraction {win/max(1e-9,win+cross):.1%}; web tome-pairs {len(web)}")

    OUT.write_text(json.dumps({
        "source": "simplewiki_assoc", "srmech": srmech.__version__, "n_nodes": nv, "n_edges": n_edges,
        "h_drop": H_DROP, "min_indeg": MIN_INDEG, "maxtome": MAXTOME, "n_tomes": len(leaves),
        "tomes": [[words[g] for g in mem] for mem, _ in leaves],
        "paths": [p for _, p in leaves],
        "web": webout,
        "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/", "license": "CC-BY-SA-4.0",
                        "method": f"native §51 normalized_cut_bisect recursive (srmech {srmech.__version__})"}}))
    print(f"  persisted tome-tree + web -> {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB)")

    # quick nav demo on the probes: FIND -> RIDE -> ZOOM(parent) -> WEB-HOP
    paths = [p for _, p in leaves]
    for p in PROBES:
        g = idx.get(p)
        if g is None:
            print(f"    {p:9}: (not in content band)"); continue
        t = tome_of[g]
        ride = [words[k] for k in leaves[t][0] if k != g][:8]
        pre = paths[t][:-1]
        sib = [i for i, pp in enumerate(paths) if pp.startswith(pre) and i != t]
        parent = sorted({words[k] for i in sib for k in leaves[i][0]})[:8]
        hop = webout.get(t, [])
        hp = f" | WEB→#{hop[0][0]} via {hop[0][2]}~{hop[0][3]}" if hop else ""
        print(f"    {p:9} (tome {t}): RIDE {ride}  | ZOOM {parent}{hp}")


if __name__ == "__main__":
    main()
