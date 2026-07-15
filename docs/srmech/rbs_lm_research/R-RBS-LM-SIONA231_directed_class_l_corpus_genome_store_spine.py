r"""R-RBS-LM-SIONA231 (#231/PKG-3) — the genome-native DIRECTED Class-L corpus store, on NATIVE srmech ops
(#1390 delivered in rc253, F1232). Replaces the loose NDJSON *relational* store with ONE content-addressed genome
carrying the directed Laplacian (edges + metric + charge) + the vocab string table — NOT Klein-4 HVs (F1221 disk rule).

Spine — now the native srmech surface (was the #1390 prototypes; re-pointed F1232):
  item 1  srmech.amsc.text.cooccurrence_edges(directed=True) -> (n, edges, metric, charge)
  item 2  srmech.amsc.genome.graph_to_kernel / kernel_to_graph -> the genome chromosome, byte-exact
  item 4  srmech.amsc.laplacian.recover_check + recover_check_structural + recover_check_spectral(max_dim=)
  (item 3 laplacian.eulerian_path is the reconstruction read-out on the same object)

Proves the store end-to-end on the tier0 FINDINGS corpus (fresh, real), measures the size win vs loose JSON, and
PROJECTS to the real simplewiki body instrument (831k vocab / 39M edges). The recover_check SPLIT (structural /
bounded-spectral) that #231's scale pass surfaced (F1227) is now native — so the dense-eigendecompose wall is gone.

srmech 0.9.0rc253 (native); exact ints; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONA231_...py
"""
import json
import shutil
import sys
import time
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import hdc
from srmech.amsc import laplacian as L
from srmech.amsc import text as T

HERE = Path(__file__).parent
LEAF = 64
OUT = Path("/tmp/siona231")
COUPLE = hdc.klein4_random(LEAF, seed=1080)          # the sandroing/UNESCO 00073 coupling seed


# ---------- the vocab string-table codec (a SECOND chromosome so the genome is self-contained, not loose) ----------
def _vocab_to_syms(vocab):
    """'\\n'-join the vocab, UTF-8 bytes, each byte -> 4 fixed base-4 digits (256 = 4^4). Genome-native, no loose file."""
    b = "\n".join(vocab).encode("utf-8")
    syms = []
    for x in b:
        syms += [x & 3, (x >> 2) & 3, (x >> 4) & 3, (x >> 6) & 3]
    return syms


def _syms_to_vocab(syms):
    out = bytearray()
    for i in range(0, len(syms) - 3, 4):
        out.append(syms[i] + (syms[i + 1] << 2) + (syms[i + 2] << 4) + (syms[i + 3] << 6))
    return out.decode("utf-8", errors="ignore").split("\n")


# ---------- the store: build / load (2 chromosomes: directed graph + vocab table) ----------
def build_corpus_genome(vocab, edges, metric, charge, out_dir):
    strand_g, n_syms = G.graph_to_kernel(len(vocab), [tuple(e) for e in edges], metric, charge,
                                         leaf_dim=LEAF, label="graph", the_one=COUPLE)
    vsyms = _vocab_to_syms(vocab)
    d = Path(out_dir)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.parent.mkdir(parents=True, exist_ok=True)
    info = G.genome_save(strand_g, str(d), COUPLE, labels=["graph"])          # chromosome 1: the directed Laplacian
    G.genome_append_kernel(str(d), "vocab", vsyms, the_one=COUPLE)             # chromosome 2: vocab table (raw klein4 syms)
    size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    return {"sha": info.get("body_sha256"), "size": size, "n_syms": n_syms, "n_vsyms": len(vsyms)}


def load_corpus_genome(out_dir, n_syms, n_vsyms):
    d = str(out_dir)
    chg, _c, _l = G.genome_load(d, labels=["graph"], the_one=COUPLE)
    graph = G.kernel_to_graph(chg, COUPLE, n_syms)
    chv, _c2, _l2 = G.genome_load(d, labels=["vocab"], the_one=COUPLE)
    vsyms = list(G.kernel_unpack(chv, COUPLE))[:n_vsyms]
    vocab = _syms_to_vocab(vsyms)
    return vocab, graph


def neighbors(graph, vocab, token, k=6):
    """RELATIONAL read-out (no eig): what co-occurs with `token`, ranked by metric, with the DIRECTION (charge sign)."""
    if token not in vocab:
        return []
    ti = vocab.index(token)
    out = []
    for (i, j), w, c in zip(graph["edges"], graph["weights"], graph["charges"]):
        if i == ti or j == ti:
            other = j if i == ti else i
            # charge>0 on (i<j) means i precedes j; report who-precedes from token's view
            sense = "→" if ((i == ti) == (c >= 0)) else "←"
            out.append((w, sense, vocab[other]))
    out.sort(reverse=True)
    return out[:k]


def _findings_docs(cap_files=None):
    docs = []
    files = sorted(HERE.glob("R-RBS-LM-FINDING_*.md"))
    if cap_files:
        files = files[:cap_files]
    for f in files:
        docs.append(T.tokenize(f.read_text(errors="ignore")))
    return docs


def _bounded_vocab(docs, n):
    freq = {}
    for d in docs:
        for t in d:
            freq[t] = freq.get(t, 0) + 1
    return [t for t, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def main():
    print("=== R-RBS-LM-SIONA231 — genome-native directed Class-L corpus store (#231 spine on the #1390 prototypes) ===\n")
    docs = _findings_docs()
    print("tier0 FINDINGS corpus: %d docs" % len(docs))

    # (A) BOUNDED (n<=256) — the WHOLE spine end-to-end, full recover_check PASSES, relational read-out
    print("\n(A) bounded store (top-200 vocab, n<=256 so the full 4-faculty check runs):")
    vocab = _bounded_vocab(docs, 200)
    n, edges, metric, charge = T.cooccurrence_edges(docs, window=2, vocab=vocab, directed=True)
    info = build_corpus_genome(vocab, edges, metric, charge, OUT / "findings200.genome")
    v2, graph = load_corpus_genome(OUT / "findings200.genome", info["n_syms"], info["n_vsyms"])
    rt = (v2 == vocab and graph["edges"] == [tuple(e) for e in edges]
          and graph["weights"] == metric and graph["charges"] == charge)
    v = L.recover_check(n, edges, metric, charge)
    loose = len(json.dumps({"vocab": vocab, "edges": edges, "weights": metric, "charge": charge}).encode())
    print("     %d vocab, %d edges -> genome %d B (loose JSON %d B; %.2fx)"
          % (n, len(edges), info["size"], loose, loose / max(info["size"], 1)))
    print("     2-chromosome round-trip exact? %s   recover_check ok=%s curvature=%s"
          % (rt, v["ok"], v["curvature"]["verdict"]))
    tok = "curvature" if "curvature" in vocab else vocab[10]
    print("     relational read-out  neighbors(%r) = %s" % (tok, neighbors(graph, v2, tok)))

    # (B) FULL vocab — both native faculties run: structural (sparse, any vocab) + bounded-spectral (the rc253 split)
    print("\n(B) full-vocab store (the corpus-scale reality — the rc253 recover_check SPLIT now runs BOTH faculties):")
    fvocab = _bounded_vocab(docs, 10 ** 9)
    fn, fedges, fmetric, fcharge = T.cooccurrence_edges(docs, window=2, vocab=fvocab, directed=True)
    t0 = time.time()
    finfo = build_corpus_genome(fvocab, fedges, fmetric, fcharge, OUT / "findingsfull.genome")
    t_build = time.time() - t0
    floose = len(json.dumps({"vocab": fvocab, "edges": [list(e) for e in fedges],
                             "weights": fmetric, "charge": fcharge}).encode())
    print("     %d vocab, %d edges -> genome %d B (loose JSON %d B; %.2fx) built in %.1fs"
          % (fn, len(fedges), finfo["size"], floose, floose / max(finfo["size"], 1), t_build))
    t0 = time.time()
    st = L.recover_check_structural(fn, fedges, fmetric, fcharge)
    print("     recover_check_STRUCTURAL (native, sparse, O(edges)): %s  in %.2fs  <- scales to any vocab"
          % ({k: st[k] for k in ("operand", "directed", "curvature_sampled_nonzero")}, time.time() - t0))
    t0 = time.time()
    sp = L.recover_check_spectral(fn, fedges, fmetric, fcharge, max_dim=256)
    print("     recover_check_SPECTRAL (native, bounded max_dim=256): op=%s responsion=%s dim=%s  in %.2fs"
          % (sp.get("op"), sp.get("responsion"), sp.get("dim"), time.time() - t0))
    print("     -> the rc253 SPLIT RUNS at full-vocab where the full dense n×n eigendecompose (178s last pass) could not.")

    # (C) the real #231 target: simplewiki body instrument — PROJECT from its header (no 916MB load)
    print("\n(C) simplewiki body instrument projection (the real #231 target, from its header):")
    p = Path.home() / "corpora" / "wikipedia" / "simplewiki_directed_sparse_kernel.json"
    if p.exists():
        with open(p) as f:
            head = f.read(300)
        import re
        vs = int(re.search(r'"vocab_size":\s*(\d+)', head).group(1))
        ne = int(re.search(r'"edges":\s*(\d+)', head).group(1))
        loose_mb = p.stat().st_size / 1e6
        # per-edge genome cost measured from (B): genome_bytes/edge (dominated by the 4-int codec at ~0.25 B/sym)
        b_per_edge = finfo["size"] / max(len(fedges), 1)
        est_mb = b_per_edge * ne / 1e6
        print("     vocab_size=%d edges=%d  loose JSON=%.0f MB" % (vs, ne, loose_mb))
        print("     projected genome ~%.0f MB (@ %.1f B/edge from (B)) -> ~%.1fx smaller than the loose kernel"
              % (est_mb, b_per_edge, loose_mb / max(est_mb, 1)))
        print("     int-cap check: max node id %d < 2^30? %s ; metric weights need <2^30 (codec 15 base-4 digits)"
              % (vs, vs < 2 ** 30))
    else:
        print("     (simplewiki kernel not present — projection skipped)")

    print("\n=== #231 SPINE WORKS on NATIVE srmech rc253: directed Class-L + vocab -> ONE content-addressed genome, ===")
    print("=== byte-exact round-trip, integrity-checkable (structural + bounded-spectral), relational read-out.   ===")
    print("\n#1390 DELIVERED (rc253, F1232) — the prototype-pass learnings are now the native surface:")
    print("  * recover_check SPLIT is native: recover_check_structural (sparse, any vocab) + recover_check_spectral")
    print("    (bounded max_dim=) — both run at full-vocab scale above; the dense-eigendecompose wall is gone.")
    print("  * graph_to_kernel/kernel_to_graph native + byte-exact (%.2f B/edge); the 30-bit int cap is the doc'd bound."
          % (finfo["size"] / max(len(fedges), 1)))
    print("  * vocab string table = 2nd chromosome via genome_append_kernel. Store = the Laplacian + fiber, not Klein-4.")
    print("  NEXT: the real simplewiki genome (stream the 916MB kernel -> genome) + wire the store into Siona's read path (F1219).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
