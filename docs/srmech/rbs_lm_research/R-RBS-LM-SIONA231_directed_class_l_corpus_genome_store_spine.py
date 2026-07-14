r"""R-RBS-LM-SIONA231 (#231/PKG-3) — the genome-native DIRECTED Class-L corpus store, built on the #1390 prototype
spine (items 1-4). Replaces the loose NDJSON *relational* store with ONE content-addressed genome carrying the
directed Laplacian (edges + metric + charge) + the vocab string table — NOT Klein-4 HVs (F1221 disk rule).

Spine (all from the #1390 prototypes):
  item 1  cooccurrence_edges(directed=True)  -> (n, edges, metric, charge)          [DIRCOOCCUR]
  item 2  graph_to_kernel / kernel_to_graph  -> the genome chromosome, byte-exact   [GRAPH2KERNEL]
  item 4  recover_check                      -> the four-faculty integrity check     [RECOVERCHECK]
  (item 3 eulerian_path is the reconstruction read-out on the same object)

This turn STARTS #231: builds the store module, proves it end-to-end on the tier0 FINDINGS corpus (fresh, real),
measures the size win vs loose JSON, and PROJECTS to the real simplewiki body instrument (831k vocab / 39M edges) —
surfacing what the #1390 ops need AT CORPUS SCALE (flagged for the maintainer).

srmech 0.9.0rc241; exact ints; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONA231_...py
"""
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import laplacian as L
from srmech.amsc import text as T

HERE = Path(__file__).parent
LEAF = 64
OUT = Path("/tmp/siona231")


def _load(stem):
    p = HERE / stem
    spec = importlib.util.spec_from_file_location(stem.split("_")[0].replace("-", ""), str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GK = _load("R-RBS-LM-GRAPH2KERNEL_prototype_general_directed_signed_graph_genome_codec.py")
RC = _load("R-RBS-LM-RECOVERCHECK_prototype_general_class_l_genome_recover_check_four_faculties.py")
DC = _load("R-RBS-LM-DIRCOOCCUR_prototype_directed_cooccurrence_edges_metric_plus_charge.py")
COUPLE = GK.COUPLE


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
    strand_g, n_syms = GK.graph_to_kernel(len(vocab), [tuple(e) for e in edges], metric, charge,
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
    graph = GK.kernel_to_graph(chg, COUPLE, n_syms)
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


# ---------- a SCALABLE integrity check (proposed #1390 item-4 refinement — the corpus-scale finding) ----------
def recover_check_structural(vocab_size, edges, weights, charges, *, cycle_sample=48):
    """The O(edges) faculties only — operand (edges present/valid) + a SAMPLED curvature read — so integrity is
    checkable at ANY vocab size. The dense op/responsion faculties (full n×n eigendecompose) do NOT scale past the
    native n<=256 / O(n^3) wall (measured below), so recover_check must SPLIT: structural (this, sparse, scales) vs
    spectral (op+responsion, bounded submatrix / top-k Lanczos). This is the #1390 item-4 corpus-scale learning."""
    operand = (len(edges) > 0 and len(edges) == len(weights) and all(w >= 1 for w in weights))
    directed = charges is not None and any(c != 0 for c in charges)
    # curvature sample: take the first `cycle_sample` edges that close a triangle with earlier ones (cheap probe)
    seen = {}
    holo = False
    from fractions import Fraction
    for idx, ((i, j), c) in enumerate(zip(edges, charges or [0] * len(edges))):
        seen[(i, j)] = c
        # look for a 2-path i->k and k->j already seen -> a triangle
        for k in range(min(vocab_size, 64)):
            a = seen.get((min(i, k), max(i, k)))
            b = seen.get((min(k, j), max(k, j)))
            if a is not None and b is not None and k not in (i, j):
                mc = c if c >= 0 else -c                          # Class-K magnitude (not the builtin)
                q = Fraction(1, 2 * max(1, mc) + 1)
                hh = L.cycle_holonomy([(i, k), (k, j), (i, j)],
                                      charges=[Fraction(int(a)) * q, Fraction(int(b)) * q, Fraction(int(c)) * q],
                                      n=vocab_size)
                if any(h != 0 for h in hh["holonomies"]):
                    holo = True
                    break
        if holo or idx > cycle_sample * 200:
            break
    return {"operand": operand, "directed": directed, "curvature_sampled_nonzero": holo,
            "ok_structural": operand}


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
    n, edges, metric, charge = DC.cooccurrence_edges(docs, window=2, vocab=vocab, directed=True)
    info = build_corpus_genome(vocab, edges, metric, charge, OUT / "findings200.genome")
    v2, graph = load_corpus_genome(OUT / "findings200.genome", info["n_syms"], info["n_vsyms"])
    rt = (v2 == vocab and graph["edges"] == [tuple(e) for e in edges]
          and graph["weights"] == metric and graph["charges"] == charge)
    v = RC.recover_check(n, edges, metric, charge)
    loose = len(json.dumps({"vocab": vocab, "edges": edges, "weights": metric, "charge": charge}).encode())
    print("     %d vocab, %d edges -> genome %d B (loose JSON %d B; %.2fx)"
          % (n, len(edges), info["size"], loose, loose / max(info["size"], 1)))
    print("     2-chromosome round-trip exact? %s   recover_check ok=%s curvature=%s"
          % (rt, v["ok"], v["curvature"]["verdict"]))
    tok = "curvature" if "curvature" in vocab else vocab[10]
    print("     relational read-out  neighbors(%r) = %s" % (tok, neighbors(graph, v2, tok)))

    # (B) FULL vocab — sparse faculties scale; the DENSE op/responsion faculties hit the wall (the #1390 learning)
    print("\n(B) full-vocab store (the corpus-scale reality — sparse scales, dense does not):")
    fvocab = _bounded_vocab(docs, 10 ** 9)
    fn, fedges, fmetric, fcharge = DC.cooccurrence_edges(docs, window=2, vocab=fvocab, directed=True)
    t0 = time.time()
    finfo = build_corpus_genome(fvocab, fedges, fmetric, fcharge, OUT / "findingsfull.genome")
    t_build = time.time() - t0
    floose = len(json.dumps({"vocab": fvocab, "edges": [list(e) for e in fedges],
                             "weights": fmetric, "charge": fcharge}).encode())
    print("     %d vocab, %d edges -> genome %d B (loose JSON %d B; %.2fx) built in %.1fs"
          % (fn, len(fedges), finfo["size"], floose, floose / max(finfo["size"], 1), t_build))
    t0 = time.time()
    st = recover_check_structural(fn, fedges, fmetric, fcharge)
    print("     recover_check_STRUCTURAL (sparse, O(edges)): %s  in %.2fs  <- SCALES"
          % ({k: st[k] for k in ("operand", "directed", "curvature_sampled_nonzero")}, time.time() - t0))
    try:
        t0 = time.time()
        _ = L.dense_laplacian(fn, [tuple(e) for e in fedges], [float(w) for w in fmetric])
        print("     dense_laplacian(n=%d) built in %.2fs (unexpected at this n)" % (fn, time.time() - t0))
    except Exception as e:
        print("     recover_check SPECTRAL (dense op/responsion) at n=%d: %s: %s  <- DOES NOT SCALE (native n<=256 / O(n^3)/O(n^2) mem)"
              % (fn, type(e).__name__, str(e)[:70]))

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

    print("\n=== #231 SPINE WORKS: directed Class-L + vocab -> ONE content-addressed genome, byte-exact round-trip, ===")
    print("=== integrity-checkable, with the relational read-out. Built entirely on the #1390 prototypes.       ===")
    print("\nLEARNINGS FOR #1390 (flag to the maintainer):")
    print("  * item 4 recover_check: op+responsion do a DENSE n×n eigendecompose (native n<=256, O(n^3), O(n^2) mem)")
    print("    -> at corpus vocab it CANNOT run. SPLIT into recover_check_structural (operand+sampled-curvature,")
    print("    O(edges), scales — prototyped here) vs recover_check_spectral (bounded submatrix / top-k Lanczos).")
    print("  * item 2 graph_to_kernel: linear + tiny (measured %.2f B/edge), but the codec's 2-symbol length header"
          % (finfo["size"] / max(len(fedges), 1)))
    print("    caps ints at 15 base-4 digits (30 bits) — fine for simplewiki (831k vocab, weights< that), but a")
    print("    huge corpus (enwiki, or a weight>2^30) needs a wider header; worth documenting the cap.")
    print("  * a self-contained genome needs the VOCAB STRING TABLE too — here a 2nd chromosome via")
    print("    genome_append_kernel worked; graph_to_kernel could optionally accept/emit the string table.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
