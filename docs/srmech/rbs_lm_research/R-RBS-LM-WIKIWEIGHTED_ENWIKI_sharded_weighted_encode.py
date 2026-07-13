r"""R-RBS-LM-WIKITOWERC_FULL (#225/#260) — the FULL-SCALE, sharded, RESUMABLE comprehended encode: stream the whole
enwiki dump ONCE, route each article through the sub-language ROUTER, and encode each shard's CLEAN PROSE as the Class-L
co-occurrence assoc (the ① distributional tome-tower input) — plus the per-shard ② relational counts (the kernels' typed
edges by family) and the sublanguage-block census. WIKITOWER's validated sharded/resumable machinery, with route_article
in the loop (so nothing materializes the whole corpus; one shard at a time; a kill re-streams to the offset).

Primary deliverable = the comprehended co-occurrence genome (assoc + freq per shard, merged downstream like the raw
tower). The relational typed-edge graph is deterministic from route_article; here we persist its per-family COUNTS +
the block census (the volume of what was comprehended, not stripped) to keep the multi-day job bounded and robust.

srmech 0.9.0rc209. numpy-free; no Python abs builtin; no Counter; no CAD. CC-BY-SA enwiki (attested-not-committed). Run:
  SHARD=50000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKITOWERC_FULL_...py
  # tiny validation: MAX_ARTICLES=4000 SHARD=2000 ... (2 shards, then stop)
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

import srmech

DUMP = os.environ.get("WIKI_DUMP", str(Path.home() / "corpora" / "wikipedia" / "enwiki-latest-pages-articles.xml.bz2"))
OUTDIR = Path(os.environ.get("SHARD_DIR", str(Path.home() / "corpora" / "wikipedia" / "enwiki_weighted_shards")))
SHARD = int(os.environ.get("SHARD", "50000"))
WINDOW = int(os.environ.get("WINDOW", "4"))
K_NBR = int(os.environ.get("K_NBR", "16"))
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "0")) or None
_D = "docs/srmech/rbs_lm_research/"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


ROUTER = _load("rt", _D + "R-RBS-LM-ROUTER_sublanguage_dispatch_compose.py")
WK = _load("wk", _D + "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


class _ListSource:
    def __init__(self, texts):
        self.texts = texts

    def __iter__(self):
        return iter(self.texts)


def _family(rt):
    rt = str(rt)
    if ":" in rt:
        return rt.split(":")[0]
    if rt == "cites":
        return "cites"
    if rt in ("in_language", "pronounced_as") or rt.startswith("has_") or rt.startswith("melody"):
        return "quantity/lang/pron"
    return "wikilink"


def _assoc(vocab, edges, weights):
    fan = {}
    for (i, j), w in zip(edges, weights):
        wi, wj = vocab[i], vocab[j]; wt = float(w)
        fi = fan.setdefault(wi, {}); fi[wj] = fi.get(wj, 0.0) + wt
        fj = fan.setdefault(wj, {}); fj[wi] = fj.get(wi, 0.0) + wt
    return {w: [nb for nb, _ in sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:K_NBR]] for w, d in fan.items()}


def encode_shard(shard_id, prose, fam_counts, block_counts, gap_counts):
    vocab, idx, edges, weights, freq, dropped = WK.build_edges_topk(_ListSource(prose), window=WINDOW, vocab_cap=None)
    # F1207 REPOINT: the shard is a mini full_sparse_kernel — the FULL UNCAPPED WEIGHTED edges (edge_list +
    # edge_weights + vocab), NOT the truncated top-K `assoc` the comprehended encoder stored. The weighted external
    # merge sums edge_weights across shards; op/operand/responsion all recover. Comprehension (ROUTER) is unchanged.
    rec = {"shard_id": shard_id, "n_articles": len(prose), "srmech": srmech.__version__, "window": WINDOW,
           "vocab_size": len(vocab), "n_cooc_edges": len(edges), "uncapped": True,
           "vocab": vocab, "freq": freq,
           "edge_list": [[int(a), int(b)] for a, b in edges],
           "edge_weights": [float(w) for w in weights],
           "relational_edge_counts": fam_counts, "sublang_blocks": block_counts, "residual_gaps": gap_counts}
    return rec, len(vocab), len(edges)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f"=== WIKITOWERC_FULL — sharded resumable COMPREHENDED encode (srmech {srmech.__version__}) ===")
    print(f"  SHARD={SHARD} WINDOW={WINDOW} K_NBR={K_NBR} max={MAX_ARTICLES or 'ALL'} outdir={OUTDIR}\n")
    done = sorted(OUTDIR.glob("wshard_*.json"))
    n_done = len(done); skip = n_done * SHARD
    if n_done:
        print(f"  RESUME: {n_done} shard(s) done -> stream-discard {skip} articles\n")
    t0 = time.time()
    buf, fam, blk, gap = [], {}, {}, {}
    shard_id = n_done
    seen = 0

    def flush():
        nonlocal buf, fam, blk, gap, shard_id
        if not buf:
            return
        te = time.time()
        rec, nv, ne = encode_shard(shard_id, buf, fam, blk, gap)
        out = OUTDIR / f"wshard_{shard_id:05d}.json"
        out.write_text(json.dumps(rec))
        print(f"  wshard {shard_id:05d}: {len(buf)} arts -> vocab {nv:,} cooc {ne:,} | rel {sum(fam.values()):,} "
              f"blocks {sum(blk.values()):,} | {out.stat().st_size/1e6:.0f}MB {time.time()-te:.0f}s "
              f"peakRSS {rss_gb():.1f}GB | elapsed {time.time()-t0:.0f}s", flush=True)
        shard_id += 1; buf, fam, blk, gap = [], {}, {}, {}

    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _ev, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                seen += 1
                if seen <= skip:
                    el.clear()
                    if seen % 500000 == 0:
                        print(f"    ...skipped {seen}/{skip} ({time.time()-t0:.0f}s)", flush=True)
                    continue
                r = ROUTER.route_article(el.text)
                buf.append(r["prose"])
                for e in r["edges"]:
                    fam[_family(e[1] if len(e) > 1 else "")] = fam.get(_family(e[1] if len(e) > 1 else ""), 0) + 1
                for k, v in r["counts"].items():
                    blk[k] = blk.get(k, 0) + v
                for k, v in (r["gaps"] or {}).items():
                    gap[k] = gap.get(k, 0) + v
                if len(buf) >= SHARD:
                    flush()
                    if MAX_ARTICLES and (seen - skip) >= MAX_ARTICLES:
                        el.clear(); print("\n  MAX_ARTICLES reached — stopping (validation)."); break
            el.clear()
        else:
            flush()
    total = len(sorted(OUTDIR.glob("wshard_*.json")))
    print(f"\n  DONE: {total} comprehended shards in {OUTDIR} ({time.time()-t0:.0f}s, peakRSS {rss_gb():.1f}GB)")


if __name__ == "__main__":
    main()
