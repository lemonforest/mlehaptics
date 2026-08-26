r"""R-RBS-LM-WIKITOWER (#225 / the bigwiki genome) — the RESUMABLE SHARDED TOME TOWER for the FULL enwiki dump.

WHY sharded (the fractal tower, user-authorized "address it with fractal tower if other idea doesn't work"): the flat
encoders (WIKIBIGENCODE / build_edges_topk's native cooccurrence path / LOOPSHELF's toks.extend) all MATERIALIZE the
whole corpus in RAM at once (`docs = [[...] for art in stream]` / one giant token list). For ~300k simplewiki articles
that fits; for the ~6.9M-article, ~3-4B-content-token enwiki dump it is hundreds of GB -> it does not fit in 90GB+swap
(the 40k-article probe timed out on exactly this). The tower encodes ONE SHARD of SHARD articles at a time — each shard
is simplewiki-scale, so it fits — then composes them. This HONORS F708 (NO magic vocab ceiling: vocab_cap=None keeps
ALL content words WITHIN each shard; the global vocab is the UNION across shards) while bounding peak RAM to one shard.

The per-word neighbourhood is trimmed to top-K_NBR — that is the SANCTIONED RELATIONAL discipline
([[feedback_relational_not_dense_distributional]]: "relational is inherently selective — top-K neighbourhoods + the
Class-L backbone; we never carry the large"), NOT a magic vocab ceiling. All words are kept; only each word's edge FAN
is bounded. The weighted per-shard assoc merges (sum weights across shards, re-trim to global top-K) into one global
enwiki_assoc.json that FULLCLUMP consumes for the native tome-TREE (the Class-L spectral community class signal).

RESUMABLE: one shard -> one checkpoint file shard_NNNNN.json. On restart, done shards are counted and the bz2 is
streamed-and-discarded (no tokenize/encode) up to that article offset, then encoding resumes. A multi-hour job survives
a kill. swap is available for the per-shard peak.

srmech 0.9.0rc207 (native dense_laplacian/jacobi live in the DOWNSTREAM FULLCLUMP step; this step is streaming + the
disciplined build_edges_topk). No numpy; no Python abs builtin; no Counter; no CAD. Persisted OUTSIDE the repo
(CC-BY-SA enwiki; attested-not-committed). Run from the worktree root:
  SHARD=50000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKITOWER_...py
  # tiny validation: MAX_ARTICLES=10000 SHARD=5000 ... (2 shards, measures RSS/time/size then stops)
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
OUTDIR = Path(os.environ.get("SHARD_DIR", str(Path.home() / "corpora" / "wikipedia" / "enwiki_tome_shards")))
SHARD = int(os.environ.get("SHARD", "50000"))                 # articles per shard (simplewiki-scale -> fits)
WINDOW = int(os.environ.get("WINDOW", "4"))                   # real-text co-occurrence window
K_NBR = int(os.environ.get("K_NBR", "16"))                   # top-K co-occurrence neighbours per word (relational trim)
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "0")) or None   # 0/unset = whole dump; set for a validation run


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    saved = sys.argv
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    sys.argv = saved
    return mod


wk = _load("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)   # linux ru_maxrss is KiB


class ListSource:
    """A re-iterable source wrapping a shard's buffered raw article texts (build_edges_topk streams it TWICE)."""
    def __init__(self, texts):
        self.texts = texts

    def __iter__(self):
        return iter(self.texts)


def shard_assoc(vocab, edges, weights, freq):
    """Derive per-word top-K_NBR WEIGHTED neighbours from the shard's sparse edge list (plain-dict; no Counter/abs).

    edges is a list of (i,j) index pairs (i<j); weights parallel. Build word -> [(nbr_word, weight)] then keep top-K.
    """
    fan = {}                                                  # word -> {nbr_word: weight}
    for (i, j), w in zip(edges, weights):
        wi, wj = vocab[i], vocab[j]
        wt = float(w)
        fi = fan.setdefault(wi, {}); fi[wj] = fi.get(wj, 0.0) + wt
        fj = fan.setdefault(wj, {}); fj[wi] = fj.get(wi, 0.0) + wt
    assoc = {}
    for w, nbrs in fan.items():
        top = sorted(nbrs.items(), key=lambda kv: (-kv[1], kv[0]))[:K_NBR]
        assoc[w] = [[nb, wt] for nb, wt in top]
    return assoc


def encode_shard(shard_id, texts):
    src = ListSource(texts)
    vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(src, window=WINDOW, vocab_cap=None)   # F708: ALL words
    assoc = shard_assoc(vocab, edges, weights, freq)
    rec = {
        "shard_id": shard_id, "n_articles": len(texts), "srmech": srmech.__version__,
        "window": WINDOW, "k_nbr": K_NBR, "vocab_size": len(vocab), "n_edges": len(edges),
        "assoc": assoc, "freq": freq,                         # freq for ALL shard words (F708 union upstream)
    }
    return rec, len(vocab), len(edges)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ns = srmech.native_status()
    print(f"=== R-RBS-LM-WIKITOWER — resumable sharded tome tower (srmech {srmech.__version__}, native {ns['has_native']}) ===")
    print(f"  dump={DUMP}")
    print(f"  SHARD={SHARD}  WINDOW={WINDOW}  K_NBR={K_NBR}  max_articles={MAX_ARTICLES or 'ALL'}  outdir={OUTDIR}\n")

    done = sorted(p for p in OUTDIR.glob("shard_*.json"))
    n_done = len(done)
    skip_articles = n_done * SHARD
    if n_done:
        print(f"  RESUME: {n_done} shard(s) already done -> streaming-discard {skip_articles} articles to catch up\n")

    t0 = time.time()
    buf = []
    shard_id = n_done
    seen = 0                                                  # total articles seen this run (incl. skipped)
    encoded_this_run = 0

    def flush(final=False):
        nonlocal buf, shard_id
        if not buf:
            return True
        te = time.time()
        rec, nv, ne = encode_shard(shard_id, buf)
        out = OUTDIR / f"shard_{shard_id:05d}.json"
        out.write_text(json.dumps(rec))
        sz = out.stat().st_size / 1e6
        print(f"  shard {shard_id:05d}: {len(buf)} arts -> vocab {nv:,} edges {ne:,} | {out.name} {sz:.1f}MB | "
              f"encode {time.time()-te:.1f}s peakRSS {rss_gb():.1f}GB | elapsed {time.time()-t0:.0f}s", flush=True)
        shard_id += 1
        buf = []
        return True

    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _ev, el in ET.iterparse(fh, events=("end",)):
            is_text = el.tag.endswith("}text") or el.tag == "text"
            if is_text and el.text:
                seen += 1
                if seen <= skip_articles:                     # RESUME skip: discard without buffering/encoding
                    el.clear()
                    if seen % 500000 == 0:
                        print(f"    ...skipped {seen}/{skip_articles} ({time.time()-t0:.0f}s)", flush=True)
                    continue
                buf.append(el.text)
                if len(buf) >= SHARD:
                    flush()
                    encoded_this_run += SHARD
                    if MAX_ARTICLES and (seen - skip_articles) >= MAX_ARTICLES:
                        el.clear()
                        print("\n  MAX_ARTICLES reached (validation run) — stopping.")
                        break
            el.clear()
        else:
            flush(final=True)                                 # trailing partial shard at true EOF

    total_shards = len(sorted(OUTDIR.glob("shard_*.json")))
    print(f"\n  DONE: {total_shards} shards on disk in {OUTDIR}  (this run encoded {encoded_this_run}+ arts, "
          f"{time.time()-t0:.0f}s, peakRSS {rss_gb():.1f}GB)")
    print("  NEXT: merge shards -> enwiki_assoc.json (R-RBS-LM-WIKITOWER_merge), then FULLCLUMP -> enwiki_tome_tree.json")


if __name__ == "__main__":
    main()
