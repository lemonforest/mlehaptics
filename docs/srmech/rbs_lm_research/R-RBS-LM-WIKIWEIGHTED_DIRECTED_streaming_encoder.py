r"""R-RBS-LM-WIKIWEIGHTED_DIRECTED (F1210) — the DIRECTED (curvature-carrying) streaming kernel encoder + self-validate.

The symmetric WIKIWEIGHTED encoder folds word ORDER away (`a,b=sorted((i,j))`, and one layer below the shipped
`text.cooccurrence_edges` symmetrizes to u<v) — so its kernel is a FLAT BAG with EXACTLY ZERO curvature (F1210 B0/B2).
This encoder keeps the direction: for each windowed pair it records which word came FIRST, as two count columns on the
same canonical (i<j) edge:
  • edge_weights = w_fwd + w_bwd   -> the METRIC / field read = EXACTLY today's symmetric weight (drop-in; nothing lost)
  • edge_charge  = w_fwd - w_bwd   -> the CURVATURE / responsion read = the magnetic-Laplacian per-edge charge
The stored object is a SUPERSET of the symmetric kernel (sum the columns → the old metric). It is the ONE directed
(magnetic) Laplacian per F1207: metric + curvature both read out; nothing truncated.

Interim per UPSTREAM_NOTES (the shipped `cooccurrence_edges` has no `directed=` flag): we count the directed
forward-window pairs ourselves over the SAME uncapped vocab + SAME per-article window as `build_edges_topk`, and
SELF-VALIDATE that w_fwd+w_bwd == the symmetric count EXACTLY (the metric-subset proof).

srmech 0.9.0rc238; numpy-free; no abs-builtin (Class-K magnitude); disciplined sha256_bytes. CC-BY-SA (attested-not-committed).
Env: WIKI_DUMP, OUT, MAX_ARTICLES (0=ALL; use a subset to VALIDATE first), WINDOW.
Run (validate on a subset): MAX_ARTICLES=30000 OUT=~/corpora/wikipedia/simplewiki_directed_validate.json \
     /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIWEIGHTED_DIRECTED_streaming_encoder.py
"""
import bz2
import importlib.util
import json
import os
import resource
import sys
import time
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

import srmech
from srmech.amsc import laplacian as L
from srmech.amsc.format import sha256_bytes
from srmech.amsc.cascade import magnitude          # Class-K real pin-slot magnitude (cascade-honest, not the builtin)

HERE = Path(__file__).parent
DUMP = Path(os.environ.get("WIKI_DUMP", str(Path.home() / "corpora" / "wikipedia" / "simplewiki-latest-pages-articles.xml.bz2")))
OUT = Path(os.environ.get("OUT", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed_sparse_kernel.json")))
WINDOW = int(os.environ.get("WINDOW", "4"))
_mx = os.environ.get("MAX_ARTICLES", "0")
MAX_ARTICLES = None if _mx in ("", "0", "none", "None") else int(_mx)

_spec = importlib.util.spec_from_file_location("wk", str(HERE / "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py"))
wk = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(wk)


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


class WikiDump:
    """Re-iterable streaming reader — one <text> = one article; RAM stays flat over the dump."""
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
                        print(f"    [pass {self._pass}] {self.count:,} streamed ({time.time()-t0:.0f}s, rss {rss_gb():.1f}GB)", flush=True)
                    if self.max_articles and self.count >= self.max_articles:
                        el.clear(); return
                el.clear()


def directed_pass(dump, window, idx):
    """One more stream over the SAME tokens (wk.stream_articles, per-article window reset, uncapped so every token is
    in vocab) — count DIRECTED forward-window pairs. fwd[(lo,hi)] = #(lo before hi); bwd = #(hi before lo)."""
    fwd, bwd = {}, {}
    for art in wk.stream_articles(dump):
        toks = [idx[w] for w in art]                      # uncapped vocab => every token maps (no OOV compaction)
        m = len(toks)
        for a in range(m):
            u = toks[a]
            hi_b = a + window + 1 if a + window + 1 < m else m
            for b in range(a + 1, hi_b):                  # distance 1..window (matches cooccurrence_edges radius)
                v = toks[b]
                if u == v:
                    continue
                if u < v:
                    fwd[(u, v)] = fwd.get((u, v), 0) + 1    # lo (=u) appeared BEFORE hi (=v)
                else:
                    bwd[(v, u)] = bwd.get((v, u), 0) + 1    # hi (=u) appeared BEFORE lo (=v)
    return fwd, bwd


def validate_metric_is_subset(edges, sym_w, fwd, bwd):
    """PROVE the metric read is a SUBSET (exact): w_fwd+w_bwd == the symmetric co-occurrence count, edge for edge."""
    bad = 0
    seen = set()
    for (a, b), w in zip(edges, sym_w):
        seen.add((a, b))
        if fwd.get((a, b), 0) + bwd.get((a, b), 0) != int(w):
            bad += 1
    orphan = sum(1 for e in fwd if e not in seen) + sum(1 for e in bwd if e not in seen)
    return bad, orphan


def curvature_recovers(vocab, edges, sym_w, fwd, bwd, freq, N=400):
    """Find a directed triangle among the top-N words; feed the exact-ℚ per-edge charge (f-b)/(f+b) to cycle_holonomy;
    a symmetric bag would give holonomy identically 0 — a nonzero one proves the curvature/responsion recovers."""
    order = sorted(range(len(vocab)), key=lambda i: (-freq[vocab[i]], vocab[i]))[:N]
    keep = set(order)
    adj = {}
    wof = {}
    for (a, b), w in zip(edges, sym_w):
        if a in keep and b in keep and int(w) >= 3:
            adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
            wof[(a, b)] = int(w)
    for u in adj:
        ns = [x for x in adj[u] if x > u]
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                v, w = ns[i], ns[j]
                if w in adj.get(v, ()):
                    tri = [(u, v), (min(v, w), max(v, w)), (min(u, w), max(u, w))]
                    ch = []
                    for (p, q) in tri:
                        f, r = fwd.get((p, q), 0), bwd.get((p, q), 0)
                        tot = f + r
                        ch.append(Fraction(f - r, tot) if tot else Fraction(0))
                    hol = L.cycle_holonomy([(0, 1), (1, 2), (2, 0)], charges=ch, n=3)
                    if not hol["balanced"]:                 # nonzero holonomy = genuine curvature recovered
                        return (vocab[u], vocab[v], vocab[w]), ch, hol
    return None, None, None


def recover_check(vocab, edges, weights, freq, N=256):
    """op/operand/responsion recover from the METRIC part (same check as the symmetric encoder)."""
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
    r = L.responsion(Lm, [1.0] + [0.0] * (N - 1), 5.0 / mx, kind="propagator")
    reach = sum(float(magnitude((z.real * z.real + z.imag * z.imag) ** 0.5)) for z in r[1:])
    return len(se), float(evals[1] if len(evals) > 1 else 0.0), reach


def persist(vocab, edges, sym_w, fwd, bwd, freq, n_articles):
    charge = [int(fwd.get((a, b), 0) - bwd.get((a, b), 0)) for (a, b) in edges]
    payload = {
        "wiki": OUT.stem.split("_")[0], "srmech": srmech.__version__, "uncapped": True,
        "directed": True, "format_version": 2, "window": WINDOW,
        "articles": n_articles, "vocab_size": len(vocab), "edges": len(edges),
        "vocab": vocab, "freq": [int(freq[w]) for w in vocab],
        "edge_list": [[int(a), int(b)] for a, b in edges],
        "edge_weights": [int(w) for w in sym_w],            # METRIC = w_fwd + w_bwd (drop-in; == symmetric kernel)
        "edge_charge": charge,                              # CURVATURE = w_fwd - w_bwd (signed net direction)
        "attestation": {
            "source_url": "https://dumps.wikimedia.org/simplewiki/latest/", "license": "CC-BY-SA-4.0",
            "response_sha256": sha256_bytes((" ".join(vocab)).encode()),
            "parser_version": f"srmech {srmech.__version__}",
            "note": "DIRECTED (curvature-carrying) sparse kernel (R-RBS-LM-WIKIWEIGHTED_DIRECTED / F1210). SUPERSET of the "
                    "symmetric kernel: metric=edge_weights=w_fwd+w_bwd (exact), curvature=edge_charge=w_fwd-w_bwd -> "
                    "magnetic_laplacian charge -> cycle_holonomy. Directed forward-window count (interim; UPSTREAM_NOTES "
                    "cooccurrence_edges directed= ask)."}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload))
    return OUT.stat().st_size


def main():
    print(f"=== R-RBS-LM-WIKIWEIGHTED_DIRECTED — directed kernel + self-validate (srmech {srmech.__version__}) ===")
    print(f"  dump={DUMP.name}  max_articles={MAX_ARTICLES or 'ALL'}  window={WINDOW}  out={OUT.name}\n")
    dump = WikiDump(DUMP, MAX_ARTICLES)
    t0 = time.time()
    vocab, idx, edges, sym_w, freq, dropped = wk.build_edges_topk(dump, window=WINDOW, vocab_cap=None)
    print(f"(1) symmetric reference (metric ground truth): {dump.count:,} articles -> {len(vocab):,} words, "
          f"{len(edges):,} edges ({time.time()-t0:.0f}s)")
    fwd, bwd = directed_pass(dump, WINDOW, idx)
    print(f"(2) directed pass: {len(fwd):,} fwd + {len(bwd):,} bwd directed edge-counts ({time.time()-t0:.0f}s)")

    bad, orphan = validate_metric_is_subset(edges, sym_w, fwd, bwd)
    print(f"(3) VALIDATE metric == subset: mismatched edges={bad}  orphan directed edges={orphan}  "
          f"-> {'PASS (w_fwd+w_bwd == symmetric count, exact)' if bad == 0 and orphan == 0 else 'FAIL'}")

    tri, ch, hol = curvature_recovers(vocab, edges, sym_w, fwd, bwd, freq)
    if tri:
        print(f"(4) VALIDATE curvature recovers: triangle {tri} charges={[str(c) for c in ch]} "
              f"-> cycle_holonomy={hol['holonomies']} balanced={hol['balanced']} -> PASS (nonzero holonomy)")
    else:
        print(f"(4) curvature check: no unbalanced triangle in top band (raise N or MAX_ARTICLES)")

    ne, fied, reach = recover_check(vocab, edges, sym_w, freq)
    print(f"(5) op/operand/responsion on the metric part: top-256 subgraph {ne} edges, L eigval[1]={fied:.4f}, "
          f"responsion reach={reach:.3f}")

    size = persist(vocab, edges, sym_w, fwd, bwd, freq, dump.count)
    print(f"(6) PERSISTED directed SSoT -> {OUT.name} ({size/1e6:.0f} MB)")
    ok = (bad == 0 and orphan == 0 and tri is not None)
    print(f"\nVERDICT: {'DIRECTED ENCODER VALIDATED' if ok else 'CHECK FAILED — see above'}. "
          f"metric=subset(exact)={'yes' if bad == 0 and orphan == 0 else 'NO'}, curvature-recovers={'yes' if tri else 'NO'}. "
          f"wall={time.time()-t0:.0f}s peakRSS={rss_gb():.1f}GB")


if __name__ == "__main__":
    main()
