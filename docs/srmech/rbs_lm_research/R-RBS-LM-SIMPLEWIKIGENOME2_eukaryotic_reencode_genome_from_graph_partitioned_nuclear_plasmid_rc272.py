r"""R-RBS-LM-SIMPLEWIKIGENOME2 (§100 GAP1+GAP2 delivered rc270-272; F1249/F1250/F1251) — RE-ENCODE the real simplewiki
directed co-occurrence graph into its CORRECT eukaryotic shape with the NEW `genome.genome_from_graph`: "hand a graph,
get nuclear + plasmid from its OWN structure." This replaces the old 2x-stick `simplewiki_directed.genome` (built raw
via graph_to_kernel+genome_save at rc253, which could not mint) with the data-driven partitioned genome — nuclear
communities MINTED (0x58 centromere), plasmid communities kept as Tier-1 stick — so the earlier layout/read A-D
questions can be answered on the correct genome.

This ALSO completes F1250's open question: genome_partition runs the FULL out-of-core recursive_cut communities (not
the 5000-word tome band), so we finally see whether the 831k/39M word graph is genuinely bimodal (nuclear+plasmid) or
`one_dna_type` at scale — measured, not assumed (§100.1).

Source: ~/corpora/wikipedia/simplewiki_directed_sparse_kernel.json (vocab / edge_list / edge_weights / edge_charge;
831,139 vocab / 39,048,148 edges). COUPLE = klein4_random(64, seed=1080) (the store's canonical seed).

srmech 0.9.0rc272 (native). No numpy in the harness; no abs-builtin. Composes F1249/F1250/F1251, §95/§100, #231.
Run (background — recursive_cut on 39M edges is the heavy step):
  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-SIMPLEWIKIGENOME2_*.py
"""
import json
import shutil
import sys
import time
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import hdc

LEAF = 64
COUPLE = hdc.klein4_expand(LEAF, 1080)
SRC = Path.home() / "corpora" / "wikipedia" / "simplewiki_directed_sparse_kernel.json"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_eukaryotic.genome"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_eukaryotic.report.json"
T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def vocab_to_syms(vocab):
    b = "\n".join(vocab).encode("utf-8")
    syms = []
    for x in b:
        syms += [x & 3, (x >> 2) & 3, (x >> 4) & 3, (x >> 6) & 3]
    return syms


def main():
    import srmech
    log("=== SIMPLEWIKIGENOME2 — eukaryotic re-encode via genome_from_graph (srmech %s) ===" % srmech.__version__)
    log("loading the directed sparse kernel (916 MB) ...")
    K = json.load(open(SRC))
    vocab = K["vocab"]
    edges = [tuple(e) for e in K["edge_list"]]
    weights = K["edge_weights"]
    charges = K["edge_charge"]
    n = len(vocab)
    log("loaded: %d vocab, %d edges" % (n, len(edges)))

    if OUT.exists():
        shutil.rmtree(OUT, ignore_errors=True)

    # THE re-encode: partition by the graph's own structure + mint nuclear / keep plasmid, in one call.
    log("genome_from_graph: partition (out-of-core recursive_cut) + mint nuclear / keep plasmid ... (heavy)")
    info = G.genome_from_graph(n, edges, weights, charges, the_one=COUPLE, path=str(OUT))
    part = info["partition"]
    log("PARTITION: n_communities=%s bimodal=%s one_dna_type=%s antimode_gap=%s counts=%s node_counts=%s" %
        (part.get("n_communities"), part.get("bimodal"), part.get("one_dna_type"),
         part.get("antimode", {}).get("gap"), part.get("counts"), part.get("node_counts")))
    log("built %d chromosomes: %s" % (len(info["chromosomes"]),
        [(c["label"], c["type"], len(c["nodes"])) for c in info["chromosomes"][:8]]))

    # append the vocab string-table as its own chromosome (self-contained genome, no plaintext)
    log("appending the __vocab__ chromosome ...")
    G.genome_append_kernel(str(OUT), "__vocab__", vocab_to_syms(vocab), the_one=COUPLE)

    # census + sizes
    cen = G.genome_census(str(OUT))
    nbytes = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    log("CENSUS: %s | topology=%s | genome %.1f MB" %
        (cen.get("types"), cen.get("topology"), nbytes / 1e6))

    # node -> chromosome mapping (so the read path can address token -> (chromosome, local node))
    node_map = {}
    for c in info["chromosomes"]:
        for local, glob in enumerate(c["nodes"]):
            node_map[glob] = (c["label"], local)

    rec = {"srmech": srmech.__version__, "vocab": n, "edges": len(edges),
           "n_chromosomes": cen.get("n_chromosomes"), "types": cen.get("types"),
           "topology": cen.get("topology"), "genome_mb": round(nbytes / 1e6, 2),
           "partition": {"n_communities": part.get("n_communities"), "bimodal": part.get("bimodal"),
                         "one_dna_type": part.get("one_dna_type"), "antimode": part.get("antimode"),
                         "counts": part.get("counts"), "node_counts": part.get("node_counts")},
           "chromosomes": [{"label": c["label"], "type": c["type"], "n_nodes": len(c["nodes"])}
                           for c in info["chromosomes"]],
           "seconds": round(time.time() - T0, 1)}
    REPORT.write_text(json.dumps(rec) + "\n")
    log("report -> %s" % REPORT)
    log("VERDICT: eukaryotic re-encode COMPLETE — %d chromosomes (%s), topology=%s, %.1f MB in %.0fs" %
        (cen.get("n_chromosomes"), cen.get("types"), cen.get("topology"), nbytes / 1e6, time.time() - T0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
