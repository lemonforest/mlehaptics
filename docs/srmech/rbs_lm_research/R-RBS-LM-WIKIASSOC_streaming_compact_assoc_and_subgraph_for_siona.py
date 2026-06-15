r"""R-RBS-LM-WIKIASSOC (F754 infra) — the MEMORY-SAFE streaming builder that emits COMPACT artifacts so nothing
downstream has to json.loads the 112MB SSoT (which OOM'd the viewport, F750). One streaming encode -> two small files:

  (1) simplewiki_assoc.json — word -> top-K co-occurrence neighbours, for ALL vocab (UNCAPPED relational tier).
      This is "Siona knows the words" relationally (F748) + gives the input-ride (F753) room to FLIP: subject's
      neighbours re-ranked toward the relation/steer. Compact (145k×K), built with bounded per-word HEAPS (flat mem).
  (2) simplewiki_top{M}_kernel.json — the top-M-by-freq induced subgraph, for the dense-eig spectral tomes
      (the viewport experiment + the 14/16 bookshelf). Small (M≤400 — the numpy-free Jacobi eig is O(n^3), F754).

Reuses R-RBS-LM-WIKIKERNEL.build_edges_topk (F708 uncapped). Source = simplewiki_extracted/articles.jsonl.
Run (background, no timeout):  MAX_ARTICLES=15000 /tmp/srmech_rc149/venv/bin/python3 docs/.../R-RBS-LM-WIKIASSOC_...py
No abs(); no CAD; srmech 0.7.5rc149.
"""
import json
import os
import time
import heapq
import importlib.util as U
from pathlib import Path
import srmech
from srmech.amsc.format import sha256_raw

HERE = Path(__file__).parent
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUTDIR = Path.home() / "corpora" / "wikipedia"
N = int(os.environ.get("MAX_ARTICLES", "0"))      # 0 = ALL articles. The sparse tier has NO capacity cap (bounded-heap
#                                                   build, uncapped vocab F708); MAX_ARTICLES is a TEST dial, not a limit.
K = int(os.environ.get("ASSOC_K", "16"))          # neighbours kept per word
M = int(os.environ.get("SUBGRAPH_M", "400"))      # dense-eig subgraph size (eig-tractable)

_spec = U.spec_from_file_location("wk", str(HERE / "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py"))
wk = U.module_from_spec(_spec); _spec.loader.exec_module(wk)


def main():
    print(f"=== R-RBS-LM-WIKIASSOC — streaming compact build (N={N or 'ALL'} articles, K={K}, M={M}; srmech {srmech.__version__}) ===")
    texts = []
    with open(ART) as f:
        for i, line in enumerate(f):
            if N and i >= N:                       # N==0 -> read the WHOLE corpus
                break
            try:
                texts.append(json.loads(line).get("text", ""))
            except ValueError:
                continue
    t0 = time.time()
    vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(texts, window=4, vocab_cap=None)   # UNCAPPED
    print(f"  encoded {len(texts)} articles -> {len(vocab)} vocab, {len(edges)} edges ({time.time()-t0:.1f}s)")

    # (1) top-K association table — bounded per-word min-heaps (flat memory: 145k×K, never the full edge list again)
    heaps = {}
    for (a, b), wt in zip(edges, weights):
        for i, j in ((a, b), (b, a)):
            h = heaps.get(i)
            if h is None:
                heaps[i] = [(wt, j)]
            elif len(h) < K:
                heapq.heappush(h, (wt, j))
            elif wt > h[0][0]:
                heapq.heapreplace(h, (wt, j))
    assoc = {vocab[i]: [vocab[j] for _w, j in sorted(heaps.get(i, []), reverse=True)] for i in range(len(vocab))}
    assoc_path = OUTDIR / "simplewiki_assoc.json"
    assoc_path.write_text(json.dumps({"wiki": "simplewiki", "articles": len(texts), "vocab_size": len(vocab),
                                      "K": K, "freq": {vocab[i]: int(freq[vocab[i]]) for i in range(len(vocab))},
                                      "assoc": assoc,
                                      "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/",
                                                      "license": "CC-BY-SA-4.0",
                                                      "response_sha256": sha256_raw(",".join(vocab).encode()).hex(),
                                                      "parser_version": f"srmech {srmech.__version__}"}}))
    print(f"  wrote {assoc_path.name} ({assoc_path.stat().st_size/1e6:.1f} MB) — UNCAPPED top-{K} assoc for {len(vocab)} words")

    # (2) top-M induced subgraph for the dense-eig spectral tomes
    order = sorted(range(len(vocab)), key=lambda i: (-freq[vocab[i]], vocab[i]))[:M]
    keep = {oi: ni for ni, oi in enumerate(order)}
    se, sw = [], []
    for (a, b), wt in zip(edges, weights):
        if a in keep and b in keep:
            se.append([keep[a], keep[b]]); sw.append(wt)
    sub_path = OUTDIR / f"simplewiki_top{M}_kernel.json"
    sub_path.write_text(json.dumps({"vocab": [vocab[oi] for oi in order], "edge_list": se, "edge_weights": sw,
                                    "freq": [int(freq[vocab[oi]]) for oi in order]}))
    print(f"  wrote {sub_path.name} ({sub_path.stat().st_size/1e6:.1f} MB) — top-{M} subgraph, {len(se)} edges (eig-ready)")

    # spot-check the assoc tier (does the input-ride have room? are real relations present?)
    print("\n  assoc spot-check (the relational tier the input-ride steers over):")
    for w in ("kombucha", "bread", "dragon", "tea", "computer"):
        print(f"    {w:9}: {', '.join(assoc.get(w, [])[:8]) if w in assoc else '(not in vocab)'}")


if __name__ == "__main__":
    main()
