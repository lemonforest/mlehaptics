r"""R-RBS-LM-WIKITOWER_merge (#225) — merge the per-shard weighted assoc stores into ONE global enwiki_assoc.json in the
FULLCLUMP-consumable format, plus enwiki_freq.json (the union frequency table for the class-lexicon / mass-count work).

INPUT:  enwiki_tome_shards/shard_NNNNN.json  (each: {assoc:{word:[[nbr,wt],...topK]}, freq:{word:count}, ...})
OUTPUT: enwiki_assoc.json  = {"assoc": {word: [nbr1, nbr2, ... global-topK ordered by SUMMED weight]}, ...meta}
        enwiki_freq.json   = {"freq":  {word: total_count}, ...meta}   (ALL words kept — F708 union)

MERGE math: a word-pair's total co-occurrence weight is the SUM of its per-shard weights (co-occurrence is additive over
disjoint article shards). Per-word neighbourhoods are re-trimmed to global top-K after accumulation — the relational
discipline ([[feedback_relational_not_dense_distributional]]: top-K neighbourhoods, never the large), NOT a vocab cap.
To bound peak RAM the running fan is pruned to PRUNE_K (=4*K) per touched word after each shard; the final pass trims to
K. numpy-free; plain dicts (no Counter); no Python abs builtin. CC-BY-SA enwiki; persisted OUTSIDE the repo.

Run:  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKITOWER_merge_shards_to_global_assoc.py
"""
import json
import os
import resource
import time
from pathlib import Path

import srmech

SHARD_DIR = Path(os.environ.get("SHARD_DIR", str(Path.home() / "corpora" / "wikipedia" / "enwiki_tome_shards")))
ASSOC_OUT = Path(os.environ.get("ASSOC_OUT", str(Path.home() / "corpora" / "wikipedia" / "enwiki_assoc.json")))
FREQ_OUT = Path(os.environ.get("FREQ_OUT", str(Path.home() / "corpora" / "wikipedia" / "enwiki_freq.json")))
K = int(os.environ.get("K_NBR", "16"))                        # final top-K neighbours per word
PRUNE_K = 4 * K                                               # running fan bound per word


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


def topk(d, k):
    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def main():
    t0 = time.time()
    shards = sorted(SHARD_DIR.glob("shard_*.json"))
    print(f"=== WIKITOWER_merge — {len(shards)} shards -> global assoc (srmech {srmech.__version__}) ===")
    if not shards:
        print(f"  NO shards in {SHARD_DIR} — run the tower encoder first."); return

    fan = {}                                                  # word -> {nbr: summed_weight}
    freq = {}                                                 # word -> total count (F708 union)
    for si, sp in enumerate(shards):
        rec = json.loads(sp.read_text())
        for w, c in rec.get("freq", {}).items():
            freq[w] = freq.get(w, 0) + c
        touched = set()
        for w, nbrs in rec.get("assoc", {}).items():
            fw = fan.setdefault(w, {})
            for nb, wt in nbrs:
                fw[nb] = fw.get(nb, 0.0) + float(wt)
            touched.add(w)
        for w in touched:                                     # bound the running fan (memory)
            fw = fan[w]
            if len(fw) > PRUNE_K:
                fan[w] = dict(topk(fw, PRUNE_K))
        if (si + 1) % 10 == 0 or si + 1 == len(shards):
            print(f"  merged {si+1}/{len(shards)} shards | words {len(fan):,} | freq-vocab {len(freq):,} "
                  f"| peakRSS {rss_gb():.1f}GB | {time.time()-t0:.0f}s", flush=True)

    assoc = {w: [nb for nb, _ in topk(d, K)] for w, d in fan.items()}   # FULLCLUMP format: ordered neighbour-word list
    meta = {"wiki": "enwiki", "srmech": srmech.__version__, "n_shards": len(shards),
            "vocab": len(assoc), "k_nbr": K, "note": "sharded tome tower, full-vocab (F708), top-K relational assoc"}
    ASSOC_OUT.write_text(json.dumps({"assoc": assoc, **meta}))
    FREQ_OUT.write_text(json.dumps({"freq": freq, "wiki": "enwiki", "vocab": len(freq)}))
    print(f"\n  WROTE {ASSOC_OUT.name} ({ASSOC_OUT.stat().st_size/1e6:.0f}MB, {len(assoc):,} words) "
          f"+ {FREQ_OUT.name} ({FREQ_OUT.stat().st_size/1e6:.0f}MB, {len(freq):,} words)")
    print(f"  peakRSS {rss_gb():.1f}GB | {time.time()-t0:.0f}s")
    print("  NEXT: ASSOC=enwiki_assoc.json OUT=enwiki_tome_tree.json FULLCLUMP -> the Class-L spectral community tower")


if __name__ == "__main__":
    main()
