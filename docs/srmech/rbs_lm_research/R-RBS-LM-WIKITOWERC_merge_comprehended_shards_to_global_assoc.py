r"""R-RBS-LM-WIKITOWERC_merge (#260) — merge the 514 COMPREHENDED per-shard assoc stores
(``enwiki_comprehended_shards/cshard_NNNNN.json``) into ONE global ``enwiki_assoc.json`` in the
simplewiki_assoc-compatible / FULLCLUMP-consumable format, plus ``enwiki_freq.json``.

WHY THIS IS A SEPARATE MERGE FROM THE TOME-TOWER ONE (R-RBS-LM-WIKITOWER_merge):
The comprehended encoder's ``_assoc`` DROPS per-edge weights — each shard stores only
``{word: [top-K neighbours ORDERED by that shard's weight]}`` (weights gone), plus ``freq``. So the
weight-SUM math of the tome-tower merge cannot run here. Instead we aggregate by RANK: reciprocal-rank
fusion (RRF) — a neighbour that sits high in many shards' lists ranks high globally. RRF is the standard
rank-fusion move and is arguably MORE robust than a raw weight-sum here (it is not dominated by the
front-loaded dense early shards 0-10, an integrity note from the header pass). ``freq`` and article
counts are additive and summed exactly. The seam at shard 114 (rc209->rc217) was verified BIT-IDENTICAL
(seam_parity: same vocab/edges/weights hash), so mixing the two srmech legs is safe.

MERGE math: score(w, nbr) += 1/(rank+1) summed over every shard that lists nbr in w's neighbourhood.
Per-word running fan pruned to PRUNE_K (=4*K) after each shard to bound RAM; final trim to K.
numpy-free; plain dicts (NO Counter); NO Python abs builtin. CC-BY-SA enwiki; persisted OUTSIDE the repo.

Env: SHARD_DIR, ASSOC_OUT, FREQ_OUT, K_NBR, MAX_SHARDS (0=all; a subset for a dry run).
Run:  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKITOWERC_merge_comprehended_shards_to_global_assoc.py
"""
import hashlib
import json
import os
import resource
import time
from pathlib import Path

import srmech
from srmech.amsc.format import sha256_bytes                 # Class-A content hash (native dispatch)

SHARD_DIR = Path(os.environ.get("SHARD_DIR", str(Path.home() / "corpora" / "wikipedia" / "enwiki_comprehended_shards")))
ASSOC_OUT = Path(os.environ.get("ASSOC_OUT", str(Path.home() / "corpora" / "wikipedia" / "enwiki_assoc.json")))
FREQ_OUT = Path(os.environ.get("FREQ_OUT", str(Path.home() / "corpora" / "wikipedia" / "enwiki_freq.json")))
K = int(os.environ.get("K_NBR", "16"))
PRUNE_K = 4 * K
MAX_SHARDS = int(os.environ.get("MAX_SHARDS", "0"))          # 0 = all; >0 = dry-run subset


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


def topk(fan_w, k):
    # rank by (RRF score DESC, neighbour name ASC) — deterministic, ties broken lexically
    return sorted(fan_w.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def main():
    t0 = time.time()
    shards = sorted(SHARD_DIR.glob("cshard_*.json"))
    if MAX_SHARDS:
        shards = shards[:MAX_SHARDS]
    if not shards:
        print(f"  NO cshard_*.json in {SHARD_DIR}"); return
    print(f"=== WIKITOWERC_merge (#260) — {len(shards)} comprehended shards -> global assoc "
          f"(srmech {srmech.__version__}, RRF rank-fusion) ===")

    fan = {}                                                # word -> {nbr: rrf_score}
    freq = {}                                               # word -> total count (F708 union)
    n_articles = 0
    versions = {}                                           # srmech version -> shard count (seam audit)
    manifest = []                                           # (name, size) for the attestation hash
    for si, sp in enumerate(shards):
        rec = json.loads(sp.read_text())
        n_articles += int(rec.get("n_articles", 0))
        v = rec.get("srmech", "?"); versions[v] = versions.get(v, 0) + 1
        manifest.append((sp.name, sp.stat().st_size))
        for w, c in rec.get("freq", {}).items():
            freq[w] = freq.get(w, 0) + int(c)
        touched = []
        for w, nbrs in rec.get("assoc", {}).items():
            fw = fan.setdefault(w, {})
            for rank, nb in enumerate(nbrs):                # nbrs are ordered strongest-first
                fw[nb] = fw.get(nb, 0.0) + 1.0 / (rank + 1.0)
            touched.append(w)
        for w in touched:                                   # bound the running fan (memory)
            fw = fan[w]
            if len(fw) > PRUNE_K:
                fan[w] = dict(topk(fw, PRUNE_K))
        if (si + 1) % 25 == 0 or si + 1 == len(shards):
            print(f"  [{si+1:>3}/{len(shards)}] words={len(fan):,} freq_vocab={len(freq):,} "
                  f"rss={rss_gb():.1f}GB t={time.time()-t0:.0f}s")

    assoc = {w: [nb for nb, _ in topk(d, K)] for w, d in fan.items()}
    mhash = sha256_bytes(("\n".join(f"{n}:{s}" for n, s in manifest)).encode())
    attestation = {
        "source": "Wikipedia enwiki full-article comprehended co-occurrence shards (#259 encoder)",
        "license": "CC-BY-SA-4.0",
        "n_shards": len(shards),
        "srmech_versions": versions,                        # seam audit: rc209 + rc217, verified bit-identical
        "seam_note": "shard 114 rc209->rc217 boundary verified bit-identical (seam_parity)",
        "aggregation": "reciprocal-rank fusion over per-shard top-K neighbour lists (weights dropped by _assoc)",
        "shard_manifest_sha256": mhash,
        "parser_version": f"WIKITOWERC_merge / srmech {srmech.__version__}",
    }
    out = {"wiki": "enwiki", "articles": n_articles, "vocab_size": len(assoc), "K": K,
           "freq": freq, "assoc": assoc, "attestation": attestation}
    ASSOC_OUT.write_text(json.dumps(out))
    FREQ_OUT.write_text(json.dumps({"wiki": "enwiki", "articles": n_articles,
                                    "freq": freq, "attestation": attestation}))
    print(f"=== DONE: {len(assoc):,} words, {n_articles:,} articles, versions={versions} ===")
    print(f"  assoc -> {ASSOC_OUT} ({ASSOC_OUT.stat().st_size/1e6:.0f} MB)")
    print(f"  freq  -> {FREQ_OUT} ({FREQ_OUT.stat().st_size/1e6:.0f} MB)")
    print(f"  peak rss={rss_gb():.1f}GB  wall={time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
