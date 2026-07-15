r"""R-RBS-LM-BUILDTREE (#231/F786) — build the de-lensed Fiedler tome-TREE + WEB for a corpus genome, ONCE.

The tome-tree is Siona's find->ride->web-hop navigation surface (F786/F791 ETAKNAV, at corpus scale): drop the
top-df hubs (markup / function words), keep a content band, IDF-weight + sparsify, recursive sparse-Fiedler
bisection = clumps-of-clumps (the TREE); the cut edges between leaf tomes = the WEB. Written under
<genome_dir>/tree/ (cached like reads/), so corpus_store.prepare() attaches it and find/ride/web_hop are instant.

Run (background; ~1-2 min: edge scan + Fiedler recursion over the content band):
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-BUILDTREE_...py
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "siona"))
from siona import corpus_store as cs

GENOME = os.environ.get("TREE_GENOME", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome"))


def main():
    print("=== R-RBS-LM-BUILDTREE — the tome-tree find/ride/web-hop for %s ===" % Path(GENOME).name, flush=True)
    t0 = time.time()
    r = cs.build_tree_from_store(GENOME)                # memory-light: straight from reads/ (no 960MB json.load)
    print("[%.0fs] BUILT tree/: %d tomes, %d hubs dropped, %d content words placed"
          % (time.time() - t0, r["tomes"], r["hubs"], r["words"]), flush=True)

    # verify: attach + navigate
    t0 = time.time()
    h = cs.prepare(GENOME)
    print("[%.2fs] open (tree attached=%s)" % (time.time() - t0, bool(h.get("tree"))), flush=True)
    for tok in ("water", "planet", "music", "science", "vanuatu", "chirality"):
        f = cs.find(h, tok)
        if not f:
            print("    %-10s -> (not in the content band)" % tok, flush=True)
            continue
        hop = cs.web_hop(h, f["tome"])
        print("    %-10s FIND tome #%d (zoom %d) {%s}" % (tok, f["tome"], f["depth"], ", ".join(f["label"][:6])), flush=True)
        if hop:
            print("               WEB-HOP -> tome #%d {%s} via bridge '%s'~'%s'"
                  % (hop["to"], ", ".join(hop["label"][:5]), hop["bridge"][0], hop["bridge"][1]), flush=True)
    print("VERDICT: tome-tree built; find/ride/web-hop live over the corpus genome.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
