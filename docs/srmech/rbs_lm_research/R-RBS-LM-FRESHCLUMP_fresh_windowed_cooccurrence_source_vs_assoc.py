r"""R-RBS-LM-FRESHCLUMP (#223 #3 — the fresh-source quality lever) — build the clump SOURCE graph from a FRESH windowed
co-occurrence pass over the corpus (clean srmech tokenization), instead of the pre-built assoc top-K (which carries
extraction artifacts). Same de-lensing + native §51 clump as FULLCLUMP; compare probe coherence to the assoc tree.

Source: stream MAX_ARTICLES, tokenize (srmech text.tokenize — clean), df-select the content band (drop top-H df hubs +
keep next K by df), build a FRESH windowed co-occurrence (text.cooccurrence_edges), IDF-weight (w=idf(a)·idf(b), idf
from df), sparsify to top-K_NBR per node. Recursive native normalized_cut_bisect -> tome-tree + web. Persist to a
SEPARATE file (don't clobber the deployed assoc tree until validated).

srmech 0.7.5rc166 (native fiedler). No numpy; no abs; no CAD; CC-BY-SA. Run from worktree root:
  MAX_ARTICLES=30000 /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-FRESHCLUMP_...py
"""
import json
import os
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path
import srmech
from srmech.amsc import text as T
from srmech.amsc import laplacian as L

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_tome_tree_fresh.json"
N = int(os.environ.get("MAX_ARTICLES", "30000"))
WINDOW = 6
H_DROP = 200          # drop top-df hubs
K_KEEP = int(os.environ.get("K_KEEP", "12000"))   # content band by df
K_NBR = 20            # sparsify to top-K_NBR per node
MAXTOME = 12
MAX_ITERS = 250
PROBES = "ketchup tomato planet star guitar dog volcano music france computer".split()


def main():
    sys.setrecursionlimit(1_000_000)
    print(f"=== R-RBS-LM-FRESHCLUMP — fresh windowed co-occurrence source (srmech {srmech.__version__}) ===")
    t0 = time.time()
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
    ranked = sorted(df, key=df.get, reverse=True)
    vocab = [w for w in ranked[H_DROP:] if df[w] >= 5 and 3 <= len(w) <= 18][:K_KEEP]
    print(f"  {ndoc} articles; content vocab {len(vocab)} (dropped top-{H_DROP} df hubs; e.g. kept {vocab[:6]}) ({time.time()-t0:.1f}s)")

    nv, edges, weights = T.cooccurrence_edges(docs, window=WINDOW, vocab=vocab)   # FRESH windowed co-occurrence
    print(f"  fresh co-occurrence: {len(edges)} raw edges ({time.time()-t0:.1f}s)")
    idf = [1.0 - df[vocab[i]] / ndoc for i in range(nv)]
    cand = [dict() for _ in range(nv)]
    for (a, b), w in zip(edges, weights):
        ww = w * idf[a] * idf[b]
        if ww > cand[a].get(b, 0.0):
            cand[a][b] = ww; cand[b][a] = ww
    adj = [dict() for _ in range(nv)]
    for i in range(nv):
        for j, ww in sorted(cand[i].items(), key=lambda kv: kv[1], reverse=True)[:K_NBR]:
            adj[i][j] = ww; adj[j][i] = ww
    n_edges = sum(len(d) for d in adj) // 2
    print(f"  IDF-weighted + top-{K_NBR} sparsified -> {n_edges} edges ({time.time()-t0:.1f}s)")

    leaves, calls = [], [0]

    def bisect(nodes, path):
        if len(nodes) <= MAXTOME:
            leaves.append((nodes, path)); return
        pos = {g: k for k, g in enumerate(nodes)}
        es, ws = [], []
        for g in nodes:
            for j, wt in adj[g].items():
                if j > g and j in pos:
                    es.append((pos[g], pos[j])); ws.append(wt)
        if not es:
            leaves.append((nodes, path)); return
        calls[0] += 1
        lft, rgt = L.normalized_cut_bisect(len(nodes), es, ws, max_iters=MAX_ITERS)
        if not lft or not rgt:
            leaves.append((nodes, path)); return
        bisect([nodes[k] for k in lft], path + "L")
        bisect([nodes[k] for k in rgt], path + "R")

    t1 = time.time()
    bisect(list(range(nv)), "")
    dt = time.time() - t1
    ram_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    tome_of = {}
    for t, (mem, _) in enumerate(leaves):
        for g in mem:
            tome_of[g] = t
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
        webout[t] = [[other, round(tot, 4), vocab[gi], vocab[gj]] for tot, other, gi, gj in lst[:3]]
    paths = [p for _, p in leaves]
    print(f"  native bisection -> {len(leaves)} tomes in {dt:.1f}s ({calls[0]} cuts), peak RAM {ram_mb:.0f} MB")
    print(f"  community within-fraction {win/max(1e-9,win+cross):.1%}; web pairs {len(web)}")

    OUT.write_text(json.dumps({
        "source": "fresh_windowed_cooccurrence", "srmech": srmech.__version__, "articles": ndoc,
        "window": WINDOW, "n_nodes": nv, "n_edges": n_edges, "maxtome": MAXTOME, "n_tomes": len(leaves),
        "tomes": [[vocab[g] for g in mem] for mem, _ in leaves], "paths": paths, "web": webout,
        "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/", "license": "CC-BY-SA-4.0",
                        "method": f"fresh windowed co-occurrence + native §51 (srmech {srmech.__version__})"}}))
    print(f"  persisted -> {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB)")

    idx = {w: i for i, w in enumerate(vocab)}
    print("\n  PROBE tomes (fresh source — compare coherence to the assoc tree):")
    for p in PROBES:
        g = idx.get(p)
        if g is None:
            print(f"    {p:9}: (not in band)"); continue
        t = tome_of[g]
        ride = [vocab[k] for k in leaves[t][0] if k != g][:9]
        hop = webout.get(t, [])
        hp = f"  WEB→{hop[0][2]}~{hop[0][3]}" if hop else ""
        print(f"    {p:9}: {{{', '.join(ride)}}}{hp}")


if __name__ == "__main__":
    main()
