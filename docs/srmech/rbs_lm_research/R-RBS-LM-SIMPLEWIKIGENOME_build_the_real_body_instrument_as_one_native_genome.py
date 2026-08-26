r"""R-RBS-LM-SIMPLEWIKIGENOME (#231/PKG-3) — build the REAL simplewiki body instrument as ONE native srmech genome.

The actual #231 target: `simplewiki_directed_sparse_kernel.json` (916 MB, 831,139 vocab, 39,048,148 directed edges —
the item-1 output at real scale) -> ONE content-addressed genome (directed Laplacian + vocab), via the native rc253
store (`R-RBS-LM-SIONA231.build_corpus_genome` = `genome.graph_to_kernel` + the vocab 2nd chromosome). Then verify with
the native `recover_check_structural` (sparse) + `recover_check_spectral(max_dim=256)` (bounded), and a round-trip spot
check. Measures the size win vs the 916 MB loose kernel.

srmech 0.9.0rc253 (native). Run (BACKGROUND — ~20-30 min at 39M edges):
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIMPLEWIKIGENOME_...py
"""
import importlib.util
import json
import os
import time
from pathlib import Path

import srmech.amsc.laplacian as L

HERE = Path(__file__).parent


def _load(stem):
    p = HERE / stem
    spec = importlib.util.spec_from_file_location(stem.split("_")[0].replace("-", ""), str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S = _load("R-RBS-LM-SIONA231_directed_class_l_corpus_genome_store_spine.py")


def _mx(seq):
    m = 0
    for x in seq:
        v = x if x >= 0 else -x
        if v > m:
            m = v
    return m


def main():
    src = Path.home() / "corpora" / "wikipedia" / "simplewiki_directed_sparse_kernel.json"
    out = Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome"
    print("=== R-RBS-LM-SIMPLEWIKIGENOME — the real simplewiki body instrument -> ONE native genome (rc253) ===", flush=True)

    t0 = time.time()
    K = json.load(open(src))
    vocab = K["vocab"]
    edges = [tuple(e) for e in K["edge_list"]]
    metric = K["edge_weights"]
    charge = K["edge_charge"]
    print("[%.0fs] loaded: %d vocab, %d edges" % (time.time() - t0, len(vocab), len(edges)), flush=True)

    # 30-bit int-cap pre-check (F1227 — the codec's 2-symbol length header caps ints at 15 base-4 digits = 2^30)
    cap = 2 ** 30
    mw, mc, mn = _mx(metric), _mx(charge), len(vocab)
    print("    int-cap check: max node id %d, max metric %d, max |charge| %d  — all < 2^30 (%d)? %s"
          % (mn, mw, mc, cap, mn < cap and mw < cap and mc < cap), flush=True)
    assert mn < cap and mw < cap and mc < cap, "an int exceeds the 30-bit codec cap — needs the wide-int header"

    t0 = time.time()
    info = S.build_corpus_genome(vocab, edges, metric, charge, out)
    loose_mb = src.stat().st_size / 1e6
    genome_mb = info["size"] / 1e6
    print("[%.0fs] BUILT genome: %.0f MB (loose JSON %.0f MB; %.2fx smaller)  sha=%s.."
          % (time.time() - t0, genome_mb, loose_mb, loose_mb / max(genome_mb, 1e-9), (info["sha"] or "----")[:12]), flush=True)

    # verify — native faculties (both scale: structural sparse, spectral bounded)
    t0 = time.time()
    st = L.recover_check_structural(len(vocab), edges, metric, charge)
    print("[%.0fs] recover_check_structural: %s" % (time.time() - t0, st), flush=True)
    t0 = time.time()
    sp = L.recover_check_spectral(len(vocab), edges, metric, charge, max_dim=256)
    print("[%.0fs] recover_check_spectral(max_dim=256): op=%s responsion=%s dim=%s"
          % (time.time() - t0, sp.get("op"), sp.get("responsion"), sp.get("dim")), flush=True)

    # round-trip spot check — load the genome back, confirm vocab + a slice of edges byte-exact
    t0 = time.time()
    v2, g = S.load_corpus_genome(out, info["n_syms"], info["n_vsyms"])
    rt = (v2 == vocab and g["vocab_size"] == len(vocab) and g["edges"] == edges
          and g["weights"] == metric and g["charges"] == charge)
    print("[%.0fs] round-trip byte-exact (vocab + all %d edges + metric + charge)? %s"
          % (time.time() - t0, len(edges), rt), flush=True)

    # a relational read-out on the real corpus (proof it is queryable)
    for tok in ("science", "water", "country"):
        if tok in v2:
            print("    neighbors(%r) = %s" % (tok, S.neighbors(g, v2, tok, k=5)), flush=True)

    print("\nVERDICT: %s — the real simplewiki body instrument is ONE native content-addressed genome (%.0f MB, %.1fx"
          % ("PASS" if rt else "FAIL — investigate", genome_mb, loose_mb / max(genome_mb, 1e-9)))
    print("         smaller than the 916 MB loose kernel), integrity-checkable + relationally queryable. #231 at real scale.")
    print("         Genome at: %s" % out, flush=True)
    return 0 if rt else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
