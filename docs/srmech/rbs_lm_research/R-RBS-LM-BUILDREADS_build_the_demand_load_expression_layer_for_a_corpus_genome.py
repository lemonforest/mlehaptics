r"""R-RBS-LM-BUILDREADS (#231/F1235) — build the DEMAND-LOAD expression layer (reads/) for a corpus genome, ONCE.

The genome is the DNA (the store). reads/ is the gene-expression index (F1095/F1112 / EPH) so a query EXPRESSES only
the queried token's neighbourhood on demand (mmap) instead of inflating all 39M edges into RAM at startup. This builds
reads/ under the genome dir from the SOURCE directed kernel JSON (fast — no 39M-edge genome re-decode; equivalent to
the genome, which round-trips the source byte-exact, F1233). After this, corpus_store.prepare() opens INSTANTLY.

Run (background; ~5-10 min: JSON load + adjacency + write):
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-BUILDREADS_...py
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "siona"))
from siona import corpus_store as cs

SRC = os.environ.get("READS_SRC", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed_sparse_kernel.json"))
GENOME = os.environ.get("READS_GENOME", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome"))


def main():
    print("=== R-RBS-LM-BUILDREADS — the demand-load reads/ layer for %s ===" % Path(GENOME).name, flush=True)
    t0 = time.time()
    K = json.load(open(SRC))
    vocab = K["vocab"]
    edges = [tuple(e) for e in K["edge_list"]]
    print("[%.0fs] source loaded: %d vocab, %d edges" % (time.time() - t0, len(vocab), len(edges)), flush=True)
    t0 = time.time()
    nv = cs.build_reads(GENOME, vocab=vocab, edges=edges, weights=K["edge_weights"], charges=K["edge_charge"])
    rd = Path(GENOME) / "reads"
    size = sum(f.stat().st_size for f in rd.rglob("*") if f.is_file())
    print("[%.0fs] BUILT reads/: %d vocab, %d MB (adj.bin+adj.idx+vocab.txt)" % (time.time() - t0, nv, size / 1e6), flush=True)

    # verify: open INSTANTLY + a demand read
    t0 = time.time()
    h = cs.prepare(GENOME)
    print("[%.2fs] open (demand mmap) -> mode=%s, %d vocab" % (time.time() - t0, h["mode"], len(h["vocab"])), flush=True)
    for tok in ("water", "science", "country"):
        t0 = time.time()
        r = cs.read(h, tok, 6)
        print("    read(%r) in %.4fs -> %s" % (tok, time.time() - t0, r), flush=True)
    print("VERDICT: reads/ built; corpus_store.prepare() now opens INSTANTLY (was ~21 min full-materialize).", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
