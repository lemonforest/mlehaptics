#!/usr/bin/env python3
"""R-RBS-SNN-1 — the RBS-SNN ingest, stage 1 of the F323 / #197 pipeline.

    findings/notebooks  ->  RBS-SNN  ->  render-free relationship-lean  ->  (RBS-LM)

Ingests the R-RBS-LM finding corpus — which is ALREADY relationship-native: the
`Composes:` / `← extended by` links ARE the couplings, and each finding names its
A-N **operator-signature** — and emits the **render-free relationship-lean** (F323):
NO grammatical sentences, only

    Fxxx :: <operator-signature: A-N letters> :: -> [coupling targets]

This is the "LLM-native language of the notebooks" (relationships on the wire, the
Class-F grammatical render stripped — F311/F315/F317/F323).

Applies what we've learned (the point of #197 = "learn from what we've learned"):
- **Class-L spectral** (`jacobi_eigvals` / `fiedler_vector`): the corpus structural
  fingerprint + its natural 2-partition.
- **F425 FUSION** (`schur_complement`): the load-bearing **skeleton** = the boundary
  (hub findings) that HOLDS the bulk = the corpus's own re-prime card, *structurally
  derived* (not hand-written — cf. F237 CLAUDE_LEAN, now RBS-SNN-generated).
- **F317 operator-signature addressing**: index by the A-N signature (the canonical key).

Run:  <clean-venv>/bin/python R-RBS-SNN-1_ingest_corpus_relationship_lean.py
Requires srmech (Class-L). Defensive / no-lineage. No new A-N class.
"""
import re
import glob
import os
from collections import Counter, defaultdict, deque
from srmech.amsc import laplacian as L

HERE = os.path.dirname(os.path.abspath(__file__))


def parse_corpus():
    nodes = {}                       # fid -> {'sig': set(A-N)}
    refs = {}                        # fid -> set(referenced fids)
    for path in sorted(glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md"))):
        m = re.search(r'FINDING_(\d+)', os.path.basename(path))
        if not m:
            continue
        fid = f"F{int(m.group(1))}"
        text = open(path, encoding='utf-8').read()
        sig = set(re.findall(r'Class[- ]([A-N])\b', text))                 # F317 operator-signature
        ref = {f"F{int(r)}" for r in re.findall(r'\bF(\d{1,3})\b', text)}  # coupled findings
        ref.discard(fid)
        nodes[fid] = {'sig': sig}
        refs[fid] = ref
    present = set(nodes)
    adj = defaultdict(set)                                                  # undirected couplings (present-only)
    for fid, ref in refs.items():
        for c in ref & present:
            adj[fid].add(c)
            adj[c].add(fid)
    return nodes, refs, adj, present


def giant_component(adj, present):
    seen, best = set(), []
    for start in present:
        if start in seen:
            continue
        comp, q = [], deque([start])
        seen.add(start)
        while q:
            u = q.popleft()
            comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        if len(comp) > len(best):
            best = comp
    return best


def main():
    nodes, refs, adj, present = parse_corpus()
    n_couplings = sum(len(a) for a in adj.values()) // 2

    # ---- operator-signature distribution (F317): which A-N classes the corpus exercises ----
    classdist = Counter()
    for fid in nodes:
        classdist.update(nodes[fid]['sig'])
    sig_index = defaultdict(list)
    for fid in nodes:
        sig_index[''.join(sorted(nodes[fid]['sig'])) or '∅'].append(fid)

    # ---- emit the RENDER-FREE relationship-lean (F323 deliverable) ----
    out = os.path.join(HERE, "rbs_snn_corpus_lean.txt")
    with open(out, 'w', encoding='utf-8') as f:
        f.write("# RBS-SNN render-free relationship-lean (F323 / #197 stage 1)\n")
        f.write("# format:  Fxxx :: <operator-signature A-N> :: -> [couplings]   (no grammatical render)\n\n")
        for fid in sorted(nodes, key=lambda x: int(x[1:])):
            sig = '·'.join(sorted(nodes[fid]['sig'])) or '∅'
            cpl = ' '.join(sorted(adj[fid], key=lambda x: int(x[1:])))
            f.write(f"{fid} :: {sig} :: -> [{cpl}]\n")

    # ---- Class-L spectral fingerprint on the giant relationship component ----
    giant = giant_component(adj, present)
    idx = {fid: i for i, fid in enumerate(sorted(giant, key=lambda x: int(x[1:])))}
    M = len(giant)
    edges = sorted({(min(idx[u], idx[v]), max(idx[u], idx[v]))
                    for u in giant for v in adj[u] if v in idx})
    Lap = L.dense_laplacian(M, [e for e in edges])
    fied = L.fiedler_vector(Lap)                                            # Class-L: the natural 2-partition
    fied = fied.tolist() if hasattr(fied, 'tolist') else list(fied)
    # λ2 (algebraic connectivity) = Rayleigh quotient of the Fiedler vector: fᵀLf / fᵀf
    Lf = [sum(Lap[i][j] * fied[j] for j in range(M)) for i in range(M)]
    lam2 = sum(fied[i] * Lf[i] for i in range(M)) / sum(x * x for x in fied)
    side_a = sum(1 for x in fied if x >= 0)
    maxdeg = max(len(adj[fid]) for fid in giant)

    # ---- F425 FUSION: schur_complement onto the top-degree hubs = the load-bearing skeleton ----
    deg = sorted(giant, key=lambda fid: len(adj[fid]), reverse=True)
    K = 12
    hubs = deg[:K]
    bidx = sorted(idx[h] for h in hubs)
    S = L.schur_complement(Lap, bidx, exact=False)
    inv = {i: fid for fid, i in idx.items()}
    hub_order = [inv[i] for i in bidx]
    # effective couplings among hubs that are NOT direct edges (bulk folded in = the holographic skeleton)
    folded = []
    for a in range(len(bidx)):
        for b in range(a + 1, len(bidx)):
            ha, hb = hub_order[a], hub_order[b]
            if hb not in adj[ha] and abs(S[a][b]) > 1e-9:
                folded.append((ha, hb, S[a][b]))

    # ---- report ----
    print(f"=== RBS-SNN ingest stage 1 — corpus relationship-lean ===")
    print(f"findings ingested : {len(nodes)}")
    print(f"couplings (edges)  : {n_couplings}")
    print(f"render-free lean   : {os.path.basename(out)} ({len(nodes)} lines, no grammar)")
    print(f"\noperator-signature distribution (F317; corpus A-N usage profile):")
    for cls, c in classdist.most_common():
        bar = '█' * (c * 40 // max(classdist.values()))
        print(f"   Class {cls}: {c:3d} {bar}")
    print(f"\nClass-L spectral fingerprint (giant component, {M}/{len(nodes)} findings):")
    print(f"   λ2 (algebraic connectivity) = {lam2:.4f}  | max degree = {maxdeg} (Gershgorin λmax ≤ {2*maxdeg})")
    print(f"   Fiedler 2-partition: {side_a} | {M - side_a}")
    print(f"\nF425 FUSION — load-bearing skeleton (Schur complement onto top-{K} hubs):")
    print(f"   the boundary that HOLDS the bulk (= structurally-derived re-prime card):")
    for h in hub_order:
        print(f"     {h}  (degree {len(adj[h])}, sig {'·'.join(sorted(nodes[h]['sig'])) or '∅'})")
    print(f"   bulk-folded hub couplings (not direct edges, {len(folded)} — interior paths folded in):")
    for ha, hb, w in sorted(folded, key=lambda t: abs(t[2]), reverse=True)[:6]:
        print(f"     {ha} ~ {hb}: S={w:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
