r"""R-RBS-LM-ETAKNAV (#223 parts 3+2 / stress test before the srmech §51 ask) — HARDER de-lensing + ETAK NAVIGATION
over the tome-TREE and the cross-tome WEB, on a bigger genuinely-sparse real-vocab graph (stress-tests the sparse
Fiedler of F785 before we send it upstream).

PART 3 — harder de-lensing (three levers, F784):
  (a) drop the top-H highest-df hubs (vocab-level);
  (b) IDF-weight every edge by endpoint inverse-frequency  w' = w * (1-df_a/Ndoc) * (1-df_b/Ndoc)  (mass-sheet
      subtraction applied to the GRAPH -> suppress hub-incident edges, the residual function-word contamination);
  (c) sparsify to each node's top-K_NBR edges (kills the near-complete-graph artifact that misled F783/F785 and
      makes the graph genuinely SPARSE -> the real O(edges) stress case for the sparse Fiedler).

PART 2 — etak navigation: recursive sparse-Fiedler bisection now records the TREE (clumps-of-clumps, F780); the
  cut edges between leaf tomes are the WEB (F780). Demo: FIND (descend the tree to a query's tome = the zoom
  path), RIDE (the tome's coherent neighbourhood), WEB-HOP (cross the strongest bridge to an adjacent tome).

STRESS signal: K=1500 words (vs 400 in F785), deeper recursion, many sub-bisections -> does the sparse Fiedler
  CONVERGE everywhere (STATS.capped should be ~0)? timing / RAM / community density reported.

srmech 0.7.5rc165 (Class-L co-occurrence + dense normalized Fiedler for the gate; Class-K magnitude; rational.sqrt).
No numpy; no abs; no CAD; data outside repo; CC-BY-SA. Run from worktree root:
  MAX_ARTICLES=12000 /tmp/srmech_rc165/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-ETAKNAV_...py
"""
import json
import os
import resource
import time
from pathlib import Path
import srmech
from srmech.amsc import text as T
from srmech.amsc import laplacian as L
from srmech.amsc import cascade as K
from srmech.amsc import rational as R

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
WINDOW = 8
N = int(os.environ.get("MAX_ARTICLES", "12000"))
H_DROP = 120         # drop top-df hubs (vocab-level de-lensing)
K_KEEP = 1500        # content band (>> 400 of F785 -> stress)
K_NBR = 20           # keep each node's top-K_NBR IDF-weighted edges (sparsify)
MAXTOME = 12         # leaf when a clump is this small
T_ITERS = 300

SEED_TOPICS = {      # gate only
    "food":   "tomato potato onion garlic sauce recipe vegetable cooking".split(),
    "music":  "song album band guitar concert singer jazz melody".split(),
    "space":  "planet star orbit galaxy moon comet asteroid telescope".split(),
    "animal": "dog cat horse lion tiger mammal species wildlife".split(),
}
STATS = {"calls": 0, "capped": 0}


def fiedler_sparse(nodes, adj, t_iters=T_ITERS):
    """Normalized-cut power-iteration Fiedler (verified 100% vs dense in F785). Updates STATS convergence."""
    STATS["calls"] += 1
    n = len(nodes)
    if n < 2:
        return [0.0] * n
    pos = {g: i for i, g in enumerate(nodes)}
    nbr = [[] for _ in range(n)]
    deg = [0.0] * n
    for i, g in enumerate(nodes):
        for h, w in adj[g].items():
            j = pos.get(h)
            if j is not None:
                nbr[i].append((j, w)); deg[i] += w
    s = [(1.0 / R.sqrt(deg[i])) if deg[i] > 0 else 0.0 for i in range(n)]
    p = [R.sqrt(deg[i]) for i in range(n)]
    pn2 = sum(x * x for x in p)
    if pn2 <= 0:
        return [0.0] * n
    pnorm = R.sqrt(pn2); p = [x / pnorm for x in p]
    v = [1.0 if (k % 2 == 0) else -1.0 for k in range(n)]
    dot = sum(v[i] * p[i] for i in range(n)); v = [v[i] - dot * p[i] for i in range(n)]
    prev_sign, stable, converged = None, 0, False
    for it in range(t_iters):
        tmp = [s[j] * v[j] for j in range(n)]
        u = [v[i] + s[i] * sum(w * tmp[j] for j, w in nbr[i]) for i in range(n)]
        dot = sum(u[i] * p[i] for i in range(n)); u = [u[i] - dot * p[i] for i in range(n)]
        mx = max((float(K.magnitude(x)) for x in u), default=0.0)
        if mx <= 0:
            break
        v = [x / mx for x in u]
        sign = tuple(1 if x >= 0 else 0 for x in v)
        if sign == prev_sign and it >= 20:
            stable += 1
            if stable >= 5:
                converged = True; break
        else:
            stable = 0
        prev_sign = sign
    if not converged:
        STATS["capped"] += 1
    return v


def main():
    print(f"=== R-RBS-LM-ETAKNAV — harder de-lensing + etak tome-tree/web navigation (srmech {srmech.__version__}) ===")
    docs, n, df = [], 0, {}
    with open(ART) as f:
        for line in f:
            if n >= N:
                break
            try:
                d = json.loads(line)
            except ValueError:
                continue
            n += 1
            toks = T.tokenize(d.get("text", ""))
            docs.append(toks)
            for w in set(toks):
                df[w] = df.get(w, 0) + 1
    ndoc = n
    print(f"  loaded {ndoc} articles; {len(df)} distinct tokens")

    # --- gate: re-verify the sparse Fiedler is intact (vs dense normalized) ---
    sv = [w for ws in SEED_TOPICS.values() for w in ws]
    nv_s, e_s, w_s = T.cooccurrence_edges(docs, window=WINDOW, vocab=sv)
    adj_s = {i: {} for i in range(nv_s)}
    for (a, b), w in zip(e_s, w_s):
        adj_s[a][b] = adj_s[a].get(b, 0.0) + w; adj_s[b][a] = adj_s[b].get(a, 0.0) + w
    _, nvecs = L.symmetric_eigendecompose(L.normalized_laplacian(nv_s, e_s, w_s))
    sd = [1 if nvecs[i][1] >= 0 else 0 for i in range(nv_s)]
    sp = [1 if x >= 0 else 0 for x in fiedler_sparse(list(range(nv_s)), adj_s)]
    ag = max(sum(1 for a, b in zip(sd, sp) if a == b) / nv_s, 1 - sum(1 for a, b in zip(sd, sp) if a == b) / nv_s)
    print(f"  [GATE] sparse vs dense normalized Fiedler: {ag:.0%}  {'PASS' if ag >= 0.9 else 'FAIL'}")
    if ag < 0.9:
        return

    # --- PART 3: harder de-lensing ---
    ranked = sorted(df.items(), key=lambda kv: kv[1], reverse=True)
    content = [w for w, _ in ranked[H_DROP:H_DROP + K_KEEP]]
    cidx = {w: i for i, w in enumerate(content)}
    nv, edges, weights = T.cooccurrence_edges(docs, window=WINDOW, vocab=content)
    idf = [1.0 - df[content[i]] / ndoc for i in range(nv)]               # (b) endpoint inverse-frequency
    cand = {i: {} for i in range(nv)}
    raw = 0
    for (a, b), w in zip(edges, weights):
        raw += 1
        ww = w * idf[a] * idf[b]                                          # (b) de-lens the edge
        if ww > cand[a].get(b, 0.0):
            cand[a][b] = ww; cand[b][a] = ww
    adj = {i: {} for i in range(nv)}                                     # (c) sparsify to top-K_NBR per node
    for i in range(nv):
        for j, ww in sorted(cand[i].items(), key=lambda kv: kv[1], reverse=True)[:K_NBR]:
            adj[i][j] = ww; adj[j][i] = ww
    n_edges = sum(len(a) for a in adj.values()) // 2
    print(f"\n  de-lensed graph: dropped top-{H_DROP} hubs, kept {nv} content words; raw {raw} edges -> "
          f"IDF-weighted + top-{K_NBR} sparsified -> {n_edges} edges (genuinely sparse)")

    # --- PART 2: recursive bisection WITH tree (clumps-of-clumps) ---
    import sys
    sys.setrecursionlimit(10000)

    def cluster(nodes):
        if len(nodes) <= MAXTOME:
            return {"members": nodes, "children": None}
        fv = fiedler_sparse(nodes, adj)
        left = [nodes[i] for i in range(len(nodes)) if fv[i] < 0]
        right = [nodes[i] for i in range(len(nodes)) if fv[i] >= 0]
        if not left or not right:
            return {"members": nodes, "children": None}
        return {"members": nodes, "children": [cluster(left), cluster(right)]}

    t0 = time.time()
    tree = cluster(list(range(nv)))
    dt = time.time() - t0
    ram_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    leaves = []

    def collect(node, depth):
        if node["children"] is None:
            leaves.append((node["members"], depth))
        else:
            for ch in node["children"]:
                collect(ch, depth + 1)
    collect(tree, 0)
    tome_of = {}
    for t, (mem, _) in enumerate(leaves):
        for i in mem:
            tome_of[i] = t

    # community density (per possible pair)
    win = sum(w for i in range(nv) for j, w in adj[i].items() if i < j and tome_of[i] == tome_of[j])
    cross = sum(w for i in range(nv) for j, w in adj[i].items() if i < j and tome_of[i] != tome_of[j])
    win_pairs = sum(len(m) * (len(m) - 1) // 2 for m, _ in leaves)
    cross_pairs = nv * (nv - 1) // 2 - win_pairs
    depths = [d for _, d in leaves]
    print(f"  recursive sparse-Fiedler -> {len(leaves)} leaf tomes in {dt*1000:.0f} ms, peak RAM {ram_mb:.0f} MB")
    print(f"  STRESS: fiedler calls {STATS['calls']}, non-converged (capped) {STATS['capped']}  "
          f"(want ~0); tree depth {min(depths)}..{max(depths)}")
    print(f"  community (weight/possible pair): within {win/max(1,win_pairs):.2f} vs cross "
          f"{cross/max(1,cross_pairs):.2f} -> {(win/max(1,win_pairs))/max(1e-9,cross/max(1,cross_pairs)):.1f}x denser inside")

    # --- inter-tome WEB (cut edges between leaf tomes) ---
    web = {}
    bridges = {}
    for i in range(nv):
        for j, w in adj[i].items():
            if i < j and tome_of[i] != tome_of[j]:
                key = (min(tome_of[i], tome_of[j]), max(tome_of[i], tome_of[j]))
                web[key] = web.get(key, 0.0) + w
                bridges.setdefault(key, []).append((content[i], content[j], w))

    def tome_label(t):
        mem = leaves[t][0]
        return ", ".join(sorted((content[i] for i in mem), key=lambda w: df[w], reverse=True)[:8])

    # --- etak navigation demo on the 3 largest tomes ---
    def find_path(query_idx):
        path, node = [], tree
        while node["children"] is not None:
            c0 = node["children"][0]["members"]
            nxt = node["children"][0] if query_idx in c0 else node["children"][1]
            path.append("L" if nxt is node["children"][0] else "R")
            node = nxt
        return "".join(path), node

    print("\n  ETAK NAVIGATION (find -> ride -> web-hop), on the 3 largest tomes:")
    big = sorted(range(len(leaves)), key=lambda t: len(leaves[t][0]), reverse=True)[:3]
    for t in big:
        mem = leaves[t][0]
        q = max(mem, key=lambda i: df[content[i]])                    # representative (highest-df) word
        path, _ = find_path(q)
        # web-hop: strongest adjacent tome
        adj_tomes = sorted(((k, v) for k, v in web.items() if t in k), key=lambda kv: kv[1], reverse=True)
        print(f"   query '{content[q]}'")
        print(f"     FIND  -> tome #{t} via tree path {path or '(root leaf)'} (zoom depth {len(path)})")
        print(f"     RIDE  -> {{{tome_label(t)}}}")
        if adj_tomes:
            (k, v) = adj_tomes[0]; other = k[0] if k[1] == t else k[1]
            br = sorted(bridges[k], key=lambda x: x[2], reverse=True)[0]
            print(f"     WEB   -> hop to tome #{other} {{{tome_label(other)}}}  via bridge '{br[0]}'~'{br[1]}'")
        else:
            print("     WEB   -> (no cross-tome bridges; isolated community)")

    print(f"\nVERDICT: harder de-lensing (drop hubs + IDF edge-weight + top-{K_NBR} sparsify) yields a genuinely")
    print(f"  SPARSE {nv}-word graph; the sparse Fiedler converges across {STATS['calls']} sub-bisections "
          f"({STATS['capped']} capped) and the tomes navigate by etak (find->ride->web-hop) over the tome-tree +")
    print(f"  cut-edge web (F780). Stress-tested at {nv} words before the §51 srmech ask. (Clump lensing; math in data.)")


if __name__ == "__main__":
    main()
