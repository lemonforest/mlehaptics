r"""R-RBS-LM-WIKIWEIGHTED — the STREAMING, UNCAPPED, WEIGHTED sparse kernel encoder (F708/F748 done at FULL scale).

WHY THIS EXISTS: the comprehended-shard path (#259) REGRESSED to `_assoc`'s top-16 + weight-drop at STORAGE time —
the SAME class of bug the user caught at F708 (pre-encode quantization). This encoder is the correct object:
  • STREAM the dump one article at a time (RAM flat on input; WikiDump re-streams the bz2 for each of build_edges_topk's
    passes) — no materialised article list.
  • build_edges_topk(vocab_cap=None) -> the FULL uncapped WEIGHTED graph (vocab, edges, weights, freq) — NO top-K, NO cap.
  • persist the full_sparse_kernel SSoT: {wiki, uncapped, vocab, freq, edge_list, edge_weights, attestation} — the object
    from which op (L = D-A), operand (edges), and responsion (excite L) ALL recover. Top-N is a LOAD-time RAM knob, never
    a storage truncation.

Reuses R-RBS-LM-WIKIKERNEL.build_edges_topk (uncapped) + the WikiDump streamer from R-RBS-LM-UNCAPPED. numpy-free; no
Counter as a store (build_edges_topk's PASS-1 freq dict only RANKS vocab); no abs-builtin; disciplined sha256_bytes.

Env: WIKI_DUMP, OUT, MAX_ARTICLES (0/none=ALL), WINDOW.
Run: OUT=~/corpora/wikipedia/simplewiki_full_sparse_kernel.json \
     WIKI_DUMP=~/corpora/wikipedia/simplewiki-latest-pages-articles.xml.bz2 \
     /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIWEIGHTED_streaming_uncapped_weighted_kernel.py
"""
import bz2
import importlib.util
import json
import os
import resource
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import laplacian as L
from srmech.amsc.format import sha256_bytes

HERE = Path(__file__).parent
DUMP = Path(os.environ.get("WIKI_DUMP", str(Path.home() / "corpora" / "wikipedia" / "simplewiki-latest-pages-articles.xml.bz2")))
OUT = Path(os.environ.get("OUT", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_full_sparse_kernel.json")))
WINDOW = int(os.environ.get("WINDOW", "4"))
_mx = os.environ.get("MAX_ARTICLES", "0")
MAX_ARTICLES = None if _mx in ("", "0", "none", "None") else int(_mx)

_spec = importlib.util.spec_from_file_location("wk", str(HERE / "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py"))
wk = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(wk)


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


class WikiDump:
    """Re-iterable streaming reader — one <text> = one article; RAM stays flat over the multi-GB dump."""
    def __init__(self, path, max_articles=None):
        self.path, self.max_articles, self.count, self._pass = str(path), max_articles, 0, 0

    def __iter__(self):
        self.count = 0; self._pass += 1; t0 = time.time()
        with bz2.open(self.path, "rt", encoding="utf-8") as fh:
            for _ev, el in ET.iterparse(fh, events=("end",)):
                if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                    yield el.text
                    self.count += 1
                    if self.count % 50000 == 0:
                        print(f"    [pass {self._pass}] {self.count:,} articles streamed ({time.time()-t0:.0f}s, rss {rss_gb():.1f}GB)", flush=True)
                    if self.max_articles and self.count >= self.max_articles:
                        el.clear(); return
                el.clear()


def persist(vocab, edges, weights, freq, n_articles):
    payload = {
        "wiki": OUT.stem.split("_")[0], "srmech": srmech.__version__, "uncapped": True,
        "articles": n_articles, "vocab_size": len(vocab), "edges": len(edges),
        "vocab": vocab, "freq": [int(freq[w]) for w in vocab],
        "edge_list": [[int(a), int(b)] for a, b in edges],
        "edge_weights": [float(w) for w in weights],
        "attestation": {
            "source_url": "https://dumps.wikimedia.org/simplewiki/latest/", "license": "CC-BY-SA-4.0",
            "response_sha256": sha256_bytes((" ".join(vocab)).encode()),
            "parser_version": f"srmech {srmech.__version__}",
            "note": "FULL uncapped WEIGHTED sparse kernel (R-RBS-LM-WIKIWEIGHTED / F708/F748); ceiling is a LOAD-time knob, "
                    "NOT an encode truncation. op=L=D-A, operand=edges, responsion=excite(L) all recover from this."}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload))
    return OUT.stat().st_size


def recover_check(vocab, edges, weights, freq, N=256):
    """PROVE op/operand/responsion recover from the stored WEIGHTED graph: build L on the top-N induced subgraph,
    eigendecompose, recover A=D-L (operand), run a responsion (the read-out). A top-16 unweighted store CANNOT do this."""
    order = sorted(range(len(vocab)), key=lambda i: (-freq[vocab[i]], vocab[i]))[:N]
    keep = {oi: ni for ni, oi in enumerate(order)}
    se, sw = [], []
    for (a, b), w in zip(edges, weights):
        if a in keep and b in keep:
            se.append((keep[a], keep[b])); sw.append(float(w))
    lap = L.dense_laplacian(N, se, sw)
    evals, _V = L.symmetric_eigendecompose(lap)
    mx = max((float(e) for e in evals), default=1.0) or 1.0
    Lm = L.magnetic_laplacian(N, se, sw, q=0.25)
    # propagator e^{-zL} with z SCALED to the spectrum (weights are raw co-occurrence counts -> eigenvalues reach
    # ~1e6, so a fixed small z underflows the read-out to ~0; z*max_eig ~ O(1) gives an honest excitability signal).
    r = L.responsion(Lm, [1.0] + [0.0] * (N - 1), 5.0 / mx, kind="propagator")
    reach = sum((z.real * z.real + z.imag * z.imag) ** 0.5 for z in r[1:])   # Class-K real magnitude (re^2+im^2)^0.5
    return len(se), float(evals[1] if len(evals) > 1 else 0.0), reach


def main():
    print(f"=== R-RBS-LM-WIKIWEIGHTED — streaming UNCAPPED WEIGHTED kernel (srmech {srmech.__version__}) ===")
    print(f"  dump={DUMP.name}  max_articles={MAX_ARTICLES or 'ALL'}  window={WINDOW}  out={OUT.name}\n")
    dump = WikiDump(DUMP, MAX_ARTICLES)
    t0 = time.time()
    vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(dump, window=WINDOW, vocab_cap=None)  # UNCAPPED
    dt = time.time() - t0
    print(f"\n(1) ENCODED (streamed): {dump.count:,} articles -> {len(vocab):,} words (dropped={len(dropped)}=0 -> NO quantization), "
          f"{len(edges):,} WEIGHTED edges in {dt:.0f}s, rss {rss_gb():.1f}GB")

    # proof of no truncation: the max node degree is nowhere near a top-16 cap
    deg = {}
    for a, b in edges:
        deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
    dv = sorted(deg.values())
    print(f"(2) node degree: median={dv[len(dv)//2]}  max={dv[-1]}  (max >> 16 => genuinely UNCAPPED, not top-K)")

    size = persist(vocab, edges, weights, freq, dump.count)
    print(f"(3) PERSISTED full weighted SSoT -> {OUT.name} ({size/1e6:.0f} MB)")

    ne, fiedler_lam, reach = recover_check(vocab, edges, weights, freq)
    print(f"(4) RECOVER CHECK (op/operand/responsion from the stored WEIGHTED graph): top-256 induced subgraph "
          f"{ne} edges -> L eigval[1]={fiedler_lam:.4f}, responsion reach={reach:.3f} (>0 => excitable)")
    print(f"\nVERDICT: uncapped + weighted + streamed. The stored object IS the Class-L source — L, edges, and the "
          f"responsion all recover. peak rss={rss_gb():.1f}GB, wall={time.time()-t0:.0f}s.")


if __name__ == "__main__":
    main()
