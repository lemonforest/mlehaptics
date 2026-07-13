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

# F1207 REPOINT: the source is now the WEIGHTED full_sparse_kernel (edge_list + edge_weights = TRUE co-occurrence
# weights) — the correct object. Falls back to a legacy top-K assoc (word->names, IDF-of-degree proxy) if given one.
SRC = Path(os.environ.get("KERNEL") or os.environ.get("ASSOC")
           or str(Path.home() / "corpora" / "wikipedia" / "simplewiki_full_sparse_kernel.json"))
OUT = Path(os.environ.get("OUT", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_tome_tree.json")))
H_DROP = int(os.environ.get("H_DROP", "300"))               # drop top-df hubs (scale H_DROP with the graph, e.g. enwiki)
MIN_INDEG = int(os.environ.get("MIN_INDEG", "3"))
MAXTOME = int(os.environ.get("MAXTOME", "12"))
MAX_ITERS = 250
MAX_NODES = int(os.environ.get("MAX_NODES", "0"))
# true_idf = the TRUE co-occurrence weight DE-LENSED by IDF (hub suppression, F784/F786) — the right default:
# raw 'true' weights let frequency lens the partition (small-kernel within-fraction 4.5% -> 63.5% with true_idf,
# coherent domain tomes: volcano~pinatubo~kilauea, planet~ixion~varda). 'true' | 'idf' (legacy proxy) also selectable.
WEIGHT_MODE = os.environ.get("WEIGHT_MODE", "true_idf")
SRC_LABEL = SRC.stem                                        # e.g. 'simplewiki_full_sparse_kernel' (attestation)
PROBES = "ketchup tomato planet star music guitar france dog volcano computer".split()
_MONTH = re.compile(r".+(january|february|march|april|may|june|july|august|september|october|november|december)$")


def is_artifact(w):
    """concatenation junk from infobox extraction: overlong tokens, or a word+month merge (e.g. 'bouncedecember')."""
    return len(w) > 18 or bool(_MONTH.match(w))


def load_graph():
    """Load the graph source and build the de-lensed weighted adjacency. The WEIGHTED full_sparse_kernel path uses
    the TRUE co-occurrence weights (F1207 repoint); the legacy top-K assoc path uses the IDF-of-degree proxy (the
    substitute for the weights it lacked). De-lensing is structural + weight-agnostic: drop top-H in-degree hubs +
    rare floor (in-degree < MIN_INDEG) + artifact tokens. Returns (words, idx, adj, indeg, n_edges, weighted)."""
    k = json.loads(SRC.read_text())
    weighted = bool(k.get("edge_list")) and bool(k.get("edge_weights"))
    indeg = {}
    if weighted:                                            # in-degree from the real edges (for hub-drop + rare floor)
        vocab = k["vocab"]
        for a, b in k["edge_list"]:
            indeg[vocab[a]] = indeg.get(vocab[a], 0) + 1
            indeg[vocab[b]] = indeg.get(vocab[b], 0) + 1
    else:
        for w, nbrs in k.get("assoc", {}).items():
            for nb in nbrs:
                indeg[nb] = indeg.get(nb, 0) + 1
    ranked = sorted(indeg, key=indeg.get, reverse=True)
    words = [w for w in ranked[H_DROP:] if indeg[w] >= MIN_INDEG and 3 <= len(w) <= 18 and not is_artifact(w)]
    if MAX_NODES:
        words = words[:MAX_NODES]
    idx = {w: i for i, w in enumerate(words)}
    nv = len(words)

    def idf(w):
        return 1.0 / (1.0 + indeg.get(w, 0))

    adj = [dict() for _ in range(nv)]
    if weighted:
        vocab, ew = k["vocab"], k["edge_weights"]
        for (a, b), wraw in zip(k["edge_list"], ew):
            i, j = idx.get(vocab[a]), idx.get(vocab[b])
            if i is None or j is None or i == j:
                continue
            wt = float(wraw)                                # TRUE co-occurrence weight (the repoint)
            if WEIGHT_MODE == "idf":
                wt = idf(vocab[a]) * idf(vocab[b])
            elif WEIGHT_MODE == "true_idf":                 # true weight, de-lensed by IDF (hub suppression, F784/F786)
                wt = float(wraw) * idf(vocab[a]) * idf(vocab[b])
            if wt > adj[i].get(j, 0.0):
                adj[i][j] = wt; adj[j][i] = wt
    else:
        assoc = k.get("assoc", {})
        for w in words:
            i = idx[w]
            for nb in assoc.get(w, ()):
                j = idx.get(nb)
                if j is None or j == i:
                    continue
                wt = idf(w) * idf(nb)
                if wt > adj[i].get(j, 0.0):
                    adj[i][j] = wt; adj[j][i] = wt
    return words, idx, adj, indeg, sum(len(d) for d in adj) // 2, weighted


def main():
    sys.setrecursionlimit(1_000_000)
    print(f"=== R-RBS-LM-FULLCLUMP — full-vocab native tome-tree + web (srmech {srmech.__version__}) ===")
    t0 = time.time()
    words, idx, adj, indeg, n_edges, weighted = load_graph()
    nv = len(words)
    print(f"  graph: {nv} content words (dropped top-{H_DROP} hubs + rare/artifact), {n_edges} edges, "
          f"weights={'TRUE co-occurrence (%s)' % WEIGHT_MODE if weighted else 'IDF proxy (legacy assoc)'} "
          f"({time.time()-t0:.1f}s)")

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
        "source": SRC_LABEL, "srmech": srmech.__version__, "n_nodes": nv, "n_edges": n_edges,
        "weighted": weighted, "weight_mode": WEIGHT_MODE if weighted else "idf_proxy_legacy",
        "h_drop": H_DROP, "min_indeg": MIN_INDEG, "maxtome": MAXTOME, "n_tomes": len(leaves),
        "tomes": [[words[g] for g in mem] for mem, _ in leaves],
        "paths": [p for _, p in leaves],
        "web": webout,
        "attestation": {"source_url": f"https://dumps.wikimedia.org/{SRC_LABEL.split('_')[0]}/latest/", "license": "CC-BY-SA-4.0",
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
